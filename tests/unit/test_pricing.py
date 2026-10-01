"""Pure unit tests: server-side pricing and cart validation.

These are the rules that stop a manipulated client payload from becoming
the authoritative order total.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.errors import UnprocessableError
from app.schemas.orders import OrderItemCreate
from app.services.order_service import (
    calculate_total,
    merge_duplicate_lines,
    to_money,
)


def test_to_money_rounds_to_two_decimals() -> None:
    assert to_money(50.16) == Decimal("50.16")
    assert to_money(1) == Decimal("1.00")
    assert to_money("9.999") == Decimal("10.00")
    assert to_money(0.1) + to_money(0.2) == Decimal("0.30")


def test_calculate_total_is_sum_of_line_totals() -> None:
    from app.services.order_service import ResolvedLine

    lines = [
        ResolvedLine("p1", "Wireless Mouse", 3, Decimal("50.16")),
        ResolvedLine("p2", "Desk Lamp LED", 2, Decimal("42.00")),
    ]
    # 150.48 + 84.00
    assert calculate_total(lines) == Decimal("234.48")


def test_calculate_total_of_empty_cart_is_zero() -> None:
    from app.services.order_service import ResolvedLine

    assert calculate_total([]) == Decimal("0.00")


def test_merge_duplicate_lines_sums_quantities() -> None:
    merged = merge_duplicate_lines(
        [
            OrderItemCreate(product_id="aaa", quantity=2),
            OrderItemCreate(product_id="bbb", quantity=1),
            OrderItemCreate(product_id="aaa", quantity=3),
        ]
    )
    assert [(item.product_id, item.quantity) for item in merged] == [("aaa", 5), ("bbb", 1)]


def test_merge_rejects_quantities_above_the_limit() -> None:
    with pytest.raises(UnprocessableError) as excinfo:
        merge_duplicate_lines(
            [
                OrderItemCreate(product_id="aaa", quantity=60),
                OrderItemCreate(product_id="aaa", quantity=60),
            ]
        )
    assert excinfo.value.code == "quantity_limit_exceeded"


def test_order_item_schema_rejects_zero_and_negative_quantities() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        OrderItemCreate(product_id="aaa", quantity=0)
    with pytest.raises(ValidationError):
        OrderItemCreate(product_id="aaa", quantity=-3)
    with pytest.raises(ValidationError):
        OrderItemCreate(product_id="aaa", quantity=101)


def test_order_create_has_no_price_fields() -> None:
    """The client can never submit a total — the field does not exist."""
    from app.schemas.orders import OrderCreate

    payload = OrderCreate(user_id=1, items=[{"product_id": "x", "quantity": 1}])
    dumped = payload.model_dump()
    assert "total_amount" not in dumped
    assert "total" not in dumped
    assert set(dumped) == {"user_id", "items"}
