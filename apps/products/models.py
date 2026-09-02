import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Product(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    sku = models.CharField(
        max_length=64,
        unique=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(
        null=True,
        blank=True,
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        constraints = [
            models.CheckConstraint(
                condition=~Q(sku=""),
                name="product_sku_non_empty",
            ),
            models.CheckConstraint(
                condition=~Q(name=""),
                name="product_name_non_empty",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="product_unit_price_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"
