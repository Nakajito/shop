from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from myshop.utils import replace_with_webp

from .models import Category, Product, ProductImage


@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, **kwargs):
    cache.clear()


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, **kwargs):
    cache.clear()


@receiver(pre_save, sender=Product)
def compress_product_image(sender, instance, **kwargs):
    replace_with_webp(instance, "image")


@receiver(pre_save, sender=Category)
def compress_category_image(sender, instance, **kwargs):
    replace_with_webp(instance, "image")


@receiver(pre_save, sender=ProductImage)
def compress_product_gallery_image(sender, instance, **kwargs):
    replace_with_webp(instance, "image")
