# Django ERP Operations Platform — API Specification

**Document:** API Specification
**Project:** Django ERP Operations Platform
**Version:** 1.0
**Status:** Approved
**Requirements Baseline:** `14db353`
**Architecture Baseline:** `Draft v1.0`
**Last Updated:** 2026-09-02

---

# 1. Purpose

This document defines the REST API contract for the Django ERP Operations Platform.

The API SHALL provide an external interface to the business capabilities defined in `docs/requirements.md`.

The API SHALL expose application capabilities without moving core business rules into HTTP views, serializers or URL handlers.

The API is therefore a transport boundary over the application and domain layers.

The intended dependency direction is:

```text
HTTP Request
     |
     v
API Endpoint
     |
     v
Input / Transport Validation
     |
     v
Application Service
     |
     v
Domain Models / Operations
     |
     v
PostgreSQL
```

The API specification defines:

* endpoint structure
* HTTP methods
* request representations
* response representations
* validation responsibilities
* HTTP status semantics
* business error mapping
* authentication and authorization boundaries
* order lifecycle operations
* inventory access
* webhook boundaries
* pagination and filtering conventions
* requirements traceability
* API-specific out-of-scope behavior

This document does not define implementation details of Django views, serializers or URL configuration.

---

# 2. API Design Principles

The API SHALL follow the following principles.

## 2.1 API as a Transport Boundary

The API SHALL translate between HTTP representations and application-level operations.

The API SHALL NOT become the primary location for business workflows.

For example:

```text
POST /api/v1/orders/{id}/confirm/
        |
        v
API endpoint
        |
        v
confirm_order(order_id)
```

The endpoint SHALL NOT independently implement:

* inventory availability calculations
* stock locking
* reservation allocation
* order state transitions
* transaction management

Those responsibilities belong to the application/domain layer.

---

## 2.2 Explicit Business Operations

Operations that represent meaningful business transitions SHALL use explicit endpoints rather than generic unrestricted state updates.

For example:

```text
POST /api/v1/orders/{id}/confirm/
```

is preferred over:

```text
PATCH /api/v1/orders/{id}/
{
    "status": "CONFIRMED"
}
```

The latter would hide a multi-step business operation inside a generic update.

---

## 2.3 Database and Domain Invariants Remain Authoritative

API validation MAY reject malformed input before it reaches the application layer.

However, API validation SHALL NOT be the only enforcement mechanism for business invariants.

The following remain application/database responsibilities:

* positive order quantities
* non-negative prices
* valid lifecycle transitions
* customer activity requirements
* product activity requirements
* stock availability
* inventory reservation invariants
* transactional consistency
* uniqueness constraints

---

## 2.4 No Direct Inventory Mutation Through Generic CRUD

The API SHALL NOT expose unrestricted updates to inventory consistency fields.

In particular, clients SHALL NOT directly manipulate:

```text
StockItem.quantity
StockItem.reserved_quantity
```

through a generic PATCH endpoint.

Inventory mutations SHALL occur through explicit business operations.

---

## 2.5 Versioned API

The initial API SHALL use an explicit version prefix:

```text
/api/v1/
```

All API endpoints defined by this specification SHALL be under this prefix.

Future incompatible API changes SHALL use a new API version rather than silently changing the existing contract.

---

# 3. API Scope

The initial API v1 scope covers the core operational domains:

```text
Customers
Products
Warehouses
Inventory
Sales Orders
Order Confirmation
Authentication / Authorization boundary
```

External payment event processing is part of the broader platform architecture but is treated as a separate integration boundary.

CSV import is also a separate operational capability and SHALL NOT be introduced into the core CRUD API unless explicitly specified.

The initial API does not claim to provide:

* real payment processing
* real shipping-provider integration
* accounting
* payroll
* tax calculation
* production infrastructure management
* advanced reporting
* partial shipment
* reservation expiration
* return processing

Such capabilities require explicit requirements before being added.

---

# 4. Base URL

The logical API base path is:

```text
/api/v1/
```

Examples:

```text
GET  /api/v1/customers/
GET  /api/v1/products/
GET  /api/v1/warehouses/
GET  /api/v1/inventory/
GET  /api/v1/orders/
POST /api/v1/orders/{order_id}/confirm/
```

The deployment-specific host is intentionally not fixed by this specification.

---

# 5. HTTP and Representation Conventions

## 5.1 HTTP Methods

The API SHALL use standard HTTP semantics.

| Method   | Purpose                                                  |
| -------- | -------------------------------------------------------- |
| `GET`    | Retrieve resources                                       |
| `POST`   | Create resources or execute explicit business operations |
| `PATCH`  | Partially update mutable resource attributes             |
| `DELETE` | Delete a resource only where explicitly permitted        |

Generic `PUT` is not required by the initial API contract.

---

## 5.2 Content Type

JSON SHALL be the primary API representation.

Requests containing bodies SHALL use:

```http
Content-Type: application/json
```

Successful responses containing JSON SHALL use:

```http
Content-Type: application/json
```

---

## 5.3 Identifiers

Domain resources SHALL expose their persistent identifiers.

The current domain model uses UUID primary keys for:

* customers
* products
* warehouses
* stock items
* sales orders
* sales order lines

API clients SHALL treat identifiers as opaque values.

Clients SHALL NOT depend on UUID generation details.

---

## 5.4 Timestamps

Timestamps SHALL be represented in ISO 8601-compatible format.

Example:

```json
{
  "created_at": "2026-09-02T12:30:00Z"
}
```

The API SHALL preserve timezone-aware timestamps.

---

## 5.5 Decimal Values

Monetary values SHALL be represented as decimal values with two decimal places.

Example:

```json
{
  "unit_price": "19.95"
}
```

The API SHALL NOT represent monetary values as binary floating-point numbers.

---

# 6. Authentication

The API SHALL require authentication for protected ERP operations.

The exact authentication mechanism SHALL be selected during implementation based on the project requirements and approved application configuration.

The API contract intentionally does not prescribe a specific authentication library at this stage.

Unauthenticated requests to protected endpoints SHALL receive:

```http
401 Unauthorized
```

The API SHALL NOT expose protected ERP data to unauthenticated clients.

---

# 7. Authorization

Authorization SHALL be evaluated after authentication.

The `accounts` Django application owns:

* authenticated users
* roles
* permissions
* access-control policies

The API layer SHALL enforce authorization before invoking protected application operations.

An authenticated user who does not have permission to perform an operation SHALL receive:

```http
403 Forbidden
```

Authorization checks SHALL NOT replace business validation.

For example:

```text
Authentication / Authorization
        |
        v
May this user invoke the operation?
        |
        v
Application service
        |
        v
Is the business operation valid?
```

The precise role-to-permission matrix SHALL be finalized from the authentication and authorization requirements before implementation.

---

# 8. Common Error Model

API errors SHALL use a consistent structured representation.

The canonical error format is:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message."
  }
}
```

The `code` field SHALL be stable enough for programmatic client handling.

Clients SHOULD NOT depend on the exact wording of `message`.

---

## 8.1 Validation Errors

Malformed or invalid request data SHALL use:

```http
400 Bad Request
```

Example:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request contains invalid data."
  }
}
```

Field-level validation MAY additionally include structured details:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more fields are invalid.",
    "fields": {
      "quantity": [
        "Quantity must be greater than zero."
      ]
    }
  }
}
```

The exact field-error representation SHALL remain consistent across API endpoints.

---

# 9. Business Error Mapping

Application services expose domain/business exceptions.

The API layer SHALL translate these exceptions into HTTP responses.

For order confirmation, the current exception taxonomy is:

```text
OrderConfirmationError
├── OrderNotFound
├── InvalidOrderState
├── InactiveCustomer
├── OrderHasNoLines
├── InvalidOrderQuantity
├── InactiveProduct
└── InsufficientStock
```

The API mapping SHALL be:

| Application Error      | HTTP Status | API Code                 |
| ---------------------- | ----------: | ------------------------ |
| `OrderNotFound`        |       `404` | `ORDER_NOT_FOUND`        |
| `InvalidOrderState`    |       `409` | `INVALID_ORDER_STATE`    |
| `InactiveCustomer`     |       `409` | `INACTIVE_CUSTOMER`      |
| `OrderHasNoLines`      |       `409` | `ORDER_HAS_NO_LINES`     |
| `InvalidOrderQuantity` |       `400` | `INVALID_ORDER_QUANTITY` |
| `InactiveProduct`      |       `409` | `INACTIVE_PRODUCT`       |
| `InsufficientStock`    |       `409` | `INSUFFICIENT_STOCK`     |

The API layer SHALL NOT expose Python exception class names as its public contract.

---

# 10. HTTP Status Semantics

The API SHALL use the following general status semantics.

| Status                      | Meaning                                                              |
| --------------------------- | -------------------------------------------------------------------- |
| `200 OK`                    | Successful retrieval or update                                       |
| `201 Created`               | Successful resource creation                                         |
| `204 No Content`            | Successful operation with no response representation                 |
| `400 Bad Request`           | Invalid/malformed request                                            |
| `401 Unauthorized`          | Authentication required or invalid                                   |
| `403 Forbidden`             | Authenticated but not authorized                                     |
| `404 Not Found`             | Requested resource does not exist                                    |
| `409 Conflict`              | Request conflicts with current business state                        |
| `422 Unprocessable Entity`  | Not required by initial contract; avoid unless explicitly introduced |
| `500 Internal Server Error` | Unexpected server failure                                            |

Business rule violations SHALL generally use `409 Conflict` where the request is structurally valid but cannot be applied to the current domain state.

---

# 11. Customer API

Customers are owned by the `customers` application.

## 11.1 List Customers

```http
GET /api/v1/customers/
```

Returns a collection of customers accessible to the authenticated user.

Example response:

```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Example Customer",
      "email": "customer@example.com",
      "active": true,
      "created_at": "2026-09-02T10:00:00Z",
      "modified_at": "2026-09-02T10:00:00Z"
    }
  ]
}
```

---

## 11.2 Retrieve Customer

```http
GET /api/v1/customers/{customer_id}/
```

Successful response:

```http
200 OK
```

Unknown customer:

```http
404 Not Found
```

---

## 11.3 Create Customer

```http
POST /api/v1/customers/
```

The request SHALL contain the fields required by the customer requirements.

Example:

```json
{
  "name": "Example Customer",
  "email": "customer@example.com"
}
```

Successful creation:

```http
201 Created
```

The API SHALL not allow clients to bypass customer-domain validation.

---

## 11.4 Customer State

Customer active/inactive status is a business property.

The API SHALL expose the current state.

Changing customer state SHALL use an explicitly defined business operation or approved update mechanism.

The API SHALL NOT introduce an arbitrary state transition mechanism without corresponding requirements.

---

# 12. Product API

Products are owned by the `products` application.

## 12.1 List Products

```http
GET /api/v1/products/
```

Example response:

```json
{
  "results": [
    {
      "id": "uuid",
      "sku": "SKU-001",
      "name": "Example Product",
      "description": "Example description.",
      "unit_price": "19.95",
      "active": true,
      "created_at": "2026-09-02T10:00:00Z",
      "modified_at": "2026-09-02T10:00:00Z"
    }
  ]
}
```

---

## 12.2 Retrieve Product

```http
GET /api/v1/products/{product_id}/
```

Unknown product:

```http
404 Not Found
```

---

## 12.3 Create Product

```http
POST /api/v1/products/
```

Example:

```json
{
  "sku": "SKU-001",
  "name": "Example Product",
  "description": "Example description.",
  "unit_price": "19.95"
}
```

The API SHALL validate basic request structure.

The product domain/database SHALL remain authoritative for:

* SKU uniqueness
* non-negative pricing
* product invariants

---

## 12.4 Product Price

The current product price is represented by:

```text
Product.unit_price
```

The API SHALL expose the current product price.

When an order line is created, the order line SHALL preserve the applicable price snapshot.

Clients SHALL NOT be allowed to manipulate historical order-line pricing through the product API.

---

# 13. Warehouse API

Warehouses are owned by the `warehouses` application.

## 13.1 List Warehouses

```http
GET /api/v1/warehouses/
```

Example:

```json
{
  "results": [
    {
      "id": "uuid",
      "code": "WH-001",
      "name": "Main Warehouse",
      "location": "Athens",
      "active": true,
      "created_at": "2026-09-02T10:00:00Z",
      "modified_at": "2026-09-02T10:00:00Z"
    }
  ]
}
```

---

## 13.2 Retrieve Warehouse

```http
GET /api/v1/warehouses/{warehouse_id}/
```

Unknown warehouse:

```http
404 Not Found
```

---

## 13.3 Create Warehouse

```http
POST /api/v1/warehouses/
```

Example:

```json
{
  "code": "WH-001",
  "name": "Main Warehouse",
  "location": "Athens"
}
```

Warehouse code uniqueness SHALL be enforced by the domain/database layer.

---

# 14. Inventory API

Inventory is owned by the `inventory` application.

Inventory is a critical consistency boundary.

## 14.1 List Inventory

```http
GET /api/v1/inventory/
```

Example:

```json
{
  "results": [
    {
      "id": "uuid",
      "product_id": "uuid",
      "warehouse_id": "uuid",
      "quantity": 100,
      "reserved_quantity": 25,
      "available_quantity": 75,
      "created_at": "2026-09-02T10:00:00Z",
      "modified_at": "2026-09-02T10:00:00Z"
    }
  ]
}
```

---

## 14.2 Retrieve Inventory Record

```http
GET /api/v1/inventory/{stock_item_id}/
```

The response SHALL expose:

```text
quantity
reserved_quantity
available_quantity
```

The API SHALL calculate or obtain `available_quantity` consistently with:

```text
available_quantity =
    quantity - reserved_quantity
```

---

## 14.3 Inventory Filtering

The inventory API SHOULD support filtering by:

```text
product_id
warehouse_id
```

Example:

```http
GET /api/v1/inventory/?product_id={uuid}
```

and:

```http
GET /api/v1/inventory/?warehouse_id={uuid}
```

Filtering SHALL not change inventory semantics.

---

## 14.4 Inventory Mutation Boundary

Generic inventory mutation is intentionally excluded from the initial CRUD contract.

The API SHALL NOT provide an endpoint equivalent to:

```http
PATCH /api/v1/inventory/{id}/
```

that permits arbitrary modification of:

```text
quantity
reserved_quantity
```

Business operations such as reservation, release and consumption SHALL be exposed through explicit application operations when their corresponding requirements are implemented.

---

# 15. Sales Order API

Sales orders are owned by the `orders` application.

## 15.1 List Orders

```http
GET /api/v1/orders/
```

Example response:

```json
{
  "results": [
    {
      "id": "uuid",
      "customer_id": "uuid",
      "status": "DRAFT",
      "created_at": "2026-09-02T10:00:00Z",
      "modified_at": "2026-09-02T10:00:00Z",
      "lines": []
    }
  ]
}
```

---

## 15.2 Retrieve Order

```http
GET /api/v1/orders/{order_id}/
```

The response SHALL include:

* order identifier
* customer reference
* lifecycle status
* timestamps
* order lines
* line product references
* quantities
* historical unit-price snapshots

Example:

```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "status": "DRAFT",
  "created_at": "2026-09-02T10:00:00Z",
  "modified_at": "2026-09-02T10:00:00Z",
  "lines": [
    {
      "id": "uuid",
      "product_id": "uuid",
      "quantity": 2,
      "unit_price": "19.95"
    }
  ]
}
```

---

# 16. Sales Order Creation

## 16.1 Create Order

```http
POST /api/v1/orders/
```

The API SHALL require the customer and requested order lines.

Example:

```json
{
  "customer_id": "customer-uuid",
  "lines": [
    {
      "product_id": "product-uuid",
      "quantity": 2
    },
    {
      "product_id": "another-product-uuid",
      "quantity": 1
    }
  ]
}
```

The API SHALL require both `customer_id` and `lines`. The `lines` collection SHALL NOT be empty for normal order creation; an empty order SHALL NOT be created through this endpoint. The domain model MAY technically permit an empty DRAFT order, but the initial API creation workflow does not create one.

A newly created order SHALL start in:

```text
DRAFT
```

The client SHALL NOT request:

```json
{
  "status": "CONFIRMED"
}
```

as part of ordinary order creation.

Confirmation is a separate business operation.

---

## 16.2 Order-Line Price Snapshot

The create-order API SHALL NOT treat a client-provided `unit_price` as authoritative.

The applicable product price SHALL be resolved by the application/domain layer and stored on the order line.

Conceptually:

```text
Product.unit_price
       |
       v
Order creation
       |
       v
SalesOrderLine.unit_price
```

This preserves historical order pricing.

---

## 16.3 Order Quantity Validation

Order quantities SHALL be positive.

Malformed or invalid quantities SHALL be rejected before an invalid order is persisted where possible.

The database constraint remains the final integrity boundary.

---

## 16.4 Empty Orders

The domain model MAY technically permit an order to exist in `DRAFT` state before it contains lines.

However, the API creation workflow defined in Section 16.1 SHALL NOT create an empty order. The `lines` collection is required and SHALL contain at least one line for normal order creation.

Regardless of how a `DRAFT` order is created, an order SHALL NOT be confirmed without at least one line.

---

# 17. Sales Order Update

Only `DRAFT` orders SHALL be modified through the generic order update endpoint.

The API MAY expose:

```http
PATCH /api/v1/orders/{order_id}/
```

for permitted draft modifications.

The following fields SHALL NOT be accepted:

- `status` – lifecycle transitions SHALL use explicit endpoints
- `created_at` and `modified_at` – SHALL NOT be client‑controlled
- `unit_price` – SHALL NOT be client‑controlled (historical pricing is resolved by the domain)
- inventory fields – SHALL NOT be accepted

Completed, shipped, confirmed and cancelled orders SHALL NOT be modified through this endpoint.

Line modifications SHALL follow the explicitly defined order‑line contract rather than arbitrary nested mutation. Until the order‑line modification contract is separately defined, the API SHALL NOT claim unrestricted nested line mutation.

The endpoint SHALL NOT permit unrestricted lifecycle changes.

For example:

```json
{
  "status": "CONFIRMED"
}
```

is not a valid generic update mechanism.

Lifecycle transitions SHALL use explicit business endpoints.

---

# 18. Order Confirmation API

Order confirmation is the first explicitly defined critical business operation in API v1.

## 18.1 Endpoint

```http
POST /api/v1/orders/{order_id}/confirm/
```

The endpoint SHALL invoke:

```python
confirm_order(order_id)
```

The API layer SHALL pass the order identifier to the application service.

---

## 18.2 Confirmation Preconditions

Confirmation SHALL succeed only when:

1. the order exists
2. the order is `DRAFT`
3. the customer is active
4. the order contains at least one line
5. all line quantities are valid
6. all referenced products are active
7. sufficient available stock exists for all required products

---

## 18.3 Confirmation Transaction

The API endpoint SHALL NOT manage individual inventory writes.

The application service owns the transaction.

The complete operation is:

```text
HTTP POST
   |
   v
confirm_order(order_id)
   |
   v
transaction.atomic()
   |
   +--> lock order
   |
   +--> validate customer
   |
   +--> validate lines
   |
   +--> aggregate required quantities
   |
   +--> lock relevant StockItems
   |
   +--> re-check availability
   |
   +--> reserve inventory
   |
   +--> set order CONFIRMED
   |
   +--> COMMIT
```

The API SHALL therefore inherit the atomicity guarantee of the application service.

---

## 18.4 Successful Confirmation

Successful confirmation SHALL return:

```http
200 OK
```

with the updated order representation.

Example:

```json
{
  "id": "uuid",
  "customer_id": "customer-uuid",
  "status": "CONFIRMED",
  "created_at": "2026-09-02T10:00:00Z",
  "modified_at": "2026-09-02T10:05:00Z",
  "lines": [
    {
      "id": "uuid",
      "product_id": "product-uuid",
      "quantity": 2,
      "unit_price": "19.95"
    }
  ]
}
```

The response SHALL represent the committed state.

---

## 18.5 Order Not Found

If the requested order does not exist:

```http
404 Not Found
```

Example:

```json
{
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "The requested order does not exist."
  }
}
```

---

## 18.6 Invalid Order State

If the order is not `DRAFT`:

```http
409 Conflict
```

Example:

```json
{
  "error": {
    "code": "INVALID_ORDER_STATE",
    "message": "The order cannot be confirmed from its current state."
  }
}
```

This includes concurrent confirmation of the same order where the second operation observes that the order has already become `CONFIRMED`.

---

## 18.7 Inactive Customer

If the order customer is inactive:

```http
409 Conflict
```

Example:

```json
{
  "error": {
    "code": "INACTIVE_CUSTOMER",
    "message": "The order customer is inactive."
  }
}
```

---

## 18.8 Order Without Lines

If the order contains no lines:

```http
409 Conflict
```

Example:

```json
{
  "error": {
    "code": "ORDER_HAS_NO_LINES",
    "message": "An order must contain at least one line before confirmation."
  }
}
```

---

## 18.9 Invalid Quantity

If an invalid quantity reaches the application service:

```http
400 Bad Request
```

Example:

```json
{
  "error": {
    "code": "INVALID_ORDER_QUANTITY",
    "message": "Order line quantity must be greater than zero."
  }
}
```

Database constraints remain authoritative for persisted order-line invariants.

---

## 18.10 Inactive Product

If an order contains an inactive product:

```http
409 Conflict
```

Example:

```json
{
  "error": {
    "code": "INACTIVE_PRODUCT",
    "message": "The order contains an inactive product."
  }
}
```

---

## 18.11 Insufficient Stock

If available inventory cannot satisfy the order:

```http
409 Conflict
```

Example:

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Insufficient stock to confirm the order."
  }
}
```

The failed confirmation SHALL leave:

```text
Order = DRAFT
```

and:

```text
Inventory = unchanged
```

---

# 19. Multi-Warehouse Inventory Semantics

The current architecture does not associate a warehouse directly with a sales order or sales order line.

Therefore, the confirmation API SHALL NOT accept:

```json
{
  "warehouse_id": "..."
}
```

as part of the current order-line confirmation contract.

For each required product:

```text
available quantity =
sum of available StockItems for that product
```

When sufficient stock exists across multiple warehouses, allocation SHALL be deterministic.

The current service contract defines allocation by:

```text
product_id
StockItem.id ascending
```

The API does not expose internal allocation decisions as client-controlled input.

The API MAY expose resulting inventory state where appropriate, but clients SHALL NOT choose arbitrary stock rows through the order confirmation request.

---

# 20. Duplicate Product Lines

Multiple order lines may reference the same product.

Before inventory availability is evaluated, the application service SHALL aggregate required quantities by product.

Example:

```text
Line 1: Product A × 3
Line 2: Product A × 4
```

The inventory requirement is:

```text
Product A × 7
```

The API SHALL preserve the individual order-line representation while the application service handles the aggregate inventory requirement.

---

# 21. Order Cancellation API

The current lifecycle permits:

```text
DRAFT -> CANCELLED
```

Only.

The explicit endpoint is:

```http
POST /api/v1/orders/{order_id}/cancel/
```

The endpoint SHALL invoke an application-level cancellation operation.

It SHALL NOT implement cancellation by directly setting the status field in the API view.

Cancellation of:

```text
CONFIRMED
SHIPPED
COMPLETED
CANCELLED
```

orders SHALL be rejected.

Because the current requirements allow cancellation only from `DRAFT`, cancellation does not release an existing reservation.

The detailed cancellation service contract SHALL be defined and approved before implementation.

---

# 22. Shipment API

Shipment is a separate business operation.

The conceptual endpoint is:

```http
POST /api/v1/orders/{order_id}/ship/
```

The operation SHALL only be permitted from:

```text
CONFIRMED
```

The shipment operation SHALL:

1. validate order state
2. verify required reservation
3. consume physical inventory
4. reduce reserved quantity
5. transition order to `SHIPPED`
6. commit atomically

The API SHALL invoke an application service responsible for these operations.

The API SHALL NOT directly manipulate inventory fields.

The detailed shipment service and API contract SHALL be finalized before implementation.

---

# 23. Completion API

Completion is a separate business operation.

The conceptual endpoint is:

```http
POST /api/v1/orders/{order_id}/complete/
```

The operation SHALL only be permitted from:

```text
SHIPPED
```

Completion SHALL transition the order to:

```text
COMPLETED
```

Completion SHALL NOT perform another inventory deduction.

A completed order SHALL be immutable under normal business operations.

The detailed completion service and API contract SHALL be finalized before implementation.

---

# 24. Order Lifecycle API

The valid lifecycle is:

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

The public lifecycle operations are conceptually:

### Current API v1 lifecycle operations

```text
POST /api/v1/orders/{id}/confirm/
POST /api/v1/orders/{id}/cancel/
```

### Future API milestones (design-only)

```text
POST /api/v1/orders/{id}/ship/
POST /api/v1/orders/{id}/complete/
```

The `ship` and `complete` endpoints are design-only until their application services, tests and verification evidence exist. Their implementation SHALL NOT be treated as part of the current milestone.

The API SHALL NOT expose a generic endpoint for arbitrary state transitions.

For example, the following SHALL NOT be supported:

```http
PATCH /api/v1/orders/{id}/
{
  "status": "SHIPPED"
}
```

---

# 25. Order Immutability

Once an order reaches:

```text
COMPLETED
```

normal API operations SHALL NOT permit modification of its business data.

The API SHALL reject attempts to mutate completed orders.

The exact HTTP representation of this rejection SHALL use the common business error model.

---

# 26. Pagination

Collection endpoints SHALL support pagination.

The initial representation is:

```json
{
  "count": 100,
  "next": "...",
  "previous": null,
  "results": []
}
```

The exact page-size defaults and maximums SHALL be configured during implementation.

The API contract SHALL not require clients to depend on a specific pagination implementation library.

---

# 27. Filtering

Where useful, collection endpoints MAY support query-parameter filtering.

Initial filtering candidates include:

### Customers

```text
active
```

### Products

```text
active
sku
```

### Warehouses

```text
active
code
```

### Inventory

```text
product_id
warehouse_id
```

### Orders

```text
customer_id
status
```

Filtering SHALL not bypass authorization or business rules.

Filtering semantics SHALL be documented when implemented.

---

# 28. Ordering

Collection endpoints MAY expose deterministic ordering.

Where an endpoint exposes database-backed resources, the API SHOULD use stable ordering to avoid inconsistent pagination.

The public API SHALL not expose internal locking order as a client-controlled option.

In particular, the deterministic StockItem allocation order used by confirmation is an application-service concern, not an API query parameter.

---

# 29. Concurrency Semantics

The API SHALL rely on application/database transaction boundaries for concurrency safety.

For order confirmation:

```text
Request A
   |
   v
lock order
   |
   v
lock stock
   |
   v
reserve
   |
   v
commit

Request B
   |
   v
wait for lock
   |
   v
observe current order state
   |
   v
success or business error
```

Concurrent confirmation requests for the same order SHALL NOT create duplicate reservations.

Concurrent confirmations of different orders competing for the same inventory SHALL be serialized through appropriate database row locking and availability re-evaluation.

The API SHALL expose the resulting business outcome rather than implementation-specific database locking details.

---

# 30. Idempotency

The API SHALL distinguish between:

```text
HTTP retry safety
```

and:

```text
business-operation idempotency
```

The current order confirmation implementation protects against duplicate confirmation through order-state validation and transactional locking.

A second confirmation of an already confirmed order is therefore a business conflict:

```http
409 Conflict
```

with:

```text
INVALID_ORDER_STATE
```

A general-purpose `Idempotency-Key` mechanism is not required by the initial core order API contract.

It MAY be introduced later if an explicit requirement establishes the need.

---

# 31. Webhook API Boundary

External payment events belong to the `integrations` application.

The conceptual endpoint is:

```http
POST /api/v1/integrations/payment/webhook/
```

The endpoint SHALL:

1. receive external event data
2. validate the external request
3. identify the external event
4. enforce event-id uniqueness/idempotency
5. invoke the appropriate application service
6. persist processing state atomically

The webhook endpoint SHALL NOT directly modify order state in the HTTP handler.

The detailed webhook request schema, authentication/signature mechanism and event-processing service SHALL be specified as a separate integration milestone.

---

# 32. CSV Import Boundary

CSV import is an operational capability defined by the broader requirements.

It SHALL NOT be implemented as an unrestricted generic API upload endpoint unless explicitly required.

The import workflow SHALL have its own application-level validation and error handling.

If an HTTP import endpoint is introduced, it SHALL use an explicit endpoint and application service rather than embedding import logic in a serializer or view.

The exact CSV API contract is deferred until the import requirements are implemented.

---

# 33. API Validation Responsibility

Validation is divided into three layers.

```text
                 API
                  |
        Transport validation
                  |
                  v
        Application Service
                  |
         Business validation
                  |
                  v
             Database
                  |
          Integrity constraints
```

## 33.1 API Layer

Responsible for:

* JSON syntax
* required request fields
* basic type validation
* malformed identifiers
* request representation
* authentication
* authorization
* HTTP-specific validation

## 33.2 Application Layer

Responsible for:

* lifecycle rules
* customer state
* product state
* inventory availability
* business operation preconditions
* transaction coordination
* concurrency behavior

## 33.3 Database Layer

Responsible for:

* uniqueness
* non-negative persisted quantities
* positive order-line quantities
* non-negative prices
* foreign-key integrity
* persisted state constraints

No single layer SHALL be treated as the exclusive enforcement mechanism for critical invariants.

---

# 34. Security Requirements

The API implementation SHALL:

* require authentication for protected ERP operations
* enforce authorization
* validate incoming data
* avoid exposing internal exception details
* avoid exposing database internals
* avoid returning sensitive credentials or secrets
* use environment-based configuration for secrets
* avoid trusting client-provided calculated business values
* preserve transactional business boundaries

Unexpected exceptions SHALL produce controlled server errors without exposing stack traces in production responses.

---

# 35. API Logging Boundary

Application-level logging is part of the broader architecture.

The API layer SHOULD provide useful request-level context for operational diagnostics.

Logging SHALL NOT contain:

* passwords
* authentication secrets
* tokens
* credentials
* unnecessary sensitive customer data

Business operations SHALL remain observable without coupling business logic to HTTP logging.

The detailed logging policy is outside this initial API contract.

---

# 36. API and Application-Service Separation

The following pattern SHALL be maintained:

```text
                 REST API
                    |
        +-----------+-----------+
        |                       |
    Serializer              Auth/Authz
        |                       |
        +-----------+-----------+
                    |
                    v
            Application Service
                    |
          +---------+---------+
          |                   |
        Orders            Inventory
          |                   |
          +---------+---------+
                    |
                    v
                PostgreSQL
```

The API SHALL NOT:

* call `StockItem.save()` to implement confirmation
* calculate reservation allocations itself
* change order lifecycle state directly
* implement transaction workflows
* duplicate service-layer business validation

---

# 37. API Testing Strategy

API functionality SHALL be tested independently from core service tests.

The test architecture SHALL distinguish:

```text
Unit tests
    |
    +--> business logic

Integration tests
    |
    +--> database/application interactions

API tests
    |
    +--> HTTP request/response contract

Webhook tests
    |
    +--> external event boundary
```

For the order confirmation API, API tests SHALL eventually verify at minimum:

1. successful confirmation
2. unknown order
3. invalid order state
4. inactive customer
5. empty order
6. inactive product
7. invalid quantity
8. insufficient stock
9. atomic failure behavior
10. authenticated access
11. unauthorized access
12. response/error schema

The existing 18 service-level confirmation tests remain the authoritative current verification of the application service itself.

The API layer SHALL not replace those tests.

---

# 38. API Test Independence

API tests SHALL exercise the HTTP boundary.

They SHALL NOT be considered a substitute for application-service tests.

For example:

```text
tests/orders/test_confirmation.py
```

verifies the application service.

Future API tests SHALL verify:

```text
tests/api/test_orders.py
```

or an equivalent API test structure.

The two layers provide different evidence.

---

# 39. Requirements Traceability

The API specification SHALL be traceable to the ERP requirements.

The initial API mapping is:

| Requirement       | API Capability                         | Status                      |
| ----------------- | -------------------------------------- | --------------------------- |
| ERP-REQ-001 – 011 | Customer/Product/Warehouse foundations | Draft                       |
| ERP-REQ-012       | Sales order creation                   | Draft                       |
| ERP-REQ-013       | Sales order lines                      | Draft                       |
| ERP-REQ-014       | Positive quantities                    | Draft                       |
| ERP-REQ-015       | Price snapshot                         | Draft                       |
| ERP-REQ-016       | Draft state                            | Draft                       |
| ERP-REQ-017       | Order confirmation                     | Draft API; service verified |
| ERP-REQ-018       | Stock reservation                      | Draft API; service verified |
| ERP-REQ-019       | Insufficient stock                     | Draft API; service verified |
| ERP-REQ-020       | Order cancellation                     | Draft                       |
| ERP-REQ-021       | Shipment                               | Draft                       |
| ERP-REQ-022       | Completion                             | Draft                       |
| ERP-REQ-023       | Completed order immutability           | Draft                       |
| ERP-REQ-024+      | Remaining ERP capabilities             | Future API milestones       |

The API specification itself SHALL NOT change requirement verification status.

Requirement status remains controlled by:

```text
docs/traceability.md
```

The API document describes intended transport coverage; it does not constitute implementation evidence.

---

# 40. API Requirements and Verification Lifecycle

API requirements SHALL follow the same evidence lifecycle as the rest of the project:

```text
DESIGNED
   |
   v
IMPLEMENTED
   |
   v
TESTED
   |
   v
VERIFIED
```

Definitions:

### DESIGNED

The API contract is documented and approved.

### IMPLEMENTED

The corresponding API endpoint exists in production source.

### TESTED

Automated API tests exercise the endpoint and pass.

### VERIFIED

Implementation, tests and requirement evidence have been reviewed and are reproducible.

An endpoint SHALL NOT be marked VERIFIED merely because:

* its URL exists
* a Django view exists
* a serializer exists
* `manage.py check` succeeds
* the endpoint starts successfully
* manual testing succeeds

Automated reproducible evidence is required.

---

# 41. API Out of Scope for v1.0

The following are intentionally excluded from the initial API implementation scope unless separately approved:

```text
Real payment gateway integration
Real shipping provider integration
Accounting
Payroll
Tax calculation
Partial shipments
Partial fulfillment
Reservation expiration
Return processing
Advanced reporting
Real-time event streaming
Generic arbitrary inventory mutation
Generic arbitrary order state mutation
```

The following future lifecycle capabilities also remain outside the current contract:

```text
CONFIRMED -> CANCELLED
Reservation expiration
Partial shipment
Return processing
```

They SHALL require explicit requirements before implementation.

---

# 42. Implementation Boundary

The API implementation is expected to use the Django project structure:

```text
config/
    urls.py

apps/
    accounts/
    customers/
    products/
    warehouses/
    inventory/
    orders/
    integrations/
```

API-specific implementation MAY be organized within the owning Django applications.

The API implementation SHALL preserve domain ownership.

For example:

```text
apps/orders/
    views / endpoints
    serializers
    services
```

rather than placing order business logic inside:

```text
config/
```

---

# 43. Initial Endpoint Inventory

The intended API v1 surface is summarized below. Endpoints are grouped by implementation scope.

## Core v1 Implementation Scope

| Domain       | Method | Endpoint                                | Purpose                     |
| ------------ | ------ | --------------------------------------- | --------------------------- |
| Customers    | GET    | `/api/v1/customers/`                    | List customers              |
| Customers    | GET    | `/api/v1/customers/{id}/`               | Retrieve customer           |
| Customers    | POST   | `/api/v1/customers/`                    | Create customer             |
| Products     | GET    | `/api/v1/products/`                     | List products               |
| Products     | GET    | `/api/v1/products/{id}/`                | Retrieve product            |
| Products     | POST   | `/api/v1/products/`                     | Create product              |
| Warehouses   | GET    | `/api/v1/warehouses/`                   | List warehouses             |
| Warehouses   | GET    | `/api/v1/warehouses/{id}/`              | Retrieve warehouse          |
| Warehouses   | POST   | `/api/v1/warehouses/`                   | Create warehouse            |
| Inventory    | GET    | `/api/v1/inventory/`                    | List stock                  |
| Inventory    | GET    | `/api/v1/inventory/{id}/`               | Retrieve stock item         |
| Orders       | GET    | `/api/v1/orders/`                       | List orders                 |
| Orders       | GET    | `/api/v1/orders/{id}/`                  | Retrieve order              |
| Orders       | POST   | `/api/v1/orders/`                       | Create draft order with lines |
| Orders       | PATCH  | `/api/v1/orders/{id}/`                  | Update permitted draft data |
| Orders       | POST   | `/api/v1/orders/{id}/confirm/`          | Confirm and reserve stock   |
| Orders       | POST   | `/api/v1/orders/{id}/cancel/`           | Cancel draft order          |

## Future API Milestones (design‑only)

| Domain       | Method | Endpoint                                | Purpose                     |
| ------------ | ------ | --------------------------------------- | --------------------------- |
| Orders       | POST   | `/api/v1/orders/{id}/ship/`             | Ship confirmed order        |
| Orders       | POST   | `/api/v1/orders/{id}/complete/`         | Complete shipped order      |
| Integrations | POST   | `/api/v1/integrations/payment/webhook/` | External payment event      |
| (CSV Import) | POST   | (not yet specified)                     | Legacy customer import      |

Endpoints listed in the Future API Milestones section are design‑only and SHALL NOT be implemented as part of the current v1 milestone. They require explicit service contracts, tests and verification evidence before implementation.

---

# 44. Current Implementation Status

At the time of this document's creation:

```text
API implementation:                    NOT STARTED
API contract:                         DRAFT
Order confirmation application service: IMPLEMENTED
Order confirmation service tests:       18 PASS
Order confirmation requirements:        VERIFIED
```

The currently verified service entry point is:

```python
confirm_order(order_id)
```

implemented at:

```text
apps/orders/services.py
```

The service-level verification is documented independently and SHALL remain separate from API verification.

---

# 45. Recommended Implementation Sequence

API implementation SHALL proceed incrementally.

Recommended sequence:

```text
1. Approve API specification
        |
        v
2. Implement API foundation
        |
        v
3. Implement authentication / authorization boundary
        |
        v
4. Implement Customer/Product/Warehouse read APIs
        |
        v
5. Implement Sales Order creation/retrieval
        |
        v
6. Implement Order Confirmation endpoint
        |
        v
7. Add API tests
        |
        v
8. Reconcile traceability
        |
        v
9. Verify API behavior
        |
        v
10. Implement remaining lifecycle endpoints
```

No API implementation SHALL be treated as verified before the corresponding automated API tests and traceability evidence exist.

---

# 46. Design Decisions

The following decisions are intentional.

## 46.1 Explicit Confirmation Endpoint

Chosen:

```http
POST /api/v1/orders/{id}/confirm/
```

instead of generic status mutation.

Reason:

Order confirmation is a transactional business operation involving inventory.

---

## 46.2 Structured Business Errors

Chosen:

```json
{
  "error": {
    "code": "...",
    "message": "..."
  }
}
```

Reason:

Clients need stable machine-readable business error codes without exposing internal Python exception classes.

---

## 46.3 No Direct Inventory Field Mutation

Chosen:

```text
No generic PATCH for StockItem quantities/reservations.
```

Reason:

Inventory is a consistency boundary and mutations must remain under application-level business operations.

---

## 46.4 Client Does Not Control Historical Price

Chosen:

```text
order creation -> resolve current Product.unit_price
                 -> persist SalesOrderLine.unit_price
```

Reason:

The order line represents a historical price snapshot.

---

## 46.5 Warehouse Is Not an Order-Line Input

Chosen:

```text
No warehouse_id on SalesOrderLine API contract.
```

Reason:

The current domain model does not associate an order line with a specific warehouse. Inventory allocation remains an application-service concern.

---

## 46.6 API Does Not Replace Service Tests

Chosen:

```text
service tests + API tests
```

Reason:

Business logic and HTTP transport provide separate verification boundaries.

---

# 47. Approval

This document is initially created as:

```text
Status: Draft
```

Before API implementation begins, the specification SHALL be reviewed for:

* endpoint completeness
* requirements coverage
* authentication/authorization correctness
* error semantics
* lifecycle semantics
* inventory boundaries
* request/response representations
* traceability
* consistency with the architecture specification

After review, the document MAY transition to:

```text
Status: Approved
```

Only after approval SHALL API implementation begin.

---

# 48. Change History

| Date       | Change                                       | Reference                |
| ---------- | -------------------------------------------- | ------------------------ |
| 2026-09-02 | Initial API Specification Draft v1.0 created | Current design milestone |
| 2026-09-02 | Revision 1 — tightened draft-order mutation semantics, clarified order creation, separated current v1 API scope from future lifecycle/integration milestones | API contract review      |
| 2026-09-02 | API Specification v1.0 Revision 1 approved | Formal API design review |

---

# 49. Final API Contract Summary

The API is intentionally designed as a thin interface over application services.

The central operational pattern is:

```text
Client
  |
  | HTTP
  v
REST API
  |
  | validate / authenticate / authorize
  v
Application Service
  |
  | business rules / transaction
  v
Domain
  |
  v
PostgreSQL
```

For order confirmation:

```text
POST /api/v1/orders/{id}/confirm/
              |
              v
       confirm_order(id)
              |
              v
       Atomic transaction
              |
       +------+------+
       |             |
       v             v
   SalesOrder    Inventory
       |             |
       +------+------+
              |
              v
           COMMIT
```

The API SHALL expose business capabilities without duplicating their implementation.

The API contract therefore preserves the project's primary engineering principle:

```text
Requirements
     ↓
Architecture
     ↓
Application Services
     ↓
API Contract
     ↓
API Implementation
     ↓
Automated Tests
     ↓
Verification
```

This specification defines the intended API boundary but does not itself constitute implementation or verification evidence.
