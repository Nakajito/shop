from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib import messages
from shop.models import Product
from .cart import Cart
from .forms import CartAddProductForm
from coupons.forms import CouponApplyForm
from shop.recommender import Recommender
from coupons.forms import CouponApplyForm


@require_POST
def cart_add(request, product_id):
    """
    View to add a product to the cart or update its quantity.

    Uses POST method to ensure state-changing actions are safe.
    Includes success/error messages for better UX.
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
        messages.success(request, "Product added to cart.")
    else:
        messages.error(request, "Error adding product to cart.")

    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    """
    View to remove a product from the cart.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, "Product removed from cart.")
    return redirect("cart:cart_detail")


def cart_detail(request):
    """
    View to display the current contents of the shopping cart.

    Optimizations:
    - Iterates the cart once to generate a list ('cart_items') with attached forms.
    - Passes this list to the template to avoid re-querying the database or losing forms.
    """
    cart = Cart(request)

    # We iterate the cart generator once and store the results in a list.
    # This persists the attached 'update_quantity_form' for the template.
    cart_items = []
    for item in cart:
        item["update_quantity_form"] = CartAddProductForm(
            initial={"quantity": item["quantity"], "override": True}
        )
        cart_items.append(item)

    coupon_apply_form = CouponApplyForm()

    # Recommendation logic
    r = Recommender()
    # Extract product objects from the prepared list
    cart_products = [item["product"] for item in cart_items]

    if cart_products:
        recommended_products = r.suggest_products_for(cart_products, max_results=4)
    else:
        recommended_products = []

    coupon_apply_form = CouponApplyForm()

    return render(
        request,
        "cart/detail.html",
        {
            "cart": cart,  # Passed for total calculations methods
            "cart_items": cart_items,  # Passed for iteration (contains forms)
            "coupon_apply_form": coupon_apply_form,
            "recommended_products": recommended_products,
        },
    )
