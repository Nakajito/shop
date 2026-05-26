import logging
from io import BytesIO

import weasyprint
from celery import shared_task
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from orders.models import Order

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def payment_completed(self, order_id):
    """Send an email with an attached PDF invoice when an order is paid."""
    try:
        order = Order.objects.get(id=order_id)

        subject = _("One Synk - Invoice nr. {}").format(order.id)
        message = _(
            "Thank you for your purchase! Please find attached the invoice for your recent order."
        )

        email = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
        )

        html_content = render_to_string("orders/order/pdf.html", {"order": order})
        out = BytesIO()

        css_path = finders.find("css/pdf.css")
        stylesheets = [weasyprint.CSS(css_path)] if css_path else []

        weasyprint.HTML(string=html_content).write_pdf(out, stylesheets=stylesheets)

        attachment_name = _("invoice_order_{}.pdf").format(order.id)
        email.attach(attachment_name, out.getvalue(), "application/pdf")

        email.send()
        logger.info(f"Invoice email sent successfully for Order {order_id}")

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found. Not retrying.")
    except Exception as exc:
        logger.warning(
            f"Retry {self.request.retries}/{self.max_retries} for "
            f"payment_completed (Order {order_id}): {exc}"
        )
        raise self.retry(exc=exc) from exc
