#!/bin/sh
#
# Refresh the message catalogs after adding or changing {% trans %} / gettext
# strings, then commit the updated myshop/locale/**/django.po.
#
#   1. makemessages   -> extract new/changed strings into en/django.po
#   2. translate_po   -> fill untranslated entries via DeepL (needs DEEPL_API_KEY)
#   3. compilemessages -> build the .mo files locally for a quick check
#
# The DEPLOY does not run steps 1-2. It only needs the committed .po files:
# the Docker image's start command already runs `manage.py compilemessages`
# on every boot (see Dockerfile), so pushing an updated django.po is all it
# takes for new translations to go live. Machine-translating at deploy time
# would mean non-deterministic builds and a DeepL call on every release.
#
# Usage:  make translations       (or)   sh scripts/update-translations.sh
#
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PROJECT_DIR="$REPO_ROOT/myshop"
cd "$PROJECT_DIR"

# --- pick an interpreter: project venv first, then uv, then bare python ----
if [ -x ".venv/Scripts/python.exe" ]; then
    PY=".venv/Scripts/python.exe"           # Windows venv layout
elif [ -x ".venv/bin/python" ]; then
    PY=".venv/bin/python"                   # POSIX venv layout
elif command -v uv >/dev/null 2>&1; then
    PY="uv run python"
else
    PY="python"
fi
echo "Interpreter: $PY"

# translate_po.py prints non-latin-1 glyphs; force UTF-8 so it doesn't crash
# when stdout is a pipe / a legacy-codepage console (Git Bash on Windows).
export PYTHONIOENCODING="utf-8"
export PYTHONUTF8="1"

# Settings module + dummy values for the vars base.py has no default for.
# makemessages / translate_po / compilemessages never touch Stripe, email or
# the database, so CI-style dummies keep this runnable from any shell — not
# just the one where the real secrets are exported.
export DJANGO_SETTINGS_MODULE="myshop.settings.testing"
export STRIPE_PUBLISHABLE_KEY="${STRIPE_PUBLISHABLE_KEY:-pk_test_dummy}"
export STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-sk_test_dummy}"
export STRIPE_API_VERSION="${STRIPE_API_VERSION:-2024-04-10}"
export STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET:-whsec_dummy}"
export EMAIL_HOST_USER="${EMAIL_HOST_USER:-dev@example.com}"
export EMAIL_HOST_PASSWORD="${EMAIL_HOST_PASSWORD:-dummy}"
export DEFAULT_FROM_EMAIL="${DEFAULT_FROM_EMAIL:-dev@example.com}"

echo "==> 1/3  makemessages -l en"
$PY manage.py makemessages -l en

echo "==> 2/3  translate_po.py (DeepL)"
if grep -q '^DEEPL_API_KEY=..*' .env 2>/dev/null || [ -n "${DEEPL_API_KEY:-}" ]; then
    $PY translate_po.py
else
    echo "    DEEPL_API_KEY not set — skipping auto-translation."
    echo "    Fill myshop/locale/en/LC_MESSAGES/django.po by hand, then re-run."
fi

echo "==> 3/3  compilemessages -l en"
$PY manage.py compilemessages -l en --ignore=.venv

cat <<'EOF'

Done. Review and commit the catalog (the .mo files are git-ignored and get
rebuilt on deploy):

    git diff -- myshop/locale/en/LC_MESSAGES/django.po
    git add   myshop/locale/en/LC_MESSAGES/django.po
EOF
