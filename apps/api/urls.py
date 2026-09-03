from django.urls import path

from apps.api.customer_views import (
    CustomerDetailView,
    CustomerListCreateView,
)
from apps.api.product_views import (
    ProductDetailView,
    ProductListCreateView,
)
from apps.api.warehouse_views import (
    WarehouseDetailView,
    WarehouseListView,
)
from apps.api.inventory_views import (
    InventoryDetailView,
    InventoryListView,
)
from apps.api.order_views import (
    OrderCancelView,
    OrderCompleteView,
    OrderConfirmView,
    OrderDetailView,
    OrderListCreateView,
    OrderShipView,
)
from apps.api.views import ApiRootView
from apps.api.integration_views import PaymentWebhookView


urlpatterns = [
    path(
        "webhooks/payment/",
        PaymentWebhookView.as_view(),
        name="payment-webhook",
    ),
    path("", ApiRootView.as_view(), name="api-root"),
    path(
        "customers/",
        CustomerListCreateView.as_view(),
        name="customer-list",
    ),
    path(
        "customers/<uuid:customer_id>/",
        CustomerDetailView.as_view(),
        name="customer-detail",
    ),
    path(
        "products/",
        ProductListCreateView.as_view(),
        name="product-list",
    ),
    path(
        "products/<uuid:product_id>/",
        ProductDetailView.as_view(),
        name="product-detail",
    ),
    path(
        "warehouses/",
        WarehouseListView.as_view(),
        name="warehouse-list",
    ),
    path(
        "warehouses/<uuid:warehouse_id>/",
        WarehouseDetailView.as_view(),
        name="warehouse-detail",
    ),
    path(
        "inventory/",
        InventoryListView.as_view(),
        name="inventory-list",
    ),
    path(
        "inventory/<uuid:inventory_id>/",
        InventoryDetailView.as_view(),
        name="inventory-detail",
    ),
    path(
        "orders/",
        OrderListCreateView.as_view(),
        name="order-list",
    ),
    path(
        "orders/<uuid:order_id>/",
        OrderDetailView.as_view(),
        name="order-detail",
    ),
    path(
        "orders/<uuid:order_id>/confirm/",
        OrderConfirmView.as_view(),
        name="order-confirm",
    ),
    path(
        "orders/<uuid:order_id>/cancel/",
        OrderCancelView.as_view(),
        name="order-cancel",
    ),
    path(
        "orders/<uuid:order_id>/ship/",
        OrderShipView.as_view(),
        name="order-ship",
    ),
    path(
        "orders/<uuid:order_id>/complete/",
        OrderCompleteView.as_view(),
        name="order-complete",
    ),
]
