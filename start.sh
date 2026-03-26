# 1. Instalar dependencias del sistema para WeasyPrint
apt-get update
apt-get install -y libpango-1.0-0 libcairo2 libpangoft2-1.0-0 libffi-dev shared-mime-info

# 2. Ejecutar comandos de Django
python myshop/manage.py migrate --noinput
python myshop/manage.py collectstatic --noinput

# 3. Iniciar el servidor Gunicorn
gunicorn --pythonpath myshop myshop.wsgi:application --bind 0.0.0.0:8000