"""QR code widget for displaying configuration URLs."""

from __future__ import annotations

import io

import qrcode
from textual.app import RenderResult
from textual.reactive import var
from textual.widgets import Static


class Qr(Static):
    """QR code widget."""

    DEFAULT_CSS = """
      Qr {
          border: solid $primary;
          width: auto;
          height: auto;
          margin: 0;
      }

    """
    text = var("")

    def __init__(self, text: str = "") -> None:
        """Initialize QR code widget.

        Args:
            text: Text to encode in QR code
        """
        self._qr = qrcode.QRCode(
            version=4,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        self._qr_out = io.StringIO()

        super().__init__()

        self.text = text

    def _read(self) -> str:
        """Read the QR code output.

        Returns:
            QR code as ASCII art
        """
        renderable = self._qr_out.read()
        self._qr_out.seek(0)
        return renderable

    def render(self) -> RenderResult:
        """Render the QR code.

        Returns:
            QR code ASCII art
        """
        return self._read()

    def watch_text(self, old: str, new: str) -> None:
        """Watch for text changes and regenerate QR code.

        Args:
            old: Old text value
            new: New text value
        """
        if old == new or not new:
            return

        # Only allow a max of 78 characters. Any more and it forces the QR bigger,
        # which breaks things. (and it doesn't go smaller again)
        data = str(new)[:78]

        self._qr.clear()
        self._qr.add_data(data)
        self._qr.print_ascii(out=self._qr_out)
        self._qr_out.seek(0)
        self.update()
