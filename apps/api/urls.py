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
from apps.api.views import ApiRootView


urlpatterns = [
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
]