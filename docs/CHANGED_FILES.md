# Changed files

Backend root: this workspace. Frontend root: `D:\Devlopment files\Project files\Frontend code\ssct-Frontend CF`.

## Backend, tests and documentation

- `.gitignore`
- `.env.example`
- `.dev.vars.example`
- `README.md`
- `requirements-dev.txt`
- `pyproject.toml`
- `wrangler.jsonc`
- `app/main.py`
- `app/entry.py`
- `app/core/auth.py`
- `app/core/db.py`
- `app/core/content.py`
- `app/core/middleware.py`
- `app/routers/admin.py`
- `app/routers/register.py`
- `app/routers/catalog.py`
- `app/schemas/register.py`
- `app/schemas/content.py`
- `app/catalog_seed.json`
- `migrations/0003_admin_management.sql`
- `migrations/0004_existing_catalog.sql`
- `tests/test_portal.py`
- `tests/test_d1_adapter.py`
- `tests/browser_server.py`
- `tests/browser-portal.mjs`
- `tests/browser-programs.mjs`
- `tests/capture-local.mjs`
- `tests/format-prepared.mjs`
- `docs/IMPLEMENTATION_REPORT.md`
- `docs/CHANGED_FILES.md`

## Frontend

- `functions/api/[[path]].js`
- `package-lock.json`
- `package.json`
- `playwright.config.js`
- `public/_headers`
- `src/admin/AdminApp.jsx`
- `src/admin/Auth.jsx`
- `src/admin/Dashboard.jsx`
- `src/admin/Management.jsx`
- `src/admin/Settings.jsx`
- `src/admin/admin.css`
- `src/admin/api.js`
- `src/components/CourseCard.jsx`
- `src/components/EnquiryForm.jsx`
- `src/components/Footer.jsx`
- `src/components/HomeCourseHighlights.jsx`
- `src/components/Navbar.jsx`
- `src/components/Programs.css`
- `src/components/Programs.jsx`
- `src/components/common/TechnologyLogo.jsx`
- `src/data/chatbot.js`
- `src/main.jsx`
- `src/pages/InfoPages.jsx`
- `src/pages/admin/Admin.jsx`
- `src/pages/batches/Batches.jsx`
- `src/pages/courses/CourseDetails.jsx`
- `src/pages/courses/Courses.jsx`
- `src/pages/enroll/Enroll.jsx`
- `src/pages/home/Home.jsx`
- `src/pages/internship/Internship.jsx`
- `src/services/Catalog.jsx`
- `src/services/api.js`
- `tests/premium.spec.js`
- `tests/redesign.spec.js`
- `tests/reference-pages.spec.js`
- `tests/site.spec.js`
- `tests/technology-logos.spec.js`

## Generated screenshots

- `artifacts/admin-redesign/batches-empty-mobile.png`
- `artifacts/admin-redesign/dashboard-desktop-test.png`
- `artifacts/admin-redesign/dashboard-desktop.png`
- `artifacts/admin-redesign/dashboard-mobile-test.png`
- `artifacts/admin-redesign/dashboard-mobile.png`
- `artifacts/admin-redesign/dashboard-tablet-test.png`
- `artifacts/admin-redesign/dashboard-tablet.png`
- `artifacts/admin-redesign/dashboard-with-test-records.png`
- `artifacts/admin-redesign/login-mobile.png`

Build output was regenerated in the existing frontend `dist/` directory. Existing student database records and `.env` contents were preserved. The migrations add tables/columns and seed the existing catalog; they do not reset the database. Recovery and QA files in `.work` are ignored and must not be deployed.
