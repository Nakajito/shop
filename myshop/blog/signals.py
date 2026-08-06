from django.db.models.signals import pre_save
from django.dispatch import receiver

from myshop.utils import replace_with_webp

from .models import Post, PostImage


@receiver(pre_save, sender=Post)
def compress_post_cover_image(sender, instance, **kwargs):
    replace_with_webp(instance, "cover_image")


@receiver(pre_save, sender=PostImage)
def compress_post_gallery_image(sender, instance, **kwargs):
    replace_with_webp(instance, "image")
