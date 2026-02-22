from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Configuration class for the 'orders' application.

    This class manages metadata and configuration settings for the order
    processing system, including the default primary key type and the
    application name displayed in the Django Admin.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"
    verbose_name = "Order Management"

    def ready(self):
        import orders.signals  # noqa: F401
