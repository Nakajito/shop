"""PDF receipt + staff admin-detail views for orders."""

import logging

import weasyprint
from django.apps import apps
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from orders.models import Order

from ._helpers import get_user_order

logger = logging.getLogger(__name__)

PDF_STYLESHEET_PATH = "css/pdf.css"


def _render_invoice_pdf(request, order, *, filename, disposition="filename"):
    """Render the invoice PDF template and return it as an HTTP response."""
    html_string = render_to_string("orders/order/pdf.html", {"order": order})
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'{disposition}="{filename}"' if disposition == "attachment" else f"{disposition}={filename}"
    )
    weasyprint.HTML(
        string=html_string, base_url=request.build_absolute_uri("/")
    ).write_pdf(
        response,
        stylesheets=[weasyprint.CSS(finders.find(PDF_STYLESHEET_PATH))],
    )
    return response


@staff_member_required
def admin_order_detail(request, order_id):
    """Staff-only internal order summary."""
    order = get_object_or_404(Order, id=order_id)

    opts = order._meta
    try:
        app_config = apps.get_app_config(opts.app_label)
    except LookupError:
        app_config = None

    context = {"order": order, "opts": opts, "app_config": app_config}
    return render(request, "admin/orders/order/detail.html", context)


@staff_member_required
def admin_order_pdf(request, order_id):
    """Staff-side invoice PDF (inline disposition)."""
    order = get_object_or_404(Order, id=order_id)
    return _render_invoice_pdf(
        request, order, filename=f"order_{order.id}.pdf", disposition="filename"
    )


@login_required
@require_http_methods(["GET"])
def order_pdf(request, order_id):
    """Customer receipt PDF download."""
    try:
        order = get_user_order(request, order_id)
        return _render_invoice_pdf(
            request,
            order,
            filename=f"receipt_order_{order.id}.pdf",
            disposition="attachment",
        )
    except Exception as e:
        logger.error(f"Error generating PDF for order {order_id}: {e!s}")
        messages.error(request, _("Error generating the receipt PDF."))
        return redirect("orders:order_history")
