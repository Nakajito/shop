from shop.models import Category


def footer_categories(request):
    """
    Context processor to make real product categories available to the
    footer (included on every page, whether or not the view already
    provides its own ``categories`` for something else).
    """
    return {"footer_categories": Category.objects.all()}
