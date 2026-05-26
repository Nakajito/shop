from django.urls import path

from . import views, webhooks

"""
URL Configuration for the 'payment' application.

This module manages the payment lifecycle including:
- Stripe Checkout & Intent creation.
- Success/Failure customer landing pages.
- User payment method management (Vaulting).
- Stripe Webhook listener for asynchronous events.

Namespace:
    app_name = "payment"
"""

app_name = "payment"

urlpatterns = [
    # --- Checkout Flow ---
    path("process/", views.payment_process, name="process"),
    path("completed/", views.payment_completed, name="completed"),
    path("canceled/", views.payment_canceled, name="canceled"),
    # --- Payment Method Management (User Profile) ---
    path("methods/", views.payment_method_list, name="payment_method_list"),
    path("methods/add/", views.payment_method_add, name="payment_method_add"),
    path(
        "methods/<int:payment_method_id>/delete/",
        views.payment_method_delete,
        name="payment_method_delete",
    ),
    path(
        "methods/<int:payment_method_id>/set-default/",
        views.payment_method_set_default,
        name="payment_method_set_default",
    ),
    # --- Stripe AJAX API Endpoints ---
    path("api/create-intent/", views.create_payment_intent, name="create_intent"),
    path("api/confirm-payment/", views.confirm_payment, name="confirm_payment"),
    # --- System / Webhooks ---
    path("webhook/", webhooks.stripe_webhook, name="stripe-webhook"),
]
