"""Integration tests: catalog endpoints (Screen 1 + Screen 5).

Data source: MongoDB.  Nothing here may touch PostgreSQL or Elasticsearch.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

REQUIRED_CATEGORIES = {"peripherals", "audio", "cables", "office"}


def test_storefront_lists_at_least_24_active_products(api) -> None:
    response = api.get("/api/products", params={"limit": 100})
    assert response.status_code == 200
    body = response.json()

    assert body["total"] >= 24
    assert all(product["active"] for product in body["items"])


def test_inactive_product_is_hidden_from_the_storefront(api) -> None:
    active = api.get("/api/products", params={"limit": 100}).json()
    inactive = api.get(
        "/api/products", params={"limit": 100, "visibility": "inactive"}
    ).json()

    assert inactive["total"] == 1
    hidden_sku = inactive["items"][0]["sku"]
    assert hidden_sku not in {product["sku"] for product in active["items"]}


def test_every_category_has_products(api) -> None:
    facets = api.get("/api/products/facets").json()
    counts = {bucket["value"]: bucket["count"] for bucket in facets["categories"]}

    assert set(counts) == REQUIRED_CATEGORIES
    assert all(count >= 5 for count in counts.values())
    assert facets["tags"], "tag facets must not be empty"


def test_category_filter_returns_only_that_category(api) -> None:
    body = api.get("/api/products", params={"category": "audio", "limit": 100}).json()
    assert body["total"] >= 5
    assert {product["category"] for product in body["items"]} == {"audio"}


def test_tag_filter_uses_and_semantics(api) -> None:
    body = api.get("/api/products", params={"tags": ["wireless"], "limit": 100}).json()
    assert body["total"] >= 6
    for product in body["items"]:
        assert "wireless" in product["tags"] or "wireless" in product["title"].lower()


def test_text_search_filters_the_catalog(api) -> None:
    body = api.get("/api/products", params={"q": "keyboard", "limit": 50}).json()
    assert body["total"] >= 1
    assert all("keyboard" in product["title"].lower() for product in body["items"])


def test_pagination_metadata_is_correct(api) -> None:
    body = api.get("/api/products", params={"page": 2, "limit": 10}).json()
    assert body["page"] == 2
    assert body["limit"] == 10
    assert len(body["items"]) == 10
    assert body["pages"] == (body["total"] + 9) // 10


def test_get_single_product(api) -> None:
    first = api.get("/api/products", params={"limit": 1}).json()["items"][0]
    fetched = api.get(f"/api/products/{first['id']}")

    assert fetched.status_code == 200
    assert fetched.json()["sku"] == first["sku"]
    assert isinstance(fetched.json()["attributes"], dict)
    assert isinstance(fetched.json()["variants"], list)


def test_get_product_with_invalid_object_id_returns_404_not_500(api) -> None:
    response = api.get("/api/products/not-a-valid-object-id")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_not_found"


def test_create_update_and_soft_delete_product(admin_api, product_factory) -> None:
    created_response = admin_api.post(
        "/api/products",
        json={
            "sku": "ITEST-001",
            "title": "Integration Test Product",
            "description": "created by pytest",
            "price": 12.34,
            "category": "cables",
            "tags": ["test"],
            "attributes": {"length": 1},
            "variants": [{"sku": "ITEST-001-A", "color": "black", "stock": 5}],
        },
    )
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    assert created["id"]
    assert created["price"] == 12.34

    try:
        # update
        updated = admin_api.patch(
            f"/api/products/{created['id']}",
            json={"price": 20.5, "title": "Integration Test Product v2"},
        )
        assert updated.status_code == 200
        assert updated.json()["price"] == 20.5
        assert updated.json()["title"] == "Integration Test Product v2"

        # duplicate SKU -> 409
        conflict = admin_api.post(
            "/api/products",
            json={
                "sku": "ITEST-001",
                "title": "Duplicate",
                "price": 5,
                "category": "cables",
            },
        )
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "duplicate_sku"

        # soft delete -> still present with visibility=all, gone from storefront
        deleted = admin_api.delete(f"/api/products/{created['id']}")
        assert deleted.status_code == 200
        assert deleted.json()["active"] is False

        all_products = admin_api.get(
            "/api/products", params={"visibility": "all", "q": "ITEST-001", "limit": 50}
        ).json()
        assert all_products["total"] == 1
        active_products = admin_api.get(
            "/api/products", params={"q": "ITEST-001", "limit": 50}
        ).json()
        assert active_products["total"] == 0
    finally:
        # hard cleanup so reruns stay deterministic
        from app.clients.mongodb import get_mongo_db

        get_mongo_db()["products"].delete_many({"sku": {"$regex": "^ITEST-001"}})


def test_product_validation_errors_are_specific(admin_api) -> None:
    missing_fields = admin_api.post("/api/products", json={"sku": "X"})
    assert missing_fields.status_code == 422
    assert missing_fields.json()["error"]["code"] == "validation_error"

    bad_price = admin_api.post(
        "/api/products",
        json={"sku": "ITEST-BAD", "title": "Bad Price", "price": 0, "category": "cables"},
    )
    assert bad_price.status_code == 422
    field_messages = str(bad_price.json()["error"]["details"])
    assert "price" in field_messages
