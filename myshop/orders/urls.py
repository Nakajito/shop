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
    path("create/", views.order_create, name="order_create"),
    path(
        "admin/order/<int:order_id>/",
        views.admin_order_detail,
        name="admin_order_detail",
    ),
    path(
        "admin/order/<int:order_id>/pdf/", views.admin_order_pdf, name="admin_order_pdf"
    ),
]
