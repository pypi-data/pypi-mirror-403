"""Session management handler."""

import json
import logging

from .base import BaseProxyHandler

logger = logging.getLogger(__name__)


class SessionHandler(BaseProxyHandler):
    """Handle session creation and management.

    POST /ai/sessions - Create a new session
    Returns 501 Not Implemented when SaaS orchestrator is not configured.
    """

    async def post(self):
        """Create a new session.

        POST /ai/sessions

        Returns:
            - 201: Session created successfully (when SaaS configured)
            - 501: Not Implemented (when SaaS not configured)
            - 413: Payload too large
            - 500: Internal server error
        """
        if not await self.ensure_upstream_auth():
            return

        try:
            # Read request body
            body = self.request.body
            if len(body) > self.max_payload_size:
                await self.handle_error(413, "Payload too large", code="PAYLOAD_TOO_LARGE")
                return

            # Forward to orchestrator
            response = await self.http_client.post(
                f"{self.orchestrator_url}/v1/sessions",
                content=body,
                headers=await self.get_upstream_headers(),
            )

            # Forward response
            self.set_status(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ("content-encoding", "transfer-encoding", "content-length"):
                    self.set_header(key, value)

            self.write(response.content)
            self.finish()

        except Exception as e:
            logger.exception("Failed to create session")
            await self.handle_error(500, str(e), code="PROXY_ERROR")


class SessionInfoHandler(BaseProxyHandler):
    """Proxy session metadata from orchestrator."""

    async def get(self, session_id: str):
        if not await self.ensure_upstream_auth():
            return

        try:
            response = await self.http_client.get(
                f"{self.orchestrator_url}/v1/sessions/{session_id}",
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ("content-encoding", "transfer-encoding", "content-length"):
                    self.set_header(key, value)

            self.write(response.content)
            self.finish()
        except Exception as e:
            logger.exception("Failed to load session info")
            await self.handle_error(500, str(e), code="PROXY_ERROR")


class SessionHistoryHandler(BaseProxyHandler):
    """Proxy session history from orchestrator."""

    async def get(self, session_id: str):
        if not await self.ensure_upstream_auth():
            return

        try:
            query = self.request.query
            url = f"{self.orchestrator_url}/v1/sessions/{session_id}/history"
            if query:
                url = f"{url}?{query}"
            response = await self.http_client.get(
                url,
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ("content-encoding", "transfer-encoding", "content-length"):
                    self.set_header(key, value)

            self.write(response.content)
            self.finish()
        except Exception as e:
            logger.exception("Failed to load session history")
            await self.handle_error(500, str(e), code="PROXY_ERROR")


class ThreadHistoryHandler(BaseProxyHandler):
    """Proxy thread history from orchestrator."""

    async def get(self, thread_id: str):
        if not await self.ensure_upstream_auth():
            return

        try:
            query = self.request.query
            url = f"{self.orchestrator_url}/v1/threads/{thread_id}/history"
            if query:
                url = f"{url}?{query}"
            response = await self.http_client.get(
                url,
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ("content-encoding", "transfer-encoding", "content-length"):
                    self.set_header(key, value)

            self.write(response.content)
            self.finish()
        except Exception as e:
            logger.exception("Failed to load thread history")
            await self.handle_error(500, str(e), code="PROXY_ERROR")


class ActiveTurnEventsHandler(BaseProxyHandler):
    """Proxy active turn events from orchestrator."""

    async def get(self, session_id: str):
        if not await self.ensure_upstream_auth():
            return

        try:
            query = self.request.query
            url = f"{self.orchestrator_url}/v1/sessions/{session_id}/turns/active/events"
            if query:
                url = f"{url}?{query}"
            response = await self.http_client.get(
                url,
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in ("content-encoding", "transfer-encoding", "content-length"):
                    self.set_header(key, value)

            self.write(response.content)
            self.finish()
        except Exception as e:
            logger.exception("Failed to load active turn events")
            await self.handle_error(500, str(e), code="PROXY_ERROR")


class ToolLeaseProxyHandler(BaseProxyHandler):
    """Proxy tool lease requests to the orchestrator."""

    async def post(self, session_id: str, action: str):
        if not await self.ensure_upstream_auth():
            return

        try:
            body = self.request.body
            if len(body) > self.max_payload_size:
                await self.handle_error(413, "Payload too large", code="PAYLOAD_TOO_LARGE")
                return

            response = await self.http_client.post(
                f"{self.orchestrator_url}/v1/sessions/{session_id}/tool-lease/{action}",
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
            logger.exception("Failed to proxy tool lease")
            await self.handle_error(500, str(e), code="PROXY_ERROR")
