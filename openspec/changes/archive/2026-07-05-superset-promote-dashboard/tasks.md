## 1. Project Scaffolding

- [x] 1.1 Create Python package directory `superset_promote_dashboard/` with `__init__.py`
- [x] 1.2 Create `pyproject.toml` with package metadata, dependencies (`flask`, `flask-appbuilder`), and entry points
- [x] 1.3 Create top-level directory structure: `superset/`, `postgres/`, `superset_promote_dashboard/templates/`

## 2. Docker & Test Environment

- [x] 2.1 Write `postgres/init.sql` — creates `db_source` and `db_target` databases, `students`, `grades`, `attendance` tables in both, and seeds `db_source` with ~50 grade records across 4 quarters (2023-2024 school year) and `db_target` with ~15 records (2024-2025 cohort)
- [x] 2.2 Write `superset/Dockerfile` — based on `apache/superset:4.1.1`, installs `psycopg2-binary` and the local plugin package
- [x] 2.3 Write `superset/superset_config.py` — sets `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, and `FLASK_APP_MUTATOR` to register the promote view and grant Admin role all required permissions
- [x] 2.4 Write `superset/import_connections.py` — init script that authenticates to Superset API, creates "Source DB" and "Target DB" connections, creates datasets for all tables in both DBs, and creates an "Academic Overview" sample dashboard with 5 charts (scores by subject/quarter, attendance, student count)
- [x] 2.5 Write `docker-compose.yaml` with services: `postgres` (one container serving `superset`, `db_source`, `db_target`), `superset`, and `superset-init` (runs `import_connections.py` then exits)

## 3. Plugin — Backend

- [x] 3.1 Create `superset_promote_dashboard/promote_view.py` — Flask-AppBuilder `BaseView` subclass with route `/promote_dashboard/`, all routes protected by `@has_access`
- [x] 3.2 Implement `GET /promote_dashboard/` — renders the main template; passes dashboard list, database list, and a generated CSRF token fetched from Superset API
- [x] 3.3 Implement `POST /promote_dashboard/api/preview` — accepts `dashboard_id` and `target_db_id`, returns JSON array of `{chart_name, current_dataset, matched_dataset, status}` for each chart; status is `already_current` when chart is already on the target DB
- [x] 3.4 Implement `POST /promote_dashboard/api/promote` — accepts `dashboard_id` and `target_db_id`, executes the swap for all `will_swap` charts via `PUT /api/v1/chart/{id}`, skips `already_current` charts, returns per-chart result JSON
- [x] 3.5 Extract Superset API helper functions into `superset_promote_dashboard/superset_api.py` — `get_dashboards()`, `get_dashboard_charts(dashboard_id)`, `get_datasets(db_id)`, `update_chart_datasource(chart_id, dataset_id)`
- [x] 3.6 Implement dataset matching logic in `superset_api.py` — match by `table_name` + `schema` (when non-empty), handle virtual datasets
- [x] 3.7 Forward CSRF token in all server-side API calls — `_auth_headers()` calls `generate_csrf()` and includes `X-CSRFToken` so outbound `PUT /api/v1/chart/{id}` requests are not rejected by Superset's CSRF middleware

## 4. Plugin — Frontend

- [x] 4.1 Create `superset_promote_dashboard/templates/promote_dashboard.html` — Jinja2 template with Superset's base layout, two dropdowns (dashboard, target database), "Preview" button, preview results table, "Promote" button (hidden until preview runs)
- [x] 4.2 Implement vanilla JS for "Preview" — `fetch POST /promote_dashboard/api/preview`, render results table with status badges (Will swap / Already on target / No match / Virtual dataset); use `display: block` to show the results section (not `''` which leaves a CSS `display: none` rule in effect)
- [x] 4.3 Implement vanilla JS for "Promote" — `fetch POST /promote_dashboard/api/promote`, replace table rows with final status (Promoted / Skipped / Failed), disable buttons after run
- [x] 4.4 CSRF token sourced from `<meta name="csrf-token">` populated by `generate_csrf()` in the view, included as `X-CSRFToken` header in all fetch POSTs; inline script uses `baselib.get_nonce()` to satisfy Superset's CSP nonce requirement

## 5. Plugin Registration

- [x] 5.1 Register `PromoteDashboardView` via `FLASK_APP_MUTATOR`; grant Admin role all five required permissions at startup: `menu_access` on "Promote Dashboard" and "Custom Tools", `can_index` / `can_api_preview` / `can_api_promote` on `PromoteDashboardView`
- [x] 5.2 Add plugin templates to Jinja2 search path via `ChoiceLoader` + `FileSystemLoader` so `promote_dashboard.html` is found when the package is installed

## 6. Security

- [x] 6.1 All routes protected by `@has_access` — unauthenticated requests redirect to `/login/`
- [x] 6.2 CSRF enabled (no `WTF_CSRF_ENABLED = False` override) — browser POSTs include token from meta tag; server-side `PUT` calls include token via `generate_csrf()`
- [x] 6.3 Admin role permissions auto-granted on startup so no manual Superset UI setup is required after install

## 7. Validation & Smoke Test

- [x] 7.1 Run `docker compose up` and confirm all containers reach healthy state
- [x] 7.2 Log into Superset as admin, navigate to "Academic Overview" dashboard, verify charts show `db_source` data (2023-2024 school year)
- [x] 7.3 Navigate to Custom Tools → Promote Dashboard, select "Academic Overview" and "Target DB", run preview — confirm charts show "Will swap"
- [x] 7.4 Click "Promote", confirm charts show "Promoted", reload dashboard — verify charts reflect `db_target` data (2024-2025 cohort, different numbers)
- [x] 7.5 Run promotion again (idempotency) — charts show "Already on target", Promote button hidden
