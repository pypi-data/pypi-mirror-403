#!/bin/bash
set -euo pipefail

# Build a local pylibxc wheel backed by the LibXC core compiled under .libxc-core.
# This is only used for development (tests/benchmarks), not at runtime for the
# jxc-python PyPI package.

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
STAGE_DIR="$PROJECT_ROOT/build/pylibxc-stage"
PY_SETUP_DIR="$PROJECT_ROOT/python/pylibxc_setup"

mkdir -p "$STAGE_DIR"

if [ ! -d "$PROJECT_ROOT/.libxc-core" ]; then
  echo "LibXC core not found; running build_libxc_core.sh..."
  bash "$PROJECT_ROOT/scripts/build_libxc_core.sh"
fi

echo "Building pylibxc helper extension into stage dir..."
PY_BIN="${PYTHON_BIN_PATH:-python}"
(
  cd "$PROJECT_ROOT"
  "$PY_BIN" -m pip install --quiet pybind11 build
  bash "scripts/build_pylibxc_extension.sh" "$STAGE_DIR/pylibxc"
)

echo "Building pylibxc wheel from python/pylibxc_setup..."
(
  cd "$PY_SETUP_DIR"
  # Copy pylibxc source from libxc submodule
  rm -rf pylibxc
  cp -r "$PROJECT_ROOT/libxc/pylibxc" .
  # Copy the built helper extension
  cp "$STAGE_DIR"/pylibxc/helper*.so pylibxc/ 2>/dev/null || \
    cp "$STAGE_DIR"/pylibxc/helper*.dylib pylibxc/ 2>/dev/null || true
  # Copy libxc shared library
  cp "$PROJECT_ROOT"/.libxc-core/lib/libxc.so* pylibxc/ 2>/dev/null || \
    cp "$PROJECT_ROOT"/.libxc-core/lib/libxc*.dylib pylibxc/ 2>/dev/null || true
  "$PY_BIN" -m build --wheel --outdir "$PROJECT_ROOT/dist"
)

echo "✓ Built pylibxc wheel(s):"
ls "$PROJECT_ROOT"/dist/pylibxc-*.whl
