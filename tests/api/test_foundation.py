import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_api_v1_root_is_available():
    client = APIClient()

    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Django ERP Operations Platform API",
        "version": "1.0",
        "status": "ok",
    }
