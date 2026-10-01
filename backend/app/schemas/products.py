"""Product (MongoDB) request/response schemas."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = ("peripherals", "audio", "cables", "office")

ProductSort = Literal["newest", "title_asc", "price_asc", "price_desc"]


class VariantBase(BaseModel):
    sku: str = Field(min_length=1, max_length=64, examples=["WM-001-BLK"])
    color: str | None = Field(default=None, max_length=64, examples=["black"])
    stock: int = Field(default=0, ge=0, le=100_000)


class VariantCreate(VariantBase):
    pass


class VariantResponse(VariantBase):
    pass


class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9\-_]*$", examples=["WM-001"])
    title: str = Field(min_length=2, max_length=200, examples=["Wireless Mouse"])
    description: str = Field(default="", max_length=4000, examples=["Ergonomic 2.4GHz mouse"])
    price: float = Field(gt=0, le=1_000_000, examples=[50.16])
    category: str = Field(min_length=2, max_length=64, examples=["peripherals"])
    tags: list[str] = Field(default_factory=list, max_length=30)
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form nested attribute map, e.g. {color: black, dpi: 1600}",
        examples=[{"color": "black", "dpi": 1600, "battery": "AA"}],
    )
    variants: list[VariantCreate] = Field(
        default_factory=list,
        max_length=20,
        description="Nested variant array, each with its own sku/color/stock",
    )
    active: bool = True

    @field_validator("category")
    @classmethod
    def _normalise_category(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("tags")
    @classmethod
    def _normalise_tags(cls, value: list[str]) -> list[str]:
        seen: dict[str, None] = {}
        for tag in value:
            cleaned = tag.strip().lower()
            if cleaned:
                seen.setdefault(cleaned)
        return list(seen)

    @field_validator("price")
    @classmethod
    def _round_price(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("price must be greater than zero")
        return round(value, 2)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    """Partial update — every field is optional."""

    sku: str | None = Field(default=None, min_length=2, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9\-_]*$")
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    price: float | None = Field(default=None, gt=0, le=1_000_000)
    category: str | None = Field(default=None, min_length=2, max_length=64)
    tags: list[str] | None = Field(default=None, max_length=30)
    attributes: dict[str, Any] | None = None
    variants: list[VariantCreate] | None = Field(default=None, max_length=20)
    active: bool | None = None

    @field_validator("category")
    @classmethod
    def _normalise_category(cls, value: str | None) -> str | None:
        return value.strip().lower() if value else value

    @field_validator("tags")
    @classmethod
    def _normalise_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        seen: dict[str, None] = {}
        for tag in value:
            cleaned = tag.strip().lower()
            if cleaned:
                seen.setdefault(cleaned)
        return list(seen)

    @field_validator("price")
    @classmethod
    def _round_price(cls, value: float | None) -> float | None:
        return round(value, 2) if value is not None else value


class ProductResponse(BaseModel):
    #: MongoDB `_id` in, plain `id` in the JSON response.
    id: str = Field(
        validation_alias="_id",
        serialization_alias="id",
        description="MongoDB ObjectId",
    )
    sku: str
    title: str
    description: str
    price: float
    category: str
    tags: list[str]
    attributes: dict[str, Any]
    variants: list[VariantResponse]
    active: bool
    updated_at: dt.datetime | None = None
    created_at: dt.datetime | None = None

    model_config = {"populate_by_name": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    page: int
    limit: int
    total: int
    pages: int


class FacetBucket(BaseModel):
    value: str
    count: int


class ProductFacetsResponse(BaseModel):
    categories: list[FacetBucket]
    tags: list[FacetBucket]
