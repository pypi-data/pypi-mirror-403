"""Configuration models and YAML parsing for itermspace."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, Field, model_validator

from itermspace.exceptions import ConfigError


class PaneConfig(BaseModel):
    """Configuration for a single terminal pane."""

    name: str | None = None
    working_directory: str | None = None
    commands: list[str] = Field(default_factory=list)
    delay: float = 0.0


class LayoutConfig(BaseModel):
    """Configuration for a pane layout (can be nested)."""

    split: Literal["vertical", "horizontal"] = "vertical"
    panes: list[PaneConfig | LayoutConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_panes(self) -> Self:
        """Ensure at least 2 panes if split is specified."""
        if len(self.panes) < 2:
            raise ValueError("Layout must have at least 2 panes for splitting")
        return self


class TabConfig(BaseModel):
    """Configuration for a single terminal tab."""

    name: str
    working_directory: str | None = None
    layout: LayoutConfig | None = None
    commands: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_tab(self) -> Self:
        """Validate that either layout or commands (or neither) is specified."""
        if self.layout and self.commands:
            raise ValueError(
                f"Tab '{self.name}': Cannot specify both 'layout' and 'commands'. "
                "Use layout.panes[0].commands for the first pane."
            )
        return self

    @model_validator(mode="after")
    def apply_working_directory_to_panes(self) -> Self:
        """Apply tab's working directory to panes that don't have one."""
        if self.layout and self.working_directory:
            _walk_layout(
                self.layout,
                lambda p: _set_default_dir(p, self.working_directory),  # type: ignore[arg-type]
            )
        return self


class WorkspaceConfig(BaseModel):
    """Root configuration for a workspace."""

    version: str = "1"
    name: str | None = None
    tabs: list[TabConfig] = Field(min_length=1)


def _walk_layout(layout: LayoutConfig, fn: Callable[[PaneConfig], None]) -> None:
    """Recursively apply a function to all panes in a layout."""
    for pane in layout.panes:
        if isinstance(pane, LayoutConfig):
            _walk_layout(pane, fn)
        else:
            fn(pane)


def _set_default_dir(pane: PaneConfig, parent_dir: str) -> None:
    """Set working directory if not already set."""
    if pane.working_directory is None:
        pane.working_directory = parent_dir


def _expand_path(path: str | None) -> str | None:
    """Expand ~ and environment variables in a path."""
    return os.path.expandvars(os.path.expanduser(path)) if path else None


def load_config(path: Path) -> WorkspaceConfig:
    """Load and validate a workspace configuration from a YAML file."""
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError("Configuration must be a YAML mapping (dictionary)")

    try:
        config = WorkspaceConfig.model_validate(data)
    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {e}") from e

    # Expand paths after validation
    for tab in config.tabs:
        tab.working_directory = _expand_path(tab.working_directory)
        if tab.layout:
            _walk_layout(
                tab.layout,
                lambda p: setattr(p, "working_directory", _expand_path(p.working_directory)),
            )

    return config
