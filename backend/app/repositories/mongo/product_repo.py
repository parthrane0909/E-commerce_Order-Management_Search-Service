"""Product catalog repository (MongoDB).

All catalog reads and writes for Screen 1 (storefront) and Screen 5
(catalog admin) go through this module.  Orders are *never* read from
MongoDB — PostgreSQL owns those.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.clients.mongodb import get_mongo_db
from app.core.errors import ConflictError

PRODUCTS = "products"

SORT_OPTIONS: dict[str, list[tuple[str, int]]] = {
    "newest": [("created_at", DESCENDING), ("_id", DESCENDING)],
    "title_asc": [("title", ASCENDING)],
    "price_asc": [("price", ASCENDING)],
    "price_desc": [("price", DESCENDING)],
}


def _collection() -> Collection:
    return get_mongo_db()[PRODUCTS]


def to_object_id(value: str) -> ObjectId | None:
    """Convert a path/query id into an ObjectId, or None when invalid."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def ensure_indexes() -> None:
    """Create the indexes the catalog queries rely on (idempotent)."""
    collection = _collection()
    collection.create_index([("sku", ASCENDING)], unique=True, name="uniq_products_sku")
    collection.create_index([("category", ASCENDING)], name="ix_products_category")
    collection.create_index([("active", ASCENDING)], name="ix_products_active")
    collection.create_index([("created_at", DESCENDING)], name="ix_products_created_at")


#: Which products a query may return: storefront always uses "active".
VISIBILITY_CHOICES = ("active", "inactive", "all")


def _build_filter(
    *,
    category: str | None = None,
    tags: list[str] | None = None,
    q: str | None = None,
    visibility: str = "active",
) -> dict[str, Any]:
    query: dict[str, Any] = {}

    if visibility == "active":
        query["active"] = True
    elif visibility == "inactive":
        query["active"] = False

    if category:
        query["category"] = category.strip().lower()

    if tags:
        query["tags"] = {"$all": [tag.strip().lower() for tag in tags if tag.strip()]}

    if q and q.strip():
        pattern = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [
            {"title": pattern},
            {"description": pattern},
            {"sku": pattern},
            {"tags": pattern},
        ]
    return query


def list_products(
    *,
    category: str | None = None,
    tags: list[str] | None = None,
    q: str | None = None,
    visibility: str = "active",
    page: int = 1,
    limit: int = 24,
    sort: str = "newest",
) -> tuple[list[dict[str, Any]], int]:
    """Return `(documents, total)` for the requested catalogue slice."""
    if visibility not in VISIBILITY_CHOICES:
        raise ValueError(f"visibility must be one of {VISIBILITY_CHOICES}")
    query = _build_filter(category=category, tags=tags, q=q, visibility=visibility)

    collection = _collection()
    total = collection.count_documents(query)
    cursor = (
        collection.find(query)
        .sort(SORT_OPTIONS.get(sort, SORT_OPTIONS["newest"]))
        .skip(max(page - 1, 0) * limit)
        .limit(limit)
    )
    return list(cursor), total


def get_product(product_id: str) -> dict[str, Any] | None:
    """Fetch a single product by its MongoDB ObjectId string."""
    oid = to_object_id(product_id)
    if oid is None:
        return None
    return _collection().find_one({"_id": oid})


def get_products_by_ids(product_ids: list[str]) -> list[dict[str, Any]]:
    """Bulk fetch used by checkout to validate the cart in one round trip."""
    oids = [oid for oid in (to_object_id(pid) for pid in product_ids) if oid is not None]
    if not oids:
        return []
    return list(_collection().find({"_id": {"$in": oids}}))


def get_product_by_sku(sku: str, exclude_id: str | None = None) -> dict[str, Any] | None:
    query: dict[str, Any] = {"sku": sku.strip()}
    if exclude_id:
        oid = to_object_id(exclude_id)
        if oid is not None:
            query["_id"] = {"$ne": oid}
    return _collection().find_one(query)


def create_product(document: dict[str, Any]) -> dict[str, Any]:
    """Insert a new product; raises ConflictError when the SKU exists."""
    now = dt.datetime.now(dt.timezone.utc)
    payload = {**document, "created_at": now, "updated_at": now}
    try:
        result = _collection().insert_one(payload)
    except DuplicateKeyError as exc:
        raise ConflictError(
            f"A product with SKU '{document.get('sku')}' already exists.",
            code="duplicate_sku",
            details={"field": "sku"},
        ) from exc
    payload["_id"] = result.inserted_id
    return payload


def update_product(product_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Apply a partial update to a product document."""
    oid = to_object_id(product_id)
    if oid is None:
        return None
    if not updates:
        return get_product(product_id)
    if "sku" in updates:
        existing = get_product_by_sku(updates["sku"], exclude_id=product_id)
        if existing is not None:
            raise ConflictError(
                f"A product with SKU '{updates['sku']}' already exists.",
                code="duplicate_sku",
                details={"field": "sku"},
            )
    updates = {**updates, "updated_at": dt.datetime.now(dt.timezone.utc)}
    try:
        return _collection().find_one_and_update(
            {"_id": oid},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError as exc:
        raise ConflictError(
            "A product with this SKU already exists.",
            code="duplicate_sku",
            details={"field": "sku"},
        ) from exc


def delete_product(product_id: str) -> dict[str, Any] | None:
    """Soft-delete: products referenced by historical orders stay intact."""
    return update_product(product_id, {"active": False})


def list_facets(*, include_inactive: bool = False) -> dict[str, list[dict[str, Any]]]:
    """Category and tag counts used by the storefront filter bar."""
    match: dict[str, Any] = {}
    if not include_inactive:
        match["active"] = True

    pipeline = [
        {"$match": match},
        {
            "$facet": {
                "categories": [
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                    {"$sort": {"count": DESCENDING, "_id": ASCENDING}},
                ],
                "tags": [
                    {"$unwind": "$tags"},
                    {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
                    {"$sort": {"count": DESCENDING, "_id": ASCENDING}},
                    {"$limit": 40},
                ],
            }
        },
    ]
    result = list(_collection().aggregate(pipeline))
    if not result:
        return {"categories": [], "tags": []}
    facet = result[0]
    return {
        "categories": [{"value": item["_id"], "count": item["count"]} for item in facet["categories"]],
        "tags": [{"value": item["_id"], "count": item["count"]} for item in facet["tags"]],
    }


def count_products(*, visibility: str = "active") -> int:
    query = _build_filter(visibility=visibility)
    return _collection().count_documents(query)


def delete_all_products() -> None:
    """Drop every product document (used by the reproducible seed)."""
    _collection().drop()
