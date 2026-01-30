"""Tests for layout engine."""

from itermspace.config import LayoutConfig, PaneConfig, TabConfig
from itermspace.layout import PaneSetup, SplitOperation, TabLayout, plan_tab_layout
from itermspace.preview import format_layout_preview


class TestPlanTabLayout:
    """Tests for plan_tab_layout function."""

    def test_single_pane_tab(self) -> None:
        """Test layout planning for a simple single-pane tab."""
        tab = TabConfig(
            name="Shell",
            working_directory="/home/user",
            commands=["echo hello"],
        )
        layout = plan_tab_layout(tab)

        assert layout.tab_name == "Shell"
        assert len(layout.splits) == 0
        assert len(layout.panes) == 1
        assert layout.panes[0].working_directory == "/home/user"
        assert layout.panes[0].commands == ["echo hello"]

    def test_two_pane_vertical_split(self) -> None:
        """Test layout with two panes (vertical split)."""
        tab = TabConfig(
            name="Dev",
            layout=LayoutConfig(
                split="vertical",
                panes=[
                    PaneConfig(name="Left", commands=["left cmd"]),
                    PaneConfig(name="Right", commands=["right cmd"]),
                ],
            ),
        )
        layout = plan_tab_layout(tab)

        assert layout.tab_name == "Dev"
        assert len(layout.panes) == 2
        assert len(layout.splits) == 1

        # First pane (no split needed)
        assert layout.panes[0].name == "Left"
        assert layout.panes[0].creation_order == 0

        # Second pane (requires split)
        assert layout.panes[1].name == "Right"
        assert layout.panes[1].creation_order == 1

        # Split operation
        assert layout.splits[0].source_pane_index == 0
        assert layout.splits[0].vertical is True

    def test_two_pane_horizontal_split(self) -> None:
        """Test layout with two panes (horizontal split)."""
        tab = TabConfig(
            name="Dev",
            layout=LayoutConfig(
                split="horizontal",
                panes=[
                    PaneConfig(name="Top"),
                    PaneConfig(name="Bottom"),
                ],
            ),
        )
        layout = plan_tab_layout(tab)

        assert len(layout.splits) == 1
        assert layout.splits[0].vertical is False

    def test_three_pane_layout(self) -> None:
        """Test layout with three panes."""
        tab = TabConfig(
            name="Triple",
            layout=LayoutConfig(
                split="vertical",
                panes=[
                    PaneConfig(name="Left"),
                    PaneConfig(name="Center"),
                    PaneConfig(name="Right"),
                ],
            ),
        )
        layout = plan_tab_layout(tab)

        assert len(layout.panes) == 3
        assert len(layout.splits) == 2

        # Splits are chained: 0→1, then 1→2 to preserve order
        assert layout.splits[0].source_pane_index == 0
        assert layout.splits[1].source_pane_index == 1

    def test_nested_layout(self) -> None:
        """Test nested layout (e.g., IDE-style with sidebar and split main area)."""
        tab = TabConfig(
            name="IDE",
            layout=LayoutConfig(
                split="vertical",
                panes=[
                    PaneConfig(name="Sidebar"),
                    LayoutConfig(
                        split="horizontal",
                        panes=[
                            PaneConfig(name="Editor"),
                            PaneConfig(name="Terminal"),
                        ],
                    ),
                ],
            ),
        )
        layout = plan_tab_layout(tab)

        assert len(layout.panes) == 3
        assert len(layout.splits) == 2

        # Pane names in creation order
        assert layout.panes[0].name == "Sidebar"
        assert layout.panes[1].name == "Editor"
        assert layout.panes[2].name == "Terminal"

    def test_working_directory_inheritance(self) -> None:
        """Test that working directory is inherited from tab."""
        tab = TabConfig(
            name="Test",
            working_directory="/parent/dir",
            layout=LayoutConfig(
                panes=[
                    PaneConfig(name="A"),  # Should inherit /parent/dir
                    PaneConfig(name="B", working_directory="/custom"),  # Custom
                ],
            ),
        )
        layout = plan_tab_layout(tab)

        assert layout.panes[0].working_directory == "/parent/dir"
        assert layout.panes[1].working_directory == "/custom"


class TestFormatLayoutPreview:
    """Tests for format_layout_preview function."""

    def test_simple_preview(self) -> None:
        """Test preview formatting for a simple layout."""
        layout = TabLayout(
            tab_name="Test",
            splits=[],
            panes=[
                PaneSetup(
                    creation_order=0,
                    name="Main",
                    working_directory="/home/user",
                    commands=["echo hello"],
                )
            ],
        )
        preview = format_layout_preview(layout)

        assert "Tab: Test" in preview
        assert "Main (0)" in preview  # Grid shows name and pane number

    def test_preview_with_splits(self) -> None:
        """Test preview formatting with split operations."""
        layout = TabLayout(
            tab_name="Dev",
            splits=[
                SplitOperation(source_pane_index=0, vertical=True),
            ],
            panes=[
                PaneSetup(creation_order=0, name="Left"),
                PaneSetup(creation_order=1, name="Right"),
            ],
        )
        preview = format_layout_preview(layout)

        assert "Tab: Dev" in preview
        assert "Left (0)" in preview
        assert "Right (1)" in preview
