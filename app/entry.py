# Cloudflare Python Workers provides the ASGI environment on request.scope['env'].
from workers import asgi
from app.main import app

Default = asgi.entrypoint(app)
