# E-Commerce Order Management & Search Service

A full-stack **polyglot persistence** demonstration: a Vue 3 storefront + admin console backed by
FastAPI, with each database used strictly for the job it is best at.

> **TL;DR**
>
> ```bash
> cp .env.example .env
> docker compose up -d --build
> docker compose run --rm seed        # seed PostgreSQL + MongoDB + Elasticsearch
> ```
>
> - API + Swagger UI: <http://localhost:8000/docs>
> - Frontend: <http://localhost:5173>
> - RabbitMQ management UI: <http://localhost:15672> (`ecommerce` / `change_me_rabbit`)
> - Tests: `python -m pytest` (101 tests) and `cd frontend && npx vitest run` (28 tests)

---

## Table of contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Technology stack](#3-technology-stack)
4. [Database responsibilities](#4-database-responsibilities)
5. [API reference](#5-api-reference)
6. [Order creation & transactions](#6-order--transactions)
7. [Snapshotting](#7-snapshotting)
8. [Synchronisation strategy](#8-synchronisation-strategy)
9. [Elasticsearch: search & analytics](#9-elasticsearch-search--analytics)
10. [Docker Compose](#10-docker-compose)
11. [Environment variables](#11-environment-variables)
12. [Seed data](#12-seed-data)
13. [Running each service](#13-running-each-service)
14. [Frontend](#14-frontend)
15. [Testing](#15-testing)
16. [Demo flow](#16-demo-flow)
17. [Known limitations](#17-known-limitations)

---

## 1. Overview

Five screens, three databases, one messaging pipeline:

| Screen | Where it lives | Data source |
| --- | --- | --- |
| 1. Storefront | `/` | **MongoDB** product catalog |
| 2. Checkout | `/checkout` | **MongoDB** (pricing) → **PostgreSQL** (order) |
| 3. Admin search dashboard | `/admin/search` | **Elasticsearch only** (results + KPIs) |
| 4. Admin order details | `/admin/orders/:id` | **PostgreSQL** (canonical) + status PATCH → sync |
| 5. Catalog admin | `/admin/catalog` | **MongoDB** CRUD (soft delete) |

The design rule the whole project hangs on:

> **PostgreSQL is the source of truth for orders. Elasticsearch is a *search and analytics*
> projection of those orders. MongoDB holds the product catalog. Nothing else.**

Concretely:

- Screen 3 results **never** read PostgreSQL or MongoDB — a guard test asserts it.
- Screen 4 always reads PostgreSQL, even though a searchable copy exists in Elasticsearch.
- The client never supplies a total; the server always recomputes it from MongoDB prices.

---

## 2. Architecture

```
                        ┌───────────────────────────────────────────┐
                        │                Vue 3 + Vite               │
                        │  Storefront · Checkout · Admin (3 views)  │
                        └───────────────────┬───────────────────────┘
                                            │  REST / JSON  (Axios)
                                            ▼
                        ┌───────────────────────────────────────────┐
                        │                 FastAPI                   │
                        │   products · orders · users · search      │
                        └───┬───────────────┬───────────────┬───────┘
                            │               │               │
              read/write ───┘               │               └─── read/write
                            ▼               │               ▼
                  ┌──────────────────┐       │     ┌──────────────────────┐
                  │     MongoDB      │       │     │     PostgreSQL       │
                  │ product catalog  │       │     │  users / orders /    │
                  │  (Screen 1, 5)   │       │     │  order_items         │
                  └──────────────────┘       │     │ (source of truth)    │
                                             │     └──────────┬───────────┘
                                             │                │
                                             │      1. BEGIN / INSERT / COMMIT
                                             │      2. after COMMIT → publish
                                             │                ▼
                                             │     ┌──────────────────────┐
                                             │     │      RabbitMQ        │
                                             │     │  queue: orders_sync  │
                                             │     └──────────┬───────────┘
                                             │                │  consume
                                             │                ▼
                                             │     ┌──────────────────────┐
                                             │     │    Celery worker     │
                                             │     │ build doc from PG    │
                                             │     └──────────┬───────────┘
                                             │                │  index (upsert, _id = order_id)
                                             │                ▼
                                             │     ┌──────────────────────┐
                                             └────▶│    Elasticsearch     │
                                                   │  orders index        │
         Screen 3 ──── POST /api/search/orders ───▶│  (search + KPI aggs) │
                                                   └──────────────────────┘
```

**The only synchronisation path in this project:**

```
PostgreSQL  ──▶  RabbitMQ  ──▶  Celery  ──▶  Elasticsearch
 (commit)        (queue)       (worker)        (index)
```

There is deliberately **no** polling loop, **no** CDC/Debezium, **no** transactional outbox
presented as an alternative, and **no** Kafka/Redis/MySQL/OpenSearch anywhere in the stack.

---

## 3. Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | Vue 3, Vite, Vue Router, Pinia, Axios, Vitest + @vue/test-utils |
| API | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 (sync), Uvicorn |
| Orders DB | PostgreSQL 16 (`psycopg` driver) |
| Catalog DB | MongoDB 7 (`pymongo`) |
| Search | Elasticsearch 8.15.3 (`elasticsearch-py`, `dynamic: strict` mapping) |
| Messaging | RabbitMQ 3.13 (management image) + Celery 5 |
| Tests | pytest (unit + integration), Vitest (frontend) |
| Packaging | Docker Compose, multi-stage Dockerfiles, nginx for the production frontend build |

---

## 4. Database responsibilities

### PostgreSQL — source of truth for orders

| Table | Purpose |
| --- | --- |
| `users` | 8 seeded customers, unique e-mail |
| `orders` | `order_number` (`ORD-000123`, unique), FK → `users`, `status` CHECK (`PENDING`/`PROCESSING`/`SHIPPED`), `numeric(12,2)` total, `order_date`, `created_at`/`updated_at`, `search_indexed_at` |
| `order_items` | FK → `orders` (ON DELETE CASCADE), **snapshot** `title` + `unit_price`, `quantity`/`unit_price` CHECKs, `line_total` |

Indexes: `orders(status)`, `orders(order_date)`, `orders(user_id)`, `orders(order_number)`,
`order_items(order_id)`.

### MongoDB — product catalog

```jsonc
{
  "_id": ObjectId, "sku": "PER-1001", "title": "Wireless Mouse Pro",
  "description": "…", "price": 60.00, "category": "peripherals",
  "tags": ["wireless", "usb", "office"],
  "attributes": { "colour": "black", "connectivity": "2.4GHz" },
  "variants": [{ "sku": "PER-1001-BLK", "color": "black", "stock": 12 }],
  "active": true, "updated_at": ISODate
}
```

Indexes: unique `sku`, `category`, `active`. **DELETE is a soft delete** (`active=false`) so
historical orders keep a meaningful product reference.

### Elasticsearch — search + analytics only

One index, `orders`, holding a *document per order* rebuilt from PostgreSQL. See §9.

**Why three databases?** Each store is queried with a different access pattern: catalog lookups
are document-shaped and filter-heavy (Mongo), order writes need real transactions and referential
integrity (Postgres), and search needs inverted indexes plus bucket aggregations (Elasticsearch).
The exercise is precisely to keep those roles honest instead of forcing one store to do all three.

---

## 5. API reference

Base URL: `http://localhost:8000` — interactive docs at `/docs`.

### Products (MongoDB)

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/products` | `q`, `category`, `tags[]`, `min_price`, `max_price`, `visibility=active\|inactive\|all`, `sort`, `page`, `limit` |
| `GET` | `/api/products/facets` | category + tag facet counts for the filter sidebar |
| `GET` | `/api/products/{id}` | single product (`404` envelope if unknown) |
| `POST` | `/api/products` | create; `409` on duplicate SKU |
| `PATCH` | `/api/products/{id}` | partial update |
| `DELETE` | `/api/products/{id}` | **soft delete** → `active: false` |

Product JSON uses `id` (not `_id`).

### Orders (PostgreSQL)

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/orders` | `{ user_id, items: [{product_id, quantity}] }` → `201` |
| `GET` | `/api/orders/{id}` | canonical details, straight from PostgreSQL |
| `PATCH` | `/api/orders/{id}/status` | `{ status: PENDING\|PROCESSING\|SHIPPED }` → `200` |
| `GET` | `/api/users` | 8 seeded customers for the "Log In As" selector |

> There is intentionally **no** `total_amount` field on the create payload. Sending one is
> harmless — the server re-reads MongoDB and computes the total itself.

Both write responses include a `sync` block describing the messaging outcome:

```json
"sync": { "enqueued": true, "task_id": "…", "queue": "orders_sync", "error": null }
```

### Search (Elasticsearch)

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/search/orders` | body: `query`, `status[]`, `date_from`, `date_to`, `min_price`, `max_price`, `page`, `limit` |

Response: `{ results, total, page, limit, pages, took_ms, aggregations: { revenue, status_counts } }`.

### System

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/health` | liveness + per-dependency status |
| `GET` | `/` | service metadata |

### Error envelope

Every failure — validation, not-found, dependency down, crash — uses one shape:

```json
{ "error": { "code": "order_not_found", "message": "Order '999999' was not found.",
             "details": { "order_id": 999999 } } }
```

Codes: `validation_error` (422), `not_found`/`product_not_found`/`order_not_found`/
`user_not_found` (404), `conflict` (409), `inactive_product`/`invalid_price`/
`quantity_limit_exceeded` (422), `order_persistence_failed` (500),
`dependency_unavailable`/`search_unavailable` (503).

---

## 6. Order creation & transactions

`app/services/order_service.py` makes the transaction **explicit and visible**, not implicit in
the ORM:

```
1. resolve cart against MongoDB      (validate products, re-read live prices)
2. session.begin()                                        ← BEGIN
3. INSERT orders        + session.flush()                 ← order.id available
4. order_number = 'ORD-{id:06d}'      (second flush)
5. INSERT order_items × N + session.flush()               ← CHECK constraints run here
6. session.commit()                                       ← COMMIT (now durable)
   └─ on ANY exception: session.rollback()                ← ROLLBACK, zero rows written
       → HTTP 500 { code: "order_persistence_failed" }
7. only after COMMIT: publish sync task to RabbitMQ
```

Guarantees, each covered by an integration test:

- **Totals are server-side.** The price of every line is re-read from MongoDB at order time;
  `total = Σ(quantity × unit_price)` in exact `Decimal` arithmetic (ROUND_HALF_UP).
  A client-sent `total_amount: 0.01` is ignored.
- **Duplicate cart lines are merged** (≤ 100 units per product).
- **All-or-nothing.** A failure while inserting items rolls back *everything* — asserted by
  comparing `orders`/`order_items` row counts before and after.
- **Messaging never breaks a write.** If RabbitMQ is down, the order is still committed and the
  response reports `sync.enqueued: false` with the error string.
- The status PATCH runs its own BEGIN/UPDATE/COMMIT/ROLLBACK and only then publishes a sync.

---

## 7. Snapshotting

`order_items.title` and `order_items.unit_price` are **copies of the catalog at purchase time**.
Later catalog edits — even a rename and a price change — never rewrite history.

The seed ships a deliberate demonstration:

| | Before (as ordered) | After (live catalog) |
| --- | --- | --- |
| Product title | `Wireless Mouse` | `Wireless Mouse Pro` |
| Price | `$50.16` | `$60.00` |

- **MongoDB** shows `Wireless Mouse Pro — $60.00` on the storefront.
- **PostgreSQL** orders placed earlier still show `Wireless Mouse — $50.16`, and their
  `total_amount` still equals the sum of those snapshot lines.
- **Elasticsearch** documents also carry the historical title/price, because the worker rebuilds
  them from PostgreSQL snapshots — never from live MongoDB data.

Open Screen 4 on one of those orders (or search `Wireless Mouse` on Screen 3) to see it.

---

## 8. Synchronisation strategy

**PostgreSQL → RabbitMQ → Celery → Elasticsearch.** That is the whole story.

| Concern | How it is handled |
| --- | --- |
| Publish point | Immediately **after** `COMMIT`, never inside the transaction |
| Queue | `orders_sync` (Celery `send_task`, JSON serialization) |
| Task | `app.tasks.elasticsearch_tasks.sync_order_to_elasticsearch(order_id, reason)` |
| Idempotency | Document `_id = order_id` → an at-least-once redelivery **upserts**, never duplicates |
| Payload | The task reads PostgreSQL itself and rebuilds the whole document — no order data in the message |
| Retries | 5 attempts, exponential backoff 10 s → 20 → 40 → 80 → capped at 120 s |
| Worker resilience | `acks_late`, `reject_on_worker_lost`, `prefetch=1` → an unacked task is re-queued if a worker dies |
| Bookkeeping | Worker sets `orders.search_indexed_at` (shown as the sync indicator on Screen 4) |
| Reasons | `order_created` / `status_update` — both map to the same rebuild |

**What is deliberately not used:** polling, CDC/Debezium, transactional outbox, Kafka, or any
second broker. See [§17](#17-known-limitations) for the honest trade-offs of this choice.

---

## 9. Elasticsearch: search & analytics

### Mapping (`dynamic: strict`)

| Field | Type | Why |
| --- | --- | --- |
| `order_number`, `status` | `keyword` | exact match / terms facets |
| `customer.name`, `customer.email`, `order_number` | `text` + `.keyword` | full-text search **and** sorting/aggregation |
| `items` | **`nested`** | item fields must not bleed across orders |
| `items.title` | `text` + `.keyword` | search inside line items |
| `order_date`, `updated_at` | `date` | range filters on Screen 3 |
| `total_amount`, `items.unit_price`, `items.line_total` | `double` | revenue KPI + price bands |
| `customer.id` | `long` | join-free identity |

### Query

A single `bool` query per request:

- **Free text** → `multi_match` over `customer.name^3`, `customer.email`, `order_number`,
  plus a `nested` `multi_match` over `items.title^2`; `minimum_should_match: 1`.
- **Filters** → `terms` on `status`, `range` on `order_date` (inclusive whole-day bounds),
  `range` on `total_amount`. All filters combine with `AND`.
- **Sort** → `order_date desc, order_id desc` (stable pagination), `track_total_hits: true`.

### Aggregations (the KPI cards)

```jsonc
"aggs": {
  "revenue":       { "sum":  { "field": "total_amount" } },
  "status_counts": { "terms": { "field": "status", "size": 3 } }
}
```

Because the aggregations run **inside** the same query, the KPI values always describe the
*current* filter set — filter to `SHIPPED` and both the revenue card and the status cards narrow
with it.

### Reindexing

```bash
docker compose run --rm reindex                 # python -m scripts.reindex_orders --recreate
# or locally:
cd backend && python -m scripts.reindex_orders          # incremental
cd backend && python -m scripts.reindex_orders --recreate
```

The script rebuilds every document from PostgreSQL, prints
`postgres_orders / documents_built / indexed / failed / elasticsearch_documents`, and **exits
non-zero** if the counts differ — so it is safe to run in CI.

### The architecture guard

`tests/integration/test_search_api.py::test_search_service_never_touches_postgres_or_mongodb`
scans `search_service.py`, `api/search.py` and `search_repo.py` for SQL/Mongo imports, and
`test_search_endpoint_works_while_mongo_session_is_poisoned` monkeypatches `SessionLocal` to
raise and confirms search still works.

---

## 10. Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
docker compose run --rm seed       # profile "tools"
docker compose run --rm reindex
docker compose ps
docker compose logs -f celery-worker
docker compose down                 # -v to also drop volumes
```

| Service | Image | Port(s) | Notes |
| --- | --- | --- | --- |
| `postgres` | `postgres:16-alpine` | `5436:5432`¹ | volume `postgres_data`, `pg_isready` healthcheck |
| `mongodb` | `mongo:7` | `27017` | volume `mongodb_data`, `mongosh ping` healthcheck |
| `elasticsearch` | `elasticsearch:8.15.3` | `9200` | security off, 512 MB heap, volume `elasticsearch_data` |
| `rabbitmq` | `rabbitmq:3.13-management-alpine` | `5672`, `15672` | volume `rabbitmq_data` |
| `backend` | built from `backend/` | `8000` | uvicorn `--reload`, bind-mounted source, healthcheck on `/api/health` |
| `celery-worker` | built from `backend/` | — | `celery -A app.tasks.celery_app worker --concurrency=2` |
| `frontend` | `frontend/` target `dev` | `5173` | Vite dev server with HMR; proxies `/api` to `http://backend:8000` |
| `frontend-prod` | `frontend/` target `prod` | `8080` | nginx serving the built bundle + `/api` proxy. **Opt-in**: `--profile prod` |
| `seed` / `reindex` | built from `backend/` | — | one-shot, `profiles: ["tools"]` |

```bash
# production-style frontend (nginx, no HMR, hashed assets):
docker compose --profile prod up -d --build frontend-prod   # → http://localhost:8080
```

¹ The published host port defaults to `5432` in `docker-compose.yml`; this machine's `.env`
sets `POSTGRES_PORT=5436` because a local PostgreSQL 16 already occupies 5432. Inside the
compose network the container port is always `5432` — the `environment:` block overrides
`POSTGRES_HOST`/`POSTGRES_PORT`/`MONGO_URI`/`ELASTICSEARCH_URL`/`RABBITMQ_URL` so containers
never see the `localhost` values from `.env`.

Startup order is enforced with `depends_on: condition: service_healthy`, so the backend waits
for all four data services.

---

## 11. Environment variables

`.env.example` documents every variable (copy it to `.env`). Highlights:

| Variable | Default / example | Purpose |
| --- | --- | --- |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `localhost` / `5432` | overridden in-network to `postgres` / `5432` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `ecommerce` / `change_me_postgres` / `ecommerce` | credentials |
| `MONGO_URI` | `mongodb://localhost:27017` | overridden to `mongodb://mongodb:27017` |
| `MONGO_DB` | `catalog` | database name |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | overridden to `http://elasticsearch:9200` |
| `ELASTICSEARCH_INDEX` | `orders` | search index |
| `ELASTICSEARCH_REFRESH_ON_WRITE` | `true` | immediate visibility for the demo/tests |
| `RABBITMQ_URL` | `amqp://…@localhost:5672//` | overridden to the in-network host |
| `CELERY_TASK_DEFAULT_QUEUE` | `orders_sync` | the single sync queue |
| `CELERY_MAX_RETRIES` / `CELERY_RETRY_BACKOFF` / `_MAX` | `5` / `10` / `120` | retry policy |
| `CELERY_TASK_ALWAYS_EAGER` | `false` | test-only: run tasks in-process |
| `CORS_ORIGINS` | `http://localhost:5173` | browser access |
| `VITE_API_BASE_URL` | `http://localhost:8000` | frontend → API base URL |
| `LOG_LEVEL` | `INFO` | logging |

Settings are loaded by pydantic-settings from a `.env` **resolved relative to the repository
root**, so commands work from any working directory. `.env.example` deliberately keeps
`localhost` values so it is also valid for running the backend outside Docker.

---

## 12. Seed data

```bash
docker compose run --rm seed          # or: cd backend && python -m scripts.seed
```

Deterministic, idempotent (drops and rebuilds), and **self-verifying** — every requirement below
is an assertion that fails the script if unmet:

| Requirement | Result |
| --- | --- |
| Users | **8**, including `Wendy Wireless` |
| Active products | **26** (≥ 24) across `peripherals`/`audio`/`cables`/`office`, **≥ 5 each** |
| Inactive product | **1** (hidden from the storefront, 422 if ordered) |
| "wireless" products | **≥ 6** |
| Price bands | ≥ 4 cheap / ≥ 4 mid / ≥ 4 premium |
| Orders / items | **44 / 86** (≥ 40 / ≥ 80) |
| Status distribution | `PENDING 15 · PROCESSING 15 · SHIPPED 14` (**≥ 10 each**) |
| Date spread | > 60 days old, ≤ 7 days old, and everything between (90-day window) |
| Total buckets | ≥ 5 under $30, ≥ 5 in $30–150, ≥ 5 over $200 |
| Per-user orders | every user ≥ 2; **Wendy ≥ 3**, at least one containing a wireless product |
| Search fixtures | ≥ 8 orders with `Wireless Mouse`, ≥ 3 with `Mechanical Keyboard`, ≥ 2 with **both** |
| Totals | `total_amount == Σ(quantity × unit_price)` for **every** order (asserted) |
| Snapshot demo | MongoDB `Wireless Mouse` ($50.16) → `Wireless Mouse Pro` ($60.00) **after** orders exist |
| PG ↔ ES parity | reindex runs inside the seed; counts must match |

---

## 13. Running each service

### Everything (recommended)

```bash
cp .env.example .env && docker compose up -d --build && docker compose run --rm seed
```

### Backend only (outside Docker)

```bash
# infrastructure must already be running
cd backend
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python -m scripts.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Celery worker only

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=INFO --concurrency=2
```

Confirm it connected to `orders_sync` in the startup banner, then place an order and watch the
worker log index the document.

### Frontend only

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (needs the API on :8000)
```

### Full production-style build

```bash
# static bundle behind nginx (SPA fallback + /api proxy), no HMR:
docker compose --profile prod up -d --build frontend-prod   # http://localhost:8080
```

---

## 14. Frontend

Vue 3 + Vite, Router, Pinia stores (`cart`, `user`, `toast`), Axios API layer in `src/api/`.
`VITE_API_BASE_URL` points the client at the API (default `http://localhost:8000`).

```
src/
├── api/            client.js + products / orders / search / users modules
├── layouts/        StorefrontLayout, AdminLayout (sidebar, collapsible on mobile)
├── views/          StorefrontView · CheckoutView · AdminSearchView ·
│                   OrderDetailsView · CatalogAdminView
├── components/
│   ├── common/     AppCard, AppModal, AppDrawer, AppPagination, AppBadge, StatusBadge,
│   │               BaseButton/Input/Select/Textarea, FormField, ConfirmDialog,
│   │               EmptyState, LoadingSkeleton, ToastHost, KpiCard, UserSelect…
│   ├── storefront/ ProductGrid, ProductCard, ProductFilters, CartDrawer
│   ├── checkout/   CheckoutLineItems, OrderSummaryCard, OrderSuccessPanel
│   └── admin/      SearchKpis, SearchFilters, ResultsTable/ResultsCardList,
│                   OrderStatusControl, SearchSyncIndicator, CatalogTable,
│                   ProductFormModal, AttributesEditor, VariantsEditor, TagsInput
├── stores/         cart, user, toast
├── styles/         tokens.css (design tokens), utilities.css
└── utils/          currency, dates, status, debounce, validation
```

Behaviour worth noting:

- **All five screens make real API calls** — no mock data, no `alert()`.
- Consistent **loading / error / empty / confirmation** states everywhere
  (`LoadingSkeleton`, `AppAlert`, `EmptyState`, `ConfirmDialog`), plus toasts for feedback.
- **Cart drawer** with reactive add/remove/quantity and live totals.
- **Checkout** renders an invoice-style summary; the button shows totals read from the same
  server-validated calculation path, and the response confirms the server's total.
- **Admin search** has KPI cards, filter chips, table (desktop) / card (mobile) layouts, and
  pagination; **order details** shows the `search_indexed_at` sync indicator and a status
  dropdown; **catalog admin** edits `attributes` and `variants` through dedicated editors and
  requires confirmation before a soft delete.
- Responsive across desktop / laptop / tablet / mobile; restrained, original design.

```bash
cd frontend
npm run build      # production bundle → dist/
npx vitest run     # component + util tests
```

---

## 15. Testing

### Backend — `python -m pytest` from the repository root

`pytest.ini` sets `testpaths = tests` and `pythonpath = backend`. Integration tests
**auto-skip with an actionable message** when the infrastructure is down:

```
skipped: infrastructure unavailable: postgresql, elasticsearch.
Start it with `docker compose up -d postgres mongodb elasticsearch rabbitmq`.
```

| Suite | Files | Covers |
| --- | --- | --- |
| Unit (40) | `test_pricing`, `test_schemas`, `test_es_document`, `test_search_query` | Decimal totals, duplicate-line merging, schema rules, ES document shape, exact query/aggregation DSL |
| Integration (61) | `test_products_api` | listing, filters, facets, create/update/soft-delete, inactive hidden |
| | `test_orders_api` | server-side totals, client total ignored, snapshots (incl. the rename demo), **forced INSERT failure → full rollback with unchanged row counts**, 404/422 paths, status PATCH + sync |
| | `test_search_api` | free text, every filter, KPI ↔ result agreement, pagination, validation, **PG/Mongo architecture guard**, PG ↔ ES count parity |
| | `test_sync_task` | document build from PG, idempotency, status propagation, snapshot-not-live-catalog, reindex script, publish success/failure, `Retry` + `max_retries` exhaustion, task registration |

```bash
python -m pytest                 # 101 passed
python -m pytest -q tests/unit   # fast, no infrastructure needed
```

### Frontend — `npx vitest run`

28 tests: cart store, currency/date/status/validation utils, shared components, and a
full-app render smoke test that mounts every screen through the real router.

### Acceptance

```bash
.venv/bin/python /tmp/opencode/acceptance.py   # 28 end-to-end checks against :8000
```

Verifies health, catalog, facets, all search filters + KPIs, the snapshot demo, order creation
with server-computed totals, worker indexing, status PATCH → ES propagation, catalog CRUD with
soft delete, error envelopes, and PG/ES parity.

---

## 16. Demo flow

Start everything (§13), then walk the five screens:

1. **Storefront (`/`)** — 26 active products, category/tag/price filters, search box,
   "Log In As" user selector, cart badge. Note `Wireless Mouse Pro — $60.00` (renamed catalog).
2. **Cart → Checkout (`/checkout`)** — adjust quantities in the drawer, then place the order.
   Confirm the success panel and the order number (`ORD-0001xx`).
3. **Admin search (`/admin/search`)** — search `Wireless`; watch the revenue and status KPIs
   narrow as you apply `SHIPPED`, a date range, or a price band. Search `Wendy Wireless` to see
   her orders. Open a result → order details.
4. **Order details (`/admin/orders/:id`)** — canonical PostgreSQL data. Change the status to
   `SHIPPED`; the sync indicator shows `search_indexed_at` update after the worker runs, and
   re-running the Screen 3 search shows the new status.
5. **Catalog admin (`/admin/catalog`)** — create a product (attributes + variants), edit its
   price, then delete it: the storefront hides it immediately (soft delete).

**The snapshot demo:** open an order that contains `Wireless Mouse` from before the rename.
PostgreSQL and Elasticsearch both show `Wireless Mouse — $50.16` while the storefront sells
`Wireless Mouse Pro — $60.00`. That is the whole snapshotting requirement in one screen.

**RabbitMQ UI:** <http://localhost:15672> → Queues → `orders_sync` to see messages arrive and
get consumed.

---

## 17. Known limitations

Honestly stated, because the design choices above are trade-offs:

1. **At-least-once delivery ⇒ possible duplicate deliveries.** Safe because `_id = order_id`
   makes indexing an upsert, but a redelivered task does repeat work.
2. **Elasticsearch can lag PostgreSQL.** Between COMMIT and the worker finishing, a brand-new
   order may not be searchable yet (typically milliseconds). PostgreSQL is authoritative
   throughout — a missing or stale ES document never affects order data, and
   `python -m scripts.reindex_orders` is the recovery path.
3. **No transactional outbox.** If PostgreSQL commits and the process dies *before* publishing
   to RabbitMQ, that order is not queued (the API reports `sync.enqueued: false`). The order is
   still safe in PostgreSQL; a reindex or a status update re-publishes it. An outbox/CDC would
   close this window — deliberately **not** used here to keep exactly one sync strategy.
4. **No polling fallback / CDC / Debezium / Kafka.** One path, by requirement.
5. **Sync tasks carry only `order_id`.** The worker re-reads PostgreSQL, so a message never
   carries order contents — but a task for a *deleted* order is a no-op (`status: skipped`).
6. **Money as `double` in Elasticsearch.** Fine for analytics/KPIs; PostgreSQL keeps the exact
   `numeric(12,2)` values, and all money maths in the API uses `Decimal`.
7. **Synchronous SQLAlchemy + sync FastAPI endpoints.** Simple and adequate for this scale;
   not a high-concurrency design (no async drivers, no connection-pool tuning beyond defaults).
8. **Elasticsearch runs single-node with security disabled** and a 512 MB heap — a demo
   configuration, not production.
9. **`ELASTICSEARCH_REFRESH_ON_WRITE=true`** trades write throughput for immediate visibility
   in tests/demo; turn it off under real load.
10. **`search_indexed_at` is bookkeeping, not a guarantee.** It is written after indexing and is
    ignored if that bookkeeping update fails.
11. **One RabbitMQ queue and one worker pool** for all sync work; no per-tenant partitioning or
    rate limiting.
12. **Frontend dev server talks to a CORS-allowed API on `:8000`.** The production image serves
    the built bundle through nginx and needs `VITE_API_BASE_URL` baked in at build time.
13. **Seeded data is intentionally small** (44 orders) so aggregations are instant; the query
    paths are not load-tested.

---

## Repository layout

```
.
├── backend/
│   ├── app/
│   │   ├── api/          products · orders · users · search · health
│   │   ├── clients/      mongodb · elasticsearch · rabbitmq
│   │   ├── core/         config · database · errors · logging
│   │   ├── models/       SQLAlchemy models (users, orders, order_items)
│   │   ├── repositories/ mongo/ · postgres/ · elasticsearch/ (document, mapping, search, orders)
│   │   ├── schemas/      Pydantic request/response models
│   │   ├── services/     product_service · order_service · search_service · sync_service
│   │   ├── tasks/        celery_app · elasticsearch_tasks
│   │   └── main.py       FastAPI entry point + lifespan
│   ├── scripts/          seed.py · reindex_orders.py
│   └── Dockerfile
├── frontend/             Vue 3 app (src/, tests/, vite.config.js, Dockerfile, nginx.conf)
├── tests/                pytest suite (unit/ + integration/)
├── docker-compose.yml
├── .env.example
├── TODO.md               checklist — [x] only when verified
├── IMPLEMENTATION_STATUS.md
└── pytest.ini
```
