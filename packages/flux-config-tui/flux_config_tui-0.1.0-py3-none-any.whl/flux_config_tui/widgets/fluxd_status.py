"""FluxD status widget for displaying node status."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import var
from textual.widgets import Label

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)


class FluxdStatus(Horizontal):
    """Widget showing FluxD node status from getfluxnodestatus.

    Event-driven: listens for FLUXD_STATUS_CHANGED events from daemon.
    Daemon polls getfluxnodestatus when blockchain topic has subscribers.
    """

    status = var("Unknown")

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield Label("Status: ")
        yield Label(self.status, id="status-label")

    def watch_status(self, old: str, new: str) -> None:
        """React to status changes.

        Args:
            old: Previous status (lowercase)
            new: New status (lowercase)
        """
        if old == new:
            return

        try:
            display_value = new.title() if new and new != "Unknown" else new
            self.query_one("#status-label", Label).update(display_value)
        except NoMatches as e:
            logger.warning("Failed to update status label: %s", e)
