# Django ERP Operations Platform — Requirements Specification

**Document:** Requirements Specification  
**Project:** Django ERP Operations Platform  
**Version:** 1.0  
**Status:** Approved for Implementation  
**Last Updated:** 2026-09-02

---

# 1. Purpose

The Django ERP Operations Platform is a production-oriented backend system for managing customers, products, warehouses, inventory, and sales orders for a small or medium-sized business.

The project is designed to demonstrate production-oriented Python and Django engineering practices, including:

- Django ORM and relational data modelling
- PostgreSQL
- Business logic and workflow enforcement
- REST APIs
- Webhook integrations
- Data migration and transformation
- Validation
- Authentication and permissions
- Automated testing
- Docker-based development
- Continuous Integration
- Logging and error handling
- Git-based collaborative development
- Technical documentation

The system is intentionally limited in scope. It is not intended to replace a complete ERP platform such as Odoo.

---

# 2. Business Context

A business sells products to customers and manages inventory across one or more warehouses.

The system must support the operational workflow from customer and product management through sales order creation, stock validation, order confirmation, shipment, and completion.

The system must preserve data integrity when business operations fail or when multiple operations interact with the same inventory.

The system must also provide integration points for external systems and a controlled mechanism for importing legacy data.

---

# 3. Scope

## 3.1 In Scope

The system SHALL provide:

- Customer management
- Product management
- Warehouse management
- Inventory management
- Sales order management
- Sales order lifecycle management
- Stock availability and reservation
- Authentication
- Role-based permissions
- REST API
- External payment webhook simulation
- Data import and migration utilities
- Data validation and transformation
- Error handling
- Application logging
- PostgreSQL persistence
- Automated tests
- Docker-based development environment
- Continuous Integration
- Technical documentation

## 3.2 Out of Scope

The following are explicitly outside the scope of version 1.0:

- Real payment processing
- Real shipping provider integration
- Accounting system
- Tax calculation engine
- Payroll
- Complete e-commerce frontend
- Production cloud infrastructure
- Kubernetes
- High-availability deployment
- Real-world financial transactions
- Real customer personal data
- Complete ERP replacement
- Functional safety or safety-critical operation

---

# 4. Actors

## 4.1 ERP User

A user who interacts with the system to perform normal operational tasks.

## 4.2 Operations Manager

A user responsible for sales orders and inventory-related operations.

## 4.3 Administrator

A privileged user responsible for system administration, users, and permissions.

## 4.4 Read-Only User

A user who can retrieve operational information but cannot modify business data.

## 4.5 External System

An external application that communicates with the platform through REST APIs or webhooks.

---

# 5. Domain Model

The initial domain SHALL contain the following core entities:

- Customer
- Product
- Warehouse
- StockItem
- SalesOrder
- SalesOrderLine
- ExternalEvent

The high-level relationships are:

```text
Customer
    |
    | 1:N
    v
SalesOrder
    |
    | 1:N
    v
SalesOrderLine
    |
    | N:1
    v
Product
    |
    | 1:N
    v
StockItem
    |
    | N:1
    v
Warehouse
````

External integration events SHALL be represented independently so that webhook processing can be tracked and made idempotent.

---

# 6. Customer Requirements

## ERP-REQ-001 — Customer Creation

The system SHALL allow authorized users to create customer records.

A customer SHALL contain at least:

* unique identifier
* name
* email
* phone
* active/inactive status
* creation timestamp
* modification timestamp

---

## ERP-REQ-002 — Customer Retrieval

The system SHALL allow authorized users to retrieve customer records.

The system SHALL support retrieval of individual customers and listing of customers through the API.

---

## ERP-REQ-003 — Customer Status

The system SHALL support active and inactive customer states.

Inactive customers SHALL NOT be allowed to create new sales orders.

---

# 7. Product Requirements

## ERP-REQ-004 — Product Creation

The system SHALL allow authorized users to create product records.

A product SHALL contain at least:

* unique identifier
* SKU
* name
* description
* unit price
* active/inactive status
* creation timestamp
* modification timestamp

---

## ERP-REQ-005 — Unique SKU

Each product SHALL have a unique SKU.

The system SHALL reject attempts to create duplicate SKUs.

---

## ERP-REQ-006 — Product Validation

The system SHALL reject invalid product data.

At minimum:

* SKU SHALL NOT be empty
* product name SHALL NOT be empty
* unit price SHALL NOT be negative
* invalid product state SHALL be rejected

---

# 8. Warehouse Requirements

## ERP-REQ-007 — Warehouse Management

The system SHALL support warehouse records.

A warehouse SHALL contain at least:

* unique identifier
* unique warehouse code
* name
* location
* active/inactive status

---

# 9. Inventory Requirements

## ERP-REQ-008 — Stock Representation

The system SHALL maintain inventory per product and warehouse.

The inventory model SHALL represent the relationship:

```text
Warehouse + Product
```

as a unique inventory record.

---

## ERP-REQ-009 — Stock Quantities

The system SHALL distinguish between:

```text
quantity
reserved_quantity
available_quantity
```

The available quantity SHALL be calculated as:

```text
available_quantity = quantity - reserved_quantity
```

---

## ERP-REQ-010 — Stock Validation

The system SHALL NOT allow inventory operations that result in negative available stock.

---

## ERP-REQ-011 — Inventory Consistency

Critical inventory updates SHALL be performed atomically.

The system SHALL protect inventory operations against inconsistent state caused by concurrent operations.

Where necessary, database transactions and row-level locking SHALL be used.

---

# 10. Sales Order Requirements

## ERP-REQ-012 — Sales Order Creation

The system SHALL allow authorized users to create sales orders for active customers.

New sales orders SHALL initially have the status:

```text
DRAFT
```

---

## ERP-REQ-013 — Sales Order Lines

A sales order SHALL contain one or more sales order lines.

Each order line SHALL contain at least:

* product
* quantity
* unit price

---

## ERP-REQ-014 — Positive Quantities

Sales order line quantity SHALL be greater than zero.

Invalid quantities SHALL be rejected.

---

## ERP-REQ-015 — Price Snapshot

The unit price of a sales order line SHALL be stored when the order line is created.

Changes to the current product price SHALL NOT modify the historical price of existing orders.

---

# 11. Sales Order Lifecycle

The sales order lifecycle SHALL follow the state machine:

```text
                    ┌──────────────┐
                    │    DRAFT     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              │         confirm       cancel
              │            │            │
              │            v            v
              │       ┌───────────┐  ┌───────────┐
              │       │ CONFIRMED │  │ CANCELLED │
              │       └─────┬─────┘  └───────────┘
              │             │
              │           ship
              │             │
              │             v
              │       ┌───────────┐
              │       │  SHIPPED  │
              │       └─────┬─────┘
              │             │
              │          complete
              │             │
              │             v
              │       ┌───────────┐
              └─────► │ COMPLETED │
                      └───────────┘
```

Only explicitly supported state transitions SHALL be allowed.

---

## ERP-REQ-016 — Draft State

New sales orders SHALL initially have status:

```text
DRAFT
```

---

## ERP-REQ-017 — Order Confirmation

A sales order SHALL only be confirmed if:

* the customer is active
* the order contains at least one line
* all quantities are valid
* sufficient available stock exists for all required products

---

## ERP-REQ-018 — Stock Reservation

When an order is successfully confirmed, the system SHALL reserve the required inventory.

The reservation SHALL be part of the same atomic business operation as order confirmation.

---

## ERP-REQ-019 — Insufficient Stock

If sufficient stock is not available, order confirmation SHALL fail.

The order SHALL remain:

```text
DRAFT
```

Inventory SHALL remain unchanged.

---

## ERP-REQ-020 — Order Cancellation

A `DRAFT` order SHALL be cancellable.

The system SHALL reject unsupported cancellation transitions.

---

## ERP-REQ-021 — Shipment

Only a `CONFIRMED` order SHALL be allowed to transition to:

```text
SHIPPED
```

---

## ERP-REQ-022 — Completion

Only a `SHIPPED` order SHALL be allowed to transition to:

```text
COMPLETED
```

---

## ERP-REQ-023 — Completed Order Immutability

A `COMPLETED` order SHALL NOT be modified through normal business operations.

Historical order information SHALL remain preserved.

---

# 12. REST API Requirements

## ERP-REQ-024 — API Versioning

The REST API SHALL use explicit versioning.

The initial API version SHALL be:

```text
/api/v1/
```

---

## ERP-REQ-025 — Customer API

The API SHALL support:

* customer creation
* customer retrieval
* customer listing
* customer status management

---

## ERP-REQ-026 — Product API

The API SHALL support:

* product creation
* product retrieval
* product listing
* product status management

---

## ERP-REQ-027 — Inventory API

The API SHALL provide read access to inventory information.

The API SHALL expose sufficient information to determine available stock.

---

## ERP-REQ-028 — Sales Order API

The API SHALL support:

* sales order creation
* sales order retrieval
* sales order listing
* order confirmation
* order cancellation
* order shipment
* order completion

---

## ERP-REQ-029 — API Validation

Invalid API requests SHALL return structured error responses.

API clients SHALL receive useful validation information without exposure of internal implementation details.

---

# 13. Webhook Integration Requirements

## ERP-REQ-030 — Payment Webhook

The system SHALL expose a payment webhook endpoint:

```text
/api/v1/webhooks/payment
```

The webhook SHALL simulate notification from an external payment system.

No real payment processing is required.

---

## ERP-REQ-031 — Webhook Validation

Webhook payloads SHALL be validated before processing.

Invalid payloads SHALL be rejected.

At minimum, validation SHALL cover:

* event identifier
* event type
* order reference
* payment amount
* required payload fields

---

## ERP-REQ-032 — Webhook Idempotency

The same external event SHALL NOT be processed more than once.

The system SHALL maintain a unique external event identifier.

Repeated delivery of an already processed event SHALL NOT cause duplicate business effects.

---

## ERP-REQ-033 — Unknown Order Webhook

A webhook referencing a non-existing order SHALL NOT modify application state.

The event SHALL be rejected or recorded as failed according to the integration error-handling policy.

---

# 14. Data Migration and Transformation Requirements

## ERP-REQ-034 — Legacy Customer Import

The system SHALL provide a utility for importing legacy customer data from CSV files.

---

## ERP-REQ-035 — Migration Validation

Legacy records SHALL be validated before being inserted into the application database.

Invalid records SHALL NOT silently enter the system.

---

## ERP-REQ-036 — Data Transformation

Legacy records SHALL be transformed into the application's domain representation.

Transformation logic SHALL be explicit and testable.

---

## ERP-REQ-037 — Migration Report

The migration utility SHALL produce a report containing at least:

```text
records processed
records imported
records rejected
validation errors
```

The utility SHALL provide sufficient information to diagnose rejected records.

---

# 15. Authentication and Authorization Requirements

## ERP-REQ-038 — Authentication

Protected API endpoints SHALL require authentication.

---

## ERP-REQ-039 — User Roles

The system SHALL support at least the following logical roles:

```text
ADMIN
OPERATIONS
READ_ONLY
```

---

## ERP-REQ-040 — Permission Enforcement

Users SHALL only perform operations permitted by their role.

At minimum:

```text
ADMIN
    full administrative access

OPERATIONS
    operational customer/product/inventory/order access

READ_ONLY
    read-only access to permitted resources
```

The exact Django permission implementation SHALL be defined during architecture design.

---

# 16. Error Handling Requirements

## ERP-REQ-041 — Business Errors

Business rule violations SHALL generate controlled application errors.

Examples include:

```text
InsufficientStock
InvalidOrderTransition
InactiveCustomer
InvalidOrder
DuplicateWebhook
```

---

## ERP-REQ-042 — Consistent API Errors

API errors SHALL use a consistent response structure.

Clients SHALL be able to distinguish validation errors from business-rule errors and unexpected server errors.

---

## ERP-REQ-043 — Unexpected Errors

Unexpected exceptions SHALL be handled centrally.

Internal implementation details, stack traces, secrets, and sensitive information SHALL NOT be exposed to API clients.

Unexpected failures SHALL be logged appropriately.

---

# 17. Logging Requirements

## ERP-REQ-044 — Application Logging

The application SHALL provide structured application logging for important operations.

At minimum, logging SHALL cover:

* request failures
* order state transitions
* inventory changes
* webhook processing
* migration failures
* unexpected application errors

---

## ERP-REQ-045 — Sensitive Information

Logs SHALL NOT expose:

* passwords
* authentication credentials
* API secrets
* database credentials
* other sensitive secrets

---

# 18. Testing Requirements

## ERP-REQ-046 — Automated Testing

The project SHALL include automated tests using pytest.

---

## ERP-REQ-047 — Business Logic Testing

Critical business rules SHALL have automated tests.

---

## ERP-REQ-048 — Inventory Testing

Automated tests SHALL verify:

* sufficient stock
* insufficient stock
* stock reservation
* stock release where applicable
* prevention of negative available stock
* atomic inventory updates
* concurrent inventory behaviour where practical

---

## ERP-REQ-049 — Order Lifecycle Testing

Automated tests SHALL verify:

* valid state transitions
* invalid state transitions
* confirmation rules
* cancellation rules
* shipment rules
* completion rules
* completed-order immutability

---

## ERP-REQ-050 — API Testing

REST API endpoints SHALL have automated tests covering successful and failure scenarios.

---

## ERP-REQ-051 — Webhook Testing

Webhook tests SHALL verify:

* valid webhook
* invalid payload
* duplicate event
* unknown order
* failed processing
* idempotent processing

---

## ERP-REQ-052 — Migration Testing

Migration and validation functionality SHALL have automated tests.

Tests SHALL cover both valid and invalid legacy records.

---

# 19. Database Requirements

## ERP-REQ-053 — PostgreSQL

The production-oriented environment SHALL use PostgreSQL as the primary relational database.

---

## ERP-REQ-054 — Referential Integrity

Database relationships SHALL enforce appropriate referential integrity.

---

## ERP-REQ-055 — Database Constraints

Critical data invariants SHALL be enforced at database level where appropriate.

Examples include:

* unique SKU
* unique warehouse code
* unique external event identifier
* valid non-negative quantities
* valid relationships between domain entities

---

# 20. Configuration Requirements

## ERP-REQ-056 — Environment Configuration

Environment-specific configuration SHALL be externalized.

Configuration SHALL NOT depend on hard-coded secrets.

---

## ERP-REQ-057 — Secret Management

Secrets SHALL NOT be committed to Git.

The repository SHALL provide an `.env.example` file documenting required environment variables without containing real secrets.

---

## ERP-REQ-058 — Environment Separation

The application SHALL distinguish between development, testing, and production configuration.

---

# 21. Docker Requirements

## ERP-REQ-059 — Containerized Development

The project SHALL provide a Docker-based development environment.

---

## ERP-REQ-060 — Database Container

PostgreSQL SHALL run as a separate service in the development environment.

---

## ERP-REQ-061 — Reproducible Environment

The Docker configuration SHALL provide a reproducible development environment with documented startup procedures.

---

# 22. Continuous Integration Requirements

## ERP-REQ-062 — CI Pipeline

Every push and pull request SHALL trigger automated CI checks.

At minimum, CI SHALL perform:

```text
dependency installation
database setup
database migrations
Django system checks
automated tests
```

---

## ERP-REQ-063 — CI Failure Handling

A CI pipeline SHALL fail when required checks fail.

The repository SHALL provide a clear indication of whether the current revision passes the required automated checks.

---

# 23. Documentation Requirements

## ERP-REQ-064 — Architecture Documentation

The repository SHALL document:

* system architecture
* application boundaries
* major components
* major design decisions
* important trade-offs

---

## ERP-REQ-065 — Database Documentation

The repository SHALL document the main domain entities and their relationships.

---

## ERP-REQ-066 — API Documentation

The repository SHALL document:

* available API endpoints
* HTTP methods
* request format
* response format
* validation behaviour
* authentication requirements
* error responses

---

## ERP-REQ-067 — Development Documentation

A developer SHALL be able to understand how to:

* configure the project
* start the development environment
* start application services
* run database migrations
* run tests
* run quality checks

---

# 24. Git and Engineering Practice Requirements

## ERP-REQ-068 — Version Control

The project SHALL use Git for source control.

---

## ERP-REQ-069 — Meaningful Commits

Git commits SHALL represent meaningful engineering changes.

Commit messages SHALL describe the purpose of the change.

---

## ERP-REQ-070 — Reproducibility

A clean checkout of the repository SHALL provide sufficient documentation and configuration to reproduce the development and test environment.

---

# 25. Non-Functional Requirements

## ERP-NFR-001 — Maintainability

The application SHALL be organized into domain-oriented Django applications.

Business responsibilities SHALL be separated according to domain boundaries.

---

## ERP-NFR-002 — Testability

Critical business logic SHALL be structured so that it can be tested independently and deterministically.

---

## ERP-NFR-003 — Reliability

Critical inventory and order operations SHALL preserve database consistency.

Failed operations SHALL NOT leave partially applied business state.

---

## ERP-NFR-004 — Security

The application SHALL:

* protect authenticated endpoints
* enforce authorization
* keep secrets outside source control
* avoid exposing sensitive information through API responses or logs

---

## ERP-NFR-005 — Observability

Important business operations and application failures SHALL be observable through structured logging.

---

## ERP-NFR-006 — Reproducibility

Dependency and environment configuration SHALL be deterministic and documented.

---

## ERP-NFR-007 — API Consistency

The API SHALL follow consistent conventions for:

* URL structure
* HTTP methods
* status codes
* validation errors
* business errors
* authentication failures

---

# 26. Requirement Priority

Requirements SHALL be implemented according to the following priority levels:

## Priority 1 — Core

The following capabilities are mandatory for the first working release:

* Customer management
* Product management
* Warehouse management
* Inventory
* Sales orders
* Order lifecycle
* Business rules
* PostgreSQL
* Automated tests

## Priority 2 — Integration

The following capabilities SHALL be implemented after the core domain is stable:

* REST API
* Authentication
* Permissions
* Webhooks
* Error handling
* Logging

## Priority 3 — Operational Engineering

The following capabilities SHALL follow the core implementation:

* Data migration utility
* Docker
* CI
* Documentation
* Reproducibility improvements

---

# 27. Requirement-to-Test Traceability

Every functional requirement SHALL eventually be mapped to implementation evidence and automated verification.

The target relationship is:

```text
Requirement
    |
    v
Design
    |
    v
Implementation
    |
    v
Automated Test
    |
    v
Verification Evidence
```

Example:

```text
ERP-REQ-019
Insufficient stock
        |
        +--> inventory/order business logic
        |
        +--> test_insufficient_stock
        |
        +--> CI result
```

A requirement SHALL NOT be considered fully verified merely because corresponding code exists.

Verification SHALL require appropriate automated evidence wherever practical.

---

# 28. Acceptance Criteria

Version 1.0 SHALL be considered technically complete when:

1. Core domain entities are implemented.
2. PostgreSQL is used as the relational database.
3. Required business rules are implemented.
4. Inventory operations preserve consistency.
5. Sales order lifecycle is enforced.
6. REST API functionality is implemented.
7. Authentication and authorization are implemented.
8. Webhook processing is validated and idempotent.
9. Legacy data migration functionality is implemented.
10. Critical requirements have automated tests.
11. Docker-based development is functional.
12. CI executes the required automated checks.
13. Application errors are handled consistently.
14. Important business operations are logged.
15. Documentation is sufficient for another developer to run and understand the system.
16. Requirement-to-test traceability is documented.
17. A clean checkout can reproduce the development/test environment.

---

# 29. Implementation Principle

The project SHALL be developed incrementally.

No major implementation component should be added without a corresponding requirement or documented architectural reason.

The implementation process SHALL follow:

```text
Requirements
     |
     v
Architecture
     |
     v
Domain Model
     |
     v
Database Design
     |
     v
Implementation
     |
     v
Automated Tests
     |
     v
API / Integration
     |
     v
Docker
     |
     v
CI
     |
     v
Verification
```

The primary engineering objective is not feature count.

The primary objective is to demonstrate a maintainable, testable, reliable and production-oriented Django backend that models realistic business operations.

---

# 30. Requirement Verification Reconciliation

This section is the current requirement-verification reconciliation for
Milestones 2A through 2E.

It supersedes the historical Milestone 2B verification snapshot previously
recorded in this section. The current state is based on the audited repository
evidence recorded in `docs/milestones_2a_2e_reconciliation.md`.

## 30.1 Current verification status

The current reconciliation covers all 70 requirements.

| Status | Count |
|---|---:|
| VERIFIED | 30 |
| TESTED | 15 |
| IMPLEMENTED | 8 |
| PARTIAL | 2 |
| DESIGNED | 4 |
| PENDING | 11 |
| **Total** | **70** |

## 30.2 Audited requirement matrix

| Requirement | Area | Current state | Evidence / milestone | Remaining gap |
|---|---|---|---|---|
| ERP-REQ-001 | Customer Creation | TESTED | 2A/2B customer API tests | Full cross-domain verification not separately established |
| ERP-REQ-002 | Customer Retrieval | TESTED | 2B customer API tests | Same |
| ERP-REQ-003 | Customer Status | TESTED | 2B customer API tests | Same |
| ERP-REQ-004 | Product Creation | IMPLEMENTED | Product model | Dedicated creation test |
| ERP-REQ-005 | Unique SKU | TESTED | Model integrity tests | Full verification chain |
| ERP-REQ-006 | Product Validation | IMPLEMENTED | DB constraints | Dedicated validation tests |
| ERP-REQ-007 | Warehouse Management | TESTED | Model integrity tests | Full verification chain |
| ERP-REQ-008 | Stock Representation | TESTED | Model integrity tests | Full verification chain |
| ERP-REQ-009 | Stock Quantities | TESTED | Model integrity tests | Full verification chain |
| ERP-REQ-010 | Stock Validation | TESTED | Model integrity tests | Full verification chain |
| ERP-REQ-011 | Inventory Consistency | VERIFIED | Confirmation service + concurrency/atomicity tests | None within current scope |
| ERP-REQ-012 | Sales Order Creation | IMPLEMENTED | SalesOrder model | Dedicated creation test |
| ERP-REQ-013 | Sales Order Lines | TESTED | Order confirmation tests | Dedicated broader line API evidence |
| ERP-REQ-014 | Positive Quantities | TESTED | DB constraint test | Full verification chain |
| ERP-REQ-015 | Price Snapshot | IMPLEMENTED | SalesOrderLine model | Dedicated snapshot test |
| ERP-REQ-016 | Draft State | TESTED | Model integrity test | Full verification chain |
| ERP-REQ-017 | Order Confirmation | VERIFIED | Confirmation service + tests | None within current scope |
| ERP-REQ-018 | Stock Reservation | VERIFIED | Confirmation service + reservation/concurrency tests | None within current scope |
| ERP-REQ-019 | Insufficient Stock | VERIFIED | Confirmation service + atomicity tests | None within current scope |
| ERP-REQ-020 | Order Cancellation | VERIFIED | 2C lifecycle service + 19 lifecycle tests | No production workflow integration |
| ERP-REQ-021 | Shipment | VERIFIED | 2C shipment service + lifecycle tests | No carrier integration |
| ERP-REQ-022 | Completion | VERIFIED | 2C completion service + lifecycle tests | No external fulfillment integration |
| ERP-REQ-023 | Completed Order Immutability | VERIFIED | 2C lifecycle state enforcement/tests | No broader domain-wide immutability policy |
| ERP-REQ-024 | API Versioning | TESTED | `/api/v1/` routing + API tests | Dedicated versioning test/documentation not isolated |
| ERP-REQ-025 | Customer API | VERIFIED | 2B customer API tests | No material gap within implemented customer API scope |
| ERP-REQ-026 | Product API | VERIFIED | Product REST API implementation + dedicated product API tests | None within current scoped requirement |
| ERP-REQ-027 | Inventory API | VERIFIED | Inventory REST API implementation + dedicated inventory API tests | None within current scoped requirement |
| ERP-REQ-028 | Sales Order API | VERIFIED | 2D lifecycle API + tests | Broader CRUD/order API coverage may remain |
| ERP-REQ-029 | API Validation | TESTED | serializers + 2D/2E API error tests | No globally centralized unexpected-error contract |
| ERP-REQ-030 | Payment Webhook | VERIFIED | 2E webhook implementation/tests | No real payment provider |
| ERP-REQ-031 | Webhook Validation | VERIFIED | 2E serializer + invalid payload tests | No provider-specific schema/signature |
| ERP-REQ-032 | Webhook Idempotency | TESTED | unique event ID + duplicate webhook test | Concurrent first-delivery race remains untested; unique-key race handling is not production-grade distributed idempotency |
| ERP-REQ-033 | Unknown Order Webhook | VERIFIED | FAILED event + unknown-order test | No external retry/dead-letter policy |
| ERP-REQ-034 | Legacy Customer Import | VERIFIED | Customer import service + management command + 13 dedicated migration tests | Legacy customer CSV import is implemented and verified; no external ERP/Odoo source integration is claimed |
| ERP-REQ-035 | Migration Validation | VERIFIED | `_validate_row()` + invalid-record tests | Legacy records are validated before insertion and invalid rows are rejected with diagnostics |
| ERP-REQ-036 | Data Transformation | VERIFIED | `_transform_row()` + transformation test | Legacy CSV values are explicitly normalized into the application domain representation |
| ERP-REQ-037 | Migration Report | VERIFIED | `CustomerImportReport` + management-command output tests | Processed/imported/rejected counts and row/field/message validation diagnostics are reported |
| ERP-REQ-038 | Authentication | VERIFIED | DRF config + auth tests | Broader endpoint coverage |
| ERP-REQ-039 | User Roles | VERIFIED | Roles migration + permission tests | Broader endpoint matrix |
| ERP-REQ-040 | Permission Enforcement | TESTED | Customer API permission tests | Broader endpoint coverage |
| ERP-REQ-041 | Business Errors | VERIFIED | Order-domain business exceptions + centralized API mappings + business-error tests | Broader cross-domain business-error taxonomy can be expanded as new domains are added |
| ERP-REQ-042 | Consistent API Errors | VERIFIED | Centralized API error envelope for validation, business-rule and integration failures + API regression tests | Broader endpoint-specific error contract coverage can be expanded as new APIs are implemented |
| ERP-REQ-043 | Unexpected Errors | VERIFIED | Centralized DRF exception handler + safe 500 response + unexpected-error logging tests | Broader operational alerting/monitoring remains future scope |
| ERP-REQ-044 | Application Logging | VERIFIED | Structured application logging for order transitions, inventory changes, webhook processing, unexpected application errors, request failures and migration failures + M4 logging regression tests | Broader production observability, monitoring and alerting remain future scope |
| ERP-REQ-045 | Sensitive Information | PARTIAL | Configured application formatter excludes sensitive extra fields + regression test verifies passwords, authentication credentials, API secrets and database credentials are not rendered | No general-purpose sanitizer prevents sensitive values explicitly embedded in log messages |
| ERP-REQ-046 | Automated Testing | VERIFIED | Pytest suite + repeated full regressions | No material gap within current scope |
| ERP-REQ-047 | Business Logic Testing | VERIFIED | Confirmation, lifecycle and webhook tests | No formal coverage matrix |
| ERP-REQ-048 | Inventory Testing | VERIFIED | Inventory/model/confirmation/lifecycle tests including atomicity and concurrency | Reservation release is N/A under current cancellation contract; broader concurrent scenarios remain limited |
| ERP-REQ-049 | Order Lifecycle Testing | VERIFIED | 2C lifecycle tests | No production integration |
| ERP-REQ-050 | API Testing | VERIFIED | Customer, lifecycle and webhook API tests + full regressions | Endpoint-wide matrix can be expanded as future APIs are implemented |
| ERP-REQ-051 | Webhook Testing | VERIFIED | 2E 8-case suite | No provider/HIL testing |
| ERP-REQ-052 | Migration Testing | VERIFIED | 13 dedicated migration tests + full regression | Valid and invalid legacy customer records are covered by automated migration tests |
| ERP-REQ-053 | PostgreSQL | IMPLEMENTED | PostgreSQL 16 runtime verification | Broader DB verification |
| ERP-REQ-054 | Referential Integrity | IMPLEMENTED | Django relationships/migrations | Explicit schema verification |
| ERP-REQ-055 | Database Constraints | IMPLEMENTED | Model constraints/migrations | Consolidated constraint audit |
| ERP-REQ-056 | Environment Configuration | VERIFIED | `config/settings.py` reads environment variables for secret, debug, hosts and PostgreSQL settings | No material gap within current scope |
| ERP-REQ-057 | Secret Management | VERIFIED | Tracked `.env.example` contains placeholders; secrets are environment-configured | No real secret-management backend is claimed |
| ERP-REQ-058 | Environment Separation | DESIGNED | Configuration architecture | Explicit environment separation |
| ERP-REQ-059 | Containerized Development | VERIFIED | `Dockerfile`, `docker-compose.yml` + Docker verification | Dockerized Django application and PostgreSQL development environment build and start successfully; full regression passes in the container |
| ERP-REQ-060 | Database Container | VERIFIED | PostgreSQL Compose service + healthcheck | PostgreSQL container reaches healthy state and the Django web service starts against it |
| ERP-REQ-061 | Reproducible Environment | VERIFIED | `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `docs/development.md` + Docker verification | Documented local and Docker development procedures execute successfully, including startup, migrations, checks, compilation and tests |
| ERP-REQ-062 | CI Pipeline | VERIFIED | `.github/workflows/ci.yml` + successful GitHub Actions CI run | CI provisions PostgreSQL 16, installs dependencies, migrates, checks, compiles and executes pytest successfully |
| ERP-REQ-063 | CI Failure Handling | DESIGNED | CI architecture | Failure-path verification |
| ERP-REQ-064 | Architecture Documentation | VERIFIED | Substantive `docs/architecture.md` covering boundaries, components, transactions and design decisions | No material documentation gap within current scope |
| ERP-REQ-065 | Database Documentation | VERIFIED | Substantive `docs/database.md` covering entities, relationships, constraints, transactions and migrations | No material documentation gap within current scope |
| ERP-REQ-066 | API Documentation | VERIFIED | Substantive `docs/api.md` covering endpoints, schemas, validation, errors, lifecycle and integration design | Documentation contains stale pre-2D/2E implementation-status text and an obsolete webhook path; reconciliation update is required |
| ERP-REQ-067 | Development Documentation | VERIFIED | `docs/development.md` | Development guide documents setup, environment configuration, PostgreSQL, migrations, checks, tests, compilation, Docker workflow and management commands |
| ERP-REQ-068 | Version Control | VERIFIED | Git repository and milestone history | No material gap within current scope |
| ERP-REQ-069 | Meaningful Commits | VERIFIED | Meaningful milestone commits with purpose-specific messages | No material gap within current scope |
| ERP-REQ-070 | Reproducibility | PENDING | Git, migrations, `pyproject.toml`, `.env.example` and PostgreSQL Compose infrastructure | Dockerized build/startup, PostgreSQL initialization, migrations, Django checks, compilation, and full test execution are reproducible in the current environment; a fresh clean-checkout/end-to-end reproduction has not yet been independently demonstrated |

## 30.3 Milestone scope and regression evidence

The reconciliation covers the implemented scope of Milestones 2A through 2E:

- Milestone 2A: domain and order workflow foundation.
- Milestone 2B: REST API foundation and API verification.
- Milestone 2C: sales-order lifecycle services.
- Milestone 2D: sales-order lifecycle REST API.
- Milestone 2E: external payment webhook integration foundation.

Current Milestone 2E baseline:

- Git commit: `0fb41d2`
- Dedicated payment webhook suite: 8 passed.
- Full regression: 157 passed.
- Django system check passed.
- Python compilation checks passed.
- `git diff --check` clean.

The reconciliation distinguishes implemented behavior from independently tested
or verified behavior. Requirements marked PARTIAL or PENDING retain explicit
remaining gaps and are not treated as completed implementation scope.

## 30.4 Known remaining cross-cutting gaps

The current audit identifies the following cross-cutting gaps that remain
outside the completed 2A-2E verification baseline:

- Unified cross-domain business-error taxonomy.
- Unified API error envelope across validation, business-rule, and integration
  failures.
- Global unexpected-exception handling.
- Structured application logging.
- Explicit sensitive-information protection and verification at
  logging/application boundaries.

These gaps are intentionally retained as requirements work rather than being
implicitly marked complete by the existence of individual endpoint
implementations.

## 30.5 Reconciliation authority and traceability

`docs/milestones_2a_2e_reconciliation.md` is the audited 2A-2E reconciliation
source used to establish the current status recorded here.

`docs/traceability.md` is intentionally not synchronized by this update.
Traceability synchronization is a separate controlled documentation step to be
performed after this requirements reconciliation has passed its diff and
consistency checks.

The current regression and implementation state documented here must therefore
be interpreted as the Milestone 2A-2E baseline only; it does not constitute
Milestone 2F scope or implementation.
