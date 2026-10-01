"""Catalog (MongoDB) business logic for Screen 1 and Screen 5."""

from __future__ import annotations

import datetime as dt
from typing import Any

from app.core.errors import NotFoundError, UnprocessableError
from app.core.logging import get_logger
from app.repositories.mongo import product_repo
from app.schemas.products import (
    ProductCreate,
    ProductFacetsResponse,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)

logger = get_logger(__name__)


def _to_response(document: dict[str, Any]) -> ProductResponse:
    payload = dict(document)
    payload["_id"] = str(payload["_id"])
    payload.setdefault("description", "")
    payload.setdefault("tags", [])
    payload.setdefault("attributes", {})
    payload.setdefault("variants", [])
    payload.setdefault("active", True)
    payload.setdefault("created_at", None)
    payload.setdefault("updated_at", None)
    return ProductResponse.model_validate(payload)


def list_products(
    *,
    category: str | None = None,
    tags: list[str] | None = None,
    q: str | None = None,
    visibility: str = "active",
    page: int = 1,
    limit: int = 24,
    sort: str = "newest",
) -> ProductListResponse:
    documents, total = product_repo.list_products(
        category=category,
        tags=tags,
        q=q,
        visibility=visibility,
        page=page,
        limit=limit,
        sort=sort,
    )
    pages = (total + limit - 1) // limit if total else 0
    return ProductListResponse(
        items=[_to_response(document) for document in documents],
        page=page,
        limit=limit,
        total=total,
        pages=pages,
    )


def get_product(product_id: str) -> ProductResponse:
    document = product_repo.get_product(product_id)
    if document is None:
        raise NotFoundError(
            f"Product '{product_id}' was not found.",
            code="product_not_found",
            details={"product_id": product_id},
        )
    return _to_response(document)


def create_product(payload: ProductCreate) -> ProductResponse:
    existing = product_repo.get_product_by_sku(payload.sku)
    if existing is not None:
        from app.core.errors import ConflictError

        raise ConflictError(
            f"A product with SKU '{payload.sku}' already exists.",
            code="duplicate_sku",
            details={"field": "sku"},
        )
    document = payload.model_dump()
    document["variants"] = [variant.model_dump() for variant in payload.variants]
    created = product_repo.create_product(document)
    logger.info("product created sku=%s title=%r", created["sku"], created["title"])
    return _to_response(created)


def update_product(product_id: str, payload: ProductUpdate) -> ProductResponse:
    current = product_repo.get_product(product_id)
    if current is None:
        raise NotFoundError(
            f"Product '{product_id}' was not found.",
            code="product_not_found",
            details={"product_id": product_id},
        )

    updates = payload.model_dump(exclude_unset=True)
    if "variants" in updates:
        updates["variants"] = [
            variant.model_dump() if hasattr(variant, "model_dump") else variant
            for variant in payload.variants or []
        ]

    new_price = updates.get("price")
    if new_price is not None and new_price <= 0:
        raise UnprocessableError(
            "Price must be greater than zero.",
            code="invalid_price",
            details={"field": "price"},
        )

    updated = product_repo.update_product(product_id, updates)
    if updated is None:
        raise NotFoundError(
            f"Product '{product_id}' was not found.",
            code="product_not_found",
            details={"product_id": product_id},
        )
    logger.info("product updated id=%s fields=%s", product_id, sorted(updates))
    return _to_response(updated)


def delete_product(product_id: str) -> ProductResponse:
    """Soft delete — historical orders keep their PostgreSQL snapshot."""
    current = product_repo.get_product(product_id)
    if current is None:
        raise NotFoundError(
            f"Product '{product_id}' was not found.",
            code="product_not_found",
            details={"product_id": product_id},
        )
    updated = product_repo.delete_product(product_id)
    logger.info("product deactivated id=%s sku=%s", product_id, current.get("sku"))
    return _to_response(updated or current)


def list_facets() -> ProductFacetsResponse:
    return ProductFacetsResponse.model_validate(product_repo.list_facets())


def ensure_catalog_indexes() -> None:
    product_repo.ensure_indexes()


def catalog_stats() -> dict[str, int]:
    return {
        "active": product_repo.count_products(visibility="active"),
        "inactive": product_repo.count_products(visibility="inactive"),
        "total": product_repo.count_products(visibility="all"),
    }


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)
