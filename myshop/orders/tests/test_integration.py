from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import CustomUser
from shop.models import Category, Product
from orders.models import Order


class CheckoutFlowIntegrationTest(TestCase):
    """Integration test for cart -> checkout -> order creation flow."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            slug="test-product",
            price=Decimal("25.00"),
            available=True,
        )

    def test_add_to_cart_and_create_order(self):
        # 1. Add product to cart
        response = self.client.post(
            reverse("cart:cart_add", args=[self.product.id]),
            {"quantity": 2, "override": False},
        )
        self.assertEqual(response.status_code, 302)

        # 2. Verify cart has items
        response = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(response.status_code, 200)

        # 3. Create order via checkout
        response = self.client.post(
            reverse("orders:order_create"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "address": "123 Main St",
                "postal_code": "12345",
                "city": "TestCity",
            },
        )
        # Should redirect to payment
        self.assertEqual(response.status_code, 302)

        # 4. Verify order was created
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.first_name, "John")
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 2)
        self.assertEqual(order.get_total_cost(), Decimal("50.00"))
