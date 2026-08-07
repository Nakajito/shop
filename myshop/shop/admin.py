import os
import tempfile
from pathlib import Path

from django.apps import apps
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .forms import ProductImportForm
from .models import Category, Product, ProductImage
from .services import import_products_from_file


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
        "sku",
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
    search_fields = ["name", "sku", "description", "category__name"]

    # Automatic slug generation
    prepopulated_fields = {"slug": ("name",)}

    # Organize fields in the detail view
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("category", "name", "slug", "sku", "description")},
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

    change_list_template = "admin/shop/product/change_list.html"

    @admin.display(description=_("Preview"))
    def image_tag(self, obj):
        """Renders a small thumbnail for the product list view."""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 45px; height:45px; object-fit:cover; border-radius:5px;" />',
                obj.image.url,
            )
        return "-"

    def get_urls(self):
        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(self.import_products_view),
                name="shop_product_import",
            ),
        ]
        return custom_urls + super().get_urls()

    def _admin_context(self, request, **extra):
        opts = self.model._meta
        try:
            app_config = apps.get_app_config(opts.app_label)
        except LookupError:
            app_config = None
        return {
            **self.admin_site.each_context(request),
            "opts": opts,
            "app_config": app_config,
            **extra,
        }

    def import_products_view(self, request):
        """Upload form for the CSV/XLS/XLSX bulk product importer (shop.services)."""
        if not self.has_add_permission(request):
            raise PermissionDenied

        if request.method == "POST":
            form = ProductImportForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded = form.cleaned_data["file"]
                suffix = Path(uploaded.name).suffix
                fd, tmp_path = tempfile.mkstemp(suffix=suffix)
                try:
                    with os.fdopen(fd, "wb") as tmp:
                        for chunk in uploaded.chunks():
                            tmp.write(chunk)
                    result = import_products_from_file(
                        tmp_path,
                        default_category=form.cleaned_data["category"] or None,
                        sheet_name=form.cleaned_data["sheet"] or None,
                        dry_run=form.cleaned_data["dry_run"],
                    )
                finally:
                    os.unlink(tmp_path)

                context = self._admin_context(
                    request,
                    title=_("Resultado de la importación"),
                    result=result,
                    dry_run=form.cleaned_data["dry_run"],
                )
                return render(request, "admin/shop/product/import_result.html", context)
        else:
            form = ProductImportForm()

        context = self._admin_context(
            request,
            title=_("Importar productos"),
            form=form,
        )
        return render(request, "admin/shop/product/import_form.html", context)
