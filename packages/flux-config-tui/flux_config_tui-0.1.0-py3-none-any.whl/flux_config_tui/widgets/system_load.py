"""System load widget - displays uptime and load averages."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)


class SystemLoad(Horizontal):
    """Widget that displays system load average and uptime."""

    def __init__(self) -> None:
        """Initialize the system load widget."""
        super().__init__()
        self.initial_value = ""

    @work(name="start_monitoring", exclusive=True)
    async def start_monitoring(self) -> None:
        """Monitor system load in background and update display."""
        while True:
            try:
                app: FluxConfigApp = self.app  # type: ignore

                if not app.backend_client or not app.backend_connected.is_set():
                    await asyncio.sleep(5)
                    continue

                # Call backend RPC to get system load
                response = await app.backend_client.call_method("metrics.get_system_load", {})

                if response.error:
                    logger.error(f"Failed to get system load: {response.error.message}")
                    result = "Load: unavailable"
                elif response.result and response.result.get("success"):
                    # Use the uptime text which includes load averages
                    result = response.result.get("uptime_text", "")
                else:
                    result = "Load: error"

                if self.is_mounted:
                    self.query_one("#load-label", Label).update(result)
                else:
                    self.initial_value = result

            except Exception as e:
                logger.error(f"Error getting system load: {e}")
                if self.is_mounted:
                    self.query_one("#load-label", Label).update("Load: error")

            await asyncio.sleep(5)

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label(self.initial_value, id="load-label")

    def on_mount(self) -> None:
        """Start monitoring when mounted."""
        self.start_monitoring()
