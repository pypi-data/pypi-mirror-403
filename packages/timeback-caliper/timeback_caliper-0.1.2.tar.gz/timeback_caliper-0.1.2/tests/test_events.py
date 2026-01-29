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
