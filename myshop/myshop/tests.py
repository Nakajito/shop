import json

from django.test import Client, TestCase
from django.urls import reverse


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
