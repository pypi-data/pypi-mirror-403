"""
Lightweight LibXC bindings vendored into JXC.

We keep this package minimal to avoid circular imports:

- ``core``: ctypes-loaded LibXC shared library (bundled with the wheel)

Callers should import ``LibXCFunctional`` and ``util`` directly from
``jxc._libxc.functional`` and ``jxc._libxc.util``.
"""

from .core import core, get_core_path  # noqa: F401

__all__ = ["core", "get_core_path"]
