import logging

import stripe
from decouple import config
from django.conf import settings
from django.utils.translation import gettext as _

from accounts.models import CustomUser
from payment.models import PaymentMethod

# Initialize logger
logger = logging.getLogger(__name__)

# SECURITY FIX: Use STRIPE_SECRET_KEY for server-side API calls
stripe.api_key = config("STRIPE_SECRET_KEY")


class StripeCustomerHandler:
    """
    Manages Stripe Customer objects and links them to CustomUser instances.
    """

    @staticmethod
    def create_or_get_customer(user: CustomUser):
        """
        Retrieves an existing Stripe customer ID or creates a new one.

        Returns:
            dict: {'id': str, 'created': bool}
        """
        try:
            # Return existing ID if already present on the user model
            if user.stripe_customer_id:
                return {"id": user.stripe_customer_id, "created": False}

            # Create a new customer in Stripe
            customer = stripe.Customer.create(
                email=user.email,
                name=user.get_full_name() or user.username,
                metadata={
                    "user_id": user.id,
                    "env": "production" if not settings.DEBUG else "development",
                },
            )

            # Sync local database
            user.stripe_customer_id = customer.id
            user.save(update_fields=["stripe_customer_id"])

            logger.info(f"Created Stripe customer for User {user.id}: {customer.id}")
            return {"id": customer.id, "created": True}

        except stripe.error.StripeError as e:
            logger.error(f"Stripe Customer Error for User {user.id}: {str(e)}")
            raise Exception(
                _("Could not verify customer identity with payment provider.")
            ) from e


class StripePaymentMethodHandler:
    """
    Handles logic for attaching, detaching, and defaulting cards via Stripe.
    """

    @staticmethod
    def attach_payment_method(user: CustomUser, payment_method_id: str):
        """
        Links a Stripe PaymentMethod (pm_...) to a Customer and saves it locally.
        """
        try:
            # 1. Ensure user has a Stripe Customer profile
            stripe_customer = StripeCustomerHandler.create_or_get_customer(user)
            customer_id = stripe_customer["id"]

            # 2. Retrieve method details from Stripe to verify validity
            stripe_pm = stripe.PaymentMethod.retrieve(payment_method_id)

            # 3. Attach to customer (if not already attached)
            if not stripe_pm.customer:
                stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)

            # 4. Extract card metadata
            card = stripe_pm.card
            # Default logic: if it's the first active card, make it default
            is_first = not PaymentMethod.objects.filter(
                user=user, is_active=True
            ).exists()

            # 5. Create local record
            db_method = PaymentMethod.objects.create(
                user=user,
                stripe_payment_method_id=payment_method_id,
                card_type=card.brand,
                last_four_digits=card.last4,
                card_holder_name=stripe_pm.billing_details.name or user.get_full_name(),
                exp_month=card.exp_month,
                exp_year=card.exp_year,
                is_default=is_first,
            )

            logger.info(f"Attached PM {payment_method_id} to User {user.id}")
            return db_method

        except stripe.error.CardError as e:
            raise Exception(e.user_message) from e
        except stripe.error.StripeError as e:
            logger.error(f"Stripe PM Error: {str(e)}")
            raise Exception(
                _("Failed to link payment method. Please try again.")
            ) from e

    @staticmethod
    def detach_payment_method(payment_method_id: str):
        """
        Safely disconnects a card from Stripe.
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)
        except stripe.error.InvalidRequestError:
            # Card might already be detached or deleted on Stripe dashboard
            pass

    @staticmethod
    def delete_payment_method(payment_method: PaymentMethod):
        """
        Removes card from Stripe and deletes local database record.
        """
        StripePaymentMethodHandler.detach_payment_method(
            payment_method.stripe_payment_method_id
        )
        payment_method.delete()

    @staticmethod
    def set_default_payment_method(payment_method: PaymentMethod):
        """
        Updates the Stripe Customer's default payment method settings.
        """
        if not payment_method.user.stripe_customer_id:
            StripeCustomerHandler.create_or_get_customer(payment_method.user)

        try:
            stripe.Customer.modify(
                payment_method.user.stripe_customer_id,
                invoice_settings={
                    "default_payment_method": payment_method.stripe_payment_method_id
                },
            )
            # update local DB
            payment_method.is_default = True
            payment_method.save()

            logger.info(
                f"Default PM updated to {payment_method.id} for User {payment_method.user.id}"
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Default Update Error: {str(e)}")
            raise Exception(
                _("Could not update default payment method.")
            ) from e
