from django import forms
from payment.models import PaymentMethod


class PaymentMethodForm(forms.Form):
    """Form to add a payment card.
    This form is sent directly to Stripe (we do not store sensitive data).

    In the view, we will use Stripe Elements to capture card data
    securely, without our server seeing it.

    Args:
        forms (_type_): _description_
    """

    cardholder_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Name of the holder",
                "autocomplete": "cc-name",
            }
        ),
    )

    is_default = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Use as default payment method",
    )
