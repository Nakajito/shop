from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Create or update Site and Google SocialApp for local development (allauth). "
        "Alternative to setting GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET in .env — don't "
        "use both, since allauth will see two apps for the same provider and raise "
        "MultipleObjectsReturned."
    )

    def add_arguments(self, parser):
        parser.add_argument("--client-id", dest="client_id", required=True)
        parser.add_argument("--secret", dest="secret", required=True)
        parser.add_argument("--site-domain", dest="site_domain", default="127.0.0.1:8000")
        parser.add_argument("--site-name", dest="site_name", default="Local")
        parser.add_argument("--site-id", dest="site_id", type=int, default=1)

    def handle(self, *args, **options):
        client_id = options["client_id"]
        secret = options["secret"]
        site_domain = options["site_domain"]
        site_name = options["site_name"]
        site_id = options["site_id"]

        # Import here to avoid import-time dependency on Django setup
        from django.contrib.sites.models import Site

        try:
            from allauth.socialaccount.models import SocialApp
        except Exception:
            self.stderr.write(
                "Error importing allauth SocialApp. Is django-allauth installed and migrated?"
            )
            raise

        site, created = Site.objects.update_or_create(
            pk=site_id, defaults={"domain": site_domain, "name": site_name}
        )

        if created:
            self.stdout.write(f"Created Site id={site.pk} domain={site.domain}")
        else:
            self.stdout.write(f"Updated Site id={site.pk} domain={site.domain}")

        socialapp, created = SocialApp.objects.update_or_create(
            provider="google",
            defaults={"name": "Google", "client_id": client_id, "secret": secret},
        )

        # Associate with the site
        socialapp.sites.set([site])
        socialapp.save()

        if created:
            self.stdout.write("Created/updated SocialApp for provider 'google'.")
        else:
            self.stdout.write("Updated SocialApp for provider 'google'.")

        self.stdout.write("Done. Make sure your Google Cloud redirect URIs include (both")
        self.stdout.write("locales — accounts/ is inside i18n_patterns):")
        self.stdout.write(f"  http://{site_domain}/es/accounts/google/login/callback/")
        self.stdout.write(f"  http://{site_domain}/en/accounts/google/login/callback/")
