from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase

from accounts.models import CustomUser
from cart.cart import Cart
from orders.forms import OrderCreateForm
from orders.models import Address, Order, OrderItem
from orders.services import AddressService, OrderService
from shop.models import Category, Product


class OrderServiceTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            category=self.category, name="P1", slug="p1",
            price=Decimal("50.00"), available=True,
        )
        self.factory = RequestFactory()

    def _get_cart_with_items(self):
        request = self.factory.get("/")
        request.session = SessionStore()
        cart = Cart(request)
        cart.add(self.product, quantity=2)
        return cart

    def test_create_order_from_cart(self):
        cart = self._get_cart_with_items()
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@test.com",
            "address": "123 Main St",
            "postal_code": "12345",
            "city": "TestCity",
        }
        form = OrderCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

        order = OrderService.create_order_from_cart(cart, form, user=self.user)

        self.assertIsNotNone(order.id)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 2)

    def test_create_order_without_user(self):
        cart = self._get_cart_with_items()
        form_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@test.com",
            "address": "456 Oak Ave",
            "postal_code": "67890",
            "city": "OtherCity",
        }
        form = OrderCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

        order = OrderService.create_order_from_cart(cart, form, user=None)

        self.assertIsNotNone(order.id)
        self.assertIsNone(order.user)

    def test_get_order_summary(self):
        order = Order.objects.create(
            user=self.user, first_name="John", last_name="Doe",
            email="j@test.com", address="Addr", postal_code="12345",
            city="City", discount=10,
        )
        OrderItem.objects.create(
            order=order, product=self.product,
            price=Decimal("50.00"), quantity=2,
        )
        summary = OrderService.get_order_summary(order)
        self.assertEqual(summary["total_before_discount"], Decimal("100.00"))
        self.assertEqual(summary["discount"], Decimal("10.00"))
        self.assertEqual(summary["total"], Decimal("90.00"))
        self.assertEqual(summary["item_count"], 1)


class AddressServiceTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_set_default_address(self):
        addr = Address.objects.create(
            user=self.user, address_line1="Addr 1", city="City",
            state="CDMX", postal_code="06600", phone="5522445104",
            recipient_name="John",
        )
        self.assertFalse(addr.is_default)
        AddressService.set_default_address(addr)
        addr.refresh_from_db()
        self.assertTrue(addr.is_default)

    def test_get_default_address(self):
        Address.objects.create(
            user=self.user, address_line1="Addr 1", city="City",
            state="CDMX", postal_code="06600", phone="5522445104",
            recipient_name="John", is_default=False,
        )
        default_addr = Address.objects.create(
            user=self.user, address_line1="Addr 2", city="City",
            state="CDMX", postal_code="06600", phone="5522445104",
            recipient_name="John", is_default=True,
        )
        result = AddressService.get_default_address(self.user)
        self.assertEqual(result, default_addr)

    def test_get_default_address_none(self):
        result = AddressService.get_default_address(self.user)
        self.assertIsNone(result)
