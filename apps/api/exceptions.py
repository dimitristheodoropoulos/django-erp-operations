"""
Centralized DRF exception handler and custom exceptions for the ERP API.
"""

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.orders.exceptions import (
    OrderNotFound,
    InvalidOrderState,
    InactiveCustomer,
    OrderHasNoLines,
    InvalidOrderQuantity,
    InactiveProduct,
    InsufficientStock,
    OrderConfirmationError,
)
from apps.integrations.exceptions import PaymentWebhookFailed
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Central exception handler for the ERP API.

    Transforms:
      - Business exceptions (OrderConfirmationError subclasses) into structured error responses.
      - DRF ValidationError into a structured envelope with details.
      - DRF's own exceptions (AuthenticationFailed, PermissionDenied, etc.) into our envelope.
      - Unexpected exceptions into a safe 500 response with INTERNAL_ERROR code.
    """

    # Handle our business exceptions first
    if isinstance(exc, OrderConfirmationError):
        # Base mapping for most business exceptions
        mapping = {
            OrderNotFound: (
                "ORDER_NOT_FOUND",
                "The requested order does not exist.",
                status.HTTP_404_NOT_FOUND,
            ),
            InactiveCustomer: (
                "INACTIVE_CUSTOMER",
                "The order customer is inactive.",
                status.HTTP_409_CONFLICT,
            ),
            OrderHasNoLines: (
                "ORDER_HAS_NO_LINES",
                "An order must contain at least one line before confirmation.",
                status.HTTP_409_CONFLICT,
            ),
            InvalidOrderQuantity: (
                "INVALID_ORDER_QUANTITY",
                "Order line quantity must be greater than zero.",
                status.HTTP_400_BAD_REQUEST,
            ),
            InactiveProduct: (
                "INACTIVE_PRODUCT",
                "The order contains an inactive product.",
                status.HTTP_409_CONFLICT,
            ),
        }

        code, message, http_status = mapping.get(
            type(exc),
            ("BUSINESS_ERROR", "A business rule violation occurred.", status.HTTP_409_CONFLICT),
        )

        view = context.get("view")
        view_name = view.__class__.__name__ if view else None

        # Special handling for InvalidOrderState with operation-specific messages
        if isinstance(exc, InvalidOrderState):
            lifecycle_messages = {
                "OrderConfirmView": "The order cannot be confirmed from its current state.",
                "OrderCancelView": "The order cannot be cancelled from its current state.",
                "OrderShipView": "The order cannot be shipped from its current state.",
                "OrderCompleteView": "The order cannot be completed from its current state.",
            }
            code = "INVALID_ORDER_STATE"
            message = lifecycle_messages.get(
                view_name,
                "The order cannot be transitioned from its current state.",
            )
            http_status = status.HTTP_409_CONFLICT

        # Special handling for InsufficientStock with operation-specific messages
        elif isinstance(exc, InsufficientStock):
            stock_messages = {
                "OrderConfirmView": "Insufficient stock to confirm the order.",
                "OrderShipView": "Insufficient stock to ship the order.",
            }
            code = "INSUFFICIENT_STOCK"
            message = stock_messages.get(
                view_name,
                "Insufficient stock to process the order.",
            )
            http_status = status.HTTP_409_CONFLICT

        return Response(
            {
                "error": {
                    "code": code,
                    "message": message,
                }
            },
            status=http_status,
        )

    # Handle payment webhook failure
    if isinstance(exc, PaymentWebhookFailed):
        # Do not expose external_event_id in the error response
        return Response(
            {
                "error": {
                    "code": "PAYMENT_WEBHOOK_FAILED",
                    "message": exc.message,
                }
            },
            status=status.HTTP_409_CONFLICT,
        )

    # Let DRF handle other exceptions (like ValidationError)
    response = drf_exception_handler(exc, context)

    # If response is None, DRF couldn't handle it -> unexpected error
    if response is None:
        # Log the unexpected exception with a safe structured event
        # Do NOT include exception message or traceback in the log message
        view = context.get("view")
        view_name = view.__class__.__name__ if view else None
        request = context.get("request")

        # Safe structured logging without exposing exception details
        logger.error(
            "unexpected_application_error",
            extra={
                "event": "unexpected_application_error",
                "exception_type": type(exc).__name__,
                "view": view_name,
                "method": request.method if request else None,
                "path": request.path if request else None,
            },
            # exc_info=False ensures we don't log traceback or exception message
            exc_info=False,
        )

        return Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # For DRF ValidationError (including those raised by serializers), we keep the details
    if isinstance(exc, (DRFValidationError, DjangoValidationError)):
        error_data = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": response.data,
            }
        }
        response.data = error_data
        return response

    # For other DRF exceptions (AuthenticationFailed, PermissionDenied, etc.),
    # we transform to our envelope while keeping the original status code.
    # We try to extract a meaningful message.
    error_message = "An error occurred processing your request."
    if hasattr(exc, "detail"):
        if isinstance(exc.detail, dict):
            # For validation errors that might have slipped, but they are already handled above.
            error_message = str(exc.detail)
        elif isinstance(exc.detail, list):
            error_message = exc.detail[0] if exc.detail else error_message
        else:
            error_message = str(exc.detail)

    # Override response data
    response.data = {
        "error": {
            "code": "REQUEST_ERROR",
            "message": error_message,
        }
    }
    return response
