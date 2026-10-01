"""Shared pytest fixtures for the backend test suite.

Layout
------
* `tests/unit/**`         pure logic, no infrastructure required
* `tests/integration/**`  needs the Docker infrastructure

If the infrastructure is not reachable the integration tests are skipped
with an actionable message instead of failing mysteriously.
"""

from __future__ import annotations

import uuid

import pytest

# --- configuration must be importable before any app module -------------
from app.core.config import get_settings  # noqa: E402,F401
from app.core.logging import configure_logging

configure_logging("WARNING")


def _get_token_for_user(email: str, password: str) -> str:
    """Get a JWT token for a user by calling the login endpoint."""
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        if response.status_code != 200:
            raise RuntimeError(f"Failed to login as {email}: {response.text}")
        return response.json()["access_token"]


def _get_authenticated_client(email: str, password: str):
    """Create a TestClient with Authorization header set for a user.
    
    This uses a context manager to ensure proper lifespan handling.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    # Create the authenticated client with a custom request method
    class AuthenticatedTestClient(TestClient):
        def __init__(self, *args, token: str = None, **kwargs):
            super().__init__(*args, **kwargs)
            self._auth_token = token
        
        def request(self, *args, **kwargs):
            if self._auth_token is None:
                # First request - login to get token
                # We need to use the parent's request method without our custom headers
                response = super().request("POST", "/api/auth/login", json={"email": email, "password": password})
                if response.status_code != 200:
                    raise RuntimeError(f"Failed to login as {email}: {response.text}")
                self._auth_token = response.json()["access_token"]
                # Now make the actual request
                return self.request(*args, **kwargs)
            
            headers = kwargs.get("headers") or {}
            headers["Authorization"] = f"Bearer {self._auth_token}"
            kwargs["headers"] = headers
            return super().request(*args, **kwargs)
    
    return AuthenticatedTestClient(app, raise_server_exceptions=False)


def _infra_status() -> dict[str, bool]:
    from app.clients.elasticsearch import ping_elasticsearch
    from app.clients.mongodb import ping_mongo
    from app.clients.rabbitmq import ping_rabbitmq
    from app.core.database import ping_postgres

    return {
        "postgresql": ping_postgres(),
        "mongodb": ping_mongo(),
        "elasticsearch": ping_elasticsearch(),
        "rabbitmq": ping_rabbitmq(),
    }


def pytest_collection_modifyitems(config, items):  # noqa: ANN001, ANN201
    """Skip integration tests (with a clear reason) when infra is down."""
    missing = [name for name, ok in _infra_status().items() if not ok]
    if not missing:
        return
    skip = pytest.mark.skip(
        reason=(
            f"infrastructure unavailable: {', '.join(missing)}. "
            "Start it with `docker compose up -d postgres mongodb elasticsearch rabbitmq`."
        )
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def api():
    """FastAPI TestClient with lifespan handling (creates schema/indexes)."""
    from fastapi.testclient import TestClient

    from app.main import app

    # raise_server_exceptions=False so our own 500 envelope is asserted
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture(scope="session")
def settings():  # noqa: ANN201
    return get_settings()


@pytest.fixture
def es_purge_orphans():  # noqa: ANN201
    """Delete Elasticsearch documents whose order no longer exists in PG.

    The Celery worker is asynchronous: a task read may start before a test
    fixture deletes its order row and finish afterwards, leaving a stale
    document behind.  Tests that assert PG/ES parity call this first.
    """

    def _purge() -> int:
        from app.clients.elasticsearch import get_elasticsearch_client
        from app.core.database import SessionLocal
        from app.models.postgres import Order
        from app.repositories.elasticsearch.orders_repo import index_name

        session = SessionLocal()
        try:
            postgres_ids = {str(row[0]) for row in session.query(Order.id).all()}
        finally:
            session.close()

        client = get_elasticsearch_client()
        response = client.search(
            index=index_name(),
            query={"match_all": {}},
            size=1000,
            _source=False,
        )
        removed = 0
        for hit in response["hits"]["hits"]:
            if hit["_id"] not in postgres_ids:
                client.delete(index=index_name(), id=hit["_id"], refresh=True)
                removed += 1
        return removed

    return _purge


@pytest.fixture
def es_document():  # noqa: ANN001, ANN201
    """Fetch an order document straight from Elasticsearch (None if absent)."""
    from app.clients.elasticsearch import get_elasticsearch_client
    from app.repositories.elasticsearch.orders_repo import index_name

    def _get(order_id: int) -> dict | None:
        try:
            response = get_elasticsearch_client().get(index=index_name(), id=str(order_id))
            return dict(response["_source"])
        except Exception:
            return None

    return _get


@pytest.fixture
def es_delete():  # noqa: ANN001, ANN201
    """Remove an order document from Elasticsearch."""
    from app.clients.elasticsearch import get_elasticsearch_client
    from app.repositories.elasticsearch.orders_repo import index_name

    def _delete(order_id: int) -> None:
        try:
            get_elasticsearch_client().delete(index=index_name(), id=str(order_id))
        except Exception:
            pass

    return _delete


@pytest.fixture
def product_factory():
    """Create throwaway catalog products; removed from MongoDB afterwards."""
    from app.repositories.mongo import product_repo

    created: list[str] = []

    def _create(**overrides):  # noqa: ANN001, ANN201
        sku = overrides.pop("sku", f"TEST-{uuid.uuid4().hex[:10].upper()}")
        payload = {
            "sku": sku,
            "title": f"Test Product {sku}",
            "description": "Temporary product created by the test suite.",
            "price": 19.99,
            "category": "peripherals",
            "tags": ["test"],
            "attributes": {"colour": "black"},
            "variants": [{"sku": f"{sku}-A", "color": "black", "stock": 3}],
            "active": True,
            **overrides,
        }
        document = product_repo.create_product(payload)
        created.append(str(document["_id"]))
        return document

    yield _create

    if created:
        from bson import ObjectId

        from app.clients.mongodb import get_mongo_db

        collection = get_mongo_db()["products"]
        for product_id in created:
            collection.delete_one({"_id": ObjectId(product_id)})


@pytest.fixture
def order_factory(authenticated_api, es_delete):  # noqa: ANN001
    """Place real orders through the API as an authenticated customer and delete them afterwards."""
    from app.core.database import SessionLocal
    from app.models.postgres import Order

    created: list[int] = []

    def _create(items: list[dict] | None = None):  # noqa: ANN001
        if items is None:
            from app.repositories.mongo import product_repo

            product, _ = product_repo.list_products(visibility="active", limit=1)
            items = [{"product_id": str(product[0]["_id"]), "quantity": 1}]
        response = authenticated_api.post("/api/orders", json={"items": items})
        assert response.status_code == 201, response.text
        payload = response.json()
        created.append(payload["id"])
        return payload

    yield _create

    if created:
        from app.core.database import SessionLocal
        from app.models.postgres import Order

        session = SessionLocal()
        try:
            session.begin()
            session.query(Order).filter(Order.id.in_(created)).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()

    # keep Elasticsearch consistent with the cleaned up PostgreSQL rows
    for order_id in created:
        es_delete(order_id)


@pytest.fixture(scope="session")
def authenticated_api():
    """FastAPI TestClient authenticated as a demo customer (John Doe)."""
    return _get_authenticated_client("john.doe@example.com", "john")


@pytest.fixture(scope="session")
def admin_api():
    """FastAPI TestClient authenticated as admin."""
    return _get_authenticated_client("admin@example.com", "admin")


@pytest.fixture
def order_factory_authenticated(authenticated_api, es_delete):
    """Place real orders through the API as an authenticated customer and delete them afterwards."""
    from app.core.database import SessionLocal
    from app.models.postgres import Order

    created: list[int] = []

    def _create(items: list[dict] | None = None):  # noqa: ANN001
        if items is None:
            from app.repositories.mongo import product_repo

            product, _ = product_repo.list_products(visibility="active", limit=1)
            items = [{"product_id": str(product[0]["_id"]), "quantity": 1}]
        response = authenticated_api.post("/api/orders", json={"items": items})
        assert response.status_code == 201, response.text
        payload = response.json()
        created.append(payload["id"])
        return payload

    yield _create

    if created:
        from app.core.database import SessionLocal
        from app.models.postgres import Order

        session = SessionLocal()
        try:
            session.begin()
            session.query(Order).filter(Order.id.in_(created)).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()

    # keep Elasticsearch consistent with the cleaned up PostgreSQL rows
    for order_id in created:
        es_delete(order_id)
