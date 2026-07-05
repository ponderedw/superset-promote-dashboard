import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "thisISaSECRET_1234")

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_DB_URI",
    "postgresql+psycopg2://superset:superset@postgres:5432/superset",
)

SUPERSET_LOAD_EXAMPLES = False


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

        # Grant Admin role every permission the plugin creates so it is
        # immediately usable and shows in the nav without manual setup.
        sm = app.appbuilder.sm
        admin_role = sm.find_role("Admin")
        if admin_role:
            grants = [
                # menu visibility
                ("menu_access", "Promote Dashboard"),
                ("menu_access", "Custom Tools"),
                # view-level access (required by @has_access on each method)
                ("can_index",       "PromoteDashboardView"),
                ("can_api_preview", "PromoteDashboardView"),
                ("can_api_promote", "PromoteDashboardView"),
            ]
            for action, view_name in grants:
                pvm = sm.add_permission_view_menu(action, view_name)
                if pvm:
                    sm.add_permission_role(admin_role, pvm)

        # Add plugin templates to Jinja2 search path
        pkg_templates = os.path.join(os.path.dirname(superset_promote_dashboard.__file__), "templates")
        if os.path.exists(pkg_templates):
            app.jinja_env.loader = ChoiceLoader([app.jinja_env.loader, FileSystemLoader(pkg_templates)])
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to register promote-dashboard plugin: {e}")


FLASK_APP_MUTATOR = init_promote_plugin
