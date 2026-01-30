import os
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static
from textual_fspicker import FileOpen, Filters


class SetupScreen(Screen):
    """Setup screen for SSH key configuration using file browser."""

    CSS = """
    SetupScreen {
        align: center middle;
    }

    #setup-container {
        width: 80;
        height: auto;
        border: solid green;
        padding: 2;
    }

    .setup-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .setup-help {
        margin-bottom: 2;
    }

    #selected-key-label {
        margin-top: 1;
        margin-bottom: 1;
        color: $accent;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.selected_key_path: str | None = None

    def compose(self) -> ComposeResult:
        with Container(id="setup-container"):
            yield Static("SSH Key Configuration Required", classes="setup-title")
            yield Static(
                "Remote access requires SSH key authentication.\n"
                "Click 'Browse' to select your SSH private key file:",
                classes="setup-help",
            )
            yield Label("No key selected", id="selected-key-label")
            yield Label("", id="error-label")
            with Vertical():
                yield Button("Browse for SSH Key...", variant="primary", id="browse-button")
                yield Button("Use Auto-Detected Key", variant="default", id="auto-button")
                yield Button("Cancel", variant="error", id="cancel-button")

    @on(Button.Pressed, "#browse-button")
    @work
    async def open_file_browser(self) -> None:
        """Open file browser for SSH key selection."""
        ssh_key_filters = Filters(
            ("SSH Keys", lambda p: p.suffix in ("", ".pem", ".pub") or p.name.startswith("id_")),
            ("All Files", lambda p: True),
        )

        start_dir = Path.home() / ".ssh"
        if not start_dir.exists():
            start_dir = Path.home()

        selected_file = await self.app.push_screen_wait(
            FileOpen(
                location=start_dir,
                filters=ssh_key_filters,
            )
        )

        if selected_file:
            # FileOpen returns a Path object
            selected_path = Path(selected_file) if not isinstance(selected_file, Path) else selected_file
            self.selected_key_path = str(selected_path)
            self.query_one("#selected-key-label", Label).update(f"Selected: {self.selected_key_path}")
            self.query_one("#error-label", Label).update("")

            self.save_config(self.selected_key_path)

    @on(Button.Pressed, "#auto-button")
    def use_auto_detected_key(self) -> None:
        """Use auto-detected SSH key."""
        auto_key = self.detect_default_key()
        if auto_key:
            self.selected_key_path = auto_key
            self.query_one("#selected-key-label", Label).update(f"Using auto-detected: {auto_key}")
            self.save_config(auto_key)
        else:
            self.query_one("#error-label", Label).update(
                "Error: No SSH key found in common locations"
            )

    @on(Button.Pressed, "#cancel-button")
    def cancel_setup(self) -> None:
        """Cancel setup and exit."""
        self.app.exit()

    def detect_default_key(self) -> str | None:
        """Auto-detect SSH key from common locations."""
        common_keys = [
            "~/.ssh/id_ed25519",
            "~/.ssh/id_rsa",
            "~/.ssh/id_ecdsa",
            "~/.ssh/operator_ed25519",
        ]

        for key_path in common_keys:
            expanded = os.path.expanduser(key_path)
            if Path(expanded).exists():
                return expanded

        return None

    def save_config(self, key_path: str) -> None:
        """Validate and save SSH key configuration to XDG config file."""
        from flux_config_tui.config import TUIConfig

        if not Path(key_path).exists():
            self.query_one("#error-label", Label).update(f"Error: Key not found at {key_path}")
            return

        config = TUIConfig.load()
        if "ssh" not in config:
            config["ssh"] = {}
        config["ssh"]["key_path"] = key_path
        TUIConfig.save(config)

        self.dismiss(key_path)
