from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser
from orders.models import Order
from support.managers import SupportTicketManager


class SupportTicket(models.Model):
    """
    Model for customer support tickets.
    Handles issue reporting, clarifications, and staff assignments.
    """

    class IssueType(models.TextChoices):
        CLARIFICATION = "clarification", _("Request Clarification")
        PROBLEM = "problem", _("Report a Problem")
        CONTACT = "contact", _("Contact Support")
        REFUND = "refund", _("Request Refund")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        IN_PROGRESS = "in_progress", _("In Progress")
        WAITING_CUSTOMER = "waiting_customer", _("Waiting for Customer")
        RESOLVED = "resolved", _("Resolved")
        CLOSED = "closed", _("Closed")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        verbose_name=_("user"),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
        verbose_name=_("related order"),
    )

    issue_type = models.CharField(
        max_length=20,
        choices=IssueType.choices,
        default=IssueType.CONTACT,
        verbose_name=_("issue type"),
    )

    subject = models.CharField(max_length=255, verbose_name=_("subject"))

    message = models.TextField(verbose_name=_("detailed description"))

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name=_("status"),
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name=_("priority"),
    )

    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name=_("assigned staff"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("resolved at")
    )

    objects = SupportTicketManager()

    class Meta:
        verbose_name = _("Support Ticket")
        verbose_name_plural = _("Support Tickets")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"#{self.id} - {self.subject} ({self.get_status_display()})"

    def get_status_color(self):
        """Returns Bootstrap 5 context class for the status badge."""
        colors = {
            self.Status.OPEN: "danger",
            self.Status.IN_PROGRESS: "info",
            self.Status.WAITING_CUSTOMER: "warning",
            self.Status.RESOLVED: "success",
            self.Status.CLOSED: "secondary",
        }
        return colors.get(self.status, "secondary")

    def save(self, *args, **kwargs):
        # Automatically set resolved_at when status changes to resolved
        if self.status == self.Status.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)


class TicketMessage(models.Model):
    """
    Messages within a support ticket conversation.
    """

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("ticket"),
    )

    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_messages",
        verbose_name=_("sender"),
    )

    message = models.TextField(verbose_name=_("message content"))

    is_internal = models.BooleanField(
        default=False,
        verbose_name=_("internal note"),
        help_text=_("Staff only. Hidden from the customer."),
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Ticket Message")
        verbose_name_plural = _("Ticket Messages")
        ordering = ["created_at"]

    def __str__(self):
        return f"Message by {self.sender} on Ticket #{self.ticket.id}"

    @property
    def is_staff_reply(self):
        """Checks if the sender is a staff member."""
        return self.sender.is_staff if self.sender else False
