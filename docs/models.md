# Django ERP Operations Platform — Model Implementation Specification

**Document:** Model Implementation Specification
**Project:** Django ERP Operations Platform
**Version:** 1.0
**Status:** Approved
**Requirements Baseline:** `14db353`
**Database Design Baseline:** `b1bfb88`
**Last Updated:** 2026-09-02

---

# 1. Purpose

This document defines the Django ORM implementation contract derived from the approved database design.

It is the implementation bridge between:

```text
docs/database.md
        ↓
docs/models.md
        ↓
apps/*/models.py
```

The Django models must implement this specification without introducing schema behavior that is not defined by the approved database design.

Business workflows remain outside the models unless explicitly identified as model-level invariants.

---

# 2. Model-to-Table Mapping

| Django app     | Django model     | Database table                |
| -------------- | ---------------- | ----------------------------- |
| `customers`    | `Customer`       | `customers`                   |
| `products`     | `Product`        | `products`                    |
| `warehouses`   | `Warehouse`      | `warehouses`                  |
| `inventory`    | `StockItem`      | `inventory_stock_items`       |
| `orders`       | `SalesOrder`     | `orders`                      |
| `orders`       | `SalesOrderLine` | `order_lines`                 |
| `integrations` | `ExternalEvent`  | `integration_external_events` |

All domain models use UUID primary keys.

---

# 3. Common Model Conventions

## 3.1 Primary Keys

Every domain model uses:

```text
UUID primary key
```

The Django implementation should use:

```text
UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
```

UUIDs provide technical identity.

They do not replace business uniqueness constraints.

---

## 3.2 Timestamps

Models requiring timestamps use:

```text
created_at
modified_at
```

Both are non-null timezone-aware datetime fields.

The implementation should use UTC-aware Django datetime handling.

---

## 3.3 Table Names

Explicit database table names must preserve the approved schema:

```text
Customer        → customers
Product         → products
Warehouse       → warehouses
StockItem       → inventory_stock_items
SalesOrder      → orders
SalesOrderLine  → order_lines
ExternalEvent   → integration_external_events
```

---

# 4. Customer Model

## 4.1 Identity

```text
Model: Customer
Table: customers
App: customers
```

## 4.2 Fields

| Field         | Django type          | Null | Default       | Constraints            |
| ------------- | -------------------- | ---: | ------------- | ---------------------- |
| `id`          | `UUIDField`          |   No | `uuid.uuid4`  | Primary key            |
| `name`        | `CharField(max_length=255)` |   No | —             | Non-empty              |
| `email`       | `CharField(max_length=254)` |  Yes | —             | Application validation |
| `phone`       | `CharField(max_length=32)`  |  Yes | —             | Application validation |
| `active`      | `BooleanField`       |   No | `True`        | —                      |
| `created_at`  | `DateTimeField`      |   No | Creation time | —                      |
| `modified_at` | `DateTimeField`      |   No | Update time   | —                      |

## 4.3 Database Constraints

```text
CHECK(name <> '')
```

No unique constraint is required for:

```text
email
phone
```

The database design specifies email and phone as nullable contact fields. Their business-level validation belongs to the application layer.

## 4.4 Relationships

`SalesOrder.customer` references `Customer` with:

```text
on_delete=PROTECT
```

## 4.5 Business Invariants

* Inactive customers cannot create new orders.
* Existing historical orders remain associated with the customer.
* Customer deletion must not invalidate historical orders.

These are application/domain invariants and are separate from the database-level `name <> ''` constraint.

## 4.6 Requirements

```text
ERP-REQ-001
ERP-REQ-002
ERP-REQ-003
ERP-REQ-054
ERP-REQ-055
```

---

# 5. Product Model

## 5.1 Identity

```text
Model: Product
Table: products
App: products
```

## 5.2 Fields

| Field         | Django type          | Null | Default       | Constraints                                 |
| ------------- | -------------------- | ---: | ------------- | ------------------------------------------- |
| `id`          | `UUIDField`          |   No | `uuid.uuid4`  | Primary key                                 |
| `sku`         | `CharField(max_length=64)`  |   No | —             | Unique, non-empty                           |
| `name`        | `CharField(max_length=255)` |   No | —             | Non-empty                                   |
| `description` | `TextField`          |  Yes | —             | —                                           |
| `unit_price`  | `DecimalField`       |   No | —             | `max_digits=12`, `decimal_places=2`, `>= 0` |
| `active`      | `BooleanField`       |   No | `True`        | —                                           |
| `created_at`  | `DateTimeField`      |   No | Creation time | —                                           |
| `modified_at` | `DateTimeField`      |   No | Update time   | —                                           |

## 5.3 Database Constraints

```text
UNIQUE(sku)

CHECK(sku <> '')
CHECK(name <> '')
CHECK(unit_price >= 0)
```

## 5.4 Relationships

`SalesOrderLine.product` references `Product` with:

```text
on_delete=PROTECT
```

`StockItem.product` references `Product` with:

```text
on_delete=PROTECT
```

## 5.5 Business Invariants

* SKU is unique.
* SKU cannot be empty.
* Product name cannot be empty.
* Unit price cannot be negative.
* Inactive products cannot be used for new order lines.
* Historical order lines retain their own price snapshot.

## 5.6 Requirements

```text
ERP-REQ-004
ERP-REQ-005
ERP-REQ-006
ERP-REQ-015
ERP-REQ-055
```

---

# 6. Warehouse Model

## 6.1 Identity

```text
Model: Warehouse
Table: warehouses
App: warehouses
```

## 6.2 Fields

| Field         | Django type          | Null | Default       | Constraints       |
| ------------- | -------------------- | ---: | ------------- | ----------------- |
| `id`          | `UUIDField`          |   No | `uuid.uuid4`  | Primary key       |
| `code`        | `CharField(max_length=64)`  |   No | —             | Unique, non-empty |
| `name`        | `CharField(max_length=255)` |   No | —             | —                 |
| `location`    | `CharField(max_length=255)` |  Yes | —             | —                 |
| `active`      | `BooleanField`       |   No | `True`        | —                 |
| `created_at`  | `DateTimeField`      |   No | Creation time | —                 |
| `modified_at` | `DateTimeField`      |   No | Update time   | —                 |

## 6.3 Database Constraints

```text
UNIQUE(code)

CHECK(code <> '')
```

## 6.4 Relationships

`StockItem.warehouse` references `Warehouse` with:

```text
on_delete=PROTECT
```

## 6.5 Business Invariants

* Warehouse code is unique.
* Warehouse code cannot be empty.
* Inactive warehouses cannot accept new inventory operations.

## 6.6 Requirements

```text
ERP-REQ-007
ERP-REQ-055
```

---

# 7. StockItem Model

## 7.1 Identity

```text
Model: StockItem
Table: inventory_stock_items
App: inventory
```

## 7.2 Fields

| Field               | Django type             | Null | Default       | Constraints |
| ------------------- | ----------------------- | ---: | ------------- | ----------- |
| `id`                | `UUIDField`             |   No | `uuid.uuid4`  | Primary key |
| `product`           | `ForeignKey(Product)`   |   No | —             | `PROTECT`   |
| `warehouse`         | `ForeignKey(Warehouse)` |   No | —             | `PROTECT`   |
| `quantity`          | `IntegerField`          |   No | —             | `>= 0`      |
| `reserved_quantity` | `IntegerField`          |   No | —             | `>= 0`      |
| `created_at`        | `DateTimeField`         |   No | Creation time | —           |
| `modified_at`       | `DateTimeField`         |   No | Update time   | —           |

## 7.3 Database Constraints

```text
UNIQUE(product, warehouse)

CHECK(quantity >= 0)
CHECK(reserved_quantity >= 0)
CHECK(reserved_quantity <= quantity)
```

## 7.4 Available Quantity

`available_quantity` is not a stored database field.

It is derived as:

```text
available_quantity = quantity - reserved_quantity
```

The implementation may expose this as a read-only model property or equivalent domain-level calculation.

A separate mutable database column for `available_quantity` must not be introduced.

## 7.5 Critical Integrity Boundary

Inventory updates are critical business operations.

The implementation must use:

```text
transaction.atomic()
```

together with:

```text
select_for_update()
```

where required by the approved transaction strategy.

The model itself must not be treated as sufficient protection against concurrent inventory updates.

## 7.6 Business Invariants

```text
quantity >= 0
reserved_quantity >= 0
reserved_quantity <= quantity
available_quantity >= 0
```

## 7.7 Requirements

```text
ERP-REQ-008
ERP-REQ-009
ERP-REQ-010
ERP-REQ-011
ERP-REQ-048
ERP-REQ-055
```

---

# 8. SalesOrder Model

## 8.1 Identity

```text
Model: SalesOrder
Table: orders
App: orders
```

## 8.2 Fields

| Field         | Django type                          | Null | Default       | Constraints           |
| ------------- | ------------------------------------ | ---: | ------------- | --------------------- |
| `id`          | `UUIDField`                          |   No | `uuid.uuid4`  | Primary key           |
| `customer`    | `ForeignKey(Customer)`               |   No | —             | `PROTECT`             |
| `status`      | `CharField(max_length=32, choices=...)` |   No | `DRAFT`       | Valid lifecycle state |
| `created_at`  | `DateTimeField`                      |   No | Creation time | —                     |
| `modified_at` | `DateTimeField`                      |   No | Update time   | —                     |

## 8.3 Status Choices

```text
DRAFT
CONFIRMED
SHIPPED
COMPLETED
CANCELLED
```

New orders start in:

```text
DRAFT
```

This is an application/model initialization default; it is **not** a PostgreSQL column `DEFAULT`. Lifecycle transitions remain controlled by application services.

## 8.4 Database Constraint

```text
CHECK(
    status IN (
        'DRAFT',
        'CONFIRMED',
        'SHIPPED',
        'COMPLETED',
        'CANCELLED'
    )
)
```

Django `TextChoices` provides application-level representation.

The database `CHECK` provides persistence-level protection against unknown values.

## 8.5 Relationships

```text
customer → Customer
on_delete=PROTECT
```

Order lines reference the order using:

```text
SalesOrderLine.order
on_delete=CASCADE
```

## 8.6 Lifecycle

Valid transitions:

```text
DRAFT      → CONFIRMED
DRAFT      → CANCELLED
CONFIRMED  → SHIPPED
SHIPPED    → COMPLETED
```

`COMPLETED` and `CANCELLED` are terminal states.

The following transitions are invalid:

```text
CONFIRMED → DRAFT
SHIPPED   → DRAFT
COMPLETED → any other state
CANCELLED → any other state
```

Lifecycle transitions are application/service responsibilities.

They must not be implemented as unrestricted direct field assignments.

## 8.7 Confirmation Invariants

An order can be confirmed only when:

```text
customer is active
order contains at least one line
all line quantities are valid
all required products are valid
sufficient inventory is available
inventory reservation succeeds atomically
```

The order must not become `CONFIRMED` unless the corresponding inventory reservation succeeds.

## 8.8 Requirements

```text
ERP-REQ-012
ERP-REQ-016
ERP-REQ-017
ERP-REQ-018
ERP-REQ-019
ERP-REQ-020
ERP-REQ-021
ERP-REQ-022
ERP-REQ-023
ERP-REQ-028
ERP-REQ-041
ERP-REQ-055
```

---

# 9. SalesOrderLine Model

## 9.1 Identity

```text
Model: SalesOrderLine
Table: order_lines
App: orders
```

## 9.2 Fields

| Field        | Django type              | Null | Default       | Constraints                                 |
| ------------ | ------------------------ | ---: | ------------- | ------------------------------------------- |
| `id`         | `UUIDField`              |   No | `uuid.uuid4`  | Primary key                                 |
| `order`      | `ForeignKey(SalesOrder)` |   No | —             | `CASCADE`                                   |
| `product`    | `ForeignKey(Product)`    |   No | —             | `PROTECT`                                   |
| `quantity`   | `IntegerField`           |   No | —             | `> 0`                                       |
| `unit_price` | `DecimalField`           |   No | —             | `max_digits=12`, `decimal_places=2`, `>= 0` |
| `created_at` | `DateTimeField`          |   No | Creation time | —                                           |

## 9.3 Database Constraints

```text
CHECK(quantity > 0)
CHECK(unit_price >= 0)
```

## 9.4 Price Snapshot

`unit_price` is the historical price snapshot captured for the order line.

It must not be derived dynamically from:

```text
Product.unit_price
```

Changing a product's current catalog price must not modify existing order lines.

## 9.5 Business Invariants

* Order-line quantity must be positive.
* Order-line unit price cannot be negative.
* An order must contain at least one line before confirmation.
* Inactive products cannot be used for new order lines.
* Product identity is preserved through the foreign-key relationship.

The minimum-line requirement is an application/service invariant rather than a simple row-level database constraint.

## 9.6 Requirements

```text
ERP-REQ-013
ERP-REQ-014
ERP-REQ-015
ERP-REQ-017
ERP-REQ-055
```

---

# 10. ExternalEvent Model

## 10.1 Identity

```text
Model: ExternalEvent
Table: integration_external_events
App: integrations
```

## 10.2 Fields

| Field               | Django type                          | Null | Default      | Constraints                                 |
| ------------------- | ------------------------------------ | ---: | ------------ | ------------------------------------------- |
| `id`                | `UUIDField`                          |   No | `uuid.uuid4` | Primary key                                 |
| `external_event_id` | `CharField(max_length=255)`          |   No | —            | Unique                                      |
| `event_type`        | `CharField(max_length=64)`           |   No | —            | Application validation                      |
| `order`             | `ForeignKey(SalesOrder)`             |  Yes | —            | `PROTECT`                                   |
| `payment_amount`    | `DecimalField`                       |  Yes | —            | `max_digits=12`, `decimal_places=2`, `>= 0` |
| `processing_status` | `CharField(max_length=32, choices=...)` |   No | `RECEIVED`   | Valid processing state                      |
| `received_at`       | `DateTimeField`                      |   No | —            | —                                           |
| `processed_at`      | `DateTimeField`                      |  Yes | —            | —                                           |
| `error_message`     | `TextField`                          |  Yes | —            | Sanitized error text                        |

## 10.3 Processing Status

```text
RECEIVED
PROCESSED
FAILED
```

The initial processing status is `RECEIVED`.

This is an application/model initialization default; it is **not** a PostgreSQL column `DEFAULT`. Processing state transitions remain controlled by the integration application service.

## 10.4 Database Constraints

```text
UNIQUE(external_event_id)

CHECK(
    processing_status IN (
        'RECEIVED',
        'PROCESSED',
        'FAILED'
    )
)

CHECK(
    payment_amount IS NULL
    OR payment_amount >= 0
)
```

## 10.5 Relationships

```text
order → SalesOrder
on_delete=PROTECT
```

The `order` relationship is nullable because an incoming external event may be rejected when its referenced order does not exist.

## 10.6 Idempotency

`external_event_id` is the database-level uniqueness boundary for webhook idempotency.

Repeated processing of the same external event must not create duplicate event records or duplicate business effects.

Idempotency behavior belongs to the integration/application service layer.

## 10.7 Requirements

```text
ERP-REQ-030
ERP-REQ-031
ERP-REQ-032
ERP-REQ-033
ERP-REQ-041
ERP-REQ-055
```

---

# 11. Relationship Matrix

| From                     | To           | Relationship          | `on_delete` |
| ------------------------ | ------------ | --------------------- | ----------- |
| `SalesOrder.customer`    | `Customer`   | Many-to-one           | `PROTECT`   |
| `SalesOrderLine.order`   | `SalesOrder` | Many-to-one           | `CASCADE`   |
| `SalesOrderLine.product` | `Product`    | Many-to-one           | `PROTECT`   |
| `StockItem.product`      | `Product`    | Many-to-one           | `PROTECT`   |
| `StockItem.warehouse`    | `Warehouse`  | Many-to-one           | `PROTECT`   |
| `ExternalEvent.order`    | `SalesOrder` | Many-to-one, nullable | `PROTECT`   |

---

# 12. Constraint Matrix

| Model            | Constraint                      | Django implementation              |
| ---------------- | ------------------------------- | ---------------------------------- |
| `Customer`       | `name <> ''`                    | `CheckConstraint`                  |
| `Product`        | `sku` unique                    | `UniqueConstraint` / `unique=True` |
| `Product`        | `sku <> ''`                     | `CheckConstraint`                  |
| `Product`        | `name <> ''`                    | `CheckConstraint`                  |
| `Product`        | `unit_price >= 0`               | `CheckConstraint`                  |
| `Warehouse`      | `code` unique                   | `UniqueConstraint` / `unique=True` |
| `Warehouse`      | `code <> ''`                    | `CheckConstraint`                  |
| `StockItem`      | `(product, warehouse)` unique   | `UniqueConstraint`                 |
| `StockItem`      | `quantity >= 0`                 | `CheckConstraint`                  |
| `StockItem`      | `reserved_quantity >= 0`        | `CheckConstraint`                  |
| `StockItem`      | `reserved_quantity <= quantity` | `CheckConstraint`                  |
| `SalesOrder`     | valid status                    | `CheckConstraint`                  |
| `SalesOrderLine` | `quantity > 0`                  | `CheckConstraint`                  |
| `SalesOrderLine` | `unit_price >= 0`               | `CheckConstraint`                  |
| `ExternalEvent`  | `external_event_id` unique      | `UniqueConstraint` / `unique=True` |
| `ExternalEvent`  | valid processing status         | `CheckConstraint`                  |
| `ExternalEvent`  | payment amount non-negative     | `CheckConstraint`                  |

---

# 13. Database Constraints vs Application Invariants

## 13.1 Database-Level Constraints

The following must be enforced at database level:

```text
UUID primary keys
foreign-key integrity
unique SKU
unique warehouse code
unique product/warehouse stock item
unique external event ID
non-empty required identity strings
non-negative monetary values
non-negative inventory quantities
reserved quantity <= quantity
valid order statuses
valid external-event processing statuses
```

## 13.2 Application/Service-Level Invariants

The following require business logic:

```text
inactive customer cannot create order
inactive product cannot be added to new order
inactive warehouse cannot accept new inventory operations
order must contain at least one line before confirmation
confirmation requires sufficient available stock
confirmation reserves stock atomically
insufficient stock leaves order in DRAFT
only valid lifecycle transitions are permitted
shipment consumes reserved stock
completion does not modify inventory
webhook processing is idempotent
unexpected failures are translated to controlled errors
```

Models must not be treated as a replacement for application services.

---

# 14. Inventory Transaction Contract

Inventory consistency is a critical domain boundary.

## 14.1 Confirmation

Order confirmation must conceptually execute:

```text
BEGIN TRANSACTION

validate order
validate customer
validate products

LOCK required StockItem rows

re-check available quantity

reserve required inventory

set order status = CONFIRMED

COMMIT
```

Failure must result in:

```text
ROLLBACK
```

The system must not allow:

```text
order = CONFIRMED
inventory = not reserved
```

or:

```text
inventory = reserved
order = DRAFT
```

as a committed final state.

---

## 14.2 Shipment

Shipment must conceptually execute:

```text
BEGIN TRANSACTION

validate order state

LOCK required StockItem rows

verify reservation

reduce physical quantity
reduce reserved quantity

set order status = SHIPPED

COMMIT
```

Example:

```text
Before:
quantity = 100
reserved_quantity = 30
available_quantity = 70

After shipment:
quantity = 70
reserved_quantity = 0
available_quantity = 70
```

`reserved_quantity` represents active reservations, not historical shipped quantity.

---

# 15. Index Strategy

Indexes must support documented access patterns without introducing unnecessary indexes.

The Django implementation must preserve the index strategy defined by the approved `docs/database.md`.

Expected access patterns include:

```text
Customer.active
Product.active
SalesOrder.customer
SalesOrder.status
SalesOrderLine.order
ExternalEvent.external_event_id
```

Unique constraints may provide the required unique indexes automatically.

No additional indexes should be introduced solely for convenience without updating the database design specification.

---

# 16. Model Responsibilities

Models are responsible for:

* representing persistent domain state;
* declaring relationships;
* declaring field-level persistence rules;
* declaring database constraints;
* declaring indexes;
* exposing derived read-only values where appropriate.

Models are not the primary location for:

* order confirmation workflows;
* inventory reservation workflows;
* shipment workflows;
* webhook processing;
* cross-aggregate transactions;
* permission workflows.

Those responsibilities belong to the application/domain service layer.

---

# 17. Django ORM Design Rules

## 17.1 Foreign Keys

Foreign keys must explicitly define the approved `on_delete` behavior.

Do not use `CASCADE` by default where the database design specifies `PROTECT`.

---

## 17.2 Monetary Values

Monetary values must use decimal storage:

```text
DecimalField
max_digits = 12
decimal_places = 2
```

Floating-point fields must not be used for prices or payment amounts.

---

## 17.3 Mutable Derived Values

`available_quantity` must not be stored as a second mutable inventory quantity.

It is derived from:

```text
quantity - reserved_quantity
```

---

## 17.4 Status Fields

Status values must use explicit Django choices corresponding exactly to the approved database values.

Order statuses:

```text
DRAFT
CONFIRMED
SHIPPED
COMPLETED
CANCELLED
```

External event statuses:

```text
RECEIVED
PROCESSED
FAILED
```

The database must independently reject unknown status values through `CHECK` constraints.

---

## 17.5 Business Methods

Small invariant-preserving model methods may be used where appropriate.

However, multi-model workflows and critical transactions must remain in application/domain services.

The following must not be implemented as unrestricted direct assignments:

```text
order.status = ...
```

for lifecycle transitions.

Instead, lifecycle operations must pass through the defined business workflow.

---

# 18. Migration Requirements

The initial Django migration must create the schema represented by this specification.

Expected migration structure:

```text
0001_initial
    ├── customers
    ├── products
    ├── warehouses
    ├── inventory_stock_items
    ├── orders
    ├── order_lines
    └── integration_external_events
```

The migration must preserve:

* UUID primary keys;
* foreign-key relationships;
* `PROTECT` / `CASCADE` policies;
* unique constraints;
* check constraints;
* indexes;
* decimal precision;
* nullable fields;
* timestamp semantics.

Migration files are generated implementation artifacts and must be reviewed against `docs/database.md` and `docs/models.md`.

---

# 19. Verification Strategy

The model implementation must be verified at multiple levels.

## 19.1 Static Model Audit

Verify:

```text
database table names
field names
field types
nullability
defaults
relationships
on_delete
choices
constraints
indexes
```

## 19.2 Django Checks

Run:

```text
python manage.py check
```

The command must complete without model configuration errors.

## 19.3 Migration Verification

Run:

```text
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

Generated migrations must be inspected rather than accepted blindly.

## 19.4 PostgreSQL Verification

The resulting PostgreSQL schema must be checked against the approved database design.

Verification must include:

```text
tables
columns
primary keys
foreign keys
unique constraints
check constraints
indexes
```

## 19.5 Automated Tests

Tests must verify critical constraints and model behavior before application-service integration is considered complete.

---

# 20. Traceability

| Requirement area              | Models involved     |
| ----------------------------- | ------------------- |
| Customer management           | `Customer`          |
| Product management            | `Product`           |
| Warehouse management          | `Warehouse`         |
| Inventory representation      | `StockItem`         |
| Order lifecycle               | `SalesOrder`        |
| Order lines / price snapshots | `SalesOrderLine`    |
| Webhook idempotency           | `ExternalEvent`     |
| Referential integrity         | All related models  |
| Database constraints          | All affected models |

Detailed requirement-level verification remains governed by:

```text
docs/requirements.md
```

The complete traceability chain is:

```text
Requirement
    ↓
Architecture
    ↓
Database Design
    ↓
Model Specification
    ↓
Django Models
    ↓
Migration
    ↓
Automated Tests
    ↓
Verification Evidence
```

---

# 21. Explicitly Deferred

The model layer must not introduce:

```text
accounting ledger
invoices
tax entities
payment settlement entities
shipment tracking
partial shipments
returns
stock adjustment ledger
reservation expiration
supplier management
purchase orders
multi-currency
product variants
batch/lot tracking
serial-number tracking
soft-delete framework
database audit triggers
```

These require explicit requirements before implementation.

---

# 22. Model Implementation Status

Current status:

```text
Model Implementation Specification: APPROVED
```

Approval checklist:

```text
[x] Customer mapping audited
[x] Product mapping audited
[x] Warehouse mapping audited
[x] StockItem mapping audited
[x] SalesOrder mapping audited
[x] SalesOrderLine mapping audited
[x] ExternalEvent mapping audited
[x] Foreign-key policies audited
[x] Database constraints audited
[x] Index strategy audited
[x] Requirement traceability audited
[x] Migration expectations audited
```

The model specification is approved for Django model implementation.

---

# 23. Baseline References

```text
Requirements:
docs/requirements.md
Baseline commit: 14db353

Architecture:
docs/architecture.md

Database Design:
docs/database.md
Approval commit: b1bfb88
```

This specification is derived from the approved database design and must remain consistent with it.

Any model implementation decision that changes the database contract must first be reflected in the appropriate design specification and reviewed before implementation.
