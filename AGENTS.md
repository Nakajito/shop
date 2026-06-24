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

## Error pages — custom handlers + 502 limitation

Django natively supports `handler400`, `handler403`, `handler404`, and `handler500`. These are configured in `myshop/urls.py` and render branded templates from `templates/{400,403,404,500}.html`.

### The 502 problem

Django has NO `handler502`. A **true 502 Bad Gateway** happens when the reverse proxy (Caddy/nginx) cannot reach the Django upstream — so Django is **not running** and cannot serve any template.

### Solution implemented

- `myshop/views.py` contains `bad_gateway()` (502) and `maintenance()` (503) views
- Both routes are mounted at `/502/` and `/maintenance/` (inside and outside i18n_patterns)
- In Coolify, configure **Caddy** to rewrite a failed health check to `/502/` so the proxy renders the branded template **only when Django is still running**:

```caddyfile
# Coolify Caddyfile fragment — serve branded 502 when upstream fails
handle_errors {
    @502 {
        expression {http.error.status_code} == 502
    }
    rewrite @502 /502/
    reverse_proxy @502 django:8000
}
```

For **true 502s** (Django completely down, container crashed), the reverse proxy must serve a **static file**:

```caddyfile
handle_errors {
    @502_static {
        expression {http.error.status_code} == 502
    }
    handle @502_static {
        respond * 502 {
            body "Site temporarily unavailable — please try again later."
        }
    }
}
```

### Key files
- `myshop/views.py` — `bad_gateway()`, `maintenance()`, `page_not_found()`, `server_error()`, etc.
- `myshop/urls.py` — variable assignments: `handler400`, `handler403`, `handler404`, `handler500`
- `templates/502.html`, `templates/500.html`, `templates/404.html`, `templates/403.html`, `templates/400.html`

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

## Plan Mode (default)
- Plan si tarea >3 pasos o decisión arquitectónica. Si falla → para y replanifica.
- Usa plan también para verificación. Especifica requisitos upfront.

## Subagentes (ahorra contexto)
- Investiga, explora o analiza en paralelo con subagentes. Uno por tarea.

## Mejora continua
- Tras cada corrección: actualiza `tasks/lessons.md` con el patrón y reglas para no repetirlo.
- Revisa lecciones al iniciar cada sesión.

## Verificación antes de finalizar
- No marques completado sin pruebas. Compara comportamiento con el original.
- Pregunta: “¿Staff engineer aprobaría esto?”. Corre tests, revisa logs.

## Elegancia balanceada
- Cambios no triviales: pausa y busca solución más elegante.
- Si el fix es chapucero: implementa la versión elegante con lo que sabes ahora.
- Omitir solo en fixes obvios.

## Bug fixing autónomo
- Recibes un bug → arréglalo sin pedir ayuda. Señala logs, errores, tests.
- Arregla CI fallida sin instrucciones.

## Task Management
1. Plan → `tasks/todo.md` (ítems chequeables).
2. Verifica plan antes de implementar.
3. Marca progreso.
4. Explica cambios al final.
5. Documenta resultados en `todo.md`.
6. Lecciones → `lessons.md`.

## Principios
- Simplicidad: cambios mínimos.
- Sin parches temporales: encuentra causa raíz.
- Impacto mínimo: solo toca lo necesario.
- Realiza preguntas si tienes dudas para realizar las tareas y realiza propuestas.

## TDD
- Usa TDD siempre.

## Stack (por defecto)
- Python (última versión - MCP Context 7)
- Bootstrap 5 o Tailwind CSS (Preguntar primero),  SQLite (dev) / PostgreSQL (prod).

## UI/UX
- Responsivo, interfaces simples primero.

## CI/CD
- Genera configuración para GitHub Actions por defecto (a menos que se pida otro).

## Calidad y Estilo de Código
- Formateadores: Ruff 
- Seguridad: CodeQL 

## Pruebas (Testing):
- Pytest
- Cada vez que se agregue, modifique o elimine funcionalidad → actualizar los tests.

## Gestión de Paquetes y Entornos
- uv

## Tipado Estático (Type Checking)
- mypy, Pydantic

## Creación de Documentación
- Sphinx
- Skill "software-docs"