from decimal import Decimal

from django.conf import settings

from coupons.models import Coupon
from shop.models import Product


class Cart:
    """
    A session-based shopping cart management class.

    This class handles the addition, removal, and iteration of products within
    the user's session. It persists data using Django's session framework,
    ensuring the cart remains available across requests. It also handles
    price calculations, coupon applications, and data serialization.
    """

    def __init__(self, request):
        """
        Initialize the cart using the Django session.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        # Store current applied coupon
        self.coupon_id = self.session.get("coupon_id")

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database.
        """
        product_ids = list(self.cart.keys())
        # Get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)
        found_ids = {str(product.id) for product in products}

        # Prune entries whose product was deleted from the DB. Leaving them in
        # the session yields items without a "product" key (breaking templates
        # that reverse 'cart_add' with an empty id) and inflates len()/totals.
        orphaned_ids = [pid for pid in product_ids if pid not in found_ids]
        if orphaned_ids:
            for pid in orphaned_ids:
                del self.cart[pid]
            self.save()

        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]["product"] = product

        for item in cart.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item["quantity"] for item in self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}

        if override_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity

        self.save()

    def save(self):
        # Mark the session as "modified" to make sure it gets saved
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def get_total_price(self):
        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )

    @property
    def coupon(self):
        """
        Retrieve the Coupon object associated with the current session.

        Uses caching (`self._coupon_cache`) to avoid hitting the database
        multiple times during the same request lifecycle.

        Returns:
            Coupon or None: The Coupon object if valid, otherwise None.
        """
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id, active=True)
            except Coupon.DoesNotExist:
                pass
        return None

    def get_discount(self) -> Decimal:
        """
        Calculate the monetary value of the discount based on the active coupon.

        Returns:
            Decimal: The discount amount. Returns 0 if no coupon is active.
        """
        if self.coupon:
            return (self.coupon.discount / Decimal(100)) * self.get_total_price()
        return Decimal(0)

    def clear(self):
        # Remove cart and coupon from session
        del self.session[settings.CART_SESSION_ID]
        if "coupon_id" in self.session:
            del self.session["coupon_id"]
        self.save()

    def get_total_price_after_discount(self) -> Decimal:
        """
        Calculate the final total price after applying the coupon discount.

        Returns:
            Decimal: The total price minus the discount.
        """
        return self.get_total_price() - self.get_discount()
