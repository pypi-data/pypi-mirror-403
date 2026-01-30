"""ASCII preview rendering for layout visualization."""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from itermspace.layout import TabLayout


@dataclass
class _Region:
    """A rectangular region in the grid."""

    x: int
    y: int
    w: int
    h: int
    pane_id: int
    name: str | None = None


def format_layout_preview(tab_layout: TabLayout) -> str:
    """Format a tab layout as ASCII grid preview."""
    lines = [f"Tab: {tab_layout.tab_name}"]
    grid = render_grid(tab_layout)
    if grid:
        lines.extend(f"  {line}" for line in grid.split("\n"))
    return "\n".join(lines)


def render_grid(layout: TabLayout, width: int = 0, height: int = 0) -> str:
    """Render layout as ASCII grid."""
    if not layout.panes:
        return ""

    if width <= 0 or height <= 0:
        term = shutil.get_terminal_size((80, 24))
        width = max(40, term.columns - 6)
        height = max(7, min(20, width // 5))

    regions = _build_regions(layout)
    _scale_to_chars(regions, width, height, {p.creation_order: p.name for p in layout.panes})

    grid = [[" "] * width for _ in range(height)]
    _draw_borders(grid, regions, width, height)
    _draw_labels(grid, regions, width)

    return "\n".join("".join(row) for row in grid)


def _build_regions(layout: TabLayout) -> dict[int, _Region]:
    """Build regions by simulating iTerm2's equal redistribution."""
    scale = 1000
    regions: dict[int, _Region] = {0: _Region(0, 0, scale, scale, 0)}

    i = 0
    while i < len(layout.splits):
        split = layout.splits[i]
        src = regions.get(split.source_pane_index)
        if not src:
            i += 1
            continue

        # Collect chained splits (same direction, consecutive sources)
        chain = [split]
        j = i + 1
        expected_source = max(regions.keys()) + 1
        while j < len(layout.splits):
            next_split = layout.splits[j]
            same_direction = next_split.vertical == split.vertical
            if next_split.source_pane_index == expected_source and same_direction:
                chain.append(next_split)
                expected_source += 1
                j += 1
            else:
                break

        n_panes = len(chain) + 1
        _distribute_space(regions, src, chain, split.vertical, n_panes)
        i = j

    return regions


def _distribute_space(
    regions: dict[int, _Region],
    src: _Region,
    chain: list,
    vertical: bool,
    n_panes: int,
) -> None:
    """Distribute space equally among sibling panes."""
    if vertical:
        each = src.w // n_panes
        for k, _ in enumerate(chain):
            new_id = max(regions.keys()) + 1
            new_x = src.x + (k + 1) * each
            new_w = each if k < len(chain) - 1 else (src.x + src.w - new_x)
            regions[new_id] = _Region(new_x, src.y, new_w, src.h, new_id)
        src.w = each
    else:
        each = src.h // n_panes
        for k, _ in enumerate(chain):
            new_id = max(regions.keys()) + 1
            new_y = src.y + (k + 1) * each
            new_h = each if k < len(chain) - 1 else (src.y + src.h - new_y)
            regions[new_id] = _Region(src.x, new_y, src.w, new_h, new_id)
        src.h = each


def _scale_to_chars(
    regions: dict[int, _Region],
    width: int,
    height: int,
    pane_names: dict[int, str | None],
) -> None:
    """Convert scaled coordinates to character coordinates."""
    scale = 1000
    for r in regions.values():
        ex, ey = r.x + r.w, r.y + r.h
        r.x = r.x * (width - 1) // scale
        r.y = r.y * (height - 1) // scale
        r.w = (width - 1 if ex == scale else ex * (width - 1) // scale) - r.x + 1
        r.h = (height - 1 if ey == scale else ey * (height - 1) // scale) - r.y + 1
        r.w, r.h = max(r.w, 5), max(r.h, 3)
        r.name = pane_names.get(r.pane_id)


def _draw_borders(
    grid: list[list[str]],
    regions: dict[int, _Region],
    w: int,
    h: int,
) -> None:
    """Draw all borders including outer frame."""
    # Outer border
    for x in range(w):
        grid[0][x] = grid[h - 1][x] = "─"
    for y in range(h):
        grid[y][0] = grid[y][w - 1] = "│"
    grid[0][0], grid[0][w - 1], grid[h - 1][0], grid[h - 1][w - 1] = "┌", "┐", "└", "┘"

    # Region borders
    for r in regions.values():
        rx, by = r.x + r.w - 1, r.y + r.h - 1
        if rx < w - 1:
            for y in range(r.y, min(by + 1, h)):
                if grid[y][rx] == " ":
                    grid[y][rx] = "│"
        if by < h - 1:
            for x in range(r.x, min(rx + 1, w)):
                if grid[by][x] == " ":
                    grid[by][x] = "─"

    # Fix corners
    _fix_corners(grid, w, h)


def _fix_corners(grid: list[list[str]], w: int, h: int) -> None:
    """Fix corner characters based on neighbors."""
    borders = {"─", "│", "┌", "┐", "└", "┘", "├", "┤", "┬", "┴", "┼"}
    horiz = {"─", "┬", "┴", "┼", "├", "┤", "┌", "┐", "└", "┘"}
    vert = {"│", "┬", "┴", "┼", "├", "┤", "┌", "┐", "└", "┘"}

    corner_map = {
        (True, True, True, True): "┼",
        (False, True, False, True): "┌",
        (False, True, True, False): "┐",
        (True, False, False, True): "└",
        (True, False, True, False): "┘",
        (True, True, False, True): "├",
        (True, True, True, False): "┤",
        (False, True, True, True): "┬",
        (True, False, True, True): "┴",
    }

    for y in range(h):
        for x in range(w):
            if grid[y][x] not in borders:
                continue

            u = grid[y - 1][x] in vert if y > 0 else False
            d = grid[y + 1][x] in vert if y < h - 1 else False
            lf = grid[y][x - 1] in horiz if x > 0 else False
            rt = grid[y][x + 1] in horiz if x < w - 1 else False

            key = (u, d, lf, rt)
            if key in corner_map:
                grid[y][x] = corner_map[key]
            elif lf and rt:
                grid[y][x] = "─"
            elif u and d:
                grid[y][x] = "│"


def _draw_labels(grid: list[list[str]], regions: dict[int, _Region], total_w: int) -> None:
    """Draw labels centered in each region."""
    for r in regions.values():
        max_w = r.w - 2
        if max_w < 3:
            continue

        name = r.name or "Pane"
        suffix = f" ({r.pane_id})"
        label = f"{name}{suffix}"

        if len(label) > max_w:
            avail = max_w - len(suffix) - 1
            label = f"{name[:avail]}…{suffix}" if avail >= 2 else f"{name[: max_w - 1]}…"

        cy, cx = r.y + r.h // 2, r.x + (r.w - len(label)) // 2
        if r.y < cy < r.y + r.h - 1:
            for i, ch in enumerate(label):
                if r.x < cx + i < r.x + r.w - 1 < total_w:
                    grid[cy][cx + i] = ch
