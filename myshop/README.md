# One Synk — Tienda de Comida Coreana

E-commerce Django para venta de comida coreana (fideos, salsas, snacks). Soporta clientes regulares y mayoristas, pagos con Stripe, facturas PDF, recomendaciones con Redis y blog con CKEditor 5.

## Stack

- **Django 5.0** (Python 3.13)
- **PostgreSQL** (producción) / SQLite (dev)
- **Redis** — caché, sesiones, recomendador, broker de Celery
- **Celery + Flower** — emails, generación de PDF
- **Stripe** — pagos y webhooks
- **django-allauth** — login email + Google OAuth
- **WeasyPrint** — facturas PDF
- **WhiteNoise + Gunicorn** — servir estáticos y WSGI
- **Sentry** — observabilidad en producción

## Estructura

```
myshop/
├── accounts/      # CustomUser (regular/mayorista), perfiles, adapters allauth
├── shop/          # Category, Product, recomendador Redis
├── cart/          # Carrito por sesión
├── orders/        # Order, OrderItem, Address, tracking, servicios
├── payment/       # Integración Stripe, webhooks, facturas PDF
├── coupons/       # Cupones de descuento
├── support/       # Tickets de soporte
├── blog/          # Posts con CKEditor 5, categorías, tags
├── templates/     # Plantillas globales
├── static/        # Assets estáticos
├── media/         # Uploads
└── myshop/        # settings/, urls.py, celery.py, wsgi.py, asgi.py
```

Detalles de arquitectura en [CLAUDE.md](CLAUDE.md).

## Requisitos

- Python 3.13+
- PostgreSQL 14+ (o SQLite para pruebas rápidas)
- Redis 7+
- Stripe CLI (para webhooks en desarrollo)

## Instalación

```bash
# Clonar y entrar
cd shop/myshop

# Sincronizar venv + dependencias (uv-managed)
uv sync

# Variables de entorno (en raíz del repo)
cp ../.env.example ../.env   # editar credenciales

# Migraciones
uv run python manage.py migrate

# Superusuario
uv run python manage.py createsuperuser

# Datos demo (3 categorías, 10 productos, 5 posts de blog)
uv run python manage.py seed_demo
```

## Comandos comunes

Todos asumen el cwd `myshop/`. También disponibles vía `make <target>` desde la raíz.

```bash
# Servidor de desarrollo (SQLite por defecto)
uv run python manage.py runserver

# Tests (in-memory SQLite vía settings/testing.py)
DJANGO_SETTINGS_MODULE=myshop.settings.testing uv run python manage.py test
DJANGO_SETTINGS_MODULE=myshop.settings.testing uv run python manage.py test orders

# Coverage report
DJANGO_SETTINGS_MODULE=myshop.settings.testing uv run coverage run manage.py test
uv run coverage report

# Ruff lint
uv run ruff check

# Worker Celery (requiere Redis)
uv run celery -A myshop worker -l info

# Flower con auth básica
uv run celery -A myshop flower --basic-auth=user:pwd

# Webhook Stripe local (desde raíz)
./stripe listen --forward-to 127.0.0.1:8000/payment/webhook/

# Cargar recomendaciones a Redis
uv run python manage.py load_recommendations

# Setup Google OAuth
uv run python manage.py setup_google_oauth --client-id=ID --secret=SECRET

# Regenerar requirements.txt (raíz, para Docker) desde pyproject.toml
cd .. && uv pip compile myshop/pyproject.toml -o requirements.txt
```

## Entornos

`DJANGO_SETTINGS_MODULE` selecciona el módulo. Sin variable, se carga `development`.

- `myshop.settings.development` — DEBUG=True, LocMemCache, **SQLite** local
- `myshop.settings.production`  — DEBUG=False, Redis, HTTPS/HSTS, WhiteNoise, Sentry, PostgreSQL via `DATABASE_URL`
- `myshop.settings.testing`     — in-memory SQLite, dummy cache, eager Celery, MD5 hasher

Variables cargadas desde `.env` vía `python-decouple`.

## Variables de entorno clave

```
SECRET_KEY=
DJANGO_SETTINGS_MODULE=myshop.settings.development     # o .production
DATABASE_URL=postgres://user:pass@host:5432/db         # solo production
STRIPE_PUBLISHABLE_KEY= STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET= STRIPE_API_VERSION=
REDIS_HOST= REDIS_PORT= REDIS_DB= REDIS_PASSWORD=
REDIS_CACHE_URL=                                       # solo production
EMAIL_HOST_USER= EMAIL_HOST_PASSWORD= DEFAULT_FROM_EMAIL=
ALLOWED_HOSTS=                                         # comma-separated
CSRF_TRUSTED_ORIGINS=                                  # production
SENTRY_DSN=                                            # opcional
```

## Dependencias

Fuente única: `myshop/pyproject.toml` (uv). El `requirements.txt` en la raíz se **regenera** desde pyproject para el build Docker. No editarlo a mano.

## Docker

```bash
# Build
docker build -t myshop ../   # Dockerfile vive en la raíz del repo

# El contenedor ejecuta:
#   migrate --noinput
#   collectstatic --noinput
#   gunicorn --bind 0.0.0.0:8000 --workers 3 --threads 2
```

## URLs principales

| Ruta | App |
|------|-----|
| `/` | shop (catálogo) |
| `/cart/` | cart |
| `/orders/` | orders |
| `/payment/` | payment + webhook |
| `/coupons/` | coupons |
| `/support/` | support |
| `/blog/` | blog |
| `/accounts/` | allauth |
| `/admin/` | Django admin |

## Tarjetas de prueba Stripe

```
Éxito:        4242 4242 4242 4242
Fallo:        4000 0000 0000 0002
3D Secure:    4000 0025 0000 3155
```

## Licencia

Privada — proyecto interno.
