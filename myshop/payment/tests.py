from django.test import TestCase

from accounts.models import CustomUser
from payment.models import PaymentMethod


class PaymentMethodModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.pm = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id="pm_test_123",
            card_type="visa",
            last_four_digits="4242",
            card_holder_name="John Doe",
            exp_month=12,
            exp_year=2030,
            is_default=True,
        )

    def test_str(self):
        self.assertIn("4242", str(self.pm))

    def test_get_masked_card(self):
        self.assertEqual(self.pm.get_masked_card(), "\u2022\u2022\u2022\u2022 4242")

    def test_is_expired_false(self):
        self.assertFalse(self.pm.is_expired())

    def test_is_expired_true(self):
        self.pm.exp_year = 2020
        self.pm.exp_month = 1
        self.pm.save()
        self.assertTrue(self.pm.is_expired())

    def test_get_expiration_display(self):
        self.assertEqual(self.pm.get_expiration_display(), "12/30")

    def test_default_unique_per_user(self):
        pm2 = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id="pm_test_456",
            card_type="mastercard",
            last_four_digits="1234",
            card_holder_name="John Doe",
            exp_month=6,
            exp_year=2028,
            is_default=True,
        )
        self.pm.refresh_from_db()
        self.assertFalse(self.pm.is_default)
        self.assertTrue(pm2.is_default)
