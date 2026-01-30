"""FluxBenchD metrics widget showing daemon status and resources."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.message import Message
from textual.reactive import var
from textual.widget import Widget

from .benchmark_status import BenchmarkStatus
from .online_indicator import OnlineIndicator
from .system_resources import SystemResources

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)


class FluxbenchdMetrics(Widget, can_focus=True):
    """FluxBenchD metrics widget showing service status and resources."""

    class ShowRpcModal(Message):
        """Posted when user requests to see FluxBenchD RPC data."""
        pass

    BORDER_TITLE = "Fluxbenchd Metrics"

    BINDINGS = [
        Binding("enter", "show_modal", "Show RPC Data", show=False),
    ]

    main_pid = var(0)
    control_pid = var(0)
    active_state = var("unknown")
    sub_state = var("unknown")
    online = var(False)

    def __init__(self) -> None:
        """Initialize FluxBenchD metrics widget."""
        super().__init__()
        self.online_indicator = OnlineIndicator()
        self.system_resources = SystemResources("fluxbenchd")
        self.benchmark_status = BenchmarkStatus()

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield self.online_indicator
        yield self.system_resources
        yield self.benchmark_status

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

        if not new:
            self.benchmark_status.state = "Unknown"

    def action_show_modal(self) -> None:
        """Action to show the modal."""
        self.post_message(self.ShowRpcModal())

    def on_click(self, event: Click) -> None:
        """Handle click events."""
        self.post_message(self.ShowRpcModal())
