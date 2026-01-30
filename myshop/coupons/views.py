from django.shortcuts import redirect
from django.utils import timezone
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

    If valid, the coupon's ID is stored in the user's session. If invalid,
    any existing coupon in the session is cleared.

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
            coupon = Coupon.objects.get(
                code__iexact=code, valid_from__lte=now, valid_to__gte=now, active=True
            )
            request.session["coupon_id"] = coupon.id
        except Coupon.DoesNotExist:
            request.session["coupon_id"] = None

    return redirect("cart:cart_detail")
