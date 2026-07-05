## Context

Apache Superset stores chart–datasource relationships via `datasource_id` on each chart (slice). When a team maintains multiple database environments (e.g. `db_source` for staging, `db_target` for production), promoting a dashboard means finding the equivalent dataset in the target database and re-pointing every chart. Currently this requires updating each chart manually in the Superset UI or via ad-hoc API calls.

This plugin is modelled after the `superset-mcp-plugins` reference project: a pure Flask-AppBuilder extension registered via `FLASK_APP_MUTATOR`, with no changes to Superset core.

The test environment uses a single PostgreSQL container (`postgres:15`) running three databases created at init time: `superset` (Superset metadata), `db_source` (source data), and `db_target` (target data). This keeps the Docker stack minimal while still exercising cross-database promotion.

## Goals / Non-Goals

**Goals:**
- Install as a pip package alongside Superset with zero core modifications
- Provide a single-page UI for selecting a dashboard, target database, previewing the swap, and executing it
- Match charts to datasets by `table_name` (and optionally `schema`); report unmatched charts as skipped
- Seed `db_source` and `db_target` with identical schemas but visually different mock data so the swap is immediately verifiable
- Auto-register `db_source` and `db_target` as Superset database connections on first boot via an init container

**Non-Goals:**
- Handling virtual datasets (SQL-based, not table-backed)
- Migrating chart-level custom SQL or calculated columns
- Multi-tenant or permission-scoped promotion (admin-only for now)
- Undo / rollback of a swap (left to future work)

## Decisions

### 1. Plugin registration via `FLASK_APP_MUTATOR`

**Decision**: Register the custom `BaseView` subclass using `FLASK_APP_MUTATOR` in `superset_config.py`.

**Rationale**: This is Superset's officially supported hook for additive extensions and is exactly how the reference plugin registers its chat view. Alternatives (monkey-patching, custom blueprints before app init) are fragile across Superset versions.

### 2. All Superset API calls from the Python backend, not the browser

**Decision**: The plugin's `/api/preview` and `/api/promote` endpoints call the Superset REST API server-side using the current user's session cookie, not from JavaScript in the browser.

**Rationale**: Avoids CORS issues and keeps auth handling in one place. The view can reuse Flask's `g.user` and forward cookies/CSRF tokens internally. Client JS only talks to the plugin's own endpoints.

**Alternative considered**: Direct browser→Superset API calls (simpler JS) — rejected because it requires exposing CSRF tokens to client code and breaks when Superset is behind a proxy.

### 3. Dataset matching by `table_name` (+ `schema` when set)

**Decision**: Match source dataset to target dataset using `table_name`. If source dataset has a non-empty `schema`, also match on `schema`.

**Rationale**: This is the most natural identity key — the table is the same logical entity across environments. UUID and `id` differ per environment; display names can be customised.

**Alternative considered**: Match by dataset display name — rejected because display names are user-editable and often differ between environments.

### 4. Single PostgreSQL container, three databases

**Decision**: One `postgres:15` container runs `superset`, `db_source`, and `db_target` databases, all created by an init SQL script.

**Rationale**: Reduces Docker complexity (one healthcheck, one volume, one set of credentials). The databases are logically isolated at the Postgres schema level; Superset sees them as separate datasource connections via different `dbname` values in the connection URI.

**Alternative considered**: Three separate `postgres` containers — rejected as unnecessarily heavy for a dev/test environment.

### 5. Vanilla JS + Jinja2 template (no frontend build step)

**Decision**: The UI is a single Jinja2 HTML template with vanilla JS, following the reference plugin pattern.

**Rationale**: Keeps the plugin self-contained with no Node.js toolchain requirement. The UI is simple enough (two selects, a preview table, a button) that a build step would be pure overhead.

## Risks / Trade-offs

- **Virtual datasets not supported** → Promotion will skip any chart backed by a SQL dataset. The preview UI will label these clearly so the user knows before executing.
- **`db_source`/`db_target` share the same Postgres host in dev** → In real use the two connections point to different hosts; the plugin code is host-agnostic and uses only `database_id`, so this is not a code limitation.
- **Admin-only scope** → The plugin uses `@has_access` but does not enforce row-level or database-level permissions. Any Superset admin can promote any dashboard to any database. Fine for the current use case; RBAC can be layered on later.
- **Chart update is not atomic** → If the loop fails halfway (network error, missing dataset), some charts are updated and others are not. Mitigation: the preview step shows the full plan before execution, and partial results are reported per-chart in the response so the user can re-run safely (already-promoted charts match the new dataset and are a no-op on re-run).

## Open Questions

- Should the UI also auto-create missing datasets in the target database when no match is found? (Deferred — current spec says skip and report.)
- Should promotion be logged to Superset's audit log? (Nice-to-have, not in scope for v1.)
