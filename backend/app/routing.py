from django.urls import re_path
from . import consumers
from .consumers import ChatConsumer


websocket_urlpatterns = [
    re_path(
        r"ws/chat/(?P<room_id>[A-Z0-9]+)/$",
        ChatConsumer.as_asgi()
    ),
]

# routing.py defines the WebSocket URL patterns for the Django Channels application.
## It maps WebSocket URL routes to their corresponding consumer classes.
## In this case, the 'ws/chat/<room_code>/' URL is routed to the ChatConsumer.
## Additional Applications of routing
## include defining URL patterns for multiple consumers, handling different WebSocket endpoints,
## and organizing the routing logic for complex real-time applications.
## This modular approach helps maintain clean and scalable code for WebSocket communication.