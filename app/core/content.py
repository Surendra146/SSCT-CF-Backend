import json
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from .db import rows, execute
from ..schemas.content import Content
TABLES = {'courses', 'batches', 'internships'}
IST = timezone(timedelta(hours=5, minutes=30))

def today():
    return datetime.now(IST).date()

def decode(row):
    data = json.loads(row.get('data') or '{}')
    data.update({k: v for k, v in row.items() if k != 'data'})
    if data.get('start_date'):
        now = today().isoformat()
        data['lifecycle'] = 'upcoming' if data['start_date'] > now else 'completed' if data.get('end_date') and data['end_date'] < now else 'current'
        data['accepting_applications'] = bool(data.get('applications_open', True) and data['status'] == 'published' and (data['lifecycle'] != 'completed') and (not data.get('closing_date') or data['closing_date'] >= now) and (data.get('available_seats') != 0))
    return data

async def get_content(kind, identifier, public=False):
    if kind not in TABLES:
        raise HTTPException(404, 'Unknown module')
    found = await rows(f'SELECT * FROM {kind} WHERE id=?', (identifier,))
    if not found or (public and found[0]['status'] != 'published'):
        raise HTTPException(404, 'Not found')
    return decode(found[0])

async def list_content(kind, public=False):
    if kind not in TABLES:
        raise HTTPException(404, 'Unknown module')
    return sorted([decode(r) for r in await rows(f'SELECT * FROM {kind}' + (" WHERE status='published'" if public else ''))], key=lambda r: (r.get('display_order', 0), r['name']))

async def save_content(kind, data, existing=None):
    if kind not in TABLES:
        raise HTTPException(404, 'Unknown module')
    value = Content.model_validate(data)
    if kind=='internships' and value.duration_value is not None:
        value.duration=f'{value.duration_value} {value.duration_unit}'
    record = value.model_dump(mode='json')
    if kind != 'courses':
        if value.course_id:
            await get_content('courses', value.course_id)
        if value.status == 'published':
            if not value.start_date or not value.duration or (not value.description):
                raise HTTPException(422, 'Published schedules require a start date, duration and description')
            if value.training_mode != 'Online' and (not value.branch):
                raise HTTPException(422, 'A branch is required for classroom or hybrid programs')
            if kind == 'batches' and (not value.course_id or not value.start_time or (not value.end_time) or (not value.schedule_days)):
                raise HTTPException(422, 'Published batches require a course, start/end times and schedule days')
    elif value.status == 'published' and (not value.description or not value.categories):
        raise HTTPException(422, 'Published courses require a description and category')
    if existing and value.id != existing:
        raise HTTPException(422, 'Stable IDs cannot be changed')
    if not existing and await rows(f'SELECT id FROM {kind} WHERE id=?', (value.id,)):
        raise HTTPException(409, 'This slug already exists')
    columns = ['id', 'name', 'status', 'data']
    params = [value.id, value.name, value.status, json.dumps(record)]
    if kind != 'courses':
        columns += ['course_id', 'start_date', 'end_date']
        params += [value.course_id, record['start_date'], record['end_date']]
    if existing:
        await execute(f'UPDATE {kind} SET ' + ','.join((f'{c}=?' for c in columns[1:])) + ",updated_at=datetime('now') WHERE id=?", tuple(params[1:] + [existing]))
    else:
        await execute(f"INSERT INTO {kind}({','.join(columns)}) VALUES({','.join(('?' for _ in columns))})", tuple(params))
    return await get_content(kind, value.id)

async def validate_selection(data):
    if data.course_id == 'data-science':
        data.course_id = 'data-science-ai'
    course = await get_content('courses', data.course_id, public=True)
    for kind, identifier in [('batches', data.batch_id), ('internships', data.internship_id)]:
        if identifier:
            item = await get_content(kind, identifier, public=True)
            if not item.get('accepting_applications'):
                raise HTTPException(409, 'Applications are closed for this program or batch')
            if item.get('course_id') and item['course_id'] != course['id']:
                raise HTTPException(422, 'Selected course does not match the program or batch')
            if kind == 'batches':
                data.preferred_batch = item['name']

async def audit(actor, action, entity, identifier):
    await execute('INSERT INTO audit_logs(actor,action,entity,entity_id) VALUES(?,?,?,?)', (actor, action, entity, str(identifier)))
