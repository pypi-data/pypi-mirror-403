"""
JAX-XC: JAX implementations of exchange-correlation functionals.

This module exposes:
- ``get_xc_functional``: high-level EXC/VXC/FXC/KXC/LXC API.
- ``get_params``: access to LibXC parameter structs via the bundled helper.
- ``list_functionals``: LibXC registry introspection.
"""

from . import functionals

try:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("jxc-python")
    except PackageNotFoundError:  # pragma: no cover - local/uninstalled tree
        __version__ = "0.0.0"
except Exception:  # pragma: no cover - very old Python
    __version__ = "0.0.0"

# Import main functions from get_params if it exists
try:
    from .get_params import (
        XC_POLARIZED,
        XC_UNPOLARIZED,
        get_params,
        get_xc_functional,
        list_functionals,
    )

    __all__ = [
        "functionals",
        "get_params",
        "get_xc_functional",
        "list_functionals",
        "XC_UNPOLARIZED",
        "XC_POLARIZED",
        "__version__",
    ]
except ImportError:
    # If get_params doesn't exist, just export functionals and version
    __all__ = ["functionals", "__version__"]
