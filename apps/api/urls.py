from django.urls import path

from apps.api.customer_views import (
    CustomerDetailView,
    CustomerListCreateView,
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
]
