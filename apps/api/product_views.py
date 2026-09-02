from rest_framework import generics

from apps.accounts.permissions import CustomerAccessPermission
from apps.api.serializers import ProductSerializer
from apps.products.models import Product


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    permission_classes = [CustomerAccessPermission]


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [CustomerAccessPermission]
    lookup_field = "id"
    lookup_url_kwarg = "product_id"
