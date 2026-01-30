"""Top-level namespace for derivative drivers.

This package exposes:

- ``ad_derivs``: JAX-AD based VXC/FXC/KXC/LXC drivers (runtime default).
- ``_maple_derivs``: Maple-generated VXC/FXC/KXC/LXC implementations.
- ``libxc_derivs``: LibXC-backed wrappers, used only in development tests.

The ``libxc_derivs`` module depends on the optional ``pylibxc`` package and
is imported lazily so that end users do not need ``pylibxc`` installed in
order to use the AD or Maple derivative paths.
"""

from . import ad_derivs, _maple_derivs

try:  # Optional; only needed for certain parity tests.
    from . import libxc_derivs  # type: ignore[import]
except Exception:  # pragma: no cover - pylibxc not installed
    libxc_derivs = None  # type: ignore[assignment]

__all__ = ["ad_derivs", "_maple_derivs", "libxc_derivs"]

