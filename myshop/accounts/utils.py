from django.conf import settings


def is_google_oauth_configured():
    """Whether a Google login attempt can complete a real OAuth handshake.

    True if either the env-var-based settings APP or a DB SocialApp exists
    for provider "google" -- the two mutually exclusive sources documented in
    accounts/management/commands/setup_google_oauth.py (using both raises
    MultipleObjectsReturned, see accounts/checks.py). GOOGLE_CLIENT_ID/SECRET
    are allowed to be blank to disable Google login (see .env.example); used
    to hide the "Continuar con Google" button instead of sending users into
    Google's "Missing required parameter: client_id" error.
    """
    app_cfg = settings.SOCIALACCOUNT_PROVIDERS.get("google", {}).get("APP", {})
    if app_cfg.get("client_id") and app_cfg.get("secret"):
        return True

    try:
        from allauth.socialaccount.models import SocialApp

        return SocialApp.objects.filter(provider="google").exists()
    except Exception:
        return False
