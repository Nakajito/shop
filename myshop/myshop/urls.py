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
    Media is served by Django ONLY when DEBUG=True. In production, an
    upstream proxy (nginx/Caddy) or WhiteNoise must serve MEDIA_ROOT.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Custom accounts URLs first so they take precedence over allauth defaults
    path("accounts/", include("accounts.urls")),
    # Allauth URLs (without namespace) for social auth provider routes
    path("accounts/", include("allauth.urls")),
    path("cart/", include("cart.urls", namespace="cart")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("payment/", include("payment.urls", namespace="payment")),
    path("coupons/", include("coupons.urls", namespace="coupons")),
    path("support/", include("support.urls", namespace="support")),
    path("blog/", include("blog.urls", namespace="blog")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    # The 'shop' app handles the root URL, so it is included last to allow
    # other specific patterns to be matched first.
    path("", include("shop.urls", namespace="shop")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
