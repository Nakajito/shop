from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from shop.models import Category, Product, ProductImage


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics", slug="electronics")

    def test_str(self):
        self.assertEqual(str(self.category), "Electronics")

    def test_get_absolute_url(self):
        url = self.category.get_absolute_url()
        self.assertEqual(url, reverse("shop:product_list_by_category", args=["electronics"]))


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Books", slug="books")
        self.product = Product.objects.create(
            category=self.category,
            name="Django Book",
            slug="django-book",
            price=Decimal("29.99"),
            available=True,
        )

    def test_str(self):
        self.assertEqual(str(self.product), "Django Book")

    def test_get_absolute_url(self):
        url = self.product.get_absolute_url()
        self.assertEqual(
            url, reverse("shop:product_detail", args=["django-book"])
        )

    def test_price_non_negative_constraint(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                category=self.category,
                name="Bad Product",
                slug="bad-product",
                price=Decimal("-5.00"),
                available=True,
            )


class ProductManagerTest(TestCase):
    def setUp(self):
        self.cat1 = Category.objects.create(name="Cat1", slug="cat1")
        self.cat2 = Category.objects.create(name="Cat2", slug="cat2")
        self.p1 = Product.objects.create(
            category=self.cat1, name="P1", slug="p1", price=Decimal("10"), available=True
        )
        self.p2 = Product.objects.create(
            category=self.cat1, name="P2", slug="p2", price=Decimal("20"), available=False
        )
        self.p3 = Product.objects.create(
            category=self.cat2, name="P3", slug="p3", price=Decimal("30"), available=True
        )

    def test_available(self):
        qs = Product.objects.available()
        self.assertEqual(qs.count(), 2)
        self.assertNotIn(self.p2, qs)

    def test_by_category(self):
        qs = Product.objects.by_category(self.cat1)
        self.assertEqual(qs.count(), 2)

    def test_with_category(self):
        qs = Product.objects.with_category()
        # Should not cause extra queries when accessing .category
        product = qs.first()
        self.assertIsNotNone(product.category)


class ProductListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Tech", slug="tech")
        self.product = Product.objects.create(
            category=self.category,
            name="Laptop",
            slug="laptop",
            price=Decimal("999.99"),
            available=True,
        )
        self.unavailable = Product.objects.create(
            category=self.category,
            name="Old Phone",
            slug="old-phone",
            price=Decimal("99.99"),
            available=False,
        )

    def test_product_list(self):
        response = self.client.get(reverse("shop:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laptop")
        self.assertNotContains(response, "Old Phone")

    def test_product_list_by_category(self):
        response = self.client.get(
            reverse("shop:product_list_by_category", args=["tech"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laptop")

    def test_product_list_invalid_category(self):
        response = self.client.get(
            reverse("shop:product_list_by_category", args=["nonexistent"])
        )
        self.assertEqual(response.status_code, 404)


class ProductDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Games", slug="games")
        self.product = Product.objects.create(
            category=self.category,
            name="Chess Set",
            slug="chess-set",
            price=Decimal("49.99"),
            available=True,
        )

    def test_product_detail(self):
        response = self.client.get(
            reverse("shop:product_detail", args=["chess-set"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chess Set")

    def test_product_detail_unavailable(self):
        self.product.available = False
        self.product.save()
        response = self.client.get(
            reverse("shop:product_detail", args=["chess-set"])
        )
        self.assertEqual(response.status_code, 404)

    def test_product_detail_gallery_single_image(self):
        """Gallery renders one slide (active) and no arrows/dots."""
        response = self.client.get(
            reverse("shop:product_detail", args=["chess-set"])
        )
        self.assertContains(response, 'pd-carousel__slide--active')
        self.assertContains(response, 'pd-carousel__slides')
        # Arrows should NOT be rendered in HTML (no images)
        self.assertNotContains(response, 'aria-label="Anterior"')
        self.assertNotContains(response, 'aria-label="Siguiente"')
        # Gallery JS should exist
        self.assertContains(response, 'function goTo(')

    def test_product_detail_gallery_multi_image(self):
        """Gallery renders slides, arrows, and dots when images exist."""
        img = SimpleUploadedFile("test.png", b"fake-image-data", content_type="image/png")
        ProductImage.objects.create(product=self.product, image=img, order=0)
        ProductImage.objects.create(product=self.product, image=img, order=1)
        response = self.client.get(
            reverse("shop:product_detail", args=["chess-set"])
        )
        self.assertContains(response, 'pd-carousel__slide--active')
        self.assertContains(response, 'aria-label="Anterior"')
        self.assertContains(response, 'aria-label="Siguiente"')
        self.assertContains(response, 'function goTo(')
        # Arrows rendered as HTML buttons (not just JS references)
        self.assertContains(response, '<button class="pd-carousel__arrow pd-carousel__arrow--prev"')
        self.assertContains(response, '<button class="pd-carousel__arrow pd-carousel__arrow--next"')
        # Dots rendered
        self.assertContains(response, 'data-index="1"')
        self.assertContains(response, 'data-index="2"')
