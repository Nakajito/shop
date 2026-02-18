from django.db import models


class SupportTicketQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def open_tickets(self):
        return self.filter(status="open")

    def with_messages(self):
        return self.prefetch_related("messages", "messages__sender")


class SupportTicketManager(models.Manager):
    def get_queryset(self):
        return SupportTicketQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def open_tickets(self):
        return self.get_queryset().open_tickets()

    def with_messages(self):
        return self.get_queryset().with_messages()
