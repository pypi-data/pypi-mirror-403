"""
API Response Types

Types for Caliper API responses.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# SEND EVENTS
# ═══════════════════════════════════════════════════════════════════════════════


class SendEventsResult(BaseModel):
    """Result from sending events."""

    job_id: str = Field(alias="jobId")
    """Job ID for tracking async processing."""

    events_accepted: int = Field(default=0, alias="eventsAccepted")
    """Number of events accepted for processing."""

    model_config = {"populate_by_name": True}


# ═══════════════════════════════════════════════════════════════════════════════
# JOB STATUS
# ═══════════════════════════════════════════════════════════════════════════════


class EventResult(BaseModel):
    """Individual event result from job completion."""

    allocated_id: str = Field(alias="allocatedId")
    """Internal ID allocated by the database."""

    external_id: str = Field(alias="externalId")
    """External event ID (URN UUID)."""

    model_config = {"populate_by_name": True}


class JobReturnValue(BaseModel):
    """Return value from a completed job."""

    status: Literal["success", "error"]
    """Overall job status."""

    results: list[EventResult] = Field(default_factory=list)
    """Individual event processing results."""

    model_config = {"populate_by_name": True}


class JobStatus(BaseModel):
    """
    Status of an async processing job.

    Uses state-based semantics (waiting, active, completed, failed).
    """

    id: str
    """Job ID."""

    state: Literal["waiting", "active", "completed", "failed"]
    """Current job state."""

    return_value: JobReturnValue | None = Field(default=None, alias="returnValue")
    """Return value on completion (contains results array)."""

    processed_on: str | None = Field(default=None, alias="processedOn")
    """Timestamp when job was processed."""

    model_config = {"populate_by_name": True}


# ═══════════════════════════════════════════════════════════════════════════════
# STORED EVENT
# ═══════════════════════════════════════════════════════════════════════════════

# Caliper entity can be a URI string or an object with properties
CaliperEntity = str | dict[str, Any] | None


class StoredEvent(BaseModel):
    """
    A stored Caliper event as returned by the API.

    The API adds internal fields and transforms the original event ID to `external_id`.
    """

    id: int
    """Internal numeric ID (allocated by the database)."""

    external_id: str = Field(alias="externalId")
    """Original event ID (URN UUID format) - use this for get() calls."""

    sensor: str
    """Sensor that sent the event."""

    type: str
    """Event type (e.g., 'ActivityEvent', 'Event')."""

    profile: str | None = None
    """Caliper profile (e.g., 'TimebackProfile')."""

    action: str
    """The action or predicate."""

    event_time: str = Field(alias="eventTime")
    """When the event occurred."""

    send_time: str = Field(alias="sendTime")
    """When the event was sent."""

    updated_at: str | None = Field(default=None, alias="updated_at")
    """When the record was last updated."""

    created_at: str = Field(alias="created_at")
    """When the record was created."""

    deleted_at: str | None = Field(default=None, alias="deleted_at")
    """When the record was deleted (soft delete)."""

    actor: CaliperEntity = None
    """The agent who initiated the event."""

    object: CaliperEntity = None
    """The object of the event."""

    generated: CaliperEntity = None
    """Generated entity (e.g., result, score)."""

    target: CaliperEntity = None
    """Target entity."""

    referrer: CaliperEntity = None
    """Referrer entity."""

    ed_app: CaliperEntity = Field(default=None, alias="edApp")
    """EdApp entity."""

    group: CaliperEntity = None
    """Group/organization entity."""

    membership: CaliperEntity = None
    """Membership entity."""

    session: CaliperEntity = None
    """Session entity."""

    federated_session: CaliperEntity = Field(default=None, alias="federatedSession")
    """Federated session entity."""

    extensions: dict[str, Any] | None = None
    """Extension data."""

    client_app_id: str | None = Field(default=None, alias="clientAppId")
    """Client application ID."""

    model_config = {"populate_by_name": True}


# ═══════════════════════════════════════════════════════════════════════════════
# PAGINATION
# ═══════════════════════════════════════════════════════════════════════════════


class Pagination(BaseModel):
    """Pagination metadata from list responses."""

    total: int
    """Total number of items."""

    total_pages: int = Field(alias="totalPages")
    """Total number of pages."""

    current_page: int = Field(alias="currentPage")
    """Current page number."""

    limit: int
    """Items per page."""

    model_config = {"populate_by_name": True}


class ListEventsResult(BaseModel):
    """Result from listing events."""

    events: list[StoredEvent]
    """List of stored events."""

    pagination: Pagination
    """Pagination metadata."""


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


class ValidationResult(BaseModel):
    """Result from validating events."""

    status: Literal["success", "error"]
    """Validation status."""

    message: str | None = None
    """Human-readable message."""

    errors: list[dict[str, Any]] | None = None
    """List of validation errors (if status is error)."""


# ═══════════════════════════════════════════════════════════════════════════════
# ENVELOPE
# ═══════════════════════════════════════════════════════════════════════════════


class CaliperEnvelope(BaseModel):
    """Caliper envelope for sending events."""

    sensor: str
    """Sensor identifier (IRI format)."""

    send_time: str = Field(alias="sendTime")
    """ISO 8601 datetime when data was sent."""

    data_version: str = Field(alias="dataVersion")
    """Caliper data version."""

    data: list[dict[str, Any]]
    """Array of events."""

    model_config = {"populate_by_name": True}
