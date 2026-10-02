"""Catalog endpoints — data source: **MongoDB**.

Screen 1 (storefront) and Screen 5 (catalog admin) read and write the
product catalog here.  No PostgreSQL or Elasticsearch query is ever made
for product data.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path as FsPath
from typing import Literal

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.auth import require_admin
from app.core.config import get_settings
from app.core.errors import NotFoundError, UnprocessableError
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
from app.repositories.mongo import product_repo

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

# Image upload configuration (root comes from Settings.UPLOADS_DIR)
settings = get_settings()
UPLOAD_ROOT = settings.uploads_path
UPLOAD_DIR = UPLOAD_ROOT / "products"
UPLOAD_URL_PREFIX = "/uploads/"
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _stored_image_path(image_url: str) -> FsPath | None:
    """Map a stored `image_url` back to a file inside the upload root.

    Only paths that resolve inside `UPLOAD_ROOT` are returned, so front-end
    assets such as `/products/DESK-001.svg` can never be deleted by mistake.
    """
    rel = str(image_url or "").split("?")[0]
    if rel.startswith("/"):
        rel = rel[1:]
    if not rel.startswith("uploads/"):
        return None
    rel = rel[len("uploads/"):]
    candidate = (UPLOAD_ROOT / rel).resolve()
    try:
        candidate.relative_to(UPLOAD_ROOT.resolve())
    except ValueError:
        return None
    return candidate


def _validate_image_file(file: UploadFile) -> None:
    if not file.filename:
        raise UnprocessableError("No filename provided.", code="invalid_image", details={"field": "image"})
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise UnprocessableError(
            f"Unsupported image format. Allowed: JPEG, PNG, WebP, SVG.",
            code="invalid_image_format",
            details={"field": "image", "allowed": sorted(ALLOWED_CONTENT_TYPES)},
        )


def _generate_safe_filename(original_filename: str) -> str:
    ext = FsPath(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".webp"
    return f"{uuid.uuid4().hex}{ext}"


async def _save_upload_file(file: UploadFile, destination: FsPath) -> None:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise UnprocessableError(
            f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)} MB.",
            code="image_too_large",
            details={"field": "image", "max_size_mb": MAX_FILE_SIZE // (1024 * 1024)},
        )
    destination.write_bytes(content)


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


# ---------------- Product Image Endpoints ----------------


@router.post(
    "/{product_id}/image",
    response_model=ProductResponse,
    summary="Upload or replace product image (admin)",
    description="Upload a product image. Replaces existing image if present.",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "Product not found"},
        422: {"model": ErrorResponse, "description": "Invalid image file"},
    },
)
async def upload_product_image(
    product_id: str = PRODUCT_ID,
    file: UploadFile = File(...),
    _admin = Depends(require_admin),
) -> ProductResponse:
    _ensure_upload_dir()

    # Verify product exists
    product = product_repo.get_product(product_id)
    if product is None:
        raise NotFoundError(
            f"Product '{product_id}' was not found.",
            code="product_not_found",
            details={"product_id": product_id},
        )

    _validate_image_file(file)

    # Generate safe filename
    filename = _generate_safe_filename(file.filename)
    destination = UPLOAD_DIR / filename

    # Save new image
    await _save_upload_file(file, destination)

    # Remove old image if exists
    old_image_url = product.get("image_url")
    if old_image_url:
        old_path = _stored_image_path(old_image_url)
        if old_path and old_path.exists() and old_path != destination:
            try:
                old_path.unlink()
            except OSError:
                pass  # Best effort cleanup

    # Update product with new image URL
    new_image_url = f"/uploads/products/{filename}"
    updated = product_repo.update_product(product_id, {"image_url": new_image_url})
    if updated is None:
        # Rollback: delete the uploaded file
        try:
            destination.unlink()
        except OSError:
            pass
        raise NotFoundError(
            f"Product '{product_id}' was not found.",
            code="product_not_found",
            details={"product_id": product_id},
        )

    return product_service._to_response(updated)


@router.delete(
    "/{product_id}/image",
    response_model=ProductResponse,
    summary="Remove product image (admin)",
    description="Remove the product's image. The image file is deleted from storage.",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
)
def remove_product_image(product_id: str = PRODUCT_ID, _admin = Depends(require_admin)) -> ProductResponse:
    product = product_repo.get_product(product_id)
    if product is None:
        raise NotFoundError(
            f"Product '{product_id}' was not found.",
            code="product_not_found",
            details={"product_id": product_id},
        )

    old_image_url = product.get("image_url")
    if old_image_url:
        old_path = _stored_image_path(old_image_url)
        if old_path and old_path.exists():
            try:
                old_path.unlink()
            except OSError:
                pass  # Best effort cleanup

    updated = product_repo.update_product(product_id, {"image_url": None})
    if updated is None:
        raise NotFoundError(
            f"Product '{product_id}' was not found.",
            code="product_not_found",
            details={"product_id": product_id},
        )

    return product_service._to_response(updated)
