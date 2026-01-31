"""
Timeback Caliper Client

Async client for sending Caliper learning analytics events to Timeback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, cast

from .lib.transport import Transport
from .resources.events import EventsResource
from .resources.jobs import JobsResource

if TYPE_CHECKING:
    from timeback_common import AuthCheckResult, Environment, TimebackProvider

Platform = Literal["BEYOND_AI", "LEARNWITH_AI"]


class CaliperTransportLike(Protocol):
    """Duck-typed transport interface for custom transports."""

    base_url: str

    async def close(self) -> None:
        """Close the transport and release resources."""
        ...


class CaliperClient:
    """
    Caliper Analytics API client.

    Provides methods to send, list, and retrieve Caliper learning events,
    as well as track async processing jobs.

    Example: Environment mode (Timeback APIs)
        ```python
        client = CaliperClient(
            env="staging",  # or "production"
            client_id="your-client-id",
            client_secret="your-client-secret",
        )
        ```

    Example: Environment variables fallback
        ```python
        # Set CALIPER_CLIENT_ID and CALIPER_CLIENT_SECRET
        client = CaliperClient(env="staging")
        ```

    Example: Custom base URL
        ```python
        client = CaliperClient(
            base_url="https://custom.example.com",
            client_id="your-client-id",
            client_secret="your-client-secret",
        )
        ```

    Example: Sending events
        ```python
        result = await client.events.send_activity(
            sensor_id="https://example.edu/sensors/lms",
            input=ActivityCompletedInput(
                actor=TimebackUser(id="...", email="student@example.edu"),
                object=TimebackActivityContext(id="...", subject="Math", app=TimebackApp(name="My App")),
                metrics=[TimebackActivityMetric(type="correctQuestions", value=8)],
            ),
        )

        # Wait for processing
        status = await client.jobs.wait_for_completion(result.job_id)
        ```
    """

    def __init__(
        self,
        *,
        platform: Platform | None = None,
        env: str | None = None,
        transport: CaliperTransportLike | None = None,
        base_url: str | None = None,
        auth_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 30.0,
        provider: TimebackProvider | None = None,
    ) -> None:
        """
        Initialize the Caliper client.

        Args:
            platform: Target platform ("BEYOND_AI" or "LEARNWITH_AI"). Defaults to BEYOND_AI.
            env: Environment ("staging" or "production")
            base_url: API base URL (overrides platform/env resolution)
            auth_url: Auth token URL (overrides platform/env resolution)
            client_id: OAuth2 client ID (or set CALIPER_CLIENT_ID env var)
            client_secret: OAuth2 client secret (or set CALIPER_CLIENT_SECRET env var)
            timeout: Request timeout in seconds
            provider: Optional TimebackProvider for shared auth

        Note:
            Platform determines available features:
            - BEYOND_AI: Full Caliper support (send, validate, list, get, jobs)
            - LEARNWITH_AI: Send-only; validate/list/get/jobs raise errors
        """
        self._transport: Transport | CaliperTransportLike
        if transport is not None:
            self._transport = transport
            self._provider = None
        else:
            from timeback_common import EnvVarNames, build_provider_env, build_provider_explicit

            env_vars = EnvVarNames(
                base_url="CALIPER_BASE_URL",
                auth_url="CALIPER_TOKEN_URL",
                client_id="CALIPER_CLIENT_ID",
                client_secret="CALIPER_CLIENT_SECRET",
            )

            if provider is None:
                if env is not None:
                    provider = build_provider_env(
                        platform=platform,
                        env=cast("Environment", env),
                        client_id=client_id,
                        client_secret=client_secret,
                        timeout=timeout,
                        env_vars=env_vars,
                    )
                else:
                    provider = build_provider_explicit(
                        base_url=base_url,
                        auth_url=auth_url,
                        client_id=client_id,
                        client_secret=client_secret,
                        timeout=timeout,
                        env_vars=env_vars,
                    )

            self._provider = provider

            endpoint = provider.get_endpoint("caliper")
            paths = provider.get_paths("caliper")
            token_manager = provider.get_token_manager("caliper")

            self._transport = Transport(
                base_url=endpoint.base_url,
                token_manager=token_manager,
                paths=paths,
                timeout=provider.timeout,
                no_auth=token_manager is None,
            )

        # Initialize resources - cast needed because Resources expect full Transport
        # but we allow duck-typed transports for testing flexibility
        self.events = EventsResource(cast("Transport", self._transport))
        self.jobs = JobsResource(cast("Transport", self._transport))

    def get_transport(self) -> Transport | CaliperTransportLike:
        """
        Get the underlying transport for advanced use cases.

        Returns:
            The transport instance used by this client
        """
        return self._transport

    async def check_auth(self) -> AuthCheckResult:
        """
        Verify that OAuth authentication is working.

        Returns:
            Auth check result with ok, latency_ms, and checks

        Raises:
            RuntimeError: If client was initialized without a provider
        """
        if self._provider is None:
            raise RuntimeError("Cannot check auth: client initialized without provider")
        return await self._provider.check_auth()

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self._transport.close()

    async def __aenter__(self) -> CaliperClient:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()
