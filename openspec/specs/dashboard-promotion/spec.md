# dashboard-promotion Specification

## Purpose
TBD - created by archiving change superset-promote-dashboard. Update Purpose after archive.
## Requirements
### Requirement: Plugin registers without modifying Superset core
The plugin SHALL register its Flask-AppBuilder view via the `FLASK_APP_MUTATOR` hook in `superset_config.py`. No Superset source files SHALL be modified.

#### Scenario: Plugin view is accessible after Superset start
- **WHEN** Superset starts with the plugin installed and `FLASK_APP_MUTATOR` configured
- **THEN** the route `/promote_dashboard/` returns HTTP 200 for authenticated admin users

---

### Requirement: Dashboard list is populated from Superset API
The UI SHALL display a dropdown listing all dashboards available in the Superset instance, fetched via `GET /api/v1/dashboard/`.

#### Scenario: Dashboards load on page open
- **WHEN** an admin navigates to `/promote_dashboard/`
- **THEN** the dashboard dropdown is populated with all dashboard titles from the Superset API

---

### Requirement: Target database list is populated from Superset API
The UI SHALL display a dropdown listing all registered database connections, fetched via `GET /api/v1/database/`.

#### Scenario: Databases load on page open
- **WHEN** an admin navigates to `/promote_dashboard/`
- **THEN** the target database dropdown is populated with all database connection names from the Superset API

---

### Requirement: Preview shows per-chart swap plan before execution
When the user selects a dashboard and a target database and clicks "Preview", the plugin SHALL return a table showing each chart name, its current dataset, the target dataset name, and the planned action for each chart.

#### Scenario: All charts have matching datasets in target
- **WHEN** the user selects a dashboard where every chart's `table_name` exists as a dataset in the target database and clicks "Preview"
- **THEN** the preview table shows each chart with a "Will swap" status and the target dataset name

#### Scenario: Some charts have no matching dataset in target
- **WHEN** the user selects a dashboard where one or more charts have no dataset with a matching `table_name` in the target database and clicks "Preview"
- **THEN** those charts are listed with status "Will create" (a new dataset will be created in the target DB on promote) and the Promote button is still enabled

#### Scenario: Chart backed by virtual (SQL) dataset
- **WHEN** a chart in the selected dashboard is backed by a virtual (SQL-defined) dataset rather than a physical table
- **THEN** the preview lists that chart with status "Virtual dataset — will skip"

#### Scenario: Chart's source dataset cannot be resolved
- **WHEN** the source dataset ID cannot be fetched (e.g. deleted dataset) and no `table_name` is determinable
- **THEN** the preview lists that chart with status "No match" and it is skipped on promote

---

### Requirement: Promotion syncs columns and updates chart datasource_id via Superset API
When the user confirms execution, for each chart the plugin SHALL:
1. If the target dataset already exists (`will_swap`): sync its columns via `PUT /api/v1/dataset/{id}/refresh`, then update the chart via `PUT /api/v1/chart/{id}`.
2. If the target dataset does not exist (`will_create`): create it via `POST /api/v1/dataset/`, sync columns, then update the chart.

The plugin SHALL NOT modify the source dataset's `database_id` — it only creates new datasets or updates chart pointers.

#### Scenario: Successful promotion of all matched charts
- **WHEN** the user clicks "Promote" after previewing a plan with matched charts
- **THEN** each matched chart has its target dataset columns synced, the chart is re-pointed to the target dataset, and the result view shows "Promoted"

#### Scenario: Charts with no existing target dataset are created and promoted
- **WHEN** the user clicks "Promote" and some charts show "Will create" in the preview
- **THEN** a new dataset is created in the target database for each such chart, columns are synced, the chart is re-pointed, and the result view shows "Created" for those charts

#### Scenario: Partial promotion when some charts cannot be resolved
- **WHEN** the user clicks "Promote" and some charts have unresolvable source datasets (no table_name)
- **THEN** those charts are reported as their preview status (virtual, no_match) in the result view without raising an error

#### Scenario: API error on a single chart does not abort the entire promotion
- **WHEN** the Superset API returns an error for one chart during promotion
- **THEN** the plugin logs the error, marks that chart as "Failed" in the result, and continues updating the remaining charts

---

### Requirement: Dataset matching uses table_name (and schema when set)
The plugin SHALL match source dataset to target dataset by comparing `table_name`. When the source dataset's `schema` field is non-empty, the match SHALL also require `schema` equality.

#### Scenario: Match found by table_name only
- **WHEN** source dataset has `table_name = "orders"` and `schema = ""` and the target database has a dataset with `table_name = "orders"`
- **THEN** that target dataset is selected as the match

#### Scenario: Match requires schema when source schema is set
- **WHEN** source dataset has `table_name = "orders"` and `schema = "public"` and target has two datasets: one with `schema = "public"` and one with `schema = "archive"`
- **THEN** only the `schema = "public"` dataset is selected as the match

---

### Requirement: Plugin UI is accessible only to authenticated users
The plugin view and its API sub-routes SHALL be protected by Superset's `@has_access` decorator. Unauthenticated requests SHALL be redirected to the Superset login page.

#### Scenario: Unauthenticated access is rejected
- **WHEN** an unauthenticated user requests `/promote_dashboard/`
- **THEN** the response redirects to the Superset login page (HTTP 302)

