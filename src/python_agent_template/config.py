"""Typed configuration models and loading for this application.

All hyperparameters, thresholds, hardware targets, and file paths must be
defined in YAML files under ``configs/`` and loaded through `load_config`,
never hardcoded in processing logic.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class HardwareConfig(BaseModel):
    """Hardware target configuration.

    Parameters
    ----------
    device : str
        Compute device identifier (e.g. ``"a100"``, ``"dgx"``, ``"cpu"``).
    num_workers : int
        Number of data-loading worker processes.
    """

    device: str
    num_workers: int = Field(ge=0)


class ExampleConfig(BaseModel):
    """Example placeholder configuration block.

    Replace this with your application's real configuration as the
    project grows. Demonstrates a typed, validated config section loaded
    via `load_config`.

    Parameters
    ----------
    feature_name : str
        Name of the example feature this config section controls.
    enabled : bool
        Whether the example feature is active.
    """

    feature_name: str
    enabled: bool = True


class AppConfig(BaseModel):
    """Top-level application configuration.

    Parameters
    ----------
    hardware : HardwareConfig
        Hardware target settings.
    example : ExampleConfig
        Example placeholder settings.
    data_dir : Path
        Root directory for pipeline input/output data.
    """

    hardware: HardwareConfig
    example: ExampleConfig
    data_dir: Path


def read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML file into a plain dictionary.

    Parameters
    ----------
    path : Path
        Path to the YAML configuration file.

    Returns
    -------
    dict[str, Any]
        Parsed YAML contents.

    Raises
    ------
    FileNotFoundError
        If `path` does not exist.
    yaml.YAMLError
        If `path` does not contain valid YAML.
    """
    if not path.exists():
        msg = f"Config file not found: {path}"
        raise FileNotFoundError(msg)

    with path.open("r", encoding="utf-8") as handle:
        contents: dict[str, Any] = yaml.safe_load(handle)
    return contents


def load_config(path: Path) -> AppConfig:
    """Load and validate an `AppConfig` from a YAML file.

    Parameters
    ----------
    path : Path
        Path to the YAML configuration file.

    Returns
    -------
    AppConfig
        Validated application configuration.

    Raises
    ------
    FileNotFoundError
        If `path` does not exist.
    pydantic.ValidationError
        If the YAML contents do not satisfy the `AppConfig` schema.
    """
    raw = read_yaml(path)
    return AppConfig.model_validate(raw)
