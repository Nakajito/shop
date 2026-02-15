from django.urls import path
from . import views

"""
URL Configuration for the 'shop' application.

This module manages the storefront routing including:
- Main catalog browsing.
- Category-based filtering.
- SEO-optimized product detail pages.

Namespace:
    app_name = "shop"
"""

app_name = "shop"

urlpatterns = [
    # Catalog Index: Displays all available products.
    path("", views.product_list, name="product_list"),
    # Category Filter: Displays products belonging to a specific category.
    # Note: Placed before detail view to avoid slug collisions.
    path(
        "category/<slug:category_slug>/",
        views.product_list,
        name="product_list_by_category",
    ),
    # Product Detail: Unique lookup using both ID (for speed) and Slug (for SEO).
    # Example: /shop/42/gaming-laptop/
    path("<int:id>/<slug:slug>/", views.product_detail, name="product_detail"),
]
