import hashlib

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from shop.managers import ProductManager


class Category(models.Model):
    """
    Model representing a product category.
    """

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(_("image"), upload_to="categories/%Y/%m/%d", blank=True, null=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """
        Return the canonical URL for the category detail view.
        """
        return reverse("shop:product_list_by_category", args=[self.slug])


class Product(models.Model):
    """
    Model representing an item for sale in the shop.
    """

    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE,
        verbose_name=_("category"),
    )
    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    sku = models.CharField(_("sku"), max_length=64, unique=True, blank=True, null=True)
    image = models.ImageField(_("image"), upload_to="products/%Y/%m/%d", blank=True, null=True)
    description = models.TextField(_("description"), blank=True)
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=2)
    available = models.BooleanField(_("available"), default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    class Meta:
        ordering = ["name"]
        verbose_name = _("product")
        verbose_name_plural = _("products")
        indexes = [
            models.Index(fields=["id", "slug"]),
            models.Index(fields=["name"]),
            models.Index(fields=["-created"]),
            models.Index(fields=["available"]),
            models.Index(fields=["category", "available"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name="product_price_non_negative",
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """
        Return the canonical URL for the product detail view.
        """
        return reverse("shop:product_detail", args=[self.slug])


class ProductImage(models.Model):
    """
    Additional image for a product, used to build the detail page carousel.
    """

    product = models.ForeignKey(
        Product,
        related_name="images",
        on_delete=models.CASCADE,
        verbose_name=_("product"),
    )
    image = models.ImageField(_("image"), upload_to="products/%Y/%m/%d")
    alt_text = models.CharField(_("alt text"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("order"), default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("product image")
        verbose_name_plural = _("product images")
        indexes = [
            models.Index(fields=["product", "order"]),
        ]

    def __str__(self):
        return f"{self.product.name} ({self.pk})"


class TranslationCache(models.Model):
    """Persistent cache of dynamic (database) content translations."""

    source_hash = models.CharField(max_length=64, db_index=True)
    source_lang = models.CharField(max_length=5)
    target_lang = models.CharField(max_length=5)
    source_text = models.TextField()
    translated_text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("translation cache")
        verbose_name_plural = _("translation cache")
        constraints = [
            models.UniqueConstraint(
                fields=["source_hash", "source_lang", "target_lang"],
                name="unique_translation_entry",
            ),
        ]
        indexes = [
            models.Index(fields=["source_hash", "source_lang", "target_lang"]),
        ]

    def __str__(self):
        return f"{self.source_lang}->{self.target_lang}: {self.source_text[:30]}"

    @staticmethod
    def make_hash(text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached(cls, text, source_lang, target_lang):
        entry = cls.objects.filter(
            source_hash=cls.make_hash(text),
            source_lang=source_lang.lower(),
            target_lang=target_lang.lower(),
        ).first()
        return entry.translated_text if entry else None

    @classmethod
    def store(cls, text, source_lang, target_lang, translated_text):
        return cls.objects.update_or_create(
            source_hash=cls.make_hash(text),
            source_lang=source_lang.lower(),
            target_lang=target_lang.lower(),
            defaults={
                "source_text": text,
                "translated_text": translated_text,
            },
        )[0]
