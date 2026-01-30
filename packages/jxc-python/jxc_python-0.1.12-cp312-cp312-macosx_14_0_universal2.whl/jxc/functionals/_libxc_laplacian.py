"""LibXC-backed wrappers for Laplacian-sensitive MGGA XC functionals."""

from __future__ import annotations

import functools
from typing import Tuple

import jax
import jax.numpy as jnp
import numpy as np
import pylibxc


@functools.lru_cache(maxsize=None)
def _get_libxc(name: str, spin: int) -> pylibxc.LibXCFunctional:
  return pylibxc.LibXCFunctional(name, spin)


def _prepare_unpolarized(rho: jnp.ndarray, sigma: jnp.ndarray, lapl: jnp.ndarray):
  rho_arr = jnp.asarray(rho, dtype=jnp.float64).reshape(-1, 1)
  sigma_arr = jnp.asarray(sigma, dtype=jnp.float64).reshape(-1, 1)
  lapl_arr = jnp.asarray(lapl, dtype=jnp.float64).reshape(-1, 1)
  return rho_arr, sigma_arr, lapl_arr


def _prepare_polarized(
  rho: Tuple[jnp.ndarray, jnp.ndarray],
  sigma: Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray],
  lapl: Tuple[jnp.ndarray, jnp.ndarray],
):
  rho_arr = jnp.stack([jnp.asarray(rho[0], dtype=jnp.float64),
                       jnp.asarray(rho[1], dtype=jnp.float64)], axis=1)
  sigma_arr = jnp.stack(
      [jnp.asarray(sigma[0], dtype=jnp.float64),
       jnp.asarray(sigma[1], dtype=jnp.float64),
       jnp.asarray(sigma[2], dtype=jnp.float64)],
      axis=1,
  )
  lapl_arr = jnp.stack([jnp.asarray(lapl[0], dtype=jnp.float64),
                        jnp.asarray(lapl[1], dtype=jnp.float64)], axis=1)
  return rho_arr, sigma_arr, lapl_arr


def _libxc_callback(name: str, spin: int, rho, sigma, lapl):
  rho_np = np.asarray(rho, dtype=np.float64)
  sigma_np = np.asarray(sigma, dtype=np.float64)
  lapl_np = np.asarray(lapl, dtype=np.float64)
  inputs = {
      "rho": rho_np,
      "sigma": sigma_np,
      "lapl": lapl_np,
  }
  out = _get_libxc(name, spin).compute(inputs, do_vxc=True)
  energy = np.asarray(out["zk"], dtype=np.float64).reshape(rho_np.shape[0])
  vrho = np.asarray(out["vrho"], dtype=np.float64)
  vsigma = np.asarray(out["vsigma"], dtype=np.float64)
  vlapl = np.asarray(out["vlapl"], dtype=np.float64)
  return energy, vrho, vsigma, vlapl


def _libxc_energy_core(name: str, spin: int, rho, sigma, lapl):
  shapes = (
      jax.ShapeDtypeStruct((rho.shape[0],), jnp.float64),
      jax.ShapeDtypeStruct((rho.shape[0], rho.shape[1]), jnp.float64),
      jax.ShapeDtypeStruct((sigma.shape[0], sigma.shape[1]), jnp.float64),
      jax.ShapeDtypeStruct((lapl.shape[0], lapl.shape[1]), jnp.float64),
  )
  return jax.pure_callback(
      lambda rho_cb, sigma_cb, lapl_cb: _libxc_callback(name, spin, rho_cb, sigma_cb, lapl_cb),
      shapes,
      rho,
      sigma,
      lapl,
  )


@functools.lru_cache(maxsize=None)
def _make_energy_fn(name: str, spin: int):
  def core(rho, sigma, lapl):
    return _libxc_energy_core(name, spin, rho, sigma, lapl)

  @jax.custom_vjp
  def energy(rho, sigma, lapl):
    energy_val, _, _, _ = core(rho, sigma, lapl)
    return energy_val

  def fwd(rho, sigma, lapl):
    energy_val, vrho, vsigma, vlapl = core(rho, sigma, lapl)
    return energy_val, (vrho, vsigma, vlapl)

  def bwd(residual, g):
    vrho, vsigma, vlapl = residual
    g_arr = jnp.asarray(g, dtype=jnp.float64).reshape(-1, 1)
    grad_rho = g_arr * jnp.asarray(vrho, dtype=jnp.float64)
    grad_sigma = g_arr * jnp.asarray(vsigma, dtype=jnp.float64)
    grad_lapl = g_arr * jnp.asarray(vlapl, dtype=jnp.float64)
    return grad_rho, grad_sigma, grad_lapl

  energy.defvjp(fwd, bwd)
  return energy


def eval_unpolarized(name: str, rho, sigma, lapl):
  rho_arr, sigma_arr, lapl_arr = _prepare_unpolarized(rho, sigma, lapl)
  energy_fn = _make_energy_fn(name, 1)
  energy = energy_fn(rho_arr, sigma_arr, lapl_arr)
  return energy.reshape(-1)


def eval_polarized(
  name: str,
  rho: Tuple[jnp.ndarray, jnp.ndarray],
  sigma: Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray],
  lapl: Tuple[jnp.ndarray, jnp.ndarray],
):
  rho_arr, sigma_arr, lapl_arr = _prepare_polarized(rho, sigma, lapl)
  energy_fn = _make_energy_fn(name, 2)
  energy = energy_fn(rho_arr, sigma_arr, lapl_arr)
  return energy.reshape(-1)
