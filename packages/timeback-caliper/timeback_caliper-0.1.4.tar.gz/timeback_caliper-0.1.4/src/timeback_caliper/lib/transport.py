"""
Caliper Transport Layer

This module keeps the Caliper transport focused:
- Holds `paths`
- Adds `request_paginated()` normalization for the Caliper list response shape
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from timeback_common import BaseTransport, CaliperPaths, TokenManager

if TYPE_CHECKING:
    import httpx


@dataclass
class PaginatedResponse:
    """Normalized paginated response."""

    data: list[Any]
    has_more: bool
    total: int | None = None


class Transport(BaseTransport):
    """HTTP transport layer for Caliper API communication."""

    def __init__(
        self,
        *,
        base_url: str,
        token_manager: TokenManager | None = None,
        paths: CaliperPaths,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
        no_auth: bool = False,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            token_manager=token_manager,
            http_client=http_client,
            no_auth=no_auth,
        )
        self.paths = paths

    async def request_paginated(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> PaginatedResponse:
        """
        Make a paginated request using Caliper's body pagination format.

        Caliper list endpoints return:
        - `events`: items array
        - `pagination`: { total, totalPages, currentPage, limit }

        """
        body = await self.get(path, params=params)
        events = body.get("events", [])
        if not isinstance(events, list):
            events = []

        pagination = body.get("pagination", {})
        total: int | None = None
        if isinstance(pagination, dict):
            raw_total = pagination.get("total")
            if isinstance(raw_total, int):
                total = raw_total

        offset = 0
        if params and isinstance(params.get("offset"), int):
            offset = params["offset"]

        has_more = False
        if total is not None:
            has_more = offset + len(events) < total

        return PaginatedResponse(data=events, has_more=has_more, total=total)


__all__ = ["PaginatedResponse", "Transport"]
