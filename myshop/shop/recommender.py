import redis
from django.conf import settings
from .models import Product

# Connect to Redis using settings
r = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB
)


class Recommender:
    """
    A product recommendation engine based on 'Frequently Bought Together' logic.

    This class uses Redis Sorted Sets to store and retrieve product relationships.
    When products are bought together, their relationship score is incremented.
    """

    def get_product_key(self, id):
        """
        Generate the Redis key for a specific product's relationship set.

        Format: 'product:{id}:purchased_with'
        """
        return f"product:{id}:purchased_with"

    def products_bought(self, products):
        """
        Record that a list of products were purchased together.

        Iterates through the list of products and updates the Redis Sorted Set
        for each item, incrementing the score for every other item in the same
        batch.

        Args:
            products (list): A list of Product objects.
        """
        product_ids = [p.id for p in products]

        for product_id in product_ids:
            for with_id in product_ids:
                # get the other products bought with each product
                if product_id != with_id:
                    # increment score for product purchased together
                    r.zincrby(self.get_product_key(product_id), 1, with_id)

    def suggest_products_for(self, products, max_results=6):
        """
        Suggest products based on a list of input products.

        Logic:
        1. If single product: Retrieve the top-ranked items from its Redis Sorted Set.
        2. If multiple products:
           - Create a temporary Redis key.
           - Perform a ZUNIONSTORE (Union) of all input products' sets to sum scores.
           - Remove the input products themselves from the results.
           - Retrieve top results and delete the temporary key.

        Args:
            products (list): List of Product objects to base suggestions on.
            max_results (int): Maximum number of suggestions to return.

        Returns:
            list: A list of Product objects, sorted by relevance.
        """
        product_ids = [p.id for p in products]

        if len(products) == 1:
            # only 1 product
            suggestions = r.zrange(
                self.get_product_key(product_ids[0]), 0, -1, desc=True
            )[:max_results]
        else:
            # generate a temporary key based on the IDs
            flat_ids = "".join([str(id) for id in product_ids])
            tmp_key = f"tmp_{flat_ids}"

            # multiple products, combine scores of all products
            # store the resulting sorted set in a temporary key
            keys = [self.get_product_key(id) for id in product_ids]
            r.zunionstore(tmp_key, keys)

            # remove ids for the products the recommendation is for
            r.zrem(tmp_key, *product_ids)

            # get the product ids by their score, descendant sort
            suggestions = r.zrange(tmp_key, 0, -1, desc=True)[:max_results]

            # remove the temporary key
            r.delete(tmp_key)

        suggested_products_ids = [int(id) for id in suggestions]

        # get suggested products from DB and sort by order of appearance in Redis
        suggested_products = list(Product.objects.filter(id__in=suggested_products_ids))
        suggested_products.sort(key=lambda x: suggested_products_ids.index(x.id))

        return suggested_products

    def clear_purchases(self):
        """
        Clear all recommendation data from Redis.
        Useful for testing or resetting the engine.
        """
        for id in Product.objects.values_list("id", flat=True):
            r.delete(self.get_product_key(id))
