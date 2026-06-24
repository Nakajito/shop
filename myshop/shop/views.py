from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_cookie

from cart.forms import CartAddProductForm

from .models import Category, Product
from .recommender import Recommender


def home(request):
    return render(request, "shop/home.html")


def synkfood(request):
    categories = Category.objects.all()
    return render(
        request,
        "shop/synkfood.html",
        {"categories": categories},
    )


@vary_on_cookie
@cache_control(private=True, no_cache=True)
def product_list(request, category_slug=None):
    """
    Displays the product catalog with optional category filtering.
    Optimized with select_related for category lookups.
    """
    category = None
    categories = Category.objects.all()
    # select_related avoids multiple queries when accessing product.category in the template
    products = Product.objects.filter(available=True).select_related("category")

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Text search filter
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(name__icontains=query)

    # Price range filter via GET params: min_price, max_price
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    price_filter_applied = False
    try:
        if min_price:
            min_val = Decimal(min_price)
            products = products.filter(price__gte=min_val)
            price_filter_applied = True
        if max_price:
            max_val = Decimal(max_price)
            products = products.filter(price__lte=max_val)
            price_filter_applied = True
    except (InvalidOperation, ValueError):
        # ignore invalid numeric input
        min_price = None
        max_price = None

    user_favorites = []
    if request.user.is_authenticated:
        user_favorites = list(request.user.favorites.values_list("id", flat=True))

    context = {
        "category": category,
        "categories": categories,
        "products": products,
        "min_price": min_price,
        "max_price": max_price,
        "price_filter_applied": price_filter_applied,
        "user_favorites": user_favorites,
        "query": query,
        "page_title": category.name if category else _("All Products"),
    }

    return render(request, "shop/product/list.html", context)


@vary_on_cookie
@cache_control(private=True, no_cache=True)
def product_detail(request, id, slug):
    """
    Displays single product details, the cart form, and Redis recommendations.
    """
    # select_related here ensures category data is available for breadcrumbs/UI
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images"),
        id=id,
        slug=slug,
        available=True,
    )

    # Initialize the Add to Cart form
    cart_product_form = CartAddProductForm()

    # Retrieve recommendations from Redis
    recommended_products = []
    try:
        r = Recommender()
        recommended_products = r.suggest_products_for([product], 4)
    except Exception:
        # If Redis is down, we still want to show the product page
        pass

    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = request.user.favorites.filter(id=product.id).exists()

    context = {
        "product": product,
        "cart_product_form": cart_product_form,
        "recommended_products": recommended_products,
        "is_favorite": is_favorite,
        "page_title": product.name,
    }

    return render(request, "shop/product/detail.html", context)


@login_required(login_url="accounts:login")
@require_POST
def toggle_favorite(request, product_id):
    """Toggle a product in the user's favorites list. Returns JSON."""
    product = get_object_or_404(Product, id=product_id)
    if request.user.favorites.filter(id=product_id).exists():
        request.user.favorites.remove(product)
        is_favorite = False
    else:
        request.user.favorites.add(product)
        is_favorite = True
    return JsonResponse(
        {
            "is_favorite": is_favorite,
            "count": request.user.favorites.count(),
        }
    )


def form_mayorista(request):
    """Displays the wholesaler contact form."""
    return render(request, "form-mayorista.html")


@login_required(login_url="accounts:login")
def favorite_list(request):
    """Display all products in the user's favorites."""
    products = request.user.favorites.select_related("category").filter(available=True)
    context = {
        "products": products,
        "page_title": _("My Favorites"),
    }
    return render(request, "shop/product/favorites.html", context)
