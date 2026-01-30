"""Setup script for jxc-python package.

This file wires up a compiled helper extension (jxc.helper) that is built
per-Python ABI at wheel/install time using pybind11. The helper is used to
extract LibXC parameters; LibXC itself is shipped as a shared library under
``jxc/_libxc/libxc.so``.
"""

from pathlib import Path

from setuptools import Extension, setup
from setuptools.dist import Distribution

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
except ImportError:  # pragma: no cover - wheel not installed
    _bdist_wheel = None

try:
    import pybind11  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - pybind11 missing at import time
    pybind11 = None

# Work around setuptools 80+ insisting that all manifest/package paths are
# relative by default. Our build only ever runs in isolated environments for
# this package, so it's safe to relax this check.
try:  # pragma: no cover - defensive monkeypatch
    import setuptools.command.build_py as _build_py_mod

    def _assert_relative(path: str) -> str:  # type: ignore[override]
        return path

    if hasattr(_build_py_mod, "assert_relative"):
        _build_py_mod.assert_relative = _assert_relative
except Exception:
    pass

class BinaryDistribution(Distribution):
    """Mark the distribution as containing platform-specific binaries."""

    def has_ext_modules(self):  # pragma: no cover - simple override
        return True


class CustomBDistWheel(_bdist_wheel):
    """Ensure wheels are tagged as platform-specific."""

    def finalize_options(self):  # pragma: no cover - simple override
        super().finalize_options()
        self.root_is_pure = False


def _build_ext_modules():
    """Construct the helper extension in a way that works from sdist."""
    # All paths here must be relative to this setup.py, per setuptools rules.
    helper_src = "libxc/src/helper.cc"

    include_dirs = [
        "libxc",
        "libxc/src",
        "third_party/visit_struct/include",
    ]
    extra_compile_args = ["-std=c++14"]

    if pybind11 is not None:
        try:
            include_dirs.append(pybind11.get_include())
        except Exception:
            # If get_include fails, proceed without the extra include path; the
            # headers may be available via a system installation.
            pass

    return [
        Extension(
            "jxc.helper",
            [helper_src],
            include_dirs=include_dirs,
            language="c++",
            extra_compile_args=extra_compile_args,
        )
    ]


cmdclass = {}

if _bdist_wheel is not None:
    cmdclass["bdist_wheel"] = CustomBDistWheel


if __name__ == "__main__":
    setup(
        cmdclass=cmdclass,
        distclass=BinaryDistribution,
        ext_modules=_build_ext_modules(),
    )
