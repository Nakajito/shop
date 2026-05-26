# One Synk — shop

E-commerce Django (Korean food). Mono-repo con tooling en la raíz y código Django bajo `myshop/`.

## Layout

```
shop/                       # repo root
├── myshop/                 # Django project (manage.py, apps, settings, pyproject.toml)
├── requirements.txt        # autogenerado desde myshop/pyproject.toml (Docker)
├── Dockerfile              # producción
├── REFACTORING_PLAN.md     # plan de refactor activo
├── BASELINE.md             # baseline de tests pre-refactor
├── Makefile                # atajos
└── .github/workflows/      # CI (ruff + tests + coverage)
```

## Quick start

```bash
make install        # uv sync + .env
make migrate
make test
make run
```

Ver detalle en [`myshop/README.md`](myshop/README.md) y arquitectura en [`myshop/CLAUDE.md`](myshop/CLAUDE.md).

## CI

GitHub Actions corre en cada push/PR a `main`/`dev`:

- `ruff check`
- `python manage.py check`
- `python manage.py test`
- `coverage report --fail-under=78`

## Licencia

Privada — proyecto interno.
