"""Flux Config TUI - Pure Event-Driven Client Application.

This TUI is a thin display layer that:
- Connects to the flux-configd daemon via WebSocket
- Receives all application state from daemon via events
- Updates UI based on events (INITIAL_STATE, SYSTEM_METRICS_UPDATE, etc.)
- Sends RPC commands for user actions (NO business logic)

All business logic runs in the daemon. The TUI is purely reactive.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import os
import sys
import time
from collections.abc import Awaitable, Callable
from os import environ
from typing import TYPE_CHECKING, Any

from setproctitle import setproctitle
from textual import on, work
from textual.app import App
from textual.await_complete import AwaitComplete
from textual.reactive import Reactive, var
from yarl import URL

from flux_config_shared.config_locations import ConfigLocations
from flux_config_shared.daemon_state import (
    ConnectivityStatus,
    DaemonPhase,
    DaemonState,
    DatMountStatus,
)
from flux_config_shared.log import configure_logging
from flux_config_shared.protocol import Event, EventType, InstallState, MethodName, UpgradeStateData
from flux_config_shared.user_config import InstallerProvidedConfig, UserProvidedConfig
from flux_config_tui.client import BackendClient, ConnectionState
from flux_config_tui.messages import ScreenRequestedMessage
from flux_config_tui.providers import ThemeProvider
from flux_config_tui.screens.activate_launch import ActivateLaunchScreen
from flux_config_tui.screens.app_settings import AppSettingsScreen
from flux_config_tui.screens.firewall_rules import FirewallRulesScreen
from flux_config_tui.screens.upnp_mappings import UpnpMappingsScreen
from flux_config_tui.screens.launch import LaunchScreen
from flux_config_tui.screens.loading import LoadingScreen
from flux_config_tui.screens.log_viewer import LogViewerScreen
from flux_config_tui.screens.settings import SettingsScreen
from flux_config_tui.screens.shutdown import ShutdownScreen
from flux_config_tui.screens.start_fluxnode_modal import StartFluxnodeModal
from flux_config_tui.screens.system_metrics import SystemMetrics
from flux_config_tui.widgets.launchpad import LaunchPad

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Loading message mappings (daemon phase, waiting_for) -> message
LOADING_MESSAGES: dict[tuple[str, frozenset[str]] | str, str] = {
    # Initial connection
    ("initializing", frozenset()): "Connecting to daemon...",
    # System initialization phase
    ("system_initialization", frozenset()): "Initializing system...",
    ("system_initialization", frozenset(["connectivity_validated"])): "Checking network connectivity...",
    ("system_initialization", frozenset(["dat_mounted"])): "Initializing system...",
    # Application initialization phase
    ("application_initialization", frozenset()): "Loading configuration...",
    # Node synchronization phase
    ("node_synchronization", frozenset()): "Initializing system...",
    ("node_synchronization", frozenset(["dat_mounted"])): "Waiting for data crypt to mount...",
    ("node_synchronization", frozenset(["db_state_populated"])): "Loading system state...",
    ("node_synchronization", frozenset(["connectivity_validated"])): "Verifying network connectivity...",
    # Multiple waits - provide fallback for common combinations
    ("node_synchronization", frozenset(["dat_mounted", "connectivity_validated"])): "Initializing system...",
    # Fallback for any unmatched state
    "default": "Loading...",
}

# Timeout escalation messages (TUI decides when to show these)
TIMEOUT_MESSAGES: dict[str, str] = {
    "dat_mounted_5s": "It's taking longer than expected to mount the data crypt...",
}

# Map task operations to action states
# Service name comes from event.data["service"] to determine which widget to update
TASK_ACTION_STATE_MAP: dict[str, tuple[str, bool]] = {
    # Task operation -> (Action State Label, Show Progress Indicator)
    # FluxD blockchain tasks
    "download_chain": ("Downloading Chain", True),
    "fetch_params": ("Fetching Flux Params", False),
    "verify_chain": ("Verifying Chain", False),
    "create_config": ("Waiting for Config", False),
    # FluxOS tasks (for future use)
    "clone_repo": ("Cloning", False),
    "install_modules": ("Installing", False),
}


class FluxConfigApp(App[None]):
    """Flux Config TUI Application - Pure Event-Driven Client.

    This app has ZERO business logic. All application state comes from
    the daemon via events. User actions are sent to daemon via RPC.
    """

    CSS_PATH = "flux_config_tui.tcss"
    TITLE = "Flux Config"
    AUTO_FOCUS = None
    ENABLE_COMMAND_PALETTE = False

    # Reactive vars for service states (updated from daemon events)
    fluxd_installed: Reactive[bool] = var(False)
    fluxd_online: Reactive[bool] = var(False)
    fluxbenchd_installed: Reactive[bool] = var(False)
    fluxos_installed: Reactive[bool] = var(False)
    syncthing_installed: Reactive[bool] = var(False)
    flux_watchdog_installed: Reactive[bool] = var(False)

    def __init__(
        self,
        connection_string: str,
        api_key: str | None = None,
        ssh_key_path: str | None = None,
        needs_setup: bool = False,
    ) -> None:
        """Initialize the TUI application.

        Args:
            connection_string: Connection string (unix://, ws://, ssh://)
            api_key: Optional API key for authentication
            ssh_key_path: SSH key path for SSH connections
            needs_setup: Whether setup screen is needed
        """
        super().__init__()

        self.connection_string = connection_string
        self.api_key = api_key
        self.ssh_key_path = ssh_key_path
        self.needs_setup = needs_setup

        self.backend_client: BackendClient | None = None

        # Connection state tracking
        self.connection_state = ConnectionState.DISCONNECTED
        self.backend_connected = asyncio.Event()

        # Configuration objects (received from daemon)
        self.installer_config: InstallerProvidedConfig | None = None
        self.user_config: UserProvidedConfig | None = None

        self._pending_webserver_details: dict[str, Any] | None = None
        self._pending_tunnel_state: dict[str, Any] | None = None

        # System information (updated from daemon events)
        self.blockheight: int | None = None
        self.public_ip: str | None = None
        self.local_ip: str | None = None

        # Installation and upgrade states (from daemon)
        self.install_state: InstallState = InstallState.UNKNOWN
        self.upgrade_state: UpgradeStateData = UpgradeStateData()

        # Service start timestamps (for UI display only)
        self.fluxd_started_at: float | None = None
        self.fluxbenchd_started_at: float | None = None
        self.fluxos_started_at: float | None = None
        self.syncthing_started_at: float | None = None
        self.flux_watchdog_started_at: float | None = None

        # Reconfiguration state (from daemon)
        self.reconfigure_mode: str | None = None
        self.reconfiguring_fluxnode = False

        # Network shaping policy data (from daemon)
        self.shaping_policy: dict[str, Any] | None = None

        # Loading screen state tracking
        self._loading_screen_active: bool = False

        # Display configuration
        self.current_resolution = environ.get("UI_RES")

        # Application state flags
        self.shutting_down = False
        self.network_connected = False

        # Keyboard input tracking (for shutdown sequence)
        self.stored_keys: list[str] = []

        # Unified daemon state (new state model)
        self._daemon_state: DaemonState | None = None

    def install_screen(self, screen: Any, name: str) -> None:
        logger.info(f"TUI: Installing screen '{name}'")
        super().install_screen(screen, name)

    def uninstall_screen(self, screen: Any) -> None:
        screen_name = screen if isinstance(screen, str) else getattr(screen, "name", "unknown")
        logger.info(f"TUI: Uninstalling screen '{screen_name}'")
        super().uninstall_screen(screen)

    def push_screen(self, screen: Any, callback: Any = None, **kwargs: Any) -> Any:
        screen_name = screen.__class__.__name__
        logger.info(f"TUI: Pushing screen '{screen_name}'")
        if callback:
            return super().push_screen(screen, callback, **kwargs)
        else:
            return super().push_screen(screen, **kwargs)

    def pop_screen(self) -> AwaitComplete:
        logger.info("TUI: Popping screen")
        return super().pop_screen()

    def switch_screen(self, screen: Any) -> None:
        screen_name = screen if isinstance(screen, str) else getattr(screen, "name", "unknown")
        logger.info(f"TUI: Switching to screen '{screen_name}'")
        super().switch_screen(screen)

    async def on_mount(self) -> None:
        """Mount the application and connect to daemon."""
        logger.info("TUI starting - connecting to daemon")

        metrics = SystemMetrics()
        if self.install_state == InstallState.COMPLETE:
            metrics.enable_shell = True
            metrics.enable_logs = True
        self.install_screen(metrics, "system_metrics")

        self.push_screen(LoadingScreen("Loading..."))

        # Start connection in worker (handles setup screen if needed)
        self._connect_to_daemon()

    @work(exclusive=True)
    async def _connect_to_daemon(self) -> None:
        """Connect to daemon (runs in worker context for setup screen)."""
        if self.needs_setup:
            from flux_config_tui.screens.setup import SetupScreen

            ssh_key = await self.push_screen_wait(SetupScreen())
            if not ssh_key:
                self.exit()
                return

            self.ssh_key_path = ssh_key

        self.backend_client = BackendClient(
            connection_string=self.connection_string,
            api_key=self.api_key,
            ssh_key_path=self.ssh_key_path,
        )

        self._register_event_handlers()

        try:
            await self.backend_client.connect()
            self.backend_connected.set()
            logger.info("Connected to daemon, waiting for initial state...")

            # Subscribe to all topics to receive events
            # Without subscription, topic-based events are not broadcast to this client
            try:
                result = await self.backend_client.subscribe_all()
                subscribed_topics = result.get("subscribed", [])
                logger.info(f"Subscribed to topics: {subscribed_topics}")

                # Process initial state from subscription to set action states for active tasks
                subscription_state = result.get("state", {})
                await self._process_subscription_state(subscription_state)
            except Exception as sub_error:
                logger.error(f"Failed to subscribe to topics: {sub_error}", exc_info=True)
                # Non-fatal - TUI can still function via RPC calls

        except Exception as e:
            logger.error(f"Failed to connect to daemon: {e}")
            self.exit(message=f"Failed to connect to daemon: {e}")

    def _determine_current_screen(self) -> str:
        """Determine which screen to display based on current state.

        Returns:
            Screen name: "loading", "launch", "activate_launch", or "system_metrics"
        """
        # Use unified state model
        if self._daemon_state:
            phase = self._daemon_state.get("phase")

            # Check daemon phase enum
            if isinstance(phase, DaemonPhase):
                # Daemon is still initializing
                if phase == DaemonPhase.INITIALIZING:
                    return "loading"

                # Daemon encountered fatal error
                if phase == DaemonPhase.ERROR:
                    return "shutdown"

                # Daemon is RUNNING - fall through to config-based logic

        # Daemon is running - determine screen based on configuration state

        # Need configuration? Show launch screen
        if self.reconfigure_mode == "now" or not self.user_config:
            return "launch"

        # Deferred reconfiguration? Show activate screen
        if self.reconfigure_mode == "later":
            return "activate_launch"

        # Normal operation - show metrics
        return "system_metrics"

    async def _sync_screen_with_state(self) -> None:
        """Ensure displayed screen matches current domain state.

        This method should be called whenever state changes that might
        affect which screen should be displayed (install_state, reconfigure_mode,
        user_config, etc.).
        """
        # Check for fatal error first - takes precedence over all other screens
        fatal_error = None
        if self._daemon_state and "system_status" in self._daemon_state:
            fatal_error = self._daemon_state["system_status"].get("fatal_error")

        if fatal_error:
            logger.info(f"Fatal error present, showing shutdown screen: {fatal_error.get('error')}")
            shutdown_screen = ShutdownScreen(
                label_text=fatal_error.get("message", "System error occurred"),
                firmware_option=True,
                cancel_option=False,
            )
            self.install_screen(shutdown_screen, "shutdown")
            result = self.switch_screen("shutdown")
            if result is not None:
                await result
            return

        desired_screen = self._determine_current_screen()

        logger.info(f"Syncing screen to state: desired={desired_screen}, current_stack={len(self.screen_stack)}")

        # Show desired screen
        if desired_screen == "loading":
            message = self._get_loading_message()
            await self._show_loading(message)
        elif desired_screen == "launch":
            await self._show_launch_screen()

            if self._pending_webserver_details:
                logger.info("Applying stored webserver details to launch screen")
                await self._apply_webserver_details(
                    host=self._pending_webserver_details.get("host"),
                    port=self._pending_webserver_details.get("port"),
                    token=self._pending_webserver_details.get("token"),
                )
                self._pending_webserver_details = None

            if self._pending_tunnel_state:
                logger.info("Applying stored tunnel state to launch screen")
                await self._apply_tunnel_state(self._pending_tunnel_state)
                self._pending_tunnel_state = None
        elif desired_screen == "activate_launch":
            await self._show_activate_launch_screen()
        elif desired_screen == "system_metrics":
            await self._show_system_metrics()

            metrics = self.get_screen("system_metrics", SystemMetrics)
            complete = self.install_state == InstallState.COMPLETE
            metrics.show_back = not complete and self.is_screen_installed("launch")

    def _register_event_handlers(self) -> None:
        """Register handlers for all daemon events."""
        # Initial state synchronization (sent on connect)
        self.backend_client.on_event(EventType.INITIAL_STATE, self._handle_initial_state)

        # Unified state updates (new state model)
        self.backend_client.on_event(EventType.STATE_UPDATE, self._handle_state_update)

        # Periodic metrics updates (every 5 seconds)
        self.backend_client.on_event(EventType.SYSTEM_METRICS_UPDATE, self._handle_metrics_update)

        # Installation state changes
        self.backend_client.on_event(
            EventType.INSTALL_STATE_CHANGED, self._handle_install_state_changed
        )

        # Service state changes
        self.backend_client.on_event(
            EventType.SERVICE_STATE_CHANGED, self._handle_service_state_changed
        )
        self.backend_client.on_event(
            EventType.SERVICE_STATES_READY, self._handle_service_states_ready
        )

        # FluxD events
        self.backend_client.on_event(EventType.FLUXD_RPC_ONLINE, self._handle_fluxd_rpc_online)
        self.backend_client.on_event(EventType.FLUXD_RPC_OFFLINE, self._handle_fluxd_rpc_online)
        self.backend_client.on_event(EventType.FLUXD_BLOCK_HEIGHT, self._handle_fluxd_block_height)
        self.backend_client.on_event(EventType.FLUXD_ZMQ_NEW_BLOCK, self._handle_fluxd_zmq_new_block)
        self.backend_client.on_event(EventType.FLUXD_STATUS_CHANGED, self._handle_fluxd_status_changed)
        self.backend_client.on_event(EventType.FLUXBENCHD_STATUS_CHANGED, self._handle_fluxbenchd_status_changed)

        # Upgrade events
        self.backend_client.on_event(EventType.UPGRADE_STARTED, self._handle_upgrade_started)
        self.backend_client.on_event(EventType.UPGRADE_PROGRESS, self._handle_upgrade_progress)
        self.backend_client.on_event(EventType.UPGRADE_COMPLETED, self._handle_upgrade_completed)

        # System events
        self.backend_client.on_event(
            EventType.SYSTEM_CONNECTIVITY, self._handle_system_connectivity
        )
        self.backend_client.on_event(EventType.SYSTEM_PUBLIC_IP, self._handle_system_public_ip)
        self.backend_client.on_event(EventType.SYSTEM_ERROR, self._handle_system_error)
        self.backend_client.on_event(
            EventType.NETWORK_CONFIG_REQUIRED, self._handle_network_config_required
        )
        self.backend_client.on_event(
            EventType.INSUFFICIENT_SPACE, self._handle_insufficient_space
        )

        # Installation task events
        self.backend_client.on_event(
            EventType.DOWNLOAD_PROGRESS, self._handle_download_progress
        )
        self.backend_client.on_event(
            EventType.INSTALL_TASK_STARTED, self._handle_install_task_started
        )
        self.backend_client.on_event(
            EventType.INSTALL_TASK_COMPLETED, self._handle_install_task_completed
        )
        self.backend_client.on_event(
            EventType.INSTALL_TASK_FAILED, self._handle_install_task_failed
        )

        # Webserver events
        self.backend_client.on_event(EventType.WEBSERVER_STARTED, self._handle_webserver_started)

        # Tunnel events
        self.backend_client.on_event(EventType.TUNNEL_CONNECTING, self._handle_tunnel_connecting)
        self.backend_client.on_event(EventType.TUNNEL_STARTED, self._handle_tunnel_started)
        self.backend_client.on_event(EventType.TUNNEL_STOPPED, self._handle_tunnel_stopped)
        self.backend_client.on_event(EventType.TUNNEL_ERROR, self._handle_tunnel_error)

        logger.info("Event handlers registered")

    # ========================================================================
    # Loading Screen Management
    # ========================================================================

    async def _show_loading(self, message: str) -> None:
        """Show or update loading screen with message.

        Args:
            message: Loading message to display
        """
        if not self._loading_screen_active:
            logger.info(f"TUI: Showing loading screen: {message}")
            self.push_screen(LoadingScreen(message))
            self._loading_screen_active = True
        else:
            logger.info(f"TUI: Updating loading screen: {message}")
            try:
                screen = self.screen
                if isinstance(screen, LoadingScreen):
                    screen.set_loading_message(message)
            except Exception:
                pass

    async def _dismiss_loading(self) -> None:
        """Dismiss loading screen if active."""
        if self._loading_screen_active:
            logger.info("TUI: Dismissing loading screen")
            self._loading_screen_active = False
            # Loading screen will be replaced by switch_screen()

    def _get_loading_message(self) -> str:
        """Get appropriate loading message for current daemon state.

        Business logic: TUI decides what to display based on daemon state.
        Uses unified state model with timestamp-based delayed detection
        and enum-based status checks.

        Returns:
            Loading message string
        """
        # Use unified state model
        if self._daemon_state and "system_status" in self._daemon_state:
            status = self._daemon_state["system_status"]

            # Check /dat mount status (typically the longest operation)
            dat_status = status.get("dat_mount_status")
            if isinstance(dat_status, DatMountStatus):
                if dat_status == DatMountStatus.MOUNTING:
                    return "Waiting for data crypt to mount..."

                if dat_status == DatMountStatus.DELAYED:
                    return "It's taking longer than expected to mount the data crypt..."

                if dat_status == DatMountStatus.FAILED:
                    return status.get("dat_mount_error") or "Failed to mount data crypt"

            # Check connectivity status
            conn_status = status.get("connectivity_status")
            if isinstance(conn_status, ConnectivityStatus):
                if conn_status == ConnectivityStatus.CHECKING:
                    return "Verifying network connectivity..."

                if conn_status == ConnectivityStatus.FAILED:
                    return status.get("connectivity_error") or "Network connectivity failed"

            # Check database population
            if not status.get("db_populated", True):
                return "Loading system state..."

            # Check blocked_on list for specific operations
            if "initialization" in self._daemon_state:
                blocked_on = self._daemon_state["initialization"].get("blocked_on", [])
                if blocked_on:
                    operation_messages = {
                        "dat_mounted": "Waiting for data crypt...",
                        "db_state_populated": "Loading system state...",
                        "connectivity_validated": "Checking network...",
                        "installer_config_loaded": "Loading configuration...",
                        "public_ip_loaded": "Getting network information...",
                    }
                    if blocked_on[0] in operation_messages:
                        return operation_messages[blocked_on[0]]

            # Generic fallback when phase=INITIALIZING but no specific status
            return "Initializing system..."

        # No state available yet
        return "Connecting to daemon..."

    # ========================================================================
    # Event Handlers - Receive State from Daemon
    # ========================================================================

    async def _handle_initial_state(self, event: Event) -> None:
        """Handle INITIAL_STATE event (sent when TUI connects).

        This event contains the complete current state of the system.
        All UI state is updated from this event.

        Args:
            event: Initial state event from daemon
        """
        logger.info("Received initial state from daemon")
        state = event.data

        # Populate unified daemon state (convert string enums to enum instances)
        try:
            if isinstance(state.get("phase"), str):
                state["phase"] = DaemonPhase(state["phase"])

            if "system_status" in state:
                sys_status = state["system_status"]
                if isinstance(sys_status.get("dat_mount_status"), str):
                    sys_status["dat_mount_status"] = DatMountStatus(sys_status["dat_mount_status"])
                if isinstance(sys_status.get("connectivity_status"), str):
                    sys_status["connectivity_status"] = ConnectivityStatus(sys_status["connectivity_status"])

            self._daemon_state = state
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to populate unified daemon state: {e}")

        # Update install state
        self.install_state = InstallState[state.get("install_state", "UNKNOWN")]
        self.reconfigure_mode = state.get("reconfigure_mode")

        # Update upgrade state
        if "upgrade" in state:
            self.upgrade_state = UpgradeStateData(**state["upgrade"])

        # Update configuration objects
        if state.get("config", {}).get("installer_config"):
            self.installer_config = InstallerProvidedConfig(**state["config"]["installer_config"])

        if state.get("config", {}).get("user_config"):
            self.user_config = UserProvidedConfig(**state["config"]["user_config"])

        # Update network info
        network = state.get("network", {})
        self.public_ip = network.get("public_ip")
        self.local_ip = network.get("local_ip")
        self.network_connected = network.get("connected", False)

        # Update metrics screen endpoint details
        try:
            metrics = self.get_screen("system_metrics")
            if hasattr(metrics, "set_endpoint_details"):
                # Set network details
                if self.local_ip or self.public_ip:
                    metrics.set_endpoint_details(
                        local_ip=self.local_ip,
                        public_ip=self.public_ip,
                    )
                # Set API port and UPnP from installer config if available
                if self.installer_config:
                    metrics.set_endpoint_details(
                        api_port=str(self.installer_config.upnp_port)
                        if self.installer_config.upnp_port
                        else "16127",
                        upnp_enabled=self.installer_config.upnp_enabled,
                    )
        except KeyError:
            pass  # Metrics screen not installed yet

        # Update blockchain info
        blockchain = state.get("blockchain", {})
        self.blockheight = blockchain.get("height")

        # Update service states (reactive vars updated via direct assignment)
        services = state.get("services", {})
        self.fluxd_installed = services.get("fluxd_started", False)
        self.fluxbenchd_installed = services.get("fluxbenchd_started", False)
        self.fluxos_installed = services.get("fluxos_started", False)
        self.syncthing_installed = services.get("syncthing_started", False)
        self.flux_watchdog_installed = services.get("flux_watchdog_started", False)

        logger.info(
            f"Initial state applied: install_state={self.install_state}, "
            f"reconfigure_mode={self.reconfigure_mode}"
        )

        # Store webserver details if present (apply when launch screen is installed)
        webserver = state.get("webserver", {})
        if webserver.get("host") and webserver.get("port"):
            logger.info(f"Storing webserver details from INITIAL_STATE: {webserver}")
            self._pending_webserver_details = webserver

        # Store tunnel state if present (apply when launch screen is installed)
        tunnel = state.get("tunnel", {})
        if tunnel.get("state") == "connected":
            logger.info(f"Storing tunnel state from INITIAL_STATE")
            self._pending_tunnel_state = tunnel

        # Sync screen with received state (will apply pending details if launch screen created)
        await self._sync_screen_with_state()

    async def _handle_state_update(self, event: Event) -> None:
        """Handle STATE_UPDATE event (unified state update).

        This receives the complete daemon state via the new unified state model.
        Populates _daemon_state and applies to existing instance variables for
        backward compatibility during the transition.

        Args:
            event: State update event from daemon
        """
        data = event.data

        # Reconstruct DaemonState from dict (convert string enums to enum instances)
        try:
            # Convert phase enum
            if isinstance(data.get("phase"), str):
                data["phase"] = DaemonPhase(data["phase"])

            # Convert system_status enums
            if "system_status" in data:
                sys_status = data["system_status"]
                if isinstance(sys_status.get("dat_mount_status"), str):
                    sys_status["dat_mount_status"] = DatMountStatus(sys_status["dat_mount_status"])
                if isinstance(sys_status.get("connectivity_status"), str):
                    sys_status["connectivity_status"] = ConnectivityStatus(sys_status["connectivity_status"])

            # Reconstruct DaemonState (for now, just store the dict)
            self._daemon_state = data

            # Apply state to existing instance variables (backward compatibility)
            self._apply_daemon_state_to_legacy_vars(data)

            # Sync screen with new state
            await self._sync_screen_with_state()

        except Exception as e:
            logger.error(f"Error processing STATE_UPDATE: {e}", exc_info=True)

    def _apply_daemon_state_to_legacy_vars(self, state: dict[str, Any]) -> None:
        """Apply daemon state to TUI instance variables (backward compatibility).

        During the transition, we populate both the new _daemon_state and
        the existing instance variables.

        Args:
            state: DaemonState as dict
        """
        # Installation state
        self.install_state = InstallState[state.get("install_state", "UNKNOWN")]
        self.reconfigure_mode = state.get("reconfigure_mode")

        # Network
        if "network" in state:
            self.public_ip = state["network"].get("public_ip")
            self.local_ip = state["network"].get("local_ip")
            self.network_connected = state["network"].get("connected", False)

        # Blockchain
        if "blockchain" in state:
            self.blockheight = state["blockchain"].get("height")

        # Services
        if "services" in state:
            services = state["services"]
            self.fluxd_installed = services.get("fluxd_started", False)
            self.fluxbenchd_installed = services.get("fluxbenchd_started", False)
            self.fluxos_installed = services.get("fluxos_started", False)
            self.syncthing_installed = services.get("syncthing_started", False)
            self.flux_watchdog_installed = services.get("flux_watchdog_started", False)

        # Configuration
        if "config" in state:
            if state["config"].get("installer_config"):
                self.installer_config = InstallerProvidedConfig(**state["config"]["installer_config"])
            if state["config"].get("user_config"):
                self.user_config = UserProvidedConfig(**state["config"]["user_config"])

    async def _handle_metrics_update(self, event: Event) -> None:
        """Handle SYSTEM_METRICS_UPDATE event (sent every 5 seconds).

        Args:
            event: System metrics update event containing cpu, memory, disk,
                   network_io, and processes stats
        """
        metrics = event.data

        processes = metrics.get("processes", {})
        if processes:
            screen = self.screen
            if hasattr(screen, "update_process_stats"):
                screen.update_process_stats(processes)

    async def _handle_install_state_changed(self, event: Event) -> None:
        """Handle INSTALL_STATE_CHANGED event.

        Args:
            event: Install state changed event
        """
        new_state = event.data.get("install_state")
        if new_state:
            self.install_state = InstallState[new_state]
            logger.info(f"Install state changed to: {self.install_state}")

        self.reconfigure_mode = event.data.get("reconfigure_mode")

        # Sync screen with new state
        await self._sync_screen_with_state()

    async def _handle_service_state_changed(self, event: Event) -> None:
        """Handle SERVICE_STATE_CHANGED event.

        Args:
            event: Service state changed event
        """
        service = event.data.get("service")
        active_state = event.data.get("active_state")
        sub_state = event.data.get("sub_state")

        logger.info(f"Service {service} state changed: {active_state}/{sub_state}")

        # Update reactive vars based on service
        is_running = active_state == "active"

        if service == "fluxd":
            self.fluxd_installed = is_running
            if is_running and self.fluxd_started_at is None:
                self.fluxd_started_at = time.time()

        elif service == "fluxbenchd":
            self.fluxbenchd_installed = is_running
            if is_running and self.fluxbenchd_started_at is None:
                self.fluxbenchd_started_at = time.time()

        elif service == "fluxos":
            self.fluxos_installed = is_running
            if is_running and self.fluxos_started_at is None:
                self.fluxos_started_at = time.time()

        elif service == "flux-watchdog":
            self.flux_watchdog_installed = is_running
            if is_running and self.flux_watchdog_started_at is None:
                self.flux_watchdog_started_at = time.time()

        elif service == "syncthing":
            self.syncthing_installed = is_running
            if is_running and self.syncthing_started_at is None:
                self.syncthing_started_at = time.time()

        # Update metrics screen widgets if screen is installed
        try:
            metrics = self.get_screen("system_metrics")
            if hasattr(metrics, "update_service_state"):
                main_pid = event.data.get("main_pid", 0)
                metrics.update_service_state(service, main_pid, active_state, sub_state)
        except KeyError:
            pass  # Metrics screen not installed yet

    async def _handle_service_states_ready(self, event: Event) -> None:
        """Handle SERVICE_STATES_READY event - initial service states after systemd subscription.

        Args:
            event: Service states ready event containing service_states dict
        """
        service_states = event.data.get("service_states", {})
        logger.info(f"Received initial service states: {len(service_states)} services")

        if not service_states:
            logger.warning("SERVICE_STATES_READY event has empty service_states")
            return

        # Update metrics screen with service states - widgets handle mount checking
        try:
            metrics = self.get_screen("system_metrics")
            if hasattr(metrics, "update_service_state"):
                for service_name, service_state in service_states.items():
                    metrics.update_service_state(
                        service=service_state.get("service", service_name),
                        main_pid=service_state.get("main_pid", 0),
                        active_state=service_state.get("active_state", "unknown"),
                        sub_state=service_state.get("sub_state", "unknown"),
                    )
        except KeyError:
            logger.debug("Metrics screen not installed yet")
        except Exception as e:
            logger.error(f"Error processing service states: {e}", exc_info=True)

    async def _handle_fluxd_rpc_online(self, event: Event) -> None:
        """Handle FLUXD_RPC_ONLINE event.

        Args:
            event: FluxD RPC online event
        """
        online = event.data.get("online", False)
        self.fluxd_online = online

        if online:
            logger.info("FluxD RPC is online")
        else:
            logger.warning("FluxD RPC went offline")

        try:
            metrics = self.get_screen("system_metrics")
            if hasattr(metrics, "fluxd_metrics"):
                metrics.fluxd_metrics.rpc_indicator.rpc_online = online
        except KeyError:
            pass
        except Exception as e:
            logger.warning(f"Failed to update RPC status: {e}")

    async def _handle_fluxd_block_height(self, event: Event) -> None:
        """Handle FLUXD_BLOCK_HEIGHT event.

        Args:
            event: FluxD block height event
        """
        self.blockheight = event.data.get("height")

    async def _handle_fluxd_zmq_new_block(self, event: Event) -> None:
        """Handle FLUXD_ZMQ_NEW_BLOCK event - update block count widget.

        Args:
            event: ZMQ new block event with height
        """
        height = event.data.get("height")
        if height:
            self.blockheight = height
            try:
                metrics = self.get_screen("system_metrics")
                if hasattr(metrics, "fluxd_metrics"):
                    metrics.fluxd_metrics.blockcount.update_daemon_block_count(height)
            except KeyError:
                pass
            except Exception as e:
                logger.error(f"Error updating block count from ZMQ event: {e}")

    async def _handle_fluxd_status_changed(self, event: Event) -> None:
        """Handle FLUXD_STATUS_CHANGED event.

        Args:
            event: Status change event with status field
        """
        status = event.data.get("status")
        if not status:
            return

        try:
            if self.is_screen_installed("system_metrics"):
                metrics = self.get_screen("system_metrics")
                metrics.fluxd_metrics.fluxd_status.status = status
        except Exception as e:
            logger.warning(f"Failed to update FluxD status: {e}")

    async def _handle_fluxbenchd_status_changed(self, event: Event) -> None:
        """Handle FLUXBENCHD_STATUS_CHANGED event.

        Args:
            event: Status change event with status field
        """
        status = event.data.get("status")
        if not status:
            return

        try:
            if self.is_screen_installed("system_metrics"):
                metrics = self.get_screen("system_metrics")
                metrics.fluxbenchd_metrics.benchmark_status.state = status
        except Exception as e:
            logger.warning(f"Failed to update FluxBenchD status: {e}")

    async def _handle_upgrade_started(self, event: Event) -> None:
        """Handle UPGRADE_STARTED event.

        Args:
            event: Upgrade started event
        """
        self.upgrade_state = UpgradeStateData(**event.data)
        logger.info("System upgrade started")

    async def _handle_upgrade_progress(self, event: Event) -> None:
        """Handle UPGRADE_PROGRESS event.

        Args:
            event: Upgrade progress event
        """
        self.upgrade_state = UpgradeStateData(**event.data)

    async def _handle_upgrade_completed(self, event: Event) -> None:
        """Handle UPGRADE_COMPLETED event.

        Args:
            event: Upgrade completed event
        """
        self.upgrade_state = UpgradeStateData(**event.data)
        logger.info("System upgrade completed")

    async def _handle_system_connectivity(self, event: Event) -> None:
        """Handle SYSTEM_CONNECTIVITY event.

        Args:
            event: System connectivity event
        """
        self.network_connected = event.data.get("connected", False)
        logger.info(f"Network connectivity: {self.network_connected}")

    async def _handle_system_public_ip(self, event: Event) -> None:
        """Handle SYSTEM_PUBLIC_IP event.

        Args:
            event: System public IP event
        """
        self.public_ip = event.data.get("ip")
        logger.info(f"Public IP: {self.public_ip}")

        # Update metrics screen with new public IP
        try:
            metrics = self.get_screen("system_metrics")
            if hasattr(metrics, "set_endpoint_details"):
                metrics.set_endpoint_details(
                    local_ip=self.local_ip,
                    public_ip=self.public_ip,
                )
        except KeyError:
            pass  # Metrics screen not installed yet

    async def _handle_system_error(self, event: Event) -> None:
        """Handle SYSTEM_ERROR event.

        Args:
            event: System error event
        """
        error = event.data.get("error")
        message = event.data.get("message")
        logger.error(f"System error: {error} - {message}")

        if self._daemon_state:
            self._daemon_state["system_status"]["fatal_error"] = {
                "error": error,
                "message": message,
            }

        await self._sync_screen_with_state()

    async def _handle_network_config_required(self, event: Event) -> None:
        """Handle NETWORK_CONFIG_REQUIRED event.

        Args:
            event: Network configuration required event
        """
        reason = event.data.get("reason")
        logger.warning(f"Network configuration required: {reason}")

        if self._daemon_state:
            self._daemon_state["system_status"]["fatal_error"] = {
                "error": "Network connectivity test failed",
                "message": "Warning! Network connectivity test failed. This node most likely has no internet connection.",
            }

        await self._sync_screen_with_state()

    async def _handle_insufficient_space(self, event: Event) -> None:
        """Handle INSUFFICIENT_SPACE event.

        Args:
            event: Insufficient space event
        """
        available_gb = event.data.get("available_gb")
        required_gb = event.data.get("required_gb")
        message = event.data.get("message")
        logger.error(f"Insufficient space: {available_gb}GB available, {required_gb}GB required")

        if self._daemon_state:
            self._daemon_state["system_status"]["fatal_error"] = {
                "error": "Insufficient disk space",
                "message": message or f"{available_gb} GiB is not enough space to continue the install",
            }

        await self._sync_screen_with_state()

    async def _process_subscription_state(self, state: dict[str, Any]) -> None:
        """Process initial state from topic subscription.

        When the TUI connects and subscribes to topics, each topic provides
        initial state. For the "install" topic, this includes active_tasks.
        We need to process these to set action states for any currently
        running tasks (e.g., if TUI reconnects during blockchain download).

        Args:
            state: Dictionary of topic states from subscription
        """
        blockchain_state = state.get("blockchain", {})
        if blockchain_state:
            self._process_blockchain_state(blockchain_state)

        benchmarks_state = state.get("benchmarks", {})
        if benchmarks_state:
            self._process_benchmarks_state(benchmarks_state)

        install_state = state.get("install", {})
        active_tasks = install_state.get("active_tasks", [])

        if not active_tasks:
            return

        logger.info(f"Processing {len(active_tasks)} active tasks from subscription state")

        # Find currently running tasks and set their action states
        for task_info in active_tasks:
            if task_info.get("status") != "running":
                continue

            task_name = task_info.get("task") or task_info.get("name", "").split(".")[-1]
            service = task_info.get("service", "").lower()

            # Map task to action state
            if task_name in TASK_ACTION_STATE_MAP:
                action_state, _show_progress = TASK_ACTION_STATE_MAP[task_name]

                logger.info(
                    f"Setting action state '{action_state}' for {service} "
                    f"from active task: {task_name}"
                )

                # Update appropriate service widget
                try:
                    if self.is_screen_installed("system_metrics"):
                        metrics = self.get_screen("system_metrics")

                        # Route to correct widget based on service
                        if service == "fluxd":
                            metrics.fluxd_metrics.set_action_state(action_state)
                        elif service == "fluxos":
                            metrics.fluxos_metrics.set_action_state(action_state)

                except Exception as e:
                    logger.warning(f"Could not set action state for {service}: {e}")

    def _process_blockchain_state(self, blockchain_state: dict[str, Any]) -> None:
        """Process blockchain state from subscription to set block counts and RPC status.

        Args:
            blockchain_state: Blockchain state from subscription containing
                status (with online, block_height), zmq (with block_count), and api_block_count
        """
        try:
            if not self.is_screen_installed("system_metrics"):
                return

            metrics = self.get_screen("system_metrics")
            if not hasattr(metrics, "fluxd_metrics"):
                return

            fluxd_metrics = metrics.fluxd_metrics
            status = blockchain_state.get("status", {})

            rpc_online = status.get("online", False)
            fluxd_metrics.rpc_indicator.rpc_online = rpc_online
            logger.info(f"Set initial RPC online status: {rpc_online}")

            daemon_block_count = None
            if blockchain_state.get("zmq", {}).get("block_count"):
                daemon_block_count = blockchain_state["zmq"]["block_count"]
            elif status.get("block_height"):
                daemon_block_count = status["block_height"]

            api_block_count = blockchain_state.get("api_block_count")

            if daemon_block_count:
                fluxd_metrics.blockcount.update_daemon_block_count(daemon_block_count)
                logger.info(f"Set initial daemon block count: {daemon_block_count}")

            if api_block_count:
                fluxd_metrics.blockcount.set_total_block_count(api_block_count)
                logger.info(f"Set initial API block count: {api_block_count}")

            node_status = blockchain_state.get("node_status")
            if node_status:
                fluxd_metrics.fluxd_status.status = node_status
                logger.info(f"Set initial node status: {node_status}")

        except Exception as e:
            logger.warning(f"Could not process blockchain state: {e}")

    def _process_benchmarks_state(self, benchmarks_state: dict[str, Any]) -> None:
        """Process benchmarks state from subscription to set benchmark tier status.

        Args:
            benchmarks_state: Benchmarks state from subscription containing benchmark_status
        """
        try:
            if not self.is_screen_installed("system_metrics"):
                return

            metrics = self.get_screen("system_metrics")
            if not hasattr(metrics, "fluxbenchd_metrics"):
                return

            benchmark_status = benchmarks_state.get("benchmark_status")
            if benchmark_status:
                metrics.fluxbenchd_metrics.benchmark_status.state = benchmark_status
                logger.info(f"Set initial benchmark status: {benchmark_status}")

        except Exception as e:
            logger.warning(f"Could not process benchmarks state: {e}")

    async def _handle_install_task_started(self, event: Event) -> None:
        """Handle INSTALL_TASK_STARTED - set action state for service widget.

        Args:
            event: Install task started event with service and operation
        """
        operation = event.data.get("operation") or event.data.get("task")
        service = event.data.get("service", "").lower()

        logger.info(f"_handle_install_task_started: operation={operation}, service={service}, event_data={event.data}")

        # Map task operation to action state
        if operation in TASK_ACTION_STATE_MAP:
            action_state, _show_progress = TASK_ACTION_STATE_MAP[operation]

            # Update appropriate service widget based on service name
            try:
                if self.is_screen_installed("system_metrics"):
                    metrics = self.get_screen("system_metrics")

                    # Route to correct widget based on service
                    if service == "fluxd":
                        logger.info(f"Setting action state '{action_state}' for fluxd")
                        metrics.fluxd_metrics.set_action_state(action_state)
                    elif service == "fluxos":
                        logger.info(f"Setting action state '{action_state}' for fluxos")
                        metrics.fluxos_metrics.set_action_state(action_state)
                    else:
                        logger.warning(f"No widget for service '{service}' (operation: {operation})")

            except Exception as e:
                logger.warning(f"Could not set action state for {service}: {e}")
        else:
            logger.info(f"Operation '{operation}' not in TASK_ACTION_STATE_MAP (service: {service})")

    async def _handle_install_task_completed(self, event: Event) -> None:
        """Handle INSTALL_TASK_COMPLETED - clear action state.

        Args:
            event: Install task completed event
        """
        service = event.data.get("service", "").lower()

        try:
            if self.is_screen_installed("system_metrics"):
                metrics = self.get_screen("system_metrics")

                # Clear action state for the appropriate service widget
                if service == "fluxd":
                    metrics.fluxd_metrics.set_action_state(None)
                elif service == "fluxos":
                    metrics.fluxos_metrics.set_action_state(None)

        except Exception:
            pass

    async def _handle_install_task_failed(self, event: Event) -> None:
        """Handle INSTALL_TASK_FAILED - clear action state.

        Args:
            event: Install task failed event
        """
        service = event.data.get("service", "").lower()

        try:
            if self.is_screen_installed("system_metrics"):
                metrics = self.get_screen("system_metrics")

                # Clear action state for the appropriate service widget
                if service == "fluxd":
                    metrics.fluxd_metrics.set_action_state(None)
                elif service == "fluxos":
                    metrics.fluxos_metrics.set_action_state(None)

        except Exception:
            pass

    async def _handle_download_progress(self, event: Event) -> None:
        """Handle DOWNLOAD_PROGRESS - update progress indicator.

        Args:
            event: Download progress event with bytes/speed data
        """
        logger.info(f"_handle_download_progress: event_data={event.data}")

        try:
            if not self.is_screen_installed("system_metrics"):
                logger.warning("system_metrics screen not installed, skipping download progress")
                return

            metrics = self.get_screen("system_metrics")
            fluxd_metrics = metrics.fluxd_metrics
            progress_indicator = fluxd_metrics.progress_indicator

            # Extract progress data
            bytes_downloaded = event.data.get("bytes_downloaded", 0)
            total_bytes = event.data.get("total_bytes", 0)
            speed_mbps = event.data.get("speed_mbps", 0.0)
            source = event.data.get("source")
            source_url = event.data.get("source_url")
            cdn_server = event.data.get("cdn_server")

            # Check if streaming from fluxnode and update label with node IP:port
            if source == "fluxnode" and source_url:
                try:
                    from yarl import URL

                    parsed = URL(source_url)
                    node_endpoint = f"{parsed.host}:{parsed.port}"
                    fluxd_metrics.set_action_state(
                        "Streaming Chain", label=f"Streaming Chain: {node_endpoint}"
                    )
                    logger.info(f"Updated action state label for fluxnode streaming: {node_endpoint}")
                except Exception as url_error:
                    logger.warning(f"Could not parse fluxnode URL: {url_error}")
            # Check if downloading from CDN and update label with CDN server
            elif source == "cdn" and cdn_server:
                fluxd_metrics.set_action_state(
                    "Downloading Chain", label=f"Downloading Chain: {cdn_server}"
                )
                logger.info(f"Updated action state label for CDN download: {cdn_server}")

            # Set total on first progress event
            if total_bytes > 0 and progress_indicator.total_bytes == 0:
                progress_indicator.set_total(total_bytes)

            # Update progress (calculate increment from last update)
            if progress_indicator.total_bytes > 0:
                increment = bytes_downloaded - progress_indicator.transferred_bytes
                if increment > 0:
                    progress_indicator.update(speed_mbps, increment)
                else:
                    # Initial event or no increment: just update speed display
                    if progress_indicator.is_mounted:
                        progress_indicator.progress_throughput.update(f"{speed_mbps:.2f} Mbit/s")

        except Exception as e:
            logger.warning(f"Could not update download progress: {e}")

    async def _handle_webserver_started(self, event: Event) -> None:
        """Handle WEBSERVER_STARTED event (daemon sends webserver details).

        Args:
            event: Webserver started event with host/port/token
        """
        logger.info("Daemon sent webserver details")
        data = event.data
        await self._apply_webserver_details(
            host=data.get("host"),
            port=data.get("port"),
            token=data.get("token"),
        )

    async def _apply_webserver_details(
        self,
        host: str | None,
        port: int | None,
        token: str | None,
    ) -> None:
        """Apply webserver details to LaunchScreen if it's currently displayed.

        Args:
            host: Webserver host
            port: Webserver port
            token: Auth token
        """
        if not host or not port:
            logger.warning("Received incomplete webserver details")
            return

        if not self.is_screen_installed("launch"):
            logger.info("Launch screen not installed yet, storing details for later")
            self._pending_webserver_details = {"host": host, "port": port, "token": token}
            return

        # Get the current LaunchScreen if it's active
        try:
            launch_screen = self.get_screen("launch")
            logger.info(f"Got screen 'launch': {type(launch_screen)}")
            if isinstance(launch_screen, LaunchScreen):
                from ipaddress import IPv4Address

                launch_screen.host = IPv4Address(host)
                launch_screen.port = port
                launch_screen.auth_token = token or ""

                try:
                    launchpad = launch_screen.query_one(LaunchPad)
                    launchpad.show_tunnel_connector = launch_screen.private_ipv4
                except Exception as e:
                    logger.warning(f"Failed to update tunnel connector visibility: {e}")

                launch_screen.refresh()
                logger.info(f"Applied webserver details to LaunchScreen: {host}:{port}")
            else:
                logger.warning(f"Screen 'launch' is not a LaunchScreen: {type(launch_screen)}")
        except Exception as e:
            logger.warning(f"Error applying webserver details: {e}", exc_info=True)

    async def _handle_tunnel_connecting(self, event: Event) -> None:
        """Handle TUNNEL_CONNECTING - show loading state.

        Args:
            event: Tunnel connecting event
        """
        logger.info(f"Received TUNNEL_CONNECTING event: {event.data}")
        try:
            launch_screen = self.get_screen("launch")
            if isinstance(launch_screen, LaunchScreen):
                launch_screen.tunnel_state = "connecting"
                try:
                    launchpad = launch_screen.query_one(LaunchPad)
                    launchpad.set_loading(True)
                    logger.info("LaunchPad loading state set to True")
                except Exception:
                    pass
                launch_screen.refresh()
        except Exception as e:
            logger.warning(f"Error handling TUNNEL_CONNECTING: {e}")

    async def _handle_tunnel_started(self, event: Event) -> None:
        """Handle TUNNEL_STARTED - update LaunchScreen with proxy URL.

        Args:
            event: Tunnel started event with proxy_url
        """
        logger.info(f"Received TUNNEL_STARTED event: {event.data}")
        data = event.data
        proxy_url = data.get("proxy_url")

        if not proxy_url:
            logger.warning("TUNNEL_STARTED missing proxy_url")
            return

        try:
            launch_screen = self.get_screen("launch")
            if isinstance(launch_screen, LaunchScreen):
                launch_screen.tunnel_state = "connected"
                launch_screen.proxy_url = URL(proxy_url)
                try:
                    launchpad = launch_screen.query_one(LaunchPad)
                    launchpad.set_loading(False)
                except Exception:
                    pass
                launch_screen.refresh()
                logger.info(f"Tunnel started, updated LaunchScreen: {proxy_url}")
        except Exception as e:
            logger.warning(f"Error handling TUNNEL_STARTED: {e}")

    async def _handle_tunnel_stopped(self, event: Event) -> None:
        """Handle TUNNEL_STOPPED - clear proxy state.

        Args:
            event: Tunnel stopped event with reason
        """
        data = event.data
        reason = data.get("reason", "unknown")

        try:
            launch_screen = self.get_screen("launch")
            if isinstance(launch_screen, LaunchScreen):
                launch_screen.tunnel_state = "disconnected"
                launch_screen.proxy_url = URL("")
                try:
                    launchpad = launch_screen.query_one(LaunchPad)
                    launchpad.set_loading(False)
                except Exception:
                    pass
                launch_screen.show_proxy = False
                launch_screen.refresh()

                # Notify user based on reason
                if reason == "keepalive_expired":
                    self.notify("Tunnel disconnected - 1hr timeout")
                elif reason == "webserver_stopped":
                    self.notify("Tunnel disconnected - webserver stopped")
        except Exception:
            pass

    async def _handle_tunnel_error(self, event: Event) -> None:
        """Handle TUNNEL_ERROR - show error notification.

        Args:
            event: Tunnel error event with error message
        """
        data = event.data
        error = data.get("error", "Unknown error")

        try:
            launch_screen = self.get_screen("launch")
            if isinstance(launch_screen, LaunchScreen):
                launch_screen.tunnel_state = "error"
                try:
                    launchpad = launch_screen.query_one(LaunchPad)
                    launchpad.set_loading(False)
                except Exception:
                    pass
                launch_screen.show_proxy = False
                launch_screen.refresh()
                self.notify(f"Tunnel error: {error}")
        except Exception:
            pass

    async def _apply_tunnel_state(self, tunnel: dict[str, Any]) -> None:
        """Apply tunnel state from INITIAL_STATE to LaunchScreen.

        Args:
            tunnel: Tunnel state dict with state, proxy_url, etc.
        """
        try:
            launch_screen = self.get_screen("launch")
            if isinstance(launch_screen, LaunchScreen):
                tunnel_state = tunnel.get("state", "disconnected")
                proxy_url = tunnel.get("proxy_url")

                launch_screen.tunnel_state = tunnel_state

                if tunnel_state == "connected" and proxy_url:
                    launch_screen.proxy_url = URL(proxy_url)
                    launch_screen.show_proxy = True
                    launch_screen.url = launch_screen.compute_url()

                    # Update switch state to reflect connected tunnel
                    try:
                        launchpad = launch_screen.query_one(LaunchPad)
                        with launchpad.prevent(Switch.Changed):
                            switch = launchpad.query_one(Switch)
                            switch.value = True
                    except NoMatches:
                        logger.debug("LaunchPad not yet mounted, switch will be set later")

                launch_screen.refresh()
                logger.info(f"Applied tunnel state: {tunnel_state}")
        except Exception as e:
            logger.warning(f"Error applying tunnel state: {e}")

    # ========================================================================
    # UI Screen Management (based on daemon events)
    # ========================================================================

    async def _show_launch_screen(self) -> None:
        """Show the launch screen for user configuration.

        Pattern from old code (frontend.py:2662-2664):
        - Install launch screen
        - Switch to it (replaces LoadingScreen)
        """
        logger.info("Showing LaunchScreen")

        # Create and install launch screen
        launch_screen = LaunchScreen(public_ip=self.public_ip)
        self.install_screen(launch_screen, "launch")

        # Switch to launch screen (replaces whatever is on stack)
        self.switch_screen("launch")

    async def _show_activate_launch_screen(self) -> None:
        """Show the activate launch screen (for deferred reconfiguration).

        Pattern from old code (frontend.py:2667-2668):
        - Install activate_launch screen
        - But show system_metrics (user can activate later)
        """
        logger.info("Installing ActivateLaunchScreen (showing metrics)")

        # Create and install activate screen (for back button navigation)
        activate_screen = ActivateLaunchScreen()
        self.install_screen(activate_screen, "activate_launch")

        # Show system_metrics, not activate_launch
        # User can navigate to activate_launch via back button if needed
        await self._show_system_metrics()

    async def _show_system_metrics(self) -> None:
        """Show the system metrics screen.

        Pattern from old code (frontend.py:2672):
        - system_metrics is always installed in on_mount()
        - Switch to it (replaces LoadingScreen or other screen)
        """
        logger.info("Showing SystemMetrics screen")

        # Switch to system_metrics (always works - LoadingScreen on stack)
        self.switch_screen("system_metrics")

    # ========================================================================
    # User Action Handlers - Send RPC Commands Only
    # ========================================================================

    def on_config_received(self, event: LaunchScreen.ConfigReceived) -> None:
        """Handle user config received from launch screen.

        Config is already sent via webserver POST /configure endpoint.
        This handler updates local TUI state and syncs screen display.

        Args:
            event: ConfigReceived event from LaunchScreen
        """
        logger.info("User submitted FluxNode config via webserver")

        # Store config locally for TUI display purposes
        config_changed = event.config != self.user_config

        if config_changed:
            self.user_config = event.config
            self.persist_user_config()  # Persists to TUI-local JSON file

        # Pattern from old code (frontend.py:2186-2194):
        # Switch to metrics, hide back button, uninstall launch
        self.switch_screen("system_metrics")

        metrics = self.get_screen("system_metrics", SystemMetrics)
        metrics.show_back = False

        self.uninstall_screen("launch")

    @on(LaunchScreen.MetricsRequested)
    def on_metrics_requested(self, event: LaunchScreen.MetricsRequested) -> None:
        """Handle metrics button clicked on launch screen.

        Args:
            event: MetricsRequested event from LaunchScreen
        """
        logger.info("Metrics requested from launch screen")
        self.switch_screen("system_metrics")

    @on(SystemMetrics.BackRequested)
    def on_metrics_back_requested(self, event: SystemMetrics.BackRequested) -> None:
        """Handle back button clicked on metrics screen.

        Args:
            event: BackRequested event from SystemMetrics
        """
        try:
            self.switch_screen("launch")
        except KeyError:
            try:
                self.switch_screen("activate_launch")
            except KeyError:
                # No launch screen to go back to
                logger.warning("No launch screen to return to from metrics")

    @on(SystemMetrics.ShutdownScreenRequested)
    def on_system_metrics_shutdown_screen_requested(
        self, message: SystemMetrics.ShutdownScreenRequested
    ) -> None:
        """Handle shutdown screen request from system metrics."""
        logger.info("Opening shutdown screen")
        self.push_screen(
            ShutdownScreen(
                message.label_text,
                firmware_option=True,
                cancel_option=True,
            )
        )

    @on(SystemMetrics.SettingsScreenRequested)
    def on_system_metrics_settings_screen_requested(
        self, message: SystemMetrics.SettingsScreenRequested
    ) -> None:
        """Handle settings screen request from system metrics."""
        logger.info("Opening settings screen")
        self.push_screen(
            SettingsScreen(
                name="settings_screen",
                install_complete=True,
                reconfiguring=False,
            ),
            self._handle_settings_action,
        )

    @on(ShutdownScreen.ShutdownRequested)
    async def on_shutdown_requested(self, event: ShutdownScreen.ShutdownRequested) -> None:
        """Handle shutdown request from ShutdownScreen.

        Args:
            event: ShutdownRequested event
        """
        logger.info("Shutdown requested via ShutdownScreen")

        try:
            response = await self.backend_client.call_method(
                MethodName.SYSTEM_SHUTDOWN.value, {}
            )

            if response.result and not response.result.get("success"):
                logger.error(f"Shutdown failed: {response.result.get('message')}")
        except Exception as e:
            logger.exception(f"Error calling shutdown: {e}")

    @on(ShutdownScreen.RebootRequested)
    async def on_reboot_requested(self, event: ShutdownScreen.RebootRequested) -> None:
        """Handle reboot request from ShutdownScreen.

        Args:
            event: RebootRequested event (has .firmware attribute)
        """
        if event.firmware:
            logger.info("Firmware reboot requested via ShutdownScreen")
            method = MethodName.SYSTEM_FIRMWARE_REBOOT.value
        else:
            logger.info("Reboot requested via ShutdownScreen")
            method = MethodName.SYSTEM_REBOOT.value

        try:
            response = await self.backend_client.call_method(method, {})

            if response.result and not response.result.get("success"):
                logger.error(f"Reboot failed: {response.result.get('message')}")
        except Exception as e:
            logger.exception(f"Error calling reboot: {e}")

    async def _handle_settings_action(self, action: str | None) -> None:
        """Handle action from settings screen.

        Args:
            action: Button ID from settings screen
        """
        if not action or action == "cancel":
            return

        logger.info(f"Settings action: {action}")

        match action:
            case "start-fluxnode":
                self.push_screen(StartFluxnodeModal())

            case "app-settings":
                self.push_screen(AppSettingsScreen())

            case "firewall-rules":
                self.push_screen(FirewallRulesScreen())

            case "upnp-mappings":
                self.push_screen(UpnpMappingsScreen())

            case "reconfigure-fluxnode":
                logger.warning("Reconfigure Fluxnode not yet implemented")
                self.notify("Reconfigure Fluxnode not yet implemented", severity="warning")

            case "reconfigure-network":
                logger.warning("Reconfigure Network not yet implemented")
                self.notify("Reconfigure Network not yet implemented", severity="warning")

            case "reinstall-components":
                logger.warning("Reinstall Components not yet implemented")
                self.notify("Reinstall Components not yet implemented", severity="warning")

            case _:
                logger.warning(f"Unknown settings action: {action}")

    @work(exclusive=True)
    async def _send_user_config_to_daemon(self, config: UserProvidedConfig) -> None:
        """Send user configuration to daemon via RPC.

        Args:
            config: User configuration to send
        """
        result = await self._rpc_call_safe(
            self.backend_client.call_method, "config.set_user", {"config": config.asdict()}
        )

        if result and result.get("success"):
            logger.info("User config sent to daemon successfully")
        else:
            logger.error(f"Failed to send user config to daemon: {result}")

    def persist_user_config(self) -> None:
        """Persist user configuration to disk.

        This is a UI-side operation for quick restart. The daemon also
        stores the config in its database.
        """
        if not self.user_config:
            return

        try:
            locations = ConfigLocations()
            config_file = locations.config_dir / "user_config.json"
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w") as f:
                f.write(json.dumps(dataclasses.asdict(self.user_config), indent=2))

            logger.info(f"User config persisted to {config_file}")
        except Exception as e:
            logger.error(f"Failed to persist user config: {e}")

    def on_screen_requested_message(self, event: ScreenRequestedMessage) -> None:
        """Handle screen navigation requests.

        Args:
            event: ScreenRequestedMessage
        """

        screen_name = event.screen

        # Close command palette if open
        if self.is_screen_installed("_command_palette"):
            self.pop_screen()

        # Navigate to requested screen
        if screen_name == "theme":
            self.push_screen(ThemeProvider())
        elif screen_name == "logs":
            self.push_screen(LogViewerScreen())
        else:
            self.switch_screen(screen_name)

    # ========================================================================
    # Helper Methods - RPC Utilities
    # ========================================================================

    async def _rpc_call_safe(
        self,
        method: Callable[[str, dict[str, Any] | None], Awaitable[Any]],
        rpc_method: str,
        params: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Safely call an RPC method with error handling.

        Args:
            method: The RPC method to call
            rpc_method: Name of the RPC method
            params: Parameters for the RPC call

        Returns:
            RPC result dict or None on error
        """
        try:
            result = await method(rpc_method, params)
            return result
        except Exception as e:
            logger.error(f"RPC call failed ({rpc_method}): {e}")
            return None


def run() -> None:
    """Run the Flux Config TUI application."""
    configure_logging("flux-config-tui", use_textual=True)

    setproctitle("flux-config-tui")

    connection_string = os.getenv("FLUX_CONFIG_CONNECTION", "unix:///run/flux-configd/daemon.sock")
    api_key = os.getenv("FLUX_CONFIG_API_KEY")

    ssh_key = None
    needs_setup = False
    if connection_string.startswith("ssh://"):
        from flux_config_tui.config import TUIConfig

        ssh_key = TUIConfig.get_ssh_key_path()

        if not ssh_key:
            needs_setup = True

    app = FluxConfigApp(
        connection_string=connection_string,
        api_key=api_key,
        ssh_key_path=ssh_key,
        needs_setup=needs_setup,
    )

    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("TUI interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"TUI failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
