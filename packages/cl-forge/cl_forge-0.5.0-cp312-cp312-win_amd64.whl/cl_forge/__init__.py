"""Simple yet powerful Chilean and other tools written in Rust and Python."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("cl-forge")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"