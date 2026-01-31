"""
Event Factory Functions

Pure factory functions for creating Timeback profile events.
Use these when you want to batch multiple events into a single envelope.
"""

from __future__ import annotations

import uuid

from timeback_common import utc_iso_timestamp

from .types.timeback import (
    ActivityCompletedEvent,
    ActivityCompletedInput,
    TimebackActivityMetricsCollection,
    TimebackTimeSpentMetricsCollection,
    TimeSpentEvent,
    TimeSpentInput,
)


def create_activity_event(input: ActivityCompletedInput) -> ActivityCompletedEvent:
    """
    Create an ActivityEvent from input.

    Pure factory function - creates the event object without sending.
    Use this when you want to batch multiple events into a single envelope.

    Args:
        input: Activity completion data

    Returns:
        A fully-formed ActivityCompletedEvent ready to send

    Example:
        ```python
        from timeback_caliper import create_activity_event, create_time_spent_event

        activity_event = create_activity_event(ActivityCompletedInput(
            actor=TimebackUser(id="...", type="TimebackUser", email="student@example.edu"),
            object=TimebackActivityContext(
                id="...",
                type="TimebackActivityContext",
                subject="Math",
                app=TimebackApp(name="My App"),
            ),
            metrics=[
                TimebackActivityMetric(type="totalQuestions", value=10),
                TimebackActivityMetric(type="correctQuestions", value=8),
            ],
        ))

        time_spent_event = create_time_spent_event(TimeSpentInput(
            actor=TimebackUser(id="...", type="TimebackUser", email="student@example.edu"),
            object=TimebackActivityContext(...),
            metrics=[TimeSpentMetric(type="active", value=1800)],
        ))

        # Send both in one envelope
        await client.events.send(sensor, [activity_event, time_spent_event])
        ```
    """
    event_id = input.id or f"urn:uuid:{uuid.uuid4()}"
    metrics_id = input.metrics_id or f"urn:uuid:{uuid.uuid4()}"

    return ActivityCompletedEvent(
        id=event_id,
        actor=input.actor,
        object=input.object,
        eventTime=input.event_time or utc_iso_timestamp(),
        generated=TimebackActivityMetricsCollection(
            id=metrics_id,
            items=input.metrics,
            attempt=input.attempt,
            extensions=input.generated_extensions,
        ),
        extensions=input.extensions,
    )


def create_time_spent_event(input: TimeSpentInput) -> TimeSpentEvent:
    """
    Create a TimeSpentEvent from input.

    Pure factory function - creates the event object without sending.
    Use this when you want to batch multiple events into a single envelope.

    Args:
        input: Time spent data

    Returns:
        A fully-formed TimeSpentEvent ready to send

    Example:
        ```python
        from timeback_caliper import create_time_spent_event

        event = create_time_spent_event(TimeSpentInput(
            actor=TimebackUser(id="...", type="TimebackUser", email="student@example.edu"),
            object=TimebackActivityContext(
                id="...",
                type="TimebackActivityContext",
                subject="Reading",
                app=TimebackApp(name="My App"),
            ),
            metrics=[
                TimeSpentMetric(type="active", value=1800),
                TimeSpentMetric(type="inactive", value=300),
            ],
        ))

        await client.events.send(sensor, [event])
        ```
    """
    event_id = input.id or f"urn:uuid:{uuid.uuid4()}"
    metrics_id = input.metrics_id or f"urn:uuid:{uuid.uuid4()}"

    return TimeSpentEvent(
        id=event_id,
        actor=input.actor,
        object=input.object,
        eventTime=input.event_time or utc_iso_timestamp(),
        generated=TimebackTimeSpentMetricsCollection(
            id=metrics_id,
            items=input.metrics,
        ),
        extensions=input.extensions,
    )


__all__ = [
    "create_activity_event",
    "create_time_spent_event",
]
