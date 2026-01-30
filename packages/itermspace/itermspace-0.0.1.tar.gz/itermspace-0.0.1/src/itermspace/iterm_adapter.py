"""iTerm2 API adapter for workspace management."""

from __future__ import annotations

import asyncio
import shlex

import iterm2

from itermspace.config import WorkspaceConfig
from itermspace.exceptions import ITerm2Error
from itermspace.layout import PaneSetup, TabLayout, plan_tab_layout


class ITerm2Adapter:
    """Adapter for interacting with iTerm2 via its Python API."""

    def __init__(self, connection: iterm2.Connection, app: iterm2.App) -> None:
        self.connection = connection
        self.app = app

    async def create_workspace(self, config: WorkspaceConfig) -> None:
        """Create an entire workspace from configuration."""
        window = await self._ensure_window()

        for tab_config in config.tabs:
            tab_layout = plan_tab_layout(tab_config)
            tab = await window.async_create_tab()
            if tab is None:
                raise ITerm2Error("Failed to create new tab")
            await self._setup_tab(tab, tab_layout)

    async def _ensure_window(self) -> iterm2.Window:
        """Get current window or create a new one."""
        window = self.app.current_terminal_window
        if window is None:
            window = await iterm2.Window.async_create(self.connection)
        if window is None:
            raise ITerm2Error("Failed to get or create iTerm2 window")
        return window

    async def _setup_tab(self, tab: iterm2.Tab, layout: TabLayout) -> None:
        """Set up a single tab with its panes."""
        await tab.async_set_title(layout.tab_name)

        session = tab.current_session
        if session is None:
            raise ITerm2Error(f"No session in tab '{layout.tab_name}'")

        sessions = await self._execute_splits(session, layout)

        for pane in layout.panes:
            if pane.creation_order < len(sessions):
                await self._configure_pane(sessions[pane.creation_order], pane)

    async def _execute_splits(
        self,
        initial_session: iterm2.Session,
        layout: TabLayout,
    ) -> list[iterm2.Session]:
        """Execute split operations and return all sessions in creation order."""
        sessions: list[iterm2.Session] = [initial_session]

        for split in layout.splits:
            source = sessions[split.source_pane_index]
            new_session = await source.async_split_pane(vertical=split.vertical)
            sessions.append(new_session)

        return sessions

    async def _configure_pane(self, session: iterm2.Session, pane: PaneSetup) -> None:
        """Configure a single pane with working directory and commands."""
        if pane.working_directory:
            await session.async_send_text(f"cd {shlex.quote(pane.working_directory)} && clear\n")
            await asyncio.sleep(0.1)

        if pane.delay > 0:
            await asyncio.sleep(pane.delay)

        for cmd in pane.commands:
            await session.async_send_text(f"{cmd}\n")
            await asyncio.sleep(0.05)
