"""Layout engine for converting configuration to iTerm2 split operations."""

from __future__ import annotations

from dataclasses import dataclass, field

from itermspace.config import LayoutConfig, PaneConfig, TabConfig


@dataclass
class SplitOperation:
    """A split operation: source pane index and direction."""

    source_pane_index: int
    vertical: bool


@dataclass
class PaneSetup:
    """Configuration for a pane after splits."""

    creation_order: int
    name: str | None = None
    working_directory: str | None = None
    commands: list[str] = field(default_factory=list)
    delay: float = 0.0


@dataclass
class TabLayout:
    """Layout plan for a tab: splits to perform and pane configurations."""

    tab_name: str
    splits: list[SplitOperation]
    panes: list[PaneSetup]


def plan_tab_layout(tab: TabConfig) -> TabLayout:
    """Convert a tab configuration into a layout plan."""
    splits: list[SplitOperation] = []
    panes: list[PaneSetup] = []

    if tab.layout is None:
        panes.append(PaneSetup(0, tab.name, tab.working_directory, tab.commands))
    else:
        _plan_recursive(tab.layout, 0, splits, panes, [1], tab.working_directory)

    return TabLayout(tab.name, splits, panes)


def _plan_recursive(
    layout: LayoutConfig,
    source_pane: int,
    splits: list[SplitOperation],
    panes: list[PaneSetup],
    counter: list[int],
    parent_dir: str | None,
) -> None:
    """Recursively plan splits.

    Splits are chained from the last created pane to preserve order.
    For 3 panes: split 0→1, then split 1→2, giving order [0, 1, 2].
    """
    is_vertical = layout.split == "vertical"

    # Create all regions by chaining splits
    region_panes = [source_pane]
    last_pane = source_pane
    for _ in range(len(layout.panes) - 1):
        splits.append(SplitOperation(last_pane, is_vertical))
        new_pane = counter[0]
        region_panes.append(new_pane)
        last_pane = new_pane
        counter[0] += 1

    # Process each child
    for i, item in enumerate(layout.panes):
        if isinstance(item, PaneConfig):
            panes.append(
                PaneSetup(
                    region_panes[i],
                    item.name,
                    item.working_directory or parent_dir,
                    item.commands,
                    item.delay,
                )
            )
        else:
            _plan_recursive(item, region_panes[i], splits, panes, counter, parent_dir)
