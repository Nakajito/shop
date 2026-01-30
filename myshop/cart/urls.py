from django.urls import path
from . import views

"""
URL configuration for the 'cart' application.

This module defines the URL patterns mapping HTTP requests to the corresponding
views for managing the shopping cart.

Namespace:
    app_name = "cart"

Available patterns:
    - cart_detail: Displays the contents of the cart.
    - cart_add: Adds a specific product (by ID) to the cart.
    - cart_remove: Removes a specific product (by ID) from the cart.

Usage Example (in templates):
    <a href="{% url 'cart:cart_add' product.id %}">Add to Cart</a>
"""

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("add/<int:product_id>/", views.cart_add, name="cart_add"),
    path(
        "remove/<int:product_id>/",
        views.cart_remove,
        name="cart_remove",
    ),
]
