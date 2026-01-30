"""Settings modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.dom import NoMatches
from textual.events import Key
from textual.reactive import var
from textual.screen import ModalScreen
from textual.widgets import Button


class SettingsScreen(ModalScreen[str]):
    """Modal screen for accessing settings and reconfiguration options."""

    reconfigure_fluxnode_disabled = var(True)
    reconfigure_network_disabled = var(False)
    start_fluxnode_disabled = var(True)

    def __init__(self, name: str, install_complete: bool, reconfiguring: bool) -> None:
        """Initialize settings screen.

        Args:
            name: Screen name
            install_complete: Whether installation is complete
            reconfiguring: Whether currently reconfiguring
        """
        super().__init__(name=name)

        self._reconfigure_fluxnode_disabled = not install_complete or reconfiguring
        self._reconfig_network_disabled = not install_complete or reconfiguring
        self._start_fluxnode_disabled = not install_complete

    def compose(self) -> ComposeResult:
        """Compose the screen.

        Yields:
            Container with buttons
        """
        with Container():
            yield Button(
                "Start Fluxnode",
                id="start-fluxnode",
                disabled=self._start_fluxnode_disabled,
            )
            yield Button(
                "Reconfigure Fluxnode",
                id="reconfigure-fluxnode",
                disabled=self._reconfigure_fluxnode_disabled,
            )
            yield Button(
                "Reconfigure Network",
                id="reconfigure-network",
                disabled=self._reconfig_network_disabled,
            )
            yield Button(
                "Reinstall Components",
                id="reinstall-components",
                disabled=self._reconfigure_fluxnode_disabled,
            )
            yield Button("View Firewall Rules", id="firewall-rules")
            yield Button("View UPnP Mappings", id="upnp-mappings")
            yield Button("App Settings", id="app-settings")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button press event
        """
        self.dismiss(event.button.id)

    def on_key(self, event: Key) -> None:
        """Handle key press.

        Args:
            event: Key press event
        """
        if event.name == "escape":
            self.dismiss("cancel")

    def on_mount(self) -> None:
        """Set initial reactive values on mount."""
        self.reconfigure_fluxnode_disabled = self._reconfigure_fluxnode_disabled
        self.reconfigure_network_disabled = self._reconfig_network_disabled
        self.start_fluxnode_disabled = self._start_fluxnode_disabled

    def watch_reconfigure_fluxnode_disabled(self, old: bool, new: bool) -> None:
        """Watch for changes to fluxnode reconfigure disabled state.

        Args:
            old: Old disabled state
            new: New disabled state
        """
        if old == new:
            return

        self._reconfigure_fluxnode_disabled = new

        try:
            self.query_one("#reconfigure-fluxnode", Button).disabled = new
        except NoMatches:
            pass

    def watch_reconfigure_network_disabled(self, old: bool, new: bool) -> None:
        """Watch for changes to network reconfigure disabled state.

        Args:
            old: Old disabled state
            new: New disabled state
        """
        if old == new:
            return

        self._reconfigure_network_disabled = new

        try:
            self.query_one("#reconfigure-network", Button).disabled = new
        except NoMatches:
            pass

    def watch_start_fluxnode_disabled(self, old: bool, new: bool) -> None:
        """Watch for changes to start fluxnode disabled state.

        Args:
            old: Old disabled state
            new: New disabled state
        """
        if old == new:
            return

        self._start_fluxnode_disabled = new

        try:
            self.query_one("#start-fluxnode", Button).disabled = new
        except NoMatches:
            pass
