from django import forms
from django.utils.translation import gettext_lazy as _

# Generate a list of tuples for quantity selection (1 to 20)
# Format: [(1, '1'), (2, '2'), ..., (20, '20')]
PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]


class CartAddProductForm(forms.Form):
    """
    Form for adding products to the cart or updating existing quantities.

    Attributes:
        quantity (TypedChoiceField): A drop-down menu allowing users to select
            a quantity between 1 and 20. The input is coerced to an integer.
        override (BooleanField): A hidden field that determines the update behavior.
            - If False (default): The quantity is added to the existing cart item.
            - If True: The quantity replaces the existing cart item's quantity.
    """

    quantity = forms.TypedChoiceField(
        choices=PRODUCT_QUANTITY_CHOICES,
        coerce=int,
        label=_("Quantity"),
        widget=forms.Select(attrs={"class": "form-select quantity-select"}),  # Bootstrap 5 styling
    )

    override = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput
    )
