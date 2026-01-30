from io import BytesIO
import weasyprint
from celery import shared_task
from django.contrib.staticfiles import finders
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from orders.models import Order


@shared_task
def payment_completed(order_id):
    """
    Task to send an email notification with an attached PDF invoice when an
    order is successfully paid.

    This task performs the following steps asynchronously:
    1. Retrieves the Order object from the database.
    2. Renders the 'orders/order/pdf.html' template into an HTML string.
    3. Uses WeasyPrint to convert that HTML into a PDF byte stream (in-memory).
    4. Creates an EmailMessage with the PDF attached.
    5. Sends the email to the customer.

    Args:
        order_id (int): The primary key of the paid Order.
    """
    order = Order.objects.get(id=order_id)

    # Create the email object
    subject = f"My Shop - Invoice no. {order.id}"
    message = "Please, find attached the invoice for your recent purchase."
    email = EmailMessage(
        subject,
        message,
        "db212748@gmail.com",  # From email
        [order.email],  # To email
    )

    # Generate PDF from HTML template
    html = render_to_string("orders/order/pdf.html", {"order": order})

    # Create an in-memory byte stream to hold the PDF data
    out = BytesIO()

    # Locate CSS files for WeasyPrint
    stylesheets = [weasyprint.CSS(finders.find("css/pdf.css"))]

    # Write the PDF to the byte stream
    weasyprint.HTML(string=html).write_pdf(out, stylesheets=stylesheets)

    # Attach the PDF file to the email
    # getvalue() retrieves the entire content of the BytesIO buffer
    email.attach(f"order_{order.id}.pdf", out.getvalue(), "application/pdf")

    # Send the email
    email.send()
