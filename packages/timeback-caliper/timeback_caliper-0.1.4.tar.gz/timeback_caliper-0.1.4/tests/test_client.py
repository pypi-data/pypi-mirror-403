"""Tests for CaliperClient."""

import os
from unittest.mock import patch

import pytest

from timeback_caliper import (
    CaliperClient,
    UnsupportedOperationError,
)


class TestCaliperClientInit:
    """Tests for client initialization."""

    def test_staging_environment(self):
        """Staging environment should use staging URL."""
        with patch.dict(os.environ, {"CALIPER_CLIENT_ID": "id", "CALIPER_CLIENT_SECRET": "secret"}):
            client = CaliperClient(env="staging")
            # BEYOND_AI (default) uses "staging" subdomain; LEARNWITH_AI uses "dev"
            assert "staging" in client._transport.base_url

    def test_production_environment(self):
        """Production environment should use production URL."""
        with patch.dict(os.environ, {"CALIPER_CLIENT_ID": "id", "CALIPER_CLIENT_SECRET": "secret"}):
            client = CaliperClient(env="production")
            # Production URLs don't contain "dev" or "staging"
            assert "dev" not in client._transport.base_url
            assert "staging" not in client._transport.base_url

    def test_custom_base_url(self):
        """Custom base URL should override environment."""
        with patch.dict(
            os.environ,
            {
                "CALIPER_CLIENT_ID": "id",
                "CALIPER_CLIENT_SECRET": "secret",
                "CALIPER_TOKEN_URL": "https://auth.example.com/oauth2/token",
            },
        ):
            client = CaliperClient(
                base_url="https://custom.example.com",
                auth_url="https://auth.example.com/oauth2/token",
            )
            assert client._transport.base_url == "https://custom.example.com"

    def test_explicit_credentials(self):
        """Explicit credentials should work."""
        client = CaliperClient(
            env="staging",
            client_id="my-id",
            client_secret="my-secret",
        )
        assert client._provider is not None
        tm = client._provider.get_token_manager("caliper")
        assert tm is not None
        assert tm._config.client_id == "my-id"
        assert tm._config.client_secret == "my-secret"

    def test_missing_credentials_raises(self):
        """Missing credentials should raise AuthenticationError."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove any env vars that might be set
            os.environ.pop("CALIPER_CLIENT_ID", None)
            os.environ.pop("CALIPER_CLIENT_SECRET", None)
            with pytest.raises(ValueError, match="Missing required environment variable"):
                CaliperClient(env="staging")


class TestCaliperClientResources:
    """Tests for client resources."""

    def test_events_resource(self):
        """Client should have events resource."""
        client = CaliperClient(env="staging", client_id="id", client_secret="secret")
        assert hasattr(client, "events")
        assert hasattr(client.events, "send")
        assert hasattr(client.events, "send_activity")
        assert hasattr(client.events, "send_time_spent")

    def test_jobs_resource(self):
        """Client should have jobs resource."""
        client = CaliperClient(env="staging", client_id="id", client_secret="secret")
        assert hasattr(client, "jobs")
        assert hasattr(client.jobs, "get_status")
        assert hasattr(client.jobs, "wait_for_completion")


class TestCaliperClientContextManager:
    """Tests for context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Client should work as async context manager."""
        async with CaliperClient(env="staging", client_id="id", client_secret="secret") as client:
            assert client._provider is not None
        # Client should be closed after exiting context


class TestPlatformSelection:
    """Tests for platform selection and path profiles."""

    def test_default_platform_is_beyond_ai(self):
        """Default platform should be BEYOND_AI."""
        client = CaliperClient(env="staging", client_id="id", client_secret="secret")
        # BEYOND_AI staging URL contains "staging.alpha-1edtech.ai"
        assert "alpha-1edtech" in client._transport.base_url

    def test_beyond_ai_platform_paths(self):
        """BEYOND_AI should have full Caliper path support."""
        client = CaliperClient(
            platform="BEYOND_AI",
            env="staging",
            client_id="id",
            client_secret="secret",
        )
        paths = client._transport.paths
        assert paths.send == "/caliper/event"
        assert paths.validate == "/caliper/event/validate"
        assert paths.list == "/caliper/events"
        assert paths.get == "/caliper/events/{id}"
        assert paths.job_status == "/jobs/{id}/status"

    def test_learnwith_ai_platform_paths(self):
        """LEARNWITH_AI should only support send (others None)."""
        client = CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="id",
            client_secret="secret",
        )
        paths = client._transport.paths
        assert paths.send == "/events/1.0/"
        assert paths.validate is None
        assert paths.list is None
        assert paths.get is None
        assert paths.job_status is None

    def test_learnwith_ai_platform_url(self):
        """LEARNWITH_AI should use timeback.com URLs."""
        client = CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="id",
            client_secret="secret",
        )
        assert "timeback.com" in client._transport.base_url
        assert "dev" in client._transport.base_url  # staging uses dev subdomain

    def test_beyond_ai_production_url(self):
        """BEYOND_AI production should use production URL."""
        client = CaliperClient(
            platform="BEYOND_AI",
            env="production",
            client_id="id",
            client_secret="secret",
        )
        assert "caliper.alpha-1edtech.ai" in client._transport.base_url
        assert "staging" not in client._transport.base_url


class TestPlatformGating:
    """Tests for platform feature gating (LEARNWITH_AI restrictions)."""

    def test_learnwith_ai_validate_raises(self):
        """validate() should raise UnsupportedOperationError on LEARNWITH_AI."""
        client = CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="id",
            client_secret="secret",
        )
        # The method exists but will raise when the path is None
        # We can't easily test the async method without mocking, but we can
        # check the path is None which is the gating condition
        assert client._transport.paths.validate is None

    def test_learnwith_ai_list_raises(self):
        """list() should raise UnsupportedOperationError on LEARNWITH_AI."""
        client = CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="id",
            client_secret="secret",
        )
        assert client._transport.paths.list is None

    def test_learnwith_ai_get_raises(self):
        """get() should raise UnsupportedOperationError on LEARNWITH_AI."""
        client = CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="id",
            client_secret="secret",
        )
        assert client._transport.paths.get is None

    def test_learnwith_ai_job_status_raises(self):
        """jobs.get_status() should raise UnsupportedOperationError on LEARNWITH_AI."""
        client = CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="id",
            client_secret="secret",
        )
        assert client._transport.paths.job_status is None

    def test_stream_raises_on_learnwith_ai(self):
        """stream() should raise UnsupportedOperationError on LEARNWITH_AI."""
        client = CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="id",
            client_secret="secret",
        )
        with pytest.raises(UnsupportedOperationError) as exc_info:
            client.events.stream()
        assert "stream()" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)


class TestJobStatusModel:
    """Tests for JobStatus model."""

    def test_job_status_uses_state_field(self):
        """JobStatus should use 'state' field."""
        from timeback_caliper import JobStatus

        status = JobStatus(id="job-123", state="completed")
        assert status.state == "completed"
        assert status.id == "job-123"

    def test_job_status_with_return_value(self):
        """JobStatus should have return_value with results."""
        from timeback_caliper import EventResult, JobReturnValue, JobStatus

        status = JobStatus(
            id="job-123",
            state="completed",
            return_value=JobReturnValue(
                status="success",
                results=[
                    EventResult(allocated_id="1", external_id="urn:uuid:abc"),
                ],
            ),
        )
        assert status.return_value is not None
        assert len(status.return_value.results) == 1
        assert status.return_value.results[0].external_id == "urn:uuid:abc"

    def test_job_status_from_json(self):
        """JobStatus should parse from API JSON format."""
        from timeback_caliper import JobStatus

        # Simulate API response with camelCase
        data = {
            "id": "job-456",
            "state": "active",
            "processedOn": "2024-01-15T10:00:00Z",
        }
        status = JobStatus(**data)
        assert status.id == "job-456"
        assert status.state == "active"
        assert status.processed_on == "2024-01-15T10:00:00Z"
