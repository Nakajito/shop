from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from orders.models import Order
from support.models import SupportTicket, TicketMessage


class SupportTicketModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.ticket = SupportTicket.objects.create(
            user=self.user,
            subject="Test Ticket",
            message="I have a problem",
            issue_type="problem",
        )

    def test_str(self):
        self.assertIn("Test Ticket", str(self.ticket))

    def test_default_status(self):
        self.assertEqual(self.ticket.status, "open")

    def test_default_priority(self):
        self.assertEqual(self.ticket.priority, "medium")

    def test_get_status_color(self):
        self.assertEqual(self.ticket.get_status_color(), "danger")

    def test_resolved_at_auto_set(self):
        self.ticket.status = "resolved"
        self.ticket.save()
        self.assertIsNotNone(self.ticket.resolved_at)


class TicketMessageModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.ticket = SupportTicket.objects.create(
            user=self.user, subject="Test", message="Description",
        )
        self.message = TicketMessage.objects.create(
            ticket=self.ticket, sender=self.user, message="Reply text",
        )

    def test_str(self):
        self.assertIn("testuser", str(self.message))

    def test_is_staff_reply_false(self):
        self.assertFalse(self.message.is_staff_reply)

    def test_is_staff_reply_true(self):
        staff = CustomUser.objects.create_user(
            username="staff", password="testpass123", is_staff=True
        )
        msg = TicketMessage.objects.create(
            ticket=self.ticket, sender=staff, message="Staff reply",
        )
        self.assertTrue(msg.is_staff_reply)


class SupportTicketManagerTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        SupportTicket.objects.create(
            user=self.user, subject="Open", message="desc", status="open",
        )
        SupportTicket.objects.create(
            user=self.user, subject="Closed", message="desc", status="closed",
        )

    def test_for_user(self):
        qs = SupportTicket.objects.for_user(self.user)
        self.assertEqual(qs.count(), 2)

    def test_open_tickets(self):
        qs = SupportTicket.objects.open_tickets()
        self.assertEqual(qs.count(), 1)


class TicketListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        SupportTicket.objects.create(
            user=self.user, subject="Ticket 1", message="desc",
        )

    def test_requires_login(self):
        response = self.client.get(reverse("support:ticket_list"))
        self.assertEqual(response.status_code, 302)

    def test_ticket_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("support:ticket_list"))
        self.assertEqual(response.status_code, 200)


class TicketDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.ticket = SupportTicket.objects.create(
            user=self.user, subject="Detail Test", message="desc",
        )

    def test_ticket_detail(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("support:ticket_detail", args=[self.ticket.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_ticket_detail_other_user(self):
        other = CustomUser.objects.create_user(
            username="other", password="testpass123"
        )
        self.client.force_login(other)
        response = self.client.get(
            reverse("support:ticket_detail", args=[self.ticket.id])
        )
        self.assertEqual(response.status_code, 404)


class TicketReplyViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.ticket = SupportTicket.objects.create(
            user=self.user, subject="Reply Test", message="desc",
        )

    def test_reply(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("support:ticket_reply", args=[self.ticket.id]),
            {"message": "My reply"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.ticket.messages.count(), 1)


class TicketCloseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.ticket = SupportTicket.objects.create(
            user=self.user, subject="Close Test", message="desc",
        )

    def test_close_ticket(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("support:ticket_close", args=[self.ticket.id])
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "closed")
