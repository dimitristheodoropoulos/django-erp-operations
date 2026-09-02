from rest_framework import generics

from apps.customers.models import Customer

from apps.api.serializers import CustomerSerializer


class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer


class CustomerDetailView(generics.RetrieveAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    lookup_field = "id"
    lookup_url_kwarg = "customer_id"
