"""Benchmark status widget for FluxBenchD."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import var
from textual.widgets import Label

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)


class BenchStates(StrEnum):
    """Benchmark states."""

    CUMULUS = "cumulus"
    NIMBUS = "nimbus"
    STRATUS = "stratus"


class BenchmarkStatus(Horizontal):
    """Widget showing FluxBenchD benchmark status.

    Event-driven: listens for FLUXBENCHD_STATUS_CHANGED events from daemon.
    Daemon polls getbenchmarks when blockchain topic has subscribers.
    """

    state = var("Unknown")

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield Label("Status: ")
        yield Label(self.state, id="state-label")

    def watch_state(self, old: str, new: str) -> None:
        """React to state changes.

        Args:
            old: Old state (lowercase)
            new: New state (lowercase)
        """
        if old == new:
            return

        try:
            display_value = new.title() if new and new != "Unknown" else new
            self.query_one("#state-label", Label).update(display_value)
        except NoMatches as e:
            logger.warning("Failed to update state label: %s", e)
