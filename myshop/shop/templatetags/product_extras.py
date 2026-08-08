import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

_SECTION_LABELS = {
    "ingredients": "Ingredientes:",
    "nutrition": "Declaración nutrimental:",
}
_SPLIT_RE = re.compile(
    r"\n\n(?=Ingredientes:|Declaración nutrimental:)"
)
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


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


@register.filter
def bold_lead(text):
    """Wrap the first sentence of ``text`` in <strong> as a visual hook."""
    if not text:
        return text
    parts = _SENTENCE_END_RE.split(text, maxsplit=1)
    lead = escape(parts[0])
    rest = escape(parts[1]) if len(parts) > 1 else ""
    html = f"<strong>{lead}</strong>"
    if rest:
        html += f" {rest}"
    return mark_safe(html)
