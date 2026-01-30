"""SSE proxy handler for event streaming.

# IMPORTANT: SSE proxy buffering is the #1 early pitfall
# TODO: Validate with integration tests that responses are not buffered
# Checklist:
# - [ ] Verify nginx/proxy has proxy_buffering off
# - [ ] Verify Content-Type is text/event-stream
# - [ ] Verify Transfer-Encoding chunked or no Content-Length
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator

import httpx
from httpx_sse import aconnect_sse, ServerSentEvent

from .base import BaseProxyHandler

logger = logging.getLogger(__name__)


class SSEProxyHandler(BaseProxyHandler):
    """Proxy SSE events from the orchestrator.

    CRITICAL: This handler must:
    - Disable buffering (flush chunks immediately)
    - Forward SSE id and event fields unchanged
    - Handle heartbeats for keep-alive
    - Support reconnection with Last-Event-ID

    # IMPORTANT: SSE proxy buffering is the #1 early pitfall
    # TODO: Validate with integration tests that responses are not buffered
    # Checklist:
    # - [ ] Verify nginx/proxy has proxy_buffering off
    # - [ ] Verify Content-Type is text/event-stream
    # - [ ] Verify Transfer-Encoding chunked or no Content-Length
    """

    @property
    def heartbeat_interval(self) -> float:
        """Get heartbeat interval from settings."""
        return self.connector_settings.get("heartbeat_interval", 15.0)

    async def get(self, session_id: str):
        """Stream SSE events.

        GET /ai/sessions/{session_id}/events

        When SaaS orchestrator is not configured, streams dummy heartbeat events
        to demonstrate the SSE connection is working.

        # IMPORTANT: SSE proxy buffering is the #1 early pitfall
        # TODO: Validate with integration tests that responses are not buffered
        # Checklist:
        # - [ ] Verify nginx/proxy has proxy_buffering off
        # - [ ] Verify Content-Type is text/event-stream
        # - [ ] Verify Transfer-Encoding chunked or no Content-Length
        """
        # Set SSE headers - these are critical for streaming
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        self.set_header("X-Accel-Buffering", "no")  # Disable nginx buffering

        # No SaaS configured - stream dummy heartbeat events
        if not self.orchestrator_token and not self.auth0_configured:
            await self._stream_dummy_heartbeat(session_id)
            return

        if not await self.ensure_upstream_auth():
            return

        # Get replay cursor
        last_event_id = self.request.headers.get("Last-Event-ID")
        after_seq = self.get_argument("after_seq", None)

        # Build upstream URL
        url = f"{self.orchestrator_url}/v1/sessions/{session_id}/events"
        if after_seq:
            url += f"?after_seq={after_seq}"

        # Build headers
        headers = await self.get_upstream_headers()
        headers["Accept"] = "text/event-stream"
        if last_event_id:
            headers["Last-Event-ID"] = last_event_id

        try:
            # Stream from orchestrator using raw byte streaming
            # httpx_sse can have issues with some SSE implementations
            # Use explicit timeout config to keep SSE connection open indefinitely
            timeout = httpx.Timeout(
                connect=30.0,  # 30s to establish connection
                read=None,     # No read timeout - SSE can have long gaps
                write=None,    # No write timeout
                pool=None,     # No pool timeout
            )
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    if response.status_code >= 400:
                        await self._proxy_error_response(response)
                        return
                    logger.debug(f"SSE proxy connected to upstream for session {session_id}")
                    async for line in response.aiter_lines():
                        # Forward each line directly
                        self.write(line + "\n")
                        await self.flush()
                    logger.debug(f"SSE upstream stream ended for session {session_id}")

        except Exception as e:
            # StreamClosedError is expected when client disconnects - don't log as error
            if "Stream is closed" in str(e):
                logger.debug("SSE stream closed by client")
            else:
                logger.exception("SSE stream error")
                await self._safe_send_error(str(e))
        finally:
            await self._safe_finish()

    async def _stream_dummy_heartbeat(self, session_id: str):
        """Stream dummy heartbeat events when SaaS is not configured.

        This is useful for testing the SSE connection without a real orchestrator.

        # IMPORTANT: SSE proxy buffering is the #1 early pitfall
        # TODO: Validate with integration tests that responses are not buffered
        """
        try:
            seq = 0
            while True:
                # Send heartbeat event
                heartbeat_data = json.dumps({
                    "type": "heartbeat",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "message": "Orchestrator not configured - streaming dummy heartbeat",
                })

                self.write(f"id: {seq}\n")
                self.write("event: heartbeat\n")
                self.write(f"data: {heartbeat_data}\n")
                self.write("\n")

                # Flush immediately - critical for streaming
                await self.flush()

                seq += 1
                await asyncio.sleep(self.heartbeat_interval)

        except asyncio.CancelledError:
            logger.debug("Heartbeat stream cancelled")
        except Exception as e:
            logger.exception("Heartbeat stream error")
        finally:
            self.finish()

    async def _forward_event(self, event: ServerSentEvent):
        """Forward an SSE event to the client.

        MUST preserve:
        - id field (for reconnection)
        - event field (for type dispatch)
        - data field (the payload)

        # IMPORTANT: SSE proxy buffering is the #1 early pitfall
        # Flush immediately after writing to avoid buffering issues.
        """
        # Write SSE frame
        if event.id:
            self.write(f"id: {event.id}\n")
        if event.event:
            self.write(f"event: {event.event}\n")
        if event.data:
            self.write(f"data: {event.data}\n")
        self.write("\n")

        # Flush immediately - critical for streaming
        await self.flush()

    async def _send_error_event(self, message: str):
        """Send an error event to the client."""
        error_data = json.dumps({
            "type": "error",
            "data": {"code": "PROXY_ERROR", "message": message},
        })
        self.write("event: error\n")
        self.write(f"data: {error_data}\n")
        self.write("\n")
        await self.flush()

    async def _safe_send_error(self, message: str):
        """Send error event, ignoring if stream is closed."""
        try:
            await self._send_error_event(message)
        except Exception:
            pass

    async def _proxy_error_response(self, response: httpx.Response) -> None:
        """Proxy an upstream error response without wrapping it in SSE."""
        self.set_status(response.status_code)
        content_type = response.headers.get("Content-Type") or "application/json"
        self.set_header("Content-Type", content_type)
        body = await response.aread()
        if body:
            self.write(body)
            await self._safe_finish()
            return
        await self.handle_error(response.status_code, "Upstream error", code="PROXY_ERROR")

    async def _safe_finish(self):
        """Finish response, ignoring if stream is closed."""
        try:
            self.finish()
        except Exception:
            pass

    def on_connection_close(self):
        """Handle client disconnect."""
        logger.debug("SSE client disconnected")
