from django import forms
from django.utils.translation import gettext_lazy as _


class CartAddProductForm(forms.Form):
    """
    Form for adding products to the cart or updating existing quantities.

    Attributes:
        quantity (IntegerField): A hidden input holding the selected quantity (1-20).
            Controlled by +/- buttons in the template.
        override (BooleanField): A hidden field that determines the update behavior.
            - If False (default): The quantity is added to the existing cart item.
            - If True: The quantity replaces the existing cart item's quantity.
    """

    quantity = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        label=_("Quantity"),
        widget=forms.HiddenInput(attrs={"class": "quantity-input"}),
    )

    override = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput
    )
