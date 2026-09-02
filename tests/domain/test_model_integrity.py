import pytest
from django.db import IntegrityError

from apps.inventory.models import StockItem
from apps.orders.models import SalesOrder
from apps.products.models import Product
from apps.warehouses.models import Warehouse


@pytest.mark.django_db
def test_product_sku_must_be_unique():
    Product.objects.create(
        sku="SKU-001",
        name="Product One",
        unit_price="10.00",
        active=True,
    )

    with pytest.raises(IntegrityError):
        Product.objects.create(
            sku="SKU-001",
            name="Product Two",
            unit_price="20.00",
            active=True,
        )


@pytest.mark.django_db
def test_warehouse_code_must_be_unique():
    Warehouse.objects.create(
        code="WH-001",
        name="Warehouse One",
        active=True,
    )

    with pytest.raises(IntegrityError):
        Warehouse.objects.create(
            code="WH-001",
            name="Warehouse Two",
            active=True,
        )


@pytest.mark.django_db
def test_warehouse_preserves_required_fields():
    warehouse = Warehouse.objects.create(
        code="WH-001",
        name="Main Warehouse",
        location="Athens",
        active=False,
    )

    warehouse.refresh_from_db()

    assert warehouse.id is not None
    assert warehouse.code == "WH-001"
    assert warehouse.name == "Main Warehouse"
    assert warehouse.location == "Athens"
    assert warehouse.active is False
    assert warehouse.created_at is not None
    assert warehouse.modified_at is not None


@pytest.mark.django_db
def test_stock_item_product_warehouse_pair_must_be_unique(
    product,
    warehouse,
):
    StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=10,
        reserved_quantity=0,
    )

    with pytest.raises(IntegrityError):
        StockItem.objects.create(
            product=product,
            warehouse=warehouse,
            quantity=20,
            reserved_quantity=0,
        )


@pytest.mark.django_db
def test_stock_item_allows_same_product_in_different_warehouses(
    product,
    warehouse,
):
    second_warehouse = Warehouse.objects.create(
        code="WH-002",
        name="Second Warehouse",
        active=True,
    )

    first_stock = StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=10,
        reserved_quantity=2,
    )

    second_stock = StockItem.objects.create(
        product=product,
        warehouse=second_warehouse,
        quantity=20,
        reserved_quantity=5,
    )

    assert first_stock.pk != second_stock.pk


@pytest.mark.django_db
def test_stock_item_available_quantity_is_derived():
    product = Product.objects.create(
        sku="SKU-001",
        name="Test Product",
        unit_price="10.00",
        active=True,
    )
    warehouse = Warehouse.objects.create(
        code="WH-001",
        name="Test Warehouse",
        active=True,
    )

    stock_item = StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=25,
    )

    assert stock_item.quantity == 100
    assert stock_item.reserved_quantity == 25
    assert stock_item.available_quantity == 75


@pytest.mark.django_db
def test_stock_item_rejects_negative_quantity(
    product,
    warehouse,
):
    with pytest.raises(IntegrityError):
        StockItem.objects.create(
            product=product,
            warehouse=warehouse,
            quantity=-1,
            reserved_quantity=0,
        )


@pytest.mark.django_db
def test_stock_item_rejects_negative_reserved_quantity(
    product,
    warehouse,
):
    with pytest.raises(IntegrityError):
        StockItem.objects.create(
            product=product,
            warehouse=warehouse,
            quantity=10,
            reserved_quantity=-1,
        )


@pytest.mark.django_db
def test_stock_item_rejects_reserved_quantity_above_quantity(
    product,
    warehouse,
):
    with pytest.raises(IntegrityError):
        StockItem.objects.create(
            product=product,
            warehouse=warehouse,
            quantity=10,
            reserved_quantity=11,
        )


@pytest.mark.django_db
def test_sales_order_defaults_to_draft(customer):
    order = SalesOrder.objects.create(
        customer=customer,
    )

    order.refresh_from_db()

    assert order.status == SalesOrder.Status.DRAFT
