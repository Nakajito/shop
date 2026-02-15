from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from cart.forms import CartAddProductForm
from .models import Category, Product
from .recommender import Recommender


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

    context = {
        "category": category,
        "categories": categories,
        "products": products,
        "page_title": category.name if category else _("All Products"),
    }

    return render(request, "shop/product/list.html", context)


def product_detail(request, id, slug):
    """
    Displays single product details, the cart form, and Redis recommendations.
    """
    # select_related here ensures category data is available for breadcrumbs/UI
    product = get_object_or_404(
        Product.objects.select_related("category"), id=id, slug=slug, available=True
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

    context = {
        "product": product,
        "cart_product_form": cart_product_form,
        "recommended_products": recommended_products,
        "page_title": product.name,
    }

    return render(request, "shop/product/detail.html", context)
