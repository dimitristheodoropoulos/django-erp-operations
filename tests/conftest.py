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

@pytest.fixture
def authenticated_api_client(db):
    from django.contrib.auth.models import Group, User
    from rest_framework.authtoken.models import Token
    from rest_framework.test import APIClient

    def make_client(role_name):
        user = User.objects.create_user(
            username=f"api_user_{role_name.lower()}",
            password="test-password",
        )

        role = Group.objects.get(name=role_name)
        user.groups.add(role)

        token = Token.objects.create(user=user)

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )
        return client

    return make_client


@pytest.fixture
def admin_api_client(authenticated_api_client):
    return authenticated_api_client("ADMIN")


@pytest.fixture
def operations_api_client(authenticated_api_client):
    return authenticated_api_client("OPERATIONS")


@pytest.fixture
def read_only_api_client(authenticated_api_client):
    return authenticated_api_client("READ_ONLY")
