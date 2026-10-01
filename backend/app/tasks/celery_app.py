"""Celery application.

RabbitMQ is the broker: the FastAPI process publishes tasks with
`send_task()` and `celery-worker` consumes them from the
`orders_sync` queue.

Run the worker with:

    celery -A app.tasks.celery_app worker --loglevel=INFO
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ecommerce_orders",
    broker=settings.broker_url,
    backend=None,  # results are not needed: the DB + ES are the state
)

celery_app.conf.update(
    # --- transport -------------------------------------------------------
    broker_connection_retry_on_startup=True,
    broker_transport_options={"confirm_publish": True, "visibility_timeout": 3600},
    task_default_queue=settings.celery_task_default_queue,
    # The worker imports this module at boot to register every task.
    imports=["app.tasks.elasticsearch_tasks"],
    # --- serialisation ---------------------------------------------------
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # --- reliability -----------------------------------------------------
    # Re-queue unacknowledged work if a worker dies mid-task. Combined with
    # `_id = order_id` indexing this gives *at-least-once* semantics.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_time_limit=120,
    task_soft_time_limit=90,
    # --- test mode -------------------------------------------------------
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=False,
)

__all__ = ["celery_app"]


if __name__ == "__main__":  # pragma: no cover - manual CLI entry point
    celery_app.start()
