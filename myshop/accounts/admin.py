from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from accounts.models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Defines the inline admin interface for the UserProfile model.

    Best Practices:
    - uses 'can_delete = False' to enforce 1-to-1 integrity.
    - fk_name is explicit to avoid ambiguity.
    """

    model = UserProfile
    can_delete = False
    verbose_name_plural = _("Profile")
    fk_name = "user"

    fields = (
        "bio",
        "profile_picture",
        "phone_verified",
        "email_verified",
        "newsletter_subscribed",
    )
    # Es buena práctica que la fecha de creación sea solo lectura en inlines
    readonly_fields = ("created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        # Si quisieras lógica condicional, iría aquí.
        # Por ahora retornamos los definidos arriba.
        return self.readonly_fields


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Admin interface configuration for the CustomUser model.

    Optimizations:
    - Organizes custom fields into logical fieldsets.
    - Protects external IDs (like stripe_customer_id) from accidental edits.
    """

    inlines = (UserProfileInline,)

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "user_type",
        "is_staff",
        "created_at",
    )

    list_filter = ("user_type", "is_staff", "is_active", "created_at")
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "stripe_customer_id",
    )
    ordering = ("-date_joined",)

    # Campos que no deberían editarse manualmente para no romper la integración con Stripe
    readonly_fields = ("stripe_customer_id", "date_joined", "last_login")

    # Configuración del formulario de edición
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            _("Extra Information"),
            {"fields": ("phone", "user_type", "stripe_customer_id", "payment_method")},
        ),
    )

    # Configuración del formulario de creación
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            _("Extra Information"),
            {"fields": ("email", "first_name", "last_name", "phone", "user_type")},
        ),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the UserProfile model.

    Performance:
    - Uses 'list_select_related' to fetch the related User in a single query (prevents N+1 problem).
    - Uses 'autocomplete_fields' for the User selection to handle large datasets efficiently.
    """

    list_display = (
        "user",
        "phone_verified",
        "email_verified",
        "newsletter_subscribed",
        "created_at",
    )

    list_filter = (
        "phone_verified",
        "email_verified",
        "newsletter_subscribed",
        "created_at",
    )

    # Search by fields in the related model (CustomUser)
    search_fields = ("user__username", "user__email", "user__first_name")

    # CRITICAL OPTIMIZATION: Retrieve user information in the same SQL query
    list_select_related = ("user",)

    # USABILITY: Instead of a giant dropdown, use an AJAX search box
    # (Requires CustomUserAdmin to have search_fields defined)
    autocomplete_fields = ["user"]

    # Data integrity
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("user",)}),
        (_("Profile Info"), {"fields": ("bio", "profile_picture")}),
        (
            _("Status & Verification"),
            {"fields": ("phone_verified", "email_verified", "newsletter_subscribed")},
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": (
                    "collapse",
                ),  # Hide this section by default to clean up the UI
            },
        ),
    )
