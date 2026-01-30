"""Theme and configuration providers for the TUI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.screen import Screen
from textual.widgets import Label

if TYPE_CHECKING:
    from textual.app import ComposeResult


class ThemeProvider(Screen[None]):
    """Screen for theme selection and customization."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the theme provider screen."""
        yield Label("Theme customization coming soon...")
