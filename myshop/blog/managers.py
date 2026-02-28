from django.db import models


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status="published")

    def drafts(self):
        return self.filter(status="draft")

    def by_author(self, user):
        return self.filter(author=user)

    def by_category(self, category):
        return self.filter(category=category)

    def by_tag(self, tag):
        return self.filter(tags=tag)

    def with_relations(self):
        return self.select_related("author", "category").prefetch_related("tags")

    def search(self, query):
        return self.filter(
            models.Q(title__icontains=query)
            | models.Q(subtitle__icontains=query)
            | models.Q(body__icontains=query)
        )


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def drafts(self):
        return self.get_queryset().drafts()

    def by_author(self, user):
        return self.get_queryset().by_author(user)

    def by_category(self, category):
        return self.get_queryset().by_category(category)

    def by_tag(self, tag):
        return self.get_queryset().by_tag(tag)

    def with_relations(self):
        return self.get_queryset().with_relations()

    def search(self, query):
        return self.get_queryset().search(query)
