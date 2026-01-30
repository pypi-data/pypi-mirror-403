"""Jupyter AI client bundle."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ainotebookdev")
except PackageNotFoundError:
    __version__ = "0.0.0"
