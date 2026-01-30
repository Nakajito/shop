from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from shop.models import Product
from coupons.models import Coupon
from accounts.models import CustomUser


class Address(models.Model):
    """
    Model representing a user's shipping or billing address.

    This model handles multiple addresses per user, allowing one to be marked
    as the default. It includes logic to automatically unset other default
    addresses when a new one is selected.
    """

    COUNTRY_CHOICES = (("MX", "México"), ("US", "Estados Unidos"), ("ES", "España"))

    STATE_CHOICES = (
        ("CDMX", "Ciudad de México"),
        ("MEX", "Estado de México"),
        ("QRO", "Querétaro"),
    )

    ADDRESS_TYPE_CHOICES = (
        ("home", "Home"),
        ("office", "Office"),
        ("other", "Other"),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="addresses",
        help_text="User who owns the address",
    )

    address_line1 = models.CharField(
        max_length=255, help_text="Street, number, and apartment"
    )

    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Additional information (floor, reference, etc.)",
    )

    city = models.CharField(max_length=100, help_text="City")
    state = models.CharField(max_length=50, choices=STATE_CHOICES, help_text="State")
    postal_code = models.CharField(max_length=10, help_text="Zip Code")
    country = models.CharField(
        max_length=2, choices=COUNTRY_CHOICES, default="MX", help_text="Country"
    )

    phone = models.CharField(
        max_length=10, help_text="Contact telephone number for shipping"
    )

    recipient_name = models.CharField(
        max_length=200, help_text="Name of the person receiving the package"
    )

    is_default = models.BooleanField(
        default=False, help_text="Is this the default address?"
    )

    address_type = models.CharField(
        max_length=10,
        choices=ADDRESS_TYPE_CHOICES,
        default="home",
        help_text="Address type",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        # Ordered by default status first, then newest created
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-is_default"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.recipient_name} - {self.address_line1}, {self.city}, {self.country}"
        )

    def save(self, *args, **kwargs):
        """
        Save the address.
        If this address is marked as default, ensure no other address for this user
        is also marked as default.
        """
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)

        super().save(*args, **kwargs)

    def get_full_address(self):
        """
        Return the formatted full address string.
        """
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)

        # Combine City, State, Zip into one line
        location_line = f"{self.city}, {self.state}, {self.postal_code}"
        parts.append(location_line)

        parts.append(self.get_country_display())

        return ", ".join(parts)


class Order(models.Model):
    """
    Model representing a customer order.

    Stores shipping information, payment status, Stripe transaction IDs,
    and applied coupon data. It serves as the parent model for individual
    OrderItems.
    """

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="orders",
        help_text="User who made the purchase",
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_shipper",
        help_text="Shipping address",
    )

    billing_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordes_billed",
        help_text="Billing address (if different)",
    )
    address = models.CharField(max_length=200)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    # Stores the Stripe PaymentIntent ID (e.g., pi_12345...)
    stripe_id = models.CharField(max_length=250, blank=True)

    # Coupon system integration
    coupon = models.ForeignKey(
        Coupon, related_name="orders", null=True, blank=True, on_delete=models.SET_NULL
    )
    discount = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage (0-100) applied at the time of order.",
    )

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["-created"])]

    def __str__(self):
        return f"Order {self.id}"

    def get_total_cost(self):
        """
        Calculate the final total cost of the order.

        Returns:
            Decimal: Total cost of items minus the discount amount.
        """
        total_cost = self.get_total_cost_before_discount()
        return total_cost - self.get_discount()

    def get_stripe_url(self):
        """
        Generate a link to the Stripe Dashboard for this specific payment.

        Checks the STRIPE_SECRET_KEY setting to determine if the link should
        point to the Test mode or Live mode dashboard.

        Returns:
            str: URL to the Stripe transaction or an empty string if no ID exists.
        """
        if not self.stripe_id:
            return ""

        if "_test_" in settings.STRIPE_SECRET_KEY:
            # Stripe path for test payments
            path = "/test/"
        else:
            # Stripe path for real payments
            path = "/"

        return f"https://dashboard.stripe.com{path}payments/{self.stripe_id}"

    def get_total_cost_before_discount(self):
        """
        Calculate the sum of all line items before any discounts.

        Returns:
            Decimal: Sum of (price * quantity) for all items.
        """
        return sum(item.get_cost() for item in self.items.all())

    def get_discount(self):
        """
        Calculate the monetary value of the applied discount.

        Returns:
            Decimal: The calculated discount amount based on the percentage.
        """
        total_cost = self.get_total_cost_before_discount()
        if self.discount:
            return total_cost * (self.discount / Decimal(100))
        return Decimal(0)


class OrderItem(models.Model):
    """
    Model representing an individual line item within an order.

    Links a specific Product to an Order, capturing the price at the moment
    of purchase (to prevent historical data changes if product price updates).
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="order_items", on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        """
        Calculate the total cost for this line item.

        Returns:
            Decimal: price * quantity
        """
        return self.price * self.quantity
