import os
from app.main import app
from app.core import db
os.environ['FRONTEND_ORIGIN']='http://localhost:5174'
os.environ['ADMIN_USERNAME']='qa-admin'
os.environ['ADMIN_PASSWORD']='qa-password-only-123'
db.LOCAL_DB='.work/portal-browser-test.sqlite3'
