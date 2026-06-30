"""Tests for {{ project_slug }}.config."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from {{ project_slug }}.config import AppConfig, load_config, read_yaml

VALID_CONFIG: dict[str, Any] = {
    "hardware": {"device": "a100", "num_workers": 2},
    "example": {"feature_name": "demo", "enabled": True},
    "data_dir": "data/",
}


def test_read_yaml_returns_dict_for_existing_file(tmp_path: Path) -> None:
    """read_yaml parses an existing YAML file into a dict."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(VALID_CONFIG))

    result = read_yaml(config_path)

    assert result == VALID_CONFIG


def test_read_yaml_raises_file_not_found_for_missing_file(tmp_path: Path) -> None:
    """read_yaml raises FileNotFoundError when the path does not exist."""
    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        read_yaml(missing_path)


def test_load_config_returns_app_config_for_valid_yaml(tmp_path: Path) -> None:
    """load_config builds a validated AppConfig from valid YAML."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(VALID_CONFIG))

    config = load_config(config_path)

    assert isinstance(config, AppConfig)
    assert config.hardware.device == "a100"
    assert config.example.feature_name == "demo"


def test_load_config_raises_validation_error_for_invalid_enabled_flag(tmp_path: Path) -> None:
    """load_config raises ValidationError when enabled is not a bool."""
    invalid_example = {"feature_name": "demo", "enabled": "not-a-bool"}
    invalid_config = {**VALID_CONFIG, "example": invalid_example}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(invalid_config))

    with pytest.raises(ValidationError):
        load_config(config_path)
