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
cd shop

# Entorno virtual
python -m venv .venv
source .venv/bin/activate

# Dependencias
pip install -r requirements.txt

# Variables de entorno
cp .env.example .env   # editar credenciales

# Migraciones
python myshop/manage.py migrate

# Superusuario
python myshop/manage.py createsuperuser

# Datos demo (3 categorías, 10 productos, 5 posts de blog)
python myshop/manage.py seed_demo
```

## Comandos comunes

```bash
# Servidor de desarrollo
python myshop/manage.py runserver

# Tests
python myshop/manage.py test
python myshop/manage.py test orders

# Worker Celery (requiere Redis)
cd myshop && celery -A myshop worker -l info

# Flower con auth básica
cd myshop && celery -A myshop flower --basic-auth=user:pwd

# Webhook Stripe local
./stripe listen --forward-to 127.0.0.1:8000/payment/webhook/

# Cargar recomendaciones a Redis
python myshop/manage.py load_recommendations

# Setup Google OAuth
python myshop/manage.py setup_google_oauth --client-id=ID --secret=SECRET
```

## Entornos

`DJANGO_ENV` selecciona el módulo de settings:

- `development` — DEBUG=True, LocMemCache, PostgreSQL local
- `production` — DEBUG=False, Redis, HTTPS/HSTS, WhiteNoise, Sentry
- `testing` — overrides para test runner

Variables cargadas desde `.env` vía `python-decouple`.

## Variables de entorno clave

```
SECRET_KEY=
DJANGO_ENV=development
DB_NAME= DB_USER= DB_PASSWORD= DB_HOST= DB_PORT=
STRIPE_PUBLISHABLE_KEY= STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET= STRIPE_API_VERSION=
REDIS_HOST= REDIS_PORT= REDIS_DB= REDIS_PASSWORD=
REDIS_CACHE_URL=
EMAIL_HOST= EMAIL_HOST_USER= EMAIL_HOST_PASSWORD=
```

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
