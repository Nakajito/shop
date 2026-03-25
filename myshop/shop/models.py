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
    slug = models.SlugField(max_length=200, db_index=True)
    image = models.ImageField(
        _("image"), upload_to="products/%Y/%m/%d", blank=True, null=True
    )
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
        return reverse("shop:product_detail", args=[self.id, self.slug])
