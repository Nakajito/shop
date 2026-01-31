from django.db import models
from accounts.models import CustomUser
from datetime import datetime


class PaymentMethod(models.Model):
    """Model for storing payment methods (credit/debit cards).
    We never store sensitive card details (only reference numbers).

        Args:
            models (_type_): _description_
    """

    CARD_TYPE_CHOICES = (
        ("visa", "Visa"),
        ("mastercard", "Mastercard"),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="payment_methods",
        help_text="User who owns the payment method",
    )

    stripe_payment_method_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Stripe ID of the payment method (never disclose to the user)",
    )

    card_type = models.CharField(
        max_length=20, choices=CARD_TYPE_CHOICES, default="visa", help_text="Card type"
    )

    last_four_digits = models.CharField(
        max_length=4, help_text="Last 4 digits of the card (e.g., 4242)"
    )

    card_holder_name = models.CharField(max_length=255, help_text="Cardholder name")

    exp_month = models.IntegerField(help_text="Expiration month (1-12)")

    exp_year = models.IntegerField(help_text="Expiration year (e.g. 2027)")

    is_default = models.BooleanField(
        default=False, help_text="Is this the default payment method?"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Is the method active? (false if the card has expired or been canceled)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-is_default"]),
            models.Index(
                fields=["user", "-is_active"],
            ),
        ]

    def __str__(self):
        return f"{self.card_holder_name} - {self.get_card_type_display()} ****{self.last_four_digits}"

    def save(self, *args, **kwargs):
        """If marked as default, uncheck other user methods."""
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)

    def get_masked_card(self):
        """Returns the masked card (e.g., ****4242)"""
        return f"****{self.last_four_digits}"

    def is_expired(self):
        """Returns True if the card has expired"""
        today = datetime.now()
        return self.exp_year < today.year or (
            self.exp_year == today.year and self.exp_month < today.month
        )

    def get_expiration_display(self):
        """Returns the formatted expiration date (e.g., 12/25)."""

        return f"{self.exp_month:02d}/{self.exp_year % 100:02d}"
