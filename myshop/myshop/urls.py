from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

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

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
]
