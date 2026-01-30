from django.apps import AppConfig


class CouponsConfig(AppConfig):
    """
    Configuration class for the 'coupons' application.

    This class manages metadata and configuration settings for the coupon
    management system, including the default primary key type and the
    application name displayed in the Django Admin.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "coupons"
    verbose_name = "Coupons & Promotions"
