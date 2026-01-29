"""Notebook thread management handlers."""

import asyncio
import json
import logging
import os
import threading
import time
from typing import Any

from jupyter_server.base.handlers import APIHandler

from .base import BaseProxyHandler

logger = logging.getLogger(__name__)

_APPEND_LOCKS: dict[str, asyncio.Lock] = {}
_APPEND_READ_BYTES = 16384


def _normalize_notebook_path(path: str) -> str:
    if not path:
        return ""
    return path[1:] if path.startswith("/") else path


def _sidecar_events_path(
    notebook_path: str,
    notebook_uuid: str,
    thread_id: str,
    session_id: str,
) -> str:
    normalized = _normalize_notebook_path(notebook_path)
    notebook_dir = os.path.dirname(normalized)
    root_dir = os.path.join(notebook_dir, ".jupyter_ai", "notebooks", notebook_uuid)
    return os.path.join(root_dir, "threads", thread_id, "sessions", session_id, "events.ndjson")


class NotebookPathRegistry:
    def __init__(self) -> None:
        self._paths: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def set_path(self, notebook_uuid: str, notebook_path: str) -> str | None:
        if not notebook_uuid or not notebook_path:
            return None
        normalized = _normalize_notebook_path(notebook_path)
        if not normalized:
            return None
        with self._lock:
            self._paths[notebook_uuid] = (normalized, time.time())
        return normalized

    def get_path(self, notebook_uuid: str) -> str | None:
        if not notebook_uuid:
            return None
        with self._lock:
            entry = self._paths.get(notebook_uuid)
        return entry[0] if entry else None


def get_notebook_registry(settings: dict[str, Any]) -> NotebookPathRegistry:
    registry = settings.get("jupyter_ai_connector_notebook_registry")
    if registry is None:
        registry = NotebookPathRegistry()
        settings["jupyter_ai_connector_notebook_registry"] = registry
    return registry


def _get_lock(path: str) -> asyncio.Lock:
    lock = _APPEND_LOCKS.get(path)
    if lock is None:
        lock = asyncio.Lock()
        _APPEND_LOCKS[path] = lock
    return lock


def _read_last_seq(events_path: str) -> int:
    if not os.path.exists(events_path):
        return 0
    try:
        with open(events_path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            if size == 0:
                return 0
            offset = min(size, _APPEND_READ_BYTES)
            handle.seek(-offset, os.SEEK_END)
            data = handle.read(offset)
        lines = data.splitlines()
        for raw in reversed(lines):
            if not raw.strip():
                continue
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except Exception:
                return 0
            seq = parsed.get("seq") if isinstance(parsed, dict) else None
            if isinstance(seq, int):
                return seq
            if isinstance(seq, float) and seq.is_integer():
                return int(seq)
            return 0
        return 0
    except Exception:
        logger.exception("Failed to read last seq from events file")
        return 0


class NotebookPathHandler(APIHandler):
    """Register notebook path for a UUID."""

    async def put(self, notebook_uuid: str) -> None:
        try:
            body = self.request.body
            max_payload_size = self.settings.get("jupyter_ai_connector", {}).get(
                "max_payload_size",
                12 * 1024 * 1024,
            )
            if body and len(body) > max_payload_size:
                self.set_status(413)
                self.write({"code": "PAYLOAD_TOO_LARGE", "message": "Payload too large"})
                self.finish()
                return

            try:
                payload = json.loads(body or b"{}")
            except json.JSONDecodeError:
                self.set_status(400)
                self.write({"code": "INVALID_JSON", "message": "Invalid JSON payload"})
                self.finish()
                return

            notebook_path = payload.get("notebook_path")
            if not isinstance(notebook_path, str) or not notebook_path:
                self.set_status(400)
                self.write({"code": "INVALID_REQUEST", "message": "notebook_path is required"})
                self.finish()
                return

            registry = get_notebook_registry(self.settings)
            normalized = registry.set_path(notebook_uuid, notebook_path)
            if not normalized:
                self.set_status(400)
                self.write({"code": "INVALID_REQUEST", "message": "notebook_path is invalid"})
                self.finish()
                return

            self.write({
                "status": "ok",
                "notebook_uuid": notebook_uuid,
                "notebook_path": normalized,
            })
            self.finish()
        except Exception as exc:
            logger.exception("Failed to register notebook path")
            self.set_status(500)
            self.write({"code": "REGISTER_FAILED", "message": str(exc)})
            self.finish()


class NotebookThreadEventsAppendHandler(APIHandler):
    """Append sidecar events to the server-side event log."""

    async def post(self, notebook_uuid: str, thread_id: str):
        try:
            body = self.request.body
            max_payload_size = self.settings.get("jupyter_ai_connector", {}).get(
                "max_payload_size",
                12 * 1024 * 1024,
            )
            if body and len(body) > max_payload_size:
                self.set_status(413)
                self.write({"code": "PAYLOAD_TOO_LARGE", "message": "Payload too large"})
                self.finish()
                return

            try:
                payload = json.loads(body or b"{}")
            except json.JSONDecodeError:
                self.set_status(400)
                self.write({"code": "INVALID_JSON", "message": "Invalid JSON payload"})
                self.finish()
                return

            events = payload.get("events")
            if not isinstance(events, list) or not events:
                self.set_status(400)
                self.write({"code": "INVALID_REQUEST", "message": "events must be a non-empty list"})
                self.finish()
                return

            normalized: list[dict[str, Any]] = []
            for item in events:
                if not isinstance(item, dict):
                    self.set_status(400)
                    self.write({"code": "INVALID_REQUEST", "message": "event must be an object"})
                    self.finish()
                    return
                seq = item.get("seq")
                event_type = item.get("type")
                event_session = item.get("session_id")
                event_thread = item.get("thread_id")
                if not isinstance(seq, (int, float)) or not float(seq).is_integer():
                    self.set_status(400)
                    self.write({"code": "INVALID_REQUEST", "message": "event.seq must be an integer"})
                    self.finish()
                    return
                if not isinstance(event_type, str) or not event_type:
                    self.set_status(400)
                    self.write({"code": "INVALID_REQUEST", "message": "event.type must be a string"})
                    self.finish()
                    return
                if not isinstance(event_session, str) or not event_session:
                    self.set_status(400)
                    self.write({"code": "INVALID_REQUEST", "message": "event.session_id must be a string"})
                    self.finish()
                    return
                if event_thread is None:
                    event_thread = thread_id
                elif not isinstance(event_thread, str) or not event_thread:
                    self.set_status(400)
                    self.write({"code": "INVALID_REQUEST", "message": "event.thread_id must be a string"})
                    self.finish()
                    return
                if event_thread != thread_id:
                    self.set_status(400)
                    self.write({"code": "INVALID_REQUEST", "message": "event.thread_id mismatch"})
                    self.finish()
                    return
                data = item.get("data")
                normalized.append({
                    "seq": int(seq),
                    "type": event_type,
                    "session_id": event_session,
                    "thread_id": event_thread,
                    "turn_id": item.get("turn_id"),
                    "ts": item.get("ts"),
                    "data": data if isinstance(data, dict) else {},
                })

            normalized.sort(key=lambda event: event["seq"])
            session_id = normalized[0]["session_id"]
            for event in normalized[1:]:
                if event["session_id"] != session_id:
                    self.set_status(400)
                    self.write({
                        "code": "INVALID_REQUEST",
                        "message": "events must share the same session_id",
                    })
                    self.finish()
                    return
            contents_manager = self.contents_manager
            get_os_path = getattr(contents_manager, "_get_os_path", None) or getattr(contents_manager, "get_os_path", None)
            if get_os_path is None:
                self.set_status(501)
                self.write({
                    "code": "APPEND_UNSUPPORTED",
                    "message": "Contents manager does not support filesystem appends",
                })
                self.finish()
                return

            registry = get_notebook_registry(self.settings)
            notebook_path = payload.get("notebook_path")
            if notebook_path is not None:
                if not isinstance(notebook_path, str) or not notebook_path:
                    self.set_status(400)
                    self.write({"code": "INVALID_REQUEST", "message": "notebook_path must be a string"})
                    self.finish()
                    return
                resolved_path = registry.set_path(notebook_uuid, notebook_path)
            else:
                resolved_path = registry.get_path(notebook_uuid)

            if not resolved_path:
                self.set_status(400)
                self.write({
                    "code": "NOTEBOOK_PATH_NOT_REGISTERED",
                    "message": "Notebook path not registered for UUID",
                })
                self.finish()
                return

            events_rel_path = _sidecar_events_path(resolved_path, notebook_uuid, thread_id, session_id)
            events_path = get_os_path(events_rel_path)
            os.makedirs(os.path.dirname(events_path), exist_ok=True)
            lock = _get_lock(events_path)
            async with lock:
                last_seq = _read_last_seq(events_path)
                pending = [event for event in normalized if event["seq"] > last_seq]
                if pending:
                    with open(events_path, "a", encoding="utf-8") as handle:
                        for event in pending:
                            handle.write(json.dumps(event))
                            handle.write("\n")
                    last_seq = pending[-1]["seq"]

            self.write({
                "status": "ok",
                "appended": len(pending),
                "last_seq_cached": last_seq,
            })
            self.finish()
        except Exception as exc:
            logger.exception("Failed to append sidecar events")
            self.set_status(500)
            self.write({"code": "APPEND_FAILED", "message": str(exc)})
            self.finish()


class NotebookResolveHandler(BaseProxyHandler):
    """Proxy notebook thread resolution."""

    async def post(self, notebook_uuid: str):
        if not await self.ensure_upstream_auth():
            return

        try:
            body = self.request.body
            if len(body) > self.max_payload_size:
                await self.handle_error(413, "Payload too large", code="PAYLOAD_TOO_LARGE")
                return

            response = await self.http_client.post(
                f"{self.orchestrator_url}/v1/notebooks/{notebook_uuid}/resolve",
                content=body,
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ("content-encoding", "transfer-encoding", "content-length"):
                    self.set_header(key, value)

            self.write(response.content)
            self.finish()
        except Exception as e:
            logger.exception("Failed to resolve notebook thread")
            await self.handle_error(500, str(e), code="PROXY_ERROR")


class NotebookThreadsHandler(BaseProxyHandler):
    """Proxy notebook threads list and creation."""

    async def get(self, notebook_uuid: str):
        if not await self.ensure_upstream_auth():
            return

        try:
            response = await self.http_client.get(
                f"{self.orchestrator_url}/v1/notebooks/{notebook_uuid}/threads",
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ("content-encoding", "transfer-encoding", "content-length"):
                    self.set_header(key, value)

            self.write(response.content)
            self.finish()
        except Exception as e:
            logger.exception("Failed to list notebook threads")
            await self.handle_error(500, str(e), code="PROXY_ERROR")

    async def post(self, notebook_uuid: str):
        if not await self.ensure_upstream_auth():
            return

        try:
            body = self.request.body
            if len(body) > self.max_payload_size:
                await self.handle_error(413, "Payload too large", code="PAYLOAD_TOO_LARGE")
                return

            response = await self.http_client.post(
                f"{self.orchestrator_url}/v1/notebooks/{notebook_uuid}/threads",
                content=body,
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ("content-encoding", "transfer-encoding", "content-length"):
                    self.set_header(key, value)

            self.write(response.content)
            self.finish()
        except Exception as e:
            logger.exception("Failed to create notebook thread")
            await self.handle_error(500, str(e), code="PROXY_ERROR")


class NotebookThreadHandler(BaseProxyHandler):
    """Proxy notebook thread updates."""

    async def patch(self, notebook_uuid: str, thread_id: str):
        if not await self.ensure_upstream_auth():
            return

        try:
            body = self.request.body
            if len(body) > self.max_payload_size:
                await self.handle_error(413, "Payload too large", code="PAYLOAD_TOO_LARGE")
                return

            response = await self.http_client.patch(
                f"{self.orchestrator_url}/v1/notebooks/{notebook_uuid}/threads/{thread_id}",
                content=body,
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ("content-encoding", "transfer-encoding", "content-length"):
                    self.set_header(key, value)

            self.write(response.content)
            self.finish()
        except Exception as e:
            logger.exception("Failed to update notebook thread")
            await self.handle_error(500, str(e), code="PROXY_ERROR")
