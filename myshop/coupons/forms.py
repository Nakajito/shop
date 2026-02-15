from django import forms
from django.utils.translation import gettext_lazy as _


class CouponApplyForm(forms.Form):
    """
    Form to allow users to input and submit a coupon code.

    This form is typically rendered in the shopping cart view. It includes
    input normalization (whitespace stripping) to reduce user errors.
    """

    code = forms.CharField(
        label=_("Coupon"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter promo code"),
                "aria-label": _("Coupon Code"),
            }
        ),
    )

    def clean_code(self):
        """
        Normalize the coupon code by stripping whitespace.
        This prevents ' SUMMER20 ' from failing when 'SUMMER20' is expected.
        """
        code = self.cleaned_data.get("code")
        if code:
            return code.strip()
        return code


class CouponApplyForm(forms.Form):
    code = forms.CharField(
        label=_("Coupon Code"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Enter code")}
        ),
    )
