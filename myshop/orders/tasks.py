import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from .models import Order

# Get an instance of a logger
logger = logging.getLogger(__name__)


@shared_task
def order_created(order_id):
    """
    Celery task to send an email notification when an order is created.

    This task runs asynchronously to prevent blocking the user's request/response
    cycle during checkout. It retrieves the order by ID and sends a confirmation email.

    Args:
        order_id (int): The primary key of the newly created Order.

    Returns:
        int: The number of emails successfully delivered (typically 1).
    """
    try:
        order = Order.objects.get(id=order_id)

        subject = _("Order Confirmation - Order nr. {}").format(order.id)

        message = _(
            "Dear {name},\n\n"
            "You have successfully placed an order. "
            "Your order ID is {id}."
        ).format(name=order.first_name, id=order.id)

        mail_sent = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=False,
        )

        logger.info(f"Order confirmation email sent for Order {order_id}")
        return mail_sent

    except Order.DoesNotExist:
        logger.error(
            f"Failed to send confirmation email: Order {order_id} does not exist."
        )
    except Exception as e:
        logger.error(
            f"Error sending order confirmation email for Order {order_id}: {e}"
        )


@shared_task
def send_order_status_update_email(order_id, new_status):
    """
    Send an email to the customer notifying them of a change in order status.

    Args:
        order_id (int): The ID of the order being updated.
        new_status (str): The new status key (e.g., 'shipped', 'delivered').
    """
    try:
        # Select related tracking info if available to avoid extra DB hits later
        order = Order.objects.select_related("tracking").get(id=order_id)

        # Mapping status keys to user-friendly, translatable messages
        status_messages = {
            "confirmed": _("Your order has been confirmed."),
            "preparing": _("We are preparing your order."),
            "shipped": _("Your order has been shipped."),
            "delivered": _("Your order has been delivered."),
            "cancelled": _("Your order has been cancelled."),
        }

        # Default subject fallback
        subject_text = status_messages.get(
            new_status, _("Update on order #{}").format(order.id)
        )
        subject = f"{subject_text} - One Synk"

        context = {
            "order": order,
            "status": new_status,
            "status_display": order.get_status_display(),
            "subject": subject,
        }

        # Try to render HTML template, fall back to plain text if template missing/fails
        try:
            html_message = render_to_string(
                "orders/emails/order_status_update.html", context
            )
            plain_message = render_to_string(
                "orders/emails/order_status_update.txt", context
            )
        except Exception:
            # Fallback plain text generation if templates fail
            tracking_info = ""
            if (
                hasattr(order, "tracking")
                and order.tracking
                and order.tracking.tracking_url
            ):
                tracking_info = _("You can track your shipment at: {}").format(
                    order.tracking.tracking_url
                )

            plain_message = _(
                "Hello {name},\n\n"
                "{subject}\n\n"
                "Order ID: {id}\n"
                "New Status: {status}\n\n"
                "{tracking}\n\n"
                "Best regards,\nThe One Synk Team"
            ).format(
                name=order.first_name,
                subject=subject_text,
                id=order.id,
                status=order.get_status_display(),
                tracking=tracking_info,
            )
            html_message = None

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"Status update email ({new_status}) sent to {order.email} for Order {order.id}"
        )

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for status update.")
    except Exception as e:
        logger.error(f"Error sending status update email for Order {order_id}: {e}")


@shared_task
def send_order_tracking_email(order_id):
    """
    Send an email with tracking information when an order is shipped.

    Args:
        order_id (int): Order ID.
    """
    try:
        order = Order.objects.select_related("tracking").get(id=order_id)

        if not hasattr(order, "tracking") or not order.tracking:
            logger.warning(
                f"Order {order_id} has no tracking information. Email skipped."
            )
            return

        tracking = order.tracking
        subject = _("Your order #{} has been shipped - Tracking available").format(
            order.id
        )

        context = {
            "order": order,
            "tracking": tracking,
            "subject": subject,
        }

        try:
            html_message = render_to_string(
                "orders/emails/order_tracking.html", context
            )
            plain_message = render_to_string(
                "orders/emails/order_tracking.txt", context
            )
        except Exception:
            # Fallback plain text
            tracking_link = ""
            if tracking.tracking_url:
                tracking_link = _("Tracking link: {}").format(tracking.tracking_url)

            est_delivery = (
                tracking.estimated_delivery_date
                if tracking.estimated_delivery_date
                else _("To be determined")
            )

            plain_message = _(
                "Hello {name},\n\n"
                "Your order #{id} has been shipped.\n\n"
                "Shipment details:\n"
                "Tracking number: {track_num}\n"
                "Carrier: {carrier}\n\n"
                "{link}\n\n"
                "Estimated delivery date: {date}\n\n"
                "Best regards,\nThe One Synk Team"
            ).format(
                name=order.first_name,
                id=order.id,
                track_num=tracking.tracking_number,
                carrier=tracking.get_carrier_display(),
                link=tracking_link,
                date=est_delivery,
            )
            html_message = None

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Tracking email sent to {order.email} for Order {order.id}")

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for tracking email.")
    except Exception as e:
        logger.error(f"Error sending tracking email for Order {order_id}: {e}")
