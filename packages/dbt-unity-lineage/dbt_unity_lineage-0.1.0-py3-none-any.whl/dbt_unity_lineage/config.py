"""Configuration file parsing for dbt_unity_lineage.yml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator

from .mapping import UCSystemType, normalize_system_type


class SourceSystemConfig(BaseModel):
    """Configuration for a source system."""

    system_type: str
    entity_type: str = "table"
    description: Optional[str] = None
    url: Optional[str] = None
    owner: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: str) -> str:
        """Validate and normalize the system type."""
        return normalize_system_type(v).value

    @property
    def normalized_system_type(self) -> UCSystemType:
        """Get the normalized UC system type."""
        return UCSystemType(self.system_type)


class Settings(BaseModel):
    """Optional settings for the tool."""

    batch_size: int = 50
    strict: bool = False


class Config(BaseModel):
    """Root configuration model for dbt_unity_lineage.yml."""

    version: int = 1
    source_systems: Dict[str, SourceSystemConfig] = Field(default_factory=dict)
    source_paths: List[str] = Field(default_factory=list)
    settings: Settings = Field(default_factory=Settings)

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: int) -> int:
        """Validate the config version."""
        if v != 1:
            raise ValueError(f"Unsupported config version: {v}. Only version 1 is supported.")
        return v


def load_config(config_path: Union[Path, str]) -> Config:
    """Load and parse the configuration file.

    Args:
        config_path: Path to dbt_unity_lineage.yml.

    Returns:
        Parsed Config object.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If the config file is invalid.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    if raw_config is None:
        raw_config = {}

    return Config.model_validate(raw_config)


def find_config_file(project_dir: Optional[Union[Path, str]] = None) -> Optional[Path]:
    """Find the dbt_unity_lineage.yml config file.

    Searches in order:
    1. project_dir/dbt_unity_lineage.yml
    2. ./dbt_unity_lineage.yml

    Args:
        project_dir: Optional project directory to search in.

    Returns:
        Path to the config file, or None if not found.
    """
    search_paths = []

    if project_dir:
        search_paths.append(Path(project_dir) / "dbt_unity_lineage.yml")

    search_paths.append(Path.cwd() / "dbt_unity_lineage.yml")

    for path in search_paths:
        if path.exists():
            return path

    return None
