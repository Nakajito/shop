from django import forms
from .models import Order
from orders.models import Address


class OrderCreateForm(forms.ModelForm):
    """
    Form for creating a new Order.

    This ModelForm is used in the checkout view. It exposes the essential
    customer details required to process an order (name, email, address)
    while excluding internal fields like 'paid', 'created', or 'stripe_id'.
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


class AddressForm(forms.ModelForm):
    """
    Form to create or edit shipping addresses.

    This form handles user input for the Address model. It excludes the 'user'
    field because that is securely assigned in the view based on the currently
    logged-in user.

    It uses Bootstrap-ready widgets for immediate frontend integration.
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
                attrs={"class": "form-control", "placeholder": "Recipient's name"}
            ),
            "address_line1": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Street, number, and apartment",
                }
            ),
            "address_line2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Additional information (optional)",
                }
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "City"}
            ),
            "state": forms.Select(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Postal Code"}
            ),
            "country": forms.Select(attrs={"class": "form-control"}),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "5547130542"}
            ),
            "address_type": forms.Select(attrs={"class": "form-control"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

        labels = {
            "recipient_name": "Recipient's name",
            "address_line1": "Main address",
            "address_line2": "Secondary address",
            "city": "City",
            "state": "State/Province",
            "postal_code": "Postal code",
            "country": "Country",
            "phone": "Contact telephone number",
            "address_type": "Address type",
            "is_default": "Use as default address",
        }
