#!/bin/bash
# Re-run Maple conversion only for modules that timed out in previous run.

set -euo pipefail

LIBXC_DIR="libxc"
FUNCTIONALS_DIR="jxc/functionals"
LOG_DIR="logs"
TIMEOUTS_FILE="$LOG_DIR/maple_timeouts.list"
RETRY_LOG="$LOG_DIR/maple_timeouts_retry_failures.log"

if [[ ! -f "$TIMEOUTS_FILE" ]]; then
  echo "No timeouts file found at $TIMEOUTS_FILE"
  exit 0
fi

echo -n > "$RETRY_LOG"

# Default timeout can be overridden by caller
: "${JXC_MAPLE_TIMEOUT:=7200}"
export JXC_MAPLE_TIMEOUT

# Ensure output dir exists
mkdir -p "$FUNCTIONALS_DIR"

mapfile -t entries < <(awk '{print $1" "$2}' "$TIMEOUTS_FILE" | sort -u)
total=${#entries[@]}
idx=0
for line in "${entries[@]}"; do
  idx=$((idx+1))
  fam=$(echo "$line" | awk '{print $1}')
  file=$(echo "$line" | awk '{print $2}')
  echo "[retry ${idx}/${total}] ${fam} $(basename "$file") with timeout ${JXC_MAPLE_TIMEOUT}s" >&2
  tmp_log=$(mktemp)
  if python3 maple_codegen.py exc_vxc_py "$fam" "$file" "$FUNCTIONALS_DIR" >"${tmp_log}" 2>&1; then
    :
  else
    echo "[RETRY_FAIL] ${fam} $(basename "$file")" >> "$RETRY_LOG"
  fi
  cat "${tmp_log}"
  rm -f "${tmp_log}"
done

echo "✓ Retry complete. Failures (if any) recorded in $RETRY_LOG"
