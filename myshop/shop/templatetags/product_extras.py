import re

from django import template

register = template.Library()

_SECTION_LABELS = {
    "ingredients": "Ingredientes:",
    "nutrition": "Declaración nutrimental:",
}
_SPLIT_RE = re.compile(
    r"\n\n(?=Ingredientes:|Declaración nutrimental:)"
)


@register.filter
def split_description(text):
    """Split the description blob built by shop.services into named sections.

    Returns a dict with 'description', 'ingredients', 'nutrition' — any
    section not present in the text is an empty string.
    """
    sections = {"description": "", "ingredients": "", "nutrition": ""}
    if not text:
        return sections

    parts = _SPLIT_RE.split(text)
    for part in parts:
        part = part.strip()
        if part.startswith(_SECTION_LABELS["ingredients"]):
            sections["ingredients"] = part[len(_SECTION_LABELS["ingredients"]):].strip()
        elif part.startswith(_SECTION_LABELS["nutrition"]):
            sections["nutrition"] = part[len(_SECTION_LABELS["nutrition"]):].strip()
        else:
            sections["description"] = part

    return sections
