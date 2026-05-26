from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import CouponApplyForm
from .models import Coupon


@require_POST
def coupon_apply(request):
    """
    View to process coupon code application.

    This view accepts a POST request containing a coupon code. It validates the code
    against the database by checking:
    1. Case-insensitive code match (`code__iexact`).
    2. Current time matches the validity window (`valid_from` <= now <= `valid_to`).
    3. The coupon is explicitly marked as `active`.

    It provides immediate feedback to the user via Django messages.

    Args:
        request (HttpRequest): The incoming POST request.

    Returns:
        HttpResponseRedirect: Redirects back to the cart detail page.
    """
    now = timezone.now()
    form = CouponApplyForm(request.POST)

    if form.is_valid():
        code = form.cleaned_data["code"]
        try:
            # Check for a valid, active coupon within the date range
            coupon = Coupon.objects.get(
                code__iexact=code, valid_from__lte=now, valid_to__gte=now, active=True
            )
            request.session["coupon_id"] = coupon.id
            messages.success(request, _("Coupon applied successfully."))

        except Coupon.DoesNotExist:
            # Clear any previously applied coupon if the new one is invalid
            request.session["coupon_id"] = None
            messages.error(request, _("This coupon is invalid, expired, or inactive."))

    return redirect("cart:cart_detail")
