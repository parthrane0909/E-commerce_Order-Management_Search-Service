"""Unit tests for request validation (Pydantic schemas)."""

from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from app.schemas.orders import OrderCreate, StatusUpdateRequest
from app.schemas.products import ProductCreate, ProductUpdate
from app.schemas.search import SearchRequest


# ---------------------------------------------------------------- search
def test_search_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(status=["CANCELLED"])


def test_search_accepts_the_three_real_statuses() -> None:
    request = SearchRequest(status=["PENDING", "PROCESSING", "SHIPPED"])
    assert len(request.status) == 3


def test_search_rejects_inverted_price_range() -> None:
    with pytest.raises(ValidationError) as excinfo:
        SearchRequest(min_price=200, max_price=10)
    assert "min_price" in str(excinfo.value)


def test_search_rejects_inverted_date_range() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(date_from=dt.date(2026, 5, 1), date_to=dt.date(2026, 4, 1))


def test_search_rejects_invalid_pagination() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(page=0)
    with pytest.raises(ValidationError):
        SearchRequest(limit=101)
    with pytest.raises(ValidationError):
        SearchRequest(min_price=-1)


def test_search_defaults_are_sensible() -> None:
    request = SearchRequest()
    assert request.page == 1
    assert request.limit == 20
    assert request.status == []
    assert request.query is None


# -------------------------------------------------------------- products
def _product(**overrides):  # noqa: ANN001, ANN201
    payload = {
        "sku": "TEST-001",
        "title": "Test Product",
        "description": "d",
        "price": 10.5,
        "category": "Peripherals",
        "tags": ["Wireless", "wireless", " USB ", ""],
    }
    payload.update(overrides)
    return payload


def test_product_requires_a_positive_price() -> None:
    with pytest.raises(ValidationError):
        ProductCreate(**_product(price=0))
    with pytest.raises(ValidationError):
        ProductCreate(**_product(price=-5))


def test_product_price_is_rounded_to_two_decimals() -> None:
    product = ProductCreate(**_product(price=10.567))
    assert product.price == 10.57


def test_product_rejects_invalid_sku_pattern() -> None:
    with pytest.raises(ValidationError):
        ProductCreate(**_product(sku="-bad sku!"))


def test_product_normalises_category_and_tags() -> None:
    product = ProductCreate(**_product())
    assert product.category == "peripherals"
    assert product.tags == ["wireless", "usb"]  # trimmed, lowercased, deduplicated


def test_product_supports_nested_attributes_and_variants() -> None:
    product = ProductCreate(
        **_product(
            attributes={"colour": "black", "dpi": 1600},
            variants=[{"sku": "TEST-001-BLK", "colour": "black", "stock": 4}],
        )
    )
    assert product.attributes["dpi"] == 1600
    assert product.variants[0].stock == 4


def test_product_update_is_partial() -> None:
    update = ProductUpdate(price=99.99)
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {"price": 99.99}


def test_product_update_rejects_zero_price() -> None:
    with pytest.raises(ValidationError):
        ProductUpdate(price=0)


# ---------------------------------------------------------------- orders
@pytest.mark.parametrize("status", ["PENDING", "PROCESSING", "SHIPPED"])
def test_status_update_accepts_valid_statuses(status: str) -> None:
    assert StatusUpdateRequest(status=status).status == status


def test_status_update_rejects_anything_else() -> None:
    with pytest.raises(ValidationError):
        StatusUpdateRequest(status="DELIVERED")


def test_order_create_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(user_id=1, items=[])


def test_order_create_requires_a_positive_user() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(user_id=0, items=[{"product_id": "x", "quantity": 1}])
