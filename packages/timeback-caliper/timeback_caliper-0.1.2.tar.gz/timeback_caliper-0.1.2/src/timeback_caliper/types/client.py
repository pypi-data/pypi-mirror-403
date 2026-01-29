"""
Client Configuration Types
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Environment = Literal["staging", "production"]


class EnvAuth(BaseModel):
    """Authentication using client credentials."""

    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)


class ExplicitAuth(BaseModel):
    """Authentication with explicit auth URL."""

    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)
    auth_url: str = Field(..., min_length=1)


class CaliperClientConfig(BaseModel):
    """
    Configuration for the Caliper client.

    Supports three modes:
    - Environment mode: `env='staging'` or `env='production'`
    - Explicit mode: `base_url='...'` with explicit auth
    - Environment variables fallback
    """

    env: Environment | None = None
    base_url: str | None = None
    auth: EnvAuth | ExplicitAuth | None = None
    timeout: float = Field(default=30.0, gt=0)
