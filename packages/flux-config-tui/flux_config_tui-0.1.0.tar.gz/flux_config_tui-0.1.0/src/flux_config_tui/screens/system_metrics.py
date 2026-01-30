"""System metrics dashboard screen."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.events import Click, Key, MouseMove
from textual.message import Message
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Button, Label

from flux_config_tui.screens.fluxbenchd_rpc_modal import FluxbenchdRpcModal
from flux_config_tui.screens.fluxd_rpc_modal import FluxdRpcModal
from flux_config_tui.widgets import (
    FluxbenchdMetrics,
    FluxdMetrics,
    FluxosMetrics,
    ServiceMetrics,
    SystemLoad,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SystemMetrics(Screen):
    """System metrics dashboard showing service status and system resources."""

    # Custom messages for button actions
    class BackRequested(Message):
        """Request to go back to previous screen."""

    class ShellRequested(Message):
        """Request to open shell."""

    class LogsRequested(Message):
        """Request to view logs."""

    class ShutdownScreenRequested(Message):
        """Request to show shutdown screen."""

        def __init__(self, label_text: str) -> None:
            super().__init__()
            self.label_text = label_text

    class SettingsScreenRequested(Message):
        """Request to show settings screen."""

    CSS_PATH = "system_metrics.tcss"

    BINDINGS = [
        ("escape", "clear_focus", "Clear focus"),
    ]

    # Reactive variables for button visibility
    show_back = var(True)
    enable_shell = var(False)
    enable_logs = var(False)

    def __init__(self) -> None:
        """Initialize the system metrics screen."""
        super().__init__()

        # Create widget instances that can be accessed before mounting
        self.fluxd_metrics = FluxdMetrics()
        self.fluxbenchd_metrics = FluxbenchdMetrics()
        self.fluxos_metrics = FluxosMetrics()
        self.service_metrics = ServiceMetrics()

        self._enable_shell = False
        self._enable_logs = False
        self._show_back = True

        # Endpoint details for footer
        self.local_ip = "Unknown"
        self.public_ip = "Unknown"
        self.api_port = "Unknown"
        self.upnp_enabled = False

    def on_screen_resume(self) -> None:
        """Clear focus when screen resumes."""
        self.set_focus(None)

    def action_clear_focus(self) -> None:
        """Clear focus from all widgets."""
        self.set_focus(None)

    def on_mount(self) -> None:
        """Configure buttons and labels when mounted."""
        logger.info("SystemMetrics mounted")
        self.query_one("#shell", Button).display = self._enable_shell
        self.query_one("#logs", Button).display = self._enable_logs
        self.query_one("#back", Button).display = self._show_back
        self.query_one("#local-ip", Label).update(f"Local: {self.local_ip}")
        self.query_one("#public-ip", Label).update(f"Public: {self.public_ip}")
        self.query_one("#api-port", Label).update(f"Api port: {self.api_port}")
        self.query_one("#upnp-enabled", Label).update(f"UPnP Enabled: {self.upnp_enabled}")

    def on_key(self, event: Key) -> None:
        """Log key events."""
        logger.info(f"SystemMetrics KEY: key={event.key}, char={event.character}")

    def on_mouse_move(self, event: MouseMove) -> None:
        """Log mouse move events."""
        logger.info(f"SystemMetrics MOUSE MOVE: x={event.x}, y={event.y}")

    def on_click(self, event: Click) -> None:
        """Log click events."""
        logger.info(f"SystemMetrics CLICK: x={event.x}, y={event.y}")

    def compose(self) -> ComposeResult:
        """Compose the system metrics UI."""
        # Header with action buttons
        header = Horizontal(id="metrics-header")
        header.border_title = "FluxOS System Metrics"

        # Footer with network info
        footer = Horizontal(id="metrics-footer")

        # Action buttons
        back_button = Button("\u21b0", id="back", classes="header-button", tooltip="Back")
        log_button = Button("i", id="logs", classes="header-button", tooltip="Logs")
        shell_button = Button("\u003e\u0332", id="shell", classes="header-button", tooltip="Shell")
        shutdown_button = Button(
            "\u23fb",
            id="shutdown",
            classes="header-button",
            tooltip="Power Options",
        )
        settings_button = Button(
            "\u26ed", id="settings", classes="header-button", tooltip="Settings"
        )

        with header:
            yield back_button
            yield shell_button
            yield log_button
            yield Label(
                f"Build: {os.environ.get('FLUXOS_HUMAN_VERSION', 'unknown')}",
                id="version-label",
            )
            yield SystemLoad()
            yield shutdown_button
            yield settings_button

        with Grid():
            # FluxD metrics widget
            self.fluxd_metrics.border_title = "Fluxd Metrics"
            yield self.fluxd_metrics

            # FluxBenchD metrics widget
            self.fluxbenchd_metrics.border_title = "Fluxbenchd Metrics"
            yield self.fluxbenchd_metrics

            # FluxOS metrics widget
            self.fluxos_metrics.border_title = "Gravity Metrics"
            yield self.fluxos_metrics

            # Service metrics widget
            self.service_metrics.border_title = "Service Metrics"
            yield self.service_metrics

        with footer:
            yield Label("Local: Unknown", id="local-ip")
            yield Label("Public: Unknown", id="public-ip")
            yield Label("Api Port: Unknown", id="api-port")
            yield Label("UPnP Enabled: Unknown", id="upnp-enabled")

    def set_endpoint_details(
        self,
        *,
        local_ip: str | None = None,
        public_ip: str | None = None,
        api_port: str | None = None,
        upnp_enabled: bool | None = None,
    ) -> None:
        """Update endpoint details in the footer.

        Args:
            local_ip: Local IP address
            public_ip: Public IP address
            api_port: API port number
            upnp_enabled: Whether UPnP is enabled
        """
        if local_ip:
            self.local_ip = local_ip
            if self.is_attached:
                self.query_one("#local-ip", Label).update(f"Local: {local_ip}")

        if public_ip:
            self.public_ip = public_ip
            if self.is_attached:
                self.query_one("#public-ip", Label).update(f"Public: {public_ip}")

        if upnp_enabled is False:
            api_port = "16127"

        if api_port:
            self.api_port = api_port
            if self.is_attached:
                self.query_one("#api-port", Label).update(f"Api port: {api_port}")

        if upnp_enabled is not None:
            self.upnp_enabled = upnp_enabled
            if self.is_attached:
                self.query_one("#upnp-enabled", Label).update(f"UPnP Enabled: {upnp_enabled}")

    def update_service_state(
        self, service: str, main_pid: int, active_state: str, sub_state: str
    ) -> None:
        """Update service state from SERVICE_STATE_CHANGED event.

        Args:
            service: Service name (e.g., "docker.service", "fluxd.service")
            main_pid: Process ID
            active_state: Active state (active, inactive, etc.)
            sub_state: Sub state (running, dead, etc.)
        """
        try:
            if service in ["docker.service", "mongod.service", "syncthing.service"]:
                self.service_metrics.set_state(service, main_pid, active_state, sub_state)
            elif service == "fluxd.service":
                self.fluxd_metrics.set_state(main_pid, active_state, sub_state)
            elif service == "fluxbenchd.service":
                self.fluxbenchd_metrics.set_state(main_pid, active_state, sub_state)
            elif service == "fluxos.service":
                self.fluxos_metrics.set_state(main_pid, active_state, sub_state)
        except Exception as e:
            logger.error(f"Error updating service state for {service}: {e}", exc_info=True)

    def update_process_stats(self, processes: dict) -> None:
        """Update process resource stats from SYSTEM_METRICS_UPDATE event.

        Args:
            processes: Dict mapping process name to stats (rss_bytes, cpu_percent)
        """
        try:
            for name, stats in processes.items():
                rss = stats.get("rss_bytes", 0)
                cpu = stats.get("cpu_percent", 0.0)

                if name == "fluxd":
                    self.fluxd_metrics.system_resources.update_stats(rss, cpu)
                elif name == "fluxbenchd":
                    self.fluxbenchd_metrics.system_resources.update_stats(rss, cpu)
                elif name == "fluxos":
                    self.fluxos_metrics.system_resources.update_stats(rss, cpu)
        except Exception as e:
            logger.error(f"Error updating process stats: {e}", exc_info=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        logger.info(f"Button pressed: {event.button.id}")
        msg: (
            SystemMetrics.BackRequested
            | SystemMetrics.ShellRequested
            | SystemMetrics.ShutdownScreenRequested
            | SystemMetrics.SettingsScreenRequested
            | SystemMetrics.LogsRequested
            | None
        )

        match event.button.id:
            case "back":
                msg = SystemMetrics.BackRequested()
            case "shell":
                msg = SystemMetrics.ShellRequested()
            case "shutdown":
                msg = SystemMetrics.ShutdownScreenRequested("Select a Power State Option:")
            case "logs":
                msg = SystemMetrics.LogsRequested()
            case "settings":
                msg = SystemMetrics.SettingsScreenRequested()
            case _:
                msg = None

        if msg:
            self.post_message(msg)

    def watch_show_back(self, old: bool, new: bool) -> None:
        """React to show_back changes."""
        if old == new:
            return

        self._show_back = new

        if self.is_mounted:
            back_button = self.query_one("#back", Button)
            back_button.display = new

    def watch_enable_shell(self, old: bool, new: bool) -> None:
        """React to enable_shell changes."""
        if old == new:
            return

        self._enable_shell = new

        if self.is_mounted:
            shell_button = self.query_one("#shell", Button)
            shell_button.display = new

    def watch_enable_logs(self, old: bool, new: bool) -> None:
        """React to enable_logs changes."""
        if old == new:
            return

        self._enable_logs = new

        if self.is_mounted:
            logs_button = self.query_one("#logs", Button)
            logs_button.display = new

    def on_fluxd_metrics_show_rpc_modal(self, message: FluxdMetrics.ShowRpcModal) -> None:
        """Handle FluxD metrics widget requesting to show RPC modal."""
        logger.info("Opening FluxD RPC modal")
        self.app.push_screen(FluxdRpcModal())

    def on_fluxbenchd_metrics_show_rpc_modal(
        self, message: FluxbenchdMetrics.ShowRpcModal
    ) -> None:
        """Handle FluxBenchD metrics widget requesting to show RPC modal."""
        logger.info("Opening FluxBenchD RPC modal")
        self.app.push_screen(FluxbenchdRpcModal())
