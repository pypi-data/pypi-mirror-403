"""Generated from mgga_x_tpss.mpl."""

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
  params_BLOC_a_raw = params.BLOC_a
  if isinstance(params_BLOC_a_raw, (str, bytes, dict)):
    params_BLOC_a = params_BLOC_a_raw
  else:
    try:
      params_BLOC_a_seq = list(params_BLOC_a_raw)
    except TypeError:
      params_BLOC_a = params_BLOC_a_raw
    else:
      params_BLOC_a_seq = np.asarray(params_BLOC_a_seq, dtype=np.float64)
      params_BLOC_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_BLOC_a_seq))
  params_BLOC_b_raw = params.BLOC_b
  if isinstance(params_BLOC_b_raw, (str, bytes, dict)):
    params_BLOC_b = params_BLOC_b_raw
  else:
    try:
      params_BLOC_b_seq = list(params_BLOC_b_raw)
    except TypeError:
      params_BLOC_b = params_BLOC_b_raw
    else:
      params_BLOC_b_seq = np.asarray(params_BLOC_b_seq, dtype=np.float64)
      params_BLOC_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_BLOC_b_seq))
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
  params_e_raw = params.e
  if isinstance(params_e_raw, (str, bytes, dict)):
    params_e = params_e_raw
  else:
    try:
      params_e_seq = list(params_e_raw)
    except TypeError:
      params_e = params_e_raw
    else:
      params_e_seq = np.asarray(params_e_seq, dtype=np.float64)
      params_e = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_seq))
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  tpss_ff = lambda z: params_BLOC_a + params_BLOC_b * z

  tpss_kappa = lambda x=None, t=None: params_kappa

  tpss_p = lambda x: X2S ** 2 * x ** 2

  tpss_z = lambda x, t: x ** 2 / (8 * t)

  tpss_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tpss_fxden = lambda x: (1 + jnp.sqrt(params_e) * tpss_p(x)) ** 2

  tpss_qb = lambda x, t: 9 / 20 * (tpss_alpha(x, t) - 1) / jnp.sqrt(1 + params_b * tpss_alpha(x, t) * (tpss_alpha(x, t) - 1)) + 2 * tpss_p(x) / 3

  tpss_fxnum = lambda x, t: +(MU_GE + params_c * tpss_z(x, t) ** tpss_ff(tpss_z(x, t)) / (1 + tpss_z(x, t) ** 2) ** 2) * tpss_p(x) + 146 / 2025 * tpss_qb(x, t) ** 2 - 73 / 405 * tpss_qb(x, t) * jnp.sqrt(1 / 2 * (9 / 25 * tpss_z(x, t) ** 2 + tpss_p(x) ** 2)) + MU_GE ** 2 / tpss_kappa(x, t) * tpss_p(x) ** 2 + 2 * jnp.sqrt(params_e) * MU_GE * 9 / 25 * tpss_z(x, t) ** 2 + params_e * params_mu * tpss_p(x) ** 3

  tpss_fx = lambda x, t: tpss_fxnum(x, t) / tpss_fxden(x)

  tpss_a1 = lambda x, t: tpss_kappa(x, t) / (tpss_kappa(x, t) + tpss_fx(x, t))

  tpss_f = lambda x, u, t: 1 + tpss_kappa(x, t) * (1 - tpss_a1(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, tpss_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_BLOC_a_raw = params.BLOC_a
  if isinstance(params_BLOC_a_raw, (str, bytes, dict)):
    params_BLOC_a = params_BLOC_a_raw
  else:
    try:
      params_BLOC_a_seq = list(params_BLOC_a_raw)
    except TypeError:
      params_BLOC_a = params_BLOC_a_raw
    else:
      params_BLOC_a_seq = np.asarray(params_BLOC_a_seq, dtype=np.float64)
      params_BLOC_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_BLOC_a_seq))
  params_BLOC_b_raw = params.BLOC_b
  if isinstance(params_BLOC_b_raw, (str, bytes, dict)):
    params_BLOC_b = params_BLOC_b_raw
  else:
    try:
      params_BLOC_b_seq = list(params_BLOC_b_raw)
    except TypeError:
      params_BLOC_b = params_BLOC_b_raw
    else:
      params_BLOC_b_seq = np.asarray(params_BLOC_b_seq, dtype=np.float64)
      params_BLOC_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_BLOC_b_seq))
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
  params_e_raw = params.e
  if isinstance(params_e_raw, (str, bytes, dict)):
    params_e = params_e_raw
  else:
    try:
      params_e_seq = list(params_e_raw)
    except TypeError:
      params_e = params_e_raw
    else:
      params_e_seq = np.asarray(params_e_seq, dtype=np.float64)
      params_e = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_seq))
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  tpss_ff = lambda z: params_BLOC_a + params_BLOC_b * z

  tpss_kappa = lambda x=None, t=None: params_kappa

  tpss_p = lambda x: X2S ** 2 * x ** 2

  tpss_z = lambda x, t: x ** 2 / (8 * t)

  tpss_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tpss_fxden = lambda x: (1 + jnp.sqrt(params_e) * tpss_p(x)) ** 2

  tpss_qb = lambda x, t: 9 / 20 * (tpss_alpha(x, t) - 1) / jnp.sqrt(1 + params_b * tpss_alpha(x, t) * (tpss_alpha(x, t) - 1)) + 2 * tpss_p(x) / 3

  tpss_fxnum = lambda x, t: +(MU_GE + params_c * tpss_z(x, t) ** tpss_ff(tpss_z(x, t)) / (1 + tpss_z(x, t) ** 2) ** 2) * tpss_p(x) + 146 / 2025 * tpss_qb(x, t) ** 2 - 73 / 405 * tpss_qb(x, t) * jnp.sqrt(1 / 2 * (9 / 25 * tpss_z(x, t) ** 2 + tpss_p(x) ** 2)) + MU_GE ** 2 / tpss_kappa(x, t) * tpss_p(x) ** 2 + 2 * jnp.sqrt(params_e) * MU_GE * 9 / 25 * tpss_z(x, t) ** 2 + params_e * params_mu * tpss_p(x) ** 3

  tpss_fx = lambda x, t: tpss_fxnum(x, t) / tpss_fxden(x)

  tpss_a1 = lambda x, t: tpss_kappa(x, t) / (tpss_kappa(x, t) + tpss_fx(x, t))

  tpss_f = lambda x, u, t: 1 + tpss_kappa(x, t) * (1 - tpss_a1(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, tpss_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_BLOC_a_raw = params.BLOC_a
  if isinstance(params_BLOC_a_raw, (str, bytes, dict)):
    params_BLOC_a = params_BLOC_a_raw
  else:
    try:
      params_BLOC_a_seq = list(params_BLOC_a_raw)
    except TypeError:
      params_BLOC_a = params_BLOC_a_raw
    else:
      params_BLOC_a_seq = np.asarray(params_BLOC_a_seq, dtype=np.float64)
      params_BLOC_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_BLOC_a_seq))
  params_BLOC_b_raw = params.BLOC_b
  if isinstance(params_BLOC_b_raw, (str, bytes, dict)):
    params_BLOC_b = params_BLOC_b_raw
  else:
    try:
      params_BLOC_b_seq = list(params_BLOC_b_raw)
    except TypeError:
      params_BLOC_b = params_BLOC_b_raw
    else:
      params_BLOC_b_seq = np.asarray(params_BLOC_b_seq, dtype=np.float64)
      params_BLOC_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_BLOC_b_seq))
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
  params_e_raw = params.e
  if isinstance(params_e_raw, (str, bytes, dict)):
    params_e = params_e_raw
  else:
    try:
      params_e_seq = list(params_e_raw)
    except TypeError:
      params_e = params_e_raw
    else:
      params_e_seq = np.asarray(params_e_seq, dtype=np.float64)
      params_e = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_seq))
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  tpss_ff = lambda z: params_BLOC_a + params_BLOC_b * z

  tpss_kappa = lambda x=None, t=None: params_kappa

  tpss_p = lambda x: X2S ** 2 * x ** 2

  tpss_z = lambda x, t: x ** 2 / (8 * t)

  tpss_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tpss_fxden = lambda x: (1 + jnp.sqrt(params_e) * tpss_p(x)) ** 2

  tpss_qb = lambda x, t: 9 / 20 * (tpss_alpha(x, t) - 1) / jnp.sqrt(1 + params_b * tpss_alpha(x, t) * (tpss_alpha(x, t) - 1)) + 2 * tpss_p(x) / 3

  tpss_fxnum = lambda x, t: +(MU_GE + params_c * tpss_z(x, t) ** tpss_ff(tpss_z(x, t)) / (1 + tpss_z(x, t) ** 2) ** 2) * tpss_p(x) + 146 / 2025 * tpss_qb(x, t) ** 2 - 73 / 405 * tpss_qb(x, t) * jnp.sqrt(1 / 2 * (9 / 25 * tpss_z(x, t) ** 2 + tpss_p(x) ** 2)) + MU_GE ** 2 / tpss_kappa(x, t) * tpss_p(x) ** 2 + 2 * jnp.sqrt(params_e) * MU_GE * 9 / 25 * tpss_z(x, t) ** 2 + params_e * params_mu * tpss_p(x) ** 3

  tpss_fx = lambda x, t: tpss_fxnum(x, t) / tpss_fxden(x)

  tpss_a1 = lambda x, t: tpss_kappa(x, t) / (tpss_kappa(x, t) + tpss_fx(x, t))

  tpss_f = lambda x, u, t: 1 + tpss_kappa(x, t) * (1 - tpss_a1(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, tpss_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
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
  t26 = t6 ** (0.1e1 / 0.3e1)
  t27 = t25 * t26
  t28 = 0.1e1 / r0
  t30 = 0.1e1 / tau0
  t32 = s0 * t28 * t30 / 0.8e1
  t33 = params.BLOC_b * s0
  t37 = params.BLOC_a + t33 * t28 * t30 / 0.8e1
  t38 = t32 ** t37
  t39 = params.c * t38
  t40 = s0 ** 2
  t41 = r0 ** 2
  t42 = 0.1e1 / t41
  t43 = t40 * t42
  t44 = tau0 ** 2
  t45 = 0.1e1 / t44
  t46 = t43 * t45
  t48 = 0.1e1 + t46 / 0.64e2
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t53 = 6 ** (0.1e1 / 0.3e1)
  t54 = (0.10e2 / 0.81e2 + t39 * t50) * t53
  t55 = jnp.pi ** 2
  t56 = t55 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t58 = 0.1e1 / t57
  t59 = t58 * s0
  t60 = r0 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t63 = 0.1e1 / t61 / t41
  t64 = t59 * t63
  t68 = 0.1e1 / t61 / r0
  t70 = s0 * t63
  t72 = tau0 * t68 - t70 / 0.8e1
  t74 = t72 * t53 * t58
  t76 = t74 / 0.4e1 - 0.9e1 / 0.20e2
  t77 = params.b * t72
  t78 = t53 * t58
  t81 = t78 * (0.5e1 / 0.9e1 * t74 - 0.1e1)
  t84 = 0.5e1 * t77 * t81 + 0.9e1
  t85 = jnp.sqrt(t84)
  t86 = 0.1e1 / t85
  t87 = t76 * t86
  t89 = t78 * t70
  t91 = 0.3e1 * t87 + t89 / 0.36e2
  t92 = t91 ** 2
  t96 = 0.73e2 / 0.135e3 * t87 + 0.73e2 / 0.14580e5 * t89
  t98 = t53 ** 2
  t100 = 0.1e1 / t56 / t55
  t101 = t98 * t100
  t102 = t41 ** 2
  t105 = 0.1e1 / t60 / t102 / r0
  t110 = jnp.sqrt(0.50e2 * t101 * t40 * t105 + 0.162e3 * t46)
  t114 = 0.1e1 / params.kappa * t98
  t115 = t100 * t40
  t119 = jnp.sqrt(params.e)
  t120 = t119 * t40
  t121 = t42 * t45
  t124 = params.e * params.mu
  t125 = t55 ** 2
  t126 = 0.1e1 / t125
  t128 = t126 * t40 * s0
  t129 = t102 ** 2
  t130 = 0.1e1 / t129
  t134 = t54 * t64 / 0.24e2 + 0.146e3 / 0.2025e4 * t92 - t96 * t110 / 0.240e3 + 0.25e2 / 0.944784e6 * t114 * t115 * t105 + t120 * t121 / 0.720e3 + t124 * t128 * t130 / 0.2304e4
  t135 = t119 * t53
  t138 = 0.1e1 + t135 * t64 / 0.24e2
  t139 = t138 ** 2
  t140 = 0.1e1 / t139
  t142 = t134 * t140 + params.kappa
  t147 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t142)
  t151 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t147)
  t152 = r1 <= f.p.dens_threshold
  t153 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t154 = 0.1e1 + t153
  t155 = t154 <= f.p.zeta_threshold
  t156 = t154 ** (0.1e1 / 0.3e1)
  t158 = f.my_piecewise3(t155, t22, t156 * t154)
  t159 = t158 * t26
  t160 = 0.1e1 / r1
  t162 = 0.1e1 / tau1
  t164 = s2 * t160 * t162 / 0.8e1
  t165 = params.BLOC_b * s2
  t169 = params.BLOC_a + t165 * t160 * t162 / 0.8e1
  t170 = t164 ** t169
  t171 = params.c * t170
  t172 = s2 ** 2
  t173 = r1 ** 2
  t174 = 0.1e1 / t173
  t175 = t172 * t174
  t176 = tau1 ** 2
  t177 = 0.1e1 / t176
  t178 = t175 * t177
  t180 = 0.1e1 + t178 / 0.64e2
  t181 = t180 ** 2
  t182 = 0.1e1 / t181
  t185 = (0.10e2 / 0.81e2 + t171 * t182) * t53
  t186 = t58 * s2
  t187 = r1 ** (0.1e1 / 0.3e1)
  t188 = t187 ** 2
  t190 = 0.1e1 / t188 / t173
  t191 = t186 * t190
  t195 = 0.1e1 / t188 / r1
  t197 = s2 * t190
  t199 = tau1 * t195 - t197 / 0.8e1
  t201 = t199 * t53 * t58
  t203 = t201 / 0.4e1 - 0.9e1 / 0.20e2
  t204 = params.b * t199
  t207 = t78 * (0.5e1 / 0.9e1 * t201 - 0.1e1)
  t210 = 0.5e1 * t204 * t207 + 0.9e1
  t211 = jnp.sqrt(t210)
  t212 = 0.1e1 / t211
  t213 = t203 * t212
  t215 = t78 * t197
  t217 = 0.3e1 * t213 + t215 / 0.36e2
  t218 = t217 ** 2
  t222 = 0.73e2 / 0.135e3 * t213 + 0.73e2 / 0.14580e5 * t215
  t224 = t173 ** 2
  t227 = 0.1e1 / t187 / t224 / r1
  t232 = jnp.sqrt(0.50e2 * t101 * t172 * t227 + 0.162e3 * t178)
  t235 = t100 * t172
  t239 = t119 * t172
  t240 = t174 * t177
  t244 = t126 * t172 * s2
  t245 = t224 ** 2
  t246 = 0.1e1 / t245
  t250 = t185 * t191 / 0.24e2 + 0.146e3 / 0.2025e4 * t218 - t222 * t232 / 0.240e3 + 0.25e2 / 0.944784e6 * t114 * t235 * t227 + t239 * t240 / 0.720e3 + t124 * t244 * t246 / 0.2304e4
  t253 = 0.1e1 + t135 * t191 / 0.24e2
  t254 = t253 ** 2
  t255 = 0.1e1 / t254
  t257 = t250 * t255 + params.kappa
  t262 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t257)
  t266 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t5 * t159 * t262)
  t267 = t6 ** 2
  t269 = t16 / t267
  t270 = t7 - t269
  t271 = f.my_piecewise5(t10, 0, t14, 0, t270)
  t274 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t271)
  t279 = t26 ** 2
  t280 = 0.1e1 / t279
  t284 = t5 * t25 * t280 * t147 / 0.8e1
  t285 = t5 * t25
  t286 = params.kappa ** 2
  t287 = t26 * t286
  t288 = t142 ** 2
  t289 = 0.1e1 / t288
  t291 = jnp.log(t32)
  t301 = t39 / t49 / t48
  t302 = t41 * r0
  t303 = 0.1e1 / t302
  t305 = t40 * t303 * t45
  t313 = 0.1e1 / t61 / t302
  t319 = s0 * t313
  t321 = -0.5e1 / 0.3e1 * tau0 * t63 + t319 / 0.3e1
  t323 = t58 * t86
  t324 = t321 * t53 * t323
  t328 = t76 / t85 / t84
  t336 = t328 * (0.5e1 * params.b * t321 * t81 + 0.25e2 / 0.9e1 * t77 * t101 * t321)
  t338 = t78 * t319
  t350 = t96 / t110
  t354 = 0.1e1 / t60 / t102 / t41
  t377 = t134 / t139 / t138 * t119
  t386 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t274 * t26 * t147 - t284 - 0.3e1 / 0.8e1 * t285 * t287 * t289 * (((t39 * (-t33 * t42 * t30 * t291 / 0.8e1 - t37 * t28) * t50 + t301 * t305 / 0.16e2) * t53 * t64 / 0.24e2 - t54 * t59 * t313 / 0.9e1 + 0.292e3 / 0.2025e4 * t91 * (0.3e1 / 0.4e1 * t324 - 0.3e1 / 0.2e1 * t336 - 0.2e1 / 0.27e2 * t338) - (0.73e2 / 0.540e3 * t324 - 0.73e2 / 0.270e3 * t336 - 0.146e3 / 0.10935e5 * t338) * t110 / 0.240e3 - t350 * (-0.324e3 * t305 - 0.800e3 / 0.3e1 * t101 * t40 * t354) / 0.480e3 - 0.25e2 / 0.177147e6 * t114 * t115 * t354 - t120 * t303 * t45 / 0.360e3 - t124 * t128 / t129 / r0 / 0.288e3) * t140 + 0.2e1 / 0.9e1 * t377 * t338))
  t388 = f.my_piecewise5(t14, 0, t10, 0, -t270)
  t391 = f.my_piecewise3(t155, 0, 0.4e1 / 0.3e1 * t156 * t388)
  t399 = t5 * t158 * t280 * t262 / 0.8e1
  t401 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t5 * t391 * t26 * t262 - t399)
  vrho_0_ = t151 + t266 + t6 * (t386 + t401)
  t404 = -t7 - t269
  t405 = f.my_piecewise5(t10, 0, t14, 0, t404)
  t408 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t405)
  t414 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t408 * t26 * t147 - t284)
  t416 = f.my_piecewise5(t14, 0, t10, 0, -t404)
  t419 = f.my_piecewise3(t155, 0, 0.4e1 / 0.3e1 * t156 * t416)
  t424 = t5 * t158
  t425 = t257 ** 2
  t426 = 0.1e1 / t425
  t428 = jnp.log(t164)
  t438 = t171 / t181 / t180
  t439 = t173 * r1
  t440 = 0.1e1 / t439
  t442 = t172 * t440 * t177
  t450 = 0.1e1 / t188 / t439
  t456 = s2 * t450
  t458 = -0.5e1 / 0.3e1 * tau1 * t190 + t456 / 0.3e1
  t460 = t58 * t212
  t461 = t458 * t53 * t460
  t465 = t203 / t211 / t210
  t473 = t465 * (0.5e1 * params.b * t458 * t207 + 0.25e2 / 0.9e1 * t204 * t101 * t458)
  t475 = t78 * t456
  t487 = t222 / t232
  t491 = 0.1e1 / t187 / t224 / t173
  t514 = t250 / t254 / t253 * t119
  t523 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t5 * t419 * t26 * t262 - t399 - 0.3e1 / 0.8e1 * t424 * t287 * t426 * (((t171 * (-t165 * t174 * t162 * t428 / 0.8e1 - t169 * t160) * t182 + t438 * t442 / 0.16e2) * t53 * t191 / 0.24e2 - t185 * t186 * t450 / 0.9e1 + 0.292e3 / 0.2025e4 * t217 * (0.3e1 / 0.4e1 * t461 - 0.3e1 / 0.2e1 * t473 - 0.2e1 / 0.27e2 * t475) - (0.73e2 / 0.540e3 * t461 - 0.73e2 / 0.270e3 * t473 - 0.146e3 / 0.10935e5 * t475) * t232 / 0.240e3 - t487 * (-0.324e3 * t442 - 0.800e3 / 0.3e1 * t101 * t172 * t491) / 0.480e3 - 0.25e2 / 0.177147e6 * t114 * t235 * t491 - t239 * t440 * t177 / 0.360e3 - t124 * t244 / t245 / r1 / 0.288e3) * t255 + 0.2e1 / 0.9e1 * t514 * t475))
  vrho_1_ = t151 + t266 + t6 * (t414 + t523)
  t536 = s0 * t42 * t45
  t546 = t63 * t53
  t547 = t546 * t323
  t556 = t328 * (-0.5e1 / 0.8e1 * params.b * t63 * t81 - 0.25e2 / 0.72e2 * t77 * t101 * t63)
  t558 = t546 * t58
  t596 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t285 * t287 * t289 * (((t39 * (params.BLOC_b * t28 * t30 * t291 / 0.8e1 + t37 / s0) * t50 - t301 * t536 / 0.16e2) * t53 * t64 / 0.24e2 + t54 * t58 * t63 / 0.24e2 + 0.292e3 / 0.2025e4 * t91 * (-0.3e1 / 0.32e2 * t547 - 0.3e1 / 0.2e1 * t556 + t558 / 0.36e2) - (-0.73e2 / 0.4320e4 * t547 - 0.73e2 / 0.270e3 * t556 + 0.73e2 / 0.14580e5 * t558) * t110 / 0.240e3 - t350 * (0.100e3 * t101 * s0 * t105 + 0.324e3 * t536) / 0.480e3 + 0.25e2 / 0.472392e6 * t114 * t100 * s0 * t105 + t119 * s0 * t121 / 0.360e3 + t124 * t126 * t40 * t130 / 0.768e3) * t140 - t377 * t558 / 0.12e2))
  vsigma_0_ = t6 * t596
  vsigma_1_ = 0.0e0
  t607 = s2 * t174 * t177
  t617 = t190 * t53
  t618 = t617 * t460
  t627 = t465 * (-0.5e1 / 0.8e1 * params.b * t190 * t207 - 0.25e2 / 0.72e2 * t204 * t101 * t190)
  t629 = t617 * t58
  t667 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t424 * t287 * t426 * (((t171 * (params.BLOC_b * t160 * t162 * t428 / 0.8e1 + t169 / s2) * t182 - t438 * t607 / 0.16e2) * t53 * t191 / 0.24e2 + t185 * t58 * t190 / 0.24e2 + 0.292e3 / 0.2025e4 * t217 * (-0.3e1 / 0.32e2 * t618 - 0.3e1 / 0.2e1 * t627 + t629 / 0.36e2) - (-0.73e2 / 0.4320e4 * t618 - 0.73e2 / 0.270e3 * t627 + 0.73e2 / 0.14580e5 * t629) * t232 / 0.240e3 - t487 * (0.100e3 * t101 * s2 * t227 + 0.324e3 * t607) / 0.480e3 + 0.25e2 / 0.472392e6 * t114 * t100 * s2 * t227 + t119 * s2 * t240 / 0.360e3 + t124 * t126 * t172 * t246 / 0.768e3) * t255 - t514 * t629 / 0.12e2))
  vsigma_2_ = t6 * t667
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t679 = 0.1e1 / t44 / tau0
  t680 = t43 * t679
  t688 = t68 * t53 * t323
  t697 = t328 * (0.5e1 * params.b * t68 * t81 + 0.25e2 / 0.9e1 * t77 * t101 * t68)
  t717 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t286 * t289 * ((t39 * (-t33 * t28 * t45 * t291 / 0.8e1 - t37 * t30) * t50 + t301 * t680 / 0.16e2) * t53 * t64 / 0.24e2 + 0.292e3 / 0.2025e4 * t91 * (0.3e1 / 0.4e1 * t688 - 0.3e1 / 0.2e1 * t697) - (0.73e2 / 0.540e3 * t688 - 0.73e2 / 0.270e3 * t697) * t110 / 0.240e3 + 0.27e2 / 0.40e2 * t350 * t680 - t120 * t42 * t679 / 0.360e3) * t140)
  vtau_0_ = t6 * t717
  t729 = 0.1e1 / t176 / tau1
  t730 = t175 * t729
  t738 = t195 * t53 * t460
  t747 = t465 * (0.5e1 * params.b * t195 * t207 + 0.25e2 / 0.9e1 * t204 * t101 * t195)
  t767 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t5 * t159 * t286 * t426 * ((t171 * (-t165 * t160 * t177 * t428 / 0.8e1 - t169 * t162) * t182 + t438 * t730 / 0.16e2) * t53 * t191 / 0.24e2 + 0.292e3 / 0.2025e4 * t217 * (0.3e1 / 0.4e1 * t738 - 0.3e1 / 0.2e1 * t747) - (0.73e2 / 0.540e3 * t738 - 0.73e2 / 0.270e3 * t747) * t232 / 0.240e3 + 0.27e2 / 0.40e2 * t487 * t730 - t239 * t174 * t729 / 0.360e3) * t255)
  vtau_1_ = t6 * t767
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
  params_BLOC_a_raw = params.BLOC_a
  if isinstance(params_BLOC_a_raw, (str, bytes, dict)):
    params_BLOC_a = params_BLOC_a_raw
  else:
    try:
      params_BLOC_a_seq = list(params_BLOC_a_raw)
    except TypeError:
      params_BLOC_a = params_BLOC_a_raw
    else:
      params_BLOC_a_seq = np.asarray(params_BLOC_a_seq, dtype=np.float64)
      params_BLOC_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_BLOC_a_seq))
  params_BLOC_b_raw = params.BLOC_b
  if isinstance(params_BLOC_b_raw, (str, bytes, dict)):
    params_BLOC_b = params_BLOC_b_raw
  else:
    try:
      params_BLOC_b_seq = list(params_BLOC_b_raw)
    except TypeError:
      params_BLOC_b = params_BLOC_b_raw
    else:
      params_BLOC_b_seq = np.asarray(params_BLOC_b_seq, dtype=np.float64)
      params_BLOC_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_BLOC_b_seq))
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
  params_e_raw = params.e
  if isinstance(params_e_raw, (str, bytes, dict)):
    params_e = params_e_raw
  else:
    try:
      params_e_seq = list(params_e_raw)
    except TypeError:
      params_e = params_e_raw
    else:
      params_e_seq = np.asarray(params_e_seq, dtype=np.float64)
      params_e = np.concatenate((np.array([np.nan], dtype=np.float64), params_e_seq))
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  tpss_ff = lambda z: params_BLOC_a + params_BLOC_b * z

  tpss_kappa = lambda x=None, t=None: params_kappa

  tpss_p = lambda x: X2S ** 2 * x ** 2

  tpss_z = lambda x, t: x ** 2 / (8 * t)

  tpss_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tpss_fxden = lambda x: (1 + jnp.sqrt(params_e) * tpss_p(x)) ** 2

  tpss_qb = lambda x, t: 9 / 20 * (tpss_alpha(x, t) - 1) / jnp.sqrt(1 + params_b * tpss_alpha(x, t) * (tpss_alpha(x, t) - 1)) + 2 * tpss_p(x) / 3

  tpss_fxnum = lambda x, t: +(MU_GE + params_c * tpss_z(x, t) ** tpss_ff(tpss_z(x, t)) / (1 + tpss_z(x, t) ** 2) ** 2) * tpss_p(x) + 146 / 2025 * tpss_qb(x, t) ** 2 - 73 / 405 * tpss_qb(x, t) * jnp.sqrt(1 / 2 * (9 / 25 * tpss_z(x, t) ** 2 + tpss_p(x) ** 2)) + MU_GE ** 2 / tpss_kappa(x, t) * tpss_p(x) ** 2 + 2 * jnp.sqrt(params_e) * MU_GE * 9 / 25 * tpss_z(x, t) ** 2 + params_e * params_mu * tpss_p(x) ** 3

  tpss_fx = lambda x, t: tpss_fxnum(x, t) / tpss_fxden(x)

  tpss_a1 = lambda x, t: tpss_kappa(x, t) / (tpss_kappa(x, t) + tpss_fx(x, t))

  tpss_f = lambda x, u, t: 1 + tpss_kappa(x, t) * (1 - tpss_a1(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, tpss_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t17 * t18
  t20 = 0.1e1 / r0
  t22 = 0.1e1 / tau0
  t24 = s0 * t20 * t22 / 0.8e1
  t25 = params.BLOC_b * s0
  t29 = params.BLOC_a + t25 * t20 * t22 / 0.8e1
  t30 = t24 ** t29
  t31 = params.c * t30
  t32 = s0 ** 2
  t33 = r0 ** 2
  t34 = 0.1e1 / t33
  t35 = t32 * t34
  t36 = tau0 ** 2
  t37 = 0.1e1 / t36
  t38 = t35 * t37
  t40 = 0.1e1 + t38 / 0.64e2
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t45 = 6 ** (0.1e1 / 0.3e1)
  t46 = (0.10e2 / 0.81e2 + t31 * t42) * t45
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t51 = t46 * t50
  t52 = 2 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t54 = s0 * t53
  t55 = t18 ** 2
  t57 = 0.1e1 / t55 / t33
  t58 = t54 * t57
  t61 = tau0 * t53
  t63 = 0.1e1 / t55 / r0
  t66 = t61 * t63 - t58 / 0.8e1
  t68 = t66 * t45 * t50
  t70 = t68 / 0.4e1 - 0.9e1 / 0.20e2
  t71 = params.b * t66
  t72 = t45 * t50
  t75 = t72 * (0.5e1 / 0.9e1 * t68 - 0.1e1)
  t78 = 0.5e1 * t71 * t75 + 0.9e1
  t79 = jnp.sqrt(t78)
  t80 = 0.1e1 / t79
  t81 = t70 * t80
  t83 = t72 * t58
  t85 = 0.3e1 * t81 + t83 / 0.36e2
  t86 = t85 ** 2
  t90 = 0.73e2 / 0.135e3 * t81 + 0.73e2 / 0.14580e5 * t83
  t92 = t45 ** 2
  t94 = 0.1e1 / t48 / t47
  t95 = t92 * t94
  t96 = t32 * t52
  t97 = t33 ** 2
  t100 = 0.1e1 / t18 / t97 / r0
  t101 = t96 * t100
  t105 = jnp.sqrt(0.100e3 * t95 * t101 + 0.162e3 * t38)
  t110 = 0.1e1 / params.kappa * t92 * t94
  t113 = jnp.sqrt(params.e)
  t114 = t113 * t32
  t115 = t34 * t37
  t118 = params.e * params.mu
  t119 = t47 ** 2
  t120 = 0.1e1 / t119
  t122 = t120 * t32 * s0
  t123 = t97 ** 2
  t124 = 0.1e1 / t123
  t128 = t51 * t58 / 0.24e2 + 0.146e3 / 0.2025e4 * t86 - t90 * t105 / 0.240e3 + 0.25e2 / 0.472392e6 * t110 * t101 + t114 * t115 / 0.720e3 + t118 * t122 * t124 / 0.576e3
  t129 = t113 * t45
  t133 = 0.1e1 + t129 * t50 * t58 / 0.24e2
  t134 = t133 ** 2
  t135 = 0.1e1 / t134
  t137 = t128 * t135 + params.kappa
  t142 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t137)
  t146 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t142)
  t152 = t6 * t17
  t153 = params.kappa ** 2
  t154 = t18 * t153
  t155 = t137 ** 2
  t156 = 0.1e1 / t155
  t158 = jnp.log(t24)
  t168 = t31 / t41 / t40
  t169 = t33 * r0
  t170 = 0.1e1 / t169
  t172 = t32 * t170 * t37
  t181 = 0.1e1 / t55 / t169
  t182 = t54 * t181
  t188 = -0.5e1 / 0.3e1 * t61 * t57 + t182 / 0.3e1
  t191 = t188 * t45 * t50 * t80
  t195 = t70 / t79 / t78
  t203 = t195 * (0.5e1 * params.b * t188 * t75 + 0.25e2 / 0.9e1 * t71 * t95 * t188)
  t205 = t72 * t182
  t217 = t90 / t105
  t222 = t96 / t18 / t97 / t33
  t242 = t128 / t134 / t133
  t255 = f.my_piecewise3(t2, 0, -t6 * t17 / t55 * t142 / 0.8e1 - 0.3e1 / 0.8e1 * t152 * t154 * t156 * (((t31 * (-t25 * t34 * t22 * t158 / 0.8e1 - t29 * t20) * t42 + t168 * t172 / 0.16e2) * t45 * t50 * t58 / 0.24e2 - t51 * t182 / 0.9e1 + 0.292e3 / 0.2025e4 * t85 * (0.3e1 / 0.4e1 * t191 - 0.3e1 / 0.2e1 * t203 - 0.2e1 / 0.27e2 * t205) - (0.73e2 / 0.540e3 * t191 - 0.73e2 / 0.270e3 * t203 - 0.146e3 / 0.10935e5 * t205) * t105 / 0.240e3 - t217 * (-0.324e3 * t172 - 0.1600e4 / 0.3e1 * t95 * t222) / 0.480e3 - 0.50e2 / 0.177147e6 * t110 * t222 - t114 * t170 * t37 / 0.360e3 - t118 * t122 / t123 / r0 / 0.72e2) * t135 + 0.2e1 / 0.9e1 * t242 * t129 * t50 * s0 * t53 * t181))
  vrho_0_ = 0.2e1 * r0 * t255 + 0.2e1 * t146
  t268 = s0 * t34 * t37
  t280 = t53 * t57
  t281 = t72 * t80
  t282 = t280 * t281
  t284 = params.b * t53
  t288 = t71 * t92
  t289 = t94 * t53
  t294 = t195 * (-0.5e1 / 0.8e1 * t284 * t57 * t75 - 0.25e2 / 0.72e2 * t288 * t289 * t57)
  t296 = t280 * t72
  t309 = s0 * t52 * t100
  t334 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t152 * t154 * t156 * (((t31 * (params.BLOC_b * t20 * t22 * t158 / 0.8e1 + t29 / s0) * t42 - t168 * t268 / 0.16e2) * t45 * t50 * t58 / 0.24e2 + t46 * t50 * t53 * t57 / 0.24e2 + 0.292e3 / 0.2025e4 * t85 * (-0.3e1 / 0.32e2 * t282 - 0.3e1 / 0.2e1 * t294 + t296 / 0.36e2) - (-0.73e2 / 0.4320e4 * t282 - 0.73e2 / 0.270e3 * t294 + 0.73e2 / 0.14580e5 * t296) * t105 / 0.240e3 - t217 * (0.200e3 * t95 * t309 + 0.324e3 * t268) / 0.480e3 + 0.25e2 / 0.236196e6 * t110 * t309 + t113 * s0 * t115 / 0.360e3 + t118 * t120 * t32 * t124 / 0.192e3) * t135 - t242 * t113 * t296 / 0.12e2))
  vsigma_0_ = 0.2e1 * r0 * t334
  vlapl_0_ = 0.0e0
  t347 = 0.1e1 / t36 / tau0
  t348 = t35 * t347
  t357 = t53 * t63 * t281
  t366 = t195 * (0.5e1 * t284 * t63 * t75 + 0.25e2 / 0.9e1 * t288 * t289 * t63)
  t386 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t153 * t156 * ((t31 * (-t25 * t20 * t37 * t158 / 0.8e1 - t29 * t22) * t42 + t168 * t348 / 0.16e2) * t45 * t50 * t58 / 0.24e2 + 0.292e3 / 0.2025e4 * t85 * (0.3e1 / 0.4e1 * t357 - 0.3e1 / 0.2e1 * t366) - (0.73e2 / 0.540e3 * t357 - 0.73e2 / 0.270e3 * t366) * t105 / 0.240e3 + 0.27e2 / 0.40e2 * t217 * t348 - t114 * t34 * t347 / 0.360e3) * t135)
  vtau_0_ = 0.2e1 * r0 * t386
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
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t20 = 0.1e1 / t19
  t22 = 0.1e1 / r0
  t24 = 0.1e1 / tau0
  t26 = s0 * t22 * t24 / 0.8e1
  t27 = params.BLOC_b * s0
  t31 = params.BLOC_a + t27 * t22 * t24 / 0.8e1
  t32 = t26 ** t31
  t33 = params.c * t32
  t34 = s0 ** 2
  t35 = r0 ** 2
  t36 = 0.1e1 / t35
  t38 = tau0 ** 2
  t39 = 0.1e1 / t38
  t40 = t34 * t36 * t39
  t42 = 0.1e1 + t40 / 0.64e2
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t47 = 6 ** (0.1e1 / 0.3e1)
  t49 = jnp.pi ** 2
  t50 = t49 ** (0.1e1 / 0.3e1)
  t51 = t50 ** 2
  t52 = 0.1e1 / t51
  t53 = (0.10e2 / 0.81e2 + t33 * t44) * t47 * t52
  t54 = 2 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t56 = s0 * t55
  t58 = 0.1e1 / t19 / t35
  t59 = t56 * t58
  t62 = tau0 * t55
  t64 = 0.1e1 / t19 / r0
  t67 = t62 * t64 - t59 / 0.8e1
  t71 = 0.5e1 / 0.9e1 * t67 * t47 * t52 - 0.1e1
  t72 = params.b * t67
  t73 = t47 * t52
  t74 = t73 * t71
  t77 = 0.5e1 * t72 * t74 + 0.9e1
  t78 = jnp.sqrt(t77)
  t79 = 0.1e1 / t78
  t84 = 0.27e2 / 0.20e2 * t71 * t79 + t73 * t59 / 0.36e2
  t85 = t84 ** 2
  t88 = t47 ** 2
  t90 = 0.1e1 / t50 / t49
  t91 = t88 * t90
  t92 = t34 * t54
  t93 = t35 ** 2
  t97 = t92 / t18 / t93 / r0
  t100 = 0.100e3 * t91 * t97 + 0.162e3 * t40
  t101 = jnp.sqrt(t100)
  t106 = 0.1e1 / params.kappa * t88 * t90
  t109 = jnp.sqrt(params.e)
  t110 = t109 * t34
  t114 = params.e * params.mu
  t115 = t49 ** 2
  t118 = 0.1e1 / t115 * t34 * s0
  t119 = t93 ** 2
  t124 = t53 * t59 / 0.24e2 + 0.146e3 / 0.2025e4 * t85 - 0.73e2 / 0.97200e5 * t84 * t101 + 0.25e2 / 0.472392e6 * t106 * t97 + t110 * t36 * t39 / 0.720e3 + t114 * t118 / t119 / 0.576e3
  t125 = t109 * t47
  t129 = 0.1e1 + t125 * t52 * t59 / 0.24e2
  t130 = t129 ** 2
  t131 = 0.1e1 / t130
  t133 = t124 * t131 + params.kappa
  t138 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t133)
  t142 = t6 * t17
  t143 = params.kappa ** 2
  t144 = t18 * t143
  t145 = t133 ** 2
  t146 = 0.1e1 / t145
  t148 = jnp.log(t26)
  t153 = -t27 * t36 * t24 * t148 / 0.8e1 - t31 * t22
  t157 = 0.1e1 / t43 / t42
  t158 = t33 * t157
  t159 = t35 * r0
  t160 = 0.1e1 / t159
  t162 = t34 * t160 * t39
  t167 = (t33 * t153 * t44 + t158 * t162 / 0.16e2) * t47 * t52
  t171 = 0.1e1 / t19 / t159
  t172 = t56 * t171
  t178 = -0.5e1 / 0.3e1 * t62 * t58 + t172 / 0.3e1
  t179 = t178 * t47
  t180 = t52 * t79
  t184 = 0.1e1 / t78 / t77
  t185 = t71 * t184
  t192 = 0.5e1 * params.b * t178 * t74 + 0.25e2 / 0.9e1 * t72 * t91 * t178
  t197 = 0.3e1 / 0.4e1 * t179 * t180 - 0.27e2 / 0.40e2 * t185 * t192 - 0.2e1 / 0.27e2 * t73 * t172
  t202 = 0.1e1 / t101
  t203 = t84 * t202
  t205 = t93 * t35
  t208 = t92 / t18 / t205
  t211 = -0.324e3 * t162 - 0.1600e4 / 0.3e1 * t91 * t208
  t216 = t160 * t39
  t224 = t167 * t59 / 0.24e2 - t53 * t172 / 0.9e1 + 0.292e3 / 0.2025e4 * t84 * t197 - 0.73e2 / 0.97200e5 * t197 * t101 - 0.73e2 / 0.194400e6 * t203 * t211 - 0.50e2 / 0.177147e6 * t106 * t208 - t110 * t216 / 0.360e3 - t114 * t118 / t119 / r0 / 0.72e2
  t227 = 0.1e1 / t130 / t129
  t229 = t124 * t227 * t125
  t230 = t52 * s0
  t232 = t230 * t55 * t171
  t235 = t224 * t131 + 0.2e1 / 0.9e1 * t229 * t232
  t236 = t146 * t235
  t241 = f.my_piecewise3(t2, 0, -t6 * t17 * t20 * t138 / 0.8e1 - 0.3e1 / 0.8e1 * t142 * t144 * t236)
  t253 = t235 ** 2
  t258 = t153 ** 2
  t261 = t160 * t24
  t276 = t43 ** 2
  t279 = t34 ** 2
  t282 = t38 ** 2
  t287 = 0.1e1 / t93
  t289 = t34 * t287 * t39
  t300 = 0.1e1 / t19 / t93
  t301 = t56 * t300
  t304 = t197 ** 2
  t309 = 0.40e2 / 0.9e1 * t62 * t171 - 0.11e2 / 0.9e1 * t301
  t317 = t77 ** 2
  t321 = t192 ** 2
  t327 = t178 ** 2
  t339 = 0.3e1 / 0.4e1 * t309 * t47 * t180 - 0.3e1 / 0.4e1 * t179 * t52 * t184 * t192 + 0.81e2 / 0.80e2 * t71 / t78 / t317 * t321 - 0.27e2 / 0.40e2 * t185 * (0.5e1 * params.b * t309 * t74 + 0.50e2 / 0.9e1 * params.b * t327 * t91 + 0.25e2 / 0.9e1 * t72 * t91 * t309) + 0.22e2 / 0.81e2 * t73 * t301
  t350 = t211 ** 2
  t356 = 0.1e1 / t18 / t93 / t159
  t357 = t92 * t356
  t373 = (t33 * t258 * t44 + t33 * (t27 * t261 * t148 / 0.4e1 + t27 * t261 / 0.4e1 + t31 * t36) * t44 + t33 * t153 * t157 * t34 * t216 / 0.8e1 + 0.3e1 / 0.512e3 * t33 / t276 * t279 / t205 / t282 - 0.3e1 / 0.16e2 * t158 * t289) * t47 * t52 * t59 / 0.24e2 - 0.2e1 / 0.9e1 * t167 * t172 + 0.11e2 / 0.27e2 * t53 * t301 + 0.292e3 / 0.2025e4 * t304 + 0.292e3 / 0.2025e4 * t84 * t339 - 0.73e2 / 0.97200e5 * t339 * t101 - 0.73e2 / 0.97200e5 * t197 * t202 * t211 + 0.73e2 / 0.388800e6 * t84 / t101 / t100 * t350 - 0.73e2 / 0.194400e6 * t203 * (0.972e3 * t289 + 0.30400e5 / 0.9e1 * t91 * t357) + 0.950e3 / 0.531441e6 * t106 * t357 + t110 * t287 * t39 / 0.120e3 + t114 * t118 / t119 / t35 / 0.8e1
  t379 = t130 ** 2
  t399 = f.my_piecewise3(t2, 0, t6 * t17 * t64 * t138 / 0.12e2 - t142 * t20 * t143 * t236 / 0.4e1 + 0.3e1 / 0.4e1 * t142 * t144 / t145 / t133 * t253 - 0.3e1 / 0.8e1 * t142 * t144 * t146 * (t373 * t131 + 0.4e1 / 0.9e1 * t224 * t227 * t125 * t232 + 0.4e1 / 0.27e2 * t124 / t379 * params.e * t88 * t90 * t34 * t54 * t356 - 0.22e2 / 0.27e2 * t229 * t230 * t55 * t300))
  v2rho2_0_ = 0.2e1 * r0 * t399 + 0.4e1 * t241
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = 0.1e1 / t19 / r0
  t23 = 0.1e1 / r0
  t25 = 0.1e1 / tau0
  t27 = s0 * t23 * t25 / 0.8e1
  t28 = params.BLOC_b * s0
  t32 = params.BLOC_a + t28 * t23 * t25 / 0.8e1
  t33 = t27 ** t32
  t34 = params.c * t33
  t35 = s0 ** 2
  t36 = r0 ** 2
  t37 = 0.1e1 / t36
  t39 = tau0 ** 2
  t40 = 0.1e1 / t39
  t41 = t35 * t37 * t40
  t43 = 0.1e1 + t41 / 0.64e2
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t48 = 6 ** (0.1e1 / 0.3e1)
  t50 = jnp.pi ** 2
  t51 = t50 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t53 = 0.1e1 / t52
  t54 = (0.10e2 / 0.81e2 + t34 * t45) * t48 * t53
  t55 = 2 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = s0 * t56
  t59 = 0.1e1 / t19 / t36
  t60 = t57 * t59
  t63 = tau0 * t56
  t66 = t63 * t21 - t60 / 0.8e1
  t70 = 0.5e1 / 0.9e1 * t66 * t48 * t53 - 0.1e1
  t71 = params.b * t66
  t72 = t48 * t53
  t73 = t72 * t70
  t76 = 0.5e1 * t71 * t73 + 0.9e1
  t77 = jnp.sqrt(t76)
  t78 = 0.1e1 / t77
  t83 = 0.27e2 / 0.20e2 * t70 * t78 + t72 * t60 / 0.36e2
  t84 = t83 ** 2
  t87 = t48 ** 2
  t89 = 0.1e1 / t51 / t50
  t90 = t87 * t89
  t91 = t35 * t55
  t92 = t36 ** 2
  t93 = t92 * r0
  t96 = t91 / t18 / t93
  t99 = 0.100e3 * t90 * t96 + 0.162e3 * t41
  t100 = jnp.sqrt(t99)
  t105 = 0.1e1 / params.kappa * t87 * t89
  t108 = jnp.sqrt(params.e)
  t109 = t108 * t35
  t113 = params.e * params.mu
  t114 = t50 ** 2
  t117 = 0.1e1 / t114 * t35 * s0
  t118 = t92 ** 2
  t123 = t54 * t60 / 0.24e2 + 0.146e3 / 0.2025e4 * t84 - 0.73e2 / 0.97200e5 * t83 * t100 + 0.25e2 / 0.472392e6 * t105 * t96 + t109 * t37 * t40 / 0.720e3 + t113 * t117 / t118 / 0.576e3
  t124 = t108 * t48
  t128 = 0.1e1 + t124 * t53 * t60 / 0.24e2
  t129 = t128 ** 2
  t130 = 0.1e1 / t129
  t132 = t123 * t130 + params.kappa
  t137 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t132)
  t141 = t6 * t17
  t143 = params.kappa ** 2
  t144 = 0.1e1 / t19 * t143
  t145 = t132 ** 2
  t146 = 0.1e1 / t145
  t148 = jnp.log(t27)
  t153 = -t28 * t37 * t25 * t148 / 0.8e1 - t32 * t23
  t154 = t153 * t45
  t157 = 0.1e1 / t44 / t43
  t158 = t34 * t157
  t159 = t36 * r0
  t160 = 0.1e1 / t159
  t162 = t35 * t160 * t40
  t167 = (t34 * t154 + t158 * t162 / 0.16e2) * t48 * t53
  t171 = 0.1e1 / t19 / t159
  t172 = t57 * t171
  t178 = -0.5e1 / 0.3e1 * t63 * t59 + t172 / 0.3e1
  t179 = t178 * t48
  t180 = t53 * t78
  t184 = 0.1e1 / t77 / t76
  t185 = t70 * t184
  t189 = t90 * t178
  t192 = 0.5e1 * params.b * t178 * t73 + 0.25e2 / 0.9e1 * t71 * t189
  t197 = 0.3e1 / 0.4e1 * t179 * t180 - 0.27e2 / 0.40e2 * t185 * t192 - 0.2e1 / 0.27e2 * t72 * t172
  t202 = 0.1e1 / t100
  t203 = t83 * t202
  t205 = t92 * t36
  t208 = t91 / t18 / t205
  t211 = -0.324e3 * t162 - 0.1600e4 / 0.3e1 * t90 * t208
  t216 = t160 * t40
  t220 = 0.1e1 / t118 / r0
  t224 = t167 * t60 / 0.24e2 - t54 * t172 / 0.9e1 + 0.292e3 / 0.2025e4 * t83 * t197 - 0.73e2 / 0.97200e5 * t197 * t100 - 0.73e2 / 0.194400e6 * t203 * t211 - 0.50e2 / 0.177147e6 * t105 * t208 - t109 * t216 / 0.360e3 - t113 * t117 * t220 / 0.72e2
  t227 = 0.1e1 / t129 / t128
  t229 = t123 * t227 * t124
  t230 = t53 * s0
  t232 = t230 * t56 * t171
  t235 = t224 * t130 + 0.2e1 / 0.9e1 * t229 * t232
  t236 = t146 * t235
  t240 = t18 * t143
  t242 = 0.1e1 / t145 / t132
  t243 = t235 ** 2
  t244 = t242 * t243
  t248 = t153 ** 2
  t251 = t160 * t25
  t258 = t28 * t251 * t148 / 0.4e1 + t28 * t251 / 0.4e1 + t32 * t37
  t261 = t34 * t153
  t262 = t157 * t35
  t263 = t262 * t216
  t266 = t44 ** 2
  t267 = 0.1e1 / t266
  t268 = t34 * t267
  t269 = t35 ** 2
  t270 = 0.1e1 / t205
  t272 = t39 ** 2
  t273 = 0.1e1 / t272
  t277 = 0.1e1 / t92
  t279 = t35 * t277 * t40
  t284 = (t34 * t248 * t45 + t34 * t258 * t45 + t261 * t263 / 0.8e1 + 0.3e1 / 0.512e3 * t268 * t269 * t270 * t273 - 0.3e1 / 0.16e2 * t158 * t279) * t48 * t53
  t290 = 0.1e1 / t19 / t92
  t291 = t57 * t290
  t294 = t197 ** 2
  t299 = 0.40e2 / 0.9e1 * t63 * t171 - 0.11e2 / 0.9e1 * t291
  t300 = t299 * t48
  t303 = t53 * t184
  t304 = t303 * t192
  t307 = t76 ** 2
  t309 = 0.1e1 / t77 / t307
  t310 = t70 * t309
  t311 = t192 ** 2
  t314 = params.b * t299
  t317 = t178 ** 2
  t324 = 0.5e1 * t314 * t73 + 0.50e2 / 0.9e1 * params.b * t317 * t90 + 0.25e2 / 0.9e1 * t71 * t90 * t299
  t329 = 0.3e1 / 0.4e1 * t300 * t180 - 0.3e1 / 0.4e1 * t179 * t304 + 0.81e2 / 0.80e2 * t310 * t311 - 0.27e2 / 0.40e2 * t185 * t324 + 0.22e2 / 0.81e2 * t72 * t291
  t334 = t197 * t202
  t338 = 0.1e1 / t100 / t99
  t339 = t83 * t338
  t340 = t211 ** 2
  t344 = t92 * t159
  t346 = 0.1e1 / t18 / t344
  t347 = t91 * t346
  t350 = 0.972e3 * t279 + 0.30400e5 / 0.9e1 * t90 * t347
  t355 = t277 * t40
  t363 = t284 * t60 / 0.24e2 - 0.2e1 / 0.9e1 * t167 * t172 + 0.11e2 / 0.27e2 * t54 * t291 + 0.292e3 / 0.2025e4 * t294 + 0.292e3 / 0.2025e4 * t83 * t329 - 0.73e2 / 0.97200e5 * t329 * t100 - 0.73e2 / 0.97200e5 * t334 * t211 + 0.73e2 / 0.388800e6 * t339 * t340 - 0.73e2 / 0.194400e6 * t203 * t350 + 0.950e3 / 0.531441e6 * t105 * t347 + t109 * t355 / 0.120e3 + t113 * t117 / t118 / t36 / 0.8e1
  t366 = t224 * t227 * t124
  t369 = t129 ** 2
  t370 = 0.1e1 / t369
  t372 = params.e * t87
  t373 = t123 * t370 * t372
  t374 = t89 * t35
  t376 = t374 * t55 * t346
  t380 = t230 * t56 * t290
  t383 = t363 * t130 + 0.4e1 / 0.9e1 * t366 * t232 + 0.4e1 / 0.27e2 * t373 * t376 - 0.22e2 / 0.27e2 * t229 * t380
  t384 = t146 * t383
  t389 = f.my_piecewise3(t2, 0, t6 * t17 * t21 * t137 / 0.12e2 - t141 * t144 * t236 / 0.4e1 + 0.3e1 / 0.4e1 * t141 * t240 * t244 - 0.3e1 / 0.8e1 * t141 * t240 * t384)
  t405 = t145 ** 2
  t428 = t277 * t25
  t465 = 0.1e1 / t93
  t467 = t35 * t465 * t40
  t480 = 0.1e1 / t19 / t93
  t481 = t57 * t480
  t489 = -0.440e3 / 0.27e2 * t63 * t290 + 0.154e3 / 0.27e2 * t481
  t525 = 0.3e1 / 0.4e1 * t489 * t48 * t180 - 0.9e1 / 0.8e1 * t300 * t304 + 0.27e2 / 0.16e2 * t179 * t53 * t309 * t311 - 0.9e1 / 0.8e1 * t179 * t303 * t324 - 0.81e2 / 0.32e2 * t70 / t77 / t307 / t76 * t311 * t192 + 0.243e3 / 0.80e2 * t310 * t192 * t324 - 0.27e2 / 0.40e2 * t185 * (0.5e1 * params.b * t489 * t73 + 0.50e2 / 0.3e1 * t314 * t189 + 0.25e2 / 0.9e1 * t71 * t90 * t489) - 0.308e3 / 0.243e3 * t72 * t481
  t538 = t99 ** 2
  t550 = 0.1e1 / t18 / t118
  t551 = t91 * t550
  t564 = t117 / t118 / t159
  t567 = (t34 * t248 * t153 * t45 + 0.3e1 * t34 * t154 * t258 + 0.3e1 / 0.16e2 * t34 * t248 * t263 + t34 * (-0.3e1 / 0.4e1 * t28 * t428 * t148 - 0.9e1 / 0.8e1 * t28 * t428 - 0.2e1 * t32 * t160) * t45 + 0.3e1 / 0.16e2 * t34 * t258 * t263 + 0.9e1 / 0.512e3 * t261 * t267 * t269 * t270 * t273 - 0.9e1 / 0.16e2 * t261 * t262 * t355 + 0.3e1 / 0.4096e4 * t34 / t266 / t43 * t269 * t35 * t220 / t272 / t39 - 0.27e2 / 0.512e3 * t268 * t269 / t344 * t273 + 0.3e1 / 0.4e1 * t158 * t467) * t48 * t53 * t60 / 0.24e2 - t284 * t172 / 0.3e1 + 0.11e2 / 0.9e1 * t167 * t291 - 0.154e3 / 0.81e2 * t54 * t481 + 0.292e3 / 0.675e3 * t197 * t329 + 0.292e3 / 0.2025e4 * t83 * t525 - 0.73e2 / 0.97200e5 * t525 * t100 - 0.73e2 / 0.64800e5 * t329 * t202 * t211 + 0.73e2 / 0.129600e6 * t197 * t338 * t340 - 0.73e2 / 0.64800e5 * t334 * t350 - 0.73e2 / 0.259200e6 * t83 / t100 / t538 * t340 * t211 + 0.73e2 / 0.129600e6 * t339 * t211 * t350 - 0.73e2 / 0.194400e6 * t203 * (-0.3888e4 * t467 - 0.668800e6 / 0.27e2 * t90 * t551) - 0.20900e5 / 0.1594323e7 * t105 * t551 - t109 * t465 * t40 / 0.30e2 - 0.5e1 / 0.4e1 * t113 * t564
  t600 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t59 * t137 + t141 * t21 * t143 * t236 / 0.4e1 + 0.3e1 / 0.4e1 * t141 * t144 * t244 - 0.3e1 / 0.8e1 * t141 * t144 * t384 - 0.9e1 / 0.4e1 * t141 * t240 / t405 * t243 * t235 + 0.9e1 / 0.4e1 * t6 * t17 * t18 * t143 * t242 * t235 * t383 - 0.3e1 / 0.8e1 * t141 * t240 * t146 * (t567 * t130 + 0.2e1 / 0.3e1 * t363 * t227 * t124 * t232 + 0.4e1 / 0.9e1 * t224 * t370 * t372 * t376 - 0.22e2 / 0.9e1 * t366 * t380 + 0.64e2 / 0.81e2 * t123 / t369 / t128 * t108 * params.e * t564 - 0.44e2 / 0.27e2 * t373 * t374 * t55 * t550 + 0.308e3 / 0.81e2 * t229 * t230 * t56 * t480))
  v3rho3_0_ = 0.2e1 * r0 * t600 + 0.6e1 * t389

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** 2
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / t18
  t24 = 0.1e1 / r0
  t26 = 0.1e1 / tau0
  t28 = s0 * t24 * t26 / 0.8e1
  t29 = params.BLOC_b * s0
  t33 = params.BLOC_a + t29 * t24 * t26 / 0.8e1
  t34 = t28 ** t33
  t35 = params.c * t34
  t36 = s0 ** 2
  t37 = 0.1e1 / t18
  t39 = tau0 ** 2
  t40 = 0.1e1 / t39
  t41 = t36 * t37 * t40
  t43 = 0.1e1 + t41 / 0.64e2
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t48 = 6 ** (0.1e1 / 0.3e1)
  t50 = jnp.pi ** 2
  t51 = t50 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t53 = 0.1e1 / t52
  t54 = (0.10e2 / 0.81e2 + t35 * t45) * t48 * t53
  t55 = 2 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = s0 * t56
  t58 = t57 * t22
  t61 = tau0 * t56
  t63 = 0.1e1 / t20 / r0
  t66 = t61 * t63 - t58 / 0.8e1
  t70 = 0.5e1 / 0.9e1 * t66 * t48 * t53 - 0.1e1
  t71 = params.b * t66
  t72 = t48 * t53
  t73 = t72 * t70
  t76 = 0.5e1 * t71 * t73 + 0.9e1
  t77 = jnp.sqrt(t76)
  t78 = 0.1e1 / t77
  t83 = 0.27e2 / 0.20e2 * t70 * t78 + t72 * t58 / 0.36e2
  t84 = t83 ** 2
  t87 = t48 ** 2
  t89 = 0.1e1 / t51 / t50
  t90 = t87 * t89
  t91 = t36 * t55
  t92 = t18 ** 2
  t93 = t92 * r0
  t96 = t91 / t19 / t93
  t99 = 0.100e3 * t90 * t96 + 0.162e3 * t41
  t100 = jnp.sqrt(t99)
  t105 = 0.1e1 / params.kappa * t87 * t89
  t108 = jnp.sqrt(params.e)
  t109 = t108 * t36
  t113 = params.e * params.mu
  t114 = t50 ** 2
  t115 = 0.1e1 / t114
  t117 = t115 * t36 * s0
  t118 = t92 ** 2
  t119 = 0.1e1 / t118
  t123 = t54 * t58 / 0.24e2 + 0.146e3 / 0.2025e4 * t84 - 0.73e2 / 0.97200e5 * t83 * t100 + 0.25e2 / 0.472392e6 * t105 * t96 + t109 * t37 * t40 / 0.720e3 + t113 * t117 * t119 / 0.576e3
  t124 = t108 * t48
  t128 = 0.1e1 + t124 * t53 * t58 / 0.24e2
  t129 = t128 ** 2
  t130 = 0.1e1 / t129
  t132 = t123 * t130 + params.kappa
  t137 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t132)
  t141 = t6 * t17
  t142 = params.kappa ** 2
  t143 = t63 * t142
  t144 = t132 ** 2
  t145 = 0.1e1 / t144
  t147 = jnp.log(t28)
  t152 = -t29 * t37 * t26 * t147 / 0.8e1 - t33 * t24
  t153 = t152 * t45
  t156 = 0.1e1 / t44 / t43
  t157 = t35 * t156
  t158 = t18 * r0
  t159 = 0.1e1 / t158
  t161 = t36 * t159 * t40
  t166 = (t35 * t153 + t157 * t161 / 0.16e2) * t48 * t53
  t170 = 0.1e1 / t20 / t158
  t171 = t57 * t170
  t177 = -0.5e1 / 0.3e1 * t61 * t22 + t171 / 0.3e1
  t178 = t177 * t48
  t179 = t53 * t78
  t183 = 0.1e1 / t77 / t76
  t184 = t70 * t183
  t188 = t90 * t177
  t191 = 0.5e1 * params.b * t177 * t73 + 0.25e2 / 0.9e1 * t71 * t188
  t196 = 0.3e1 / 0.4e1 * t178 * t179 - 0.27e2 / 0.40e2 * t184 * t191 - 0.2e1 / 0.27e2 * t72 * t171
  t201 = 0.1e1 / t100
  t202 = t83 * t201
  t204 = t92 * t18
  t207 = t91 / t19 / t204
  t210 = -0.324e3 * t161 - 0.1600e4 / 0.3e1 * t90 * t207
  t215 = t159 * t40
  t218 = t118 * r0
  t219 = 0.1e1 / t218
  t223 = t166 * t58 / 0.24e2 - t54 * t171 / 0.9e1 + 0.292e3 / 0.2025e4 * t83 * t196 - 0.73e2 / 0.97200e5 * t196 * t100 - 0.73e2 / 0.194400e6 * t202 * t210 - 0.50e2 / 0.177147e6 * t105 * t207 - t109 * t215 / 0.360e3 - t113 * t117 * t219 / 0.72e2
  t226 = 0.1e1 / t129 / t128
  t228 = t123 * t226 * t124
  t229 = t53 * s0
  t231 = t229 * t56 * t170
  t234 = t223 * t130 + 0.2e1 / 0.9e1 * t228 * t231
  t235 = t145 * t234
  t239 = 0.1e1 / t20
  t240 = t239 * t142
  t242 = 0.1e1 / t144 / t132
  t243 = t234 ** 2
  t244 = t242 * t243
  t248 = t152 ** 2
  t249 = t248 * t45
  t251 = t159 * t26
  t258 = t29 * t251 * t147 / 0.4e1 + t29 * t251 / 0.4e1 + t33 * t37
  t261 = t35 * t152
  t262 = t156 * t36
  t263 = t262 * t215
  t266 = t44 ** 2
  t267 = 0.1e1 / t266
  t268 = t35 * t267
  t269 = t36 ** 2
  t270 = 0.1e1 / t204
  t272 = t39 ** 2
  t273 = 0.1e1 / t272
  t277 = 0.1e1 / t92
  t279 = t36 * t277 * t40
  t284 = (t35 * t249 + t35 * t258 * t45 + t261 * t263 / 0.8e1 + 0.3e1 / 0.512e3 * t268 * t269 * t270 * t273 - 0.3e1 / 0.16e2 * t157 * t279) * t48 * t53
  t290 = 0.1e1 / t20 / t92
  t291 = t57 * t290
  t294 = t196 ** 2
  t299 = 0.40e2 / 0.9e1 * t61 * t170 - 0.11e2 / 0.9e1 * t291
  t300 = t299 * t48
  t303 = t53 * t183
  t304 = t303 * t191
  t307 = t76 ** 2
  t309 = 0.1e1 / t77 / t307
  t310 = t70 * t309
  t311 = t191 ** 2
  t314 = params.b * t299
  t317 = t177 ** 2
  t324 = 0.5e1 * t314 * t73 + 0.50e2 / 0.9e1 * params.b * t317 * t90 + 0.25e2 / 0.9e1 * t71 * t90 * t299
  t329 = 0.3e1 / 0.4e1 * t300 * t179 - 0.3e1 / 0.4e1 * t178 * t304 + 0.81e2 / 0.80e2 * t310 * t311 - 0.27e2 / 0.40e2 * t184 * t324 + 0.22e2 / 0.81e2 * t72 * t291
  t334 = t196 * t201
  t338 = 0.1e1 / t100 / t99
  t339 = t83 * t338
  t340 = t210 ** 2
  t344 = t92 * t158
  t346 = 0.1e1 / t19 / t344
  t347 = t91 * t346
  t350 = 0.972e3 * t279 + 0.30400e5 / 0.9e1 * t90 * t347
  t355 = t277 * t40
  t359 = 0.1e1 / t118 / t18
  t363 = t284 * t58 / 0.24e2 - 0.2e1 / 0.9e1 * t166 * t171 + 0.11e2 / 0.27e2 * t54 * t291 + 0.292e3 / 0.2025e4 * t294 + 0.292e3 / 0.2025e4 * t83 * t329 - 0.73e2 / 0.97200e5 * t329 * t100 - 0.73e2 / 0.97200e5 * t334 * t210 + 0.73e2 / 0.388800e6 * t339 * t340 - 0.73e2 / 0.194400e6 * t202 * t350 + 0.950e3 / 0.531441e6 * t105 * t347 + t109 * t355 / 0.120e3 + t113 * t117 * t359 / 0.8e1
  t366 = t223 * t226 * t124
  t369 = t129 ** 2
  t370 = 0.1e1 / t369
  t372 = params.e * t87
  t373 = t123 * t370 * t372
  t374 = t89 * t36
  t376 = t374 * t55 * t346
  t380 = t229 * t56 * t290
  t383 = t363 * t130 + 0.4e1 / 0.9e1 * t366 * t231 + 0.4e1 / 0.27e2 * t373 * t376 - 0.22e2 / 0.27e2 * t228 * t380
  t384 = t145 * t383
  t388 = t19 * t142
  t389 = t144 ** 2
  t390 = 0.1e1 / t389
  t392 = t390 * t243 * t234
  t397 = t6 * t17 * t19
  t398 = t142 * t242
  t400 = t398 * t234 * t383
  t403 = t248 * t152
  t409 = t35 * t248
  t412 = t277 * t26
  t420 = -0.3e1 / 0.4e1 * t29 * t412 * t147 - 0.9e1 / 0.8e1 * t29 * t412 - 0.2e1 * t33 * t159
  t423 = t35 * t258
  t426 = t267 * t269
  t428 = t426 * t270 * t273
  t431 = t262 * t355
  t435 = 0.1e1 / t266 / t43
  t436 = t35 * t435
  t437 = t269 * t36
  t440 = 0.1e1 / t272 / t39
  t444 = 0.1e1 / t344
  t449 = 0.1e1 / t93
  t451 = t36 * t449 * t40
  t456 = (t35 * t403 * t45 + 0.3e1 * t35 * t153 * t258 + 0.3e1 / 0.16e2 * t409 * t263 + t35 * t420 * t45 + 0.3e1 / 0.16e2 * t423 * t263 + 0.9e1 / 0.512e3 * t261 * t428 - 0.9e1 / 0.16e2 * t261 * t431 + 0.3e1 / 0.4096e4 * t436 * t437 * t219 * t440 - 0.27e2 / 0.512e3 * t268 * t269 * t444 * t273 + 0.3e1 / 0.4e1 * t157 * t451) * t48 * t53
  t464 = 0.1e1 / t20 / t93
  t465 = t57 * t464
  t473 = -0.440e3 / 0.27e2 * t61 * t290 + 0.154e3 / 0.27e2 * t465
  t474 = t473 * t48
  t480 = t53 * t309 * t311
  t483 = t303 * t324
  t488 = 0.1e1 / t77 / t307 / t76
  t489 = t70 * t488
  t490 = t311 * t191
  t496 = params.b * t473
  t504 = 0.5e1 * t496 * t73 + 0.50e2 / 0.3e1 * t314 * t188 + 0.25e2 / 0.9e1 * t71 * t90 * t473
  t509 = 0.3e1 / 0.4e1 * t474 * t179 - 0.9e1 / 0.8e1 * t300 * t304 + 0.27e2 / 0.16e2 * t178 * t480 - 0.9e1 / 0.8e1 * t178 * t483 - 0.81e2 / 0.32e2 * t489 * t490 + 0.243e3 / 0.80e2 * t310 * t191 * t324 - 0.27e2 / 0.40e2 * t184 * t504 - 0.308e3 / 0.243e3 * t72 * t465
  t514 = t329 * t201
  t517 = t196 * t338
  t522 = t99 ** 2
  t524 = 0.1e1 / t100 / t522
  t525 = t83 * t524
  t526 = t340 * t210
  t529 = t210 * t350
  t534 = 0.1e1 / t19 / t118
  t535 = t91 * t534
  t538 = -0.3888e4 * t451 - 0.668800e6 / 0.27e2 * t90 * t535
  t543 = t449 * t40
  t548 = t117 / t118 / t158
  t551 = t456 * t58 / 0.24e2 - t284 * t171 / 0.3e1 + 0.11e2 / 0.9e1 * t166 * t291 - 0.154e3 / 0.81e2 * t54 * t465 + 0.292e3 / 0.675e3 * t196 * t329 + 0.292e3 / 0.2025e4 * t83 * t509 - 0.73e2 / 0.97200e5 * t509 * t100 - 0.73e2 / 0.64800e5 * t514 * t210 + 0.73e2 / 0.129600e6 * t517 * t340 - 0.73e2 / 0.64800e5 * t334 * t350 - 0.73e2 / 0.259200e6 * t525 * t526 + 0.73e2 / 0.129600e6 * t339 * t529 - 0.73e2 / 0.194400e6 * t202 * t538 - 0.20900e5 / 0.1594323e7 * t105 * t535 - t109 * t543 / 0.30e2 - 0.5e1 / 0.4e1 * t113 * t548
  t554 = t363 * t226 * t124
  t558 = t223 * t370 * t372
  t564 = 0.1e1 / t369 / t128
  t566 = t108 * params.e
  t567 = t123 * t564 * t566
  t571 = t374 * t55 * t534
  t575 = t229 * t56 * t464
  t578 = t551 * t130 + 0.2e1 / 0.3e1 * t554 * t231 + 0.4e1 / 0.9e1 * t558 * t376 - 0.22e2 / 0.9e1 * t366 * t380 + 0.64e2 / 0.81e2 * t567 * t548 - 0.44e2 / 0.27e2 * t373 * t571 + 0.308e3 / 0.81e2 * t228 * t575
  t579 = t145 * t578
  t584 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t137 + t141 * t143 * t235 / 0.4e1 + 0.3e1 / 0.4e1 * t141 * t240 * t244 - 0.3e1 / 0.8e1 * t141 * t240 * t384 - 0.9e1 / 0.4e1 * t141 * t388 * t392 + 0.9e1 / 0.4e1 * t397 * t400 - 0.3e1 / 0.8e1 * t141 * t388 * t579)
  t611 = t243 ** 2
  t621 = t383 ** 2
  t642 = t340 ** 2
  t648 = t350 ** 2
  t664 = 0.73e2 / 0.64800e5 * t329 * t338 * t340 - 0.73e2 / 0.64800e5 * t196 * t524 * t526 + 0.73e2 / 0.32400e5 * t517 * t529 + 0.73e2 / 0.103680e6 * t83 / t100 / t522 / t99 * t642 - 0.73e2 / 0.43200e5 * t525 * t340 * t350 + 0.73e2 / 0.129600e6 * t339 * t648 + 0.73e2 / 0.97200e5 * t339 * t210 * t538 + t109 * t270 * t40 / 0.6e1 - 0.73e2 / 0.48600e5 * t509 * t201 * t210 - 0.73e2 / 0.32400e5 * t514 * t350 - 0.73e2 / 0.48600e5 * t334 * t538
  t666 = t36 * t270 * t40
  t669 = 0.1e1 / t19 / t218
  t670 = t91 * t669
  t677 = 0.1e1 / t118 / t92
  t678 = t117 * t677
  t681 = t329 ** 2
  t688 = 0.1e1 / t20 / t204
  t689 = t57 * t688
  t691 = 0.6160e4 / 0.81e2 * t61 * t464 - 0.2618e4 / 0.81e2 * t689
  t713 = t307 ** 2
  t717 = t311 ** 2
  t723 = t324 ** 2
  t734 = t299 ** 2
  t746 = 0.3e1 / 0.4e1 * t691 * t48 * t179 - 0.3e1 / 0.2e1 * t474 * t304 + 0.27e2 / 0.8e1 * t300 * t480 - 0.9e1 / 0.4e1 * t300 * t483 - 0.45e2 / 0.8e1 * t178 * t53 * t488 * t490 + 0.27e2 / 0.4e1 * t178 * t53 * t309 * t191 * t324 - 0.3e1 / 0.2e1 * t178 * t303 * t504 + 0.567e3 / 0.64e2 * t70 / t77 / t713 * t717 - 0.243e3 / 0.16e2 * t489 * t311 * t324 + 0.243e3 / 0.80e2 * t310 * t723 + 0.81e2 / 0.20e2 * t310 * t191 * t504 - 0.27e2 / 0.40e2 * t184 * (0.5e1 * params.b * t691 * t73 + 0.200e3 / 0.9e1 * t496 * t188 + 0.50e2 / 0.3e1 * params.b * t734 * t90 + 0.25e2 / 0.9e1 * t71 * t90 * t691) + 0.5236e4 / 0.729e3 * t72 * t689
  t759 = t449 * t26
  t790 = t248 ** 2
  t793 = t258 ** 2
  t828 = t269 ** 2
  t830 = t272 ** 2
  t835 = t35 * (0.3e1 * t29 * t759 * t147 + 0.11e2 / 0.2e1 * t29 * t759 + 0.6e1 * t33 * t277) * t45 - 0.27e2 / 0.128e3 * t261 * t426 * t444 * t273 + 0.3e1 * t261 * t262 * t543 + 0.3e1 / 0.4e1 * t35 * t152 * t156 * t258 * t36 * t215 - 0.9e1 / 0.8e1 * t409 * t431 - 0.9e1 / 0.8e1 * t423 * t431 + 0.6e1 * t35 * t249 * t258 + t35 * t790 * t45 + 0.3e1 * t35 * t793 * t45 + 0.4e1 * t35 * t153 * t420 + 0.9e1 / 0.256e3 * t423 * t428 + 0.3e1 / 0.1024e4 * t261 * t435 * t437 * t219 * t440 - 0.27e2 / 0.2048e4 * t436 * t437 * t359 * t440 + 0.225e3 / 0.512e3 * t268 * t269 * t119 * t273 - 0.15e2 / 0.4e1 * t157 * t666 + t35 * t403 * t263 / 0.4e1 + 0.9e1 / 0.256e3 * t409 * t428 + t35 * t420 * t263 / 0.4e1 + 0.15e2 / 0.131072e6 * t35 / t266 / t44 * t828 * t677 / t830
  t842 = -0.73e2 / 0.194400e6 * t202 * (0.19440e5 * t666 + 0.16720000e8 / 0.81e2 * t90 * t670) + 0.55e2 / 0.4e1 * t113 * t678 + 0.292e3 / 0.675e3 * t681 + 0.1168e4 / 0.2025e4 * t196 * t509 + 0.292e3 / 0.2025e4 * t83 * t746 - 0.73e2 / 0.97200e5 * t746 * t100 - 0.4e1 / 0.9e1 * t456 * t171 + 0.22e2 / 0.9e1 * t284 * t291 - 0.616e3 / 0.81e2 * t166 * t465 + 0.2618e4 / 0.243e3 * t54 * t689 + t835 * t48 * t53 * t58 / 0.24e2 + 0.522500e6 / 0.4782969e7 * t105 * t670
  t866 = params.e ** 2
  t887 = (t664 + t842) * t130 + 0.8e1 / 0.9e1 * t551 * t226 * t124 * t231 + 0.8e1 / 0.9e1 * t363 * t370 * t372 * t376 - 0.44e2 / 0.9e1 * t554 * t380 + 0.256e3 / 0.81e2 * t223 * t564 * t566 * t548 - 0.176e3 / 0.27e2 * t558 * t571 + 0.1232e4 / 0.81e2 * t366 * t575 + 0.320e3 / 0.729e3 * t123 / t369 / t129 * t866 * t115 * t269 / t20 / t118 / t204 * t72 * t56 - 0.1408e4 / 0.81e2 * t567 * t678 + 0.3916e4 / 0.243e3 * t373 * t374 * t55 * t669 - 0.5236e4 / 0.243e3 * t228 * t229 * t56 * t688
  t892 = 0.10e2 / 0.27e2 * t6 * t17 * t170 * t137 - 0.5e1 / 0.9e1 * t141 * t22 * t142 * t235 - t141 * t143 * t244 + t141 * t143 * t384 / 0.2e1 - 0.3e1 * t141 * t240 * t392 + 0.3e1 * t6 * t17 * t239 * t400 - t141 * t240 * t579 / 0.2e1 + 0.9e1 * t141 * t388 / t389 / t132 * t611 - 0.27e2 / 0.2e1 * t397 * t142 * t390 * t243 * t383 + 0.9e1 / 0.4e1 * t141 * t388 * t242 * t621 + 0.3e1 * t397 * t398 * t234 * t578 - 0.3e1 / 0.8e1 * t141 * t388 * t145 * t887
  t893 = f.my_piecewise3(t2, 0, t892)
  v4rho4_0_ = 0.2e1 * r0 * t893 + 0.8e1 * t584

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
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
  t30 = t6 ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / r0
  t34 = 0.1e1 / tau0
  t36 = s0 * t32 * t34 / 0.8e1
  t37 = params.BLOC_b * s0
  t41 = params.BLOC_a + t37 * t32 * t34 / 0.8e1
  t42 = t36 ** t41
  t43 = params.c * t42
  t44 = s0 ** 2
  t45 = r0 ** 2
  t46 = 0.1e1 / t45
  t48 = tau0 ** 2
  t49 = 0.1e1 / t48
  t50 = t44 * t46 * t49
  t52 = 0.1e1 + t50 / 0.64e2
  t53 = t52 ** 2
  t54 = 0.1e1 / t53
  t57 = 6 ** (0.1e1 / 0.3e1)
  t58 = (0.10e2 / 0.81e2 + t43 * t54) * t57
  t59 = jnp.pi ** 2
  t60 = t59 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t62 = 0.1e1 / t61
  t63 = t62 * s0
  t64 = r0 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t67 = 0.1e1 / t65 / t45
  t68 = t63 * t67
  t74 = s0 * t67
  t76 = tau0 / t65 / r0 - t74 / 0.8e1
  t80 = 0.5e1 / 0.9e1 * t76 * t57 * t62 - 0.1e1
  t81 = params.b * t76
  t82 = t57 * t62
  t83 = t82 * t80
  t86 = 0.5e1 * t81 * t83 + 0.9e1
  t87 = jnp.sqrt(t86)
  t88 = 0.1e1 / t87
  t93 = 0.27e2 / 0.20e2 * t80 * t88 + t82 * t74 / 0.36e2
  t94 = t93 ** 2
  t97 = t57 ** 2
  t99 = 0.1e1 / t60 / t59
  t100 = t97 * t99
  t101 = t45 ** 2
  t104 = 0.1e1 / t64 / t101 / r0
  t108 = 0.50e2 * t100 * t44 * t104 + 0.162e3 * t50
  t109 = jnp.sqrt(t108)
  t113 = 0.1e1 / params.kappa * t97
  t114 = t99 * t44
  t118 = jnp.sqrt(params.e)
  t119 = t118 * t44
  t123 = params.e * params.mu
  t124 = t59 ** 2
  t125 = 0.1e1 / t124
  t127 = t125 * t44 * s0
  t128 = t101 ** 2
  t133 = t58 * t68 / 0.24e2 + 0.146e3 / 0.2025e4 * t94 - 0.73e2 / 0.97200e5 * t93 * t109 + 0.25e2 / 0.944784e6 * t113 * t114 * t104 + t119 * t46 * t49 / 0.720e3 + t123 * t127 / t128 / 0.2304e4
  t134 = t118 * t57
  t137 = 0.1e1 + t134 * t68 / 0.24e2
  t138 = t137 ** 2
  t139 = 0.1e1 / t138
  t141 = t133 * t139 + params.kappa
  t146 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t141)
  t150 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t151 = t150 * f.p.zeta_threshold
  t153 = f.my_piecewise3(t20, t151, t21 * t19)
  t154 = t30 ** 2
  t155 = 0.1e1 / t154
  t159 = t5 * t153 * t155 * t146 / 0.8e1
  t160 = t5 * t153
  t161 = params.kappa ** 2
  t162 = t30 * t161
  t163 = t141 ** 2
  t164 = 0.1e1 / t163
  t166 = jnp.log(t36)
  t171 = -t37 * t46 * t34 * t166 / 0.8e1 - t41 * t32
  t175 = 0.1e1 / t53 / t52
  t176 = t43 * t175
  t177 = t45 * r0
  t178 = 0.1e1 / t177
  t180 = t44 * t178 * t49
  t184 = (t43 * t171 * t54 + t176 * t180 / 0.16e2) * t57
  t188 = 0.1e1 / t65 / t177
  t189 = t63 * t188
  t194 = s0 * t188
  t196 = -0.5e1 / 0.3e1 * tau0 * t67 + t194 / 0.3e1
  t197 = t196 * t57
  t198 = t62 * t88
  t202 = 0.1e1 / t87 / t86
  t203 = t80 * t202
  t210 = 0.5e1 * params.b * t196 * t83 + 0.25e2 / 0.9e1 * t81 * t100 * t196
  t213 = t82 * t194
  t215 = 0.3e1 / 0.4e1 * t197 * t198 - 0.27e2 / 0.40e2 * t203 * t210 - 0.2e1 / 0.27e2 * t213
  t220 = 0.1e1 / t109
  t221 = t93 * t220
  t223 = t101 * t45
  t225 = 0.1e1 / t64 / t223
  t229 = -0.324e3 * t180 - 0.800e3 / 0.3e1 * t100 * t44 * t225
  t235 = t178 * t49
  t243 = t184 * t68 / 0.24e2 - t58 * t189 / 0.9e1 + 0.292e3 / 0.2025e4 * t93 * t215 - 0.73e2 / 0.97200e5 * t215 * t109 - 0.73e2 / 0.194400e6 * t221 * t229 - 0.25e2 / 0.177147e6 * t113 * t114 * t225 - t119 * t235 / 0.360e3 - t123 * t127 / t128 / r0 / 0.288e3
  t246 = 0.1e1 / t138 / t137
  t248 = t133 * t246 * t118
  t251 = t243 * t139 + 0.2e1 / 0.9e1 * t248 * t213
  t252 = t164 * t251
  t253 = t162 * t252
  t257 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t146 - t159 - 0.3e1 / 0.8e1 * t160 * t253)
  t259 = r1 <= f.p.dens_threshold
  t260 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t261 = 0.1e1 + t260
  t262 = t261 <= f.p.zeta_threshold
  t263 = t261 ** (0.1e1 / 0.3e1)
  t265 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t268 = f.my_piecewise3(t262, 0, 0.4e1 / 0.3e1 * t263 * t265)
  t270 = 0.1e1 / r1
  t272 = 0.1e1 / tau1
  t274 = s2 * t270 * t272 / 0.8e1
  t275 = params.BLOC_b * s2
  t279 = params.BLOC_a + t275 * t270 * t272 / 0.8e1
  t280 = t274 ** t279
  t281 = params.c * t280
  t282 = s2 ** 2
  t283 = r1 ** 2
  t284 = 0.1e1 / t283
  t286 = tau1 ** 2
  t287 = 0.1e1 / t286
  t288 = t282 * t284 * t287
  t290 = 0.1e1 + t288 / 0.64e2
  t291 = t290 ** 2
  t292 = 0.1e1 / t291
  t295 = (0.10e2 / 0.81e2 + t281 * t292) * t57
  t296 = t62 * s2
  t297 = r1 ** (0.1e1 / 0.3e1)
  t298 = t297 ** 2
  t300 = 0.1e1 / t298 / t283
  t301 = t296 * t300
  t307 = s2 * t300
  t309 = tau1 / t298 / r1 - t307 / 0.8e1
  t313 = 0.5e1 / 0.9e1 * t309 * t57 * t62 - 0.1e1
  t314 = params.b * t309
  t315 = t82 * t313
  t318 = 0.5e1 * t314 * t315 + 0.9e1
  t319 = jnp.sqrt(t318)
  t320 = 0.1e1 / t319
  t325 = 0.27e2 / 0.20e2 * t313 * t320 + t82 * t307 / 0.36e2
  t326 = t325 ** 2
  t329 = t283 ** 2
  t332 = 0.1e1 / t297 / t329 / r1
  t336 = 0.50e2 * t100 * t282 * t332 + 0.162e3 * t288
  t337 = jnp.sqrt(t336)
  t340 = t99 * t282
  t344 = t118 * t282
  t349 = t125 * t282 * s2
  t350 = t329 ** 2
  t355 = t295 * t301 / 0.24e2 + 0.146e3 / 0.2025e4 * t326 - 0.73e2 / 0.97200e5 * t325 * t337 + 0.25e2 / 0.944784e6 * t113 * t340 * t332 + t344 * t284 * t287 / 0.720e3 + t123 * t349 / t350 / 0.2304e4
  t358 = 0.1e1 + t134 * t301 / 0.24e2
  t359 = t358 ** 2
  t360 = 0.1e1 / t359
  t362 = t355 * t360 + params.kappa
  t367 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t362)
  t372 = f.my_piecewise3(t262, t151, t263 * t261)
  t376 = t5 * t372 * t155 * t367 / 0.8e1
  t378 = f.my_piecewise3(t259, 0, -0.3e1 / 0.8e1 * t5 * t268 * t30 * t367 - t376)
  t380 = t21 ** 2
  t381 = 0.1e1 / t380
  t382 = t26 ** 2
  t387 = t16 / t22 / t6
  t389 = -0.2e1 * t23 + 0.2e1 * t387
  t390 = f.my_piecewise5(t10, 0, t14, 0, t389)
  t394 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t381 * t382 + 0.4e1 / 0.3e1 * t21 * t390)
  t401 = t5 * t29 * t155 * t146
  t407 = 0.1e1 / t154 / t6
  t411 = t5 * t153 * t407 * t146 / 0.12e2
  t412 = t155 * t161
  t414 = t160 * t412 * t252
  t418 = t251 ** 2
  t423 = t171 ** 2
  t426 = t178 * t34
  t441 = t53 ** 2
  t444 = t44 ** 2
  t447 = t48 ** 2
  t452 = 0.1e1 / t101
  t454 = t44 * t452 * t49
  t464 = 0.1e1 / t65 / t101
  t468 = t215 ** 2
  t472 = s0 * t464
  t474 = 0.40e2 / 0.9e1 * tau0 * t188 - 0.11e2 / 0.9e1 * t472
  t482 = t86 ** 2
  t486 = t210 ** 2
  t492 = t196 ** 2
  t502 = t82 * t472
  t504 = 0.3e1 / 0.4e1 * t474 * t57 * t198 - 0.3e1 / 0.4e1 * t197 * t62 * t202 * t210 + 0.81e2 / 0.80e2 * t80 / t87 / t482 * t486 - 0.27e2 / 0.40e2 * t203 * (0.5e1 * params.b * t474 * t83 + 0.50e2 / 0.9e1 * params.b * t492 * t100 + 0.25e2 / 0.9e1 * t81 * t100 * t474) + 0.22e2 / 0.81e2 * t502
  t515 = t229 ** 2
  t521 = 0.1e1 / t64 / t101 / t177
  t523 = t100 * t44 * t521
  t539 = (t43 * t423 * t54 + t43 * (t37 * t426 * t166 / 0.4e1 + t37 * t426 / 0.4e1 + t41 * t46) * t54 + t43 * t171 * t175 * t44 * t235 / 0.8e1 + 0.3e1 / 0.512e3 * t43 / t441 * t444 / t223 / t447 - 0.3e1 / 0.16e2 * t176 * t454) * t57 * t68 / 0.24e2 - 0.2e1 / 0.9e1 * t184 * t189 + 0.11e2 / 0.27e2 * t58 * t63 * t464 + 0.292e3 / 0.2025e4 * t468 + 0.292e3 / 0.2025e4 * t93 * t504 - 0.73e2 / 0.97200e5 * t504 * t109 - 0.73e2 / 0.97200e5 * t215 * t220 * t229 + 0.73e2 / 0.388800e6 * t93 / t109 / t108 * t515 - 0.73e2 / 0.194400e6 * t221 * (0.972e3 * t454 + 0.15200e5 / 0.9e1 * t523) + 0.475e3 / 0.531441e6 * t113 * t114 * t521 + t119 * t452 * t49 / 0.120e3 + t123 * t127 / t128 / t45 / 0.32e2
  t545 = t138 ** 2
  t559 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t394 * t30 * t146 - t401 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t29 * t253 + t411 - t414 / 0.4e1 + 0.3e1 / 0.4e1 * t160 * t162 / t163 / t141 * t418 - 0.3e1 / 0.8e1 * t160 * t162 * t164 * (t539 * t139 + 0.4e1 / 0.9e1 * t243 * t246 * t118 * t213 + 0.2e1 / 0.27e2 * t133 / t545 * params.e * t523 - 0.22e2 / 0.27e2 * t248 * t502))
  t560 = t263 ** 2
  t561 = 0.1e1 / t560
  t562 = t265 ** 2
  t566 = f.my_piecewise5(t14, 0, t10, 0, -t389)
  t570 = f.my_piecewise3(t262, 0, 0.4e1 / 0.9e1 * t561 * t562 + 0.4e1 / 0.3e1 * t263 * t566)
  t577 = t5 * t268 * t155 * t367
  t582 = t5 * t372 * t407 * t367 / 0.12e2
  t584 = f.my_piecewise3(t259, 0, -0.3e1 / 0.8e1 * t5 * t570 * t30 * t367 - t577 / 0.4e1 + t582)
  d11 = 0.2e1 * t257 + 0.2e1 * t378 + t6 * (t559 + t584)
  t587 = -t7 - t24
  t588 = f.my_piecewise5(t10, 0, t14, 0, t587)
  t591 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t588)
  t597 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t591 * t30 * t146 - t159)
  t599 = f.my_piecewise5(t14, 0, t10, 0, -t587)
  t602 = f.my_piecewise3(t262, 0, 0.4e1 / 0.3e1 * t263 * t599)
  t607 = t5 * t372
  t608 = t362 ** 2
  t609 = 0.1e1 / t608
  t611 = jnp.log(t274)
  t616 = -t275 * t284 * t272 * t611 / 0.8e1 - t279 * t270
  t620 = 0.1e1 / t291 / t290
  t621 = t281 * t620
  t622 = t283 * r1
  t623 = 0.1e1 / t622
  t625 = t282 * t623 * t287
  t629 = (t281 * t616 * t292 + t621 * t625 / 0.16e2) * t57
  t633 = 0.1e1 / t298 / t622
  t634 = t296 * t633
  t639 = s2 * t633
  t641 = -0.5e1 / 0.3e1 * tau1 * t300 + t639 / 0.3e1
  t642 = t641 * t57
  t643 = t62 * t320
  t647 = 0.1e1 / t319 / t318
  t648 = t313 * t647
  t655 = 0.5e1 * params.b * t641 * t315 + 0.25e2 / 0.9e1 * t314 * t100 * t641
  t658 = t82 * t639
  t660 = 0.3e1 / 0.4e1 * t642 * t643 - 0.27e2 / 0.40e2 * t648 * t655 - 0.2e1 / 0.27e2 * t658
  t665 = 0.1e1 / t337
  t666 = t325 * t665
  t668 = t329 * t283
  t670 = 0.1e1 / t297 / t668
  t674 = -0.324e3 * t625 - 0.800e3 / 0.3e1 * t100 * t282 * t670
  t680 = t623 * t287
  t688 = t629 * t301 / 0.24e2 - t295 * t634 / 0.9e1 + 0.292e3 / 0.2025e4 * t325 * t660 - 0.73e2 / 0.97200e5 * t660 * t337 - 0.73e2 / 0.194400e6 * t666 * t674 - 0.25e2 / 0.177147e6 * t113 * t340 * t670 - t344 * t680 / 0.360e3 - t123 * t349 / t350 / r1 / 0.288e3
  t691 = 0.1e1 / t359 / t358
  t693 = t355 * t691 * t118
  t696 = t688 * t360 + 0.2e1 / 0.9e1 * t693 * t658
  t697 = t609 * t696
  t698 = t162 * t697
  t702 = f.my_piecewise3(t259, 0, -0.3e1 / 0.8e1 * t5 * t602 * t30 * t367 - t376 - 0.3e1 / 0.8e1 * t607 * t698)
  t706 = 0.2e1 * t387
  t707 = f.my_piecewise5(t10, 0, t14, 0, t706)
  t711 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t381 * t588 * t26 + 0.4e1 / 0.3e1 * t21 * t707)
  t718 = t5 * t591 * t155 * t146
  t726 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t711 * t30 * t146 - t718 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t591 * t253 - t401 / 0.8e1 + t411 - t414 / 0.8e1)
  t730 = f.my_piecewise5(t14, 0, t10, 0, -t706)
  t734 = f.my_piecewise3(t262, 0, 0.4e1 / 0.9e1 * t561 * t599 * t265 + 0.4e1 / 0.3e1 * t263 * t730)
  t741 = t5 * t602 * t155 * t367
  t748 = t607 * t412 * t697
  t751 = f.my_piecewise3(t259, 0, -0.3e1 / 0.8e1 * t5 * t734 * t30 * t367 - t741 / 0.8e1 - t577 / 0.8e1 + t582 - 0.3e1 / 0.8e1 * t5 * t268 * t698 - t748 / 0.8e1)
  d12 = t257 + t378 + t597 + t702 + t6 * (t726 + t751)
  t756 = t588 ** 2
  t760 = 0.2e1 * t23 + 0.2e1 * t387
  t761 = f.my_piecewise5(t10, 0, t14, 0, t760)
  t765 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t381 * t756 + 0.4e1 / 0.3e1 * t21 * t761)
  t772 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t765 * t30 * t146 - t718 / 0.4e1 + t411)
  t773 = t599 ** 2
  t777 = f.my_piecewise5(t14, 0, t10, 0, -t760)
  t781 = f.my_piecewise3(t262, 0, 0.4e1 / 0.9e1 * t561 * t773 + 0.4e1 / 0.3e1 * t263 * t777)
  t793 = t696 ** 2
  t798 = t616 ** 2
  t801 = t623 * t272
  t816 = t291 ** 2
  t819 = t282 ** 2
  t822 = t286 ** 2
  t827 = 0.1e1 / t329
  t829 = t282 * t827 * t287
  t839 = 0.1e1 / t298 / t329
  t843 = t660 ** 2
  t847 = s2 * t839
  t849 = 0.40e2 / 0.9e1 * tau1 * t633 - 0.11e2 / 0.9e1 * t847
  t857 = t318 ** 2
  t861 = t655 ** 2
  t867 = t641 ** 2
  t877 = t82 * t847
  t879 = 0.3e1 / 0.4e1 * t849 * t57 * t643 - 0.3e1 / 0.4e1 * t642 * t62 * t647 * t655 + 0.81e2 / 0.80e2 * t313 / t319 / t857 * t861 - 0.27e2 / 0.40e2 * t648 * (0.5e1 * params.b * t849 * t315 + 0.50e2 / 0.9e1 * params.b * t867 * t100 + 0.25e2 / 0.9e1 * t314 * t100 * t849) + 0.22e2 / 0.81e2 * t877
  t890 = t674 ** 2
  t896 = 0.1e1 / t297 / t329 / t622
  t898 = t100 * t282 * t896
  t914 = (t281 * t798 * t292 + t281 * (t275 * t801 * t611 / 0.4e1 + t275 * t801 / 0.4e1 + t279 * t284) * t292 + t281 * t616 * t620 * t282 * t680 / 0.8e1 + 0.3e1 / 0.512e3 * t281 / t816 * t819 / t668 / t822 - 0.3e1 / 0.16e2 * t621 * t829) * t57 * t301 / 0.24e2 - 0.2e1 / 0.9e1 * t629 * t634 + 0.11e2 / 0.27e2 * t295 * t296 * t839 + 0.292e3 / 0.2025e4 * t843 + 0.292e3 / 0.2025e4 * t325 * t879 - 0.73e2 / 0.97200e5 * t879 * t337 - 0.73e2 / 0.97200e5 * t660 * t665 * t674 + 0.73e2 / 0.388800e6 * t325 / t337 / t336 * t890 - 0.73e2 / 0.194400e6 * t666 * (0.972e3 * t829 + 0.15200e5 / 0.9e1 * t898) + 0.475e3 / 0.531441e6 * t113 * t340 * t896 + t344 * t827 * t287 / 0.120e3 + t123 * t349 / t350 / t283 / 0.32e2
  t920 = t359 ** 2
  t934 = f.my_piecewise3(t259, 0, -0.3e1 / 0.8e1 * t5 * t781 * t30 * t367 - t741 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t602 * t698 + t582 - t748 / 0.4e1 + 0.3e1 / 0.4e1 * t607 * t162 / t608 / t362 * t793 - 0.3e1 / 0.8e1 * t607 * t162 * t609 * (t914 * t360 + 0.4e1 / 0.9e1 * t688 * t691 * t118 * t658 + 0.2e1 / 0.27e2 * t355 / t920 * params.e * t898 - 0.22e2 / 0.27e2 * t693 * t877))
  d22 = 0.2e1 * t597 + 0.2e1 * t702 + t6 * (t772 + t934)
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
  t5 = t2 / t3
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
  t42 = t6 ** (0.1e1 / 0.3e1)
  t44 = 0.1e1 / r0
  t46 = 0.1e1 / tau0
  t48 = s0 * t44 * t46 / 0.8e1
  t49 = params.BLOC_b * s0
  t53 = params.BLOC_a + t49 * t44 * t46 / 0.8e1
  t54 = t48 ** t53
  t55 = params.c * t54
  t56 = s0 ** 2
  t57 = r0 ** 2
  t58 = 0.1e1 / t57
  t60 = tau0 ** 2
  t61 = 0.1e1 / t60
  t62 = t56 * t58 * t61
  t64 = 0.1e1 + t62 / 0.64e2
  t65 = t64 ** 2
  t66 = 0.1e1 / t65
  t69 = 6 ** (0.1e1 / 0.3e1)
  t70 = (0.10e2 / 0.81e2 + t55 * t66) * t69
  t71 = jnp.pi ** 2
  t72 = t71 ** (0.1e1 / 0.3e1)
  t73 = t72 ** 2
  t74 = 0.1e1 / t73
  t75 = t74 * s0
  t76 = r0 ** (0.1e1 / 0.3e1)
  t77 = t76 ** 2
  t79 = 0.1e1 / t77 / t57
  t80 = t75 * t79
  t86 = s0 * t79
  t88 = tau0 / t77 / r0 - t86 / 0.8e1
  t92 = 0.5e1 / 0.9e1 * t88 * t69 * t74 - 0.1e1
  t93 = params.b * t88
  t94 = t69 * t74
  t95 = t94 * t92
  t98 = 0.5e1 * t93 * t95 + 0.9e1
  t99 = jnp.sqrt(t98)
  t100 = 0.1e1 / t99
  t105 = 0.27e2 / 0.20e2 * t92 * t100 + t94 * t86 / 0.36e2
  t106 = t105 ** 2
  t109 = t69 ** 2
  t111 = 0.1e1 / t72 / t71
  t112 = t109 * t111
  t113 = t57 ** 2
  t114 = t113 * r0
  t116 = 0.1e1 / t76 / t114
  t120 = 0.50e2 * t112 * t56 * t116 + 0.162e3 * t62
  t121 = jnp.sqrt(t120)
  t125 = 0.1e1 / params.kappa * t109
  t126 = t111 * t56
  t130 = jnp.sqrt(params.e)
  t131 = t130 * t56
  t135 = params.e * params.mu
  t136 = t71 ** 2
  t137 = 0.1e1 / t136
  t139 = t137 * t56 * s0
  t140 = t113 ** 2
  t145 = t70 * t80 / 0.24e2 + 0.146e3 / 0.2025e4 * t106 - 0.73e2 / 0.97200e5 * t105 * t121 + 0.25e2 / 0.944784e6 * t125 * t126 * t116 + t131 * t58 * t61 / 0.720e3 + t135 * t139 / t140 / 0.2304e4
  t146 = t130 * t69
  t149 = 0.1e1 + t146 * t80 / 0.24e2
  t150 = t149 ** 2
  t151 = 0.1e1 / t150
  t153 = t145 * t151 + params.kappa
  t158 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t153)
  t164 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t165 = t42 ** 2
  t166 = 0.1e1 / t165
  t171 = t5 * t164
  t172 = params.kappa ** 2
  t173 = t42 * t172
  t174 = t153 ** 2
  t175 = 0.1e1 / t174
  t177 = jnp.log(t48)
  t182 = -t49 * t58 * t46 * t177 / 0.8e1 - t53 * t44
  t183 = t182 * t66
  t186 = 0.1e1 / t65 / t64
  t187 = t55 * t186
  t188 = t57 * r0
  t189 = 0.1e1 / t188
  t191 = t56 * t189 * t61
  t195 = (t55 * t183 + t187 * t191 / 0.16e2) * t69
  t199 = 0.1e1 / t77 / t188
  t200 = t75 * t199
  t205 = s0 * t199
  t207 = -0.5e1 / 0.3e1 * tau0 * t79 + t205 / 0.3e1
  t208 = t207 * t69
  t209 = t74 * t100
  t213 = 0.1e1 / t99 / t98
  t214 = t92 * t213
  t218 = t112 * t207
  t221 = 0.5e1 * params.b * t207 * t95 + 0.25e2 / 0.9e1 * t93 * t218
  t224 = t94 * t205
  t226 = 0.3e1 / 0.4e1 * t208 * t209 - 0.27e2 / 0.40e2 * t214 * t221 - 0.2e1 / 0.27e2 * t224
  t231 = 0.1e1 / t121
  t232 = t105 * t231
  t234 = t113 * t57
  t236 = 0.1e1 / t76 / t234
  t240 = -0.324e3 * t191 - 0.800e3 / 0.3e1 * t112 * t56 * t236
  t246 = t189 * t61
  t250 = 0.1e1 / t140 / r0
  t254 = t195 * t80 / 0.24e2 - t70 * t200 / 0.9e1 + 0.292e3 / 0.2025e4 * t105 * t226 - 0.73e2 / 0.97200e5 * t226 * t121 - 0.73e2 / 0.194400e6 * t232 * t240 - 0.25e2 / 0.177147e6 * t125 * t126 * t236 - t131 * t246 / 0.360e3 - t135 * t139 * t250 / 0.288e3
  t257 = 0.1e1 / t150 / t149
  t259 = t145 * t257 * t130
  t262 = t254 * t151 + 0.2e1 / 0.9e1 * t259 * t224
  t263 = t175 * t262
  t264 = t173 * t263
  t267 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t268 = t267 * f.p.zeta_threshold
  t270 = f.my_piecewise3(t20, t268, t21 * t19)
  t272 = 0.1e1 / t165 / t6
  t277 = t5 * t270
  t278 = t166 * t172
  t279 = t278 * t263
  t283 = 0.1e1 / t174 / t153
  t284 = t262 ** 2
  t285 = t283 * t284
  t286 = t173 * t285
  t289 = t182 ** 2
  t292 = t189 * t46
  t299 = t49 * t292 * t177 / 0.4e1 + t49 * t292 / 0.4e1 + t53 * t58
  t302 = t55 * t182
  t303 = t186 * t56
  t304 = t303 * t246
  t307 = t65 ** 2
  t308 = 0.1e1 / t307
  t309 = t55 * t308
  t310 = t56 ** 2
  t311 = 0.1e1 / t234
  t313 = t60 ** 2
  t314 = 0.1e1 / t313
  t318 = 0.1e1 / t113
  t320 = t56 * t318 * t61
  t324 = (t55 * t289 * t66 + t55 * t299 * t66 + t302 * t304 / 0.8e1 + 0.3e1 / 0.512e3 * t309 * t310 * t311 * t314 - 0.3e1 / 0.16e2 * t187 * t320) * t69
  t330 = 0.1e1 / t77 / t113
  t331 = t75 * t330
  t334 = t226 ** 2
  t338 = s0 * t330
  t340 = 0.40e2 / 0.9e1 * tau0 * t199 - 0.11e2 / 0.9e1 * t338
  t341 = t340 * t69
  t344 = t74 * t213
  t345 = t344 * t221
  t348 = t98 ** 2
  t350 = 0.1e1 / t99 / t348
  t351 = t92 * t350
  t352 = t221 ** 2
  t355 = params.b * t340
  t358 = t207 ** 2
  t365 = 0.5e1 * t355 * t95 + 0.50e2 / 0.9e1 * params.b * t358 * t112 + 0.25e2 / 0.9e1 * t93 * t112 * t340
  t368 = t94 * t338
  t370 = 0.3e1 / 0.4e1 * t341 * t209 - 0.3e1 / 0.4e1 * t208 * t345 + 0.81e2 / 0.80e2 * t351 * t352 - 0.27e2 / 0.40e2 * t214 * t365 + 0.22e2 / 0.81e2 * t368
  t375 = t226 * t231
  t379 = 0.1e1 / t121 / t120
  t380 = t105 * t379
  t381 = t240 ** 2
  t385 = t113 * t188
  t387 = 0.1e1 / t76 / t385
  t389 = t112 * t56 * t387
  t391 = 0.972e3 * t320 + 0.15200e5 / 0.9e1 * t389
  t397 = t318 * t61
  t405 = t324 * t80 / 0.24e2 - 0.2e1 / 0.9e1 * t195 * t200 + 0.11e2 / 0.27e2 * t70 * t331 + 0.292e3 / 0.2025e4 * t334 + 0.292e3 / 0.2025e4 * t105 * t370 - 0.73e2 / 0.97200e5 * t370 * t121 - 0.73e2 / 0.97200e5 * t375 * t240 + 0.73e2 / 0.388800e6 * t380 * t381 - 0.73e2 / 0.194400e6 * t232 * t391 + 0.475e3 / 0.531441e6 * t125 * t126 * t387 + t131 * t397 / 0.120e3 + t135 * t139 / t140 / t57 / 0.32e2
  t408 = t254 * t257 * t130
  t411 = t150 ** 2
  t412 = 0.1e1 / t411
  t414 = t145 * t412 * params.e
  t419 = t405 * t151 + 0.4e1 / 0.9e1 * t408 * t224 + 0.2e1 / 0.27e2 * t414 * t389 - 0.22e2 / 0.27e2 * t259 * t368
  t420 = t175 * t419
  t421 = t173 * t420
  t425 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t158 - t5 * t164 * t166 * t158 / 0.4e1 - 0.3e1 / 0.4e1 * t171 * t264 + t5 * t270 * t272 * t158 / 0.12e2 - t277 * t279 / 0.4e1 + 0.3e1 / 0.4e1 * t277 * t286 - 0.3e1 / 0.8e1 * t277 * t421)
  t427 = r1 <= f.p.dens_threshold
  t428 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t429 = 0.1e1 + t428
  t430 = t429 <= f.p.zeta_threshold
  t431 = t429 ** (0.1e1 / 0.3e1)
  t432 = t431 ** 2
  t433 = 0.1e1 / t432
  t435 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t436 = t435 ** 2
  t440 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t444 = f.my_piecewise3(t430, 0, 0.4e1 / 0.9e1 * t433 * t436 + 0.4e1 / 0.3e1 * t431 * t440)
  t446 = 0.1e1 / r1
  t448 = 0.1e1 / tau1
  t456 = (s2 * t446 * t448 / 0.8e1) ** (params.BLOC_a + params.BLOC_b * s2 * t446 * t448 / 0.8e1)
  t458 = s2 ** 2
  t459 = r1 ** 2
  t460 = 0.1e1 / t459
  t462 = tau1 ** 2
  t463 = 0.1e1 / t462
  t464 = t458 * t460 * t463
  t467 = (0.1e1 + t464 / 0.64e2) ** 2
  t473 = r1 ** (0.1e1 / 0.3e1)
  t474 = t473 ** 2
  t476 = 0.1e1 / t474 / t459
  t477 = t74 * s2 * t476
  t483 = s2 * t476
  t485 = tau1 / t474 / r1 - t483 / 0.8e1
  t489 = 0.5e1 / 0.9e1 * t485 * t69 * t74 - 0.1e1
  t495 = jnp.sqrt(0.5e1 * params.b * t485 * t94 * t489 + 0.9e1)
  t501 = 0.27e2 / 0.20e2 * t489 / t495 + t94 * t483 / 0.36e2
  t502 = t501 ** 2
  t505 = t459 ** 2
  t508 = 0.1e1 / t473 / t505 / r1
  t513 = jnp.sqrt(0.50e2 * t112 * t458 * t508 + 0.162e3 * t464)
  t526 = t505 ** 2
  t535 = (0.1e1 + t146 * t477 / 0.24e2) ** 2
  t543 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + ((0.10e2 / 0.81e2 + params.c * t456 / t467) * t69 * t477 / 0.24e2 + 0.146e3 / 0.2025e4 * t502 - 0.73e2 / 0.97200e5 * t501 * t513 + 0.25e2 / 0.944784e6 * t125 * t111 * t458 * t508 + t130 * t458 * t460 * t463 / 0.720e3 + t135 * t137 * t458 * s2 / t526 / 0.2304e4) / t535))
  t549 = f.my_piecewise3(t430, 0, 0.4e1 / 0.3e1 * t431 * t435)
  t555 = f.my_piecewise3(t430, t268, t431 * t429)
  t561 = f.my_piecewise3(t427, 0, -0.3e1 / 0.8e1 * t5 * t444 * t42 * t543 - t5 * t549 * t166 * t543 / 0.4e1 + t5 * t555 * t272 * t543 / 0.12e2)
  t566 = t174 ** 2
  t591 = 0.1e1 / t165 / t24
  t604 = t24 ** 2
  t608 = 0.6e1 * t33 - 0.6e1 * t16 / t604
  t609 = f.my_piecewise5(t10, 0, t14, 0, t608)
  t613 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t609)
  t634 = t318 * t46
  t671 = 0.1e1 / t114
  t673 = t56 * t671 * t61
  t685 = 0.1e1 / t77 / t114
  t693 = s0 * t685
  t695 = -0.440e3 / 0.27e2 * tau0 * t330 + 0.154e3 / 0.27e2 * t693
  t729 = t94 * t693
  t731 = 0.3e1 / 0.4e1 * t695 * t69 * t209 - 0.9e1 / 0.8e1 * t341 * t345 + 0.27e2 / 0.16e2 * t208 * t74 * t350 * t352 - 0.9e1 / 0.8e1 * t208 * t344 * t365 - 0.81e2 / 0.32e2 * t92 / t99 / t348 / t98 * t352 * t221 + 0.243e3 / 0.80e2 * t351 * t221 * t365 - 0.27e2 / 0.40e2 * t214 * (0.5e1 * params.b * t695 * t95 + 0.50e2 / 0.3e1 * t355 * t218 + 0.25e2 / 0.9e1 * t93 * t112 * t695) - 0.308e3 / 0.243e3 * t729
  t744 = t120 ** 2
  t756 = 0.1e1 / t76 / t140
  t758 = t112 * t56 * t756
  t771 = t139 / t140 / t188
  t774 = (t55 * t289 * t182 * t66 + 0.3e1 * t55 * t183 * t299 + 0.3e1 / 0.16e2 * t55 * t289 * t304 + t55 * (-0.3e1 / 0.4e1 * t49 * t634 * t177 - 0.9e1 / 0.8e1 * t49 * t634 - 0.2e1 * t53 * t189) * t66 + 0.3e1 / 0.16e2 * t55 * t299 * t304 + 0.9e1 / 0.512e3 * t302 * t308 * t310 * t311 * t314 - 0.9e1 / 0.16e2 * t302 * t303 * t397 + 0.3e1 / 0.4096e4 * t55 / t307 / t64 * t310 * t56 * t250 / t313 / t60 - 0.27e2 / 0.512e3 * t309 * t310 / t385 * t314 + 0.3e1 / 0.4e1 * t187 * t673) * t69 * t80 / 0.24e2 - t324 * t200 / 0.3e1 + 0.11e2 / 0.9e1 * t195 * t331 - 0.154e3 / 0.81e2 * t70 * t75 * t685 + 0.292e3 / 0.675e3 * t226 * t370 + 0.292e3 / 0.2025e4 * t105 * t731 - 0.73e2 / 0.97200e5 * t731 * t121 - 0.73e2 / 0.64800e5 * t370 * t231 * t240 + 0.73e2 / 0.129600e6 * t226 * t379 * t381 - 0.73e2 / 0.64800e5 * t375 * t391 - 0.73e2 / 0.259200e6 * t105 / t121 / t744 * t381 * t240 + 0.73e2 / 0.129600e6 * t380 * t240 * t391 - 0.73e2 / 0.194400e6 * t232 * (-0.3888e4 * t673 - 0.334400e6 / 0.27e2 * t758) - 0.10450e5 / 0.1594323e7 * t125 * t126 * t756 - t131 * t671 * t61 / 0.30e2 - 0.5e1 / 0.16e2 * t135 * t771
  t809 = 0.3e1 / 0.4e1 * t277 * t278 * t285 - 0.9e1 / 0.4e1 * t277 * t173 / t566 * t284 * t262 + 0.9e1 / 0.4e1 * t5 * t270 * t42 * t172 * t283 * t262 * t419 + 0.9e1 / 0.4e1 * t171 * t286 - 0.3e1 / 0.8e1 * t5 * t41 * t166 * t158 + t5 * t164 * t272 * t158 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t270 * t591 * t158 - 0.3e1 / 0.8e1 * t5 * t613 * t42 * t158 + t277 * t272 * t172 * t263 / 0.4e1 - 0.3e1 / 0.8e1 * t277 * t278 * t420 - 0.3e1 / 0.8e1 * t277 * t173 * t175 * (t774 * t151 + 0.2e1 / 0.3e1 * t405 * t257 * t130 * t224 + 0.2e1 / 0.9e1 * t254 * t412 * params.e * t389 - 0.22e2 / 0.9e1 * t408 * t368 + 0.16e2 / 0.81e2 * t145 / t411 / t149 * t130 * params.e * t771 - 0.22e2 / 0.27e2 * t414 * t758 + 0.308e3 / 0.81e2 * t259 * t729) - 0.9e1 / 0.8e1 * t5 * t41 * t264 - 0.3e1 / 0.4e1 * t171 * t279 - 0.9e1 / 0.8e1 * t171 * t421
  t810 = f.my_piecewise3(t1, 0, t809)
  t820 = f.my_piecewise5(t14, 0, t10, 0, -t608)
  t824 = f.my_piecewise3(t430, 0, -0.8e1 / 0.27e2 / t432 / t429 * t436 * t435 + 0.4e1 / 0.3e1 * t433 * t435 * t440 + 0.4e1 / 0.3e1 * t431 * t820)
  t842 = f.my_piecewise3(t427, 0, -0.3e1 / 0.8e1 * t5 * t824 * t42 * t543 - 0.3e1 / 0.8e1 * t5 * t444 * t166 * t543 + t5 * t549 * t272 * t543 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t555 * t591 * t543)
  d111 = 0.3e1 * t425 + 0.3e1 * t561 + t6 * (t810 + t842)

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
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
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
  t25 = -t16 * t23 + t7
  t26 = f.my_piecewise5(t10, 0, t14, 0, t25)
  t29 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t26)
  t30 = t5 * t29
  t31 = t6 ** (0.1e1 / 0.3e1)
  t32 = params.kappa ** 2
  t33 = t31 * t32
  t34 = 0.1e1 / r0
  t36 = 0.1e1 / tau0
  t38 = s0 * t34 * t36 / 0.8e1
  t39 = params.BLOC_b * s0
  t43 = params.BLOC_a + t39 * t34 * t36 / 0.8e1
  t44 = t38 ** t43
  t45 = params.c * t44
  t46 = s0 ** 2
  t47 = r0 ** 2
  t48 = 0.1e1 / t47
  t50 = tau0 ** 2
  t51 = 0.1e1 / t50
  t52 = t46 * t48 * t51
  t54 = 0.1e1 + t52 / 0.64e2
  t55 = t54 ** 2
  t56 = 0.1e1 / t55
  t59 = 6 ** (0.1e1 / 0.3e1)
  t60 = (0.10e2 / 0.81e2 + t45 * t56) * t59
  t61 = jnp.pi ** 2
  t62 = t61 ** (0.1e1 / 0.3e1)
  t63 = t62 ** 2
  t64 = 0.1e1 / t63
  t65 = t64 * s0
  t66 = r0 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t69 = 0.1e1 / t67 / t47
  t70 = t65 * t69
  t76 = s0 * t69
  t78 = tau0 / t67 / r0 - t76 / 0.8e1
  t82 = 0.5e1 / 0.9e1 * t78 * t59 * t64 - 0.1e1
  t83 = params.b * t78
  t84 = t59 * t64
  t85 = t84 * t82
  t88 = 0.5e1 * t83 * t85 + 0.9e1
  t89 = jnp.sqrt(t88)
  t90 = 0.1e1 / t89
  t95 = 0.27e2 / 0.20e2 * t82 * t90 + t84 * t76 / 0.36e2
  t96 = t95 ** 2
  t99 = t59 ** 2
  t101 = 0.1e1 / t62 / t61
  t102 = t99 * t101
  t103 = t47 ** 2
  t104 = t103 * r0
  t106 = 0.1e1 / t66 / t104
  t110 = 0.50e2 * t102 * t46 * t106 + 0.162e3 * t52
  t111 = jnp.sqrt(t110)
  t115 = 0.1e1 / params.kappa * t99
  t116 = t101 * t46
  t120 = jnp.sqrt(params.e)
  t121 = t120 * t46
  t125 = params.e * params.mu
  t126 = t61 ** 2
  t127 = 0.1e1 / t126
  t129 = t127 * t46 * s0
  t130 = t103 ** 2
  t131 = 0.1e1 / t130
  t135 = t60 * t70 / 0.24e2 + 0.146e3 / 0.2025e4 * t96 - 0.73e2 / 0.97200e5 * t95 * t111 + 0.25e2 / 0.944784e6 * t115 * t116 * t106 + t121 * t48 * t51 / 0.720e3 + t125 * t129 * t131 / 0.2304e4
  t136 = t120 * t59
  t139 = 0.1e1 + t136 * t70 / 0.24e2
  t140 = t139 ** 2
  t141 = 0.1e1 / t140
  t143 = t135 * t141 + params.kappa
  t144 = t143 ** 2
  t146 = 0.1e1 / t144 / t143
  t148 = jnp.log(t38)
  t153 = -t39 * t48 * t36 * t148 / 0.8e1 - t43 * t34
  t154 = t153 * t56
  t157 = 0.1e1 / t55 / t54
  t158 = t45 * t157
  t159 = t47 * r0
  t160 = 0.1e1 / t159
  t162 = t46 * t160 * t51
  t166 = (t45 * t154 + t158 * t162 / 0.16e2) * t59
  t170 = 0.1e1 / t67 / t159
  t171 = t65 * t170
  t176 = s0 * t170
  t178 = -0.5e1 / 0.3e1 * tau0 * t69 + t176 / 0.3e1
  t179 = t178 * t59
  t180 = t64 * t90
  t184 = 0.1e1 / t89 / t88
  t185 = t82 * t184
  t189 = t102 * t178
  t192 = 0.5e1 * params.b * t178 * t85 + 0.25e2 / 0.9e1 * t83 * t189
  t195 = t84 * t176
  t197 = 0.3e1 / 0.4e1 * t179 * t180 - 0.27e2 / 0.40e2 * t185 * t192 - 0.2e1 / 0.27e2 * t195
  t202 = 0.1e1 / t111
  t203 = t95 * t202
  t205 = t103 * t47
  t207 = 0.1e1 / t66 / t205
  t211 = -0.324e3 * t162 - 0.800e3 / 0.3e1 * t102 * t46 * t207
  t217 = t160 * t51
  t220 = t130 * r0
  t221 = 0.1e1 / t220
  t225 = t166 * t70 / 0.24e2 - t60 * t171 / 0.9e1 + 0.292e3 / 0.2025e4 * t95 * t197 - 0.73e2 / 0.97200e5 * t197 * t111 - 0.73e2 / 0.194400e6 * t203 * t211 - 0.25e2 / 0.177147e6 * t115 * t116 * t207 - t121 * t217 / 0.360e3 - t125 * t129 * t221 / 0.288e3
  t228 = 0.1e1 / t140 / t139
  t230 = t135 * t228 * t120
  t233 = t225 * t141 + 0.2e1 / 0.9e1 * t230 * t195
  t234 = t233 ** 2
  t235 = t146 * t234
  t236 = t33 * t235
  t239 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t240 = t239 * f.p.zeta_threshold
  t242 = f.my_piecewise3(t20, t240, t21 * t19)
  t243 = t5 * t242
  t244 = t31 ** 2
  t245 = 0.1e1 / t244
  t246 = t245 * t32
  t247 = t246 * t235
  t250 = t144 ** 2
  t251 = 0.1e1 / t250
  t253 = t251 * t234 * t233
  t254 = t33 * t253
  t258 = t5 * t242 * t31
  t259 = t32 * t146
  t260 = t153 ** 2
  t261 = t260 * t56
  t263 = t160 * t36
  t270 = t39 * t263 * t148 / 0.4e1 + t39 * t263 / 0.4e1 + t43 * t48
  t273 = t45 * t153
  t274 = t157 * t46
  t275 = t274 * t217
  t278 = t55 ** 2
  t279 = 0.1e1 / t278
  t280 = t45 * t279
  t281 = t46 ** 2
  t282 = 0.1e1 / t205
  t284 = t50 ** 2
  t285 = 0.1e1 / t284
  t289 = 0.1e1 / t103
  t291 = t46 * t289 * t51
  t295 = (t45 * t261 + t45 * t270 * t56 + t273 * t275 / 0.8e1 + 0.3e1 / 0.512e3 * t280 * t281 * t282 * t285 - 0.3e1 / 0.16e2 * t158 * t291) * t59
  t301 = 0.1e1 / t67 / t103
  t302 = t65 * t301
  t305 = t197 ** 2
  t309 = s0 * t301
  t311 = 0.40e2 / 0.9e1 * tau0 * t170 - 0.11e2 / 0.9e1 * t309
  t312 = t311 * t59
  t315 = t64 * t184
  t316 = t315 * t192
  t319 = t88 ** 2
  t321 = 0.1e1 / t89 / t319
  t322 = t82 * t321
  t323 = t192 ** 2
  t326 = params.b * t311
  t329 = t178 ** 2
  t336 = 0.5e1 * t326 * t85 + 0.50e2 / 0.9e1 * params.b * t329 * t102 + 0.25e2 / 0.9e1 * t83 * t102 * t311
  t339 = t84 * t309
  t341 = 0.3e1 / 0.4e1 * t312 * t180 - 0.3e1 / 0.4e1 * t179 * t316 + 0.81e2 / 0.80e2 * t322 * t323 - 0.27e2 / 0.40e2 * t185 * t336 + 0.22e2 / 0.81e2 * t339
  t346 = t197 * t202
  t350 = 0.1e1 / t111 / t110
  t351 = t95 * t350
  t352 = t211 ** 2
  t356 = t103 * t159
  t358 = 0.1e1 / t66 / t356
  t360 = t102 * t46 * t358
  t362 = 0.972e3 * t291 + 0.15200e5 / 0.9e1 * t360
  t368 = t289 * t51
  t372 = 0.1e1 / t130 / t47
  t376 = t295 * t70 / 0.24e2 - 0.2e1 / 0.9e1 * t166 * t171 + 0.11e2 / 0.27e2 * t60 * t302 + 0.292e3 / 0.2025e4 * t305 + 0.292e3 / 0.2025e4 * t95 * t341 - 0.73e2 / 0.97200e5 * t341 * t111 - 0.73e2 / 0.97200e5 * t346 * t211 + 0.73e2 / 0.388800e6 * t351 * t352 - 0.73e2 / 0.194400e6 * t203 * t362 + 0.475e3 / 0.531441e6 * t115 * t116 * t358 + t121 * t368 / 0.120e3 + t125 * t129 * t372 / 0.32e2
  t379 = t225 * t228 * t120
  t382 = t140 ** 2
  t383 = 0.1e1 / t382
  t385 = t135 * t383 * params.e
  t390 = t376 * t141 + 0.4e1 / 0.9e1 * t379 * t195 + 0.2e1 / 0.27e2 * t385 * t360 - 0.22e2 / 0.27e2 * t230 * t339
  t392 = t259 * t233 * t390
  t395 = t21 ** 2
  t396 = 0.1e1 / t395
  t397 = t26 ** 2
  t400 = t22 * t6
  t401 = 0.1e1 / t400
  t404 = 0.2e1 * t16 * t401 - 0.2e1 * t23
  t405 = f.my_piecewise5(t10, 0, t14, 0, t404)
  t409 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t396 * t397 + 0.4e1 / 0.3e1 * t21 * t405)
  t415 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t143)
  t420 = 0.1e1 / t244 / t6
  t426 = 0.1e1 / t244 / t22
  t432 = 0.1e1 / t395 / t19
  t436 = t396 * t26
  t439 = t22 ** 2
  t440 = 0.1e1 / t439
  t443 = -0.6e1 * t16 * t440 + 0.6e1 * t401
  t444 = f.my_piecewise5(t10, 0, t14, 0, t443)
  t448 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t432 * t397 * t26 + 0.4e1 / 0.3e1 * t436 * t405 + 0.4e1 / 0.3e1 * t21 * t444)
  t453 = t420 * t32
  t454 = 0.1e1 / t144
  t455 = t454 * t233
  t456 = t453 * t455
  t459 = t454 * t390
  t460 = t246 * t459
  t463 = t260 * t153
  t469 = t45 * t260
  t472 = t289 * t36
  t480 = -0.3e1 / 0.4e1 * t39 * t472 * t148 - 0.9e1 / 0.8e1 * t39 * t472 - 0.2e1 * t43 * t160
  t483 = t45 * t270
  t486 = t279 * t281
  t488 = t486 * t282 * t285
  t491 = t274 * t368
  t495 = 0.1e1 / t278 / t54
  t496 = t45 * t495
  t497 = t281 * t46
  t500 = 0.1e1 / t284 / t50
  t504 = 0.1e1 / t356
  t509 = 0.1e1 / t104
  t511 = t46 * t509 * t51
  t515 = (t45 * t463 * t56 + 0.3e1 * t45 * t154 * t270 + 0.3e1 / 0.16e2 * t469 * t275 + t45 * t480 * t56 + 0.3e1 / 0.16e2 * t483 * t275 + 0.9e1 / 0.512e3 * t273 * t488 - 0.9e1 / 0.16e2 * t273 * t491 + 0.3e1 / 0.4096e4 * t496 * t497 * t221 * t500 - 0.27e2 / 0.512e3 * t280 * t281 * t504 * t285 + 0.3e1 / 0.4e1 * t158 * t511) * t59
  t523 = 0.1e1 / t67 / t104
  t524 = t65 * t523
  t531 = s0 * t523
  t533 = -0.440e3 / 0.27e2 * tau0 * t301 + 0.154e3 / 0.27e2 * t531
  t534 = t533 * t59
  t540 = t64 * t321 * t323
  t543 = t315 * t336
  t548 = 0.1e1 / t89 / t319 / t88
  t549 = t82 * t548
  t550 = t323 * t192
  t556 = params.b * t533
  t564 = 0.5e1 * t556 * t85 + 0.50e2 / 0.3e1 * t326 * t189 + 0.25e2 / 0.9e1 * t83 * t102 * t533
  t567 = t84 * t531
  t569 = 0.3e1 / 0.4e1 * t534 * t180 - 0.9e1 / 0.8e1 * t312 * t316 + 0.27e2 / 0.16e2 * t179 * t540 - 0.9e1 / 0.8e1 * t179 * t543 - 0.81e2 / 0.32e2 * t549 * t550 + 0.243e3 / 0.80e2 * t322 * t192 * t336 - 0.27e2 / 0.40e2 * t185 * t564 - 0.308e3 / 0.243e3 * t567
  t574 = t341 * t202
  t577 = t197 * t350
  t582 = t110 ** 2
  t584 = 0.1e1 / t111 / t582
  t585 = t95 * t584
  t586 = t352 * t211
  t589 = t211 * t362
  t594 = 0.1e1 / t66 / t130
  t596 = t102 * t46 * t594
  t598 = -0.3888e4 * t511 - 0.334400e6 / 0.27e2 * t596
  t604 = t509 * t51
  t609 = t129 / t130 / t159
  t612 = t515 * t70 / 0.24e2 - t295 * t171 / 0.3e1 + 0.11e2 / 0.9e1 * t166 * t302 - 0.154e3 / 0.81e2 * t60 * t524 + 0.292e3 / 0.675e3 * t197 * t341 + 0.292e3 / 0.2025e4 * t95 * t569 - 0.73e2 / 0.97200e5 * t569 * t111 - 0.73e2 / 0.64800e5 * t574 * t211 + 0.73e2 / 0.129600e6 * t577 * t352 - 0.73e2 / 0.64800e5 * t346 * t362 - 0.73e2 / 0.259200e6 * t585 * t586 + 0.73e2 / 0.129600e6 * t351 * t589 - 0.73e2 / 0.194400e6 * t203 * t598 - 0.10450e5 / 0.1594323e7 * t115 * t116 * t594 - t121 * t604 / 0.30e2 - 0.5e1 / 0.16e2 * t125 * t609
  t615 = t376 * t228 * t120
  t619 = t225 * t383 * params.e
  t625 = 0.1e1 / t382 / t139
  t627 = t120 * params.e
  t628 = t135 * t625 * t627
  t635 = t612 * t141 + 0.2e1 / 0.3e1 * t615 * t195 + 0.2e1 / 0.9e1 * t619 * t360 - 0.22e2 / 0.9e1 * t379 * t339 + 0.16e2 / 0.81e2 * t628 * t609 - 0.22e2 / 0.27e2 * t385 * t596 + 0.308e3 / 0.81e2 * t230 * t567
  t636 = t454 * t635
  t637 = t33 * t636
  t640 = t5 * t409
  t641 = t33 * t455
  t644 = t246 * t455
  t647 = t33 * t459
  t650 = 0.9e1 / 0.4e1 * t30 * t236 + 0.3e1 / 0.4e1 * t243 * t247 - 0.9e1 / 0.4e1 * t243 * t254 + 0.9e1 / 0.4e1 * t258 * t392 - 0.3e1 / 0.8e1 * t5 * t409 * t245 * t415 + t5 * t29 * t420 * t415 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t242 * t426 * t415 - 0.3e1 / 0.8e1 * t5 * t448 * t31 * t415 + t243 * t456 / 0.4e1 - 0.3e1 / 0.8e1 * t243 * t460 - 0.3e1 / 0.8e1 * t243 * t637 - 0.9e1 / 0.8e1 * t640 * t641 - 0.3e1 / 0.4e1 * t30 * t644 - 0.9e1 / 0.8e1 * t30 * t647
  t651 = f.my_piecewise3(t1, 0, t650)
  t653 = r1 <= f.p.dens_threshold
  t654 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t655 = 0.1e1 + t654
  t656 = t655 <= f.p.zeta_threshold
  t657 = t655 ** (0.1e1 / 0.3e1)
  t658 = t657 ** 2
  t660 = 0.1e1 / t658 / t655
  t662 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t663 = t662 ** 2
  t667 = 0.1e1 / t658
  t668 = t667 * t662
  t670 = f.my_piecewise5(t14, 0, t10, 0, -t404)
  t674 = f.my_piecewise5(t14, 0, t10, 0, -t443)
  t678 = f.my_piecewise3(t656, 0, -0.8e1 / 0.27e2 * t660 * t663 * t662 + 0.4e1 / 0.3e1 * t668 * t670 + 0.4e1 / 0.3e1 * t657 * t674)
  t680 = 0.1e1 / r1
  t682 = 0.1e1 / tau1
  t690 = (s2 * t680 * t682 / 0.8e1) ** (params.BLOC_a + params.BLOC_b * s2 * t680 * t682 / 0.8e1)
  t692 = s2 ** 2
  t693 = r1 ** 2
  t694 = 0.1e1 / t693
  t696 = tau1 ** 2
  t697 = 0.1e1 / t696
  t698 = t692 * t694 * t697
  t701 = (0.1e1 + t698 / 0.64e2) ** 2
  t707 = r1 ** (0.1e1 / 0.3e1)
  t708 = t707 ** 2
  t710 = 0.1e1 / t708 / t693
  t711 = t64 * s2 * t710
  t717 = s2 * t710
  t719 = tau1 / t708 / r1 - t717 / 0.8e1
  t723 = 0.5e1 / 0.9e1 * t719 * t59 * t64 - 0.1e1
  t729 = jnp.sqrt(0.5e1 * params.b * t719 * t84 * t723 + 0.9e1)
  t735 = 0.27e2 / 0.20e2 * t723 / t729 + t84 * t717 / 0.36e2
  t736 = t735 ** 2
  t739 = t693 ** 2
  t742 = 0.1e1 / t707 / t739 / r1
  t747 = jnp.sqrt(0.50e2 * t102 * t692 * t742 + 0.162e3 * t698)
  t760 = t739 ** 2
  t769 = (0.1e1 + t136 * t711 / 0.24e2) ** 2
  t777 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + ((0.10e2 / 0.81e2 + params.c * t690 / t701) * t59 * t711 / 0.24e2 + 0.146e3 / 0.2025e4 * t736 - 0.73e2 / 0.97200e5 * t735 * t747 + 0.25e2 / 0.944784e6 * t115 * t101 * t692 * t742 + t120 * t692 * t694 * t697 / 0.720e3 + t125 * t127 * t692 * s2 / t760 / 0.2304e4) / t769))
  t786 = f.my_piecewise3(t656, 0, 0.4e1 / 0.9e1 * t667 * t663 + 0.4e1 / 0.3e1 * t657 * t670)
  t793 = f.my_piecewise3(t656, 0, 0.4e1 / 0.3e1 * t657 * t662)
  t799 = f.my_piecewise3(t656, t240, t657 * t655)
  t805 = f.my_piecewise3(t653, 0, -0.3e1 / 0.8e1 * t5 * t678 * t31 * t777 - 0.3e1 / 0.8e1 * t5 * t786 * t245 * t777 + t5 * t793 * t420 * t777 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t799 * t426 * t777)
  t837 = 0.1e1 / t244 / t400
  t842 = t19 ** 2
  t845 = t397 ** 2
  t851 = t405 ** 2
  t860 = -0.24e2 * t440 + 0.24e2 * t16 / t439 / t6
  t861 = f.my_piecewise5(t10, 0, t14, 0, t860)
  t865 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t395 / t842 * t845 - 0.16e2 / 0.9e1 * t432 * t397 * t405 + 0.4e1 / 0.3e1 * t396 * t851 + 0.16e2 / 0.9e1 * t436 * t444 + 0.4e1 / 0.3e1 * t21 * t861)
  t889 = t352 ** 2
  t895 = t362 ** 2
  t904 = t341 ** 2
  t911 = 0.1e1 / t67 / t205
  t912 = s0 * t911
  t914 = 0.6160e4 / 0.81e2 * tau0 * t523 - 0.2618e4 / 0.81e2 * t912
  t936 = t319 ** 2
  t940 = t323 ** 2
  t946 = t336 ** 2
  t957 = t311 ** 2
  t967 = t84 * t912
  t969 = 0.3e1 / 0.4e1 * t914 * t59 * t180 - 0.3e1 / 0.2e1 * t534 * t316 + 0.27e2 / 0.8e1 * t312 * t540 - 0.9e1 / 0.4e1 * t312 * t543 - 0.45e2 / 0.8e1 * t179 * t64 * t548 * t550 + 0.27e2 / 0.4e1 * t179 * t64 * t321 * t192 * t336 - 0.3e1 / 0.2e1 * t179 * t315 * t564 + 0.567e3 / 0.64e2 * t82 / t89 / t936 * t940 - 0.243e3 / 0.16e2 * t549 * t323 * t336 + 0.243e3 / 0.80e2 * t322 * t946 + 0.81e2 / 0.20e2 * t322 * t192 * t564 - 0.27e2 / 0.40e2 * t185 * (0.5e1 * params.b * t914 * t85 + 0.200e3 / 0.9e1 * t556 * t189 + 0.50e2 / 0.3e1 * params.b * t957 * t102 + 0.25e2 / 0.9e1 * t83 * t102 * t914) + 0.5236e4 / 0.729e3 * t967
  t972 = 0.73e2 / 0.64800e5 * t341 * t350 * t352 - 0.73e2 / 0.64800e5 * t197 * t584 * t586 + 0.73e2 / 0.32400e5 * t577 * t589 + 0.73e2 / 0.103680e6 * t95 / t111 / t582 / t110 * t889 - 0.73e2 / 0.43200e5 * t585 * t352 * t362 + 0.73e2 / 0.129600e6 * t351 * t895 + 0.73e2 / 0.97200e5 * t351 * t211 * t598 + t121 * t282 * t51 / 0.6e1 + 0.292e3 / 0.675e3 * t904 + 0.1168e4 / 0.2025e4 * t197 * t569 + 0.292e3 / 0.2025e4 * t95 * t969
  t992 = t46 * t282 * t51
  t995 = 0.1e1 / t66 / t220
  t997 = t102 * t46 * t995
  t1006 = 0.1e1 / t130 / t103
  t1007 = t129 * t1006
  t1010 = t509 * t36
  t1041 = t281 ** 2
  t1043 = t284 ** 2
  t1051 = t260 ** 2
  t1054 = t270 ** 2
  t1086 = t45 * (0.3e1 * t39 * t1010 * t148 + 0.11e2 / 0.2e1 * t39 * t1010 + 0.6e1 * t43 * t289) * t56 - 0.27e2 / 0.128e3 * t273 * t486 * t504 * t285 + 0.3e1 * t273 * t274 * t604 + 0.3e1 / 0.4e1 * t45 * t153 * t157 * t270 * t46 * t217 - 0.9e1 / 0.8e1 * t469 * t491 - 0.9e1 / 0.8e1 * t483 * t491 + 0.15e2 / 0.131072e6 * t45 / t278 / t55 * t1041 * t1006 / t1043 + 0.6e1 * t45 * t261 * t270 + t45 * t1051 * t56 + 0.3e1 * t45 * t1054 * t56 + 0.4e1 * t45 * t154 * t480 + t45 * t463 * t275 / 0.4e1 + 0.9e1 / 0.256e3 * t469 * t488 + t45 * t480 * t275 / 0.4e1 + 0.9e1 / 0.256e3 * t483 * t488 + 0.3e1 / 0.1024e4 * t273 * t495 * t497 * t221 * t500 - 0.27e2 / 0.2048e4 * t496 * t497 * t372 * t500 + 0.225e3 / 0.512e3 * t280 * t281 * t131 * t285 - 0.15e2 / 0.4e1 * t158 * t992
  t1090 = -0.73e2 / 0.97200e5 * t969 * t111 - 0.4e1 / 0.9e1 * t515 * t171 + 0.22e2 / 0.9e1 * t295 * t302 - 0.616e3 / 0.81e2 * t166 * t524 + 0.2618e4 / 0.243e3 * t60 * t65 * t911 - 0.73e2 / 0.48600e5 * t569 * t202 * t211 - 0.73e2 / 0.32400e5 * t574 * t362 - 0.73e2 / 0.48600e5 * t346 * t598 - 0.73e2 / 0.194400e6 * t203 * (0.19440e5 * t992 + 0.8360000e7 / 0.81e2 * t997) + 0.261250e6 / 0.4782969e7 * t115 * t116 * t995 + 0.55e2 / 0.16e2 * t125 * t1007 + t1086 * t59 * t70 / 0.24e2
  t1114 = params.e ** 2
  t1130 = (t972 + t1090) * t141 + 0.8e1 / 0.9e1 * t612 * t228 * t120 * t195 + 0.4e1 / 0.9e1 * t376 * t383 * params.e * t360 - 0.44e2 / 0.9e1 * t615 * t339 + 0.64e2 / 0.81e2 * t225 * t625 * t627 * t609 - 0.88e2 / 0.27e2 * t619 * t596 + 0.1232e4 / 0.81e2 * t379 * t567 + 0.80e2 / 0.729e3 * t135 / t382 / t140 * t1114 * t127 * t281 / t67 / t130 / t205 * t84 - 0.352e3 / 0.81e2 * t628 * t1007 + 0.1958e4 / 0.243e3 * t385 * t997 - 0.5236e4 / 0.243e3 * t230 * t967
  t1137 = -0.27e2 / 0.2e1 * t258 * t32 * t251 * t234 * t390 + 0.3e1 * t258 * t259 * t233 * t635 + 0.3e1 * t5 * t242 * t245 * t392 + 0.9e1 * t5 * t29 * t31 * t392 - t5 * t448 * t245 * t415 / 0.2e1 + t5 * t409 * t420 * t415 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t29 * t426 * t415 + 0.10e2 / 0.27e2 * t5 * t242 * t837 * t415 - 0.3e1 / 0.8e1 * t5 * t865 * t31 * t415 - 0.5e1 / 0.9e1 * t243 * t426 * t32 * t455 - 0.3e1 / 0.2e1 * t5 * t448 * t641 - 0.3e1 / 0.8e1 * t243 * t33 * t454 * t1130 + 0.9e1 / 0.2e1 * t640 * t236
  t1150 = t390 ** 2
  t1162 = t234 ** 2
  t1174 = -0.3e1 / 0.2e1 * t640 * t644 + t30 * t456 - 0.3e1 / 0.2e1 * t30 * t637 - t243 * t246 * t636 / 0.2e1 - 0.3e1 / 0.2e1 * t30 * t460 - 0.9e1 / 0.4e1 * t640 * t647 + 0.9e1 / 0.4e1 * t243 * t33 * t146 * t1150 - t243 * t453 * t235 - 0.3e1 * t243 * t246 * t253 + 0.9e1 * t243 * t33 / t250 / t143 * t1162 + 0.3e1 * t30 * t247 - 0.9e1 * t30 * t254 + t243 * t453 * t459 / 0.2e1
  t1176 = f.my_piecewise3(t1, 0, t1137 + t1174)
  t1177 = t655 ** 2
  t1180 = t663 ** 2
  t1186 = t670 ** 2
  t1192 = f.my_piecewise5(t14, 0, t10, 0, -t860)
  t1196 = f.my_piecewise3(t656, 0, 0.40e2 / 0.81e2 / t658 / t1177 * t1180 - 0.16e2 / 0.9e1 * t660 * t663 * t670 + 0.4e1 / 0.3e1 * t667 * t1186 + 0.16e2 / 0.9e1 * t668 * t674 + 0.4e1 / 0.3e1 * t657 * t1192)
  t1218 = f.my_piecewise3(t653, 0, -0.3e1 / 0.8e1 * t5 * t1196 * t31 * t777 - t5 * t678 * t245 * t777 / 0.2e1 + t5 * t786 * t420 * t777 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t793 * t426 * t777 + 0.10e2 / 0.27e2 * t5 * t799 * t837 * t777)
  d1111 = 0.4e1 * t651 + 0.4e1 * t805 + t6 * (t1176 + t1218)

  res = {'v4rho4': d1111}
  return res
