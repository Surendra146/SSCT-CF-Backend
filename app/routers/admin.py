import hashlib, secrets, time, json, csv, io
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from pydantic import ValidationError
from ..schemas.register import LoginRequest, RegistrationCreate, EnquiryCreate, StatusUpdate
from ..schemas.content import Content
from ..core.auth import check, secret, COOKIE, bootstrap_admin, verify_password, check_origin, session_minutes
from ..core.db import rows, execute
from ..core.passwords import DUMMY_HASH
from ..core.content import list_content, get_content, save_content, audit, today
from .register import register, enquiry
router = APIRouter(prefix='/api/admin', tags=['admin'])
STATUSES = {'New', 'Contacted', 'In Process', 'Enrolled', 'Closed'}

def profile(s):
    return {k: s[k] for k in ('username', 'name', 'role', 'csrf')}

@router.post('/login')
@router.post('/auth/login')
async def login(data: LoginRequest, request: Request, response: Response):
    check_origin(request)
    await bootstrap_admin()
    now = int(time.time())
    address = request.headers.get('cf-connecting-ip') if secret('TRUST_CLOUDFLARE_IP') == 'true' else None
    identity = hashlib.sha256((address or (request.client.host if request.client else 'unknown')).encode()).hexdigest()
    await execute('DELETE FROM login_attempts WHERE attempted_at<?', (now - 900,))
    await execute('INSERT INTO login_attempts(identity,attempted_at) VALUES(?,?)', (identity, now))
    if (await rows('SELECT COUNT(*) AS n FROM login_attempts WHERE identity=? AND attempted_at>?', (identity, now - 900)))[0]['n'] > 5:
        raise HTTPException(429, 'Too many login attempts. Try again in 15 minutes')
    user = await rows('SELECT * FROM admin_users WHERE username=?', (data.username,))
    if not user or not await verify_password(data.password, user[0]['password_hash']):
        if not user:
            await verify_password(data.password, DUMMY_HASH)
        raise HTTPException(401, 'Invalid credentials')
    await execute('DELETE FROM login_attempts WHERE identity=?', (identity,))
    token = secrets.token_urlsafe(40)
    csrf = secrets.token_urlsafe(32)
    await execute('DELETE FROM admin_sessions WHERE expires_at<=? OR last_seen<?', (now, now - session_minutes() * 60))
    old = request.cookies.get(COOKIE)
    if old:
        await execute('DELETE FROM admin_sessions WHERE id=?', (hashlib.sha256(old.encode()).hexdigest(),))
    await execute('INSERT INTO admin_sessions(id,user_id,csrf,expires_at,last_seen) VALUES(?,?,?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), user[0]['id'], csrf, now + 28800, now))
    secure = request.url.scheme == 'https' or secret('COOKIE_SECURE') == 'true'
    response.set_cookie(COOKIE, token, max_age=28800, httponly=True, secure=secure, samesite='none' if secure else 'lax', path='/api/admin')
    await audit(user[0]['username'], 'login', 'admin', user[0]['id'])
    return {**{k: user[0][k] for k in ('username', 'name', 'role')}, 'csrf': csrf, 'idle_minutes': session_minutes()}

@router.get('/auth/me')
async def me(s=Depends(check)):
    return {**profile(s), 'idle_minutes': session_minutes()}

@router.post('/auth/logout')
async def logout(request: Request, response: Response):
    check_origin(request)
    token = request.cookies.get(COOKIE)
    if token:
        await execute('DELETE FROM admin_sessions WHERE id=?', (hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie(COOKIE, path='/api/admin')
    return {'ok': True}

@router.get('/settings')
async def settings(s=Depends(check)):
    return {'name': s['name'], 'username': s['username'], 'role': s['role'], 'idle_minutes': session_minutes(), 'timezone': 'Asia/Kolkata', 'absolute_session_hours': 8}

@router.patch('/settings')
async def save_settings(data: dict, s=Depends(check)):
    name = str(data.get('name', '')).strip()
    if not 2 <= len(name) <= 120:
        raise HTTPException(422, 'Name must contain 2–120 characters')
    if data.get('new_password'):
        from ..core.auth import hash_password_async
        current = (await rows('SELECT password_hash FROM admin_users WHERE id=?', (s['user_id'],)))[0]
        if not await verify_password(data.get('current_password', ''), current['password_hash']):
            raise HTTPException(400, 'Current password is incorrect')
        if not 12 <= len(data['new_password']) <= 128:
            raise HTTPException(422, 'Use a password containing 12–128 characters')
        await execute('UPDATE admin_users SET password_hash=? WHERE id=?', (await hash_password_async(data['new_password']), s['user_id']))
        await execute('DELETE FROM admin_sessions WHERE user_id=? AND id!=?', (s['user_id'], s['id']))
    await execute('UPDATE admin_users SET name=? WHERE id=?', (name, s['user_id']))
    await audit(s['username'], 'updated', 'settings', s['user_id'])
    return {'ok': True}

def range_dates(start=None, end=None):
    end = date.fromisoformat(end) if end else today()
    start = date.fromisoformat(start) if start else end.replace(day=1)
    if end < start or (end - start).days > 730:
        raise HTTPException(422, 'Choose a date range of at most 731 days')
    return (start, end)

@router.get('/stats')
@router.get('/dashboard/summary')
async def summary(start: date | None=None, end: date | None=None, s=Depends(check)):
    a, b = range_dates(str(start) if start else None, str(end) if end else None)
    n = (b - a).days + 1

    async def count(table, x, y):
        return (await rows(f"SELECT COUNT(*) AS n FROM {table} WHERE archived=0 AND date(created_at,'+330 minutes') BETWEEN ? AND ?", (str(x), str(y))))[0]['n']
    reg = await count('registrations', a, b)
    previous = await count('registrations', a - timedelta(days=n), a - timedelta(days=1))
    trend = await rows("SELECT date(created_at,'+330 minutes') AS day,COUNT(*) AS count FROM registrations WHERE archived=0 AND date(created_at,'+330 minutes') BETWEEN ? AND ? GROUP BY day ORDER BY day", (str(a), str(b)))
    distribution = await rows("SELECT r.course_id,COALESCE(c.name,r.course_id) AS name,COUNT(*) AS count FROM registrations r LEFT JOIN courses c ON c.id=r.course_id WHERE r.archived=0 AND date(r.created_at,'+330 minutes') BETWEEN ? AND ? GROUP BY r.course_id ORDER BY count DESC", (str(a), str(b)))
    recent = await rows('SELECT r.*,COALESCE(c.name,r.course_id) AS course_name FROM registrations r LEFT JOIN courses c ON c.id=r.course_id WHERE r.archived=0 ORDER BY r.id DESC LIMIT 5')
    activities = await rows("SELECT actor,action,entity,entity_id,created_at FROM audit_logs WHERE date(created_at,'+330 minutes')=? ORDER BY id DESC LIMIT 8", (str(today()),))
    from ..core.content import IST
    return {'registrations': reg, 'enquiries': await count('enquiries', a, b), 'courses': len(await list_content('courses', True)), 'batches': sum((x.get('lifecycle') in ('current', 'upcoming') for x in await list_content('batches', True))), 'change': round((reg - previous) * 100 / previous, 1) if previous else None, 'trend': trend, 'distribution': distribution, 'recent': recent, 'activities': activities, 'today_registrations': await count('registrations', today(), today()), 'today_enquiries': await count('enquiries', today(), today()), 'start': str(a), 'end': str(b), 'updated_at': datetime.now(IST).isoformat()}
RECORDS = {'registrations', 'enquiries'}

def record_filters(kind, q='', status='', course='', batch='', start='', end='', archived=False, internship=''):
    conditions = ['r.archived=?']
    params = [int(archived)]
    if q:
        name = 'full_name' if kind == 'registrations' else 'name'
        conditions.append(f'(r.{name} LIKE ? OR r.mobile LIKE ? OR r.email LIKE ?)')
        params += ['%' + q + '%'] * 3
    if status:
        conditions.append('r.status=?')
        params.append(status)
    if kind == 'registrations':
        for column, value in [('course_id', course), ('preferred_batch', batch), ('internship_id', internship)]:
            if value:
                conditions.append(f'r.{column}=?')
                params.append(value)
    for operator, value in [('>=', start), ('<=', end)]:
        if value:
            try:
                date.fromisoformat(value)
            except ValueError:
                raise HTTPException(422, 'Invalid date filter')
            conditions.append(f"date(r.created_at,'+330 minutes'){operator}?")
            params.append(value)
    return (' AND '.join(conditions), params)

@router.get('/internship-applications')
async def applications(q: str='', s=Depends(check)):
    return {'items': await rows('SELECT r.*,COALESCE(i.name,r.internship_id) AS program_name FROM registrations r LEFT JOIN internships i ON i.id=r.internship_id WHERE r.internship_id IS NOT NULL AND r.archived=0 AND (r.full_name LIKE ? OR r.mobile LIKE ?) ORDER BY r.id DESC', ('%' + q + '%', '%' + q + '%'))}

@router.patch('/internship-applications/{identifier}')
async def edit_application(identifier: int, data: dict, s=Depends(check)):
    return await edit_record('registrations', str(identifier), data, s)

@router.get('/{kind}/export')
async def export_records(kind: str, q: str='', status: str='', course: str='', batch: str='', start: str='', end: str='', archived: bool=False, internship: str='', s=Depends(check)):
    if kind not in RECORDS:
        raise HTTPException(404, 'Not found')
    where, params = record_filters(kind, q, status, course, batch, start, end, archived, internship)
    items = await rows(f'SELECT r.* FROM {kind} r WHERE {where} ORDER BY r.id DESC', tuple(params))
    stream = io.StringIO()
    fields = list(items[0]) if items else ['id']
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for item in items:
        writer.writerow({k: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else v for k, v in item.items()})
    return Response(stream.getvalue(), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename="{kind}.csv"', 'Cache-Control': 'no-store'})

@router.get('/{kind}')
async def listing(kind: str, q: str='', status: str='', course: str='', batch: str='', branch: str='', start: str='', end: str='', archived: bool=False, internship: str='', page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100), s=Depends(check)):
    overview={}
    if kind in RECORDS:
        where, params = record_filters(kind, q, status, course, batch, start, end, archived, internship)
        total = (await rows(f'SELECT COUNT(*) AS n FROM {kind} r WHERE {where}', tuple(params)))[0]['n']
        select = 'r.*,COALESCE(c.name,r.course_id) AS course_name' if kind == 'registrations' else 'r.*'
        join = ' LEFT JOIN courses c ON c.id=r.course_id' if kind == 'registrations' else ''
        items = await rows(f'SELECT {select} FROM {kind} r{join} WHERE {where} ORDER BY r.id DESC LIMIT ? OFFSET ?', tuple(params + [page_size, (page - 1) * page_size]))
    else:
        all_items=await list_content(kind)
        overview={'total':len(all_items),**{key:sum(r['status']==key for r in all_items) for key in ('draft','published','archived','cancelled')},**{key:sum(r['status']=='published' and r.get('lifecycle')==key for r in all_items) for key in ('current','upcoming','completed')}}
        items = [r for r in all_items if (not q or q.lower() in (r['name'] + ' ' + r['id']).lower()) and (not status or status in (r['status'], r.get('lifecycle'))) and (not course or r.get('course_id') == course) and (not branch or r.get('branch') == branch)]
        total = len(items)
        items = items[(page - 1) * page_size:page * page_size]
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size,'overview':overview}

@router.get('/{kind}/{identifier}')
async def detail(kind: str, identifier: str, s=Depends(check)):
    if kind not in RECORDS:
        return await get_content(kind, identifier)
    found = await rows(f'SELECT * FROM {kind} WHERE id=?', (identifier,))
    if not found:
        raise HTTPException(404, 'Record not found')
    return found[0]

@router.post('/{kind}', status_code=201)
async def create(kind: str, data: dict, s=Depends(check)):
    extras={k:data[k] for k in ('status','admin_notes','follow_up_date') if k in data} if kind in RECORDS else {}
    if extras.get('status','New') not in STATUSES:raise HTTPException(422,'Invalid workflow status')
    if 'admin_notes' in extras and (not isinstance(extras['admin_notes'],str) or len(extras['admin_notes'])>10000):raise HTTPException(422,'Notes must be text of at most 10000 characters')
    if extras.get('follow_up_date'):
        try:date.fromisoformat(extras['follow_up_date'])
        except ValueError:raise HTTPException(422,'Invalid follow-up date')
    try:
        if kind == 'registrations':
            result = await register(RegistrationCreate.model_validate(data))
        elif kind == 'enquiries':
            result = await enquiry(EnquiryCreate.model_validate(data))
        else:
            result = await save_content(kind, data)
    except ValidationError as e:
        raise HTTPException(422, e.errors(include_context=False))
    if extras:
        await edit_record(kind,str(result['id']),extras,s)
    await audit(s['username'], 'created', kind, result['id'])
    return result

@router.patch('/registrations/{identifier}/status')
async def update_status(identifier: int, data: StatusUpdate, s=Depends(check)):
    return await edit_record('registrations', str(identifier), {'status': data.status}, s)

@router.patch('/{kind}/{identifier}')
async def edit_record(kind: str, identifier: str, data: dict, s=Depends(check)):
    current = await detail(kind, identifier, s)
    if kind not in RECORDS:
        clean = {k: v for k, v in current.items() if k in Content.model_fields}
        try:
            result = await save_content(kind, {**clean, **data}, identifier)
        except ValidationError as e:
            raise HTTPException(422, e.errors(include_context=False))
    else:
        allowed = {'status', 'admin_notes', 'archived', 'follow_up_date'} if kind == 'enquiries' else {'status', 'admin_notes', 'archived'}
        model = RegistrationCreate if kind == 'registrations' else EnquiryCreate
        fields = set(model.model_fields) | allowed
        if set(data) - fields:
            raise HTTPException(422, 'Unknown record fields')
        combined = {**current, 'consent': True, **data}
        try:
            validated = model.model_validate(combined).model_dump()
        except ValidationError as e:
            raise HTTPException(422, e.errors(include_context=False))
        if 'status' in data and data['status'] not in STATUSES:
            raise HTTPException(422, 'Invalid workflow status')
        if 'admin_notes' in data and (not isinstance(data['admin_notes'], str) or len(data['admin_notes']) > 10000):
            raise HTTPException(422, 'Notes must be text of at most 10000 characters')
        if 'follow_up_date' in data and data['follow_up_date']:
            try:
                date.fromisoformat(data['follow_up_date'])
            except ValueError:
                raise HTTPException(422, 'Invalid follow-up date')
        if kind == 'registrations' and any((k in data and data[k] != current.get(k) for k in ('course_id', 'batch_id', 'internship_id'))):
            from ..core.content import validate_selection
            await validate_selection(model.model_validate(combined))
        updates = {k: v for k, v in validated.items() if k in data}
        updates.update({k: data[k] for k in allowed if k in data})
        if updates:
            await execute(f'UPDATE {kind} SET ' + ','.join((k + '=?' for k in updates)) + ",updated_at=datetime('now') WHERE id=?", tuple(list(updates.values()) + [identifier]))
        result = await detail(kind, identifier, s)
    await audit(s['username'], 'updated', kind, identifier)
    return result

@router.delete('/{kind}/{identifier}')
async def archive(kind: str, identifier: str, s=Depends(check)):
    await detail(kind, identifier, s)
    if kind in RECORDS:
        await execute(f"UPDATE {kind} SET archived=1,updated_at=datetime('now') WHERE id=?", (identifier,))
    else:
        await get_content(kind, identifier)
        await execute(f"UPDATE {kind} SET status='archived',updated_at=datetime('now') WHERE id=?", (identifier,))
    await audit(s['username'], 'archived', kind, identifier)
    return {'ok': True}
