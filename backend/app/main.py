"""FastAPI application entry point.

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import auth, health, orders, products, search, users
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger

logger = get_logger("app.main")
settings = get_settings()

OPENAPI_TAGS = [
    {"name": "Products", "description": "MongoDB product catalog (storefront + catalog admin)."},
    {"name": "Orders", "description": "PostgreSQL orders — the source of truth."},
    {"name": "Users", "description": "Seeded PostgreSQL customers ('Log In As')."},
    {"name": "Search", "description": "Elasticsearch order search, filters and aggregations."},
    {"name": "Authentication", "description": "Login, logout, current user."},
    {"name": "System", "description": "Health and readiness."},
]


def init_infrastructure() -> None:
    """Create schema/indexes at startup. Each step is best-effort except PG."""
    from app.core.database import create_tables
    from app.repositories.elasticsearch.orders_repo import ensure_index
    from app.services.product_service import ensure_catalog_indexes

    create_tables()

    try:
        ensure_catalog_indexes()
        logger.info("mongodb catalog indexes ensured")
    except Exception as exc:
        logger.warning("could not ensure MongoDB indexes: %s", exc)

    try:
        ensure_index()
    except Exception as exc:
        logger.warning("could not ensure Elasticsearch index: %s", exc)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.log_level)
    logger.info(
        "starting %s v%s environment=%s",
        settings.app_name,
        __version__,
        settings.environment,
    )
    init_infrastructure()
    logger.info("startup complete — openapi at /docs")
    yield
    logger.info("shutting down")

    from app.clients.elasticsearch import close_elasticsearch_client
    from app.clients.mongodb import close_mongo_client
    from app.core.database import engine

    close_mongo_client()
    close_elasticsearch_client()
    engine.dispose()
    logger.info("shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Polyglot persistence demo: **MongoDB** (product catalog), "
        "**PostgreSQL** (order source of truth), **RabbitMQ + Celery** "
        "(asynchronous synchronisation) and **Elasticsearch** "
        "(search, filtering and aggregations).\n\n"
        "Synchronisation path: `PostgreSQL → RabbitMQ → Celery → Elasticsearch`."
    ),
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    contact={"name": "E-Commerce Order Management & Search Service"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(auth.router)
app.include_router(health.router)


@app.get("/", tags=["System"], summary="API information")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/api/health",
    }
