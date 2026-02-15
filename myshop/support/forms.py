from django import forms
from django.utils.translation import gettext_lazy as _
from support.models import SupportTicket, TicketMessage


class SupportTicketForm(forms.ModelForm):
    """
    Form for customers to create new support tickets.
    """

    class Meta:
        model = SupportTicket
        fields = ["issue_type", "subject", "message", "priority", "order"]
        widgets = {
            "issue_type": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Briefly describe the issue"),
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": _("Please provide as much detail as possible..."),
                }
            ),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "order": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Add labels for better UX
        self.fields["order"].empty_label = _("Not related to a specific order")

        if user:
            # Filter orders to show only those belonging to the current user
            # Ordered by newest first to make selection easier
            self.fields["order"].queryset = user.orders.all().order_by("-created")


class TicketMessageForm(forms.ModelForm):
    """
    Form for users to add replies to an existing ticket.
    """

    class Meta:
        model = TicketMessage
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Type your reply here..."),
                }
            ),
        }
