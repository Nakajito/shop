"""Tests for the CSV/XLS/XLSX product importer (shop/services.py)."""

import csv
import io
import tempfile
from decimal import Decimal
from pathlib import Path

import openpyxl
from django.test import TestCase
from PIL import Image as PILImage

from shop.models import Category, Product
from shop.services import (
    _build_description,
    _build_field_map,
    _build_product_name,
    _get_or_create_category,
    _normalize_header,
    _parse_price,
    _resolve_category_name,
    import_products_from_file,
)


class NormalizeHeaderTests(TestCase):
    def test_strips_accents_and_case(self):
        self.assertEqual(_normalize_header("Descripción del Producto"), "descripcion del producto")

    def test_collapses_whitespace(self):
        self.assertEqual(_normalize_header("  Contenido   Neto  "), "contenido neto")

    def test_none_returns_empty_string(self):
        self.assertEqual(_normalize_header(None), "")


class BuildFieldMapTests(TestCase):
    def test_matches_known_aliases_case_and_accent_insensitively(self):
        headers = ["SKU", "Categoría", "PRECIO", "Nombre del producto", "Algo Irrelevante"]
        field_map = _build_field_map(headers)
        self.assertEqual(field_map["sku"], 0)
        self.assertEqual(field_map["category"], 1)
        self.assertEqual(field_map["price"], 2)
        self.assertEqual(field_map["producto"], 3)
        self.assertNotIn("web_title", field_map)


class ParsePriceTests(TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(_parse_price(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(_parse_price("   "))

    def test_strips_currency_symbol_and_thousands_separator(self):
        self.assertEqual(_parse_price("$1,234.56"), Decimal("1234.56"))

    def test_accepts_numeric_types(self):
        self.assertEqual(_parse_price(19.99), Decimal("19.99"))
        self.assertEqual(_parse_price(20), Decimal("20"))

    def test_invalid_text_returns_none(self):
        self.assertIsNone(_parse_price("no es un precio"))


class BuildProductNameTests(TestCase):
    def test_combines_producto_and_net_content(self):
        row = {"producto": "Coffe Mix Alba", "net_content": "30 pz"}
        self.assertEqual(_build_product_name(row), "Coffe Mix Alba 30 pz")

    def test_falls_back_to_producto_only(self):
        row = {"producto": "Kimchi", "net_content": ""}
        self.assertEqual(_build_product_name(row), "Kimchi")

    def test_falls_back_to_web_title_when_no_producto(self):
        row = {"web_title": "TITULO WEB"}
        self.assertEqual(_build_product_name(row), "TITULO WEB")

    def test_collapses_internal_newlines(self):
        row = {"producto": "MGF PEPTIDE\nEMULSION PLUS", "net_content": ""}
        self.assertEqual(_build_product_name(row), "MGF PEPTIDE EMULSION PLUS")


class BuildDescriptionTests(TestCase):
    def test_empty_row_returns_empty_string(self):
        self.assertEqual(_build_description({}), "")

    def test_combines_all_sections_with_labels(self):
        row = {
            "description": "Rico y crujiente.",
            "ingredients": "Harina, azúcar.",
            "nutrition": "100 kcal",
        }
        description = _build_description(row)
        self.assertIn("Rico y crujiente.", description)
        self.assertIn("Ingredientes: Harina, azúcar.", description)
        self.assertIn("Declaración nutrimental:\n100 kcal", description)


class ResolveCategoryNameTests(TestCase):
    def test_explicit_column_wins(self):
        row = {"category": "Snacks"}
        self.assertEqual(_resolve_category_name(row, "Hoja1", "Default"), "Snacks")

    def test_falls_back_to_sheet_name(self):
        self.assertEqual(_resolve_category_name({}, "Synk food", None), "Synk food")

    def test_falls_back_to_default_category(self):
        self.assertEqual(_resolve_category_name({}, None, "Varios"), "Varios")

    def test_raises_when_nothing_available(self):
        with self.assertRaises(ValueError):
            _resolve_category_name({}, None, None)


class GetOrCreateCategoryTests(TestCase):
    def test_creates_new_category(self):
        category = _get_or_create_category("Bebidas")
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(category.name, "Bebidas")

    def test_reuses_existing_category_case_insensitively(self):
        Category.objects.create(name="Bebidas", slug="bebidas")
        category = _get_or_create_category("BEBIDAS")
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(category.name, "Bebidas")


def _write_csv(rows, header):
    tmp = tempfile.NamedTemporaryFile(
        suffix=".csv", delete=False, mode="w", newline="", encoding="utf-8"
    )
    writer = csv.writer(tmp)
    writer.writerow(header)
    writer.writerows(rows)
    tmp.close()
    return tmp.name


class ImportFromCsvTests(TestCase):
    def test_creates_products_with_category_column(self):
        path = _write_csv(
            [
                ["TST001", "Kimchi Clasico 500g", "Fermentados", "$120.50", "Kimchi tradicional"],
                ["TST002", "Salsa Gochujang 250g", "Salsas", "", "Pasta de chile fermentada"],
            ],
            ["SKU", "Producto", "Categoria", "Precio", "Descripcion"],
        )
        try:
            result = import_products_from_file(path)
        finally:
            Path(path).unlink()

        self.assertEqual(result.created, 2)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.errors, [])

        priced = Product.objects.get(sku="TST001")
        self.assertEqual(priced.price, Decimal("120.50"))
        self.assertTrue(priced.available)
        self.assertEqual(priced.category.name, "Fermentados")

        priceless = Product.objects.get(sku="TST002")
        self.assertEqual(priceless.price, Decimal("0"))
        self.assertFalse(priceless.available)

    def test_reimport_by_sku_updates_without_duplicating_or_clobbering_price(self):
        path = _write_csv(
            [["TST001", "Kimchi Clasico 500g", "Fermentados", "", "Kimchi tradicional"]],
            ["SKU", "Producto", "Categoria", "Precio", "Descripcion"],
        )
        try:
            import_products_from_file(path)
            product = Product.objects.get(sku="TST001")
            product.price = Decimal("99.00")
            product.available = True
            product.save(update_fields=["price", "available"])

            result = import_products_from_file(path)
        finally:
            Path(path).unlink()

        self.assertEqual(result.created, 0)
        self.assertEqual(result.updated, 1)
        self.assertEqual(Product.objects.filter(sku="TST001").count(), 1)

        product.refresh_from_db()
        self.assertEqual(product.price, Decimal("99.00"))
        self.assertTrue(product.available)

    def test_dry_run_does_not_write_to_database(self):
        path = _write_csv(
            [["TST001", "Kimchi Clasico 500g", "Fermentados", "$120.50", ""]],
            ["SKU", "Producto", "Categoria", "Precio", "Descripcion"],
        )
        try:
            result = import_products_from_file(path, dry_run=True)
        finally:
            Path(path).unlink()

        self.assertEqual(result.created, 1)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 0)

    def test_row_without_category_source_is_reported_as_error(self):
        path = _write_csv(
            [["TST001", "Kimchi Clasico 500g", "$120.50", ""]],
            ["SKU", "Producto", "Precio", "Descripcion"],
        )
        try:
            result = import_products_from_file(path)
        finally:
            Path(path).unlink()

        self.assertEqual(result.created, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(Product.objects.count(), 0)

    def test_default_category_applies_when_no_category_column(self):
        path = _write_csv(
            [["TST001", "Kimchi Clasico 500g", "$120.50", ""]],
            ["SKU", "Producto", "Precio", "Descripcion"],
        )
        try:
            result = import_products_from_file(path, default_category="Varios")
        finally:
            Path(path).unlink()

        self.assertEqual(result.created, 1)
        self.assertEqual(Product.objects.get(sku="TST001").category.name, "Varios")

    def test_unsupported_extension_raises(self):
        with self.assertRaises(ValueError):
            import_products_from_file("archivo.pdf")


def _write_xlsx_with_image(sheet_rows_by_name):
    """Build a tiny xlsx with a header row + data rows + one embedded image
    anchored on the "Imagen" column of the first data row of each sheet.
    """
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)

    image_buffer = io.BytesIO()
    PILImage.new("RGB", (20, 20), color=(10, 100, 200)).save(image_buffer, format="PNG")

    for sheet_name, rows in sheet_rows_by_name.items():
        worksheet = workbook.create_sheet(title=sheet_name)
        worksheet.append(
            ["#", "Producto", "Imagen", "SKU", "Precio", "Contenido Neto", "Descripcion"]
        )
        for row in rows:
            worksheet.append(row)

        image_buffer.seek(0)
        xl_image = openpyxl.drawing.image.Image(io.BytesIO(image_buffer.getvalue()))
        xl_image.anchor = "C2"
        worksheet.add_image(xl_image)

    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    workbook.save(tmp.name)
    tmp.close()
    return tmp.name


class ImportFromXlsxTests(TestCase):
    def test_imports_all_sheets_using_sheet_name_as_category(self):
        path = _write_xlsx_with_image(
            {
                "Synk food": [
                    [1, "Ramyeon Picante", None, "RAM001", 25, "120g", "Fideos picantes"],
                    [2, "Kimchi", None, "KIM001", None, "500g", "Kimchi tradicional"],
                ],
                "Synk Beauty": [
                    [1, "Toner Facial", None, "TON001", 199.5, "100ml", "Tonico facial"],
                ],
            }
        )
        try:
            result = import_products_from_file(path)
        finally:
            Path(path).unlink()

        self.assertEqual(result.created, 3)
        self.assertEqual(result.errors, [])
        self.assertEqual(
            set(Category.objects.values_list("name", flat=True)), {"Synk food", "Synk Beauty"}
        )

        ramyeon = Product.objects.get(sku="RAM001")
        self.assertEqual(ramyeon.name, "Ramyeon Picante 120g")
        self.assertEqual(ramyeon.category.name, "Synk food")
        self.assertTrue(ramyeon.available)
        # The embedded image is extracted and passes through the WebP pipeline.
        self.assertTrue(ramyeon.image.name.endswith(".webp"))

        kimchi = Product.objects.get(sku="KIM001")
        self.assertFalse(kimchi.available)
        self.assertEqual(kimchi.price, Decimal("0"))

    def test_sheet_argument_restricts_import_to_one_sheet(self):
        path = _write_xlsx_with_image(
            {
                "Synk food": [[1, "Ramyeon", None, "RAM001", 25, "120g", ""]],
                "Synk Beauty": [[1, "Toner", None, "TON001", 199, "100ml", ""]],
            }
        )
        try:
            result = import_products_from_file(path, sheet_name="Synk food")
        finally:
            Path(path).unlink()

        self.assertEqual(result.created, 1)
        self.assertTrue(Product.objects.filter(sku="RAM001").exists())
        self.assertFalse(Product.objects.filter(sku="TON001").exists())
