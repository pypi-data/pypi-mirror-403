"""Configuration file parsing for unity_lineage.yml (V2 schema)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from .mapping import normalize_system_type


class ValidationConfig(BaseModel):
    """Validation settings with ENV var support."""

    require_owner: bool = False
    require_description: bool = False
    require_source_system: bool = False


class LayerSources(BaseModel):
    """Sources configuration for a layer."""

    folders: List[str] = Field(default_factory=list)


class LayerExposures(BaseModel):
    """Exposures configuration for a layer."""

    folders: List[str] = Field(default_factory=list)


class LayerConfig(BaseModel):
    """Configuration for a single layer."""

    sources: Optional[LayerSources] = None
    exposures: Optional[LayerExposures] = None

    @model_validator(mode="after")
    def validate_at_least_one(self) -> LayerConfig:
        """Ensure at least one of sources or exposures is defined."""
        if self.sources is None and self.exposures is None:
            raise ValueError("Layer must have at least one of 'sources' or 'exposures'")
        return self

    @property
    def source_folders(self) -> List[str]:
        """Get list of source folders."""
        return self.sources.folders if self.sources else []

    @property
    def exposure_folders(self) -> List[str]:
        """Get list of exposure folders."""
        return self.exposures.folders if self.exposures else []


class Configuration(BaseModel):
    """Project configuration settings."""

    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    layers: Dict[str, LayerConfig] = Field(default_factory=dict)

    @field_validator("layers")
    @classmethod
    def validate_layers(cls, v: Dict[str, LayerConfig]) -> Dict[str, LayerConfig]:
        """Ensure at least one layer is defined."""
        if not v:
            raise ValueError("At least one layer must be defined in configuration.layers")
        return v


class ProjectConfig(BaseModel):
    """Project identification."""

    name: str


class SourceSystemConfig(BaseModel):
    """Configuration for a source system."""

    system_type: str
    description: Optional[str] = None
    owner: Optional[str] = None
    url: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    table_lineage: bool = False
    meta_columns: List[str] = Field(default_factory=list)

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: str) -> str:
        """Validate and normalize the system type."""
        return normalize_system_type(v).value


class Config(BaseModel):
    """Root configuration model for unity_lineage.yml (V2)."""

    version: int = 1
    project: ProjectConfig
    configuration: Configuration
    source_systems: Dict[str, SourceSystemConfig] = Field(default_factory=dict)

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: int) -> int:
        """Validate the config version."""
        if v != 1:
            raise ValueError(f"Unsupported config version: {v}. Only version 1 is supported.")
        return v

    @property
    def project_name(self) -> str:
        """Get the project name."""
        return self.project.name

    def get_all_source_folders(self) -> List[str]:
        """Get all source folders across all layers."""
        folders = []
        for layer in self.configuration.layers.values():
            folders.extend(layer.source_folders)
        return folders

    def get_all_exposure_folders(self) -> List[str]:
        """Get all exposure folders across all layers."""
        folders = []
        for layer in self.configuration.layers.values():
            folders.extend(layer.exposure_folders)
        return folders

    def get_source_folders_for_layer(self, layer_name: str) -> List[str]:
        """Get source folders for a specific layer."""
        layer = self.configuration.layers.get(layer_name)
        return layer.source_folders if layer else []

    def get_exposure_folders_for_layer(self, layer_name: str) -> List[str]:
        """Get exposure folders for a specific layer."""
        layer = self.configuration.layers.get(layer_name)
        return layer.exposure_folders if layer else []


# ENV var pattern: ${VAR_NAME} or ${VAR_NAME:-default}
ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(:-([^}]*))?\}")


def expand_env_vars(value: Any) -> Any:
    """Recursively expand environment variables in config values.

    Supports patterns:
    - ${VAR_NAME} - uses environment variable, empty string if not set
    - ${VAR_NAME:-default} - uses environment variable, default if not set

    Args:
        value: The value to expand (can be string, dict, list, or other).

    Returns:
        The value with environment variables expanded.
    """
    if isinstance(value, str):
        return _expand_string(value)
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    return value


def _expand_string(value: str) -> Union[str, bool]:
    """Expand environment variables in a string value.

    Args:
        value: The string value to expand.

    Returns:
        The expanded value. If the result is 'true'/'false', returns a boolean.
    """

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(3) if match.group(3) is not None else ""
        return os.environ.get(var_name, default)

    result = ENV_VAR_PATTERN.sub(replacer, value)

    # Convert boolean strings
    if result.lower() == "true":
        return True
    elif result.lower() == "false":
        return False
    return result


def load_config(config_path: Union[Path, str]) -> Config:
    """Load and parse the configuration file.

    Args:
        config_path: Path to unity_lineage.yml.

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

    # Expand environment variables
    raw_config = expand_env_vars(raw_config)

    return Config.model_validate(raw_config)


def find_config_file(project_dir: Optional[Union[Path, str]] = None) -> Optional[Path]:
    """Find the unity_lineage.yml config file.

    Searches in order:
    1. project_dir/models/lineage/unity_lineage.yml
    2. project_dir/unity_lineage.yml
    3. ./models/lineage/unity_lineage.yml
    4. ./unity_lineage.yml

    Args:
        project_dir: Optional project directory to search in.

    Returns:
        Path to the config file, or None if not found.
    """
    search_paths = []

    if project_dir:
        project_path = Path(project_dir)
        search_paths.append(project_path / "models" / "lineage" / "unity_lineage.yml")
        search_paths.append(project_path / "unity_lineage.yml")

    search_paths.append(Path.cwd() / "models" / "lineage" / "unity_lineage.yml")
    search_paths.append(Path.cwd() / "unity_lineage.yml")

    for path in search_paths:
        if path.exists():
            return path

    return None
