"""LaunchPad widget for configuration web interface."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Grid, Horizontal, Vertical
from textual.message import Message
from textual.reactive import var
from textual.widget import Widget
from textual.widgets import Button, Static, Switch
from yarl import URL

from flux_config_tui.widgets.qr import Qr


class LaunchPad(Widget):
    """Widget displaying QR code and configuration URL for setup."""

    class MetricsRequested(Message):
        """Message emitted when user requests metrics view."""

    class ProxyChanged(Message):
        """Message emitted when proxy toggle changes."""

        def __init__(self, value: bool) -> None:
            """Initialize message.

            Args:
                value: New proxy state
            """
            super().__init__()
            self.value = value

    auth_token = var("")
    url = var(URL)
    show_tunnel_connector = var(True)

    @property
    def qr_link(self) -> URL:
        """Get URL with token query parameter for QR code.

        Returns:
            URL with token query parameter
        """
        query = f"token={self.auth_token}"
        return self.url % query  # type: ignore[operator]

    @property
    def url_link(self) -> str:
        """Get formatted URL for display.

        Returns:
            Formatted URL string (clickable if query string present)
        """
        if self.url.query_string:
            url = f"{self.url.origin()}\n{self.url.relative()}"  # type: ignore[misc]
        else:
            url = self.url
        return f"[@click='screen.copy_url']{url}[/]"

    def __init__(self, auth_token: str, url: URL) -> None:
        """Initialize LaunchPad widget.

        Args:
            auth_token: Authentication token for webserver
            url: Configuration URL
        """
        super().__init__()

        self._auth_token = auth_token
        self._url = url

        self._connection_container = Horizontal(id="connection-type")

    def on_mount(self) -> None:
        """Set initial reactive values on mount."""
        self.auth_token = self._auth_token
        self.url = self._url

    def compose(self) -> ComposeResult:
        """Compose the widget.

        Yields:
            Child widgets
        """
        with Grid():
            yield Static("Configure your Fluxnode. Scan QR or visit URL.", id="title")
            yield Qr(str(self.qr_link))
            with Vertical(id="labels-container"):
                with Vertical(id="labels-content"):
                    with Vertical(id="url-container"):
                        yield Static("URL:\n")
                        yield Static(self.url_link, id="url")
                    yield Static(f"Token: {self.auth_token}", id="token")
                    yield Center(Button("Metrics", id="metrics-button"))
            with self._connection_container:
                yield Static("Direct Connect  ")
                yield Switch(id="connection_switch")
                yield Static("  Secure Tunnel")

    def watch_show_tunnel_connector(self, old: bool, new: bool) -> None:
        """Watch for tunnel connector visibility changes.

        Args:
            old: Old visibility state
            new: New visibility state
        """
        if old == new:
            return

        self._connection_container.visible = new

    def watch_auth_token(self, old: str, new: str) -> None:
        """Watch for auth token changes.

        Args:
            old: Old token
            new: New token
        """
        if old == new:
            return

        self._auth_token = new

        token = self.query_one("#token", Static)
        token.update(f"Token: {new}")

        qr = self.query_one(Qr)
        qr.text = str(self.qr_link)

    def watch_url(self, old: URL, new: URL) -> None:
        """Watch for URL changes.

        Args:
            old: Old URL
            new: New URL
        """
        if old == new:
            return

        self._url = new

        qr = self.query_one(Qr)
        qr.text = str(self.qr_link)

        link = self.query_one("#url", Static)
        link.update(self.url_link)

    def set_loading(self, loading: bool) -> None:
        """Set loading state on labels content (inside border).

        Args:
            loading: Loading state
        """
        container = self.query_one("#labels-content", Vertical)
        container.loading = loading

    def disable_proxy(self, url: URL) -> None:
        """Disable proxy and reset to direct URL.

        Args:
            url: Direct connection URL
        """
        switch = self.query_one(Switch)

        self.url = url

        with self.prevent(Switch.Changed):
            switch.value = False

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle metrics button press.

        Args:
            event: Button press event
        """
        event.stop()

        self.post_message(self.MetricsRequested())

    @on(Switch.Changed)
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle proxy toggle switch change.

        Args:
            event: Switch change event
        """
        event.stop()

        self.post_message(self.ProxyChanged(event.value))
