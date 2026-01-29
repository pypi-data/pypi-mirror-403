"""Base handler with common functionality."""

import logging
from typing import Any

from jupyter_server.base.handlers import APIHandler
import httpx

from ..auth.identity import IdentityMapper
from ..auth.token_store import TokenStore
from ..auth.browser_id import get_token_user_ids

logger = logging.getLogger(__name__)

# Global token store reference (shared with oauth handler)
_base_token_store: TokenStore | None = None


class BaseProxyHandler(APIHandler):
    """Base class for proxy handlers."""

    _http_client: httpx.AsyncClient | None = None

    @property
    def connector_settings(self) -> dict[str, Any]:
        """Get connector settings."""
        return self.settings.get("jupyter_ai_connector", {})

    @property
    def orchestrator_url(self) -> str:
        """Get orchestrator base URL."""
        return self.connector_settings.get("orchestrator_url", "http://localhost:8000")

    @property
    def orchestrator_token(self) -> str:
        """Get orchestrator service token."""
        return self.connector_settings.get("orchestrator_token", "")

    @property
    def auth0_configured(self) -> bool:
        """Check whether Auth0 settings are configured."""
        auth0_domain = self.connector_settings.get("auth0_domain", "")
        auth0_client_id = self.connector_settings.get("auth0_client_id", "")
        return bool(auth0_domain and auth0_client_id)

    @property
    def proxy_timeout(self) -> int:
        """Get proxy timeout."""
        return self.connector_settings.get("proxy_timeout", 30)

    @property
    def max_payload_size(self) -> int:
        """Get max payload size."""
        return self.connector_settings.get("max_payload_size", 25 * 1024 * 1024)

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.proxy_timeout),
            )
        return self._http_client

    def get_identity_headers(self) -> dict[str, str]:
        """Get identity headers to inject into upstream requests."""
        mapper = IdentityMapper(self)
        return mapper.get_headers()

    async def get_auth0_token(self) -> str | None:
        """Get stored Auth0 token for current user."""
        global _base_token_store

        # Check if Auth0 is configured
        if not self.auth0_configured:
            return None

        # Import here to avoid circular imports
        from .oauth import get_token_store

        _base_token_store = get_token_store(self.settings)

        for user_id in get_token_user_ids(self):
            token = await _base_token_store.get_valid_token(user_id)
            if token:
                return token
        return None

    async def ensure_upstream_auth(self) -> bool:
        """Ensure we have credentials to call the upstream service."""
        if self.orchestrator_token:
            return True

        if self.auth0_configured:
            if await self.get_auth0_token():
                return True
            self.set_status(401)
            self.write({
                "error": "Unauthorized",
                "message": "Sign in to Jupyter AI to access this endpoint.",
            })
            self.finish()
            return False

        self.set_status(501)
        self.write({
            "error": "Not Implemented",
            "message": "Orchestrator not configured. "
            "Configure orchestrator_url and orchestrator_token in Jupyter config "
            "to enable proxying.",
        })
        self.finish()
        return False

    async def get_upstream_headers(self) -> dict[str, str]:
        """Get all headers to send upstream."""
        headers = {
            "Content-Type": "application/json",
        }

        # Try Auth0 token first (user-specific), fall back to service token (shared)
        auth0_token = await self.get_auth0_token()
        if auth0_token:
            headers["Authorization"] = f"Bearer {auth0_token}"
            logger.debug("Using Auth0 token for upstream request")
        elif self.orchestrator_token:
            headers["Authorization"] = f"Bearer {self.orchestrator_token}"
            logger.debug("Using service token for upstream request")

        # Add identity headers
        headers.update(self.get_identity_headers())

        # Add request tracing
        request_id = self.request.headers.get("X-Request-Id")
        if request_id:
            headers["X-Request-Id"] = request_id

        return headers

    async def handle_error(self, status_code: int, message: str, code: str | None = None):
        """Send an error response."""
        self.set_status(status_code)
        self.write({
            "code": code or "PROXY_ERROR",
            "message": message,
        })
        self.finish()
