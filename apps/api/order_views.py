from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import CustomerAccessPermission
from apps.api.serializers import OrderSerializer
from apps.orders.models import SalesOrder
from apps.orders.services import (
    cancel_order,
    complete_order,
    confirm_order,
    ship_order,
)


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


class OrderConfirmView(APIView):
    permission_classes = [CustomerAccessPermission]

    def post(self, request, order_id):
        order = confirm_order(order_id)
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )


class OrderCancelView(APIView):
    permission_classes = [CustomerAccessPermission]

    def post(self, request, order_id):
        order = cancel_order(order_id)
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )


class OrderShipView(APIView):
    permission_classes = [CustomerAccessPermission]

    def post(self, request, order_id):
        order = ship_order(order_id)
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )


class OrderCompleteView(APIView):
    permission_classes = [CustomerAccessPermission]

    def post(self, request, order_id):
        order = complete_order(order_id)
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )
