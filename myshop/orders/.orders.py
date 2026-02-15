from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Order


class OrderCreateForm(forms.ModelForm):
    """
    Form for creating a new Order instance.

    This form is used during the checkout process to collect essential
    shipping and contact information from the user. It excludes internal
    fields like payment status, created dates, or discount logic.
    """

    class Meta:
        model = Order
        fields = [
            "first_name",
            "last_name",
            "email",
            "address",
            "postal_code",
            "city",
        ]

        # Add Bootstrap 5 classes for consistent styling
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("John")}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Doe")}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "john@example.com"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("123 Main St")}
            ),
            "postal_code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "12345"}
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("City")}
            ),
        }

        labels = {
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "email": _("Email Address"),
            "address": _("Shipping Address"),
            "postal_code": _("Postal Code"),
            "city": _("City"),
        }
