import asyncio
import json
import logging
from collections.abc import AsyncIterator
from functools import cached_property
from typing import Any, Self, TypeVar

import websockets
from websockets.asyncio.client import ClientConnection, connect

from cdpify.domains import (
    AccessibilityClient,
    AnimationClient,
    AuditsClient,
    BackgroundServiceClient,
    BrowserClient,
    CacheStorageClient,
    CastClient,
    ConsoleClient,
    CSSClient,
    DebuggerClient,
    DeviceOrientationClient,
    DOMClient,
    DOMDebuggerClient,
    DOMSnapshotClient,
    DOMStorageClient,
    EmulationClient,
    EventBreakpointsClient,
    FetchClient,
    HeapProfilerClient,
    IndexedDBClient,
    InputClient,
    IOClient,
    LayerTreeClient,
    LogClient,
    MediaClient,
    MemoryClient,
    NetworkClient,
    OverlayClient,
    PageClient,
    PerformanceClient,
    ProfilerClient,
    RuntimeClient,
    SchemaClient,
    SecurityClient,
    ServiceWorkerClient,
    StorageClient,
    SystemInfoClient,
    TargetClient,
    TetheringClient,
    TracingClient,
    WebAudioClient,
    WebAuthnClient,
)
from cdpify.events import EventDispatcher
from cdpify.exceptions import (
    CDPCommandException,
    CDPConnectionException,
    CDPTimeoutException,
)
from cdpify.shared.models import CDPModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=CDPModel)


class CDPClient:
    def __init__(
        self,
        url: str,
        *,
        additional_headers: dict[str, str] | None = None,
        max_frame_size: int = 100 * 1024 * 1024,
        default_timeout: float = 30.0,
    ) -> None:
        self.url: str = url
        self._additional_headers: dict[str, str] | None = additional_headers
        self._max_frame_size: int = max_frame_size
        self._default_timeout: float = default_timeout

        self._ws: ClientConnection | None = None
        self._next_message_id: int = 0
        self._pending_requests: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._message_loop_task: asyncio.Task[None] | None = None
        self._events: EventDispatcher = EventDispatcher()
        self._is_shutting_down: bool = False

    @property
    def is_connected(self) -> bool:
        return self._ws is not None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        if self._ws is not None:
            raise CDPConnectionException("Already connected")

        logger.info(f"Connecting to {self.url}")

        try:
            self._ws = await connect(
                self.url,
                max_size=self._max_frame_size,
                additional_headers=self._additional_headers,
            )
            self._is_shutting_down = False
            self._message_loop_task = asyncio.create_task(self._run_message_loop())
            logger.info("Connected")
        except Exception as e:
            raise CDPConnectionException(f"Connection failed: {e}") from e

    async def _run_message_loop(self) -> None:
        try:
            async for raw_message in self._ws:
                if self._is_shutting_down:
                    break
                await self._process_message(raw_message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        except asyncio.CancelledError:
            logger.debug("Message loop cancelled")
            raise
        except Exception:
            logger.exception("Message loop error")
        finally:
            if not self._is_shutting_down:
                await self.disconnect()

    async def _process_message(self, raw: str) -> None:
        msg = json.loads(raw)

        if self._is_cdp_response(msg):
            await self._handle_response(msg)
        elif self._is_cdp_event(msg):
            await self._handle_event(msg)
        else:
            logger.warning(f"Unknown CDP message format: {msg}")

    def _is_cdp_response(self, msg: dict[str, Any]) -> bool:
        """CDP responses contain an 'id' field"""
        return "id" in msg

    def _is_cdp_event(self, msg: dict[str, Any]) -> bool:
        """CDP events contain a 'method' field"""
        return "method" in msg

    async def _handle_response(self, msg: dict[str, Any]) -> None:
        msg_id = msg["id"]
        future = self._pending_requests.get(msg_id)

        if not future or future.done():
            return

        if "error" in msg:
            future.set_exception(CDPCommandException(msg["error"]))
        else:
            future.set_result(msg.get("result", {}))

    async def _handle_event(self, msg: dict[str, Any]) -> None:
        method = msg["method"]
        params = msg.get("params", {})

        logger.debug(f"Event: {method}")
        handled = await self._events.dispatch(method, params)

        if not handled:
            logger.debug(f"Unhandled event: {method}")

    async def disconnect(self) -> None:
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        logger.info("Disconnecting...")

        await self._stop_message_loop()
        self._cancel_pending_requests()
        await self._close_websocket()

        logger.info("Disconnected")

    async def _stop_message_loop(self) -> None:
        if self._message_loop_task and not self._message_loop_task.done():
            self._message_loop_task.cancel()
            try:
                await self._message_loop_task
            except asyncio.CancelledError:
                pass

    def _cancel_pending_requests(self) -> None:
        error = CDPConnectionException("Disconnected")
        for future in self._pending_requests.values():
            if not future.done():
                future.set_exception(error)
        self._pending_requests.clear()

    async def _close_websocket(self) -> None:
        if self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                logger.debug(f"Websocket close error: {e}")
            finally:
                self._ws = None

    async def listen(
        self, event_name: str, event_type: type[T], timeout: float | None = None
    ) -> AsyncIterator[T]:
        queue: asyncio.Queue[T] = asyncio.Queue()

        async def handler(params: dict[str, Any]) -> None:
            typed_event = event_type.from_cdp(params)
            await queue.put(typed_event)

        try:
            self._events.add_handler(event_name, handler)

            while True:
                yield await asyncio.wait_for(queue.get(), timeout=timeout)

        finally:
            self._events.remove_handler(event_name, handler)

    async def send_raw(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        session_id: str | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        if not self.is_connected:
            raise CDPConnectionException("Not connected")

        timeout = timeout or self._default_timeout
        msg_id = self._next_message_id
        self._next_message_id += 1

        message = self._build_message(msg_id, method, params, session_id)
        future = self._create_pending_request(msg_id)

        try:
            await self._send(msg_id, method, message)
            return await self._await_response(msg_id, method, future, timeout)
        finally:
            self._pending_requests.pop(msg_id, None)

    def _build_message(
        self,
        msg_id: int,
        method: str,
        params: dict[str, Any] | None,
        session_id: str | None,
    ) -> dict[str, Any]:
        message = {"id": msg_id, "method": method, "params": params or {}}
        if session_id:
            message["sessionId"] = session_id
        return message

    def _create_pending_request(self, msg_id: int) -> asyncio.Future[dict[str, Any]]:
        future: asyncio.Future[dict[str, Any]] = asyncio.Future()
        self._pending_requests[msg_id] = future
        return future

    async def _send(self, msg_id: int, method: str, message: dict[str, Any]) -> None:
        logger.debug(f"→ #{msg_id}: {method}")
        await self._ws.send(json.dumps(message))

    async def _await_response(
        self, msg_id: int, method: str, future: asyncio.Future, timeout: float
    ) -> dict[str, Any]:
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            logger.debug(f"← #{msg_id}: OK")
            return result
        except asyncio.TimeoutError:
            raise CDPTimeoutException(f"{method} timed out after {timeout}s") from None

    @cached_property
    def accessibility(self) -> AccessibilityClient:
        return AccessibilityClient(self)

    @cached_property
    def animation(self) -> AnimationClient:
        return AnimationClient(self)

    @cached_property
    def audits(self) -> AuditsClient:
        return AuditsClient(self)

    @cached_property
    def background_service(self) -> BackgroundServiceClient:
        return BackgroundServiceClient(self)

    @cached_property
    def browser(self) -> BrowserClient:
        return BrowserClient(self)

    @cached_property
    def cache_storage(self) -> CacheStorageClient:
        return CacheStorageClient(self)

    @cached_property
    def cast(self) -> CastClient:
        return CastClient(self)

    @cached_property
    def console(self) -> ConsoleClient:
        return ConsoleClient(self)

    @cached_property
    def css(self) -> CSSClient:
        return CSSClient(self)

    @cached_property
    def debugger(self) -> DebuggerClient:
        return DebuggerClient(self)

    @cached_property
    def device_orientation(self) -> DeviceOrientationClient:
        return DeviceOrientationClient(self)

    @cached_property
    def dom(self) -> DOMClient:
        return DOMClient(self)

    @cached_property
    def dom_debugger(self) -> DOMDebuggerClient:
        return DOMDebuggerClient(self)

    @cached_property
    def dom_snapshot(self) -> DOMSnapshotClient:
        return DOMSnapshotClient(self)

    @cached_property
    def dom_storage(self) -> DOMStorageClient:
        return DOMStorageClient(self)

    @cached_property
    def emulation(self) -> EmulationClient:
        return EmulationClient(self)

    @cached_property
    def event_breakpoints(self) -> EventBreakpointsClient:
        return EventBreakpointsClient(self)

    @cached_property
    def fetch(self) -> FetchClient:
        return FetchClient(self)

    @cached_property
    def heap_profiler(self) -> HeapProfilerClient:
        return HeapProfilerClient(self)

    @cached_property
    def indexed_db(self) -> IndexedDBClient:
        return IndexedDBClient(self)

    @cached_property
    def input(self) -> InputClient:
        return InputClient(self)

    @cached_property
    def io(self) -> IOClient:
        return IOClient(self)

    @cached_property
    def layer_tree(self) -> LayerTreeClient:
        return LayerTreeClient(self)

    @cached_property
    def log(self) -> LogClient:
        return LogClient(self)

    @cached_property
    def media(self) -> MediaClient:
        return MediaClient(self)

    @cached_property
    def memory(self) -> MemoryClient:
        return MemoryClient(self)

    @cached_property
    def network(self) -> NetworkClient:
        return NetworkClient(self)

    @cached_property
    def overlay(self) -> OverlayClient:
        return OverlayClient(self)

    @cached_property
    def page(self) -> PageClient:
        return PageClient(self)

    @cached_property
    def performance(self) -> PerformanceClient:
        return PerformanceClient(self)

    @cached_property
    def profiler(self) -> ProfilerClient:
        return ProfilerClient(self)

    @cached_property
    def runtime(self) -> RuntimeClient:
        return RuntimeClient(self)

    @cached_property
    def schema(self) -> SchemaClient:
        return SchemaClient(self)

    @cached_property
    def security(self) -> SecurityClient:
        return SecurityClient(self)

    @cached_property
    def service_worker(self) -> ServiceWorkerClient:
        return ServiceWorkerClient(self)

    @cached_property
    def storage(self) -> StorageClient:
        return StorageClient(self)

    @cached_property
    def system_info(self) -> SystemInfoClient:
        return SystemInfoClient(self)

    @cached_property
    def target(self) -> TargetClient:
        return TargetClient(self)

    @cached_property
    def tethering(self) -> TetheringClient:
        return TetheringClient(self)

    @cached_property
    def tracing(self) -> TracingClient:
        return TracingClient(self)

    @cached_property
    def web_audio(self) -> WebAudioClient:
        return WebAudioClient(self)

    @cached_property
    def web_authn(self) -> WebAuthnClient:
        return WebAuthnClient(self)
