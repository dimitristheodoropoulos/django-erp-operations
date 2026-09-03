from django.db import transaction
from django.utils import timezone

from apps.integrations.models import ExternalEvent
from apps.orders.models import SalesOrder


@transaction.atomic
def process_payment_webhook(
    *,
    external_event_id,
    event_type,
    order_id,
    payment_amount,
):
    existing_event = (
        ExternalEvent.objects
        .select_for_update()
        .filter(external_event_id=external_event_id)
        .first()
    )

    if existing_event is not None:
        return existing_event

    received_at = timezone.now()

    try:
        order = SalesOrder.objects.get(id=order_id)
    except SalesOrder.DoesNotExist:
        return ExternalEvent.objects.create(
            external_event_id=external_event_id,
            event_type=event_type,
            order=None,
            payment_amount=payment_amount,
            processing_status=ExternalEvent.ProcessingStatus.FAILED,
            received_at=received_at,
            error_message="The referenced sales order does not exist.",
        )

    return ExternalEvent.objects.create(
        external_event_id=external_event_id,
        event_type=event_type,
        order=order,
        payment_amount=payment_amount,
        processing_status=ExternalEvent.ProcessingStatus.PROCESSED,
        received_at=received_at,
        processed_at=received_at,
    )
