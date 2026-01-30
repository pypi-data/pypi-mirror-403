"""Tests for configuration parsing and validation."""

from pathlib import Path

import pytest

from itermspace.config import (
    LayoutConfig,
    PaneConfig,
    TabConfig,
    WorkspaceConfig,
    _expand_path,
    load_config,
)
from itermspace.exceptions import ConfigError


class TestExpandPath:
    """Tests for path expansion."""

    def test_expand_tilde(self) -> None:
        """Test that ~ is expanded to home directory."""
        result = _expand_path("~/projects")
        assert result is not None
        assert not result.startswith("~")
        assert "projects" in result

    def test_expand_none(self) -> None:
        """Test that None is returned for None input."""
        assert _expand_path(None) is None

    def test_expand_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables are expanded."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = _expand_path("$TEST_VAR/subdir")
        assert result == "test_value/subdir"


class TestPaneConfig:
    """Tests for PaneConfig model."""

    def test_defaults(self) -> None:
        """Test default values."""
        pane = PaneConfig()
        assert pane.name is None
        assert pane.working_directory is None
        assert pane.commands == []
        assert pane.delay == 0.0

    def test_with_values(self) -> None:
        """Test creating a pane with values."""
        pane = PaneConfig(
            name="Test",
            working_directory="~/test",
            commands=["echo hello"],
            delay=1.0,
        )
        assert pane.name == "Test"
        assert pane.working_directory == "~/test"
        assert pane.commands == ["echo hello"]
        assert pane.delay == 1.0


class TestLayoutConfig:
    """Tests for LayoutConfig model."""

    def test_minimum_panes(self) -> None:
        """Test that layout requires at least 2 panes."""
        with pytest.raises(ValueError, match="at least 2 panes"):
            LayoutConfig(panes=[PaneConfig()])

    def test_valid_layout(self) -> None:
        """Test creating a valid layout."""
        layout = LayoutConfig(
            split="vertical",
            panes=[PaneConfig(name="Left"), PaneConfig(name="Right")],
        )
        assert layout.split == "vertical"
        assert len(layout.panes) == 2

    def test_nested_layout(self) -> None:
        """Test nested layout configuration."""
        inner = LayoutConfig(
            split="horizontal",
            panes=[PaneConfig(name="Top"), PaneConfig(name="Bottom")],
        )
        outer = LayoutConfig(
            split="vertical",
            panes=[PaneConfig(name="Left"), inner],
        )
        assert len(outer.panes) == 2
        assert isinstance(outer.panes[1], LayoutConfig)


class TestTabConfig:
    """Tests for TabConfig model."""

    def test_simple_tab(self) -> None:
        """Test creating a simple single-pane tab."""
        tab = TabConfig(name="Shell", commands=["ls"])
        assert tab.name == "Shell"
        assert tab.layout is None
        assert tab.commands == ["ls"]

    def test_layout_tab(self) -> None:
        """Test creating a tab with layout."""
        tab = TabConfig(
            name="Dev",
            layout=LayoutConfig(panes=[PaneConfig(name="Left"), PaneConfig(name="Right")]),
        )
        assert tab.name == "Dev"
        assert tab.layout is not None
        assert tab.commands == []

    def test_layout_and_commands_conflict(self) -> None:
        """Test that specifying both layout and commands raises error."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            TabConfig(
                name="Invalid",
                layout=LayoutConfig(panes=[PaneConfig(), PaneConfig()]),
                commands=["echo hello"],
            )


class TestWorkspaceConfig:
    """Tests for WorkspaceConfig model."""

    def test_minimum_config(self) -> None:
        """Test minimum valid configuration."""
        config = WorkspaceConfig(tabs=[TabConfig(name="Main")])
        assert config.version == "1"
        assert len(config.tabs) == 1

    def test_empty_tabs_invalid(self) -> None:
        """Test that empty tabs list is invalid."""
        with pytest.raises(ValueError):
            WorkspaceConfig(tabs=[])

    def test_working_directory_inherited_by_panes(self) -> None:
        """Test that tab's working directory is inherited by panes."""
        config = WorkspaceConfig(
            tabs=[
                TabConfig(
                    name="Test",
                    working_directory="/parent/path",
                    layout=LayoutConfig(
                        panes=[
                            PaneConfig(name="A"),
                            PaneConfig(name="B", working_directory="/custom"),
                        ]
                    ),
                )
            ],
        )
        # First pane inherits from tab
        assert config.tabs[0].layout.panes[0].working_directory == "/parent/path"
        # Second pane keeps its own
        assert config.tabs[0].layout.panes[1].working_directory == "/custom"


class TestLoadConfig:
    """Tests for loading configuration from files."""

    def test_load_simple_config(self, simple_config_path: Path) -> None:
        """Test loading the simple example config."""
        config = load_config(simple_config_path)
        assert config.name == "Two Panes"
        assert len(config.tabs) == 1
        assert config.tabs[0].name == "Main"

    def test_load_complex_config(self, complex_config_path: Path) -> None:
        """Test loading the complex example config."""
        config = load_config(complex_config_path)
        assert config.name == "Complex Workspace"
        assert len(config.tabs) == 4

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Test that missing file raises ConfigError."""
        with pytest.raises(ConfigError, match="not found"):
            load_config(tmp_path / "nonexistent.yaml")

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        """Test that invalid YAML raises ConfigError."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")
        with pytest.raises(ConfigError, match="Failed to parse YAML"):
            load_config(config_file)

    def test_invalid_config(self, tmp_path: Path) -> None:
        """Test that invalid config structure raises ConfigError."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("tabs: []")  # Empty tabs is invalid
        with pytest.raises(ConfigError, match="validation failed"):
            load_config(config_file)
