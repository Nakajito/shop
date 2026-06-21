from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    """
    Inline for managing multiple images of a product (carousel).
    """

    model = ProductImage
    extra = 1
    fields = ["image", "image_tag", "alt_text", "order"]
    readonly_fields = ["image_tag"]

    @admin.display(description=_("Preview"))
    def image_tag(self, obj):
        """Renders a small thumbnail for the inline image."""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 45px; height:45px; '
                'object-fit:cover; border-radius:5px;" />',
                obj.image.url,
            )
        return "-"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Administration interface for product categories.
    """

    list_display = ["name", "slug", "products_count"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]
    fields = ["name", "slug", "image", "image_tag"]
    readonly_fields = ["image_tag"]

    @admin.display(description=_("Preview"))
    def image_tag(self, obj):
        """Renders a small thumbnail for the category image."""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 45px; height:45px; '
                'object-fit:cover; border-radius:5px;" />',
                obj.image.url,
            )
        return "-"

    @admin.display(description=_("Total Products"))
    def products_count(self, obj):
        """Displays the number of products in this category."""
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Administration interface for products with enhanced filtering
    and visual previews.
    """

    list_display = [
        "image_tag",
        "name",
        "category",
        "price",
        "available",
        "created",
        "updated",
    ]

    inlines = [ProductImageInline]

    list_filter = ["available", "created", "updated", "category"]

    # Enable quick-edit directly in the list view
    list_editable = ["price", "available"]

    # Improve lookup speed for large catalogs
    search_fields = ["name", "description", "category__name"]

    # Automatic slug generation
    prepopulated_fields = {"slug": ("name",)}

    # Organize fields in the detail view
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("category", "name", "slug", "description")},
        ),
        (_("Pricing & Availability"), {"fields": ("price", "available")}),
        (
            _("Media"),
            {
                "fields": ("image", "image_tag"),
            },
        ),
    )

    readonly_fields = ["image_tag"]

    @admin.display(description=_("Preview"))
    def image_tag(self, obj):
        """Renders a small thumbnail for the product list view."""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 45px; height:45px; object-fit:cover; border-radius:5px;" />',
                obj.image.url,
            )
        return "-"
