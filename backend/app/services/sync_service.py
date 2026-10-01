"""Synchronisation publisher: PostgreSQL → RabbitMQ → Celery → Elasticsearch.

The API only *publishes* a task after the PostgreSQL transaction has
committed.  Building/updating the Elasticsearch document happens in the
Celery worker (`app.tasks.elasticsearch_tasks`), never in the request
cycle.

If RabbitMQ is temporarily unreachable the order is still safe — it is
already committed in PostgreSQL — and the failure is reported to the
caller instead of breaking order placement.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.orders import SyncInfo

logger = get_logger(__name__)
settings = get_settings()

EAGER_QUEUE = "in-process"


def publish_order_sync(order_id: int, reason: str) -> SyncInfo:
    """Queue `sync_order_to_elasticsearch(order_id)` on RabbitMQ.

    Returns a `SyncInfo` describing the outcome; the order itself is
    already committed at this point and is never rolled back because of
    a messaging failure.
    """
    if settings.celery_task_always_eager:
        return _run_inline(order_id, reason)

    try:
        from app.tasks.celery_app import celery_app

        result = celery_app.send_task(
            settings.sync_task_name,
            kwargs={"order_id": order_id, "reason": reason},
            queue=settings.celery_task_default_queue,
        )
        task_id = getattr(result, "id", None)
        logger.info(
            "sync task queued order_id=%s reason=%s task_id=%s queue=%s",
            order_id,
            reason,
            task_id,
            settings.celery_task_default_queue,
        )
        return SyncInfo(
            enqueued=True,
            queue=settings.celery_task_default_queue,
            task_id=task_id,
        )
    except Exception as exc:
        # PostgreSQL already committed: report the problem, never fail the order.
        logger.error(
            "failed to queue sync task for order_id=%s reason=%s: %s",
            order_id,
            reason,
            exc,
        )
        return SyncInfo(
            enqueued=False,
            queue=settings.celery_task_default_queue,
            error=f"Could not reach RabbitMQ: {exc}",
        )


def _run_inline(order_id: int, reason: str) -> SyncInfo:
    """Test-only shortcut: execute the worker task in this process."""
    from app.tasks.elasticsearch_tasks import sync_order_to_elasticsearch

    logger.info("sync task running eagerly (test mode) order_id=%s reason=%s", order_id, reason)
    async_result = sync_order_to_elasticsearch.apply(
        kwargs={"order_id": order_id, "reason": reason},
        throw=False,
    )
    if async_result.successful():
        return SyncInfo(enqueued=True, queue=EAGER_QUEUE, task_id=async_result.id)
    return SyncInfo(
        enqueued=False,
        queue=EAGER_QUEUE,
        task_id=async_result.id,
        error=str(async_result.result),
    )
