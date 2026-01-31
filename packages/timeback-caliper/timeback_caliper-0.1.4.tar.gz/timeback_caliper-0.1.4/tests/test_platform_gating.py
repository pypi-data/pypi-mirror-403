"""Tests for platform gating (LEARNWITH_AI vs BEYOND_AI).

Tests that platform-specific features are correctly gated at path level,
using path profiles and client construction rather than HTTP-level mocking.
"""

import pytest

from timeback_caliper import CaliperClient, UnsupportedOperationError
from timeback_caliper.types.api import CaliperEnvelope


class TestBeyondAIPlatformPaths:
    """Tests that BEYOND_AI has full path support."""

    @pytest.fixture
    def client(self) -> CaliperClient:
        """Create a BEYOND_AI client for testing."""
        return CaliperClient(
            platform="BEYOND_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

    def test_send_path_available(self, client: CaliperClient):
        """BEYOND_AI should have send path."""
        assert client._transport.paths.send == "/caliper/event"

    def test_validate_path_available(self, client: CaliperClient):
        """BEYOND_AI should have validate path."""
        assert client._transport.paths.validate == "/caliper/event/validate"

    def test_list_path_available(self, client: CaliperClient):
        """BEYOND_AI should have list path."""
        assert client._transport.paths.list == "/caliper/events"

    def test_get_path_available(self, client: CaliperClient):
        """BEYOND_AI should have get path with {id} template."""
        assert client._transport.paths.get == "/caliper/events/{id}"

    def test_job_status_path_available(self, client: CaliperClient):
        """BEYOND_AI should have job_status path with {id} template."""
        assert client._transport.paths.job_status == "/jobs/{id}/status"


class TestLearnWithAIPlatformPaths:
    """Tests that LEARNWITH_AI only supports send (others None)."""

    @pytest.fixture
    def client(self) -> CaliperClient:
        """Create a LEARNWITH_AI client for testing."""
        return CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

    def test_send_path_available(self, client: CaliperClient):
        """LEARNWITH_AI should have send path."""
        assert client._transport.paths.send == "/events/1.0/"

    def test_validate_path_none(self, client: CaliperClient):
        """LEARNWITH_AI should have None for validate path."""
        assert client._transport.paths.validate is None

    def test_list_path_none(self, client: CaliperClient):
        """LEARNWITH_AI should have None for list path."""
        assert client._transport.paths.list is None

    def test_get_path_none(self, client: CaliperClient):
        """LEARNWITH_AI should have None for get path."""
        assert client._transport.paths.get is None

    def test_job_status_path_none(self, client: CaliperClient):
        """LEARNWITH_AI should have None for job_status path."""
        assert client._transport.paths.job_status is None


class TestLearnWithAIPlatformGating:
    """Tests that LEARNWITH_AI raises UnsupportedOperationError for unsupported operations."""

    @pytest.fixture
    def client(self) -> CaliperClient:
        """Create a LEARNWITH_AI client for testing."""
        return CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

    def test_stream_raises_unsupported(self, client: CaliperClient):
        """stream() should raise UnsupportedOperationError on LEARNWITH_AI."""
        with pytest.raises(UnsupportedOperationError) as exc_info:
            client.events.stream()

        assert "stream()" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_raises_unsupported(self, client: CaliperClient):
        """validate() should raise UnsupportedOperationError on LEARNWITH_AI."""
        envelope = CaliperEnvelope(
            sensor="https://example.edu/sensors/1",
            send_time="2024-01-15T10:00:00Z",
            data_version="http://purl.imsglobal.org/ctx/caliper/v1p2",
            data=[],
        )

        with pytest.raises(UnsupportedOperationError) as exc_info:
            await client.events.validate(envelope)

        assert "validate()" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_raises_unsupported(self, client: CaliperClient):
        """list() should raise UnsupportedOperationError on LEARNWITH_AI."""
        with pytest.raises(UnsupportedOperationError) as exc_info:
            await client.events.list()

        assert "list()" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_raises_unsupported(self, client: CaliperClient):
        """get() should raise UnsupportedOperationError on LEARNWITH_AI."""
        with pytest.raises(UnsupportedOperationError) as exc_info:
            await client.events.get("urn:uuid:test-id")

        assert "get()" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_jobs_get_status_raises_unsupported(self, client: CaliperClient):
        """jobs.get_status() should raise UnsupportedOperationError on LEARNWITH_AI."""
        with pytest.raises(UnsupportedOperationError) as exc_info:
            await client.jobs.get_status("job-123")

        assert "get_status()" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_jobs_wait_for_completion_raises_unsupported(self, client: CaliperClient):
        """jobs.wait_for_completion() should raise UnsupportedOperationError on LEARNWITH_AI."""
        with pytest.raises(UnsupportedOperationError) as exc_info:
            await client.jobs.wait_for_completion("job-123")

        assert "wait_for_completion()" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)


class TestUnsupportedOperationError:
    """Tests for UnsupportedOperationError formatting."""

    def test_error_message_format(self):
        """Error message should include operation name and 'not supported'."""
        error = UnsupportedOperationError("validate")
        assert "validate()" in str(error)
        assert "not supported" in str(error)

    def test_error_inherits_from_api_error(self):
        """UnsupportedOperationError should inherit from APIError."""
        from timeback_caliper import APIError

        error = UnsupportedOperationError("test")
        assert isinstance(error, APIError)

    def test_error_has_none_status_code(self):
        """UnsupportedOperationError should have None status_code (not HTTP error)."""
        error = UnsupportedOperationError("test")
        assert error.status_code is None


class TestPlatformClientConstruction:
    """Tests for platform-based client construction."""

    def test_succeeds_with_beyond_ai_platform(self):
        """Client should construct successfully with BEYOND_AI platform."""
        client = CaliperClient(
            platform="BEYOND_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert client._transport.paths.send is not None

    def test_succeeds_with_learnwith_ai_platform(self):
        """Client should construct successfully with LEARNWITH_AI platform."""
        client = CaliperClient(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert client._transport.paths.send is not None

    def test_succeeds_with_default_platform(self):
        """Client should construct successfully with default platform (BEYOND_AI)."""
        client = CaliperClient(
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )
        # Default is BEYOND_AI
        assert "alpha-1edtech" in client._transport.base_url

    def test_succeeds_with_custom_provider(self):
        """Client should construct successfully with custom base URL."""
        client = CaliperClient(
            base_url="https://custom.api.com",
            auth_url="https://custom.auth.com/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert client._transport.base_url == "https://custom.api.com"
