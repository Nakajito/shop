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
from orders.models import Order, OrderItem, Address, OrderTracking, STATUS_CHOICES
from orders.services import OrderService, AddressService
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
    default_address = None
    user_addresses = None
    if request.user.is_authenticated:
        default_address = AddressService.get_default_address(request.user)
        user_addresses = request.user.addresses.all()

    # When user posts, allow selecting a saved address to override form fields
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
                cart, form, user=request.user if request.user.is_authenticated else None
            )

            # Set the order in the session
            request.session["order_id"] = order.id

            # Attach chosen or default address as shipping reference and snapshot
            chosen_address = None
            if request.user.is_authenticated:
                # priority: selected_addr (POST) > default_address
                chosen_address = selected_addr or default_address

            if chosen_address:
                order.shipping_address = chosen_address
                # Snapshot the address fields onto the order for historical accuracy
                addr_text = chosen_address.address_line1 or ""
                if chosen_address.address_line2:
                    addr_text = f"{addr_text} {chosen_address.address_line2}"
                order.address = addr_text
                order.postal_code = chosen_address.postal_code or order.postal_code
                order.city = chosen_address.city or order.city
                order.save()

            # Redirect for payment
            return redirect(reverse("payment:process"))
    else:
        # Pre-fill form with user's profile and default address when available
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
    """
    Displays the user's past orders with pagination and status filtering.
    """
    base_qs = (
        Order.objects.for_user(request.user)
        .select_related("shipping_address", "coupon")
        .order_by("-created")
    )

    # Filters applied to the listing
    status_filter = request.GET.get("status")
    search_query = request.GET.get("q", "")
    orders_qs = base_qs
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)
    if search_query:
        orders_qs = orders_qs.filter(
            models.Q(id__iexact=search_query) | models.Q(email__icontains=search_query)
        )

    # Statistics computed from the user's full order history (unfiltered)
    all_orders = base_qs
    total_spent = sum([o.get_total_cost() for o in all_orders.filter(paid=True)])
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
    """
    User view for specific order details, including tracking and items.
    """
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
    """
    Full tracking view for the customer.
    Displays status history, shipping provider info, and a visual progress timeline.
    """
    order = get_user_order(request, order_id)

    status_updates = order.status_updates.select_related("changed_by").order_by(
        "-created_at"
    )

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
    if not order.can_be_reordered:
        messages.error(request, _("This order is not eligible for reordering."))
        return redirect("orders:order_detail", order_id=order.id)

    cart = Cart(request)
    added_count = 0
    for item in order.items.select_related("product").all():
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


@require_POST
@login_required
def buy_order(request, order_id):
    """
    Add all available items from a past order to the current cart and
    redirect the user straight to the payment process.
    """
    order = get_user_order(request, order_id)
    if not order.can_be_reordered:
        messages.error(request, _("This order is not eligible for reordering."))
        return redirect("orders:order_detail", order_id=order.id)

    cart = Cart(request)
    added_count = 0
    for item in order.items.select_related("product").all():
        if item.product.available:
            cart.add(product=item.product, quantity=item.quantity)
            added_count += 1

    if added_count == 0:
        messages.warning(
            request, _("None of the products from this order are currently available.")
        )
        return redirect("orders:order_detail", order_id=order.id)

    # Proceed directly to payment
    messages.success(request, _("Items added to cart — continue to payment."))
    return redirect(reverse("payment:process"))


@require_http_methods(["GET", "POST"])
@login_required
def cancel_order(request, order_id):
    """
    Cancels an order. If paid, initiates a Stripe refund automatically.
    """
    order = get_user_order(request, order_id)
    # Log removed: keep view silent in normal operation

    if not order.can_be_cancelled:
        messages.error(request, _("This order can no longer be cancelled."))
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        # debug logs removed
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
