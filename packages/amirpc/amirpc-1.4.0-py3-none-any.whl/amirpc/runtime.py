from __future__ import annotations

import socket
import time
from collections.abc import Awaitable, Callable
from logging import getLogger
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from nats.aio.msg import Msg as NatsMessage

    from .app import Runtime

from aiohttp import web
from fast_depends import inject
from nats.errors import NoRespondersError, TimeoutError
from opentelemetry import metrics, propagate, trace
from opentelemetry.trace import SpanKind, StatusCode
from pydantic import ValidationError

from .context import (
    USER_CONTEXT_HEADER,
    deserialize_user_context,
    get_user_context,
    serialize_user_context,
    set_user_context,
)
from .errors import (
    AmiServiceError,
    ServiceUnavailableError,
    UnknownRemoteError,
    UnspecifiedError,
)
from .types import (
    AmiErrorEnvelope,
    AmiEvent,
    AmiEventPayload,
    AmiModel,
    AmiRequest,
    AmiRequestPayload,
    AmiResponse,
    HealthStatus,
)

logger = getLogger(__name__)

# OpenTelemetry Metrics
_meter = metrics.get_meter(__name__)

rpc_request_counter = _meter.create_counter(
    "amirpc.rpc.requests",
    unit="1",
    description="Total number of RPC requests",
)

rpc_duration_histogram = _meter.create_histogram(
    "amirpc.rpc.duration",
    unit="s",
    description="RPC request duration in seconds",
)

event_counter = _meter.create_counter(
    "amirpc.events",
    unit="1",
    description="Total number of events processed",
)

event_published_counter = _meter.create_counter(
    "amirpc.events.published",
    unit="1",
    description="Total number of events published",
)


def _split_rpc_subject(subject: str) -> tuple[str | None, str | None, str]:
    """Split AMI RPC subject into service and method.

    Expected form: "infra.service.type.namespace(.subnamespace...).method" -> ("infra.service", "type", "namespace(.subnamespace...).method").
    """
    if "." in subject:
        parts = subject.split(".")
        return parts[1], parts[2], ".".join(parts[3:])
    return None, None, subject


class BaseEmitter:
    """Base class for generated AMI event emitters."""

    def __init__(self, *, runtime: Runtime) -> None:
        self._runtime = runtime

    async def _publish_event[T: AmiEventPayload](
        self,
        subject: str,
        payload: T,
        *,
        source: str | None = None,
        event_id: UUID | None = None,
    ) -> None:
        """Publish an AmiEvent[T] to the given subject."""
        await publish_event(
            self._runtime, subject, payload, source=source, event_id=event_id
        )


async def publish_event[T: AmiEventPayload](
    runtime: Runtime,
    subject: str,
    payload: T,
    *,
    source: str | None = None,
    event_id: UUID | None = None,
) -> None:
    """Publish an AmiEvent[T] to the given subject with tracing and context propagation."""
    service, type_, method = _split_rpc_subject(subject)
    with trace.get_tracer(__name__).start_as_current_span(
        f"publish {service}.{method}" if service is not None else "publish " + subject,
        kind=SpanKind.PRODUCER,
    ):
        span = trace.get_current_span()
        span.set_attribute("messaging.system", "nats")
        span.set_attribute("messaging.destination.name", subject)
        span.set_attribute("messaging.destination.kind", "topic")
        span.set_attribute("messaging.operation", "publish")
        if type_ is not None:
            span.set_attribute("rpc.type", type_)

        envelope = AmiEvent[payload.__class__](  # type: ignore[invalid-type-form]
            id=event_id or uuid4(),
            payload=payload,
            source=source,
        )
        headers: dict[str, str] = {}
        propagate.inject(headers)
        await runtime.publish(
            subject, envelope.model_dump_json().encode("utf-8"), headers=headers
        )
        event_published_counter.add(1, {"subject": subject})


class BaseClient:
    """Base class for generated AMI RPC clients."""

    _errors_registry: dict[str, type[AmiServiceError]] | None = None
    _subject_prefix: ClassVar[str | None] = None

    def __init__(self, *, runtime: Runtime) -> None:
        self._runtime = runtime

    async def health(self, *, rpc_timeout: float = 5.0) -> HealthStatus:
        """Check health of the remote service."""
        if not self._subject_prefix:
            raise ValueError("Client does not have _subject_prefix set")
        subject = f"{self._subject_prefix}._internal.rpc.health"
        response_data = await self._runtime.request(subject, b"{}", rpc_timeout)
        resp = AmiResponse[HealthStatus].model_validate_json(response_data)
        if resp.error is not None:
            raise UnspecifiedError(resp.error.message or "Health check failed")
        if resp.payload is None:
            raise UnspecifiedError("Empty health response")
        return resp.payload

    async def _request_raw[T: AmiModel](
        self,
        subject: str,
        request: AmiRequest,
        response_type: type[AmiResponse[T]],
        *,
        rpc_timeout: float = 5.0,
    ) -> AmiResponse[T]:
        """Low-level transport call that expects and validates AmiResponse[T]."""
        start_time = time.monotonic()
        service, type_, method = _split_rpc_subject(subject)
        status = "success"
        with trace.get_tracer(__name__).start_as_current_span(
            f"call {service}.{method}", kind=SpanKind.CLIENT
        ):
            span = trace.get_current_span()
            span.set_attribute("rpc.system", "ami")
            if service is not None:
                span.set_attribute("rpc.service", service)
                span.set_attribute("peer.service", service)
            if type_ is not None:
                span.set_attribute("rpc.type", type_)
            span.set_attribute("rpc.method", method)
            span.set_attribute("messaging.system", "nats")
            span.set_attribute("messaging.destination.name", subject)
            span.set_attribute("messaging.destination.kind", "topic")

            headers: dict[str, str] = {}
            propagate.inject(headers)

            user_ctx = get_user_context()
            if user_ctx is not None:
                try:
                    headers[USER_CONTEXT_HEADER] = serialize_user_context(user_ctx)
                    logger.debug(
                        f"Propagating user context: user_id={user_ctx.id}, email={user_ctx.email}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to serialize user context: {e}")

            try:
                response_data = await self._runtime.request(
                    subject,
                    request.model_dump_json().encode("utf-8"),
                    rpc_timeout,
                    headers=headers,
                )
            except TimeoutError as e:
                status = "timeout"
                span.set_status(StatusCode.ERROR, "Timeout")
                span.record_exception(e)
                raise ServiceUnavailableError(
                    "Service unavailable: timeout", reason="timeout", subject=subject
                ) from None
            except NoRespondersError as e:
                status = "no_responders"
                span.set_status(StatusCode.ERROR, "No responders")
                span.record_exception(e)
                raise ServiceUnavailableError(
                    "Service unavailable: no responders",
                    reason="no_responders",
                    subject=subject,
                ) from None
            except Exception as e:
                status = "error"
                span.set_status(StatusCode.ERROR, "Request failed")
                span.record_exception(e)
                raise UnspecifiedError(
                    "Unspecified error", reason="request_failed", subject=subject
                ) from e
            finally:
                # Record client-side metrics
                duration = time.monotonic() - start_time
                labels = {
                    "service": service or "unknown",
                    "method": method,
                    "status": status,
                }
                rpc_request_counter.add(1, labels)
                rpc_duration_histogram.record(duration, labels)

            return response_type.model_validate_json(response_data)

    async def _request_payload[T: AmiModel](
        self,
        subject: str,
        request: AmiRequestPayload,
        response_payload_type: type[T],
        *,
        rpc_timeout: float = 5.0,
    ) -> T:
        """Send request and return payload or raise typed exception."""
        wrapped = AmiRequest(payload=request)
        resp_type = AmiResponse[response_payload_type]  # type: ignore[invalid-type-form]
        resp = await self._request_raw(
            subject, wrapped, resp_type, rpc_timeout=rpc_timeout
        )

        if resp.error is not None:
            code = resp.error.code
            details = resp.error.data or {}
            if code == "unspecified":
                raise UnspecifiedError(
                    resp.error.message or "Unspecified error", **details
                )
            registry = getattr(self, "_errors_registry", None)
            if isinstance(registry, dict):
                err_cls = registry.get(code)
                if err_cls is not None:
                    raise err_cls(resp.error.message, **details)
            raise UnknownRemoteError(
                resp.error.message or code,
                code_override=code,
                **details,
            )

        if resp.payload is None:
            raise UnspecifiedError(
                "Empty response payload", reason="empty_payload", subject=subject
            )
        return resp.payload

    def _subscribe_event[T: AmiEventPayload](
        self,
        subject: str,
        payload_type: type[T],
        handler: Callable[[T], Awaitable[Any]],
        *,
        queue: str | None = None,
    ) -> None:
        """Subscribe to an event stream and decode AmiEvent[T], passing payload to handler."""
        # Wrap handler with fast_depends for dependency injection
        injected_handler = inject(handler)

        async def _subscriber(msg: NatsMessage):
            ctx = propagate.extract(msg.headers or {})
            with trace.get_tracer(__name__).start_as_current_span(
                "subscribe " + subject,
                context=ctx,
                kind=SpanKind.CONSUMER,
            ):
                span = trace.get_current_span()
                span.set_attribute("messaging.system", "nats")
                span.set_attribute("messaging.destination.name", subject)
                span.set_attribute("messaging.destination.kind", "topic")
                span.set_attribute("messaging.operation", "process")

                try:
                    event = AmiEvent[payload_type].model_validate_json(msg.data)  # type: ignore[invalid-type-form]
                except ValidationError as exc:
                    logger.error(
                        "Event validation failed for %s: %d errors. Data: %s",
                        subject,
                        exc.error_count(),
                        msg.data[:500] if msg.data else None,
                    )
                    span.set_status(StatusCode.ERROR, "Event validation failed")
                    span.record_exception(exc)
                    event_counter.add(
                        1, {"subject": subject, "status": "validation_error"}
                    )
                    return

                try:
                    await injected_handler(event.payload)
                    event_counter.add(1, {"subject": subject, "status": "success"})
                except Exception as exc:
                    logger.exception(
                        "Unhandled exception in event handler for %s", subject
                    )
                    span.set_status(StatusCode.ERROR, "Event handler failed")
                    span.record_exception(exc)
                    event_counter.add(1, {"subject": subject, "status": "error"})

        # Store subscription coroutine to be awaited during start
        if not hasattr(self, "_pending_subscriptions"):
            self._pending_subscriptions = []
        self._pending_subscriptions.append((subject, _subscriber, queue))

    async def _publish_event[T: AmiEventPayload](
        self,
        subject: str,
        payload: T,
        *,
        source: str | None = None,
        event_id: UUID | None = None,
    ) -> None:
        """Publish an AmiEvent[T] to the given subject (client side)."""
        await publish_event(
            self._runtime, subject, payload, source=source, event_id=event_id
        )

    async def start(self) -> None:
        """Start subscriptions."""
        for subject, cb, queue in getattr(self, "_pending_subscriptions", []):
            await self._runtime.subscribe(subject, cb, queue)


HandlerT = TypeVar("HandlerT", bound=Callable[..., Awaitable[Any]])


class BaseServer:
    """Base class for generated AMI RPC servers."""

    _subject_prefix: ClassVar[str | None] = None
    _service_name: ClassVar[str | None] = None

    def __init__(
        self,
        *,
        version: str | None = None,
        server: str | None = None,
        instance_id: str | None = None,
        enable_http_health: bool = False,
        health_port: int = 8080,
        health_host: str = "0.0.0.0",
    ):
        self._version = version
        self._server = server
        self._instance_id = instance_id
        self._hostname = socket.gethostname()
        self._start_time = time.monotonic()
        self._enable_http_health = enable_http_health
        self._health_port = health_port
        self._health_host = health_host
        self._health_runner: web.AppRunner | None = None
        self._pending_subscriptions: list[tuple[str, Callable, str | None]] = []
        self._subscriptions: list = []
        self._runtime: Runtime | None = None
        self._setup_handlers()

    def _setup_handlers(self):
        """Register health handler. Generated subclasses should call super()."""
        if self._subject_prefix and self._service_name:
            subject = f"{self._subject_prefix}._internal.rpc.health"
            self._register_health_handler(subject)

    def _register_health_handler(self, subject: str) -> None:
        """Register the universal health check handler."""

        async def _health_handler(msg: NatsMessage) -> None:
            uptime = time.monotonic() - self._start_time
            status = HealthStatus(
                alive=await self._is_alive(),
                ready=await self._is_ready(),
                service=self._service_name or "unknown",
                version=self._version,
                hostname=self._hostname,
                server=self._server,
                instance_id=self._instance_id,
                uptime_seconds=uptime,
            )
            response = AmiResponse(payload=status)
            await msg.respond(response.model_dump_json().encode("utf-8"))

        self._pending_subscriptions.append((subject, _health_handler, None))
        logger.debug(f"Registered health handler on {subject}")

    async def _is_alive(self) -> bool:
        """Check if the server is alive.

        Returns True if NATS connection is active.
        Override to add custom async liveness checks.

        Example:
            async def _is_alive(self) -> bool:
                if not await super()._is_alive():
                    return False
                return await self.redis.ping()
        """
        return self._runtime is not None and self._runtime.is_connected

    async def _is_ready(self) -> bool:
        """Check if the server is ready to accept requests.

        Returns True if NATS connection is active and not draining/reconnecting.
        Override to add custom async readiness checks.

        Example:
            async def _is_ready(self) -> bool:
                if not await super()._is_ready():
                    return False
                return await self.opensearch.ping() and self.scheduler.is_healthy
        """
        if self._runtime is None or self._runtime._nc is None:
            return False
        nc = self._runtime._nc
        return nc.is_connected and not nc.is_draining and not nc.is_reconnecting

    async def start_health_server(self) -> None:
        """Start the HTTP health server."""
        if not self._enable_http_health:
            return

        health_app = web.Application()
        health_app.router.add_get("/alive", self._http_alive_handler)
        health_app.router.add_get("/ready", self._http_ready_handler)
        health_app.router.add_get("/health", self._http_health_handler)

        self._health_runner = web.AppRunner(health_app, access_log=None)
        await self._health_runner.setup()
        site = web.TCPSite(self._health_runner, self._health_host, self._health_port)
        await site.start()
        logger.info(
            "HTTP health server started on http://%s:%d",
            self._health_host,
            self._health_port,
        )

    async def stop_health_server(self) -> None:
        """Stop the HTTP health server."""
        if self._health_runner:
            await self._health_runner.cleanup()
            self._health_runner = None
            logger.info("HTTP health server stopped")

    async def _http_alive_handler(self, _request: web.Request) -> web.Response:
        try:
            alive = await self._is_alive()
        except Exception as e:
            logger.exception("Liveness check failed: %s", e)
            alive = False
        if alive:
            return web.json_response({"alive": True})
        return web.json_response({"alive": False}, status=503)

    async def _http_ready_handler(self, _request: web.Request) -> web.Response:
        try:
            ready = await self._is_ready()
        except Exception as e:
            logger.exception("Readiness check failed: %s", e)
            ready = False
        if ready:
            return web.json_response({"ready": True})
        return web.json_response({"ready": False}, status=503)

    async def _http_health_handler(self, _request: web.Request) -> web.Response:
        try:
            alive = await self._is_alive()
            ready = await self._is_ready()
        except Exception as e:
            logger.exception("Health check failed: %s", e)
            return web.json_response(
                {"alive": False, "ready": False, "error": str(e)},
                status=503,
            )
        status = 200 if (alive and ready) else 503
        return web.json_response({"alive": alive, "ready": ready}, status=status)

    def _bind_rpc(
        self,
        subject: str,
        handler: HandlerT,
        request_payload_type: type[AmiRequestPayload],
        response_payload_type: type[AmiModel],
        *,
        queue: str | None = None,
    ) -> None:
        """Bind a user handler as an RPC subscriber with uniform wrapping."""
        # Wrap handler with fast_depends for dependency injection
        injected_handler = inject(handler)

        async def _subscriber(msg: NatsMessage):
            start_time = time.monotonic()
            ctx = propagate.extract(msg.headers or {})
            service, type_, method = _split_rpc_subject(subject)
            with trace.get_tracer(__name__).start_as_current_span(
                f"handle {service}.{method}",
                context=ctx,
                kind=SpanKind.SERVER,
            ):
                span = trace.get_current_span()
                span.set_attribute("rpc.system", "ami")
                if service is not None:
                    span.set_attribute("rpc.service", service)
                if type_ is not None:
                    span.set_attribute("rpc.type", type_)
                span.set_attribute("rpc.method", method)
                span.set_attribute("messaging.system", "nats")
                span.set_attribute("messaging.destination.name", subject)
                span.set_attribute("messaging.destination.kind", "topic")

                user_context = None
                if msg.headers and USER_CONTEXT_HEADER in msg.headers:
                    try:
                        user_context = deserialize_user_context(
                            msg.headers[USER_CONTEXT_HEADER]
                        )
                        set_user_context(user_context)
                        span.set_attribute("user.id", user_context.id)
                        if user_context.email:
                            span.set_attribute("user.email", user_context.email)
                        if user_context.username:
                            span.set_attribute("user.username", user_context.username)
                        if user_context.organization_name:
                            span.set_attribute(
                                "user.organization.name", user_context.organization_name
                            )
                        if user_context.organization_id:
                            span.set_attribute(
                                "user.organization.id", user_context.organization_id
                            )
                        logger.debug(
                            f"Received user context: user_id={user_context.id}, email={user_context.email}, "
                            f"org={user_context.organization_name}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to deserialize user context from headers: {e}"
                        )
                        set_user_context(None)
                else:
                    set_user_context(None)

                request_id = None
                try:
                    request = AmiRequest[
                        request_payload_type  # ty: ignore[invalid-type-form]
                    ].model_validate_json(msg.data)
                    request_id = request.request_id
                    span.set_attribute("rpc.request_id", str(request_id))
                except ValidationError as exc:
                    logger.warning(
                        "Validation error parsing request for %s: %s",
                        subject,
                        exc.error_count(),
                    )
                    span.set_status(StatusCode.ERROR, "Request validation error")
                    span.record_exception(exc)
                    response = AmiResponse(
                        request_id=request_id,
                        payload=None,
                        error=AmiErrorEnvelope(
                            code="validation_error",
                            message="Request validation failed",
                            data={"errors": exc.errors()},
                        ),
                    )
                    await msg.respond(response.model_dump_json().encode("utf-8"))
                    return

                try:
                    result = await injected_handler(request.payload)
                    if hasattr(response_payload_type, "model_validate"):
                        resp_payload = response_payload_type.model_validate(result)
                    else:
                        resp_payload = result
                    response = AmiResponse(request_id=request_id, payload=resp_payload)
                except ValidationError as exc:
                    logger.warning(
                        "Validation error in RPC handler for %s: %s",
                        subject,
                        exc.error_count(),
                    )
                    span.set_status(StatusCode.ERROR, "Response validation error")
                    span.record_exception(exc)
                    response = AmiResponse(
                        request_id=request_id,
                        payload=None,
                        error=AmiErrorEnvelope(
                            code="validation_error",
                            message="Response validation failed",
                            data={"errors": exc.errors()},
                        ),
                    )
                except AmiServiceError as exc:
                    span.set_status(StatusCode.ERROR, exc.message)
                    span.record_exception(exc)
                    response = AmiResponse(
                        request_id=request_id, payload=None, error=exc.to_envelope()
                    )
                except Exception as exc:
                    logger.exception(
                        "Unhandled exception in RPC handler for %s", subject
                    )
                    span.set_status(StatusCode.ERROR, "Unhandled exception")
                    span.record_exception(exc)
                    response = AmiResponse(
                        request_id=request_id,
                        payload=None,
                        error=AmiErrorEnvelope(
                            code="unspecified",
                            message="Unspecified error",
                            data={"reason": str(exc)} if str(exc) else None,
                        ),
                    )

                await msg.respond(response.model_dump_json().encode("utf-8"))

                # Record metrics
                duration = time.monotonic() - start_time
                labels = {
                    "service": service or "unknown",
                    "method": method,
                    "status": "error" if response.error else "success",
                }
                rpc_request_counter.add(1, labels)
                rpc_duration_histogram.record(duration, labels)

        self._pending_subscriptions.append((subject, _subscriber, queue))

    def _bind_event[T: AmiEventPayload](
        self,
        subject: str,
        handler: HandlerT,
        payload_type: type[T],
        *,
        queue: str | None = None,
    ) -> None:
        """Bind a user handler for a Listen event as a subscriber."""
        # Wrap handler with fast_depends for dependency injection
        injected_handler = inject(handler)

        async def _subscriber(msg: NatsMessage):
            ctx = propagate.extract(msg.headers or {})
            service, type_, method = _split_rpc_subject(subject)
            with trace.get_tracer(__name__).start_as_current_span(
                f"handle {service}.{method}",
                context=ctx,
                kind=SpanKind.CONSUMER,
            ):
                span = trace.get_current_span()
                if type_ is not None:
                    span.set_attribute("rpc.type", type_)
                span.set_attribute("messaging.system", "nats")
                span.set_attribute("messaging.destination.name", subject)
                span.set_attribute("messaging.destination.kind", "topic")
                span.set_attribute("messaging.operation", "process")

                try:
                    event = AmiEvent[payload_type].model_validate_json(msg.data)  # type: ignore[invalid-type-form]
                except ValidationError as exc:
                    logger.error(
                        "Event validation failed for %s: %d errors. Data: %s",
                        subject,
                        exc.error_count(),
                        msg.data[:500] if msg.data else None,
                    )
                    span.set_status(StatusCode.ERROR, "Event validation failed")
                    span.record_exception(exc)
                    event_counter.add(
                        1, {"subject": subject, "status": "validation_error"}
                    )
                    return

                try:
                    await injected_handler(event.payload)
                    event_counter.add(1, {"subject": subject, "status": "success"})
                except Exception as exc:
                    logger.exception(
                        "Unhandled exception in event handler for %s", subject
                    )
                    span.set_status(StatusCode.ERROR, "Event handler failed")
                    span.record_exception(exc)
                    event_counter.add(1, {"subject": subject, "status": "error"})

        self._pending_subscriptions.append((subject, _subscriber, queue))

    async def _publish_event[T: AmiEventPayload](
        self,
        subject: str,
        payload: T,
        *,
        source: str | None = None,
        event_id: UUID | None = None,
    ) -> None:
        """Publish an AmiEvent[T] to the given subject."""
        if self._runtime is None:
            raise RuntimeError("Server must be started via Runtime.serve()")
        await publish_event(
            self._runtime, subject, payload, source=source, event_id=event_id
        )

    def client[T: BaseClient](self, client_class: type[T]) -> T:
        """Create a client instance for S2S calls.

        Args:
            client_class: The client class to instantiate

        Returns:
            An instance of the client class
        """
        if self._runtime is None:
            raise RuntimeError("Server must be started via Runtime.serve()")
        return self._runtime.client(client_class)

    def emitter[T: BaseEmitter](self, emitter_class: type[T]) -> T:
        """Create an emitter instance for publishing events.

        Args:
            emitter_class: The emitter class to instantiate

        Returns:
            An instance of the emitter class
        """
        if self._runtime is None:
            raise RuntimeError("Server must be started via Runtime.serve()")
        return self._runtime.emitter(emitter_class)
