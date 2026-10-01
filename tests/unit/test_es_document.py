"""Pure unit tests for the Elasticsearch document builder.

The document must be built exclusively from PostgreSQL data — in
particular the historical title/price snapshots.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

from app.repositories.elasticsearch.document import build_order_document

UTC = dt.timezone.utc


def _order(status: str = "PENDING") -> SimpleNamespace:
    user = SimpleNamespace(id=3, name="Wendy Wireless", email="wendy.wireless@example.com")
    items = [
        SimpleNamespace(
            product_id="652f1c3e9a4b2f0012ab34cd",
            title="Wireless Mouse",  # historical snapshot
            quantity=2,
            unit_price=Decimal("50.16"),
            line_total=Decimal("100.32"),
        ),
        SimpleNamespace(
            product_id="652f1c3e9a4b2f0012ab34ce",
            title="Desk Lamp LED",
            quantity=1,
            unit_price=Decimal("42.00"),
            line_total=Decimal("42.00"),
        ),
    ]
    return SimpleNamespace(
        id=12,
        order_number="ORD-000012",
        user_id=3,
        user=user,
        status=status,
        order_date=dt.datetime(2026, 6, 1, 10, 30, tzinfo=UTC),
        updated_at=dt.datetime(2026, 6, 1, 10, 31, tzinfo=UTC),
        total_amount=Decimal("142.32"),
        items=items,
    )


def test_document_contains_every_required_field() -> None:
    document = build_order_document(_order())

    assert document["order_id"] == 12
    assert document["order_number"] == "ORD-000012"
    assert document["status"] == "PENDING"
    assert document["customer"] == {
        "id": 3,
        "name": "Wendy Wireless",
        "email": "wendy.wireless@example.com",
    }
    assert document["total_amount"] == 142.32
    assert len(document["items"]) == 2
    assert set(document) == {
        "order_id",
        "order_number",
        "status",
        "order_date",
        "updated_at",
        "total_amount",
        "customer",
        "items",
    }


def test_document_uses_the_postgresql_snapshots() -> None:
    """No MongoDB read happens here: the snapshot values must survive."""
    document = build_order_document(_order())

    first = document["items"][0]
    assert first["title"] == "Wireless Mouse"
    assert first["unit_price"] == 50.16
    assert first["quantity"] == 2
    assert first["line_total"] == 100.32


def test_document_money_values_are_floats_with_two_decimals() -> None:
    document = build_order_document(_order())

    assert isinstance(document["total_amount"], float)
    for item in document["items"]:
        assert isinstance(item["unit_price"], float)
        assert round(item["unit_price"], 2) == item["unit_price"]


def test_document_serialises_timestamps_as_iso_strings() -> None:
    document = build_order_document(_order())

    assert document["order_date"] == "2026-06-01T10:30:00+00:00"
    assert document["updated_at"] == "2026-06-01T10:31:00+00:00"


def test_document_is_idempotent_input_to_index_id() -> None:
    """The same order always produces the same document (safe to re-index)."""
    assert build_order_document(_order()) == build_order_document(_order(status="PENDING"))
