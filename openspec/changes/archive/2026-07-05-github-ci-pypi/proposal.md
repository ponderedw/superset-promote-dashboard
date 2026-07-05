## Why

The plugin is shippable but has no automated release process — publishing to PyPI is manual and error-prone. Adding a CI workflow means every merge to `main` that touches the package automatically builds and publishes a new version, keeping PyPI in sync with the repo without developer intervention.

## What Changes

- Add `.github/workflows/publish.yml` — triggers on push to `main`, filters to package-relevant paths, builds with standard tooling, and publishes to PyPI using a token secret
- No changes to plugin code or Docker environment

## Capabilities

### New Capabilities
- `ci-pypi-publish`: GitHub Actions workflow that builds and publishes the package to PyPI on every relevant push to `main`

### Modified Capabilities

## Impact

- New file: `.github/workflows/publish.yml`
- Requires `PYPI_TOKEN` secret set in the GitHub repo settings
- `pyproject.toml` must have a valid version and package metadata (already in place)
- No runtime or plugin behavior changes
