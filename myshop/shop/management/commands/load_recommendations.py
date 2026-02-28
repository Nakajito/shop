from django.core.management.base import BaseCommand
from orders.models import Order
from shop.models import Product
from shop.recommender import Recommender


class Command(BaseCommand):
    help = "Load recommendation data from existing paid orders into Redis."

    def handle(self, *args, **options):
        rec = Recommender()
        paid_orders = Order.objects.filter(paid=True)
        count = 0

        for order in paid_orders:
            product_ids = order.items.values_list("product_id", flat=True)
            products = list(Product.objects.filter(id__in=product_ids))
            if len(products) > 1:
                rec.products_bought(products)
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Loaded recommendations from {count} orders.")
        )
