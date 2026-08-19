from django.conf import settings
from django.core.checks import Error, register


@register()
def check_google_oauth_single_source(app_configs, **kwargs):
    """Google OAuth must be configured via env vars OR a DB SocialApp, never both.

    allauth's list_apps() merges the settings-based APP with any DB-stored
    SocialApp for the same provider instead of one overriding the other. If
    both exist, get_app() sees two apps and raises MultipleObjectsReturned,
    which 500s the login page (see accounts/management/commands/setup_google_oauth.py).
    """
    app_cfg = settings.SOCIALACCOUNT_PROVIDERS.get("google", {}).get("APP", {})
    if not (app_cfg.get("client_id") and app_cfg.get("secret")):
        return []

    try:
        from allauth.socialaccount.models import SocialApp

        db_app_exists = SocialApp.objects.filter(provider="google").exists()
    except Exception:
        # DB not migrated/reachable yet (e.g. `manage.py check` runs before
        # migrate in CI) -- nothing to conflict with, so don't fail the check.
        return []

    if not db_app_exists:
        return []

    return [
        Error(
            "GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET are set AND a DB SocialApp "
            "row exists for provider 'google'.",
            hint=(
                "Pick one source. To keep the env-var config, delete the DB row: "
                "python manage.py shell -c \"from allauth.socialaccount.models "
                "import SocialApp; SocialApp.objects.filter(provider='google').delete()\""
            ),
            id="accounts.E001",
        )
    ]
