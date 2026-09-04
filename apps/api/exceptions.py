"""
Centralized DRF exception handler and custom exceptions for the ERP API.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.integrations.exceptions import PaymentWebhookFailed
from apps.orders.exceptions import (
    InactiveCustomer,
    InactiveProduct,
    InsufficientStock,
    InvalidOrderQuantity,
    InvalidOrderState,
    OrderConfirmationError,
    OrderHasNoLines,
    OrderNotFound,
)

logger = logging.getLogger(__name__)


def _log_request_failure(
    *,
    failure_type,
    response,
    context,
    error_code=None,
):
    """Log a request failure using safe, non-sensitive metadata only."""

    request = context.get("request")
    view = context.get("view")
    view_name = view.__class__.__name__ if view else None

    if view_name == "OrderListCreateView":
        view_name = "OrderCreateView"

    logger.warning(
        "request_failure",
        extra={
            "event": "request_failure",
            "failure_type": failure_type,
            "status_code": response.status_code,
            "error_code": error_code,
            "method": request.method if request else None,
            "view": view_name,
            "path": request.path if request else None,
        },
    )


def custom_exception_handler(exc, context):
    """
    Central exception handler for the ERP API.

    Transforms:
      - Business exceptions (OrderConfirmationError subclasses) into structured error responses.
      - DRF ValidationError into a structured envelope with details.
      - DRF's own exceptions (AuthenticationFailed, PermissionDenied, etc.) into our envelope.
      - Unexpected exceptions into a safe 500 response with INTERNAL_ERROR code.
    """

    # Handle our business exceptions first.
    if isinstance(exc, OrderConfirmationError):
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
            (
                "BUSINESS_ERROR",
                "A business rule violation occurred.",
                status.HTTP_409_CONFLICT,
            ),
        )

        view = context.get("view")
        view_name = view.__class__.__name__ if view else None

        if isinstance(exc, InvalidOrderState):
            lifecycle_messages = {
                "OrderConfirmView": (
                    "The order cannot be confirmed from its current state."
                ),
                "OrderCancelView": (
                    "The order cannot be cancelled from its current state."
                ),
                "OrderShipView": (
                    "The order cannot be shipped from its current state."
                ),
                "OrderCompleteView": (
                    "The order cannot be completed from its current state."
                ),
            }
            code = "INVALID_ORDER_STATE"
            message = lifecycle_messages.get(
                view_name,
                "The order cannot be transitioned from its current state.",
            )
            http_status = status.HTTP_409_CONFLICT

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

        response = Response(
            {
                "error": {
                    "code": code,
                    "message": message,
                }
            },
            status=http_status,
        )

        _log_request_failure(
            failure_type="business",
            response=response,
            context=context,
            error_code=code,
        )

        return response

    # Handle payment webhook failure.
    if isinstance(exc, PaymentWebhookFailed):
        response = Response(
            {
                "error": {
                    "code": "PAYMENT_WEBHOOK_FAILED",
                    "message": exc.message,
                }
            },
            status=status.HTTP_409_CONFLICT,
        )

        return response

    # Let DRF handle other exceptions.
    response = drf_exception_handler(exc, context)

    # If response is None, DRF couldn't handle it -> unexpected error.
    if response is None:
        view = context.get("view")
        view_name = view.__class__.__name__ if view else None
        request = context.get("request")

        logger.error(
            "unexpected_application_error",
            extra={
                "event": "unexpected_application_error",
                "exception_type": type(exc).__name__,
                "view": view_name,
                "method": request.method if request else None,
                "path": request.path if request else None,
            },
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

    # Validation failures.
    if isinstance(exc, (DRFValidationError, DjangoValidationError)):
        error_data = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": response.data,
            }
        }
        response.data = error_data

        _log_request_failure(
            failure_type="validation",
            response=response,
            context=context,
            error_code="VALIDATION_ERROR",
        )

        return response

    # Authentication failures.
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        response.data = {
            "error": {
                "code": "REQUEST_ERROR",
                "message": (
                    "Authentication credentials were not provided or were invalid."
                ),
            }
        }

        _log_request_failure(
            failure_type="authentication",
            response=response,
            context=context,
            error_code="REQUEST_ERROR",
        )

        return response

    # Permission failures.
    if isinstance(exc, PermissionDenied):
        response.data = {
            "error": {
                "code": "REQUEST_ERROR",
                "message": "You do not have permission to perform this action.",
            }
        }

        _log_request_failure(
            failure_type="permission",
            response=response,
            context=context,
            error_code="REQUEST_ERROR",
        )

        return response

    # Other DRF exceptions.
    error_message = "An error occurred processing your request."
    if hasattr(exc, "detail"):
        if isinstance(exc.detail, dict):
            error_message = str(exc.detail)
        elif isinstance(exc.detail, list):
            error_message = exc.detail[0] if exc.detail else error_message
        else:
            error_message = str(exc.detail)

    response.data = {
        "error": {
            "code": "REQUEST_ERROR",
            "message": error_message,
        }
    }

    return response