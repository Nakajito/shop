"""Main URL configuration for the 'myshop' project.

Central routing hub. Delegates requests to per-app URLconfs by path prefix.

Mounted apps:
    - admin/        Django admin
    - accounts/     custom accounts urls + allauth (social/email auth)
    - cart/         shopping cart
    - orders/       order creation/history
    - payment/      Stripe checkout + webhooks
    - coupons/      discount codes
    - support/      support tickets
    - blog/         CKEditor-5 powered blog
    - ckeditor5/    CKEditor uploader
    - /             shop catalog (root)
    - 502/          explicit Bad Gateway (maintenance / proxy fallback)
    - maintenance/  maintenance-mode page (503)
    - healthz/      container liveness/readiness probe (200)
    - csp-report/   CSP violation report sink (report-uri directive)

Static & media:
    Media files served by Django via static() helper in all environments.
    For high-traffic production, consider placing an upstream proxy
    (nginx/Caddy) in front of MEDIA_ROOT, or using cloud storage.

Error handlers:
    Custom branded pages for all standard HTTP errors + a 502 endpoint
    that the reverse proxy can rewrite to when the upstream is unhealthy.
    See myshop/views.py for implementation.
"""

import re

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_control
from django.views.static import serve

from payment import webhooks as payment_webhooks

from . import views as myshop_views

# ── Custom error handlers ────────────────────────────────────────
handler400 = "myshop.views.bad_request"
handler403 = "myshop.views.permission_denied"
handler404 = "myshop.views.page_not_found"
handler500 = "myshop.views.server_error"

# MFA gate for /admin/ (A07, see SECURITY.md and MFA_ENFORCE_STAFF in
# settings/base.py). django-otp's OTPAdminSite has no bypass for staff with
# zero enrolled devices, so this only activates once the flag is flipped on.
if settings.MFA_ENFORCE_STAFF:
    from django_otp.admin import OTPAdminSite

    admin.site.__class__ = OTPAdminSite

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # Stripe webhook must stay outside i18n_patterns — Stripe POSTs to a fixed URL
    path(
        "payment/webhook/",
        payment_webhooks.stripe_webhook,
        name="stripe-webhook",
    ),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    # Explicit 502 for proxy fallback / maintenance rewrites (outside i18n)
    path("502/", myshop_views.bad_gateway, name="bad_gateway"),
    path("maintenance/", myshop_views.maintenance, name="maintenance"),
    # Container liveness/readiness probe (outside i18n — no redirect games)
    path("healthz/", myshop_views.healthz, name="healthz"),
    # CSP violation reports (report-uri directive, settings/base.py) — fixed
    # path so it works regardless of active language.
    path("csp-report/", myshop_views.csp_report, name="csp_report"),
]

urlpatterns += i18n_patterns(
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
    path("cart/", include("cart.urls", namespace="cart")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("payment/", include("payment.urls", namespace="payment")),
    path("coupons/", include("coupons.urls", namespace="coupons")),
    path("support/", include("support.urls", namespace="support")),
    path("blog/", include("blog.urls", namespace="blog")),
    path("502/", myshop_views.bad_gateway, name="bad_gateway_i18n"),
    path("maintenance/", myshop_views.maintenance, name="maintenance_i18n"),
    path("", include("shop.urls", namespace="shop")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # 1-year immutable cache: uploads never overwrite an existing filename
    # (Storage.get_available_name() suffixes on collision), so a given
    # /media/ URL's content never changes underneath it.
    cached_serve = cache_control(max_age=31536000, public=True, immutable=True)(serve)
    urlpatterns += [
        re_path(
            rf"^{re.escape(settings.MEDIA_URL.lstrip('/'))}(?P<path>.*)$",
            cached_serve,
            kwargs={"document_root": settings.MEDIA_ROOT},
        ),
    ]
