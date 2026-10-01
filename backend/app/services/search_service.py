"""Search business logic (Screen 3).

Screen 3 is the search/analytics interface: **Elasticsearch only**.
This service deliberately never opens a PostgreSQL session or a MongoDB
cursor for result data — PostgreSQL stays the source of truth for order
*details*, not for search.
"""

from __future__ import annotations

from app.core.errors import AppError, DependencyUnavailableError
from app.core.logging import get_logger
from app.repositories.elasticsearch import search_repo
from app.schemas.search import SearchRequest, SearchResponse

logger = get_logger(__name__)


def _short(reason: object, limit: int = 300) -> str:
    text = str(reason)
    return text if len(text) <= limit else f"{text[:limit]}…"


def search_orders(request: SearchRequest) -> SearchResponse:
    """Run the Elasticsearch query and map failures to API errors."""
    try:
        return search_repo.search_orders_with_index(request)
    except AppError:
        raise
    except Exception as exc:
        status = getattr(exc, "status_code", None)
        if status == 400:
            logger.warning("elasticsearch rejected the query: %s", exc)
            raise AppError(
                "Elasticsearch could not understand the search request.",
                code="search_query_invalid",
                status_code=400,
                details={"reason": _short(exc)},
            ) from exc
        logger.error("elasticsearch search failed: %s", exc, exc_info=True)
        raise DependencyUnavailableError(
            "Order search is temporarily unavailable. PostgreSQL still holds "
            "every order — try again shortly or rebuild the index.",
            code="search_unavailable",
            details={"reason": _short(exc)},
        ) from exc
