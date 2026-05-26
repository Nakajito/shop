import logging

import redis
from django.conf import settings

from .models import Product

logger = logging.getLogger(__name__)


def _get_redis():
    """Get a Redis connection, returning None if unavailable."""
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
        )
        r.ping()
        return r
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return None


class Recommender:
    """
    A product recommendation engine based on 'Frequently Bought Together' logic.
    Uses Redis Sorted Sets to store and rank product relationships.
    """

    def get_product_key(self, product_id: int) -> str:
        """Generates the Redis key for a specific product's set."""
        return f"product:{product_id}:purchased_with"

    def products_bought(self, products: list[Product]):
        """
        Records that a list of products were purchased together.
        Uses a Pipeline to execute all updates in a single network request.
        """
        r = _get_redis()
        if not r:
            return

        product_ids = [p.id for p in products]

        # Use a pipeline for atomicity and speed
        pipe = r.pipeline()
        for product_id in product_ids:
            for with_id in product_ids:
                if product_id != with_id:
                    # Increment the relationship score
                    pipe.zincrby(self.get_product_key(product_id), 1, with_id)
        pipe.execute()

    def suggest_products_for(self, products, max_results=6):
        r = _get_redis()
        if not r:
            return []

        product_ids = [p.id for p in products]

        if len(products) == 1:
            # Single product
            suggestions = r.zrange(
                self.get_product_key(product_ids[0]), 0, max_results - 1, desc=True
            )
        else:
            # Multiple products
            flat_ids = "".join([str(id) for id in product_ids])
            tmp_key = f"tmp_{flat_ids}"
            keys = [self.get_product_key(id) for id in product_ids]

            r.zunionstore(tmp_key, keys)
            r.zrem(tmp_key, *product_ids)

            suggestions = r.zrange(tmp_key, 0, max_results - 1, desc=True)

            r.delete(tmp_key)

        suggested_products_ids = [int(id) for id in suggestions]
        suggested_products = list(Product.objects.filter(id__in=suggested_products_ids))
        suggested_products.sort(key=lambda x: suggested_products_ids.index(x.id))

        return suggested_products

    def clear_purchases(self):
        """Clears all recommendation data from Redis."""
        r = _get_redis()
        if not r:
            return

        product_ids = Product.objects.values_list("id", flat=True)
        keys = [self.get_product_key(pid) for pid in product_ids]
        if keys:
            r.delete(*keys)
