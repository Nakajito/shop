from django.db import models


class OrderQuerySet(models.QuerySet):
    def with_items(self):
        return self.prefetch_related("items", "items__product")

    def with_tracking(self):
        return self.select_related("tracking")

    def with_full_details(self):
        return (
            self.select_related(
                "user",
                "shipping_address",
                "billing_address",
                "coupon",
                "payment_method",
                "tracking",
            )
            .prefetch_related("items", "items__product")
        )

    def for_user(self, user):
        return self.filter(user=user)

    def by_status(self, status):
        return self.filter(status=status)

    def paid_orders(self):
        return self.filter(paid=True)


class OrderManager(models.Manager):
    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db)

    def with_items(self):
        return self.get_queryset().with_items()

    def with_tracking(self):
        return self.get_queryset().with_tracking()

    def with_full_details(self):
        return self.get_queryset().with_full_details()

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def by_status(self, status):
        return self.get_queryset().by_status(status)

    def paid_orders(self):
        return self.get_queryset().paid_orders()
