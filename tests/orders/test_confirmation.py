import pytest

from apps.orders.models import SalesOrder


@pytest.mark.django_db
def test_confirm_valid_draft_order(order, order_line, stock_item):
    """
    TC-001 — Confirm valid draft order.

    This test intentionally fails until confirm_order() is implemented.
    """
    from apps.orders.services import confirm_order

    confirmed_order = confirm_order(order.id)

    confirmed_order.refresh_from_db()
    stock_item.refresh_from_db()

    assert confirmed_order.status == SalesOrder.Status.CONFIRMED
    assert stock_item.quantity == 100
    assert stock_item.reserved_quantity == 25
    assert stock_item.available_quantity == 75

@pytest.mark.django_db
def test_confirm_reserves_single_product(order, order_line, stock_item):
    """TC-002 — Reserve stock for a single product."""
    from apps.orders.services import confirm_order

    confirm_order(order.id)

    stock_item.refresh_from_db()

    assert stock_item.reserved_quantity == 25
    assert stock_item.quantity == 100
    assert stock_item.available_quantity == 75


@pytest.mark.django_db
def test_confirm_reserves_stock_across_multiple_warehouses(
    order,
    order_line,
    product,
    stock_item,
):
    """TC-003 — Reserve stock across multiple warehouses."""
    from apps.orders.services import confirm_order
    from apps.inventory.models import StockItem
    from apps.warehouses.models import Warehouse

    warehouse_b = Warehouse.objects.create(
        code="WH-002",
        name="Second Test Warehouse",
        active=True,
    )

    first_stock = StockItem.objects.get(product=product)

    # The service allocation is based on StockItem.id ordering.
    # The expected allocation is established after controlling the IDs
    # in the final test implementation.
    second_stock = StockItem.objects.create(
        product=product,
        warehouse=warehouse_b,
        quantity=20,
        reserved_quantity=0,
    )

    first_stock.quantity = 30
    first_stock.reserved_quantity = 0
    first_stock.save(update_fields=["quantity", "reserved_quantity"])

    order_line.quantity = 40
    order_line.save(update_fields=["quantity"])

    confirm_order(order.id)

    first_stock.refresh_from_db()
    second_stock.refresh_from_db()

    assert first_stock.reserved_quantity + second_stock.reserved_quantity == 40
    assert first_stock.quantity == 30
    assert second_stock.quantity == 20


@pytest.mark.django_db
def test_confirm_aggregates_multiple_lines_for_same_product(
    order,
    order_line,
    product,
    stock_item,
):
    """TC-004 — Aggregate multiple lines for the same product."""
    from apps.orders.models import SalesOrderLine
    from apps.orders.services import confirm_order

    SalesOrderLine.objects.create(
        order=order,
        product=product,
        quantity=20,
        unit_price="10.00",
    )

    confirm_order(order.id)

    stock_item.refresh_from_db()

    assert stock_item.reserved_quantity == 45
    assert stock_item.quantity == 100


@pytest.mark.django_db
def test_confirm_commits_order_and_reservation_together(
    order,
    order_line,
    stock_item,
):
    """TC-005 — Persist order status and reservations atomically."""
    from apps.orders.services import confirm_order

    confirmed_order = confirm_order(order.id)

    confirmed_order.refresh_from_db()
    stock_item.refresh_from_db()

    assert confirmed_order.status == SalesOrder.Status.CONFIRMED
    assert stock_item.reserved_quantity == order_line.quantity



@pytest.mark.django_db
def test_confirm_missing_order_raises_order_not_found():
    """TC-006 — Missing order raises OrderNotFound."""
    import uuid

    import pytest

    from apps.orders.exceptions import OrderNotFound
    from apps.orders.services import confirm_order

    with pytest.raises(OrderNotFound):
        confirm_order(uuid.uuid4())


@pytest.mark.django_db
def test_confirm_non_draft_order_raises_invalid_order_state(
    order,
    order_line,
    stock_item,
):
    """TC-007 — Non-DRAFT order cannot be confirmed."""
    from apps.orders.exceptions import InvalidOrderState
    from apps.orders.services import confirm_order

    order.status = order.Status.CONFIRMED
    order.save(update_fields=["status"])

    with pytest.raises(InvalidOrderState):
        confirm_order(order.id)


@pytest.mark.django_db
def test_confirm_inactive_customer_raises_inactive_customer(
    order,
    order_line,
    stock_item,
):
    """TC-008 — Inactive customer cannot confirm an order."""
    from apps.orders.exceptions import InactiveCustomer
    from apps.orders.services import confirm_order

    order.customer.active = False
    order.customer.save(update_fields=["active"])

    with pytest.raises(InactiveCustomer):
        confirm_order(order.id)


@pytest.mark.django_db
def test_confirm_order_without_lines_raises_order_has_no_lines(
    order,
    stock_item,
):
    """TC-009 — Order without lines cannot be confirmed."""
    from apps.orders.exceptions import OrderHasNoLines
    from apps.orders.services import confirm_order

    with pytest.raises(OrderHasNoLines):
        confirm_order(order.id)


@pytest.mark.django_db
def test_confirm_inactive_product_raises_inactive_product(
    order,
    order_line,
    stock_item,
):
    """TC-010 — Inactive product cannot be confirmed."""
    from apps.orders.exceptions import InactiveProduct
    from apps.orders.services import confirm_order

    order_line.product.active = False
    order_line.product.save(update_fields=["active"])

    with pytest.raises(InactiveProduct):
        confirm_order(order.id)


@pytest.mark.django_db
def test_confirm_insufficient_stock_raises_insufficient_stock(
    order,
    order_line,
    stock_item,
):
    """TC-011 — Insufficient stock prevents confirmation."""
    from apps.orders.exceptions import InsufficientStock
    from apps.orders.services import confirm_order

    order_line.quantity = 101
    order_line.save(update_fields=["quantity"])

    with pytest.raises(InsufficientStock):
        confirm_order(order.id)


@pytest.mark.django_db
def test_insufficient_stock_leaves_order_in_draft(
    order,
    order_line,
    stock_item,
):
    """TC-012 — Insufficient stock leaves order DRAFT."""
    from apps.orders.exceptions import InsufficientStock
    from apps.orders.services import confirm_order

    order_line.quantity = 101
    order_line.save(update_fields=["quantity"])

    with pytest.raises(InsufficientStock):
        confirm_order(order.id)

    order.refresh_from_db()

    assert order.status == SalesOrder.Status.DRAFT


@pytest.mark.django_db
def test_insufficient_stock_leaves_inventory_unchanged(
    order,
    order_line,
    stock_item,
):
    """TC-013 — Insufficient stock leaves inventory unchanged."""
    from apps.orders.exceptions import InsufficientStock
    from apps.orders.services import confirm_order

    order_line.quantity = 101
    order_line.save(update_fields=["quantity"])

    with pytest.raises(InsufficientStock):
        confirm_order(order.id)

    stock_item.refresh_from_db()

    assert stock_item.quantity == 100
    assert stock_item.reserved_quantity == 0


@pytest.mark.django_db
def test_confirmation_is_atomic_when_later_product_is_insufficient(
    order,
    order_line,
    stock_item,
):
    """TC-014 — Earlier reservations roll back if a later product fails."""
    from apps.inventory.models import StockItem
    from apps.orders.exceptions import InsufficientStock
    from apps.orders.models import SalesOrderLine
    from apps.orders.services import confirm_order
    from apps.products.models import Product
    from apps.warehouses.models import Warehouse

    product_b = Product.objects.create(
        sku="TEST-002",
        name="Second Test Product",
        unit_price="20.00",
        active=True,
    )

    warehouse_b = Warehouse.objects.create(
        code="WH-002",
        name="Second Test Warehouse",
        active=True,
    )

    stock_b = StockItem.objects.create(
        product=product_b,
        warehouse=warehouse_b,
        quantity=10,
        reserved_quantity=0,
    )

    SalesOrderLine.objects.create(
        order=order,
        product=product_b,
        quantity=11,
        unit_price="20.00",
    )

    with pytest.raises(InsufficientStock):
        confirm_order(order.id)

    stock_item.refresh_from_db()
    stock_b.refresh_from_db()
    order.refresh_from_db()

    assert stock_item.reserved_quantity == 0
    assert stock_b.reserved_quantity == 0
    assert order.status == SalesOrder.Status.DRAFT


@pytest.mark.django_db
def test_invalid_quantity_is_rejected_by_database_constraint(
    order,
    product,
):
    """TC-015 — Persisted order lines cannot have non-positive quantity."""
    from django.db import IntegrityError
    from apps.orders.models import SalesOrderLine

    with pytest.raises(IntegrityError):
        SalesOrderLine.objects.create(
            order=order,
            product=product,
            quantity=0,
            unit_price="10.00",
        )


@pytest.mark.django_db(transaction=True)
def test_concurrent_confirmation_of_same_order(
    order,
    order_line,
    stock_item,
):
    """TC-016 — Concurrent confirmation of the same order."""
    import threading

    from django.db import close_old_connections

    from apps.orders.exceptions import InvalidOrderState
    from apps.orders.services import confirm_order

    results = []
    errors = []
    barrier = threading.Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait()
            confirm_order(order.id)
            results.append("confirmed")
        except Exception as exc:
            errors.append(exc)
        finally:
            close_old_connections()

    thread_a = threading.Thread(target=worker)
    thread_b = threading.Thread(target=worker)

    thread_a.start()
    thread_b.start()

    thread_a.join()
    thread_b.join()

    assert results.count("confirmed") == 1
    assert len(errors) == 1
    assert isinstance(errors[0], InvalidOrderState)

    order.refresh_from_db()
    stock_item.refresh_from_db()

    assert order.status == SalesOrder.Status.CONFIRMED
    assert stock_item.reserved_quantity == 25


@pytest.mark.django_db(transaction=True)
def test_concurrent_orders_competing_for_same_stock(
    customer,
    product,
    warehouse,
):
    """TC-017 — Concurrent orders compete safely for shared stock."""
    import threading

    from django.db import close_old_connections

    from apps.inventory.models import StockItem
    from apps.orders.exceptions import InsufficientStock
    from apps.orders.models import SalesOrder, SalesOrderLine
    from apps.orders.services import confirm_order

    stock_item = StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=10,
        reserved_quantity=0,
    )

    order_a = SalesOrder.objects.create(
        customer=customer,
        status=SalesOrder.Status.DRAFT,
    )
    SalesOrderLine.objects.create(
        order=order_a,
        product=product,
        quantity=7,
        unit_price="10.00",
    )

    order_b = SalesOrder.objects.create(
        customer=customer,
        status=SalesOrder.Status.DRAFT,
    )
    SalesOrderLine.objects.create(
        order=order_b,
        product=product,
        quantity=7,
        unit_price="10.00",
    )

    results = []
    errors = []
    barrier = threading.Barrier(2)

    def worker(order_id):
        close_old_connections()
        try:
            barrier.wait()
            confirm_order(order_id)
            results.append(order_id)
        except Exception as exc:
            errors.append(exc)
        finally:
            close_old_connections()

    thread_a = threading.Thread(target=worker, args=(order_a.id,))
    thread_b = threading.Thread(target=worker, args=(order_b.id,))

    thread_a.start()
    thread_b.start()

    thread_a.join()
    thread_b.join()

    assert len(results) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], InsufficientStock)

    stock_item.refresh_from_db()

    assert stock_item.reserved_quantity == 7

    order_a.refresh_from_db()
    order_b.refresh_from_db()

    confirmed_orders = [
        order
        for order in (order_a, order_b)
        if order.status == SalesOrder.Status.CONFIRMED
    ]
    draft_orders = [
        order
        for order in (order_a, order_b)
        if order.status == SalesOrder.Status.DRAFT
    ]

    assert len(confirmed_orders) == 1
    assert len(draft_orders) == 1


@pytest.mark.django_db
def test_confirm_allocates_stock_by_stock_item_id(
    order,
    order_line,
    product,
):
    """TC-018 — Stock allocation follows ascending StockItem.id."""
    import uuid

    from apps.inventory.models import StockItem
    from apps.orders.services import confirm_order
    from apps.warehouses.models import Warehouse

    warehouse_a = Warehouse.objects.create(
        code="WH-002",
        name="Allocation Warehouse A",
        active=True,
    )
    warehouse_b = Warehouse.objects.create(
        code="WH-003",
        name="Allocation Warehouse B",
        active=True,
    )

    lower_id_stock = StockItem.objects.create(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        product=product,
        warehouse=warehouse_a,
        quantity=30,
        reserved_quantity=0,
    )

    higher_id_stock = StockItem.objects.create(
        id=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        product=product,
        warehouse=warehouse_b,
        quantity=20,
        reserved_quantity=0,
    )

    order_line.quantity = 40
    order_line.save(update_fields=["quantity"])

    confirm_order(order.id)

    lower_id_stock.refresh_from_db()
    higher_id_stock.refresh_from_db()

    assert lower_id_stock.reserved_quantity == 30
    assert higher_id_stock.reserved_quantity == 10
