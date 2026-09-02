import pytest
from rest_framework.test import APIClient

from apps.products.models import Product


@pytest.mark.django_db
def test_product_list_returns_products(operations_api_client):
    Product.objects.create(
        sku="SKU-001",
        name="Product One",
        unit_price="10.00",
    )
    Product.objects.create(
        sku="SKU-002",
        name="Product Two",
        unit_price="20.00",
    )

    response = operations_api_client.get("/api/v1/products/")

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert len(response.json()["results"]) == 2


@pytest.mark.django_db
def test_product_retrieve_returns_product(operations_api_client):
    product = Product.objects.create(
        sku="SKU-001",
        name="Example Product",
        description="Example description",
        unit_price="25.50",
    )

    response = operations_api_client.get(
        f"/api/v1/products/{product.id}/"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(product.id)
    assert data["sku"] == "SKU-001"
    assert data["name"] == "Example Product"
    assert data["description"] == "Example description"
    assert data["unit_price"] == "25.50"
    assert data["active"] is True


@pytest.mark.django_db
def test_product_retrieve_unknown_product_returns_404(operations_api_client):
    response = operations_api_client.get(
        "/api/v1/products/00000000-0000-0000-0000-000000000000/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_product_create_returns_201_and_server_managed_fields(
    operations_api_client,
):
    response = operations_api_client.post(
        "/api/v1/products/",
        {
            "sku": "SKU-NEW",
            "name": "New Product",
            "description": "New description",
            "unit_price": "99.90",
        },
        format="json",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["sku"] == "SKU-NEW"
    assert data["name"] == "New Product"
    assert data["description"] == "New description"
    assert data["unit_price"] == "99.90"
    assert data["active"] is True
    assert data["id"]
    assert data["created_at"]
    assert data["modified_at"]

    assert Product.objects.filter(
        id=data["id"],
        sku="SKU-NEW",
        name="New Product",
        active=True,
    ).exists()


@pytest.mark.django_db
def test_product_create_does_not_allow_client_to_set_active(
    operations_api_client,
):
    response = operations_api_client.post(
        "/api/v1/products/",
        {
            "sku": "SKU-STATE",
            "name": "State Protected Product",
            "unit_price": "10.00",
            "active": False,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["active"] is True


@pytest.mark.django_db
def test_product_create_rejects_duplicate_sku(operations_api_client):
    Product.objects.create(
        sku="SKU-DUPLICATE",
        name="Existing Product",
        unit_price="10.00",
    )

    response = operations_api_client.post(
        "/api/v1/products/",
        {
            "sku": "SKU-DUPLICATE",
            "name": "Duplicate Product",
            "unit_price": "20.00",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "sku" in response.json()


@pytest.mark.django_db
def test_product_create_rejects_negative_price(operations_api_client):
    response = operations_api_client.post(
        "/api/v1/products/",
        {
            "sku": "SKU-NEGATIVE",
            "name": "Invalid Product",
            "unit_price": "-1.00",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "unit_price" in response.json()


@pytest.mark.django_db
def test_product_create_rejects_empty_sku(operations_api_client):
    response = operations_api_client.post(
        "/api/v1/products/",
        {
            "sku": "   ",
            "name": "Invalid Product",
            "unit_price": "10.00",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "sku" in response.json()


@pytest.mark.django_db
def test_product_create_rejects_empty_name(operations_api_client):
    response = operations_api_client.post(
        "/api/v1/products/",
        {
            "sku": "SKU-NAME",
            "name": "   ",
            "unit_price": "10.00",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "name" in response.json()


@pytest.mark.django_db
def test_anonymous_product_list_requires_authentication():
    response = APIClient().get("/api/v1/products/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_product_create_requires_authentication():
    response = APIClient().post(
        "/api/v1/products/",
        {
            "sku": "SKU-AUTH",
            "name": "Unauthorized Product",
            "unit_price": "10.00",
        },
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_read_only_can_read_products(read_only_api_client):
    response = read_only_api_client.get("/api/v1/products/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_read_only_cannot_create_products(read_only_api_client):
    response = read_only_api_client.post(
        "/api/v1/products/",
        {
            "sku": "SKU-READONLY",
            "name": "Read Only Product",
            "unit_price": "10.00",
        },
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_create_products(admin_api_client):
    response = admin_api_client.post(
        "/api/v1/products/",
        {
            "sku": "SKU-ADMIN",
            "name": "Admin Product",
            "unit_price": "10.00",
        },
        format="json",
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_operations_can_create_products(operations_api_client):
    response = operations_api_client.post(
        "/api/v1/products/",
        {
            "sku": "SKU-OPERATIONS",
            "name": "Operations Product",
            "unit_price": "10.00",
        },
        format="json",
    )

    assert response.status_code == 201
