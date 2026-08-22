"""Project-wide middleware (no Django app — plain callables)."""

from django.conf import settings
from django.contrib.auth import get_user
from django.http import Http404


class AdminAccessMiddleware:
    """Hide the admin at ``ADMIN_URL`` from anyone who isn't already an
    authenticated, active staff user (A01/A07 — see SECURITY.md).

    Without this, Django's own admin shows its login form to any anonymous
    visitor who guesses the path — confirming the admin exists there and
    handing out a login screen to brute-force or fingerprint. This 404s the
    entire ``ADMIN_URL`` prefix, including ``.../login/``, before Django's
    admin URLconf ever sees the request.

    This does **not** block legitimate staff access: they authenticate via
    the normal site login (``accounts:login``) first, and once their
    session is staff-authenticated, requests under ``ADMIN_URL`` pass
    straight through to the real admin.

    Placement matters more than it looks: this must sit after
    ``SessionMiddleware`` (``get_user`` needs ``request.session``) but
    *before* ``LocaleMiddleware``. Django's ``LocaleMiddleware`` turns any
    404 on an unprefixed path into a redirect toward the equivalent
    ``/<lang>/...`` path when that one resolves (this project uses
    ``i18n_patterns(prefix_default_language=True)``) — and ``shop``'s
    catch-all product-slug route (``shop/urls.py``: ``<slug:slug>/``)
    matches almost anything, including "admin". Left after
    ``LocaleMiddleware``, our 404 silently turns into a 302 to
    ``/es/admin/`` instead of a clean 404. Sitting before it short-circuits
    the chain before that redirect logic ever runs. Uses
    ``django.contrib.auth.get_user`` directly rather than
    ``request.user`` so it doesn't need to wait for
    ``AuthenticationMiddleware``, which runs much later.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._admin_prefix = "/" + settings.ADMIN_URL

    def __call__(self, request):
        if request.path.startswith(self._admin_prefix):
            user = get_user(request)
            if not (user.is_authenticated and user.is_active and user.is_staff):
                raise Http404
        return self.get_response(request)
