"""Re-encode every existing product/category/blog/profile image as WebP.

One-off backfill for the pre_save WebP hooks in shop/signals.py,
blog/signals.py and accounts/signals.py, which only cover new uploads.
Run once after deploying those hooks to normalize the existing media
library; safe to re-run afterwards since already-``.webp`` files are
skipped.
"""

from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from blog.models import Post, PostImage
from myshop.utils import WEBP_MAX_DIMENSION, WEBP_QUALITY, compress_image_to_webp
from shop.models import Category, Product, ProductImage

IMAGE_FIELDS = [
    (Category, "image"),
    (Product, "image"),
    (ProductImage, "image"),
    (Post, "cover_image"),
    (PostImage, "image"),
    (UserProfile, "profile_picture"),
]


class Command(BaseCommand):
    help = "Re-encode existing product/category/blog/profile images to compressed WebP."

    def add_arguments(self, parser):
        parser.add_argument(
            "--quality",
            type=int,
            default=WEBP_QUALITY,
            help=f"WebP quality 0-100 (default: {WEBP_QUALITY}).",
        )
        parser.add_argument(
            "--max-dimension",
            type=int,
            default=WEBP_MAX_DIMENSION,
            help=f"Longest side in px after downscaling (default: {WEBP_MAX_DIMENSION}).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing or deleting any files.",
        )

    def handle(self, *args, **options):
        quality = options["quality"]
        max_dimension = options["max_dimension"]
        dry_run = options["dry_run"]
        converted = skipped = failed = 0

        for model, field_name in IMAGE_FIELDS:
            for obj in model.objects.all():
                field_file = getattr(obj, field_name)
                if not field_file or not field_file.name:
                    continue
                if field_file.name.lower().endswith(".webp"):
                    skipped += 1
                    continue

                label = f"{model.__name__}#{obj.pk}.{field_name}"
                old_name = field_file.name

                try:
                    field_file.open("rb")
                    try:
                        compressed = compress_image_to_webp(
                            field_file, quality=quality, max_dimension=max_dimension
                        )
                    finally:
                        field_file.close()
                except Exception as exc:  # noqa: BLE001 - report and keep going
                    failed += 1
                    self.stderr.write(self.style.ERROR(f"{label}: FAILED ({exc})"))
                    continue

                if compressed is None:
                    skipped += 1
                    continue

                if dry_run:
                    self.stdout.write(f"[dry-run] {label}: {old_name} -> {compressed.name}")
                    converted += 1
                    continue

                field_file.save(compressed.name, compressed, save=False)
                obj.save(update_fields=[field_name])
                if old_name != field_file.name:
                    field_file.storage.delete(old_name)
                self.stdout.write(self.style.SUCCESS(f"{label}: {old_name} -> {field_file.name}"))
                converted += 1

        self.stdout.write(
            self.style.NOTICE(f"Done. Converted: {converted}, skipped: {skipped}, failed: {failed}")
        )
