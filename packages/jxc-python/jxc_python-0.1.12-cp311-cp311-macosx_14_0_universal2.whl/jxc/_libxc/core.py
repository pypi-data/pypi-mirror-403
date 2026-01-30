"""
Minimal LibXC loader used by JXC.

This module is intentionally self-contained and only looks for the
LibXC shared library next to this file (bundled into the jxc wheel).
"""

import ctypes
from pathlib import Path

import numpy as np

core = None
__libxc_path: str | None = None

_HERE = Path(__file__).resolve().parent

for _name in ("libxc.so", "libxc.dylib"):
    candidate = _HERE / _name
    if candidate.is_file():
        __libxc_path = str(candidate)
        core = np.ctypeslib.load_library("libxc", str(_HERE))
        break

if core is None or __libxc_path is None:
    raise ImportError(
        "Bundled LibXC shared library not found in jxc._libxc. "
        "This build of jxc is incomplete; expected libxc.so next to core.py."
    )


def get_core_path() -> str:
    """Return the absolute path of the loaded LibXC shared object."""
    return __libxc_path
