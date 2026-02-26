from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    This model serves as the primary authentication entity, replacing the default
    Django User model. It includes application-specific fields for phone validation,
    user role classification (Regular vs. Wholesaler), and Stripe integration.
    """

    # Validators
    # Enforces exactly 10 digits.
    phone_regex = RegexValidator(
        regex=r"^\d{10}$",
        message=_("Phone number must be exactly 10 digits (e.g., 5522445104)."),
    )

    USER_TYPE_CHOICES = (
        ("regular_user", "Regular User"),
        ("wholesaler", "Wholesaler"),
    )

    class UserTypes(models.TextChoices):
        """Enumeration for User Types to avoid magic strings."""

        REGULAR = "regular_user", _("Regular User")
        WHOLESALER = "wholesaler", _("Wholesaler")

    # Additional fields
    phone = models.CharField(
        _("phone number"),
        max_length=10,
        validators=[phone_regex],
        blank=True,
        null=True,
        help_text=_("Format: 5522445104"),
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default="regular_user",
        help_text=_(
            "Designates whether the user is a regular customer or a wholesaler."
        ),
    )

    # Stripe Integration Fields
    stripe_customer_id = models.CharField(
        _("Stripe Customer ID"),
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text=_("Unique identifier for the customer in Stripe."),
    )

    payment_method = models.CharField(
        _("default payment method"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("ID of the default payment method in Stripe."),
    )

    favorites = models.ManyToManyField(
        "shop.Product",
        blank=True,
        related_name="favorited_by",
        verbose_name=_("Favorite Products"),
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    @property
    def is_wholesaler(self):
        """Check if the user has the Wholesaler role."""
        return self.user_type == self.UserTypes.WHOLESALER

    @property
    def is_regular_user(self):
        """Check if the user has the Regular User role."""
        return self.user_type == self.UserTypes.REGULAR


class UserProfile(models.Model):
    """
    Data model for extended user profile information.

    Establishes a one-to-one relationship with the CustomUser model to store
    non-authentication details such as biography, avatar images, and
    verification statuses.
    """

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("user"),
    )

    bio = models.TextField(
        _("biography"),
        max_length=500,
        blank=True,
        help_text=_("User biography or description."),
    )

    profile_picture = models.ImageField(
        _("profile picture"),
        upload_to="profile_pictures/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("User profile picture."),
    )

    # Verification Status Flags
    phone_verified = models.BooleanField(
        _("phone verified"),
        default=False,
        help_text=_("Indicates if the phone number has been verified via SMS."),
    )

    email_verified = models.BooleanField(
        _("email verified"),
        default=False,
        help_text=_("Indicates if the email address has been verified."),
    )

    newsletter_subscribed = models.BooleanField(
        _("newsletter subscribed"),
        default=False,
        help_text=_("Indicates if the user has opted in to the newsletter."),
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return f"{self.user.username}'s Profile"
