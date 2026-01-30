"""
Jupyter AI Connector

Jupyter Server extension that provides a same-origin proxy for the
Jupyter AI SaaS Orchestrator.

Responsibilities:
- Authentication mapping (Jupyter auth → SaaS identity headers)
- /ai/* endpoint proxying
- SSE proxy with streaming correctness
- Secret hiding (SaaS tokens never exposed to browser)
"""

from ._version import __version__
from .app import JupyterAIConnectorExtension


def _jupyter_server_extension_points():
    """Return Jupyter Server extension points."""
    return [{"module": "jupyter_ai_connector", "app": JupyterAIConnectorExtension}]


__all__ = ["__version__", "JupyterAIConnectorExtension"]
