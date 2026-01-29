"""
Timeback Caliper Types

Type definitions for the Caliper client.
"""

from .api import (
    CaliperEnvelope,
    EventResult,
    JobReturnValue,
    JobStatus,
    ListEventsResult,
    Pagination,
    SendEventsResult,
    StoredEvent,
    ValidationResult,
)
from .client import CaliperClientConfig, EnvAuth, Environment, ExplicitAuth
from .timeback import (
    ActivityCompletedEvent,
    ActivityCompletedInput,
    ActivityMetricType,
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
)

__all__ = [
    "ActivityCompletedEvent",
    "ActivityCompletedInput",
    "ActivityMetricType",
    "CaliperClientConfig",
    "CaliperEnvelope",
    "EnvAuth",
    "Environment",
    "EventResult",
    "ExplicitAuth",
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
    "TimebackEvent",
    "TimebackSubject",
    "TimebackTimeSpentMetricsCollection",
    "TimebackUser",
    "TimebackUserRole",
    "ValidationResult",
]
