"""Project-wide utility helpers (no Django app — pure functions)."""

from io import BytesIO
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.utils.http import url_has_allowed_host_and_scheme
from PIL import Image, ImageOps


def safe_next_url(request, fallback):
    """Return ``?next=`` (or ``next`` POST field) only if same-host + scheme.

    Prevents open-redirect via attacker-controlled ``next=https://evil/...``.
    Falls back to ``fallback`` (any value accepted by ``django.shortcuts.redirect``)
    when the supplied URL is missing or not allowed.
    """
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback


WEBP_QUALITY = 80
WEBP_MAX_DIMENSION = 1600


def compress_image_to_webp(source_file, quality=WEBP_QUALITY, max_dimension=WEBP_MAX_DIMENSION):
    """Re-encode an image file as compressed WebP.

    ``source_file`` must be a readable, seekable file-like object with a
    ``.name`` (a Django ``File``/``FieldFile``/``UploadedFile``). Downscales
    so the longest side is at most ``max_dimension`` px. Returns a
    ``ContentFile`` named ``<original-basename>.webp``, or ``None`` if
    ``source_file`` is falsy.
    """
    if not source_file:
        return None

    source_file.seek(0)
    image = ImageOps.exif_transpose(Image.open(source_file))

    if image.mode in ("P", "LA"):
        image = image.convert("RGBA")
    elif image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    image.save(buffer, format="WEBP", quality=quality, method=6)

    base_name = PurePosixPath(source_file.name).stem
    return ContentFile(buffer.getvalue(), name=f"{base_name}.webp")


def replace_with_webp(instance, field_name, quality=WEBP_QUALITY, max_dimension=WEBP_MAX_DIMENSION):
    """Swap a model's pending (uncommitted) image upload for a compressed WebP version.

    Connect to ``pre_save`` for any model with an ``ImageField`` so every
    upload — from the admin or anywhere else — is normalized to WebP before
    it reaches storage. Saves that don't touch the field (the file is already
    committed) are left untouched, so this is safe to run on every save.
    """
    field_file = getattr(instance, field_name)
    if not field_file or getattr(field_file, "_committed", True):
        return

    try:
        compressed = compress_image_to_webp(
            field_file, quality=quality, max_dimension=max_dimension
        )
    except OSError:
        # Not decodable as an image (e.g. corrupt upload, or non-form paths
        # like fixtures/tests that bypass ImageField's own PIL validation).
        # Leave the original file untouched rather than blocking the save.
        return

    if compressed is not None:
        setattr(instance, field_name, compressed)
