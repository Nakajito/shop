import os

from decouple import config

# Esto lee la variable de Coolify, si no existe, usa development
settings_module = os.getenv("DJANGO_SETTINGS_MODULE", "myshop.settings.development")

if settings_module == "myshop.settings.production":
    from .production import *
else:
    from .development import *
