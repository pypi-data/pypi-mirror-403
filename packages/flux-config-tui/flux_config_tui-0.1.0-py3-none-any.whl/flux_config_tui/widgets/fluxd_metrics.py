"""FluxD metrics widget showing daemon status and resources."""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from typing import TYPE_CHECKING, Literal

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Click
from textual.message import Message
from textual.reactive import var
from textual.widget import Widget

from .action_state import ActionState
from .block_count import BlockCount
from .fluxd_status import FluxdStatus
from .online_indicator import OnlineIndicator
from .progress_indicator import ProgressIndicator
from .rpc_indicator import RpcIndicator
from .system_resources import SystemResources

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)

StateType = Literal[
    "Waiting for Config",
    "Downloading Chain",
    "Streaming Chain",
    "Speedtesting CDN",
    "Fetching Flux Params",
    "Cloning",
    "Installing",
    None,
]


class FluxdMetrics(Widget, can_focus=True):
    """FluxD metrics widget showing service status and resources."""

    class ShowRpcModal(Message):
        """Posted when user requests to see FluxD RPC data."""

        pass

    BORDER_TITLE = "Fluxd Metrics"

    BINDINGS = [
        Binding("enter", "show_modal", "Show RPC Data", show=False),
    ]

    update_interval_s: int = 5

    main_pid = var(0)
    control_pid = var(0)
    active_state = var("unknown")
    sub_state = var("unknown")
    online = var(False)

    def __init__(self, action_state: StateType | None = None) -> None:
        """Initialize FluxD metrics widget.

        Args:
            action_state: Initial action state (like "Downloading Chain")
        """
        super().__init__()

        self.progress_indicator = ProgressIndicator()
        self.progress_indicator.visible = action_state == "Downloading Chain"

        self.action_state = ActionState(action_state)
        self.online_indicator = OnlineIndicator()
        self.rpc_indicator = RpcIndicator()
        self.blockcount = BlockCount()
        self.system_resources = SystemResources("fluxd")
        self.fluxd_status = FluxdStatus()

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        with Horizontal(id="resources-row"):
            yield self.system_resources
            yield self.online_indicator
        with Horizontal(id="block-rpc-row"):
            yield self.blockcount
            yield self.rpc_indicator
        yield self.fluxd_status
        yield self.action_state
        yield self.progress_indicator

    def set_state(self, main_pid: int, active_state: str, sub_state: str) -> None:
        """Set service state from SERVICE_STATE_CHANGED event (replaces polling).

        Args:
            main_pid: Process ID
            active_state: Active state (active, inactive, etc.)
            sub_state: Sub state (running, dead, etc.)
        """
        self.main_pid = main_pid
        self.active_state = active_state
        self.sub_state = sub_state

        if active_state != "active" or sub_state != "running":
            self.rpc_indicator.rpc_online = False

    def set_action_state(
        self,
        state: StateType,
        label: str | None = None,
    ) -> None:
        """Set the current action state.

        Args:
            state: State type
            label: Optional custom label (overrides state)
        """
        logger.info(f"Setting fluxd action state: {state}")

        action_label = label or state
        self.action_state.state = action_label

        # Show progress indicator for download/stream states
        self.progress_indicator.visible = state in [
            "Downloading Chain",
            "Streaming Chain",
        ]

    def set_stream_initiated(self, stream_details: dict) -> None:
        """Handle stream initiated event.

        Args:
            stream_details: Stream details dict
        """
        last_details = {
            "response_received": False,
            "bytes": stream_details.get("total_bytes", 0),
            "timestamp": stream_details.get("start", perf_counter()),
        }

        logger.info("Byte logger starting")
        logger.info(f"starting bytes: {last_details['bytes']}")

        self.byte_logger(last_details, stream_details)

    @work(name="byte_logger", exclusive=True)
    async def byte_logger(
        self,
        last_details: dict,
        stream: dict,
    ) -> None:
        """Monitor stream progress and update progress indicator.

        Args:
            last_details: Dict tracking last update details
            stream: Stream details dict
        """
        done = stream.get("done", False)

        while not done:
            # Check if response started
            if not last_details["response_received"] and stream.get("started"):
                last_details["response_received"] = True
                self.progress_indicator.set_total(stream.get("approx_stream_size", 0))

            now = perf_counter()
            total_bytes = stream.get("total_bytes", 0)

            elapsed = now - last_details["timestamp"]
            transferred = total_bytes - last_details["bytes"]

            bps = (transferred / elapsed) * 8 if elapsed > 0 else 0
            mbps = round(bps / 1000 / 1000, 2)

            logger.info(
                f"Instantaneous Throughput: {mbps} Mbit/s, Queue length: {stream.get('qsize', 0)}"
            )

            self.progress_indicator.update(mbps, transferred)

            last_details["bytes"] = total_bytes
            last_details["timestamp"] = now

            try:
                await asyncio.sleep(self.update_interval_s)
            except asyncio.CancelledError:
                return

            # Update done status
            done = stream.get("done", False)

        if stream.get("error"):
            logger.error(f"Chain Stream error: {stream.get('error')}")

        logger.info("Byte logger complete")
        logger.info(f"Total Bytes: {stream.get('total_bytes', 0)}")

    def compute_online(self) -> bool:
        """Compute if service is online.

        Returns:
            True if service is active and running
        """
        return self.active_state == "active" and self.sub_state == "running"

    def watch_main_pid(self, old: int, new: int) -> None:
        """React to main PID changes.

        Args:
            old: Old PID
            new: New PID
        """
        if old == new:
            return

        self.online_indicator.main_pid = str(new)

        if new:
            self.blockcount.start()
        else:
            self.system_resources.reset()
            self.blockcount.stop()

    def watch_online(self, old: bool, new: bool) -> None:
        """React to online status changes.

        Args:
            old: Old status
            new: New status
        """
        if old == new:
            return

        self.online_indicator.online = new

        if not new:
            self.fluxd_status.status = "Unknown"

    def action_show_modal(self) -> None:
        """Action to show the modal."""
        self.post_message(self.ShowRpcModal())

    def on_click(self, event: Click) -> None:
        """Handle click events."""
        self.post_message(self.ShowRpcModal())
