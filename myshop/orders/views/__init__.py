"""Orders views — split by domain.

Re-exports the public view callables so legacy imports like
``from orders import views`` and ``views.order_create`` keep working
without changing ``urls.py`` or external references.
"""

from .address import (
    address_create,
    address_delete,
    address_edit,
    address_list,
    address_set_default,
)
from .order import (
    buy_order,
    cancel_order,
    order_create,
    order_detail,
    order_history,
    order_status_history,
    order_tracking,
    order_tracking_info,
    reorder,
)
from .pdf import admin_order_detail, admin_order_pdf, order_pdf

__all__ = [
    # order lifecycle
    "buy_order",
    "cancel_order",
    "order_create",
    "order_detail",
    "order_history",
    "order_status_history",
    "order_tracking",
    "order_tracking_info",
    "reorder",
    # pdf + admin
    "admin_order_detail",
    "admin_order_pdf",
    "order_pdf",
    # address management
    "address_create",
    "address_delete",
    "address_edit",
    "address_list",
    "address_set_default",
]
