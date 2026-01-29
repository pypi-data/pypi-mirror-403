"""Identity mapping from Jupyter auth to SaaS headers.

Per the protocol spec, the Connector MUST inject:
- X-End-User-Subject
- X-Workspace-Id
- X-Jupyter-Server-Id
- X-Request-Id / trace IDs
"""

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jupyter_server.base.handlers import APIHandler

from .browser_id import get_or_set_browser_id


class IdentityMapper:
    """Maps Jupyter authentication to SaaS identity headers.

    The SaaS orchestrator MUST treat injected identity as authoritative
    only when requests originate from a valid Connector token.
    """

    def __init__(self, handler: "APIHandler"):
        self._handler = handler

    def get_headers(self) -> dict[str, str]:
        """Get identity headers to inject into upstream requests."""
        headers: dict[str, str] = {}

        # Stable browser identity for token lookup and correlation
        try:
            browser_id = get_or_set_browser_id(self._handler)
        except Exception:
            browser_id = None
        if browser_id:
            headers["X-JAI-Browser-Id"] = browser_id

        # Get user identity from Jupyter auth
        user = self._get_current_user()
        if user:
            headers["X-End-User-Subject"] = user.get("username", "anonymous")

        # Get workspace ID (could be derived from server config)
        workspace_id = self._get_workspace_id()
        if workspace_id:
            headers["X-Workspace-Id"] = workspace_id

        # Get Jupyter server instance ID
        server_id = self._get_server_id()
        if server_id:
            headers["X-Jupyter-Server-Id"] = server_id

        # Generate or forward request ID for tracing
        request_id = self._handler.request.headers.get("X-Request-Id")
        if not request_id:
            request_id = str(uuid.uuid4())
        headers["X-Request-Id"] = request_id

        return headers

    def _get_current_user(self) -> dict | None:
        """Get the current authenticated user."""
        try:
            # Use Jupyter Server's identity system
            user = self._handler.current_user
            if isinstance(user, dict):
                return user
            elif user:
                return {"username": str(user)}
        except Exception:
            pass
        return None

    def _get_workspace_id(self) -> str | None:
        """Get workspace ID from server configuration."""
        try:
            # Could be set in server settings or environment
            settings = self._handler.settings
            workspace_id = settings.get("workspace_id") or settings.get("WORKSPACE_ID")
            if not workspace_id:
                return "default"
            return str(workspace_id)
        except Exception:
            pass
        return None

    def _get_server_id(self) -> str | None:
        """Get Jupyter server instance ID."""
        try:
            settings = self._handler.settings
            # Server ID could be in settings or generated on startup
            return settings.get("jupyter_server_id")
        except Exception:
            pass
        return None
