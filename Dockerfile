# Usamos una imagen oficial de Python ligera
FROM python:3.12-slim

# Evita que Python cree archivos .pyc y fuerza la salida de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalamos las librerías gráficas de WeasyPrint en el Ubuntu interno
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    libgdk-pixbuf-2.0-0 \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Establecemos la carpeta de trabajo
WORKDIR /app

# Copiamos e instalamos los requerimientos de Python primero (optimiza el caché)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de tu código
COPY . /app/

# El comando maestro que arrancará todo
CMD python myshop/manage.py migrate --noinput && \
    python myshop/manage.py collectstatic --noinput && \
    python myshop/manage.py compilemessages && \
    gunicorn --pythonpath myshop myshop.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --access-logfile - \
    --error-logfile -