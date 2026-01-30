"""Service metrics widget showing status of multiple services."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Grid
from textual.reactive import var
from textual.widgets import Label

from .online_indicator import OnlineIndicator

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)


class ServiceMetrics(Grid):
    """Service metrics widget showing status of syncthing, docker, and mongod."""

    BORDER_TITLE = "Service Metrics"

    # Service states
    main_pid_syncthing = var(0)
    active_state_syncthing = var("unknown")
    sub_state_syncthing = var("unknown")
    online_syncthing = var(False)

    main_pid_docker = var(0)
    active_state_docker = var("unknown")
    sub_state_docker = var("unknown")
    online_docker = var(False)

    main_pid_mongod = var(0)
    active_state_mongod = var("unknown")
    sub_state_mongod = var("unknown")
    online_mongod = var(False)

    longest_pid_len = var(0)

    def __init__(self) -> None:
        """Initialize service metrics widget."""
        super().__init__()
        self.syncthing = OnlineIndicator()
        self.docker = OnlineIndicator()
        self.mongod = OnlineIndicator()

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield Label("Syncthing: ")
        yield self.syncthing
        yield Label("Docker: ")
        yield self.docker
        yield Label("Mongod: ")
        yield self.mongod

    def set_state(
        self, service: str, main_pid: int, active_state: str, sub_state: str
    ) -> None:
        """Set service state from SERVICE_STATE_CHANGED event (replaces polling).

        Args:
            service: Service name (e.g., "docker.service")
            main_pid: Process ID
            active_state: Active state (active, inactive, etc.)
            sub_state: Sub state (running, dead, etc.)
        """
        # Extract suffix from service name (e.g., "docker.service" -> "docker")
        suffix = service.removesuffix(".service")

        # Update reactive variables - watchers will handle UI updates
        setattr(self, f"main_pid_{suffix}", main_pid)
        setattr(self, f"active_state_{suffix}", active_state)
        setattr(self, f"sub_state_{suffix}", sub_state)

    def pad_pids(self) -> None:
        """Pad PIDs to align them nicely."""
        longest = self.longest_pid_len

        syncthing = str(self.main_pid_syncthing)
        docker = str(self.main_pid_docker)
        mongod = str(self.main_pid_mongod)

        self.syncthing.main_pid = syncthing.ljust(longest)
        self.docker.main_pid = docker.ljust(longest)
        self.mongod.main_pid = mongod.ljust(longest)

    def compute_online_syncthing(self) -> bool:
        """Compute if syncthing is online."""
        return self.active_state_syncthing == "active" and self.sub_state_syncthing == "running"

    def compute_online_docker(self) -> bool:
        """Compute if docker is online."""
        return self.active_state_docker == "active" and self.sub_state_docker == "running"

    def compute_online_mongod(self) -> bool:
        """Compute if mongod is online."""
        return self.active_state_mongod == "active" and self.sub_state_mongod == "running"

    def compute_longest_pid_len(self) -> int:
        """Compute longest PID length for padding."""
        return max(
            len(str(self.main_pid_syncthing)),
            len(str(self.main_pid_docker)),
            len(str(self.main_pid_mongod)),
        )

    def watch_longest_pid_len(self, old: int, new: int) -> None:
        """React to longest PID length changes."""
        if old == new:
            return
        self.pad_pids()

    def watch_main_pid_syncthing(self, old: int, new: int) -> None:
        """React to syncthing PID changes."""
        if old == new:
            return
        self.syncthing.main_pid = str(new).ljust(self.longest_pid_len)

    def watch_main_pid_docker(self, old: int, new: int) -> None:
        """React to docker PID changes."""
        if old == new:
            return
        self.docker.main_pid = str(new).ljust(self.longest_pid_len)

    def watch_main_pid_mongod(self, old: int, new: int) -> None:
        """React to mongod PID changes."""
        if old == new:
            return
        self.mongod.main_pid = str(new).ljust(self.longest_pid_len)


    def watch_online_syncthing(self, old: bool, new: bool) -> None:
        """React to syncthing online status changes."""
        if old == new:
            return
        self.syncthing.online = new

    def watch_online_docker(self, old: bool, new: bool) -> None:
        """React to docker online status changes."""
        if old == new:
            return
        self.docker.online = new

    def watch_online_mongod(self, old: bool, new: bool) -> None:
        """React to mongod online status changes."""
        if old == new:
            return
        self.mongod.online = new
