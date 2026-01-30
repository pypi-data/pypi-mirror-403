#!/bin/bash
# Generate helper.cc from libxc source

set -e

LIBXC_DIR="libxc"

echo "Generating helper.cc..."
python3 make_helper.py "${LIBXC_DIR}/"

# Apply CMakeLists.txt patch if not already applied
if ! grep -q "helper" "${LIBXC_DIR}/CMakeLists.txt" 2>/dev/null; then
    echo "Applying CMakeLists.txt patch..."
    patch "${LIBXC_DIR}/CMakeLists.txt" CMakeLists.txt.patch
else
    echo "CMakeLists.txt already patched"
fi

echo "✓ Helper generation complete"

echo "Normalizing libxc/setup.py for modern builds..."
python3 scripts/ensure_pylibxc_setup.py
