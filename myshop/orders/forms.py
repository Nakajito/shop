from django import forms
from .models import Order


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
