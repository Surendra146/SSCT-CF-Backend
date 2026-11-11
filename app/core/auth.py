import os, hmac, hashlib, secrets, time
from fastapi import Request, HTTPException
from .db import worker_env, rows, execute
COOKIE = 'ssct_admin_session'

def secret(name):
    env = worker_env.get()
    return getattr(env, name, None) if env is not None else os.environ.get(name)

from .passwords import hash_password, hash_password_async, verify_password as _verify_password, UnsupportedPasswordHash

async def verify_password(password, encoded):
    try:
        return await _verify_password(password, encoded)
    except UnsupportedPasswordHash as error:
        raise HTTPException(503, 'Administrator password requires an approved runtime migration.') from error

async def bootstrap_admin():
    username, password, encoded = (secret('ADMIN_USERNAME'), secret('ADMIN_PASSWORD'), secret('ADMIN_PASSWORD_HASH'))
    if not username or not (password or encoded):
        return
    if not await rows('SELECT id FROM admin_users WHERE username=?', (username,)):
        await execute('INSERT OR IGNORE INTO admin_users(username,password_hash,name) VALUES(?,?,?)', (username, encoded or await hash_password_async(password), secret('ADMIN_NAME') or 'Admin'))

def session_minutes():
    return max(1, min(int(secret('ADMIN_IDLE_MINUTES') or 15), 60))

def check_origin(request):
    origin = request.headers.get('origin')
    allowed = secret('FRONTEND_ORIGIN') or 'http://localhost:5173'
    if origin and origin != allowed:
        raise HTTPException(403, 'Untrusted request origin')

async def check(request: Request):
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, 'Please sign in')
    sid = hashlib.sha256(token.encode()).hexdigest()
    found = await rows('SELECT s.*,u.username,u.name,u.role FROM admin_sessions s JOIN admin_users u ON u.id=s.user_id WHERE s.id=?', (sid,))
    now = int(time.time())
    if not found:
        raise HTTPException(401, 'Session expired. Please sign in again')
    session = found[0]
    if session['expires_at'] <= now or session['last_seen'] + session_minutes() * 60 <= now:
        await execute('DELETE FROM admin_sessions WHERE id=?', (sid,))
        raise HTTPException(401, 'Session expired. Please sign in again')
    if session['role'] != 'admin':
        raise HTTPException(403, 'Administrator access required')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        check_origin(request)
        if not hmac.compare_digest(request.headers.get('x-csrf-token', ''), session['csrf']):
            raise HTTPException(403, 'Invalid CSRF token')
    await execute('UPDATE admin_sessions SET last_seen=? WHERE id=?', (now, sid))
    return session
