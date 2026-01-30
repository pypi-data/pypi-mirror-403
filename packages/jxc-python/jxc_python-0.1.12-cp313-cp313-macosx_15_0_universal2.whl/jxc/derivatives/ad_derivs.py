from __future__ import annotations

import functools
import os
import types
import importlib
from typing import Dict, Optional, Tuple

import jax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
import numpy as np
import scipy.special as sp_special

# Dynamic Maple generation removed - all VXC must be pre-generated via convert_maple_targeted.py

from ..functionals import utils as _utils  # ensure JAX x64 config
from ..functionals.utils import LambertW as _lambertw

try:
  from maple_codegen import _apply_post_replacements  # type: ignore
except Exception:  # pragma: no cover
  def _apply_post_replacements(rendered: str) -> str:
    return rendered

if not hasattr(jnp, "erfc"):
  jnp.erfc = jsp_special.erfc  # type: ignore[attr-defined]


def _hydrate_params_for_module(p):
  """Ensure params object has fields some Maple modules expect (alpha_ab, etc.).

  Provides zeros for missing fields to avoid AttributeError in generated code.
  Does not alter present fields.
  """
  try:
    params = getattr(p, 'params', None)
    if params is None:
      return p
    need = ( 'alpha_ab', 'alpha_ss', 'dab', 'dss', 'cab', 'css', 'gamma_ab', 'gamma_ss', 'Fermi_D_cnst' )
    # Robust dict conversion for namedtuples/namespaces
    pd = _to_dict(p)
    # Build an overlay for required fields without losing original attributes
    class _ParamsComposite:
      __slots__ = ("_base", "_overlay")
      def __init__(self, base):
        object.__setattr__(self, "_base", base)
        object.__setattr__(self, "_overlay", {})
      def __getattr__(self, attr):
        ov = object.__getattribute__(self, "_overlay")
        if attr in ov:
          return ov[attr]
        base = object.__getattribute__(self, "_base")
        try:
          return getattr(base, attr)
        except AttributeError:
          return 0.0
      def __setattr__(self, attr, value):
        ov = object.__getattribute__(self, "_overlay")
        ov[attr] = value
    composite = _ParamsComposite(params)
    # Inject missing fields as zeros or promoted arrays in overlay
    for k in need:
      try:
        has = hasattr(params, k)
      except Exception:
        has = False
      if not has:
        setattr(composite, k, (1.0 if k == 'Fermi_D_cnst' else 0.0))
      else:
        try:
          val = getattr(params, k)
          if not isinstance(val, (list, tuple, np.ndarray)):
            arr = np.zeros((6,), dtype=np.float64)
            arr[0] = np.nan
            setattr(composite, k, arr)
        except Exception:
          setattr(composite, k, 0.0)
    pd['params'] = composite
    out_p = types.SimpleNamespace(**pd)
    # Ensure sensible top-level thresholds (used by utils.opz_pow_n, etc.)
    try:
      if not hasattr(out_p, 'zeta_threshold') or float(getattr(out_p, 'zeta_threshold', 0.0)) <= 0.0:
        out_p.zeta_threshold = np.finfo(np.float64).eps
    except Exception:
      out_p.zeta_threshold = np.finfo(np.float64).eps
    try:
      if not hasattr(out_p, 'dens_threshold') or float(getattr(out_p, 'dens_threshold', 0.0)) <= 0.0:
        out_p.dens_threshold = np.float64(1e-30)
    except Exception:
      out_p.dens_threshold = np.float64(1e-30)
    return out_p
  except Exception:
    return p

def _promote_param_arrays(p):
  try:
    params = getattr(p, 'params', None)
    if params is None:
      return p
    pd = _to_dict(p)
    pr = _to_dict(params)
    # If we cannot introspect params, keep original to avoid losing attributes
    if not isinstance(pr, dict) or len(pr) == 0:
      return p
    new_params = types.SimpleNamespace(**pr)
    def _as_vec(val):
      if isinstance(val, (list, tuple, np.ndarray)):
        return val
      arr = np.zeros((6,), dtype=np.float64)
      arr[0] = np.nan
      return arr
    for k in ('css','cab','dab','dss'):
      if hasattr(new_params, k):
        setattr(new_params, k, _as_vec(getattr(new_params, k)))
    pd['params'] = new_params
    return types.SimpleNamespace(**pd)
  except Exception:
    return p


def _family_from_name(name: str) -> Optional[str]:
  if name.startswith(("lda_", "hyb_lda_")):
    return "lda"
  if name.startswith(("gga_", "hyb_gga_")):
    return "gga"
  if name.startswith(("mgga_", "hyb_mgga_")):
    return "mgga"
  return None


def _needs_density_prefactor(name: str) -> bool:
  """Return True if rho*epsilon is required to obtain the energy density."""
  # For kinetic functionals the Maple EXC already yields an energy density,
  # so multiplying by rho would double count.
  return not _is_kinetic_functional(name)


def _is_kinetic_functional(name: str) -> bool:
  lowered = name.lower()
  if "_xc_" in lowered:
    return False
  return "_k_" in lowered or lowered.endswith("_k")


def _build_unpolarized_energy_fn(name: str, exc_callable):
  if _needs_density_prefactor(name):
    return lambda rho, sigma, lapl, tau: rho * exc_callable(rho, sigma, lapl, tau)
  return lambda rho, sigma, lapl, tau: exc_callable(rho, sigma, lapl, tau)


def _build_polarized_energy_fn(name: str, exc_callable, *, scale_with_density: bool = True):
  if scale_with_density and _needs_density_prefactor(name):
    return lambda rho0, rho1, *rest: (rho0 + rho1) * exc_callable(rho0, rho1, *rest)
  return lambda rho0, rho1, *rest: exc_callable(rho0, rho1, *rest)


from ..libxc_aliases import LIBXC_ALIAS_REMAP  # type: ignore

LIBXC_ALIAS_REVERSE = {v: k for k, v in LIBXC_ALIAS_REMAP.items() if v}


def _find_maple_file(name: str) -> Tuple[str, str]:
  family = _family_from_name(name)
  if family is None:
    raise FileNotFoundError(f"Unsupported functional family for {name}")
  root = os.path.join(
    os.path.dirname(
      os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    ),
    "libxc",
    "maple",
  )

  # First, try to get maple_name from get_params
  try:
    from jxc import get_params as _get_params, XC_UNPOLARIZED as _XCU
    p = _get_params(name, _XCU)
    maple_name = getattr(p, 'maple_name', '')
    if maple_name and maple_name != name:
      # Try the maple_name first (it's the canonical name)
      for subdir in [f"{family}_vxc", f"{family}_exc"]:
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
  # Ensure relative imports in generated modules resolve against the derivatives package
  ns["__package__"] = "jxc.derivatives"
  ns["__name__"] = mod_name
  exec(code, ns, ns)
  return mod


def _eval_leaf_unpol_with_p(name: str, p_obj, r, s, l, t) -> Dict[str, jnp.ndarray]:
  target = _module_name_for_params(name, p_obj)
  mod = _load_module(target)
  p_obj = _hydrate_params_for_module(p_obj)
  fn = getattr(mod, 'unpol_vxc', None)
  if fn is None:
    return {}
  res = fn(p_obj, r, s, l, t)
  return {k: jnp.asarray(v) for k, v in res.items()}


def _eval_leaf_pol_with_p(name: str, p_obj, r_pair: Tuple, s=None, l=None, t=None) -> Dict[str, jnp.ndarray]:
  target = _module_name_for_params(name, p_obj)
  mod = _load_module(target)
  p_obj = _hydrate_params_for_module(p_obj)
  fn = getattr(mod, 'pol_vxc', None)
  if fn is None:
    return {}
  res = fn(p_obj, r_pair, s if s is not None else (None, None, None), l if l is not None else (None, None), t if t is not None else (None, None))
  return {k: jnp.asarray(v) for k, v in res.items()}


@functools.lru_cache(maxsize=None)
def _load_exc_module_for_ad(name: str) -> types.ModuleType:
  """Dynamically load an EXC module (pol/unpol) for AD.

  Prefers pre-generated module if available; Maple compilation is disabled at
  runtime to keep the system Maple-free.
  """
  # Try pre-generated EXC module
  try:
    return importlib.import_module(f"jxc.functionals.{name}")
  except Exception:
    pass
  # Try alias remap before giving up
  alias = LIBXC_ALIAS_REMAP.get(name, name)
  if alias and alias != name:
    try:
      return importlib.import_module(f"jxc.functionals.{alias}")
    except Exception:
      pass
  rev_alias = LIBXC_ALIAS_REVERSE.get(name, name)
  if rev_alias and rev_alias != name:
    try:
      return importlib.import_module(f"jxc.functionals.{rev_alias}")
    except Exception:
      pass
  raise ImportError(
      f"EXC module '{name}' is not pre-generated. Please run "
      f"'convert_maple_targeted.py exc --functionals {name}' to generate it."
  )


def _slice_tuple(data: Optional[Tuple], index: int, fallback: Tuple) -> Tuple:
  if data is None:
    return fallback
  return tuple(comp[index] for comp in data)  # type: ignore[index]


def _stack_results(
  results: list[Dict[str, jnp.ndarray]],
) -> Dict[str, jnp.ndarray]:
  keys = results[0].keys()
  return {
    key: jnp.stack([jnp.asarray(sample[key]) for sample in results], axis=0)
    for key in keys
  }


def _ensure_special_functions(mod: types.ModuleType) -> None:
  if getattr(mod, "_jxc_special_patched", False):
    return
  lambertw_fn = getattr(jsp_special, "lambertw", None) or _lambertw
  if "scipy" not in mod.__dict__:
    mod.scipy = types.SimpleNamespace(
      special=types.SimpleNamespace(
        erf=jsp_special.erf,
        erfc=jsp_special.erfc,
        lambertw=lambertw_fn,
        i0=jsp_special.i0,
        i1=jsp_special.i1,
      )
    )
  mod.lambertw = lambertw_fn  # type: ignore[attr-defined]
  mod.erf = jsp_special.erf  # type: ignore[attr-defined]
  mod.erfc = jsp_special.erfc  # type: ignore[attr-defined]
  mod._jxc_special_patched = True  # type: ignore[attr-defined]


def _evaluate_pol_derivatives(
  mod: types.ModuleType,
  p_stub,
  rho: Tuple,
  sigma: Optional[Tuple],
  lapl: Optional[Tuple],
  tau: Optional[Tuple],
) -> Dict[str, jnp.ndarray]:
  r0, r1 = rho
  r0_arr = jnp.asarray(r0, dtype=jnp.float64)
  r1_arr = jnp.asarray(r1, dtype=jnp.float64)
  sigma_tuple = (
    None
    if sigma is None
    else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in sigma)
  )
  lapl_tuple = (
    None
    if lapl is None
    else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in lapl)
  )
  tau_tuple = (
    None
    if tau is None
    else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in tau)
  )

  _ensure_special_functions(mod)
  # Ensure parameter object has required fields for generated Maple code
  p_stub = _hydrate_params_for_module(p_stub)

  if r0_arr.ndim == 0:
    res = mod.pol_vxc(
      p_stub,
      (r0_arr, r1_arr),
      sigma_tuple if sigma_tuple is not None else (None, None, None),
      lapl_tuple if lapl_tuple is not None else (None, None),
      tau_tuple if tau_tuple is not None else (None, None),
    )
    return {k: jnp.asarray(v) for k, v in res.items()}

  size = int(r0_arr.shape[0])
  results: list[Dict[str, jnp.ndarray]] = []
  for i in range(size):
    sigma_sample = _slice_tuple(sigma_tuple, i, (None, None, None))
    lapl_sample = _slice_tuple(lapl_tuple, i, (None, None))
    tau_sample = _slice_tuple(tau_tuple, i, (None, None))
    res = mod.pol_vxc(
      p_stub,
      (r0_arr[i], r1_arr[i]),
      sigma_sample,
      lapl_sample,
      tau_sample,
    )
    results.append({k: jnp.asarray(v) for k, v in res.items()})
  return _stack_results(results)


def _ad__get_child_name(cp) -> str:
  return getattr(cp, 'name', getattr(cp, 'maple_name', ''))


def _to_dict(obj):
  try:
    return obj._asdict()
  except Exception:
    return obj.__dict__ if hasattr(obj, '__dict__') else {}


def _merge_param_struct(base_params, variant_params):
  """Merge param namedtuples/namespaces: variant overrides base on matching fields."""
  b = _to_dict(base_params).copy()
  v = _to_dict(variant_params)
  import numpy as _np
  for k, val in v.items():
    if k in b:
      # Avoid overwriting array-like base fields with scalar floats
      base_val = b[k]
      is_base_seq = isinstance(base_val, (list, tuple, _np.ndarray))
      is_val_seq = isinstance(val, (list, tuple, _np.ndarray))
      if is_base_seq and not is_val_seq:
        continue
    b[k] = val
  return types.SimpleNamespace(**b)


def _merge_p_objects(base_p, variant_p):
  """Create a merged parameter object with base fields and variant param overrides."""
  bd = _to_dict(base_p)
  vd = _to_dict(variant_p)
  merged = bd.copy()
  # Merge nested params
  if 'params' in bd and 'params' in vd and bd['params'] and vd['params']:
    merged['params'] = _merge_param_struct(bd['params'], vd['params'])
  # Override top-level fields from variant (e.g., cam_alpha/beta/omega, thresholds)
  for k, val in vd.items():
    if k == 'params':
      continue
    merged[k] = val
  return types.SimpleNamespace(**merged)


def _ad__exc_pol_callable(name: str, p_stub):
  """Return a JAX-friendly callable E(r0,r1,s0,s1,s2,l0,l1,t0,t1) for EXC energy (polarized).

  Prefers composite decomposition via get_params before importing modules,
  avoiding import-time ModuleNotFoundError for non-existent EXC modules.
  """
  from jxc import get_params as _get_params, XC_POLARIZED as _XCP
  from ..libxc_aliases import LIBXC_ALIAS_REMAP
  p = _get_params(name, _XCP)
  if hasattr(p, 'func_aux') and p.func_aux:
    child_calls = []
    for cp in p.func_aux:
      cname = _ad__get_child_name(cp)
      if not cname:
        continue
      cname = LIBXC_ALIAS_REMAP.get(cname, cname)
      child_stub = cp if cp is not None else p_stub
      child_calls.append(_ad__exc_pol_callable(cname, child_stub))

    def E(r0, r1, s0, s1, s2, l0, l1, t0, t1):
      total = 0.0
      for coef, cE in zip(p.mix_coef, child_calls):
        total = total + coef * cE(r0, r1, s0, s1, s2, l0, l1, t0, t1)
      bname = getattr(p, 'maple_name', '')
      if bname:
        # Only add base component if not already in aux
        base_in_aux = any(
          _ad__get_child_name(cp) == bname or getattr(cp, 'maple_name', '') == bname
          for cp in p.func_aux
        )
        if not base_in_aux:
          try:
            bcall = _ad__exc_pol_callable(LIBXC_ALIAS_REMAP.get(bname, bname), p_stub)
            total = total + bcall(r0, r1, s0, s1, s2, l0, l1, t0, t1)
          except BaseException:
            pass
      return total
    return E

  # Leaf: import EXC module using maple_name or alias if present
  leaf = getattr(p, "maple_name", "") or name
  try:
    mod_exc = _load_exc_module_for_ad(leaf)
  except ImportError as exc:
    alias_leaf = LIBXC_ALIAS_REMAP.get(leaf, leaf)
    if alias_leaf == leaf:
      raise
    leaf = alias_leaf
    mod_exc = _load_exc_module_for_ad(leaf)
  _ensure_special_functions(mod_exc)
  try:
    from jxc import get_params as _get_params, XC_POLARIZED as _XCP
    p_leaf = _get_params(leaf, _XCP)
  except Exception:
    p_leaf = p_stub
  # Merge variant parameters into leaf params to honor variant coefficients
  p_eff = _merge_p_objects(p_leaf, p_stub)
  p_eff = _hydrate_params_for_module(p_eff)
  p_eff = _promote_param_arrays(p_eff)

  def E(r0, r1, s0, s1, s2, l0, l1, t0, t1):
    val = mod_exc.pol(p_eff, (r0, r1), (s0, s1, s2), (l0, l1), (t0, t1))
    # Hybrid exchange-only scaling for semilocal part
    if name.startswith('hyb_') and ('_x_' in name) and ('_xc_' not in name) and ('erf' not in name) and ('erfc' not in name):
      try:
        val = (1.0 - float(getattr(p_stub, 'cam_alpha', 0.0))) * val
      except Exception:
        pass
    return val
  return E


def _ad__exc_unpol_callable(name: str, p_stub):
  """Return a JAX-friendly callable E(r,s,l,t) for EXC energy (unpolarized)."""
  from jxc import get_params as _get_params, XC_UNPOLARIZED as _XCU
  from ..libxc_aliases import LIBXC_ALIAS_REMAP
  p = _get_params(name, _XCU)
  if hasattr(p, 'func_aux') and p.func_aux:
    child_calls = []
    for cp in p.func_aux:
      cname = _ad__get_child_name(cp)
      if not cname:
        continue
      cname = LIBXC_ALIAS_REMAP.get(cname, cname)
      child_stub = cp if cp is not None else p_stub
      child_calls.append(_ad__exc_unpol_callable(cname, child_stub))

    def E_u(r, s, l, t):
      total = 0.0
      for coef, cE in zip(p.mix_coef, child_calls):
        total = total + coef * cE(r, s, l, t)
      bname = getattr(p, 'maple_name', '')
      if bname:
        base_in_aux = any(
          _ad__get_child_name(cp) == bname or getattr(cp, 'maple_name', '') == bname
          for cp in p.func_aux
        )
        if not base_in_aux:
          try:
            bcall = _ad__exc_unpol_callable(LIBXC_ALIAS_REMAP.get(bname, bname), p_stub)
            total = total + bcall(r, s, l, t)
          except BaseException:
            pass
      return total
    return E_u

  leaf = getattr(p, "maple_name", "") or name
  try:
    mod_exc = _load_exc_module_for_ad(leaf)
  except ImportError:
    alias_leaf = LIBXC_ALIAS_REMAP.get(leaf, leaf)
    if alias_leaf == leaf:
      raise
    leaf = alias_leaf
    mod_exc = _load_exc_module_for_ad(leaf)
  _ensure_special_functions(mod_exc)
  try:
    from jxc import get_params as _get_params, XC_UNPOLARIZED as _XCU
    p_leaf = _get_params(leaf, _XCU)
  except Exception:
    p_leaf = p_stub
  p_eff = _merge_p_objects(p_leaf, p_stub)
  p_eff = _hydrate_params_for_module(p_eff)
  p_eff = _promote_param_arrays(p_eff)
  def E_u(r, s, l, t):
    val = mod_exc.unpol(p_eff, r, s, l, t)
    if name.startswith('hyb_') and ('_x_' in name) and ('_xc_' not in name) and ('erf' not in name) and ('erfc' not in name):
      try:
        val = (1.0 - float(getattr(p_stub, 'cam_alpha', 0.0))) * val
      except Exception:
        pass
    return val
  return E_u


@functools.lru_cache(maxsize=None)
def _load_module(name: str) -> types.ModuleType:
  # Prefer pre-generated combined module if present under jxc.functionals and it
  # already exposes Maple derivatives.
  try:
    mod = importlib.import_module(f"jxc.functionals.{name}")
    if hasattr(mod, "pol_vxc") and hasattr(mod, "unpol_vxc"):
      return mod
  except Exception:
    mod = None
  # If direct import failed, try alias-based module import before attempting
  # any dynamic Maple generation.
  if mod is None:
    try:
      from ..libxc_aliases import LIBXC_ALIAS_REMAP as _ALIAS
    except Exception:
      _ALIAS = {}
    alias = _ALIAS.get(name, name)
    if alias != name:
      try:
        mod = importlib.import_module(f"jxc.functionals.{alias}")
        if hasattr(mod, "pol_vxc") and hasattr(mod, "unpol_vxc"):
          return mod
      except Exception:
        mod = None
    # Try reverse alias map (canonical->variant) in case only the variant was generated
    if not mod and _ALIAS:
      try:
        _REV = {v: k for k, v in _ALIAS.items()}
        if name in _REV:
          mod = importlib.import_module(f"jxc.functionals.{_REV[name]}")
          if hasattr(mod, "pol_vxc") and hasattr(mod, "unpol_vxc"):
            return mod
      except Exception:
        mod = None
  if mod is not None:
    # Module was imported but may be missing pol_vxc/unpol_vxc
    if not hasattr(mod, "pol_vxc") or not hasattr(mod, "unpol_vxc"):
      raise ImportError(
        f"Module jxc.functionals.{name} exists but is missing pre-generated VXC functions. "
        f"Please regenerate VXC using: convert_maple_targeted.py vxc --functionals {name} --force"
      )
    return mod

  # No module found at all
  raise ImportError(
    f"No pre-generated module found for {name}. "
    f"Please generate VXC using: convert_maple_targeted.py vxc --functionals {name} --force"
  )


def _module_name_for_params(fallback: str, p_obj) -> str:
  if p_obj is not None:
    maple = getattr(p_obj, "maple_name", "") or ""
    if maple:
      return maple
  return fallback


def _eval_composite_unpolarized(
  p, rho, sigma=None, lapl=None, tau=None, use_jax: bool = False
) -> Dict[str, jnp.ndarray]:
  """Evaluate composite functional VXC for unpolarized case.

  Linear combination of component VXCs using mix_coef weights.
  """
  from jxc import get_params as _get_params, XC_UNPOLARIZED as _XCU

  # Special case: DEORBITALIZE pattern
  if p.maple_name == "DEORBITALIZE":
    # TODO: Full implementation requires molecular orbitals
    # For now, evaluate p0 and p1 separately
    p0, p1 = (p.func_aux[0], p.func_aux[1])
    # Recursively evaluate (p1 might also be composite)
    result = _eval_single_unpolarized(p0.name, rho, sigma, lapl, tau, use_jax)
    return result

  # Build component VXCs using child parameter objects (respect ext params)
  children_results = []
  for child_p in p.func_aux:
    child_name = getattr(child_p, 'name', getattr(child_p, 'maple_name', ''))
    if not child_name:
      continue
    # Apply LibXC alias if needed
    from ..libxc_aliases import LIBXC_ALIAS_REMAP
    child_name = LIBXC_ALIAS_REMAP.get(child_name, child_name)
    # Evaluate leaf with the child's parameter object to preserve ext params (e.g., SR/LR split)
    try:
      child_res = _eval_leaf_unpol_with_p(child_name, child_p, rho, sigma, lapl, tau)
    except Exception:
      # Fallback to name-based evaluation if direct call fails
      child_res = _eval_single_unpolarized(child_name, rho, sigma, lapl, tau, use_jax)
    # Hybrid exchange-only scaling for semilocal exchange parts
    parent_name = str(getattr(p, 'name', ''))
    if (
      parent_name.startswith('hyb_') and ('_x_' in parent_name) and ('_xc_' not in parent_name)
      and ('_x_' in child_name) and ('_xc_' not in child_name)
      and ('erf' not in parent_name) and ('erfc' not in parent_name)
    ):
      try:
        scale = (1.0 - float(getattr(p, 'cam_alpha', 0.0)))
        child_res = {k: (v * scale) for k, v in child_res.items()}
      except Exception:
        pass
    children_results.append(child_res)

  # Linear combination using mix_coef
  if not children_results:
    raise ValueError(f"Composite functional {p.name} has no valid components")

  # Collect all keys from all children (different components may have different keys)
  all_keys = set()
  for child_res in children_results:
    all_keys.update(child_res.keys())

  # Initialize result with zeros matching first child's structure (for shape/dtype)
  result: Dict[str, jnp.ndarray] = {}
  first_child = children_results[0]
  for key in all_keys:
    # Use first child that has this key to determine shape/dtype
    for child_res in children_results:
      if key in child_res:
        result[key] = jnp.zeros_like(child_res[key])
        break

  # Sum weighted components
  for coef, child_res in zip(p.mix_coef, children_results):
    for key in all_keys:
      if key in child_res:
        result[key] = result[key] + coef * child_res[key]

  # Special case: hyb_mgga_xc_b0kcis uses (1 - alpha) * Ex + 2 * Ec
  if p.name == 'hyb_mgga_xc_b0kcis' and len(children_results) >= 2:
    alpha = getattr(p, 'cam_alpha', 0.25)
    for key in result.keys():
      result[key] = (1.0 - alpha) * children_results[0][key] + 2.0 * children_results[1][key]

  # For some LibXC hybrids, base functional is added separately
  # (similar to EXC composite.py logic)
  EXCLUDE_BASE_ADDITION = {
    'hyb_gga_xc_lb07',
    'hyb_gga_xc_apbe0',
  }
  if p.maple_name and (p.name not in EXCLUDE_BASE_ADDITION):
    # Check if base is already in func_aux
    base_in_aux = any(
      getattr(cp, 'name', '') == p.maple_name or getattr(cp, 'maple_name', '') == p.maple_name
      for cp in p.func_aux
    )
    if not base_in_aux:
      try:
        base_res = _eval_single_unpolarized(p.maple_name, rho, sigma, lapl, tau, use_jax)
        for key in result.keys():
          if key in base_res:
            result[key] = result[key] + base_res[key]
      except Exception:
        pass

  return result


def _eval_composite_polarized(
  p, rho: Tuple, sigma: Optional[Tuple] = None, lapl: Optional[Tuple] = None, tau: Optional[Tuple] = None, use_jax: bool = False
) -> Dict[str, jnp.ndarray]:
  """Evaluate composite functional VXC for polarized case.

  Linear combination of component VXCs using mix_coef weights.
  """
  from jxc import get_params as _get_params, XC_POLARIZED as _XCP

  # Special case: DEORBITALIZE pattern
  if p.maple_name == "DEORBITALIZE":
    p0, p1 = (p.func_aux[0], p.func_aux[1])
    result = _eval_single_polarized(p0.name, rho, sigma, lapl, tau, use_jax)
    return result

  # Build component VXCs using child parameter objects (respect ext params)
  children_results = []
  for child_p in p.func_aux:
    child_name = getattr(child_p, 'name', getattr(child_p, 'maple_name', ''))
    if not child_name:
      continue
    # Apply LibXC alias if needed
    from ..libxc_aliases import LIBXC_ALIAS_REMAP
    child_name = LIBXC_ALIAS_REMAP.get(child_name, child_name)
    try:
      child_res = _eval_leaf_pol_with_p(child_name, child_p, rho, sigma, lapl, tau)
    except Exception:
      child_res = _eval_single_polarized(child_name, rho, sigma, lapl, tau, use_jax)
    parent_name = str(getattr(p, 'name', ''))
    if (
      parent_name.startswith('hyb_') and ('_x_' in parent_name) and ('_xc_' not in parent_name)
      and ('_x_' in child_name) and ('_xc_' not in child_name)
      and ('erf' not in parent_name) and ('erfc' not in parent_name)
    ):
      try:
        scale = (1.0 - float(getattr(p, 'cam_alpha', 0.0)))
        child_res = {k: (v * scale) for k, v in child_res.items()}
      except Exception:
        pass
    children_results.append(child_res)

  if not children_results:
    raise ValueError(f"Composite functional {p.name} has no valid components")

  # Collect all keys from all children (different components may have different keys)
  all_keys = set()
  for child_res in children_results:
    all_keys.update(child_res.keys())

  # Initialize result with zeros matching first child's structure (for shape/dtype)
  result: Dict[str, jnp.ndarray] = {}
  for key in all_keys:
    # Use first child that has this key to determine shape/dtype
    for child_res in children_results:
      if key in child_res:
        result[key] = jnp.zeros_like(child_res[key])
        break

  # Sum weighted components
  for coef, child_res in zip(p.mix_coef, children_results):
    for key in all_keys:
      if key in child_res:
        result[key] = result[key] + coef * child_res[key]

  # Special case: hyb_mgga_xc_b0kcis
  if p.name == 'hyb_mgga_xc_b0kcis' and len(children_results) >= 2:
    alpha = getattr(p, 'cam_alpha', 0.25)
    for key in result.keys():
      result[key] = (1.0 - alpha) * children_results[0][key] + 2.0 * children_results[1][key]

  # Add base functional if needed
  EXCLUDE_BASE_ADDITION = {
    'hyb_gga_xc_lb07',
    'hyb_gga_xc_apbe0',
  }
  if p.maple_name and (p.name not in EXCLUDE_BASE_ADDITION):
    base_in_aux = any(
      getattr(cp, 'name', '') == p.maple_name or getattr(cp, 'maple_name', '') == p.maple_name
      for cp in p.func_aux
    )
    if not base_in_aux:
      try:
        base_res = _eval_single_polarized(p.maple_name, rho, sigma, lapl, tau, use_jax)
        for key in result.keys():
          if key in base_res:
            result[key] = result[key] + base_res[key]
      except Exception:
        pass

  return result


def _eval_single_unpolarized(
  name: str, rho, sigma=None, lapl=None, tau=None, use_jax: bool = False
) -> Dict[str, jnp.ndarray]:
  """Evaluate a single (non-composite) functional's unpolarized VXC."""
  p_stub = None
  try:
    from jxc import get_params as _get_params, XC_UNPOLARIZED as _XCU
    p_stub = _get_params(name, _XCU)
  except Exception:
    p_stub = None

  r = jnp.asarray(rho, dtype=jnp.float64)
  s = None if sigma is None else jnp.asarray(sigma, dtype=jnp.float64)
  l = None if lapl is None else jnp.asarray(lapl, dtype=jnp.float64)
  t = None if tau is None else jnp.asarray(tau, dtype=jnp.float64)

  if use_jax and _is_kinetic_functional(name):
    if p_stub is None:
      p_stub = types.SimpleNamespace(
        name=name,
        params=types.SimpleNamespace(),
        dens_threshold=np.float64(1e-30),
        zeta_threshold=np.float64(np.finfo(np.float64).eps),
      )
    return _ad_eval_unpolarized(name, p_stub, r, s, l, t)

  if p_stub is not None and hasattr(p_stub, 'func_aux') and p_stub.func_aux:
    return _eval_composite_unpolarized(p_stub, rho, sigma, lapl, tau, use_jax)

  if p_stub is None:
    p_stub = types.SimpleNamespace(
      name=name,
      params=types.SimpleNamespace(),
      dens_threshold=np.float64(1e-30),
      zeta_threshold=np.float64(np.finfo(np.float64).eps),
    )

  module_name = _module_name_for_params(name, p_stub)
  mod = _load_module(module_name)

  fam = _family_from_name(name)
  if fam is None:
    return {}
  rho_pair = (r / 2, r / 2)
  sigma_tuple = None
  lapl_tuple = None
  tau_tuple = None if t is None else (t / 2, t / 2)
  if fam == "gga":
    assert s is not None, "sigma required for GGA"
    sigma_tuple = (s / 4, s / 4, s / 4)
  elif fam == "mgga":
    assert s is not None and l is not None, "sigma and lapl required for MGGA"
    sigma_tuple = (s / 4, s / 4, s / 4)
    lapl_tuple = (l / 2, l / 2)
  elif fam != "lda":
    # Unsupported family fallback: differentiate energy directly
    if use_jax:
      return _ad_eval_unpolarized(name, p_stub, r, s, l, t)
    try:
      direct_res = dict(mod.unpol_vxc(_hydrate_params_for_module(p_stub), r, s, l, t))
      if direct_res:
        return direct_res
    except Exception:
        pass
    return {}

  if use_jax:
    pol_res = _ad_eval_polarized(
      name,
      p_stub,
      rho_pair,
      sigma_tuple,
      lapl_tuple,
      tau_tuple,
      scale_with_density=False,
    )
  else:
    if hasattr(mod, "unpol_vxc") and not use_jax:
      try:
        direct_res = dict(mod.unpol_vxc(_hydrate_params_for_module(p_stub), r, s, l, t))
        if direct_res:
          return direct_res
      except Exception:
        pass
    pol_res = _evaluate_pol_derivatives(
      mod,
      p_stub,
      rho_pair,
      sigma_tuple if sigma_tuple is not None else None,
      lapl_tuple if lapl_tuple is not None else None,
      tau_tuple if tau_tuple is not None else None,
    )

  out: Dict[str, jnp.ndarray] = {}
  if "vrho" in pol_res:
    vr = jnp.asarray(pol_res["vrho"], dtype=jnp.float64)
    out["vrho"] = 0.5 * (vr[..., 0] + vr[..., 1])
  if "vsigma" in pol_res:
    vs = jnp.asarray(pol_res["vsigma"], dtype=jnp.float64)
    out["vsigma"] = 0.25 * (vs[..., 0] + vs[..., 1] + vs[..., 2])
  if "vlapl" in pol_res:
    vl = jnp.asarray(pol_res["vlapl"], dtype=jnp.float64)
    out["vlapl"] = 0.5 * (vl[..., 0] + vl[..., 1])
  if "vtau" in pol_res:
    vt = jnp.asarray(pol_res["vtau"], dtype=jnp.float64)
    out["vtau"] = 0.5 * (vt[..., 0] + vt[..., 1])
  return out


def _eval_single_polarized(
  name: str, rho: Tuple, sigma: Optional[Tuple] = None, lapl: Optional[Tuple] = None, tau: Optional[Tuple] = None, use_jax: bool = False
) -> Dict[str, jnp.ndarray]:
  """Evaluate a single (non-composite) functional's polarized VXC."""
  p_stub = None
  try:
    from jxc import get_params as _get_params, XC_POLARIZED as _XCP
    p_stub = _get_params(name, _XCP)
  except Exception:
    p_stub = None

  r0 = jnp.asarray(rho[0], dtype=jnp.float64)
  r1 = jnp.asarray(rho[1], dtype=jnp.float64)
  s = None if sigma is None else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in sigma)
  l = None if lapl is None else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in lapl)
  t = None if tau is None else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in tau)

  if use_jax:
    if p_stub is None:
      p_stub = types.SimpleNamespace(
        name=name,
        params=types.SimpleNamespace(),
        dens_threshold=np.float64(1e-30),
        zeta_threshold=np.float64(np.finfo(np.float64).eps),
      )
    return _ad_eval_polarized(name, p_stub, (r0, r1), s, l, t)

  if p_stub is not None and hasattr(p_stub, 'func_aux') and p_stub.func_aux:
    return _eval_composite_polarized(p_stub, rho, sigma, lapl, tau, use_jax)

  if p_stub is None:
    p_stub = types.SimpleNamespace(
      name=name,
      params=types.SimpleNamespace(),
      dens_threshold=np.float64(1e-30),
      zeta_threshold=np.float64(np.finfo(np.float64).eps),
    )

  module_name = _module_name_for_params(name, p_stub)
  mod = _load_module(module_name)
  res = _evaluate_pol_derivatives(mod, p_stub, (r0, r1), s, l, t)
  return dict(res)


def eval_unpolarized_vxc(
  name: str, rho, sigma=None, lapl=None, tau=None, use_jax: bool = False
) -> Dict[str, jnp.ndarray]:
  """Evaluate unpolarized VXC.

  Uses chain-rule from polarized derivatives to avoid Maple's Python emitter
  issues on the unpolarized branch. For family f in {lda,gga,mgga} with mapping
  r -> (r/2, r/2), s -> (s/4, s/4, s/4), l -> (l/2, l/2), tau -> (tau/2, tau/2):
    vrho = 0.5 * (vrho0 + vrho1)
    vsigma = 0.25 * (vsigma0 + vsigma1 + vsigma2)  [gga, mgga]
    vlapl = 0.5 * (vlapl0 + vlapl1)                 [mgga]
    vtau  = 0.5 * (vtau0 + vtau1)                   [mgga]

  Supports composite functionals via linear combination of components.
  """
  # Delegate to unified single/composite evaluator
  return _eval_single_unpolarized(name, rho, sigma, lapl, tau, use_jax)


def eval_unpolarized_vxc_with_params(
  params, rho, sigma=None, lapl=None, tau=None, use_jax: bool = False
) -> Dict[str, jnp.ndarray]:
  """Evaluate unpolarized VXC using an explicit parameter object."""
  name = getattr(params, "name", "") or getattr(params, "maple_name", "") or getattr(params, "libxc_name", "")
  if use_jax:
    r = jnp.asarray(rho, dtype=jnp.float64)
    s = None if sigma is None else jnp.asarray(sigma, dtype=jnp.float64)
    l = None if lapl is None else jnp.asarray(lapl, dtype=jnp.float64)
    t = None if tau is None else jnp.asarray(tau, dtype=jnp.float64)
    hydrated = _hydrate_params_for_module(params)
    base_name = name or getattr(hydrated, "name", "")
    return _ad_eval_unpolarized(base_name or name, hydrated, r, s, l, t)
  if hasattr(params, "func_aux") and params.func_aux:
    return _eval_composite_unpolarized(params, rho, sigma, lapl, tau, use_jax)
  target = name or getattr(params, "maple_name", "") or getattr(params, "libxc_name", name)
  return _eval_leaf_unpol_with_p(target or name, params, rho, sigma, lapl, tau)


def eval_polarized_vxc(
  name: str,
  rho: Tuple,
  sigma: Optional[Tuple] = None,
  lapl: Optional[Tuple] = None,
  tau: Optional[Tuple] = None,
  use_jax: bool = False,
) -> Dict[str, jnp.ndarray]:
  """Evaluate polarized VXC.

  Supports composite functionals via linear combination of components.
  """
  # Delegate to unified single/composite evaluator
  return _eval_single_polarized(name, rho, sigma, lapl, tau, use_jax)


def eval_polarized_vxc_with_params(
  params,
  rho: Tuple,
  sigma: Optional[Tuple] = None,
  lapl: Optional[Tuple] = None,
  tau: Optional[Tuple] = None,
  use_jax: bool = False,
) -> Dict[str, jnp.ndarray]:
  """Evaluate polarized VXC using an explicit parameter object."""
  name = getattr(params, "name", "") or getattr(params, "maple_name", "") or getattr(params, "libxc_name", "")
  if use_jax:
    r0 = jnp.asarray(rho[0], dtype=jnp.float64)
    r1 = jnp.asarray(rho[1], dtype=jnp.float64)
    s = None if sigma is None else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in sigma)
    l = None if lapl is None else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in lapl)
    t = None if tau is None else tuple(jnp.asarray(comp, dtype=jnp.float64) for comp in tau)
    hydrated = _hydrate_params_for_module(params)
    base_name = name or getattr(hydrated, "name", "")
    return _ad_eval_polarized(base_name or name, hydrated, (r0, r1), s, l, t)
  if hasattr(params, "func_aux") and params.func_aux:
    return _eval_composite_polarized(params, rho, sigma, lapl, tau, use_jax)
  target = name or getattr(params, "maple_name", "") or getattr(params, "libxc_name", name)
  return _eval_leaf_pol_with_p(target or name, params, rho, sigma, lapl, tau)


def ad_eval_unpolarized_vxc(
  name: str, order: str, rho, sigma=None, lapl=None, tau=None
) -> Dict[str, jnp.ndarray]:
  try:
    from jxc import get_params as _get_params, XC_UNPOLARIZED as _XCU
    p_stub = _get_params(name, _XCU)
  except Exception:
    p_stub = types.SimpleNamespace(
      name=name,
      params=types.SimpleNamespace(),
      dens_threshold=np.float64(1e-30),
      zeta_threshold=np.float64(np.finfo(np.float64).eps),
    )

  r_arr = jnp.asarray(rho, dtype=jnp.float64)
  s_arr = None if sigma is None else jnp.asarray(sigma, dtype=jnp.float64)
  l_arr = None if lapl is None else jnp.asarray(lapl, dtype=jnp.float64)
  t_arr = None if tau is None else jnp.asarray(tau, dtype=jnp.float64)

  order = order.lower()
  if order == "vxc":
    return _ad_eval_unpolarized(name, p_stub, r_arr, s_arr, l_arr, t_arr)
  if order == "fxc":
    return _ad_eval_unpolarized_fxc(name, p_stub, r_arr, s_arr, l_arr, t_arr)
  if order == "kxc":
    return _ad_eval_unpolarized_kxc(name, p_stub, r_arr, s_arr, l_arr, t_arr)
  if order == "lxc":
    return _ad_eval_unpolarized_lxc(name, p_stub, r_arr, s_arr, l_arr, t_arr)
  raise ValueError(f"Unsupported AD derivative order: {order}")


def ad_eval_polarized_vxc(
  name: str, order: str, rho: Tuple, sigma: Optional[Tuple] = None, lapl: Optional[Tuple] = None, tau: Optional[Tuple] = None
) -> Dict[str, jnp.ndarray]:
  try:
    from jxc import get_params as _get_params, XC_POLARIZED as _XCP
    p_stub = _get_params(name, _XCP)
  except Exception:
    p_stub = types.SimpleNamespace(
      name=name,
      params=types.SimpleNamespace(),
      dens_threshold=np.float64(1e-30),
      zeta_threshold=np.float64(np.finfo(np.float64).eps),
    )

  r0 = jnp.asarray(rho[0], dtype=jnp.float64)
  r1 = jnp.asarray(rho[1], dtype=jnp.float64)
  sigma_tuple = None
  if sigma is not None:
    sigma_tuple = tuple(
      jnp.asarray(comp, dtype=jnp.float64) if comp is not None else None
      for comp in sigma
    )
  lapl_tuple = None
  if lapl is not None:
    lapl_tuple = tuple(jnp.asarray(comp, dtype=jnp.float64) if comp is not None else None for comp in lapl)
  tau_tuple = None
  if tau is not None:
    tau_tuple = tuple(jnp.asarray(comp, dtype=jnp.float64) if comp is not None else None for comp in tau)

  order = order.lower()
  if order == "vxc":
    return _ad_eval_polarized(name, p_stub, (r0, r1), sigma_tuple, lapl_tuple, tau_tuple)
  if order == "fxc":
    return _ad_eval_polarized_fxc(name, p_stub, (r0, r1), sigma_tuple, lapl_tuple, tau_tuple)
  if order == "kxc":
    return _ad_eval_polarized_kxc(name, p_stub, (r0, r1), sigma_tuple, lapl_tuple, tau_tuple)
  if order == "lxc":
    return _ad_eval_polarized_lxc(name, p_stub, (r0, r1), sigma_tuple, lapl_tuple, tau_tuple)
  raise ValueError(f"Unsupported AD derivative order: {order}")

# Backwards-compatibility aliases (deprecated).
eval_unpolarized = eval_unpolarized_vxc
eval_polarized = eval_polarized_vxc
ad_eval_unpolarized = ad_eval_unpolarized_vxc
ad_eval_polarized = ad_eval_polarized_vxc


def _ad_eval_polarized(name: str, p_stub, rho: Tuple, sigma: Optional[Tuple], lapl: Optional[Tuple], tau: Optional[Tuple], *, scale_with_density: bool = True) -> Dict[str, jnp.ndarray]:
  """Evaluate polarized VXC via AD. Expects scalar inputs; use jax.vmap for batching."""
  E = _ad__exc_pol_callable(name, p_stub)
  fam = _family_from_name(name) or "gga"
  r0, r1 = rho
  energy_fn = _build_polarized_energy_fn(name, E, scale_with_density=scale_with_density)
  return _ad_eval_polarized_point(energy_fn, fam, r0, r1, sigma, lapl, tau)


def _ad_eval_polarized_point(energy_fn, fam: str, r0, r1, sigma, lapl, tau) -> Dict[str, jnp.ndarray]:
  s0, s1, s2 = sigma or (None, None, None)
  l0, l1 = lapl or (None, None)
  t0, t1 = tau or (None, None)

  def _as_array(val):
    if val is None:
      return jnp.asarray(0.0, dtype=jnp.float64)
    return jnp.asarray(val, dtype=jnp.float64)

  s0a, s1a, s2a = _as_array(s0), _as_array(s1), _as_array(s2)
  l0a, l1a = _as_array(l0), _as_array(l1)
  t0a, t1a = _as_array(t0), _as_array(t1)

  grads_r = jax.grad(energy_fn, argnums=(0, 1))(r0, r1, s0a, s1a, s2a, l0a, l1a, t0a, t1a)
  out: Dict[str, jnp.ndarray] = {"vrho": jnp.stack(grads_r, axis=-1)}

  if fam in ("gga", "mgga"):
    grads_sigma = jax.grad(energy_fn, argnums=(2, 3, 4))(r0, r1, s0a, s1a, s2a, l0a, l1a, t0a, t1a)
    out["vsigma"] = jnp.stack(grads_sigma, axis=-1)

  if fam == "mgga":
    grads_lapl = jax.grad(energy_fn, argnums=(5, 6))(r0, r1, s0a, s1a, s2a, l0a, l1a, t0a, t1a)
    out["vlapl"] = jnp.stack(grads_lapl, axis=-1)
    grads_tau = jax.grad(energy_fn, argnums=(7, 8))(r0, r1, s0a, s1a, s2a, l0a, l1a, t0a, t1a)
    out["vtau"] = jnp.stack(grads_tau, axis=-1)

  return out


def _ad_eval_unpolarized(name: str, p_stub, r, s, l, t) -> Dict[str, jnp.ndarray]:
  """Evaluate unpolarized VXC via AD. Expects scalar inputs; use jax.vmap for batching."""
  E_u = _ad__exc_unpol_callable(name, p_stub)
  fam = _family_from_name(name) or "gga"
  energy_fn = _build_unpolarized_energy_fn(name, E_u)
  return _ad_eval_unpol_point(energy_fn, fam, r, s, l, t)


def _ad_eval_unpol_point(energy_fn, fam: str, r, s, l, t) -> Dict[str, jnp.ndarray]:
  out: Dict[str, jnp.ndarray] = {}
  s_val = jnp.asarray(0.0 if s is None else s, dtype=jnp.float64)
  l_val = jnp.asarray(0.0 if l is None else l, dtype=jnp.float64)
  t_val = jnp.asarray(0.0 if t is None else t, dtype=jnp.float64)

  vr = jax.grad(energy_fn, argnums=0)(r, s_val, l_val, t_val)
  out["vrho"] = vr

  if fam in ("gga", "mgga"):
    out["vsigma"] = jax.grad(energy_fn, argnums=1)(r, s_val, l_val, t_val)
  if fam == "mgga":
    out["vlapl"] = jax.grad(energy_fn, argnums=2)(r, s_val, l_val, t_val)
    out["vtau"] = jax.grad(energy_fn, argnums=3)(r, s_val, l_val, t_val)
  return out


def _ad_eval_unpol_fxc_point(energy_fn, has_sigma: bool, has_lapl: bool, has_tau: bool, r, s, l, t) -> Dict[str, jnp.ndarray]:
  s_val = jnp.asarray(0.0 if s is None else s, dtype=jnp.float64)
  l_val = jnp.asarray(0.0 if l is None else l, dtype=jnp.float64)
  t_val = jnp.asarray(0.0 if t is None else t, dtype=jnp.float64)
  hess = jax.hessian(energy_fn, argnums=(0, 1, 2, 3))(r, s_val, l_val, t_val)

  res: Dict[str, jnp.ndarray] = {}
  res["v2rho2"] = hess[0][0]
  if has_sigma:
    res["v2rhosigma"] = hess[0][1]
    res["v2sigma2"] = hess[1][1]
  if has_lapl:
    res["v2rholapl"] = hess[0][2]
    if has_sigma:
      res["v2sigmalapl"] = hess[1][2]
    res["v2lapl2"] = hess[2][2]
  if has_tau:
    res["v2rhotau"] = hess[0][3]
    if has_sigma:
      res["v2sigmatau"] = hess[1][3]
    if has_lapl:
      res["v2lapltau"] = hess[2][3]
    res["v2tau2"] = hess[3][3]
  return res


def _ad_eval_pol_fxc_point(energy_fn, has_sigma: bool, has_lapl: bool, has_tau: bool, args: Tuple) -> Dict[str, jnp.ndarray]:
  hess = jax.hessian(energy_fn, argnums=tuple(range(9)))(*args)
  res: Dict[str, jnp.ndarray] = {}

  def _gather(indices_a, indices_b):
    rows = []
    for i in indices_a:
      row = []
      for j in indices_b:
        row.append(hess[i][j])
      rows.append(jnp.stack(row, axis=-1))
    return jnp.stack(rows, axis=-2)

  rho_idx = (0, 1)
  res["v2rho2"] = _gather(rho_idx, rho_idx)

  if has_sigma:
    sigma_idx = (2, 3, 4)
    res["v2rhosigma"] = _gather(rho_idx, sigma_idx)
    res["v2sigma2"] = _gather(sigma_idx, sigma_idx)

  if has_lapl:
    lapl_idx = (5, 6)
    res["v2rholapl"] = _gather(rho_idx, lapl_idx)
    if has_sigma:
      res["v2sigmalapl"] = _gather((2, 3, 4), lapl_idx)
    res["v2lapl2"] = _gather(lapl_idx, lapl_idx)

  if has_tau:
    tau_idx = (7, 8)
    res["v2rhotau"] = _gather(rho_idx, tau_idx)
    if has_sigma:
      res["v2sigmatau"] = _gather((2, 3, 4), tau_idx)
    if has_lapl:
      res["v2lapltau"] = _gather((5, 6), tau_idx)
    res["v2tau2"] = _gather(tau_idx, tau_idx)

  return res


def _flatten_polarized_fxc(res: Dict[str, jnp.ndarray]) -> Dict[str, jnp.ndarray]:
  out = dict(res)

  def _flatten_sym(arr):
    return jnp.stack(
      (
        arr[..., 0, 0],
        arr[..., 0, 1],
        arr[..., 1, 1],
      ),
      axis=-1,
    )

  def _flatten_rect(arr, left_dim, right_dim):
    order = []
    for i in range(left_dim):
      for j in range(right_dim):
        order.append(arr[..., i, j])
    return jnp.stack(order, axis=-1)

  if "v2rho2" in out:
    out["v2rho2"] = _flatten_sym(out["v2rho2"])
  if "v2rhosigma" in out:
    out["v2rhosigma"] = _flatten_rect(out["v2rhosigma"], 2, 3)
  if "v2sigma2" in out:
    arr = out["v2sigma2"]
    out["v2sigma2"] = jnp.stack(
      (
        arr[..., 0, 0],
        arr[..., 0, 1],
        arr[..., 0, 2],
        arr[..., 1, 1],
        arr[..., 1, 2],
        arr[..., 2, 2],
      ),
      axis=-1,
    )
  if "v2rholapl" in out:
    out["v2rholapl"] = _flatten_rect(out["v2rholapl"], 2, 2)
  if "v2sigmalapl" in out:
    out["v2sigmalapl"] = _flatten_rect(out["v2sigmalapl"], 3, 2)
  if "v2lapl2" in out:
    out["v2lapl2"] = _flatten_sym(out["v2lapl2"])
  if "v2rhotau" in out:
    out["v2rhotau"] = _flatten_rect(out["v2rhotau"], 2, 2)
  if "v2sigmatau" in out:
    out["v2sigmatau"] = _flatten_rect(out["v2sigmatau"], 3, 2)
  if "v2lapltau" in out:
    out["v2lapltau"] = _flatten_rect(out["v2lapltau"], 2, 2)
  if "v2tau2" in out:
    out["v2tau2"] = _flatten_sym(out["v2tau2"])
  return out


def _ad_eval_unpolarized_fxc(name: str, p_stub, r, s, l, t) -> Dict[str, jnp.ndarray]:
  """Evaluate unpolarized FXC via AD. Expects scalar inputs; use jax.vmap for batching."""
  E_u = _ad__exc_unpol_callable(name, p_stub)
  fam = _family_from_name(name) or "gga"
  has_sigma = fam in ("gga", "mgga") and s is not None
  has_lapl = fam == "mgga" and l is not None
  has_tau = fam == "mgga" and t is not None
  energy_fn = _build_unpolarized_energy_fn(name, E_u)
  res = _ad_eval_unpol_fxc_point(
    energy_fn,
    has_sigma,
    has_lapl,
    has_tau,
    jnp.asarray(r, dtype=jnp.float64),
    None if s is None else jnp.asarray(s, dtype=jnp.float64),
    None if l is None else jnp.asarray(l, dtype=jnp.float64),
    None if t is None else jnp.asarray(t, dtype=jnp.float64),
  )
  return {k: jnp.asarray(v, dtype=jnp.float64) for k, v in res.items()}


def _ad_eval_polarized_fxc(name: str, p_stub, rho: Tuple, sigma: Optional[Tuple], lapl: Optional[Tuple], tau: Optional[Tuple]) -> Dict[str, jnp.ndarray]:
  """Evaluate polarized FXC via AD. Expects scalar inputs; use jax.vmap for batching."""
  E = _ad__exc_pol_callable(name, p_stub)
  r0, r1 = rho
  r0a = jnp.asarray(r0, dtype=jnp.float64)
  r1a = jnp.asarray(r1, dtype=jnp.float64)
  sigma_raw = sigma or (None, None, None)
  lapl_raw = lapl or (None, None)
  tau_raw = tau or (None, None)

  def _normalize(comp):
    if comp is None:
      return jnp.asarray(0.0, dtype=jnp.float64)
    return jnp.asarray(comp, dtype=jnp.float64)

  has_sigma = any(comp is not None for comp in sigma_raw)
  has_lapl = any(comp is not None for comp in lapl_raw)
  has_tau = any(comp is not None for comp in tau_raw)

  energy_fn = _build_polarized_energy_fn(name, E)

  args = (
    r0a,
    r1a,
    _normalize(sigma_raw[0]),
    _normalize(sigma_raw[1]),
    _normalize(sigma_raw[2]),
    _normalize(lapl_raw[0]),
    _normalize(lapl_raw[1]),
    _normalize(tau_raw[0]),
    _normalize(tau_raw[1]),
  )
  res = _ad_eval_pol_fxc_point(energy_fn, has_sigma, has_lapl, has_tau, args)
  res = _flatten_polarized_fxc(res)
  return {k: jnp.asarray(v, dtype=jnp.float64) for k, v in res.items()}


def _scalar_density_derivative(fn, order: int, rho: jnp.ndarray) -> jnp.ndarray:
  deriv_fn = fn
  for _ in range(order):
    deriv_fn = jax.grad(deriv_fn)
  return deriv_fn(rho)


def _ad_eval_unpolarized_density_order(
  name: str,
  p_stub,
  r,
  s,
  l,
  t,
  order: int,
  key: str,
) -> Dict[str, jnp.ndarray]:
  """Evaluate unpolarized KXC/LXC via AD. Expects scalar inputs; use jax.vmap for batching."""
  E_u = _ad__exc_unpol_callable(name, p_stub)
  energy_fn = _build_unpolarized_energy_fn(name, E_u)

  def _as_scalar(value):
    if value is None:
      return jnp.asarray(0.0, dtype=jnp.float64)
    return jnp.asarray(value, dtype=jnp.float64)

  r_arr = jnp.asarray(r, dtype=jnp.float64)
  sigma_val = _as_scalar(s)
  lapl_val = _as_scalar(l)
  tau_val = _as_scalar(t)

  def fn(rho_val):
    return energy_fn(rho_val, sigma_val, lapl_val, tau_val)

  value = _scalar_density_derivative(fn, order, r_arr)
  return {key: jnp.asarray(value, dtype=jnp.float64)}


def _flatten_spin_tensor(tensor: jnp.ndarray, order: int) -> jnp.ndarray:
  if order == 3:
    combos = (
      (0, 0, 0),
      (0, 0, 1),
      (0, 1, 1),
      (1, 1, 1),
    )
  elif order == 4:
    combos = (
      (0, 0, 0, 0),
      (0, 0, 0, 1),
      (0, 0, 1, 1),
      (0, 1, 1, 1),
      (1, 1, 1, 1),
    )
  else:
    raise ValueError(f"Unsupported spin tensor order: {order}")
  values = [tensor[idx] for idx in combos]
  return jnp.stack(values, axis=-1)


def _spin_density_derivative(fn, order: int, rho_vec: jnp.ndarray) -> jnp.ndarray:
  grad_fn = jax.grad(fn)
  tensor_fn = grad_fn
  for _ in range(order - 1):
    tensor_fn = jax.jacfwd(tensor_fn)
  return tensor_fn(rho_vec)


def _ad_eval_polarized_density_order(
  name: str,
  p_stub,
  rho: Tuple,
  sigma: Optional[Tuple],
  lapl: Optional[Tuple],
  tau: Optional[Tuple],
  order: int,
  key: str,
) -> Dict[str, jnp.ndarray]:
  """Evaluate polarized KXC/LXC via AD. Expects scalar inputs; use jax.vmap for batching."""
  E = _ad__exc_pol_callable(name, p_stub)
  r0, r1 = rho
  r0a = jnp.asarray(r0, dtype=jnp.float64)
  r1a = jnp.asarray(r1, dtype=jnp.float64)

  sigma_raw = sigma or (None, None, None)
  lapl_raw = lapl or (None, None)
  tau_raw = tau or (None, None)

  def _normalize(comp):
    if comp is None:
      return jnp.asarray(0.0, dtype=jnp.float64)
    return jnp.asarray(comp, dtype=jnp.float64)

  energy_fn = _build_polarized_energy_fn(name, E)

  sig0 = _normalize(sigma_raw[0])
  sig1 = _normalize(sigma_raw[1])
  sig2 = _normalize(sigma_raw[2])
  lap0 = _normalize(lapl_raw[0])
  lap1 = _normalize(lapl_raw[1])
  tau0 = _normalize(tau_raw[0])
  tau1 = _normalize(tau_raw[1])

  def scalar_fn(r_vec):
    return energy_fn(r_vec[0], r_vec[1], sig0, sig1, sig2, lap0, lap1, tau0, tau1)

  tensor = _spin_density_derivative(scalar_fn, order, jnp.stack((r0a, r1a)))
  values = _flatten_spin_tensor(tensor, order)
  return {key: jnp.asarray(values, dtype=jnp.float64)}


def _ad_eval_unpolarized_kxc(name: str, p_stub, r, s, l, t) -> Dict[str, jnp.ndarray]:
  return _ad_eval_unpolarized_density_order(name, p_stub, r, s, l, t, order=3, key="v3rho3")


def _ad_eval_unpolarized_lxc(name: str, p_stub, r, s, l, t) -> Dict[str, jnp.ndarray]:
  return _ad_eval_unpolarized_density_order(name, p_stub, r, s, l, t, order=4, key="v4rho4")


def _ad_eval_polarized_kxc(name: str, p_stub, rho: Tuple, sigma: Optional[Tuple], lapl: Optional[Tuple], tau: Optional[Tuple]) -> Dict[str, jnp.ndarray]:
  return _ad_eval_polarized_density_order(name, p_stub, rho, sigma, lapl, tau, order=3, key="v3rho3")


def _ad_eval_polarized_lxc(name: str, p_stub, rho: Tuple, sigma: Optional[Tuple], lapl: Optional[Tuple], tau: Optional[Tuple]) -> Dict[str, jnp.ndarray]:
  return _ad_eval_polarized_density_order(name, p_stub, rho, sigma, lapl, tau, order=4, key="v4rho4")
  # If this functional aliases to a Maple-backed leaf, merge leaf params to supply missing fields
  try:
    from ..libxc_aliases import LIBXC_ALIAS_REMAP
    alias = LIBXC_ALIAS_REMAP.get(name, name)
    if alias != name:
      try:
        p_leaf = _get_params(alias, _XCU)
        p_stub = _merge_p_objects(p_leaf, p_stub)
      except Exception:
        pass
  except Exception:
    pass
  # Merge alias leaf params if available to supply missing fields
  try:
    from ..libxc_aliases import LIBXC_ALIAS_REMAP
    alias = LIBXC_ALIAS_REMAP.get(name, name)
    if alias != name:
      try:
        p_leaf = _get_params(alias, _XCP)
        p_stub = _merge_p_objects(p_leaf, p_stub)
      except Exception:
        pass
  except Exception:
    pass
