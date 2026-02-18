from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from coupons.models import Coupon
from coupons.forms import CouponApplyForm


class CouponModelTest(TestCase):
    def test_create_coupon(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="SUMMER20",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
            discount=20,
            active=True,
        )
        self.assertEqual(coupon.discount, 20)
        self.assertTrue(coupon.active)

    def test_str(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="TEST10",
            valid_from=now,
            valid_to=now + timedelta(days=1),
            discount=10,
            active=True,
        )
        self.assertEqual(str(coupon), "TEST10 (10%)")

    def test_clean_invalid_dates(self):
        from django.core.exceptions import ValidationError
        now = timezone.now()
        coupon = Coupon(
            code="INVALID",
            valid_from=now + timedelta(days=10),
            valid_to=now - timedelta(days=10),
            discount=15,
            active=True,
        )
        with self.assertRaises(ValidationError):
            coupon.clean()


class CouponApplyFormTest(TestCase):
    def test_clean_code_strips_whitespace(self):
        form = CouponApplyForm(data={"code": "  SUMMER20  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["code"], "SUMMER20")

    def test_empty_code_invalid(self):
        form = CouponApplyForm(data={"code": ""})
        self.assertFalse(form.is_valid())


class CouponApplyViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        now = timezone.now()
        self.valid_coupon = Coupon.objects.create(
            code="VALID20",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
            discount=20,
            active=True,
        )
        self.expired_coupon = Coupon.objects.create(
            code="EXPIRED",
            valid_from=now - timedelta(days=30),
            valid_to=now - timedelta(days=1),
            discount=10,
            active=True,
        )

    def test_apply_valid_coupon(self):
        response = self.client.post(
            reverse("coupons:apply"),
            {"code": "VALID20"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session.get("coupon_id"), self.valid_coupon.id
        )

    def test_apply_expired_coupon(self):
        response = self.client.post(
            reverse("coupons:apply"),
            {"code": "EXPIRED"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.client.session.get("coupon_id"))

    def test_apply_nonexistent_coupon(self):
        response = self.client.post(
            reverse("coupons:apply"),
            {"code": "DOESNOTEXIST"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.client.session.get("coupon_id"))

    def test_get_not_allowed(self):
        response = self.client.get(reverse("coupons:apply"))
        self.assertEqual(response.status_code, 405)
