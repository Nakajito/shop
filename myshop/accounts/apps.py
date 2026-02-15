from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    """
    Configuration class for the 'accounts' application.

    This class sets up application-specific configurations, such as the
    default auto-incrementing field type and the human-readable name
    displayed in the Django Admin interface.

    It also overrides the `ready()` method to ensure signal handlers are
    imported and registered when the application starts up.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    # Best Practice: Use gettext_lazy for the verbose_name.
    # This allows the app name "Account Management" to be translated
    # automatically based on the user's browser language settings if configured.
    verbose_name = _("Account Management")

    def ready(self):
        """
        Perform initialization tasks when the application is ready.

        This method imports the signals module to ensure that signal receivers
        (like creating a Profile when a User is created) are connected
        before any operations occur.
        """
        try:
            import accounts.signals
        except ImportError:
            # Log a warning if signals cannot be imported, or pass if
            # no signals exist yet.
            pass
