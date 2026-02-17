from django.db import models


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.filter(available=True)

    def by_category(self, category):
        return self.filter(category=category)

    def with_category(self):
        return self.select_related("category")


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def available(self):
        return self.get_queryset().available()

    def by_category(self, category):
        return self.get_queryset().by_category(category)

    def with_category(self):
        return self.get_queryset().with_category()
