import json
import logging
import stripe
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from decouple import config
from orders.models import Order
from payment.forms import PaymentMethodForm
from payment.models import PaymentMethod
from payment.services import PaymentService
from payment.stripe_handler import StripePaymentMethodHandler, StripeCustomerHandler

# Initialize logger
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION


def payment_process(request):
    """
    Initiates the Stripe Checkout process for an existing Order.
    """
    order_id = request.session.get("order_id")
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        success_url = request.build_absolute_uri(reverse("payment:completed"))
        cancel_url = request.build_absolute_uri(reverse("payment:canceled"))

        try:
            session = PaymentService.create_checkout_session(
                order, success_url, cancel_url
            )
            return redirect(session.url, code=303)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Session Error for Order {order.id}: {e}")
            messages.error(request, _("Payment gateway is currently unavailable."))
            return redirect("payment:process")

    return render(request, "payment/process.html", {"order": order})


def payment_completed(request):
    return render(
        request, "payment/completed.html", {"page_title": _("Payment Successful")}
    )


def payment_canceled(request):
    return render(
        request, "payment/canceled.html", {"page_title": _("Payment Cancelled")}
    )


# --- PAYMENT METHOD MANAGEMENT (VAULTING) ---


@login_required
def payment_method_list(request):
    """Lists saved active payment methods for the user."""
    payment_methods = request.user.payment_methods.filter(is_active=True)
    return render(
        request,
        "payment/payment_methods/list.html",
        {"payment_methods": payment_methods, "page_title": _("My Payment Methods")},
    )


@login_required
@require_http_methods(["GET", "POST"])
def payment_method_add(request):
    """Vaults a new card using Stripe Elements payment_method_id."""
    if request.method == "POST":
        form = PaymentMethodForm(request.POST)
        payment_method_id = request.POST.get("payment_method_id")

        if form.is_valid() and payment_method_id:
            try:
                with transaction.atomic():
                    db_method = StripePaymentMethodHandler.attach_payment_method(
                        request.user, payment_method_id
                    )
                    messages.success(
                        request,
                        _("Card {} added successfully.").format(
                            db_method.get_masked_card()
                        ),
                    )

                    next_url = request.GET.get("next")
                    return redirect(
                        next_url if next_url else "payment:payment_method_list"
                    )
            except Exception as e:
                logger.error(f"Error vaulting card for User {request.user.id}: {e}")
                messages.error(request, str(e))
        else:
            messages.error(request, _("Please provide valid card details."))

    form = PaymentMethodForm()
    return render(
        request,
        "payment/payment_methods/add.html",
        {
            "form": form,
            "stripe_public_key": settings.STRIPE_PUBLISHABLE_KEY,
            "page_title": _("Add New Card"),
        },
    )


@require_POST
@login_required
def payment_method_delete(request, payment_method_id):
    """Deletes a saved card from both DB and Stripe."""
    method = get_object_or_404(PaymentMethod, id=payment_method_id, user=request.user)
    try:
        with transaction.atomic():
            StripePaymentMethodHandler.delete_payment_method(method)
            messages.success(request, _("Payment method removed."))
    except Exception as e:
        logger.error(f"Error deleting PM {payment_method_id}: {e}")
        messages.error(request, _("Could not delete card. Please contact support."))

    return redirect("payment:payment_method_list")


@require_POST
@login_required
def payment_method_set_default(request, payment_method_id):
    """Sets a vaulted card as the primary choice."""
    method = get_object_or_404(PaymentMethod, id=payment_method_id, user=request.user)
    try:
        StripePaymentMethodHandler.set_default_payment_method(method)
        messages.success(request, _("Default payment method updated."))
    except Exception as e:
        messages.error(request, str(e))

    return redirect("payment:payment_method_list")


# --- AJAX API ENDPOINTS ---


@require_POST
@login_required
def create_payment_intent(request):
    """AJAX endpoint to generate a PaymentIntent client secret."""
    try:
        data = json.loads(request.body)
        amount = data.get("amount")

        if not amount or amount <= 0:
            return JsonResponse({"error": _("Invalid amount")}, status=400)

        # Sync user with Stripe
        stripe_customer = StripeCustomerHandler.create_or_get_customer(request.user)

        intent = stripe.PaymentIntent.create(
            amount=int(amount),
            currency="mxn",
            customer=stripe_customer["id"],
            automatic_payment_methods={"enabled": True},
        )

        return JsonResponse(
            {
                "clientSecret": intent.client_secret,
                "intentId": intent.id,
            }
        )

    except (json.JSONDecodeError, stripe.error.StripeError) as e:
        logger.error(f"Payment Intent API Error: {e}")
        return JsonResponse({"error": str(e)}, status=400)


@require_POST
@login_required
def confirm_payment(request):
    """AJAX endpoint to verify PaymentIntent status after frontend processing."""
    try:
        data = json.loads(request.body)
        intent_id = data.get("paymentIntentId")

        if not intent_id:
            return JsonResponse({"error": _("Missing PaymentIntent ID")}, status=400)

        intent = stripe.PaymentIntent.retrieve(intent_id)

        if intent.status == "succeeded":
            return JsonResponse({"success": True, "message": _("Payment successful")})

        return JsonResponse(
            {
                "success": False,
                "status": intent.status,
                "requiresAction": intent.status == "requires_action",
            }
        )

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)
