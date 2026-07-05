# superset-promote-dashboard

A Superset plugin that lets you swap all chart datasources in a dashboard from one database connection to another in one click — useful for promoting dashboards between environments (dev → staging → prod).

## How it works

1. Pick a dashboard and a target database connection
2. **Preview** — see which charts will be swapped, which have no match, and which are already on the target
3. **Promote** — each chart is updated to the matching dataset in the target DB, matched by table name

Charts are matched by `table_name` (and `schema` when set). Virtual datasets (SQL-based) are skipped.

## Installation

```bash
pip install superset-promote-dashboard
```

Register the plugin in your `superset_config.py`:

```python
def init_promote_plugin(app):
    try:
        from superset_promote_dashboard.promote_view import PromoteDashboardView
        import os, superset_promote_dashboard
        from jinja2 import ChoiceLoader, FileSystemLoader

        app.appbuilder.add_view(
            PromoteDashboardView,
            "Promote Dashboard",
            icon="fa-arrow-circle-up",
            category="Custom Tools",
            category_icon="fa-wrench",
        )

        sm = app.appbuilder.sm
        admin_role = sm.find_role("Admin")
        if admin_role:
            grants = [
                ("menu_access", "Promote Dashboard"),
                ("menu_access", "Custom Tools"),
                ("can_index",       "PromoteDashboardView"),
                ("can_api_preview", "PromoteDashboardView"),
                ("can_api_promote", "PromoteDashboardView"),
            ]
            for action, view_name in grants:
                pvm = sm.add_permission_view_menu(action, view_name)
                if pvm:
                    sm.add_permission_role(admin_role, pvm)

        pkg_templates = os.path.join(os.path.dirname(superset_promote_dashboard.__file__), "templates")
        if os.path.exists(pkg_templates):
            from jinja2 import ChoiceLoader, FileSystemLoader
            app.jinja_env.loader = ChoiceLoader([app.jinja_env.loader, FileSystemLoader(pkg_templates)])
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to register promote-dashboard plugin: {e}")

FLASK_APP_MUTATOR = init_promote_plugin
```

Restart Superset — **Custom Tools → Promote Dashboard** will appear in the navigation.

## Local development

Requires Docker.

```bash
docker compose up
```

This starts:
- **postgres** — one container serving three databases: `superset`, `db_source`, `db_target`
- **superset** — Apache Superset 4.1.1 with the plugin installed, at http://localhost:8088
- **superset-init** — one-shot container that runs migrations, creates the admin user, seeds database connections, datasets, and the "Academic Overview" demo dashboard

Login: `admin` / `admin`

### Demo data

The test environment uses a high-school theme to make the source vs. target difference obvious:

| Database | Contents |
|---|---|
| Source DB | 2023-2024 school year — 20 students, 50 grade records (Q1-Q4), 36 attendance records |
| Target DB | 2024-2025 cohort — 6 students, 15 grade records (Q1-Q3 in progress), 10 attendance records |

Tables in both databases: `students`, `grades`, `attendance`.

### Promoting the demo dashboard

1. Navigate to **Custom Tools → Promote Dashboard**
2. Select **Academic Overview** and **Target DB**
3. Click **Preview** — all 5 charts should show "Will swap"
4. Click **Promote** — charts are updated; reload the dashboard to see the new cohort's data
5. Run Preview again — all charts now show "Already on target"

## Security

- All routes are protected by `@has_access` — unauthenticated requests redirect to login
- CSRF is fully enabled; the plugin generates a CSRF token via `generate_csrf()` and forwards it in both the browser meta tag and all server-side `PUT` calls to the Superset API
- Admin role permissions are granted automatically on startup; other roles can be granted access through **Security → List Roles** in the Superset UI

## Requirements

- Apache Superset 4.x
- Python 3.10+
- `flask-wtf` (included with Superset)
