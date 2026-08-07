"""Bulk-import products from a CSV/XLS/XLSX price list.

See shop/services.py (import_products_from_file) for the matching/upsert
rules — SKU-based idempotent re-import, category from sheet name/column,
price never overwritten by a price-less row, etc.
"""

from django.core.management.base import BaseCommand, CommandError

from shop.services import import_products_from_file


class Command(BaseCommand):
    help = "Importa/actualiza productos desde un archivo .csv, .xls o .xlsx."

    def add_arguments(self, parser):
        parser.add_argument("file_path", help="Ruta al archivo .csv/.xls/.xlsx a importar.")
        parser.add_argument(
            "--sheet",
            default=None,
            help="Importar solo esta hoja (xlsx). Por defecto: todas las hojas.",
        )
        parser.add_argument(
            "--category",
            default=None,
            help="Categoría a usar cuando el archivo no trae columna 'categoria' "
            "ni (para xlsx) nombre de hoja.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Reporta qué pasaría sin escribir nada en la base de datos.",
        )

    def handle(self, *args, **options):
        try:
            result = import_products_from_file(
                options["file_path"],
                default_category=options["category"],
                sheet_name=options["sheet"],
                dry_run=options["dry_run"],
            )
        except (FileNotFoundError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        prefix = "[dry-run] " if options["dry_run"] else ""
        self.stdout.write(self.style.SUCCESS(f"{prefix}Creados: {result.created}"))
        self.stdout.write(self.style.SUCCESS(f"{prefix}Actualizados: {result.updated}"))
        for row_label, message in result.errors:
            self.stderr.write(self.style.ERROR(f"{row_label}: {message}"))
        if result.errors:
            self.stdout.write(self.style.WARNING(f"Errores: {len(result.errors)}"))
