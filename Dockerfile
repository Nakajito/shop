# Usamos una imagen oficial de Python ligera
FROM python:3.13-slim

# Evita que Python cree archivos .pyc y fuerza la salida de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalamos las librerías gráficas de WeasyPrint en el Ubuntu interno.
# gosu: para bajar privilegios limpiamente desde el entrypoint (ver abajo).
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    libgdk-pixbuf-2.0-0 \
    gettext \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Establecemos la carpeta de trabajo
WORKDIR /app

# Copiamos e instalamos los requerimientos de Python primero (optimiza el caché)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de tu código
COPY . /app/

# Corre como usuario sin privilegios en runtime (A02 — el contenedor corría
# como root). El proceso arranca como root (sin USER aquí) porque
# entrypoint.sh necesita permisos de root para corregir el dueño del volumen
# de media montado por Coolify en /app/media ANTES de bajar a appuser — ver
# el comentario en entrypoint.sh para el porqué (ese volumen no es parte de
# esta imagen, así que el chown de abajo nunca lo toca).
RUN useradd --uid 1000 --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Shell-form CMD: Docker wraps it as `/bin/sh -c "<this>"` and appends that
# to the exec-form ENTRYPOINT above, so entrypoint.sh receives it as "$@"
# and hands it to gosu unchanged (corre como appuser).
CMD python myshop/manage.py migrate --noinput && \
    python myshop/manage.py check && \
    python myshop/manage.py collectstatic --noinput && \
    python myshop/manage.py compilemessages && \
    gunicorn --pythonpath myshop myshop.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -