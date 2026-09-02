import pytest
from rest_framework.test import APIClient

from apps.warehouses.models import Warehouse


@pytest.mark.django_db
def test_warehouse_list_returns_warehouses(operations_api_client):
    Warehouse.objects.create(
        code="WH-001",
        name="Main Warehouse",
        location="Athens",
    )
    Warehouse.objects.create(
        code="WH-002",
        name="Secondary Warehouse",
        location="Piraeus",
    )

    response = operations_api_client.get("/api/v1/warehouses/")

    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 2
    assert len(data["results"]) == 2


@pytest.mark.django_db
def test_warehouse_retrieve_returns_warehouse(operations_api_client):
    warehouse = Warehouse.objects.create(
        code="WH-001",
        name="Main Warehouse",
        location="Athens",
    )

    response = operations_api_client.get(
        f"/api/v1/warehouses/{warehouse.id}/"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(warehouse.id)
    assert data["code"] == "WH-001"
    assert data["name"] == "Main Warehouse"
    assert data["location"] == "Athens"
    assert data["active"] is True
    assert data["created_at"]
    assert data["modified_at"]


@pytest.mark.django_db
def test_unknown_warehouse_returns_404(operations_api_client):
    response = operations_api_client.get(
        "/api/v1/warehouses/00000000-0000-0000-0000-000000000000/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_warehouse_list_uses_pagination(operations_api_client):
    for index in range(25):
        Warehouse.objects.create(
            code=f"WH-{index:03d}",
            name=f"Warehouse {index}",
        )

    response = operations_api_client.get("/api/v1/warehouses/")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 25
    assert len(data["results"]) == 20
    assert data["next"] is not None
    assert data["previous"] is None


@pytest.mark.django_db
def test_anonymous_warehouse_list_requires_authentication():
    response = APIClient().get("/api/v1/warehouses/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_warehouse_detail_requires_authentication():
    warehouse = Warehouse.objects.create(
        code="WH-001",
        name="Main Warehouse",
    )

    response = APIClient().get(
        f"/api/v1/warehouses/{warehouse.id}/"
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_can_read_warehouses(admin_api_client):
    response = admin_api_client.get("/api/v1/warehouses/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_operations_can_read_warehouses(operations_api_client):
    response = operations_api_client.get("/api/v1/warehouses/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_read_only_can_read_warehouses(read_only_api_client):
    response = read_only_api_client.get("/api/v1/warehouses/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_warehouse_serializer_exposes_read_only_representation(
    operations_api_client,
):
    warehouse = Warehouse.objects.create(
        code="WH-001",
        name="Main Warehouse",
        location="Athens",
        active=False,
    )

    response = operations_api_client.get(
        f"/api/v1/warehouses/{warehouse.id}/"
    )

    assert response.status_code == 200

    data = response.json()

    assert set(data) == {
        "id",
        "code",
        "name",
        "location",
        "active",
        "created_at",
        "modified_at",
    }
    assert data["active"] is False
