# CLAUDE.md - dbt-unity-lineage

> Context for Claude AI when working with dbt-unity-lineage projects.

## What is dbt-unity-lineage?

A CLI tool that pushes dbt source and exposure metadata to Databricks Unity Catalog as external lineage. It bridges the gap between where data comes from (SAP, Salesforce, etc.) and where it goes (Power BI, Tableau, etc.) — making this visible in Unity Catalog's lineage graph.

## Key Commands

```bash
# Initialize configuration file
dbt-unity-lineage init [--output FILE] [--force]

# Validate configuration and folder structure
dbt-unity-lineage validate [--format text|json|md]

# Scan folders and show discovered sources/exposures
dbt-unity-lineage scan [--select PATTERN] [--type source|exposure] [--format text|json|md]

# Find missing source_systems definitions
dbt-unity-lineage sync [--dry-run] [--format text|json|md]

# Show sync status (local vs remote)
dbt-unity-lineage status [--select PATTERN] [--format text|json|md]

# Push sources and exposures to Unity Catalog
dbt-unity-lineage push [--dry-run] [--select PATTERN] [--format text|json|md]

# Remove all project objects from Unity Catalog
dbt-unity-lineage clean [--dry-run] [--force] [--format text|json|md]

# Output this context file
dbt-unity-lineage --claude
```

### Global Options
- `--project-dir PATH`: Path to dbt project directory
- `--profiles-dir PATH`: Path to profiles directory
- `--profile NAME`: dbt profile name
- `--target NAME`: dbt target name
- `--verbose` / `--quiet`: Control output verbosity

## Configuration

The tool uses `unity_lineage.yml` (default location: `models/lineage/unity_lineage.yml`):

### Minimal Configuration

```yaml
version: 1

project:
  name: my_project

configuration:
  layers:
    sources:
      sources:
        folders:
          - models/sources
```

### Full Configuration

```yaml
version: 1

project:
  name: enterprise_analytics

configuration:
  validation:
    require_owner: ${REQUIRE_OWNER:-false}
    require_source_system: ${REQUIRE_SOURCE_SYSTEM:-true}

  layers:
    bronze:
      sources:
        folders:
          - bronze/erp
          - bronze/crm
      exposures:
        folders:
          - bronze/data_quality

    gold:
      exposures:
        folders:
          - gold/dashboards
          - gold/reports

source_systems:
  sap_ecc:
    system_type: SAP
    description: SAP ECC Production
    owner: erp-team@example.com
    url: https://sap.example.com
    table_lineage: true           # Enable table-level lineage
    meta_columns:                 # Columns to exclude from lineage
      - _loaded_at
      - _batch_id
    meta:                         # Custom properties
      environment: production

  salesforce:
    system_type: Salesforce
    description: Salesforce CRM
```

### Configuration Options

| Section | Field | Required | Description |
|---------|-------|----------|-------------|
| `project.name` | | Yes | Project identifier for tagging in UC |
| `configuration.validation` | `require_owner` | No | Require owner on sources (default: false) |
| | `require_description` | No | Require description on sources (default: false) |
| | `require_source_system` | No | Require `uc_source` meta on all sources (default: false) |
| `configuration.layers.{name}` | `sources.folders` | No* | Folders to scan for sources |
| | `exposures.folders` | No* | Folders to scan for exposures |
| `source_systems.{key}` | `system_type` | Yes | Type of system (SAP, Salesforce, etc.) |
| | `table_lineage` | No | Enable table-level lineage (default: false) |
| | `meta_columns` | No | Columns to exclude from lineage |

*Each layer needs at least one of `sources` or `exposures`.

## Source Tagging

Sources need a `meta.uc_source` tag pointing to the config key:

```yaml
# bronze/erp/_sources.yml
sources:
  - name: erp
    meta:
      uc_source: sap_ecc      # References source_systems key
    tables:
      - name: gl_accounts
      - name: cost_centers
```

## Exposures

Exposures work automatically — no extra config needed. System type is inferred from URL:

```yaml
# gold/dashboards/_exposures.yml
exposures:
  - name: executive_dashboard
    type: dashboard
    url: https://app.powerbi.com/groups/abc/reports/xyz  # Detected as POWER_BI
    depends_on:
      - ref('fct_orders')
```

URL patterns recognized:
- `powerbi.com` → POWER_BI
- `tableau.com` → TABLEAU
- `looker.com`, `lookerstudio.google.com` → LOOKER
- `salesforce.com`, `lightning.force.com` → SALESFORCE
- `servicenow.com` → SERVICENOW
- `workday.com` → WORKDAY
- `snowflake.com` → SNOWFLAKE
- `databricks.com` → DATABRICKS

## System Type Normalization

The tool normalizes common aliases to Unity Catalog system types:

| Input | Normalized |
|-------|------------|
| `sap`, `sap_ecc`, `sap_hana`, `sap_s4hana` | SAP |
| `salesforce`, `sfdc` | SALESFORCE |
| `postgres`, `postgresql`, `pg` | POSTGRESQL |
| `sql_server`, `mssql`, `sqlserver` | MICROSOFT_SQL_SERVER |
| `bigquery`, `bq` | GOOGLE_BIGQUERY |
| `powerbi`, `power_bi` | POWER_BI |
| Unknown values | CUSTOM |

## Ownership & Idempotency

Every object created includes tracking properties:

```json
{
  "properties": {
    "dbt_unity_lineage_managed": "true",
    "dbt_unity_lineage_project": "my_project"
  }
}
```

This ensures:
- Safe to run repeatedly (idempotent)
- Multiple dbt projects don't interfere
- Manual UC objects are never touched
- `clean` only removes objects we created

## Common Tasks

### Initial Setup

1. Run `dbt-unity-lineage init` to create `models/lineage/unity_lineage.yml`
2. Edit the file to configure layers and source systems
3. Add `meta.uc_source` tags to relevant sources in `_sources.yml`
4. Run `dbt-unity-lineage validate` to check configuration
5. Run `dbt-unity-lineage scan` to preview what will be synced
6. Run `dbt-unity-lineage push --dry-run` to preview changes
7. Run `dbt-unity-lineage push` to sync

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Validate lineage
  run: dbt-unity-lineage validate --format md >> $GITHUB_STEP_SUMMARY

- name: Push lineage
  run: dbt-unity-lineage push --format md >> $GITHUB_STEP_SUMMARY
  env:
    DATABRICKS_HOST: ${{ vars.DATABRICKS_HOST }}
    DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

### Debugging

```bash
# Verbose output
dbt-unity-lineage push --verbose

# Check what's in your folders
dbt-unity-lineage scan --format json

# Find missing source_systems
dbt-unity-lineage sync --dry-run

# Preview cleanup
dbt-unity-lineage clean --dry-run
```

## File Structure Expected

```
my-dbt-project/
├── dbt_project.yml
├── models/
│   ├── lineage/
│   │   └── unity_lineage.yml    # Tool config (default location)
│   ├── bronze/
│   │   └── erp/
│   │       └── _sources.yml     # With meta.uc_source tags
│   └── gold/
│       └── dashboards/
│           └── _exposures.yml   # Auto-detected from URL
└── profiles.yml                 # Databricks connection
```

## Requirements

- Python 3.9+
- Databricks workspace with:
  - Unity Catalog enabled
  - External lineage preview enabled
  - `CREATE EXTERNAL METADATA` privilege on metastore

## Important Notes

### Table-Level Lineage (Coming Soon)

The configuration supports `table_lineage: true` for source systems, which would enable column-level lineage from source tables. However, the Databricks API does not yet support this feature. The configuration option is available for forward compatibility.

### Unity Catalog External Lineage is in Public Preview

As of January 2026, this feature is in Public Preview. The API may change.

## Troubleshooting

### "API returns 404"
The external lineage API is a Public Preview feature. It must be enabled by a workspace admin.

### "Create external metadata button grayed out"
Missing privilege. Run:
```sql
GRANT CREATE EXTERNAL METADATA ON METASTORE TO `user@example.com`;
```

### "No config file found"
Run `dbt-unity-lineage init` or specify path with `--project-dir`.

### "Unknown system type warning"
Add the system type to `source_systems` in config, or let it default to CUSTOM.

## Links

- [GitHub Repository](https://github.com/dbt-conceptual/dbt-unity-lineage)
- [PyPI Package](https://pypi.org/project/dbt-unity-lineage/)
- [Databricks External Lineage Docs](https://docs.databricks.com/aws/en/data-governance/unity-catalog/external-lineage)
