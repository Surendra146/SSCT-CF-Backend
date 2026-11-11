from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=True)
from fastapi import FastAPI
from .core.middleware import EnvironmentMiddleware
from .routers import register, admin, catalog
from .core.auth import bootstrap_admin
from .core.db import init_local
app = FastAPI(title='SSCT API', docs_url=None, redoc_url=None)
import os
origin = os.environ.get('FRONTEND_ORIGIN', 'http://localhost:5173')
app.add_middleware(EnvironmentMiddleware)

@app.middleware('http')
async def response_security(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    if request.url.path.startswith('/api/admin'):
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response
app.include_router(register.router)
app.include_router(admin.router)

@app.get('/api/health')
async def health():
    return {'ok': True}

@app.on_event('startup')
async def startup():
    import sys
    if sys.platform=='emscripten':return
    init_local()
    await bootstrap_admin()
app.include_router(catalog.router)
