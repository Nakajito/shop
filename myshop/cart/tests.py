from datetime import timedelta
from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase
from django.utils import timezone

from cart.cart import Cart
from coupons.models import Coupon
from shop.models import Category, Product


class CartTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.category = Category.objects.create(name="Test", slug="test")
        self.product1 = Product.objects.create(
            category=self.category,
            name="Product 1",
            slug="product-1",
            price=Decimal("10.00"),
            available=True,
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name="Product 2",
            slug="product-2",
            price=Decimal("25.50"),
            available=True,
        )

    def _get_request(self):
        request = self.factory.get("/")
        request.session = SessionStore()
        return request

    def test_cart_init_empty(self):
        request = self._get_request()
        cart = Cart(request)
        self.assertEqual(len(cart), 0)

    def test_add_product(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.product1, quantity=2)
        self.assertEqual(len(cart), 2)

    def test_add_product_increments(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.product1, quantity=1)
        cart.add(self.product1, quantity=3)
        self.assertEqual(len(cart), 4)

    def test_add_product_override_quantity(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.product1, quantity=5)
        cart.add(self.product1, quantity=2, override_quantity=True)
        self.assertEqual(len(cart), 2)

    def test_remove_product(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.product1, quantity=3)
        cart.add(self.product2, quantity=1)
        cart.remove(self.product1)
        self.assertEqual(len(cart), 1)

    def test_get_total_price(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.product1, quantity=2)  # 2 * 10 = 20
        cart.add(self.product2, quantity=1)  # 1 * 25.50 = 25.50
        self.assertEqual(cart.get_total_price(), Decimal("45.50"))

    def test_iter(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.product1, quantity=2)
        cart.add(self.product2, quantity=1)
        items = list(cart)
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertIn("product", item)
            self.assertIn("price", item)
            self.assertIn("total_price", item)
            self.assertIn("quantity", item)

    def test_clear(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.product1, quantity=1)
        cart.clear()
        # After clear, re-init cart from same session to verify it's empty
        new_cart = Cart(request)
        self.assertEqual(len(new_cart), 0)

    def test_clear_removes_coupon(self):
        request = self._get_request()
        request.session["coupon_id"] = 999
        cart = Cart(request)
        cart.add(self.product1, quantity=1)
        cart.clear()
        self.assertNotIn("coupon_id", request.session)

    def test_coupon_property_none(self):
        request = self._get_request()
        cart = Cart(request)
        self.assertIsNone(cart.coupon)

    def test_coupon_property_valid(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="TEST20",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=1),
            discount=20,
            active=True,
        )
        request = self._get_request()
        request.session["coupon_id"] = coupon.id
        cart = Cart(request)
        self.assertEqual(cart.coupon, coupon)

    def test_get_discount(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="DISC10",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=1),
            discount=10,
            active=True,
        )
        request = self._get_request()
        request.session["coupon_id"] = coupon.id
        cart = Cart(request)
        cart.add(self.product1, quantity=10)  # 10 * 10 = 100
        self.assertEqual(cart.get_discount(), Decimal("10.00"))

    def test_get_total_price_after_discount(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="DISC50",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=1),
            discount=50,
            active=True,
        )
        request = self._get_request()
        request.session["coupon_id"] = coupon.id
        cart = Cart(request)
        cart.add(self.product1, quantity=10)  # 100
        self.assertEqual(cart.get_total_price_after_discount(), Decimal("50.00"))

    def test_get_discount_no_coupon(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.product1, quantity=5)
        self.assertEqual(cart.get_discount(), Decimal("0"))
