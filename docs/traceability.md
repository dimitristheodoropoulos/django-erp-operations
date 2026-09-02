# ERP Requirements Traceability Matrix

**Status:** Living Engineering Artifact
**Requirements Baseline:** `14db353`
**Database Design Baseline:** `c5a9e31`
**Model Specification Baseline:** `13d0a8d`
**Last Updated:** 2026-09-02

---

## 1. Purpose

This document is the authoritative traceability matrix for the ERP
requirements baseline defined in `docs/requirements.md`.

The matrix is intentionally designed as a living engineering artifact.

A requirement progresses through the following verification lifecycle:

```text
PENDING
   ↓
DESIGNED
   ↓
IMPLEMENTED
   ↓
TESTED
   ↓
VERIFIED
```

A status must only advance when corresponding engineering evidence exists.

### Status definitions

| Status        | Meaning                                                                                                                      |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `PENDING`     | No sufficient design or implementation evidence has been established yet.                                                    |
| `DESIGNED`    | The requirement is represented by an approved architecture, database, model, API, or other design artifact.                  |
| `IMPLEMENTED` | The required production implementation exists in source code.                                                                |
| `TESTED`      | Automated or otherwise explicit tests exercise the requirement and pass.                                                     |
| `VERIFIED`    | The implementation and test evidence have been reviewed against the requirement and the verification result is reproducible. |

### Important verification rule

The existence of a model, database constraint, migration, endpoint skeleton,
or documentation entry does **not** by itself justify `TESTED` or `VERIFIED`.

`VERIFIED` requires implementation evidence, test evidence, and a reproducible
verification result.

---

## 2. Traceability Chain

Each requirement should ultimately be traceable through:

```text
Requirement
    ↓
Architecture
    ↓
Database Design
    ↓
Model Specification
    ↓
Migration
    ↓
Implementation
    ↓
Automated Test
    ↓
Verification Evidence
    ↓
Status
```

Not every requirement requires every layer.

For example, a CI requirement may map primarily to development/CI
documentation, workflow configuration, and execution evidence rather than
to a database model.

---

## 3. Requirements Matrix

| ID          | Requirement                  | Architecture / Design                       | Database      | Model       | Migration                      | Implementation                       | Test | Evidence                       | Status      |
| ----------- | ---------------------------- | ------------------------------------------- | ------------- | ----------- | ------------------------------ | ------------------------------------ | ---- | ------------------------------ | ----------- |
| ERP-REQ-001 | Customer Creation            | `architecture.md` / Customers               | `database.md` | `models.md` | `customers/0001_initial.py`    | `apps/api/customer_views.py::CustomerListCreateView; apps/api/serializers.py::CustomerSerializer` | `tests/api/test_customers.py::test_customer_create_returns_201_and_server_managed_fields; test_customer_create_rejects_empty_name; test_customer_create_does_not_allow_client_to_set_active` | `python -m pytest -q tests/api/test_customers.py` → 7 passed | TESTED      |
| ERP-REQ-002 | Customer Retrieval           | `architecture.md` / Customers               | `database.md` | `models.md` | `customers/0001_initial.py`    | `apps/api/customer_views.py::CustomerListCreateView; apps/api/customer_views.py::CustomerDetailView` | `tests/api/test_customers.py::test_customer_list_returns_customers; test_customer_retrieve_returns_customer; test_customer_retrieve_unknown_customer_returns_404` | `python -m pytest -q tests/api/test_customers.py` → 7 passed | TESTED      |
| ERP-REQ-003 | Customer Status              | `architecture.md` / Customers               | `database.md` | `models.md` | `customers/0001_initial.py`    | `apps/api/serializers.py::CustomerSerializer; apps/api/customer_views.py::CustomerDetailView` | `tests/api/test_customers.py::test_customer_retrieve_returns_customer; test_customer_retrieve_exposes_inactive_state; test_customer_create_does_not_allow_client_to_set_active` | `python -m pytest -q tests/api/test_customers.py` → 7 passed | TESTED      |
| ERP-REQ-004 | Product Creation             | `architecture.md` / Products                | `database.md` | `models.md` | `products/0001_initial.py`     | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-005 | Unique SKU                   | `architecture.md` / Products                | `database.md` | `models.md` | `products/0001_initial.py`     | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-006 | Product Validation           | `architecture.md` / Products                | `database.md` | `models.md` | `products/0001_initial.py`     | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-007 | Warehouse Management         | `architecture.md` / Warehouses              | `database.md` | `models.md` | `warehouses/0001_initial.py`   | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-008 | Stock Representation         | `architecture.md` / Inventory               | `database.md` | `models.md` | `inventory/0001_initial.py`    | `StockItem`                          | —    | —                              | DESIGNED    |
| ERP-REQ-009 | Stock Quantities             | `architecture.md` / Inventory               | `database.md` | `models.md` | `inventory/0001_initial.py`    | `StockItem`                          | —    | —                              | DESIGNED    |
| ERP-REQ-010 | Stock Validation             | `architecture.md` / Inventory               | `database.md` | `models.md` | `inventory/0001_initial.py`    | `StockItem`                          | —    | —                              | DESIGNED    |
| ERP-REQ-011 | Inventory Consistency        | Inventory invariants                        | `database.md` | `models.md` | `inventory/0001_initial.py`    | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-012 | Sales Order Creation         | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`       | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-013 | Sales Order Lines            | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`       | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-014 | Positive Quantities          | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`       | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-015 | Price Snapshot               | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`       | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-016 | Draft State                  | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`       | `SalesOrder`                         | —    | —                              | DESIGNED    |
| ERP-REQ-017 | Order Confirmation           | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`       | `apps/orders/services.py::confirm_order` | `tests/orders/test_confirmation.py::test_confirm_valid_draft_order; test_confirm_non_draft_order_raises_invalid_order_state; test_confirm_inactive_customer_raises_inactive_customer; test_confirm_order_without_lines_raises_order_has_no_lines; test_confirm_inactive_product_raises_inactive_product` | `python -m pytest tests/orders/test_confirmation.py -q` → 18 passed | VERIFIED    |
| ERP-REQ-018 | Stock Reservation            | Inventory/order workflow                    | `database.md` | `models.md` | `inventory/0001_initial.py`    | `apps/orders/services.py::confirm_order` | `tests/orders/test_confirmation.py::test_confirm_reserves_single_product; test_confirm_reserves_stock_across_multiple_warehouses; test_confirm_aggregates_multiple_lines_for_same_product; test_confirm_commits_order_and_reservation_together; test_confirm_allocates_stock_by_stock_item_id; test_concurrent_orders_competing_for_same_stock` | `python -m pytest tests/orders/test_confirmation.py -q` → 18 passed | VERIFIED    |
| ERP-REQ-019 | Insufficient Stock           | Inventory/order workflow                    | `database.md` | `models.md` | `inventory/0001_initial.py`    | `apps/orders/services.py::confirm_order` | `tests/orders/test_confirmation.py::test_confirm_insufficient_stock_raises_insufficient_stock; test_insufficient_stock_leaves_order_in_draft; test_insufficient_stock_leaves_inventory_unchanged; test_confirmation_is_atomic_when_later_product_is_insufficient; test_concurrent_orders_competing_for_same_stock` | `python -m pytest tests/orders/test_confirmation.py -q` → 18 passed | VERIFIED    |
| ERP-REQ-020 | Order Cancellation           | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`       | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-021 | Shipment                     | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`       | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-022 | Completion                   | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`       | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-023 | Completed Order Immutability | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`       | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-024 | API Versioning               | `api.md`                                    | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-025 | Customer API                 | `api.md` / Customers                        | —             | `models.md` | `customers/0001_initial.py`    | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-026 | Product API                  | `api.md` / Products                         | —             | `models.md` | `products/0001_initial.py`     | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-027 | Inventory API                | `api.md` / Inventory                        | `database.md` | `models.md` | `inventory/0001_initial.py`    | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-028 | Sales Order API              | `api.md` / Orders                           | `database.md` | `models.md` | `orders/0001_initial.py`       | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-029 | API Validation               | `api.md` / API error design                 | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-030 | Payment Webhook              | Integration architecture                    | `database.md` | `models.md` | `integrations/0001_initial.py` | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-031 | Webhook Validation           | Integration architecture                    | `database.md` | `models.md` | `integrations/0001_initial.py` | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-032 | Webhook Idempotency          | Integration architecture                    | `database.md` | `models.md` | `integrations/0001_initial.py` | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-033 | Unknown Order Webhook        | Integration architecture                    | `database.md` | `models.md` | `integrations/0001_initial.py` | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-034 | Legacy Customer Import       | Integration / Migration design              | —             | —           | —                              | —                                    | —    | —                              | PENDING     |
| ERP-REQ-035 | Migration Validation         | Integration / Migration design              | —             | —           | —                              | —                                    | —    | —                              | PENDING     |
| ERP-REQ-036 | Data Transformation          | Integration / Migration design              | —             | —           | —                              | —                                    | —    | —                              | PENDING     |
| ERP-REQ-037 | Migration Report             | Integration / Migration design              | —             | —           | —                              | —                                    | —    | —                              | PENDING     |
| ERP-REQ-038 | Authentication               | Accounts architecture                       | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-039 | User Roles                   | Accounts architecture                       | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-040 | Permission Enforcement       | Accounts architecture                       | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-041 | Business Errors              | Application/service architecture            | —             | `models.md` | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-042 | Consistent API Errors        | `api.md` / API error design                 | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-043 | Unexpected Errors            | Application/API architecture                | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-044 | Application Logging          | Application architecture                    | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-045 | Sensitive Information        | Application/configuration architecture      | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-046 | Automated Testing            | `development.md`                            | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-047 | Business Logic Testing       | `development.md` / test strategy            | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-048 | Inventory Testing            | `development.md` / test strategy            | —             | `models.md` | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-049 | Order Lifecycle Testing      | `development.md` / lifecycle design         | —             | `models.md` | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-050 | API Testing                  | `api.md` / `development.md`                 | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-051 | Webhook Testing              | Integration architecture / `development.md` | `database.md` | `models.md` | `integrations/0001_initial.py` | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-052 | Migration Testing            | `development.md` / migration design         | —             | —           | —                              | —                                    | —    | —                              | PENDING     |
| ERP-REQ-053 | PostgreSQL                   | Infrastructure architecture                 | `database.md` | —           | —                              | `config/settings.py` / Docker        | —    | PostgreSQL 16 runtime verified | IMPLEMENTED |
| ERP-REQ-054 | Referential Integrity        | Database architecture                       | `database.md` | `models.md` | domain migrations              | —                                    | —    | PostgreSQL schema inspection   | DESIGNED    |
| ERP-REQ-055 | Database Constraints         | Database architecture                       | `database.md` | `models.md` | domain migrations              | —                                    | —    | PostgreSQL schema inspection   | DESIGNED    |
| ERP-REQ-056 | Environment Configuration    | Configuration architecture                  | `database.md` | —           | —                              | `config/settings.py`                 | —    | —                              | DESIGNED    |
| ERP-REQ-057 | Secret Management            | Configuration architecture                  | `database.md` | —           | —                              | `.env.example` / settings            | —    | —                              | DESIGNED    |
| ERP-REQ-058 | Environment Separation       | Configuration architecture                  | —             | —           | —                              | settings/environment configuration   | —    | —                              | DESIGNED    |
| ERP-REQ-059 | Containerized Development    | Infrastructure architecture                 | `database.md` | —           | —                              | `docker-compose.yml`                 | —    | `docker compose config` PASS   | IMPLEMENTED |
| ERP-REQ-060 | Database Container           | Infrastructure architecture                 | `database.md` | —           | —                              | `docker-compose.yml`                 | —    | PostgreSQL container healthy   | IMPLEMENTED |
| ERP-REQ-061 | Reproducible Environment     | Infrastructure/development architecture     | —             | —           | —                              | `pyproject.toml`, Docker             | —    | —                              | DESIGNED    |
| ERP-REQ-062 | CI Pipeline                  | Development/CI architecture                 | `database.md` | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-063 | CI Failure Handling          | Development/CI architecture                 | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-064 | Architecture Documentation   | `architecture.md`                           | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-065 | Database Documentation       | `database.md`                               | `database.md` | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-066 | API Documentation            | `api.md`                                    | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-067 | Development Documentation    | `development.md`                            | —             | —           | —                              | —                                    | —    | —                              | DESIGNED    |
| ERP-REQ-068 | Version Control              | Development documentation                   | —             | —           | —                              | Git                                  | —    | Git history                    | IMPLEMENTED |
| ERP-REQ-069 | Meaningful Commits           | Development documentation                   | —             | —           | —                              | Git                                  | —    | Git history                    | IMPLEMENTED |
| ERP-REQ-070 | Reproducibility              | Development/infrastructure architecture     | —             | —           | —                              | `pyproject.toml`, Docker, migrations | —    | —                              | DESIGNED    |

---

## 4. Current Verification Boundary

The current project state is a **design and infrastructure foundation**.

The following should NOT currently be represented as `VERIFIED`:

* Customer business workflows
* Product business workflows
* Warehouse business workflows
* Stock mutation workflows
* Atomic stock reservation
* Sales-order confirmation
* Insufficient-stock behavior
* Order cancellation workflow
* Shipment workflow
* Completion workflow
* Completed-order immutability
* Customer/Product/Inventory/Order APIs
* Payment webhook processing
* Webhook idempotency
* Legacy customer migration
* Authentication and authorization enforcement
* Business-error handling
* Application logging behavior
* Automated business test coverage
* API test coverage
* Webhook test coverage
* Migration test coverage
* CI execution

These require implementation and reproducible test evidence.

---

## 5. Existing Infrastructure Evidence

The following evidence already exists independently of the future service/API
implementation:

### Django configuration

```text
python manage.py check
→ PASS

python manage.py makemigrations --check --dry-run
→ No changes detected.
```

### PostgreSQL

```text
PostgreSQL 16
Database: erp
User: erp
```

The Django project successfully migrated against PostgreSQL and the resulting
schema was inspected.

### Docker Compose

```text
docker compose config
→ PASS
```

The PostgreSQL service was started successfully and its healthcheck reported
healthy.

### Python environment

```text
Python 3.12.3
Django 5.2.x
pytest 8.4.2
pytest-django
psycopg
```

The project is configured through `pyproject.toml` and supports installation
of the test dependencies through the project test extra.

---

## 6. Domain Model Evidence

The current model specification and implementation establish the following
domain structures:

```text
Customer
Product
Warehouse
StockItem
SalesOrder
SalesOrderLine
ExternalEvent
```

The current implementation deliberately does not place critical lifecycle
or reservation workflows directly inside Django models.

Critical business workflows are expected to be implemented through explicit
application/domain services.

This is particularly important for:

```text
SalesOrder confirmation
        ↓
transaction.atomic()
        ↓
select_for_update()
        ↓
re-check stock availability
        ↓
reserve stock atomically
        ↓
transition order state
        ↓
commit
```

The existence of these design decisions is design evidence only. It is not
verification of the final business behavior.

---

## 7. Update Protocol

When implementing a requirement, update only the corresponding row.

### Step 1 — Design

Populate the design references.

```text
Status = DESIGNED
```

### Step 2 — Implementation

Add the concrete production source location.

Example:

```text
Implementation = apps/orders/services.py::confirm_order
```

Then:

```text
Status = IMPLEMENTED
```

### Step 3 — Test

Add the automated test location.

Example:

```text
Test = tests/orders/test_confirmation.py::test_confirm_order_reserves_stock
```

After the test passes:

```text
Status = TESTED
```

### Step 4 — Verification

Record reproducible execution evidence.

Example:

```text
Evidence = python -m pytest tests/orders/test_confirmation.py -q → PASS
```

After review:

```text
Status = VERIFIED
```

---

## 8. Evidence Rules

A requirement may not skip directly from `DESIGNED` to `VERIFIED`.

For a normal business requirement:

```text
DESIGNED
→ IMPLEMENTED
→ TESTED
→ VERIFIED
```

Each transition must have corresponding evidence.

### Evidence must be concrete

Preferred:

```text
Implementation:
apps/orders/services.py::confirm_order

Test:
tests/orders/test_confirmation.py::test_reserves_stock_atomically

Evidence:
python -m pytest tests/orders/test_confirmation.py -q
→ 1 passed
```

Avoid vague evidence such as:

```text
"implemented"
"works"
"tested manually"
"covered by service"
```

### No evidence inflation

The following are not sufficient for `VERIFIED`:

* model existence
* database column existence
* migration existence
* endpoint existence
* passing `manage.py check`
* successful application startup
* code inspection alone
* a test file existing without execution evidence

---

## 9. Requirement Status Summary

The initial matrix is intentionally conservative.

Current status categories:

```text
DESIGNED
IMPLEMENTED
TESTED
VERIFIED
PENDING
```

As implementation proceeds, this summary should be regenerated from the
individual requirement rows rather than maintained manually.

The authoritative state is the requirement row itself.

---

## 10. Future Verification Evidence

Future rows should capture concrete evidence such as:

```text
Implementation:
apps/<domain>/services.py::<function>

Test:
tests/<domain>/test_<behavior>.py::<test_function>

Evidence:
python -m pytest <test-path> -q
→ PASS
```

For concurrency-sensitive inventory workflows, evidence should additionally
cover transactional behavior and concurrent access where required.

For API requirements, evidence should identify the endpoint test.

For webhook requirements, evidence should identify the webhook handler,
validation/idempotency implementation, and corresponding test.

For migration requirements, evidence should identify the import command,
fixture/input data, validation result, transformation behavior, and generated
migration report.

For CI requirements, evidence should identify the workflow configuration and
a successful CI execution.

---

## 11. Change History

| Date       | Change                                      | Commit       |
| ---------- | ------------------------------------------- | ------------ |
| 2026-09-02 | Initial traceability matrix established     | Working tree |
| 2026-09-02 | Requirements baseline established           | `14db353`    |
| 2026-09-02 | Database design refined                     | `c5a9e31`    |
| 2026-09-02 | Model implementation specification approved | `13d0a8d`    |

---

## 12. Traceability Principle

This document is not a declaration that the ERP is complete.

It is the controlled bridge between the requirements baseline and future
engineering evidence.

A requirement is considered complete only when the matrix can answer all of
the following questions:

1. What requirement are we satisfying?
2. Where was it designed?
3. Where is it implemented?
4. Which test exercises it?
5. What was the reproducible test result?
6. Why is the result sufficient to call the requirement verified?

Until those questions can be answered, the requirement must not be marked
`VERIFIED`.
