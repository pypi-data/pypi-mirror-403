"""Reconfiguration screen for TUI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, Label

if TYPE_CHECKING:
    from flux_config_tui.client import BackendClient

logger = logging.getLogger(__name__)


class ReconfigureScreen(ModalScreen[str]):
    """Screen to prompt user for reconfiguration choice."""

    DEFAULT_STYLES = """
    ReconfigureScreen {
        align: center middle;
    }

    ReconfigureScreen > Container {
        width: 80;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 2;
    }

    ReconfigureScreen Label {
        width: 100%;
        content-align: left top;
        padding: 1 0;
    }

    ReconfigureScreen Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    ReconfigureScreen Button {
        margin: 0 1;
    }
    """

    def __init__(self, backend_client: BackendClient) -> None:
        """Initialize the reconfigure screen.

        Args:
            backend_client: Backend client for RPC calls
        """
        super().__init__()
        self.backend_client = backend_client

    def compose(self) -> ComposeResult:
        """Compose the reconfigure screen."""
        with Container():
            yield Label(
                "You can reconfigure now, or stop Flux services and do it later.\n\n"
                "If you stop services, fluxd will remain running to keep the chain fresh.\n\n"
                "You can access the launch screen from the metrics screen if you decide "
                "to do it later."
            )

            with Horizontal():
                yield Button("Set up now", id="now", variant="primary")
                yield Button("I'll do it later", id="later")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Apply custom styles
        self.styles.css = self.DEFAULT_STYLES  # type: ignore[misc]

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            # User cancelled
            self.dismiss("cancel")

        elif event.button.id in ("now", "later"):
            # Set reconfiguration mode via backend
            mode: Literal["now", "later"] = event.button.id  # type: ignore[assignment]

            try:
                result = await self.backend_client.call_rpc(
                    "reconfigure.set_mode",
                    {"mode": mode},
                )

                if result.get("success"):
                    logger.info(f"Reconfiguration mode set to: {mode}")
                    self.dismiss(mode)
                else:
                    error_msg = result.get("message", "Unknown error")
                    logger.error(f"Failed to set reconfiguration mode: {error_msg}")
                    self.notify(
                        f"Failed to set reconfiguration mode: {error_msg}",
                        severity="error",
                    )
                    self.dismiss("cancel")

            except Exception as e:
                logger.error(f"Error setting reconfiguration mode: {e}", exc_info=True)
                self.notify(f"Error: {e}", severity="error")
                self.dismiss("cancel")

    def on_key(self, event: Key) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss("cancel")
