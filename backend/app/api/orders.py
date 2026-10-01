"""Order endpoints — data source: **PostgreSQL** (source of truth).

* `POST /api/orders`          validate cart (MongoDB) → PostgreSQL
                              transaction → publish RabbitMQ sync task
* `GET  /api/orders/{id}`     canonical order details (never Elasticsearch)
* `PATCH /api/orders/{id}/status`  update PostgreSQL, then synchronise
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status

from app.api.auth import get_current_user
from app.core.auth import require_admin
from app.schemas.common import ErrorResponse
from app.schemas.orders import (
    OrderCreate,
    OrderCreateResponse,
    OrderResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
)
from app.services import order_service

router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"],
    responses={
        404: {"model": ErrorResponse, "description": "Order, user or product not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "PostgreSQL unavailable"},
    },
)

ORDER_ID = Path(..., description="PostgreSQL order id", examples=[1], ge=1)


@router.post(
    "",
    response_model=OrderCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place an order",
    description=(
        "1. The cart is validated against the live MongoDB catalog and every "
        "price is re-read server-side (client totals are never trusted).\n"
        "2. `orders` + `order_items` are written inside a single explicit "
        "PostgreSQL transaction (rollback on any failure).\n"
        "3. After COMMIT an Elasticsearch sync task is published to RabbitMQ.\n"
        "Requires authentication — user_id is taken from the authenticated user."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Unknown user or product"},
        409: {"model": ErrorResponse, "description": "Conflict"},
        500: {"model": ErrorResponse, "description": "Transaction rolled back — nothing was written"},
    },
)
def create_order(payload: OrderCreate, current_user = Depends(get_current_user)) -> OrderCreateResponse:
    # Override user_id with authenticated user's ID
    payload.user_id = current_user.id
    return order_service.create_order(payload)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get canonical order details",
    description=(
        "Reads PostgreSQL only. Line items contain the title/price *snapshots* "
        "recorded when the order was placed.\n"
        "Requires authentication. Customers can only view their own orders; admins can view any order."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Forbidden: not your order"},
    },
)
def get_order(order_id: int = ORDER_ID, current_user = Depends(get_current_user)) -> OrderResponse:
    order = order_service.get_order(order_id)
    # Authorization: customers can only view their own orders
    if current_user.role != "ADMIN" and order.user_id != current_user.id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders",
        )
    return order


@router.patch(
    "/{order_id}/status",
    response_model=StatusUpdateResponse,
    summary="Update order status",
    description=(
        "Updates PostgreSQL inside an explicit transaction, then publishes a "
        "synchronisation task so Elasticsearch reflects the new status.\n"
        "Admin only."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
def update_status(
    payload: StatusUpdateRequest,
    order_id: int = ORDER_ID,
    _admin = Depends(require_admin),
) -> StatusUpdateResponse:
    return order_service.update_order_status(order_id, payload.status)
