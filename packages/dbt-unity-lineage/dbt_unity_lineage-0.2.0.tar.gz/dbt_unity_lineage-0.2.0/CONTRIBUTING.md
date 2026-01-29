# Contributing to dbt-unity-lineage

Thanks for your interest in contributing!

## Development Setup

```bash
# Clone the repo
git clone https://github.com/dbt-conceptual/dbt-unity-lineage.git
cd dbt-unity-lineage

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"
```

## Running Tests

```bash
# Unit tests
pytest

# With coverage
pytest --cov=dbt_unity_lineage

# Integration tests (requires Databricks credentials in env vars)
export DATABRICKS_HOST="your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"
export DATABRICKS_CATALOG="your-catalog"
pytest -m integration
```

## Code Style

We use:
- **ruff** for linting and formatting
- **mypy** for type checking

```bash
# Format
ruff format .

# Lint
ruff check .

# Type check
mypy src/
```

## Pull Request Process

1. **Open an issue first** — Discuss what you'd like to change
2. **Fork and branch** — Create a feature branch from `main`
3. **Write tests** — Cover your changes
4. **Update docs** — If you're changing behavior
5. **Submit PR** — Link to the issue

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add column-level lineage support
fix: handle empty manifest gracefully  
docs: update CI/CD example
chore: bump databricks-sdk version
```

## Questions?

Open an issue or start a discussion. We're happy to help.
