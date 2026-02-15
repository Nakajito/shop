from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Coupon(models.Model):
    """
    Model representing a discount coupon.

    This model stores the code users must enter, the validity period,
    and the discount percentage. It includes validation logic to ensure
    date ranges are consistent.
    """

    code = models.CharField(
        _("code"),
        max_length=50,
        unique=True,
        help_text=_("The code users enter to apply the discount (e.g. SUMMER20)."),
    )

    valid_from = models.DateTimeField(_("valid from"))
    valid_to = models.DateTimeField(_("valid to"))

    discount = models.IntegerField(
        _("discount"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Percentage value (0 to 100)"),
    )

    active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")
        ordering = ["-valid_to"]

    def __str__(self):
        return f"{self.code} ({self.discount}%)"

    def clean(self):
        """
        Custom validation to ensure the date range is logical.
        Django admin calls this automatically before saving.
        """
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValidationError(
                {"valid_to": _("The end date cannot be before the start date.")}
            )
