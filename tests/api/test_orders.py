import pytest
from rest_framework.test import APIClient
from decimal import Decimal

from apps.orders.models import SalesOrder, SalesOrderLine


@pytest.mark.django_db
def test_order_list_returns_orders(operations_api_client, customer):
    SalesOrder.objects.create(
        customer=customer,
        status=SalesOrder.Status.DRAFT,
    )
    SalesOrder.objects.create(
        customer=customer,
        status=SalesOrder.Status.CONFIRMED,
    )

    response = operations_api_client.get("/api/v1/orders/")

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert len(response.json()["results"]) == 2


@pytest.mark.django_db
def test_order_retrieve_returns_order_with_lines(
    operations_api_client,
    order,
    order_line,
):
    response = operations_api_client.get(
        f"/api/v1/orders/{order.id}/"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(order.id)
    assert data["customer"] == str(order.customer.id)
    assert data["status"] == "DRAFT"
    assert len(data["lines"]) == 1

    line = data["lines"][0]

    assert line["id"] == str(order_line.id)
    assert line["product"] == str(order_line.product.id)
    assert line["quantity"] == 25
    assert line["unit_price"] == "10.00"
    assert line["created_at"]


@pytest.mark.django_db
def test_order_retrieve_unknown_order_returns_404(
    operations_api_client,
):
    response = operations_api_client.get(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_order_list_is_paginated(
    operations_api_client,
    customer,
):
    for index in range(25):
        SalesOrder.objects.create(
            customer=customer,
            status=SalesOrder.Status.DRAFT,
        )

    response = operations_api_client.get("/api/v1/orders/")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 25
    assert len(data["results"]) == 20
    assert data["next"] is not None
    assert data["previous"] is None


@pytest.mark.django_db
def test_order_create_returns_201_and_creates_draft(
    operations_api_client,
    customer,
    product,
):
    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 2,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer"] == str(customer.id)
    assert data["status"] == "DRAFT"
    assert len(data["lines"]) == 1

    line = data["lines"][0]

    assert line["product"] == str(product.id)
    assert line["quantity"] == 2
    assert line["unit_price"] == "10.00"

    order = SalesOrder.objects.get(id=data["id"])

    assert order.status == SalesOrder.Status.DRAFT

    assert SalesOrderLine.objects.filter(
        order=order,
        product=product,
        quantity=2,
        unit_price="10.00",
    ).exists()


@pytest.mark.django_db
def test_order_create_snapshots_current_product_price(
    operations_api_client,
    customer,
    product,
):
    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 3,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 201

    line = SalesOrderLine.objects.get(
        order_id=response.json()["id"]
    )

    # product.unit_price is Decimal('10.00'), ensure we compare with Decimal
    assert line.unit_price == Decimal(product.unit_price)


@pytest.mark.django_db
def test_order_create_supports_multiple_lines(
    operations_api_client,
    customer,
    product,
):
    from apps.products.models import Product

    product_b = Product.objects.create(
        sku="TEST-002",
        name="Second Product",
        unit_price="20.00",
        active=True,
    )

    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 2,
                },
                {
                    "product": str(product_b.id),
                    "quantity": 4,
                },
            ],
        },
        format="json",
    )

    assert response.status_code == 201

    data = response.json()

    assert len(data["lines"]) == 2

    prices = {
        line["product"]: line["unit_price"]
        for line in data["lines"]
    }

    assert prices[str(product.id)] == "10.00"
    assert prices[str(product_b.id)] == "20.00"


@pytest.mark.django_db
def test_order_create_does_not_allow_client_to_set_status(
    operations_api_client,
    customer,
    product,
):
    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "status": "CONFIRMED",
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 2,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["status"] == "DRAFT"


@pytest.mark.django_db
def test_order_create_rejects_client_supplied_unit_price(
    operations_api_client,
    customer,
    product,
):
    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 2,
                    "unit_price": "999.99",
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 400
    # The error is nested under "lines" -> list -> "unit_price"
    assert response.json()["lines"][0]["unit_price"] == (
        "Unit price is set by the server."
    )


@pytest.mark.django_db
def test_order_create_rejects_unknown_customer(
    operations_api_client,
    product,
):
    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": "00000000-0000-0000-0000-000000000000",
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 2,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "customer" in response.json()


@pytest.mark.django_db
def test_order_create_rejects_unknown_product(
    operations_api_client,
    customer,
):
    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": "00000000-0000-0000-0000-000000000000",
                    "quantity": 2,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "lines" in response.json()


@pytest.mark.parametrize("quantity", [0, -1])
@pytest.mark.django_db
def test_order_create_rejects_non_positive_quantity(
    operations_api_client,
    customer,
    product,
    quantity,
):
    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": quantity,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "lines" in response.json()


@pytest.mark.django_db
def test_order_create_rejects_empty_lines(
    operations_api_client,
    customer,
):
    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "lines" in response.json()


@pytest.mark.django_db
def test_anonymous_order_list_requires_authentication():
    response = APIClient().get("/api/v1/orders/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_order_create_requires_authentication(
    customer,
    product,
):
    response = APIClient().post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 2,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_can_create_orders(
    admin_api_client,
    customer,
    product,
):
    response = admin_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 2,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_operations_can_create_orders(
    operations_api_client,
    customer,
    product,
):
    response = operations_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 2,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_read_only_can_read_orders(
    read_only_api_client,
    order,
):
    response = read_only_api_client.get(
        f"/api/v1/orders/{order.id}/"
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_read_only_cannot_create_orders(
    read_only_api_client,
    customer,
    product,
):
    response = read_only_api_client.post(
        "/api/v1/orders/",
        {
            "customer": str(customer.id),
            "lines": [
                {
                    "product": str(product.id),
                    "quantity": 2,
                }
            ],
        },
        format="json",
    )

    assert response.status_code == 403