from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from shop.models import Product
from coupons.models import Coupon
from accounts.models import CustomUser
from payment.models import PaymentMethod

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

ORDER_STATUS_CHOICES = (
    ("pending", "Pedido Pendiente"),
    ("confirmed", "Pedido Confirmado"),
    ("preparing", "Preparando Pedido"),
    ("shipped", "Enviado"),
    ("delivered", "Entregado"),
    ("cancelled", "Cancelado"),
)

CARRIER_CHOICES = (
    ("fedex", "FedEx"),
    ("ups", "UPS"),
    ("dhl", "DHL"),
    ("other", "Otro"),
)


class Address(models.Model):
    """
    Model representing a user's shipping or billing address.

    This model handles multiple addresses per user, allowing one to be marked
    as the default. It includes logic to automatically unset other default
    addresses when a new one is selected.
    """

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

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="pending",
        help_text="Current order status",
    )

    estimated_delivery_date = models.DateField(
        null=True, blank=True, help_text="Estimated delivery date"
    )

    notes = models.TextField(
        blank=True, null=True, help_text="Internal notes on the order"
    )

    customer_notes = models.TextField(
        blank=True, null=True, help_text="Customer notes when making the purchase"
    )

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

    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Método de pago utilizado",
    )

    def get_timeline_steps(self):
        """
        Returns steps from the order timeline to display in templates.
        Useful for displaying visual progress.
        """
        steps = [
            {
                "step": "Order Confirmed",
                "status": "confirmed",
                "completed": self.status
                in ["confirmed", "preparing", "shipped", "delivered"],
                "icon": "check-circle",
            },
            {
                "step": "Preparing",
                "status": "preparing",
                "completed": self.status in ["preparing", "shipped", "delivered"],
                "icon": "box",
            },
            {
                "step": "Shipped",
                "status": "shipped",
                "completed": self.status in ["shipped", "delivered"],
                "icon": "truck",
            },
            {
                "step": "Delivered",
                "status": "delivered",
                "completed": self.status == "delivered",
                "icon": "check-circle",
            },
        ]
        return steps

    def can_be_cancelled(self):
        """Returns True if the order can be cancelled"""
        return self.status in ["pending", "confirmed"]

    def can_be_reordered(self):
        """Returns True if the order can be reordered"""
        return self.status in ["delivered", "cancelled"]

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

    def change_status(self, new_status, changed_by=None, reason=None):
        """
        Changes the order status and creates an audit log.
        """
        if new_status not in dict(ORDER_STATUS_CHOICES):
            raise ValidationError(f"Invalid status: {new_status}")

        if self.status == new_status:
            return None

        old_status = self.status
        self.status = new_status
        self.save()

        # Create audit log
        status_update = OrderStatusUpdate.objects.create(
            order=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
        )

        return status_update

    def get_status_display_with_badge(self):
        """Returns the status with color for templates"""
        colors = {
            "pending": "warning",
            "confirmed": "info",
            "preparing": "info",
            "shipped": "primary",
            "delivered": "success",
            "cancelled": "danger",
        }
        color = colors.get(self.status, "secondary")
        return f'<span class="badge bg-{color}">{self.get_status_display()}</span>'


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


class OrderStatusUpdate(models.Model):
    """Audit log of order status changes.
    Each status change creates a record here.
    Allows you to view the complete history of changes.

    Args:
        models (_type_): _description_
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_updated",
        help_text="Order status changed",
    )

    old_status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, help_text="Previous status"
    )

    new_status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, help_text="New status"
    )

    changed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_changed",
        help_text="User who made the change",
    )

    reason = models.TextField(
        blank=True, null=True, help_text="Reason for change of status"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Status Change"
        verbose_name_plural = "Order Status Changes"
        indexes = [models.Index(fields=["-order", "-created_at"])]

    def __str__(self):
        return f"Order {self.order.id}: {self.old_status} -> {self.new_status}"


class OrderTracking(models.Model):
    """Tracking and shipping information for an order.
    Links mail/carrier data to the order.

    Args:
        models (_type_): _description_
    """

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="tracking",
        help_text="Associated order",
    )

    tracking_number = models.CharField(
        max_length=255, help_text="Tracking number (e.g., 1Z999AA10123456784)"
    )

    carrier = models.CharField(
        max_length=20, choices=CARRIER_CHOICES, help_text="Parcel delivery company"
    )

    tracking_url = models.URLField(
        blank=True,
        null=True,
        help_text="Direct link to tracking (e.g., https://tracking.fedex.com/...)",
    )

    shipped_at = models.DateTimeField(
        auto_now_add=True, help_text="Date/time when sent"
    )

    estimated_delivery_date = models.DateField(
        blank=True, null=True, help_text="Estimated delivery date of the carrier"
    )

    actual_delivery_date = models.DateField(
        blank=True, null=True, help_text="Date when it was actually delivered"
    )

    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Package weight in kg",
    )

    dimensions = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Package dimensions (e.g., 30x20x10 cm)",
    )

    last_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Last known location of the package",
    )

    last_status_update = models.DateTimeField(
        blank=True, null=True, help_text="Latest carrier update"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order Tracking"
        verbose_name_plural = "Order Tracking"

    def __str__(self):
        return f"Tracking {self.tracking_number} - {self.get_carrier_display()}"

    def get_full_tracking_info(self):
        """Returns formatted tracking information"""
        info = f"Tracking number: {self.tracking_number}\n"
        info += f"Parcel delivery: {self.get_carrier_display()}\n"
        if self.tracking_url:
            info += f"Tracking link: {self.tracking_url}\n"
        if self.last_location:
            info += f"Last location: {self.last_location}\n"
        if self.estimated_delivery_date:
            info += f"Estimated delivery: {self.estimated_delivery_date}\n"
        return info
