"""App settings screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button


class ScreenRequestedMessage(Message):
    """Message requesting a specific screen to be shown."""

    def __init__(self, screen: str) -> None:
        """Initialize message.

        Args:
            screen: Name of screen to show
        """
        super().__init__()
        self.screen = screen


class AppSettingsScreen(Screen):
    """Screen for accessing app-level settings."""

    BINDINGS = [Binding("escape", "dismiss", "Dismiss", show=False)]
    BORDER_TITLE = "App Settings"

    def compose(self) -> ComposeResult:
        """Compose the screen.

        Yields:
            Container with setting buttons
        """
        with Container():
            with Grid():
                yield Button("Theme Selector", id="change-theme")
                yield Button("Energy Saving", id="energy-saving")
                yield Button("Display Size", id="display-size")
                with Container():
                    yield Button("Back", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button press event
        """
        if event.button.id == "change-theme":
            self.post_message(ScreenRequestedMessage("change_theme"))
        elif event.button.id == "energy-saving":
            self.post_message(ScreenRequestedMessage("energy_saving"))
        elif event.button.id == "display-size":
            self.post_message(ScreenRequestedMessage("display_size"))
        elif event.button.id == "back":
            self.dismiss()
