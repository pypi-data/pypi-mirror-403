from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyinstaller-plus")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__"]
