# ERP Requirements Traceability Matrix

**Status:** Living Engineering Artifact

**Requirements Baseline:** `14db353`

**Database Design Baseline:** `c5a9e31`

**Model Specification Baseline:** `13d0a8d`

**Last Updated:** 2026-09-04

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

`PARTIAL` is used when meaningful implementation and executable test evidence
exist, but the broader requirement contract is not yet fully established.

A status must only advance when corresponding engineering evidence exists.

### Status definitions

| Status        | Meaning                                                                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PENDING`     | No sufficient design or implementation evidence has been established yet.                                                                            |
| `DESIGNED`    | The requirement is represented by an approved architecture, database, model, API, or other design artifact.                                          |
| `IMPLEMENTED` | The required production implementation exists in source code.                                                                                        |
| `TESTED`      | Automated or otherwise explicit tests exercise the requirement and pass, but the available evidence does not justify the stronger `VERIFIED` claim.  |
| `PARTIAL`     | Meaningful implementation and executable tests exist, but the broader requirement contract is not yet fully established.                             |
| `VERIFIED`    | The implementation and test evidence have been reviewed against the requirement and the verification result is reproducible within the stated scope. |

### Important verification rule

The existence of a model, database constraint, migration, endpoint skeleton,

or documentation entry does **not** by itself justify `TESTED` or `VERIFIED`.

`VERIFIED` requires implementation evidence, test evidence, and a reproducible

verification result within the stated requirement scope.

The matrix must not claim verification beyond the evidence actually established.

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

Milestone-specific reconciliation documents provide an additional verification
layer for requirements whose implementation and tests were established during
later milestones.

---

## 3. Requirements Matrix

| ID          | Requirement                  | Architecture / Design                       | Database      | Model       | Migration                       | Implementation                                                                                                | Test                                                                                                                                                                                                                                                                                                                                            | Evidence                                                                                                                                                                                                                  | Status      |
| ----------- | ---------------------------- | ------------------------------------------- | ------------- | ----------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| ERP-REQ-001 | Customer Creation            | `architecture.md` / Customers               | `database.md` | `models.md` | `customers/0001_initial.py`     | `apps/api/customer_views.py::CustomerListCreateView; apps/api/serializers.py::CustomerSerializer` | `tests/api/test_customers.py::test_customer_create_returns_201_and_server_managed_fields; test_customer_create_rejects_empty_name; test_customer_create_does_not_allow_client_to_set_active` | `docker compose exec web pytest -q tests/api/test_customers.py` → 16 passed; full regression → 188 passed | VERIFIED |
| ERP-REQ-002 | Customer Retrieval           | `architecture.md` / Customers               | `database.md` | `models.md` | `customers/0001_initial.py`     | `apps/api/customer_views.py::CustomerListCreateView; apps/api/customer_views.py::CustomerDetailView` | `tests/api/test_customers.py::test_customer_list_returns_customers; test_customer_retrieve_returns_customer; test_customer_retrieve_unknown_customer_returns_404` | `docker compose exec web pytest -q tests/api/test_customers.py` → 16 passed; full regression → 188 passed | VERIFIED |
| ERP-REQ-003 | Customer Status              | `architecture.md` / Customers               | `database.md` | `models.md` | `customers/0001_initial.py`     | `apps/api/serializers.py::CustomerSerializer; apps/api/customer_views.py::CustomerDetailView` | `tests/api/test_customers.py::test_customer_retrieve_returns_customer; test_customer_retrieve_exposes_inactive_state; test_customer_create_does_not_allow_client_to_set_active` | `docker compose exec web pytest -q tests/api/test_customers.py` → 16 passed; full regression → 188 passed | VERIFIED |
| ERP-REQ-004 | Product Creation             | `architecture.md` / Products                | `database.md` | `models.md` | `products/0001_initial.py`      | `apps/products/models.py::Product` | `tests/api/test_products.py::test_product_create_returns_201_and_server_managed_fields` | `docker compose exec web pytest -q tests/api/test_products.py` → 15 passed; full regression → 188 passed | VERIFIED |
| ERP-REQ-005 | Unique SKU                   | `architecture.md` / Products                | `database.md` | `models.md` | `products/0001_initial.py`      | `apps/products/models.py::Product.sku` (`unique=True`)                                                        | `tests/domain/test_model_integrity.py::test_product_sku_must_be_unique`                                                                                                                                                                                                                                                                         | `python -m pytest -q tests/domain/test_model_integrity.py` → 10 passed                                                                                                                                                    | TESTED      |
| ERP-REQ-006 | Product Validation           | `architecture.md` / Products                | `database.md` | `models.md` | `products/0001_initial.py`      | `apps/products/models.py::Product` DB constraints for non-empty SKU/name and non-negative unit price | `tests/api/test_products.py::test_product_create_rejects_negative_price; test_product_create_rejects_empty_sku; test_product_create_rejects_empty_name` | `docker compose exec web pytest -q tests/api/test_products.py` → 15 passed; full regression → 188 passed | VERIFIED |
| ERP-REQ-007 | Warehouse Management         | `architecture.md` / Warehouses              | `database.md` | `models.md` | `warehouses/0001_initial.py`    | `apps/warehouses/models.py::Warehouse`                                                                        | `tests/domain/test_model_integrity.py::test_warehouse_code_must_be_unique; test_warehouse_preserves_required_fields`                                                                                                                                                                                                                            | `python -m pytest -q tests/domain/test_model_integrity.py` → 10 passed                                                                                                                                                    | TESTED      |
| ERP-REQ-008 | Stock Representation         | `architecture.md` / Inventory               | `database.md` | `models.md` | `inventory/0001_initial.py`     | `apps/inventory/models.py::StockItem`                                                                         | `tests/domain/test_model_integrity.py::test_stock_item_product_warehouse_pair_must_be_unique; test_stock_item_allows_same_product_in_different_warehouses`                                                                                                                                                                                      | `python -m pytest -q tests/domain/test_model_integrity.py` → 10 passed                                                                                                                                                    | TESTED      |
| ERP-REQ-009 | Stock Quantities             | `architecture.md` / Inventory               | `database.md` | `models.md` | `inventory/0001_initial.py`     | `apps/inventory/models.py::StockItem.quantity; reserved_quantity; available_quantity`                         | `tests/domain/test_model_integrity.py::test_stock_item_available_quantity_is_derived; test_stock_item_rejects_negative_quantity; test_stock_item_rejects_negative_reserved_quantity`                                                                                                                                                            | `python -m pytest -q tests/domain/test_model_integrity.py` → 10 passed                                                                                                                                                    | TESTED      |
| ERP-REQ-010 | Stock Validation             | `architecture.md` / Inventory               | `database.md` | `models.md` | `inventory/0001_initial.py`     | `apps/inventory/models.py::StockItem` DB constraints                                                          | `tests/domain/test_model_integrity.py::test_stock_item_rejects_negative_quantity; test_stock_item_rejects_negative_reserved_quantity; test_stock_item_rejects_reserved_quantity_above_quantity`                                                                                                                                                 | `python -m pytest -q tests/domain/test_model_integrity.py` → 10 passed                                                                                                                                                    | TESTED      |
| ERP-REQ-011 | Inventory Consistency        | Inventory invariants                        | `database.md` | `models.md` | `inventory/0001_initial.py`     | `apps/orders/services.py::confirm_order` using `transaction.atomic()` and `select_for_update()`               | `tests/orders/test_confirmation.py::test_confirmation_is_atomic_when_later_product_is_insufficient; test_concurrent_confirmation_of_same_order; test_concurrent_orders_competing_for_same_stock`                                                                                                                                                | `python -m pytest -q tests/orders/test_confirmation.py` → 18 passed; `python -m pytest -q` → 45 passed                                                                                                                    | VERIFIED    |
| ERP-REQ-012 | Sales Order Creation         | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/models.py::SalesOrder` | `tests/api/test_orders.py::test_order_create_returns_201_and_creates_draft` | `docker compose exec web pytest -q tests/api/test_orders.py` → 49 passed; full regression → 188 passed | VERIFIED |
| ERP-REQ-013 | Sales Order Lines            | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/models.py::SalesOrderLine`                                                                       | `tests/orders/test_confirmation.py::test_confirm_aggregates_multiple_lines_for_same_product; test_confirm_valid_draft_order`                                                                                                                                                                                                                    | `python -m pytest -q tests/orders/test_confirmation.py` → 18 passed                                                                                                                                                       | TESTED      |
| ERP-REQ-014 | Positive Quantities          | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/models.py::SalesOrderLine.quantity` DB CHECK (`quantity > 0`)                                    | `tests/orders/test_confirmation.py::test_invalid_quantity_is_rejected_by_database_constraint`                                                                                                                                                                                                                                                   | `python -m pytest -q tests/orders/test_confirmation.py` → 18 passed                                                                                                                                                       | TESTED      |
| ERP-REQ-015 | Price Snapshot               | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/models.py::SalesOrderLine.unit_price` | `tests/api/test_orders.py::test_order_create_snapshots_current_product_price` | `docker compose exec web pytest -q tests/api/test_orders.py` → 49 passed; full regression → 188 passed | VERIFIED |
| ERP-REQ-016 | Draft State                  | `architecture.md` / Orders                  | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/models.py::SalesOrder.Status.DRAFT`                                                              | `tests/domain/test_model_integrity.py::test_sales_order_defaults_to_draft`                                                                                                                                                                                                                                                                      | `python -m pytest -q tests/domain/test_model_integrity.py` → 10 passed                                                                                                                                                    | TESTED      |
| ERP-REQ-017 | Order Confirmation           | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/services.py::confirm_order`                                                                      | `tests/orders/test_confirmation.py::test_confirm_valid_draft_order; test_confirm_non_draft_order_raises_invalid_order_state; test_confirm_inactive_customer_raises_inactive_customer; test_confirm_order_without_lines_raises_order_has_no_lines; test_confirm_inactive_product_raises_inactive_product`                                        | `python -m pytest tests/orders/test_confirmation.py -q` → 18 passed                                                                                                                                                       | VERIFIED    |
| ERP-REQ-018 | Stock Reservation            | Inventory/order workflow                    | `database.md` | `models.md` | `inventory/0001_initial.py`     | `apps/orders/services.py::confirm_order`                                                                      | `tests/orders/test_confirmation.py::test_confirm_reserves_single_product; test_confirm_reserves_stock_across_multiple_warehouses; test_confirm_aggregates_multiple_lines_for_same_product; test_confirm_commits_order_and_reservation_together; test_confirm_allocates_stock_by_stock_item_id; test_concurrent_orders_competing_for_same_stock` | `python -m pytest tests/orders/test_confirmation.py -q` → 18 passed                                                                                                                                                       | VERIFIED    |
| ERP-REQ-019 | Insufficient Stock           | Inventory/order workflow                    | `database.md` | `models.md` | `inventory/0001_initial.py`     | `apps/orders/services.py::confirm_order`                                                                      | `tests/orders/test_confirmation.py::test_confirm_insufficient_stock_raises_insufficient_stock; test_insufficient_stock_leaves_order_in_draft; test_insufficient_stock_leaves_inventory_unchanged; test_confirmation_is_atomic_when_later_product_is_insufficient; test_concurrent_orders_competing_for_same_stock`                              | `python -m pytest tests/orders/test_confirmation.py -q` → 18 passed                                                                                                                                                       | VERIFIED    |
| ERP-REQ-020 | Order Cancellation           | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/services.py::cancel_order`                                                                       | `tests/orders/test_lifecycle.py` lifecycle coverage                                                                                                                                                                                                                                                                                             | 19 dedicated lifecycle tests passed; full regression before 2D: 132 passed; commit `e59e34e`                                                                                                                              | VERIFIED    |
| ERP-REQ-021 | Shipment                     | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/services.py::ship_order`                                                                         | `tests/orders/test_lifecycle.py` lifecycle coverage                                                                                                                                                                                                                                                                                             | 19 dedicated lifecycle tests passed; full regression before 2D: 132 passed; commit `e59e34e`                                                                                                                              | VERIFIED    |
| ERP-REQ-022 | Completion                   | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/services.py::complete_order`                                                                     | `tests/orders/test_lifecycle.py` lifecycle coverage                                                                                                                                                                                                                                                                                             | 19 dedicated lifecycle tests passed; full regression before 2D: 132 passed; commit `e59e34e`                                                                                                                              | VERIFIED    |
| ERP-REQ-023 | Completed Order Immutability | Order lifecycle design                      | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/orders/services.py` lifecycle state enforcement                                                         | `tests/orders/test_lifecycle.py` lifecycle state-enforcement coverage                                                                                                                                                                                                                                                                           | 19 dedicated lifecycle tests passed; full regression before 2D: 132 passed; commit `e59e34e`                                                                                                                              | VERIFIED    |
| ERP-REQ-024 | API Versioning               | `api.md`                                    | —             | —           | —                               | `/api/v1/` routing                                                                                            | API routing tests                                                                                                                                                                                                                                                                                                                               | `/api/v1/` routes exercised by API test suites                                                                                                                                                                            | TESTED      |
| ERP-REQ-025 | Customer API                 | `api.md` / Customers                        | —             | `models.md` | `customers/0001_initial.py`     | Customer REST API                                                                                             | `tests/api/test_customers.py`                                                                                                                                                                                                                                                                                                                   | Customer API tests passed; broader regression evidence available                                                                                                                                                          | VERIFIED    |
| ERP-REQ-026 | Product API                  | `api.md` / Products                         | —             | `models.md` | `products/0001_initial.py`      | `apps/api/product_views.py::ProductListCreateView; ProductDetailView`                                         | `tests/api/test_products.py`                                                                                                                                                                                                                                                                                                                    | Dedicated product API tests cover list, retrieve, create, validation, permissions and roles                                                                                                                               | VERIFIED    |
| ERP-REQ-027 | Inventory API                | `api.md` / Inventory                        | `database.md` | `models.md` | `inventory/0001_initial.py`     | `apps/api/inventory_views.py::InventoryListView; InventoryDetailView`                                         | `tests/api/test_inventory.py`                                                                                                                                                                                                                                                                                                                   | Dedicated inventory API tests cover list, detail, 404, pagination, authentication, roles, fields and no-write behavior                                                                                                    | VERIFIED    |
| ERP-REQ-028 | Sales Order API              | `api.md` / Orders                           | `database.md` | `models.md` | `orders/0001_initial.py`        | `apps/api/order_views.py` lifecycle endpoints                                                                 | `tests/api/test_orders.py`                                                                                                                                                                                                                                                                                                                      | 49 dedicated order API tests passed; full regression 149 passed; commit `850d261`                                                                                                                                         | VERIFIED    |
| ERP-REQ-029 | API Validation               | `api.md` / API error design                 | —             | —           | —                               | DRF serializers and API error handling                                                                        | 2D/2E API error tests                                                                                                                                                                                                                                                                                                                           | Structured validation/business/integration error tests; no globally centralized unexpected-error contract                                                                                                                 | TESTED      |
| ERP-REQ-030 | Payment Webhook              | Integration architecture                    | `database.md` | `models.md` | `integrations/0001_initial.py`  | `apps/api/integration_views.py::PaymentWebhookView`; `apps/integrations/services.py::process_payment_webhook` | `tests/integrations/test_payment_webhook.py`                                                                                                                                                                                                                                                                                                    | 8 dedicated webhook tests passed; full regression 157 passed; commit `0fb41d2`                                                                                                                                            | VERIFIED    |
| ERP-REQ-031 | Webhook Validation           | Integration architecture                    | `database.md` | `models.md` | `integrations/0001_initial.py`  | `apps/api/serializers.py::PaymentWebhookSerializer`                                                           | `tests/integrations/test_payment_webhook.py` invalid-payload cases                                                                                                                                                                                                                                                                              | 8 dedicated webhook tests passed; full regression 157 passed                                                                                                                                                              | VERIFIED    |
| ERP-REQ-032 | Webhook Idempotency          | Integration architecture                    | `database.md` | `models.md` | `integrations/0001_initial.py`  | `apps/integrations/services.py::process_payment_webhook`; unique external event ID                            | `tests/integrations/test_payment_webhook.py` duplicate-event test                                                                                                                                                                                                                                                                               | Duplicate webhook behavior tested; concurrent first-delivery race remains untested and production-grade distributed idempotency is not established                                                                        | TESTED      |
| ERP-REQ-033 | Unknown Order Webhook        | Integration architecture                    | `database.md` | `models.md` | `integrations/0001_initial.py`  | `apps/integrations/services.py::process_payment_webhook`                                                      | `tests/integrations/test_payment_webhook.py` unknown-order case                                                                                                                                                                                                                                                                                 | Unknown order persisted as FAILED event; 8 dedicated webhook tests passed                                                                                                                                                 | VERIFIED    |
| ERP-REQ-034 | Legacy Customer Import | Integration / Migration design | — | — | — | `apps/customers/services.py::import_customers`; `apps/customers/management/commands/import_customers.py` | `tests/migrations/test_customer_import.py`; `tests/management/test_import_customers_command.py` | Legacy customer CSV files are imported through a Django management command delegating to the customer migration service; 13 dedicated migration tests and full regression pass | VERIFIED |
| ERP-REQ-035 | Migration Validation | Integration / Migration design | — | — | — | `apps/customers/services.py::_validate_row` | `tests/migrations/test_customer_import.py` invalid-record tests | Legacy records are explicitly validated before `Customer.objects.create()`; invalid rows are rejected and reported rather than silently inserted | VERIFIED |
| ERP-REQ-036 | Data Transformation | Integration / Migration design | — | — | — | `apps/customers/services.py::_transform_row` | `tests/migrations/test_customer_import.py::test_customer_import_transforms_whitespace_and_empty_optional_values` | Transformation explicitly strips string values and converts empty optional values to `None`; behaviour is directly tested | VERIFIED |
| ERP-REQ-037 | Migration Report | Integration / Migration design | — | — | — | `apps/customers/services.py::CustomerImportReport`; `apps/customers/management/commands/import_customers.py` | `tests/migrations/test_customer_import.py`; `tests/management/test_import_customers_command.py` | Migration reports processed, imported and rejected records plus row/field/message validation diagnostics | VERIFIED |
| ERP-REQ-038 | Authentication               | Accounts architecture                       | —             | —           | —                               | `config/settings.py::REST_FRAMEWORK`; `apps/accounts/permissions.py::CustomerAccessPermission`                | `tests/api/test_customers.py` anonymous-access tests                                                                                                                                                                                                                                                                                            | Authentication tests passed; full regression evidence available                                                                                                                                                           | VERIFIED    |
| ERP-REQ-039 | User Roles                   | Accounts architecture                       | —             | —           | `accounts/0001_create_roles.py` | `apps/accounts/permissions.py::ROLE_ADMIN; ROLE_OPERATIONS; ROLE_READ_ONLY`                                   | Customer API role/permission tests                                                                                                                                                                                                                                                                                                              | Admin, operations and read-only role behavior tested; full regression evidence available                                                                                                                                  | VERIFIED    |
| ERP-REQ-040 | Permission Enforcement       | Accounts architecture                       | —             | —           | —                               | `apps/accounts/permissions.py::CustomerAccessPermission`; customer API views                                  | `tests/api/test_customers.py` permission tests                                                                                                                                                                                                                                                                                                  | Customer API permission matrix tested; broader endpoint coverage remains possible                                                                                                                                         | TESTED      |
| ERP-REQ-041 | Business Errors              | Application/service architecture            | —             | `models.md` | —                               | `apps/orders/exceptions.py` order-domain exception hierarchy; `apps/api/exceptions.py::custom_exception_handler` business-error mappings | `tests/api/test_error_handling.py` business-error contract tests; lifecycle API error tests | Controlled business-rule errors are mapped to explicit API error codes/messages and exercised by automated tests; no requirement for a single cross-domain exception hierarchy is claimed | VERIFIED    |
| ERP-REQ-042 | Consistent API Errors        | `api.md` / API error design                 | —             | —           | —                               | `apps/api/exceptions.py::custom_exception_handler` centralized API error handling | `tests/api/test_error_handling.py` consistent envelope tests; `tests/api/test_orders.py`; webhook API error tests | Validation, business-rule, integration and unexpected failures use the common top-level `error` envelope with distinguishable error codes | VERIFIED    |
| ERP-REQ-043 | Unexpected Errors            | Application/API architecture                | —             | —           | —                               | `apps/api/exceptions.py::custom_exception_handler` centralized DRF exception handler | `tests/api/test_error_handling.py::test_unexpected_error_contract_is_safe`; `test_unexpected_errors_are_logged` | Unexpected exceptions return a safe generic 500 response without internal exception details; controlled unexpected-error logging is exercised by regression tests | VERIFIED    |
| ERP-REQ-044 | Application Logging          | Application architecture                    | —             | —           | —                               | `config/settings.py::LOGGING`; application loggers in order, integration and API exception services; `apps/api/exceptions.py::_log_request_failure`; `apps/customers/services.py` migration failure logging | `tests/api/test_error_handling.py` M4 request-failure, business-failure, authentication, permission, migration-failure and sensitive-operational logging tests; full regression | Structured application logging covers request failures, order transitions, inventory changes, webhook processing, migration failures and unexpected application errors; M4 targeted suite passed 18/18 and full regression passed 188/188 | VERIFIED    |
| ERP-REQ-045 | Sensitive Information        | Application/configuration architecture      | —             | —           | —                               | `config/settings.py::LOGGING` application formatter configuration; safe structured logging in `apps/api/exceptions.py` and `apps/customers/services.py` | `tests/api/test_error_handling.py` sensitive-information and sensitive-operational logging tests | Structured logging avoids rendering sensitive request data and sensitive structured fields; M4 tests verify sensitive values are not exposed through the covered logging paths. No universal sanitizer for secrets explicitly embedded directly in arbitrary log messages is claimed | PARTIAL     |
| ERP-REQ-046 | Automated Testing            | `development.md`                            | —             | —           | —                               | Pytest test suite                                                                                             | Repeated full-project regression suites                                                                                                                                                                                                                                                                                                         | Pytest suite and repeated full regressions provide executable evidence                                                                                                                                                    | VERIFIED    |
| ERP-REQ-047 | Business Logic Testing       | `development.md` / test strategy            | —             | —           | —                               | Domain services and tests                                                                                     | Confirmation, lifecycle and webhook tests                                                                                                                                                                                                                                                                                                       | Business logic is covered by dedicated executable tests                                                                                                                                                                   | VERIFIED    |
| ERP-REQ-048 | Inventory Testing            | `development.md` / test strategy            | —             | `models.md` | —                               | Inventory and order confirmation workflows                                                                    | Inventory/model/confirmation/lifecycle tests                                                                                                                                                                                                                                                                                                    | Includes atomicity and concurrency evidence; broader concurrent scenarios remain limited                                                                                                                                  | VERIFIED    |
| ERP-REQ-049 | Order Lifecycle Testing      | `development.md` / lifecycle design         | —             | `models.md` | —                               | Order lifecycle services                                                                                      | `tests/orders/test_lifecycle.py`                                                                                                                                                                                                                                                                                                                | 19 dedicated lifecycle tests passed                                                                                                                                                                                       | VERIFIED    |
| ERP-REQ-050 | API Testing                  | `api.md` / `development.md`                 | —             | —           | —                               | Customer, product, inventory, order and webhook APIs                                                          | Dedicated API test suites and full regressions                                                                                                                                                                                                                                                                                                  | Customer/product/inventory/order/webhook API behavior exercised; endpoint-wide matrix can expand with future APIs                                                                                                         | VERIFIED    |
| ERP-REQ-051 | Webhook Testing              | Integration architecture / `development.md` | `database.md` | `models.md` | `integrations/0001_initial.py`  | Payment webhook implementation                                                                                | `tests/integrations/test_payment_webhook.py`                                                                                                                                                                                                                                                                                                    | 8 dedicated webhook tests passed; full regression 157 passed                                                                                                                                                              | VERIFIED    |
| ERP-REQ-052 | Migration Testing | `development.md` / migration design | — | — | — | `apps/customers/services.py`; `apps/customers/management/commands/import_customers.py` | `tests/migrations/test_customer_import.py`; `tests/management/test_import_customers_command.py` | Automated migration tests cover valid and invalid legacy customer records; 13 dedicated migration tests pass and are included in the 181-test full regression | VERIFIED |
| ERP-REQ-053 | PostgreSQL                   | Infrastructure architecture                 | `database.md` | —           | —                               | `config/settings.py` / Docker                                                                                 | —                                                                                                                                                                                                                                                                                                                                               | PostgreSQL 16 runtime verified                                                                                                                                                                                            | IMPLEMENTED |
| ERP-REQ-054 | Referential Integrity        | Database architecture                       | `database.md` | `models.md` | domain migrations               | Django relationships/migrations                                                                               | —                                                                                                                                                                                                                                                                                                                                               | PostgreSQL schema inspection                                                                                                                                                                                              | IMPLEMENTED |
| ERP-REQ-055 | Database Constraints         | Database architecture                       | `database.md` | `models.md` | domain migrations               | Django model constraints/migrations                                                                           | —                                                                                                                                                                                                                                                                                                                                               | PostgreSQL schema inspection                                                                                                                                                                                              | IMPLEMENTED |
| ERP-REQ-056 | Environment Configuration    | Configuration architecture                  | `database.md` | —           | —                               | `config/settings.py` reads environment variables for secret, debug, hosts and PostgreSQL settings             | —                                                                                                                                                                                                                                                                                                                                               | Environment configuration verified in settings implementation                                                                                                                                                             | VERIFIED    |
| ERP-REQ-057 | Secret Management            | Configuration architecture                  | `database.md` | —           | —                               | `.env.example` / settings                                                                                     | —                                                                                                                                                                                                                                                                                                                                               | Tracked `.env.example` contains placeholders; secrets are environment-configured; no real secret-management backend is claimed                                                                                            | VERIFIED    |
| ERP-REQ-058 | Environment Separation       | Configuration architecture                  | —             | —           | —                               | settings/environment configuration                                                                            | —                                                                                                                                                                                                                                                                                                                                               | Configuration architecture exists but explicit environment separation is not yet established                                                                                                                              | DESIGNED    |
| ERP-REQ-059 | Containerized Development    | Infrastructure architecture                 | `database.md` | —           | —                               | `Dockerfile`, `docker-compose.yml`                                                                             | —                                                                                                                                                                                                                                                                                                                                               | Dockerized Django application and PostgreSQL development environment builds and starts successfully; Compose configuration validates, PostgreSQL reaches healthy state, Django migrations apply, Django system checks pass, migration consistency is verified, Python sources compile successfully, and the full pytest regression passes in the container | VERIFIED    |
| ERP-REQ-060 | Database Container           | Infrastructure architecture                 | `database.md` | —           | —                               | `docker-compose.yml`                                                                                          | —                                                                                                                                                                                                                                                                                                                                               | PostgreSQL container runs as a separate Compose service; the container reaches a healthy state and the Django web service starts successfully against it | VERIFIED    |
| ERP-REQ-061 | Reproducible Environment     | Infrastructure/development architecture     | —             | —           | —                               | `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `docs/development.md`                                    | —                                                                                                                                                                                                                                                                                                                                               | Documented local and Docker development procedures are established; Docker image build, Compose startup, PostgreSQL healthcheck, Django migration, system check, migration consistency check, Python compilation, and full pytest regression execute successfully | VERIFIED    |
| ERP-REQ-062 | CI Pipeline                  | Development/CI architecture                 | `database.md` | —           | —                               | `.github/workflows/ci.yml`                                                                                     | —                                                                                                                                                                                                                                                                                                                                               | GitHub Actions workflow triggers on push and pull request, provisions PostgreSQL 16, installs Python 3.12 project/test dependencies, applies Django migrations, runs Django system checks, verifies migration consistency, compiles Python sources, and executes the full pytest suite; GitHub Actions CI #1 for commit `35a65ea` completed successfully | VERIFIED    |
| ERP-REQ-063 | CI Failure Handling          | Development/CI architecture                 | —             | —           | —                               | `.github/workflows/ci.yml`                                                                                     | —                                                                                                                                                                                                                                                                                                                                               | CI failure handling verified through temporary revision `2ff3f46`: the intentional failing test caused the GitHub Actions `Tests` step to terminate with exit code 1 and CI run #6 reported overall `Failure` (run `33890770456`) | VERIFIED    |
| ERP-REQ-064 | Architecture Documentation   | `architecture.md`                           | —             | —           | —                               | —                                                                                                             | —                                                                                                                                                                                                                                                                                                                                               | Substantive `docs/architecture.md` covering boundaries, components, transactions and design decisions                                                                                                                     | VERIFIED    |
| ERP-REQ-065 | Database Documentation       | `database.md`                               | `database.md` | —           | —                               | —                                                                                                             | —                                                                                                                                                                                                                                                                                                                                               | Substantive `docs/database.md` covering entities, relationships, constraints, transactions and migrations                                                                                                                 | VERIFIED    |
| ERP-REQ-066 | API Documentation            | `api.md`                                    | —             | —           | —                               | —                                                                                                             | —                                                                                                                                                                                                                                                                                                                                               | Substantive `docs/api.md` covering endpoints, schemas, validation, errors, lifecycle and integration design; stale pre-2D/2E implementation-status text and an obsolete webhook path require documentation reconciliation | VERIFIED    |
| ERP-REQ-067 | Development Documentation    | `development.md`                            | —             | —           | —                               | `docs/development.md`                                                                                          | —                                                                                                                                                                                                                                                                                                                                               | Development guide documents prerequisites, environment configuration, Python setup, PostgreSQL startup, migrations, Django checks, tests, compilation checks, Docker workflow, logs, shutdown, reproducibility workflow, and management commands | VERIFIED    |
| ERP-REQ-068 | Version Control              | Development documentation                   | —             | —           | —                               | Git                                                                                                           | —                                                                                                                                                                                                                                                                                                                                               | Git repository and milestone history                                                                                                                                                                                      | VERIFIED    |
| ERP-REQ-069 | Meaningful Commits           | Development documentation                   | —             | —           | —                               | Git                                                                                                           | —                                                                                                                                                                                                                                                                                                                                               | Meaningful milestone commits with purpose-specific messages                                                                                                                                                               | VERIFIED    |
| ERP-REQ-070 | Reproducibility              | Development/infrastructure architecture     | —             | —           | —                               | `pyproject.toml`, Docker, migrations, `docs/development.md`                                                   | —                                                                                                                                                                                                                                                                                                                                               | Fresh clone from the GitHub repository at commit `3c821c061b6fc07c8a2abc20e3276b49b84d26d3` was built in a clean Docker environment with PostgreSQL 16 and a fresh database volume; migrations reported no pending changes, Django system checks passed, Python sources compiled successfully, and the full pytest regression completed with 188 passed and 0 failed (exit status 0) | VERIFIED    |

---

## 4. Current Verification Boundary

Milestones 2A–2E and the Milestone 2F error-handling/logging enhancements have established the current verification boundary.

The requirement-specific verification state is:

```text
VERIFIED     : 34
TESTED       : 15
IMPLEMENTED  : 8
PARTIAL      : 1
DESIGNED     : 4
PENDING      : 8
TOTAL        : 70
```

Milestone evidence currently establishes:

* 2A–2B: customer, product, inventory, and order-domain foundation and APIs
* 2C: executable sales-order lifecycle services
* 2D: REST API exposure of the lifecycle services
* 2E: payment webhook integration foundation
* 2F: centralized error handling and comprehensive structured logging (with sensitive‑information protection partial)

The current implementation and verification boundary does **not** establish
the following as complete:

* explicit sensitive-information protection for all log sources (no universal sanitizer)
* concurrent first-delivery webhook idempotency race handling
* complete environment separation
* complete application containerization
* complete reproducible developer setup
* CI failure-path verification
* real external payment-provider integration
* production carrier or fulfillment integration
* production deployment validation

`PARTIAL` is used where meaningful implementation and executable tests exist
but the broader requirement contract is not yet fully established.

`TESTED` is used where concrete implementation behavior has been exercised
but the available evidence does not justify the stronger `VERIFIED` claim.

---

## 5. Existing Infrastructure Evidence

The following evidence exists independently of the later domain-service,
REST API, and integration milestones.

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

This infrastructure evidence establishes the environment foundation but does
not by itself establish the requirements whose statuses remain `PENDING`,
`DESIGNED`, `IMPLEMENTED`, or `PARTIAL`.

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

The implementation deliberately does not place critical lifecycle or
reservation workflows directly inside Django models.

Critical business workflows are implemented through explicit application/domain
services.

The order confirmation workflow established during the earlier milestones is
transactional:

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

Milestone 2C extends this service-oriented boundary with explicit lifecycle
services for cancellation, shipment, and completion.

Milestone 2D exposes those already-established lifecycle services through thin
REST API adapters. The API layer is responsible for HTTP concerns,
authentication/authorization, request handling, serialization, and mapping
known business exceptions to HTTP responses. Business rules remain in the
service layer.

The resulting architectural boundary is:

```text
HTTP request

    ↓

API View

    ↓

CustomerAccessPermission

    ↓

Lifecycle Service

    ↓

Transactional Business Logic

    ↓

OrderSerializer

    ↓

HTTP response
```

Milestone 2E adds an external payment webhook boundary with:

```text
HTTP webhook request

    ↓

PaymentWebhookSerializer

    ↓

PaymentWebhookView

    ↓

process_payment_webhook()

    ↓

ExternalEvent persistence

    ↓

duplicate / unknown-order / successful processing
```

The webhook foundation includes payload validation, external-event persistence,
duplicate-event handling, and explicit failed-event persistence for unknown
orders.

Milestone 2F adds a centralized exception handling boundary and structured
application logging:

```text
HTTP request

    ↓

API View

    ↓

(no explicit try/except)

    ↓

Application service

    ↓

Business exception / unexpected failure

    ↓

Centralized exception handler
    ├── business exceptions → error envelope
    ├── validation errors → validation envelope
    ├── unexpected errors → safe 500 + structured log
    └── other DRF exceptions → error envelope

    ↓

HTTP response
```

These implementations are backed by executable milestone-specific tests.
However, external provider integration, provider-specific signatures, retries,
distributed race handling, and production integration behavior remain outside
the current verification boundary.

Design artifacts alone are not treated as runtime verification.

---

## 7. Update Protocol

When implementing a requirement, update only the corresponding row and its
supporting evidence.

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

After review against the requirement:

```text
Status = VERIFIED
```

### Partial status

Use `PARTIAL` when the requirement has meaningful implementation and executable
test evidence but the complete requirement contract is not yet established.

For example, the current business-error requirement has an implemented order
exception hierarchy and lifecycle API mappings, but there is not yet a unified
cross-domain business-error taxonomy.

Similarly, the API-error requirement has structured order API errors and
webhook error handling, but the error envelopes are not yet unified across
validation, business-rule, and integration failures.

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

`PARTIAL` may be used when implementation and test evidence exist but the
complete requirement contract remains incomplete.

Each status transition must have corresponding evidence.

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

A full regression result may support verification when the requirement-specific
implementation and test evidence are also identifiable.

A requirement must not be marked `VERIFIED` merely because another unrelated
requirement passed during the same regression.

---

## 9. Requirement Status Summary

The authoritative reconciled matrix contains 70 requirements.

Current status distribution:

| Status      |  Count |
| ----------- | -----: |
| VERIFIED    |     34 |
| TESTED      |     15 |
| IMPLEMENTED |      8 |
| PARTIAL     |      1 |
| DESIGNED    |      4 |
| PENDING     |      8 |
| **TOTAL**   | **70** |

The status distribution is the result of the Milestone 2A–2E and 2F reconciliation.

The authoritative state is the individual requirement row.

The status summary should be regenerated from the requirement rows rather than
maintained independently.

The current matrix therefore represents:

```text
34 VERIFIED
15 TESTED
 8 IMPLEMENTED
 1 PARTIAL
 4 DESIGNED
 8 PENDING
----------------
70 REQUIREMENTS
```

`VERIFIED` does not mean that the entire ERP is production-complete.

It means that the specific requirement has sufficient implementation,
test, and reproducible verification evidence within the stated scope.

---

## 10. Future Verification Evidence

The current milestone evidence provides the following reproducible checkpoints.

### Milestone 2C — Sales Order Lifecycle

```text
Dedicated lifecycle suite:

19 passed

Full project regression:

132 passed

Commit:

e59e34e Add sales order lifecycle services
```

This evidence supports the verified lifecycle requirements within the stated
2C scope.

### Milestone 2D — Lifecycle REST API

The RED/GREEN cycle established that the API tests initially failed because
the lifecycle routes were absent and then passed after the API adapters were
implemented.

```text
Dedicated order API suite:

49 passed in 33.74s

Full project regression:

149 passed in 66.47s

Commit:

850d261 Expose sales order lifecycle API

git diff --check:

clean
```

The API implementation preserves the service-layer boundary and maps known
order-domain exceptions to structured HTTP errors.

### Milestone 2E — Payment Webhook Integration Foundation

```text
Dedicated webhook suite:

8 passed in 8.17s

Full project regression:

157 passed in 72.65s

Django system check:

System check identified no issues (0 silenced).

Python compilation:

PASS

git diff --check:

clean

Commit:

0fb41d2 Add payment webhook integration foundation
```

The 2E evidence establishes the simulated payment-webhook foundation within
scope.

It does not establish:

* real payment-provider integration
* provider-specific signature/HMAC validation
* provider credentials
* network communication with a real provider
* retry/dead-letter infrastructure
* asynchronous processing
* monitoring/alerting
* concurrent first-delivery race verification
* payment reconciliation
* refunds
* payment-driven order lifecycle transitions
* production deployment validation

### Milestone 2F — Centralized Error Handling and Logging

```text
Dedicated error/logging test suite:

18 passed

Full project regression:

188 passed

Key evidence:
- Centralized exception handler maps business/validation/unexpected errors
- Structured request-failure logging covers validation, authentication,
  permission and business failures
- Structured logging covers order transitions, inventory changes,
  webhook processing and unexpected application errors
- Operational customer migration failures are logged separately from
  validation rejections
- Sensitive structured fields are not rendered by the log formatter
- Unexpected API errors return a safe generic 500 response

Commit:

c695b2e Implement M4 request failure logging
```

The 2F evidence establishes the centralized exception-handling and
structured application-logging foundation within the current requirement scope.

It does not establish:

* a universal sanitizer for secrets embedded directly in arbitrary log messages
* production-grade monitoring or alerting
* full environment separation
* CI-based logging verification

### Future evidence requirements

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

For API requirements, evidence should identify the endpoint test and the
relevant authentication, authorization, validation, and error behavior.

For webhook requirements, evidence should identify the webhook handler,
validation/idempotency implementation, and corresponding tests.

For migration requirements, evidence should identify the import command,
fixture/input data, validation result, transformation behavior, and generated
migration report.

For CI requirements, evidence should identify the workflow configuration and
a successful CI execution, including relevant failure-path behavior.

For reproducibility requirements, evidence should demonstrate that a clean
environment can install dependencies, configure the application, initialize
the database, run migrations, and execute the test suite using documented
procedures.

---

## 11. Change History

| Date       | Change                                                                      | Commit                    |
| ---------- | --------------------------------------------------------------------------- | ------------------------- |
| 2026-09-02 | Initial traceability matrix established                                     | Working tree              |
| 2026-09-02 | Requirements baseline established                                           | `14db353`                 |
| 2026-09-02 | Database design refined                                                     | `c5a9e31`                 |
| 2026-09-02 | Model implementation specification approved                                 | `13d0a8d`                 |
| 2026-09-03 | Milestones 2A–2E independently reconciled against the requirements baseline | `0fb41d2` baseline for 2E |
| 2026-09-03 | Traceability statuses synchronized with the authoritative reconciliation    | Working tree              |
| 2026-09-03 | Traceability narrative synchronized with the current verification boundary  | Working tree              |
| 2026-09-03 | Milestone 2F error-handling/logging reconciliation integrated               | Working tree              |
| 2026-09-04 | M4 request‑failure logging reconciliation                                   | `c695b2e`                 |

---

## 12. Traceability Principle

This document is not a declaration that the ERP is complete.

It is the controlled bridge between the requirements baseline and engineering
evidence.

The traceability matrix reflects the actual repository state and the evidence
that has been established. It must not represent intended architecture,
future implementation, or planned verification as completed engineering work.

A requirement is considered `VERIFIED` only when the matrix can answer all of
the following questions:

1. What requirement are we satisfying?
2. Where was it designed?
3. Where is it implemented?
4. Which test exercises it?
5. What was the reproducible test result?
6. Why is the result sufficient to call the requirement verified within the
   stated scope?

If implementation or test evidence exists but the broader requirement contract
is incomplete, the requirement may be `PARTIAL` or `TESTED` rather than
`VERIFIED`.

If only the design exists, the requirement remains `DESIGNED`.

If implementation exists without sufficient test evidence, the requirement
remains `IMPLEMENTED`.

If no sufficient design or implementation evidence exists, the requirement
remains `PENDING`.

The purpose of this discipline is to ensure that the traceability matrix
describes **what the repository can currently prove**, rather than what the
project intends to build next.

---

## 13. Traceability Synchronization Decision

The reconciliation audit has passed.

`docs/traceability.md` has been synchronized with the audited
Milestone 2A–2E and 2F reconciliation state.

The requirement set is consistent across:

- `docs/requirements.md`
- `docs/milestones_2a_2e_reconciliation.md`
- `docs/traceability.md`

All 70 requirement identifiers are present in all three documents,
and their recorded statuses match.

Milestone 2F is now fully reconciled for the requirements 041–045.
No additional Milestone 2F scope is implied by this synchronization.
