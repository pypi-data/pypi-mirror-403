"""Tests for Caliper event models."""

import pytest
from pydantic import ValidationError

from timeback_caliper import (
    ActivityCompletedEvent,
    TimebackActivityContext,
    TimebackActivityMetric,
    TimebackActivityMetricsCollection,
    TimebackApp,
    TimebackTimeSpentMetricsCollection,
    TimebackUser,
    TimeSpentEvent,
    TimeSpentMetric,
)


class TestTimebackUser:
    """Tests for TimebackUser model."""

    def test_minimal_user(self):
        """Minimal user should work."""
        user = TimebackUser(
            id="https://example.edu/users/123",
            email="student@example.edu",
        )
        assert user.id == "https://example.edu/users/123"
        assert user.type == "TimebackUser"
        assert user.email == "student@example.edu"
        assert user.name is None
        assert user.role is None

    def test_full_user(self):
        """Full user with all fields should work."""
        user = TimebackUser(
            id="https://example.edu/users/123",
            email="student@example.edu",
            name="Jane Doe",
            role="student",
        )
        assert user.name == "Jane Doe"
        assert user.role == "student"

    def test_empty_id_rejected(self):
        """Empty id should be rejected."""
        with pytest.raises(ValidationError):
            TimebackUser(id="", email="student@example.edu")


class TestTimebackActivityContext:
    """Tests for TimebackActivityContext model."""

    def test_minimal_context(self):
        """Minimal context should work."""
        context = TimebackActivityContext(
            id="https://myapp.example.com/activities/123",
            subject="Math",
            app=TimebackApp(name="My Learning App"),
        )
        assert context.id == "https://myapp.example.com/activities/123"
        assert context.type == "TimebackActivityContext"
        assert context.subject == "Math"
        assert context.app.name == "My Learning App"

    def test_full_context(self):
        """Full context with all fields should work."""
        context = TimebackActivityContext(
            id="https://myapp.example.com/activities/123",
            subject="Math",
            app=TimebackApp(name="My App", id="https://myapp.example.com"),
        )
        assert context.app.id == "https://myapp.example.com"


class TestTimebackActivityMetric:
    """Tests for TimebackActivityMetric model."""

    def test_metric(self):
        """Metric should work."""
        metric = TimebackActivityMetric(type="correctQuestions", value=8)
        assert metric.type == "correctQuestions"
        assert metric.value == 8

    def test_negative_value_rejected(self):
        """Negative value should be rejected."""
        with pytest.raises(ValidationError):
            TimebackActivityMetric(type="xpEarned", value=-10)


class TestActivityCompletedEvent:
    """Tests for ActivityCompletedEvent model."""

    def test_full_event(self):
        """Full event should work."""
        event = ActivityCompletedEvent(
            id="urn:uuid:123e4567-e89b-12d3-a456-426614174000",
            actor=TimebackUser(
                id="https://example.edu/users/123",
                email="student@example.edu",
            ),
            object=TimebackActivityContext(
                id="https://myapp.example.com/activities/456",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            event_time="2024-01-15T14:30:00Z",
            generated=TimebackActivityMetricsCollection(
                id="urn:uuid:789",
                items=[
                    TimebackActivityMetric(type="totalQuestions", value=10),
                    TimebackActivityMetric(type="correctQuestions", value=8),
                ],
            ),
        )
        assert event.type == "ActivityEvent"
        assert event.action == "Completed"
        assert event.profile == "TimebackProfile"
        assert len(event.generated.items) == 2

    def test_serialization(self):
        """Event should serialize with aliases."""
        event = ActivityCompletedEvent(
            id="urn:uuid:123",
            actor=TimebackUser(id="...", email="a@b.com"),
            object=TimebackActivityContext(
                id="...",
                subject="Math",
                app=TimebackApp(name="App"),
            ),
            event_time="2024-01-15T14:30:00Z",
            generated=TimebackActivityMetricsCollection(
                id="urn:uuid:456",
                items=[TimebackActivityMetric(type="xpEarned", value=100)],
            ),
        )
        data = event.model_dump(mode="json", by_alias=True)
        assert "@context" in data
        assert "eventTime" in data
        assert data["eventTime"] == "2024-01-15T14:30:00Z"


class TestTimeSpentEvent:
    """Tests for TimeSpentEvent model."""

    def test_time_spent_event(self):
        """Time spent event should work."""
        event = TimeSpentEvent(
            id="urn:uuid:123",
            actor=TimebackUser(id="...", email="a@b.com"),
            object=TimebackActivityContext(
                id="...",
                subject="Reading",
                app=TimebackApp(name="App"),
            ),
            event_time="2024-01-15T15:00:00Z",
            generated=TimebackTimeSpentMetricsCollection(
                id="urn:uuid:456",
                items=[
                    TimeSpentMetric(type="active", value=1800),
                    TimeSpentMetric(type="inactive", value=300),
                ],
            ),
        )
        assert event.type == "TimeSpentEvent"
        assert event.action == "SpentTime"
        assert len(event.generated.items) == 2


class TestTimeSpentMetric:
    """Tests for TimeSpentMetric model."""

    def test_metric(self):
        """Metric should work."""
        metric = TimeSpentMetric(
            type="active",
            value=1800,
            start_date="2024-01-15T10:00:00Z",
            end_date="2024-01-15T10:30:00Z",
        )
        assert metric.value == 1800
        assert metric.start_date == "2024-01-15T10:00:00Z"

    def test_value_over_24h_rejected(self):
        """Value over 24 hours (86400s) should be rejected."""
        with pytest.raises(ValidationError):
            TimeSpentMetric(type="active", value=90000)


class TestEventSerializationExcludesNone:
    """Tests that None values are excluded when serializing events.

    The Caliper API rejects null values - fields should be omitted, not set to null.
    This verifies the fix for validation errors like:
    - event.actor.name: Expected string, received null
    - event.actor.extensions: Expected object, received null
    - event.object.extensions: Expected object, received null
    - event.generated.extensions: Expected object, received null
    - event.edApp: edApp must be either a URL string or a valid object
    """

    def test_activity_event_excludes_none_values(self):
        """ActivityCompletedEvent with exclude_none=True should omit None fields."""
        event = ActivityCompletedEvent(
            id="urn:uuid:123e4567-e89b-12d3-a456-426614174000",
            actor=TimebackUser(
                id="https://example.edu/users/123",
                email="student@example.edu",
                # name, role, extensions are None by default
            ),
            object=TimebackActivityContext(
                id="https://myapp.example.com/activities/456",
                subject="Math",
                app=TimebackApp(name="My App"),
                # course, activity, process, extensions are None
            ),
            event_time="2024-01-15T14:30:00Z",
            generated=TimebackActivityMetricsCollection(
                id="urn:uuid:789",
                items=[TimebackActivityMetric(type="correctQuestions", value=8)],
                # extensions is None
            ),
            # ed_app, extensions are None
        )

        # Serialize with exclude_none=True (as events.send() does)
        data = event.model_dump(mode="json", by_alias=True, exclude_none=True)

        # Top-level None fields should be omitted
        assert "edApp" not in data
        assert "extensions" not in data

        # actor.* None fields should be omitted
        assert "name" not in data["actor"]
        assert "role" not in data["actor"]
        assert "extensions" not in data["actor"]

        # object.* None fields should be omitted
        assert "course" not in data["object"]
        assert "activity" not in data["object"]
        assert "process" not in data["object"]
        assert "extensions" not in data["object"]

        # generated.extensions should be omitted
        assert "extensions" not in data["generated"]

        # Required fields should still be present
        assert data["actor"]["id"] == "https://example.edu/users/123"
        assert data["actor"]["email"] == "student@example.edu"
        assert data["object"]["subject"] == "Math"

    def test_time_spent_event_excludes_none_values(self):
        """TimeSpentEvent with exclude_none=True should omit None fields."""
        event = TimeSpentEvent(
            id="urn:uuid:123",
            actor=TimebackUser(
                id="https://example.edu/users/456",
                email="student@example.edu",
            ),
            object=TimebackActivityContext(
                id="https://myapp.example.com/activities/789",
                subject="Reading",
                app=TimebackApp(name="App"),
            ),
            event_time="2024-01-15T15:00:00Z",
            generated=TimebackTimeSpentMetricsCollection(
                id="urn:uuid:456",
                items=[TimeSpentMetric(type="active", value=1800)],
            ),
        )

        data = event.model_dump(mode="json", by_alias=True, exclude_none=True)

        # Top-level None fields should be omitted
        assert "edApp" not in data
        assert "extensions" not in data

        # Nested None fields should be omitted
        assert "name" not in data["actor"]
        assert "extensions" not in data["actor"]
        assert "extensions" not in data["object"]
        assert "extensions" not in data["generated"]

    def test_event_with_values_includes_them(self):
        """When fields have actual values, they should be included."""
        event = ActivityCompletedEvent(
            id="urn:uuid:123",
            actor=TimebackUser(
                id="https://example.edu/users/123",
                email="student@example.edu",
                name="Jane Doe",  # Explicit value
                role="student",  # Explicit value
                extensions={"customField": "value"},  # Explicit value
            ),
            object=TimebackActivityContext(
                id="https://myapp.example.com/activities/456",
                subject="Math",
                app=TimebackApp(name="My App"),
                extensions={"contextData": 123},  # Explicit value
            ),
            event_time="2024-01-15T14:30:00Z",
            generated=TimebackActivityMetricsCollection(
                id="urn:uuid:789",
                items=[TimebackActivityMetric(type="correctQuestions", value=8)],
                extensions={"pctCompleteApp": 0.85},  # Explicit value
            ),
            ed_app="https://myapp.example.com",  # Explicit value
            extensions={"courseId": "course-123"},  # Explicit value
        )

        data = event.model_dump(mode="json", by_alias=True, exclude_none=True)

        # Explicit values should be present
        assert data["edApp"] == "https://myapp.example.com"
        assert data["extensions"] == {"courseId": "course-123"}
        assert data["actor"]["name"] == "Jane Doe"
        assert data["actor"]["role"] == "student"
        assert data["actor"]["extensions"] == {"customField": "value"}
        assert data["object"]["extensions"] == {"contextData": 123}
        assert data["generated"]["extensions"] == {"pctCompleteApp": 0.85}

    def test_without_exclude_none_includes_nulls(self):
        """Without exclude_none=True, None values serialize as null (bad for Caliper API)."""
        event = ActivityCompletedEvent(
            id="urn:uuid:123",
            actor=TimebackUser(id="...", email="a@b.com"),
            object=TimebackActivityContext(id="...", subject="Math", app=TimebackApp(name="App")),
            event_time="2024-01-15T14:30:00Z",
            generated=TimebackActivityMetricsCollection(
                id="urn:uuid:456",
                items=[TimebackActivityMetric(type="xpEarned", value=100)],
            ),
        )

        # Without exclude_none=True (would cause Caliper API validation errors)
        data_with_nulls = event.model_dump(mode="json", by_alias=True)

        # These would be null in the JSON, causing Caliper API to reject
        assert data_with_nulls["edApp"] is None
        assert data_with_nulls["extensions"] is None
        assert data_with_nulls["actor"]["name"] is None
        assert data_with_nulls["actor"]["extensions"] is None

        # With exclude_none=True (correct for Caliper API)
        data_clean = event.model_dump(mode="json", by_alias=True, exclude_none=True)

        # These fields should be omitted entirely
        assert "edApp" not in data_clean
        assert "extensions" not in data_clean
        assert "name" not in data_clean["actor"]
        assert "extensions" not in data_clean["actor"]
