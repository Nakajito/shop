from decimal import Decimal
import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from orders.models import Order

# Configure the Stripe library with settings
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION


def payment_process(request):
    """
    View to initiate the Stripe checkout process.

    This view performs the following actions:
    1. Retrieves the current order from the session.
    2. On POST request (user clicking "Pay"):
       - Constructs the success and cancel URLs.
       - Iterates over order items to format them for the Stripe API (converting
         price to the smallest currency unit, e.g., cents/centavos).
       - Checks for an associated coupon; if present, creates a temporary Stripe
         coupon and attaches it to the session.
       - Creates the Stripe Checkout Session.
       - Redirects the user to the Stripe-hosted payment page.
    3. On GET request:
       - Renders a confirmation page ('payment/process.html') allowing the user
         to review details before proceeding to Stripe.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: Renders the process template or redirects to Stripe.
    """
    order_id = request.session.get("order_id")
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        success_url = request.build_absolute_uri(reverse("payment:completed"))
        cancel_url = request.build_absolute_uri(reverse("payment:canceled"))

        # Initialize Stripe checkout session data
        session_data = {
            "mode": "payment",
            "client_reference_id": order.id,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": [],
        }

        # Populate line items
        for item in order.items.all():
            session_data["line_items"].append(
                {
                    "price_data": {
                        # Stripe expects amounts in the smallest currency unit (e.g., cents)
                        "unit_amount": int(item.price * Decimal("100")),
                        "currency": "mxn",  # Mexican Peso
                        "product_data": {
                            "name": item.product.name,
                        },
                    },
                    "quantity": item.quantity,
                }
            )

        # Apply discount if a coupon exists on the order
        if order.coupon:
            stripe_coupon = stripe.Coupon.create(
                name=order.coupon.code, percent_off=order.discount, duration="once"
            )
            session_data["discounts"] = [{"coupon": stripe_coupon.id}]

        # Create the Stripe checkout session
        session = stripe.checkout.Session.create(**session_data)

        # Redirect the user to the Stripe payment form
        return redirect(session.url, code=303)

    else:
        return render(request, "payment/process.html", locals())


def payment_completed(request):
    """
    View to display the 'Payment Successful' page.
    """
    return render(request, "payment/completed.html")


def payment_canceled(request):
    """
    View to display the 'Payment Canceled' page.
    """
    return render(request, "payment/canceled.html")
