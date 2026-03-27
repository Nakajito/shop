from decimal import Decimal

from accounts.models import CustomUser
from coupons.models import Coupon
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from payment.models import PaymentMethod
from shop.models import Product

from orders.managers import OrderManager

STATUS_CHOICES = (
    ("pending", _("Pending")),
    ("confirmed", _("Confirmed")),
    ("preparing", _("Preparing")),
    ("shipped", _("Shipped")),
    ("delivered", _("Delivered")),
    ("cancelled", _("Cancelled")),
)


class Address(models.Model):
    """
    Model representing a user's shipping or billing address.
    """

    class AddressType(models.TextChoices):
        HOME = "home", _("Home")
        OFFICE = "office", _("Office")
        OTHER = "other", _("Other")

    # We define Country/State choices here or import them from a utils file
    # to keep the global namespace clean.
    COUNTRY_CHOICES = (
        ("MX", _("Mexico")),
        ("US", _("United States")),
        ("ES", _("Spain")),
    )

    STATE_CHOICES = (
        ("CDMX", "Ciudad de México"),
        ("MEX", "Estado de México"),
        ("QRO", "Querétaro"),
        # Add more states as needed
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("user"),
    )

    address_line1 = models.CharField(
        _("address line 1"),
        max_length=255,
        help_text=_("Street, number, and apartment"),
    )

    address_line2 = models.CharField(
        _("address line 2"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Additional information (floor, reference, etc.)"),
    )

    city = models.CharField(_("city"), max_length=100)

    state = models.CharField(_("state"), max_length=50, choices=STATE_CHOICES)

    postal_code = models.CharField(_("postal code"), max_length=10)

    country = models.CharField(
        _("country"), max_length=2, choices=COUNTRY_CHOICES, default="MX"
    )

    phone = models.CharField(
        _("phone number"),
        max_length=15,
        help_text=_("Contact telephone number for shipping"),
    )

    recipient_name = models.CharField(
        _("recipient name"),
        max_length=200,
        help_text=_("Name of the person receiving the package"),
    )

    is_default = models.BooleanField(
        _("default address"),
        default=False,
    )

    address_type = models.CharField(
        _("address type"),
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.HOME,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-is_default"]),
        ]

    def __str__(self):
        return f"{self.recipient_name} - {self.city}"

    def save(self, *args, **kwargs):
        """
        Ensure only one address is marked as default per user.
        """
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)

    def get_full_address(self):
        """Return the formatted full address string."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        location = f"{self.city}, {self.state}, {self.postal_code}"
        parts.append(location)
        parts.append(self.get_country_display())
        return ", ".join(parts)


class Order(models.Model):
    """
    Model representing a customer order.
    Includes snapshots of shipping data, payment status, and coupon usage.
    """

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("user"),
    )

    # Snapshot fields: These store the data AS IT WAS when the order was created.
    # Even if the User or Address model changes later, this data remains historic.
    first_name = models.CharField(_("first name"), max_length=50)
    last_name = models.CharField(_("last name"), max_length=50)
    email = models.EmailField(_("email"))
    address = models.CharField(_("address"), max_length=250)
    postal_code = models.CharField(_("postal code"), max_length=20)
    city = models.CharField(_("city"), max_length=100)

    # Links to Address book (optional, for reference)
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_as_shipping",
        verbose_name=_("shipping address reference"),
    )

    billing_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_as_billing",
        verbose_name=_("billing address reference"),
    )

    created = models.DateTimeField(_("created at"), auto_now_add=True)
    updated = models.DateTimeField(_("updated at"), auto_now=True)

    paid = models.BooleanField(_("paid"), default=False)

    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    estimated_delivery_date = models.DateField(
        _("estimated delivery"), null=True, blank=True
    )

    notes = models.TextField(_("internal notes"), blank=True, null=True)
    customer_notes = models.TextField(_("customer notes"), blank=True, null=True)

    # Payment Integration
    stripe_id = models.CharField(_("Stripe Payment ID"), max_length=250, blank=True)

    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("payment method"),
    )

    # Coupon Integration
    coupon = models.ForeignKey(
        Coupon,
        related_name="orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("coupon"),
    )

    discount = models.IntegerField(
        _("discount percentage"),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    objects = OrderManager()

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["-created"]),
            models.Index(fields=["status"]),
            models.Index(fields=["paid"]),
            models.Index(fields=["user", "-created"]),
            models.Index(fields=["user", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(discount__gte=0, discount__lte=100),
                name="order_discount_range",
            ),
        ]

    def __str__(self):
        return f"Order {self.id}"

    def get_total_cost_before_discount(self):
        """Sum of all items before discount."""
        return sum(item.get_cost() for item in self.items.all())

    def get_discount(self):
        """Calculate discount amount."""
        total = self.get_total_cost_before_discount()
        if self.discount:
            return total * (self.discount / Decimal(100))
        return Decimal(0)

    def get_total_cost(self):
        """Final total to pay."""
        return self.get_total_cost_before_discount() - self.get_discount()

    def get_status_display_with_badge(self):
        badge_map = {
            "pending": "warning",
            "confirmed": "info",
            "preparing": "primary",
            "shipped": "info",
            "delivered": "success",
            "cancelled": "danger",
        }
        color = badge_map.get(self.status, "secondary")
        return f'<span class="badge bg-{color}">{self.get_status_display()}</span>'

    @property
    def can_be_reordered(self):
        # Allow reordering for delivered, cancelled and confirmed orders
        return self.status in ("delivered", "cancelled", "confirmed")

    @property
    def can_be_cancelled(self):
        return self.status in ("pending", "confirmed")

    def get_stripe_url(self):
        """Generate link to Stripe dashboard based on environment."""
        if not self.stripe_id:
            return ""
        path = "/test/" if "_test_" in settings.STRIPE_SECRET_KEY else "/"
        return f"https://dashboard.stripe.com{path}payments/{self.stripe_id}"

    def get_timeline_steps(self):
        """
        Returns steps for the frontend timeline visualization.
        """
        steps = [
            {"id": "confirmed", "label": _("Confirmed"), "icon": "bi-check-circle"},
            {"id": "shipped", "label": _("Shipped"), "icon": "bi-truck"},
            {"id": "delivered", "label": _("Delivered"), "icon": "bi-house-door"},
        ]

        status_order = ["pending", "confirmed", "shipped", "delivered"]

        current_idx = -1
        if self.status in status_order:
            current_idx = status_order.index(self.status)

        timeline = []
        for step in steps:
            step_idx = status_order.index(step["id"])

            is_completed = current_idx >= step_idx
            is_current = current_idx == step_idx

            timeline.append(
                {
                    "label": step["label"],
                    "completed": is_completed,
                    "current": is_current,
                    "icon": step["icon"],
                }
            )

        return timeline

    def change_status(self, new_status, user=None, note=""):
        """
        Updates the order status and creates a tracking log entry.
        """
        if self.status != new_status:
            old_status = self.status
            self.status = new_status
            self.save()

            # Create a status update audit entry (OrderStatusUpdate)
            OrderStatusUpdate.objects.create(
                order=self,
                old_status=old_status,
                new_status=new_status,
                changed_by=user,
                reason=note,
            )

            # If you need to create or update shipping tracking information
            # for specific statuses (e.g. 'shipped'), handle that elsewhere.
            return True
        return False


class OrderItem(models.Model):
    """
    Individual line item within an order.
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="order_items", on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.id}"

    def get_cost(self):
        return self.price * self.quantity


class OrderStatusUpdate(models.Model):
    """
    Audit log for order status changes.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_updates",
    )
    old_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    changed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Status Update")
        verbose_name_plural = _("Status Updates")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.old_status} -> {self.new_status}"


class OrderTracking(models.Model):
    """
    Tracking and shipping information.
    """

    class Carrier(models.TextChoices):
        FEDEX = "fedex", "FedEx"
        UPS = "ups", "UPS"
        DHL = "dhl", "DHL"
        OTHER = "other", _("Other")

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="tracking",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    note = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    tracking_number = models.CharField(max_length=255)
    carrier = models.CharField(max_length=20, choices=Carrier.choices)
    tracking_url = models.URLField(blank=True, null=True)

    # Dates
    shipped_at = models.DateTimeField(auto_now_add=True)
    estimated_delivery_date = models.DateField(blank=True, null=True)
    actual_delivery_date = models.DateField(blank=True, null=True)

    # Details
    weight = models.DecimalField(
        _("weight (kg)"), max_digits=8, decimal_places=2, blank=True, null=True
    )
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    last_location = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Order Tracking")
        verbose_name_plural = _("Order Trackings")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.tracking_number} ({self.get_carrier_display()})"

    def get_full_tracking_info(self):
        lines = [
            f"{_('Tracking Number')}: {self.tracking_number}",
            f"{_('Carrier')}: {self.get_carrier_display()}",
        ]
        if self.tracking_url:
            lines.append(f"{_('Link')}: {self.tracking_url}")
        return "\n".join(lines)
