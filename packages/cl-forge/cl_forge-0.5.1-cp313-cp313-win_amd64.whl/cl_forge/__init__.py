"""Simple yet powerful Chilean and other tools written in Rust and Python."""

import importlib.metadata

from cl_forge import cmf, exceptions, utils, verify

__all__ = ("cmf", "exceptions", "utils", "verify",)

try:
    __version__ = importlib.metadata.version("cl-forge")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"