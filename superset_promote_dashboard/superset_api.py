"""
Thin wrappers around the Superset REST API.
All calls are made server-side using the current user's session cookie.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import requests
from flask import request as flask_request, current_app

logger = logging.getLogger(__name__)

_TIMEOUT = 30


def _base_url() -> str:
    host = current_app.config.get("SUPERSET_WEBSERVER_HOST", "localhost")
    port = current_app.config.get("SUPERSET_WEBSERVER_PORT", 8088)
    proto = "https" if current_app.config.get("SUPERSET_WEBSERVER_PROTOCOL") == "https" else "http"
    return f"{proto}://{host}:{port}"


def _cookies() -> dict[str, str]:
    return flask_request.cookies.to_dict()


def _auth_headers() -> dict[str, str]:
    try:
        from flask_wtf.csrf import generate_csrf
        csrf = generate_csrf()
    except Exception:
        csrf = ""
    return {"Content-Type": "application/json", "X-CSRFToken": csrf}


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def get_dashboards() -> list[dict[str, Any]]:
    resp = requests.get(
        f"{_base_url()}/api/v1/dashboard/",
        cookies=_cookies(),
        params={"q": json.dumps({"page_size": 200, "order_column": "dashboard_title", "order_direction": "asc"})},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def get_dashboard_charts(dashboard_id: int) -> list[dict[str, Any]]:
    resp = requests.get(
        f"{_base_url()}/api/v1/dashboard/{dashboard_id}/charts",
        cookies=_cookies(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def get_databases() -> list[dict[str, Any]]:
    resp = requests.get(
        f"{_base_url()}/api/v1/database/",
        cookies=_cookies(),
        params={"q": json.dumps({"page_size": 200})},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def get_datasets(db_id: int) -> list[dict[str, Any]]:
    """Return all physical datasets for a given database."""
    resp = requests.get(
        f"{_base_url()}/api/v1/dataset/",
        cookies=_cookies(),
        params={"q": json.dumps({"page_size": 500})},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        ds for ds in resp.json().get("result", [])
        if ds.get("database", {}).get("id") == db_id
    ]


def get_dataset(dataset_id: int) -> dict[str, Any]:
    resp = requests.get(
        f"{_base_url()}/api/v1/dataset/{dataset_id}",
        cookies=_cookies(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("result", {})


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def update_chart_datasource(chart_id: int, dataset_id: int) -> None:
    resp = requests.put(
        f"{_base_url()}/api/v1/chart/{chart_id}",
        cookies=_cookies(),
        headers=_auth_headers(),
        json={"datasource_id": dataset_id, "datasource_type": "table"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Datasource parsing
# ---------------------------------------------------------------------------

def _parse_datasource(form_data: dict) -> tuple[int | None, str]:
    """
    Parse 'datasource' from chart form_data.
    Format: "{id}__table" or "{id}__query" (virtual).
    Returns (dataset_id, type_str).
    """
    raw = form_data.get("datasource", "")
    if not raw or "__" not in raw:
        return None, ""
    parts = raw.split("__", 1)
    try:
        return int(parts[0]), parts[1]
    except ValueError:
        return None, ""


def _is_virtual(ds_type: str) -> bool:
    return ds_type not in ("table", "")


# ---------------------------------------------------------------------------
# Matching logic
# ---------------------------------------------------------------------------

def build_preview(dashboard_charts: list[dict], target_datasets: list[dict]) -> list[dict]:
    """
    For each chart return a preview row:
      {chart_id, chart_name, current_dataset, matched_dataset, matched_id, status}

    status: 'will_swap' | 'no_match' | 'virtual' | 'error'
    """
    # Index target datasets by (table_name, schema) and by table_name alone
    by_table_schema: dict[tuple[str, str], dict] = {}
    by_table: dict[str, dict] = {}
    for ds in target_datasets:
        tname = ds.get("table_name", "")
        schema = ds.get("schema") or ""
        by_table_schema[(tname, schema)] = ds
        by_table.setdefault(tname, ds)

    rows = []
    for chart in dashboard_charts:
        chart_id = chart.get("id")
        chart_name = chart.get("slice_name") or f"Chart {chart_id}"
        form_data = chart.get("form_data") or {}

        ds_id, ds_type = _parse_datasource(form_data)

        if _is_virtual(ds_type):
            rows.append({
                "chart_id": chart_id,
                "chart_name": chart_name,
                "current_dataset": form_data.get("datasource", "—"),
                "matched_dataset": None,
                "matched_id": None,
                "status": "virtual",
            })
            continue

        # Look up the source dataset to get table_name + schema
        src_table = ""
        src_schema = ""
        if ds_id:
            try:
                ds = get_dataset(ds_id)
                src_table = ds.get("table_name", "")
                src_schema = ds.get("schema") or ""
            except Exception as exc:
                logger.warning("Could not fetch dataset %s: %s", ds_id, exc)

        if not src_table:
            rows.append({
                "chart_id": chart_id,
                "chart_name": chart_name,
                "current_dataset": f"Dataset {ds_id}" if ds_id else "—",
                "matched_dataset": None,
                "matched_id": None,
                "status": "no_match",
            })
            continue

        # Match against target
        matched = by_table_schema.get((src_table, src_schema)) if src_schema else None
        if matched is None:
            matched = by_table.get(src_table)

        if matched:
            already_current = matched.get("id") == ds_id
            rows.append({
                "chart_id": chart_id,
                "chart_name": chart_name,
                "current_dataset": src_table,
                "matched_dataset": matched.get("table_name"),
                "matched_id": matched.get("id"),
                "status": "already_current" if already_current else "will_swap",
            })
        else:
            rows.append({
                "chart_id": chart_id,
                "chart_name": chart_name,
                "current_dataset": src_table,
                "matched_dataset": None,
                "matched_id": None,
                "status": "no_match",
            })

    return rows
