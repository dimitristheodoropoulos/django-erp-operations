# Django ERP Operations Platform — Architecture Specification

**Document:** Architecture Specification  
**Project:** Django ERP Operations Platform  
**Version:** 1.0  
**Status:** Draft  
**Requirements Baseline:** `14db353`  
**Last Updated:** 2026-09-02

---

# 1. Architectural Goals

The architecture SHALL provide a maintainable, testable, reliable and production-oriented Django backend for the operational requirements defined in `docs/requirements.md`.

The architecture is designed around the following principles:

## 1.1 Domain-Oriented Design

The system SHALL be organized around business domains rather than around technical layers alone.

The primary domains are:

- customers
- products
- warehouses
- inventory
- sales orders
- external integrations
- authentication and authorization

Django applications SHALL have clear responsibilities and SHALL avoid unnecessary coupling.

## 1.2 Explicit Business Logic

Critical business rules SHALL be implemented explicitly rather than being distributed unpredictably across views, serializers, model methods and signals.

Business operations such as:

- order confirmation
- inventory reservation
- order cancellation
- shipment
- completion
- webhook processing

SHALL have clearly defined application-level entry points.

## 1.3 Transactional Integrity

Operations that modify multiple related records SHALL execute atomically.

In particular, order confirmation and inventory reservation SHALL form a single transactional operation.

A failed operation SHALL NOT leave partially applied business state.

## 1.4 Database as an Integrity Boundary

The PostgreSQL database SHALL enforce critical invariants where appropriate.

Application-level validation SHALL provide useful errors, while database constraints SHALL provide a final integrity boundary for invariants that can be expressed at database level.

## 1.5 Concurrency Safety

Inventory operations SHALL be designed explicitly for concurrent access.

Where concurrent updates can produce inconsistent inventory state, PostgreSQL transactions and row-level locking SHALL be used.

Concurrency correctness SHALL be tested where practical.

## 1.6 Testability

Critical business logic SHALL be structured so that it can be tested independently of HTTP transport.

The test architecture SHALL distinguish between:

- domain/business logic tests
- database/integration tests
- API tests
- webhook tests
- migration tests

## 1.7 API Separation

The REST API SHALL act as an external interface to application capabilities.

API-specific concerns such as:

- request parsing
- authentication
- serialization
- HTTP status codes
- error formatting

SHALL remain separate from core business rules.

## 1.8 Explicit Integration Boundaries

External events SHALL enter the system through controlled integration boundaries.

Webhook processing SHALL validate external input and use persistent event identifiers to provide idempotent processing.

## 1.9 Reproducibility

The architecture SHALL support deterministic development and testing through:

- explicit dependencies
- environment-based configuration
- PostgreSQL
- Docker
- automated tests
- CI

## 1.10 Incremental Implementation

Architecture SHALL support incremental implementation.

No component SHALL be introduced solely for theoretical complexity.

Architectural decisions SHALL be justified by current requirements, testability, maintainability or operational reliability.

```
# 2. System Context

The Django ERP Operations Platform is a backend application responsible for managing operational business data and workflows.

The system interacts with the following actors and external systems:

```text
                         ┌──────────────────────┐
                         │      ERP Users       │
                         │                      │
                         │ Admin                │
                         │ Operations           │
                         │ Read-Only            │
                         └──────────┬───────────┘
                                    │
                                    │ REST API
                                    │
                                    v
                    ┌──────────────────────────────┐
                    │ Django ERP Operations        │
                    │ Platform                    │
                    │                              │
                    │ Customer Management          │
                    │ Product Management           │
                    │ Warehouse / Inventory        │
                    │ Sales Orders                 │
                    │ Webhook Integration          │
                    │ Authentication               │
                    │ Authorization                │
                    └──────────────┬───────────────┘
                                   │
                         ┌─────────┴─────────┐
                         │                   │
                         v                   v
                ┌────────────────┐   ┌─────────────────┐
                │  PostgreSQL    │   │ External System │
                │                │   │ / Payment      │
                │ Domain data    │   │ Simulator      │
                │ Transactions   │   │                │
                │ Constraints    │   │ Webhooks       │
                └────────────────┘   └─────────────────┘
```

## 2.1 System Boundary

The Django application is responsible for:

* domain data management
* business rule enforcement
* sales order lifecycle management
* inventory reservation
* API request handling
* webhook validation and idempotency
* authentication and authorization
* application-level logging
* migration utilities

## 2.2 External Responsibilities

The following responsibilities remain outside the system:

* real payment processing
* real shipping provider integration
* accounting
* payroll
* tax calculation
* production cloud infrastructure

External systems interact with the application through explicitly defined interfaces.

## 2.3 Primary Interaction Paths

The primary interaction paths are:

```text
ERP User
    |
    v
REST API
    |
    v
Application Services
    |
    +----> Domain Models
    |
    +----> PostgreSQL
```

For external payment events:

```text
External System
    |
    v
Payment Webhook
    |
    v
Webhook Validation
    |
    v
Idempotency Check
    |
    v
Business Processing
    |
    v
PostgreSQL
```

```
# 3. Django Project Structure

The project SHALL use a domain-oriented Django application structure.

The proposed structure is:

```text
django-erp-operations/
│
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── testing.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── customers/
│   ├── products/
│   ├── warehouses/
│   ├── inventory/
│   ├── orders/
│   ├── integrations/
│   └── accounts/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   ├── webhooks/
│   └── migrations/
│
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── database.md
│   ├── api.md
│   └── development.md
│
├── manage.py
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── .env.example
```

## 3.1 Application Responsibilities

### `customers`

Responsible for customer domain functionality.

Responsibilities include:

* customer model
* customer status
* customer validation
* customer-related application operations

### `products`

Responsible for product domain functionality.

Responsibilities include:

* product model
* SKU uniqueness
* product validation
* product status
* product pricing

### `warehouses`

Responsible for warehouse domain functionality.

Responsibilities include:

* warehouse model
* warehouse identity
* warehouse status
* warehouse-related validation

### `inventory`

Responsible for inventory domain functionality.

Responsibilities include:

* stock representation
* available quantity calculation
* stock validation
* reservation
* reservation release
* concurrency control
* inventory transactions

Inventory is a critical consistency boundary.

### `orders`

Responsible for sales order functionality.

Responsibilities include:

* sales order model
* sales order lines
* order lifecycle
* order validation
* order confirmation
* order cancellation
* shipment
* completion
* coordination with inventory

### `integrations`

Responsible for external integration functionality.

Responsibilities include:

* external events
* webhook endpoints
* webhook validation
* idempotency
* integration error handling

### `accounts`

Responsible for authentication and authorization.

Responsibilities include:

* authenticated users
* roles
* permissions
* access-control policies

### 3.1.1 Authentication and Authorization Model

The `accounts` application SHALL own the application's authentication and authorization model.

Authentication SHALL use Django's built-in user model together with Django REST Framework token authentication.

The system SHALL represent the required logical application roles using Django Groups:

```text
ADMIN
OPERATIONS
READ_ONLY
```

The role model SHALL be interpreted as follows:

| Role       | Read operational data | Create/modify operational data | Administrative access |
| ---------- | --------------------- | ------------------------------ | --------------------- |
| ADMIN      | Yes                   | Yes                            | Yes                   |
| OPERATIONS | Yes                   | Yes                            | No                    |
| READ_ONLY  | Yes                   | No                             | No                    |

`ADMIN` SHALL represent the application's full administrative role.

`OPERATIONS` SHALL provide operational access to customer, product, inventory and sales-order functionality.

`READ_ONLY` SHALL provide read-only access to permitted operational resources.

The role model SHALL NOT imply that every future endpoint is automatically accessible. Endpoint permissions SHALL be explicitly enforced according to the operation and the applicable requirements.

Authentication SHALL be evaluated before authorization.

Authorization SHALL be evaluated before protected application operations are invoked.

The API SHALL use authentication as the security boundary and the `accounts` application as the owner of role and access-control policy.

The API root MAY remain publicly accessible where explicitly configured as a public API infrastructure endpoint.

The Django superuser mechanism SHALL NOT be treated as a substitute for the application's logical role model.

## 3.2 Shared Configuration

The `config` package SHALL contain Django project configuration only.

It SHALL NOT contain business-domain logic.

## 3.3 Dependency Direction

The preferred dependency direction is:

```text
API / HTTP
     |
     v
Application Services
     |
     v
Domain Models / Domain Operations
     |
     v
Django ORM / PostgreSQL
```
# 4. Application Boundaries and Business Operations

The system SHALL keep business operations explicit and separate from HTTP transport concerns.

Business operations that modify domain state SHALL be exposed through application-level service functions or equivalent domain operations.

## 4.1 Application Services

Application services SHALL coordinate multi-step business operations.

Examples include:

* confirming a sales order
* cancelling a sales order
* shipping an order
* completing an order
* processing an external payment event
* importing legacy customer records

Application services SHALL:

* validate business preconditions
* coordinate affected domain objects
* execute required database transactions
* enforce transactional boundaries
* translate domain failures into controlled application errors

Application services SHALL NOT depend on HTTP request or response objects.

## 4.2 Order and Inventory Boundary

The `orders` application SHALL coordinate operations that affect both orders and inventory.

The preferred dependency direction is:

```text
orders
   |
   v
inventory
```

The `inventory` application SHALL NOT depend on the `orders` application.

This prevents circular dependencies and keeps inventory functionality reusable independently of sales orders.

The inventory application SHALL expose operations required by order processing, such as:

* checking available stock
* reserving stock
* releasing a reservation where applicable

## 4.3 Order Confirmation

Order confirmation is a critical transactional operation.

The conceptual operation is:

```text
confirm_order(order_id)
        |
        v
Validate order state
        |
        v
Validate customer state
        |
        v
Validate order lines
        |
        v
Identify required inventory records
        |
        v
Acquire row-level locks
        |
        v
Check available quantities
        |
        v
Reserve inventory
        |
        v
Change order state to CONFIRMED
        |
        v
Commit transaction
```

The inventory reservation and order state transition SHALL occur within the same database transaction.

If any required inventory operation fails:

* the transaction SHALL roll back
* the order SHALL remain in its previous state
* inventory quantities SHALL remain unchanged by the failed operation

## 4.4 Concurrency Control

Inventory reservation SHALL protect against concurrent confirmations consuming the same available stock.

The implementation SHALL use PostgreSQL transactions and row-level locking where required.

Conceptually:

```text
Transaction A                 Transaction B
-----------                   -----------
Lock StockItem
Check available
Reserve stock
Commit
                              Wait for lock
                              Re-read stock
                              Check available
                              Reserve or fail
                              Commit
```

The exact locking strategy SHALL be defined in the database design.

## 4.5 Order Lifecycle Operations

The order application SHALL expose explicit operations for lifecycle transitions.

The conceptual interface is:

```text
confirm_order()
cancel_order()
ship_order()
complete_order()
```

Each operation SHALL:

1. load the relevant order
2. validate the current state
3. validate operation-specific business rules
4. perform required related operations
5. persist the resulting state atomically

The following transitions SHALL be enforced:

```text
DRAFT
  |
  +----> CONFIRMED
  |          |
  |          v
  |       SHIPPED
  |          |
  |          v
  |      COMPLETED
  |
  +----> CANCELLED
```

Unsupported transitions SHALL raise a controlled business error.

## 4.6 Separation from API Layer

The API layer SHALL call application services rather than implementing complex business workflows directly.

The preferred flow is:

```text
HTTP Request
     |
     v
API View / Endpoint
     |
     v
Serializer / Input Validation
     |
     v
Application Service
     |
     v
Domain Operations
     |
     v
PostgreSQL
```

API serializers SHALL handle transport-level input validation and representation.

They SHALL NOT become the primary location for multi-step business workflows.

## 4.7 Django Signals

Django signals SHALL NOT be used as the primary mechanism for critical business workflows.

Critical operations such as:

* inventory reservation
* order confirmation
* order cancellation
* shipment
* completion
* webhook processing

SHALL be explicitly invoked through application-level operations.

Signals MAY be introduced for non-critical technical concerns where they provide a clear benefit and do not hide business behavior.

## 4.8 Transaction Boundaries

Transactions SHALL be placed around complete business operations rather than around individual model writes.

For example:

```python
transaction.atomic():
    validate order
    lock inventory
    validate stock
    reserve stock
    transition order
```

The exact implementation SHALL be determined during the implementation phase.

The architecture SHALL preserve the invariant that a critical business operation either completes fully or has no externally visible partial state.

# 5. Domain Model and Responsibilities

The domain model SHALL represent the business entities defined by the requirements specification.

Each entity SHALL have a clearly defined owning Django application and a limited set of responsibilities.

The initial domain model consists of:

* Customer
* Product
* Warehouse
* StockItem
* SalesOrder
* SalesOrderLine
* ExternalEvent

## 5.1 Customer

**Owning application:** `customers`

A `Customer` represents a business customer that may place sales orders.

Core responsibilities:

* customer identity
* customer contact information
* active/inactive status
* creation and modification timestamps

Key invariants:

* customer identity SHALL be unique
* inactive customers SHALL NOT be allowed to create or confirm new orders
* customer records SHALL remain referentially valid for existing orders

The customer domain SHALL own customer status and customer-specific validation.

## 5.2 Product

**Owning application:** `products`

A `Product` represents an item that can be sold and held in inventory.

Core responsibilities:

* product identity
* SKU
* name
* description
* unit price
* active/inactive status
* creation and modification timestamps

Key invariants:

* SKU SHALL be unique
* SKU and name SHALL NOT be empty
* unit price SHALL NOT be negative
* inactive products SHALL NOT be used for new order lines

The product domain SHALL own product identity, pricing and product status.

## 5.3 Warehouse

**Owning application:** `warehouses`

A `Warehouse` represents a physical or logical location in which inventory is held.

Core responsibilities:

* warehouse identity
* warehouse code
* name
* location
* active/inactive status

Key invariants:

* warehouse code SHALL be unique
* inactive warehouses SHALL NOT accept new inventory operations

The warehouse domain SHALL own warehouse identity and status.

## 5.4 StockItem

**Owning application:** `inventory`

A `StockItem` represents the inventory position for one product in one warehouse.

The conceptual relationship is:

```text
Product 1 ──────── * StockItem * ──────── 1 Warehouse
```

Each product/warehouse combination SHALL have at most one stock record.

Core attributes:

* product
* warehouse
* quantity
* reserved quantity
* available quantity

The conceptual invariant is:

```text
available_quantity = quantity - reserved_quantity
```

Key invariants:

* quantity SHALL NOT be negative
* reserved quantity SHALL NOT be negative
* reserved quantity SHALL NOT exceed quantity
* available quantity SHALL NOT be negative
* `(product, warehouse)` SHALL be unique

`StockItem` is the primary inventory consistency boundary.

Inventory operations SHALL be responsible for maintaining these invariants.

## 5.5 SalesOrder

**Owning application:** `orders`

A `SalesOrder` represents a customer's request to purchase one or more products.

Core responsibilities:

* order identity
* customer relationship
* lifecycle state
* order timestamps
* coordination of order-level business operations

The order lifecycle SHALL be:

```text
DRAFT
  |
  +----> CONFIRMED
  |          |
  |          v
  |       SHIPPED
  |          |
  |          v
  |      COMPLETED
  |
  +----> CANCELLED
```

The order domain SHALL own lifecycle transitions.

Key invariants include:

* an order SHALL belong to a customer
* an order SHALL contain at least one line before confirmation
* only valid lifecycle transitions SHALL be allowed
* a completed order SHALL be immutable under normal business operations

## 5.6 SalesOrderLine

**Owning application:** `orders`

A `SalesOrderLine` represents one product entry within a sales order.

Core attributes:

* sales order
* product
* quantity
* unit price snapshot

The line SHALL preserve the product price applicable at order creation time.

Therefore, subsequent changes to the current `Product.unit_price` SHALL NOT alter the historical unit price stored on an existing order line.

Key invariants:

* quantity SHALL be greater than zero
* product SHALL reference a valid product
* unit price snapshot SHALL NOT be negative
* each line SHALL belong to exactly one sales order

The order domain SHALL own order-line creation and validation.

## 5.7 ExternalEvent

**Owning application:** `integrations`

An `ExternalEvent` represents an externally supplied event received through an integration boundary.

Core responsibilities:

* external event identity
* event type
* referenced order
* external payment amount where applicable
* processing status
* timestamps
* diagnostic processing information where appropriate

Key invariants:

* external event identifier SHALL be unique
* the same external event SHALL NOT produce duplicate business effects
* invalid events SHALL NOT modify unrelated business state

The integrations domain SHALL own event validation and idempotency.

## 5.8 Domain Ownership

Domain ownership SHALL follow this mapping:

| Entity         | Owning Application | Primary Responsibility                        |
| -------------- | ------------------ | --------------------------------------------- |
| Customer       | `customers`        | Customer identity and status                  |
| Product        | `products`         | Product identity, pricing and status          |
| Warehouse      | `warehouses`       | Warehouse identity and status                 |
| StockItem      | `inventory`        | Inventory quantities and reservations         |
| SalesOrder     | `orders`           | Order lifecycle and order business operations |
| SalesOrderLine | `orders`           | Order contents and price snapshots            |
| ExternalEvent  | `integrations`     | External event validation and idempotency     |

An application MAY reference entities owned by another application when required by the domain model.

However, ownership of an entity's invariants SHALL remain with its owning application.

## 5.9 Cross-Domain Relationships

The principal relationships are:

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

External events reference the order they are associated with where applicable:

```text
ExternalEvent
      |
      | *
      |
      | 1
      v
SalesOrder
```

These relationships SHALL be enforced through appropriate database foreign keys and constraints.

## 5.10 Aggregate and Transaction Boundaries

The `SalesOrder` and its `SalesOrderLine` records SHALL be treated as one logical business unit for order lifecycle operations.

Inventory records SHALL remain independently owned by the inventory domain.

An operation that crosses domain boundaries SHALL be coordinated by an application service.

For example, order confirmation crosses:

```text
Orders
   |
   +----> Inventory
```

The transaction boundary SHALL encompass the complete confirmation operation.

This prevents the system from reaching states such as:

```text
Order = CONFIRMED
Inventory = not reserved
```

or:

```text
Inventory = reserved
Order = DRAFT
```

after a failed confirmation attempt.

## 5.11 Domain Invariants vs API Validation

The domain model SHALL distinguish between transport validation and business invariants.

API-level validation MAY reject malformed input before it reaches the domain.

However, business invariants SHALL NOT depend exclusively on API validation.

For example:

```text
API:
    quantity is an integer
        |
        v
Application / Domain:
    quantity > 0
        |
        v
Database:
    quantity cannot violate persisted constraints
```

Critical invariants SHALL remain enforced when business operations are invoked outside the REST API, such as through management commands, migration utilities or automated tests.

# 6. State and Inventory Lifecycle

The system SHALL define explicit lifecycle rules for sales orders and inventory reservations.

Lifecycle transitions SHALL be controlled by application-level business operations and SHALL NOT be performed through unrestricted direct state updates.

## 6.1 Sales Order States

A sales order SHALL use the following states:

```text
DRAFT
CONFIRMED
SHIPPED
COMPLETED
CANCELLED
```

The valid lifecycle is:

```text
                 confirm
DRAFT --------------------------> CONFIRMED
  |                                  |
  | cancel                           | ship
  |                                  v
  v                               SHIPPED
CANCELLED                            |
                                     | complete
                                     v
                                  COMPLETED
```

Only the transitions explicitly defined by the lifecycle SHALL be permitted.

## 6.2 DRAFT State

A newly created sales order SHALL start in `DRAFT`.

A `DRAFT` order MAY be modified before confirmation, subject to normal validation rules.

A `DRAFT` order MAY be cancelled.

Cancelling a `DRAFT` order SHALL NOT create or release an inventory reservation because no reservation has been established.

## 6.3 Confirmation

Confirmation SHALL be an atomic business operation.

Before confirmation, the application SHALL verify:

* the customer is active
* the order contains at least one line
* all order line quantities are valid
* all referenced products are valid for ordering
* sufficient available inventory exists

The confirmation operation SHALL:

1. validate the order
2. identify required inventory records
3. acquire the necessary row-level locks
4. re-evaluate available inventory under the transaction
5. reserve the required quantities
6. transition the order from `DRAFT` to `CONFIRMED`
7. commit the transaction

The reservation and state transition SHALL occur in the same database transaction.

If confirmation fails, the transaction SHALL roll back.

Therefore:

```text
Failed confirmation
        |
        +----> Order remains DRAFT
        |
        +----> No new reservation remains applied
        |
        +----> Existing inventory state is preserved
```

## 6.4 Inventory Reservation Model

Inventory SHALL distinguish between physical quantity and reserved quantity.

The conceptual model is:

```text
quantity
   |
   +---- reserved_quantity
   |
   v
available_quantity
```

with:

```text
available_quantity = quantity - reserved_quantity
```

Confirmation SHALL increase `reserved_quantity`.

Confirmation SHALL NOT immediately reduce `quantity`.

This distinction allows the system to represent stock that exists physically but is committed to confirmed orders.

## 6.5 Confirmed State

A `CONFIRMED` order represents an order for which the required inventory has been successfully reserved.

Once confirmed:

* the order SHALL no longer be treated as a draft
* normal order editing SHALL NOT be permitted
* the corresponding inventory reservation SHALL remain associated with the order until the next lifecycle operation determines its disposition

The architecture SHALL treat the reservation as part of the order's business state.

## 6.6 Cancellation

Cancellation SHALL be permitted only from `DRAFT` unless an explicit future requirement introduces additional cancellation states.

For the current requirements:

```text
DRAFT -> CANCELLED
```

is the only supported cancellation transition.

Therefore, cancellation of a `CONFIRMED`, `SHIPPED` or `COMPLETED` order SHALL be rejected.

Because only `DRAFT` orders can currently be cancelled, the current implementation does not require a reservation-release operation as part of order cancellation.

The inventory domain SHALL nevertheless provide reservation-release capability where required by future lifecycle extensions or other valid inventory workflows.

## 6.7 Shipment

Shipment SHALL be permitted only from `CONFIRMED`.

The valid transition is:

```text
CONFIRMED -> SHIPPED
```

Shipment represents the point at which previously reserved stock becomes consumed by the completed fulfillment step.

The shipment operation SHALL therefore:

1. validate that the order is `CONFIRMED`
2. verify the required inventory reservation exists
3. reduce the corresponding physical `quantity`
4. reduce the corresponding `reserved_quantity`
5. transition the order to `SHIPPED`
6. commit the complete operation atomically

The resulting inventory relationship SHALL remain:

```text
quantity_after = quantity_before - shipped_quantity

reserved_quantity_after =
    reserved_quantity_before - shipped_quantity
```

Therefore:

```text
available_quantity_after =
    quantity_after - reserved_quantity_after
```

The inventory change and order transition SHALL occur in the same database transaction.

A failed shipment SHALL NOT leave the order partially shipped or inventory partially consumed.

## 6.8 Completion

Completion SHALL be permitted only from `SHIPPED`.

The valid transition is:

```text
SHIPPED -> COMPLETED
```

Completion SHALL represent the final operational state of the current order lifecycle.

Completion SHALL NOT perform another inventory deduction because inventory consumption occurs during shipment.

A completed order SHALL be immutable under normal business operations.

## 6.9 Lifecycle Invariants

The following invariants SHALL always hold:

```text
DRAFT
    -> may become CONFIRMED
    -> may become CANCELLED

CONFIRMED
    -> may become SHIPPED

SHIPPED
    -> may become COMPLETED

COMPLETED
    -> terminal state

CANCELLED
    -> terminal state
```

The following transitions SHALL be rejected:

```text
CONFIRMED -> DRAFT
SHIPPED -> DRAFT
COMPLETED -> any state
CANCELLED -> any state
DRAFT -> SHIPPED
DRAFT -> COMPLETED
CONFIRMED -> COMPLETED
```

## 6.10 Inventory Invariants

At all persisted states:

```text
quantity >= 0

reserved_quantity >= 0

reserved_quantity <= quantity

available_quantity >= 0
```

The application and database SHALL cooperate to preserve these invariants.

Concurrent inventory operations SHALL not be allowed to produce a negative available quantity.

## 6.11 Transactional Lifecycle Rules

The following operations SHALL be atomic:

### Confirmation

```text
Validate
   |
Lock inventory
   |
Check availability
   |
Reserve
   |
CONFIRMED
   |
COMMIT
```

### Shipment

```text
Validate
   |
Lock inventory
   |
Validate reservation
   |
Consume quantity
   |
Release reservation
   |
SHIPPED
   |
COMMIT
```

A transaction failure at any stage SHALL roll back all state changes belonging to that operation.

## 6.12 Lifecycle Ownership

The `orders` application SHALL own sales order lifecycle transitions.

The `inventory` application SHALL own inventory quantity and reservation invariants.

Cross-domain lifecycle operations SHALL be coordinated by application services in the `orders` domain.

Therefore:

```text
orders
   |
   +---- confirm ----> inventory.reserve()
   |
   +---- ship -------> inventory.consume_reservation()
```

The inventory application SHALL not decide whether an order is confirmed or shipped.

The order application SHALL not directly manipulate inventory fields without going through the inventory domain operations.

## 6.13 Future Lifecycle Extensions

The architecture intentionally leaves room for future lifecycle extensions without requiring them in the current scope.

Examples include:

* cancellation after confirmation
* reservation expiration
* partial shipment
* partial fulfillment
* stock adjustment workflows
* return processing

Such functionality SHALL require explicit requirements and SHALL NOT be inferred from the current implementation.

The current implementation SHALL therefore remain limited to the lifecycle defined in this specification.
