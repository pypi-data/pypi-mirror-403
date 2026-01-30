"""Firewall rules viewer screen."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Center, Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class FirewallRulesScreen(ModalScreen[None]):
    """Display current firewall rules."""

    def __init__(self) -> None:
        """Initialize firewall rules screen."""
        super().__init__()
        self.rules: list[dict[str, Any]] = []
        self.enabled = False
        self.error_message: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout.

        Yields:
            Container with firewall rules or error message
        """
        container = Container(id="firewall_container")
        container.border_title = "Firewall Rules"

        with container:
            # Status label
            status = "Active" if self.enabled else "Inactive"
            yield Static(
                f"Firewall Status: {status}",
                id="firewall_status",
                classes="header",
            )

            # Error message or rules list
            if self.error_message:
                yield Label(
                    f"Error: {self.error_message}",
                    id="error_label",
                    classes="error",
                )
            elif not self.enabled:
                yield Label(
                    "Firewall is disabled",
                    id="disabled_label",
                    classes="info",
                )
            elif not self.rules:
                yield Label(
                    "No firewall rules configured",
                    id="empty_label",
                    classes="info",
                )
            else:
                # Scrollable rules list
                with VerticalScroll(id="rules_list"):
                    for rule in self.rules:
                        number = rule.get("number", "?")
                        rule_text = rule.get("rule", "")
                        yield Label(f"[{number}] {rule_text}")

            with Center():
                yield Button("Back", id="back", variant="primary")

    async def on_mount(self) -> None:
        """Fetch firewall rules when screen mounts."""
        from flux_config_tui.client_app import FluxConfigApp

        app: FluxConfigApp = self.app  # type: ignore
        response = await app.backend_client.call_method("firewall.get_rules", {})

        if response.result and response.result.get("success"):
            result = response.result
            self.enabled = result.get("enabled", False)
            self.rules = result.get("rules", [])
        else:
            error_msg = response.error.message if response.error else "Unknown error"
            self.error_message = error_msg

        # Refresh to show updated data
        await self.recompose()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button press event
        """
        if event.button.id == "back":
            self.dismiss()


# CSS for the firewall rules screen
FirewallRulesScreen.DEFAULT_CSS = """
FirewallRulesScreen {
    align: center middle;
}

#firewall_container {
    width: 80;
    height: auto;
    max-height: 30;
    border: solid $primary;
    border-title-align: center;
    padding: 1 2;
}

#firewall_status {
    text-align: center;
    text-style: bold;
    padding: 0 0 1 0;
    color: $accent;
}

#rules_list {
    height: auto;
    max-height: 18;
    border: solid $primary;
    padding: 1;
    margin: 1 0;
}

#rules_list Label {
    padding: 0 1;
}

.error {
    color: $error;
    text-align: center;
    width: 100%;
    padding: 1;
}

.info {
    color: $text-muted;
    text-align: center;
    width: 100%;
    padding: 1;
}

#back {
    width: auto;
}
"""
