from django import template
from django.utils.safestring import mark_safe

from shop.translation import get_translation

register = template.Library()


@register.filter(name="tr")
def tr(value):
    """Dynamically translate database content to the active language.

    Spanish (source) is returned unchanged. For other languages the value is
    translated through the cached DeepL service.
    """
    if value is None:
        return value
    return get_translation(str(value))


@register.filter(name="tr_safe", is_safe=True)
def tr_safe(value):
    """Like :func:`tr` but marks the result as safe HTML."""
    if value is None:
        return value
    return mark_safe(get_translation(str(value)))
