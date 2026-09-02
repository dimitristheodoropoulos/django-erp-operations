from rest_framework import generics

from apps.accounts.permissions import CustomerAccessPermission
from apps.api.serializers import InventorySerializer
from apps.inventory.models import StockItem


class InventoryListView(generics.ListAPIView):
    queryset = StockItem.objects.all().order_by("id")
    serializer_class = InventorySerializer
    permission_classes = [CustomerAccessPermission]


class InventoryDetailView(generics.RetrieveAPIView):
    queryset = StockItem.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [CustomerAccessPermission]
    lookup_field = "id"
    lookup_url_kwarg = "inventory_id"
