# Order Confirmation Service — Specification

**Document:** Order Confirmation Service Specification  
**Project:** Django ERP Operations Platform  
**Version:** 1.0  
**Status:** Approved / Implemented
**Requirements Baseline:** `14db353`  
**Database Design Baseline:** `c5a9e31`  
**Model Specification Baseline:** `13d0a8d`  
**Last Updated:** 2026-09-02

---

## 1. Purpose

This document defines the **contract** and **test specification** for the
order confirmation service.

It is the authoritative reference for:

- What the service must do
- What it must reject
- How it must behave under concurrent access
- What tests must verify before implementation is considered complete

The service is implemented in:

```text
apps/orders/services.py
```

The implementation must preserve all requirements, database constraints, and
model semantics already documented in the approved design specifications.

---

## 2. Service Identity

**Service name:** `confirm_order`

**Location:** `apps/orders/services.py`

**Signature:**

```python
def confirm_order(order_id: UUID) -> SalesOrder:
    """
    Confirm a draft sales order.

    Raises:
        OrderNotFound: If order_id does not exist.
        InvalidOrderState: If order is not in DRAFT state.
        InactiveCustomer: If the order's customer is inactive.
        OrderHasNoLines: If the order has no lines.
        InvalidOrderQuantity: If any line quantity <= 0.
        InactiveProduct: If any line references an inactive product.
        InsufficientStock: If any product's available stock is insufficient.

    Returns:
        SalesOrder: The confirmed order with status CONFIRMED.
    """
```

All error types are application-defined business errors as specified in
ERP-REQ-041.

---

## 3. Preconditions

Before confirming an order, the service must verify:

| Precondition                    | Source                          |
| ------------------------------- | ------------------------------- |
| Order exists                    | Domain invariant                |
| Order status is `DRAFT`         | ERP-REQ-016, ERP-REQ-017        |
| Customer is active              | ERP-REQ-003, ERP-REQ-017        |
| Order contains at least one line | ERP-REQ-017                    |
| All line quantities > 0         | ERP-REQ-014, ERP-REQ-017        |
| All products are active         | Product domain invariant        |
| Sufficient available stock exists | ERP-REQ-017, ERP-REQ-019      |

If any precondition fails, the transaction must roll back and the order must
remain in its original state.

---

## 4. Postconditions

After successful confirmation:

| Postcondition                         | Source                          |
| ------------------------------------- | ------------------------------- |
| Order status = `CONFIRMED`            | ERP-REQ-017                     |
| Inventory reserved for each line      | ERP-REQ-018                     |
| `reserved_quantity` increases by line quantity | ERP-REQ-018         |
| `quantity` remains unchanged          | ERP-REQ-018                     |
| `available_quantity` decreases by line quantity | Derived invariant   |
| All changes committed atomically      | ERP-REQ-011, ERP-REQ-018       |

The following must **never** be committed:

```text
Order = CONFIRMED, Inventory = not reserved
Inventory = reserved, Order = DRAFT
```

---

## 5. Transaction Boundary

The service must execute inside a single database transaction:

```python
with transaction.atomic():
    # 1. Lock SalesOrder row (FOR UPDATE)
    # 2. Validate order state and preconditions
    # 3. Lock required StockItem rows (FOR UPDATE)
    # 4. Re-check availability under lock
    # 5. Reserve stock
    # 6. Transition order to CONFIRMED
    # 7. Commit
```

All operations that modify either inventory or order state must be part of
the same atomic unit.

Failure of any step must result in:

```text
ROLLBACK
```

---

## 6. Concurrency Strategy

### 6.1 Row-Level Locking

The service must use `select_for_update()` to lock:

1. The `SalesOrder` row for the given `order_id`
2. All `StockItem` rows required by the order

Locking must occur **after** the order row lock, and **before** any
availability re-check or reservation update.

### 6.2 Lock Scope

Lock all `StockItem` records for the products referenced by the order lines.

The implementation **does not** require a warehouse to be specified on the
order line. Instead, the service calculates the total required quantity per
product and then allocates stock across all available warehouses using the
deterministic allocation rule defined in Section 7.2.

If no stock exists for a product (i.e., no `StockItem` records), the service
must treat that as `quantity = 0` (insufficient stock).

### 6.3 Re-check After Lock

After acquiring locks, the service must **re-evaluate** available quantities.

This prevents two concurrent transactions from both observing available stock
that only one can reserve.

### 6.4 Deterministic Ordering (Prevent Deadlocks)

To prevent deadlocks, stock rows must be locked in a deterministic order.

The service must lock rows in ascending `StockItem.id` order.

This applies regardless of the order in which lines appear on the sales order.

If a product has multiple stock items across warehouses, they must be locked
in ID order.

---

## 7. Stock Allocation Rules

### 7.1 Single Product, Multiple Lines

If a sales order contains multiple lines for the same product, the service
must aggregate quantities before checking availability.

### 7.2 Multiple Warehouses

If the same product exists in multiple warehouses, the service must allocate
stock using the following deterministic rule:

```text
For each product:
    Order StockItem rows by id ASC
    For each StockItem:
        If required_quantity <= available_quantity:
            Reserve from this StockItem
            Reduce required_quantity by reserved amount
        If required_quantity == 0:
            Stop
    If required_quantity > 0:
        Raise InsufficientStock
```

This ensures deterministic behavior across executions.

### 7.3 No Partial Allocation

If insufficient stock exists for any product, the entire confirmation must
fail and roll back.

Partial allocation is not permitted.

---

## 8. Error Handling

All business errors must raise application-defined exceptions that inherit
from a common base (e.g., `BusinessError`).

Error types (as per the approved contract):

| Error                     | Condition                                      |
| ------------------------- | ---------------------------------------------- |
| `OrderNotFound`           | `order_id` does not exist                      |
| `InvalidOrderState`       | Order status is not `DRAFT`                    |
| `InactiveCustomer`        | `Customer.active == False`                     |
| `OrderHasNoLines`         | Order has zero lines                           |
| `InvalidOrderQuantity`    | Line quantity <= 0                             |
| `InactiveProduct`         | `Product.active == False`                      |
| `InsufficientStock`       | Available stock < required quantity            |

All errors must contain sufficient diagnostic information without exposing
internal implementation details or secrets.

---

## 9. Test Specification

### 9.1 Test Environment

All tests must run against PostgreSQL.

Tests must use `pytest-django` and the database must be reset between tests
using transactions or a test database.

### 9.2 Success Cases

#### TC-001 — Confirm valid draft order

**Preconditions:**

- Order exists
- Order status is `DRAFT`
- Customer is active
- Order has at least one line
- All quantities > 0
- All products are active
- Sufficient stock available

**Action:**

`confirm_order(order_id)`

**Expected:**

- Order status becomes `CONFIRMED`
- Stock reservation applied
- `reserved_quantity` increases by line quantities
- `quantity` remains unchanged
- All changes committed
- Returns the confirmed order

---

#### TC-002 — Reserve stock for a single product

**Preconditions:**

- One product
- Stock available: quantity = 100, reserved = 0
- Order line: quantity = 25

**Action:**

`confirm_order(order_id)`

**Expected:**

- `reserved_quantity` = 25
- `quantity` = 100
- `available_quantity` = 75

---

#### TC-003 — Reserve stock across multiple warehouses

**Preconditions:**

- Product exists in two warehouses
- Warehouse A: quantity = 30, reserved = 0
- Warehouse B: quantity = 20, reserved = 0
- Order line: quantity = 40

**Action:**

`confirm_order(order_id)`

**Expected (assuming A has lower StockItem.id):**

- Warehouse A: reserved_quantity = 30, quantity = 30
- Warehouse B: reserved_quantity = 10, quantity = 20
- Total reserved = 40

---

#### TC-004 — Aggregate multiple lines for the same product

**Preconditions:**

- One product, one warehouse
- Stock: quantity = 100, reserved = 0
- Order has two lines for the same product: 30 + 20 = 50 total

**Action:**

`confirm_order(order_id)`

**Expected:**

- `reserved_quantity` = 50
- `quantity` = 100

---

#### TC-005 — Persist order status and reservations atomically

**Preconditions:**

- Valid order

**Action:**

`confirm_order(order_id)`

**Expected:**

- `SalesOrder.status` = `CONFIRMED`
- `StockItem.reserved_quantity` updated
- Both changes visible in the same committed transaction

---

### 9.3 Validation Failures

#### TC-006 — Order does not exist

**Action:**

`confirm_order(non_existent_id)`

**Expected:**

- `OrderNotFound`
- No changes to database

---

#### TC-007 — Order is not DRAFT

**Preconditions:**

- Order status = `CONFIRMED` (or any non-DRAFT state)

**Action:**

`confirm_order(order_id)`

**Expected:**

- `InvalidOrderState`
- No changes to database
- Order status remains unchanged

---

#### TC-008 — Customer is inactive

**Preconditions:**

- `Customer.active = False`

**Action:**

`confirm_order(order_id)`

**Expected:**

- `InactiveCustomer`
- Order remains `DRAFT`
- No inventory changes

---

#### TC-009 — Order has no lines

**Preconditions:**

- Valid order with zero `SalesOrderLine` records

**Action:**

`confirm_order(order_id)`

**Expected:**

- `OrderHasNoLines`
- Order remains `DRAFT`
- No inventory changes

---

#### TC-010 — Invalid line quantity

**Preconditions:**

- Order line quantity = 0 (or negative)

**Action:**

`confirm_order(order_id)`

**Expected:**

- `InvalidOrderQuantity`
- Order remains `DRAFT`
- No inventory changes

---

#### TC-011 — Inactive product

**Preconditions:**

- One or more order lines reference `Product.active = False`

**Action:**

`confirm_order(order_id)`

**Expected:**

- `InactiveProduct`
- Order remains `DRAFT`
- No inventory changes

---

#### TC-012 — Insufficient stock

**Preconditions:**

- Stock available = 10
- Order line quantity = 15

**Action:**

`confirm_order(order_id)`

**Expected:**

- `InsufficientStock`
- Order remains `DRAFT`
- No inventory changes

---

### 9.4 Rollback

#### TC-013 — Insufficient stock leaves order DRAFT

**Preconditions:**

- Available stock = 10
- Order line quantity = 15

**Action:**

`confirm_order(order_id)`

**Expected:**

- `InsufficientStock`
- Order status remains `DRAFT`
- No partial reservation applied

---

#### TC-014 — Insufficient stock leaves inventory unchanged

**Preconditions:**

- Available stock = 10
- Order line quantity = 15

**Action:**

`confirm_order(order_id)`

**Expected:**

- `InsufficientStock`
- `StockItem.quantity` unchanged
- `StockItem.reserved_quantity` unchanged

---

#### TC-015 — Failure on later product rolls back earlier reservations

**Preconditions:**

- Product A: sufficient stock (100)
- Product B: insufficient stock (5 required, 3 available)

**Action:**

`confirm_order(order_id)`

**Expected:**

- `InsufficientStock`
- Product A reservation rolled back
- Product B unchanged
- Order remains `DRAFT`

---

### 9.5 Concurrency

#### TC-016 — Concurrent confirmation cannot double-confirm same order

**Preconditions:**

- Valid order with sufficient stock

**Action:**

- Transaction A: begins confirmation
- Transaction B: begins confirmation on the same order
- Transaction A: commits
- Transaction B: attempts to commit

**Expected:**

- Transaction A succeeds, order becomes `CONFIRMED`
- Transaction B fails with `InvalidOrderState` (since the order is no longer DRAFT)
- No double confirmation
- No duplicate reservations

---

#### TC-017 — Inventory availability is re-evaluated after row locking

**Preconditions:**

- Stock: quantity = 10, reserved = 0
- Order A: requires 7
- Order B: requires 7

**Action (concurrent):**

- Transaction A: begins confirmation, locks stock, sees 10 available, reserves 7
- Transaction B: waits for lock
- Transaction A: commits, stock available = 3
- Transaction B: acquires lock, re-evaluates, sees available = 3

**Expected:**

- Transaction A succeeds
- Transaction B fails with `InsufficientStock`
- No overselling

---

### 9.6 Deterministic Allocation

#### TC-018 — Stock allocation follows StockItem.id ascending order

**Preconditions:**

- Product exists in two warehouses
- StockItem X (id = 100): quantity = 50, reserved = 0
- StockItem Y (id = 200): quantity = 50, reserved = 0
- Order line: quantity = 70

**Action:**

`confirm_order(order_id)`

**Expected:**

- StockItem X (lower ID) reserves 50
- StockItem Y reserves 20
- Allocation is deterministic and repeatable

**Repeat with reversed scenario:**

- If the same test is run multiple times, the allocation result is identical

---

## 10. Non-Functional Requirements

### 10.1 Idempotency

Confirming an order is **not** idempotent because it changes state.

The service must protect against double confirmation through:

- Precondition checks (order must be `DRAFT`)
- Row-level locking (order row lock prevents concurrent modification)
- Atomic transactions

### 10.2 Performance

The service must not perform unnecessary database queries.

Specific query counts are not fixed as a contract; they are implementation details.
However, the service must avoid N+1 problems and must not issue queries inside loops.

### 10.3 Logging

Logging is handled at the application and API layer (ERP-REQ-044).
This service itself does not include logging as a mandatory part of its contract.
Operational logging of confirmation attempts, successes, and failures will be
added at the API or middleware level as part of the overall logging strategy.

---

## 11. Implementation Sequence

The recommended implementation order is:

1. Define error types in `apps/orders/exceptions.py`
2. Implement `confirm_order` service in `apps/orders/services.py`
3. Write tests per this specification
4. Run tests against PostgreSQL
5. Refactor until all tests pass

---

## 12. Verification Criteria

The service is considered complete when:

1. All test cases (TC-001 through TC-018) pass
2. All business errors raise the correct exception types
3. Transactional integrity is preserved
4. Concurrency tests pass
5. No unnecessary database queries are performed (no N+1)

---

## 13. Future Extensions (Out of Scope)

The following are intentionally deferred:

- Partial order confirmation
- Multiple shipment locations per order
- Confirmation with backorder support
- Confirmation email notifications
- Auditing of confirmation decisions

These require explicit requirements before implementation.

---

## 14. Change History

| Date       | Change                                           | Commit       |
| ---------- | ----------------------------------------------- | ------------ |
| 2026-09-02 | Initial service specification created            | `2aefa32`    |
| 2026-09-02 | Specification approved and implementation verified | `b517c56` |

---

## 15. Approval

This specification is approved and has been implemented.

Approval record:

```text
[x] Service contract approved
[x] Test specification approved
[x] Concurrency strategy approved
```

Implementation:

```text
apps/orders/services.py::confirm_order
```

Automated verification:

```text
python -m pytest tests/orders/test_confirmation.py -q
→ 18 passed
