#!/bin/bash
# Compile libxc and Python bindings

set -e

LIBXC_DIR="libxc"

cd "${LIBXC_DIR}"

# Get Python version info
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_IMPL=$(python3 -c "import sys; print(sys.implementation.name)")
PYTHON_TAG="cp${PYTHON_VERSION//./}"

# Build directories
BUILD_DIR="build/temp.linux-x86_64-${PYTHON_IMPL}${PYTHON_VERSION}"
LIB_DIR="build/lib.linux-x86_64-${PYTHON_IMPL}-${PYTHON_VERSION}"

# Check if libxc.a (static library) exists - this is Python-version independent
EXISTING_LIBXC=$(find build -path "*/src/libxc.a" -type f | head -1)
if [ -f "${BUILD_DIR}/src/libxc.a" ] || [ -n "$EXISTING_LIBXC" ]; then
    echo "✓ Found existing libxc.a (C library), skipping libxc rebuild"

    if [ -n "$EXISTING_LIBXC" ] && [ ! -f "${BUILD_DIR}/src/libxc.a" ]; then
        mkdir -p "${BUILD_DIR}/src"
        ln -sf "$(realpath "$EXISTING_LIBXC")" "${BUILD_DIR}/src/libxc.a"
        echo "  Linked existing libxc.a from $(basename "$(dirname "$EXISTING_LIBXC")")"
    fi

    TARGET_HELPER="${LIB_DIR}/pylibxc/helper.${PYTHON_IMPL}-${PYTHON_TAG}*.so"
    NEED_EXT_REBUILD=true
    if compgen -G "$TARGET_HELPER" > /dev/null; then
        if [ "src/helper.cc" -ot "$(ls $TARGET_HELPER | head -1)" ]; then
            NEED_EXT_REBUILD=false
        fi
    fi

    if [ "$NEED_EXT_REBUILD" = true ]; then
        echo "Building Python ${PYTHON_VERSION} extension module only..."
        python3 setup.py build_ext --inplace
        python3 setup.py bdist_wheel
    else
        echo "✓ Python ${PYTHON_VERSION} extension up to date"
    fi
else
    echo "Building libxc and Python bindings for the first time..."
    echo "This will take several minutes..."
    python3 setup.py bdist_wheel
fi

# Copy libxc.so to a Python-version-independent location if not already there
if [ -f "${LIB_DIR}/pylibxc/libxc.so" ] && [ ! -f "pylibxc/libxc.so" ]; then
    cp "${LIB_DIR}/pylibxc/libxc.so"* pylibxc/ 2>/dev/null || true
    echo "✓ Copied libxc.so to source directory"
fi

echo "✓ Compilation complete for Python ${PYTHON_VERSION}"
