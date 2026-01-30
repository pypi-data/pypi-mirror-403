"""Progress indicator widget for download/stream operations."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.widgets import Label, ProgressBar


class ProgressIndicator(Grid):
    """Widget showing download/stream progress with throughput."""

    def __init__(self) -> None:
        """Initialize progress indicator."""
        super().__init__()
        self.total_bytes = 0
        self.transferred_bytes = 0
        self.progress_bar = ProgressBar()
        self.progress_throughput = Label("0.00 Mbit/s", id="progress-throughput")

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield Label("     Chain Download Progress")
        with Horizontal():
            yield Label("Rate:")
            yield self.progress_throughput
        yield self.progress_bar

    def on_mount(self) -> None:
        """Update progress bar when mounted."""
        if self.total_bytes:
            self.progress_bar.update(total=self.total_bytes, progress=self.transferred_bytes)

    def reset(self) -> None:
        """Reset progress to zero."""
        self.total_bytes = 0
        self.transferred_bytes = 0
        self.progress_bar.update(total=None, progress=0)

    def set_total(self, total: int) -> None:
        """Set total bytes for progress bar.

        Args:
            total: Total bytes to download
        """
        self.total_bytes = total
        if self.is_mounted:
            self.progress_bar.update(total=total, progress=0)

    def update(self, throughput: float, increment: int) -> None:
        """Update progress with new throughput and bytes transferred.

        Args:
            throughput: Current throughput in Mbit/s
            increment: Bytes transferred since last update
        """
        self.transferred_bytes += increment

        if self.is_mounted:
            self.progress_throughput.update(f"{throughput} Mbit/s")
            self.progress_bar.advance(increment)
