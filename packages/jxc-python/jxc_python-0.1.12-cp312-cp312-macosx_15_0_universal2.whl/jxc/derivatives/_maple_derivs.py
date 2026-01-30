"""Order-agnostic Maple-backed derivative evaluators (VXC/FXC/KXC/LXC).

This module mirrors jxc.derivatives.ad_derivs but generalizes to other orders.
It never falls back to LibXC; when Maple code is unavailable for VXC,
you may opt into JAX AD via use_jax=True (FXC/KXC/LXC via AD are not
implemented here).
"""

from __future__ import annotations

import functools
import importlib
import os
import types
from typing import Dict, Optional, Tuple

import jax.numpy as jnp
import jax.scipy.special as jsp_special
import numpy as np

# For higher orders we do not dynamically generate at runtime; we import
# pre-generated modules under jxc.functionals and call pol_*/unpol_* directly.
from ..libxc_aliases import LIBXC_ALIAS_REMAP  # type: ignore
from jxc import get_params as GP_PARAMS
from .ad_derivs import _hydrate_params_for_module, _promote_param_arrays


def _order_to_max(suffix: str) -> int:
  suffix = suffix.lower()
  return {"vxc": 1, "fxc": 2, "kxc": 3, "lxc": 4}.get(suffix, 1)


def _family_from_name(name: str) -> Optional[str]:
  if name.startswith(("lda_", "hyb_lda_")):
    return "lda"
  if name.startswith(("gga_", "hyb_gga_")):
    return "gga"
  if name.startswith(("mgga_", "hyb_mgga_")):
    return "mgga"
  return None


def _suffix_for_order(order: str) -> str:
  order = order.lower()
  if order in ("vxc", "fxc", "kxc", "lxc"):
    return order
  raise ValueError(f"Unsupported derivative order: {order}")


def _find_maple_file(name: str) -> Tuple[str, str]:
  family = _family_from_name(name)
  if family is None:
    raise FileNotFoundError(f"Unsupported functional family for {name}")
  root = os.path.realpath(
      os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "..", "libxc", "maple")
  )

  # Try get_params().maple_name first; it is the canonical LibXC leaf name
  try:
    from jxc import get_params as _gp, XC_UNPOLARIZED as _XCU
    p = _gp(name, _XCU)
    maple_name = getattr(p, 'maple_name', '')
    if maple_name and maple_name != name:
      for subdir in (f"{family}_vxc", f"{family}_exc"):
        path = os.path.join(root, subdir, f"{maple_name}.mpl")
        if os.path.exists(path):
          return family, path
  except Exception:
    pass

  def _candidates(n: str):
    yield n
    rev = {v: k for k, v in LIBXC_ALIAS_REMAP.items()}
    if n in rev:
      yield rev[n]
    if n in LIBXC_ALIAS_REMAP:
      yield LIBXC_ALIAS_REMAP[n]
    if n.endswith("_mpw91"):
      yield n[:-6] + "pw91"
    if n.endswith("_wi0"):
      yield n[:-1]  # _wi0 -> _wi
    if n.endswith("_pbe_mol") or n.endswith("_pbe_sol"):
      yield n.rsplit("_", 2)[0]
      yield n.replace("_pbe_mol", "_pbe").replace("_pbe_sol", "_pbe")
    parts = n.split("_")
    if len(parts) > 3:
      yield "_".join(parts[:3])

  for cand in _candidates(name):
    exc = os.path.join(root, f"{family}_exc", f"{cand}.mpl")
    if os.path.exists(exc):
      return family, exc
    vxc = os.path.join(root, f"{family}_vxc", f"{cand}.mpl")
    if os.path.exists(vxc):
      return family, vxc
  raise FileNotFoundError(f"Maple file not found for {name}")


def _compile_module(code: str, mod_name: str) -> types.ModuleType:
  mod = types.ModuleType(mod_name)
  ns = mod.__dict__
  ns["__package__"] = "jxc.derivatives"
  ns["__name__"] = mod_name
  exec(code, ns, ns)
  return mod


@functools.lru_cache(maxsize=None)
def _load_module(name: str, order: str) -> types.ModuleType:
  # Always import the pre-generated functional module; no dynamic Maple generation here.
  try:
    return importlib.import_module(f"jxc.functionals.{name}")
  except Exception as exc:
    # Try alias remap before failing
    alias = LIBXC_ALIAS_REMAP.get(name, name)
    if alias != name:
      try:
        return importlib.import_module(f"jxc.functionals.{alias}")
      except Exception:
        pass
    # Try reverse alias map as a last resort
    rev = {v: k for k, v in LIBXC_ALIAS_REMAP.items()}
    if name in rev:
      try:
        return importlib.import_module(f"jxc.functionals.{rev[name]}")
      except Exception:
        pass
    raise ImportError(f"Failed to import pre-generated module for {name}") from exc


def _get_params(name: str, spin: int):
  try:
    from jxc import get_params as _gp
    return _gp(name, spin)
  except Exception:
    return types.SimpleNamespace(
        name=name,
        params=types.SimpleNamespace(),
        dens_threshold=np.float64(1e-30),
        zeta_threshold=np.float64(np.finfo(np.float64).eps),
    )


def _eval_composite_unpolarized(p, order: str, rho, sigma=None, lapl=None, tau=None) -> Dict[str, jnp.ndarray]:
  """Evaluate unpolarized derivatives for composite functionals via linear mix."""
  # Handle DEORBITALIZE pattern in the same spirit as EXC: use first child
  if getattr(p, 'maple_name', '') == 'DEORBITALIZE' and getattr(p, 'func_aux', None):
    p0 = p.func_aux[0]
    cname = getattr(p0, 'name', getattr(p0, 'maple_name', ''))
    cname = LIBXC_ALIAS_REMAP.get(cname, cname)
    return eval_unpolarized(cname, order, rho, sigma=sigma, lapl=lapl, tau=tau)
  out: Dict[str, jnp.ndarray] = {}
  mix = getattr(p, 'mix_coef', []) or []
  children = getattr(p, 'func_aux', []) or []
  for coef, cp in zip(mix, children):
    cname = getattr(cp, 'name', getattr(cp, 'maple_name', ''))
    cname = LIBXC_ALIAS_REMAP.get(cname, cname)
    cres = _eval_unpolarized_core(cname, order, rho, sigma=sigma, lapl=lapl, tau=tau)
    for k, v in cres.items():
      out[k] = (out.get(k, 0.0) + coef * jnp.asarray(v))
  bname = getattr(p, 'maple_name', '')
  if bname:
    base_in_aux = any(getattr(cp, 'name', '') == bname or getattr(cp, 'maple_name', '') == bname for cp in children)
    if not base_in_aux:
      try:
        bres = _eval_unpolarized_core(LIBXC_ALIAS_REMAP.get(bname, bname), order, rho, sigma=sigma, lapl=lapl, tau=tau)
        for k, v in bres.items():
          out[k] = (out.get(k, 0.0) + jnp.asarray(v))
      except Exception:
        pass
  return out


def _eval_composite_polarized(p, order: str, rho: Tuple, sigma=None, lapl=None, tau=None) -> Dict[str, jnp.ndarray]:
  """Evaluate polarized derivatives for composite functionals via linear mix."""
  if getattr(p, 'maple_name', '') == 'DEORBITALIZE' and getattr(p, 'func_aux', None):
    p0 = p.func_aux[0]
    cname = getattr(p0, 'name', getattr(p0, 'maple_name', ''))
    cname = LIBXC_ALIAS_REMAP.get(cname, cname)
    return eval_polarized(cname, order, rho, sigma=sigma, lapl=lapl, tau=tau)
  out: Dict[str, jnp.ndarray] = {}
  mix = getattr(p, 'mix_coef', []) or []
  children = getattr(p, 'func_aux', []) or []
  for coef, cp in zip(mix, children):
    cname = getattr(cp, 'name', getattr(cp, 'maple_name', ''))
    cname = LIBXC_ALIAS_REMAP.get(cname, cname)
    cres = _eval_polarized_core(cname, order, rho, sigma=sigma, lapl=lapl, tau=tau)
    for k, v in cres.items():
      out[k] = (out.get(k, 0.0) + coef * jnp.asarray(v))
  bname = getattr(p, 'maple_name', '')
  if bname:
    base_in_aux = any(getattr(cp, 'name', '') == bname or getattr(cp, 'maple_name', '') == bname for cp in children)
    if not base_in_aux:
      try:
        bres = _eval_polarized_core(LIBXC_ALIAS_REMAP.get(bname, bname), order, rho, sigma=sigma, lapl=lapl, tau=tau)
        for k, v in bres.items():
          out[k] = (out.get(k, 0.0) + jnp.asarray(v))
      except Exception:
        pass
  return out


def _eval_unpolarized_core(
    name: str,
    order: str,
    rho,
    sigma=None,
    lapl=None,
    tau=None,
) -> Dict[str, jnp.ndarray]:
  suffix = _suffix_for_order(order)
  # All orders: call pre-generated Maple derivative modules (no AD here).
  p = GP_PARAMS(name, 0)
  if getattr(p, 'func_aux', None):
    return _eval_composite_unpolarized(p, order, rho, sigma=sigma, lapl=lapl, tau=tau)
  mod = _load_module(name, order)
  r = jnp.asarray(rho, dtype=jnp.float64)
  s = None if sigma is None else jnp.asarray(sigma, dtype=jnp.float64)
  l = None if lapl is None else jnp.asarray(lapl, dtype=jnp.float64)
  t = None if tau is None else jnp.asarray(tau, dtype=jnp.float64)
  fn = getattr(mod, f"unpol_{suffix}", None)
  if fn is None:
    return {}
  return {k: jnp.asarray(v) for k, v in fn(p, r, s, l, t).items()}


def _eval_polarized_core(
    name: str,
    order: str,
    rho: Tuple,
    sigma: Optional[Tuple] = None,
    lapl: Optional[Tuple] = None,
    tau: Optional[Tuple] = None,
) -> Dict[str, jnp.ndarray]:
  suffix = _suffix_for_order(order)
  p = GP_PARAMS(name, 1)
  if getattr(p, 'func_aux', None):
    return _eval_composite_polarized(p, order, rho, sigma=sigma, lapl=lapl, tau=tau)
  mod = _load_module(name, order)
  r0 = jnp.asarray(rho[0], dtype=jnp.float64)
  r1 = jnp.asarray(rho[1], dtype=jnp.float64)
  s = None if sigma is None else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in sigma)
  l = None if lapl is None else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in lapl)
  t = None if tau is None else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in tau)
  fn = getattr(mod, f"pol_{suffix}", None)
  if fn is None:
    return {}
  return {k: jnp.asarray(v) for k, v in fn(p, (r0, r1), s if s is not None else (None, None, None), l if l is not None else (None, None), t if t is not None else (None, None)).items()}


def eval_unpolarized(
    name: str,
    rho,
    sigma=None,
    lapl=None,
    tau=None,
    order: str = "vxc",
    use_maple: bool = True,
) -> Dict[str, jnp.ndarray]:
  """Backwards-compatible unpolarized Maple derivative entry point.

  The `use_maple` flag is accepted for API compatibility but ignored here;
  higher-order AD is handled by ad_derivs, and this module is always Maple-backed.
  """
  return _eval_unpolarized_core(name, order, rho, sigma=sigma, lapl=lapl, tau=tau)


def eval_polarized(
    name: str,
    rho: Tuple,
    sigma: Optional[Tuple] = None,
    lapl: Optional[Tuple] = None,
    tau: Optional[Tuple] = None,
    order: str = "vxc",
    use_maple: bool = True,
) -> Dict[str, jnp.ndarray]:
  """Backwards-compatible polarized Maple derivative entry point."""
  return _eval_polarized_core(name, order, rho, sigma=sigma, lapl=lapl, tau=tau)
