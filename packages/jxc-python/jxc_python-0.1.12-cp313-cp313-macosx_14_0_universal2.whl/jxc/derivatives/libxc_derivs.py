"""LibXC-backed helpers for VXC evaluation."""

from __future__ import annotations

import functools
from typing import Dict, Optional, Tuple

import jax.numpy as jnp
import numpy as np
import pylibxc


@functools.lru_cache(maxsize=None)
def _get_functional(name: str, spin: int) -> pylibxc.LibXCFunctional:
  return pylibxc.LibXCFunctional(name, spin)


def _as_array(value, columns: int) -> Optional[np.ndarray]:
  if value is None:
    return None
  arr = np.asarray(value, dtype=np.float64)
  if arr.ndim == 0:
    arr = arr.reshape(1, 1)
  elif arr.ndim == 1:
    arr = arr.reshape(-1, columns)
  return arr


def _evaluate(
  name: str,
  spin: int,
  rho: np.ndarray,
  sigma: Optional[np.ndarray],
  lapl: Optional[np.ndarray],
  tau: Optional[np.ndarray],
) -> Dict[str, jnp.ndarray]:
  lib_inputs: Dict[str, np.ndarray] = {"rho": rho}
  if sigma is not None:
    lib_inputs["sigma"] = sigma
  if lapl is not None:
    lib_inputs["lapl"] = lapl
  if tau is not None:
    lib_inputs["tau"] = tau

  out = _get_functional(name, spin).compute(lib_inputs, do_exc=False, do_vxc=True)
  result: Dict[str, jnp.ndarray] = {}
  for key in ("vrho", "vsigma", "vlapl", "vtau"):
    if key in out:
      arr = np.asarray(out[key], dtype=np.float64)
      result[key] = jnp.asarray(np.squeeze(arr))
  return result


def eval_unpolarized_vxc(
  name: str,
  rho,
  sigma=None,
  lapl=None,
  tau=None,
) -> Dict[str, jnp.ndarray]:
  rho_arr = _as_array(rho, 1)
  sigma_arr = _as_array(sigma, 1) if sigma is not None else None
  lapl_arr = _as_array(lapl, 1) if lapl is not None else None
  tau_arr = _as_array(tau, 1) if tau is not None else None
  return _evaluate(name, 1, rho_arr, sigma_arr, lapl_arr, tau_arr)


def eval_polarized_vxc(
  name: str,
  rho: Tuple,
  sigma: Optional[Tuple] = None,
  lapl: Optional[Tuple] = None,
  tau: Optional[Tuple] = None,
) -> Dict[str, jnp.ndarray]:
  rho_arr = np.stack(
      [np.asarray(rho[0], dtype=np.float64), np.asarray(rho[1], dtype=np.float64)],
      axis=1,
  )
  sigma_arr = None
  if sigma is not None:
    sigma_arr = np.stack(
        [
            np.asarray(sigma[0], dtype=np.float64),
            np.asarray(sigma[1], dtype=np.float64),
            np.asarray(sigma[2], dtype=np.float64),
        ],
        axis=1,
    )
  lapl_arr = None
  if lapl is not None:
    lapl_arr = np.stack(
        [
            np.asarray(lapl[0], dtype=np.float64),
            np.asarray(lapl[1], dtype=np.float64),
        ],
        axis=1,
    )
  tau_arr = None
  if tau is not None:
    tau_arr = np.stack(
        [
            np.asarray(tau[0], dtype=np.float64),
            np.asarray(tau[1], dtype=np.float64),
        ],
        axis=1,
    )
  return _evaluate(name, 2, rho_arr, sigma_arr, lapl_arr, tau_arr)

# Backwards-compatibility aliases (deprecated).
eval_unpolarized = eval_unpolarized_vxc
eval_polarized = eval_polarized_vxc
