import stripe
from django.conf import settings
from django.utils.translation import gettext as _
from payment.models import PaymentMethod
from accounts.models import CustomUser

# Configure Stripe with your secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeCustomerHandler:
    """Manage the creation and updating of clients in Stripe.
    Link users with Stripe clients.
    """

    @staticmethod
    def create_or_get_customer(user: CustomUser):
        """Creates a customer in Stripe if it does not exist, or returns the existing one.

        Args:
            user: CustomUser instance

        Returns:
            Dictionary with {‘id’: stripe_customer_id, ‘created’: bool}

        Args:
            user (CustomUser): _description_
        """

        try:
            # If the user already has a stripe_customer_id, return it.
            if hasattr(user, "stripe_customer_id") and user.stripe_customer_id:
                return {"id": user.stripe_customer_user_id, "created": False}

            # Create a new customer in Stripe
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip(),
                metadata={"user_id": user.id, "username": user.username},
            )

            # Save stripe_customer_id in the user
            user.stripe_customer_id = customer.id
            user.save()

            return {"id": customer.id, "created": True}
        except stripe.error.CardError as e:
            raise Exception(f"Card error: {e.user_message}")
        except stripe.error.RateLimitError as e:
            raise Exception("Too many requests. Please try again later.")
        except stripe.error.InvalidRequestError as e:
            raise Exception(f"Invalid parameters: {str(e)}")
        except stripe.error.AuthenticationError:
            raise Exception("Authentication error")
        except stripe.error.APIConnectionError:
            raise Exception("Connection error")


class StripePaymentMethodHandler:
    """Manage payment methods (cards) in Stripe"""

    @staticmethod
    def attach_payment_method(user: CustomUser, payment_method_id: str):
        """Links a payment method to a Stripe customer.

        Args:
            user: CustomUser instance
            payment_method_id: Stripe payment method ID (pm_xxxxx)

        Returns:
            PaymentMethod object created in DB

        """

        try:
            # Ensure that the user has a client in Stripe
            stripe_customer = StripeCustomerHandler.create_or_get_customer(user)
            stripe_customer_id = stripe_customer["id"]

            # Get details of Stripe's payment method
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)

            # Link card to customer
            stripe.PaymentMethod.attach(payment_method_id, customer=stripe_customer_id)

            # Extract information from the card
            card = payment_method.card

            # Create PaymentMethod in our database
            db_payment_method = PaymentMethod.objects.create(
                user=user,
                stripe_payment_method_id=payment_method_id,
                card_type=card.brand,
                last_four_digits=card.last4,
                card_holder_name=payment_method.billing_details.name
                or user.get_full_name(),
                exp_month=card.exp_month,
                exp_year=card.exp_year,
                is_default=not user.payment_method.exists(),
            )

            return db_payment_method

        except stripe.error.CardError as e:
            raise Exception(f"Card error: {e.user_message}")
        except stripe.error.InvalidRequestError as e:
            raise Exception(f"Invalid payment method: {str(e)}")

    @staticmethod
    def detach_payment_method(payment_method_id: str):
        """
        Disconnect a payment method from Stripe.

        Args:
            payment_method_id: Stripe payment method ID
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)
        except stripe.error.InvalidRequestError:
            # If it is already disconnected or does not exist, there is no problem.
            pass

    @staticmethod
    def delete_payment_method(payment_method: PaymentMethod):
        """
        Deletes a payment method from the database and unlinks it from Stripe.

        Args:
            payment_method: PaymentMethod instance
        """
        # Disconnect from Stripe
        StripePaymentMethodHandler.detach_payment_method(
            payment_method.stripe_payment_method_id
        )

        # Delete it from the database
        payment_method.delete()

    @staticmethod
    def set_default_payment_method(payment_method: PaymentMethod):
        """
        Set a payment method as the default in Stripe.

        Args:
            payment_method: PaymentMethod instance
        """
        try:
            stripe.Customer.modify(
                payment_method.user.stripe_customer_id,
                invoice_settings={
                    "default_payment_method": payment_method.stripe_payment_method_id
                },
            )
            # Also update in our database
            payment_method.is_default = True
            payment_method.save()

        except stripe.error.InvalidRequestError as e:
            raise Exception(f"Error setting default method: {str(e)}")
