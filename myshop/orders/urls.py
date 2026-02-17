from django.urls import path
from . import views

"""
URL Configuration for the 'orders' application.

This module handles the routing for:
- Checkout & Reordering logic.
- User Order History & Detailed Tracking.
- Shipping Address Management (CRUD).
- Admin-specific extensions (PDF generation and extended details).

Namespace:
    app_name = "orders"
"""

app_name = "orders"

urlpatterns = [
    # --- Checkout & Core Actions ---
    path("create/", views.order_create, name="order_create"),
    path("reorder/<int:order_id>/", views.reorder, name="reorder"),
    path("buy/<int:order_id>/", views.buy_order, name="buy_order"),
    path("cancel/<int:order_id>/", views.cancel_order, name="cancel_order"),
    # --- User Order History & Details ---
    path("history/", views.order_history, name="order_history"),
    path("detail/<int:order_id>/", views.order_detail, name="order_detail"),
    path("detail/<int:order_id>/pdf/", views.order_pdf, name="order_pdf"),
    # --- Tracking & Logistics ---
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
    # --- Shipping Address Management (CRUD) ---
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
    # --- Admin Custom Extensions ---
    # These views are typically called from the Django Admin interface
    path(
        "admin/order/<int:order_id>/",
        views.admin_order_detail,
        name="admin_order_detail",
    ),
    path(
        "admin/order/<int:order_id>/pdf/", views.admin_order_pdf, name="admin_order_pdf"
    ),
]
