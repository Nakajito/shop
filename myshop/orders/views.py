from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.staticfiles import finders
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import models, transaction
import weasyprint
import logging

from cart.cart import Cart
from orders.forms import OrderCreateForm, AddressForm
from orders.models import Order, OrderItem, Address, OrderStatusUpdate, OrderTracking
from orders.tasks import order_created

# Configurar logger para registro de errores
logger = logging.getLogger(__name__)


def get_user_order(request, order_id):
    """
    Helper function to get an order accessible by the current user.
    Allows access to orders that:
    1. Have the current user as owner (user = request.user)
    2. Have the same email as the current user (for legacy orders before user field)

    Returns the Order or raises Http404 if not found or not accessible.
    """
    try:
        # Try to get order by user (new orders)
        return Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        # Try to get order by email (legacy orders without user field)
        order = get_object_or_404(Order, id=order_id, email=request.user.email)
        return order


def order_create(request):
    """
    View to handle the creation of a new order.

    Process:
    1. Instantiates the cart to access current items.
    2. On POST, validates the user's shipping data (OrderCreateForm).
    3. Creates the Order object (pausing save with commit=False to apply coupons).
    4. Transfers items from the session Cart to database OrderItem records.
    5. Clears the cart session.
    6. Triggers the asynchronous 'order_created' email task.
    7. Stores the order ID in the session for the payment gateway.
    8. Redirects to the payment processing view.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: Renders the checkout page (on GET) or redirects to
        payment (on success).
    """
    cart = Cart(request)

    # If the user is authenticated, obtain their default payment method.
    if request.user.is_authenticated:
        default_payment_method = request.user.payment_methods.filter(
            is_default=True, is_active=True
        ).first()
    else:
        default_payment_method = None

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # Create order object but don't save to DB yet
            order = form.save(commit=False)

            # Apply coupon if one exists in the cart
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount

            # Now save the order to the database
            order.save()

            # Create a database record for each item in the cart
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )

            # clear the cart
            cart.clear()

            # launch asynchronous task
            order_created.delay(order.id)

            # set order status to 'pending'
            order.status = "pending"
            order.change_status(
                "pending",
                changed_by=request.user if request.user.is_authenticated else None,
                reason="Order created, pending payment",
            )

            # set the order in the session for the payment step
            request.session["order_id"] = order.id

            # redirect for payment
            return redirect("payment:process")

    else:
        form = OrderCreateForm()

    return render(
        request,
        "orders/order/create.html",
        {"cart": cart, "form": form, "default_payment_method": default_payment_method},
    )


@staff_member_required
def admin_order_detail(request, order_id):
    """
    Custom admin view to display order details.

    This view is accessible only by staff members and provides a read-only
    summary of the order, used by the 'View' link in the Order Admin list.
    """
    order = get_object_or_404(Order, id=order_id)
    return render(request, "admin/orders/order/detail.html", {"order": order})


@staff_member_required
def admin_order_pdf(request, order_id):
    """
    Generate a PDF invoice for a specific order.

    Uses WeasyPrint to render an HTML template into a PDF document.
    It automatically locates the CSS file using Django's static file finders.

    Args:
        request (HttpRequest): The incoming request.
        order_id (int): ID of the order to print.

    Returns:
        HttpResponse: A response with content_type='application/pdf'.
    """
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string("orders/order/pdf.html", {"order": order})

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"filename=order_{order.id}.pdf"

    # render PDF with CSS
    weasyprint.HTML(string=html).write_pdf(
        response,
        stylesheets=[weasyprint.CSS(finders.find("css/pdf.css"))],
    )

    return response


@login_required
@require_http_methods(["GET"])
def order_pdf(request, order_id):
    """
    Vista para que el USUARIO descargue su recibo en PDF.
    GET: Genera y descarga PDF del recibo.
    """
    try:
        # Aseguramos que la orden pertenezca al usuario actual
        order = get_user_order(request, order_id)

        # Renderizar plantilla HTML
        # Nota: Usamos la plantilla existente 'orders/order/pdf.html'.
        # Si prefieres una distinta, cambia a 'orders/pdf/order_receipt.html'
        html_string = render_to_string("orders/order/pdf.html", {"order": order})

        # Configurar respuesta HTTP
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="recibo_pedido_{order.id}.pdf"'
        )

        # Convertir a PDF
        # Incluimos base_url y stylesheets para que carguen las imágenes y CSS correctamente
        html = weasyprint.HTML(
            string=html_string, base_url=request.build_absolute_uri("/")
        )

        html.write_pdf(
            response, stylesheets=[weasyprint.CSS(finders.find("css/pdf.css"))]
        )

        return response

    except Exception as e:
        logger.error(f"Error generando PDF para orden {order_id}: {str(e)}")
        messages.error(request, "Error al generar el PDF del recibo.")
        # Redirige a la lista de historial o al detalle si ocurre un error
        return redirect(
            "orders:order_history"
        )  # Asegúrate que esta URL existe en urls.py


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def address_list(request):
    """
    View to list all user addresses.
    GET: Displays all addresses
    """

    addresses = request.user.addresses.all().order_by("-is_default", "-created_at")

    context = {
        "addresses": addresses,
        "page_title": "My address",
        "total_addresses": addresses.count(),
    }

    return render(request, "orders/addresses/list.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def address_create(request):
    """
    View to create new address.
    GET: Display form
    POST: Save new address
    """

    if request.method == "POST":
        form = AddressForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    address = form.save(commit=False)
                    address.user = request.user
                    address.save()

                    messages.success(request, "Address successfully added.")

                    # Redirect to the next page if coming from checkout
                    next_url = request.GET.get("next")
                    if next_url:
                        return redirect(next_url)

                    return redirect("orders:address_list")

            except Exception as e:
                messages.error(request, f"Error saving address: {str(e)}")

    else:
        form = AddressForm()

    context = {
        "form": form,
        "page_title": "Add New Address",
        "is_create": True,
    }

    return render(request, "orders/addresses/form.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def address_edit(request, address_id):
    """
    View to edit existing address.
    GET: Displays form with current data
    POST: Saves changes
    """

    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, "Address successfully updated.")
                    return redirect("orders:address_list")

            except Exception as e:
                messages.error(request, f"Error updating address: {str(e)}")

    else:
        form = AddressForm(instance=address)

    context = {
        "form": form,
        "address": address,
        "page_title": f"Edit Address - {address.recipient_name}",
        "is_create": False,
    }

    return render(request, "orders/addresses/form.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def address_delete(request, address_id):
    """
    View to delete address.
    GET: Shows confirmation
    POST: Deletes address
    """

    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        try:
            address_info = str(address)
            address.delete()
            messages.success(request, f'Address "{address_info}" Successfully deleted.')
            return redirect("orders:address_list")

        except Exception as e:
            messages.error(request, f"Error deleting address: {str(e)}")

    context = {
        "address": address,
        "page_title": "Delete Address",
    }

    return render(request, "orders/addresses/confirm_delete.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def address_set_default(request, address_id):
    """
    View to set default address.
    POST only for security.
    """

    address = get_object_or_404(Address, id=address_id, user=request.user)

    try:
        address.is_default = True
        address.save()

        messages.success(request, "Address set as default.")

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")

    # Redirigir a origen o a lista de direcciones
    next_url = request.GET.get("next")
    return redirect(next_url if next_url else "orders:address_list")


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def order_history(request):
    """
    Vista mejorada para ver el historial de compras del usuario.
    Incluye filtros, búsqueda y estadísticas.
    GET: Muestra todas las órdenes del usuario con opciones de filtro.
    """

    # Obtener todas las órdenes del usuario
    orders = request.user.orders.all().order_by("-created")

    # Filtros
    status_filter = request.GET.get("status")
    payment_filter = request.GET.get("payment")
    search_query = request.GET.get("q")

    # Aplicar filtro de estado
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Aplicar filtro de pago
    if payment_filter:
        if payment_filter == "paid":
            orders = orders.filter(paid=True)
        elif payment_filter == "unpaid":
            orders = orders.filter(paid=False)

    # Aplicar búsqueda por ID o email
    if search_query:
        orders = orders.filter(
            models.Q(id__icontains=search_query)
            | models.Q(email__icontains=search_query)
        )

    # Paginación
    from django.core.paginator import Paginator

    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Estadísticas
    all_orders = request.user.orders.all()
    stats = {
        "total_orders": all_orders.count(),
        "total_spent": sum(o.get_total() for o in all_orders),
        "delivered_orders": all_orders.filter(status="delivered").count(),
        "pending_orders": all_orders.filter(
            status__in=["pending", "confirmed"]
        ).count(),
        "cancelled_orders": all_orders.filter(status="cancelled").count(),
    }

    # Opciones de filtro para dropdown
    status_choices = [
        ("", "Todos los estados"),
        ("pending", "Pendiente"),
        ("confirmed", "Confirmado"),
        ("preparing", "Preparando"),
        ("shipped", "Enviado"),
        ("delivered", "Entregado"),
        ("cancelled", "Cancelado"),
    ]

    payment_choices = [
        ("", "Todos los pagos"),
        ("paid", "Pagado"),
        ("unpaid", "No pagado"),
    ]

    context = {
        "orders": page_obj,
        "stats": stats,
        "status_choices": status_choices,
        "payment_choices": payment_choices,
        "current_status": status_filter,
        "current_payment": payment_filter,
        "search_query": search_query,
        "page_title": "Mis Compras",
    }

    return render(request, "orders/order/order_history.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def order_detail(request, order_id):
    """
    View to see complete details of an order.
    GET: Displays complete order information.
    """

    order = get_user_order(request, order_id)
    items = order.items.all()

    context = {
        "order": order,
        "items": items,
        "page_title": f"Order #{order.id}",
    }

    return render(request, "orders/order/order_detail.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def order_tracking(request, order_id):
    """
    Vista para ver el seguimiento completo de un pedido.
    Muestra timeline de cambios de estado e información de envío.
    GET: Muestra información de tracking del pedido
    """

    order = get_user_order(request, order_id)

    # Obtener historial de cambios de estado
    status_updates = order.status_updates.all().order_by("-created_at")

    # Obtener información de tracking
    tracking = order.tracking if hasattr(order, "tracking") else None

    # Obtener timeline de pasos
    timeline_steps = order.get_timeline_steps()

    context = {
        "order": order,
        "status_updates": status_updates,
        "tracking": tracking,
        "timeline_steps": timeline_steps,
        "page_title": f"Seguimiento de Pedido #{order.id}",
    }

    return render(request, "orders/order/order_tracking.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def order_status_history(request, order_id):
    """
    Vista para ver el historial detallado de cambios de estado.
    GET: Muestra todos los cambios de estado con detalles
    """

    order = get_user_order(request, order_id)
    status_updates = order.status_updates.all().order_by("-created_at")

    context = {
        "order": order,
        "status_updates": status_updates,
        "page_title": f"Historial de Estado - Pedido #{order.id}",
    }

    return render(request, "orders/order/order_status_history.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def order_tracking_info(request, order_id):
    """
    Vista para ver información detallada de envío/tracking.
    GET: Muestra datos del carrier, número de guía, ubicación actual
    """

    order = get_user_order(request, order_id)
    tracking = get_object_or_404(OrderTracking, order=order)

    context = {
        "order": order,
        "tracking": tracking,
        "page_title": f"Información de Envío - Pedido #{order.id}",
    }

    return render(request, "orders/order/order_tracking_info.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def reorder(request, order_id):
    """
    Vista para reordenar una compra anterior.
    Copia todos los items de una orden anterior al carrito.
    POST: Agrega items al carrito
    """

    try:
        order = get_user_order(request, order_id)

        # Validar que la orden pueda reordenarse
        if not order.can_be_reordered():
            messages.error(
                request, "Solo puedes reordenar pedidos entregados o cancelados."
            )
            return redirect("orders:order_detail", order_id=order_id)

        # Obtener carrito
        from cart.cart import Cart

        cart = Cart(request)

        # Verificar disponibilidad de productos y agregar al carrito
        items_added = 0
        for item in order.items.all():
            # Verificar que el producto aún existe y está disponible
            if item.product and item.product.available:
                # Agregar al carrito
                cart.add(
                    product=item.product,
                    quantity=item.quantity,
                    override_quantity=False,
                )
                items_added += 1
            else:
                messages.warning(
                    request,
                    f'Producto "{item.product.name}" no está disponible actualmente.',
                )

        if items_added > 0:
            messages.success(
                request,
                f"{items_added} producto(s) agregado(s) al carrito. "
                f"Total en carrito: {len(cart)} artículos.",
            )
            return redirect("cart:cart_detail")
        else:
            messages.error(request, "No hay productos disponibles para reordenar.")
            return redirect("orders:order_detail", order_id=order_id)

        request.session["reordered_from"] = order.id

    except Exception as e:
        logger.error(f"Error reordenando: {str(e)}")
        messages.error(request, f"Error al reordenar: {str(e)}")
        return redirect("orders:order_history")


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def cancel_order(request, order_id):
    """
    View to cancel an order.
    Only allows cancellation if the status is pending or confirmed.
    GET: Shows confirmation.
    POST: Cancels the order and issues a refund if it was paid.
    """

    try:
        order = get_user_order(request, order_id)

        if request.method == "POST":
            # Confirm that it can be canceled
            if not order.can_be_cancelled():
                messages.error(
                    request,
                    "This order cannot be canceled. "
                    "Only pending or confirmed orders can be canceled.",
                )
                return redirect("orders:order_detail", order_id=order_id)

            # Obtain reason for cancellation (optional)
            reason = request.POST.get("reason", "User requested cancellation")

            with transaction.atomic():
                # Change status to canceled
                order.change_status("cancelled", changed_by=request.user, reason=reason)

                # Si fue pagado, procesar reembolso con Stripe
                if order.paid and order.stripe_id:
                    try:
                        import stripe
                        from django.conf import settings

                        stripe.api_key = settings.STRIPE_SECRET_KEY

                        # Revertir el PaymentIntent
                        intent = stripe.PaymentIntent.retrieve(order.stripe_id)

                        # Si el status es succeeded, crear un refund
                        if intent.status == "succeeded":
                            refund = stripe.Refund.create(
                                payment_intent=order.stripe_id,
                                reason="requested_by_customer",
                            )

                            logger.info(
                                f"Reembolso procesado para orden {order.id}: "
                                f"Stripe Refund ID {refund.id}"
                            )

                            messages.success(
                                request,
                                "Pedido cancelado. Tu reembolso será procesado "
                                "en 5-10 días hábiles.",
                            )
                        else:
                            messages.warning(
                                request,
                                "Pedido cancelado, pero no se pudo procesar "
                                "el reembolso automáticamente. "
                                "Por favor contacta a soporte.",
                            )

                    except stripe.error.StripeError as e:
                        logger.error(f"Error al procesar reembolso: {str(e)}")
                        messages.warning(
                            request,
                            "Pedido cancelado, pero hubo un error al "
                            "procesar el reembolso. Nos contactaremos pronto.",
                        )
                else:
                    messages.success(request, "Pedido cancelado exitosamente.")

            return redirect("orders:order_history")

        else:
            # GET - Mostrar confirmación
            context = {
                "order": order,
                "page_title": f"Cancelar Pedido #{order.id}",
            }
            return render(request, "orders/order/cancel_order.html", context)

    except Exception as e:
        logger.error(f"Error cancelando pedido: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect("orders:order_history")
