"""
ASGI config for videochat project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import chat.routing
import videocall.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')

application = ProtocolTypeRouter({
    "http" :  get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns +
            videocall.routing.websocket_urlpatterns
        )
    ),
})
