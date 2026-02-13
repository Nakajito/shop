from django.urls import path
from support import views

app_name = "support"

urlpatterns = [
    # Tickets
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/create/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:ticket_id>/reply/", views.ticket_reply, name="ticket_reply"),
    path("tickets/<int:ticket_id>/close/", views.ticket_close, name="ticket_close"),
    # Crear ticket desde orden
    path(
        "tickets/order/<int:order_id>/",
        views.ticket_create_for_order,
        name="ticket_create_for_order",
    ),
]
