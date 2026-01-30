from django.urls import path
from . import views

"""
URL configuration for the 'shop' application.

This module defines the public-facing URL patterns for browsing the product catalog.

Namespace:
    app_name = "shop"

Available patterns:
    - product_list: The home page of the shop, listing all available products.
    - product_list_by_category: Filters the product list by a specific category slug.
    - product_detail: Displays the full details of a specific product.
      Pattern: /<id>/<slug>/ (e.g., /5/green-t-shirt/)
"""

app_name = "shop"

urlpatterns = [
    # Catalog Home / List of all products
    path("", views.product_list, name="product_list"),
    # List products filtered by category
    path("<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    # Product detail view
    # Note: Using both ID and Slug for better SEO and unique lookup
    path("<int:id>/<slug:slug>/", views.product_detail, name="product_detail"),
]
