"""Pure unit tests for the Elasticsearch query builder (Screen 3).

Guards the actual query shape: bool + multi_match + range + terms +
aggregations, exactly as the assignment requires.
"""

from __future__ import annotations

import datetime as dt

from app.repositories.elasticsearch.search_repo import build_search_query
from app.schemas.search import SearchRequest


def _bool(query: SearchRequest) -> dict:
    return build_search_query(query)["bool"]


def test_default_query_filters_everything_but_returns_all_documents() -> None:
    body = build_search_query(SearchRequest())
    assert body["query"] == {"bool": {"filter": []}}
    assert "should" not in body["query"]["bool"]
    assert body["track_total_hits"] is True
    assert body["from"] == 0
    assert body["size"] == 20


def test_free_text_uses_multi_match_on_customer_and_item_fields() -> None:
    body = build_search_query(SearchRequest(query="Wireless"))
    bool_query = body["query"]["bool"]

    should = bool_query["should"]
    assert bool_query["minimum_should_match"] == 1

    top_level = should[0]["multi_match"]
    assert top_level["query"] == "Wireless"
    top_fields = [f.split("^")[0] for f in top_level["fields"]]
    assert "customer.name" in top_fields
    assert "customer.email" in top_fields
    assert "order_number" in top_fields
    # Customer name is boosted above email / order number.
    assert "customer.name^3" in top_level["fields"]

    nested = should[1]["nested"]
    assert nested["path"] == "items"
    item_fields = [f.split("^")[0] for f in nested["query"]["multi_match"]["fields"]]
    assert "items.title" in item_fields


def test_status_filter_is_a_terms_query() -> None:
    body = build_search_query(SearchRequest(status=["PENDING", "SHIPPED"]))
    assert {"terms": {"status": ["PENDING", "SHIPPED"]}} in body["query"]["bool"]["filter"]


def test_date_filter_is_an_inclusive_range_on_order_date() -> None:
    body = build_search_query(
        SearchRequest(date_from=dt.date(2026, 1, 1), date_to=dt.date(2026, 1, 31))
    )
    ranges = [c for c in body["query"]["bool"]["filter"] if "range" in c]
    order_date = ranges[0]["range"]["order_date"]

    assert order_date["gte"].startswith("2026-01-01T00:00:00")
    # inclusive upper bound: the whole day of date_to must be covered
    assert order_date["lte"].startswith("2026-01-31T23:59:59")


def test_price_filter_is_a_range_on_total_amount() -> None:
    body = build_search_query(SearchRequest(min_price=30, max_price=200))
    ranges = [c for c in body["query"]["bool"]["filter"] if "range" in c]
    assert ranges[0]["range"]["total_amount"] == {"gte": 30, "lte": 200}

    only_min = build_search_query(SearchRequest(min_price=30))
    assert {"range": {"total_amount": {"gte": 30}}} in only_min["query"]["bool"]["filter"]


def test_aggregations_sum_revenue_and_count_by_status() -> None:
    aggs = build_search_query(SearchRequest())["aggs"]

    assert aggs["revenue"] == {"sum": {"field": "total_amount"}}
    assert aggs["status_counts"]["terms"]["field"] == "status"
    assert aggs["status_counts"]["terms"]["size"] == 3


def test_pagination_translates_to_from_and_size() -> None:
    body = build_search_query(SearchRequest(page=4, limit=25))
    assert body["from"] == 75
    assert body["size"] == 25


def test_sorting_is_newest_order_first() -> None:
    body = build_search_query(SearchRequest())
    assert body["sort"][0] == {"order_date": {"order": "desc"}}
    assert body["sort"][1] == {"order_id": {"order": "desc"}}


def test_combined_filters_all_appear_in_the_filter_clause() -> None:
    body = build_search_query(
        SearchRequest(
            query="Wireless",
            status=["PROCESSING"],
            date_from=dt.date(2026, 2, 1),
            min_price=10,
            max_price=500,
        )
    )
    filters = body["query"]["bool"]["filter"]
    assert len(filters) == 3  # status + date + price
    assert any("terms" in f for f in filters)
    assert sum(1 for f in filters if "range" in f) == 2
    assert "should" in body["query"]["bool"]
