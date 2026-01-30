"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def examples_dir() -> Path:
    """Return the path to the examples directory."""
    return Path(__file__).parent.parent / "examples"


@pytest.fixture
def simple_config_path(examples_dir: Path) -> Path:
    """Return the path to the simple example config."""
    return examples_dir / "01-basic" / "two-panes.yaml"


@pytest.fixture
def complex_config_path(examples_dir: Path) -> Path:
    """Return the path to the complex example config."""
    return examples_dir / "04-advanced" / "complex-workspace.yaml"
