"""Jupyter AI Extension - JupyterLab client for AI-powered notebooks."""

from ._version import __version__


def _jupyter_labextension_paths():
    """Return the JupyterLab extension paths."""
    return [{"src": "labextension", "dest": "@jupyter-ai/jupyterlab-extension"}]
