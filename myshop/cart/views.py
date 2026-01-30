from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from shop.models import Product

from .cart import Cart
from .forms import CartAddProductForm
from coupons.forms import CouponApplyForm
from shop.recommender import Recommender


@require_POST
def cart_add(request, product_id):
    """
    View to add a product to the cart or update its quantity.

    This view requires a POST request containing valid form data (quantity and
    override boolean). It retrieves the product by ID and uses the Cart class
    to update the session.

    Args:
        request (HttpRequest): The incoming POST request.
        product_id (int): The primary key of the Product to add/update.

    Returns:
        HttpResponseRedirect: Redirects the user to the cart detail page upon success.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(
            product=product,
            quantity=cd["quantity"],
            override_quantity=cd["override"],
        )
    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    """
    View to remove a product from the cart.

    Args:
        request (HttpRequest): The incoming POST request.
        product_id (int): The primary key of the Product to remove.

    Returns:
        HttpResponseRedirect: Redirects the user to the cart detail page.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect("cart:cart_detail")


def cart_detail(request):
    """
    View to display the current contents of the shopping cart.

    This view performs several key tasks:
    1. Iterates over cart items to attach a `CartAddProductForm` to each one,
       allowing users to update quantities directly from the cart page (with
       `override=True` pre-set).
    2. Instantiates a `CouponApplyForm` for discount codes.
    3. Uses the `Recommender` engine to fetch suggested products based on
       items currently in the cart.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: Renders the 'cart/detail.html' template with the cart,
        forms, and recommended products in the context.
    """
    cart = Cart(request)

    # Create a form for each item to allow quantity updates in the view
    for item in cart:
        item["update_quantity_form"] = CartAddProductForm(
            initial={"quantity": item["quantity"], "override": True}
        )

    coupon_apply_form = CouponApplyForm()

    # Recommendation logic
    r = Recommender()
    cart_products = [item["product"] for item in cart]
    if cart_products:
        recommended_products = r.suggest_products_for(cart_products, max_results=4)
    else:
        recommended_products = []

    return render(
        request,
        "cart/detail.html",
        {
            "cart": cart,
            "coupon_apply_form": coupon_apply_form,
            "recommended_products": recommended_products,
        },
    )
