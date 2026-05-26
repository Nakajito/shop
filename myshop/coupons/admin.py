from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """
    Administration interface for the Coupon model.

    Optimizations:
    - list_editable: Allows toggling 'active' status without opening the edit form.
    - search_help_text: Provides guidance on search functionality.
    - fieldsets: Organizes fields logically.
    """

    list_display = [
        "code",
        "valid_from",
        "valid_to",
        "discount",
        "active",
    ]

    # Allows editing these fields directly from the list view
    list_editable = ["active", "valid_from", "valid_to"]

    list_filter = ["active", "valid_from", "valid_to"]
    search_fields = ["code"]
    search_help_text = _("Search by coupon code (e.g., SUMMER20)")

    ordering = ["-valid_to"]

    fieldsets = (
        (None, {"fields": ("code", "discount", "active")}),
        (
            _("Validity Period"),
            {
                "fields": ("valid_from", "valid_to"),
                "description": _(
                    "Set the start and end dates for the coupon's validity."
                ),
            },
        ),
    )
