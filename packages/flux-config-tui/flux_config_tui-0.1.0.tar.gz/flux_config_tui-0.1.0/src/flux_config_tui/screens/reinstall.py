"""Reinstall components screen."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Grid, Horizontal
from textual.dom import NoMatches
from textual.reactive import var
from textual.screen import ModalScreen
from textual.widgets import Button, Markdown

from flux_config_tui.widgets.label_switch import LabelSwitch

DIALOG = """\
## Reinstall Fluxnode components here. This would usually be used \
to reinstall the Flux chain if it is corrupt. Only choose "all" \
as a last resort.

# Warning! If you reinstall fluxd, the chain will be deleted, and streamed.
"""


class ReinstallScreen(ModalScreen[list[str] | None]):
    """Modal screen for selecting components to reinstall."""

    BINDINGS = [Binding("escape", "dismiss", "Dismiss", show=False)]

    reinstall_all = var(False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize reinstall screen.

        Args:
            *args: Positional arguments for ModalScreen
            **kwargs: Keyword arguments for ModalScreen
        """
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose the screen.

        Yields:
            Grid with markdown dialog and component switches
        """
        with Grid():
            with Center(id="dialog"):
                yield Markdown(DIALOG)

            yield LabelSwitch("all ", id="all", value=False)
            yield LabelSwitch("fluxos ", id="fluxos", value=False)
            yield LabelSwitch("watchdog  ", id="flux-watchdog", value=False)
            yield LabelSwitch("    fluxd ", id="fluxd", value=False)
            with Horizontal(id="button-container"):
                yield Button("Cancel", id="cancel")
                yield Button("Install", id="install")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button press event
        """
        if event.button.id != "install":
            self.dismiss(None)
        else:
            switches = self.query(LabelSwitch)

            results: list[str] = []

            selected = [x.id for x in switches if x.id and x.id != "all" and x.value]

            # Services must be in this order - watchdog stopped first,
            # fluxos started after fluxd (for RPC credentials)
            if "flux-watchdog" in selected:
                results.append("flux-watchdog")

            if "fluxd" in selected:
                results.append("fluxd")

            if "fluxos" in selected:
                results.append("fluxos")

            self.dismiss(results)

    def on_label_switch_changed(self, event: LabelSwitch.Changed) -> None:
        """Handle label switch change.

        Args:
            event: Label switch change event
        """
        if event.switch.id == "all":
            self.reinstall_all = event.value

    def watch_reinstall_all(self, old: bool, new: bool) -> None:
        """Watch for changes to reinstall_all.

        Args:
            old: Old value
            new: New value
        """
        if old == new:
            return

        try:
            switches = self.query(LabelSwitch)
        except NoMatches:
            return

        # This will include the "all" switch as well, but it doesn't matter
        for switch in switches:
            switch.value = new
