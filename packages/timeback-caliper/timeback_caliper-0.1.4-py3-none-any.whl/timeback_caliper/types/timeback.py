"""
Timeback Profile Types

First-class types for the Timeback Caliper profile, including
ActivityCompletedEvent and TimeSpentEvent.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..constants import CALIPER_DATA_VERSION

# ═══════════════════════════════════════════════════════════════════════════════
# TIMEBACK USER
# ═══════════════════════════════════════════════════════════════════════════════

TimebackUserRole = Literal["student", "teacher", "admin", "guide"]


class TimebackUser(BaseModel):
    """
    Timeback user entity.

    Represents a user in the Timeback platform. The `id` should ideally be
    the OneRoster URL for the user when available.

    Example:
        ```python
        user = TimebackUser(
            id="https://api.alpha-1edtech.ai/ims/oneroster/rostering/v1p2/users/123",
            type="TimebackUser",
            email="student@example.edu",
            name="Jane Doe",
            role="student",
        )
        ```
    """

    id: str = Field(..., min_length=1, description="User identifier (IRI format)")
    type: Literal["TimebackUser"] = "TimebackUser"
    email: str = Field(..., min_length=1)
    name: str | None = None
    role: TimebackUserRole | None = None
    extensions: dict[str, object] | None = None

    model_config = {"extra": "allow"}


# ═══════════════════════════════════════════════════════════════════════════════
# TIMEBACK ACTIVITY CONTEXT
# ═══════════════════════════════════════════════════════════════════════════════

TimebackSubject = Literal[
    "Reading",
    "Language",
    "Vocabulary",
    "Social Studies",
    "Writing",
    "Science",
    "FastMath",
    "Math",
    "None",
    "Other",
]


class TimebackApp(BaseModel):
    """Application reference within activity context."""

    id: str | None = None
    name: str = Field(..., min_length=1)
    extensions: dict[str, object] | None = None


class TimebackCourse(BaseModel):
    """Course reference within activity context."""

    id: str | None = None
    name: str = Field(..., min_length=1)
    extensions: dict[str, object] | None = None


class TimebackActivity(BaseModel):
    """Activity reference within activity context."""

    id: str | None = None
    name: str = Field(..., min_length=1)
    extensions: dict[str, object] | None = None


class TimebackActivityContext(BaseModel):
    """
    Timeback activity context.

    Represents the context where an event was recorded, including
    subject, application, course, and activity information.

    Example:
        ```python
        context = TimebackActivityContext(
            id="https://myapp.example.com/activities/123",
            type="TimebackActivityContext",
            subject="Math",
            app=TimebackApp(name="My Learning App"),
            course=TimebackCourse(name="Algebra 101"),
        )
        ```
    """

    id: str = Field(..., min_length=1)
    type: Literal["TimebackActivityContext"] = "TimebackActivityContext"
    subject: TimebackSubject
    app: TimebackApp
    course: TimebackCourse | None = None
    activity: TimebackActivity | None = None
    process: bool | None = None
    extensions: dict[str, object] | None = None

    model_config = {"extra": "allow"}


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVITY METRICS
# ═══════════════════════════════════════════════════════════════════════════════

ActivityMetricType = Literal["xpEarned", "totalQuestions", "correctQuestions", "masteredUnits"]


class TimebackActivityMetric(BaseModel):
    """
    Individual activity metric.

    Example:
        ```python
        metric = TimebackActivityMetric(type="correctQuestions", value=8)
        metric_xp = TimebackActivityMetric(type="xpEarned", value=1.5)
        ```
    """

    type: ActivityMetricType
    value: int | float = Field(..., ge=0)
    extensions: dict[str, object] | None = None


class TimebackActivityMetricsCollection(BaseModel):
    """Collection of activity metrics."""

    id: str = Field(..., min_length=1)
    type: Literal["TimebackActivityMetricsCollection"] = "TimebackActivityMetricsCollection"
    items: list[TimebackActivityMetric]
    attempt: int | None = Field(default=None, ge=1)
    extensions: dict[str, object] | None = None

    model_config = {"extra": "allow"}


# ═══════════════════════════════════════════════════════════════════════════════
# TIME SPENT METRICS
# ═══════════════════════════════════════════════════════════════════════════════

TimeSpentMetricType = Literal["active", "inactive", "waste", "unknown", "anti-pattern"]


class TimeSpentMetric(BaseModel):
    """
    Individual time spent metric.

    Example:
        ```python
        metric = TimeSpentMetric(
            type="active",
            value=1800,  # 30 minutes in seconds
            start_date="2024-01-15T10:00:00Z",
            end_date="2024-01-15T10:30:00Z",
        )
        ```
    """

    type: TimeSpentMetricType
    value: int | float = Field(..., ge=0, le=86400, description="Time in seconds (max 24h)")
    sub_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    extensions: dict[str, object] | None = None


class TimebackTimeSpentMetricsCollection(BaseModel):
    """Collection of time spent metrics."""

    id: str = Field(..., min_length=1)
    type: Literal["TimebackTimeSpentMetricsCollection"] = "TimebackTimeSpentMetricsCollection"
    items: list[TimeSpentMetric]
    extensions: dict[str, object] | None = None

    model_config = {"extra": "allow"}


# ═══════════════════════════════════════════════════════════════════════════════
# TIMEBACK EVENTS
# ═══════════════════════════════════════════════════════════════════════════════


class ActivityCompletedEvent(BaseModel):
    """
    Timeback Activity Completed Event.

    Records when a student completes an activity, along with performance metrics.
    """

    context: str = Field(default=CALIPER_DATA_VERSION, alias="@context")
    id: str = Field(..., min_length=1, description="URN UUID format")
    type: Literal["ActivityEvent"] = "ActivityEvent"
    action: Literal["Completed"] = "Completed"
    actor: TimebackUser
    object: TimebackActivityContext
    event_time: str = Field(..., alias="eventTime")
    profile: Literal["TimebackProfile"] = "TimebackProfile"
    generated: TimebackActivityMetricsCollection
    ed_app: str | dict[str, object] | None = Field(default=None, alias="edApp")
    extensions: dict[str, object] | None = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class TimeSpentEvent(BaseModel):
    """
    Timeback Time Spent Event.

    Records time spent on an activity, categorized by engagement type.
    """

    context: str = Field(default=CALIPER_DATA_VERSION, alias="@context")
    id: str = Field(..., min_length=1)
    type: Literal["TimeSpentEvent"] = "TimeSpentEvent"
    action: Literal["SpentTime"] = "SpentTime"
    actor: TimebackUser
    object: TimebackActivityContext
    event_time: str = Field(..., alias="eventTime")
    profile: Literal["TimebackProfile"] = "TimebackProfile"
    generated: TimebackTimeSpentMetricsCollection
    ed_app: str | dict[str, object] | None = Field(default=None, alias="edApp")
    extensions: dict[str, object] | None = None

    model_config = {"populate_by_name": True, "extra": "allow"}


TimebackEvent = ActivityCompletedEvent | TimeSpentEvent


# ═══════════════════════════════════════════════════════════════════════════════
# BUILDER INPUT TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class ActivityCompletedInput(BaseModel):
    """
    Input for creating an ActivityCompletedEvent.

    Omits fields that are auto-generated (id, eventTime, @context, profile).
    """

    actor: TimebackUser
    object: TimebackActivityContext
    metrics: list[TimebackActivityMetric]
    # Surfaces at `event.generated.attempt`
    attempt: int | None = Field(default=None, ge=1)
    event_time: str | None = None
    metrics_id: str | None = None
    id: str | None = None
    extensions: dict[str, object] | None = None
    generated_extensions: dict[str, object] | None = None


class TimeSpentInput(BaseModel):
    """
    Input for creating a TimeSpentEvent.

    Omits fields that are auto-generated (id, eventTime, @context, profile).
    """

    actor: TimebackUser
    object: TimebackActivityContext
    metrics: list[TimeSpentMetric]
    event_time: str | None = None
    metrics_id: str | None = None
    id: str | None = None
    extensions: dict[str, object] | None = None
