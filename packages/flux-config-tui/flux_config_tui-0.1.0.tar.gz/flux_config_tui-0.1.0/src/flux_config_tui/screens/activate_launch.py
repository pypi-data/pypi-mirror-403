"""Activate launch screen for standby mode."""

from __future__ import annotations

import logging

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Label

logger = logging.getLogger(__name__)


class ActivateLaunchScreen(Screen[str]):
    """Screen shown when node is in standby mode (only fluxd running)."""

    class LaunchRequested(Message):
        """Message emitted when user requests to activate launch pad."""

    class MetricsRequested(Message):
        """Message emitted when user requests metrics view."""

    def compose(self) -> ComposeResult:
        """Compose the screen.

        Yields:
            Child widgets
        """
        with Container():
            yield Label(
                """This node is in standby mode. I.e. only fluxd is running.

Click activate to start up the launchpad and configure."""
            )
            with Horizontal():
                yield Button("Activate", id="activate")
                yield Button("Metrics", id="metrics")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button press event
        """
        if event.button.id == "activate":
            self.post_message(self.LaunchRequested())
        elif event.button.id == "metrics":
            self.post_message(self.MetricsRequested())
        else:
            logger.warning("Unknown activate button pressed")
