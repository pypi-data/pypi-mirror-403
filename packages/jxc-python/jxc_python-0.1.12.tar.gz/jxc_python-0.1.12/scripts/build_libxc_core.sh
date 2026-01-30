#!/bin/bash
# Build the LibXC C core once so it can be reused across Python versions.

set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
LIBXC_DIR="$PROJECT_ROOT/libxc"
CORE_BUILD_DIR="$PROJECT_ROOT/build/libxc-core"
INSTALL_PREFIX="$PROJECT_ROOT/.libxc-core"

mkdir -p "$CORE_BUILD_DIR" "$INSTALL_PREFIX"

if [ -f "$INSTALL_PREFIX/lib/libxc.so" ] || [ -f "$INSTALL_PREFIX/lib64/libxc.so" ] || [ -f "$INSTALL_PREFIX/lib/libxc.dylib" ]; then
  echo "✓ LibXC core already built at $INSTALL_PREFIX"
  exit 0
fi

cmake -S "$LIBXC_DIR" -B "$CORE_BUILD_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=ON \
  -DBUILD_TESTING=OFF \
  -DENABLE_PYTHON=OFF \
  -DDISABLE_KXC=OFF \
  -DCMAKE_POLICY_VERSION=3.30 \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX"

CORES=$(python -c "import multiprocessing as mp; print(max(1, mp.cpu_count()))")
cmake --build "$CORE_BUILD_DIR" --target install --config Release --parallel ${CORES}
echo "✓ Installed LibXC core to $INSTALL_PREFIX"
