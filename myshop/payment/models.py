from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser


class PaymentMethod(models.Model):
    """
    Model for storing user-saved payment methods (credit/debit cards).

    We store only reference metadata and Stripe identifiers.
    Sensitive data like full card numbers or CVC are never stored on this server.
    """

    class CardType(models.TextChoices):
        VISA = "visa", "Visa"
        MASTERCARD = "mastercard", "Mastercard"
        AMEX = "amex", "American Express"
        DISCOVER = "discover", "Discover"
        DINERS = "diners", "Diners Club"
        JCB = "jcb", "JCB"
        OTHER = "other", _("Other")

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="payment_methods",
        verbose_name=_("user"),
    )

    stripe_payment_method_id = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Stripe ID for the payment method (pi_... or pm_...)."),
    )

    card_type = models.CharField(
        max_length=20,
        choices=CardType.choices,
        default=CardType.VISA,
        verbose_name=_("card type"),
    )

    last_four_digits = models.CharField(max_length=4, verbose_name=_("last 4 digits"))

    card_holder_name = models.CharField(
        max_length=255, verbose_name=_("cardholder name")
    )

    exp_month = models.PositiveSmallIntegerField(verbose_name=_("expiration month"))

    exp_year = models.PositiveIntegerField(verbose_name=_("expiration year"))

    is_default = models.BooleanField(default=False, verbose_name=_("default method"))

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("active"),
        help_text=_("Uncheck to manually disable this payment method."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment Methods")
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-is_default"]),
            models.Index(fields=["user", "-is_active"]),
        ]

    def __str__(self):
        return f"{self.get_card_type_display()} •••• {self.last_four_digits}"

    def save(self, *args, **kwargs):
        """
        Ensures only one payment method is marked as default per user.
        """
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)

    def get_masked_card(self):
        """Returns the visually standard masked card (e.g., •••• 4242)."""
        return f"•••• {self.last_four_digits}"

    def is_expired(self):
        """Returns True if the card expiration date has passed."""
        today = timezone.now().date()
        # Cards expire at the end of the specified month
        if self.exp_year < today.year:
            return True
        if self.exp_year == today.year and self.exp_month < today.month:
            return True
        return False

    def get_expiration_display(self):
        """Returns the formatted expiration date (e.g., 08/27)."""
        return f"{self.exp_month:02d}/{str(self.exp_year)[-2:]}"
