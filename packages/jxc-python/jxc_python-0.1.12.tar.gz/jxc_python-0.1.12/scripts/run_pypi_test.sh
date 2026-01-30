#!/usr/bin/env bash
set -euo pipefail

for ver in 3.12 3.13; do
  echo "=== PyPI smoke test for Python ${ver} ==="
  TMP_DIR="/tmp/jxc-pypi-${ver}"
  echo "Creating fresh tmp dir ${TMP_DIR} ..."
  rm -rf "${TMP_DIR}"
  mkdir -p "${TMP_DIR}"

  ENV_DIR="${TMP_DIR}/.venv"
  echo "Creating uv environment ${ENV_DIR} with Python ${ver}..."
  (
    cd "${TMP_DIR}"
    UV_PROJECT_ENVIRONMENT="${ENV_DIR}" uv venv --python "${ver}" "${ENV_DIR}"
  )

  echo "Installing jxc-python and jax[cpu]==0.7.1 into ${ENV_DIR}..."
  (
    cd "${TMP_DIR}"
    "${ENV_DIR}/bin/python" -m ensurepip --upgrade --default-pip >/dev/null 2>&1
    "${ENV_DIR}/bin/python" -m pip install --quiet jxc-python "jax[cpu]==0.7.1"
  )

  echo "Running EXC/VXC/FXC/KXC/LXC smoke tests on CPU (Python ${ver})..."
  (
    cd "${TMP_DIR}"
    JAX_PLATFORM_NAME=cpu "${ENV_DIR}/bin/python" << 'PY'
import jax.numpy as jnp, jxc

print("jxc version:", getattr(jxc, "__version__", "unknown"))

rho = jnp.array([0.1, 0.2, 0.3])
sigma = jnp.array([0.01, 0.05, 0.1])

# EXC smoke test (B3LYP)
b3 = jxc.get_xc_functional("hyb_gga_xc_b3lyp", polarized=False)
print("CPU B3LYP eps_xc:", b3(rho, s=sigma))
print("CPU B3LYP cam_alpha:", getattr(b3, "cam_alpha", None))

# Derivative smoke tests on a simple GGA (AD path)
vxc = jxc.get_xc_functional("gga_x_pbe", polarized=False, order="vxc")
fxc = jxc.get_xc_functional("gga_x_pbe", polarized=False, order="fxc")
kxc = jxc.get_xc_functional("gga_x_pbe", polarized=False, order="kxc")
lxc = jxc.get_xc_functional("gga_x_pbe", polarized=False, order="lxc")

print("VXC keys:", sorted(vxc(rho, sigma=sigma).keys()))
print("FXC keys:", sorted(fxc(rho, sigma=sigma).keys()))
print("KXC keys:", sorted(kxc(rho, sigma=sigma).keys()))
print("LXC keys:", sorted(lxc(rho, sigma=sigma).keys()))

# list_functionals sanity check
names = jxc.list_functionals()
print("Total LibXC functionals visible:", len(names))
print("Sample BLYP-like entries:", [n for n in names if "blyp" in n.lower()][:5])
PY
  )

  echo "CPU-only JAX smoke test complete for Python ${ver} in ${TMP_DIR}."
done

