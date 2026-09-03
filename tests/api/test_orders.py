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
    # The error is nested under error.details -> lines -> list
    assert response.json()["error"]["details"]["lines"][0]["unit_price"] == (
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
    assert "customer" in response.json()["error"]["details"]


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
    assert "lines" in response.json()["error"]["details"]


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
    assert "lines" in response.json()["error"]["details"]


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
    assert "lines" in response.json()["error"]["details"]


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


# ---------------------------------------------------------------------------
# Order confirmation API
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_order_confirm_returns_200_and_confirms_order(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 200

    order.refresh_from_db()
    stock_item.refresh_from_db()

    assert order.status == SalesOrder.Status.CONFIRMED
    assert stock_item.reserved_quantity == order_line.quantity


@pytest.mark.django_db
def test_order_confirm_unknown_order_returns_404(
    operations_api_client,
):
    response = operations_api_client.post(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "ORDER_NOT_FOUND",
            "message": "The requested order does not exist.",
        }
    }


@pytest.mark.django_db
def test_order_confirm_invalid_state_returns_409(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    order.status = SalesOrder.Status.CONFIRMED
    order.save(update_fields=["status"])

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INVALID_ORDER_STATE",
            "message": "The order cannot be confirmed from its current state.",
        }
    }


@pytest.mark.django_db
def test_order_confirm_inactive_customer_returns_409(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    order.customer.active = False
    order.customer.save(update_fields=["active"])

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INACTIVE_CUSTOMER",
            "message": "The order customer is inactive.",
        }
    }


@pytest.mark.django_db
def test_order_confirm_without_lines_returns_409(
    operations_api_client,
    order,
    stock_item,
):
    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "ORDER_HAS_NO_LINES",
            "message": "An order must contain at least one line before confirmation.",
        }
    }


@pytest.mark.django_db
def test_order_confirm_inactive_product_returns_409(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    order_line.product.active = False
    order_line.product.save(update_fields=["active"])

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INACTIVE_PRODUCT",
            "message": "The order contains an inactive product.",
        }
    }


@pytest.mark.django_db
def test_order_confirm_insufficient_stock_returns_409(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    order_line.quantity = 101
    order_line.save(update_fields=["quantity"])

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INSUFFICIENT_STOCK",
            "message": "Insufficient stock to confirm the order.",
        }
    }

    order.refresh_from_db()
    stock_item.refresh_from_db()

    assert order.status == SalesOrder.Status.DRAFT
    assert stock_item.reserved_quantity == 0


@pytest.mark.django_db
def test_order_confirm_invalid_quantity_returns_400(
    operations_api_client,
    order,
    order_line,
    stock_item,
    monkeypatch,
):
    from apps.api import order_views
    from apps.orders.exceptions import InvalidOrderQuantity

    def raise_invalid_quantity(order_id):
        raise InvalidOrderQuantity

    monkeypatch.setattr(
        order_views,
        "confirm_order",
        raise_invalid_quantity,
    )

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "INVALID_ORDER_QUANTITY",
            "message": "Order line quantity must be greater than zero.",
        }
    }


@pytest.mark.django_db
def test_anonymous_order_confirm_requires_authentication(
    order,
    order_line,
    stock_item,
):
    response = APIClient().post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_read_only_cannot_confirm_order(
    read_only_api_client,
    order,
    order_line,
    stock_item,
):
    response = read_only_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_confirm_order(
    admin_api_client,
    order,
    order_line,
    stock_item,
):
    response = admin_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 200

    order.refresh_from_db()

    assert order.status == SalesOrder.Status.CONFIRMED


@pytest.mark.django_db
def test_operations_can_confirm_order(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/confirm/",
        {},
        format="json",
    )

    assert response.status_code == 200

    order.refresh_from_db()

    assert order.status == SalesOrder.Status.CONFIRMED


# ---------------------------------------------------------------------------
# Sales order lifecycle API
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_order_cancel_returns_200_and_cancels_draft_order(
    operations_api_client,
    order,
):
    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/cancel/",
        {},
        format="json",
    )

    assert response.status_code == 200

    data = response.json()

    order.refresh_from_db()

    assert order.status == SalesOrder.Status.CANCELLED
    assert data["id"] == str(order.id)
    assert data["status"] == "CANCELLED"


@pytest.mark.django_db
def test_order_cancel_invalid_state_returns_409(
    operations_api_client,
    order,
):
    order.status = SalesOrder.Status.CONFIRMED
    order.save(update_fields=["status"])

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/cancel/",
        {},
        format="json",
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INVALID_ORDER_STATE",
            "message": "The order cannot be cancelled from its current state.",
        }
    }


@pytest.mark.django_db
def test_order_cancel_unknown_order_returns_404(
    operations_api_client,
):
    response = operations_api_client.post(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000/cancel/",
        {},
        format="json",
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "ORDER_NOT_FOUND",
            "message": "The requested order does not exist.",
        }
    }


@pytest.mark.django_db
def test_anonymous_order_cancel_requires_authentication():
    response = APIClient().post(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000/cancel/",
        {},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_read_only_cannot_cancel_orders(
    read_only_api_client,
    order,
):
    response = read_only_api_client.post(
        f"/api/v1/orders/{order.id}/cancel/",
        {},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_order_ship_returns_200_and_consumes_reserved_inventory(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    order.status = SalesOrder.Status.CONFIRMED
    order.save(update_fields=["status"])

    stock_item.reserved_quantity = order_line.quantity
    stock_item.save(update_fields=["reserved_quantity"])

    original_quantity = stock_item.quantity

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/ship/",
        {},
        format="json",
    )

    assert response.status_code == 200

    data = response.json()

    order.refresh_from_db()
    stock_item.refresh_from_db()

    assert order.status == SalesOrder.Status.SHIPPED
    assert data["id"] == str(order.id)
    assert data["status"] == "SHIPPED"
    assert stock_item.quantity == original_quantity - order_line.quantity
    assert stock_item.reserved_quantity == 0


@pytest.mark.django_db
def test_order_ship_invalid_state_returns_409(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/ship/",
        {},
        format="json",
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INVALID_ORDER_STATE",
            "message": "The order cannot be shipped from its current state.",
        }
    }


@pytest.mark.django_db
def test_order_ship_unknown_order_returns_404(
    operations_api_client,
):
    response = operations_api_client.post(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000/ship/",
        {},
        format="json",
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "ORDER_NOT_FOUND",
            "message": "The requested order does not exist.",
        }
    }


@pytest.mark.django_db
def test_order_ship_insufficient_reserved_stock_returns_409(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    order.status = SalesOrder.Status.CONFIRMED
    order.save(update_fields=["status"])

    stock_item.reserved_quantity = order_line.quantity - 1
    stock_item.save(update_fields=["reserved_quantity"])

    original_quantity = stock_item.quantity
    original_reserved_quantity = stock_item.reserved_quantity

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/ship/",
        {},
        format="json",
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INSUFFICIENT_STOCK",
            "message": "Insufficient stock to ship the order.",
        }
    }

    order.refresh_from_db()
    stock_item.refresh_from_db()

    assert order.status == SalesOrder.Status.CONFIRMED
    assert stock_item.quantity == original_quantity
    assert stock_item.reserved_quantity == original_reserved_quantity


@pytest.mark.django_db
def test_anonymous_order_ship_requires_authentication():
    response = APIClient().post(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000/ship/",
        {},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_read_only_cannot_ship_orders(
    read_only_api_client,
    order,
):
    response = read_only_api_client.post(
        f"/api/v1/orders/{order.id}/ship/",
        {},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_order_complete_returns_200_and_completes_shipped_order(
    operations_api_client,
    order,
):
    order.status = SalesOrder.Status.SHIPPED
    order.save(update_fields=["status"])

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/complete/",
        {},
        format="json",
    )

    assert response.status_code == 200

    data = response.json()

    order.refresh_from_db()

    assert order.status == SalesOrder.Status.COMPLETED
    assert data["id"] == str(order.id)
    assert data["status"] == "COMPLETED"


@pytest.mark.django_db
def test_order_complete_does_not_modify_inventory(
    operations_api_client,
    order,
    order_line,
    stock_item,
):
    order.status = SalesOrder.Status.SHIPPED
    order.save(update_fields=["status"])

    original_quantity = stock_item.quantity
    original_reserved_quantity = stock_item.reserved_quantity

    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/complete/",
        {},
        format="json",
    )

    assert response.status_code == 200

    order.refresh_from_db()
    stock_item.refresh_from_db()

    assert order.status == SalesOrder.Status.COMPLETED
    assert stock_item.quantity == original_quantity
    assert stock_item.reserved_quantity == original_reserved_quantity


@pytest.mark.django_db
def test_order_complete_invalid_state_returns_409(
    operations_api_client,
    order,
):
    response = operations_api_client.post(
        f"/api/v1/orders/{order.id}/complete/",
        {},
        format="json",
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INVALID_ORDER_STATE",
            "message": "The order cannot be completed from its current state.",
        }
    }


@pytest.mark.django_db
def test_order_complete_unknown_order_returns_404(
    operations_api_client,
):
    response = operations_api_client.post(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000/complete/",
        {},
        format="json",
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "ORDER_NOT_FOUND",
            "message": "The requested order does not exist.",
        }
    }


@pytest.mark.django_db
def test_anonymous_order_complete_requires_authentication():
    response = APIClient().post(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000/complete/",
        {},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_read_only_cannot_complete_orders(
    read_only_api_client,
    order,
):
    response = read_only_api_client.post(
        f"/api/v1/orders/{order.id}/complete/",
        {},
        format="json",
    )

    assert response.status_code == 403