import logging

import requests
from django.conf import settings
from django.utils.translation import get_language

logger = logging.getLogger(__name__)

DEEPL_FREE_URL = "https://api-free.deepl.com/v2/translate"
DEEPL_PRO_URL = "https://api.deepl.com/v2/translate"


def _endpoint(api_key):
    if api_key.endswith(":fx"):
        return DEEPL_FREE_URL
    return DEEPL_PRO_URL


def translate_text(text, target_lang="EN", source_lang="ES"):
    """Translate ``text`` using the DeepL REST API.

    Returns the original text unchanged when no API key is configured or when
    the request fails, so the site degrades gracefully.
    """
    api_key = getattr(settings, "DEEPL_API_KEY", "")
    if not api_key or not text or not text.strip():
        return text

    data = {
        "text": text,
        "target_lang": target_lang.upper(),
    }
    if source_lang:
        data["source_lang"] = source_lang.upper()
    if "<" in text and ">" in text:
        data["tag_handling"] = "html"

    headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}

    try:
        response = requests.post(_endpoint(api_key), data=data, headers=headers, timeout=10)
        response.raise_for_status()
        payload = response.json()
        translations = payload.get("translations") or []
        if translations:
            return translations[0].get("text", text)
    except (requests.RequestException, ValueError) as exc:
        logger.warning("DeepL translation failed: %s", exc)
    return text


def get_translation(text, target_lang=None, source_lang="ES"):
    """Return cached/dynamic translation of ``text`` for the active language.

    When the active language is the source language (Spanish) the text is
    returned untouched. Otherwise the :class:`~shop.models.TranslationCache`
    table is used as a persistent cache in front of DeepL.
    """
    if not text or not text.strip():
        return text

    if target_lang is None:
        target_lang = (get_language() or "es").split("-")[0]

    target_lang = target_lang.lower()
    if target_lang == source_lang.lower():
        return text

    from shop.models import TranslationCache

    cached = TranslationCache.get_cached(text, source_lang, target_lang)
    if cached is not None:
        return cached

    translated = translate_text(text, target_lang=target_lang, source_lang=source_lang)
    TranslationCache.store(text, source_lang, target_lang, translated)
    return translated
