import logging
from decimal import Decimal

import stripe
from django.conf import settings

from payment.stripe_handler import StripeCustomerHandler, StripePaymentMethodHandler

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION


class PaymentService:
    @staticmethod
    def create_checkout_session(order, success_url, cancel_url):
        """Create a Stripe Checkout Session for the given order."""
        session_data = {
            "mode": "payment",
            "client_reference_id": order.id,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": [],
        }

        for item in order.items.select_related("product").all():
            session_data["line_items"].append(
                {
                    "price_data": {
                        "unit_amount": int(item.price * Decimal("100")),
                        "currency": "mxn",
                        "product_data": {
                            "name": item.product.name,
                        },
                    },
                    "quantity": item.quantity,
                }
            )

        if order.coupon:
            stripe_coupon = stripe.Coupon.create(
                name=order.coupon.code,
                percent_off=order.discount,
                duration="once",
            )
            session_data["discounts"] = [{"coupon": stripe_coupon.id}]

        session = stripe.checkout.Session.create(**session_data)
        return session

    @staticmethod
    def process_successful_payment(order):
        """Mark order as paid after successful payment."""
        order.paid = True
        order.save(update_fields=["paid"])

    @staticmethod
    def add_payment_method(user, payment_method_id):
        """Vault a new payment method for a user."""
        return StripePaymentMethodHandler.attach_payment_method(user, payment_method_id)

    @staticmethod
    def create_payment_intent(user, amount, currency="mxn"):
        """Create a Stripe PaymentIntent."""
        stripe_customer = StripeCustomerHandler.create_or_get_customer(user)

        intent = stripe.PaymentIntent.create(
            amount=int(amount),
            currency=currency,
            customer=stripe_customer["id"],
            automatic_payment_methods={"enabled": True},
            metadata={"user_id": str(user.id)},
        )

        return intent
