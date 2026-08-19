from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from coupons.forms import CouponApplyForm
from shop.models import Product
from shop.recommender import Recommender

from .cart import Cart
from .forms import CartAddProductForm


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
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if form.is_valid():
        cd = form.cleaned_data
        cart.add(
            product=product,
            quantity=cd["quantity"],
            override_quantity=cd["override"],
        )
        if is_ajax:
            return JsonResponse(
                {
                    "ok": True,
                    "cart_len": len(cart),
                    "product_name": product.name,
                }
            )
        messages.success(request, _("Producto agregado al carrito."))
    else:
        if is_ajax:
            return JsonResponse(
                {"ok": False, "error": _("Error al agregar el producto al carrito.")},
                status=400,
            )
        messages.error(request, _("Error al agregar el producto al carrito."))

    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    """
    View to remove a product from the cart.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, _("Producto eliminado del carrito."))
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
    recommended_products = []
    try:
        r = Recommender()
        cart_products = [item["product"] for item in cart_items]
        if cart_products:
            recommended_products = r.suggest_products_for(cart_products, max_results=4)
    except Exception:
        pass

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
