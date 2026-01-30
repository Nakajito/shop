from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    """Extended user model that replaces the default User.
    Inherits from AbstractUser to maintain standard functionality.

    Args:
        AbstractUser (_type_): _description_
    """

    PHONE_REGEX = RegexValidator(regex=r"^\+?1\d{10}$", message="Phone number")
    USER_TYPE_CHOICES = (("regular_user", "regular_user"), ("wholesaler", "wholesaler"))

    # aditional fields
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
        default="normal",
        help_text="User type: Regular or Wholesaler",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def if_wholesaler(self):
        return self.user_type == "wholesaler"

    def is_regular_user(self):
        return self.user_type == "regular_user"


class UserProfile(models.Model):
    """Additional user profile with complementary information. One-to-one relationship with CustomUser.

    Args:
        models (_type_): _description_
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
        verbose_name_plural = "Users Profile"

    def __str__(self):
        return f"{self.user.username}'s profile"
