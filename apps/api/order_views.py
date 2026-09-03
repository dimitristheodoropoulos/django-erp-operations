from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import CustomerAccessPermission
from apps.api.serializers import OrderSerializer
from apps.orders.exceptions import (
    InactiveCustomer,
    InactiveProduct,
    InsufficientStock,
    InvalidOrderQuantity,
    InvalidOrderState,
    OrderHasNoLines,
    OrderNotFound,
)
from apps.orders.models import SalesOrder
from apps.orders.services import confirm_order


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
        try:
            order = confirm_order(order_id)
        except OrderNotFound:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except InvalidOrderQuantity:
            return Response(
                {"detail": "Order contains an invalid quantity."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (
            InvalidOrderState,
            InactiveCustomer,
            InactiveProduct,
            OrderHasNoLines,
            InsufficientStock,
        ):
            return Response(
                {"detail": "Order cannot be confirmed."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )
