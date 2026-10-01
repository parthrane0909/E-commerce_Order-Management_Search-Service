"""Customer endpoints — data source: **PostgreSQL** (`users` table)."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.orders import UserResponse
from app.services import order_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List seeded customers",
    description="Used by the storefront 'Log In As' selector.",
)
def list_users() -> list[UserResponse]:
    return order_service.list_users()
