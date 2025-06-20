from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from images.consumers import UploadProgressConsumer

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/upload-progress/<uuid:batch_id>/', UploadProgressConsumer.as_asgi()),
        ])
    ),
})