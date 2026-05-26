import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from orders.models import Order
from support.forms import SupportTicketForm, TicketMessageForm
from support.models import SupportTicket

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def ticket_list(request):
    """
    Lists all support tickets for the current user with filtering and pagination.
    """
    tickets = request.user.support_tickets.select_related("order", "assigned_to").order_by("-created_at")

    # Filters
    status_filter = request.GET.get("status")
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    # Pagination
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Statistics for the dashboard
    stats = {
        "open": request.user.support_tickets.filter(status="open").count(),
        "in_progress": request.user.support_tickets.filter(
            status="in_progress"
        ).count(),
        "resolved": request.user.support_tickets.filter(status="resolved").count(),
        "total": request.user.support_tickets.count(),
    }

    context = {
        "tickets": page_obj,
        "stats": stats,
        "current_status": status_filter,
        "page_title": _("My Support Tickets"),
    }

    return render(request, "support/ticket_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def ticket_create(request, order_id=None):
    """
    Handles support ticket creation, optionally linked to a specific order.
    """
    order = None
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        form = SupportTicketForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    ticket = form.save(commit=False)
                    ticket.user = request.user
                    ticket.save()

                    messages.success(
                        request,
                        _("Support ticket created successfully. ID: #%(id)s")
                        % {"id": ticket.id},
                    )
                    return redirect("support:ticket_detail", ticket_id=ticket.id)
            except Exception as e:
                logger.error(f"Error creating ticket: {str(e)}")
                messages.error(
                    request, _("An error occurred while creating the ticket.")
                )
        else:
            messages.error(request, _("Please correct the errors in the form."))
    else:
        initial_data = {"order": order} if order else {}
        form = SupportTicketForm(initial=initial_data, user=request.user)

    context = {
        "form": form,
        "order": order,
        "page_title": _("Create Support Ticket"),
    }
    return render(request, "support/ticket_form.html", context)


@login_required
@require_http_methods(["GET"])
def ticket_detail(request, ticket_id):
    """
    Displays the details and message history of a specific ticket.
    """
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    # Hide internal staff notes from the customer
    messages_list = ticket.messages.select_related("sender").filter(is_internal=False).order_by("created_at")
    form = TicketMessageForm()

    context = {
        "ticket": ticket,
        "messages": messages_list,
        "form": form,
        "page_title": _("Ticket #%(id)s") % {"id": ticket.id},
    }
    return render(request, "support/ticket_detail.html", context)


@login_required
@require_http_methods(["POST"])
def ticket_reply(request, ticket_id):
    """
    Handles customer replies to an existing ticket.
    """
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    form = TicketMessageForm(request.POST)

    if form.is_valid():
        try:
            with transaction.atomic():
                message = form.save(commit=False)
                message.ticket = ticket
                message.sender = request.user
                message.is_internal = False
                message.save()

                # Reopen ticket if it was resolved or closed
                if ticket.status in ["resolved", "closed"]:
                    ticket.status = "open"
                    ticket.resolved_at = None
                    ticket.save()

                messages.success(request, _("Your reply has been sent."))
        except Exception as e:
            logger.error(f"Error replying to ticket {ticket_id}: {str(e)}")
            messages.error(request, _("Error sending reply."))
    else:
        messages.error(request, _("Invalid message content."))

    return redirect("support:ticket_detail", ticket_id=ticket_id)


@login_required
@require_http_methods(["POST"])
def ticket_close(request, ticket_id):
    """
    Allows the user to manually close their own ticket.
    """
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)

    if ticket.status != "closed":
        ticket.status = "closed"
        ticket.save()
        messages.success(request, _("Ticket closed successfully."))
    else:
        messages.info(request, _("This ticket is already closed."))

    return redirect("support:ticket_detail", ticket_id=ticket_id)
