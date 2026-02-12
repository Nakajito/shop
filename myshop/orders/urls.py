from django.urls import path
from . import views

"""
URL configuration for the 'orders' application.

This module defines the URL patterns for order management, including:
- Public-facing order creation (checkout).
- Admin-specific views for detailed order inspection and PDF generation.

Namespace:
    app_name = "orders"

Available patterns:
    - order_create: Public checkout page processing.
    - admin_order_detail: Custom admin view to see order details.
    - admin_order_pdf: Custom admin view to download the invoice PDF.
"""

app_name = "orders"

urlpatterns = [
    # orders
    path("create/", views.order_create, name="order_create"),
    path(
        "admin/order/<int:order_id>/",
        views.admin_order_detail,
        name="admin_order_detail",
    ),
    path(
        "admin/order/<int:order_id>/pdf/", views.admin_order_pdf, name="admin_order_pdf"
    ),
    path("detail/<int:order_id>/", views.order_detail, name="order_detail"),
    path("detail/<int:order_id>/pdf/", views.order_pdf, name="order_pdf"),
    # Purchase history
    path("history/", views.order_history, name="order_history"),
    # Shipping addresses
    path("addresses/", views.address_list, name="address_list"),
    path("addresses/create/", views.address_create, name="address_create"),
    path("addresses/<int:address_id>/edit/", views.address_edit, name="address_edit"),
    path(
        "addresses/<int:address_id>/delete/",
        views.address_delete,
        name="address_delete",
    ),
    path(
        "addresses/<int:address_id>/set-default/",
        views.address_set_default,
        name="address_set_default",
    ),
    # Tracking
    path(
        "detail/<int:order_id>/tracking/", views.order_tracking, name="order_tracking"
    ),
    path(
        "detail/<int:order_id>/status-history/",
        views.order_status_history,
        name="order_status_history",
    ),
    path(
        "detail/<int:order_id>/tracking-info/",
        views.order_tracking_info,
        name="order_tracking_info",
    ),
]
