"""Online indicator widget showing PID and online status."""

from __future__ import annotations

import logging

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import var
from textual.widgets import Label

logger = logging.getLogger(__name__)


class OnlineIndicator(Horizontal):
    """Widget showing process PID and online status."""

    # Unicode Character "●" (U+25CF)
    states = {
        True: Text("\U000025cf", style="bold green"),
        False: "\U000025cf",
    }

    online = var(False)
    main_pid = var("0")

    def __init__(
        self,
        initial_online_state: bool = False,
        initial_main_pid: str = "0",
    ) -> None:
        """Initialize online indicator.

        Args:
            initial_online_state: Initial online state
            initial_main_pid: Initial main PID
        """
        super().__init__()
        self._online = initial_online_state
        self._main_pid = initial_main_pid

    def on_mount(self) -> None:
        """Set initial values when mounted."""
        self.online = self._online
        self.main_pid = self._main_pid

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield Label("MainPid: ")
        yield Label(self.main_pid, id="pid-label")
        yield Label("Online: ")
        yield Label(self.states[self._online], id="state-label")

    def watch_online(self, old: bool, new: bool) -> None:
        """React to online status changes.

        Args:
            old: Old online state
            new: New online state
        """
        if old == new:
            return

        self._online = new

        if self.is_mounted:
            try:
                self.query_one("#state-label", Label).update(self.states[new])
            except NoMatches as e:
                logger.warning("Failed to update online state label: %s", e)

    def watch_main_pid(self, old: str, new: str) -> None:
        """React to PID changes.

        Args:
            old: Old PID
            new: New PID
        """
        if old == new:
            return

        self._main_pid = new

        if self.is_mounted:
            try:
                self.query_one("#pid-label", Label).update(new)
            except NoMatches as e:
                logger.warning("Failed to update PID label: %s", e)
