from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from shop.models import Category, Product
from orders.models import Order, OrderItem, Address, OrderTracking, OrderStatusUpdate


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            category=self.category,
            name="P1",
            slug="p1",
            price=Decimal("100.00"),
            available=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            address="123 Main St",
            postal_code="12345",
            city="TestCity",
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=Decimal("100.00"),
            quantity=2,
        )

    def test_str(self):
        self.assertEqual(str(self.order), f"Order {self.order.id}")

    def test_get_total_cost_before_discount(self):
        self.assertEqual(self.order.get_total_cost_before_discount(), Decimal("200.00"))

    def test_get_discount_zero(self):
        self.assertEqual(self.order.get_discount(), Decimal("0"))

    def test_get_discount_with_percentage(self):
        self.order.discount = 10
        self.order.save()
        self.assertEqual(self.order.get_discount(), Decimal("20.00"))

    def test_get_total_cost(self):
        self.order.discount = 10
        self.order.save()
        self.assertEqual(self.order.get_total_cost(), Decimal("180.00"))

    def test_get_timeline_steps(self):
        self.order.status = "confirmed"
        self.order.save()
        timeline = self.order.get_timeline_steps()
        self.assertEqual(len(timeline), 3)
        self.assertTrue(timeline[0]["completed"])  # confirmed
        self.assertFalse(timeline[1]["completed"])  # shipped

    def test_change_status(self):
        result = self.order.change_status("confirmed", user=self.user, note="Confirmed")
        self.assertTrue(result)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "confirmed")

    def test_change_status_same(self):
        self.order.status = "pending"
        self.order.save()
        result = self.order.change_status("pending")
        self.assertFalse(result)


class OrderItemModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            category=self.category,
            name="P1",
            slug="p1",
            price=Decimal("50.00"),
            available=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            address="Addr",
            postal_code="12345",
            city="City",
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=Decimal("50.00"),
            quantity=3,
        )

    def test_get_cost(self):
        self.assertEqual(self.item.get_cost(), Decimal("150.00"))


class AddressModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_address(self):
        address = Address.objects.create(
            user=self.user,
            address_line1="123 Main St",
            city="TestCity",
            state="CDMX",
            postal_code="06600",
            phone="5522445104",
            recipient_name="John Doe",
        )
        self.assertIn("John Doe", str(address))

    def test_get_full_address(self):
        address = Address.objects.create(
            user=self.user,
            address_line1="123 Main St",
            address_line2="Apt 4",
            city="TestCity",
            state="CDMX",
            postal_code="06600",
            country="MX",
            phone="5522445104",
            recipient_name="John Doe",
        )
        full = address.get_full_address()
        self.assertIn("123 Main St", full)
        self.assertIn("Apt 4", full)
        self.assertIn("TestCity", full)

    def test_default_address_unique(self):
        addr1 = Address.objects.create(
            user=self.user,
            address_line1="Addr 1",
            city="City",
            state="CDMX",
            postal_code="06600",
            phone="5522445104",
            recipient_name="John",
            is_default=True,
        )
        addr2 = Address.objects.create(
            user=self.user,
            address_line1="Addr 2",
            city="City",
            state="CDMX",
            postal_code="06600",
            phone="5522445104",
            recipient_name="John",
            is_default=True,
        )
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)


class OrderManagerTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.order1 = Order.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="j@test.com",
            address="Addr",
            postal_code="12345",
            city="City",
            status="pending",
        )
        self.order2 = Order.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="j@test.com",
            address="Addr",
            postal_code="12345",
            city="City",
            status="shipped",
            paid=True,
        )

    def test_for_user(self):
        qs = Order.objects.for_user(self.user)
        self.assertEqual(qs.count(), 2)

    def test_by_status(self):
        qs = Order.objects.by_status("shipped")
        self.assertEqual(qs.count(), 1)

    def test_paid_orders(self):
        qs = Order.objects.paid_orders()
        self.assertEqual(qs.count(), 1)

    def test_with_full_details(self):
        qs = Order.objects.with_full_details()
        self.assertEqual(qs.count(), 2)


class OrderHistoryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        Order.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="j@test.com",
            address="Addr",
            postal_code="12345",
            city="City",
        )

    def test_requires_login(self):
        response = self.client.get(reverse("orders:order_history"))
        self.assertEqual(response.status_code, 302)

    def test_order_history(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("orders:order_history"))
        self.assertEqual(response.status_code, 200)

    def test_order_history_filter(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("orders:order_history") + "?status=pending")
        self.assertEqual(response.status_code, 200)


class CancelOrderViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="canceluser", email="cancel@test.com", password="testpass123"
        )
        self.order = Order.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            address="Somewhere",
            postal_code="00000",
            city="City",
            status="pending",
            paid=False,
        )

    def test_cancel_order_post_unpaid(self):
        """POST to cancel an unpaid order should mark it cancelled and create a status update."""
        self.client.force_login(self.user)
        url = reverse("orders:cancel_order", args=[self.order.id])
        response = self.client.post(
            url, {"reason": "Changed my mind", "confirm_cancel": "1"}
        )
        # Successful cancellation redirects to order history
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")
        self.assertTrue(
            OrderStatusUpdate.objects.filter(
                order=self.order, new_status="cancelled"
            ).exists()
        )
