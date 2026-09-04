from decimal import Decimal
import uuid

import pytest
from rest_framework.test import APIClient

from apps.integrations.models import ExternalEvent


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


@pytest.mark.django_db(transaction=True)
def test_concurrent_first_delivery_of_same_payment_webhook_is_idempotent(
    order,
):
    """Concurrent first deliveries of the same event must create one event."""
    import threading

    from django.db import close_old_connections

    from apps.integrations.services import process_payment_webhook

    external_event_id = "evt-concurrent-first-delivery"
    results = []
    errors = []
    barrier = threading.Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait()
            event = process_payment_webhook(
                external_event_id=external_event_id,
                event_type="PAYMENT_RECEIVED",
                order_id=order.id,
                payment_amount=Decimal("125.00"),
            )
            results.append(event.processing_status)
        except Exception as exc:
            errors.append(exc)
        finally:
            close_old_connections()

    thread_a = threading.Thread(target=worker)
    thread_b = threading.Thread(target=worker)

    thread_a.start()
    thread_b.start()

    thread_a.join()
    thread_b.join()

    assert not errors
    assert len(results) == 2
    assert all(
        status == ExternalEvent.ProcessingStatus.PROCESSED
        for status in results
    )

    assert ExternalEvent.objects.filter(
        external_event_id=external_event_id
    ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_first_delivery_of_unknown_order_is_idempotent():
    """Concurrent deliveries for an unknown order must create one FAILED event."""
    import threading

    from django.db import close_old_connections

    from apps.integrations.services import process_payment_webhook

    unknown_order_id = uuid.uuid4()
    external_event_id = "evt-concurrent-unknown-order"
    results = []
    errors = []
    barrier = threading.Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait()
            event = process_payment_webhook(
                external_event_id=external_event_id,
                event_type="PAYMENT_RECEIVED",
                order_id=unknown_order_id,
                payment_amount=Decimal("125.00"),
            )
            results.append(event.processing_status)
        except Exception as exc:
            errors.append(exc)
        finally:
            close_old_connections()

    thread_a = threading.Thread(target=worker)
    thread_b = threading.Thread(target=worker)

    thread_a.start()
    thread_b.start()

    thread_a.join()
    thread_b.join()

    assert not errors
    assert len(results) == 2
    assert all(
        status == ExternalEvent.ProcessingStatus.FAILED
        for status in results
    )

    assert ExternalEvent.objects.filter(
        external_event_id=external_event_id
    ).count() == 1
