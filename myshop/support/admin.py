from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from support.models import SupportTicket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    """
    Displays ticket messages inline within the SupportTicket detail view.
    """

    model = TicketMessage
    extra = 1
    fields = ("sender", "message", "is_internal", "created_at")
    readonly_fields = ("sender", "created_at")
    verbose_name = _("Message")
    verbose_name_plural = _("Ticket Conversation")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """
    Admin interface for managing support tickets and customer issues.
    """

    list_display = (
        "id",
        "user",
        "subject",
        "issue_type",
        "status_badge",
        "priority_badge",
        "created_at",
    )
    list_filter = ("status", "priority", "issue_type", "created_at")
    search_fields = ("user__username", "user__email", "subject", "message")
    readonly_fields = ("created_at", "updated_at", "resolved_at")
    inlines = [TicketMessageInline]

    fieldsets = (
        (
            _("General Information"),
            {"fields": ("user", "order", "subject", "issue_type")},
        ),
        (_("Initial Details"), {"fields": ("message",)}),
        (_("Management"), {"fields": ("status", "priority", "assigned_to")}),
        (
            _("Audit Trail"),
            {
                "fields": ("created_at", "updated_at", "resolved_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        """Renders a color-coded badge based on ticket status."""
        colors = {
            "open": "#dc3545",  # Red
            "in_progress": "#ffc107",  # Yellow
            "waiting": "#17a2b8",  # Teal
            "resolved": "#28a745",  # Green
            "closed": "#6c757d",  # Grey
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 10px; text-transform: uppercase;">{}</span>',
            colors.get(obj.status, "#000"),
            obj.get_status_display(),
        )

    @admin.display(description=_("Priority"))
    def priority_badge(self, obj):
        """Highlights high-priority tickets."""
        if obj.priority == "high" or obj.priority == "urgent":
            return format_html(
                '<strong style="color: #dc3545;">{}</strong>',
                obj.get_priority_display(),
            )
        return obj.get_priority_display()


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    """
    Standalone admin for auditing individual ticket messages.
    """

    list_display = ("ticket", "sender", "is_internal_display", "created_at")
    list_filter = ("is_internal", "created_at")
    search_fields = ("ticket__subject", "message", "sender__username")
    readonly_fields = ("created_at",)

    @admin.display(boolean=True, description=_("Internal Note"))
    def is_internal_display(self, obj):
        return obj.is_internal
