from django.apps import AppConfig


class CartConfig(AppConfig):
    """
    Configuration class for the 'cart' application.

    This class defines application-specific settings for the shopping cart
    module, including the default primary key type and the readable name
    displayed in the Django Admin interface.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "cart"
    verbose_name = "Shopping Cart"
