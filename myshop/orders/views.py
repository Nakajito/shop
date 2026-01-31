import weasyprint
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem
from .tasks import order_created


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
