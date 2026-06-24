# Project-specific lessons

## Django `static()` returns [] when DEBUG=False

`django.conf.urls.static.static()` checks `settings.DEBUG` internally and returns an empty list when `DEBUG=False`. Never rely on it for production media serving.

Always use `re_path` + `django.views.static.serve` directly for production:

```python
from django.urls import re_path
from django.views.static import serve

urlpatterns += [
    re_path(
        r"^%s(?P<path>.*)$" % re.escape(settings.MEDIA_URL.lstrip("/")),
        serve,
        kwargs={"document_root": settings.MEDIA_ROOT},
    ),
]
```

## Coolify + Docker persistent volumes

In Coolify deployments, `MEDIA_ROOT` in production must match the volume mount `Destination Path`. The Django `BASE_DIR` resolves to `/app/myshop` inside the container (`WORKDIR /app` + repo root is `myshop/`). If the Coolify volume is mounted at `/app/media`, override `MEDIA_ROOT` in `production.py`:

```python
MEDIA_ROOT = BASE_DIR.parent / "media"  # /app/media
```

## Translation system (i18n — static + dynamic)

The site uses two complementary translation layers:

### Static text — `{% trans %}` + `.po` files

Template hardcoded Spanish text is wrapped with `{% trans "text" %}` and extracted via `makemessages`. English translations live in `locale/en/LC_MESSAGES/django.po`. Run `translate_po.py` to auto-fill new English entries via DeepL.

```bash
# Extract new strings, translate via DeepL, and compile
uv run django-admin makemessages -l en
uv run python translate_po.py
uv run django-admin compilemessages
```

### Dynamic content — `|tr` filter + DeepL cache

Database content (product names, descriptions, category names, blog posts) uses the `|tr` / `|tr_safe` template filters from `i18n_extras.py`. These call `shop.translation.get_translation()` which:
- Returns text unchanged when the active language is Spanish (source language)
- Checks `TranslationCache` model on cache hit
- Calls DeepL API on cache miss and stores the result

**All product detail templates MUST load `i18n_extras`** and apply `|tr` to product name, description, category name, and recommended products. Future products added via admin are translated automatically on first visit.

### Key files
- `shop/templatetags/i18n_extras.py` — `|tr` and `|tr_safe` template filters
- `shop/translation.py` — `translate_text()` (DeepL API) and `get_translation()` (cached wrapper)
- `shop/models.py` — `TranslationCache` model
- `translate_po.py` — script to translate `.po` untranslated entries via DeepL

### Required template tags

```html
{% load i18n %}        <!-- for {% trans "..." %} -->
{% load i18n_extras %} <!-- for {{ product.name|tr }} -->
```

## AJAX add-to-cart (product detail)

The product detail form uses `data-ajax-add` attribute and submits via AJAX (instead of redirecting to cart). Shows a toast notification and updates the cart badge. Behavior defined in `interactions.js` section 7. The catalog list buttons use class `.js-add-cart-btn` (section 13).

## Debugging media files in production

Inside the Coolify container, verify `MEDIA_ROOT` and file existence:

```bash
python /app/myshop/manage.py shell -c "
from django.conf import settings
import os
print('MEDIA_ROOT:', settings.MEDIA_ROOT)
print('MEDIA_URL:', settings.MEDIA_URL)
print('Existe MEDIA_ROOT:', os.path.isdir(settings.MEDIA_ROOT))
"
find /app -name "*product-name*" -type f 2>/dev/null
```
