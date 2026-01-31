"""Runtime wrapper for amirpc that hides nats-py from users."""

from __future__ import annotations

import asyncio
import signal
import sys
from contextlib import asynccontextmanager, suppress
from logging import getLogger
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse, urlunparse

import dns.resolver
from fast_depends import inject

from .config import RuntimeConfig
from .context import set_runtime

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Sequence

    from nats.aio.client import Client as NatsClient

    from .runtime import BaseClient, BaseEmitter, BaseServer

logger = getLogger(__name__)

# Connection state constants
_STATE_DISCONNECTED = "disconnected"
_STATE_CONNECTED = "connected"
_STATE_CLOSED = "closed"


def _resolve_srv(hostname: str) -> list[tuple[str, int]]:
    """Resolve SRV records for _nats._tcp.<hostname>.

    Returns a list of (target, port) tuples sorted by priority then weight.
    If no SRV records found or resolution fails, returns empty list.
    """
    srv_name = f"_nats._tcp.{hostname}"

    try:
        answers = dns.resolver.resolve(srv_name, "SRV")
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        return []
    except Exception as e:
        logger.debug("SRV resolution failed for %s: %s", srv_name, e)
        return []

    records = sorted(answers, key=lambda r: (r.priority, -r.weight))
    return [(str(r.target).rstrip("."), r.port) for r in records]


def _expand_nats_url_srv(nats_url: str) -> list[str]:
    """Expand a NATS URL by resolving SRV records.

    Looks up _nats._tcp.<hostname> and returns a URL for each SRV target.
    If no SRV records found, returns the original URL unchanged.
    """
    parsed = urlparse(nats_url)

    if not parsed.hostname:
        return [nats_url]

    hostname = parsed.hostname

    # Skip localhost and IP addresses
    if (
        hostname in ("localhost", "127.0.0.1", "::1")
        or hostname.replace(".", "").isdigit()
    ):
        return [nats_url]

    targets = _resolve_srv(hostname)

    if not targets:
        return [nats_url]

    expanded_urls = []
    for target, port in targets:
        new_netloc = f"{target}:{port}"

        if parsed.username:
            if parsed.password:
                new_netloc = f"{parsed.username}:{parsed.password}@{new_netloc}"
            else:
                new_netloc = f"{parsed.username}@{new_netloc}"

        new_url = urlunparse(
            (
                parsed.scheme,
                new_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
        expanded_urls.append(new_url)

    logger.info(
        "Expanded NATS URL %s to %d servers via SRV: %s",
        nats_url,
        len(expanded_urls),
        expanded_urls,
    )
    return expanded_urls


class Runtime:
    """Runtime wrapper for NATS-based AMI RPC services.

    Provides a clean API for servers and clients without exposing nats-py directly.

    Server usage:
        runtime = Runtime.from_env()
        runtime.serve(
            [UserServer, OrderServer],
            on_startup=init_db,
            on_shutdown=close_db,
        )

    Client usage (context manager - auto-closes on exit):
        async with Runtime.from_env().connect() as rt:
            client = rt.client(UserServiceClient)
            result = await client.get_user("123")

    Client usage (long-lived connection - for async apps):
        runtime = Runtime.from_env()
        await runtime.start()
        # Use runtime.client() from anywhere, connection stays open
        client = runtime.client(UserServiceClient)
        result = await client.get_user("123")
        # When done:
        await runtime.stop()
    """

    def __init__(
        self,
        nats_url: str = "nats://localhost:4222",
        creds_file: str | None = None,
        service_version: str | None = None,
        service_server: str | None = None,
        service_instance_id: str | None = None,
        connect_timeout: float = 2.0,
        reconnect_time_wait: float = 2.0,
        max_reconnect_attempts: int = 60,
        expand_srv: bool = True,
        drain_timeout: float = 25.0,
    ) -> None:
        """Initialize runtime with connection configuration.

        Args:
            nats_url: NATS server URL
            creds_file: Path to .creds file for authentication
            service_version: Version string for service identification
            service_server: Server/host identifier for health checks
            service_instance_id: Unique instance ID for health checks
            connect_timeout: Connection timeout in seconds
            reconnect_time_wait: Time to wait between reconnection attempts
            max_reconnect_attempts: Maximum number of reconnection attempts
            expand_srv: Resolve DNS SRV records and expand to multiple server URLs
            drain_timeout: Timeout in seconds for draining NATS connection on shutdown
        """
        self._config = RuntimeConfig(
            nats_url=nats_url,
            creds_file=creds_file,
            service_version=service_version,
            service_server=service_server,
            service_instance_id=service_instance_id,
            connect_timeout=connect_timeout,
            reconnect_time_wait=reconnect_time_wait,
            max_reconnect_attempts=max_reconnect_attempts,
            expand_srv=expand_srv,
            drain_timeout=drain_timeout,
        )
        self._nc: NatsClient | None = None
        self._connection_state: str = _STATE_DISCONNECTED
        self._server_instances: list[BaseServer] = []
        self._connect_lock: asyncio.Lock | None = None

    @classmethod
    def from_env(cls, *, expand_srv: bool = True) -> Runtime:
        """Create Runtime from environment variables.

        Args:
            expand_srv: Resolve DNS SRV records and expand to multiple server URLs

        Environment variables:
            NATS_URL: NATS server URL (default: nats://localhost:4222)
            NATS_CREDS_FILE: Path to .creds file (optional)
            AMI_SERVICE_VERSION: Service version string (optional)
        """
        config = RuntimeConfig.from_env()
        return cls(
            nats_url=config.nats_url,
            creds_file=config.creds_file,
            service_version=config.service_version,
            service_server=config.service_server,
            service_instance_id=config.service_instance_id,
            connect_timeout=config.connect_timeout,
            reconnect_time_wait=config.reconnect_time_wait,
            max_reconnect_attempts=config.max_reconnect_attempts,
            expand_srv=expand_srv,
            drain_timeout=config.drain_timeout,
        )

    async def _on_error(self, error: Exception) -> None:
        """Callback for NATS connection errors."""
        logger.error("NATS connection error: %s", error)

    async def _on_disconnect(self) -> None:
        """Callback when NATS connection is lost."""
        self._connection_state = _STATE_DISCONNECTED
        logger.warning("Disconnected from NATS server")

    async def _on_reconnect(self) -> None:
        """Callback when NATS connection is restored.

        Note: nats-py automatically re-subscribes all subscriptions after reconnect
        (see nats/aio/client.py:1525-1550), so we only update state and log here.
        """
        self._connection_state = _STATE_CONNECTED
        logger.info(
            "Reconnected to NATS server (subscriptions auto-restored by nats-py)"
        )

    async def _on_close(self) -> None:
        """Callback when NATS connection is closed."""
        self._connection_state = _STATE_CLOSED
        logger.info("NATS connection closed")

    @property
    def is_connected(self) -> bool:
        """Check if NATS connection is active."""
        return self._nc is not None and self._nc.is_connected

    @property
    def connection_state(self) -> str:
        """Get current connection state."""
        return self._connection_state

    def _get_lock(self) -> asyncio.Lock:
        """Get or create the connection lock (lazy init for event loop safety)."""
        if self._connect_lock is None:
            self._connect_lock = asyncio.Lock()
        return self._connect_lock

    async def start(self) -> None:
        """Connect to NATS and keep connection open.

        Safe to call multiple times - will only connect once.
        Use this for long-lived async applications where you want to
        reuse the same connection across multiple coroutines.

        Sets the runtime context so get_runtime() works anywhere.

        Usage:
            runtime = Runtime.from_env()
            await runtime.start()
            # Now use runtime.client() from anywhere
            client = runtime.client(UserServiceClient)
            # Or use get_runtime()
            from amirpc.context import get_runtime
            rt = get_runtime()
        """
        async with self._get_lock():
            if self._nc is not None and self._nc.is_connected:
                return
            self._nc = await self._connect()
            set_runtime(self)

    async def stop(self) -> None:
        """Close the NATS connection.

        Safe to call multiple times or when not connected.
        Clears the runtime context.
        """
        async with self._get_lock():
            if self._nc is None:
                return
            set_runtime(None)
            await self._drain_and_close()

    async def _drain_and_close(self) -> None:
        """Drain and close NATS connection with timeout handling."""
        if self._nc is None:
            return
        try:
            await asyncio.wait_for(self._nc.drain(), timeout=self._config.drain_timeout)
        except TimeoutError:
            logger.warning(
                "NATS drain timed out after %.1fs, forcing close",
                self._config.drain_timeout,
            )
            await self._nc.close()
        except Exception as e:
            logger.exception("Error draining NATS connection: %s", e)
            with suppress(Exception):
                await self._nc.close()
        finally:
            self._nc = None

    async def _connect(self) -> NatsClient:
        """Connect to NATS server.

        Imports nats-py only when actually connecting.
        If expand_srv is enabled, resolves SRV records to discover additional servers.
        Registers callbacks for connection events (disconnect, reconnect, error, close).
        """
        import nats

        # Expand SRV records if enabled
        if self._config.expand_srv:
            servers = _expand_nats_url_srv(self._config.nats_url)
        else:
            servers = [self._config.nats_url]

        connect_kwargs: dict[str, Any] = {
            "servers": servers,
            "connect_timeout": self._config.connect_timeout,
            "reconnect_time_wait": self._config.reconnect_time_wait,
            "max_reconnect_attempts": self._config.max_reconnect_attempts,
            # Connection event callbacks
            "error_cb": self._on_error,
            "disconnected_cb": self._on_disconnect,
            "reconnected_cb": self._on_reconnect,
            "closed_cb": self._on_close,
        }

        if self._config.creds_file:
            connect_kwargs["user_credentials"] = self._config.creds_file

        nc = await nats.connect(**connect_kwargs)
        self._connection_state = _STATE_CONNECTED
        logger.info("Connected to NATS at %s", servers)
        return nc

    def serve(
        self,
        servers: Sequence[type[BaseServer] | BaseServer],
        *,
        on_startup: Callable[..., Awaitable[None]] | None = None,
        on_shutdown: Callable[..., Awaitable[None]] | None = None,
    ) -> None:
        """Start servers and block until shutdown signal.

        This method runs the event loop and handles SIGINT/SIGTERM for graceful shutdown.

        Args:
            servers: List of BaseServer subclasses or instances to run.
                     Classes will be instantiated with default config.
                     Instances allow custom configuration (e.g., health server settings).
            on_startup: Optional async callback with DI support (can inject RuntimeDep, etc.)
            on_shutdown: Optional async callback with DI support (can inject RuntimeDep, etc.)

        Example:
            >>> from amirpc.context import RuntimeDep
            >>>
            >>> # Using classes (default config)
            >>> runtime.serve([MyServer])
            >>>
            >>> # Using instances (custom config)
            >>> server = MyServer(enable_http_health=True, health_port=8081)
            >>> runtime.serve([server])
            >>>
            >>> async def on_startup(runtime: RuntimeDep):
            ...     client = runtime.client(OrchestratorClient)
            ...     await client.workers.register(worker_id)
            >>>
            >>> runtime.serve([MyServer], on_startup=on_startup)
        """
        asyncio.run(
            self._serve_async(servers, on_startup=on_startup, on_shutdown=on_shutdown)
        )

    async def _serve_async(
        self,
        servers: Sequence[type[BaseServer] | BaseServer],
        *,
        on_startup: Callable[..., Awaitable[None]] | None = None,
        on_shutdown: Callable[..., Awaitable[None]] | None = None,
    ) -> None:
        """Internal async implementation of serve."""
        shutdown_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def signal_handler() -> None:
            logger.info("Received shutdown signal")
            shutdown_event.set()

        # Set up signal handlers (Unix only)
        if sys.platform != "win32":
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)

        self._nc = await self._connect()
        self._server_instances = []

        # Set runtime context for DI in callbacks
        set_runtime(self)

        try:
            if on_startup:
                logger.info("Running startup hooks")
                await inject(on_startup)()

            for server in servers:
                if isinstance(server, type):
                    # It's a class, instantiate it
                    instance = server(
                        version=self._config.service_version,
                        server=self._config.service_server,
                        instance_id=self._config.service_instance_id,
                    )
                else:
                    # It's already an instance
                    instance = server
                instance._runtime = self
                self._server_instances.append(instance)
                await instance.start_health_server()
                await self._start_server(instance)
                logger.info("Started server: %s", type(instance).__name__)

            logger.info("All servers started, waiting for shutdown signal")
            await shutdown_event.wait()

        finally:
            logger.info("Shutting down servers")

            for server in reversed(self._server_instances):
                try:
                    await server.stop_health_server()
                    await self._stop_server(server)
                    logger.info("Stopped server: %s", type(server).__name__)
                except Exception as e:
                    logger.exception(
                        "Error stopping server %s: %s", type(server).__name__, e
                    )

            if on_shutdown:
                logger.info("Running shutdown hooks")
                try:
                    await inject(on_shutdown)()
                except Exception as e:
                    logger.exception("Error in shutdown hook: %s", e)

            if self._nc:
                logger.info(
                    "Draining NATS connection (timeout: %.1fs)",
                    self._config.drain_timeout,
                )
                await self._drain_and_close()
                self._server_instances = []

            # Clear runtime context
            set_runtime(None)

            # Remove signal handlers (Unix only)
            if sys.platform != "win32":
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.remove_signal_handler(sig)

    async def _start_server(self, server: BaseServer) -> None:
        """Start server subscriptions."""
        for subject, cb, queue in server._pending_subscriptions:
            sub = await self.subscribe(subject, cb, queue)
            server._subscriptions.append(sub)
            logger.debug(
                f"Subscribed to {subject}" + (f" (queue={queue})" if queue else "")
            )

    async def _stop_server(self, server: BaseServer) -> None:
        """Stop server subscriptions."""
        for sub in server._subscriptions:
            await sub.unsubscribe()
        server._subscriptions.clear()

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[Runtime]:
        """Connect to NATS and yield self for client usage.

        Idempotent: if already connected, reuses existing connection
        and does not close it on exit.

        Usage:
            async with Runtime.from_env().connect() as rt:
                client = rt.client(UserServiceClient)
                result = await client.get_user("123")
        """
        # Track if we created the connection (so we know whether to close it)
        created_connection = False

        if self._nc is None or not self._nc.is_connected:
            await self.start()
            created_connection = True

        try:
            yield self
        finally:
            # Only close if we created the connection in this context
            if created_connection:
                await self.stop()

    def client[T: BaseClient](self, client_class: type[T]) -> T:
        """Create a client instance bound to this runtime.

        Args:
            client_class: The client class to instantiate

        Returns:
            An instance of the client class

        Raises:
            RuntimeError: If not connected
        """
        self._ensure_connected()
        return client_class(runtime=self)

    def emitter[T: BaseEmitter](self, emitter_class: type[T]) -> T:
        """Create an emitter instance bound to this runtime.

        Args:
            emitter_class: The emitter class to instantiate

        Returns:
            An instance of the emitter class

        Raises:
            RuntimeError: If not connected
        """
        self._ensure_connected()
        return emitter_class(runtime=self)

    # =========================================================================
    # Transport abstraction layer
    # These methods abstract the underlying message queue implementation.
    # Override these to use a different MQ (RabbitMQ, Kafka, etc.)
    # =========================================================================

    def _ensure_connected(self) -> None:
        """Raise if not connected."""
        if self._nc is None:
            raise RuntimeError(
                "Not connected. Use 'await runtime.start()' or "
                "'async with runtime.connect()' first."
            )

    async def request(
        self,
        subject: str,
        data: bytes,
        timeout: float,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        """Send a request and wait for response.

        Args:
            subject: The subject to send to
            data: Request payload as bytes
            timeout: Timeout in seconds
            headers: Optional headers

        Returns:
            Response data as bytes
        """
        self._ensure_connected()
        assert self._nc is not None
        response = await self._nc.request(
            subject, data, timeout=timeout, headers=headers
        )
        return response.data

    async def publish(
        self,
        subject: str,
        data: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Publish a message (fire and forget).

        Args:
            subject: The subject to publish to
            data: Message payload as bytes
            headers: Optional headers
        """
        self._ensure_connected()
        assert self._nc is not None
        await self._nc.publish(subject, data, headers=headers)

    async def subscribe(
        self,
        subject: str,
        callback: Callable,
        queue: str | None = None,
    ):
        """Subscribe to a subject.

        Args:
            subject: The subject to subscribe to
            callback: Async callback function
            queue: Optional queue group for load balancing

        Returns:
            Subscription object (for unsubscribing)
        """
        self._ensure_connected()
        assert self._nc is not None
        if queue:
            return await self._nc.subscribe(subject, cb=callback, queue=queue)
        return await self._nc.subscribe(subject, cb=callback)


__all__ = ["Runtime"]
