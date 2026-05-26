"""Order checkout, history, tracking and lifecycle views."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST, require_http_methods

from cart.cart import Cart
from orders.forms import OrderCreateForm
from orders.models import STATUS_CHOICES, Address, Order, OrderTracking
from orders.services import AddressService, OrderService
from orders.tasks import order_created

from ._helpers import get_user_order

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def order_create(request):
    """Transition Cart -> Order. On success redirect to payment process."""
    cart = Cart(request)
    default_address = None
    user_addresses = None
    if request.user.is_authenticated:
        default_address = AddressService.get_default_address(request.user)
        user_addresses = request.user.addresses.all()

    if request.method == "POST":
        post_data = request.POST.copy()
        selected_addr_id = post_data.get("selected_address")
        selected_addr = None
        if selected_addr_id:
            try:
                selected_addr = Address.objects.get(
                    id=selected_addr_id, user=request.user
                )
                addr = selected_addr.address_line1 or ""
                if selected_addr.address_line2:
                    addr = f"{addr} {selected_addr.address_line2}"
                post_data["address"] = addr
                post_data["postal_code"] = selected_addr.postal_code or ""
                post_data["city"] = selected_addr.city or ""
            except Address.DoesNotExist:
                selected_addr = None

        form = OrderCreateForm(post_data)
        if form.is_valid():
            order = OrderService.create_order_from_cart(
                cart,
                form,
                user=request.user if request.user.is_authenticated else None,
            )

            request.session["order_id"] = order.id

            chosen_address = None
            if request.user.is_authenticated:
                chosen_address = selected_addr or default_address

            if chosen_address:
                order.shipping_address = chosen_address
                addr_text = chosen_address.address_line1 or ""
                if chosen_address.address_line2:
                    addr_text = f"{addr_text} {chosen_address.address_line2}"
                order.address = addr_text
                order.postal_code = chosen_address.postal_code or order.postal_code
                order.city = chosen_address.city or order.city
                order.save()

            order_created.delay(order.id)
            return redirect(reverse("payment:process"))
    else:
        initial = {}
        if request.user.is_authenticated:
            if getattr(request.user, "first_name", None):
                initial["first_name"] = request.user.first_name
            if getattr(request.user, "last_name", None):
                initial["last_name"] = request.user.last_name
            if getattr(request.user, "email", None):
                initial["email"] = request.user.email

        if default_address:
            addr = default_address.address_line1 or ""
            if default_address.address_line2:
                addr = f"{addr} {default_address.address_line2}"
            initial.update(
                {
                    "address": addr,
                    "postal_code": default_address.postal_code,
                    "city": default_address.city,
                }
            )

        form = OrderCreateForm(initial=initial)
    return render(request, "orders/order/create.html", {"cart": cart, "form": form})


@login_required
def order_history(request):
    """Past orders with pagination, status filter, and search."""
    base_qs = (
        Order.objects.for_user(request.user)
        .select_related("shipping_address", "coupon")
        .order_by("-created")
    )

    status_filter = request.GET.get("status")
    search_query = request.GET.get("q", "")
    orders_qs = base_qs
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)
    if search_query:
        orders_qs = orders_qs.filter(
            models.Q(id__iexact=search_query) | models.Q(email__icontains=search_query)
        )

    all_orders = base_qs
    total_spent = sum(o.get_total_cost() for o in all_orders.filter(paid=True))
    stats = {
        "total_orders": all_orders.count(),
        "total_spent": total_spent,
        "delivered_orders": all_orders.filter(status="delivered").count(),
        "pending_orders": all_orders.filter(status="pending").count(),
        "cancelled_orders": all_orders.filter(status="cancelled").count(),
    }

    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "orders/order/order_history.html",
        {
            "orders": page_obj,
            "page_title": "My Order History",
            "stats": stats,
            "status_choices": STATUS_CHOICES,
            "current_status": status_filter,
            "search_query": search_query,
        },
    )


@login_required
def order_detail(request, order_id):
    """Order detail page including items and tracking."""
    order = get_object_or_404(
        Order.objects.with_full_details(),
        id=order_id,
        user=request.user,
    )

    return render(
        request,
        "orders/order/order_detail.html",
        {"order": order, "page_title": f"Order #{order.id}"},
    )


@login_required
@require_http_methods(["GET"])
def order_tracking(request, order_id):
    """Customer-facing tracking with timeline + status history."""
    order = get_user_order(request, order_id)

    status_updates = order.status_updates.select_related("changed_by").order_by(
        "-created_at"
    )

    tracking = getattr(order, "tracking", None)
    timeline_steps = order.get_timeline_steps()

    context = {
        "order": order,
        "status_updates": status_updates,
        "tracking": tracking,
        "timeline_steps": timeline_steps,
        "page_title": _("Order Tracking #{}").format(order.id),
    }

    return render(request, "orders/order/order_tracking.html", context)


@login_required
@require_http_methods(["GET"])
def order_tracking_info(request, order_id):
    """Carrier / tracking-number / last-location detail."""
    order = get_user_order(request, order_id)
    tracking = get_object_or_404(OrderTracking, order=order)

    context = {
        "order": order,
        "tracking": tracking,
        "page_title": _("Shipping Information - Order #{}").format(order.id),
    }

    return render(request, "orders/order/order_tracking_info.html", context)


@login_required
@require_http_methods(["GET"])
def order_status_history(request, order_id):
    """Audit-trail view of status changes."""
    order = get_user_order(request, order_id)
    status_updates = order.status_updates.all().order_by("-created_at")

    context = {
        "order": order,
        "status_updates": status_updates,
        "page_title": _("Status History - Order #{}").format(order.id),
    }

    return render(request, "orders/order/order_status_history.html", context)


def _readd_order_items_to_cart(order, cart):
    """Re-add a past order's available items into ``cart``. Returns count added."""
    added = 0
    for item in order.items.select_related("product").all():
        if item.product.available:
            cart.add(product=item.product, quantity=item.quantity)
            added += 1
    return added


@require_POST
@login_required
def reorder(request, order_id):
    """Re-add a past order's items to the current cart."""
    order = get_user_order(request, order_id)
    if not order.can_be_reordered:
        messages.error(request, _("This order is not eligible for reordering."))
        return redirect("orders:order_detail", order_id=order.id)

    cart = Cart(request)
    added_count = _readd_order_items_to_cart(order, cart)

    if added_count > 0:
        messages.success(request, _("Items successfully added to your cart."))
        return redirect("cart:cart_detail")

    messages.warning(
        request, _("None of the products from this order are currently available.")
    )
    return redirect("orders:order_history")


@require_POST
@login_required
def buy_order(request, order_id):
    """Re-add items and jump straight to payment."""
    order = get_user_order(request, order_id)
    if not order.can_be_reordered:
        messages.error(request, _("This order is not eligible for reordering."))
        return redirect("orders:order_detail", order_id=order.id)

    cart = Cart(request)
    added_count = _readd_order_items_to_cart(order, cart)

    if added_count == 0:
        messages.warning(
            request, _("None of the products from this order are currently available.")
        )
        return redirect("orders:order_detail", order_id=order.id)

    messages.success(request, _("Items added to cart — continue to payment."))
    return redirect(reverse("payment:process"))


@require_http_methods(["GET", "POST"])
@login_required
def cancel_order(request, order_id):
    """Cancel an order. Initiates Stripe refund if it was paid."""
    order = get_user_order(request, order_id)

    if not order.can_be_cancelled:
        messages.error(request, _("This order can no longer be cancelled."))
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        reason = request.POST.get("reason", _("Cancelled by customer."))
        try:
            refunded = OrderService.cancel_order(order, request.user, reason)
            if refunded:
                messages.success(request, _("Order cancelled and refund initiated."))
            else:
                messages.success(request, _("Order cancelled successfully."))
            return redirect("orders:order_history")
        except Exception as e:
            logger.error(f"Cancellation error for Order {order.id}: {e}")
            messages.error(
                request,
                _("Refund failed. Please contact support to complete cancellation."),
            )

    return render(request, "orders/order/cancel_order.html", {"order": order})
