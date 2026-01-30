"""Generated from gga_c_lypr.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
import scipy.special as sp_special
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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))
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
  params_m1_raw = params.m1
  if isinstance(params_m1_raw, (str, bytes, dict)):
    params_m1 = params_m1_raw
  else:
    try:
      params_m1_seq = list(params_m1_raw)
    except TypeError:
      params_m1 = params_m1_raw
    else:
      params_m1_seq = np.asarray(params_m1_seq, dtype=np.float64)
      params_m1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_m1_seq))
  params_m2_raw = params.m2
  if isinstance(params_m2_raw, (str, bytes, dict)):
    params_m2 = params_m2_raw
  else:
    try:
      params_m2_seq = list(params_m2_raw)
    except TypeError:
      params_m2 = params_m2_raw
    else:
      params_m2_seq = np.asarray(params_m2_seq, dtype=np.float64)
      params_m2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_m2_seq))
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  lyp_Cf = 3 / 10 * (3 * jnp.pi ** 2) ** (2 / 3)

  lyp_omega = lambda rr: params_b * jnp.exp(-params_c * rr) / (1 + params_d * rr)

  lyp_delta = lambda rr: (params_c + params_d / (1 + params_d * rr)) * rr

  lyp_aux6 = 1 / 2 ** (8 / 3)

  lyp_t1 = lambda rr, z: -(1 - z ** 2) / (1 + params_d * rr)

  lypr_eta = lambda rr: -2 / (3 * jnp.sqrt(jnp.pi)) * params_m2 * params_omega * jnp.exp(-params_m2 ** 2 * params_omega ** 2 * rr ** 2)

  lyp_t3 = lambda z: -lyp_Cf / 2 * (1 - z ** 2) * (f.opz_pow_n(z, 8 / 3) + f.opz_pow_n(-z, 8 / 3))

  lyp_t2 = lambda rr, z, xt: -xt ** 2 * ((1 - z ** 2) * (47 - 7 * lyp_delta(rr)) / (4 * 18) - 2 / 3)

  lyp_aux4 = lyp_aux6 / 4

  lyp_t6 = lambda z, xs0, xs1: -lyp_aux6 * (2 / 3 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3)) - f.opz_pow_n(z, 2) * xs1 ** 2 * f.opz_pow_n(-z, 8 / 3) / 4 - f.opz_pow_n(-z, 2) * xs0 ** 2 * f.opz_pow_n(z, 8 / 3) / 4)

  lypr_t7 = lambda rr, z, xt, xs0, xs1: -rr * (1 - z ** 2) / 4 * (+7 / 6 * (xt ** 2 - lyp_aux6 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))) + (1 + (1 + z) / 6) * xs0 ** 2 * lyp_aux6 * f.opz_pow_n(z, 8 / 3) + (1 + (1 - z) / 6) * xs1 ** 2 * lyp_aux6 * f.opz_pow_n(-z, 8 / 3))

  lyp_aux5 = lyp_aux4 / (9 * 2)

  lyp_t4 = lambda rr, z, xs0, xs1: lyp_aux4 * (1 - z ** 2) * (5 / 2 - lyp_delta(rr) / 18) * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))

  lyp_t5 = lambda rr, z, xs0, xs1: lyp_aux5 * (1 - z ** 2) * (lyp_delta(rr) - 11) * (xs0 ** 2 * f.opz_pow_n(z, 11 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 11 / 3))

  f_lypr_rr = lambda rr, z, xt, xs0, xs1: params_a * (+jax.scipy.special.erfc(params_m1 * params_omega * rr) * lyp_t1(rr, z) + jax.scipy.special.erfc(params_m2 * params_omega * rr) * lyp_omega(rr) * (+lyp_t2(rr, z, xt) + lyp_t3(z) + lyp_t4(rr, z, xs0, xs1) + lyp_t5(rr, z, xs0, xs1) + lyp_t6(z, xs0, xs1)) + lyp_omega(rr) * lypr_eta(rr) * lypr_t7(rr, z, xt, xs0, xs1))

  f_lypr = lambda rs, z, xt, xs0, xs1: f_lypr_rr(rs / f.RS_FACTOR, z, xt, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_lypr(rs, z, xt, xs0, xs1)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
      f.xt(r0, r1, s0, s1, s2),
      f.xs0(r0, r1, s0, s2),
      f.xs1(r0, r1, s0, s2),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))
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
  params_m1_raw = params.m1
  if isinstance(params_m1_raw, (str, bytes, dict)):
    params_m1 = params_m1_raw
  else:
    try:
      params_m1_seq = list(params_m1_raw)
    except TypeError:
      params_m1 = params_m1_raw
    else:
      params_m1_seq = np.asarray(params_m1_seq, dtype=np.float64)
      params_m1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_m1_seq))
  params_m2_raw = params.m2
  if isinstance(params_m2_raw, (str, bytes, dict)):
    params_m2 = params_m2_raw
  else:
    try:
      params_m2_seq = list(params_m2_raw)
    except TypeError:
      params_m2 = params_m2_raw
    else:
      params_m2_seq = np.asarray(params_m2_seq, dtype=np.float64)
      params_m2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_m2_seq))
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  lyp_Cf = 3 / 10 * (3 * jnp.pi ** 2) ** (2 / 3)

  lyp_omega = lambda rr: params_b * jnp.exp(-params_c * rr) / (1 + params_d * rr)

  lyp_delta = lambda rr: (params_c + params_d / (1 + params_d * rr)) * rr

  lyp_aux6 = 1 / 2 ** (8 / 3)

  lyp_t1 = lambda rr, z: -(1 - z ** 2) / (1 + params_d * rr)

  lypr_eta = lambda rr: -2 / (3 * jnp.sqrt(jnp.pi)) * params_m2 * params_omega * jnp.exp(-params_m2 ** 2 * params_omega ** 2 * rr ** 2)

  lyp_t3 = lambda z: -lyp_Cf / 2 * (1 - z ** 2) * (f.opz_pow_n(z, 8 / 3) + f.opz_pow_n(-z, 8 / 3))

  lyp_t2 = lambda rr, z, xt: -xt ** 2 * ((1 - z ** 2) * (47 - 7 * lyp_delta(rr)) / (4 * 18) - 2 / 3)

  lyp_aux4 = lyp_aux6 / 4

  lyp_t6 = lambda z, xs0, xs1: -lyp_aux6 * (2 / 3 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3)) - f.opz_pow_n(z, 2) * xs1 ** 2 * f.opz_pow_n(-z, 8 / 3) / 4 - f.opz_pow_n(-z, 2) * xs0 ** 2 * f.opz_pow_n(z, 8 / 3) / 4)

  lypr_t7 = lambda rr, z, xt, xs0, xs1: -rr * (1 - z ** 2) / 4 * (+7 / 6 * (xt ** 2 - lyp_aux6 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))) + (1 + (1 + z) / 6) * xs0 ** 2 * lyp_aux6 * f.opz_pow_n(z, 8 / 3) + (1 + (1 - z) / 6) * xs1 ** 2 * lyp_aux6 * f.opz_pow_n(-z, 8 / 3))

  lyp_aux5 = lyp_aux4 / (9 * 2)

  lyp_t4 = lambda rr, z, xs0, xs1: lyp_aux4 * (1 - z ** 2) * (5 / 2 - lyp_delta(rr) / 18) * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))

  lyp_t5 = lambda rr, z, xs0, xs1: lyp_aux5 * (1 - z ** 2) * (lyp_delta(rr) - 11) * (xs0 ** 2 * f.opz_pow_n(z, 11 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 11 / 3))

  f_lypr_rr = lambda rr, z, xt, xs0, xs1: params_a * (+jax.scipy.special.erfc(params_m1 * params_omega * rr) * lyp_t1(rr, z) + jax.scipy.special.erfc(params_m2 * params_omega * rr) * lyp_omega(rr) * (+lyp_t2(rr, z, xt) + lyp_t3(z) + lyp_t4(rr, z, xs0, xs1) + lyp_t5(rr, z, xs0, xs1) + lyp_t6(z, xs0, xs1)) + lyp_omega(rr) * lypr_eta(rr) * lypr_t7(rr, z, xt, xs0, xs1))

  f_lypr = lambda rs, z, xt, xs0, xs1: f_lypr_rr(rs / f.RS_FACTOR, z, xt, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_lypr(rs, z, xt, xs0, xs1)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
      f.xt(r0 / 2, r0 / 2, s0 / 4, s0 / 4, s0 / 4),
      f.xs0(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.xs1(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))
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
  params_m1_raw = params.m1
  if isinstance(params_m1_raw, (str, bytes, dict)):
    params_m1 = params_m1_raw
  else:
    try:
      params_m1_seq = list(params_m1_raw)
    except TypeError:
      params_m1 = params_m1_raw
    else:
      params_m1_seq = np.asarray(params_m1_seq, dtype=np.float64)
      params_m1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_m1_seq))
  params_m2_raw = params.m2
  if isinstance(params_m2_raw, (str, bytes, dict)):
    params_m2 = params_m2_raw
  else:
    try:
      params_m2_seq = list(params_m2_raw)
    except TypeError:
      params_m2 = params_m2_raw
    else:
      params_m2_seq = np.asarray(params_m2_seq, dtype=np.float64)
      params_m2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_m2_seq))
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  lyp_Cf = 3 / 10 * (3 * jnp.pi ** 2) ** (2 / 3)

  lyp_omega = lambda rr: params_b * jnp.exp(-params_c * rr) / (1 + params_d * rr)

  lyp_delta = lambda rr: (params_c + params_d / (1 + params_d * rr)) * rr

  lyp_aux6 = 1 / 2 ** (8 / 3)

  lyp_t1 = lambda rr, z: -(1 - z ** 2) / (1 + params_d * rr)

  lypr_eta = lambda rr: -2 / (3 * jnp.sqrt(jnp.pi)) * params_m2 * params_omega * jnp.exp(-params_m2 ** 2 * params_omega ** 2 * rr ** 2)

  lyp_t3 = lambda z: -lyp_Cf / 2 * (1 - z ** 2) * (f.opz_pow_n(z, 8 / 3) + f.opz_pow_n(-z, 8 / 3))

  lyp_t2 = lambda rr, z, xt: -xt ** 2 * ((1 - z ** 2) * (47 - 7 * lyp_delta(rr)) / (4 * 18) - 2 / 3)

  lyp_aux4 = lyp_aux6 / 4

  lyp_t6 = lambda z, xs0, xs1: -lyp_aux6 * (2 / 3 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3)) - f.opz_pow_n(z, 2) * xs1 ** 2 * f.opz_pow_n(-z, 8 / 3) / 4 - f.opz_pow_n(-z, 2) * xs0 ** 2 * f.opz_pow_n(z, 8 / 3) / 4)

  lypr_t7 = lambda rr, z, xt, xs0, xs1: -rr * (1 - z ** 2) / 4 * (+7 / 6 * (xt ** 2 - lyp_aux6 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))) + (1 + (1 + z) / 6) * xs0 ** 2 * lyp_aux6 * f.opz_pow_n(z, 8 / 3) + (1 + (1 - z) / 6) * xs1 ** 2 * lyp_aux6 * f.opz_pow_n(-z, 8 / 3))

  lyp_aux5 = lyp_aux4 / (9 * 2)

  lyp_t4 = lambda rr, z, xs0, xs1: lyp_aux4 * (1 - z ** 2) * (5 / 2 - lyp_delta(rr) / 18) * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))

  lyp_t5 = lambda rr, z, xs0, xs1: lyp_aux5 * (1 - z ** 2) * (lyp_delta(rr) - 11) * (xs0 ** 2 * f.opz_pow_n(z, 11 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 11 / 3))

  f_lypr_rr = lambda rr, z, xt, xs0, xs1: params_a * (+jax.scipy.special.erfc(params_m1 * params_omega * rr) * lyp_t1(rr, z) + jax.scipy.special.erfc(params_m2 * params_omega * rr) * lyp_omega(rr) * (+lyp_t2(rr, z, xt) + lyp_t3(z) + lyp_t4(rr, z, xs0, xs1) + lyp_t5(rr, z, xs0, xs1) + lyp_t6(z, xs0, xs1)) + lyp_omega(rr) * lypr_eta(rr) * lypr_t7(rr, z, xt, xs0, xs1))

  f_lypr = lambda rs, z, xt, xs0, xs1: f_lypr_rr(rs / f.RS_FACTOR, z, xt, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_lypr(rs, z, xt, xs0, xs1)

  t2 = r0 + r1
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t6 = jax.lax.erfc(params.m1 * params.omega * t4)
  t7 = r0 - r1
  t8 = t7 ** 2
  t9 = t2 ** 2
  t10 = 0.1e1 / t9
  t12 = -t8 * t10 + 0.1e1
  t13 = t6 * t12
  t15 = params.d * t4 + 0.1e1
  t16 = 0.1e1 / t15
  t18 = params.m2 * params.omega
  t20 = jax.lax.erfc(t18 * t4)
  t21 = t20 * params.b
  t23 = jnp.exp(-params.c * t4)
  t24 = t23 * t16
  t26 = s0 + 0.2e1 * s1 + s2
  t27 = t3 ** 2
  t29 = 0.1e1 / t27 / t9
  t30 = t26 * t29
  t32 = params.d * t16 + params.c
  t33 = t32 * t4
  t35 = 0.47e2 - 0.7e1 * t33
  t38 = t12 * t35 / 0.72e2 - 0.2e1 / 0.3e1
  t40 = 3 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t42 = jnp.pi ** 2
  t43 = t42 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = t41 * t44
  t46 = 0.1e1 / t2
  t47 = t7 * t46
  t48 = 0.1e1 + t47
  t49 = t48 <= f.p.zeta_threshold
  t50 = f.p.zeta_threshold ** 2
  t51 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t53 = t52 * t50
  t54 = t48 ** 2
  t55 = t48 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = t56 * t54
  t58 = f.my_piecewise3(t49, t53, t57)
  t59 = 0.1e1 - t47
  t60 = t59 <= f.p.zeta_threshold
  t61 = t59 ** 2
  t62 = t59 ** (0.1e1 / 0.3e1)
  t63 = t62 ** 2
  t64 = t63 * t61
  t65 = f.my_piecewise3(t60, t53, t64)
  t66 = t58 + t65
  t70 = 2 ** (0.1e1 / 0.3e1)
  t71 = t70 * t12
  t73 = 0.5e1 / 0.2e1 - t33 / 0.18e2
  t74 = r0 ** 2
  t75 = r0 ** (0.1e1 / 0.3e1)
  t76 = t75 ** 2
  t78 = 0.1e1 / t76 / t74
  t79 = s0 * t78
  t80 = t79 * t58
  t81 = r1 ** 2
  t82 = r1 ** (0.1e1 / 0.3e1)
  t83 = t82 ** 2
  t85 = 0.1e1 / t83 / t81
  t86 = s2 * t85
  t87 = t86 * t65
  t88 = t80 + t87
  t89 = t73 * t88
  t92 = t33 - 0.11e2
  t94 = t52 * t50 * f.p.zeta_threshold
  t97 = f.my_piecewise3(t49, t94, t56 * t54 * t48)
  t101 = f.my_piecewise3(t60, t94, t63 * t61 * t59)
  t103 = t86 * t101 + t79 * t97
  t104 = t92 * t103
  t109 = f.my_piecewise3(t49, t50, t54)
  t110 = t109 * s2
  t111 = t85 * t65
  t114 = f.my_piecewise3(t60, t50, t61)
  t115 = t114 * s0
  t116 = t78 * t58
  t122 = -t30 * t38 - 0.3e1 / 0.20e2 * t45 * t12 * t66 + t71 * t89 / 0.32e2 + t71 * t104 / 0.576e3 - t70 * (0.2e1 / 0.3e1 * t80 + 0.2e1 / 0.3e1 * t87 - t110 * t111 / 0.4e1 - t115 * t116 / 0.4e1) / 0.8e1
  t123 = t24 * t122
  t125 = params.b * t23
  t126 = jnp.sqrt(jnp.pi)
  t127 = 0.1e1 / t126
  t128 = t16 * t127
  t130 = t125 * t128 * params.m2
  t131 = params.m2 ** 2
  t132 = params.omega ** 2
  t134 = 0.1e1 / t27
  t136 = jnp.exp(-t131 * t132 * t134)
  t137 = params.omega * t136
  t138 = t4 * t12
  t142 = t47 / 0.6e1
  t143 = 0.7e1 / 0.6e1 + t142
  t144 = t143 * s0
  t145 = t70 * t78
  t146 = t145 * t58
  t149 = 0.7e1 / 0.6e1 - t142
  t150 = t149 * s2
  t151 = t70 * t85
  t152 = t151 * t65
  t155 = 0.7e1 / 0.6e1 * t30 - 0.7e1 / 0.48e2 * t70 * t88 + t144 * t146 / 0.8e1 + t150 * t152 / 0.8e1
  t161 = params.a * (-t13 * t16 + t21 * t123 + t130 * t137 * t138 * t155 / 0.6e1)
  t162 = t2 * params.a
  t163 = params.m1 ** 2
  t166 = jnp.exp(-t163 * t132 * t134)
  t170 = 0.1e1 / t3 / t2
  t175 = 0.2e1 / 0.3e1 * t127 * t166 * params.m1 * params.omega * t170 * t12 * t16
  t176 = t7 * t10
  t177 = t9 * t2
  t178 = 0.1e1 / t177
  t179 = t8 * t178
  t181 = -0.2e1 * t176 + 0.2e1 * t179
  t184 = t15 ** 2
  t185 = 0.1e1 / t184
  t189 = t13 * t185 * params.d * t170 / 0.3e1
  t195 = 0.2e1 / 0.3e1 * t127 * t136 * t18 * t170 * params.b * t123
  t201 = t21 * params.c * t170 * t23 * t16 * t122 / 0.3e1
  t202 = t21 * t23
  t207 = t202 * t185 * t122 * params.d * t170 / 0.3e1
  t210 = t26 / t27 / t177
  t212 = 0.8e1 / 0.3e1 * t210 * t38
  t214 = params.d ** 2
  t217 = 0.1e1 / t27 / t2
  t220 = -t214 * t185 * t217 + t32 * t170
  t222 = 0.7e1 / 0.3e1 * t12 * t220
  t229 = t56 * t48
  t230 = t46 - t176
  t233 = f.my_piecewise3(t49, 0, 0.8e1 / 0.3e1 * t229 * t230)
  t234 = t63 * t59
  t235 = -t230
  t238 = f.my_piecewise3(t60, 0, 0.8e1 / 0.3e1 * t234 * t235)
  t243 = t70 * t181
  t249 = t71 * t220 * t88 / 0.1728e4
  t252 = 0.1e1 / t76 / t74 / r0
  t253 = s0 * t252
  t254 = t253 * t58
  t256 = t79 * t233
  t257 = t86 * t238
  t258 = -0.8e1 / 0.3e1 * t254 + t256 + t257
  t268 = -t71 * t220 * t103 / 0.1728e4
  t273 = f.my_piecewise3(t49, 0, 0.11e2 / 0.3e1 * t57 * t230)
  t277 = f.my_piecewise3(t60, 0, 0.11e2 / 0.3e1 * t64 * t235)
  t288 = f.my_piecewise3(t49, 0, 0.2e1 * t48 * t230)
  t297 = f.my_piecewise3(t60, 0, 0.2e1 * t59 * t235)
  t310 = t212 - t30 * (t181 * t35 / 0.72e2 + t222 / 0.72e2) - 0.3e1 / 0.20e2 * t45 * t181 * t66 - 0.3e1 / 0.20e2 * t45 * t12 * (t233 + t238) + t243 * t89 / 0.32e2 + t249 + t71 * t73 * t258 / 0.32e2 + t243 * t104 / 0.576e3 + t268 + t71 * t92 * (-0.8e1 / 0.3e1 * t253 * t97 + t79 * t273 + t86 * t277) / 0.576e3 - t70 * (-0.16e2 / 0.9e1 * t254 + 0.2e1 / 0.3e1 * t256 + 0.2e1 / 0.3e1 * t257 - t288 * s2 * t111 / 0.4e1 - t110 * t85 * t238 / 0.4e1 - t297 * s0 * t116 / 0.4e1 + 0.2e1 / 0.3e1 * t115 * t252 * t58 - t115 * t78 * t233 / 0.4e1) / 0.8e1
  t320 = t136 * t12 * t155
  t323 = params.b * params.c * t217 * t23 * t16 * t127 * params.m2 * params.omega * t320 / 0.18e2
  t332 = t125 * t185 * t127 * params.m2 * t137 * t217 * t12 * t155 * params.d / 0.18e2
  t340 = t125 * t128 * t131 * params.m2 * t132 * params.omega * t10 * t320 / 0.9e1
  t345 = t130 * t137 * t170 * t12 * t155 / 0.18e2
  t351 = 0.28e2 / 0.9e1 * t210
  t354 = t230 / 0.6e1
  t377 = -t175 - t6 * t181 * t16 - t189 + t195 + t201 + t207 + t21 * t24 * t310 + t323 + t332 + t340 - t345 + t130 * t137 * t4 * t181 * t155 / 0.6e1 + t130 * t137 * t138 * (-t351 - 0.7e1 / 0.48e2 * t70 * t258 + t354 * s0 * t146 / 0.8e1 - t144 * t252 * t70 * t58 / 0.3e1 + t144 * t145 * t233 / 0.8e1 - t354 * s2 * t152 / 0.8e1 + t150 * t151 * t238 / 0.8e1) / 0.6e1
  vrho_0_ = t162 * t377 + t161
  t380 = 0.2e1 * t176 + 0.2e1 * t179
  t390 = -t46 - t176
  t393 = f.my_piecewise3(t49, 0, 0.8e1 / 0.3e1 * t229 * t390)
  t394 = -t390
  t397 = f.my_piecewise3(t60, 0, 0.8e1 / 0.3e1 * t234 * t394)
  t402 = t70 * t380
  t405 = t79 * t393
  t408 = 0.1e1 / t83 / t81 / r1
  t409 = s2 * t408
  t410 = t409 * t65
  t412 = t86 * t397
  t413 = t405 - 0.8e1 / 0.3e1 * t410 + t412
  t421 = f.my_piecewise3(t49, 0, 0.11e2 / 0.3e1 * t57 * t390)
  t427 = f.my_piecewise3(t60, 0, 0.11e2 / 0.3e1 * t64 * t394)
  t438 = f.my_piecewise3(t49, 0, 0.2e1 * t48 * t390)
  t450 = f.my_piecewise3(t60, 0, 0.2e1 * t59 * t394)
  t460 = t212 - t30 * (t380 * t35 / 0.72e2 + t222 / 0.72e2) - 0.3e1 / 0.20e2 * t45 * t380 * t66 - 0.3e1 / 0.20e2 * t45 * t12 * (t393 + t397) + t402 * t89 / 0.32e2 + t249 + t71 * t73 * t413 / 0.32e2 + t402 * t104 / 0.576e3 + t268 + t71 * t92 * (t79 * t421 - 0.8e1 / 0.3e1 * t409 * t101 + t86 * t427) / 0.576e3 - t70 * (0.2e1 / 0.3e1 * t405 - 0.16e2 / 0.9e1 * t410 + 0.2e1 / 0.3e1 * t412 - t438 * s2 * t111 / 0.4e1 + 0.2e1 / 0.3e1 * t110 * t408 * t65 - t110 * t85 * t397 / 0.4e1 - t450 * s0 * t116 / 0.4e1 - t115 * t78 * t393 / 0.4e1) / 0.8e1
  t470 = t390 / 0.6e1
  t493 = -t175 - t6 * t380 * t16 - t189 + t195 + t201 + t207 + t21 * t24 * t460 + t323 + t332 + t340 - t345 + t130 * t137 * t4 * t380 * t155 / 0.6e1 + t130 * t137 * t138 * (-t351 - 0.7e1 / 0.48e2 * t70 * t413 + t470 * s0 * t146 / 0.8e1 + t144 * t145 * t393 / 0.8e1 - t470 * s2 * t152 / 0.8e1 - t150 * t408 * t70 * t65 / 0.3e1 + t150 * t151 * t397 / 0.8e1) / 0.6e1
  vrho_1_ = t162 * t493 + t161
  t495 = t29 * t38
  t514 = 0.7e1 / 0.6e1 * t29
  vsigma_0_ = t162 * (t21 * t24 * (-t495 + t71 * t73 * t78 * t58 / 0.32e2 + t71 * t92 * t78 * t97 / 0.576e3 - t70 * (0.2e1 / 0.3e1 * t116 - t114 * t78 * t58 / 0.4e1) / 0.8e1) + t130 * t137 * t138 * (t514 - 0.7e1 / 0.48e2 * t146 + t143 * t78 * t70 * t58 / 0.8e1) / 0.6e1)
  vsigma_1_ = t162 * (-0.2e1 * t202 * t16 * t29 * t38 + 0.7e1 / 0.18e2 * t125 * t128 * t18 * t136 * t178 * t12)
  vsigma_2_ = t162 * (t21 * t24 * (-t495 + t71 * t73 * t85 * t65 / 0.32e2 + t71 * t92 * t85 * t101 / 0.576e3 - t70 * (0.2e1 / 0.3e1 * t111 - t109 * t85 * t65 / 0.4e1) / 0.8e1) + t130 * t137 * t138 * (t514 - 0.7e1 / 0.48e2 * t152 + t149 * t85 * t70 * t65 / 0.8e1) / 0.6e1)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  vsigma_0_ = _b(vsigma_0_)
  vsigma_1_ = _b(vsigma_1_)
  vsigma_2_ = _b(vsigma_2_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1), 'vsigma': jnp.stack([vsigma_0_, vsigma_1_, vsigma_2_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))
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
  params_m1_raw = params.m1
  if isinstance(params_m1_raw, (str, bytes, dict)):
    params_m1 = params_m1_raw
  else:
    try:
      params_m1_seq = list(params_m1_raw)
    except TypeError:
      params_m1 = params_m1_raw
    else:
      params_m1_seq = np.asarray(params_m1_seq, dtype=np.float64)
      params_m1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_m1_seq))
  params_m2_raw = params.m2
  if isinstance(params_m2_raw, (str, bytes, dict)):
    params_m2 = params_m2_raw
  else:
    try:
      params_m2_seq = list(params_m2_raw)
    except TypeError:
      params_m2 = params_m2_raw
    else:
      params_m2_seq = np.asarray(params_m2_seq, dtype=np.float64)
      params_m2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_m2_seq))
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  lyp_Cf = 3 / 10 * (3 * jnp.pi ** 2) ** (2 / 3)

  lyp_omega = lambda rr: params_b * jnp.exp(-params_c * rr) / (1 + params_d * rr)

  lyp_delta = lambda rr: (params_c + params_d / (1 + params_d * rr)) * rr

  lyp_aux6 = 1 / 2 ** (8 / 3)

  lyp_t1 = lambda rr, z: -(1 - z ** 2) / (1 + params_d * rr)

  lypr_eta = lambda rr: -2 / (3 * jnp.sqrt(jnp.pi)) * params_m2 * params_omega * jnp.exp(-params_m2 ** 2 * params_omega ** 2 * rr ** 2)

  lyp_t3 = lambda z: -lyp_Cf / 2 * (1 - z ** 2) * (f.opz_pow_n(z, 8 / 3) + f.opz_pow_n(-z, 8 / 3))

  lyp_t2 = lambda rr, z, xt: -xt ** 2 * ((1 - z ** 2) * (47 - 7 * lyp_delta(rr)) / (4 * 18) - 2 / 3)

  lyp_aux4 = lyp_aux6 / 4

  lyp_t6 = lambda z, xs0, xs1: -lyp_aux6 * (2 / 3 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3)) - f.opz_pow_n(z, 2) * xs1 ** 2 * f.opz_pow_n(-z, 8 / 3) / 4 - f.opz_pow_n(-z, 2) * xs0 ** 2 * f.opz_pow_n(z, 8 / 3) / 4)

  lypr_t7 = lambda rr, z, xt, xs0, xs1: -rr * (1 - z ** 2) / 4 * (+7 / 6 * (xt ** 2 - lyp_aux6 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))) + (1 + (1 + z) / 6) * xs0 ** 2 * lyp_aux6 * f.opz_pow_n(z, 8 / 3) + (1 + (1 - z) / 6) * xs1 ** 2 * lyp_aux6 * f.opz_pow_n(-z, 8 / 3))

  lyp_aux5 = lyp_aux4 / (9 * 2)

  lyp_t4 = lambda rr, z, xs0, xs1: lyp_aux4 * (1 - z ** 2) * (5 / 2 - lyp_delta(rr) / 18) * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))

  lyp_t5 = lambda rr, z, xs0, xs1: lyp_aux5 * (1 - z ** 2) * (lyp_delta(rr) - 11) * (xs0 ** 2 * f.opz_pow_n(z, 11 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 11 / 3))

  f_lypr_rr = lambda rr, z, xt, xs0, xs1: params_a * (+jax.scipy.special.erfc(params_m1 * params_omega * rr) * lyp_t1(rr, z) + jax.scipy.special.erfc(params_m2 * params_omega * rr) * lyp_omega(rr) * (+lyp_t2(rr, z, xt) + lyp_t3(z) + lyp_t4(rr, z, xs0, xs1) + lyp_t5(rr, z, xs0, xs1) + lyp_t6(z, xs0, xs1)) + lyp_omega(rr) * lypr_eta(rr) * lypr_t7(rr, z, xt, xs0, xs1))

  f_lypr = lambda rs, z, xt, xs0, xs1: f_lypr_rr(rs / f.RS_FACTOR, z, xt, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_lypr(rs, z, xt, xs0, xs1)

  t2 = r0 ** (0.1e1 / 0.3e1)
  t3 = 0.1e1 / t2
  t5 = jax.lax.erfc(params.m1 * params.omega * t3)
  t7 = params.d * t3 + 0.1e1
  t8 = 0.1e1 / t7
  t10 = params.m2 * params.omega
  t12 = jax.lax.erfc(t10 * t3)
  t13 = t12 * params.b
  t15 = jnp.exp(-params.c * t3)
  t16 = t15 * t8
  t17 = r0 ** 2
  t18 = t2 ** 2
  t20 = 0.1e1 / t18 / t17
  t21 = s0 * t20
  t23 = params.d * t8 + params.c
  t24 = t23 * t3
  t26 = -0.1e1 / 0.72e2 - 0.7e1 / 0.72e2 * t24
  t28 = 3 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t34 = 0.1e1 <= f.p.zeta_threshold
  t35 = f.p.zeta_threshold ** 2
  t36 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = f.my_piecewise3(t34, t37 * t35, 1)
  t43 = 0.5e1 / 0.2e1 - t24 / 0.18e2
  t44 = t43 * s0
  t45 = t20 * t39
  t48 = t24 - 0.11e2
  t49 = t48 * s0
  t52 = f.my_piecewise3(t34, t37 * t35 * f.p.zeta_threshold, 1)
  t53 = t20 * t52
  t56 = 2 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t58 = s0 * t57
  t61 = f.my_piecewise3(t34, t35, 1)
  t62 = t61 * s0
  t64 = t57 * t20 * t39
  t70 = -t21 * t26 - 0.3e1 / 0.10e2 * t29 * t32 * t39 + t44 * t45 / 0.8e1 + t49 * t53 / 0.144e3 - t56 * (0.4e1 / 0.3e1 * t58 * t45 - t62 * t64 / 0.2e1) / 0.8e1
  t71 = t16 * t70
  t73 = params.b * t15
  t74 = jnp.sqrt(jnp.pi)
  t75 = 0.1e1 / t74
  t77 = t73 * t8 * t75
  t78 = params.m2 ** 2
  t79 = params.omega ** 2
  t81 = 0.1e1 / t18
  t83 = jnp.exp(-t78 * t79 * t81)
  t84 = t17 * r0
  t86 = t83 / t84
  t93 = r0 * params.a
  t94 = params.m1 ** 2
  t97 = jnp.exp(-t94 * t79 * t81)
  t101 = 0.1e1 / t2 / r0
  t106 = t7 ** 2
  t107 = 0.1e1 / t106
  t109 = params.d * t101
  t130 = 0.1e1 / t18 / t84
  t134 = params.d ** 2
  t140 = -t134 * t107 / t18 / r0 + t23 * t101
  t147 = t130 * t39
  t171 = t17 ** 2
  t173 = 0.1e1 / t2 / t171
  t178 = params.omega * t83
  vrho_0_ = params.a * (-t5 * t8 + t13 * t71 + 0.7e1 / 0.36e2 * t77 * t10 * t86 * s0) + t93 * (-0.2e1 / 0.3e1 * t75 * t97 * params.m1 * params.omega * t101 * t8 - t5 * t107 * t109 / 0.3e1 + 0.2e1 / 0.3e1 * t75 * t83 * t10 * t101 * params.b * t71 + t13 * params.c * t101 * t15 * t8 * t70 / 0.3e1 + t13 * t15 * t107 * t70 * t109 / 0.3e1 + t13 * t16 * (0.8e1 / 0.3e1 * s0 * t130 * t26 - 0.7e1 / 0.216e3 * t21 * t140 + t140 * s0 * t45 / 0.432e3 - t44 * t147 / 0.3e1 - t140 * s0 * t53 / 0.432e3 - t49 * t130 * t52 / 0.54e2 - t56 * (-0.32e2 / 0.9e1 * t58 * t147 + 0.4e1 / 0.3e1 * t62 * t57 * t130 * t39) / 0.8e1) + 0.7e1 / 0.108e3 * params.b * params.c * t173 * t15 * t8 * t75 * params.m2 * t178 * s0 + 0.7e1 / 0.108e3 * t73 * t107 * t75 * params.m2 * t178 * t173 * s0 * params.d + 0.7e1 / 0.54e2 * t77 * t78 * params.m2 * t79 * params.omega / t18 / t171 * t83 * s0 - 0.7e1 / 0.12e2 * t77 * t10 * t83 / t171 * s0)
  vsigma_0_ = t93 * (t13 * t16 * (-t20 * t26 + t43 * t20 * t39 / 0.8e1 + t48 * t20 * t52 / 0.144e3 - t56 * (0.4e1 / 0.3e1 * t64 - t61 * t57 * t45 / 0.2e1) / 0.8e1) + 0.7e1 / 0.36e2 * t77 * t10 * t86)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = jnp.sqrt(jnp.pi)
  t2 = 0.1e1 / t1
  t3 = params.m1 ** 2
  t4 = params.omega ** 2
  t6 = r0 ** (0.1e1 / 0.3e1)
  t7 = t6 ** 2
  t8 = 0.1e1 / t7
  t10 = jnp.exp(-t3 * t4 * t8)
  t12 = t2 * t10 * params.m1
  t14 = 0.1e1 / t6 / r0
  t16 = 0.1e1 / t6
  t18 = params.d * t16 + 0.1e1
  t19 = 0.1e1 / t18
  t25 = jax.lax.erfc(params.m1 * params.omega * t16)
  t26 = t18 ** 2
  t27 = 0.1e1 / t26
  t28 = t25 * t27
  t29 = params.d * t14
  t32 = params.m2 ** 2
  t35 = jnp.exp(-t32 * t4 * t8)
  t36 = t2 * t35
  t37 = params.m2 * params.omega
  t38 = t36 * t37
  t39 = t14 * params.b
  t41 = jnp.exp(-params.c * t16)
  t42 = t41 * t19
  t43 = r0 ** 2
  t45 = 0.1e1 / t7 / t43
  t46 = s0 * t45
  t48 = params.d * t19 + params.c
  t49 = t48 * t16
  t51 = -0.1e1 / 0.72e2 - 0.7e1 / 0.72e2 * t49
  t53 = 3 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t55 = jnp.pi ** 2
  t56 = t55 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t59 = 0.1e1 <= f.p.zeta_threshold
  t60 = f.p.zeta_threshold ** 2
  t61 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t62 = t61 ** 2
  t64 = f.my_piecewise3(t59, t62 * t60, 1)
  t68 = 0.5e1 / 0.2e1 - t49 / 0.18e2
  t69 = t68 * s0
  t70 = t45 * t64
  t73 = t49 - 0.11e2
  t74 = t73 * s0
  t77 = f.my_piecewise3(t59, t62 * t60 * f.p.zeta_threshold, 1)
  t78 = t45 * t77
  t81 = 2 ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t83 = s0 * t82
  t86 = f.my_piecewise3(t59, t60, 1)
  t87 = t86 * s0
  t89 = t82 * t45 * t64
  t95 = -t46 * t51 - 0.3e1 / 0.10e2 * t54 * t57 * t64 + t69 * t70 / 0.8e1 + t74 * t78 / 0.144e3 - t81 * (0.4e1 / 0.3e1 * t83 * t70 - t87 * t89 / 0.2e1) / 0.8e1
  t96 = t42 * t95
  t101 = jax.lax.erfc(t37 * t16)
  t102 = t101 * params.b
  t103 = t102 * params.c
  t104 = t14 * t41
  t105 = t19 * t95
  t109 = t102 * t41
  t110 = t27 * t95
  t114 = t43 * r0
  t116 = 0.1e1 / t7 / t114
  t117 = s0 * t116
  t120 = params.d ** 2
  t121 = t120 * t27
  t126 = -t121 / t7 / r0 + t48 * t14
  t127 = 0.7e1 / 0.216e3 * t126
  t129 = t126 / 0.54e2
  t130 = t129 * s0
  t133 = t116 * t64
  t137 = -t126 / 0.3e1
  t138 = t137 * s0
  t141 = t116 * t77
  t147 = t82 * t116 * t64
  t153 = 0.8e1 / 0.3e1 * t117 * t51 - t46 * t127 + t130 * t70 / 0.8e1 - t69 * t133 / 0.3e1 + t138 * t78 / 0.144e3 - t74 * t141 / 0.54e2 - t81 * (-0.32e2 / 0.9e1 * t83 * t133 + 0.4e1 / 0.3e1 * t87 * t147) / 0.8e1
  t154 = t42 * t153
  t156 = params.b * params.c
  t157 = t43 ** 2
  t159 = 0.1e1 / t6 / t157
  t160 = t159 * t41
  t163 = t2 * params.m2
  t164 = params.omega * t35
  t166 = t163 * t164 * s0
  t169 = params.b * t41
  t170 = t27 * t2
  t172 = t169 * t170 * params.m2
  t178 = t19 * t2
  t179 = t169 * t178
  t180 = t32 * params.m2
  t181 = t4 * params.omega
  t182 = t180 * t181
  t184 = 0.1e1 / t7 / t157
  t185 = t184 * t35
  t191 = t35 / t157
  t199 = r0 * params.a
  t207 = 0.1e1 / t26 / t18
  t209 = 0.1e1 / t114
  t210 = t120 * params.d * t207 * t209
  t212 = t121 * t45
  t215 = 0.1e1 / t6 / t43
  t216 = t48 * t215
  t229 = t184 * t64
  t263 = t157 * r0
  t265 = 0.1e1 / t7 / t263
  t266 = t265 * t41
  t271 = t35 * s0 * params.d
  t283 = params.d * t215
  t287 = params.c ** 2
  t298 = t120 * t45
  t308 = 0.1e1 / t6 / t263
  t324 = t157 * t43
  t325 = 0.1e1 / t324
  t331 = t36 * t37 * t45
  t335 = t102 * t42 * (-0.88e2 / 0.9e1 * s0 * t184 * t51 + 0.16e2 / 0.3e1 * t117 * t127 - t46 * (-0.7e1 / 0.324e3 * t210 + 0.7e1 / 0.108e3 * t212 - 0.7e1 / 0.162e3 * t216) + (-t210 / 0.81e2 + t212 / 0.27e2 - 0.2e1 / 0.81e2 * t216) * s0 * t70 / 0.8e1 - 0.2e1 / 0.3e1 * t130 * t133 + 0.11e2 / 0.9e1 * t69 * t229 + (0.2e1 / 0.9e1 * t210 - 0.2e1 / 0.3e1 * t212 + 0.4e1 / 0.9e1 * t216) * s0 * t78 / 0.144e3 - t138 * t141 / 0.27e2 + 0.11e2 / 0.162e3 * t74 * t184 * t77 - t81 * (0.352e3 / 0.27e2 * t83 * t229 - 0.44e2 / 0.9e1 * t87 * t82 * t184 * t64) / 0.8e1) + 0.2e1 / 0.9e1 * t102 * params.c * t45 * t41 * t27 * t95 * params.d + 0.7e1 / 0.162e3 * t156 * t266 * t27 * t163 * params.omega * t271 + 0.2e1 / 0.3e1 * t103 * t104 * t19 * t153 - 0.4e1 / 0.9e1 * t103 * t215 * t41 * t105 - 0.4e1 / 0.9e1 * t109 * t110 * t283 + t102 * t287 * t45 * t41 * t105 / 0.9e1 + 0.2e1 / 0.3e1 * t109 * t27 * t153 * t29 + 0.2e1 / 0.9e1 * t109 * t207 * t95 * t298 - 0.4e1 / 0.9e1 * t12 * params.omega * t45 * t27 * params.d - 0.77e2 / 0.162e3 * t172 * t164 * t308 * s0 * params.d + 0.7e1 / 0.162e3 * t169 * t207 * t2 * params.m2 * t164 * t265 * s0 * t120 + 0.7e1 / 0.81e2 * t169 * t170 * t180 * t181 * t325 * t271 + 0.4e1 / 0.9e1 * t331 * t156 * t96
  t348 = t2 * t180
  t383 = t32 ** 2
  t385 = t4 ** 2
  t411 = 0.4e1 / 0.9e1 * t331 * t169 * t110 * params.d + 0.7e1 / 0.324e3 * params.b * t287 * t266 * t19 * t166 + 0.7e1 / 0.81e2 * t156 * t325 * t41 * t19 * t348 * t181 * t35 * s0 - 0.77e2 / 0.162e3 * t156 * t308 * t41 * t19 * t166 - 0.161e3 / 0.162e3 * t179 * t182 * t265 * t35 * s0 + 0.7e1 / 0.3e1 * t179 * t37 * t35 / t263 * s0 - 0.8e1 / 0.9e1 * t38 * t215 * params.b * t96 + 0.4e1 / 0.3e1 * t38 * t39 * t154 + 0.4e1 / 0.9e1 * t348 * t181 * t209 * t35 * params.b * t96 + 0.7e1 / 0.81e2 * t179 * t383 * params.m2 * t385 * params.omega / t6 / t324 * t35 * s0 + 0.4e1 / 0.9e1 * t28 * t283 - 0.2e1 / 0.9e1 * t25 * t207 * t298 + 0.8e1 / 0.9e1 * t12 * params.omega * t215 * t19 - 0.4e1 / 0.9e1 * t2 * t3 * params.m1 * t181 * t209 * t10 * t19
  v2rho2_0_ = 0.2e1 * params.a * (-0.2e1 / 0.3e1 * t12 * params.omega * t14 * t19 - t28 * t29 / 0.3e1 + 0.2e1 / 0.3e1 * t38 * t39 * t96 + t103 * t104 * t105 / 0.3e1 + t109 * t110 * t29 / 0.3e1 + t102 * t154 + 0.7e1 / 0.108e3 * t156 * t160 * t19 * t166 + 0.7e1 / 0.108e3 * t172 * t164 * t159 * s0 * params.d + 0.7e1 / 0.54e2 * t179 * t182 * t185 * s0 - 0.7e1 / 0.12e2 * t179 * t37 * t191 * s0) + t199 * (t335 + t411)
  t422 = t86 * t82
  t428 = -t45 * t51 + t68 * t45 * t64 / 0.8e1 + t73 * t45 * t77 / 0.144e3 - t81 * (0.4e1 / 0.3e1 * t89 - t422 * t70 / 0.2e1) / 0.8e1
  t429 = t42 * t428
  v2rhosigma_0_ = params.a * (t102 * t429 + 0.7e1 / 0.36e2 * t179 * t37 * t35 * t209) + t199 * (0.2e1 / 0.3e1 * t38 * t39 * t429 + t103 * t104 * t19 * t428 / 0.3e1 + t109 * t27 * t428 * t29 / 0.3e1 + t102 * t42 * (0.8e1 / 0.3e1 * t116 * t51 - t45 * t127 + t129 * t45 * t64 / 0.8e1 - t68 * t116 * t64 / 0.3e1 + t137 * t45 * t77 / 0.144e3 - t73 * t116 * t77 / 0.54e2 - t81 * (-0.32e2 / 0.9e1 * t147 + 0.4e1 / 0.3e1 * t422 * t133) / 0.8e1) + 0.7e1 / 0.108e3 * t156 * t160 * t178 * t37 * t35 + 0.7e1 / 0.108e3 * t169 * t170 * t37 * t35 * t159 * params.d + 0.7e1 / 0.54e2 * t179 * t182 * t185 - 0.7e1 / 0.12e2 * t179 * t37 * t191)
  v2sigma2_0_ = 0.0e0
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.m2 * params.omega
  t2 = r0 ** (0.1e1 / 0.3e1)
  t3 = 0.1e1 / t2
  t5 = jnp.erfc(t1 * t3)
  t6 = t5 * params.b
  t8 = jnp.exp(-params.c * t3)
  t10 = params.d * t3 + 0.1e1
  t11 = 0.1e1 / t10
  t12 = t8 * t11
  t13 = r0 ** 2
  t14 = t13 ** 2
  t15 = t2 ** 2
  t17 = 0.1e1 / t15 / t14
  t18 = s0 * t17
  t20 = params.d * t11 + params.c
  t21 = t20 * t3
  t23 = -0.1e1 / 0.72e2 - 0.7e1 / 0.72e2 * t21
  t26 = t13 * r0
  t28 = 0.1e1 / t15 / t26
  t29 = s0 * t28
  t30 = params.d ** 2
  t31 = t10 ** 2
  t32 = 0.1e1 / t31
  t33 = t30 * t32
  t38 = 0.1e1 / t2 / r0
  t40 = -t33 / t15 / r0 + t20 * t38
  t41 = 0.7e1 / 0.216e3 * t40
  t45 = 0.1e1 / t15 / t13
  t46 = s0 * t45
  t47 = t30 * params.d
  t49 = 0.1e1 / t31 / t10
  t50 = t47 * t49
  t51 = 0.1e1 / t26
  t52 = t50 * t51
  t54 = t33 * t45
  t57 = 0.1e1 / t2 / t13
  t58 = t20 * t57
  t60 = -0.7e1 / 0.324e3 * t52 + 0.7e1 / 0.108e3 * t54 - 0.7e1 / 0.162e3 * t58
  t66 = (-t52 / 0.81e2 + t54 / 0.27e2 - 0.2e1 / 0.81e2 * t58) * s0
  t67 = 0.1e1 <= f.p.zeta_threshold
  t68 = f.p.zeta_threshold ** 2
  t69 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t70 = t69 ** 2
  t72 = f.my_piecewise3(t67, t70 * t68, 1)
  t73 = t45 * t72
  t77 = t40 * s0 / 0.54e2
  t78 = t28 * t72
  t83 = (0.5e1 / 0.2e1 - t21 / 0.18e2) * s0
  t84 = t17 * t72
  t91 = (0.2e1 / 0.9e1 * t52 - 0.2e1 / 0.3e1 * t54 + 0.4e1 / 0.9e1 * t58) * s0
  t94 = f.my_piecewise3(t67, t70 * t68 * f.p.zeta_threshold, 1)
  t95 = t45 * t94
  t100 = -t40 * s0 / 0.3e1
  t101 = t28 * t94
  t105 = (t21 - 0.11e2) * s0
  t106 = t17 * t94
  t109 = 2 ** (0.1e1 / 0.3e1)
  t110 = t109 ** 2
  t111 = s0 * t110
  t114 = f.my_piecewise3(t67, t68, 1)
  t115 = t114 * s0
  t123 = -0.88e2 / 0.9e1 * t18 * t23 + 0.16e2 / 0.3e1 * t29 * t41 - t46 * t60 + t66 * t73 / 0.8e1 - 0.2e1 / 0.3e1 * t77 * t78 + 0.11e2 / 0.9e1 * t83 * t84 + t91 * t95 / 0.144e3 - t100 * t101 / 0.27e2 + 0.11e2 / 0.162e3 * t105 * t106 - t109 * (0.352e3 / 0.27e2 * t111 * t84 - 0.44e2 / 0.9e1 * t115 * t110 * t17 * t72) / 0.8e1
  t124 = t12 * t123
  t127 = t6 * params.c * t45
  t128 = t8 * t32
  t130 = 3 ** (0.1e1 / 0.3e1)
  t131 = t130 ** 2
  t132 = jnp.pi ** 2
  t133 = t132 ** (0.1e1 / 0.3e1)
  t134 = t133 ** 2
  t151 = -t46 * t23 - 0.3e1 / 0.10e2 * t131 * t134 * t72 + t83 * t73 / 0.8e1 + t105 * t95 / 0.144e3 - t109 * (0.4e1 / 0.3e1 * t111 * t73 - t115 * t110 * t45 * t72 / 0.2e1) / 0.8e1
  t153 = t128 * t151 * params.d
  t158 = jnp.erfc(params.m1 * params.omega * t3)
  t159 = t158 * t32
  t160 = params.d * t57
  t163 = t158 * t49
  t164 = t30 * t45
  t167 = params.b * params.c
  t168 = t14 * r0
  t170 = 0.1e1 / t15 / t168
  t171 = t170 * t8
  t174 = jnp.sqrt(jnp.pi)
  t175 = 0.1e1 / t174
  t176 = t175 * params.m2
  t177 = t176 * params.omega
  t178 = params.m2 ** 2
  t179 = params.omega ** 2
  t181 = 0.1e1 / t15
  t183 = jnp.exp(-t178 * t179 * t181)
  t184 = t183 * s0
  t185 = t184 * params.d
  t186 = t177 * t185
  t189 = params.m1 ** 2
  t192 = jnp.exp(-t189 * t179 * t181)
  t194 = t175 * t192 * params.m1
  t196 = t32 * params.d
  t200 = t6 * params.c
  t201 = t38 * t8
  t222 = 0.8e1 / 0.3e1 * t29 * t23 - t46 * t41 + t77 * t73 / 0.8e1 - t83 * t78 / 0.3e1 + t100 * t95 / 0.144e3 - t105 * t101 / 0.54e2 - t109 * (-0.32e2 / 0.9e1 * t111 * t78 + 0.4e1 / 0.3e1 * t115 * t110 * t28 * t72) / 0.8e1
  t223 = t11 * t222
  t227 = t57 * t8
  t228 = t11 * t151
  t232 = t6 * t8
  t233 = t32 * t151
  t237 = params.c ** 2
  t238 = t6 * t237
  t239 = t45 * t8
  t243 = t32 * t222
  t244 = params.d * t38
  t248 = t49 * t151
  t252 = params.b * t8
  t253 = t49 * t175
  t255 = t252 * t253 * params.m2
  t256 = params.omega * t183
  t257 = t170 * s0
  t262 = t32 * t175
  t263 = t178 * params.m2
  t265 = t252 * t262 * t263
  t266 = t179 * params.omega
  t267 = t14 * t13
  t268 = 0.1e1 / t267
  t273 = t6 * t124 + 0.2e1 / 0.9e1 * t127 * t153 + 0.4e1 / 0.9e1 * t159 * t160 - 0.2e1 / 0.9e1 * t163 * t164 + 0.7e1 / 0.162e3 * t167 * t171 * t32 * t186 - 0.4e1 / 0.9e1 * t194 * params.omega * t45 * t196 + 0.2e1 / 0.3e1 * t200 * t201 * t223 - 0.4e1 / 0.9e1 * t200 * t227 * t228 - 0.4e1 / 0.9e1 * t232 * t233 * t160 + t238 * t239 * t228 / 0.9e1 + 0.2e1 / 0.3e1 * t232 * t243 * t244 + 0.2e1 / 0.9e1 * t232 * t248 * t164 + 0.7e1 / 0.162e3 * t255 * t256 * t257 * t30 + 0.7e1 / 0.81e2 * t265 * t266 * t268 * t185
  t274 = t175 * t183
  t276 = t274 * t1 * t45
  t277 = t12 * t151
  t278 = t167 * t277
  t281 = t233 * params.d
  t282 = t252 * t281
  t285 = params.b * t237
  t289 = t176 * t256 * s0
  t295 = t175 * t263
  t298 = t295 * t266 * t183 * s0
  t302 = 0.1e1 / t2 / t168
  t309 = t252 * t262 * params.m2
  t316 = t252 * t11 * t175
  t317 = t263 * t266
  t329 = t274 * t1
  t330 = t57 * params.b
  t334 = t38 * params.b
  t335 = t12 * t222
  t340 = t295 * t266 * t51
  t341 = t183 * params.b
  t342 = t341 * t277
  t345 = t178 ** 2
  t346 = t345 * params.m2
  t347 = t179 ** 2
  t348 = t347 * params.omega
  t349 = t346 * t348
  t351 = 0.1e1 / t2 / t267
  t363 = t175 * t189 * params.m1 * t266
  t368 = 0.4e1 / 0.9e1 * t276 * t278 + 0.4e1 / 0.9e1 * t276 * t282 + 0.7e1 / 0.324e3 * t285 * t171 * t11 * t289 + 0.7e1 / 0.81e2 * t167 * t268 * t8 * t11 * t298 - 0.77e2 / 0.162e3 * t167 * t302 * t8 * t11 * t289 - 0.77e2 / 0.162e3 * t309 * t256 * t302 * s0 * params.d - 0.161e3 / 0.162e3 * t316 * t317 * t170 * t183 * s0 + 0.7e1 / 0.3e1 * t316 * t1 * t183 / t168 * s0 - 0.8e1 / 0.9e1 * t329 * t330 * t277 + 0.4e1 / 0.3e1 * t329 * t334 * t335 + 0.4e1 / 0.9e1 * t340 * t342 + 0.7e1 / 0.81e2 * t316 * t349 * t351 * t183 * s0 + 0.8e1 / 0.9e1 * t194 * params.omega * t57 * t11 - 0.4e1 / 0.9e1 * t363 * t51 * t192 * t11
  t379 = t30 ** 2
  t380 = t31 ** 2
  t381 = 0.1e1 / t380
  t384 = 0.1e1 / t2 / t14
  t385 = t379 * t381 * t384
  t387 = 0.1e1 / t14
  t388 = t50 * t387
  t390 = t33 * t28
  t393 = 0.1e1 / t2 / t26
  t394 = t20 * t393
  t409 = t170 * t72
  t436 = 0.1232e4 / 0.27e2 * t257 * t23 - 0.88e2 / 0.3e1 * t18 * t41 + 0.8e1 * t29 * t60 - t46 * (-0.7e1 / 0.324e3 * t385 + 0.35e2 / 0.324e3 * t388 - 0.91e2 / 0.486e3 * t390 + 0.49e2 / 0.486e3 * t394) + (-t385 / 0.81e2 + 0.5e1 / 0.81e2 * t388 - 0.26e2 / 0.243e3 * t390 + 0.14e2 / 0.243e3 * t394) * s0 * t73 / 0.8e1 - t66 * t78 + 0.11e2 / 0.3e1 * t77 * t84 - 0.154e3 / 0.27e2 * t83 * t409 + (0.2e1 / 0.9e1 * t385 - 0.10e2 / 0.9e1 * t388 + 0.52e2 / 0.27e2 * t390 - 0.28e2 / 0.27e2 * t394) * s0 * t95 / 0.144e3 - t91 * t101 / 0.18e2 + 0.11e2 / 0.54e2 * t100 * t106 - 0.77e2 / 0.243e3 * t105 * t170 * t94 - t109 * (-0.4928e4 / 0.81e2 * t111 * t409 + 0.616e3 / 0.27e2 * t115 * t110 * t170 * t72) / 0.8e1
  t458 = t30 * t28
  t462 = t47 * t387
  t465 = params.d * t393
  t469 = t274 * t1 * t387
  t474 = t14 * t26
  t475 = 0.1e1 / t474
  t476 = t475 * t8
  t483 = t184 * t30
  t488 = 0.1e1 / t2 / t474
  t489 = t488 * t8
  t497 = 0.1e1 / t15 / t267
  t498 = t497 * t8
  t503 = t237 * params.c
  t512 = t6 * t12 * t436 + 0.2e1 / 0.9e1 * t6 * params.c * t387 * t8 * t49 * t151 * t30 + 0.2e1 / 0.3e1 * t127 * t128 * t222 * params.d - 0.8e1 / 0.9e1 * t6 * params.c * t28 * t153 + t6 * t237 * t387 * t153 / 0.9e1 + 0.8e1 / 0.9e1 * t163 * t458 - 0.2e1 / 0.9e1 * t158 * t381 * t462 - 0.28e2 / 0.27e2 * t159 * t465 + 0.4e1 / 0.9e1 * t469 * t167 * t8 * t281 + 0.7e1 / 0.324e3 * t285 * t476 * t32 * t186 + 0.7e1 / 0.162e3 * t167 * t476 * t49 * t177 * t483 + 0.7e1 / 0.81e2 * t167 * t489 * t32 * t295 * t266 * t185 - 0.91e2 / 0.162e3 * t167 * t498 * t32 * t186 + t6 * t503 * t387 * t8 * t228 / 0.27e2 + t232 * t32 * t123 * t244
  t574 = 0.2e1 / 0.3e1 * t232 * t49 * t222 * t164 + 0.2e1 / 0.9e1 * t232 * t381 * t151 * t462 - 0.4e1 / 0.9e1 * t363 * t384 * t192 * t196 - 0.4e1 / 0.9e1 * t194 * params.omega * t387 * t49 * t30 + t200 * t201 * t11 * t123 + t238 * t239 * t223 / 0.3e1 - 0.4e1 / 0.9e1 * t238 * t28 * t8 * t228 - 0.4e1 / 0.3e1 * t232 * t243 * t160 - 0.8e1 / 0.9e1 * t232 * t248 * t458 + 0.16e2 / 0.9e1 * t194 * params.omega * t28 * t196 - 0.4e1 / 0.3e1 * t200 * t227 * t223 + 0.28e2 / 0.27e2 * t200 * t393 * t8 * t228 + 0.28e2 / 0.27e2 * t232 * t233 * t465 + 0.7e1 / 0.162e3 * t252 * t381 * t175 * params.m2 * t256 * t475 * s0 * t47 + 0.7e1 / 0.81e2 * t252 * t253 * t263 * t266 * t488 * t483
  t579 = 0.1e1 / t15 / t474
  t587 = t175 * t346
  t603 = t274 * t1 * t28
  t614 = t476 * t11
  t644 = 0.7e1 / 0.81e2 * t252 * t262 * t346 * t348 * t579 * t185 + 0.7e1 / 0.81e2 * t167 * t579 * t8 * t11 * t587 * t348 * t183 * s0 - 0.91e2 / 0.162e3 * t255 * t256 * t497 * s0 * t30 - 0.7e1 / 0.6e1 * t265 * t266 * t475 * t185 - 0.16e2 / 0.9e1 * t603 * t282 + 0.2e1 / 0.9e1 * t469 * t285 * t277 + 0.4e1 / 0.3e1 * t276 * t252 * t243 * params.d + 0.7e1 / 0.972e3 * params.b * t503 * t614 * t289 + 0.7e1 / 0.162e3 * t285 * t489 * t11 * t298 + 0.4e1 / 0.9e1 * t469 * t252 * t248 * t30 + 0.4e1 / 0.3e1 * t276 * t167 * t335 - 0.16e2 / 0.9e1 * t603 * t278 - 0.7e1 / 0.6e1 * t167 * t614 * t298 + 0.805e3 / 0.243e3 * t167 * t351 * t8 * t11 * t289 + 0.805e3 / 0.243e3 * t309 * t256 * t351 * s0 * params.d
  t651 = t295 * t266 * t384 * t183
  t659 = t14 ** 2
  t710 = t189 ** 2
  t718 = -0.91e2 / 0.324e3 * t285 * t498 * t11 * t289 + 0.4e1 / 0.9e1 * t651 * t278 + 0.4e1 / 0.9e1 * t651 * t282 + 0.14e2 / 0.243e3 * t316 * t345 * t263 * t347 * t266 / t659 * t183 * s0 - 0.98e2 / 0.81e2 * t316 * t349 * t488 * t183 * s0 - 0.8e1 / 0.3e1 * t329 * t330 * t335 - 0.52e2 / 0.27e2 * t295 * t266 * t387 * t342 - 0.35e2 / 0.3e1 * t316 * t1 * t183 * t268 * s0 + 0.56e2 / 0.27e2 * t329 * t393 * params.b * t277 + 0.3493e4 / 0.486e3 * t316 * t317 * t497 * t183 * s0 + 0.2e1 * t329 * t334 * t124 + 0.4e1 / 0.3e1 * t340 * t341 * t335 + 0.8e1 / 0.27e2 * t587 * t348 * t17 * t342 - 0.56e2 / 0.27e2 * t194 * params.omega * t393 * t11 + 0.52e2 / 0.27e2 * t363 * t387 * t192 * t11 - 0.8e1 / 0.27e2 * t175 * t710 * params.m1 * t348 * t17 * t192 * t11
  v3rho3_0_ = 0.3e1 * params.a * (t273 + t368) + r0 * params.a * (t512 + t574 + t644 + t718)

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.b * params.c
  t2 = r0 ** 2
  t3 = t2 ** 2
  t4 = t3 * t2
  t5 = r0 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t8 = 0.1e1 / t6 / t4
  t9 = 0.1e1 / t5
  t11 = jnp.exp(-params.c * t9)
  t12 = t8 * t11
  t14 = params.d * t9 + 0.1e1
  t15 = t14 ** 2
  t16 = 0.1e1 / t15
  t19 = jnp.sqrt(jnp.pi)
  t20 = 0.1e1 / t19
  t21 = t20 * params.m2
  t22 = t21 * params.omega
  t23 = params.m2 ** 2
  t24 = params.omega ** 2
  t26 = 0.1e1 / t6
  t28 = jnp.exp(-t23 * t24 * t26)
  t29 = t28 * s0
  t30 = t29 * params.d
  t31 = t22 * t30
  t34 = t20 * t28
  t35 = params.m2 * params.omega
  t36 = 0.1e1 / t3
  t38 = t34 * t35 * t36
  t39 = t1 * t11
  t41 = 0.1e1 / t6 / t2
  t42 = s0 * t41
  t43 = 0.1e1 / t14
  t45 = params.d * t43 + params.c
  t46 = t45 * t9
  t48 = -0.1e1 / 0.72e2 - 0.7e1 / 0.72e2 * t46
  t50 = 3 ** (0.1e1 / 0.3e1)
  t51 = t50 ** 2
  t52 = jnp.pi ** 2
  t53 = t52 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 <= f.p.zeta_threshold
  t57 = f.p.zeta_threshold ** 2
  t58 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t61 = f.my_piecewise3(t56, t59 * t57, 1)
  t66 = (0.5e1 / 0.2e1 - t46 / 0.18e2) * s0
  t67 = t41 * t61
  t71 = (t46 - 0.11e2) * s0
  t74 = f.my_piecewise3(t56, t59 * t57 * f.p.zeta_threshold, 1)
  t75 = t41 * t74
  t78 = 2 ** (0.1e1 / 0.3e1)
  t79 = t78 ** 2
  t80 = s0 * t79
  t83 = f.my_piecewise3(t56, t57, 1)
  t84 = t83 * s0
  t92 = -t42 * t48 - 0.3e1 / 0.10e2 * t51 * t54 * t61 + t66 * t67 / 0.8e1 + t71 * t75 / 0.144e3 - t78 * (0.4e1 / 0.3e1 * t80 * t67 - t84 * t79 * t41 * t61 / 0.2e1) / 0.8e1
  t93 = t16 * t92
  t94 = t93 * params.d
  t95 = t39 * t94
  t98 = params.c ** 2
  t99 = params.b * t98
  t100 = t2 * r0
  t101 = t3 * t100
  t102 = 0.1e1 / t101
  t103 = t102 * t11
  t109 = 0.1e1 / t15 / t14
  t112 = params.d ** 2
  t113 = t29 * t112
  t114 = t22 * t113
  t118 = 0.1e1 / t5 / t101
  t119 = t118 * t11
  t122 = t23 * params.m2
  t123 = t20 * t122
  t124 = t24 * params.omega
  t125 = t123 * t124
  t126 = t125 * t30
  t130 = jnp.erfc(t35 * t9)
  t131 = t130 * params.b
  t132 = t11 * t43
  t133 = t3 * r0
  t135 = 0.1e1 / t6 / t133
  t136 = s0 * t135
  t140 = 0.1e1 / t6 / t3
  t141 = s0 * t140
  t142 = t112 * t16
  t147 = 0.1e1 / t5 / r0
  t149 = -t142 / t6 / r0 + t45 * t147
  t150 = 0.7e1 / 0.216e3 * t149
  t154 = 0.1e1 / t6 / t100
  t155 = s0 * t154
  t156 = t112 * params.d
  t157 = t156 * t109
  t158 = 0.1e1 / t100
  t159 = t157 * t158
  t161 = t142 * t41
  t164 = 0.1e1 / t5 / t2
  t165 = t45 * t164
  t167 = -0.7e1 / 0.324e3 * t159 + 0.7e1 / 0.108e3 * t161 - 0.7e1 / 0.162e3 * t165
  t170 = t112 ** 2
  t171 = t15 ** 2
  t172 = 0.1e1 / t171
  t173 = t170 * t172
  t175 = 0.1e1 / t5 / t3
  t176 = t173 * t175
  t178 = t157 * t36
  t180 = t142 * t154
  t183 = 0.1e1 / t5 / t100
  t184 = t45 * t183
  t186 = -0.7e1 / 0.324e3 * t176 + 0.35e2 / 0.324e3 * t178 - 0.91e2 / 0.486e3 * t180 + 0.49e2 / 0.486e3 * t184
  t193 = (-t176 / 0.81e2 + 0.5e1 / 0.81e2 * t178 - 0.26e2 / 0.243e3 * t180 + 0.14e2 / 0.243e3 * t184) * s0
  t200 = (-t159 / 0.81e2 + t161 / 0.27e2 - 0.2e1 / 0.81e2 * t165) * s0
  t201 = t154 * t61
  t204 = t149 * s0 / 0.54e2
  t205 = t140 * t61
  t208 = t135 * t61
  t216 = (0.2e1 / 0.9e1 * t176 - 0.10e2 / 0.9e1 * t178 + 0.52e2 / 0.27e2 * t180 - 0.28e2 / 0.27e2 * t184) * s0
  t223 = (0.2e1 / 0.9e1 * t159 - 0.2e1 / 0.3e1 * t161 + 0.4e1 / 0.9e1 * t165) * s0
  t224 = t154 * t74
  t229 = -t149 * s0 / 0.3e1
  t230 = t140 * t74
  t233 = t135 * t74
  t245 = 0.1232e4 / 0.27e2 * t136 * t48 - 0.88e2 / 0.3e1 * t141 * t150 + 0.8e1 * t155 * t167 - t42 * t186 + t193 * t67 / 0.8e1 - t200 * t201 + 0.11e2 / 0.3e1 * t204 * t205 - 0.154e3 / 0.27e2 * t66 * t208 + t216 * t75 / 0.144e3 - t223 * t224 / 0.18e2 + 0.11e2 / 0.54e2 * t229 * t230 - 0.77e2 / 0.243e3 * t71 * t233 - t78 * (-0.4928e4 / 0.81e2 * t80 * t208 + 0.616e3 / 0.27e2 * t84 * t79 * t135 * t61) / 0.8e1
  t246 = t132 * t245
  t248 = t131 * t98
  t249 = t41 * t11
  t270 = 0.8e1 / 0.3e1 * t155 * t48 - t42 * t150 + t204 * t67 / 0.8e1 - t66 * t201 / 0.3e1 + t229 * t75 / 0.144e3 - t71 * t224 / 0.54e2 - t78 * (-0.32e2 / 0.9e1 * t80 * t201 + 0.4e1 / 0.3e1 * t84 * t79 * t154 * t61) / 0.8e1
  t271 = t43 * t270
  t275 = t154 * t11
  t276 = t43 * t92
  t280 = t131 * t11
  t281 = t16 * t270
  t282 = params.d * t164
  t286 = t109 * t92
  t287 = t112 * t154
  t291 = params.m1 ** 2
  t294 = jnp.exp(-t291 * t24 * t26)
  t296 = t20 * t294 * params.m1
  t298 = t16 * params.d
  t302 = t131 * params.c
  t303 = t164 * t11
  t307 = t183 * t11
  t311 = params.d * t183
  t315 = t98 * params.c
  t316 = t131 * t315
  t317 = t36 * t11
  t321 = -0.91e2 / 0.162e3 * t1 * t12 * t16 * t31 + 0.4e1 / 0.9e1 * t38 * t95 + 0.7e1 / 0.324e3 * t99 * t103 * t16 * t31 + 0.7e1 / 0.162e3 * t1 * t103 * t109 * t114 + 0.7e1 / 0.81e2 * t1 * t119 * t16 * t126 + t131 * t246 + t248 * t249 * t271 / 0.3e1 - 0.4e1 / 0.9e1 * t248 * t275 * t276 - 0.4e1 / 0.3e1 * t280 * t281 * t282 - 0.8e1 / 0.9e1 * t280 * t286 * t287 + 0.16e2 / 0.9e1 * t296 * params.omega * t154 * t298 - 0.4e1 / 0.3e1 * t302 * t303 * t271 + 0.28e2 / 0.27e2 * t302 * t307 * t276 + 0.28e2 / 0.27e2 * t280 * t93 * t311 + t316 * t317 * t276 / 0.27e2
  t348 = -0.88e2 / 0.9e1 * t141 * t48 + 0.16e2 / 0.3e1 * t155 * t150 - t42 * t167 + t200 * t67 / 0.8e1 - 0.2e1 / 0.3e1 * t204 * t201 + 0.11e2 / 0.9e1 * t66 * t205 + t223 * t75 / 0.144e3 - t229 * t224 / 0.27e2 + 0.11e2 / 0.162e3 * t71 * t230 - t78 * (0.352e3 / 0.27e2 * t80 * t205 - 0.44e2 / 0.9e1 * t84 * t79 * t140 * t61) / 0.8e1
  t349 = t16 * t348
  t350 = params.d * t147
  t353 = t109 * t270
  t354 = t112 * t41
  t358 = t172 * t92
  t359 = t156 * t36
  t363 = t291 * params.m1
  t365 = t20 * t363 * t124
  t371 = t109 * t112
  t375 = t147 * t11
  t376 = t43 * t348
  t381 = jnp.erfc(params.m1 * params.omega * t9)
  t382 = t381 * t109
  t385 = t381 * t172
  t388 = t381 * t16
  t392 = t131 * params.c * t36
  t393 = t11 * t109
  t395 = t393 * t92 * t112
  t399 = t131 * params.c * t41
  t400 = t11 * t16
  t402 = t400 * t270 * params.d
  t406 = t131 * params.c * t154
  t408 = t400 * t92 * params.d
  t412 = t131 * t98 * t36
  t416 = t34 * t35 * t41
  t417 = t132 * t270
  t418 = t1 * t417
  t422 = t34 * t35 * t154
  t423 = t132 * t92
  t424 = t1 * t423
  t427 = t280 * t349 * t350 + 0.2e1 / 0.3e1 * t280 * t353 * t354 + 0.2e1 / 0.9e1 * t280 * t358 * t359 - 0.4e1 / 0.9e1 * t365 * t175 * t294 * t298 - 0.4e1 / 0.9e1 * t296 * params.omega * t36 * t371 + t302 * t375 * t376 + 0.8e1 / 0.9e1 * t382 * t287 - 0.2e1 / 0.9e1 * t385 * t359 - 0.28e2 / 0.27e2 * t388 * t311 + 0.2e1 / 0.9e1 * t392 * t395 + 0.2e1 / 0.3e1 * t399 * t402 - 0.8e1 / 0.9e1 * t406 * t408 + t412 * t408 / 0.9e1 + 0.4e1 / 0.3e1 * t416 * t418 - 0.16e2 / 0.9e1 * t422 * t424
  t429 = t103 * t43
  t433 = t123 * t124 * t28 * s0
  t437 = 0.1e1 / t5 / t4
  t441 = params.omega * t28
  t443 = t21 * t441 * s0
  t446 = params.b * t11
  t447 = t16 * t20
  t449 = t446 * t447 * params.m2
  t461 = t123 * t124 * t175 * t28
  t464 = t446 * t94
  t467 = t172 * t20
  t469 = t446 * t467 * params.m2
  t475 = t109 * t20
  t477 = t446 * t475 * t122
  t482 = t23 ** 2
  t483 = t482 * params.m2
  t485 = t446 * t447 * t483
  t486 = t24 ** 2
  t487 = t486 * params.omega
  t489 = 0.1e1 / t6 / t101
  t494 = t489 * t11
  t495 = t494 * t43
  t497 = t20 * t483
  t500 = t497 * t487 * t28 * s0
  t504 = t446 * t475 * params.m2
  t505 = t8 * s0
  t511 = t446 * t447 * t122
  t518 = t99 * t423
  t521 = t281 * params.d
  t522 = t446 * t521
  t525 = -0.7e1 / 0.6e1 * t1 * t429 * t433 + 0.805e3 / 0.243e3 * t1 * t437 * t11 * t43 * t443 + 0.805e3 / 0.243e3 * t449 * t441 * t437 * s0 * params.d - 0.91e2 / 0.324e3 * t99 * t12 * t43 * t443 + 0.4e1 / 0.9e1 * t461 * t424 + 0.4e1 / 0.9e1 * t461 * t464 + 0.7e1 / 0.162e3 * t469 * t441 * t102 * s0 * t156 + 0.7e1 / 0.81e2 * t477 * t124 * t118 * t113 + 0.7e1 / 0.81e2 * t485 * t487 * t489 * t30 + 0.7e1 / 0.81e2 * t1 * t495 * t500 - 0.91e2 / 0.162e3 * t504 * t441 * t505 * t112 - 0.7e1 / 0.6e1 * t511 * t124 * t102 * t30 - 0.16e2 / 0.9e1 * t422 * t464 + 0.2e1 / 0.9e1 * t38 * t518 + 0.4e1 / 0.3e1 * t416 * t522
  t526 = params.b * t315
  t530 = t119 * t43
  t534 = t286 * t112
  t535 = t446 * t534
  t539 = t123 * t124 * t36
  t540 = t28 * params.b
  t541 = t540 * t423
  t545 = t446 * t43 * t20
  t546 = 0.1e1 / t4
  t552 = t34 * t35
  t553 = t183 * params.b
  t557 = t122 * t124
  t563 = t147 * params.b
  t564 = t132 * t348
  t569 = t123 * t124 * t158
  t570 = t540 * t417
  t574 = t497 * t487 * t140
  t577 = t482 * t122
  t578 = t486 * t124
  t579 = t577 * t578
  t580 = t3 ** 2
  t581 = 0.1e1 / t580
  t587 = t483 * t487
  t593 = t164 * params.b
  t605 = t291 ** 2
  t608 = t20 * t605 * params.m1 * t487
  t613 = 0.7e1 / 0.972e3 * t526 * t429 * t443 + 0.7e1 / 0.162e3 * t99 * t530 * t433 + 0.4e1 / 0.9e1 * t38 * t535 - 0.52e2 / 0.27e2 * t539 * t541 - 0.35e2 / 0.3e1 * t545 * t35 * t28 * t546 * s0 + 0.56e2 / 0.27e2 * t552 * t553 * t423 + 0.3493e4 / 0.486e3 * t545 * t557 * t8 * t28 * s0 + 0.2e1 * t552 * t563 * t564 + 0.4e1 / 0.3e1 * t569 * t570 + 0.8e1 / 0.27e2 * t574 * t541 + 0.14e2 / 0.243e3 * t545 * t579 * t581 * t28 * s0 - 0.98e2 / 0.81e2 * t545 * t587 * t118 * t28 * s0 - 0.8e1 / 0.3e1 * t552 * t593 * t417 - 0.56e2 / 0.27e2 * t296 * params.omega * t183 * t43 + 0.52e2 / 0.27e2 * t365 * t36 * t294 * t43 - 0.8e1 / 0.27e2 * t608 * t140 * t294 * t43
  t619 = 0.1e1 / t133
  t620 = t156 * t619
  t624 = 0.1e1 / t171 / t14
  t627 = 0.1e1 / t5 / t133
  t628 = t170 * t627
  t631 = t112 * t140
  t634 = params.d * t175
  t676 = 0.16e2 / 0.9e1 * t385 * t620 - 0.8e1 / 0.27e2 * t381 * t624 * t628 - 0.320e3 / 0.81e2 * t382 * t631 + 0.280e3 / 0.81e2 * t388 * t634 - 0.32e2 / 0.9e1 * t406 * t402 - 0.16e2 / 0.9e1 * t131 * params.c * t619 * t395 + 0.320e3 / 0.81e2 * t131 * params.c * t140 * t408 + 0.8e1 / 0.27e2 * t131 * params.c * t627 * t11 * t172 * t92 * t156 + 0.4e1 / 0.9e1 * t412 * t402 + 0.4e1 / 0.81e2 * t131 * t315 * t627 * t408 + 0.4e1 / 0.3e1 * t399 * t400 * t348 * params.d + 0.8e1 / 0.9e1 * t392 * t393 * t270 * t112 + 0.4e1 / 0.27e2 * t131 * t98 * t627 * t395 - 0.8e1 / 0.9e1 * t131 * t98 * t619 * t408
  t678 = 0.1e1 / t6 / t580
  t679 = t678 * t11
  t685 = t580 * r0
  t686 = 0.1e1 / t685
  t687 = t686 * t11
  t696 = t123 * t124 * t135 * t28
  t700 = t34 * t35 * t627
  t709 = 0.1e1 / t5 / t580
  t710 = t709 * t11
  t711 = t710 * t16
  t723 = t581 * t11
  t743 = t34 * t35 * t619
  t746 = 0.28e2 / 0.243e3 * t1 * t679 * t109 * t125 * t113 + 0.28e2 / 0.243e3 * t1 * t687 * t16 * t497 * t487 * t30 + 0.16e2 / 0.27e2 * t696 * t95 + 0.8e1 / 0.27e2 * t700 * t99 * t11 * t94 + 0.16e2 / 0.27e2 * t700 * t39 * t534 + 0.7e1 / 0.729e3 * t526 * t711 * t31 + 0.7e1 / 0.243e3 * t99 * t710 * t109 * t114 + 0.14e2 / 0.243e3 * t99 * t679 * t16 * t126 - 0.35e2 / 0.81e2 * t99 * t723 * t16 * t31 - 0.70e2 / 0.81e2 * t1 * t723 * t109 * t114 - 0.434e3 / 0.243e3 * t1 * t711 * t126 + 0.16e2 / 0.9e1 * t38 * t39 * t521 + 0.4340e4 / 0.729e3 * t1 * t494 * t16 * t31 - 0.32e2 / 0.9e1 * t743 * t95
  t750 = t29 * t156
  t754 = t8 * t61
  t772 = t170 * params.d * t624 * t135
  t774 = t173 * t627
  t776 = t157 * t619
  t778 = t142 * t140
  t780 = t45 * t175
  t821 = -t78 * (0.83776e5 / 0.243e3 * t80 * t754 - 0.10472e5 / 0.81e2 * t84 * t79 * t8 * t61) / 0.8e1 + 0.4928e4 / 0.27e2 * t136 * t150 - 0.176e3 / 0.3e1 * t141 * t167 + 0.32e2 / 0.3e1 * t155 * t186 - t42 * (-0.7e1 / 0.243e3 * t772 + 0.49e2 / 0.243e3 * t774 - 0.406e3 / 0.729e3 * t776 + 0.175e3 / 0.243e3 * t778 - 0.245e3 / 0.729e3 * t780) + (0.8e1 / 0.27e2 * t772 - 0.56e2 / 0.27e2 * t774 + 0.464e3 / 0.81e2 * t776 - 0.200e3 / 0.27e2 * t778 + 0.280e3 / 0.81e2 * t780) * s0 * t75 / 0.144e3 - 0.20944e5 / 0.81e2 * t505 * t48 + (-0.4e1 / 0.243e3 * t772 + 0.28e2 / 0.243e3 * t774 - 0.232e3 / 0.729e3 * t776 + 0.100e3 / 0.243e3 * t778 - 0.140e3 / 0.729e3 * t780) * s0 * t67 / 0.8e1 - 0.4e1 / 0.3e1 * t193 * t201 + 0.22e2 / 0.3e1 * t200 * t205 - 0.616e3 / 0.27e2 * t204 * t208 + 0.2618e4 / 0.81e2 * t66 * t754 - 0.2e1 / 0.27e2 * t216 * t224 + 0.11e2 / 0.27e2 * t223 * t230 - 0.308e3 / 0.243e3 * t229 * t233 + 0.1309e4 / 0.729e3 * t71 * t8 * t74
  t831 = t98 ** 2
  t869 = 0.14e2 / 0.243e3 * t1 * t710 * t172 * t22 * t750 + t131 * t132 * t821 + 0.4e1 / 0.3e1 * t280 * t16 * t245 * t350 + 0.4e1 / 0.27e2 * t316 * t317 * t271 + t131 * t831 * t627 * t11 * t276 / 0.81e2 + 0.4e1 / 0.3e1 * t280 * t109 * t348 * t354 + 0.8e1 / 0.9e1 * t280 * t172 * t270 * t359 + 0.304e3 / 0.81e2 * t365 * t627 * t294 * t298 - 0.8e1 / 0.3e1 * t302 * t303 * t376 - 0.16e2 / 0.9e1 * t248 * t275 * t271 + 0.160e3 / 0.81e2 * t248 * t140 * t11 * t276 - 0.8e1 / 0.27e2 * t316 * t619 * t11 * t276 - 0.8e1 / 0.3e1 * t280 * t349 * t282 - 0.32e2 / 0.9e1 * t280 * t353 * t287
  t897 = t135 * t294
  t923 = t497 * t487 * t546 * t28
  t926 = -0.16e2 / 0.9e1 * t280 * t358 * t620 + 0.112e3 / 0.27e2 * t280 * t281 * t311 + 0.320e3 / 0.81e2 * t280 * t286 * t631 + 0.112e3 / 0.27e2 * t302 * t307 * t271 - 0.280e3 / 0.81e2 * t302 * t175 * t11 * t276 - 0.280e3 / 0.81e2 * t280 * t93 * t634 + 0.8e1 / 0.27e2 * t280 * t624 * t92 * t628 - 0.32e2 / 0.81e2 * t608 * t546 * t294 * t298 - 0.16e2 / 0.27e2 * t365 * t897 * t371 + 0.2e1 / 0.3e1 * t248 * t249 * t376 + 0.32e2 / 0.9e1 * t296 * params.omega * t619 * t371 - 0.16e2 / 0.27e2 * t296 * params.omega * t627 * t172 * t156 - 0.640e3 / 0.81e2 * t296 * params.omega * t140 * t298 + 0.4e1 / 0.3e1 * t302 * t375 * t43 * t245 + 0.32e2 / 0.81e2 * t923 * t464
  t954 = t723 * t43
  t958 = t710 * t43
  t981 = 0.16e2 / 0.27e2 * t696 * t535 + 0.14e2 / 0.243e3 * t446 * t624 * t20 * params.m2 * t441 * t709 * s0 * t170 + 0.28e2 / 0.243e3 * t446 * t467 * t122 * t124 * t678 * t750 + 0.4340e4 / 0.729e3 * t504 * t441 * t489 * s0 * t112 + 0.9310e4 / 0.729e3 * t511 * t124 * t581 * t30 - 0.35e2 / 0.243e3 * t526 * t954 * t443 - 0.217e3 / 0.243e3 * t99 * t958 * t433 + 0.16e2 / 0.9e1 * t461 * t418 + 0.32e2 / 0.81e2 * t923 * t424 + 0.8e1 / 0.9e1 * t38 * t99 * t417 - 0.16e2 / 0.9e1 * t743 * t518 + 0.9961e4 / 0.729e3 * t545 * t587 * t709 * t28 * s0 + 0.8e1 / 0.3e1 * t569 * t540 * t564 + 0.32e2 / 0.27e2 * t574 * t570
  t982 = t20 * t577
  t998 = t482 ** 2
  t1000 = t486 ** 2
  t1048 = 0.16e2 / 0.81e2 * t982 * t578 * t437 * t541 - 0.208e3 / 0.27e2 * t539 * t570 - 0.8e1 / 0.3e1 * t497 * t487 * t135 * t541 - 0.40600e5 / 0.729e3 * t545 * t557 * t489 * t28 * s0 + 0.28e2 / 0.729e3 * t545 * t998 * params.m2 * t1000 * params.omega / t6 / t685 * t28 * s0 - 0.16e2 / 0.3e1 * t552 * t593 * t564 + 0.8e1 / 0.3e1 * t552 * t563 * t246 - 0.560e3 / 0.81e2 * t552 * t175 * params.b * t423 + 0.224e3 / 0.27e2 * t552 * t553 * t417 + 0.736e3 / 0.81e2 * t123 * t124 * t619 * t541 + 0.70e2 * t545 * t35 * t28 * t102 * s0 - 0.308e3 / 0.243e3 * t545 * t579 * t686 * t28 * s0 + 0.560e3 / 0.81e2 * t296 * params.omega * t175 * t43 - 0.736e3 / 0.81e2 * t365 * t619 * t294 * t43 + 0.8e1 / 0.3e1 * t608 * t897 * t43
  t1064 = t34 * t35 * t140
  t1097 = -0.16e2 / 0.81e2 * t20 * t605 * t363 * t578 * t437 * t294 * t43 - 0.64e2 / 0.9e1 * t422 * t522 - 0.32e2 / 0.9e1 * t743 * t535 - 0.64e2 / 0.9e1 * t422 * t418 + 0.640e3 / 0.81e2 * t1064 * t424 + 0.640e3 / 0.81e2 * t1064 * t464 + 0.7e1 / 0.2916e4 * params.b * t831 * t958 * t443 + 0.8e1 / 0.81e2 * t700 * t526 * t423 + 0.8e1 / 0.3e1 * t416 * t446 * t349 * params.d + 0.16e2 / 0.9e1 * t38 * t446 * t353 * t112 + 0.16e2 / 0.27e2 * t700 * t446 * t358 * t156 + 0.8e1 / 0.3e1 * t416 * t1 * t564 - 0.18130e5 / 0.729e3 * t1 * t530 * t443 + 0.9310e4 / 0.729e3 * t1 * t954 * t433
  t1102 = t679 * t43
  t1120 = t123 * t124 * t627 * t28
  t1142 = 0.1e1 / t5 / t685
  t1163 = -0.448e3 / 0.243e3 * t485 * t487 * t678 * t30 - 0.448e3 / 0.243e3 * t1 * t1102 * t500 - 0.70e2 / 0.81e2 * t469 * t441 * t581 * s0 * t156 - 0.434e3 / 0.243e3 * t477 * t124 * t709 * t113 + 0.2170e4 / 0.729e3 * t99 * t495 * t443 - 0.304e3 / 0.81e2 * t1120 * t424 - 0.304e3 / 0.81e2 * t1120 * t464 - 0.18130e5 / 0.729e3 * t449 * t441 * t118 * s0 * params.d + 0.14e2 / 0.729e3 * t526 * t1102 * t433 + 0.28e2 / 0.243e3 * t446 * t475 * t483 * t487 * t686 * t113 + 0.56e2 / 0.729e3 * t446 * t447 * t577 * t578 * t1142 * t30 + 0.14e2 / 0.243e3 * t99 * t687 * t43 * t500 + 0.56e2 / 0.729e3 * t1 * t1142 * t11 * t43 * t982 * t578 * t28 * s0 + 0.8e1 / 0.27e2 * t696 * t518 + 0.16e2 / 0.9e1 * t461 * t522
  v4rho4_0_ = 0.4e1 * params.a * (t321 + t427 + t525 + t613) + r0 * params.a * (t676 + t746 + t869 + t926 + t981 + t1048 + t1097 + t1163)

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = jnp.sqrt(jnp.pi)
  t2 = 0.1e1 / t1
  t3 = params.m1 ** 2
  t4 = params.omega ** 2
  t6 = r0 + r1
  t7 = t6 ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t9 = 0.1e1 / t8
  t11 = jnp.exp(-t3 * t4 * t9)
  t12 = t2 * t11
  t13 = t12 * params.m1
  t15 = 0.1e1 / t7 / t6
  t16 = params.omega * t15
  t17 = r0 - r1
  t18 = t17 ** 2
  t19 = t6 ** 2
  t20 = 0.1e1 / t19
  t22 = -t18 * t20 + 0.1e1
  t23 = 0.1e1 / t7
  t25 = params.d * t23 + 0.1e1
  t26 = 0.1e1 / t25
  t27 = t22 * t26
  t30 = 0.2e1 / 0.3e1 * t13 * t16 * t27
  t31 = params.m1 * params.omega
  t33 = jax.lax.erfc(t31 * t23)
  t34 = t17 * t20
  t35 = t19 * t6
  t36 = 0.1e1 / t35
  t37 = t18 * t36
  t39 = -0.2e1 * t34 + 0.2e1 * t37
  t40 = t33 * t39
  t42 = t33 * t22
  t43 = t25 ** 2
  t44 = 0.1e1 / t43
  t45 = t44 * params.d
  t46 = t45 * t15
  t48 = t42 * t46 / 0.3e1
  t49 = params.m2 ** 2
  t52 = jnp.exp(-t49 * t4 * t9)
  t53 = t2 * t52
  t54 = params.m2 * params.omega
  t55 = t53 * t54
  t56 = t15 * params.b
  t58 = jnp.exp(-params.c * t23)
  t59 = t58 * t26
  t61 = s0 + 0.2e1 * s1 + s2
  t63 = 0.1e1 / t8 / t19
  t64 = t61 * t63
  t66 = params.d * t26 + params.c
  t67 = t66 * t23
  t69 = 0.47e2 - 0.7e1 * t67
  t72 = t22 * t69 / 0.72e2 - 0.2e1 / 0.3e1
  t74 = 3 ** (0.1e1 / 0.3e1)
  t75 = t74 ** 2
  t76 = jnp.pi ** 2
  t77 = t76 ** (0.1e1 / 0.3e1)
  t78 = t77 ** 2
  t79 = t75 * t78
  t80 = 0.1e1 / t6
  t81 = t17 * t80
  t82 = 0.1e1 + t81
  t83 = t82 <= f.p.zeta_threshold
  t84 = f.p.zeta_threshold ** 2
  t85 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t86 = t85 ** 2
  t87 = t86 * t84
  t88 = t82 ** 2
  t89 = t82 ** (0.1e1 / 0.3e1)
  t90 = t89 ** 2
  t91 = t90 * t88
  t92 = f.my_piecewise3(t83, t87, t91)
  t93 = 0.1e1 - t81
  t94 = t93 <= f.p.zeta_threshold
  t95 = t93 ** 2
  t96 = t93 ** (0.1e1 / 0.3e1)
  t97 = t96 ** 2
  t98 = t97 * t95
  t99 = f.my_piecewise3(t94, t87, t98)
  t100 = t92 + t99
  t104 = 2 ** (0.1e1 / 0.3e1)
  t105 = t104 * t22
  t107 = 0.5e1 / 0.2e1 - t67 / 0.18e2
  t108 = r0 ** 2
  t109 = r0 ** (0.1e1 / 0.3e1)
  t110 = t109 ** 2
  t112 = 0.1e1 / t110 / t108
  t113 = s0 * t112
  t114 = t113 * t92
  t115 = r1 ** 2
  t116 = r1 ** (0.1e1 / 0.3e1)
  t117 = t116 ** 2
  t119 = 0.1e1 / t117 / t115
  t120 = s2 * t119
  t121 = t120 * t99
  t122 = t114 + t121
  t123 = t107 * t122
  t126 = t67 - 0.11e2
  t128 = t86 * t84 * f.p.zeta_threshold
  t131 = f.my_piecewise3(t83, t128, t90 * t88 * t82)
  t135 = f.my_piecewise3(t94, t128, t97 * t95 * t93)
  t137 = t113 * t131 + t120 * t135
  t138 = t126 * t137
  t143 = f.my_piecewise3(t83, t84, t88)
  t144 = t143 * s2
  t145 = t119 * t99
  t148 = f.my_piecewise3(t94, t84, t95)
  t149 = t148 * s0
  t150 = t112 * t92
  t156 = -t64 * t72 - 0.3e1 / 0.20e2 * t79 * t22 * t100 + t105 * t123 / 0.32e2 + t105 * t138 / 0.576e3 - t104 * (0.2e1 / 0.3e1 * t114 + 0.2e1 / 0.3e1 * t121 - t144 * t145 / 0.4e1 - t149 * t150 / 0.4e1) / 0.8e1
  t157 = t59 * t156
  t160 = 0.2e1 / 0.3e1 * t55 * t56 * t157
  t162 = jax.lax.erfc(t54 * t23)
  t163 = t162 * params.b
  t164 = t163 * params.c
  t165 = t15 * t58
  t166 = t26 * t156
  t169 = t164 * t165 * t166 / 0.3e1
  t170 = t163 * t58
  t171 = t44 * t156
  t172 = params.d * t15
  t175 = t170 * t171 * t172 / 0.3e1
  t177 = 0.1e1 / t8 / t35
  t178 = t61 * t177
  t180 = 0.8e1 / 0.3e1 * t178 * t72
  t182 = params.d ** 2
  t183 = t182 * t44
  t185 = 0.1e1 / t8 / t6
  t188 = t66 * t15 - t183 * t185
  t189 = 0.7e1 / 0.3e1 * t188
  t190 = t22 * t189
  t192 = t39 * t69 / 0.72e2 + t190 / 0.72e2
  t197 = t90 * t82
  t198 = t80 - t34
  t201 = f.my_piecewise3(t83, 0, 0.8e1 / 0.3e1 * t197 * t198)
  t202 = t97 * t93
  t203 = -t198
  t206 = f.my_piecewise3(t94, 0, 0.8e1 / 0.3e1 * t202 * t203)
  t207 = t201 + t206
  t211 = t104 * t39
  t214 = t188 / 0.54e2
  t215 = t214 * t122
  t217 = t105 * t215 / 0.32e2
  t220 = 0.1e1 / t110 / t108 / r0
  t221 = s0 * t220
  t222 = t221 * t92
  t224 = t113 * t201
  t225 = t120 * t206
  t226 = -0.8e1 / 0.3e1 * t222 + t224 + t225
  t227 = t107 * t226
  t233 = -t188 / 0.3e1
  t234 = t233 * t137
  t236 = t105 * t234 / 0.576e3
  t241 = f.my_piecewise3(t83, 0, 0.11e2 / 0.3e1 * t91 * t198)
  t245 = f.my_piecewise3(t94, 0, 0.11e2 / 0.3e1 * t98 * t203)
  t247 = -0.8e1 / 0.3e1 * t221 * t131 + t113 * t241 + t120 * t245
  t248 = t126 * t247
  t256 = f.my_piecewise3(t83, 0, 0.2e1 * t82 * t198)
  t257 = t256 * s2
  t260 = t119 * t206
  t265 = f.my_piecewise3(t94, 0, 0.2e1 * t93 * t203)
  t266 = t265 * s0
  t269 = t220 * t92
  t272 = t112 * t201
  t278 = t180 - t64 * t192 - 0.3e1 / 0.20e2 * t79 * t39 * t100 - 0.3e1 / 0.20e2 * t79 * t22 * t207 + t211 * t123 / 0.32e2 + t217 + t105 * t227 / 0.32e2 + t211 * t138 / 0.576e3 + t236 + t105 * t248 / 0.576e3 - t104 * (-0.16e2 / 0.9e1 * t222 + 0.2e1 / 0.3e1 * t224 + 0.2e1 / 0.3e1 * t225 - t257 * t145 / 0.4e1 - t144 * t260 / 0.4e1 - t266 * t150 / 0.4e1 + 0.2e1 / 0.3e1 * t149 * t269 - t149 * t272 / 0.4e1) / 0.8e1
  t279 = t59 * t278
  t281 = params.b * params.c
  t284 = t281 * t185 * t58 * t26
  t286 = t2 * params.m2 * params.omega
  t287 = t52 * t22
  t291 = t81 / 0.6e1
  t293 = (0.7e1 / 0.6e1 + t291) * s0
  t294 = t112 * t104
  t295 = t294 * t92
  t299 = (0.7e1 / 0.6e1 - t291) * s2
  t300 = t119 * t104
  t301 = t300 * t99
  t304 = 0.7e1 / 0.6e1 * t64 - 0.7e1 / 0.48e2 * t104 * t122 + t293 * t295 / 0.8e1 + t299 * t301 / 0.8e1
  t305 = t287 * t304
  t306 = t286 * t305
  t308 = t284 * t306 / 0.18e2
  t309 = params.b * t58
  t310 = t44 * t2
  t312 = t309 * t310 * params.m2
  t313 = params.omega * t52
  t314 = t313 * t185
  t315 = t22 * t304
  t316 = t315 * params.d
  t319 = t312 * t314 * t316 / 0.18e2
  t320 = t26 * t2
  t321 = t49 * params.m2
  t323 = t309 * t320 * t321
  t324 = t4 * params.omega
  t325 = t324 * t20
  t328 = t323 * t325 * t305 / 0.9e1
  t330 = t309 * t320 * params.m2
  t331 = t15 * t22
  t335 = t330 * t313 * t331 * t304 / 0.18e2
  t336 = t23 * t39
  t341 = t23 * t22
  t342 = 0.28e2 / 0.9e1 * t178
  t345 = t198 / 0.6e1
  t346 = t345 * s0
  t349 = t220 * t104
  t350 = t349 * t92
  t353 = t294 * t201
  t357 = -t345 * s2
  t360 = t300 * t206
  t363 = -t342 - 0.7e1 / 0.48e2 * t104 * t226 + t346 * t295 / 0.8e1 - t293 * t350 / 0.3e1 + t293 * t353 / 0.8e1 + t357 * t301 / 0.8e1 + t299 * t360 / 0.8e1
  t368 = -t30 - t40 * t26 - t48 + t160 + t169 + t175 + t163 * t279 + t308 + t319 + t328 - t335 + t330 * t313 * t336 * t304 / 0.6e1 + t330 * t313 * t341 * t363 / 0.6e1
  t369 = params.a * t368
  t371 = t6 * params.a
  t373 = 0.1e1 / t7 / t19
  t377 = 0.8e1 / 0.9e1 * t55 * t373 * params.b * t157
  t379 = t55 * t56 * t279
  t381 = t2 * t321
  t382 = t324 * t36
  t387 = 0.4e1 / 0.9e1 * t381 * t382 * t52 * params.b * t157
  t389 = t58 * t44
  t395 = t281 * t36 * t389 * t2 * t54 * t52 * t316 / 0.27e2
  t398 = t164 * t165 * t26 * t278
  t400 = params.c ** 2
  t402 = t63 * t58
  t405 = t163 * t400 * t402 * t166 / 0.9e1
  t408 = t170 * t44 * t278 * t172
  t411 = 0.1e1 / t43 / t25
  t416 = 0.2e1 / 0.9e1 * t170 * t411 * t156 * t182 * t63
  t420 = 0.8e1 / 0.9e1 * t13 * params.omega * t373 * t27
  t424 = 0.4e1 / 0.9e1 * t164 * t373 * t58 * t166
  t429 = 0.4e1 / 0.9e1 * t170 * t171 * params.d * t373
  t432 = t13 * t16 * t39 * t26
  t440 = 0.4e1 / 0.9e1 * t2 * t3 * params.m1 * t324 * t36 * t11 * t27
  t442 = 0.1e1 / t7 / t35
  t449 = 0.2e1 / 0.27e2 * t281 * t442 * t58 * t26 * t381 * t324 * t305
  t453 = t312 * t313 * t63 * t316 / 0.9e1
  t457 = t281 * t402 * t26 * t306 / 0.9e1
  t461 = t312 * t314 * t39 * t304 * params.d
  t466 = t312 * t314 * t22 * t363 * params.d
  t475 = t309 * t411 * t2 * params.m2 * t313 * t36 * t315 * t182 / 0.27e2
  t482 = 0.2e1 / 0.27e2 * t309 * t310 * t321 * t324 * t442 * t52 * t316
  t484 = t52 * t39 * t304
  t486 = t284 * t286 * t484
  t488 = -t429 - 0.4e1 / 0.3e1 * t432 - t440 + t449 - t453 - t457 + t461 / 0.9e1 + t466 / 0.9e1 + t475 + t482 + t486 / 0.9e1
  t490 = t287 * t363
  t492 = t284 * t286 * t490
  t499 = params.b * t400 * t36 * t58 * t26 * t306 / 0.54e2
  t502 = 0.7e1 / 0.27e2 * t323 * t382 * t305
  t507 = 0.2e1 / 0.27e2 * t330 * t313 * t373 * t22 * t304
  t508 = t19 ** 2
  t511 = t61 / t8 / t508
  t512 = 0.308e3 / 0.27e2 * t511
  t513 = t108 ** 2
  t515 = 0.1e1 / t110 / t513
  t516 = s0 * t515
  t517 = t516 * t92
  t519 = t221 * t201
  t521 = t198 ** 2
  t524 = t17 * t36
  t525 = -t20 + t524
  t526 = 0.2e1 * t525
  t530 = f.my_piecewise3(t83, 0, 0.40e2 / 0.9e1 * t90 * t521 + 0.8e1 / 0.3e1 * t197 * t526)
  t531 = t113 * t530
  t532 = t203 ** 2
  t535 = -t526
  t539 = f.my_piecewise3(t94, 0, 0.40e2 / 0.9e1 * t97 * t532 + 0.8e1 / 0.3e1 * t202 * t535)
  t540 = t120 * t539
  t541 = 0.88e2 / 0.9e1 * t517 - 0.16e2 / 0.3e1 * t519 + t531 + t540
  t544 = t525 / 0.3e1
  t571 = t512 - 0.7e1 / 0.48e2 * t104 * t541 + t544 * s0 * t295 / 0.8e1 - 0.2e1 / 0.3e1 * t346 * t350 + t346 * t353 / 0.4e1 + 0.11e2 / 0.9e1 * t293 * t515 * t104 * t92 - 0.2e1 / 0.3e1 * t293 * t349 * t201 + t293 * t294 * t530 / 0.8e1 - t544 * s2 * t301 / 0.8e1 + t357 * t360 / 0.4e1 + t299 * t300 * t539 / 0.8e1
  t577 = t323 * t325 * t484
  t580 = t323 * t325 * t490
  t582 = t49 ** 2
  t586 = t4 ** 2
  t591 = 0.2e1 / 0.27e2 * t309 * t320 * t582 * params.m2 * t586 * params.omega * t177 * t305
  t595 = t330 * t313 * t15 * t39 * t304
  t599 = t330 * t313 * t331 * t363
  t602 = 0.2e1 * t20
  t603 = 0.8e1 * t524
  t606 = 0.6e1 * t18 / t508
  t607 = -t602 + t603 - t606
  t618 = t53 * t54 * t63
  t621 = 0.4e1 / 0.9e1 * t618 * t281 * t157
  t625 = 0.4e1 / 0.9e1 * t618 * t309 * t171 * params.d
  t626 = t40 * t46
  t631 = 0.2e1 / 0.9e1 * t42 * t411 * t182 * t63
  t639 = f.my_piecewise3(t83, 0, 0.2e1 * t82 * t526 + 0.2e1 * t521)
  t651 = f.my_piecewise3(t94, 0, 0.2e1 * t93 * t535 + 0.2e1 * t532)
  t668 = 0.176e3 / 0.27e2 * t517 - 0.32e2 / 0.9e1 * t519 + 0.2e1 / 0.3e1 * t531 + 0.2e1 / 0.3e1 * t540 - t639 * s2 * t145 / 0.4e1 - t257 * t260 / 0.2e1 - t144 * t119 * t539 / 0.4e1 - t651 * s0 * t150 / 0.4e1 + 0.4e1 / 0.3e1 * t266 * t269 - t266 * t272 / 0.2e1 - 0.22e2 / 0.9e1 * t149 * t515 * t92 + 0.4e1 / 0.3e1 * t149 * t220 * t201 - t149 * t112 * t530 / 0.4e1
  t672 = 0.88e2 / 0.9e1 * t511 * t72
  t683 = t104 * t607
  t686 = t211 * t215
  t692 = t182 * params.d * t411 * t36
  t694 = t183 * t63
  t696 = t66 * t373
  t701 = t105 * (-t692 / 0.81e2 + t694 / 0.27e2 - 0.2e1 / 0.81e2 * t696) * t122 / 0.32e2
  t703 = t105 * t214 * t226
  t710 = t211 * t234
  t720 = t105 * (0.2e1 / 0.9e1 * t692 - 0.2e1 / 0.3e1 * t694 + 0.4e1 / 0.9e1 * t696) * t137 / 0.576e3
  t722 = t105 * t233 * t247
  t733 = f.my_piecewise3(t83, 0, 0.88e2 / 0.9e1 * t197 * t521 + 0.11e2 / 0.3e1 * t91 * t526)
  t740 = f.my_piecewise3(t94, 0, 0.88e2 / 0.9e1 * t202 * t532 + 0.11e2 / 0.3e1 * t98 * t535)
  t746 = t178 * t192
  t750 = t39 * t189
  t756 = t22 * (-0.14e2 / 0.9e1 * t692 + 0.14e2 / 0.3e1 * t694 - 0.28e2 / 0.9e1 * t696)
  t757 = t756 / 0.72e2
  t760 = -t104 * t668 / 0.8e1 - t672 - 0.3e1 / 0.20e2 * t79 * t607 * t100 - 0.3e1 / 0.10e2 * t79 * t39 * t207 - 0.3e1 / 0.20e2 * t79 * t22 * (t530 + t539) + t683 * t123 / 0.32e2 + t686 / 0.16e2 + t211 * t227 / 0.16e2 + t701 + t703 / 0.16e2 + t105 * t107 * t541 / 0.32e2 + t683 * t138 / 0.576e3 + t710 / 0.288e3 + t211 * t248 / 0.288e3 + t720 + t722 / 0.288e3 + t105 * t126 * (0.88e2 / 0.9e1 * t516 * t131 - 0.16e2 / 0.3e1 * t221 * t241 + t113 * t733 + t120 * t740) / 0.576e3 + 0.16e2 / 0.3e1 * t746 - t64 * (t607 * t69 / 0.72e2 + t750 / 0.36e2 + t757)
  t765 = 0.4e1 / 0.9e1 * t42 * t45 * t373
  t770 = 0.4e1 / 0.9e1 * t12 * t31 * t63 * t22 * t45
  t776 = 0.2e1 / 0.9e1 * t163 * params.c * t63 * t389 * t156 * params.d
  t779 = t330 * t313 * t23 * t607 * t304 / 0.6e1 + t330 * t313 * t336 * t363 / 0.3e1 + t621 + t625 - 0.2e1 / 0.3e1 * t626 - t631 + t163 * t59 * t760 + t765 - t770 + t776 - t33 * t607 * t26
  d11 = 0.2e1 * t369 + t371 * (-t377 + 0.4e1 / 0.3e1 * t379 + t387 + t395 + 0.2e1 / 0.3e1 * t398 + t405 + 0.2e1 / 0.3e1 * t408 + t416 + t420 - t424 + t488 + t492 / 0.9e1 + t499 - t502 + t507 + t330 * t313 * t341 * t571 / 0.6e1 + 0.2e1 / 0.9e1 * t577 + 0.2e1 / 0.9e1 * t580 + t591 - t595 / 0.9e1 - t599 / 0.9e1 + t779)
  t784 = 0.2e1 * t34 + 0.2e1 * t37
  t785 = t33 * t784
  t789 = t784 * t69 / 0.72e2 + t190 / 0.72e2
  t794 = -t80 - t34
  t795 = t197 * t794
  t797 = f.my_piecewise3(t83, 0, 0.8e1 / 0.3e1 * t795)
  t798 = -t794
  t799 = t202 * t798
  t801 = f.my_piecewise3(t94, 0, 0.8e1 / 0.3e1 * t799)
  t802 = t797 + t801
  t806 = t104 * t784
  t809 = t113 * t797
  t812 = 0.1e1 / t117 / t115 / r1
  t813 = s2 * t812
  t814 = t813 * t99
  t816 = t120 * t801
  t817 = t809 - 0.8e1 / 0.3e1 * t814 + t816
  t818 = t107 * t817
  t825 = f.my_piecewise3(t83, 0, 0.11e2 / 0.3e1 * t91 * t794)
  t831 = f.my_piecewise3(t94, 0, 0.11e2 / 0.3e1 * t98 * t798)
  t833 = t113 * t825 - 0.8e1 / 0.3e1 * t813 * t135 + t120 * t831
  t834 = t126 * t833
  t842 = f.my_piecewise3(t83, 0, 0.2e1 * t82 * t794)
  t843 = t842 * s2
  t846 = t812 * t99
  t849 = t119 * t801
  t854 = f.my_piecewise3(t94, 0, 0.2e1 * t93 * t798)
  t855 = t854 * s0
  t858 = t112 * t797
  t864 = t180 - t64 * t789 - 0.3e1 / 0.20e2 * t79 * t784 * t100 - 0.3e1 / 0.20e2 * t79 * t22 * t802 + t806 * t123 / 0.32e2 + t217 + t105 * t818 / 0.32e2 + t806 * t138 / 0.576e3 + t236 + t105 * t834 / 0.576e3 - t104 * (0.2e1 / 0.3e1 * t809 - 0.16e2 / 0.9e1 * t814 + 0.2e1 / 0.3e1 * t816 - t843 * t145 / 0.4e1 + 0.2e1 / 0.3e1 * t144 * t846 - t144 * t849 / 0.4e1 - t855 * t150 / 0.4e1 - t149 * t858 / 0.4e1) / 0.8e1
  t865 = t59 * t864
  t867 = t23 * t784
  t874 = t794 / 0.6e1
  t875 = t874 * s0
  t878 = t294 * t797
  t882 = -t874 * s2
  t885 = t812 * t104
  t886 = t885 * t99
  t889 = t300 * t801
  t892 = -t342 - 0.7e1 / 0.48e2 * t104 * t817 + t875 * t295 / 0.8e1 + t293 * t878 / 0.8e1 + t882 * t301 / 0.8e1 - t299 * t886 / 0.3e1 + t299 * t889 / 0.8e1
  t897 = -t30 - t785 * t26 - t48 + t160 + t169 + t175 + t163 * t865 + t308 + t319 + t328 - t335 + t330 * t313 * t867 * t304 / 0.6e1 + t330 * t313 * t341 * t892 / 0.6e1
  t898 = params.a * t897
  t899 = t602 - t606
  t904 = t55 * t56 * t865
  t909 = -t33 * t899 * t26 - t377 + 0.2e1 / 0.3e1 * t379 + t387 + 0.2e1 / 0.3e1 * t904 + t395 + t398 / 0.3e1 + t405 + t408 / 0.3e1 + t416 + t420 - t424 - t429 - 0.2e1 / 0.3e1 * t432
  t912 = t170 * t44 * t864 * t172
  t916 = t13 * t16 * t784 * t26
  t920 = t164 * t165 * t26 * t864
  t923 = t52 * t784 * t304
  t925 = t284 * t286 * t923
  t930 = t312 * t314 * t784 * t304 * params.d
  t932 = t287 * t892
  t934 = t284 * t286 * t932
  t939 = t312 * t314 * t22 * t892 * params.d
  t943 = -t440 + t912 / 0.3e1 - 0.2e1 / 0.3e1 * t916 + t920 / 0.3e1 + t925 / 0.18e2 + t930 / 0.18e2 + t934 / 0.18e2 + t939 / 0.18e2 + t449 - t453 - t457 + t461 / 0.18e2 + t466 / 0.18e2 + t475
  t950 = t330 * t313 * t15 * t784 * t304
  t954 = t330 * t313 * t331 * t892
  t956 = t221 * t797
  t965 = f.my_piecewise3(t83, 0, 0.40e2 / 0.9e1 * t90 * t794 * t198 + 0.16e2 / 0.3e1 * t197 * t17 * t36)
  t966 = t113 * t965
  t967 = t813 * t206
  t976 = f.my_piecewise3(t94, 0, 0.40e2 / 0.9e1 * t97 * t798 * t203 - 0.16e2 / 0.3e1 * t202 * t17 * t36)
  t977 = t120 * t976
  t978 = -0.8e1 / 0.3e1 * t956 + t966 - 0.8e1 / 0.3e1 * t967 + t977
  t1011 = t512 - 0.7e1 / 0.48e2 * t104 * t978 + t524 * s0 * t295 / 0.24e2 - t875 * t350 / 0.3e1 + t875 * t353 / 0.8e1 + t346 * t878 / 0.8e1 - t293 * t349 * t797 / 0.3e1 + t293 * t294 * t965 / 0.8e1 - t524 * s2 * t301 / 0.24e2 + t882 * t360 / 0.8e1 - t357 * t886 / 0.3e1 - t299 * t885 * t206 / 0.3e1 + t357 * t889 / 0.8e1 + t299 * t300 * t976 / 0.8e1
  t1017 = t323 * t325 * t932
  t1029 = t323 * t325 * t923
  t1035 = t482 + t486 / 0.18e2 + t492 / 0.18e2 + t499 - t950 / 0.18e2 - t954 / 0.18e2 + t330 * t313 * t341 * t1011 / 0.6e1 + t1017 / 0.9e1 + t330 * t313 * t23 * t899 * t304 / 0.6e1 + t330 * t313 * t867 * t363 / 0.6e1 + t1029 / 0.9e1 + t330 * t313 * t336 * t892 / 0.6e1 - t502 + t507
  t1040 = t785 * t46
  t1047 = t784 * t189
  t1051 = t178 * t789
  t1063 = f.my_piecewise3(t83, 0, 0.4e1 * t82 * t17 * t36 + 0.2e1 * t198 * t794)
  t1085 = f.my_piecewise3(t94, 0, -0.4e1 * t93 * t17 * t36 + 0.2e1 * t203 * t798)
  t1101 = -0.16e2 / 0.9e1 * t956 + 0.2e1 / 0.3e1 * t966 - 0.16e2 / 0.9e1 * t967 + 0.2e1 / 0.3e1 * t977 - t1063 * s2 * t145 / 0.4e1 - t843 * t260 / 0.4e1 + 0.2e1 / 0.3e1 * t257 * t846 + 0.2e1 / 0.3e1 * t144 * t812 * t206 - t257 * t849 / 0.4e1 - t144 * t119 * t976 / 0.4e1 - t1085 * s0 * t150 / 0.4e1 + 0.2e1 / 0.3e1 * t855 * t269 - t855 * t272 / 0.4e1 - t266 * t858 / 0.4e1 + 0.2e1 / 0.3e1 * t149 * t220 * t797 - t149 * t112 * t965 / 0.4e1
  t1107 = t105 * t214 * t817
  t1112 = t104 * t899
  t1115 = t686 / 0.32e2 + t701 + t703 / 0.32e2 + t710 / 0.576e3 + t720 + t722 / 0.576e3 - t64 * (t899 * t69 / 0.72e2 + t1047 / 0.72e2 + t750 / 0.72e2 + t756 / 0.72e2) + 0.8e1 / 0.3e1 * t1051 - t104 * t1101 / 0.8e1 + t211 * t818 / 0.32e2 + t1107 / 0.32e2 + t105 * t107 * t978 / 0.32e2 + t1112 * t138 / 0.576e3
  t1116 = t806 * t234
  t1123 = t105 * t233 * t833
  t1133 = f.my_piecewise3(t83, 0, 0.88e2 / 0.9e1 * t795 * t198 + 0.22e2 / 0.3e1 * t91 * t17 * t36)
  t1143 = f.my_piecewise3(t94, 0, 0.88e2 / 0.9e1 * t799 * t203 - 0.22e2 / 0.3e1 * t98 * t17 * t36)
  t1164 = t806 * t215
  t1169 = t1116 / 0.576e3 + t806 * t248 / 0.576e3 + t211 * t834 / 0.576e3 + t1123 / 0.576e3 + t105 * t126 * (-0.8e1 / 0.3e1 * t221 * t825 + t113 * t1133 - 0.8e1 / 0.3e1 * t813 * t245 + t120 * t1143) / 0.576e3 - 0.3e1 / 0.20e2 * t79 * t899 * t100 - 0.3e1 / 0.20e2 * t79 * t784 * t207 - 0.3e1 / 0.20e2 * t79 * t39 * t802 - 0.3e1 / 0.20e2 * t79 * t22 * (t965 + t976) + t1112 * t123 / 0.32e2 + t1164 / 0.32e2 + t806 * t227 / 0.32e2 - t672 + 0.8e1 / 0.3e1 * t746
  t1174 = t577 / 0.9e1 + t580 / 0.9e1 + t591 - t595 / 0.18e2 - t599 / 0.18e2 + t621 + t625 - t1040 / 0.3e1 + t163 * t59 * (t1115 + t1169) - t626 / 0.3e1 - t631 + t765 - t770 + t776
  d12 = t369 + t898 + t371 * (t909 + t943 + t1035 + t1174)
  t1179 = -t602 - t603 - t606
  t1188 = t794 ** 2
  t1191 = t20 + t524
  t1192 = 0.2e1 * t1191
  t1196 = f.my_piecewise3(t83, 0, 0.88e2 / 0.9e1 * t197 * t1188 + 0.11e2 / 0.3e1 * t91 * t1192)
  t1198 = t115 ** 2
  t1200 = 0.1e1 / t117 / t1198
  t1201 = s2 * t1200
  t1206 = t798 ** 2
  t1209 = -t1192
  t1213 = f.my_piecewise3(t94, 0, 0.88e2 / 0.9e1 * t202 * t1206 + 0.11e2 / 0.3e1 * t98 * t1209)
  t1230 = f.my_piecewise3(t83, 0, 0.40e2 / 0.9e1 * t90 * t1188 + 0.8e1 / 0.3e1 * t197 * t1192)
  t1236 = f.my_piecewise3(t94, 0, 0.40e2 / 0.9e1 * t97 * t1206 + 0.8e1 / 0.3e1 * t202 * t1209)
  t1241 = t104 * t1179
  t1248 = t113 * t1230
  t1249 = t1201 * t99
  t1251 = t813 * t801
  t1253 = t120 * t1236
  t1254 = t1248 + 0.88e2 / 0.9e1 * t1249 - 0.16e2 / 0.3e1 * t1251 + t1253
  t1271 = f.my_piecewise3(t83, 0, 0.2e1 * t82 * t1192 + 0.2e1 * t1188)
  t1291 = f.my_piecewise3(t94, 0, 0.2e1 * t93 * t1209 + 0.2e1 * t1206)
  t1300 = 0.2e1 / 0.3e1 * t1248 + 0.176e3 / 0.27e2 * t1249 - 0.32e2 / 0.9e1 * t1251 + 0.2e1 / 0.3e1 * t1253 - t1271 * s2 * t145 / 0.4e1 + 0.4e1 / 0.3e1 * t843 * t846 - t843 * t849 / 0.2e1 - 0.22e2 / 0.9e1 * t144 * t1200 * t99 + 0.4e1 / 0.3e1 * t144 * t812 * t801 - t144 * t119 * t1236 / 0.4e1 - t1291 * s0 * t150 / 0.4e1 - t855 * t858 / 0.2e1 - t149 * t112 * t1230 / 0.4e1
  t1303 = 0.16e2 / 0.3e1 * t1051 - t64 * (t1179 * t69 / 0.72e2 + t1047 / 0.36e2 + t757) + t105 * t126 * (t113 * t1196 + 0.88e2 / 0.9e1 * t1201 * t135 - 0.16e2 / 0.3e1 * t813 * t831 + t120 * t1213) / 0.576e3 - t672 - 0.3e1 / 0.20e2 * t79 * t1179 * t100 - 0.3e1 / 0.10e2 * t79 * t784 * t802 - 0.3e1 / 0.20e2 * t79 * t22 * (t1230 + t1236) + t1241 * t123 / 0.32e2 + t1164 / 0.16e2 + t806 * t818 / 0.16e2 + t701 + t1107 / 0.16e2 + t105 * t107 * t1254 / 0.32e2 + t1241 * t138 / 0.576e3 + t1116 / 0.288e3 + t806 * t834 / 0.288e3 + t720 + t1123 / 0.288e3 - t104 * t1300 / 0.8e1
  t1315 = -t429 - t440 + 0.2e1 / 0.3e1 * t912 - 0.4e1 / 0.3e1 * t916 + 0.2e1 / 0.3e1 * t920 + t925 / 0.9e1 + t930 / 0.9e1 + t934 / 0.9e1 + t939 / 0.9e1 + t449 - t453
  t1328 = t1191 / 0.3e1
  t1355 = t512 - 0.7e1 / 0.48e2 * t104 * t1254 + t1328 * s0 * t295 / 0.8e1 + t875 * t878 / 0.4e1 + t293 * t294 * t1230 / 0.8e1 - t1328 * s2 * t301 / 0.8e1 - 0.2e1 / 0.3e1 * t882 * t886 + t882 * t889 / 0.4e1 + 0.11e2 / 0.9e1 * t299 * t1200 * t104 * t99 - 0.2e1 / 0.3e1 * t299 * t885 * t801 + t299 * t300 * t1236 / 0.8e1
  t1366 = 0.2e1 / 0.9e1 * t1029 - t502 + t507 + t591 + t621 + t625 - 0.2e1 / 0.3e1 * t1040 - t631 + t765 - t770 + t776
  d22 = 0.2e1 * t898 + t371 * (-t33 * t1179 * t26 + t163 * t59 * t1303 - t377 + t387 + 0.4e1 / 0.3e1 * t904 + t395 + t405 + t416 + t420 - t424 + t1315 - t457 + t475 + t482 + t499 + t330 * t313 * t23 * t1179 * t304 / 0.6e1 + t330 * t313 * t867 * t892 / 0.3e1 + t330 * t313 * t341 * t1355 / 0.6e1 - t950 / 0.9e1 - t954 / 0.9e1 + 0.2e1 / 0.9e1 * t1017 + t1366)
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

  t1 = jnp.sqrt(jnp.pi)
  t2 = 0.1e1 / t1
  t3 = params.m1 ** 2
  t4 = params.omega ** 2
  t6 = r0 + r1
  t7 = t6 ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t9 = 0.1e1 / t8
  t11 = jnp.exp(-t3 * t4 * t9)
  t12 = t2 * t11
  t13 = params.m1 * params.omega
  t14 = t12 * t13
  t15 = t6 ** 2
  t17 = 0.1e1 / t8 / t15
  t18 = r0 - r1
  t19 = t18 ** 2
  t20 = 0.1e1 / t15
  t22 = -t19 * t20 + 0.1e1
  t24 = 0.1e1 / t7
  t26 = params.d * t24 + 0.1e1
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t28 * params.d
  t33 = params.m2 * params.omega
  t35 = jnp.erfc(t33 * t24)
  t36 = t35 * params.b
  t38 = t36 * params.c * t17
  t40 = jnp.exp(-params.c * t24)
  t41 = t40 * t28
  t43 = s0 + 0.2e1 * s1 + s2
  t44 = t43 * t17
  t45 = 0.1e1 / t26
  t47 = params.d * t45 + params.c
  t48 = t47 * t24
  t50 = 0.47e2 - 0.7e1 * t48
  t53 = t22 * t50 / 0.72e2 - 0.2e1 / 0.3e1
  t55 = 3 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = jnp.pi ** 2
  t58 = t57 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t60 = t56 * t59
  t61 = 0.1e1 / t6
  t62 = t18 * t61
  t63 = 0.1e1 + t62
  t64 = t63 <= f.p.zeta_threshold
  t65 = f.p.zeta_threshold ** 2
  t66 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t68 = t67 * t65
  t69 = t63 ** 2
  t70 = t63 ** (0.1e1 / 0.3e1)
  t71 = t70 ** 2
  t72 = t71 * t69
  t73 = f.my_piecewise3(t64, t68, t72)
  t74 = 0.1e1 - t62
  t75 = t74 <= f.p.zeta_threshold
  t76 = t74 ** 2
  t77 = t74 ** (0.1e1 / 0.3e1)
  t78 = t77 ** 2
  t79 = t78 * t76
  t80 = f.my_piecewise3(t75, t68, t79)
  t81 = t73 + t80
  t85 = 2 ** (0.1e1 / 0.3e1)
  t86 = t85 * t22
  t88 = 0.5e1 / 0.2e1 - t48 / 0.18e2
  t89 = r0 ** 2
  t90 = r0 ** (0.1e1 / 0.3e1)
  t91 = t90 ** 2
  t93 = 0.1e1 / t91 / t89
  t94 = s0 * t93
  t95 = t94 * t73
  t96 = r1 ** 2
  t97 = r1 ** (0.1e1 / 0.3e1)
  t98 = t97 ** 2
  t100 = 0.1e1 / t98 / t96
  t101 = s2 * t100
  t102 = t101 * t80
  t103 = t95 + t102
  t104 = t88 * t103
  t107 = t48 - 0.11e2
  t109 = t67 * t65 * f.p.zeta_threshold
  t112 = f.my_piecewise3(t64, t109, t71 * t69 * t63)
  t116 = f.my_piecewise3(t75, t109, t78 * t76 * t74)
  t118 = t101 * t116 + t94 * t112
  t119 = t107 * t118
  t124 = f.my_piecewise3(t64, t65, t69)
  t125 = t124 * s2
  t126 = t100 * t80
  t129 = f.my_piecewise3(t75, t65, t76)
  t130 = t129 * s0
  t131 = t93 * t73
  t137 = -t44 * t53 - 0.3e1 / 0.20e2 * t60 * t22 * t81 + t86 * t104 / 0.32e2 + t86 * t119 / 0.576e3 - t85 * (0.2e1 / 0.3e1 * t95 + 0.2e1 / 0.3e1 * t102 - t125 * t126 / 0.4e1 - t130 * t131 / 0.4e1) / 0.8e1
  t139 = t41 * t137 * params.d
  t142 = params.m2 ** 2
  t145 = jnp.exp(-t142 * t4 * t9)
  t146 = t2 * t145
  t147 = t146 * t33
  t149 = 0.1e1 / t7 / t15
  t150 = t149 * params.b
  t151 = t40 * t45
  t152 = t151 * t137
  t157 = 0.1e1 / t7 / t6
  t158 = t157 * params.b
  t159 = t15 * t6
  t161 = 0.1e1 / t8 / t159
  t162 = t43 * t161
  t165 = t18 * t20
  t166 = 0.1e1 / t159
  t169 = 0.2e1 * t19 * t166 - 0.2e1 * t165
  t171 = params.d ** 2
  t172 = t171 * t28
  t174 = 0.1e1 / t8 / t6
  t177 = t47 * t157 - t172 * t174
  t178 = 0.7e1 / 0.3e1 * t177
  t181 = t169 * t50 / 0.72e2 + t22 * t178 / 0.72e2
  t186 = t71 * t63
  t187 = t61 - t165
  t188 = t186 * t187
  t190 = f.my_piecewise3(t64, 0, 0.8e1 / 0.3e1 * t188)
  t191 = t78 * t74
  t192 = -t187
  t193 = t191 * t192
  t195 = f.my_piecewise3(t75, 0, 0.8e1 / 0.3e1 * t193)
  t196 = t190 + t195
  t200 = t85 * t169
  t203 = t177 / 0.54e2
  t204 = t203 * t103
  t209 = 0.1e1 / t91 / t89 / r0
  t210 = s0 * t209
  t211 = t210 * t73
  t213 = t94 * t190
  t214 = t101 * t195
  t215 = -0.8e1 / 0.3e1 * t211 + t213 + t214
  t216 = t88 * t215
  t222 = -t177 / 0.3e1
  t223 = t222 * t118
  t230 = f.my_piecewise3(t64, 0, 0.11e2 / 0.3e1 * t72 * t187)
  t234 = f.my_piecewise3(t75, 0, 0.11e2 / 0.3e1 * t79 * t192)
  t236 = -0.8e1 / 0.3e1 * t210 * t112 + t94 * t230 + t101 * t234
  t237 = t107 * t236
  t245 = f.my_piecewise3(t64, 0, 0.2e1 * t63 * t187)
  t246 = t245 * s2
  t249 = t100 * t195
  t254 = f.my_piecewise3(t75, 0, 0.2e1 * t74 * t192)
  t255 = t254 * s0
  t258 = t209 * t73
  t261 = t93 * t190
  t267 = 0.8e1 / 0.3e1 * t162 * t53 - t44 * t181 - 0.3e1 / 0.20e2 * t60 * t169 * t81 - 0.3e1 / 0.20e2 * t60 * t22 * t196 + t200 * t104 / 0.32e2 + t86 * t204 / 0.32e2 + t86 * t216 / 0.32e2 + t200 * t119 / 0.576e3 + t86 * t223 / 0.576e3 + t86 * t237 / 0.576e3 - t85 * (-0.16e2 / 0.9e1 * t211 + 0.2e1 / 0.3e1 * t213 + 0.2e1 / 0.3e1 * t214 - t246 * t126 / 0.4e1 - t125 * t249 / 0.4e1 - t255 * t131 / 0.4e1 + 0.2e1 / 0.3e1 * t130 * t258 - t130 * t261 / 0.4e1) / 0.8e1
  t268 = t151 * t267
  t272 = t142 * params.m2
  t273 = t2 * t272
  t274 = t4 * params.omega
  t275 = t274 * t166
  t276 = t273 * t275
  t277 = t145 * params.b
  t278 = t277 * t152
  t281 = params.b * params.c
  t283 = t41 * t2
  t284 = t281 * t166 * t283
  t285 = t33 * t145
  t289 = t62 / 0.6e1
  t291 = (0.7e1 / 0.6e1 + t289) * s0
  t292 = t93 * t85
  t293 = t292 * t73
  t297 = (0.7e1 / 0.6e1 - t289) * s2
  t298 = t100 * t85
  t299 = t298 * t80
  t302 = 0.7e1 / 0.6e1 * t44 - 0.7e1 / 0.48e2 * t85 * t103 + t291 * t293 / 0.8e1 + t297 * t299 / 0.8e1
  t303 = t22 * t302
  t304 = t303 * params.d
  t305 = t285 * t304
  t308 = t36 * t40
  t309 = t28 * t137
  t310 = params.d * t149
  t314 = t12 * params.m1
  t315 = params.omega * t157
  t316 = t169 * t45
  t321 = t2 * t3 * params.m1
  t322 = t321 * t274
  t323 = t166 * t11
  t324 = t22 * t45
  t328 = t36 * params.c
  t329 = t157 * t40
  t330 = t45 * t267
  t335 = params.c ** 2
  t336 = t36 * t335
  t337 = t17 * t40
  t338 = t45 * t137
  t342 = t28 * t267
  t343 = params.d * t157
  t348 = 0.1e1 / t27 / t26
  t349 = t348 * t137
  t350 = t171 * t17
  t354 = params.omega * t149
  t358 = t149 * t40
  t362 = params.b * t40
  t363 = t28 * t2
  t365 = t362 * t363 * params.m2
  t366 = params.omega * t145
  t367 = t366 * t174
  t371 = t187 / 0.6e1
  t372 = t371 * s0
  t375 = t209 * t85
  t376 = t375 * t73
  t379 = t292 * t190
  t383 = -t371 * s2
  t386 = t298 * t195
  t389 = -0.28e2 / 0.9e1 * t162 - 0.7e1 / 0.48e2 * t85 * t215 + t372 * t293 / 0.8e1 - t291 * t376 / 0.3e1 + t291 * t379 / 0.8e1 + t383 * t299 / 0.8e1 + t297 * t386 / 0.8e1
  t390 = t22 * t389
  t391 = t390 * params.d
  t395 = t348 * t2
  t397 = t362 * t395 * params.m2
  t398 = t366 * t166
  t399 = t303 * t171
  t404 = t362 * t363 * t272
  t406 = 0.1e1 / t7 / t159
  t408 = t274 * t406 * t145
  t414 = t281 * t174 * t40 * t45
  t416 = t2 * params.m2 * params.omega
  t417 = t145 * t169
  t418 = t417 * t302
  t419 = t416 * t418
  t422 = t145 * t22
  t423 = t422 * t389
  t424 = t416 * t423
  t427 = params.b * t335
  t430 = t427 * t166 * t40 * t45
  t431 = t422 * t302
  t432 = t416 * t431
  t435 = t336 * t337 * t338 / 0.9e1 + 0.2e1 / 0.3e1 * t308 * t342 * t343 + 0.2e1 / 0.9e1 * t308 * t349 * t350 + 0.8e1 / 0.9e1 * t314 * t354 * t324 - 0.4e1 / 0.9e1 * t328 * t358 * t338 + t365 * t367 * t391 / 0.9e1 + t397 * t398 * t399 / 0.27e2 + 0.2e1 / 0.27e2 * t404 * t408 * t304 + t414 * t419 / 0.9e1 + t414 * t424 / 0.9e1 + t430 * t432 / 0.54e2
  t437 = t45 * t2
  t439 = t362 * t437 * params.m2
  t440 = t157 * t22
  t446 = t18 * t166
  t448 = t15 ** 2
  t449 = 0.1e1 / t448
  t452 = -0.6e1 * t19 * t449 - 0.2e1 * t20 + 0.8e1 * t446
  t453 = t24 * t452
  t458 = t24 * t169
  t464 = t146 * t33 * t17
  t465 = t281 * t152
  t468 = t309 * params.d
  t469 = t362 * t468
  t473 = t362 * t437 * t272
  t477 = t149 * t22
  t482 = t24 * t22
  t484 = 0.1e1 / t8 / t448
  t485 = t43 * t484
  t487 = t89 ** 2
  t489 = 0.1e1 / t91 / t487
  t490 = s0 * t489
  t491 = t490 * t73
  t493 = t210 * t190
  t495 = t187 ** 2
  t498 = -t20 + t446
  t499 = 0.2e1 * t498
  t503 = f.my_piecewise3(t64, 0, 0.40e2 / 0.9e1 * t71 * t495 + 0.8e1 / 0.3e1 * t186 * t499)
  t504 = t94 * t503
  t505 = t192 ** 2
  t508 = -t499
  t512 = f.my_piecewise3(t75, 0, 0.40e2 / 0.9e1 * t78 * t505 + 0.8e1 / 0.3e1 * t191 * t508)
  t513 = t101 * t512
  t514 = 0.88e2 / 0.9e1 * t491 - 0.16e2 / 0.3e1 * t493 + t504 + t513
  t517 = t498 / 0.3e1
  t518 = t517 * s0
  t525 = t489 * t85
  t526 = t525 * t73
  t529 = t375 * t190
  t532 = t292 * t503
  t536 = -t517 * s2
  t541 = t298 * t512
  t544 = 0.308e3 / 0.27e2 * t485 - 0.7e1 / 0.48e2 * t85 * t514 + t518 * t293 / 0.8e1 - 0.2e1 / 0.3e1 * t372 * t376 + t372 * t379 / 0.4e1 + 0.11e2 / 0.9e1 * t291 * t526 - 0.2e1 / 0.3e1 * t291 * t529 + t291 * t532 / 0.8e1 + t536 * t299 / 0.8e1 + t383 * t386 / 0.4e1 + t297 * t541 / 0.8e1
  t549 = t274 * t20
  t557 = t142 ** 2
  t558 = t557 * params.m2
  t560 = t362 * t437 * t558
  t561 = t4 ** 2
  t562 = t561 * params.omega
  t563 = t562 * t161
  t567 = t157 * t169
  t572 = t406 * t40
  t574 = t281 * t572 * t45
  t575 = t273 * t274
  t576 = t575 * t431
  t579 = t366 * t17
  t584 = t281 * t337 * t45
  t587 = t169 * t302
  t588 = t587 * params.d
  t593 = jnp.erfc(t13 * t24)
  t594 = t593 * t452
  t596 = t593 * t169
  t597 = t29 * t157
  t600 = t593 * t22
  t601 = t348 * t171
  t602 = t601 * t17
  t612 = f.my_piecewise3(t64, 0, 0.2e1 * t63 * t499 + 0.2e1 * t495)
  t613 = t612 * s2
  t618 = t100 * t512
  t624 = f.my_piecewise3(t75, 0, 0.2e1 * t74 * t508 + 0.2e1 * t505)
  t625 = t624 * s0
  t632 = t489 * t73
  t635 = t209 * t190
  t638 = t93 * t503
  t641 = 0.176e3 / 0.27e2 * t491 - 0.32e2 / 0.9e1 * t493 + 0.2e1 / 0.3e1 * t504 + 0.2e1 / 0.3e1 * t513 - t613 * t126 / 0.4e1 - t246 * t249 / 0.2e1 - t125 * t618 / 0.4e1 - t625 * t131 / 0.4e1 + 0.4e1 / 0.3e1 * t255 * t258 - t255 * t261 / 0.2e1 - 0.22e2 / 0.9e1 * t130 * t632 + 0.4e1 / 0.3e1 * t130 * t635 - t130 * t638 / 0.4e1
  t652 = t503 + t512
  t656 = t85 * t452
  t663 = t171 * params.d
  t664 = t663 * t348
  t665 = t664 * t166
  t667 = t172 * t17
  t669 = t47 * t149
  t671 = -t665 / 0.81e2 + t667 / 0.27e2 - 0.2e1 / 0.81e2 * t669
  t672 = t671 * t103
  t675 = t203 * t215
  t678 = t88 * t514
  t690 = 0.2e1 / 0.9e1 * t665 - 0.2e1 / 0.3e1 * t667 + 0.4e1 / 0.9e1 * t669
  t691 = t690 * t118
  t694 = t222 * t236
  t706 = f.my_piecewise3(t64, 0, 0.88e2 / 0.9e1 * t186 * t495 + 0.11e2 / 0.3e1 * t72 * t499)
  t713 = f.my_piecewise3(t75, 0, 0.88e2 / 0.9e1 * t191 * t505 + 0.11e2 / 0.3e1 * t79 * t508)
  t715 = 0.88e2 / 0.9e1 * t490 * t112 - 0.16e2 / 0.3e1 * t210 * t230 + t94 * t706 + t101 * t713
  t716 = t107 * t715
  t728 = -0.14e2 / 0.9e1 * t665 + 0.14e2 / 0.3e1 * t667 - 0.28e2 / 0.9e1 * t669
  t731 = t452 * t50 / 0.72e2 + t169 * t178 / 0.36e2 + t22 * t728 / 0.72e2
  t733 = -t85 * t641 / 0.8e1 - 0.88e2 / 0.9e1 * t485 * t53 - 0.3e1 / 0.20e2 * t60 * t452 * t81 - 0.3e1 / 0.10e2 * t60 * t169 * t196 - 0.3e1 / 0.20e2 * t60 * t22 * t652 + t656 * t104 / 0.32e2 + t200 * t204 / 0.16e2 + t200 * t216 / 0.16e2 + t86 * t672 / 0.32e2 + t86 * t675 / 0.16e2 + t86 * t678 / 0.32e2 + t656 * t119 / 0.576e3 + t200 * t223 / 0.288e3 + t200 * t237 / 0.288e3 + t86 * t691 / 0.576e3 + t86 * t694 / 0.288e3 + t86 * t716 / 0.576e3 + 0.16e2 / 0.3e1 * t162 * t181 - t44 * t731
  t734 = t151 * t733
  t736 = t29 * t149
  t739 = 0.2e1 / 0.27e2 * t560 * t563 * t431 - t439 * t366 * t567 * t302 / 0.9e1 + 0.2e1 / 0.27e2 * t574 * t576 - t365 * t579 * t304 / 0.9e1 - t584 * t432 / 0.9e1 + t365 * t367 * t588 / 0.9e1 - t594 * t45 - 0.2e1 / 0.3e1 * t596 * t597 - 0.2e1 / 0.9e1 * t600 * t602 + t36 * t734 + 0.4e1 / 0.9e1 * t600 * t736
  t751 = t27 ** 2
  t752 = 0.1e1 / t751
  t757 = 0.1e1 / t7 / t448
  t772 = t448 * t6
  t773 = 0.1e1 / t772
  t780 = t145 * t452 * t302
  t784 = t417 * t389
  t812 = -t365 * t579 * t588 / 0.3e1 - t365 * t579 * t391 / 0.3e1 + t362 * t752 * t2 * params.m2 * t366 * t757 * t303 * t663 / 0.27e2 + 0.2e1 / 0.27e2 * t362 * t395 * t272 * t274 * t484 * t145 * t399 + 0.2e1 / 0.27e2 * t362 * t363 * t558 * t562 * t773 * t145 * t304 + t414 * t416 * t780 / 0.6e1 + t414 * t416 * t784 / 0.3e1 + t397 * t398 * t587 * t171 / 0.9e1 + 0.2e1 / 0.9e1 * t404 * t408 * t588 + t365 * t367 * t22 * t544 * params.d / 0.6e1 - 0.4e1 / 0.3e1 * t14 * t17 * t169 * t29 - 0.4e1 / 0.9e1 * t14 * t449 * t22 * t601 + 0.16e2 / 0.9e1 * t14 * t161 * t22 * t29
  t823 = t40 * t348
  t832 = t274 * t757
  t848 = t274 * t449
  t855 = t2 * t558
  t856 = t562 * t484
  t867 = 0.2e1 / 0.3e1 * t38 * t41 * t267 * params.d + t36 * t335 * t449 * t139 / 0.9e1 + 0.2e1 / 0.9e1 * t36 * params.c * t449 * t823 * t137 * t171 - 0.8e1 / 0.9e1 * t36 * params.c * t161 * t139 - 0.4e1 / 0.9e1 * t321 * t832 * t11 * t22 * t29 + 0.56e2 / 0.27e2 * t147 * t406 * params.b * t152 + 0.2e1 * t147 * t158 * t734 - 0.8e1 / 0.3e1 * t147 * t150 * t268 - 0.52e2 / 0.27e2 * t273 * t848 * t278 + 0.4e1 / 0.3e1 * t276 * t277 * t268 + 0.8e1 / 0.27e2 * t855 * t856 * t278 - 0.5e1 / 0.27e2 * t281 * t449 * t283 * t305 + t284 * t285 * t588 / 0.9e1
  t921 = t284 * t285 * t391 / 0.9e1 + t427 * t757 * t283 * t305 / 0.54e2 + t281 * t757 * t823 * t2 * t285 * t399 / 0.27e2 + 0.2e1 / 0.27e2 * t281 * t484 * t283 * t272 * t274 * t145 * t304 - 0.4e1 / 0.3e1 * t308 * t342 * t310 - 0.8e1 / 0.9e1 * t308 * t349 * t171 * t161 - 0.56e2 / 0.27e2 * t314 * params.omega * t406 * t324 + 0.28e2 / 0.27e2 * t328 * t572 * t338 + 0.28e2 / 0.27e2 * t308 * t309 * params.d * t406 + 0.8e1 / 0.3e1 * t314 * t354 * t316 + 0.52e2 / 0.27e2 * t322 * t449 * t11 * t324 - 0.2e1 * t314 * t315 * t452 * t45 - 0.4e1 / 0.3e1 * t322 * t323 * t316
  t922 = t3 ** 2
  t939 = t335 * params.c
  t941 = t449 * t40
  t957 = t161 * t40
  t970 = t146 * t33 * t449
  t975 = t422 * t544
  t979 = -0.8e1 / 0.27e2 * t2 * t922 * params.m1 * t562 * t484 * t11 * t324 + t328 * t329 * t45 * t733 + t308 * t28 * t733 * t343 + t336 * t337 * t330 / 0.3e1 + t36 * t939 * t941 * t338 / 0.27e2 + 0.2e1 / 0.3e1 * t308 * t348 * t267 * t350 + 0.2e1 / 0.9e1 * t308 * t752 * t137 * t663 * t449 - 0.4e1 / 0.3e1 * t328 * t358 * t330 - 0.4e1 / 0.9e1 * t336 * t957 * t338 + 0.26e2 / 0.81e2 * t281 * t957 * t45 * t432 - 0.5e1 / 0.54e2 * t427 * t941 * t45 * t432 + 0.4e1 / 0.9e1 * t970 * t281 * t40 * t468 + t414 * t416 * t975 / 0.6e1
  t1003 = t832 * t145
  t1027 = t757 * t40 * t45
  t1031 = 0.2e1 / 0.9e1 * t574 * t575 * t423 + 0.2e1 / 0.27e2 * t281 * t773 * t40 * t45 * t855 * t562 * t431 + t397 * t398 * t390 * t171 / 0.9e1 + 0.2e1 / 0.9e1 * t404 * t408 * t391 - 0.5e1 / 0.27e2 * t397 * t366 * t449 * t399 - 0.11e2 / 0.27e2 * t404 * t1003 * t304 - t584 * t419 / 0.3e1 - t584 * t424 / 0.3e1 + t365 * t367 * t452 * t302 * params.d / 0.6e1 + t365 * t367 * t169 * t389 * params.d / 0.3e1 + t430 * t419 / 0.18e2 + t430 * t424 / 0.18e2 + params.b * t939 * t1027 * t432 / 0.162e3
  t1057 = t18 * t449
  t1061 = 0.24e2 * t19 * t773 - 0.36e2 * t1057 + 0.12e2 * t166
  t1093 = t427 * t484 * t40 * t45 * t576 / 0.27e2 + 0.2e1 / 0.9e1 * t574 * t575 * t418 - 0.11e2 / 0.27e2 * t281 * t1027 * t576 + 0.26e2 / 0.81e2 * t365 * t366 * t161 * t304 - t439 * t366 * t157 * t452 * t302 / 0.6e1 - t439 * t366 * t567 * t389 / 0.3e1 + t439 * t366 * t24 * t1061 * t302 / 0.6e1 + t439 * t366 * t453 * t389 / 0.2e1 + t473 * t549 * t780 / 0.3e1 + 0.2e1 / 0.3e1 * t473 * t549 * t784 + 0.2e1 / 0.9e1 * t560 * t563 * t418 + 0.2e1 / 0.9e1 * t560 * t563 * t423 + 0.4e1 / 0.81e2 * t362 * t437 * t557 * t272 * t561 * t274 / t7 / t772 * t431
  t1119 = t43 / t8 / t772
  t1124 = t495 * t187
  t1130 = t166 - t1057
  t1131 = 0.6e1 * t1130
  t1135 = f.my_piecewise3(t64, 0, 0.80e2 / 0.27e2 / t70 * t1124 + 0.40e2 / 0.3e1 * t71 * t187 * t499 + 0.8e1 / 0.3e1 * t186 * t1131)
  t1148 = t505 * t192
  t1154 = -t1131
  t1158 = f.my_piecewise3(t75, 0, 0.80e2 / 0.27e2 / t77 * t1148 + 0.40e2 / 0.3e1 * t78 * t192 * t508 + 0.8e1 / 0.3e1 * t191 * t1154)
  t1176 = 0.1e1 / t91 / t487 / r0
  t1177 = s0 * t1176
  t1178 = t1177 * t73
  t1180 = t490 * t190
  t1182 = t210 * t503
  t1184 = t94 * t1135
  t1185 = t101 * t1158
  t1186 = -0.1232e4 / 0.27e2 * t1178 + 0.88e2 / 0.3e1 * t1180 - 0.8e1 * t1182 + t1184 + t1185
  t1196 = -0.4312e4 / 0.81e2 * t1119 - t291 * t375 * t503 + t291 * t292 * t1135 / 0.8e1 - t1130 * s2 * t299 / 0.8e1 + 0.3e1 / 0.8e1 * t536 * t386 + 0.3e1 / 0.8e1 * t383 * t541 + t297 * t298 * t1158 / 0.8e1 + t1130 * s0 * t293 / 0.8e1 + 0.3e1 / 0.8e1 * t518 * t379 - 0.2e1 * t372 * t529 + 0.3e1 / 0.8e1 * t372 * t532 + 0.11e2 / 0.3e1 * t291 * t525 * t190 - 0.7e1 / 0.48e2 * t85 * t1186 - t518 * t376 + 0.11e2 / 0.3e1 * t372 * t526 - 0.154e3 / 0.27e2 * t291 * t1176 * t85 * t73
  t1204 = t273 * t1003
  t1215 = t146 * t33 * t161
  t1220 = -0.7e1 / 0.9e1 * t473 * t275 * t418 - 0.7e1 / 0.9e1 * t473 * t275 * t423 - 0.4e1 / 0.9e1 * t560 * t856 * t431 + 0.2e1 / 0.9e1 * t439 * t366 * t149 * t169 * t302 + 0.2e1 / 0.9e1 * t439 * t366 * t477 * t389 + t439 * t366 * t458 * t544 / 0.2e1 + t439 * t366 * t482 * t1196 / 0.6e1 + t473 * t549 * t975 / 0.3e1 + 0.4e1 / 0.9e1 * t1204 * t469 + 0.2e1 / 0.9e1 * t970 * t427 * t152 + 0.4e1 / 0.9e1 * t970 * t362 * t349 * t171 - 0.16e2 / 0.9e1 * t1215 * t465 - 0.16e2 / 0.9e1 * t1215 * t469
  t1261 = t171 ** 2
  t1263 = t1261 * t752 * t757
  t1265 = t664 * t449
  t1267 = t172 * t161
  t1269 = t47 * t406
  t1284 = t85 * t1061
  t1311 = 0.3e1 / 0.32e2 * t200 * t678 + t86 * (-t1263 / 0.81e2 + 0.5e1 / 0.81e2 * t1265 - 0.26e2 / 0.243e3 * t1267 + 0.14e2 / 0.243e3 * t1269) * t103 / 0.32e2 + 0.3e1 / 0.32e2 * t86 * t671 * t215 + 0.3e1 / 0.32e2 * t86 * t203 * t514 + t86 * t88 * t1186 / 0.32e2 + t1284 * t119 / 0.576e3 + t656 * t223 / 0.192e3 + t656 * t237 / 0.192e3 + t200 * t691 / 0.192e3 + t200 * t694 / 0.96e2 + t200 * t716 / 0.192e3 + t86 * (0.2e1 / 0.9e1 * t1263 - 0.10e2 / 0.9e1 * t1265 + 0.52e2 / 0.27e2 * t1267 - 0.28e2 / 0.27e2 * t1269) * t118 / 0.576e3 + t86 * t690 * t236 / 0.192e3 + t86 * t222 * t715 / 0.192e3
  t1325 = f.my_piecewise3(t64, 0, 0.440e3 / 0.27e2 * t71 * t1124 + 0.88e2 / 0.3e1 * t188 * t499 + 0.11e2 / 0.3e1 * t72 * t1131)
  t1334 = f.my_piecewise3(t75, 0, 0.440e3 / 0.27e2 * t78 * t1148 + 0.88e2 / 0.3e1 * t193 * t508 + 0.11e2 / 0.3e1 * t79 * t1154)
  t1380 = f.my_piecewise3(t64, 0, 0.2e1 * t63 * t1131 + 0.6e1 * t187 * t499)
  t1396 = f.my_piecewise3(t75, 0, 0.2e1 * t74 * t1154 + 0.6e1 * t192 * t508)
  t1415 = 0.2e1 / 0.3e1 * t1185 + 0.308e3 / 0.27e2 * t130 * t1176 * t73 + 0.2e1 * t625 * t258 - 0.22e2 / 0.3e1 * t255 * t632 + 0.176e3 / 0.9e1 * t1180 - 0.16e2 / 0.3e1 * t1182 + 0.2e1 / 0.3e1 * t1184 - 0.2464e4 / 0.81e2 * t1178 - t1380 * s2 * t126 / 0.4e1 - 0.3e1 / 0.4e1 * t613 * t249 - 0.3e1 / 0.4e1 * t246 * t618 - t125 * t100 * t1158 / 0.4e1 - t1396 * s0 * t131 / 0.4e1 - 0.3e1 / 0.4e1 * t625 * t261 + 0.4e1 * t255 * t635 - 0.3e1 / 0.4e1 * t255 * t638 - 0.22e2 / 0.3e1 * t130 * t489 * t190 + 0.2e1 * t130 * t209 * t503 - t130 * t93 * t1135 / 0.4e1
  t1439 = t86 * t107 * (-0.1232e4 / 0.27e2 * t1177 * t112 + 0.88e2 / 0.3e1 * t490 * t230 - 0.8e1 * t210 * t706 + t94 * t1325 + t101 * t1334) / 0.576e3 - 0.3e1 / 0.20e2 * t60 * t1061 * t81 - 0.9e1 / 0.20e2 * t60 * t452 * t196 - 0.9e1 / 0.20e2 * t60 * t169 * t652 - 0.3e1 / 0.20e2 * t60 * t22 * (t1135 + t1158) + t1284 * t104 / 0.32e2 + 0.3e1 / 0.32e2 * t656 * t204 + 0.3e1 / 0.32e2 * t656 * t216 + 0.3e1 / 0.32e2 * t200 * t672 + 0.3e1 / 0.16e2 * t200 * t675 - t85 * t1415 / 0.8e1 - 0.88e2 / 0.3e1 * t485 * t181 + 0.8e1 * t162 * t731 - t44 * (t1061 * t50 / 0.72e2 + t452 * t178 / 0.24e2 + t169 * t728 / 0.24e2 + t22 * (-0.14e2 / 0.9e1 * t1263 + 0.70e2 / 0.9e1 * t1265 - 0.364e3 / 0.27e2 * t1267 + 0.196e3 / 0.27e2 * t1269) / 0.72e2) + 0.1232e4 / 0.27e2 * t1119 * t53
  t1443 = 0.4e1 / 0.3e1 * t464 * t281 * t268 + 0.4e1 / 0.3e1 * t464 * t362 * t342 * params.d + 0.4e1 / 0.9e1 * t1204 * t465 - 0.14e2 / 0.81e2 * t439 * t366 * t406 * t22 * t302 - t439 * t366 * t440 * t544 / 0.6e1 + 0.67e2 / 0.81e2 * t473 * t848 * t431 - t593 * t1061 * t45 + 0.4e1 / 0.3e1 * t596 * t736 + 0.8e1 / 0.9e1 * t600 * t601 * t161 - 0.28e2 / 0.27e2 * t600 * t29 * t406 - t594 * t597 - 0.2e1 / 0.3e1 * t596 * t602 - 0.2e1 / 0.9e1 * t600 * t752 * t663 * t449 + t36 * t151 * (t1311 + t1439)
  d111 = 0.3e1 * params.a * (-0.4e1 / 0.9e1 * t14 * t17 * t22 * t29 + 0.2e1 / 0.9e1 * t38 * t139 - 0.8e1 / 0.9e1 * t147 * t150 * t152 + 0.4e1 / 0.3e1 * t147 * t158 * t268 + 0.4e1 / 0.9e1 * t276 * t278 + t284 * t305 / 0.27e2 - 0.4e1 / 0.9e1 * t308 * t309 * t310 - 0.4e1 / 0.3e1 * t314 * t315 * t316 - 0.4e1 / 0.9e1 * t322 * t323 * t324 + 0.2e1 / 0.3e1 * t328 * t329 * t330 + t435 - t439 * t366 * t440 * t389 / 0.9e1 + t439 * t366 * t453 * t302 / 0.6e1 + t439 * t366 * t458 * t389 / 0.3e1 + 0.4e1 / 0.9e1 * t464 * t465 + 0.4e1 / 0.9e1 * t464 * t469 - 0.7e1 / 0.27e2 * t473 * t275 * t431 + 0.2e1 / 0.27e2 * t439 * t366 * t477 * t302 + t439 * t366 * t482 * t544 / 0.6e1 + 0.2e1 / 0.9e1 * t473 * t549 * t418 + 0.2e1 / 0.9e1 * t473 * t549 * t423 + t739) + t6 * params.a * (t812 + t867 + t921 + t979 + t1031 + t1093 + t1220 + t1443)

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

  t1 = params.m1 * params.omega
  t2 = r0 + r1
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t6 = jnp.erfc(t1 * t4)
  t7 = t2 ** 2
  t8 = t7 * t2
  t9 = 0.1e1 / t8
  t11 = r0 - r1
  t12 = t7 ** 2
  t13 = 0.1e1 / t12
  t14 = t11 * t13
  t16 = t11 ** 2
  t17 = t12 * t2
  t18 = 0.1e1 / t17
  t21 = 0.24e2 * t16 * t18 - 0.36e2 * t14 + 0.12e2 * t9
  t22 = t6 * t21
  t24 = params.d * t4 + 0.1e1
  t25 = 0.1e1 / t24
  t28 = jnp.exp(-params.c * t4)
  t29 = params.b * t28
  t30 = jnp.sqrt(jnp.pi)
  t31 = 0.1e1 / t30
  t32 = t25 * t31
  t34 = t29 * t32 * params.m2
  t35 = params.m2 ** 2
  t36 = params.omega ** 2
  t38 = t3 ** 2
  t39 = 0.1e1 / t38
  t41 = jnp.exp(-t35 * t36 * t39)
  t42 = params.omega * t41
  t44 = 0.1e1 / t3 / t7
  t45 = 0.1e1 / t7
  t46 = t11 * t45
  t49 = 0.2e1 * t16 * t9 - 0.2e1 * t46
  t50 = t44 * t49
  t52 = s0 + 0.2e1 * s1 + s2
  t54 = 0.1e1 / t38 / t7
  t55 = t52 * t54
  t57 = 2 ** (0.1e1 / 0.3e1)
  t58 = r0 ** 2
  t59 = r0 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t62 = 0.1e1 / t60 / t58
  t63 = s0 * t62
  t64 = 0.1e1 / t2
  t65 = t11 * t64
  t66 = 0.1e1 + t65
  t67 = t66 <= f.p.zeta_threshold
  t68 = f.p.zeta_threshold ** 2
  t69 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t70 = t69 ** 2
  t71 = t70 * t68
  t72 = t66 ** 2
  t73 = t66 ** (0.1e1 / 0.3e1)
  t74 = t73 ** 2
  t75 = t74 * t72
  t76 = f.my_piecewise3(t67, t71, t75)
  t77 = t63 * t76
  t78 = r1 ** 2
  t79 = r1 ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t82 = 0.1e1 / t80 / t78
  t83 = s2 * t82
  t84 = 0.1e1 - t65
  t85 = t84 <= f.p.zeta_threshold
  t86 = t84 ** 2
  t87 = t84 ** (0.1e1 / 0.3e1)
  t88 = t87 ** 2
  t89 = t88 * t86
  t90 = f.my_piecewise3(t85, t71, t89)
  t91 = t83 * t90
  t92 = t77 + t91
  t95 = t65 / 0.6e1
  t97 = (0.7e1 / 0.6e1 + t95) * s0
  t98 = t62 * t57
  t99 = t98 * t76
  t103 = (0.7e1 / 0.6e1 - t95) * s2
  t104 = t82 * t57
  t105 = t104 * t90
  t108 = 0.7e1 / 0.6e1 * t55 - 0.7e1 / 0.48e2 * t57 * t92 + t97 * t99 / 0.8e1 + t103 * t105 / 0.8e1
  t114 = -t16 * t45 + 0.1e1
  t115 = t44 * t114
  t117 = 0.1e1 / t38 / t8
  t118 = t52 * t117
  t122 = 0.1e1 / t60 / t58 / r0
  t123 = s0 * t122
  t124 = t123 * t76
  t126 = t74 * t66
  t127 = t64 - t46
  t128 = t126 * t127
  t130 = f.my_piecewise3(t67, 0, 0.8e1 / 0.3e1 * t128)
  t131 = t63 * t130
  t132 = t88 * t84
  t133 = -t127
  t134 = t132 * t133
  t136 = f.my_piecewise3(t85, 0, 0.8e1 / 0.3e1 * t134)
  t137 = t83 * t136
  t138 = -0.8e1 / 0.3e1 * t124 + t131 + t137
  t141 = t127 / 0.6e1
  t142 = t141 * s0
  t145 = t122 * t57
  t146 = t145 * t76
  t149 = t98 * t130
  t153 = -t141 * s2
  t156 = t104 * t136
  t159 = -0.28e2 / 0.9e1 * t118 - 0.7e1 / 0.48e2 * t57 * t138 + t142 * t99 / 0.8e1 - t97 * t146 / 0.3e1 + t97 * t149 / 0.8e1 + t153 * t105 / 0.8e1 + t103 * t156 / 0.8e1
  t164 = t4 * t49
  t166 = 0.1e1 / t38 / t12
  t167 = t52 * t166
  t169 = t58 ** 2
  t171 = 0.1e1 / t60 / t169
  t172 = s0 * t171
  t173 = t172 * t76
  t175 = t123 * t130
  t177 = t127 ** 2
  t178 = t74 * t177
  t180 = t11 * t9
  t181 = -t45 + t180
  t182 = 0.2e1 * t181
  t186 = f.my_piecewise3(t67, 0, 0.40e2 / 0.9e1 * t178 + 0.8e1 / 0.3e1 * t126 * t182)
  t187 = t63 * t186
  t188 = t133 ** 2
  t189 = t88 * t188
  t191 = -t182
  t195 = f.my_piecewise3(t85, 0, 0.40e2 / 0.9e1 * t189 + 0.8e1 / 0.3e1 * t132 * t191)
  t196 = t83 * t195
  t197 = 0.88e2 / 0.9e1 * t173 - 0.16e2 / 0.3e1 * t175 + t187 + t196
  t200 = t181 / 0.3e1
  t201 = t200 * s0
  t208 = t171 * t57
  t209 = t208 * t76
  t212 = t145 * t130
  t215 = t98 * t186
  t219 = -t200 * s2
  t224 = t104 * t195
  t227 = 0.308e3 / 0.27e2 * t167 - 0.7e1 / 0.48e2 * t57 * t197 + t201 * t99 / 0.8e1 - 0.2e1 / 0.3e1 * t142 * t146 + t142 * t149 / 0.4e1 + 0.11e2 / 0.9e1 * t97 * t209 - 0.2e1 / 0.3e1 * t97 * t212 + t97 * t215 / 0.8e1 + t219 * t105 / 0.8e1 + t153 * t156 / 0.4e1 + t103 * t224 / 0.8e1
  t232 = t4 * t114
  t234 = 0.1e1 / t38 / t17
  t235 = t52 * t234
  t237 = t145 * t186
  t239 = 0.1e1 / t73
  t240 = t177 * t127
  t243 = t74 * t127
  t246 = t9 - t14
  t247 = 0.6e1 * t246
  t251 = f.my_piecewise3(t67, 0, 0.80e2 / 0.27e2 * t239 * t240 + 0.40e2 / 0.3e1 * t243 * t182 + 0.8e1 / 0.3e1 * t126 * t247)
  t252 = t98 * t251
  t256 = -t246 * s2
  t263 = 0.1e1 / t87
  t264 = t188 * t133
  t267 = t88 * t133
  t270 = -t247
  t274 = f.my_piecewise3(t85, 0, 0.80e2 / 0.27e2 * t263 * t264 + 0.40e2 / 0.3e1 * t267 * t191 + 0.8e1 / 0.3e1 * t132 * t270)
  t275 = t104 * t274
  t278 = t246 * s0
  t287 = t208 * t130
  t292 = 0.1e1 / t60 / t169 / r0
  t293 = s0 * t292
  t294 = t293 * t76
  t296 = t172 * t130
  t298 = t123 * t186
  t300 = t63 * t251
  t301 = t83 * t274
  t302 = -0.1232e4 / 0.27e2 * t294 + 0.88e2 / 0.3e1 * t296 - 0.8e1 * t298 + t300 + t301
  t308 = t292 * t57
  t309 = t308 * t76
  t312 = -0.4312e4 / 0.81e2 * t235 - t97 * t237 + t97 * t252 / 0.8e1 + t256 * t105 / 0.8e1 + 0.3e1 / 0.8e1 * t219 * t156 + 0.3e1 / 0.8e1 * t153 * t224 + t103 * t275 / 0.8e1 + t278 * t99 / 0.8e1 + 0.3e1 / 0.8e1 * t201 * t149 - 0.2e1 * t142 * t212 + 0.3e1 / 0.8e1 * t142 * t215 + 0.11e2 / 0.3e1 * t97 * t287 - 0.7e1 / 0.48e2 * t57 * t302 - t201 * t146 + 0.11e2 / 0.3e1 * t142 * t209 - 0.154e3 / 0.27e2 * t97 * t309
  t317 = t35 * params.m2
  t319 = t29 * t32 * t317
  t320 = t36 * params.omega
  t321 = t320 * t45
  t322 = t41 * t114
  t323 = t322 * t227
  t327 = t31 * t317
  t329 = 0.1e1 / t3 / t12
  t330 = t320 * t329
  t331 = t330 * t41
  t332 = t327 * t331
  t333 = t24 ** 2
  t334 = 0.1e1 / t333
  t336 = params.d * t25 + params.c
  t337 = t336 * t4
  t339 = 0.47e2 - 0.7e1 * t337
  t342 = t114 * t339 / 0.72e2 - 0.2e1 / 0.3e1
  t344 = 3 ** (0.1e1 / 0.3e1)
  t345 = t344 ** 2
  t346 = jnp.pi ** 2
  t347 = t346 ** (0.1e1 / 0.3e1)
  t348 = t347 ** 2
  t349 = t345 * t348
  t350 = t76 + t90
  t354 = t57 * t114
  t356 = 0.5e1 / 0.2e1 - t337 / 0.18e2
  t357 = t356 * t92
  t360 = t337 - 0.11e2
  t362 = t70 * t68 * f.p.zeta_threshold
  t365 = f.my_piecewise3(t67, t362, t74 * t72 * t66)
  t369 = f.my_piecewise3(t85, t362, t88 * t86 * t84)
  t371 = t63 * t365 + t83 * t369
  t372 = t360 * t371
  t377 = f.my_piecewise3(t67, t68, t72)
  t378 = t377 * s2
  t379 = t82 * t90
  t382 = f.my_piecewise3(t85, t68, t86)
  t383 = t382 * s0
  t384 = t62 * t76
  t390 = -t55 * t342 - 0.3e1 / 0.20e2 * t349 * t114 * t350 + t354 * t357 / 0.32e2 + t354 * t372 / 0.576e3 - t57 * (0.2e1 / 0.3e1 * t77 + 0.2e1 / 0.3e1 * t91 - t378 * t379 / 0.4e1 - t383 * t384 / 0.4e1) / 0.8e1
  t391 = t334 * t390
  t392 = t391 * params.d
  t393 = t29 * t392
  t396 = t31 * t41
  t397 = params.m2 * params.omega
  t399 = t396 * t397 * t13
  t400 = params.c ** 2
  t401 = params.b * t400
  t402 = t28 * t25
  t403 = t402 * t390
  t404 = t401 * t403
  t408 = 0.1e1 / t333 / t24
  t409 = t408 * t390
  t410 = params.d ** 2
  t411 = t409 * t410
  t412 = t29 * t411
  t416 = t396 * t397 * t117
  t417 = params.b * params.c
  t418 = t417 * t403
  t424 = t396 * t397 * t54
  t428 = t410 * t334
  t430 = 0.1e1 / t38 / t2
  t433 = 0.1e1 / t3 / t2
  t435 = t336 * t433 - t428 * t430
  t436 = 0.7e1 / 0.3e1 * t435
  t439 = t114 * t436 / 0.72e2 + t49 * t339 / 0.72e2
  t444 = t130 + t136
  t448 = t57 * t49
  t451 = t435 / 0.54e2
  t452 = t451 * t92
  t455 = t356 * t138
  t461 = -t435 / 0.3e1
  t462 = t461 * t371
  t469 = f.my_piecewise3(t67, 0, 0.11e2 / 0.3e1 * t75 * t127)
  t473 = f.my_piecewise3(t85, 0, 0.11e2 / 0.3e1 * t89 * t133)
  t475 = -0.8e1 / 0.3e1 * t123 * t365 + t63 * t469 + t83 * t473
  t476 = t360 * t475
  t484 = f.my_piecewise3(t67, 0, 0.2e1 * t66 * t127)
  t485 = t484 * s2
  t488 = t82 * t136
  t493 = f.my_piecewise3(t85, 0, 0.2e1 * t84 * t133)
  t494 = t493 * s0
  t497 = t122 * t76
  t500 = t62 * t130
  t506 = 0.8e1 / 0.3e1 * t118 * t342 - t55 * t439 - 0.3e1 / 0.20e2 * t349 * t49 * t350 - 0.3e1 / 0.20e2 * t349 * t114 * t444 + t448 * t357 / 0.32e2 + t354 * t452 / 0.32e2 + t354 * t455 / 0.32e2 + t448 * t372 / 0.576e3 + t354 * t462 / 0.576e3 + t354 * t476 / 0.576e3 - t57 * (-0.16e2 / 0.9e1 * t124 + 0.2e1 / 0.3e1 * t131 + 0.2e1 / 0.3e1 * t137 - t485 * t379 / 0.4e1 - t378 * t488 / 0.4e1 - t494 * t384 / 0.4e1 + 0.2e1 / 0.3e1 * t383 * t497 - t383 * t500 / 0.4e1) / 0.8e1
  t507 = t402 * t506
  t508 = t417 * t507
  t511 = t334 * t506
  t512 = t511 * params.d
  t513 = t29 * t512
  t516 = -t22 * t25 + 0.2e1 / 0.9e1 * t34 * t42 * t50 * t108 + 0.2e1 / 0.9e1 * t34 * t42 * t115 * t159 + t34 * t42 * t164 * t227 / 0.2e1 + t34 * t42 * t232 * t312 / 0.6e1 + t319 * t321 * t323 / 0.3e1 + 0.4e1 / 0.9e1 * t332 * t393 + 0.2e1 / 0.9e1 * t399 * t404 + 0.4e1 / 0.9e1 * t399 * t412 - 0.16e2 / 0.9e1 * t416 * t418 - 0.16e2 / 0.9e1 * t416 * t393 + 0.4e1 / 0.3e1 * t424 * t508 + 0.4e1 / 0.3e1 * t424 * t513
  t520 = 0.1e1 / t3 / t8
  t521 = t520 * t114
  t526 = t433 * t114
  t531 = t320 * t13
  t532 = t322 * t108
  t540 = -0.6e1 * t16 * t13 + 0.8e1 * t180 - 0.2e1 * t45
  t541 = t433 * t540
  t546 = t433 * t49
  t551 = t4 * t21
  t556 = t4 * t540
  t561 = t396 * t397
  t562 = t433 * params.b
  t570 = f.my_piecewise3(t67, 0, 0.2e1 * t66 * t182 + 0.2e1 * t177)
  t571 = t570 * s2
  t576 = t82 * t195
  t582 = f.my_piecewise3(t85, 0, 0.2e1 * t84 * t191 + 0.2e1 * t188)
  t583 = t582 * s0
  t590 = t171 * t76
  t593 = t122 * t130
  t596 = t62 * t186
  t599 = 0.176e3 / 0.27e2 * t173 - 0.32e2 / 0.9e1 * t175 + 0.2e1 / 0.3e1 * t187 + 0.2e1 / 0.3e1 * t196 - t571 * t379 / 0.4e1 - t485 * t488 / 0.2e1 - t378 * t576 / 0.4e1 - t583 * t384 / 0.4e1 + 0.4e1 / 0.3e1 * t494 * t497 - t494 * t500 / 0.2e1 - 0.22e2 / 0.9e1 * t383 * t590 + 0.4e1 / 0.3e1 * t383 * t593 - t383 * t596 / 0.4e1
  t610 = t186 + t195
  t614 = t57 * t540
  t621 = t410 * params.d
  t622 = t621 * t408
  t623 = t622 * t9
  t625 = t428 * t54
  t627 = t336 * t44
  t629 = -t623 / 0.81e2 + t625 / 0.27e2 - 0.2e1 / 0.81e2 * t627
  t630 = t629 * t92
  t633 = t451 * t138
  t636 = t356 * t197
  t648 = 0.2e1 / 0.9e1 * t623 - 0.2e1 / 0.3e1 * t625 + 0.4e1 / 0.9e1 * t627
  t649 = t648 * t371
  t652 = t461 * t475
  t664 = f.my_piecewise3(t67, 0, 0.88e2 / 0.9e1 * t126 * t177 + 0.11e2 / 0.3e1 * t75 * t182)
  t671 = f.my_piecewise3(t85, 0, 0.88e2 / 0.9e1 * t132 * t188 + 0.11e2 / 0.3e1 * t89 * t191)
  t673 = 0.88e2 / 0.9e1 * t172 * t365 - 0.16e2 / 0.3e1 * t123 * t469 + t63 * t664 + t83 * t671
  t674 = t360 * t673
  t686 = -0.14e2 / 0.9e1 * t623 + 0.14e2 / 0.3e1 * t625 - 0.28e2 / 0.9e1 * t627
  t689 = t540 * t339 / 0.72e2 + t49 * t436 / 0.36e2 + t114 * t686 / 0.72e2
  t691 = -t57 * t599 / 0.8e1 - 0.88e2 / 0.9e1 * t167 * t342 - 0.3e1 / 0.20e2 * t349 * t540 * t350 - 0.3e1 / 0.10e2 * t349 * t49 * t444 - 0.3e1 / 0.20e2 * t349 * t114 * t610 + t614 * t357 / 0.32e2 + t448 * t452 / 0.16e2 + t448 * t455 / 0.16e2 + t354 * t630 / 0.32e2 + t354 * t633 / 0.16e2 + t354 * t636 / 0.32e2 + t614 * t372 / 0.576e3 + t448 * t462 / 0.288e3 + t448 * t476 / 0.288e3 + t354 * t649 / 0.576e3 + t354 * t652 / 0.288e3 + t354 * t674 / 0.576e3 + 0.16e2 / 0.3e1 * t118 * t439 - t55 * t689
  t692 = t402 * t691
  t696 = t44 * params.b
  t700 = t327 * t531
  t701 = t41 * params.b
  t702 = t701 * t403
  t705 = t320 * t9
  t706 = t327 * t705
  t707 = t701 * t507
  t710 = t35 ** 2
  t711 = t710 * params.m2
  t712 = t31 * t711
  t713 = t36 ** 2
  t714 = t713 * params.omega
  t715 = t714 * t166
  t716 = t712 * t715
  t719 = 0.4e1 / 0.9e1 * t332 * t418 - 0.14e2 / 0.81e2 * t34 * t42 * t521 * t108 - t34 * t42 * t526 * t227 / 0.6e1 + 0.67e2 / 0.81e2 * t319 * t531 * t532 - t34 * t42 * t541 * t108 / 0.6e1 - t34 * t42 * t546 * t159 / 0.3e1 + t34 * t42 * t551 * t108 / 0.6e1 + t34 * t42 * t556 * t159 / 0.2e1 + 0.2e1 * t561 * t562 * t692 - 0.8e1 / 0.3e1 * t561 * t696 * t507 - 0.52e2 / 0.27e2 * t700 * t702 + 0.4e1 / 0.3e1 * t706 * t707 + 0.8e1 / 0.27e2 * t716 * t702
  t721 = t520 * params.b
  t726 = jnp.erfc(t397 * t4)
  t727 = t726 * params.b
  t728 = t727 * params.c
  t729 = t44 * t28
  t730 = t25 * t506
  t734 = t727 * t400
  t735 = t117 * t28
  t736 = t25 * t390
  t740 = t727 * t28
  t741 = params.d * t44
  t745 = t410 * t117
  t749 = params.m1 ** 2
  t752 = jnp.exp(-t749 * t36 * t39)
  t753 = t31 * t752
  t754 = t753 * params.m1
  t755 = params.omega * t520
  t756 = t114 * t25
  t760 = t520 * t28
  t764 = params.d * t520
  t768 = params.omega * t44
  t769 = t49 * t25
  t773 = t749 * params.m1
  t774 = t31 * t773
  t775 = t774 * t320
  t776 = t13 * t752
  t780 = params.omega * t433
  t781 = t540 * t25
  t785 = t9 * t752
  t789 = t749 ** 2
  t791 = t31 * t789 * params.m1
  t792 = t791 * t714
  t793 = t166 * t752
  t797 = 0.56e2 / 0.27e2 * t561 * t721 * t403 - 0.4e1 / 0.3e1 * t728 * t729 * t730 - 0.4e1 / 0.9e1 * t734 * t735 * t736 - 0.4e1 / 0.3e1 * t740 * t511 * t741 - 0.8e1 / 0.9e1 * t740 * t409 * t745 - 0.56e2 / 0.27e2 * t754 * t755 * t756 + 0.28e2 / 0.27e2 * t728 * t760 * t736 + 0.28e2 / 0.27e2 * t740 * t391 * t764 + 0.8e1 / 0.3e1 * t754 * t768 * t769 + 0.52e2 / 0.27e2 * t775 * t776 * t756 - 0.2e1 * t754 * t780 * t781 - 0.4e1 / 0.3e1 * t775 * t785 * t769 - 0.8e1 / 0.27e2 * t792 * t793 * t756
  t798 = t433 * t28
  t799 = t25 * t691
  t802 = t334 * t691
  t803 = params.d * t433
  t806 = t54 * t28
  t810 = t400 * params.c
  t811 = t727 * t810
  t812 = t13 * t28
  t816 = t408 * t506
  t817 = t410 * t54
  t821 = t333 ** 2
  t822 = 0.1e1 / t821
  t823 = t822 * t390
  t824 = t621 * t13
  t828 = t6 * t114
  t829 = t408 * t410
  t830 = t829 * t117
  t833 = t334 * params.d
  t834 = t833 * t520
  t837 = t6 * t49
  t838 = t833 * t44
  t841 = t6 * t540
  t842 = t833 * t433
  t844 = t829 * t54
  t847 = t822 * t621
  t848 = t847 * t13
  t851 = t292 * t76
  t868 = f.my_piecewise3(t67, 0, 0.6e1 * t127 * t182 + 0.2e1 * t66 * t247)
  t869 = t868 * s2
  t876 = t82 * t274
  t884 = f.my_piecewise3(t85, 0, 0.6e1 * t133 * t191 + 0.2e1 * t84 * t270)
  t885 = t884 * s0
  t894 = t171 * t130
  t897 = t122 * t186
  t900 = t62 * t251
  t903 = 0.308e3 / 0.27e2 * t383 * t851 + 0.2e1 * t583 * t497 - 0.22e2 / 0.3e1 * t494 * t590 + 0.176e3 / 0.9e1 * t296 - 0.16e2 / 0.3e1 * t298 + 0.2e1 / 0.3e1 * t300 + 0.2e1 / 0.3e1 * t301 - 0.2464e4 / 0.81e2 * t294 - t869 * t379 / 0.4e1 - 0.3e1 / 0.4e1 * t571 * t488 - 0.3e1 / 0.4e1 * t485 * t576 - t378 * t876 / 0.4e1 - t885 * t384 / 0.4e1 - 0.3e1 / 0.4e1 * t583 * t500 + 0.4e1 * t494 * t593 - 0.3e1 / 0.4e1 * t494 * t596 - 0.22e2 / 0.3e1 * t383 * t894 + 0.2e1 * t383 * t897 - t383 * t900 / 0.4e1
  t908 = t410 ** 2
  t909 = t908 * t822
  t910 = t909 * t329
  t912 = t622 * t13
  t914 = t428 * t117
  t916 = t336 * t520
  t918 = -t910 / 0.81e2 + 0.5e1 / 0.81e2 * t912 - 0.26e2 / 0.243e3 * t914 + 0.14e2 / 0.243e3 * t916
  t919 = t918 * t92
  t922 = t629 * t138
  t925 = t451 * t197
  t928 = t356 * t302
  t931 = t57 * t21
  t948 = 0.2e1 / 0.9e1 * t910 - 0.10e2 / 0.9e1 * t912 + 0.52e2 / 0.27e2 * t914 - 0.28e2 / 0.27e2 * t916
  t949 = t948 * t371
  t952 = t648 * t475
  t955 = -t57 * t903 / 0.8e1 + 0.3e1 / 0.32e2 * t448 * t636 + t354 * t919 / 0.32e2 + 0.3e1 / 0.32e2 * t354 * t922 + 0.3e1 / 0.32e2 * t354 * t925 + t354 * t928 / 0.32e2 + t931 * t372 / 0.576e3 + t614 * t462 / 0.192e3 + t614 * t476 / 0.192e3 + t448 * t649 / 0.192e3 + t448 * t652 / 0.96e2 + t448 * t674 / 0.192e3 + t354 * t949 / 0.576e3 + t354 * t952 / 0.192e3
  t956 = t461 * t673
  t968 = t251 + t274
  t995 = f.my_piecewise3(t67, 0, 0.440e3 / 0.27e2 * t74 * t240 + 0.88e2 / 0.3e1 * t128 * t182 + 0.11e2 / 0.3e1 * t75 * t247)
  t1004 = f.my_piecewise3(t85, 0, 0.440e3 / 0.27e2 * t88 * t264 + 0.88e2 / 0.3e1 * t134 * t191 + 0.11e2 / 0.3e1 * t89 * t270)
  t1006 = -0.1232e4 / 0.27e2 * t293 * t365 + 0.88e2 / 0.3e1 * t172 * t469 - 0.8e1 * t123 * t664 + t63 * t995 + t83 * t1004
  t1007 = t360 * t1006
  t1024 = -0.14e2 / 0.9e1 * t910 + 0.70e2 / 0.9e1 * t912 - 0.364e3 / 0.27e2 * t914 + 0.196e3 / 0.27e2 * t916
  t1027 = t21 * t339 / 0.72e2 + t540 * t436 / 0.24e2 + t49 * t686 / 0.24e2 + t114 * t1024 / 0.72e2
  t1031 = t354 * t956 / 0.192e3 - 0.3e1 / 0.20e2 * t349 * t21 * t350 - 0.9e1 / 0.20e2 * t349 * t540 * t444 - 0.9e1 / 0.20e2 * t349 * t49 * t610 - 0.3e1 / 0.20e2 * t349 * t114 * t968 + t931 * t357 / 0.32e2 + 0.3e1 / 0.32e2 * t614 * t452 + 0.3e1 / 0.32e2 * t614 * t455 + 0.3e1 / 0.32e2 * t448 * t630 + 0.3e1 / 0.16e2 * t448 * t633 + t354 * t1007 / 0.576e3 - 0.88e2 / 0.3e1 * t167 * t439 + 0.8e1 * t118 * t689 - t55 * t1027 + 0.1232e4 / 0.27e2 * t235 * t342
  t1032 = t955 + t1031
  t1033 = t402 * t1032
  t1035 = t728 * t798 * t799 + t740 * t802 * t803 + t734 * t806 * t730 / 0.3e1 + t811 * t812 * t736 / 0.27e2 + 0.2e1 / 0.3e1 * t740 * t816 * t817 + 0.2e1 / 0.9e1 * t740 * t823 * t824 + 0.8e1 / 0.9e1 * t828 * t830 - 0.28e2 / 0.27e2 * t828 * t834 + 0.4e1 / 0.3e1 * t837 * t838 - t841 * t842 - 0.2e1 / 0.3e1 * t837 * t844 - 0.2e1 / 0.9e1 * t828 * t848 + t727 * t1033
  t1039 = t28 * t408
  t1040 = t1039 * t31
  t1041 = t417 * t329 * t1040
  t1042 = t397 * t41
  t1043 = t114 * t108
  t1044 = t1043 * t410
  t1045 = t1042 * t1044
  t1049 = t28 * t334
  t1050 = t1049 * t31
  t1051 = t417 * t166 * t1050
  t1053 = t317 * t320 * t41
  t1054 = t1043 * params.d
  t1055 = t1053 * t1054
  t1059 = t417 * t13 * t1050
  t1060 = t1042 * t1054
  t1064 = t417 * t9 * t1050
  t1065 = t49 * t108
  t1066 = t1065 * params.d
  t1067 = t1042 * t1066
  t1070 = t114 * t159
  t1071 = t1070 * params.d
  t1072 = t1042 * t1071
  t1076 = t401 * t329 * t1050
  t1079 = t408 * t31
  t1081 = t29 * t1079 * params.m2
  t1082 = t42 * t9
  t1083 = t1070 * t410
  t1087 = t334 * t31
  t1089 = t29 * t1087 * t317
  t1091 = t320 * t520 * t41
  t1095 = t42 * t13
  t1103 = t417 * t806 * t25
  t1105 = t31 * params.m2 * params.omega
  t1106 = t41 * t49
  t1107 = t1106 * t108
  t1108 = t1105 * t1107
  t1111 = t322 * t159
  t1112 = t1105 * t1111
  t1116 = t29 * t1087 * params.m2
  t1117 = t42 * t430
  t1118 = t540 * t108
  t1119 = t1118 * params.d
  t1123 = t1041 * t1045 / 0.27e2 + 0.2e1 / 0.27e2 * t1051 * t1055 - 0.5e1 / 0.27e2 * t1059 * t1060 + t1064 * t1067 / 0.9e1 + t1064 * t1072 / 0.9e1 + t1076 * t1060 / 0.54e2 + t1081 * t1082 * t1083 / 0.9e1 + 0.2e1 / 0.9e1 * t1089 * t1091 * t1071 - 0.5e1 / 0.27e2 * t1081 * t1095 * t1044 - 0.11e2 / 0.27e2 * t1089 * t331 * t1054 - t1103 * t1108 / 0.3e1 - t1103 * t1112 / 0.3e1 + t1116 * t1117 * t1119 / 0.6e1
  t1124 = t49 * t159
  t1125 = t1124 * params.d
  t1131 = t401 * t9 * t28 * t25
  t1136 = params.b * t810
  t1137 = t329 * t28
  t1138 = t1137 * t25
  t1139 = t1136 * t1138
  t1140 = t1105 * t532
  t1143 = t166 * t28
  t1144 = t1143 * t25
  t1145 = t401 * t1144
  t1146 = t327 * t320
  t1147 = t1146 * t532
  t1151 = t417 * t760 * t25
  t1152 = t1146 * t1107
  t1155 = t417 * t1138
  t1158 = t42 * t117
  t1163 = t417 * t735 * t25
  t1167 = t401 * t812 * t25
  t1170 = t417 * t28
  t1171 = t1170 * t392
  t1174 = t1146 * t1111
  t1177 = t18 * t28
  t1178 = t1177 * t25
  t1179 = t417 * t1178
  t1180 = t712 * t714
  t1181 = t1180 * t532
  t1184 = t1116 * t1117 * t1125 / 0.3e1 + t1131 * t1108 / 0.18e2 + t1131 * t1112 / 0.18e2 + t1139 * t1140 / 0.162e3 + t1145 * t1147 / 0.27e2 + 0.2e1 / 0.9e1 * t1151 * t1152 - 0.11e2 / 0.27e2 * t1155 * t1147 + 0.26e2 / 0.81e2 * t1116 * t1158 * t1054 + 0.26e2 / 0.81e2 * t1163 * t1140 - 0.5e1 / 0.54e2 * t1167 * t1140 + 0.4e1 / 0.9e1 * t399 * t1171 + 0.2e1 / 0.9e1 * t1151 * t1174 + 0.2e1 / 0.27e2 * t1179 * t1181
  t1186 = t42 * t54
  t1195 = t417 * t430 * t28 * t25
  t1196 = t1105 * t323
  t1199 = t1065 * t410
  t1206 = t114 * t227
  t1207 = t1206 * params.d
  t1211 = t41 * t540
  t1212 = t1211 * t108
  t1216 = t1106 * t159
  t1221 = t29 * t32 * t711
  t1222 = t714 * t117
  t1229 = t710 * t317
  t1231 = t29 * t32 * t1229
  t1232 = t713 * t320
  t1234 = 0.1e1 / t3 / t17
  t1235 = t1232 * t1234
  t1245 = -t1116 * t1186 * t1066 / 0.3e1 - t1116 * t1186 * t1071 / 0.3e1 + t1195 * t1196 / 0.6e1 + t1081 * t1082 * t1199 / 0.9e1 + 0.2e1 / 0.9e1 * t1089 * t1091 * t1066 + t1116 * t1117 * t1207 / 0.6e1 + t319 * t321 * t1212 / 0.3e1 + 0.2e1 / 0.3e1 * t319 * t321 * t1216 + 0.2e1 / 0.9e1 * t1221 * t1222 * t1107 + 0.2e1 / 0.9e1 * t1221 * t1222 * t1111 + 0.4e1 / 0.81e2 * t1231 * t1235 * t532 - 0.7e1 / 0.9e1 * t319 * t705 * t1107 - 0.7e1 / 0.9e1 * t319 * t705 * t1111
  t1249 = t822 * t31
  t1251 = t29 * t1249 * params.m2
  t1252 = t42 * t329
  t1253 = t1043 * t621
  t1258 = t29 * t1079 * t317
  t1260 = t320 * t166 * t41
  t1265 = t29 * t1087 * t711
  t1267 = t714 * t18 * t41
  t1271 = t1105 * t1212
  t1274 = t1105 * t1216
  t1277 = t774 * t330
  t1278 = t752 * t114
  t1279 = t1278 * t833
  t1282 = t753 * t1
  t1296 = t727 * params.c * t54
  t1298 = t1049 * t506 * params.d
  t1302 = t727 * t400 * t13
  t1304 = t1049 * t390 * params.d
  t1308 = t727 * params.c * t13
  t1310 = t1039 * t390 * t410
  t1314 = t727 * params.c * t117
  t1317 = -0.4e1 / 0.9e1 * t1221 * t715 * t532 + t1251 * t1252 * t1253 / 0.27e2 + 0.2e1 / 0.27e2 * t1258 * t1260 * t1044 + 0.2e1 / 0.27e2 * t1265 * t1267 * t1054 + t1195 * t1271 / 0.6e1 + t1195 * t1274 / 0.3e1 - 0.4e1 / 0.9e1 * t1277 * t1279 - 0.4e1 / 0.3e1 * t1282 * t54 * t49 * t833 - 0.4e1 / 0.9e1 * t1282 * t13 * t114 * t829 + 0.16e2 / 0.9e1 * t1282 * t117 * t114 * t833 + 0.2e1 / 0.3e1 * t1296 * t1298 + t1302 * t1304 / 0.9e1 + 0.2e1 / 0.9e1 * t1308 * t1310 - 0.8e1 / 0.9e1 * t1314 * t1304
  t1329 = 0.1e1 / t821 / t24
  t1352 = t12 * t7
  t1354 = 0.1e1 / t3 / t1352
  t1369 = t400 ** 2
  t1371 = t1234 * t28
  t1382 = 0.8e1 / 0.9e1 * t740 * t822 * t506 * t824 + 0.8e1 / 0.27e2 * t740 * t1329 * t390 * t908 * t1234 + 0.8e1 / 0.3e1 * t792 * t234 * t752 * t756 - 0.8e1 / 0.3e1 * t754 * t780 * t21 * t25 - 0.8e1 / 0.3e1 * t775 * t785 * t781 - 0.32e2 / 0.27e2 * t792 * t793 * t769 - 0.16e2 / 0.81e2 * t31 * t789 * t773 * t1232 * t1354 * t752 * t756 + 0.4e1 / 0.3e1 * t728 * t798 * t25 * t1032 + 0.2e1 / 0.3e1 * t734 * t806 * t799 + 0.4e1 / 0.27e2 * t811 * t812 * t730 + t727 * t1369 * t1371 * t736 / 0.81e2 - 0.224e3 / 0.27e2 * t754 * t755 * t769 - 0.736e3 / 0.81e2 * t775 * t18 * t752 * t756
  t1429 = 0.16e2 / 0.3e1 * t754 * t768 * t781 + 0.208e3 / 0.27e2 * t775 * t776 * t769 - 0.8e1 / 0.3e1 * t728 * t729 * t799 - 0.16e2 / 0.9e1 * t734 * t735 * t730 - 0.8e1 / 0.27e2 * t811 * t1177 * t736 - 0.8e1 / 0.3e1 * t740 * t802 * t741 - 0.280e3 / 0.81e2 * t740 * t391 * params.d * t329 + 0.112e3 / 0.27e2 * t728 * t760 * t730 + 0.160e3 / 0.81e2 * t734 * t1143 * t736 + 0.112e3 / 0.27e2 * t740 * t511 * t764 + 0.320e3 / 0.81e2 * t740 * t409 * t410 * t166 + 0.560e3 / 0.81e2 * t754 * params.omega * t329 * t756 - 0.280e3 / 0.81e2 * t728 * t1137 * t736 + 0.4e1 / 0.3e1 * t740 * t334 * t1032 * t803
  t1446 = 0.1e1 / t1352
  t1476 = 0.4e1 / 0.3e1 * t740 * t408 * t691 * t817 - 0.32e2 / 0.9e1 * t740 * t816 * t745 - 0.16e2 / 0.9e1 * t740 * t823 * t621 * t18 + 0.2e1 / 0.81e2 * t401 * t234 * t1040 * t1045 + 0.4e1 / 0.81e2 * t401 * t1446 * t1050 * t1055 + 0.232e3 / 0.243e3 * t417 * t18 * t1050 * t1060 - 0.14e2 / 0.81e2 * t401 * t1234 * t1050 * t1060 + 0.16e2 / 0.9e1 * t828 * t847 * t18 - 0.112e3 / 0.27e2 * t837 * t834 - 0.320e3 / 0.81e2 * t828 * t829 * t166 + 0.280e3 / 0.81e2 * t828 * t833 * t329 - 0.4e1 / 0.3e1 * t22 * t842 - 0.4e1 / 0.3e1 * t841 * t844 - 0.8e1 / 0.9e1 * t837 * t848
  t1492 = t177 ** 2
  t1498 = t182 ** 2
  t1503 = t11 * t18
  t1504 = -t13 + t1503
  t1505 = 0.24e2 * t1504
  t1509 = f.my_piecewise3(t67, 0, -0.80e2 / 0.81e2 / t73 / t66 * t1492 + 0.160e3 / 0.9e1 * t239 * t177 * t182 + 0.40e2 / 0.3e1 * t74 * t1498 + 0.160e3 / 0.9e1 * t243 * t247 + 0.8e1 / 0.3e1 * t126 * t1505)
  t1530 = f.my_piecewise3(t67, 0, 0.8e1 * t127 * t247 + 0.2e1 * t66 * t1505 + 0.6e1 * t1498)
  t1537 = 0.8e1 * t494 * t897 - t494 * t900 - 0.44e2 / 0.3e1 * t383 * t171 * t186 + 0.8e1 / 0.3e1 * t383 * t122 * t251 - t383 * t62 * t1509 / 0.4e1 + 0.1232e4 / 0.27e2 * t494 * t851 + 0.1232e4 / 0.27e2 * t383 * t292 * t130 + 0.8e1 / 0.3e1 * t885 * t497 + 0.8e1 * t583 * t593 - 0.88e2 / 0.3e1 * t494 * t894 - t1530 * s2 * t379 / 0.4e1 - t869 * t488 - 0.3e1 / 0.2e1 * t571 * t576
  t1541 = t188 ** 2
  t1547 = t191 ** 2
  t1552 = -t1505
  t1556 = f.my_piecewise3(t85, 0, -0.80e2 / 0.81e2 / t87 / t84 * t1541 + 0.160e3 / 0.9e1 * t263 * t188 * t191 + 0.40e2 / 0.3e1 * t88 * t1547 + 0.160e3 / 0.9e1 * t267 * t270 + 0.8e1 / 0.3e1 * t132 * t1552)
  t1566 = f.my_piecewise3(t85, 0, 0.8e1 * t133 * t270 + 0.2e1 * t84 * t1552 + 0.6e1 * t1547)
  t1575 = 0.1e1 / t60 / t169 / t58
  t1581 = t83 * t1556
  t1583 = s0 * t1575
  t1584 = t1583 * t76
  t1586 = t293 * t130
  t1588 = t172 * t186
  t1590 = t123 * t251
  t1592 = t63 * t1509
  t1594 = -t485 * t876 - t378 * t82 * t1556 / 0.4e1 - t1566 * s0 * t384 / 0.4e1 - t885 * t500 - 0.3e1 / 0.2e1 * t583 * t596 - 0.5236e4 / 0.81e2 * t383 * t1575 * t76 - 0.44e2 / 0.3e1 * t583 * t590 + 0.2e1 / 0.3e1 * t1581 + 0.41888e5 / 0.243e3 * t1584 - 0.9856e4 / 0.81e2 * t1586 + 0.352e3 / 0.9e1 * t1588 - 0.64e2 / 0.9e1 * t1590 + 0.2e1 / 0.3e1 * t1592
  t1600 = t908 * params.d * t1329 * t234
  t1602 = t909 * t1234
  t1604 = t622 * t18
  t1606 = t428 * t166
  t1608 = t336 * t329
  t1627 = 0.20944e5 / 0.81e2 * t1584 - 0.4928e4 / 0.27e2 * t1586 + 0.176e3 / 0.3e1 * t1588 - 0.32e2 / 0.3e1 * t1590 + t1592 + t1581
  t1635 = -0.120e3 * t16 * t1446 - 0.72e2 * t13 + 0.192e3 * t1503
  t1636 = t57 * t1635
  t1680 = 0.1e1 / t38 / t1352
  t1681 = t52 * t1680
  t1684 = -t57 * (t1537 + t1594) / 0.8e1 + t354 * (-0.4e1 / 0.243e3 * t1600 + 0.28e2 / 0.243e3 * t1602 - 0.232e3 / 0.729e3 * t1604 + 0.100e3 / 0.243e3 * t1606 - 0.140e3 / 0.729e3 * t1608) * t92 / 0.32e2 + t354 * t918 * t138 / 0.8e1 + 0.3e1 / 0.16e2 * t354 * t629 * t197 + t354 * t451 * t302 / 0.8e1 + t354 * t356 * t1627 / 0.32e2 + t1636 * t372 / 0.576e3 + t931 * t462 / 0.144e3 + t931 * t476 / 0.144e3 + t614 * t649 / 0.96e2 + t614 * t652 / 0.48e2 + t614 * t674 / 0.96e2 + t448 * t949 / 0.144e3 + t448 * t952 / 0.48e2 + t448 * t956 / 0.48e2 - t55 * (t1635 * t339 / 0.72e2 + t21 * t436 / 0.18e2 + t540 * t686 / 0.12e2 + t49 * t1024 / 0.18e2 + t114 * (-0.56e2 / 0.27e2 * t1600 + 0.392e3 / 0.27e2 * t1602 - 0.3248e4 / 0.81e2 * t1604 + 0.1400e4 / 0.27e2 * t1606 - 0.1960e4 / 0.81e2 * t1608) / 0.72e2) + 0.4928e4 / 0.27e2 * t235 * t439 - 0.176e3 / 0.3e1 * t167 * t689 + 0.32e2 / 0.3e1 * t118 * t1027 - 0.20944e5 / 0.81e2 * t1681 * t342
  t1744 = f.my_piecewise3(t67, 0, 0.880e3 / 0.81e2 * t239 * t1492 + 0.880e3 / 0.9e1 * t178 * t182 + 0.88e2 / 0.3e1 * t126 * t1498 + 0.352e3 / 0.9e1 * t128 * t247 + 0.11e2 / 0.3e1 * t75 * t1505)
  t1757 = f.my_piecewise3(t85, 0, 0.880e3 / 0.81e2 * t263 * t1541 + 0.880e3 / 0.9e1 * t189 * t191 + 0.88e2 / 0.3e1 * t132 * t1547 + 0.352e3 / 0.9e1 * t134 * t270 + 0.11e2 / 0.3e1 * t89 * t1552)
  t1780 = 0.3e1 / 0.8e1 * t614 * t633 + 0.3e1 / 0.16e2 * t614 * t636 + t448 * t919 / 0.8e1 + 0.3e1 / 0.8e1 * t448 * t922 + 0.3e1 / 0.8e1 * t448 * t925 + t448 * t928 / 0.8e1 + t354 * t360 * (0.20944e5 / 0.81e2 * t1583 * t365 - 0.4928e4 / 0.27e2 * t293 * t469 + 0.176e3 / 0.3e1 * t172 * t664 - 0.32e2 / 0.3e1 * t123 * t995 + t63 * t1744 + t83 * t1757) / 0.576e3 + t448 * t1007 / 0.144e3 + t354 * (0.8e1 / 0.27e2 * t1600 - 0.56e2 / 0.27e2 * t1602 + 0.464e3 / 0.81e2 * t1604 - 0.200e3 / 0.27e2 * t1606 + 0.280e3 / 0.81e2 * t1608) * t371 / 0.576e3 + t354 * t948 * t475 / 0.144e3 + t354 * t648 * t673 / 0.96e2
  t1799 = t396 * t397 * t1234
  t1812 = t396 * t397 * t166
  t1817 = t31 * t1229
  t1818 = t1232 * t1354
  t1825 = -0.8e1 / 0.27e2 * t828 * t1329 * t908 * t1234 + t727 * t402 * (t1684 + t354 * t461 * t1006 / 0.144e3 - 0.3e1 / 0.20e2 * t349 * t1635 * t350 - 0.3e1 / 0.5e1 * t349 * t21 * t444 - 0.9e1 / 0.10e2 * t349 * t540 * t610 - 0.3e1 / 0.5e1 * t349 * t49 * t968 - 0.3e1 / 0.20e2 * t349 * t114 * (t1509 + t1556) + t1636 * t357 / 0.32e2 + t931 * t452 / 0.8e1 + t931 * t455 / 0.8e1 + 0.3e1 / 0.16e2 * t614 * t630 + t1780) + 0.8e1 / 0.3e1 * t841 * t838 + 0.32e2 / 0.9e1 * t837 * t830 - 0.14e2 / 0.9e1 * t319 * t705 * t323 - 0.16e2 / 0.9e1 * t1221 * t715 * t1111 + 0.8e1 / 0.9e1 * t399 * t401 * t507 + 0.8e1 / 0.81e2 * t1799 * t1136 * t403 + 0.16e2 / 0.9e1 * t399 * t29 * t816 * t410 + 0.16e2 / 0.27e2 * t1799 * t29 * t823 * t621 + 0.640e3 / 0.81e2 * t1812 * t418 + 0.640e3 / 0.81e2 * t1812 * t393 + 0.16e2 / 0.81e2 * t1817 * t1818 * t702 + 0.8e1 / 0.3e1 * t561 * t562 * t1033
  t1833 = t714 * t234
  t1839 = t320 * t18
  t1866 = 0.8e1 / 0.3e1 * t706 * t701 * t692 - 0.208e3 / 0.27e2 * t700 * t707 - 0.8e1 / 0.3e1 * t712 * t1833 * t702 + 0.32e2 / 0.27e2 * t716 * t707 + 0.736e3 / 0.81e2 * t327 * t1839 * t702 - 0.16e2 / 0.3e1 * t561 * t696 * t692 + 0.224e3 / 0.27e2 * t561 * t721 * t507 - 0.560e3 / 0.81e2 * t561 * t329 * params.b * t403 + 0.104e3 / 0.81e2 * t1163 * t1108 + 0.104e3 / 0.81e2 * t1163 * t1112 + 0.116e3 / 0.243e3 * t401 * t1178 * t1140 - 0.10e2 / 0.27e2 * t1167 * t1108 - 0.10e2 / 0.27e2 * t1167 * t1112 - 0.44e2 / 0.27e2 * t1155 * t1174
  t1868 = t1446 * t28 * t25
  t1882 = t320 * t1234
  t1883 = t1882 * t41
  t1891 = t234 * t28 * t25
  t1913 = t320 * t234
  t1914 = t1913 * t41
  t1915 = t327 * t1914
  t1918 = -0.64e2 / 0.81e2 * t417 * t1868 * t1181 + 0.104e3 / 0.81e2 * t1116 * t1158 * t1066 + 0.104e3 / 0.81e2 * t1116 * t1158 * t1071 + 0.232e3 / 0.243e3 * t1081 * t42 * t18 * t1044 + 0.548e3 / 0.243e3 * t1089 * t1883 * t1054 + 0.2e1 / 0.81e2 * t1139 * t1112 + params.b * t1369 * t1891 * t1140 / 0.486e3 + 0.4e1 / 0.243e3 * t1136 * t1868 * t1147 + 0.4e1 / 0.27e2 * t1145 * t1152 + 0.4e1 / 0.27e2 * t1145 * t1174 + 0.4e1 / 0.81e2 * t401 * t1354 * t28 * t25 * t1181 + 0.4e1 / 0.9e1 * t1151 * t1146 * t1212 + 0.8e1 / 0.27e2 * t1258 * t1260 * t1199 + 0.16e2 / 0.27e2 * t1915 * t1171
  t1927 = t1106 * t227
  t1931 = t322 * t312
  t1982 = 0.8e1 / 0.27e2 * t1799 * t401 * t28 * t392 + 0.16e2 / 0.27e2 * t1799 * t1170 * t411 + 0.2e1 / 0.3e1 * t1195 * t1105 * t1927 + 0.2e1 / 0.9e1 * t1195 * t1105 * t1931 + t1131 * t1196 / 0.9e1 + 0.4e1 / 0.9e1 * t1151 * t1146 * t323 + 0.2e1 / 0.3e1 * t1116 * t1117 * t49 * t227 * params.d + 0.2e1 / 0.9e1 * t1116 * t1117 * t114 * t312 * params.d + 0.4e1 / 0.27e2 * t1251 * t1252 * t1070 * t621 + 0.4e1 / 0.81e2 * t29 * t1329 * t31 * params.m2 * t42 * t234 * t1043 * t908 + 0.8e1 / 0.81e2 * t29 * t1249 * t317 * t320 * t1446 * t41 * t1253 + 0.8e1 / 0.27e2 * t1258 * t1260 * t1083 + 0.8e1 / 0.27e2 * t1179 * t1180 * t1111 + 0.16e2 / 0.243e3 * t417 * t1680 * t28 * t25 * t1817 * t1232 * t532
  t2022 = -0.4e1 * t1504
  t2030 = -0.7e1 / 0.48e2 * t57 * t1627 + 0.73304e5 / 0.243e3 * t1681 + t278 * t149 / 0.2e1 + 0.3e1 / 0.4e1 * t201 * t215 - 0.4e1 * t142 * t237 - 0.4e1 / 0.3e1 * t97 * t145 * t251 + t142 * t252 / 0.2e1 + t97 * t98 * t1509 / 0.8e1 + t2022 * s2 * t105 / 0.8e1 + t256 * t156 / 0.2e1 + 0.3e1 / 0.4e1 * t219 * t224
  t2060 = t153 * t275 / 0.2e1 + t103 * t104 * t1556 / 0.8e1 - t2022 * s0 * t99 / 0.8e1 - 0.4e1 / 0.3e1 * t278 * t146 - 0.4e1 * t201 * t212 + 0.44e2 / 0.3e1 * t142 * t287 - 0.616e3 / 0.27e2 * t97 * t308 * t130 + 0.22e2 / 0.3e1 * t201 * t209 - 0.616e3 / 0.27e2 * t142 * t309 + 0.2618e4 / 0.81e2 * t97 * t1575 * t57 * t76 + 0.22e2 / 0.3e1 * t97 * t208 * t186
  t2088 = -0.2e1 / 0.3e1 * t1116 * t1186 * t1119 - 0.4e1 / 0.3e1 * t1116 * t1186 * t1125 - 0.20e2 / 0.27e2 * t1081 * t1095 * t1199 - 0.44e2 / 0.27e2 * t1089 * t331 * t1066 + 0.16e2 / 0.9e1 * t399 * t1170 * t512 - 0.832e3 / 0.243e3 * t319 * t1839 * t532 - 0.16e2 / 0.9e1 * t1221 * t715 * t1107 + t34 * t42 * t232 * (t2030 + t2060) / 0.6e1 + 0.4e1 / 0.9e1 * t319 * t321 * t1931 + 0.4e1 / 0.9e1 * t1221 * t1222 * t323 + 0.4e1 / 0.9e1 * t34 * t42 * t44 * t540 * t108 + 0.8e1 / 0.9e1 * t34 * t42 * t50 * t159 + 0.4e1 / 0.9e1 * t34 * t42 * t115 * t227 + 0.16e2 / 0.81e2 * t1231 * t1235 * t1107
  t2095 = t710 ** 2
  t2099 = t713 ** 2
  t2154 = 0.16e2 / 0.81e2 * t1231 * t1235 * t1111 + 0.8e1 / 0.243e3 * t29 * t32 * t2095 * params.m2 * t2099 * params.omega / t12 / t8 * t532 + 0.638e3 / 0.243e3 * t1221 * t1833 * t532 - 0.56e2 / 0.81e2 * t34 * t42 * t520 * t49 * t108 - 0.56e2 / 0.81e2 * t34 * t42 * t521 * t159 - 0.136e3 / 0.243e3 * t1231 * t1818 * t532 + 0.268e3 / 0.81e2 * t319 * t531 * t1107 + 0.268e3 / 0.81e2 * t319 * t531 * t1111 + 0.140e3 / 0.243e3 * t34 * t42 * t329 * t114 * t108 - 0.2e1 / 0.9e1 * t34 * t42 * t433 * t21 * t108 - 0.2e1 / 0.3e1 * t34 * t42 * t541 * t159 + 0.8e1 / 0.9e1 * t1221 * t1222 * t1216 + t34 * t42 * t4 * t1635 * t108 / 0.6e1 + 0.2e1 / 0.3e1 * t34 * t42 * t551 * t159
  t2156 = t41 * t21 * t108
  t2160 = t1211 * t159
  t2190 = t396 * t397 * t18
  t2199 = 0.4e1 / 0.9e1 * t319 * t321 * t2156 + 0.4e1 / 0.3e1 * t319 * t321 * t2160 + 0.4e1 / 0.9e1 * t1221 * t1222 * t1212 - 0.64e2 / 0.9e1 * t416 * t513 + 0.16e2 / 0.27e2 * t1915 * t412 + 0.8e1 / 0.27e2 * t1915 * t404 + t34 * t42 * t556 * t227 + 0.2e1 / 0.3e1 * t34 * t42 * t164 * t312 + 0.4e1 / 0.3e1 * t319 * t321 * t1927 + 0.8e1 / 0.9e1 * t1151 * t1146 * t1216 + 0.8e1 / 0.27e2 * t1179 * t1180 * t1107 - 0.32e2 / 0.9e1 * t2190 * t1171 - 0.2e1 / 0.3e1 * t1103 * t1196 - 0.100e3 / 0.81e2 * t1116 * t42 * t166 * t1054
  t2206 = t1371 * t25
  t2223 = t714 * t1446
  t2224 = t2223 * t41
  t2245 = -0.100e3 / 0.81e2 * t417 * t1144 * t1140 - 0.44e2 / 0.27e2 * t1155 * t1152 + 0.548e3 / 0.243e3 * t417 * t2206 * t1147 - 0.14e2 / 0.243e3 * t1136 * t2206 * t1140 - 0.10e2 / 0.27e2 * t401 * t1891 * t1147 - 0.2e1 / 0.3e1 * t1103 * t1271 - 0.4e1 / 0.3e1 * t1103 * t1274 - 0.20e2 / 0.27e2 * t1258 * t1914 * t1044 - 0.64e2 / 0.81e2 * t1265 * t2224 * t1054 - 0.28e2 / 0.81e2 * t1251 * t42 * t1234 * t1253 + 0.4e1 / 0.9e1 * t1089 * t1091 * t1207 + 0.2e1 / 0.9e1 * t1131 * t1274 + 0.2e1 / 0.9e1 * t1081 * t1082 * t1118 * t410 + 0.4e1 / 0.9e1 * t1081 * t1082 * t1124 * t410
  t2299 = 0.8e1 / 0.81e2 * t29 * t1079 * t711 * t714 * t1354 * t41 * t1044 + 0.8e1 / 0.27e2 * t1265 * t1267 * t1066 + 0.8e1 / 0.27e2 * t1265 * t1267 * t1071 + 0.16e2 / 0.243e3 * t29 * t1087 * t1229 * t1232 * t1680 * t41 * t1054 + 0.2e1 / 0.9e1 * t1195 * t1105 * t2156 + 0.2e1 / 0.3e1 * t1195 * t1105 * t2160 + t1131 * t1271 / 0.9e1 - 0.2e1 / 0.3e1 * t1116 * t1186 * t1207 - 0.20e2 / 0.27e2 * t1081 * t1095 * t1083 - 0.44e2 / 0.27e2 * t1089 * t331 * t1071 + 0.4e1 / 0.27e2 * t1251 * t1252 * t1065 * t621 + 0.2e1 / 0.81e2 * t1139 * t1108 + 0.2e1 / 0.9e1 * t1116 * t1117 * t21 * t108 * params.d + 0.2e1 / 0.3e1 * t1116 * t1117 * t540 * t159 * params.d
  t2316 = t417 * t234
  t2339 = t28 * t822
  t2350 = 0.4e1 / 0.9e1 * t1089 * t1091 * t1119 + 0.8e1 / 0.9e1 * t1089 * t1091 * t1125 + 0.2e1 / 0.9e1 * t1081 * t1082 * t1206 * t410 - 0.28e2 / 0.81e2 * t417 * t1234 * t1040 * t1045 - 0.20e2 / 0.27e2 * t2316 * t1050 * t1055 + 0.2e1 / 0.9e1 * t1064 * t1042 * t1207 - 0.20e2 / 0.27e2 * t1059 * t1067 - 0.20e2 / 0.27e2 * t1059 * t1072 + 0.2e1 / 0.9e1 * t1064 * t1042 * t1119 + 0.4e1 / 0.9e1 * t1064 * t1042 * t1125 + 0.4e1 / 0.27e2 * t1041 * t1042 * t1199 + 0.4e1 / 0.27e2 * t1041 * t1042 * t1083 + 0.4e1 / 0.81e2 * t2316 * t2339 * t31 * t1042 * t1253 + 0.8e1 / 0.81e2 * t417 * t1446 * t1040 * t1053 * t1044
  t2378 = t327 * t1883
  t2390 = 0.8e1 / 0.27e2 * t1051 * t1053 * t1066 + 0.8e1 / 0.27e2 * t1051 * t1053 * t1071 + 0.8e1 / 0.81e2 * t417 * t1354 * t1050 * t711 * t714 * t41 * t1054 + 0.2e1 / 0.27e2 * t1076 * t1067 + 0.2e1 / 0.27e2 * t1076 * t1072 + 0.2e1 / 0.243e3 * t1136 * t234 * t1050 * t1060 - t6 * t1635 * t25 - 0.16e2 / 0.9e1 * t2190 * t404 - 0.32e2 / 0.9e1 * t2190 * t412 - 0.304e3 / 0.81e2 * t2378 * t418 - 0.304e3 / 0.81e2 * t2378 * t393 + 0.16e2 / 0.9e1 * t332 * t508 - 0.64e2 / 0.9e1 * t416 * t508 + 0.8e1 / 0.3e1 * t424 * t417 * t692
  t2412 = t712 * t2224
  t2440 = 0.8e1 / 0.3e1 * t424 * t29 * t802 * params.d - 0.2e1 / 0.3e1 * t34 * t42 * t546 * t227 - 0.2e1 / 0.9e1 * t34 * t42 * t526 * t312 - 0.14e2 / 0.9e1 * t319 * t705 * t1212 - 0.28e2 / 0.9e1 * t319 * t705 * t1216 + 0.16e2 / 0.9e1 * t332 * t513 + 0.32e2 / 0.81e2 * t2412 * t418 + 0.32e2 / 0.81e2 * t2412 * t393 - 0.8e1 / 0.3e1 * t1282 * t54 * t540 * t833 - 0.16e2 / 0.9e1 * t1277 * t752 * t49 * t833 - 0.32e2 / 0.81e2 * t791 * t2223 * t1279 + 0.64e2 / 0.9e1 * t1282 * t117 * t49 * t833 + 0.32e2 / 0.9e1 * t1282 * t18 * t114 * t829 - 0.640e3 / 0.81e2 * t1282 * t166 * t114 * t833
  t2494 = -0.32e2 / 0.9e1 * t1314 * t1298 - 0.8e1 / 0.9e1 * t727 * t400 * t18 * t1304 + 0.4e1 / 0.3e1 * t1296 * t1049 * t691 * params.d + 0.4e1 / 0.9e1 * t1302 * t1298 + 0.4e1 / 0.81e2 * t727 * t810 * t1234 * t1304 - 0.16e2 / 0.9e1 * t727 * params.c * t18 * t1310 + 0.8e1 / 0.9e1 * t1308 * t1039 * t506 * t410 + 0.8e1 / 0.27e2 * t727 * params.c * t1234 * t2339 * t390 * t621 + 0.4e1 / 0.27e2 * t727 * t400 * t1234 * t1310 - 0.16e2 / 0.9e1 * t1282 * t13 * t49 * t829 - 0.16e2 / 0.27e2 * t1282 * t1234 * t114 * t847 - 0.16e2 / 0.27e2 * t774 * t1913 * t1278 * t829 + 0.320e3 / 0.81e2 * t727 * params.c * t166 * t1304 + 0.304e3 / 0.81e2 * t774 * t1882 * t1279
  d1111 = 0.4e1 * params.a * (t516 + t719 + t797 + t1035 + t1123 + t1184 + t1245 + t1317) + t2 * params.a * (t1382 + t1429 + t1476 + t1825 + t1866 + t1918 + t1982 + t2088 + t2154 + t2199 + t2245 + t2299 + t2350 + t2390 + t2440 + t2494)

  res = {'v4rho4': d1111}
  return res
