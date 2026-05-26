from django.urls import path

from . import views

"""
URL Configuration for the 'cart' application.

This module defines the URL patterns for managing the shopping cart, including
viewing the cart, adding products, and removing items.

Namespace:
    app_name = "cart"

Endpoints:
    - /: Displays the current contents of the shopping cart (cart_detail).
    - /add/<product_id>/: Adds a specific product to the cart (cart_add).
    - /remove/<product_id>/: Removes a specific product from the cart (cart_remove).
"""

app_name = "cart"

urlpatterns = [
    # Cart detail view (the main cart page)
    path("", views.cart_detail, name="cart_detail"),
    # Add a product to the cart
    # Requires the product ID as an integer argument
    path("add/<int:product_id>/", views.cart_add, name="cart_add"),
    # Remove a product from the cart
    path("remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
]
