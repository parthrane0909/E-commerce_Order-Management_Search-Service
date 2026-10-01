"""Health / readiness endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter, Response, status

from app.clients.elasticsearch import ping_elasticsearch
from app.clients.mongodb import ping_mongo
from app.clients.rabbitmq import ping_rabbitmq
from app.core.config import get_settings
from app.core.database import ping_postgres
from app.schemas.common import HealthDependency, HealthResponse

router = APIRouter(prefix="/api", tags=["System"])
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health",
    description=(
        "Pings PostgreSQL, MongoDB, Elasticsearch and RabbitMQ. "
        "Returns 200 when everything is reachable, 503 otherwise "
        "(used by the Docker health check)."
    ),
    responses={503: {"description": "One or more dependencies are unreachable"}},
)
def health(response: Response) -> HealthResponse:
    checks = {
        "postgresql": ping_postgres,
        "mongodb": ping_mongo,
        "elasticsearch": ping_elasticsearch,
        "rabbitmq": ping_rabbitmq,
    }

    dependencies: dict[str, HealthDependency] = {}
    all_up = True
    for name, probe in checks.items():
        started = time.perf_counter()
        up = probe()
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        dependencies[name] = HealthDependency(
            status="up" if up else "down", latency_ms=elapsed_ms
        )
        all_up = all_up and up

    if not all_up:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if all_up else "degraded",
        environment=settings.environment,
        dependencies=dependencies,
    )
