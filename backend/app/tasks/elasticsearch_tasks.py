"""Celery tasks: PostgreSQL → Elasticsearch synchronisation.

One task handles both cases:

* a new order was committed  (`reason="order_created"`)
* an order status changed    (`reason="status_update"`)

The task always rebuilds the whole document from PostgreSQL, which keeps
the worker idempotent and guarantees the searchable copy can never
diverge from the source of truth.
"""

from __future__ import annotations

from typing import Any

from celery.exceptions import MaxRetriesExceededError

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.repositories.elasticsearch.document import build_order_document
from app.repositories.elasticsearch.orders_repo import ensure_index, index_order_document
from app.repositories.postgres import order_repo
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)
settings = get_settings()

TASK_NAME = "app.tasks.elasticsearch_tasks.sync_order_to_elasticsearch"


def _record_indexed_at(order_id: int) -> None:
    """Bookkeeping only: expose 'indexed in ES' inside the order details UI."""
    session = SessionLocal()
    try:
        session.begin()
        order_repo.mark_search_indexed(session, order_id)
        session.commit()
    except Exception as exc:  # pragma: no cover - bookkeeping must not fail the task
        session.rollback()
        logger.warning("could not record search_indexed_at for order_id=%s: %s", order_id, exc)
    finally:
        session.close()


def sync_order_document(order_id: int, reason: str = "unknown") -> dict[str, Any]:
    """Synchronous core of the task — also reused by the reindex script."""
    session = SessionLocal()
    try:
        order = order_repo.get_order(session, order_id)
        if order is None:
            logger.warning("order_id=%s not present in PostgreSQL — nothing to index", order_id)
            return {"status": "skipped", "order_id": order_id}
        document = build_order_document(order)
    finally:
        session.close()

    ensure_index()
    response = index_order_document(document)
    _record_indexed_at(order_id)
    logger.info(
        "elasticsearch synchronised order_id=%s number=%s status=%s reason=%s version=%s",
        order_id,
        document.get("order_number"),
        document.get("status"),
        reason,
        response.get("_version"),
    )
    return {
        "status": "indexed",
        "order_id": order_id,
        "reason": reason,
        "version": response.get("_version"),
    }


@celery_app.task(bind=True, name=TASK_NAME, acks_late=True)
def sync_order_to_elasticsearch(self, order_id: int, reason: str = "unknown") -> dict[str, Any]:
    """Build/refresh the Elasticsearch document for a PostgreSQL order.

    Failure behaviour: any error (typically Elasticsearch being down)
    causes a retried delivery with exponential backoff.  PostgreSQL stays
    authoritative the whole time — a lagging or missing ES document never
    affects order data.
    """
    retries = int(getattr(self.request, "retries", 0) or 0)
    logger.info(
        "celery task start task=%s order_id=%s reason=%s attempt=%s",
        TASK_NAME,
        order_id,
        reason,
        retries + 1,
    )
    try:
        return sync_order_document(order_id, reason)
    except Exception as exc:
        if retries >= settings.celery_max_retries or isinstance(exc, MaxRetriesExceededError):
            logger.error(
                "celery task failed permanently order_id=%s after %s attempts: %s",
                order_id,
                retries,
                exc,
                exc_info=True,
            )
            raise
        countdown = min(
            settings.celery_retry_backoff_max,
            settings.celery_retry_backoff * (2**retries),
        )
        logger.warning(
            "celery task attempt %s failed order_id=%s reason=%s — retrying in %ss: %s",
            retries + 1,
            order_id,
            reason,
            countdown,
            exc,
        )
        raise self.retry(exc=exc, countdown=countdown)
