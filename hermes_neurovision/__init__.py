"""Hermes Vision — Terminal neurovisualizer for Hermes Agent."""

from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("hermes-neurovision")
except PackageNotFoundError:
    __version__ = "unknown"
