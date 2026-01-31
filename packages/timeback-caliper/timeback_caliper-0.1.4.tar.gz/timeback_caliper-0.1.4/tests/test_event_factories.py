"""
Tests for event factory functions.
"""

from __future__ import annotations

from timeback_caliper import (
    CALIPER_DATA_VERSION,
    ActivityCompletedEvent,
    ActivityCompletedInput,
    TimeSpentEvent,
    TimeSpentInput,
    create_activity_event,
    create_time_spent_event,
)
from timeback_caliper.types.timeback import (
    TimebackActivityContext,
    TimebackActivityMetric,
    TimebackApp,
    TimebackUser,
    TimeSpentMetric,
)


class TestCreateActivityEvent:
    """Tests for create_activity_event factory."""

    def test_creates_event_with_required_fields(self) -> None:
        """Creates ActivityCompletedEvent with all required fields."""
        input_data = ActivityCompletedInput(
            actor=TimebackUser(
                id="urn:uuid:user-123",
                email="student@example.edu",
            ),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[
                TimebackActivityMetric(type="totalQuestions", value=10),
                TimebackActivityMetric(type="correctQuestions", value=8),
            ],
        )

        event = create_activity_event(input_data)

        assert isinstance(event, ActivityCompletedEvent)
        assert event.context == CALIPER_DATA_VERSION
        assert event.type == "ActivityEvent"
        assert event.action == "Completed"
        assert event.profile == "TimebackProfile"
        assert event.actor.email == "student@example.edu"
        assert len(event.generated.items) == 2

    def test_auto_generates_event_id(self) -> None:
        """Auto-generates event ID if not provided."""
        input_data = ActivityCompletedInput(
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
        )

        event = create_activity_event(input_data)

        assert event.id.startswith("urn:uuid:")
        assert len(event.id) > 10

    def test_uses_provided_event_id(self) -> None:
        """Uses provided event ID if specified."""
        input_data = ActivityCompletedInput(
            id="urn:uuid:custom-event-id",
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
        )

        event = create_activity_event(input_data)

        assert event.id == "urn:uuid:custom-event-id"

    def test_auto_generates_metrics_id(self) -> None:
        """Auto-generates metrics collection ID if not provided."""
        input_data = ActivityCompletedInput(
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
        )

        event = create_activity_event(input_data)

        assert event.generated.id.startswith("urn:uuid:")

    def test_uses_provided_metrics_id(self) -> None:
        """Uses provided metrics ID if specified."""
        input_data = ActivityCompletedInput(
            metrics_id="urn:uuid:custom-metrics-id",
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
        )

        event = create_activity_event(input_data)

        assert event.generated.id == "urn:uuid:custom-metrics-id"

    def test_auto_generates_event_time(self) -> None:
        """Auto-generates event time if not provided."""
        input_data = ActivityCompletedInput(
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
        )

        event = create_activity_event(input_data)

        # Should be ISO format
        assert "T" in event.event_time

    def test_uses_provided_event_time(self) -> None:
        """Uses provided event time if specified."""
        input_data = ActivityCompletedInput(
            event_time="2024-01-15T10:30:00Z",
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
        )

        event = create_activity_event(input_data)

        assert event.event_time == "2024-01-15T10:30:00Z"

    def test_includes_extensions(self) -> None:
        """Includes extensions if provided."""
        input_data = ActivityCompletedInput(
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
            extensions={"customField": "customValue"},
        )

        event = create_activity_event(input_data)

        assert event.extensions == {"customField": "customValue"}

    def test_includes_attempt_in_generated_when_provided(self) -> None:
        """Includes attempt at generated.attempt (not inside generated.extensions)."""
        input_data = ActivityCompletedInput(
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
            attempt=2,
        )

        event = create_activity_event(input_data)

        assert event.generated.attempt == 2
        assert event.generated.extensions is None


class TestCreateTimeSpentEvent:
    """Tests for create_time_spent_event factory."""

    def test_creates_event_with_required_fields(self) -> None:
        """Creates TimeSpentEvent with all required fields."""
        input_data = TimeSpentInput(
            actor=TimebackUser(
                id="urn:uuid:user-123",
                email="student@example.edu",
            ),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Reading",
                app=TimebackApp(name="My App"),
            ),
            metrics=[
                TimeSpentMetric(type="active", value=1800),
                TimeSpentMetric(type="inactive", value=300),
            ],
        )

        event = create_time_spent_event(input_data)

        assert isinstance(event, TimeSpentEvent)
        assert event.context == CALIPER_DATA_VERSION
        assert event.type == "TimeSpentEvent"
        assert event.action == "SpentTime"
        assert event.profile == "TimebackProfile"
        assert event.actor.email == "student@example.edu"
        assert len(event.generated.items) == 2

    def test_auto_generates_ids(self) -> None:
        """Auto-generates event and metrics IDs if not provided."""
        input_data = TimeSpentInput(
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Reading",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
        )

        event = create_time_spent_event(input_data)

        assert event.id.startswith("urn:uuid:")
        assert event.generated.id.startswith("urn:uuid:")

    def test_uses_provided_ids(self) -> None:
        """Uses provided IDs if specified."""
        input_data = TimeSpentInput(
            id="urn:uuid:my-event",
            metrics_id="urn:uuid:my-metrics",
            actor=TimebackUser(id="urn:uuid:user-123", email="test@example.edu"),
            object=TimebackActivityContext(
                id="urn:uuid:activity-123",
                subject="Reading",
                app=TimebackApp(name="My App"),
            ),
            metrics=[],
        )

        event = create_time_spent_event(input_data)

        assert event.id == "urn:uuid:my-event"
        assert event.generated.id == "urn:uuid:my-metrics"
