"""UPnP mappings viewer screen."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.reactive import var
from textual.screen import ModalScreen
from textual.widgets import Button, Label, LoadingIndicator, Static

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class ModalState(StrEnum):
    """Modal display states."""

    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class UpnpMappingsScreen(ModalScreen[None]):
    """Display current UPnP port mappings."""

    state = var(ModalState.LOADING)

    def __init__(self) -> None:
        """Initialize UPnP mappings screen."""
        super().__init__()
        self.mappings: dict[str, dict[str, Any]] = {}
        self.igd_available = False
        self.client_address: str | None = None
        self.error_message: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout.

        Yields:
            Container with UPnP mappings or error message
        """
        container = Container(id="upnp_container")
        container.border_title = "UPnP Port Mappings"

        with container:
            if self.state == ModalState.LOADING:
                yield Label("Querying UPnP router...", id="message_label", classes="info")
                yield LoadingIndicator(id="loading_indicator")
                with Horizontal(id="button_container"):
                    yield Button("Back", id="back", variant="primary")

            elif self.state == ModalState.ERROR:
                yield Static(
                    "UPnP Status: Error",
                    id="upnp_status",
                    classes="header",
                )
                yield Label(
                    f"Error: {self.error_message}",
                    id="error_label",
                    classes="error",
                )
                with Horizontal(id="button_container"):
                    yield Button("Back", id="back", variant="primary")
                    yield Button("Refresh", id="refresh")

            elif self.state == ModalState.LOADED:
                status = "IGD Available" if self.igd_available else "IGD Not Found"
                yield Static(
                    f"UPnP Status: {status}",
                    id="upnp_status",
                    classes="header",
                )

                if not self.igd_available:
                    yield Label(
                        "No UPnP router found",
                        id="no_igd_label",
                        classes="info",
                    )
                elif not self.mappings:
                    yield Label(
                        "No UPnP mappings configured",
                        id="empty_label",
                        classes="info",
                    )
                else:
                    with VerticalScroll(id="mappings_list"):
                        for port, mapping in sorted(self.mappings.items(), key=lambda x: int(x[0])):
                            host = mapping.get("host", "")
                            remaining_s = mapping.get("remaining_s", 0)
                            description = mapping.get("description", "")

                            ttl_text = self._format_ttl(remaining_s)
                            desc_text = f" [{description}]" if description else ""

                            yield Label(f"Port {port} → {host} (TTL: {ttl_text}){desc_text}")

                with Horizontal(id="button_container"):
                    if self._has_test_mappings():
                        yield Button("Clear Test Mappings", id="clear_test", variant="error")
                    yield Button("Back", id="back", variant="primary")
                    yield Button("Refresh", id="refresh")

    def _format_ttl(self, seconds: int) -> str:
        """Format TTL in seconds to human-readable format.

        Args:
            seconds: TTL in seconds

        Returns:
            Formatted TTL string
        """
        if seconds == 0:
            return "Permanent"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{seconds}s"

    def _has_test_mappings(self) -> bool:
        """Check if any FluxOS gravity test mappings exist for this local IP.

        Returns:
            True if test mappings exist for the local IP
        """
        if not self.client_address:
            return False

        for mapping in self.mappings.values():
            host = mapping.get("host", "")
            if host != self.client_address:
                continue

            desc = mapping.get("description", "")
            if desc in ["Flux_UPNP_Mapping_Test", "Flux_Test_App"]:
                return True
            if desc.startswith("Flux_Prelaunch_App_"):
                return True
        return False

    @work(exclusive=True)
    async def _fetch_mappings(self) -> None:
        """Fetch UPnP status and mappings from backend."""
        from flux_config_tui.client_app import FluxConfigApp

        app: FluxConfigApp = self.app  # type: ignore

        self.state = ModalState.LOADING
        self.error_message = None

        status_response = await app.backend_client.call_method(
            "network.upnp.get_status", {}
        )

        if status_response.result and status_response.result.get("success"):
            self.igd_available = status_response.result.get("igd_available", False)
            self.client_address = status_response.result.get("client_address")
        else:
            self.igd_available = False
            error_msg = status_response.error.message if status_response.error else "Unknown error"
            self.error_message = f"Failed to get UPnP status: {error_msg}"
            self.state = ModalState.ERROR
            return

        if self.igd_available:
            mappings_response = await app.backend_client.call_method(
                "network.upnp.get_mappings", {}
            )

            if mappings_response.result and mappings_response.result.get("success"):
                self.mappings = mappings_response.result.get("mappings", {})
                self.state = ModalState.LOADED
            else:
                error_msg = mappings_response.error.message if mappings_response.error else "Unknown error"
                self.error_message = f"Failed to get UPnP mappings: {error_msg}"
                self.state = ModalState.ERROR
        else:
            self.state = ModalState.LOADED

    @work(exclusive=True)
    async def _clear_test_mappings(self) -> None:
        """Remove all FluxOS gravity test mappings for this local IP."""
        from flux_config_tui.client_app import FluxConfigApp

        app: FluxConfigApp = self.app  # type: ignore

        self.state = ModalState.LOADING

        if not self.client_address:
            logger.warning("Cannot clear test mappings: client address unknown")
            self._fetch_mappings()
            return

        for port, mapping in list(self.mappings.items()):
            host = mapping.get("host", "")
            if host != self.client_address:
                continue

            desc = mapping.get("description", "")
            if desc in ["Flux_UPNP_Mapping_Test", "Flux_Test_App"] or desc.startswith("Flux_Prelaunch_App_"):
                response = await app.backend_client.call_method(
                    "network.upnp.remove_mapping", {"port": int(port)}
                )
                if response.result and response.result.get("success"):
                    logger.info(f"Removed test mapping: {desc} on port {port} for {host}")

        self._fetch_mappings()

    def on_mount(self) -> None:
        """Fetch initial data when screen opens."""
        self._fetch_mappings()

    def watch_state(self, old: ModalState, new: ModalState) -> None:
        """Watch for state changes and recompose.

        Args:
            old: Old state
            new: New state
        """
        if old == new:
            return

        self.call_later(self.recompose)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button press event
        """
        if event.button.id == "back":
            self.dismiss()
        elif event.button.id == "refresh":
            self._fetch_mappings()
        elif event.button.id == "clear_test":
            self._clear_test_mappings()


UpnpMappingsScreen.DEFAULT_CSS = """
UpnpMappingsScreen {
    align: center middle;
}

#upnp_container {
    width: 80;
    height: auto;
    max-height: 30;
    border: solid $primary;
    border-title-align: center;
    padding: 1 2;
}

#message_label {
    text-align: center;
    padding: 1;
    margin-bottom: 1;
}

#loading_indicator {
    height: 3;
    margin: 1 0;
}

#upnp_status {
    text-align: center;
    text-style: bold;
    padding: 0 0 1 0;
    color: $accent;
}

#mappings_list {
    height: auto;
    max-height: 18;
    padding: 1;
    margin: 1 0;
}

#mappings_list Label {
    text-align: center;
    width: 100%;
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

#button_container {
    width: 100%;
    height: auto;
    align: center middle;
}

#button_container Button {
    margin: 0 1;
}
"""
