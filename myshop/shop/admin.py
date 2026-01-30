from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Administration interface for product categories.

    Features:
    - Automatically generates the 'slug' field based on the 'name' input,
      ensuring consistent and SEO-friendly URLs.
    """

    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Administration interface for products.

    Features:
    - Quick-edit capabilities: Shop managers can update the 'price' and
      'available' status directly from the list view without opening
      individual records.
    - Filtering by availability and timestamps.
    - Automatic slug generation.
    """

    list_display = ["name", "slug", "price", "available", "created", "updated"]
    list_filter = ["available", "created", "updated"]

    # allow editing these fields directly in the list view
    list_editable = ["price", "available"]

    prepopulated_fields = {"slug": ("name",)}
