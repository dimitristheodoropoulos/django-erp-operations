import uuid

from django.db import models
from django.db.models import F, Q

from apps.products.models import Product
from apps.warehouses.models import Warehouse


class StockItem(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_items",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stock_items",
    )
    quantity = models.IntegerField()
    reserved_quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_stock_items"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "warehouse"],
                name="stockitem_product_warehouse_unique",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name="stockitem_quantity_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(reserved_quantity__gte=0),
                name="stockitem_reserved_quantity_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(reserved_quantity__lte=F("quantity")),
                name="stockitem_reserved_lte_quantity",
            ),
        ]

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.code}"
