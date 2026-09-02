import pytest
from rest_framework.test import APIClient

from apps.customers.models import Customer


@pytest.mark.django_db
def test_customer_list_returns_customers():
    Customer.objects.create(
        name="Customer One",
        email="one@example.com",
        phone="+301111111111",
    )
    Customer.objects.create(
        name="Customer Two",
        email="two@example.com",
    )

    response = APIClient().get("/api/v1/customers/")

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert len(response.json()["results"]) == 2


@pytest.mark.django_db
def test_customer_retrieve_returns_customer():
    customer = Customer.objects.create(
        name="Example Customer",
        email="customer@example.com",
    )

    response = APIClient().get(
        f"/api/v1/customers/{customer.id}/"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(customer.id)
    assert response.json()["name"] == "Example Customer"
    assert response.json()["email"] == "customer@example.com"
    assert response.json()["active"] is True


@pytest.mark.django_db
def test_customer_retrieve_unknown_customer_returns_404():
    response = APIClient().get(
        "/api/v1/customers/00000000-0000-0000-0000-000000000000/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_customer_create_returns_201_and_server_managed_fields():
    response = APIClient().post(
        "/api/v1/customers/",
        {
            "name": "New Customer",
            "email": "new@example.com",
            "phone": "+302222222222",
        },
        format="json",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "New Customer"
    assert data["email"] == "new@example.com"
    assert data["phone"] == "+302222222222"
    assert data["active"] is True
    assert data["id"]
    assert data["created_at"]
    assert data["modified_at"]

    assert Customer.objects.filter(
        id=data["id"],
        name="New Customer",
        active=True,
    ).exists()


@pytest.mark.django_db
def test_customer_create_rejects_empty_name():
    response = APIClient().post(
        "/api/v1/customers/",
        {
            "name": "   ",
            "email": "invalid@example.com",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "name" in response.json()


@pytest.mark.django_db
def test_customer_create_does_not_allow_client_to_set_active():
    response = APIClient().post(
        "/api/v1/customers/",
        {
            "name": "State Protected Customer",
            "active": False,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["active"] is True


@pytest.mark.django_db
def test_customer_retrieve_exposes_inactive_state():
    customer = Customer.objects.create(
        name="Inactive Customer",
        active=False,
    )

    response = APIClient().get(
        f"/api/v1/customers/{customer.id}/"
    )

    assert response.status_code == 200
    assert response.json()["active"] is False
