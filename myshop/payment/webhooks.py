import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from shop.models import Product
from shop.recommender import Recommender
from .tasks import payment_completed


@csrf_exempt
def stripe_webhook(request):
    """
    Webhook endpoint to handle asynchronous events from Stripe.

    This view handles the 'checkout.session.completed' event. It performs
    the following security and logic steps:
    1. Verifies the request signature using the STRIPE_WEBHOOK_SECRET to ensure
       the request actually came from Stripe.
    2. Retrieves the Order based on the 'client_reference_id' passed to Stripe
       during session creation.
    3. Marks the order as paid and stores the Stripe Payment Intent ID.
    4. Updates the product recommendation engine with the purchased items.
    5. Triggers the asynchronous email confirmation task.

    Args:
        request (HttpRequest): The incoming POST request from Stripe.

    Returns:
        HttpResponse: 200 OK on success, 400 on invalid payload/signature,
        or 404 if the order is missing.
    """
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    if event.type == "checkout.session.completed":
        session = event.data.object

        if session.mode == "payment" and session.payment_status == "paid":
            try:
                # The client_reference_id corresponds to our Order ID
                order = Order.objects.get(id=session.client_reference_id)
            except Order.DoesNotExist:
                return HttpResponse(status=404)

            # Mark order as paid
            order.paid = True

            # Store the Stripe PaymentIntent ID (useful for refunds/audits)
            order.stripe_id = session.payment_intent
            order.save()

            # Update the recommendation engine with the items purchased together
            product_ids = order.items.values_list("product_id", flat=True)
            products = Product.objects.filter(id__in=product_ids)

            r = Recommender()
            r.products_bought(products)

            # Launch asynchronous task to send the invoice email
            payment_completed.delay(order.id)

    return HttpResponse(status=200)
