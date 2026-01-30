#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="${REPO_ROOT}/JXC.jl"

if [[ ! -d "${PROJECT_DIR}" ]]; then
  echo "JXC.jl project not found relative to ${BASH_SOURCE[0]}" >&2
  exit 1
fi

export JULIA_PKG_SERVER="${JULIA_PKG_SERVER:-}"
if [[ -x "${REPO_ROOT}/.venv/bin/python" && -z "${PYTHON:-}" ]]; then
  export PYTHON="${REPO_ROOT}/.venv/bin/python"
fi

cat <<'JL' | JULIA_PKG_SERVER="${JULIA_PKG_SERVER}" julia --project="${PROJECT_DIR}"
using Pkg
ENV["JULIA_PKG_SERVER"] = get(ENV, "JULIA_PKG_SERVER", "")
Pkg.instantiate()

using JXC

rho = fill(0.3, 4)
lda_params = JXC.get_params("lda_x", JXC.XC_UNPOLARIZED)
lda_exc = JXC.get_xc_functional("lda_x"; polarized=false)
println("LDA ε_xc sample → ", lda_exc(lda_params, rho))

b3lyp = JXC.get_xc_functional("hyb_gga_xc_b3lyp"; polarized=false)
# Uses the same rho and sigma signature as Python
sigma = fill(0.01, length(rho))
println("B3LYP ε_xc sample → ", b3lyp(rho; s=sigma))
println("B3LYP cam_alpha → ", b3lyp.cam_alpha)
JL
