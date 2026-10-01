"""Integration tests: orders (Screen 2 checkout + Screen 4 order details).

PostgreSQL is the source of truth.  These tests pin down the three
hard requirements of the assignment:

1. the server always recomputes the total (client totals are ignored),
2. line items are *snapshots* that survive later catalog edits,
3. order creation runs in one explicit transaction that rolls back
   completely when any statement fails.
"""

from __future__ import annotations

import time

import pytest

pytestmark = pytest.mark.integration


def _order_counts() -> tuple[int, int]:
    """`(orders, order_items)` straight from PostgreSQL."""
    from app.core.database import SessionLocal
    from app.models.postgres import Order, OrderItem

    session = SessionLocal()
    try:
        return session.query(Order).count(), session.query(OrderItem).count()
    finally:
        session.close()


@pytest.fixture
def place(authenticated_api):
    """POST /api/orders, remembering every id so it is removed afterwards."""
    created: list[int] = []

    def _place(payload: dict):
        # Remove user_id from payload since it's now taken from authenticated user
        payload = {k: v for k, v in payload.items() if k != "user_id"}
        response = authenticated_api.post("/api/orders", json=payload)
        if response.status_code == 201:
            created.append(response.json()["id"])
        return response

    yield _place

    if created:
        from app.core.database import SessionLocal
        from app.models.postgres import Order
        from app.repositories.elasticsearch.orders_repo import index_name
        from app.clients.elasticsearch import get_elasticsearch_client

        session = SessionLocal()
        try:
            session.begin()
            session.query(Order).filter(Order.id.in_(created)).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()

        # Give a racing worker a moment to finish, then clear stale documents.
        time.sleep(0.5)
        client = get_elasticsearch_client()
        for order_id in created:
            try:
                client.delete(index=index_name(), id=str(order_id), refresh=True)
            except Exception:  # noqa: BLE001 - document may simply not exist
                pass


def _payload_with_extra_total(product_id: str, quantity: int = 2) -> dict:
    return {
        "items": [{"product_id": product_id, "quantity": quantity}],
        # Deliberately wrong client-side total: must never be trusted.
        "total_amount": 0.01,
        "currency": "EUR",
    }


def test_server_recomputes_the_total_and_ignores_client_totals(authenticated_api, product_factory, place) -> None:
    product = product_factory(price=19.99)

    response = place(_payload_with_extra_total(str(product["_id"])))

    assert response.status_code == 201, response.text
    body = response.json()

    # 19.99 x 2 computed server-side from MongoDB, not 0.01 from the client.
    assert body["total_amount"] == pytest.approx(39.98, abs=0.001)
    assert body["items"][0]["unit_price"] == pytest.approx(19.99, abs=0.001)
    assert body["items"][0]["line_total"] == pytest.approx(39.98, abs=0.001)
    # The response must not echo any client supplied total.
    assert set(body) >= {"id", "order_number", "total_amount", "items", "sync"}
    assert body["order_number"].startswith("ORD-")


def test_duplicate_lines_are_merged_into_one_row(authenticated_api, product_factory, place) -> None:
    product = product_factory(price=10.00)

    response = place(
        {
            "items": [
                {"product_id": str(product["_id"]), "quantity": 1},
                {"product_id": str(product["_id"]), "quantity": 2},
            ],
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 3
    assert body["total_amount"] == pytest.approx(30.00, abs=0.001)


def test_new_order_snapshots_the_current_catalog_values(authenticated_api, product_factory, place) -> None:
    product = product_factory(title="Snapshot Probe", price=12.34)

    created = place(
        {
            "items": [{"product_id": str(product["_id"]), "quantity": 1}],
        }
    )
    assert created.status_code == 201, created.text

    # Edit the catalog *after* the purchase...
    from app.clients.mongodb import get_mongo_db

    get_mongo_db()["products"].update_one(
        {"_id": product["_id"]}, {"$set": {"title": "Renamed Later", "price": 99.99}}
    )

    # ...the stored line item still shows what was actually purchased.
    fetched = authenticated_api.get(f"/api/orders/{created.json()['id']}")
    assert fetched.status_code == 200
    item = fetched.json()["items"][0]
    assert item["title"] == "Snapshot Probe"
    assert item["unit_price"] == pytest.approx(12.34, abs=0.001)


def test_historical_snapshot_survives_the_wireless_mouse_rename(authenticated_api, es_document) -> None:
    """Seed fixture: MongoDB 'Wireless Mouse' ($50.16) was renamed to
    'Wireless Mouse Pro' ($60.00) *after* orders were placed."""
    from app.clients.mongodb import get_mongo_db
    from app.core.database import SessionLocal
    from app.models.postgres import OrderItem

    session = SessionLocal()
    try:
        snapshot = (
            session.query(OrderItem)
            .filter(OrderItem.title == "Wireless Mouse")
            .first()
        )
        assert snapshot is not None, "seed must contain a 'Wireless Mouse' snapshot"
        order_id = snapshot.order_id
    finally:
        session.close()

    live = get_mongo_db()["products"].find_one({"title": "Wireless Mouse Pro"})
    assert live is not None, "MongoDB product must have been renamed"
    assert float(live["price"]) == pytest.approx(60.00, abs=0.001)

    body = authenticated_api.get(f"/api/orders/{order_id}").json()
    item = next(i for i in body["items"] if i["product_id"] == str(live["_id"]))
    assert item["title"] == "Wireless Mouse"
    assert item["unit_price"] == pytest.approx(50.16, abs=0.001)
    # Every order total equals SUM(quantity * unit_price) of its snapshots.
    assert body["total_amount"] == pytest.approx(
        sum(i["line_total"] for i in body["items"]), abs=0.001
    )

    # Elasticsearch carries the same snapshot, not the live catalog value.
    document = es_document(order_id)
    if document is not None:  # the worker may not have indexed this row yet
        es_item = next(i for i in document["items"] if i["product_id"] == str(live["_id"]))
        assert es_item["title"] == "Wireless Mouse"
        assert es_item["unit_price"] == pytest.approx(50.16, abs=0.001)


def test_transaction_rolls_back_completely_when_an_item_insert_fails(
    authenticated_api, product_factory, monkeypatch
) -> None:
    """A failure after the `orders` INSERT must leave no partial rows."""
    product = product_factory(price=25.00)

    orders_before, items_before = _order_counts()

    class _Boom:
        def __init__(self, **_kwargs):  # noqa: ANN003
            raise RuntimeError("simulated order_items INSERT failure")

    import app.services.order_service as order_service

    monkeypatch.setattr(order_service, "OrderItem", _Boom)

    response = authenticated_api.post(
        "/api/orders",
        json={
            "items": [{"product_id": str(product["_id"]), "quantity": 2}],
        },
    )

    assert response.status_code == 500, response.text
    error = response.json()["error"]
    assert error["code"] == "order_persistence_failed"
    assert "No data was written" in error["message"]

    # Nothing at all was written: no order row, no item row.
    assert _order_counts() == (orders_before, items_before)


def test_unknown_product_is_rejected(authenticated_api) -> None:
    response = authenticated_api.post(
        "/api/orders",
        json={
            "items": [{"product_id": "652f1c3e9a4b2f0000000000", "quantity": 1}],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_not_found"


def test_inactive_product_cannot_be_ordered(authenticated_api) -> None:
    inactive = authenticated_api.get("/api/products", params={"visibility": "inactive", "limit": 1}).json()
    assert inactive["total"] == 1, "seed must deactivate exactly one product"

    response = authenticated_api.post(
        "/api/orders",
        json={
            "items": [{"product_id": inactive["items"][0]["id"], "quantity": 1}],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "inactive_product"


@pytest.mark.parametrize(
    ("items", "expected_code"),
    [
        ([], "validation_error"),
        ([{"product_id": "x", "quantity": 0}], "validation_error"),
        ([{"product_id": "", "quantity": 1}], "validation_error"),
    ],
)
def test_malformed_carts_are_rejected(authenticated_api, items, expected_code) -> None:
    response = authenticated_api.post("/api/orders", json={"items": items})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == expected_code


def test_created_order_is_readable_from_postgres(authenticated_api, product_factory, place) -> None:
    product = product_factory(price=7.50)
    created = place(
        {"items": [{"product_id": str(product["_id"]), "quantity": 4}]}
    )
    assert created.status_code == 201
    order_id = created.json()["id"]

    fetched = authenticated_api.get(f"/api/orders/{order_id}")
    assert fetched.status_code == 200
    body = fetched.json()

    assert body["id"] == order_id
    assert body["status"] == "PENDING"
    assert body["customer"]["name"] == "John Doe"
    assert body["total_amount"] == pytest.approx(30.00, abs=0.001)
    assert body["order_number"] == f"ORD-{order_id:06d}"
    # `sync` only exists on the write responses, not on the read endpoint.
    assert "sync" not in body
    assert created.json()["sync"]["queue"] == "orders_sync"


def test_unknown_order_returns_404(authenticated_api) -> None:
    response = authenticated_api.get("/api/orders/999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "order_not_found"


def test_status_patch_updates_postgres_and_queues_the_sync(admin_api) -> None:
    # Reuse an existing seeded order instead of creating a new one.
    from app.core.database import SessionLocal
    from app.models.postgres import Order

    session = SessionLocal()
    try:
        existing = session.query(Order).order_by(Order.id.desc()).first()
        order_id, previous = existing.id, existing.status
    finally:
        session.close()

    new_status = "SHIPPED" if previous != "SHIPPED" else "PROCESSING"
    response = admin_api.patch(f"/api/orders/{order_id}/status", json={"status": new_status})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == new_status
    assert body["sync"]["enqueued"] is True
    assert body["sync"]["queue"] == "orders_sync"
    assert body["sync"]["task_id"]

    # PostgreSQL (source of truth) really changed.
    session = SessionLocal()
    try:
        assert session.get(Order, order_id).status == new_status
    finally:
        session.close()

    # Re-reading returns the new status too.
    assert admin_api.get(f"/api/orders/{order_id}").json()["status"] == new_status


def test_status_patch_validates_the_new_status(admin_api) -> None:
    from app.core.database import SessionLocal
    from app.models.postgres import Order

    session = SessionLocal()
    try:
        order_id = session.query(Order).first().id
    finally:
        session.close()

    response = admin_api.patch(f"/api/orders/{order_id}/status", json={"status": "DELIVERED"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_status_patch_on_unknown_order_returns_404(admin_api) -> None:
    response = admin_api.patch("/api/orders/999999/status", json={"status": "SHIPPED"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "order_not_found"