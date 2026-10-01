"""Order business logic (Screen 2 + Screen 4).

Responsibilities:
  1. Validate the cart against the **live MongoDB catalog**.
  2. Price every line server-side and compute the authoritative total.
  3. Persist the order inside an **explicit PostgreSQL transaction**
     (BEGIN → INSERT orders → INSERT order_items → COMMIT / ROLLBACK).
  4. After a successful commit, publish an Elasticsearch sync task to
     RabbitMQ (never inside the transaction).

Line items store *snapshots* (product title + unit price) taken at
purchase time, so later catalog edits never rewrite history.
"""

from __future__ import annotations

import datetime as dt
import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from app.core.database import SessionLocal
from app.core.errors import AppError, NotFoundError, UnprocessableError
from app.core.logging import get_logger
from app.models.postgres import Order, OrderItem
from app.repositories.mongo import product_repo
from app.repositories.postgres import order_repo
from app.schemas.orders import (
    OrderCreate,
    OrderCreateResponse,
    OrderItemCreate,
    OrderItemResponse,
    OrderResponse,
    StatusUpdateResponse,
    SyncInfo,
    UserResponse,
)
from app.services import sync_service

logger = get_logger(__name__)

CENT = Decimal("0.01")
MAX_LINE_QUANTITY = 100


class OrderPersistenceError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="order_persistence_failed", status_code=500)


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def to_money(value: object) -> Decimal:
    """Convert a Mongo/JSON number into an exact 2-decimal amount."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class ResolvedLine:
    """A cart line after server-side validation and pricing."""

    product_id: str
    title: str
    quantity: int
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(CENT)


def calculate_total(lines: list[ResolvedLine]) -> Decimal:
    """The single authoritative order total: SUM(quantity * unit_price)."""
    return sum((line.line_total for line in lines), Decimal("0.00")).quantize(CENT)


def merge_duplicate_lines(items: list[OrderItemCreate]) -> list[OrderItemCreate]:
    """Collapse repeated product ids so each product appears exactly once."""
    quantities: dict[str, int] = defaultdict(int)
    order: list[str] = []
    for item in items:
        if item.product_id not in quantities:
            order.append(item.product_id)
        quantities[item.product_id] += item.quantity

    merged: list[OrderItemCreate] = []
    for product_id in order:
        quantity = quantities[product_id]
        if quantity > MAX_LINE_QUANTITY:
            raise UnprocessableError(
                f"Cannot order more than {MAX_LINE_QUANTITY} units of the same product.",
                code="quantity_limit_exceeded",
                details={"product_id": product_id, "quantity": quantity},
            )
        merged.append(OrderItemCreate(product_id=product_id, quantity=quantity))
    return merged


def resolve_cart(items: list[OrderItemCreate]) -> tuple[list[ResolvedLine], Decimal]:
    """Validate the cart against MongoDB and price it server-side.

    The client never sends prices or totals — they are always recomputed
    from the current catalog documents.
    """
    if not items:
        raise UnprocessableError("An order needs at least one item.", code="empty_cart")

    merged = merge_duplicate_lines(items)
    products = product_repo.get_products_by_ids([item.product_id for item in merged])
    by_id = {str(product["_id"]): product for product in products}

    lines: list[ResolvedLine] = []
    for requested in merged:
        product = by_id.get(requested.product_id)
        if product is None:
            raise NotFoundError(
                f"Product '{requested.product_id}' does not exist in the catalog.",
                code="product_not_found",
                details={"product_id": requested.product_id},
            )
        if not product.get("active", True):
            raise UnprocessableError(
                f"'{product.get('title', requested.product_id)}' is no longer available "
                "and cannot be ordered.",
                code="inactive_product",
                details={"product_id": requested.product_id, "title": product.get("title")},
            )
        raw_price = product.get("price")
        if raw_price is None:
            raise UnprocessableError(
                f"'{product.get('title')}' has no valid price.",
                code="invalid_price",
                details={"product_id": requested.product_id},
            )
        unit_price = to_money(raw_price)
        if unit_price <= 0:
            raise UnprocessableError(
                f"'{product.get('title')}' has an invalid price.",
                code="invalid_price",
                details={"product_id": requested.product_id, "price": str(unit_price)},
            )
        lines.append(
            ResolvedLine(
                product_id=requested.product_id,
                title=str(product.get("title", "")).strip(),
                quantity=requested.quantity,
                unit_price=unit_price,
            )
        )
    return lines, calculate_total(lines)


def _temporary_order_number() -> str:
    """Unique placeholder; replaced by `ORD-<id>` once the row exists."""
    return f"TMP-{uuid.uuid4().hex[:12].upper()}"


def _order_response(order: Order) -> OrderResponse:
    """Shape the ORM order into the API response (call while attached)."""
    return OrderResponse.model_validate(order, from_attributes=True)


def create_order(payload: OrderCreate) -> OrderCreateResponse:
    """Place an order: validate → price → transaction → publish sync."""

    # 1) MongoDB validates availability and supplies the snapshot values.
    lines, total = resolve_cart(payload.items)
    logger.info(
        "order priced user_id=%s lines=%s total=%s",
        payload.user_id,
        len(lines),
        total,
    )

    # 2) EXPLICIT POSTGRESQL TRANSACTION -----------------------------------
    session = SessionLocal()
    try:
        try:
            session.begin()  # BEGIN

            user = order_repo.get_user(session, payload.user_id)
            if user is None:
                raise NotFoundError(
                    f"User '{payload.user_id}' does not exist.",
                    code="user_not_found",
                    details={"user_id": payload.user_id},
                )

            now = utcnow()
            order = Order(
                order_number=_temporary_order_number(),
                user=user,
                order_date=now,
                status="PENDING",
                total_amount=total,
                created_at=now,
                updated_at=now,
            )
            session.add(order)
            session.flush()  # INSERT orders -> order.id available
            order.order_number = f"ORD-{order.id:06d}"  # human readable number

            for line in lines:
                session.add(
                    OrderItem(
                        order=order,
                        product_id=line.product_id,
                        title=line.title,  # snapshot of MongoDB title
                        quantity=line.quantity,
                        unit_price=line.unit_price,  # snapshot of MongoDB price
                    )
                )
            session.flush()  # INSERT order_items (CHECK constraints run here)

            session.commit()  # COMMIT — the order is now durable
        except Exception as exc:
            session.rollback()  # ROLLBACK — never leave a partial order behind
            if isinstance(exc, AppError):
                logger.info(
                    "order rejected user_id=%s code=%s: %s", payload.user_id, exc.code, exc.message
                )
                raise
            logger.error(
                "order transaction failed user_id=%s: %s", payload.user_id, exc, exc_info=True
            )
            raise OrderPersistenceError(
                "The order could not be saved. No data was written — please try again."
            ) from exc

        # Built while the session is still open so relationships and
        # server-side timestamps are loaded from the canonical row.
        response = OrderResponse.model_validate(order, from_attributes=True)
    finally:
        session.close()
    # ----------------------------------------------------------------------

    logger.info(
        "order created id=%s number=%s user_id=%s total=%s items=%s",
        order.id,
        order.order_number,
        payload.user_id,
        total,
        len(lines),
    )

    # 3) Only now (after COMMIT) is the sync task handed to RabbitMQ.
    sync = sync_service.publish_order_sync(order.id, reason="order_created")
    return OrderCreateResponse(**response.model_dump(), sync=sync)


def get_order(order_id: int) -> OrderResponse:
    """Read canonical order data — always from PostgreSQL, never ES."""
    session = SessionLocal()
    try:
        order = order_repo.get_order(session, order_id)
        if order is None:
            raise NotFoundError(
                f"Order '{order_id}' was not found.",
                code="order_not_found",
                details={"order_id": order_id},
            )
        response = OrderResponse.model_validate(order, from_attributes=True)
        return response
    finally:
        session.close()


def update_order_status(order_id: int, status: str) -> StatusUpdateResponse:
    """Update status in PostgreSQL, then queue the Elasticsearch sync."""

    # ---- EXPLICIT POSTGRESQL TRANSACTION --------------------------------
    session = SessionLocal()
    try:
        try:
            session.begin()  # BEGIN

            order = order_repo.get_order(session, order_id)
            if order is None:
                raise NotFoundError(
                    f"Order '{order_id}' was not found.",
                    code="order_not_found",
                    details={"order_id": order_id},
                )

            previous = order.status
            if previous != status:
                order.status = status
                order.updated_at = utcnow()
                session.flush()  # UPDATE orders
            session.commit()  # COMMIT
        except Exception as exc:
            session.rollback()  # ROLLBACK
            if isinstance(exc, AppError):
                raise
            logger.error(
                "status update failed order_id=%s status=%s: %s", order_id, status, exc, exc_info=True
            )
            raise OrderPersistenceError(
                "The order status could not be updated. Please try again."
            ) from exc

        response = _order_response(order)  # while still attached
    finally:
        session.close()
    # ---------------------------------------------------------------------

    if previous != status:
        logger.info("order status changed order_id=%s %s -> %s", order_id, previous, status)
        sync = sync_service.publish_order_sync(order_id, reason="status_update")
    else:
        logger.info("order status unchanged order_id=%s status=%s", order_id, status)
        sync = SyncInfo(enqueued=True, queue=sync_service.EAGER_QUEUE, task_id=None)

    return StatusUpdateResponse(**response.model_dump(), sync=sync)


def list_users() -> list[UserResponse]:
    session = SessionLocal()
    try:
        return [UserResponse.model_validate(user, from_attributes=True) for user in order_repo.list_users(session)]
    finally:
        session.close()
