from django.db import models
from django.db.models import Q
from accounts.models import CustomUser
from orders.models import Order


class SupportTicket(models.Model):
    """
    Modelo para tickets de soporte al cliente.
    Permite reportar problemas, aclaraciones y contactar soporte.
    """

    ISSUE_TYPE_CHOICES = (
        ("clarification", "Solicitar Aclaración"),
        ("problem", "Reportar Problema"),
        ("contact", "Contactar Soporte"),
        ("refund", "Solicitar Reembolso"),
        ("other", "Otro"),
    )

    STATUS_CHOICES = (
        ("open", "Abierto"),
        ("in_progress", "En Progreso"),
        ("waiting_customer", "Esperando Respuesta"),
        ("resolved", "Resuelto"),
        ("closed", "Cerrado"),
    )

    PRIORITY_CHOICES = (
        ("low", "Baja"),
        ("medium", "Media"),
        ("high", "Alta"),
        ("urgent", "Urgente"),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        help_text="Usuario que creó el ticket",
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
        help_text="Pedido relacionado (opcional)",
    )

    issue_type = models.CharField(
        max_length=20,
        choices=ISSUE_TYPE_CHOICES,
        default="contact",
        help_text="Tipo de problema",
    )

    subject = models.CharField(max_length=255, help_text="Asunto del ticket")

    message = models.TextField(help_text="Descripción detallada del problema")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        help_text="Estado del ticket",
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium",
        help_text="Prioridad del ticket",
    )

    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        help_text="Staff asignado",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha de resolución"
    )

    class Meta:
        verbose_name = "Ticket de Soporte"
        verbose_name_plural = "Tickets de Soporte"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"#{self.id} - {self.subject} ({self.get_status_display()})"

    def get_status_color(self):
        """Retorna color para badge del estado"""
        colors = {
            "open": "danger",
            "in_progress": "info",
            "waiting_customer": "warning",
            "resolved": "success",
            "closed": "secondary",
        }
        return colors.get(self.status, "secondary")


class TicketMessage(models.Model):
    """
    Modelo para mensajes en un ticket de soporte.
    Permite conversación entre usuario y soporte.
    """

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
        help_text="Ticket relacionado",
    )

    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_messages",
        help_text="Usuario que envió el mensaje",
    )

    message = models.TextField(help_text="Contenido del mensaje")

    is_internal = models.BooleanField(
        default=False, help_text="¿Es una nota interna del equipo?"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje de Ticket"
        verbose_name_plural = "Mensajes de Ticket"
        ordering = ["created_at"]

    def __str__(self):
        return f"Mensaje en Ticket #{self.ticket.id}"
