"""Generated from lda_xc_ksdt.mpl."""

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
  params_T_raw = params.T
  if isinstance(params_T_raw, (str, bytes, dict)):
    params_T = params_T_raw
  else:
    try:
      params_T_seq = list(params_T_raw)
    except TypeError:
      params_T = params_T_raw
    else:
      params_T_seq = np.asarray(params_T_seq, dtype=np.float64)
      params_T = np.concatenate((np.array([np.nan], dtype=np.float64), params_T_seq))
  params_b_0__raw = params.b[0]
  if isinstance(params_b_0__raw, (str, bytes, dict)):
    params_b_0_ = params_b_0__raw
  else:
    try:
      params_b_0__seq = list(params_b_0__raw)
    except TypeError:
      params_b_0_ = params_b_0__raw
    else:
      params_b_0__seq = np.asarray(params_b_0__seq, dtype=np.float64)
      params_b_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_0__seq))
  params_b_1__raw = params.b[1]
  if isinstance(params_b_1__raw, (str, bytes, dict)):
    params_b_1_ = params_b_1__raw
  else:
    try:
      params_b_1__seq = list(params_b_1__raw)
    except TypeError:
      params_b_1_ = params_b_1__raw
    else:
      params_b_1__seq = np.asarray(params_b_1__seq, dtype=np.float64)
      params_b_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_1__seq))
  params_c_0__raw = params.c[0]
  if isinstance(params_c_0__raw, (str, bytes, dict)):
    params_c_0_ = params_c_0__raw
  else:
    try:
      params_c_0__seq = list(params_c_0__raw)
    except TypeError:
      params_c_0_ = params_c_0__raw
    else:
      params_c_0__seq = np.asarray(params_c_0__seq, dtype=np.float64)
      params_c_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_0__seq))
  params_c_1__raw = params.c[1]
  if isinstance(params_c_1__raw, (str, bytes, dict)):
    params_c_1_ = params_c_1__raw
  else:
    try:
      params_c_1__seq = list(params_c_1__raw)
    except TypeError:
      params_c_1_ = params_c_1__raw
    else:
      params_c_1__seq = np.asarray(params_c_1__seq, dtype=np.float64)
      params_c_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_1__seq))
  params_d_0__raw = params.d[0]
  if isinstance(params_d_0__raw, (str, bytes, dict)):
    params_d_0_ = params_d_0__raw
  else:
    try:
      params_d_0__seq = list(params_d_0__raw)
    except TypeError:
      params_d_0_ = params_d_0__raw
    else:
      params_d_0__seq = np.asarray(params_d_0__seq, dtype=np.float64)
      params_d_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_0__seq))
  params_d_1__raw = params.d[1]
  if isinstance(params_d_1__raw, (str, bytes, dict)):
    params_d_1_ = params_d_1__raw
  else:
    try:
      params_d_1__seq = list(params_d_1__raw)
    except TypeError:
      params_d_1_ = params_d_1__raw
    else:
      params_d_1__seq = np.asarray(params_d_1__seq, dtype=np.float64)
      params_d_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_1__seq))
  params_e_0__raw = params.e[0]
  if isinstance(params_e_0__raw, (str, bytes, dict)):
    params_e_0_ = params_e_0__raw
  else:
    try:
      params_e_0__seq = list(params_e_0__raw)
    except TypeError:
      params_e_0_ = params_e_0__raw
    else:
      params_e_0__seq = np.asarray(params_e_0__seq, dtype=np.float64)
      params_e_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_0__seq))
  params_e_1__raw = params.e[1]
  if isinstance(params_e_1__raw, (str, bytes, dict)):
    params_e_1_ = params_e_1__raw
  else:
    try:
      params_e_1__seq = list(params_e_1__raw)
    except TypeError:
      params_e_1_ = params_e_1__raw
    else:
      params_e_1__seq = np.asarray(params_e_1__seq, dtype=np.float64)
      params_e_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_1__seq))
  params_thetaParam_raw = params.thetaParam
  if isinstance(params_thetaParam_raw, (str, bytes, dict)):
    params_thetaParam = params_thetaParam_raw
  else:
    try:
      params_thetaParam_seq = list(params_thetaParam_raw)
    except TypeError:
      params_thetaParam = params_thetaParam_raw
    else:
      params_thetaParam_seq = np.asarray(params_thetaParam_seq, dtype=np.float64)
      params_thetaParam = np.concatenate((np.array([np.nan], dtype=np.float64), params_thetaParam_seq))

  g = [None, 2 / 3, -0.0139261, 0.183208]

  l = np.array([np.nan, 1.064009, 0.572565], dtype=np.float64)

  phi = lambda malpha, z: (f.opz_pow_n(z, malpha) + f.opz_pow_n(-z, malpha) - 2) / (2 ** malpha - 2)

  lambda_ = (4 / (9 * jnp.pi)) ** (1 / 3)

  a = np.array([np.nan, 0.75, 3.04363, -0.09227, 1.7035, 8.31051, 5.1105], dtype=np.float64)

  bb = lambda b, t: jnp.tanh(1 / jnp.sqrt(t)) * (b[1] + b[2] * t ** 2 + b[3] * t ** 4) / (1 + b[4] * t ** 2 + b[5] * t ** 4)

  ee = lambda e, t: jnp.tanh(1 / t) * (e[1] + e[2] * t ** 2 + e[3] * t ** 4) / (1 + e[4] * t ** 2 + e[5] * t ** 4)

  mtt = lambda rs, z: 2 * (4 / (9 * jnp.pi)) ** (2 / 3) * params_T * rs ** 2 * (1 + params_thetaParam * z) ** (2 / 3)

  alpha = lambda t, rs: 2 - (g[1] + g[2] * rs) / (1 + g[3] * rs) * jnp.exp(-t * (l[1] + l[2] * t * jnp.sqrt(rs)))

  a0 = 1 / (jnp.pi * lambda_)

  dd = lambda d, t: bb(d, t)

  cc = lambda c, e, t: (c[1] + c[2] * jnp.exp(-c[3] / t)) * ee(e, t)

  aa = lambda t: a0 * jnp.tanh(1 / t) * (a[1] + a[2] * t ** 2 + a[3] * t ** 3 + a[4] * t ** 4) / (1 + a[5] * t ** 2 + a[6] * t ** 4)

  fxc = lambda omega, b, c, d, e, rs, t: -(omega * aa(t) + bb(b, t) * jnp.sqrt(rs) + cc(c, e, t) * rs) / (rs * (1 + dd(d, t) * jnp.sqrt(rs) + ee(e, t) * rs))

  functional_body = lambda rs, z: +fxc(1, params_b_0_, params_c_0_, params_d_0_, params_e_0_, rs, mtt(rs, z)) * (1 - phi(alpha(mtt(rs, z), rs), z)) + fxc(2 ** (1 / 3), params_b_1_, params_c_1_, params_d_1_, params_e_1_, rs, mtt(rs, z) / 2 ** (2 / 3)) * phi(alpha(mtt(rs, z), rs), z)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_T_raw = params.T
  if isinstance(params_T_raw, (str, bytes, dict)):
    params_T = params_T_raw
  else:
    try:
      params_T_seq = list(params_T_raw)
    except TypeError:
      params_T = params_T_raw
    else:
      params_T_seq = np.asarray(params_T_seq, dtype=np.float64)
      params_T = np.concatenate((np.array([np.nan], dtype=np.float64), params_T_seq))
  params_b_0__raw = params.b[0]
  if isinstance(params_b_0__raw, (str, bytes, dict)):
    params_b_0_ = params_b_0__raw
  else:
    try:
      params_b_0__seq = list(params_b_0__raw)
    except TypeError:
      params_b_0_ = params_b_0__raw
    else:
      params_b_0__seq = np.asarray(params_b_0__seq, dtype=np.float64)
      params_b_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_0__seq))
  params_b_1__raw = params.b[1]
  if isinstance(params_b_1__raw, (str, bytes, dict)):
    params_b_1_ = params_b_1__raw
  else:
    try:
      params_b_1__seq = list(params_b_1__raw)
    except TypeError:
      params_b_1_ = params_b_1__raw
    else:
      params_b_1__seq = np.asarray(params_b_1__seq, dtype=np.float64)
      params_b_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_1__seq))
  params_c_0__raw = params.c[0]
  if isinstance(params_c_0__raw, (str, bytes, dict)):
    params_c_0_ = params_c_0__raw
  else:
    try:
      params_c_0__seq = list(params_c_0__raw)
    except TypeError:
      params_c_0_ = params_c_0__raw
    else:
      params_c_0__seq = np.asarray(params_c_0__seq, dtype=np.float64)
      params_c_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_0__seq))
  params_c_1__raw = params.c[1]
  if isinstance(params_c_1__raw, (str, bytes, dict)):
    params_c_1_ = params_c_1__raw
  else:
    try:
      params_c_1__seq = list(params_c_1__raw)
    except TypeError:
      params_c_1_ = params_c_1__raw
    else:
      params_c_1__seq = np.asarray(params_c_1__seq, dtype=np.float64)
      params_c_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_1__seq))
  params_d_0__raw = params.d[0]
  if isinstance(params_d_0__raw, (str, bytes, dict)):
    params_d_0_ = params_d_0__raw
  else:
    try:
      params_d_0__seq = list(params_d_0__raw)
    except TypeError:
      params_d_0_ = params_d_0__raw
    else:
      params_d_0__seq = np.asarray(params_d_0__seq, dtype=np.float64)
      params_d_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_0__seq))
  params_d_1__raw = params.d[1]
  if isinstance(params_d_1__raw, (str, bytes, dict)):
    params_d_1_ = params_d_1__raw
  else:
    try:
      params_d_1__seq = list(params_d_1__raw)
    except TypeError:
      params_d_1_ = params_d_1__raw
    else:
      params_d_1__seq = np.asarray(params_d_1__seq, dtype=np.float64)
      params_d_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_1__seq))
  params_e_0__raw = params.e[0]
  if isinstance(params_e_0__raw, (str, bytes, dict)):
    params_e_0_ = params_e_0__raw
  else:
    try:
      params_e_0__seq = list(params_e_0__raw)
    except TypeError:
      params_e_0_ = params_e_0__raw
    else:
      params_e_0__seq = np.asarray(params_e_0__seq, dtype=np.float64)
      params_e_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_0__seq))
  params_e_1__raw = params.e[1]
  if isinstance(params_e_1__raw, (str, bytes, dict)):
    params_e_1_ = params_e_1__raw
  else:
    try:
      params_e_1__seq = list(params_e_1__raw)
    except TypeError:
      params_e_1_ = params_e_1__raw
    else:
      params_e_1__seq = np.asarray(params_e_1__seq, dtype=np.float64)
      params_e_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_1__seq))
  params_thetaParam_raw = params.thetaParam
  if isinstance(params_thetaParam_raw, (str, bytes, dict)):
    params_thetaParam = params_thetaParam_raw
  else:
    try:
      params_thetaParam_seq = list(params_thetaParam_raw)
    except TypeError:
      params_thetaParam = params_thetaParam_raw
    else:
      params_thetaParam_seq = np.asarray(params_thetaParam_seq, dtype=np.float64)
      params_thetaParam = np.concatenate((np.array([np.nan], dtype=np.float64), params_thetaParam_seq))

  g = [None, 2 / 3, -0.0139261, 0.183208]

  l = np.array([np.nan, 1.064009, 0.572565], dtype=np.float64)

  phi = lambda malpha, z: (f.opz_pow_n(z, malpha) + f.opz_pow_n(-z, malpha) - 2) / (2 ** malpha - 2)

  lambda_ = (4 / (9 * jnp.pi)) ** (1 / 3)

  a = np.array([np.nan, 0.75, 3.04363, -0.09227, 1.7035, 8.31051, 5.1105], dtype=np.float64)

  bb = lambda b, t: jnp.tanh(1 / jnp.sqrt(t)) * (b[1] + b[2] * t ** 2 + b[3] * t ** 4) / (1 + b[4] * t ** 2 + b[5] * t ** 4)

  ee = lambda e, t: jnp.tanh(1 / t) * (e[1] + e[2] * t ** 2 + e[3] * t ** 4) / (1 + e[4] * t ** 2 + e[5] * t ** 4)

  mtt = lambda rs, z: 2 * (4 / (9 * jnp.pi)) ** (2 / 3) * params_T * rs ** 2 * (1 + params_thetaParam * z) ** (2 / 3)

  alpha = lambda t, rs: 2 - (g[1] + g[2] * rs) / (1 + g[3] * rs) * jnp.exp(-t * (l[1] + l[2] * t * jnp.sqrt(rs)))

  a0 = 1 / (jnp.pi * lambda_)

  dd = lambda d, t: bb(d, t)

  cc = lambda c, e, t: (c[1] + c[2] * jnp.exp(-c[3] / t)) * ee(e, t)

  aa = lambda t: a0 * jnp.tanh(1 / t) * (a[1] + a[2] * t ** 2 + a[3] * t ** 3 + a[4] * t ** 4) / (1 + a[5] * t ** 2 + a[6] * t ** 4)

  fxc = lambda omega, b, c, d, e, rs, t: -(omega * aa(t) + bb(b, t) * jnp.sqrt(rs) + cc(c, e, t) * rs) / (rs * (1 + dd(d, t) * jnp.sqrt(rs) + ee(e, t) * rs))

  functional_body = lambda rs, z: +fxc(1, params_b_0_, params_c_0_, params_d_0_, params_e_0_, rs, mtt(rs, z)) * (1 - phi(alpha(mtt(rs, z), rs), z)) + fxc(2 ** (1 / 3), params_b_1_, params_c_1_, params_d_1_, params_e_1_, rs, mtt(rs, z) / 2 ** (2 / 3)) * phi(alpha(mtt(rs, z), rs), z)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_T_raw = params.T
  if isinstance(params_T_raw, (str, bytes, dict)):
    params_T = params_T_raw
  else:
    try:
      params_T_seq = list(params_T_raw)
    except TypeError:
      params_T = params_T_raw
    else:
      params_T_seq = np.asarray(params_T_seq, dtype=np.float64)
      params_T = np.concatenate((np.array([np.nan], dtype=np.float64), params_T_seq))
  params_b_0__raw = params.b[0]
  if isinstance(params_b_0__raw, (str, bytes, dict)):
    params_b_0_ = params_b_0__raw
  else:
    try:
      params_b_0__seq = list(params_b_0__raw)
    except TypeError:
      params_b_0_ = params_b_0__raw
    else:
      params_b_0__seq = np.asarray(params_b_0__seq, dtype=np.float64)
      params_b_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_0__seq))
  params_b_1__raw = params.b[1]
  if isinstance(params_b_1__raw, (str, bytes, dict)):
    params_b_1_ = params_b_1__raw
  else:
    try:
      params_b_1__seq = list(params_b_1__raw)
    except TypeError:
      params_b_1_ = params_b_1__raw
    else:
      params_b_1__seq = np.asarray(params_b_1__seq, dtype=np.float64)
      params_b_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_1__seq))
  params_c_0__raw = params.c[0]
  if isinstance(params_c_0__raw, (str, bytes, dict)):
    params_c_0_ = params_c_0__raw
  else:
    try:
      params_c_0__seq = list(params_c_0__raw)
    except TypeError:
      params_c_0_ = params_c_0__raw
    else:
      params_c_0__seq = np.asarray(params_c_0__seq, dtype=np.float64)
      params_c_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_0__seq))
  params_c_1__raw = params.c[1]
  if isinstance(params_c_1__raw, (str, bytes, dict)):
    params_c_1_ = params_c_1__raw
  else:
    try:
      params_c_1__seq = list(params_c_1__raw)
    except TypeError:
      params_c_1_ = params_c_1__raw
    else:
      params_c_1__seq = np.asarray(params_c_1__seq, dtype=np.float64)
      params_c_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_1__seq))
  params_d_0__raw = params.d[0]
  if isinstance(params_d_0__raw, (str, bytes, dict)):
    params_d_0_ = params_d_0__raw
  else:
    try:
      params_d_0__seq = list(params_d_0__raw)
    except TypeError:
      params_d_0_ = params_d_0__raw
    else:
      params_d_0__seq = np.asarray(params_d_0__seq, dtype=np.float64)
      params_d_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_0__seq))
  params_d_1__raw = params.d[1]
  if isinstance(params_d_1__raw, (str, bytes, dict)):
    params_d_1_ = params_d_1__raw
  else:
    try:
      params_d_1__seq = list(params_d_1__raw)
    except TypeError:
      params_d_1_ = params_d_1__raw
    else:
      params_d_1__seq = np.asarray(params_d_1__seq, dtype=np.float64)
      params_d_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_1__seq))
  params_e_0__raw = params.e[0]
  if isinstance(params_e_0__raw, (str, bytes, dict)):
    params_e_0_ = params_e_0__raw
  else:
    try:
      params_e_0__seq = list(params_e_0__raw)
    except TypeError:
      params_e_0_ = params_e_0__raw
    else:
      params_e_0__seq = np.asarray(params_e_0__seq, dtype=np.float64)
      params_e_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_0__seq))
  params_e_1__raw = params.e[1]
  if isinstance(params_e_1__raw, (str, bytes, dict)):
    params_e_1_ = params_e_1__raw
  else:
    try:
      params_e_1__seq = list(params_e_1__raw)
    except TypeError:
      params_e_1_ = params_e_1__raw
    else:
      params_e_1__seq = np.asarray(params_e_1__seq, dtype=np.float64)
      params_e_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_1__seq))
  params_thetaParam_raw = params.thetaParam
  if isinstance(params_thetaParam_raw, (str, bytes, dict)):
    params_thetaParam = params_thetaParam_raw
  else:
    try:
      params_thetaParam_seq = list(params_thetaParam_raw)
    except TypeError:
      params_thetaParam = params_thetaParam_raw
    else:
      params_thetaParam_seq = np.asarray(params_thetaParam_seq, dtype=np.float64)
      params_thetaParam = np.concatenate((np.array([np.nan], dtype=np.float64), params_thetaParam_seq))

  g = [None, 2 / 3, -0.0139261, 0.183208]

  l = np.array([np.nan, 1.064009, 0.572565], dtype=np.float64)

  phi = lambda malpha, z: (f.opz_pow_n(z, malpha) + f.opz_pow_n(-z, malpha) - 2) / (2 ** malpha - 2)

  lambda_ = (4 / (9 * jnp.pi)) ** (1 / 3)

  a = np.array([np.nan, 0.75, 3.04363, -0.09227, 1.7035, 8.31051, 5.1105], dtype=np.float64)

  bb = lambda b, t: jnp.tanh(1 / jnp.sqrt(t)) * (b[1] + b[2] * t ** 2 + b[3] * t ** 4) / (1 + b[4] * t ** 2 + b[5] * t ** 4)

  ee = lambda e, t: jnp.tanh(1 / t) * (e[1] + e[2] * t ** 2 + e[3] * t ** 4) / (1 + e[4] * t ** 2 + e[5] * t ** 4)

  mtt = lambda rs, z: 2 * (4 / (9 * jnp.pi)) ** (2 / 3) * params_T * rs ** 2 * (1 + params_thetaParam * z) ** (2 / 3)

  alpha = lambda t, rs: 2 - (g[1] + g[2] * rs) / (1 + g[3] * rs) * jnp.exp(-t * (l[1] + l[2] * t * jnp.sqrt(rs)))

  a0 = 1 / (jnp.pi * lambda_)

  dd = lambda d, t: bb(d, t)

  cc = lambda c, e, t: (c[1] + c[2] * jnp.exp(-c[3] / t)) * ee(e, t)

  aa = lambda t: a0 * jnp.tanh(1 / t) * (a[1] + a[2] * t ** 2 + a[3] * t ** 3 + a[4] * t ** 4) / (1 + a[5] * t ** 2 + a[6] * t ** 4)

  fxc = lambda omega, b, c, d, e, rs, t: -(omega * aa(t) + bb(b, t) * jnp.sqrt(rs) + cc(c, e, t) * rs) / (rs * (1 + dd(d, t) * jnp.sqrt(rs) + ee(e, t) * rs))

  functional_body = lambda rs, z: +fxc(1, params_b_0_, params_c_0_, params_d_0_, params_e_0_, rs, mtt(rs, z)) * (1 - phi(alpha(mtt(rs, z), rs), z)) + fxc(2 ** (1 / 3), params_b_1_, params_c_1_, params_d_1_, params_e_1_, rs, mtt(rs, z) / 2 ** (2 / 3)) * phi(alpha(mtt(rs, z), rs), z)

  t1 = 0.1e1 / jnp.pi
  t2 = 4 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = t1 * t3
  t5 = 9 ** (0.1e1 / 0.3e1)
  t6 = t4 * t5
  t7 = t1 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t7
  t9 = t5 ** 2
  t10 = t7 * t1
  t11 = 0.1e1 / t10
  t12 = t9 * t11
  t13 = 0.1e1 / params.T
  t14 = t12 * t13
  t15 = 3 ** (0.1e1 / 0.3e1)
  t16 = r0 + r1
  t17 = t16 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t19 = t15 * t18
  t20 = r0 - r1
  t21 = params.thetaParam * t20
  t22 = 0.1e1 / t16
  t24 = t21 * t22 + 0.1e1
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t31 = jnp.tanh(t14 * t19 * t27 / 0.6e1)
  t32 = t8 * t31
  t33 = jnp.pi ** 2
  t35 = t7 ** 2
  t36 = t35 / t33
  t37 = t9 * t36
  t38 = params.T ** 2
  t39 = t37 * t38
  t41 = 0.1e1 / t17 / t16
  t42 = t15 * t41
  t43 = t25 * t24
  t45 = t39 * t42 * t43
  t47 = t33 ** 2
  t50 = 0.1e1 / t47 * t38 * params.T
  t51 = t16 ** 2
  t52 = 0.1e1 / t51
  t53 = t24 ** 2
  t55 = t50 * t52 * t53
  t59 = t7 / t47 / jnp.pi
  t60 = t5 * t59
  t61 = t38 ** 2
  t62 = t60 * t61
  t63 = t15 ** 2
  t65 = 0.1e1 / t18 / t51
  t66 = t63 * t65
  t67 = t26 * t53
  t69 = t62 * t66 * t67
  t71 = 0.750e0 + 0.45090814814814814814814814814814814814814814814815e0 * t45 - 0.82017777777777777777777777777777777777777777777778e-1 * t55 + 0.33649382716049382716049382716049382716049382716049e0 * t69
  t74 = 0.1e1 + 0.12311866666666666666666666666666666666666666666667e1 * t45 + 0.10094814814814814814814814814814814814814814814815e1 * t69
  t75 = 0.1e1 / t74
  t76 = t71 * t75
  t80 = jnp.sqrt(0.2e1)
  t81 = t5 * t10
  t82 = t81 * params.T
  t83 = 0.1e1 / t18
  t84 = t63 * t83
  t86 = t82 * t84 * t26
  t87 = jnp.sqrt(t86)
  t91 = jnp.tanh(0.3e1 / 0.2e1 * t80 / t87)
  t94 = params_b_0_[1] * t9
  t95 = t94 * t36
  t96 = t38 * t15
  t98 = t96 * t41 * t43
  t102 = params_b_0_[2] * t5
  t103 = t102 * t59
  t104 = t61 * t63
  t106 = t104 * t65 * t67
  t109 = params_b_0_[0] + 0.4e1 / 0.27e2 * t95 * t98 + 0.16e2 / 0.81e2 * t103 * t106
  t110 = t91 * t109
  t112 = params_b_0_[3] * t9
  t113 = t112 * t36
  t117 = params_b_0_[4] * t5
  t118 = t117 * t59
  t121 = 0.1e1 + 0.4e1 / 0.27e2 * t113 * t98 + 0.16e2 / 0.81e2 * t118 * t106
  t122 = 0.1e1 / t121
  t123 = t15 * t7
  t124 = 0.1e1 / t17
  t125 = t3 * t124
  t126 = t123 * t125
  t127 = jnp.sqrt(t126)
  t128 = t122 * t127
  t132 = params_c_0_[1]
  t134 = params_c_0_[2] * t9
  t135 = t134 * t11
  t136 = t13 * t15
  t141 = jnp.exp(-t135 * t136 * t18 * t27 / 0.6e1)
  t143 = t132 * t141 + params_c_0_[0]
  t144 = t143 * t31
  t147 = params_e_0_[1] * t9
  t148 = t147 * t36
  t152 = params_e_0_[2] * t5
  t153 = t152 * t59
  t156 = params_e_0_[0] + 0.4e1 / 0.27e2 * t148 * t98 + 0.16e2 / 0.81e2 * t153 * t106
  t158 = params_e_0_[3] * t9
  t159 = t158 * t36
  t163 = params_e_0_[4] * t5
  t164 = t163 * t59
  t167 = 0.1e1 + 0.4e1 / 0.27e2 * t159 * t98 + 0.16e2 / 0.81e2 * t164 * t106
  t168 = 0.1e1 / t167
  t169 = t156 * t168
  t170 = t144 * t169
  t174 = (t6 * t32 * t76 / 0.4e1 + t110 * t128 / 0.2e1 + t170 * t126 / 0.4e1) * t63
  t175 = t174 * t8
  t176 = t2 * t17
  t179 = params_d_0_[1] * t9
  t180 = t179 * t36
  t184 = params_d_0_[2] * t5
  t185 = t184 * t59
  t188 = params_d_0_[0] + 0.4e1 / 0.27e2 * t180 * t98 + 0.16e2 / 0.81e2 * t185 * t106
  t189 = t91 * t188
  t191 = params_d_0_[3] * t9
  t192 = t191 * t36
  t196 = params_d_0_[4] * t5
  t197 = t196 * t59
  t200 = 0.1e1 + 0.4e1 / 0.27e2 * t192 * t98 + 0.16e2 / 0.81e2 * t197 * t106
  t201 = 0.1e1 / t200
  t202 = t201 * t127
  t205 = t31 * t156
  t206 = t205 * t168
  t209 = 0.1e1 + t189 * t202 / 0.2e1 + t206 * t126 / 0.4e1
  t210 = 0.1e1 / t209
  t211 = t20 * t22
  t212 = 0.1e1 + t211
  t213 = t212 <= f.p.zeta_threshold
  t215 = 0.2e1 / 0.3e1 - 0.34815250000000000000000000000000000000000000000000e-2 * t126
  t217 = 0.1e1 + 0.45802000000000000000000000000000000000000000000000e-1 * t126
  t218 = 0.1e1 / t217
  t219 = t215 * t218
  t220 = t26 * t127
  t224 = 0.1064009e1 + 0.63618333333333333333333333333333333333333333333335e-1 * t82 * t84 * t220
  t225 = t26 * t224
  t229 = jnp.exp(-0.2e1 / 0.9e1 * t82 * t84 * t225)
  t231 = -t219 * t229 + 0.2e1
  t232 = f.p.zeta_threshold ** t231
  t233 = t212 ** t231
  t234 = f.my_piecewise3(t213, t232, t233)
  t235 = 0.1e1 - t211
  t236 = t235 <= f.p.zeta_threshold
  t237 = t235 ** t231
  t238 = f.my_piecewise3(t236, t232, t237)
  t239 = t234 + t238 - 0.2e1
  t240 = 2 ** t231
  t241 = t240 - 0.2e1
  t242 = 0.1e1 / t241
  t243 = t239 * t242
  t244 = 0.1e1 - t243
  t245 = t210 * t244
  t246 = t176 * t245
  t248 = t175 * t246 / 0.3e1
  t249 = 2 ** (0.1e1 / 0.3e1)
  t252 = t249 * t1 * t3 * t5
  t253 = t249 ** 2
  t254 = t27 * t253
  t255 = t19 * t254
  t258 = jnp.tanh(t14 * t255 / 0.6e1)
  t259 = t8 * t258
  t260 = t43 * t253
  t261 = t42 * t260
  t262 = t39 * t261
  t265 = t67 * t249
  t266 = t66 * t265
  t267 = t62 * t266
  t269 = 0.750e0 + 0.11272703703703703703703703703703703703703703703704e0 * t262 - 0.20504444444444444444444444444444444444444444444444e-1 * t55 + 0.42061728395061728395061728395061728395061728395062e-1 * t267
  t272 = 0.1e1 + 0.30779666666666666666666666666666666666666666666667e0 * t262 + 0.12618518518518518518518518518518518518518518518519e0 * t267
  t273 = 0.1e1 / t272
  t278 = t26 * t249
  t280 = t82 * t84 * t278
  t281 = jnp.sqrt(t280)
  t284 = jnp.tanh(0.3e1 / t281)
  t288 = t36 * t38
  t289 = params_b_1_[1] * t9 * t288
  t294 = t59 * t61
  t295 = params_b_1_[2] * t5 * t294
  t298 = params_b_1_[0] + t289 * t261 / 0.27e2 + 0.2e1 / 0.81e2 * t295 * t266
  t299 = t284 * t298
  t302 = params_b_1_[3] * t9 * t288
  t307 = params_b_1_[4] * t5 * t294
  t310 = 0.1e1 + t302 * t261 / 0.27e2 + 0.2e1 / 0.81e2 * t307 * t266
  t311 = 0.1e1 / t310
  t312 = t311 * t127
  t316 = params_c_1_[1]
  t319 = t11 * t13
  t320 = params_c_1_[2] * t9 * t319
  t323 = jnp.exp(-t320 * t255 / 0.6e1)
  t325 = t316 * t323 + params_c_1_[0]
  t326 = t325 * t258
  t330 = params_e_1_[1] * t9 * t288
  t335 = params_e_1_[2] * t5 * t294
  t338 = params_e_1_[0] + t330 * t261 / 0.27e2 + 0.2e1 / 0.81e2 * t335 * t266
  t341 = params_e_1_[3] * t9 * t288
  t346 = params_e_1_[4] * t5 * t294
  t349 = 0.1e1 + t341 * t261 / 0.27e2 + 0.2e1 / 0.81e2 * t346 * t266
  t350 = 0.1e1 / t349
  t351 = t338 * t350
  t352 = t326 * t351
  t356 = (t252 * t259 * t269 * t273 / 0.4e1 + t299 * t312 / 0.2e1 + t352 * t126 / 0.4e1) * t63
  t357 = t8 * t2
  t358 = t356 * t357
  t362 = params_d_1_[1] * t9 * t288
  t367 = params_d_1_[2] * t5 * t294
  t370 = params_d_1_[0] + t362 * t261 / 0.27e2 + 0.2e1 / 0.81e2 * t367 * t266
  t371 = t284 * t370
  t374 = params_d_1_[3] * t9 * t288
  t379 = params_d_1_[4] * t5 * t294
  t382 = 0.1e1 + t374 * t261 / 0.27e2 + 0.2e1 / 0.81e2 * t379 * t266
  t383 = 0.1e1 / t382
  t384 = t383 * t127
  t387 = t258 * t338
  t388 = t387 * t350
  t391 = 0.1e1 + t371 * t384 / 0.2e1 + t388 * t126 / 0.4e1
  t392 = 0.1e1 / t391
  t393 = t17 * t392
  t394 = t393 * t243
  t396 = t358 * t394 / 0.3e1
  t398 = t4 * t5 * t8
  t399 = t31 ** 2
  t400 = 0.1e1 - t399
  t401 = t15 * t124
  t403 = t14 * t401 * t27
  t404 = t26 * t24
  t405 = 0.1e1 / t404
  t406 = params.thetaParam * t22
  t407 = t21 * t52
  t408 = t406 - t407
  t410 = t19 * t405 * t408
  t413 = -t14 * t410 / 0.9e1 + t403 / 0.9e1
  t414 = t400 * t413
  t419 = 0.1e1 / t17 / t51
  t420 = t15 * t419
  t422 = t39 * t420 * t43
  t423 = 0.60121086419753086419753086419753086419753086419753e0 * t422
  t425 = t42 * t25 * t408
  t426 = t39 * t425
  t428 = t51 * t16
  t431 = t50 / t428 * t53
  t432 = 0.16403555555555555555555555555555555555555555555556e0 * t431
  t433 = t52 * t24
  t435 = t50 * t433 * t408
  t438 = 0.1e1 / t18 / t428
  t439 = t63 * t438
  t441 = t62 * t439 * t67
  t442 = 0.89731687242798353909465020576131687242798353909464e0 * t441
  t444 = t66 * t404 * t408
  t445 = t62 * t444
  t452 = t31 * t71
  t453 = t74 ** 2
  t454 = 0.1e1 / t453
  t455 = 0.16415822222222222222222222222222222222222222222223e1 * t422
  t457 = 0.26919506172839506172839506172839506172839506172840e1 * t441
  t464 = t91 ** 2
  t469 = (0.1e1 - t464) * t80 / t87 / t86
  t472 = t63 / t18 / t16
  t474 = t82 * t472 * t26
  t475 = 0.1e1 / t25
  t480 = 0.2e1 / 0.3e1 * t82 * t84 * t475 * t408 - 0.2e1 / 0.3e1 * t474
  t486 = t96 * t419 * t43
  t488 = 0.16e2 / 0.81e2 * t95 * t486
  t489 = t94 * t288
  t493 = t104 * t438 * t67
  t495 = 0.128e3 / 0.243e3 * t103 * t493
  t496 = t102 * t294
  t503 = t121 ** 2
  t505 = 0.1e1 / t503 * t127
  t507 = 0.16e2 / 0.81e2 * t113 * t486
  t508 = t112 * t288
  t512 = 0.128e3 / 0.243e3 * t118 * t493
  t513 = t117 * t294
  t520 = 0.1e1 / t127
  t524 = t123 * t3 * t41
  t526 = t110 * t122 * t520 * t524 / 0.12e2
  t529 = t135 * t136 * t124 * t27
  t530 = t134 * t319
  t536 = t141 * t31 * t156
  t539 = t7 * t3
  t540 = t539 * t124
  t541 = t168 * t15 * t540
  t544 = t143 * t400
  t550 = 0.16e2 / 0.81e2 * t148 * t486
  t551 = t147 * t288
  t555 = 0.128e3 / 0.243e3 * t153 * t493
  t556 = t152 * t294
  t559 = -t550 + 0.16e2 / 0.81e2 * t551 * t425 - t555 + 0.128e3 / 0.243e3 * t556 * t444
  t564 = t167 ** 2
  t565 = 0.1e1 / t564
  t567 = t144 * t156 * t565
  t569 = 0.16e2 / 0.81e2 * t159 * t486
  t570 = t158 * t288
  t574 = 0.128e3 / 0.243e3 * t164 * t493
  t575 = t163 * t294
  t578 = -t569 + 0.16e2 / 0.81e2 * t570 * t425 - t574 + 0.128e3 / 0.243e3 * t575 * t444
  t584 = t170 * t524 / 0.12e2
  t585 = t398 * t414 * t76 / 0.4e1 + t6 * t32 * (-t423 + 0.60121086419753086419753086419753086419753086419753e0 * t426 + t432 - 0.16403555555555555555555555555555555555555555555556e0 * t435 - t442 + 0.89731687242798353909465020576131687242798353909464e0 * t445) * t75 / 0.4e1 - t398 * t452 * t454 * (-t455 + 0.16415822222222222222222222222222222222222222222223e1 * t426 - t457 + 0.26919506172839506172839506172839506172839506172840e1 * t445) / 0.4e1 - 0.3e1 / 0.8e1 * t469 * t480 * t109 * t128 + t91 * (-t488 + 0.16e2 / 0.81e2 * t489 * t425 - t495 + 0.128e3 / 0.243e3 * t496 * t444) * t128 / 0.2e1 - t110 * t505 * (-t507 + 0.16e2 / 0.81e2 * t508 * t425 - t512 + 0.128e3 / 0.243e3 * t513 * t444) / 0.2e1 - t526 + t132 * (t530 * t410 / 0.9e1 - t529 / 0.9e1) * t536 * t541 / 0.4e1 + t544 * t413 * t156 * t541 / 0.4e1 + t144 * t559 * t168 * t126 / 0.4e1 - t567 * t123 * t125 * t578 / 0.4e1 - t584
  t593 = t175 * t2 * t83 * t245 / 0.9e1
  t594 = t174 * t357
  t595 = t209 ** 2
  t597 = t17 / t595
  t603 = 0.16e2 / 0.81e2 * t180 * t486
  t604 = t179 * t288
  t608 = 0.128e3 / 0.243e3 * t185 * t493
  t609 = t184 * t294
  t616 = t200 ** 2
  t618 = 0.1e1 / t616 * t127
  t620 = 0.16e2 / 0.81e2 * t192 * t486
  t621 = t191 * t288
  t625 = 0.128e3 / 0.243e3 * t197 * t493
  t626 = t196 * t294
  t636 = t189 * t201 * t520 * t524 / 0.12e2
  t645 = t205 * t565 * t15
  t651 = t206 * t524 / 0.12e2
  t661 = 0.11605083333333333333333333333333333333333333333333e-2 * t123 * t3 * t41 * t218 * t229
  t662 = t217 ** 2
  t667 = 0.15267333333333333333333333333333333333333333333333e-1 * t215 / t662 * t229 * t524
  t670 = 0.4e1 / 0.27e2 * t82 * t472 * t225
  t672 = t81 * params.T * t63
  t673 = t83 * t475
  t680 = 0.42412222222222222222222222222222222222222222222223e-1 * t82 * t472 * t220
  t692 = 0.31809166666666666666666666666666666666666666666668e-1 * t5 * t35 * t1 * params.T * t52 * t26 * t520 * t3
  t701 = -t661 - t667 - t219 * (t670 - 0.4e1 / 0.27e2 * t672 * t673 * t224 * t408 - 0.2e1 / 0.9e1 * t82 * t84 * t26 * (-t680 + 0.42412222222222222222222222222222222222222222222223e-1 * t672 * t673 * t127 * t408 - t692)) * t229
  t703 = jnp.log(f.p.zeta_threshold)
  t704 = t232 * t701 * t703
  t705 = jnp.log(t212)
  t707 = t20 * t52
  t708 = t22 - t707
  t710 = 0.1e1 / t212
  t714 = f.my_piecewise3(t213, t704, t233 * (t231 * t708 * t710 + t701 * t705))
  t715 = jnp.log(t235)
  t719 = 0.1e1 / t235
  t723 = f.my_piecewise3(t236, t704, t237 * (-t231 * t708 * t719 + t701 * t715))
  t725 = (t714 + t723) * t242
  t726 = t241 ** 2
  t727 = 0.1e1 / t726
  t728 = t239 * t727
  t730 = jnp.log(0.2e1)
  t731 = t240 * t701 * t730
  t738 = t258 ** 2
  t739 = 0.1e1 - t738
  t740 = t8 * t739
  t741 = t401 * t254
  t742 = t14 * t741
  t743 = t12 * t136
  t744 = t18 * t405
  t745 = t253 * t408
  t749 = -t743 * t744 * t745 / 0.9e1 + t742 / 0.9e1
  t755 = t420 * t260
  t756 = t39 * t755
  t757 = 0.15030271604938271604938271604938271604938271604939e0 * t756
  t758 = t37 * t96
  t759 = t41 * t25
  t761 = t758 * t759 * t745
  t763 = 0.41008888888888888888888888888888888888888888888888e-1 * t431
  t765 = t439 * t265
  t766 = t62 * t765
  t767 = 0.11216460905349794238683127572016460905349794238683e0 * t766
  t768 = t60 * t104
  t769 = t65 * t404
  t770 = t249 * t408
  t772 = t768 * t769 * t770
  t779 = t272 ** 2
  t781 = t269 / t779
  t782 = 0.41039555555555555555555555555555555555555555555556e0 * t756
  t784 = 0.33649382716049382716049382716049382716049382716051e0 * t766
  t791 = t284 ** 2
  t795 = (0.1e1 - t791) / t281 / t280
  t797 = t82 * t472 * t278
  t802 = t795 * (0.2e1 / 0.3e1 * t672 * t673 * t770 - 0.2e1 / 0.3e1 * t797)
  t804 = t298 * t311 * t127
  t808 = 0.4e1 / 0.81e2 * t289 * t755
  t809 = t25 * t253
  t811 = t42 * t809 * t408
  t815 = 0.16e2 / 0.243e3 * t295 * t765
  t816 = t404 * t249
  t818 = t66 * t816 * t408
  t825 = t310 ** 2
  t827 = 0.1e1 / t825 * t127
  t829 = 0.4e1 / 0.81e2 * t302 * t755
  t833 = 0.16e2 / 0.243e3 * t307 * t765
  t843 = t299 * t311 * t520 * t524 / 0.12e2
  t844 = t320 * t741
  t845 = t405 * t253
  t853 = t323 * t258 * t338
  t856 = t350 * t15 * t540
  t859 = t325 * t739
  t865 = 0.4e1 / 0.81e2 * t330 * t755
  t869 = 0.16e2 / 0.243e3 * t335 * t765
  t872 = -t865 + 0.4e1 / 0.81e2 * t330 * t811 - t869 + 0.16e2 / 0.243e3 * t335 * t818
  t877 = t349 ** 2
  t878 = 0.1e1 / t877
  t880 = t326 * t338 * t878
  t882 = 0.4e1 / 0.81e2 * t341 * t755
  t886 = 0.16e2 / 0.243e3 * t346 * t765
  t889 = -t882 + 0.4e1 / 0.81e2 * t341 * t811 - t886 + 0.16e2 / 0.243e3 * t346 * t818
  t895 = t352 * t524 / 0.12e2
  t896 = t252 * t740 * t749 * t269 * t273 / 0.4e1 + t252 * t259 * (-t757 + 0.15030271604938271604938271604938271604938271604939e0 * t761 + t763 - 0.41008888888888888888888888888888888888888888888888e-1 * t435 - t767 + 0.11216460905349794238683127572016460905349794238683e0 * t772) * t273 / 0.4e1 - t252 * t259 * t781 * (-t782 + 0.41039555555555555555555555555555555555555555555556e0 * t761 - t784 + 0.33649382716049382716049382716049382716049382716051e0 * t772) / 0.4e1 - 0.3e1 / 0.4e1 * t802 * t804 + t284 * (-t808 + 0.4e1 / 0.81e2 * t289 * t811 - t815 + 0.16e2 / 0.243e3 * t295 * t818) * t312 / 0.2e1 - t299 * t827 * (-t829 + 0.4e1 / 0.81e2 * t302 * t811 - t833 + 0.16e2 / 0.243e3 * t307 * t818) / 0.2e1 - t843 + t316 * (t320 * t19 * t845 * t408 / 0.9e1 - t844 / 0.9e1) * t853 * t856 / 0.4e1 + t859 * t749 * t338 * t856 / 0.4e1 + t326 * t872 * t350 * t126 / 0.4e1 - t880 * t123 * t125 * t889 / 0.4e1 - t895
  t904 = t358 * t83 * t392 * t243 / 0.9e1
  t905 = t391 ** 2
  t907 = t17 / t905
  t909 = t370 * t383 * t127
  t913 = 0.4e1 / 0.81e2 * t362 * t755
  t917 = 0.16e2 / 0.243e3 * t367 * t765
  t924 = t382 ** 2
  t926 = 0.1e1 / t924 * t127
  t928 = 0.4e1 / 0.81e2 * t374 * t755
  t932 = 0.16e2 / 0.243e3 * t379 * t765
  t942 = t371 * t383 * t520 * t524 / 0.12e2
  t952 = t387 * t878 * t15
  t958 = t388 * t524 / 0.12e2
  t968 = t356 * t357 * t17
  t970 = t392 * t239 * t727
  vrho_0_ = -t248 - t396 + t16 * (-t585 * t63 * t8 * t246 / 0.3e1 - t593 + t594 * t597 * t244 * (-0.3e1 / 0.8e1 * t469 * t480 * t188 * t202 + t91 * (-t603 + 0.16e2 / 0.81e2 * t604 * t425 - t608 + 0.128e3 / 0.243e3 * t609 * t444) * t202 / 0.2e1 - t189 * t618 * (-t620 + 0.16e2 / 0.81e2 * t621 * t425 - t625 + 0.128e3 / 0.243e3 * t626 * t444) / 0.2e1 - t636 + t414 * t169 * t126 / 0.4e1 + t31 * t559 * t168 * t126 / 0.4e1 - t645 * t539 * t124 * t578 / 0.4e1 - t651) / 0.3e1 - t175 * t176 * t210 * (t728 * t731 - t725) / 0.3e1 - t896 * t63 * t357 * t394 / 0.3e1 - t904 + t358 * t907 * t243 * (-0.3e1 / 0.4e1 * t802 * t909 + t284 * (-t913 + 0.4e1 / 0.81e2 * t362 * t811 - t917 + 0.16e2 / 0.243e3 * t367 * t818) * t384 / 0.2e1 - t371 * t926 * (-t928 + 0.4e1 / 0.81e2 * t374 * t811 - t932 + 0.16e2 / 0.243e3 * t379 * t818) / 0.2e1 - t942 + t739 * t749 * t351 * t126 / 0.4e1 + t258 * t872 * t350 * t126 / 0.4e1 - t952 * t539 * t124 * t889 / 0.4e1 - t958) / 0.3e1 - t358 * t393 * t725 / 0.3e1 + t968 * t970 * t731 / 0.3e1)
  t976 = -t406 - t407
  t978 = t19 * t405 * t976
  t981 = -t14 * t978 / 0.9e1 + t403 / 0.9e1
  t982 = t400 * t981
  t987 = t42 * t25 * t976
  t988 = t39 * t987
  t991 = t50 * t433 * t976
  t994 = t66 * t404 * t976
  t995 = t62 * t994
  t1013 = 0.2e1 / 0.3e1 * t82 * t84 * t475 * t976 - 0.2e1 / 0.3e1 * t474
  t1049 = -t550 + 0.16e2 / 0.81e2 * t551 * t987 - t555 + 0.128e3 / 0.243e3 * t556 * t994
  t1058 = -t569 + 0.16e2 / 0.81e2 * t570 * t987 - t574 + 0.128e3 / 0.243e3 * t575 * t994
  t1063 = t398 * t982 * t76 / 0.4e1 + t6 * t32 * (-t423 + 0.60121086419753086419753086419753086419753086419753e0 * t988 + t432 - 0.16403555555555555555555555555555555555555555555556e0 * t991 - t442 + 0.89731687242798353909465020576131687242798353909464e0 * t995) * t75 / 0.4e1 - t398 * t452 * t454 * (-t455 + 0.16415822222222222222222222222222222222222222222223e1 * t988 - t457 + 0.26919506172839506172839506172839506172839506172840e1 * t995) / 0.4e1 - 0.3e1 / 0.8e1 * t469 * t1013 * t109 * t128 + t91 * (-t488 + 0.16e2 / 0.81e2 * t489 * t987 - t495 + 0.128e3 / 0.243e3 * t496 * t994) * t128 / 0.2e1 - t110 * t505 * (-t507 + 0.16e2 / 0.81e2 * t508 * t987 - t512 + 0.128e3 / 0.243e3 * t513 * t994) / 0.2e1 - t526 + t132 * (t530 * t978 / 0.9e1 - t529 / 0.9e1) * t536 * t541 / 0.4e1 + t544 * t981 * t156 * t541 / 0.4e1 + t144 * t1049 * t168 * t126 / 0.4e1 - t567 * t123 * t125 * t1058 / 0.4e1 - t584
  t1120 = -t661 - t667 - t219 * (t670 - 0.4e1 / 0.27e2 * t672 * t673 * t224 * t976 - 0.2e1 / 0.9e1 * t82 * t84 * t26 * (-t680 + 0.42412222222222222222222222222222222222222222222223e-1 * t672 * t673 * t127 * t976 - t692)) * t229
  t1122 = t232 * t1120 * t703
  t1124 = -t22 - t707
  t1129 = f.my_piecewise3(t213, t1122, t233 * (t231 * t1124 * t710 + t1120 * t705))
  t1136 = f.my_piecewise3(t236, t1122, t237 * (-t231 * t1124 * t719 + t1120 * t715))
  t1138 = (t1129 + t1136) * t242
  t1140 = t240 * t1120 * t730
  t1147 = t253 * t976
  t1151 = -t743 * t744 * t1147 / 0.9e1 + t742 / 0.9e1
  t1158 = t758 * t759 * t1147
  t1161 = t249 * t976
  t1163 = t768 * t769 * t1161
  t1181 = t795 * (0.2e1 / 0.3e1 * t672 * t673 * t1161 - 0.2e1 / 0.3e1 * t797)
  t1185 = t42 * t809 * t976
  t1189 = t66 * t816 * t976
  t1221 = -t865 + 0.4e1 / 0.81e2 * t330 * t1185 - t869 + 0.16e2 / 0.243e3 * t335 * t1189
  t1230 = -t882 + 0.4e1 / 0.81e2 * t341 * t1185 - t886 + 0.16e2 / 0.243e3 * t346 * t1189
  t1235 = t252 * t740 * t1151 * t269 * t273 / 0.4e1 + t252 * t259 * (-t757 + 0.15030271604938271604938271604938271604938271604939e0 * t1158 + t763 - 0.41008888888888888888888888888888888888888888888888e-1 * t991 - t767 + 0.11216460905349794238683127572016460905349794238683e0 * t1163) * t273 / 0.4e1 - t252 * t259 * t781 * (-t782 + 0.41039555555555555555555555555555555555555555555556e0 * t1158 - t784 + 0.33649382716049382716049382716049382716049382716051e0 * t1163) / 0.4e1 - 0.3e1 / 0.4e1 * t1181 * t804 + t284 * (-t808 + 0.4e1 / 0.81e2 * t289 * t1185 - t815 + 0.16e2 / 0.243e3 * t295 * t1189) * t312 / 0.2e1 - t299 * t827 * (-t829 + 0.4e1 / 0.81e2 * t302 * t1185 - t833 + 0.16e2 / 0.243e3 * t307 * t1189) / 0.2e1 - t843 + t316 * (t320 * t19 * t845 * t976 / 0.9e1 - t844 / 0.9e1) * t853 * t856 / 0.4e1 + t859 * t1151 * t338 * t856 / 0.4e1 + t326 * t1221 * t350 * t126 / 0.4e1 - t880 * t123 * t125 * t1230 / 0.4e1 - t895
  vrho_1_ = -t248 - t396 + t16 * (-t1063 * t63 * t8 * t246 / 0.3e1 - t593 + t594 * t597 * t244 * (-0.3e1 / 0.8e1 * t469 * t1013 * t188 * t202 + t91 * (-t603 + 0.16e2 / 0.81e2 * t604 * t987 - t608 + 0.128e3 / 0.243e3 * t609 * t994) * t202 / 0.2e1 - t189 * t618 * (-t620 + 0.16e2 / 0.81e2 * t621 * t987 - t625 + 0.128e3 / 0.243e3 * t626 * t994) / 0.2e1 - t636 + t982 * t169 * t126 / 0.4e1 + t31 * t1049 * t168 * t126 / 0.4e1 - t645 * t539 * t124 * t1058 / 0.4e1 - t651) / 0.3e1 - t175 * t176 * t210 * (t728 * t1140 - t1138) / 0.3e1 - t1235 * t63 * t357 * t394 / 0.3e1 - t904 + t358 * t907 * t243 * (-0.3e1 / 0.4e1 * t1181 * t909 + t284 * (-t913 + 0.4e1 / 0.81e2 * t362 * t1185 - t917 + 0.16e2 / 0.243e3 * t367 * t1189) * t384 / 0.2e1 - t371 * t926 * (-t928 + 0.4e1 / 0.81e2 * t374 * t1185 - t932 + 0.16e2 / 0.243e3 * t379 * t1189) / 0.2e1 - t942 + t739 * t1151 * t351 * t126 / 0.4e1 + t258 * t1221 * t350 * t126 / 0.4e1 - t952 * t539 * t124 * t1230 / 0.4e1 - t958) / 0.3e1 - t358 * t393 * t1138 / 0.3e1 + t968 * t970 * t1140 / 0.3e1)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_T_raw = params.T
  if isinstance(params_T_raw, (str, bytes, dict)):
    params_T = params_T_raw
  else:
    try:
      params_T_seq = list(params_T_raw)
    except TypeError:
      params_T = params_T_raw
    else:
      params_T_seq = np.asarray(params_T_seq, dtype=np.float64)
      params_T = np.concatenate((np.array([np.nan], dtype=np.float64), params_T_seq))
  params_b_0__raw = params.b[0]
  if isinstance(params_b_0__raw, (str, bytes, dict)):
    params_b_0_ = params_b_0__raw
  else:
    try:
      params_b_0__seq = list(params_b_0__raw)
    except TypeError:
      params_b_0_ = params_b_0__raw
    else:
      params_b_0__seq = np.asarray(params_b_0__seq, dtype=np.float64)
      params_b_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_0__seq))
  params_b_1__raw = params.b[1]
  if isinstance(params_b_1__raw, (str, bytes, dict)):
    params_b_1_ = params_b_1__raw
  else:
    try:
      params_b_1__seq = list(params_b_1__raw)
    except TypeError:
      params_b_1_ = params_b_1__raw
    else:
      params_b_1__seq = np.asarray(params_b_1__seq, dtype=np.float64)
      params_b_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_1__seq))
  params_c_0__raw = params.c[0]
  if isinstance(params_c_0__raw, (str, bytes, dict)):
    params_c_0_ = params_c_0__raw
  else:
    try:
      params_c_0__seq = list(params_c_0__raw)
    except TypeError:
      params_c_0_ = params_c_0__raw
    else:
      params_c_0__seq = np.asarray(params_c_0__seq, dtype=np.float64)
      params_c_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_0__seq))
  params_c_1__raw = params.c[1]
  if isinstance(params_c_1__raw, (str, bytes, dict)):
    params_c_1_ = params_c_1__raw
  else:
    try:
      params_c_1__seq = list(params_c_1__raw)
    except TypeError:
      params_c_1_ = params_c_1__raw
    else:
      params_c_1__seq = np.asarray(params_c_1__seq, dtype=np.float64)
      params_c_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_1__seq))
  params_d_0__raw = params.d[0]
  if isinstance(params_d_0__raw, (str, bytes, dict)):
    params_d_0_ = params_d_0__raw
  else:
    try:
      params_d_0__seq = list(params_d_0__raw)
    except TypeError:
      params_d_0_ = params_d_0__raw
    else:
      params_d_0__seq = np.asarray(params_d_0__seq, dtype=np.float64)
      params_d_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_0__seq))
  params_d_1__raw = params.d[1]
  if isinstance(params_d_1__raw, (str, bytes, dict)):
    params_d_1_ = params_d_1__raw
  else:
    try:
      params_d_1__seq = list(params_d_1__raw)
    except TypeError:
      params_d_1_ = params_d_1__raw
    else:
      params_d_1__seq = np.asarray(params_d_1__seq, dtype=np.float64)
      params_d_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_1__seq))
  params_e_0__raw = params.e[0]
  if isinstance(params_e_0__raw, (str, bytes, dict)):
    params_e_0_ = params_e_0__raw
  else:
    try:
      params_e_0__seq = list(params_e_0__raw)
    except TypeError:
      params_e_0_ = params_e_0__raw
    else:
      params_e_0__seq = np.asarray(params_e_0__seq, dtype=np.float64)
      params_e_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_0__seq))
  params_e_1__raw = params.e[1]
  if isinstance(params_e_1__raw, (str, bytes, dict)):
    params_e_1_ = params_e_1__raw
  else:
    try:
      params_e_1__seq = list(params_e_1__raw)
    except TypeError:
      params_e_1_ = params_e_1__raw
    else:
      params_e_1__seq = np.asarray(params_e_1__seq, dtype=np.float64)
      params_e_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_1__seq))
  params_thetaParam_raw = params.thetaParam
  if isinstance(params_thetaParam_raw, (str, bytes, dict)):
    params_thetaParam = params_thetaParam_raw
  else:
    try:
      params_thetaParam_seq = list(params_thetaParam_raw)
    except TypeError:
      params_thetaParam = params_thetaParam_raw
    else:
      params_thetaParam_seq = np.asarray(params_thetaParam_seq, dtype=np.float64)
      params_thetaParam = np.concatenate((np.array([np.nan], dtype=np.float64), params_thetaParam_seq))

  g = [None, 2 / 3, -0.0139261, 0.183208]

  l = np.array([np.nan, 1.064009, 0.572565], dtype=np.float64)

  phi = lambda malpha, z: (f.opz_pow_n(z, malpha) + f.opz_pow_n(-z, malpha) - 2) / (2 ** malpha - 2)

  lambda_ = (4 / (9 * jnp.pi)) ** (1 / 3)

  a = np.array([np.nan, 0.75, 3.04363, -0.09227, 1.7035, 8.31051, 5.1105], dtype=np.float64)

  bb = lambda b, t: jnp.tanh(1 / jnp.sqrt(t)) * (b[1] + b[2] * t ** 2 + b[3] * t ** 4) / (1 + b[4] * t ** 2 + b[5] * t ** 4)

  ee = lambda e, t: jnp.tanh(1 / t) * (e[1] + e[2] * t ** 2 + e[3] * t ** 4) / (1 + e[4] * t ** 2 + e[5] * t ** 4)

  mtt = lambda rs, z: 2 * (4 / (9 * jnp.pi)) ** (2 / 3) * params_T * rs ** 2 * (1 + params_thetaParam * z) ** (2 / 3)

  alpha = lambda t, rs: 2 - (g[1] + g[2] * rs) / (1 + g[3] * rs) * jnp.exp(-t * (l[1] + l[2] * t * jnp.sqrt(rs)))

  a0 = 1 / (jnp.pi * lambda_)

  dd = lambda d, t: bb(d, t)

  cc = lambda c, e, t: (c[1] + c[2] * jnp.exp(-c[3] / t)) * ee(e, t)

  aa = lambda t: a0 * jnp.tanh(1 / t) * (a[1] + a[2] * t ** 2 + a[3] * t ** 3 + a[4] * t ** 4) / (1 + a[5] * t ** 2 + a[6] * t ** 4)

  fxc = lambda omega, b, c, d, e, rs, t: -(omega * aa(t) + bb(b, t) * jnp.sqrt(rs) + cc(c, e, t) * rs) / (rs * (1 + dd(d, t) * jnp.sqrt(rs) + ee(e, t) * rs))

  functional_body = lambda rs, z: +fxc(1, params_b_0_, params_c_0_, params_d_0_, params_e_0_, rs, mtt(rs, z)) * (1 - phi(alpha(mtt(rs, z), rs), z)) + fxc(2 ** (1 / 3), params_b_1_, params_c_1_, params_d_1_, params_e_1_, rs, mtt(rs, z) / 2 ** (2 / 3)) * phi(alpha(mtt(rs, z), rs), z)

  t1 = 0.1e1 / jnp.pi
  t2 = 4 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = t1 * t3
  t5 = 9 ** (0.1e1 / 0.3e1)
  t6 = t4 * t5
  t7 = t1 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t7
  t9 = t5 ** 2
  t10 = t7 * t1
  t11 = 0.1e1 / t10
  t12 = t9 * t11
  t13 = 0.1e1 / params.T
  t14 = 3 ** (0.1e1 / 0.3e1)
  t15 = t13 * t14
  t16 = r0 ** (0.1e1 / 0.3e1)
  t17 = t16 ** 2
  t18 = t15 * t17
  t21 = jnp.tanh(t12 * t18 / 0.6e1)
  t22 = t8 * t21
  t23 = jnp.pi ** 2
  t25 = t7 ** 2
  t26 = t25 / t23
  t27 = t9 * t26
  t28 = params.T ** 2
  t29 = t28 * t14
  t31 = 0.1e1 / t16 / r0
  t32 = t29 * t31
  t33 = t27 * t32
  t35 = t23 ** 2
  t38 = 0.1e1 / t35 * t28 * params.T
  t39 = r0 ** 2
  t40 = 0.1e1 / t39
  t41 = t38 * t40
  t45 = t7 / t35 / jnp.pi
  t46 = t5 * t45
  t47 = t28 ** 2
  t48 = t14 ** 2
  t49 = t47 * t48
  t51 = 0.1e1 / t17 / t39
  t52 = t49 * t51
  t53 = t46 * t52
  t55 = 0.750e0 + 0.45090814814814814814814814814814814814814814814815e0 * t33 - 0.82017777777777777777777777777777777777777777777778e-1 * t41 + 0.33649382716049382716049382716049382716049382716049e0 * t53
  t58 = 0.1e1 + 0.12311866666666666666666666666666666666666666666667e1 * t33 + 0.10094814814814814814814814814814814814814814814815e1 * t53
  t59 = 0.1e1 / t58
  t64 = jnp.sqrt(0.2e1)
  t65 = t5 * t10
  t66 = params.T * t48
  t67 = 0.1e1 / t17
  t69 = t65 * t66 * t67
  t70 = jnp.sqrt(t69)
  t74 = jnp.tanh(0.3e1 / 0.2e1 * t64 / t70)
  t78 = params_b_0_[1] * t9 * t26
  t83 = params_b_0_[2] * t5 * t45
  t86 = params_b_0_[0] + 0.4e1 / 0.27e2 * t78 * t32 + 0.16e2 / 0.81e2 * t83 * t52
  t87 = t74 * t86
  t90 = params_b_0_[3] * t9 * t26
  t95 = params_b_0_[4] * t5 * t45
  t98 = 0.1e1 + 0.4e1 / 0.27e2 * t90 * t32 + 0.16e2 / 0.81e2 * t95 * t52
  t99 = 0.1e1 / t98
  t100 = t14 * t7
  t101 = 0.1e1 / t16
  t102 = t3 * t101
  t103 = t100 * t102
  t104 = jnp.sqrt(t103)
  t105 = t99 * t104
  t109 = params_c_0_[1]
  t110 = params_c_0_[2]
  t115 = jnp.exp(-t110 * t9 * t11 * t18 / 0.6e1)
  t117 = t109 * t115 + params_c_0_[0]
  t118 = t117 * t21
  t122 = params_e_0_[1] * t9 * t26
  t127 = params_e_0_[2] * t5 * t45
  t130 = params_e_0_[0] + 0.4e1 / 0.27e2 * t122 * t32 + 0.16e2 / 0.81e2 * t127 * t52
  t133 = params_e_0_[3] * t9 * t26
  t138 = params_e_0_[4] * t5 * t45
  t141 = 0.1e1 + 0.4e1 / 0.27e2 * t133 * t32 + 0.16e2 / 0.81e2 * t138 * t52
  t142 = 0.1e1 / t141
  t143 = t130 * t142
  t144 = t118 * t143
  t148 = (t6 * t22 * t55 * t59 / 0.4e1 + t87 * t105 / 0.2e1 + t144 * t103 / 0.4e1) * t48
  t149 = t148 * t8
  t150 = t2 * t16
  t154 = params_d_0_[1] * t9 * t26
  t159 = params_d_0_[2] * t5 * t45
  t162 = params_d_0_[0] + 0.4e1 / 0.27e2 * t154 * t32 + 0.16e2 / 0.81e2 * t159 * t52
  t163 = t74 * t162
  t166 = params_d_0_[3] * t9 * t26
  t171 = params_d_0_[4] * t5 * t45
  t174 = 0.1e1 + 0.4e1 / 0.27e2 * t166 * t32 + 0.16e2 / 0.81e2 * t171 * t52
  t175 = 0.1e1 / t174
  t176 = t175 * t104
  t179 = t21 * t130
  t180 = t179 * t142
  t183 = 0.1e1 + t163 * t176 / 0.2e1 + t180 * t103 / 0.4e1
  t184 = 0.1e1 / t183
  t185 = 0.1e1 <= f.p.zeta_threshold
  t187 = 0.2e1 / 0.3e1 - 0.34815250000000000000000000000000000000000000000000e-2 * t103
  t189 = 0.1e1 + 0.45802000000000000000000000000000000000000000000000e-1 * t103
  t190 = 0.1e1 / t189
  t191 = t187 * t190
  t192 = t65 * params.T
  t193 = t48 * t67
  t197 = 0.1064009e1 + 0.63618333333333333333333333333333333333333333333335e-1 * t192 * t193 * t104
  t201 = jnp.exp(-0.2e1 / 0.9e1 * t192 * t193 * t197)
  t203 = -t191 * t201 + 0.2e1
  t204 = f.p.zeta_threshold ** t203
  t205 = f.my_piecewise3(t185, t204, 1)
  t207 = 0.2e1 * t205 - 0.2e1
  t208 = 2 ** t203
  t209 = t208 - 0.2e1
  t210 = 0.1e1 / t209
  t211 = t207 * t210
  t212 = 0.1e1 - t211
  t213 = t184 * t212
  t214 = t150 * t213
  t217 = 2 ** (0.1e1 / 0.3e1)
  t220 = t217 * t1 * t3 * t5
  t223 = t217 ** 2
  t227 = jnp.tanh(t12 * t13 * t14 * t17 * t223 / 0.6e1)
  t228 = t8 * t227
  t229 = t27 * t28
  t232 = t229 * t14 * t31 * t223
  t235 = t46 * t47
  t238 = t235 * t48 * t51 * t217
  t240 = 0.750e0 + 0.11272703703703703703703703703703703703703703703704e0 * t232 - 0.20504444444444444444444444444444444444444444444444e-1 * t41 + 0.42061728395061728395061728395061728395061728395062e-1 * t238
  t243 = 0.1e1 + 0.30779666666666666666666666666666666666666666666667e0 * t232 + 0.12618518518518518518518518518518518518518518518519e0 * t238
  t244 = 0.1e1 / t243
  t250 = t192 * t193 * t217
  t251 = jnp.sqrt(t250)
  t254 = jnp.tanh(0.3e1 / t251)
  t258 = params_b_1_[1] * t9 * t26
  t260 = t29 * t31 * t223
  t265 = params_b_1_[2] * t5 * t45
  t267 = t49 * t51 * t217
  t270 = params_b_1_[0] + t258 * t260 / 0.27e2 + 0.2e1 / 0.81e2 * t265 * t267
  t271 = t254 * t270
  t274 = params_b_1_[3] * t9 * t26
  t279 = params_b_1_[4] * t5 * t45
  t282 = 0.1e1 + t274 * t260 / 0.27e2 + 0.2e1 / 0.81e2 * t279 * t267
  t283 = 0.1e1 / t282
  t284 = t283 * t104
  t288 = params_c_1_[1]
  t289 = params_c_1_[2]
  t296 = jnp.exp(-t289 * t9 * t11 * t15 * t17 * t223 / 0.6e1)
  t298 = t288 * t296 + params_c_1_[0]
  t299 = t298 * t227
  t303 = params_e_1_[1] * t9 * t26
  t308 = params_e_1_[2] * t5 * t45
  t311 = params_e_1_[0] + t303 * t260 / 0.27e2 + 0.2e1 / 0.81e2 * t308 * t267
  t314 = params_e_1_[3] * t9 * t26
  t319 = params_e_1_[4] * t5 * t45
  t322 = 0.1e1 + t314 * t260 / 0.27e2 + 0.2e1 / 0.81e2 * t319 * t267
  t323 = 0.1e1 / t322
  t324 = t311 * t323
  t325 = t299 * t324
  t329 = (t220 * t228 * t240 * t244 / 0.4e1 + t271 * t284 / 0.2e1 + t325 * t103 / 0.4e1) * t48
  t330 = t8 * t2
  t331 = t329 * t330
  t335 = params_d_1_[1] * t9 * t26
  t340 = params_d_1_[2] * t5 * t45
  t343 = params_d_1_[0] + t335 * t260 / 0.27e2 + 0.2e1 / 0.81e2 * t340 * t267
  t344 = t254 * t343
  t347 = params_d_1_[3] * t9 * t26
  t352 = params_d_1_[4] * t5 * t45
  t355 = 0.1e1 + t347 * t260 / 0.27e2 + 0.2e1 / 0.81e2 * t352 * t267
  t356 = 0.1e1 / t355
  t357 = t356 * t104
  t360 = t227 * t311
  t361 = t360 * t323
  t364 = 0.1e1 + t344 * t357 / 0.2e1 + t361 * t103 / 0.4e1
  t365 = 0.1e1 / t364
  t366 = t16 * t365
  t367 = t366 * t211
  t370 = t25 * t1
  t371 = 0.1e1 / t370
  t372 = t21 ** 2
  t373 = 0.1e1 - t372
  t382 = 0.1e1 / t16 / t39
  t383 = t29 * t382
  t384 = t27 * t383
  t386 = t39 * r0
  t388 = t38 / t386
  t391 = 0.1e1 / t17 / t386
  t392 = t49 * t391
  t393 = t46 * t392
  t403 = t58 ** 2
  t412 = t74 ** 2
  t419 = (0.1e1 - t412) * t64 / t70 / t69 * t5 * t10
  t421 = 0.1e1 / t17 / r0
  t422 = t66 * t421
  t436 = t98 ** 2
  t447 = 0.1e1 / t104
  t451 = t100 * t3 * t31
  t456 = jnp.pi * t13
  t457 = t456 * t48
  t461 = t143 * t3
  t467 = t9 * jnp.pi * t13
  t469 = t193 * t461
  t476 = -0.16e2 / 0.81e2 * t122 * t383 - 0.128e3 / 0.243e3 * t127 * t392
  t481 = t141 ** 2
  t482 = 0.1e1 / t481
  t489 = -0.16e2 / 0.81e2 * t133 * t383 - 0.128e3 / 0.243e3 * t138 * t392
  t496 = t4 * t371 * t373 * t15 * t101 * t55 * t59 / 0.4e1 + t6 * t22 * (-0.60121086419753086419753086419753086419753086419753e0 * t384 + 0.16403555555555555555555555555555555555555555555556e0 * t388 - 0.89731687242798353909465020576131687242798353909464e0 * t393) * t59 / 0.4e1 - t4 * t5 * t8 * t21 * t55 / t403 * (-0.16415822222222222222222222222222222222222222222223e1 * t384 - 0.26919506172839506172839506172839506172839506172840e1 * t393) / 0.4e1 + t419 * t422 * t86 * t99 * t104 / 0.4e1 + t74 * (-0.16e2 / 0.81e2 * t78 * t383 - 0.128e3 / 0.243e3 * t83 * t392) * t105 / 0.2e1 - t87 / t436 * t104 * (-0.16e2 / 0.81e2 * t90 * t383 - 0.128e3 / 0.243e3 * t95 * t392) / 0.2e1 - t87 * t99 * t447 * t451 / 0.12e2 - t109 * t110 * t9 * t457 * t67 * t115 * t21 * t461 / 0.36e2 + t117 * t373 * t467 * t469 / 0.36e2 + t118 * t476 * t142 * t103 / 0.4e1 - t118 * t130 * t482 * t100 * t102 * t489 / 0.4e1 - t144 * t451 / 0.12e2
  t506 = t183 ** 2
  t522 = t174 ** 2
  t547 = t7 * t3
  t564 = t189 ** 2
  t570 = t48 * t421
  t590 = -0.11605083333333333333333333333333333333333333333333e-2 * t100 * t3 * t31 * t190 * t201 - 0.15267333333333333333333333333333333333333333333333e-1 * t187 / t564 * t201 * t451 - t191 * (0.4e1 / 0.27e2 * t192 * t570 * t197 - 0.2e1 / 0.9e1 * t192 * t193 * (-0.42412222222222222222222222222222222222222222222223e-1 * t192 * t570 * t104 - 0.31809166666666666666666666666666666666666666666668e-1 * t5 * t370 * params.T * t40 * t447 * t3)) * t201
  t592 = jnp.log(f.p.zeta_threshold)
  t594 = f.my_piecewise3(t185, t204 * t590 * t592, 0)
  t595 = t594 * t210
  t597 = t209 ** 2
  t598 = 0.1e1 / t597
  t601 = jnp.log(0.2e1)
  t602 = t208 * t590 * t601
  t609 = t227 ** 2
  t610 = 0.1e1 - t609
  t620 = t229 * t14 * t382 * t223
  t625 = t235 * t48 * t391 * t217
  t632 = t243 ** 2
  t642 = t254 ** 2
  t647 = (0.1e1 - t642) / t251 / t250 * t192
  t648 = t570 * t217
  t655 = t29 * t382 * t223
  t659 = t49 * t391 * t217
  t666 = t282 ** 2
  t684 = t67 * t223
  t694 = t324 * t3
  t702 = -0.4e1 / 0.81e2 * t303 * t655 - 0.16e2 / 0.243e3 * t308 * t659
  t707 = t322 ** 2
  t708 = 0.1e1 / t707
  t715 = -0.4e1 / 0.81e2 * t314 * t655 - 0.16e2 / 0.243e3 * t319 * t659
  t722 = t4 * t371 * t610 * t15 * t101 * t240 * t244 / 0.2e1 + t220 * t228 * (-0.15030271604938271604938271604938271604938271604939e0 * t620 + 0.41008888888888888888888888888888888888888888888888e-1 * t388 - 0.11216460905349794238683127572016460905349794238683e0 * t625) * t244 / 0.4e1 - t220 * t228 * t240 / t632 * (-0.41039555555555555555555555555555555555555555555556e0 * t620 - 0.33649382716049382716049382716049382716049382716051e0 * t625) / 0.4e1 + t647 * t648 * t270 * t283 * t104 / 0.2e1 + t254 * (-0.4e1 / 0.81e2 * t258 * t655 - 0.16e2 / 0.243e3 * t265 * t659) * t284 / 0.2e1 - t271 / t666 * t104 * (-0.4e1 / 0.81e2 * t274 * t655 - 0.16e2 / 0.243e3 * t279 * t659) / 0.2e1 - t271 * t283 * t447 * t451 / 0.12e2 - t288 * t289 * t9 * t457 * t684 * t296 * t360 * t323 * t3 / 0.36e2 + t298 * t610 * t467 * t193 * t223 * t694 / 0.36e2 + t299 * t702 * t323 * t103 / 0.4e1 - t299 * t311 * t708 * t100 * t102 * t715 / 0.4e1 - t325 * t451 / 0.12e2
  t731 = t364 ** 2
  t747 = t355 ** 2
  vrho_0_ = -t149 * t214 / 0.3e1 - t331 * t367 / 0.3e1 + r0 * (-t496 * t48 * t8 * t214 / 0.3e1 - t149 * t2 * t67 * t213 / 0.9e1 + t148 * t330 * t16 / t506 * t212 * (t419 * t422 * t162 * t175 * t104 / 0.4e1 + t74 * (-0.16e2 / 0.81e2 * t154 * t383 - 0.128e3 / 0.243e3 * t159 * t392) * t176 / 0.2e1 - t163 / t522 * t104 * (-0.16e2 / 0.81e2 * t166 * t383 - 0.128e3 / 0.243e3 * t171 * t392) / 0.2e1 - t163 * t175 * t447 * t451 / 0.12e2 + t373 * t9 * t456 * t469 / 0.36e2 + t21 * t476 * t142 * t103 / 0.4e1 - t179 * t482 * t14 * t547 * t101 * t489 / 0.4e1 - t180 * t451 / 0.12e2) / 0.3e1 - t149 * t150 * t184 * (t207 * t598 * t602 - 0.2e1 * t595) / 0.3e1 - t722 * t48 * t330 * t367 / 0.3e1 - t331 * t67 * t365 * t211 / 0.9e1 + t331 * t16 / t731 * t211 * (t647 * t648 * t343 * t356 * t104 / 0.2e1 + t254 * (-0.4e1 / 0.81e2 * t335 * t655 - 0.16e2 / 0.243e3 * t340 * t659) * t357 / 0.2e1 - t344 / t747 * t104 * (-0.4e1 / 0.81e2 * t347 * t655 - 0.16e2 / 0.243e3 * t352 * t659) / 0.2e1 - t344 * t356 * t447 * t451 / 0.12e2 + t610 * t9 * t457 * t684 * t694 / 0.36e2 + t227 * t702 * t323 * t103 / 0.4e1 - t360 * t708 * t14 * t547 * t101 * t715 / 0.4e1 - t361 * t451 / 0.12e2) / 0.3e1 - 0.2e1 / 0.3e1 * t331 * t366 * t595 + t329 * t330 * t16 * t365 * t207 * t598 * t602 / 0.3e1)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 0.1e1 / jnp.pi
  t2 = 4 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = t1 * t3
  t5 = t1 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = t6 * t1
  t8 = 0.1e1 / t7
  t9 = 9 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = t5 * t1
  t12 = 0.1e1 / t11
  t13 = t10 * t12
  t14 = 0.1e1 / params.T
  t15 = 3 ** (0.1e1 / 0.3e1)
  t16 = t14 * t15
  t17 = r0 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t19 = t16 * t18
  t22 = jnp.tanh(t13 * t19 / 0.6e1)
  t23 = t22 ** 2
  t24 = 0.1e1 - t23
  t25 = t8 * t24
  t26 = t4 * t25
  t27 = 0.1e1 / t17
  t28 = jnp.pi ** 2
  t29 = 0.1e1 / t28
  t30 = t6 * t29
  t31 = t10 * t30
  t32 = params.T ** 2
  t33 = t32 * t15
  t35 = 0.1e1 / t17 / r0
  t36 = t33 * t35
  t37 = t31 * t36
  t39 = t28 ** 2
  t42 = 0.1e1 / t39 * t32 * params.T
  t43 = r0 ** 2
  t44 = 0.1e1 / t43
  t45 = t42 * t44
  t49 = t5 / t39 / jnp.pi
  t50 = t9 * t49
  t51 = t32 ** 2
  t52 = t15 ** 2
  t53 = t51 * t52
  t55 = 0.1e1 / t18 / t43
  t56 = t53 * t55
  t57 = t50 * t56
  t59 = 0.750e0 + 0.45090814814814814814814814814814814814814814814814e0 * t37 - 0.82017777777777777777777777777777777777777777777782e-1 * t45 + 0.33649382716049382716049382716049382716049382716049e0 * t57
  t63 = 0.1e1 + 0.12311866666666666666666666666666666666666666666667e1 * t37 + 0.10094814814814814814814814814814814814814814814815e1 * t57
  t64 = 0.1e1 / t63
  t69 = t4 * t9
  t70 = 0.1e1 / t5
  t71 = t70 * t22
  t73 = 0.1e1 / t17 / t43
  t74 = t33 * t73
  t75 = t31 * t74
  t77 = t43 * r0
  t78 = 0.1e1 / t77
  t79 = t42 * t78
  t82 = 0.1e1 / t18 / t77
  t83 = t53 * t82
  t84 = t50 * t83
  t86 = -0.60121086419753086419753086419753086419753086419752e0 * t75 + 0.16403555555555555555555555555555555555555555555556e0 * t79 - 0.89731687242798353909465020576131687242798353909464e0 * t84
  t92 = t4 * t9 * t70
  t93 = t22 * t59
  t94 = t63 ** 2
  t95 = 0.1e1 / t94
  t98 = -0.16415822222222222222222222222222222222222222222223e1 * t75 - 0.26919506172839506172839506172839506172839506172840e1 * t84
  t99 = t95 * t98
  t103 = jnp.sqrt(0.2e1)
  t104 = t9 * t11
  t105 = params.T * t52
  t106 = 0.1e1 / t18
  t108 = t104 * t105 * t106
  t109 = jnp.sqrt(t108)
  t113 = jnp.tanh(0.3e1 / 0.2e1 * t103 / t109)
  t114 = t113 ** 2
  t115 = 0.1e1 - t114
  t116 = t115 * t103
  t118 = 0.1e1 / t109 / t108
  t119 = t118 * t9
  t121 = t116 * t119 * t11
  t123 = 0.1e1 / t18 / r0
  t124 = t105 * t123
  t128 = params.b_0_[1] * t10 * t30
  t133 = params.b_0_[2] * t9 * t49
  t136 = params.b_0_[0] + 0.4e1 / 0.27e2 * t128 * t36 + 0.16e2 / 0.81e2 * t133 * t56
  t139 = params.b_0_[3] * t10 * t30
  t144 = params.b_0_[4] * t9 * t49
  t147 = 0.1e1 + 0.4e1 / 0.27e2 * t139 * t36 + 0.16e2 / 0.81e2 * t144 * t56
  t148 = 0.1e1 / t147
  t150 = t15 * t5
  t151 = t3 * t27
  t152 = t150 * t151
  t153 = jnp.sqrt(t152)
  t154 = t136 * t148 * t153
  t162 = -0.16e2 / 0.81e2 * t128 * t74 - 0.128e3 / 0.243e3 * t133 * t83
  t163 = t113 * t162
  t164 = t148 * t153
  t167 = t113 * t136
  t168 = t147 ** 2
  t169 = 0.1e1 / t168
  t170 = t169 * t153
  t175 = -0.16e2 / 0.81e2 * t139 * t74 - 0.128e3 / 0.243e3 * t144 * t83
  t176 = t170 * t175
  t179 = 0.1e1 / t153
  t180 = t148 * t179
  t181 = t167 * t180
  t182 = t3 * t35
  t183 = t150 * t182
  t186 = params.c_0_[1]
  t187 = params.c_0_[2]
  t188 = t186 * t187
  t190 = jnp.pi * t14
  t191 = t190 * t52
  t192 = t188 * t10 * t191
  t197 = jnp.exp(-t187 * t10 * t12 * t19 / 0.6e1)
  t199 = t106 * t197 * t22
  t203 = params.e_0_[1] * t10 * t30
  t208 = params.e_0_[2] * t9 * t49
  t211 = params.e_0_[0] + 0.4e1 / 0.27e2 * t203 * t36 + 0.16e2 / 0.81e2 * t208 * t56
  t214 = params.e_0_[3] * t10 * t30
  t219 = params.e_0_[4] * t9 * t49
  t222 = 0.1e1 + 0.4e1 / 0.27e2 * t214 * t36 + 0.16e2 / 0.81e2 * t219 * t56
  t223 = 0.1e1 / t222
  t224 = t211 * t223
  t225 = t224 * t3
  t231 = t186 * t197 + params.c_0_[0]
  t234 = t10 * jnp.pi * t14
  t235 = t231 * t24 * t234
  t236 = t52 * t106
  t237 = t236 * t225
  t240 = t231 * t22
  t245 = -0.16e2 / 0.81e2 * t203 * t74 - 0.128e3 / 0.243e3 * t208 * t83
  t246 = t245 * t223
  t247 = t240 * t246
  t250 = t222 ** 2
  t251 = 0.1e1 / t250
  t252 = t211 * t251
  t253 = t240 * t252
  t258 = -0.16e2 / 0.81e2 * t214 * t74 - 0.128e3 / 0.243e3 * t219 * t83
  t260 = t150 * t151 * t258
  t263 = t240 * t224
  t266 = t26 * t16 * t27 * t59 * t64 / 0.4e1 + t69 * t71 * t86 * t64 / 0.4e1 - t92 * t93 * t99 / 0.4e1 + t121 * t124 * t154 / 0.4e1 + t163 * t164 / 0.2e1 - t167 * t176 / 0.2e1 - t181 * t183 / 0.12e2 - t192 * t199 * t225 / 0.36e2 + t235 * t237 / 0.36e2 + t247 * t152 / 0.4e1 - t253 * t260 / 0.4e1 - t263 * t183 / 0.12e2
  t267 = t266 * t52
  t268 = t267 * t70
  t269 = t2 * t17
  t273 = params.d_0_[1] * t10 * t30
  t278 = params.d_0_[2] * t9 * t49
  t281 = params.d_0_[0] + 0.4e1 / 0.27e2 * t273 * t36 + 0.16e2 / 0.81e2 * t278 * t56
  t282 = t113 * t281
  t285 = params.d_0_[3] * t10 * t30
  t290 = params.d_0_[4] * t9 * t49
  t293 = 0.1e1 + 0.4e1 / 0.27e2 * t285 * t36 + 0.16e2 / 0.81e2 * t290 * t56
  t294 = 0.1e1 / t293
  t295 = t294 * t153
  t298 = t22 * t211
  t299 = t298 * t223
  t302 = 0.1e1 + t282 * t295 / 0.2e1 + t299 * t152 / 0.4e1
  t303 = 0.1e1 / t302
  t304 = 0.1e1 <= f.p.zeta_threshold
  t306 = 0.2e1 / 0.3e1 - 0.34815250000000000000000000000000000000000000000000e-2 * t152
  t308 = 0.1e1 + 0.45802000000000000000000000000000000000000000000000e-1 * t152
  t309 = 0.1e1 / t308
  t310 = t306 * t309
  t311 = t104 * params.T
  t315 = 0.1064009e1 + 0.63618333333333333333333333333333333333333333333335e-1 * t311 * t236 * t153
  t319 = jnp.exp(-0.2e1 / 0.9e1 * t311 * t236 * t315)
  t321 = -t310 * t319 + 0.2e1
  t322 = f.p.zeta_threshold ** t321
  t323 = f.my_piecewise3(t304, t322, 1)
  t325 = 0.2e1 * t323 - 0.2e1
  t326 = 2 ** t321
  t327 = t326 - 0.2e1
  t328 = 0.1e1 / t327
  t329 = t325 * t328
  t330 = 0.1e1 - t329
  t331 = t303 * t330
  t332 = t269 * t331
  t344 = (t69 * t71 * t59 * t64 / 0.4e1 + t167 * t164 / 0.2e1 + t263 * t152 / 0.4e1) * t52
  t345 = t344 * t70
  t346 = t2 * t106
  t347 = t346 * t331
  t350 = t70 * t2
  t351 = t344 * t350
  t352 = t302 ** 2
  t353 = 0.1e1 / t352
  t354 = t17 * t353
  t356 = t281 * t294 * t153
  t364 = -0.16e2 / 0.81e2 * t273 * t74 - 0.128e3 / 0.243e3 * t278 * t83
  t365 = t113 * t364
  t368 = t293 ** 2
  t369 = 0.1e1 / t368
  t370 = t369 * t153
  t375 = -0.16e2 / 0.81e2 * t285 * t74 - 0.128e3 / 0.243e3 * t290 * t83
  t376 = t370 * t375
  t379 = t294 * t179
  t380 = t282 * t379
  t383 = t24 * t10
  t384 = t383 * t190
  t387 = t22 * t245
  t388 = t387 * t223
  t391 = t251 * t15
  t392 = t298 * t391
  t393 = t5 * t3
  t395 = t393 * t27 * t258
  t400 = t121 * t124 * t356 / 0.4e1 + t365 * t295 / 0.2e1 - t282 * t376 / 0.2e1 - t380 * t183 / 0.12e2 + t384 * t237 / 0.36e2 + t388 * t152 / 0.4e1 - t392 * t395 / 0.4e1 - t299 * t183 / 0.12e2
  t401 = t330 * t400
  t402 = t354 * t401
  t405 = t150 * t3
  t406 = t35 * t309
  t410 = t308 ** 2
  t411 = 0.1e1 / t410
  t412 = t306 * t411
  t413 = t412 * t319
  t416 = t52 * t123
  t424 = t9 * t7 * params.T
  t429 = -0.42412222222222222222222222222222222222222222222223e-1 * t311 * t416 * t153 - 0.31809166666666666666666666666666666666666666666668e-1 * t424 * t44 * t179 * t3
  t433 = 0.4e1 / 0.27e2 * t311 * t416 * t315 - 0.2e1 / 0.9e1 * t311 * t236 * t429
  t434 = t433 * t319
  t436 = -0.11605083333333333333333333333333333333333333333333e-2 * t405 * t406 * t319 - 0.15267333333333333333333333333333333333333333333333e-1 * t413 * t183 - t310 * t434
  t438 = jnp.log(f.p.zeta_threshold)
  t440 = f.my_piecewise3(t304, t322 * t436 * t438, 0)
  t441 = t440 * t328
  t443 = t327 ** 2
  t444 = 0.1e1 / t443
  t445 = t325 * t444
  t447 = jnp.log(0.2e1)
  t448 = t326 * t436 * t447
  t450 = t445 * t448 - 0.2e1 * t441
  t451 = t303 * t450
  t452 = t269 * t451
  t457 = 2 ** (0.1e1 / 0.3e1)
  t458 = t457 ** 2
  t462 = jnp.tanh(t13 * t14 * t15 * t18 * t458 / 0.6e1)
  t463 = t462 ** 2
  t464 = 0.1e1 - t463
  t465 = t8 * t464
  t466 = t4 * t465
  t467 = t31 * t32
  t470 = t467 * t15 * t35 * t458
  t473 = t50 * t51
  t474 = t52 * t55
  t475 = t474 * t457
  t476 = t473 * t475
  t478 = 0.750e0 + 0.11272703703703703703703703703703703703703703703704e0 * t470 - 0.20504444444444444444444444444444444444444444444444e-1 * t45 + 0.42061728395061728395061728395061728395061728395060e-1 * t476
  t482 = 0.1e1 + 0.30779666666666666666666666666666666666666666666667e0 * t470 + 0.12618518518518518518518518518518518518518518518519e0 * t476
  t483 = 0.1e1 / t482
  t490 = t457 * t1 * t3 * t9
  t491 = t70 * t462
  t494 = t467 * t15 * t73 * t458
  t499 = t473 * t52 * t82 * t457
  t501 = -0.15030271604938271604938271604938271604938271604939e0 * t494 + 0.41008888888888888888888888888888888888888888888888e-1 * t79 - 0.11216460905349794238683127572016460905349794238683e0 * t499
  t506 = t482 ** 2
  t507 = 0.1e1 / t506
  t508 = t478 * t507
  t511 = -0.41039555555555555555555555555555555555555555555556e0 * t494 - 0.33649382716049382716049382716049382716049382716051e0 * t499
  t512 = t508 * t511
  t517 = t311 * t236 * t457
  t518 = jnp.sqrt(t517)
  t521 = jnp.tanh(0.3e1 / t518)
  t522 = t521 ** 2
  t523 = 0.1e1 - t522
  t526 = t523 / t518 / t517
  t527 = t526 * t311
  t528 = t416 * t457
  t532 = params.b_1_[1] * t10 * t30
  t534 = t33 * t35 * t458
  t539 = params.b_1_[2] * t9 * t49
  t541 = t53 * t55 * t457
  t544 = params.b_1_[0] + t532 * t534 / 0.27e2 + 0.2e1 / 0.81e2 * t539 * t541
  t547 = params.b_1_[3] * t10 * t30
  t552 = params.b_1_[4] * t9 * t49
  t555 = 0.1e1 + t547 * t534 / 0.27e2 + 0.2e1 / 0.81e2 * t552 * t541
  t556 = 0.1e1 / t555
  t558 = t544 * t556 * t153
  t563 = t33 * t73 * t458
  t567 = t53 * t82 * t457
  t570 = -0.4e1 / 0.81e2 * t532 * t563 - 0.16e2 / 0.243e3 * t539 * t567
  t571 = t521 * t570
  t572 = t556 * t153
  t575 = t521 * t544
  t576 = t555 ** 2
  t577 = 0.1e1 / t576
  t578 = t577 * t153
  t583 = -0.4e1 / 0.81e2 * t547 * t563 - 0.16e2 / 0.243e3 * t552 * t567
  t584 = t578 * t583
  t587 = t556 * t179
  t588 = t575 * t587
  t591 = params.c_1_[1]
  t592 = params.c_1_[2]
  t593 = t591 * t592
  t594 = t593 * t10
  t595 = t594 * t191
  t596 = t106 * t458
  t603 = jnp.exp(-t592 * t10 * t12 * t16 * t18 * t458 / 0.6e1)
  t604 = t596 * t603
  t608 = params.e_1_[1] * t10 * t30
  t613 = params.e_1_[2] * t9 * t49
  t616 = params.e_1_[0] + t608 * t534 / 0.27e2 + 0.2e1 / 0.81e2 * t613 * t541
  t617 = t462 * t616
  t620 = params.e_1_[3] * t10 * t30
  t625 = params.e_1_[4] * t9 * t49
  t628 = 0.1e1 + t620 * t534 / 0.27e2 + 0.2e1 / 0.81e2 * t625 * t541
  t629 = 0.1e1 / t628
  t630 = t629 * t3
  t631 = t617 * t630
  t637 = t591 * t603 + params.c_1_[0]
  t638 = t637 * t464
  t639 = t638 * t234
  t640 = t236 * t458
  t641 = t616 * t629
  t642 = t641 * t3
  t646 = t637 * t462
  t651 = -0.4e1 / 0.81e2 * t608 * t563 - 0.16e2 / 0.243e3 * t613 * t567
  t652 = t651 * t629
  t653 = t646 * t652
  t656 = t628 ** 2
  t657 = 0.1e1 / t656
  t658 = t616 * t657
  t659 = t646 * t658
  t664 = -0.4e1 / 0.81e2 * t620 * t563 - 0.16e2 / 0.243e3 * t625 * t567
  t666 = t150 * t151 * t664
  t669 = t646 * t641
  t672 = t466 * t16 * t27 * t478 * t483 / 0.2e1 + t490 * t491 * t501 * t483 / 0.4e1 - t490 * t491 * t512 / 0.4e1 + t527 * t528 * t558 / 0.2e1 + t571 * t572 / 0.2e1 - t575 * t584 / 0.2e1 - t588 * t183 / 0.12e2 - t595 * t604 * t631 / 0.36e2 + t639 * t640 * t642 / 0.36e2 + t653 * t152 / 0.4e1 - t659 * t666 / 0.4e1 - t669 * t183 / 0.12e2
  t673 = t672 * t52
  t674 = t673 * t350
  t678 = params.d_1_[1] * t10 * t30
  t683 = params.d_1_[2] * t9 * t49
  t686 = params.d_1_[0] + t678 * t534 / 0.27e2 + 0.2e1 / 0.81e2 * t683 * t541
  t687 = t521 * t686
  t690 = params.d_1_[3] * t10 * t30
  t695 = params.d_1_[4] * t9 * t49
  t698 = 0.1e1 + t690 * t534 / 0.27e2 + 0.2e1 / 0.81e2 * t695 * t541
  t699 = 0.1e1 / t698
  t700 = t699 * t153
  t703 = t617 * t629
  t706 = 0.1e1 + t687 * t700 / 0.2e1 + t703 * t152 / 0.4e1
  t707 = 0.1e1 / t706
  t708 = t17 * t707
  t709 = t708 * t329
  t721 = (t490 * t491 * t478 * t483 / 0.4e1 + t575 * t572 / 0.2e1 + t669 * t152 / 0.4e1) * t52
  t722 = t721 * t350
  t723 = t106 * t707
  t724 = t723 * t329
  t727 = t706 ** 2
  t728 = 0.1e1 / t727
  t729 = t17 * t728
  t731 = t686 * t699 * t153
  t739 = -0.4e1 / 0.81e2 * t678 * t563 - 0.16e2 / 0.243e3 * t683 * t567
  t740 = t521 * t739
  t743 = t698 ** 2
  t744 = 0.1e1 / t743
  t745 = t744 * t153
  t750 = -0.4e1 / 0.81e2 * t690 * t563 - 0.16e2 / 0.243e3 * t695 * t567
  t751 = t745 * t750
  t754 = t699 * t179
  t755 = t687 * t754
  t759 = t464 * t10 * t191
  t763 = t462 * t651
  t764 = t763 * t629
  t767 = t657 * t15
  t768 = t617 * t767
  t770 = t393 * t27 * t664
  t775 = t527 * t528 * t731 / 0.2e1 + t740 * t700 / 0.2e1 - t687 * t751 / 0.2e1 - t755 * t183 / 0.12e2 + t759 * t596 * t642 / 0.36e2 + t764 * t152 / 0.4e1 - t768 * t770 / 0.4e1 - t703 * t183 / 0.12e2
  t776 = t329 * t775
  t777 = t729 * t776
  t780 = t708 * t441
  t783 = t350 * t17
  t784 = t721 * t783
  t785 = t707 * t325
  t786 = t785 * t444
  t787 = t786 * t448
  t790 = t436 ** 2
  t792 = t438 ** 2
  t798 = t52 * t6
  t812 = t798 * t2 * t55
  t819 = t150 * t3 * t73
  t838 = 0.1e1 / t17 / t77
  t840 = 0.1e1 / t153 / t152
  t853 = t433 ** 2
  t856 = 0.15473444444444444444444444444444444444444444444444e-2 * t405 * t73 * t309 * t319 - 0.14174294048888888888888888888888888888888888888888e-3 * t798 * t2 * t55 * t411 * t319 - 0.23210166666666666666666666666666666666666666666666e-2 * t405 * t406 * t434 - 0.18647317368888888888888888888888888888888888888887e-2 * t306 / t410 / t308 * t319 * t812 - 0.30534666666666666666666666666666666666666666666666e-1 * t412 * t434 * t183 + 0.20356444444444444444444444444444444444444444444444e-1 * t413 * t819 - t310 * (-0.20e2 / 0.81e2 * t311 * t474 * t315 + 0.8e1 / 0.27e2 * t311 * t416 * t429 - 0.2e1 / 0.9e1 * t311 * t236 * (0.70687037037037037037037037037037037037037037037038e-1 * t311 * t474 * t153 + 0.84824444444444444444444444444444444444444444444448e-1 * t424 * t78 * t179 * t3 - 0.21206111111111111111111111111111111111111111111112e-1 * t9 * t29 * params.T * t838 * t840 * t2 * t15)) * t319 - t310 * t853 * t319
  t860 = f.my_piecewise3(t304, t322 * t856 * t438 + t322 * t790 * t792, 0)
  t861 = t860 * t328
  t867 = 0.1e1 / t443 / t327
  t869 = t326 ** 2
  t871 = t447 ** 2
  t872 = t869 * t790 * t871
  t876 = t326 * t790 * t871
  t879 = t326 * t856 * t447
  t889 = t33 * t838
  t892 = t43 ** 2
  t894 = 0.1e1 / t18 / t892
  t895 = t53 * t894
  t910 = 0.112e3 / 0.243e3 * t203 * t889 + 0.1408e4 / 0.729e3 * t208 * t895
  t929 = 0.112e3 / 0.243e3 * t214 * t889 + 0.1408e4 / 0.729e3 * t219 * t895
  t937 = 0.1e1 / t250 / t222
  t940 = t258 ** 2
  t950 = t113 * (0.112e3 / 0.243e3 * t273 * t889 + 0.1408e4 / 0.729e3 * t278 * t895) * t295 / 0.2e1 - t388 * t183 / 0.6e1 + t299 * t819 / 0.9e1 + t22 * t910 * t223 * t152 / 0.4e1 - t365 * t379 * t183 / 0.6e1 - t282 * t294 * t840 * t812 / 0.18e2 - t387 * t391 * t395 / 0.2e1 - t392 * t393 * t27 * t929 / 0.4e1 + t380 * t819 / 0.9e1 + t298 * t937 * t15 * t393 * t27 * t940 / 0.2e1 + t392 * t393 * t35 * t258 / 0.6e1 - t365 * t376
  t962 = t375 ** 2
  t965 = t416 * t225
  t971 = t393 * t35
  t975 = t246 * t3
  t976 = t236 * t975
  t980 = t116 * t118 * t311
  t985 = t105 * t55
  t997 = t113 * t115 * t39 * t14 * t35
  t998 = t31 * t15
  t1007 = t116 / t109 / t37 * t10 * t30 / 0.3e1
  t1012 = t116 * t119 * t7
  t1013 = params.T * t78
  t1019 = t22 * t24
  t1021 = 0.1e1 / t32
  t1022 = t9 * t12 * t1021
  t1024 = 0.1e1 / r0
  t1032 = t251 * t3 * t258
  t1036 = -t282 * t370 * (0.112e3 / 0.243e3 * t285 * t889 + 0.1408e4 / 0.729e3 * t290 * t895) / 0.2e1 + t282 / t368 / t293 * t153 * t962 - t384 * t965 / 0.36e2 + t282 * t369 * t179 * t375 * t15 * t971 / 0.6e1 + t384 * t976 / 0.18e2 - t980 * t416 * t281 * t376 / 0.2e1 - 0.5e1 / 0.12e2 * t121 * t985 * t356 + t121 * t124 * t364 * t294 * t153 / 0.2e1 - t997 * t998 * t356 / 0.54e2 + 0.3e1 / 0.4e1 * t1007 * t889 * t356 - t1012 * t1013 * t281 * t379 * t3 / 0.4e1 - t1019 * t1022 * t1024 * jnp.pi * t225 / 0.6e1 - t383 * t191 * t106 * t211 * t1032 / 0.18e2
  t1046 = t33 * t838 * t458
  t1050 = t53 * t894 * t457
  t1068 = 0.28e2 / 0.243e3 * t608 * t1046 + 0.176e3 / 0.729e3 * t613 * t1050
  t1074 = t15 * t838 * t458
  t1075 = t467 * t1074
  t1078 = t42 / t892
  t1082 = t473 * t52 * t894 * t457
  t1098 = t583 ** 2
  t1122 = t511 ** 2
  t1128 = 0.1e1 / t656 / t628
  t1131 = t664 ** 2
  t1153 = 0.28e2 / 0.243e3 * t620 * t1046 + 0.176e3 / 0.729e3 * t625 * t1050
  t1162 = t521 * (0.28e2 / 0.243e3 * t532 * t1046 + 0.176e3 / 0.729e3 * t539 * t1050) * t572 / 0.2e1 - t571 * t587 * t183 / 0.6e1 - t575 * t556 * t840 * t812 / 0.18e2 + t646 * t1068 * t629 * t152 / 0.4e1 + t490 * t491 * (0.35070633744855967078189300411522633744855967078191e0 * t1075 - 0.12302666666666666666666666666666666666666666666666e0 * t1078 + 0.41127023319615912208504801097393689986282578875171e0 * t1082) * t483 / 0.4e1 + t669 * t819 / 0.9e1 + t588 * t819 / 0.9e1 - t653 * t183 / 0.6e1 + t575 / t576 / t555 * t153 * t1098 - t571 * t584 - t575 * t578 * (0.28e2 / 0.243e3 * t547 * t1046 + 0.176e3 / 0.729e3 * t552 * t1050) / 0.2e1 + t594 * t190 * t236 * t458 * t603 * t462 * t658 * t3 * t664 / 0.18e2 + t490 * t491 * t478 / t506 / t482 * t1122 / 0.2e1 + t646 * t616 * t1128 * t150 * t151 * t1131 / 0.2e1 + t659 * t150 * t182 * t664 / 0.6e1 - t466 * t16 * t35 * t478 * t483 / 0.6e1 - t646 * t651 * t657 * t666 / 0.2e1 - t659 * t150 * t151 * t1153 / 0.4e1 + t466 * t16 * t27 * t501 * t483
  t1183 = jnp.pi * t1021 * t1024
  t1192 = t123 * t458
  t1201 = t592 ** 2
  t1214 = t1024 * t457 * jnp.pi * t642
  t1220 = t526 * t9 * t11 * params.T * t52
  t1221 = t123 * t457
  t1229 = t521 * t523 * t39 * t14 * t35 * t10
  t1231 = t30 * t15 * t458
  t1240 = t596 * t616 * t657 * t3 * t664
  t1243 = t526 * t424
  t1244 = t78 * t457
  t1250 = t652 * t3
  t1254 = t28 * t3
  t1255 = t462 * t464
  t1258 = t1021 * t52
  t1280 = t523 / t518 / t470 * t467 / 0.3e1
  t1286 = t15 * t27
  t1289 = -t490 * t491 * t501 * t507 * t511 / 0.2e1 - t490 * t491 * t508 * (0.95758962962962962962962962962962962962962962962964e0 * t1075 + 0.12338106995884773662551440329218106995884773662552e1 * t1082) / 0.4e1 + t575 * t577 * t179 * t583 * t15 * t971 / 0.6e1 - t593 * t9 * t1183 * t457 * t603 * t464 * t12 * t616 * t630 / 0.3e1 + t595 * t1192 * t603 * t631 / 0.36e2 - t595 * t604 * t763 * t630 / 0.18e2 + t591 * t1201 * t9 * t1183 * t457 * t12 * t603 * t631 / 0.6e1 - t646 * t464 * t1022 * t1214 / 0.3e1 - t1220 * t1221 * t544 * t584 - t1229 * t1231 * t558 / 0.54e2 - t638 * t10 * t191 * t1240 / 0.18e2 - t1243 * t1244 * t544 * t587 * t3 / 0.2e1 + t639 * t640 * t1250 / 0.18e2 - t1254 * t1255 * t10 * t1258 * t106 * t458 * t478 * t483 / 0.9e1 - 0.5e1 / 0.6e1 * t527 * t475 * t558 - t639 * t416 * t458 * t642 / 0.36e2 + t527 * t528 * t570 * t556 * t153 + 0.3e1 / 0.2e1 * t1280 * t1074 * t558 - t4 * t465 * t14 * t1286 * t512
  t1306 = t31 * t889
  t1309 = t50 * t895
  t1355 = t187 ** 2
  t1401 = t113 * (0.112e3 / 0.243e3 * t128 * t889 + 0.1408e4 / 0.729e3 * t133 * t895) * t164 / 0.2e1 + t69 * t71 * (0.14028253497942386831275720164609053497942386831275e1 * t1306 - 0.49210666666666666666666666666666666666666666666668e0 * t1078 + 0.32901618655692729766803840877914951989026063100137e1 * t1309) * t64 / 0.4e1 + t253 * t150 * t182 * t258 / 0.6e1 - t26 * t16 * t35 * t59 * t64 / 0.12e2 + t240 * t211 * t937 * t150 * t151 * t940 / 0.2e1 - t240 * t245 * t251 * t260 / 0.2e1 - t253 * t150 * t151 * t929 / 0.4e1 + t26 * t16 * t27 * t86 * t64 / 0.2e1 + t167 * t169 * t179 * t175 * t15 * t971 / 0.6e1 + t192 * t199 * t252 * t3 * t258 / 0.18e2 + t186 * t1355 * t9 * t1183 * t12 * t197 * t22 * t225 / 0.12e2 - t188 * t9 * t1183 * t197 * t24 * t12 * t225 / 0.6e1 - t980 * t416 * t136 * t176 / 0.2e1 + t192 * t123 * t197 * t22 * t225 / 0.36e2 - t192 * t199 * t975 / 0.18e2 - 0.5e1 / 0.12e2 * t121 * t985 * t154 - t235 * t236 * t211 * t1032 / 0.18e2 - t240 * t24 * t9 * t12 * t1183 * t225 / 0.6e1 + t121 * t124 * t162 * t148 * t153 / 0.2e1
  t1434 = t175 ** 2
  t1476 = t98 ** 2
  t1481 = -t997 * t998 * t154 / 0.54e2 + 0.3e1 / 0.4e1 * t1007 * t889 * t154 - t1012 * t1013 * t136 * t180 * t3 / 0.4e1 - t1254 * t1019 * t10 * t1258 * t106 * t59 * t64 / 0.18e2 + t235 * t976 / 0.18e2 - t235 * t965 / 0.36e2 - t4 * t25 * t14 * t1286 * t59 * t95 * t98 / 0.2e1 + t167 / t168 / t147 * t153 * t1434 - t163 * t176 - t167 * t170 * (0.112e3 / 0.243e3 * t139 * t889 + 0.1408e4 / 0.729e3 * t144 * t895) / 0.2e1 + t240 * t910 * t223 * t152 / 0.4e1 - t92 * t22 * t86 * t99 / 0.2e1 - t92 * t93 * t95 * (0.38303585185185185185185185185185185185185185185187e1 * t1306 + 0.98704855967078189300411522633744855967078189300413e1 * t1309) / 0.4e1 - t163 * t180 * t183 / 0.6e1 - t167 * t148 * t840 * t812 / 0.18e2 + t181 * t819 / 0.9e1 - t247 * t183 / 0.6e1 + t263 * t819 / 0.9e1 + t92 * t93 / t94 / t63 * t1476 / 0.2e1
  t1500 = t775 ** 2
  t1552 = t521 * (0.28e2 / 0.243e3 * t678 * t1046 + 0.176e3 / 0.729e3 * t683 * t1050) * t700 / 0.2e1 - t764 * t183 / 0.6e1 + t462 * t1068 * t629 * t152 / 0.4e1 + t703 * t819 / 0.9e1 + t687 * t744 * t179 * t750 * t15 * t971 / 0.6e1 - t1220 * t1221 * t686 * t751 - t1229 * t1231 * t731 / 0.54e2 - 0.5e1 / 0.6e1 * t527 * t475 * t731 - t759 * t1240 / 0.18e2 - t1255 * t1022 * t1214 / 0.3e1 + t527 * t528 * t739 * t699 * t153 + 0.3e1 / 0.2e1 * t1280 * t1074 * t731
  t1567 = t750 ** 2
  t1605 = -t1243 * t1244 * t686 * t754 * t3 / 0.2e1 - t759 * t1192 * t642 / 0.36e2 + t759 * t596 * t1250 / 0.18e2 + t687 / t743 / t698 * t153 * t1567 - t740 * t751 - t687 * t745 * (0.28e2 / 0.243e3 * t690 * t1046 + 0.176e3 / 0.729e3 * t695 * t1050) / 0.2e1 + t617 * t1128 * t15 * t393 * t27 * t1131 / 0.2e1 + t768 * t393 * t35 * t664 / 0.6e1 + t755 * t819 / 0.9e1 - t740 * t754 * t183 / 0.6e1 - t687 * t699 * t840 * t812 / 0.18e2 - t763 * t767 * t770 / 0.2e1 - t768 * t393 * t27 * t1153 / 0.4e1
  t1611 = -t345 * t269 * t303 * (-0.2e1 * t325 * t867 * t872 + 0.4e1 * t440 * t444 * t448 + t445 * t876 + t445 * t879 - 0.2e1 * t861) / 0.3e1 - 0.4e1 / 0.9e1 * t722 * t723 * t441 + t351 * t354 * t330 * (t950 + t1036) / 0.3e1 - 0.2e1 / 0.3e1 * t722 * t708 * t861 - (t1162 + t1289) * t52 * t350 * t709 / 0.3e1 - 0.2e1 / 0.9e1 * t345 * t346 * t451 - (t1401 + t1481) * t52 * t70 * t332 / 0.3e1 - 0.2e1 / 0.3e1 * t268 * t452 + 0.2e1 / 0.27e2 * t345 * t2 * t123 * t331 - 0.2e1 / 0.9e1 * t268 * t347 + 0.2e1 / 0.3e1 * t674 * t777 - 0.2e1 / 0.3e1 * t722 * t17 / t727 / t706 * t329 * t1500 + 0.4e1 / 0.3e1 * t722 * t729 * t441 * t775 + t722 * t729 * t329 * (t1552 + t1605) / 0.3e1
  t1652 = t400 ** 2
  t1672 = 0.2e1 / 0.9e1 * t722 * t106 * t728 * t776 - 0.2e1 / 0.3e1 * t721 * t70 * t269 * t728 * t445 * t775 * t448 + 0.2e1 / 0.3e1 * t673 * t783 * t787 - 0.2e1 / 0.3e1 * t784 * t785 * t867 * t872 + t784 * t786 * t876 / 0.3e1 + 0.4e1 / 0.3e1 * t784 * t707 * t440 * t444 * t448 + t784 * t786 * t879 / 0.3e1 + 0.2e1 / 0.9e1 * t721 * t350 * t106 * t787 - 0.4e1 / 0.3e1 * t674 * t780 - 0.2e1 / 0.9e1 * t674 * t724 - 0.2e1 / 0.3e1 * t351 * t17 / t352 / t302 * t330 * t1652 + 0.2e1 / 0.3e1 * t351 * t354 * t450 * t400 + 0.2e1 / 0.9e1 * t351 * t106 * t353 * t401 + 0.2e1 / 0.3e1 * t267 * t350 * t402 + 0.2e1 / 0.27e2 * t722 * t123 * t707 * t329
  v2rho2_0_ = -0.2e1 / 0.3e1 * t268 * t332 - 0.2e1 / 0.9e1 * t345 * t347 + 0.2e1 / 0.3e1 * t351 * t402 - 0.2e1 / 0.3e1 * t345 * t452 - 0.2e1 / 0.3e1 * t674 * t709 - 0.2e1 / 0.9e1 * t722 * t724 + 0.2e1 / 0.3e1 * t722 * t777 - 0.4e1 / 0.3e1 * t722 * t780 + 0.2e1 / 0.3e1 * t784 * t787 + r0 * (t1611 + t1672)

  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 2 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t1 * t2
  t4 = 4 ** (0.1e1 / 0.3e1)
  t5 = t4 ** 2
  t6 = 9 ** (0.1e1 / 0.3e1)
  t7 = t5 * t6
  t8 = t3 * t7
  t9 = t2 ** (0.1e1 / 0.3e1)
  t10 = 0.1e1 / t9
  t11 = t6 ** 2
  t12 = t9 * t2
  t13 = 0.1e1 / t12
  t14 = t11 * t13
  t15 = 0.1e1 / params.T
  t17 = 3 ** (0.1e1 / 0.3e1)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = t1 ** 2
  t25 = jnp.tanh(t14 * t15 * t17 * t19 * t21 / 0.6e1)
  t26 = t10 * t25
  t27 = jnp.pi ** 2
  t28 = 0.1e1 / t27
  t29 = t9 ** 2
  t30 = t29 * t28
  t31 = t11 * t30
  t32 = params.T ** 2
  t33 = t31 * t32
  t35 = 0.1e1 / t18 / r0
  t36 = t17 * t35
  t38 = t33 * t36 * t21
  t40 = t27 ** 2
  t41 = 0.1e1 / t40
  t42 = t32 * params.T
  t43 = t41 * t42
  t44 = r0 ** 2
  t45 = 0.1e1 / t44
  t46 = t43 * t45
  t50 = t9 / t40 / jnp.pi
  t51 = t6 * t50
  t52 = t32 ** 2
  t53 = t51 * t52
  t54 = t17 ** 2
  t56 = 0.1e1 / t19 / t44
  t57 = t54 * t56
  t58 = t57 * t1
  t59 = t53 * t58
  t61 = 0.750e0 + 0.11272703703703703703703703703703703703703703703704e0 * t38 - 0.20504444444444444444444444444444444444444444444444e-1 * t46 + 0.42061728395061728395061728395061728395061728395060e-1 * t59
  t64 = 0.1e1 + 0.30779666666666666666666666666666666666666666666667e0 * t38 + 0.12618518518518518518518518518518518518518518518519e0 * t59
  t65 = 0.1e1 / t64
  t70 = t6 * t12
  t71 = t70 * params.T
  t72 = 0.1e1 / t19
  t73 = t54 * t72
  t75 = t71 * t73 * t1
  t76 = jnp.sqrt(t75)
  t79 = jnp.tanh(0.3e1 / t76)
  t83 = params.b_1_[1] * t11 * t30
  t84 = t32 * t17
  t86 = t84 * t35 * t21
  t91 = params.b_1_[2] * t6 * t50
  t92 = t52 * t54
  t93 = t56 * t1
  t94 = t92 * t93
  t97 = params.b_1_[0] + t83 * t86 / 0.27e2 + 0.2e1 / 0.81e2 * t91 * t94
  t98 = t79 * t97
  t101 = params.b_1_[3] * t11 * t30
  t106 = params.b_1_[4] * t6 * t50
  t109 = 0.1e1 + t101 * t86 / 0.27e2 + 0.2e1 / 0.81e2 * t106 * t94
  t110 = 0.1e1 / t109
  t111 = t17 * t9
  t112 = 0.1e1 / t18
  t113 = t5 * t112
  t114 = t111 * t113
  t115 = jnp.sqrt(t114)
  t116 = t110 * t115
  t120 = params.c_1_[1]
  t121 = params.c_1_[2]
  t124 = t15 * t17
  t129 = jnp.exp(-t121 * t11 * t13 * t124 * t19 * t21 / 0.6e1)
  t131 = t120 * t129 + params.c_1_[0]
  t132 = t131 * t25
  t136 = params.e_1_[1] * t11 * t30
  t141 = params.e_1_[2] * t6 * t50
  t144 = params.e_1_[0] + t136 * t86 / 0.27e2 + 0.2e1 / 0.81e2 * t141 * t94
  t147 = params.e_1_[3] * t11 * t30
  t152 = params.e_1_[4] * t6 * t50
  t155 = 0.1e1 + t147 * t86 / 0.27e2 + 0.2e1 / 0.81e2 * t152 * t94
  t156 = 0.1e1 / t155
  t157 = t144 * t156
  t158 = t132 * t157
  t162 = (t8 * t26 * t61 * t65 / 0.4e1 + t98 * t116 / 0.2e1 + t158 * t114 / 0.4e1) * t54
  t163 = t10 * t4
  t164 = t162 * t163
  t168 = params.d_1_[1] * t11 * t30
  t173 = params.d_1_[2] * t6 * t50
  t176 = params.d_1_[0] + t168 * t86 / 0.27e2 + 0.2e1 / 0.81e2 * t173 * t94
  t177 = t79 * t176
  t180 = params.d_1_[3] * t11 * t30
  t185 = params.d_1_[4] * t6 * t50
  t188 = 0.1e1 + t180 * t86 / 0.27e2 + 0.2e1 / 0.81e2 * t185 * t94
  t189 = 0.1e1 / t188
  t190 = t189 * t115
  t193 = t25 * t144
  t194 = t193 * t156
  t197 = 0.1e1 + t177 * t190 / 0.2e1 + t194 * t114 / 0.4e1
  t198 = t197 ** 2
  t199 = 0.1e1 / t198
  t200 = t18 * t199
  t201 = 0.1e1 <= f.p.zeta_threshold
  t203 = 0.2e1 / 0.3e1 - 0.34815250000000000000000000000000000000000000000000e-2 * t114
  t205 = 0.1e1 + 0.45802000000000000000000000000000000000000000000000e-1 * t114
  t206 = 0.1e1 / t205
  t207 = t203 * t206
  t211 = 0.1064009e1 + 0.63618333333333333333333333333333333333333333333335e-1 * t71 * t73 * t115
  t215 = jnp.exp(-0.2e1 / 0.9e1 * t71 * t73 * t211)
  t217 = -t207 * t215 + 0.2e1
  t218 = f.p.zeta_threshold ** t217
  t219 = f.my_piecewise3(t201, t218, 1)
  t221 = 0.2e1 * t219 - 0.2e1
  t222 = 2 ** t217
  t223 = t222 - 0.2e1
  t224 = 0.1e1 / t223
  t225 = t221 * t224
  t226 = t188 ** 2
  t227 = 0.1e1 / t226
  t228 = 0.1e1 / t115
  t229 = t227 * t228
  t230 = t177 * t229
  t232 = 0.1e1 / t18 / t44
  t233 = t232 * t21
  t234 = t84 * t233
  t237 = t44 * r0
  t239 = 0.1e1 / t19 / t237
  t241 = t92 * t239 * t1
  t244 = -0.4e1 / 0.81e2 * t180 * t234 - 0.16e2 / 0.243e3 * t185 * t241
  t245 = t244 * t17
  t246 = t9 * t5
  t247 = t246 * t35
  t248 = t245 * t247
  t252 = 0.1e1 / t18 / t237
  t253 = t252 * t21
  t254 = t84 * t253
  t257 = t44 ** 2
  t259 = 0.1e1 / t19 / t257
  t261 = t92 * t259 * t1
  t264 = 0.28e2 / 0.243e3 * t168 * t254 + 0.176e3 / 0.729e3 * t173 * t261
  t265 = t79 * t264
  t268 = t79 ** 2
  t269 = 0.1e1 - t268
  t271 = 0.1e1 / t76 / t75
  t272 = t269 * t271
  t273 = t272 * t6
  t276 = t273 * t12 * params.T * t54
  t278 = 0.1e1 / t19 / r0
  t279 = t278 * t1
  t280 = t279 * t176
  t281 = t227 * t115
  t282 = t281 * t244
  t285 = t79 * t269
  t286 = t285 * t40
  t288 = t15 * t35 * t11
  t289 = t286 * t288
  t290 = t30 * t17
  t291 = t290 * t21
  t293 = t176 * t189 * t115
  t294 = t291 * t293
  t297 = t155 ** 2
  t299 = 0.1e1 / t297 / t155
  t300 = t299 * t17
  t301 = t193 * t300
  t306 = -0.4e1 / 0.81e2 * t147 * t234 - 0.16e2 / 0.243e3 * t152 * t241
  t307 = t306 ** 2
  t309 = t246 * t112 * t307
  t312 = 0.1e1 / t297
  t313 = t312 * t17
  t314 = t193 * t313
  t316 = t246 * t35 * t306
  t319 = t189 * t228
  t320 = t177 * t319
  t321 = t5 * t232
  t322 = t111 * t321
  t329 = -0.4e1 / 0.81e2 * t168 * t234 - 0.16e2 / 0.243e3 * t173 * t241
  t330 = t79 * t329
  t331 = t330 * t319
  t332 = t5 * t35
  t333 = t111 * t332
  t337 = 0.1e1 / t115 / t114
  t338 = t189 * t337
  t339 = t177 * t338
  t340 = t54 * t29
  t341 = t4 * t56
  t342 = t340 * t341
  t349 = -0.4e1 / 0.81e2 * t136 * t234 - 0.16e2 / 0.243e3 * t141 * t241
  t350 = t25 * t349
  t351 = t350 * t313
  t353 = t246 * t112 * t306
  t360 = 0.28e2 / 0.243e3 * t147 * t254 + 0.176e3 / 0.729e3 * t152 * t261
  t361 = t112 * t360
  t362 = t246 * t361
  t366 = 0.1e1 / t226 / t188
  t368 = t244 ** 2
  t369 = t366 * t115 * t368
  t371 = t230 * t248 / 0.6e1 + t265 * t190 / 0.2e1 - t276 * t280 * t282 - t289 * t294 / 0.54e2 + t301 * t309 / 0.2e1 + t314 * t316 / 0.6e1 + t320 * t322 / 0.9e1 - t331 * t333 / 0.6e1 - t339 * t342 / 0.18e2 - t351 * t353 / 0.2e1 - t314 * t362 / 0.4e1 + t177 * t369
  t377 = 0.28e2 / 0.243e3 * t180 * t254 + 0.176e3 / 0.729e3 * t185 * t261
  t378 = t281 * t377
  t381 = t350 * t156
  t388 = 0.28e2 / 0.243e3 * t136 * t254 + 0.176e3 / 0.729e3 * t141 * t261
  t389 = t25 * t388
  t390 = t389 * t156
  t395 = t25 ** 2
  t396 = 0.1e1 - t395
  t397 = t396 * t11
  t398 = jnp.pi * t15
  t399 = t398 * t54
  t400 = t397 * t399
  t401 = t72 * t21
  t402 = t401 * t144
  t403 = t312 * t5
  t404 = t403 * t306
  t405 = t402 * t404
  t408 = t272 * t71
  t412 = t25 * t396
  t414 = 0.1e1 / t32
  t415 = t6 * t13 * t414
  t416 = t412 * t415
  t417 = 0.1e1 / r0
  t418 = t417 * t1
  t419 = t418 * jnp.pi
  t420 = t157 * t5
  t421 = t419 * t420
  t424 = t54 * t278
  t425 = t424 * t1
  t427 = t329 * t189 * t115
  t433 = t269 / t76 / t38 / 0.3e1
  t434 = t433 * t33
  t435 = t17 * t252
  t436 = t435 * t21
  t440 = t29 * t2
  t442 = t6 * t440 * params.T
  t443 = t272 * t442
  t444 = 0.1e1 / t237
  t445 = t444 * t1
  t447 = t319 * t5
  t451 = t278 * t21
  t455 = t349 * t156
  t456 = t455 * t5
  t460 = -t330 * t282 - t177 * t378 / 0.2e1 - t381 * t333 / 0.6e1 + t390 * t114 / 0.4e1 + t194 * t322 / 0.9e1 - t400 * t405 / 0.18e2 - 0.5e1 / 0.6e1 * t408 * t58 * t293 - t416 * t421 / 0.3e1 + t408 * t425 * t427 + 0.3e1 / 0.2e1 * t434 * t436 * t293 - t443 * t445 * t176 * t447 / 0.2e1 - t400 * t451 * t420 / 0.36e2 + t400 * t401 * t456 / 0.18e2
  t461 = t371 + t460
  t462 = t225 * t461
  t463 = t200 * t462
  t465 = 0.1e1 / t197
  t466 = t72 * t465
  t467 = t111 * t5
  t468 = t35 * t206
  t472 = t205 ** 2
  t473 = 0.1e1 / t472
  t474 = t203 * t473
  t475 = t474 * t215
  t488 = -0.42412222222222222222222222222222222222222222222223e-1 * t71 * t424 * t115 - 0.31809166666666666666666666666666666666666666666668e-1 * t442 * t45 * t228 * t5
  t492 = 0.4e1 / 0.27e2 * t71 * t424 * t211 - 0.2e1 / 0.9e1 * t71 * t73 * t488
  t493 = t492 * t215
  t495 = -0.11605083333333333333333333333333333333333333333333e-2 * t467 * t468 * t215 - 0.15267333333333333333333333333333333333333333333333e-1 * t475 * t333 - t207 * t493
  t496 = t218 * t495
  t497 = jnp.log(f.p.zeta_threshold)
  t499 = f.my_piecewise3(t201, t496 * t497, 0)
  t500 = t499 * t224
  t501 = t466 * t500
  t504 = t18 * t465
  t505 = t495 ** 2
  t507 = t497 ** 2
  t509 = t232 * t206
  t513 = t340 * t4
  t514 = t56 * t473
  t522 = 0.1e1 / t472 / t205
  t523 = t203 * t522
  t524 = t523 * t215
  t527 = t474 * t493
  t546 = t6 * t28 * params.T
  t548 = t4 * t17
  t552 = 0.70687037037037037037037037037037037037037037037038e-1 * t71 * t57 * t115 + 0.84824444444444444444444444444444444444444444444448e-1 * t442 * t444 * t228 * t5 - 0.21206111111111111111111111111111111111111111111112e-1 * t546 * t252 * t337 * t548
  t556 = -0.20e2 / 0.81e2 * t71 * t57 * t211 + 0.8e1 / 0.27e2 * t71 * t424 * t488 - 0.2e1 / 0.9e1 * t71 * t73 * t552
  t557 = t556 * t215
  t559 = t492 ** 2
  t560 = t559 * t215
  t562 = 0.15473444444444444444444444444444444444444444444444e-2 * t467 * t509 * t215 - 0.14174294048888888888888888888888888888888888888888e-3 * t513 * t514 * t215 - 0.23210166666666666666666666666666666666666666666666e-2 * t467 * t468 * t493 - 0.18647317368888888888888888888888888888888888888887e-2 * t524 * t342 - 0.30534666666666666666666666666666666666666666666666e-1 * t527 * t333 + 0.20356444444444444444444444444444444444444444444444e-1 * t475 * t322 - t207 * t557 - t207 * t560
  t566 = f.my_piecewise3(t201, t218 * t562 * t497 + t218 * t505 * t507, 0)
  t567 = t566 * t224
  t568 = t504 * t567
  t571 = t278 * t465
  t572 = t571 * t225
  t575 = t2 * t5
  t576 = t575 * t6
  t577 = t124 * t19
  t580 = jnp.tanh(t14 * t577 / 0.6e1)
  t581 = t10 * t580
  t582 = t84 * t35
  t583 = t31 * t582
  t586 = t92 * t56
  t587 = t51 * t586
  t589 = 0.750e0 + 0.45090814814814814814814814814814814814814814814814e0 * t583 - 0.82017777777777777777777777777777777777777777777782e-1 * t46 + 0.33649382716049382716049382716049382716049382716049e0 * t587
  t592 = 0.1e1 + 0.12311866666666666666666666666666666666666666666667e1 * t583 + 0.10094814814814814814814814814814814814814814814815e1 * t587
  t593 = 0.1e1 / t592
  t598 = jnp.sqrt(0.2e1)
  t599 = params.T * t54
  t601 = t70 * t599 * t72
  t602 = jnp.sqrt(t601)
  t606 = jnp.tanh(0.3e1 / 0.2e1 * t598 / t602)
  t610 = params.b_0_[1] * t11 * t30
  t615 = params.b_0_[2] * t6 * t50
  t618 = params.b_0_[0] + 0.4e1 / 0.27e2 * t610 * t582 + 0.16e2 / 0.81e2 * t615 * t586
  t619 = t606 * t618
  t622 = params.b_0_[3] * t11 * t30
  t627 = params.b_0_[4] * t6 * t50
  t630 = 0.1e1 + 0.4e1 / 0.27e2 * t622 * t582 + 0.16e2 / 0.81e2 * t627 * t586
  t631 = 0.1e1 / t630
  t632 = t631 * t115
  t636 = params.c_0_[1]
  t637 = params.c_0_[2]
  t642 = jnp.exp(-t637 * t11 * t13 * t577 / 0.6e1)
  t644 = t636 * t642 + params.c_0_[0]
  t645 = t644 * t580
  t649 = params.e_0_[1] * t11 * t30
  t654 = params.e_0_[2] * t6 * t50
  t657 = params.e_0_[0] + 0.4e1 / 0.27e2 * t649 * t582 + 0.16e2 / 0.81e2 * t654 * t586
  t660 = params.e_0_[3] * t11 * t30
  t665 = params.e_0_[4] * t6 * t50
  t668 = 0.1e1 + 0.4e1 / 0.27e2 * t660 * t582 + 0.16e2 / 0.81e2 * t665 * t586
  t669 = 0.1e1 / t668
  t670 = t657 * t669
  t671 = t645 * t670
  t675 = (t576 * t581 * t589 * t593 / 0.4e1 + t619 * t632 / 0.2e1 + t671 * t114 / 0.4e1) * t54
  t676 = t675 * t163
  t680 = params.d_0_[1] * t11 * t30
  t685 = params.d_0_[2] * t6 * t50
  t688 = params.d_0_[0] + 0.4e1 / 0.27e2 * t680 * t582 + 0.16e2 / 0.81e2 * t685 * t586
  t689 = t606 * t688
  t692 = params.d_0_[3] * t11 * t30
  t697 = params.d_0_[4] * t6 * t50
  t700 = 0.1e1 + 0.4e1 / 0.27e2 * t692 * t582 + 0.16e2 / 0.81e2 * t697 * t586
  t701 = 0.1e1 / t700
  t702 = t701 * t115
  t705 = t580 * t657
  t706 = t705 * t669
  t709 = 0.1e1 + t689 * t702 / 0.2e1 + t706 * t114 / 0.4e1
  t710 = t709 ** 2
  t711 = 0.1e1 / t710
  t712 = t72 * t711
  t713 = 0.1e1 - t225
  t714 = t606 ** 2
  t715 = 0.1e1 - t714
  t716 = t715 * t598
  t718 = 0.1e1 / t602 / t601
  t719 = t718 * t6
  t721 = t716 * t719 * t12
  t722 = t599 * t278
  t724 = t688 * t701 * t115
  t728 = t84 * t232
  t731 = t92 * t239
  t734 = -0.16e2 / 0.81e2 * t680 * t728 - 0.128e3 / 0.243e3 * t685 * t731
  t735 = t606 * t734
  t738 = t700 ** 2
  t739 = 0.1e1 / t738
  t740 = t739 * t115
  t745 = -0.16e2 / 0.81e2 * t692 * t728 - 0.128e3 / 0.243e3 * t697 * t731
  t746 = t740 * t745
  t749 = t701 * t228
  t750 = t689 * t749
  t753 = t580 ** 2
  t754 = 0.1e1 - t753
  t755 = t754 * t11
  t756 = t755 * t398
  t757 = t670 * t5
  t758 = t73 * t757
  t765 = -0.16e2 / 0.81e2 * t649 * t728 - 0.128e3 / 0.243e3 * t654 * t731
  t766 = t580 * t765
  t767 = t766 * t669
  t770 = t668 ** 2
  t771 = 0.1e1 / t770
  t772 = t771 * t17
  t773 = t705 * t772
  t778 = -0.16e2 / 0.81e2 * t660 * t728 - 0.128e3 / 0.243e3 * t665 * t731
  t779 = t112 * t778
  t780 = t246 * t779
  t785 = t721 * t722 * t724 / 0.4e1 + t735 * t702 / 0.2e1 - t689 * t746 / 0.2e1 - t750 * t333 / 0.12e2 + t756 * t758 / 0.36e2 + t767 * t114 / 0.4e1 - t773 * t780 / 0.4e1 - t706 * t333 / 0.12e2
  t786 = t713 * t785
  t787 = t712 * t786
  t790 = t675 * t10
  t791 = t4 * t278
  t792 = 0.1e1 / t709
  t793 = t792 * t713
  t794 = t791 * t793
  t797 = t4 * t72
  t799 = t223 ** 2
  t800 = 0.1e1 / t799
  t801 = t221 * t800
  t803 = jnp.log(0.2e1)
  t804 = t222 * t495 * t803
  t806 = t801 * t804 - 0.2e1 * t500
  t807 = t792 * t806
  t808 = t797 * t807
  t811 = 0.1e1 / t440
  t812 = t811 * t754
  t813 = t575 * t812
  t819 = t31 * t728
  t821 = t43 * t444
  t823 = t51 * t731
  t825 = -0.60121086419753086419753086419753086419753086419752e0 * t819 + 0.16403555555555555555555555555555555555555555555556e0 * t821 - 0.89731687242798353909465020576131687242798353909464e0 * t823
  t831 = t575 * t6 * t10
  t832 = t580 * t589
  t833 = t592 ** 2
  t834 = 0.1e1 / t833
  t837 = -0.16415822222222222222222222222222222222222222222223e1 * t819 - 0.26919506172839506172839506172839506172839506172840e1 * t823
  t838 = t834 * t837
  t843 = t618 * t631 * t115
  t851 = -0.16e2 / 0.81e2 * t610 * t728 - 0.128e3 / 0.243e3 * t615 * t731
  t852 = t606 * t851
  t855 = t630 ** 2
  t856 = 0.1e1 / t855
  t857 = t856 * t115
  t862 = -0.16e2 / 0.81e2 * t622 * t728 - 0.128e3 / 0.243e3 * t627 * t731
  t863 = t857 * t862
  t866 = t631 * t228
  t867 = t619 * t866
  t870 = t636 * t637
  t872 = t870 * t11 * t399
  t874 = t72 * t642 * t580
  t880 = t11 * jnp.pi * t15
  t881 = t644 * t754 * t880
  t884 = t765 * t669
  t885 = t645 * t884
  t888 = t657 * t771
  t889 = t645 * t888
  t891 = t111 * t113 * t778
  t896 = t813 * t124 * t112 * t589 * t593 / 0.4e1 + t576 * t581 * t825 * t593 / 0.4e1 - t831 * t832 * t838 / 0.4e1 + t721 * t722 * t843 / 0.4e1 + t852 * t632 / 0.2e1 - t619 * t863 / 0.2e1 - t867 * t333 / 0.12e2 - t872 * t874 * t757 / 0.36e2 + t881 * t758 / 0.36e2 + t885 * t114 / 0.4e1 - t889 * t891 / 0.4e1 - t671 * t333 / 0.12e2
  t897 = t896 * t54
  t898 = t897 * t10
  t899 = t797 * t793
  t902 = t4 * t18
  t903 = t902 * t807
  t906 = t811 * t396
  t907 = t575 * t906
  t913 = t17 * t232
  t915 = t33 * t913 * t21
  t918 = t54 * t239
  t919 = t918 * t1
  t920 = t53 * t919
  t922 = -0.15030271604938271604938271604938271604938271604939e0 * t915 + 0.41008888888888888888888888888888888888888888888888e-1 * t821 - 0.11216460905349794238683127572016460905349794238683e0 * t920
  t927 = t64 ** 2
  t928 = 0.1e1 / t927
  t929 = t61 * t928
  t932 = -0.41039555555555555555555555555555555555555555555556e0 * t915 - 0.33649382716049382716049382716049382716049382716051e0 * t920
  t933 = t929 * t932
  t938 = t97 * t110 * t115
  t946 = -0.4e1 / 0.81e2 * t83 * t234 - 0.16e2 / 0.243e3 * t91 * t241
  t947 = t79 * t946
  t950 = t109 ** 2
  t951 = 0.1e1 / t950
  t952 = t951 * t115
  t957 = -0.4e1 / 0.81e2 * t101 * t234 - 0.16e2 / 0.243e3 * t106 * t241
  t958 = t952 * t957
  t961 = t110 * t228
  t962 = t98 * t961
  t965 = t120 * t121
  t966 = t965 * t11
  t967 = t966 * t399
  t968 = t401 * t129
  t969 = t156 * t5
  t970 = t193 * t969
  t974 = t131 * t396
  t975 = t974 * t880
  t976 = t73 * t21
  t980 = t132 * t455
  t983 = t144 * t312
  t984 = t132 * t983
  t986 = t111 * t113 * t306
  t991 = t907 * t124 * t112 * t61 * t65 / 0.2e1 + t8 * t26 * t922 * t65 / 0.4e1 - t8 * t26 * t933 / 0.4e1 + t408 * t425 * t938 / 0.2e1 + t947 * t116 / 0.2e1 - t98 * t958 / 0.2e1 - t962 * t333 / 0.12e2 - t967 * t968 * t970 / 0.36e2 + t975 * t976 * t420 / 0.36e2 + t980 * t114 / 0.4e1 - t984 * t986 / 0.4e1 - t158 * t333 / 0.12e2
  t992 = t991 * t54
  t993 = t163 * t18
  t994 = t992 * t993
  t995 = t465 * t221
  t996 = t995 * t800
  t997 = t996 * t804
  t1000 = t162 * t993
  t1002 = 0.1e1 / t799 / t223
  t1003 = t995 * t1002
  t1004 = t222 ** 2
  t1006 = t803 ** 2
  t1007 = t1004 * t505 * t1006
  t1008 = t1003 * t1007
  t1012 = t222 * t505 * t1006
  t1013 = t996 * t1012
  t1015 = t465 * t499
  t1016 = t1015 * t800
  t1017 = t1016 * t804
  t1021 = t222 * t562 * t803
  t1022 = t996 * t1021
  t1024 = t163 * t72
  t1025 = t162 * t1024
  t1028 = t164 * t463 - 0.4e1 / 0.3e1 * t164 * t501 - 0.2e1 * t164 * t568 + 0.2e1 / 0.9e1 * t164 * t572 + 0.2e1 / 0.3e1 * t676 * t787 + 0.2e1 / 0.9e1 * t790 * t794 - 0.2e1 / 0.3e1 * t790 * t808 - 0.2e1 / 0.3e1 * t898 * t899 - 0.2e1 * t898 * t903 + 0.2e1 * t994 * t997 - 0.2e1 * t1000 * t1008 + t1000 * t1013 + 0.4e1 * t1000 * t1017 + t1000 * t1022 + 0.2e1 / 0.3e1 * t1025 * t997
  t1029 = t765 * t771
  t1030 = t645 * t1029
  t1033 = t84 * t252
  t1036 = t92 * t259
  t1039 = 0.112e3 / 0.243e3 * t660 * t1033 + 0.1408e4 / 0.729e3 * t665 * t1036
  t1041 = t111 * t113 * t1039
  t1049 = t856 * t228
  t1050 = t619 * t1049
  t1052 = t862 * t17 * t247
  t1059 = 0.112e3 / 0.243e3 * t610 * t1033 + 0.1408e4 / 0.729e3 * t615 * t1036
  t1060 = t606 * t1059
  t1069 = t111 * t332 * t778
  t1073 = 0.1e1 / t770 / t668
  t1074 = t657 * t1073
  t1075 = t645 * t1074
  t1076 = t778 ** 2
  t1078 = t111 * t113 * t1076
  t1081 = t5 * t778
  t1082 = t888 * t1081
  t1086 = t31 * t1033
  t1088 = 0.1e1 / t257
  t1089 = t43 * t1088
  t1091 = t51 * t1036
  t1093 = 0.14028253497942386831275720164609053497942386831275e1 * t1086 - 0.49210666666666666666666666666666666666666666666668e0 * t1089 + 0.32901618655692729766803840877914951989026063100137e1 * t1091
  t1099 = t278 * t642 * t580
  t1103 = t884 * t5
  t1107 = t637 ** 2
  t1108 = t636 * t1107
  t1109 = t1108 * t6
  t1110 = jnp.pi * t414
  t1111 = t1110 * t417
  t1112 = t1109 * t1111
  t1114 = t13 * t642 * t580
  t1115 = t1114 * t757
  t1118 = t870 * t6
  t1119 = t1118 * t1111
  t1120 = t642 * t754
  t1121 = t1120 * t13
  t1122 = t1121 * t757
  t1125 = t716 * t718
  t1126 = t1125 * t71
  t1127 = t424 * t618
  t1132 = 0.1e1 / t855 / t630
  t1134 = t862 ** 2
  t1135 = t1132 * t115 * t1134
  t1142 = 0.112e3 / 0.243e3 * t622 * t1033 + 0.1408e4 / 0.729e3 * t627 * t1036
  t1143 = t857 * t1142
  t1146 = t631 * t337
  t1147 = t619 * t1146
  t1150 = -t1030 * t891 / 0.2e1 - t889 * t1041 / 0.4e1 + t813 * t124 * t112 * t825 * t593 / 0.2e1 + t1050 * t1052 / 0.6e1 + t1060 * t632 / 0.2e1 - t813 * t124 * t35 * t589 * t593 / 0.12e2 + t889 * t1069 / 0.6e1 + t1075 * t1078 / 0.2e1 + t872 * t874 * t1082 / 0.18e2 + t576 * t581 * t1093 * t593 / 0.4e1 + t872 * t1099 * t757 / 0.36e2 - t872 * t874 * t1103 / 0.18e2 + t1112 * t1115 / 0.12e2 - t1119 * t1122 / 0.6e1 - t1126 * t1127 * t863 / 0.2e1 + t619 * t1135 - t852 * t863 - t619 * t1143 / 0.2e1 - t1147 * t342 / 0.18e2
  t1155 = 0.112e3 / 0.243e3 * t649 * t1033 + 0.1408e4 / 0.729e3 * t654 * t1036
  t1156 = t1155 * t669
  t1157 = t645 * t1156
  t1160 = t580 * t825
  t1164 = t852 * t866
  t1174 = 0.1e1 / t833 / t592
  t1175 = t837 ** 2
  t1176 = t1174 * t1175
  t1182 = 0.38303585185185185185185185185185185185185185185187e1 * t1086 + 0.98704855967078189300411522633744855967078189300413e1 * t1091
  t1183 = t834 * t1182
  t1189 = 0.1e1 / t602 / t583 / 0.3e1
  t1192 = t716 * t1189 * t11 * t30
  t1197 = t716 * t719 * t440
  t1198 = params.T * t444
  t1200 = t866 * t5
  t1204 = t599 * t56
  t1208 = t73 * t657
  t1209 = t771 * t5
  t1210 = t1209 * t778
  t1216 = t645 * t754 * t6 * t13
  t1221 = t851 * t631 * t115
  t1225 = t606 * t715
  t1226 = t40 * t15
  t1228 = t1225 * t1226 * t35
  t1229 = t31 * t17
  t1230 = t1229 * t843
  t1233 = t73 * t1103
  t1236 = t424 * t757
  t1239 = t27 * t5
  t1240 = t580 * t754
  t1242 = t1239 * t1240 * t11
  t1243 = t414 * t54
  t1250 = t575 * t812 * t15
  t1251 = t17 * t112
  t1252 = t589 * t834
  t1253 = t1252 * t837
  t1257 = t1157 * t114 / 0.4e1 - t831 * t1160 * t838 / 0.2e1 - t1164 * t333 / 0.6e1 + t867 * t322 / 0.9e1 - t885 * t333 / 0.6e1 + t671 * t322 / 0.9e1 + t831 * t832 * t1176 / 0.2e1 - t831 * t832 * t1183 / 0.4e1 + 0.3e1 / 0.4e1 * t1192 * t1033 * t843 - t1197 * t1198 * t618 * t1200 / 0.4e1 - 0.5e1 / 0.12e2 * t721 * t1204 * t843 - t881 * t1208 * t1210 / 0.18e2 - t1216 * t1111 * t757 / 0.6e1 + t721 * t722 * t1221 / 0.2e1 - t1228 * t1230 / 0.54e2 + t881 * t1233 / 0.18e2 - t881 * t1236 / 0.36e2 - t1242 * t1243 * t72 * t589 * t593 / 0.18e2 - t1250 * t1251 * t1253 / 0.2e1
  t1259 = (t1150 + t1257) * t54
  t1260 = t1259 * t10
  t1261 = t902 * t793
  t1264 = 0.1e1 / t950 / t109
  t1266 = t957 ** 2
  t1267 = t1264 * t115 * t1266
  t1274 = 0.28e2 / 0.243e3 * t101 * t254 + 0.176e3 / 0.729e3 * t106 * t261
  t1275 = t952 * t1274
  t1279 = t575 * t906 * t15
  t1283 = t966 * t398 * t73
  t1285 = t21 * t129 * t25
  t1286 = t5 * t306
  t1287 = t983 * t1286
  t1288 = t1285 * t1287
  t1291 = t965 * t6
  t1292 = t1291 * t1111
  t1294 = t1 * t129 * t396
  t1297 = t1294 * t13 * t144 * t969
  t1300 = t451 * t129
  t1304 = t350 * t969
  t1308 = t121 ** 2
  t1309 = t120 * t1308
  t1310 = t1309 * t6
  t1311 = t1310 * t1111
  t1313 = t1 * t13 * t129
  t1314 = t1313 * t970
  t1317 = t279 * t97
  t1320 = t291 * t938
  t1324 = t974 * t11 * t399
  t1328 = t132 * t396 * t415
  t1333 = t947 * t961
  t1336 = t110 * t337
  t1337 = t98 * t1336
  t1340 = t388 * t156
  t1341 = t132 * t1340
  t1348 = t98 * t1267 - t947 * t958 - t98 * t1275 / 0.2e1 - t1279 * t1251 * t933 + t1283 * t1288 / 0.18e2 - t1292 * t1297 / 0.3e1 + t967 * t1300 * t970 / 0.36e2 - t967 * t968 * t1304 / 0.18e2 + t1311 * t1314 / 0.6e1 - t276 * t1317 * t958 - t289 * t1320 / 0.54e2 - t1324 * t405 / 0.18e2 - t1328 * t421 / 0.3e1 - t980 * t333 / 0.6e1 - t1333 * t333 / 0.6e1 - t1337 * t342 / 0.18e2 + t1341 * t114 / 0.4e1 + t158 * t322 / 0.9e1 + t962 * t322 / 0.9e1
  t1349 = t33 * t436
  t1352 = t54 * t259
  t1354 = t53 * t1352 * t1
  t1356 = 0.35070633744855967078189300411522633744855967078191e0 * t1349 - 0.12302666666666666666666666666666666666666666666666e0 * t1089 + 0.41127023319615912208504801097393689986282578875171e0 * t1354
  t1362 = 0.1e1 / t927 / t64
  t1364 = t932 ** 2
  t1365 = t61 * t1362 * t1364
  t1376 = 0.95758962962962962962962962962962962962962962962964e0 * t1349 + 0.12338106995884773662551440329218106995884773662552e1 * t1354
  t1377 = t929 * t1376
  t1381 = t144 * t299
  t1382 = t132 * t1381
  t1384 = t111 * t113 * t307
  t1388 = t111 * t332 * t306
  t1391 = t349 * t312
  t1392 = t132 * t1391
  t1396 = t111 * t113 * t360
  t1403 = t922 * t928
  t1404 = t1403 * t932
  t1408 = t951 * t228
  t1409 = t98 * t1408
  t1411 = t957 * t17 * t247
  t1415 = t1239 * t412 * t11
  t1416 = t1243 * t72
  t1418 = t21 * t61 * t65
  t1423 = t961 * t5
  t1433 = t424 * t21
  t1438 = t946 * t110 * t115
  t1448 = 0.28e2 / 0.243e3 * t83 * t254 + 0.176e3 / 0.729e3 * t91 * t261
  t1449 = t79 * t1448
  t1452 = t8 * t26 * t1356 * t65 / 0.4e1 + t8 * t26 * t1365 / 0.2e1 - t907 * t124 * t35 * t61 * t65 / 0.6e1 - t8 * t26 * t1377 / 0.4e1 + t1382 * t1384 / 0.2e1 + t984 * t1388 / 0.6e1 - t1392 * t986 / 0.2e1 - t984 * t1396 / 0.4e1 + t907 * t124 * t112 * t922 * t65 - t8 * t26 * t1404 / 0.2e1 + t1409 * t1411 / 0.6e1 - t1415 * t1416 * t1418 / 0.9e1 - t443 * t445 * t97 * t1423 / 0.2e1 + t975 * t976 * t456 / 0.18e2 - 0.5e1 / 0.6e1 * t408 * t58 * t938 - t975 * t1433 * t420 / 0.36e2 + t408 * t425 * t1438 + 0.3e1 / 0.2e1 * t434 * t436 * t938 + t1449 * t116 / 0.2e1
  t1454 = (t1348 + t1452) * t54
  t1455 = t1454 * t163
  t1456 = t504 * t225
  t1458 = t897 * t163
  t1459 = t18 * t711
  t1460 = t1459 * t786
  t1464 = t499 * t800
  t1467 = t221 * t1002
  t1472 = -0.2e1 * t1467 * t1007 + t801 * t1012 + t801 * t1021 + 0.4e1 * t1464 * t804 - 0.2e1 * t567
  t1473 = t792 * t1472
  t1474 = t902 * t1473
  t1476 = t162 * t10
  t1477 = t902 * t199
  t1478 = t1476 * t1477
  t1497 = t408 * t425 * t293 / 0.2e1 + t330 * t190 / 0.2e1 - t177 * t282 / 0.2e1 - t320 * t333 / 0.12e2 + t400 * t401 * t420 / 0.36e2 + t381 * t114 / 0.4e1 - t314 * t353 / 0.4e1 - t194 * t333 / 0.12e2
  t1498 = t801 * t1497
  t1499 = t1498 * t804
  t1503 = 0.1e1 / t710 / t709
  t1504 = t18 * t1503
  t1505 = t785 ** 2
  t1506 = t713 * t1505
  t1507 = t1504 * t1506
  t1510 = t992 * t163
  t1511 = t504 * t500
  t1514 = t72 * t199
  t1515 = t225 * t1497
  t1516 = t1514 * t1515
  t1519 = t200 * t1515
  t1523 = 0.1e1 / t198 / t197
  t1524 = t18 * t1523
  t1525 = t1497 ** 2
  t1526 = t225 * t1525
  t1527 = t1524 * t1526
  t1530 = t500 * t1497
  t1531 = t200 * t1530
  t1537 = t505 * t495
  t1570 = t472 ** 2
  t1578 = t111 * t5 * t252
  t1598 = 0.1e1 / t18 / t257
  t1606 = 0.1e1 / t115 / t340 / t797 / 0.4e1
  t1627 = t340 * t4 * t239
  t1639 = -0.42522882146666666666666666666666666666666666666664e-3 * t513 * t514 * t493 - 0.34815249999999999999999999999999999999999999999999e-2 * t467 * t468 * t557 - 0.36104703703703703703703703703703703703703703703703e-2 * t467 * t252 * t206 * t215 + 0.46420333333333333333333333333333333333333333333332e-2 * t467 * t509 * t493 + 0.56697176195555555555555555555555555555555555555551e-3 * t513 * t239 * t473 * t215 + 0.61069333333333333333333333333333333333333333333332e-1 * t527 * t322 - 0.45801999999999999999999999999999999999999999999999e-1 * t474 * t560 * t333 - 0.3e1 * t207 * t556 * t492 * t215 - 0.10249013161558186666666666666666666666666666666666e-2 * t203 / t1570 * t215 * t2 * t1088 - 0.47498370370370370370370370370370370370370370370369e-1 * t475 * t1578 - t207 * (0.160e3 / 0.243e3 * t71 * t918 * t211 - 0.20e2 / 0.27e2 * t71 * t57 * t488 + 0.4e1 / 0.9e1 * t71 * t424 * t552 - 0.2e1 / 0.9e1 * t71 * t73 * (-0.18849876543209876543209876543209876543209876543210e0 * t71 * t918 * t115 - 0.28981685185185185185185185185185185185185185185186e0 * t442 * t1088 * t228 * t5 + 0.12723666666666666666666666666666666666666666666667e0 * t546 * t1598 * t337 * t548 - 0.42412222222222222222222222222222222222222222222224e-1 * t546 * t259 * t1606 * t54 * t9)) * t215 - 0.77905321923265066666666666666666666666666666666661e-4 * t2 * t1088 * t522 * t215 - 0.34815249999999999999999999999999999999999999999999e-2 * t467 * t468 * t560 + 0.74589269475555555555555555555555555555555555555548e-2 * t524 * t1627 - 0.55941952106666666666666666666666666666666666666662e-2 * t523 * t493 * t342 - 0.45801999999999999999999999999999999999999999999999e-1 * t474 * t557 * t333 - t207 * t559 * t492 * t215
  t1643 = f.my_piecewise3(t201, t218 * t1537 * t507 * t497 + t218 * t1639 * t497 + 0.3e1 * t496 * t507 * t562, 0)
  t1644 = t1643 * t224
  t1652 = t710 ** 2
  t1673 = t714 * t715 * t598 * t718
  t1674 = t444 * t688
  t1675 = t1674 * t702
  t1678 = t580 * t1155
  t1682 = t766 * t772
  t1684 = t246 * t112 * t1039
  t1687 = t84 * t1598
  t1690 = t257 * r0
  t1692 = 0.1e1 / t19 / t1690
  t1693 = t92 * t1692
  t1696 = -0.1120e4 / 0.729e3 * t660 * t1687 - 0.19712e5 / 0.2187e4 * t665 * t1693
  t1701 = t735 * t749
  t1708 = 0.112e3 / 0.243e3 * t680 * t1033 + 0.1408e4 / 0.729e3 * t685 * t1036
  t1709 = t606 * t1708
  t1713 = t1073 * t17
  t1716 = t246 * t112 * t1076
  t1720 = t246 * t35 * t778
  t1727 = t701 * t337
  t1733 = t689 * t1727
  t1736 = t770 ** 2
  t1737 = 0.1e1 / t1736
  t1740 = t1076 * t778
  t1745 = t705 * t1713
  t1751 = 0.1e1 / t738 / t700
  t1753 = t745 ** 2
  t1754 = t1751 * t115 * t1753
  t1757 = -t773 * t246 * t232 * t778 / 0.3e1 + t1673 * t1675 / 0.2e1 - 0.3e1 / 0.4e1 * t1678 * t772 * t780 - 0.3e1 / 0.4e1 * t1682 * t1684 - t773 * t246 * t112 * t1696 / 0.4e1 + t1701 * t322 / 0.3e1 - t1709 * t749 * t333 / 0.4e1 + 0.3e1 / 0.2e1 * t766 * t1713 * t1716 + t1682 * t1720 / 0.2e1 + t773 * t246 * t35 * t1039 / 0.4e1 - t735 * t1727 * t342 / 0.6e1 - 0.7e1 / 0.27e2 * t750 * t1578 + 0.2e1 / 0.9e1 * t1733 * t1627 - 0.3e1 / 0.2e1 * t705 * t1737 * t17 * t246 * t112 * t1740 - t1745 * t246 * t35 * t1076 / 0.2e1 + 0.3e1 * t735 * t1754
  t1762 = 0.112e3 / 0.243e3 * t692 * t1033 + 0.1408e4 / 0.729e3 * t697 * t1036
  t1763 = t740 * t1762
  t1776 = t738 ** 2
  t1783 = t599 * t239
  t1788 = t1225 * t398 * t56
  t1789 = t11 * t54
  t1791 = t749 * t5
  t1795 = 0.1e1 / t50
  t1798 = t1225 * t11 * t1795 * t15
  t1799 = t913 * t41
  t1803 = t1240 * t415
  t1804 = t417 * jnp.pi
  t1806 = t1804 * t657 * t1210
  t1810 = t734 * t701 * t115
  t1815 = t1225 * t1226 * t232
  t1816 = t1229 * t724
  t1837 = params.T * t1088
  t1846 = -0.1120e4 / 0.729e3 * t649 * t1687 - 0.19712e5 / 0.2187e4 * t654 * t1693
  t1851 = -0.3e1 / 0.2e1 * t735 * t1763 - t689 * t740 * (-0.1120e4 / 0.729e3 * t692 * t1687 - 0.19712e5 / 0.2187e4 * t697 * t1693) / 0.2e1 - 0.3e1 / 0.2e1 * t1709 * t746 - 0.3e1 * t689 / t1776 * t115 * t1753 * t745 + 0.10e2 / 0.9e1 * t721 * t1783 * t724 + t1788 * t1789 * t688 * t1791 / 0.108e3 - t1798 * t1799 * t724 / 0.54e2 + t1803 * t1806 / 0.2e1 - 0.5e1 / 0.4e1 * t721 * t1204 * t1810 + t1815 * t1816 / 0.18e2 - 0.15e2 / 0.4e1 * t1192 * t1687 * t724 - t1228 * t1229 * t1810 / 0.18e2 + 0.9e1 / 0.4e1 * t1192 * t1033 * t1810 - 0.3e1 / 0.4e1 * t1197 * t1198 * t734 * t1791 + 0.3e1 / 0.4e1 * t721 * t722 * t1708 * t701 * t115 + 0.9e1 / 0.8e1 * t1197 * t1837 * t688 * t1791 + t580 * t1846 * t669 * t114 / 0.4e1
  t1857 = t715 ** 2
  t1859 = t1857 * t598 * t718
  t1862 = t1678 * t669
  t1865 = t753 * t754
  t1866 = 0.1e1 / t30
  t1867 = 0.1e1 / t42
  t1869 = t1866 * t1867 * t17
  t1871 = t35 * jnp.pi
  t1872 = t1871 * t757
  t1882 = t755 * t399
  t1883 = t72 * t657
  t1885 = t1073 * t5 * t1076
  t1897 = t1209 * t1039
  t1909 = t716 * t1189
  t1910 = t1909 * t33
  t1915 = t1125 * t546
  t1916 = t17 * t1598
  t1922 = t1125 * t442
  t1929 = t754 ** 2
  t1931 = t1867 * t17
  t1941 = t767 * t322 / 0.3e1 - 0.7e1 / 0.27e2 * t706 * t1578 - t1859 * t1675 / 0.4e1 - t1862 * t333 / 0.4e1 + t1865 * t1869 * t1872 / 0.3e1 + t1803 * t45 * jnp.pi * t757 / 0.3e1 - t1803 * t1804 * t1103 / 0.2e1 + t1882 * t1883 * t1885 / 0.6e1 + t1882 * t278 * t657 * t1210 / 0.12e2 - t1882 * t72 * t765 * t1210 / 0.6e1 - t1882 * t1883 * t1897 / 0.12e2 + t606 * (-0.1120e4 / 0.729e3 * t680 * t1687 - 0.19712e5 / 0.2187e4 * t685 * t1693) * t702 / 0.2e1 - 0.9e1 / 0.4e1 * t1910 * t435 * t688 * t746 - t1915 * t1916 * t688 * t1727 * t4 / 0.4e1 + 0.3e1 / 0.4e1 * t1922 * t1674 * t739 * t228 * t745 * t5 - t1929 * t1866 * t1931 * t1872 / 0.6e1 - t689 * t1751 * t228 * t1753 * t17 * t247 / 0.2e1
  t1946 = t716 / t602 / t46 * t41 / 0.81e2
  t1947 = 0.1e1 / t1690
  t1948 = t42 * t1947
  t1952 = t424 * t1103
  t1955 = t1156 * t5
  t1956 = t73 * t1955
  t1963 = t424 * t688
  t1968 = 0.1e1 / t27 / jnp.pi
  t1971 = t1909 * t11 * t1968 * t32
  t1984 = t1225 * t40 * t288
  t1991 = t1606 * t2 * t1088
  t1999 = t57 * t757
  t2002 = t739 * t228
  t2005 = t745 * t17 * t247
  t2008 = t689 * t2002
  t2024 = t246 * t779 * t1039
  t2027 = 0.135e3 / 0.4e1 * t1946 * t1948 * t724 - t756 * t1952 / 0.12e2 + t756 * t1956 / 0.12e2 + 0.5e1 / 0.4e1 * t1126 * t57 * t688 * t746 + 0.3e1 / 0.2e1 * t1126 * t1963 * t1754 - 0.3e1 / 0.8e1 * t1971 * t1352 * t688 * t1791 - 0.3e1 / 0.2e1 * t1126 * t424 * t734 * t746 - 0.3e1 / 0.4e1 * t1126 * t1963 * t1763 + t1984 * t290 * t688 * t746 / 0.18e2 - t689 * t701 * t1991 / 0.3e1 + 0.3e1 * t689 * t1751 * t115 * t745 * t1762 + 0.19e2 / 0.324e3 * t756 * t1999 + t735 * t2002 * t2005 / 0.2e1 + t2008 * t1762 * t17 * t247 / 0.4e1 + t689 * t739 * t337 * t340 * t341 * t745 / 0.6e1 - t2008 * t111 * t321 * t745 / 0.3e1 + 0.3e1 / 0.2e1 * t1745 * t2024
  t2034 = t806 * t785
  t2062 = t689 * t1754 - t735 * t746 - t689 * t1763 / 0.2e1 + t706 * t322 / 0.9e1 - t767 * t333 / 0.6e1 + t1862 * t114 / 0.4e1 - t1803 * t1804 * t757 / 0.6e1 - t1882 * t1883 * t1210 / 0.18e2 - t1701 * t333 / 0.6e1 - t1733 * t342 / 0.18e2 - t1682 * t780 / 0.2e1 - t773 * t1684 / 0.4e1
  t2095 = t750 * t322 / 0.9e1 + t1745 * t1716 / 0.2e1 + t773 * t1720 / 0.6e1 + t1709 * t702 / 0.2e1 - t1126 * t1963 * t746 / 0.2e1 - t756 * t1236 / 0.36e2 + t2008 * t2005 / 0.6e1 + t756 * t1233 / 0.18e2 - 0.5e1 / 0.12e2 * t721 * t1204 * t724 + t721 * t722 * t1810 / 0.2e1 - t1228 * t1816 / 0.54e2 + 0.3e1 / 0.4e1 * t1192 * t1033 * t724 - t1197 * t1198 * t688 * t1791 / 0.4e1
  t2096 = t2062 + t2095
  t2097 = t713 * t2096
  t2104 = t1459 * t2034
  t2107 = t1459 * t2097
  t2109 = t466 * t225
  t2119 = t297 ** 2
  t2120 = 0.1e1 / t2119
  t2123 = t307 * t306
  t2151 = t269 / t76 / t46 * t43 / 0.162e3
  t2161 = t84 * t1598 * t21
  t2165 = t92 * t1692 * t1
  t2168 = -0.280e3 / 0.729e3 * t147 * t2161 - 0.2464e4 / 0.2187e4 * t152 * t2165
  t2186 = -0.3e1 / 0.2e1 * t193 * t2120 * t17 * t246 * t112 * t2123 - t301 * t246 * t35 * t307 / 0.2e1 - 0.7e1 / 0.27e2 * t320 * t1578 + 0.3e1 / 0.2e1 * t350 * t300 * t309 - 0.3e1 / 0.4e1 * t389 * t313 * t353 - t314 * t246 * t232 * t306 / 0.3e1 - t265 * t319 * t333 / 0.4e1 + 0.135e3 * t2151 * t1947 * t176 * t190 + t351 * t316 / 0.2e1 + 0.2e1 / 0.9e1 * t339 * t1627 - t314 * t246 * t112 * t2168 / 0.4e1 + t331 * t322 / 0.3e1 + t314 * t246 * t35 * t360 / 0.4e1 - t330 * t338 * t342 / 0.6e1 - 0.3e1 / 0.4e1 * t351 * t362 - 0.7e1 / 0.27e2 * t194 * t1578
  t2195 = -0.280e3 / 0.729e3 * t136 * t2161 - 0.2464e4 / 0.2187e4 * t141 * t2165
  t2201 = t268 * t269 * t271
  t2206 = t396 ** 2
  t2209 = t1871 * t420
  t2213 = t246 * t361 * t306
  t2237 = t285 * jnp.pi * t15 * t56 * t11
  t2246 = t285 * t11 * t1795 * t15 * t17
  t2247 = t233 * t41
  t2251 = t433 * t11
  t2252 = t1968 * t32
  t2260 = t28 * params.T
  t2263 = t1 * t176
  t2279 = t286 * t15 * t232 * t11
  t2282 = t381 * t322 / 0.3e1 - t390 * t333 / 0.4e1 + t25 * t2195 * t156 * t114 / 0.4e1 + 0.2e1 * t2201 * t444 * t176 * t190 - 0.2e1 / 0.3e1 * t2206 * t1866 * t1931 * t2209 + 0.3e1 / 0.2e1 * t301 * t2213 + t330 * t229 * t248 / 0.2e1 + t230 * t377 * t17 * t247 / 0.4e1 + t79 * (-0.280e3 / 0.729e3 * t168 * t2161 - 0.2464e4 / 0.2187e4 * t173 * t2165) * t190 / 0.2e1 - t289 * t291 * t427 / 0.18e2 + t2237 * t54 * t21 * t176 * t447 / 0.108e3 - t2246 * t2247 * t293 / 0.54e2 - 0.3e1 / 0.4e1 * t2251 * t2252 * t54 * t259 * t21 * t176 * t447 - t273 * t2260 * t1598 * t2263 * t189 * t337 * t4 * t17 / 0.2e1 + 0.5e1 / 0.2e1 * t276 * t93 * t176 * t282 + 0.3e1 * t276 * t280 * t369 + t2279 * t294 / 0.18e2
  t2294 = t273 * t440 * params.T * t444
  t2310 = t2251 * t30 * t32 * t17
  t2316 = t115 * t244
  t2321 = t269 ** 2
  t2323 = t2321 * t271 * t444
  t2344 = t226 ** 2
  t2353 = t1088 * t1
  t2360 = t45 * t1 * jnp.pi * t420
  t2366 = t412 * t6 * t13 * t414 * t417 * t1 * jnp.pi * t144 * t404 + 0.3e1 / 0.2e1 * t2294 * t2263 * t227 * t228 * t244 * t5 - 0.3e1 * t276 * t279 * t329 * t282 - 0.3e1 / 0.2e1 * t276 * t280 * t378 - 0.9e1 / 0.2e1 * t2310 * t253 * t176 * t282 + t289 * t291 * t176 * t227 * t2316 / 0.18e2 - t2323 * t293 + 0.3e1 * t177 * t366 * t2316 * t377 - t177 * t189 * t1991 / 0.3e1 + 0.3e1 * t330 * t369 - 0.3e1 / 0.2e1 * t330 * t378 - t177 * t281 * (-0.280e3 / 0.729e3 * t180 * t2161 - 0.2464e4 / 0.2187e4 * t185 * t2165) / 0.2e1 - 0.3e1 * t177 / t2344 * t115 * t368 * t244 - 0.3e1 / 0.2e1 * t265 * t282 + 0.9e1 / 0.4e1 * t443 * t2353 * t176 * t447 + 0.2e1 / 0.3e1 * t416 * t2360 - 0.5e1 / 0.2e1 * t408 * t58 * t427
  t2368 = t401 * t349 * t404
  t2372 = t402 * t403 * t360
  t2380 = t419 * t456
  t2393 = t451 * t144 * t404
  t2398 = t402 * t299 * t5 * t307
  t2401 = t1916 * t21
  t2426 = t1340 * t5
  t2430 = t56 * t21
  t2434 = t395 * t396
  t2438 = -t400 * t2368 / 0.6e1 - t400 * t2372 / 0.12e2 + 0.3e1 / 0.2e1 * t408 * t425 * t264 * t189 * t115 - t416 * t2380 + 0.9e1 / 0.2e1 * t434 * t436 * t427 - 0.3e1 / 0.2e1 * t443 * t445 * t329 * t447 + 0.20e2 / 0.9e1 * t408 * t919 * t293 + t400 * t2393 / 0.12e2 + t400 * t2398 / 0.6e1 - 0.15e2 / 0.2e1 * t434 * t2401 * t293 - t177 * t366 * t228 * t368 * t17 * t247 / 0.2e1 - t230 * t245 * t246 * t232 / 0.3e1 + t177 * t227 * t337 * t244 * t54 * t29 * t4 * t56 / 0.6e1 - t400 * t451 * t456 / 0.12e2 + t400 * t401 * t2426 / 0.12e2 + 0.19e2 / 0.324e3 * t400 * t2430 * t420 + 0.4e1 / 0.3e1 * t2434 * t1869 * t2209
  t2445 = 0.2e1 / 0.9e1 * t790 * t791 * t807 - 0.2e1 / 0.3e1 * t164 * t504 * t1644 + t1259 * t163 * t1460 - 0.2e1 * t1510 * t568 + 0.2e1 * t676 * t18 / t1652 * t713 * t1505 * t785 - 0.4e1 / 0.3e1 * t1510 * t501 + 0.2e1 / 0.3e1 * t1458 * t787 + t676 * t1459 * t1472 * t785 + t676 * t1459 * t713 * (t1757 + t1851 + t1941 + t2027) / 0.3e1 + 0.2e1 / 0.3e1 * t676 * t712 * t2034 + t676 * t712 * t2097 / 0.3e1 + 0.4e1 / 0.9e1 * t164 * t571 * t500 + 0.2e1 * t1458 * t2104 + t1458 * t2107 - t1455 * t2109 / 0.3e1 + 0.2e1 / 0.9e1 * t898 * t794 - 0.10e2 / 0.81e2 * t790 * t341 * t793 - t1260 * t899 / 0.3e1 + t164 * t200 * t225 * (t2186 + t2282 + t2366 + t2438) / 0.3e1
  t2452 = t799 ** 2
  t2453 = 0.1e1 / t2452
  t2457 = t1006 * t803
  t2458 = t1004 * t222 * t1537 * t2457
  t2474 = t222 * t1537 * t2457
  t2484 = t222 * t1639 * t803
  t2504 = t1004 * t1537 * t2457
  t2511 = -0.2e1 * t1455 * t1511 - t898 * t1474 - t1260 * t903 - 0.2e1 * t994 * t1008 + 0.2e1 * t1000 * t995 * t2453 * t2458 + 0.4e1 / 0.3e1 * t1025 * t1017 + t1025 * t1022 / 0.3e1 - 0.2e1 / 0.3e1 * t1025 * t1008 + t1025 * t1013 / 0.3e1 + 0.2e1 / 0.3e1 * t992 * t1024 * t997 + t1000 * t996 * t2474 / 0.3e1 + t994 * t1013 - 0.2e1 / 0.9e1 * t162 * t163 * t278 * t997 + t1000 * t996 * t2484 / 0.3e1 + 0.2e1 * t1000 * t465 * t566 * t800 * t804 + 0.2e1 * t1000 * t1016 * t1021 - 0.4e1 * t1000 * t1015 * t1002 * t1007 + 0.2e1 * t1000 * t1016 * t1012 - 0.2e1 * t1000 * t1003 * t2504 - t790 * t797 * t1473 / 0.3e1
  t2525 = t1476 * t902 * t465
  t2528 = t495 * t1006 * t562
  t2529 = t1467 * t1004 * t2528
  t2533 = t801 * t222 * t2528
  t2594 = -0.12e2 * t499 * t1002 * t1007 + 0.6e1 * t221 * t2453 * t2458 + 0.6e1 * t566 * t800 * t804 + 0.6e1 * t1464 * t1012 + 0.6e1 * t1464 * t1021 - 0.6e1 * t1467 * t2504 + t801 * t2474 + t801 * t2484 - 0.2e1 * t1644 - 0.6e1 * t2529 + 0.3e1 * t2533
  t2611 = -0.2e1 / 0.3e1 * t1476 * t797 * t199 * t1499 - t1478 * t801 * t461 * t804 + 0.2e1 * t1478 * t1467 * t1497 * t1007 - 0.2e1 * t2525 * t2529 + t2525 * t2533 - t1478 * t1498 * t1012 - t1478 * t1498 * t1021 - 0.4e1 * t1478 * t1464 * t1497 * t804 + 0.2e1 * t1476 * t902 * t1523 * t801 * t1525 * t804 - 0.2e1 * t992 * t10 * t1477 * t1499 + t676 * t1459 * t806 * t2096 - 0.10e2 / 0.81e2 * t164 * t56 * t465 * t225 - 0.2e1 * t676 * t1504 * t806 * t1505 + 0.2e1 / 0.9e1 * t1510 * t572 - 0.2e1 * t1458 * t1507 - 0.2e1 * t1000 * t1523 * t221 * t224 * t461 * t1497 - t790 * t902 * t792 * t2594 / 0.3e1 + 0.2e1 * t164 * t200 * t567 * t1497 - 0.4e1 * t164 * t1524 * t500 * t1525 - 0.2e1 / 0.3e1 * t164 * t72 * t1523 * t1526
  t2615 = t198 ** 2
  t2709 = -t889 * t111 * t321 * t778 / 0.3e1 - t619 * t1132 * t228 * t1134 * t17 * t247 / 0.2e1 + t1050 * t1142 * t17 * t247 / 0.4e1 + t852 * t1049 * t1052 / 0.2e1 - t1050 * t111 * t321 * t862 / 0.3e1 + 0.3e1 / 0.2e1 * t831 * t832 * t1174 * t837 * t1182 + t619 * t856 * t337 * t340 * t341 * t862 / 0.6e1 - 0.3e1 / 0.4e1 * t645 * t1155 * t771 * t891 - t1075 * t111 * t332 * t1076 / 0.2e1 + t813 * t124 * t232 * t589 * t593 / 0.9e1 - 0.3e1 / 0.2e1 * t645 * t657 * t1737 * t111 * t113 * t1740 + 0.3e1 / 0.4e1 * t813 * t124 * t112 * t1093 * t593
  t2715 = t13 * t1867
  t2718 = t2715 * t417 * t589 * t593
  t2742 = t444 * t618
  t2743 = t2742 * t632
  t2746 = t31 * t1687
  t2748 = t43 * t1947
  t2750 = t51 * t1693
  t2758 = t1867 * t35
  t2774 = 0.135e3 / 0.4e1 * t1946 * t1948 * t843 - t1239 * t1929 * t6 * t2718 / 0.6e1 + t889 * t111 * t332 * t1039 / 0.4e1 - t813 * t124 * t35 * t825 * t593 / 0.4e1 + 0.3e1 / 0.2e1 * t645 * t765 * t1073 * t1078 - 0.3e1 / 0.4e1 * t1030 * t1041 - t889 * t111 * t113 * t1696 / 0.4e1 + t1030 * t1069 / 0.2e1 - t1859 * t2743 / 0.4e1 + t576 * t581 * (-0.46760844993141289437585733882030178326474622770917e1 * t2746 + 0.19684266666666666666666666666666666666666666666667e1 * t2748 - 0.15354088705989940557841792409693644261545496113397e2 * t2750) * t593 / 0.4e1 + t870 * jnp.pi * t2758 * t642 * t1240 * t1866 * t17 * t657 * t669 * t5 / 0.2e1 - t1112 * t1114 * t1082 / 0.4e1 + t1119 * t1121 * t1082 / 0.2e1
  t2827 = t2758 * t1866
  t2837 = -t872 * t1099 * t1082 / 0.12e2 - t872 * t874 * t1074 * t5 * t1076 / 0.6e1 + t872 * t874 * t1029 * t1081 / 0.6e1 + t872 * t874 * t888 * t5 * t1039 / 0.12e2 + t606 * (-0.1120e4 / 0.729e3 * t610 * t1687 - 0.19712e5 / 0.2187e4 * t615 * t1693) * t632 / 0.2e1 - t619 * t631 * t1991 / 0.3e1 + 0.3e1 * t619 * t1132 * t115 * t862 * t1142 - 0.3e1 / 0.4e1 * t1126 * t1127 * t1143 + 0.3e1 / 0.4e1 * t1922 * t2742 * t856 * t228 * t862 * t5 - 0.3e1 / 0.2e1 * t1126 * t424 * t851 * t863 - 0.3e1 / 0.8e1 * t1971 * t1352 * t618 * t1200 + t1108 * jnp.pi * t2827 * t1120 * t17 * t757 / 0.4e1 + 0.5e1 / 0.4e1 * t1126 * t57 * t618 * t863
  t2859 = t1110 * t45
  t2891 = t645 * t754 * t415 * t1806 / 0.2e1 - t636 * t1107 * t637 * jnp.pi * t2827 * t17 * t642 * t580 * t757 / 0.12e2 + t1984 * t290 * t618 * t863 / 0.18e2 - 0.9e1 / 0.4e1 * t1910 * t435 * t618 * t863 + t1118 * t2859 * t1122 / 0.3e1 + t1112 * t1114 * t1103 / 0.4e1 - t1119 * t1121 * t1103 / 0.2e1 - t1109 * t2859 * t1115 / 0.6e1 - t1915 * t1916 * t618 * t1146 * t4 / 0.4e1 - t872 * t874 * t1955 / 0.12e2 + t872 * t1099 * t1103 / 0.12e2 - 0.19e2 / 0.324e3 * t872 * t56 * t642 * t580 * t757 + 0.3e1 / 0.2e1 * t1126 * t1127 * t1135
  t2912 = t833 ** 2
  t2931 = -t831 * t832 * t834 * (-0.12767861728395061728395061728395061728395061728396e2 * t2746 - 0.46062266117969821673525377229080932784636488340193e2 * t2750) / 0.4e1 - t1060 * t866 * t333 / 0.4e1 - 0.7e1 / 0.27e2 * t867 * t1578 + t885 * t322 / 0.3e1 - 0.7e1 / 0.27e2 * t671 * t1578 + t1164 * t322 / 0.3e1 - 0.3e1 / 0.2e1 * t831 * t832 / t2912 * t1175 * t837 + 0.2e1 / 0.9e1 * t1147 * t1627 - t1157 * t333 / 0.4e1 + t1673 * t2743 / 0.2e1 + 0.3e1 / 0.2e1 * t831 * t1160 * t1176 - t852 * t1146 * t342 / 0.6e1
  t2943 = t855 ** 2
  t2978 = t645 * t1846 * t669 * t114 / 0.4e1 - 0.3e1 / 0.4e1 * t831 * t580 * t1093 * t838 - 0.3e1 / 0.4e1 * t831 * t1160 * t1183 - 0.3e1 * t619 / t2943 * t115 * t1134 * t862 - 0.3e1 / 0.2e1 * t1060 * t863 - 0.3e1 / 0.2e1 * t852 * t1143 - t619 * t857 * (-0.1120e4 / 0.729e3 * t622 * t1687 - 0.19712e5 / 0.2187e4 * t627 * t1693) / 0.2e1 + 0.3e1 * t852 * t1135 - t1798 * t1799 * t843 / 0.54e2 - 0.5e1 / 0.4e1 * t721 * t1204 * t1221 + t1815 * t1230 / 0.18e2 - 0.15e2 / 0.4e1 * t1192 * t1687 * t843 - t1216 * t1111 * t1103 / 0.2e1
  t2984 = t36 * jnp.pi
  t3030 = t644 * t753 * t754 * t1866 * t1867 * t2984 * t757 / 0.3e1 - 0.3e1 / 0.4e1 * t1197 * t1198 * t851 * t1200 + 0.9e1 / 0.8e1 * t1197 * t1837 * t618 * t1200 + t881 * t424 * t657 * t1210 / 0.12e2 + t881 * t1208 * t1885 / 0.6e1 - t881 * t73 * t765 * t1210 / 0.6e1 - t881 * t1208 * t1897 / 0.12e2 + 0.10e2 / 0.9e1 * t721 * t1783 * t843 + t1216 * t2859 * t757 / 0.3e1 + t1242 * t1416 * t1253 / 0.6e1 + 0.3e1 / 0.4e1 * t721 * t722 * t1059 * t631 * t115 - t1228 * t1229 * t1221 / 0.18e2 + 0.9e1 / 0.4e1 * t1192 * t1033 * t1221
  t3080 = t1788 * t1789 * t618 * t1200 / 0.108e3 - t1242 * t1243 * t72 * t825 * t593 / 0.6e1 + t1250 * t36 * t1253 / 0.4e1 + t1242 * t1243 * t278 * t589 * t593 / 0.18e2 + 0.3e1 / 0.2e1 * t645 * t1074 * t17 * t2024 + t881 * t1956 / 0.12e2 - t881 * t1952 / 0.12e2 + 0.19e2 / 0.324e3 * t881 * t1999 - t644 * t1929 * t1869 * t1872 / 0.6e1 + 0.3e1 / 0.2e1 * t1250 * t1251 * t589 * t1174 * t1175 - 0.3e1 / 0.4e1 * t1250 * t1251 * t1252 * t1182 - 0.3e1 / 0.2e1 * t1250 * t1251 * t825 * t834 * t837 + t1239 * t1865 * t6 * t2718 / 0.3e1
  t3093 = t927 ** 2
  t3115 = t33 * t2401
  t3119 = t53 * t54 * t1692 * t1
  t3149 = 0.2e1 / 0.9e1 * t907 * t124 * t232 * t61 * t65 - 0.3e1 / 0.2e1 * t8 * t26 * t61 / t3093 * t1364 * t932 - 0.3e1 / 0.2e1 * t132 * t144 * t2120 * t111 * t113 * t2123 - t1382 * t111 * t332 * t307 / 0.2e1 - 0.3e1 / 0.4e1 * t8 * t26 * t1403 * t1376 - t8 * t26 * t929 * (-0.31919654320987654320987654320987654320987654320988e1 * t3115 - 0.57577832647462277091906721536351165980795610425243e1 * t3119) / 0.4e1 + 0.3e1 / 0.2e1 * t132 * t349 * t299 * t1384 + t984 * t111 * t332 * t360 / 0.4e1 - t907 * t124 * t35 * t922 * t65 / 0.2e1 - 0.3e1 / 0.4e1 * t1392 * t1396 - t984 * t111 * t113 * t2168 / 0.4e1 - t984 * t111 * t321 * t306 / 0.3e1
  t3207 = -t98 * t1264 * t228 * t1266 * t17 * t247 / 0.2e1 + t1409 * t1274 * t17 * t247 / 0.4e1 + 0.3e1 / 0.2e1 * t8 * t26 * t922 * t1362 * t1364 - 0.3e1 / 0.4e1 * t8 * t26 * t1356 * t928 * t932 + 0.3e1 / 0.2e1 * t907 * t124 * t112 * t1356 * t65 + t947 * t1408 * t1411 / 0.2e1 + t98 * t951 * t337 * t340 * t341 * t957 / 0.6e1 - 0.3e1 / 0.4e1 * t132 * t388 * t312 * t986 - t1409 * t111 * t321 * t957 / 0.3e1 + t1392 * t1388 / 0.2e1 - t966 * t398 * t424 * t1288 / 0.12e2 - t1283 * t1285 * t1381 * t5 * t307 / 0.6e1 + t1283 * t1285 * t1391 * t1286 / 0.6e1
  t3214 = t1110 * t418
  t3229 = t115 * t957
  t3267 = t1283 * t1285 * t983 * t5 * t360 / 0.12e2 - t1310 * t3214 * t13 * t129 * t25 * t1287 / 0.2e1 + t1291 * t3214 * t129 * t396 * t13 * t1287 + t1328 * t419 * t1287 + t289 * t291 * t97 * t951 * t3229 / 0.18e2 + t1311 * t1313 * t1304 / 0.2e1 - t1292 * t1294 * t13 * t349 * t969 + 0.2e1 * t965 * jnp.pi * t2758 * t129 * t412 * t1866 * t17 * t144 * t969 - t1310 * t2859 * t1314 / 0.3e1 + t967 * t1300 * t1304 / 0.12e2 - t967 * t968 * t389 * t969 / 0.12e2 - 0.19e2 / 0.324e3 * t967 * t2430 * t129 * t970 + 0.2e1 / 0.3e1 * t1291 * t2859 * t1297
  t3296 = t17 * t129
  t3319 = t79 * (-0.280e3 / 0.729e3 * t83 * t2161 - 0.2464e4 / 0.2187e4 * t91 * t2165) * t116 / 0.2e1 - 0.3e1 / 0.2e1 * t276 * t1317 * t1275 + t1324 * t2398 / 0.6e1 + t1324 * t2393 / 0.12e2 - t1324 * t2368 / 0.6e1 - t1324 * t2372 / 0.12e2 + 0.3e1 / 0.2e1 * t2294 * t1 * t97 * t951 * t228 * t957 * t5 + t1309 * jnp.pi * t2827 * t3296 * t396 * t420 - t120 * t1308 * t121 * jnp.pi * t2827 * t3296 * t25 * t420 / 0.3e1 + 0.2e1 / 0.3e1 * t1328 * t2360 + 0.5e1 / 0.2e1 * t276 * t93 * t97 * t958 + t2279 * t1320 / 0.18e2 - t2246 * t2247 * t938 / 0.54e2
  t3335 = t21 * t97 * t110 * t228 * t5 * t54
  t3374 = t1239 * t25 * t397 * t414 * t976 * t933 / 0.3e1 - t1328 * t2380 - 0.3e1 / 0.4e1 * t2251 * t2252 * t259 * t3335 - 0.9e1 / 0.2e1 * t2310 * t253 * t97 * t958 - t289 * t291 * t1438 / 0.18e2 + t2237 * t3335 / 0.108e3 - t273 * t2260 * t17 * t1598 * t1 * t97 * t1336 * t4 / 0.2e1 + 0.3e1 * t276 * t1317 * t1267 - 0.3e1 * t276 * t279 * t946 * t958 + 0.2e1 / 0.9e1 * t1337 * t1627 - t1341 * t333 / 0.4e1 + t8 * t26 * (-0.11690211248285322359396433470507544581618655692730e1 * t3115 + 0.49210666666666666666666666666666666666666666666664e0 * t2748 - 0.19192610882487425697302240512117055326931870141746e1 * t3119) * t65 / 0.4e1
  t3411 = t950 ** 2
  t3418 = -t947 * t1336 * t342 / 0.6e1 - t1449 * t961 * t333 / 0.4e1 - 0.7e1 / 0.27e2 * t158 * t1578 + t980 * t322 / 0.3e1 - 0.7e1 / 0.27e2 * t962 * t1578 + 0.135e3 * t2151 * t1947 * t97 * t116 + t1333 * t322 / 0.3e1 + t132 * t2195 * t156 * t114 / 0.4e1 + 0.3e1 * t947 * t1267 - 0.3e1 / 0.2e1 * t947 * t1275 - t98 * t952 * (-0.280e3 / 0.729e3 * t101 * t2161 - 0.2464e4 / 0.2187e4 * t106 * t2165) / 0.2e1 - 0.3e1 / 0.2e1 * t1449 * t958 - 0.3e1 * t98 / t3411 * t115 * t1266 * t957
  t3440 = t1 * t61 * t65
  t3472 = -t2323 * t938 - t98 * t110 * t1991 / 0.3e1 + 0.3e1 * t98 * t1264 * t3229 * t1274 - 0.3e1 / 0.2e1 * t1279 * t1251 * t1377 - 0.2e1 / 0.3e1 * t131 * t2206 * t1869 * t2209 - 0.2e1 / 0.3e1 * t1239 * t2206 * t6 * t13 * t1867 * t417 * t3440 - 0.3e1 * t1279 * t1251 * t1404 + t1279 * t36 * t933 / 0.2e1 + 0.3e1 / 0.2e1 * t3 * t7 * t10 * t25 * t61 * t1362 * t932 * t1376 + 0.3e1 * t1279 * t1251 * t1365 + 0.3e1 / 0.2e1 * t132 * t1381 * t17 * t2213 - 0.3e1 / 0.2e1 * t443 * t445 * t946 * t1423 + 0.20e2 / 0.9e1 * t408 * t919 * t938
  t3527 = -0.5e1 / 0.2e1 * t408 * t58 * t1438 - 0.15e2 / 0.2e1 * t434 * t2401 * t938 + 0.9e1 / 0.2e1 * t434 * t436 * t1438 + 0.4e1 / 0.3e1 * t131 * t395 * t396 * t1866 * t1867 * t2984 * t420 + 0.4e1 / 0.3e1 * t1239 * t2434 * t6 * t2715 * t417 * t3440 + t975 * t976 * t2426 / 0.12e2 + 0.19e2 / 0.324e3 * t975 * t57 * t21 * t420 + t1415 * t1243 * t278 * t1418 / 0.9e1 - t1415 * t1416 * t21 * t922 * t65 / 0.3e1 + 0.3e1 / 0.2e1 * t408 * t425 * t1448 * t110 * t115 + 0.9e1 / 0.4e1 * t443 * t2353 * t97 * t1423 - t975 * t1433 * t456 / 0.12e2 + 0.2e1 * t2201 * t444 * t97 * t116
  t3546 = t164 * t1514 * t462 / 0.3e1 + 0.2e1 * t164 * t18 / t2615 * t225 * t1525 * t1497 + t1510 * t463 + 0.2e1 * t164 * t200 * t500 * t461 - 0.2e1 * t1510 * t1527 + t1455 * t1519 - 0.2e1 / 0.3e1 * t898 * t808 + 0.4e1 * t994 * t1017 + t994 * t1022 + t1454 * t993 * t997 - 0.2e1 * t676 * t1504 * t2097 * t785 + 0.4e1 * t1510 * t1531 + 0.4e1 / 0.3e1 * t164 * t1514 * t1530 + 0.2e1 / 0.3e1 * t1510 * t1516 - 0.2e1 / 0.9e1 * t164 * t278 * t199 * t1515 - (t2709 + t2774 + t2837 + t2891 + t2931 + t2978 + t3030 + t3080) * t54 * t10 * t1261 / 0.3e1 - (t3149 + t3207 + t3267 + t3319 + t3374 + t3418 + t3472 + t3527) * t54 * t163 * t1456 / 0.3e1 - 0.2e1 / 0.3e1 * t164 * t466 * t567 - 0.2e1 / 0.9e1 * t676 * t278 * t711 * t786 - 0.2e1 / 0.3e1 * t676 * t72 * t1503 * t1506
  t3555 = -t1260 * t1261 - t1455 * t1456 + 0.2e1 * t1458 * t1460 - t790 * t1474 - 0.2e1 * t1478 * t1499 - 0.2e1 * t676 * t1507 - 0.4e1 * t1510 * t1511 + 0.2e1 / 0.3e1 * t164 * t1516 + 0.2e1 * t1510 * t1519 - 0.2e1 * t164 * t1527 + 0.4e1 * t164 * t1531 + r0 * (t2445 + t2511 + t2611 + t3546) - 0.2e1 / 0.3e1 * t1510 * t2109 + 0.2e1 * t676 * t2104 + t676 * t2107
  v3rho3_0_ = t1028 + t3555

  res = {'v3rho3': v3rho3_0_}
  return res
