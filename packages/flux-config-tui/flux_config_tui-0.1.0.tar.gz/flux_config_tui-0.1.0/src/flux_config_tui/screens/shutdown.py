"""Shutdown/reboot confirmation screen."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual.containers import Container, Horizontal
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label

if TYPE_CHECKING:
    from textual.app import ComposeResult


logger = logging.getLogger(__name__)


class ShutdownScreen(ModalScreen[None]):
    """Modal screen for shutdown/reboot confirmation."""

    def __init__(
        self,
        label_text: str,
        *,
        firmware_option: bool = False,
        cancel_option: bool = False,
    ) -> None:
        """Initialize shutdown screen.

        Args:
            label_text: Text to display in the modal
            firmware_option: If True, reboot will boot into firmware (UEFI)
            cancel_option: If True, show a Cancel button
        """
        super().__init__()

        self.label_text = label_text
        self.firmware_option = firmware_option
        self.cancel_option = cancel_option

    class ShutdownRequested(Message):
        """Posted when shutdown is requested."""

    class RebootRequested(Message):
        """Posted when reboot is requested."""

        def __init__(self, firmware: bool = False) -> None:
            """Initialize reboot requested message.

            Args:
                firmware: If True, boot into firmware (UEFI)
            """
            super().__init__()
            self.firmware = firmware

    def compose(self) -> ComposeResult:
        """Compose shutdown screen."""
        with Container():
            yield Label(
                self.label_text,
                id="info-label",
            )

            with Horizontal(id="button-container"):
                yield Button("Shutdown", id="shutdown")
                yield Button("Reboot", id="reboot")
                if self.cancel_option:
                    yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button pressed event
        """
        if event.button.id == "shutdown":
            self.post_message(ShutdownScreen.ShutdownRequested())
        elif event.button.id == "reboot":
            self.post_message(ShutdownScreen.RebootRequested(self.firmware_option))
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def on_mount(self) -> None:
        """Focus the last button (Cancel if present, otherwise Reboot)."""
        buttons = self.query(Button)
        buttons[-1].focus()
