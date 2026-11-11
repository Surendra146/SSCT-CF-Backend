CREATE TABLE IF NOT EXISTS registrations (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 full_name TEXT NOT NULL,mobile TEXT NOT NULL,email TEXT NOT NULL,city TEXT NOT NULL,
 qualification TEXT NOT NULL,course_id TEXT NOT NULL,preferred_batch TEXT NOT NULL,
 training_mode TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'New',
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_registrations_created ON registrations(created_at);
CREATE TABLE IF NOT EXISTS enquiries (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,mobile TEXT NOT NULL,email TEXT NOT NULL DEFAULT '',message TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
