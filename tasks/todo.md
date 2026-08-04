# TODO

- [ ] Configurar Google OAuth en producción (`synkfood.onesynk.com.mx`) — pendiente desde el despliegue inicial.
  Sin esto, `/accounts/login/` da 500 (`SocialApp.DoesNotExist`) porque la plantilla intenta
  renderizar el botón "Iniciar sesión con Google" y no hay `SocialApp` en la base de datos.

  Pasos (dentro del contenedor `web` en Coolify):

  ```bash
  cd /app/myshop
  python manage.py setup_google_oauth \
    --client-id=TU_CLIENT_ID \
    --secret=TU_CLIENT_SECRET \
    --site-domain=synkfood.onesynk.com.mx \
    --site-name="Synk Food"
  ```

  Antes de correrlo, registrar en Google Cloud Console (Credenciales → OAuth Client ID) el
  redirect URI de producción:
  `https://synkfood.onesynk.com.mx/accounts/google/login/callback/`

  El propio comando imprime al final un URI de ejemplo con `127.0.0.1:8000` (default de
  desarrollo) — ignorar esa línea, usar el de arriba con el dominio real y `https://`.
