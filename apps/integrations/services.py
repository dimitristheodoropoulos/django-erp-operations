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

        # Look up the order
        received_at = timezone.now()
        try:
            order = SalesOrder.objects.select_for_update().get(id=order_id)
        except SalesOrder.DoesNotExist:
            # Persist failed event
            event = ExternalEvent.objects.create(
                external_event_id=external_event_id,
                event_type=event_type,
                order_id=None,
                payment_amount=payment_amount,
                processing_status=ExternalEvent.ProcessingStatus.FAILED,
                received_at=received_at,
                error_message="The referenced sales order does not exist.",
            )
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

        # Create successful event
        event = ExternalEvent.objects.create(
            external_event_id=external_event_id,
            event_type=event_type,
            order=order,
            payment_amount=payment_amount,
            processing_status=ExternalEvent.ProcessingStatus.PROCESSED,
            received_at=received_at,
            processed_at=received_at,
        )

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
