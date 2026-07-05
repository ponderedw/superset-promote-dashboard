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
When the user selects a dashboard and a target database and clicks "Preview", the plugin SHALL return a table showing each chart name, its current dataset, and the matched dataset in the target database (or "No match — will skip" if none found).

#### Scenario: All charts have matching datasets in target
- **WHEN** the user selects a dashboard where every chart's `table_name` exists as a dataset in the target database and clicks "Preview"
- **THEN** the preview table shows each chart with a "Will swap" status and the target dataset name

#### Scenario: Some charts have no matching dataset in target
- **WHEN** the user selects a dashboard where one or more charts have no dataset with a matching `table_name` in the target database and clicks "Preview"
- **THEN** those charts are listed with status "No match — will skip" and the execution button is still enabled

#### Scenario: Chart backed by virtual (SQL) dataset
- **WHEN** a chart in the selected dashboard is backed by a virtual (SQL-defined) dataset rather than a physical table
- **THEN** the preview lists that chart with status "Virtual dataset — will skip"

---

### Requirement: Promotion updates chart datasource_id via Superset API
When the user confirms execution, the plugin SHALL call `PUT /api/v1/chart/{id}` for each chart that has a match, setting `datasource_id` to the matched target dataset's id and `datasource_type` to `table`.

#### Scenario: Successful promotion of all matched charts
- **WHEN** the user clicks "Promote" after previewing a plan with matched charts
- **THEN** each matched chart is updated via the Superset API, and the result view shows "Promoted" for each updated chart

#### Scenario: Partial promotion when some charts have no match
- **WHEN** the user clicks "Promote" and some charts have no matching dataset in the target database
- **THEN** matched charts are updated and skipped charts are reported as "Skipped" in the result view, without raising an error

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

