from decimal import Decimal
from django.conf import settings
from shop.models import Product
from coupons.models import Coupon


class Cart:
    """
    A session-based shopping cart management class.

    This class handles the addition, removal, and iteration of products within
    the user's session. It persists data using Django's session framework,
    ensuring the cart remains available across requests. It also handles
    price calculations and coupon applications.
    """

    def __init__(self, request):
        """
        Initialize the cart using the current request session.

        If a cart session does not exist, a new empty dictionary is created
        and stored in the session under the key defined in settings.CART_SESSION_ID.

        Args:
            request (HttpRequest): The standard Django request object.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        # store current applied coupon
        self.coupon_id = self.session.get("coupon_id")

    def __iter__(self):
        """
        Iterate over the items in the cart and attach Product database instances.

        This method retrieves the actual Product objects from the database based
        on the IDs stored in the session. It also calculates the 'total_price'
        for each line item (price * quantity) and converts stored string prices
        back to Decimal objects for accurate arithmetic.

        Yields:
            dict: A dictionary containing the product, quantity, price (Decimal),
                  and total_price (Decimal).
        """
        product_ids = self.cart.keys()
        # get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)

        # Create a copy to avoid modifying the session data directly during iteration
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]["product"] = product

        for item in cart.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            yield item

    def __len__(self):
        """
        Return the total number of items in the cart.

        Returns:
            int: The sum of quantities across all distinct items.
        """
        return sum(item["quantity"] for item in self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.

        Args:
            product (Product): The product instance to add.
            quantity (int, optional): The number of items to add. Defaults to 1.
            override_quantity (bool, optional): If True, replaces the current
                quantity with the new value. If False, adds to the existing
                quantity. Defaults to False.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                "quantity": 0,
                "price": str(product.price),  # Store as string for JSON serialization
            }

        if override_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity

        self.save()

    def save(self):
        """
        Mark the session as modified to ensure it gets saved to the backend.
        """
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.

        Args:
            product (Product): The product instance to remove.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        """
        Remove the cart from the session entirely.
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def get_total_price(self):
        """
        Calculate the total cost of all items in the cart before discounts.

        Returns:
            Decimal: The sum of (price * quantity) for all items.
        """
        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )

    @property
    def coupon(self):
        """
        Retrieve the Coupon object associated with the current session.

        Returns:
            Coupon or None: The Coupon object if a valid ID exists in the
            session, otherwise None.
        """
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass
        return None

    def get_discount(self):
        """
        Calculate the monetary value of the discount based on the active coupon.

        Returns:
            Decimal: The discount amount. Returns 0 if no coupon is active.
        """
        if self.coupon:
            return (self.coupon.discount / Decimal(100)) * self.get_total_price()
        return Decimal(0)

    def get_total_price_after_discount(self):
        """
        Calculate the final total price after applying the coupon discount.

        Returns:
            Decimal: The total price minus the discount.
        """
        return self.get_total_price() - self.get_discount()
