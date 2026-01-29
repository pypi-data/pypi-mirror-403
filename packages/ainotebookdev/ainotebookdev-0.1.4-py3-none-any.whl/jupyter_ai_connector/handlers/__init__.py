"""HTTP Handlers for Jupyter AI Connector."""

from .sessions import (
    ActiveTurnEventsHandler,
    SessionHandler,
    SessionHistoryHandler,
    SessionInfoHandler,
    ThreadHistoryHandler,
    ToolLeaseProxyHandler,
)
from .notebooks import (
    NotebookResolveHandler,
    NotebookThreadHandler,
    NotebookThreadsHandler,
    NotebookThreadEventsAppendHandler,
    NotebookPathHandler,
)
from .events import SSEProxyHandler
from .commands import CommandProxyHandler
from .config import ConfigProxyHandler
from .streams import (
    MuxStreamCreateHandler,
    MuxStreamEventsHandler,
    MuxStreamSubscriptionsHandler,
    MuxStreamDeleteHandler,
)
from .oauth import (
    OAuthCallbackHandler,
    OAuthLogoutCallbackHandler,
    OAuthConfigHandler,
    OAuthStateHandler,
    OAuthExchangeHandler,
    OAuthStatusHandler,
    OAuthLogoutUrlHandler,
    OAuthLogoutHandler,
)
from .dev_config import DevConfigHandler, DevConfigUiHandler


def setup_handlers(web_app, settings):
    """Set up the handlers for the connector."""
    host_pattern = ".*$"
    base_url = web_app.settings.get("base_url", "/")

    handlers = [
        # OAuth authentication
        (f"{base_url}ai/auth/callback", OAuthCallbackHandler),
        (f"{base_url}ai/auth/logout/callback", OAuthLogoutCallbackHandler),
        (f"{base_url}ai/auth/config", OAuthConfigHandler),
        (f"{base_url}ai/auth/state", OAuthStateHandler),
        (f"{base_url}ai/auth/exchange", OAuthExchangeHandler),
        (f"{base_url}ai/auth/status", OAuthStatusHandler),
        (f"{base_url}ai/auth/logout_url", OAuthLogoutUrlHandler),
        (f"{base_url}ai/auth/logout", OAuthLogoutHandler),
        # Session management
        (f"{base_url}ai/sessions", SessionHandler),
        # Notebook thread resolution + management
        (f"{base_url}ai/notebooks/([^/]+)/resolve", NotebookResolveHandler),
        (f"{base_url}ai/notebooks/([^/]+)/path", NotebookPathHandler),
        (f"{base_url}ai/notebooks/([^/]+)/threads", NotebookThreadsHandler),
        (f"{base_url}ai/notebooks/([^/]+)/threads/([^/]+)", NotebookThreadHandler),
        (f"{base_url}ai/notebooks/([^/]+)/threads/([^/]+)/events/append", NotebookThreadEventsAppendHandler),
        # SSE event stream
        (f"{base_url}ai/sessions/([^/]+)/events", SSEProxyHandler),
        # Active turn event fetch (JSON)
        (f"{base_url}ai/sessions/([^/]+)/turns/active/events", ActiveTurnEventsHandler),
        # Session history
        (f"{base_url}ai/sessions/([^/]+)/history", SessionHistoryHandler),
        # Thread history
        (f"{base_url}ai/threads/([^/]+)/history", ThreadHistoryHandler),
        # Tool lease management
        (f"{base_url}ai/sessions/([^/]+)/tool-lease/(acquire|renew|release)", ToolLeaseProxyHandler),
        # Command ingress
        (f"{base_url}ai/sessions/([^/]+)/commands", CommandProxyHandler),
        # Session info
        (f"{base_url}ai/sessions/([^/]+)", SessionInfoHandler),
        # Config proxy
        (f"{base_url}ai/config/(.*)", ConfigProxyHandler),
    ]

    if settings.get("jupyter_ai_connector", {}).get("enable_sse_mux"):
        handlers.extend([
            (f"{base_url}ai/streams", MuxStreamCreateHandler),
            (f"{base_url}ai/streams/([^/]+)/events", MuxStreamEventsHandler),
            (f"{base_url}ai/streams/([^/]+)/subscriptions", MuxStreamSubscriptionsHandler),
            (f"{base_url}ai/streams/([^/]+)", MuxStreamDeleteHandler),
        ])

    if settings.get("jupyter_ai_connector_dev", {}).get("enabled"):
        handlers.extend([
            (f"{base_url}ai/dev/config", DevConfigHandler),
            (f"{base_url}ai/dev", DevConfigUiHandler),
        ])

    web_app.add_handlers(host_pattern, handlers)
