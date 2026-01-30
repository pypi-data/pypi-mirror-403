"""Textual message types for TUI communication."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from textual.message import Message


class SubscribeSystemdDbus(Message):
    """Message to subscribe to systemd D-Bus signals."""

    def __init__(
        self,
        unit_name: str,
        callback: Awaitable | Callable[[dict[str, str | int]], Any],
    ) -> None:
        super().__init__()

        self.unit_name = unit_name
        self.callback = callback


class FluxdRpcOnline(Message):
    """Message indicating FluxD RPC is online."""

    ...


class ScreenRequestedMessage(Message):
    """Message to request switching to a specific screen."""

    def __init__(self, screen: str) -> None:
        super().__init__()

        self.screen = screen
