"""Project-wide utility helpers (no Django app — pure functions)."""

from django.utils.http import url_has_allowed_host_and_scheme


def safe_next_url(request, fallback):
    """Return ``?next=`` (or ``next`` POST field) only if same-host + scheme.

    Prevents open-redirect via attacker-controlled ``next=https://evil/...``.
    Falls back to ``fallback`` (any value accepted by ``django.shortcuts.redirect``)
    when the supplied URL is missing or not allowed.
    """
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback
