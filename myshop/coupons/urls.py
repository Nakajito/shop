from django.urls import path
from . import views

"""
URL configuration for the 'coupons' application.

This module defines the URL mapping for applying discount codes.

Namespace:
    app_name = "coupons"

Available patterns:
    - apply: Processes the coupon application form via POST request.

Usage Example (in templates):
    <form action="{% url 'coupons:apply' %}" method="post">
"""

app_name = "coupons"

urlpatterns = [
    path("apply/", views.coupon_apply, name="apply"),
]
