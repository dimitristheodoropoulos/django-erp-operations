import pytest

from apps.customers.models import Customer
from apps.inventory.models import StockItem
from apps.orders.models import SalesOrder, SalesOrderLine
from apps.products.models import Product
from apps.warehouses.models import Warehouse


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        name="Test Customer",
        email="customer@example.com",
        active=True,
    )


@pytest.fixture
def product(db):
    return Product.objects.create(
        sku="TEST-001",
        name="Test Product",
        unit_price="10.00",
        active=True,
    )


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(
        code="WH-001",
        name="Test Warehouse",
        active=True,
    )


@pytest.fixture
def stock_item(db, product, warehouse):
    return StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=0,
    )


@pytest.fixture
def order(db, customer):
    return SalesOrder.objects.create(
        customer=customer,
        status=SalesOrder.Status.DRAFT,
    )


@pytest.fixture
def order_line(db, order, product):
    return SalesOrderLine.objects.create(
        order=order,
        product=product,
        quantity=25,
        unit_price="10.00",
    )
