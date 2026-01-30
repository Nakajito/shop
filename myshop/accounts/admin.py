from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Defines the inline admin interface for the UserProfile model.

    This class configures how the UserProfile is displayed and edited within
    the CustomUser admin page. It uses a StackedInline layout for vertical
    field alignment and disables profile deletion to maintain one-to-one
    integrity with the User model.
    """

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = (
        "bio",
        "profile_picture",
        "phone_verified",
        "email_verified",
        "newsletter_subscribed",
    )


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Admin interface configuration for the CustomUser model.

    Extends the standard BaseUserAdmin to include application-specific fields
    (phone, user_type) and the UserProfile inline. It customizes the list view,
    filtering, search capabilities, and fieldsets for both editing and creating users.
    """

    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "user_type",
        "phone",
        "created_at",
    )
    list_filter = ("user_type", "created_at", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "phone")

    # Fields to display in edit form
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Información Adicional", {"fields": ("phone", "user_type")}),
    )

    # Fields in creation form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Additional Information", {"fields": ("phone", "user_type")}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the UserProfile model.

    This class provides a standalone view of user profiles, allowing administrators
    to filter by verification status and search for profiles via the associated
    User's username or email. Timestamp fields are set to read-only to preserve
    audit integrity.
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
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
