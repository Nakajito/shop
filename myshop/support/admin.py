from django.contrib import admin
from support.models import SupportTicket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    """Mostrar mensajes inline en el ticket"""

    model = TicketMessage
    extra = 1
    fields = ("sender", "message", "is_internal", "created_at")
    readonly_fields = ("sender", "created_at")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """Admin para gestionar tickets de soporte"""

    list_display = (
        "id",
        "user",
        "subject",
        "issue_type",
        "status",
        "priority",
        "created_at",
    )
    list_filter = ("status", "priority", "issue_type", "created_at")
    search_fields = ("user__username", "subject", "message")
    readonly_fields = ("created_at", "updated_at", "resolved_at")
    inlines = [TicketMessageInline]

    fieldsets = (
        ("Información General", {"fields": ("user", "order", "subject", "issue_type")}),
        ("Detalles", {"fields": ("message",)}),
        ("Estado", {"fields": ("status", "priority", "assigned_to")}),
        (
            "Auditoría",
            {
                "fields": ("created_at", "updated_at", "resolved_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    """Admin para ver mensajes de tickets"""

    list_display = ("ticket", "sender", "is_internal", "created_at")
    list_filter = ("is_internal", "created_at")
    search_fields = ("ticket__subject", "message")
    readonly_fields = ("created_at",)
