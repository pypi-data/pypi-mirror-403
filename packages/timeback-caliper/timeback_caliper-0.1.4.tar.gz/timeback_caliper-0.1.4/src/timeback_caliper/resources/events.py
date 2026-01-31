"""
Events Resource

Methods for sending and retrieving Caliper events.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from timeback_common import (
    PageResult,
    utc_iso_timestamp,
    validate_non_empty_string,
    validate_offset_list_params,
)

from ..constants import CALIPER_DATA_VERSION
from ..exceptions import APIError, UnsupportedOperationError
from ..types.api import (
    CaliperEnvelope,
    ListEventsResult,
    Pagination,
    SendEventsResult,
    StoredEvent,
    ValidationResult,
)
from ..types.timeback import (
    ActivityCompletedEvent,
    ActivityCompletedInput,
    TimebackActivityMetricsCollection,
    TimebackEvent,
    TimebackTimeSpentMetricsCollection,
    TimeSpentEvent,
    TimeSpentInput,
)

if TYPE_CHECKING:
    from ..lib.transport import Transport

# Default max items for to_array() safety guard (same as common paginator)
DEFAULT_MAX_ITEMS = 10_000


class EventsPaginator(AsyncIterator[StoredEvent]):
    """
    Async iterator for paginated events.

    Lazily fetches pages as you iterate.

    Example:
        ```python
        # Iterate over all events
        async for event in client.events.stream(start_date="2024-01-01"):
            print(event.id)

        # Collect into a list
        events = await client.events.stream(start_date="2024-01-01").to_list()

        # With safety guard
        events = await client.events.stream(start_date="2024-01-01").to_array(max_items=5000)

        # Get first page with metadata
        page = await client.events.stream(start_date="2024-01-01").first_page()
        print(f"Got {len(page.data)} of {page.total} events")
        ```
    """

    def __init__(
        self,
        transport: Transport,
        path: str,
        params: dict[str, Any],
        limit: int = 100,
        max_items: int | None = None,
        offset: int = 0,
    ) -> None:
        self._transport = transport
        self._path = path
        self._params = params
        self._limit = limit
        self._max_items = max_items
        self._initial_offset = offset
        self._offset = offset
        self._buffer: list[StoredEvent] = []
        self._exhausted = False
        self._items_yielded = 0
        self._total: int | None = None

    def __aiter__(self) -> EventsPaginator:
        return self

    async def __anext__(self) -> StoredEvent:
        # Check max items limit
        if self._max_items is not None and self._items_yielded >= self._max_items:
            raise StopAsyncIteration

        # Refill buffer if empty
        if not self._buffer and not self._exhausted:
            await self._fetch_page()

        if not self._buffer:
            raise StopAsyncIteration

        event = self._buffer.pop(0)
        self._items_yielded += 1
        return event

    async def _fetch_page(self) -> tuple[list[StoredEvent], int | None]:
        """Fetch the next page of results and return items + total."""
        params = {**self._params, "limit": self._limit, "offset": self._offset}

        response = await self._transport.get(self._path, params=params)

        events_data = response.get("events", [])
        items = [StoredEvent(**e) for e in events_data]
        self._buffer = items

        pagination = response.get("pagination", {})
        self._total = pagination.get("total", 0)

        # Increment offset by actual items returned, not by limit
        items_returned = len(self._buffer)
        self._offset += items_returned

        # hasMore = offset + items.length < total (or empty response)
        if items_returned == 0 or self._offset >= (self._total or 0):
            self._exhausted = True

        return items, self._total

    async def to_list(self) -> list[StoredEvent]:
        """
        Collect all items into a list.

        Alias for `to_array()` without safety guard.

        Returns:
            List of all events across all pages
        """
        items: list[StoredEvent] = []
        async for item in self:
            items.append(item)
        return items

    async def to_array(self, *, max_items: int | None = DEFAULT_MAX_ITEMS) -> list[StoredEvent]:
        """
        Collect all items into an array.

        **Warning**: Use with caution on large datasets as this loads
        all items into memory. Consider iterating with `async for` for
        better memory efficiency.

        Args:
            max_items: Maximum items to collect (default: 10,000).
                Raises error if limit is exceeded. Set to None to disable.

        Returns:
            List of all events across all pages

        Raises:
            RuntimeError: If max_items limit is exceeded
        """
        items: list[StoredEvent] = []
        async for item in self:
            if max_items is not None and len(items) >= max_items:
                raise RuntimeError(
                    f"to_array() exceeded max_items limit of {max_items}. "
                    "Use 'async for' to stream large datasets, or increase max_items."
                )
            items.append(item)
        return items

    async def first(self) -> StoredEvent | None:
        """
        Fetch just the first event.

        Returns:
            First event or None if empty
        """
        params = {**self._params, "limit": 1, "offset": self._initial_offset}
        response = await self._transport.get(self._path, params=params)
        events_data = response.get("events", [])

        if not events_data:
            return None

        return StoredEvent(**events_data[0])

    async def first_page(self) -> PageResult[StoredEvent]:
        """
        Fetch only the first page of results.

        Useful when you need pagination metadata (total count, has_more)
        or want to implement custom pagination UI.

        Returns:
            PageResult with data, has_more, total, and next_offset
        """
        params = {**self._params, "limit": self._limit, "offset": self._initial_offset}
        response = await self._transport.get(self._path, params=params)

        events_data = response.get("events", [])
        items = [StoredEvent(**e) for e in events_data]

        pagination = response.get("pagination", {})
        total = pagination.get("total")

        # hasMore logic
        has_more = False
        if total is not None and self._initial_offset + len(items) < total:
            has_more = True
        elif len(items) == self._limit and total is None:
            has_more = True  # Full page heuristic when no total

        next_offset = self._initial_offset + len(items) if has_more else None

        return PageResult(
            data=items,
            has_more=has_more,
            total=total,
            next_offset=next_offset,
        )


class EventsResource:
    """
    Events resource for sending and retrieving Caliper events.

    Access via `client.events`.

    Example:
        ```python
        # Send events
        result = await client.events.send_activity(
            sensor_id="https://myapp.example.com/sensors/main",
            input=ActivityCompletedInput(
                actor=TimebackUser(id="...", email="..."),
                object=TimebackActivityContext(id="...", subject="Math", app=TimebackApp(name="My App")),
                metrics=[TimebackActivityMetric(type="correctQuestions", value=8)],
            ),
        )

        # List events (BEYOND_AI only)
        result = await client.events.list(limit=50, start_date="2024-01-01")
        for event in result.events:
            print(event.id)

        # Stream events with pagination (BEYOND_AI only)
        async for event in client.events.stream(start_date="2024-01-01"):
            print(event.id)

        # Get a specific event (BEYOND_AI only)
        event = await client.events.get("urn:uuid:...")
        ```
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def send(
        self,
        sensor_id: str,
        events: list[TimebackEvent],
    ) -> SendEventsResult:
        """
        Send raw Caliper events.

        Wraps events in an envelope and sends to the API.
        Events are validated against the IMS Caliper specification
        and queued for async processing.

        Args:
            sensor_id: Sensor identifier (IRI format)
            events: List of Caliper events to send

        Returns:
            Result containing job_id for tracking processing status
        """
        envelope = CaliperEnvelope(
            sensor=sensor_id,
            sendTime=utc_iso_timestamp(),
            dataVersion=CALIPER_DATA_VERSION,
            data=[e.model_dump(mode="json", by_alias=True, exclude_none=True) for e in events],
        )

        return await self.send_envelope(envelope)

    async def send_envelope(
        self,
        envelope: CaliperEnvelope,
    ) -> SendEventsResult:
        """
        Send a raw Caliper envelope.

        Use this when you need full control over the envelope structure.
        For most cases, prefer `send()` which builds the envelope for you.

        Args:
            envelope: Caliper envelope containing events

        Returns:
            Result containing job_id for tracking processing status

        Example:
            ```python
            from timeback_caliper.types import CaliperEnvelope
            from datetime import datetime, UTC

            envelope = CaliperEnvelope(
                sensor="https://example.edu/sensors/1",
                send_time=utc_iso_timestamp(),
                data_version="http://purl.imsglobal.org/ctx/caliper/v1p2",
                data=[event1_dict, event2_dict],
            )
            result = await client.events.send_envelope(envelope)
            ```
        """
        send_path = self._transport.paths.send
        payload = envelope.model_dump(mode="json", by_alias=True)
        response = await self._transport.post(send_path, payload)
        return SendEventsResult(**response)

    async def validate(
        self,
        envelope: CaliperEnvelope,
    ) -> ValidationResult:
        """
        Validate Caliper events without storing them.

        Use this to check if events conform to the IMS Caliper specification
        before sending them for processing.

        Note:
            This operation is only available on the BEYOND_AI platform.

        Args:
            envelope: Caliper envelope containing events to validate

        Returns:
            Validation result with status and any errors

        Raises:
            UnsupportedOperationError: If not supported on current platform

        Example:
            ```python
            result = await client.events.validate(envelope)
            if result.status == "success":
                print("Events are valid!")
            else:
                print("Validation errors:", result.errors)
            ```
        """
        validate_path = self._transport.paths.validate
        if validate_path is None:
            raise UnsupportedOperationError("validate")

        payload = envelope.model_dump(mode="json", by_alias=True)
        response = await self._transport.post(validate_path, payload)
        return ValidationResult(**response)

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        sensor: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        actor_id: str | None = None,
        actor_email: str | None = None,
    ) -> ListEventsResult:
        """
        List Caliper events with optional filtering.

        Note:
            This operation is only available on the BEYOND_AI platform.

        Args:
            limit: Maximum events per page (default: 100)
            offset: Starting offset for pagination
            sensor: Filter by sensor ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            actor_id: Filter by actor ID
            actor_email: Filter by actor email

        Returns:
            Events array and pagination metadata

        Raises:
            UnsupportedOperationError: If not supported on current platform
            InputValidationError: If limit or offset are invalid

        Example:
            ```python
            result = await client.events.list(
                limit=50,
                actor_email="student@example.edu",
                start_date="2024-01-01",
            )
            print(f"Total: {result.pagination.total}")
            for event in result.events:
                print(event.id)
            ```
        """
        validate_offset_list_params(limit=limit, offset=offset)

        list_path = self._transport.paths.list
        if list_path is None:
            raise UnsupportedOperationError("list")

        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if sensor:
            params["sensor"] = sensor
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if actor_id:
            params["actorId"] = actor_id
        if actor_email:
            params["actorEmail"] = actor_email

        response = await self._transport.get(list_path, params=params)

        events_data = response.get("events", [])
        events = [StoredEvent(**e) for e in events_data]

        pagination_data = response.get("pagination", {})
        pagination = Pagination(**pagination_data)

        return ListEventsResult(events=events, pagination=pagination)

    def stream(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        sensor: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        actor_id: str | None = None,
        actor_email: str | None = None,
        max_items: int | None = None,
    ) -> EventsPaginator:
        """
        Stream Caliper events with automatic pagination.

        Returns a paginator that lazily fetches pages as you iterate.
        Use this for large datasets or when you need all matching events.

        Note:
            This operation is only available on the BEYOND_AI platform.

        Args:
            limit: Events per page (default: 100)
            offset: Starting offset for pagination (default: 0)
            sensor: Filter by sensor ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            actor_id: Filter by actor ID
            actor_email: Filter by actor email
            max_items: Maximum total events to fetch

        Returns:
            Async iterator for streaming events

        Raises:
            UnsupportedOperationError: If not supported on current platform
            InputValidationError: If limit, offset, or max_items are invalid

        Example:
            ```python
            # Iterate over all events
            async for event in client.events.stream(start_date="2024-01-01"):
                print(event.id)

            # Collect all events into a list
            all_events = await client.events.stream(start_date="2024-01-01").to_list()

            # Limit total events fetched
            events = await client.events.stream(max_items=1000).to_list()

            # Start from a specific offset
            events = await client.events.stream(offset=100).to_list()

            # Get first page with metadata
            page = await client.events.stream(start_date="2024-01-01").first_page()
            ```
        """
        validate_offset_list_params(limit=limit, offset=offset, max_items=max_items)

        list_path = self._transport.paths.list
        if list_path is None:
            raise UnsupportedOperationError("stream")

        params: dict[str, Any] = {}
        if sensor:
            params["sensor"] = sensor
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if actor_id:
            params["actorId"] = actor_id
        if actor_email:
            params["actorEmail"] = actor_email

        return EventsPaginator(
            self._transport,
            list_path,
            params,
            limit=limit,
            max_items=max_items,
            offset=offset,
        )

    async def get(self, external_id: str) -> StoredEvent:
        """
        Get a specific event by its external ID.

        Note:
            This operation is only available on the BEYOND_AI platform.

        Args:
            external_id: The event's external ID (URN UUID format, e.g., 'urn:uuid:...')

        Returns:
            The stored event

        Raises:
            UnsupportedOperationError: If not supported on current platform
            InputValidationError: If external_id is empty
            APIError: If the event is not found

        Important:
            Use `external_id` (URN UUID), not the internal numeric `id`.
            The `StoredEvent` returned from `list()` contains both.

        Example:
            ```python
            event = await client.events.get("urn:uuid:c51570e4-f8ed-4c18-bb3a-dfe51b2cc594")
            print(event.event_type, event.actor_id)
            ```
        """
        validate_non_empty_string(external_id, "external_id")

        get_path = self._transport.paths.get
        if get_path is None:
            raise UnsupportedOperationError("get")

        # Use {id} template like TS does
        path = get_path.replace("{id}", quote(external_id, safe=""))
        response = await self._transport.get(path)

        event_data = response.get("event")
        if not event_data:
            raise APIError(f"Event not found: {external_id}", status_code=404)

        return StoredEvent(**event_data)

    async def send_activity(
        self,
        sensor_id: str,
        input: ActivityCompletedInput,
    ) -> SendEventsResult:
        """
        Send an activity completed event.

        Auto-generates id, eventTime, and metrics collection id if not provided.

        Args:
            sensor_id: Sensor identifier (IRI format)
            input: Activity completion input

        Returns:
            Result containing job_id and events_accepted count

        Example:
            ```python
            result = await client.events.send_activity(
                sensor_id="https://myapp.example.com/sensors/main",
                input=ActivityCompletedInput(
                    actor=TimebackUser(id="...", type="TimebackUser", email="student@example.edu"),
                    object=TimebackActivityContext(
                        id="...",
                        type="TimebackActivityContext",
                        subject="Math",
                        app=TimebackApp(name="My Learning App"),
                    ),
                    metrics=[
                        TimebackActivityMetric(type="totalQuestions", value=10),
                        TimebackActivityMetric(type="correctQuestions", value=8),
                    ],
                ),
            )
            ```
        """
        event = ActivityCompletedEvent(
            id=input.id or f"urn:uuid:{uuid.uuid4()}",
            actor=input.actor,
            object=input.object,
            eventTime=input.event_time or utc_iso_timestamp(),
            generated=TimebackActivityMetricsCollection(
                id=input.metrics_id or f"urn:uuid:{uuid.uuid4()}",
                items=input.metrics,
            ),
            extensions=input.extensions,
        )

        return await self.send(sensor_id, [event])

    async def send_time_spent(
        self,
        sensor_id: str,
        input: TimeSpentInput,
    ) -> SendEventsResult:
        """
        Send a time spent event.

        Auto-generates id, eventTime, and metrics collection id if not provided.

        Args:
            sensor_id: Sensor identifier (IRI format)
            input: Time spent input

        Returns:
            Result containing job_id and events_accepted count

        Example:
            ```python
            result = await client.events.send_time_spent(
                sensor_id="https://myapp.example.com/sensors/main",
                input=TimeSpentInput(
                    actor=TimebackUser(id="...", type="TimebackUser", email="student@example.edu"),
                    object=TimebackActivityContext(
                        id="...",
                        type="TimebackActivityContext",
                        subject="Reading",
                        app=TimebackApp(name="My Learning App"),
                    ),
                    metrics=[
                        TimeSpentMetric(type="active", value=1800),  # 30 min
                        TimeSpentMetric(type="inactive", value=300),  # 5 min
                    ],
                ),
            )
            ```
        """
        event = TimeSpentEvent(
            id=input.id or f"urn:uuid:{uuid.uuid4()}",
            actor=input.actor,
            object=input.object,
            eventTime=input.event_time or utc_iso_timestamp(),
            generated=TimebackTimeSpentMetricsCollection(
                id=input.metrics_id or f"urn:uuid:{uuid.uuid4()}",
                items=input.metrics,
            ),
            extensions=input.extensions,
        )

        return await self.send(sensor_id, [event])
