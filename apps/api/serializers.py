from rest_framework import serializers

from apps.customers.models import Customer
from apps.products.models import Product


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