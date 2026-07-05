## Context

The package is built with `setuptools` via `pyproject.toml` (no Poetry). The reference workflow uses Poetry, so the build step needs to be adapted. PyPI publishing uses a trusted token (`PYPI_TOKEN`) stored as a GitHub secret. The workflow should only run when package-relevant files change to avoid spurious publishes on doc or config-only commits.

## Goals / Non-Goals

**Goals:**
- Automatically publish to PyPI on every push to `main` that touches the package
- Use path filtering so unrelated changes (README, docker, postgres/) don't trigger a release
- Mirror the structure of the reference `superset-mcp-plugins` publish workflow

**Non-Goals:**
- Version bumping automation — the developer is responsible for updating `version` in `pyproject.toml` before merging
- Test or lint steps — out of scope for this workflow
- Publishing on tags or PRs — `main` push only

## Decisions

**Build tool: Poetry**
Matches the reference `superset-mcp-plugins` workflow exactly. Requires migrating `pyproject.toml` from `setuptools` to Poetry format (`[tool.poetry]` sections, `poetry.lock`). The workflow installs Poetry via the official installer, then runs `poetry install && poetry build && poetry publish`. Alternative considered: `build` + `twine` to avoid migrating pyproject.toml — rejected to stay consistent with the reference project.

**Path filter: `superset_promote_dashboard/**` and `pyproject.toml`**
These are the only files that affect the published package. Workflow files, Docker config, postgres SQL, and docs changes should not trigger a release. Same pattern as the reference workflow's `mcp_library` filter.

**Publish via `twine` with `PYPI_TOKEN` secret**
Standard PyPI trusted-publisher pattern. The token is scoped to this package and stored as a repo secret (`PYPI_TOKEN`). Alternative: OIDC trusted publishing — deferred as a future improvement.

## Risks / Trade-offs

- **Accidental publish on version bump omission** → Developer must remember to bump version in `pyproject.toml`; if they forget, PyPI will reject the upload with a version conflict error (non-destructive).
- **Token exposure** → Token is a repo secret, not in workflow YAML; GitHub masks it in logs.
