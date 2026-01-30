from django import forms
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
