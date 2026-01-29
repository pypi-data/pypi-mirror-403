# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-01-24

### Added
- `init` command to create `dbt_unity_lineage.yml` config file with example content
- `--claude` flag to output AI context (fetches version-matched CLAUDE.md from GitHub)
- More URL patterns for exposure detection: servicenow.com, workday.com, snowflake.com, databricks.com
- More system type aliases: sfdc, sap_s4hana, redshift, synapse, fabric, and others

### Changed
- Test coverage improved from 45% to 77% (270 tests)

### Fixed
- Various edge cases in error handling

## [0.1.0] - 2026-01-24

### Added
- Initial release of `dbt-unity-lineage` CLI tool
- `push` command to sync dbt sources and exposures to Unity Catalog external lineage
- `status` command to show sync status (local vs remote comparison)
- `clean` command to remove orphaned external metadata objects
- Source system configuration via `dbt_unity_lineage.yml`
- Automatic exposure detection from URL patterns (powerbi.com, tableau.com, looker.com, salesforce.com)
- System type normalization with 30+ aliases (sap_ecc → SAP, postgres → POSTGRESQL, etc.)
- Ownership tracking via `managed_by=dbt-unity-lineage` property
- Multi-project support (projects don't interfere with each other)
- Output formats: text (Rich), JSON, Markdown
- Dry-run mode for safe previews (`--dry-run`)
- Strict mode for CI/CD pipelines (`--strict`)
- Retry logic with exponential backoff for transient API errors (429, 5xx)
- Progress indicator for sync operations
- dbt profiles.yml parsing with env var expansion
- dbt Cloud integration — fetch manifest.json directly from dbt Cloud API
  - `--dbt-cloud` flag to enable dbt Cloud mode
  - `--dbt-cloud-job-id` to fetch from latest successful run of a job
  - `--dbt-cloud-run-id` to fetch from a specific run
  - Environment variable support: `DBT_CLOUD_TOKEN`, `DBT_CLOUD_ACCOUNT_ID`

### CI/CD
- GitHub Actions workflow for unit tests (Python 3.9-3.12)
- Codecov integration for coverage reporting
- Integration tests with mock Databricks API server
- FastAPI-based mock server for external lineage API testing

### Documentation
- Comprehensive README with quick start guide
- CLI reference documentation
- Configuration reference
- MIT license

### Known Limitations
- Unity Catalog external lineage API is in Public Preview (requires workspace with feature enabled)
- No column-level lineage yet (API supports it, planned for v1.1)
