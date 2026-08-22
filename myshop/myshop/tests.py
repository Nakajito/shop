import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

CustomUser = get_user_model()


class CspReportViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_valid_report_returns_204(self):
        payload = {
            "csp-report": {
                "document-uri": "https://example.com/",
                "violated-directive": "script-src-attr",
                "blocked-uri": "inline",
            }
        }
        response = self.client.post(
            reverse("csp_report"),
            data=json.dumps(payload),
            content_type="application/csp-report",
        )
        self.assertEqual(response.status_code, 204)

    def test_malformed_body_does_not_500(self):
        """A10: untrusted browser input must never turn into a 500."""
        response = self.client.post(
            reverse("csp_report"),
            data=b"not json at all",
            content_type="application/csp-report",
        )
        self.assertEqual(response.status_code, 204)

    def test_get_not_allowed(self):
        response = self.client.get(reverse("csp_report"))
        self.assertEqual(response.status_code, 405)


class AdminAccessMiddlewareTest(TestCase):
    """A01/A07 — the admin login form must not be visible to anyone who
    isn't already an authenticated staff user (myshop/middleware.py)."""

    def setUp(self):
        self.client = Client()

    def test_anonymous_gets_404_on_admin_root(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 404)

    def test_anonymous_gets_404_on_admin_login(self):
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 404)

    def test_regular_authenticated_user_gets_404(self):
        CustomUser.objects.create_user(username="regular", password="testpass123")
        self.client.login(username="regular", password="testpass123")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 404)

    def test_inactive_staff_gets_404(self):
        user = CustomUser.objects.create_user(
            username="inactivestaff", password="testpass123", is_staff=True
        )
        self.client.force_login(user)
        user.is_active = False
        user.save(update_fields=["is_active"])
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 404)

    def test_staff_user_can_access_admin(self):
        user = CustomUser.objects.create_user(
            username="staffuser", password="testpass123", is_staff=True
        )
        self.client.force_login(user)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    def test_non_admin_paths_unaffected(self):
        response = self.client.get("/es/")
        self.assertEqual(response.status_code, 200)
