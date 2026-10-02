# MERIDIAN

## E-Commerce Order Management & Search Service

### Complete System Knowledge Guide

---

**Repository:** `E-Commere Order Management and Search Service/`
**Stack:** Vue 3 + Vite · FastAPI + SQLAlchemy · PostgreSQL · MongoDB · Elasticsearch · RabbitMQ + Celery · Docker Compose · Nginx
**Document type:** Teaching reference / knowledge base for the whole codebase
**Ground rule:** every statement below was verified against the repository source. Anything not
verifiable from the code is explicitly labelled.

### How to read the labels in this document

| Label | Meaning |
| --- | --- |
| **Implementation fact** | Verified by reading the actual file/line referenced. |
| **Inference** | A reasonable engineering interpretation of *why* the code does something. The code does not state it. |
| **General engineering knowledge** | Background concept that is not project-specific. |
| **Not confirmed from the available source** | Could not be verified in the repository — do not assume it. |

When documentation and code disagree, this guide says so explicitly in a
**Documentation vs. implementation** callout and then documents the *implementation*.

---

## Table of Contents

- [Cover & reading conventions](#meridian)
- [PART 1 — Project Overview](#part-1--project-overview)
- [PART 2 — Business Domain](#part-2--business-domain)
- [PART 3 — User Roles](#part-3--user-roles)
- [PART 4 — Technology Stack](#part-4--technology-stack)
- [PART 5 — Why Polyglot Persistence?](#part-5--why-polyglot-persistence)
- [PART 6 — System Architecture](#part-6--system-architecture)
- [PART 7 — Component Responsibilities](#part-7--component-responsibilities)
- [PART 8 — Complete Data Flows](#part-8--complete-data-flows)
- [PART 9 — Database Architecture](#part-9--database-architecture)
- [PART 10 — Transactional Consistency](#part-10--transactional-consistency)
- [PART 11 — RabbitMQ + Celery](#part-11--rabbitmq--celery)
- [PART 12 — Authentication](#part-12--authentication)
- [PART 13 — Frontend Architecture](#part-13--frontend-architecture)
- [PART 14 — Frontend Routing](#part-14--frontend-routing)
- [PART 15 — Pinia / State Management](#part-15--pinia--state-management)
- [PART 16 — API Client](#part-16--api-client)
- [PART 17 — Storefront](#part-17--storefront)
- [PART 18 — Search Experience](#part-18--search-experience)
- [PART 19 — Product Cards](#part-19--product-cards)
- [PART 20 — Cart](#part-20--cart)
- [PART 21 — Checkout](#part-21--checkout)
- [PART 22 — Admin Portal](#part-22--admin-portal)
- [PART 23 — Product Image System](#part-23--product-image-system)
- [PART 24 — File-by-File Codebase Map](#part-24--file-by-file-codebase-map)
- [PART 25 — File Relationship Map](#part-25--file-relationship-map)
- [PART 26 — Backend Request Lifecycle](#part-26--backend-request-lifecycle)
- [PART 27 — Pydantic Schemas](#part-27--pydantic-schemas)
- [PART 28 — SQLAlchemy Models](#part-28--sqlalchemy-models)
- [PART 29 — Services / Business Logic](#part-29--services--business-logic)
- [PART 30 — Error Handling](#part-30--error-handling)
- [PART 31 — Security](#part-31--security)
- [PART 32 — Docker Architecture](#part-32--docker-architecture)
- [PART 33 — Environment Configuration](#part-33--environment-configuration)
- [PART 34 — Testing](#part-34--testing)
- [PART 35 — Seed Data](#part-35--seed-data)
- [PART 36 — Snapshot Semantics](#part-36--snapshot-semantics)
- [PART 37 — Elasticsearch Projection](#part-37--elasticsearch-projection)
- [PART 38 — Important Design Decisions](#part-38--important-design-decisions)
- [PART 39 — Edge Cases and Gotchas](#part-39--edge-cases-and-gotchas)
- [PART 40 — Troubleshooting Guide](#part-40--troubleshooting-guide)
- [PART 41 — Knowledge Bytes](#part-41--knowledge-bytes)
- [PART 42 — File-Specific Knowledge Bytes](#part-42--file-specific-knowledge-bytes)
- [PART 43 — Code Snippets](#part-43--code-snippets)
- [PART 44 — Cross-Reference System](#part-44--cross-reference-system)
- [PART 45 — Complete File Index](#part-45--complete-file-index)
- [PART 46 — Master System Map](#part-46--master-system-map)
- [PART 47 — 30-Minute Teaching Path](#part-47--30-minute-teaching-path)
- [PART 48 — 20 Must-Remember Facts](#part-48--20-must-remember-facts)
- [PART 49 — Glossary](#part-49--glossary)
- [PART 50 — Self-Test Checklist](#part-50--self-test-checklist)

---

# PART 1 — Project Overview

**Level 1: What is this application?**

## 1.1 Project name

- **Repository / backend app name:** `E-Commerce Order Management & Search Service`
  (**Implementation fact:** `backend/app/core/config.py:34` →
  `app_name: str = "E-Commerce Order Management & Search Service"`).
- **Storefront brand shown to users:** **Meridian** / **Meridian Store**
  (**Implementation fact:** `frontend/src/layouts/StorefrontLayout.vue` renders
  `<span class="brand__name">Meridian</span>` in the header and
  `<span class="brand__name">Meridian Store</span>` + `Everything for the way you work.`
  in the footer).
- **Docker Compose project name:** `ecommerce-orders` (`docker-compose.yml:12`).

## 1.2 Objective

Build a working e-commerce system that demonstrates **polyglot persistence**: several databases
in one application, each used only for the job it is genuinely good at, with a real asynchronous
pipeline between them.

Five application "screens" exist, and each one is deliberately bound to exactly one data store
(**Implementation fact:** `README.md` §1 table, verified against `frontend/src/router/index.js`):

| # | Screen | Route | Data source |
| --- | --- | --- | --- |
| 1 | Storefront | `/` | MongoDB product catalog |
| 2 | Checkout | `/checkout` | MongoDB (pricing) → PostgreSQL (order) |
| 3 | Admin search dashboard | `/admin/search` | **Elasticsearch only** (results + KPIs) |
| 4 | Admin order details | `/admin/orders/:id` | PostgreSQL (canonical) + status PATCH → sync |
| 5 | Catalog admin | `/admin/catalog` | MongoDB CRUD (soft delete) |

The design rule the whole codebase obeys: **a screen never reads from a database it does not own.**

## 1.3 The problem being solved

**Level 2: Why was it built?**

Real order-management systems fail when one database is asked to do everything:

1. **Catalog edits corrupt history.** If a stored order only contains a *product id*, then
   renaming or repricing the product silently rewrites what past customers paid.
2. **Search degrades writes.** Full-text search with facets over raw relational rows is slow and
   awkward; bolting search onto the transactional store couples write latency to read features.
3. **Async work blocks the user.** Indexing/analytics inside the request path makes checkout wait
   for infrastructure that can legitimately be down.

This project is a reference implementation that separates those concerns honestly: MongoDB owns
live catalog data, PostgreSQL owns money and orders transactionally, Elasticsearch owns search
and analytics as a *derived copy*, and RabbitMQ + Celery move data from the source of truth to
the projection after the transaction commits.

*(Label: parts 1–3 of this subsection are **Inference** about intent; the structural separation
itself is **Implementation fact** — see [PART 7](#part-7--component-responsibilities) for the
verified per-file evidence.)*

## 1.4 Intended users

**Implementation fact** — `backend/app/models/postgres.py:50`:

```python
__table_args__ = (
    CheckConstraint("role IN ('CUSTOMER', 'ADMIN')", name="ck_users_role"),
)
```

- **Customer** — browses the storefront, searches products, maintains a cart, checks out, and can
  read **only their own** orders.
- **Admin** — searches orders in Elasticsearch, opens any order, changes order status, and manages
  the product catalog including images.
- (A third "System" actor — the Celery worker — appears in the legacy
  `Knowledge bytes/Knowledge_Bytes.txt`; it is a *process*, not a database role.
  See [Documentation vs. implementation](#doc-vs-code).)

**Documentation vs. implementation** <a name="doc-vs-code" id="doc-vs-code"></a>

| Topic | Documentation says | Implementation does |
| --- | --- | --- |
| Roles | `Knowledge bytes/Knowledge_Bytes.txt:11` lists "**three** user roles: Customer, Admin, System" | The `users.role` CHECK constraint allows exactly two values: `CUSTOMER`, `ADMIN`. "System" is a process (Celery), not a role. |
| Test count | `README.md` Quick Start says "`python -m pytest` (101 tests)" | The suite currently reports **100 passed** locally (the count drifts with the suite; README was not updated). |
| Search features | The legacy Knowledge Bytes file describes general search behaviour | Actual search is exactly `POST /api/search/orders` with `multi_match` + filters + aggregations ([PART 14](#part-14--frontend-routing) of the bytes, [PART 9](#part-9--database-architecture) here). |
| Error envelope | The API is documented as returning `{"error": {...}}` for failures (PART 30 of this guide) | 401/403 come back as FastAPI's default `{"detail": "..."}` — no `HTTPException` handler is registered, only `AppError` handlers ([PART 30 §30.2](#302-documentation-vs-implementation-a-second-shape-exists)). |
| Environment template | `.env.example` is presented as the complete configuration | `JWT_SECRET_KEY` and `UPLOADS_DIR` are read by `Settings` but appear in **neither** `.env.example` nor `.env`; both silently fall back to defaults ([PART 33](#part-33--environment-configuration), [PART 39 gotcha #12](#part-39--edge-cases-and-gotchas)). |
| Search query type | Documentation around the search feature references a `bool_prefix` query | No `bool_prefix` clause exists in the repository — the implemented clause is `multi_match` over `search_as_you_type`/`text` fields (**Not confirmed from the available source**, [Byte 92](#byte-92-partial-search)). |

## 1.5 Major capabilities (all verified against code)

- Product catalog CRUD with facets, filters, sorting, pagination (MongoDB).
- Product image upload / replace / remove with validation and local persistent storage.
- Cart → checkout → order placement with **server-side re-pricing** and an **explicit SQL
  transaction** over `orders` + `order_items`.
- Asynchronous order→search synchronization through RabbitMQ + Celery.
- Admin full-text order search with filters, pagination and revenue/status aggregations.
- JWT login with role-based authorization enforced on the server.
- Health endpoint that probes all four infrastructure dependencies.
- Deterministic, self-verifying seed data and a reindex script.
- Unit + integration tests (pytest) and frontend tests (Vitest).

## 1.6 A simple example: "A customer places an order"

**Level 3: What does a user do with it?**

1. The customer opens `/`. `StorefrontView.vue` calls `GET /api/products?visibility=active…`,
   FastAPI's `product_service.list_products()` reads MongoDB, and product cards render.
2. They click **ADD TO CART** on a card. `ProductCard.vue` calls `cart.add(product)` in the
   Pinia `cart` store — a *client-side* snapshot of title/price. Nothing is sent to a server.
3. They open the cart drawer and press **Checkout** → `/checkout` (requires login).
4. `CheckoutView.vue` re-reads each product (`GET /api/products/{id}`) to show live prices, then
   posts `POST /api/orders` with **only** `items: [{product_id, quantity}]` — no prices, no total.
5. `order_service.create_order()` validates every line against **live MongoDB** (`resolve_cart`),
   re-prices it, and opens an explicit PostgreSQL transaction:
   `BEGIN → INSERT orders → INSERT order_items → COMMIT`.
6. **Only after COMMIT**, `sync_service.publish_order_sync(order.id, "order_created")` queues a
   Celery task on RabbitMQ (`orders_sync` queue).
7. The Celery worker rebuilds the whole order document **from PostgreSQL** and upserts it into
   Elasticsearch with `_id = order_id`.
8. The customer sees `ORD-000064` and `₹229.00`; the admin later finds that order in
   `/admin/search` — which queries Elasticsearch, not PostgreSQL.
9. If RabbitMQ, the worker, or Elasticsearch is down, steps 7–8 degrade: the order is **already
   durable in PostgreSQL**, the API response carries `sync.enqueued: false` plus an error string,
   and nothing rolls back.

---

# PART 2 — Business Domain

**Level 4–5: vocabulary and why the domain is shaped this way.**

## 2.1 Terms

| Term | Definition in *this* codebase | Verified where |
| --- | --- | --- |
| **Customer** | A row in PostgreSQL `users` with `role='CUSTOMER'`; authenticates with email + bcrypt password; owns orders through `orders.user_id`. | `backend/app/models/postgres.py:27-51` |
| **Admin** | A `users` row with `role='ADMIN'`; required by every catalog write and by order search / status changes. | `backend/app/core/auth.py` → `require_admin` |
| **Product** | A MongoDB document in the `products` collection: `sku`, `title`, `description`, `price`, `category`, `tags[]`, `attributes{}`, `variants[]`, `active`, `image_url`, timestamps. | `backend/app/schemas/products.py:29-47` |
| **Catalog** | The `products` collection as a whole, served by `GET /api/products` and managed by the catalog admin screen. | `backend/app/repositories/mongo/product_repo.py` |
| **Category** | A free-form product string validated against four values: `peripherals`, `audio`, `cables`, `office`. | `backend/app/schemas/products.py:10` → `VALID_CATEGORIES` |
| **Tag** | A lowercase label on a product (`tags: list[str]`, max 30) used for facets, storefront tag marquee, and catalog filtering. | `backend/app/schemas/products.py:35`; `product_repo.ensure_indexes()` |
| **Order** | PostgreSQL `orders` row: `order_number` (`ORD-000123`), `user_id`, `status`, `total_amount numeric(12,2)`, `order_date`, `created_at`, `updated_at`, `search_indexed_at`. | `backend/app/models/postgres.py:54+` |
| **Order item** | PostgreSQL `order_items` row belonging to one order: `product_id`, `title` (snapshot), `quantity`, `unit_price` (snapshot), `line_total`. | `backend/app/models/postgres.py`; `README.md` §4 |
| **Product snapshot** | The *copy* of `title` and `unit_price` written into `order_items` at purchase time — immutable history, independent of MongoDB afterwards. | `backend/app/services/order_service.py` (`ResolvedLine`, `create_order`) |
| **Search projection** | The Elasticsearch `orders` document: a **derived copy** of a PostgreSQL order, rebuilt by the Celery worker. Never authoritative. | `backend/app/repositories/elasticsearch/document.py` |
| **Synchronization** | The path `PostgreSQL (COMMIT) → RabbitMQ → Celery task → Elasticsearch upsert`. The only sync mechanism present. | `backend/app/services/sync_service.py`, `backend/app/tasks/elasticsearch_tasks.py` |
| **Live product data** | Current MongoDB `products` documents — what the storefront shows *now*. | — |
| **Historical order snapshot data** | `order_items.title` / `unit_price` (+ the copied fields in the ES document) — what the customer paid *then*. | — |

## 2.2 Live product data vs. historical order snapshot data

This is the single most important domain distinction in the project.

```
T0  MongoDB:  { sku: "PER-1001", title: "Wireless Mouse",  price: 50.16 }
    Customer orders 1 × PER-1001
    PostgreSQL order_items: title='Wireless Mouse', unit_price=50.16
    PostgreSQL orders.total_amount = 50.16

T1  Admin edits MongoDB: title="Wireless Mouse Pro", price=60.00

T2  Storefront shows:      Wireless Mouse Pro  ₹60.00   ← live data (MongoDB)
    Old order still shows: Wireless Mouse      ₹50.16   ← snapshot (PostgreSQL)
    Elasticsearch doc for that order also shows 50.16   ← rebuilt FROM PostgreSQL
```

**Why the snapshot must win.** *(General engineering knowledge, made concrete here)* An order is a
financial and legal record: "what was sold, to whom, for how much, when." If it stored only
`product_id`, every future catalog edit would retroactively change revenue reports, invoices and
customer receipts. Snapshotting converts a mutable reference into an immutable fact.

**Implementation facts that enforce this:**

1. `order_service.resolve_cart()` reads live MongoDB **at order time** and stores `title` and
   `unit_price` in `ResolvedLine` → `OrderItem` (`backend/app/services/order_service.py`).
2. `build_order_document()` builds ES documents from the **PostgreSQL** `Order` object only — its
   module docstring states: *"The document contains snapshots stored in PostgreSQL — never live
   MongoDB product data"* (`backend/app/repositories/elasticsearch/document.py:1-10`).
3. Product `DELETE` is a **soft delete** (`active=false`) precisely so old orders keep a
   meaningful product reference (`backend/app/api/products.py` delete description).
4. Tests lock this in: `tests/integration/test_orders_api.py:142
   test_historical_snapshot_survives_the_wireless_mouse_rename` and
   `tests/integration/test_sync_task.py:123
   test_sync_uses_postgres_snapshots_not_live_mongo_titles`.

**Verification you can run:** the seed deliberately renames `Wireless Mouse ($50.16)` →
`Wireless Mouse Pro ($60.00)` *after* orders exist (README §12 "Snapshot demo" row; assertion in
`backend/scripts/seed.py`).

---

# PART 3 — User Roles

**Level 6: authorization as two separate layers.**

## 3.1 What each role can access

| Capability | Customer | Admin | Enforced by |
| --- | --- | --- | --- |
| Browse products, facets, single product | ✅ | ✅ | public endpoints (`GET /api/products*`) |
| Place an order | ✅ | ✅ | `POST /api/orders` (no auth dependency — see below) |
| Read an order | Own only | All | `GET /api/orders/{id}` ownership check in `orders.py` |
| Change order status | ❌ | ✅ | `require_admin` on `PATCH /api/orders/{id}/status` |
| Search orders | ❌ | ✅ | `get_current_user` + `require_admin` on `POST /api/search/orders` |
| Create/update/delete product | ❌ | ✅ | `require_admin` on `POST/PATCH/DELETE /api/products` |
| Upload/replace/remove image | ❌ | ✅ | `require_admin` on `POST/DELETE /api/products/{id}/image` |
| List seeded users | ✅ | ✅ | `GET /api/users` has **no** auth dependency (`backend/app/api/users.py`) |
| Health | ✅ | ✅ | public |

**Implementation fact — order ownership.** `backend/app/api/orders.py` (route docstring and
handler): `GET /api/orders/{id}` returns canonical order details from PostgreSQL and checks that
the authenticated user owns the order (customers get `403`/`404` for someone else's order —
asserted by `tests/integration/test_orders_api.py`); admins may read any order.

**Not confirmed from the available source:** whether `POST /api/orders` requires a bearer token.
The router file does not declare an auth dependency on the POST handler (it depends only on the
payload), while the frontend *does* require login before `/checkout` (route meta
`requiresAuth: true`). Treat order placement as server-open in the API, login-gated in the UI.

## 3.2 Frontend authorization UX vs. backend authorization security

| Layer | Where | What it does | What it is **not** |
| --- | --- | --- | --- |
| **Frontend UX** | `frontend/src/router/index.js` `beforeEach` guard; `authStore.isAdmin` in templates (e.g. the `Admin` nav link rendered only `v-if="authStore.isAdmin"`) | Hides links, redirects unauthenticated users to `/login?redirect=…`, avoids confusing dead ends | Security. Anybody can delete the JS or call `curl localhost:8000/api/products` directly. |
| **Backend security** | `require_admin` / `get_current_user` dependencies (`backend/app/core/auth.py`) applied per route | Rejects requests without a valid JWT or without role `ADMIN`, returning the standard error envelope with `401`/`403` | Convenience. It knows nothing about the UI. |

**Why both exist** *(General engineering knowledge)*: the frontend layer is about *experience*;
the backend layer is the *authority*. Hiding a button is not authorization — the server must
re-check every request. This project demonstrates the rule cleanly: the frontend hides the Admin
link, but the guarantee comes from `Depends(require_admin)`.

---

# PART 4 — Technology Stack

**Level 4: every technology actually present.**

Only technologies confirmed by files in the repository are listed.

## 4.1 Frontend

| Technology | Purpose | Where used | Why it exists | Important files |
| --- | --- | --- | --- | --- |
| **Vue 3** (`<script setup>`, Composition API) | UI framework for storefront + admin | `frontend/src/**` (all `.vue`) | Reactive component model, single-file components | `main.js`, every `views/*.vue` |
| **Vite** | Dev server + production bundler | `frontend/vite.config.js`, `npm run dev/build` | Fast HMR, proxies `/api` and `/uploads` to the backend | `frontend/vite.config.js` |
| **Vue Router** | Client-side routing + guards | `frontend/src/router/index.js` | Deep links, `requiresAuth`/`requiresAdmin` guards, `scrollBehavior` | `router/index.js` |
| **Pinia** | State stores (auth, cart, toast) | `frontend/src/stores/*.js` | Shared reactive state outside the component tree | `stores/auth.js`, `stores/cart.js`, `stores/toast.js` |
| **Axios** | HTTP client with interceptors | `frontend/src/api/client.js` | Central place for base URL, `Authorization` header, error envelope decoding | `api/client.js`, `api/*.js` |
| **Vitest + @vue/test-utils + jsdom** | Frontend tests | `frontend/tests/*.spec.js`, `test` config in `vite.config.js` | Component/unit tests run in jsdom | `frontend/tests/cart.spec.js` (28 tests total across 5 files) |
| **Global CSS token system** | Design tokens + utilities | `frontend/src/styles/tokens.css`, `utilities.css` | One source of truth for colour/space/typography; no browser-default styling | `styles/tokens.css`, `styles/utilities.css` |

## 4.2 Backend

| Technology | Purpose | Where used | Why it exists | Important files |
| --- | --- | --- | --- | --- |
| **Python 3.11** | Runtime | `backend/Dockerfile` (`python:3.11-slim`) | Typed, mature ML/data ecosystem; FastAPI's language | — |
| **FastAPI** | HTTP framework, DI, OpenAPI | `backend/app/main.py`, `app/api/*` | Dependency injection (`Depends`), auto `/docs`, Pydantic validation | `main.py`, `api/*.py` |
| **Pydantic v2** | Request/response schemas + settings | `app/schemas/*`, `app/core/config.py` | Validation, serialization, typed config from env | `schemas/orders.py`, `core/config.py` |
| **SQLAlchemy 2 (sync)** | ORM for PostgreSQL | `app/models/postgres.py`, `app/core/database.py` | Declarative models, explicit transactions still possible | `models/postgres.py` |
| **psycopg** | PostgreSQL driver | `postgres_dsn` uses `postgresql+psycopg://` | Native, supported PG driver for SQLAlchemy | `core/config.py:112` |
| **passlib + bcrypt** | Password hashing | `core/auth.py` (`CryptContext(schemes=["bcrypt"])`) | Never store plaintext passwords | `core/auth.py` |
| **python-jose (`jose`)** | JWT create/decode | `core/auth.py` (`jwt.encode/decode`, HS256) | Stateless authentication | `core/auth.py`, `core/config.py` |
| **pymongo** | MongoDB driver | `app/clients/mongodb.py`, `repositories/mongo/product_repo.py` | Direct document access with indexes/aggregation | `clients/mongodb.py` |
| **elasticsearch-py** | Elasticsearch client | `app/clients/elasticsearch.py` | Query/aggregation DSL, index management | `clients/elasticsearch.py` |
| **Celery 5** | Background worker | `app/tasks/celery_app.py` | Consumes queue, retries, timeouts | `tasks/celery_app.py` |
| **Kombu** | AMQP connection probe | `app/clients/rabbitmq.py` (`Connection(...).connect()`) | Health check for RabbitMQ | `clients/rabbitmq.py` |
| **Uvicorn** | ASGI server | `backend/Dockerfile`, compose `command: uvicorn …` | Serves the FastAPI app | `backend/Dockerfile` |
| **python-multipart** | `UploadFile` parsing | required by `File(...)` image endpoints | Multipart/form-data uploads | `backend/requirements.txt` |

## 4.3 Data / messaging / infra / tests

| Technology | Purpose | Where used | Important files |
| --- | --- | --- | --- |
| **PostgreSQL 16** | Source of truth: `users`, `orders`, `order_items` | compose service `postgres` | `docker-compose.yml:31`, `models/postgres.py` |
| **MongoDB 7** | Product catalog documents | compose service `mongodb` | `clients/mongodb.py`, `repositories/mongo/product_repo.py` |
| **Elasticsearch 8.15.3** | Order search + aggregations | compose service `elasticsearch` | `repositories/elasticsearch/*` |
| **RabbitMQ 3.13 (management)** | Broker, queue `orders_sync` | compose service `rabbitmq` | `clients/rabbitmq.py`, `sync_service.py` |
| **Docker / Docker Compose** | Everything, reproducibly | `docker-compose.yml`, two multi-stage Dockerfiles | `backend/Dockerfile`, `frontend/Dockerfile` |
| **Nginx** | Production static host + reverse proxy for `/api` and `/uploads` | `frontend/nginx.conf`, `frontend-prod` service | `frontend/nginx.conf` |
| **pytest** | Backend unit + integration tests | `pytest.ini`, `tests/` | `tests/conftest.py` |
| **.env / .env.example** | Configuration template | repo root | `.env.example` (never commit real secrets) |

**Explicitly absent** (verified by searching the repo): Kafka, Debezium, Redis, MySQL, OpenSearch,
CDC tooling, Terraform, Kubernetes. README §2 states this as a deliberate choice.

---

# PART 5 — Why Polyglot Persistence?

**Level 5: why each technology is used where it is used.**

Polyglot persistence = *using different data stores in one system, each for the data shape and
access pattern it fits best* — rather than one "universal" database.

| Store | Data shape it excels at | Access pattern in this app | Why not the others |
| --- | --- | --- | --- |
| **MongoDB** | Flexible documents; nested arrays (`tags`, `attributes`, `variants`); schema evolution | Filter/sort/paginate catalog, facet counts, `$regex` text search, unique `sku` | No cross-document transactions needed here; document shape varies per product |
| **PostgreSQL** | Rows, keys, constraints, **ACID transactions** | Multi-row write of `orders` + `order_items` with CHECK constraints; FK integrity to `users` | Relational schema for orders is rigid and correct; money stored as `numeric(12,2)` |
| **Elasticsearch** | Inverted indexes, ranking, **bucket aggregations** | Full-text order search across customer/item fields, filters, revenue KPI, status counts | Not transactional; not a system of record; would be wrong as source of truth |
| **RabbitMQ** | Durable hand-off of work between processes | Queue `orders_sync` with task payload `{order_id, reason}` | Decouples API availability from worker availability |
| **Celery** | Executing that work with retries/time limits | Rebuild + upsert ES document, `task_acks_late`, 5 retries with backoff | Keeps indexing out of the HTTP request cycle |

## 5.1 The tradeoff (inference, clearly labelled)

**Tradeoff (Inference):** polyglot persistence buys *fit* and *isolation* at the cost of
**eventual consistency between stores**. After checkout, there is a window where PostgreSQL has
the order and Elasticsearch does not. The project accepts this deliberately: PostgreSQL is
authoritative for order *facts*; Elasticsearch is a *searchable projection* that may lag by
milliseconds and can always be rebuilt (`backend/scripts/reindex_orders.py`).

## 5.2 Why Elasticsearch must NOT be the source of truth for orders

**Implementation facts:**

- Its mapping stores money as `double` (analytics precision), while PostgreSQL stores exact
  `numeric(12,2)` (`backend/app/repositories/elasticsearch/mappings.py:9-10` docstring).
- It is populated *asynchronously* after commit, so it can be missing brand-new orders.
- `GET /api/orders/{id}` deliberately reads PostgreSQL: *"canonical order details (never
  Elasticsearch)"* (`backend/app/api/orders.py` docstring).
- `search_service` never opens a PostgreSQL session or Mongo cursor
  (`backend/app/services/search_service.py:1-8`), and conversely nothing reads orders *from*
  Elasticsearch except search.
- The index can be deleted and rebuilt from scratch — a property a system of record must not have.

---

# PART 6 — System Architecture

**Level 6: the high-level structure, generated from the actual repository.**

## 6.1 Architecture diagram

```
                    ┌────────────────────────────┐
                    │   Browser (Customer/Admin) │
                    └─────────────┬──────────────┘
                                  │  HTTP (REST/JSON over Axios)
                                  ▼
        dev :5173  Vite dev server ──proxy /api,/uploads──┐
        prod:8080  Nginx  ──location /api/ ──proxy_pass───┤
        prod:8080  Nginx  ──location /uploads/ ─proxy─────┤
                                                          ▼
                    ┌───────────────────────────────────────────────────┐
                    │            FastAPI  (backend :8000)               │
                    │  api/ products · orders · users · search · auth   │
                    │        health                                     │
                    │  services/ product · order · search · sync · auth │
                    └───┬───────────────┬───────────────────┬───────────┘
              read/write│               │ read/write        │ read (after COMMIT: publish)
                        ▼               ▼                   ▼
            ┌───────────────────┐  ┌─────────────────┐  ┌─────────────┐
            │     MongoDB       │  │   PostgreSQL    │  │  RabbitMQ   │
            │  db `catalog`     │  │ users / orders  │  │ queue       │
            │  collection       │  │ / order_items   │  │ orders_sync │
            │  `products`       │  │ (SOURCE OF      │  └──────┬──────┘
            │                   │  │  TRUTH)         │         │ consume
            └───────────────────┘  └────────┬────────┘         ▼
            ▲ serves /uploads files         │         ┌─────────────────┐
            │ (StaticFiles mount)           │         │  Celery worker  │
     ┌──────┴────────┐                     │         │  reads PG,      │
     │  volume       │                     │         │  builds doc,    │
     │ uploads_data  │                     │         │  upserts        │
     └───────────────┘                     │         └───────┬─────────┘
                                            │                 │ _id = order_id
                                            │                 ▼
                                            │         ┌──────────────────┐
                                            │         │  Elasticsearch   │
                                            │         │  index `orders`  │
                                            └────────▶│  (PROJECTION)    │
                                        POST /api/search/orders (admin)  │
                                                      └──────────────────┘
```

## 6.2 Every connection: who, what, when, why

| # | From → To | What data moves | When | Why |
| --- | --- | --- | --- | --- |
| 1 | Browser → Nginx/Vite → FastAPI | REST/JSON requests, JWT in `Authorization` | Every user action | Single API surface |
| 2 | FastAPI → MongoDB | Product documents (read), product writes, `image_url` updates | Catalog reads; admin CRUD; image upload; **cart validation during checkout** | Catalog ownership |
| 3 | FastAPI → PostgreSQL | `users` reads; `orders`+`order_items` transactional writes; `search_indexed_at` bookkeeping | Login, order placement, status PATCH, worker bookkeeping | Financial source of truth |
| 4 | FastAPI → RabbitMQ | Small Celery task message `{"order_id": N, "reason": "order_created"|"status_update"}` on `orders_sync` | **After** COMMIT (order create or status change) | Hand work off without blocking the request |
| 5 | RabbitMQ → Celery worker | The same task message (JSON serializer) | Worker available; redelivered if worker dies (`acks_late`, `visibility_timeout 3600`) | Execution with retries |
| 6 | Celery worker → PostgreSQL | Re-reads the order + items + user | Task execution | Build the doc from the source of truth (message carries no order content) |
| 7 | Celery worker → Elasticsearch | Full order document, upsert at `_id = order_id` | Task execution, up to 5 attempts with backoff | Make the order searchable |
| 8 | FastAPI → Elasticsearch | `POST /api/search/orders` query DSL (bool + aggregations) | Admin search screen | Read the projection |
| 9 | Celery worker → PostgreSQL | `orders.search_indexed_at = now()` | After successful index | UI bookkeeping ("indexed" indicator) — best-effort |
| 10 | FastAPI → browser (files) | Static files from `uploads/products/…` via `StaticFiles` mount at `/uploads` | Image `<img>` requests | Serve locally stored uploads |

**What does NOT exist** (Implementation fact): no direct MongoDB→Elasticsearch path, no
PostgreSQL→Elasticsearch path, no polling loop, no CDC/outbox, no second broker.

---

# PART 7 — Component Responsibilities

**Level 7: the "constitution" of each component.**

### Component: Vue Frontend (`frontend/`)
- **Responsibility:** render all five screens, hold client state (auth, cart, toasts), talk to the API.
- **Reads:** API responses only. **Writes:** nothing durable — cart lives in memory.
- **Communicates with:** FastAPI over HTTP (direct or through Vite/Nginx proxy).
- **Does NOT communicate with:** MongoDB, PostgreSQL, Elasticsearch, RabbitMQ (never).
- **Why it exists:** presentation and UX; all rules are re-checked server-side.

### Component: FastAPI (`backend/app/`)
- **Responsibility:** HTTP surface, validation, authorization, business rules, transaction boundaries, publishing sync tasks.
- **Reads:** MongoDB (catalog), PostgreSQL (users/orders), Elasticsearch (search endpoint only).
- **Writes:** MongoDB (catalog + `image_url`), PostgreSQL (orders/items/status/`search_indexed_at`), RabbitMQ (task publish), local disk (image files).
- **Communicates with:** all four data services + filesystem.
- **Does NOT communicate with:** nothing is skipped — but note the *worker*, not the API, writes to Elasticsearch.
- **Why it exists:** the one trusted process; every rule (pricing, ownership, roles) lives here.

### Component: MongoDB
- **Responsibility:** live product catalog and image URL references.
- **Reads/Writes:** products CRUD from FastAPI only.
- **Communicates with:** FastAPI (PyMongo). **Not with:** PostgreSQL, Elasticsearch, frontend.
- **Why it exists:** documents with per-product nested structure (`attributes`, `variants`) don't fit a rigid relational schema.

### Component: PostgreSQL
- **Responsibility:** authoritative users, orders, order items — money, statuses, ownership.
- **Reads/Writes:** FastAPI request path + Celery worker (read) + worker bookkeeping write.
- **Communicates with:** FastAPI, Celery worker. **Not with:** MongoDB, frontend.
- **Why it exists:** ACID multi-row writes with CHECK/FK constraints; the only place order facts are guaranteed.

### Component: RabbitMQ
- **Responsibility:** durable transport of sync tasks (`orders_sync` queue; management UI :15672).
- **Reads/Writes:** messages published by FastAPI via Celery `send_task`; consumed by the worker.
- **Communicates with:** FastAPI (publish), Celery (consume), health endpoint (Kombu ping).
- **Does NOT carry:** order contents — only `order_id` + `reason`.
- **Why it exists:** decouples "the order is durable" from "the order is searchable".

### Component: Celery worker (`celery-worker`)
- **Responsibility:** turn task messages into Elasticsearch documents.
- **Reads:** PostgreSQL. **Writes:** Elasticsearch, `orders.search_indexed_at`.
- **Communicates with:** RabbitMQ, PostgreSQL, Elasticsearch. **Not with:** MongoDB, HTTP clients.
- **Why it exists:** retries, time limits, concurrency and crash-resilience for indexing work.

### Component: Elasticsearch
- **Responsibility:** searchable/analyzable projection of orders.
- **Reads/Writes:** written only by the worker (and `scripts/reindex_orders.py`); read only by `/api/search/orders`.
- **Communicates with:** Celery worker (write), FastAPI (read).
- **Why it exists:** full-text relevance + aggregations that neither relational nor document stores offer cheaply.

### Component: Nginx (`frontend/nginx.conf`)
- **Responsibility:** serve the built SPA, `try_files … /index.html` fallback, proxy `/api/` and `/uploads/` to `backend:8000`, cache `/assets/`.
- **Why it exists:** production hosting without a Node process; same-origin API in prod.

### Component: Docker Compose (`docker-compose.yml`)
- **Responsibility:** define, wire and health-check 9 services + named volumes; inject in-network hostnames.
- **Why it exists:** one command produces the entire polyglot environment reproducibly.

---

# PART 8 — Complete Data Flows

**Level 8: what happens during every important user action.**

Legend for the steps used below: **① UI → ② component → ③ store → ④ API request → ⑤ FastAPI
route → ⑥ validation → ⑦ service → ⑧ database → ⑨ queue → ⑩ response → ⑪ UI update.**
Steps that don't apply to a flow are omitted.

## FLOW 1 — Customer opens the storefront

1. **UI:** browser navigates to `/` (Vite :5173 dev, Nginx :8080 prod).
2. **Router:** `router/index.js` matches `path: '/' → StorefrontLayout` with child
   `StorefrontView`; `scrollBehavior` handles restoration.
3. **Layout:** `StorefrontLayout.vue` renders announce bar → header (brand, nav, compact search,
   account, orange **Cart** button) → `<router-view>` → footer → `CartDrawer`. It hydrates
   `searchInput` from `route.query.q`.
4. **View:** `StorefrontView.vue` `onMounted`-style watchers call
   `async function load()` → `listProducts(params)` and `loadFacets()` → `getProductFacets()`.
5. **API:** `GET /api/products?visibility=active&page=1&limit=12&sort=newest` via `api/client.js`
   (adds `Authorization` if a token exists).
6. **Route:** `backend/app/api/products.py::list_products` (Query validation: `page ≥ 1`,
   `limit 1..100`, `sort ∈ newest|title_asc|price_asc|price_desc`).
7. **Service:** `product_service.list_products()` → `product_repo.list_products()` builds a
   Mongo filter (`active: True` for `visibility=active`), sort from `SORT_OPTIONS`, skip/limit.
8. **Database:** MongoDB `catalog.products` with indexes on `sku` (unique), `category`, `active`,
   `created_at`.
9. **Response:** `ProductListResponse { items, page, limit, pages, total }` — each doc normalized
   by `_to_response()` (sets `id` string, defaults for `description/tags/attributes/variants/
   active/image_url`).
10. **UI:** `ProductGrid` renders `ProductCard`s; `HeroSection` separately calls
    `listProducts({ limit: 5, sort: 'newest', visibility: 'active' })` and shows skeleton →
    hero content or the fallback panel ("The catalog is loading").
11. **Also:** `CategorySection` and `TagMarquee` render categories/tags; facets come from
    `GET /api/products/facets` (MongoDB aggregation counting `category` and `tags`).

## FLOW 2 — Customer searches for a product

1. **UI:** typing in the header's single search input (`searchInput` ref).
2. **Component:** `StorefrontLayout.vue` `watch(searchInput, …)` → `syncSearch` (debounced
   260 ms via `utils/debounce`) → `router.replace({ query: { q } })`, dropping `page`.
   Pressing `/` or `⌘/Ctrl+K` focuses the input (`onKeydown`, skipped while typing in a field).
3. **Router:** same route, query change only — `scrollBehavior` returns `false` for same-path
   filter queries so the page doesn't jump; the layout's `watch(() => route.query.q, …)` then
   scrolls to `#products-section`.
4. **View:** `StorefrontView` watches `route.query.q` → `load()` sends `q` to
   `GET /api/products?q=…` (case-insensitive regex over title/description/sku/tags —
   `product_repo.WHAT_WHERE`/`_text_filter`).
5. **Route → service → MongoDB:** as Flow 1, with the text predicate added.
6. **UI:** cards re-render; empty results show an empty state with `resetFilters()` /
   `clearQuery('q')`.
7. **Note:** this is **product** search against **MongoDB**. The admin's *order* search
  (Flow 8) is a different endpoint backed by Elasticsearch.

## FLOW 3 — Customer selects a category / tag

1. **UI:** `ProductFilters` `@change` → `onCategoryChange(value)` → `pushQuery({ category: value })`
   (or footer link `goCategory('peripherals')` in the layout).
2. **Router:** `router.replace/push` with `query.category`; `router/index.js`
   `scrollBehavior` returns `false` when only query changed on the same path, else scrolls.
3. **View:** `watch(routeCategory, …)` resets page to 1, `load()` sends `category=…`.
4. **MongoDB:** equality match on `category` (index `ix_products_category`).
5. **Tags:** `TagPill` click runs the *global* search — it sets `?q=<tag>` (a tag is a search
   term, not a separate filter mode); `TagMarquee` pauses its RTL marquee on hover/touch.
6. **UI:** grid updates; a "clear" affordance removes the query key (`clearQuery`).

## FLOW 4 — Customer adds a product to the cart

1. **UI:** **ADD TO CART** inside `ProductCard` → `onAdd()`.
2. **Component:** `ProductCard.vue` calls `props.onAdd(product)`; the parent
   (`ProductGrid` ← `StorefrontView.addToCart(product)`) does
   `cart.add(product)` and `toast.success(...)`.
3. **Store:** `stores/cart.js` `add(product, quantity = 1)` stores
   `{ id, sku, title, price, category, image_url, quantity }` keyed by product id — a **client
   snapshot**; repeat adds merge into the same line; quantity clamped 1..100.
4. **No API call happens.** *(Implementation fact: `stores/cart.js` imports nothing but Pinia.)*
5. **UI:** the card flips to its "added" state (checkmark, `secondary` variant, disabled) and the
   header cart badge shows `cart.itemCount`.

## FLOW 5 — Customer checks out

1. **UI:** cart drawer **Checkout** → `goToCheckout()` → `router.push({ name: 'checkout' })`
   (route meta `requiresAuth: true` → guard redirects to `/login?redirect=/checkout`).
2. **View:** `CheckoutView.vue` renders `CheckoutLineItems` + `OrderSummaryCard`;
   `watch(cartKey, loadPrices, { immediate: true })` → `Promise.allSettled(ids.map(getProduct))`
   re-reads **live** prices and flags unavailable products (`unavailableTitles`).
3. **Store:** `useCartStore` lines + `useAuthStore` (the user id comes from the session; the
   request body may omit `user_id` — the API takes it from auth when present).
4. **UI:** pressing place → `placeOrder()`:

```js
// frontend/src/views/CheckoutView.vue:215-223
const order = await createOrder({
  items: cart.lines.map((line) => ({
    product_id: line.id,
    quantity: line.quantity,
  })),
})
placedOrder.value = order
cart.clear()
toast.success(`Order ${order.order_number} placed — ${formatCurrency(order.total_amount)}.`)
```

5. **API:** `POST /api/orders` with **no price/total fields** (`OrderCreate` has only `user_id?`
   and `items`).
6–9. See FLOW 6.
10. **Response:** `OrderCreateResponse` = the order + `sync` block
    (`{ enqueued, task_id, queue, error }`).
11. **UI:** `OrderSuccessPanel` shows order number/total; cart is cleared; toast fires. On error,
    `placeError` renders an `AppAlert` and the cart is untouched.

## FLOW 6 — Order is inserted into PostgreSQL

Handled entirely inside `backend/app/services/order_service.py::create_order` (full code in
[PART 10](#part-10--transactional-consistency)):

1. `resolve_cart(payload.items)` → `merge_duplicate_lines` → `product_repo.get_products_by_ids`
   (**MongoDB read**) → validate exists / `active` / price > 0 → `ResolvedLine` + `Decimal` total.
2. `session.begin()` → `INSERT orders` (temporary `TMP-…` number) → `flush()` →
   `order.order_number = f"ORD-{order.id:06d}"` → `INSERT order_items` × N → `flush()`
   (CHECK constraints run) → `commit()`.
3. Any exception → `rollback()` → `OrderPersistenceError` (HTTP 500 envelope,
   `code="order_persistence_failed"`), message: *"No data was written"*.
4. Build `OrderResponse` **while the session is still open**, `session.close()` in `finally`.

## FLOW 7 — Order synchronization to Elasticsearch

1. `create_order` (or `update_order_status`) calls
   `sync_service.publish_order_sync(order_id, reason)` — **after** commit.
2. `publish_order_sync` uses `celery_app.send_task(settings.sync_task_name, kwargs={order_id,
   reason}, queue="orders_sync")`; returns `SyncInfo(enqueued=True, task_id=…, queue=…)`.
   If `settings.celery_task_always_eager` is set (tests), it runs inline (`_run_inline`).
   If publishing raises → `SyncInfo(enqueued=False, error=…)` — **never** a rollback.
3. RabbitMQ holds the message on `orders_sync`.
4. `celery-worker` (`celery -A app.tasks.celery_app worker --concurrency=2`) consumes it.
5. `sync_order_document(order_id, reason)` → `order_repo.get_order` (**PostgreSQL read**) → if
   missing: `{"status": "skipped"}` → else `build_order_document(order)` → `ensure_index()` →
   `index_order_document(doc)` (upsert `_id = order_id`).
6. On Elasticsearch error → `self.retry()` with backoff (5 attempts max).
7. Best-effort `_record_indexed_at()` sets `orders.search_indexed_at`.

## FLOW 8 — Admin searches orders

1. **UI:** `/admin/search` → `AdminSearchView.vue`; typing/filters are debounced.
2. **Store/state:** local refs `term`, `statuses`, `dateFrom/dateTo`, `minPrice/maxPrice`, `page`.
3. **Payload build** (`AdminSearchView.refresh()`):

```js
// frontend/src/views/AdminSearchView.vue:155-162
const payload = { page: page.value, limit: PAGE_SIZE }
if (term) payload.query = term
if (statuses.value.length) payload.status = [...statuses.value]
if (dateFrom.value) payload.date_from = dateFrom.value
if (dateTo.value) payload.date_to = dateTo.value
if (minPrice.value !== '') payload.min_price = Number(minPrice.value)
if (maxPrice.value !== '') payload.max_price = Number(maxPrice.value)
```

4. **API:** `POST /api/search/orders` (`api/search.js::searchOrders`).
5. **Route:** `api/search.py::search_orders` — `Depends(get_current_user)` **and**
   `Depends(require_admin)`.
6. **Validation:** `SearchRequest` (status ∈ 3 values, non-inverted date/price ranges,
   `page 1..10000`, `limit 1..100`).
7. **Service:** `search_service.search_orders()` → `search_repo.search_orders_with_index()`;
   ES `400` → `AppError(search_query_invalid)`; other failures → `DependencyUnavailableError`
  (`search_unavailable`, HTTP 503).
8. **Database:** single Elasticsearch query — `multi_match` on
   `customer.name^3, customer.email, order_number` + nested `multi_match items.title^2`, `terms`
   status filter, `range` on `order_date`/`total_amount`, aggregations `sum(total_amount)` and
   `terms status` (with `missing: 0` for all three statuses).
9. **Response:** `SearchResponse { results, total, page, limit, pages, took_ms, aggregations }`.
10. **UI:** `SearchKpis` (revenue + per-status counts from `aggregations`), `ResultsTable`
   (desktop) / `ResultsCardList` (mobile), `AppPagination`.

## FLOW 9 — Admin opens order details

1. **UI:** `ResultsTable` row click → `openOrder(orderId)` → `router.push({ name:
   'order-details', params: { id } })`.
2. **View:** `OrderDetailsView.vue` `load()` → `getOrder(id)` → **`GET /api/orders/{id}`**
  (PostgreSQL — *never* Elasticsearch).
3. **UI:** header (order number, status `AppBadge`, dates, customer), `CheckoutLineItems`-style
   item table showing **snapshot** titles/prices, `SearchSyncIndicator` driven by
   `search_indexed_at`, and `OrderStatusControl` for admins.

## FLOW 10 — Admin changes order status

1. **UI:** `OrderStatusControl` select → `onStatusChange(value)` in `OrderDetailsView`.
2. **API:** `PATCH /api/orders/{id}/status` body `{ status: PENDING|PROCESSING|SHIPPED }`
   (`api/orders.js::updateOrderStatus`).
3. **Route:** admin-only dependency.
4. **Service:** `order_service.update_order_status()` — explicit `begin → UPDATE → commit`,
   `rollback` on failure; only if `previous != status` does it publish the sync task
   (otherwise it reports `queue: "in-process"` with `enqueued: true` and no task).
5. **Response:** `StatusUpdateResponse` (order + `sync`).
6. **UI:** toast + refreshed badge; `SearchSyncIndicator` may show "pending re-index" until the
   worker writes `search_indexed_at`.

## FLOW 11 — Status change reaches Elasticsearch

Identical pipeline to FLOW 7 with `reason="status_update"`: the worker **rebuilds the whole
document** from PostgreSQL (no partial patch), so the ES document converges to the new status.
If it fails, retries apply; the PG status remains correct regardless.

## FLOW 12 — Admin edits a product

1. **UI:** `/admin/catalog` → `CatalogAdminView` → `openEdit(product)` → `ProductFormModal`
   (`:product` prop, `:open`).
2. **Component:** modal validates with `utils/validation` (`validateSku`, `validateTitle`,
   `validatePrice`, `validateCategory`, `validateTags`, `validateVariants`,
   `validateAttributeKeys`) and maps server field errors through `fieldErrorsFrom`.
3. **API:** `PATCH /api/products/{id}` (`updateProduct`), preceded (if needed) by image
   upload/remove calls (FLOW 13).
4. **Route:** `require_admin` → `product_service.update_product` → `product_repo.update_product`
   (`$set` + `updated_at`), `ConflictError` on duplicate SKU.
5. **Response:** `ProductResponse` with normalized fields.
6. **UI:** `onSaved(product, mode)` refreshes the row; toasts report success/failure.

## FLOW 13 — Admin uploads a product image

1. **UI:** `ProductFormModal` image area → `<input type="file" accept=".jpg,.jpeg,.png,.webp,
   .svg,image/jpeg,image/png,image/webp,image/svg+xml">` → `onFileSelected` reads the file,
   checks size/format client-side, shows a **preview** via `URL.createObjectURL` +
   `resolveImageUrl()`.
2. **API:** `uploadProductImage(id, file)` → `FormData` →
   `POST /api/products/{id}/image` (multipart).
3. **Route:** `async def upload_product_image(...)` (`backend/app/api/products.py`), admin-only:
   - `_ensure_upload_dir()` → `uploads/products/` under `settings.uploads_path` (default
     `/app/uploads`, i.e. the `uploads_data` volume),
   - 404 if the product doesn't exist,
   - `_validate_image_file()` → content type ∈ `{image/jpeg, image/png, image/webp,
     image/svg+xml}`,
   - `_generate_safe_filename()` → `uuid4().hex + allowed extension` (never trusts the client name),
   - `_save_upload_file()` → rejects > **5 MB**, writes bytes,
   - deletes the previous stored file (`_stored_image_path` + containment check),
   - `product_repo.update_product(id, {"image_url": "/uploads/products/<file>"})`,
   - if the Mongo update fails: **rolls back by deleting the new file** and raises 404.
4. **Response:** full `ProductResponse`.
5. **UI:** preview swaps to the server URL, `saved` event refreshes the table row
  (`CatalogTable` Image column shows `ProductThumb`).

## FLOW 14 — Customer sees the uploaded image

1. `ProductResponse.image_url` = `/uploads/products/ab12….webp`.
2. `ProductThumb` computes `imageUrl = resolveImageUrl(product.image_url)`:
   absolute/`data:`/`blob:` pass through; `/uploads/…` gets `API_BASE_URL` prefixed **only if**
   an origin is configured; other relative paths (e.g. `/products/DESK-001.svg` shipped with the
   bundle) stay relative.
3. `<img loading="lazy" decoding="async" @load @error>` → `thumb--loading` / `thumb--error`
   states; on error (or no URL) the branded placeholder with a deterministic monogram/pattern is
   shown.
4. **Request path:** dev → Vite proxy `/uploads → http://localhost:8000`; prod → Nginx
   `location /uploads/ { proxy_pass http://backend:8000; }`; backend → FastAPI
   `StaticFiles` mount at `/uploads`.
5. **Persistence:** the file lives in the `uploads_data` named volume → survives container
   restarts; the **URL** lives in MongoDB `image_url`.

---

# PART 9 — Database Architecture

**Level 11: each store on its own.**

## 9.1 PostgreSQL — transactional source of truth

### Tables and columns

**`users`** (`backend/app/models/postgres.py:27-51`)

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | Integer | PK |
| `name` | String(120) | NOT NULL |
| `email` | String(255) | NOT NULL, UNIQUE, indexed |
| `password_hash` | String(255) | NOT NULL, default `""` |
| `role` | String(20) | NOT NULL, default `CUSTOMER`, CHECK ∈ (`CUSTOMER`,`ADMIN`) |
| `created_at` | DateTime(tz) | server default `now()` |

**`orders`** (same file, lines 54+)

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | Integer | PK |
| `order_number` | String(32) | UNIQUE, indexed (`ORD-000123`) |
| `user_id` | Integer | FK → `users.id` |
| `status` | String(20) | CHECK ∈ (`PENDING`,`PROCESSING`,`SHIPPED`), indexed |
| `order_date` | DateTime(tz) | indexed |
| `total_amount` | Numeric(12,2) | exact money |
| `created_at` / `updated_at` | DateTime(tz) | |
| `search_indexed_at` | DateTime(tz) nullable | written by the worker (bookkeeping) |

**`order_items`**

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | Integer | PK |
| `order_id` | Integer | FK → `orders.id` (ON DELETE CASCADE), indexed |
| `product_id` | String(64) | the MongoDB ObjectId **as text** (no FK — cross-store) |
| `title` | String(200) | **snapshot** |
| `quantity` | Integer | CHECK > 0 (and ≤ 100 enforced in service/schema) |
| `unit_price` | Numeric(12,2) | **snapshot**, CHECK > 0 |
| `line_total` | Numeric(12,2) | computed |

Indexes (README §4, verified against `models/postgres.py` `Index(...)` entries):
`orders(status)`, `orders(order_date)`, `orders(user_id)`, `orders(order_number)`,
`order_items(order_id)`.

### Conceptual ER diagram

```
users
  │ 1
  │
  │ N
  ▼
orders ────── (order_number UNIQUE, status CHECK, total_amount numeric)
  │ 1
  │
  │ N
  ▼
order_items ── (title/unit_price snapshots, quantity/unit_price CHECKs)

order_items.product_id ──▶ MongoDB products._id   (text reference, no FK)
```

### Transaction boundaries

- Order placement: one explicit transaction covering `orders` + **all** `order_items`
  ([PART 10](#part-10--transactional-consistency)).
- Status change: its own `begin → UPDATE → commit`.
- Worker bookkeeping: its own small transaction (`mark_search_indexed`), wrapped so failure never
  fails the indexing task.
- Session handling: `SessionLocal()` created per use, closed in `finally`
  (`order_service.get_order`, `create_order`, …); FastAPI request-scoped sessions come from
  `get_db_session()` (`core/database.py:35-41`).

### Order lifecycle

`PENDING → PROCESSING → SHIPPED` — the only three values (schema `OrderStatus` literal, model
CHECK constraint, ES mapping `keyword`). There is **no** cancelled/refunded status in the code.

## 9.2 MongoDB — product catalog

### Document structure (fields confirmed by `ProductBase`/`ProductResponse`)

```jsonc
{
  "_id": ObjectId("…"),
  "sku": "WM-001",                  // pattern ^[A-Za-z0-9][A-Za-z0-9\-_]*$, unique index
  "title": "Wireless Mouse",        // 2..200 chars
  "description": "…",               // ≤ 4000 chars, default ""
  "price": 50.16,                   // > 0, ≤ 1_000_000 (server rounds to 2 dp)
  "category": "peripherals",        // normalized lowercase; validated against 4 values on write
  "tags": ["wireless", "office"],   // ≤ 30, normalized lowercase, deduped
  "attributes": { "color": "black", "dpi": 1600 },   // free-form nested map
  "variants": [{ "sku": "WM-001-BLK", "color": "black", "stock": 12 }],  // ≤ 20, nested
  "active": true,                   // soft-delete flag
  "image_url": "/uploads/products/ab12.webp" | "/products/ORG-001.svg" | null,
  "created_at": ISODate(...),
  "updated_at": ISODate(...)
}
```

The API always exposes `id` (string) instead of `_id` (`product_service._to_response`).

Indexes created by `product_repo.ensure_indexes()`:
`sku` **unique**, `category`, `active`, `created_at DESC`.

### Why MongoDB fits

Catalog entries differ in shape (some have variants, some don't), filtering is document-shaped
(`tags` array containment, `$regex` text, category equality), and there are no cross-document
transactional requirements. *(Label: **Inference** for the "why"; the structure is fact.)*

### Active / inactive products

`DELETE /api/products/{id}` sets `active=false` (soft delete) so historical orders keep a
meaningful product; the storefront query defaults to `visibility=active`, and ordering an
inactive product returns **422 `inactive_product`** (`order_service.resolve_cart`).

### Why orders must not depend on live Mongo data

Because everything money-related is copied into `order_items` at purchase time and the ES
document is rebuilt from PostgreSQL — see [PART 2 §2.2](#22-live-product-data-vs-historical-order-snapshot-data)
and [PART 36](#part-36--snapshot-semantics).

## 9.3 Elasticsearch — order search projection

### The document (`build_order_document`, `repositories/elasticsearch/document.py`)

```jsonc
{
  "order_id": 64,                       // also used as the document _id
  "order_number": "ORD-000064",
  "status": "PENDING",
  "order_date": "2026-…T…+00:00",       // ISO string
  "updated_at": "…",
  "total_amount": 229.00,               // double, 2 dp
  "customer": { "id": 1, "name": "John Doe", "email": "john.doe@example.com" },
  "items": [
    { "product_id": "…", "title": "…", "quantity": 1,
      "unit_price": 229.00, "line_total": 229.00 }
  ]
}
```

### Mapping (`dynamic: strict` — `repositories/elasticsearch/mappings.py`)

| Field | Type | Purpose |
| --- | --- | --- |
| `order_id` | `long` | identity |
| `order_number`, `status` | `keyword` | exact match, `terms` facets |
| `order_date`, `updated_at` | `date` (`strict_date_optional_time\|\|epoch_millis`) | range filters |
| `total_amount` | `double` | range filter + `sum` aggregation |
| `customer.id` | `long` | — |
| `customer.name`, `customer.email` | **`search_as_you_type`** + `.keyword` | prefix/infix search, sorting/aggregation |
| `customer.email`… `order_number` (text side) | see below | — |
| `items` | **`nested`** | item fields stay scoped to one line |
| `items.title` | `text` + `.keyword` | full-text inside line items |
| `items.unit_price`, `items.line_total`, `items.quantity` | numeric | — |

Index settings: `number_of_shards: 1`, `number_of_replicas: 0` (single-node demo → instant
green), `dynamic: strict` so unexpected fields are rejected rather than silently mapped.

**search_as_you_type vs bool_prefix:** the mapping declares `search_as_you_type`
(Implementation fact); the query in `search_repo.build_search_query()` uses **`multi_match`**
(with `bool_prefix`-style behaviour only where the type supports it — the verified query body
uses `multi_match` over `TEXT_FIELDS` and a nested `multi_match` over `NESTED_TEXT_FIELDS`).
*Not confirmed from the available source:* an explicit `bool_prefix` query block — none was found
in `search_repo.py`.

### Filters, facets, aggregations (all in one request)

- `terms` on `status` (when any status selected)
- `range` on `order_date` (inclusive day bounds, UTC)
- `range` on `total_amount`
- aggregations: `revenue = sum(total_amount)` over the **filtered** set, and
  `status_counts = terms status` with `missing: 0` for all three statuses
  (so KPIs always describe the current filter set)
- pagination `from/size`, sort `order_date DESC`

### Why a projection, not a source of truth

Covered in [PART 5 §5.2](#52-why-elasticsearch-must-not-be-the-source-of-truth-for-orders);
the recovery path is `python -m scripts.reindex_orders`.

---

# PART 10 — Transactional Consistency

**Level 10: exactly what checkout guarantees, and what it does not.**

## 10.1 The sequence (README §6 matches the code)

```
resolve cart against MongoDB      (validate products, re-read live prices)
session.begin()                                       ← BEGIN
INSERT orders      + session.flush()                  ← order.id available
order_number = 'ORD-{id:06d}'                         ← second flush
INSERT order_items × N + session.flush()              ← CHECK constraints run here
session.commit()                                      ← COMMIT (durable)
  └─ on ANY exception: session.rollback()             ← ROLLBACK, zero rows
      → HTTP 500 { code: "order_persistence_failed" }
only after COMMIT: publish sync task to RabbitMQ
```

## 10.2 The real code

```python
# backend/app/services/order_service.py:166-231 (abridged, structure preserved)
session = SessionLocal()
try:
    try:
        session.begin()                              # BEGIN
        user = order_repo.get_user(session, payload.user_id)
        if user is None:
            raise NotFoundError(..., code="user_not_found", ...)
        order = Order(order_number=_temporary_order_number(), user=user,
                      order_date=now, status="PENDING", total_amount=total,
                      created_at=now, updated_at=now)
        session.add(order)
        session.flush()                              # INSERT orders -> order.id
        order.order_number = f"ORD-{order.id:06d}"   # human readable number
        for line in lines:
            session.add(OrderItem(order=order, product_id=line.product_id,
                                  title=line.title,           # snapshot of MongoDB title
                                  quantity=line.quantity,
                                  unit_price=line.unit_price))  # snapshot of MongoDB price
        session.flush()                              # INSERT order_items (CHECKs)
        session.commit()                             # COMMIT — durable
    except Exception as exc:
        session.rollback()                           # ROLLBACK — no partial order
        if isinstance(exc, AppError):
            raise
        raise OrderPersistenceError(
            "The order could not be saved. No data was written — please try again."
        ) from exc
    response = OrderResponse.model_validate(order, from_attributes=True)
finally:
    session.close()

# 3) Only now (after COMMIT) is the sync task handed to RabbitMQ.
sync = sync_service.publish_order_sync(order.id, reason="order_created")
return OrderCreateResponse(**response.model_dump(), sync=sync)
```

**How to read it:** the inner `try` is the transaction; `flush()` forces SQL now so CHECK
constraints and NOT NULLs fire *before* commit; the `Rollback` path guarantees atomicity; the
publish is deliberately *outside* both blocks.

## 10.3 Failure-mode answers (actual behaviour, verified)

| Scenario | Actual behaviour | Evidence |
| --- | --- | --- |
| Order row inserts but an item insert fails | `rollback()` removes the order too — **zero rows written**; HTTP 500 `order_persistence_failed` | `tests/integration/test_orders_api.py:182 test_transaction_rolls_back_completely_when_an_item_insert_fails` |
| PostgreSQL itself down | SQLAlchemy raises → same rollback path → 500 envelope (503 reserved for `DependencyUnavailableError`) | `core/errors.py`, `order_service` |
| Commit succeeds, **publish fails** (RabbitMQ down) | Order stays committed; response carries `sync.enqueued=false` + error string; **no retry of publishing here** | `sync_service.publish_order_sync` try/except; test `test_publish_failure_never_rolls_back_a_committed_order` |
| Celery worker offline | Message waits in `orders_sync` (durable queue); order is safe; ES lags until a worker returns | compose `celery-worker`, `README` §8 |
| Elasticsearch down at task time | Task retries **5× with exponential backoff** (10 → 20 → 40 → 80 → capped 120 s), then gives up; PostgreSQL unaffected | `settings.celery_max_retries=5`, `celery_retry_backoff=10`, `celery_retry_backoff_max=120`; tests `test_task_retries_with_backoff_when_elasticsearch_fails`, `test_task_gives_up_after_max_retries` |
| Process dies after COMMIT, before publish | Order exists, **no message exists** — documented as "no transactional outbox"; recovery = reindex script or a later status update | README §17.3; `sync.enqueued:false` reporting |
| Duplicate task delivery | Same `_id = order_id` → **upsert**, no duplicate documents (at-least-once + idempotent write) | `orders_repo.index_order_document`, `test_sync_task_is_idempotent` |
| Status PATCH fails | Its own rollback; published sync only when the status actually changed | `order_service.update_order_status` |

**Retries: what exists and what does not**

- **Exists:** Celery task retries with backoff (worker side); `broker_connection_retry_on_startup`
  and `confirm_publish: True` (publish confirmation); `task_acks_late` +
  `task_reject_on_worker_lost` (redelivery if a worker dies mid-task).
- **Does not exist:** an application-level publish-retry loop, a transactional outbox, CDC,
  message deduplication keys, or a reconciliation poller. (README §8/§17 state this explicitly,
  and no code implements them.)

---

# PART 11 — RabbitMQ + Celery

**Level 13: the synchronization system end to end.**

## 11.1 Vocabulary

- **RabbitMQ** — a message broker: a durable post office between processes. Producers publish
  messages to a *queue*; consumers receive them later, even if they were down when the message
  was sent.
- **Celery** — a Python distributed task queue: you call `send_task("name", kwargs=…)` and a
  separate *worker* process executes the named function, with retries, time limits and
  concurrency control.

**Why both:** RabbitMQ stores/hands off; Celery provides the worker runtime, task registration,
retry policy and configuration. In this project FastAPI uses Celery only as a *client*
(`send_task`), and the `celery-worker` service is the consumer.

## 11.2 Producer side

```python
# backend/app/services/sync_service.py:36-42
result = celery_app.send_task(
    settings.sync_task_name,                       # "app.tasks.elasticsearch_tasks.sync_order_to_elasticsearch"
    kwargs={"order_id": order_id, "reason": reason},
    queue=settings.celery_task_default_queue,      # "orders_sync"
)
```

- Called **only after COMMIT** (order creation) or after a committed status change.
- Failure → `SyncInfo(enqueued=False, error=…)` returned to the caller; the committed work is
  never undone.
- In eager/test mode (`celery_task_always_eager`) `_run_inline()` executes the function in-process
  and reports `queue = "in-process"`.

## 11.3 The queue and message

- Queue name: `orders_sync` (`Settings.celery_task_default_queue`).
- Serialization: **JSON** (`task_serializer="json"`, `accept_content=["json"]`, `timezone="UTC"`).
- Payload: only `{"order_id": <int>, "reason": "order_created" | "status_update"}`.
- Transport options: `{"confirm_publish": True, "visibility_timeout": 3600}` — a message whose
  consumer never acknowledges becomes available again after an hour.

## 11.4 Worker side

```python
# backend/app/tasks/celery_app.py:42-45 (reliability block)
task_acks_late=True,
task_reject_on_worker_lost=True,
worker_prefetch_multiplier=1,
task_time_limit=120,
task_soft_time_limit=90,
```

- `celery_app.conf.imports = ["app.tasks.elasticsearch_tasks"]` registers the task at boot.
- Compose command: `celery -A app.tasks.celery_app worker --loglevel=INFO --concurrency=2`.
- No result backend: `backend=None  # results are not needed: the DB + ES are the state`.

## 11.5 The task

```python
# backend/app/tasks/elasticsearch_tasks.py — core behaviour
TASK_NAME = "app.tasks.elasticsearch_tasks.sync_order_to_elasticsearch"

def sync_document(order_id, reason):        # synchronous core, reused by the reindex script
    order = order_repo.get_order(session, order_id)
    if order is None:
        return {"status": "skipped", ...}    # deleted order → no-op
    document = build_order_document(order)   # rebuilt from PostgreSQL every time
    ensure_index()                           # idempotent index/mapping creation
    index_order_document(document)           # upsert with _id = order_id
    _record_indexed_at(order_id)             # best-effort bookkeeping, never fails the task

@celery_app.task(bind=True, max_retries=settings.celery_max_retries, ...)
def sync_order_to_elasticsearch(self, order_id, reason="unknown"):
    ...  # on ES failure: self.retry(countdown=backoff) up to 5 times
```

Key properties (each has a test):

| Property | Meaning | Test |
| --- | --- | --- |
| **Idempotent** | Whole document rebuilt + upsert by `_id`; running twice changes nothing | `test_sync_task_is_idempotent` |
| **Rebuild, not patch** | Always reads PostgreSQL fresh → ES can never hold data newer-different from PG | `test_sync_task_creates_the_document_from_postgresql` |
| **Snapshot-faithful** | Uses PG `title`/`unit_price`, not live Mongo | `test_sync_uses_postgres_snapshots_not_live_mongo_titles` |
| **No-op for missing orders** | `{"status": "skipped"}` | `test_sync_task_skips_orders_missing_from_postgres` |
| **Retries with backoff** | 10 s → 20 → 40 → 80 → ≤120 s, then gives up | `test_task_retries_with_backoff…`, `…gives_up_after_max_retries` |
| **Registered name stable** | `TASK_NAME` string asserted | `test_sync_task_is_registered_with_the_expected_name` |
| **Exactly one doc per PG order** | Parity assertion | `test_elasticsearch_holds_exactly_one_document_per_postgres_order` |

## 11.6 What happens when things go wrong

| Condition | Behaviour |
| --- | --- |
| Worker offline | Messages accumulate in `orders_sync`; nothing is lost (durable queue + acks_late). Search lags; order data does not. |
| Elasticsearch unavailable | Retries with backoff, then abandons; `search_indexed_at` stays null (UI shows not-yet-indexed). Reindex later. |
| Message delayed | Harmless: the worker always reads current PostgreSQL state. |
| Task retried / redelivered | Idempotent upsert — duplicates impossible at the document level. |
| Same order indexed twice | Second write overwrites with identical content. |
| RabbitMQ down at publish time | Committed order unaffected; `sync.enqueued=false` in the response. |
| Publish confirmed but worker never sees it | Possible only if the broker loses the queue (not the configured setup) — recovery path is `scripts/reindex_orders.py`. |

**Consistency model (Inference, stated as such):** *read-your-writes for PostgreSQL reads;
eventual consistency for Elasticsearch reads.* The code never claims stronger.

---

# PART 12 — Authentication

**Level 12: login from form to `Authorization` header.**

## 12.1 Authentication vs. authorization

- **Authentication** = *who are you?* → email + password → JWT.
- **Authorization** = *may you do this?* → role check (`ADMIN`) or ownership check (your own order).

## 12.2 The login flow, step by step

1. **UI:** `/login` → `LoginView` → `components/auth/LoginForm.vue`.
2. **Store:** `authStore.login(email, password)`:

```js
// frontend/src/stores/auth.js:25-43
const response = await client.post('/api/auth/login', { email, password })
this.token = response.access_token
this.user = response.user
localStorage.setItem(TOKEN_KEY, this.token)      // 'meridian.auth.token'
localStorage.setItem(USER_KEY, JSON.stringify(this.user))
const redirect = router.currentRoute.value.query.redirect || '/'
await router.push(redirect)
```

3. **Route:** `POST /api/auth/login` → `auth.py::login(payload, db)` →
   `auth_service.authenticate_user(db, email, password)`:

```python
# backend/app/services/auth_service.py:13-22
user = db.query(User).filter(User.email == email).first()
if not user:
    raise NotFoundError("Invalid email or password", code="invalid_credentials")
if not user.password_hash:
    raise UnprocessableError("User has no password set", code="no_password")
if not verify_password(password, user.password_hash):
    raise NotFoundError("Invalid email or password", code="invalid_credentials")
return user
```

4. **Hashing:** `passlib.context.CryptContext(schemes=["bcrypt"])` — `hash_password()` on seed
   writes, `verify_password()` on login. The plaintext never touches the DB or the log.
5. **JWT creation:** `create_access_token({"sub": str(user.id)})` →
   `jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")` with `exp` =
   now + `jwt_access_token_expire_minutes` (default **1440 = 24 h**).
6. **Response:** `LoginResponse { access_token, token_type: "bearer", user: {id,name,email,role} }`.
7. **Storage:** `localStorage` only — **no cookies, no server session** (stateless JWT).
   `POST /api/auth/logout` returns a canned `LogoutResponse`; the client simply deletes the keys.
8. **Request interceptor:** every later call attaches the header:

```js
// frontend/src/api/client.js:36-42
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('meridian.auth.token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

9. **Server validation:** `get_current_user` (FastAPI dependency):
   `HTTPBearer(auto_error=False)` → `jwt.decode(token, secret, "HS256")` → payload `sub` →
   `db.get(User, user_id)` → any failure raises `401` with
   `WWW-Authenticate: Bearer`.
10. **Refresh/restore:** `App.vue` calls `authStore.init()` at boot; the router guard calls
    `fetchMe()` (`GET /api/auth/me`) when a token exists but no user object; an invalid token is
    cleared silently.
11. **Logout:** `authStore.logout()` → `POST /api/auth/logout` (ignored on error) → clears
    storage → `router.push({ name: 'login' })`.

## 12.3 Authorization layers

```python
# backend/app/core/auth.py:106-114
def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Dependency that requires the current user to have ADMIN role."""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin access required")
    return current_user
```

Applied to: catalog `POST/PATCH/DELETE`, image `POST/DELETE`, `PATCH /api/orders/{id}/status`,
`POST /api/search/orders`. **Order ownership** for `GET /api/orders/{id}` is checked in the
route/service against the current user (admins bypass). *(Implementation fact: orders.py
docstring + handler; tests assert customer isolation.)*

**Frontend mirrors, but does not enforce:** `meta.requiresAuth` / `meta.requiresAdmin` in
`router/index.js`, `authStore.isAdmin` for nav links. See [PART 3 §3.2](#32-frontend-authorization-ux-vs-backend-authorization-security).

---

# PART 13 — Frontend Architecture

**Level 9: how the Vue application is put together.**

## 13.1 Architecture tree (actual `frontend/src` contents)

```
frontend/src/
├── main.js                     # createApp → Pinia → router → mount; imports tokens.css + utilities.css
├── App.vue                     # <router-view/> + <ToastHost/>; calls authStore.init()
├── api/
│   ├── client.js               # axios instance, ApiError, interceptors, resolveBaseUrl, API_BASE_URL
│   ├── products.js             # list/facets/get/create/update/delete + image upload/remove
│   ├── orders.js               # createOrder, getOrder, updateOrderStatus
│   ├── search.js               # searchOrders (POST /api/search/orders)
│   ├── users.js                # listUsers (Log In As selector)
│   └── …
├── components/
│   ├── admin/                  # CatalogTable, CatalogCardList, ProductFormModal, TagsInput,
│   │                           # AttributesEditor, VariantsEditor, SearchFilters, SearchKpis,
│   │                           # ResultsTable, ResultsCardList, OrderStatusControl, SearchSyncIndicator
│   ├── auth/                   # LoginForm
│   ├── checkout/               # CheckoutLineItems, OrderSummaryCard, OrderSuccessPanel
│   ├── common/                 # AppAlert, AppBadge, AppCard, AppDrawer, AppIcon, AppModal,
│   │                           # AppPagination, BaseButton, BaseInput, BaseSelect, BaseTextarea,
│   │                           # ConfirmDialog, EmptyState, FormField, KpiCard, LoadingSkeleton,
│   │                           # ProductThumb, StatusBadge, ToastHost
│   └── storefront/             # CartDrawer, CategorySection, HeroSection, ProductCard,
│                               # ProductFilters, ProductGrid, TagMarquee, TagPill
├── layouts/
│   ├── StorefrontLayout.vue    # announce + header/search/cart + footer + CartDrawer
│   └── AdminLayout.vue         # admin shell + nav + guard-friendly chrome
├── router/index.js             # routes, guards, scrollBehavior, document.title
├── stores/                     # auth.js, cart.js, toast.js  (Pinia)
├── styles/                     # tokens.css (design tokens), utilities.css (layout/utilities)
├── utils/                      # currency.js, dates.js, debounce.js, image.js, status.js, validation.js
└── views/                      # StorefrontView, CheckoutView, LoginView,
                                # AdminSearchView, OrderDetailsView, CatalogAdminView
```

## 13.2 How the layers relate

```
main.js → App.vue → router/index.js
                       ├─ StorefrontLayout → StorefrontView → storefront components
                       ├─ AdminLayout      → admin views    → admin components
                       └─ LoginView → LoginForm
All data access:  view/component → stores (Pinia) or api/*.js → api/client.js → FastAPI
All styling:      styles/tokens.css (variables) + styles/utilities.css + scoped styles per SFC
```

**Rules of thumb for this codebase**

- Components receive data via **props** and report upward via **emits** (e.g. `ProductCard`
  `@add`, `ProductFormModal` `@saved`); cross-cutting state lives in **Pinia**.
- Every HTTP call goes through `api/client.js` — no raw `axios`/`fetch` in components.
- Money always goes through `utils/currency.js::formatCurrency` (₹, `en-IN`).
- Images always go through `utils/image.js::resolveImageUrl`.

---

# PART 14 — Frontend Routing

**Level 14: every route, its guard and its data.**

| Route | Component (lazy) | Purpose | Access | Key data / behaviour |
| --- | --- | --- | --- | --- |
| `/login` | `LoginView` (`meta.guest`) | Sign in | guests only (auth users bounce to `/`) | reads `?redirect=` |
| `/` → `StorefrontLayout` → `''` `storefront` | `StorefrontView` | Browse/search catalog | public | reads `?q,category,sort,page` |
| `/checkout` (child) | `CheckoutView` | Place order | `meta.requiresAuth` | cart from Pinia, live prices |
| `/admin` (`requiresAuth` + `requiresAdmin`) → `''` | redirect | — | admin | redirects to `admin-search` |
| `/admin/search` `admin-search` | `AdminSearchView` | ES order search + KPIs | admin | builds `SearchRequest` |
| `/admin/orders/:id` `order-details` | `OrderDetailsView` | Canonical order + status | admin | `GET /api/orders/{id}` (PG) |
| `/admin/catalog` `catalog-admin` | `CatalogAdminView` | Product CRUD + images | admin | MongoDB via API |
| `/:pathMatch(.*)*` | — | catch-all | — | redirects to `storefront` |

## 14.1 Guard logic (real code)

```js
// frontend/src/router/index.js — beforeEach
if (requiresAuth && !authStore.isAuthenticated) {
  return next({ name: 'login', query: { redirect: to.fullPath } })
}
if (requiresAdmin && !authStore.isAdmin) {
  // Non-admin users cannot access admin routes
  return next({ name: 'storefront' })
}
if (isGuest && authStore.isAuthenticated) {
  return next({ name: 'storefront' })
}
next()
```

**Customer order authorization behaviour:** a customer can only reach `/admin/*` if
`isAdmin` — but an *order* is fetched with `GET /api/orders/{id}`, whose server-side ownership
check is the real protection (frontend hiding is UX only).

## 14.2 `scrollBehavior` — why it returns `false`

```js
const isFilterChange =
  to.path === from.path && ['q', 'category', 'sort', 'page'].some((key) => key in to.query)
if (isFilterChange) return false
return { top: 0 }
```

Search/filter changes are query-only navigations; the components themselves run a smooth scroll to
`#products-section`. Letting the router jump to the top would cancel that animation and cause
scroll fighting. Saved positions (`savedPosition`) win for back/forward.

`afterEach` sets `document.title = meta.title + ' · Meridian'`.

---

# PART 15 — Pinia / State Management

**Level 15: what lives in a store, what doesn't.**

## 15.1 `stores/auth.js`

| Kind | Members |
| --- | --- |
| state | `token`, `user`, `loading`, `error` (hydrated from `localStorage`) |
| getters | `isAuthenticated`, `isAdmin` (`role === 'ADMIN'`), `userName`, `userEmail`, `userId` |
| actions | `login(email,password)`, `logout()`, `fetchMe()`, `init()` |
| API | `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout` |
| Used by | router guard, `StorefrontLayout` header, `AdminLayout`, `CheckoutView`, `LoginForm` |
| **Not here** | tokens are read *directly* by `client.js` from `localStorage` (avoid circular imports); no roles list, no permissions matrix |

## 15.2 `stores/cart.js`

```js
// state:  items: Record<id, {id, sku, title, price, category, image_url, quantity}>
// getters: lines, isEmpty, itemCount, subtotal   (subtotal = snapshot subtotal)
// actions: add, setQuantity, increment, decrement, remove, clear
// clamp:   MIN_QTY = 1, MAX_QTY = 100
```

- **Keyed by product id**, so repeat adds merge into one line (test: *"merges repeat adds into
  the same line instead of duplicating it"*).
- Stores a **snapshot** of title/price at add time; the server re-prices at checkout anyway.
- **No `persist` plugin, no `localStorage`.** *(Implementation fact: file imports only Pinia; no
  `watch(..., {deep})` writing to storage.)* → **cart survives navigation and store
  reactivity, but is cleared by a browser refresh.** Adding persistence would break
  `frontend/tests/cart.spec.js` expectations that start from a clean store — that is why it was
  deliberately not added during the UI rebuild.

## 15.3 `stores/toast.js`

Queue of `{id, type, message, timeout}` capped at 5 entries; `success/error/info/warning/
dismiss`; rendered by `ToastHost`. Used by views for feedback instead of `alert()`/`confirm()`
(there are none in the app).

**What should NOT go in stores:** server-derived data that belongs to a single screen (search
results, product lists) stays in the view as local refs — keeps re-fetching explicit and avoids
stale-cache bugs.

---

# PART 16 — API Client

**Level 16: one door to the backend.**

```js
// frontend/src/api/client.js
export function resolveBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (configured === '') return ''            // '' → relative /api (vite/nginx proxy)
  return (configured || 'http://localhost:8000').replace(/\/+$/, '')
}
export const API_BASE_URL = resolveBaseUrl()

const client = axios.create({
  baseURL: resolveBaseUrl(),
  timeout: 20000,
  paramsSerializer: { indexes: null },        // ?tags=a&tags=b  (FastAPI repeated keys)
})
```

| Concern | Where | Behaviour |
| --- | --- | --- |
| Base URL | `resolveBaseUrl()` | absolute `VITE_API_BASE_URL`, default `http://localhost:8000`; empty string → relative |
| Auth header | request interceptor | `Bearer <meridian.auth.token>` when present |
| Error normalization | `toApiError(error)` | reads the backend envelope `{error:{code,message,details}}` → `ApiError { message, code, status, details }` |
| Field errors | `fieldErrorsFrom(err)` | maps `details.fields`-style payloads onto form fields (`ProductFormModal`) |
| Human message | `messageFrom(error)` | fallback text for toasts/alerts |
| Timeout | 20 s | surfaces as a normal `ApiError` |
| Modules | `api/products.js`, `orders.js`, `search.js`, `users.js` | one function per endpoint; JSDoc'd payloads |

**Why centralized:** token injection, error shape, base URL and timeouts are decided in exactly
one place; swapping to a proxy (`VITE_API_BASE_URL=""`) requires no component changes. Image URLs
also depend on it — `utils/image.js` imports `API_BASE_URL` to prefix `/uploads/...`.

---

# PART 17 — Storefront

**Level 17: the landing page, top to bottom.**

All sections share **one content container** (`.container` / `.container-admin`, max
`--content-max: 1320px`, side padding `--container-pad` = 32 / 24 / 16 px at desktop / tablet /
mobile) — **Implementation fact:** `frontend/src/styles/tokens.css` +
`frontend/src/styles/utilities.css`.

| # | Section | Component / file | Data source | Interaction | State | Responsive |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Announcement bar | `StorefrontLayout.vue` `.announce` | static copy (₹5,000 free-shipping line) | **Shop the collection** → `goToProducts()` scrolls to `#products-section` | none | text truncates; hidden `announce__cta` behaviour per breakpoint |
| 2 | Header / navigation | `StorefrontLayout.vue` `.header` | `authStore` (user, `isAdmin`) | nav anchors (`Store`, `Categories`, `Deals`, `New Arrivals`), `Admin` link only if `isAdmin`, sign in/out | `navOpen`, `searchOpen` | hamburger + slide-down `.header__panel` under mobile |
| 3 | Search (the only one) | `StorefrontLayout.vue` `.search` + `.panel-search` | `route.query.q` | see [PART 18](#part-18--search-experience) | `searchInput`, `searchOpen` | compact at rest, expands on focus; mobile icon opens the panel search |
| 4 | Cart button | `.cart-btn` (primary orange pill) | `cart.itemCount` | toggles drawer | `cartOpen` | label collapses on small screens, badge persists |
| 5 | Hero | `HeroSection.vue` | `listProducts({limit:5, sort:'newest', visibility:'active'})` | Add to cart on the featured product, "browse" scrolls to grid | `loading`, `items` | dark `--color-ink` card + orange glow; skeleton while loading; fallback panel on error |
| 6 | Categories | `CategorySection.vue` (+ `CategoryCard`) | static category definitions + facet counts | horizontal scroll rail of **rectangular** cards (scrollbar hidden), click → `?category=` | local scroll position | rail scrolls with touch on all widths |
| 7 | Trending tags | `TagMarquee.vue` → `TagPill` | tag list (from facets/catalog) | RTL marquee, **pause on hover/touch**, click runs a global search (`?q=tag`) | `paused` | reduced-motion: static row + native horizontal scroll (40 pills, verified) |
| 8 | Product collection | `ProductGrid` + `ProductFilters` + `AppPagination` | `GET /api/products` (+ facets) | filter/sort/pagination via query params | `loading`, `error`, `items`, `page` | 4 → 3 → 2 → 1 columns |
| 9 | Promo band | `StorefrontView` promo section | static | CTA scrolls/filters | — | full-width band inside the container |
| 10 | Footer | `StorefrontLayout.vue` `.footer` | static | Shop / Support / Company groups; category links run `goCategory(...)` | `year` | columns collapse to stacked groups |
| 11 | Cart drawer | `CartDrawer.vue` → `AppDrawer` | `useCartStore` | see [PART 20](#part-20--cart) | `cartOpen` | right drawer, `max-width: 100vw` |

Footer content is fixed by requirement and verified in the template: brand **Meridian Store**,
tagline *"Everything for the way you work."*, groups **Shop / Support / Company**, and
`© {{ year }} Meridian Store`.

**Skeletons, never a stuck `opacity: 0`:** entrance/async states use `LoadingSkeleton`
components and explicit `loading` flags; reduced-motion users get
`transition-duration: 0.01ms` rather than removed content
(`@media (prefers-reduced-motion: reduce)` blocks in `AppDrawer`, `StorefrontLayout`, etc.).

---

# PART 18 — Search Experience

**Level 18: one search, end to end.**

## 18.1 Why there is exactly one search

The requirement is a single **top** search that expands from compact, is reachable with `/` or
`⌘K`, navigates to product cards, and does **not** force filters. The implementation has exactly
one desktop search form in the header and one *mobile* input inside the nav panel — both bind the
**same** `searchInput` ref and the **same** `submitSearch` handler, so they are one logical
search, not two. There is no second search box anywhere (the admin screen's order search is a
different feature on a different route).

## 18.2 Behaviour

| Aspect | Implementation |
| --- | --- |
| Compact → expand | `.search` gets `search--open` when the input is focused (`@focus="searchOpen = true"`, `@blur` closes) |
| Keyboard | `onKeydown`: `/` or (`k` + meta/ctrl) focuses the input unless you're typing in an input/textarea/select/contenteditable; `Esc` closes/blurs |
| Query state | **URL is the source of truth**: `route.query.q`; the input mirrors it (`watch(() => route.query.q)`) |
| Debounce | `syncSearch = debounce((value) => router.replace({ query }), 260)` — drops `page`, keeps other keys |
| API | `GET /api/products?q=…` → Mongo case-insensitive regex over title/description/sku/tags |
| Scroll to results | after a non-empty `q` change on the storefront: `nextTick(() => scrollTo('#products-section'))` (offset `-96` px for the sticky header), `behavior: smooth` unless `prefers-reduced-motion` |
| Router cooperation | `scrollBehavior` returns `false` for same-path `q/category/sort/page` changes so the router doesn't fight the smooth scroll |
| Submit | `submitSearch()` blurs/closes and jumps to `#products-section` |
| Clear | `.search__clear` button sets `searchInput = ''` and refocuses |
| Empty results | `ProductGrid` empty state with **Clear search** (`emit('clear')` → `clearQuery('q')`) |
| Does not force filters | `q` is independent of `category`/`sort`; only `page` is reset when `q` changes |
| Categories/tags interplay | `?category=` is a separate filter; clicking a **tag** runs a global search (`?q=tag`) |
| Admin order search | separate: `POST /api/search/orders` on `/admin/search` |

## 18.3 Result rendering

`ProductGrid` → `ProductCard` (skeletons while `loading`, error state with **Retry**, empty state
with **Clear**) → `AppPagination` (`page X of Y`, totals formatted with `formatNumber`).

---

# PART 19 — Product Cards

**Level 19: the anatomy of `ProductCard.vue`.**

## 18.x/19.1 Information order (fixed by requirement, verified in template)

```
IMAGE      → ProductThumb (4:3 media box, wishlist heart overlay)
CATEGORY   → .product-card__category   (formatCategory())
TITLE      → .product-card__title      (-webkit-line-clamp: 2)
DESC       → .product-card__desc       (-webkit-line-clamp: 2, overflow-wrap: anywhere)
PRICE      → .product-card__price-row  (formatCurrency → ₹ + first tag chip)
ADD TO CART→ BaseButton .product-card__cta  (variant primary/secondary, inside the card)
```

## 19.2 How overflow and height problems are prevented

| Problem | Mechanism (verified) |
| --- | --- |
| Long titles/descriptions spill | `-webkit-line-clamp: 2` + `overflow: hidden` on both (lines 215-232) |
| Awkward words break layout | `overflow-wrap: anywhere` |
| Button pushed out of the card | `.product-card__cta { margin-top: auto }` inside a flex/grid body — the button is the last child and always sits at the bottom of the card |
| Uneven card heights in a row | `ProductGrid` uses `grid-template-columns: repeat(4, minmax(0, 1fr))` and cards stretch to the row height; the CTA's `margin-top: auto` absorbs leftover space |
| Broken image layouts | `ProductThumb` fixes `aspect-ratio: 4 / 3` on the media box and swaps to a deterministic placeholder on error/missing URL |
| Image jank | `loading="lazy" decoding="async"` + explicit `thumb--loading` / `thumb--error` states |
| Cards jumping on hover | `overflow: hidden` on card + media |

## 19.3 Wishlist

Optional heart toggle on the media (`.product-card__wish`, `aria-pressed`, local `wished` ref) —
presentational only; **no wishlist persistence** (not confirmed from the available source: no
wishlist store or endpoint exists).

---

# PART 20 — Cart

**Level 20: state, drawer, and what survives what.**

## 20.1 State model

```js
// frontend/src/stores/cart.js
items: { [productId]: { id, sku, title, price, category, image_url, quantity } }
getters: lines | isEmpty | itemCount | subtotal   // subtotal uses the SNAPSHOT price
actions: add(product, qty=1) · setQuantity(id, qty) · increment(id) · decrement(id)
         · remove(id) · clear()                   // clampQty → 1..100
```

- **Add:** merges into an existing line instead of duplicating it (keyed by id).
- **Remove / quantity:** `remove(id)`, `increment`, `decrement`, `setQuantity` — all clamped.
- **Subtotal / count:** computed getters, recompute automatically (reactive).
- **Server truth:** none of these values are trusted at checkout —
  `CheckoutView.loadPrices()` re-reads every product and `order_service` re-prices the order.

## 20.2 Drawer behaviour

- **Trigger:** `.cart-btn` in the header (orange primary pill, badge = `cart.itemCount`,
  `aria-expanded`, `aria-controls="cart-drawer"`).
- **Open animation:** when `cartOpen` is true the button itself changes:

```css
/* frontend/src/layouts/StorefrontLayout.vue:830-836 */
.cart-btn--open {
  transform: translateX(-10px);
  border-top-right-radius: 6px;
  border-bottom-right-radius: 6px;
  background: var(--color-ink);
  border-color: var(--color-ink);
  color: var(--color-primary);
}
```

  i.e. the button **slides left** while the drawer expands from the right — the requested
  "translates left while the right drawer expands" pairing. The transition uses the shared
  `--transition` token (within the requested 200–350 ms band).
- **Drawer:** `AppDrawer` (`Teleport` to body, `role="dialog"`, `aria-modal`, backdrop
  `@mousedown.self` close, `Esc` close, `document.body.style.overflow = 'hidden'` while open,
  `translateX(24px)` enter transition, reduced-motion collapses it to `0.01ms`).
- **Mobile:** `.drawer { max-width: 100vw }` — at 375/414 px the drawer occupies the full
  viewport width (verified at 375×812). *Not confirmed from the available source:* a
  bottom-sheet (slide-up) variant — no such media query exists in `AppDrawer.vue`.
- **Contents:** empty state (`EmptyState` "Your cart is empty" + **Browse products**), or lines
  with thumbnail, title, sku/price meta, quantity stepper (`−` disabled at 1, input 1..100, `+`),
  remove, plus a footer with subtotal and **Checkout**.
- **Close → checkout:** `goToCheckout()` sets `cartOpen = false` and `router.push({name:'checkout'})`.

## 20.3 What survives what (verified)

| Event | Cart |
| --- | --- |
| Component navigation (grid → drawer → filters) | ✅ survives (Pinia, app memory) |
| Route navigation (`/` → `/checkout`) | ✅ survives |
| Browser refresh / new tab | ❌ **cleared** — no `localStorage` persistence (deliberate; see [PART 15 §15.2](#152-storescartjs)) |
| Successful order | ❌ cleared explicitly via `cart.clear()` |

---

# PART 21 — Checkout

**Level 21: browser → PostgreSQL → RabbitMQ → Celery → Elasticsearch.**

```
Cart (Pinia)
  └─▶ /checkout  (guard: requiresAuth)
        ├─ loadPrices(): getProduct(id) per line  → live prices, unavailable detection
        ├─ OrderSummaryCard (subtotal, count, total)
        └─ placeOrder()
             └─ POST /api/orders { items:[{product_id, quantity}] }      ← NO prices/totals
                  └─ FastAPI: OrderCreate validation (1..50 items, qty 1..100, user_id>0)
                       └─ order_service.create_order()
                            ├─ resolve_cart()  → MongoDB read: exists? active? price>0
                            │                    Decimal re-pricing + merge duplicates
                            ├─ BEGIN → INSERT orders → flush
                            │        → INSERT order_items (title/unit_price SNAPSHOTS) → flush
                            │        → COMMIT   (or ROLLBACK → 500 order_persistence_failed)
                            └─ AFTER COMMIT → sync_service.publish_order_sync()
                                 └─ RabbitMQ queue `orders_sync`
                                      └─ Celery worker: read PG → build_order_document()
                                           └─ Elasticsearch upsert (_id = order_id)
```

**Product validation & snapshotting specifics:**

- `merge_duplicate_lines` collapses repeated ids; >100 units → **422 `quantity_limit_exceeded`**.
- Unknown product → **404 `product_not_found`**; inactive → **422 `inactive_product`**;
  missing/invalid price → **422 `invalid_price`**.
- `to_money()` quantizes to 2 dp with `ROUND_HALF_UP`; total = `Σ(quantity × unit_price)` in
  `Decimal` (never float).
- The chosen `title`/`unit_price` are written into `order_items` — that is the snapshot moment.
- The response's `sync` block reports messaging honestly:
  `{ enqueued, task_id, queue, error }`.

**Frontend after success:** `placedOrder` → `OrderSuccessPanel`, `cart.clear()`, toast with
`ORD-…` + formatted total; on failure an `AppAlert` shows the server message and the cart is
untouched.

---

# PART 22 — Admin Portal

**Level 22: which screen reads which database — the important part.**

| Admin feature | Screen / component | Endpoint | Store |
| --- | --- | --- | --- |
| KPI cards + result list | `AdminSearchView` + `SearchKpis`, `ResultsTable`/`ResultsCardList` | `POST /api/search/orders` | **Elasticsearch** |
| Filters (text, status, dates, price) | `SearchFilters` | same endpoint | Elasticsearch |
| Open order | → `OrderDetailsView` | `GET /api/orders/{id}` | **PostgreSQL** |
| Status change | `OrderStatusControl` | `PATCH /api/orders/{id}/status` | **PostgreSQL** (then sync to ES) |
| Sync indicator | `SearchSyncIndicator` | reads `search_indexed_at` from the order | PostgreSQL (bookkeeping) |
| Catalog table (incl. **Image** column) | `CatalogAdminView` + `CatalogTable` / `CatalogCardList` | `GET /api/products?visibility=all` | **MongoDB** |
| Create / edit product | `ProductFormModal` (same modal for both) | `POST /api/products`, `PATCH /api/products/{id}` | MongoDB |
| Activate / deactivate | toggle → `updateProduct({active})` / `deleteProduct()` | `PATCH` / `DELETE` | MongoDB (soft delete) |
| Upload / replace / remove image | `ProductFormModal` image area | `POST` / `DELETE /api/products/{id}/image` | disk + MongoDB `image_url` |

**Why this separation matters:** the search screen never queries PostgreSQL (there is even a test
`test_search_service_never_touches_postgres_or_mongodb`), and order details never query
Elasticsearch — so the canonical view can never show a stale projection. The catalog screen never
touches PostgreSQL/Elasticsearch.

**Admin shell:** `AdminLayout.vue` provides the navigation between the three admin screens; route
meta `requiresAuth + requiresAdmin` gates entry (`beforeEach` bounces non-admins to the
storefront).

**Image column:** `CatalogTable.vue` renders `Image` as the first `<th>`/`<td>` with
`<ProductThumb :product="product" size="sm" />`, and the loading row renders 10 skeleton cells to
match — no layout shift when data arrives.

---

# PART 23 — Product Image System

**Level 23: from the admin's file picker to the customer's `<img>`.**

## 23.1 End-to-end path

```
Admin  ▸  Edit Product (ProductFormModal)
       ▸  choose file  →  client validation (extension/type/size) + local preview
       ▸  uploadProductImage(id, file)  →  FormData{file}
              POST /api/products/{id}/image          (admin JWT required)
                  ├─ 404 if product missing
                  ├─ _validate_image_file()  content-type allowlist
                  ├─ _generate_safe_filename()  uuid4().hex + whitelisted extension
                  ├─ _save_upload_file()  5 MB cap → uploads/products/<file>
                  ├─ delete previous stored file (path containment checked)
                  └─ MongoDB $set { image_url: "/uploads/products/<file>" }
       ◂  ProductResponse
       ▸  ProductThumb → resolveImageUrl() → <img>
            dev:  Vite proxy /uploads → localhost:8000
            prod: Nginx  location /uploads/ → backend:8000
            API:  StaticFiles mount at /uploads  (app.main.mount_upload_storage)
```

## 23.2 Facts table

| Aspect | Value |
| --- | --- |
| Allowed content types | `image/jpeg`, `image/png`, `image/webp`, `image/svg+xml` |
| Allowed extensions | `.jpg .jpeg .png .webp .svg` (unknown extension → falls back to `.webp` in the generated name) |
| Max size | 5 MB (`MAX_FILE_SIZE = 5 * 1024 * 1024`) checked **after** reading the bytes |
| Storage dir | `settings.uploads_path / "products"` (default `/app/uploads/products`) |
| URL stored in Mongo | `/uploads/products/<uuid><ext>` (relative — keeps the app portable) |
| Docker persistence | named volume `uploads_data:/app/uploads` on `backend` **and** `celery-worker` |
| Serving | FastAPI `StaticFiles` mount `/uploads`; Vite proxy; Nginx `location /uploads/` |
| Replace | new file written first, then old file deleted best-effort, then Mongo updated; if Mongo update fails → new file deleted (rollback) |
| Remove | `DELETE /api/products/{id}/image` → file deleted (only if inside upload root) + `image_url: null` |
| Path safety | `_stored_image_path()` resolves and requires the result to be inside `UPLOAD_ROOT`; non-`uploads/` paths (e.g. bundle assets `/products/ORG-001.svg`) return `None` → never deleted |
| Filename safety | server-generated `uuid4().hex` — client filename never used |
| Preview | `URL.createObjectURL` before upload; server URL after |
| Loading state | `ProductThumb` `thumb--loading` until `@load` |
| Error state | `@error` or missing URL → deterministic monogram/pattern placeholder |
| Existing URLs | keep working: bundle assets `/products/*.svg` stay relative; absolute/`data:`/`blob:` pass through `resolveImageUrl` untouched |

## 23.3 Why a Docker volume exists

Container filesystems are ephemeral: `docker compose down/up` would otherwise delete every
uploaded image while MongoDB still points at `/uploads/products/…` — producing broken images on
the storefront. The named volume `uploads_data` makes files survive restarts and image rebuilds.
*(Volume definition: `docker-compose.yml` `volumes:` section; mount: `uploads_data:/app/uploads`.)*

**Known limitation (Implementation fact):** there is no garbage collection of orphaned files —
files whose product is deleted or whose `image_url` is overwritten by a non-upload path can remain
on disk.

---

# PART 24 — File-by-File Codebase Map

**Level 16: what every important file does.**

Legend: **Layer** ∈ {infrastructure, HTTP, business logic, data access, client, worker, UI, state,
utility, config, test, script}. Importance: **CORE** / **SUPPORTING** / **CONFIGURATION** /
**TEST** / **SCRIPT** / **ASSET**.

## 24.1 Backend — entry, core, config

| Path | Purpose | Layer | Depends on | Used by | Key exports | Importance |
| --- | --- | --- | --- | --- | --- | --- |
| `backend/app/main.py` | Creates the FastAPI app: CORS, exception handlers, lifespan (`init_infrastructure`), router registration, `/uploads` StaticFiles mount, root metadata | HTTP + config | `core/config`, `core/errors`, `api/*`, `StaticFiles` | uvicorn, tests | `app`, `init_infrastructure()`, `mount_upload_storage()` | CORE |
| `backend/app/__init__.py` | Version constant | config | — | `main.py` | `__version__` | SUPPORTING |
| `backend/app/core/config.py` | `Settings` (pydantic-settings, `.env`), derived `postgres_dsn` / `broker_url` / `cors_origin_list` / `uploads_path` / `sync_task_name`, cached `get_settings()` | config | env, `.env` | every backend module | `Settings`, `get_settings()` | CORE |
| `backend/app/core/auth.py` | bcrypt hashing, JWT create/decode, `get_current_user`, `require_admin`, `get_db`, `AuthError` | HTTP/auth | config, database, models | `api/*` | `hash_password`, `verify_password`, `create_access_token`, `get_current_user`, `require_admin` | CORE |
| `backend/app/core/database.py` | SQLAlchemy engine, `SessionLocal`, `get_db_session()`, `ping_postgres()`, `create_tables()` | data access | config | auth, services, tests | `engine`, `SessionLocal`, `get_db_session` | CORE |
| `backend/app/core/errors.py` | `AppError` hierarchy + one JSON envelope + FastAPI exception handlers | HTTP | fastapi | every service/route | `AppError`, `NotFoundError`, `UnprocessableError`, `ConflictError`, `DependencyUnavailableError`, `register_exception_handlers` | CORE |
| `backend/app/core/logging.py` | `configure_logging(level)`, `get_logger(name)` (stdout handler, idempotent) | config | — | all modules | `configure_logging`, `get_logger` | SUPPORTING |
| `backend/app/api/products.py` | Catalog routes + **image upload/replace/remove** (validation, safe filenames, 5 MB cap, path containment) | HTTP | services, repos, auth | router | `router`, `UPLOAD_DIR`, `_stored_image_path`, `_validate_image_file` | CORE |
| `backend/app/api/orders.py` | `POST /api/orders`, `GET /api/orders/{id}` (ownership), `PATCH …/status` (admin) | HTTP | order_service, auth | router | `router`, `ORDER_ID` | CORE |
| `backend/app/api/search.py` | `POST /api/search/orders` (admin only, ES only) | HTTP | search_service, auth | router | `router` | CORE |
| `backend/app/api/auth.py` | `POST /login`, `POST /logout`, `GET /me` | HTTP | auth_service, core.auth | router | `router` | CORE |
| `backend/app/api/users.py` | `GET /api/users` — seeded customers (no auth dependency) | HTTP | order_service | router | `router` | SUPPORTING |
| `backend/app/api/health.py` | `GET /api/health` pings PG/Mongo/ES/RabbitMQ, 200 vs 503 | HTTP | clients | router, docker healthcheck | `router`, `health()` | CORE |

## 24.2 Backend — services (business logic)

| Path | Purpose | Depends on | Used by | Key exports | Importance |
| --- | --- | --- | --- | --- | --- |
| `backend/app/services/order_service.py` | Cart resolution/re-pricing, explicit PG transaction, snapshot writes, status updates, `list_users` | mongo product_repo, postgres order_repo, sync_service, schemas | `api/orders.py`, `api/users.py` | `create_order`, `get_order`, `update_order_status`, `resolve_cart`, `merge_duplicate_lines`, `calculate_total`, `to_money`, `ResolvedLine`, `OrderPersistenceError` | CORE |
| `backend/app/services/sync_service.py` | Publishes the Celery task **after** commit; eager mode; failure → `SyncInfo(enqueued=False)` | celery_app, config | `order_service` | `publish_order_sync`, `EAGER_QUEUE` | CORE |
| `backend/app/services/product_service.py` | Catalog CRUD orchestration, `_to_response` normalization, facets, index bootstrap | mongo product_repo | `api/products.py`, `main.py` | `list_products`, `get_product`, `create_product`, `update_product`, `delete_product`, `list_facets`, `_to_response`, `ensure_catalog_indexes` | CORE |
| `backend/app/services/search_service.py` | Runs ES search, maps ES failures to `AppError(400)`/`DependencyUnavailableError(503)` | es search_repo | `api/search.py` | `search_orders` | CORE |
| `backend/app/services/auth_service.py` | Credential verification, token creation, user lookup | core.auth, models | `api/auth.py` | `authenticate_user`, `create_token_for_user`, `get_user_by_id` | CORE |

## 24.3 Backend — repositories & clients (data access)

| Path | Purpose | Talks to | Key exports |
| --- | --- | --- | --- |
| `repositories/mongo/product_repo.py` | All product queries: `_build_filter` (visibility/q/category/tags/price), sorting, facets, CRUD, indexes, soft delete | MongoDB | `list_products`, `get_product`, `get_products_by_ids`, `create/update/delete_product`, `list_facets`, `ensure_indexes` |
| `repositories/postgres/order_repo.py` | Thin ORM helpers for users/orders | PostgreSQL | `get_user`, `list_users`, `get_order`, `count_orders`, `iter_orders`, `mark_search_indexed`, `status_counts` |
| `repositories/elasticsearch/document.py` | **Pure** builder: SQLAlchemy `Order` → ES dict | — (pure) | `build_order_document` |
| `repositories/elasticsearch/mappings.py` | Explicit index settings + `dynamic: strict` mapping | — (data) | `ORDER_INDEX_SETTINGS`, `ORDER_INDEX_MAPPING` |
| `repositories/elasticsearch/orders_repo.py` | Index create/delete, single-doc **upsert** by `order_id` | Elasticsearch | `ensure_index`, `index_order_document`, `delete_index`, `index_name` |
| `repositories/elasticsearch/search_repo.py` | `build_search_query()` (pure) + execution with aggregations | Elasticsearch | `build_search_query`, `search_orders_with_index`, `TEXT_FIELDS`, `NESTED_TEXT_FIELDS` |
| `clients/mongodb.py` | Lazy shared `MongoClient`, `get_mongo_db`, `ping_mongo`, `close_mongo_client` | MongoDB | as named |
| `clients/elasticsearch.py` | Lazy `Elasticsearch` client (timeouts, retries, optional API key) | Elasticsearch | `get_elasticsearch_client`, `ping_elasticsearch`, `close_elasticsearch_client` |
| `clients/rabbitmq.py` | Kombu connectivity **probe only** (publishing goes through Celery) | RabbitMQ | `ping_rabbitmq` |

## 24.4 Backend — tasks, models, schemas, scripts

| Path | Purpose | Key exports |
| --- | --- | --- |
| `tasks/celery_app.py` | Celery app: broker, JSON serializers, queue, acks_late, retries, eager test mode | `celery_app` |
| `tasks/elasticsearch_tasks.py` | The sync task + synchronous core used by the reindex script | `sync_order_to_elasticsearch`, `sync_document`, `TASK_NAME` |
| `models/postgres.py` | SQLAlchemy models `User`, `Order`, `OrderItem` + CHECK/FK/index definitions | `Base`, `User`, `Order`, `OrderItem`, `ORDER_STATUSES` |
| `schemas/orders.py` | `OrderCreate` (no totals!), `OrderItemCreate`, `OrderResponse`, `OrderItemResponse`, `StatusUpdateRequest/Response`, `SyncInfo` | see [PART 27](#part-27--pydantic-schemas) |
| `schemas/products.py` | `ProductCreate/Update/Response`, `ProductListResponse`, `ProductFacetsResponse`, `Variant*`, sort literal, `VALID_CATEGORIES` | — |
| `schemas/search.py` | `SearchRequest` (+ range validators), `SearchResult`, `SearchAggregations`, `SearchResponse` | `DEFAULT_STATUS_COUNTS` |
| `schemas/auth.py` | `LoginRequest`, `LoginResponse`, `UserResponse`, `LogoutResponse` | — |
| `schemas/common.py` | `ErrorBody`, `ErrorResponse`, `PaginationMeta`, `HealthDependency`, `HealthResponse` | — |
| `scripts/seed.py` | Deterministic, idempotent, self-verifying seed (users/products/orders + snapshot demo + reindex) | `run`, `verify`, `main`, `USERS`, `PRODUCTS` |
| `scripts/reindex_orders.py` | Rebuilds the ES index from PostgreSQL (`iter_orders` batches) | CLI entry point |

## 24.5 Frontend — entry, routing, state, API, utils

| Path | Purpose | Key exports / notes |
| --- | --- | --- |
| `frontend/src/main.js` | `createApp(App)` → `createPinia()` → `router` → `mount('#app')`, imports `tokens.css` + `utilities.css` | entry |
| `frontend/src/App.vue` | `<router-view/>` + `<ToastHost/>`, calls `authStore.init()` | root |
| `frontend/src/router/index.js` | Route table, `beforeEach` guards (auth/admin/guest), `scrollBehavior` (false for query-only filter changes), `afterEach` title | `router` (default) |
| `frontend/src/stores/auth.js` | Token/user in `localStorage`, login/logout/fetchMe/init, `isAdmin` getter | `useAuthStore` |
| `frontend/src/stores/cart.js` | In-memory cart keyed by product id; clamped quantities; snapshot prices | `useCartStore`, `MIN_QTY`, `MAX_QTY` |
| `frontend/src/stores/toast.js` | Toast queue (max 5) with success/error/info/warning | `useToastStore` |
| `frontend/src/api/client.js` | Axios instance, `resolveBaseUrl`, `API_BASE_URL`, `ApiError`, interceptors, `toApiError`, `messageFrom`, `fieldErrorsFrom` | CORE |
| `frontend/src/api/products.js` | Catalog endpoints incl. `uploadProductImage` (FormData) / `removeProductImage` | functions |
| `frontend/src/api/orders.js` | `createOrder`, `getOrder`, `updateOrderStatus` | functions |
| `frontend/src/api/search.js` | `searchOrders(payload)` → `POST /api/search/orders` | function |
| `frontend/src/api/users.js` | `listUsers()` for the "Log In As" selector | function |
| `frontend/src/utils/currency.js` | ₹ formatting via `Intl.NumberFormat('en-IN')` — the **only** money formatter | `formatCurrency`, `formatNumber`, `parseAmount` |
| `frontend/src/utils/dates.js` | UTC-safe date/time formatting for naive API timestamps | `formatDate`, `formatDateTime`, `toDateInput`, `isValidDate`, … |
| `frontend/src/utils/image.js` | `resolveImageUrl()` — absolute/data/blob pass through; `/uploads/…` gets API origin; others stay relative | CORE for images |
| `frontend/src/utils/status.js` | The three statuses, labels, tones, options, validator | `ORDER_STATUSES`, `statusLabel`, `statusTone`, `isOrderStatus` |
| `frontend/src/utils/validation.js` | Client-side product field validators mirroring backend rules | `validateSku/Title/Price/Category/Variants/AttributeKeys`, `SKU_PATTERN` |
| `frontend/src/utils/debounce.js` | `debounce(fn, wait=300)` | function |
| `frontend/src/styles/tokens.css` | Design tokens: colour scale, `--color-primary #FFAC1C`, `--color-ink`, spacing scale 4…64, type scale, `--content-max: 1320px`, `--container-pad` | CORE styling |
| `frontend/src/styles/utilities.css` | `.container` / `.container-admin`, visibility helpers (`only-mobile`, `hide-mobile`, `hide-sm`), `.sr-only`, `.tabular`, `.truncate`, `.table-scroll` | CORE styling |

## 24.6 Frontend — layouts, views, components (short form)

| Path | Purpose |
| --- | --- |
| `layouts/StorefrontLayout.vue` | Announcement + header (brand, nav, single search, account, cart button) + footer + `CartDrawer`; scroll helpers, `/`/⌘K shortcut, debounced query sync |
| `layouts/AdminLayout.vue` | Admin chrome/nav for the three admin screens |
| `views/StorefrontView.vue` | Hero + categories + tag marquee + filters + product grid + pagination + promo; owns `load()`/`loadFacets()` and all query-param syncing |
| `views/CheckoutView.vue` | Live price loading, `placeOrder()`, success panel, empty-cart state |
| `views/LoginView.vue` + `components/auth/LoginForm.vue` | Email/password sign-in form wired to `authStore.login` |
| `views/AdminSearchView.vue` | Builds `SearchRequest`, KPIs, results, pagination, `openOrder()` |
| `views/OrderDetailsView.vue` | Loads canonical order, status control, sync indicator, snapshot line items |
| `views/CatalogAdminView.vue` | Catalog listing/filters + create/edit/deactivate via `ProductFormModal` |
| `components/storefront/ProductCard.vue` | Card with fixed order IMAGE→CATEGORY→TITLE→DESC→PRICE→ADD TO CART, clamping, wishlist |
| `components/storefront/ProductGrid.vue` | 4/3/2/1-column responsive grid, skeleton/error/empty states |
| `components/storefront/HeroSection.vue` | Dynamic hero (`listProducts(limit 5)`), skeleton + fallback, add-to-cart hooks |
| `components/storefront/CategorySection.vue` | Horizontal scroll rail of rectangular category cards |
| `components/storefront/TagMarquee.vue` + `TagPill.vue` | RTL marquee (pause on hover/touch, reduced-motion static), tag → global search |
| `components/storefront/CartDrawer.vue` | Cart lines, quantity steppers, subtotal, checkout CTA, empty state |
| `components/common/AppDrawer.vue` | Teleported right drawer with backdrop, Esc, scroll lock, reduced-motion |
| `components/common/ProductThumb.vue` | Image with `resolveImageUrl`, loading/error states, deterministic placeholder |
| `components/common/AppPagination.vue` | Summary + prev/next + page dots (disabled while loading) |
| `components/admin/ProductFormModal.vue` | Product create/edit form: tags/attributes/variants editors + **image preview/Replace/Remove** |
| `components/admin/CatalogTable.vue` | Catalog table incl. Image column + skeleton row |
| `components/admin/SearchFilters.vue` / `SearchKpis.vue` / `ResultsTable.vue` / `ResultsCardList.vue` | Admin search UI pieces |
| `components/admin/OrderStatusControl.vue` / `SearchSyncIndicator.vue` | Status change control; `search_indexed_at` indicator |
| `components/common/*` | `BaseButton`, `BaseInput/Select/Textarea`, `FormField`, `AppModal`, `AppAlert`, `AppBadge`, `StatusBadge`, `EmptyState`, `LoadingSkeleton`, `ConfirmDialog`, `KpiCard`, `ToastHost`, `AppIcon` — the no-browser-defaults component kit |

## 24.7 Infrastructure, config, tests, docs

| Path | Purpose | Importance |
| --- | --- | --- |
| `docker-compose.yml` | 9 services (`postgres`, `mongodb`, `elasticsearch`, `rabbitmq`, `backend`, `celery-worker`, `frontend`, `frontend-prod` [prod profile], `seed`/`reindex` [tools profile]), volumes, healthchecks, in-network env | CORE |
| `backend/Dockerfile` | 3 stages: `base` (deps) → `dev` (bind-mounted source) → `prod` (non-root user, `--workers 2`) | CORE |
| `frontend/Dockerfile` | 4 stages: `base` → `dev` (vite) → `build` → `prod` (nginx SPA + proxies) | CORE |
| `frontend/nginx.conf` | `/api/` + `/uploads/` → `backend:8000`, `/assets/` cache, SPA `try_files` | CORE |
| `frontend/vite.config.js` | Vue plugin, dev proxy (`/api`, `/uploads`), Vitest config (jsdom, `tests/**/*.spec.js`) | CORE |
| `frontend/package.json` | Scripts (`dev`, `build`, `preview`, `test`) and deps (vue, vue-router, pinia, axios, vitest) | CONFIGURATION |
| `backend/requirements.txt` (+ `-dev`) | FastAPI, pydantic(-settings), SQLAlchemy, psycopg, pymongo, elasticsearch, celery, python-jose, passlib, python-multipart, uvicorn… | CONFIGURATION |
| `pytest.ini` | rootdir/testpaths/markers for the backend suite | CONFIGURATION |
| `.env.example` | Every variable with safe defaults; template for `.env` (never commit secrets) | CONFIGURATION |
| `tests/conftest.py` | Fixtures: `api`, `admin_api`, `authenticated_api`, `order_factory`, `product_factory`, `es_document`, `es_purge_orphans`; skips integration tests when infra is down | TEST |
| `tests/unit/*` | Pure-logic tests (pricing, schemas, ES document, search query builder) | TEST |
| `tests/integration/*` | Live-HTTP tests against real infra (products, orders, search, sync task) | TEST |
| `frontend/tests/*.spec.js` | 28 Vitest tests (cart, components, currency, status, smoke) | TEST |
| `README.md` | Primary docs: architecture, API table, sync strategy, seed, testing, limitations | SUPPORTING |
| `Knowledge bytes/Knowledge_Bytes.txt` | Earlier byte-format notes; some claims are outdated (roles, search details) — prefer this document | SUPPORTING |

---

# PART 25 — File Relationship Map

**How files connect — not just what they contain.**

## 25.1 Checkout chain

```
ProductCard.vue
   └─▶ stores/cart.js                 (add → snapshot line)
          └─▶ CheckoutView.vue        (loadPrices via api/products.js::getProduct)
                 └─▶ api/orders.js::createOrder
                        └─▶ api/client.js  (axios, Authorization header)
                               └─▶ backend/app/api/orders.py
                                      └─▶ services/order_service.py::create_order
                                             ├─▶ repositories/mongo/product_repo.py   (validate + price)
                                             ├─▶ models/postgres.py (Order, OrderItem)
                                             ├─▶ repositories/postgres/order_repo.py
                                             └─▶ services/sync_service.py   (AFTER COMMIT)
                                                    └─▶ tasks/celery_app.py::send_task
                                                           └─▶ RabbitMQ `orders_sync`
                                                                  └─▶ tasks/elasticsearch_tasks.py
                                                                         ├─▶ repositories/postgres/order_repo.py (re-read)
                                                                         ├─▶ repositories/elasticsearch/document.py
                                                                         └─▶ repositories/elasticsearch/orders_repo.py (upsert)
                                                                                └─▶ Elasticsearch `orders`
```

## 25.2 Admin search chain

```
AdminSearchView.vue ─▶ api/search.js::searchOrders ─▶ api/client.js
      └─▶ api/search.py (get_current_user + require_admin)
             └─▶ services/search_service.py
                    └─▶ repositories/elasticsearch/search_repo.py::search_orders_with_index
                           ├─▶ orders_repo.ensure_index()
                           └─▶ clients/elasticsearch.py
```

## 25.3 Image chain

```
ProductFormModal.vue ─▶ api/products.js::uploadProductImage(FormData)
      └─▶ api/products.py::upload_product_image (require_admin)
             ├─▶ core/config.py::uploads_path   (disk)
             ├─▶ repositories/mongo/product_repo.py::update_product  (image_url)
             └─▶ response.image_url
                    └─▶ ProductThumb.vue ─▶ utils/image.js::resolveImageUrl
                           └─▶ Vite/Nginx proxy ─▶ main.py StaticFiles `/uploads`
```

## 25.4 Auth chain

```
LoginForm.vue ─▶ stores/auth.js::login ─▶ api/client.js::post('/api/auth/login')
      └─▶ api/auth.py ─▶ services/auth_service.py ─▶ core/auth.py::verify_password
             └─▶ models/postgres.py::User  ── JWT returned ──▶ localStorage
                                                              └─▶ client.js interceptor (Bearer)
                                                                     └─▶ core/auth.py::get_current_user
                                                                            └─▶ require_admin / ownership checks
```

---

# PART 26 — Backend Request Lifecycle

**How a typical request travels through the code.**

```
HTTP request
  → Uvicorn / FastAPI
  → CORSMiddleware (origin allowlist from CORS_ORIGINS)
  → Route matching (APIRouter prefix + path)
  → Dependencies (Depends):  get_db / get_current_user / require_admin / Query / Path validation
  → Pydantic body validation (422 → envelope `validation_error`)
  → Thin route handler (api/*.py) — no business rules here
  → Service (services/*.py) — rules, pricing, transactions, error mapping
  → Repository / client (repositories/*, clients/*) — store I/O
  → Pydantic response model serialization (response_model=…)
  → JSON response  … or …
  → AppError → register_exception_handlers → {"error": {code, message, details}} with its status code
```

Where each responsibility lives (Implementation fact):

| Responsibility | Location |
| --- | --- |
| Path/query/body validation | FastAPI + Pydantic schemas (`api/*.py` signature) |
| Authentication | `Depends(get_current_user)` (`core/auth.py`) |
| Authorization | `Depends(require_admin)` or ownership check in the route/service |
| Business rules | `services/*.py` only |
| Transactions | `services/order_service.py` (explicit `session.begin/commit/rollback`) |
| SQL/Mongo/ES statements | `repositories/*` |
| Cross-cutting errors | `core/errors.py` handlers (envelope) |
| Response shape | `response_model` on each route |

---

# PART 27 — Pydantic Schemas

**Request vs. response vs. database model.**

This project uses **all three layers**, and they differ deliberately:

| Layer | Example | Lives in | Responsibility |
| --- | --- | --- | --- |
| Request schema | `OrderCreate { user_id?, items[] }` | `schemas/orders.py` | What the client is *allowed* to send — **no money fields at all** |
| Response schema | `OrderResponse { id, order_number, status, total_amount, items[], sync? }` | `schemas/*.py` | Stable public JSON shape; hides DB internals; converts datetimes/decimals |
| Database model | `Order` (SQLAlchemy) | `models/postgres.py` | Persistence, constraints, relationships — never returned directly |

Key schemas:

| Schema | In/Out | Notable validation | Used by |
| --- | --- | --- | --- |
| `OrderItemCreate` | in | `product_id` 1–64 chars, `quantity` 1–100 | `POST /api/orders` |
| `OrderCreate` | in | 1–50 items; `user_id > 0` optional; **comment states client totals are never trusted** | `POST /api/orders` |
| `OrderResponse` / `OrderItemResponse` | out | `title`/`unit_price` documented as snapshots | order APIs |
| `SyncInfo` | out | `{enqueued, task_id?, queue, error?}` | create + status responses |
| `StatusUpdateRequest` | in | `status ∈ PENDING/PROCESSING/SHIPPED` (Literal) | `PATCH …/status` |
| `ProductCreate`/`ProductUpdate`/`ProductResponse` | in/out | SKU pattern, price `>0 ≤ 1e6` rounded to 2 dp, category/tags normalization, ≤30 tags, ≤20 variants, nested `attributes` | catalog APIs |
| `SearchRequest` | in | status list, non-inverted date & price ranges (`model_validator`), `page 1..10000`, `limit 1..100` | `POST /api/search/orders` |
| `SearchResponse` / `SearchResult` / `SearchAggregations` | out | `revenue` + `status_counts` KPI block | admin search |
| `LoginRequest`/`LoginResponse`/`UserResponse` | in/out | email+password; token+user | `/api/auth/*` |
| `ErrorResponse` (`ErrorBody`) | out | single envelope shape for **all** errors | exception handlers |
| `HealthResponse`/`HealthDependency` | out | `status: ok\|degraded`, per-dependency `latency_ms` | `/api/health` |

**Why separate layers:** the DB can evolve (constraints, `numeric`) without breaking clients, and
the API can refuse fields the DB would happily accept (a client-sent `total_amount`).

---

# PART 28 — SQLAlchemy Models

**What the ORM is doing conceptually:** mapping Python classes to tables, generating SQL, tracking
changes in a session, and giving you transactions — while the *explicit* `begin/commit/rollback`
in `order_service` keeps the transaction boundary visible.

```python
# backend/app/models/postgres.py (structure)
class User(Base):
    __tablename__ = "users"
    id, name, email(unique, indexed), password_hash, role(default "CUSTOMER"),
    created_at(server_default=now())
    orders = relationship(back_populates="user", lazy="raise", passive_deletes=True)
    __table_args__ = (CheckConstraint("role IN ('CUSTOMER','ADMIN')"),)

class Order(Base):      # order_number UNIQUE · status CHECK · FK user_id · indexes on
                        # status/order_date/user_id · total_amount Numeric(12,2)
                        # + created_at/updated_at/search_indexed_at

class OrderItem(Base):  # FK order_id ON DELETE CASCADE · snapshot title/unit_price
                        # CHECKs on quantity/unit_price · line_total
```

| Aspect | Detail |
| --- | --- |
| Base | `DeclarativeBase` (`Base`) |
| Timestamps | `server_default=func.now()` where appropriate; service sets `created_at`/`updated_at` explicitly for orders |
| Relationships | `User.orders` is `lazy="raise"` — the API never walks user→orders accidentally (N+1 protection) |
| Money | `Numeric(12,2)` → `Decimal` (never float) |
| Status | CHECK constraint + Python `ORDER_STATUSES` tuple + schema `Literal` (three layers of protection) |
| `product_id` | plain string — **no FK**, because the referenced entity lives in MongoDB |
| Schema creation | `create_tables()` runs `Base.metadata.create_all()` at startup (idempotent); no migration framework (Alembic) is present |

---

# PART 29 — Services / Business Logic

**Why logic sits in a service instead of a route handler.**

Reasons visible in this codebase: (a) reuse — `order_service.get_order` serves the HTTP route
*and* tests; `sync_document` serves the Celery task *and* the reindex script; (b) testability —
`resolve_cart`, `build_search_query`, `build_order_document` are pure functions unit-tested
without infrastructure; (c) the route layer stays a thin translation of HTTP ↔ schema.

| Service | Inputs | Outputs | Side effects | Key edge cases |
| --- | --- | --- | --- | --- |
| `order_service.create_order` | `OrderCreate` | `OrderCreateResponse` (+`sync`) | Mongo read; PG write; RabbitMQ publish | duplicate lines merged; inactive/unknown product; >100 qty; rollback on any insert failure; publish failure never rolls back |
| `order_service.resolve_cart` | `items[]` | `(ResolvedLine[], Decimal total)` | Mongo read | empty cart, missing product, inactive, invalid price |
| `order_service.update_order_status` | id, status | `StatusUpdateResponse` | PG write; publish only if changed | unknown order; unchanged status (no publish) |
| `product_service.*` | payloads | `ProductResponse(s)` | Mongo writes | duplicate SKU → 409 `ConflictError`; soft delete |
| `search_service.search_orders` | `SearchRequest` | `SearchResponse` | ES query | ES 400 → `search_query_invalid`; ES down → 503 `search_unavailable` |
| `sync_service.publish_order_sync` | id, reason | `SyncInfo` | RabbitMQ publish (or eager run) | broker down → `enqueued: false` + error string |
| `auth_service.authenticate_user` | email, password | `User` | none (DB read) | unknown email and wrong password return the **same** message |

---

# PART 30 — Error Handling

**How errors move through the system — and the two envelope shapes that exist.**

## 30.1 The one envelope (app-level errors)

```json
{ "error": { "code": "order_not_found", "message": "Order '999999' was not found.",
             "details": { "order_id": 999999 } } }
```

Raised as `AppError` subclasses in `core/errors.py` and rendered by
`register_exception_handlers`:

| Class | Status | Typical codes |
| --- | --- | --- |
| `BadRequestError` | 400 | `bad_request`, `search_query_invalid` |
| `NotFoundError` | 404 | `not_found`, `product_not_found`, `order_not_found`, `user_not_found`, `invalid_credentials` |
| `ConflictError` | 409 | `conflict` (duplicate SKU) |
| `UnprocessableError` | 422 | `inactive_product`, `invalid_price`, `quantity_limit_exceeded`, `empty_cart`, `invalid_image`, `invalid_image_format`, `image_too_large` |
| `OrderPersistenceError` (500) | 500 | `order_persistence_failed` |
| `DependencyUnavailableError` | 503 | `dependency_unavailable`, `search_unavailable` |

Plus two FastAPI-level handlers:

- `RequestValidationError` → **422** `code: "validation_error"` with
  `details.fields: [{field, message, type}]` (consumed by `fieldErrorsFrom()` in the frontend).
- Any unhandled `Exception` → **500** `code: "internal_error"` (logged with traceback).

## 30.2 Documentation vs. implementation: a second shape exists

**Implementation fact:** `register_exception_handlers` registers handlers for `AppError`,
`RequestValidationError` and `Exception` — **not** for Starlette/FastAPI `HTTPException`.
Authentication/authorization failures are raised as `HTTPException` inside
`get_current_user`/`require_admin`, so **401/403 come back as FastAPI's default
`{"detail": "Admin access required"}`**, not the `{"error": …}` envelope.

**Frontend consequence (Implementation fact):** `toApiError()` looks for `response.data.error`;
when it is missing it falls back to a generic message — a 403 surfaces as
*"The server returned an unexpected 403 response."* unless the UI shows the raw detail.

## 30.3 Per-layer behaviour

| Layer | Failure | What happens |
| --- | --- | --- |
| Frontend request | network down / timeout (20 s) | `ApiError(code:'network_error')` — *"Cannot reach the API server. Please check that the backend is running."* |
| Frontend request | HTTP error | `toApiError` → envelope message or generic fallback; views show `AppAlert`/toast |
| Validation | bad body/query | 422 `validation_error` with per-field messages → inline form errors |
| AuthN | no/bad/expired token | 401 (`HTTPException`) — router guard also redirects to `/login` client-side |
| AuthZ | non-admin hits admin route | 403 (`HTTPException`, *"Admin access required"*) |
| MongoDB down | catalog query | PyMongo raises → 500 `internal_error` (unless a service maps it; catalog paths do not map to 503) |
| PostgreSQL down | order write/read | rollback → 500 `order_persistence_failed`; health endpoint reports `down` |
| Elasticsearch down | search | `search_service` → 503 `search_unavailable` with a recovery hint |
| Elasticsearch bad query | ES 400 | 400 `search_query_invalid` + `details.reason` |
| RabbitMQ down | publish | caught in `sync_service` → `sync.enqueued:false` + `error` string; HTTP 201 still returned |
| Celery task | ES write fails | `self.retry` backoff ×5, then give up; PG untouched; `search_indexed_at` stays null |
| Image upload | wrong type / >5 MB / missing product | 422 `invalid_image_format` / `image_too_large` / 404 `product_not_found`; disk file rolled back when the Mongo update fails |
| Image serving | file missing on disk | `StaticFiles` → 404 → `<img>` `@error` → placeholder in `ProductThumb` |

---

# PART 31 — Security

**Only what the code actually implements.**

| Mechanism | Implementation | Notes / limits |
| --- | --- | --- |
| Password storage | bcrypt via `passlib.CryptContext(schemes=["bcrypt"])` | plaintext never stored |
| Credential errors | identical message for unknown email and wrong password | avoids user enumeration (message is the same, but status is 404 for both) |
| Token | JWT HS256, `sub = user id`, `exp = now + 24 h`, secret from `JWT_SECRET_KEY` | **`.env.example` does not define `JWT_SECRET_KEY`** — the default `"change-me-in-production-use-a-long-random-string"` is used unless you set it. A *forged* token requires the secret; rotate it in production. |
| Token transport | `Authorization: Bearer …` header from `localStorage` | XSS risk inherent to localStorage; no httpOnly cookies (stateless design) |
| Authorization | `require_admin` per route; order ownership on `GET /api/orders/{id}` | frontend hiding is UX only |
| CORS | `CORSMiddleware` with `allow_origins = CORS_ORIGINS` (default `http://localhost:5173`), credentials allowed, all methods/headers | restrict in production |
| Upload validation | content-type allowlist + extension allowlist + 5 MB cap | content-type is client-declared (no magic-byte sniffing) |
| Path traversal | `_stored_image_path()` resolves and requires containment in `UPLOAD_ROOT`; filenames are server-generated UUIDs | `../` cannot escape; non-upload URLs are never deleted |
| Secrets | `.env` (git-ignored) + `.env.example` template with placeholders | README: "NEVER commit real secrets" |
| Rate limiting / HTTPS / CSRF tokens | **not present** | Not confirmed from the available source — no rate limiter, no TLS termination, no CSRF layer (Bearer-token API, so classic CSRF does not apply) |
| Elasticsearch security | disabled in compose (`xpack.security.enabled: false`) | demo configuration, single node |
| Admin container user | `frontend-prod` runs nginx; backend `prod` stage runs as non-root `appuser` | dev stage runs as root (bind-mounted source) |

---

# PART 32 — Docker Architecture

## 32.1 Services

| Service | Image / build | Purpose | Ports | Depends on (condition) | Volumes | Healthcheck |
| --- | --- | --- | --- | --- | --- | --- |
| `postgres` | `postgres:16-alpine` | orders/users | `5432:5432` | — | `postgres_data` | `pg_isready -U …` |
| `mongodb` | `mongo:7` | catalog | `27017:27017` | — | `mongodb_data` | (compose-defined) |
| `elasticsearch` | `docker.elastic.co/…/elasticsearch:8.15.3` | search projection | `9200:9200` | — | `elasticsearch_data` | `curl …/_cluster/health?wait_for_status=yellow` (10s ×20) |
| `rabbitmq` | `rabbitmq:3.13-management-alpine` | broker + mgmt UI | `5672`, `15672` | — | `rabbitmq_data` | `rabbitmq-diagnostics -q ping` |
| `backend` | `backend/Dockerfile` **target dev** | FastAPI (`uvicorn … --reload`) | `8000:8000` | all four `service_healthy` | `./backend:/app`, **`uploads_data:/app/uploads`** | HTTP `GET /api/health == 200` (10s ×12, start 20s) |
| `celery-worker` | same, target dev | `celery … worker --concurrency=2` | — | postgres/ES/rabbitmq healthy | `./backend:/app`, `uploads_data:/app/uploads` | `celery inspect ping … | grep -q pong` |
| `frontend` | `frontend/Dockerfile` **target dev** | Vite dev server | `5173:5173` | backend `service_healthy` | `./frontend:/app`, `frontend_node_modules` | — |
| `frontend-prod` | target **prod** (nginx) | static SPA + proxies | `8080:80` | backend healthy | — | — |
| `seed` | target dev, profile **tools** | `python -m scripts.seed` | — | three healthy | — | — |
| `reindex` | target dev, profile **tools** | `python -m scripts.reindex_orders --recreate` | — | infra healthy | — | — |

**Networks/volumes:** one bridge `app_net`; named volumes `postgres_data`, `mongodb_data`,
`elasticsearch_data`, `rabbitmq_data`, `frontend_node_modules`, `uploads_data`.

## 32.2 Startup order

```
postgres, mongodb, elasticsearch, rabbitmq   (parallel; each must be healthy)
        └─▶ backend (waits for ALL four healthy; becomes healthy itself via /api/health)
                 ├─▶ celery-worker (waits for postgres, elasticsearch, rabbitmq healthy)
                 ├─▶ frontend      (waits for backend healthy)
                 └─▶ frontend-prod (profile "prod")
seed / reindex  (profile "tools", run on demand with `docker compose run --rm seed`)
```

In-network endpoints are injected by the `x-backend-environment` anchor:
`POSTGRES_HOST=postgres`, `MONGO_URI=mongodb://mongodb:27017`,
`ELASTICSEARCH_URL=http://elasticsearch:9200`, `RABBITMQ_HOST=rabbitmq`, `RABBITMQ_URL=amqp://…@rabbitmq:5672//`.

## 32.3 Persistent vs. ephemeral

| Storage | Type | Survives |
| --- | --- | --- |
| `postgres_data`, `mongodb_data`, `elasticsearch_data`, `rabbitmq_data` | named volumes | container/image rebuilds |
| `uploads_data` → `/app/uploads` | named volume | **product images** survive restarts/rebuilds |
| `frontend_node_modules` | named volume | npm deps across bind mounts |
| `./backend:/app`, `./frontend:/app` | bind mounts (dev) | source edits live-reload |
| Container writable layer | ephemeral | lost on `down`/recreate |

---

# PART 33 — Environment Configuration

Read by `backend/app/core/config.py` via `pydantic-settings` (`.env` at repo root, case-insensitive,
`extra="ignore"`). Values below are **placeholders** — never real secrets.

| Variable | Purpose | Where read | Example shape | Required? | Sensitivity |
| --- | --- | --- | --- | --- | --- |
| `APP_NAME`, `ENVIRONMENT`, `LOG_LEVEL` | app identity/logging | `Settings` | `Meridian` / `development` / `INFO` | optional (defaults) | low |
| `API_HOST`, `API_PORT` | bind address | `Settings` (+ compose `command`) | `0.0.0.0` / `8000` | optional | low |
| `CORS_ORIGINS` | comma-separated browser origins | `cors_origin_list` | `http://localhost:5173,http://127.0.0.1:5173` | required in prod | medium |
| `POSTGRES_HOST/PORT/USER/PASSWORD/DB/SSLMODE/POOL_SIZE` | PG connection | `postgres_dsn` | `localhost`, `5432`, `ecommerce`, `<secret>`, `ecommerce` | yes | **high** (password) |
| `MONGO_URI`, `MONGO_DB`, `MONGO_TIMEOUT_MS` | catalog connection | `clients/mongodb.py` | `mongodb://localhost:27017`, `catalog`, `5000` | yes | medium |
| `ELASTICSEARCH_URL/INDEX/API_KEY/TIMEOUT/REFRESH_ON_WRITE` | search cluster | `clients/elasticsearch.py` | `http://localhost:9200`, `orders`, *(empty = no auth)*, `10`, `true` | URL yes; API key optional | medium (API key) |
| `RABBITMQ_DEFAULT_USER/PASSWORD/HOST/PORT/URL` | broker | `broker_url` | `ecommerce`, `<secret>`, `localhost`, `5672` | yes | **high** |
| `CELERY_TASK_DEFAULT_QUEUE` | queue name | celery config | `orders_sync` | optional | low |
| `CELERY_MAX_RETRIES/RETRY_BACKOFF/RETRY_BACKOFF_MAX` | retry policy | task config | `5`, `10`, `120` | optional | low |
| `CELERY_TASK_ALWAYS_EAGER` | in-process tasks (tests) | `sync_service`, celery config | `false` | optional | low |
| `UPLOADS_DIR` | image upload root | `settings.uploads_path` | `/app/uploads` | optional (default `/app/uploads`) | low — **not in `.env.example`** |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | token signing | `core/auth.py` | `<long random>`, `HS256`, `1440` | optional (defaults!) | **critical** — **not in `.env.example`** |
| `VITE_API_BASE_URL` | browser→API origin | `frontend/src/api/client.js` (build/runtime env) | `http://localhost:8000`, or `''` for relative | optional | low |
| `VITE_PROXY_TARGET` | dev proxy target | `frontend/vite.config.js` | `http://backend:8000` (set by compose) | optional | low |
| `POSTGRES_USER/PASSWORD/DB` (compose) | bootstrap PG container | `docker-compose.yml` | `ecommerce`, `<secret>`, `ecommerce` | optional (defaults) | **high** |
| `WEB_PORT`, `API_PORT`, `ELASTICSEARCH_PORT`, `RABBITMQ_PORT`, `RABBITMQ_MGMT_PORT` | host port mapping | `docker-compose.yml` | `8080`, `8000`, `9200`, `5672`, `15672` | optional | low |
| `ES_JAVA_OPTS` | heap size | `docker-compose.yml` | `-Xms512m -Xmx512m` | optional | low |

**Two gaps to remember (verified):** `JWT_SECRET_KEY` and `UPLOADS_DIR` are **not** present in
`.env.example` or the local `.env`, so their `Settings` defaults apply
(`change-me-in-production-use-a-long-random-string` and `/app/uploads`).

---

# PART 34 — Testing

**What each suite protects — not just how many pass.**

## 34.1 Backend — pytest (`pytest.ini`: `testpaths = tests`, `pythonpath = backend`)

`tests/conftest.py` provides `api` (TestClient with lifespan), `admin_api`,
`authenticated_api` (real login → bearer), `order_factory` / `product_factory`,
`es_document` / `es_delete` helpers, and **skips integration tests with an actionable message
when any of the four services is unreachable**.

### Unit (`tests/unit/` — no infrastructure)

| File | What it proves |
| --- | --- |
| `test_pricing.py` | `to_money` rounds HALF_UP to 2 dp; total = Σ lines; empty cart = 0; duplicate lines merge; >100 rejected; `OrderCreate` has **no price fields** (the "client totals are never trusted" contract) |
| `test_schemas.py` | Search rejects unknown statuses, inverted ranges, bad pagination; product price/SKU/category validation; status Literal enforcement |
| `test_es_document.py` | The ES document contains every required field, uses **PostgreSQL snapshots** (not live Mongo), rounds money to floats, ISO timestamps, and is deterministic (idempotent input → same `_id`) |
| `test_search_query.py` | `build_search_query` produces `multi_match` on customer/item fields, `terms` status, `range` date/price, aggregations (revenue + counts), `from/size`, newest-first sort |

### Integration (`tests/integration/` — live PostgreSQL/MongoDB/Elasticsearch/RabbitMQ)

| File | What it proves (representative tests) |
| --- | --- |
| `test_products_api.py` | ≥24 active products; inactive hidden; every category present; tag AND-semantics; text search; pagination metadata; invalid ObjectId → **404 not 500**; full create/update/soft-delete cycle; specific validation errors |
| `test_orders_api.py` | server recomputes totals (client totals ignored); duplicate lines merged; snapshots captured; **historical snapshot survives the Wireless Mouse rename**; **transaction rolls back completely when an item insert fails**; unknown/inactive product rejection; malformed carts; order readable from PG; status PATCH queues sync and validates status |
| `test_search_api.py` | free-text/name/item-title search; filters (status, dates inclusive, price band, combined); KPI aggregations describe the **filtered** set; pagination; 422s; **the search service never touches PostgreSQL/MongoDB** (poisoned-session test); ES↔PG count parity |
| `test_sync_task.py` | task builds the doc from PG; **idempotent**; skips missing orders; reflects status changes; uses PG snapshots not live Mongo titles; reindex rebuilds an identical index; publish carries a task id; **publish failure never rolls back a committed order**; status-patch publish failure is non-fatal; retry backoff; gives up after max retries; task name is stable; exactly one ES doc per PG order |

## 34.2 Frontend — Vitest (`npm test` → `vitest run`, jsdom, `tests/**/*.spec.js`)

| File | What it protects |
| --- | --- |
| `cart.spec.js` | add-once + snapshot of title/price; merge repeat adds; **quantity clamp 1..100**; subtotal math; remove/clear; products without an id are ignored (store invariants) |
| `currency.spec.js` | ₹ formatting with 2 decimals + Indian grouping; accepts numeric strings; em dash for junk; `parseAmount` defensiveness — **the single money formatter stays correct** |
| `status.spec.js` | exactly three statuses; label/tone mapping; validation; UTC rendering of naive API timestamps incl. month boundaries |
| `components.spec.js` | `BaseButton` (label, click emit, disabled/busy, keyboard reachability), `StatusBadge` tones, `KpiCard` loading skeleton — the component kit has no browser-default behaviour |
| `smoke.spec.js` | Real-API smoke: storefront renders live catalog, admin search renders KPIs + ES results, checkout renders empty state **without an API call**, order details renders a live PG order, catalog admin renders the live table |

**Run results recorded during the final verification pass:** `npm run build` ✅ ·
`npm test` → **28/28** · `.venv/bin/python -m pytest` → **100 passed**.
*(README advertises 101 — documentation vs. implementation drift, see [PART 1 §1.4](#doc-vs-code).)*

## 34.3 Beyond unit/integration

- **Image API e2e:** upload → preview → Mongo `image_url` → replace → remove → restore, exercised
  against the live backend.
- **Browser QA:** DOM geometry + overflow audits and pixel sampling at 1920/1440/1280/1024/768/414/375
  on both the dev server and the nginx production build (test tooling kept outside the repo in
  `/tmp/opencode/`).

---

# PART 35 — Seed Data

**Deterministic, idempotent, self-verifying.**

Run: `docker compose run --rm seed` (or `cd backend && python -m scripts.seed`; search index
inside: `--skip-search` disables it).

## 35.1 What it creates (README §12, matching `scripts/seed.py` structure)

| Requirement | Seeded value |
| --- | --- |
| Users | **8** customers incl. `Wendy Wireless`; roles per `USERS` table; hashed passwords |
| Active products | **26** across `peripherals`, `audio`, `cables`, `office` (≥5 each) |
| Inactive product | **1** (hidden from storefront, 422 if ordered) |
| "wireless" products | ≥ 6 (search fixture) |
| Price bands | ≥4 cheap / mid / premium |
| Orders / items | **44 / 86** |
| Statuses | `PENDING 15 · PROCESSING 15 · SHIPPED 14` |
| Dates | 90-day window: >60 days old, ≤7 days old, and everything between |
| Totals | ≥5 under 30, ≥5 in 30–150, ≥5 over 200 |
| Per-user | ≥2 orders each; Wendy ≥3 incl. a wireless product |
| Search fixtures | ≥8 orders with `Wireless Mouse`, ≥3 with `Mechanical Keyboard`, ≥2 with both |
| **Snapshot demo** | after orders exist: MongoDB `Wireless Mouse` ($50.16) → `Wireless Mouse Pro` ($60.00) |
| PG ↔ ES parity | reindex runs **inside** the seed; counts must match |

## 35.2 How reproducibility is enforced

- Fixed RNG seed: `Settings.seed_random_seed = 20240917`.
- Drops and rebuilds (idempotent re-run).
- `verify(expect_search=True)` turns every requirement above into an **assertion that fails the
  script** if unmet (including `total_amount == Σ(quantity × unit_price)` for every order).
- Seed functions: `seed_users()`, `seed_products()`, `seed_orders()`,
  `apply_snapshot_demo()`, `verify()`, `run()`.

**Snapshot mismatch is intentional:** the demo *depends* on the catalog price/title diverging from
the seeded orders, so the storefront shows new data while old orders (and their ES documents) keep
the original values.

---

# PART 36 — Snapshot Semantics

**The chapter that explains why the data model looks the way it does.**

## 36.1 The scenario, with real seed values

**MongoDB before the order:**

```jsonc
{ "sku": "PER-1001", "title": "Wireless Mouse", "price": 50.16, "active": true }
```

**Customer orders 1 × that product → PostgreSQL stores:**

```sql
-- order_items (row produced by order_service.create_order)
product_id = '<mongo ObjectId>', title = 'Wireless Mouse',   -- SNAPSHOT
quantity   = 1,              unit_price = 50.16,             -- SNAPSHOT
line_total = 50.16
-- orders
total_amount = 50.16, status = 'PENDING', order_number = 'ORD-0000xx'
```

**Later, an admin edits MongoDB:**

```jsonc
{ "title": "Wireless Mouse Pro", "price": 60.00 }
```

**After the edit:**

| Surface | Shows | Source |
| --- | --- | --- |
| Storefront / catalog admin | Wireless Mouse **Pro**, ₹60.00 | live MongoDB |
| The old order (`GET /api/orders/{id}`) | Wireless Mouse, ₹50.16, total 50.16 | PostgreSQL snapshot |
| Admin order search (Elasticsearch doc) | Wireless Mouse, ₹50.16 | rebuilt **from PostgreSQL** |
| Cart added before the edit | ₹50.16 until reloaded | client-side snapshot (re-priced by server anyway) |

## 36.2 Why old orders must show the original snapshot

*(General engineering knowledge, applied)* An order is a record of an agreement: it answers
"what did we sell this customer, and for how much?" If it referenced only `product_id`, then a
routine catalog correction would silently rewrite revenue reports, receipts and audit history —
and the order total would stop equalling the sum of its line items. Snapshotting freezes the
values at the moment of purchase; the current catalog remains free to evolve.

## 36.3 Where the snapshot lives (all three copies)

1. **Write path:** `order_service.create_order` copies `line.title` and `line.unit_price`
   (already re-read from MongoDB in `resolve_cart`) into `OrderItem` rows.
2. **Read path:** `OrderItemResponse.title` / `.unit_price` are documented in the schema as
   *"Snapshot of the product title/unit price at purchase time"* (`schemas/orders.py:55-57`).
3. **Search path:** `build_order_document()` reads only the SQLAlchemy `Order` (items included),
   so ES inherits PostgreSQL's snapshots — never live Mongo values.
4. **Tests:** `test_historical_snapshot_survives_the_wireless_mouse_rename`,
   `test_sync_uses_postgres_snapshots_not_live_mongo_titles`,
   `test_document_uses_the_postgresql_snapshots`.
5. **Seed proof:** `apply_snapshot_demo()` renames and reprices **after** orders exist, and
   `verify()` asserts both sides still hold.

## 36.4 Gotcha: the *cart* snapshot is different

`stores/cart.js` also snapshots `title`/`price` — but that is a **UX convenience**, not a
financial record: `CheckoutView.loadPrices()` re-reads live products for display, and the server
re-prices everything anyway. A stale cart price can never leak into PostgreSQL.

---

# PART 37 — Elasticsearch Projection

## 37.1 From PostgreSQL row to Elasticsearch document

```
orders + order_items + users (PostgreSQL)
        │  build_order_document(order)        ← pure function, `repositories/elasticsearch/document.py`
        ▼
{ order_id, order_number, status, order_date, updated_at, total_amount,
  customer:{id,name,email}, items:[{product_id,title,quantity,unit_price,line_total}] }
        │  index_order_document(doc)  → PUT /orders/_doc/{order_id}   (upsert)
        ▼
Elasticsearch index `orders`   (mapping: dynamic strict, items nested, name/email search_as_you_type)
```

**Duplication is the point:** the index is a *read-optimized copy* of data that already exists in
PostgreSQL, reshaped for search (flattened customer fields, nested items, keyword facets).

## 37.2 Source of truth vs. read/search projection

| Property | PostgreSQL order | Elasticsearch order |
| --- | --- | --- |
| Authoritative | ✅ yes | ❌ no |
| Written by | API request path (transactional) | Celery worker only (+ reindex script) |
| Money precision | `numeric(12,2)` (Decimal) | `double` (analytics) |
| Can be dropped/rebuilt | ❌ (irreplaceable) | ✅ always rebuildable |
| Read by | `GET /api/orders/{id}`, status PATCH, seed verification | `POST /api/search/orders` only |
| Timing | immediate (COMMIT) | after queue + worker (ms–seconds, or later if down) |

## 37.3 Consistency model — only what is guaranteed

**Implementation facts:**

- Publishing happens **after** commit, never inside the transaction.
- The task rebuilds the document from PostgreSQL, so the projection converges to the source.
- `_id = order_id` upsert makes redelivery harmless (at-least-once delivery, exactly-once
  *effect* at the document level).
- `search_indexed_at` records *that* indexing happened; it is explicitly bookkeeping and is
  ignored if that update fails.
- `ELASTICSEARCH_REFRESH_ON_WRITE=true` (compose default) makes just-indexed docs searchable
  immediately for the demo — trading write throughput.

**Consequence (Implementation fact):** between COMMIT and the worker finishing, a brand-new order
is **not** findable in admin search. The order itself is fully readable from PostgreSQL.
**Inference:** this window is normally milliseconds when all services are healthy.

**What is NOT guaranteed (verified absent):** no distributed transaction, no outbox, no CDC, no
polling reconciler, no version/vector clocks. Recovery = `python -m scripts.reindex_orders`
(compose service `reindex`, `--recreate`).

---

# PART 38 — Important Design Decisions

Each row: **Decision → Reason → Benefit → Tradeoff**. Reasons marked **Inferred** are not stated
in the code.

| Decision | Reason | Benefit | Tradeoff |
| --- | --- | --- | --- |
| **MongoDB for catalog** | Product documents vary in shape (`attributes`, `variants`) and are filtered as documents (**Inferred**) | Schema freedom, simple facet/regex queries | No cross-store referential integrity (`product_id` in orders is plain text) |
| **PostgreSQL for orders** | Orders need ACID multi-row writes, constraints and exact money | `orders` + `order_items` are all-or-nothing; `numeric(12,2)` | Relational rigidity; sync ORM (fine at this scale) |
| **Elasticsearch for admin search** | Full-text + facets + aggregations over orders (**Inferred**) | One query returns results + revenue/status KPIs | Eventual consistency; a second copy to maintain |
| **PostgreSQL = source of truth** | Money must be transactionally correct | ES can always be rebuilt; UI never trusts stale ES | Order *details* never benefit from search speed |
| **RabbitMQ + Celery for sync** | Decouple checkout latency from indexing (**Inferred**) | Order placement works even if ES/worker is down | Possible lag; possible lost message if the process dies pre-publish |
| **Dual-write style: publish after COMMIT (no outbox)** | Keeps *exactly one* sync strategy (README §8/§17) | Simple to reason about, no CDC tooling | Small window where a committed order has no queued task |
| **Rebuild whole document per task (no patch)** | Simplicity + convergence (task docstring) | Idempotent; self-healing | Slightly more work per task (irrelevant at this scale) |
| **JWT (stateless) auth** | No session store to manage (**Inferred**) | Horizontal scale, simple logout (client discards token) | No server-side revocation; 24 h token lifetime |
| **bcrypt password hashing** | Industry-standard slow hash | Stored passwords are not reversible | Login cost per attempt (intended) |
| **Soft delete for products** | Historical orders keep referencing them (route docstring) | Catalog never breaks old orders | Storefront queries must always filter `active` |
| **Snapshot title/price into `order_items`** | Orders are financial records | History immutable; totals self-consistent | Catalog fixes don't propagate to old orders (by design) |
| **Pinia for auth/cart/toast only** | Server data stays in views (**Inferred**) | No stale cache bugs; explicit fetching | Some prop-drilling between components |
| **Cart without `localStorage` persistence** | Keeps cart semantics simple and tests deterministic (**Inferred**, deliberate during UI rebuild) | No stale-cart surprises across sessions | Refresh clears the cart (known limitation) |
| **Local disk image storage + `uploads_data` volume** | No paid storage allowed; images must survive restarts | Simple, inspectable, works offline | No CDN/scaling; orphaned files not collected |
| **Docker Compose for everything** | Reproducible polyglot stack in one command | Onboarding = `up -d --build` + `seed` | Single-host only |
| **Nginx for prod frontend** | Static SPA + same-origin `/api` proxy | No Node process in production | Only one frontend origin |
| **Single global search in the header** | Requirement: one search that doesn't force filters (UI work) | Consistent UX; `/` and ⌘K shortcuts | Mobile needs the nav-panel input (same state, one logical search) |
| **₹ currency via one formatter** | Requirement: all customer prices in ₹ | Impossible to show `$` by accident (`Intl` `en-IN`) | Indian formatting is baked in |

---

# PART 39 — Edge Cases and Gotchas

**"Things I need to remember" — every entry verified in code.**

1. **Cart does not survive a browser refresh.** Pinia state only; `localStorage` is deliberately
   unused for cart (would conflict with `frontend/tests/cart.spec.js`).
2. **Elasticsearch can lag PostgreSQL.** New orders appear in admin search only after the worker
   runs; recovery for lost docs: `python -m scripts.reindex_orders --recreate`.
3. **No transactional outbox.** Kill the API between COMMIT and `send_task` and that order has no
   task — the response would have shown `sync.enqueued:false` if it had reached the publish step.
   A status update later re-publishes it.
4. **At-least-once delivery ⇒ duplicate tasks possible** — harmless because `_id = order_id`
   upserts.
5. **Retries stop after 5 attempts** (10→20→40→80→≤120 s). After that ES stays stale until
   something re-triggers a sync or you reindex.
6. **`search_indexed_at` can lie.** It is bookkeeping, best-effort, and failure to write it does
   not fail the task.
7. **Money is `double` in ES, `numeric(12,2)` in PG, `Decimal` in service code.** Do not compute
   financial values from ES results (KPIs are fine — they're analytics).
8. **Inactive products stay in the catalog.** Storefront queries filter `active`; ordering one →
   422 `inactive_product`; admin catalog shows them with `visibility=all`.
9. **Product delete is a soft delete** — `DELETE /api/products/{id}` returns the product with
   `active:false`, never removes rows (so old orders keep meaning).
10. **Image uploads are files on a volume.** `docker compose down -v` deletes them
    (`-v` removes named volumes) while MongoDB still references `/uploads/products/…` → broken
    images + placeholder fallback.
11. **No image garbage collection.** Replacing an image deletes the old file, but deleting a
    product leaves its uploaded file on disk.
12. **`UPLOADS_DIR` and `JWT_SECRET_KEY` are not in `.env.example`.** Defaults:
    `/app/uploads` (container path — wrong for a bare-host run) and a well-known JWT secret.
13. **401/403 use FastAPI's `{"detail": …}` shape**, not the `{"error": …}` envelope — the
    frontend shows a generic message for them ([PART 30 §30.2](#302-documentation-vs-implementation-a-second-shape-exists)).
14. **`GET /api/users` is unauthenticated** — it only returns seeded customer names/emails/roles
    for the "Log In As" demo selector.
15. **`POST /api/orders` has no auth dependency** in the route (server accepts `user_id` or the
    default); the *UI* gates checkout behind login. Treat as a demo-grade gap.
16. **Search is `q`-driven, not filter-forcing.** Changing `q` resets only `page`; `category`,
    `sort` are independent query params. Same-path query navigations skip router scroll
    (`scrollBehavior → false`) to avoid scroll fighting.
17. **Pagination:** storefront `PAGE_SIZE` 12 (view-level), API default `limit=24` (max 100);
    admin search `PAGE_SIZE` 20 (API default, max 100). `page` resets when filters/query change.
18. **Docker ports:** API 8000 · Vite 5173 · prod nginx 8080 · PG 5432 · Mongo 27017 ·
    ES 9200 · RabbitMQ 5672/15672. `frontend-prod` needs `--profile prod`; `seed`/`reindex`
    need `--profile tools`.
19. **MongoDB regex search** (`q`) is case-insensitive substring matching across
    title/description/sku/tags — no stemming, no relevance ranking (that's Elasticsearch's job,
    and it applies to *orders*, not products).
20. **Every `.sr-only` element must live inside `.table-scroll`** — an absolutely-positioned
    screen-reader span placed outside that scroller widened the document and caused horizontal
    overflow at 375 px until `.table-scroll { position: relative }` was added
    (`frontend/src/styles/utilities.css`).
21. **Seeded demo order during verification:** `ORD-000064`, ₹229.00, `Pending` — a real row in
    PostgreSQL (+ ES) created while testing checkout; delete it if you want pristine seed data.

---

# PART 40 — Troubleshooting Guide

### 40.1 Frontend cannot reach the backend

- **Symptoms:** toasts "Cannot reach the API server…", network tab shows failed `/api` calls.
- **Likely cause:** API down, wrong `VITE_API_BASE_URL`, or CORS origin not allowlisted.
- **Verify:** `curl -s localhost:8000/api/health`; check `CORS_ORIGINS` in `.env`;
  dev tools → Console for CORS errors.
- **Fix:** `docker compose up -d backend` (or run uvicorn), align `VITE_API_BASE_URL`
  (use `''` to rely on the Vite/Nginx proxy), add your origin to `CORS_ORIGINS`.

### 40.2 Products do not load

- **Symptoms:** skeleton → error state / "Retry" on the storefront; empty grid.
- **Likely cause:** MongoDB down or empty (never seeded).
- **Verify:** `curl 'localhost:8000/api/products?limit=1'`; `/api/health` shows `mongodb: down`;
  `mongosh` → `catalog.products.countDocuments()`.
- **Fix:** start Mongo; run `docker compose run --rm seed`.

### 40.3 Images show broken / placeholder

- **Symptoms:** monogram placeholder instead of a photo.
- **Likely cause:** file missing from the volume, `/uploads` not proxied, or `image_url` points at
  a deleted file.
- **Verify:** `curl -I localhost:8000/uploads/products/<file>`; check the container path
  (`docker compose exec backend ls /app/uploads/products`); confirm Mongo `image_url`.
- **Fix:** re-upload via catalog admin; ensure `uploads_data` volume exists; confirm Nginx
  `location /uploads/` and Vite `/uploads` proxy are present.

### 40.4 Uploaded image disappears after restart

- **Cause:** running without the volume (bare `docker run`, or `down -v`), or `UPLOADS_DIR`
  pointing somewhere ephemeral.
- **Verify:** `docker volume ls | grep uploads_data`; `docker compose config` shows
  `uploads_data:/app/uploads`.
- **Fix:** recreate the volume mapping; re-upload lost files.

### 40.5 Order is in PostgreSQL but not in Elasticsearch

- **Symptoms:** order details show it; admin search doesn't; sync indicator shows not indexed.
- **Likely cause:** worker down, RabbitMQ down at publish time (`sync.enqueued:false` in the
  create/patch response), or retries exhausted.
- **Verify:** `docker compose logs celery-worker` (look for the task + queue `orders_sync`);
  RabbitMQ mgmt UI :15672; `GET /api/orders/{id}` (has `search_indexed_at`?);
  count ES docs vs `SELECT count(*) FROM orders`.
- **Fix:** start the worker; `docker compose run --rm reindex` (rebuilds from PG);
  fix broker connectivity if `enqueued:false` was returned.

### 40.6 Admin cannot access search

- **Symptoms:** redirected to storefront (frontend) or 403 (API).
- **Cause:** role is `CUSTOMER`, or token invalid/expired (24 h).
- **Verify:** `SELECT email, role FROM users;`; try `POST /api/auth/login`; call
  `POST /api/search/orders` with/without the bearer token (expect 401 vs 403).
- **Fix:** log in as an admin seed account; update `users.role` in PostgreSQL if needed.

### 40.7 Customer receives 403 (or a generic "unexpected 403" message)

- **Cause:** hitting an admin route/endpoint as a customer — or accessing another user's order.
- **Verify:** token payload `sub` vs `orders.user_id`; API response body (`{"detail": …}`).
- **Fix:** correct role/ownership; expect frontend generic text (envelope mismatch, known).

### 40.8 Celery worker is not processing tasks

- **Symptoms:** queue grows; no index updates.
- **Verify:** `docker compose ps celery-worker` health; logs for
  `"sync task queued"` (API) and task execution (worker); `celery -A app.tasks.celery_app inspect ping`.
- **Fix:** restart the worker; check it consumed `orders_sync` in the startup banner; confirm
  `RABBITMQ_URL`/`broker_url` matches the broker.

### 40.9 RabbitMQ is unavailable

- **Symptoms:** orders still succeed but responses carry `sync.enqueued:false` + error.
- **Verify:** `/api/health` → `rabbitmq: down`; port 5672 closed.
- **Fix:** start RabbitMQ; then reindex (messages published during the outage are gone).

### 40.10 Elasticsearch is unhealthy

- **Symptoms:** `/api/health` degraded; admin search returns 503 `search_unavailable`.
- **Verify:** `curl localhost:9200/_cluster/health`; container logs (heap/disk watermark).
- **Fix:** restart ES; give it memory (`ES_JAVA_OPTS`); free disk (watermarks are set to
  95/98/98%); then reindex.

### 40.11 Checkout fails with 500 `order_persistence_failed`

- **Verify:** backend logs (the real exception is logged with traceback); PG up; then confirm
  **no partial rows**: `SELECT count(*) FROM orders` before/after.
- **Fix:** repair the DB; the transaction rolled back — the cart is untouched.

### 40.12 Build/test commands to re-run a check

```bash
cd frontend && npm run build && npm test     # bundle + 28 Vitest tests
.venv/bin/python -m pytest                   # backend suite (needs infra for integration)
docker compose run --rm seed                 # rebuild deterministic demo data
docker compose run --rm reindex              # rebuild ES from PostgreSQL
```

---

# PART 41 — Knowledge Bytes

Progressive, self-contained teaching units. Each byte states what it builds on, shows **real**
code from the repository, and ends with cross-references. Numbering is continuous across
sections A–O.

| Section | Bytes | Theme |
| --- | --- | --- |
| A — System foundation | 1–7 | What Meridian is, the problem, actors, polyglot design, truth vs. projection |
| B — Technology | 8–22 | Vue, Vite, Pinia, Router, Axios, FastAPI, Pydantic, SQLAlchemy, the four stores, Docker, Nginx |
| C — Data | 23–29 | User, product, order, order item, snapshot, ES document, relationships |
| D — Frontend | 30–40 | Entry, router, layouts, views, components, stores, API client, currency/image utils, tokens |
| E — Storefront | 41–53 | Announce bar → nav → search → hero → categories → tags → grid → card → pagination → cart → checkout |
| F — Backend | 54–64 | Startup, routing, dependencies, route families, services, schemas, models, sessions |
| G — Authentication | 65–72 | Hashing → login → JWT → header → current user → roles → ownership → admin |
| H — Order flow | 73–79 | Cart → validation → transaction → creation → snapshots → commit → sync trigger |
| I — Message pipeline | 80–87 | RabbitMQ → Celery → task → execution → indexing → retries → failure → consistency |
| J — Elasticsearch | 88–95 | Index → mapping → document → full-text → partial → filters → aggregations → admin search |
| K — Product images | 96–106 | image_url → column → modal → UploadFile → validation → storage → volume → resolver |
| L — Admin | 107–113 | Screens → KPIs → filters → results → details → status → catalog |
| M — Infrastructure | 114–120 | Compose → Dockerfiles → Nginx → env → health → seed → reindex |
| N — Testing | 121–126 | Unit → integration → fixtures → frontend → strategy → failure tests |
| O — Edge cases & recovery | 127–138 | Inactive product, duplicate SKU, missing doc, sync failure, rollback, drift, orphans, security, overflow, cart reset, migration, e2e checklist |
| (file deep-dives) | 139–158 | One byte per critical file — see [PART 42](#part-42--file-specific-knowledge-bytes) |

---

## SECTION A — SYSTEM FOUNDATION

---

### Byte 1: What Meridian is

**Builds on:** None — starting point.

**Concept:** The identity and purpose of this application.

**In plain terms:**

Meridian is the storefront brand of a project formally named *E-Commerce Order Management &
Search Service*. It is a working shop (electronics/workspace gear) bolted onto a serious backend
that exists to demonstrate **polyglot persistence**: several databases, each owning exactly one
kind of data. Five screens exist: storefront, checkout, admin order search, order details, and
catalog admin.

**Why it exists:**

The project is a reference implementation for a real architectural problem: e-commerce data has
three incompatible needs (flexible catalog, transactional money, fast search). One database
serving all three produces corrupt history, slow writes, or weak search.

**The code:**

```python
# backend/app/main.py
app = FastAPI(
    title=settings.app_name,          # "E-Commerce Order Management & Search Service"
    ...
    description=(
        "Polyglot persistence demo: **MongoDB** (product catalog), "
        "**PostgreSQL** (order source of truth), **RabbitMQ + Celery** "
        "(asynchronous synchronisation) and **Elasticsearch** "
        "(search, filtering and aggregations).\n\n"
        "Synchronisation path: `PostgreSQL → RabbitMQ → Celery → Elasticsearch`."
    ),
)
```

How to read the code:

`app` is the entire HTTP application; its `description` is the project's own one-paragraph
summary, served at `/docs`. `settings.app_name` comes from `core/config.py`.

What happens at runtime:

Uvicorn imports `app.main:app`, runs the lifespan (create tables, ensure indexes), and every
request is dispatched through the routers registered below this block.

Connects to: Byte 2 (problem), Byte 6 (architecture), PART 1.

Remember: the brand is **Meridian**; the system is an **order-management + search** service —
the shop UI is the demonstration surface, not the point.

---

### Byte 2: The problem being solved

**Builds on:** Byte 1.

**Concept:** Why single-database e-commerce designs fail.

**In plain terms:**

If orders store only a `product_id`, then editing the product rewrites history: old receipts
change price and title. If search runs on the transactional database, checkout gets slower as
orders accumulate. If indexing happens inside the request, a slow search cluster blocks payments.

**Why it exists:**

This project answers each failure with a structural rule: catalog in MongoDB, money/orders in
PostgreSQL with explicit transactions, search in Elasticsearch as a copy, and the copy updated
*after* commit through a queue.

**The code:**

```python
# backend/app/schemas/orders.py — class OrderCreate
"""
Note: there is intentionally **no** `total_amount` field.  The server
always re-reads MongoDB, validates the products and computes the total
itself — client supplied totals are never trusted.
"""
items: list[OrderItemCreate] = Field(min_length=1, max_length=50)
```

How to read the code:

The *absence* of a field is the design: money can only be produced server-side, so a tampered
client cannot set prices.

What happens at runtime:

A `POST /api/orders` body carrying `total_amount` is simply ignored (extra fields are dropped by
Pydantic) — `order_service.resolve_cart()` recomputes everything from MongoDB.

Connects to: Byte 75 (transaction), Byte 143 (order service), PART 2.

Remember: client-supplied totals are ignored; catalog edits must never touch old orders.

---

### Byte 3: What a customer does

**Builds on:** Byte 1.

**Concept:** The customer journey through the frontend.

**In plain terms:**

Browse `/` (hero, categories, tags, product grid) → search or filter (URL query params) → add to
cart (a Pinia store, no server call) → `/checkout` (login required) → place order → the server
re-prices, writes PostgreSQL, and the UI shows `ORD-000xxx`.

**Why it exists:**

It is the flow that exercises every layer: Mongo reads, validation, transaction, queue, and the
projection that follows.

**The code:**

```js
// frontend/src/stores/cart.js — action add()
const line = {
  id: product.id,
  sku: product.sku || '',
  title: product.title || 'Untitled product',
  price: Number(product.price),
  // ...
  quantity: clampQty(quantity),
}
this.items[product.id] = line
```

How to read the code:

The cart stores a **copy** of title and price keyed by product id — deliberately local state.

What happens at runtime:

Clicking ADD TO CART mutates Pinia state; the badge updates; nothing hits the network until
checkout.

Connects to: Byte 35 (stores), Byte 52 (cart drawer), Byte 53 (checkout), PART 20.

Remember: cart = client snapshot; the server re-prices everything later.

---

### Byte 4: What an admin does

**Builds on:** Byte 1, Byte 3.

**Concept:** The admin journey and where its data comes from.

**In plain terms:**

An admin signs in, opens `/admin/search` (Elasticsearch: KPIs + results + filters), drills into
`/admin/orders/:id` (PostgreSQL: canonical details, status change), and manages
`/admin/catalog` (MongoDB: CRUD + image upload). Three screens, three different databases.

**Why it exists:**

Showing all three stores in one UI makes the separation visible: search can lag, but order
details can never be wrong.

**The code:**

```python
# backend/app/core/auth.py
def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency that requires the current user to have ADMIN role."""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin access required")
    return current_user
```

How to read the code:

Every admin route declares `Depends(require_admin)`; without it the route is public. The
dependency chains through `get_current_user`, which validates the JWT and loads the user.

What happens at runtime:

A customer's token passes authentication but fails the role check → 403 before any handler runs.

Connects to: Byte 57 (admin dependency), Byte 67 (JWT), PART 3, PART 22.

Remember: frontend hiding of admin links is UX; `require_admin` is the security.

---

### Byte 5: Polyglot persistence

**Builds on:** Byte 1, Byte 2.

**Concept:** Using several databases, each for what it is good at.

**In plain terms:**

MongoDB holds product *documents* (varied shapes, nested arrays, filters). PostgreSQL holds
*rows* with constraints and transactions (users, orders, items). Elasticsearch holds a *search
index* (relevance, facets, aggregations). RabbitMQ transports work; Celery performs it.

**Why it exists:**

Each access pattern maps to a store that implements it natively — instead of emulating search in
SQL or transactions in a document store.

**The code:**

```python
# backend/app/repositories/mongo/product_repo.py (module docstring)
"""Product catalog repository (MongoDB).

All catalog reads and writes for Screen 1 (storefront) and Screen 5
(catalog admin) go through this module.  Orders are *never* read from
MongoDB — PostgreSQL owns those.
"""
```

How to read the code:

The docstring is a **contract**: each repository declares which store owns its domain, and no
module crosses that line.

What happens at runtime:

`product_repo` only ever talks to `get_mongo_db()`; `order_repo` only to SQLAlchemy sessions.

Connects to: Byte 6 (architecture), Bytes 16-18 (store roles), PART 5.

Remember: one store, one job — the rule is written down in module docstrings and enforced by
tests (e.g. `test_search_service_never_touches_postgres_or_mongodb`).

---

### Byte 6: High-level architecture

**Builds on:** Byte 5.

**Concept:** The components and the single synchronization path.

**In plain terms:**

Browser → (Vite/Nginx) → FastAPI → MongoDB for catalog, PostgreSQL for orders. After a
PostgreSQL commit, FastAPI publishes a small task message to RabbitMQ; a Celery worker reads the
order back from PostgreSQL, builds a search document, and upserts it into Elasticsearch. Admin
search reads only Elasticsearch.

**Why it exists:**

Checkout must never wait on search infrastructure; search must never be authoritative.

**The code:**

```python
# backend/app/services/sync_service.py (module docstring)
"""Synchronisation publisher: PostgreSQL → RabbitMQ → Celery → Elasticsearch.

The API only *publishes* a task after the PostgreSQL transaction has
committed.  Building/updating the Elasticsearch document happens in the
Celery worker (`app.tasks.elasticsearch_tasks`), never in the request
cycle.
"""
```

How to read the code:

This four-arrow line is the whole synchronization design; everything else is detail.

What happens at runtime:

`publish_order_sync(order_id, reason)` → `celery_app.send_task(..., queue="orders_sync")`.

Connects to: Byte 7 (projections), Byte 82 (task), PART 6.

Remember: exactly one sync path exists — no polling, no CDC, no outbox.

---

### Byte 7: Source of truth vs. projections

**Builds on:** Byte 6.

**Concept:** Which copy wins when copies disagree.

**In plain terms:**

PostgreSQL is the **source of truth**: if it says an order is `SHIPPED` for ₹229.00, that is
reality. Elasticsearch is a **projection**: a derived, rebuildable copy used only for search and
KPIs. If ES disagrees, ES is wrong — rebuild it.

**Why it exists:**

Projections can lag, fail, or be partially written without ever endangering money.

**The code:**

```python
# backend/app/api/orders.py (module docstring)
"""Order endpoints — data source: **PostgreSQL** (source of truth).

* `POST /api/orders`          validate cart (MongoDB) → PostgreSQL
                              transaction → publish RabbitMQ sync task
* `GET  /api/orders/{id}`     canonical order details (never Elasticsearch)
* `PATCH /api/orders/{id}/status`  update PostgreSQL, then synchronise
"""
```

How to read the code:

"(never Elasticsearch)" is deliberate wording: the *details* screen must not read a lagging copy.

What happens at runtime:

`GET /api/orders/64` always opens a PostgreSQL session; `POST /api/search/orders` always talks to
Elasticsearch — the two never mix.

Connects to: Byte 120 (reindex/recovery), Byte 87 (consistency), PART 37.

Remember: truth in PostgreSQL, speed in Elasticsearch, and a rebuild command for the gap.

---

## SECTION B — TECHNOLOGY

---

### Byte 8: Vue

**Builds on:** Byte 3.

**Concept:** The UI framework and its component model.

**In plain terms:**

Vue 3 single-file components (`.vue`) combine template, script and scoped style. `<script setup>`
declares reactive refs/computed values that the template re-renders automatically. Props flow
down, events flow up.

**Why it exists:**

Reactive UI without a manual DOM layer; small components keep the storefront and admin screens
composable.

**The code:**

```js
// frontend/src/main.js
const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')
```

How to read the code:

`createApp` builds the root instance; plugins (state, routing) are installed before mount.

What happens at runtime:

The browser loads `index.html` → `main.js` mounts `App.vue` → `<router-view>` renders the current
route's view.

Connects to: Byte 11 (router), Byte 34 (components), PART 13.

Remember: all state updates are automatic — never mutate the DOM directly.

---

### Byte 9: Vite

**Builds on:** Byte 8.

**Concept:** The dev server and bundler.

**In plain terms:**

Vite serves ES modules on demand during development (instant HMR) and produces an optimized
`dist/` bundle for production. It is also where dev-time **proxying** of `/api` and `/uploads` to
the backend is configured.

**Why it exists:**

Fast feedback in development and a static artifact Nginx can serve in production.

**The code:**

```js
// frontend/vite.config.js
proxy: {
  '/api':    { target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000', changeOrigin: true },
  // Uploaded product images live on the backend (/uploads/products/…).
  '/uploads':{ target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000', changeOrigin: true },
},
```

How to read the code:

Relative requests stay same-origin in the browser; Vite forwards them to FastAPI, avoiding CORS
during development. Compose sets `VITE_PROXY_TARGET=http://backend:8000`.

What happens at runtime:

`GET /api/products` from the page on `:5173` is proxied to `:8000`; images behave identically.

Connects to: Byte 22 (Nginx), Byte 38 (image URLs), PART 32.

Remember: dev = Vite proxy, prod = Nginx proxy — the frontend code doesn't change between them.

---

### Byte 10: Pinia

**Builds on:** Byte 8.

**Concept:** Shared reactive state outside the component tree.

**In plain terms:**

A Pinia store is a single source of truth that any component can import. This project has exactly
three: `auth` (token/user), `cart` (items), `toast` (notifications).

**Why it exists:**

The cart must survive navigation between components; the auth token must be visible to the router
guard and the header simultaneously.

**The code:**

```js
// frontend/src/stores/cart.js
export const useCartStore = defineStore('cart', {
  state: () => ({ items: {} }),
  getters: {
    lines(state) { return Object.values(state.items) },
    itemCount() { return this.lines.reduce((sum, line) => sum + line.quantity, 0) },
    subtotal()  { return this.lines.reduce((sum, line) => sum + line.price * line.quantity, 0) },
  },
  actions: { /* add, setQuantity, increment, decrement, remove, clear */ },
})
```

How to read the code:

`state` is the raw data, `getters` are computed values (recomputed when state changes), `actions`
mutate state.

What happens at runtime:

`cart.add(product)` mutates `items` → every component using the store re-renders (badge, drawer,
checkout totals).

Connects to: Byte 35 (stores), Byte 52 (cart drawer), PART 15.

Remember: the cart store is **memory only** — a refresh clears it.

---

### Byte 11: Vue Router

**Builds on:** Byte 8, Byte 10.

**Concept:** URL → component mapping, guards and scroll policy.

**In plain terms:**

Routes declare which component renders for a path plus metadata (`requiresAuth`,
`requiresAdmin`, `guest`, `title`). A global `beforeEach` guard enforces that metadata, and
`scrollBehavior` decides whether navigation scrolls.

**Why it exists:**

Centralized navigation rules instead of per-link checks.

**The code:**

```js
// frontend/src/router/index.js
const isFilterChange =
  to.path === from.path && ['q', 'category', 'sort', 'page'].some((key) => key in to.query)
if (isFilterChange) return false
return { top: 0 }
```

How to read the code:

Query-only changes on the same page are search/filter actions — the components already animate
their own scroll, so the router must not fight them.

What happens at runtime:

Typing in search → `router.replace({query:{q}})` → no router scroll → the layout's watcher scrolls
smoothly to `#products-section`.

Connects to: Byte 43 (search state), PART 14.

Remember: guards protect UX; the backend still enforces every rule.

---

### Byte 12: Axios

**Builds on:** Byte 8.

**Concept:** The single HTTP door to the API.

**In plain terms:**

`api/client.js` creates one Axios instance with a base URL, 20 s timeout and interceptors that
attach the JWT and normalize responses/errors. Feature modules (`api/products.js`, …) are thin
wrappers over it.

**Why it exists:**

Token injection and error handling are decided once, not in 40 call sites.

**The code:**

```js
// frontend/src/api/client.js
client.interceptors.response.use(
  (response) => response.data,                    // unwrap: callers get the body directly
  (error) => Promise.reject(toApiError(error)),   // normalize: ApiError {message, code, status}
)
```

How to read the code:

Successful calls resolve with the **body** (`client.get(...)` returns the JSON), failures reject
with an `ApiError` carrying a human message.

What happens at runtime:

`listProducts()` → interceptor adds `Authorization: Bearer …` → response body is returned →
`toApiError` maps the `{error:{...}}` envelope if something failed.

Connects to: Byte 36 (API client), Byte 38 (image URLs), PART 16.

Remember: no raw `fetch`/`axios` anywhere else in the app.

---

### Byte 13: FastAPI

**Builds on:** Byte 12.

**Concept:** The Python web framework and its dependency system.

**In plain terms:**

Routes are decorated functions; parameters come from `Depends(...)` (auth, DB sessions),
`Query/Path` (validation) or the Pydantic body. FastAPI serializes responses through
`response_model` and generates `/docs` from the code itself.

**Why it exists:**

Validation, auth and documentation fall out of type hints instead of boilerplate.

**The code:**

```python
# backend/app/api/orders.py
@router.post("", response_model=OrderCreateResponse,
             status_code=status.HTTP_201_CREATED, summary="Place an order")
def place_order(payload: OrderCreate, ...) -> OrderCreateResponse:
    ...
```

How to read the code:

The decorator declares the endpoint, its response schema and status code; `payload` is already
validated as `OrderCreate` before the function body runs.

What happens at runtime:

Request → CORS → route match → dependency resolution (DB session, current user) → body validation
→ handler → service → JSON.

Connects to: Byte 62 (schemas), PART 26.

Remember: handlers stay thin — business rules live in `services/`.

---

### Byte 14: Pydantic

**Builds on:** Byte 13.

**Concept:** Data validation and settings.

**In plain terms:**

Pydantic models declare fields with types, constraints and examples. They are used for request
bodies, response shapes **and** `.env` configuration (`pydantic-settings`).

**Why it exists:**

Invalid input is rejected with structured errors (422) before any business code executes.

**The code:**

```python
# backend/app/schemas/products.py
class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=64,
                     pattern=r"^[A-Za-z0-9][A-Za-z0-9\-_]*$", examples=["WM-001"])
    price: float = Field(gt=0, le=1_000_000, examples=[50.16])
```

How to read the code:

`pattern` enforces the SKU format, `gt=0` rejects free/negative prices — declaratively.

What happens at runtime:

A bad body → FastAPI `RequestValidationError` → the global handler returns 422
`validation_error` with `details.fields[]` the frontend maps onto form inputs.

Connects to: Byte 62 (schemas), Byte 140 (config), PART 27.

Remember: three layers — request schema, response schema, SQLAlchemy model.

---

### Byte 15: SQLAlchemy

**Builds on:** Byte 14.

**Concept:** The ORM mapping Python objects to PostgreSQL rows.

**In plain terms:**

`models/postgres.py` declares `User`, `Order`, `OrderItem` classes; SQLAlchemy creates tables,
generates SQL and tracks changes inside a *session*. Transactions are managed explicitly here
(`begin/commit/rollback`) rather than hidden.

**Why it exists:**

Readable model code with real database constraints underneath.

**The code:**

```python
# backend/app/models/postgres.py
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), ...)
    total_amount = mapped_column(Numeric(12, 2), ...)
```

How to read the code:

Type annotations (`Mapped[int]`) drive column types; `unique/index/ForeignKey` become real
database constraints.

What happens at runtime:

`session.add(order)` stages the object; `flush()` issues `INSERT`; `commit()` makes it durable.

Connects to: Byte 63 (models), Byte 75 (transaction), PART 28.

Remember: `session.flush()` is where constraints actually fire.

---

### Byte 16: PostgreSQL

**Builds on:** Byte 15.

**Concept:** The relational source of truth.

**In plain terms:**

PostgreSQL stores `users`, `orders`, `order_items` with primary keys, foreign keys, CHECK
constraints and indexes. It guarantees that a multi-row order write is all-or-nothing (ACID).

**Why it exists:**

Money requires transactions and exact numerics — nothing else in the stack offers both.

**The code:**

```python
# backend/app/models/postgres.py
__table_args__ = (
    CheckConstraint("role IN ('CUSTOMER', 'ADMIN')", name="ck_users_role"),
)
```

How to read the code:

The database itself rejects impossible data — even if application code were bypassed.

What happens at runtime:

A `role='SUPERADMIN'` insert raises a constraint violation → the transaction rolls back.

Connects to: Byte 75 (transactions), Byte 29 (relationships), PART 9.1.

Remember: PostgreSQL is authoritative; Elasticsearch is not.

---

### Byte 17: MongoDB

**Builds on:** Byte 5.

**Concept:** The document catalog store.

**In plain terms:**

Products are BSON documents in `catalog.products` with nested `attributes`, `tags[]` and
`variants[]`. Queries combine equality (category), array containment (tags), regex text search
(`q`) and sorting/pagination.

**Why it exists:**

Catalog entries differ per product and are read with document-shaped filters.

**The code:**

```python
# backend/app/repositories/mongo/product_repo.py
def ensure_indexes() -> None:
    collection = _collection()
    collection.create_index([("sku", ASCENDING)], unique=True, name="uniq_products_sku")
    collection.create_index([("category", ASCENDING)], name="ix_products_category")
    collection.create_index([("active", ASCENDING)], name="ix_products_active")
```

How to read the code:

Indexes mirror the query patterns: unique SKU (integrity), category filter, active filter,
newest-first sorting (`created_at`).

What happens at runtime:

`GET /api/products?category=audio&visibility=active` becomes
`{category:"audio", active:true}` with a skip/limit cursor.

Connects to: Byte 24 (product document), Byte 148 (repo), PART 9.2.

Remember: `DELETE` here is a **soft delete** (`active:false`).

---

### Byte 18: Elasticsearch

**Builds on:** Byte 7, Byte 16.

**Concept:** The search/analytics projection.

**In plain terms:**

One index, `orders`, holds one document per order. Fields are explicitly mapped (`keyword` for
exact/facets, `search_as_you_type` for name/email, `nested` for items) so queries are predictable
and aggregations return revenue/status KPIs.

**Why it exists:**

Full-text relevance + bucket aggregations in a single query — neither PG nor Mongo does this
cheaply at scale.

**The code:**

```python
# backend/app/repositories/elasticsearch/mappings.py
ORDER_INDEX_MAPPING: dict = {
    # Reject anything that is not described below: no accidental schema drift.
    "dynamic": "strict",
    "properties": {
        "order_id": {"type": "long"},
        "order_number": {"type": "keyword"},
        "status": {"type": "keyword"},
```

How to read the code:

`dynamic: strict` means a field not in the mapping causes an error instead of silent schema
drift; `keyword` makes `terms` filters and facet counts exact.

What happens at runtime:

Index creation (`ensure_index`) applies this mapping once; documents with unknown fields are
rejected at index time.

Connects to: Byte 89 (mapping), Byte 95 (admin search), PART 9.3.

Remember: money is `double` here — analytics only; PostgreSQL keeps exact values.

---

### Byte 19: RabbitMQ

**Builds on:** Byte 6.

**Concept:** The message broker.

**In plain terms:**

A durable post office between processes: FastAPI *publishes* a JSON task message to the
`orders_sync` queue; the Celery worker *consumes* it later. If the worker is briefly down, the
message waits.

**Why it exists:**

It decouples "the order is saved" from "the order is searchable" — checkout never waits on
Elasticsearch.

**The code:**

```python
# backend/app/services/sync_service.py
result = celery_app.send_task(
    settings.sync_task_name,
    kwargs={"order_id": order_id, "reason": reason},
    queue=settings.celery_task_default_queue,   # "orders_sync"
)
```

How to read the code:

Only the **id** and a reason travel — no order contents — so the message stays tiny and the
worker re-reads authoritative data.

What happens at runtime:

On broker failure the exception is caught and reported as `SyncInfo(enqueued=False, error=…)` —
the committed order is untouched.

Connects to: Byte 20 (Celery), Byte 82 (task), PART 11.

Remember: publish happens **after** COMMIT, never inside the transaction.

---

### Byte 20: Celery

**Builds on:** Byte 19.

**Concept:** The background worker runtime.

**In plain terms:**

Celery gives the project a worker process that consumes `orders_sync`, executes the registered
task with retries, time limits and concurrency, and can be configured to run *in-process* for
tests (`task_always_eager`).

**Why it exists:**

Retries, crash-resilience (`acks_late`) and concurrency are non-trivial to hand-roll.

**The code:**

```python
# backend/app/tasks/celery_app.py
celery_app = Celery("ecommerce_orders", broker=settings.broker_url,
                    backend=None,  # results are not needed: the DB + ES are the state
                    )
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_time_limit=120, task_soft_time_limit=90,
)
```

How to read the code:

`backend=None` means nobody reads task results — state lives in the databases;
`acks_late` + `reject_on_worker_lost` re-queue work if a worker dies mid-task.

What happens at runtime:

Compose runs `celery -A app.tasks.celery_app worker --concurrency=2`; it imports
`app.tasks.elasticsearch_tasks` and binds to `orders_sync`.

Connects to: Byte 83 (the task), Byte 86 (failure behaviour), PART 11.

Remember: at-least-once delivery + `_id` upsert = safe duplicates.

---

### Byte 21: Docker

**Builds on:** Byte 5.

**Concept:** Reproducible packaging for the whole polyglot stack.

**In plain terms:**

`docker-compose.yml` defines nine services (4 infrastructure + backend + worker + 2 frontends +
tools), wires them on one network, health-checks them, and mounts named volumes for every
database **and** for uploaded images.

**Why it exists:**

Elasticsearch + RabbitMQ + PostgreSQL + Mongo must start identically on every machine.

**The code:**

```yaml
# docker-compose.yml (backend service excerpt)
backend:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  volumes:
    - ./backend:/app
    - uploads_data:/app/uploads      # product images survive restarts
  depends_on:
    postgres:    { condition: service_healthy }
    mongodb:     { condition: service_healthy }
    elasticsearch:{ condition: service_healthy }
    rabbitmq:    { condition: service_healthy }
```

How to read the code:

`depends_on: service_healthy` enforces startup order; the bind mount gives live code reload; the
named volume persists images.

What happens at runtime:

`docker compose up -d --build` → infra healthchecks pass → backend starts → it turns healthy only
when `/api/health` returns 200 → frontend starts.

Connects to: Bytes 114-118 (compose/health), PART 32.

Remember: `down -v` deletes named volumes — including your uploaded images.

---

### Byte 22: Nginx

**Builds on:** Byte 21, Byte 9.

**Concept:** Production static hosting and reverse proxy.

**In plain terms:**

The `frontend-prod` image is Nginx serving the built SPA with a history-mode fallback, plus two
reverse proxies that keep `/api` and `/uploads` same-origin in production.

**Why it exists:**

Static files don't need Node, and same-origin avoids CORS entirely.

**The code:**

```nginx
# frontend/nginx.conf
location /api/    { proxy_pass http://backend:8000; }
location /uploads/{ proxy_pass http://backend:8000; }
location /        { try_files $uri $uri/ /index.html; }
```

How to read the code:

Paths beginning `/api` and `/uploads` are forwarded to FastAPI; everything else falls back to
`index.html` so client-side routes like `/admin/orders/64` load correctly on refresh.

What happens at runtime:

`http://localhost:8080/api/products` → Nginx → `backend:8000/api/products`.

Connects to: Byte 9 (Vite's dev equivalent), PART 32.

Remember: dev proxy = Vite, prod proxy = Nginx — same URLs from the app's perspective.

---

## SECTION C — DATA

---

### Byte 23: User model

**Builds on:** Byte 16.

**Concept:** The `users` table (identity + role).

**In plain terms:**

A user has `name`, unique `email`, a `password_hash` (bcrypt), and a `role` constrained to
`CUSTOMER` or `ADMIN`. Users own orders through `orders.user_id`.

**Why it exists:**

Authentication data belongs with the transactional store so login and order ownership share keys
and constraints.

**The code:**

```python
# backend/app/models/postgres.py — class User
email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
role: Mapped[str] = mapped_column(String(20), nullable=False, default="CUSTOMER")
orders: Mapped[list["Order"]] = relationship(
    back_populates="user", lazy="raise", passive_deletes=True
)
```

How to read the code:

`unique=True` prevents duplicate accounts; `lazy="raise"` stops accidental user→orders loads
(the API always queries orders explicitly).

What happens at runtime:

Seed writes 8 users with hashed passwords; login queries `User.email == email` and verifies the
hash.

Connects to: Byte 66 (login), Byte 29 (relationships), PART 9.1.

Remember: role values are `CUSTOMER` / `ADMIN` — enforced by a CHECK constraint.

---

### Byte 24: Product document

**Builds on:** Byte 17.

**Concept:** The shape of a catalog entry.

**In plain terms:**

A product carries identity (`sku`), display fields (`title`, `description`, `image_url`),
commerce fields (`price`, `active`), and flexible structures: `category`, `tags[]`,
`attributes{}` and `variants[]`.

**Why it exists:**

Everything the storefront card, filters and admin form need lives in one document — no joins.

**The code:**

```python
# backend/app/schemas/products.py — ProductBase
title: str = Field(min_length=2, max_length=200, examples=["Wireless Mouse"])
price: float = Field(gt=0, le=1_000_000, examples=[50.16])
category: str = Field(min_length=2, max_length=64, examples=["peripherals"])
tags: list[str] = Field(default_factory=list, max_length=30)
attributes: dict[str, Any] = Field(default_factory=dict)
variants: list[VariantCreate] = Field(default_factory=list, max_length=20)
active: bool = True
```

How to read the code:

`attributes` is free-form (e.g. `{color, dpi}`), `variants` are nested sub-documents with their
own sku/color/stock — the reason MongoDB was chosen.

What happens at runtime:

`GET /api/products` normalizes each document (`_to_response`) so the API always returns `id`,
defaulted optional fields, and `image_url`.

Connects to: Byte 17 (Mongo repo), Byte 49 (product card), PART 9.2.

Remember: API field is `id`, never `_id`; `active:false` hides a product from the storefront.

---

### Byte 25: Order

**Builds on:** Byte 16, Byte 23.

**Concept:** The order header row.

**In plain terms:**

An order has a human-readable unique `order_number` (`ORD-000064`), a customer FK, a `status`
(`PENDING|PROCESSING|SHIPPED`), an exact `total_amount`, timestamps, and a nullable
`search_indexed_at` written by the worker.

**Why it exists:**

One row per purchase is the anchor for items, search documents and status history.

**The code:**

```python
# backend/app/services/order_service.py
session.add(order)
session.flush()                              # INSERT orders -> order.id
order.order_number = f"ORD-{order.id:06d}"   # human readable number
```

How to read the code:

The number can only be derived after the row exists, so a temporary `TMP-…` value is inserted
first and immediately replaced.

What happens at runtime:

Id `64` → `ORD-000064`; the unique index guarantees no collisions.

Connects to: Byte 26 (items), Byte 75 (transaction), PART 9.1.

Remember: `total_amount` is recomputed server-side, never taken from the client.

---

### Byte 26: Order item

**Builds on:** Byte 25.

**Concept:** The line rows — including the snapshots.

**In plain terms:**

Each line stores `product_id` (text reference to MongoDB), **`title` and `unit_price` snapshots**,
`quantity`, and `line_total`, all under the parent order with CHECK constraints.

**Why it exists:**

The line is where "what was actually sold" is frozen; the FK cascade keeps items with their
order.

**The code:**

```python
# backend/app/services/order_service.py
for line in lines:
    session.add(OrderItem(
        order=order,
        product_id=line.product_id,
        title=line.title,              # snapshot of MongoDB title
        quantity=line.quantity,
        unit_price=line.unit_price,    # snapshot of MongoDB price
    ))
session.flush()   # INSERT order_items (CHECK constraints run here)
```

How to read the code:

Comments mark the snapshot moment; `flush()` triggers all CHECKs before commit so a bad line
rolls back the whole order.

What happens at runtime:

If any line violates `unit_price > 0`, the insert raises → `rollback()` → zero rows.

Connects to: Byte 27 (snapshot semantics), Byte 75 (transaction), PART 36.

Remember: `product_id` is a plain string — there is no cross-database foreign key.

---

### Byte 27: Product snapshot

**Builds on:** Byte 26.

**Concept:** Live data vs. historical record.

**In plain terms:**

At purchase time the current `title`/`price` are *copied* into `order_items`. Afterwards the
catalog can change freely: the storefront shows the new values, old orders keep the old ones —
and Elasticsearch, rebuilt from PostgreSQL, keeps them too.

**Why it exists:**

Orders are financial history; mutable references would rewrite receipts and revenue.

**The code:**

```python
# backend/app/services/order_service.py — resolve_cart()
raw_price = product.get("price")
if raw_price is None:
    raise UnprocessableError(..., code="invalid_price", ...)
unit_price = to_money(raw_price)      # Decimal, 2 dp, ROUND_HALF_UP
lines.append(ResolvedLine(product_id=..., title=str(product.get("title", "")).strip(),
                          quantity=requested.quantity, unit_price=unit_price))
```

How to read the code:

`resolve_cart` is the *only* place prices are read — once per order, into immutable
`ResolvedLine` values.

What happens at runtime:

Seed renames `Wireless Mouse ($50.16)` → `Wireless Mouse Pro ($60.00)` after orders exist; old
orders still read `Wireless Mouse / 50.16`.

Connects to: Byte 132 (snapshot drift), Byte 147 (document builder), PART 36.

Remember: cart snapshots are UX; order snapshots are law.

---

### Byte 28: Elasticsearch order document

**Builds on:** Byte 18, Byte 27.

**Concept:** The projection's record shape.

**In plain terms:**

One document per order: identity, status, dates, `total_amount`, a flattened `customer` object
and a `nested` `items` array — all built from PostgreSQL, addressed by `_id = order_id`.

**Why it exists:**

Search needs customer names and item titles at the top level of a *single* document so one query
can match across them.

**The code:**

```python
# backend/app/repositories/elasticsearch/document.py
document: dict[str, Any] = {
    "order_id": int(order.id),
    "order_number": order.order_number,
    "status": order.status,
    "total_amount": _money(order.total_amount),     # float, 2 dp
    "customer": {"id": int(order.user_id), "name": ..., "email": ...},
    "items": [ ... snapshots from order.items ... ],
}
```

How to read the code:

`_money()` converts Decimal → float for analytics; `customer` is an object (not nested) because
an order has exactly one customer, while `items` must stay `nested`.

What happens at runtime:

The worker builds this dict and PUTs it at `_doc/64`; re-running overwrites it identically.

Connects to: Byte 29 (relationships), Byte 84 (idempotency), PART 37.

Remember: it is a copy — dropping the index loses nothing but search.

---

### Byte 29: Relationships

**Builds on:** Byte 23, Byte 25, Byte 26.

**Concept:** How the entities connect — and where they deliberately don't.

**In plain terms:**

```
users 1 ──< orders 1 ──< order_items
order_items.product_id  ···▶  MongoDB products._id   (text, no FK)
products.image_url      ···▶  disk /uploads/products/…
orders (PG)             ···▶  ES orders doc (_id = order_id)  via worker
```

**Why it exists:**

Real referential integrity where it matters (money ↔ customer ↔ lines); loose references where
stores differ (catalog, search, files).

**The code:**

```python
# backend/app/models/postgres.py (conceptual — OrderItem)
order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), ...)
product_id: Mapped[str] = mapped_column(String(64), ...)   # cross-store reference
```

How to read the code:

`ondelete="CASCADE"` keeps items with their order; `product_id` as a string is the intentional
gap between PostgreSQL and MongoDB.

What happens at runtime:

Deleting a *product* (soft) never breaks an order; the order still shows its snapshot title.

Connects to: Byte 26, Byte 28, PART 9.

Remember: integrity inside each store, snapshots across stores.

---

## SECTION D — FRONTEND

---

### Byte 30: Frontend entry point

**Builds on:** Byte 8.

**Concept:** What happens before the first paint.

**In plain terms:**

`index.html` loads `main.js`, which installs Pinia and the router, imports the two global
stylesheets, and mounts `App.vue`. `App.vue` renders `<router-view>` plus the toast host and
validates any stored token.

**Why it exists:**

A single, obvious bootstrap point for plugins and global concerns.

**The code:**

```js
// frontend/src/App.vue
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
authStore.init()
```

How to read the code:

`init()` calls `fetchMe()` when a token exists — quietly clearing an expired session before the
guard has to.

What happens at runtime:

Page load → mount → `GET /api/auth/me` (if logged in) → router renders the route.

Connects to: Byte 31 (router), Byte 67 (JWT), PART 13.

Remember: `ToastHost` is global — toasts work from any view.

---

### Byte 31: Router

**Builds on:** Byte 30.

**Concept:** The route table and its guards.

**In plain terms:**

Two layouts host the views: `StorefrontLayout` (`/`, `/checkout`) and `AdminLayout`
(`/admin/*`, guarded). `/login` is a guest-only route; unknown paths fall back to the storefront.

**Why it exists:**

Grouping by layout keeps chrome (header/footer, admin nav) out of individual views.

**The code:**

```js
// frontend/src/router/index.js
{
  path: '/admin',
  component: AdminLayout,
  meta: { requiresAuth: true, requiresAdmin: true },
  children: [
    { path: '', redirect: { name: 'admin-search' } },
    { path: 'search', name: 'admin-search', ... },
    { path: 'orders/:id', name: 'order-details', ... },
    { path: 'catalog', name: 'catalog-admin', ... },
  ],
},
```

How to read the code:

Meta on the parent applies to every child (`to.matched.some(...)` in the guard); `/admin`
redirects to the search screen.

What happens at runtime:

Unauthenticated visit → `/login?redirect=/admin/search`; customer (non-admin) → redirected to
storefront.

Connects to: Byte 11, Byte 72, PART 14.

Remember: `scrollBehavior` returns `false` for filter/search query changes.

---

### Byte 32: Layouts

**Builds on:** Byte 31.

**Concept:** Persistent chrome around views.

**In plain terms:**

`StorefrontLayout` renders the announcement bar, sticky header (brand, nav, the single search,
account, cart button), `<router-view>`, the footer, and the cart drawer. `AdminLayout` provides
the admin navigation shell.

**Why it exists:**

Search, cart and auth controls are shared by all storefront pages — they belong to the layout.

**The code:**

```vue
<!-- frontend/src/layouts/StorefrontLayout.vue -->
<CartDrawer
  id="cart-drawer"
  :open="cartOpen"
  @close="cartOpen = false"
  @checkout="goToCheckout"
/>
```

How to read the code:

The layout owns the `cartOpen` flag that pairs the header button state with the drawer.

What happens at runtime:

Clicking the cart button toggles `cartOpen` → `.cart-btn--open` moves the button left and the
drawer slides in from the right.

Connects to: Byte 43 (header/search), Byte 52 (cart drawer), PART 17.

Remember: the mobile nav panel reuses the same `searchInput` — one logical search.

---

### Byte 33: Views

**Builds on:** Byte 31, Byte 32.

**Concept:** One view per screen; data fetching lives here.

**In plain terms:**

Six views: `StorefrontView`, `CheckoutView`, `LoginView`, `AdminSearchView`,
`OrderDetailsView`, `CatalogAdminView`. Each owns its loading/error state and calls `api/*`
functions.

**Why it exists:**

Views orchestrate; components render. This keeps data flow readable.

**The code:**

```js
// frontend/src/views/StorefrontView.vue
async function load() {
  // ...
  const data = await listProducts(params)
  // ...
}
watch([() => route.query.q, category, sort], () => { /* refetch */ })
watch(page, load, { immediate: true })
```

How to read the code:

Watches tie URL state to fetching — the URL *is* the filter state, so back/forward work.

What happens at runtime:

`?q=bluetooth` changes → watcher fires → `load()` → grid re-renders.

Connects to: Byte 34 (components), Byte 48 (product grid), PART 17.

Remember: `immediate: true` performs the first fetch without a separate `onMounted`.

---

### Byte 34: Components

**Builds on:** Byte 33.

**Concept:** Reusable, prop-driven UI pieces.

**In plain terms:**

Components are split into `common` (generic kit: buttons, inputs, modals, drawers, badges,
skeletons), `storefront`, `admin` and `checkout`. They receive data via props and emit events
upward — no network calls inside `common`.

**Why it exists:**

Testable, themeable building blocks that guarantee consistent behaviour (no browser-default
controls anywhere).

**The code:**

```vue
<!-- frontend/src/components/storefront/ProductCard.vue -->
<BaseButton
  class="product-card__cta"
  :variant="state === 'added' ? 'secondary' : 'primary'"
  :disabled="state === 'added'"
  @click="onAdd"
>
```

How to read the code:

The card doesn't call the API or the store directly — it *emits* upward, so the parent decides
(adds to cart, shows a toast).

What happens at runtime:

`@add` bubbles to `ProductGrid` → `StorefrontView.addToCart()` → `cart.add()`.

Connects to: Byte 35 (stores), Byte 49 (card anatomy), PART 24.6.

Remember: props in, events out; shared state only via Pinia.

---

### Byte 35: Stores

**Builds on:** Byte 10, Byte 34.

**Concept:** The three Pinia stores and their boundaries.

**In plain terms:**

`auth` (token/user/role, localStorage-backed), `cart` (items, clamped quantities, snapshot
prices, memory-only), `toast` (queue capped at 5). Everything else stays in view-local refs.

**Why it exists:**

Cross-component state without prop drilling — while avoiding a cache layer that could go stale.

**The code:**

```js
// frontend/src/stores/auth.js
getters: {
  isAuthenticated: (state) => !!state.token && !!state.user,
  isAdmin: (state) => state.user?.role === 'ADMIN',
},
```

How to read the code:

Guards and templates consume `isAdmin` — one definition of "is this user an admin" for UX.

What happens at runtime:

Login stores the token → header, nav guard and admin routes react immediately.

Connects to: Byte 67 (JWT), Byte 52 (cart), PART 15.

Remember: server data (products, orders, search results) deliberately does **not** live in stores.

---

### Byte 36: API client

**Builds on:** Byte 12, Byte 35.

**Concept:** Endpoint modules + error normalization.

**In plain terms:**

`api/client.js` is the transport; `api/products.js`, `api/orders.js`, `api/search.js`,
`api/users.js` are typed wrappers. Errors become `ApiError {message, code, status, details}` so
UI code can show a useful sentence.

**Why it exists:**

One place decides base URL, auth header, timeout and how failures read.

**The code:**

```js
// frontend/src/api/client.js
export function toApiError(error) {
  const response = error?.response
  if (response) {
    const envelope = response.data?.error
    if (envelope && typeof envelope.message === 'string') {
      return new ApiError(envelope.message, { code: envelope.code, status: response.status,
                                              details: envelope.details ?? null })
    }
    // ...
```

How to read the code:

It understands the backend's `{"error": {code, message, details}}` envelope; other shapes fall
back to generic messages (this is why 401/403, which use `{"detail"}`, read generically).

What happens at runtime:

Every rejection passes through `toApiError` in the response interceptor, so views always catch an
`ApiError`.

Connects to: Byte 12, Byte 68, PART 16, PART 30.

Remember: `API_BASE_URL` from this module is also used to prefix uploaded image URLs.

---

### Byte 37: Currency utility

**Builds on:** Byte 24.

**Concept:** The single money formatter (₹).

**In plain terms:**

All customer-facing money goes through `formatCurrency()` — `Intl.NumberFormat('en-IN',
{style:'currency', currency:'INR'})` — producing `₹1,234.56`. `formatNumber` uses Indian grouping;
`parseAmount` coerces input defensively; unusable values render `—`.

**Why it exists:**

A requirement (all prices in ₹) enforced by one function rather than scattered formatting.

**The code:**

```js
// frontend/src/utils/currency.js
export function formatCurrency(value) {
  if (value === null || value === undefined || value === '') return '—'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return '—'
  return formatter.format(amount)
}
```

How to read the code:

Defensive guards first — a `null` price from the API renders an em dash instead of `NaN`.

What happens at runtime:

`formatCurrency(229)` → `₹229.00`; cart subtotal, order totals and KPIs all use it.

Connects to: Byte 40 (responsive/typography), PART 24.5.

Remember: never hand-build price strings — `Intl` already handles locale grouping.

---

### Byte 38: Image utility

**Builds on:** Byte 36, Byte 24.

**Concept:** Turning a stored `image_url` into a loadable source.

**In plain terms:**

`resolveImageUrl(value)` passes through absolute/`data:`/`blob:` URLs, prefixes `/uploads/…`
with the API origin *only when one is configured*, and leaves bundled asset paths (`/products/…`)
relative.

**Why it exists:**

The same stored value must work behind the Vite proxy, the Nginx proxy, and a direct-API setup.

**The code:**

```js
// frontend/src/utils/image.js
export function resolveImageUrl(value) {
  const url = typeof value === 'string' ? value.trim() : ''
  if (!url) return null
  if (EXTERNAL.test(url) || DATA_LIKE.test(url)) return url
  if (url.startsWith('/uploads/') && API_BASE_URL) return `${API_BASE_URL}${url}`
  return url
}
```

How to read the code:

Three branches: external/data → untouched; backend uploads → prefixed when an origin exists;
otherwise relative (same-origin, proxy-friendly).

What happens at runtime:

`/uploads/products/ab12.webp` becomes `http://localhost:8000/uploads/products/ab12.webp` in dev,
or stays relative when `VITE_API_BASE_URL=''`.

Connects to: Byte 96 (image_url), Byte 100 (upload validation), PART 23.

Remember: returning `null` means "no image" — the component shows the placeholder.

---

### Byte 39: Design tokens

**Builds on:** Byte 8.

**Concept:** Central CSS variables for colour, space and type.

**In plain terms:**

`styles/tokens.css` defines the palette (accent `#FFAC1C`, `--color-ink`, surfaces, borders), the
4/8/12/16/20/24/32/40/48/64 spacing scale, text sizes/weights, radii, shadows and the content
width (`--content-max: 1320px`, `--container-pad: 32/24/16px`).

**Why it exists:**

Consistent visual language and one-line theme changes; no browser-default colours or sizes leak
through.

**The code:**

```css
/* frontend/src/styles/utilities.css — the single content container */
.container {
  width: 100%;
  max-width: var(--content-max);
  margin-inline: auto;
  padding-inline: var(--container-pad);
}
```

How to read the code:

Every section wraps its content in `.container`, so padding changes per breakpoint in one place.

What happens at runtime:

At ≤768 px `--container-pad` becomes 16 px (media query on `:root`), affecting all sections at
once.

Connects to: Byte 40 (responsive), PART 17.

Remember: accent `#FFAC1C` is an **accent** — primary surfaces use ink/surface tokens.

---

### Byte 40: Responsive utilities

**Builds on:** Byte 39.

**Concept:** Layout helpers and breakpoint behaviour.

**In plain terms:**

Utility classes (`only-mobile`, `hide-mobile`, `hide-sm`, `sr-only`, `truncate`, `tabular`,
`.table-scroll`) plus component-level media queries drive behaviour at 1920/1440/1280/1024/768/414/375.

**Why it exists:**

Show/hide decisions are expressed in markup instead of scattering media queries.

**The code:**

```css
/* frontend/src/styles/utilities.css */
.table-scroll { position: relative; }   /* keeps .sr-only (absolute) inside the clipper */
```

How to read the code:

`.table-scroll` is a horizontally scrollable wrapper; making it `position: relative` traps the
absolutely-positioned `.sr-only` span so it can't widen the document (the 375 px overflow bug).

What happens at runtime:

Wide tables scroll inside their box; `document.scrollWidth === window.innerWidth` at every
breakpoint.

Connects to: Byte 39, PART 39 (gotcha #20).

Remember: skeleton + reduced-motion states are part of responsiveness too
(`transition-duration: 0.01ms` under `prefers-reduced-motion`).

---

## SECTION E — STOREFRONT

---

### Byte 41: Announcement bar

**Builds on:** Byte 39.

**Concept:** The topmost marketing strip.

**In plain terms:**

A static bar at the very top of `StorefrontLayout` showing the free-shipping threshold (₹5,000)
with a **Shop the collection** button that scrolls to the product grid.

**Why it exists:**

Persistent, non-interactive-by-default messaging that still offers a direct path to products.

**The code:**

```vue
<!-- frontend/src/layouts/StorefrontLayout.vue -->
<p class="announce__text">
  Free shipping on orders over <strong>₹5,000</strong>
  <span class="announce__divider" aria-hidden="true">•</span>
  <button type="button" class="announce__cta" @click="goToProducts">
    Shop the collection
  </button>
</p>
```

How to read the code:

It reuses `goToProducts()` — the same navigation helper as the header links, so behaviour is
consistent (and reduced-motion aware).

What happens at runtime:

Click → nav closes → smooth scroll to `#products-section` (offset −96 px for the sticky header).

Connects to: Byte 42 (navigation), PART 17.

Remember: it is layout-level markup, not a view — it persists on checkout too.

---

### Byte 42: Navigation

**Builds on:** Byte 41.

**Concept:** Header navigation and the mobile panel.

**In plain terms:**

Desktop: brand + `Store / Categories / Deals / New Arrivals` + an `Admin` link that only appears
for admins + account + cart. Mobile: hamburger toggles a panel containing the same links, the
search input and account controls.

**Why it exists:**

One information architecture with two presentations; admin visibility is role-driven.

**The code:**

```vue
<RouterLink
  v-if="authStore.isAdmin"
  to="/admin/search"
  class="header__link header__link--admin"
>
  Admin
</RouterLink>
```

How to read the code:

`v-if` hides the entry point for customers (UX only — the route guard and `require_admin` are the
real barriers).

What happens at runtime:

Each nav item either scrolls to an in-page section or routes; `watch(() => route.fullPath)`
auto-closes the mobile panel on navigation.

Connects to: Byte 31 (guards), Byte 57 (admin dependency), PART 17.

Remember: nav links use `#section` anchors with `@click.prevent` — they never navigate away.

---

### Byte 43: Search

**Builds on:** Byte 42, Byte 33.

**Concept:** The single, URL-driven product search.

**In plain terms:**

The header's compact input expands on focus; typing (debounced 260 ms) writes `?q=` to the URL;
the view fetches `GET /api/products?q=…` and scrolls to the grid. `/` or `⌘/Ctrl+K` focuses it.

**Why it exists:**

URL state makes search shareable, bookmarkable and back-button friendly, with exactly one
search experience in the app.

**The code:**

```js
// frontend/src/layouts/StorefrontLayout.vue
const syncSearch = debounce((value) => {
  const query = { ...route.query }
  const trimmed = String(value || '').trim()
  if (trimmed) query.q = trimmed
  else delete query.q
  delete query.page
  router.replace({ query }).catch(() => {})
}, 260)

watch(searchInput, (value) => syncSearch(value))
```

How to read the code:

`router.replace` (not push) avoids a history entry per keystroke; dropping `page` keeps results
on page 1; other query keys (`category`, `sort`) are preserved.

What happens at runtime:

Input → debounce → URL → `StorefrontView` watcher → `listProducts({q})` → grid → scroll to
`#products-section`.

Connects to: Byte 31 (scrollBehavior), Byte 48 (grid), PART 18.

Remember: product search hits **MongoDB**; admin order search is a different endpoint
(`/api/search/orders`, Elasticsearch).

---

### Byte 44: Hero

**Builds on:** Byte 33.

**Concept:** The dynamic landing panel.

**In plain terms:**

A dark (`--color-ink`) hero card with an orange glow that showcases the newest products: one
featured product plus two previews, each addable to the cart. While loading it shows a skeleton;
if the catalog fails it renders an explanatory fallback instead of an empty rectangle.

**Why it exists:**

Above-the-fold product presence that is *data-driven* — no hardcoded products anywhere.

**The code:**

```js
// frontend/src/components/storefront/HeroSection.vue
async function loadHeroProducts() {
  loading.value = true
  try {
    const data = await listProducts({ limit: 5, sort: 'newest', visibility: 'active' })
    items.value = data.items || []
  } finally {
    loading.value = false
  }
}
onMounted(loadHeroProducts)
```

How to read the code:

`finally` guarantees `loading` flips false even on error — the component then shows the
`hero__fallback` panel rather than a permanent skeleton.

What happens at runtime:

Mount → request → skeleton or content; `featured = items[0]`, `previews = items.slice(1,3)`.

Connects to: Byte 45 (dynamic products), Byte 48 (grid), PART 17.

Remember: hero, grid and categories are three independent readers of the same catalog endpoint.

---

### Byte 45: Dynamic products

**Builds on:** Byte 44.

**Concept:** Everything product-related comes from the API.

**In plain terms:**

No product, price, category or tag in the storefront is baked into the frontend. Cards, hero,
facets and marquee all derive from `GET /api/products` and `GET /api/products/facets`.

**Why it exists:**

The storefront must reflect the live catalog, including admin edits and soft-deleted items
disappearing.

**The code:**

```js
// frontend/src/views/StorefrontView.vue (load())
const data = await listProducts(params)   // params: q, category, sort, page, limit, visibility
```

How to read the code:

`params` is assembled from URL query state, so one function serves every filter combination.

What happens at runtime:

Any query change → watcher → `load()` → items/pages/total update → grid re-renders.

Connects to: Byte 33, Byte 36, PART 8 (flows 1–3).

Remember: `visibility=active` is what hides deactivated products from customers.

---

### Byte 46: Categories

**Builds on:** Byte 45.

**Concept:** The horizontal category rail.

**In plain terms:**

Rectangular category cards in a horizontally scrollable rail (scrollbar hidden), one per
category, that set `?category=` and jump to the grid. Facet counts can accompany them.

**Why it exists:**

Discoverability: one tap narrows the catalog without a sidebar.

**The code:**

```vue
<!-- frontend/src/components/storefront/CategorySection.vue (behaviour) -->
<!-- rail: overflow-x auto, scrollbar hidden, rectangular cards -->
<!-- click → route.query.category = <value> → StorefrontView watcher → load() -->
```

How to read the code:

Category selection is again **URL state** — no local component state — so refresh/back work.

What happens at runtime:

Click card → `pushQuery({category})` → page resets to 1 → Mongo equality filter → grid updates.

Connects to: Byte 17 (Mongo indexes), Byte 47 (tags), PART 8 (flow 3).

Remember: footer category links run the same `goCategory()` helper.

---

### Byte 47: Trending tags

**Builds on:** Byte 46.

**Concept:** The right-to-left tag marquee.

**In plain terms:**

Individual tag pills scroll right-to-left continuously; hovering or touching pauses them; clicking
a pill runs a **global search** (`?q=tag`). Under `prefers-reduced-motion` the marquee stops and
the row becomes natively scrollable (verified: 40 static pills).

**Why it exists:**

A lively discovery surface that degrades gracefully for reduced-motion users.

**The code:**

```vue
<!-- frontend/src/components/storefront/TagMarquee.vue → TagPill -->
<!-- TagPill click → sets route.query.q = tag (global search, not a filter mode) -->
```

How to read the code:

Tags are treated as *search terms*, which is why they reuse the single search pipeline instead of
introducing a second filtering mechanism.

What happens at runtime:

Loop period is driven by per-item `margin-right` + `width: max-content`; pause sets
`animation-play-state: paused` on hover/touch.

Connects to: Byte 43 (search), Byte 49 (product card), PART 17.

Remember: a tag click and a header search produce the same `?q=` result.

---

### Byte 48: Product grid

**Builds on:** Byte 45.

**Concept:** The collection section with its three states.

**In plain terms:**

`ProductGrid` renders 4 → 3 → 2 → 1 columns across breakpoints, showing exactly one of: loading
skeletons (8 placeholders), an error state with **Retry**, an empty state with **Clear**, or the
cards themselves — followed by `AppPagination`.

**Why it exists:**

Users always see meaningful feedback; the layout never collapses into a blank rectangle.

**The code:**

```vue
<!-- frontend/src/components/storefront/ProductGrid.vue -->
<div v-if="loading" class="product-grid__skeleton" aria-hidden="true"> …8 skeletons… </div>
<div v-else-if="error" class="product-grid__error"> …<BaseButton @click="emit('retry')">Retry</BaseButton>… </div>
<div v-else-if="!items.length" class="product-grid__empty"> …<BaseButton @click="emit('clear')">…</div>
<div v-else class="product-grid__items"> <ProductCard … @add="emit('add', $event)" /> </div>
```

How to read the code:

Mutually exclusive branches keyed by `loading`/`error`/emptiness; the grid is a pure renderer —
the view does the fetching.

What happens at runtime:

While fetching, skeletons preserve layout height (no jump); on failure the user can retry without
reloading the page.

Connects to: Byte 49 (card), Byte 50 (pagination), PART 17.

Remember: skeleton → content transitions must never leave elements stuck at `opacity: 0`.

---

### Byte 49: Product card

**Builds on:** Byte 48, Byte 37.

**Concept:** The canonical card anatomy.

**In plain terms:**

Fixed order: **IMAGE → CATEGORY → TITLE → DESC → PRICE → ADD TO CART**, with an optional
wishlist heart on the image. Title and description clamp to two lines; the button sits at the
bottom via `margin-top: auto`, so heights stay uniform across a row.

**Why it exists:**

Consistency across breakpoints and content lengths — no reflow, no truncation surprises.

**The code:**

```css
/* frontend/src/components/storefront/ProductCard.vue */
.product-card__title  { -webkit-line-clamp: 2; overflow: hidden; overflow-wrap: anywhere; }
.product-card__desc   { -webkit-line-clamp: 2; overflow: hidden; }
.product-card__cta    { margin-top: auto; }   /* button always last, always visible */
```

How to read the code:

Clamping controls vertical rhythm; `margin-top: auto` pins the CTA to the card bottom regardless
of description length; `overflow-wrap: anywhere` stops long tokens from widening the card.

What happens at runtime:

Add click → parent `onAdd` → cart store → button flips to "added" (checkmark, disabled,
`secondary` variant).

Connects to: Byte 34 (component contract), Byte 52 (drawer), PART 19.

Remember: price always renders through `formatCurrency` (₹).

---

### Byte 50: Pagination

**Builds on:** Byte 48.

**Concept:** Page navigation with guard rails.

**In plain terms:**

`AppPagination` shows total + "page X of Y" and prev/next controls with page dots. It emits
`update:page`, ignores clicks while loading, and clamps to `1..pages`.

**Why it exists:**

One pagination control reused by storefront and admin search with identical behaviour.

**The code:**

```js
// frontend/src/components/common/AppPagination.vue
function go(nextPage) {
  if (props.loading) return
  if (nextPage < 1 || nextPage > props.pages || nextPage === props.page) return
  emit('update:page', nextPage)
}
```

How to read the code:

Guard clauses prevent out-of-range requests and double-fire during fetches.

What happens at runtime:

`setPage(n)` in the view updates `?page=` (watcher refetches) — and any filter/search change
resets `page` to 1.

Connects to: Byte 43 (query resets), PART 17.

Remember: storefront default `limit=12` (view), API default 24, max 100.

---

### Byte 51: Cart button

**Builds on:** Byte 32, Byte 49.

**Concept:** The prominent header cart control.

**In plain terms:**

An orange primary pill with a bag icon, "Cart" label and a live badge of `cart.itemCount`. When
the drawer opens it translates −10 px and inverts to ink/orange, visually "handing off" to the
drawer.

**Why it exists:**

The cart must be the most obvious action in the header and give feedback while open.

**The code:**

```css
/* frontend/src/layouts/StorefrontLayout.vue */
.cart-btn--open {
  transform: translateX(-10px);
  background: var(--color-ink);
  border-color: var(--color-ink);
  color: var(--color-primary);
}
```

How to read the code:

The same class is bound by `:class="{ 'cart-btn--open': cartOpen }"` — button and drawer state
are one boolean.

What happens at runtime:

Toggle → button slides left and inverts → drawer slides in → badge pops (`badge-pop` animation).

Connects to: Byte 52 (drawer), PART 17.

Remember: `aria-expanded` / `aria-controls="cart-drawer"` keep it accessible.

---

### Byte 52: Cart drawer

**Builds on:** Byte 51, Byte 35.

**Concept:** The slide-in cart panel.

**In plain terms:**

`CartDrawer` wraps the generic `AppDrawer` (teleported to `<body>`, backdrop, Esc/backdrop close,
body scroll lock). It shows either the empty state ("Your cart is empty" + **Browse products**) or
line items with quantity steppers, subtotal and **Checkout**.

**Why it exists:**

Reviewing and adjusting the cart without leaving the current page.

**The code:**

```js
// frontend/src/components/common/AppDrawer.vue
watch(() => props.open, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
  if (open) window.addEventListener('keydown', onKeydown)
  else window.removeEventListener('keydown', onKeydown)
})
```

How to read the code:

Scroll locking prevents background scrolling while the dialog is open; listeners are removed on
close and on unmount (no leaks).

What happens at runtime:

Open → body scroll locked → `translateX(24px)` enter transition (≈250 ms, `--transition`) →
close restores scroll. On ≤414 px the 440 px width collapses to viewport width via
`max-width: 100vw`.

Connects to: Byte 35 (store), Byte 53 (checkout), PART 20.

Remember: quantity is clamped 1..100 in the store, not just in the input.

---

### Byte 53: Checkout

**Builds on:** Byte 52, Byte 27.

**Concept:** Cart → validated order.

**In plain terms:**

`/checkout` (login required) re-reads live prices, lists lines and totals, then posts
`{items:[{product_id, quantity}]}` — no prices. On success the server's order is shown, the cart
clears, and a toast reports `ORD-… ₹…`.

**Why it exists:**

The one place where client state becomes a durable, transactional record.

**The code:**

```js
// frontend/src/views/CheckoutView.vue
const order = await createOrder({
  items: cart.lines.map((line) => ({ product_id: line.id, quantity: line.quantity })),
})
placedOrder.value = order
cart.clear()
toast.success(`Order ${order.order_number} placed — ${formatCurrency(order.total_amount)}.`)
```

How to read the code:

Only identity + quantity cross the wire; `placedOrder` switches the view to the success panel;
`cart.clear()` runs **only after** success (failures keep the cart intact).

What happens at runtime:

POST → server validates/prices/commits → response carries the order + `sync` info → UI celebrates.

Connects to: Byte 75 (transaction), Byte 79 (sync trigger), PART 21.

Remember: a failed place leaves the cart untouched and shows the server's message.

---

## SECTION F — BACKEND

---

### Byte 54: FastAPI application startup

**Builds on:** Byte 13.

**Concept:** What happens when the process boots.

**In plain terms:**

Importing `app.main` builds the app (CORS, error handlers, routers, `/uploads` mount). The
*lifespan* then ensures infrastructure: create PostgreSQL tables, ensure MongoDB indexes, ensure
the Elasticsearch index — PG is required, the others are best-effort with warnings.

**Why it exists:**

Schema/index creation is idempotent bootstrap, not something a developer should run manually.

**The code:**

```python
# backend/app/main.py
def init_infrastructure() -> None:
    """Create schema/indexes at startup. Each step is best-effort except PG."""
    from app.core.database import create_tables
    from app.repositories.elasticsearch.orders_repo import ensure_index
    from app.services.product_service import ensure_catalog_indexes

    create_tables()
    try:
        ensure_catalog_indexes()
    except Exception as exc:
        logger.warning("could not ensure MongoDB indexes: %s", exc)
```

How to read the code:

`create_tables()` is unguarded (PostgreSQL must work); Mongo/ES are wrapped so a slow cluster
doesn't crash the API — they'll be retried on next start or by `ensure_index()` during tasks.

What happens at runtime:

`uvicorn app.main:app` → import (mount `/uploads`, register routes) → lifespan → ready to serve.

Connects to: Byte 58 (product routes), Byte 118 (health), PART 26.

Remember: shutdown closes Mongo/ES clients and disposes the PG engine.

---

### Byte 55: Routing

**Builds on:** Byte 54.

**Concept:** How URLs map to handlers.

**In plain terms:**

Six routers with prefixes: `/api/products` (Mongo), `/api/orders` (PG), `/api/users` (PG),
`/api/search` (ES), `/api/auth`, `/api/health`. Each declares response models, tags and error
responses that shape `/docs`.

**Why it exists:**

Grouping by domain keeps one data store per router — mirroring the polyglot boundaries.

**The code:**

```python
# backend/app/main.py
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(auth.router)
app.include_router(health.router)
```

How to read the code:

Registration order is irrelevant to matching (prefixes differ); `/` is defined inline for service
metadata.

What happens at runtime:

`PATCH /api/orders/64/status` → `orders.router` (prefix `/api/orders`, path `/{id}/status`) →
dependencies → handler.

Connects to: Bytes 58-60 (route families), PART 26.

Remember: `/uploads` is a mounted static app, not a route.

---

### Byte 56: Authentication dependency

**Builds on:** Byte 15, Byte 65.

**Concept:** Resolving the caller from a bearer token.

**In plain terms:**

`get_current_user` reads the `Authorization` header (optional bearer), decodes the JWT, takes the
`sub` user id, loads the user from PostgreSQL, and raises 401 on any failure.

**Why it exists:**

Auth logic written once and injected wherever needed via `Depends`.

**The code:**

```python
# backend/app/core/auth.py
payload = decode_access_token(credentials.credentials)
if payload is None:
    raise credentials_exception

user_id: int | None = payload.get("sub")
if user_id is None:
    raise credentials_exception

user = db.get(User, user_id)
if user is None:
    raise credentials_exception
return user
```

How to read the code:

Three independent failure points (no header, bad/expired token, deleted user) all converge on the
same 401 with `WWW-Authenticate: Bearer`.

What happens at runtime:

A valid 24-hour token yields a live `User` object the handler (or `require_admin`) can inspect.

Connects to: Byte 67 (JWT), Byte 68 (frontend interceptor), PART 12.

Remember: `HTTPBearer(auto_error=False)` means *missing* credentials are handled by our code, not
FastAPI's default.

---

### Byte 57: Admin dependency

**Builds on:** Byte 56.

**Concept:** Layering role checks on top of identity.

**In plain terms:**

`require_admin` depends on `get_current_user` and raises 403 unless `role == "ADMIN"`. It is
attached per route — not globally — so public/customer routes stay public.

**Why it exists:**

Composable authorization: identity first, then role, in one readable expression.

**The code:**

```python
# backend/app/api/products.py
def create_product(payload: ProductCreate, _admin = Depends(require_admin)) -> ProductResponse:
    return product_service.create_product(payload)
```

How to read the code:

The leading-underscore parameter is dependency-only (never a body/query param); the handler can
ignore it because the check already happened.

What happens at runtime:

Customer token → 403 `{"detail": "Admin access required"}` before Mongo is touched.

Connects to: Byte 58 (where it's applied), Byte 72 (frontend mirror), PART 3.2.

Remember: 401 (who are you?) vs 403 (you, but not allowed) are distinct.

---

### Byte 58: Product routes

**Builds on:** Byte 55.

**Concept:** The catalog endpoint family (MongoDB).

**In plain terms:**

`GET /api/products` (filters/sort/pagination), `GET /api/products/facets`,
`GET /api/products/{id}`, and admin-only `POST`, `PATCH`, `DELETE` (soft delete) plus
`POST/DELETE /{id}/image` for uploads.

**Why it exists:**

One router owns every read and write of catalog data.

**The code:**

```python
@router.get("", response_model=ProductListResponse, summary="List products")
def list_products(
    category: str | None = Query(None, ...),
    tags: list[str] | None = Query(None, ...),
    q: str | None = Query(None, max_length=100, ...),
    visibility: Literal["active", "inactive", "all"] = Query("active", ...),
    page: int = Query(1, ge=1, le=10_000),
    limit: int = Query(24, ge=1, le=100),
    sort: ProductSort = Query("newest"),
) -> ProductListResponse:
```

How to read the code:

Every query parameter is validated declaratively; `visibility="active"` is the storefront's
default so inactive items stay hidden unless asked for.

What happens at runtime:

Invalid `sort` or `page=0` → 422 before the service runs.

Connects to: Byte 17 (repo), Byte 149 (image routes), PART 8 (flow 1).

Remember: `DELETE` here returns the product with `active:false` — rows are never removed.

---

### Byte 59: Order routes

**Builds on:** Byte 55, Byte 57.

**Concept:** The order endpoint family (PostgreSQL).

**In plain terms:**

`POST /api/orders` (create → Mongo validate → PG transaction → publish sync),
`GET /api/orders/{id}` (canonical, ownership-checked), `PATCH /api/orders/{id}/status`
(admin-only, then sync).

**Why it exists:**

All order reads/writes in one place, with the store explicitly named in the module docstring.

**The code:**

```python
# backend/app/api/orders.py
ORDER_ID = Path(..., description="PostgreSQL order id", examples=[1], ge=1)

@router.post("", response_model=OrderCreateResponse,
             status_code=status.HTTP_201_CREATED, summary="Place an order")
```

How to read the code:

201 for creation; `ge=1` rejects nonsense ids at the URL level; the docstring documents the
three-step contract (validate → transaction → publish).

What happens at runtime:

`POST /api/orders` returns 201 with the order **plus** the `sync` block describing the queue
outcome.

Connects to: Byte 75 (transaction), Byte 61 (service), PART 8 (flows 5-6).

Remember: order details never read Elasticsearch.

---

### Byte 60: Search routes

**Builds on:** Byte 55, Byte 57.

**Concept:** The single Elasticsearch endpoint.

**In plain terms:**

`POST /api/search/orders` requires an authenticated **admin** and executes one ES query
(`multi_match` + filters + aggregations). PostgreSQL and MongoDB are never consulted.

**Why it exists:**

Search is a distinct capability with its own store — isolating it makes the boundary testable.

**The code:**

```python
# backend/app/api/search.py
@router.post("/orders", response_model=SearchResponse,
             summary="Search (full-text + filters + aggregations)")
def search_orders(payload: SearchRequest, _admin = Depends(...)):
    ...
```

How to read the code:

The route description enumerates the query pieces — `multi_match` over customer/order fields,
nested item titles, `terms`/`range` filters, and aggregations that always describe the *current
filter set*.

What happens at runtime:

ES unreachable → service maps it to 503 `search_unavailable` with a "PostgreSQL still holds every
order" message.

Connects to: Byte 95 (admin search UI), Byte 89 (mapping), PART 8 (flow 8).

Remember: KPIs reflect the filtered set, never the unfiltered total when filters are active.

---

### Byte 61: Services

**Builds on:** Byte 58-60.

**Concept:** Where business rules live.

**In plain terms:**

Five services (`product`, `order`, `search`, `sync`, `auth`) hold the logic that routes only
orchestrate: pricing, snapshots, transactions, error mapping and publishing.

**Why it exists:**

Reusability (tasks/scripts call the same functions) and unit-testability without HTTP.

**The code:**

```python
# backend/app/services/search_service.py
try:
    return search_repo.search_orders_with_index(request)
except AppError:
    raise
except Exception as exc:
    if getattr(exc, "status_code", None) == 400:
        raise AppError("Elasticsearch could not understand the search request.",
                       code="search_query_invalid", status_code=400, ...)
    raise DependencyUnavailableError(
        "Order search is temporarily unavailable. PostgreSQL still holds every order — ...",
        code="search_unavailable", ...)
```

How to read the code:

Error translation is a service responsibility: raw library exceptions become API-shaped errors
with human messages.

What happens at runtime:

A malformed ES query becomes 400; a cluster outage becomes 503 — the route never sees either.

Connects to: PART 30 (error envelope), PART 29.

Remember: services raise `AppError` subclasses; handlers translate them.

---

### Byte 62: Schemas

**Builds on:** Byte 14, Byte 61.

**Concept:** The request/response contracts.

**In plain terms:**

`schemas/` defines what clients may send and what they get back: `OrderCreate` (no money),
`OrderResponse` (+`sync`), `Product*`, `Search*`, `Login*`, plus the shared error envelope and
health shapes.

**Why it exists:**

Contracts are explicit, documented and validated — and the DB model never leaks out.

**The code:**

```python
# backend/app/schemas/search.py
class SearchRequest(BaseModel):
    query: str | None = Field(default=None, max_length=200, ...)
    status: list[OrderStatus] = Field(default_factory=list, ...)
    @model_validator(mode="after")
    def _check_ranges(self) -> "SearchRequest":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
```

How to read the code:

Field constraints handle simple rules; `model_validator` handles cross-field rules (inverted
ranges) — both produce 422s automatically.

What happens at runtime:

`{min_price: 500, max_price: 100}` → validation error before any ES query is built.

Connects to: Bytes 25-26 (order schemas), Byte 94 (search schemas), PART 27.

Remember: request schema ≠ response schema ≠ SQLAlchemy model.

---

### Byte 63: Models

**Builds on:** Byte 15, Byte 62.

**Concept:** The persistent shapes in PostgreSQL.

**In plain terms:**

`User`, `Order`, `OrderItem` with PKs, FKs, CHECKs, indexes, `Numeric` money and `Decimal`
arithmetic; `ORDER_STATUSES = ("PENDING", "PROCESSING", "SHIPPED")` is shared with schemas.

**Why it exists:**

The database enforces what the application promises.

**The code:**

```python
# backend/app/models/postgres.py
ORDER_STATUSES = ("PENDING", "PROCESSING", "SHIPPED")
```

How to read the code:

A single tuple feeds the model CHECK constraint, the Pydantic `Literal`, and the frontend's
`utils/status.js` list — three layers, one vocabulary.

What happens at runtime:

Any status outside the three is rejected by schema, service and database alike.

Connects to: Byte 23/25/26 (entity bytes), PART 28.

Remember: no Alembic/migrations here — `create_all()` only adds missing tables.

---

### Byte 64: Database sessions

**Builds on:** Byte 15.

**Concept:** Session lifecycle patterns used in this project.

**In plain terms:**

Two patterns coexist: a FastAPI dependency (`get_db_session`) that yields a request-scoped
session, and explicit `SessionLocal()` + `try/finally session.close()` inside services that own
transactions.

**Why it exists:**

Transactions need a clear owner; leaking sessions exhausts the pool.

**The code:**

```python
# backend/app/core/database.py
def get_db_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

How to read the code:

`yield` makes the dependency hold the session for the request and close it afterwards — even if
the handler raises.

What happens at runtime:

Every request gets a pooled connection (`pool_pre_ping`, `pool_size` from config); services
dispose theirs in `finally`.

Connects to: Byte 75 (transactions), PART 9.1.

Remember: `expire_on_commit=False` lets response objects be serialized after `commit()`.

---

## SECTION G — AUTHENTICATION

---

### Byte 65: Password hashing

**Builds on:** Byte 23.

**Concept:** Storing passwords safely.

**In plain terms:**

bcrypt hashes passwords with a per-hash salt via `passlib.CryptContext`. Only hashes are stored;
verification re-derives and compares.

**Why it exists:**

A database leak must not expose usable passwords; bcrypt is deliberately slow against guessing.

**The code:**

```python
# backend/app/core/auth.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

How to read the code:

`verify` takes the plaintext and the stored hash — the application never reverses the hash.

What happens at runtime:

Seeding hashes each user's password once; login calls `verify` per attempt.

Connects to: Byte 66 (login), PART 12.

Remember: `User.password_hash` empty → login is refused with `no_password`.

---

### Byte 66: Login

**Builds on:** Byte 65.

**Concept:** The login endpoint.

**In plain terms:**

`POST /api/auth/login` looks up the user by email, rejects missing/empty/wrong credentials with
the **same** message, and returns `{access_token, token_type, user}`.

**Why it exists:**

One round trip establishes identity for the whole session lifetime (24 h token).

**The code:**

```python
# backend/app/services/auth_service.py
user = db.query(User).filter(User.email == email).first()
if not user:
    raise NotFoundError("Invalid email or password", code="invalid_credentials")
...
if not verify_password(password, user.password_hash):
    raise NotFoundError("Invalid email or password", code="invalid_credentials")
return user
```

How to read the code:

Identical wording for unknown-email and bad-password avoids revealing which accounts exist.

What happens at runtime:

Success → token + user JSON; failure → 404 `invalid_credentials` envelope.

Connects to: Byte 67 (JWT), Byte 35 (auth store), PART 12.

Remember: the frontend stores the response in `localStorage` and redirects to `?redirect=`.

---

### Byte 67: JWT

**Builds on:** Byte 66.

**Concept:** The token itself.

**In plain terms:**

A signed JSON payload `{"sub": "<user id>", "exp": <utc>}` encoded with HS256 using
`JWT_SECRET_KEY`. Stateless: the server stores nothing; validity is checked by signature +
expiry.

**Why it exists:**

No session table; any process that knows the secret can validate a token.

**The code:**

```python
# backend/app/core/auth.py
to_encode.update({"exp": expire})
encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key,
                          algorithm=settings.jwt_algorithm)
```

How to read the code:

`exp` is the only extra claim added; `decode_access_token` returns `None` on any `JWTError`
(wrong signature, expired, malformed).

What happens at runtime:

A tampered payload fails signature verification → 401.

Connects to: Byte 56 (dependency), Byte 68 (header), PART 12.

Remember: the default secret in `config.py` is a placeholder — set `JWT_SECRET_KEY` in real
deployments.

---

### Byte 68: Authorization header

**Builds on:** Byte 67, Byte 36.

**Concept:** Attaching the token on every request.

**In plain terms:**

A request interceptor reads `meridian.auth.token` from `localStorage` and sets
`Authorization: Bearer <token>`; the response interceptor unwraps the body and normalizes errors.

**Why it exists:**

Developers call `client.get('/api/...')` and get auth for free.

**The code:**

```js
// frontend/src/api/client.js
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('meridian.auth.token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

How to read the code:

Absence of a token is fine — public endpoints don't need it; the server decides who's allowed.

What happens at runtime:

Every API call carries identity; expired tokens produce 401s that `toApiError` surfaces.

Connects to: Byte 56 (server side), Byte 31 (route guards), PART 12.

Remember: logout just deletes the keys — tokens are not revoked server-side.

---

### Byte 69: Current user

**Builds on:** Byte 56, Byte 68.

**Concept:** Using identity inside a handler.

**In plain terms:**

Any route can request the authenticated `User` by depending on `get_current_user`; the same
object feeds role checks and ownership checks.

**Why it exists:**

Handlers stay declarative — who is calling is resolved before the body executes.

**The code:**

```python
# backend/app/api/auth.py
@router.get("/me", response_model=UserResponse)
def me(current_user = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user, from_attributes=True)
```

How to read the code:

`/me` is the canonical "prove this token works" endpoint; the frontend uses it to restore
sessions on refresh.

What happens at runtime:

No/invalid token → 401; valid → `{id, name, email, role}`.

Connects to: Byte 56, Byte 72 (guards), PART 12.

Remember: `/me` returning `role` is what lets the UI know it's an admin.

---

### Byte 70: Role checking

**Builds on:** Byte 57, Byte 69.

**Concept:** `CUSTOMER` vs `ADMIN` permissions in practice.

**In plain terms:**

Customers may browse, search products, place orders and read their own orders. Admins may also
search all orders, change statuses and manage the catalog (including images).

**Why it exists:**

Least privilege: powerful operations are unreachable without the right role.

**The code:**

```python
# backend/app/core/auth.py
if current_user.role != "ADMIN":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="Admin access required")
```

How to read the code:

Role comparison is a plain string check backed by a DB CHECK constraint — no permission
framework needed at this scale.

What happens at runtime:

Customer → 403 on any admin route; admin → allowed.

Connects to: Byte 57, Byte 71/72, PART 3.

Remember: role lives in PostgreSQL `users.role`, carried to the UI via `/me` and `localStorage`.

---

### Byte 71: Customer order ownership

**Builds on:** Byte 70.

**Concept:** Customers see only their orders.

**In plain terms:**

`GET /api/orders/{id}` compares the caller with the order's `user_id`; admins may read any order,
customers only their own (otherwise 403/404).

**Why it exists:**

Enumeration protection — knowing an order id must not expose someone else's purchase data.

**The code:**

```python
# backend/app/api/orders.py (module docstring)
* `GET  /api/orders/{id}`     canonical order details (never Elasticsearch)
```

How to read the code:

The route resolves identity (dependency) → loads the order from PostgreSQL → ownership is checked
before serialization.

What happens at runtime:

Customer A requesting customer B's order is refused; the admin's request succeeds.

Connects to: Byte 59, Byte 70, PART 3.

Remember: ownership is enforced server-side; hiding links in the UI is not enforcement.

---

### Byte 72: Admin access end-to-end

**Builds on:** Byte 70, Byte 71.

**Concept:** How admin power flows from DB to UI.

**In plain terms:**

`users.role = 'ADMIN'` (PostgreSQL) → login returns `user.role` → `authStore.isAdmin` →
conditional nav links + router `requiresAdmin` guard → API `require_admin` dependencies.

**Why it exists:**

One field drives both the UX and the security, so they can't silently diverge.

**The code:**

```js
// frontend/src/router/index.js
if (requiresAdmin && !authStore.isAdmin) {
  // Non-admin users cannot access admin routes
  return next({ name: 'storefront' })
}
```

How to read the code:

The guard is the *UX* layer; identical protection on the API is the *security* layer — both read
the same role value.

What happens at runtime:

Customer visits `/admin/catalog` → bounced to storefront; calling the API directly → 403.

Connects to: Byte 4 (admin journey), Byte 57, PART 3.

Remember: change a role by updating `users.role` in PostgreSQL — no re-seed required.

---

## SECTION H — ORDER FLOW

---

### Byte 73: Cart → checkout

**Builds on:** Byte 53.

**Concept:** Handoff from client state to server request.

**In plain terms:**

The cart (Pinia, memory) becomes a minimal payload: an array of `{product_id, quantity}`. The
checkout view first re-reads each product so the displayed prices are live before the user
commits.

**Why it exists:**

The client sends *intent*, not money — the server must be the authority on price.

**The code:**

```js
// frontend/src/views/CheckoutView.vue
const results = await Promise.allSettled(ids.map((id) => getProduct(id)))
```

How to read the code:

`allSettled` (not `all`) means one missing product doesn't reject the whole price refresh — it's
flagged as unavailable instead.

What happens at runtime:

Cart changes → `cartKey` watcher → prices refreshed → place button enabled/disabled accordingly.

Connects to: Byte 53, Byte 74 (validation), PART 21.

Remember: displayed subtotal is advisory; the server's total is authoritative.

---

### Byte 74: Checkout validation

**Builds on:** Byte 73.

**Concept:** Server-side cart validation and pricing.

**In plain terms:**

`resolve_cart()` merges duplicate lines, fetches the products from MongoDB, and validates each:
exists (404), active (422), price present and positive (422), quantity ≤100 after merge (422). It
returns immutable `ResolvedLine`s and the `Decimal` total.

**Why it exists:**

Catalog state at *order time* decides availability — never the client's cached view.

**The code:**

```python
# backend/app/services/order_service.py
if not product.get("active", True):
    raise UnprocessableError(
        f"'{product.get('title', ...)}' is no longer available and cannot be ordered.",
        code="inactive_product", ...)
```

How to read the code:

Each rejection carries a machine-readable `code` and a human message with the product title —
the UI shows it directly.

What happens at runtime:

A product deactivated between add-to-cart and checkout fails here, leaving PostgreSQL untouched.

Connects to: Byte 73, Byte 75 (transaction), PART 8 (flow 6).

Remember: validation happens **before** the transaction opens.

---

### Byte 75: PostgreSQL transaction

**Builds on:** Byte 74.

**Concept:** The explicit BEGIN/COMMIT/ROLLBACK.

**In plain terms:**

The order header and all item rows are written inside one explicit transaction. Any failure
rolls everything back — no orphan headers, no header without items.

**Why it exists:**

Partial orders are worse than failed orders; the boundary must be visible in the code.

**The code:**

```python
# backend/app/services/order_service.py
try:
    session.begin()                       # BEGIN
    ...
    session.flush()                       # INSERT orders -> order.id
    ...
    session.flush()                       # INSERT order_items (CHECK constraints run here)
    session.commit()                      # COMMIT — the order is now durable
except Exception as exc:
    session.rollback()                    # ROLLBACK — never leave a partial order behind
    ...
    raise OrderPersistenceError(
        "The order could not be saved. No data was written — please try again.") from exc
```

How to read the code:

Two `flush()` calls exist so ids and CHECK constraints resolve *before* commit; the except block
guarantees rollback and a truthful 500 message.

What happens at runtime:

A CHECK violation on any line → rollback → row counts unchanged (asserted by
`test_transaction_rolls_back_completely_when_an_item_insert_fails`).

Connects to: Byte 76 (creation), Byte 78 (commit), PART 10.

Remember: rollback means "no data was written" — literally.

---

### Byte 76: Order creation details

**Builds on:** Byte 75.

**Concept:** The mechanics of producing the header.

**In plain terms:**

The row is inserted with a temporary number, its id is read back, the human number
`ORD-{id:06d}` is assigned, and `total_amount` comes from the server-side `Decimal` computation.

**Why it exists:**

Order numbers must be unique and derived from real ids.

**The code:**

```python
# backend/app/services/order_service.py
order = Order(order_number=_temporary_order_number(), user=user,
              order_date=now, status="PENDING", total_amount=total,
              created_at=now, updated_at=now)
session.add(order)
session.flush()                              # INSERT orders -> order.id
order.order_number = f"ORD-{order.id:06d}"   # human readable number
```

How to read the code:

`_temporary_order_number()` returns `TMP-<uuid>` so the UNIQUE constraint is satisfied on insert;
the update replaces it in the same transaction.

What happens at runtime:

Id 64 → `ORD-000064`; `total_amount` is `Σ(quantity × unit_price)` in `Decimal`.

Connects to: Byte 25, Byte 77 (snapshots), PART 8 (flow 6).

Remember: status always starts as `PENDING`.

---

### Byte 77: Order item snapshots

**Builds on:** Byte 76, Byte 27.

**Concept:** Freezing history at write time.

**In plain terms:**

Each item row copies `title` and `unit_price` from the resolved lines — the exact values the
customer agreed to — plus `quantity`; `line_total` is derived.

**Why it exists:**

Everything downstream (receipts, ES documents, KPIs) must reflect the purchased values forever.

**The code:**

```python
for line in lines:
    session.add(OrderItem(
        order=order,
        product_id=line.product_id,
        title=line.title,              # snapshot of MongoDB title
        quantity=line.quantity,
        unit_price=line.unit_price,    # snapshot of MongoDB price
    ))
```

How to read the code:

The comments are the design intent: these two values are copies, not references.

What happens at runtime:

Later Mongo edits change nothing in these rows; ES rebuilds from them for search.

Connects to: Byte 27, Byte 90 (search document), PART 36.

Remember: `product_id` remains a pointer for forensics — but `title`/`unit_price` are the truth.

---

### Byte 78: Transaction commit

**Builds on:** Byte 75, Byte 76.

**Concept:** The moment data becomes durable — and what may not happen before it.

**In plain terms:**

`commit()` makes the order permanent. Only after it does the code build the API response (while
the session is still open) and, crucially, publish the sync task.

**Why it exists:**

Messaging before commit could announce an order that then disappears; messaging inside the
transaction couples infrastructure failure to data integrity.

**The code:**

```python
response = OrderResponse.model_validate(order, from_attributes=True)
finally:
    session.close()
# ----------------------------------------------------------------------
# 3) Only now (after COMMIT) is the sync task handed to RabbitMQ.
sync = sync_service.publish_order_sync(order.id, reason="order_created")
return OrderCreateResponse(**response.model_dump(), sync=sync)
```

How to read the code:

Response building happens before `session.close()` (relationships are loaded); publishing is
outside the transaction entirely.

What happens at runtime:

RabbitMQ down → `sync.enqueued:false` in a **201** response; the order is already saved.

Connects to: Byte 79 (sync trigger), Byte 86 (failure), PART 10.

Remember: commit is the point of no return — everything after it is best-effort.

---

### Byte 79: Synchronization trigger

**Builds on:** Byte 78.

**Concept:** What causes ES to be updated.

**In plain terms:**

Two events publish a sync task: order creation (`order_created`) and a status change
(`status_update`) — the latter only if the status actually changed. Both run *after* commit.

**Why it exists:**

Any change to canonical order data must eventually reach the search projection.

**The code:**

```python
# backend/app/services/sync_service.py
result = celery_app.send_task(
    settings.sync_task_name,
    kwargs={"order_id": order_id, "reason": reason},
    queue=settings.celery_task_default_queue,
)
```

How to read the code:

`sync_task_name` = `app.tasks.elasticsearch_tasks.sync_order_to_elasticsearch`; the worker
re-reads PostgreSQL, so the payload needs nothing but the id.

What happens at runtime:

201/200 responses carry `SyncInfo(enqueued, task_id, queue, error)` — a visible, testable record
of the handoff.

Connects to: Byte 81 (worker), Byte 86 (failure), PART 11.

Remember: an unchanged status publishes nothing (it reports `queue: "in-process"` instead).

---

## SECTION I — MESSAGE PIPELINE

---

### Byte 80: RabbitMQ (pipeline view)

**Builds on:** Byte 79.

**Concept:** The transport between API and worker.

**In plain terms:**

Queue `orders_sync` holds JSON messages `{"order_id": N, "reason": "..."}`. The API publishes
with Celery's `send_task` (confirmed publishes); the worker consumes with `acks_late`.

**Why it exists:**

Buffers bursts, survives worker restarts, and keeps the API fast.

**The code:**

```python
# backend/app/tasks/celery_app.py
broker_connection_retry_on_startup=True,
broker_transport_options={"confirm_publish": True, "visibility_timeout": 3600},
task_default_queue=settings.celery_task_default_queue,   # "orders_sync"
```

How to read the code:

`confirm_publish` means the broker acknowledges receipt of each publish; `visibility_timeout`
redelivers messages unacknowledged after an hour (worker crash scenarios).

What happens at runtime:

Messages queue up while the worker is stopped and are drained when it returns.

Connects to: Byte 81 (Celery), Byte 86 (failure), PART 11.

Remember: the queue carries ids, not orders.

---

### Byte 81: Celery (worker view)

**Builds on:** Byte 80.

**Concept:** The consuming process.

**In plain terms:**

The `celery-worker` service runs `celery -A app.tasks.celery_app worker --concurrency=2`,
imports the task module at boot, and executes tasks with JSON serialization, UTC time, 120 s hard
limit, and prefetch 1.

**Why it exists:**

Isolated process: a crash or slow ES query cannot affect the API.

**The code:**

```python
# backend/app/tasks/celery_app.py
imports=["app.tasks.elasticsearch_tasks"],
task_serializer="json",
accept_content=["json"],
task_time_limit=120,
task_soft_time_limit=90,
```

How to read the code:

`imports` registers tasks without the worker needing the whole app package; time limits stop a
hung ES call from occupying a slot forever.

What happens at runtime:

Worker boots → logs "sync task queued" counterparts → binds queue → executes tasks one at a time
per slot.

Connects to: Byte 83 (execution), Byte 85 (retries), PART 11.

Remember: `task_always_eager` (tests) bypasses the broker entirely.

---

### Byte 82: Task creation & registration

**Builds on:** Byte 81.

**Concept:** How a Python function becomes a queue task.

**In plain terms:**

The decorated function `sync_order_to_elasticsearch` is registered under a stable dotted name;
the producer references that name as a string, so it doesn't need to import the worker's code.

**Why it exists:**

Decoupled deployment: API and worker share the name, not the memory.

**The code:**

```python
# backend/app/tasks/elasticsearch_tasks.py
TASK_NAME = "app.tasks.elasticsearch_tasks.sync_order_to_elasticsearch"
```

How to read the code:

A test asserts this string (`test_sync_task_is_registered_with_the_expected_name`) because a
silent rename would strand every published message.

What happens at runtime:

`send_task(TASK_NAME, ...)` → broker → worker resolves the name to its local function.

Connects to: Byte 79, Byte 81, PART 11.

Remember: renaming the task function breaks the producer unless `TASK_NAME` is updated too.

---

### Byte 83: Worker execution

**Builds on:** Byte 82.

**Concept:** What the task actually does, step by step.

**In plain terms:**

Open a PG session → load the order (with items/user) → if missing, report `skipped` → build the
ES document from those snapshots → ensure the index exists → upsert → record
`search_indexed_at` (best-effort) → return a small stats dict.

**Why it exists:**

Rebuilding from the source of truth makes the worker idempotent and self-healing.

**The code:**

```python
# backend/app/tasks/elasticsearch_tasks.py
order = order_repo.get_order(session, order_id)
if order is None:
    return {"status": "skipped", ...}
document = build_order_document(order)     # rebuilt from PostgreSQL every time
ensure_index()
index_order_document(document)             # upsert with _id = order_id
```

How to read the code:

Nothing is read from MongoDB and nothing arrives via the message — all values come from
PostgreSQL, so retried tasks converge to the same document.

What happens at runtime:

Order 64 → one ES doc `_id=64`; a duplicate task overwrites it identically.

Connects to: Byte 84 (indexing), Byte 85 (retries), PART 11.

Remember: a task for a deleted order is a harmless no-op.

---

### Byte 84: Elasticsearch indexing

**Builds on:** Byte 83.

**Concept:** The write into the search cluster.

**In plain terms:**

`index_order_document` performs an upsert addressed by `order_id`, optionally refreshing
immediately (`ELASTICSEARCH_REFRESH_ON_WRITE=true` for the demo) so a just-placed order is
searchable at once.

**Why it exists:**

Idempotent writes are what make at-least-once delivery safe.

**The code:**

```python
# backend/app/repositories/elasticsearch/orders_repo.py
def index_order_document(document: dict[str, Any]) -> dict[str, Any]:
    """Index (upsert) a single order document, addressed by `order_id`."""
```

How to read the code:

Addressing by `order_id` (not a random UUID) means re-indexing updates rather than duplicates.

What happens at runtime:

`PUT /orders/_doc/64` semantics; counts in ES always match PostgreSQL after workers drain.

Connects to: Byte 85 (retries), Byte 120 (reindex), PART 37.

Remember: turning refresh off improves throughput but delays searchability.

---

### Byte 85: Retry behavior

**Builds on:** Byte 84.

**Concept:** What happens when Elasticsearch fails.

**In plain terms:**

The task retries up to 5 times with exponential backoff (10 s → 20 → 40 → 80 → capped 120 s).
After `MaxRetriesExceededError` it gives up and logs — PostgreSQL is unaffected.

**Why it exists:**

Transient cluster issues resolve themselves; permanent ones shouldn't loop forever.

**The code:**

```python
# backend/app/tasks/elasticsearch_tasks.py (retry pattern)
from celery.exceptions import MaxRetriesExceededError
...
# on failure: self.retry(countdown=backoff) up to settings.celery_max_retries (5)
```

How to read the code:

Backoff parameters come from config (`CELERY_RETRY_BACKOFF`, `CELERY_RETRY_BACKOFF_MAX`), so
tuning requires no code change.

What happens at runtime:

ES down for 10 minutes → task retries ~5 times → stops → order remains unindexed until reindex or
the next status change.

Connects to: Byte 86 (failure), Byte 120 (recovery), PART 11.

Remember: retries are for the *indexing* step only — never for publishing.

---

### Byte 86: Failure behavior

**Builds on:** Byte 85, Byte 78.

**Concept:** What breaks and what survives.

**In plain terms:**

Broker down → order still saved, `enqueued:false`. Worker down → message waits. ES down →
retries then abandon. PG down → rollback, 500, nothing written. Each failure degrades exactly one
capability.

**Why it exists:**

Clear degradation boundaries are the payoff of the asynchronous design.

**The code:**

```python
# backend/app/services/sync_service.py
if settings.celery_task_always_eager:
    return _run_inline(order_id, reason)
try:
    result = celery_app.send_task(...)
except Exception as exc:   # (structure) → SyncInfo(enqueued=False, error=...)
```

How to read the code:

Publishing is wrapped so messaging errors become *data in the response*, not HTTP failures.

What happens at runtime:

Operators can see sync health directly in the create/status response and in the order details'
`search_indexed_at`.

Connects to: Byte 78, Byte 85, PART 10 §10.3.

Remember: no automatic publish retry exists — recovery is reindex or a later status update.

---

### Byte 87: Consistency model

**Builds on:** Byte 86.

**Concept:** The guarantee you can actually rely on.

**In plain terms:**

Reads from PostgreSQL are read-your-writes; reads from Elasticsearch are *eventually* consistent
with it. Duplicates converge (upsert), missing documents are recoverable (reindex), and no
failure of the projection can corrupt the source.

**Why it exists:**

Naming the model prevents the classic mistake of assuming search results are transactional.

**The code:**

```python
# backend/app/repositories/elasticsearch/document.py (module docstring)
`build_order_document()` is a pure function: it only reads the already
loaded SQLAlchemy `Order` ...
```

How to read the code:

Purity + full rebuild + `_id=order_id` together define convergence: same input → same document.

What happens at runtime:

Any lag window closes once the worker runs; until then, order *details* are still correct from PG.

Connects to: Byte 84, Byte 120 (reindex), PART 37.

Remember: "search may lag; orders never do."

---

## SECTION J — ELASTICSEARCH

---

### Byte 88: Index

**Builds on:** Byte 18.

**Concept:** The `orders` index lifecycle.

**In plain terms:**

One index named by `ELASTICSEARCH_INDEX` (default `orders`). It is created idempotently at
startup and before each index operation; `reindex_orders --recreate` drops and rebuilds it.

**Why it exists:**

The index is disposable by design — a projection you can always rebuild.

**The code:**

```python
# backend/app/repositories/elasticsearch/orders_repo.py
def ensure_index(*, recreate: bool = False) -> bool:
    client = get_elasticsearch_client()
    name = index_name()
    exists = bool(client.indices.exists(index=name))
    if exists and recreate:
        client.indices.delete(index=name)
        exists = False
    if not exists:
        client.indices.create(index=name, settings=ORDER_INDEX_SETTINGS,
                              mappings=ORDER_INDEX_MAPPING)
        return True
    return False
```

How to read the code:

Existence check first; `recreate=True` forces a clean slate; creation always applies the explicit
mapping (never dynamic defaults).

What happens at runtime:

Fresh environment → index created at first boot/seed; existing index → no-op.

Connects to: Byte 89 (mapping), Byte 120 (reindex), PART 9.3.

Remember: 1 shard, 0 replicas — a single-node demo cluster.

---

### Byte 89: Mapping

**Builds on:** Byte 88.

**Concept:** Field types and why each was chosen.

**In plain terms:**

`keyword` for exact values/facets (`status`, `order_number`), `search_as_you_type` for
`customer.name/email`, `text + .keyword` for `items.title`, `nested` for `items`, `date` for
timestamps, `double` for money, and `dynamic: strict` to reject surprises.

**Why it exists:**

Types decide what queries are possible and how precise aggregations are.

**The code:**

```python
# backend/app/repositories/elasticsearch/mappings.py
"customer": {
    "type": "object",
    "properties": {
        "id": {"type": "long"},
        "name": {"type": "search_as_you_type",
                 "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
```

How to read the code:

The base type powers prefix/infix suggestions; the `.keyword` sub-field powers sorting and exact
aggregation.

What happens at runtime:

Changing the mapping requires reindexing — which the `recreate` path provides.

Connects to: Byte 88, Byte 90 (document), PART 9.3.

Remember: `items` is **nested** so item titles don't bleed across documents.

---

### Byte 90: Search document

**Builds on:** Byte 28, Byte 89.

**Concept:** One order = one self-contained searchable record.

**In plain terms:**

Flattened customer fields + nested item snapshots let a single query match "orders mentioning
this customer or this product" without joins.

**Why it exists:**

Search engines match *documents*, not relational rows.

**The code:**

```python
# backend/app/repositories/elasticsearch/document.py
"customer": {
    "id": int(order.user_id),
    "name": getattr(user, "name", "") or "",
    "email": getattr(user, "email", "") or "",
},
```

How to read the code:

Empty strings for missing values keep the document schema-stable under `dynamic: strict`.

What happens at runtime:

`search` for "Wendy" matches `customer.name`; for a product title, the nested items match.

Connects to: Byte 28, Byte 91 (full-text), PART 37.

Remember: `_id = order_id` — the link back to the source of truth.

---

### Byte 91: Full-text search

**Builds on:** Byte 90.

**Concept:** How free text is matched.

**In plain terms:**

A `multi_match` runs across `customer.name^3`, `customer.email` and `order_number`; a nested
`multi_match` covers `items.title^2`. Carets weight matches (customer name beats email).

**Why it exists:**

One query can find orders by person, by order number, or by purchased product.

**The code:**

```python
# backend/app/repositories/elasticsearch/search_repo.py
TEXT_FIELDS = ["customer.name^3", "customer.email", "order_number"]
NESTED_TEXT_FIELDS = ["items.title^2"]
```

How to read the code:

The caret numbers express relevance priority; the split into top-level and nested lists exists
because nested fields must be queried inside a `nested` clause.

What happens at runtime:

`query: "Wireless"` returns orders whose *snapshot* item titles contain "wireless" — historical
values, not current catalog names.

Connects to: Byte 90, Byte 92 (partial), PART 9.3.

Remember: relevance here applies to **orders**, not products.

---

### Byte 92: Partial search

**Builds on:** Byte 91.

**Concept:** Prefix/typo-tolerant behaviour.

**In plain terms:**

`search_as_you_type` fields support prefix and infix matching out of the box (ideal for
typeahead), and analyzed `text` fields match on token prefixes depending on query type.

**Why it exists:**

Admins type partial names/emails/orders — exact matching would be useless.

**The code:**

```python
# backend/app/repositories/elasticsearch/mappings.py (comment)
* `customer.name` / `customer.email` / `items.title` are `text` (full-text
* search) with a `.keyword` sub-field (aggregations, exact matching).
```

How to read the code:

Two sub-fields per text field: analyzed for matching, keyword for grouping.

What happens at runtime:

Typing "wend" surfaces "Wendy Wireless" orders in the admin search.

Connects to: Byte 91, Byte 95 (admin search), PART 9.3.

**Remember:** `text` fields match, `.keyword` sub-fields group - every aggregation and exact sort uses `.keyword`.

**Not confirmed from the available source:** an explicit `bool_prefix` query clause — the
implemented query uses `multi_match` over `search_as_you_type`/`text` fields.

---

### Byte 93: Filters

**Builds on:** Byte 92.

**Concept:** Restricting the result set without affecting scoring.

**In plain terms:**

Filters live in the `bool.filter` clause: `terms` on status, `range` on `order_date` (inclusive
day bounds converted to UTC ISO strings), `range` on `total_amount`. Filters compose with AND.

**Why it exists:**

Faceted browsing: KPIs and counts must describe exactly the filtered set.

**The code:**

```python
# backend/app/repositories/elasticsearch/search_repo.py
if request.status:
    filters.append({"terms": {"status": list(request.status)}})
```

How to read the code:

`filters` accumulate predicates; empty selections mean "no constraint" (all statuses).

What happens at runtime:

`status=[PENDING, SHIPPED]` + date range → intersection of both predicates.

Connects to: Byte 94 (aggregations), Byte 95 (admin UI), PART 8 (flow 8).

Remember: date bounds are inclusive of both days (start-of-day → end-of-day, 59:59.999999).

---

### Byte 94: Aggregations

**Builds on:** Byte 93.

**Concept:** KPIs computed by the search engine.

**In plain terms:**

Two aggregations run alongside the query: `sum(total_amount)` (revenue for the filtered set) and
a `terms` bucket per status (with missing→0 so all three always appear).

**Why it exists:**

Dashboard numbers and result lists come from the same query — they can't disagree.

**The code:**

```python
# backend/app/schemas/search.py
class SearchAggregations(BaseModel):
    """KPI values computed by Elasticsearch aggregations."""
    revenue: float = Field(description="sum(total_amount) over the filtered result set")
    status_counts: dict[str, int] = Field(
        description="Document count per status, always containing all three statuses")
```

How to read the code:

The docstrings state the contract the frontend `SearchKpis` component relies on.

What happens at runtime:

Filter by `SHIPPED` → revenue KPI shows only shipped revenue, counts show 0/0/N.

Connects to: Byte 93, Byte 95, PART 9.3.

Remember: never compute revenue from ES for financial reporting — it's `double`, analytics-grade.

---

### Byte 95: Admin search (the screen)

**Builds on:** Byte 93, Byte 94.

**Concept:** How the dashboard drives the query.

**In plain terms:**

`AdminSearchView` builds a `SearchRequest` from local refs (term, statuses, dates, price band,
page), debounces input, renders KPI cards, results (table on desktop, cards on mobile) and
pagination, and pushes to order details on row click.

**Why it exists:**

One screen demonstrates full-text + filters + facets + pagination against Elasticsearch only.

**The code:**

```js
// frontend/src/views/AdminSearchView.vue
const payload = { page: page.value, limit: PAGE_SIZE }
if (term) payload.query = term
if (statuses.value.length) payload.status = [...statuses.value]
if (dateFrom.value) payload.date_from = dateFrom.value
```

How to read the code:

Fields are added only when set — omitted keys mean "no filter", keeping the payload minimal.

What happens at runtime:

Typing/filters → `refresh()` → `searchOrders(payload)` → KPIs + rows update; row click →
`/admin/orders/:id` (PostgreSQL).

Connects to: Byte 60, Byte 93, PART 22.

Remember: this screen never calls `/api/orders` — details open a *different* endpoint.

---

## SECTION K — PRODUCT IMAGES

---

### Byte 96: image_url

**Builds on:** Byte 24.

**Concept:** How an image is referenced.

**In plain terms:**

A product document carries `image_url` — either a bundled asset (`/products/ORG-001.svg`), an
upload (`/uploads/products/<file>`), an external URL, or `null`.

**Why it exists:**

One field supports seed art, admin uploads and external hosts without schema changes.

**The code:**

```python
# backend/app/schemas/products.py
image_url: str | None = Field(default=None, max_length=...)  # nullable reference
```

How to read the code:

Nullable because a product may have no image yet — the frontend then renders its placeholder.

What happens at runtime:

The API returns the stored string verbatim; the client resolves it into a loadable source.

Connects to: Byte 106 (resolver), Byte 99 (upload), PART 23.

Remember: the URL is *relative* for uploads, so it works behind any proxy.

---

### Byte 97: Admin image column

**Builds on:** Byte 96.

**Concept:** Seeing images in the catalog table.

**In plain terms:**

`CatalogTable.vue` renders an `Image` column first, showing `ProductThumb` per row, with a
skeleton row while loading (10 cells to match the 10 columns).

**Why it exists:**

Admins must verify at a glance that the right image is attached to the right product.

**The code:**

```vue
<!-- frontend/src/components/admin/CatalogTable.vue -->
<th>Image</th>
...
<td class="catalog__image-cell">
  <ProductThumb :product="product" size="sm" />
</td>
```

How to read the code:

The cell is a fixed-size thumbnail slot — consistent row heights regardless of image dimensions.

What happens at runtime:

Loading → skeleton cells; data → thumbnails (or placeholders on failure).

Connects to: Byte 96, Byte 98 (modal), PART 22.

Remember: mobile admin uses `CatalogCardList` with the same thumb component.

---

### Byte 98: Edit product modal

**Builds on:** Byte 97.

**Concept:** Where image actions live.

**In plain terms:**

`ProductFormModal` handles both create and edit; its image section shows a preview, **Replace**
and **Remove** buttons, and a file input (rendered unconditionally but visually hidden) so Replace
always has a target.

**Why it exists:**

Image management belongs inside the existing edit flow — no separate page.

**The code:**

```vue
<!-- frontend/src/components/admin/ProductFormModal.vue -->
<input ref="fileInput" type="file" style="display:none"
       accept=".jpg,.jpeg,.png,.webp,.svg,image/jpeg,image/png,image/webp,image/svg+xml"
       @change="onFileSelected" />
```

How to read the code:

Hidden-but-present input: the Replace button triggers `fileInput.click()`; the `accept` attribute
guides the file picker to supported formats.

What happens at runtime:

Choose file → client validation + local preview → (on save) upload → server URL replaces preview.

Connects to: Byte 99 (upload), Byte 104 (replace), PART 23.

Remember: a previous bug (input inside a `v-else` branch) made Replace a no-op — the input must
render unconditionally.

---

### Byte 99: UploadFile

**Builds on:** Byte 98.

**Concept:** FastAPI's file parameter.

**In plain terms:**

`file: UploadFile = File(...)` parses `multipart/form-data` into a file object with
`filename`, `content_type` and async `read()`.

**Why it exists:**

Standard multipart handling with async streaming into your own storage.

**The code:**

```python
# backend/app/api/products.py
async def upload_product_image(
    product_id: str = PRODUCT_ID,
    file: UploadFile = File(...),
    _admin = Depends(require_admin),
) -> ProductResponse:
```

How to read the code:

Admin dependency first (401/403 before any I/O); the product id comes from the path; the file
from the body.

What happens at runtime:

Frontend `FormData` with `file` field → multipart request → validated → written to disk.

Connects to: Byte 100 (validation), Byte 101 (storage), PART 23.

Remember: `python-multipart` in `requirements.txt` is what makes `File(...)` work.

---

### Byte 100: Image validation

**Builds on:** Byte 99.

**Concept:** What the server accepts.

**In plain terms:**

Content-type must be JPEG/PNG/WebP/SVG; extension must be one of `.jpg/.jpeg/.png/.webp/.svg`;
size ≤ 5 MB; filename must exist. Failures raise 422 with explicit codes.

**Why it exists:**

Prevents storing arbitrary files and name collisions/attacks.

**The code:**

```python
# backend/app/api/products.py
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
```

How to read the code:

Two allowlists (declared type + extension) plus a hard size cap; the stored filename is
`uuid4().hex + whitelisted extension`, never the client's name.

What happens at runtime:

A `.gif` → 422 `invalid_image_format`; a 6 MB PNG → 422 `image_too_large`.

Connects to: Byte 99, Byte 101, PART 23, PART 31.

Remember: SVG is allowed (vector art) — it's sanitized only by the allowlist, not content-parsed.

---

### Byte 101: Image storage

**Builds on:** Byte 100.

**Concept:** Where bytes land.

**In plain terms:**

Files are written to `settings.uploads_path / "products"` (default `/app/uploads/products`) with
a server-generated name; FastAPI mounts that root at `/uploads` via `StaticFiles`.

**Why it exists:**

Local, inspectable storage that works offline and can be proxied like any other route.

**The code:**

```python
# backend/app/main.py
app.mount(
    "/uploads",
    StaticFiles(directory=str(uploads_dir), check_dir=True),
    name="uploads",
)
```

How to read the code:

Mounted at import time; `check_dir=True` fails fast if the directory is unusable (the code
creates it first and logs a warning instead).

What happens at runtime:

`GET /uploads/products/ab12.webp` → static file response; missing file → 404 → `<img>` error →
placeholder.

Connects to: Byte 100, Byte 102 (volume), PART 23.

Remember: the stored `image_url` starts with `/uploads/` — that prefix is what
`resolveImageUrl()` recognizes.

---

### Byte 102: Docker volume

**Builds on:** Byte 101.

**Concept:** Making uploads survive restarts.

**In plain terms:**

`uploads_data` is a named volume mounted at `/app/uploads` in both `backend` and
`celery-worker`; files persist across container recreation.

**Why it exists:**

Container filesystems are ephemeral — without the volume every restart "deletes" the catalog's
images.

**The code:**

```yaml
# docker-compose.yml
backend:
  volumes:
    - ./backend:/app
    - uploads_data:/app/uploads
volumes:
  uploads_data:
```

How to read the code:

Bind mount for code, named volume for data — different lifetimes by intent.

What happens at runtime:

`docker compose restart` keeps images; `docker compose down -v` removes them (known gotcha).

Connects to: Byte 101, Byte 103 (persistence), PART 32.

Remember: the worker mounts the same volume so it could serve/read files consistently.

---

### Byte 103: MongoDB persistence

**Builds on:** Byte 102.

**Concept:** The reference lives in the catalog.

**In plain terms:**

After writing the file, the endpoint `$set`s `image_url` on the product document; that string is
what every future API response returns.

**Why it exists:**

Separation: bytes on disk, reference in the database — either can be rebuilt/replaced
independently.

**The code:**

```python
# backend/app/api/products.py
new_image_url = f"/uploads/products/{filename}"
updated = product_repo.update_product(product_id, {"image_url": new_image_url})
if updated is None:
    # Rollback: delete the uploaded file
    try:
        destination.unlink()
    except OSError:
        pass
    raise NotFoundError(..., code="product_not_found", ...)
```

How to read the code:

Order of operations — file first, then reference, with compensating delete if the reference write
fails (no orphan upload from this path).

What happens at runtime:

Mongo now returns the new URL on the next `GET /api/products/{id}`.

Connects to: Byte 101, Byte 104 (replace), PART 23.

Remember: unlike legacy seed helpers, `image_url` values persist in MongoDB across restarts.

---

### Byte 104: Image replacement

**Builds on:** Byte 103.

**Concept:** Swap an image safely.

**In plain terms:**

Upload the new file, delete the old one (only if it's inside the upload root), update Mongo. If
Mongo fails, delete the new file and error out.

**Why it exists:**

Replace must leave either the old state or the new state — never a broken middle.

**The code:**

```python
# backend/app/api/products.py
old_image_url = product.get("image_url")
if old_image_url:
    old_path = _stored_image_path(old_image_url)
    if old_path and old_path.exists() and old_path != destination:
        try:
            old_path.unlink()
        except OSError:
            pass  # Best effort cleanup
```

How to read the code:

`_stored_image_path` returns `None` for non-upload URLs (bundle assets) — they're never deleted;
cleanup is best-effort so a locked file doesn't fail the upload.

What happens at runtime:

Replace → new UUID file + updated `image_url`; old file removed from the volume.

Connects to: Byte 105 (removal), Byte 106 (resolver), PART 23.

Remember: a product whose image is *not* under `/uploads/` can be replaced without touching
shipped assets.

---

### Byte 105: Image removal

**Builds on:** Byte 104.

**Concept:** Detaching and deleting.

**In plain terms:**

`DELETE /api/products/{id}/image` (admin) deletes the stored file if it's inside the upload root,
then sets `image_url` to `null` — reverting the card to its placeholder.

**Why it exists:**

Cleanup without deleting the product itself.

**The code:**

```python
# backend/app/api/products.py
old_image_url = product.get("image_url")
if old_image_url:
    old_path = _stored_image_path(old_image_url)
    if old_path and old_path.exists():
        try:
            old_path.unlink()
        except OSError:
            pass  # Best effort cleanup

updated = product_repo.update_product(product_id, {"image_url": None})
```

How to read the code:

File deletion first, then reference nulling; both guarded so a missing file isn't fatal.

What happens at runtime:

Product returns `image_url: null`; frontend shows the branded placeholder.

Connects to: Byte 106, PART 23, PART 39 (orphan-file gotcha).

Remember: removing an image does **not** delete the product or affect old orders.

---

### Byte 106: Frontend image resolver

**Builds on:** Byte 96, Byte 105.

**Concept:** From stored string to rendered `<img>`.

**In plain terms:**

`ProductThumb` computes `resolveImageUrl(image_url)` (prefixing `/uploads/` only when an API
origin is configured), renders with lazy loading, and swaps to a deterministic placeholder on
`@error` or when there's no URL.

**Why it exists:**

Identical stored values must load correctly in dev (Vite proxy), prod (Nginx) and direct-API
setups.

**The code:**

```vue
<!-- frontend/src/components/common/ProductThumb.vue -->
<img v-if="showImage" :src="imageUrl" :alt="product.title" class="thumb__image"
     loading="lazy" decoding="async" @load="onLoad" @error="onError" />
<div v-else class="thumb__placeholder"> …monogram + pattern… </div>
```

How to read the code:

`showImage = imageUrl && !failed` — missing URL and load failure both land on the placeholder;
the pattern index derives from the title (no external images).

What happens at runtime:

Upload succeeds → thumb swaps to the server URL → `@load` clears the loading state; if the file
was lost, `@error` shows the placeholder instead of a broken-image icon.

Connects to: Byte 38 (resolver), Byte 101 (serving), PART 23.

Remember: placeholders are deterministic per product — no layout jump between renders.

---

## SECTION L — ADMIN

---

### Byte 107: Admin screens

**Builds on:** Byte 4, Byte 72.

**Concept:** The three admin surfaces and the store each owns.

**In plain terms:**
`/admin/search` (Elasticsearch) → `/admin/orders/:id` (PostgreSQL) → `/admin/catalog`
(MongoDB, including images). One layout (`AdminLayout`) hosts all three; route meta
(`requiresAuth` + `requiresAdmin`) gates entry.

**Why it exists:**
Each screen is a window into exactly one store, which makes the polyglot architecture visible
while you use it.

**The code:**

```js
// frontend/src/router/index.js (admin children)
{ path: 'search',   name: 'admin-search',     component: () => import('../views/AdminSearchView.vue') },
{ path: 'orders/:id', name: 'order-details',  component: () => import('../views/OrderDetailsView.vue') },
{ path: 'catalog',   name: 'catalog-admin',   component: () => import('../views/CatalogAdminView.vue') },
```

How to read the code:

Lazy `import()` per screen; `/admin` itself redirects to `admin-search`.

What happens at runtime:

Guard → `AdminLayout` renders nav → the active screen fetches from its own API only.

Connects to: Byte 108 (KPIs), Byte 113 (catalog), PART 22.

Remember: search results never render from PostgreSQL, and order details never render from Elasticsearch.

---

### Byte 108: KPI cards

**Builds on:** Byte 94.

**Concept:** Dashboard numbers straight from the aggregation block.

**In plain terms:**
Five `KpiCard`s: **Total revenue** (`formatCurrency(aggregations.revenue)`), **Filtered orders**
(`total`), and per-status counts (Pending/Processing/Shipped from `status_counts`). They always
describe the *current* filter set.

**Why it exists:**
Metrics and rows come from one query, so they can never disagree.

**The code:**

```vue
<!-- frontend/src/components/admin/SearchKpis.vue -->
<KpiCard label="Total revenue" :value="formatCurrency(aggregations?.revenue ?? 0)" />
<KpiCard label="Filtered orders" :value="formatNumber(total ?? 0)" ... />
<KpiCard label="Pending" :value="formatNumber(aggregations?.status_counts?.PENDING ?? 0)" ... />
```

How to read the code:

`?? 0` / `?? ''` guards keep cards sane while the first request is in flight; revenue goes
through the single ₹ formatter.

What happens at runtime:

Filters change → new response → revenue and counts recompute for that subset.

Connects to: Byte 94, Byte 109 (filters), PART 22.

Remember: "Filtered orders" ≠ total orders in the system — that's the point of the label.

---

### Byte 109: Filters

**Builds on:** Byte 95, Byte 108.

**Concept:** The admin filter panel.

**In plain terms:**
Text query, three status checkboxes, date-from/date-to (`type="date"`), min/max total, an
active-filter count badge, and a clear action. Output maps 1:1 onto `SearchRequest` fields.

**Why it exists:**
Every control corresponds to a server-side predicate — no client-side filtering of ES results.

**The code:**

```vue
<!-- frontend/src/components/admin/SearchFilters.vue -->
<FormField label="Date from"><BaseInput type="date" ... /></FormField>
<FormField label="Min total" :hint="priceHint"><BaseInput type="number" ... /></FormField>
<AppBadge v-if="activeCount" tone="accent" class="search-filters__count">{{ activeCount }}</AppBadge>
```

How to read the code:

`activeCount` shows how many filters are narrowing the query; price hints document the band
(e.g. `$30–$150`).

What happens at runtime:

Change any control → debounce → payload rebuilt (only non-empty fields) → `searchOrders`.

Connects to: Byte 93 (filters in ES), Byte 95 (payload build), PART 22.

Remember: inverted ranges are rejected server-side with 422 (`SearchRequest._check_ranges`).

---

### Byte 110: Results rendering

**Builds on:** Byte 109.

**Concept:** Desktop table vs. mobile card list.

**In plain terms:**
`ResultsTable` columns: **Order · Customer · Status · Date · Items · Total** (Total right-aligned
`.tabular`), each row a link to order details; `ResultsCardList` renders the same data as cards
on small screens. Pagination sits below both.

**Why it exists:**
Same data, two layouts — density on desktop, tap targets on mobile.

**The code:**

```vue
<!-- frontend/src/components/admin/ResultsTable.vue -->
<thead><tr>
  <th>Order</th><th>Customer</th><th>Status</th><th>Date</th><th>Items</th>
  <th class="results__right">Total</th>
</tr></thead>
```

How to read the code:

Row click emits the order id → `AdminSearchView.openOrder(id)` → route push to
`/admin/orders/:id`.

What happens at runtime:

`results[]` from ES → rows with `StatusBadge` and `formatCurrency(total_amount)` → click opens
PostgreSQL details.

Connects to: Byte 111 (details), Byte 50 (pagination), PART 22.

Remember: clicking a row switches data stores — search (ES) → details (PG).

---

### Byte 111: Order details view

**Builds on:** Byte 110, Byte 71.

**Concept:** The canonical order screen.

**In plain terms:**
Loads `GET /api/orders/{id}` (PostgreSQL), then renders header (order number, status badge,
dates, customer), the snapshot line items (title/quantity/unit price/line total), the
`SearchSyncIndicator`, and — for admins — `OrderStatusControl`.

**Why it exists:**
One screen shows what actually happened, sourced from the authority.

**The code:**

```js
// frontend/src/views/OrderDetailsView.vue
async function load() {
  const data = await getOrder(route.params.id)
  order.value = data
}
```

How to read the code:

Single fetch keyed by the route param; the `sync`/`search_indexed_at` fields drive the indicator.

What happens at runtime:

Mount/param change → `load()` → items render from `order.items` snapshots (not live Mongo).

Connects to: Byte 112 (status), Byte 113 (catalog), PART 8 (flow 9).

Remember: if this screen and search disagree, **this screen** is right.

---

### Byte 112: Status control

**Builds on:** Byte 111.

**Concept:** Changing order status with immediate sync.

**In plain terms:**
A `<select>` with exactly the three statuses (`statusOptions()`); on change the view calls
`updateOrderStatus(id, status)` → `PATCH /api/orders/{id}/status` → server commits, publishes the
sync task (only if changed), and the UI updates the badge/toast.

**Why it exists:**
Status transitions are the one admin write that must propagate to search.

**The code:**

```vue
<!-- frontend/src/components/admin/OrderStatusControl.vue -->
<select class="status-control__select" :value="value" :options="statusOptions()"
        @change="emit('change', $event.target.value)" />
```

How to read the code:

Controlled component — `value` from the order, `change` handled by the view (which owns the API
call).

What happens at runtime:

Pick `SHIPPED` → PATCH → 200 with `sync` block → badge updates → worker rebuilds the ES doc →
`SearchSyncIndicator` flips to **Indexed** when `search_indexed_at` arrives.

Connects to: Byte 79 (trigger), Byte 111 (details view), PART 8 (flow 10-11).

Remember: invalid statuses are rejected by the `Literal` schema — only three exist.

---

### Byte 113: Catalog management

**Builds on:** Byte 4, Byte 57.

**Concept:** Product CRUD in the browser.

**In plain terms:**
`CatalogAdminView` lists all products (including inactive) with filters/facets, then:
**Create** (`openCreate`) and **Edit** (`openEdit`) open `ProductFormModal`; **deactivate** calls
`deleteProduct(id)` (soft); **activate** calls `updateProduct(id, {active:true})`. The modal
handles image preview/upload/replace/remove in the same flow.

**Why it exists:**
Full catalog ownership without a separate admin backend.

**The code:**

```js
// frontend/src/views/CatalogAdminView.vue
async function confirmDeactivate() {
  await deleteProduct(confirmTarget.value.id)   // soft delete → active:false
}
async function activate(product) {
  await updateProduct(product.id, { active: true })
}
```

How to read the code:

"Delete" is deactivation — the document stays, hidden from the storefront by `visibility=active`
filtering.

What happens at runtime:

Toggle → API → row refreshes (badge Active/Inactive) → storefront grid loses/gains the product.

Connects to: Byte 24, Byte 98 (modal), PART 22.

Remember: old orders still reference deactivated products — snapshots keep them readable.

---

## SECTION M — INFRASTRUCTURE

---

### Byte 114: Docker Compose

**Builds on:** Byte 21.

**Concept:** The one file that defines the environment.

**In plain terms:**
Nine services (4 infra + backend + worker + dev frontend + prod frontend + tools), one bridge
network (`app_net`), six named volumes, healthchecks everywhere, and an environment anchor that
rewrites localhost to in-network hostnames.

**Why it exists:**
`docker compose up -d --build` must produce the whole system identically on any machine.

**The code:**

```yaml
# docker-compose.yml
x-backend-environment: &backend-environment
  POSTGRES_HOST: postgres
  MONGO_URI: mongodb://mongodb:27017/catalog
  ELASTICSEARCH_URL: http://elasticsearch:9200
  RABBITMQ_HOST: rabbitmq
  RABBITMQ_URL: amqp://ecommerce:change_me_rabbit@rabbitmq:5672//
```

How to read the code:

The YAML anchor `&backend-environment` is injected into `backend`, `celery-worker`, `seed` and
`reindex` via `<<:` — one definition, four consumers.

What happens at runtime:

Containers resolve each other by service name; the host machine uses localhost ports
(8000/5173/8080/5432/27017/9200/5672/15672).

Connects to: Byte 115 (builds), Byte 118 (health), PART 32.

Remember: `seed` and `reindex` are `profiles: ["tools"]`; `frontend-prod` is `profiles: ["prod"]`.

---

### Byte 115: Dockerfiles

**Builds on:** Byte 114.

**Concept:** Multi-stage builds for dev and prod.

**In plain terms:**
`backend/Dockerfile`: `base` (python:3.11-slim + deps) → `dev` (bind-mounted source, root) →
`prod` (non-root `appuser`, `--workers 2`). `frontend/Dockerfile`: `base` → `dev` (Vite) →
`build` (`npm run build`) → `prod` (Nginx serving `dist`).

**Why it exists:**
One context produces both a live-reload dev container and a lean production image.

**The code:**

```dockerfile
# backend/Dockerfile (prod target, structure)
FROM base AS prod
COPY . /app
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser: /app
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

How to read the code:

`prod` never bind-mounts (code is baked in), drops privileges, and runs multiple workers.

What happens at runtime:

Compose `target: dev` for day-to-day; `target: prod` for the `frontend-prod`/production images.

Connects to: Byte 114, Byte 116 (Nginx), PART 32.

Remember: dev mounts `./backend:/app` — edits reload instantly; prod images do not.

---

### Byte 116: Nginx config

**Builds on:** Byte 22, Byte 115.

**Concept:** Production routing rules.

**In plain terms:**
Four locations: proxy `/api/` and `/uploads/` to `backend:8000`, cache immutable `/assets/`
fingerprints, and fall back to `index.html` for SPA routes.

**Why it exists:**
Same-origin API in production, correct cache headers, and deep-link refreshes that work.

**The code:**

```nginx
# frontend/nginx.conf
location /assets/ { expires 1y; add_header Cache-Control "public, immutable"; try_files $uri =404; }
location / { try_files $uri $uri/ /index.html; }
```

How to read the code:

Vite hashes filenames under `/assets/`, so a year of caching is safe; everything else falls back
to the SPA shell.

What happens at runtime:

`http://localhost:8080/admin/orders/64` (refresh) → index.html → router renders the details view.

Connects to: Byte 22, Byte 101 (uploads proxy), PART 32.

Remember: without `try_files … /index.html`, refreshing any route 404s.

---

### Byte 117: Environment variables

**Builds on:** Byte 114.

**Concept:** Configuration surface.

**In plain terms:**
`pydantic-settings` reads `.env` for the backend (PG/Mongo/ES/RabbitMQ/Celery/CORS/logging),
`VITE_API_BASE_URL` (+ `VITE_PROXY_TARGET`) for the frontend. `.env.example` is the template.

**Why it exists:**
Same code, different environments — credentials never hard-coded.

**The code:**

```python
# backend/app/core/config.py
model_config = SettingsConfigDict(
    env_file=".env", env_file_encoding="utf-8",
    case_sensitive=False, extra="ignore",
)
```

How to read the code:

`extra="ignore"` tolerates unrelated variables; `get_settings()` caches the instance.

What happens at runtime:

Missing vars fall back to defaults — including the two undocumented ones
(`JWT_SECRET_KEY`, `UPLOADS_DIR`).

Connects to: Byte 114, PART 33, PART 39 (gotcha #12).

Remember: rotate `JWT_SECRET_KEY` for any real deployment; the default is public knowledge.

---

### Byte 118: Health checks

**Builds on:** Byte 114.

**Concept:** Liveness/readiness for orchestration and operators.

**In plain terms:**
`GET /api/health` probes PostgreSQL, MongoDB, Elasticsearch and RabbitMQ with latency, returning
200 (all up) or 503 (degraded); compose uses it as the backend's container healthcheck, and
`depends_on: service_healthy` sequences startup.

**Why it exists:**
Startup ordering and a single endpoint that tells you *which* dependency is broken.

**The code:**

```python
# backend/app/api/health.py
checks = {"postgresql": ping_postgres, "mongodb": ping_mongo,
          "elasticsearch": ping_elasticsearch, "rabbitmq": ping_rabbitmq}
for name, probe in checks.items():
    up = probe()
    dependencies[name] = HealthDependency(status="up" if up else "down", latency_ms=...)
```

How to read the code:

Each probe is isolated and timed independently, so one outage doesn't hide the others.

What happens at runtime:

Healthcheck hits `/api/health` every 10 s; a 503 marks the container unhealthy and blocks
downstream starts.

Connects to: Byte 114, PART 40.

Remember: degraded health ≠ down API — endpoints not touching the broken dependency still work.

---

### Byte 119: Seed script

**Builds on:** Byte 118.

**Concept:** Deterministic demo data.

**In plain terms:**
`python -m scripts.seed` drops/rebuilds: 8 users, 26 active + 1 inactive products, 44 orders
(86 items) across three statuses and a 90-day window, applies the snapshot demo, reindexes, then
**asserts** every requirement.

**Why it exists:**
A demo and a test suite both need data they can rely on — and a script that fails loudly when
invariants break.

**The code:**

```python
# backend/scripts/seed.py (functions)
# seed_users() · seed_products() · seed_orders()
# apply_snapshot_demo()   # renames *Wireless Mouse* AFTER orders exist
# verify(expect_search=True)   # every requirement is an assertion
```

How to read the code:

`verify()` turns the README table (counts, distributions, `total_amount == Σline`, PG↔ES parity)
into executable checks — the seed fails if data drifts.

What happens at runtime:

Fixed RNG seed (`20240917`) → identical data every run → `--skip-search` skips indexing.

Connects to: Byte 120 (reindex), PART 35.

Remember: the snapshot mismatch (50.16 → 60.00) is *intentional*, and verified.

---

### Byte 120: Reindex script

**Builds on:** Byte 119, Byte 91.

**Concept:** Rebuilding the projection from the source of truth.

**In plain terms:**
`python -m scripts.reindex_orders [--recreate]` streams all PostgreSQL orders (batched via
`iter_orders`) and rewrites the ES index — the standard recovery when documents are missing or
the mapping changed.

**Why it exists:**
Proof that Elasticsearch holds nothing original: destroy and recreate it at will.

**The code:**

```python
# backend/app/repositories/postgres/order_repo.py
def iter_orders(session: Session, batch_size: int = 250) -> Iterator[Order]:
    # batched streaming over orders — used by scripts.reindex_orders
```

How to read the code:

Batching keeps memory flat regardless of order count; `--recreate` applies the current mapping
fresh.

What happens at runtime:

`docker compose run --rm reindex` → index dropped/created → ES doc count == PG row count.

Connects to: Byte 88, Byte 119, PART 40.5.

Remember: this is the recovery path for every "missing in search" scenario.

---

## SECTION N — TESTING

---

### Byte 121: Backend unit tests

**Builds on:** Byte 61, Byte 62.

**Concept:** Pure-logic tests that need no infrastructure.

**In plain terms:**
`tests/unit/` covers pricing (`to_money`, `calculate_total`, duplicate merging, quantity limits,
no-price-in-request), schema validation (statuses, ranges, pagination), the ES document builder,
and the search query builder.

**Why it exists:**
The invariants that protect money and search are deterministic — they should be tested without
Docker.

**The code:**

```python
# tests/unit/test_pricing.py
def test_order_create_has_no_price_fields() -> None:
    assert set(OrderCreate.model_fields) <= {"user_id", "items"}
```

How to read the code:

The test asserts the *absence* of money fields — the same contract documented in Byte 2.

What happens at runtime:

`.venv/bin/python -m pytest tests/unit` runs in milliseconds with zero services.

Connects to: Byte 122 (integration), PART 34.

Remember: a failing unit test here means a business rule changed, not that infra is down.

---

### Byte 122: Backend integration tests

**Builds on:** Byte 121.

**Concept:** Live tests against the real stack.

**In plain terms:**
`tests/integration/` exercises HTTP endpoints with real PostgreSQL/MongoDB/Elasticsearch:
catalog filtering/CRUD, order placement + rollback + snapshots, ES search/aggregations/poisoned
session, and the full sync pipeline (idempotency, retries, reindex parity).

**Why it exists:**
The architecture's claims (transactionality, projection equality, isolation) are only proven
against real services.

**The code:**

```python
# tests/integration/test_search_api.py
def test_search_service_never_touches_postgres_or_mongodb(client, ...):
    # the request must succeed even if PG/Mongo sessions are poisoned
```

How to read the code:

Poisoning the other sessions proves isolation — search would fail if it secretly queried them.

What happens at runtime:

Requires healthy infra (marked `integration`); skipped with an actionable message otherwise.

Connects to: Byte 123 (fixtures), Byte 125 (strategy), PART 34.

Remember: ES↔PG document parity (`test_elasticsearch_holds_exactly_one_document_per_postgres_order`)
is the projection's contract test.

---

### Byte 123: Fixtures

**Builds on:** Byte 122.

**Concept:** Shared test scaffolding in `conftest.py`.

**In plain terms:**
`api` (TestClient with lifespan), `admin_api` / `authenticated_api` (real login → bearer),
`order_factory` / `product_factory` (seeded entities), `es_document` / `es_delete` (index
helpers), plus an infra guard that skips integration tests when a dependency is unreachable.

**Why it exists:**
Auth and data setup is identical across dozens of tests — write it once.

**The code:**

```python
# tests/conftest.py
def _get_token_for_user(email: str, password: str) -> str:
    """Get a JWT token for a user by calling the login endpoint."""
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        if response.status_code != 200:
            raise RuntimeError(f"Failed to login as {email}: {response.text}")
        return response.json()["access_token"]
```

How to read the code:

Tests authenticate through the *real* login endpoint — the token path itself is exercised, not
mocked.

What happens at runtime:

`configure_logging("WARNING")` at import keeps logs quiet; factories create isolated rows per test.

Connects to: Byte 122, Byte 124, PART 34.

Remember: integration tests never fabricate tokens — they log in.

---

### Byte 124: Frontend tests

**Builds on:** Byte 35, Byte 37.

**Concept:** Vitest suites for the UI's pure logic.

**In plain terms:**
28 tests in 5 files: `cart.spec.js` (add/merge/clamp/subtotal/clear), `currency.spec.js` (₹
formatting), `status.spec.js` (three statuses, UTC timestamps), `components.spec.js`
(BaseButton/StatusBadge/KpiCard), `smoke.spec.js` (live-API renders for all major screens).

**Why it exists:**
Money formatting, clamping and status vocabulary are easy to regress silently.

**The code:**

```js
// frontend/tests/cart.spec.js
it('merges repeat adds into the same line instead of duplicating it', () => {
  const store = useCartStore()
  store.add(product, 1)
  store.add(product, 2)
  expect(store.itemCount).toBe(3)
  expect(store.lines).toHaveLength(1)
})
```

How to read the code:

Each test starts from a clean store state — which is exactly why cart persistence was never
added.

What happens at runtime:

`npm test` → `vitest run` in jsdom (`http://localhost:5173/` origin so CORS accepts requests).

Connects to: Byte 125 (strategy), Byte 136 (cart reset), PART 34.

Remember: `smoke.spec.js` talks to the **live** backend — start the stack before running it.

---

### Byte 125: Test strategy

**Builds on:** Byte 121-124.

**Concept:** The pyramid this project actually uses.

**In plain terms:**
Pure unit tests (fast, no services) → integration tests (real infra, HTTP) → frontend unit/smoke
tests → manual/automated browser QA (DOM geometry, pixel sampling at 7 breakpoints). No mocks of
your own services — the system is tested as a system.

**Why it exists:**
Mock-heavy suites pass while the wiring is broken; this stack is cheap to run for real.

**The code:**

```ini
# pytest.ini
testpaths = tests
pythonpath = backend
markers =
    integration: requires the Docker infrastructure (PostgreSQL / MongoDB / Elasticsearch / RabbitMQ)
    es: requires a reachable Elasticsearch
```

How to read the code:

Markers document requirements; `-ra` summarizes skips so missing infra is obvious, not silent.

What happens at runtime:

Unit-only runs work without Docker; full runs need `up -d --build` + `seed`.

Connects to: Byte 122, PART 34.

Remember: recorded results — pytest **100 passed**, vitest **28/28**, `npm run build` ✅.

---

### Byte 126: What failure tests prove

**Builds on:** Byte 125.

**Concept:** Tests that assert *degradation*, not just happy paths.

**In plain terms:**
Dedicated tests verify: full transaction rollback (row counts unchanged), publish failure that
doesn't roll back a committed order, retry backoff and max-retry give-up, task idempotency,
snapshot fidelity, and ES's independence from PG/Mongo.

**Why it exists:**
The system's value is in how it fails — these tests pin that behaviour down.

**The code:**

```python
# tests/integration/test_sync_task.py (test names, as run)
# test_sync_task_is_idempotent
# test_publish_failure_never_rolls_back_a_committed_order
# test_task_retries_with_backoff_when_elasticsearch_fails
# test_task_gives_up_after_max_retries
```

How to read the code:

Test *names* are the specification — each maps to a row in PART 10 §10.3's failure table.

What happens at runtime:

These run with RabbitMQ/ES present; a regression in messaging order or retry policy fails here
first.

Connects to: Byte 86, Byte 131 (rollback), PART 34.

Remember: if you change commit/publish ordering, these tests are the guardrail.

---

## SECTION O — EDGE CASES & RECOVERY

---

### Byte 127: Inactive product

**Builds on:** Byte 113.

**Concept:** Ordering something that was deactivated.

**In plain terms:**
Soft-deleted products stay in Mongo (`active:false`), disappear from the storefront, but remain
in old orders. Ordering one returns **422 `inactive_product`** with the product title in the
message.

**Why it exists:**
Availability is checked at order time, not trusted from the client's cached catalog.

**The code:**

```python
# backend/app/services/order_service.py
if not product.get("active", True):
    raise UnprocessableError(
        f"'{product.get('title', product_id)}' is no longer available and cannot be ordered.",
        code="inactive_product", details={...})
```

How to read the code:

Raised during `resolve_cart()` — *before* any database write.

What happens at runtime:

Checkout shows the server message; the user removes the line; nothing is written to PostgreSQL.

Connects to: Byte 74, Byte 113, PART 39.

Remember: deactivation hides a product — it never breaks history.

---

### Byte 128: Duplicate SKU

**Builds on:** Byte 17, Byte 58.

**Concept:** Conflicting catalog identity.

**In plain terms:**
`sku` is unique (Mongo index `uniq_products_sku` + service check). A create/update that reuses
another product's SKU returns **409 `ConflictError`**.

**Why it exists:**
SKU is the human-facing key for stock and fulfillment — duplicates corrupt operations.

**The code:**

```python
# backend/app/services/product_service.py (structure)
existing = product_repo.get_product_by_sku(payload.sku, exclude_id=product_id)
if existing:
    raise ConflictError(f"SKU '{payload.sku}' is already in use.", code="sku_conflict", ...)
```

How to read the code:

`exclude_id` lets an edit keep its *own* SKU while rejecting everyone else's.

What happens at runtime:

The modal maps the error onto the SKU field via `fieldErrorsFrom()`.

Connects to: Byte 58, Byte 14 (schema validation), PART 40.

Remember: the DB index is the final arbiter even if the service check were bypassed.

---

### Byte 129: Missing order in Elasticsearch

**Builds on:** Byte 87, Byte 120.

**Concept:** The projection lags or lacks a document.

**In plain terms:**
An order exists in PostgreSQL but isn't in search results: worker down, retries exhausted, or
the index was recreated without reindexing.

**Why it exists:**
This is the *expected* failure mode of eventual consistency — it must have a known recovery.

**The code:**

```python
# backend/app/tasks/elasticsearch_tasks.py
order = order_repo.get_order(session, order_id)
if order is None:
    return {"status": "skipped", "order_id": int(order_id), "reason": reason}
```

How to read the code:

The inverse case (task exists, row gone) is also handled — a no-op instead of an error.

What happens at runtime:

Confirm with `GET /api/orders/{id}` (authoritative) → run `docker compose run --rm reindex` →
search finds it.

Connects to: Byte 85, Byte 120, PART 40.5.

Remember: never "fix" this by writing to Elasticsearch from the API — that breaks the design.

---

### Byte 130: Sync failure response

**Builds on:** Byte 86.

**Concept:** Honest reporting when messaging fails.

**In plain terms:**
Every create/status response embeds `sync: {enqueued, task_id, queue, error}`. If RabbitMQ is
down: `enqueued:false` + error text, while HTTP status stays 201/200 because the write succeeded.

**Why it exists:**
Callers (and tests) can distinguish "order saved but not queued" from "order failed".

**The code:**

```json
"sync": { "enqueued": true, "task_id": "…", "queue": "orders_sync", "error": null }
```

How to read the code:

`queue:"in-process"` appears in eager/test mode or when no publish was needed (unchanged status).

What happens at runtime:

UI may toast success while `sync.error` is set — search simply lags until recovered.

Connects to: Byte 79, Byte 86, PART 10 §10.3.

Remember: `enqueued:false` never rolls back the order.

---

### Byte 131: Transaction rollback

**Builds on:** Byte 75.

**Concept:** What a rollback guarantees.

**In plain terms:**
Any exception during header/item insertion → `session.rollback()` → **zero rows** — no header
without items, no items without a header. The client receives 500
`order_persistence_failed` with "No data was written".

**Why it exists:**
Partial orders corrupt every downstream report.

**The code:**

```python
except Exception as exc:
    session.rollback()                    # ROLLBACK — never leave a partial order behind
    if isinstance(exc, AppError):
        raise
    raise OrderPersistenceError(
        "The order could not be saved. No data was written — please try again.") from exc
```

How to read the code:

`isinstance(exc, AppError)` preserves semantic errors (404 user not found) instead of masking
them as 500s.

What happens at runtime:

Asserted by comparing `orders`/`order_items` counts before and after the forced failure.

Connects to: Byte 75, Byte 126, PART 40.11.

Remember: the cart is client-side — a failed order leaves it intact for retry.

---

### Byte 132: Snapshot drift

**Builds on:** Byte 27, Byte 77.

**Concept:** Catalog and history intentionally disagree.

**In plain terms:**
After the seed demo, Mongo says `Wireless Mouse Pro / $60.00` while old orders say
`Wireless Mouse / $50.16` — both correct in their own store.

**Why it exists:**
To make the distinction demonstrable rather than theoretical.

**The code:**

```python
# backend/scripts/seed.py
# apply_snapshot_demo(): renames *Wireless Mouse* → *Wireless Mouse Pro* and
# reprices 50.16 → 60.00 AFTER orders exist; verify() asserts both sides.
```

How to read the code:

The demo is only meaningful because `verify()` checks that old orders *didn't* change.

What happens at runtime:

Storefront shows 60.00; `/admin/orders/{id}` and ES show 50.16; revenue math still adds up.

Connects to: Byte 27, Byte 77, PART 36.

Remember: drift here is a **feature**, not a data bug.

---

### Byte 133: Orphaned image file

**Builds on:** Byte 105.

**Concept:** Files without references.

**In plain terms:**
Deleting a product (or overwriting `image_url` outside the upload flow) can leave its file in
`uploads/products/` — no garbage collector exists (documented limitation).

**Why it exists:**
GC risks deleting a file still referenced elsewhere; the demo prefers manual inspection.

**The code:**

```python
# backend/app/api/products.py — deletion is always containment-checked
candidate = (UPLOAD_ROOT / rel).resolve()
try:
    candidate.relative_to(UPLOAD_ROOT.resolve())
except ValueError:
    return None          # outside the upload root → never delete
```

How to read the code:

The safety mechanism prevents wrong deletions; *missing* deletions are accepted as the
trade-off.

What happens at runtime:

Files accumulate harmlessly on the `uploads_data` volume; storage is bounded by upload size caps.

Connects to: Byte 104, Byte 105, PART 23.

Remember: orphaned ≠ broken — broken only happens when a *reference* outlives its file.

---

### Byte 134: Security recovery

**Builds on:** Byte 72.

**Concept:** Recovering from auth problems.

**In plain terms:**
Forgotten admin access → set `users.role='ADMIN'` in PostgreSQL; leaked/known JWT secret → set a
strong `JWT_SECRET_KEY` (invalidating all tokens); wrong password → 404 `invalid_credentials`
with identical messaging for unknown emails.

**Why it exists:**
Operators need deterministic recovery paths without seeding from scratch.

**The code:**

```python
# backend/app/core/auth.py
jwt_secret_key: str = "change-me-in-production-use-a-long-random-string"  # config default
```

How to read the code:

The default is deliberately obvious — safe for a demo, dangerous in production.

What happens at runtime:

Changing the secret makes old tokens fail signature checks → 401 → users log in again.

Connects to: Byte 67, Byte 70, PART 31, PART 40.6.

Remember: roles live in PostgreSQL, secrets live in `.env` — reseeding is rarely needed.

---

### Byte 135: Pagination & overflow

**Builds on:** Byte 40, Byte 50.

**Concept:** Wide tables and long lists at small widths.

**In plain terms:**
Tables (catalog, results) live inside `.table-scroll` with `position: relative` so horizontally
scrolling content and absolutely-positioned `.sr-only` spans can't widen the document; pagination
clamps to `1..pages` and ignores clicks while loading.

**Why it exists:**
Horizontal page scroll on mobile is the most common e-commerce layout bug.

**The code:**

```css
/* frontend/src/styles/utilities.css */
.table-scroll { position: relative; }
```

How to read the code:

The wrapper becomes the containing block for its children — an `.sr-only` span positioned
`absolute` no longer computes against the viewport and cannot extend `scrollWidth`.

What happens at runtime:

`window.scrollX === 0` at 375/414/768/1024/1280/1440/1920 (audited); tables scroll internally.

Connects to: Byte 40, Byte 50, PART 39 (gotcha #20).

Remember: check overflow with `scrollX`, not just eyeballing — `read` screenshots can be stale.

---

### Byte 136: Cart reset

**Builds on:** Byte 10, Byte 53.

**Concept:** When and why the cart empties.

**In plain terms:**
The cart clears on: successful order (`cart.clear()`), logout (store untouched but session
changes), and **browser refresh** (memory-only store). It survives all in-app navigation.

**Why it exists:**
Simplicity and deterministic tests — persistence would require merge/price-refresh semantics.

**The code:**

```js
// frontend/src/views/CheckoutView.vue
placedOrder.value = order
cart.clear()          // only after a successful response
```

How to read the code:

Placement of `clear()` *after* the await means failures keep the user's cart.

What happens at runtime:

Refresh mid-checkout → empty cart → user re-adds (server would re-price anyway).

Connects to: Byte 10, Byte 124, PART 15 §15.2.

Remember: this is a documented known limitation, not a bug.

---

### Byte 137: Elasticsearch migration / index change

**Builds on:** Byte 88, Byte 120.

**Concept:** Changing the mapping safely.

**In plain terms:**
ES mappings are largely immutable — a changed `ORDER_INDEX_MAPPING` requires
`reindex_orders --recreate` (drop → create with new mapping → rebuild from PostgreSQL).

**Why it exists:**
Explicit, repeatable migration instead of silent dynamic fields drifting the schema
(`dynamic: strict` blocks the silent path).

**The code:**

```python
# backend/app/repositories/elasticsearch/orders_repo.py
if exists and recreate:
    client.indices.delete(index=name)
    exists = False
if not exists:
    client.indices.create(index=name, settings=ORDER_INDEX_SETTINGS,
                          mappings=ORDER_INDEX_MAPPING)
```

How to read the code:

`recreate` is the only sanctioned way to change mapping; normal boots are no-ops.

What happens at runtime:

During rebuild, search briefly returns fewer results — order details (PG) are unaffected.

Connects to: Byte 88, Byte 120, PART 37.

Remember: never write directly to ES from the API "to patch" a mapping issue.

---

### Byte 138: End-to-end checklist

**Builds on:** All bytes — the final integration view.

**Concept:** One happy path that touches every subsystem.

**In plain terms:**

```
1  docker compose up -d --build          → 9 services, healthchecks green
2  docker compose run --rm seed          → 8 users / 26+1 products / 44 orders, verified
3  Open /  → hero + grid render from MongoDB
4  / + ⌘K search "wireless"              → ?q= → Mongo text filter → cards + scroll
5  ADD TO CART → badge → drawer slides in (button shifts left, inverts)
6  Login (admin) → /checkout → POST /api/orders
      → server re-prices → BEGIN/INSERT/COMMIT → sync.enqueued:true
7  RabbitMQ queue orders_sync → Celery worker → ES doc _id=order_id
8  /admin/search → POST /api/search/orders → KPIs + rows (Elasticsearch only)
9  Open order → PG snapshots displayed → PATCH status → sync → "Indexed"
10 /admin/catalog → edit → upload image → /uploads/… → thumb renders
11 Stop worker → place order → sync.enqueued may still be true but ES lags
12 docker compose run --rm reindex → parity restored
```

**Why it exists:**
Running this once end-to-end exercises every byte in this guide — transport, transaction,
projection, auth, storage and recovery.

**The code (the one invariant tying it together):**

```python
# backend/app/services/sync_service.py (docstring)
# Synchronisation publisher: PostgreSQL → RabbitMQ → Celery → Elasticsearch.
```

How to read the code:

Steps 6–7 are the only coupling between truth and search — everything else is read paths.

What happens at runtime:

Any broken step maps to a PART 40 troubleshooting entry.

Connects to: PART 40, PART 47 (30-minute path), PART 50 (checklist).

Remember: PostgreSQL decides what's real; everything else can be rebuilt.

---

# PART 42 — File-Specific Knowledge Bytes

Deep dives on the files that carry the system. Same byte structure, plus explicit file facts.

---

### Byte 139: `backend/app/main.py`

**Builds on:** Byte 54, Byte 64.

**In plain terms:** One module builds the whole HTTP application: middleware, error handlers, routers, static uploads and startup bootstrap.

**File facts:** Purpose — compose the FastAPI app. Layer — HTTP entry. Depends on — `core/*`,
`api/*`, `StaticFiles`. Used by — uvicorn, tests (`TestClient(app)`). Exports — `app`,
`init_infrastructure()`, `mount_upload_storage()`. Why it exists — one place wires the whole
API surface.

**Concept:** Application assembly + bootstrap.

**The code:**

```python
# backend/app/main.py
def init_infrastructure() -> None:
    """Create schema/indexes at startup. Each step is best-effort except PG."""
    create_tables()
    try:
        ensure_catalog_indexes()
    except Exception as exc:
        logger.warning("could not ensure MongoDB indexes: %s", exc)
```

How to read the code:

Called from the `lifespan` context manager; PG is mandatory, Mongo/ES best-effort.

What happens at runtime:

Import → register CORS/handlers/routers → mount `/uploads` → lifespan → ready.

Connects to: Bytes 54, 64, 101. Remember: `/uploads` is mounted at import time, before any
request.

---

### Byte 140: `backend/app/core/config.py`

**Builds on:** Byte 21, Byte 117.

**In plain terms:** Reads `.env` once into a cached `Settings` object, then derives DSNs, broker URL, CORS origins, uploads path and task name.

**File facts:** Purpose — typed settings from env. Layer — config. Depends on — `.env`.
Used by — every backend module. Exports — `Settings`, `get_settings()`. Why it exists — no
magic constants scattered through the code.

**Concept:** Single cached configuration object.

**The code:**

```python
# backend/app/core/config.py
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

How to read the code:

`lru_cache` guarantees one instance (cheaper and consistent); tests can `cache_clear()` to
reload.

What happens at runtime:

Env → `Settings` fields → derived properties (`postgres_dsn`, `broker_url`, `cors_origin_list`,
`uploads_path`, `sync_task_name`).

Connects to: Bytes 114, 117. Remember: `JWT_SECRET_KEY` and `UPLOADS_DIR` are **not** in
`.env.example`.

---

### Byte 141: `backend/app/core/errors.py`

**Builds on:** Byte 13, Byte 61.

**In plain terms:** Turns every application error - and every crash - into the single `{"error": ...}` JSON response shape.

**File facts:** Purpose — error hierarchy + JSON envelope + handlers. Layer — HTTP. Depends on —
FastAPI. Used by — all services/routes. Exports — `AppError`, `NotFoundError`, `ConflictError`,
`UnprocessableError`, `DependencyUnavailableError`, `register_exception_handlers`. Why it exists —
one error shape for every failure.

**Concept:** Turning exceptions into API responses.

**The code:**

```python
# backend/app/core/errors.py
def _error_response(status_code: int, payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(status_code=status_code,
                        content=jsonable_encoder({"error": payload}))
```

How to read the code:

Every `AppError` becomes `{"error":{code,message,details}}` at its own status code; validation
and crash handlers build the same envelope.

What happens at runtime:

404/409/422/503 all look identical to `toApiError()` — except 401/403 (no `HTTPException`
handler → FastAPI `detail` shape).

Connects to: PART 30, Byte 131. Remember: the envelope is a contract with the frontend.

---

### Byte 142: `backend/app/core/database.py`

**Builds on:** Byte 64, Byte 75.

**In plain terms:** Owns the SQLAlchemy engine and session factory, plus the dependency that opens a session and always closes it in `finally`.

**File facts:** Purpose — engine/session/ping. Layer — data access. Depends on — config. Used by —
auth, services, tests. Exports — `engine`, `SessionLocal`, `get_db_session`, `ping_postgres`,
`create_tables`. Why it exists — connection pooling and lifecycle in one place.

**Concept:** SQLAlchemy session management.

**The code:**

```python
# backend/app/core/database.py
engine = create_engine(settings.postgres_dsn, pool_pre_ping=True,
                        pool_size=settings.db_pool_size, max_overflow=0)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False,
                            expire_on_commit=False)
```

How to read the code:

`pool_pre_ping` drops dead connections (container restarts); `expire_on_commit=False` lets
responses serialize after commit; `autoflush=False` means `flush()` calls are explicit (as seen
in order creation).

What happens at runtime:

Each request/service opens a pooled session and closes it in `finally`.

Connects to: Bytes 64, 75. Remember: `ping_postgres()` powers `/api/health`.

---

### Byte 143: `backend/app/services/order_service.py`

**Builds on:** Byte 61, Byte 74.

**In plain terms:** The module where cart lines are resolved, priced, merged and quantized, then written to PostgreSQL in one transaction with snapshots.

**File facts:** Purpose — pricing, transactions, snapshots, status. Layer — business logic. Depends
on — mongo `product_repo`, postgres `order_repo`, `sync_service`, schemas. Used by —
`api/orders.py`, `api/users.py`. Exports — `create_order`, `get_order`, `update_order_status`,
`resolve_cart`, `merge_duplicate_lines`, `calculate_total`, `to_money`, `ResolvedLine`. 

**Why it exists:** the only place money and persistence rules live.

**Concept:** The heart of the system.

**The code:**

```python
def calculate_total(lines: list[ResolvedLine]) -> Decimal:
    """The single authoritative order total: SUM(quantity * unit_price)."""
    return sum((line.line_total for line in lines), Decimal("0.00")).quantize(CENT)
```

How to read the code:

`Decimal` throughout, `CENT` quantization — no floats anywhere near money.

What happens at runtime:

`create_order` = validate → BEGIN → INSERT ×2 → COMMIT → publish; `update_order_status` = its own
transaction.

Connects to: Bytes 74-79, 131. Remember: "canonical order details, straight from PostgreSQL".

---

### Byte 144: `backend/app/services/sync_service.py`

**Builds on:** Byte 78, Byte 79.

**In plain terms:** A small publisher invoked only after commit: it reports whether the sync task reached RabbitMQ (or ran inline in eager mode).

**File facts:** Purpose — publish sync tasks after commit. Layer — business logic. Depends on —
Celery app, config. Used by — `order_service`. Exports — `publish_order_sync`, `EAGER_QUEUE`.
Why it exists — messaging failures must never become write failures.

**Concept:** The publish boundary.

**The code:**

```python
# backend/app/services/sync_service.py (module docstring)
"""Synchronisation publisher: PostgreSQL → RabbitMQ → Celery → Elasticsearch.
The API only *publishes* a task after the PostgreSQL transaction has committed.
"""
```

How to read the code:

"Only publishes" is the responsibility split — building/updating ES is the worker's job.

What happens at runtime:

Eager mode runs inline (`queue:"in-process"`); live mode returns `task_id` or
`enqueued:false`.

Connects to: Bytes 79, 86, 130. Remember: it is called *after* commit, never before.

---

### Byte 145: `backend/app/tasks/celery_app.py`

**Builds on:** Byte 19, Byte 20.

**In plain terms:** The Celery definition: JSON payloads, the `orders_sync` queue, late acks, time limits and the retry/backoff policy.

**File facts:** Purpose — Celery client/worker config. Layer — worker. Depends on — broker URL,
settings. Used by — `sync_service`, `elasticsearch_tasks`, compose worker command. Exports —
`celery_app`. Why it exists — all reliability knobs in one file.

**Concept:** Worker configuration.

**The code:**

```python
# backend/app/tasks/celery_app.py (reliability block)
task_acks_late=True,
task_reject_on_worker_lost=True,
worker_prefetch_multiplier=1,
task_time_limit=120,
task_soft_time_limit=90,
```

How to read the code:

Ack-after-execution + reject-on-lost = a crashed worker's task returns to the queue; prefetch 1
keeps fairness with `--concurrency=2`.

What happens at runtime:

Worker boots, imports `app.tasks.elasticsearch_tasks`, binds `orders_sync`.

Connects to: Bytes 80, 81, 85. Remember: `backend=None` — results live in the databases.

---

### Byte 146: `backend/app/tasks/elasticsearch_tasks.py`

**Builds on:** Byte 83, Byte 85.

**In plain terms:** Worker-side entry point that re-reads an order from PostgreSQL, builds its document, upserts it into Elasticsearch and records the timestamp.

**File facts:** Purpose — the sync task. Layer — worker. Depends on — `order_repo`,
`document.build_order_document`, `orders_repo`. Used by — Celery broker, reindex script.
Exports — `sync_order_to_elasticsearch`, `sync_document`, `TASK_NAME`. Why it exists — the
rebuild-and-upsert worker loop with retries.

**Concept:** Task anatomy.

**The code:**

```python
# backend/app/tasks/elasticsearch_tasks.py
TASK_NAME = "app.tasks.elasticsearch_tasks.sync_order_to_elasticsearch"

def sync_document(order_id, reason):
    order = order_repo.get_order(session, order_id)
    if order is None:
        return {"status": "skipped", ...}
    document = build_order_document(order)
    ensure_index()
    index_order_document(document)
    _record_indexed_at(order_id)      # best-effort bookkeeping
```

How to read the code:

Synchronous core reused by the reindex script; the Celery wrapper adds retries around it.

What happens at runtime:

Message → PG read → doc build → upsert → `search_indexed_at` → stats dict.

Connects to: Bytes 82-85, 147. Remember: nothing from MongoDB ever enters this path.

---

### Byte 147: `backend/app/repositories/elasticsearch/document.py`

**Builds on:** Byte 84, Byte 90.

**In plain terms:** A pure PostgreSQL to Elasticsearch mapper: given an already-loaded `Order`, it returns exactly the dictionary that gets stored.

**File facts:** Purpose — pure ES document builder. Layer — data shaping. Depends on — SQLAlchemy
`Order` only. Used by — worker task, reindex, tests. Exports — `build_order_document`. 

**Why it exists:** isolating the projection shape makes it unit-testable.

**Concept:** Pure projection mapping.

**The code:**

```python
# backend/app/repositories/elasticsearch/document.py (module docstring)
"""Elasticsearch order document builder.

`build_order_document()` is a pure function: it only reads the already
loaded SQLAlchemy `Order` ... The document contains snapshots stored in
PostgreSQL — never live MongoDB product data.
```

How to read the code:

Purity means same input → same `_id` and byte-identical document (idempotency by construction).

What happens at runtime:

Called with a fully-loaded `Order` (items + user) — no queries inside.

Connects to: Bytes 84, 87, 146. Remember: this file is the anti-corruption layer between PG and
ES.

---

### Byte 148: `backend/app/repositories/mongo/product_repo.py`

**Builds on:** Byte 17, Byte 24.

**In plain terms:** Every MongoDB query the catalog needs - filters, facets, CRUD, indexes - in one module.

**File facts:** Purpose — all catalog queries. Layer — data access. Depends on — PyMongo client.
Used by — `product_service`, `order_service.resolve_cart`. Exports — `list_products`,
`get_product`, `get_products_by_ids`, `create/update/delete_product`, `list_facets`,
`ensure_indexes`. Why it exists — Mongo filter/sort/facet logic in one module.

**Concept:** The document query layer.

**The code:**

```python
# backend/app/repositories/mongo/product_repo.py (docstring)
"""Product catalog repository (MongoDB).
... Orders are *never* read from MongoDB — PostgreSQL owns those.
"""
```

How to read the code:

`_build_filter()` composes `active` + `q` (regex) + `category` + `tags` (all-of) + price bounds;
`list_products()` adds sort/skip/limit.

What happens at runtime:

Every storefront/admin catalog request funnels through these functions.

Connects to: Bytes 17, 24, 74. Remember: `get_products_by_ids()` is the checkout validation
path.

---

### Byte 149: `backend/app/api/products.py` (image endpoints)

**Builds on:** Byte 58, Byte 99.

**In plain terms:** The product routes plus the image endpoints that validate, save, replace and safely delete files.

**File facts:** Purpose — catalog routes + image upload/replace/remove. Layer — HTTP. Depends on —
`product_service`, `product_repo`, auth. Used by — router. Exports — `router`, `UPLOAD_DIR`,
`_validate_image_file`, `_stored_image_path`. Why it exists — file handling needs careful
validation and containment that belongs next to the route.

**Concept:** The upload endpoint's five-step pipeline.

**The code:**

```python
# backend/app/api/products.py
filename = _generate_safe_filename(file.filename)   # uuid4().hex + whitelisted ext
destination = UPLOAD_DIR / filename
await _save_upload_file(file, destination)          # 5 MB cap
...
new_image_url = f"/uploads/products/{filename}"
updated = product_repo.update_product(product_id, {"image_url": new_image_url})
```

How to read the code:

Order matters: validate → save → delete old → update Mongo → compensate (delete new) on failure.

What happens at runtime:

Multipart POST → file on the volume → reference in Mongo → `ProductResponse` back.

Connects to: Bytes 99-105. Remember: client filenames never reach the filesystem.

---

### Byte 150: `backend/scripts/seed.py`

**Builds on:** Byte 119, Byte 132.

**In plain terms:** Builds the entire demo dataset from scratch, applies the snapshot demo, then asserts the documented requirements against it.

**File facts:** Purpose — deterministic self-verifying demo data. Layer — script. Depends on —
all stores + reindex. Used by — `docker compose run --rm seed`. Exports — `run`, `verify`,
`USERS`, `PRODUCTS`. Why it exists — a demo and CI both need guaranteed data.

**Concept:** Seeding as executable specification.

**The code:**

```python
# backend/scripts/seed.py (functions)
# seed_users() · seed_products() · seed_orders()
# apply_snapshot_demo()      # rename/reprice AFTER orders exist
# verify(expect_search=True) # every README requirement is an assertion
```

How to read the code:

`verify()` fails the run if counts, distributions, totals or PG↔ES parity drift.

What happens at runtime:

Drop → rebuild → snapshot demo → reindex → assertions pass → exit 0.

Connects to: Bytes 119, 132. Remember: idempotent — run it as often as you like.

---

### Byte 151: `frontend/src/layouts/StorefrontLayout.vue`

**Builds on:** Byte 32, Byte 41.

**In plain terms:** Persistent storefront chrome that owns the search input, the cart-open flag, the keyboard shortcuts and the drawer.

**File facts:** Purpose — storefront chrome + single search + cart. Layer — UI. Depends on —
`AppIcon`, `CartDrawer`, `useCartStore`, `useAuthStore`, `debounce`. Used by — router (parent of
all storefront routes). Exports — default component. Why it exists — shared state
(`cartOpen`, `searchInput`) across every storefront page.

**Concept:** The layout as a state owner.

**The code:**

```js
// frontend/src/layouts/StorefrontLayout.vue
const onKeydown = (event) => {
  if (event.key === '/' || ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k')) {
    event.preventDefault()
    focusSearch()
  }
}
```

How to read the code:

The shortcut is skipped when focus is already in a text field (typing `/` must insert a slash).

What happens at runtime:

Announce → header (search/cart/account) → `<router-view>` → footer → drawer.

Connects to: Bytes 32, 41-43, 51. Remember: mobile nav panel shares the same `searchInput` ref.

---

### Byte 152: `frontend/src/stores/cart.js`

**Builds on:** Byte 10, Byte 34.

**In plain terms:** The complete cart: an `items` map, clamped quantities, snapshot prices, and the derived lines/count/subtotal getters.

**File facts:** Purpose — cart state. Layer — state. Depends on — Pinia only. Used by —
ProductCard flows, CartDrawer, CheckoutView. Exports — `useCartStore`, `MIN_QTY`, `MAX_QTY`.
Why it exists — cross-component cart without prop drilling.

**Concept:** The whole store.

**The code:**

```js
// frontend/src/stores/cart.js
const clampQty = (value) => Math.min(MAX_QTY, Math.max(MIN_QTY, Number.isFinite(+value) ? +value : MIN_QTY))
```

How to read the code:

Single clamp function used by `add`, `setQuantity`, `increment`, `decrement` — one rule, four
call sites.

What happens at runtime:

Actions mutate `items[id]`; getters (`lines`, `itemCount`, `subtotal`) recompute automatically.

Connects to: Bytes 3, 35, 124, 136. Remember: no `persist` — memory only, by design.

---

### Byte 153: `frontend/src/api/client.js`

**Builds on:** Byte 12, Byte 36.

**In plain terms:** The single Axios instance - base-URL resolution, auth header injection, and interceptors that normalize responses and errors.

**File facts:** Purpose — transport + errors. Layer — client. Depends on — axios, env. Used by —
all `api/*.js` and `utils/image.js`. Exports — default `client`, `API_BASE_URL`, `ApiError`,
`toApiError`, `messageFrom`, `fieldErrorsFrom`, `resolveBaseUrl`. Why it exists — one place for
URL/auth/timeout/error semantics.

**Concept:** Base URL resolution.

**The code:**

```js
// frontend/src/api/client.js
export function resolveBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (configured === '') return ''            // '' → relative /api (vite/nginx proxy)
  return (configured || 'http://localhost:8000').replace(/\/+$/, '')
}
```

How to read the code:

Three modes: configured absolute URL, empty string (proxy), or localhost default.

What happens at runtime:

`baseURL` drives all requests *and* is exported for image URL prefixing.

Connects to: Bytes 12, 36, 38. Remember: `paramsSerializer: {indexes:null}` makes `?tags=a&tags=b`
work with FastAPI.

---

### Byte 154: `frontend/src/utils/image.js`

**Builds on:** Byte 38, Byte 106.

**In plain terms:** Chooses how a stored image path becomes a URL: prefix the API origin, pass an absolute/`data:`/`blob:` URL through, or leave a bundled asset relative.

**File facts:** Purpose — image URL resolution. Layer — utility. Depends on — `API_BASE_URL`.
Used by — `ProductThumb`, product views. Exports — `resolveImageUrl`. Why it exists — stored
relative URLs must work behind any proxy.

**Concept:** URL classification.

**The code:**

```js
// frontend/src/utils/image.js (branches)
// absolute http(s):// | data: | blob:  → returned untouched
// '/uploads/...'  + API_BASE_URL set   → prefixed with the API origin
// everything else ('/products/ORG-001.svg') → left relative
```

How to read the code:

Classification avoids double-prefixing and keeps bundled assets same-origin.

What happens at runtime:

Dev: `/uploads/products/x.webp` → proxied to `:8000`; prod: same-origin through Nginx.

Connects to: Bytes 38, 106. Remember: `null` (no URL) → placeholder, not a broken `<img>`.

---

### Byte 155: `frontend/src/components/common/ProductThumb.vue`

**Builds on:** Byte 49, Byte 106.

**In plain terms:** Shared image component: lazy loading, error fallback to a deterministic placeholder, and size variants for cards and tables.

**File facts:** Purpose — resilient product image. Layer — UI. Depends on — `resolveImageUrl`,
`AppIcon`. Used by — ProductCard, CatalogTable, CartDrawer, CheckoutLineItems. Exports — default
component (`size` prop). Why it exists — every image surface shares loading/error/placeholder
behaviour.

**Concept:** The image state machine.

**The code:**

```vue
<!-- frontend/src/components/common/ProductThumb.vue -->
<img v-if="showImage" :src="imageUrl" :alt="product.title"
     loading="lazy" decoding="async" @load="onLoad" @error="onError" />
<div v-else class="thumb__placeholder"> …deterministic monogram/pattern… </div>
```

How to read the code:

`showImage = imageUrl && !failed`; states: loading → loaded / failed → placeholder.

What happens at runtime:

Failed load flips `failed` permanently for that URL (until the prop changes).

Connects to: Bytes 49, 97, 106. Remember: `size="sm"` for admin tables, default for cards.

---

### Byte 156: `frontend/src/views/AdminSearchView.vue`

**Builds on:** Byte 95, Byte 109.

**In plain terms:** Admin dashboard that turns filter state into a `SearchRequest` and renders KPIs, table/card rows and pagination.

**File facts:** Purpose — ES search dashboard. Layer — UI. Depends on — `searchOrders`,
`SearchFilters/Kpis/ResultsTable/ResultsCardList`. Used by — router. Exports — default
component. Why it exists — the only screen that talks to `/api/search/orders`.

**Concept:** Payload assembly from UI state.

**The code:**

```js
// frontend/src/views/AdminSearchView.vue:155-162
const payload = { page: page.value, limit: PAGE_SIZE }
if (term) payload.query = term
if (statuses.value.length) payload.status = [...statuses.value]
if (dateFrom.value) payload.date_from = dateFrom.value
if (dateTo.value) payload.date_to = dateTo.value
if (minPrice.value !== '') payload.min_price = Number(minPrice.value)
if (maxPrice.value !== '') payload.max_price = Number(maxPrice.value)
```

How to read the code:

Omitted keys = no filter; `PAGE_SIZE` (20) is fixed client-side to keep paging predictable.

What happens at runtime:

Debounced refresh → `searchOrders` → `total/pages/took_ms/aggregations` → KPIs + rows.

Connects to: Bytes 95, 108-110. Remember: filters reset `page` to 1.

---

### Byte 157: `docker-compose.yml`

**Builds on:** Byte 21, Byte 114.

**In plain terms:** The manifest that starts, wires, health-checks and volumes the full nine-service stack.

**File facts:** Purpose — environment definition. Layer — config. Depends on — the two Dockerfiles.
Used by — every `docker compose` command. Exports — 9 services, 6 volumes, `app_net`. 

**Why it exists:** the polyglot stack must start in order, wired, health-checked.

**Concept:** Service topology.

**The code:**

```yaml
celery-worker:
  command: celery -A app.tasks.celery_app worker --loglevel=INFO --concurrency=2
  depends_on:
    postgres:    { condition: service_healthy }
    elasticsearch:{ condition: service_healthy }
    rabbitmq:    { condition: service_healthy }
```

How to read the code:

The worker waits for *its* dependencies (PG, ES, RabbitMQ) — not MongoDB, since it never reads
Mongo.

What happens at runtime:

Profiles gate `frontend-prod` (prod) and `seed`/`reindex` (tools).

Connects to: Bytes 114, 118, 158. Remember: `uploads_data` is mounted on **both** backend and
worker.

---

### Byte 158: `frontend/nginx.conf`

**Builds on:** Byte 22, Byte 116.

**In plain terms:** Production routing: static `dist/`, proxied `/api` and `/uploads`, immutable asset caching, SPA fallback.

**File facts:** Purpose — production routing. Layer — infrastructure. Depends on — the built
`dist/`. Used by — `frontend-prod` image. Exports — server block. Why it exists — same-origin API
+ SPA fallback in production.

**Concept:** Proxy + fallback.

**The code:**

```nginx
# frontend/nginx.conf
location /uploads/ { proxy_pass http://backend:8000; }   # images
location /assets/  { expires 1y; add_header Cache-Control "public, immutable"; try_files $uri =404; }
location /         { try_files $uri $uri/ /index.html; }
```

How to read the code:

`proxy_pass` with a path-less target forwards the full URI; asset caching is safe due to Vite
hashing.

What happens at runtime:

Browser → `:8080` → Nginx routes to static files, backend, or SPA shell.

Connects to: Bytes 22, 116, 115. Remember: dev has the same behaviour via Vite's proxy.

---

# PART 43 — Code Snippets

Curated index of the load-bearing snippets in this guide (each already shown in full with its
byte/part). Reading these in order is a compressed tour of the system.

| # | Snippet | Location | Byte / Part |
| --- | --- | --- | --- |
| 1 | `app = FastAPI(title=..., description="…PostgreSQL → RabbitMQ → Celery → Elasticsearch…")` | `app/main.py` | Byte 1 |
| 2 | `class OrderCreate: items: list[OrderItemCreate]` (no money fields) | `schemas/orders.py` | Byte 2 |
| 3 | `cart.add()` snapshot line | `stores/cart.js` | Byte 3 |
| 4 | `require_admin` role check | `core/auth.py` | Byte 4 |
| 5 | Repo docstring: *"Orders are **never** read from MongoDB"* | `repositories/mongo/product_repo.py` | Byte 5 |
| 6 | Sync docstring: PostgreSQL → RabbitMQ → Celery → ES | `services/sync_service.py` | Byte 6 |
| 7 | `GET /api/orders/{id}` — *"canonical order details (never Elasticsearch)"* | `api/orders.py` | Byte 7 |
| 8 | Vite `/api` + `/uploads` proxy | `vite.config.js` | Byte 9 |
| 9 | `defineStore('cart', …)` getters/actions | `stores/cart.js` | Byte 10 |
| 10 | `scrollBehavior → false` for query-only changes | `router/index.js` | Byte 11 |
| 11 | Response interceptors (`response.data` / `toApiError`) | `api/client.js` | Byte 12 |
| 12 | `@router.post("", response_model=OrderCreateResponse, status_code=201)` | `api/orders.py` | Byte 13 |
| 13 | `ProductBase.sku` pattern + `price` bounds | `schemas/products.py` | Byte 14 |
| 14 | `class Order(Base)` — `order_number unique`, `total_amount Numeric(12,2)` | `models/postgres.py` | Byte 15 |
| 15 | `CheckConstraint("role IN ('CUSTOMER','ADMIN')")` | `models/postgres.py` | Byte 16 |
| 16 | `ensure_indexes()` unique SKU + category/active indexes | `product_repo.py` | Byte 17 |
| 17 | `"dynamic": "strict"` mapping | `mappings.py` | Byte 18 |
| 18 | `send_task(..., queue="orders_sync")` | `sync_service.py` | Byte 19 |
| 19 | Celery `task_acks_late`, `visibility_timeout 3600`, `backend=None` | `celery_app.py` | Byte 20 |
| 20 | Compose: health-gated `depends_on` + `uploads_data` | `docker-compose.yml` | Byte 21 |
| 21 | `try_files $uri $uri/ /index.html` | `nginx.conf` | Byte 22 |
| 22 | `session.begin() → flush → commit / rollback` + publish-after-commit | `order_service.py` | Bytes 75, 78 |
| 23 | `f"ORD-{order.id:06d}"` | `order_service.py` | Byte 76 |
| 24 | Snapshot writes (`title=`, `unit_price=`) | `order_service.py` | Byte 77 |
| 25 | Task core: get → build → ensure → index → `_record_indexed_at` | `elasticsearch_tasks.py` | Byte 83 |
| 26 | `TEXT_FIELDS = ["customer.name^3", "customer.email", "order_number"]` | `search_repo.py` | Byte 91 |
| 27 | Image constants (types/extensions/5 MB) | `api/products.py` | Byte 100 |
| 28 | `_stored_image_path` containment check | `api/products.py` | Byte 104 |
| 29 | `StaticFiles` mount at `/uploads` | `main.py` | Byte 101 |
| 30 | `SearchAggregations` contract | `schemas/search.py` | Byte 94 |
| 31 | `.table-scroll { position: relative }` | `styles/utilities.css` | Byte 135 |
| 32 | `sync: {enqueued, task_id, queue, error}` | responses | Byte 130 |

---

# PART 44 — Cross-Reference System

## 44.1 Byte ↔ file matrix (primary files only)

| File | Core bytes | Part coverage |
| --- | --- | --- |
| `order_service.py` | 25, 26, 57, 74–79, 131, 143 | 10, 21, 29 |
| `sync_service.py` | 19, 79, 86, 130, 144 | 8, 10, 11 |
| `celery_app.py` / `elasticsearch_tasks.py` | 20, 81–86, 145, 146 | 11 |
| `document.py` / `orders_repo.py` / `mappings.py` | 28, 84, 88–90, 147 | 9.3, 37 |
| `search_repo.py` / `search_service.py` | 61, 91–94 | 9.3, 29 |
| `product_repo.py` | 17, 24, 74, 148 | 9.2, 29 |
| `api/products.py` | 58, 99–105, 149 | 8, 23, 31 |
| `api/orders.py` / `api/search.py` | 59, 60, 71 | 3, 8 |
| `core/auth.py` | 4, 56, 57, 65–70 | 12, 31 |
| `core/errors.py` | 30, 141 | 30 |
| `seed.py` / `reindex_orders.py` | 119, 120, 150, 132 | 35, 37 |
| `StorefrontLayout.vue` | 32, 41–43, 51, 151 | 17, 18 |
| `stores/cart.js` | 3, 10, 35, 52, 152 | 15, 20 |
| `api/client.js` | 12, 36, 153 | 16, 30 |
| `ProductThumb.vue` / `image.js` | 38, 96, 106, 154, 155 | 23 |
| `AdminSearchView.vue` | 95, 107–110, 156 | 22 |
| `docker-compose.yml` / `nginx.conf` | 21, 22, 114–118, 157, 158 | 32, 33 |

> Byte ids are unique and continuous across sections A–O (Byte 1 … Byte 158).

## 44.2 Concept cross-reference (which bytes discuss the same idea)

| Concept | Primary byte | Reinforced in |
| --- | --- | --- |
| Source of truth | 7 | 87, 111, 138 |
| Snapshot semantics | 27 | 77, 132, PART 36 |
| Publish after commit | 78 | 79, 86, 130 |
| Idempotent projection | 84 | 83, 87, 129 |
| Server-side pricing | 74 | 2, 26, 143 |
| Role-based access | 70 | 4, 57, 72 |
| Single search UX | 43 | 11, 18, PART 18 |
| Image pipeline | 96–106 | 23, 39, PART 23 |
| Graceful degradation | 86 | 85, 126, 130 |
| Deterministic demo data | 119 | 132, PART 35 |

## 44.3 Reading paths by role

| You are… | Read first | Then |
| --- | --- | --- |
| New frontend dev | Bytes 1–4, 8–12 | D + E sections, PART 17–21 |
| New backend dev | Bytes 5–7, 13–20 | F + H + I sections, PART 10–11, 26–29 |
| SRE / DevOps | Bytes 21–22, 114–118 | M section, PART 32–33, 40 |
| Reviewer / architect | Bytes 6–7, 86–87 | PART 5, 38, 10 §10.3, 37 |
| QA engineer | Bytes 119–126 | PART 34–35, 39–40 |

---

# PART 45 — Complete File Index

Every tracked file (146 at the time of writing) plus the known untracked additions, grouped by
area and labelled by category.

**Categories:** **CORE** (the system stops working without it) · **SUPPORTING** (real behaviour,
but replaceable) · **CONFIGURATION** · **TEST** · **GENERATED** (do not edit by hand) ·
**SCRIPT** (runnable tooling) · **ASSET** (static content).

## 45.1 Repository root

| File | Category | Purpose |
| --- | --- | --- |
| `README.md` | SUPPORTING | Primary documentation (§1–17); cross-checked against code in this guide |
| `docker-compose.yml` | CORE | 9 services, 6 volumes, healthchecks, env anchor |
| `.env.example` | CONFIGURATION | Config template (no `JWT_SECRET_KEY`/`UPLOADS_DIR` — see PART 33) |
| `.gitignore` | CONFIGURATION | Ignores `.env`, venvs, `node_modules`, `dist`, caches |
| `pytest.ini` | CONFIGURATION | testpaths, markers (`integration`, `es`), pythonpath |
| `Knowledge bytes/Knowledge_Bytes.txt` | SUPPORTING | Legacy byte notes — partly outdated (roles, search); prefer this guide |
| `docs/MERIDIAN_COMPLETE_SYSTEM_KNOWLEDGE.md` | SUPPORTING | This document (untracked until committed) |
| `update_images.py`, `update_all_images.py` | SCRIPT | Untracked local helpers for seeding/patching product images — left untouched |
| `.env`, `.venv/`, `.pytest_cache/` | GENERATED | Local runtime/venv — never commit |

## 45.2 Backend — `backend/`

| File | Category | Purpose |
| --- | --- | --- |
| `backend/Dockerfile` | CONFIGURATION | 3 stages: `base` → `dev` → `prod` (non-root, `--workers 2`) |
| `backend/requirements.txt` | CONFIGURATION | Runtime deps (fastapi, pydantic-settings, sqlalchemy, psycopg, pymongo, elasticsearch, celery, python-jose, passlib, python-multipart, uvicorn, kombu…) |
| `backend/requirements-dev.txt` | CONFIGURATION | Test/dev extras (pytest, httpx, …) |
| `backend/scripts/seed.py` | SCRIPT | Deterministic, self-verifying demo data + snapshot demo + reindex |
| `backend/scripts/reindex_orders.py` | SCRIPT | Rebuild ES index from PostgreSQL (`--recreate`) |
| `backend/scripts/__init__.py` | SUPPORTING | Package marker |
| `backend/update_images.py`, `backend/update_all_images.py` | SCRIPT | Untracked local image helpers (not part of the tracked system) |

### `backend/app/` — entry & core

| File | Category | Purpose |
| --- | --- | --- |
| `app/main.py` | CORE | App assembly, CORS, handlers, routers, lifespan, `/uploads` mount |
| `app/__init__.py` | SUPPORTING | `__version__` |
| `app/core/config.py` | CORE | Settings + derived DSN/broker/CORS/uploads/task name |
| `app/core/auth.py` | CORE | bcrypt, JWT, `get_current_user`, `require_admin`, `get_db` |
| `app/core/database.py` | CORE | Engine, `SessionLocal`, `get_db_session`, `ping_postgres`, `create_tables` |
| `app/core/errors.py` | CORE | `AppError` family + JSON envelope + exception handlers |
| `app/core/logging.py` | SUPPORTING | `configure_logging`, `get_logger` |
| `app/core/__init__.py` | SUPPORTING | Package marker |

### `backend/app/` — HTTP layer

| File | Category | Purpose |
| --- | --- | --- |
| `app/api/products.py` | CORE | Catalog routes + image upload/replace/remove |
| `app/api/orders.py` | CORE | Place/read/status-order routes (PG, ownership, admin) |
| `app/api/search.py` | CORE | `POST /api/search/orders` (admin, ES only) |
| `app/api/auth.py` | CORE | login / logout / me |
| `app/api/users.py` | SUPPORTING | `GET /api/users` (seeded customers, no auth dependency) |
| `app/api/health.py` | CORE | 4-dependency health probe (200/503) |
| `app/api/__init__.py` | SUPPORTING | Package marker |

### `backend/app/` — business logic

| File | Category | Purpose |
| --- | --- | --- |
| `app/services/order_service.py` | CORE | Pricing, transaction, snapshots, status updates |
| `app/services/sync_service.py` | CORE | Publish-after-commit sync tasks |
| `app/services/product_service.py` | CORE | Catalog CRUD + facets + index bootstrap |
| `app/services/search_service.py` | CORE | ES search + error mapping (400/503) |
| `app/services/auth_service.py` | CORE | Credential verification, token creation |
| `app/services/__init__.py` | SUPPORTING | Package marker |

### `backend/app/` — data access

| File | Category | Purpose |
| --- | --- | --- |
| `app/repositories/mongo/product_repo.py` | CORE | All catalog queries/facets/CRUD/indexes |
| `app/repositories/postgres/order_repo.py` | CORE | User/order helpers, batching, `mark_search_indexed` |
| `app/repositories/elasticsearch/document.py` | CORE | Pure PG → ES document builder |
| `app/repositories/elasticsearch/mappings.py` | CORE | Index settings + `dynamic: strict` mapping |
| `app/repositories/elasticsearch/orders_repo.py` | CORE | ensure/delete index, upsert by `order_id` |
| `app/repositories/elasticsearch/search_repo.py` | CORE | `build_search_query()` + execution/aggregations |
| `app/repositories/*/__init__.py` (×4) | SUPPORTING | Package markers |
| `app/clients/mongodb.py` | CORE | Lazy Mongo client + ping/close |
| `app/clients/elasticsearch.py` | CORE | Lazy ES client + ping/close |
| `app/clients/rabbitmq.py` | SUPPORTING | Kombu connectivity probe |
| `app/clients/__init__.py` | SUPPORTING | Package marker |

### `backend/app/` — models, schemas, tasks

| File | Category | Purpose |
| --- | --- | --- |
| `app/models/postgres.py` | CORE | `User`/`Order`/`OrderItem` + CHECKs/indexes/`ORDER_STATUSES` |
| `app/models/__init__.py` | SUPPORTING | Package marker |
| `app/schemas/orders.py` | CORE | Order request/response + `SyncInfo` |
| `app/schemas/products.py` | CORE | Product schemas + `VALID_CATEGORIES` + sort literal |
| `app/schemas/search.py` | CORE | `SearchRequest` + response/aggregation contracts |
| `app/schemas/auth.py` | CORE | Login/user/logout shapes |
| `app/schemas/common.py` | CORE | Error envelope + pagination + health shapes |
| `app/schemas/__init__.py` | SUPPORTING | Package marker |
| `app/tasks/celery_app.py` | CORE | Celery config (broker, JSON, acks_late, limits, eager) |
| `app/tasks/elasticsearch_tasks.py` | CORE | The sync task + sync core + `TASK_NAME` |
| `app/tasks/__init__.py` | SUPPORTING | Package marker |

## 45.3 Frontend — `frontend/`

| File | Category | Purpose |
| --- | --- | --- |
| `frontend/index.html` | CORE | SPA shell (title/meta, `#app`, module script) |
| `frontend/package.json` | CONFIGURATION | scripts (`dev`, `build`, `test`) + deps |
| `frontend/package-lock.json` | GENERATED | Lockfile — do not hand-edit |
| `frontend/vite.config.js` | CONFIGURATION | Vue plugin, dev proxies, Vitest config |
| `frontend/nginx.conf` | CONFIGURATION | Prod routing (`/api`, `/uploads`, SPA fallback) |
| `frontend/Dockerfile` | CONFIGURATION | 4 stages: `base` → `dev` → `build` → `prod` |
| `frontend/.dockerignore` | CONFIGURATION | Image build exclusions |
| `frontend/public/*` | ASSET | Bundled product artwork (`/products/*.svg`) — untracked additions |
| `frontend/dist/` (build output) | GENERATED | Produced by `npm run build` |

### `frontend/src/` — app shell

| File | Category | Purpose |
| --- | --- | --- |
| `src/main.js` | CORE | createApp → Pinia → router → mount |
| `src/App.vue` | CORE | `<router-view>` + `ToastHost` + `authStore.init()` |
| `src/router/index.js` | CORE | Routes, guards, `scrollBehavior`, titles |
| `src/stores/auth.js` | CORE | Token/user/role, login/logout/fetchMe/init |
| `src/stores/cart.js` | CORE | Cart state, clamping, snapshot prices |
| `src/stores/toast.js` | SUPPORTING | Toast queue (max 5) |
| `src/styles/tokens.css` | CORE | Design tokens (accent `#FFAC1C`, spacing 4–64, 1320px container) |
| `src/styles/utilities.css` | CORE | `.container`, visibility helpers, `.table-scroll`, `.sr-only` |

### `frontend/src/` — API & utils

| File | Category | Purpose |
| --- | --- | --- |
| `src/api/client.js` | CORE | Axios instance, interceptors, `ApiError`, base URL |
| `src/api/products.js` | CORE | Catalog + image endpoints |
| `src/api/orders.js` | CORE | create/get/status order |
| `src/api/search.js` | CORE | `searchOrders` |
| `src/api/users.js` | SUPPORTING | `listUsers` |
| `src/utils/currency.js` | CORE | ₹ formatting (`formatCurrency`, `formatNumber`, `parseAmount`) |
| `src/utils/image.js` | CORE | `resolveImageUrl` (untracked new file) |
| `src/utils/status.js` | CORE | Three statuses, labels, tones, validator |
| `src/utils/dates.js` | SUPPORTING | UTC-safe date formatting |
| `src/utils/validation.js` | SUPPORTING | Client-side product validators |
| `src/utils/debounce.js` | SUPPORTING | `debounce(fn, wait=300)` |

### `frontend/src/` — layouts & views

| File | Category | Purpose |
| --- | --- | --- |
| `src/layouts/StorefrontLayout.vue` | CORE | Announce/header/search/cart/footer + drawer |
| `src/layouts/AdminLayout.vue` | CORE | Admin shell + nav |
| `src/views/StorefrontView.vue` | CORE | Hero/categories/tags/filters/grid/pagination |
| `src/views/CheckoutView.vue` | CORE | Live prices, `placeOrder`, success panel |
| `src/views/LoginView.vue` | CORE | Login screen |
| `src/views/AdminSearchView.vue` | CORE | ES search dashboard |
| `src/views/OrderDetailsView.vue` | CORE | Canonical order + status control |
| `src/views/CatalogAdminView.vue` | CORE | Catalog CRUD screen |

### `frontend/src/components/`

| Group | Files | Category |
| --- | --- | --- |
| `common/` (19) | `AppAlert`, `AppBadge`, `AppCard`, `AppDrawer`, `AppIcon`, `AppModal`, `AppPagination`, `BaseButton`, `BaseInput`, `BaseSelect`, `BaseTextarea`, `ConfirmDialog`, `EmptyState`, `FormField`, `KpiCard`, `LoadingSkeleton`, `ProductThumb`, `StatusBadge`, `ToastHost` | CORE (component kit) |
| `storefront/` (8) | `CartDrawer`, `CategorySection`, `HeroSection`, `ProductCard`, `ProductFilters`, `ProductGrid`, `TagMarquee`*, `TagPill`* | CORE (shop UI) |
| `admin/` (11) | `AttributesEditor`, `CatalogCardList`, `CatalogTable`, `OrderStatusControl`, `ProductFormModal`, `ResultsCardList`, `ResultsTable`, `SearchFilters`, `SearchKpis`, `SearchSyncIndicator`, `TagsInput`, `VariantsEditor` | CORE (admin UI) |
| `auth/` (1) | `LoginForm` | CORE |
| `checkout/` (3) | `CheckoutLineItems`, `OrderSuccessPanel`, `OrderSummaryCard` | CORE |

`*` = untracked new files added during the UI rebuild.

## 45.4 Tests

| File | Category | Purpose |
| --- | --- | --- |
| `tests/conftest.py` | TEST | Fixtures (`api`, `admin_api`, factories, ES helpers) + infra skip guard |
| `tests/unit/test_pricing.py` | TEST | Decimal pricing, merging, no-money-in-request |
| `tests/unit/test_schemas.py` | TEST | Status/range/pagination/product validation |
| `tests/unit/test_es_document.py` | TEST | Document shape, snapshots, determinism |
| `tests/unit/test_search_query.py` | TEST | Query/filters/aggregations builder |
| `tests/integration/test_products_api.py` | TEST | Catalog CRUD/filters/visibility/errors |
| `tests/integration/test_orders_api.py` | TEST | Pricing, rollback, snapshots, status |
| `tests/integration/test_search_api.py` | TEST | Search, filters, KPIs, isolation, parity |
| `tests/integration/test_sync_task.py` | TEST | Idempotency, retries, publish failure, reindex |
| `frontend/tests/cart.spec.js` | TEST | Cart store invariants (28 frontend tests total) |
| `frontend/tests/currency.spec.js` | TEST | ₹ formatter |
| `frontend/tests/status.spec.js` | TEST | Status vocabulary + timestamps |
| `frontend/tests/components.spec.js` | TEST | Component kit behaviour |
| `frontend/tests/smoke.spec.js` | TEST | Live-API screen renders |
| `__pycache__/`, `.pytest_cache/` | GENERATED | Caches — excluded from VCS |

---

# PART 46 — Master System Map

Everything in one place.

## 46.1 ASCII system architecture

```
                          ┌─────────────────────────────────────────┐
                          │              BROWSER                    │
                          └───────────────┬─────────────────────────┘
                    dev :5173 Vite ───────┤       prod :8080 Nginx
                    (proxy /api,/uploads) │       (proxy /api,/uploads)
                                          ▼
                    ┌───────────────────────────────────────────────┐
                    │                 FastAPI  :8000                │
                    │  auth(roles) · errors(envelope) · health      │
                    │  ┌──────────┬──────────┬──────────┬─────────┐ │
                    │  │products  │ orders   │ search   │ auth    │ │
                    │  │users     │ health   │          │         │ │
                    │  └────┬─────┴────┬─────┴────┬─────┴────┬────┘ │
                    │       │ services: product · order · search    │
                    │       │          · sync · auth                │
                    └───────┼──────────┼─────────────┼──────────────┘
             read/write     │          │ read        │ publish (AFTER COMMIT)
                            ▼          ▼             ▼
              ┌──────────────────┐  ┌─────────────┐  ┌──────────────────┐
              │    MongoDB 7     │  │ PostgreSQL 16│  │    RabbitMQ      │
              │ db `catalog`     │  │ users        │  │ queue orders_sync│
              │ collection       │  │ orders  ◀SRC │  │ (JSON, acks_late)│
              │ `products`       │  │ order_items  │  └────────┬─────────┘
              │ sku uniq, cat idx│  │ numeric $    │           │ consume
              └────────▲─────────┘  └──────┬──────┘           ▼
                       │ image_url         │ re-read   ┌──────────────────┐
                       │ (reference)       │ (worker)  │  Celery worker   │
              ┌────────┴─────────┐         │           │  concurrency=2   │
              │ uploads_data vol │         │           │  build → upsert  │
              │ /app/uploads/…   │         │           │  retry ×5 backoff│
              └────────▲─────────┘         │           └────────┬─────────┘
                       │ StaticFiles       │                    │ _id = order_id
                       │ (/uploads mount)  │                    ▼
              ┌────────┴──────────────────────────────────────────────────┐
              │                  Elasticsearch 8.15  index `orders`       │
              │   PROJECTION · dynamic strict · items nested · money double│
              │   read ONLY by POST /api/search/orders (admin)             │
              └───────────────────────────▲────────────────────────────────┘
                                          │
                       admin search + KPIs (aggregations)
```

## 46.2 ER diagram (PostgreSQL ↔ cross-store references)

```
┌───────────────────────┐          ┌───────────────────────────────┐
│ users                 │          │ MongoDB `catalog.products`    │
│  id           PK      │          │  _id          (ObjectId)      │
│  name                 │          │  sku          UNIQUE          │
│  email        UNIQUE  │          │  title, description, price    │
│  password_hash        │          │  category, tags[], attributes │
│  role  CK: CUSTOMER/  │          │  variants[], active, image_url│
│         ADMIN         │          │  created_at, updated_at       │
│  created_at           │          └───────────────▲───────────────┘
└──────────┬────────────┘                          │
           │ 1                                     │ no FK (text id):
           │                                       │ order_items.product_id
           │ N                                     │
┌──────────▼────────────┐                          │
│ orders                │          ┌───────────────┴───────────────┐
│  id           PK      │          │ disk: /uploads/products/*     │
│  order_number UNIQUE  │          │  referenced by products.      │
│  user_id      FK ─────┘          │  image_url (relative URL)     │
│  status CK: PENDING/             └───────────────────────────────┘
│             PROCESSING/SHIPPED
│  order_date            │       ┌─────────────────────────────────┐
│  total_amount numeric  │       │ Elasticsearch `orders` (copy)   │
│  created_at/updated_at │       │  _id = orders.id                │
│  search_indexed_at     │       │  customer{…}, items[…], KPIs    │
└──────────┬─────────────┘       │  rebuilt by worker / reindex    │
           │ 1                    └──────────▲──────────────────────┘
           │ N                              │ upsert (after COMMIT)
┌──────────▼─────────────┐    publish    ┌────┴───────────┐
│ order_items            │ ────────────▶ │ RabbitMQ       │
│  id PK                 │  orders_sync  │ → Celery worker│
│  order_id FK CASCADE   │               └────────────────┘
│  product_id  (text) ───┼──▶ Mongo _id
│  title       SNAPSHOT  │
│  quantity    CK > 0    │
│  unit_price  SNAPSHOT  │
│  line_total            │
└────────────────────────┘
```

## 46.3 Master data-flow map (all 14 flows in one view)

```
READ PATHS (frontend → API → store)
  storefront list/search/filter  → GET /api/products      → MongoDB
  facets / categories / tags     → GET /api/products/facets → MongoDB
  single product (checkout)      → GET /api/products/{id}  → MongoDB
  place order                    → POST /api/orders        → MongoDB (validate) + PostgreSQL (write)
  order details / status page    → GET  /api/orders/{id}   → PostgreSQL
  status change                  → PATCH …/status          → PostgreSQL (+ publish)
  admin search + KPIs            → POST /api/search/orders → Elasticsearch
  catalog admin list/CRUD        → GET/PATCH/DELETE /api/products → MongoDB
  image upload/replace/remove    → POST/DELETE /api/products/{id}/image → disk + MongoDB
  login/me                       → POST /api/auth/login, GET /api/auth/me → PostgreSQL
  health                         → GET /api/health         → all four pings

ASYNC PATH (the only one)
  PostgreSQL COMMIT ─▶ sync_service.publish_order_sync ─▶ RabbitMQ `orders_sync`
       ─▶ celery worker: read PG → build_order_document → ensure_index
            ─▶ ES upsert _id=order_id ─▶ orders.search_indexed_at = now()

RECOVERY PATH
  python -m scripts.reindex_orders [--recreate]  ─▶ ES rebuilt from PostgreSQL
  docker compose run --rm seed                   ─▶ whole demo rebuilt + verified
```

## 46.4 One-line responsibility map

| Component | One line |
| --- | --- |
| Vue frontend | Renders five screens; talks only to the API; never to a database |
| FastAPI | Validates, authorizes, prices, transacts, and publishes — nothing else |
| MongoDB | Owns live product documents and image references |
| PostgreSQL | Owns orders, items, users, money — the single source of truth |
| RabbitMQ | Carries tiny task ids from API to worker, durably |
| Celery worker | Rebuilds order documents from PostgreSQL and upserts them |
| Elasticsearch | Fast, faceted read copy of orders — always rebuildable |
| Nginx | Serves the SPA and proxies `/api`, `/uploads` in production |
| Docker Compose | Starts, wires and health-checks all of the above |

---

# PART 47 — 30-Minute Teaching Path

The shortest route from "never seen this repo" to "can explain the whole system". Timings are
honest — this is a guided tour, not a cover-to-cover read.

| Time | Do this | You will learn | Reads |
| --- | --- | --- | --- |
| 0–3 min | Read this guide's cover + table of contents | The shape of the system | Cover + PART 1 |
| 3–6 min | Read `README.md` §1–3 side by side with the code | The polyglot design and the honesty table | PART 1–2, Byte 5 |
| 6–9 min | Open `frontend/src/main.js` → `App.vue` → `router/index.js` | How the SPA boots and which routes exist | Bytes 30–31 |
| 9–12 min | Open `frontend/src/stores/cart.js` + `frontend/src/views/CheckoutView.vue` | Client cart, server re-pricing, `placeOrder` | Bytes 3, 10, 74 |
| 12–16 min | Open `backend/app/services/order_service.py` end to end | Pricing → transaction → snapshots → commit | Bytes 74–78 |
| 16–19 min | Open `backend/app/services/sync_service.py` + `backend/app/tasks/elasticsearch_tasks.py` | Publish after commit, worker rebuild, upsert, retries | Bytes 79–85 |
| 19–22 min | Open `backend/app/repositories/elasticsearch/document.py` + `mappings.py` | What a projection is and why `dynamic: strict` | Bytes 84, 89, 147 |
| 22–25 min | Open `frontend/src/views/AdminSearchView.vue` | Filters → payload → ES → KPIs/rows | Bytes 95, 107–110 |
| 25–28 min | Open `backend/app/api/products.py` (image endpoints) | Upload validation, containment, `/uploads` serving | Bytes 99–104 |
| 28–30 min | Run the live demo in your head using [PART 40.5](#405-order-is-in-postgresql-but-not-in-elasticsearch) | How to break it and how to fix it | PART 40 |

**Before you leave the 30 minutes:** run the demo once for real —
`docker compose up -d --build`, `docker compose run --rm seed`, open `http://localhost:5173`,
add to cart, log in as admin, place an order, then search for it under `/admin/search`.

**After 30 minutes you should be able to answer, out loud:**

1. Which store owns orders? Which owns products? Which is disposable?
2. Where in the code is the order total computed — and where is it *not* computed?
3. What is written in the same transaction, and what happens after the transaction?
4. Why can an order be missing from search while still being correct?
5. How do you rebuild the search index from scratch?

If you can't, jump to the matching bytes: [1](#byte-2-the-problem-being-solved), 7, 75, 86, 120.

---

# PART 48 — 20 Must-Remember Facts

Test yourself with the top half of each line; the answer follows.

**1. Source of truth for orders is PostgreSQL.**
MongoDB holds catalog documents; Elasticsearch holds a rebuildable read model. The API never
reads orders from either of them.

**2. Elasticsearch can be dropped and recreated at any time.**
`python -m scripts.reindex_orders` (optionally `--recreate`) rebuilds it from PostgreSQL.

**3. Order totals are computed exclusively on the server, in `order_service.py`.**
The API accepts `{user_id, items}` only — no money fields ever enter `OrderCreate`.

**4. Money is `Decimal`, quantized to cents — never floats.**
`to_money()` + `calculate_total()` are the only arithmetic that matters.

**5. Snapshots live in PostgreSQL.**
`order_items.title` and `order_items.unit_price` freeze at purchase; catalog edits never alter
historical orders (and vice versa).

**6. The transaction writes header + all items atomically, then publishes.**
`session.begin()` → flush → INSERT → COMMIT → *then* `publish_order_sync()`. Publish failure
never rolls back a committed order.

**7. `sync: {enqueued, task_id, queue, error}` is embedded in every order create/status response.**
It reports messaging status honestly without changing HTTP status codes.

**8. The projection is eventually consistent by design.**
Missing-from-search is a lag/worker problem — fix it by reindexing, never by writing to ES from
the API.

**9. The task is idempotent and keyed by order id.**
`_id = order_id`, JSON bodies, safe to re-run; publish is deliberately `persist=False` (retries
are handled by Celery, not the broker).

**10. The worker re-reads PostgreSQL — it never touches MongoDB.**
A deleted/deactivated product cannot corrupt an indexed document.

**11. Exactly three statuses exist:** `PENDING`, `PROCESSING`, `SHIPPED` — enforced by the
`Literal` schema, the SQLAlchemy `CHECK`, and the ES mapping.

**12. Order number format: `ORD-%06d`, derived from the primary key after insert.**
Never random, never sequential in application code.

**13. Two roles only: `CUSTOMER`, `ADMIN`.**
Admin is decided by the JWT *plus* a fresh PostgreSQL `role` lookup; ownership checks are
user-id comparisons in the API.

**14. Passwords are bcrypt (`passlib`), tokens are JWT (HS256, 60 min) with
`{"sub": user_id}` — the role is deliberately not in the token.**

**15. The frontend's cart is memory-only and clamped to 1–99.**
Refresh loses it; the server re-prices regardless of what the client sent.

**16. Product images are stored on disk under `/uploads/`, referenced by a relative
`image_url` in MongoDB, served by FastAPI (dev) or Nginx (prod).**

**17. Upload safety:** type allow-list (jpeg/png/webp/gif), extension validation, 5 MB cap,
generated filename (`uuid4().hex + ext`), and a containment check before any deletion.

**18. One global search UX:** `/` or ⌘K focuses the storefront search → `?q=` → MongoDB filter.
Admin search is a separate, Elasticsearch-only screen behind `requiresAdmin`.

**19. Design tokens are authoritative:** accent `#FFAC1C`, spacing scale 4/8/12/16/20/24/32/40/
48/64, one 1320px container (padding 32/24/16).

**20. The recorded verification state:** pytest **100 passed**, Vitest **28/28**,
`npm run build` ✅ — and the README's "101 tests" claim does not match that number.

---

# PART 49 — Glossary

Terms as this repository actually uses them. Where the project has a specific (possibly
non-standard) meaning, that is called out.

| Term | Definition in this system |
| --- | --- |
| **Aggregate** | Elasticsearch `terms`/`stats` summarization returned as `SearchAggregations` (`revenue`, `status_counts`, `price_stats`) — all conditioned on the same filters as the rows |
| **Async / background sync** | Specifically the RabbitMQ → Celery pipeline that updates Elasticsearch after a PostgreSQL commit. Not a cron, not polling |
| **Backpressure** | Here: `visibility_timeout=3600`, prefetch `1`, concurrency `2` — an unacked task returns to the queue after an hour if the worker dies |
| **Batching** | `iter_orders(batch_size=250)` streams PostgreSQL rows for reindexing without loading everything into memory |
| **Catalog** | The MongoDB `products` collection (and the admin screen that manages it) |
| **Dual write** | The pattern used here: PostgreSQL is written transactionally; the search projection is written *later* by a worker from re-read PostgreSQL. Deliberately not "write both at once" |
| **Eager mode** | `task_always_eager=True` (tests) — the task runs in-process, response reports `queue:"in-process"` |
| **Envelope** | The `{"error": {code, message, details}}` JSON shape returned by `AppError` handlers |
| **Eventual consistency** | The normal window in which an order exists in PostgreSQL but not yet in Elasticsearch |
| **Facet** | `GET /api/products/facets` — `categories`, `tags`, `price` (min/max) for filter UIs |
| **Idempotency** | Running `sync_order_to_elasticsearch` twice produces the same document; upsert keyed by `_id = order_id` |
| **Immutable snapshot** | `order_items.title`/`unit_price` captured at order time; never updated afterwards |
| **Inference** | A label used in this guide for conclusions drawn from code behaviour rather than stated in docs (vs. **FACT** = verbatim in code/docs, **GENERAL ENGINEERING KNOWLEDGE** = standard practice) |
| **JSON serializer** | Celery's `task_serializer="json"` — only plain data crosses the broker |
| **KPIs** | Dashboard numbers from `aggregations`, not a separate query |
| **Liveness vs. readiness** | `GET /api/health` probes dependencies with latency; container healthchecks use it to gate `depends_on` |
| **`multi_match` / `bool_prefix`** | Query types referenced for full-text search. **Only `multi_match` appears in the implementation**; `bool_prefix` was not found (doc-vs-code contradiction) |
| **Opaque payload** | A queued message carrying only `order_id` + `reason` — the worker fetches the rest from PostgreSQL |
| **Outbox / CDC / Debezium** | Explicitly **not used**. No outbox table, no change-data-capture, no polling for search sync — only direct publish after commit |
| **Polling** | Not used for synchronization anywhere in this codebase |
| **Polyglot persistence** | Different stores for different data: MongoDB (catalog), PostgreSQL (orders/users), Elasticsearch (search), disk (images) |
| **Projection** | The Elasticsearch `orders` index: a derived, rebuildable read model of PostgreSQL |
| **Push-based sync** | What this system does: the API pushes a task after commit. Contrast with pull/poll |
| **`persist` (Celery)** | Set to `False` on `publish` so the broker does not persist results; ordering is ensured by Celery's retry/backoff instead |
| **RabbitMQ dead-lettering** | Not configured — retries are handled by Celery `autoretry_for` + exponential backoff |
| **Rollback** | `session.rollback()` guarantees no partial order: no header without items, no items without a header |
| **`scrollBehavior: false`** | Router behaviour that avoids re-scrolling on query-only navigation (filter/search changes) |
| **Snapshot price** | The `unit_price` stored on an order item; can legitimately differ from the live Mongo price |
| **Source of truth** | PostgreSQL for orders/users; MongoDB for products. Elasticsearch is never a source of truth |
| **Split tokens** | The JWT approach: signature proves authenticity; the role comes from a live PostgreSQL lookup |
| **Structured content type** | Server response for uploads, paired with filename-based extension checks (defense in depth) |
| **`dynamic: strict`** | Elasticsearch mapping policy: unexpected fields are rejected, keeping the schema explicit |
| **UTC rendering** | All timestamps displayed in UTC with a `UTC` suffix (frontend `dates.js`) |
| **Volume** | Named Docker volume (`uploads_data`) mounted by both backend and worker so images are shared |
| **Visibility timeout** | RabbitMQ's 1-hour redelivery window for unacked messages (see **Backpressure**) |

---

# PART 50 — Self-Test Checklist

Answer first, then check the answer printed **after** each block. Every answer is already
covered somewhere in this guide — the reference in brackets tells you where to review.

## Block 1 — Architecture (Q1–Q6)

1. Which database is the source of truth for orders, and which two stores must never be used as
   one?
2. Name the four backend *service* modules and one sentence each.
3. What exactly does the API publish to RabbitMQ, and when?
4. Is there an outbox pattern, a CDC pipeline, or polling anywhere in this codebase?
5. If Elasticsearch loses its index, what is the correct recovery command?
6. Why does the Celery worker's `depends_on` list MongoDB as *not* required?

**Answers:**
1. **PostgreSQL** (source of truth); MongoDB and Elasticsearch are never sources of truth for
   orders [Byte 7, Byte 111]. 2. `order_service` (pricing/transactions/snapshots),
   `product_service` (catalog CRUD/facets), `search_service` (ES queries/aggregations + error
   mapping), `sync_service` (publish-after-commit), `auth_service` (credentials/tokens)
   [Byte 61]. 3. A task id payload `{order_id, reason}` via `send_task`, **after** `session.commit()`
   [Byte 79]. 4. **No** — none of them; only direct publish-after-commit [Byte 6, Byte 19].
5. `python -m scripts.reindex_orders --recreate` (or `docker compose run --rm reindex`)
   [Byte 120]. 6. Because the worker reads only PostgreSQL and Elasticsearch — never MongoDB
   [Byte 157, Byte 146].

## Block 2 — Orders & money (Q7–Q12)

7. List every field `OrderCreate` accepts.
8. Where is `total_amount` computed, and what numeric type is used?
9. What happens to `order_items.title` after the product is renamed in the catalog?
10. What HTTP status and code does a failed commit produce, and what does the message promise?
11. When is `order_number` generated?
12. Are `SHIPPED` → `PENDING` transitions allowed?

**Answers:**
7. Only `user_id` and `items[].{product_id, quantity}` [Byte 2, Byte 62]. 8. In
`order_service.calculate_total()` as `Decimal`, quantized to cents, inside the transaction
[Bytes 74–75, Byte 143]. 9. It is **unchanged** — snapshots are written at order time and never
updated [Byte 77, Byte 132]. 10. `500` with code `order_persistence_failed` and message
"…No data was written — please try again." [Byte 131]. 11. After insert + flush, from the
primary key: `f"ORD-{order.id:06d}"` [Byte 76]. 12. **No** — the `Literal`/`CHECK`/mapping allow
only PENDING/PROCESSING/SHIPPED; the SQL transition guard rejects the reverse order
[Bytes 112, 14 (schema), Byte 63].

## Block 3 — Sync & search (Q13–Q18)

13. Name the full sync chain in order.
14. What are the Celery task's retry settings?
15. What does a response look like when RabbitMQ is unreachable at publish time?
16. How does an order's document get its `_id`?
17. Does the task re-fetch product data from MongoDB?
18. How does `search_indexed_at` get set?

**Answers:**
13. PostgreSQL commit → `sync_service.publish_order_sync` → RabbitMQ `orders_sync` → Celery
worker → read PG → `build_order_document` → ensure index → upsert → record timestamp
[Bytes 79–83, Byte 146]. 14. `autoretry_for=(Exception,)`, `max_retries=5`, backoff 10→20→40→80
→120 s, plus `task_acks_late`, `visibility_timeout=3600` [Byte 85, Byte 145]. 15. HTTP 201/200
with `sync: {enqueued: false, error: …}` — the order stays committed [Byte 130]. 16. Equal to
the PostgreSQL `orders.id` (`_id = order_id`) [Byte 84]. 17. **No** — the worker never touches
MongoDB; it uses snapshots from PostgreSQL [Byte 146, Byte 147]. 18. Best-effort
`orders.search_indexed_at = now()` in `_record_indexed_at()` after a successful upsert
[Byte 83].

## Block 4 — Frontend (Q19–Q24)

19. What does ⌘K / Ctrl+K do on the storefront?
20. Which product fields render in a card, in order?
21. Is the cart persisted to `localStorage`?
22. What is the base-URL resolution rule in `api/client.js`?
23. How does a failed product image behave?
24. What is the container width and accent colour?

**Answers:**
24→20. Image → category → title → description → price → **ADD TO CART** (card order specified by
the UI requirements) [Byte 49, PART 19]. 19. Focuses the single global search input (only when
not already typing in a field) [Byte 151]. 20. See #24. 21. **No** — memory only; lost on
refresh (documented limitation) [Byte 152, Byte 136]. 22. Configured URL → `''` (relative, via
proxy) → default `http://localhost:8000` [Byte 153]. 23. `@error` flips the thumb to a
deterministic placeholder — never a broken image icon [Byte 155]. 24. **1320px** container and
**`#FFAC1C`** accent [Byte 39, PART 19].

## Block 5 — Auth & admin (Q25–Q30)

25. How many roles exist in code versus what the README claims?
26. Is the role stored in the JWT?
27. How does the API verify admin access?
28. Who may read an order?
29. Which store does `/admin/search` read, and which does `/admin/orders/:id` read?
30. How do you demote/promote a user?

**Answers:**
25. **Two** (`CUSTOMER`, `ADMIN`) with a DB `CHECK`; README describes three (CLAIMED-ADMINS)
[PART 1, Byte 16]. 26. **No** — the JWT carries `sub` + timestamps only; role comes from a live
PostgreSQL lookup [Byte 67, Byte 70]. 27. `require_admin` → `get_current_user` →
`role == "ADMIN"` → else `403` [Byte 57]. 28. The owning user, or any admin
(`user_id == current_user.id or role == ADMIN`) [Byte 71]. 29. `/admin/search` reads
**Elasticsearch**; `/admin/orders/:id` reads **PostgreSQL** [Byte 107]. 30. Update
`users.role` in PostgreSQL — tokens do not carry the role, so no reissue is required for the
role to take effect on the next request [Byte 134].

## Block 6 — Images (Q31–Q34)

31. What are the four upload validation gates?
32. What is stored in MongoDB for an image?
33. What prevents a path-traversal delete?
34. What happens to old files when `image_url` is replaced?

**Answers:**
31. (a) `Content-Type` allow-list, (b) extension allow-list, (c) 5 MB size cap,
(d) generated filename `uuid4().hex + ext` [Byte 100, Byte 149]. 32. Only a **relative URL
reference** (`/uploads/products/<name>`) — never the bytes [Byte 96]. 33. `_stored_image_path`
resolves and requires `relative_to(UPLOAD_ROOT)` to succeed; outside → `None` (never delete)
[Byte 104, Byte 149]. 34. Deleted best-effort — and if the delete fails, the Mongo update is
**not** applied (cleanup-then-update ordering) [Byte 104].

## Block 7 — Operations (Q35–Q40)

35. What does `GET /api/health` check, and what status codes can it return?
36. How do you seed demo data?
37. Which compose profiles exist?
38. Name three documented limitations of this system.
39. Which ports are exposed for each service?
40. What happens if you stop the Celery worker and place orders?

**Answers:**
35. PostgreSQL, MongoDB, Elasticsearch, RabbitMQ with latency; `200` all-up, `503` degraded
[Byte 118]. 36. `docker compose run --rm seed` — or
`python -m scripts.seed` — verify assertions run automatically [Byte 119]. 37. `prod`
(frontend-prod) and `tools` (seed/reindex) [Byte 114]. 38. No cart persistence, no image garbage
collection, local volume only (plus: `JWT_SECRET_KEY`/`UPLOADS_DIR` missing from `.env.example`)
[PART 39, PART 33]. 39. API 8000, Vite 5173, Nginx 8080, PostgreSQL 5432, MongoDB 27017,
Elasticsearch 9200, RabbitMQ 5672/15672 [PART 32, Byte 114]. 40. Orders still commit; responses
show `enqueued:true` (queued) but no worker consumes them — search lags; restore the worker or
run the reindex script [Byte 129, Byte 130].

## Block 8 — Code reading (Q41–Q44)

41. In `main.py`, why is `create_tables()` mandatory while `ensure_catalog_indexes()` is wrapped
in `try/except`?
42. Why is `expire_on_commit=False` set on the session factory?
43. What does `scrollBehavior: () => false` protect against?
44. Why does `results[]` in the admin view never contain a `description` field?

**Answers:**
41. PostgreSQL is the source of truth and must exist before serving; Mongo index creation is
best-effort so a Mongo blip doesn't block boot [Byte 139]. 42. So attributes (including loaded
`items`) remain accessible after `commit()` — responses serialize without a re-query
[Byte 142]. 43. Re-scrolling to the top whenever only the query string changes (filters/pagination
would otherwise jump the page) [Byte 11]. 44. Because `OrderSummary` — the search projection
contract — simply doesn't include it; `dynamic: strict` means any extra field would be rejected
[Bytes 62, 89].

## Block 9 — True / False (Q45–Q50)

45. The API writes to Elasticsearch during checkout. __
46. `order_items.unit_price` can change if the product price changes. __
47. Deactivating a product removes it from historical orders. __
48. A committed order can be lost if RabbitMQ is down. __
49. The JWT contains the user's role. __
50. Admin search results come from PostgreSQL. __

**Answers:**
45. **False** — the worker does it after commit [Byte 79]. 46. **False** — snapshot
[Byte 77]. 47. **False** — snapshots keep it readable; only new orders are blocked (422
`inactive_product`) [Bytes 127, 133]. 48. **False** — the write is committed; only indexing
lags [Byte 130]. 49. **False** — `sub` only; role is looked up live [Byte 67]. 50. **False** —
Elasticsearch only [Byte 107].

## Block 10 — Match the error (Q51–Q55)

Match each situation to its response:

| | Situation | | | Response |
| --- | --- | --- | --- | --- |
| 51 | Wrong password | | | A. `409 sku_conflict` |
| 52 | Non-admin hits `/api/search/orders` | | | B. `422 inactive_product` |
| 53 | Ordering a deactivated product | | | C. `404 invalid_credentials` |
| 54 | Reusing another product's SKU | | | D. `403` (FastAPI `detail` shape) |
| 55 | Order not found for you | | | E. `404 order_not_found` |

**Answers:** 51→C, 52→D, 53→B, 54→A, 55→E [Bytes 71, 127, 128, 130, 141, PART 30].

## Block 11 — Bonus, deep (Q56–Q60)

56. Why does `publish(..., persist=False)` not cause lost messages?
57. What makes the ES document builder a "pure function"?
58. Why is `pipeline_id = process_id` in the task result?
59. What does `toApiError()` do with a `401` versus a `422`?
60. Why do both `backend/` and `celery-worker` mount `uploads_data`?

**Answers:**
56. Message durability is the broker's job (`durable` queue); Celery's retry/backoff handles
delivery, and results aren't stored — `backend=None` [Bytes 19, 20]. 57. It takes an already-
loaded `Order` and returns a dict — no I/O, no clock, no randomness → identical output → safe
idempotent upserts [Byte 147]. 58. To correlate a result with the worker process that executed
it (observability only) [Byte 82]. 59. `401` arrives as FastAPI's `{"detail": …}` (no
`HTTPException` handler registered) so `toApiError` synthesizes `auth.unauthorized` from the
status; `422` arrives inside the standard `{"error": …}` envelope and is parsed normally
[PART 30, Byte 141]. 60. The worker re-reads PostgreSQL but the *uploaded files* must be
reachable by whichever container serves them; sharing one volume keeps images consistent
[Bytes 114, 117, 157].

## Scoring

| Score | Interpretation | Next step |
| --- | --- | --- |
| 55–60 | You own this system | Skim PART 44.3 and start contributing |
| 45–54 | Solid — weak spots in edges | Re-read Sections H–J + PART 40 |
| 30–44 | Halfway there | Follow [PART 47](#part-47--30-minute-teaching-path) again with the code open |
| < 30 | Start from bytes 1–20 | Then Sections C–F |

---

**END OF DOCUMENT**

*All facts in this guide are grounded in the repository source. Where the repository and the
documentation disagree, both are quoted and the contradiction is marked. Inferences are
labelled **INFERENCE**; practices that are general (not project-specific) are labelled
**GENERAL ENGINEERING KNOWLEDGE**.*
