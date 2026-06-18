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

Static & media:
    Media files served by Django via static() helper in all environments.
    For high-traffic production, consider placing an upstream proxy
    (nginx/Caddy) in front of MEDIA_ROOT, or using cloud storage.
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from payment import webhooks as payment_webhooks

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # Stripe webhook must stay outside i18n_patterns — Stripe POSTs to a fixed URL
    path(
        "payment/webhook/",
        payment_webhooks.stripe_webhook,
        name="stripe-webhook",
    ),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
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
    path("", include("shop.urls", namespace="shop")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(settings.MEDIA_URL.lstrip("/")),
            serve,
            kwargs={"document_root": settings.MEDIA_ROOT},
        ),
    ]
