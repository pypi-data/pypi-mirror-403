"""Multiplexed SSE stream management for the connector."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
import threading
from typing import Any, AsyncIterator, Awaitable, Callable

import httpx

from .handlers.oauth import get_token_store
from .handlers.notebooks import _read_last_seq, _sidecar_events_path, get_notebook_registry

logger = logging.getLogger(__name__)


_MAX_BACKOFF_SECONDS = 30.0
_SIDECAR_EVENT_TYPES = {
    "turn_started",
    "ui_event",
    "tool_request",
    "tool_result",
    "approval_request",
    "approval_resolved",
    "turn_interrupted",
    "model_switch",
    "model_used",
}
_TOOLS_ONLY_EVENT_TYPES = {
    "turn_started",
    "turn_interrupted",
    "tool_request",
    "tool_result",
    "approval_request",
    "approval_resolved",
    "toolset_update",
    "model_switch",
}
_UI_TERMINAL_SUBTYPES = {"final", "error", "cancelled"}
_PRIORITY_EVENT_TYPES = {
    "events_gap",
    "tool_request",
    "tool_result",
    "approval_request",
    "approval_resolved",
    "toolset_update",
    "turn_started",
    "turn_interrupted",
    "model_switch",
}
_SIDECAR_LOCKS: dict[str, threading.Lock] = {}
_SIDECAR_LOCKS_GUARD = threading.Lock()


@dataclass(frozen=True)
class IdentityContext:
    """Identity context for a mux stream."""

    end_user_subject: str | None
    workspace_id: str | None
    server_id: str | None

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> "IdentityContext":
        return cls(
            end_user_subject=headers.get("X-End-User-Subject"),
            workspace_id=headers.get("X-Workspace-Id"),
            server_id=headers.get("X-Jupyter-Server-Id"),
        )


def _resolve_scope_key(identity: IdentityContext) -> str:
    if identity.workspace_id and identity.end_user_subject:
        return f"workspace_user:{identity.workspace_id}::{identity.end_user_subject}"
    if identity.workspace_id:
        return f"workspace:{identity.workspace_id}"
    if identity.end_user_subject:
        return f"user:{identity.end_user_subject}"
    return "none:global"


@dataclass
class SubscriptionState:
    session_id: str
    after_seq: int
    priority: str
    mode: str
    notebook_uuid: str | None = None
    notebook_uuid_valid: bool = True
    notebook_uuid_error: str | None = None
    upstream_task: asyncio.Task | None = None
    backfill_task: asyncio.Task | None = None
    backfill_after_seq: int | None = None
    backfill_until_seq: int | None = None
    backfill_buffer: list[dict[str, Any]] = field(default_factory=list)
    connected: bool = False
    last_event_at: float | None = None
    last_seq_seen: int | None = None
    last_seq_checked_at: float | None = None
    clamped_after_seq: int | None = None
    last_forwarded_seq: int | None = None
    pending_gap_event: "QueuedEvent | None" = None
    stop_requested: bool = False
    backoff_attempts: int = 0
    last_error: str | None = None
    pending_events: deque["QueuedEvent"] = field(default_factory=deque)
    sidecar_paused: bool = False
    sidecar_ready: bool = False
    sidecar_pause_reason: str | None = None
    sidecar_pause_at: float | None = None
    degraded: bool = False


@dataclass(frozen=True)
class QueuedEvent:
    event: str
    payload: dict | None
    include_mux_seq: bool = False


@dataclass
class MuxStream:
    stream_id: str
    identity: IdentityContext
    identity_headers: dict[str, str]
    orchestrator_url: str
    heartbeat_interval: float
    max_subscriptions: int
    outbound_queue_max: int
    write_batch_size: int
    ttl_seconds: float
    contents_manager: Any | None
    sidecar_flush_interval: float
    sidecar_pending_max_events: int
    backfill_page_limit: int
    backfill_semaphore: asyncio.Semaphore
    backfill_semaphore_global: asyncio.Semaphore
    notebook_registry: Any
    cursor_cache_ttl: float
    cursor_prefetch_concurrency: int
    session_metadata_cache_ttl: float
    session_metadata_prefetch_concurrency: int
    upstream_headers_provider: Callable[["MuxStream"], Awaitable[dict[str, str] | None]]
    scope_manager: "ScopeStreamManager"
    created_at: float = field(default_factory=time.time)
    last_client_seen_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=time.time)
    mux_seq: int = 0
    subscriptions: dict[str, SubscriptionState] = field(default_factory=dict)
    _subscriptions_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _writer_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _writer_generation: int = 0
    _writer: Any | None = None
    _closed: bool = False
    _close_code: str | None = None
    _close_message: str | None = None
    _close_event: asyncio.Event = field(default_factory=asyncio.Event)
    _pending_event: asyncio.Event = field(default_factory=asyncio.Event)
    _pending_count: int = 0
    _system_events: deque[QueuedEvent] = field(default_factory=deque)
    _sticky_events: deque[QueuedEvent] = field(default_factory=deque)
    _all_order: deque[str] = field(default_factory=deque)
    _foreground_order: deque[str] = field(default_factory=deque)
    _background_order: deque[str] = field(default_factory=deque)
    _foreground_weight: int = 8
    _background_weight: int = 1
    _foreground_budget: int = 0
    _background_budget: int = 0
    _degraded: bool = False
    _degraded_clear_at: float | None = None
    _foreground_suppressed: bool = False
    _foreground_clear_at: float | None = None
    _soft_limit: int = 0
    _recovery_limit: int = 0
    _sidecar_pending: dict[tuple[str, str, str], list[dict[str, Any]]] = field(default_factory=dict)
    _sidecar_flush_task: asyncio.Task | None = None
    _sidecar_flush_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _cursor_cache: dict[str, tuple[int, float]] = field(default_factory=dict)
    _session_metadata_cache: dict[str, tuple[str | None, float]] = field(default_factory=dict)
    _session_metadata_inflight: dict[str, asyncio.Task] = field(default_factory=dict)
    _scope_stream: "ScopeStream | None" = None
    _pending_scope_start: int | None = None

    def __post_init__(self) -> None:
        self.touch()
        self._soft_limit = max(1, int(self.outbound_queue_max * 0.7))
        self._recovery_limit = max(1, int(self.outbound_queue_max * 0.4))
        self._foreground_budget = self._foreground_weight
        self._background_budget = self._background_weight

    def touch(self) -> None:
        now = time.time()
        self.last_client_seen_at = now
        self.expires_at = now + self.ttl_seconds

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def close(self, code: str | None = None, message: str | None = None) -> None:
        if self._closed:
            return
        self._closed = True
        self._close_code = code
        self._close_message = message
        self._close_event.set()
        asyncio.create_task(self._stop_all_subscriptions())
        self._clear_pending_events()
        asyncio.create_task(self._finalize_sidecar_flush())
        if self._sidecar_flush_task and not self._sidecar_flush_task.done():
            self._sidecar_flush_task.cancel()

    def _clear_pending_events(self) -> None:
        self._system_events.clear()
        self._sticky_events.clear()
        for state in self.subscriptions.values():
            if state.pending_events:
                self._pending_count -= len(state.pending_events)
                state.pending_events.clear()
            state.pending_gap_event = None
        self._pending_count = 0
        self._pending_event.clear()

    def _drop_sticky_events_for_session(self, session_id: str) -> int:
        if not self._sticky_events:
            return 0
        kept: deque[QueuedEvent] = deque()
        removed = 0
        while self._sticky_events:
            queued = self._sticky_events.popleft()
            payload = queued.payload
            queued_session_id = payload.get("session_id") if isinstance(payload, dict) else None
            if queued_session_id == session_id:
                removed += 1
                continue
            kept.append(queued)
        self._sticky_events = kept
        return removed

    def _next_mux_seq(self) -> int:
        self.mux_seq += 1
        return self.mux_seq

    def _coerce_seq(self, value: Any) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return None

    def _format_sse_frame(self, event: str, data: dict | None, event_id: int | None) -> str:
        lines: list[str] = []
        if event_id is not None:
            lines.append(f"id: {event_id}")
        if event:
            lines.append(f"event: {event}")
        if data is not None:
            lines.append(f"data: {json.dumps(data)}")
        lines.append("")
        return "\n".join(lines) + "\n"

    def enqueue_event(self, event: str, payload: dict | None, include_mux_seq: bool = False) -> bool:
        if self._closed:
            return False
        if self._pending_count >= self.outbound_queue_max:
            self._apply_soft_pressure(force=True)
            if self._pending_count >= self.outbound_queue_max:
                logger.warning("Mux stream queue overflow; closing stream %s", self.stream_id)
                self.close(code="CLIENT_OVERLOADED", message="Client event queue overflow")
                return False
        self._system_events.append(QueuedEvent(event, payload, include_mux_seq))
        self._pending_count += 1
        self._pending_event.set()
        self._apply_soft_pressure()
        return True

    def enqueue_subscription_event(
        self,
        state: SubscriptionState,
        event: str,
        payload: dict | None,
        include_mux_seq: bool = False,
    ) -> bool:
        if self._closed or state.stop_requested:
            return False
        if self._pending_count >= self.outbound_queue_max:
            self._apply_soft_pressure(force=True)
            if self._pending_count >= self.outbound_queue_max:
                logger.warning("Mux stream queue overflow; closing stream %s", self.stream_id)
                self.close(code="CLIENT_OVERLOADED", message="Client event queue overflow")
                return False
        state.pending_events.append(QueuedEvent(event, payload, include_mux_seq))
        self._pending_count += 1
        self._pending_event.set()
        self._apply_soft_pressure()
        return True

    async def _write_event(
        self,
        handler: Any,
        event: str,
        payload: dict | None,
        include_mux_seq: bool = False,
    ) -> None:
        frame = self._render_frame(event, payload, include_mux_seq)
        handler.write(frame)
        await handler.flush()

    def _render_frame(self, event: str, payload: dict | None, include_mux_seq: bool) -> str:
        next_seq = self._next_mux_seq()
        data = payload
        if include_mux_seq and isinstance(payload, dict):
            data = dict(payload)
            data["mux_seq"] = next_seq
        return self._format_sse_frame(event, data, next_seq)

    async def attach_writer(self, handler: Any) -> int:
        async with self._writer_lock:
            if self._writer is not None and self._writer is not handler:
                try:
                    self._writer.finish()
                except Exception:
                    pass
            self._writer = handler
            self._writer_generation += 1
            generation = self._writer_generation
        await self._ensure_scope_stream()
        await self._start_pending_backfills()
        return generation

    async def detach_writer(self, generation: int) -> None:
        async with self._writer_lock:
            if generation != self._writer_generation:
                return
            self._writer = None
        await self._stop_all_subscriptions()
        self._clear_pending_events()
        await self._finalize_sidecar_flush()
        if self._sidecar_flush_task and not self._sidecar_flush_task.done():
            self._sidecar_flush_task.cancel()

    async def _ensure_scope_stream(self) -> None:
        if self._scope_stream is not None:
            return
        if not self.subscriptions:
            return
        start_event_id = self._pending_scope_start
        self._pending_scope_start = None
        self._scope_stream = await self.scope_manager.attach(self, start_event_id)

    async def _detach_scope_stream(self) -> None:
        if self._scope_stream is None:
            return
        await self.scope_manager.detach(self)
        self._scope_stream = None

    async def _start_pending_backfills(self) -> None:
        async with self._subscriptions_lock:
            states = list(self.subscriptions.values())
        for state in states:
            if state.stop_requested:
                continue
            if state.backfill_until_seq is None:
                continue
            if state.backfill_task and not state.backfill_task.done():
                continue
            state.backfill_task = asyncio.create_task(self._run_backfill(state))

    async def _stop_all_subscriptions(self) -> None:
        await self._detach_scope_stream()
        async with self._subscriptions_lock:
            states = list(self.subscriptions.values())
            self.subscriptions.clear()
            self._all_order.clear()
            self._foreground_order.clear()
            self._background_order.clear()
        for state in states:
            state.stop_requested = True
            if state.upstream_task and not state.upstream_task.done():
                state.upstream_task.cancel()
                try:
                    await state.upstream_task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception("Failed to cancel upstream task for %s", state.session_id)
            if state.backfill_task and not state.backfill_task.done():
                state.backfill_task.cancel()
                try:
                    await state.backfill_task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception("Failed to cancel backfill task for %s", state.session_id)
            state.backfill_buffer.clear()

    async def run_writer(self, handler: Any) -> None:
        generation = await self.attach_writer(handler)
        try:
            self._enqueue_hello()
            while True:
                if self._closed:
                    await self._send_stream_error(handler)
                    break
                if generation != self._writer_generation:
                    break
                try:
                    await asyncio.wait_for(
                        self._pending_event.wait(),
                        timeout=self.heartbeat_interval,
                    )
                except asyncio.TimeoutError:
                    if self._pending_count > 0:
                        continue
                    await self._send_heartbeat(handler)
                    continue

                frames: list[str] = []
                for _ in range(self.write_batch_size):
                    queued = self._dequeue_next_event()
                    if queued is None:
                        break
                    frames.append(self._render_frame(queued.event, queued.payload, queued.include_mux_seq))
                if frames:
                    handler.write("".join(frames))
                    await handler.flush()
                    self.touch()
        except Exception as exc:
            logger.debug("Mux writer closed for %s: %s", self.stream_id, exc)
        finally:
            await self.detach_writer(generation)

    def _enqueue_hello(self) -> None:
        payload = {
            "stream_id": self.stream_id,
            "server_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "heartbeat_interval_ms": int(self.heartbeat_interval * 1000),
            "max_subscriptions": self.max_subscriptions,
            "features": {
                "subscription_put": True,
                "server_backpressure": True,
                "sidecar_append": bool(self.contents_manager),
            },
        }
        self.enqueue_event("hello", payload)

    async def _send_heartbeat(self, handler: Any) -> None:
        last_seq_by_session: dict[str, int] = {}
        for sub_state in self.subscriptions.values():
            last_seq = self._subscription_last_seq(sub_state)
            if last_seq is not None:
                last_seq_by_session[sub_state.session_id] = last_seq
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if last_seq_by_session:
            payload["last_seq_by_session"] = last_seq_by_session
        await self._write_event(handler, "heartbeat", payload, include_mux_seq=True)
        self.touch()

    async def _send_stream_error(self, handler: Any) -> None:
        if not self._close_code:
            return
        payload = {
            "code": self._close_code,
            "message": self._close_message or "Stream closed",
        }
        await self._write_event(handler, "stream_error", payload)

    def _dequeue_next_event(self) -> QueuedEvent | None:
        if self._pending_count <= 0:
            self._pending_event.clear()
            return None
        if self._sticky_events:
            event = self._sticky_events.popleft()
            self._pending_count -= 1
            if self._pending_count <= 0:
                self._pending_event.clear()
            self._apply_soft_pressure()
            return event
        if self._system_events:
            event = self._system_events.popleft()
            self._pending_count -= 1
            if self._pending_count <= 0:
                self._pending_event.clear()
            self._apply_soft_pressure()
            return event

        event = self._pop_matching(self._all_order, self._is_priority_event)
        if event:
            self._maybe_queue_sticky_after_gap(event)
            self._apply_soft_pressure()
            return event

        event = self._pop_matching(self._all_order, self._is_terminal_ui_event)
        if event:
            self._apply_soft_pressure()
            return event

        event = self._pop_weighted_event()
        if event:
            self._apply_soft_pressure()
            return event

        self._pending_event.clear()
        return None

    def _is_priority_event(self, queued: QueuedEvent) -> bool:
        if queued.event != "mux_event":
            return False
        payload = queued.payload
        if not isinstance(payload, dict):
            return False
        return payload.get("type") in _PRIORITY_EVENT_TYPES

    def _is_terminal_ui_event(self, queued: QueuedEvent) -> bool:
        if queued.event != "mux_event":
            return False
        payload = queued.payload
        if not isinstance(payload, dict):
            return False
        if payload.get("type") != "ui_event":
            return False
        data = payload.get("data")
        if not isinstance(data, dict):
            return False
        subtype = data.get("subtype")
        return subtype in _UI_TERMINAL_SUBTYPES

    def _pop_matching(
        self,
        order: deque[str],
        predicate: Callable[[QueuedEvent], bool],
    ) -> QueuedEvent | None:
        for _ in range(len(order)):
            session_id = order.popleft()
            state = self.subscriptions.get(session_id)
            if state is None:
                continue
            if state.pending_events:
                queued = state.pending_events[0]
                if not predicate(queued):
                    order.append(session_id)
                    continue
                event = state.pending_events.popleft()
                if (
                    event.event == "mux_event"
                    and isinstance(event.payload, dict)
                    and event.payload.get("type") == "events_gap"
                ):
                    self._clear_pending_gap_event(state, event)
                order.append(session_id)
                self._pending_count -= 1
                if self._pending_count <= 0:
                    self._pending_event.clear()
                return event
            order.append(session_id)
        return None

    def _maybe_queue_sticky_after_gap(self, event: QueuedEvent) -> None:
        if event.event != "mux_event" or not isinstance(event.payload, dict):
            return
        if event.payload.get("type") != "events_gap":
            return
        session_id = event.payload.get("session_id")
        if not isinstance(session_id, str):
            return
        state = self.subscriptions.get(session_id)
        if state is None or not state.pending_events:
            return
        next_event = state.pending_events[0]
        if not self._is_priority_event(next_event):
            return
        if (
            next_event.event == "mux_event"
            and isinstance(next_event.payload, dict)
            and next_event.payload.get("type") == "events_gap"
        ):
            return
        state.pending_events.popleft()
        self._sticky_events.append(next_event)

    def _pop_weighted_event(self) -> QueuedEvent | None:
        for _ in range(2):
            if self._foreground_order and self._foreground_budget > 0:
                event = self._pop_matching(self._foreground_order, lambda _: True)
                if event:
                    self._foreground_budget -= 1
                    return event
            if self._background_order and self._background_budget > 0:
                event = self._pop_matching(self._background_order, lambda _: True)
                if event:
                    self._background_budget -= 1
                    return event
            self._foreground_budget = self._foreground_weight
            self._background_budget = self._background_weight
        return None

    def _effective_mode(self, state: SubscriptionState) -> str:
        if (
            self._degraded
            and state.priority == "background"
            and state.mode != "tools_only"
        ):
            return "tools_only"
        if state.degraded:
            return "tools_only"
        return state.mode

    def _should_suppress_foreground_ui(self, state: SubscriptionState, payload: dict[str, Any]) -> bool:
        if not self._foreground_suppressed or state.priority != "foreground":
            return False
        event_type = payload.get("type")
        if event_type != "ui_event":
            return False
        data = payload.get("data")
        if not isinstance(data, dict):
            return False
        subtype = data.get("subtype")
        return subtype not in _UI_TERMINAL_SUBTYPES

    def _suppression_reason(self, state: SubscriptionState) -> str:
        if self._foreground_suppressed and state.priority == "foreground":
            return "degraded_low_bandwidth"
        if (self._degraded or state.degraded) and state.priority == "background" and state.mode != "tools_only":
            return "degraded_low_bandwidth"
        if state.mode == "tools_only":
            return "tools_only"
        return "suppressed_ui"

    def _should_forward(self, state: SubscriptionState, payload: dict[str, Any]) -> bool:
        if payload.get("type") == "events_gap":
            return True
        if self._should_suppress_foreground_ui(state, payload):
            return False
        mode = self._effective_mode(state)
        if mode == "live":
            return True
        event_type = payload.get("type")
        if event_type in _TOOLS_ONLY_EVENT_TYPES:
            return True
        if event_type == "ui_event":
            data = payload.get("data")
            if isinstance(data, dict):
                subtype = data.get("subtype")
                return subtype in _UI_TERMINAL_SUBTYPES
        return False

    def _build_gap_payload(self, state: SubscriptionState, from_seq: int, to_seq: int, reason: str) -> dict[str, Any]:
        return {
            "session_id": state.session_id,
            "seq": None,
            "type": "events_gap",
            "turn_id": None,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data": {
                "from_seq": from_seq,
                "to_seq": to_seq,
                "effective_after_seq": to_seq,
                "reason": reason,
            },
        }

    def _extend_gap_payload(self, queued: QueuedEvent, to_seq: int, reason: str) -> None:
        payload = queued.payload
        if not isinstance(payload, dict):
            return
        data = payload.get("data")
        if not isinstance(data, dict):
            return
        current = data.get("to_seq")
        if isinstance(current, float) and current.is_integer():
            current = int(current)
        if isinstance(current, int) and current >= to_seq:
            return
        data["to_seq"] = to_seq
        data["effective_after_seq"] = to_seq
        data["reason"] = reason

    def _enqueue_gap_event(self, state: SubscriptionState, from_seq: int, to_seq: int, reason: str) -> None:
        if to_seq <= from_seq:
            return
        if state.pending_gap_event is not None:
            if state.pending_events and state.pending_events[-1] is state.pending_gap_event:
                self._extend_gap_payload(state.pending_gap_event, to_seq, reason)
                state.last_forwarded_seq = to_seq
                return
        if self._closed or state.stop_requested:
            return
        if self._pending_count >= self.outbound_queue_max:
            self._apply_soft_pressure(force=True)
            if self._pending_count >= self.outbound_queue_max:
                logger.warning("Mux stream queue overflow; closing stream %s", self.stream_id)
                self.close(code="CLIENT_OVERLOADED", message="Client event queue overflow")
                return
        payload = self._build_gap_payload(state, from_seq, to_seq, reason)
        state.pending_gap_event = QueuedEvent("mux_event", payload, include_mux_seq=True)
        state.pending_events.append(state.pending_gap_event)
        state.last_forwarded_seq = to_seq
        self._pending_count += 1
        self._pending_event.set()
        self._apply_soft_pressure()

    def _clear_pending_gap_event(self, state: SubscriptionState, queued: QueuedEvent | None = None) -> None:
        if queued is None:
            state.pending_gap_event = None
            return
        if state.pending_gap_event is queued:
            state.pending_gap_event = None

    def _process_payload(self, state: SubscriptionState, payload: dict[str, Any]) -> None:
        seq = self._coerce_seq(payload.get("seq"))
        if seq is None:
            return
        if state.last_seq_seen is not None and seq <= state.last_seq_seen:
            return
        self._buffer_sidecar_event(state, payload)
        if self._should_forward(state, payload):
            self._clear_pending_gap_event(state)
            self.enqueue_subscription_event(state, "mux_event", payload, include_mux_seq=True)
            state.last_forwarded_seq = seq
        else:
            from_seq = state.last_forwarded_seq
            if from_seq is None:
                from_seq = state.after_seq
            if from_seq is None:
                from_seq = 0
            self._enqueue_gap_event(state, from_seq, seq, self._suppression_reason(state))
        state.last_seq_seen = seq
        state.last_event_at = time.time()

    def _drop_background_noncritical(self) -> None:
        pending_delta = 0
        for state in self.subscriptions.values():
            if state.priority != "background" or state.stop_requested:
                continue
            pending_delta += self._filter_pending_events(state)
        if pending_delta:
            self._pending_count = max(0, self._pending_count - pending_delta)
            if self._pending_count <= 0:
                self._pending_event.clear()

    def _drop_foreground_noncritical(self) -> None:
        pending_delta = 0
        for state in self.subscriptions.values():
            if state.priority != "foreground" or state.stop_requested:
                continue
            pending_delta += self._filter_pending_events(state)
        if pending_delta:
            self._pending_count = max(0, self._pending_count - pending_delta)
            if self._pending_count <= 0:
                self._pending_event.clear()

    def _filter_pending_events(self, state: SubscriptionState) -> int:
        if not state.pending_events:
            return 0
        original_len = len(state.pending_events)
        new_queue: deque[QueuedEvent] = deque()
        cursor_seq = state.last_forwarded_seq if state.last_forwarded_seq is not None else state.after_seq
        pending_gap_event: QueuedEvent | None = None
        for queued in state.pending_events:
            if queued.event != "mux_event" or not isinstance(queued.payload, dict):
                new_queue.append(queued)
                pending_gap_event = None
                continue
            payload = queued.payload
            if payload.get("type") == "events_gap":
                new_queue.append(queued)
                pending_gap_event = queued
                data = payload.get("data")
                to_seq = None
                if isinstance(data, dict):
                    to_seq = self._coerce_seq(data.get("to_seq"))
                    if to_seq is None:
                        to_seq = self._coerce_seq(data.get("effective_after_seq"))
                if to_seq is not None:
                    cursor_seq = to_seq
                continue
            if self._should_forward(state, payload):
                pending_gap_event = None
                new_queue.append(queued)
                seq = self._coerce_seq(payload.get("seq"))
                if seq is not None:
                    cursor_seq = seq
                continue
            seq = self._coerce_seq(payload.get("seq"))
            if seq is None:
                continue
            if pending_gap_event is None:
                from_seq = cursor_seq if cursor_seq is not None else 0
                reason = self._suppression_reason(state)
                gap_payload = self._build_gap_payload(state, from_seq, seq, reason)
                pending_gap_event = QueuedEvent("mux_event", gap_payload, include_mux_seq=True)
                new_queue.append(pending_gap_event)
            else:
                self._extend_gap_payload(pending_gap_event, seq, self._suppression_reason(state))
            cursor_seq = seq
        state.pending_events = new_queue
        if new_queue and new_queue[-1] is pending_gap_event:
            state.pending_gap_event = pending_gap_event
        else:
            state.pending_gap_event = None
        if cursor_seq is not None:
            state.last_forwarded_seq = cursor_seq
        return original_len - len(new_queue)

    def _apply_soft_pressure(self, force: bool = False) -> None:
        if self._closed:
            return
        if self._pending_count >= self._soft_limit or force:
            if not self._degraded:
                self._degraded = True
                self._degraded_clear_at = None
                logger.warning(
                    "Mux stream %s entering degraded mode at queue depth %s",
                    self.stream_id,
                    self._pending_count,
                )
            else:
                self._degraded_clear_at = None
            self._drop_background_noncritical()
            for state in self.subscriptions.values():
                if (
                    state.priority == "background"
                    and state.mode != "tools_only"
                    and not state.degraded
                    and not state.stop_requested
                ):
                    state.degraded = True
                    try:
                        asyncio.create_task(
                            self._emit_subscription_state(
                                state.session_id,
                                "degraded",
                                {
                                    "reason": "high_queue_depth",
                                    "effective_mode": "tools_only",
                                },
                            )
                        )
                    except RuntimeError:
                        logger.debug(
                            "No running loop to emit degraded state for %s",
                            state.session_id,
                        )
            if self._pending_count >= self._soft_limit:
                if not self._foreground_suppressed:
                    self._foreground_suppressed = True
                    self._foreground_clear_at = None
                    logger.warning(
                        "Mux stream %s suppressing foreground UI at queue depth %s",
                        self.stream_id,
                        self._pending_count,
                    )
                else:
                    self._foreground_clear_at = None
                self._drop_foreground_noncritical()
            return
        if self._degraded:
            if self._pending_count > self._recovery_limit:
                self._degraded_clear_at = None
            elif self._degraded_clear_at is None:
                self._degraded_clear_at = time.time() + 5.0
            elif time.time() >= self._degraded_clear_at:
                self._degraded = False
                self._degraded_clear_at = None
                logger.info(
                    "Mux stream %s recovered from degraded mode at queue depth %s",
                    self.stream_id,
                    self._pending_count,
                )
                for state in self.subscriptions.values():
                    if state.degraded:
                        state.degraded = False
                        try:
                            asyncio.create_task(
                                self._emit_subscription_state(
                                    state.session_id,
                                    "connected",
                                    {"effective_mode": state.mode},
                                )
                            )
                        except RuntimeError:
                            logger.debug(
                                "No running loop to emit recovery state for %s",
                                state.session_id,
                            )
        if self._foreground_suppressed:
            if self._pending_count > self._recovery_limit:
                self._foreground_clear_at = None
            elif self._foreground_clear_at is None:
                self._foreground_clear_at = time.time() + 5.0
            elif time.time() >= self._foreground_clear_at:
                self._foreground_suppressed = False
                self._foreground_clear_at = None
                logger.info(
                    "Mux stream %s resumed foreground UI at queue depth %s",
                    self.stream_id,
                    self._pending_count,
                )

    def _maybe_mark_degraded(self, state: SubscriptionState) -> None:
        if not self._degraded:
            return
        if (
            state.priority != "background"
            or state.mode == "tools_only"
            or state.degraded
            or state.stop_requested
        ):
            return
        state.degraded = True
        try:
            asyncio.create_task(
                self._emit_subscription_state(
                    state.session_id,
                    "degraded",
                    {"reason": "high_queue_depth", "effective_mode": "tools_only"},
                )
            )
        except RuntimeError:
            logger.debug("No running loop to emit degraded state for %s", state.session_id)

    async def _resolve_scope_subscriptions(
        self,
        subscriptions: list[dict[str, Any]],
    ) -> tuple[dict[str, dict[str, Any]], int | None] | None:
        headers = await self.upstream_headers_provider(self)
        if headers is None:
            return None
        url = f"{self.orchestrator_url}/v1/scopes/events/resolve"
        payload = {
            "subscriptions": [
                {
                    "session_id": sub["session_id"],
                    "after_seq": sub["after_seq"],
                }
                for sub in subscriptions
            ]
        }
        timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=None)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
        except Exception as exc:
            logger.debug("Failed to resolve scope cursors: %s", exc)
            return None
        if response.status_code != 200:
            logger.debug(
                "Scope resolve failed with status %s", response.status_code
            )
            return None
        try:
            body = response.json()
        except json.JSONDecodeError:
            return None
        if not isinstance(body, dict):
            return None
        results_raw = body.get("results")
        if not isinstance(results_raw, list):
            return None
        results: dict[str, dict[str, Any]] = {}
        for item in results_raw:
            if not isinstance(item, dict):
                continue
            session_id = item.get("session_id")
            if isinstance(session_id, str):
                results[session_id] = item
        min_event_id = body.get("min_event_id")
        if not isinstance(min_event_id, int):
            min_event_id = None
        return results, min_event_id

    async def update_subscriptions(self, requested: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        requested_map = {item["session_id"]: item for item in requested}
        normalized: dict[str, dict[str, Any]] = {}

        for session_id, requested_state in requested_map.items():
            after_seq_raw = requested_state.get("after_seq", 0)
            if not isinstance(after_seq_raw, (int, float)) or not float(after_seq_raw).is_integer():
                after_seq = 0
            else:
                after_seq = int(after_seq_raw)
            if after_seq < 0:
                after_seq = 0
            priority = requested_state.get("priority", "foreground")
            mode = requested_state.get("mode", "live")
            notebook_uuid = requested_state.get("notebook_uuid")

            normalized[session_id] = {
                "session_id": session_id,
                "after_seq": after_seq,
                "priority": priority,
                "mode": mode,
                "notebook_uuid": notebook_uuid,
            }

        notebook_uuid_errors = await self._validate_notebook_uuid_assignments(normalized)
        resolved = await self._resolve_scope_subscriptions(list(normalized.values()))
        resolved_map: dict[str, dict[str, Any]] | None = None
        min_event_id: int | None = None
        if resolved is not None:
            resolved_map, min_event_id = resolved

        accepted: dict[str, dict[str, Any]] = {}
        if resolved_map is not None:
            for session_id, requested_state in normalized.items():
                if session_id in notebook_uuid_errors:
                    logger.warning(
                        "Mux subscription notebook_uuid mismatch for %s (requested=%s, pinned=%s)",
                        session_id,
                        requested_state.get("notebook_uuid"),
                        notebook_uuid_errors[session_id],
                    )
                    results.append({
                        "session_id": session_id,
                        "accepted": False,
                        "message": "notebook_uuid_mismatch",
                        "error_code": "NOTEBOOK_UUID_MISMATCH",
                        "effective_after_seq": 0,
                    })
                    await self._emit_subscription_state(
                        session_id,
                        "error",
                        {
                            "message": "Notebook UUID mismatch",
                            "reason": "NOTEBOOK_UUID_MISMATCH",
                            "error_code": "NOTEBOOK_UUID_MISMATCH",
                        },
                    )
                    continue
                resolved_state = resolved_map.get(session_id)
                if resolved_state is None:
                    results.append({
                        "session_id": session_id,
                        "accepted": False,
                        "message": "scope_resolve_missing",
                        "effective_after_seq": 0,
                    })
                    await self._emit_subscription_state(
                        session_id,
                        "error",
                        {"message": "Scope resolution missing"},
                    )
                    continue
                if not resolved_state.get("accepted", True):
                    results.append({
                        "session_id": session_id,
                        "accepted": False,
                        "message": resolved_state.get("message") or "rejected",
                        "error_code": resolved_state.get("error_code"),
                        "effective_after_seq": 0,
                    })
                    await self._emit_subscription_state(
                        session_id,
                        "error",
                        {
                            "message": resolved_state.get("message") or "Rejected",
                            "error_code": resolved_state.get("error_code"),
                        },
                    )
                    continue
                requested_after_seq = requested_state["after_seq"]
                effective_after_seq = resolved_state.get("effective_after_seq")
                if not isinstance(effective_after_seq, int):
                    effective_after_seq = requested_after_seq
                last_seq = resolved_state.get("last_seq")
                if not isinstance(last_seq, int):
                    last_seq = None
                clamped_after_seq: int | None = None
                if last_seq is not None and requested_after_seq > effective_after_seq:
                    clamped_after_seq = effective_after_seq
                    self._emit_events_gap(
                        session_id,
                        requested_after_seq,
                        effective_after_seq,
                        last_seq,
                        "preflight_clamp",
                    )
                requested_state["after_seq"] = effective_after_seq
                requested_state["clamped_after_seq"] = clamped_after_seq
                requested_state["last_seq_checked_at"] = time.time() if last_seq is not None else None
                requested_state["last_seq"] = last_seq
                requested_state["resolve_message"] = resolved_state.get("message")
                accepted[session_id] = requested_state
        else:
            preflight_ids = [
                session_id
                for session_id, requested_state in normalized.items()
                if requested_state["after_seq"] > 0
            ]
            last_seq_map = await self._get_last_seq_bulk(preflight_ids)
            for session_id, requested_state in normalized.items():
                if session_id in notebook_uuid_errors:
                    logger.warning(
                        "Mux subscription notebook_uuid mismatch for %s (requested=%s, pinned=%s)",
                        session_id,
                        requested_state.get("notebook_uuid"),
                        notebook_uuid_errors[session_id],
                    )
                    results.append({
                        "session_id": session_id,
                        "accepted": False,
                        "message": "notebook_uuid_mismatch",
                        "error_code": "NOTEBOOK_UUID_MISMATCH",
                        "effective_after_seq": 0,
                    })
                    await self._emit_subscription_state(
                        session_id,
                        "error",
                        {
                            "message": "Notebook UUID mismatch",
                            "reason": "NOTEBOOK_UUID_MISMATCH",
                            "error_code": "NOTEBOOK_UUID_MISMATCH",
                        },
                    )
                    continue
                requested_after_seq = requested_state["after_seq"]
                last_seq = last_seq_map.get(session_id)
                checked_at = time.time() if last_seq is not None else None
                effective_after_seq = requested_after_seq
                clamped_after_seq: int | None = None
                if last_seq is not None and requested_after_seq > last_seq:
                    effective_after_seq = last_seq
                    clamped_after_seq = last_seq
                    self._emit_events_gap(
                        session_id,
                        requested_after_seq,
                        effective_after_seq,
                        last_seq,
                        "preflight_clamp",
                    )
                requested_state["after_seq"] = effective_after_seq
                requested_state["clamped_after_seq"] = clamped_after_seq
                requested_state["last_seq_checked_at"] = checked_at
                requested_state["last_seq"] = last_seq
                accepted[session_id] = requested_state

        if self._scope_stream is None and min_event_id is not None:
            self._pending_scope_start = min_event_id

        pending_connected: list[str] = []
        async with self._subscriptions_lock:
            existing_ids = set(self.subscriptions.keys())
            requested_ids = set(accepted.keys())

            removed = existing_ids - requested_ids
            for session_id in removed:
                state = self.subscriptions.pop(session_id, None)
                if state:
                    state.stop_requested = True
                    self._remove_from_order(session_id, state.priority)
                    if state.pending_events:
                        self._pending_count -= len(state.pending_events)
                        state.pending_events.clear()
                    if state.upstream_task and not state.upstream_task.done():
                        state.upstream_task.cancel()

            for session_id in requested_ids:
                requested_state = accepted[session_id]
                after_seq = requested_state["after_seq"]
                priority = requested_state["priority"]
                mode = requested_state["mode"]
                notebook_uuid = requested_state.get("notebook_uuid")
                clamped_after_seq = requested_state.get("clamped_after_seq")
                last_seq_checked_at = requested_state.get("last_seq_checked_at")
                last_seq = requested_state.get("last_seq")
                existing = self.subscriptions.get(session_id)
                if existing is None:
                    state = SubscriptionState(
                        session_id=session_id,
                        after_seq=after_seq,
                        priority=priority,
                        mode=mode,
                        notebook_uuid=notebook_uuid,
                    )
                    state.notebook_uuid_valid = True
                    state.notebook_uuid_error = None
                    state.clamped_after_seq = clamped_after_seq
                    state.last_seq_checked_at = last_seq_checked_at
                    state.last_seq_seen = after_seq
                    state.last_forwarded_seq = after_seq
                    state.pending_gap_event = None
                    if isinstance(last_seq, int) and last_seq > after_seq:
                        state.backfill_after_seq = after_seq
                        state.backfill_until_seq = last_seq
                    self.subscriptions[session_id] = state
                    self._register_in_order(session_id, priority)
                    self._maybe_mark_degraded(state)
                    if state.backfill_until_seq is None and self._scope_stream is not None:
                        if self._scope_stream._state == "connected":
                            pending_connected.append(session_id)
                    results.append({
                        "session_id": session_id,
                        "accepted": True,
                        "message": requested_state.get("resolve_message") or "subscribed",
                        "effective_after_seq": after_seq,
                    })
                    continue

                if existing.priority != priority:
                    self._move_in_order(session_id, existing.priority, priority)
                restart = after_seq != existing.after_seq or existing.stop_requested
                existing.after_seq = after_seq
                existing.stop_requested = False
                existing.priority = priority
                existing.mode = mode
                existing.notebook_uuid = notebook_uuid or existing.notebook_uuid
                existing.notebook_uuid_valid = True
                existing.notebook_uuid_error = None
                existing.degraded = existing.degraded and priority == "background"
                existing.clamped_after_seq = clamped_after_seq
                existing.last_seq_checked_at = last_seq_checked_at or existing.last_seq_checked_at
                if existing.last_forwarded_seq is None:
                    existing.last_forwarded_seq = existing.after_seq
                self._maybe_mark_degraded(existing)
                if restart:
                    if existing.pending_events:
                        self._pending_count -= len(existing.pending_events)
                        existing.pending_events.clear()
                    existing.pending_gap_event = None
                    existing.last_seq_seen = after_seq
                    existing.last_forwarded_seq = after_seq
                    existing.backfill_buffer.clear()
                    if existing.backfill_task and not existing.backfill_task.done():
                        existing.backfill_task.cancel()
                    existing.backfill_task = None
                if isinstance(last_seq, int):
                    current_seen = existing.last_seq_seen or after_seq
                    if last_seq > current_seen:
                        existing.backfill_after_seq = current_seen
                        existing.backfill_until_seq = last_seq
                    else:
                        existing.backfill_after_seq = None
                        existing.backfill_until_seq = None
                if existing.backfill_until_seq is None and self._scope_stream is not None:
                    if self._scope_stream._state == "connected":
                        pending_connected.append(session_id)
                results.append({
                    "session_id": session_id,
                    "accepted": True,
                    "message": requested_state.get("resolve_message") or "updated",
                    "effective_after_seq": after_seq,
                })
        for session_id in pending_connected:
            await self._emit_subscription_state(session_id, "connected")

        if not self.subscriptions:
            await self._detach_scope_stream()
        elif self._writer is not None:
            await self._ensure_scope_stream()
            await self._start_pending_backfills()
        return results

    def handle_scope_event(self, payload: dict[str, Any], event_id: int | None) -> None:
        session_id = payload.get("session_id")
        if not isinstance(session_id, str):
            return
        state = self.subscriptions.get(session_id)
        if state is None or state.stop_requested:
            return
        seq = payload.get("seq")
        if isinstance(seq, float) and seq.is_integer():
            seq = int(seq)
        if not isinstance(seq, int):
            return
        if state.backfill_task and not state.backfill_task.done():
            state.backfill_buffer.append(payload)
        elif state.backfill_until_seq is not None:
            state.backfill_buffer.append(payload)
        else:
            self._process_payload(state, payload)
            return
        if len(state.backfill_buffer) > self.outbound_queue_max:
            logger.warning(
                "Backfill buffer overflow for %s; closing stream %s",
                session_id,
                self.stream_id,
            )
            self.close(code="CLIENT_OVERLOADED", message="Backfill buffer overflow")

    async def handle_scope_state(
        self,
        state: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        async with self._subscriptions_lock:
            subscriptions = list(self.subscriptions.values())
        for sub_state in subscriptions:
            if sub_state.stop_requested:
                continue
            if state == "connected" and sub_state.backfill_until_seq is not None:
                continue
            sub_state.connected = state == "connected"
            await self._emit_subscription_state(sub_state.session_id, state, details)

    def _flush_backfill_buffer(self, state: SubscriptionState) -> None:
        if not state.backfill_buffer:
            return
        buffer = state.backfill_buffer
        state.backfill_buffer = []
        buffer.sort(key=lambda item: item.get("seq") or 0)
        for payload in buffer:
            self._process_payload(state, payload)

    async def _run_backfill(self, state: SubscriptionState) -> None:
        try:
            async with self.backfill_semaphore, self.backfill_semaphore_global:
                while not state.stop_requested and not self._closed:
                    start_after_seq = state.backfill_after_seq
                    stop_after_seq = state.backfill_until_seq
                    if stop_after_seq is None:
                        return
                    if start_after_seq is None:
                        start_after_seq = state.after_seq
                    headers = await self.upstream_headers_provider(self)
                    if headers is None:
                        await self._emit_subscription_state(
                            state.session_id,
                            "backoff",
                            {
                                "http_status": 401,
                                "message": "Unauthorized",
                                "retry_in_ms": 15000,
                            },
                        )
                        await asyncio.sleep(15)
                        continue
                    fetch_mode = self._effective_mode(state)
                    types: list[str] | None = None
                    ui_subtypes: list[str] | None = None
                    if fetch_mode == "tools_only":
                        types = sorted(_TOOLS_ONLY_EVENT_TYPES | {"ui_event"})
                        ui_subtypes = sorted(_UI_TERMINAL_SUBTYPES)
                    events, last_seq, status_code, error_payload = await self._fetch_events_page(
                        state.session_id,
                        start_after_seq or 0,
                        self.backfill_page_limit,
                        types,
                        ui_subtypes,
                        headers,
                    )
                    if status_code is not None and status_code >= 400:
                        await self._handle_upstream_error(state, status_code, error_payload)
                        continue
                    if last_seq is not None and stop_after_seq is not None:
                        stop_after_seq = min(stop_after_seq, last_seq)
                        state.backfill_until_seq = stop_after_seq
                    if not events:
                        if fetch_mode == "tools_only" and stop_after_seq is not None:
                            from_seq = state.last_forwarded_seq
                            if from_seq is None:
                                from_seq = state.after_seq
                            if from_seq is None:
                                from_seq = 0
                            if stop_after_seq > from_seq:
                                self._enqueue_gap_event(
                                    state,
                                    from_seq,
                                    stop_after_seq,
                                    self._suppression_reason(state),
                                )
                                state.last_seq_seen = stop_after_seq
                        if stop_after_seq is not None:
                            state.backfill_until_seq = None
                            state.backfill_after_seq = None
                            self._flush_backfill_buffer(state)
                            await self._emit_subscription_state(state.session_id, "connected")
                            return
                        return

                    previous_seen = state.last_seq_seen
                    max_page_seq: int | None = None
                    for payload in events:
                        if state.stop_requested or self._closed:
                            break
                        seq = self._coerce_seq(payload.get("seq"))
                        if seq is None:
                            continue
                        if max_page_seq is None or seq > max_page_seq:
                            max_page_seq = seq
                        if stop_after_seq is not None and seq > stop_after_seq:
                            break
                        if state.last_seq_seen is not None and seq <= state.last_seq_seen:
                            continue
                        if fetch_mode == "tools_only":
                            last_forwarded = state.last_forwarded_seq
                            if last_forwarded is None:
                                last_forwarded = state.after_seq or 0
                            if seq > last_forwarded + 1:
                                self._enqueue_gap_event(
                                    state,
                                    last_forwarded,
                                    seq - 1,
                                    self._suppression_reason(state),
                                )
                        self._process_payload(state, payload)
                        if stop_after_seq is not None and seq >= stop_after_seq:
                            break
                    if state.stop_requested or self._closed:
                        break
                    if (
                        stop_after_seq is not None
                        and state.last_seq_seen is not None
                        and state.last_seq_seen >= stop_after_seq
                    ):
                        if fetch_mode == "tools_only":
                            last_forwarded = state.last_forwarded_seq
                            if last_forwarded is None:
                                last_forwarded = state.after_seq or 0
                            if stop_after_seq > last_forwarded:
                                self._enqueue_gap_event(
                                    state,
                                    last_forwarded,
                                    stop_after_seq,
                                    self._suppression_reason(state),
                                )
                        state.backfill_until_seq = None
                        state.backfill_after_seq = None
                        self._flush_backfill_buffer(state)
                        await self._emit_subscription_state(state.session_id, "connected")
                        return
                    if state.last_seq_seen == previous_seen and events:
                        progress_seq = max_page_seq
                        if progress_seq is None:
                            progress_seq = state.last_seq_seen
                        if progress_seq is None:
                            progress_seq = start_after_seq
                        if progress_seq < start_after_seq:
                            progress_seq = start_after_seq
                        state.backfill_after_seq = progress_seq
                    else:
                        state.backfill_after_seq = state.last_seq_seen or max_page_seq or start_after_seq
            state.connected = False
        finally:
            state.backfill_task = None

    async def _fetch_events_page(
        self,
        session_id: str,
        after_seq: int,
        limit: int,
        types: list[str] | None,
        ui_subtypes: list[str] | None,
        headers: dict[str, str],
    ) -> tuple[list[dict[str, Any]], int | None, int | None, dict[str, Any] | None]:
        url = f"{self.orchestrator_url}/v1/sessions/{session_id}/events/page"
        params: dict[str, str] = {
            "after_seq": str(max(0, after_seq)),
            "limit": str(max(1, limit)),
        }
        if types:
            params["types"] = ",".join(types)
        if ui_subtypes:
            params["ui_subtypes"] = ",".join(ui_subtypes)
        timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=None)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers, params=params)
        except Exception as exc:
            logger.warning("Backfill page request failed for %s: %s", session_id, exc)
            return [], None, 503, {"detail": {"code": "UPSTREAM_ERROR", "message": str(exc)}}
        if response.status_code >= 400:
            error_payload = None
            try:
                raw = response.json()
                if isinstance(raw, dict):
                    error_payload = raw
            except Exception:
                error_payload = None
            return [], None, response.status_code, error_payload
        try:
            payload = response.json()
        except Exception:
            return [], None, 502, {"detail": {"code": "BAD_RESPONSE", "message": "Invalid JSON"}}
        if not isinstance(payload, dict):
            return [], None, response.status_code, None
        events_raw = payload.get("events")
        events: list[dict[str, Any]] = []
        if isinstance(events_raw, list):
            for item in events_raw:
                if isinstance(item, dict):
                    events.append(item)
        last_seq = payload.get("last_seq")
        if isinstance(last_seq, float) and last_seq.is_integer():
            last_seq = int(last_seq)
        if not isinstance(last_seq, int):
            last_seq = None
        return events, last_seq, response.status_code, None

    async def _emit_subscription_state(
        self,
        session_id: str,
        state: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        payload_details = dict(details) if isinstance(details, dict) else {}
        legacy_last_seq = payload_details.get("last_seq")
        if "known_last_seq" not in payload_details:
            if isinstance(legacy_last_seq, float) and legacy_last_seq.is_integer():
                legacy_last_seq = int(legacy_last_seq)
            if isinstance(legacy_last_seq, int):
                payload_details["known_last_seq"] = legacy_last_seq
        payload_details.pop("last_seq", None)
        sub_state = self.subscriptions.get(session_id)
        sidecar_ready = self._is_sidecar_ready(sub_state) if sub_state else False
        if sub_state:
            sub_state.sidecar_ready = sidecar_ready
            last_seq = self._subscription_last_seq(sub_state)
            if last_seq is not None:
                payload_details.setdefault("known_last_seq", last_seq)
        payload_details.setdefault("sidecar_ready", sidecar_ready)
        if sub_state and sub_state.sidecar_paused:
            if sub_state.sidecar_pause_reason == "backlog":
                payload_details.setdefault("sidecar_state", "paused_due_to_backlog")
            else:
                payload_details.setdefault("sidecar_state", "paused")
        elif sidecar_ready:
            payload_details.setdefault("sidecar_state", "ready")
        else:
            payload_details.setdefault("sidecar_state", "pending_path")
        payload = {
            "session_id": session_id,
            "state": state,
            "details": payload_details,
        }
        self.enqueue_event("subscription_state", payload)

    def _subscription_last_seq(self, state: SubscriptionState) -> int | None:
        last_seq = state.last_seq_seen
        if isinstance(last_seq, float) and last_seq.is_integer():
            last_seq = int(last_seq)
        if not isinstance(last_seq, int):
            last_seq = None
        if state.backfill_until_seq is not None:
            if last_seq is None or state.backfill_until_seq > last_seq:
                last_seq = state.backfill_until_seq
        return last_seq

    async def _get_last_seq(self, session_id: str) -> int | None:
        now = time.time()
        cached = self._cursor_cache.get(session_id)
        if cached and (now - cached[1]) < self.cursor_cache_ttl:
            return cached[0]
        last_seq = await self._fetch_last_seq(session_id)
        if last_seq is not None:
            self._cursor_cache[session_id] = (last_seq, now)
        return last_seq

    async def _get_last_seq_bulk(self, session_ids: list[str]) -> dict[str, int | None]:
        if not session_ids:
            return {}
        concurrency = max(1, self.cursor_prefetch_concurrency)
        semaphore = asyncio.Semaphore(concurrency)
        results: dict[str, int | None] = {}

        async def _fetch(session_id: str) -> None:
            async with semaphore:
                results[session_id] = await self._get_last_seq(session_id)

        await asyncio.gather(*(_fetch(session_id) for session_id in session_ids))
        return results

    async def _fetch_last_seq(self, session_id: str) -> int | None:
        headers = await self.upstream_headers_provider(self)
        if headers is None:
            return None
        url = f"{self.orchestrator_url}/v1/sessions/{session_id}"
        timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=None)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
        except Exception as exc:
            logger.debug("Failed to fetch last_seq for %s: %s", session_id, exc)
            return None
        if response.status_code != 200:
            return None
        try:
            payload = response.json()
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        last_seq = payload.get("last_seq")
        if isinstance(last_seq, int):
            return last_seq
        if isinstance(last_seq, float) and last_seq.is_integer():
            return int(last_seq)
        return None

    def _extract_notebook_uuid(self, payload: dict[str, Any]) -> str | None:
        notebook_uuid = payload.get("notebook_uuid")
        if isinstance(notebook_uuid, str) and notebook_uuid:
            return notebook_uuid
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            meta_uuid = metadata.get("notebook_uuid") or metadata.get("notebook_id")
            if isinstance(meta_uuid, str) and meta_uuid:
                return meta_uuid
        return None

    async def _fetch_session_notebook_uuid(self, session_id: str) -> str | None:
        headers = await self.upstream_headers_provider(self)
        if headers is None:
            return None
        url = f"{self.orchestrator_url}/v1/sessions/{session_id}"
        timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=None)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
        except Exception as exc:
            logger.debug("Failed to fetch session metadata for %s: %s", session_id, exc)
            return None
        if response.status_code != 200:
            return None
        try:
            payload = response.json()
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        return self._extract_notebook_uuid(payload)

    async def _get_session_notebook_uuid(self, session_id: str) -> str | None:
        now = time.time()
        cached = self._session_metadata_cache.get(session_id)
        if cached and (now - cached[1]) < self.session_metadata_cache_ttl:
            return cached[0]
        inflight = self._session_metadata_inflight.get(session_id)
        if inflight:
            try:
                return await inflight
            except Exception:
                return None
        task = asyncio.create_task(self._fetch_session_notebook_uuid(session_id))
        self._session_metadata_inflight[session_id] = task
        try:
            notebook_uuid = await task
        finally:
            self._session_metadata_inflight.pop(session_id, None)
        self._session_metadata_cache[session_id] = (notebook_uuid, now)
        return notebook_uuid

    async def _get_session_notebook_uuid_bulk(self, session_ids: list[str]) -> dict[str, str | None]:
        if not session_ids:
            return {}
        concurrency = max(1, int(self.session_metadata_prefetch_concurrency))
        semaphore = asyncio.Semaphore(concurrency)
        results: dict[str, str | None] = {}

        async def _fetch(session_id: str) -> None:
            async with semaphore:
                results[session_id] = await self._get_session_notebook_uuid(session_id)

        await asyncio.gather(*(_fetch(session_id) for session_id in session_ids))
        return results

    async def _validate_notebook_uuid_assignments(
        self,
        subscriptions: dict[str, dict[str, Any]],
    ) -> dict[str, str]:
        session_ids = [
            session_id
            for session_id, sub in subscriptions.items()
            if isinstance(sub.get("notebook_uuid"), str) and sub.get("notebook_uuid")
        ]
        if not session_ids:
            return {}
        resolved = await self._get_session_notebook_uuid_bulk(session_ids)
        errors: dict[str, str] = {}
        for session_id in session_ids:
            pinned = resolved.get(session_id)
            requested = subscriptions[session_id].get("notebook_uuid")
            if isinstance(pinned, str) and pinned and pinned != requested:
                errors[session_id] = pinned
        return errors

    def _emit_events_gap(
        self,
        session_id: str,
        requested_after_seq: int,
        effective_after_seq: int,
        last_seq: int,
        reason: str,
    ) -> None:
        payload = {
            "session_id": session_id,
            "seq": None,
            "type": "events_gap",
            "turn_id": None,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data": {
                "requested_after_seq": requested_after_seq,
                "effective_after_seq": effective_after_seq,
                "last_seq": last_seq,
                "reason": reason,
            },
        }
        self.enqueue_event("mux_event", payload, include_mux_seq=True)

    def _register_in_order(self, session_id: str, priority: str) -> None:
        if session_id not in self._all_order:
            self._all_order.append(session_id)
        order = self._foreground_order if priority == "foreground" else self._background_order
        if session_id not in order:
            order.append(session_id)

    def _remove_from_order(self, session_id: str, priority: str) -> None:
        try:
            self._all_order.remove(session_id)
        except ValueError:
            pass
        order = self._foreground_order if priority == "foreground" else self._background_order
        try:
            order.remove(session_id)
        except ValueError:
            pass

    def _move_in_order(self, session_id: str, old_priority: str, new_priority: str) -> None:
        self._remove_from_order(session_id, old_priority)
        self._register_in_order(session_id, new_priority)

    def _buffer_sidecar_event(self, state: SubscriptionState, payload: dict[str, Any]) -> None:
        if not self.contents_manager:
            return
        if state.notebook_uuid is None:
            return
        if not state.notebook_uuid_valid:
            return
        if state.sidecar_paused:
            return
        notebook_path = self._resolve_notebook_path(state.notebook_uuid)
        if not notebook_path:
            return
        if not state.sidecar_ready and not state.sidecar_paused:
            state.sidecar_ready = True
            asyncio.create_task(self._emit_subscription_state(state.session_id, "connected"))
        event_type = payload.get("type")
        if event_type not in _SIDECAR_EVENT_TYPES:
            return
        seq = payload.get("seq")
        if not isinstance(seq, int):
            if isinstance(seq, float) and seq.is_integer():
                seq = int(seq)
            else:
                return
        thread_id = payload.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            thread_id = state.session_id
        record = {
            "seq": seq,
            "type": event_type,
            "session_id": state.session_id,
            "thread_id": thread_id,
            "turn_id": payload.get("turn_id"),
            "ts": payload.get("ts"),
            "data": payload.get("data") if isinstance(payload.get("data"), dict) else {},
        }
        key = (state.notebook_uuid, thread_id, state.session_id)
        pending = self._sidecar_pending.get(key)
        if pending is None:
            pending = []
            self._sidecar_pending[key] = pending
        if self.sidecar_pending_max_events > 0 and len(pending) >= self.sidecar_pending_max_events:
            self._pause_sidecar_subscription(state, len(pending), "backlog")
            self._schedule_sidecar_flush()
            return
        pending.append(record)
        self._schedule_sidecar_flush()

    def _pause_sidecar_subscription(self, state: SubscriptionState, pending_count: int, reason: str) -> None:
        if state.sidecar_paused or state.stop_requested or self._closed:
            return
        state.sidecar_paused = True
        state.sidecar_pause_reason = reason
        state.sidecar_pause_at = time.time()
        state.sidecar_ready = False
        logger.warning(
            "Sidecar buffer cap hit for %s/%s; pausing sidecar buffering at %s pending events",
            state.notebook_uuid,
            state.session_id,
            pending_count,
        )
        try:
            asyncio.create_task(
                self._emit_subscription_state(
                    state.session_id,
                    "paused",
                    {
                        "message": "Sidecar backlog exceeded; buffering paused",
                        "reason": "sidecar_backlog_exceeded",
                        "sidecar_state": "paused_due_to_backlog",
                    },
                )
            )
        except RuntimeError:
            logger.debug("No running loop to emit subscription_state for %s", state.session_id)

    def _schedule_sidecar_flush(self) -> None:
        if self._sidecar_flush_task and not self._sidecar_flush_task.done():
            return
        self._sidecar_flush_task = asyncio.create_task(self._sidecar_flush_loop())

    async def _sidecar_flush_loop(self) -> None:
        try:
            while not self._closed:
                await asyncio.sleep(self.sidecar_flush_interval)
                await asyncio.shield(self._flush_sidecar_pending())
        except asyncio.CancelledError:
            return

    async def _flush_sidecar_pending(self) -> None:
        if not self.contents_manager:
            return
        async with self._sidecar_flush_lock:
            if not self._sidecar_pending:
                return
            items = list(self._sidecar_pending.items())
            self._sidecar_pending = {}
        for (notebook_uuid, thread_id, session_id), events in items:
            if not events:
                continue
            notebook_path = self._resolve_notebook_path(notebook_uuid)
            if not notebook_path:
                async with self._sidecar_flush_lock:
                    existing = self._sidecar_pending.get((notebook_uuid, thread_id, session_id))
                    if existing:
                        existing.extend(events)
                    else:
                        self._sidecar_pending[(notebook_uuid, thread_id, session_id)] = events
                continue
            events.sort(key=lambda item: item["seq"])
            await asyncio.to_thread(
                _append_sidecar_events,
                self.contents_manager,
                notebook_path,
                notebook_uuid,
                thread_id,
                session_id,
                events,
            )
            session_id = events[0].get("session_id") if events else None
            state = self.subscriptions.get(session_id) if session_id else None
            if state and state.sidecar_paused and state.sidecar_pause_reason == "backlog":
                state.sidecar_paused = False
                state.sidecar_pause_reason = None
                state.sidecar_pause_at = None
                if self._writer is not None and not state.stop_requested:
                    try:
                        asyncio.create_task(
                            self._emit_subscription_state(
                                state.session_id,
                                "connected",
                                {"reason": "sidecar_backlog_drained"},
                            )
                        )
                    except RuntimeError:
                        logger.debug("No running loop to emit subscription_state for %s", state.session_id)

    def _is_sidecar_ready(self, state: SubscriptionState | None) -> bool:
        if not state or state.sidecar_paused:
            return False
        if not self.contents_manager or not state.notebook_uuid:
            return False
        if not state.notebook_uuid_valid:
            return False
        return bool(self._resolve_notebook_path(state.notebook_uuid))

    def _resolve_notebook_path(self, notebook_uuid: str) -> str | None:
        if not self.notebook_registry:
            return None
        return self.notebook_registry.get_path(notebook_uuid)

    async def _run_subscription(self, state: SubscriptionState) -> None:
        while not state.stop_requested and not self._closed:
            headers = await self.upstream_headers_provider(self)
            if headers is None:
                await self._emit_subscription_state(
                    state.session_id,
                    "backoff",
                    {
                        "http_status": 401,
                        "message": "Unauthorized",
                        "retry_in_ms": 15000,
                    },
                )
                await asyncio.sleep(15)
                continue

            url = f"{self.orchestrator_url}/v1/sessions/{state.session_id}/events"
            params: list[str] = []
            if state.after_seq:
                params.append(f"after_seq={state.after_seq}")
            if params:
                url = f"{url}?{'&'.join(params)}"
            headers = dict(headers)
            headers["Accept"] = "text/event-stream"

            timeout = httpx.Timeout(connect=30.0, read=None, write=None, pool=None)
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("GET", url, headers=headers) as response:
                        if response.status_code >= 400:
                            error_payload = None
                            try:
                                raw = await response.aread()
                                if raw:
                                    error_payload = json.loads(raw)
                            except Exception:
                                error_payload = None
                            await self._handle_upstream_error(state, response.status_code, error_payload)
                            continue

                        state.connected = True
                        state.backoff_attempts = 0
                        await self._emit_subscription_state(state.session_id, "connected")
                        async for event in _iter_sse_events(response):
                            if state.stop_requested or self._closed:
                                break
                            payload = _parse_upstream_event(event, state.session_id)
                            if payload is None:
                                continue
                            self._process_payload(state, payload)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(
                    "Upstream stream error for %s: %s", state.session_id, exc
                )
                await self._handle_upstream_error(state, None)

        state.connected = False

    async def _ensure_subscription_tasks(self) -> None:
        async with self._subscriptions_lock:
            for state in self.subscriptions.values():
                if state.stop_requested:
                    continue
                if state.sidecar_paused:
                    continue
                if state.upstream_task and not state.upstream_task.done():
                    continue
                state.upstream_task = asyncio.create_task(self._run_subscription(state))

    async def _finalize_sidecar_flush(self) -> None:
        try:
            await self._flush_sidecar_pending()
        except Exception:
            logger.exception("Failed to finalize sidecar flush for %s", self.stream_id)

    async def _handle_upstream_error(
        self,
        state: SubscriptionState,
        status_code: int | None,
        error_payload: dict[str, Any] | None = None,
    ) -> None:
        if state.stop_requested or self._closed:
            return
        state.connected = False
        retry_ms = int(min(_MAX_BACKOFF_SECONDS, 2 ** state.backoff_attempts) * 1000)
        message = "Upstream connection failed"
        if status_code == 400:
            error_code, last_seq = _extract_error_detail(error_payload)
            if error_code == "RESUME_CURSOR_INVALID" and last_seq is not None:
                requested_after_seq = state.after_seq
                effective_after_seq = max(0, min(requested_after_seq, last_seq))
                backfill_task = state.backfill_task
                if backfill_task and not backfill_task.done():
                    backfill_task.cancel()
                    try:
                        await backfill_task
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        logger.exception("Failed to cancel backfill task for %s", state.session_id)
                now = time.time()
                async with self._subscriptions_lock:
                    if state.pending_events:
                        self._pending_count -= len(state.pending_events)
                        state.pending_events.clear()
                    removed = self._drop_sticky_events_for_session(state.session_id)
                    if removed:
                        self._pending_count = max(0, self._pending_count - removed)
                    state.pending_gap_event = None
                    state.backfill_buffer.clear()
                    state.backfill_after_seq = None
                    state.backfill_until_seq = None
                    state.backfill_task = None
                    state.after_seq = effective_after_seq
                    state.clamped_after_seq = effective_after_seq
                    state.last_seq_seen = effective_after_seq
                    state.last_forwarded_seq = effective_after_seq
                    state.last_seq_checked_at = now
                    if self._pending_count <= 0:
                        self._pending_event.clear()
                self._cursor_cache[state.session_id] = (last_seq, now)
                self._emit_events_gap(
                    state.session_id,
                    requested_after_seq,
                    effective_after_seq,
                    last_seq,
                    "RESUME_CURSOR_INVALID",
                )
                await self._emit_subscription_state(
                    state.session_id,
                    "connected",
                    {
                        "reason": "resume_cursor_invalid_clamped",
                        "effective_after_seq": effective_after_seq,
                        "known_last_seq": last_seq,
                    },
                )
                return
            await self._emit_subscription_state(
                state.session_id,
                "error",
                {"http_status": status_code, "message": message},
            )
            state.stop_requested = True
            return
        if status_code in (401,):
            retry_ms = 15000
            message = "Unauthorized"
        elif status_code == 429:
            retry_ms = 30000
            message = "Rate limited"
        elif status_code in (403, 404):
            await self._emit_subscription_state(
                state.session_id,
                "error",
                {"http_status": status_code, "message": "Session unavailable"},
            )
            state.stop_requested = True
            return

        state.backoff_attempts += 1
        await self._emit_subscription_state(
            state.session_id,
            "backoff",
            {"http_status": status_code, "message": message, "retry_in_ms": retry_ms},
        )
        await asyncio.sleep(retry_ms / 1000)


class ScopeStream:
    """Upstream scope-level SSE stream shared across mux streams."""

    def __init__(
        self,
        *,
        scope_key: str,
        identity: IdentityContext,
        identity_headers: dict[str, str],
        orchestrator_url: str,
        heartbeat_interval: float,
        headers_provider: Callable[[Any], Awaitable[dict[str, str] | None]],
        start_event_id: int | None = None,
    ) -> None:
        self.scope_key = scope_key
        self.identity = identity
        self.identity_headers = identity_headers
        self.orchestrator_url = orchestrator_url
        self.heartbeat_interval = heartbeat_interval
        self.headers_provider = headers_provider
        self.last_event_id = start_event_id or 0
        self._subscribers: dict[int, MuxStream] = {}
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._closed = False
        self._state = "disconnected"
        self._backoff_attempts = 0

    async def add_subscriber(self, stream: MuxStream, start_event_id: int | None) -> None:
        async with self._lock:
            self._subscribers[id(stream)] = stream
            if self._task is None or self._task.done():
                if start_event_id is not None:
                    self.last_event_id = start_event_id
                self._task = asyncio.create_task(self._run())
            state = self._state
        if state != "disconnected":
            await stream.handle_scope_state(state)

    async def remove_subscriber(self, stream: MuxStream) -> None:
        async with self._lock:
            self._subscribers.pop(id(stream), None)
            if self._subscribers:
                return
            task = self._task
            self._task = None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _notify_state(self, state: str, details: dict[str, Any] | None = None) -> None:
        async with self._lock:
            self._state = state
            subscribers = list(self._subscribers.values())
        for stream in subscribers:
            try:
                await stream.handle_scope_state(state, details)
            except Exception:
                logger.debug("Failed to notify scope state for %s", self.scope_key)

    async def _dispatch_event(self, payload: dict[str, Any], event_id: int) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.values())
        for stream in subscribers:
            try:
                stream.handle_scope_event(payload, event_id)
            except Exception:
                logger.debug("Failed to dispatch scope event for %s", self.scope_key)

    async def _run(self) -> None:
        while not self._closed:
            headers = await self.headers_provider(self)
            if headers is None:
                await self._notify_state(
                    "backoff",
                    {"http_status": 401, "message": "Unauthorized", "retry_in_ms": 15000},
                )
                await asyncio.sleep(15)
                continue
            url = f"{self.orchestrator_url}/v1/scopes/events"
            if self.last_event_id:
                url = f"{url}?after_event_id={self.last_event_id}"
            headers = dict(headers)
            headers["Accept"] = "text/event-stream"
            timeout = httpx.Timeout(connect=30.0, read=None, write=None, pool=None)
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("GET", url, headers=headers) as response:
                        if response.status_code >= 400:
                            error_payload = None
                            try:
                                raw = await response.aread()
                                if raw:
                                    error_payload = json.loads(raw)
                            except Exception:
                                error_payload = None
                            if response.status_code == 400:
                                last_event_id = None
                                if isinstance(error_payload, dict):
                                    detail = error_payload.get("detail")
                                    candidate = detail if isinstance(detail, dict) else error_payload
                                    if isinstance(candidate, dict):
                                        last_event_id = candidate.get("last_event_id")
                                if isinstance(last_event_id, int):
                                    self.last_event_id = last_event_id
                                await self._notify_state(
                                    "backoff",
                                    {
                                        "http_status": 400,
                                        "message": "Resume cursor invalid",
                                        "retry_in_ms": 1000,
                                    },
                                )
                                await asyncio.sleep(1)
                                continue
                            if response.status_code in (403, 404):
                                await self._notify_state(
                                    "error",
                                    {
                                        "http_status": response.status_code,
                                        "message": "Scope stream unavailable",
                                    },
                                )
                                await asyncio.sleep(30)
                                continue
                            retry_ms = int(min(_MAX_BACKOFF_SECONDS, 2 ** self._backoff_attempts) * 1000)
                            message = "Upstream connection failed"
                            if response.status_code == 401:
                                retry_ms = 15000
                                message = "Unauthorized"
                            elif response.status_code == 429:
                                retry_ms = 30000
                                message = "Rate limited"
                            await self._notify_state(
                                "backoff",
                                {
                                    "http_status": response.status_code,
                                    "message": message,
                                    "retry_in_ms": retry_ms,
                                },
                            )
                            self._backoff_attempts += 1
                            await asyncio.sleep(retry_ms / 1000)
                            continue

                        self._backoff_attempts = 0
                        await self._notify_state("connected")
                        async for event in _iter_sse_events(response):
                            if self._closed:
                                break
                            event_id, payload = _parse_scope_event(event)
                            if event_id is None or payload is None:
                                continue
                            if event_id <= self.last_event_id:
                                continue
                            self.last_event_id = event_id
                            await self._dispatch_event(payload, event_id)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("Scope stream error for %s: %s", self.scope_key, exc)
                retry_ms = int(min(_MAX_BACKOFF_SECONDS, 2 ** self._backoff_attempts) * 1000)
                self._backoff_attempts += 1
                await self._notify_state(
                    "backoff",
                    {
                        "message": "Scope stream error",
                        "retry_in_ms": retry_ms,
                    },
                )
                await asyncio.sleep(retry_ms / 1000)


class ScopeStreamManager:
    """Manage upstream scope streams."""

    def __init__(
        self,
        *,
        orchestrator_url: str,
        heartbeat_interval: float,
        headers_provider: Callable[[Any], Awaitable[dict[str, str] | None]],
    ) -> None:
        self.orchestrator_url = orchestrator_url
        self.heartbeat_interval = heartbeat_interval
        self.headers_provider = headers_provider
        self._streams: dict[str, ScopeStream] = {}
        self._lock = asyncio.Lock()

    async def attach(self, stream: MuxStream, start_event_id: int | None) -> ScopeStream:
        scope_key = _resolve_scope_key(stream.identity)
        async with self._lock:
            scope_stream = self._streams.get(scope_key)
            if scope_stream is None:
                scope_stream = ScopeStream(
                    scope_key=scope_key,
                    identity=stream.identity,
                    identity_headers=stream.identity_headers,
                    orchestrator_url=self.orchestrator_url,
                    heartbeat_interval=self.heartbeat_interval,
                    headers_provider=self.headers_provider,
                    start_event_id=start_event_id,
                )
                self._streams[scope_key] = scope_stream
        await scope_stream.add_subscriber(stream, start_event_id)
        return scope_stream

    async def detach(self, stream: MuxStream) -> None:
        scope_key = _resolve_scope_key(stream.identity)
        async with self._lock:
            scope_stream = self._streams.get(scope_key)
        if scope_stream is None:
            return
        await scope_stream.remove_subscriber(stream)
        async with self._lock:
            if scope_stream._subscribers:
                return
            if self._streams.get(scope_key) is scope_stream:
                self._streams.pop(scope_key, None)


class MuxStreamManager:
    """Global manager for mux streams."""

    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        connector_settings = settings.get("jupyter_ai_connector", {})
        self.orchestrator_url = connector_settings.get("orchestrator_url", "http://localhost:8000")
        self.orchestrator_token = connector_settings.get("orchestrator_token", "")
        self.auth0_domain = connector_settings.get("auth0_domain", "")
        self.auth0_client_id = connector_settings.get("auth0_client_id", "")
        self.max_subscriptions = int(connector_settings.get("mux_max_subscriptions", 50))
        self.outbound_queue_max = int(connector_settings.get("mux_outbound_queue_max", 2000))
        self.write_batch_size = int(connector_settings.get("mux_write_batch_size", 50))
        self.ttl_seconds = float(connector_settings.get("mux_stream_ttl_ms", 600000)) / 1000.0
        self.heartbeat_interval = float(connector_settings.get("heartbeat_interval", 15.0))
        self.contents_manager = settings.get("contents_manager")
        self.sidecar_flush_interval = float(
            connector_settings.get("mux_sidecar_flush_ms", 5000)
        ) / 1000.0
        self.sidecar_pending_max_events = int(
            connector_settings.get("mux_sidecar_pending_max_events", 2000)
        )
        self.backfill_page_limit = int(connector_settings.get("mux_backfill_page_limit", 200))
        self.backfill_concurrency_global = max(
            1, int(connector_settings.get("mux_backfill_concurrency_global", 8))
        )
        self.backfill_concurrency_per_stream = max(
            1, int(connector_settings.get("mux_backfill_concurrency_per_stream", 2))
        )
        self.cursor_cache_ttl = float(
            connector_settings.get("mux_cursor_cache_ms", 5000)
        ) / 1000.0
        self.cursor_prefetch_concurrency = max(
            1,
            int(connector_settings.get("mux_cursor_prefetch_concurrency", 6)),
        )
        self.session_metadata_cache_ttl = float(
            connector_settings.get("mux_session_metadata_cache_ms", 60000)
        ) / 1000.0
        self.session_metadata_prefetch_concurrency = max(
            1,
            int(connector_settings.get("mux_session_metadata_prefetch_concurrency", 6)),
        )
        self.notebook_registry = get_notebook_registry(settings)
        self.streams: dict[str, MuxStream] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None
        self._cleanup_interval = max(5.0, min(30.0, self.ttl_seconds / 2))
        self.scope_manager = ScopeStreamManager(
            orchestrator_url=self.orchestrator_url,
            heartbeat_interval=self.heartbeat_interval,
            headers_provider=self.build_upstream_headers,
        )
        self._backfill_semaphore_global = asyncio.Semaphore(self.backfill_concurrency_global)

    def _auth0_configured(self) -> bool:
        return bool(self.auth0_domain and self.auth0_client_id)

    async def _get_auth_token(self, user_ids: list[str]) -> str | None:
        if self.orchestrator_token:
            return self.orchestrator_token
        if not self._auth0_configured():
            return None
        token_store = get_token_store(self.settings)
        for user_id in user_ids:
            if not user_id:
                continue
            token = await token_store.get_valid_token(user_id)
            if token:
                return token
        return None

    async def build_upstream_headers(self, stream: MuxStream) -> dict[str, str] | None:
        browser_id = stream.identity_headers.get("X-JAI-Browser-Id")
        user_ids: list[str] = []
        if isinstance(browser_id, str) and browser_id:
            user_ids.append(f"browser:{browser_id}")
        if stream.identity.end_user_subject:
            user_ids.append(stream.identity.end_user_subject)
        token = await self._get_auth_token(user_ids)
        if not token:
            return None
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "X-Request-Id": str(uuid.uuid4()),
        }
        headers.update(stream.identity_headers)
        return headers

    async def create_stream(
        self,
        identity: IdentityContext,
        identity_headers: dict[str, str],
    ) -> MuxStream:
        async with self._lock:
            self._ensure_cleanup_task()
            self._cleanup_expired_locked()
            stream_id = _generate_stream_id()
            while stream_id in self.streams:
                stream_id = _generate_stream_id()
            stream = MuxStream(
                stream_id=stream_id,
                identity=identity,
                identity_headers=identity_headers,
                orchestrator_url=self.orchestrator_url,
                heartbeat_interval=self.heartbeat_interval,
                max_subscriptions=self.max_subscriptions,
                outbound_queue_max=self.outbound_queue_max,
                write_batch_size=self.write_batch_size,
                ttl_seconds=self.ttl_seconds,
                contents_manager=self.contents_manager,
                sidecar_flush_interval=self.sidecar_flush_interval,
                sidecar_pending_max_events=self.sidecar_pending_max_events,
                backfill_page_limit=self.backfill_page_limit,
                backfill_semaphore=asyncio.Semaphore(self.backfill_concurrency_per_stream),
                backfill_semaphore_global=self._backfill_semaphore_global,
                notebook_registry=self.notebook_registry,
                cursor_cache_ttl=self.cursor_cache_ttl,
                cursor_prefetch_concurrency=self.cursor_prefetch_concurrency,
                session_metadata_cache_ttl=self.session_metadata_cache_ttl,
                session_metadata_prefetch_concurrency=self.session_metadata_prefetch_concurrency,
                upstream_headers_provider=self.build_upstream_headers,
                scope_manager=self.scope_manager,
            )
            self.streams[stream_id] = stream
            logger.info("Created mux stream %s", stream_id)
            return stream

    async def get_stream(self, stream_id: str) -> MuxStream | None:
        async with self._lock:
            self._ensure_cleanup_task()
            self._cleanup_expired_locked()
            return self.streams.get(stream_id)

    async def delete_stream(self, stream_id: str) -> None:
        async with self._lock:
            stream = self.streams.pop(stream_id, None)
        if stream:
            stream.close(code="STREAM_EXPIRED", message="Stream closed")
            logger.info("Deleted mux stream %s", stream_id)

    async def shutdown(self) -> None:
        async with self._lock:
            streams = list(self.streams.values())
            self.streams.clear()
        for stream in streams:
            stream.close(code="STREAM_EXPIRED", message="Stream closed")
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    def _cleanup_expired_locked(self) -> None:
        expired = [stream_id for stream_id, stream in self.streams.items() if stream.is_expired()]
        for stream_id in expired:
            stream = self.streams.pop(stream_id, None)
            if stream:
                stream.close(code="STREAM_EXPIRED", message="Stream expired")
                logger.info("Expired mux stream %s", stream_id)

    def _ensure_cleanup_task(self) -> None:
        if self._cleanup_task and not self._cleanup_task.done():
            return
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._cleanup_interval)
                async with self._lock:
                    self._cleanup_expired_locked()
        except asyncio.CancelledError:
            return


def get_mux_manager(settings: dict[str, Any]) -> MuxStreamManager:
    manager = settings.get("jupyter_ai_connector_mux_manager")
    if manager is None:
        manager = MuxStreamManager(settings)
        settings["jupyter_ai_connector_mux_manager"] = manager
    return manager


def _generate_stream_id() -> str:
    return secrets.token_urlsafe(18)


def _get_sidecar_lock(path: str) -> threading.Lock:
    with _SIDECAR_LOCKS_GUARD:
        lock = _SIDECAR_LOCKS.get(path)
        if lock is None:
            lock = threading.Lock()
            _SIDECAR_LOCKS[path] = lock
        return lock


def _append_sidecar_events(
    contents_manager: Any,
    notebook_path: str,
    notebook_uuid: str,
    thread_id: str,
    session_id: str,
    events: list[dict[str, Any]],
) -> None:
    if not events:
        return
    get_os_path = getattr(contents_manager, "_get_os_path", None) or getattr(
        contents_manager, "get_os_path", None
    )
    if get_os_path is None:
        return
    events_rel_path = _sidecar_events_path(notebook_path, notebook_uuid, thread_id, session_id)
    events_path = get_os_path(events_rel_path)
    os.makedirs(os.path.dirname(events_path), exist_ok=True)
    lock = _get_sidecar_lock(events_path)
    with lock:
        last_seq = _read_last_seq(events_path)
        pending = [event for event in events if event["seq"] > last_seq]
        if not pending:
            return
        with open(events_path, "a", encoding="utf-8") as handle:
            for event in pending:
                handle.write(json.dumps(event))
                handle.write("\n")


@dataclass
class ParsedSSEEvent:
    event: str | None = None
    data: str = ""
    event_id: str | None = None


async def _iter_sse_events(response: httpx.Response) -> AsyncIterator[ParsedSSEEvent]:
    event_name: str | None = None
    event_id: str | None = None
    data_lines: list[str] = []
    async for raw_line in response.aiter_lines():
        if raw_line == "":
            if event_name or event_id or data_lines:
                yield ParsedSSEEvent(
                    event=event_name,
                    data="\n".join(data_lines),
                    event_id=event_id,
                )
            event_name = None
            event_id = None
            data_lines = []
            continue
        if raw_line.startswith(":"):
            continue
        field, _, value = raw_line.partition(":")
        if value.startswith(" "):
            value = value[1:]
        if field == "event":
            event_name = value
        elif field == "id":
            event_id = value
        elif field == "data":
            data_lines.append(value)

    if event_name or event_id or data_lines:
        yield ParsedSSEEvent(event=event_name, data="\n".join(data_lines), event_id=event_id)


def _parse_upstream_event(event: ParsedSSEEvent, session_id: str) -> dict[str, Any] | None:
    if not event.data:
        return None
    try:
        envelope = json.loads(event.data)
    except json.JSONDecodeError:
        logger.debug("Failed to decode upstream event data")
        return None
    if not isinstance(envelope, dict):
        return None
    if envelope.get("session_id") and envelope.get("session_id") != session_id:
        logger.warning(
            "Skipping event for mismatched session %s (expected %s)",
            envelope.get("session_id"),
            session_id,
        )
        return None
    thread_id = envelope.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id:
        thread_id = session_id
    event_type = envelope.get("type") or event.event
    if not isinstance(event_type, str):
        return None
    return {
        "session_id": session_id,
        "thread_id": thread_id,
        "seq": envelope.get("seq"),
        "type": event_type,
        "turn_id": envelope.get("turn_id"),
        "ts": envelope.get("ts"),
        "data": envelope.get("data") if isinstance(envelope.get("data"), dict) else {},
        "protocol_version": envelope.get("protocol_version"),
    }


def _parse_scope_event(event: ParsedSSEEvent) -> tuple[int | None, dict[str, Any] | None]:
    if not event.data:
        return None, None
    try:
        envelope = json.loads(event.data)
    except json.JSONDecodeError:
        logger.debug("Failed to decode scope event data")
        return None, None
    if not isinstance(envelope, dict):
        return None, None
    event_id = None
    if event.event_id:
        try:
            event_id = int(event.event_id)
        except ValueError:
            event_id = None
    return event_id, envelope


def _extract_error_detail(payload: dict[str, Any] | None) -> tuple[str | None, int | None]:
    if not isinstance(payload, dict):
        return None, None
    detail = payload.get("detail")
    candidate = detail if isinstance(detail, dict) else payload
    if not isinstance(candidate, dict):
        return None, None
    code = candidate.get("code") if isinstance(candidate.get("code"), str) else None
    last_seq = candidate.get("last_seq")
    if isinstance(last_seq, int):
        return code, last_seq
    if isinstance(last_seq, float) and last_seq.is_integer():
        return code, int(last_seq)
    return code, None
