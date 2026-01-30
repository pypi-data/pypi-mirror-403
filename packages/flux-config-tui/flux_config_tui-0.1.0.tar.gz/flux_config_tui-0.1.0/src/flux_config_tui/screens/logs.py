"""Logs viewer screen for systemd service logs."""

from __future__ import annotations

import logging
from copy import copy
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import TYPE_CHECKING

from textual import work
from textual.binding import Binding
from textual.containers import Horizontal
from textual.dom import NoMatches
from textual.events import Click, Focus, Key
from textual.message import Message
from textual.reactive import var
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Label, RichLog, Select, Switch

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)


@dataclass
class LoggerSettings:
    """Settings for log viewer widget."""

    max_lines: int = 500
    wrap: bool = True
    highlight: bool = True
    auto_scroll: bool = True

    asdict = asdict


class Logger(Widget):
    """Widget for displaying systemd service logs."""

    class LoggerSelected(Message):
        """Posted when logger is double-clicked or Enter is pressed."""

        def __init__(self, logger: Logger) -> None:
            super().__init__()
            self.logger = logger

    class LoggerFocused(Message):
        """Posted when logger receives focus."""

        def __init__(self, logger: Logger) -> None:
            super().__init__()
            self.logger = logger

    ALLOW_MAXIMIZE = True
    BINDINGS = [
        Binding("escape", "dismiss", "Dismiss", show=False),
    ]

    highlight = var(True)
    auto_scroll = var(True)

    def __init__(
        self,
        service: str,
        logger_settings: LoggerSettings | None = None,
    ) -> None:
        """Initialize logger widget.

        Args:
            service: Service name (e.g., "fluxd", "fluxos")
            logger_settings: Optional logger settings
        """
        super().__init__()

        self.service = service
        self.logger_settings = logger_settings or LoggerSettings()
        self.rich_log = RichLog(**self.logger_settings.asdict())
        self.last_click = 0.0
        self._tailing = False

    @classmethod
    def from_service(cls, service: str) -> Logger:
        """Create logger from service name.

        Args:
            service: Service name

        Returns:
            Logger widget
        """
        logger = cls(service)
        logger.border_title = service
        return logger

    def compose(self) -> ComposeResult:
        """Compose logger widget."""
        yield self.rich_log

    def on_mount(self) -> None:
        """Start tailing logs when mounted."""
        self.tail_logs()

    @work(name="tail_logs", exclusive=True)
    async def tail_logs(self) -> None:
        """Tail logs from backend via RPC."""
        if self._tailing:
            return

        self._tailing = True
        app: FluxConfigApp = self.app  # type: ignore[assignment]

        try:
            # Get initial logs
            response = await app.backend_client.call_method(
                "logs.get_service",
                {"service": self.service, "lines": self.logger_settings.max_lines},
            )

            if response.get("success"):
                logs = response.get("logs", "")
                self.rich_log.write(logs)
            else:
                error = response.get("error", "Unknown error")
                self.rich_log.write(f"Error loading logs: {error}")

        except Exception as e:
            logger.error(f"Error tailing logs for {self.service}: {e}", exc_info=True)
            self.rich_log.write(f"Error: {e}")
        finally:
            self._tailing = False

    def stop_tail_logs(self) -> None:
        """Stop tailing logs and clear display."""
        self.rich_log.clear()
        self.workers.cancel_node(self)
        self._tailing = False

    def watch_highlight(self, old: bool, new: bool) -> None:
        """React to highlight setting change.

        Args:
            old: Old value
            new: New value
        """
        if old == new:
            return

        lines = copy(self.rich_log.lines)
        raw = "\n".join(x.text for x in lines)

        self.rich_log.clear()
        self.rich_log.highlight = new
        self.rich_log.write(raw)

    def watch_auto_scroll(self, old: bool, new: bool) -> None:
        """React to auto_scroll setting change.

        Args:
            old: Old value
            new: New value
        """
        if old == new:
            return

        self.rich_log.auto_scroll = new

    def on_key(self, event: Key) -> None:
        """Handle key events.

        Args:
            event: Key event
        """
        if event.name == "enter":
            self.post_message(self.LoggerSelected(self))

    def on_click(self, event: Click) -> None:
        """Handle click events (double-click to maximize).

        Args:
            event: Click event
        """
        now = perf_counter()

        if now - self.last_click < 0.4:
            self.post_message(self.LoggerSelected(self))
        else:
            self.last_click = now

    def on_descendant_focus(self, event: Focus) -> None:
        """Handle descendant focus events.

        Args:
            event: Focus event
        """
        event.stop()
        self.post_message(self.LoggerFocused(self))


class LogScreen(Screen):
    """Screen for viewing systemd service logs."""

    CSS_PATH = "logs.tcss"
    BINDINGS = [
        Binding("escape", "dismiss", "Dismiss", show=False),
    ]

    def __init__(self, services: list[str] | None = None) -> None:
        """Initialize log screen.

        Args:
            services: List of service names to show logs for.
                     If None, will fetch from backend on mount.
        """
        super().__init__()
        self._services = services or []
        self.loggers: list[Logger] = []

    def compose(self) -> ComposeResult:
        """Compose log screen."""
        # Create loggers for services
        self.loggers = [Logger.from_service(s) for s in self._services]

        options = [(s, s) for s in self._services]

        header = Horizontal()
        header.border_title = "Flux Logs"

        with header:
            with Horizontal(classes="switch-container"):
                yield Label("Logger:")
                yield Select(
                    options=options,
                    value=self._services[0] if self._services else None,
                    allow_blank=False,
                )
            yield Button("Close", id="state-toggle")
            with Horizontal(classes="switch-container"):
                yield Label("Highlight:")
                yield Switch(value=True, id="highlight")
            with Horizontal(classes="switch-container"):
                yield Label("Auto Scroll:")
                yield Switch(value=True, id="auto-scroll")
            yield Button("Exit", id="exit")
        yield from self.loggers

    async def on_mount(self) -> None:
        """Load available services from backend if not provided."""
        if not self._services:
            app: FluxConfigApp = self.app  # type: ignore[assignment]

            try:
                response = await app.backend_client.call_method(
                    "logs.get_available_services",
                    {},
                )

                if response.get("success"):
                    all_services = response.get("services", [])
                    # Filter to only flux-related services
                    flux_services = [
                        s for s in all_services if s.startswith("flux") or s == "mongodb"
                    ]
                    self._services = flux_services[:5]  # Limit to 5 services
                else:
                    logger.error("Failed to load services")
                    self._services = ["fluxd", "fluxos", "mongodb"]  # Defaults

            except Exception as e:
                logger.error(f"Error loading services: {e}", exc_info=True)
                self._services = ["fluxd", "fluxos", "mongodb"]  # Defaults

            # Recompose with loaded services
            await self.recompose()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch changes.

        Args:
            event: Switch changed event
        """
        try:
            logger_name = self.query_one(Select).value
        except NoMatches:
            return

        logger_widget = next(
            filter(lambda x: x.service == logger_name, self.loggers),
            None,
        )

        if not logger_widget:
            return

        if event.switch.id == "highlight":
            logger_widget.highlight = event.value
        elif event.switch.id == "auto-scroll":
            logger_widget.auto_scroll = event.value

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes.

        Args:
            event: Select changed event
        """
        logger_widget = next(
            filter(lambda x: x.service == event.value, self.loggers),
            None,
        )

        if not logger_widget:
            return

        highlight = self.query_one("#highlight", Switch)
        auto_scroll = self.query_one("#auto-scroll", Switch)
        state_toggle = self.query_one("#state-toggle", Button)

        highlight.value = logger_widget.highlight
        auto_scroll.value = logger_widget.auto_scroll
        state_toggle.label = "Close" if logger_widget.display else "Open"

    def on_logger_logger_selected(self, event: Logger.LoggerSelected) -> None:
        """Handle logger selection (maximize/minimize).

        Args:
            event: Logger selected event
        """
        self.minimize() if event.logger.is_maximized else self.maximize(event.logger)

    def on_logger_logger_focused(self, event: Logger.LoggerFocused) -> None:
        """Handle logger focus.

        Args:
            event: Logger focused event
        """
        self.query_one(Select).value = event.logger.service

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button pressed event
        """
        if event.button.id == "exit":
            self.dismiss()
        elif event.button.id == "state-toggle":
            logger_name = self.query_one(Select).value

            logger_widget = next(
                filter(lambda x: x.service == logger_name, self.loggers),
                None,
            )

            if not logger_widget:
                return

            logger_widget.display = not logger_widget.display
            event.button.label = "Close" if logger_widget.display else "Open"

            if logger_widget.display:
                logger_widget.tail_logs()
            else:
                logger_widget.stop_tail_logs()
