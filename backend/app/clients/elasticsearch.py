"""Elasticsearch client — search/analytics representation of orders."""

from __future__ import annotations

from elasticsearch import Elasticsearch

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client: Elasticsearch | None = None


def get_elasticsearch_client() -> Elasticsearch:
    """Return (and reuse) the shared Elasticsearch client."""
    global _client
    if _client is None:
        kwargs: dict[str, object] = {
            "hosts": [settings.elasticsearch_url],
            "request_timeout": settings.elasticsearch_timeout,
            "retry_on_timeout": True,
            "max_retries": 3,
        }
        if settings.elasticsearch_api_key:
            kwargs["api_key"] = settings.elasticsearch_api_key
        _client = Elasticsearch(**kwargs)  # type: ignore[arg-type]
        logger.info("elasticsearch client created for %s", settings.elasticsearch_url)
    return _client


def ping_elasticsearch() -> bool:
    """Cheap connectivity probe used by the health endpoint."""
    try:
        return bool(get_elasticsearch_client().ping())
    except Exception as exc:  # pragma: no cover - depends on infra state
        logger.warning("elasticsearch ping failed: %s", exc)
        return False


def close_elasticsearch_client() -> None:
    """Close the shared client during shutdown."""
    global _client
    if _client is not None:
        try:
            _client.close()
        finally:
            _client = None
            logger.info("elasticsearch client closed")
