"""
Python module for **nmk-vscode** plugin code.
"""

from importlib.metadata import version

__title__ = "nmk-vscode"
try:
    __version__ = version(__title__)
except Exception:  # pragma: no cover
    __version__ = "unknown"
