from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    This model replaces the default User model to include application-specific
    fields such as phone number validation and user role classification
    (Regular vs. Wholesaler). It serves as the primary authentication entity.
    """

    # Validators
    # Note: Regex adjusted to allow 10 digits as per your help text example.
    PHONE_REGEX = RegexValidator(
        regex=r"^\d{10}$",
        message="Phone number must be exactly 10 digits (e.g., 5522445104).",
    )

    USER_TYPE_CHOICES = (
        ("regular_user", "Regular User"),
        ("wholesaler", "Wholesaler"),
    )

    # Additional fields
    phone = models.CharField(
        max_length=10,
        validators=[PHONE_REGEX],
        blank=True,
        null=True,
        help_text="Format: 5522445104",
    )

    user_type = models.CharField(
        max_length=12,
        choices=USER_TYPE_CHOICES,
        default="regular_user",  # Fixed: 'normal' was not in choices
        help_text="User type: Regular or Wholesaler",
    )

    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Customer ID in Stripe",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    @property
    def is_wholesaler(self):
        """Boolean property to check if user is a wholesaler."""
        return self.user_type == "wholesaler"

    @property
    def is_regular_user(self):
        """Boolean property to check if user is a regular user."""
        return self.user_type == "regular_user"


class UserProfile(models.Model):
    """
    Data model for extended user profile information.

    Establishes a one-to-one relationship with the CustomUser model to store
    non-authentication details such as biography, avatar images, and
    verification statuses (email/phone).
    """

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )

    bio = models.TextField(
        max_length=500, blank=True, help_text="User biography or description"
    )
    profile_picture = models.ImageField(
        upload_to="profile_pictures/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text="User profile picture",
    )

    phone_verified = models.BooleanField(
        default=False, help_text="Has the phone been verified?"
    )
    email_verified = models.BooleanField(
        default=False, help_text="Has the email been verified?"
    )
    newsletter_subscribed = models.BooleanField(
        default=False, help_text="Subscribed to the newsletter?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"  # Fixed grammar from "Users Profile"

    def __str__(self):
        return f"{self.user.username}'s profile"
