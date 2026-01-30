#!/bin/bash
# Convert Maple files to Julia code

set -e

LIBXC_DIR="libxc"
JULIA_PKG_DIR="JXC.jl"
JULIA_FUNCTIONALS_DIR="${JULIA_PKG_DIR}/src/functionals"
JULIA_VXC_DIR="${JULIA_PKG_DIR}/src/vxc"

# Ensure Julia package structure exists
mkdir -p "${JULIA_FUNCTIONALS_DIR}"
mkdir -p "${JULIA_VXC_DIR}"

echo "Converting Maple to Julia..."

# Convert all Maple files
echo "  Converting LDA functionals..."
ls ${LIBXC_DIR}/maple/lda_exc/*.mpl 2>/dev/null | xargs -P4 -I{} python3 maple_codegen_julia.py lda {} $JULIA_FUNCTIONALS_DIR || true
ls ${LIBXC_DIR}/maple/lda_vxc/*.mpl 2>/dev/null | xargs -P4 -I{} python3 maple_codegen_julia.py lda {} $JULIA_VXC_DIR || true

echo "  Converting GGA functionals..."
ls ${LIBXC_DIR}/maple/gga_exc/*.mpl 2>/dev/null | xargs -P4 -I{} python3 maple_codegen_julia.py gga {} $JULIA_FUNCTIONALS_DIR || true
ls ${LIBXC_DIR}/maple/gga_vxc/*.mpl 2>/dev/null | xargs -P4 -I{} python3 maple_codegen_julia.py gga {} $JULIA_VXC_DIR || true

echo "  Converting MGGA functionals..."
ls ${LIBXC_DIR}/maple/mgga_exc/*.mpl 2>/dev/null | xargs -P4 -I{} python3 maple_codegen_julia.py mgga {} $JULIA_FUNCTIONALS_DIR || true
ls ${LIBXC_DIR}/maple/mgga_vxc/*.mpl 2>/dev/null | xargs -P4 -I{} python3 maple_codegen_julia.py mgga {} $JULIA_VXC_DIR || true

# Post-process to handle failed conversions
echo "Post-processing Julia conversion results..."
python3 scripts/postprocess_julia_conversion.py $JULIA_FUNCTIONALS_DIR logs/julia_conversion_failures.log

echo "✓ Julia Maple conversion complete"
