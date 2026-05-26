from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from blog.models import Category as BlogCategory
from blog.models import Post, Tag
from shop.models import Category, Product

SHOP_CATEGORIES = [
    ("Fideos e Instantáneos", "fideos-instantaneos"),
    ("Salsas y Condimentos", "salsas-condimentos"),
    ("Snacks y Dulces", "snacks-dulces"),
]

PRODUCTS = [
    ("Fideos e Instantáneos", "Ramyeon Shin Picante 120g", "1.80",
     "Fideos instantáneos coreanos de sabor picante intenso. Marca clásica, listos en 4 minutos."),
    ("Fideos e Instantáneos", "Buldak Carbonara 130g", "2.30",
     "Fideos extremadamente picantes con salsa cremosa estilo carbonara. Edición popular de Samyang."),
    ("Fideos e Instantáneos", "Jjapaghetti Fideos Negros 140g", "2.10",
     "Fideos con salsa de pasta de soja negra (jjajang). Inspirados en el plato chino-coreano clásico."),
    ("Fideos e Instantáneos", "Tteokbokki Instantáneo Copo 120g", "3.50",
     "Pasteles de arroz en salsa gochujang. Listo en microondas, textura masticable."),
    ("Salsas y Condimentos", "Gochujang Pasta Pimiento 500g", "8.90",
     "Pasta fermentada de chile rojo. Base esencial de la cocina coreana, picante y dulce."),
    ("Salsas y Condimentos", "Doenjang Pasta de Soja 500g", "7.50",
     "Pasta de soja fermentada. Imprescindible para sopas (jjigae) y marinados."),
    ("Salsas y Condimentos", "Salsa de Soja Coreana Premium 500ml", "6.20",
     "Ganjang tradicional, sabor profundo y equilibrado. Ideal para banchan y salteados."),
    ("Snacks y Dulces", "Choco Pie Caja 12 unidades", "5.40",
     "Galletas de malvavisco bañadas en chocolate. Snack icónico coreano."),
    ("Snacks y Dulces", "Algas Tostadas Nori 5 paquetes", "3.80",
     "Láminas de alga marina sazonadas con aceite de sésamo y sal. Snack crujiente y ligero."),
    ("Snacks y Dulces", "Pepero Palitos de Chocolate 47g", "1.50",
     "Galletas finas recubiertas de chocolate. El snack del 11 de noviembre en Corea."),
]

BLOG_CATEGORIES = [
    ("Recetas Coreanas", "recetas-coreanas"),
    ("Cultura y Tradición", "cultura-tradicion"),
    ("Guías de Producto", "guias-de-producto"),
]

TAGS = ["ramyeon", "kimchi", "picante", "fermentados", "snacks"]

POSTS = [
    ("Cómo Preparar el Ramyeon Perfecto",
     "Trucos de cocineros coreanos para llevar tu ramyeon al siguiente nivel",
     "Recetas Coreanas",
     ["ramyeon", "picante"],
     "<h2>Más allá del paquete</h2><p>El ramyeon instantáneo es delicioso tal cual, "
     "pero unos pocos extras lo transforman en una comida completa.</p>"
     "<h3>1. Huevo en el momento justo</h3><p>Añádelo en los últimos 90 segundos para una yema cremosa.</p>"
     "<h3>2. Queso fundido</h3><p>Una loncha de queso americano suaviza el picante y aporta cremosidad.</p>"
     "<h3>3. Cebolleta y ajo</h3><p>Frescos al final, realzan el aroma del caldo.</p>"
     "<h3>4. Kimchi al lado</h3><p>El contraste ácido y picante completa el plato.</p>"),

    ("El Kimchi: Historia y Variedades",
     "Más de 200 tipos de kimchi conviven en la mesa coreana",
     "Cultura y Tradición",
     ["kimchi", "fermentados"],
     "<p>El kimchi es el alma de la cocina coreana. Su fermentación se remonta a más de "
     "2.000 años, cuando se conservaban vegetales para sobrevivir al invierno.</p>"
     "<h3>Baechu kimchi</h3><p>El más conocido, hecho con col china y pasta de chile.</p>"
     "<h3>Kkakdugi</h3><p>Kimchi de rábano cortado en cubos, crujiente y refrescante.</p>"
     "<h3>Oi sobagi</h3><p>Pepino relleno, típico del verano.</p>"),

    ("Guía del Gochujang: Usos y Conservación",
     "El comodín fermentado que necesitas en tu nevera",
     "Guías de Producto",
     ["fermentados", "picante"],
     "<p>El gochujang es una pasta de chile fermentada con arroz glutinoso y soja. "
     "Aporta picante, dulzor y umami simultáneamente.</p>"
     "<h3>Usos principales</h3><ul><li>Base del tteokbokki y el bibimbap.</li>"
     "<li>Marinado para cerdo y pollo.</li><li>Mezclado con mayo: salsa coreana fusión.</li></ul>"
     "<h3>Conservación</h3><p>Refrigerado tras abrir. Dura hasta 2 años sin perder calidad.</p>"),

    ("Bibimbap Casero en 20 Minutos",
     "El plato bandera de Corea, paso a paso",
     "Recetas Coreanas",
     ["recetas"],
     "<p>Bibimbap significa literalmente «arroz mezclado». Es un cuenco equilibrado de arroz, "
     "verduras salteadas, proteína y huevo, todo coronado con gochujang.</p>"
     "<ul><li>Saltea por separado espinacas, zanahoria, brotes de soja y champiñones.</li>"
     "<li>Cocina el arroz al vapor.</li><li>Añade carne picada salteada con salsa de soja.</li>"
     "<li>Corona con huevo a la plancha y una cucharada de gochujang.</li></ul>"),

    ("Snacks Coreanos que Debes Probar",
     "Una vuelta dulce y salada por los pasillos coreanos",
     "Guías de Producto",
     ["snacks"],
     "<p>Más allá del ramyeon, los snacks coreanos son toda una cultura. Selección imprescindible:</p>"
     "<h3>Choco Pie</h3><p>Galleta con malvavisco y chocolate. Nostalgia en cada bocado.</p>"
     "<h3>Pepero</h3><p>Palitos de chocolate que tienen su propio día (11 de noviembre).</p>"
     "<h3>Algas tostadas</h3><p>Crujientes, ligeras y adictivas. Perfectas con cerveza.</p>"
     "<h3>Honey Butter Chips</h3><p>Patatas dulces y mantecosas que arrasaron en redes.</p>"),
]


class Command(BaseCommand):
    help = "Carga contenido demo: 3 categorías, 10 productos, 5 entradas de blog. Idempotente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--author-username",
            default="demo_author",
            help="Username para autor de las entradas de blog. Se crea si no existe.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        self._seed_shop_categories()
        self._seed_products()
        author = self._ensure_author(opts["author_username"])
        self._seed_blog(author)
        self.stdout.write(self.style.SUCCESS("Demo cargado."))

    def _seed_shop_categories(self):
        for name, slug in SHOP_CATEGORIES:
            obj, created = Category.objects.get_or_create(
                slug=slug, defaults={"name": name}
            )
            self._log("Categoría", obj.name, created)

    def _seed_products(self):
        for cat_name, name, price, desc in PRODUCTS:
            category = Category.objects.get(name=cat_name)
            obj, created = Product.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    "category": category,
                    "name": name,
                    "price": Decimal(price),
                    "description": desc,
                    "available": True,
                },
            )
            self._log("Producto", obj.name, created)

    def _ensure_author(self, username):
        User = get_user_model()
        author = User.objects.filter(username=username).first()
        if author:
            return author
        author = User.objects.filter(is_superuser=True).first()
        if author:
            return author
        author = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=User.objects.make_random_password()
            if hasattr(User.objects, "make_random_password")
            else "demo-password-change-me",
        )
        self.stdout.write(self.style.WARNING(
            f"Autor creado: {username} (contraseña temporal, cámbiala)."
        ))
        return author

    def _seed_blog(self, author):
        for name, slug in BLOG_CATEGORIES:
            BlogCategory.objects.get_or_create(slug=slug, defaults={"name": name})
        tag_objs = {
            name: Tag.objects.get_or_create(
                slug=slugify(name), defaults={"name": name}
            )[0]
            for name in TAGS
        }
        for title, subtitle, cat_name, tag_names, body in POSTS:
            slug = slugify(title)
            category = BlogCategory.objects.get(name=cat_name)
            post, created = Post.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "subtitle": subtitle,
                    "body": body,
                    "author": author,
                    "category": category,
                    "status": Post.Status.PUBLISHED,
                },
            )
            if created:
                post.tags.set(tag_objs[t] for t in tag_names if t in tag_objs)
            self._log("Post", post.title, created)

    def _log(self, kind, name, created):
        verb = "creado" if created else "ya existía"
        style = self.style.SUCCESS if created else self.style.NOTICE
        self.stdout.write(style(f"{kind}: {name} ({verb})"))
