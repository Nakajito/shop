from django import forms


class CouponApplyForm(forms.Form):
    """
    Form to allow users to input and submit a coupon code.

    This form is typically rendered in the shopping cart view. It handles the
    validation of the input string before the view logic checks the database
    for a matching, active Coupon instance.
    """

    code = forms.CharField(
        label="Coupon",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter promo code",
                "class": "form-control",  # Example CSS class for styling
            }
        ),
    )
