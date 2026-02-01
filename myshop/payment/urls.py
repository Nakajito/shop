from django.urls import path
from . import views, webhooks

"""
URL configuration for the 'payment' application.

This module defines the URL patterns for handling the payment lifecycle.

Namespace:
    app_name = "payment"

Available patterns:
    - process: Initiates the payment workflow (creates Stripe session).
    - completed: Displayed to the user after a successful payment.
    - canceled: Displayed to the user if they cancel the payment.
    - stripe-webhook: Endpoint for Stripe to send asynchronous event notifications
    (e.g., checkout.session.completed).
"""

app_name = "payment"

urlpatterns = [
    path("process/", views.payment_process, name="process"),
    path("completed/", views.payment_completed, name="completed"),
    path("canceled/", views.payment_canceled, name="canceled"),
    path("webhook/", webhooks.stripe_webhook, name="stripe-webhook"),
    # Payment methods
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
    # APIs AJAX
    path("api/create-intent/", views.create_payment_intent, name="create_intent"),
    path("api/confirm-payment/", views.confirm_payment, name="confirm_payment"),
]
