#!/bin/bash
# Build the pybind11 helper module against the prebuilt LibXC core.

set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
LIBXC_DIR="$PROJECT_ROOT/libxc"
VISIT_STRUCT_DIR="$PROJECT_ROOT/third_party/visit_struct"
INSTALL_PREFIX="$PROJECT_ROOT/.libxc-core"

if [ ! -d "$INSTALL_PREFIX" ]; then
  echo "Error: LibXC core not found at $INSTALL_PREFIX. Run scripts/build_libxc_core.sh first." >&2
  exit 1
fi

OUTPUT_DIR=${1:-$PROJECT_ROOT/build/pylibxc-stage/pylibxc}
mkdir -p "$OUTPUT_DIR"

EXT_SUFFIX=$(python -c "from sysconfig import get_config_var; print(get_config_var('EXT_SUFFIX'))")
TARGET="$OUTPUT_DIR/helper$EXT_SUFFIX"

PYBIND11_INCLUDES=$(python -m pybind11 --includes)

LIB_DIR_CANDIDATES=("$INSTALL_PREFIX/lib" "$INSTALL_PREFIX/lib64" "$INSTALL_PREFIX/lib/x86_64-linux-gnu")
LIB_PATH=""
for candidate in "${LIB_DIR_CANDIDATES[@]}"; do
  if [ -f "$candidate/libxc.so" ] || [ -f "$candidate/libxc.dylib" ]; then
    LIB_PATH="$candidate"
    break
  fi
done

if [ -z "$LIB_PATH" ]; then
  echo "Error: libxc shared library not found in $INSTALL_PREFIX" >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  RPATH_FLAG="-Wl,-rpath,@loader_path"
  EXTRA_LINK=(-undefined dynamic_lookup)
else
  RPATH_FLAG="-Wl,-rpath,'\$ORIGIN'"
  EXTRA_LINK=()
fi

c++ -O3 -std=c++14 -fPIC -shared \
  $PYBIND11_INCLUDES \
  -I"$INSTALL_PREFIX/include" \
  -I"$VISIT_STRUCT_DIR" \
  "$LIBXC_DIR/src/helper.cc" \
  -L"$LIB_PATH" -lxc \
  "$RPATH_FLAG" \
  "${EXTRA_LINK[@]}" \
  -o "$TARGET"

strip --strip-unneeded "$TARGET" || true

echo "✓ Built helper module at $TARGET"
