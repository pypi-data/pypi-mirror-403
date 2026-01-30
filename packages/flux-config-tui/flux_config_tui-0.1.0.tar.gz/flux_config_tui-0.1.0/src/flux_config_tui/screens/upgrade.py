"""Upgrade screen for TUI - displays upgrade progress and handles reboot countdown."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Literal

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.dom import NoMatches
from textual.reactive import var
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ProgressBar

from flux_config_shared.protocol import EventType
from flux_config_tui.widgets.spinner import Spinner

if TYPE_CHECKING:
    from flux_config_tui.client import BackendClient

logger = logging.getLogger(__name__)


class UpgradeScreen(ModalScreen[bool]):
    """Screen to display upgrade progress and reboot countdown.

    This screen listens for upgrade events from the backend and updates
    the UI accordingly. It shows download progress, processing state,
    and handles the reboot countdown.
    """

    AUTO_FOCUS = None

    bytes_complete = var(0)
    bytes_total = var(0)
    reboot_timer = var(0)
    action_state: var[Literal["Downloading", "Processing", "Finished"]] = var("Downloading")

    def __init__(
        self,
        backend_client: BackendClient,
        bytes_complete: int = 0,
        bytes_total: int = 0,
        reboot_deferred: bool = False,
        reboot_timer: int = 0,
        new_install: bool = False,
    ) -> None:
        """Initialize the upgrade screen.

        Args:
            backend_client: Backend client for RPC calls
            bytes_complete: Initial bytes downloaded
            bytes_total: Total bytes to download
            reboot_deferred: Whether reboot is deferred
            reboot_timer: Countdown timer in seconds
            new_install: Whether this is a new installation
        """
        super().__init__()

        self.backend_client = backend_client
        self._bytes_complete = bytes_complete
        self._bytes_total = bytes_total
        self._reboot_deferred = reboot_deferred
        # Remove 1 second so counter can get to zero
        self._reboot_timer = max(0, reboot_timer - 1)
        self._new_install = new_install

        # Track event listener removal
        self._event_listener_id: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        container = Container()
        container.border_title = "Upgrade Details"
        countdown = Label("", id="countdown-timer")
        countdown.visible = False

        with container:
            yield Label(
                "Upgrade is being processed. This node will reboot when the upgrade is complete.",
                shrink=True,
                id="dialog",
            )
            with Horizontal(id="action-container"):
                yield Label("", id="action-state")
            with Container(id="progress-container"):
                yield ProgressBar()
            yield countdown
            with Horizontal():
                yield Button("Ok", disabled=True)

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.bytes_complete = self._bytes_complete
        self.bytes_total = self._bytes_total

        # Register event listener for upgrade events
        self._event_listener_id = self.backend_client.add_event_listener(self._handle_upgrade_event)
        logger.debug("UpgradeScreen mounted, listening for upgrade events")

    def on_unmount(self) -> None:
        """Called when screen is unmounted."""
        # Remove event listener
        if self._event_listener_id:
            self.backend_client.remove_event_listener(self._event_listener_id)
            self._event_listener_id = None
            logger.debug("UpgradeScreen unmounted, stopped listening for events")

    def _handle_upgrade_event(self, event_type: str, data: dict) -> None:
        """Handle upgrade events from backend.

        Args:
            event_type: Type of event
            data: Event data
        """
        logger.debug(f"UpgradeScreen received event: {event_type}")

        if event_type == EventType.UPGRADE_PROPERTY_CHANGED:
            # Update state from property changes
            if "bytes_complete" in data:
                self.bytes_complete = data["bytes_complete"]

            if "bytes_total" in data:
                self.bytes_total = data["bytes_total"]

            if "reboot_timer" in data:
                self._reboot_timer = data["reboot_timer"]
                self.reboot_timer = data["reboot_timer"]

            # Determine action state based on progress
            if data.get("in_progress"):
                if self.bytes_total > 0 and self.bytes_complete < self.bytes_total:
                    self.action_state = "Downloading"
                else:
                    self.action_state = "Processing"

        elif event_type == EventType.UPGRADE_COMPLETED:
            # Upgrade completed
            self.set_completed()

        elif event_type == EventType.UPGRADE_FAILED:
            # Upgrade failed
            self.set_failed()

    def on_button_pressed(self) -> None:
        """Handle Ok button press - dismiss screen."""
        self.dismiss(True)

    def update_data(
        self,
        *,
        bytes_complete: int | None = None,
        bytes_total: int | None = None,
        reboot_timer: int | None = None,
        action_state: Literal["Downloading", "Processing", "Finished"] | None = None,
        **kwargs: Any,
    ) -> None:
        """Update screen data.

        Args:
            bytes_complete: Bytes downloaded
            bytes_total: Total bytes to download
            reboot_timer: Countdown timer value
            action_state: Current action state
            **kwargs: Additional arguments (ignored)
        """
        if bytes_complete is not None:
            self.bytes_complete = bytes_complete

        if bytes_total is not None:
            self.bytes_total = bytes_total

        if reboot_timer is not None:
            self._reboot_timer = reboot_timer

        if action_state is not None:
            self.action_state = action_state

    def set_failed(self) -> None:
        """Mark upgrade as failed and update UI."""
        try:
            label = self.query_one("#dialog", Label)
        except NoMatches:
            return

        base_text = (
            "Upgrade failed! This can happen for a number of reasons. "
            "Don't worry - this node will try again in a couple of days."
        )
        new_install_text = (
            "This node will proceed with the normal installation flow - "
            "on the version that came with the ISO"
        )

        if self._new_install:
            label_text = f"{base_text}\n\n{new_install_text}"
        else:
            label_text = base_text

        label.update(label_text)

        # Remove progress UI elements
        try:
            self.query_one("#progress-container").remove()
        except NoMatches:
            pass

        try:
            self.query_one("#action-container").remove()
        except NoMatches:
            pass

        # Enable OK button
        try:
            self.query_one(Button).disabled = False
        except NoMatches:
            pass

        # Remove spinner if present
        try:
            self.query_one(Spinner).remove()
        except NoMatches:
            pass

        logger.info("Upgrade marked as failed")

    @work(name="reboot_countdown")
    async def reboot_countdown(self) -> None:
        """Count down to reboot."""
        logger.info(f"Starting reboot countdown from {self._reboot_timer}")

        while self._reboot_timer >= 0:
            self.reboot_timer = self._reboot_timer
            await asyncio.sleep(1)
            self._reboot_timer -= 1

        logger.info("Reboot countdown finished")

    def set_completed(self) -> None:
        """Mark upgrade as completed and start reboot countdown if not deferred."""
        if self._reboot_deferred:
            logger.info("Upgrade completed, reboot deferred")
            return

        self.action_state = "Finished"

        try:
            label = self.query_one("#countdown-timer", Label)
        except NoMatches:
            return

        try:
            self.query_one(Button).disabled = False
        except NoMatches:
            pass

        if self._reboot_timer:
            label.visible = True
            self.reboot_countdown()

        logger.info("Upgrade completed, starting reboot countdown")

    def watch_bytes_complete(self, old: int, new: int) -> None:
        """React to bytes_complete changes.

        Args:
            old: Old value
            new: New value
        """
        if old == new or not new:
            return

        self._bytes_complete = new

        try:
            progress = self.query_one(ProgressBar)
        except NoMatches:
            return

        progress.update(progress=new)

        if new >= self._bytes_total:
            self.action_state = "Processing"

    def watch_bytes_total(self, old: int, new: int) -> None:
        """React to bytes_total changes.

        Args:
            old: Old value
            new: New value
        """
        if old == new or not new:
            return

        self._bytes_total = new

        try:
            progress = self.query_one(ProgressBar)
        except NoMatches:
            return

        progress.update(total=new, progress=0)

    def watch_reboot_timer(self) -> None:
        """React to reboot_timer changes."""
        try:
            label = self.query_one("#countdown-timer", Label)
        except NoMatches:
            return

        text = f"Rebooting in: {self._reboot_timer}" if self._reboot_timer else "Byeeeeee!"

        label.update(text)

    def watch_action_state(self, old: str, new: str) -> None:
        """React to action_state changes.

        Args:
            old: Old state
            new: New state
        """
        try:
            label = self.query_one("#action-state", Label)
        except NoMatches:
            return

        label.update(f"Action: {new}")

        if new == "Processing":
            self.mount(Spinner("line"), after=label)
        elif new == "Finished":
            try:
                self.query_one(Spinner).remove()
            except NoMatches:
                pass
