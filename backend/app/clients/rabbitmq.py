"""RabbitMQ helpers.

Task publishing goes through Celery's `send_task()` (see
`app.services.sync_service`), which writes to the same RabbitMQ queue the
worker consumes.  This module only provides connectivity probing for the
health endpoint.
"""

from __future__ import annotations

from kombu import Connection

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def ping_rabbitmq(timeout: float = 3.0) -> bool:
    """Open (and immediately release) an AMQP connection as a probe."""
    connection = Connection(settings.broker_url, connect_timeout=timeout, read_timeout=timeout)
    try:
        connection.connect()
        return True
    except Exception as exc:  # pragma: no cover - depends on infra state
        logger.warning("rabbitmq ping failed: %s", exc)
        return False
    finally:
        try:
            connection.release()
        except Exception:  # pragma: no cover - release is best effort
            pass
