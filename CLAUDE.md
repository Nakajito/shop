# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo shape

Mono-repo: tooling at the root, the Django project lives one level down in `myshop/`.
Nearly every command must run with cwd = `myshop/` (the `Makefile` targets `cd` for you).
Note the doubled name: `myshop/` is the project dir, `myshop/myshop/` is the settings/urls/celery package.

## Commands

Run from the repo root (targets `cd myshop` themselves):

```bash
make install        # uv sync + .env
make migrate
make run            # dev server :8000
make test           # full suite under settings.testing
make test-fast      # --keepdb
make coverage
make lint           # ruff check
make format         # ruff check --fix + ruff format
make check-deploy   # manage.py check --deploy against production settings
make seed           # demo data (categories + products + posts)
make celery         # worker (needs Redis)
make deps-lock      # regenerate root requirements.txt from myshop/pyproject.toml
```

Tests **require** the testing settings module — without it you hit the dev SQLite file:

```bash
cd myshop
DJANGO_SETTINGS_MODULE=myshop.settings.testing uv run python manage.py test               # all
DJANGO_SETTINGS_MODULE=myshop.settings.testing uv run python manage.py test orders        # one app
DJANGO_SETTINGS_MODULE=myshop.settings.testing uv run python manage.py test \
    orders.tests.test_services.OrderServiceTest.test_create_order_from_cart               # one test
```

CI (`.github/workflows/ci.yml`, on push/PR to `main`/`dev`) runs `ruff check`, `manage.py check`,
then `coverage run manage.py test` with `--fail-under=78`. Coverage is scoped to the eight local
apps only (see `[tool.coverage.run]` in `pyproject.toml`). Ruff: line-length 100, py313,
`E,F,W,I,B,DJ,UP`, migrations excluded. `pre-commit` also runs ruff + djLint on templates.

## Settings

`myshop/myshop/settings/` is `base.py` + three env modules. `DJANGO_SETTINGS_MODULE` picks one:

- `development` — DEBUG, LocMemCache, local SQLite file (default when the var is unset)
- `production` — Redis, HTTPS/HSTS, WhiteNoise, Sentry, PostgreSQL via `DATABASE_URL`
- `testing` — in-memory SQLite, dummy cache, `CELERY_TASK_ALWAYS_EAGER`, MD5 hasher, logging nulled

`settings/__init__.py` is a selector that only branches production-vs-development. Pointing
`DJANGO_SETTINGS_MODULE` at `myshop.settings.testing` bypasses it (Django imports the module
directly) — that's why the tests need the explicit env var.

Config comes from `.env` at the repo root via `python-decouple`. `STRIPE_*`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD` and `DEFAULT_FROM_EMAIL` have **no defaults** in `base.py` — a missing one
raises at import, which is why CI injects dummy values.

Dependencies live in `myshop/pyproject.toml` (uv). The root `requirements.txt` is generated output
for the Docker build — never hand-edit it, run `make deps-lock`.

## Apps and layering

Eight local apps: `accounts`, `shop`, `cart`, `orders`, `payment`, `coupons`, `support`, `blog`.

Business logic sits in a **service layer**, not in views:

- `orders/services.py` — `OrderService.create_order_from_cart()` wraps order + `OrderItem`
  creation + `cart.clear()` in one `transaction.atomic()`; `cancel_order()` also issues the Stripe
  refund. `AddressService` for default-address handling.
- `payment/services.py` — `PaymentService` builds Stripe Checkout Sessions and PaymentIntents;
  `payment/stripe_handler.py` holds the customer / payment-method vaulting.
- Query optimisation lives in `managers.py` per app (`OrderQuerySet.with_full_details()` etc.).
  Prefer these over ad-hoc `select_related` in views — the N+1 audit was done against them.

`orders/views/` is a **package** (`address.py`, `order.py`, `pdf.py`, `_helpers.py`) whose
`__init__.py` re-exports every view so `from orders import views; views.order_create` keeps working.
Add a new view to its domain module *and* to the `__init__` re-export list. `orders/tests/` is
likewise a package.

Cart is session-based (`cart/cart.py`, key `CART_SESSION_ID`); the applied coupon is stored as
`coupon_id` in the session, not on the cart dict. `Cart.__iter__` prunes entries whose product was
deleted from the DB — don't reintroduce code that assumes every session key still resolves.

Celery handles email and PDF side-effects (`orders/tasks.py`, `payment/tasks.py`); tasks run eagerly
under the testing settings. `shop/recommender.py` uses Redis sorted sets and returns `None` from
`_get_redis()` when Redis is down — recommendations degrade silently rather than erroring.

`accounts.CustomUser` (`AUTH_USER_MODEL`) carries a `user_type` of regular vs wholesaler
(`is_wholesaler` / `is_regular`); wholesale pricing and the `form-mayorista` flow depend on it.

## URL routing

`myshop/myshop/urls.py` wraps most apps in `i18n_patterns(..., prefix_default_language=True)`, so
public URLs are language-prefixed (`/es/…`, `/en/…`). Deliberately **outside** i18n: `admin/`,
`i18n/`, `ckeditor5/`, and `payment/webhook/` — Stripe POSTs to a fixed unprefixed URL, so never
move that route inside `i18n_patterns`. `502/` and `maintenance/` are mounted both inside and out.

Error handlers `handler400/403/404/500` point at `myshop/views.py` and render branded templates from
`myshop/templates/`. There is no `handler502` in Django; see AGENTS.md for the Caddy-side story.

Media serving is deliberately split: `static()` under DEBUG, an explicit `re_path` + `django.views
.static.serve` otherwise, because `django.conf.urls.static.static()` returns `[]` when `DEBUG=False`.

## Translations — two layers

Both must be kept in mind when touching templates. Source language is Spanish (`LANGUAGE_CODE="es"`).

1. **Static UI text** — `{% trans %}` + `.po` files in `myshop/locale/en/LC_MESSAGES/`.

   ```bash
   uv run django-admin makemessages -l en
   uv run python translate_po.py      # auto-fills untranslated entries via DeepL
   uv run django-admin compilemessages
   ```

2. **DB content** (product names/descriptions, category names, blog posts) — the `|tr` / `|tr_safe`
   filters from `shop/templatetags/i18n_extras.py`, backed by `shop.translation.get_translation()`
   and the `TranslationCache` model (DeepL on cache miss; unchanged text when the active language is
   Spanish or when `DEEPL_API_KEY` is unset).

Any template rendering product or category data must `{% load i18n_extras %}` and apply `|tr`,
otherwise new admin-entered content silently stays Spanish in the English locale.

## Conventions

- Use `myshop.utils.safe_next_url(request, fallback)` for any `?next=` redirect — raw `next` is an
  open redirect and three views were already fixed for this.
- Codebase mixes Spanish and English; user-facing strings are Spanish, code/comments trend English.
- Templates: Bootstrap 5, djLint-formatted (profile `django`, indent 2). AJAX behaviour for
  add-to-cart and favourites lives in `myshop/static/js/interactions.js` — favourites badges are
  always set from the server-returned `count` via `window.skUpdateFavBadge()`, never DOM math.

## Project docs

- `AGENTS.md` — accumulated project-specific lessons (media in Coolify, i18n, error pages, AJAX
  details) plus the user's working preferences. Read it before deploy/media/i18n work.
- `BASELINE.md` / `REFACTORING_PLAN.md` — the completed 2026-05 refactor. BASELINE records four
  pre-existing `blog.tests.BlogPublicViewTests` failures and a Django-6 `CheckConstraint(check=)`
  deprecation as known-not-blocking; verify against a current run before treating either as new.
- `tasks/todo.md`, `tasks/lessons.md` — the user's task-tracking convention.
