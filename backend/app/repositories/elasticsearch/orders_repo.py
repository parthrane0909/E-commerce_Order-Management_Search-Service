"""Index administration and order document writes (Elasticsearch)."""

from __future__ import annotations

from typing import Any

from app.clients.elasticsearch import get_elasticsearch_client
from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.elasticsearch.mappings import ORDER_INDEX_MAPPING, ORDER_INDEX_SETTINGS

logger = get_logger(__name__)
settings = get_settings()


def index_name() -> str:
    return settings.elasticsearch_index


def ensure_index(*, recreate: bool = False) -> bool:
    """Create the `orders` index with its mapping (idempotent).

    Returns True when the index was (re)created.
    """
    client = get_elasticsearch_client()
    name = index_name()
    exists = bool(client.indices.exists(index=name))

    if exists and recreate:
        client.indices.delete(index=name)
        logger.info("elasticsearch index %s dropped for recreation", name)
        exists = False

    if not exists:
        client.indices.create(
            index=name,
            settings=ORDER_INDEX_SETTINGS,
            mappings=ORDER_INDEX_MAPPING,
        )
        logger.info("elasticsearch index %s created with explicit mapping", name)
        return True
    return False


def delete_index() -> None:
    client = get_elasticsearch_client()
    if bool(client.indices.exists(index=index_name())):
        client.indices.delete(index=index_name())
        logger.info("elasticsearch index %s deleted", index_name())


def index_order_document(document: dict[str, Any]) -> dict[str, Any]:
    """Index (upsert) a single order document, addressed by `order_id`.

    Using the order id as the document `_id` makes the operation idempotent
    — re-running a sync task can never create duplicates.
    """
    client = get_elasticsearch_client()
    response = client.index(
        index=index_name(),
        id=str(document["order_id"]),
        document=document,
        refresh=settings.elasticsearch_refresh_on_write,
    )
    return dict(response)


def bulk_index_orders(documents: list[dict[str, Any]]) -> tuple[int, int]:
    """Bulk index many documents. Returns `(indexed, failed)`."""
    if not documents:
        return 0, 0

    client = get_elasticsearch_client()
    operations: list[dict[str, Any]] = []
    for document in documents:
        operations.append({"index": {"_index": index_name(), "_id": str(document["order_id"])}})
        operations.append(document)

    response = client.bulk(
        operations=operations,
        refresh=settings.elasticsearch_refresh_on_write,
    )
    items = response.get("items", [])
    failed = sum(1 for entry in items if entry.get("index", {}).get("error"))
    for entry in items:
        error = entry.get("index", {}).get("error")
        if error:
            logger.error("bulk index failed for document: %s", error)
    return len(items) - failed, failed


def count_documents() -> int:
    """Number of order documents currently searchable in Elasticsearch."""
    client = get_elasticsearch_client()
    response = client.count(index=index_name())
    return int(response.get("count", 0))
