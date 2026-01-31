"""pycatalyst — a modern Python package template."""

from __future__ import annotations

try:
    from importlib.metadata import version

    __version__ = version("pycatalyst")
except Exception:
    __version__ = "0.1.0"

__all__ = ["__version__"]
