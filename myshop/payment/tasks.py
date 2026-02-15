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

# Initialize logger
logger = logging.getLogger(__name__)


@shared_task
def payment_completed(order_id):
    """
    Task to send an email notification with an attached PDF invoice when an
    order is successfully paid.
    """
    try:
        order = Order.objects.get(id=order_id)

        # Create the email object with localized subject
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

        # Generate PDF logic
        html_content = render_to_string("orders/order/pdf.html", {"order": order})
        out = BytesIO()

        # Locate the CSS file
        css_path = finders.find("css/pdf.css")
        stylesheets = [weasyprint.CSS(css_path)] if css_path else []

        # Generate PDF to memory buffer
        # We use a dummy base_url to help resolve local relative paths if needed
        weasyprint.HTML(string=html_content).write_pdf(out, stylesheets=stylesheets)

        # Attach the PDF
        attachment_name = _("invoice_order_{}.pdf").format(order.id)
        email.attach(attachment_name, out.getvalue(), "application/pdf")

        # Send the email
        email.send()
        logger.info(f"Invoice email sent successfully for Order {order_id}")

    except Order.DoesNotExist:
        logger.error(f"Failed to send invoice: Order {order_id} not found.")
    except Exception as e:
        logger.error(f"Error in payment_completed task for Order {order_id}: {str(e)}")
