"""Action state widget showing current operation state."""

from __future__ import annotations

import logging

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import var
from textual.widgets import Label

logger = logging.getLogger(__name__)


class ActionState(Horizontal):
    """Widget showing current action/operation state."""

    state: var[str | None] = var(None)

    def __init__(self, initial_state: str | None = None) -> None:
        """Initialize action state widget.

        Args:
            initial_state: Initial state text
        """
        super().__init__()
        self.visible = bool(initial_state)
        self._state = initial_state

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        state_label = self._state or ""
        yield Label("Install State: ")
        yield Label(state_label, id="state_label")

    def on_mount(self) -> None:
        """Set initial state when mounted."""
        self.state = self._state

    def watch_state(self, old: str | None, new: str | None) -> None:
        """React to state changes.

        Args:
            old: Old state
            new: New state
        """
        if old == new:
            return

        # Hide widget if no state to display
        self.visible = bool(new)
        self._state = new

        if self.is_mounted:
            label = new or ""
            try:
                self.query_one("#state_label", Label).update(label)
            except NoMatches as e:
                logger.warning("Failed to update state label: %s", e)
