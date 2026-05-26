from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Address, Order


class OrderCreateForm(forms.ModelForm):
    """
    Form for creating a new Order during checkout.

    This ModelForm handles the essential customer details required to process
    an order. It includes Bootstrap styling for immediate frontend integration.
    """

    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email", "address", "postal_code", "city"]

        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
        }

        labels = {
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "email": _("Email Address"),
            "address": _("Shipping Address"),
            "postal_code": _("Postal Code"),
            "city": _("City"),
        }


class AddressForm(forms.ModelForm):
    """
    Form to create or edit shipping addresses.

    This form handles user input for the Address model, excluding the 'user'
    field which is assigned in the view. It uses Bootstrap-ready widgets.
    """

    class Meta:
        model = Address
        fields = [
            "recipient_name",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "phone",
            "address_type",
            "is_default",
        ]

        widgets = {
            "recipient_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Recipient's full name"),
                }
            ),
            "address_line1": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Street address, company name, c/o"),
                }
            ),
            "address_line2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Apartment, suite, unit, building, floor, etc."),
                }
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("City")}
            ),
            # 'form-select' is the correct class for dropdowns in Bootstrap 5
            "state": forms.Select(attrs={"class": "form-select"}),
            "postal_code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("ZIP / Postal Code")}
            ),
            "country": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Phone number (for delivery updates)"),
                }
            ),
            "address_type": forms.Select(attrs={"class": "form-select"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

        labels = {
            "recipient_name": _("Recipient's Name"),
            "address_line1": _("Address Line 1"),
            "address_line2": _("Address Line 2 (Optional)"),
            "city": _("City"),
            "state": _("State / Province / Region"),
            "postal_code": _("Postal Code"),
            "country": _("Country"),
            "phone": _("Phone Number"),
            "address_type": _("Address Type"),
            "is_default": _("Set as default address"),
        }
