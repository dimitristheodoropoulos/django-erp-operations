from rest_framework import generics

from apps.accounts.permissions import CustomerAccessPermission
from apps.api.serializers import WarehouseSerializer
from apps.warehouses.models import Warehouse


class WarehouseListView(generics.ListAPIView):
    queryset = Warehouse.objects.all().order_by("id")
    serializer_class = WarehouseSerializer
    permission_classes = [CustomerAccessPermission]


class WarehouseDetailView(generics.RetrieveAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [CustomerAccessPermission]
    lookup_field = "id"
    lookup_url_kwarg = "warehouse_id"
