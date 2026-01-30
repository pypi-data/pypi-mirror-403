"""WebSocket client for TUI to connect to backend daemon."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from enum import Enum
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse as URL

import websockets.asyncio.client
import websockets.exceptions

from flux_config_shared.protocol import (
    Event,
    EventType,
    JsonRpcRequest,
    JsonRpcResponse,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from websockets.asyncio.client import ClientConnection

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """Connection states."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class BackendClient:
    """WebSocket client for connecting to the backend daemon."""

    def __init__(
        self,
        connection_string: str,
        api_key: str | None = None,
        ssh_key_path: str | None = None,
    ) -> None:
        """Initialize the backend client.

        Args:
            connection_string: Connection in format:
                - unix:///path/to/socket
                - ws://host:port
                - ssh://user@host/socket/path
            api_key: Optional API key for TCP
            ssh_key_path: SSH private key for ssh:// connections
        """
        self.connection_string = connection_string
        self.api_key = api_key
        self.ssh_key_path = ssh_key_path

        self.connection_type, self.connection_params = self._parse_connection_string(
            connection_string
        )

        self.websocket: ClientConnection | None = None
        self.is_connected = False
        self.is_authenticated = False
        self.state = ConnectionState.DISCONNECTED

        self._request_counter = 0
        self._pending_requests: dict[str | int, asyncio.Future[JsonRpcResponse]] = {}
        self._event_handlers: dict[
            EventType, list[Callable[[Event], Coroutine[Any, Any, None]]]
        ] = {}
        self._receive_task: asyncio.Task[None] | None = None

        self._state_change_callback: Callable[[ConnectionState], None] | None = None

        self._subscribed_topics: set[str] = set()
        self._initial_state_callback: Callable[[dict[str, Any]], None] | None = None

        self._reconnect_task: asyncio.Task[None] | None = None
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 30.0
        self._should_reconnect = True
        self.next_reconnect_in: float = 0.0

        self.ssh_connection: Any = None
        self.ssh_forward_listener: Any = None
        self._local_forward_socket: str | None = None

    def _parse_connection_string(self, conn_str: str) -> tuple[str, dict[str, Any]]:
        """Parse connection string into type and parameters."""
        if conn_str.startswith("unix://"):
            socket_path = conn_str[7:]
            return ("unix", {"socket_path": socket_path})

        elif conn_str.startswith("ws://") or conn_str.startswith("wss://"):
            url = URL(conn_str)
            return ("tcp", {"host": url.hostname, "port": url.port})

        elif conn_str.startswith("ssh://"):
            url = URL(conn_str)
            return (
                "ssh",
                {
                    "ssh_user": url.username,
                    "ssh_host": url.hostname,
                    "ssh_port": url.port or 22,
                    "remote_socket": url.path,
                },
            )

        raise ValueError(f"Invalid connection string: {conn_str}")

    async def connect(self) -> None:
        """Connect to backend daemon."""
        self._set_state(ConnectionState.CONNECTING)

        if self.connection_type == "unix":
            await self._connect_unix_socket(self.connection_params["socket_path"])
        elif self.connection_type == "tcp":
            await self._connect_tcp(
                self.connection_params["host"], self.connection_params["port"]
            )
        elif self.connection_type == "ssh":
            await self._connect_ssh_forwarding(
                self.connection_params["ssh_user"],
                self.connection_params["ssh_host"],
                self.connection_params["ssh_port"],
                self.connection_params["remote_socket"],
            )

    async def _connect_tcp(self, host: str, port: int) -> None:
        """Connect to TCP WebSocket."""
        uri = f"ws://{host}:{port}"
        logger.info(f"Connecting to TCP WebSocket: {uri}")

        try:
            self.websocket = await websockets.asyncio.client.connect(uri)
            self.is_connected = True

            await self._authenticate()

            self._set_state(ConnectionState.CONNECTED)
            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info(f"Connected to TCP WebSocket: {uri}")

        except Exception as e:
            self._set_state(ConnectionState.DISCONNECTED)
            logger.error(f"TCP connection failed: {e}")

            if self._should_reconnect and self._reconnect_task is None:
                self._reconnect_task = asyncio.create_task(self._reconnect())

            raise

    async def _connect_unix_socket(self, socket_path: str) -> None:
        """Connect to Unix domain socket."""
        logger.info(f"Connecting to Unix socket: {socket_path}")

        try:
            self.websocket = await websockets.asyncio.client.unix_connect(socket_path)
            self.is_connected = True

            await self._authenticate_unix()

            self._set_state(ConnectionState.CONNECTED)
            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info(f"Connected to Unix socket: {socket_path}")

        except Exception as e:
            self._set_state(ConnectionState.DISCONNECTED)
            logger.error(f"Unix socket connection failed: {e}")

            if self._should_reconnect and self._reconnect_task is None:
                self._reconnect_task = asyncio.create_task(self._reconnect())

            raise

    async def _connect_ssh_forwarding(
        self,
        ssh_user: str,
        ssh_host: str,
        ssh_port: int,
        remote_socket: str,
    ) -> None:
        """Connect via SSH TCP-to-Unix socket forwarding."""
        import asyncssh

        try:
            logger.info(f"SSH connecting to {ssh_user}@{ssh_host}:{ssh_port}")

            ssh_key = self.ssh_key_path or os.path.expanduser("~/.ssh/id_rsa")

            self.ssh_connection = await asyncssh.connect(
                ssh_host,
                port=ssh_port,
                username=ssh_user,
                client_keys=[ssh_key],
                known_hosts=None,
            )

            local_port = 0
            self.ssh_forward_listener = await self.ssh_connection.forward_local_port_to_path(
                "127.0.0.1",
                local_port,
                remote_socket,
            )

            forwarded_port = self.ssh_forward_listener.get_port()
            logger.info(f"SSH forwarding: {remote_socket} -> 127.0.0.1:{forwarded_port}")

            await self._connect_tcp("127.0.0.1", forwarded_port)
            self._local_forward_port = forwarded_port

        except Exception as e:
            logger.error(f"SSH forwarding failed: {e}")
            await self._cleanup_ssh_forwarding()
            raise

    async def _cleanup_ssh_forwarding(self) -> None:
        """Clean up SSH resources."""
        if hasattr(self, "ssh_forward_listener") and self.ssh_forward_listener:
            self.ssh_forward_listener.close()
            await self.ssh_forward_listener.wait_closed()

        if hasattr(self, "ssh_connection") and self.ssh_connection:
            self.ssh_connection.close()
            await self.ssh_connection.wait_closed()

    async def disconnect(self) -> None:
        """Disconnect from the backend daemon."""
        if not self.is_connected:
            return

        logger.info("Disconnecting from backend daemon")

        self._should_reconnect = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reconnect_task
            self._reconnect_task = None

        if self._receive_task:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task
            self._receive_task = None

        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        await self._cleanup_ssh_forwarding()

        self.is_connected = False
        self.is_authenticated = False
        self._set_state(ConnectionState.DISCONNECTED)

        logger.info("Disconnected from backend daemon")

    async def _authenticate(self) -> None:
        """Authenticate with the backend daemon."""
        if not self.websocket:
            raise RuntimeError("Not connected")

        auth_message = {"api_key": self.api_key}
        await self.websocket.send(json.dumps(auth_message))

        response = await self.websocket.recv()
        response_data = json.loads(response)

        if response_data.get("authenticated"):
            self.is_authenticated = True
            logger.info("Authenticated with backend daemon")
        else:
            raise RuntimeError("Authentication failed")

    async def _authenticate_unix(self) -> None:
        """Unix socket authentication (server uses SO_PEERCRED)."""
        if not self.websocket:
            raise RuntimeError("Not connected")

        auth_message = {"unix_socket": True}
        await self.websocket.send(json.dumps(auth_message))

        response = await self.websocket.recv()
        response_data = json.loads(response)

        if response_data.get("authenticated"):
            self.is_authenticated = True
            logger.info("Unix socket authenticated (via SO_PEERCRED)")
        else:
            raise RuntimeError("Unix socket authentication failed")

    async def _receive_loop(self) -> None:
        """Receive and process messages from the backend daemon."""
        if not self.websocket:
            return

        try:
            async for message in self.websocket:
                # Convert bytes to str if needed
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                await self._handle_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection to backend daemon closed (abnormal)")
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")

        # Loop exited - either normal close or exception
        # Mark as disconnected and trigger reconnect
        if self.is_connected:
            logger.warning("Connection to backend daemon closed")
            self.is_connected = False
            self.is_authenticated = False
            self._set_state(ConnectionState.DISCONNECTED)

            # Auto-reconnect
            if self._should_reconnect:
                self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        while self._should_reconnect and not self.is_connected:
            self._set_state(ConnectionState.RECONNECTING)
            logger.info(f"Reconnecting in {self._reconnect_delay}s...")

            # Sleep in 1-second intervals to allow UI countdown display
            self.next_reconnect_in = self._reconnect_delay
            while self.next_reconnect_in > 0 and not self.is_connected:
                await asyncio.sleep(1.0)
                self.next_reconnect_in -= 1.0

            # Reset countdown
            self.next_reconnect_in = 0.0

            try:
                await self.connect()
                # Reset delay on successful connection
                self._reconnect_delay = 1.0
                logger.info("Reconnected successfully")

            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
                # Exponential backoff
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

    async def _handle_message(self, message: str) -> None:
        """Handle a message from the backend daemon."""
        try:
            data = json.loads(message)

            # Check if it's an RPC response
            if "jsonrpc" in data and ("result" in data or "error" in data):
                response = JsonRpcResponse(**data)
                await self._handle_rpc_response(response)

            # Check if it's an event
            elif "type" in data and "data" in data and "timestamp" in data:
                event = Event(**data)
                await self._handle_event(event)

            else:
                logger.warning(f"Unknown message type: {data}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def _handle_rpc_response(self, response: JsonRpcResponse) -> None:
        """Handle an RPC response."""
        request_id = response.id
        if request_id in self._pending_requests:
            future = self._pending_requests.pop(request_id)
            if not future.done():
                future.set_result(response)

    async def _handle_event(self, event: Event) -> None:
        """Handle an event from the backend daemon."""
        # Find event type
        event_type = None
        for et in EventType:
            if et.value == event.type:
                event_type = et
                break

        if not event_type:
            logger.warning(f"Unknown event type: {event.type}")
            return

        # Call event handlers
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    def on_event(
        self,
        event_type: EventType,
        handler: Callable[[Event], Coroutine[Any, Any, None]],
    ) -> None:
        """Register an event handler (prevents duplicate registration)."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []

        # Prevent duplicate registration
        if handler not in self._event_handlers[event_type]:
            self._event_handlers[event_type].append(handler)

    def on_state_change(self, callback: Callable[[ConnectionState], None]) -> None:
        """Register a callback for connection state changes.

        Args:
            callback: Function called with new ConnectionState when state changes
        """
        self._state_change_callback = callback

    def _set_state(self, new_state: ConnectionState) -> None:
        """Update connection state and notify callback.

        Args:
            new_state: The new connection state
        """
        if self.state != new_state:
            self.state = new_state
            if self._state_change_callback:
                try:
                    self._state_change_callback(new_state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {e}")

    async def call_method(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,  # noqa: ASYNC109 - RPC client needs configurable timeouts per method
    ) -> JsonRpcResponse:
        """Call an RPC method on the backend daemon.

        Args:
            method: RPC method name
            params: Optional parameters dict
            timeout: Request timeout in seconds (default 30.0)

        Returns:
            JsonRpcResponse

        Raises:
            RuntimeError: If not connected/authenticated or request times out
        """
        if not self.is_connected or not self.is_authenticated:
            raise RuntimeError("Not connected or authenticated")

        if not self.websocket:
            raise RuntimeError("WebSocket not initialized")

        # Generate request ID
        self._request_counter += 1
        request_id = self._request_counter

        # Create request
        request = JsonRpcRequest(
            method=method,
            params=params,
            id=request_id,
        )

        # Create future for response
        future: asyncio.Future[JsonRpcResponse] = asyncio.Future()
        self._pending_requests[request_id] = future

        # Send request
        await self.websocket.send(request.model_dump_json())

        # Wait for response (with timeout)
        try:
            async with asyncio.timeout(timeout):
                response = await future
                return response
        except TimeoutError as e:
            self._pending_requests.pop(request_id, None)
            raise RuntimeError(f"Request timeout: {method}") from e

    # --- Convenience methods for RPC calls ---

    # Configuration

    async def get_user_config(self, username: str) -> dict[str, Any]:
        """Get user configuration."""
        response = await self.call_method("config.get_user", {"username": username})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def set_user_config(self, username: str, config: dict[str, Any]) -> dict[str, Any]:
        """Set user configuration."""
        response = await self.call_method(
            "config.set_user", {"username": username, "config": config}
        )
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def validate_pubkey(self, pubkey: str) -> dict[str, Any]:
        """Validate SSH public key."""
        response = await self.call_method("config.validate_pubkey", {"pubkey": pubkey})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    # Service Management

    async def start_service(self, service: str) -> dict[str, Any]:
        """Start a systemd service."""
        response = await self.call_method("service.start", {"service": service})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def stop_service(self, service: str) -> dict[str, Any]:
        """Stop a systemd service."""
        response = await self.call_method("service.stop", {"service": service})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def restart_service(self, service: str) -> dict[str, Any]:
        """Restart a systemd service."""
        response = await self.call_method("service.restart", {"service": service})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def enable_service(self, service: str) -> dict[str, Any]:
        """Enable a systemd service."""
        response = await self.call_method("service.enable", {"service": service})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def disable_service(self, service: str) -> dict[str, Any]:
        """Disable a systemd service."""
        response = await self.call_method("service.disable", {"service": service})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def get_service_status(self, service: str) -> dict[str, Any]:
        """Get systemd service status."""
        response = await self.call_method("service.get_status", {"service": service})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def list_services(self) -> dict[str, Any]:
        """List all managed services."""
        response = await self.call_method("service.list")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    # System

    async def reboot(self) -> dict[str, Any]:
        """Reboot the system."""
        response = await self.call_method("system.reboot")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def shutdown(self) -> dict[str, Any]:
        """Shutdown the system."""
        response = await self.call_method("system.shutdown")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def firmware_reboot(self) -> dict[str, Any]:
        """Reboot to firmware setup."""
        response = await self.call_method("system.firmware_reboot")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def daemon_reload(self) -> dict[str, Any]:
        """Reload systemd daemon configuration."""
        response = await self.call_method("system.daemon_reload")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def sync_filesystems(self) -> dict[str, Any]:
        """Sync filesystems."""
        response = await self.call_method("system.sync")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def drop_caches(self, level: int = 3) -> dict[str, Any]:
        """Drop system caches."""
        response = await self.call_method("system.drop_caches", {"level": level})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    # Firewall

    async def firewall_add_rule(self, target: str) -> dict[str, Any]:
        """Add firewall rule."""
        response = await self.call_method("firewall.add_rule", {"target": target})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def firewall_remove_rule(self, target: str) -> dict[str, Any]:
        """Remove firewall rule."""
        response = await self.call_method("firewall.remove_rule", {"target": target})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def firewall_get_rules(self) -> dict[str, Any]:
        """Get firewall rules."""
        response = await self.call_method("firewall.get_rules")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    # Installation

    async def get_install_state(self) -> dict[str, Any]:
        """Get installation state."""
        response = await self.call_method("install.get_state")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    # Upgrade

    async def check_upgrade(self) -> dict[str, Any]:
        """Check for available upgrades."""
        response = await self.call_method("upgrade.check")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def start_upgrade(self) -> dict[str, Any]:
        """Start system upgrade."""
        response = await self.call_method("upgrade.start")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def get_upgrade_state(self) -> dict[str, Any]:
        """Get upgrade state."""
        response = await self.call_method("upgrade.get_state")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    # FluxD Status

    async def get_fluxd_status(self) -> dict[str, Any]:
        """Get FluxD daemon status."""
        response = await self.call_method("fluxd.get_status")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def get_fluxd_block_height(self) -> dict[str, Any]:
        """Get FluxD block height."""
        response = await self.call_method("fluxd.get_block_height")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    # Subscriptions

    def set_topics(self, topics: list[str]) -> None:
        """Set topics to subscribe to on connect.

        Args:
            topics: List of topic names (e.g., ["services", "metrics", "system"])
        """
        self._subscribed_topics = set(topics)

    def on_initial_state(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Register callback for initial state received on subscription.

        Args:
            callback: Function called with initial state dict when subscription completes
        """
        self._initial_state_callback = callback

    async def subscribe(self, topics: list[str]) -> dict[str, Any]:
        """Subscribe to event topics and receive initial state.

        Args:
            topics: List of topic names to subscribe to

        Returns:
            Dict with "subscribed" (list) and "state" (dict) keys
        """
        response = await self.call_method("subscribe", {"topics": topics})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")

        result = cast("dict[str, Any]", response.result)
        self._subscribed_topics.update(result.get("subscribed", []))

        # Call initial state callback if registered
        if self._initial_state_callback and result.get("state"):
            try:
                self._initial_state_callback(result["state"])
            except Exception as e:
                logger.error(f"Error in initial state callback: {e}")

        return result

    async def unsubscribe(self, topics: list[str]) -> dict[str, Any]:
        """Unsubscribe from event topics.

        Args:
            topics: List of topic names to unsubscribe from

        Returns:
            Dict with "unsubscribed" (list) key
        """
        response = await self.call_method("unsubscribe", {"topics": topics})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")

        result = cast("dict[str, Any]", response.result)
        for topic in result.get("unsubscribed", []):
            self._subscribed_topics.discard(topic)

        return result

    async def subscribe_all(self) -> dict[str, Any]:
        """Subscribe to all common topics for TUI.

        Subscribes to: services, metrics, blockchain, benchmarks, install, upgrade, system

        Returns:
            Dict with "subscribed" (list) and "state" (dict) keys
        """
        topics = ["services", "metrics", "blockchain", "benchmarks", "install", "upgrade", "system"]
        return await self.subscribe(topics)

    # --- Network Management ---

    async def get_interfaces(self) -> dict[str, Any]:
        """Get all network interfaces."""
        response = await self.call_method("network.get_interfaces")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def set_static_ip(
        self,
        interface: str,
        address: str,
        gateway: str | None,
        dns: list[str],
    ) -> dict[str, Any]:
        """Set static IP configuration for an interface.

        Args:
            interface: Interface name (e.g., "eth0")
            address: IP address with prefix (e.g., "192.168.1.10/24")
            gateway: Gateway address (e.g., "192.168.1.1")
            dns: List of DNS servers
        """
        response = await self.call_method(
            "network.set_static_ip",
            {
                "interface": interface,
                "address": address,
                "gateway": gateway,
                "dns": dns,
            },
        )
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def set_dhcp(self, interface: str) -> dict[str, Any]:
        """Set DHCP configuration for an interface.

        Args:
            interface: Interface name (e.g., "eth0")
        """
        response = await self.call_method("network.set_dhcp", {"interface": interface})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def set_interface_disabled(self, interface: str) -> dict[str, Any]:
        """Disable an interface.

        Args:
            interface: Interface name (e.g., "eth0")
        """
        response = await self.call_method("network.set_disabled", {"interface": interface})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def create_vlan(self, parent_interface: str, vlan_id: int) -> dict[str, Any]:
        """Create a VLAN subinterface.

        Args:
            parent_interface: Parent interface name
            vlan_id: VLAN ID (2-4094)
        """
        response = await self.call_method(
            "network.create_vlan",
            {"parent_interface": parent_interface, "vlan_id": vlan_id},
        )
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def delete_vlan(self, interface: str) -> dict[str, Any]:
        """Delete a VLAN subinterface.

        Args:
            interface: VLAN interface name (e.g., "eth0.100")
        """
        response = await self.call_method("network.delete_vlan", {"interface": interface})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def restart_networkd(self) -> dict[str, Any]:
        """Restart systemd-networkd."""
        response = await self.call_method("network.restart_networkd")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def get_routes(self) -> dict[str, Any]:
        """Get routing table."""
        response = await self.call_method("network.get_routes")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def test_connectivity(
        self, gateway: str, interface: str | None = None
    ) -> dict[str, Any]:
        """Test connectivity to a gateway.

        Args:
            gateway: Gateway IP to test
            interface: Optional interface to use
        """
        params: dict[str, Any] = {"gateway": gateway}
        if interface:
            params["interface"] = interface

        response = await self.call_method("network.test_connectivity", params)
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def get_dns(self) -> dict[str, Any]:
        """Get DNS servers."""
        response = await self.call_method("network.get_dns")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def test_dns(self, hostnames: list[str] | None = None) -> dict[str, Any]:
        """Test DNS resolution.

        Args:
            hostnames: List of hostnames to resolve (default: flux.dev, google.com)
        """
        params: dict[str, Any] = {}
        if hostnames:
            params["hostnames"] = hostnames

        response = await self.call_method("network.test_dns", params)
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def get_upnp_status(self) -> dict[str, Any]:
        """Get UPnP IGD status."""
        response = await self.call_method("network.upnp.get_status")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def get_upnp_mappings(self) -> dict[str, Any]:
        """Get current UPnP port mappings."""
        response = await self.call_method("network.upnp.get_mappings")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def add_upnp_mapping(self, port: int) -> dict[str, Any]:
        """Add UPnP port mapping.

        Args:
            port: Port to map
        """
        response = await self.call_method("network.upnp.add_mapping", {"port": port})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def remove_upnp_mapping(self, port: int) -> dict[str, Any]:
        """Remove UPnP port mapping.

        Args:
            port: Port to unmap
        """
        response = await self.call_method("network.upnp.remove_mapping", {"port": port})
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def get_shaping_policy(self) -> dict[str, Any]:
        """Get traffic shaping policy."""
        response = await self.call_method("network.shaping.get_policy")
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)

    async def set_shaping_policy(
        self, interface: str, rate: int | None
    ) -> dict[str, Any]:
        """Set traffic shaping policy.

        Args:
            interface: Interface name
            rate: Rate limit in Mbps (35, 75, 135, 250) or None to disable
        """
        response = await self.call_method(
            "network.shaping.set_policy",
            {"interface": interface, "rate": rate},
        )
        if response.error:
            raise RuntimeError(f"RPC error: {response.error.message}")
        return cast("dict[str, Any]", response.result)
