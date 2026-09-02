import uuid

from django.db import models
from django.db.models import Q

from apps.customers.models import Customer
from apps.products.models import Product


class SalesOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        SHIPPED = "SHIPPED", "Shipped"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default="DRAFT",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "DRAFT",
                        "CONFIRMED",
                        "SHIPPED",
                        "COMPLETED",
                        "CANCELLED",
                    ]
                ),
                name="salesorder_valid_status",
            ),
        ]

    def __str__(self):
        return f"{self.id} - {self.status}"


class SalesOrderLine(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_lines",
    )
    quantity = models.IntegerField()
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_lines"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="orderline_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="orderline_unit_price_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.order_id} - {self.product.sku}"
