import csv
import datetime
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem, Address, OrderStatusUpdate, OrderTracking


def export_to_csv(modeladmin, request, queryset):
    """
    Admin action to export selected orders to a CSV file.

    This function introspects the model fields to dynamically generate
    header columns and data rows. It handles datetime formatting and
    excludes many-to-many or one-to-many relationships to keep the CSV flat.

    Args:
        modeladmin (ModelAdmin): The admin class instance.
        request (HttpRequest): The current request.
        queryset (QuerySet): The list of selected objects to export.

    Returns:
        HttpResponse: A response containing the generated CSV file with
        Content-Disposition set to attachment.
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


export_to_csv.short_description = "Export to CSV"


def order_payment(obj):
    """
    Display a link to the Stripe payment dashboard for this order.

    Requires the Order model to have a `get_stripe_url()` method and
    a `stripe_id` field.
    """
    url = obj.get_stripe_url()
    if obj.stripe_id:
        html = f'<a href="{url}" target="_blank">{obj.stripe_id}</a>'
        return mark_safe(html)
    return ""


order_payment.short_description = "Stripe payment"


def order_detail(obj):
    """
    Display a link to the custom admin detail view for the order.
    """
    url = reverse("orders:admin_order_detail", args=[obj.id])
    return mark_safe(f'<a href="{url}">View</a>')


def order_pdf(obj):
    """
    Display a link to generate and download the PDF invoice for the order.
    """
    url = reverse("orders:admin_order_pdf", args=[obj.id])
    return mark_safe(f"<a href='{url}' target='_blank'>PDF</a>")


order_pdf.short_description = "Invoice"


class OrderItemsInLine(admin.TabularInline):
    """
    Inline admin view for OrderItems.

    Allows admins to view and edit the specific products (items) attached
    to an Order directly within the Order detail page.
    """

    model = OrderItem
    raw_id_fields = ["product"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Administration interface for the Order model.

    Features:
    - Lists essential customer and status information.
    - Includes computed columns for Stripe links, PDF invoices, and detailed views.
    - Filters by payment status and dates.
    - Inline editing of order items.
    - custom action to export selected orders to CSV.
    """

    list_display = [
        "id",
        "first_name",
        "last_name",
        "email",
        "user",
        "shipping_address",
        "paid",
        "status",
        order_payment,
        "created",
        "updated",
        order_detail,
        order_pdf,
    ]
    readonly_fields = ("created", "updated")
    fieldsets = (
        ("Customer", {"fields": ("first_name", "last_name", "email")}),
        ("Address", {"fields": ("shipping_address", "billing_address")}),
        ("Payment", {"fields": ("payment_method", "paid", "stripe_id")}),
        (
            "Order",
            {"fields": ("status", "estimated_delivery_date", "coupon", "discount")},
        ),
        ("Notes", {"fields": ("notes", "customer_notes")}),
        ("Audit", {"fields": ("created", "updated"), "classes": ("collapse",)}),
    )
    list_filter = ["paid", "created", "status"]
    search_fields = ("id", "first_name", "last_name", "email")
    inlines = [OrderItemsInLine]
    actions = [export_to_csv]

    def get_total(self, obj):
        return f"${obj.get_total()}"

    get_total.short_description = "Total"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin to manage shipping addresses"""

    list_display = (
        "recipient_name",
        "user",
        "address_line1",
        "city",
        "state",
        "is_default",
        "created_at",
    )
    list_filter = ("country", "state", "is_default", "address_type", "created_at")
    search_fields = (
        "user__username",
        "recipient_name",
        "address_line1",
        "city",
        "postal_code",
    )
    readonly_fields = ("created_at", "updated_at", "get_full_address")

    fieldsets = (
        ("User", {"fields": ("user",)}),
        ("Delivery Information", {"fields": ("recipient_name", "phone")}),
        (
            "Address",
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
        ("Configuration", {"fields": ("address_type", "is_default")}),
        (
            "Full Address",
            {"fields": ("get_full_address",), "classes": ("collapse",)},
        ),
        (
            "Audit",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_full_address(self, obj):
        """Display the full address in the admin panel"""
        return obj.get_full_address()

    get_full_address.short_description = "Full"


class OrderStatusUpdateInline(admin.TabularInline):
    """Show inline status change history"""

    model = OrderStatusUpdate
    extra = 0
    can_delete = False
    readonly_fields = ("old_status", "new_status", "changed_by", "reason", "created_at")
    fields = ("old_status", "new_status", "changed_by", "reason", "created_at")


class OrderTrackingInline(admin.StackedInline):
    """Display tracking information inline"""

    model = OrderTracking
    extra = 0
    readonly_fields = ("shipped_at", "created_at", "updated_at")
    fields = (
        "tracking_number",
        "carrier",
        "tracking_url",
        "shipped_at",
        "estimated_delivery_date",
        "actual_delivery_date",
        "weight",
        "dimensions",
        "last_location",
        "last_status_update",
    )


@admin.register(OrderStatusUpdate)
class OrderStatusUpdateAdmin(admin.ModelAdmin):
    """Admin to view status changes"""

    list_display = ("order", "old_status", "new_status", "changed_by", "created_at")
    list_filter = ("new_status", "created_at")
    search_fields = ("order__id", "order__email")
    readonly_fields = ("created_at",)

    def has_add_permission(self, request):
        """Do not allow manual changes to be added from the admin panel"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Do not allow changes to be deleted (audit)"""
        return False


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    """Admin to manage tracking information"""

    list_display = (
        "order",
        "tracking_number",
        "carrier",
        "actual_delivery_date",
        "last_status_update",
    )
    list_filter = ("carrier", "shipped_at", "actual_delivery_date")
    search_fields = ("order__id", "tracking_number")
    readonly_fields = (
        "shipped_at",
        "created_at",
        "updated_at",
        "get_full_tracking_info",
    )

    fieldsets = (
        ("Order", {"fields": ("order",)}),
        (
            "Shipping Information",
            {"fields": ("tracking_number", "carrier", "tracking_url")},
        ),
        (
            "Dates",
            {
                "fields": (
                    "shipped_at",
                    "estimated_delivery_date",
                    "actual_delivery_date",
                )
            },
        ),
        (
            "Package Details",
            {"fields": ("weight", "dimensions", "last_location", "last_status_update")},
        ),
        (
            "Formatted Information",
            {"fields": ("get_full_tracking_info",), "classes": ("collapse",)},
        ),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_full_tracking_info(self, obj):
        if obj.pk:
            return obj.get_full_tracking_info()
        return "Save first to view information"

    get_full_tracking_info.short_description = "Complete Tracking Information"
