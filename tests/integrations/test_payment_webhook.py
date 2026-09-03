import pytest
from rest_framework.test import APIClient
from decimal import Decimal

from apps.integrations.models import ExternalEvent
from apps.orders.models import SalesOrder


@pytest.mark.django_db
def test_valid_payment_webhook_is_processed(
    order,
    admin_user,
):
    client = APIClient()
    client.force_authenticate(user=admin_user)

    payload = {
        "external_event_id": "evt-001",
        "event_type": "PAYMENT_RECEIVED",
        "order_id": str(order.id),
        "payment_amount": "125.00",
    }

    response = client.post(
        "/api/v1/webhooks/payment/",
        payload,
        format="json",
    )

    assert response.status_code == 200

    event = ExternalEvent.objects.get(
        external_event_id="evt-001"
    )

    assert event.event_type == "PAYMENT_RECEIVED"
    assert event.order_id == order.id
    assert event.payment_amount == Decimal("125.00")
    assert event.processing_status == ExternalEvent.ProcessingStatus.PROCESSED
    assert event.processed_at is not None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload",
    [
        {
            "event_type": "PAYMENT_RECEIVED",
            "order_id": "00000000-0000-0000-0000-000000000000",
            "payment_amount": "125.00",
        },
        {
            "external_event_id": "evt-invalid-type",
            "order_id": "00000000-0000-0000-0000-000000000000",
            "payment_amount": "125.00",
        },
        {
            "external_event_id": "evt-invalid-order",
            "event_type": "PAYMENT_RECEIVED",
            "payment_amount": "125.00",
        },
        {
            "external_event_id": "evt-invalid-amount",
            "event_type": "PAYMENT_RECEIVED",
            "order_id": "00000000-0000-0000-0000-000000000000",
            "payment_amount": "-1.00",
        },
    ],
)
def test_invalid_payment_webhook_payload_is_rejected(
    payload,
    admin_user,
):
    client = APIClient()
    client.force_authenticate(user=admin_user)

    response = client.post(
        "/api/v1/webhooks/payment/",
        payload,
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_duplicate_payment_webhook_is_idempotent(
    order,
    admin_user,
):
    client = APIClient()
    client.force_authenticate(user=admin_user)

    payload = {
        "external_event_id": "evt-duplicate",
        "event_type": "PAYMENT_RECEIVED",
        "order_id": str(order.id),
        "payment_amount": "125.00",
    }

    first = client.post(
        "/api/v1/webhooks/payment/",
        payload,
        format="json",
    )
    second = client.post(
        "/api/v1/webhooks/payment/",
        payload,
        format="json",
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert ExternalEvent.objects.filter(
        external_event_id="evt-duplicate"
    ).count() == 1


@pytest.mark.django_db
def test_unknown_order_webhook_is_recorded_as_failed(
    admin_user,
):
    client = APIClient()
    client.force_authenticate(user=admin_user)

    payload = {
        "external_event_id": "evt-unknown-order",
        "event_type": "PAYMENT_RECEIVED",
        "order_id": "00000000-0000-0000-0000-000000000000",
        "payment_amount": "125.00",
    }

    response = client.post(
        "/api/v1/webhooks/payment/",
        payload,
        format="json",
    )

    assert response.status_code == 409

    event = ExternalEvent.objects.get(
        external_event_id="evt-unknown-order"
    )

    assert event.processing_status == ExternalEvent.ProcessingStatus.FAILED
    assert event.error_message


@pytest.mark.django_db
def test_failed_webhook_does_not_modify_order(
    order,
    admin_user,
):
    original_status = order.status

    client = APIClient()
    client.force_authenticate(user=admin_user)

    payload = {
        "external_event_id": "evt-failed-order",
        "event_type": "PAYMENT_RECEIVED",
        "order_id": str(order.id),
        "payment_amount": "-10.00",
    }

    response = client.post(
        "/api/v1/webhooks/payment/",
        payload,
        format="json",
    )

    assert response.status_code == 400

    order.refresh_from_db()

    assert order.status == original_status