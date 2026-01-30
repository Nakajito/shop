from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration class for the 'accounts' application.

    This class defines application-specific settings, including the default
    primary key field type and the verbose name for the admin interface.
    It also overrides the ready() method to import and register signal
    handlers when the application starts.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Gestión de Cuentas"

    def ready(self):
        import accounts.signals
