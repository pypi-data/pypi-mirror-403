"""FluxOS (Gravity) metrics widget showing daemon status and resources."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from textual.app import ComposeResult
from textual.reactive import var
from textual.widget import Widget

from .action_state import ActionState
from .online_indicator import OnlineIndicator
from .system_resources import SystemResources

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)


class FluxosMetrics(Widget):
    """FluxOS (Gravity) metrics widget showing service status and resources."""

    BORDER_TITLE = "Gravity Metrics"

    main_pid = var(0)
    control_pid = var(0)
    active_state = var("unknown")
    sub_state = var("unknown")
    online = var(False)

    def __init__(self) -> None:
        """Initialize FluxOS metrics widget."""
        super().__init__()
        self.online_indicator = OnlineIndicator()
        self.system_resources = SystemResources("fluxos")
        self.action_state = ActionState(None)

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield self.online_indicator
        yield self.system_resources
        yield self.action_state

    def set_state(self, main_pid: int, active_state: str, sub_state: str) -> None:
        """Set service state from SERVICE_STATE_CHANGED event (replaces polling).

        Args:
            main_pid: Process ID
            active_state: Active state (active, inactive, etc.)
            sub_state: Sub state (running, dead, etc.)
        """
        self.main_pid = main_pid
        self.active_state = active_state
        self.sub_state = sub_state

    def compute_online(self) -> bool:
        """Compute if service is online.

        Returns:
            True if service is active and running
        """
        return self.active_state == "active" and self.sub_state == "running"

    def watch_main_pid(self, old: int, new: int) -> None:
        """React to main PID changes.

        Args:
            old: Old PID
            new: New PID
        """
        if old == new:
            return

        self.online_indicator.main_pid = str(new)

        if not new:
            self.system_resources.reset()

    def watch_online(self, old: bool, new: bool) -> None:
        """React to online status changes.

        Args:
            old: Old status
            new: New status
        """
        if old == new:
            return

        self.online_indicator.online = new

    def set_action_state(
        self,
        state: Literal["Cloning", "Installing", "Waiting for Config", None],
        label: str | None = None,
    ) -> None:
        """Set the current action state.

        Args:
            state: State type
            label: Optional custom label (overrides state)
        """
        logger.info(f"Setting fluxos action state: {state}")
        action_label = label or state
        self.action_state.state = action_label
