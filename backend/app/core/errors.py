"""Application errors and the global exception handlers.

Every error response uses the same envelope:

    {"error": {"code": "...", "message": "...", "details": {...}}}
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")


class AppError(Exception):
    """Base class for every error the API intentionally raises."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "app_error",
        status_code: int = 400,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        return payload


class BadRequestError(AppError):
    def __init__(self, message: str, *, code: str = "bad_request", details=None) -> None:
        super().__init__(message, code=code, status_code=400, details=details)


class NotFoundError(AppError):
    def __init__(self, message: str, *, code: str = "not_found", details=None) -> None:
        super().__init__(message, code=code, status_code=404, details=details)


class ConflictError(AppError):
    def __init__(self, message: str, *, code: str = "conflict", details=None) -> None:
        super().__init__(message, code=code, status_code=409, details=details)


class UnprocessableError(AppError):
    """Semantic validation failure (e.g. inactive product, bad price)."""

    def __init__(self, message: str, *, code: str = "unprocessable", details=None) -> None:
        super().__init__(message, code=code, status_code=422, details=details)


class DependencyUnavailableError(AppError):
    """PostgreSQL / MongoDB / Elasticsearch / RabbitMQ is not reachable."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "dependency_unavailable",
        details=None,
    ) -> None:
        super().__init__(message, code=code, status_code=503, details=details)


def _error_response(status_code: int, payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=jsonable_encoder({"error": payload}))


def register_exception_handlers(app: FastAPI) -> None:
    """Attach consistent error handlers to the FastAPI application."""

    @app.exception_handler(AppError)
    async def _app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("application error [%s]: %s", exc.code, exc.message)
        else:
            logger.info("request rejected [%s]: %s", exc.code, exc.message)
        return _error_response(exc.status_code, exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields = [
            {
                "field": ".".join(str(part) for part in error.get("loc", ())) or "<root>",
                "message": error.get("msg", "invalid value"),
                "type": error.get("type", "value_error"),
            }
            for error in exc.errors()
        ]
        logger.info("request body validation failed: %s", fields)
        return _error_response(
            422,
            {
                "code": "validation_error",
                "message": "Request validation failed.",
                "details": {"fields": fields},
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error: %s", exc)
        return _error_response(
            500,
            {
                "code": "internal_error",
                "message": "An unexpected server error occurred. Check the API logs.",
            },
        )
