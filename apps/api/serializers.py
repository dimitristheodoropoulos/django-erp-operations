from decimal import Decimal

from rest_framework import serializers

from apps.customers.models import Customer
from apps.products.models import Product
from apps.warehouses.models import Warehouse
from apps.inventory.models import StockItem
from apps.orders.models import SalesOrder, SalesOrderLine


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "active",
            "created_at",
            "modified_at",
        ]
        read_only_fields = [
            "id",
            "active",
            "created_at",
            "modified_at",
        ]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Customer name must not be empty."
            )
        return value


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "description",
            "unit_price",
            "active",
            "created_at",
            "modified_at",
        ]
        read_only_fields = [
            "id",
            "active",
            "created_at",
            "modified_at",
        ]

    def validate_sku(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Product SKU must not be empty."
            )
        return value

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Product name must not be empty."
            )
        return value


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            "id",
            "code",
            "name",
            "location",
            "active",
            "created_at",
            "modified_at",
        ]
        read_only_fields = [
            "id",
            "code",
            "name",
            "location",
            "active",
            "created_at",
            "modified_at",
        ]


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockItem
        fields = [
            "id",
            "product",
            "warehouse",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "created_at",
            "modified_at",
        ]
        read_only_fields = [
            "id",
            "product",
            "warehouse",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "created_at",
            "modified_at",
        ]


class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderLine
        fields = [
            "id",
            "product",
            "quantity",
            "unit_price",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "unit_price",
            "created_at",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Order line quantity must be greater than zero."
            )
        return value


class OrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = [
            "id",
            "customer",
            "status",
            "lines",
            "created_at",
            "modified_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "modified_at",
        ]

    def to_internal_value(self, data):
        # Reject client-supplied unit_price for order lines
        for line in data.get("lines", []):
            if "unit_price" in line:
                raise serializers.ValidationError(
                    {
                        "lines": [
                            {
                                "unit_price": "Unit price is set by the server."
                            }
                        ]
                    }
                )

        return super().to_internal_value(data)

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError(
                "Order must contain at least one line."
            )
        return value

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")

        order = SalesOrder.objects.create(
            status=SalesOrder.Status.DRAFT,
            **validated_data,
        )

        SalesOrderLine.objects.bulk_create(
            [
                SalesOrderLine(
                    order=order,
                    product=line_data["product"],
                    quantity=line_data["quantity"],
                    unit_price=line_data["product"].unit_price,
                )
                for line_data in lines_data
            ]
        )

        return order


class PaymentWebhookSerializer(serializers.Serializer):
    external_event_id = serializers.CharField(
        max_length=255,
        required=True,
    )
    event_type = serializers.CharField(
        max_length=64,
        required=True,
    )
    order_id = serializers.UUIDField(
        required=True,
    )
    payment_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        min_value=Decimal("0.00"),
    )