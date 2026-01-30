from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Coupon(models.Model):
    """
    Model representing a discount coupon.

    This model stores the code users must enter, the validity period during which
    the coupon can be redeemed, and the discount percentage (constrained between
    0 and 100). The 'active' boolean allows for manual deactivation regardless
    of dates.
    """

    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage value (0 to 100)",
    )

    active = models.BooleanField()

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ["-valid_to"]

    def __str__(self):
        return self.code
