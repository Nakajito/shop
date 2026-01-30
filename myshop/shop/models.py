from django.db import models
from django.urls import reverse


class Category(models.Model):
    """
    Model representing a product category.

    Categories are used to organize products and filter the product list view.
    The 'slug' field is used for SEO-friendly URLs.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """
        Return the canonical URL for the category detail view.

        Returns:
            str: URL pattern resolving to 'shop:product_list_by_category'.
        """
        return reverse("shop:product_list_by_category", args=[self.slug])


class Product(models.Model):
    """
    Model representing an item for sale in the shop.

    Includes fields for pricing, availability status, and images. The indexes
    are optimized for common queries: retrieving by ID/slug (detail view),
    sorting by name, or displaying the newest items first.
    """

    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    image = models.ImageField(upload_to="products/%Y/%m/%d", blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            # Index for looking up specific products by ID and Slug (Detail View)
            models.Index(fields=["id", "slug"]),
            models.Index(fields=["name"]),
            # Index for filtering/sorting by newest products
            models.Index(fields=["-created"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """
        Return the canonical URL for the product detail view.

        Returns:
            str: URL pattern resolving to 'shop:product_detail'.
        """
        return reverse("shop:product_detail", args=[self.id, self.slug])
