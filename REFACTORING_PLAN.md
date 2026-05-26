# Refactoring Plan — One Synk (myshop)

Fecha: 2026-05-25
Autor: Claude (Opus 4.7)
Skills aplicadas: `django-expert`, `tdd-workflow`
Codegraph: `.codegraph/codegraph.db` (índice de símbolos disponible)

## Objetivo

Refactor profundo sin romper estilos, funcionalidad ni procesos. Limpieza estructural, eliminación de código muerto / duplicado, aplicación de DRY, organización de directorios, base de tests reforzada (TDD). Cero regresiones funcionales.

## Garantías (no se rompe)

- URLs públicas y namespaces intactos (`shop`, `cart`, `orders`, `payment`, `coupons`, `support`, `blog`, `accounts`).
- Plantillas y bloques `{% block %}` se mantienen; rutas `{% static %}` y `{% url %}` no cambian de nombre.
- Modelos: sin renombrar campos ni tablas. Si hay cambios estructurales -> sólo migraciones aditivas + reversibles.
- Settings: `DJANGO_ENV` y variables `.env` preservadas.
- Celery, Stripe, allauth, WeasyPrint: integraciones intactas.
- Comportamiento del admin (lista/búsqueda/filtros) preservado.

## Hallazgos clave (evidencia)

### A. Archivos duplicados / muertos
- `myshop/templates/fom-mayorista_copia.html` -> typo + `_copia` (duplicado).
- `myshop/blog/templates/blog/post_detail_ORIGINAL.html` -> backup huérfano.
- `myshop/shop/templates/shop/product/list_original.html` -> backup huérfano.
- `myshop/main.py` -> sólo imprime "Hello from myshop!" (artefacto `uv init`).
- `myshop/products/2026/01/...` -> directorio fantasma fuera de `MEDIA_ROOT` (`myshop/media/`). Sin referencias en código.
- Borrados en `git status` aún sin commit: `static/blog/css/blog.css`, `static/blog/js/blog.js`, `static/css/pdf.css`, `static/css/stripe.css`, `static/js/stripe_script.js`.

### B. Archivos versionados que NO deberían estarlo
- `myshop/static/admin/**`, `myshop/static/account/**`, `myshop/static/django_ckeditor_5/**` -> son salida de `collectstatic`. Deben servirse desde `STATIC_ROOT = staticfiles/` o WhiteNoise.
- `myshop/db.sqlite3` está rastreado (ignored pattern existe pero archivo fue committeado antes).
- `myshop/logs/django.log` debería estar en `.gitignore`.

### C. Configuración inconsistente
- `pyproject.toml` declara sólo 5 dependencias (falta Django, Stripe, Redis, Celery, WeasyPrint, etc.). `requirements.txt` tiene la lista real. Hay desincronización fuente-única-de-verdad.
- `myshop/myshop/settings/__init__.py` importa `from decouple import config` sin usarlo.
- `development.py` fuerza `sqlite3` (CLAUDE.md dice PostgreSQL en dev) — desalineado con doc.
- `myshop/myshop/urls.py` duplica el serve de media: bloque `if DEBUG` + bloque `re_path(r'^media/...')` siempre activo. El segundo expone media en producción sin proxy.

### D. Apps y dominio
- `shop/` app correcta. `myshop/products/` es directorio basura, no es app Django.
- `orders/views.py` (506 LOC) y `orders/models.py` (461 LOC) -> candidatos a modularización por dominio (address, tracking, history).
- `payment/services.py` y `orders/services.py` coexisten -> revisar duplicación de lógica de totales/estados.
- Tests fragmentados: `orders/tests.py` + `orders/test_services.py` + `orders/test_integration.py`. Unificar a paquete `orders/tests/`.

### E. Convenciones
- Comentarios y código mezclados en español/inglés (no problema, pero hay strings de UI y nombres de variables mezclados).
- Indentación inconsistente puntual en `base.py INSTALLED_APPS` (línea `widget_tweaks` con espacios extra y comentario emoji).
- Sin `pre-commit`, sin `ruff/black`, sin CI.

### F. Riesgos de seguridad / producción
- `re_path` que sirve `MEDIA_URL` con `django.views.static.serve` activo siempre (línea ~54 `urls.py`). Debe ir sólo bajo `DEBUG`.
- `static/` de admin committeado puede divergir de la versión instalada de Django -> CSS roto al actualizar.

## Plan de ejecución (fases)

> Cada fase termina con: **tests pasando** + **commit checkpoint** (siguiendo `tdd-workflow`: RED -> GREEN -> REFACTOR).

### Fase 0 — Baseline & red de seguridad (BLOQUEANTE)
1. Crear rama `refactor/cleanup-and-structure`.
2. Inventariar tests existentes: `python myshop/manage.py test --verbosity=2 --keepdb` (registrar baseline pass/fail).
3. Generar `coverage` baseline (`coverage run --source=. manage.py test && coverage report`).
4. Añadir `pre-commit` config mínimo (ruff + djlint + check-merge-conflict + end-of-file-fixer).
5. Añadir `.editorconfig`.
6. Commit checkpoint: `chore(baseline): pre-commit + coverage baseline`.

### Fase 1 — Limpieza segura (zero-risk)
1. **Eliminar archivos muertos:**
   - `myshop/templates/fom-mayorista_copia.html`
   - `myshop/blog/templates/blog/post_detail_ORIGINAL.html`
   - `myshop/shop/templates/shop/product/list_original.html`
   - `myshop/main.py`
   - `myshop/products/` (directorio entero — confirmar con usuario que es huérfano)
2. **Confirmar deleciones pendientes** del git status (stripe/blog/pdf static) o restaurar si se siguen referenciando (`grep -rn "stripe_script.js\|pdf.css\|blog/css/blog.css"`).
3. **Untrack collectstatic output:**
   - `git rm -r --cached myshop/static/admin myshop/static/account myshop/static/django_ckeditor_5`
   - `git rm --cached myshop/db.sqlite3 myshop/logs/django.log`
4. **Actualizar `.gitignore`:** agregar `myshop/staticfiles/`, `myshop/static/admin/`, `myshop/static/account/`, `myshop/static/django_ckeditor_5/`, `myshop/logs/*.log`, `myshop/db.sqlite3`.
5. Test suite verde tras cada borrado (`./manage.py test`).
6. Commit: `chore(cleanup): remove dead templates, scaffolding files, untrack build artifacts`.

### Fase 2 — Settings & configuración (DRY de la verdad)
1. Unificar gestión de dependencias: **mover todo a `pyproject.toml`** (con `[project.dependencies]` completo desde `requirements.txt`). Mantener `requirements.txt` autogenerado por `uv pip compile` o `pip freeze` para Docker (cita en README).
2. Quitar imports muertos en `myshop/settings/__init__.py` (`from decouple import config`).
3. Limpiar `INSTALLED_APPS` de comentarios emoji y espacios.
4. Resolver doc-vs-realidad: actualizar `development.py` para usar PostgreSQL si lo describe CLAUDE.md, **o** corregir CLAUDE.md para reflejar SQLite (preguntar al usuario, ver dudas).
5. Sólo servir media en DEBUG: eliminar el `re_path` permanente de `urls.py`.
6. Añadir helper `myshop/settings/utils.py` con loaders `env_bool`, `env_list` (DRY de `python-decouple`).
7. Tests: añadir `tests/test_settings.py` que carga cada settings module sin crash.
8. Commit: `refactor(settings): single source of truth, secure media serving`.

### Fase 3 — Reorganización de apps (estructura)
1. Convertir cada `tests.py` grande a paquete:
   ```
   orders/tests/
     __init__.py
     test_models.py
     test_views.py
     test_services.py
     test_integration.py
     factories.py        # factory_boy
     conftest.py
   ```
   Aplicar a `orders`, `blog`, `accounts`, `payment`, `support`, `shop`.
2. **Adelgazar `orders/views.py`**: separar en `views/order.py`, `views/address.py`, `views/tracking.py`, `views/history.py`. Mantener nombres exportados via `views/__init__.py` (sin romper imports en `urls.py`).
3. Detectar y consolidar lógica duplicada entre `orders/services.py` y `payment/services.py` -> extraer a `orders/services/totals.py` / `payment/services/stripe.py` según pertenencia de dominio.
4. Crear `myshop/core/` app utilitaria (opcional, sólo si emergen helpers compartidos: mixins, middlewares, querysets base, `BaseTimeStampedModel`). **No crear si no hay duplicación real.**
5. Templates: confirmar que cada app tiene `templates/<app>/...` (ya lo está) — sin movimientos.
6. Tests verdes en cada paso. Un commit por app.

### Fase 4 — DRY en código
1. **Modelos:** introducir mixin `TimeStampedModel(created_at, updated_at)` donde se repita. Buscar duplicación de `__str__`, `Meta.ordering`, slugs.
2. **Vistas:** extraer decorator stack repetido (`@login_required + @require_POST`) o convertir a CBV donde aporte.
3. **Forms:** revisar `accounts/forms.py` (250 LOC), `blog/forms.py` (170 LOC), `support/forms.py` (60 LOC) — extraer validadores comunes (teléfono, email-corporativo) a `core/validators.py`.
4. **Querysets:** verificar `managers.py` en orders/shop/blog/support. Consolidar patterns como `published()`, `active()`.
5. **Templates:** detectar HTML duplicado entre `templates/form-mayorista.html` y otros formularios -> extraer a `includes/` partials.
6. Cada extracción precedida de test (TDD).
7. Commit por categoría.

### Fase 5 — Tests reforzados (TDD coverage 80%+)
1. Añadir `factory_boy` + `pytest-django` (opcional — decidir con usuario; ver dudas) **o** mantener `unittest` puro y `model_bakery`.
2. Cobertura objetivo por app (mínimo 80%):
   - `accounts`, `orders`, `payment`, `shop`, `blog`, `support`, `cart`, `coupons`.
3. Añadir tests faltantes a `cart/` y `coupons/` (actualmente carecen de `tests.py` específico).
4. Smoke E2E con Django test client para flujo crítico: catálogo -> cart -> order -> payment success webhook.
5. CI: GitHub Actions `python-version: 3.13`, ejecuta test + coverage + ruff + djlint.
6. Commit: `test(coverage): raise to 80% across apps`.

### Fase 6 — Performance & seguridad (no destructivo)
1. Auditar N+1 en `orders/views.py` y `shop/views.py` con `django-debug-toolbar` (sólo dev). Aplicar `select_related/prefetch_related` donde falten.
2. Revisar índices DB en campos de búsqueda/orden frecuente (`Product.slug`, `Order.created`, etc.). Añadir `db_index=True` o `class Meta: indexes = [...]`.
3. Revisar permisos en views sensibles (`@login_required`, ownership checks en orders).
4. Headers de seguridad en `production.py` (ya hay HSTS/HTTPS — confirmar `SECURE_*` completo).
5. Commit: `perf+sec: index hotspots and tighten permission boundaries`.

### Fase 7 — Documentación
1. Sync `myshop/CLAUDE.md` con realidad post-refactor.
2. Sync `myshop/README.md`.
3. Documentar comandos en `pyproject.toml` scripts o `Makefile`.
4. Commit: `docs: align project docs with post-refactor state`.

### Fase 8 — Cierre
1. Re-ejecutar suite completa + coverage.
2. `python manage.py check --deploy` -> sin warnings críticos.
3. Squash de checkpoints internos (si el usuario lo prefiere) o PR con historia completa.
4. PR a `dev` con descripción detallada por fase.

## Verificación por fase (gates obligatorios)

Cada fase pasa SI:
- `python myshop/manage.py test` -> 100% verde.
- `python myshop/manage.py check --deploy` (con `DJANGO_ENV=production`) -> sin errores nuevos.
- Cobertura no decrece respecto a baseline.
- Smoke manual: `runserver` -> login + listado productos + agregar al cart -> sin error 500.

## Reversión

Cada fase = commit independiente. Reversión = `git revert <hash>` o `git reset --hard` al baseline tag (`pre-refactor-2026-05-25`).

## Dependencias entre fases

```
Fase 0 -> Fase 1 -> Fase 2 -> Fase 3 -> Fase 4 -> Fase 5 -> Fase 6 -> Fase 7 -> Fase 8
                        \__ Fase 5 (subset) puede ir en paralelo a 3-4
```

## Decisiones confirmadas (2026-05-25)

1. ✅ Borrar `myshop/products/2026/` y `myshop/main.py`.
2. ✅ Fuente única de dependencias: **`pyproject.toml` con `uv`**. `requirements.txt` se regenera via `uv pip compile` para Docker.
3. ✅ Framework de tests: mantener **`unittest` + Django TestCase**.
4. ✅ Dev DB: **SQLite**. `myshop/CLAUDE.md` actualizado.
5. ✅ Untrack: `static/admin`, `static/account`, `static/django_ckeditor_5`, `db.sqlite3`, `logs/django.log`.
6. ✅ Completar deletes pendientes en git status (stripe/blog/pdf css/js → restaurados, siguen referenciados).

## Resultado final (2026-05-25)

Rama: `refactor/cleanup-and-structure` ✅ todas las fases completadas.

| Fase | Commit | Diff | Highlight |
|---|---|---|---|
| 0 baseline | `c28aa6a` | +709 | plan + baseline doc + tooling (pre-commit, editorconfig) |
| 1 limpieza | `de00922` | −32639 | dead templates, main.py, products/, untrack collectstatic outputs |
| 2 settings | `b44ba2c` | +793 | pyproject único, Django 5 pin, urls.py media fix, CLAUDE.md sync |
| 3 estructura | `db8ecb3` | +20 | orders/views/ y orders/tests/ packages, DRY internos |
| 4 lint/DRY | `b971af4` | −21 | ruff clean (103→0), dead code, raise-from |
| 5 coverage+CI | `3d8dae1` | +832 | +55 tests, coverage 70→80%, GitHub Actions |
| 6 sec+perf | `3515c59` | +83 | open-redirect cerrado en 3 views, auditorías deploy/N+1/auth |
| 7-8 docs+PR | — | — | README/Makefile + PR a `dev` |

### Métricas

- **Tests**: 141 → 201 (+60). 4 fallos pre-existentes blog. 0 errors.
- **Coverage**: 70% → **81%**.
- **Ruff**: 103 → **0**.
- **`check --deploy`**: **0 issues**.
- **LOC neto**: −32 245 (mayoritariamente collectstatic outputs y duplicados).

### Diferidos documentados

- `CheckConstraint(check=)` → `condition=`: válido en Django 5 pinned, requerido en Django 6.
- `TimeStampedModel` mixin: requiere migración 7 modelos por divergencia `created_at` vs `created`.
- `confirm_payment` AJAX: añadir cross-check de ownership de Stripe intent.
- `redirect(url, code=303)` en `payment_process`: kwarg ignorado silenciosamente por Django.
- `DJ001` (nullable CharField/TextField): ignorado por ruff, cambio schema separado.

## Notas

- `.codegraph/codegraph.db` se usará para mapear referencias cruzadas antes de mover/renombrar (consulta SQLite).
- Cero cambios de UX/visual. Si algún cambio toca template debe pasar revisión visual manual.
- Migraciones: ninguna prevista en Fase 0-4. Si Fase 4 introduce mixin de timestamps, migraciones serán aditivas + `null=True` -> `default=timezone.now` por etapa.
