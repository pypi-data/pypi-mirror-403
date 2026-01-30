"""No network widget for launch screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Static


class NoNetwork(Widget):
    """Widget displayed when no network connectivity is available."""

    class ShellRequested(Message):
        """Message emitted when user requests a shell."""

    def compose(self) -> ComposeResult:
        """Compose the widget.

        Yields:
            Child widgets
        """
        yield Static(
            "No Network connectivity available, unable to present the launchpad."
            " Click the button below for a login shell. Soon this page will handle"
            " the network configuration also."
        )

        yield Center(Button("Shell"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press to request shell.

        Args:
            event: Button press event
        """
        self.post_message(self.ShellRequested())
