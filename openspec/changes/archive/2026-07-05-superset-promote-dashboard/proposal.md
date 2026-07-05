## Why

Data teams managing multiple environments (dev/staging/prod) in Apache Superset must manually update each chart's datasource one by one when promoting a dashboard — a tedious, error-prone process that blocks fast iteration. This plugin automates that workflow by swapping all chart connections in a dashboard to a target database in a single operation.

## What Changes

- **New Python package** `superset-promote-dashboard` installable as a Superset plugin via pip
- **New Superset plugin view** registered via `FLASK_APP_MUTATOR`, adding a `/promote_dashboard` UI route
- **Dashboard promotion UI** — pick a source dashboard, pick a target database connection, preview the swap plan, then execute
- **Swap logic** — for each chart in the dashboard, find a dataset with the same `table_name` in the target database and update the chart's `datasource_id` to point to it; missing datasets are reported as skipped
- **Docker test environment** — single PostgreSQL cluster hosting 3 databases (`superset`, `db_source`, `db_target`) with identical schemas but different mock data rows, plus auto-initialization of Superset database connections, datasets, and a sample dashboard

## Capabilities

### New Capabilities

- `dashboard-promotion`: UI and backend logic for swapping all chart datasources in a Superset dashboard to a target database connection in one click
- `test-environment`: Docker-compose stack with Superset + one PostgreSQL instance running three databases (`superset`, `db_source`, `db_target`), pre-seeded with mock data and wired connections

### Modified Capabilities

<!-- none — this is a net-new project -->

## Impact

- **New package**: `superset_promote_dashboard/` Python package with Flask-AppBuilder view and Jinja2 template
- **Superset config**: `FLASK_APP_MUTATOR` hook to register the plugin view
- **Superset REST API**: reads dashboards, charts, datasets, databases; writes chart `datasource_id`
- **Docker**: `docker-compose.yaml` with services: `superset`, `postgres` (one container, 3 DBs), `superset-init`
- **Mock data**: `db_source` seeded with "production-like" rows; `db_target` seeded with identical schema but different (e.g. smaller/newer) rows to make the swap visually verifiable
- **No changes** to Superset core — plugin is purely additive via the supported extension hook
