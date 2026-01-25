<<<<<<< HEAD
from django.shortcuts import render
=======
from django.shortcuts import render, redirect
>>>>>>> 2101fdf (feat(payment): Add Stripe payment integration)

from cart.cart import Cart
from .forms import OrderCreateForm
from .models import OrderItem
from .tasks import order_created


def order_create(request):
    cart = Cart(request)
    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )
            # clear the cart
            cart.clear()
            order_created.delay(order.id)
<<<<<<< HEAD
            return render(request, "orders/order/created.html", {"order": order})
=======
            # set the order in the session
            request.session["order_id"] = order.id
            # redirect to the payment
            return redirect("payment:process")

>>>>>>> 2101fdf (feat(payment): Add Stripe payment integration)
    else:
        form = OrderCreateForm()
    return render(
        request,
        "orders/order/create.html",
        {"cart": cart, "form": form},
    )
