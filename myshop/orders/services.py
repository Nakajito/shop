import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from orders.models import OrderItem

logger = logging.getLogger(__name__)


class OrderService:
    @staticmethod
    def create_order_from_cart(cart, form, user=None):
        """Create an order from a shopping cart and form data."""
        with transaction.atomic():
            order = form.save(commit=False)
            if user and user.is_authenticated:
                order.user = user
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount
            order.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )
            cart.clear()
            return order

    @staticmethod
    def cancel_order(order, user, reason=""):
        """Cancel an order and initiate refund if paid."""
        if not OrderService.can_cancel_order(order):
            raise ValueError(_("This order can no longer be cancelled."))

        with transaction.atomic():
            # `Order.change_status` signature is (new_status, user=None, note="")
            order.change_status("cancelled", user=user, note=reason)

            refunded = False
            if order.paid and order.stripe_id:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe.Refund.create(payment_intent=order.stripe_id)
                refunded = True

            return refunded

    @staticmethod
    def can_cancel_order(order):
        attr = getattr(order, "can_be_cancelled", None)
        if callable(attr):
            return attr()
        return bool(attr)

    @staticmethod
    def can_reorder(order):
        attr = getattr(order, "can_be_reordered", None)
        if callable(attr):
            return attr()
        return bool(attr)

    @staticmethod
    def get_order_summary(order):
        """Return a summary dict with order calculations."""
        return {
            "total_before_discount": order.get_total_cost_before_discount(),
            "discount": order.get_discount(),
            "total": order.get_total_cost(),
            "item_count": order.items.count(),
            "status": order.get_status_display(),
        }


class AddressService:
    @staticmethod
    def set_default_address(address):
        """Set an address as default (model save handles unsetting others)."""
        address.is_default = True
        address.save()

    @staticmethod
    def get_default_address(user):
        """Get the user's default address."""
        return user.addresses.filter(is_default=True).first()
