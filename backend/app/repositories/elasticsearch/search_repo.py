"""Elasticsearch order search (Screen 3).

`build_search_query()` is a pure function that turns a `SearchRequest`
into a single Elasticsearch query body (bool + multi_match + range +
terms + aggregations), which makes it directly unit-testable without a
running cluster.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from app.clients.elasticsearch import get_elasticsearch_client
from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.elasticsearch.orders_repo import ensure_index, index_name
from app.schemas.search import (
    DEFAULT_STATUS_COUNTS,
    SearchAggregations,
    SearchRequest,
    SearchResponse,
    SearchResult,
)

logger = get_logger(__name__)
settings = get_settings()

UTC = dt.timezone.utc

#: Fields covered by the top level `multi_match` (customer side).
TEXT_FIELDS = ["customer.name^3", "customer.email", "order_number"]
#: Fields covered by the nested `multi_match` (line item side).
NESTED_TEXT_FIELDS = ["items.title^2"]


def _start_of_day(value: dt.date) -> str:
    return dt.datetime(value.year, value.month, value.day, tzinfo=UTC).isoformat()


def _end_of_day(value: dt.date) -> str:
    return (
        dt.datetime(value.year, value.month, value.day, 23, 59, 59, 999999, tzinfo=UTC).isoformat()
    )


def build_search_query(request: SearchRequest) -> dict[str, Any]:
    """Translate the API request into an Elasticsearch query body."""
    filters: list[dict[str, Any]] = []
    should: list[dict[str, Any]] = []

    if request.status:
        filters.append({"terms": {"status": list(request.status)}})

    if request.date_from or request.date_to:
        range_clause: dict[str, str] = {}
        if request.date_from:
            range_clause["gte"] = _start_of_day(request.date_from)
        if request.date_to:
            # inclusive: include every order placed on `date_to`
            range_clause["lte"] = _end_of_day(request.date_to)
        filters.append({"range": {"order_date": range_clause}})

    if request.min_price is not None or request.max_price is not None:
        price_clause: dict[str, float] = {}
        if request.min_price is not None:
            price_clause["gte"] = request.min_price
        if request.max_price is not None:
            price_clause["lte"] = request.max_price
        filters.append({"range": {"total_amount": price_clause}})

    text = (request.query or "").strip()
    if text:
        should.append(
            {
                "multi_match": {
                    "query": text,
                    "fields": TEXT_FIELDS,
                    "type": "bool_prefix",
                    "operator": "or",
                }
            }
        )
        should.append(
            {
                "nested": {
                    "path": "items",
                    "score_mode": "max",
                    "query": {
                        "multi_match": {
                            "query": text,
                            "fields": NESTED_TEXT_FIELDS,
                            "type": "bool_prefix",
                            "operator": "or",
                        }
                    },
                }
            }
        )

    bool_query: dict[str, Any] = {"filter": filters}
    if should:
        bool_query["should"] = should
        # Required: `should` would otherwise be optional once filters exist.
        bool_query["minimum_should_match"] = 1

    offset = (request.page - 1) * request.limit
    return {
        "query": {"bool": bool_query},
        "aggs": {
            "revenue": {"sum": {"field": "total_amount"}},
            "status_counts": {"terms": {"field": "status", "size": len(DEFAULT_STATUS_COUNTS)}},
        },
        "sort": [
            {"order_date": {"order": "desc"}},
            {"order_id": {"order": "desc"}},
        ],
        "from": offset,
        "size": request.limit,
        "track_total_hits": True,
    }


def _parse_results(response: dict[str, Any]) -> tuple[list[SearchResult], int, int]:
    hits = response.get("hits", {})
    total_value = hits.get("total", {})
    total = int(total_value.get("value", 0)) if isinstance(total_value, dict) else int(total_value or 0)
    results = [SearchResult.model_validate(hit["_source"]) for hit in hits.get("hits", [])]
    return results, total, int(response.get("took", 0))


def _parse_aggregations(response: dict[str, Any]) -> SearchAggregations:
    aggregations = response.get("aggregations", {})
    revenue = round(float(aggregations.get("revenue", {}).get("value", 0.0) or 0.0), 2)

    counts = dict(DEFAULT_STATUS_COUNTS)
    for bucket in aggregations.get("status_counts", {}).get("buckets", []):
        counts[str(bucket.get("key"))] = int(bucket.get("doc_count", 0))
    return SearchAggregations(revenue=revenue, status_counts=counts)


def search_orders(request: SearchRequest) -> SearchResponse:
    """Run the query against Elasticsearch and shape the API response."""
    body = build_search_query(request)
    client = get_elasticsearch_client()

    response = client.search(
        index=index_name(),
        query=body["query"],
        aggs=body["aggs"],
        sort=body["sort"],
        size=body["size"],
        from_=body["from"],
        track_total_hits=True,
    )

    results, total, took_ms = _parse_results(response)
    aggregations = _parse_aggregations(response)
    pages = (total + request.limit - 1) // request.limit if total else 0

    logger.info(
        "elasticsearch search query=%r status=%s hits=%s took=%sms",
        request.query,
        list(request.status),
        total,
        took_ms,
    )
    return SearchResponse(
        results=results,
        total=total,
        page=request.page,
        limit=request.limit,
        pages=pages,
        took_ms=took_ms,
        aggregations=aggregations,
    )


def search_orders_with_index(request: SearchRequest) -> SearchResponse:
    """Same as `search_orders`, creating the index on first use."""
    try:
        return search_orders(request)
    except Exception as exc:
        if getattr(exc, "status_code", None) != 404:
            raise
        logger.warning("orders index missing (%s) — creating it and retrying", exc)
        ensure_index()
        return search_orders(request)
