"""dbt profiles.yml parsing for Databricks connection details."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict


class DatabricksConnection(BaseModel):
    """Databricks connection configuration extracted from dbt profile."""

    model_config = ConfigDict(populate_by_name=True)

    host: str
    token: str
    catalog: str
    http_path: Optional[str] = None
    schema_: Optional[str] = None

    @property
    def workspace_url(self) -> str:
        """Get the full workspace URL."""
        if self.host.startswith("https://"):
            return self.host
        return f"https://{self.host}"


def _expand_env_vars(value: Any) -> Any:
    """Expand dbt-style environment variable references.

    Supports:
    - {{ env_var('VAR_NAME') }}
    - {{ env_var('VAR_NAME', 'default') }}
    - $VAR_NAME
    - ${VAR_NAME}

    Args:
        value: The value to expand (can be any type, only strings are processed).

    Returns:
        The expanded value.
    """
    if not isinstance(value, str):
        return value

    # Pattern for {{ env_var('VAR_NAME') }} or {{ env_var('VAR_NAME', 'default') }}
    env_var_pattern = re.compile(
        r"\{\{\s*env_var\s*\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*['\"]([^'\"]*)['\"])?\s*\)\s*\}\}"
    )

    def replace_env_var(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)
        value = os.environ.get(var_name)
        if value is not None:
            return value
        if default is not None:
            return default
        raise ValueError(f"Environment variable '{var_name}' is not set and no default provided")

    result = env_var_pattern.sub(replace_env_var, value)

    # Also handle ${VAR_NAME} and $VAR_NAME patterns
    result = os.path.expandvars(result)

    return result


def _expand_env_vars_recursive(data: Any) -> Any:
    """Recursively expand environment variables in a data structure.

    Args:
        data: The data structure to process.

    Returns:
        The data structure with environment variables expanded.
    """
    if isinstance(data, dict):
        return {k: _expand_env_vars_recursive(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_expand_env_vars_recursive(item) for item in data]
    else:
        return _expand_env_vars(data)


def load_profiles(
    profiles_dir: Optional[Union[Path, str]] = None,
) -> Dict[str, Any]:
    """Load the dbt profiles.yml file.

    Args:
        profiles_dir: Path to the profiles directory (default: ~/.dbt).

    Returns:
        The parsed profiles data with environment variables expanded.

    Raises:
        FileNotFoundError: If profiles.yml doesn't exist.
    """
    if profiles_dir is None:
        profiles_dir = Path.home() / ".dbt"
    else:
        profiles_dir = Path(profiles_dir)

    profiles_path = profiles_dir / "profiles.yml"

    if not profiles_path.exists():
        raise FileNotFoundError(f"Profiles file not found: {profiles_path}")

    with open(profiles_path) as f:
        raw_profiles = yaml.safe_load(f)

    if raw_profiles is None:
        return {}

    return _expand_env_vars_recursive(raw_profiles)


def get_target_config(
    profiles: Dict[str, Any],
    profile_name: str,
    target_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Get the configuration for a specific profile and target.

    Args:
        profiles: The loaded profiles data.
        profile_name: The name of the profile.
        target_name: The name of the target (default: profile's default target).

    Returns:
        The target configuration.

    Raises:
        ValueError: If the profile or target doesn't exist.
    """
    if profile_name not in profiles:
        raise ValueError(f"Profile '{profile_name}' not found in profiles.yml")

    profile = profiles[profile_name]

    if target_name is None:
        target_name = profile.get("target")
        if target_name is None:
            raise ValueError(f"No default target specified for profile '{profile_name}'")

    outputs = profile.get("outputs", {})
    if target_name not in outputs:
        raise ValueError(f"Target '{target_name}' not found in profile '{profile_name}'")

    return outputs[target_name]


def get_databricks_connection(
    profiles_dir: Optional[Union[Path, str]] = None,
    profile_name: Optional[str] = None,
    target_name: Optional[str] = None,
    project_dir: Optional[Union[Path, str]] = None,
) -> DatabricksConnection:
    """Get Databricks connection details from dbt profiles.

    Args:
        profiles_dir: Path to the profiles directory (default: ~/.dbt).
        profile_name: The name of the profile (default: from dbt_project.yml).
        target_name: The name of the target (default: profile's default target).
        project_dir: Path to the dbt project directory (for reading dbt_project.yml).

    Returns:
        DatabricksConnection with the connection details.

    Raises:
        ValueError: If the profile is not a Databricks profile or missing required fields.
    """
    # Load profiles
    profiles = load_profiles(profiles_dir)

    # If no profile specified, try to get from dbt_project.yml
    if profile_name is None:
        profile_name = _get_profile_from_project(project_dir)
        if profile_name is None:
            raise ValueError("No profile specified and could not find dbt_project.yml")

    # Get target config
    target_config = get_target_config(profiles, profile_name, target_name)

    # Validate it's a Databricks connection
    conn_type = target_config.get("type", "").lower()
    if conn_type != "databricks":
        raise ValueError(
            f"Profile '{profile_name}' is not a Databricks connection (type: {conn_type})"
        )

    # Extract required fields
    host = target_config.get("host")
    if not host:
        raise ValueError(f"Missing 'host' in Databricks profile '{profile_name}'")

    token = target_config.get("token")
    if not token:
        raise ValueError(f"Missing 'token' in Databricks profile '{profile_name}'")

    catalog = target_config.get("catalog")
    if not catalog:
        raise ValueError(f"Missing 'catalog' in Databricks profile '{profile_name}'")

    return DatabricksConnection(
        host=host,
        token=token,
        catalog=catalog,
        http_path=target_config.get("http_path"),
        schema_=target_config.get("schema"),
    )


def _get_profile_from_project(project_dir: Optional[Union[Path, str]] = None) -> Optional[str]:
    """Get the profile name from dbt_project.yml.

    Args:
        project_dir: Path to the dbt project directory.

    Returns:
        The profile name, or None if not found.
    """
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir)

    project_file = project_dir / "dbt_project.yml"
    if not project_file.exists():
        return None

    with open(project_file) as f:
        project_config = yaml.safe_load(f)

    if project_config is None:
        return None

    return project_config.get("profile")
