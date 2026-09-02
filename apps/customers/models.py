import uuid

from django.db import models
from django.db.models import Q


class Customer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=255)
    email = models.CharField(
        max_length=254,
        null=True,
        blank=True,
    )
    phone = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        constraints = [
            models.CheckConstraint(
                condition=~Q(name=""),
                name="customer_name_non_empty",
            ),
        ]

    def __str__(self):
        return self.name
