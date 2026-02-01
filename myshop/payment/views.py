from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from orders.models import Order
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import JsonResponse
from decouple import config
import stripe
from payment.stripe_handler import StripePaymentMethodHandler
import json
import logging
from payment.models import PaymentMethod
from payment.forms import PaymentMethodForm


logger = logging.getLogger(__name__)


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


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def payment_method_list(request):
    """
    View to list all user payment methods.
    GET: Shows all cards
    """

    payment_methods = request.user.payment_methods.filter(is_active=True).order_by(
        "-is_default", "-created_at"
    )

    context = {
        "payment_methods": payment_methods,
        "page_title": "My Payment Methods",
        "total_payment_methods": payment_methods.count(),
    }

    return render(request, "payment/payment_methods/list.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def payment_method_add(request):
    """
    View to add a new payment card.
    GET: Displays form with Stripe Elements
    POST: Processes Stripe token and creates payment method
    """

    if request.method == "POST":
        form = PaymentMethodForm(request.POST)
        payment_method_id = request.POST.get("payment_method_id")

        if form.is_valid() and payment_method_id:
            try:
                with transaction.atomic():
                    # Add card to Stripe and create record in database
                    db_payment_method = (
                        StripePaymentMethodHandler.attach_payment_method(
                            request.user, payment_method_id
                        )
                    )

                    messages.success(
                        request,
                        f"Card {db_payment_method.get_masked_card()} successfully added.",
                    )

                    # Redirect to the next page if coming from checkout
                    next_url = request.GET.get("next")
                    if next_url:
                        return redirect(next_url)

                    return redirect("payment:payment_method_list")

            except Exception as e:
                logger.error(f"Error adding payment method: {str(e)}")
                messages.error(request, f"Error adding card: {str(e)}")

        else:
            if not payment_method_id:
                messages.error(request, "Please enter your card details.")
            else:
                messages.error(request, "Please review the information on the form.")

    else:
        form = PaymentMethodForm()

    # Get Stripe public key for Stripe Elements
    # stripe_public_key = settings.STRIPE_PUBLISHABLE_KEY
    stripe_public_key = config("STRIPE_PUBLISHABLE_KEY")

    context = {
        "form": form,
        "page_title": "Add New Card",
        "stripe_public_key": stripe_public_key,
    }

    return render(request, "payment/payment_methods/add.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def payment_method_delete(request, payment_method_id):
    """
    View to delete payment card.
    GET: Display confirmation
    POST: Delete card
    """

    payment_method = get_object_or_404(
        PaymentMethod, id=payment_method_id, user=request.user
    )

    if request.method == "POST":
        try:
            payment_method_info = payment_method.get_masked_card()

            with transaction.atomic():
                StripePaymentMethodHandler.delete_payment_method(payment_method)

            messages.success(
                request, f"Card {payment_method_info} successfully deleted."
            )

            return redirect("payment:payment_method_list")

        except Exception as e:
            logger.error(f"Error deleting payment method: {str(e)}")
            messages.error(request, f"Error deleting card: {str(e)}")

    context = {
        "payment_method": payment_method,
        "page_title": "Delete Payment Method",
    }

    return render(request, "payment/payment_methods/confirm_delete.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def payment_method_set_default(request, payment_method_id):
    """
    View to set card as default.
    POST only for security.
    """

    payment_method = get_object_or_404(
        PaymentMethod, id=payment_method_id, user=request.user
    )

    try:
        with transaction.atomic():
            StripePaymentMethodHandler.set_default_payment_method(payment_method)

        messages.success(
            request, f"Card {payment_method.get_masked_card()} set as default."
        )

    except Exception as e:
        logger.error(f"Error setting default method: {str(e)}")
        messages.error(request, f"Error: {str(e)}")

    # Redirect to source or method list
    next_url = request.GET.get("next")
    return redirect(next_url if next_url else "payment:payment_method_list")


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def create_payment_intent(request):
    """
    AJAX view to create a Stripe PaymentIntent.
    Used by Stripe Elements to process payments.

    POST: JSON with amount
    Returns: JSON with clientSecret
    """

    try:
        data = json.loads(request.body)
        amount = data.get("amount")

        if not amount or amount <= 0:
            return JsonResponse({"error": "Invalid amount"}, status=400)

        # Ensure that the user has a Stripe account
        from payment.stripe_handler import StripeCustomerHandler

        stripe_customer = StripeCustomerHandler.create_or_get_customer(request.user)

        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="mxn",
            customer=stripe_customer["id"],
            automatic_payment_methods={
                "enabled": True,
            },
        )

        return JsonResponse(
            {
                "clientSecret": intent.client_secret,
                "intentId": intent.id,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return JsonResponse({"error": f"Stripe error {str(e)}"}, status=400)
    except Exception as e:
        logger.error(f"Error creating PaymentIntent: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def confirm_payment(request):
    """
    AJAX view to confirm payment after Stripe 3D Secure.
    POST: JSON with paymentIntentId
    Returns: JSON with status
    """

    try:
        data = json.loads(request.body)
        intent_id = data.get("paymentIntentId")

        if not intent_id:
            return JsonResponse({"error": "PaymentIntent ID required"}, status=400)

        # Retrieve the intent to verify status
        intent = stripe.PaymentIntent.retrieve(intent_id)

        if intent.status == "succeeded":
            return JsonResponse(
                {"success": True, "message": "Payment successfully completed"}
            )
        elif intent.status == "requires_action":
            return JsonResponse(
                {
                    "success": False,
                    "message": "Additional authentication is required.",
                    "requiresAction": True,
                }
            )
        else:
            return JsonResponse(
                {"success": False, "message": f"Payment status: {intent.status}"}
            )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return JsonResponse({"error": f"Stripe error: {str(e)}"}, status=400)
    except Exception as e:
        logger.error(f"Error confirming payment: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)
