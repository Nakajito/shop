from celery import shared_task
from django.core.mail import send_mail
from .models import Order


@shared_task
def order_created(order_id):
    """
    Celery task to send an email notification when an order is created.

    This task runs asynchronously to prevent blocking the user's request/response
    cycle during checkout. It retrieves the order by ID and sends a simple
    text-based confirmation email.

    Args:
        order_id (int): The primary key of the newly created Order.

    Returns:
        int: The number of emails successfully delivered (typically 1).
    """
    order = Order.objects.get(id=order_id)
    subject = f"Order nr. {order.id}"
    message = (
        f"Dear {order.first_name},\n\n"
        f"You have successfully placed an order. "
        f"Your order ID is {order.id}."
    )

    # Send the email using the address configured in settings (or hardcoded here)
    mail_sent = send_mail(subject, message, "db212748@gmail.com", [order.email])

    return mail_sent
