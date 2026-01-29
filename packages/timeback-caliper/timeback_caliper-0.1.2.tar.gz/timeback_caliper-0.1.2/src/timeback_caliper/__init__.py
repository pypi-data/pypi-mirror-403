"""
Timeback Caliper Client

A Python client for sending Caliper learning analytics events to Timeback.

Example:
    ```python
    from timeback_caliper import CaliperClient, ActivityCompletedInput

    async def main():
        client = CaliperClient(
            env="staging",
            client_id="your-client-id",
            client_secret="your-client-secret",
        )

        result = await client.events.send_activity(
            sensor_id="https://myapp.example.com/sensors/main",
            input=ActivityCompletedInput(
                actor=TimebackUser(id="...", email="student@example.edu"),
                object=TimebackActivityContext(
                    id="...",
                    subject="Math",
                    app=TimebackApp(name="My Learning App"),
                ),
                metrics=[
                    TimebackActivityMetric(type="totalQuestions", value=10),
                    TimebackActivityMetric(type="correctQuestions", value=8),
                ],
            ),
        )

        # Wait for processing
        status = await client.jobs.wait_for_completion(result.job_id)

        # List events
        result = await client.events.list(start_date="2024-01-01")

        # Stream events with pagination
        async for event in client.events.stream(start_date="2024-01-01"):
            print(event.id)
    ```
"""

from .client import CaliperClient
from .constants import CALIPER_DATA_VERSION
from .event_factories import create_activity_event, create_time_spent_event
from .exceptions import (
    APIError,
    AuthenticationError,
    JobFailedError,
    TimebackError,
    UnsupportedOperationError,
    ValidationError,
)
from .types import (
    ActivityCompletedEvent,
    ActivityCompletedInput,
    ActivityMetricType,
    CaliperEnvelope,
    EventResult,
    JobReturnValue,
    JobStatus,
    ListEventsResult,
    Pagination,
    SendEventsResult,
    StoredEvent,
    TimebackActivity,
    TimebackActivityContext,
    TimebackActivityMetric,
    TimebackActivityMetricsCollection,
    TimebackApp,
    TimebackCourse,
    TimebackEvent,
    TimebackSubject,
    TimebackTimeSpentMetricsCollection,
    TimebackUser,
    TimebackUserRole,
    TimeSpentEvent,
    TimeSpentInput,
    TimeSpentMetric,
    TimeSpentMetricType,
    ValidationResult,
)

__all__ = [
    "CALIPER_DATA_VERSION",
    "APIError",
    "ActivityCompletedEvent",
    "ActivityCompletedInput",
    "ActivityMetricType",
    "AuthenticationError",
    "CaliperClient",
    "CaliperEnvelope",
    "EventResult",
    "JobFailedError",
    "JobReturnValue",
    "JobStatus",
    "ListEventsResult",
    "Pagination",
    "SendEventsResult",
    "StoredEvent",
    "TimeSpentEvent",
    "TimeSpentInput",
    "TimeSpentMetric",
    "TimeSpentMetricType",
    "TimebackActivity",
    "TimebackActivityContext",
    "TimebackActivityMetric",
    "TimebackActivityMetricsCollection",
    "TimebackApp",
    "TimebackCourse",
    "TimebackError",
    "TimebackEvent",
    "TimebackSubject",
    "TimebackTimeSpentMetricsCollection",
    "TimebackUser",
    "TimebackUserRole",
    "UnsupportedOperationError",
    "ValidationError",
    "ValidationResult",
    # Event factories
    "create_activity_event",
    "create_time_spent_event",
]

__version__ = "0.1.0"
