"""Label with Switch widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.dom import NoMatches
from textual.message import Message
from textual.reactive import var
from textual.widgets import Label, Switch


class LabelSwitch(Horizontal):
    """Widget combining a label with a switch control."""

    class Changed(Message):
        """Message emitted when switch value changes."""

        def __init__(self, switch: LabelSwitch, value: bool) -> None:
            """Initialize message.

            Args:
                switch: LabelSwitch that changed
                value: New switch value
            """
            super().__init__()

            self.switch = switch
            self.value = value

    DEFAULT_CSS = """
        LabelSwitch {
            height: auto;
            width: auto;
            &> Label {
                height: 3;
                content-align: center middle;
            }
        }
    """

    label = var("")
    value = var(False)

    def __init__(self, label: str, *, value: bool = True, id: str | None = None) -> None:
        """Initialize LabelSwitch.

        Args:
            label: Label text
            value: Initial switch value
            id: Widget ID
        """
        super().__init__(id=id)

        self._label = label
        self._value = value

    def compose(self) -> ComposeResult:
        """Compose the widget.

        Yields:
            Label and Switch widgets
        """
        yield Label(self._label)
        yield Switch(self._value)

    def on_mount(self) -> None:
        """Set initial reactive values on mount."""
        self.label = self._label
        self.value = self._value

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch change event.

        Args:
            event: Switch change event
        """
        event.stop()

        self.value = event.value
        self.post_message(LabelSwitch.Changed(self, event.value))

    def watch_label(self, old: str, new: str) -> None:
        """Watch for label text changes.

        Args:
            old: Old label text
            new: New label text
        """
        if old == new:
            return

        self._label = new

        try:
            label = self.query_one(Label)
        except NoMatches:
            return

        label.update(new)

    def watch_value(self, old: bool, new: bool) -> None:
        """Watch for switch value changes.

        Args:
            old: Old switch value
            new: New switch value
        """
        if old == new:
            return

        self._value = new

        try:
            switch = self.query_one(Switch)
        except NoMatches:
            return

        switch.value = new
