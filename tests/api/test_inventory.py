import uuid

import pytest
from rest_framework import status

from apps.inventory.models import StockItem
from apps.products.models import Product
from apps.warehouses.models import Warehouse


@pytest.mark.django_db
def test_inventory_list_returns_stock_items(
    admin_api_client,
    product,
    warehouse,
):
    StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=25,
    )

    response = admin_api_client.get("/api/v1/inventory/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1

    item = response.data["results"][0]

    assert item["product"] == product.id
    assert item["warehouse"] == warehouse.id
    assert item["quantity"] == 100
    assert item["reserved_quantity"] == 25
    assert item["available_quantity"] == 75


@pytest.mark.django_db
def test_inventory_detail_returns_derived_available_quantity(
    admin_api_client,
    product,
    warehouse,
):
    stock_item = StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=25,
    )

    response = admin_api_client.get(
        f"/api/v1/inventory/{stock_item.id}/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["available_quantity"] == 75


@pytest.mark.django_db
def test_inventory_detail_returns_404_for_unknown_item(
    admin_api_client,
):
    response = admin_api_client.get(
        f"/api/v1/inventory/{uuid.uuid4()}/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_inventory_list_is_paginated(
    admin_api_client,
    product,
    warehouse,
):
    for index in range(24):
        extra_product = Product.objects.create(
            sku=f"TEST-INV-{index:03d}",
            name=f"Inventory Product {index}",
            unit_price="10.00",
            active=True,
        )

        StockItem.objects.create(
            product=extra_product,
            warehouse=warehouse,
            quantity=100,
            reserved_quantity=0,
        )

    StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=0,
    )

    response = admin_api_client.get("/api/v1/inventory/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 25
    assert len(response.data["results"]) == 20
    assert response.data["next"] is not None
    assert response.data["previous"] is None


@pytest.mark.django_db
def test_anonymous_user_cannot_list_inventory():
    from rest_framework.test import APIClient

    response = APIClient().get("/api/v1/inventory/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_anonymous_user_cannot_retrieve_inventory(
    product,
    warehouse,
):
    stock_item = StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=20,
    )

    from rest_framework.test import APIClient

    response = APIClient().get(
        f"/api/v1/inventory/{stock_item.id}/"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_admin_role_can_read_inventory(
    admin_api_client,
    product,
    warehouse,
):
    StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=20,
    )

    response = admin_api_client.get("/api/v1/inventory/")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_operations_role_can_read_inventory(
    operations_api_client,
    product,
    warehouse,
):
    StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=20,
    )

    response = operations_api_client.get("/api/v1/inventory/")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_read_only_role_can_read_inventory(
    read_only_api_client,
    product,
    warehouse,
):
    StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=20,
    )

    response = read_only_api_client.get("/api/v1/inventory/")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_inventory_representation_has_exact_fields(
    admin_api_client,
    product,
    warehouse,
):
    stock_item = StockItem.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=100,
        reserved_quantity=20,
    )

    response = admin_api_client.get(
        f"/api/v1/inventory/{stock_item.id}/"
    )

    assert response.status_code == status.HTTP_200_OK

    assert set(response.data.keys()) == {
        "id",
        "product",
        "warehouse",
        "quantity",
        "reserved_quantity",
        "available_quantity",
        "created_at",
        "modified_at",
    }


@pytest.mark.django_db
def test_inventory_has_no_write_endpoint(
    admin_api_client,
):
    response = admin_api_client.post(
        "/api/v1/inventory/",
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
