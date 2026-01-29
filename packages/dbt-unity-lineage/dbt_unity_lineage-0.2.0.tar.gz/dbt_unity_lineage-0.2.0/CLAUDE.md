# CLAUDE.md - dbt-unity-lineage

> Context for Claude AI when working with dbt-unity-lineage projects.

## What is dbt-unity-lineage?

A CLI tool that pushes dbt source and exposure metadata to Databricks Unity Catalog as external lineage. It bridges the gap between where data comes from (SAP, Salesforce, etc.) and where it goes (Power BI, Tableau, etc.) — making this visible in Unity Catalog's lineage graph.

## Key Commands

```bash
# Create a config file with example content
dbt-unity-lineage init [--output FILE] [--force]

# Push sources and exposures to Unity Catalog
dbt-unity-lineage push [--dry-run] [--no-clean] [--sources-only] [--exposures-only] \
                       [--batch-size N] [--strict] [--format text|json|md]

# Show sync status (what's in sync, needs update, etc.)
dbt-unity-lineage status [--format text|json|md]

# Remove orphaned external metadata objects
dbt-unity-lineage clean [--dry-run] [--format text|json|md]

# Output this context file
dbt-unity-lineage --claude
```

### Push Options
- `--dry-run`: Preview changes without executing
- `--no-clean`: Skip removal of orphaned objects
- `--sources-only`: Only push upstream sources (skip exposures)
- `--exposures-only`: Only push downstream exposures (skip sources)
- `--batch-size N`: Control API batch size
- `--strict`: Fail immediately on first error

## Configuration

The tool uses `dbt_unity_lineage.yml` in the dbt project root:

```yaml
version: 1

source_systems:
  sap_ecc:                    # Key referenced in sources.yml
    system_type: SAP          # Normalized to UC system type
    description: SAP ECC Production
    owner: erp-team@example.com

  salesforce:
    system_type: Salesforce
    description: Salesforce CRM

# Optional: limit which source paths to process
source_paths:
  - bronze_erp
  - bronze_crm

settings:
  batch_size: 50
  strict: false
```

## Source Tagging

Sources need a single `meta.uc_source` tag pointing to the config key:

```yaml
# models/staging/sources.yml
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
# models/exposures.yml
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
- `looker.com`, `lookerstudio.google.com`, `cloud.looker.com` → LOOKER
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
| `redshift`, `amazon_redshift` | AMAZON_REDSHIFT |
| `synapse`, `azure_synapse` | AZURE_SYNAPSE |
| `snowflake` | SNOWFLAKE |
| `mongo`, `mongodb` | MONGODB |
| `powerbi`, `power_bi` | POWER_BI |
| `fabric`, `microsoft_fabric` | MICROSOFT_FABRIC |
| `mysql`, `oracle`, `kafka`, `looker`, `tableau`, `workday`, `servicenow`, `teradata`, `databricks` | (same name, uppercase) |
| Unknown values | CUSTOM |

## dbt Cloud Integration

Fetch manifest directly from dbt Cloud instead of local file:

```bash
export DBT_CLOUD_TOKEN=your-token
export DBT_CLOUD_ACCOUNT_ID=12345

# From latest successful job run
dbt-unity-lineage push --dbt-cloud --dbt-cloud-job-id 67890

# From specific run
dbt-unity-lineage push --dbt-cloud --dbt-cloud-run-id 11111
```

## Ownership & Idempotency

Every object created includes tracking properties:

```json
{
  "properties": {
    "managed_by": "dbt-unity-lineage",
    "dbt_project": "jaffle_shop",
    "dbt_source": "erp.gl_accounts"
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

1. Run `dbt-unity-lineage init` to create `dbt_unity_lineage.yml`
2. Edit the file to add your source system definitions
3. Add `meta.uc_source` tags to relevant sources in `sources.yml`
4. Run `dbt-unity-lineage push --dry-run` to preview
5. Run `dbt-unity-lineage push` to sync

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Push lineage
  run: dbt-unity-lineage push --strict --format md >> $GITHUB_STEP_SUMMARY
  env:
    DATABRICKS_HOST: ${{ vars.DATABRICKS_HOST }}
    DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

### Debugging

```bash
# Verbose output
dbt-unity-lineage push --verbose

# Check what's different
dbt-unity-lineage status --format json | jq '.sources[] | select(.status != "in_sync")'

# Preview cleanup
dbt-unity-lineage clean --dry-run
```

## File Structure Expected

```
my-dbt-project/
├── dbt_project.yml
├── dbt_unity_lineage.yml     # Tool config
├── models/
│   ├── staging/
│   │   └── sources.yml       # With meta.uc_source tags
│   └── exposures.yml         # Auto-detected
└── target/
    └── manifest.json         # Generated by dbt build
```

## Requirements

- Python 3.9+
- dbt 1.5+ (needs manifest.json)
- Databricks workspace with:
  - Unity Catalog enabled
  - External lineage preview enabled
  - `CREATE EXTERNAL METADATA` privilege on metastore

## Troubleshooting

### "API returns 404"
The external lineage API is a Public Preview feature. It must be enabled by a workspace admin. Contact your Databricks admin or account rep.

### "Create external metadata button grayed out"
Missing privilege. Run:
```sql
GRANT CREATE EXTERNAL METADATA ON METASTORE TO `user@example.com`;
```

### "Source not found in manifest"
Run `dbt build` or `dbt compile` first to generate `target/manifest.json`.

### "Unknown system type warning"
Add the system type to `source_systems` in config, or let it default to CUSTOM.

## Links

- [GitHub Repository](https://github.com/dbt-conceptual/dbt-unity-lineage)
- [PyPI Package](https://pypi.org/project/dbt-unity-lineage/)
- [Databricks External Lineage Docs](https://docs.databricks.com/aws/en/data-governance/unity-catalog/external-lineage)
- [Related: dbt-conceptual](https://github.com/dbt-conceptual/dbt-conceptual)
