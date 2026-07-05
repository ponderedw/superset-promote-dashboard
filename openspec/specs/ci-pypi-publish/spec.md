# ci-pypi-publish Specification

## Purpose
TBD - created by archiving change github-ci-pypi. Update Purpose after archive.
## Requirements
### Requirement: Publish to PyPI on relevant push to main
The system SHALL automatically build and publish the package to PyPI whenever a push to `main` modifies `superset_promote_dashboard/` source files or `pyproject.toml`.

#### Scenario: Package source changes merged to main
- **WHEN** a commit is pushed to `main` that modifies files under `superset_promote_dashboard/` or `pyproject.toml`
- **THEN** the workflow builds a distribution and publishes it to PyPI using the `PYPI_TOKEN` secret

#### Scenario: Non-package changes merged to main
- **WHEN** a commit is pushed to `main` that only modifies files outside `superset_promote_dashboard/` and `pyproject.toml` (e.g. README, docker, postgres SQL)
- **THEN** the publish job is skipped and no PyPI upload occurs

### Requirement: Publish uses token authentication
The workflow SHALL authenticate to PyPI using a token stored as the `PYPI_TOKEN` GitHub repository secret.

#### Scenario: Token present
- **WHEN** the workflow runs and `PYPI_TOKEN` is set in repository secrets
- **THEN** twine uploads the package successfully without prompting for credentials

#### Scenario: Token absent
- **WHEN** `PYPI_TOKEN` is not set
- **THEN** the publish step fails with an authentication error and no package is uploaded

