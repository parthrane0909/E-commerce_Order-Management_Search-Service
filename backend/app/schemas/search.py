"""Elasticsearch search request/response schemas (Screen 3)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field, model_validator

from app.schemas.orders import ORDER_STATUSES, OrderStatus


class SearchRequest(BaseModel):
    """Filterable, paginated order search.

    Everything in this payload is translated into a single Elasticsearch
    `bool` query — results never touch PostgreSQL or MongoDB.
    """

    query: str | None = Field(
        default=None,
        max_length=200,
        description="Free-text query executed as multi_match across customer and item fields",
        examples=["Wireless"],
    )
    status: list[OrderStatus] = Field(
        default_factory=list,
        description="Status facets (terms filter). Empty means all statuses.",
        examples=[["PENDING", "SHIPPED"]],
    )
    date_from: dt.date | None = Field(default=None, description="Inclusive lower bound on order_date")
    date_to: dt.date | None = Field(default=None, description="Inclusive upper bound on order_date")
    min_price: float | None = Field(default=None, ge=0, description="Minimum total_amount")
    max_price: float | None = Field(default=None, ge=0, description="Maximum total_amount")
    page: int = Field(default=1, ge=1, le=10_000)
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def _check_ranges(self) -> "SearchRequest":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price must be lower than or equal to max_price")
        return self


class SearchCustomer(BaseModel):
    id: int
    name: str
    email: str


class SearchItem(BaseModel):
    product_id: str
    title: str
    quantity: int
    unit_price: float
    line_total: float


class SearchResult(BaseModel):
    order_id: int = Field(serialization_alias="order_id")
    order_number: str
    customer: SearchCustomer
    status: OrderStatus
    order_date: dt.datetime
    updated_at: dt.datetime | None = None
    total_amount: float
    items: list[SearchItem]


class SearchAggregations(BaseModel):
    """KPI values computed by Elasticsearch aggregations."""

    revenue: float = Field(description="sum(total_amount) over the filtered result set")
    status_counts: dict[str, int] = Field(
        description="Document count per status, always containing all three statuses"
    )


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int = Field(description="Total number of matching documents")
    page: int
    limit: int
    pages: int
    took_ms: int | None = Field(default=None, description="Elasticsearch query duration")
    aggregations: SearchAggregations


DEFAULT_STATUS_COUNTS = {status: 0 for status in ORDER_STATUSES}
