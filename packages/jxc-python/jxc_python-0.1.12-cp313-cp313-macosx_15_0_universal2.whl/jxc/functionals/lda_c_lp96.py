"""Generated from lda_c_lp96.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
import numpy as np
from jax.numpy import array as array
from jax.numpy import int32 as int32
from jax.numpy import nan as nan
from typing import Callable, Optional
from jxc.functionals.utils import *


def pol(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_C1_raw = params.C1
  if isinstance(params_C1_raw, (str, bytes, dict)):
    params_C1 = params_C1_raw
  else:
    try:
      params_C1_seq = list(params_C1_raw)
    except TypeError:
      params_C1 = params_C1_raw
    else:
      params_C1_seq = np.asarray(params_C1_seq, dtype=np.float64)
      params_C1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C1_seq))
  params_C2_raw = params.C2
  if isinstance(params_C2_raw, (str, bytes, dict)):
    params_C2 = params_C2_raw
  else:
    try:
      params_C2_seq = list(params_C2_raw)
    except TypeError:
      params_C2 = params_C2_raw
    else:
      params_C2_seq = np.asarray(params_C2_seq, dtype=np.float64)
      params_C2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C2_seq))
  params_C3_raw = params.C3
  if isinstance(params_C3_raw, (str, bytes, dict)):
    params_C3 = params_C3_raw
  else:
    try:
      params_C3_seq = list(params_C3_raw)
    except TypeError:
      params_C3 = params_C3_raw
    else:
      params_C3_seq = np.asarray(params_C3_seq, dtype=np.float64)
      params_C3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C3_seq))

  functional_body = lambda rs, zeta=None: params_C1 + params_C2 * f.n_total(rs) ** (-1 / 3) + params_C3 * f.n_total(rs) ** (-2 / 3)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res


def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_C1_raw = params.C1
  if isinstance(params_C1_raw, (str, bytes, dict)):
    params_C1 = params_C1_raw
  else:
    try:
      params_C1_seq = list(params_C1_raw)
    except TypeError:
      params_C1 = params_C1_raw
    else:
      params_C1_seq = np.asarray(params_C1_seq, dtype=np.float64)
      params_C1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C1_seq))
  params_C2_raw = params.C2
  if isinstance(params_C2_raw, (str, bytes, dict)):
    params_C2 = params_C2_raw
  else:
    try:
      params_C2_seq = list(params_C2_raw)
    except TypeError:
      params_C2 = params_C2_raw
    else:
      params_C2_seq = np.asarray(params_C2_seq, dtype=np.float64)
      params_C2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C2_seq))
  params_C3_raw = params.C3
  if isinstance(params_C3_raw, (str, bytes, dict)):
    params_C3 = params_C3_raw
  else:
    try:
      params_C3_seq = list(params_C3_raw)
    except TypeError:
      params_C3 = params_C3_raw
    else:
      params_C3_seq = np.asarray(params_C3_seq, dtype=np.float64)
      params_C3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C3_seq))

  functional_body = lambda rs, zeta=None: params_C1 + params_C2 * f.n_total(rs) ** (-1 / 3) + params_C3 * f.n_total(rs) ** (-2 / 3)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t5 = t2 ** 2
  vrho_0_ = params.C1 + params.C2 / t2 + params.C3 / t5 + t1 * (-params.C2 / t2 / t1 / 0.3e1 - 0.2e1 / 0.3e1 * params.C3 / t5 / t1)
  vrho_1_ = vrho_0_

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res


def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** (0.1e1 / 0.3e1)
  t4 = t1 ** 2
  vrho_0_ = params.C1 + params.C2 / t1 + params.C3 / t4 + r0 * (-params.C2 / t1 / r0 / 0.3e1 - 0.2e1 / 0.3e1 * params.C3 / t4 / r0)

  res = {'vrho': vrho_0_}
  return res
