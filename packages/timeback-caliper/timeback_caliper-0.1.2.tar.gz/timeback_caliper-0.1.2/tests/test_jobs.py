"""Tests for Caliper jobs resource (job status + polling).

Tests job status model parsing and polling logic.
approach of testing models and semantics rather than full HTTP integration.
"""

import inspect

import pytest

from timeback_caliper import EventResult, JobFailedError, JobReturnValue, JobStatus
from timeback_caliper.resources.jobs import JobsResource


class TestJobStatusSchema:
    """Tests for JobStatus model."""

    def test_uses_state_field(self):
        """JobStatus should use 'state' field."""
        status = JobStatus(id="job-123", state="completed")
        assert status.state == "completed"
        assert status.id == "job-123"

    def test_state_values(self):
        """JobStatus state should accept TS-canon values."""
        for state in ["waiting", "active", "completed", "failed"]:
            status = JobStatus(id="job-123", state=state)
            assert status.state == state

    def test_with_return_value(self):
        """JobStatus should have return_value with results array."""
        status = JobStatus(
            id="job-123",
            state="completed",
            return_value=JobReturnValue(
                status="success",
                results=[
                    EventResult(allocated_id="1", external_id="urn:uuid:abc"),
                    EventResult(allocated_id="2", external_id="urn:uuid:def"),
                ],
            ),
        )
        assert status.return_value is not None
        assert len(status.return_value.results) == 2
        assert status.return_value.results[0].external_id == "urn:uuid:abc"
        assert status.return_value.results[1].allocated_id == "2"

    def test_from_api_json_with_camel_case(self):
        """JobStatus should parse from API JSON format with camelCase."""
        data = {
            "id": "job-456",
            "state": "active",
            "processedOn": "2024-01-15T10:00:00Z",
        }
        status = JobStatus(**data)
        assert status.id == "job-456"
        assert status.state == "active"
        assert status.processed_on == "2024-01-15T10:00:00Z"

    def test_optional_fields_default_to_none(self):
        """Optional fields should default to None."""
        status = JobStatus(id="job-123", state="waiting")
        assert status.return_value is None
        assert status.processed_on is None


class TestEventResult:
    """Tests for EventResult model."""

    def test_basic_fields(self):
        """EventResult should have allocated_id and external_id."""
        result = EventResult(allocated_id="123", external_id="urn:uuid:abc")
        assert result.allocated_id == "123"
        assert result.external_id == "urn:uuid:abc"

    def test_from_camel_case(self):
        """EventResult should parse from camelCase JSON."""
        data = {"allocatedId": "123", "externalId": "urn:uuid:abc"}
        result = EventResult(**data)
        assert result.allocated_id == "123"
        assert result.external_id == "urn:uuid:abc"


class TestJobReturnValue:
    """Tests for JobReturnValue model."""

    def test_status_and_results(self):
        """JobReturnValue should have status and results."""
        return_value = JobReturnValue(
            status="success",
            results=[EventResult(allocated_id="1", external_id="urn:uuid:a")],
        )
        assert return_value.status == "success"
        assert len(return_value.results) == 1


class TestWaitForCompletionDefaults:
    """Tests for wait_for_completion default values."""

    def test_default_timeout_matches_ts(self):
        """Default timeout should be 30s."""
        sig = inspect.signature(JobsResource.wait_for_completion)
        timeout_default = sig.parameters["timeout"].default
        assert timeout_default == 30.0

    def test_default_poll_interval_matches_ts(self):
        """Default poll_interval should be 1s."""
        sig = inspect.signature(JobsResource.wait_for_completion)
        poll_interval_default = sig.parameters["poll_interval"].default
        assert poll_interval_default == 1.0


class TestJobFailedError:
    """Tests for JobFailedError."""

    def test_message_includes_job_id(self):
        """Error message should include job ID."""
        error = JobFailedError("job-123")
        assert "job-123" in str(error)

    def test_message_includes_error_detail(self):
        """Error message should include error detail if provided."""
        error = JobFailedError("job-123", error="Validation failed")
        assert "job-123" in str(error)
        assert "Validation failed" in str(error)

    def test_job_id_attribute(self):
        """Error should have job_id attribute."""
        error = JobFailedError("job-123")
        assert error.job_id == "job-123"


class MockTransport:
    """Mock transport for testing job polling logic."""

    def __init__(self, responses: list[dict]):
        """
        Initialize mock transport with predefined responses.

        Args:
            responses: List of job status response dicts to return in order
        """
        self._responses = responses
        self._call_count = 0

        # Provide paths for gating checks
        class MockPaths:
            job_status = "/jobs/{id}/status"

        self.paths = MockPaths()

    async def get(self, _path: str, *, params: dict | None = None) -> dict:
        """Mock GET request that returns next response."""
        del params  # Unused but part of interface
        if self._call_count >= len(self._responses):
            raise RuntimeError("Unexpected request - no more mock responses")
        response = self._responses[self._call_count]
        self._call_count += 1
        return response

    @property
    def call_count(self) -> int:
        return self._call_count


class TestWaitForCompletionLogic:
    """Tests for wait_for_completion polling logic."""

    @pytest.mark.asyncio
    async def test_returns_immediately_on_completed(self):
        """wait_for_completion should return immediately if job is already completed."""
        transport = MockTransport(
            [
                {
                    "job": {
                        "id": "job-123",
                        "state": "completed",
                        "returnValue": {
                            "status": "success",
                            "results": [{"allocatedId": "1", "externalId": "urn:uuid:abc"}],
                        },
                    }
                }
            ]
        )

        jobs = JobsResource(transport)
        status = await jobs.wait_for_completion("job-123")

        assert status.state == "completed"
        assert transport.call_count == 1

    @pytest.mark.asyncio
    async def test_raises_job_failed_error_on_failed(self):
        """wait_for_completion should raise JobFailedError if job fails."""
        transport = MockTransport([{"job": {"id": "job-123", "state": "failed"}}])

        jobs = JobsResource(transport)

        with pytest.raises(JobFailedError) as exc_info:
            await jobs.wait_for_completion("job-123")

        assert "job-123" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_polls_until_completed(self):
        """wait_for_completion should poll until job reaches terminal state."""
        transport = MockTransport(
            [
                {"job": {"id": "job-123", "state": "waiting"}},
                {"job": {"id": "job-123", "state": "active"}},
                {"job": {"id": "job-123", "state": "active"}},
                {"job": {"id": "job-123", "state": "completed"}},
            ]
        )

        jobs = JobsResource(transport)

        # Use short poll interval for faster test
        status = await jobs.wait_for_completion("job-123", poll_interval=0.01)

        assert status.state == "completed"
        assert transport.call_count == 4

    @pytest.mark.asyncio
    async def test_raises_timeout_error(self):
        """wait_for_completion should raise TimeoutError if job doesn't complete."""
        transport = MockTransport(
            [{"job": {"id": "job-123", "state": "active"}} for _ in range(100)]
        )

        jobs = JobsResource(transport)

        with pytest.raises(TimeoutError) as exc_info:
            await jobs.wait_for_completion("job-123", timeout=0.05, poll_interval=0.01)

        assert "job-123" in str(exc_info.value)
        assert "did not complete" in str(exc_info.value)
