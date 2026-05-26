"""Shared helpers for orders views."""

from django.shortcuts import get_object_or_404

from orders.models import Order


def get_user_order(request, order_id):
    """Return the order if it belongs to the authenticated request user."""
    return get_object_or_404(Order, id=order_id, user=request.user)
