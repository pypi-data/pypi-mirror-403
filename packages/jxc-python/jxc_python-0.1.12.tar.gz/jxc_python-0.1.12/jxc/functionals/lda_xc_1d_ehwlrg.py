"""Generated from lda_xc_1d_ehwlrg.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
  params_a3_raw = params.a3
  if isinstance(params_a3_raw, (str, bytes, dict)):
    params_a3 = params_a3_raw
  else:
    try:
      params_a3_seq = list(params_a3_raw)
    except TypeError:
      params_a3 = params_a3_raw
    else:
      params_a3_seq = np.asarray(params_a3_seq, dtype=np.float64)
      params_a3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a3_seq))
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))

  functional_body = lambda rs, zeta=None: (params_a1 + params_a2 * f.n_total(rs) + params_a3 * f.n_total(rs) ** 2) * f.n_total(rs) ** params_alpha

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
  params_a3_raw = params.a3
  if isinstance(params_a3_raw, (str, bytes, dict)):
    params_a3 = params_a3_raw
  else:
    try:
      params_a3_seq = list(params_a3_raw)
    except TypeError:
      params_a3 = params_a3_raw
    else:
      params_a3_seq = np.asarray(params_a3_seq, dtype=np.float64)
      params_a3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a3_seq))
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))

  functional_body = lambda rs, zeta=None: (params_a1 + params_a2 * f.n_total(rs) + params_a3 * f.n_total(rs) ** 2) * f.n_total(rs) ** params_alpha

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
  params_a3_raw = params.a3
  if isinstance(params_a3_raw, (str, bytes, dict)):
    params_a3 = params_a3_raw
  else:
    try:
      params_a3_seq = list(params_a3_raw)
    except TypeError:
      params_a3 = params_a3_raw
    else:
      params_a3_seq = np.asarray(params_a3_seq, dtype=np.float64)
      params_a3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a3_seq))
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))

  functional_body = lambda rs, zeta=None: (params_a1 + params_a2 * f.n_total(rs) + params_a3 * f.n_total(rs) ** 2) * f.n_total(rs) ** params_alpha

  t1 = r0 + r1
  t3 = t1 ** 2
  t6 = t1 ** params.alpha
  t7 = (params.a2 * t1 + params.a3 * t3 + params.a1) * t6
  vrho_0_ = t7 + t1 * (0.2e1 * params.a3 * t1 + params.a2) * t6 + t7 * params.alpha
  vrho_1_ = vrho_0_
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
  params_a3_raw = params.a3
  if isinstance(params_a3_raw, (str, bytes, dict)):
    params_a3 = params_a3_raw
  else:
    try:
      params_a3_seq = list(params_a3_raw)
    except TypeError:
      params_a3 = params_a3_raw
    else:
      params_a3_seq = np.asarray(params_a3_seq, dtype=np.float64)
      params_a3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a3_seq))
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))

  functional_body = lambda rs, zeta=None: (params_a1 + params_a2 * f.n_total(rs) + params_a3 * f.n_total(rs) ** 2) * f.n_total(rs) ** params_alpha

  t1 = r0 ** 2
  t5 = r0 ** params.alpha
  t6 = (r0 * params.a2 + t1 * params.a3 + params.a1) * t5
  vrho_0_ = t6 + r0 * (0.2e1 * r0 * params.a3 + params.a2) * t5 + t6 * params.alpha
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = r0 * params.a3
  t4 = r0 ** params.alpha
  t5 = (0.2e1 * t1 + params.a2) * t4
  t7 = r0 ** 2
  t11 = (r0 * params.a2 + t7 * params.a3 + params.a1) * t4
  t12 = 0.1e1 / r0
  t19 = params.alpha ** 2
  v2rho2_0_ = t11 * t19 * t12 + t11 * params.alpha * t12 + 0.2e1 * t1 * t4 + 0.2e1 * t5 * params.alpha + 0.2e1 * t5
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** params.alpha
  t2 = params.a3 * t1
  t7 = (0.2e1 * r0 * params.a3 + params.a2) * t1
  t8 = 0.1e1 / r0
  t12 = r0 ** 2
  t16 = (r0 * params.a2 + t12 * params.a3 + params.a1) * t1
  t17 = 0.1e1 / t12
  t22 = params.alpha ** 2
  v3rho3_0_ = t16 * t22 * params.alpha * t17 - t16 * params.alpha * t17 + 0.3e1 * t7 * t22 * t8 + 0.3e1 * t7 * params.alpha * t8 + 0.6e1 * t2 * params.alpha + 0.6e1 * t2

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** params.alpha
  t2 = params.a3 * t1
  t3 = 0.1e1 / r0
  t10 = (0.2e1 * r0 * params.a3 + params.a2) * t1
  t11 = r0 ** 2
  t12 = 0.1e1 / t11
  t19 = (r0 * params.a2 + t11 * params.a3 + params.a1) * t1
  t20 = params.alpha ** 2
  t22 = 0.1e1 / t11 / r0
  t31 = t20 * params.alpha
  t35 = t20 ** 2
  v4rho4_0_ = 0.4e1 * t10 * t31 * t12 - 0.4e1 * t10 * params.alpha * t12 - t19 * t20 * t22 - 0.2e1 * t19 * t31 * t22 + t19 * t35 * t22 + 0.2e1 * t19 * params.alpha * t22 + 0.12e2 * t2 * t20 * t3 + 0.12e2 * t2 * params.alpha * t3

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 + r1
  t2 = params.a3 * t1
  t5 = t1 ** params.alpha
  t6 = (params.a2 + 0.2e1 * t2) * t5
  t9 = t1 ** 2
  t12 = (params.a2 * t1 + params.a3 * t9 + params.a1) * t5
  t13 = 0.1e1 / t1
  t20 = params.alpha ** 2
  d11 = t12 * t20 * t13 + t12 * params.alpha * t13 + 0.2e1 * t2 * t5 + 0.2e1 * t6 * params.alpha + 0.2e1 * t6
  d12 = d11
  d22 = d12
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** params.alpha
  t3 = params.a3 * t2
  t8 = (0.2e1 * params.a3 * t1 + params.a2) * t2
  t9 = 0.1e1 / t1
  t14 = t1 ** 2
  t17 = (params.a2 * t1 + params.a3 * t14 + params.a1) * t2
  t18 = 0.1e1 / t14
  t23 = params.alpha ** 2
  d111 = t17 * t23 * params.alpha * t18 - t17 * params.alpha * t18 + 0.3e1 * t8 * t23 * t9 + 0.3e1 * t8 * params.alpha * t9 + 0.6e1 * t3 * params.alpha + 0.6e1 * t3

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** params.alpha
  t3 = params.a3 * t2
  t4 = 0.1e1 / t1
  t11 = (0.2e1 * params.a3 * t1 + params.a2) * t2
  t12 = t1 ** 2
  t13 = 0.1e1 / t12
  t20 = (params.a2 * t1 + params.a3 * t12 + params.a1) * t2
  t21 = params.alpha ** 2
  t23 = 0.1e1 / t12 / t1
  t32 = t21 * params.alpha
  t36 = t21 ** 2
  d1111 = 0.4e1 * t11 * t32 * t13 - 0.4e1 * t11 * params.alpha * t13 - t20 * t21 * t23 - 0.2e1 * t20 * t32 * t23 + t20 * t36 * t23 + 0.2e1 * t20 * params.alpha * t23 + 0.12e2 * t3 * t21 * t4 + 0.12e2 * t3 * params.alpha * t4

  res = {'v4rho4': d1111}
  return res
