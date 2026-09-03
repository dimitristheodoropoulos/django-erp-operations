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
        try:
            order = confirm_order(order_id)
        except OrderNotFound:
            return Response(
                {
                    "error": {
                        "code": "ORDER_NOT_FOUND",
                        "message": "The requested order does not exist.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except InvalidOrderQuantity:
            return Response(
                {
                    "error": {
                        "code": "INVALID_ORDER_QUANTITY",
                        "message": "Order line quantity must be greater than zero.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InvalidOrderState:
            return Response(
                {
                    "error": {
                        "code": "INVALID_ORDER_STATE",
                        "message": "The order cannot be confirmed from its current state.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        except InactiveCustomer:
            return Response(
                {
                    "error": {
                        "code": "INACTIVE_CUSTOMER",
                        "message": "The order customer is inactive.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        except OrderHasNoLines:
            return Response(
                {
                    "error": {
                        "code": "ORDER_HAS_NO_LINES",
                        "message": "An order must contain at least one line before confirmation.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        except InactiveProduct:
            return Response(
                {
                    "error": {
                        "code": "INACTIVE_PRODUCT",
                        "message": "The order contains an inactive product.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        except InsufficientStock:
            return Response(
                {
                    "error": {
                        "code": "INSUFFICIENT_STOCK",
                        "message": "Insufficient stock to confirm the order.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )


class OrderCancelView(APIView):
    permission_classes = [CustomerAccessPermission]

    def post(self, request, order_id):
        try:
            order = cancel_order(order_id)
        except OrderNotFound:
            return Response(
                {
                    "error": {
                        "code": "ORDER_NOT_FOUND",
                        "message": "The requested order does not exist.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except InvalidOrderState:
            return Response(
                {
                    "error": {
                        "code": "INVALID_ORDER_STATE",
                        "message": "The order cannot be cancelled from its current state.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )


class OrderShipView(APIView):
    permission_classes = [CustomerAccessPermission]

    def post(self, request, order_id):
        try:
            order = ship_order(order_id)
        except OrderNotFound:
            return Response(
                {
                    "error": {
                        "code": "ORDER_NOT_FOUND",
                        "message": "The requested order does not exist.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except InvalidOrderState:
            return Response(
                {
                    "error": {
                        "code": "INVALID_ORDER_STATE",
                        "message": "The order cannot be shipped from its current state.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        except InsufficientStock:
            return Response(
                {
                    "error": {
                        "code": "INSUFFICIENT_STOCK",
                        "message": "Insufficient stock to ship the order.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )


class OrderCompleteView(APIView):
    permission_classes = [CustomerAccessPermission]

    def post(self, request, order_id):
        try:
            order = complete_order(order_id)
        except OrderNotFound:
            return Response(
                {
                    "error": {
                        "code": "ORDER_NOT_FOUND",
                        "message": "The requested order does not exist.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except InvalidOrderState:
            return Response(
                {
                    "error": {
                        "code": "INVALID_ORDER_STATE",
                        "message": "The order cannot be completed from its current state.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )