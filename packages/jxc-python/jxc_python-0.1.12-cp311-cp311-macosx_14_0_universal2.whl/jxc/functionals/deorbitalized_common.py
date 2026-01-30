"""Shared helpers for deorbitalized (L-type) MGGA functionals.

These functionals replace the explicit kinetic-energy density ``tau`` with a
model derived from the PC07 kinetic functional.  LibXC accomplishes this by
evaluating PC07 on each spin channel independently and reusing the canonical
MGGA Maple implementation.  We mirror that behaviour in pure JAX so the
runtime stays Maple-free and JIT-friendly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Tuple

import jax.numpy as jnp
import numpy as np

from jxc import XC_POLARIZED, XC_UNPOLARIZED, get_params
from . import mgga_k_pc07


@lru_cache(maxsize=None)
def _base_template(base_name: str, polarized: bool):
  spin = XC_POLARIZED if polarized else XC_UNPOLARIZED
  return get_params(base_name, spin)


@lru_cache(maxsize=None)
def _pc07_template(polarized: bool):
  spin = XC_POLARIZED if polarized else XC_UNPOLARIZED
  return get_params("mgga_k_pc07", spin)


def _as_numpy(value):
  return np.asarray(value, dtype=np.float64)


def prepare_base_params(
  base_name: str,
  polarized: bool,
  user_params,
  override_fields: Iterable[str],
):
  template = _base_template(base_name, polarized)
  overrides = {}
  if isinstance(user_params, (list, tuple)):
    for field, value in zip(override_fields, user_params):
      overrides[field] = _as_numpy(value)
  else:
    for field in override_fields:
      if hasattr(user_params, field):
        overrides[field] = _as_numpy(getattr(user_params, field))
  if overrides:
    params = template.params._replace(**overrides)
    return template._replace(params=params)
  return template


def prepare_pc07_params(polarized: bool, user_params):
  template = _pc07_template(polarized)
  overrides = {}
  if hasattr(user_params, "pc07_a"):
    overrides["a"] = _as_numpy(getattr(user_params, "pc07_a"))
  if hasattr(user_params, "pc07_b"):
    overrides["b"] = _as_numpy(getattr(user_params, "pc07_b"))
  if overrides:
    params = template.params._replace(**overrides)
    return template._replace(params=params)
  return template


def _ensure_array(value, reference):
  ref = jnp.asarray(reference, dtype=jnp.float64)
  if value is None:
    return jnp.zeros_like(ref)
  return jnp.asarray(value, dtype=jnp.float64)


def _pc07_tau_unpolarized(pc07_params, r, s, l):
  rho = jnp.asarray(r, dtype=jnp.float64)
  sigma = _ensure_array(s, rho)
  lapl = _ensure_array(l, rho)
  zeros = jnp.zeros_like(rho)
  energy = mgga_k_pc07.unpol(pc07_params, rho, sigma, lapl, zeros)
  return rho * jnp.asarray(energy, dtype=jnp.float64)


def _pc07_tau_polarized(pc07_params, r, s, l):
  r0 = jnp.asarray(r[0], dtype=jnp.float64)
  r1 = jnp.asarray(r[1], dtype=jnp.float64)

  sigma0 = None if s is None else s[0]
  sigma2 = None if s is None else s[2]
  lapl0 = None if l is None else l[0]
  lapl1 = None if l is None else l[1]

  def _channel(rho_val, sigma_diag, lapl_val):
    zero = jnp.zeros_like(rho_val)
    sigma_diag_arr = _ensure_array(sigma_diag, rho_val)
    lapl_arr = _ensure_array(lapl_val, rho_val)
    energy = mgga_k_pc07.pol(
      pc07_params,
      (rho_val, zero),
      (sigma_diag_arr, zero, zero),
      (lapl_arr, zero),
      (zero, zero),
    )
    return rho_val * jnp.asarray(energy, dtype=jnp.float64)

  tau0 = _channel(r0, sigma0, lapl0)
  tau1 = _channel(r1, sigma2, lapl1)
  return tau0, tau1


def evaluate_deorbitalized(base_module, base_params, pc07_params, r, s, l, polarized: bool):
  if polarized:
    tau_eff = _pc07_tau_polarized(pc07_params, r, s, l)
    return base_module.pol(base_params, r, s, l, tau_eff)
  tau_eff = _pc07_tau_unpolarized(pc07_params, r, s, l)
  return base_module.unpol(base_params, r, s, l, tau_eff)
