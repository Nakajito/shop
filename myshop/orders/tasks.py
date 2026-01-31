from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging
from .models import Order

logger = logging.getLogger(__name__)


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


@shared_task
def send_order_status_update_email(order_id, new_status):
    """
    Send an email to the customer notifying them of the change in order status.

    Args:
        order_id: Order ID
        new_status: New order status
    """
    try:
        order = Order.objects.get(id=order_id)

        # Mapping states to user-friendly messages
        status_messages = {
            "confirmed": "Your order has been confirmed.",
            "preparing": "We are preparing your order.",
            "shipped": "Your order has been shipped.",
            "delivered": "Your order has been delivered.",
            "cancelled": "Your order has been cancelled.",
        }

        subject = status_messages.get(new_status, f"Update on order #{order.id}")

        # Render email template
        context = {
            "order": order,
            "status": new_status,
            "status_display": order.get_status_display(),
        }

        # Try using an HTML template, otherwise use plain text.
        try:
            message = render_to_string(
                "orders/emails/order_status_update.html", context
            )
        except Exception:
            message = f"""
            Hello {order.first_name},
            
            {subject}
            
            Order ID: {order.id}
            Status: {order.get_status_display()}
            
            {"You can track your shipment at: " + order.tracking.tracking_url if hasattr(order, 'tracking') and order.tracking else ""}
            
            Best regards,
            The Shop Team
            """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            html_message=message if "<html" in message else None,
            fail_silently=False,
        )

        logger.info(f"Status update email sent to {order.email} for order {order.id}")

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
    except Exception as e:
        logger.error(f"Error sending status update email: {str(e)}")


@shared_task
def send_order_tracking_email(order_id):
    """
    Send an email with tracking information when an order is shipped.

    Args:
        order_id: Order ID
    """
    try:
        order = Order.objects.select_related("tracking").get(id=order_id)

        if not hasattr(order, "tracking") or not order.tracking:
            logger.warning(f"Order {order_id} has no tracking information")
            return

        tracking = order.tracking

        subject = f"Your order #{order.id} has been shipped - Tracking available"

        context = {
            "order": order,
            "tracking": tracking,
        }

        try:
            message = render_to_string("orders/emails/order_tracking.html", context)
        except Exception:
            message = f"""
            Hello {order.first_name},
            
            Your order #{order.id} has been shipped.
            
            Shipment details:
            Tracking number: {tracking.tracking_number}
            Carrier: {tracking.get_carrier_display()}
            
            {"Tracking link: " + tracking.tracking_url if tracking.tracking_url else ""}
            
            Estimated delivery date: {tracking.estimated_delivery_date if tracking.estimated_delivery_date else 'To be determined'}
            
            Best regards,
            The Shop Team
            """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            html_message=message if "<html" in message else None,
            fail_silently=False,
        )

        logger.info(f"Tracking email sent to {order.email} for order {order.id}")

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
    except Exception as e:
        logger.error(f"Error sending tracking email: {str(e)}")
