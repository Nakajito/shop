from django.shortcuts import get_object_or_404, render

from cart.forms import CartAddProductForm
from .models import Category, Product
from .recommender import Recommender


def product_list(request, category_slug=None):
    """
    View to display the product catalog.

    This view handles two cases:
    1. Listing all available products (if category_slug is None).
    2. Filtering products by a specific category (if category_slug is provided).

    Args:
        request (HttpRequest): The incoming request.
        category_slug (str, optional): The slug of the category to filter by.

    Returns:
        HttpResponse: Renders 'shop/product/list.html' with the list of products
        and categories.
    """
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(
        request,
        "shop/product/list.html",
        {
            "category": category,
            "categories": categories,
            "products": products,
        },
    )


def product_detail(request, id, slug):
    """
    View to display a single product's details.

    Features:
    - Retrieves the product using both ID and Slug for SEO and data integrity.
    - Includes the 'Add to Cart' form.
    - Queries the Redis-based Recommender engine to fetch 'Frequently bought together'
      items (up to 4 suggestions).

    Args:
        request (HttpRequest): The incoming request.
        id (int): The primary key of the product.
        slug (str): The slug of the product.

    Returns:
        HttpResponse: Renders 'shop/product/detail.html'.
    """
    product = get_object_or_404(Product, id=id, slug=slug, available=True)

    # Form to add this product to the cart
    cart_product_form = CartAddProductForm()

    # Get recommended products based on past purchase history
    r = Recommender()
    recommended_products = r.suggest_products_for([product], 4)

    return render(
        request,
        "shop/product/detail.html",
        {
            "product": product,
            "cart_product_form": cart_product_form,
            "recommended_products": recommended_products,
        },
    )
