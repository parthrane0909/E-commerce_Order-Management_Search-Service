"""Authentication request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=1, max_length=128, description="Plaintext password")


class LoginResponse(BaseModel):
    """Login success response with access token."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    user: "UserResponse" = Field(description="Authenticated user info")


class UserResponse(BaseModel):
    """User info returned after login or from /me endpoint."""

    id: int
    name: str
    email: str
    role: str


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str = "Logged out successfully"


# Forward reference resolution
LoginResponse.model_rebuild()