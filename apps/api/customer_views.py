from rest_framework import generics

from apps.customers.models import Customer

from apps.api.serializers import CustomerSerializer
from apps.accounts.permissions import CustomerAccessPermission


class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [CustomerAccessPermission]


class CustomerDetailView(generics.RetrieveAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [CustomerAccessPermission]
    lookup_field = "id"
    lookup_url_kwarg = "customer_id"
