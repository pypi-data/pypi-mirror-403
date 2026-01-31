"""
Caliper Pagination Support

Uses body-based pagination (events array + pagination metadata).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from timeback_common import validate_offset_list_params

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from .transport import PaginatedResponse

T = TypeVar("T")


@dataclass
class PageResult[T]:
    """
    Result of fetching a single page of resources.

    Provides pagination metadata for building custom pagination UIs.
    """

    data: list[T]
    """Array of items in this page."""

    has_more: bool
    """Whether more pages are available."""

    total: int | None = None
    """Total count of items (if provided by server)."""

    next_offset: int | None = None
    """Offset to use for fetching the next page."""


class PaginatedTransportProtocol(Protocol):
    """Protocol for transports that support paginated requests."""

    async def request_paginated(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> PaginatedResponse: ...


class Paginator[T]:
    """
    Async paginator for Caliper list endpoints.

    Uses body-based pagination (events array + pagination metadata).
    Lazily fetches pages as you iterate.

    Example:
        ```python
        async for event in paginator:
            print(event.id)

        # Or collect all at once
        all_events = await paginator.to_list()

        # Get just the first item
        first = await paginator.first()

        # Get first page with metadata
        page = await paginator.first_page()
        ```
    """

    def __init__(
        self,
        transport: PaginatedTransportProtocol,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        max_items: int | None = None,
        transform: Callable[[Any], T] | None = None,
    ) -> None:
        """
        Initialize paginator.

        Args:
            transport: Transport instance with request_paginated() method
            path: API endpoint path
            params: Additional query parameters
            limit: Items per page
            offset: Starting offset (default: 0)
            max_items: Maximum total items to fetch (None for all)
            transform: Optional function to transform each item before returning

        """
        # Validate params upfront
        validate_offset_list_params(limit=limit, offset=offset, max_items=max_items)

        self._transport = transport
        self._path = path
        self._params = params or {}
        self._limit = limit
        self._initial_offset = offset
        self._offset = offset
        self._max_items = max_items
        self._transform = transform
        # Internal state
        self._total_fetched = 0
        self._has_more = True
        self._total: int | None = None
        self._buffer: list[T] = []
        self._buffer_index = 0

    @property
    def total(self) -> int | None:
        """Total number of items (from pagination.total in response body)."""
        return self._total

    def _apply_transform(self, items: list[Any]) -> list[T]:
        """Apply transform to a list of items if transform is defined."""
        if self._transform is None:
            return items
        return [self._transform(item) for item in items]

    async def _fetch_page(self) -> list[T]:
        """Fetch the next page of results."""
        params = {
            **self._params,
            "limit": self._limit,
            "offset": self._offset,
        }

        response = await self._transport.request_paginated(
            self._path,
            params=params,
        )

        items = response.data

        # Update total if provided
        if response.total is not None:
            self._total = response.total

        # Increment offset by actual items returned
        self._offset += len(items)

        # Update has_more from response
        self._has_more = response.has_more

        # Apply transform to items
        return self._apply_transform(items)

    def __aiter__(self) -> AsyncIterator[T]:
        """Return async iterator."""
        return self

    async def __anext__(self) -> T:
        """Get next item, fetching pages as needed."""
        # Check max items limit
        if self._max_items is not None and self._total_fetched >= self._max_items:
            raise StopAsyncIteration

        # If buffer is exhausted, fetch more
        while self._buffer_index >= len(self._buffer):
            if not self._has_more and self._offset > self._initial_offset:
                raise StopAsyncIteration

            self._buffer = await self._fetch_page()
            self._buffer_index = 0

            if not self._buffer:
                raise StopAsyncIteration

        # Return next item from buffer
        item = self._buffer[self._buffer_index]
        self._buffer_index += 1
        self._total_fetched += 1
        return item

    async def to_list(self) -> list[T]:
        """
        Fetch all pages and return as a single list.

        Alias for `to_array()` without safety guard.

        Returns:
            List of all items across all pages
        """
        all_items: list[T] = []

        async for item in self:
            all_items.append(item)

        return all_items

    async def to_array(self, *, max_items: int | None = 10_000) -> list[T]:
        """
        Collect all items into an array with safety guard.

        **Warning**: Use with caution on large datasets as this loads
        all items into memory. Consider iterating with `async for` for
        better memory efficiency.

        Args:
            max_items: Maximum items to collect (default: 10,000).
                Raises error if limit is exceeded. Set to None to disable.

        Returns:
            List of all items across all pages

        Raises:
            RuntimeError: If max_items limit is exceeded
        """
        all_items: list[T] = []

        async for item in self:
            if max_items is not None and len(all_items) >= max_items:
                raise RuntimeError(
                    f"to_array() exceeded max_items limit of {max_items}. "
                    "Use 'async for' to stream large datasets, or increase max_items."
                )
            all_items.append(item)

        return all_items

    async def first(self) -> T | None:
        """
        Fetch just the first item.

        Returns:
            First item or None if empty
        """
        response = await self._transport.request_paginated(
            self._path,
            params={**self._params, "limit": 1, "offset": self._initial_offset},
        )
        items = self._apply_transform(response.data)
        return items[0] if items else None

    async def first_page(self) -> PageResult[T]:
        """
        Fetch only the first page of results with pagination metadata.

        Useful when you need pagination metadata (total count, has_more)
        or want to implement custom pagination UI.

        Returns:
            PageResult with data, has_more, total, and next_offset
        """
        params = {
            **self._params,
            "limit": self._limit,
            "offset": self._initial_offset,
        }

        response = await self._transport.request_paginated(
            self._path,
            params=params,
        )

        items = self._apply_transform(response.data)
        total = response.total
        has_more = response.has_more
        next_offset = self._initial_offset + len(items) if has_more else None

        return PageResult(
            data=items,
            has_more=has_more,
            total=total,
            next_offset=next_offset,
        )

    def reset(self) -> None:
        """Reset the paginator to start from the beginning."""
        self._offset = self._initial_offset
        self._total_fetched = 0
        self._has_more = True
        self._buffer = []
        self._buffer_index = 0


__all__ = ["PageResult", "PaginatedTransportProtocol", "Paginator"]
