"""Centralised application configuration.

All runtime configuration is read from environment variables (optionally
loaded from a `.env` file) through `pydantic-settings`.  No secrets are
hardcoded anywhere in the code base — see `.env.example`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#: `backend/app/core/config.py` -> repository root (holds the `.env` file).
REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"

MONEY_PRECISION = "0.01"


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------ app
    app_name: str = "E-Commerce Order Management & Search Service"
    environment: str = "development"
    log_level: str = "INFO"

    # ------------------------------------------------------------------ api
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    # ------------------------------------------------------------- postgres
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "ecommerce"
    postgres_password: str = "ecommerce"
    postgres_db: str = "ecommerce"
    postgres_sslmode: str = "disable"
    postgres_pool_size: int = 5

    # --------------------------------------------------------------- mongo
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "catalog"
    mongo_timeout_ms: int = 5000

    # -------------------------------------------------------- elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "orders"
    elasticsearch_api_key: str | None = None
    elasticsearch_timeout: int = 10
    elasticsearch_refresh_on_write: bool = True

    # ------------------------------------------------------------- rabbitmq
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_default_user: str = "ecommerce"
    rabbitmq_default_password: str = "ecommerce"
    rabbitmq_url: str | None = None

    # --------------------------------------------------------------- celery
    celery_task_default_queue: str = "orders_sync"
    celery_max_retries: int = 5
    celery_retry_backoff: int = 10
    celery_retry_backoff_max: int = 120
    celery_task_always_eager: bool = False

    # -------------------------------------------------------------- seeding
    seed_random_seed: int = 20240917

    # --------------------------------------------------------------- auth
    jwt_secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    # ---------------------------------------------------------- validations
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _strip_origins(cls, value: object) -> object:
        return value if not isinstance(value, str) else value.strip()

    @field_validator(
        "elasticsearch_refresh_on_write", "celery_task_always_eager", mode="before"
    )
    @classmethod
    def _coerce_bool(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return value

    # ------------------------------------------------------------- derived
    @property
    def postgres_dsn(self) -> str:
        """SQLAlchemy/psycopg connection string for PostgreSQL."""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            f"?sslmode={self.postgres_sslmode}"
        )

    @property
    def postgres_async_dsn(self) -> str:
        return self.postgres_dsn

    @property
    def broker_url(self) -> str:
        """RabbitMQ URL used both by Celery and by health checks."""
        if self.rabbitmq_url:
            return self.rabbitmq_url
        return (
            f"amqp://{self.rabbitmq_default_user}:{self.rabbitmq_default_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}//"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sync_task_name(self) -> str:
        return "app.tasks.elasticsearch_tasks.sync_order_to_elasticsearch"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings singleton."""
    return Settings()
