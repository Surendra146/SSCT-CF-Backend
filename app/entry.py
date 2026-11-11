# Cloudflare Python Workers provides the ASGI environment on request.scope['env'].
from workers import asgi
from .main import app
Default = asgi.entrypoint(app)
