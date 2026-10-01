"""PostgreSQL engine, session factory and FastAPI dependency."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

engine: Engine = create_engine(
    settings.postgres_dsn,
    pool_pre_ping=True,
    pool_size=settings.postgres_pool_size,
    max_overflow=settings.postgres_pool_size,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db_session() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def ping_postgres() -> bool:
    """Cheap connectivity probe used by the health endpoint."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # pragma: no cover - depends on infra state
        logger.warning("postgres ping failed: %s", exc)
        return False


def create_tables() -> None:
    """Create every table described by the SQLAlchemy metadata (idempotent)."""
    from app.models.postgres import Base

    Base.metadata.create_all(engine)
    logger.info("postgresql schema ensured")


def drop_tables() -> None:
    """Drop every table (used by the seed script for reproducibility)."""
    from app.models.postgres import Base

    Base.metadata.drop_all(engine)
    logger.info("postgresql schema dropped")
