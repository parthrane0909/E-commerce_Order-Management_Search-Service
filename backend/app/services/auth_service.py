"""Authentication business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.auth import verify_password, create_access_token
from app.core.errors import NotFoundError, UnprocessableError
from app.models.postgres import User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticate a user by email and password. Returns User on success."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise NotFoundError("Invalid email or password", code="invalid_credentials")
    if not user.password_hash:
        raise UnprocessableError("User has no password set", code="no_password")
    if not verify_password(password, user.password_hash):
        raise NotFoundError("Invalid email or password", code="invalid_credentials")
    return user


def create_token_for_user(user: User) -> LoginResponse:
    """Create a JWT access token for a user and return the login response."""
    access_token = create_access_token(data={"sub": str(user.id)})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user, from_attributes=True),
    )


def get_user_by_id(db: Session, user_id: int) -> UserResponse:
    """Get user info by ID for /me endpoint."""
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found", code="user_not_found")
    return UserResponse.model_validate(user, from_attributes=True)