import uuid

from django.db import models
from django.db.models import Q


class Warehouse(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    code = models.CharField(
        max_length=64,
        unique=True,
    )
    name = models.CharField(max_length=255)
    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "warehouses"
        constraints = [
            models.CheckConstraint(
                condition=~Q(code=""),
                name="warehouse_code_non_empty",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"
