# Test Baseline — pre-refactor

Tag git: `pre-refactor-2026-05-25`
Rama: `refactor/cleanup-and-structure`
Fecha: 2026-05-25

## Suite

`DJANGO_ENV=myshop.settings.testing python manage.py test`

- Ejecutados: **141 tests**
- Fallos: **4** (todos en `blog.tests.BlogPublicViewTests`)
- Errores: **1** (CheckConstraint deprecated en Django 6)

## Fallos pre-existentes (NO bloquean refactor)

```
FAIL: blog.tests.BlogPublicViewTests.test_post_list_by_category
FAIL: blog.tests.BlogPublicViewTests.test_post_list_by_tag
FAIL: blog.tests.BlogPublicViewTests.test_post_list_search
FAIL: blog.tests.BlogPublicViewTests.test_post_list_shows_published
```

Razón: tests buscan `"Public Post"` en respuesta pero el template no lo emite (probable cambio en plantilla de blog sin actualizar fixtures de test).

## Error pre-existente (NO bloquea refactor)

```
TypeError: CheckConstraint.__init__() got an unexpected keyword argument 'check'
```

Ubicación:
- `shop/models.py:70-74` -> `product_price_non_negative`
- `orders/models.py:244-...`
- Migraciones `shop/migrations/0005_*.py`, `orders/migrations/0013_*.py`

Razón: Django 6 renombró `check=` a `condition=` en `CheckConstraint`. Migraciones legacy aún usan kwarg antiguo.

Plan: arreglar en Fase 4 (DRY/limpieza) o Fase 1 si bloquea tests posteriores.

## Cobertura baseline

`coverage run --source=apps_locales manage.py test` -> **3% (degradado por crash en CheckConstraint)**.

Cuando se corrija `CheckConstraint`, regenerar cobertura real. Objetivo Fase 5: **80%+** por app.

## Gate por fase

Cada fase NO puede empeorar el baseline:
- Tests verdes >= 136 (141 - 4 pre-existentes - 1 error)
- Sin nuevos fallos ni errores introducidos
- `python manage.py check` sin warnings nuevos
