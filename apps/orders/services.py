from collections import defaultdict
import logging

from django.db import transaction

from apps.inventory.models import StockItem
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

logger = logging.getLogger(__name__)


def confirm_order(order_id):
    """
    Confirm a DRAFT sales order and reserve the required inventory atomically.

    The operation locks the order first and then all relevant stock rows.
    Inventory availability is re-evaluated after the locks are acquired.
    """

    with transaction.atomic():
        try:
            order = (
                SalesOrder.objects
                .select_for_update()
                .get(id=order_id)
            )
        except SalesOrder.DoesNotExist as exc:
            raise OrderNotFound from exc

        if order.status != SalesOrder.Status.DRAFT:
            raise InvalidOrderState

        if not order.customer.active:
            raise InactiveCustomer

        lines = list(
            order.lines
            .select_related("product")
            .order_by("product_id", "id")
        )

        if not lines:
            raise OrderHasNoLines

        required_quantities = defaultdict(int)

        for line in lines:
            if line.quantity <= 0:
                raise InvalidOrderQuantity

            if not line.product.active:
                raise InactiveProduct

            required_quantities[line.product_id] += line.quantity

        product_ids = sorted(required_quantities)

        stock_items = list(
            StockItem.objects
            .select_for_update()
            .filter(product_id__in=product_ids)
            .order_by("product_id", "id")
        )

        stock_by_product = defaultdict(list)

        for stock_item in stock_items:
            stock_by_product[stock_item.product_id].append(stock_item)

        # Log inventory check before reservation
        for product_id in product_ids:
            required = required_quantities[product_id]
            available = sum(
                item.available_quantity
                for item in stock_by_product[product_id]
            )
            logger.info(
                "inventory_check",
                extra={
                    "event": "inventory_check",
                    "order_id": str(order.id),
                    "product_id": str(product_id),
                    "required": required,
                    "available": available,
                }
            )

            if available < required:
                raise InsufficientStock

        # Perform reservation
        for product_id in product_ids:
            remaining = required_quantities[product_id]

            for stock_item in stock_by_product[product_id]:
                if remaining == 0:
                    break

                available = stock_item.available_quantity
                reservation = min(available, remaining)

                if reservation:
                    stock_item.reserved_quantity += reservation
                    stock_item.save(
                        update_fields=["reserved_quantity", "modified_at"]
                    )
                    logger.info(
                        "inventory_reserved",
                        extra={
                            "event": "inventory_reserved",
                            "order_id": str(order.id),
                            "product_id": str(stock_item.product_id),
                            "warehouse_id": str(stock_item.warehouse_id),
                            "quantity": reservation,
                        }
                    )
                    remaining -= reservation

        old_status = order.status
        order.status = SalesOrder.Status.CONFIRMED
        order.save(update_fields=["status", "modified_at"])

        logger.info(
            "order_state_transition",
            extra={
                "event": "order_state_transition",
                "order_id": str(order.id),
                "from_status": old_status,
                "to_status": order.status,
            }
        )

        return order


def cancel_order(order_id):
    """
    Cancel a DRAFT sales order atomically.
    """

    with transaction.atomic():
        try:
            order = (
                SalesOrder.objects
                .select_for_update()
                .get(id=order_id)
            )
        except SalesOrder.DoesNotExist as exc:
            raise OrderNotFound from exc

        if order.status != SalesOrder.Status.DRAFT:
            raise InvalidOrderState

        old_status = order.status
        order.status = SalesOrder.Status.CANCELLED
        order.save(update_fields=["status", "modified_at"])

        logger.info(
            "order_state_transition",
            extra={
                "event": "order_state_transition",
                "order_id": str(order.id),
                "from_status": old_status,
                "to_status": order.status,
            }
        )

        return order


def ship_order(order_id):
    """
    Ship a CONFIRMED sales order and consume its reserved inventory atomically.
    """

    with transaction.atomic():
        try:
            order = (
                SalesOrder.objects
                .select_for_update()
                .get(id=order_id)
            )
        except SalesOrder.DoesNotExist as exc:
            raise OrderNotFound from exc

        if order.status != SalesOrder.Status.CONFIRMED:
            raise InvalidOrderState

        lines = list(
            order.lines
            .select_related("product")
            .order_by("product_id", "id")
        )

        required_quantities = defaultdict(int)

        for line in lines:
            required_quantities[line.product_id] += line.quantity

        product_ids = sorted(required_quantities)

        stock_items = list(
            StockItem.objects
            .select_for_update()
            .filter(product_id__in=product_ids)
            .order_by("product_id", "id")
        )

        stock_by_product = defaultdict(list)

        for stock_item in stock_items:
            stock_by_product[stock_item.product_id].append(stock_item)

        for product_id in product_ids:
            required = required_quantities[product_id]
            reserved = sum(
                item.reserved_quantity
                for item in stock_by_product[product_id]
            )

            if reserved < required:
                raise InsufficientStock

        # Consume reserved stock
        for product_id in product_ids:
            remaining = required_quantities[product_id]

            for stock_item in stock_by_product[product_id]:
                if remaining == 0:
                    break

                reserved = stock_item.reserved_quantity
                consumed = min(reserved, remaining)

                if consumed:
                    stock_item.quantity -= consumed
                    stock_item.reserved_quantity -= consumed
                    stock_item.save(
                        update_fields=[
                            "quantity",
                            "reserved_quantity",
                            "modified_at",
                        ]
                    )
                    logger.info(
                        "inventory_consumed",
                        extra={
                            "event": "inventory_consumed",
                            "order_id": str(order.id),
                            "product_id": str(stock_item.product_id),
                            "warehouse_id": str(stock_item.warehouse_id),
                            "quantity": consumed,
                        }
                    )
                    remaining -= consumed

        old_status = order.status
        order.status = SalesOrder.Status.SHIPPED
        order.save(update_fields=["status", "modified_at"])

        logger.info(
            "order_state_transition",
            extra={
                "event": "order_state_transition",
                "order_id": str(order.id),
                "from_status": old_status,
                "to_status": order.status,
            }
        )

        return order


def complete_order(order_id):
    """
    Complete a SHIPPED sales order atomically.
    """

    with transaction.atomic():
        try:
            order = (
                SalesOrder.objects
                .select_for_update()
                .get(id=order_id)
            )
        except SalesOrder.DoesNotExist as exc:
            raise OrderNotFound from exc

        if order.status != SalesOrder.Status.SHIPPED:
            raise InvalidOrderState

        old_status = order.status
        order.status = SalesOrder.Status.COMPLETED
        order.save(update_fields=["status", "modified_at"])

        logger.info(
            "order_state_transition",
            extra={
                "event": "order_state_transition",
                "order_id": str(order.id),
                "from_status": old_status,
                "to_status": order.status,
            }
        )

        return order
