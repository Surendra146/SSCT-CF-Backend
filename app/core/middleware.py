from starlette.middleware.cors import CORSMiddleware
from .db import worker_env
from .auth import secret

class EnvironmentMiddleware:
    def __init__(self, app):self.app=app

    async def __call__(self, scope, receive, send):
        token=worker_env.set(scope.get('env'))
        try:
            cors=CORSMiddleware(self.app,
                allow_origins=[secret('FRONTEND_ORIGIN') or 'http://localhost:5173'],
                allow_credentials=True,allow_methods=['GET','POST','PATCH','DELETE','OPTIONS'],
                allow_headers=['Content-Type','X-CSRF-Token'])
            await cors(scope,receive,send)
        finally:worker_env.reset(token)
