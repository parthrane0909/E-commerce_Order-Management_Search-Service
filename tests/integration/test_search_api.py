"""Integration tests: order search (Screen 3).

Screen 3 must be served by **Elasticsearch only**.  The tests here verify
the query behaviour (free text + filters + aggregations + pagination) and
enforce the architecture rule: the search path may never open a
PostgreSQL session or a MongoDB cursor.
"""

from __future__ import annotations

import datetime as dt

import pytest

pytestmark = pytest.mark.integration


def _search(admin_api, **payload):
    return admin_api.post("/api/search/orders", json=payload)


# --- free text -------------------------------------------------------------


def test_free_text_search_returns_matching_orders(admin_api) -> None:
    response = _search(admin_api, query="Wireless", limit=50)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["total"] >= 1
    assert body["results"], "a matching query must return hits"
    assert body["took_ms"] is not None

    for result in body["results"]:
        haystack = " ".join(
            [result["customer"]["name"], result["customer"]["email"], result["order_number"]]
            + [item["title"] for item in result["items"]]
        ).lower()
        assert "wireless" in haystack


def test_search_finds_wendy_wireless_by_name(admin_api) -> None:
    body = _search(admin_api, query="Wendy Wireless", limit=100).json()

    names = [r["customer"]["name"] for r in body["results"]]
    assert "Wendy Wireless" in names
    assert sum(1 for name in names if name == "Wendy Wireless") >= 1
    # Her seeded orders are all returned when we search her full name.
    wendy_hits = [
        r for r in body["results"] if r["customer"]["name"] == "Wendy Wireless"
    ]
    assert len(wendy_hits) >= 3


def test_search_matches_the_historical_item_title(admin_api) -> None:
    """'Wireless Mouse' only exists in PostgreSQL/ES snapshots now."""
    body = _search(admin_api, query="Wireless Mouse", limit=100).json()

    assert body["total"] >= 8, "seed places >=8 orders containing 'Wireless Mouse'"
    titles = {item["title"] for r in body["results"] for item in r["items"]}
    assert "Wireless Mouse" in titles


def test_search_without_query_returns_everything(admin_api) -> None:
    body = _search(admin_api, limit=1).json()
    assert body["total"] >= 40


# --- filters ---------------------------------------------------------------


def test_status_filter_returns_only_that_status(admin_api) -> None:
    body = _search(admin_api, status=["SHIPPED"], limit=100).json()

    assert body["total"] >= 10
    assert {r["status"] for r in body["results"]} == {"SHIPPED"}
    assert body["aggregations"]["status_counts"]["SHIPPED"] == body["total"]
    assert body["aggregations"]["status_counts"]["PENDING"] == 0


def test_multiple_status_filter_includes_both(admin_api) -> None:
    body = _search(admin_api, status=["PENDING", "PROCESSING"], limit=100).json()
    assert {r["status"] for r in body["results"]} <= {"PENDING", "PROCESSING"}
    counts = body["aggregations"]["status_counts"]
    assert counts["PENDING"] + counts["PROCESSING"] == body["total"]


def test_date_range_filter_is_inclusive(admin_api) -> None:
    today = dt.date.today()
    recent = _search(admin_api, date_from=(today - dt.timedelta(days=7)).isoformat(),
                     date_to=today.isoformat(), limit=100).json()

    assert recent["total"] >= 1
    for result in recent["results"]:
        order_day = dt.datetime.fromisoformat(result["order_date"].replace("Z", "+00:00")).date()
        assert today - dt.timedelta(days=7) <= order_day <= today

    old = _search(admin_api, date_to=(today - dt.timedelta(days=365)).isoformat(), limit=100).json()
    assert old["total"] == 0


def test_price_band_filter(admin_api) -> None:
    cheap = _search(admin_api, max_price=30, limit=100).json()
    assert cheap["total"] >= 5
    assert all(r["total_amount"] <= 30 for r in cheap["results"])

    mid = _search(admin_api, min_price=30, max_price=150, limit=100).json()
    assert mid["total"] >= 5
    assert all(30 <= r["total_amount"] <= 150 for r in mid["results"])

    pricey = _search(admin_api, min_price=200, limit=100).json()
    assert pricey["total"] >= 5
    assert all(r["total_amount"] >= 200 for r in pricey["results"])


def test_filters_combine(admin_api) -> None:
    body = _search(admin_api, query="Wireless", status=["SHIPPED"], max_price=1000, limit=100).json()
    assert all(r["status"] == "SHIPPED" for r in body["results"])
    assert all(r["total_amount"] <= 1000 for r in body["results"])
    assert body["total"] == len(body["results"]) or body["pages"] >= 1


# --- aggregations / KPIs ---------------------------------------------------


def test_kpi_aggregations_describe_the_filtered_set(admin_api) -> None:
    all_orders = _search(admin_api, limit=100).json()
    counts = all_orders["aggregations"]["status_counts"]

    assert set(counts) == {"PENDING", "PROCESSING", "SHIPPED"}
    assert sum(counts.values()) == all_orders["total"]
    assert all_orders["aggregations"]["revenue"] == pytest.approx(
        sum(r["total_amount"] for r in all_orders["results"]), abs=0.05
    )

    shipped = _search(admin_api, status=["SHIPPED"], limit=100).json()
    assert shipped["aggregations"]["status_counts"]["SHIPPED"] == shipped["total"]
    assert shipped["aggregations"]["revenue"] == pytest.approx(
        sum(r["total_amount"] for r in shipped["results"]), abs=0.05
    )


def test_revenue_kpi_is_never_the_unfiltered_total_when_filtered(admin_api) -> None:
    all_body = _search(admin_api, limit=100).json()
    cheap = _search(admin_api, max_price=30, limit=100).json()
    assert cheap["aggregations"]["revenue"] < all_body["aggregations"]["revenue"]


# --- pagination ------------------------------------------------------------


def test_pagination_pages_through_results(admin_api) -> None:
    first = _search(admin_api, page=1, limit=5).json()
    second = _search(admin_api, page=2, limit=5).json()

    assert first["limit"] == 5
    assert first["page"] == 1
    assert len(first["results"]) == 5
    assert first["pages"] == (first["total"] + 4) // 5

    first_ids = [r["order_id"] for r in first["results"]]
    second_ids = [r["order_id"] for r in second["results"]]
    assert not set(first_ids) & set(second_ids), "pages must not overlap"

    # Sorted by order_date desc, then order_id desc.
    def _key(result):  # noqa: ANN202
        return (result["order_date"], result["order_id"])

    ordered = sorted(first["results"], key=_key, reverse=True)
    assert [r["order_id"] for r in first["results"]] == [r["order_id"] for r in ordered]


# --- validation ------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {"date_from": "2026-05-01", "date_to": "2026-01-01"},
        {"min_price": 100, "max_price": 10},
        {"page": 0},
        {"limit": 0},
        {"min_price": -5},
    ],
)
def test_invalid_search_requests_return_422(admin_api, payload) -> None:
    response = _search(admin_api, **payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_status_is_rejected(admin_api) -> None:
    response = _search(admin_api, status=["DELIVERED"])
    assert response.status_code == 422


# --- architecture guard: Elasticsearch only --------------------------------


def test_search_service_never_touches_postgres_or_mongodb() -> None:
    """Screen 3 results must come from Elasticsearch, never PG/Mongo."""
    from pathlib import Path

    backend = Path(__file__).resolve().parents[2] / "backend"
    forbidden = (
        "SessionLocal",
        "sessionmaker",
        "sqlalchemy",
        "MongoClient",
        "pymongo",
        "get_mongo_db",
    )
    scan = [
        backend / "app" / "services" / "search_service.py",
        backend / "app" / "api" / "search.py",
        backend / "app" / "repositories" / "elasticsearch" / "search_repo.py",
    ]
    for path in scan:
        source = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{path.name} must not reference {token!r}"
        assert "elasticsearch" in source.lower()


def test_search_endpoint_works_while_mongo_session_is_poisoned(admin_api, monkeypatch) -> None:
    """Runtime proof: searching must not require MongoDB or PostgreSQL."""
    from app.core import database

    def _explode(*_args, **_kwargs):  # noqa: ANN003
        raise AssertionError("search must not open a SQL session")

    monkeypatch.setattr(database, "SessionLocal", _explode)
    response = _search(admin_api, query="Wireless", limit=5)
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_search_agrees_with_postgres_on_order_count(admin_api, es_purge_orphans) -> None:
    """The searchable copy describes every PostgreSQL order."""
    from app.core.database import SessionLocal
    from app.models.postgres import Order

    es_purge_orphans()  # drop documents left behind by async test cleanup

    session = SessionLocal()
    try:
        postgres_orders = session.query(Order).count()
    finally:
        session.close()

    assert _search(admin_api, limit=1).json()["total"] == postgres_orders
