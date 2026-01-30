"""Start Fluxnode modal screen for delegate key signing."""

from __future__ import annotations

import logging
from enum import StrEnum
from itertools import groupby
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Center, Container, Horizontal
from textual.css.query import NoMatches
from textual.reactive import var
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, LoadingIndicator, Markdown

if TYPE_CHECKING:
    from flux_config_tui.client_app import FluxConfigApp

logger = logging.getLogger(__name__)


class ModalState(StrEnum):
    """Modal display states."""

    LOADING = "loading"
    NOT_READY = "not_ready"
    NO_DELEGATE = "no_delegate"
    READY = "ready"


class ValidationState(StrEnum):
    """Password validation states."""

    IDLE = "idle"
    VALIDATING = "validating"
    VALIDATED = "validated"
    FAILED = "failed"
    SENDING = "sending"
    SUCCESS = "success"
    SEND_FAILED = "send_failed"


class StartFluxnodeModal(ModalScreen[None]):
    """Modal for starting Fluxnode with delegate key."""

    DEFAULT_CSS = """
    StartFluxnodeModal {
        align: center middle;
    }

    #start_fluxnode_container {
        width: 80;
        height: auto;
        max-height: 80%;
        border: solid $primary;
        border-title-align: center;
        padding: 1 2;
    }

    #message_label {
        text-align: center;
        padding: 1;
        margin-bottom: 1;
    }

    #message_markdown {
        padding: 1;
        margin-bottom: 1;
    }

    #message_markdown MarkdownParagraph {
        text-align: center;
    }

    .error {
        color: $error;
    }

    .success {
        color: $success;
    }

    .info {
        color: $text-muted;
    }

    #not_ready_message {
        color: $warning;
        margin-bottom: 1;
    }

    #not_ready_message MarkdownParagraph {
        text-align: center;
    }

    #password_input {
        margin: 1 0;
    }

    #validation_feedback {
        text-align: center;
        height: auto;
        min-height: 1;
        margin-bottom: 1;
    }

    #button_container {
        width: 100%;
        align: center middle;
        margin-top: 1;
    }

    #button_container Button {
        margin: 0 1;
    }

    #loading_indicator {
        height: 3;
        margin: 1 0;
    }

    #txid_label {
        text-align: center;
        padding: 1;
        background: $surface;
        margin: 1 0;
    }
    """

    state = var(ModalState.LOADING)
    validation_state = var(ValidationState.IDLE)
    password = var("")
    error_message = var("")
    txid = var("")

    @staticmethod
    def check_password_requirements(password: str) -> tuple[bool, str]:
        """Validate password meets requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 12:
            return False, "Password must be at least 12 characters"

        groups = groupby(password)
        for _, group in groups:
            if len(list(group)) > 3:
                return False, "Password cannot have more than 3 consecutive repeating characters"

        return True, ""

    def __init__(self) -> None:
        """Initialize Start Fluxnode modal screen."""
        super().__init__()
        self._daemon_synced = False
        self._benchmarks_passing = False
        self._delegate_configured = False

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        container = Container(id="start_fluxnode_container")
        container.border_title = "Start Fluxnode"

        with container:
            if self.state == ModalState.LOADING:
                yield Label("Checking node readiness...", id="message_label", classes="info")
                yield LoadingIndicator(id="loading_indicator")
                with Horizontal(id="button_container"):
                    yield Button("Cancel", id="cancel", variant="error")

            elif self.state == ModalState.NOT_READY:
                yield Markdown(
                    "The Flux daemon must be synced, and the node passing benchmarks "
                    "before you can start the node locally.",
                    id="not_ready_message",
                )
                with Horizontal(id="button_container"):
                    yield Button("Close", id="close", variant="primary")

            elif self.state == ModalState.NO_DELEGATE:
                yield Label(
                    "In order to start this node directly, you first need to send a "
                    "START transaction via your chosen wallet, where you provide the "
                    "public key of your delegate key. If you don't have a delegate key, "
                    "you can generate one on the 'Reconfigure Fluxnode' screen.",
                    id="message_label",
                    classes="info",
                )
                with Horizontal(id="button_container"):
                    yield Button("Close", id="close", variant="primary")

            elif self.state == ModalState.READY:
                yield from self._compose_ready_state()

    def _compose_ready_state(self) -> ComposeResult:
        """Compose the READY state UI."""
        if self.validation_state == ValidationState.SUCCESS:
            yield Label(
                "Transaction sent successfully!",
                id="message_label",
                classes="success",
            )
            yield Label(f"TXID: {self.txid}", id="txid_label")
            with Horizontal(id="button_container"):
                yield Button("Close", id="close", variant="primary")
            return

        if self.validation_state == ValidationState.SENDING:
            yield Label("Signing and sending transaction...", id="message_label", classes="info")
            yield LoadingIndicator(id="loading_indicator")
            return

        if self.validation_state == ValidationState.VALIDATING:
            yield Label("Decrypting delegate key...", id="message_label", classes="info")
            yield LoadingIndicator(id="loading_indicator")
            return

        yield Markdown(
            "Encrypted delegate key available. Enter your decryption "
            "password and validate it. You can then start this node.",
            id="message_markdown",
        )

        yield Input(
            placeholder="Enter decryption password (min 12 chars)",
            password=True,
            id="password_input",
        )

        feedback_classes = "info"
        feedback_text = ""

        if self.validation_state == ValidationState.FAILED:
            feedback_classes = "error"
            feedback_text = self.error_message or "Validation failed"
        elif self.validation_state == ValidationState.SEND_FAILED:
            feedback_classes = "error"
            feedback_text = self.error_message or "Failed to send transaction"
        elif self.validation_state == ValidationState.VALIDATED:
            feedback_classes = "success"
            feedback_text = "Password validated! Click Start to begin."

        yield Label(feedback_text, id="validation_feedback", classes=feedback_classes)

        with Horizontal(id="button_container"):
            yield Button("Cancel", id="cancel", variant="error")

            password_valid, _ = self.check_password_requirements(self.password)
            validate_disabled = (
                not password_valid or self.validation_state == ValidationState.VALIDATED
            )
            yield Button("Validate", id="validate", disabled=validate_disabled)

            start_disabled = self.validation_state != ValidationState.VALIDATED
            yield Button("Start", id="start", variant="primary", disabled=start_disabled)

    async def on_mount(self) -> None:
        """Check node readiness when screen mounts."""
        app: FluxConfigApp = self.app

        response = await app.backend_client.call_method("delegate.check_readiness", {})

        if response.error:
            logger.error("Error checking delegate readiness: %s", response.error)
            self.state = ModalState.NOT_READY
        elif response.result:
            self._daemon_synced = response.result.get("daemon_synced", False)
            self._benchmarks_passing = response.result.get("benchmarks_passing", False)
            self._delegate_configured = response.result.get("delegate_configured", False)

            if not self._daemon_synced or not self._benchmarks_passing:
                self.state = ModalState.NOT_READY
            elif not self._delegate_configured:
                self.state = ModalState.NO_DELEGATE
            else:
                self.state = ModalState.READY
        else:
            self.state = ModalState.NOT_READY

        await self.recompose()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle password input changes."""
        if event.input.id != "password_input":
            return

        self.password = event.value

        if self.validation_state in [
            ValidationState.VALIDATED,
            ValidationState.FAILED,
            ValidationState.SEND_FAILED,
        ]:
            self.validation_state = ValidationState.IDLE
            self.error_message = ""

        try:
            validate_btn = self.query_one("#validate", Button)
            password_valid, _ = self.check_password_requirements(self.password)
            validate_btn.disabled = not password_valid
        except NoMatches:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id in ["close", "cancel"]:
            self.dismiss()
            return

        if button_id == "validate":
            await self._verify_and_decrypt_key()
            return

        if button_id == "start":
            await self._start_node()

    async def _verify_and_decrypt_key(self) -> None:
        """Verify password by attempting to decrypt the delegate key."""
        password_valid, error_msg = self.check_password_requirements(self.password)
        if not password_valid:
            self.error_message = error_msg
            self.validation_state = ValidationState.FAILED
            await self.recompose()
            return

        self.validation_state = ValidationState.VALIDATING
        await self.recompose()

        app: FluxConfigApp = self.app

        response = await app.backend_client.call_method(
            "delegate.validate_password",
            {"password": self.password},
        )

        if response.error:
            self.error_message = str(response.error.message)
            self.validation_state = ValidationState.FAILED
        elif response.result:
            if response.result.get("success"):
                self.validation_state = ValidationState.VALIDATED
            else:
                error = response.result.get("error", "Unknown error")
                self.error_message = error
                self.validation_state = ValidationState.FAILED
        else:
            self.error_message = "No response from daemon"
            self.validation_state = ValidationState.FAILED

        await self.recompose()

    async def _start_node(self) -> None:
        """Send the start transaction."""
        self.validation_state = ValidationState.SENDING
        await self.recompose()

        app: FluxConfigApp = self.app

        response = await app.backend_client.call_method(
            "delegate.start_node",
            {"password": self.password},
        )

        if response.error:
            self.error_message = str(response.error.message)
            self.validation_state = ValidationState.SEND_FAILED
        elif response.result:
            if response.result.get("success"):
                self.txid = response.result.get("txid", "")
                self.validation_state = ValidationState.SUCCESS
            else:
                self.error_message = response.result.get("error", "Unknown error")
                self.validation_state = ValidationState.SEND_FAILED
        else:
            self.error_message = "No response from daemon"
            self.validation_state = ValidationState.SEND_FAILED

        await self.recompose()

    def watch_state(self, old: ModalState, new: ModalState) -> None:
        """React to state changes."""
        if old != new:
            logger.info("Modal state changed: %s -> %s", old, new)
