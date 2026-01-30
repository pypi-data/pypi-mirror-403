#!/bin/bash
# Convert Maple files to Python/JAX code

set -euo pipefail

LIBXC_DIR="libxc"
FUNCTIONALS_DIR="jxc/functionals"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/maple_conversion_failures.log"
TIMEOUTS_FILE="$LOG_DIR/maple_timeouts.list"

mkdir -p "$LOG_DIR"
echo -n > "$LOG_FILE"
echo -n > "$TIMEOUTS_FILE"

# Default timeout for Maple if not provided
: "${JXC_MAPLE_TIMEOUT:=7200}"
export JXC_MAPLE_TIMEOUT

# Check if conversion is needed by looking for key generated files.
# Allow callers to force regeneration by setting JXC_FORCE_MAPLE=1.
if [ "${JXC_FORCE_MAPLE:-0}" != "1" ] && \
   [ -f "${FUNCTIONALS_DIR}/lda_x.py" ] && \
   [ -f "${FUNCTIONALS_DIR}/gga_x_pbe.py" ]; then
    echo "Python functionals already generated, skipping conversion"
    exit 0
fi

echo "Converting Maple to Python (combined EXC+VXC+FXC+KXC+LXC)..."

# Ensure jxc structure exists
mkdir -p "${FUNCTIONALS_DIR}"

# Remove legacy VXC-only package if present (no longer used)
if [ -d "jxc/functionals/vxc" ]; then
  echo "Removing legacy jxc/functionals/vxc (superseded by combined modules)"
  rm -rf jxc/functionals/vxc
fi

# Convert all Maple files in parallel
convert_family() {
  local fam="$1"; shift
  local files=("$@")
  local total=${#files[@]}
  local i=0
  echo "  -> ${fam}: ${total} files"
  for f in "${files[@]}"; do
    i=$((i+1))
    echo "     [${i}/${total}] ${fam} $(basename "$f")" >&2
    tmp_log=$(mktemp)
    if python3 maple_codegen.py exc_vxc_py "${fam}" "${f}" "${FUNCTIONALS_DIR}" >"${tmp_log}" 2>&1; then
      :
    else
      echo "[FAIL] ${fam} $(basename "$f")" >> "$LOG_FILE"
    fi
    # Echo output to console
    cat "${tmp_log}"
    # Record timeouts if present in output (non-fatal)
    if rg -q "Maple timeout" "${tmp_log}" 2>/dev/null; then
      echo "${fam} ${f}" >> "$TIMEOUTS_FILE"
    fi
    rm -f "${tmp_log}"
  done
}

LDA_FILES=( ${LIBXC_DIR}/maple/lda_exc/*.mpl )
GGA_FILES=( ${LIBXC_DIR}/maple/gga_exc/*.mpl )
MGGA_FILES=( ${LIBXC_DIR}/maple/mgga_exc/*.mpl )

echo "  Converting LDA functionals (EXC + VXC + FXC/KXC/LXC)..."
convert_family lda "${LDA_FILES[@]}"

echo "  Converting GGA functionals (EXC + VXC + FXC/KXC/LXC)..."
convert_family gga "${GGA_FILES[@]}"

echo "  Converting MGGA functionals (EXC + VXC + FXC/KXC/LXC)..."
convert_family mgga "${MGGA_FILES[@]}"

# Post-process to handle failed conversions
echo "Post-processing conversion results..."
python3 scripts/postprocess_maple_conversion.py "$FUNCTIONALS_DIR" "$LOG_FILE"

echo "✓ Maple conversion complete"
