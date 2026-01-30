"""System resources widget showing CPU and memory usage for a process."""

from __future__ import annotations

import logging

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import var
from textual.widgets import Label

logger = logging.getLogger(__name__)


class SystemResources(Horizontal):
    """Widget showing CPU and memory usage for a process."""

    IEC = [
        (1024**5, "P"),
        (1024**4, "T"),
        (1024**3, "G"),
        (1024**2, "M"),
        (1024**1, "K"),
        (1, "B"),
    ]

    cpu = var(0.0)
    mem = var(0.0)

    def __init__(self, process_name: str = "") -> None:
        """Initialize system resources widget.

        Args:
            process_name: Name of process to monitor (used for event matching)
        """
        super().__init__()
        self.process_name = process_name

    @staticmethod
    def human_size(target: float, units: list | None = None) -> str:
        """Convert bytes to human-readable size.

        Args:
            target: Size in bytes
            units: List of (factor, suffix) tuples

        Returns:
            Human-readable size string
        """
        if units is None:
            units = SystemResources.IEC

        for factor, suffix in units:  # noqa: B007
            if target >= factor:
                break

        amount = round(target / factor, 2)
        return str(amount) + suffix

    @property
    def cpu_human_readable(self) -> str:
        """Get CPU usage as human-readable string."""
        return f"{round(self.cpu, 2)}%".ljust(6)

    @property
    def mem_human_readable(self) -> str:
        """Get memory usage as human-readable string."""
        return f"{self.human_size(self.mem)}".ljust(7)

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield Label("Cpu:")
        yield Label(self.cpu_human_readable, id="cpu")
        yield Label("Mem:")
        yield Label(self.mem_human_readable, id="mem")

    def update_stats(self, rss_bytes: float = 0.0, cpu_percent: float = 0.0) -> None:
        """Update resource stats from metrics event.

        Args:
            rss_bytes: Memory RSS in bytes
            cpu_percent: CPU usage percentage
        """
        self.mem = rss_bytes
        self.cpu = cpu_percent

    def reset(self) -> None:
        """Reset resource values to zero."""
        self.cpu = 0.0
        self.mem = 0.0

    def watch_cpu(self, old: float, new: float) -> None:
        """React to CPU changes.

        Args:
            old: Old CPU value
            new: New CPU value
        """
        if old == new:
            return

        if self.is_mounted:
            try:
                self.query_one("#cpu", Label).update(self.cpu_human_readable)
            except NoMatches as e:
                logger.warning("Failed to update CPU label: %s", e)

    def watch_mem(self, old: float, new: float) -> None:
        """React to memory changes.

        Args:
            old: Old memory value
            new: New memory value
        """
        if old == new:
            return

        if self.is_mounted:
            try:
                self.query_one("#mem", Label).update(self.mem_human_readable)
            except NoMatches as e:
                logger.warning("Failed to update memory label: %s", e)
