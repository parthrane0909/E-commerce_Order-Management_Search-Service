"""Authentication endpoints: login, logout, current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_db
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, UserResponse
from app.services.auth_service import authenticate_user, create_token_for_user, get_user_by_id

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate with email and password, receive JWT access token.",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate user and return access token."""
    user = authenticate_user(db, payload.email, payload.password)
    return create_token_for_user(user)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User logout",
    description="Client-side logout — token invalidation happens on the client by discarding the token.",
)
def logout() -> LogoutResponse:
    """Logout endpoint (stateless JWT — client discards token)."""
    return LogoutResponse()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the currently authenticated user's information.",
)
def me(current_user = Depends(get_current_user)) -> UserResponse:
    """Get current authenticated user info."""
    return UserResponse.model_validate(current_user, from_attributes=True)