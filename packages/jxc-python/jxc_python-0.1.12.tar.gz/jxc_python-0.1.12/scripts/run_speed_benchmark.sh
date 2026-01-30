#!/bin/bash
set -euo pipefail

# Locate workspace and Python
if [[ -n "${BUILD_WORKSPACE_DIRECTORY:-}" ]]; then
  WORKSPACE_DIR="${BUILD_WORKSPACE_DIRECTORY}"
elif [[ -n "${TEST_TMPDIR:-}" ]]; then
  WORKSPACE_DIR="${TEST_SRCDIR%/bazel-out/*}"
  WORKSPACE_DIR="${WORKSPACE_DIR%/execroot/*}"
  if [[ -d "/home/zekun/qc/projects/jxc" ]]; then
    WORKSPACE_DIR="/home/zekun/qc/projects/jxc"
  fi
else
  WORKSPACE_DIR="$(pwd)"
fi

PY_BIN="${PYTHON_BIN_PATH:-${PYTHON:-${WORKSPACE_DIR}/.venv/bin/python}}"
[[ -x "${PY_BIN}" ]] || PY_BIN="python3"

export PYTHONPATH="${WORKSPACE_DIR}:${PYTHONPATH:-}"

SCRIPT="${WORKSPACE_DIR}/scripts/speed_benchmark.py"

# Keep default functional set small for CI/runtime; allow args passthrough
exec "${PY_BIN}" "${SCRIPT}" "$@"

