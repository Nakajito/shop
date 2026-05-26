from django import forms
from django.utils.translation import gettext_lazy as _


class PaymentMethodForm(forms.Form):
    """
    Form to add a payment card using Stripe Elements.

    IMPORTANT: Sensitive data (number, CVC) is captured in JavaScript
    with Stripe Elements, NEVER on the server.
    The server only receives payment_method_id from Stripe.
    """

    cardholder_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Name as it appears on card"),
                "autocomplete": "cc-name",
            }
        ),
        label=_("Cardholder Name"),
    )

    is_default = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Set as default payment method"),
    )


class PaymentMethodSelectionForm(forms.Form):
    """
    Form to select an existing payment method during the checkout process.
    """

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Retrieve active, non-expired payment methods
        payment_methods = user.payment_methods.filter(is_active=True)

        choices = [
            (
                pm.id,
                f"{pm.get_card_type_display()} •••• {pm.last_four_digits} "
                f"({_('Exp')}: {pm.get_expiration_display()})",
            )
            for pm in payment_methods
        ]

        self.fields["payment_method"] = forms.ChoiceField(
            choices=choices,
            required=False,  # Optional if they choose to use a new card instead
            widget=forms.RadioSelect(
                attrs={
                    "class": "form-check-input",
                }
            ),
            label=_("Select a saved card"),
        )

        self.fields["use_new_card"] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "role": "switch",  # Bootstrap 5 switch style
                }
            ),
            label=_("Use a different card"),
        )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")
        use_new_card = cleaned_data.get("use_new_card")

        if not payment_method and not use_new_card:
            raise forms.ValidationError(
                _("Please select a saved card or choose to use a new one.")
            )
        return cleaned_data
