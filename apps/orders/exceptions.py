class OrderConfirmationError(Exception):
    """Base exception for order confirmation failures."""


class OrderNotFound(OrderConfirmationError):
    """Raised when the requested sales order does not exist."""


class InvalidOrderState(OrderConfirmationError):
    """Raised when the sales order is not in DRAFT state."""


class InactiveCustomer(OrderConfirmationError):
    """Raised when the order customer is inactive."""


class OrderHasNoLines(OrderConfirmationError):
    """Raised when the order contains no lines."""


class InvalidOrderQuantity(OrderConfirmationError):
    """Raised when an order line has an invalid quantity."""


class InactiveProduct(OrderConfirmationError):
    """Raised when an order line references an inactive product."""


class InsufficientStock(OrderConfirmationError):
    """Raised when available inventory cannot satisfy the order."""