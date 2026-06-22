from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from shop.translation import translate_text

try:
    import polib
except ImportError:  # pragma: no cover
    polib = None


class Command(BaseCommand):
    help = (
        "Fill empty msgstr entries in a .po file using the DeepL API. "
        "Run makemessages first, then this command, then compilemessages."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--lang",
            default="en",
            help="Target language code of the .po file (default: en).",
        )
        parser.add_argument(
            "--source-lang",
            default="es",
            help="Source language code (default: es).",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Re-translate entries that already have a msgstr.",
        )

    def handle(self, *args, **options):
        if polib is None:
            self.stderr.write(
                self.style.ERROR(
                    "polib is required. Install it with: pip install polib"
                )
            )
            return

        if not getattr(settings, "DEEPL_API_KEY", ""):
            self.stderr.write(
                self.style.ERROR(
                    "DEEPL_API_KEY is not configured. Set it before running."
                )
            )
            return

        lang = options["lang"]
        source_lang = options["source_lang"]
        overwrite = options["overwrite"]

        locale_dir = Path(settings.LOCALE_PATHS[0])
        po_path = locale_dir / lang / "LC_MESSAGES" / "django.po"
        if not po_path.exists():
            self.stderr.write(
                self.style.ERROR(f"PO file not found: {po_path}")
            )
            return

        po = polib.pofile(str(po_path))
        translated = 0
        for entry in po:
            if entry.obsolete or entry.msgid_plural:
                continue
            if entry.msgstr and not overwrite:
                continue
            if not entry.msgid.strip():
                continue
            result = translate_text(
                entry.msgid,
                target_lang=lang,
                source_lang=source_lang,
            )
            if result and result != entry.msgid:
                entry.msgstr = result
                translated += 1
                if "fuzzy" in entry.flags:
                    entry.flags.remove("fuzzy")

        po.save(str(po_path))
        self.stdout.write(
            self.style.SUCCESS(
                f"Translated {translated} entries in {po_path}. "
                "Now run: python manage.py compilemessages"
            )
        )
