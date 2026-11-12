import os
from contextlib import closing
from pathlib import Path
from contextvars import ContextVar
from typing import Any

worker_env: ContextVar[Any | None] = ContextVar('worker_env', default=None)
LOCAL_DB = os.environ.get('SSCT_DB_PATH', 'ssct_local.sqlite3')


def local_conn():
    import sqlite3
    conn = sqlite3.connect(LOCAL_DB)
    conn.execute('PRAGMA foreign_keys=ON')
    conn.row_factory = sqlite3.Row
    return conn


async def rows(sql, params=()):
    env = worker_env.get()
    if env is not None:
        db: Any = env.DB
        stmt: Any = db.prepare(sql)
        if params:
            stmt = stmt.bind(*(int(x) if isinstance(x, bool) else x for x in params))
        result = await stmt.all()
        return result['results']
    with closing(local_conn()) as c:
        return [dict(x) for x in c.execute(sql, params).fetchall()]


async def execute(sql, params=()):
    env = worker_env.get()
    if env is not None:
        db: Any = env.DB
        stmt: Any = db.prepare(sql)
        if params:
            stmt = stmt.bind(*(int(x) if isinstance(x, bool) else x for x in params))
        result = await stmt.run()
        return result['meta'].get('last_row_id')
    with closing(local_conn()) as c:
        cursor = c.execute(sql, params)
        c.commit()
        return cursor.lastrowid

def init_local():
    if worker_env.get() is not None:return
    sql=(Path(__file__).resolve().parents[2]/'migrations'/'0001_init.sql').read_text()
    with closing(local_conn()) as c:
        c.executescript(sql)
        if 'message' not in {row['name'] for row in c.execute('PRAGMA table_info(registrations)')}:
            migration=Path(__file__).resolve().parents[2]/'migrations'/'0002_registration_message.sql'
            c.executescript(migration.read_text())
        c.execute('CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)')
        c.commit()
        for migration in sorted((Path(__file__).resolve().parents[2]/'migrations').glob('*.sql')):
            if migration.name[:4] < '0003':continue
            if not c.execute('SELECT 1 FROM schema_migrations WHERE name=?',(migration.name,)).fetchone():
                script=migration.read_text(encoding='utf-8')
                c.executescript("BEGIN;\n"+script+"\nINSERT INTO schema_migrations(name) VALUES('"+migration.name+"');\nCOMMIT;")
