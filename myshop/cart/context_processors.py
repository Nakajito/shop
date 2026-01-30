from .cart import Cart


def cart(request):
    """
    Context processor to make the Cart object available in all templates.

    This function instantiates the Cart class with the current request and
    returns it as a dictionary. When registered in settings.TEMPLATES,
    it allows you to use {{ cart }} variables (like {{ cart.__len__ }} or
    {{ cart.get_total_price }}) in any HTML template without passing it
    from the view.

    Args:
        request (HttpRequest): The incoming request object.

    Returns:
        dict: A context dictionary containing the 'cart' instance.
    """
    return {"cart": Cart(request)}
