from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

"""
Main URL configuration for the 'myshop' project.

This module acts as the central routing hub, delegating requests to specific
application URL configurations based on the path prefix.

Included Apps:
    - admin/: Django administrative interface.
    - cart/: Shopping cart management (add/remove/view).
    - orders/: Order creation and history.
    - payment/: Payment gateway integration.
    - coupons/: Discount code application.
    - /: The core shop application (product catalog), handling the root URL.

Static & Media Files:
    In DEBUG mode, this configuration also serves user-uploaded media files
    directly from the MEDIA_ROOT directory.
"""

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    # Include django-allauth canonical URLs under the same `accounts/` prefix
    # so provider login paths like `/accounts/google/login/` are exposed.
    path("accounts/", include("allauth.urls")),
    path("cart/", include("cart.urls", namespace="cart")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("payment/", include("payment.urls", namespace="payment")),
    path("coupons/", include("coupons.urls", namespace="coupons")),
    path("support/", include("support.urls", namespace="support")),
    # The 'shop' app handles the root URL, so it is included last to allow
    # other specific patterns to be matched first.
    path("", include("shop.urls", namespace="shop")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
