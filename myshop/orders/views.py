import logging
import weasyprint
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator
from django.db import models, transaction
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from cart.cart import Cart
from orders.forms import OrderCreateForm, AddressForm
from orders.models import Order, OrderItem, Address, OrderTracking
from orders.tasks import order_created

# Initialize logger
logger = logging.getLogger(__name__)


# --- HELPERS ---


def get_user_order(request, order_id):
    """
    Helper to retrieve an order only if it belongs to the authenticated user.
    """
    return get_object_or_404(Order, id=order_id, user=request.user)


# --- ORDER CORE VIEWS ---


@require_http_methods(["GET", "POST"])
def order_create(request):
    """
    Handles the transition from Cart to Order.
    If the form is valid, it saves the order and its items,
    then redirects to the payment process.
    """
    cart = Cart(request)
    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            # Associate the order with the authenticated user when present
            if request.user.is_authenticated:
                order.user = request.user
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
            # Launch asynchronous task (optional)
            # order_created.delay(order.id)

            # Set the order in the session
            request.session["order_id"] = order.id

            # Redirect for payment
            return redirect(reverse("payment:process"))
    else:
        form = OrderCreateForm()
    return render(request, "orders/order/create.html", {"cart": cart, "form": form})


@login_required
def order_history(request):
    """
    Displays the user's past orders with pagination and status filtering.
    """
    orders = Order.objects.filter(user=request.user).order_by("-created")

    status_filter = request.GET.get("status")
    if status_filter:
        orders = orders.filter(status=status_filter)

    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "orders/order/order_history.html",
        {"orders": orders, "page_title": "My Order History"},
    )


@login_required
def order_detail(request, order_id):
    """
    User view for specific order details, including tracking and items.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if not order:
        raise Http404

    return render(
        request,
        "orders/order/order_detail.html",
        {"order": order, "page_title": f"Order #{order.id}"},
    )


@login_required
@require_http_methods(["GET"])
def order_tracking(request, order_id):
    """
    Full tracking view for the customer.
    Displays status history, shipping provider info, and a visual progress timeline.
    """
    order = get_user_order(request, order_id)

    # Prefetch status updates to optimize queries
    status_updates = order.status_updates.all().order_by("-created_at")

    # Tracking and timeline logic
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
    """
    Specific shipment data view (Carrier, Tracking Number, Last Location).
    """
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
    """
    Simplified view focused specifically on the audit trail of status changes.
    """
    order = get_user_order(request, order_id)
    status_updates = order.status_updates.all().order_by("-created_at")

    context = {
        "order": order,
        "status_updates": status_updates,
        "page_title": _("Status History - Order #{}").format(order.id),
    }

    return render(request, "orders/order/order_status_history.html", context)


@require_POST
@login_required
def reorder(request, order_id):
    """
    Duplicates items from a past order into the current active cart.
    """
    order = get_user_order(request, order_id)
    if not order.can_be_reordered():
        messages.error(request, _("This order is not eligible for reordering."))
        return redirect("orders:order_detail", order_id=order.id)

    cart = Cart(request)
    added_count = 0
    for item in order.items.all():
        if item.product.available:
            cart.add(product=item.product, quantity=item.quantity)
            added_count += 1

    if added_count > 0:
        messages.success(request, _("Items successfully added to your cart."))
        return redirect("cart:cart_detail")

    messages.warning(
        request, _("None of the products from this order are currently available.")
    )
    return redirect("orders:order_history")


@require_http_methods(["GET", "POST"])
@login_required
def cancel_order(request, order_id):
    """
    Cancels an order. If paid, initiates a Stripe refund automatically.
    """
    order = get_user_order(request, order_id)

    if not order.can_be_cancelled():
        messages.error(request, _("This order can no longer be cancelled."))
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        reason = request.POST.get("reason", _("Cancelled by customer."))
        try:
            with transaction.atomic():
                order.change_status("cancelled", changed_by=request.user, reason=reason)

                if order.paid and order.stripe_id:
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    stripe.Refund.create(payment_intent=order.stripe_id)
                    messages.success(
                        request, _("Order cancelled and refund initiated.")
                    )
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


# --- PDF & ADMIN ---


@staff_member_required
def admin_order_detail(request, order_id):
    """
    Staff-only view to display internal order details.
    Provides a comprehensive summary for admin users.
    """
    order = get_object_or_404(Order, id=order_id)

    # Provide `opts` (model _meta) and attach app_config so admin template
    # breadcrumb reversal (`admin:app_list`) can resolve the app label correctly.
    from django.apps import apps

    opts = order._meta
    try:
        app_config = apps.get_app_config(opts.app_label)
    except LookupError:
        app_config = None

    context = {"order": order, "opts": opts, "app_config": app_config}
    return render(request, "admin/orders/order/detail.html", context)


@staff_member_required
def admin_order_pdf(request, order_id):
    """
    Generates a professional PDF invoice for staff use.
    """
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string("orders/order/pdf.html", {"order": order})
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"filename=order_{order.id}.pdf"

    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(
        response,
        stylesheets=[weasyprint.CSS(finders.find("css/pdf.css"))],
    )
    return response


@login_required
@require_http_methods(["GET"])
def order_pdf(request, order_id):
    """
    User view to download their receipt as a PDF.
    - Ensures the order belongs to the current user.
    - Generates PDF using WeasyPrint with associated static styles.
    """
    try:
        order = get_user_order(request, order_id)

        # Context for the PDF template
        context = {"order": order}
        html_string = render_to_string("orders/order/pdf.html", context)

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="receipt_order_{order.id}.pdf"'
        )

        # PDF Conversion with absolute base URL for image/CSS resolution
        html = weasyprint.HTML(
            string=html_string, base_url=request.build_absolute_uri("/")
        )

        html.write_pdf(
            response, stylesheets=[weasyprint.CSS(finders.find("css/pdf.css"))]
        )

        return response

    except Exception as e:
        logger.error(f"Error generating PDF for order {order_id}: {str(e)}")
        messages.error(request, _("Error generating the receipt PDF."))
        return redirect("orders:order_history")


# --- ADDRESS MANAGEMENT ---


@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, "orders/addresses/list.html", {"addresses": addresses})


@login_required
@require_http_methods(["GET", "POST"])
def address_create(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, _("New address saved."))
            return redirect("orders:address_list")
    else:
        form = AddressForm()
    return render(
        request, "orders/addresses/form.html", {"form": form, "is_create": True}
    )


@login_required
@require_http_methods(["GET", "POST"])
def address_edit(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, _("Address updated successfully."))
            return redirect("orders:address_list")
    else:
        form = AddressForm(instance=address)
    return render(
        request, "orders/addresses/form.html", {"form": form, "is_create": False}
    )


@require_POST
@login_required
def address_delete(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, _("Address deleted."))
    return redirect("orders:address_list")


@login_required
@require_POST
def address_set_default(request, address_id):
    """
    Sets a specific address as the user's default.
    POST only to prevent cross-site request forgery.
    """
    address = get_object_or_404(Address, id=address_id, user=request.user)

    try:
        address.is_default = True
        address.save()  # Logic for unsetting other defaults is handled in the model's save()
        messages.success(request, _("Address set as default."))
    except Exception as e:
        logger.error(f"Error setting default address: {e}")
        messages.error(request, _("Could not update default address."))

    next_url = request.GET.get("next")
    return redirect(next_url if next_url else "orders:address_list")
