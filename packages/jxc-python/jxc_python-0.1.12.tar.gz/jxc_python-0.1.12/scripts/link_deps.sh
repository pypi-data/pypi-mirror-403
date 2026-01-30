#!/bin/bash
# Link third_party dependencies into libxc tree expected by our CMake patch

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
LIBXC_DIR="$ROOT_DIR/libxc"
TP_DIR="$ROOT_DIR/third_party"

if [ ! -d "$LIBXC_DIR" ]; then
  echo "Error: $LIBXC_DIR not found. Did you run: make init-submodules?" >&2
  exit 1
fi

# Ensure pybind11 is accessible at libxc/pybind11
if [ -d "$TP_DIR/pybind11" ]; then
  if [ -L "$LIBXC_DIR/pybind11" ] || [ -e "$LIBXC_DIR/pybind11" ]; then
    : # already present
  else
    ln -sfn "$TP_DIR/pybind11" "$LIBXC_DIR/pybind11"
    echo "✓ Linked pybind11 -> libxc/pybind11"
  fi
else
  echo "Error: third_party/pybind11 missing. Initialize submodules." >&2
  exit 1
fi

# Provide visit_struct header where helper.cc expects it
VS_HDR_SRC="$TP_DIR/visit_struct/include/visit_struct/visit_struct.hpp"
VS_HDR_DST="$LIBXC_DIR/src/visit_struct.hpp"
if [ -f "$VS_HDR_SRC" ]; then
  if [ ! -L "$VS_HDR_DST" ] && [ -e "$VS_HDR_DST" ]; then
    echo "Info: $VS_HDR_DST already exists (not touching)"
  else
    ln -sfn "$VS_HDR_SRC" "$VS_HDR_DST"
    echo "✓ Linked visit_struct.hpp into libxc src/"
  fi
else
  echo "Error: $VS_HDR_SRC not found. Initialize submodules." >&2
  exit 1
fi

echo "✓ Dependencies linked"
