from django import forms
from payment.models import PaymentMethod


class PaymentMethodForm(forms.Form):
    """Form to add a payment card using Stripe Elements.

    IMPORTANT: Sensitive data (number, CVC) is captured in JavaScript
    with Stripe Elements, NEVER on the server.
    The server only receives payment_method_id from Stripe.

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
        label="Name of the Holder",
    )

    is_default = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Use as default payment method",
    )


class PaymentMethodSelectionForm(forms.Form):
    """
    Form to select an existing payment method at checkout.
    """

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get active payment methods from the user
        payment_methods = user.payment_methods.filter(is_active=True)

        choices = [
            (
                pm.id,
                f"{pm.get_card_type_display()} ****{pm.last_four_digits} (Expires: {pm.get_expiration_display()})",
            )
            for pm in payment_methods
        ]

        self.fields["payment_method"] = forms.ChoiceField(
            choices=choices,
            widget=forms.RadioSelect(
                attrs={
                    "class": "form-check-input",
                }
            ),
            label="Select a payment method",
        )

        # Add option to add new card
        self.fields["use_new_card"] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            label="Use a new card",
        )
