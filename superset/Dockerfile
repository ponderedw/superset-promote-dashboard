FROM apache/superset:4.1.1

USER root

# Install psycopg2 for PostgreSQL connections
RUN pip install --no-cache-dir psycopg2-binary pillow

# Copy and install the plugin package
COPY superset_promote_dashboard /app/superset_promote_dashboard
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir /app

USER superset
