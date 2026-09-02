from rest_framework import serializers

from apps.customers.models import Customer


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
