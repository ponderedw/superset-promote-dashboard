## 1. Migrate pyproject.toml to Poetry

- [x] 1.1 Replace `[build-system]` with `requires = ["poetry-core"]` / `build-backend = "poetry.core.masonry.api"`
- [x] 1.2 Replace `[project]` with `[tool.poetry]` — set `name`, `version`, `description`, `readme`, `python` constraint, and `packages` include for `superset_promote_dashboard`
- [x] 1.3 Move dependencies into `[tool.poetry.dependencies]` (`flask`, `flask-appbuilder`) and dev dependencies into `[tool.poetry.group.dev.dependencies]`
- [ ] 1.4 Run `poetry install` locally to generate `poetry.lock` and verify the package resolves correctly

## 2. Workflow File

- [x] 2.1 Create `.github/workflows/publish.yml` — trigger on `push` to `main`
- [x] 2.2 Add a `filter` job using `dorny/paths-filter@v3` that detects changes to `superset_promote_dashboard/**` and `pyproject.toml`
- [x] 2.3 Add a `publish` job that depends on `filter` and runs only when the path filter matches: checkout, set up Python 3.10, install Poetry via `curl -sSL https://install.python-poetry.org | python3 -`, run `poetry install`, `poetry build`, and `poetry publish -u __token__ -p $PYPI_TOKEN`

## 3. Validation

- [ ] 3.1 Confirm `poetry build` succeeds locally and produces a valid dist tarball + wheel
- [ ] 3.2 Confirm the path filter skips the publish job when only non-package files change (README, docker-compose.yaml, postgres/, superset/)
- [ ] 3.3 Add `PYPI_TOKEN` secret to GitHub repo settings and confirm a publish run succeeds
