"""
Utilities for the functional implementations.
"""

import ctypes
import importlib
from collections import namedtuple
from functools import partial

import numpy as np

PARAM_ALIASES = {
  "gga_c_acgga": "gga_c_pbe",
  "gga_c_acggap": "gga_c_pbe",
  "gga_c_regtpss": "gga_c_pbe",
  "gga_c_sg4": "gga_c_zpbeint",
  "gga_k_mpbe": "gga_k_pbe4",
  "gga_k_pg": "gga_k_pg1",
  "gga_k_pw86": "gga_k_fr_pw86",
  "gga_k_tflw": "gga_k_tfvw",
  "gga_x_bkl": "gga_x_bkl1",
  "gga_x_bpccac": "gga_x_pbe",
  "gga_x_dk87": "gga_x_dk87_r1",
  "gga_x_ft97": "gga_x_ft97_b",
  "gga_x_hjs": "gga_x_hjs_b88",
  # "gga_x_htbs": "gga_x_rpbe",  # REMOVED: Different functionals with different params
  # "gga_x_ityh": "gga_x_b88",  # REMOVED: Different functionals with different params
  "gga_x_kt": "gga_x_kt1",
  "gga_x_lv_rpw86": "gga_x_pw86",
  "gga_x_q1d": "gga_x_pbe",
  "gga_x_q2d": "gga_x_pbe",
  "gga_x_s12": "gga_x_s12g",
  # "gga_x_sfat_pbe": "gga_x_pbe",  # REMOVED: Different functionals with different params
  "gga_x_vmt": "gga_x_vmt_pbe",
  "gga_x_vmt84": "gga_x_vmt84_pbe",
  "gga_xc_b97": "gga_xc_b97_d",
  "hyb_gga_x_cam_s12": "hyb_gga_x_cam_s12g",
  "hyb_mgga_xc_wb97mv": "hyb_mgga_xc_wb97m_v",
  "lda_c_epc18": "lda_c_epc18_1",
  "lda_x_rel": "lda_x",
  "lda_xc_1d_ehwlrg": "lda_xc_1d_ehwlrg_1",
  "mgga_c_b88": "gga_x_b86",
  "mgga_c_cc": "lda_c_pw",
  "mgga_c_ltapw": "mgga_c_hltapw",
  "mgga_c_m08": "mgga_c_m08_so",
  "mgga_c_pkzb": "gga_c_pbe",
  # Correlation variants must not alias to exchange counterparts; keep their own params
  # "mgga_c_r2scan": "mgga_x_r2scan",
  # "mgga_c_revscan": "mgga_x_revscan",
  # "mgga_c_rmggac": "mgga_x_scan",
  # "mgga_c_rppscan": "mgga_x_rppscan",
  # "mgga_c_rregtm": "mgga_x_scan",
  # "mgga_c_rscan": "mgga_x_rscan",
  # "mgga_c_scan": "mgga_x_scan",
  "mgga_k_csk": "mgga_k_csk1",
  "mgga_k_csk_loc": "mgga_k_csk_loc1",
  "mgga_k_lk": "mgga_k_l04",
  "mgga_k_pgslb": "mgga_k_pgsl025",
  "mgga_x_2d_prp10": "mgga_x_2d_prhg07_prp10",
  "mgga_x_gdme": "mgga_x_gdme_nv",
  "mgga_x_ktbm": "mgga_x_ktbm_0",
  "mgga_c_m06l": "mgga_c_m06_l",
  "mgga_x_m06l": "mgga_x_m06_l",
  "mgga_x_m11": "mgga_x_m11_l",
  "mgga_x_mbrxh_bg": "mgga_x_br89",
  "mgga_x_mn12": "mgga_x_mn12_l",
  "mgga_x_ms": "mgga_x_ms0",
  "mgga_x_msb": "mgga_x_msb86bl",
  "mgga_x_pbe_gx": "mgga_x_gx",
  "mgga_x_regtpss": "mgga_x_tpss",
  "mgga_xc_b97mv": "mgga_xc_b97m_v",
  "mgga_xc_b98": "lda_c_pw",
  "mgga_xc_cc06": "lda_c_pw",
  # Exchange functionals that need parameters from related functionals
  # Note: mgga_x_rppscan and mgga_x_rscan have their own distinct parameter structs
}

PARAM_ALIAS_BLACKLIST = set()

# Functionals that historically required LibXC fallbacks now have explicit
# Python implementations.  Keep the set for future use, but leave it empty so
# new additions fail loudly until they gain coverage.
NO_HELPER_FUNCTIONALS: set[str] = set()

_PC07_A = 1.784720
_PC07_B = 0.258304

_DEORBITALIZED_CONFIG = {
  "mgga_x_scanl": {"base": "mgga_x_scan", "number": 700, "module": "mgga_x_scanl"},
  "mgga_x_revscanl": {"base": "mgga_x_revscan", "number": 701, "module": "mgga_x_revscanl"},
  "mgga_c_scanl": {"base": "mgga_c_scan", "number": 702, "module": "mgga_c_scanl"},
  "mgga_c_scanl_rvv10": {
    "base": "mgga_c_scan",
    "number": 703,
    "module": "mgga_c_scanl",
    "nlc_b": 15.7,
    "nlc_C": 0.0093,
  },
  "mgga_c_scanl_vv10": {
    "base": "mgga_c_scan",
    "number": 704,
    "module": "mgga_c_scanl",
    "nlc_b": 14.0,
    "nlc_C": 0.0093,
  },
  "mgga_x_r2scanl": {"base": "mgga_x_r2scan", "number": 718, "module": "mgga_x_r2scanl"},
  "mgga_c_r2scanl": {"base": "mgga_c_r2scan", "number": 719, "module": "mgga_c_r2scanl"},
}

_M06_NUMBERS = {
  "mgga_c_m06_l": 233,
  "mgga_c_m06l": 233,
  "mgga_c_m06": 235,
  "mgga_c_m06_2x": 236,
  "mgga_c_m06_hf": 234,
  "mgga_c_m06_sx": 311,
  "mgga_c_revm06": 306,
  "mgga_c_revm06_l": 294,
}

_M06_FIELD_LAYOUT: tuple[tuple[str, int], ...] = (
  ("gamma_ss", 1),
  ("gamma_ab", 1),
  ("alpha_ss", 1),
  ("alpha_ab", 1),
  ("css", 5),
  ("cab", 5),
  ("dss", 6),
  ("dab", 6),
  ("Fermi_D_cnst", 1),
)

_M06_DEFAULT_META = {
  "cam_omega": 0.0,
  "cam_alpha": 0.0,
  "cam_beta": 0.0,
  "nlc_b": 0.0,
  "nlc_C": 0.0,
  "dens_threshold": 1e-15,
  "zeta_threshold": np.finfo(np.float64).eps,
  "sigma_threshold": 1e-20,
  "tau_threshold": 1e-20,
  "maple_name": "mgga_c_m06l",
}

_M06_PARAM_SETS = {
  "mgga_c_m06_l": (
    0.06, 0.0031, 0.00515088, 0.00304966,
    5.349466e-01, 5.396620e-01, -3.161217e+01, 5.149592e+01, -2.919613e+01,
    6.042374e-01, 1.776783e+02, -2.513252e+02, 7.635173e+01, -1.255699e+01,
    4.650534e-01, 1.617589e-01, 1.833657e-01, 4.692100e-04, -4.990573e-03, 0.0,
    3.957626e-01, -5.614546e-01, 1.403963e-02, 9.831442e-04, -3.577176e-03, 0.0,
    1e-10,
  ),
  "mgga_c_m06": (
    0.06, 0.0031, 0.00515088, 0.00304966,
    5.094055e-01, -1.491085e+00, 1.723922e+01, -3.859018e+01, 2.845044e+01,
    3.741539e+00, 2.187098e+02, -4.531252e+02, 2.936479e+02, -6.287470e+01,
    4.905945e-01, -1.437348e-01, 2.357824e-01, 1.871015e-03, -3.788963e-03, 0.0,
    -2.741539e+00, -6.720113e-01, -7.932688e-02, 1.918681e-03, -2.032902e-03, 0.0,
    1e-10,
  ),
  "mgga_c_m06_2x": (
    0.06, 0.0031, 0.00515088, 0.00304966,
    3.097855e-01, -5.528642e+00, 1.347420e+01, -3.213623e+01, 2.846742e+01,
    8.833596e-01, 3.357972e+01, -7.043548e+01, 4.978271e+01, -1.852891e+01,
    6.902145e-01, 9.847204e-02, 2.214797e-01, -1.968264e-03, -6.775479e-03, 0.0,
    1.166404e-01, -9.120847e-02, -6.726189e-02, 6.720580e-05, 8.448011e-04, 0.0,
    1e-10,
  ),
  "mgga_c_m06_hf": (
    0.06, 0.0031, 0.00515088, 0.00304966,
    1.023254e-01, -2.453783e+00, 2.913180e+01, -3.494358e+01, 2.315955e+01,
    1.674634e+00, 5.732017e+01, 5.955416e+01, -2.311007e+02, 1.255199e+02,
    8.976746e-01, -2.345830e-01, 2.368173e-01, -9.913890e-04, -1.146165e-02, 0.0,
    -6.746338e-01, -1.534002e-01, -9.021521e-02, -1.292037e-03, -2.352983e-04, 0.0,
    1e-10,
  ),
  "mgga_c_m06_sx": (
    0.06, 0.0031, 0.00515088, 0.00304966,
    1.17575011057022E+00, 6.58083496678423E-01, -2.78913774852905E+00, -1.18597601856255E+00, 1.16439928209688E+00,
    1.63738167314691E-01, -4.36481171027951E-01, -1.90232628449712E+00, -1.42432902881841E+00, -9.05909137360893E-01,
    8.17322574473352E-02, -2.88531085759385E-02, 9.05917734868130E-02, 0.0, 0.0, -4.86297499082106E-04,
    7.40594619832397E-01, 1.23306511345974E-02, -1.88253421850249E-02, 0.0, 0.0, 4.87276242162303E-04,
    1e-10,
  ),
  "mgga_c_revm06": (
    0.06, 0.0031, 0.00515088, 0.00304966,
    0.9017224575, 0.2079991827, -1.823747562, -1.384430429, -0.4423253381,
    1.222401598, 0.6613907336, -1.884581043, -2.780360568, -3.068579344,
    -0.14670959, -0.0001832187007, 0.0848437243, 0.0, 0.0, 0.0002280677172,
    -0.339066672, 0.003790156384, -0.02762485975, 0.0, 0.0, 0.0004076285162,
    1e-10,
  ),
  "mgga_c_revm06_l": (
    0.06, 0.0031, 0.00515088, 0.00304966,
    1.227659748, 0.855201283, -3.113346677, -2.239678026, 0.354638962,
    0.344360696, -0.557080242, -2.009821162, -1.857641887, -1.076639864,
    -0.538821292, -0.02829603, 0.023889696, 0.0, 0.0, -0.002437902,
    0.4007146, 0.015796569, -0.032680984, 0.0, 0.0, 0.001260132,
    1e-10,
  ),
}

_M06_PARAM_SETS["mgga_c_m06l"] = _M06_PARAM_SETS["mgga_c_m06_l"]


def _as_param_dict(params) -> dict:
  if hasattr(params, "_asdict"):
    return {k: _as_numpy(v) for k, v in params._asdict().items()}
  return {}


def _as_numpy(value):
  return np.asarray(value, dtype=np.float64)


def _build_deorbitalized(name: str, polarized: bool, _visited: set[str]):
  cfg = _DEORBITALIZED_CONFIG[name]
  base = get_params(cfg["base"], polarized, _visited=_visited)
  params_dict = _as_param_dict(base.params)
  params_dict["pc07_a"] = _as_numpy(_PC07_A)
  params_dict["pc07_b"] = _as_numpy(_PC07_B)
  params = dict_to_namedtuple(params_dict, "params")
  data = base._asdict()
  data.update({
    "number": cfg["number"],
    "libxc_name": name,
    "params": params,
    "maple_name": cfg["module"],
    "name": name,
    "nlc_b": cfg.get("nlc_b", base.nlc_b),
    "nlc_C": cfg.get("nlc_C", base.nlc_C),
  })
  return dict_to_namedtuple(data, "P")


def _m06_params_from_values(values: tuple[float, ...]) -> dict[str, np.ndarray]:
  idx = 0
  params: dict[str, np.ndarray] = {}
  for field, count in _M06_FIELD_LAYOUT:
    chunk = values[idx:idx + count]
    idx += count
    if count == 1:
      params[field] = _as_numpy(chunk[0])
    else:
      params[field] = _as_numpy(chunk)
  return params


def _build_m06_variant(name: str, polarized: bool, _visited: set[str]):
  values = _M06_PARAM_SETS[name]
  params = _m06_params_from_values(values)
  data = dict(_M06_DEFAULT_META)
  data.update({
    "number": _M06_NUMBERS[name],
    "libxc_name": name,
    "params": params,
    "name": name,
    "nspin": 2 if polarized else 1,
  })
  return dict_to_namedtuple(data, "P")

# Constants
XC_UNPOLARIZED = 0
XC_POLARIZED = 1

from ._libxc.functional import LibXCFunctional
from ._libxc import util as _libxc_util


def list_functionals() -> list[str]:
  """Return all LibXC functional names known to JXC.

  This is a lightweight convenience wrapper around LibXC's registry:

  - If the bundled LibXC bindings are available, we return the list from
    ``jxc._libxc.util.xc_available_functional_names()``, sorted.
  - If that fails, we fall back to scanning the
    ``jxc.functionals`` package for generated Maple modules.

  Returns:
    A sorted list of functional names (e.g. ``\"lda_x\"``,
    ``\"gga_x_pbe\"``, ``\"hyb_gga_xc_b3lyp\"``).
  """
  try:
    return sorted(_libxc_util.xc_available_functional_names())
  except Exception:
    # Minimal, best-effort fallback based on generated modules.
    import pkgutil
    from . import functionals as functionals_pkg

    return sorted(
      name
      for _, name, is_pkg in pkgutil.iter_modules(functionals_pkg.__path__)
      if not is_pkg and name != "utils"
    )


def dict_to_namedtuple(d: dict, name: str):
  """Recursively convert a dict to a namedtuple

  Parameters:
  ----------
  d : dict
      A dictionary obtained from `get_param`
  name : str
      The name of the namedtuple

  Notes:
  ------
  If the dict contains a key "lambda", it will be renamed to "lambda_".
  If the value is a dict, it will be converted to a namedtuple,
  based on the key name. If the value is a list, it will remain a list
  but with elements converted to namedtuples.
  """
  if "lambda" in d:
    d["lambda_"] = d.pop("lambda")

  for k, v in d.items():
    if isinstance(v, dict):
      d[k] = dict_to_namedtuple(v, k)
    elif isinstance(v, (list, tuple)):
      d[k] = [dict_to_namedtuple(i, k) if isinstance(i, dict) else i for i in v]

  return namedtuple(name, d.keys())(*d.values())


def get_params(name, polarized, *ext_params, _visited=None):
  """Get parameters for a functional using compiled helper bindings.

  Always extract metadata (thresholds, aux components) from the actual
  functional `name`. If the functional reuses parameter structs from a
  related functional (see PARAM_ALIASES), merge those params in so that
  generated code referring to params.<attr> can resolve correctly without
  perturbing thresholds or metadata.
  """
  if _visited is None:
    _visited = set()
  if name in _visited:
    raise RuntimeError(f"Parameter alias cycle detected for {name}")
  _visited.add(name)
  if name in PARAM_ALIAS_BLACKLIST:
    raise RuntimeError(
      f"parameter extraction for {name} requires helper support"
    )
  if name in _DEORBITALIZED_CONFIG:
    return _build_deorbitalized(name, polarized, _visited)
  if name in _M06_PARAM_SETS:
    return _build_m06_variant(name, polarized, _visited)
  try:
    from . import helper as _helper
  except Exception as e:
    raise RuntimeError(
      "jxc.helper extension not found. Run 'make build-helper' to build it."
    ) from e

  # 1) Extract metadata from the actual functional
  func_actual = LibXCFunctional(name, int(polarized) + 1)
  if ext_params:
    func_actual.set_ext_params(ext_params)
  xc_func_ptr_actual = ctypes.cast(func_actual.xc_func, ctypes.c_void_p).value
  p_actual = _helper.get_p(xc_func_ptr_actual)

  # 2) If an alias exists, try to pull params from the canonical functional
  params_dict = p_actual.get("params", {}) or {}
  alias = PARAM_ALIASES.get(name)
  if alias is not None:
    try:
      func_alias = LibXCFunctional(alias, int(polarized) + 1)
      if ext_params:
        func_alias.set_ext_params(ext_params)
      xc_func_ptr_alias = ctypes.cast(func_alias.xc_func, ctypes.c_void_p).value
      p_alias = _helper.get_p(xc_func_ptr_alias)
      alias_params = p_alias.get("params", {}) or {}
      # Only adopt alias params if actual has none, or merge conservatively
      if not params_dict:
        params_dict = alias_params
      else:
        # Merge without clobbering any existing actual fields
        merged = dict(params_dict)
        for k, v in alias_params.items():
          if k not in merged:
            merged[k] = v
        params_dict = merged
    except Exception:
      # Fallback silently if alias cannot be instantiated
      pass

  # 3) Build final dict and attach name
  p_dict = dict(p_actual)
  p_dict["params"] = params_dict
  p_dict["name"] = name
  # Preserve maple_name from helper (may be "", "DEORBITALIZE", or actual name)

  # Add name field to func_aux children (use maple_name or reverse-lookup from number)
  if "func_aux" in p_dict:
    func_aux = []
    for entry in p_dict["func_aux"]:
      if isinstance(entry, dict):
        func_aux.append(entry)
      else:
        try:
          key = entry[0]
          coef = entry[1] if len(entry) > 1 else None
          new_child = {"name": key}
          if coef is not None:
            new_child["mix_coef"] = coef
          func_aux.append(new_child)
        except Exception:
          # fallback: keep original entry even if not understood
          func_aux.append({"name": ""})
    for child_dict in func_aux:
      if "name" not in child_dict or not child_dict["name"]:
        maple_name = child_dict.get("maple_name", "")
        if maple_name:
          child_dict["name"] = maple_name
        else:
          child_number = child_dict.get("number")
          if child_number is not None:
            try:
              temp_func = LibXCFunctional(child_number, int(polarized) + 1)
              child_dict["name"] = child_dict.get("libxc_name", temp_func.get_name())
            except Exception:
              child_dict["name"] = child_dict.get("libxc_name", f"xc_{child_number}")
          else:
            child_dict.setdefault("name", "")
    p_dict["func_aux"] = func_aux

  params_dict = p_dict.get("params", {})
  if isinstance(params_dict, dict) and not params_dict:
    alias = PARAM_ALIASES.get(name)
    if alias is not None:
      base_np = get_params(alias, polarized, *ext_params, _visited=_visited)
      params_dict = dict(base_np.params._asdict())
      p_dict["params"] = params_dict
  return dict_to_namedtuple(p_dict, "P")


def get_xc_functional(
  xc: str = "gga_x_pbe",
  polarized: bool = False,
  order: str = "exc",
  *,
  backend: str = "maple",
):
  """
  Import XC functional implementation or its derivatives.

  Args:
      xc: Functional name like 'lda_x', 'gga_x_pbe', 'hyb_gga_xc_b3lyp', etc.
      polarized: Whether to use polarized version.
      order: Which quantity to evaluate.  Supported values:
          - "exc" (default): exchange-correlation energy density callable.
          - "vxc": first derivative (vrho, vsigma, ...).
          - "fxc": second derivatives (FXC tensor).
          - "kxc": third derivatives.
          - "lxc": fourth derivatives.
      backend: Derivative backend for orders >= \"vxc\". Supported values:
          - \"maple\" (default): Maple-generated derivatives when available,
            with automatic fallback to AD if no pre-generated code exists.
          - \"ad\": JAX AD over EXC modules (slower JIT, useful for functionals
            without Maple codegen).

  Returns:
      Callable with a high-level API:
        - order="exc": `f(rho, sigma=None, lapl=None, tau=None) -> epsilon_xc`
        - order="vxc": `f(rho, sigma=None, lapl=None, tau=None, use_jax=False) -> {"vrho", "vsigma", ...}`
        - order in {"fxc","kxc","lxc"}: `f(rho, sigma=None, lapl=None, tau=None) -> derivative dict`

      For all derivative orders, an optional first positional argument can be
      a precomputed parameter object from `get_params`; if omitted, parameters
      are looked up automatically.
  """
  normalized = order.lower()
  if normalized not in {"exc", "vxc", "fxc", "kxc", "lxc"}:
    raise ValueError(
      f"Unsupported order '{order}'. Expected 'exc', 'vxc', 'fxc', 'kxc', or 'lxc'."
    )
  if normalized == "exc":
    from .composite import make_epsilon_xc

    p = get_params(xc, polarized)
    return make_epsilon_xc(p)

  if normalized == "vxc":
    return _build_vxc_callable(xc, polarized, backend=backend)
  if normalized == "fxc":
    return _build_fxc_callable(xc, polarized, backend=backend)
  if normalized == "kxc":
    return _build_ad_deriv_callable(xc, polarized, "kxc", backend=backend)
  if normalized == "lxc":
    return _build_ad_deriv_callable(xc, polarized, "lxc", backend=backend)
  raise AssertionError("unreachable")


def _split_callable_args(args, name: str):
  if not args:
    raise TypeError(f"{name}: expected (rho,) or (params, rho) arguments")
  if len(args) == 1:
    return None, args[0]
  if len(args) == 2:
    params, rho = args
    param_name = getattr(params, "name", "") or getattr(params, "maple_name", "") or getattr(params, "libxc_name", "")
    if param_name and param_name != name:
      raise ValueError(f"Parameter object '{param_name}' does not match functional '{name}'")
    return params, rho
  raise TypeError(f"{name}: expected at most two positional arguments, got {len(args)}")


def _maybe_use_maple_backend(name: str, polarized: bool, order: str) -> bool:
  """Return True if Maple derivatives appear to be available and non-trivial for this order.

  Tests the Maple backend with a representative input and verifies that:
  1. The call succeeds
  2. The output contains expected keys
  3. The output is not all zeros (which would indicate a stub implementation)
  """
  from .derivatives import _maple_derivs as _maple  # type: ignore
  import jax.numpy as jnp
  import numpy as np

  fam = _maple._family_from_name(name)  # type: ignore[attr-defined]
  if fam is None:
    return False

  # Use non-trivial test inputs to detect stub implementations that return all zeros
  rho = jnp.array(0.3, dtype=jnp.float64)  # scalar for proper testing

  try:
    if polarized:
      rho_pair = (rho, rho * 0.8)
      if fam == "lda":
        sigma = lapl = tau = None
      elif fam == "gga":
        sig_val = jnp.array(0.05, dtype=jnp.float64)
        sigma = (sig_val, sig_val * 0.5, sig_val * 0.3)
        lapl = tau = None
      elif fam == "mgga":
        sig_val = jnp.array(0.05, dtype=jnp.float64)
        other_val = jnp.array(0.02, dtype=jnp.float64)
        sigma = (sig_val, sig_val * 0.5, sig_val * 0.3)
        lapl = (other_val, other_val * 0.8)
        tau = (other_val * 2, other_val * 1.5)
      else:
        return False
      out = _maple.eval_polarized(name, rho_pair, sigma=sigma, lapl=lapl, tau=tau, order=order, use_maple=True)
    else:
      if fam == "lda":
        sigma = lapl = tau = None
      elif fam == "gga":
        sigma = jnp.array(0.05, dtype=jnp.float64)
        lapl = tau = None
      elif fam == "mgga":
        sigma = jnp.array(0.05, dtype=jnp.float64)
        lapl = jnp.array(0.02, dtype=jnp.float64)
        tau = jnp.array(0.04, dtype=jnp.float64)
      else:
        return False
      out = _maple.eval_unpolarized(name, rho, sigma=sigma, lapl=lapl, tau=tau, order=order, use_maple=True)
  except Exception:
    return False

  if not out:
    return False

  # Check that at least one key derivative is non-zero (detect stub implementations)
  # Map order to expected primary key
  primary_keys = {
    "vxc": "vrho",
    "fxc": "v2rho2",
    "kxc": "v3rho3",
    "lxc": "v4rho4",
  }
  primary_key = primary_keys.get(order, "vrho")

  if primary_key in out:
    val = np.asarray(out[primary_key])
    # Check if any value is non-zero (not a stub)
    if np.any(np.abs(val) > 1e-15):
      return True

  # If primary key missing or all zeros, check any key
  for key, val in out.items():
    arr = np.asarray(val)
    if np.any(np.abs(arr) > 1e-15):
      return True

  # All values are zero - likely a stub implementation
  return False


def _build_vxc_callable(name: str, polarized: bool, backend: str = "ad"):
  # Lazy imports to avoid circular dependency during module import.
  from .derivatives import ad_derivs as _ad

  backend_norm = (backend or "ad").lower()
  use_maple = backend_norm == "maple"
  _maple = None
  if use_maple:
    try:
      from .derivatives import _maple_derivs as _maple  # type: ignore
      use_maple = _maybe_use_maple_backend(name, polarized, "vxc")
    except Exception:
      use_maple = False

  if use_maple and _maple is not None:
    if polarized:
      def _call(*args, sigma=None, lapl=None, tau=None):
        _, rho = _split_callable_args(args, name)
        return _maple.eval_polarized(name, rho, sigma=sigma, lapl=lapl, tau=tau, order="vxc", use_maple=True)
    else:
      def _call(*args, sigma=None, lapl=None, tau=None):
        _, rho = _split_callable_args(args, name)
        return _maple.eval_unpolarized(name, rho, sigma=sigma, lapl=lapl, tau=tau, order="vxc", use_maple=True)
    return _call

  # Default / fallback: AD backend.
  if polarized:
    def _call(*args, sigma=None, lapl=None, tau=None):
      _, rho = _split_callable_args(args, name)
      return _ad.ad_eval_polarized_vxc(
        name, "vxc", rho, sigma=sigma, lapl=lapl, tau=tau
      )
  else:
    def _call(*args, sigma=None, lapl=None, tau=None):
      _, rho = _split_callable_args(args, name)
      return _ad.ad_eval_unpolarized_vxc(
        name, "vxc", rho, sigma=sigma, lapl=lapl, tau=tau
      )
  return _call


def _build_fxc_callable(name: str, polarized: bool, backend: str = "ad"):
  from .derivatives import ad_derivs as _ad

  backend_norm = (backend or "ad").lower()
  use_maple = backend_norm == "maple"
  _maple = None
  if use_maple:
    try:
      from .derivatives import _maple_derivs as _maple  # type: ignore
      use_maple = _maybe_use_maple_backend(name, polarized, "fxc")
    except Exception:
      use_maple = False

  if use_maple and _maple is not None:
    if polarized:
      def _call(*args, sigma=None, lapl=None, tau=None):
        _, rho = _split_callable_args(args, name)
        return _maple.eval_polarized(name, rho, sigma=sigma, lapl=lapl, tau=tau, order="fxc", use_maple=True)
    else:
      def _call(*args, sigma=None, lapl=None, tau=None):
        _, rho = _split_callable_args(args, name)
        return _maple.eval_unpolarized(name, rho, sigma=sigma, lapl=lapl, tau=tau, order="fxc", use_maple=True)
    return _call

  # Default / fallback: AD backend for FXC.
  if polarized:
    def _call(*args, sigma=None, lapl=None, tau=None):
      _, rho = _split_callable_args(args, name)
      return _ad.ad_eval_polarized_vxc(
        name, "fxc", rho, sigma=sigma, lapl=lapl, tau=tau
      )
  else:
    def _call(*args, sigma=None, lapl=None, tau=None):
      _, rho = _split_callable_args(args, name)
      return _ad.ad_eval_unpolarized_vxc(
        name, "fxc", rho, sigma=sigma, lapl=lapl, tau=tau
      )
  return _call


def _build_ad_deriv_callable(name: str, polarized: bool, order: str, backend: str = "ad"):
  """Build a high-level AD derivative callable for FXC/KXC/LXC."""
  from .derivatives import ad_derivs as _derivs

  norm_order = order.lower()
  if norm_order not in {"fxc", "kxc", "lxc"}:
    raise ValueError(f"_build_ad_deriv_callable: unsupported order {order}")

  backend_norm = (backend or "ad").lower()
  use_maple = backend_norm == "maple"
  _maple = None
  if use_maple:
    try:
      from .derivatives import _maple_derivs as _maple  # type: ignore
      use_maple = _maybe_use_maple_backend(name, polarized, norm_order)
    except Exception:
      use_maple = False

  if use_maple and _maple is not None:
    if polarized:

      def _call(*args, sigma=None, lapl=None, tau=None):
        _, rho = _split_callable_args(args, name)
        return _maple.eval_polarized(name, rho, sigma=sigma, lapl=lapl, tau=tau, order=norm_order, use_maple=True)

    else:

      def _call(*args, sigma=None, lapl=None, tau=None):
        _, rho = _split_callable_args(args, name)
        return _maple.eval_unpolarized(name, rho, sigma=sigma, lapl=lapl, tau=tau, order=norm_order, use_maple=True)

    return _call

  # Default / fallback: AD backend.
  if polarized:

    def _call(*args, sigma=None, lapl=None, tau=None):
      # Optional first arg may be params; AD driver handles params internally.
      _, rho = _split_callable_args(args, name)
      return _derivs.ad_eval_polarized_vxc(
        name, norm_order, rho, sigma=sigma, lapl=lapl, tau=tau
      )

  else:

    def _call(*args, sigma=None, lapl=None, tau=None):
      _, rho = _split_callable_args(args, name)
      return _derivs.ad_eval_unpolarized_vxc(
        name, norm_order, rho, sigma=sigma, lapl=lapl, tau=tau
      )

  return _call
