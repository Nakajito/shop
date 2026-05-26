from django.test import RequestFactory, TestCase

from myshop.utils import safe_next_url


class SafeNextUrlTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_fallback_when_no_next(self):
        request = self.factory.get("/some/path")
        self.assertEqual(safe_next_url(request, "shop:product_list"), "shop:product_list")

    def test_returns_same_host_path(self):
        request = self.factory.get("/some/path?next=/orders/history/")
        self.assertEqual(safe_next_url(request, "fb"), "/orders/history/")

    def test_blocks_external_url(self):
        request = self.factory.get("/x?next=https://evil.example.com/steal")
        self.assertEqual(safe_next_url(request, "fb"), "fb")

    def test_blocks_protocol_relative_url(self):
        request = self.factory.get("/x?next=//evil.example.com/steal")
        self.assertEqual(safe_next_url(request, "fb"), "fb")

    def test_reads_from_post_when_no_get(self):
        request = self.factory.post("/x", {"next": "/orders/history/"})
        self.assertEqual(safe_next_url(request, "fb"), "/orders/history/")
