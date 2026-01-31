from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.staticfiles import finders
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
import weasyprint

from cart.cart import Cart
from orders.forms import OrderCreateForm, AddressForm
from orders.models import Order, OrderItem, Address
from orders.tasks import order_created


def order_create(request):
    """
    View to handle the creation of a new order.

    Process:
    1. Instantiates the cart to access current items.
    2. On POST, validates the user's shipping data (OrderCreateForm).
    3. Creates the Order object (pausing save with commit=False to apply coupons).
    4. Transfers items from the session Cart to database OrderItem records.
    5. Clears the cart session.
    6. Triggers the asynchronous 'order_created' email task.
    7. Stores the order ID in the session for the payment gateway.
    8. Redirects to the payment processing view.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: Renders the checkout page (on GET) or redirects to
        payment (on success).
    """
    cart = Cart(request)

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # Create order object but don't save to DB yet
            order = form.save(commit=False)

            # Apply coupon if one exists in the cart
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount

            # Now save the order to the database
            order.save()

            # Create a database record for each item in the cart
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )

            # clear the cart
            cart.clear()

            # launch asynchronous task
            order_created.delay(order.id)

            # set order status to 'pending'
            order.status = "pending"
            order.change_status(
                "pending",
                changed_by=request.user if request.user.is_authenticated else None,
                reason="Order created, pending payment",
            )

            # set the order in the session for the payment step
            request.session["order_id"] = order.id

            # redirect for payment
            return redirect("payment:process")

    else:
        form = OrderCreateForm()

    return render(
        request,
        "orders/order/create.html",
        {"cart": cart, "form": form},
    )


@staff_member_required
def admin_order_detail(request, order_id):
    """
    Custom admin view to display order details.

    This view is accessible only by staff members and provides a read-only
    summary of the order, used by the 'View' link in the Order Admin list.
    """
    order = get_object_or_404(Order, id=order_id)
    return render(request, "admin/orders/order/detail.html", {"order": order})


@staff_member_required
def admin_order_pdf(request, order_id):
    """
    Generate a PDF invoice for a specific order.

    Uses WeasyPrint to render an HTML template into a PDF document.
    It automatically locates the CSS file using Django's static file finders.

    Args:
        request (HttpRequest): The incoming request.
        order_id (int): ID of the order to print.

    Returns:
        HttpResponse: A response with content_type='application/pdf'.
    """
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string("orders/order/pdf.html", {"order": order})

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"filename=order_{order.id}.pdf"

    # render PDF with CSS
    weasyprint.HTML(string=html).write_pdf(
        response,
        stylesheets=[weasyprint.CSS(finders.find("css/pdf.css"))],
    )

    return response


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def address_list(request):
    """
    View to list all user addresses.
    GET: Displays all addresses
    """

    addresses = request.user.addresses.all().order_by("-is_default", "-created_at")

    context = {
        "addresses": addresses,
        "page_title": "My address",
        "total_addresses": addresses.count(),
    }

    return render(request, "orders/addresses/list.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def address_create(request):
    """
    View to create new address.
    GET: Display form
    POST: Save new address
    """

    if request.method == "POST":
        form = AddressForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    address = form.save(commit=False)
                    address.user = request.user
                    address.save()

                    messages.success(request, "Address successfully added.")

                    # Redirect to the next page if coming from checkout
                    next_url = request.GET.get("next")
                    if next_url:
                        return redirect(next_url)

                    return redirect("orders:address_list")

            except Exception as e:
                messages.error(request, f"Error saving address: {str(e)}")

    else:
        form = AddressForm()

    context = {
        "form": form,
        "page_title": "Add New Address",
        "is_create": True,
    }

    return render(request, "orders/addresses/form.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def address_edit(request, address_id):
    """
    View to edit existing address.
    GET: Displays form with current data
    POST: Saves changes
    """

    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, "Address successfully updated.")
                    return redirect("orders:address_list")

            except Exception as e:
                messages.error(request, f"Error updating address: {str(e)}")

    else:
        form = AddressForm(instance=address)

    context = {
        "form": form,
        "address": address,
        "page_title": f"Edit Address - {address.recipient_name}",
        "is_create": False,
    }

    return render(request, "orders/addresses/form.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def address_delete(request, address_id):
    """
    View to delete address.
    GET: Shows confirmation
    POST: Deletes address
    """

    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        try:
            address_info = str(address)
            address.delete()
            messages.success(request, f'Address "{address_info}" Successfully deleted.')
            return redirect("orders:address_list")

        except Exception as e:
            messages.error(request, f"Error deleting address: {str(e)}")

    context = {
        "address": address,
        "page_title": "Delete Address",
    }

    return render(request, "orders/addresses/confirm_delete.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def address_set_default(request, address_id):
    """
    View to set default address.
    POST only for security.
    """

    address = get_object_or_404(Address, id=address_id, user=request.user)

    try:
        address.is_default = True
        address.save()

        messages.success(request, "Address set as default.")

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")

    # Redirigir a origen o a lista de direcciones
    next_url = request.GET.get("next")
    return redirect(next_url if next_url else "orders:address_list")


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def order_history(request):
    """
    View to see the user's purchase history.
    GET: Shows all the user's orders.
    """

    orders = request.user.orders.all().order_by("-created")

    # Paginación opcional
    from django.core.paginator import Paginator

    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "orders": page_obj,
        "page_title": "My Purchases",
        "total_orders": orders.count(),
    }

    return render(request, "orders/order_history.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def order_detail(request, order_id):
    """
    View to see complete details of an order.
    GET: Displays complete order information.
    """

    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()

    context = {
        "order": order,
        "items": items,
        "page_title": f"Order #{order.id}",
    }

    return render(request, "orders/order_detail.html", context)
