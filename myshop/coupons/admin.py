from django.contrib import admin
from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """
    Administration interface for the Coupon model.

    This configuration provides a dashboard for managing discount codes.
    It allows administrators to:
    - Quickly view active status and validity windows.
    - Filter coupons by date ranges and active status.
    - Search for specific coupon codes.
    """

    list_display = [
        "code",
        "valid_from",
        "valid_to",
        "discount",
        "active",
    ]
    list_filter = ["active", "valid_from", "valid_to"]
    search_fields = ["code"]
