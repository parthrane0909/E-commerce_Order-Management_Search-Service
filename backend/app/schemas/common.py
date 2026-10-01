"""Shared response shapes (errors, pagination, health)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(examples=["not_found"])
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope returned by every failing endpoint."""

    error: ErrorBody


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    limit: int = Field(ge=1)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)


class HealthDependency(BaseModel):
    status: str = Field(description="'up' or 'down'")
    latency_ms: int | None = Field(default=None, ge=0)


class HealthResponse(BaseModel):
    status: str = Field(description="'ok' when every dependency is reachable")
    environment: str
    dependencies: dict[str, HealthDependency]
