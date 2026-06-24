"""Tests for the dynamic translation system (DeepL + TranslationCache).

Covers:
- TranslationCache model (store, get_cached, hash)
- get_translation() pipeline (cache hit, cache miss, same-lang bypass)
- translate_text() API call (mocked)
- Template filter |tr (mocked)
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.utils.translation import activate, deactivate

from shop.models import TranslationCache
from shop.templatetags.i18n_extras import tr, tr_safe
from shop.translation import get_translation, translate_text


class TranslationCacheModelTests(TestCase):
    """Unit tests for the TranslationCache model."""

    def test_make_hash_deterministic(self):
        """Same text always produces the same hash."""
        h1 = TranslationCache.make_hash("Comida coreana")
        h2 = TranslationCache.make_hash("Comida coreana")
        self.assertEqual(h1, h2)

    def test_make_hash_different_for_different_text(self):
        h1 = TranslationCache.make_hash("Comida coreana")
        h2 = TranslationCache.make_hash("Comida japonesa")
        self.assertNotEqual(h1, h2)

    def test_store_and_get_cached(self):
        """Stored translations can be retrieved via get_cached."""
        TranslationCache.store("Hola mundo", "es", "en", "Hello world")
        result = TranslationCache.get_cached("Hola mundo", "es", "en")
        self.assertEqual(result, "Hello world")

    def test_get_cached_returns_none_for_missing(self):
        result = TranslationCache.get_cached("No existe", "es", "en")
        self.assertIsNone(result)

    def test_store_updates_existing(self):
        """Storing the same text+langs again updates the translation."""
        TranslationCache.store("Hola", "es", "en", "Hello")
        TranslationCache.store("Hola", "es", "en", "Hi")
        result = TranslationCache.get_cached("Hola", "es", "en")
        self.assertEqual(result, "Hi")
        self.assertEqual(TranslationCache.objects.count(), 1)

    def test_different_target_langs_stored_separately(self):
        TranslationCache.store("Hola", "es", "en", "Hello")
        TranslationCache.store("Hola", "es", "fr", "Bonjour")
        self.assertEqual(TranslationCache.get_cached("Hola", "es", "en"), "Hello")
        self.assertEqual(TranslationCache.get_cached("Hola", "es", "fr"), "Bonjour")

    def test_str_representation(self):
        entry = TranslationCache.store("Comida coreana", "es", "en", "Korean food")
        self.assertIn("es->en", str(entry))
        self.assertIn("Comida coreana", str(entry))


class TranslateTextTests(TestCase):
    """Tests for the translate_text() function (DeepL API wrapper)."""

    @override_settings(DEEPL_API_KEY="")
    def test_returns_original_without_api_key(self):
        """When no API key is configured, returns the original text."""
        result = translate_text("Comida coreana", target_lang="EN")
        self.assertEqual(result, "Comida coreana")

    @override_settings(DEEPL_API_KEY="")
    def test_returns_empty_for_empty_text(self):
        result = translate_text("", target_lang="EN")
        self.assertEqual(result, "")

    @override_settings(DEEPL_API_KEY="test-key:fx")
    @patch("shop.translation.requests.post")
    def test_calls_deepl_free_endpoint(self, mock_post):
        """Uses free endpoint when key ends with :fx."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "translations": [{"text": "Korean food"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = translate_text("Comida coreana", target_lang="EN", source_lang="ES")

        self.assertEqual(result, "Korean food")
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        self.assertIn("api-free.deepl.com", call_url)

    @override_settings(DEEPL_API_KEY="test-key-pro")
    @patch("shop.translation.requests.post")
    def test_calls_deepl_pro_endpoint(self, mock_post):
        """Uses pro endpoint when key does NOT end with :fx."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "translations": [{"text": "Korean food"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        translate_text("Comida coreana", target_lang="EN", source_lang="ES")

        call_url = mock_post.call_args[0][0]
        self.assertIn("api.deepl.com", call_url)
        self.assertNotIn("api-free", call_url)

    @override_settings(DEEPL_API_KEY="test-key:fx")
    @patch("shop.translation.requests.post")
    def test_enables_html_tag_handling(self, mock_post):
        """Enables tag_handling=html when text contains HTML tags."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "translations": [{"text": "<p>Welcome</p>"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        translate_text("<p>Bienvenido</p>", target_lang="EN")

        call_data = mock_post.call_args[1].get("data") or mock_post.call_args[0][1]
        self.assertEqual(call_data.get("tag_handling"), "html")

    @override_settings(DEEPL_API_KEY="test-key:fx")
    @patch("shop.translation.requests.post")
    def test_graceful_degradation_on_api_error(self, mock_post):
        """Returns original text when the API raises an exception."""
        import requests as req
        mock_post.side_effect = req.RequestException("Network error")

        result = translate_text("Comida coreana", target_lang="EN")
        self.assertEqual(result, "Comida coreana")


class GetTranslationTests(TestCase):
    """Tests for the get_translation() pipeline."""

    def test_returns_text_unchanged_for_source_lang(self):
        """When target language == source language, returns text as-is."""
        activate("es")
        try:
            result = get_translation("Comida coreana")
            self.assertEqual(result, "Comida coreana")
        finally:
            deactivate()

    def test_returns_empty_for_empty_text(self):
        result = get_translation("")
        self.assertEqual(result, "")

    def test_returns_whitespace_for_whitespace(self):
        result = get_translation("   ")
        self.assertEqual(result, "   ")

    @patch("shop.translation.translate_text")
    def test_cache_miss_calls_api_and_stores(self, mock_translate):
        """On cache miss, calls DeepL and stores in TranslationCache."""
        mock_translate.return_value = "Korean food"

        result = get_translation("Comida coreana", target_lang="en")

        self.assertEqual(result, "Korean food")
        mock_translate.assert_called_once_with(
            "Comida coreana", target_lang="en", source_lang="ES"
        )
        cached = TranslationCache.get_cached("Comida coreana", "ES", "en")
        self.assertEqual(cached, "Korean food")

    @patch("shop.translation.translate_text")
    def test_cache_hit_skips_api_call(self, mock_translate):
        """When cached, returns cached value without calling DeepL."""
        TranslationCache.store("Comida coreana", "ES", "en", "Korean food")

        result = get_translation("Comida coreana", target_lang="en")

        self.assertEqual(result, "Korean food")
        mock_translate.assert_not_called()

    @patch("shop.translation.translate_text")
    def test_respects_active_language(self, mock_translate):
        """Uses Django's active language when target_lang is None."""
        mock_translate.return_value = "Korean food"
        activate("en")
        try:
            result = get_translation("Comida coreana")
            self.assertEqual(result, "Korean food")
            mock_translate.assert_called_once()
        finally:
            deactivate()


class TemplateFilterTests(TestCase):
    """Tests for the |tr and |tr_safe template filters."""

    def test_tr_returns_none_for_none(self):
        self.assertIsNone(tr(None))

    @patch("shop.templatetags.i18n_extras.get_translation")
    def test_tr_calls_get_translation(self, mock_get):
        mock_get.return_value = "Korean food"
        result = tr("Comida coreana")
        self.assertEqual(result, "Korean food")
        mock_get.assert_called_once_with("Comida coreana")

    def test_tr_safe_returns_none_for_none(self):
        self.assertIsNone(tr_safe(None))

    @patch("shop.templatetags.i18n_extras.get_translation")
    def test_tr_safe_marks_output_as_safe(self, mock_get):
        mock_get.return_value = "<p>Welcome</p>"
        result = tr_safe("<p>Bienvenido</p>")
        self.assertEqual(str(result), "<p>Welcome</p>")
        # Verify it's marked safe (won't be escaped in templates)
        self.assertTrue(hasattr(result, "__html__") or not getattr(result, "is_safe", True))
