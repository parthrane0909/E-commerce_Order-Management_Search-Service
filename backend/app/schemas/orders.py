"""Order (PostgreSQL) request/response schemas."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

OrderStatus = Literal["PENDING", "PROCESSING", "SHIPPED"]
ORDER_STATUSES: tuple[OrderStatus, ...] = ("PENDING", "PROCESSING", "SHIPPED")


class OrderItemCreate(BaseModel):
    product_id: str = Field(
        min_length=1,
        max_length=64,
        description="MongoDB product ObjectId",
        examples=["652f1c3e9a4b2f0012ab34cd"],
    )
    quantity: int = Field(ge=1, le=100, description="Units requested (1-100)")


class OrderCreate(BaseModel):
    """Order placement payload.

    Note: there is intentionally **no** `total_amount` field.  The server
    always re-reads MongoDB, validates the products and computes the total
    itself — client supplied totals are never trusted.
    """

    user_id: int | None = Field(default=None, gt=0, description="Seeded PostgreSQL user id (optional, taken from auth)")
    items: list[OrderItemCreate] = Field(min_length=1, max_length=50)


class SyncInfo(BaseModel):
    """Outcome of publishing the Elasticsearch sync task to RabbitMQ."""

    enqueued: bool
    task_id: str | None = None
    queue: str
    error: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str


class OrderItemResponse(BaseModel):
    id: int
    product_id: str
    title: str = Field(description="Snapshot of the product title at purchase time")
    quantity: int
    unit_price: float = Field(description="Snapshot of the unit price at purchase time")
    line_total: float


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    customer: UserResponse
    order_date: dt.datetime
    status: OrderStatus
    total_amount: float
    updated_at: dt.datetime
    search_indexed_at: dt.datetime | None = Field(
        default=None,
        description="Set by the Celery worker once the document is in Elasticsearch",
    )
    items: list[OrderItemResponse]

    model_config = {"from_attributes": True}


class OrderCreateResponse(OrderResponse):
    sync: SyncInfo = Field(description="RabbitMQ/Celery synchronisation outcome")


class StatusUpdateRequest(BaseModel):
    status: OrderStatus


class StatusUpdateResponse(OrderResponse):
    sync: SyncInfo
