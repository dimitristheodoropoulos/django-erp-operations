import logging
from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.integrations.models import ExternalEvent
from apps.orders.models import SalesOrder

logger = logging.getLogger(__name__)


def process_payment_webhook(
    external_event_id: str,
    event_type: str,
    order_id: UUID,
    payment_amount: Decimal,
) -> ExternalEvent:
    """
    Process an incoming payment webhook.

    Returns:
        ExternalEvent: The persisted event object (either PROCESSED or FAILED).

    Raises:
        None directly; returns FAILED event for unknown orders.
    """
    with transaction.atomic():
        # Check for existing event (idempotency)
        existing = ExternalEvent.objects.filter(
            external_event_id=external_event_id
        ).select_for_update().first()

        if existing:
            logger.info(
                "payment_webhook_duplicate",
                extra={
                    "event": "payment_webhook_duplicate",
                    "external_event_id": external_event_id,
                    "existing_status": existing.processing_status,
                }
            )
            return existing

        # Look up and lock the order before creating the event.
        # Re-check idempotency after acquiring the order lock so concurrent
        # first deliveries of the same event serialize safely.
        received_at = timezone.now()
        try:
            order = SalesOrder.objects.select_for_update().get(id=order_id)
        except SalesOrder.DoesNotExist:
            # Persist failed event. get_or_create() handles concurrent
            # first deliveries through the unique external event ID.
            event, created = ExternalEvent.objects.get_or_create(
                external_event_id=external_event_id,
                defaults={
                    "event_type": event_type,
                    "order_id": None,
                    "payment_amount": payment_amount,
                    "processing_status": ExternalEvent.ProcessingStatus.FAILED,
                    "received_at": received_at,
                    "error_message": (
                        "The referenced sales order does not exist."
                    ),
                },
            )

            if not created:
                logger.info(
                    "payment_webhook_duplicate",
                    extra={
                        "event": "payment_webhook_duplicate",
                        "external_event_id": external_event_id,
                        "existing_status": event.processing_status,
                    }
                )
                return event

            logger.warning(
                "payment_webhook_failed",
                extra={
                    "event": "payment_webhook_failed",
                    "external_event_id": external_event_id,
                    "reason": "unknown_order",
                    "order_id": str(order_id),
                }
            )
            # Return the failed event (do not raise)
            return event

        # Re-check after acquiring the order lock. A concurrent request may
        # have created the event while this request was waiting for the lock.
        existing = ExternalEvent.objects.filter(
            external_event_id=external_event_id
        ).select_for_update().first()

        if existing:
            logger.info(
                "payment_webhook_duplicate",
                extra={
                    "event": "payment_webhook_duplicate",
                    "external_event_id": external_event_id,
                    "existing_status": existing.processing_status,
                }
            )
            return existing

        # get_or_create() also protects the unique event ID if another
        # transaction can race at the database boundary.
        event, created = ExternalEvent.objects.get_or_create(
            external_event_id=external_event_id,
            defaults={
                "event_type": event_type,
                "order": order,
                "payment_amount": payment_amount,
                "processing_status": ExternalEvent.ProcessingStatus.PROCESSED,
                "received_at": received_at,
                "processed_at": received_at,
            },
        )

        if not created:
            logger.info(
                "payment_webhook_duplicate",
                extra={
                    "event": "payment_webhook_duplicate",
                    "external_event_id": external_event_id,
                    "existing_status": event.processing_status,
                }
            )
            return event

        logger.info(
            "payment_webhook_processed",
            extra={
                "event": "payment_webhook_processed",
                "external_event_id": external_event_id,
                "order_id": str(order.id),
                "payment_amount": str(payment_amount),
            }
        )

        return event
