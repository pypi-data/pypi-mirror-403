"""Simple loading screen for initialization."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widgets import Label, Static


class LoadingIndicator(Static):
    """Animated loading indicator with fixed-width dot animation.

    Ported from original implementation which uses a gradient-based
    5-dot indicator with constant width to prevent text shifting.
    """

    def __init__(self, message: str = "Loading") -> None:
        """Initialize loading indicator.

        Args:
            message: Loading message to display
        """
        super().__init__()
        self._message = message
        self._frame = 0

    def on_mount(self) -> None:
        """Start animation when mounted."""
        self.update_display()
        self.set_interval(0.4, self.animate)

    def animate(self) -> None:  # type: ignore[override]
        """Animate the loading indicator by advancing the frame."""
        self._frame = (self._frame + 1) % 5
        self.update_display()

    def update_display(self) -> None:
        """Update the display with animated indicator.

        Creates a fixed-width indicator with 5 dots where one dot
        cycles through positions. This matches the original behavior
        which used gradient colors on fixed-width dots.
        """
        # Create fixed-width indicator with 5 dots (9 chars: "○ ○ ○ ○ ○")
        dots = ["○"] * 5
        dots[self._frame] = "●"
        indicator = " ".join(dots)

        # Display message with fixed-width indicator below
        self.update(f"{self._message}\n{indicator}")

    def set_message(self, message: str) -> None:
        """Change the loading message.

        Args:
            message: New message to display
        """
        self._message = message
        self.update_display()


class LoadingScreen(Screen):
    """Loading screen shown during initialization."""

    DEFAULT_CSS = """
    LoadingScreen {
        align: center middle;
    }

    LoadingScreen > Center > Middle {
        width: auto;
        height: auto;
    }

    LoadingScreen Label {
        text-align: center;
        padding: 1 2;
    }

    LoadingIndicator {
        text-align: center;
        color: $accent;
        text-style: bold;
        padding: 1 2;
    }
    """

    def __init__(self, message: str = "Initializing Flux Configuration System") -> None:
        """Initialize loading screen.

        Args:
            message: Initial loading message
        """
        super().__init__()
        self._message = message
        self._indicator: LoadingIndicator | None = None

    def compose(self) -> ComposeResult:
        """Compose the loading screen UI."""
        with Center():
            with Middle():
                yield Label("[bold]Flux Configuration System[/bold]")
                self._indicator = LoadingIndicator(self._message)
                yield self._indicator

    def set_loading_message(self, message: str) -> None:
        """Update the loading message.

        Args:
            message: New message to display
        """
        if self._indicator:
            self._indicator.set_message(message)
