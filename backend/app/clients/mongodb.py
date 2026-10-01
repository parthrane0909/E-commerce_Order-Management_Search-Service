"""MongoDB client — holds the flexible product catalog."""

from __future__ import annotations

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    """Return (and reuse) the shared PyMongo client."""
    global _client
    if _client is None:
        _client = MongoClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=settings.mongo_timeout_ms,
            connectTimeoutMS=settings.mongo_timeout_ms,
            socketTimeoutMS=settings.mongo_timeout_ms,
            # return timezone aware UTC datetimes (created_at / updated_at)
            tz_aware=True,
        )
        logger.info("mongodb client created for %s (db=%s)", settings.mongo_uri, settings.mongo_db)
    return _client


def get_mongo_db() -> Database:
    """Return the catalog database."""
    return get_mongo_client()[settings.mongo_db]


def ping_mongo() -> bool:
    """Cheap connectivity probe used by the health endpoint."""
    try:
        get_mongo_client().admin.command("ping")
        return True
    except PyMongoError as exc:
        logger.warning("mongodb ping failed: %s", exc)
        return False


def close_mongo_client() -> None:
    """Close the shared client during shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("mongodb client closed")
