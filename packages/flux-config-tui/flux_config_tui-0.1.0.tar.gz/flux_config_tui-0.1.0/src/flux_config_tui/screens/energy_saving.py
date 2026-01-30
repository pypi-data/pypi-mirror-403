"""Energy saving (screen poweroff) settings screen."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Select

if TYPE_CHECKING:
    from textual.app import ComposeResult

logger = logging.getLogger(__name__)


class EnergySavingScreen(ModalScreen[int | None]):
    """Modal screen for configuring screen poweroff timeout."""

    def __init__(self, current_option: int) -> None:
        """Initialize energy saving screen.

        Args:
            current_option: Current timeout value in seconds
        """
        super().__init__()
        self.current_option = current_option

    def compose(self) -> ComposeResult:
        """Compose energy saving screen."""
        options = [
            ("After 10 Minutes", 600),
            ("After 20 Minutes", 1200),
            ("After 30 Minutes", 1800),
            ("After 1 hour", 3600),
            ("Never", 0),
        ]

        with Vertical():
            yield Label(
                "By default, ArcaneOS will leave the screen enabled for easy monitoring of the "
                "system. However, if you are running bare-metal, you may not want this. Adjust "
                "the display off time here.",
                id="dialog",
            )
            with Horizontal(id="poweroff-container"):
                yield Label("Power Off Screen:", classes="text-label")
                yield Select(
                    options,
                    allow_blank=False,
                    value=self.current_option,
                    id="poweroff",
                )
            with Horizontal(id="button-container"):
                yield Button("Back", id="back")
                yield Button("Save", id="save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button pressed event
        """
        if event.button.id == "back":
            self.dismiss(None)
        elif event.button.id == "save":
            from textual.widgets._select import NoSelection

            poweroff = self.query_one("#poweroff", Select)
            value = poweroff.value
            if isinstance(value, NoSelection):
                value = None
            self.dismiss(value)
