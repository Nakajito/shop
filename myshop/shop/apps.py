from django.apps import AppConfig


class ShopConfig(AppConfig):
    """
    Configuration class for the 'shop' application.

    This class manages the metadata and configuration for the core product
    catalog, including the default primary key type.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "shop"
    verbose_name = "Shop"
