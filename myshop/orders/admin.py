import csv
import datetime

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from payment.models import PaymentMethod

from .models import Address, Order, OrderItem, OrderStatusUpdate, OrderTracking


@admin.action(description=_("Export selected orders to CSV"))
def export_to_csv(modeladmin, request, queryset):
    """
    Admin action to export selected orders to a CSV file.

    This function introspects the model fields to dynamically generate
    header columns and data rows. It handles datetime formatting and
    excludes many-to-many or one-to-many relationships to keep the CSV flat.
    """
    opts = modeladmin.model._meta
    content_disposition = f"attachment; filename={opts.verbose_name}.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = content_disposition
    writer = csv.writer(response)

    # dynamically get fields, excluding relationships
    fields = [
        field
        for field in opts.get_fields()
        if not field.many_to_many and not field.one_to_many
    ]

    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])

    # Write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime("%d/%m/%Y")
            data_row.append(value)
        writer.writerow(data_row)
    return response


class OrderItemsInline(admin.TabularInline):
    """
    Inline admin view for OrderItems (read-only).
    """

    model = OrderItem
    raw_id_fields = ["product"]
    extra = 0
    readonly_fields = ("product", "price", "quantity")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderStatusUpdateInline(admin.TabularInline):
    """Show inline status change history (Read-only for audit)."""

    model = OrderStatusUpdate
    extra = 0
    can_delete = False
    readonly_fields = ("old_status", "new_status", "changed_by", "reason", "created_at")

    def has_add_permission(self, request, obj):
        return False


class OrderTrackingInline(admin.StackedInline):
    """Display tracking information inline."""

    model = OrderTracking
    extra = 0
    readonly_fields = ("user", "created_at", "updated_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Administration interface for the Order model.

    Features:
    - Lists essential customer and status information.
    - Includes computed columns for Stripe links, PDF invoices, and detailed views.
    - Filters by payment status and dates.
    - Inline editing of order items and tracking info.
    - Custom action to export selected orders to CSV.
    """

    list_display = [
        "id",
        "first_name",
        "last_name",
        "email",
        "paid",
        "status",
        "order_payment",
        "created",
        "updated",
        "order_detail_link",
        "order_pdf_link",
    ]

    list_filter = ["paid", "created", "updated", "status"]
    search_fields = ["first_name", "last_name", "email"]
    inlines = [OrderItemsInline, OrderTrackingInline, OrderStatusUpdateInline]
    actions = [export_to_csv]

    readonly_fields = (
        "created",
        "updated",
        "order_payment",
        "first_name",
        "last_name",
        "email",
        "user",
    )

    fieldsets = (
        (
            _("Customer Information"),
            {
                "fields": ("first_name", "last_name", "email", "user"),
                "description": _("Read-only customer snapshot at purchase time."),
            },
        ),
        (_("Shipping & Billing"), {"fields": ("shipping_address", "billing_address")}),
        (
            _("Payment Details"),
            {"fields": ("payment_method", "paid", "order_payment")},
        ),
        (
            _("Order Details"),
            {"fields": ("status", "estimated_delivery_date", "coupon", "discount")},
        ),
        (
            _("Notes"),
            {"fields": ("notes", "customer_notes"), "classes": ("collapse",)},
        ),
        (_("Timestamps"), {"fields": ("created", "updated"), "classes": ("collapse",)}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ("shipping_address", "billing_address"):
            order_id = request.resolver_match.kwargs.get("object_id")
            if order_id:
                try:
                    order = Order.objects.get(pk=order_id)
                    if order.user:
                        kwargs["queryset"] = Address.objects.filter(user=order.user)
                    else:
                        kwargs["queryset"] = Address.objects.none()
                except Order.DoesNotExist:
                    kwargs["queryset"] = Address.objects.none()
        elif db_field.name == "payment_method":
            order_id = request.resolver_match.kwargs.get("object_id")
            if order_id:
                try:
                    order = Order.objects.get(pk=order_id)
                    if order.user:
                        kwargs["queryset"] = PaymentMethod.objects.filter(
                            user=order.user
                        )
                    else:
                        kwargs["queryset"] = PaymentMethod.objects.none()
                except Order.DoesNotExist:
                    kwargs["queryset"] = PaymentMethod.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def order_payment(self, obj):
        """Link to Stripe Dashboard if applicable."""
        url = obj.get_stripe_url()
        if obj.stripe_id and url:
            return format_html(
                '<a href="{}" target="_blank">{}</a>', url, obj.stripe_id
            )
        return obj.stripe_id or "-"

    order_payment.short_description = _("Stripe Payment")

    def order_detail_link(self, obj):
        """Link to custom order detail view."""
        url = reverse("orders:admin_order_detail", args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, _("View"))

    order_detail_link.short_description = _("Detail")

    def order_pdf_link(self, obj):
        """Link to download PDF invoice."""
        url = reverse("orders:admin_order_pdf", args=[obj.id])
        return format_html('<a href="{}" target="_blank">{}</a>', url, _("Invoice"))

    order_pdf_link.short_description = _("PDF")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin to manage shipping addresses."""

    list_display = (
        "recipient_name",
        "user",
        "city",
        "state",
        "country",
        "is_default",
        "address_type",
    )
    list_filter = ("country", "state", "is_default", "address_type")
    search_fields = (
        "user__username",
        "recipient_name",
        "address_line1",
        "city",
        "postal_code",
    )
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (_("User & Recipient"), {"fields": ("user", "recipient_name", "phone")}),
        (
            _("Address Details"),
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                )
            },
        ),
        (_("Settings"), {"fields": ("address_type", "is_default")}),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# No need to register OrderStatusUpdate separately if it's an inline on Order
# unless you want a global view of all status changes.
@admin.register(OrderStatusUpdate)
class OrderStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ("order", "old_status", "new_status", "changed_by", "created_at")
    list_filter = ("new_status", "created_at")
    readonly_fields = (
        "order",
        "old_status",
        "new_status",
        "changed_by",
        "reason",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    """Admin to manage tracking information independently."""

    list_display = (
        "order",
        "order_customer",
        "tracking_number",
        "carrier",
        "status",
        "estimated_delivery_date",
    )
    search_fields = ("order__id", "tracking_number")
    list_filter = ("carrier", "status")

    readonly_fields = (
        "order",
        "user",
        "order_customer",
        "order_email",
        "order_status",
        "order_total",
        "order_paid",
        "shipped_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            _("Order Information"),
            {
                "fields": (
                    "order",
                    "order_customer",
                    "order_email",
                    "order_status",
                    "order_total",
                    "order_paid",
                ),
                "description": _("Read-only information from the associated order."),
            },
        ),
        (
            _("Tracking Details"),
            {
                "fields": (
                    "user",
                    "tracking_number",
                    "carrier",
                    "tracking_url",
                    "status",
                ),
            },
        ),
        (
            _("Shipping Details"),
            {
                "fields": (
                    "shipped_at",
                    "estimated_delivery_date",
                    "actual_delivery_date",
                    "weight",
                    "dimensions",
                    "last_location",
                ),
            },
        ),
        (
            _("Notes"),
            {"fields": ("note",), "classes": ("collapse",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def order_customer(self, obj):
        if obj.order:
            return f"{obj.order.first_name} {obj.order.last_name}"
        return "-"

    order_customer.short_description = _("Customer")

    def order_email(self, obj):
        if obj.order:
            return obj.order.email
        return "-"

    order_email.short_description = _("Email")

    def order_status(self, obj):
        if obj.order:
            return obj.order.get_status_display()
        return "-"

    order_status.short_description = _("Order Status")

    def order_total(self, obj):
        if obj.order:
            return f"${obj.order.get_total_cost()}"
        return "-"

    order_total.short_description = _("Order Total")

    def order_paid(self, obj):
        if obj.order:
            return obj.order.paid
        return False

    order_paid.short_description = _("Paid")
    order_paid.boolean = True
