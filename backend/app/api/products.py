"""Catalog endpoints — data source: **MongoDB**.

Screen 1 (storefront) and Screen 5 (catalog admin) read and write the
product catalog here.  No PostgreSQL or Elasticsearch query is ever made
for product data.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.auth import require_admin
from app.schemas.products import (
    ProductCreate,
    ProductFacetsResponse,
    ProductListResponse,
    ProductResponse,
    ProductSort,
    ProductUpdate,
)
from app.schemas.common import ErrorResponse
from app.services import product_service

router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
        409: {"model": ErrorResponse, "description": "Duplicate SKU"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)

PRODUCT_ID = Path(..., description="MongoDB product id (ObjectId)", examples=["652f1c3e9a4b2f0012ab34cd"])


@router.get(
    "",
    response_model=ProductListResponse,
    summary="List products",
    description=(
        "Paginated product catalog read from MongoDB.  The storefront always "
        "uses `visibility=active` so deactivated products stay hidden."
    ),
)
def list_products(
    category: str | None = Query(None, description="Exact category (peripherals, audio, cables, office)"),
    tags: list[str] | None = Query(None, description="Repeatable tag; every tag must match"),
    q: str | None = Query(None, max_length=100, description="Case-insensitive search in title/description/sku/tags"),
    visibility: Literal["active", "inactive", "all"] = Query(
        "active", description="Which products to return"
    ),
    page: int = Query(1, ge=1, le=10_000),
    limit: int = Query(24, ge=1, le=100),
    sort: ProductSort = Query("newest"),
) -> ProductListResponse:
    return product_service.list_products(
        category=category,
        tags=tags,
        q=q,
        visibility=visibility,
        page=page,
        limit=limit,
        sort=sort,
    )


@router.get(
    "/facets",
    response_model=ProductFacetsResponse,
    summary="Category and tag facets",
    description="Counts used by the storefront filter bar (active products only).",
)
def product_facets() -> ProductFacetsResponse:
    return product_service.list_facets()


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get one product",
)
def get_product(product_id: str = PRODUCT_ID) -> ProductResponse:
    return product_service.get_product(product_id)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product (catalog admin)",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
def create_product(payload: ProductCreate, _admin = Depends(require_admin)) -> ProductResponse:
    return product_service.create_product(payload)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product (catalog admin)",
    description="Partial update. Changing title/price only affects the *current* catalog.",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
def update_product(
    payload: ProductUpdate,
    product_id: str = PRODUCT_ID,
    _admin = Depends(require_admin),
) -> ProductResponse:
    return product_service.update_product(product_id, payload)


@router.delete(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Deactivate a product (soft delete)",
    description=(
        "Products are deactivated rather than removed, because historical "
        "orders keep referencing them. Existing order snapshots are untouched."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
def delete_product(product_id: str = PRODUCT_ID, _admin = Depends(require_admin)) -> ProductResponse:
    return product_service.delete_product(product_id)
