from __future__ import annotations

import logging

from flask import jsonify, request
from flask_appbuilder import BaseView, expose
from flask_appbuilder.security.decorators import has_access
from flask_wtf.csrf import generate_csrf

from superset_promote_dashboard import superset_api

logger = logging.getLogger(__name__)


class PromoteDashboardView(BaseView):
    route_base = "/promote_dashboard"
    default_view = "index"

    @expose("/")
    @has_access
    def index(self):
        try:
            dashboards = superset_api.get_dashboards()
            databases = superset_api.get_databases()
        except Exception as exc:
            logger.exception("Failed to fetch dashboards/databases: %s", exc)
            dashboards, databases = [], []

        return self.render_template(
            "promote_dashboard.html",
            dashboards=dashboards,
            databases=databases,
            csrf_token=generate_csrf(),
        )

    @expose("/api/preview", methods=["POST"])
    @has_access
    def api_preview(self):
        """
        Body: {"dashboard_id": int, "target_db_id": int}
        Returns: list of {chart_id, chart_name, current_dataset, matched_dataset, status}
        """
        data = request.get_json(force=True) or {}
        dashboard_id = data.get("dashboard_id")
        target_db_id = data.get("target_db_id")

        if not dashboard_id or not target_db_id:
            return jsonify({"error": "dashboard_id and target_db_id are required"}), 400

        try:
            charts = superset_api.get_dashboard_charts(dashboard_id)
            target_datasets = superset_api.get_datasets(target_db_id)
            preview = superset_api.build_preview(charts, target_datasets)
        except Exception as exc:
            logger.exception("Preview failed: %s", exc)
            return jsonify({"error": str(exc)}), 500

        return jsonify(preview)

    @expose("/api/promote", methods=["POST"])
    @has_access
    def api_promote(self):
        """
        Body: {"dashboard_id": int, "target_db_id": int}
        Returns: list of {chart_id, chart_name, status, error?}
        """
        data = request.get_json(force=True) or {}
        dashboard_id = data.get("dashboard_id")
        target_db_id = data.get("target_db_id")

        if not dashboard_id or not target_db_id:
            return jsonify({"error": "dashboard_id and target_db_id are required"}), 400

        try:
            charts = superset_api.get_dashboard_charts(dashboard_id)
            target_datasets = superset_api.get_datasets(target_db_id)
            preview = superset_api.build_preview(charts, target_datasets)
        except Exception as exc:
            logger.exception("Failed to build preview for promotion: %s", exc)
            return jsonify({"error": str(exc)}), 500

        results = []
        for row in preview:
            chart_id = row["chart_id"]
            chart_name = row["chart_name"]

            if row["status"] == "already_current":
                results.append({"chart_id": chart_id, "chart_name": chart_name, "status": "skipped"})
                continue

            if row["status"] != "will_swap":
                results.append({"chart_id": chart_id, "chart_name": chart_name, "status": row["status"]})
                continue

            try:
                superset_api.update_chart_datasource(chart_id, row["matched_id"])
                results.append({"chart_id": chart_id, "chart_name": chart_name, "status": "promoted"})
            except Exception as exc:
                logger.exception("Failed to update chart %s: %s", chart_id, exc)
                results.append({"chart_id": chart_id, "chart_name": chart_name, "status": "failed", "error": str(exc)})

        return jsonify(results)
