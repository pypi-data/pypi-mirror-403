"""Block count widget showing daemon and total block height."""

from __future__ import annotations

import logging

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import var
from textual.widgets import Label

logger = logging.getLogger(__name__)


class BlockCount(Horizontal):
    """Widget showing FluxD block count vs total network block count."""

    daemon_block_count = var(0)
    total_block_count = var(0)

    def __init__(self) -> None:
        """Initialize block count widget."""
        super().__init__()
        self.started = False
        self.block_count_validated = False

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield Label("Blocks: ")
        yield Label(str(self.daemon_block_count), id="daemon_block_count")
        yield Label(" / ")
        yield Label(str(self.total_block_count), id="total_block_count")

    def start(self) -> None:
        """Mark widget as started (block counts set via events)."""
        self.started = True

    def stop(self) -> None:
        """Stop and reset block counts."""
        self.started = False
        self.block_count_validated = False
        self.daemon_block_count = 0
        self.total_block_count = 0

    def update_daemon_block_count(self, block_count: int) -> None:
        """Update daemon block count from event.

        Args:
            block_count: New block count from daemon
        """
        if block_count and block_count > self.daemon_block_count:
            self.daemon_block_count = block_count
            self.block_count_validated = True
            logger.info(f"Daemon block count: {block_count}")

    def set_total_block_count(self, block_count: int) -> None:
        """Set total block count from API.

        Args:
            block_count: Total network block count from API
        """
        if block_count and block_count > self.total_block_count:
            self.total_block_count = block_count
            logger.info(f"Total block count from API: {block_count}")

    def watch_daemon_block_count(self, old: int, new: int) -> None:
        """React to daemon block count changes.

        Args:
            old: Old block count
            new: New block count
        """
        if old == new:
            return

        if new > self.total_block_count:
            self.total_block_count = new

        if self.is_mounted:
            try:
                self.query_one("#daemon_block_count", Label).update(str(new))
            except NoMatches as e:
                logger.warning("Failed to update daemon block count: %s", e)

    def watch_total_block_count(self, old: int, new: int) -> None:
        """React to total block count changes.

        Args:
            old: Old block count
            new: New block count
        """
        if old == new:
            return

        if self.is_mounted:
            try:
                self.query_one("#total_block_count", Label).update(str(new))
            except NoMatches as e:
                logger.warning("Failed to update total block count: %s", e)
