"""Search endpoint — data source: **Elasticsearch only**.

Screen 3 (admin search dashboard) calls this endpoint.  It never reads
PostgreSQL or MongoDB: Elasticsearch holds the searchable/analytics copy
of every order.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.auth import get_current_user
from app.core.auth import require_admin
from app.schemas.common import ErrorResponse
from app.schemas.search import SearchRequest, SearchResponse
from app.services import search_service

router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
    responses={
        400: {"model": ErrorResponse, "description": "Search request could not be executed"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        503: {"model": ErrorResponse, "description": "Elasticsearch unavailable"},
    },
)


@router.post(
    "/orders",
    response_model=SearchResponse,
    summary="Search orders (full-text + filters + aggregations)",
    description=(
        "Runs a single Elasticsearch query:\n\n"
        "* `multi_match` across `customer.name`, `customer.email`, "
        "`order_number` and the nested `items.title`\n"
        "* `terms` filter on status\n"
        "* `range` filters on `order_date` and `total_amount`\n"
        "* aggregations: `sum(total_amount)` (revenue KPI) and document "
        "count per status\n\n"
        "KPI values therefore always describe the *current filter set*.\n"
        "Admin only."
    ),
    status_code=status.HTTP_200_OK,
)
def search_orders(payload: SearchRequest, _admin = Depends(require_admin)) -> SearchResponse:
    return search_service.search_orders(payload)
