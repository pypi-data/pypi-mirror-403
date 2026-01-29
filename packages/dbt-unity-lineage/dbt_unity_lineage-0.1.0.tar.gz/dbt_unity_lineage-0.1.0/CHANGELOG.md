# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- **dbt Cloud integration** - fetch manifest.json directly from dbt Cloud API (#5)
  - `--dbt-cloud` flag to enable dbt Cloud mode
  - `--dbt-cloud-job-id` to fetch from latest successful run of a job
  - `--dbt-cloud-run-id` to fetch from a specific run
  - Environment variable support: `DBT_CLOUD_TOKEN`, `DBT_CLOUD_ACCOUNT_ID`

### CI/CD
- GitHub Actions workflow for unit tests (Python 3.9-3.12)
- Codecov integration for coverage reporting
- Integration tests with real Databricks connection (runs on PRs)
- Automatic PR comments with integration test results

### Documentation
- Comprehensive README with quick start guide
- CLI reference documentation
- Configuration reference
- MIT license

### Known Limitations
- Unity Catalog external lineage API is in Public Preview (requires paid tier + feature enabled)
- No column-level lineage yet (API supports it, planned for future release)

## [0.1.0] - 2026-01-24

Initial release.
