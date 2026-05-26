import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import OrderTracking
from .tasks import send_order_tracking_email

logger = logging.getLogger(__name__)


@receiver(post_save, sender=OrderTracking)
def tracking_created(sender, instance, created, **kwargs):
    """Dispatch tracking email when a new OrderTracking record is created."""
    if created:
        logger.info(
            f"OrderTracking created for Order {instance.order.id}. "
            "Dispatching tracking email."
        )
        send_order_tracking_email.delay(instance.order.id)
