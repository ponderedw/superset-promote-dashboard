# test-environment Specification

## Purpose
TBD - created by archiving change superset-promote-dashboard. Update Purpose after archive.
## Requirements
### Requirement: Single PostgreSQL container hosts all three databases
The Docker Compose stack SHALL use one `postgres:15` service that creates three databases on first boot: `superset` (Superset metadata), `db_source` (source analytics data), and `db_target` (target analytics data). No separate Postgres containers SHALL be used.

#### Scenario: All three databases exist after stack start
- **WHEN** `docker compose up` completes and the `postgres` container is healthy
- **THEN** running `psql -U postgres -c "\l"` lists `superset`, `db_source`, and `db_target`

---

### Requirement: db_source and db_target have identical table schemas
`db_source` and `db_target` SHALL contain the same set of tables with the same column definitions. The tables SHALL be created by a single init SQL script to guarantee schema parity.

#### Scenario: Schema parity between source and target
- **WHEN** the postgres init script completes
- **THEN** `\d orders` in `db_source` and `\d orders` in `db_target` return the same column list

---

### Requirement: db_source and db_target are seeded with different mock data
`db_source` SHALL be seeded with a larger or "production-like" dataset. `db_target` SHALL be seeded with a smaller or "staging-like" dataset with different values, so that swapping a dashboard's connection produces a visually different result in charts.

#### Scenario: Source has more rows than target
- **WHEN** the init script completes
- **THEN** `SELECT COUNT(*) FROM orders` in `db_source` returns a larger number than in `db_target`

#### Scenario: Row values differ between source and target
- **WHEN** the init script completes
- **THEN** `SELECT SUM(revenue) FROM orders` returns different values in `db_source` vs `db_target`

---

### Requirement: Tables included for mock data
The init script SHALL create at least the following tables in both `db_source` and `db_target`:
- `orders` — columns: `id`, `customer_name`, `product`, `quantity`, `revenue`, `order_date`, `region`
- `customers` — columns: `id`, `name`, `email`, `country`, `signup_date`
- `products` — columns: `id`, `name`, `category`, `unit_price`

#### Scenario: All required tables exist in both databases
- **WHEN** the init script completes
- **THEN** `\dt` in both `db_source` and `db_target` lists `orders`, `customers`, and `products`

---

### Requirement: Superset init container registers database connections and datasets
A one-shot `superset-init` service SHALL run after the Postgres container is healthy. It SHALL:
1. Run `superset db upgrade` and `superset init`
2. Create the admin user
3. Register `db_source` and `db_target` as named database connections via the Superset API
4. Create datasets for each table in both databases
5. Create a sample dashboard with charts backed by `db_source` datasets

#### Scenario: Source and target connections appear in Superset after init
- **WHEN** the `superset-init` container exits with code 0
- **THEN** `GET /api/v1/database/` lists connections named "Source DB" and "Target DB"

#### Scenario: Sample dashboard exists after init
- **WHEN** the `superset-init` container exits with code 0
- **THEN** `GET /api/v1/dashboard/` lists at least one dashboard titled "Sales Overview"

---

### Requirement: Stack starts with a single command
Running `docker compose up` SHALL bring up all services (postgres, superset, superset-init) with no additional manual steps required.

#### Scenario: Superset UI is reachable after compose up
- **WHEN** `docker compose up` completes and all containers are healthy
- **THEN** `GET http://localhost:8088/login/` returns HTTP 200

