#!/usr/bin/env python
"""Translate all untranslated entries in the English .po file using DeepL."""

import os
import re
import sys
import time

# Django setup — must happen before any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myshop.settings.development")

import django  # noqa: E402

django.setup()

import polib  # noqa: E402

from shop.translation import translate_text  # noqa: E402

PO_PATH = os.path.join(
    os.path.dirname(__file__),
    "locale",
    "en",
    "LC_MESSAGES",
    "django.po",
)

# Regex patterns for Python format placeholders
BRACE_FMT = re.compile(r"\{[^}]*\}")  # {name}, {0}, {}
PERCENT_FMT = re.compile(r"%(?:\([^)]+\))?[sdifFeEgGcrboxXn%]")  # %(name)s, %s, %d


def _restore_placeholders(original: str, translated: str) -> str:
    """Make sure every placeholder from *original* appears in *translated*.

    DeepL sometimes translates or removes placeholders.  This function
    re-inserts any that went missing and removes any that were invented.
    """
    orig_brace = BRACE_FMT.findall(original)
    orig_pct = PERCENT_FMT.findall(original)

    # Restore missing brace-style placeholders
    for ph in orig_brace:
        if ph not in translated:
            translated = translated.rstrip() + " " + ph

    # Restore missing %-style placeholders
    for ph in orig_pct:
        if ph not in translated:
            translated = translated.rstrip() + " " + ph

    return translated


def main() -> None:
    po = polib.pofile(PO_PATH)
    untranslated = po.untranslated_entries()
    total = len(untranslated)

    if total == 0:
        print("All entries are already translated.")
        return

    print(f"Found {total} untranslated entries. Starting translation…\n")

    translated_count = 0
    errors = 0
    batch_size = 10

    for i, entry in enumerate(untranslated, 1):
        msgid = entry.msgid
        if not msgid.strip():
            continue

        try:
            result = translate_text(msgid, target_lang="EN", source_lang="ES")
            if result and result != msgid:
                result = _restore_placeholders(msgid, result)
                entry.msgstr = result
                translated_count += 1
            else:
                # DeepL returned the same text — it's likely already English
                entry.msgstr = msgid
                translated_count += 1
        except Exception as exc:
            print(f"  ✗ Error translating entry {i}: {exc}")
            errors += 1

        # Progress reporting every batch
        if i % batch_size == 0 or i == total:
            print(f"  [{i}/{total}] Translated so far: {translated_count} | Errors: {errors}")

        # Rate-limit to be kind to the free API
        time.sleep(0.1)

    po.save()
    print(f"\n✓ Saved {PO_PATH}")
    print(f"  Translated: {translated_count}")
    print(f"  Errors: {errors}")


if __name__ == "__main__":
    main()
