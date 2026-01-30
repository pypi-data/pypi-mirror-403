"""Handlers for multiplexed SSE streams."""

import json
import logging
from typing import Any

from .base import BaseProxyHandler
from ..auth.identity import IdentityMapper
from ..mux import IdentityContext, get_mux_manager
from .notebooks import get_notebook_registry

logger = logging.getLogger(__name__)


def _identity_headers(handler: BaseProxyHandler) -> dict[str, str]:
    headers = IdentityMapper(handler).get_headers()
    headers.pop("X-Request-Id", None)
    return headers


class MuxStreamCreateHandler(BaseProxyHandler):
    """Create a new mux stream."""

    async def post(self) -> None:
        if not await self.ensure_upstream_auth():
            return

        body = self.request.body or b"{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            await self.handle_error(400, "Invalid JSON payload", code="INVALID_JSON")
            return

        if payload and not isinstance(payload, dict):
            await self.handle_error(400, "Invalid JSON payload", code="INVALID_JSON")
            return

        manager = get_mux_manager(self.settings)
        headers = _identity_headers(self)
        identity = IdentityContext.from_headers(headers)
        stream = await manager.create_stream(identity, headers)
        stream.touch()

        self.write({
            "stream_id": stream.stream_id,
            "events_url": f"/ai/streams/{stream.stream_id}/events",
            "subscriptions_url": f"/ai/streams/{stream.stream_id}/subscriptions",
            "expires_in_ms": int(stream.ttl_seconds * 1000),
        })
        self.finish()


class MuxStreamEventsHandler(BaseProxyHandler):
    """Open mux SSE stream."""

    async def get(self, stream_id: str) -> None:
        if not await self.ensure_upstream_auth():
            return

        manager = get_mux_manager(self.settings)
        stream = await manager.get_stream(stream_id)
        if stream is None:
            await self.handle_error(404, "Stream not found", code="STREAM_NOT_FOUND")
            return

        headers = _identity_headers(self)
        if IdentityContext.from_headers(headers) != stream.identity:
            await self.handle_error(403, "Forbidden", code="STREAM_FORBIDDEN")
            return

        # Set SSE headers - critical for streaming
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache, no-transform")
        self.set_header("Connection", "keep-alive")
        self.set_header("X-Accel-Buffering", "no")

        stream.touch()
        await stream.run_writer(self)


class MuxStreamSubscriptionsHandler(BaseProxyHandler):
    """Manage mux subscriptions."""

    async def put(self, stream_id: str) -> None:
        if not await self.ensure_upstream_auth():
            return

        manager = get_mux_manager(self.settings)
        stream = await manager.get_stream(stream_id)
        if stream is None:
            await self.handle_error(404, "Stream not found", code="STREAM_NOT_FOUND")
            return

        headers = _identity_headers(self)
        if IdentityContext.from_headers(headers) != stream.identity:
            await self.handle_error(403, "Forbidden", code="STREAM_FORBIDDEN")
            return

        body = self.request.body or b"{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            await self.handle_error(400, "Invalid JSON payload", code="INVALID_JSON")
            return

        subscriptions_raw = payload.get("subscriptions") if isinstance(payload, dict) else None
        if subscriptions_raw is None:
            await self.handle_error(400, "subscriptions is required", code="INVALID_REQUEST")
            return
        if not isinstance(subscriptions_raw, list):
            await self.handle_error(400, "subscriptions must be a list", code="INVALID_REQUEST")
            return
        if len(subscriptions_raw) > stream.max_subscriptions:
            await self.handle_error(400, "Too many subscriptions", code="TOO_MANY_SUBSCRIPTIONS")
            return

        normalized: list[dict[str, Any]] = []
        for entry in subscriptions_raw:
            if not isinstance(entry, dict):
                await self.handle_error(400, "subscription must be an object", code="INVALID_REQUEST")
                return
            session_id = entry.get("session_id")
            if not isinstance(session_id, str) or not session_id:
                await self.handle_error(400, "session_id is required", code="INVALID_REQUEST")
                return
            after_seq = entry.get("after_seq", 0)
            if not isinstance(after_seq, (int, float)) or not float(after_seq).is_integer():
                await self.handle_error(400, "after_seq must be an integer", code="INVALID_REQUEST")
                return
            priority = entry.get("priority", "foreground")
            if priority not in ("foreground", "background"):
                await self.handle_error(400, "priority must be foreground or background", code="INVALID_REQUEST")
                return
            mode = entry.get("mode", "live")
            if mode not in ("live", "tools_only"):
                await self.handle_error(
                    400,
                    "mode must be live or tools_only",
                    code="MODE_UNSUPPORTED",
                )
                return
            notebook_uuid = entry.get("notebook_uuid")
            notebook_path = entry.get("notebook_path")
            if notebook_uuid is not None and (not isinstance(notebook_uuid, str) or not notebook_uuid):
                await self.handle_error(400, "notebook_uuid must be a string", code="INVALID_REQUEST")
                return
            if notebook_path is not None and (not isinstance(notebook_path, str) or not notebook_path):
                await self.handle_error(400, "notebook_path must be a string", code="INVALID_REQUEST")
                return
            if notebook_uuid and notebook_path:
                registry = get_notebook_registry(self.settings)
                registry.set_path(notebook_uuid, notebook_path)
            normalized.append({
                "session_id": session_id,
                "after_seq": int(after_seq),
                "priority": priority,
                "mode": mode,
                "notebook_uuid": notebook_uuid,
            })

        results = await stream.update_subscriptions(normalized)
        stream.touch()
        self.write({"applied": True, "results": results})
        self.finish()

    async def get(self, stream_id: str) -> None:
        if not await self.ensure_upstream_auth():
            return

        manager = get_mux_manager(self.settings)
        stream = await manager.get_stream(stream_id)
        if stream is None:
            await self.handle_error(404, "Stream not found", code="STREAM_NOT_FOUND")
            return

        headers = _identity_headers(self)
        if IdentityContext.from_headers(headers) != stream.identity:
            await self.handle_error(403, "Forbidden", code="STREAM_FORBIDDEN")
            return

        async with stream._subscriptions_lock:
            subscriptions = [
                {
                    "session_id": state.session_id,
                    "after_seq": state.after_seq,
                    "priority": state.priority,
                    "mode": state.mode,
                    "connected": state.connected,
                    "last_event_at": state.last_event_at,
                }
                for state in stream.subscriptions.values()
            ]
        self.write({"subscriptions": subscriptions})
        self.finish()


class MuxStreamDeleteHandler(BaseProxyHandler):
    """Delete mux stream."""

    async def delete(self, stream_id: str) -> None:
        if not await self.ensure_upstream_auth():
            return

        manager = get_mux_manager(self.settings)
        stream = await manager.get_stream(stream_id)
        if stream is None:
            await self.handle_error(404, "Stream not found", code="STREAM_NOT_FOUND")
            return

        headers = _identity_headers(self)
        if IdentityContext.from_headers(headers) != stream.identity:
            await self.handle_error(403, "Forbidden", code="STREAM_FORBIDDEN")
            return

        await manager.delete_stream(stream_id)
        self.write({"status": "deleted"})
        self.finish()
