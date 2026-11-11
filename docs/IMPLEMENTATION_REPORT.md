# SSCT website and admin implementation report

Date: 10 November 2026 (Asia/Kolkata).

## Outcome and scope

Implemented locally in the existing React frontend and FastAPI backend. The admin portal is now an independent application with its own login, header, sidebar, dashboard and management routes. The public site's purple theme and `/enroll` URLs are preserved. No production deployment, database reset, or physical deletion of business records was performed.

The frontend is at `D:\Devlopment files\Project files\Frontend code\ssct-Frontend CF`; the backend is this workspace. Previous frontend file versions are retained in `.work/frontend-backup` as a local recovery copy, excluded from source control.

## Audit findings and resulting changes

| Before | Implemented behavior |
|---|---|
| Admin rendered inside the public announcement/header/footer/chatbot | Dedicated `/admin/*` layout; none of those public components mount on admin pages |
| `/admin` basic dashboard | `/admin/login`, `/admin/dashboard`, `/admin/registrations`, `/admin/enquiries`, `/admin/courses`, `/admin/batches`, `/admin/internships`, `/admin/settings`; `/admin` remains compatible |
| Browser bearer token in sessionStorage; stateless logout | Opaque HttpOnly cookie; only a SHA-256 digest of its token is stored in the sessions table; server-side revocation and expiry |
| Plaintext environment password compared on every login | Environment secrets bootstrap an account once, stored with salted scrypt; subsequent password changes use Settings and revoke other sessions |
| Dashboard course count fixed at 8 | Published database count; all 78 existing website catalog records imported without changing stable IDs |
| Eight permitted registration course slugs | Registration validates against the actual published catalog, including newly created courses |
| Static batch/internship assistance cards without actual schedules | Published database records, current/upcoming lifecycle, real dates/times, availability and professional empty states |
| Registrations/enquiries only listed, first 100 | Dedicated searchable/filterable/paginated management, details, manual creation, edits, status, notes, archival and filtered CSV export |
| No database relationship for selected schedules | Registration stores `batch_id` / `internship_id`; backend validates course relationship and program availability |
| Enroll Now and mixed registration terms | Public registration actions use Register Now; existing `/enroll` URLs and internal CSS identifiers remain compatible |

## Dashboard and management

- Navy gradient sidebar, purple active navigation and decorative blue waves; independent white SSCT admin header, administrator profile dropdown, settings and logout.
- Responsive layout: four desktop statistic cards, two columns on mobile/tablet, mobile drawer and horizontally scrollable tables.
- Actual registration/enquiry counts by Today, Last 7 Days, This Month, Last Month or custom range. Percentage comparisons use the previous equivalent period and are omitted when its count is zero.
- Recharts area chart uses real registration dates and interactive tooltips. The course-distribution donut uses actual counts, names and percentages. Empty ranges show an empty state.
- Real recent registrations, full course names, database-backed activities and functional quick actions. No reference-image example metrics, fabricated notifications or unsupported Students/Reports modules were added.
- Courses: full descriptions, category IDs, skills, modules, image/logo references, duration, eligibility, modes, featured flag, publication and ordering.
- Batches: related course, code, dates/times, days, training mode/branch, duration, trainer, seats/capacity, fees, deadline, instructions and publication.
- Internships: course relationship, skills required/learned, technologies, projects, eligibility, outcomes, duration value/unit, dates, mode/branch/timing, seats, fees, mentor, certificate, instructions, publication and application closure.
- Internship applications use the registrations table and are visible within the internship module, with a link to manage the full registration.
- Existing workflow statuses remain `New`, `Contacted`, `In Process`, `Enrolled`, `Closed`. No incompatible status rename or physical-delete action was introduced.

## Security and lifecycle decisions

- Every admin data/CRUD endpoint independently checks the database session and administrator role. Frontend route protection is additional.
- SameSite=Lax cookies on local HTTP; Secure, HttpOnly, SameSite=None on HTTPS. Mutations require the session-specific CSRF token and a trusted Origin. Logout is idempotent and Origin-checked.
- Session idle limit defaults to 15 minutes, configured by `ADMIN_IDLE_MINUTES`; absolute expiry is eight hours. Activity-aware browser heartbeats keep an actively used workspace alive. Backend expiry is independent of browser timers.
- Leaving admin for a public route clears the local auth state and calls backend logout. Navigating between admin modules preserves the session. Browser regression tests verify protected re-entry.
- Authentication state and CSRF token remain in memory. The former sessionStorage bearer token is removed. No credentials enter frontend files or browser persistent storage.
- Login limiting is persisted in the database: five attempts per source address per fifteen minutes. Cloudflare address trust is explicitly configured.
- Admin API responses and admin hosting paths use no-store; admin pages are marked noindex/nofollow. CSV values that could be spreadsheet formulas are escaped.
- DELETE archives records and preserves historical relationships. Applications to draft/unpublished, archived, cancelled, completed, closed, deadline-passed or zero-seat schedules are rejected.
- Asia/Kolkata controls schedule lifecycle and reporting dates. A schedule without an end date remains current after its start until explicitly closed/archived.
- An optional same-origin Cloudflare Pages API bridge avoids dependence on third-party cookies and does not require an additional domain.

## Data preservation and migrations

`0002_registration_message.sql` is retained. New migrations:

1. `0003_admin_management.sql`: administrator users, hashed sessions, login attempts, courses, batches, internships, audit records and new registration/enquiry relationship/management columns and indexes.
2. `0004_existing_catalog.sql`: imports the original 78-course catalog using INSERT OR IGNORE and stable IDs.

Local SQLite applies missing migrations automatically and records their filenames. Existing student records are preserved. Tests cover upgrading a database containing a historical registration and running startup migrations repeatedly. Real local dashboard screenshots show the original registration remains and the catalog contains 78 courses.

No example batches, internship programs or test student records were inserted into the real database. Browser write tests use `.work/portal-browser-test.sqlite3` on an isolated server. They are not production content.

## Validation evidence

| Check | Result |
|---|---|
| Backend unittest suite | 11 passed: auth/authorization, CSRF, rate limit, session expiry/revocation, password update, catalog visibility, CRUD, schedule/application rules, CSV, reporting, legacy upgrades and D1 binding adapter |
| Frontend Playwright suite | 18 passed: public routes, responsive widths, catalog/filter/search, registration, enquiries, program details/prefill, protected admin entry, admin-to-public logout and technology assets |
| Full isolated browser write workflows | Passed: login, create/publish course, batch and internship, public batch registration, public internship application, admin status/notes update, application visibility, logout/re-entry and mobile navigation |
| Production frontend build | Passed; no TypeScript or lint script exists in the existing project |
| Browser runtime errors in tested workflows | None |
| Real local dashboard screenshots | Captured at desktop, tablet and mobile widths, followed by logout |
| Actual Cloudflare Workers / remote D1 execution | Not verified; release blockers below |

The regression suite was updated for the requested new behavior: it no longer expects placeholder schedules or browser bearer tokens. It also caught and verified fixes for selected-batch prefill timing and dialog focus restoration.

Screenshots in `artifacts/admin-redesign`:

- `dashboard-desktop.png`, `dashboard-tablet.png`, `dashboard-mobile.png`: real local database.
- `login-mobile.png`: independent login screen.
- Files with `test` in the name, and `dashboard-with-test-records.png`, are isolated QA fixtures only.

## Deployment readiness and remaining limits

**Locally implemented and tested; not production-released or certified for Workers.**

1. `wrangler.jsonc` still contains the existing D1 ID and Pages-domain placeholders. Actual credentials, configured binding and Python Workers CLI were not available for a local/staging Workers integration run.
2. Apply only missing D1 migrations after backup and migration-history inspection. Unlike local SQLite, remote D1 migrations are a release operation and were not applied. Do not blindly replay ALTER TABLE migrations on an installation that applied them manually.
3. The Worker adapter now uses the documented ASGI entrypoint and awaits D1 operations, with a binding-double test. Validate real JS/Python conversions, packaged dependencies, scrypt availability and password-hashing CPU cost against the intended Cloudflare plan before release. A local CPython test does not prove Worker runtime compatibility.
4. Configure the exact HTTPS frontend Origin, Cloudflare secrets and Secure cookies. Prefer the included Pages Function bridge with server-side `API_ORIGIN` and empty frontend API URL variables to avoid cross-site cookie restrictions.
5. Existing environment credentials initialize an account only once; after migration the account's password is managed in Settings. `.env` changes do not overwrite an existing hashed account.
6. External website navigation/browser termination cannot reliably call logout. Server idle/absolute expiry provides the fallback, as required. If an exit request cannot reach the server, revocation completes when connectivity returns or the server timeout expires.
7. Public pages fetch updates on navigation, focus or refresh; no WebSockets or paid live-update service was added. In-place pages are not continuously subscribed.
8. No new hosting service, domain or paid dependency was introduced. Free-tier suitability depends on the existing account quotas and Worker runtime measurement.
9. The sitemap generator still needs a verified `VITE_SITE_URL`; the build reports that sitemap generation was skipped when it is unset.

The implementation does not claim production readiness until the actual Cloudflare integration and release configuration have been validated. No deployment was attempted.

## Sources consulted for runtime integration

- [Cloudflare Python Workers with FastAPI](https://developers.cloudflare.com/workers/languages/python/packages/fastapi/)
- [Query D1 from Python Workers](https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers/)
- [Recharts AreaChart API](https://recharts.github.io/en-US/api/AreaChart/)

## Changed files

The generated `docs/CHANGED_FILES.md` lists the backend implementation, frontend files, migrations, tests, configuration and screenshots. Current prepared frontend files and recovery copies live in `.work`, which is excluded from source control. No `.env` values are included in this report.
