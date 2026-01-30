from django.contrib import admin
from payment.models import PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin to manage payment methods"""

    list_display = (
        "card_holder_name",
        "user",
        "card_type",
        "get_masked_card",
        "get_expiration_display",
        "is_default",
        "is_active",
        "created_at",
    )
    list_filter = ("card_type", "is_default", "is_active", "created_at")
    search_fields = ("user__username", "card_holder_name", "last_four_digits")
    readonly_fields = (
        "stripe_payment_method_id",
        "created_at",
        "updated_at",
        "get_masked_card",
        "get_expiration_display",
        "is_expired",
    )

    fieldsets = (
        ("User", {"fields": ("user",)}),
        (
            "Card information",
            {
                "fields": (
                    "card_holder_name",
                    "card_type",
                    "get_masked_card",
                    "exp_month",
                    "exp_year",
                    "get_expiration_display",
                )
            },
        ),
        (
            "Stripe",
            {
                "fields": ("stripe_payment_method_id",),
                "classes": ("collapse",),
                "description": "Información de Stripe (solo lectura)",
            },
        ),
        ("State", {"fields": ("is_default", "is_active", "is_expired")}),
        (
            "Audit",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def is_expired(self, obj):
        """Shows whether the card has expired"""
        return obj.is_expired()

    is_expired.boolean = True
    is_expired.short_description = "Expired?"

    def has_add_permission(self, request):
        """Do not allow adding payment methods from the admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow careful removal"""
        return True
