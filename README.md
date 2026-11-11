# SSCT FastAPI + Cloudflare D1 backend

The public website and private admin portal share one API and database. Run the backend here and the React frontend in `D:\Devlopment files\Project files\Frontend code\ssct-Frontend CF`.

## Local development

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

The root `.env` is loaded automatically, taking precedence over inherited environment variables. Use `.env.example` as a template. Existing administrator credentials bootstrap a **hashed** account in `admin_users` once. After initialization, change the name/password in `/admin/settings`; changing `.env` does not silently overwrite an established account's password. `ADMIN_PASSWORD_HASH` can supply a precomputed PBKDF2-SHA256 hash instead of a plaintext bootstrap password. Neither password nor session token is sent to frontend storage.

Visit `http://localhost:5173/admin/login`. `/admin` remains a compatible entry point. Keep frontend `VITE_API_URL=http://localhost:8000` and backend `FRONTEND_ORIGIN=http://localhost:5173` for local development. Use the same hostname consistently.

Startup applies missing versioned local migrations without deleting business records. It imports the existing 78-course catalog once using stable IDs. New batches/internships start empty until real schedules are entered by an admin.

## Admin API

- `POST /api/admin/auth/login`, `GET /api/admin/auth/me`, `POST /api/admin/auth/logout`. The original `/api/admin/login` URL remains an alias; its response now establishes an HttpOnly session rather than returning a bearer token.
- `GET /api/admin/dashboard/summary?start=YYYY-MM-DD&end=YYYY-MM-DD` returns actual counts, period comparison, daily trend, course distribution, recent registrations and today's activity. `/stats` remains an alias.
- `/api/admin/{registrations,enquiries,courses,batches,internships}` supports authenticated list/create, detail/update and archive operations. `DELETE` archives; it never physically deletes business records.
- Record lists support search, status/date/course/batch filters and pagination; `/registrations/export` and `/enquiries/export` export filtered CSV with formula-injection protection.
- `/api/admin/internship-applications` lists linked applications; PATCH on an application ID updates its registration record.
- `/api/admin/settings` reads settings and updates the administrator's profile/password.

Mutations require a session and `X-CSRF-Token`, obtained from login or `/auth/me`. Logout is idempotent and origin-checked even when a session has expired. All admin responses use `Cache-Control: no-store`. Old bearer tokens are no longer accepted.

Sessions expire after 15 minutes without authenticated activity (`ADMIN_IDLE_MINUTES`, configurable 1–60) or eight hours absolutely. The browser sends an activity-aware heartbeat and logs out when leaving admin routes. The server enforces expiry independently. Login attempts are rate limited per source address to five per fifteen minutes; trust the Cloudflare-supplied address only on Cloudflare using `TRUST_CLOUDFLARE_IP=true`.

## Dynamic public content

`GET /api/courses`, `/api/batches`, `/api/internships` and their detail URLs return published content only. Public APIs never return registration/enquiry lists. Course pages, registration choices, batches and internships fetch the backend; no rebuild is needed to publish edits. Responses use no-store and pages refetch on navigation/focus.

Schedule lifecycle uses Asia/Kolkata calendar dates: future start = upcoming, started and not ended = current, end before today = completed. With no end date a program remains current until explicitly closed/archived. Applications are rejected for unpublished, cancelled, completed, closed, deadline-passed, or zero-seat schedules. Batch/course and internship/course relationships are validated. Applications share the registrations table and retain their batch/internship IDs.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Backend tests use temporary databases. Browser workflow scripts under `tests/` use the isolated server `tests.browser_server:app` on port 8001 and a frontend preview on 5174 configured with `VITE_API_URL=http://localhost:8001`. `capture-local.mjs` uses local `.env` credentials privately to capture the real dashboard, then logs out. Test fixture credentials must never be used for a deployment.

## Cloudflare release preparation — not deployed

1. Replace the D1 database ID and Pages origin placeholders in `wrangler.jsonc`.
2. Install the Python Workers toolchain from `pyproject.toml` and validate with local pywrangler before any production action.
3. Back up D1, then apply missing migrations in numerical order. Do not reapply `0002` if its message column already exists. Local SQLite uses its own `schema_migrations` ledger; Cloudflare's migration ledger is separate. Existing D1 installations that applied SQL directly must baseline their migration history first.
4. Configure `ADMIN_USERNAME` and either `ADMIN_PASSWORD_HASH` or `ADMIN_PASSWORD` using Cloudflare secrets. Set `FRONTEND_ORIGIN` to the exact frontend origin. Do not commit `.env` or `.dev.vars`.
5. Prefer the included Pages Function `functions/api/[[path]].js` for a same-origin API bridge: set **server-side** Pages `API_ORIGIN` to the existing Worker HTTPS origin, and leave frontend `VITE_API_URL` / `VITE_API_BASE_URL` empty. This avoids depending on third-party cookies between Pages and workers.dev. No extra domain is required.
6. Verify cookie security, D1 migrations, Web Crypto compatibility/CPU use, bootstrap login, CSRF and a full public registration using local/staging Workers. No paid service has been added, but free-tier suitability requires runtime measurement.
7. Production deployment remains subject to the owner's explicit approval.

The Worker adapter uses `workers.asgi.entrypoint` and awaits D1 bindings. It has unit coverage with a binding double; actual Workers execution is not verified in this environment because the CLI and real D1 binding configuration are absent. See `docs/IMPLEMENTATION_REPORT.md` for test evidence, changed files, screenshots and release limitations.

## Production readiness review (10 November 2026)

New administrator hashes use salted PBKDF2-HMAC-SHA256 at 600,000 iterations. Python Workers use asynchronous Web Crypto; native Python uses the equivalent hashlib implementation. Existing scrypt hashes are retained and work only where scrypt is available. A Worker returns an explicit migration-required error for such hashes; an approved password reset is required before migrating an existing scrypt account. No existing account was reset by the review.

Use the frontend `scripts/prepare-cloudflare-backend.py` to create a clean release source package; it excludes native requirements.txt, local databases and secrets. The current Workers CLI rejects a root requirements.txt, and a raw Wrangler dry-run does not prove dependency packaging. Use the supported pywrangler workflow in the clean package. Production configuration is in `wrangler.production.jsonc`; its D1 UUID is intentionally unresolved until authenticated inventory.

The authoritative readiness report and exact command checklist are in the paired frontend project under `docs/production-readiness-report.md` and `docs/cloudflare-deployment-checklist.md`. Full ASGI Worker+D1 verification, authenticated Cloudflare inventory and Free CPU profiling remain release gates. No production deployment or live data modification was performed.
