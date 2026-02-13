from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.paginator import Paginator
from support.models import SupportTicket, TicketMessage
from support.forms import SupportTicketForm, TicketMessageForm
from orders.models import Order
import logging

logger = logging.getLogger(__name__)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def ticket_list(request):
    """
    Vista para listar todos los tickets de soporte del usuario.
    GET: Muestra todos los tickets con filtros
    """

    tickets = request.user.support_tickets.all().order_by("-created_at")

    # Filtros
    status_filter = request.GET.get("status")
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    # Paginación
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Estadísticas
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
        "page_title": "Mis Tickets de Soporte",
    }

    return render(request, "support/ticket_list.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def ticket_create(request, order_id=None):
    """
    Vista para crear un nuevo ticket de soporte.
    GET: Muestra formulario
    POST: Crea el ticket
    """

    order = None
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        form = SupportTicketForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear ticket
                    ticket = form.save(commit=False)
                    ticket.user = request.user
                    ticket.save()

                    messages.success(
                        request,
                        f"Ticket de soporte creado exitosamente. " f"ID: #{ticket.id}",
                    )

                    return redirect("support:ticket_detail", ticket_id=ticket.id)

            except Exception as e:
                logger.error(f"Error creando ticket: {str(e)}")
                messages.error(request, f"Error al crear ticket: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        initial_data = {}
        if order:
            initial_data["order"] = order
        form = SupportTicketForm(initial=initial_data, user=request.user)

    context = {
        "form": form,
        "order": order,
        "page_title": "Crear Ticket de Soporte",
    }

    return render(request, "support/ticket_form.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def ticket_detail(request, ticket_id):
    """
    Vista para ver detalles de un ticket.
    GET: Muestra ticket y mensajes
    """

    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    messages_list = ticket.messages.filter(is_internal=False).order_by("created_at")
    form = TicketMessageForm()

    context = {
        "ticket": ticket,
        "messages": messages_list,
        "form": form,
        "page_title": f"Ticket #{ticket.id}",
    }

    return render(request, "support/ticket_detail.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def ticket_reply(request, ticket_id):
    """
    Vista para responder a un ticket.
    POST: Agrega mensaje al ticket
    """

    try:
        ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)

        form = TicketMessageForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Crear mensaje
                message = form.save(commit=False)
                message.ticket = ticket
                message.sender = request.user
                message.is_internal = False
                message.save()

                # Cambiar estado a "waiting_customer" (esperando respuesta del staff)
                if ticket.status == "resolved":
                    ticket.status = "open"
                    ticket.save()

                messages.success(request, "Tu respuesta ha sido enviada.")
        else:
            messages.error(request, "Error al enviar la respuesta.")

    except Exception as e:
        logger.error(f"Error respondiendo ticket: {str(e)}")
        messages.error(request, f"Error al enviar respuesta: {str(e)}")

    return redirect("support:ticket_detail", ticket_id=ticket_id)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def ticket_close(request, ticket_id):
    """
    Vista para cerrar un ticket.
    POST: Cierra el ticket
    """

    try:
        ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)

        if ticket.status != "closed":
            ticket.status = "closed"
            ticket.save()
            messages.success(request, "Ticket cerrado exitosamente.")
        else:
            messages.info(request, "Este ticket ya estaba cerrado.")

    except Exception as e:
        logger.error(f"Error cerrando ticket: {str(e)}")
        messages.error(request, f"Error al cerrar ticket: {str(e)}")

    return redirect("support:ticket_detail", ticket_id=ticket_id)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def ticket_create_for_order(request, order_id):
    """
    Alias para crear ticket desde una orden.
    Redirige a ticket_create con order_id
    """

    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if request.method == "POST":
            return ticket_create(request, order_id=order_id)

        # GET: Redirigir a ticket_create
        return redirect("support:ticket_create", order_id=order_id)

    except:
        messages.error(request, "Orden no encontrada.")
        return redirect("orders:order_history")
