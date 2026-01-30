"""Launch screen for initial node configuration."""

from __future__ import annotations

import asyncio
import base64
import logging
from ipaddress import IPv4Address
from os import system
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import var
from textual.screen import Screen
from yarl import URL

from flux_config_shared.user_config import UserProvidedConfig
from flux_config_tui.widgets.launchpad import LaunchPad
from flux_config_tui.widgets.no_network import NoNetwork

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

try:
    import pyperclip
    from pyperclip import PyperclipException
except ImportError:
    pyperclip = None  # type: ignore[assignment]

    class PyperclipException(Exception):  # type: ignore[no-redef]  # noqa: N818
        """Fallback exception when pyperclip is not installed."""

logger = logging.getLogger(__name__)


class LaunchScreen(Screen):
    """Screen for initial node configuration via web interface."""

    class MetricsRequested(Message):
        """Message emitted when metrics view is requested."""

    class ConfigReceived(Message):
        """Message emitted when configuration is received from web UI."""

        config: UserProvidedConfig
        screen: LaunchScreen

        def __init__(self, config: UserProvidedConfig, screen: LaunchScreen) -> None:
            """Initialize message.

            Args:
                config: User provided configuration
                screen: LaunchScreen that received config
            """
            super().__init__()

            self.config = config
            self.screen = screen

    show_proxy = var(False)

    port = var(0)
    url: URL = var("")  # type: ignore[assignment]
    auth_token = var("")
    proxy_url: URL = var(URL(""))  # type: ignore[assignment]

    def __init__(self, public_ip: str | None = None) -> None:
        """Initialize launch screen.

        Args:
            public_ip: Public IP address for proxy tunnel
        """
        self.host: IPv4Address | None = None

        self.public_ip = public_ip

        # Tunnel state (managed by daemon, reflected in TUI)
        self.tunnel_state = "disconnected"

        super().__init__()

    @property
    def private_ipv4(self) -> bool:
        """Check if host is a private IPv4 address.

        Returns:
            True if host is private IPv4
        """
        return bool(self.host and self.host.is_private)

    def set_public_ip(self, ip: str) -> None:
        """Set public IP address.

        Args:
            ip: Public IP address
        """
        self.public_ip = ip

    def post_app_configured_message(self, config: UserProvidedConfig) -> None:
        """Post message that configuration was received.

        Args:
            config: User provided configuration
        """
        self.post_message(self.ConfigReceived(config, self))

    def write_tty(self, data: bytes) -> None:
        """Write data to TTY8 for OSC52 copy.

        Args:
            data: Data to write
        """
        try:
            with open("/dev/tty8", "wb") as f:
                f.write(data)
                f.flush()
        except (FileNotFoundError, PermissionError):
            pass

    def osc52_copy(self, data: str) -> None:
        """Copy data using OSC52 escape sequence.

        Args:
            data: Data to copy
        """
        data_bytes = bytes(data, encoding="utf-8")
        encoded = base64.b64encode(data_bytes)
        buffer = b"\033]52;p;" + encoded + b"\a"

        self.write_tty(buffer)

    def action_copy_url(self) -> None:
        """Action to copy URL to clipboard."""
        if pyperclip:
            try:
                pyperclip.copy(str(self.url))
            except PyperclipException as e:
                logger.warning("Failed to copy URL to clipboard: %s", e)
            else:
                self.notify(
                    "Copied. This may not work depending on your environment",
                    timeout=7,
                )

    def compose(self) -> ComposeResult:
        """Compose the screen.

        Yields:
            LaunchPad if network available, NoNetwork otherwise
        """
        app: FluxConfigApp = self.app  # type: ignore

        # Show NoNetwork only when daemon detects no connectivity
        if not app.network_connected:
            yield NoNetwork()
        else:
            # Network available - show LaunchPad
            launchpad = LaunchPad(self.auth_token, self.url)
            launchpad.show_tunnel_connector = self.private_ipv4
            yield launchpad

    @work(name="start_tunnel", exclusive=True)
    async def start_tunnel_via_rpc(self) -> None:
        """Start tunnel via daemon RPC."""
        app: FluxConfigApp = self.app  # type: ignore
        logger.info(f"start_tunnel_via_rpc called: host={self.host}, port={self.port}")

        try:
            launchpad = self.query_one(LaunchPad)
            launchpad.set_loading(True)
        except NoMatches:
            pass

        try:
            logger.info("Calling backend tunnel.start RPC")
            response = await app.backend_client.call_method(
                "tunnel.start",
                {
                    "webserver_host": str(self.host),
                    "webserver_port": self.port,
                    "public_ip": app.public_ip,
                    "keepalive_duration": 3600,
                },
            )
            logger.info(f"RPC response: {response}")

            if response.error or not response.result.get("success"):
                error = response.error.message if response.error else "Unknown error"
                self.notify(f"Tunnel failed: {error}")
                try:
                    launchpad = self.query_one(LaunchPad)
                    launchpad.set_loading(False)
                except NoMatches:
                    pass
                self.show_proxy = False
                return

            # Daemon will emit TUNNEL_STARTED event
            # Event handler will update UI

        except Exception as e:
            logger.error(f"RPC error starting tunnel: {e}")
            self.notify(f"Tunnel error: {e}")
            try:
                launchpad = self.query_one(LaunchPad)
                launchpad.set_loading(False)
            except NoMatches:
                pass
            self.show_proxy = False

    @work(name="stop_tunnel", exclusive=True)
    async def stop_tunnel_via_rpc(self) -> None:
        """Stop tunnel via daemon RPC."""
        app: FluxConfigApp = self.app  # type: ignore

        try:
            await app.backend_client.call_method("tunnel.stop", {})
            # Daemon will emit TUNNEL_STOPPED event
        except Exception as e:
            logger.error(f"RPC error stopping tunnel: {e}")

    @on(LaunchPad.ProxyChanged)
    def on_proxy_changed(self, event: LaunchPad.ProxyChanged) -> None:
        """Handle proxy toggle change - make RPC call to daemon.

        Args:
            event: Proxy change event
        """
        logger.info(f"Proxy toggle changed: {event.value}, tunnel_state: {self.tunnel_state}")
        self.show_proxy = event.value

        if event.value and self.tunnel_state != "connected":
            logger.info("Starting tunnel via RPC")
            self.start_tunnel_via_rpc()
        elif not event.value and self.tunnel_state == "connected":
            logger.info("Stopping tunnel via RPC")
            self.stop_tunnel_via_rpc()

    @on(NoNetwork.ShellRequested)
    def on_shell_requested(self) -> None:
        """Handle shell request from NoNetwork widget."""
        with self.app.suspend():
            system("login")  # noqa: S605

    def _get_current_url(self) -> URL:
        """Compute the current URL based on proxy state.

        Returns:
            Current URL (proxy or direct)
        """
        if not self.port:
            return URL("")

        return self.proxy_url if self.show_proxy else URL(f"https://{self.host}:{self.port}/")

    def watch_host(self, old: IPv4Address | None, new: IPv4Address | None) -> None:
        """Watch host changes and update URL.

        Args:
            old: Old host value
            new: New host value
        """
        self.url = self._get_current_url()

    def watch_port(self, old: int, new: int) -> None:
        """Watch port changes and update URL.

        Args:
            old: Old port value
            new: New port value
        """
        self.url = self._get_current_url()

    def watch_show_proxy(self, old: bool, new: bool) -> None:
        """Watch show_proxy changes and update URL.

        Args:
            old: Old show_proxy value
            new: New show_proxy value
        """
        self.url = self._get_current_url()

    def watch_proxy_url(self, old: URL, new: URL) -> None:
        """Watch proxy_url changes and update URL.

        Args:
            old: Old proxy_url value
            new: New proxy_url value
        """
        if self.show_proxy:
            self.url = self._get_current_url()

    def watch_url(self, old: URL, new: URL) -> None:
        """Watch URL changes.

        Args:
            old: Old URL
            new: New URL
        """
        if old == new or not new:
            return

        try:
            launchpad = self.query_one(LaunchPad)
        except NoMatches:
            return

        launchpad.url = new

    def watch_auth_token(self, old: str, new: str) -> None:
        """Watch auth token changes.

        Args:
            old: Old token
            new: New token
        """
        if old == new:
            return

        try:
            launchpad = self.query_one(LaunchPad)
        except NoMatches:
            return

        launchpad.auth_token = new

    @work(name="start_webserver", exclusive=True)
    async def start_webserver(self, host: str) -> None:
        """Start the configuration webserver.

        Args:
            host: IP address to bind to
        """
        app: FluxConfigApp = self.app  # type: ignore

        # Call backend to start webserver
        response = await app.backend_client.call_method("webserver.start", {"host": host})

        if not response.result or not response.result.get("success"):
            error = response.error.message if response.error else "Unknown error"
            self.notify(f"Failed to start webserver: {error}", severity="error")
            return

        # Set webserver details
        result = response.result
        self.port = result["port"]
        self.auth_token = result["token"]
        self.host = IPv4Address(host)

        # Update URL
        self.url = self._get_current_url()

        self.notify(f"Webserver started on port {self.port}")

    @work(name="stop_webserver", exclusive=True)
    async def stop_webserver(self) -> None:
        """Stop the configuration webserver."""
        app: FluxConfigApp = self.app  # type: ignore

        response = await app.backend_client.call_method("webserver.stop", {})

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            self.notify(f"Failed to stop webserver: {error}", severity="error")
            return

        self.port = 0
        self.auth_token = ""
        self.host = None
        self.url = URL("")

    @on(LaunchPad.MetricsRequested)
    def on_metrics_requested(self, event: LaunchPad.MetricsRequested) -> None:
        """Handle metrics request.

        Args:
            event: Metrics request event
        """
        event.stop()

        self.post_message(self.MetricsRequested())
