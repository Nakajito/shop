from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cart/", include("cart.urls", namespace="cart")),
    path("orders", include("orders.urls", namespace="orders")),
<<<<<<< HEAD
=======
    path("payment/", include("payment.urls", namespace="payment")),
>>>>>>> 2101fdf (feat(payment): Add Stripe payment integration)
    path("", include("shop.urls", namespace="shop")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
