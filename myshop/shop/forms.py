from django import forms
from django.utils.translation import gettext_lazy as _

ALLOWED_IMPORT_EXTENSIONS = (".csv", ".xls", ".xlsx")


class ProductImportForm(forms.Form):
    """Upload form backing the admin's "Importar productos" action."""

    file = forms.FileField(
        label=_("Archivo de productos"),
        help_text=_("Formatos aceptados: .csv, .xls, .xlsx"),
    )
    category = forms.CharField(
        label=_("Categoría por defecto"),
        required=False,
        help_text=_(
            "Se usa solo si el archivo no trae columna 'categoria' ni (para xlsx) nombre de hoja."
        ),
    )
    sheet = forms.CharField(
        label=_("Hoja específica (xlsx)"),
        required=False,
        help_text=_("Deja vacío para importar todas las hojas del archivo."),
    )
    dry_run = forms.BooleanField(
        label=_("Solo simular (no guardar cambios)"),
        required=False,
        initial=False,
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if not uploaded.name.lower().endswith(ALLOWED_IMPORT_EXTENSIONS):
            raise forms.ValidationError(
                _("Formato no soportado. Usa un archivo .csv, .xls o .xlsx.")
            )
        return uploaded
