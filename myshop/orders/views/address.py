"""Shipping address CRUD for the authenticated user."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from myshop.utils import safe_next_url
from orders.forms import AddressForm
from orders.models import Address

logger = logging.getLogger(__name__)


@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, "orders/addresses/list.html", {"addresses": addresses})


@login_required
@require_http_methods(["GET", "POST"])
def address_create(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, _("New address saved."))
            return redirect("orders:address_list")
    else:
        form = AddressForm()
    return render(
        request, "orders/addresses/form.html", {"form": form, "is_create": True}
    )


@login_required
@require_http_methods(["GET", "POST"])
def address_edit(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, _("Address updated successfully."))
            return redirect("orders:address_list")
    else:
        form = AddressForm(instance=address)
    return render(
        request, "orders/addresses/form.html", {"form": form, "is_create": False}
    )


@require_POST
@login_required
def address_delete(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, _("Address deleted."))
    return redirect("orders:address_list")


@login_required
@require_POST
def address_set_default(request, address_id):
    """Mark an address as the user's default."""
    address = get_object_or_404(Address, id=address_id, user=request.user)

    try:
        address.is_default = True
        address.save()  # the model unsets other defaults
        messages.success(request, _("Address set as default."))
    except Exception as e:
        logger.error(f"Error setting default address: {e}")
        messages.error(request, _("Could not update default address."))

    return redirect(safe_next_url(request, "orders:address_list"))
