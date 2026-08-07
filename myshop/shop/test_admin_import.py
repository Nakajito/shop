"""Tests for shop/forms.ProductImportForm and the admin import view/URL."""

import csv
import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from shop.forms import ProductImportForm
from shop.models import Product

User = get_user_model()


def _csv_upload(rows, header, filename="productos.csv"):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    return SimpleUploadedFile(filename, buffer.getvalue().encode("utf-8"), content_type="text/csv")


class ProductImportFormTests(TestCase):
    def test_accepts_csv_xls_xlsx_extensions(self):
        for filename in ("a.csv", "b.xls", "c.xlsx", "d.CSV"):
            upload = SimpleUploadedFile(filename, b"contenido")
            form = ProductImportForm(data={}, files={"file": upload})
            self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_unsupported_extension(self):
        upload = SimpleUploadedFile("productos.pdf", b"contenido")
        form = ProductImportForm(data={}, files={"file": upload})
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)


class ProductImportAdminViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="staffuser", password="staffpass123", is_staff=True, is_superuser=True
        )
        self.regular_user = User.objects.create_user(username="regular", password="regularpass123")
        self.import_url = reverse("admin:shop_product_import")

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.import_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_non_staff_is_redirected(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(self.import_url)
        self.assertEqual(response.status_code, 302)

    def test_staff_can_load_the_form(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(self.import_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_changelist_links_to_import_view(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("admin:shop_product_changelist"))
        self.assertContains(response, self.import_url)

    def test_post_valid_csv_creates_products_and_shows_result(self):
        self.client.force_login(self.staff_user)
        upload = _csv_upload(
            [["TST001", "Kimchi Clasico 500g", "Fermentados", "120.50", "Rico"]],
            ["SKU", "Producto", "Categoria", "Precio", "Descripcion"],
        )
        response = self.client.post(
            self.import_url,
            {"file": upload, "category": "", "sheet": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 1)
        self.assertContains(response, "1")

    def test_post_dry_run_does_not_persist(self):
        self.client.force_login(self.staff_user)
        upload = _csv_upload(
            [["TST001", "Kimchi Clasico 500g", "Fermentados", "120.50", "Rico"]],
            ["SKU", "Producto", "Categoria", "Precio", "Descripcion"],
        )
        response = self.client.post(
            self.import_url,
            {"file": upload, "category": "", "sheet": "", "dry_run": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)

    def test_post_invalid_extension_reshows_form_with_error(self):
        self.client.force_login(self.staff_user)
        upload = SimpleUploadedFile("productos.pdf", b"contenido")
        response = self.client.post(self.import_url, {"file": upload})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertContains(response, "Formato no soportado")
