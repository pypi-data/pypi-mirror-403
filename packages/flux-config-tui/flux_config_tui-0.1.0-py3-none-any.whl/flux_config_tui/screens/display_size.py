"""Display size configuration screen for TUI."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Select

if TYPE_CHECKING:
    from flux_config_tui.client import BackendClient

logger = logging.getLogger(__name__)


class DisplaySizeScreen(ModalScreen[bool]):
    """Screen for changing display resolution."""

    DEFAULT_STYLES = """
    DisplaySizeScreen {
        align: center middle;
    }

    DisplaySizeScreen > Vertical {
        width: 80;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #dialog {
        width: 100%;
        content-align: center middle;
        padding: 1 0;
    }

    #display-size-container {
        width: 100%;
        height: 3;
        align: center middle;
        padding: 1 0;
    }

    .text-label {
        width: auto;
        padding: 0 1;
    }

    #resolution {
        width: 20;
    }

    #button-container {
        width: 100%;
        height: 3;
        align: center middle;
        padding: 1 0;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        backend_client: BackendClient,
        current_resolution: str,
        available_resolutions: list[str],
    ) -> None:
        """Initialize the display size screen.

        Args:
            backend_client: Backend client for RPC calls
            current_resolution: Current display resolution
            available_resolutions: List of available resolutions
        """
        super().__init__()
        self.backend_client = backend_client
        self.current_resolution = current_resolution
        self.available_resolutions = available_resolutions
        self.pending_resolution: str | None = None
        self.previous_resolution: str | None = None
        self._confirmation_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        """Compose the display size screen."""
        options = [(res, res) for res in self.available_resolutions]

        with Vertical():
            yield Label(
                "Warning! This is experimental. Choosing a larger size WILL cause "
                "higher CPU usage. This is mainly intended for bare metal machines "
                "for the content to fit the screen.\n\n"
                "You must select 'Confirm' within 10 seconds to keep the selected resolution",
                id="dialog",
            )
            with Horizontal(id="display-size-container"):
                yield Label("Resolution:", classes="text-label")
                yield Select(
                    options,
                    allow_blank=False,
                    value=self.current_resolution,
                    id="resolution",
                )
            with Horizontal(id="button-container"):
                yield Button("Back", id="back")
                yield Button("Set", id="set", disabled=True)
                yield Button("Confirm", id="confirm", disabled=True)

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Apply custom styles
        self.styles.css = self.DEFAULT_STYLES  # type: ignore[misc]

    def on_unmount(self) -> None:
        """Called when screen is unmounted."""
        # Cancel any pending confirmation task
        if self._confirmation_task and not self._confirmation_task.done():
            self._confirmation_task.cancel()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle resolution selection change."""
        no_change = self.current_resolution == event.value
        confirm_enabled = not self.query_one("#confirm", Button).disabled

        # Enable/disable Set button based on selection
        self.query_one("#set", Button).disabled = no_change or confirm_enabled

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "back":
            # Cancel and return
            self.dismiss(False)

        elif event.button.id == "set":
            # Apply the selected resolution
            await self._apply_resolution()

        elif event.button.id == "confirm":
            # Confirm the resolution change
            self._confirm_resolution()

    async def _apply_resolution(self) -> None:
        """Apply the selected resolution."""
        select = self.query_one("#resolution", Select)
        new_resolution = str(select.value)

        if new_resolution == self.current_resolution:
            return

        logger.info(f"Setting resolution to {new_resolution}")

        # Disable buttons during operation
        self.query_one("#set", Button).disabled = True
        self.query_one("#back", Button).disabled = True

        try:
            # Call backend to set resolution
            result = await self.backend_client.call_rpc(
                "display.set_resolution",
                {"resolution": new_resolution},
            )

            if not result.get("success"):
                error_msg = result.get("message", "Unknown error")
                self.notify(f"Failed to set resolution: {error_msg}", severity="error")
                logger.error(f"Failed to set resolution: {error_msg}")

                # Re-enable buttons
                self.query_one("#set", Button).disabled = False
                self.query_one("#back", Button).disabled = False
                return

            # Track previous resolution for rollback
            self.previous_resolution = result.get("previous", self.current_resolution)
            self.pending_resolution = new_resolution

            # Enable Confirm button
            self.query_one("#confirm", Button).disabled = False

            # Start 10-second confirmation timer
            self._confirmation_task = asyncio.create_task(self._confirmation_timeout())

            self.notify(
                f"Resolution set to {new_resolution}. Confirm within 10 seconds to keep.",
                severity="warning",
            )

        except Exception as e:
            logger.error(f"Error setting resolution: {e}", exc_info=True)
            self.notify(f"Error: {e}", severity="error")

            # Re-enable buttons
            self.query_one("#set", Button).disabled = False
            self.query_one("#back", Button).disabled = False

    async def _confirmation_timeout(self) -> None:
        """Handle confirmation timeout (10 seconds)."""
        try:
            await asyncio.sleep(10)

            # Timeout - rollback resolution
            if self.pending_resolution and self.previous_resolution:
                logger.info(
                    f"Resolution confirmation timeout - rolling back to {self.previous_resolution}"
                )
                await self._rollback_resolution()

        except asyncio.CancelledError:
            # Task was cancelled (user confirmed or dismissed)
            pass

    async def _rollback_resolution(self) -> None:
        """Rollback to previous resolution."""
        if not self.previous_resolution:
            return

        logger.info(f"Rolling back resolution to {self.previous_resolution}")

        try:
            # Call backend to restore previous resolution
            result = await self.backend_client.call_rpc(
                "display.set_resolution",
                {"resolution": self.previous_resolution},
            )

            if result.get("success"):
                self.notify(
                    f"Resolution rolled back to {self.previous_resolution}",
                    severity="information",
                )

                # Update UI
                select = self.query_one("#resolution", Select)
                select.value = self.previous_resolution
                self.current_resolution = self.previous_resolution
                self.pending_resolution = None

                # Disable Confirm, enable Back
                self.query_one("#confirm", Button).disabled = True
                self.query_one("#back", Button).disabled = False

            else:
                error_msg = result.get("message", "Unknown error")
                logger.error(f"Failed to rollback resolution: {error_msg}")
                self.notify(
                    f"Failed to rollback resolution: {error_msg}",
                    severity="error",
                )

        except Exception as e:
            logger.error(f"Error rolling back resolution: {e}", exc_info=True)
            self.notify(f"Error rolling back: {e}", severity="error")

    def _confirm_resolution(self) -> None:
        """Confirm the resolution change."""
        # Cancel the timeout task
        if self._confirmation_task and not self._confirmation_task.done():
            self._confirmation_task.cancel()

        # Update current resolution
        if self.pending_resolution:
            self.current_resolution = self.pending_resolution
            self.pending_resolution = None
            self.previous_resolution = None

        self.notify("Resolution confirmed", severity="information")

        # Dismiss screen with success
        self.dismiss(True)
