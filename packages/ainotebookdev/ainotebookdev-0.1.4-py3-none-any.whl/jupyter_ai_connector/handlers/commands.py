"""Command proxy handler."""

import logging

from .base import BaseProxyHandler

logger = logging.getLogger(__name__)


class CommandProxyHandler(BaseProxyHandler):
    """Proxy commands to the orchestrator.

    POST /ai/sessions/{session_id}/commands - Send command to session
    Returns 501 Not Implemented when SaaS orchestrator is not configured.
    """

    async def post(self, session_id: str):
        """Forward a command to the orchestrator.

        POST /ai/sessions/{session_id}/commands

        Accepts JSON command payload and forwards to SaaS orchestrator.

        Returns:
            - 200/202: Command accepted (when SaaS configured)
            - 501: Not Implemented (when SaaS not configured)
            - 413: Payload too large
            - 500: Internal server error
        """
        if not await self.ensure_upstream_auth():
            return

        try:
            # Read and validate payload size
            body = self.request.body
            if len(body) > self.max_payload_size:
                await self.handle_error(413, "Payload too large", code="PAYLOAD_TOO_LARGE")
                return

            # Forward to orchestrator
            response = await self.http_client.post(
                f"{self.orchestrator_url}/v1/sessions/{session_id}/commands",
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
            logger.exception("Failed to proxy command")
            await self.handle_error(500, str(e), code="PROXY_ERROR")
