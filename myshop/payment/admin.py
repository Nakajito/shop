from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from payment.models import PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """
    Admin configuration to manage user payment methods.

    Registration/Addition is disabled via admin to ensure Stripe
    tokenization integrity, which must happen on the frontend.
    """

    list_display = (
        "card_holder_name",
        "user",
        "card_type",
        "get_masked_card",
        "get_expiration_display",
        "is_default",
        "is_active",
        "is_expired_display",
        "created_at",
    )

    list_filter = ("card_type", "is_default", "is_active", "created_at")

    search_fields = (
        "user__username",
        "user__email",
        "card_holder_name",
        "last_four_digits",
    )

    readonly_fields = (
        "stripe_payment_method_id",
        "created_at",
        "updated_at",
        "get_masked_card",
        "get_expiration_display",
        "is_expired_display",
    )

    fieldsets = (
        (_("Ownership"), {"fields": ("user",)}),
        (
            _("Card Details"),
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
            _("Stripe Integration"),
            {
                "fields": ("stripe_payment_method_id",),
                "classes": ("collapse",),
                "description": _("Stripe reference data (Read-only for integrity)."),
            },
        ),
        (_("Status"), {"fields": ("is_default", "is_active", "is_expired_display")}),
        (
            _("Audit Trail"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(boolean=True, description=_("Expired?"))
    def is_expired_display(self, obj):
        """Displays a boolean icon if the card is past its expiry date."""
        return obj.is_expired()

    def has_add_permission(self, request):
        """
        Prevents manual card addition.
        Cards must be added via the frontend to be tokenized by Stripe.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """Allows removal, but use with caution as it affects recurring logic."""
        return True
