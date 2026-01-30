from django.apps import AppConfig


class PaymentConfig(AppConfig):
    """
    Configuration class for the 'payment' application.

    This class manages metadata and configuration settings for the payment
    processing module, which handles integration with external gateways
    like Stripe.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "payment"
    verbose_name = "Payment Management"
