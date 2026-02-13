from django import forms
from support.models import SupportTicket, TicketMessage


class SupportTicketForm(forms.ModelForm):
    """Formulario para crear tickets de soporte"""

    class Meta:
        model = SupportTicket
        fields = ["issue_type", "subject", "message", "priority", "order"]
        widgets = {
            "issue_type": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": True,
                }
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Escribe un asunto breve",
                    "required": True,
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Cuéntanos con detalle qué sucede...",
                    "required": True,
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": True,
                }
            ),
            "order": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": False,
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Limitar los pedidos al usuario actual
            self.fields["order"].queryset = user.orders.all()


class TicketMessageForm(forms.ModelForm):
    """Formulario para responder a tickets"""

    class Meta:
        model = TicketMessage
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Escribe tu respuesta...",
                    "required": True,
                }
            ),
        }
