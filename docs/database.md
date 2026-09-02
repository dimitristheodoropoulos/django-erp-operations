# Django ERP Operations Platform — Database Design Specification

**Document:** Database Design Specification
**Project:** Django ERP Operations Platform
**Version:** 1.0
**Status:** Approved
**Requirements Baseline:** `14db353`
**Architecture Baseline:** `docs/architecture.md`
**Last Updated:** 2026-09-02

---

# 1. Database Goals

The database design must provide:

* strong relational integrity;
* explicit ownership of domain data;
* uniqueness where required by the business domain;
* non-negative inventory quantities;
* protection against invalid inventory states;
* referential integrity between customers, products, warehouses, orders and inventory;
* idempotency support for external webhook events;
* transactional consistency for critical business operations;
* concurrency-safe inventory updates;
* deterministic and reproducible migrations;
* PostgreSQL as the primary relational database.

The database is treated as an **integrity boundary**, not merely as persistent storage.

Application-level validation remains necessary, but critical invariants must also be enforced at database level wherever practical.

---

# 2. Database Technology

## 2.1 Primary Database

The primary database is:

**PostgreSQL**

PostgreSQL is required by:

* ERP-REQ-053 — PostgreSQL primary relational database
* ERP-REQ-054 — referential integrity
* ERP-REQ-055 — database constraints

SQLite is not considered the production database.

A lightweight SQLite configuration may be used only if explicitly introduced for a non-production development scenario and must not weaken the PostgreSQL verification path.

---

# 3. Database Schema Overview

The initial schema consists of the following logical tables:

```text
customers
products
warehouses
inventory_stock_items
orders
order_lines
integration_external_events
accounts / Django authentication tables
```

The core domain relationship is:

```text
Customer
   |
   | 1
   |
   | *
SalesOrder
   |
   | 1
   |
   | *
SalesOrderLine
   |
   | *
   |
   | 1
Product
   |
   | 1
   |
   | *
StockItem
   |
   | *
   |
   | 1
Warehouse
```

External integration events relate to orders where the external event contains an order reference:

```text
ExternalEvent
      |
      | 0..*
      |
      v
   SalesOrder
```

---

# 4. Table Design

## 4.1 Customer

Logical table:

```text
customers
```

Purpose:

Stores customer identity, contact information and operational status.

Fields:

| Field       | Type                     | Nullable | Constraints                    |
| ----------- | ------------------------ | -------: | ------------------------------ |
| id          | UUID                     |       No | Primary key                    |
| name        | VARCHAR(255)             |       No | Non-empty                      |
| email       | VARCHAR(254)             |      Yes | Validated at application level |
| phone       | VARCHAR(32)              |      Yes | Validated at application level |
| active      | BOOLEAN                  |       No | Default `true`                 |
| created_at  | TIMESTAMP WITH TIME ZONE |       No | Set on creation                |
| modified_at | TIMESTAMP WITH TIME ZONE |       No | Updated on modification        |

Business rules:

* A customer may be active or inactive.
* Inactive customers cannot create new orders.
* Existing historical orders remain associated with the customer.
* Customer deletion must not invalidate historical orders.

Relevant requirements:

* ERP-REQ-001
* ERP-REQ-002
* ERP-REQ-003
* ERP-REQ-054

---

## 4.2 Product

Logical table:

```text
products
```

Purpose:

Stores products and their current catalog information.

Fields:

| Field       | Type                     | Nullable | Constraints             |
| ----------- | ------------------------ | -------: | ----------------------- |
| id          | UUID                     |       No | Primary key             |
| sku         | VARCHAR(64)              |       No | Unique, non-empty       |
| name        | VARCHAR(255)             |       No | Non-empty               |
| description | TEXT                     |      Yes |                         |
| unit_price  | NUMERIC(12,2)            |       No | `>= 0`                  |
| active      | BOOLEAN                  |       No | Default `true`          |
| created_at  | TIMESTAMP WITH TIME ZONE |       No | Set on creation         |
| modified_at | TIMESTAMP WITH TIME ZONE |       No | Updated on modification |

### Money representation

`unit_price` uses:

```text
NUMERIC(12,2)
```

This provides exact decimal representation and avoids floating-point monetary calculations.

The application must use decimal arithmetic for monetary values.

Business rules:

* SKU is unique.
* SKU cannot be empty.
* Name cannot be empty.
* Unit price cannot be negative.
* Inactive products cannot be used for new order lines.
* Historical order lines retain their own unit-price snapshot.

Relevant requirements:

* ERP-REQ-004
* ERP-REQ-005
* ERP-REQ-006
* ERP-REQ-015
* ERP-REQ-055

---

## 4.3 Warehouse

Logical table:

```text
warehouses
```

Purpose:

Stores warehouse identity and operational status.

Fields:

| Field       | Type                     | Nullable | Constraints             |
| ----------- | ------------------------ | -------: | ----------------------- |
| id          | UUID                     |       No | Primary key             |
| code        | VARCHAR(64)              |       No | Unique, non-empty       |
| name        | VARCHAR(255)             |       No | Non-empty               |
| location    | VARCHAR(255)             |      Yes |                         |
| active      | BOOLEAN                  |       No | Default `true`          |
| created_at  | TIMESTAMP WITH TIME ZONE |       No | Set on creation         |
| modified_at | TIMESTAMP WITH TIME ZONE |       No | Updated on modification |

Business rules:

* Warehouse code is unique.
* Warehouse code cannot be empty.
* Inactive warehouses cannot accept new inventory operations.

Relevant requirements:

* ERP-REQ-007
* ERP-REQ-055

---

# 5. Inventory Schema

## 5.1 StockItem

Logical table:

```text
inventory_stock_items
```

Purpose:

Represents the stock of one product in one warehouse.

Fields:

| Field             | Type                     | Nullable | Constraints        |
| ----------------- | ------------------------ | -------: | ------------------ |
| id                | UUID                     |       No | Primary key        |
| product_id        | UUID                     |       No | FK → products.id   |
| warehouse_id      | UUID                     |       No | FK → warehouses.id |
| quantity          | INTEGER                  |       No | `>= 0`             |
| reserved_quantity | INTEGER                  |       No | `>= 0`             |
| created_at        | TIMESTAMP WITH TIME ZONE |       No |                    |
| modified_at       | TIMESTAMP WITH TIME ZONE |       No |                    |

The logical available quantity is:

```text
available_quantity = quantity - reserved_quantity
```

`available_quantity` does not need to be stored as an independently mutable column.

This prevents duplicated state.

---

## 5.2 Stock Uniqueness

There must be exactly one inventory record for a given:

```text
product + warehouse
```

Therefore:

```text
UNIQUE(product_id, warehouse_id)
```

is required.

This implements ERP-REQ-008.

---

## 5.3 Inventory Constraints

The following database constraints are required:

```text
quantity >= 0
reserved_quantity >= 0
reserved_quantity <= quantity
```

The third constraint guarantees:

```text
available_quantity >= 0
```

Therefore:

```text
available_quantity = quantity - reserved_quantity
```

can never become negative while database constraints are respected.

These constraints implement:

* ERP-REQ-009
* ERP-REQ-010
* ERP-REQ-055

---

# 6. Sales Order Schema

## 6.1 SalesOrder

Logical table:

```text
orders
```

Purpose:

Stores the order header and lifecycle state.

Fields:

| Field       | Type                       | Nullable | Constraints           |
| ----------- | -------------------------- | -------: | --------------------- |
| id          | UUID                       |       No | Primary key           |
| customer_id | UUID                       |       No | FK → customers.id     |
| status      | VARCHAR(32)                |       No | Valid lifecycle state |
| created_at  | TIMESTAMP WITH TIME ZONE   |       No |                       |
| modified_at | TIMESTAMP WITH TIME ZONE   |       No |                       |

Order statuses:

```text
DRAFT
CONFIRMED
SHIPPED
COMPLETED
CANCELLED
```

The database must reject unknown status values.

The implementation may use Django `TextChoices` or an equivalent explicit representation, with database-level enforcement where practical.

The initial order status is `DRAFT`.

This is an application/model initialization default rather than a required
PostgreSQL column `DEFAULT`. Order lifecycle transitions remain controlled by
application services.

---

## 6.2 Order Reference

The primary order identifier is the UUID `id`.

For external integrations, the system must provide a stable order reference that can be safely represented in webhook payloads.

The initial implementation should use the UUID as the canonical external order reference unless an explicit human-readable order-number requirement is introduced later.

No separate sequential order number is required by the current requirements baseline.

---

# 7. Sales Order Line Schema

Logical table:

```text
order_lines
```

Purpose:

Stores the products and quantities belonging to an order.

Fields:

| Field      | Type                     | Nullable | Constraints      |
| ---------- | ------------------------ | -------: | ---------------- |
| id         | UUID                     |       No | Primary key      |
| order_id   | UUID                     |       No | FK → orders.id   |
| product_id | UUID                     |       No | FK → products.id |
| quantity   | INTEGER                  |       No | `> 0`            |
| unit_price | NUMERIC(12,2)            |       No | `>= 0`           |
| created_at | TIMESTAMP WITH TIME ZONE |       No |                  |

The `unit_price` is the **price snapshot at order-line creation**.

It is intentionally independent from:

```text
products.unit_price
```

Therefore, changing the current product price must not modify an existing order line.

This implements ERP-REQ-013, ERP-REQ-014 and ERP-REQ-015.

---

# 8. Order Line Constraints

The database must enforce:

```text
quantity > 0
unit_price >= 0
```

The order line must reference an existing:

```text
orders
products
```

through foreign keys.

An order must contain at least one order line before confirmation.

The "at least one line before confirmation" rule is primarily a business/application invariant because the database cannot enforce it with a simple row-level check constraint.

The confirmation service must therefore verify:

```text
COUNT(order_lines) >= 1
```

inside the confirmation transaction.

---

# 9. Order State Constraints

The database stores the current state, while valid transitions are controlled by application services.

Valid transitions:

```text
DRAFT      -> CONFIRMED
DRAFT      -> CANCELLED
CONFIRMED  -> SHIPPED
SHIPPED    -> COMPLETED
```

Terminal states:

```text
COMPLETED
CANCELLED
```

The database must prevent invalid status values, but transition semantics remain application-level business logic.

For example, a simple database constraint should not attempt to encode:

```text
DRAFT -> CONFIRMED
CONFIRMED -> SHIPPED
```

as a generic row constraint because the validity of a transition depends on the previous persisted state and the complete business operation.

Transition enforcement belongs to the order application service and its transaction.

Relevant requirements:

* ERP-REQ-016
* ERP-REQ-020
* ERP-REQ-021
* ERP-REQ-022
* ERP-REQ-023

---

# 10. External Event Schema

Logical table:

```text
integration_external_events
```

Purpose:

Stores external webhook events and provides durable idempotency.

Fields:

| Field             | Type                     | Nullable | Constraints           |
| ----------------- | ------------------------ | -------: | --------------------- |
| id                | UUID                     |       No | Primary key           |
| external_event_id | VARCHAR(255)             |       No | Unique                |
| event_type        | VARCHAR(64)              |       No | Non-empty             |
| order_id          | UUID                     |      Yes | FK → orders.id        |
| payment_amount    | NUMERIC(12,2)            |      Yes | `>= 0`                |
| processing_status | VARCHAR(32)              |       No | Explicit status       |
| received_at       | TIMESTAMP WITH TIME ZONE |       No |                       |
| processed_at      | TIMESTAMP WITH TIME ZONE |      Yes |                       |
| error_message     | TEXT                     |      Yes | Diagnostic, sanitized |

---

# 11. External Event Idempotency

`external_event_id` must be unique.

Database constraint:

```text
UNIQUE(external_event_id)
```

This is the primary database-level idempotency boundary.

The webhook processing flow must still use a transaction because uniqueness alone does not define the complete business behavior.

The expected behavior is:

```text
new external_event_id
        |
        v
create event record
        |
        v
process business effect
        |
        v
mark processed
```

For a repeated event:

```text
existing external_event_id
        |
        v
do not duplicate business effect
```

Relevant requirements:

* ERP-REQ-030
* ERP-REQ-031
* ERP-REQ-032
* ERP-REQ-033

---

# 12. External Event Processing States

The initial processing status vocabulary is:

```text
RECEIVED
PROCESSED
FAILED
```

The initial processing status is `RECEIVED`.

This is an application/model initialization default rather than a required
PostgreSQL column `DEFAULT`. Processing state transitions remain controlled by
the integration application service.

Meaning:

### RECEIVED

The event passed basic persistence requirements and has been recorded but processing has not completed.

### PROCESSED

The event was successfully handled and its business effect was applied.

### FAILED

Processing failed according to the integration error policy.

The system must not expose internal stack traces or secrets through the API.

Diagnostic information stored in `error_message` must be sanitized.

---

# 13. Referential Integrity

Foreign keys are required for all core domain relationships.

## 13.1 Customer → Order

```text
orders.customer_id
    REFERENCES customers.id
```

A customer referenced by an order must not be physically deleted through normal business operations.

Recommended behavior:

```text
ON DELETE PROTECT
```

or equivalent application-level deletion prevention.

Customer deactivation is the supported lifecycle mechanism.

---

## 13.2 Order → OrderLine

```text
order_lines.order_id
    REFERENCES orders.id
```

An order line has no independent business meaning without its order.

Recommended behavior:

```text
ON DELETE CASCADE
```

when an order is physically removed during controlled non-production/test cleanup.

Normal production business operations should not delete orders.

---

## 13.3 Product → OrderLine

```text
order_lines.product_id
    REFERENCES products.id
```

Products referenced by historical order lines must remain available for referential integrity.

Recommended behavior:

```text
ON DELETE PROTECT
```

Product deactivation is preferred over deletion.

---

## 13.4 Product → StockItem

```text
inventory_stock_items.product_id
    REFERENCES products.id
```

Recommended behavior:

```text
ON DELETE PROTECT
```

A product with inventory history or current stock must not be deleted through normal business operations.

---

## 13.5 Warehouse → StockItem

```text
inventory_stock_items.warehouse_id
    REFERENCES warehouses.id
```

Recommended behavior:

```text
ON DELETE PROTECT
```

Warehouse deactivation is preferred over deletion.

---

## 13.6 Order → ExternalEvent

```text
integration_external_events.order_id
    REFERENCES orders.id
```

The order reference may be nullable because ERP-REQ-033 explicitly allows unknown-order webhook events to be rejected or failed without modifying unrelated order state.

Therefore:

```text
order_id NULL
```

is permitted for events that cannot be associated with an existing order.

Recommended behavior:

```text
ON DELETE PROTECT
```

for associated orders.

---

# 14. Nullability Policy

Nullability must have explicit business meaning.

Nullable fields are limited to information that is genuinely optional.

Examples:

```text
Customer.email             nullable
Customer.phone             nullable
Warehouse.location         nullable
Product.description        nullable
ExternalEvent.order_id     nullable
ExternalEvent.processed_at nullable
ExternalEvent.error_message nullable
```

Core identity and integrity fields are non-nullable:

```text
Customer.name
Product.sku
Product.name
Product.unit_price
Warehouse.code
Warehouse.name
StockItem.product_id
StockItem.warehouse_id
StockItem.quantity
StockItem.reserved_quantity
SalesOrder.customer_id
SalesOrder.status
SalesOrderLine.order_id
SalesOrderLine.product_id
SalesOrderLine.quantity
SalesOrderLine.unit_price
ExternalEvent.external_event_id
ExternalEvent.event_type
ExternalEvent.processing_status
```

---

# 15. Primary Keys

All domain entities use UUID primary keys.

The primary entities are:

```text
customers.id
products.id
warehouses.id
inventory_stock_items.id
orders.id
order_lines.id
integration_external_events.id
```

Reasons:

* avoids exposing sequential database identifiers;
* suitable for distributed integration boundaries;
* stable external references;
* avoids coupling business identifiers to database insertion order.

The UUID itself is not considered a substitute for business uniqueness constraints.

For example:

```text
Product.id       -> technical identity
Product.sku      -> business identity
Warehouse.id     -> technical identity
Warehouse.code   -> business identity
ExternalEvent.id -> technical identity
ExternalEvent.external_event_id -> external business identity
```

---

# 16. Unique Constraints

The following unique constraints are mandatory:

```text
products.sku
warehouses.code
inventory_stock_items(product_id, warehouse_id)
integration_external_events.external_event_id
```

These implement:

* ERP-REQ-005
* ERP-REQ-007
* ERP-REQ-008
* ERP-REQ-032
* ERP-REQ-055

No uniqueness requirement is currently defined for customer email or phone.

Therefore the database must not invent such a constraint.

---

# 17. Check Constraints

The database must enforce the following invariants.

## Customer

```text
name <> ''
```

## Product

```text
sku <> ''
name <> ''
unit_price >= 0
```

## Warehouse

```text
code <> ''
```

## Inventory

```text
quantity >= 0
reserved_quantity >= 0
reserved_quantity <= quantity
```

## Sales Order

```text
status IN (
    'DRAFT',
    'CONFIRMED',
    'SHIPPED',
    'COMPLETED',
    'CANCELLED'
)
```

## Order Line

```text
quantity > 0
unit_price >= 0
```

## External Event

```text
processing_status IN (
    'RECEIVED',
    'PROCESSED',
    'FAILED'
)

payment_amount IS NULL OR payment_amount >= 0
```

These constraints provide defense in depth against invalid persisted states.

Application-level validation remains responsible for business workflows and cross-entity rules that cannot be represented safely as simple database constraints.

---

# 18. Available Quantity

`available_quantity` is defined as:

```text
available_quantity = quantity - reserved_quantity
```

It should not be independently persisted as mutable state.

Example:

```text
quantity = 100
reserved_quantity = 30

available_quantity = 70
```

This avoids the possibility of:

```text
quantity = 100
reserved_quantity = 30
available_quantity = 80
```

where duplicated state would become inconsistent.

The API may expose `available_quantity` as a calculated field.

---

# 19. Inventory Transaction Strategy

Inventory-changing operations must execute inside database transactions.

Critical operations include:

```text
order confirmation
order shipment
future inventory adjustments
```

The confirmation operation must conceptually execute:

```text
BEGIN

validate order
validate customer
validate order lines

SELECT required stock rows
FOR UPDATE

re-check available quantity

increase reserved_quantity

transition order to CONFIRMED

COMMIT
```

The exact Django implementation will use:

```text
transaction.atomic()
```

and row-level locking through:

```text
SELECT ... FOR UPDATE
```

where required.

---

# 20. Inventory Concurrency

The database must protect against concurrent confirmations consuming the same available stock.

Example:

```text
Available stock = 10
Order A requires = 7
Order B requires = 7
```

Without locking, both transactions could observe:

```text
available = 10
```

and both succeed incorrectly.

The required strategy is:

```text
transaction
    +
row-level lock
    +
re-check after lock
    +
atomic update
```

Therefore only one transaction can reserve the contested stock at a time.

The second transaction must re-evaluate availability after obtaining the lock.

If insufficient stock remains:

```text
confirmation fails
order remains DRAFT
inventory remains unchanged
```

This directly implements ERP-REQ-011, ERP-REQ-017, ERP-REQ-018 and ERP-REQ-019.

---

# 21. Shipment Transaction Strategy

Shipment is also an atomic inventory/order operation.

Conceptually:

```text
BEGIN

validate order is CONFIRMED

lock required inventory rows

verify reservation

quantity -= shipped_quantity
reserved_quantity -= shipped_quantity

transition order to SHIPPED

COMMIT
```

Example:

```text
Before:

quantity = 100
reserved_quantity = 30
available_quantity = 70
```

After shipment of 30:

```text
quantity = 70
reserved_quantity = 0
available_quantity = 70
```

`reserved_quantity` therefore represents **active reservations**, not historical shipped quantities.

---

# 22. Order Confirmation Consistency

The following state must never be committed:

```text
Order = CONFIRMED
Inventory reservation = not applied
```

The following state must also never be committed:

```text
Inventory reservation = applied
Order = DRAFT
```

The order confirmation transaction must therefore encompass:

```text
inventory reservation
+
order state transition
```

in one atomic transaction.

A failure in either operation must roll back both.

---

# 23. Order Immutability

Once an order reaches:

```text
COMPLETED
```

normal business operations must not modify its meaningful business state.

The database does not attempt to enforce all application-level immutability rules through triggers.

Instead:

* application services reject unsupported operations;
* API permissions prevent unauthorized changes;
* tests verify lifecycle immutability;
* database constraints preserve referential integrity.

This is consistent with ERP-REQ-023.

---

# 24. Index Strategy

Indexes must support common access patterns without creating unnecessary indexes.

## Customers

Recommended:

```text
PRIMARY KEY(id)
INDEX(active)
```

The active index supports operational filtering.

---

## Products

Required:

```text
PRIMARY KEY(id)
UNIQUE(sku)
INDEX(active)
```

Potential query pattern:

```text
list active products
lookup by SKU
```

---

## Warehouses

Required:

```text
PRIMARY KEY(id)
UNIQUE(code)
INDEX(active)
```

---

## Inventory

Required:

```text
PRIMARY KEY(id)
UNIQUE(product_id, warehouse_id)
INDEX(product_id)
INDEX(warehouse_id)
```

The composite unique index supports the main lookup:

```text
product + warehouse
```

Separate indexes may be retained where query plans demonstrate value.

---

## Orders

Recommended:

```text
PRIMARY KEY(id)
INDEX(customer_id)
INDEX(status)
INDEX(created_at)
```

A composite index may later be introduced for frequent operational queries such as:

```text
customer_id + status
```

only if profiling demonstrates a need.

---

## Order Lines

Required:

```text
PRIMARY KEY(id)
INDEX(order_id)
INDEX(product_id)
```

`order_id` is particularly important for retrieving all lines belonging to an order.

---

## External Events

Required:

```text
PRIMARY KEY(id)
UNIQUE(external_event_id)
INDEX(order_id)
INDEX(processing_status)
INDEX(received_at)
```

The unique index on `external_event_id` is also the database-level idempotency mechanism.

---

# 25. Timestamp Strategy

All domain tables use timezone-aware timestamps.

Preferred database representation:

```text
TIMESTAMP WITH TIME ZONE
```

Application configuration must use UTC as the canonical storage timezone.

At minimum:

```text
created_at
modified_at
```

are required for core mutable entities.

Integration events additionally require:

```text
received_at
processed_at
```

where `processed_at` remains nullable until processing completes.

---

# 26. Delete Policy

The system is primarily designed around **deactivation rather than physical deletion**.

For business entities:

```text
Customer
Product
Warehouse
```

the preferred lifecycle is:

```text
active = true
        |
        v
active = false
```

rather than deleting the row.

This preserves historical relationships.

Recommended foreign-key policies:

```text
Order.customer        -> PROTECT
OrderLine.product     -> PROTECT
StockItem.product     -> PROTECT
StockItem.warehouse   -> PROTECT
ExternalEvent.order   -> PROTECT
Order.order_lines     -> CASCADE
```

Physical deletion of business records is considered an administrative/data-management operation rather than a normal business workflow.

---

# 27. Database and Application Responsibility Boundary

The system deliberately separates database invariants from application workflows.

## Database responsibility

The database must enforce:

* primary keys;
* foreign keys;
* unique constraints;
* non-negative quantities;
* valid numeric ranges;
* valid persisted state values where practical;
* inventory relational uniqueness;
* external event uniqueness;
* transactional atomicity;
* row-level locking.

## Application responsibility

Application services must enforce:

* customer active-state rules;
* product active-state rules;
* order lifecycle transitions;
* order contains at least one line before confirmation;
* sufficient available inventory;
* reservation logic;
* shipment logic;
* webhook validation;
* webhook business effects;
* role-based authorization;
* controlled business exceptions.

This prevents business workflows from being incorrectly encoded as isolated database constraints.

---

# 28. Migration Strategy

All schema changes must be represented by version-controlled Django migrations.

Migrations must be:

* deterministic;
* committed to Git;
* reviewable;
* reproducible from a clean checkout;
* compatible with the documented environment.

Initial implementation sequence:

```text
1. Create Django project structure
2. Create domain applications
3. Define models
4. Generate initial migrations
5. Review generated migrations
6. Apply migrations against PostgreSQL
7. Run Django system checks
8. Run automated tests
9. Verify constraints
10. Commit migration changes
```

Migration files must not be manually edited unless there is a specific documented reason.

---

# 29. Test Database Strategy

Automated tests must execute against a database configuration representative of production.

The primary integration test database is PostgreSQL.

Tests must verify:

* unique SKU enforcement;
* unique warehouse code enforcement;
* unique product/warehouse inventory record;
* non-negative inventory constraints;
* reservation invariants;
* order-line quantity constraints;
* referential integrity;
* external-event idempotency;
* transaction rollback;
* concurrent inventory behavior where practical.

Database-level constraints must not be tested only through application validation.

At least some tests must demonstrate that invalid direct persistence is rejected by the database layer.

---

# 30. Requirement Traceability

| Requirement | Database Design Evidence                         |
| ----------- | ------------------------------------------------ |
| ERP-REQ-005 | Unique `products.sku`                            |
| ERP-REQ-007 | Unique `warehouses.code`                         |
| ERP-REQ-008 | Unique `(product_id, warehouse_id)`              |
| ERP-REQ-009 | Quantity/reservation representation              |
| ERP-REQ-010 | `reserved_quantity <= quantity`                  |
| ERP-REQ-011 | Transactions + row-level locking                 |
| ERP-REQ-013 | `order_lines` relationship                       |
| ERP-REQ-014 | `quantity > 0`                                   |
| ERP-REQ-015 | Order-line price snapshot                        |
| ERP-REQ-017 | Transactional confirmation validation            |
| ERP-REQ-018 | Atomic inventory reservation                     |
| ERP-REQ-019 | Transaction rollback on insufficient stock       |
| ERP-REQ-021 | Confirmed → Shipped lifecycle                    |
| ERP-REQ-022 | Shipped → Completed lifecycle                    |
| ERP-REQ-023 | Application-level immutability                   |
| ERP-REQ-032 | Unique `external_event_id`                       |
| ERP-REQ-033 | Nullable order reference + failed event handling |
| ERP-REQ-053 | PostgreSQL                                       |
| ERP-REQ-054 | Foreign keys                                     |
| ERP-REQ-055 | Unique/check constraints                         |
| ERP-REQ-056 | Externalized configuration                       |
| ERP-REQ-057 | No secrets in repository                         |
| ERP-REQ-062 | Migration execution in CI                        |
| ERP-REQ-065 | This database specification                      |

---

# 31. Design Invariants

The following invariants are considered part of the database contract.

### Inventory

```text
quantity >= 0
reserved_quantity >= 0
reserved_quantity <= quantity
available_quantity = quantity - reserved_quantity
```

### Product

```text
sku is unique
unit_price >= 0
```

### Warehouse

```text
code is unique
```

### Order Line

```text
quantity > 0
unit_price >= 0
```

### External Events

```text
external_event_id is unique
```

### Relationships

```text
order.customer exists
order_line.order exists
order_line.product exists
stock_item.product exists
stock_item.warehouse exists
```

### Order confirmation

```text
CONFIRMED
    =>
required inventory reservation exists
```

### Shipment

```text
SHIPPED
    =>
previous state was CONFIRMED
```

---

# 32. Explicitly Deferred Database Decisions

The following are intentionally not introduced into the schema because they are outside the current requirements baseline:

* cell-level battery inventory;
* accounting ledger;
* invoices;
* tax tables;
* payment settlement tables;
* shipment tracking entities;
* partial shipment quantities;
* returns;
* stock adjustment audit ledger;
* reservation expiration;
* reservation ownership tables;
* supplier management;
* purchase orders;
* multi-currency support;
* product variants;
* batch/lot tracking;
* serial-number tracking;
* soft-delete framework;
* database audit triggers.

These features require explicit requirements before being added.

---

# 33. Database Design Status

Current status:

```text
Database Design: APPROVED
```

The design is aligned with the current requirements baseline and architecture baseline.

The database design review has confirmed:

```text
[x] All requirements mapped to architecture
[x] All core entities confirmed
[x] Field types confirmed
[x] Monetary precision confirmed
[x] Foreign-key policies confirmed
[x] Unique constraints confirmed
[x] Check constraints confirmed
[x] Inventory locking strategy confirmed
[x] External-event idempotency confirmed
[x] Index strategy confirmed
[x] Migration strategy confirmed
```

The database design is approved for Django model and migration implementation.

Implementation must preserve the constraints, relationships, transaction boundaries, concurrency strategy and lifecycle invariants defined in this specification.
