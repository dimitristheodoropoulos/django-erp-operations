import uuid

from django.db import models
from django.db.models import Q

from apps.orders.models import SalesOrder


class ExternalEvent(models.Model):
    class ProcessingStatus(models.TextChoices):
        RECEIVED = "RECEIVED", "Received"
        PROCESSED = "PROCESSED", "Processed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    external_event_id = models.CharField(
        max_length=255,
        unique=True,
    )
    event_type = models.CharField(max_length=64)
    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.PROTECT,
        related_name="external_events",
        null=True,
        blank=True,
    )
    payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    processing_status = models.CharField(
        max_length=32,
        choices=ProcessingStatus.choices,
        default="RECEIVED",
    )
    received_at = models.DateTimeField()
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    error_message = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "integration_external_events"
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    processing_status__in=[
                        "RECEIVED",
                        "PROCESSED",
                        "FAILED",
                    ]
                ),
                name="externalevent_valid_processing_status",
            ),
            models.CheckConstraint(
                condition=(
                    Q(payment_amount__isnull=True)
                    | Q(payment_amount__gte=0)
                ),
                name="externalevent_payment_amount_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.external_event_id} - {self.processing_status}"
