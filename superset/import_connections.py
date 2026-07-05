"""
One-shot init script: registers database connections, datasets, charts,
and a sample dashboard in a freshly started Superset instance.
Run inside the superset-init container after `superset init`.
"""
import json
import os
import sys
import time

import requests

SUPERSET_URL = os.environ.get("SUPERSET_URL", "http://superset:8088")
USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

SOURCE_DB_URI = os.environ.get(
    "SOURCE_DB_URI",
    "postgresql+psycopg2://superset:superset@postgres:5432/db_source",
)
TARGET_DB_URI = os.environ.get(
    "TARGET_DB_URI",
    "postgresql+psycopg2://superset:superset@postgres:5432/db_target",
)

TABLES = ["students", "grades", "attendance"]


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def wait_for_superset(timeout: int = 120) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{SUPERSET_URL}/health", timeout=5)
            if r.status_code == 200:
                print("Superset is up.")
                return
        except requests.exceptions.ConnectionError:
            pass
        print("Waiting for Superset…")
        time.sleep(5)
    print("ERROR: Superset did not become healthy in time.", file=sys.stderr)
    sys.exit(1)


def get_tokens() -> tuple[str, str]:
    resp = requests.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={"username": USERNAME, "password": PASSWORD, "provider": "db", "refresh": True},
    )
    resp.raise_for_status()
    access_token = resp.json()["access_token"]

    csrf_resp = requests.get(
        f"{SUPERSET_URL}/api/v1/security/csrf_token/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    csrf_resp.raise_for_status()
    csrf_token = csrf_resp.json()["result"]
    return access_token, csrf_token


def make_headers(access_token: str, csrf_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/json",
        "Referer": SUPERSET_URL,
    }


# ---------------------------------------------------------------------------
# Database connections
# ---------------------------------------------------------------------------

def create_database(headers: dict, name: str, uri: str) -> int:
    # Check if already exists
    resp = requests.get(f"{SUPERSET_URL}/api/v1/database/", headers=headers)
    resp.raise_for_status()
    for db in resp.json().get("result", []):
        if db["database_name"] == name:
            print(f"  Database '{name}' already exists (id={db['id']})")
            return db["id"]

    resp = requests.post(
        f"{SUPERSET_URL}/api/v1/database/",
        headers=headers,
        json={
            "database_name": name,
            "sqlalchemy_uri": uri,
            "expose_in_sqllab": True,
            "allow_run_async": True,
            "allow_dml": False,
            "allow_ctas": False,
            "allow_cvas": False,
        },
    )
    if resp.status_code not in (200, 201):
        print(f"  ERROR creating database '{name}': {resp.text}", file=sys.stderr)
        sys.exit(1)
    db_id = resp.json()["id"]
    print(f"  Created database '{name}' (id={db_id})")
    return db_id


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

def create_dataset(headers: dict, db_id: int, table_name: str) -> int:
    # List datasets for this database and check by table_name
    resp = requests.get(
        f"{SUPERSET_URL}/api/v1/dataset/",
        headers=headers,
        params={"q": json.dumps({"filters": [
            {"col": "database_id", "opr": "DatasetIsNullOrNotFilter", "value": False},
        ], "page_size": 500})},
    )
    # Fallback: fetch all and filter locally
    all_resp = requests.get(
        f"{SUPERSET_URL}/api/v1/dataset/",
        headers=headers,
        params={"q": json.dumps({"page_size": 500})},
    )
    if all_resp.ok:
        for ds in all_resp.json().get("result", []):
            if ds.get("table_name") == table_name and ds.get("database", {}).get("id") == db_id:
                ds_id = ds["id"]
                print(f"    Dataset '{table_name}' already exists (id={ds_id})")
                return ds_id

    resp = requests.post(
        f"{SUPERSET_URL}/api/v1/dataset/",
        headers=headers,
        json={"database": db_id, "table_name": table_name, "schema": "public"},
    )
    if resp.status_code not in (200, 201):
        print(f"    ERROR creating dataset '{table_name}': {resp.text}", file=sys.stderr)
        sys.exit(1)
    ds_id = resp.json()["id"]
    print(f"    Created dataset '{table_name}' (id={ds_id})")
    return ds_id


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def create_chart(headers: dict, slice_name: str, viz_type: str, datasource_id: int, params: dict) -> int:
    # Check if exists
    resp = requests.get(
        f"{SUPERSET_URL}/api/v1/chart/",
        headers=headers,
        params={"q": json.dumps({"filters": [{"col": "slice_name", "opr": "eq", "value": slice_name}]})},
    )
    resp.raise_for_status()
    results = resp.json().get("result", [])
    if results:
        chart_id = results[0]["id"]
        print(f"    Chart '{slice_name}' already exists (id={chart_id})")
        return chart_id

    resp = requests.post(
        f"{SUPERSET_URL}/api/v1/chart/",
        headers=headers,
        json={
            "slice_name": slice_name,
            "viz_type": viz_type,
            "datasource_id": datasource_id,
            "datasource_type": "table",
            "params": json.dumps(params),
        },
    )
    if resp.status_code not in (200, 201):
        print(f"    ERROR creating chart '{slice_name}': {resp.text}", file=sys.stderr)
        sys.exit(1)
    chart_id = resp.json()["id"]
    print(f"    Created chart '{slice_name}' (id={chart_id})")
    return chart_id


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def create_dashboard(headers: dict, title: str, chart_ids: list[int]) -> int:
    # Check if exists
    resp = requests.get(
        f"{SUPERSET_URL}/api/v1/dashboard/",
        headers=headers,
        params={"q": json.dumps({"filters": [{"col": "dashboard_title", "opr": "eq", "value": title}]})},
    )
    resp.raise_for_status()
    results = resp.json().get("result", [])
    if results:
        dash_id = results[0]["id"]
        print(f"  Dashboard '{title}' already exists (id={dash_id})")
        return dash_id

    resp = requests.post(
        f"{SUPERSET_URL}/api/v1/dashboard/",
        headers=headers,
        json={"dashboard_title": title, "published": True},
    )
    if resp.status_code not in (200, 201):
        print(f"  ERROR creating dashboard '{title}': {resp.text}", file=sys.stderr)
        sys.exit(1)
    dash_id = resp.json()["id"]
    print(f"  Created dashboard '{title}' (id={dash_id})")

    # Link each chart to the dashboard
    for chart_id in chart_ids:
        link_resp = requests.put(
            f"{SUPERSET_URL}/api/v1/chart/{chart_id}",
            headers=headers,
            json={"dashboards": [dash_id]},
        )
        if not link_resp.ok:
            print(f"  WARNING: could not link chart {chart_id} to dashboard: {link_resp.text}", file=sys.stderr)
        else:
            print(f"    Linked chart {chart_id} to dashboard {dash_id}")

    return dash_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    wait_for_superset()
    print("\n--- Authenticating ---")
    access_token, csrf_token = get_tokens()
    headers = make_headers(access_token, csrf_token)

    print("\n--- Creating database connections ---")
    source_db_id = create_database(headers, "Source DB", SOURCE_DB_URI)
    target_db_id = create_database(headers, "Target DB", TARGET_DB_URI)

    print("\n--- Creating datasets for Source DB ---")
    source_datasets: dict[str, int] = {}
    for table in TABLES:
        source_datasets[table] = create_dataset(headers, source_db_id, table)

    print("\n--- Creating datasets for Target DB ---")
    for table in TABLES:
        create_dataset(headers, target_db_id, table)

    print("\n--- Creating charts (backed by Source DB) ---")
    grades_ds   = source_datasets["grades"]
    students_ds = source_datasets["students"]
    attend_ds   = source_datasets["attendance"]

    chart_ids = [
        create_chart(
            headers,
            slice_name="Average Score by Subject",
            viz_type="echarts_bar",
            datasource_id=grades_ds,
            params={
                "groupby": ["subject"],
                "metrics": [{"aggregate": "AVG", "column": {"column_name": "score"}, "expressionType": "SIMPLE", "label": "AVG(score)"}],
                "row_limit": 10,
            },
        ),
        create_chart(
            headers,
            slice_name="Scores by Quarter",
            viz_type="echarts_bar",
            datasource_id=grades_ds,
            params={
                "groupby": ["quarter"],
                "metrics": [{"aggregate": "AVG", "column": {"column_name": "score"}, "expressionType": "SIMPLE", "label": "AVG(score)"}],
                "row_limit": 10,
            },
        ),
        create_chart(
            headers,
            slice_name="Pass vs Fail by Quarter",
            viz_type="pie",
            datasource_id=grades_ds,
            params={
                "groupby": ["quarter"],
                "metric": {"aggregate": "COUNT", "column": {"column_name": "id"}, "expressionType": "SIMPLE", "label": "COUNT(*)"},
            },
        ),
        create_chart(
            headers,
            slice_name="Students by Grade Level",
            viz_type="echarts_bar",
            datasource_id=students_ds,
            params={
                "groupby": ["grade_level"],
                "metrics": [{"aggregate": "COUNT", "column": {"column_name": "id"}, "expressionType": "SIMPLE", "label": "COUNT(*)"}],
                "row_limit": 10,
            },
        ),
        create_chart(
            headers,
            slice_name="Attendance by Day Type",
            viz_type="pie",
            datasource_id=attend_ds,
            params={
                "groupby": ["day_type"],
                "metric": {"aggregate": "COUNT", "column": {"column_name": "id"}, "expressionType": "SIMPLE", "label": "COUNT(*)"},
            },
        ),
    ]

    print("\n--- Creating dashboard ---")
    create_dashboard(headers, "Academic Overview", chart_ids)

    print("\n=== Init complete ===")
    print(f"  Source DB id : {source_db_id}")
    print(f"  Target DB id : {target_db_id}")
    print(f"  Charts created: {len(chart_ids)}")
    print("  Dashboard: Academic Overview")


if __name__ == "__main__":
    main()
