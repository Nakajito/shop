import stripe
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils.translation import gettext as _

from orders.models import Order
from shop.models import Product
from shop.recommender import Recommender
from .tasks import payment_completed
from orders.tasks import send_order_status_update_email

# Initialize logger for production debugging
logger = logging.getLogger(__name__)


@csrf_exempt
def stripe_webhook(request):
    """
    Webhook endpoint to handle asynchronous events from Stripe.

    Security: Verifies the STRIPE_WEBHOOK_SECRET signature.
    Event: checkout.session.completed
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    # Basic check for signature presence
    if not sig_header:
        logger.error("Stripe Webhook Error: Missing signature header.")
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Stripe Webhook Error: Invalid payload. {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Stripe Webhook Error: Invalid signature. {e}")
        return HttpResponse(status=400)

    # Logic for successful checkout session
    if event.type == "checkout.session.completed":
        session = event.data.object

        if session.mode == "payment" and session.payment_status == "paid":
            try:
                # The client_reference_id corresponds to our local Order ID
                order_id = session.client_reference_id
                order = Order.objects.get(id=order_id)

                # Wrap business logic in an atomic transaction
                with transaction.atomic():
                    # 1. Update Order Payment Details
                    order.paid = True
                    order.stripe_id = session.payment_intent
                    order.save(update_fields=["paid", "stripe_id"])

                    # 2. Update Status & Audit Log
                    order.change_status(
                        "confirmed",
                        user=None,
                        note=_("Payment confirmed via Stripe Checkout."),
                    )

                # 3. Trigger Asynchronous Background Tasks
                try:
                    send_order_status_update_email.delay(order.id, "confirmed")
                    payment_completed.delay(order.id)
                except Exception as e:
                    logger.error(
                        f"Celery task dispatch error for Order {order.id}: {e}"
                    )
                    # Don't fail the webhook — order is already saved as paid

                # 4. Update Recommendation Engine (Redis)
                try:
                    product_ids = order.items.values_list("product_id", flat=True)
                    products = Product.objects.filter(id__in=product_ids)
                    r = Recommender()
                    r.products_bought(products)
                except Exception as e:
                    # Don't fail the whole webhook if recommendation engine fails
                    logger.warning(
                        f"Recommendation Engine Error for Order {order.id}: {e}"
                    )

                logger.info(
                    f"Webhook Success: Order {order.id} processed successfully."
                )

            except Order.DoesNotExist:
                logger.error(
                    f"Stripe Webhook Error: Order {session.client_reference_id} not found."
                )
                return HttpResponse(status=404)
            except Exception as e:
                logger.error(f"Stripe Webhook Business Logic Error: {str(e)}")
                return HttpResponse(status=500)

    return HttpResponse(status=200)
