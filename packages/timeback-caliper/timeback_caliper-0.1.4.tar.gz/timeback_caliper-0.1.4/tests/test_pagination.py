"""Tests for Caliper events pagination.

Tests the EventsPaginator logic in isolation, using mock fetchers rather than HTTP-level mocking.
"""

import pytest

from timeback_caliper.resources.events import EventsPaginator
from timeback_caliper.types.api import StoredEvent


class MockTransport:
    """Mock transport for testing pagination in isolation."""

    def __init__(self, pages: list[dict]):
        """
        Initialize mock transport with predefined pages.

        Args:
            pages: List of response dicts, each containing:
                - events: list of event dicts
                - pagination: {total, limit, offset}
        """
        self._pages = pages
        self._call_count = 0
        self.requests: list[dict] = []

    async def get(self, path: str, *, params: dict | None = None) -> dict:
        """Mock GET request that returns next page."""
        self.requests.append({"path": path, "params": params or {}})
        if self._call_count >= len(self._pages):
            # Return empty page if we've exhausted the predefined pages
            return {"events": [], "pagination": {"total": 0, "limit": 100, "offset": 0}}
        response = self._pages[self._call_count]
        self._call_count += 1
        return response

    @property
    def call_count(self) -> int:
        return self._call_count


def make_event(id: int) -> dict:
    """Create a complete event dict for testing (all required StoredEvent fields)."""
    return {
        "id": id,
        "externalId": f"urn:uuid:event-{id}",
        "sensor": "https://example.edu/sensors/1",
        "type": "ActivityEvent",
        "action": "Completed",
        "eventTime": "2024-01-15T10:00:00Z",
        "sendTime": "2024-01-15T10:00:01Z",
        "created_at": "2024-01-15T10:00:02Z",
    }


class TestEventsPaginatorOffsetIncrement:
    """Tests that paginator increments offset by actual returned items."""

    @pytest.mark.asyncio
    async def test_offset_increments_by_returned_items(self):
        """Offset should increment by number of items returned, not by limit."""
        # Page 1: returns 3 items (less than limit)
        # Page 2: returns 2 items
        transport = MockTransport(
            [
                {
                    "events": [make_event(1), make_event(2), make_event(3)],
                    "pagination": {"total": 5, "limit": 10, "offset": 0},
                },
                {
                    "events": [make_event(4), make_event(5)],
                    "pagination": {"total": 5, "limit": 10, "offset": 3},
                },
            ]
        )

        paginator = EventsPaginator(transport, "/events", {}, limit=10)
        events = await paginator.to_list()

        assert len(events) == 5
        assert transport.call_count == 2

        # Verify offset progression: 0 -> 3 (not 0 -> 10)
        assert transport.requests[0]["params"]["offset"] == 0
        assert transport.requests[1]["params"]["offset"] == 3


class TestEventsPaginatorExhaustion:
    """Tests for paginator exhaustion logic."""

    @pytest.mark.asyncio
    async def test_exhausts_when_offset_reaches_total(self):
        """Paginator should stop when offset >= total."""
        # Return exactly total items in one page
        transport = MockTransport(
            [
                {
                    "events": [make_event(1), make_event(2)],
                    "pagination": {"total": 2, "limit": 10, "offset": 0},
                },
            ]
        )

        paginator = EventsPaginator(transport, "/events", {}, limit=10)
        events = await paginator.to_list()

        assert len(events) == 2
        assert transport.call_count == 1  # Should not fetch another page

    @pytest.mark.asyncio
    async def test_exhausts_on_empty_response(self):
        """Paginator should stop when server returns empty events array."""
        transport = MockTransport(
            [
                {
                    "events": [make_event(1)],
                    "pagination": {"total": 10, "limit": 10, "offset": 0},
                },
                {
                    "events": [],  # Empty page
                    "pagination": {"total": 10, "limit": 10, "offset": 1},
                },
            ]
        )

        paginator = EventsPaginator(transport, "/events", {}, limit=10)
        events = await paginator.to_list()

        assert len(events) == 1
        assert transport.call_count == 2


class TestEventsPaginatorMaxItems:
    """Tests that max_items limit works correctly."""

    @pytest.mark.asyncio
    async def test_respects_max_items_limit(self):
        """Paginator should stop after max_items even if more available."""
        transport = MockTransport(
            [
                {
                    "events": [make_event(i) for i in range(1, 6)],
                    "pagination": {"total": 100, "limit": 10, "offset": 0},
                },
            ]
        )

        paginator = EventsPaginator(transport, "/events", {}, limit=10, max_items=3)
        events = await paginator.to_list()

        assert len(events) == 3

    @pytest.mark.asyncio
    async def test_max_items_across_pages(self):
        """max_items should work across multiple pages."""
        transport = MockTransport(
            [
                {
                    "events": [make_event(1), make_event(2)],
                    "pagination": {"total": 10, "limit": 2, "offset": 0},
                },
                {
                    "events": [make_event(3), make_event(4)],
                    "pagination": {"total": 10, "limit": 2, "offset": 2},
                },
                {
                    "events": [make_event(5), make_event(6)],
                    "pagination": {"total": 10, "limit": 2, "offset": 4},
                },
            ]
        )

        # Get 5 items (should need 3 pages: 2 + 2 + 1)
        paginator = EventsPaginator(transport, "/events", {}, limit=2, max_items=5)
        events = await paginator.to_list()

        assert len(events) == 5
        assert transport.call_count == 3


class TestEventsPaginatorParams:
    """Tests that paginator correctly passes params to transport."""

    @pytest.mark.asyncio
    async def test_passes_filter_params(self):
        """Paginator should pass filter params to transport."""
        transport = MockTransport(
            [
                {
                    "events": [],
                    "pagination": {"total": 0, "limit": 50, "offset": 0},
                },
            ]
        )

        params = {"startDate": "2024-01-01", "sensor": "https://example.edu/sensors/1"}
        paginator = EventsPaginator(transport, "/events", params, limit=50)
        await paginator.to_list()

        request_params = transport.requests[0]["params"]
        assert request_params["startDate"] == "2024-01-01"
        assert request_params["sensor"] == "https://example.edu/sensors/1"
        assert request_params["limit"] == 50
        assert request_params["offset"] == 0


class TestStoredEventParsing:
    """Tests that paginator correctly parses StoredEvent objects."""

    @pytest.mark.asyncio
    async def test_parses_stored_events(self):
        """Paginator should return StoredEvent instances."""
        transport = MockTransport(
            [
                {
                    "events": [make_event(1)],
                    "pagination": {"total": 1, "limit": 10, "offset": 0},
                },
            ]
        )

        paginator = EventsPaginator(transport, "/events", {}, limit=10)
        events = await paginator.to_list()

        assert len(events) == 1
        assert isinstance(events[0], StoredEvent)
        assert events[0].id == 1
        assert events[0].external_id == "urn:uuid:event-1"
