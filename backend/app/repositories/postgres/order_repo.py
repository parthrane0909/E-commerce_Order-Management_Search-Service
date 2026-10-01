"""Order repository (PostgreSQL) — source of truth for orders.

Repository functions receive an already-open session; transaction control
(`begin` / `commit` / `rollback`) lives in the service layer where it stays
explicit and readable.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.postgres import ORDER_STATUSES, Order, OrderItem, User


def get_user(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def list_users(session: Session) -> list[User]:
    return list(session.scalars(select(User).order_by(User.id)))


def get_order(session: Session, order_id: int) -> Order | None:
    """Fetch an order with its customer and line items eagerly loaded."""
    statement = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items), selectinload(Order.user))
    )
    return session.scalars(statement).first()


def count_orders(session: Session) -> int:
    return int(session.scalar(select(func.count(Order.id))) or 0)


def count_order_items(session: Session) -> int:
    return int(session.scalar(select(func.count(OrderItem.id))) or 0)


def iter_orders(session: Session, batch_size: int = 250) -> Iterator[Order]:
    """Stream orders ordered by id (used by the reindex script)."""
    last_id = 0
    while True:
        statement = (
            select(Order)
            .where(Order.id > last_id)
            .order_by(Order.id)
            .limit(batch_size)
            .options(selectinload(Order.items), selectinload(Order.user))
        )
        batch = list(session.scalars(statement))
        if not batch:
            return
        yield from batch
        last_id = batch[-1].id


def mark_search_indexed(session: Session, order_id: int, when: dt.datetime | None = None) -> None:
    """Bookkeeping: record that the order document reached Elasticsearch."""
    order = session.get(Order, order_id)
    if order is not None:
        order.search_indexed_at = when or dt.datetime.now(dt.timezone.utc)


def status_counts(session: Session) -> dict[str, int]:
    """Row count per status directly from PostgreSQL (verification helper)."""
    rows = session.execute(
        select(Order.status, func.count(Order.id)).group_by(Order.status)
    ).all()
    counts = {status: 0 for status in ORDER_STATUSES}
    counts.update({status: int(count) for status, count in rows})
    return counts
