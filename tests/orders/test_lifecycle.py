import pytest

from apps.orders.exceptions import InvalidOrderState, OrderNotFound
from apps.orders.models import SalesOrder
from apps.orders.services import (
    cancel_order,
    complete_order,
    ship_order,
)


@pytest.mark.django_db
def test_cancel_draft_order(order):
    order.status = SalesOrder.Status.DRAFT
    order.save(update_fields=["status"])

    result = cancel_order(order.id)

    order.refresh_from_db()

    assert result.id == order.id
    assert order.status == SalesOrder.Status.CANCELLED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [
        SalesOrder.Status.CONFIRMED,
        SalesOrder.Status.SHIPPED,
        SalesOrder.Status.COMPLETED,
        SalesOrder.Status.CANCELLED,
    ],
)
def test_cancel_rejects_unsupported_states(order, status):
    order.status = status
    order.save(update_fields=["status"])

    with pytest.raises(InvalidOrderState):
        cancel_order(order.id)

    order.refresh_from_db()

    assert order.status == status


@pytest.mark.django_db
def test_cancel_missing_order_raises_order_not_found():
    with pytest.raises(OrderNotFound):
        cancel_order("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
def test_ship_confirmed_order_consumes_reserved_inventory(
    order,
    order_line,
    stock_item,
):
    order.status = SalesOrder.Status.CONFIRMED
    order.save(update_fields=["status"])

    order_line.quantity = 4
    order_line.save(update_fields=["quantity"])

    stock_item.quantity = 10
    stock_item.reserved_quantity = 4
    stock_item.save(
        update_fields=["quantity", "reserved_quantity"]
    )

    result = ship_order(order.id)

    order.refresh_from_db()
    stock_item.refresh_from_db()

    assert result.id == order.id
    assert order.status == SalesOrder.Status.SHIPPED
    assert stock_item.quantity == 6
    assert stock_item.reserved_quantity == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [
        SalesOrder.Status.DRAFT,
        SalesOrder.Status.SHIPPED,
        SalesOrder.Status.COMPLETED,
        SalesOrder.Status.CANCELLED,
    ],
)
def test_ship_rejects_unsupported_states(order, status):
    order.status = status
    order.save(update_fields=["status"])

    with pytest.raises(InvalidOrderState):
        ship_order(order.id)

    order.refresh_from_db()

    assert order.status == status


@pytest.mark.django_db
def test_ship_missing_order_raises_order_not_found():
    with pytest.raises(OrderNotFound):
        ship_order("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
def test_complete_shipped_order(order):
    order.status = SalesOrder.Status.SHIPPED
    order.save(update_fields=["status"])

    result = complete_order(order.id)

    order.refresh_from_db()

    assert result.id == order.id
    assert order.status == SalesOrder.Status.COMPLETED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [
        SalesOrder.Status.DRAFT,
        SalesOrder.Status.CONFIRMED,
        SalesOrder.Status.COMPLETED,
        SalesOrder.Status.CANCELLED,
    ],
)
def test_complete_rejects_unsupported_states(order, status):
    order.status = status
    order.save(update_fields=["status"])

    with pytest.raises(InvalidOrderState):
        complete_order(order.id)

    order.refresh_from_db()

    assert order.status == status


@pytest.mark.django_db
def test_complete_does_not_modify_inventory(
    order,
    stock_item,
):
    order.status = SalesOrder.Status.SHIPPED
    order.save(update_fields=["status"])

    stock_item.quantity = 6
    stock_item.reserved_quantity = 0
    stock_item.save(
        update_fields=["quantity", "reserved_quantity"]
    )

    complete_order(order.id)

    stock_item.refresh_from_db()

    assert stock_item.quantity == 6
    assert stock_item.reserved_quantity == 0


@pytest.mark.django_db
def test_complete_missing_order_raises_order_not_found():
    with pytest.raises(OrderNotFound):
        complete_order("00000000-0000-0000-0000-000000000000")
