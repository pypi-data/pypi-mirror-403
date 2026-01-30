"""FluxBenchD RPC data modal screen."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich.json import JSON
from textual.app import ComposeResult
from textual.containers import Center, Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)


class FluxbenchdRpcModal(ModalScreen[None]):
    """Display FluxBenchD RPC data (getbenchmarks)."""

    DEFAULT_CSS = """
    FluxbenchdRpcModal {
        align: center middle;
    }

    #fluxbenchd_rpc_container {
        width: 90%;
        height: 80%;
        border: solid $primary;
        border-title-align: center;
        padding: 1 2;
    }

    #rpc_data_scroll {
        height: 1fr;
        padding: 1;
        margin: 1 0;
    }

    #error_label, #empty_label, #loading_label {
        width: 1fr;
        height: 1fr;
        content-align: center middle;
    }

    #error_label {
        color: $error;
    }

    #empty_label, #loading_label {
        color: $text-muted;
    }

    #close_container {
        dock: bottom;
        height: auto;
    }

    #close {
        width: auto;
    }
    """

    def __init__(self) -> None:
        """Initialize FluxBenchD RPC modal screen."""
        super().__init__()
        self.rpc_data: dict | None = None
        self.error_message: str | None = None
        self.is_loading = True

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        container = Container(id="fluxbenchd_rpc_container")
        container.border_title = "Fluxbenchd Status"

        with container:
            if self.is_loading:
                yield Label("Loading...", id="loading_label")
            elif self.error_message:
                yield Label(self.error_message, id="error_label")
            elif not self.rpc_data:
                yield Label("No data available", id="empty_label")
            else:
                with VerticalScroll(id="rpc_data_scroll"):
                    yield Static(JSON.from_data(self.rpc_data), id="rpc_data")

            with Center(id="close_container"):
                yield Button("Close", id="close", variant="primary")

    async def on_mount(self) -> None:
        """Fetch FluxBenchD RPC data when screen mounts."""
        app: FluxConfigApp = self.app

        try:
            response = await app.backend_client.call_method(
                "fluxbenchd.call_rpc",
                {"method": "getbenchmarks", "params": []},
            )

            if response.error or (response.result and not response.result.get("success")):
                self.error_message = "RPC offline"
            elif response.result:
                self.rpc_data = response.result.get("result")
            else:
                self.error_message = "No data available"

        except Exception as e:
            logger.error(f"Error fetching FluxBenchD RPC data: {e}", exc_info=True)
            self.error_message = "RPC offline"

        self.is_loading = False
        await self.recompose()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close":
            self.dismiss()
