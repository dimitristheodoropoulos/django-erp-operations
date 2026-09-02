from rest_framework import generics

from apps.accounts.permissions import CustomerAccessPermission
from apps.api.serializers import OrderSerializer
from apps.orders.models import SalesOrder


class OrderListCreateView(generics.ListCreateAPIView):
    queryset = (
        SalesOrder.objects
        .select_related("customer")
        .prefetch_related("lines__product")
        .order_by("id")
    )
    serializer_class = OrderSerializer
    permission_classes = [CustomerAccessPermission]


class OrderDetailView(generics.RetrieveAPIView):
    queryset = (
        SalesOrder.objects
        .select_related("customer")
        .prefetch_related("lines__product")
    )
    serializer_class = OrderSerializer
    permission_classes = [CustomerAccessPermission]
    lookup_field = "id"
    lookup_url_kwarg = "order_id"
