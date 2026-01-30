from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    """Display UserProfile inline in the CustomUser admin

    Args:
        admin (_type_): _description_
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
    """Custom Admin for CustomUser

    Args:
        BaseUserAdmin (_type_): _description_
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
        ("Aditional Information", {"fields": ("phone", "user_type")}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile

    Args:
        admin (_type_): _description_
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
