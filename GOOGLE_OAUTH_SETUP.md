# 🔐 Google OAuth Setup Guide

## Pasos para configurar autenticación con Google

### 1. Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Haz clic en el selector de proyecto en la parte superior
3. Haz clic en "NUEVO PROYECTO"
4. Ingresa un nombre (ej: "One Synk Shop")
5. Haz clic en "CREAR"

---

### 2. Habilitar Google+ API

1. En la barra de búsqueda, escribe "Google+ API"
2. Haz clic en el resultado
3. Haz clic en "HABILITAR"

(Alternativa: Busca "OAuth 2.0 API" o "Google Identity")

---

### 3. Crear Credenciales OAuth 2.0

1. Ve a **Credenciales** en el menú lateral
2. Haz clic en **"+ CREAR CREDENCIALES"**
3. Selecciona **"ID de cliente OAuth"**
4. Se te pedirá crear una **pantalla de consentimiento** primero:
   - Selecciona **"Externo"** como tipo de usuario
   - Haz clic en **"CREAR"**
   - Completa el formulario:
     - **Nombre de la app:** One Synk Shop
     - **Email de soporte:** tu-email@ejemplo.com
     - **Email de contacto:** tu-email@ejemplo.com
   - Haz clic en **GUARDAR Y CONTINUAR**

---

### 4. Configurar Tipos de Cliente

1. De vuelta en Credenciales, haz clic en **"+ CREAR CREDENCIALES"**
2. Selecciona **"ID de cliente OAuth"**
3. Tipo de aplicación: **"Aplicación web"**
4. En **"Orígenes autorizados de JavaScript"**, agrega:
   ```
   http://127.0.0.1:8000
   http://localhost:8000
   ```

5. En **"URI de redirección autorizados"**, agrega:
   ```
   http://127.0.0.1:8000/accounts/auth/google/callback/
   http://localhost:8000/accounts/auth/google/callback/
   ```

6. Haz clic en **"CREAR"**

---

### 5. Obtener tus Credenciales

1. Una vez creado, verás un modal con:
   - **Client ID**
   - **Client Secret**

Copia ambos valores.

---

### 6. Configurar en Django

#### Opción A: Usar Django Admin

1. Ve a `http://127.0.0.1:8000/admin/`
2. Navega a **Sites** → asegúrate de que el sitio sea `example.com` o `localhost:8000`
3. Ve a **Social Applications** → **Add Social Application**
4. Completa:
   - **Provider:** Google
   - **Name:** Google
   - **Client id:** (tu Client ID)
   - **Secret key:** (tu Client Secret)
   - **Sites:** Selecciona tu sitio
5. Haz clic en **SAVE**

#### Opción B: Usar Variables de Entorno (Más seguro)

1. Abre `.env` (o crea el archivo en la raíz del proyecto):
   ```bash
   GOOGLE_OAUTH_CLIENT_ID=tu_client_id_aqui
   GOOGLE_OAUTH_CLIENT_SECRET=tu_client_secret_aqui
   ```

2. En `myshop/settings.py`, descomentar o agregar:
   ```python
   SOCIALACCOUNT_PROVIDERS = {
       "google": {
           "APP": {
               "client_id": config("GOOGLE_OAUTH_CLIENT_ID"),
               "secret": config("GOOGLE_OAUTH_CLIENT_SECRET"),
           },
           "SCOPE": ["profile", "email"],
           "AUTH_PARAMS": {"access_type": "online"},
           "VERIFIED_EMAIL": True,
       }
   }
   ```

---

### 7. Probar el Login

1. Inicia el servidor:
   ```bash
   python manage.py runserver
   ```

2. Ve a `http://127.0.0.1:8000/accounts/login/`

3. Haz clic en "Iniciar sesión con Google"

4. Se abrirá una ventana de Google ¡Listo! ✅

---

## 🔒 Consideraciones de Seguridad

- **Nunca** comitas `Client Secret` en el código
- Usa variables de entorno (`.env`)
- En producción, usa HTTPS (requerido por Google)
- Agrega tus dominios de producción a "Orígenes autorizados"

---

## ⚙️ Configuración de Producción

Para producción (ej: `shop.ejemplo.com`):

1. En Google Cloud Console, agrega:
   ```
   https://shop.ejemplo.com
   ```

2. En "URI de redirección":
   ```
   https://shop.ejemplo.com/accounts/auth/google/callback/
   ```

3. En Django, configura:
   ```python
   # settings.py
   ALLOWED_HOSTS = ["shop.ejemplo.com", "www.shop.ejemplo.com"]
   SECURE_SSL_REDIRECT = True
   ```

---

## 🐛 Troubleshooting

### Error: "redirect_uri_mismatch"
- Verifica que la URL exacta coincida en Google Cloud Console
- Recuerda: incluye la barra final `/`

### Error: "invalid_client"
- Comprueba que el `Client ID` y `Client Secret` sean correctos
- Asegúrate de estar usando HTTPS en producción

### Botón no aparece
- Verifica que `{% load socialaccount %}` esté en la plantilla
- Recarga el servidor

---

## 📚 Enlaces Útiles

- [Google Cloud Console](https://console.cloud.google.com/)
- [Django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth 2.0 Docs](https://developers.google.com/identity/protocols/oauth2)
