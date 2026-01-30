"""Command-line interface for itermspace."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from itermspace import __version__
from itermspace.config import LayoutConfig, TabConfig, WorkspaceConfig, load_config
from itermspace.exceptions import ConfigError, ITerm2Error
from itermspace.layout import plan_tab_layout
from itermspace.preview import format_layout_preview


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="itermspace",
        description="Launch iTerm2 workspaces from YAML configuration",
    )
    parser.add_argument(
        "configs",
        type=Path,
        nargs="+",
        metavar="CONFIG",
        help="Path(s) to workspace YAML configuration file(s) or directories containing them",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without executing",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate config file(s) without launching",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _workspace_name(config: WorkspaceConfig, path: Path) -> str:
    """Get display name for a workspace."""
    return config.name or path.stem


def _count_panes(tab: TabConfig) -> int:
    """Count the number of panes in a tab configuration."""
    if tab.layout is None:
        return 1

    def count(layout: LayoutConfig) -> int:
        return sum(count(p) if isinstance(p, LayoutConfig) else 1 for p in layout.panes)

    return count(tab.layout)


def _print_dry_run(config: WorkspaceConfig, path: Path) -> None:
    """Print a dry-run preview of the workspace."""
    print(f"Config: {path}")
    print(f"Workspace: {config.name or '(unnamed)'}")
    print(f"Version: {config.version}")
    print(f"Tabs: {len(config.tabs)}")
    print()
    for tab in config.tabs:
        print(format_layout_preview(plan_tab_layout(tab)))
        print()


def _print_validation(config: WorkspaceConfig, path: Path) -> None:
    """Print validation summary."""
    print(f"Configuration is valid: {path}")
    print(f"  Workspace: {config.name or '(unnamed)'}")
    print(f"  Tabs: {len(config.tabs)}")
    for tab in config.tabs:
        print(f"    - {tab.name}: {_count_panes(tab)} pane(s)")


def _run_sync(configs: list[WorkspaceConfig]) -> None:
    """Run the workspace launch synchronously."""
    import iterm2

    from itermspace.iterm_adapter import ITerm2Adapter

    async def _launch(connection: iterm2.Connection) -> None:
        app = await iterm2.async_get_app(connection)
        if app is None:
            raise ITerm2Error("Failed to get iTerm2 app instance")
        adapter = ITerm2Adapter(connection, app)
        for config in configs:
            await adapter.create_workspace(config)

    try:
        iterm2.run_until_complete(_launch)
    except Exception as e:
        raise ITerm2Error(
            f"Failed to connect to iTerm2. Make sure:\n"
            f"  1. iTerm2 is running\n"
            f"  2. Python API is enabled (Preferences > General > Magic > Enable Python API)\n"
            f"Error: {e}"
        ) from e


def _load_configs(paths: list[Path]) -> list[tuple[Path, WorkspaceConfig]]:
    """Resolve and load configs, expanding directories and skipping invalid files."""
    result = []
    for path in paths:
        files = (
            sorted(path.glob("*.yaml")) + sorted(path.glob("*.yml")) if path.is_dir() else [path]
        )
        for f in files:
            try:
                result.append((f, load_config(f)))
            except ConfigError as e:
                print(f"\n⚠ Skipping {f}\n  {e}\n", file=sys.stderr)
    return result


def main() -> int:
    """Main entry point for the CLI."""
    args = create_parser().parse_args()

    try:
        configs = _load_configs(args.configs)
        if not configs:
            print("No valid configuration files found", file=sys.stderr)
            return 1

        if args.validate:
            for i, (path, config) in enumerate(configs):
                if i > 0:
                    print()
                _print_validation(config, path)
            return 0

        if args.dry_run:
            for i, (path, config) in enumerate(configs):
                if i > 0:
                    print("-" * 40 + "\n")
                _print_dry_run(config, path)
            return 0

        _run_sync([c for _, c in configs])

        if len(configs) == 1:
            path, config = configs[0]
            print(f"Workspace '{_workspace_name(config, path)}' launched successfully!")
        else:
            print(f"Launched {len(configs)} workspaces successfully!")
            for path, config in configs:
                print(f"  - {_workspace_name(config, path)}")
        return 0

    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except ITerm2Error as e:
        print(f"iTerm2 error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
