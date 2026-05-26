from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    # Ticket Dashboard & Management
    path("", views.ticket_list, name="ticket_list"),
    # Ticket Creation
    path("create/", views.ticket_create, name="ticket_create"),
    path(
        "create/order/<int:order_id>/",
        views.ticket_create,
        name="ticket_create_for_order",
    ),
    # Ticket Interaction
    path("<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
    path("<int:ticket_id>/reply/", views.ticket_reply, name="ticket_reply"),
    path("<int:ticket_id>/close/", views.ticket_close, name="ticket_close"),
]
