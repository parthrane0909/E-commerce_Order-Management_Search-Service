"""Build the Elasticsearch order document from canonical PostgreSQL data.

`build_order_document()` is a pure function: it only reads the already
loaded SQLAlchemy `Order` (and its items/user), which makes it trivial to
unit test and to reuse from the Celery task and the reindex script.

The document contains *snapshots* stored in PostgreSQL — never live
MongoDB product data — so historical orders keep their original titles
and prices.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.postgres import Order


def _isoformat(value: Any) -> str | None:
    if value is None:
        return None
    to_format = getattr(value, "isoformat", None)
    return to_format() if callable(to_format) else str(value)


def _money(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


def build_order_document(order: Order) -> dict[str, Any]:
    """Translate a PostgreSQL order into the Elasticsearch document."""
    user = getattr(order, "user", None)
    items = getattr(order, "items", []) or []

    document: dict[str, Any] = {
        "order_id": int(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "order_date": _isoformat(order.order_date),
        "updated_at": _isoformat(order.updated_at),
        "total_amount": _money(order.total_amount),
        "customer": {
            "id": int(order.user_id),
            "name": getattr(user, "name", "") or "",
            "email": getattr(user, "email", "") or "",
        },
        "items": [
            {
                "product_id": item.product_id,
                # Snapshot values straight out of PostgreSQL.
                "title": item.title,
                "quantity": int(item.quantity),
                "unit_price": _money(item.unit_price),
                "line_total": _money(item.line_total),
            }
            for item in items
        ],
    }
    return document
