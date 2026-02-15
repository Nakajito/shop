from django.urls import path
from . import views

"""
URL Configuration for the 'coupons' application.

This module defines the URL patterns for managing discount codes.

Namespace:
    app_name = "coupons"

Endpoints:
    - /apply/: Processes the coupon application form (typically via POST).
      Accepts a 'code' parameter and validates it against active coupons.
"""

app_name = "coupons"

urlpatterns = [
    # Applies a coupon to the current session's cart
    path("apply/", views.coupon_apply, name="apply"),
]
