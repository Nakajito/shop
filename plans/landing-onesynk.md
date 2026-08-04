# Plan — Publicar home.html como landing real en el repo `onesynk`

## Contexto

El landing corporativo (`myshop/shop/templates/shop/home.html`, repo `shop`) es el contenido
completo y terminado (imágenes reales, textos de misión/visión/filosofía/valores, email real). El
repo separado `Nakajito/onesynk` (Django 6, ya desplegado en `onesynk.com.mx` vía Coolify +
Cloudflare, staging en `thrill.onesynk.com.mx`) tiene hoy un `templates/index.html` que es
claramente un placeholder sin terminar: email `hello@reallygreatsite.com`, footer con categorías
genéricas de suplementos ("Falcon Protein", "Creatina") que no son de comida coreana, secciones
Misión/Visión/Filosofía sin texto, y sin imágenes reales (solo cajas con CSS). El objetivo es que
`home.html` reemplace ese placeholder y sea lo que realmente sirve `onesynk.com.mx`.

Verificado clonando `Nakajito/onesynk` (rama `main`, sin otras ramas) a un directorio temporal:
Django 6 con `core/` (una sola app), `templates/` (`base.html` + `includes/{navbar,footer,sidebar}.html`
compartidos, Bootstrap 5 vía CDN) y una página `synkfood.html` que el propio `CLAUDE.md` del repo
documenta como **excepción intencional**: "fully self-contained HTML document... does NOT extend
base.html... treat it as a separate brand skin". `config/urls.py` ya tiene `path("", views.home,
name="home")` → `core/views.py: home()` → `render(request, "index.html")` — no hace falta tocar
ninguno de los dos.

## Dónde queda guardado este plan

Dos copias, ambas creadas en la fase de ejecución (pasos 0a/0b más abajo):

- **`plans/landing-onesynk.md`** en la raíz de este repo (`shop`) — para retomarlo desde esta misma
  sesión/proyecto más adelante, sin depender de que el archivo temporal de plan mode siga existiendo.
- **`onesynk/docs/plans/landing-real.md`**, dentro del repo `onesynk` — para que al abrir Claude
  Code directamente ahí, una sesión sin memoria de esta conversación pueda retomarlo sin
  re-explorar todo desde cero.

## Cómo continuar esto desde una sesión nueva en el repo `onesynk`

Contexto que esa sesión necesita y no va a tener por sí sola:

- **El HTML fuente vive en otro repositorio**: `Nakajito/shop`, archivo
  `myshop/shop/templates/shop/home.html`. Si hace falta reconsultarlo (por ejemplo si cambió desde
  que se escribió este plan), ese es el origen — no existe copia de referencia dentro de `onesynk`
  hasta que el paso 1 de abajo se ejecute.
- **Decisiones ya tomadas y confirmadas con el usuario** (no volver a preguntarlas):
  - `index.html` se trata como documento autónomo, igual que `synkfood.html` — sin
    `{% extends 'base.html' %}`, sin tocar `base.html`/`includes/`.
  - El botón "Synk Food" enlaza a la tienda real `https://synkfood.onesynk.com.mx/`, no a la
    página `synkfood.html` interna de este mismo repo.
  - El trabajo va en una rama dedicada (`feat/landing-real`), nunca directo a `main`.
  - Tres imágenes (`PRIMERA-PANTALLA-01.png`, `TERCERA.png`, `FOODSYNK.png`) se redimensionan/
    recomprimen antes de copiarlas — están a resolución de impresión (9000px+) en el origen.
- **Estado al guardar este documento**: plan aprobado, ejecución aún no iniciada. Si se abre esta
  sesión y ya existe la rama `feat/landing-real` con commits, verificar con `git log` qué de los
  pasos 1-4 ya se hizo antes de repetir trabajo.

## Enfoque

Tratar `index.html` igual que `synkfood.html` ya trata su propio caso: documento autónomo con su
propio `<head>`/navbar/footer/CSS, sin `{% extends 'base.html' %}`. Es el patrón que el propio repo
ya documenta para este tipo de página, y es el cambio más chico posible — no toca `base.html` ni
los includes compartidos, que quedan disponibles tal cual para futuras páginas que sí quieran seguir
ese otro patrón.

0a. **Guardar copia en este repo (`shop`)**: crear `plans/landing-onesynk.md` en la raíz de este
    proyecto con el contenido completo de este documento — para poder retomarlo desde aquí sin
    depender del archivo temporal de plan mode.

0b. **Guardar copia en el repo `onesynk`**: crear `onesynk/docs/plans/landing-real.md` con el mismo
    contenido, como primer commit de la rama dedicada (paso 4) — disponible ahí para cualquier
    sesión futura de Claude Code abierta directamente en ese repo.

1. **Reemplazar `templates/index.html`** con el contenido completo de `home.html`, con solo estas
   adaptaciones de URLs (todo lo demás — `{% load static %}`, `{% load i18n %}`, `{% trans %}`,
   `{% blocktrans %}`, `{% static %}` — funciona sin cambios: `onesynk` tiene `USE_I18N = True` y
   `django.contrib.staticfiles` instalado):
   - `{% url 'shop:home' %}` (logo del navbar y del footer, 2 apariciones) → `{% url 'home' %}`,
     el nombre de ruta que ya existe en `onesynk`.
   - `{% url 'shop:synkfood' %}` (imagen, badge y botón "CONOCER MÁS" de la tarjeta Synk Food, 3
     apariciones) → `https://synkfood.onesynk.com.mx/` con `target="_blank" rel="noopener"` (mismo
     patrón que ya usa el link de Synk Beauty en el propio archivo) — la tienda real, donde
     efectivamente se puede comprar.
   - `{% include 'includes/lang_toggle.html' with css_class='os-nav__lang-form' %}` (línea 55) →
     se quita. No existe ese include en `onesynk`, y su navbar actual tampoco tiene selector de
     idioma funcional (solo un ícono decorativo).

2. **Copiar los assets que usa `home.html`** a `onesynk/static/` (no existen ahí hoy — el repo solo
   tiene `static/img/hero.webp`):
   - `css/onesynk.css` → `onesynk/static/css/onesynk-landing.css` (nombre distinto al `css/onesynk/style.css`
     que ya existe, para no pisarlo — ese sigue siendo el CSS del sistema `base.html`/Bootstrap,
     intacto para cuando se agregue una próxima página real que sí lo use). Actualizar el `<link>`
     del nuevo `index.html` a este nombre.
   - Imágenes a `onesynk/static/img/onesynk/`: `01.png, 04.png, 05.png, 06.png, 07.png, 08.png,
     09.png, 10.png, 11.png, FOODSYNK.png, LOGO.png, logo-sinfood.svg, PRIMERA-PANTALLA-01.png,
     SEGUNDA-01.png, TERCERA.png` — y a `onesynk/static/img/`: `LOGOTIPO-ROSA.png`, `mac_bueno.png`.
   - Se **copian**, no se mueven — siguen existiendo en `shop/static/` porque otras plantillas de
     ese repo (`synkfood.html`, `shop/product/list.html`, `includes/navbar.html`/`footer.html`) los
     siguen usando.

3. **Optimizar 3 imágenes antes de copiarlas** (hallazgo, no pedido explícitamente pero relevante
   para que la landing realmente funcione bien): `PRIMERA-PANTALLA-01.png` (25MB, 9000×5706px) y
   `TERCERA.png` (13MB, 9000×4409px) son exports a resolución de impresión sin redimensionar para
   web — cargarían en decenas de segundos en una conexión normal. `FOODSYNK.png` (2.9MB) también
   pesa más de lo necesario para su tamaño de despliegue en pantalla. Redimensiono estas 3 a un
   ancho máximo razonable (2400px, de sobra para pantallas 4K en un fondo de sección) y las
   recomprimo con Pillow (`optimize=True`) antes de copiarlas — incluido en este plan porque una
   landing que tarda 40+ segundos en cargar no cumple el objetivo de "que funcione como landing
   page". El resto de imágenes (todas <30KB) se copian tal cual.

4. **Rama dedicada**: crear `feat/landing-real` a partir de `main` en `Nakajito/onesynk`, commitear
   ahí (mensaje conventional commit en español, siguiendo la convención ya usada en ese repo según
   su `AGENTS.md`: `feat(core): reemplaza landing placeholder con contenido real`) y hacer push de
   esa rama — no se toca `main` directamente. Dejo la rama lista para que el usuario la revise y
   decida cómo mergearla (PR o merge directo cuando esté conforme).

## Verificación

- `uv run djlint templates/ --check` en `onesynk` (ya está configurado como lint de templates ahí,
  según su `AGENTS.md`).
- `uv run python manage.py check` bajo settings de `onesynk`.
- `uv run python manage.py runserver` local, visitar `/` — confirmar que carga con imágenes/CSS/JS
  del nuevo landing, sin 404 en consola del navegador.
- Confirmar que el botón "Synk Food" abre `https://synkfood.onesynk.com.mx/` en pestaña nueva, y
  que "Synk Beauty" sigue apuntando a `https://synkbeauty.dabg.dev/` (sin cambios, no se toca).
- Confirmar que `synkfood.html` (la otra página del repo `onesynk`) sigue funcionando igual — no se
  modifica nada de lo que usa.
- Tras el push, verificar que Coolify redeploya `onesynk.com.mx` (o disparar el redeploy manualmente
  si ese repo no tiene un webhook de auto-deploy en push a `main` — no confirmado en este plan, el
  `AGENTS.md` de `onesynk` no menciona CI/CD automático, solo el Dockerfile/coolify.json).
