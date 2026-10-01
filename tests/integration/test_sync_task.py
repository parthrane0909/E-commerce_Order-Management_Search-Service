"""Integration tests: PostgreSQL → RabbitMQ → Celery → Elasticsearch sync.

Covers the whole synchronisation contract:

* the Celery task builds the document from PostgreSQL (never MongoDB),
* writes are idempotent (`_id = order_id`, so no duplicates),
* the API publishes the task *after* COMMIT and never fails an order
  because RabbitMQ is unreachable,
* failed Elasticsearch writes are retried with exponential backoff.
"""

from __future__ import annotations

from unittest import mock

import pytest

pytestmark = pytest.mark.integration


def _latest_order_id() -> int:
    from app.core.database import SessionLocal
    from app.models.postgres import Order

    session = SessionLocal()
    try:
        return int(session.query(Order.id).order_by(Order.id.desc()).first()[0])
    finally:
        session.close()


def _es_count() -> int:
    from app.repositories.elasticsearch.orders_repo import count_documents

    return count_documents()


def _order_count() -> int:
    from app.core.database import SessionLocal
    from app.models.postgres import Order

    session = SessionLocal()
    try:
        return session.query(Order).count()
    finally:
        session.close()


# --- the Celery task -------------------------------------------------------


def test_sync_task_creates_the_document_from_postgresql(authenticated_api, order_factory, es_document, es_delete) -> None:
    from app.tasks.elasticsearch_tasks import sync_order_document

    # Create an order as the authenticated user
    created = order_factory()
    order_id = created["id"]
    es_delete(order_id)  # start from "not searchable yet"

    result = sync_order_document(order_id, reason="test")

    assert result["status"] == "indexed"
    assert result["order_id"] == order_id

    document = es_document(order_id)
    assert document is not None
    assert document["order_id"] == order_id

    # The document mirrors PostgreSQL, snapshots included.
    canonical = authenticated_api.get(f"/api/orders/{order_id}").json()
    assert document["order_number"] == canonical["order_number"]
    assert document["status"] == canonical["status"]
    assert document["total_amount"] == pytest.approx(canonical["total_amount"], abs=0.01)
    assert document["customer"]["name"] == canonical["customer"]["name"]
    assert [i["title"] for i in document["items"]] == [i["title"] for i in canonical["items"]]

    # Bookkeeping flag shown in the order details UI.
    assert canonical["search_indexed_at"] is not None


def test_sync_task_is_idempotent(authenticated_api, es_document, es_delete) -> None:
    from app.repositories.elasticsearch.orders_repo import count_documents
    from app.tasks.elasticsearch_tasks import sync_order_document

    order_id = _latest_order_id()
    es_delete(order_id)

    first = sync_order_document(order_id, reason="first")
    documents_after_first = count_documents()
    second = sync_order_document(order_id, reason="second")

    assert first["status"] == "indexed"
    assert second["status"] == "indexed"
    # Same _id => upsert, never a duplicate document.
    assert count_documents() == documents_after_first
    assert es_document(order_id) is not None


def test_sync_task_skips_orders_missing_from_postgres() -> None:
    from app.tasks.elasticsearch_tasks import sync_order_document

    assert sync_order_document(999999, reason="ghost")["status"] == "skipped"


def test_sync_task_reflects_a_status_change(admin_api, es_document, es_delete) -> None:
    from app.tasks.elasticsearch_tasks import sync_order_document

    order_id = _latest_order_id()
    target = "SHIPPED" if admin_api.get(f"/api/orders/{order_id}").json()["status"] != "SHIPPED" else "PROCESSING"

    response = admin_api.patch(f"/api/orders/{order_id}/status", json={"status": target})
    assert response.status_code == 200

    es_delete(order_id)
    sync_order_document(order_id, reason="status_update")

    document = es_document(order_id)
    assert document is not None
    assert document["status"] == target
    assert document["status"] in ("PENDING", "PROCESSING", "SHIPPED")


def test_sync_uses_postgres_snapshots_not_live_mongo_titles(authenticated_api, es_document, es_delete) -> None:
    """MongoDB says 'Wireless Mouse Pro' ($60) — ES must keep the snapshot."""
    from app.tasks.elasticsearch_tasks import sync_order_document
    from app.core.database import SessionLocal
    from app.models.postgres import OrderItem

    session = SessionLocal()
    try:
        row = session.query(OrderItem).filter(OrderItem.title == "Wireless Mouse").first()
        assert row is not None
        order_id = row.order_id
    finally:
        session.close()

    es_delete(order_id)
    sync_order_document(order_id, reason="test")

    document = es_document(order_id)
    assert document is not None
    titles = [(i["title"], i["unit_price"]) for i in document["items"]]
    assert ("Wireless Mouse", 50.16) in [(t, round(p, 2)) for t, p in titles]


def test_reindex_script_rebuilds_an_identical_index(es_purge_orphans) -> None:
    """`python -m scripts.reindex_orders` is the documented recovery path."""
    import time

    from scripts.reindex_orders import reindex_orders

    stats = None
    for _ in range(10):
        # reindex upserts; stale documents must go first.
        es_purge_orphans()
        stats = reindex_orders(recreate=False)
        if stats["elasticsearch_documents"] == stats["postgres_orders"]:
            break
        time.sleep(0.3)

    assert stats is not None
    assert stats["failed"] == 0
    assert stats["documents_built"] == stats["postgres_orders"]
    assert stats["indexed"] == stats["postgres_orders"]
    assert stats["elasticsearch_documents"] == stats["postgres_orders"]


# --- publishing from the API ----------------------------------------------


def test_successful_publish_carries_a_task_id(order_factory) -> None:
    response = order_factory()

    sync = response["sync"]
    assert sync["enqueued"] is True
    assert sync["queue"] == "orders_sync"
    assert sync["task_id"]
    assert sync["error"] is None


def test_publish_failure_never_rolls_back_a_committed_order(
    authenticated_api, product_factory, order_factory, monkeypatch
) -> None:
    from app.tasks.celery_app import celery_app

    def _boom(*_args, **_kwargs):  # noqa: ANN003
        raise ConnectionError("broker is down")

    monkeypatch.setattr(celery_app, "send_task", _boom)

    orders_before = _order_count()
    product = product_factory(price=15.00)

    body = order_factory(items=[{"product_id": str(product["_id"]), "quantity": 1}])

    # The order itself committed successfully...
    assert body["total_amount"] == pytest.approx(15.00, abs=0.001)
    assert _order_count() == orders_before + 1

    # ...and the messaging failure is reported instead of thrown away.
    sync = body["sync"]
    assert sync["enqueued"] is False
    assert sync["error"]
    assert "RabbitMQ" in sync["error"] or "broker" in sync["error"]

    # The order is readable from PostgreSQL regardless.
    assert authenticated_api.get(f"/api/orders/{body['id']}").status_code == 200


def test_status_update_publish_failure_does_not_break_the_update(admin_api, authenticated_api, order_factory, monkeypatch) -> None:
    from app.tasks.celery_app import celery_app

    def _boom(*_args, **_kwargs):  # noqa: ANN003
        raise ConnectionError("broker is down")

    monkeypatch.setattr(celery_app, "send_task", _boom)

    # Create an order as the authenticated user
    created = order_factory()
    order_id = created["id"]
    current = authenticated_api.get(f"/api/orders/{order_id}").json()["status"]
    target = "PROCESSING" if current != "PROCESSING" else "SHIPPED"

    response = admin_api.patch(f"/api/orders/{order_id}/status", json={"status": target})

    assert response.status_code == 200, response.text
    assert response.json()["status"] == target
    assert response.json()["sync"]["enqueued"] is False
    assert response.json()["sync"]["error"]


# --- retry behaviour -------------------------------------------------------


def test_task_retries_with_backoff_when_elasticsearch_fails() -> None:
    from celery.exceptions import Retry

    from app.tasks import elasticsearch_tasks as module

    with mock.patch.object(
        module, "sync_order_document", side_effect=ConnectionError("cluster red")
    ) as stub:
        with pytest.raises(Retry):
            module.sync_order_to_elasticsearch.apply(
                kwargs={"order_id": 1, "reason": "test"}, throw=True
            )

    # The attempt was retried rather than silently swallowed.
    assert stub.call_count >= 1


def test_task_gives_up_after_max_retries(monkeypatch) -> None:
    from app.core.config import get_settings
    from app.tasks import elasticsearch_tasks as module

    settings = get_settings()
    monkeypatch.setattr(settings, "celery_max_retries", 1)

    with mock.patch.object(
        module, "sync_order_document", side_effect=ConnectionError("cluster red")
    ) as stub:
        result = module.sync_order_to_elasticsearch.apply(
            kwargs={"order_id": 1, "reason": "test"}, throw=False
        )

    assert result.state == "FAILURE"
    assert isinstance(result.result, ConnectionError)
    # initial attempt + one retry, then it stops.
    assert stub.call_count == 2


def test_sync_task_is_registered_with_the_expected_name() -> None:
    from app.tasks.celery_app import celery_app
    from app.tasks.elasticsearch_tasks import TASK_NAME

    assert TASK_NAME in celery_app.tasks


def test_elasticsearch_holds_exactly_one_document_per_postgres_order(
    es_purge_orphans,
) -> None:
    """Seed invariant: the searchable copy mirrors every PostgreSQL order."""
    import time

    es_purge_orphans()

    # The worker may still be finishing a task started before cleanup.
    for _ in range(10):
        if _es_count() == _order_count():
            break
        time.sleep(0.3)
        es_purge_orphans()

    assert _es_count() == _order_count()
