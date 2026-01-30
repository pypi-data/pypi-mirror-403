"""RPC status indicator widget."""

from __future__ import annotations

import logging

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import var
from textual.widgets import Label

logger = logging.getLogger(__name__)


class RpcIndicator(Horizontal):
    """Widget showing RPC online status."""

    states = {
        True: Text("\U000025cf", style="bold green"),
        False: "\U000025cf",
    }

    rpc_online = var(False)

    def __init__(self, initial_online_state: bool = False) -> None:
        """Initialize RPC indicator.

        Args:
            initial_online_state: Initial RPC online state
        """
        super().__init__()
        self._rpc_online = initial_online_state

    def on_mount(self) -> None:
        """Set initial values when mounted."""
        self.rpc_online = self._rpc_online

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield Label("RPC: ")
        yield Label(self.states[self._rpc_online], id="rpc-state")

    def watch_rpc_online(self, old: bool, new: bool) -> None:
        """React to RPC online status changes.

        Args:
            old: Old RPC online state
            new: New RPC online state
        """
        if old == new:
            return

        self._rpc_online = new

        if self.is_mounted:
            try:
                self.query_one("#rpc-state", Label).update(self.states[new])
            except NoMatches as e:
                logger.warning("Failed to update RPC state label: %s", e)
