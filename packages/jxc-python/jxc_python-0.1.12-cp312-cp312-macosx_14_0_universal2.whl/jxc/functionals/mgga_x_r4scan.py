"""Generated from mgga_x_r4scan.mpl."""

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))
  params_da4_raw = params.da4
  if isinstance(params_da4_raw, (str, bytes, dict)):
    params_da4 = params_da4_raw
  else:
    try:
      params_da4_seq = list(params_da4_raw)
    except TypeError:
      params_da4 = params_da4_raw
    else:
      params_da4_seq = np.asarray(params_da4_seq, dtype=np.float64)
      params_da4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_da4_seq))
  params_dp2_raw = params.dp2
  if isinstance(params_dp2_raw, (str, bytes, dict)):
    params_dp2 = params_dp2_raw
  else:
    try:
      params_dp2_seq = list(params_dp2_raw)
    except TypeError:
      params_dp2 = params_dp2_raw
    else:
      params_dp2_seq = np.asarray(params_dp2_seq, dtype=np.float64)
      params_dp2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp2_seq))
  params_dp4_raw = params.dp4
  if isinstance(params_dp4_raw, (str, bytes, dict)):
    params_dp4 = params_dp4_raw
  else:
    try:
      params_dp4_seq = list(params_dp4_raw)
    except TypeError:
      params_dp4 = params_dp4_raw
    else:
      params_dp4_seq = np.asarray(params_dp4_seq, dtype=np.float64)
      params_dp4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp4_seq))
  params_eta_raw = params.eta
  if isinstance(params_eta_raw, (str, bytes, dict)):
    params_eta = params_eta_raw
  else:
    try:
      params_eta_seq = list(params_eta_raw)
    except TypeError:
      params_eta = params_eta_raw
    else:
      params_eta_seq = np.asarray(params_eta_seq, dtype=np.float64)
      params_eta = np.concatenate((np.array([np.nan], dtype=np.float64), params_eta_seq))
  params_k1_raw = params.k1
  if isinstance(params_k1_raw, (str, bytes, dict)):
    params_k1 = params_k1_raw
  else:
    try:
      params_k1_seq = list(params_k1_raw)
    except TypeError:
      params_k1 = params_k1_raw
    else:
      params_k1_seq = np.asarray(params_k1_seq, dtype=np.float64)
      params_k1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k1_seq))

  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  r2scan_alpha = lambda x, t: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  r2scan_f_alpha_neg = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  Cn = 20 / 27 + params_eta * 5 / 3

  df2 = lambda ff: jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0)

  df4 = lambda ff: jnp.sum(jnp.array([(i - 1) * (i - 2) * ff[9 - i] for i in range(2, 8 + 1)]), axis=0)

  r4scan_dFdamp = lambda p, a: 2 * a ** 2 / (1 + a ** 4) * jnp.exp(-(1 - a) ** 2 / params_da4 ** 2 - p ** 2 / params_dp4 ** 4)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  Caa = lambda ff: 73 / 5000 - df4(ff) / 2 * (scan_h0x - 1)

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  Cpa = lambda ff: 511 / 13500 - 73 / 1500 * params_eta - df2(ff) * (Cn * C2(ff) + MU_GE)

  Cpp = lambda ff: 146 / 2025 * (params_eta * 3 / 4 + 2 / 3) ** 2 - 73 / 405 * (params_eta * 3 / 4 + 2 / 3) + (Cn * C2(ff) + MU_GE) ** 2 / params_k1

  r4scan_dF = lambda ff, p, a: (C2(ff) * (1 - a - Cn * p) + Caa(ff) * (1 - a) ** 2 + Cpa(ff) * p * (1 - a) + Cpp(ff) * p ** 2) * r4scan_dFdamp(p, a)

  r4scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx))) + r4scan_dF(rscan_fx, scan_p(x), r2scan_alpha(x, t))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r4scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
      f.xt(r0, r1, s0, s1, s2),
      f.xs0(r0, r1, s0, s2),
      f.xs1(r0, r1, s0, s2),
      f.u0(r0, r1, l0, l1),
      f.u1(r0, r1, l0, l1),
      f.tt0(r0, r1, tau0, tau1),
      f.tt1(r0, r1, tau0, tau1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))
  params_da4_raw = params.da4
  if isinstance(params_da4_raw, (str, bytes, dict)):
    params_da4 = params_da4_raw
  else:
    try:
      params_da4_seq = list(params_da4_raw)
    except TypeError:
      params_da4 = params_da4_raw
    else:
      params_da4_seq = np.asarray(params_da4_seq, dtype=np.float64)
      params_da4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_da4_seq))
  params_dp2_raw = params.dp2
  if isinstance(params_dp2_raw, (str, bytes, dict)):
    params_dp2 = params_dp2_raw
  else:
    try:
      params_dp2_seq = list(params_dp2_raw)
    except TypeError:
      params_dp2 = params_dp2_raw
    else:
      params_dp2_seq = np.asarray(params_dp2_seq, dtype=np.float64)
      params_dp2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp2_seq))
  params_dp4_raw = params.dp4
  if isinstance(params_dp4_raw, (str, bytes, dict)):
    params_dp4 = params_dp4_raw
  else:
    try:
      params_dp4_seq = list(params_dp4_raw)
    except TypeError:
      params_dp4 = params_dp4_raw
    else:
      params_dp4_seq = np.asarray(params_dp4_seq, dtype=np.float64)
      params_dp4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp4_seq))
  params_eta_raw = params.eta
  if isinstance(params_eta_raw, (str, bytes, dict)):
    params_eta = params_eta_raw
  else:
    try:
      params_eta_seq = list(params_eta_raw)
    except TypeError:
      params_eta = params_eta_raw
    else:
      params_eta_seq = np.asarray(params_eta_seq, dtype=np.float64)
      params_eta = np.concatenate((np.array([np.nan], dtype=np.float64), params_eta_seq))
  params_k1_raw = params.k1
  if isinstance(params_k1_raw, (str, bytes, dict)):
    params_k1 = params_k1_raw
  else:
    try:
      params_k1_seq = list(params_k1_raw)
    except TypeError:
      params_k1 = params_k1_raw
    else:
      params_k1_seq = np.asarray(params_k1_seq, dtype=np.float64)
      params_k1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k1_seq))

  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  r2scan_alpha = lambda x, t: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  r2scan_f_alpha_neg = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  Cn = 20 / 27 + params_eta * 5 / 3

  df2 = lambda ff: jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0)

  df4 = lambda ff: jnp.sum(jnp.array([(i - 1) * (i - 2) * ff[9 - i] for i in range(2, 8 + 1)]), axis=0)

  r4scan_dFdamp = lambda p, a: 2 * a ** 2 / (1 + a ** 4) * jnp.exp(-(1 - a) ** 2 / params_da4 ** 2 - p ** 2 / params_dp4 ** 4)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  Caa = lambda ff: 73 / 5000 - df4(ff) / 2 * (scan_h0x - 1)

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  Cpa = lambda ff: 511 / 13500 - 73 / 1500 * params_eta - df2(ff) * (Cn * C2(ff) + MU_GE)

  Cpp = lambda ff: 146 / 2025 * (params_eta * 3 / 4 + 2 / 3) ** 2 - 73 / 405 * (params_eta * 3 / 4 + 2 / 3) + (Cn * C2(ff) + MU_GE) ** 2 / params_k1

  r4scan_dF = lambda ff, p, a: (C2(ff) * (1 - a - Cn * p) + Caa(ff) * (1 - a) ** 2 + Cpa(ff) * p * (1 - a) + Cpp(ff) * p ** 2) * r4scan_dFdamp(p, a)

  r4scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx))) + r4scan_dF(rscan_fx, scan_p(x), r2scan_alpha(x, t))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r4scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
      f.xt(r0 / 2, r0 / 2, s0 / 4, s0 / 4, s0 / 4),
      f.xs0(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.xs1(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.u0(r0 / 2, r0 / 2, l0 / 2, l0 / 2),
      f.u1(r0 / 2, r0 / 2, l0 / 2, l0 / 2),
      f.tt0(r0 / 2, r0 / 2, tau0 / 2, tau0 / 2),
      f.tt1(r0 / 2, r0 / 2, tau0 / 2, tau0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))
  params_da4_raw = params.da4
  if isinstance(params_da4_raw, (str, bytes, dict)):
    params_da4 = params_da4_raw
  else:
    try:
      params_da4_seq = list(params_da4_raw)
    except TypeError:
      params_da4 = params_da4_raw
    else:
      params_da4_seq = np.asarray(params_da4_seq, dtype=np.float64)
      params_da4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_da4_seq))
  params_dp2_raw = params.dp2
  if isinstance(params_dp2_raw, (str, bytes, dict)):
    params_dp2 = params_dp2_raw
  else:
    try:
      params_dp2_seq = list(params_dp2_raw)
    except TypeError:
      params_dp2 = params_dp2_raw
    else:
      params_dp2_seq = np.asarray(params_dp2_seq, dtype=np.float64)
      params_dp2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp2_seq))
  params_dp4_raw = params.dp4
  if isinstance(params_dp4_raw, (str, bytes, dict)):
    params_dp4 = params_dp4_raw
  else:
    try:
      params_dp4_seq = list(params_dp4_raw)
    except TypeError:
      params_dp4 = params_dp4_raw
    else:
      params_dp4_seq = np.asarray(params_dp4_seq, dtype=np.float64)
      params_dp4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp4_seq))
  params_eta_raw = params.eta
  if isinstance(params_eta_raw, (str, bytes, dict)):
    params_eta = params_eta_raw
  else:
    try:
      params_eta_seq = list(params_eta_raw)
    except TypeError:
      params_eta = params_eta_raw
    else:
      params_eta_seq = np.asarray(params_eta_seq, dtype=np.float64)
      params_eta = np.concatenate((np.array([np.nan], dtype=np.float64), params_eta_seq))
  params_k1_raw = params.k1
  if isinstance(params_k1_raw, (str, bytes, dict)):
    params_k1 = params_k1_raw
  else:
    try:
      params_k1_seq = list(params_k1_raw)
    except TypeError:
      params_k1 = params_k1_raw
    else:
      params_k1_seq = np.asarray(params_k1_seq, dtype=np.float64)
      params_k1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k1_seq))

  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  r2scan_alpha = lambda x, t: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  r2scan_f_alpha_neg = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  Cn = 20 / 27 + params_eta * 5 / 3

  df2 = lambda ff: jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0)

  df4 = lambda ff: jnp.sum(jnp.array([(i - 1) * (i - 2) * ff[9 - i] for i in range(2, 8 + 1)]), axis=0)

  r4scan_dFdamp = lambda p, a: 2 * a ** 2 / (1 + a ** 4) * jnp.exp(-(1 - a) ** 2 / params_da4 ** 2 - p ** 2 / params_dp4 ** 4)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  Caa = lambda ff: 73 / 5000 - df4(ff) / 2 * (scan_h0x - 1)

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  Cpa = lambda ff: 511 / 13500 - 73 / 1500 * params_eta - df2(ff) * (Cn * C2(ff) + MU_GE)

  Cpp = lambda ff: 146 / 2025 * (params_eta * 3 / 4 + 2 / 3) ** 2 - 73 / 405 * (params_eta * 3 / 4 + 2 / 3) + (Cn * C2(ff) + MU_GE) ** 2 / params_k1

  r4scan_dF = lambda ff, p, a: (C2(ff) * (1 - a - Cn * p) + Caa(ff) * (1 - a) ** 2 + Cpa(ff) * p * (1 - a) + Cpp(ff) * p ** 2) * r4scan_dFdamp(p, a)

  r4scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx))) + r4scan_dF(rscan_fx, scan_p(x), r2scan_alpha(x, t))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r4scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = t21 * f.p.zeta_threshold
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t20, t22, t23 * t19)
  t26 = t5 * t25
  t27 = t6 ** (0.1e1 / 0.3e1)
  t28 = 0.27123702538979000000000000000000000000000000000000e0 * params.eta
  t29 = -0.12054978906212888888888888888888888888888888888889e0 - t28
  t30 = 6 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t35 = 0.1e1 / t33 / t32
  t36 = t31 * t35
  t37 = s0 ** 2
  t38 = r0 ** 2
  t39 = t38 ** 2
  t41 = r0 ** (0.1e1 / 0.3e1)
  t43 = 0.1e1 / t41 / t39 / r0
  t44 = t37 * t43
  t45 = params.dp2 ** 2
  t46 = t45 ** 2
  t47 = 0.1e1 / t46
  t51 = jnp.exp(-t36 * t44 * t47 / 0.576e3)
  t54 = (t29 * t51 + 0.10e2 / 0.81e2) * t30
  t55 = t33 ** 2
  t56 = 0.1e1 / t55
  t57 = t56 * s0
  t58 = t41 ** 2
  t60 = 0.1e1 / t58 / t38
  t61 = t57 * t60
  t64 = params.k1 + t54 * t61 / 0.24e2
  t68 = params.k1 * (0.1e1 - params.k1 / t64)
  t70 = 0.1e1 / t58 / r0
  t72 = s0 * t60
  t74 = tau0 * t70 - t72 / 0.8e1
  t76 = 0.3e1 / 0.10e2 * t31 * t55
  t77 = params.eta * s0
  t80 = t76 + t77 * t60 / 0.8e1
  t81 = 0.1e1 / t80
  t82 = t74 * t81
  t83 = t82 <= 0.0e0
  t84 = 0.0e0 < t82
  t85 = f.my_piecewise3(t84, 0, t82)
  t86 = params.c1 * t85
  t87 = 0.1e1 - t85
  t88 = 0.1e1 / t87
  t90 = jnp.exp(-t86 * t88)
  t91 = t82 <= 0.25e1
  t92 = 0.25e1 < t82
  t93 = f.my_piecewise3(t92, 0.25e1, t82)
  t95 = t93 ** 2
  t97 = t95 * t93
  t99 = t95 ** 2
  t101 = t99 * t93
  t103 = t99 * t95
  t108 = f.my_piecewise3(t92, t82, 0.25e1)
  t109 = 0.1e1 - t108
  t112 = jnp.exp(params.c2 / t109)
  t114 = f.my_piecewise5(t83, t90, t91, 0.1e1 - 0.667e0 * t93 - 0.4445555e0 * t95 - 0.663086601049e0 * t97 + 0.1451297044490e1 * t99 - 0.887998041597e0 * t101 + 0.234528941479e0 * t103 - 0.23185843322e-1 * t99 * t97, -params.d * t112)
  t115 = 0.174e0 - t68
  t120 = (0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta) * t30
  t123 = 0.1e1 - t82
  t124 = t123 ** 2
  t128 = (0.40570770199022687796862290864197530864197530864200e-1 - 0.30235468026081006356817095666666666666666666666667e0 * params.eta) * t30
  t129 = t128 * t56
  t135 = (0.3e1 / 0.4e1 * params.eta + 0.2e1 / 0.3e1) ** 2
  t139 = (0.290700106132790123456790123456790123456790123457e-2 - t28) ** 2
  t143 = (0.146e3 / 0.2025e4 * t135 - 0.73e2 / 0.540e3 * params.eta - 0.146e3 / 0.1215e4 + t139 / params.k1) * t31
  t144 = t35 * t37
  t148 = -0.162742215233874e0 + 0.162742215233874e0 * t82 + 0.67809256347447500000000000000000000000000000000000e-2 * t120 * t61 - 0.59353125082804000000000000000000000000000000000000e-1 * t124 + t129 * t72 * t123 / 0.24e2 + t143 * t144 * t43 / 0.576e3
  t149 = t74 ** 2
  t150 = t148 * t149
  t151 = t80 ** 2
  t152 = 0.1e1 / t151
  t153 = t149 ** 2
  t154 = t151 ** 2
  t155 = 0.1e1 / t154
  t157 = t153 * t155 + 0.1e1
  t158 = 0.1e1 / t157
  t160 = params.da4 ** 2
  t161 = 0.1e1 / t160
  t163 = params.dp4 ** 2
  t164 = t163 ** 2
  t165 = 0.1e1 / t164
  t170 = jnp.exp(-t124 * t161 - t36 * t44 * t165 / 0.576e3)
  t171 = t152 * t158 * t170
  t174 = t114 * t115 + 0.2e1 * t150 * t171 + t68 + 0.1e1
  t176 = jnp.sqrt(0.3e1)
  t177 = 0.1e1 / t33
  t178 = t31 * t177
  t179 = jnp.sqrt(s0)
  t181 = 0.1e1 / t41 / r0
  t183 = t178 * t179 * t181
  t184 = jnp.sqrt(t183)
  t188 = jnp.exp(-0.98958e1 * t176 / t184)
  t189 = 0.1e1 - t188
  t190 = t27 * t174 * t189
  t193 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t190)
  t194 = r1 <= f.p.dens_threshold
  t195 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t196 = 0.1e1 + t195
  t197 = t196 <= f.p.zeta_threshold
  t198 = t196 ** (0.1e1 / 0.3e1)
  t200 = f.my_piecewise3(t197, t22, t198 * t196)
  t201 = t5 * t200
  t202 = s2 ** 2
  t203 = r1 ** 2
  t204 = t203 ** 2
  t206 = r1 ** (0.1e1 / 0.3e1)
  t208 = 0.1e1 / t206 / t204 / r1
  t209 = t202 * t208
  t213 = jnp.exp(-t36 * t209 * t47 / 0.576e3)
  t216 = (t29 * t213 + 0.10e2 / 0.81e2) * t30
  t217 = t56 * s2
  t218 = t206 ** 2
  t220 = 0.1e1 / t218 / t203
  t221 = t217 * t220
  t224 = params.k1 + t216 * t221 / 0.24e2
  t228 = params.k1 * (0.1e1 - params.k1 / t224)
  t230 = 0.1e1 / t218 / r1
  t232 = s2 * t220
  t234 = tau1 * t230 - t232 / 0.8e1
  t235 = params.eta * s2
  t238 = t76 + t235 * t220 / 0.8e1
  t239 = 0.1e1 / t238
  t240 = t234 * t239
  t241 = t240 <= 0.0e0
  t242 = 0.0e0 < t240
  t243 = f.my_piecewise3(t242, 0, t240)
  t244 = params.c1 * t243
  t245 = 0.1e1 - t243
  t246 = 0.1e1 / t245
  t248 = jnp.exp(-t244 * t246)
  t249 = t240 <= 0.25e1
  t250 = 0.25e1 < t240
  t251 = f.my_piecewise3(t250, 0.25e1, t240)
  t253 = t251 ** 2
  t255 = t253 * t251
  t257 = t253 ** 2
  t259 = t257 * t251
  t261 = t257 * t253
  t266 = f.my_piecewise3(t250, t240, 0.25e1)
  t267 = 0.1e1 - t266
  t270 = jnp.exp(params.c2 / t267)
  t272 = f.my_piecewise5(t241, t248, t249, 0.1e1 - 0.667e0 * t251 - 0.4445555e0 * t253 - 0.663086601049e0 * t255 + 0.1451297044490e1 * t257 - 0.887998041597e0 * t259 + 0.234528941479e0 * t261 - 0.23185843322e-1 * t257 * t255, -params.d * t270)
  t273 = 0.174e0 - t228
  t278 = 0.1e1 - t240
  t279 = t278 ** 2
  t284 = t35 * t202
  t288 = -0.162742215233874e0 + 0.162742215233874e0 * t240 + 0.67809256347447500000000000000000000000000000000000e-2 * t120 * t221 - 0.59353125082804000000000000000000000000000000000000e-1 * t279 + t129 * t232 * t278 / 0.24e2 + t143 * t284 * t208 / 0.576e3
  t289 = t234 ** 2
  t290 = t288 * t289
  t291 = t238 ** 2
  t292 = 0.1e1 / t291
  t293 = t289 ** 2
  t294 = t291 ** 2
  t295 = 0.1e1 / t294
  t297 = t293 * t295 + 0.1e1
  t298 = 0.1e1 / t297
  t305 = jnp.exp(-t279 * t161 - t36 * t209 * t165 / 0.576e3)
  t306 = t292 * t298 * t305
  t309 = t272 * t273 + 0.2e1 * t290 * t306 + t228 + 0.1e1
  t311 = jnp.sqrt(s2)
  t313 = 0.1e1 / t206 / r1
  t315 = t178 * t311 * t313
  t316 = jnp.sqrt(t315)
  t320 = jnp.exp(-0.98958e1 * t176 / t316)
  t321 = 0.1e1 - t320
  t322 = t27 * t309 * t321
  t325 = f.my_piecewise3(t194, 0, -0.3e1 / 0.8e1 * t201 * t322)
  t326 = t6 ** 2
  t328 = t16 / t326
  t329 = t7 - t328
  t330 = f.my_piecewise5(t10, 0, t14, 0, t329)
  t333 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t330)
  t337 = t27 ** 2
  t338 = 0.1e1 / t337
  t342 = t26 * t338 * t174 * t189 / 0.8e1
  t343 = params.k1 ** 2
  t344 = t64 ** 2
  t345 = 0.1e1 / t344
  t346 = t343 * t345
  t347 = t32 ** 2
  t349 = t29 / t347
  t352 = t39 ** 2
  t361 = 0.1e1 / t58 / t38 / r0
  t362 = t57 * t361
  t365 = t349 * t37 * s0 / t352 / r0 * t47 * t51 / 0.432e3 - t54 * t362 / 0.9e1
  t369 = s0 * t361
  t371 = -0.5e1 / 0.3e1 * tau0 * t60 + t369 / 0.3e1
  t372 = t371 * t81
  t373 = t74 * t152
  t374 = t77 * t361
  t375 = t373 * t374
  t377 = t372 + t375 / 0.3e1
  t378 = f.my_piecewise3(t84, 0, t377)
  t381 = t87 ** 2
  t382 = 0.1e1 / t381
  t387 = f.my_piecewise3(t92, 0, t377)
  t402 = params.d * params.c2
  t403 = t109 ** 2
  t404 = 0.1e1 / t403
  t405 = f.my_piecewise3(t92, t377, 0)
  t409 = f.my_piecewise5(t83, (-t86 * t382 * t378 - params.c1 * t378 * t88) * t90, t91, -0.667e0 * t387 - 0.8891110e0 * t93 * t387 - 0.1989259803147e1 * t95 * t387 + 0.5805188177960e1 * t97 * t387 - 0.4439990207985e1 * t99 * t387 + 0.1407173648874e1 * t101 * t387 - 0.162300903254e0 * t103 * t387, -t402 * t404 * t405 * t112)
  t411 = t114 * t343
  t418 = -t377
  t429 = 0.1e1 / t41 / t39 / t38
  t438 = t148 * t74 * t152
  t439 = t158 * t170
  t444 = 0.1e1 / t151 / t80
  t446 = t150 * t444 * t158
  t451 = t150 * t152
  t452 = t157 ** 2
  t454 = 0.1e1 / t452 * t170
  t456 = t149 * t74 * t155
  t461 = t153 / t154 / t80
  t468 = t123 * t161
  t485 = 3 ** (0.1e1 / 0.6e1)
  t486 = t485 ** 2
  t487 = t486 ** 2
  t489 = t487 * t485 * t4
  t492 = t489 * t25 * t27 * t174
  t496 = 0.1e1 / t184 / t183 * t31 * t177
  t505 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t333 * t190 - t342 - 0.3e1 / 0.8e1 * t26 * t27 * (t346 * t365 + t409 * t115 - t411 * t345 * t365 + 0.2e1 * (0.162742215233874e0 * t372 + 0.54247405077958000000000000000000000000000000000000e-1 * t375 - 0.18082468359319333333333333333333333333333333333333e-1 * t120 * t362 - 0.11870625016560800000000000000000000000000000000000e0 * t123 * t418 - t129 * t369 * t123 / 0.9e1 + t129 * t72 * t418 / 0.24e2 - t143 * t144 * t429 / 0.108e3) * t149 * t171 + 0.4e1 * t438 * t439 * t371 + 0.4e1 / 0.3e1 * t446 * t170 * params.eta * t369 - 0.2e1 * t451 * t454 * (0.4e1 * t456 * t371 + 0.4e1 / 0.3e1 * t461 * t374) + 0.2e1 * t451 * t158 * (-0.2e1 * t468 * t418 + t36 * t37 * t429 * t165 / 0.108e3) * t170) * t189 - 0.24739500000000000000000000000000000000000000000000e1 * t492 * t496 * t179 / t41 / t38 * t188)
  t507 = f.my_piecewise5(t14, 0, t10, 0, -t329)
  t510 = f.my_piecewise3(t197, 0, 0.4e1 / 0.3e1 * t198 * t507)
  t517 = t201 * t338 * t309 * t321 / 0.8e1
  t519 = f.my_piecewise3(t194, 0, -0.3e1 / 0.8e1 * t5 * t510 * t322 - t517)
  vrho_0_ = t193 + t325 + t6 * (t505 + t519)
  t522 = -t7 - t328
  t523 = f.my_piecewise5(t10, 0, t14, 0, t522)
  t526 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t523)
  t531 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t526 * t190 - t342)
  t533 = f.my_piecewise5(t14, 0, t10, 0, -t522)
  t536 = f.my_piecewise3(t197, 0, 0.4e1 / 0.3e1 * t198 * t533)
  t540 = t224 ** 2
  t541 = 0.1e1 / t540
  t542 = t343 * t541
  t545 = t204 ** 2
  t554 = 0.1e1 / t218 / t203 / r1
  t555 = t217 * t554
  t558 = t349 * t202 * s2 / t545 / r1 * t47 * t213 / 0.432e3 - t216 * t555 / 0.9e1
  t562 = s2 * t554
  t564 = -0.5e1 / 0.3e1 * tau1 * t220 + t562 / 0.3e1
  t565 = t564 * t239
  t566 = t234 * t292
  t567 = t235 * t554
  t568 = t566 * t567
  t570 = t565 + t568 / 0.3e1
  t571 = f.my_piecewise3(t242, 0, t570)
  t574 = t245 ** 2
  t575 = 0.1e1 / t574
  t580 = f.my_piecewise3(t250, 0, t570)
  t595 = t267 ** 2
  t596 = 0.1e1 / t595
  t597 = f.my_piecewise3(t250, t570, 0)
  t601 = f.my_piecewise5(t241, (-t244 * t575 * t571 - params.c1 * t571 * t246) * t248, t249, -0.667e0 * t580 - 0.8891110e0 * t251 * t580 - 0.1989259803147e1 * t253 * t580 + 0.5805188177960e1 * t255 * t580 - 0.4439990207985e1 * t257 * t580 + 0.1407173648874e1 * t259 * t580 - 0.162300903254e0 * t261 * t580, -t402 * t596 * t597 * t270)
  t603 = t272 * t343
  t610 = -t570
  t621 = 0.1e1 / t206 / t204 / t203
  t630 = t288 * t234 * t292
  t631 = t298 * t305
  t636 = 0.1e1 / t291 / t238
  t638 = t290 * t636 * t298
  t643 = t290 * t292
  t644 = t297 ** 2
  t646 = 0.1e1 / t644 * t305
  t648 = t289 * t234 * t295
  t653 = t293 / t294 / t238
  t660 = t278 * t161
  t679 = t489 * t200 * t27 * t309
  t683 = 0.1e1 / t316 / t315 * t31 * t177
  t692 = f.my_piecewise3(t194, 0, -0.3e1 / 0.8e1 * t5 * t536 * t322 - t517 - 0.3e1 / 0.8e1 * t201 * t27 * (t542 * t558 + t601 * t273 - t603 * t541 * t558 + 0.2e1 * (0.162742215233874e0 * t565 + 0.54247405077958000000000000000000000000000000000000e-1 * t568 - 0.18082468359319333333333333333333333333333333333333e-1 * t120 * t555 - 0.11870625016560800000000000000000000000000000000000e0 * t278 * t610 - t129 * t562 * t278 / 0.9e1 + t129 * t232 * t610 / 0.24e2 - t143 * t284 * t621 / 0.108e3) * t289 * t306 + 0.4e1 * t630 * t631 * t564 + 0.4e1 / 0.3e1 * t638 * t305 * params.eta * t562 - 0.2e1 * t643 * t646 * (0.4e1 * t648 * t564 + 0.4e1 / 0.3e1 * t653 * t567) + 0.2e1 * t643 * t298 * (-0.2e1 * t660 * t610 + t36 * t202 * t621 * t165 / 0.108e3) * t305) * t321 - 0.24739500000000000000000000000000000000000000000000e1 * t679 * t683 * t311 / t206 / t203 * t320)
  vrho_1_ = t193 + t325 + t6 * (t531 + t692)
  t701 = t56 * t60
  t704 = -t349 * t37 / t352 * t47 * t51 / 0.1152e4 + t54 * t701 / 0.24e2
  t706 = t60 * t81
  t707 = params.eta * t60
  t708 = t373 * t707
  t710 = -t706 / 0.8e1 - t708 / 0.8e1
  t711 = f.my_piecewise3(t84, 0, t710)
  t718 = f.my_piecewise3(t92, 0, t710)
  t733 = f.my_piecewise3(t92, t710, 0)
  t737 = f.my_piecewise5(t83, (-t86 * t382 * t711 - params.c1 * t711 * t88) * t90, t91, -0.667e0 * t718 - 0.8891110e0 * t93 * t718 - 0.1989259803147e1 * t95 * t718 + 0.5805188177960e1 * t97 * t718 - 0.4439990207985e1 * t99 * t718 + 0.1407173648874e1 * t101 * t718 - 0.162300903254e0 * t103 * t718, -t402 * t404 * t733 * t112)
  t745 = -t710
  t799 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (t346 * t704 + t737 * t115 - t411 * t345 * t704 + 0.2e1 * (-0.20342776904234250000000000000000000000000000000000e-1 * t706 - 0.20342776904234250000000000000000000000000000000000e-1 * t708 + 0.67809256347447500000000000000000000000000000000000e-2 * t120 * t701 - 0.11870625016560800000000000000000000000000000000000e0 * t123 * t745 + t128 * t701 * t123 / 0.24e2 + t129 * t72 * t745 / 0.24e2 + t143 * t35 * s0 * t43 / 0.288e3) * t149 * t171 - t438 * t439 * t60 / 0.2e1 - t150 * t444 * t439 * t707 / 0.2e1 - 0.2e1 * t451 * t454 * (-t456 * t60 / 0.2e1 - t461 * t707 / 0.2e1) + 0.2e1 * t451 * t158 * (-0.2e1 * t468 * t745 - t36 * s0 * t43 * t165 / 0.288e3) * t170) * t189 + 0.92773125000000000000000000000000000000000000000000e0 * t492 * t496 / t179 * t181 * t188)
  vsigma_0_ = t6 * t799
  vsigma_1_ = 0.0e0
  t806 = t56 * t220
  t809 = -t349 * t202 / t545 * t47 * t213 / 0.1152e4 + t216 * t806 / 0.24e2
  t811 = t220 * t239
  t812 = params.eta * t220
  t813 = t566 * t812
  t815 = -t811 / 0.8e1 - t813 / 0.8e1
  t816 = f.my_piecewise3(t242, 0, t815)
  t823 = f.my_piecewise3(t250, 0, t815)
  t838 = f.my_piecewise3(t250, t815, 0)
  t842 = f.my_piecewise5(t241, (-t244 * t575 * t816 - params.c1 * t816 * t246) * t248, t249, -0.667e0 * t823 - 0.8891110e0 * t251 * t823 - 0.1989259803147e1 * t253 * t823 + 0.5805188177960e1 * t255 * t823 - 0.4439990207985e1 * t257 * t823 + 0.1407173648874e1 * t259 * t823 - 0.162300903254e0 * t261 * t823, -t402 * t596 * t838 * t270)
  t850 = -t815
  t904 = f.my_piecewise3(t194, 0, -0.3e1 / 0.8e1 * t201 * t27 * (t542 * t809 + t842 * t273 - t603 * t541 * t809 + 0.2e1 * (-0.20342776904234250000000000000000000000000000000000e-1 * t811 - 0.20342776904234250000000000000000000000000000000000e-1 * t813 + 0.67809256347447500000000000000000000000000000000000e-2 * t120 * t806 - 0.11870625016560800000000000000000000000000000000000e0 * t278 * t850 + t128 * t806 * t278 / 0.24e2 + t129 * t232 * t850 / 0.24e2 + t143 * t35 * s2 * t208 / 0.288e3) * t289 * t306 - t630 * t631 * t220 / 0.2e1 - t290 * t636 * t631 * t812 / 0.2e1 - 0.2e1 * t643 * t646 * (-t648 * t220 / 0.2e1 - t653 * t812 / 0.2e1) + 0.2e1 * t643 * t298 * (-0.2e1 * t660 * t850 - t36 * s2 * t208 * t165 / 0.288e3) * t305) * t321 + 0.92773125000000000000000000000000000000000000000000e0 * t679 * t683 / t311 * t313 * t320)
  vsigma_2_ = t6 * t904
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t905 = t70 * t81
  t906 = f.my_piecewise3(t84, 0, t905)
  t913 = f.my_piecewise3(t92, 0, t905)
  t928 = f.my_piecewise3(t92, t905, 0)
  t932 = f.my_piecewise5(t83, (-t86 * t382 * t906 - params.c1 * t906 * t88) * t90, t91, -0.667e0 * t913 - 0.8891110e0 * t93 * t913 - 0.1989259803147e1 * t95 * t913 + 0.5805188177960e1 * t97 * t913 - 0.4439990207985e1 * t99 * t913 + 0.1407173648874e1 * t101 * t913 - 0.162300903254e0 * t103 * t913, -t402 * t404 * t928 * t112)
  t968 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (t932 * t115 + 0.2e1 * (0.162742215233874e0 * t905 + 0.11870625016560800000000000000000000000000000000000e0 * t123 * t70 * t81 - t129 * s0 / t41 / t39 * t81 / 0.24e2) * t149 * t171 + 0.4e1 * t438 * t439 * t70 - 0.8e1 * t148 * t153 * t74 / t154 / t151 * t454 * t70 + 0.4e1 * t446 * t468 * t70 * t170) * t189)
  vtau_0_ = t6 * t968
  t969 = t230 * t239
  t970 = f.my_piecewise3(t242, 0, t969)
  t977 = f.my_piecewise3(t250, 0, t969)
  t992 = f.my_piecewise3(t250, t969, 0)
  t996 = f.my_piecewise5(t241, (-t244 * t575 * t970 - params.c1 * t970 * t246) * t248, t249, -0.667e0 * t977 - 0.8891110e0 * t251 * t977 - 0.1989259803147e1 * t253 * t977 + 0.5805188177960e1 * t255 * t977 - 0.4439990207985e1 * t257 * t977 + 0.1407173648874e1 * t259 * t977 - 0.162300903254e0 * t261 * t977, -t402 * t596 * t992 * t270)
  t1032 = f.my_piecewise3(t194, 0, -0.3e1 / 0.8e1 * t201 * t27 * (t996 * t273 + 0.2e1 * (0.162742215233874e0 * t969 + 0.11870625016560800000000000000000000000000000000000e0 * t278 * t230 * t239 - t129 * s2 / t206 / t204 * t239 / 0.24e2) * t289 * t306 + 0.4e1 * t630 * t631 * t230 - 0.8e1 * t288 * t293 * t234 / t294 / t291 * t646 * t230 + 0.4e1 * t638 * t660 * t230 * t305) * t321)
  vtau_1_ = t6 * t1032
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  vsigma_0_ = _b(vsigma_0_)
  vsigma_1_ = _b(vsigma_1_)
  vsigma_2_ = _b(vsigma_2_)
  vlapl_0_ = _b(vlapl_0_)
  vlapl_1_ = _b(vlapl_1_)
  vtau_0_ = _b(vtau_0_)
  vtau_1_ = _b(vtau_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1), 'vsigma': jnp.stack([vsigma_0_, vsigma_1_, vsigma_2_], axis=-1), 'vlapl': jnp.stack([vlapl_0_, vlapl_1_], axis=-1), 'vtau':  jnp.stack([vtau_0_, vtau_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))
  params_da4_raw = params.da4
  if isinstance(params_da4_raw, (str, bytes, dict)):
    params_da4 = params_da4_raw
  else:
    try:
      params_da4_seq = list(params_da4_raw)
    except TypeError:
      params_da4 = params_da4_raw
    else:
      params_da4_seq = np.asarray(params_da4_seq, dtype=np.float64)
      params_da4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_da4_seq))
  params_dp2_raw = params.dp2
  if isinstance(params_dp2_raw, (str, bytes, dict)):
    params_dp2 = params_dp2_raw
  else:
    try:
      params_dp2_seq = list(params_dp2_raw)
    except TypeError:
      params_dp2 = params_dp2_raw
    else:
      params_dp2_seq = np.asarray(params_dp2_seq, dtype=np.float64)
      params_dp2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp2_seq))
  params_dp4_raw = params.dp4
  if isinstance(params_dp4_raw, (str, bytes, dict)):
    params_dp4 = params_dp4_raw
  else:
    try:
      params_dp4_seq = list(params_dp4_raw)
    except TypeError:
      params_dp4 = params_dp4_raw
    else:
      params_dp4_seq = np.asarray(params_dp4_seq, dtype=np.float64)
      params_dp4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp4_seq))
  params_eta_raw = params.eta
  if isinstance(params_eta_raw, (str, bytes, dict)):
    params_eta = params_eta_raw
  else:
    try:
      params_eta_seq = list(params_eta_raw)
    except TypeError:
      params_eta = params_eta_raw
    else:
      params_eta_seq = np.asarray(params_eta_seq, dtype=np.float64)
      params_eta = np.concatenate((np.array([np.nan], dtype=np.float64), params_eta_seq))
  params_k1_raw = params.k1
  if isinstance(params_k1_raw, (str, bytes, dict)):
    params_k1 = params_k1_raw
  else:
    try:
      params_k1_seq = list(params_k1_raw)
    except TypeError:
      params_k1 = params_k1_raw
    else:
      params_k1_seq = np.asarray(params_k1_seq, dtype=np.float64)
      params_k1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k1_seq))

  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  r2scan_alpha = lambda x, t: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  r2scan_f_alpha_neg = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  Cn = 20 / 27 + params_eta * 5 / 3

  df2 = lambda ff: jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0)

  df4 = lambda ff: jnp.sum(jnp.array([(i - 1) * (i - 2) * ff[9 - i] for i in range(2, 8 + 1)]), axis=0)

  r4scan_dFdamp = lambda p, a: 2 * a ** 2 / (1 + a ** 4) * jnp.exp(-(1 - a) ** 2 / params_da4 ** 2 - p ** 2 / params_dp4 ** 4)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  Caa = lambda ff: 73 / 5000 - df4(ff) / 2 * (scan_h0x - 1)

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  Cpa = lambda ff: 511 / 13500 - 73 / 1500 * params_eta - df2(ff) * (Cn * C2(ff) + MU_GE)

  Cpp = lambda ff: 146 / 2025 * (params_eta * 3 / 4 + 2 / 3) ** 2 - 73 / 405 * (params_eta * 3 / 4 + 2 / 3) + (Cn * C2(ff) + MU_GE) ** 2 / params_k1

  r4scan_dF = lambda ff, p, a: (C2(ff) * (1 - a - Cn * p) + Caa(ff) * (1 - a) ** 2 + Cpa(ff) * p * (1 - a) + Cpp(ff) * p ** 2) * r4scan_dFdamp(p, a)

  r4scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx))) + r4scan_dF(rscan_fx, scan_p(x), r2scan_alpha(x, t))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r4scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 * t5 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = 0.27123702538979000000000000000000000000000000000000e0 * params.eta
  t21 = -0.12054978906212888888888888888888888888888888888889e0 - t20
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t25 / t24
  t28 = t23 * t27
  t29 = s0 ** 2
  t30 = t28 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = r0 ** 2
  t33 = t32 ** 2
  t36 = 0.1e1 / t19 / t33 / r0
  t37 = t31 * t36
  t38 = params.dp2 ** 2
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t44 = jnp.exp(-t30 * t37 * t40 / 0.288e3)
  t47 = (t21 * t44 + 0.10e2 / 0.81e2) * t22
  t48 = t25 ** 2
  t49 = 0.1e1 / t48
  t50 = t47 * t49
  t51 = t31 ** 2
  t52 = s0 * t51
  t53 = t19 ** 2
  t55 = 0.1e1 / t53 / t32
  t56 = t52 * t55
  t59 = params.k1 + t50 * t56 / 0.24e2
  t63 = params.k1 * (0.1e1 - params.k1 / t59)
  t64 = tau0 * t51
  t66 = 0.1e1 / t53 / r0
  t69 = t64 * t66 - t56 / 0.8e1
  t73 = t51 * t55
  t76 = 0.3e1 / 0.10e2 * t23 * t48 + params.eta * s0 * t73 / 0.8e1
  t77 = 0.1e1 / t76
  t78 = t69 * t77
  t79 = t78 <= 0.0e0
  t80 = 0.0e0 < t78
  t81 = f.my_piecewise3(t80, 0, t78)
  t82 = params.c1 * t81
  t83 = 0.1e1 - t81
  t84 = 0.1e1 / t83
  t86 = jnp.exp(-t82 * t84)
  t87 = t78 <= 0.25e1
  t88 = 0.25e1 < t78
  t89 = f.my_piecewise3(t88, 0.25e1, t78)
  t91 = t89 ** 2
  t93 = t91 * t89
  t95 = t91 ** 2
  t97 = t95 * t89
  t99 = t95 * t91
  t104 = f.my_piecewise3(t88, t78, 0.25e1)
  t105 = 0.1e1 - t104
  t108 = jnp.exp(params.c2 / t105)
  t110 = f.my_piecewise5(t79, t86, t87, 0.1e1 - 0.667e0 * t89 - 0.4445555e0 * t91 - 0.663086601049e0 * t93 + 0.1451297044490e1 * t95 - 0.887998041597e0 * t97 + 0.234528941479e0 * t99 - 0.23185843322e-1 * t95 * t93, -params.d * t108)
  t111 = 0.174e0 - t63
  t116 = (0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta) * t22
  t117 = t116 * t49
  t120 = 0.1e1 - t78
  t121 = t120 ** 2
  t126 = (0.40570770199022687796862290864197530864197530864200e-1 - 0.30235468026081006356817095666666666666666666666667e0 * params.eta) * t22 * t49
  t133 = (0.3e1 / 0.4e1 * params.eta + 0.2e1 / 0.3e1) ** 2
  t137 = (0.290700106132790123456790123456790123456790123457e-2 - t20) ** 2
  t142 = (0.146e3 / 0.2025e4 * t133 - 0.73e2 / 0.540e3 * params.eta - 0.146e3 / 0.1215e4 + t137 / params.k1) * t23 * t27
  t143 = t29 * t31
  t147 = -0.162742215233874e0 + 0.162742215233874e0 * t78 + 0.67809256347447500000000000000000000000000000000000e-2 * t117 * t56 - 0.59353125082804000000000000000000000000000000000000e-1 * t121 + t126 * t52 * t55 * t120 / 0.24e2 + t142 * t143 * t36 / 0.288e3
  t148 = t69 ** 2
  t149 = t147 * t148
  t150 = t76 ** 2
  t151 = 0.1e1 / t150
  t152 = t148 ** 2
  t153 = t150 ** 2
  t154 = 0.1e1 / t153
  t156 = t152 * t154 + 0.1e1
  t157 = 0.1e1 / t156
  t159 = params.da4 ** 2
  t160 = 0.1e1 / t159
  t162 = params.dp4 ** 2
  t163 = t162 ** 2
  t164 = 0.1e1 / t163
  t165 = t37 * t164
  t169 = jnp.exp(-t121 * t160 - t30 * t165 / 0.288e3)
  t170 = t151 * t157 * t169
  t173 = t110 * t111 + 0.2e1 * t149 * t170 + t63 + 0.1e1
  t175 = jnp.sqrt(0.3e1)
  t176 = 0.1e1 / t25
  t178 = jnp.sqrt(s0)
  t179 = t178 * t31
  t183 = t23 * t176 * t179 / t19 / r0
  t184 = jnp.sqrt(t183)
  t188 = jnp.exp(-0.98958e1 * t175 / t184)
  t189 = 0.1e1 - t188
  t193 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t173 * t189)
  t199 = params.k1 ** 2
  t200 = t59 ** 2
  t201 = 0.1e1 / t200
  t202 = t199 * t201
  t203 = t24 ** 2
  t205 = t21 / t203
  t208 = t33 ** 2
  t217 = 0.1e1 / t53 / t32 / r0
  t218 = t52 * t217
  t221 = t205 * t29 * s0 / t208 / r0 * t40 * t44 / 0.108e3 - t50 * t218 / 0.9e1
  t226 = -0.5e1 / 0.3e1 * t64 * t55 + t218 / 0.3e1
  t227 = t226 * t77
  t228 = t69 * t151
  t230 = t228 * params.eta * t218
  t232 = t227 + t230 / 0.3e1
  t233 = f.my_piecewise3(t80, 0, t232)
  t236 = t83 ** 2
  t237 = 0.1e1 / t236
  t242 = f.my_piecewise3(t88, 0, t232)
  t257 = params.d * params.c2
  t258 = t105 ** 2
  t259 = 0.1e1 / t258
  t260 = f.my_piecewise3(t88, t232, 0)
  t264 = f.my_piecewise5(t79, (-t82 * t237 * t233 - params.c1 * t233 * t84) * t86, t87, -0.667e0 * t242 - 0.8891110e0 * t89 * t242 - 0.1989259803147e1 * t91 * t242 + 0.5805188177960e1 * t93 * t242 - 0.4439990207985e1 * t95 * t242 + 0.1407173648874e1 * t97 * t242 - 0.162300903254e0 * t99 * t242, -t257 * t259 * t260 * t108)
  t266 = t110 * t199
  t273 = -t232
  t286 = 0.1e1 / t19 / t33 / t32
  t295 = t147 * t69 * t151
  t296 = t157 * t169
  t303 = t149 / t150 / t76 * t157
  t304 = t169 * params.eta
  t308 = t149 * t151
  t309 = t156 ** 2
  t311 = 0.1e1 / t309 * t169
  t313 = t148 * t69 * t154
  t318 = t152 / t153 / t76
  t326 = t120 * t160
  t343 = 3 ** (0.1e1 / 0.6e1)
  t344 = t343 ** 2
  t345 = t344 ** 2
  t347 = t345 * t343 * t5
  t355 = 0.1e1 / t184 / t183 * t23 * t176
  t361 = f.my_piecewise3(t2, 0, -t18 / t53 * t173 * t189 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (t202 * t221 + t264 * t111 - t266 * t201 * t221 + 0.2e1 * (0.162742215233874e0 * t227 + 0.54247405077958000000000000000000000000000000000000e-1 * t230 - 0.18082468359319333333333333333333333333333333333333e-1 * t117 * t218 - 0.11870625016560800000000000000000000000000000000000e0 * t120 * t273 - t126 * t52 * t217 * t120 / 0.9e1 + t126 * t52 * t55 * t273 / 0.24e2 - t142 * t143 * t286 / 0.54e2) * t148 * t170 + 0.4e1 * t295 * t296 * t226 + 0.4e1 / 0.3e1 * t303 * t304 * t218 - 0.2e1 * t308 * t311 * (0.4e1 * t313 * t226 + 0.4e1 / 0.3e1 * t318 * params.eta * t218) + 0.2e1 * t308 * t157 * (-0.2e1 * t326 * t273 + t30 * t31 * t286 * t164 / 0.54e2) * t169) * t189 - 0.24739500000000000000000000000000000000000000000000e1 * t347 * t17 / t32 * t173 * t355 * t179 * t188)
  vrho_0_ = 0.2e1 * r0 * t361 + 0.2e1 * t193
  t371 = t49 * t51 * t55
  t374 = -t205 * t29 / t208 * t40 * t44 / 0.288e3 + t47 * t371 / 0.24e2
  t376 = t73 * t77
  t378 = params.eta * t51 * t55
  t379 = t228 * t378
  t381 = -t376 / 0.8e1 - t379 / 0.8e1
  t382 = f.my_piecewise3(t80, 0, t381)
  t389 = f.my_piecewise3(t88, 0, t381)
  t404 = f.my_piecewise3(t88, t381, 0)
  t408 = f.my_piecewise5(t79, (-t82 * t237 * t382 - params.c1 * t382 * t84) * t86, t87, -0.667e0 * t389 - 0.8891110e0 * t89 * t389 - 0.1989259803147e1 * t91 * t389 + 0.5805188177960e1 * t93 * t389 - 0.4439990207985e1 * t95 * t389 + 0.1407173648874e1 * t97 * t389 - 0.162300903254e0 * t99 * t389, -t257 * t259 * t404 * t108)
  t416 = -t381
  t426 = s0 * t31
  t473 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (t202 * t374 + t408 * t111 - t266 * t201 * t374 + 0.2e1 * (-0.20342776904234250000000000000000000000000000000000e-1 * t376 - 0.20342776904234250000000000000000000000000000000000e-1 * t379 + 0.67809256347447500000000000000000000000000000000000e-2 * t116 * t371 - 0.11870625016560800000000000000000000000000000000000e0 * t120 * t416 + t126 * t73 * t120 / 0.24e2 + t126 * t52 * t55 * t416 / 0.24e2 + t142 * t426 * t36 / 0.144e3) * t148 * t170 - t295 * t296 * t73 / 0.2e1 - t303 * t304 * t73 / 0.2e1 - 0.2e1 * t308 * t311 * (-t313 * t73 / 0.2e1 - t318 * t378 / 0.2e1) + 0.2e1 * t308 * t157 * (-0.2e1 * t326 * t416 - t28 * s0 * t165 / 0.144e3) * t169) * t189 + 0.92773125000000000000000000000000000000000000000000e0 * t347 * t17 / r0 * t173 * t355 / t178 * t31 * t188)
  vsigma_0_ = 0.2e1 * r0 * t473
  vlapl_0_ = 0.0e0
  t475 = t51 * t66
  t476 = t475 * t77
  t477 = f.my_piecewise3(t80, 0, t476)
  t484 = f.my_piecewise3(t88, 0, t476)
  t499 = f.my_piecewise3(t88, t476, 0)
  t503 = f.my_piecewise5(t79, (-t82 * t237 * t477 - params.c1 * t477 * t84) * t86, t87, -0.667e0 * t484 - 0.8891110e0 * t89 * t484 - 0.1989259803147e1 * t91 * t484 + 0.5805188177960e1 * t93 * t484 - 0.4439990207985e1 * t95 * t484 + 0.1407173648874e1 * t97 * t484 - 0.162300903254e0 * t99 * t484, -t257 * t259 * t499 * t108)
  t540 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (t503 * t111 + 0.2e1 * (0.162742215233874e0 * t476 + 0.11870625016560800000000000000000000000000000000000e0 * t120 * t51 * t66 * t77 - t126 * t426 / t19 / t33 * t77 / 0.12e2) * t148 * t170 + 0.4e1 * t295 * t296 * t475 - 0.8e1 * t147 * t152 * t69 / t153 / t150 * t311 * t475 + 0.4e1 * t303 * t326 * t475 * t169) * t189)
  vtau_0_ = 0.2e1 * r0 * t540
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 * t5 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t23 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t27 / t26
  t31 = s0 ** 2
  t32 = t25 * t29 * t31
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = r0 ** 2
  t35 = t34 ** 2
  t38 = 0.1e1 / t19 / t35 / r0
  t39 = t33 * t38
  t40 = params.dp2 ** 2
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t46 = jnp.exp(-t32 * t39 * t42 / 0.288e3)
  t51 = t27 ** 2
  t52 = 0.1e1 / t51
  t53 = (-0.162742215233874e0 * t23 * t46 + 0.10e2 / 0.81e2) * t24 * t52
  t54 = t33 ** 2
  t55 = s0 * t54
  t57 = 0.1e1 / t20 / t34
  t58 = t55 * t57
  t61 = params.k1 + t53 * t58 / 0.24e2
  t65 = params.k1 * (0.1e1 - params.k1 / t61)
  t66 = tau0 * t54
  t68 = 0.1e1 / t20 / r0
  t71 = t66 * t68 - t58 / 0.8e1
  t74 = params.eta * s0
  t78 = 0.3e1 / 0.10e2 * t25 * t51 + t74 * t54 * t57 / 0.8e1
  t79 = 0.1e1 / t78
  t80 = t71 * t79
  t81 = t80 <= 0.0e0
  t82 = 0.0e0 < t80
  t83 = f.my_piecewise3(t82, 0, t80)
  t84 = params.c1 * t83
  t85 = 0.1e1 - t83
  t86 = 0.1e1 / t85
  t88 = jnp.exp(-t84 * t86)
  t89 = t80 <= 0.25e1
  t90 = 0.25e1 < t80
  t91 = f.my_piecewise3(t90, 0.25e1, t80)
  t93 = t91 ** 2
  t95 = t93 * t91
  t97 = t93 ** 2
  t99 = t97 * t91
  t101 = t97 * t93
  t106 = f.my_piecewise3(t90, t80, 0.25e1)
  t107 = 0.1e1 - t106
  t110 = jnp.exp(params.c2 / t107)
  t112 = f.my_piecewise5(t81, t88, t89, 0.1e1 - 0.667e0 * t91 - 0.4445555e0 * t93 - 0.663086601049e0 * t95 + 0.1451297044490e1 * t97 - 0.887998041597e0 * t99 + 0.234528941479e0 * t101 - 0.23185843322e-1 * t97 * t95, -params.d * t110)
  t113 = 0.174e0 - t65
  t117 = t23 * t24 * t52
  t120 = 0.1e1 - t80
  t121 = t120 ** 2
  t126 = (0.40570770199022687796862290864197530864197530864200e-1 - 0.30235468026081006356817095666666666666666666666667e0 * params.eta) * t24 * t52
  t133 = (0.3e1 / 0.4e1 * params.eta + 0.2e1 / 0.3e1) ** 2
  t138 = (0.290700106132790123456790123456790123456790123457e-2 - 0.27123702538979000000000000000000000000000000000000e0 * params.eta) ** 2
  t143 = (0.146e3 / 0.2025e4 * t133 - 0.73e2 / 0.540e3 * params.eta - 0.146e3 / 0.1215e4 + t138 / params.k1) * t25 * t29
  t144 = t31 * t33
  t148 = -0.162742215233874e0 + 0.162742215233874e0 * t80 + 0.67809256347447500000000000000000000000000000000000e-2 * t117 * t58 - 0.59353125082804000000000000000000000000000000000000e-1 * t121 + t126 * t55 * t57 * t120 / 0.24e2 + t143 * t144 * t38 / 0.288e3
  t149 = t71 ** 2
  t150 = t148 * t149
  t151 = t78 ** 2
  t152 = 0.1e1 / t151
  t153 = t149 ** 2
  t154 = t151 ** 2
  t155 = 0.1e1 / t154
  t157 = t153 * t155 + 0.1e1
  t158 = 0.1e1 / t157
  t160 = params.da4 ** 2
  t161 = 0.1e1 / t160
  t163 = params.dp4 ** 2
  t164 = t163 ** 2
  t165 = 0.1e1 / t164
  t170 = jnp.exp(-t121 * t161 - t32 * t39 * t165 / 0.288e3)
  t171 = t152 * t158 * t170
  t174 = t112 * t113 + 0.2e1 * t150 * t171 + t65 + 0.1e1
  t176 = jnp.sqrt(0.3e1)
  t177 = 0.1e1 / t27
  t179 = jnp.sqrt(s0)
  t180 = t179 * t33
  t184 = t25 * t177 * t180 / t19 / r0
  t185 = jnp.sqrt(t184)
  t189 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t176 / t185)
  t190 = 0.1e1 - t189
  t194 = params.k1 ** 2
  t195 = t61 ** 2
  t196 = 0.1e1 / t195
  t197 = t194 * t196
  t198 = t26 ** 2
  t200 = t23 / t198
  t202 = t200 * t31 * s0
  t203 = t35 ** 2
  t210 = t34 * r0
  t212 = 0.1e1 / t20 / t210
  t213 = t55 * t212
  t216 = -0.15068723632766111111111111111111111111111111111111e-2 * t202 / t203 / r0 * t42 * t46 - t53 * t213 / 0.9e1
  t221 = -0.5e1 / 0.3e1 * t66 * t57 + t213 / 0.3e1
  t222 = t221 * t79
  t224 = t71 * t152 * params.eta
  t225 = t224 * t213
  t227 = t222 + t225 / 0.3e1
  t228 = f.my_piecewise3(t82, 0, t227)
  t231 = t85 ** 2
  t232 = 0.1e1 / t231
  t235 = -t84 * t232 * t228 - params.c1 * t228 * t86
  t237 = f.my_piecewise3(t90, 0, t227)
  t252 = params.d * params.c2
  t253 = t107 ** 2
  t254 = 0.1e1 / t253
  t255 = f.my_piecewise3(t90, t227, 0)
  t259 = f.my_piecewise5(t81, t235 * t88, t89, -0.667e0 * t237 - 0.8891110e0 * t91 * t237 - 0.1989259803147e1 * t93 * t237 + 0.5805188177960e1 * t95 * t237 - 0.4439990207985e1 * t97 * t237 + 0.1407173648874e1 * t99 * t237 - 0.162300903254e0 * t101 * t237, -t252 * t254 * t255 * t110)
  t261 = t112 * t194
  t262 = t196 * t216
  t268 = -t227
  t281 = 0.1e1 / t19 / t35 / t34
  t285 = 0.162742215233874e0 * t222 + 0.54247405077958000000000000000000000000000000000000e-1 * t225 - 0.18082468359319333333333333333333333333333333333333e-1 * t117 * t213 - 0.11870625016560800000000000000000000000000000000000e0 * t120 * t268 - t126 * t55 * t212 * t120 / 0.9e1 + t126 * t55 * t57 * t268 / 0.24e2 - t143 * t144 * t281 / 0.54e2
  t286 = t285 * t149
  t289 = t148 * t71
  t290 = t289 * t152
  t291 = t158 * t170
  t292 = t291 * t221
  t296 = 0.1e1 / t151 / t78
  t297 = t296 * t158
  t298 = t150 * t297
  t299 = t170 * params.eta
  t300 = t299 * t213
  t303 = t150 * t152
  t304 = t157 ** 2
  t305 = 0.1e1 / t304
  t306 = t305 * t170
  t307 = t149 * t71
  t308 = t307 * t155
  t312 = 0.1e1 / t154 / t78
  t314 = t153 * t312 * params.eta
  t317 = 0.4e1 * t308 * t221 + 0.4e1 / 0.3e1 * t314 * t213
  t318 = t306 * t317
  t321 = t120 * t161
  t328 = -0.2e1 * t321 * t268 + t32 * t33 * t281 * t165 / 0.54e2
  t329 = t158 * t328
  t330 = t329 * t170
  t333 = t197 * t216 + t259 * t113 - t261 * t262 + 0.2e1 * t286 * t171 + 0.4e1 * t290 * t292 + 0.4e1 / 0.3e1 * t298 * t300 - 0.2e1 * t303 * t318 + 0.2e1 * t303 * t330
  t338 = 3 ** (0.1e1 / 0.6e1)
  t339 = t338 ** 2
  t340 = t339 ** 2
  t342 = t340 * t338 * t5
  t344 = t17 / t34
  t352 = 0.1e1 / t185 / t184 * t25 * t177 * t180 * t189
  t356 = f.my_piecewise3(t2, 0, -t18 * t21 * t174 * t190 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t333 * t190 - 0.24739500000000000000000000000000000000000000000000e1 * t342 * t344 * t174 * t352)
  t372 = t221 ** 2
  t379 = 0.1e1 / t20 / t35
  t380 = t55 * t379
  t382 = 0.40e2 / 0.9e1 * t66 * t212 - 0.11e2 / 0.9e1 * t380
  t383 = t382 * t79
  t387 = t221 * t152 * params.eta * t213
  t390 = params.eta ** 2
  t392 = t35 * t210
  t394 = 0.1e1 / t19 / t392
  t395 = t144 * t394
  t396 = t71 * t296 * t390 * t395
  t398 = t224 * t380
  t402 = t268 ** 2
  t407 = -t383 - 0.2e1 / 0.3e1 * t387 - 0.4e1 / 0.9e1 * t396 + 0.11e2 / 0.9e1 * t398
  t424 = 0.162742215233874e0 * t383 + 0.10849481015591600000000000000000000000000000000000e0 * t387 + 0.72329873437277333333333333333333333333333333333333e-1 * t396 - 0.19890715195251266666666666666666666666666666666667e0 * t398 + 0.66302383984170888888888888888888888888888888888888e-1 * t117 * t380 - 0.11870625016560800000000000000000000000000000000000e0 * t402 - 0.11870625016560800000000000000000000000000000000000e0 * t120 * t407 + 0.11e2 / 0.27e2 * t126 * t55 * t379 * t120 - 0.2e1 / 0.9e1 * t126 * t55 * t212 * t268 + t126 * t55 * t57 * t407 / 0.24e2 + 0.19e2 / 0.162e3 * t143 * t395
  t428 = -t407
  t429 = f.my_piecewise3(t82, 0, t428)
  t432 = t228 ** 2
  t445 = t235 ** 2
  t448 = f.my_piecewise3(t90, 0, t428)
  t450 = t237 ** 2
  t474 = -0.667e0 * t448 - 0.8891110e0 * t450 - 0.8891110e0 * t91 * t448 - 0.3978519606294e1 * t91 * t450 - 0.1989259803147e1 * t93 * t448 + 0.17415564533880e2 * t93 * t450 + 0.5805188177960e1 * t95 * t448 - 0.17759960831940e2 * t95 * t450 - 0.4439990207985e1 * t97 * t448 + 0.7035868244370e1 * t97 * t450 + 0.1407173648874e1 * t99 * t448 - 0.973805419524e0 * t99 * t450 - 0.162300903254e0 * t101 * t448
  t477 = t255 ** 2
  t482 = f.my_piecewise3(t90, t428, 0)
  t486 = params.c2 ** 2
  t488 = t253 ** 2
  t494 = f.my_piecewise5(t81, (-params.c1 * t429 * t86 - 0.2e1 * params.c1 * t432 * t232 - 0.2e1 * t84 / t231 / t85 * t432 - t84 * t232 * t429) * t88 + t445 * t88, t89, t474, -0.2e1 * t252 / t253 / t107 * t477 * t110 - t252 * t254 * t482 * t110 - params.d * t486 / t488 * t477 * t110)
  t502 = t31 ** 2
  t509 = t41 ** 2
  t519 = 0.17580177571560462962962962962962962962962962962963e-1 * t202 / t203 / t34 * t42 * t46 - 0.27905043764381687242798353909465020576131687242798e-4 * t200 * t502 * s0 / t19 / t203 / t392 / t509 * t25 * t29 * t33 * t46 + 0.11e2 / 0.27e2 * t53 * t380
  t522 = 0.1e1 / t195 / t61
  t524 = t216 ** 2
  t540 = t328 ** 2
  t549 = t286 * t152
  t554 = -0.4e1 * t303 * t305 * t328 * t170 * t317 + 0.8e1 * t285 * t71 * t152 * t292 + 0.2e1 * t303 * t158 * t540 * t170 + 0.8e1 * t290 * t329 * t170 * t221 - 0.8e1 * t290 * t306 * t221 * t317 + 0.4e1 * t148 * t372 * t171 + 0.2e1 * t424 * t149 * t171 - 0.2e1 * t194 * t522 * t524 + t494 * t113 + t197 * t519 - 0.4e1 * t549 * t318 + 0.4e1 * t549 * t330
  t563 = t54 * t212
  t597 = t317 ** 2
  t638 = 0.4e1 * t290 * t291 * t382 - 0.2e1 * t303 * t306 * (0.12e2 * t149 * t155 * t372 + 0.32e2 / 0.3e1 * t307 * t312 * t221 * t74 * t563 + 0.4e1 * t308 * t382 + 0.40e2 / 0.9e1 * t153 / t154 / t151 * t390 * t395 - 0.44e2 / 0.9e1 * t314 * t380) + 0.2e1 * t303 * t158 * (-0.2e1 * t402 * t161 - 0.2e1 * t321 * t407 - 0.19e2 / 0.162e3 * t32 * t33 * t394 * t165) * t170 + 0.4e1 * t303 / t304 / t157 * t170 * t597 - 0.2e1 * t259 * t194 * t262 + 0.2e1 * t261 * t522 * t524 - t261 * t196 * t519 + 0.16e2 / 0.3e1 * t289 * t297 * t170 * t221 * params.eta * t213 - 0.8e1 / 0.3e1 * t150 * t296 * t305 * t170 * t74 * t563 * t317 + 0.8e1 / 0.3e1 * t150 * t297 * t328 * t300 - 0.44e2 / 0.9e1 * t298 * t299 * t380 + 0.8e1 / 0.3e1 * t150 * t155 * t158 * t170 * t390 * t395 + 0.8e1 / 0.3e1 * t286 * t297 * t300
  t664 = t4 ** 2
  t679 = f.my_piecewise3(t2, 0, t18 * t68 * t174 * t190 / 0.12e2 - t18 * t21 * t333 * t190 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t342 * t17 / t210 * t174 * t352 - 0.3e1 / 0.8e1 * t18 * t19 * (t554 + t638) * t190 - 0.49479000000000000000000000000000000000000000000000e1 * t342 * t344 * t333 * t352 - 0.49479000000000000000000000000000000000000000000000e1 * t342 * t17 / t19 / t35 * t174 / t185 / t58 * t55 * t189 + 0.40802857350000000000000000000000000000000000000000e1 * t3 * t664 * jnp.pi * t17 / t19 * t174 / t179 * t24 * t52 * t54 * t189)
  v2rho2_0_ = 0.2e1 * r0 * t679 + 0.4e1 * t356
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 * t5 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / r0
  t24 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 * t27
  t30 = 0.1e1 / t29
  t32 = s0 ** 2
  t33 = t26 * t30 * t32
  t34 = 2 ** (0.1e1 / 0.3e1)
  t35 = r0 ** 2
  t36 = t35 ** 2
  t37 = t36 * r0
  t39 = 0.1e1 / t19 / t37
  t40 = t34 * t39
  t41 = params.dp2 ** 2
  t42 = t41 ** 2
  t43 = 0.1e1 / t42
  t47 = jnp.exp(-t33 * t40 * t43 / 0.288e3)
  t52 = t28 ** 2
  t53 = 0.1e1 / t52
  t54 = (-0.162742215233874e0 * t24 * t47 + 0.10e2 / 0.81e2) * t25 * t53
  t55 = t34 ** 2
  t56 = s0 * t55
  t58 = 0.1e1 / t20 / t35
  t59 = t56 * t58
  t62 = params.k1 + t54 * t59 / 0.24e2
  t66 = params.k1 * (0.1e1 - params.k1 / t62)
  t67 = tau0 * t55
  t70 = t67 * t22 - t59 / 0.8e1
  t73 = params.eta * s0
  t77 = 0.3e1 / 0.10e2 * t26 * t52 + t73 * t55 * t58 / 0.8e1
  t78 = 0.1e1 / t77
  t79 = t70 * t78
  t80 = t79 <= 0.0e0
  t81 = 0.0e0 < t79
  t82 = f.my_piecewise3(t81, 0, t79)
  t83 = params.c1 * t82
  t84 = 0.1e1 - t82
  t85 = 0.1e1 / t84
  t87 = jnp.exp(-t83 * t85)
  t88 = t79 <= 0.25e1
  t89 = 0.25e1 < t79
  t90 = f.my_piecewise3(t89, 0.25e1, t79)
  t92 = t90 ** 2
  t94 = t92 * t90
  t96 = t92 ** 2
  t98 = t96 * t90
  t100 = t96 * t92
  t105 = f.my_piecewise3(t89, t79, 0.25e1)
  t106 = 0.1e1 - t105
  t109 = jnp.exp(params.c2 / t106)
  t111 = f.my_piecewise5(t80, t87, t88, 0.1e1 - 0.667e0 * t90 - 0.4445555e0 * t92 - 0.663086601049e0 * t94 + 0.1451297044490e1 * t96 - 0.887998041597e0 * t98 + 0.234528941479e0 * t100 - 0.23185843322e-1 * t96 * t94, -params.d * t109)
  t112 = 0.174e0 - t66
  t116 = t24 * t25 * t53
  t119 = 0.1e1 - t79
  t120 = t119 ** 2
  t125 = (0.40570770199022687796862290864197530864197530864200e-1 - 0.30235468026081006356817095666666666666666666666667e0 * params.eta) * t25 * t53
  t132 = (0.3e1 / 0.4e1 * params.eta + 0.2e1 / 0.3e1) ** 2
  t137 = (0.290700106132790123456790123456790123456790123457e-2 - 0.27123702538979000000000000000000000000000000000000e0 * params.eta) ** 2
  t142 = (0.146e3 / 0.2025e4 * t132 - 0.73e2 / 0.540e3 * params.eta - 0.146e3 / 0.1215e4 + t137 / params.k1) * t26 * t30
  t143 = t32 * t34
  t147 = -0.162742215233874e0 + 0.162742215233874e0 * t79 + 0.67809256347447500000000000000000000000000000000000e-2 * t116 * t59 - 0.59353125082804000000000000000000000000000000000000e-1 * t120 + t125 * t56 * t58 * t119 / 0.24e2 + t142 * t143 * t39 / 0.288e3
  t148 = t70 ** 2
  t149 = t147 * t148
  t150 = t77 ** 2
  t151 = 0.1e1 / t150
  t152 = t148 ** 2
  t153 = t150 ** 2
  t154 = 0.1e1 / t153
  t156 = t152 * t154 + 0.1e1
  t157 = 0.1e1 / t156
  t159 = params.da4 ** 2
  t160 = 0.1e1 / t159
  t162 = params.dp4 ** 2
  t163 = t162 ** 2
  t164 = 0.1e1 / t163
  t169 = jnp.exp(-t120 * t160 - t33 * t40 * t164 / 0.288e3)
  t170 = t151 * t157 * t169
  t173 = t111 * t112 + 0.2e1 * t149 * t170 + t66 + 0.1e1
  t175 = jnp.sqrt(0.3e1)
  t176 = 0.1e1 / t28
  t178 = jnp.sqrt(s0)
  t179 = t178 * t34
  t181 = 0.1e1 / t19 / r0
  t183 = t26 * t176 * t179 * t181
  t184 = jnp.sqrt(t183)
  t188 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t175 / t184)
  t189 = 0.1e1 - t188
  t193 = 0.1e1 / t20
  t194 = params.k1 ** 2
  t195 = t62 ** 2
  t196 = 0.1e1 / t195
  t197 = t194 * t196
  t198 = t27 ** 2
  t200 = t24 / t198
  t201 = t32 * s0
  t202 = t200 * t201
  t203 = t36 ** 2
  t210 = t35 * r0
  t212 = 0.1e1 / t20 / t210
  t213 = t56 * t212
  t216 = -0.15068723632766111111111111111111111111111111111111e-2 * t202 / t203 / r0 * t43 * t47 - t54 * t213 / 0.9e1
  t221 = -0.5e1 / 0.3e1 * t67 * t58 + t213 / 0.3e1
  t222 = t221 * t78
  t224 = t70 * t151 * params.eta
  t225 = t224 * t213
  t227 = t222 + t225 / 0.3e1
  t228 = f.my_piecewise3(t81, 0, t227)
  t231 = t84 ** 2
  t232 = 0.1e1 / t231
  t233 = t232 * t228
  t235 = -params.c1 * t228 * t85 - t83 * t233
  t237 = f.my_piecewise3(t89, 0, t227)
  t239 = t90 * t237
  t241 = t92 * t237
  t243 = t94 * t237
  t245 = t96 * t237
  t247 = t98 * t237
  t252 = params.d * params.c2
  t253 = t106 ** 2
  t254 = 0.1e1 / t253
  t255 = f.my_piecewise3(t89, t227, 0)
  t259 = f.my_piecewise5(t80, t235 * t87, t88, -0.667e0 * t237 - 0.8891110e0 * t239 - 0.1989259803147e1 * t241 + 0.5805188177960e1 * t243 - 0.4439990207985e1 * t245 + 0.1407173648874e1 * t247 - 0.162300903254e0 * t100 * t237, -t252 * t254 * t255 * t109)
  t261 = t111 * t194
  t262 = t196 * t216
  t268 = -t227
  t279 = t36 * t35
  t281 = 0.1e1 / t19 / t279
  t285 = 0.162742215233874e0 * t222 + 0.54247405077958000000000000000000000000000000000000e-1 * t225 - 0.18082468359319333333333333333333333333333333333333e-1 * t116 * t213 - 0.11870625016560800000000000000000000000000000000000e0 * t119 * t268 - t125 * t56 * t212 * t119 / 0.9e1 + t125 * t56 * t58 * t268 / 0.24e2 - t142 * t143 * t281 / 0.54e2
  t286 = t285 * t148
  t289 = t147 * t70
  t290 = t289 * t151
  t291 = t157 * t169
  t292 = t291 * t221
  t295 = t150 * t77
  t296 = 0.1e1 / t295
  t297 = t296 * t157
  t298 = t149 * t297
  t299 = t169 * params.eta
  t300 = t299 * t213
  t303 = t149 * t151
  t304 = t156 ** 2
  t305 = 0.1e1 / t304
  t306 = t305 * t169
  t307 = t148 * t70
  t308 = t307 * t154
  t312 = 0.1e1 / t153 / t77
  t314 = t152 * t312 * params.eta
  t317 = 0.4e1 * t308 * t221 + 0.4e1 / 0.3e1 * t314 * t213
  t318 = t306 * t317
  t321 = t119 * t160
  t328 = -0.2e1 * t321 * t268 + t33 * t34 * t281 * t164 / 0.54e2
  t329 = t157 * t328
  t330 = t329 * t169
  t333 = t197 * t216 + t259 * t112 - t261 * t262 + 0.2e1 * t286 * t170 + 0.4e1 * t290 * t292 + 0.4e1 / 0.3e1 * t298 * t300 - 0.2e1 * t303 * t318 + 0.2e1 * t303 * t330
  t338 = 3 ** (0.1e1 / 0.6e1)
  t339 = t338 ** 2
  t340 = t339 ** 2
  t341 = t340 * t338
  t342 = t341 * t5
  t344 = t17 / t210
  t348 = 0.1e1 / t184 / t183
  t352 = t348 * t26 * t176 * t179 * t188
  t355 = t297 * t169
  t356 = t289 * t355
  t357 = t221 * params.eta
  t358 = t357 * t213
  t361 = t296 * t305
  t362 = t361 * t169
  t363 = t149 * t362
  t364 = t55 * t212
  t366 = t73 * t364 * t317
  t369 = t297 * t328
  t370 = t149 * t369
  t376 = 0.1e1 / t20 / t36
  t377 = t56 * t376
  t379 = 0.40e2 / 0.9e1 * t67 * t212 - 0.11e2 / 0.9e1 * t377
  t380 = t379 * t78
  t382 = t221 * t151 * params.eta
  t383 = t382 * t213
  t386 = params.eta ** 2
  t387 = t70 * t296 * t386
  t388 = t36 * t210
  t390 = 0.1e1 / t19 / t388
  t391 = t143 * t390
  t392 = t387 * t391
  t394 = t224 * t377
  t396 = t380 + 0.2e1 / 0.3e1 * t383 + 0.4e1 / 0.9e1 * t392 - 0.11e2 / 0.9e1 * t394
  t397 = f.my_piecewise3(t81, 0, t396)
  t398 = params.c1 * t397
  t400 = t228 ** 2
  t405 = 0.1e1 / t231 / t84
  t411 = -t83 * t232 * t397 - 0.2e1 * params.c1 * t400 * t232 - 0.2e1 * t83 * t405 * t400 - t398 * t85
  t413 = t235 ** 2
  t416 = f.my_piecewise3(t89, 0, t396)
  t418 = t237 ** 2
  t442 = -0.667e0 * t416 - 0.8891110e0 * t418 - 0.8891110e0 * t90 * t416 - 0.3978519606294e1 * t90 * t418 - 0.1989259803147e1 * t92 * t416 + 0.17415564533880e2 * t92 * t418 + 0.5805188177960e1 * t94 * t416 - 0.17759960831940e2 * t94 * t418 - 0.4439990207985e1 * t96 * t416 + 0.7035868244370e1 * t96 * t418 + 0.1407173648874e1 * t98 * t416 - 0.973805419524e0 * t98 * t418 - 0.162300903254e0 * t100 * t416
  t444 = 0.1e1 / t253 / t106
  t445 = t255 ** 2
  t450 = f.my_piecewise3(t89, t396, 0)
  t454 = params.c2 ** 2
  t455 = params.d * t454
  t456 = t253 ** 2
  t457 = 0.1e1 / t456
  t462 = f.my_piecewise5(t80, t411 * t87 + t413 * t87, t88, t442, -t252 * t254 * t450 * t109 - 0.2e1 * t252 * t444 * t445 * t109 - t455 * t457 * t445 * t109)
  t464 = t221 ** 2
  t465 = t147 * t464
  t474 = t268 ** 2
  t476 = -t396
  t493 = 0.162742215233874e0 * t380 + 0.10849481015591600000000000000000000000000000000000e0 * t383 + 0.72329873437277333333333333333333333333333333333333e-1 * t392 - 0.19890715195251266666666666666666666666666666666667e0 * t394 + 0.66302383984170888888888888888888888888888888888888e-1 * t116 * t377 - 0.11870625016560800000000000000000000000000000000000e0 * t474 - 0.11870625016560800000000000000000000000000000000000e0 * t119 * t476 + 0.11e2 / 0.27e2 * t125 * t56 * t376 * t119 - 0.2e1 / 0.9e1 * t125 * t56 * t212 * t268 + t125 * t56 * t58 * t476 / 0.24e2 + 0.19e2 / 0.162e3 * t142 * t391
  t494 = t493 * t148
  t503 = t32 ** 2
  t504 = t503 * s0
  t510 = t42 ** 2
  t515 = 0.1e1 / t510 * t26 * t30 * t34 * t47
  t520 = 0.17580177571560462962962962962962962962962962962963e-1 * t202 / t203 / t35 * t43 * t47 - 0.27905043764381687242798353909465020576131687242798e-4 * t200 * t504 / t19 / t203 / t388 * t515 + 0.11e2 / 0.27e2 * t54 * t377
  t521 = t196 * t520
  t523 = t259 * t194
  t527 = 0.1e1 / t195 / t62
  t528 = t216 ** 2
  t529 = t527 * t528
  t533 = t194 * t527
  t536 = t305 * t328
  t537 = t169 * t317
  t538 = t536 * t537
  t541 = 0.16e2 / 0.3e1 * t356 * t358 - 0.8e1 / 0.3e1 * t363 * t366 + 0.8e1 / 0.3e1 * t370 * t300 + t462 * t112 + 0.4e1 * t465 * t170 + 0.2e1 * t494 * t170 - t261 * t521 - 0.2e1 * t523 * t262 + 0.2e1 * t261 * t529 + t197 * t520 - 0.2e1 * t533 * t528 - 0.4e1 * t303 * t538
  t542 = t221 * t317
  t543 = t306 * t542
  t546 = t169 * t221
  t547 = t329 * t546
  t550 = t154 * t157
  t551 = t149 * t550
  t552 = t169 * t386
  t553 = t552 * t391
  t556 = t286 * t297
  t559 = t299 * t377
  t562 = t328 ** 2
  t563 = t157 * t562
  t564 = t563 * t169
  t567 = t291 * t379
  t570 = t148 * t154
  t573 = t307 * t312
  t574 = t573 * t221
  t575 = t73 * t364
  t581 = 0.1e1 / t153 / t150
  t583 = t152 * t581 * t386
  t588 = 0.12e2 * t570 * t464 + 0.32e2 / 0.3e1 * t574 * t575 + 0.4e1 * t308 * t379 + 0.40e2 / 0.9e1 * t583 * t391 - 0.44e2 / 0.9e1 * t314 * t377
  t589 = t306 * t588
  t596 = t34 * t390
  t600 = -0.2e1 * t474 * t160 - 0.2e1 * t321 * t476 - 0.19e2 / 0.162e3 * t33 * t596 * t164
  t601 = t157 * t600
  t602 = t601 * t169
  t606 = 0.1e1 / t304 / t156
  t607 = t606 * t169
  t608 = t317 ** 2
  t609 = t607 * t608
  t612 = t285 * t70
  t613 = t612 * t151
  t616 = t286 * t151
  t621 = -0.8e1 * t290 * t543 + 0.8e1 * t290 * t547 + 0.8e1 / 0.3e1 * t551 * t553 + 0.8e1 / 0.3e1 * t556 * t300 - 0.44e2 / 0.9e1 * t298 * t559 + 0.2e1 * t303 * t564 + 0.4e1 * t290 * t567 - 0.2e1 * t303 * t589 + 0.2e1 * t303 * t602 + 0.4e1 * t303 * t609 + 0.8e1 * t613 * t292 - 0.4e1 * t616 * t318 + 0.4e1 * t616 * t330
  t622 = t541 + t621
  t628 = t17 / t35
  t635 = t17 / t19 / t36
  t646 = 0.1e1 / t184 / t59 * t56 * t188 / 0.6e1
  t649 = t4 ** 2
  t651 = t3 * t649 * jnp.pi
  t653 = t17 / t19
  t656 = 0.1e1 / t178
  t660 = t656 * t25 * t53 * t55 * t188
  t664 = f.my_piecewise3(t2, 0, t18 * t22 * t173 * t189 / 0.12e2 - t18 * t193 * t333 * t189 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t342 * t344 * t173 * t352 - 0.3e1 / 0.8e1 * t18 * t19 * t622 * t189 - 0.49479000000000000000000000000000000000000000000000e1 * t342 * t628 * t333 * t352 - 0.29687400000000000000000000000000000000000000000000e2 * t342 * t635 * t173 * t646 + 0.40802857350000000000000000000000000000000000000000e1 * t651 * t653 * t173 * t660)
  t666 = t58 * t173
  t674 = 0.1e1 / t36
  t694 = t17 * t181 * t173
  t701 = 0.1e1 / t20 / t37
  t702 = t56 * t701
  t704 = -0.440e3 / 0.27e2 * t67 * t376 + 0.154e3 / 0.27e2 * t702
  t705 = t704 * t78
  t708 = t379 * t151 * params.eta * t213
  t711 = t221 * t296 * t386 * t391
  t713 = t382 * t377
  t715 = t70 * t154
  t716 = t386 * params.eta
  t719 = 0.1e1 / t203 / t210
  t720 = t716 * t201 * t719
  t721 = t715 * t720
  t724 = 0.1e1 / t19 / t203
  t725 = t143 * t724
  t726 = t387 * t725
  t728 = t224 * t702
  t730 = t705 + t708 + 0.4e1 / 0.3e1 * t711 - 0.11e2 / 0.3e1 * t713 + 0.8e1 / 0.9e1 * t721 - 0.44e2 / 0.9e1 * t726 + 0.154e3 / 0.27e2 * t728
  t731 = f.my_piecewise3(t81, 0, t730)
  t736 = t400 * t228
  t740 = t231 ** 2
  t759 = f.my_piecewise3(t89, 0, t730)
  t765 = t418 * t237
  t795 = -0.667e0 * t759 - 0.26673330e1 * t237 * t416 - 0.8891110e0 * t90 * t759 - 0.3978519606294e1 * t765 - 0.11935558818882e2 * t239 * t416 - 0.1989259803147e1 * t92 * t759 + 0.34831129067760e2 * t90 * t765 + 0.52246693601640e2 * t241 * t416 + 0.5805188177960e1 * t94 * t759 - 0.53279882495820e2 * t92 * t765 - 0.53279882495820e2 * t243 * t416 - 0.4439990207985e1 * t96 * t759 + 0.28143472977480e2 * t94 * t765 + 0.21107604733110e2 * t245 * t416 + 0.1407173648874e1 * t98 * t759 - 0.4869027097620e1 * t96 * t765 - 0.2921416258572e1 * t247 * t416 - 0.162300903254e0 * t100 * t759
  t796 = t445 * t255
  t803 = t255 * t109 * t450
  t812 = f.my_piecewise3(t89, t730, 0)
  t827 = f.my_piecewise5(t80, (-params.c1 * t731 * t85 - 0.6e1 * t398 * t233 - 0.6e1 * params.c1 * t736 * t405 - 0.6e1 * t83 / t740 * t736 - 0.6e1 * t83 * t405 * t228 * t397 - t83 * t232 * t731) * t87 + 0.3e1 * t411 * t235 * t87 + t413 * t235 * t87, t88, t795, -0.6e1 * t252 * t457 * t796 * t109 - 0.6e1 * t252 * t444 * t803 - 0.6e1 * t455 / t456 / t106 * t796 * t109 - t252 * t254 * t812 * t109 - 0.3e1 * t455 * t457 * t803 - params.d * t454 * params.c2 / t456 / t253 * t796 * t109)
  t829 = t195 ** 2
  t830 = 0.1e1 / t829
  t832 = t528 * t216
  t839 = t203 ** 2
  t864 = -0.19053563882319816049382716049382716049382716049383e0 * t202 * t719 * t43 * t47 + 0.75343618163830555555555555555555555555555555555555e-3 * t200 * t504 / t19 / t839 * t515 - 0.31005604182646319158664837677183356195701874714220e-5 * t200 * t503 * t201 / t20 / t839 / t37 / t510 / t42 * t25 / t52 / t198 * t55 * t47 - 0.154e3 / 0.81e2 * t54 * t702
  t901 = t386 * t32
  t919 = t55 * t376
  t926 = t827 * t112 + 0.6e1 * t194 * t830 * t832 + t197 * t864 + 0.8e1 * t149 * t550 * t328 * t553 + 0.8e1 * t356 * t379 * params.eta * t213 - 0.4e1 * t363 * t588 * params.eta * t213 + 0.4e1 * t149 * t297 * t600 * t300 + 0.8e1 * t149 * t296 * t606 * t169 * t608 * params.eta * t213 - 0.8e1 * t286 * t362 * t366 + 0.16e2 * t289 * t550 * t169 * t221 * t386 * t391 - 0.8e1 * t149 * t154 * t305 * t169 * t901 * t596 * t317 + 0.4e1 * t149 * t297 * t562 * t300 + 0.16e2 * t612 * t355 * t358 + 0.8e1 * t286 * t369 * t300 - 0.88e2 / 0.3e1 * t356 * t357 * t377 + 0.44e2 / 0.3e1 * t363 * t73 * t919 * t317 - 0.44e2 / 0.3e1 * t370 * t559
  t993 = 0.64e2 / 0.9e1 * t149 * t312 * t157 * t169 * t716 * t201 * t719 - 0.24e2 * t289 * t151 * t305 * t328 * t169 * t542 - 0.6e1 * t303 * t305 * t600 * t537 - 0.6e1 * t303 * t536 * t169 * t588 - 0.24e2 * t613 * t543 + 0.12e2 * t290 * t601 * t546 + 0.12e2 * t290 * t329 * t169 * t379 - 0.12e2 * t616 * t538 - 0.6e1 * t303 * t305 * t562 * t537 + 0.24e2 * t290 * t607 * t221 * t608 + 0.6e1 * t303 * t329 * t169 * t600 + 0.24e2 * t613 * t547 - 0.12e2 * t290 * t306 * t221 * t588 + 0.12e2 * t303 * t607 * t588 * t317 + 0.12e2 * t290 * t563 * t546 + 0.12e2 * t303 * t606 * t328 * t169 * t608 - 0.12e2 * t290 * t306 * t379 * t317
  t1021 = -t730
  t1042 = 0.162742215233874e0 * t705 + 0.16274221523387400000000000000000000000000000000000e0 * t708 + 0.21698962031183200000000000000000000000000000000000e0 * t711 - 0.59672145585753800000000000000000000000000000000000e0 * t713 + 0.14465974687455466666666666666666666666666666666667e0 * t721 - 0.79562860781005066666666666666666666666666666666667e0 * t726 + 0.92823337577839244444444444444444444444444444444446e0 * t728 - 0.30941112525946414814814814814814814814814814814814e0 * t116 * t702 - 0.35611875049682400000000000000000000000000000000000e0 * t268 * t476 - 0.11870625016560800000000000000000000000000000000000e0 * t119 * t1021 - 0.154e3 / 0.81e2 * t125 * t56 * t701 * t119 + 0.11e2 / 0.9e1 * t125 * t56 * t376 * t268 - t125 * t56 * t212 * t476 / 0.3e1 + t125 * t56 * t58 * t1021 / 0.24e2 - 0.209e3 / 0.243e3 * t142 * t725
  t1053 = t304 ** 2
  t1060 = t494 * t151
  t1090 = 0.6e1 * t523 * t529 - 0.6e1 * t261 * t830 * t832 - 0.3e1 * t462 * t194 * t262 - 0.3e1 * t523 * t521 - t261 * t196 * t864 - 0.6e1 * t533 * t520 * t216 + 0.2e1 * t1042 * t148 * t170 + 0.6e1 * t261 * t527 * t520 * t216 + 0.12e2 * t285 * t464 * t170 - 0.12e2 * t303 / t1053 * t169 * t608 * t317 - 0.6e1 * t1060 * t318 + 0.6e1 * t616 * t564 + 0.6e1 * t1060 * t330 + 0.6e1 * t616 * t602 + 0.2e1 * t303 * t157 * (-0.6e1 * t268 * t160 * t476 - 0.2e1 * t321 * t1021 + 0.209e3 / 0.243e3 * t33 * t34 * t724 * t164) * t169 + 0.12e2 * t147 * t221 * t151 * t567 + 0.4e1 * t290 * t291 * t704
  t1142 = t465 * t151
  t1180 = -0.6e1 * t616 * t589 + 0.2e1 * t303 * t157 * t562 * t328 * t169 + 0.12e2 * t493 * t70 * t151 * t292 + 0.12e2 * t613 * t567 - 0.2e1 * t303 * t306 * (0.24e2 * t715 * t464 * t221 + 0.48e2 * t148 * t312 * t464 * t575 + 0.36e2 * t570 * t221 * t379 + 0.160e3 / 0.3e1 * t307 * t581 * t221 * t901 * t596 + 0.16e2 * t573 * t379 * t575 - 0.176e3 / 0.3e1 * t574 * t73 * t919 + 0.4e1 * t308 * t704 + 0.160e3 / 0.9e1 * t152 / t153 / t295 * t720 - 0.440e3 / 0.9e1 * t583 * t725 + 0.616e3 / 0.27e2 * t314 * t702) + 0.12e2 * t616 * t609 - 0.12e2 * t1142 * t318 + 0.12e2 * t1142 * t330 + 0.616e3 / 0.27e2 * t298 * t299 * t702 + 0.8e1 * t465 * t297 * t300 - 0.44e2 / 0.3e1 * t556 * t559 - 0.88e2 / 0.3e1 * t551 * t552 * t725 + 0.8e1 * t286 * t550 * t553 + 0.4e1 * t494 * t297 * t300 - 0.8e1 * t149 * t361 * t328 * t537 * params.eta * t213 - 0.16e2 * t289 * t362 * t542 * params.eta * t213 + 0.16e2 * t289 * t369 * t546 * params.eta * t213
  t1200 = 0.1e1 / t4 / t27
  t1207 = t178 * s0
  t1231 = -0.5e1 / 0.36e2 * t18 * t666 * t189 + t18 * t22 * t333 * t189 / 0.4e1 - 0.11819983333333333333333333333333333333333333333333e2 * t342 * t17 * t674 * t173 * t352 - 0.3e1 / 0.8e1 * t18 * t193 * t622 * t189 + 0.12369750000000000000000000000000000000000000000000e2 * t342 * t344 * t333 * t352 + 0.17812440000000000000000000000000000000000000000000e3 * t342 * t17 * t39 * t173 * t646 - 0.81605714700000000000000000000000000000000000000000e1 * t651 * t694 * t660 - 0.3e1 / 0.8e1 * t18 * t19 * (t926 + t993 + t1090 + t1180) * t189 - 0.74218500000000000000000000000000000000000000000000e1 * t342 * t628 * t622 * t352 - 0.89062200000000000000000000000000000000000000000000e2 * t342 * t635 * t333 * t646 + 0.12240857205000000000000000000000000000000000000000e2 * t651 * t653 * t333 * t660 - 0.16493000000000000000000000000000000000000000000000e2 * t341 * t1200 * t17 / t20 / t279 * t173 / t184 * t27 / t674 * t188 + 0.81605714699999999999999999999999999999999999999999e1 * t3 * t1200 * t694 * t25 * t29 * t656 * t55 * t188 - 0.32302153261130400000000000000000000000000000000000e3 * t342 * t17 * t666 * t348 * t188
  t1232 = f.my_piecewise3(t2, 0, t1231)
  v3rho3_0_ = 0.2e1 * r0 * t1232 + 0.6e1 * t664

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 * t5 * t17
  t19 = r0 ** 2
  t20 = r0 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t23 = 0.1e1 / t21 / t19
  t25 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 * t28
  t31 = 0.1e1 / t30
  t32 = t27 * t31
  t33 = s0 ** 2
  t34 = t32 * t33
  t35 = 2 ** (0.1e1 / 0.3e1)
  t36 = t19 ** 2
  t37 = t36 * r0
  t39 = 0.1e1 / t20 / t37
  t40 = t35 * t39
  t41 = params.dp2 ** 2
  t42 = t41 ** 2
  t43 = 0.1e1 / t42
  t47 = jnp.exp(-t34 * t40 * t43 / 0.288e3)
  t52 = t29 ** 2
  t53 = 0.1e1 / t52
  t54 = (-0.162742215233874e0 * t25 * t47 + 0.10e2 / 0.81e2) * t26 * t53
  t55 = t35 ** 2
  t56 = s0 * t55
  t57 = t56 * t23
  t60 = params.k1 + t54 * t57 / 0.24e2
  t64 = params.k1 * (0.1e1 - params.k1 / t60)
  t65 = tau0 * t55
  t67 = 0.1e1 / t21 / r0
  t70 = t65 * t67 - t57 / 0.8e1
  t73 = params.eta * s0
  t77 = 0.3e1 / 0.10e2 * t27 * t52 + t73 * t55 * t23 / 0.8e1
  t78 = 0.1e1 / t77
  t79 = t70 * t78
  t80 = t79 <= 0.0e0
  t81 = 0.0e0 < t79
  t82 = f.my_piecewise3(t81, 0, t79)
  t83 = params.c1 * t82
  t84 = 0.1e1 - t82
  t85 = 0.1e1 / t84
  t87 = jnp.exp(-t83 * t85)
  t88 = t79 <= 0.25e1
  t89 = 0.25e1 < t79
  t90 = f.my_piecewise3(t89, 0.25e1, t79)
  t92 = t90 ** 2
  t94 = t92 * t90
  t96 = t92 ** 2
  t98 = t96 * t90
  t100 = t96 * t92
  t105 = f.my_piecewise3(t89, t79, 0.25e1)
  t106 = 0.1e1 - t105
  t109 = jnp.exp(params.c2 / t106)
  t111 = f.my_piecewise5(t80, t87, t88, 0.1e1 - 0.667e0 * t90 - 0.4445555e0 * t92 - 0.663086601049e0 * t94 + 0.1451297044490e1 * t96 - 0.887998041597e0 * t98 + 0.234528941479e0 * t100 - 0.23185843322e-1 * t96 * t94, -params.d * t109)
  t112 = 0.174e0 - t64
  t116 = t25 * t26 * t53
  t119 = 0.1e1 - t79
  t120 = t119 ** 2
  t125 = (0.40570770199022687796862290864197530864197530864200e-1 - 0.30235468026081006356817095666666666666666666666667e0 * params.eta) * t26 * t53
  t132 = (0.3e1 / 0.4e1 * params.eta + 0.2e1 / 0.3e1) ** 2
  t137 = (0.290700106132790123456790123456790123456790123457e-2 - 0.27123702538979000000000000000000000000000000000000e0 * params.eta) ** 2
  t142 = (0.146e3 / 0.2025e4 * t132 - 0.73e2 / 0.540e3 * params.eta - 0.146e3 / 0.1215e4 + t137 / params.k1) * t27 * t31
  t143 = t33 * t35
  t144 = t143 * t39
  t147 = -0.162742215233874e0 + 0.162742215233874e0 * t79 + 0.67809256347447500000000000000000000000000000000000e-2 * t116 * t57 - 0.59353125082804000000000000000000000000000000000000e-1 * t120 + t125 * t56 * t23 * t119 / 0.24e2 + t142 * t144 / 0.288e3
  t148 = t70 ** 2
  t149 = t147 * t148
  t150 = t77 ** 2
  t151 = 0.1e1 / t150
  t152 = t148 ** 2
  t153 = t150 ** 2
  t154 = 0.1e1 / t153
  t156 = t152 * t154 + 0.1e1
  t157 = 0.1e1 / t156
  t158 = t151 * t157
  t159 = params.da4 ** 2
  t160 = 0.1e1 / t159
  t162 = params.dp4 ** 2
  t163 = t162 ** 2
  t164 = 0.1e1 / t163
  t169 = jnp.exp(-t120 * t160 - t34 * t40 * t164 / 0.288e3)
  t170 = t158 * t169
  t173 = t111 * t112 + 0.2e1 * t149 * t170 + t64 + 0.1e1
  t174 = t23 * t173
  t175 = jnp.sqrt(0.3e1)
  t176 = 0.1e1 / t29
  t177 = t27 * t176
  t178 = jnp.sqrt(s0)
  t179 = t178 * t35
  t181 = 0.1e1 / t20 / r0
  t183 = t177 * t179 * t181
  t184 = jnp.sqrt(t183)
  t188 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t175 / t184)
  t189 = 0.1e1 - t188
  t193 = params.k1 ** 2
  t194 = t60 ** 2
  t195 = 0.1e1 / t194
  t196 = t193 * t195
  t197 = t28 ** 2
  t199 = t25 / t197
  t200 = t33 * s0
  t201 = t199 * t200
  t202 = t36 ** 2
  t203 = t202 * r0
  t204 = 0.1e1 / t203
  t209 = t19 * r0
  t211 = 0.1e1 / t21 / t209
  t212 = t56 * t211
  t215 = -0.15068723632766111111111111111111111111111111111111e-2 * t201 * t204 * t43 * t47 - t54 * t212 / 0.9e1
  t220 = -0.5e1 / 0.3e1 * t65 * t23 + t212 / 0.3e1
  t221 = t220 * t78
  t223 = t70 * t151 * params.eta
  t224 = t223 * t212
  t226 = t221 + t224 / 0.3e1
  t227 = f.my_piecewise3(t81, 0, t226)
  t230 = t84 ** 2
  t231 = 0.1e1 / t230
  t232 = t231 * t227
  t234 = -params.c1 * t227 * t85 - t83 * t232
  t236 = f.my_piecewise3(t89, 0, t226)
  t238 = t90 * t236
  t240 = t92 * t236
  t242 = t94 * t236
  t244 = t96 * t236
  t246 = t98 * t236
  t251 = params.d * params.c2
  t252 = t106 ** 2
  t253 = 0.1e1 / t252
  t254 = f.my_piecewise3(t89, t226, 0)
  t258 = f.my_piecewise5(t80, t234 * t87, t88, -0.667e0 * t236 - 0.8891110e0 * t238 - 0.1989259803147e1 * t240 + 0.5805188177960e1 * t242 - 0.4439990207985e1 * t244 + 0.1407173648874e1 * t246 - 0.162300903254e0 * t100 * t236, -t251 * t253 * t254 * t109)
  t260 = t111 * t193
  t261 = t195 * t215
  t267 = -t226
  t278 = t36 * t19
  t280 = 0.1e1 / t20 / t278
  t284 = 0.162742215233874e0 * t221 + 0.54247405077958000000000000000000000000000000000000e-1 * t224 - 0.18082468359319333333333333333333333333333333333333e-1 * t116 * t212 - 0.11870625016560800000000000000000000000000000000000e0 * t119 * t267 - t125 * t56 * t211 * t119 / 0.9e1 + t125 * t56 * t23 * t267 / 0.24e2 - t142 * t143 * t280 / 0.54e2
  t285 = t284 * t148
  t288 = t147 * t70
  t289 = t288 * t151
  t290 = t157 * t169
  t291 = t290 * t220
  t294 = t150 * t77
  t295 = 0.1e1 / t294
  t296 = t295 * t157
  t297 = t149 * t296
  t298 = t169 * params.eta
  t299 = t298 * t212
  t302 = t149 * t151
  t303 = t156 ** 2
  t304 = 0.1e1 / t303
  t305 = t304 * t169
  t306 = t148 * t70
  t307 = t306 * t154
  t311 = 0.1e1 / t153 / t77
  t313 = t152 * t311 * params.eta
  t316 = 0.4e1 * t307 * t220 + 0.4e1 / 0.3e1 * t313 * t212
  t317 = t305 * t316
  t320 = t119 * t160
  t327 = -0.2e1 * t320 * t267 + t34 * t35 * t280 * t164 / 0.54e2
  t328 = t157 * t327
  t329 = t328 * t169
  t332 = t196 * t215 + t258 * t112 - t260 * t261 + 0.2e1 * t285 * t170 + 0.4e1 * t289 * t291 + 0.4e1 / 0.3e1 * t297 * t299 - 0.2e1 * t302 * t317 + 0.2e1 * t302 * t329
  t337 = 3 ** (0.1e1 / 0.6e1)
  t338 = t337 ** 2
  t339 = t338 ** 2
  t340 = t339 * t337
  t341 = t340 * t5
  t342 = 0.1e1 / t36
  t343 = t17 * t342
  t347 = 0.1e1 / t184 / t183
  t351 = t347 * t27 * t176 * t179 * t188
  t354 = 0.1e1 / t21
  t356 = 0.1e1 / t21 / t36
  t357 = t56 * t356
  t358 = t298 * t357
  t361 = t154 * t157
  t362 = t149 * t361
  t363 = params.eta ** 2
  t364 = t169 * t363
  t365 = t36 * t209
  t367 = 0.1e1 / t20 / t365
  t368 = t143 * t367
  t369 = t364 * t368
  t372 = t285 * t296
  t375 = t220 ** 2
  t376 = t147 * t375
  t382 = 0.40e2 / 0.9e1 * t65 * t211 - 0.11e2 / 0.9e1 * t357
  t383 = t382 * t78
  t386 = t220 * t151 * params.eta
  t387 = t386 * t212
  t390 = t70 * t295 * t363
  t391 = t390 * t368
  t393 = t223 * t357
  t397 = t267 ** 2
  t402 = -t383 - 0.2e1 / 0.3e1 * t387 - 0.4e1 / 0.9e1 * t391 + 0.11e2 / 0.9e1 * t393
  t419 = 0.162742215233874e0 * t383 + 0.10849481015591600000000000000000000000000000000000e0 * t387 + 0.72329873437277333333333333333333333333333333333333e-1 * t391 - 0.19890715195251266666666666666666666666666666666667e0 * t393 + 0.66302383984170888888888888888888888888888888888888e-1 * t116 * t357 - 0.11870625016560800000000000000000000000000000000000e0 * t397 - 0.11870625016560800000000000000000000000000000000000e0 * t119 * t402 + 0.11e2 / 0.27e2 * t125 * t56 * t356 * t119 - 0.2e1 / 0.9e1 * t125 * t56 * t211 * t267 + t125 * t56 * t23 * t402 / 0.24e2 + 0.19e2 / 0.162e3 * t142 * t368
  t420 = t419 * t148
  t423 = t327 ** 2
  t424 = t157 * t423
  t425 = t424 * t169
  t428 = t290 * t382
  t431 = t148 * t154
  t434 = t306 * t311
  t435 = t434 * t220
  t436 = t55 * t211
  t437 = t73 * t436
  t443 = 0.1e1 / t153 / t150
  t445 = t152 * t443 * t363
  t450 = 0.12e2 * t431 * t375 + 0.32e2 / 0.3e1 * t435 * t437 + 0.4e1 * t307 * t382 + 0.40e2 / 0.9e1 * t445 * t368 - 0.44e2 / 0.9e1 * t313 * t357
  t451 = t305 * t450
  t454 = t220 * t316
  t455 = t305 * t454
  t458 = t169 * t220
  t459 = t328 * t458
  t462 = t304 * t327
  t463 = t169 * t316
  t464 = t462 * t463
  t467 = t285 * t151
  t470 = -0.44e2 / 0.9e1 * t297 * t358 + 0.8e1 / 0.3e1 * t362 * t369 + 0.8e1 / 0.3e1 * t372 * t299 + 0.4e1 * t376 * t170 + 0.2e1 * t420 * t170 + 0.2e1 * t302 * t425 + 0.4e1 * t289 * t428 - 0.2e1 * t302 * t451 - 0.8e1 * t289 * t455 + 0.8e1 * t289 * t459 - 0.4e1 * t302 * t464 + 0.4e1 * t467 * t329
  t471 = t284 * t70
  t472 = t471 * t151
  t476 = 0.1e1 / t303 / t156
  t477 = t476 * t169
  t478 = t316 ** 2
  t479 = t477 * t478
  t486 = t35 * t367
  t490 = -0.2e1 * t397 * t160 - 0.2e1 * t320 * t402 - 0.19e2 / 0.162e3 * t34 * t486 * t164
  t491 = t157 * t490
  t492 = t491 * t169
  t497 = t296 * t327
  t498 = t149 * t497
  t501 = t296 * t169
  t502 = t288 * t501
  t503 = t220 * params.eta
  t504 = t503 * t212
  t507 = t295 * t304
  t508 = t507 * t169
  t509 = t149 * t508
  t510 = t436 * t316
  t511 = t73 * t510
  t514 = t258 * t193
  t523 = t33 ** 2
  t524 = t523 * s0
  t530 = t42 ** 2
  t535 = 0.1e1 / t530 * t27 * t31 * t35 * t47
  t540 = 0.17580177571560462962962962962962962962962962962963e-1 * t201 / t202 / t19 * t43 * t47 - 0.27905043764381687242798353909465020576131687242798e-4 * t199 * t524 / t20 / t202 / t365 * t535 + 0.11e2 / 0.27e2 * t54 * t357
  t541 = t195 * t540
  t545 = 0.1e1 / t194 / t60
  t546 = t193 * t545
  t547 = t215 ** 2
  t550 = t545 * t547
  t553 = -t402
  t554 = f.my_piecewise3(t81, 0, t553)
  t555 = params.c1 * t554
  t557 = t227 ** 2
  t562 = 0.1e1 / t230 / t84
  t563 = t562 * t557
  t568 = -t83 * t231 * t554 - 0.2e1 * params.c1 * t557 * t231 - t555 * t85 - 0.2e1 * t83 * t563
  t570 = t234 ** 2
  t573 = f.my_piecewise3(t89, 0, t553)
  t575 = t236 ** 2
  t579 = t90 * t575
  t583 = t92 * t575
  t587 = t94 * t575
  t591 = t96 * t575
  t599 = -0.667e0 * t573 - 0.8891110e0 * t575 - 0.8891110e0 * t90 * t573 - 0.3978519606294e1 * t579 - 0.1989259803147e1 * t92 * t573 + 0.17415564533880e2 * t583 + 0.5805188177960e1 * t94 * t573 - 0.17759960831940e2 * t587 - 0.4439990207985e1 * t96 * t573 + 0.7035868244370e1 * t591 + 0.1407173648874e1 * t98 * t573 - 0.973805419524e0 * t98 * t575 - 0.162300903254e0 * t100 * t573
  t600 = t252 * t106
  t601 = 0.1e1 / t600
  t602 = t254 ** 2
  t607 = f.my_piecewise3(t89, t553, 0)
  t611 = params.c2 ** 2
  t612 = params.d * t611
  t613 = t252 ** 2
  t614 = 0.1e1 / t613
  t619 = f.my_piecewise5(t80, t568 * t87 + t570 * t87, t88, t599, -t251 * t253 * t607 * t109 - 0.2e1 * t251 * t601 * t602 * t109 - t612 * t614 * t602 * t109)
  t621 = 0.8e1 * t472 * t291 + 0.4e1 * t302 * t479 + 0.2e1 * t302 * t492 - 0.4e1 * t467 * t317 + 0.8e1 / 0.3e1 * t498 * t299 + 0.16e2 / 0.3e1 * t502 * t504 - 0.8e1 / 0.3e1 * t509 * t511 - 0.2e1 * t514 * t261 - t260 * t541 + t196 * t540 - 0.2e1 * t546 * t547 + 0.2e1 * t260 * t550 + t619 * t112
  t622 = t470 + t621
  t628 = t17 / t209
  t633 = t17 * t39
  t640 = 0.1e1 / t184 / t26 / t53 / t57 / 0.6e1
  t644 = t640 * t26 * t53 * t56 * t188
  t647 = t4 ** 2
  t649 = t3 * t647 * jnp.pi
  t650 = t17 * t181
  t651 = t650 * t173
  t653 = 0.1e1 / t178
  t657 = t653 * t26 * t53 * t55 * t188
  t661 = 0.1e1 / t20 / t202
  t662 = t143 * t661
  t663 = t364 * t662
  t667 = 0.1e1 / t21 / t37
  t668 = t56 * t667
  t669 = t298 * t668
  t672 = t376 * t296
  t677 = t285 * t361
  t680 = t420 * t296
  t686 = -0.440e3 / 0.27e2 * t65 * t356 + 0.154e3 / 0.27e2 * t668
  t687 = t686 * t78
  t689 = t382 * t151 * params.eta
  t690 = t689 * t212
  t692 = t220 * t295 * t363
  t693 = t692 * t368
  t695 = t386 * t357
  t697 = t70 * t154
  t698 = t363 * params.eta
  t699 = t698 * t200
  t701 = 0.1e1 / t202 / t209
  t702 = t699 * t701
  t703 = t697 * t702
  t705 = t390 * t662
  t707 = t223 * t668
  t709 = t687 + t690 + 0.4e1 / 0.3e1 * t693 - 0.11e2 / 0.3e1 * t695 + 0.8e1 / 0.9e1 * t703 - 0.44e2 / 0.9e1 * t705 + 0.154e3 / 0.27e2 * t707
  t710 = f.my_piecewise3(t81, 0, t709)
  t711 = params.c1 * t710
  t715 = t557 * t227
  t719 = t230 ** 2
  t720 = 0.1e1 / t719
  t724 = t562 * t227
  t730 = -t83 * t231 * t710 - 0.6e1 * t83 * t724 * t554 - 0.6e1 * params.c1 * t715 * t562 - 0.6e1 * t83 * t720 * t715 - 0.6e1 * t555 * t232 - t711 * t85
  t738 = f.my_piecewise3(t89, 0, t709)
  t744 = t575 * t236
  t774 = -0.667e0 * t738 - 0.26673330e1 * t236 * t573 - 0.8891110e0 * t90 * t738 - 0.3978519606294e1 * t744 - 0.11935558818882e2 * t238 * t573 - 0.1989259803147e1 * t92 * t738 + 0.34831129067760e2 * t90 * t744 + 0.52246693601640e2 * t240 * t573 + 0.5805188177960e1 * t94 * t738 - 0.53279882495820e2 * t92 * t744 - 0.53279882495820e2 * t242 * t573 - 0.4439990207985e1 * t96 * t738 + 0.28143472977480e2 * t94 * t744 + 0.21107604733110e2 * t244 * t573 + 0.1407173648874e1 * t98 * t738 - 0.4869027097620e1 * t96 * t744 - 0.2921416258572e1 * t246 * t573 - 0.162300903254e0 * t100 * t738
  t775 = t602 * t254
  t780 = t251 * t601
  t781 = t254 * t109
  t782 = t781 * t607
  t786 = 0.1e1 / t613 / t106
  t791 = f.my_piecewise3(t89, t709, 0)
  t795 = t612 * t614
  t799 = params.d * t611 * params.c2
  t801 = 0.1e1 / t613 / t252
  t806 = f.my_piecewise5(t80, 0.3e1 * t568 * t234 * t87 + t570 * t234 * t87 + t730 * t87, t88, t774, -t251 * t253 * t791 * t109 - 0.6e1 * t251 * t614 * t775 * t109 - 0.6e1 * t612 * t786 * t775 * t109 - t799 * t801 * t775 * t109 - 0.6e1 * t780 * t782 - 0.3e1 * t795 * t782)
  t810 = t194 ** 2
  t811 = 0.1e1 / t810
  t812 = t547 * t215
  t813 = t811 * t812
  t816 = t619 * t193
  t823 = t304 * t490
  t824 = t823 * t463
  t827 = t169 * t450
  t828 = t462 * t827
  t833 = t295 * t476
  t834 = t833 * t169
  t835 = t149 * t834
  t836 = t478 * params.eta
  t837 = t836 * t212
  t840 = t285 * t508
  t843 = -0.88e2 / 0.3e1 * t362 * t663 + 0.616e3 / 0.27e2 * t297 * t669 + 0.8e1 * t672 * t299 - 0.44e2 / 0.3e1 * t372 * t358 + 0.8e1 * t677 * t369 + 0.4e1 * t680 * t299 + t806 * t112 + 0.6e1 * t514 * t550 - 0.6e1 * t260 * t813 - 0.3e1 * t816 * t261 - 0.24e2 * t472 * t455 + 0.24e2 * t472 * t459 - 0.6e1 * t302 * t824 - 0.6e1 * t302 * t828 - 0.12e2 * t467 * t464 + 0.8e1 * t835 * t837 - 0.8e1 * t840 * t511
  t844 = t471 * t501
  t847 = t285 * t497
  t850 = t361 * t169
  t851 = t288 * t850
  t852 = t220 * t363
  t853 = t852 * t368
  t856 = t154 * t304
  t857 = t856 * t169
  t858 = t149 * t857
  t859 = t363 * t33
  t860 = t486 * t316
  t861 = t859 * t860
  t864 = t296 * t423
  t865 = t149 * t864
  t868 = t503 * t357
  t871 = t55 * t356
  t872 = t871 * t316
  t873 = t73 * t872
  t878 = t361 * t327
  t879 = t149 * t878
  t882 = t382 * params.eta
  t883 = t882 * t212
  t886 = t450 * params.eta
  t887 = t886 * t212
  t890 = t296 * t490
  t891 = t149 * t890
  t902 = t419 * t70
  t903 = t902 * t151
  t906 = 0.16e2 * t844 * t504 + 0.8e1 * t847 * t299 + 0.16e2 * t851 * t853 - 0.8e1 * t858 * t861 + 0.4e1 * t865 * t299 - 0.88e2 / 0.3e1 * t502 * t868 + 0.44e2 / 0.3e1 * t509 * t873 - 0.44e2 / 0.3e1 * t498 * t358 + 0.8e1 * t879 * t369 + 0.8e1 * t502 * t883 - 0.4e1 * t509 * t887 + 0.4e1 * t891 * t299 + 0.6e1 * t467 * t492 + 0.12e2 * t467 * t479 - 0.6e1 * t467 * t451 + 0.6e1 * t467 * t425 + 0.12e2 * t903 * t291
  t910 = t420 * t151
  t913 = t267 * t160
  t916 = -t709
  t919 = t35 * t661
  t923 = -0.6e1 * t913 * t402 - 0.2e1 * t320 * t916 + 0.209e3 / 0.243e3 * t34 * t919 * t164
  t924 = t157 * t923
  t925 = t924 * t169
  t928 = t375 * t220
  t931 = t148 * t311
  t932 = t931 * t375
  t938 = t306 * t443
  t939 = t938 * t220
  t940 = t859 * t486
  t943 = t434 * t382
  t946 = t73 * t871
  t952 = 0.1e1 / t153 / t294
  t953 = t152 * t952
  t960 = 0.24e2 * t697 * t928 + 0.48e2 * t932 * t437 + 0.36e2 * t431 * t220 * t382 + 0.160e3 / 0.3e1 * t939 * t940 + 0.16e2 * t943 * t437 - 0.176e3 / 0.3e1 * t435 * t946 + 0.4e1 * t307 * t686 + 0.160e3 / 0.9e1 * t953 * t702 - 0.440e3 / 0.9e1 * t445 * t662 + 0.616e3 / 0.27e2 * t313 * t668
  t961 = t305 * t960
  t964 = t376 * t151
  t969 = t382 * t316
  t970 = t305 * t969
  t973 = t220 * t450
  t974 = t305 * t973
  t977 = t169 * t490
  t978 = t328 * t977
  t981 = t220 * t478
  t982 = t477 * t981
  t985 = t147 * t220
  t986 = t985 * t151
  t989 = t290 * t686
  t992 = t303 ** 2
  t993 = 0.1e1 / t992
  t994 = t993 * t169
  t995 = t478 * t316
  t996 = t994 * t995
  t999 = t423 * t327
  t1000 = t157 * t999
  t1001 = t1000 * t169
  t1008 = t507 * t327
  t1009 = t149 * t1008
  t1011 = t463 * params.eta * t212
  t1014 = 0.2e1 * t302 * t1001 - 0.8e1 * t1009 * t1011 - 0.12e2 * t289 * t970 - 0.12e2 * t289 * t974 + 0.24e2 * t289 * t982 + 0.4e1 * t289 * t989 + 0.2e1 * t302 * t925 - 0.2e1 * t302 * t961 + 0.6e1 * t302 * t978 - 0.12e2 * t302 * t996 - 0.6e1 * t910 * t317 - 0.12e2 * t964 * t317 + 0.6e1 * t910 * t329 + 0.12e2 * t964 * t329 + 0.12e2 * t472 * t428 + 0.12e2 * t986 * t428 - 0.3e1 * t514 * t541
  t1015 = t288 * t508
  t1017 = t454 * params.eta * t212
  t1020 = t288 * t497
  t1021 = t458 * params.eta
  t1022 = t1021 * t212
  t1029 = t202 ** 2
  t1036 = t523 * t200
  t1049 = 0.1e1 / t530 / t42 * t26 / t52 / t197 * t55 * t47
  t1054 = -0.19053563882319816049382716049382716049382716049383e0 * t201 * t701 * t43 * t47 + 0.75343618163830555555555555555555555555555555555555e-3 * t199 * t524 / t20 / t1029 * t535 - 0.31005604182646319158664837677183356195701874714220e-5 * t199 * t1036 / t21 / t1029 / t37 * t1049 - 0.154e3 / 0.81e2 * t54 * t668
  t1055 = t195 * t1054
  t1060 = t424 * t458
  t1064 = t169 * t478
  t1065 = t476 * t327 * t1064
  t1068 = t304 * t423
  t1069 = t1068 * t463
  t1072 = t193 * t811
  t1107 = 0.162742215233874e0 * t687 + 0.16274221523387400000000000000000000000000000000000e0 * t690 + 0.21698962031183200000000000000000000000000000000000e0 * t693 - 0.59672145585753800000000000000000000000000000000000e0 * t695 + 0.14465974687455466666666666666666666666666666666667e0 * t703 - 0.79562860781005066666666666666666666666666666666667e0 * t705 + 0.92823337577839244444444444444444444444444444444446e0 * t707 - 0.30941112525946414814814814814814814814814814814814e0 * t116 * t668 - 0.35611875049682400000000000000000000000000000000000e0 * t267 * t402 - 0.11870625016560800000000000000000000000000000000000e0 * t119 * t916 - 0.154e3 / 0.81e2 * t125 * t56 * t667 * t119 + 0.11e2 / 0.9e1 * t125 * t56 * t356 * t267 - t125 * t56 * t211 * t402 / 0.3e1 + t125 * t56 * t23 * t916 / 0.24e2 - 0.209e3 / 0.243e3 * t142 * t662
  t1108 = t1107 * t148
  t1112 = t545 * t540 * t215
  t1115 = t491 * t458
  t1118 = t169 * t382
  t1119 = t328 * t1118
  t1122 = t450 * t316
  t1123 = t477 * t1122
  t1126 = t284 * t375
  t1129 = t311 * t157
  t1130 = t149 * t1129
  t1131 = t169 * t698
  t1132 = t200 * t701
  t1133 = t1131 * t1132
  t1136 = t151 * t304
  t1137 = t288 * t1136
  t1138 = t327 * t169
  t1139 = t1138 * t454
  t1142 = -0.16e2 * t1015 * t1017 + 0.16e2 * t1020 * t1022 - t260 * t1055 - 0.6e1 * t546 * t540 * t215 + 0.12e2 * t289 * t1060 + 0.12e2 * t302 * t1065 - 0.6e1 * t302 * t1069 + 0.6e1 * t1072 * t812 + t196 * t1054 + 0.2e1 * t1108 * t170 + 0.6e1 * t260 * t1112 + 0.12e2 * t289 * t1115 + 0.12e2 * t289 * t1119 + 0.12e2 * t302 * t1123 + 0.12e2 * t1126 * t170 + 0.64e2 / 0.9e1 * t1130 * t1133 - 0.24e2 * t1137 * t1139
  t1144 = t843 + t906 + t1014 + t1142
  t1150 = t17 / t19
  t1157 = t17 / t20 / t36
  t1163 = t17 / t20
  t1169 = 0.1e1 / t4 / t28
  t1170 = t340 * t1169
  t1172 = 0.1e1 / t21 / t278
  t1174 = t1170 * t17 * t1172
  t1176 = t178 * s0
  t1181 = 0.1e1 / t184 * t28 / t1176 / t342 / 0.72e2
  t1183 = t1176 * t188
  t1184 = t173 * t1181 * t1183
  t1187 = t3 * t1169
  t1192 = t26 * t30 * t653 * t55 * t188
  t1195 = t341 * t17
  t1196 = t347 * t188
  t1200 = -0.5e1 / 0.36e2 * t18 * t174 * t189 + t18 * t67 * t332 * t189 / 0.4e1 - 0.11819983333333333333333333333333333333333333333333e2 * t341 * t343 * t173 * t351 - 0.3e1 / 0.8e1 * t18 * t354 * t622 * t189 + 0.12369750000000000000000000000000000000000000000000e2 * t341 * t628 * t332 * t351 + 0.17812440000000000000000000000000000000000000000000e3 * t341 * t633 * t173 * t644 - 0.81605714700000000000000000000000000000000000000000e1 * t649 * t651 * t657 - 0.3e1 / 0.8e1 * t18 * t20 * t1144 * t189 - 0.74218500000000000000000000000000000000000000000000e1 * t341 * t1150 * t622 * t351 - 0.89062200000000000000000000000000000000000000000000e2 * t341 * t1157 * t332 * t644 + 0.12240857205000000000000000000000000000000000000000e2 * t649 * t1163 * t332 * t657 - 0.11874960000000000000000000000000000000000000000000e4 * t1174 * t1184 + 0.81605714699999999999999999999999999999999999999999e1 * t1187 * t651 * t1192 - 0.32302153261130400000000000000000000000000000000000e3 * t1195 * t174 * t1196
  t1201 = f.my_piecewise3(t2, 0, t1200)
  t1214 = t650 * t332
  t1276 = t540 ** 2
  t1288 = 0.48e2 * t288 * t158 * t1138 * t220 * t490 - 0.48e2 * t1137 * t423 * t169 * t454 - 0.16e2 * t289 * t305 * t960 * t220 + 0.24e2 * t419 * t375 * t170 + 0.48e2 * t472 * t1060 + 0.48e2 * t467 * t1065 + 0.48e2 * t467 * t1123 - 0.6e1 * t546 * t1276 - 0.24e2 * t910 * t464 + 0.24e2 * t467 * t978 + 0.96e2 * t472 * t982
  t1290 = t151 * t476
  t1291 = t288 * t1290
  t1319 = t202 * t36
  t1320 = 0.1e1 / t1319
  t1332 = 0.96e2 * t1291 * t458 * t1122 + 0.96e2 * t1291 * t1138 * t981 - 0.48e2 * t1137 * t1138 * t969 + 0.48e2 * t149 * t1290 * t1138 * t1122 - 0.96e2 * t471 * t1136 * t1139 - 0.48e2 * t1137 * t977 * t454 - 0.24e2 * t149 * t1136 * t490 * t327 * t463 - 0.48e2 * t1137 * t1138 * t973 - 0.1408e4 / 0.9e1 * t1130 * t1131 * t200 * t1320 + 0.256e3 / 0.9e1 * t285 * t1129 * t1133 - 0.96e2 * t289 * t994 * t995 * t220
  t1344 = t402 ** 2
  t1351 = t56 * t1172
  t1353 = 0.6160e4 / 0.81e2 * t65 * t667 - 0.2618e4 / 0.81e2 * t1351
  t1354 = t1353 * t78
  t1357 = t686 * t151 * params.eta * t212
  t1361 = t382 * t295 * t363 * t368
  t1363 = t689 * t357
  t1366 = t220 * t154 * t702
  t1368 = t692 * t662
  t1370 = t386 * t668
  t1372 = t70 * t311
  t1373 = t363 ** 2
  t1379 = t523 / t21 / t202 / t278 * t55
  t1380 = t1372 * t1373 * t1379
  t1382 = t699 * t1320
  t1383 = t697 * t1382
  t1386 = 0.1e1 / t20 / t203
  t1387 = t143 * t1386
  t1388 = t390 * t1387
  t1390 = t223 * t1351
  t1392 = -t1354 - 0.4e1 / 0.3e1 * t1357 - 0.8e1 / 0.3e1 * t1361 + 0.22e2 / 0.3e1 * t1363 - 0.32e2 / 0.9e1 * t1366 + 0.176e3 / 0.9e1 * t1368 - 0.616e3 / 0.27e2 * t1370 - 0.32e2 / 0.27e2 * t1380 + 0.176e3 / 0.9e1 * t1383 - 0.3916e4 / 0.81e2 * t1388 + 0.2618e4 / 0.81e2 * t1390
  t1409 = t478 ** 2
  t1413 = t423 ** 2
  t1426 = -0.72e2 * t302 * t994 * t478 * t450 + 0.24e2 * t302 * t476 * t490 * t1064 + 0.24e2 * t289 * t491 * t1118 + 0.2e1 * t302 * t157 * (-0.6e1 * t1344 * t160 - 0.8e1 * t913 * t916 - 0.2e1 * t320 * t1392 - 0.5225e4 / 0.729e3 * t34 * t35 * t1386 * t164) * t169 + 0.8e1 * t467 * t1001 + 0.48e2 * t302 / t992 / t156 * t169 * t1409 + 0.2e1 * t302 * t157 * t1413 * t169 - 0.12e2 * t910 * t451 + 0.12e2 * t910 * t425 + 0.8e1 * t467 * t925 + 0.48e2 * t964 * t479
  t1434 = t490 ** 2
  t1445 = t450 ** 2
  t1451 = t1126 * t151
  t1460 = 0.16e2 * t1107 * t70 * t151 * t291 + 0.6e1 * t302 * t157 * t1434 * t169 + 0.12e2 * t302 * t477 * t1445 - 0.4e1 * t806 * t193 * t261 + 0.48e2 * t472 * t1119 + 0.48e2 * t1451 * t329 + 0.24e2 * t964 * t425 + 0.24e2 * t903 * t428 - 0.48e2 * t903 * t455 + 0.48e2 * t903 * t459 + 0.24e2 * t964 * t492
  t1506 = -0.47482500066243200000000000000000000000000000000000e0 * t267 * t916 - 0.11870625016560800000000000000000000000000000000000e0 * t119 * t1392 + t125 * t56 * t23 * t1392 / 0.24e2 - 0.616e3 / 0.81e2 * t125 * t56 * t667 * t267 + 0.22e2 / 0.9e1 * t125 * t56 * t356 * t402 - 0.4e1 / 0.9e1 * t125 * t56 * t211 * t916 + 0.21698962031183200000000000000000000000000000000000e0 * t1357 + 0.43397924062366400000000000000000000000000000000000e0 * t1361 - 0.31825144312402026666666666666666666666666666666667e1 * t1383 + 0.19287966249940622222222222222222222222222222222223e0 * t1380 + 0.57863898749821866666666666666666666666666666666667e0 * t1366
  t1511 = t382 ** 2
  t1538 = 0.16e2 * t302 * t477 * t960 * t316 + 0.2e1 * (-0.11934429117150760000000000000000000000000000000000e1 * t1363 - 0.31825144312402026666666666666666666666666666666667e1 * t1368 + 0.37129335031135697777777777777777777777777777777778e1 * t1370 + 0.78678828994549454814814814814814814814814814814815e1 * t1388 - 0.52599891294108905185185185185185185185185185185186e1 * t1390 + 0.17533297098036301728395061728395061728395061728395e1 * t116 * t1351 + 0.5225e4 / 0.729e3 * t142 * t1387 + 0.2618e4 / 0.243e3 * t125 * t56 * t1172 * t119 + 0.162742215233874e0 * t1354 - 0.35611875049682400000000000000000000000000000000000e0 * t1344 + t1506) * t148 * t170 + 0.12e2 * t147 * t1511 * t170 - 0.36e2 * t260 * t811 * t547 * t540 + 0.24e2 * t514 * t1112 + 0.8e1 * t260 * t545 * t1054 * t215 + 0.48e2 * t284 * t220 * t151 * t428 + 0.16e2 * t472 * t989 - 0.24e2 * t964 * t451 + 0.16e2 * t986 * t989 + 0.4e1 * t289 * t290 * t1353
  t1579 = 0.12e2 * t816 * t550 - 0.32e2 * t285 * t857 * t861 + 0.64e2 * t471 * t850 * t853 + 0.32e2 * t149 * t154 * t476 * t169 * t478 * t363 * t368 + 0.32e2 * t851 * t382 * t363 * t368 - 0.352e3 / 0.3e1 * t879 * t663 + 0.16e2 * t149 * t361 * t423 * t369 - 0.176e3 / 0.3e1 * t502 * t882 * t357 + 0.88e2 / 0.3e1 * t509 * t886 * t357 - 0.16e2 / 0.3e1 * t509 * t960 * params.eta * t212 + 0.16e2 / 0.3e1 * t149 * t296 * t923 * t299
  t1618 = -0.16e2 * t858 * t450 * t363 * t368 + 0.16e2 * t285 * t890 * t299 + 0.32e2 * t285 * t834 * t837 - 0.16e2 * t420 * t508 * t511 + 0.16e2 * t285 * t864 * t299 - 0.32e2 * t149 * t295 * t993 * t169 * t995 * params.eta * t212 + 0.32e2 * t844 * t883 + 0.16e2 * t420 * t497 * t299 + 0.16e2 / 0.3e1 * t149 * t296 * t999 * t299 - 0.32e2 * t376 * t508 * t511 + 0.32e2 * t985 * t501 * t883
  t1626 = t1108 * t151
  t1684 = -0.8e1 * t302 * t462 * t169 * t960 - 0.8e1 * t302 * t304 * t999 * t463 + 0.16e2 * t289 * t1000 * t458 + 0.24e2 * t289 * t424 * t1118 + 0.16e2 * t289 * t924 * t458 + 0.12e2 * t302 * t424 * t977 - 0.12e2 * t302 * t823 * t827 + 0.48e2 * t472 * t1115 - 0.48e2 * t964 * t464 - 0.24e2 * t467 * t824 - 0.48e2 * t986 * t970
  t1698 = t364 * t33
  t1710 = t886 * s0
  t1711 = t436 * t220
  t1729 = -0.352e3 / 0.3e1 * t1020 * t1021 * t357 + 0.32e2 * t288 * t864 * t1022 - 0.16e2 * t149 * t507 * t423 * t1011 - 0.32e2 * t149 * t856 * t327 * t1698 * t860 - 0.32e2 * t1015 * t882 * s0 * t510 + 0.32e2 * t1020 * t1118 * params.eta * t212 - 0.32e2 * t1015 * t1710 * t1711 + 0.32e2 * t835 * t1710 * t510 - 0.16e2 * t1009 * t827 * params.eta * t212 + 0.32e2 * t288 * t890 * t1022 - 0.16e2 * t149 * t507 * t490 * t1011
  t1774 = 0.64e2 * t288 * t878 * t1698 * t486 * t220 + 0.176e3 / 0.3e1 * t1009 * t298 * s0 * t872 + 0.64e2 * t471 * t497 * t1022 + 0.352e3 / 0.3e1 * t1015 * t503 * s0 * t872 + 0.16e2 * t891 * t1138 * params.eta * t212 + 0.64e2 * t288 * t834 * t836 * s0 * t1711 + 0.32e2 * t149 * t833 * t327 * t1064 * params.eta * t212 - 0.64e2 * t471 * t508 * t1017 - 0.32e2 * t285 * t1008 * t1011 - 0.64e2 * t288 * t857 * t852 * t33 * t860 - 0.8e1 * t467 * t961
  t1783 = t153 ** 2
  t1824 = t375 ** 2
  t1831 = t55 * t667
  t1835 = 0.2560e4 / 0.9e1 * t306 * t952 * t220 * t702 - 0.3520e4 / 0.9e1 * t953 * t1382 + 0.1120e4 / 0.27e2 * t152 / t1783 * t1373 * t1379 + 0.192e3 * t931 * t503 * t56 * t211 * t382 - 0.352e3 * t932 * t946 - 0.7040e4 / 0.9e1 * t939 * t859 * t919 + 0.320e3 * t148 * t443 * t375 * t940 + 0.320e3 / 0.3e1 * t938 * t382 * t940 + 0.64e2 / 0.3e1 * t434 * t686 * t437 + 0.39160e5 / 0.81e2 * t445 * t1387 - 0.10472e5 / 0.81e2 * t313 * t1351 + 0.128e3 * t1372 * t928 * t437 + 0.144e3 * t697 * t375 * t382 + 0.36e2 * t431 * t1511 + 0.48e2 * t431 * t220 * t686 + 0.24e2 * t1824 * t154 + 0.4e1 * t307 * t1353 - 0.352e3 / 0.3e1 * t943 * t946 + 0.9856e4 / 0.27e2 * t435 * t73 * t1831
  t1840 = 0.1e1 / t810 / t60
  t1841 = t547 ** 2
  t1877 = -0.2e1 * t302 * t305 * t1835 + 0.24e2 * t260 * t1840 * t1841 + 0.6e1 * t260 * t545 * t1276 + 0.36e2 * t1072 * t540 * t547 - 0.256e3 / 0.9e1 * t149 * t311 * t304 * t1131 * t1132 * t316 - 0.10472e5 / 0.81e2 * t297 * t298 * t1351 + 0.2464e4 / 0.27e2 * t372 * t669 + 0.7832e4 / 0.27e2 * t362 * t364 * t1387 + 0.32e2 * t1126 * t296 * t299 + 0.32e2 * t376 * t361 * t369 + 0.320e3 / 0.27e2 * t149 * t443 * t157 * t169 * t1373 * t1379
  t1918 = t197 ** 2
  t1922 = t523 ** 2
  t1927 = t530 ** 2
  t1935 = 0.21646500548906162427983539094650205761316872427984e1 * t201 * t1320 * t43 * t47 - 0.15834562056077475194330132601737540009144947416552e-1 * t199 * t524 / t20 / t1029 / r0 * t535 + 0.15089394035554541990550221002895900015241579027587e-3 * t199 * t1036 / t21 / t1029 / t278 * t1049 - 0.68901342628102931463699639282629680434893054920489e-6 * t25 / t1918 / t197 * t1922 * s0 / t1029 / t1319 / t1927 * t47 + 0.2618e4 / 0.243e3 * t54 * t1351
  t1937 = -t1392
  t1938 = f.my_piecewise3(t81, 0, t1937)
  t1945 = t554 ** 2
  t1949 = t557 ** 2
  t1975 = t568 ** 2
  t1981 = t570 ** 2
  t1984 = t573 ** 2
  t1986 = t575 ** 2
  t1988 = f.my_piecewise3(t89, 0, t1937)
  t2012 = -0.26673330e1 * t1984 + 0.34831129067760e2 * t1986 - 0.667e0 * t1988 + 0.5805188177960e1 * t94 * t1988 - 0.11935558818882e2 * t90 * t1984 - 0.53279882495820e2 * t94 * t1984 + 0.84430418932440e2 * t92 * t1986 - 0.8891110e0 * t90 * t1988 - 0.23871117637764e2 * t575 * t573 - 0.1989259803147e1 * t92 * t1988 - 0.19476108390480e2 * t94 * t1986 - 0.2921416258572e1 * t98 * t1984 - 0.35564440e1 * t236 * t738 + 0.1407173648874e1 * t98 * t1988
  t2041 = -0.162300903254e0 * t100 * t1988 + 0.21107604733110e2 * t96 * t1984 - 0.4439990207985e1 * t96 * t1988 + 0.52246693601640e2 * t92 * t1984 - 0.106559764991640e3 * t90 * t1986 + 0.28143472977480e2 * t244 * t738 - 0.29214162585720e2 * t591 * t573 - 0.319679294974920e3 * t583 * t573 - 0.15914078425176e2 * t238 * t738 + 0.208986774406560e3 * t579 * t573 + 0.69662258135520e2 * t240 * t738 - 0.71039843327760e2 * t242 * t738 + 0.168860837864880e3 * t587 * t573 - 0.3895221678096e1 * t246 * t738
  t2043 = t602 ** 2
  t2050 = t602 * t109 * t607
  t2057 = t607 ** 2
  t2065 = t781 * t791
  t2074 = f.my_piecewise3(t89, t1937, 0)
  t2087 = t611 ** 2
  t2089 = t613 ** 2
  t2094 = -0.24e2 * t251 * t786 * t2043 * t109 - 0.36e2 * t251 * t614 * t2050 - 0.36e2 * t612 * t801 * t2043 * t109 - 0.6e1 * t251 * t601 * t2057 * t109 - 0.36e2 * t612 * t786 * t2050 - 0.8e1 * t780 * t2065 - 0.12e2 * t799 / t613 / t600 * t2043 * t109 - t251 * t253 * t2074 * t109 - 0.4e1 * t795 * t2065 - 0.3e1 * t612 * t614 * t2057 * t109 - 0.6e1 * t799 * t801 * t2050 - params.d * t2087 / t2089 * t2043 * t109
  t2095 = f.my_piecewise5(t80, (-params.c1 * t1938 * t85 - 0.8e1 * t711 * t232 - 0.36e2 * t555 * t563 - 0.6e1 * params.c1 * t1945 * t231 - 0.24e2 * params.c1 * t1949 * t720 - 0.24e2 * t83 / t719 / t84 * t1949 - 0.36e2 * t83 * t720 * t557 * t554 - 0.6e1 * t83 * t562 * t1945 - 0.8e1 * t83 * t724 * t710 - t83 * t231 * t1938) * t87 + 0.4e1 * t730 * t234 * t87 + 0.3e1 * t1975 * t87 + 0.6e1 * t568 * t570 * t87 + t1981 * t87, t88, t2012 + t2041, t2094)
  t2102 = 0.256e3 / 0.9e1 * t1130 * t1138 * t702 - 0.176e3 / 0.3e1 * t672 * t358 - 0.88e2 / 0.3e1 * t680 * t358 - 0.352e3 / 0.3e1 * t677 * t663 + 0.16e2 * t420 * t361 * t369 + 0.16e2 / 0.3e1 * t1108 * t296 * t299 + 0.512e3 / 0.9e1 * t288 * t1129 * t458 * t702 - 0.24e2 * t193 * t1840 * t1841 + t196 * t1935 + t2095 * t112 - 0.64e2 * t288 * t295 * t462 * t169 * t1017
  t2133 = -0.6e1 * t816 * t541 - 0.24e2 * t514 * t813 - 0.16e2 * t840 * t887 + 0.32e2 * t376 * t497 * t299 + 0.32e2 * t285 * t878 * t369 + 0.16e2 * t149 * t361 * t490 * t369 - 0.88e2 / 0.3e1 * t891 * t358 - 0.176e3 / 0.3e1 * t835 * t836 * t357 + 0.176e3 / 0.3e1 * t840 * t873 - 0.2464e4 / 0.27e2 * t509 * t73 * t1831 * t316 + 0.2464e4 / 0.27e2 * t498 * t669
  t2162 = -0.352e3 / 0.3e1 * t844 * t868 - 0.176e3 / 0.3e1 * t847 * t358 + 0.4928e4 / 0.27e2 * t502 * t503 * t668 - 0.704e3 / 0.3e1 * t851 * t852 * t662 + 0.352e3 / 0.3e1 * t858 * t859 * t919 * t316 - 0.88e2 / 0.3e1 * t865 * t358 + 0.32e2 * t902 * t501 * t504 - 0.4e1 * t514 * t1055 - t260 * t195 * t1935 - 0.8e1 * t546 * t1054 * t215 - 0.48e2 * t1451 * t317
  t2177 = t17 / t20 / t19 * t173
  t2184 = t211 * t173
  t2188 = t23 * t332
  t2195 = t341 * t17 / t37 * t173
  t2216 = 0.88793235622637281199999999999999999999999999999999e2 * t649 * t17 / r0 * t173 / s0 * t27 * t176 * t35 * t188 + 0.32642285880000000000000000000000000000000000000000e2 * t1187 * t1214 * t1192 + 0.24481714410000000000000000000000000000000000000000e2 * t649 * t1163 * t622 * t657 - 0.47499840000000000000000000000000000000000000000000e4 * t1174 * t332 * t1181 * t1183 - 0.3e1 / 0.8e1 * t18 * t20 * (-0.48e2 * t302 * t993 * t327 * t169 * t995 + t1288 + 0.8e1 * t302 * t924 * t1138 - 0.12e2 * t302 * t1068 * t827 + t1877 + t1460 + t1774 + t2102 + t1426 + t2133 + t1332 + t2162 + t1538 + t1579 + t1684 + t1729 - 0.24e2 * t467 * t828 - 0.8e1 * t1626 * t317 + 0.24e2 * t910 * t479 + 0.8e1 * t1626 * t329 - 0.48e2 * t467 * t996 - 0.48e2 * t472 * t974 - 0.48e2 * t472 * t970 - 0.24e2 * t467 * t1069 + 0.48e2 * t986 * t1119 + 0.12e2 * t910 * t492 + 0.32e2 / 0.3e1 * t502 * t686 * params.eta * t212 + 0.48e2 * t289 * t477 * t382 * t478 + 0.24e2 * t302 * t476 * t423 * t1064 - 0.8e1 * t302 * t304 * t923 * t463 + 0.16e2 * t289 * t328 * t169 * t686 - 0.24e2 * t289 * t305 * t382 * t450 - 0.16e2 * t289 * t305 * t686 * t316 + t1618) * t189 - 0.32642285880000000000000000000000000000000000000000e2 * t649 * t1214 * t657 - 0.32642285879999999999999999999999999999999999999998e2 * t1187 * t2177 * t1192 + 0.30375460471666666666666666666666666666666666666666e2 * t649 * t2177 * t657 + 0.10e2 / 0.27e2 * t18 * t2184 * t189 - 0.12920861304452160000000000000000000000000000000000e4 * t1195 * t2188 * t1196 - 0.64604306522260800000000000000000000000000000000000e3 * t2195 * t640 * t188 * t27 * t176 * t178 * t35 - 0.76967333333333333333333333333333333333333333333333e2 * t1170 * t17 * t204 * t173 / t184 / t32 / t144 * t33 * t188 * t177 * t35
  t2264 = -0.17812440000000000000000000000000000000000000000000e3 * t341 * t1157 * t622 * t644 - 0.98958000000000000000000000000000000000000000000000e1 * t341 * t1150 * t1144 * t351 + 0.15041616000000000000000000000000000000000000000000e5 * t1170 * t17 / t21 / t365 * t1184 + 0.86139075363014400000000000000000000000000000000001e3 * t1195 * t2184 * t1196 + 0.24739500000000000000000000000000000000000000000000e2 * t341 * t628 * t622 * t351 + 0.71249760000000000000000000000000000000000000000000e3 * t341 * t633 * t332 * t644 + 0.46363655555555555555555555555555555555555555555554e2 * t2195 * t351 - 0.47279933333333333333333333333333333333333333333333e2 * t341 * t343 * t332 * t351 - 0.10918366000000000000000000000000000000000000000000e4 * t341 * t17 * t280 * t173 * t644 - 0.5e1 / 0.9e1 * t18 * t2188 * t189 + t18 * t67 * t622 * t189 / 0.2e1 - t18 * t354 * t1144 * t189 / 0.2e1
  t2266 = f.my_piecewise3(t2, 0, t2216 + t2264)
  v4rho4_0_ = 0.2e1 * r0 * t2266 + 0.8e1 * t1201

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t6 ** 2
  t23 = 0.1e1 / t22
  t24 = t16 * t23
  t25 = t7 - t24
  t26 = f.my_piecewise5(t10, 0, t14, 0, t25)
  t29 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t26)
  t30 = t5 * t29
  t31 = t6 ** (0.1e1 / 0.3e1)
  t33 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t39 = 0.1e1 / t37 / t36
  t40 = t35 * t39
  t41 = s0 ** 2
  t42 = r0 ** 2
  t43 = t42 ** 2
  t45 = r0 ** (0.1e1 / 0.3e1)
  t47 = 0.1e1 / t45 / t43 / r0
  t48 = t41 * t47
  t49 = params.dp2 ** 2
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t55 = jnp.exp(-t40 * t48 * t51 / 0.576e3)
  t59 = (-0.162742215233874e0 * t33 * t55 + 0.10e2 / 0.81e2) * t34
  t60 = t37 ** 2
  t61 = 0.1e1 / t60
  t62 = t61 * s0
  t63 = t45 ** 2
  t65 = 0.1e1 / t63 / t42
  t66 = t62 * t65
  t69 = params.k1 + t59 * t66 / 0.24e2
  t73 = params.k1 * (0.1e1 - params.k1 / t69)
  t77 = s0 * t65
  t79 = tau0 / t63 / r0 - t77 / 0.8e1
  t81 = 0.3e1 / 0.10e2 * t35 * t60
  t82 = params.eta * s0
  t85 = t81 + t82 * t65 / 0.8e1
  t86 = 0.1e1 / t85
  t87 = t79 * t86
  t88 = t87 <= 0.0e0
  t89 = 0.0e0 < t87
  t90 = f.my_piecewise3(t89, 0, t87)
  t91 = params.c1 * t90
  t92 = 0.1e1 - t90
  t93 = 0.1e1 / t92
  t95 = jnp.exp(-t91 * t93)
  t96 = t87 <= 0.25e1
  t97 = 0.25e1 < t87
  t98 = f.my_piecewise3(t97, 0.25e1, t87)
  t100 = t98 ** 2
  t102 = t100 * t98
  t104 = t100 ** 2
  t106 = t104 * t98
  t108 = t104 * t100
  t113 = f.my_piecewise3(t97, t87, 0.25e1)
  t114 = 0.1e1 - t113
  t117 = jnp.exp(params.c2 / t114)
  t119 = f.my_piecewise5(t88, t95, t96, 0.1e1 - 0.667e0 * t98 - 0.4445555e0 * t100 - 0.663086601049e0 * t102 + 0.1451297044490e1 * t104 - 0.887998041597e0 * t106 + 0.234528941479e0 * t108 - 0.23185843322e-1 * t104 * t102, -params.d * t117)
  t120 = 0.174e0 - t73
  t123 = t33 * t34
  t126 = 0.1e1 - t87
  t127 = t126 ** 2
  t132 = (0.40570770199022687796862290864197530864197530864200e-1 - 0.30235468026081006356817095666666666666666666666667e0 * params.eta) * t34 * t61
  t138 = (0.3e1 / 0.4e1 * params.eta + 0.2e1 / 0.3e1) ** 2
  t143 = (0.290700106132790123456790123456790123456790123457e-2 - 0.27123702538979000000000000000000000000000000000000e0 * params.eta) ** 2
  t147 = (0.146e3 / 0.2025e4 * t138 - 0.73e2 / 0.540e3 * params.eta - 0.146e3 / 0.1215e4 + t143 / params.k1) * t35
  t148 = t39 * t41
  t152 = -0.162742215233874e0 + 0.162742215233874e0 * t87 + 0.67809256347447500000000000000000000000000000000000e-2 * t123 * t66 - 0.59353125082804000000000000000000000000000000000000e-1 * t127 + t132 * t77 * t126 / 0.24e2 + t147 * t148 * t47 / 0.576e3
  t153 = t79 ** 2
  t154 = t152 * t153
  t155 = t85 ** 2
  t156 = 0.1e1 / t155
  t157 = t153 ** 2
  t158 = t155 ** 2
  t159 = 0.1e1 / t158
  t161 = t157 * t159 + 0.1e1
  t162 = 0.1e1 / t161
  t164 = params.da4 ** 2
  t165 = 0.1e1 / t164
  t167 = params.dp4 ** 2
  t168 = t167 ** 2
  t169 = 0.1e1 / t168
  t174 = jnp.exp(-t127 * t165 - t40 * t48 * t169 / 0.576e3)
  t175 = t156 * t162 * t174
  t178 = t119 * t120 + 0.2e1 * t154 * t175 + t73 + 0.1e1
  t180 = jnp.sqrt(0.3e1)
  t181 = 0.1e1 / t37
  t182 = t35 * t181
  t183 = jnp.sqrt(s0)
  t187 = t182 * t183 / t45 / r0
  t188 = jnp.sqrt(t187)
  t192 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t180 / t188)
  t193 = 0.1e1 - t192
  t194 = t31 * t178 * t193
  t197 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t198 = t197 * f.p.zeta_threshold
  t200 = f.my_piecewise3(t20, t198, t21 * t19)
  t201 = t5 * t200
  t202 = t31 ** 2
  t203 = 0.1e1 / t202
  t205 = t203 * t178 * t193
  t207 = t201 * t205 / 0.8e1
  t208 = params.k1 ** 2
  t209 = t69 ** 2
  t210 = 0.1e1 / t209
  t211 = t208 * t210
  t212 = t36 ** 2
  t214 = t33 / t212
  t216 = t214 * t41 * s0
  t217 = t43 ** 2
  t224 = t42 * r0
  t226 = 0.1e1 / t63 / t224
  t227 = t62 * t226
  t230 = -0.37671809081915277777777777777777777777777777777778e-3 * t216 / t217 / r0 * t51 * t55 - t59 * t227 / 0.9e1
  t234 = s0 * t226
  t236 = -0.5e1 / 0.3e1 * tau0 * t65 + t234 / 0.3e1
  t237 = t236 * t86
  t238 = t79 * t156
  t239 = t82 * t226
  t240 = t238 * t239
  t242 = t237 + t240 / 0.3e1
  t243 = f.my_piecewise3(t89, 0, t242)
  t246 = t92 ** 2
  t247 = 0.1e1 / t246
  t250 = -t91 * t247 * t243 - params.c1 * t243 * t93
  t252 = f.my_piecewise3(t97, 0, t242)
  t267 = params.d * params.c2
  t268 = t114 ** 2
  t269 = 0.1e1 / t268
  t270 = f.my_piecewise3(t97, t242, 0)
  t274 = f.my_piecewise5(t88, t250 * t95, t96, -0.667e0 * t252 - 0.8891110e0 * t98 * t252 - 0.1989259803147e1 * t100 * t252 + 0.5805188177960e1 * t102 * t252 - 0.4439990207985e1 * t104 * t252 + 0.1407173648874e1 * t106 * t252 - 0.162300903254e0 * t108 * t252, -t267 * t269 * t270 * t117)
  t276 = t119 * t208
  t277 = t210 * t230
  t283 = -t242
  t294 = 0.1e1 / t45 / t43 / t42
  t298 = 0.162742215233874e0 * t237 + 0.54247405077958000000000000000000000000000000000000e-1 * t240 - 0.18082468359319333333333333333333333333333333333333e-1 * t123 * t227 - 0.11870625016560800000000000000000000000000000000000e0 * t126 * t283 - t132 * t234 * t126 / 0.9e1 + t132 * t77 * t283 / 0.24e2 - t147 * t148 * t294 / 0.108e3
  t299 = t298 * t153
  t302 = t152 * t79
  t303 = t302 * t156
  t304 = t162 * t174
  t305 = t304 * t236
  t309 = 0.1e1 / t155 / t85
  t310 = t309 * t162
  t311 = t154 * t310
  t312 = t174 * params.eta
  t313 = t312 * t234
  t316 = t154 * t156
  t317 = t161 ** 2
  t318 = 0.1e1 / t317
  t319 = t318 * t174
  t320 = t153 * t79
  t321 = t320 * t159
  t325 = 0.1e1 / t158 / t85
  t326 = t157 * t325
  t329 = 0.4e1 * t321 * t236 + 0.4e1 / 0.3e1 * t326 * t239
  t330 = t319 * t329
  t333 = t126 * t165
  t340 = -0.2e1 * t333 * t283 + t40 * t41 * t294 * t169 / 0.108e3
  t341 = t162 * t340
  t342 = t341 * t174
  t345 = t211 * t230 + t274 * t120 - t276 * t277 + 0.2e1 * t299 * t175 + 0.4e1 * t303 * t305 + 0.4e1 / 0.3e1 * t311 * t313 - 0.2e1 * t316 * t330 + 0.2e1 * t316 * t342
  t347 = t31 * t345 * t193
  t350 = 3 ** (0.1e1 / 0.6e1)
  t351 = t350 ** 2
  t352 = t351 ** 2
  t354 = t352 * t350 * t4
  t355 = t200 * t31
  t356 = t355 * t178
  t357 = t354 * t356
  t361 = 0.1e1 / t188 / t187 * t35 * t181
  t366 = t361 * t183 / t45 / t42 * t192
  t370 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t194 - t207 - 0.3e1 / 0.8e1 * t201 * t347 - 0.24739500000000000000000000000000000000000000000000e1 * t357 * t366)
  t372 = r1 <= f.p.dens_threshold
  t373 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t374 = 0.1e1 + t373
  t375 = t374 <= f.p.zeta_threshold
  t376 = t374 ** (0.1e1 / 0.3e1)
  t378 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t381 = f.my_piecewise3(t375, 0, 0.4e1 / 0.3e1 * t376 * t378)
  t382 = t5 * t381
  t383 = s2 ** 2
  t384 = r1 ** 2
  t385 = t384 ** 2
  t387 = r1 ** (0.1e1 / 0.3e1)
  t389 = 0.1e1 / t387 / t385 / r1
  t390 = t383 * t389
  t394 = jnp.exp(-t40 * t390 * t51 / 0.576e3)
  t398 = (-0.162742215233874e0 * t33 * t394 + 0.10e2 / 0.81e2) * t34
  t399 = t61 * s2
  t400 = t387 ** 2
  t402 = 0.1e1 / t400 / t384
  t403 = t399 * t402
  t406 = params.k1 + t398 * t403 / 0.24e2
  t410 = params.k1 * (0.1e1 - params.k1 / t406)
  t414 = s2 * t402
  t416 = tau1 / t400 / r1 - t414 / 0.8e1
  t417 = params.eta * s2
  t420 = t81 + t417 * t402 / 0.8e1
  t421 = 0.1e1 / t420
  t422 = t416 * t421
  t423 = t422 <= 0.0e0
  t424 = 0.0e0 < t422
  t425 = f.my_piecewise3(t424, 0, t422)
  t426 = params.c1 * t425
  t427 = 0.1e1 - t425
  t428 = 0.1e1 / t427
  t430 = jnp.exp(-t426 * t428)
  t431 = t422 <= 0.25e1
  t432 = 0.25e1 < t422
  t433 = f.my_piecewise3(t432, 0.25e1, t422)
  t435 = t433 ** 2
  t437 = t435 * t433
  t439 = t435 ** 2
  t441 = t439 * t433
  t443 = t439 * t435
  t448 = f.my_piecewise3(t432, t422, 0.25e1)
  t449 = 0.1e1 - t448
  t452 = jnp.exp(params.c2 / t449)
  t454 = f.my_piecewise5(t423, t430, t431, 0.1e1 - 0.667e0 * t433 - 0.4445555e0 * t435 - 0.663086601049e0 * t437 + 0.1451297044490e1 * t439 - 0.887998041597e0 * t441 + 0.234528941479e0 * t443 - 0.23185843322e-1 * t439 * t437, -params.d * t452)
  t455 = 0.174e0 - t410
  t460 = 0.1e1 - t422
  t461 = t460 ** 2
  t466 = t39 * t383
  t470 = -0.162742215233874e0 + 0.162742215233874e0 * t422 + 0.67809256347447500000000000000000000000000000000000e-2 * t123 * t403 - 0.59353125082804000000000000000000000000000000000000e-1 * t461 + t132 * t414 * t460 / 0.24e2 + t147 * t466 * t389 / 0.576e3
  t471 = t416 ** 2
  t472 = t470 * t471
  t473 = t420 ** 2
  t474 = 0.1e1 / t473
  t475 = t471 ** 2
  t476 = t473 ** 2
  t477 = 0.1e1 / t476
  t479 = t475 * t477 + 0.1e1
  t480 = 0.1e1 / t479
  t487 = jnp.exp(-t461 * t165 - t40 * t390 * t169 / 0.576e3)
  t488 = t474 * t480 * t487
  t491 = t454 * t455 + 0.2e1 * t472 * t488 + t410 + 0.1e1
  t493 = jnp.sqrt(s2)
  t497 = t182 * t493 / t387 / r1
  t498 = jnp.sqrt(t497)
  t502 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t180 / t498)
  t503 = 0.1e1 - t502
  t504 = t31 * t491 * t503
  t508 = f.my_piecewise3(t375, t198, t376 * t374)
  t509 = t5 * t508
  t511 = t203 * t491 * t503
  t513 = t509 * t511 / 0.8e1
  t515 = f.my_piecewise3(t372, 0, -0.3e1 / 0.8e1 * t382 * t504 - t513)
  t517 = t21 ** 2
  t518 = 0.1e1 / t517
  t519 = t26 ** 2
  t524 = t16 / t22 / t6
  t526 = -0.2e1 * t23 + 0.2e1 * t524
  t527 = f.my_piecewise5(t10, 0, t14, 0, t526)
  t531 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t518 * t519 + 0.4e1 / 0.3e1 * t21 * t527)
  t535 = t30 * t205
  t545 = 0.1e1 / t202 / t6
  t549 = t201 * t545 * t178 * t193 / 0.12e2
  t552 = t201 * t203 * t345 * t193
  t557 = t354 * t200 * t203 * t178 * t366
  t562 = 0.1e1 / t63 / t43
  t563 = s0 * t562
  t565 = 0.40e2 / 0.9e1 * tau0 * t226 - 0.11e2 / 0.9e1 * t563
  t566 = t565 * t86
  t568 = t236 * t156 * t239
  t571 = params.eta ** 2
  t573 = t43 * t224
  t575 = 0.1e1 / t45 / t573
  t576 = t571 * t41 * t575
  t577 = t79 * t309 * t576
  t579 = t82 * t562
  t580 = t238 * t579
  t582 = t566 + 0.2e1 / 0.3e1 * t568 + 0.2e1 / 0.9e1 * t577 - 0.11e2 / 0.9e1 * t580
  t583 = f.my_piecewise3(t89, 0, t582)
  t586 = t243 ** 2
  t599 = t250 ** 2
  t602 = f.my_piecewise3(t97, 0, t582)
  t604 = t252 ** 2
  t628 = -0.667e0 * t602 - 0.8891110e0 * t604 - 0.8891110e0 * t98 * t602 - 0.3978519606294e1 * t98 * t604 - 0.1989259803147e1 * t100 * t602 + 0.17415564533880e2 * t100 * t604 + 0.5805188177960e1 * t102 * t602 - 0.17759960831940e2 * t102 * t604 - 0.4439990207985e1 * t104 * t602 + 0.7035868244370e1 * t104 * t604 + 0.1407173648874e1 * t106 * t602 - 0.973805419524e0 * t106 * t604 - 0.162300903254e0 * t108 * t602
  t631 = t270 ** 2
  t636 = f.my_piecewise3(t97, t582, 0)
  t640 = params.c2 ** 2
  t641 = params.d * t640
  t642 = t268 ** 2
  t648 = f.my_piecewise5(t88, (-params.c1 * t583 * t93 - 0.2e1 * params.c1 * t586 * t247 - 0.2e1 * t91 / t246 / t92 * t586 - t91 * t247 * t583) * t95 + t599 * t95, t96, t628, -0.2e1 * t267 / t268 / t114 * t631 * t117 - t267 * t269 * t636 * t117 - t641 / t642 * t631 * t117)
  t654 = t62 * t562
  t657 = t283 ** 2
  t659 = -t582
  t674 = 0.162742215233874e0 * t566 + 0.10849481015591600000000000000000000000000000000000e0 * t568 + 0.36164936718638666666666666666666666666666666666667e-1 * t577 - 0.19890715195251266666666666666666666666666666666667e0 * t580 + 0.66302383984170888888888888888888888888888888888888e-1 * t123 * t654 - 0.11870625016560800000000000000000000000000000000000e0 * t657 - 0.11870625016560800000000000000000000000000000000000e0 * t126 * t659 + 0.11e2 / 0.27e2 * t132 * t563 * t126 - 0.2e1 / 0.9e1 * t132 * t234 * t283 + t132 * t77 * t659 / 0.24e2 + 0.19e2 / 0.324e3 * t147 * t148 * t575
  t678 = t236 ** 2
  t686 = t174 * t236
  t722 = t41 * t575
  t734 = t329 ** 2
  t738 = t340 ** 2
  t747 = t648 * t120 + 0.2e1 * t674 * t153 * t175 + 0.4e1 * t152 * t678 * t175 - 0.8e1 * t303 * t319 * t236 * t329 + 0.8e1 * t303 * t341 * t686 - 0.4e1 * t316 * t318 * t340 * t174 * t329 + 0.4e1 * t303 * t304 * t565 - 0.2e1 * t316 * t319 * (0.12e2 * t153 * t159 * t678 + 0.32e2 / 0.3e1 * t320 * t325 * t236 * t239 + 0.4e1 * t321 * t565 + 0.20e2 / 0.9e1 * t157 / t158 / t155 * t576 - 0.44e2 / 0.9e1 * t326 * t579) + 0.2e1 * t316 * t162 * (-0.2e1 * t657 * t165 - 0.2e1 * t333 * t659 - 0.19e2 / 0.324e3 * t40 * t722 * t169) * t174 + 0.4e1 * t316 / t317 / t161 * t174 * t734 + 0.2e1 * t316 * t162 * t738 * t174 + 0.8e1 * t298 * t79 * t156 * t305
  t748 = t299 * t156
  t754 = 0.1e1 / t209 / t69
  t756 = t230 ** 2
  t765 = t41 ** 2
  t772 = t50 ** 2
  t774 = 0.1e1 / t772 * t35
  t781 = 0.43950443928901157407407407407407407407407407407407e-2 * t216 / t217 / t42 * t51 * t55 - 0.34881304705477109053497942386831275720164609053498e-5 * t214 * t765 * s0 / t45 / t217 / t573 * t774 * t39 * t55 + 0.11e2 / 0.27e2 * t59 * t654
  t817 = -0.4e1 * t748 * t330 + 0.4e1 * t748 * t342 - 0.2e1 * t208 * t754 * t756 + t211 * t781 - 0.2e1 * t274 * t208 * t277 - t276 * t210 * t781 + 0.2e1 * t276 * t754 * t756 + 0.4e1 / 0.3e1 * t154 * t159 * t162 * t174 * t571 * t722 + 0.8e1 / 0.3e1 * t299 * t310 * t313 - 0.44e2 / 0.9e1 * t311 * t312 * t563 + 0.16e2 / 0.3e1 * t302 * t310 * t686 * t239 - 0.8e1 / 0.3e1 * t154 * t309 * t318 * t312 * t234 * t329 + 0.8e1 / 0.3e1 * t311 * t340 * t174 * t239
  t827 = t34 * t61
  t845 = t3 ** 2
  t847 = t2 * t845 * jnp.pi
  t856 = -0.3e1 / 0.8e1 * t5 * t531 * t194 - t535 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t347 - 0.49479000000000000000000000000000000000000000000000e1 * t354 * t29 * t31 * t178 * t366 + t549 - t552 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t557 - 0.3e1 / 0.8e1 * t201 * t31 * (t747 + t817) * t193 - 0.49479000000000000000000000000000000000000000000000e1 * t354 * t355 * t345 * t366 - 0.49479000000000000000000000000000000000000000000000e1 * t357 / t188 / t827 / t77 * t34 * t61 * t563 * t192 + 0.57725500000000000000000000000000000000000000000000e1 * t357 * t361 * t183 / t45 / t224 * t192 + 0.81605714700000000000000000000000000000000000000000e1 * t847 * t356 / t183 / t63 * t827 * t192
  t857 = f.my_piecewise3(t1, 0, t856)
  t858 = t376 ** 2
  t859 = 0.1e1 / t858
  t860 = t378 ** 2
  t864 = f.my_piecewise5(t14, 0, t10, 0, -t526)
  t868 = f.my_piecewise3(t375, 0, 0.4e1 / 0.9e1 * t859 * t860 + 0.4e1 / 0.3e1 * t376 * t864)
  t872 = t382 * t511
  t877 = t509 * t545 * t491 * t503 / 0.12e2
  t879 = f.my_piecewise3(t372, 0, -0.3e1 / 0.8e1 * t5 * t868 * t504 - t872 / 0.4e1 + t877)
  d11 = 0.2e1 * t370 + 0.2e1 * t515 + t6 * (t857 + t879)
  t882 = -t7 - t24
  t883 = f.my_piecewise5(t10, 0, t14, 0, t882)
  t886 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t883)
  t887 = t5 * t886
  t891 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t887 * t194 - t207)
  t893 = f.my_piecewise5(t14, 0, t10, 0, -t882)
  t896 = f.my_piecewise3(t375, 0, 0.4e1 / 0.3e1 * t376 * t893)
  t897 = t5 * t896
  t900 = t406 ** 2
  t901 = 0.1e1 / t900
  t902 = t208 * t901
  t904 = t214 * t383 * s2
  t905 = t385 ** 2
  t912 = t384 * r1
  t914 = 0.1e1 / t400 / t912
  t915 = t399 * t914
  t918 = -0.37671809081915277777777777777777777777777777777778e-3 * t904 / t905 / r1 * t51 * t394 - t398 * t915 / 0.9e1
  t922 = s2 * t914
  t924 = -0.5e1 / 0.3e1 * tau1 * t402 + t922 / 0.3e1
  t925 = t924 * t421
  t926 = t416 * t474
  t927 = t417 * t914
  t928 = t926 * t927
  t930 = t925 + t928 / 0.3e1
  t931 = f.my_piecewise3(t424, 0, t930)
  t934 = t427 ** 2
  t935 = 0.1e1 / t934
  t938 = -t426 * t935 * t931 - params.c1 * t931 * t428
  t940 = f.my_piecewise3(t432, 0, t930)
  t955 = t449 ** 2
  t956 = 0.1e1 / t955
  t957 = f.my_piecewise3(t432, t930, 0)
  t961 = f.my_piecewise5(t423, t938 * t430, t431, -0.667e0 * t940 - 0.8891110e0 * t433 * t940 - 0.1989259803147e1 * t435 * t940 + 0.5805188177960e1 * t437 * t940 - 0.4439990207985e1 * t439 * t940 + 0.1407173648874e1 * t441 * t940 - 0.162300903254e0 * t443 * t940, -t267 * t956 * t957 * t452)
  t963 = t454 * t208
  t964 = t901 * t918
  t970 = -t930
  t981 = 0.1e1 / t387 / t385 / t384
  t985 = 0.162742215233874e0 * t925 + 0.54247405077958000000000000000000000000000000000000e-1 * t928 - 0.18082468359319333333333333333333333333333333333333e-1 * t123 * t915 - 0.11870625016560800000000000000000000000000000000000e0 * t460 * t970 - t132 * t922 * t460 / 0.9e1 + t132 * t414 * t970 / 0.24e2 - t147 * t466 * t981 / 0.108e3
  t986 = t985 * t471
  t989 = t470 * t416
  t990 = t989 * t474
  t991 = t480 * t487
  t992 = t991 * t924
  t996 = 0.1e1 / t473 / t420
  t997 = t996 * t480
  t998 = t472 * t997
  t999 = t487 * params.eta
  t1000 = t999 * t922
  t1003 = t472 * t474
  t1004 = t479 ** 2
  t1005 = 0.1e1 / t1004
  t1006 = t1005 * t487
  t1007 = t471 * t416
  t1008 = t1007 * t477
  t1012 = 0.1e1 / t476 / t420
  t1013 = t475 * t1012
  t1016 = 0.4e1 * t1008 * t924 + 0.4e1 / 0.3e1 * t1013 * t927
  t1017 = t1006 * t1016
  t1020 = t460 * t165
  t1027 = -0.2e1 * t1020 * t970 + t40 * t383 * t981 * t169 / 0.108e3
  t1028 = t480 * t1027
  t1029 = t1028 * t487
  t1032 = t902 * t918 + t961 * t455 - t963 * t964 + 0.2e1 * t986 * t488 + 0.4e1 * t990 * t992 + 0.4e1 / 0.3e1 * t998 * t1000 - 0.2e1 * t1003 * t1017 + 0.2e1 * t1003 * t1029
  t1034 = t31 * t1032 * t503
  t1037 = t508 * t31
  t1038 = t1037 * t491
  t1039 = t354 * t1038
  t1043 = 0.1e1 / t498 / t497 * t35 * t181
  t1048 = t1043 * t493 / t387 / t384 * t502
  t1052 = f.my_piecewise3(t372, 0, -0.3e1 / 0.8e1 * t897 * t504 - t513 - 0.3e1 / 0.8e1 * t509 * t1034 - 0.24739500000000000000000000000000000000000000000000e1 * t1039 * t1048)
  t1056 = 0.2e1 * t524
  t1057 = f.my_piecewise5(t10, 0, t14, 0, t1056)
  t1061 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t518 * t883 * t26 + 0.4e1 / 0.3e1 * t21 * t1057)
  t1065 = t887 * t205
  t1078 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t1061 * t194 - t1065 / 0.8e1 - 0.3e1 / 0.8e1 * t887 * t347 - 0.24739500000000000000000000000000000000000000000000e1 * t354 * t886 * t31 * t178 * t366 - t535 / 0.8e1 + t549 - t552 / 0.8e1 - 0.82465000000000000000000000000000000000000000000000e0 * t557)
  t1082 = f.my_piecewise5(t14, 0, t10, 0, -t1056)
  t1086 = f.my_piecewise3(t375, 0, 0.4e1 / 0.9e1 * t859 * t893 * t378 + 0.4e1 / 0.3e1 * t376 * t1082)
  t1090 = t897 * t511
  t1097 = t509 * t203 * t1032 * t503
  t1107 = t354 * t508 * t203 * t491 * t1048
  t1110 = f.my_piecewise3(t372, 0, -0.3e1 / 0.8e1 * t5 * t1086 * t504 - t1090 / 0.8e1 - t872 / 0.8e1 + t877 - 0.3e1 / 0.8e1 * t382 * t1034 - t1097 / 0.8e1 - 0.24739500000000000000000000000000000000000000000000e1 * t354 * t381 * t31 * t491 * t1048 - 0.82465000000000000000000000000000000000000000000000e0 * t1107)
  d12 = t370 + t515 + t891 + t1052 + t6 * (t1078 + t1110)
  t1115 = t883 ** 2
  t1119 = 0.2e1 * t23 + 0.2e1 * t524
  t1120 = f.my_piecewise5(t10, 0, t14, 0, t1119)
  t1124 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t518 * t1115 + 0.4e1 / 0.3e1 * t21 * t1120)
  t1130 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t1124 * t194 - t1065 / 0.4e1 + t549)
  t1131 = t893 ** 2
  t1135 = f.my_piecewise5(t14, 0, t10, 0, -t1119)
  t1139 = f.my_piecewise3(t375, 0, 0.4e1 / 0.9e1 * t859 * t1131 + 0.4e1 / 0.3e1 * t376 * t1135)
  t1153 = t924 ** 2
  t1160 = 0.1e1 / t400 / t385
  t1161 = s2 * t1160
  t1163 = 0.40e2 / 0.9e1 * tau1 * t914 - 0.11e2 / 0.9e1 * t1161
  t1164 = t1163 * t421
  t1167 = t924 * t474 * t927
  t1171 = t385 * t912
  t1173 = 0.1e1 / t387 / t1171
  t1174 = t571 * t383 * t1173
  t1175 = t416 * t996 * t1174
  t1177 = t417 * t1160
  t1178 = t926 * t1177
  t1180 = t399 * t1160
  t1183 = t970 ** 2
  t1188 = -t1164 - 0.2e1 / 0.3e1 * t1167 - 0.2e1 / 0.9e1 * t1175 + 0.11e2 / 0.9e1 * t1178
  t1203 = 0.162742215233874e0 * t1164 + 0.10849481015591600000000000000000000000000000000000e0 * t1167 + 0.36164936718638666666666666666666666666666666666667e-1 * t1175 - 0.19890715195251266666666666666666666666666666666667e0 * t1178 + 0.66302383984170888888888888888888888888888888888888e-1 * t123 * t1180 - 0.11870625016560800000000000000000000000000000000000e0 * t1183 - 0.11870625016560800000000000000000000000000000000000e0 * t460 * t1188 + 0.11e2 / 0.27e2 * t132 * t1161 * t460 - 0.2e1 / 0.9e1 * t132 * t922 * t970 + t132 * t414 * t1188 / 0.24e2 + 0.19e2 / 0.324e3 * t147 * t466 * t1173
  t1207 = -t1188
  t1208 = f.my_piecewise3(t424, 0, t1207)
  t1211 = t931 ** 2
  t1224 = t938 ** 2
  t1227 = f.my_piecewise3(t432, 0, t1207)
  t1229 = t940 ** 2
  t1253 = -0.667e0 * t1227 - 0.8891110e0 * t1229 - 0.8891110e0 * t433 * t1227 - 0.3978519606294e1 * t433 * t1229 - 0.1989259803147e1 * t435 * t1227 + 0.17415564533880e2 * t435 * t1229 + 0.5805188177960e1 * t437 * t1227 - 0.17759960831940e2 * t437 * t1229 - 0.4439990207985e1 * t439 * t1227 + 0.7035868244370e1 * t439 * t1229 + 0.1407173648874e1 * t441 * t1227 - 0.973805419524e0 * t441 * t1229 - 0.162300903254e0 * t443 * t1227
  t1256 = t957 ** 2
  t1261 = f.my_piecewise3(t432, t1207, 0)
  t1265 = t955 ** 2
  t1271 = f.my_piecewise5(t423, (-params.c1 * t1208 * t428 - 0.2e1 * params.c1 * t1211 * t935 - 0.2e1 * t426 / t934 / t427 * t1211 - t426 * t935 * t1208) * t430 + t1224 * t430, t431, t1253, -0.2e1 * t267 / t955 / t449 * t1256 * t452 - t267 * t956 * t1261 * t452 - t641 / t1265 * t1256 * t452)
  t1297 = t383 * t1173
  t1309 = t1016 ** 2
  t1313 = t1027 ** 2
  t1322 = t986 * t474
  t1330 = t487 * t924
  t1334 = 0.4e1 * t470 * t1153 * t488 + 0.2e1 * t1203 * t471 * t488 + t1271 * t455 - 0.2e1 * t1003 * t1006 * (0.12e2 * t471 * t477 * t1153 + 0.32e2 / 0.3e1 * t1007 * t1012 * t924 * t927 + 0.4e1 * t1008 * t1163 + 0.20e2 / 0.9e1 * t475 / t476 / t473 * t1174 - 0.44e2 / 0.9e1 * t1013 * t1177) + 0.2e1 * t1003 * t480 * (-0.2e1 * t1183 * t165 - 0.2e1 * t1020 * t1188 - 0.19e2 / 0.324e3 * t40 * t1297 * t169) * t487 + 0.4e1 * t1003 / t1004 / t479 * t487 * t1309 + 0.2e1 * t1003 * t480 * t1313 * t487 + 0.8e1 * t985 * t416 * t474 * t992 - 0.4e1 * t1322 * t1017 + 0.4e1 * t1322 * t1029 + 0.4e1 * t990 * t991 * t1163 + 0.8e1 * t990 * t1028 * t1330
  t1345 = 0.1e1 / t900 / t406
  t1347 = t918 ** 2
  t1356 = t383 ** 2
  t1369 = 0.43950443928901157407407407407407407407407407407407e-2 * t904 / t905 / t384 * t51 * t394 - 0.34881304705477109053497942386831275720164609053498e-5 * t214 * t1356 * s2 / t387 / t905 / t1171 * t774 * t39 * t394 + 0.11e2 / 0.27e2 * t398 * t1180
  t1405 = -0.4e1 * t1003 * t1005 * t1027 * t487 * t1016 - 0.8e1 * t990 * t1006 * t924 * t1016 - 0.2e1 * t208 * t1345 * t1347 + t902 * t1369 - 0.2e1 * t961 * t208 * t964 - t963 * t901 * t1369 + 0.2e1 * t963 * t1345 * t1347 - 0.44e2 / 0.9e1 * t998 * t999 * t1161 + 0.8e1 / 0.3e1 * t986 * t997 * t1000 + 0.4e1 / 0.3e1 * t472 * t477 * t480 * t487 * t571 * t1297 + 0.16e2 / 0.3e1 * t989 * t997 * t1330 * t927 - 0.8e1 / 0.3e1 * t472 * t996 * t1005 * t999 * t922 * t1016 + 0.8e1 / 0.3e1 * t998 * t1027 * t487 * t927
  t1440 = -0.3e1 / 0.8e1 * t5 * t1139 * t504 - t1090 / 0.4e1 - 0.3e1 / 0.4e1 * t897 * t1034 - 0.49479000000000000000000000000000000000000000000000e1 * t354 * t896 * t31 * t491 * t1048 + t877 - t1097 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t1107 - 0.3e1 / 0.8e1 * t509 * t31 * (t1334 + t1405) * t503 - 0.49479000000000000000000000000000000000000000000000e1 * t354 * t1037 * t1032 * t1048 - 0.49479000000000000000000000000000000000000000000000e1 * t1039 / t498 / t827 / t414 * t34 * t61 * t1161 * t502 + 0.57725500000000000000000000000000000000000000000000e1 * t1039 * t1043 * t493 / t387 / t912 * t502 + 0.81605714700000000000000000000000000000000000000000e1 * t847 * t1038 / t493 / t400 * t827 * t502
  t1441 = f.my_piecewise3(t372, 0, t1440)
  d22 = 0.2e1 * t891 + 0.2e1 * t1052 + t6 * (t1130 + t1441)
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r
  s0 = s[0] if s is not None else None
  s1 = s[1] if s is not None else None
  s2 = s[2] if s is not None else None
  l0 = l[0] if l is not None else None
  l1 = l[1] if l is not None else None
  tau0 = tau[0] if tau is not None else None
  tau1 = tau[1] if tau is not None else None

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = 0.1e1 / t22
  t24 = t6 ** 2
  t25 = 0.1e1 / t24
  t27 = -t16 * t25 + t7
  t28 = f.my_piecewise5(t10, 0, t14, 0, t27)
  t29 = t28 ** 2
  t33 = 0.1e1 / t24 / t6
  t36 = 0.2e1 * t16 * t33 - 0.2e1 * t25
  t37 = f.my_piecewise5(t10, 0, t14, 0, t36)
  t41 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t23 * t29 + 0.4e1 / 0.3e1 * t21 * t37)
  t42 = t5 * t41
  t43 = t6 ** (0.1e1 / 0.3e1)
  t45 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t50 = t49 * t48
  t51 = 0.1e1 / t50
  t52 = t47 * t51
  t53 = s0 ** 2
  t54 = r0 ** 2
  t55 = t54 ** 2
  t56 = t55 * r0
  t57 = r0 ** (0.1e1 / 0.3e1)
  t59 = 0.1e1 / t57 / t56
  t60 = t53 * t59
  t61 = params.dp2 ** 2
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t67 = jnp.exp(-t52 * t60 * t63 / 0.576e3)
  t71 = (-0.162742215233874e0 * t45 * t67 + 0.10e2 / 0.81e2) * t46
  t72 = t49 ** 2
  t73 = 0.1e1 / t72
  t74 = t73 * s0
  t75 = t57 ** 2
  t77 = 0.1e1 / t75 / t54
  t78 = t74 * t77
  t81 = params.k1 + t71 * t78 / 0.24e2
  t85 = params.k1 * (0.1e1 - params.k1 / t81)
  t87 = 0.1e1 / t75 / r0
  t89 = s0 * t77
  t91 = tau0 * t87 - t89 / 0.8e1
  t93 = 0.3e1 / 0.10e2 * t47 * t72
  t94 = params.eta * s0
  t97 = t93 + t94 * t77 / 0.8e1
  t98 = 0.1e1 / t97
  t99 = t91 * t98
  t100 = t99 <= 0.0e0
  t101 = 0.0e0 < t99
  t102 = f.my_piecewise3(t101, 0, t99)
  t103 = params.c1 * t102
  t104 = 0.1e1 - t102
  t105 = 0.1e1 / t104
  t107 = jnp.exp(-t103 * t105)
  t108 = t99 <= 0.25e1
  t109 = 0.25e1 < t99
  t110 = f.my_piecewise3(t109, 0.25e1, t99)
  t112 = t110 ** 2
  t114 = t112 * t110
  t116 = t112 ** 2
  t118 = t116 * t110
  t120 = t116 * t112
  t125 = f.my_piecewise3(t109, t99, 0.25e1)
  t126 = 0.1e1 - t125
  t129 = jnp.exp(params.c2 / t126)
  t131 = f.my_piecewise5(t100, t107, t108, 0.1e1 - 0.667e0 * t110 - 0.4445555e0 * t112 - 0.663086601049e0 * t114 + 0.1451297044490e1 * t116 - 0.887998041597e0 * t118 + 0.234528941479e0 * t120 - 0.23185843322e-1 * t116 * t114, -params.d * t129)
  t132 = 0.174e0 - t85
  t135 = t45 * t46
  t138 = 0.1e1 - t99
  t139 = t138 ** 2
  t144 = (0.40570770199022687796862290864197530864197530864200e-1 - 0.30235468026081006356817095666666666666666666666667e0 * params.eta) * t46 * t73
  t150 = (0.3e1 / 0.4e1 * params.eta + 0.2e1 / 0.3e1) ** 2
  t155 = (0.290700106132790123456790123456790123456790123457e-2 - 0.27123702538979000000000000000000000000000000000000e0 * params.eta) ** 2
  t159 = (0.146e3 / 0.2025e4 * t150 - 0.73e2 / 0.540e3 * params.eta - 0.146e3 / 0.1215e4 + t155 / params.k1) * t47
  t160 = t51 * t53
  t164 = -0.162742215233874e0 + 0.162742215233874e0 * t99 + 0.67809256347447500000000000000000000000000000000000e-2 * t135 * t78 - 0.59353125082804000000000000000000000000000000000000e-1 * t139 + t144 * t89 * t138 / 0.24e2 + t159 * t160 * t59 / 0.576e3
  t165 = t91 ** 2
  t166 = t164 * t165
  t167 = t97 ** 2
  t168 = 0.1e1 / t167
  t169 = t165 ** 2
  t170 = t167 ** 2
  t171 = 0.1e1 / t170
  t173 = t169 * t171 + 0.1e1
  t174 = 0.1e1 / t173
  t176 = params.da4 ** 2
  t177 = 0.1e1 / t176
  t179 = params.dp4 ** 2
  t180 = t179 ** 2
  t181 = 0.1e1 / t180
  t186 = jnp.exp(-t139 * t177 - t52 * t60 * t181 / 0.576e3)
  t187 = t168 * t174 * t186
  t190 = t131 * t132 + 0.2e1 * t166 * t187 + t85 + 0.1e1
  t192 = jnp.sqrt(0.3e1)
  t193 = 0.1e1 / t49
  t194 = t47 * t193
  t195 = jnp.sqrt(s0)
  t199 = t194 * t195 / t57 / r0
  t200 = jnp.sqrt(t199)
  t204 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t192 / t200)
  t205 = 0.1e1 - t204
  t206 = t43 * t190 * t205
  t211 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t212 = t5 * t211
  t213 = t43 ** 2
  t214 = 0.1e1 / t213
  t216 = t214 * t190 * t205
  t219 = params.k1 ** 2
  t220 = t81 ** 2
  t221 = 0.1e1 / t220
  t222 = t219 * t221
  t223 = t48 ** 2
  t225 = t45 / t223
  t226 = t53 * s0
  t227 = t225 * t226
  t228 = t55 ** 2
  t235 = t54 * r0
  t237 = 0.1e1 / t75 / t235
  t238 = t74 * t237
  t241 = -0.37671809081915277777777777777777777777777777777778e-3 * t227 / t228 / r0 * t63 * t67 - t71 * t238 / 0.9e1
  t245 = s0 * t237
  t247 = -0.5e1 / 0.3e1 * tau0 * t77 + t245 / 0.3e1
  t248 = t247 * t98
  t249 = t91 * t168
  t250 = t94 * t237
  t251 = t249 * t250
  t253 = t248 + t251 / 0.3e1
  t254 = f.my_piecewise3(t101, 0, t253)
  t257 = t104 ** 2
  t258 = 0.1e1 / t257
  t259 = t258 * t254
  t261 = -params.c1 * t254 * t105 - t103 * t259
  t263 = f.my_piecewise3(t109, 0, t253)
  t265 = t110 * t263
  t267 = t112 * t263
  t269 = t114 * t263
  t271 = t116 * t263
  t273 = t118 * t263
  t278 = params.d * params.c2
  t279 = t126 ** 2
  t280 = 0.1e1 / t279
  t281 = f.my_piecewise3(t109, t253, 0)
  t285 = f.my_piecewise5(t100, t261 * t107, t108, -0.667e0 * t263 - 0.8891110e0 * t265 - 0.1989259803147e1 * t267 + 0.5805188177960e1 * t269 - 0.4439990207985e1 * t271 + 0.1407173648874e1 * t273 - 0.162300903254e0 * t120 * t263, -t278 * t280 * t281 * t129)
  t287 = t131 * t219
  t288 = t221 * t241
  t294 = -t253
  t305 = 0.1e1 / t57 / t55 / t54
  t309 = 0.162742215233874e0 * t248 + 0.54247405077958000000000000000000000000000000000000e-1 * t251 - 0.18082468359319333333333333333333333333333333333333e-1 * t135 * t238 - 0.11870625016560800000000000000000000000000000000000e0 * t138 * t294 - t144 * t245 * t138 / 0.9e1 + t144 * t89 * t294 / 0.24e2 - t159 * t160 * t305 / 0.108e3
  t310 = t309 * t165
  t313 = t164 * t91
  t314 = t313 * t168
  t315 = t174 * t186
  t316 = t315 * t247
  t319 = t167 * t97
  t320 = 0.1e1 / t319
  t321 = t320 * t174
  t322 = t166 * t321
  t323 = t186 * params.eta
  t324 = t323 * t245
  t327 = t166 * t168
  t328 = t173 ** 2
  t329 = 0.1e1 / t328
  t330 = t329 * t186
  t331 = t165 * t91
  t332 = t331 * t171
  t336 = 0.1e1 / t170 / t97
  t337 = t169 * t336
  t340 = 0.4e1 * t332 * t247 + 0.4e1 / 0.3e1 * t337 * t250
  t341 = t330 * t340
  t344 = t138 * t177
  t351 = -0.2e1 * t344 * t294 + t52 * t53 * t305 * t181 / 0.108e3
  t352 = t174 * t351
  t353 = t352 * t186
  t356 = t222 * t241 + t285 * t132 - t287 * t288 + 0.2e1 * t310 * t187 + 0.4e1 * t314 * t316 + 0.4e1 / 0.3e1 * t322 * t324 - 0.2e1 * t327 * t341 + 0.2e1 * t327 * t353
  t358 = t43 * t356 * t205
  t361 = 3 ** (0.1e1 / 0.6e1)
  t362 = t361 ** 2
  t363 = t362 ** 2
  t364 = t363 * t361
  t365 = t364 * t4
  t366 = t211 * t43
  t367 = t366 * t190
  t368 = t365 * t367
  t370 = 0.1e1 / t200 / t199
  t372 = t370 * t47 * t193
  t377 = t372 * t195 / t57 / t54 * t204
  t380 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t381 = t380 * f.p.zeta_threshold
  t383 = f.my_piecewise3(t20, t381, t21 * t19)
  t384 = t5 * t383
  t386 = 0.1e1 / t213 / t6
  t388 = t386 * t190 * t205
  t392 = t214 * t356 * t205
  t395 = t383 * t214
  t396 = t395 * t190
  t397 = t365 * t396
  t403 = 0.1e1 / t75 / t55
  t404 = s0 * t403
  t406 = 0.40e2 / 0.9e1 * tau0 * t237 - 0.11e2 / 0.9e1 * t404
  t407 = t406 * t98
  t408 = t247 * t168
  t409 = t408 * t250
  t411 = t91 * t320
  t412 = params.eta ** 2
  t413 = t412 * t53
  t414 = t55 * t235
  t416 = 0.1e1 / t57 / t414
  t417 = t413 * t416
  t418 = t411 * t417
  t420 = t94 * t403
  t421 = t249 * t420
  t423 = t407 + 0.2e1 / 0.3e1 * t409 + 0.2e1 / 0.9e1 * t418 - 0.11e2 / 0.9e1 * t421
  t424 = f.my_piecewise3(t101, 0, t423)
  t425 = params.c1 * t424
  t427 = t254 ** 2
  t432 = 0.1e1 / t257 / t104
  t438 = -t103 * t258 * t424 - 0.2e1 * t103 * t432 * t427 - 0.2e1 * params.c1 * t427 * t258 - t425 * t105
  t440 = t261 ** 2
  t443 = f.my_piecewise3(t109, 0, t423)
  t445 = t263 ** 2
  t469 = -0.667e0 * t443 - 0.8891110e0 * t445 - 0.8891110e0 * t110 * t443 - 0.3978519606294e1 * t110 * t445 - 0.1989259803147e1 * t112 * t443 + 0.17415564533880e2 * t112 * t445 + 0.5805188177960e1 * t114 * t443 - 0.17759960831940e2 * t114 * t445 - 0.4439990207985e1 * t116 * t443 + 0.7035868244370e1 * t116 * t445 + 0.1407173648874e1 * t118 * t443 - 0.973805419524e0 * t118 * t445 - 0.162300903254e0 * t120 * t443
  t471 = 0.1e1 / t279 / t126
  t472 = t281 ** 2
  t477 = f.my_piecewise3(t109, t423, 0)
  t481 = params.c2 ** 2
  t482 = params.d * t481
  t483 = t279 ** 2
  t484 = 0.1e1 / t483
  t489 = f.my_piecewise5(t100, t438 * t107 + t440 * t107, t108, t469, -t278 * t280 * t477 * t129 - 0.2e1 * t278 * t471 * t472 * t129 - t482 * t484 * t472 * t129)
  t492 = 0.1e1 / t220 / t81
  t493 = t241 ** 2
  t494 = t492 * t493
  t497 = t285 * t219
  t506 = t53 ** 2
  t507 = t506 * s0
  t513 = t62 ** 2
  t517 = 0.1e1 / t513 * t47 * t51 * t67
  t520 = t74 * t403
  t523 = 0.43950443928901157407407407407407407407407407407407e-2 * t227 / t228 / t54 * t63 * t67 - 0.34881304705477109053497942386831275720164609053498e-5 * t225 * t507 / t57 / t228 / t414 * t517 + 0.11e2 / 0.27e2 * t71 * t520
  t524 = t221 * t523
  t526 = t351 ** 2
  t527 = t174 * t526
  t528 = t527 * t186
  t531 = t315 * t406
  t534 = t165 * t171
  t535 = t247 ** 2
  t538 = t331 * t336
  t539 = t538 * t247
  t545 = 0.1e1 / t170 / t167
  t546 = t169 * t545
  t551 = 0.12e2 * t534 * t535 + 0.32e2 / 0.3e1 * t539 * t250 + 0.4e1 * t332 * t406 + 0.20e2 / 0.9e1 * t546 * t417 - 0.44e2 / 0.9e1 * t337 * t420
  t552 = t330 * t551
  t555 = t294 ** 2
  t558 = -t423
  t561 = t53 * t416
  t565 = -0.2e1 * t555 * t177 - 0.2e1 * t344 * t558 - 0.19e2 / 0.324e3 * t52 * t561 * t181
  t566 = t174 * t565
  t567 = t566 * t186
  t570 = t309 * t91
  t571 = t570 * t168
  t574 = t310 * t168
  t580 = 0.1e1 / t328 / t173
  t581 = t580 * t186
  t582 = t340 ** 2
  t583 = t581 * t582
  t586 = t489 * t132 + 0.2e1 * t287 * t494 - t287 * t524 - 0.2e1 * t497 * t288 + 0.4e1 * t314 * t531 + 0.8e1 * t571 * t316 + 0.2e1 * t327 * t528 - 0.2e1 * t327 * t552 + 0.2e1 * t327 * t567 + 0.4e1 * t327 * t583 - 0.4e1 * t574 * t341 + 0.4e1 * t574 * t353
  t588 = t219 * t492
  t591 = t164 * t535
  t615 = 0.162742215233874e0 * t407 + 0.10849481015591600000000000000000000000000000000000e0 * t409 + 0.36164936718638666666666666666666666666666666666667e-1 * t418 - 0.19890715195251266666666666666666666666666666666667e0 * t421 + 0.66302383984170888888888888888888888888888888888888e-1 * t135 * t520 - 0.11870625016560800000000000000000000000000000000000e0 * t555 - 0.11870625016560800000000000000000000000000000000000e0 * t138 * t558 + 0.11e2 / 0.27e2 * t144 * t404 * t138 - 0.2e1 / 0.9e1 * t144 * t245 * t294 + t144 * t89 * t558 / 0.24e2 + 0.19e2 / 0.324e3 * t159 * t160 * t416
  t616 = t615 * t165
  t619 = t310 * t321
  t622 = t323 * t404
  t625 = t171 * t174
  t626 = t166 * t625
  t627 = t186 * t412
  t628 = t627 * t561
  t631 = t320 * t329
  t632 = t166 * t631
  t634 = t323 * t245 * t340
  t637 = t351 * t186
  t638 = t637 * t250
  t641 = t313 * t321
  t642 = t186 * t247
  t643 = t642 * t250
  t646 = t247 * t340
  t647 = t330 * t646
  t650 = t352 * t642
  t653 = t329 * t351
  t654 = t186 * t340
  t655 = t653 * t654
  t658 = t222 * t523 - 0.2e1 * t588 * t493 + 0.4e1 * t591 * t187 + 0.2e1 * t616 * t187 + 0.8e1 / 0.3e1 * t619 * t324 - 0.44e2 / 0.9e1 * t322 * t622 + 0.4e1 / 0.3e1 * t626 * t628 - 0.8e1 / 0.3e1 * t632 * t634 + 0.8e1 / 0.3e1 * t322 * t638 + 0.16e2 / 0.3e1 * t641 * t643 - 0.8e1 * t314 * t647 + 0.8e1 * t314 * t650 - 0.4e1 * t327 * t655
  t659 = t586 + t658
  t661 = t43 * t659 * t205
  t664 = t383 * t43
  t665 = t664 * t356
  t666 = t365 * t665
  t669 = t664 * t190
  t670 = t365 * t669
  t671 = t46 * t73
  t677 = 0.1e1 / t200 / t671 / t89 * t46 * t73 / 0.6e1
  t679 = t677 * t404 * t204
  t686 = t372 * t195 / t57 / t235 * t204
  t689 = t3 ** 2
  t691 = t2 * t689 * jnp.pi
  t692 = t691 * t669
  t693 = 0.1e1 / t195
  t696 = t671 * t204
  t697 = t693 / t75 * t696
  t700 = -0.3e1 / 0.8e1 * t42 * t206 - t212 * t216 / 0.4e1 - 0.3e1 / 0.4e1 * t212 * t358 - 0.49479000000000000000000000000000000000000000000000e1 * t368 * t377 + t384 * t388 / 0.12e2 - t384 * t392 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t397 * t377 - 0.3e1 / 0.8e1 * t384 * t661 - 0.49479000000000000000000000000000000000000000000000e1 * t666 * t377 - 0.29687400000000000000000000000000000000000000000000e2 * t670 * t679 + 0.57725500000000000000000000000000000000000000000000e1 * t670 * t686 + 0.81605714700000000000000000000000000000000000000000e1 * t692 * t697
  t701 = f.my_piecewise3(t1, 0, t700)
  t703 = r1 <= f.p.dens_threshold
  t704 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t705 = 0.1e1 + t704
  t706 = t705 <= f.p.zeta_threshold
  t707 = t705 ** (0.1e1 / 0.3e1)
  t708 = t707 ** 2
  t709 = 0.1e1 / t708
  t711 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t712 = t711 ** 2
  t716 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t720 = f.my_piecewise3(t706, 0, 0.4e1 / 0.9e1 * t709 * t712 + 0.4e1 / 0.3e1 * t707 * t716)
  t721 = t5 * t720
  t722 = s2 ** 2
  t723 = r1 ** 2
  t724 = t723 ** 2
  t726 = r1 ** (0.1e1 / 0.3e1)
  t728 = 0.1e1 / t726 / t724 / r1
  t729 = t722 * t728
  t733 = jnp.exp(-t52 * t729 * t63 / 0.576e3)
  t739 = t726 ** 2
  t741 = 0.1e1 / t739 / t723
  t742 = t73 * s2 * t741
  t749 = params.k1 * (0.1e1 - params.k1 / (params.k1 + (-0.162742215233874e0 * t45 * t733 + 0.10e2 / 0.81e2) * t46 * t742 / 0.24e2))
  t753 = s2 * t741
  t755 = tau1 / t739 / r1 - t753 / 0.8e1
  t759 = t93 + params.eta * s2 * t741 / 0.8e1
  t761 = t755 / t759
  t764 = f.my_piecewise3(0.0e0 < t761, 0, t761)
  t769 = jnp.exp(-params.c1 * t764 / (0.1e1 - t764))
  t771 = 0.25e1 < t761
  t772 = f.my_piecewise3(t771, 0.25e1, t761)
  t774 = t772 ** 2
  t776 = t774 * t772
  t778 = t774 ** 2
  t787 = f.my_piecewise3(t771, t761, 0.25e1)
  t791 = jnp.exp(params.c2 / (0.1e1 - t787))
  t793 = f.my_piecewise5(t761 <= 0.0e0, t769, t761 <= 0.25e1, 0.1e1 - 0.667e0 * t772 - 0.4445555e0 * t774 - 0.663086601049e0 * t776 + 0.1451297044490e1 * t778 - 0.887998041597e0 * t778 * t772 + 0.234528941479e0 * t778 * t774 - 0.23185843322e-1 * t778 * t776, -params.d * t791)
  t799 = 0.1e1 - t761
  t800 = t799 ** 2
  t810 = t755 ** 2
  t812 = t759 ** 2
  t814 = t810 ** 2
  t815 = t812 ** 2
  t826 = jnp.exp(-t800 * t177 - t52 * t729 * t181 / 0.576e3)
  t830 = 0.1e1 + t749 + t793 * (0.174e0 - t749) + 0.2e1 * (-0.162742215233874e0 + 0.162742215233874e0 * t761 + 0.67809256347447500000000000000000000000000000000000e-2 * t135 * t742 - 0.59353125082804000000000000000000000000000000000000e-1 * t800 + t144 * t753 * t799 / 0.24e2 + t159 * t51 * t722 * t728 / 0.576e3) * t810 / t812 / (0.1e1 + t814 / t815) * t826
  t832 = jnp.sqrt(s2)
  t837 = jnp.sqrt(t194 * t832 / t726 / r1)
  t841 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t192 / t837)
  t842 = 0.1e1 - t841
  t843 = t43 * t830 * t842
  t848 = f.my_piecewise3(t706, 0, 0.4e1 / 0.3e1 * t707 * t711)
  t849 = t5 * t848
  t851 = t214 * t830 * t842
  t855 = f.my_piecewise3(t706, t381, t707 * t705)
  t856 = t5 * t855
  t858 = t386 * t830 * t842
  t862 = f.my_piecewise3(t703, 0, -0.3e1 / 0.8e1 * t721 * t843 - t849 * t851 / 0.4e1 + t856 * t858 / 0.12e2)
  t875 = 0.1e1 / t213 / t24
  t899 = 0.1e1 / t3 / t48
  t903 = t693 * t87
  t921 = -0.3e1 / 0.4e1 * t212 * t392 - 0.9e1 / 0.8e1 * t212 * t661 - 0.9e1 / 0.8e1 * t42 * t358 - 0.3e1 / 0.8e1 * t384 * t214 * t659 * t205 - 0.5e1 / 0.36e2 * t384 * t875 * t190 * t205 + t212 * t388 / 0.4e1 - 0.3e1 / 0.8e1 * t42 * t216 + t384 * t386 * t356 * t205 / 0.4e1 - 0.32302153261130400000000000000000000000000000000000e3 * t365 * t664 * t190 / t235 * t370 * t204 + 0.24481714410000000000000000000000000000000000000000e2 * t691 * t665 * t697 + 0.16321142940000000000000000000000000000000000000000e2 * t2 * t899 * t669 * t46 * t50 * t903 * t204 - 0.24481714410000000000000000000000000000000000000000e2 * t692 * t903 * t696 + 0.24481714410000000000000000000000000000000000000000e2 * t691 * t367 * t697 + 0.81605714700000000000000000000000000000000000000000e1 * t691 * t396 * t697 - 0.74218500000000000000000000000000000000000000000000e1 * t365 * t664 * t659 * t377
  t961 = 0.1e1 / t75 / t56
  t962 = s0 * t961
  t974 = t195 * s0
  t996 = t24 ** 2
  t1000 = 0.6e1 * t33 - 0.6e1 * t16 / t996
  t1001 = f.my_piecewise5(t10, 0, t14, 0, t1000)
  t1005 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t1001)
  t1009 = t186 * t565
  t1019 = -0.440e3 / 0.27e2 * tau0 * t403 + 0.154e3 / 0.27e2 * t962
  t1020 = t1019 * t98
  t1022 = t406 * t168 * t250
  t1024 = t247 * t320 * t417
  t1026 = t408 * t420
  t1028 = t91 * t171
  t1029 = t412 * params.eta
  t1032 = 0.1e1 / t228 / t235
  t1033 = t1029 * t226 * t1032
  t1034 = t1028 * t1033
  t1037 = 0.1e1 / t57 / t228
  t1038 = t413 * t1037
  t1039 = t411 * t1038
  t1041 = t94 * t961
  t1042 = t249 * t1041
  t1044 = -t1020 - t1022 - 0.2e1 / 0.3e1 * t1024 + 0.11e2 / 0.3e1 * t1026 - 0.2e1 / 0.9e1 * t1034 + 0.22e2 / 0.9e1 * t1039 - 0.154e3 / 0.27e2 * t1042
  t1047 = t53 * t1037
  t1093 = t591 * t168
  t1100 = t328 ** 2
  t1114 = t616 * t168
  t1125 = t220 ** 2
  t1126 = 0.1e1 / t1125
  t1127 = t493 * t241
  t1135 = 0.6e1 * t327 * t352 * t1009 + 0.2e1 * t327 * t174 * (-0.6e1 * t294 * t177 * t558 - 0.2e1 * t344 * t1044 + 0.209e3 / 0.486e3 * t52 * t1047 * t181) * t186 + 0.4e1 * t314 * t315 * t1019 - 0.2e1 * t327 * t330 * (0.24e2 * t1028 * t535 * t247 + 0.48e2 * t165 * t336 * t535 * t250 + 0.36e2 * t534 * t247 * t406 + 0.80e2 / 0.3e1 * t331 * t545 * t247 * t417 + 0.16e2 * t538 * t406 * t250 - 0.176e3 / 0.3e1 * t539 * t420 + 0.4e1 * t332 * t1019 + 0.40e2 / 0.9e1 * t169 / t170 / t319 * t1033 - 0.220e3 / 0.9e1 * t546 * t1038 + 0.616e3 / 0.27e2 * t337 * t1041) + 0.12e2 * t1093 * t353 + 0.12e2 * t574 * t583 + 0.6e1 * t574 * t528 - 0.12e2 * t327 / t1100 * t186 * t582 * t340 + 0.2e1 * t327 * t174 * t526 * t351 * t186 - 0.12e2 * t1093 * t341 + 0.6e1 * t1114 * t353 - 0.6e1 * t574 * t552 + 0.12e2 * t615 * t91 * t168 * t316 + 0.6e1 * t574 * t567 - 0.6e1 * t287 * t1126 * t1127 + 0.6e1 * t497 * t494 - 0.3e1 * t497 * t524
  t1140 = t228 ** 2
  t1162 = t74 * t961
  t1165 = -0.47633909705799540123456790123456790123456790123456e-1 * t227 * t1032 * t63 * t67 + 0.94179522704788194444444444444444444444444444444444e-4 * t225 * t507 / t57 / t1140 * t517 - 0.19378502614153949474165523548239597622313671696388e-6 * t225 * t506 * t226 / t75 / t1140 / t56 / t513 / t62 * t46 / t72 / t223 * t67 - 0.154e3 / 0.81e2 * t71 * t1162
  t1202 = 0.162742215233874e0 * t1020 + 0.16274221523387400000000000000000000000000000000000e0 * t1022 + 0.10849481015591600000000000000000000000000000000000e0 * t1024 - 0.59672145585753800000000000000000000000000000000000e0 * t1026 + 0.36164936718638666666666666666666666666666666666667e-1 * t1034 - 0.39781430390502533333333333333333333333333333333334e0 * t1039 + 0.92823337577839244444444444444444444444444444444446e0 * t1042 - 0.30941112525946414814814814814814814814814814814814e0 * t135 * t1162 - 0.35611875049682400000000000000000000000000000000000e0 * t294 * t558 - 0.11870625016560800000000000000000000000000000000000e0 * t138 * t1044 - 0.154e3 / 0.81e2 * t144 * t962 * t138 + 0.11e2 / 0.9e1 * t144 * t404 * t294 - t144 * t245 * t558 / 0.3e1 + t144 * t89 * t1044 / 0.24e2 - 0.209e3 / 0.486e3 * t159 * t160 * t1037
  t1221 = -t1044
  t1222 = f.my_piecewise3(t101, 0, t1221)
  t1227 = t427 * t254
  t1231 = t257 ** 2
  t1250 = f.my_piecewise3(t109, 0, t1221)
  t1256 = t445 * t263
  t1286 = -0.667e0 * t1250 - 0.26673330e1 * t263 * t443 - 0.8891110e0 * t110 * t1250 - 0.3978519606294e1 * t1256 - 0.11935558818882e2 * t265 * t443 - 0.1989259803147e1 * t112 * t1250 + 0.34831129067760e2 * t110 * t1256 + 0.52246693601640e2 * t267 * t443 + 0.5805188177960e1 * t114 * t1250 - 0.53279882495820e2 * t112 * t1256 - 0.53279882495820e2 * t269 * t443 - 0.4439990207985e1 * t116 * t1250 + 0.28143472977480e2 * t114 * t1256 + 0.21107604733110e2 * t271 * t443 + 0.1407173648874e1 * t118 * t1250 - 0.4869027097620e1 * t116 * t1256 - 0.2921416258572e1 * t273 * t443 - 0.162300903254e0 * t120 * t1250
  t1287 = t472 * t281
  t1294 = t281 * t129 * t477
  t1303 = f.my_piecewise3(t109, t1221, 0)
  t1318 = f.my_piecewise5(t100, (-params.c1 * t1222 * t105 - 0.6e1 * t425 * t259 - 0.6e1 * params.c1 * t1227 * t432 - 0.6e1 * t103 / t1231 * t1227 - 0.6e1 * t103 * t432 * t254 * t424 - t103 * t258 * t1222) * t107 + 0.3e1 * t438 * t261 * t107 + t440 * t261 * t107, t108, t1286, -0.6e1 * t278 * t484 * t1287 * t129 - 0.6e1 * t278 * t471 * t1294 - 0.6e1 * t482 / t483 / t126 * t1287 * t129 - t278 * t280 * t1303 * t129 - 0.3e1 * t482 * t484 * t1294 - params.d * t481 * params.c2 / t483 / t279 * t1287 * t129)
  t1347 = -t287 * t221 * t1165 - 0.3e1 * t489 * t219 * t288 - 0.6e1 * t588 * t241 * t523 + 0.2e1 * t1202 * t165 * t187 + 0.12e2 * t309 * t535 * t187 + 0.6e1 * t287 * t492 * t241 * t523 + 0.12e2 * t571 * t531 - 0.6e1 * t1114 * t341 + 0.12e2 * t164 * t247 * t168 * t531 + t1318 * t132 - 0.24e2 * t313 * t168 * t329 * t637 * t646 - 0.44e2 / 0.3e1 * t626 * t627 * t1047 + 0.16e2 / 0.9e1 * t166 * t336 * t174 * t186 * t1029 * t226 * t1032 + 0.8e1 * t591 * t321 * t324 + 0.4e1 * t616 * t321 * t324 + 0.4e1 * t310 * t625 * t628 + 0.616e3 / 0.27e2 * t322 * t323 * t962
  t1369 = t186 * t406
  t1406 = t186 * t582
  t1417 = -0.44e2 / 0.3e1 * t619 * t622 - 0.8e1 * t166 * t631 * t351 * t634 + 0.16e2 * t313 * t321 * t351 * t643 - 0.16e2 * t313 * t631 * t186 * t94 * t237 * t340 * t247 + 0.4e1 * t322 * t1009 * t250 + 0.8e1 * t641 * t1369 * t250 + 0.8e1 * t619 * t638 - 0.88e2 / 0.3e1 * t641 * t323 * t404 * t247 + 0.44e2 / 0.3e1 * t632 * t323 * t404 * t340 - 0.44e2 / 0.3e1 * t322 * t637 * t420 + 0.8e1 * t313 * t625 * t627 * t561 * t247 - 0.4e1 * t166 * t171 * t329 * t627 * t561 * t340 + 0.4e1 * t626 * t637 * t417 - 0.4e1 * t632 * t323 * t245 * t551 + 0.8e1 * t166 * t320 * t580 * t1406 * t250 + 0.4e1 * t322 * t526 * t186 * t250 + 0.16e2 * t570 * t321 * t643
  t1472 = -0.8e1 * t310 * t631 * t634 + 0.6e1 * t219 * t1126 * t1127 + t222 * t1165 - 0.6e1 * t327 * t653 * t186 * t551 - 0.12e2 * t574 * t655 - 0.12e2 * t314 * t330 * t406 * t340 - 0.12e2 * t314 * t330 * t247 * t551 + 0.12e2 * t314 * t566 * t642 + 0.12e2 * t314 * t352 * t1369 - 0.24e2 * t571 * t647 + 0.24e2 * t571 * t650 + 0.24e2 * t314 * t581 * t582 * t247 + 0.12e2 * t327 * t581 * t340 * t551 + 0.12e2 * t327 * t580 * t351 * t1406 + 0.12e2 * t314 * t527 * t642 - 0.6e1 * t327 * t329 * t526 * t654 - 0.6e1 * t327 * t329 * t565 * t654
  t1479 = -0.89062200000000000000000000000000000000000000000000e2 * t666 * t679 - 0.74218500000000000000000000000000000000000000000000e1 * t365 * t41 * t43 * t190 * t377 - 0.49479000000000000000000000000000000000000000000000e1 * t365 * t211 * t214 * t190 * t377 - 0.14843700000000000000000000000000000000000000000000e2 * t365 * t366 * t356 * t377 - 0.89062200000000000000000000000000000000000000000000e2 * t368 * t679 + 0.16493000000000000000000000000000000000000000000000e1 * t365 * t383 * t386 * t190 * t377 - 0.49479000000000000000000000000000000000000000000000e1 * t365 * t395 * t356 * t377 - 0.29687400000000000000000000000000000000000000000000e2 * t397 * t679 - 0.19241833333333333333333333333333333333333333333333e2 * t670 * t372 * t195 / t57 / t55 * t204 + 0.17317650000000000000000000000000000000000000000000e2 * t666 * t686 + 0.20781180000000000000000000000000000000000000000000e3 * t670 * t677 * t962 * t204 + 0.57725500000000000000000000000000000000000000000000e1 * t397 * t686 + 0.17317650000000000000000000000000000000000000000000e2 * t368 * t686 - 0.16493000000000000000000000000000000000000000000000e2 * t364 * t899 * t664 * t190 / t200 * t48 * t55 / t414 * t204 - 0.3e1 / 0.8e1 * t5 * t1005 * t206 - 0.3e1 / 0.8e1 * t384 * t43 * (t1135 + t1347 + t1417 + t1472) * t205
  t1481 = f.my_piecewise3(t1, 0, t921 + t1479)
  t1491 = f.my_piecewise5(t14, 0, t10, 0, -t1000)
  t1495 = f.my_piecewise3(t706, 0, -0.8e1 / 0.27e2 / t708 / t705 * t712 * t711 + 0.4e1 / 0.3e1 * t709 * t711 * t716 + 0.4e1 / 0.3e1 * t707 * t1491)
  t1508 = f.my_piecewise3(t703, 0, -0.3e1 / 0.8e1 * t5 * t1495 * t843 - 0.3e1 / 0.8e1 * t721 * t851 + t849 * t858 / 0.4e1 - 0.5e1 / 0.36e2 * t856 * t875 * t830 * t842)
  d111 = 0.3e1 * t701 + 0.3e1 * t862 + t6 * (t1481 + t1508)

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r
  s0 = s[0] if s is not None else None
  s1 = s[1] if s is not None else None
  s2 = s[2] if s is not None else None
  l0 = l[0] if l is not None else None
  l1 = l[1] if l is not None else None
  tau0 = tau[0] if tau is not None else None
  tau1 = tau[1] if tau is not None else None

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.6e1)
  t3 = t2 ** 2
  t4 = t3 ** 2
  t5 = t4 * t2
  t6 = jnp.pi ** 2
  t7 = jnp.pi ** (0.1e1 / 0.3e1)
  t9 = 0.1e1 / t7 / t6
  t10 = t5 * t9
  t11 = r0 + r1
  t12 = 0.1e1 / t11
  t15 = 0.2e1 * r0 * t12 <= f.p.zeta_threshold
  t16 = f.p.zeta_threshold - 0.1e1
  t19 = 0.2e1 * r1 * t12 <= f.p.zeta_threshold
  t20 = -t16
  t21 = r0 - r1
  t22 = t21 * t12
  t23 = f.my_piecewise5(t15, t16, t19, t20, t22)
  t24 = 0.1e1 + t23
  t25 = t24 <= f.p.zeta_threshold
  t26 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t27 = t26 * f.p.zeta_threshold
  t28 = t24 ** (0.1e1 / 0.3e1)
  t30 = f.my_piecewise3(t25, t27, t28 * t24)
  t31 = t11 ** (0.1e1 / 0.3e1)
  t32 = t30 * t31
  t33 = t10 * t32
  t35 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t36 = 6 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = t6 ** (0.1e1 / 0.3e1)
  t39 = t38 * t6
  t40 = 0.1e1 / t39
  t41 = t37 * t40
  t42 = s0 ** 2
  t43 = r0 ** 2
  t44 = t43 ** 2
  t45 = t44 * r0
  t46 = r0 ** (0.1e1 / 0.3e1)
  t48 = 0.1e1 / t46 / t45
  t49 = t42 * t48
  t50 = params.dp2 ** 2
  t51 = t50 ** 2
  t52 = 0.1e1 / t51
  t56 = jnp.exp(-t41 * t49 * t52 / 0.576e3)
  t60 = (-0.162742215233874e0 * t35 * t56 + 0.10e2 / 0.81e2) * t36
  t61 = t38 ** 2
  t62 = 0.1e1 / t61
  t63 = t62 * s0
  t64 = t46 ** 2
  t66 = 0.1e1 / t64 / t43
  t67 = t63 * t66
  t70 = params.k1 + t60 * t67 / 0.24e2
  t74 = params.k1 * (0.1e1 - params.k1 / t70)
  t76 = 0.1e1 / t64 / r0
  t78 = s0 * t66
  t80 = tau0 * t76 - t78 / 0.8e1
  t82 = 0.3e1 / 0.10e2 * t37 * t61
  t83 = params.eta * s0
  t86 = t82 + t83 * t66 / 0.8e1
  t87 = 0.1e1 / t86
  t88 = t80 * t87
  t89 = t88 <= 0.0e0
  t90 = 0.0e0 < t88
  t91 = f.my_piecewise3(t90, 0, t88)
  t92 = params.c1 * t91
  t93 = 0.1e1 - t91
  t94 = 0.1e1 / t93
  t96 = jnp.exp(-t92 * t94)
  t97 = t88 <= 0.25e1
  t98 = 0.25e1 < t88
  t99 = f.my_piecewise3(t98, 0.25e1, t88)
  t101 = t99 ** 2
  t103 = t101 * t99
  t105 = t101 ** 2
  t107 = t105 * t99
  t109 = t105 * t101
  t114 = f.my_piecewise3(t98, t88, 0.25e1)
  t115 = 0.1e1 - t114
  t118 = jnp.exp(params.c2 / t115)
  t120 = f.my_piecewise5(t89, t96, t97, 0.1e1 - 0.667e0 * t99 - 0.4445555e0 * t101 - 0.663086601049e0 * t103 + 0.1451297044490e1 * t105 - 0.887998041597e0 * t107 + 0.234528941479e0 * t109 - 0.23185843322e-1 * t105 * t103, -params.d * t118)
  t121 = 0.174e0 - t74
  t124 = t35 * t36
  t127 = 0.1e1 - t88
  t128 = t127 ** 2
  t133 = (0.40570770199022687796862290864197530864197530864200e-1 - 0.30235468026081006356817095666666666666666666666667e0 * params.eta) * t36 * t62
  t139 = (0.3e1 / 0.4e1 * params.eta + 0.2e1 / 0.3e1) ** 2
  t144 = (0.290700106132790123456790123456790123456790123457e-2 - 0.27123702538979000000000000000000000000000000000000e0 * params.eta) ** 2
  t148 = (0.146e3 / 0.2025e4 * t139 - 0.73e2 / 0.540e3 * params.eta - 0.146e3 / 0.1215e4 + t144 / params.k1) * t37
  t149 = t40 * t42
  t153 = -0.162742215233874e0 + 0.162742215233874e0 * t88 + 0.67809256347447500000000000000000000000000000000000e-2 * t124 * t67 - 0.59353125082804000000000000000000000000000000000000e-1 * t128 + t133 * t78 * t127 / 0.24e2 + t148 * t149 * t48 / 0.576e3
  t154 = t80 ** 2
  t155 = t153 * t154
  t156 = t86 ** 2
  t157 = 0.1e1 / t156
  t158 = t154 ** 2
  t159 = t156 ** 2
  t160 = 0.1e1 / t159
  t162 = t158 * t160 + 0.1e1
  t163 = 0.1e1 / t162
  t164 = t157 * t163
  t165 = params.da4 ** 2
  t166 = 0.1e1 / t165
  t168 = params.dp4 ** 2
  t169 = t168 ** 2
  t170 = 0.1e1 / t169
  t175 = jnp.exp(-t128 * t166 - t41 * t49 * t170 / 0.576e3)
  t176 = t164 * t175
  t179 = t120 * t121 + 0.2e1 * t155 * t176 + t74 + 0.1e1
  t181 = jnp.sqrt(s0)
  t182 = t181 * s0
  t184 = 0.1e1 / t44
  t187 = 0.1e1 / t38
  t188 = t37 * t187
  t190 = 0.1e1 / t46 / r0
  t192 = t188 * t181 * t190
  t193 = jnp.sqrt(t192)
  t195 = 0.1e1 / t193 * t6 / t182 / t184 / 0.36e2
  t196 = t179 * t195
  t197 = t43 * r0
  t198 = t44 * t197
  t201 = jnp.sqrt(0.3e1)
  t205 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t201 / t193)
  t206 = t182 / t198 * t205
  t207 = t196 * t206
  t210 = 3 ** (0.1e1 / 0.3e1)
  t211 = 0.1e1 / t7
  t212 = t210 * t211
  t213 = t28 ** 2
  t214 = 0.1e1 / t213
  t215 = t11 ** 2
  t216 = 0.1e1 / t215
  t218 = -t21 * t216 + t12
  t219 = f.my_piecewise5(t15, 0, t19, 0, t218)
  t220 = t219 ** 2
  t223 = t215 * t11
  t224 = 0.1e1 / t223
  t227 = 0.2e1 * t21 * t224 - 0.2e1 * t216
  t228 = f.my_piecewise5(t15, 0, t19, 0, t227)
  t232 = f.my_piecewise3(t25, 0, 0.4e1 / 0.9e1 * t214 * t220 + 0.4e1 / 0.3e1 * t28 * t228)
  t233 = t212 * t232
  t234 = params.k1 ** 2
  t235 = t70 ** 2
  t236 = 0.1e1 / t235
  t237 = t234 * t236
  t238 = t6 ** 2
  t240 = t35 / t238
  t241 = t42 * s0
  t242 = t240 * t241
  t243 = t44 ** 2
  t244 = t243 * r0
  t251 = 0.1e1 / t64 / t197
  t252 = t63 * t251
  t255 = -0.37671809081915277777777777777777777777777777777778e-3 * t242 / t244 * t52 * t56 - t60 * t252 / 0.9e1
  t259 = s0 * t251
  t261 = -0.5e1 / 0.3e1 * tau0 * t66 + t259 / 0.3e1
  t262 = t261 * t87
  t263 = t80 * t157
  t264 = t83 * t251
  t265 = t263 * t264
  t267 = t262 + t265 / 0.3e1
  t268 = f.my_piecewise3(t90, 0, t267)
  t271 = t93 ** 2
  t272 = 0.1e1 / t271
  t273 = t272 * t268
  t275 = -params.c1 * t268 * t94 - t92 * t273
  t277 = f.my_piecewise3(t98, 0, t267)
  t279 = t99 * t277
  t281 = t101 * t277
  t283 = t103 * t277
  t285 = t105 * t277
  t287 = t107 * t277
  t292 = params.d * params.c2
  t293 = t115 ** 2
  t294 = 0.1e1 / t293
  t295 = f.my_piecewise3(t98, t267, 0)
  t299 = f.my_piecewise5(t89, t275 * t96, t97, -0.667e0 * t277 - 0.8891110e0 * t279 - 0.1989259803147e1 * t281 + 0.5805188177960e1 * t283 - 0.4439990207985e1 * t285 + 0.1407173648874e1 * t287 - 0.162300903254e0 * t109 * t277, -t292 * t294 * t295 * t118)
  t301 = t120 * t234
  t302 = t236 * t255
  t308 = -t267
  t317 = t44 * t43
  t319 = 0.1e1 / t46 / t317
  t323 = 0.162742215233874e0 * t262 + 0.54247405077958000000000000000000000000000000000000e-1 * t265 - 0.18082468359319333333333333333333333333333333333333e-1 * t124 * t252 - 0.11870625016560800000000000000000000000000000000000e0 * t127 * t308 - t133 * t259 * t127 / 0.9e1 + t133 * t78 * t308 / 0.24e2 - t148 * t149 * t319 / 0.108e3
  t324 = t323 * t154
  t327 = t153 * t80
  t328 = t327 * t157
  t329 = t163 * t175
  t330 = t329 * t261
  t333 = t156 * t86
  t334 = 0.1e1 / t333
  t335 = t334 * t163
  t336 = t155 * t335
  t337 = t175 * params.eta
  t338 = t337 * t259
  t341 = t155 * t157
  t342 = t162 ** 2
  t343 = 0.1e1 / t342
  t344 = t343 * t175
  t345 = t154 * t80
  t346 = t345 * t160
  t350 = 0.1e1 / t159 / t86
  t351 = t158 * t350
  t354 = 0.4e1 * t346 * t261 + 0.4e1 / 0.3e1 * t351 * t264
  t355 = t344 * t354
  t358 = t127 * t166
  t365 = -0.2e1 * t358 * t308 + t41 * t42 * t319 * t170 / 0.108e3
  t366 = t163 * t365
  t367 = t366 * t175
  t370 = t237 * t255 + t299 * t121 - t301 * t302 + 0.2e1 * t324 * t176 + 0.4e1 * t328 * t330 + 0.4e1 / 0.3e1 * t336 * t338 - 0.2e1 * t341 * t355 + 0.2e1 * t341 * t367
  t372 = 0.1e1 - t205
  t373 = t31 * t370 * t372
  t377 = 0.1e1 / t213 / t24
  t381 = t214 * t219
  t384 = t215 ** 2
  t385 = 0.1e1 / t384
  t388 = -0.6e1 * t21 * t385 + 0.6e1 * t224
  t389 = f.my_piecewise5(t15, 0, t19, 0, t388)
  t393 = f.my_piecewise3(t25, 0, -0.8e1 / 0.27e2 * t377 * t220 * t219 + 0.4e1 / 0.3e1 * t381 * t228 + 0.4e1 / 0.3e1 * t28 * t389)
  t394 = t212 * t393
  t396 = t31 * t179 * t372
  t399 = t212 * t30
  t400 = t31 ** 2
  t402 = 0.1e1 / t400 / t11
  t404 = t402 * t370 * t372
  t407 = t365 ** 2
  t408 = t407 * t175
  t409 = t408 * t264
  t412 = t327 * t335
  t414 = 0.1e1 / t64 / t44
  t415 = s0 * t414
  t417 = t337 * t415 * t261
  t420 = t323 * t80
  t421 = t420 * t335
  t423 = t337 * t259 * t261
  t426 = t334 * t343
  t427 = t324 * t426
  t429 = t337 * t259 * t354
  t432 = t324 * t335
  t433 = t365 * t175
  t434 = t433 * t264
  t437 = t155 * t426
  t439 = t337 * t415 * t354
  t442 = t308 ** 2
  t448 = 0.40e2 / 0.9e1 * tau0 * t251 - 0.11e2 / 0.9e1 * t415
  t449 = t448 * t87
  t450 = t261 * t157
  t451 = t450 * t264
  t453 = t80 * t334
  t454 = params.eta ** 2
  t455 = t454 * t42
  t457 = 0.1e1 / t46 / t198
  t458 = t455 * t457
  t459 = t453 * t458
  t461 = t83 * t414
  t462 = t263 * t461
  t464 = -t449 - 0.2e1 / 0.3e1 * t451 - 0.2e1 / 0.9e1 * t459 + 0.11e2 / 0.9e1 * t462
  t467 = t42 * t457
  t471 = -0.2e1 * t442 * t166 - 0.2e1 * t358 * t464 - 0.19e2 / 0.324e3 * t41 * t467 * t170
  t472 = t471 * t175
  t473 = t472 * t264
  t476 = t175 * t448
  t477 = t476 * t264
  t480 = t433 * t461
  t483 = t160 * t163
  t484 = t327 * t483
  t485 = t175 * t454
  t487 = t485 * t467 * t261
  t490 = t160 * t343
  t491 = t155 * t490
  t493 = t485 * t467 * t354
  t496 = t155 * t483
  t497 = t433 * t458
  t500 = t154 * t160
  t501 = t261 ** 2
  t504 = t345 * t350
  t505 = t504 * t261
  t511 = 0.1e1 / t159 / t156
  t512 = t158 * t511
  t517 = 0.12e2 * t500 * t501 + 0.32e2 / 0.3e1 * t505 * t264 + 0.4e1 * t346 * t448 + 0.20e2 / 0.9e1 * t512 * t458 - 0.44e2 / 0.9e1 * t351 * t461
  t519 = t337 * t259 * t517
  t523 = 0.1e1 / t342 / t162
  t524 = t334 * t523
  t525 = t155 * t524
  t526 = t354 ** 2
  t527 = t175 * t526
  t528 = t527 * t264
  t531 = t153 * t501
  t532 = t531 * t157
  t537 = t153 * t261
  t538 = t537 * t157
  t539 = t329 * t448
  t542 = 0.4e1 * t336 * t409 - 0.88e2 / 0.3e1 * t412 * t417 + 0.16e2 * t421 * t423 - 0.8e1 * t427 * t429 + 0.8e1 * t432 * t434 + 0.44e2 / 0.3e1 * t437 * t439 + 0.4e1 * t336 * t473 + 0.8e1 * t412 * t477 - 0.44e2 / 0.3e1 * t336 * t480 + 0.8e1 * t484 * t487 - 0.4e1 * t491 * t493 + 0.4e1 * t496 * t497 - 0.4e1 * t437 * t519 + 0.8e1 * t525 * t528 - 0.12e2 * t532 * t355 + 0.12e2 * t532 * t367 + 0.12e2 * t538 * t539
  t546 = 0.1e1 / t64 / t45
  t547 = s0 * t546
  t549 = -0.440e3 / 0.27e2 * tau0 * t414 + 0.154e3 / 0.27e2 * t547
  t550 = t329 * t549
  t553 = t80 * t160
  t554 = t501 * t261
  t557 = t154 * t350
  t558 = t557 * t501
  t564 = t345 * t511
  t565 = t564 * t261
  t568 = t504 * t448
  t576 = 0.1e1 / t159 / t333
  t577 = t158 * t576
  t578 = t454 * params.eta
  t579 = t578 * t241
  t581 = 0.1e1 / t243 / t197
  t582 = t579 * t581
  t586 = 0.1e1 / t46 / t243
  t587 = t455 * t586
  t590 = t83 * t546
  t593 = 0.24e2 * t553 * t554 + 0.48e2 * t558 * t264 + 0.36e2 * t500 * t261 * t448 + 0.80e2 / 0.3e1 * t565 * t458 + 0.16e2 * t568 * t264 - 0.176e3 / 0.3e1 * t505 * t461 + 0.4e1 * t346 * t549 + 0.40e2 / 0.9e1 * t577 * t582 - 0.220e3 / 0.9e1 * t512 * t587 + 0.616e3 / 0.27e2 * t351 * t590
  t594 = t344 * t593
  t597 = t342 ** 2
  t598 = 0.1e1 / t597
  t599 = t598 * t175
  t600 = t526 * t354
  t601 = t599 * t600
  t604 = t324 * t157
  t605 = t523 * t175
  t606 = t605 * t526
  t609 = t163 * t407
  t610 = t609 * t175
  t613 = t448 * t354
  t614 = t344 * t613
  t617 = t261 * t517
  t618 = t344 * t617
  t621 = t163 * t471
  t622 = t175 * t261
  t623 = t621 * t622
  t626 = t366 * t476
  t629 = t526 * t261
  t630 = t605 * t629
  t633 = t343 * t407
  t634 = t175 * t354
  t635 = t633 * t634
  t638 = t366 * t472
  t641 = t343 * t471
  t642 = t641 * t634
  t645 = t343 * t365
  t646 = t175 * t517
  t647 = t645 * t646
  t650 = t645 * t634
  t653 = t420 * t157
  t654 = t261 * t354
  t655 = t344 * t654
  t658 = t366 * t622
  t661 = 0.4e1 * t328 * t550 - 0.12e2 * t328 * t614 - 0.12e2 * t328 * t618 + 0.12e2 * t328 * t623 + 0.12e2 * t328 * t626 + 0.24e2 * t328 * t630 - 0.2e1 * t341 * t594 - 0.12e2 * t341 * t601 - 0.6e1 * t341 * t635 + 0.6e1 * t341 * t638 - 0.6e1 * t341 * t642 - 0.6e1 * t341 * t647 + 0.12e2 * t604 * t606 + 0.6e1 * t604 * t610 - 0.12e2 * t604 * t650 - 0.24e2 * t653 * t655 + 0.24e2 * t653 * t658
  t663 = t308 * t166
  t666 = t549 * t87
  t667 = t448 * t157
  t668 = t667 * t264
  t669 = t261 * t334
  t670 = t669 * t458
  t672 = t450 * t461
  t674 = t553 * t582
  t676 = t453 * t587
  t678 = t263 * t590
  t680 = -t666 - t668 - 0.2e1 / 0.3e1 * t670 + 0.11e2 / 0.3e1 * t672 - 0.2e1 / 0.9e1 * t674 + 0.22e2 / 0.9e1 * t676 - 0.154e3 / 0.27e2 * t678
  t683 = t42 * t586
  t687 = -0.6e1 * t663 * t464 - 0.2e1 * t358 * t680 + 0.209e3 / 0.486e3 * t41 * t683 * t170
  t688 = t163 * t687
  t689 = t688 * t175
  t698 = t63 * t414
  t716 = 0.162742215233874e0 * t449 + 0.10849481015591600000000000000000000000000000000000e0 * t451 + 0.36164936718638666666666666666666666666666666666667e-1 * t459 - 0.19890715195251266666666666666666666666666666666667e0 * t462 + 0.66302383984170888888888888888888888888888888888888e-1 * t124 * t698 - 0.11870625016560800000000000000000000000000000000000e0 * t442 - 0.11870625016560800000000000000000000000000000000000e0 * t127 * t464 + 0.11e2 / 0.27e2 * t133 * t415 * t127 - 0.2e1 / 0.9e1 * t133 * t259 * t308 + t133 * t78 * t464 / 0.24e2 + 0.19e2 / 0.324e3 * t148 * t149 * t457
  t717 = t716 * t154
  t718 = t717 * t157
  t721 = t407 * t365
  t722 = t163 * t721
  t723 = t722 * t175
  t726 = t354 * t517
  t727 = t605 * t726
  t731 = t523 * t365 * t527
  t734 = t609 * t622
  t737 = t335 * t365
  t738 = t327 * t737
  t741 = t426 * t175
  t742 = t327 * t741
  t743 = t251 * t354
  t745 = t83 * t743 * t261
  t748 = t426 * t365
  t749 = t155 * t748
  t752 = -t680
  t753 = f.my_piecewise3(t90, 0, t752)
  t754 = params.c1 * t753
  t756 = -t464
  t757 = f.my_piecewise3(t90, 0, t756)
  t758 = params.c1 * t757
  t761 = t268 ** 2
  t762 = t761 * t268
  t765 = 0.1e1 / t271 / t93
  t768 = t271 ** 2
  t769 = 0.1e1 / t768
  t773 = t765 * t268
  t779 = -t92 * t272 * t753 - 0.6e1 * t92 * t773 * t757 - 0.6e1 * params.c1 * t762 * t765 - 0.6e1 * t92 * t769 * t762 - 0.6e1 * t758 * t273 - t754 * t94
  t785 = t765 * t761
  t790 = -t92 * t272 * t757 - 0.2e1 * params.c1 * t761 * t272 - t758 * t94 - 0.2e1 * t92 * t785
  t794 = t275 ** 2
  t798 = f.my_piecewise3(t98, 0, t752)
  t800 = f.my_piecewise3(t98, 0, t756)
  t805 = t277 ** 2
  t806 = t805 * t277
  t836 = -0.667e0 * t798 - 0.26673330e1 * t277 * t800 - 0.8891110e0 * t99 * t798 - 0.3978519606294e1 * t806 - 0.11935558818882e2 * t279 * t800 - 0.1989259803147e1 * t101 * t798 + 0.34831129067760e2 * t99 * t806 + 0.52246693601640e2 * t281 * t800 + 0.5805188177960e1 * t103 * t798 - 0.53279882495820e2 * t101 * t806 - 0.53279882495820e2 * t283 * t800 - 0.4439990207985e1 * t105 * t798 + 0.28143472977480e2 * t103 * t806 + 0.21107604733110e2 * t285 * t800 + 0.1407173648874e1 * t107 * t798 - 0.4869027097620e1 * t105 * t806 - 0.2921416258572e1 * t287 * t800 - 0.162300903254e0 * t109 * t798
  t837 = t293 ** 2
  t838 = 0.1e1 / t837
  t839 = t295 ** 2
  t840 = t839 * t295
  t845 = t293 * t115
  t846 = 0.1e1 / t845
  t847 = t292 * t846
  t848 = t295 * t118
  t849 = f.my_piecewise3(t98, t756, 0)
  t850 = t848 * t849
  t853 = params.c2 ** 2
  t854 = params.d * t853
  t856 = 0.1e1 / t837 / t115
  t861 = f.my_piecewise3(t98, t752, 0)
  t865 = t854 * t838
  t869 = params.d * t853 * params.c2
  t871 = 0.1e1 / t837 / t293
  t876 = f.my_piecewise5(t89, 0.3e1 * t790 * t275 * t96 + t794 * t275 * t96 + t779 * t96, t97, t836, -t292 * t294 * t861 * t118 - 0.6e1 * t292 * t838 * t840 * t118 - 0.6e1 * t854 * t856 * t840 * t118 - t869 * t871 * t840 * t118 - 0.6e1 * t847 * t850 - 0.3e1 * t865 * t850)
  t878 = t344 * t517
  t881 = t716 * t80
  t882 = t881 * t157
  t885 = t621 * t175
  t890 = t337 * t415
  t893 = t324 * t483
  t894 = t485 * t467
  t897 = 0.2e1 * t341 * t689 + 0.12e2 * t653 * t539 - 0.6e1 * t718 * t355 + 0.2e1 * t341 * t723 + 0.12e2 * t341 * t727 + 0.12e2 * t341 * t731 + 0.12e2 * t328 * t734 + 0.16e2 * t738 * t423 - 0.16e2 * t742 * t745 - 0.8e1 * t749 * t429 + t876 * t121 - 0.6e1 * t604 * t878 + 0.12e2 * t882 * t330 + 0.6e1 * t604 * t885 + 0.6e1 * t718 * t367 - 0.44e2 / 0.3e1 * t432 * t890 + 0.4e1 * t893 * t894
  t898 = t350 * t163
  t899 = t155 * t898
  t900 = t175 * t578
  t901 = t241 * t581
  t902 = t900 * t901
  t905 = t157 * t343
  t906 = t327 * t905
  t907 = t433 * t654
  t910 = t485 * t683
  t913 = t337 * t547
  t916 = t531 * t335
  t919 = t717 * t335
  t929 = t63 * t546
  t951 = 0.162742215233874e0 * t666 + 0.16274221523387400000000000000000000000000000000000e0 * t668 + 0.10849481015591600000000000000000000000000000000000e0 * t670 - 0.59672145585753800000000000000000000000000000000000e0 * t672 + 0.36164936718638666666666666666666666666666666666667e-1 * t674 - 0.39781430390502533333333333333333333333333333333334e0 * t676 + 0.92823337577839244444444444444444444444444444444446e0 * t678 - 0.30941112525946414814814814814814814814814814814814e0 * t124 * t929 - 0.35611875049682400000000000000000000000000000000000e0 * t308 * t464 - 0.11870625016560800000000000000000000000000000000000e0 * t127 * t680 - 0.154e3 / 0.81e2 * t133 * t547 * t127 + 0.11e2 / 0.9e1 * t133 * t415 * t308 - t133 * t259 * t464 / 0.3e1 + t133 * t78 * t680 / 0.24e2 - 0.209e3 / 0.486e3 * t148 * t149 * t586
  t952 = t951 * t154
  t956 = 0.1e1 / t235 / t70
  t957 = t956 * t255
  t964 = t42 ** 2
  t965 = t964 * s0
  t971 = t51 ** 2
  t975 = 0.1e1 / t971 * t37 * t40 * t56
  t980 = 0.43950443928901157407407407407407407407407407407407e-2 * t242 / t243 / t43 * t52 * t56 - 0.34881304705477109053497942386831275720164609053498e-5 * t240 * t965 / t46 / t243 / t198 * t975 + 0.11e2 / 0.27e2 * t60 * t698
  t981 = t957 * t980
  t984 = t323 * t501
  t987 = t235 ** 2
  t988 = 0.1e1 / t987
  t989 = t255 ** 2
  t990 = t989 * t255
  t991 = t988 * t990
  t994 = t299 * t234
  t995 = t956 * t989
  t998 = t236 * t980
  t1005 = t243 ** 2
  t1012 = t964 * t241
  t1024 = 0.1e1 / t971 / t51 * t36 / t61 / t238 * t56
  t1029 = -0.47633909705799540123456790123456790123456790123456e-1 * t242 * t581 * t52 * t56 + 0.94179522704788194444444444444444444444444444444444e-4 * t240 * t965 / t46 / t1005 * t975 - 0.19378502614153949474165523548239597622313671696388e-6 * t240 * t1012 / t64 / t1005 / t45 * t1024 - 0.154e3 / 0.81e2 * t60 * t929
  t1030 = t236 * t1029
  t1039 = t99 * t805
  t1043 = t101 * t805
  t1047 = t103 * t805
  t1051 = t105 * t805
  t1059 = -0.667e0 * t800 - 0.8891110e0 * t805 - 0.8891110e0 * t99 * t800 - 0.3978519606294e1 * t1039 - 0.1989259803147e1 * t101 * t800 + 0.17415564533880e2 * t1043 + 0.5805188177960e1 * t103 * t800 - 0.17759960831940e2 * t1047 - 0.4439990207985e1 * t105 * t800 + 0.7035868244370e1 * t1051 + 0.1407173648874e1 * t107 * t800 - 0.973805419524e0 * t107 * t805 - 0.162300903254e0 * t109 * t800
  t1071 = f.my_piecewise5(t89, t790 * t96 + t794 * t96, t97, t1059, -t292 * t294 * t849 * t118 - 0.2e1 * t292 * t846 * t839 * t118 - t854 * t838 * t839 * t118)
  t1072 = t1071 * t234
  t1075 = t234 * t956
  t1080 = t234 * t988
  t1083 = 0.16e2 / 0.9e1 * t899 * t902 - 0.24e2 * t906 * t907 - 0.44e2 / 0.3e1 * t496 * t910 + 0.616e3 / 0.27e2 * t336 * t913 + 0.8e1 * t916 * t338 + 0.4e1 * t919 * t338 + 0.2e1 * t952 * t176 + 0.6e1 * t301 * t981 + 0.12e2 * t984 * t176 - 0.6e1 * t301 * t991 + 0.6e1 * t994 * t995 - 0.3e1 * t994 * t998 - t301 * t1030 - 0.3e1 * t1072 * t302 - 0.6e1 * t1075 * t980 * t255 + t237 * t1029 + 0.6e1 * t1080 * t990
  t1085 = t542 + t661 + t897 + t1083
  t1087 = t31 * t1085 * t372
  t1090 = 0.1e1 / t400
  t1092 = t1090 * t179 * t372
  t1096 = 0.1e1 / t400 / t215
  t1098 = t1096 * t179 * t372
  t1103 = f.my_piecewise3(t25, 0, 0.4e1 / 0.3e1 * t28 * t219)
  t1104 = t212 * t1103
  t1106 = t402 * t179 * t372
  t1133 = 0.16e2 / 0.3e1 * t412 * t423 - 0.8e1 / 0.3e1 * t437 * t429 + 0.8e1 / 0.3e1 * t336 * t434 - 0.8e1 * t328 * t655 + 0.8e1 * t328 * t658 - 0.4e1 * t341 * t650 + 0.4e1 * t531 * t176 + 0.2e1 * t717 * t176 + 0.2e1 * t341 * t610 + 0.8e1 * t653 * t330 - 0.4e1 * t604 * t355 + 0.4e1 * t604 * t367
  t1157 = -0.2e1 * t341 * t878 + 0.2e1 * t341 * t885 + 0.4e1 * t328 * t539 + 0.4e1 * t341 * t606 + t1071 * t121 + 0.2e1 * t301 * t995 - 0.2e1 * t994 * t302 - t301 * t998 + t237 * t980 - 0.2e1 * t1075 * t989 - 0.44e2 / 0.9e1 * t336 * t890 + 0.4e1 / 0.3e1 * t496 * t894 + 0.8e1 / 0.3e1 * t432 * t338
  t1158 = t1133 + t1157
  t1160 = t1090 * t1158 * t372
  t1163 = t7 ** 2
  t1165 = t210 * t1163 * jnp.pi
  t1166 = t32 * t370
  t1167 = t1165 * t1166
  t1168 = 0.1e1 / t181
  t1171 = t36 * t62
  t1172 = t1171 * t205
  t1173 = t1168 / t64 * t1172
  t1176 = t210 * t9
  t1177 = t32 * t179
  t1178 = t1176 * t1177
  t1179 = t36 * t39
  t1180 = t1168 * t76
  t1182 = t1179 * t1180 * t205
  t1185 = t1165 * t1177
  t1186 = t1180 * t1172
  t1189 = t1103 * t31
  t1190 = t1189 * t179
  t1191 = t1165 * t1190
  t1194 = t30 * t1090
  t1195 = t1194 * t179
  t1196 = t1165 * t1195
  t1200 = t31 * t1158 * t372
  t1203 = -0.59374800000000000000000000000000000000000000000000e3 * t33 * t207 - 0.9e1 / 0.8e1 * t233 * t373 - 0.3e1 / 0.8e1 * t394 * t396 + t399 * t404 / 0.4e1 - 0.3e1 / 0.8e1 * t399 * t1087 - 0.3e1 / 0.8e1 * t233 * t1092 - 0.5e1 / 0.36e2 * t399 * t1098 + t1104 * t1106 / 0.4e1 - 0.3e1 / 0.8e1 * t399 * t1160 + 0.24481714410000000000000000000000000000000000000000e2 * t1167 * t1173 + 0.16321142940000000000000000000000000000000000000000e2 * t1178 * t1182 - 0.24481714410000000000000000000000000000000000000000e2 * t1185 * t1186 + 0.24481714410000000000000000000000000000000000000000e2 * t1191 * t1173 + 0.81605714700000000000000000000000000000000000000000e1 * t1196 * t1173 - 0.9e1 / 0.8e1 * t1104 * t1200
  t1205 = t1090 * t370 * t372
  t1208 = t5 * t211
  t1209 = t1208 * t1195
  t1211 = 0.1e1 / t193 / t192
  t1213 = t1211 * t37 * t187
  t1218 = t1213 * t181 / t46 / t197 * t205
  t1221 = t1208 * t1190
  t1224 = t32 * t1158
  t1225 = t1208 * t1224
  t1230 = t1213 * t181 / t46 / t43 * t205
  t1233 = t1208 * t1166
  t1237 = 0.1e1 / t193 / t1171 / t78 / 0.6e1
  t1239 = t1237 * t36 * t62
  t1241 = t1239 * t415 * t205
  t1244 = t232 * t31
  t1245 = t1244 * t179
  t1246 = t1208 * t1245
  t1249 = t1103 * t1090
  t1250 = t1249 * t179
  t1251 = t1208 * t1250
  t1254 = t1194 * t370
  t1255 = t1208 * t1254
  t1260 = t1208 * t1177
  t1265 = t1213 * t181 / t46 / t44 * t205
  t1271 = t1239 * t547 * t205
  t1274 = t1189 * t370
  t1275 = t1208 * t1274
  t1280 = t30 * t402
  t1281 = t1280 * t179
  t1282 = t1208 * t1281
  t1285 = t1208 * t32
  t1286 = 0.1e1 / t197
  t1288 = t1211 * t205
  t1289 = t179 * t1286 * t1288
  t1292 = -0.3e1 / 0.4e1 * t1104 * t1205 + 0.57725500000000000000000000000000000000000000000000e1 * t1209 * t1218 + 0.17317650000000000000000000000000000000000000000000e2 * t1221 * t1218 - 0.74218500000000000000000000000000000000000000000000e1 * t1225 * t1230 - 0.89062200000000000000000000000000000000000000000000e2 * t1233 * t1241 - 0.74218500000000000000000000000000000000000000000000e1 * t1246 * t1230 - 0.49479000000000000000000000000000000000000000000000e1 * t1251 * t1230 - 0.49479000000000000000000000000000000000000000000000e1 * t1255 * t1230 - 0.29687400000000000000000000000000000000000000000000e2 * t1209 * t1241 - 0.19241833333333333333333333333333333333333333333333e2 * t1260 * t1265 + 0.17317650000000000000000000000000000000000000000000e2 * t1233 * t1218 + 0.20781180000000000000000000000000000000000000000000e3 * t1260 * t1271 - 0.14843700000000000000000000000000000000000000000000e2 * t1275 * t1230 - 0.89062200000000000000000000000000000000000000000000e2 * t1221 * t1241 + 0.16493000000000000000000000000000000000000000000000e1 * t1282 * t1230 - 0.32302153261130400000000000000000000000000000000000e3 * t1285 * t1289
  t1294 = f.my_piecewise3(t1, 0, t1203 + t1292)
  t1296 = r1 <= f.p.dens_threshold
  t1297 = f.my_piecewise5(t19, t16, t15, t20, -t22)
  t1298 = 0.1e1 + t1297
  t1299 = t1298 <= f.p.zeta_threshold
  t1300 = t1298 ** (0.1e1 / 0.3e1)
  t1301 = t1300 ** 2
  t1303 = 0.1e1 / t1301 / t1298
  t1305 = f.my_piecewise5(t19, 0, t15, 0, -t218)
  t1306 = t1305 ** 2
  t1310 = 0.1e1 / t1301
  t1311 = t1310 * t1305
  t1313 = f.my_piecewise5(t19, 0, t15, 0, -t227)
  t1317 = f.my_piecewise5(t19, 0, t15, 0, -t388)
  t1321 = f.my_piecewise3(t1299, 0, -0.8e1 / 0.27e2 * t1303 * t1306 * t1305 + 0.4e1 / 0.3e1 * t1311 * t1313 + 0.4e1 / 0.3e1 * t1300 * t1317)
  t1322 = t212 * t1321
  t1323 = s2 ** 2
  t1324 = r1 ** 2
  t1325 = t1324 ** 2
  t1327 = r1 ** (0.1e1 / 0.3e1)
  t1329 = 0.1e1 / t1327 / t1325 / r1
  t1330 = t1323 * t1329
  t1334 = jnp.exp(-t41 * t1330 * t52 / 0.576e3)
  t1340 = t1327 ** 2
  t1342 = 0.1e1 / t1340 / t1324
  t1343 = t62 * s2 * t1342
  t1350 = params.k1 * (0.1e1 - params.k1 / (params.k1 + (-0.162742215233874e0 * t35 * t1334 + 0.10e2 / 0.81e2) * t36 * t1343 / 0.24e2))
  t1354 = s2 * t1342
  t1356 = tau1 / t1340 / r1 - t1354 / 0.8e1
  t1360 = t82 + params.eta * s2 * t1342 / 0.8e1
  t1362 = t1356 / t1360
  t1365 = f.my_piecewise3(0.0e0 < t1362, 0, t1362)
  t1370 = jnp.exp(-params.c1 * t1365 / (0.1e1 - t1365))
  t1372 = 0.25e1 < t1362
  t1373 = f.my_piecewise3(t1372, 0.25e1, t1362)
  t1375 = t1373 ** 2
  t1377 = t1375 * t1373
  t1379 = t1375 ** 2
  t1388 = f.my_piecewise3(t1372, t1362, 0.25e1)
  t1392 = jnp.exp(params.c2 / (0.1e1 - t1388))
  t1394 = f.my_piecewise5(t1362 <= 0.0e0, t1370, t1362 <= 0.25e1, 0.1e1 - 0.667e0 * t1373 - 0.4445555e0 * t1375 - 0.663086601049e0 * t1377 + 0.1451297044490e1 * t1379 - 0.887998041597e0 * t1379 * t1373 + 0.234528941479e0 * t1379 * t1375 - 0.23185843322e-1 * t1379 * t1377, -params.d * t1392)
  t1400 = 0.1e1 - t1362
  t1401 = t1400 ** 2
  t1411 = t1356 ** 2
  t1413 = t1360 ** 2
  t1415 = t1411 ** 2
  t1416 = t1413 ** 2
  t1427 = jnp.exp(-t1401 * t166 - t41 * t1330 * t170 / 0.576e3)
  t1431 = 0.1e1 + t1350 + t1394 * (0.174e0 - t1350) + 0.2e1 * (-0.162742215233874e0 + 0.162742215233874e0 * t1362 + 0.67809256347447500000000000000000000000000000000000e-2 * t124 * t1343 - 0.59353125082804000000000000000000000000000000000000e-1 * t1401 + t133 * t1354 * t1400 / 0.24e2 + t148 * t40 * t1323 * t1329 / 0.576e3) * t1411 / t1413 / (0.1e1 + t1415 / t1416) * t1427
  t1433 = jnp.sqrt(s2)
  t1438 = jnp.sqrt(t188 * t1433 / t1327 / r1)
  t1442 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t201 / t1438)
  t1443 = 0.1e1 - t1442
  t1444 = t31 * t1431 * t1443
  t1452 = f.my_piecewise3(t1299, 0, 0.4e1 / 0.9e1 * t1310 * t1306 + 0.4e1 / 0.3e1 * t1300 * t1313)
  t1453 = t212 * t1452
  t1455 = t1090 * t1431 * t1443
  t1460 = f.my_piecewise3(t1299, 0, 0.4e1 / 0.3e1 * t1300 * t1305)
  t1461 = t212 * t1460
  t1463 = t402 * t1431 * t1443
  t1467 = f.my_piecewise3(t1299, t27, t1300 * t1298)
  t1468 = t212 * t1467
  t1470 = t1096 * t1431 * t1443
  t1474 = f.my_piecewise3(t1296, 0, -0.3e1 / 0.8e1 * t1322 * t1444 - 0.3e1 / 0.8e1 * t1453 * t1455 + t1461 * t1463 / 0.4e1 - 0.5e1 / 0.36e2 * t1468 * t1470)
  t1497 = 0.1e1 / t64 / t317
  t1498 = s0 * t1497
  t1500 = 0.6160e4 / 0.81e2 * tau0 * t546 - 0.2618e4 / 0.81e2 * t1498
  t1511 = t952 * t157
  t1514 = t407 ** 2
  t1529 = t667 * t461
  t1531 = t669 * t587
  t1533 = t450 * t590
  t1535 = t243 * t44
  t1536 = 0.1e1 / t1535
  t1537 = t579 * t1536
  t1538 = t553 * t1537
  t1541 = 0.1e1 / t46 / t244
  t1542 = t455 * t1541
  t1543 = t453 * t1542
  t1545 = t83 * t1497
  t1546 = t263 * t1545
  t1551 = t1500 * t87
  t1553 = t464 ** 2
  t1559 = t549 * t157 * t264
  t1562 = t448 * t334 * t458
  t1566 = t261 * t160 * t582
  t1570 = t80 * t350
  t1571 = t454 ** 2
  t1575 = 0.1e1 / t64 / t243 / t317
  t1576 = t1571 * t964 * t1575
  t1577 = t1570 * t1576
  t1582 = -t1551 - 0.4e1 / 0.3e1 * t1559 - 0.4e1 / 0.3e1 * t1562 + 0.22e2 / 0.3e1 * t1529 - 0.8e1 / 0.9e1 * t1566 + 0.88e2 / 0.9e1 * t1531 - 0.616e3 / 0.27e2 * t1533 - 0.8e1 / 0.27e2 * t1577 + 0.44e2 / 0.9e1 * t1538 - 0.1958e4 / 0.81e2 * t1543 + 0.2618e4 / 0.81e2 * t1546
  t1600 = t63 * t1497
  t1607 = -0.11870625016560800000000000000000000000000000000000e0 * t127 * t1582 - 0.616e3 / 0.81e2 * t133 * t547 * t308 + 0.22e2 / 0.9e1 * t133 * t415 * t464 - 0.4e1 / 0.9e1 * t133 * t259 * t680 + t133 * t78 * t1582 / 0.24e2 + 0.5225e4 / 0.1458e4 * t148 * t149 * t1541 + 0.17533297098036301728395061728395061728395061728395e1 * t124 * t1600 + 0.21698962031183200000000000000000000000000000000000e0 * t1559 + 0.21698962031183200000000000000000000000000000000000e0 * t1562 + 0.14465974687455466666666666666666666666666666666667e0 * t1566 + 0.48219915624851555555555555555555555555555555555556e-1 * t1577
  t1637 = t517 ** 2
  t1641 = 0.2e1 * (-0.11934429117150760000000000000000000000000000000000e1 * t1529 - 0.15912572156201013333333333333333333333333333333333e1 * t1531 + 0.37129335031135697777777777777777777777777777777778e1 * t1533 - 0.79562860781005066666666666666666666666666666666668e0 * t1538 + 0.39339414497274727407407407407407407407407407407408e1 * t1543 - 0.52599891294108905185185185185185185185185185185186e1 * t1546 + 0.2618e4 / 0.243e3 * t133 * t1498 * t127 + 0.162742215233874e0 * t1551 - 0.35611875049682400000000000000000000000000000000000e0 * t1553 - 0.47482500066243200000000000000000000000000000000000e0 * t308 * t680 + t1607) * t154 * t176 + 0.8e1 * t341 * t688 * t433 - 0.48e2 * t882 * t655 - 0.24e2 * t718 * t650 + 0.12e2 * t341 * t609 * t472 - 0.48e2 * t538 * t614 - 0.48e2 * t532 * t650 + 0.24e2 * t328 * t609 * t476 + 0.48e2 * t328 * t605 * t448 * t526 + 0.24e2 * t341 * t523 * t407 * t527 + 0.12e2 * t341 * t605 * t1637
  t1643 = t984 * t157
  t1672 = 0.24e2 * t341 * t523 * t471 * t527 - 0.72e2 * t341 * t599 * t526 * t517 - 0.12e2 * t341 * t633 * t646 - 0.12e2 * t341 * t641 * t646 + 0.48e2 * t1643 * t367 + 0.24e2 * t532 * t885 + 0.48e2 * t538 * t626 - 0.24e2 * t604 * t647 + 0.48e2 * t604 * t727 - 0.48e2 * t653 * t618 + 0.48e2 * t882 * t658
  t1694 = t175 * t549
  t1707 = -0.16e2 * t328 * t344 * t549 * t354 - 0.24e2 * t328 * t344 * t448 * t517 - 0.8e1 * t341 * t343 * t687 * t634 - 0.8e1 * t341 * t343 * t721 * t634 + 0.16e2 * t328 * t366 * t1694 + 0.16e2 * t328 * t688 * t622 + 0.16e2 * t328 * t722 * t622 - 0.24e2 * t604 * t635 + 0.48e2 * t604 * t731 + 0.96e2 * t653 * t630 + 0.48e2 * t653 * t734
  t1751 = t448 ** 2
  t1757 = t159 ** 2
  t1762 = t501 ** 2
  t1767 = 0.128e3 * t1570 * t554 * t264 + 0.160e3 * t154 * t511 * t501 * t458 + 0.160e3 / 0.3e1 * t564 * t448 * t458 + 0.640e3 / 0.9e1 * t345 * t576 * t261 * t582 + 0.64e2 / 0.3e1 * t504 * t549 * t264 - 0.880e3 / 0.9e1 * t577 * t1537 + 0.19580e5 / 0.81e2 * t512 * t1542 + 0.192e3 * t557 * t261 * t83 * t251 * t448 - 0.352e3 * t558 * t461 - 0.3520e4 / 0.9e1 * t565 * t587 - 0.352e3 / 0.3e1 * t568 * t461 + 0.9856e4 / 0.27e2 * t505 * t590 - 0.10472e5 / 0.81e2 * t351 * t1545 + 0.144e3 * t553 * t501 * t448 + 0.36e2 * t500 * t1751 + 0.48e2 * t500 * t261 * t549 + 0.280e3 / 0.27e2 * t158 / t1757 * t1576 + 0.24e2 * t1762 * t160 + 0.4e1 * t346 * t1500
  t1804 = t238 ** 2
  t1808 = t964 ** 2
  t1813 = t971 ** 2
  t1821 = 0.54116251372265406069958847736625514403292181069958e0 * t242 * t1536 * t52 * t56 - 0.19793202570096843992912665752171925011431184270690e-2 * t240 * t965 / t46 / t1005 / r0 * t975 + 0.94308712722215887440938881268099375095259868922421e-5 * t240 * t1012 / t64 / t1005 / t317 * t1024 - 0.10765834785641083041203068637910887567952039831327e-7 * t35 / t1804 / t238 * t1808 * s0 / t1005 / t1535 / t1813 * t56 + 0.2618e4 / 0.243e3 * t60 * t1600
  t1828 = 0.1e1 / t987 / t70
  t1829 = t989 ** 2
  t1833 = 0.16e2 * t951 * t80 * t157 * t330 - 0.8e1 * t1075 * t1029 * t255 + 0.36e2 * t1080 * t980 * t989 - 0.2e1 * t341 * t344 * t1767 - t301 * t236 * t1821 + 0.24e2 * t301 * t1828 * t1829 - 0.4e1 * t994 * t1030 + 0.12e2 * t1072 * t995 - 0.6e1 * t1072 * t998 - 0.8e1 * t1511 * t355 + 0.24e2 * t882 * t539
  t1834 = t980 ** 2
  t1875 = 0.6e1 * t301 * t956 * t1834 - 0.24e2 * t994 * t991 - 0.4e1 * t876 * t234 * t302 + 0.32e2 * t327 * t335 * t471 * t423 + 0.32e2 * t738 * t477 + 0.32e2 * t327 * t483 * t365 * t487 - 0.64e2 * t420 * t741 * t745 - 0.32e2 * t742 * t83 * t251 * t517 * t261 - 0.32e2 * t742 * t83 * t743 * t448 - 0.32e2 * t327 * t490 * t175 * t455 * t457 * t354 * t261 - 0.32e2 * t324 * t748 * t429
  t1893 = t524 * t175
  t1919 = -0.16e2 * t155 * t426 * t471 * t429 - 0.16e2 * t749 * t519 - 0.16e2 * t155 * t490 * t365 * t493 - 0.352e3 / 0.3e1 * t738 * t417 + 0.32e2 * t327 * t335 * t407 * t423 + 0.64e2 * t327 * t1893 * t83 * t251 * t526 * t261 + 0.352e3 / 0.3e1 * t742 * t83 * t414 * t354 * t261 + 0.32e2 * t155 * t524 * t365 * t528 + 0.176e3 / 0.3e1 * t749 * t439 - 0.16e2 * t155 * t426 * t407 * t429 + 0.32e2 * t155 * t1893 * t726 * t264
  t1951 = 0.16e2 * t155 * t737 * t473 + 0.64e2 * t420 * t737 * t423 + 0.12e2 * t153 * t1751 * t176 - 0.48e2 * t906 * t433 * t613 - 0.48e2 * t906 * t433 * t617 - 0.88e2 / 0.3e1 * t919 * t890 - 0.176e3 / 0.3e1 * t893 * t910 + 0.8e1 * t717 * t483 * t894 + 0.32e2 * t984 * t335 * t338 + 0.64e2 / 0.9e1 * t324 * t898 * t902 + 0.16e2 / 0.3e1 * t952 * t335 * t338
  t1966 = t157 * t523
  t1967 = t327 * t1966
  t1976 = t42 * t1541
  t2029 = 0.96e2 * t1967 * t622 * t726 + 0.48e2 * t327 * t164 * t471 * t365 * t622 + 0.80e2 / 0.27e2 * t155 * t511 * t163 * t175 * t1571 * t964 * t1575 - 0.96e2 * t420 * t905 * t907 - 0.48e2 * t906 * t472 * t654 - 0.48e2 * t653 * t614 + 0.24e2 * t328 * t621 * t476 + 0.48e2 * t653 * t626 - 0.16e2 * t328 * t344 * t593 * t261 + 0.48e2 * t653 * t623 + 0.16e2 * t341 * t605 * t593 * t354
  t2033 = t175 * t593
  t2044 = t175 * t600
  t2062 = 0.48e2 * t323 * t261 * t157 * t539 - 0.48e2 * t341 * t598 * t365 * t2044 - 0.96e2 * t328 * t599 * t600 * t261 - 0.8e1 * t341 * t645 * t2033 + 0.16e2 * t538 * t550 - 0.8e1 * t604 * t594 + 0.24e2 * t604 * t638 - 0.24e2 * t604 * t642 + 0.8e1 * t604 * t689 - 0.12e2 * t718 * t878 + 0.12e2 * t718 * t885
  t2063 = t471 ** 2
  t2101 = 0.6e1 * t341 * t163 * t2063 * t175 - 0.24e2 * t234 * t1828 * t1829 + t237 * t1821 - 0.36e2 * t301 * t988 * t989 * t980 - 0.64e2 * t327 * t748 * t622 * t354 * t264 + 0.32e2 * t881 * t335 * t423 + 0.32e2 * t421 * t477 + 0.16e2 * t432 * t473 - 0.352e3 / 0.3e1 * t484 * t485 * t683 * t261 + 0.176e3 / 0.3e1 * t491 * t485 * t683 * t354 + 0.128e3 / 0.9e1 * t327 * t898 * t900 * t901 * t261
  t2145 = -0.64e2 / 0.9e1 * t155 * t350 * t343 * t900 * t901 * t354 + 0.64e2 / 0.9e1 * t899 * t433 * t582 - 0.176e3 / 0.3e1 * t412 * t337 * t415 * t448 - 0.176e3 / 0.3e1 * t496 * t433 * t587 + 0.4928e4 / 0.27e2 * t412 * t337 * t547 * t261 - 0.2464e4 / 0.27e2 * t437 * t337 * t547 * t354 + 0.2464e4 / 0.27e2 * t336 * t433 * t590 + 0.8e1 * t496 * t472 * t458 + 0.16e2 * t484 * t485 * t467 * t448 - 0.8e1 * t491 * t485 * t467 * t517 - 0.88e2 / 0.3e1 * t336 * t472 * t461
  t2181 = 0.88e2 / 0.3e1 * t437 * t337 * t415 * t517 - 0.176e3 / 0.3e1 * t525 * t527 * t461 - 0.88e2 / 0.3e1 * t336 * t408 * t461 + 0.8e1 * t496 * t408 * t458 + 0.16e2 * t155 * t160 * t523 * t485 * t467 * t526 + 0.16e2 / 0.3e1 * t336 * t687 * t175 * t264 - 0.16e2 * t717 * t426 * t429 + 0.32e2 * t537 * t335 * t477 - 0.16e2 * t427 * t519 - 0.6e1 * t1075 * t1834 + 0.16e2 * t919 * t434
  t2214 = 0.32e2 * t324 * t524 * t528 + 0.16e2 * t432 * t409 + 0.32e2 / 0.3e1 * t412 * t1694 * t264 - 0.16e2 / 0.3e1 * t437 * t2033 * t264 - 0.32e2 * t155 * t334 * t598 * t2044 * t264 + 0.16e2 / 0.3e1 * t336 * t721 * t175 * t264 - 0.32e2 * t531 * t426 * t429 + 0.32e2 * t916 * t434 - 0.352e3 / 0.3e1 * t421 * t417 + 0.176e3 / 0.3e1 * t427 * t439 - 0.176e3 / 0.3e1 * t432 * t480
  t2228 = t526 ** 2
  t2232 = -t1582
  t2233 = f.my_piecewise3(t90, 0, t2232)
  t2240 = t757 ** 2
  t2244 = t761 ** 2
  t2270 = t790 ** 2
  t2276 = t794 ** 2
  t2279 = f.my_piecewise3(t98, 0, t2232)
  t2281 = t800 ** 2
  t2283 = t805 ** 2
  t2307 = -0.667e0 * t2279 - 0.26673330e1 * t2281 + 0.34831129067760e2 * t2283 - 0.3895221678096e1 * t287 * t798 - 0.71039843327760e2 * t283 * t798 + 0.168860837864880e3 * t1047 * t800 + 0.28143472977480e2 * t285 * t798 - 0.29214162585720e2 * t1051 * t800 - 0.15914078425176e2 * t279 * t798 + 0.208986774406560e3 * t1039 * t800 + 0.69662258135520e2 * t281 * t798 - 0.319679294974920e3 * t1043 * t800 - 0.1989259803147e1 * t101 * t2279 - 0.162300903254e0 * t109 * t2279
  t2336 = -0.4439990207985e1 * t105 * t2279 - 0.23871117637764e2 * t805 * t800 + 0.1407173648874e1 * t107 * t2279 + 0.5805188177960e1 * t103 * t2279 + 0.52246693601640e2 * t101 * t2281 - 0.35564440e1 * t277 * t798 - 0.8891110e0 * t99 * t2279 - 0.106559764991640e3 * t99 * t2283 + 0.21107604733110e2 * t105 * t2281 + 0.84430418932440e2 * t101 * t2283 - 0.53279882495820e2 * t103 * t2281 - 0.11935558818882e2 * t99 * t2281 - 0.19476108390480e2 * t103 * t2283 - 0.2921416258572e1 * t107 * t2281
  t2338 = t839 ** 2
  t2345 = t839 * t118 * t849
  t2352 = t849 ** 2
  t2360 = t848 * t861
  t2369 = f.my_piecewise3(t98, t2232, 0)
  t2382 = t853 ** 2
  t2384 = t837 ** 2
  t2389 = -0.24e2 * t292 * t856 * t2338 * t118 - 0.36e2 * t292 * t838 * t2345 - 0.36e2 * t854 * t871 * t2338 * t118 - 0.6e1 * t292 * t846 * t2352 * t118 - 0.36e2 * t854 * t856 * t2345 - 0.8e1 * t847 * t2360 - 0.12e2 * t869 / t837 / t845 * t2338 * t118 - t292 * t294 * t2369 * t118 - 0.4e1 * t865 * t2360 - 0.3e1 * t854 * t838 * t2352 * t118 - 0.6e1 * t869 * t871 * t2345 - params.d * t2382 / t2384 * t2338 * t118
  t2390 = f.my_piecewise5(t89, (-params.c1 * t2233 * t94 - 0.8e1 * t754 * t273 - 0.36e2 * t758 * t785 - 0.6e1 * params.c1 * t2240 * t272 - 0.24e2 * params.c1 * t2244 * t769 - 0.24e2 * t92 / t768 / t93 * t2244 - 0.36e2 * t92 * t769 * t761 * t757 - 0.6e1 * t92 * t765 * t2240 - 0.8e1 * t92 * t773 * t753 - t92 * t272 * t2233) * t96 + 0.4e1 * t779 * t275 * t96 + 0.3e1 * t2270 * t96 + 0.6e1 * t790 * t794 * t96 + t2276 * t96, t97, t2307 + t2336, t2389)
  t2414 = 0.32e2 * t420 * t483 * t487 - 0.16e2 * t324 * t490 * t493 + 0.16e2 * t893 * t497 + 0.12e2 * t718 * t610 + 0.48e2 * t341 / t597 / t162 * t175 * t2228 + t2390 * t121 + 0.2e1 * t341 * t163 * (-0.6e1 * t1553 * t166 - 0.8e1 * t663 * t680 - 0.2e1 * t358 * t1582 - 0.5225e4 / 0.1458e4 * t41 * t1976 * t170) * t175 - 0.48e2 * t604 * t601 + 0.8e1 * t604 * t723 - 0.48e2 * t1643 * t355 - 0.24e2 * t532 * t878
  t2423 = t24 ** 2
  t2426 = t220 ** 2
  t2432 = t228 ** 2
  t2441 = -0.24e2 * t385 + 0.24e2 * t21 / t384 / t11
  t2442 = f.my_piecewise5(t15, 0, t19, 0, t2441)
  t2446 = f.my_piecewise3(t25, 0, 0.40e2 / 0.81e2 / t213 / t2423 * t2426 - 0.16e2 / 0.9e1 * t377 * t220 * t228 + 0.4e1 / 0.3e1 * t214 * t2432 + 0.16e2 / 0.9e1 * t381 * t389 + 0.4e1 / 0.3e1 * t28 * t2442)
  t2473 = -0.9e1 / 0.4e1 * t233 * t1200 - 0.3e1 / 0.2e1 * t1104 * t1087 - 0.3e1 / 0.2e1 * t1104 * t1160 - 0.3e1 / 0.2e1 * t233 * t1205 - t394 * t1092 / 0.2e1 - 0.5e1 / 0.9e1 * t399 * t1096 * t370 * t372 + t399 * t402 * t1158 * t372 / 0.2e1 - 0.3e1 / 0.8e1 * t399 * t31 * (t2062 + t1919 + t2414 + t1833 + 0.2e1 * t341 * t163 * t1514 * t175 - 0.352e3 / 0.9e1 * t899 * t900 * t241 * t1536 + 0.48e2 * t155 * t1966 * t433 * t726 + 0.8e1 * t1511 * t367 + 0.48e2 * t532 * t606 + 0.24e2 * t532 * t610 + 0.24e2 * t718 * t606 + 0.16e2 * t653 * t550 + 0.24e2 * t994 * t981 - 0.176e3 / 0.3e1 * t916 * t890 + 0.2464e4 / 0.27e2 * t432 * t913 + 0.4e1 * t328 * t329 * t1500 + 0.8e1 * t301 * t957 * t1029 + 0.24e2 * t716 * t501 * t176 - 0.48e2 * t906 * t408 * t654 + 0.96e2 * t1967 * t433 * t629 + 0.3916e4 / 0.27e2 * t496 * t485 * t1976 - 0.10472e5 / 0.81e2 * t336 * t337 * t1498 + 0.16e2 * t531 * t483 * t894 + t1951 + t2029 + t2181 + t1641 - 0.24e2 * t155 * t905 * t433 * t354 * t471 + t2145 + t1875 + t1707 + t2101 + t1672 + t2214) * t372 - 0.3e1 / 0.8e1 * t212 * t2446 * t396 + 0.97926857640000000000000000000000000000000000000000e2 * t1165 * t1274 * t1173 + 0.48963428820000000000000000000000000000000000000000e2 * t1165 * t1224 * t1173 + 0.65284571760000000000000000000000000000000000000000e2 * t1176 * t1190 * t1182 + 0.65284571760000000000000000000000000000000000000000e2 * t1176 * t1166 * t1182 - 0.97926857640000000000000000000000000000000000000000e2 * t1191 * t1186 + 0.48963428820000000000000000000000000000000000000000e2 * t1165 * t1245 * t1173 + 0.32642285880000000000000000000000000000000000000000e2 * t1165 * t1250 * t1173 - 0.10880761960000000000000000000000000000000000000000e2 * t1165 * t1281 * t1173
  t2479 = t1168 * t66
  t2494 = t188 * t205
  t2532 = -0.97926857640000000000000000000000000000000000000000e2 * t1167 * t1186 + 0.21761523920000000000000000000000000000000000000000e2 * t1176 * t1195 * t1182 - 0.87046095680000000000000000000000000000000000000001e2 * t1178 * t1179 * t2479 * t205 - 0.32642285880000000000000000000000000000000000000000e2 * t1196 * t1186 + 0.10427396878333333333333333333333333333333333333333e3 * t1185 * t2479 * t1172 + 0.32642285880000000000000000000000000000000000000000e2 * t1165 * t1254 * t1173 + 0.17758647124527456240000000000000000000000000000000e3 * t1185 * t190 / s0 * t2494 + t1104 * t404 - 0.79166400000000000000000000000000000000000000000000e3 * t10 * t1194 * t207 + 0.12920861304452160000000000000000000000000000000000e4 * t1285 * t179 * t184 * t1288 - 0.12920861304452160000000000000000000000000000000000e4 * t1208 * t1189 * t1289 - 0.12920861304452160000000000000000000000000000000000e4 * t1285 * t370 * t1286 * t1288 - 0.43069537681507200000000000000000000000000000000000e3 * t1208 * t1194 * t1289 - 0.3e1 / 0.2e1 * t394 * t373 + t233 * t1106 / 0.2e1 - 0.5e1 / 0.9e1 * t1104 * t1098 - 0.98958000000000000000000000000000000000000000000000e1 * t1208 * t232 * t1090 * t179 * t1230 + 0.65972000000000000000000000000000000000000000000000e1 * t1208 * t1103 * t402 * t179 * t1230
  t2582 = -0.17812440000000000000000000000000000000000000000000e3 * t1246 * t1241 - 0.25655777777777777777777777777777777777777777777777e2 * t1209 * t1265 - 0.29687400000000000000000000000000000000000000000000e2 * t1208 * t1244 * t370 * t1230 + 0.65972000000000000000000000000000000000000000000000e1 * t1208 * t1280 * t370 * t1230 - 0.76967333333333333333333333333333333333333333333333e2 * t1221 * t1265 - 0.76967333333333333333333333333333333333333333333333e2 * t1233 * t1265 - 0.14085022000000000000000000000000000000000000000000e4 * t1260 * t1239 * t1498 * t205 + 0.69270600000000000000000000000000000000000000000000e2 * t1275 * t1218 - 0.76967333333333333333333333333333333333333333333334e1 * t1282 * t1218 - 0.76967333333333333333333333333333333333333333333333e2 * t10 * t1177 / t193 / t41 / t49 * t42 * t1541 * t2494 - 0.17812440000000000000000000000000000000000000000000e3 * t1225 * t1241 - 0.35624880000000000000000000000000000000000000000000e3 * t1275 * t1241 + 0.23090200000000000000000000000000000000000000000000e2 * t1255 * t1218 + 0.27708240000000000000000000000000000000000000000000e3 * t1209 * t1271 + 0.83124720000000000000000000000000000000000000000000e3 * t1233 * t1271 + 0.83124720000000000000000000000000000000000000000000e3 * t1221 * t1271 + 0.39583200000000000000000000000000000000000000000000e2 * t1282 * t1241
  t2635 = 0.1e1 / t400 / t223
  t2653 = -0.29687400000000000000000000000000000000000000000000e2 * t1208 * t1189 * t1158 * t1230 - 0.36651111111111111111111111111111111111111111111111e1 * t1208 * t30 * t1096 * t179 * t1230 + 0.23090200000000000000000000000000000000000000000000e2 * t1251 * t1218 + 0.34635300000000000000000000000000000000000000000000e2 * t1246 * t1218 - 0.11874960000000000000000000000000000000000000000000e3 * t1255 * t1241 - 0.11874960000000000000000000000000000000000000000000e3 * t1251 * t1241 - 0.98958000000000000000000000000000000000000000000000e1 * t1208 * t32 * t1085 * t1230 - 0.98958000000000000000000000000000000000000000000000e1 * t1208 * t1194 * t1158 * t1230 - 0.98958000000000000000000000000000000000000000000000e1 * t1208 * t393 * t31 * t179 * t1230 + 0.34635300000000000000000000000000000000000000000000e2 * t1225 * t1218 + 0.83381277777777777777777777777777777777777777777776e2 * t1260 * t1213 * t181 * t48 * t205 - 0.19791600000000000000000000000000000000000000000000e2 * t1208 * t1249 * t370 * t1230 - 0.64604306522260800000000000000000000000000000000000e3 * t1260 * t48 * t1237 * t205 * t188 * t181 - t399 * t1090 * t1085 * t372 / 0.2e1 + 0.10e2 / 0.27e2 * t399 * t2635 * t179 * t372 - 0.23749920000000000000000000000000000000000000000000e4 * t33 * t370 * t195 * t206 + 0.83124720000000000000000000000000000000000000000000e4 * t33 * t196 * t182 / t243 * t205 - 0.23749920000000000000000000000000000000000000000000e4 * t10 * t1189 * t207
  t2656 = f.my_piecewise3(t1, 0, t2473 + t2532 + t2582 + t2653)
  t2657 = t1298 ** 2
  t2660 = t1306 ** 2
  t2666 = t1313 ** 2
  t2672 = f.my_piecewise5(t19, 0, t15, 0, -t2441)
  t2676 = f.my_piecewise3(t1299, 0, 0.40e2 / 0.81e2 / t1301 / t2657 * t2660 - 0.16e2 / 0.9e1 * t1303 * t1306 * t1313 + 0.4e1 / 0.3e1 * t1310 * t2666 + 0.16e2 / 0.9e1 * t1311 * t1317 + 0.4e1 / 0.3e1 * t1300 * t2672)
  t2691 = f.my_piecewise3(t1296, 0, -0.3e1 / 0.8e1 * t212 * t2676 * t1444 - t1322 * t1455 / 0.2e1 + t1453 * t1463 / 0.2e1 - 0.5e1 / 0.9e1 * t1461 * t1470 + 0.10e2 / 0.27e2 * t1468 * t2635 * t1431 * t1443)
  d1111 = 0.4e1 * t1294 + 0.4e1 * t1474 + t11 * (t2656 + t2691)

  res = {'v4rho4': d1111}
  return res
