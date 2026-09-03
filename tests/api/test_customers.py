import pytest
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.customers.models import Customer


@pytest.fixture
def authenticated_client(db):
    def make_client(role_name):
        user = User.objects.create_user(
            username=f"user_{role_name.lower()}",
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
def admin_client(authenticated_client):
    return authenticated_client("ADMIN")


@pytest.fixture
def operations_client(authenticated_client):
    return authenticated_client("OPERATIONS")


@pytest.fixture
def read_only_client(authenticated_client):
    return authenticated_client("READ_ONLY")


@pytest.mark.django_db
def test_customer_list_returns_customers(operations_client):
    Customer.objects.create(
        name="Customer One",
        email="one@example.com",
        phone="+301111111111",
    )
    Customer.objects.create(
        name="Customer Two",
        email="two@example.com",
    )

    response = operations_client.get("/api/v1/customers/")

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert len(response.json()["results"]) == 2


@pytest.mark.django_db
def test_customer_retrieve_returns_customer(operations_client):
    customer = Customer.objects.create(
        name="Example Customer",
        email="customer@example.com",
    )

    response = operations_client.get(
        f"/api/v1/customers/{customer.id}/"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(customer.id)
    assert response.json()["name"] == "Example Customer"
    assert response.json()["email"] == "customer@example.com"
    assert response.json()["active"] is True


@pytest.mark.django_db
def test_customer_retrieve_unknown_customer_returns_404(operations_client):
    response = operations_client.get(
        "/api/v1/customers/00000000-0000-0000-0000-000000000000/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_customer_create_returns_201_and_server_managed_fields(
    operations_client,
):
    response = operations_client.post(
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
def test_customer_create_rejects_empty_name(operations_client):
    response = operations_client.post(
        "/api/v1/customers/",
        {
            "name": "   ",
            "email": "invalid@example.com",
        },
        format="json",
    )

    assert response.status_code == 400
    # New error envelope: details are nested under error.details
    assert response.json()["error"]["details"]["name"] == [
        "This field may not be blank."
    ]


@pytest.mark.django_db
def test_customer_create_does_not_allow_client_to_set_active(
    operations_client,
):
    response = operations_client.post(
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
def test_customer_retrieve_exposes_inactive_state(operations_client):
    customer = Customer.objects.create(
        name="Inactive Customer",
        active=False,
    )

    response = operations_client.get(
        f"/api/v1/customers/{customer.id}/"
    )

    assert response.status_code == 200
    assert response.json()["active"] is False


@pytest.mark.django_db
def test_anonymous_customer_list_requires_authentication():
    response = APIClient().get("/api/v1/customers/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_customer_detail_requires_authentication():
    customer = Customer.objects.create(
        name="Protected Customer",
    )

    response = APIClient().get(
        f"/api/v1/customers/{customer.id}/"
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_customer_create_requires_authentication():
    response = APIClient().post(
        "/api/v1/customers/",
        {"name": "Unauthorized Customer"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_can_read_customers(admin_client):
    response = admin_client.get("/api/v1/customers/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_can_create_customers(admin_client):
    response = admin_client.post(
        "/api/v1/customers/",
        {"name": "Admin Customer"},
        format="json",
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_operations_can_read_customers(operations_client):
    response = operations_client.get("/api/v1/customers/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_operations_can_create_customers(operations_client):
    response = operations_client.post(
        "/api/v1/customers/",
        {"name": "Operations Customer"},
        format="json",
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_read_only_can_read_customers(read_only_client):
    response = read_only_client.get("/api/v1/customers/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_read_only_cannot_create_customers(read_only_client):
    response = read_only_client.post(
        "/api/v1/customers/",
        {"name": "Read Only Customer"},
        format="json",
    )

    assert response.status_code == 403