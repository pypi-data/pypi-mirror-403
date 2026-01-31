"""
Jobs Resource

Methods for tracking async processing jobs.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from urllib.parse import quote

from ..exceptions import JobFailedError, UnsupportedOperationError
from ..types.api import JobStatus

if TYPE_CHECKING:
    from ..lib.transport import Transport


class JobsResource:
    """
    Jobs resource for tracking async event processing.

    Access via `client.jobs`.

    Note:
        Job tracking is only available on the BEYOND_AI platform.

    Example:
        ```python
        status = await client.jobs.get_status(job_id)
        if status.state == "completed":
            print(f"Processed {len(status.return_value.results)} events")
        ```
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def get_status(self, job_id: str) -> JobStatus:
        """
        Get the status of a processing job.

        Note:
            This operation is only available on the BEYOND_AI platform.

        Args:
            job_id: Job identifier from send_events result

        Returns:
            Current job status

        Raises:
            UnsupportedOperationError: If not supported on current platform
        """
        job_status_path = self._transport.paths.job_status
        if job_status_path is None:
            raise UnsupportedOperationError("get_status")

        # Use {id} template like TS does
        path = job_status_path.replace("{id}", quote(job_id, safe=""))
        response = await self._transport.get(path)

        # Handle nested "job" key in response
        job_data = response.get("job", response)
        return JobStatus(**job_data)

    async def wait_for_completion(
        self,
        job_id: str,
        *,
        timeout: float = 30.0,
        poll_interval: float = 1.0,
    ) -> JobStatus:
        """
        Wait for a job to complete.

        Polls the job status until it reaches a terminal state.

        Note:
            This operation is only available on the BEYOND_AI platform.

        Args:
            job_id: Job identifier from send_events result
            timeout: Maximum time to wait in seconds (default: 30s)
            poll_interval: Time between status checks in seconds (default: 1s)

        Returns:
            Final job status (only on success)

        Raises:
            UnsupportedOperationError: If not supported on current platform
            JobFailedError: If job fails
            TimeoutError: If job doesn't complete within timeout

        Example:
            ```python
            result = await client.events.send_activity(sensor_id, input)
            try:
                status = await client.jobs.wait_for_completion(result.job_id)
                print(f"Success! Results: {status.return_value.results}")
            except JobFailedError as e:
                print(f"Job failed: {e}")
            ```
        """
        # Check platform support upfront
        if self._transport.paths.job_status is None:
            raise UnsupportedOperationError("wait_for_completion")

        elapsed = 0.0
        while elapsed < timeout:
            status = await self.get_status(job_id)

            # Uses `state` field with values: waiting, active, completed, failed
            if status.state == "completed":
                return status

            if status.state == "failed":
                raise JobFailedError(job_id)

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")
