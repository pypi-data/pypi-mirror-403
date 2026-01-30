"""Generated from mgga_x_rtpss.mpl."""

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

  tpss_ff = lambda z=None: 2

  tpss_kappa = lambda x=None, t=None: params_kappa

  tpss_p = lambda x: X2S ** 2 * x ** 2

  tpss_z = lambda x, t: x ** 2 / (8 * t)

  tpss_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tpss_fxden = lambda x: (1 + jnp.sqrt(params_e) * tpss_p(x)) ** 2

  tpss_qb = lambda x, t: 9 / 20 * (tpss_alpha(x, t) - 1) / jnp.sqrt(1 + params_b * tpss_alpha(x, t) * (tpss_alpha(x, t) - 1)) + 2 * tpss_p(x) / 3

  tpss_fxnum = lambda x, t: +(MU_GE + params_c * tpss_z(x, t) ** tpss_ff(tpss_z(x, t)) / (1 + tpss_z(x, t) ** 2) ** 2) * tpss_p(x) + 146 / 2025 * tpss_qb(x, t) ** 2 - 73 / 405 * tpss_qb(x, t) * jnp.sqrt(1 / 2 * (9 / 25 * tpss_z(x, t) ** 2 + tpss_p(x) ** 2)) + MU_GE ** 2 / tpss_kappa(x, t) * tpss_p(x) ** 2 + 2 * jnp.sqrt(params_e) * MU_GE * 9 / 25 * tpss_z(x, t) ** 2 + params_e * params_mu * tpss_p(x) ** 3

  tpss_fx = lambda x, t: tpss_fxnum(x, t) / tpss_fxden(x)

  rtpss_f = lambda x, u, t: 1 + tpss_kappa(x, t) * (1 - jnp.exp(-tpss_fx(x, t) / tpss_kappa(x, t)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, rtpss_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  tpss_ff = lambda z=None: 2

  tpss_kappa = lambda x=None, t=None: params_kappa

  tpss_p = lambda x: X2S ** 2 * x ** 2

  tpss_z = lambda x, t: x ** 2 / (8 * t)

  tpss_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tpss_fxden = lambda x: (1 + jnp.sqrt(params_e) * tpss_p(x)) ** 2

  tpss_qb = lambda x, t: 9 / 20 * (tpss_alpha(x, t) - 1) / jnp.sqrt(1 + params_b * tpss_alpha(x, t) * (tpss_alpha(x, t) - 1)) + 2 * tpss_p(x) / 3

  tpss_fxnum = lambda x, t: +(MU_GE + params_c * tpss_z(x, t) ** tpss_ff(tpss_z(x, t)) / (1 + tpss_z(x, t) ** 2) ** 2) * tpss_p(x) + 146 / 2025 * tpss_qb(x, t) ** 2 - 73 / 405 * tpss_qb(x, t) * jnp.sqrt(1 / 2 * (9 / 25 * tpss_z(x, t) ** 2 + tpss_p(x) ** 2)) + MU_GE ** 2 / tpss_kappa(x, t) * tpss_p(x) ** 2 + 2 * jnp.sqrt(params_e) * MU_GE * 9 / 25 * tpss_z(x, t) ** 2 + params_e * params_mu * tpss_p(x) ** 3

  tpss_fx = lambda x, t: tpss_fxnum(x, t) / tpss_fxden(x)

  rtpss_f = lambda x, u, t: 1 + tpss_kappa(x, t) * (1 - jnp.exp(-tpss_fx(x, t) / tpss_kappa(x, t)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, rtpss_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  tpss_ff = lambda z=None: 2

  tpss_kappa = lambda x=None, t=None: params_kappa

  tpss_p = lambda x: X2S ** 2 * x ** 2

  tpss_z = lambda x, t: x ** 2 / (8 * t)

  tpss_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tpss_fxden = lambda x: (1 + jnp.sqrt(params_e) * tpss_p(x)) ** 2

  tpss_qb = lambda x, t: 9 / 20 * (tpss_alpha(x, t) - 1) / jnp.sqrt(1 + params_b * tpss_alpha(x, t) * (tpss_alpha(x, t) - 1)) + 2 * tpss_p(x) / 3

  tpss_fxnum = lambda x, t: +(MU_GE + params_c * tpss_z(x, t) ** tpss_ff(tpss_z(x, t)) / (1 + tpss_z(x, t) ** 2) ** 2) * tpss_p(x) + 146 / 2025 * tpss_qb(x, t) ** 2 - 73 / 405 * tpss_qb(x, t) * jnp.sqrt(1 / 2 * (9 / 25 * tpss_z(x, t) ** 2 + tpss_p(x) ** 2)) + MU_GE ** 2 / tpss_kappa(x, t) * tpss_p(x) ** 2 + 2 * jnp.sqrt(params_e) * MU_GE * 9 / 25 * tpss_z(x, t) ** 2 + params_e * params_mu * tpss_p(x) ** 3

  tpss_fx = lambda x, t: tpss_fxnum(x, t) / tpss_fxden(x)

  rtpss_f = lambda x, u, t: 1 + tpss_kappa(x, t) * (1 - jnp.exp(-tpss_fx(x, t) / tpss_kappa(x, t)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, rtpss_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t28 = s0 ** 2
  t29 = params.c * t28
  t30 = r0 ** 2
  t31 = 0.1e1 / t30
  t32 = tau0 ** 2
  t33 = 0.1e1 / t32
  t34 = t31 * t33
  t35 = t28 * t31
  t36 = t35 * t33
  t38 = 0.1e1 + t36 / 0.64e2
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t41 = t34 * t40
  t45 = 6 ** (0.1e1 / 0.3e1)
  t46 = (0.10e2 / 0.81e2 + t29 * t41 / 0.64e2) * t45
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t51 = t50 * s0
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t55 = 0.1e1 / t53 / t30
  t56 = t51 * t55
  t60 = 0.1e1 / t53 / r0
  t62 = s0 * t55
  t64 = tau0 * t60 - t62 / 0.8e1
  t66 = t64 * t45 * t50
  t68 = t66 / 0.4e1 - 0.9e1 / 0.20e2
  t69 = params.b * t64
  t70 = t45 * t50
  t73 = t70 * (0.5e1 / 0.9e1 * t66 - 0.1e1)
  t76 = 0.5e1 * t69 * t73 + 0.9e1
  t77 = jnp.sqrt(t76)
  t78 = 0.1e1 / t77
  t79 = t68 * t78
  t81 = t70 * t62
  t83 = 0.3e1 * t79 + t81 / 0.36e2
  t84 = t83 ** 2
  t88 = 0.73e2 / 0.135e3 * t79 + 0.73e2 / 0.14580e5 * t81
  t90 = t45 ** 2
  t92 = 0.1e1 / t48 / t47
  t93 = t90 * t92
  t94 = t30 ** 2
  t95 = t94 * r0
  t97 = 0.1e1 / t52 / t95
  t102 = jnp.sqrt(0.50e2 * t93 * t28 * t97 + 0.162e3 * t36)
  t105 = 0.1e1 / params.kappa
  t106 = t105 * t90
  t107 = t92 * t28
  t111 = jnp.sqrt(params.e)
  t112 = t111 * t28
  t115 = params.e * params.mu
  t116 = t47 ** 2
  t117 = 0.1e1 / t116
  t118 = t28 * s0
  t119 = t117 * t118
  t120 = t94 ** 2
  t121 = 0.1e1 / t120
  t125 = t46 * t56 / 0.24e2 + 0.146e3 / 0.2025e4 * t84 - t88 * t102 / 0.240e3 + 0.25e2 / 0.944784e6 * t106 * t107 * t97 + t112 * t34 / 0.720e3 + t115 * t119 * t121 / 0.2304e4
  t126 = t111 * t45
  t129 = 0.1e1 + t126 * t56 / 0.24e2
  t130 = t129 ** 2
  t131 = 0.1e1 / t130
  t134 = jnp.exp(-t125 * t131 * t105)
  t137 = 0.1e1 + params.kappa * (0.1e1 - t134)
  t141 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t137)
  t142 = r1 <= f.p.dens_threshold
  t143 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t144 = 0.1e1 + t143
  t145 = t144 <= f.p.zeta_threshold
  t146 = t144 ** (0.1e1 / 0.3e1)
  t148 = f.my_piecewise3(t145, t22, t146 * t144)
  t150 = s2 ** 2
  t151 = params.c * t150
  t152 = r1 ** 2
  t153 = 0.1e1 / t152
  t154 = tau1 ** 2
  t155 = 0.1e1 / t154
  t156 = t153 * t155
  t157 = t150 * t153
  t158 = t157 * t155
  t160 = 0.1e1 + t158 / 0.64e2
  t161 = t160 ** 2
  t162 = 0.1e1 / t161
  t163 = t156 * t162
  t167 = (0.10e2 / 0.81e2 + t151 * t163 / 0.64e2) * t45
  t168 = t50 * s2
  t169 = r1 ** (0.1e1 / 0.3e1)
  t170 = t169 ** 2
  t172 = 0.1e1 / t170 / t152
  t173 = t168 * t172
  t177 = 0.1e1 / t170 / r1
  t179 = s2 * t172
  t181 = tau1 * t177 - t179 / 0.8e1
  t183 = t181 * t45 * t50
  t185 = t183 / 0.4e1 - 0.9e1 / 0.20e2
  t186 = params.b * t181
  t189 = t70 * (0.5e1 / 0.9e1 * t183 - 0.1e1)
  t192 = 0.5e1 * t186 * t189 + 0.9e1
  t193 = jnp.sqrt(t192)
  t194 = 0.1e1 / t193
  t195 = t185 * t194
  t197 = t70 * t179
  t199 = 0.3e1 * t195 + t197 / 0.36e2
  t200 = t199 ** 2
  t204 = 0.73e2 / 0.135e3 * t195 + 0.73e2 / 0.14580e5 * t197
  t206 = t152 ** 2
  t207 = t206 * r1
  t209 = 0.1e1 / t169 / t207
  t214 = jnp.sqrt(0.50e2 * t93 * t150 * t209 + 0.162e3 * t158)
  t217 = t92 * t150
  t221 = t111 * t150
  t224 = t150 * s2
  t225 = t117 * t224
  t226 = t206 ** 2
  t227 = 0.1e1 / t226
  t231 = t167 * t173 / 0.24e2 + 0.146e3 / 0.2025e4 * t200 - t204 * t214 / 0.240e3 + 0.25e2 / 0.944784e6 * t106 * t217 * t209 + t221 * t156 / 0.720e3 + t115 * t225 * t227 / 0.2304e4
  t234 = 0.1e1 + t126 * t173 / 0.24e2
  t235 = t234 ** 2
  t236 = 0.1e1 / t235
  t239 = jnp.exp(-t231 * t236 * t105)
  t242 = 0.1e1 + params.kappa * (0.1e1 - t239)
  t246 = f.my_piecewise3(t142, 0, -0.3e1 / 0.8e1 * t5 * t148 * t26 * t242)
  t247 = t6 ** 2
  t249 = t16 / t247
  t250 = t7 - t249
  t251 = f.my_piecewise5(t10, 0, t14, 0, t250)
  t254 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t251)
  t259 = t26 ** 2
  t260 = 0.1e1 / t259
  t264 = t5 * t25 * t260 * t137 / 0.8e1
  t265 = t5 * t25
  t266 = t26 * params.kappa
  t267 = t30 * r0
  t268 = 0.1e1 / t267
  t269 = t268 * t33
  t273 = t28 ** 2
  t274 = params.c * t273
  t276 = t32 ** 2
  t277 = 0.1e1 / t276
  t280 = 0.1e1 / t39 / t38
  t289 = 0.1e1 / t53 / t267
  t295 = s0 * t289
  t297 = -0.5e1 / 0.3e1 * tau0 * t55 + t295 / 0.3e1
  t299 = t50 * t78
  t300 = t297 * t45 * t299
  t304 = t68 / t77 / t76
  t312 = t304 * (0.5e1 * params.b * t297 * t73 + 0.25e2 / 0.9e1 * t69 * t93 * t297)
  t314 = t70 * t295
  t326 = t88 / t102
  t332 = 0.1e1 / t52 / t94 / t30
  t354 = t125 / t130 / t129
  t355 = t105 * t111
  t365 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t254 * t26 * t137 - t264 + 0.3e1 / 0.8e1 * t265 * t266 * (-((-t29 * t269 * t40 / 0.32e2 + t274 / t95 * t277 * t280 / 0.1024e4) * t45 * t56 / 0.24e2 - t46 * t51 * t289 / 0.9e1 + 0.292e3 / 0.2025e4 * t83 * (0.3e1 / 0.4e1 * t300 - 0.3e1 / 0.2e1 * t312 - 0.2e1 / 0.27e2 * t314) - (0.73e2 / 0.540e3 * t300 - 0.73e2 / 0.270e3 * t312 - 0.146e3 / 0.10935e5 * t314) * t102 / 0.240e3 - t326 * (-0.324e3 * t28 * t268 * t33 - 0.800e3 / 0.3e1 * t93 * t28 * t332) / 0.480e3 - 0.25e2 / 0.177147e6 * t106 * t107 * t332 - t112 * t269 / 0.360e3 - t115 * t119 / t120 / r0 / 0.288e3) * t131 * t105 - 0.2e1 / 0.9e1 * t354 * t355 * t314) * t134)
  t367 = f.my_piecewise5(t14, 0, t10, 0, -t250)
  t370 = f.my_piecewise3(t145, 0, 0.4e1 / 0.3e1 * t146 * t367)
  t378 = t5 * t148 * t260 * t242 / 0.8e1
  t380 = f.my_piecewise3(t142, 0, -0.3e1 / 0.8e1 * t5 * t370 * t26 * t242 - t378)
  vrho_0_ = t141 + t246 + t6 * (t365 + t380)
  t383 = -t7 - t249
  t384 = f.my_piecewise5(t10, 0, t14, 0, t383)
  t387 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t384)
  t393 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t387 * t26 * t137 - t264)
  t395 = f.my_piecewise5(t14, 0, t10, 0, -t383)
  t398 = f.my_piecewise3(t145, 0, 0.4e1 / 0.3e1 * t146 * t395)
  t403 = t5 * t148
  t404 = t152 * r1
  t405 = 0.1e1 / t404
  t406 = t405 * t155
  t410 = t150 ** 2
  t411 = params.c * t410
  t413 = t154 ** 2
  t414 = 0.1e1 / t413
  t417 = 0.1e1 / t161 / t160
  t426 = 0.1e1 / t170 / t404
  t432 = s2 * t426
  t434 = -0.5e1 / 0.3e1 * tau1 * t172 + t432 / 0.3e1
  t436 = t50 * t194
  t437 = t434 * t45 * t436
  t441 = t185 / t193 / t192
  t449 = t441 * (0.5e1 * params.b * t434 * t189 + 0.25e2 / 0.9e1 * t186 * t93 * t434)
  t451 = t70 * t432
  t463 = t204 / t214
  t469 = 0.1e1 / t169 / t206 / t152
  t491 = t231 / t235 / t234
  t501 = f.my_piecewise3(t142, 0, -0.3e1 / 0.8e1 * t5 * t398 * t26 * t242 - t378 + 0.3e1 / 0.8e1 * t403 * t266 * (-((-t151 * t406 * t162 / 0.32e2 + t411 / t207 * t414 * t417 / 0.1024e4) * t45 * t173 / 0.24e2 - t167 * t168 * t426 / 0.9e1 + 0.292e3 / 0.2025e4 * t199 * (0.3e1 / 0.4e1 * t437 - 0.3e1 / 0.2e1 * t449 - 0.2e1 / 0.27e2 * t451) - (0.73e2 / 0.540e3 * t437 - 0.73e2 / 0.270e3 * t449 - 0.146e3 / 0.10935e5 * t451) * t214 / 0.240e3 - t463 * (-0.324e3 * t150 * t405 * t155 - 0.800e3 / 0.3e1 * t93 * t150 * t469) / 0.480e3 - 0.25e2 / 0.177147e6 * t106 * t217 * t469 - t221 * t406 / 0.360e3 - t115 * t225 / t226 / r1 / 0.288e3) * t236 * t105 - 0.2e1 / 0.9e1 * t491 * t355 * t451) * t239)
  vrho_1_ = t141 + t246 + t6 * (t393 + t501)
  t508 = 0.1e1 / t94
  t517 = t50 * t55
  t520 = t55 * t45
  t521 = t520 * t299
  t530 = t304 * (-0.5e1 / 0.8e1 * params.b * t55 * t73 - 0.25e2 / 0.72e2 * t69 * t93 * t55)
  t532 = t520 * t50
  t575 = f.my_piecewise3(t1, 0, 0.3e1 / 0.8e1 * t265 * t266 * (-((params.c * s0 * t41 / 0.32e2 - params.c * t118 * t508 * t277 * t280 / 0.1024e4) * t45 * t56 / 0.24e2 + t46 * t517 / 0.24e2 + 0.292e3 / 0.2025e4 * t83 * (-0.3e1 / 0.32e2 * t521 - 0.3e1 / 0.2e1 * t530 + t532 / 0.36e2) - (-0.73e2 / 0.4320e4 * t521 - 0.73e2 / 0.270e3 * t530 + 0.73e2 / 0.14580e5 * t532) * t102 / 0.240e3 - t326 * (0.324e3 * s0 * t31 * t33 + 0.100e3 * t93 * s0 * t97) / 0.480e3 + 0.25e2 / 0.472392e6 * t106 * t92 * s0 * t97 + t111 * s0 * t34 / 0.360e3 + t115 * t117 * t28 * t121 / 0.768e3) * t131 * t105 + t354 * t105 * t126 * t517 / 0.12e2) * t134)
  vsigma_0_ = t6 * t575
  vsigma_1_ = 0.0e0
  t580 = 0.1e1 / t206
  t589 = t50 * t172
  t592 = t172 * t45
  t593 = t592 * t436
  t602 = t441 * (-0.5e1 / 0.8e1 * params.b * t172 * t189 - 0.25e2 / 0.72e2 * t186 * t93 * t172)
  t604 = t592 * t50
  t647 = f.my_piecewise3(t142, 0, 0.3e1 / 0.8e1 * t403 * t266 * (-((params.c * s2 * t163 / 0.32e2 - params.c * t224 * t580 * t414 * t417 / 0.1024e4) * t45 * t173 / 0.24e2 + t167 * t589 / 0.24e2 + 0.292e3 / 0.2025e4 * t199 * (-0.3e1 / 0.32e2 * t593 - 0.3e1 / 0.2e1 * t602 + t604 / 0.36e2) - (-0.73e2 / 0.4320e4 * t593 - 0.73e2 / 0.270e3 * t602 + 0.73e2 / 0.14580e5 * t604) * t214 / 0.240e3 - t463 * (0.324e3 * s2 * t153 * t155 + 0.100e3 * t93 * s2 * t209) / 0.480e3 + 0.25e2 / 0.472392e6 * t106 * t92 * s2 * t209 + t111 * s2 * t156 / 0.360e3 + t115 * t117 * t150 * t227 / 0.768e3) * t236 * t105 + t491 * t105 * t126 * t589 / 0.12e2) * t239)
  vsigma_2_ = t6 * t647
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t649 = 0.1e1 / t32 / tau0
  t650 = t31 * t649
  t665 = t60 * t45 * t299
  t674 = t304 * (0.5e1 * params.b * t60 * t73 + 0.25e2 / 0.9e1 * t69 * t93 * t60)
  t695 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t265 * t26 * ((-t29 * t650 * t40 / 0.32e2 + t274 * t508 / t276 / tau0 * t280 / 0.1024e4) * t45 * t56 / 0.24e2 + 0.292e3 / 0.2025e4 * t83 * (0.3e1 / 0.4e1 * t665 - 0.3e1 / 0.2e1 * t674) - (0.73e2 / 0.540e3 * t665 - 0.73e2 / 0.270e3 * t674) * t102 / 0.240e3 + 0.27e2 / 0.40e2 * t326 * t35 * t649 - t112 * t650 / 0.360e3) * t131 * t134)
  vtau_0_ = t6 * t695
  t697 = 0.1e1 / t154 / tau1
  t698 = t153 * t697
  t713 = t177 * t45 * t436
  t722 = t441 * (0.5e1 * params.b * t177 * t189 + 0.25e2 / 0.9e1 * t186 * t93 * t177)
  t743 = f.my_piecewise3(t142, 0, -0.3e1 / 0.8e1 * t403 * t26 * ((-t151 * t698 * t162 / 0.32e2 + t411 * t580 / t413 / tau1 * t417 / 0.1024e4) * t45 * t173 / 0.24e2 + 0.292e3 / 0.2025e4 * t199 * (0.3e1 / 0.4e1 * t713 - 0.3e1 / 0.2e1 * t722) - (0.73e2 / 0.540e3 * t713 - 0.73e2 / 0.270e3 * t722) * t214 / 0.240e3 + 0.27e2 / 0.40e2 * t463 * t157 * t697 - t221 * t698 / 0.360e3) * t236 * t239)
  vtau_1_ = t6 * t743
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

  tpss_ff = lambda z=None: 2

  tpss_kappa = lambda x=None, t=None: params_kappa

  tpss_p = lambda x: X2S ** 2 * x ** 2

  tpss_z = lambda x, t: x ** 2 / (8 * t)

  tpss_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tpss_fxden = lambda x: (1 + jnp.sqrt(params_e) * tpss_p(x)) ** 2

  tpss_qb = lambda x, t: 9 / 20 * (tpss_alpha(x, t) - 1) / jnp.sqrt(1 + params_b * tpss_alpha(x, t) * (tpss_alpha(x, t) - 1)) + 2 * tpss_p(x) / 3

  tpss_fxnum = lambda x, t: +(MU_GE + params_c * tpss_z(x, t) ** tpss_ff(tpss_z(x, t)) / (1 + tpss_z(x, t) ** 2) ** 2) * tpss_p(x) + 146 / 2025 * tpss_qb(x, t) ** 2 - 73 / 405 * tpss_qb(x, t) * jnp.sqrt(1 / 2 * (9 / 25 * tpss_z(x, t) ** 2 + tpss_p(x) ** 2)) + MU_GE ** 2 / tpss_kappa(x, t) * tpss_p(x) ** 2 + 2 * jnp.sqrt(params_e) * MU_GE * 9 / 25 * tpss_z(x, t) ** 2 + params_e * params_mu * tpss_p(x) ** 3

  tpss_fx = lambda x, t: tpss_fxnum(x, t) / tpss_fxden(x)

  rtpss_f = lambda x, u, t: 1 + tpss_kappa(x, t) * (1 - jnp.exp(-tpss_fx(x, t) / tpss_kappa(x, t)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, rtpss_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t20 = s0 ** 2
  t21 = params.c * t20
  t22 = r0 ** 2
  t23 = 0.1e1 / t22
  t24 = tau0 ** 2
  t25 = 0.1e1 / t24
  t26 = t23 * t25
  t27 = t20 * t23
  t28 = t27 * t25
  t30 = 0.1e1 + t28 / 0.64e2
  t31 = t30 ** 2
  t32 = 0.1e1 / t31
  t33 = t26 * t32
  t37 = 6 ** (0.1e1 / 0.3e1)
  t38 = (0.10e2 / 0.81e2 + t21 * t33 / 0.64e2) * t37
  t39 = jnp.pi ** 2
  t40 = t39 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t43 = t38 * t42
  t44 = 2 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = s0 * t45
  t47 = t18 ** 2
  t49 = 0.1e1 / t47 / t22
  t50 = t46 * t49
  t53 = tau0 * t45
  t55 = 0.1e1 / t47 / r0
  t58 = t53 * t55 - t50 / 0.8e1
  t60 = t58 * t37 * t42
  t62 = t60 / 0.4e1 - 0.9e1 / 0.20e2
  t63 = params.b * t58
  t64 = t37 * t42
  t67 = t64 * (0.5e1 / 0.9e1 * t60 - 0.1e1)
  t70 = 0.5e1 * t63 * t67 + 0.9e1
  t71 = jnp.sqrt(t70)
  t72 = 0.1e1 / t71
  t73 = t62 * t72
  t75 = t64 * t50
  t77 = 0.3e1 * t73 + t75 / 0.36e2
  t78 = t77 ** 2
  t82 = 0.73e2 / 0.135e3 * t73 + 0.73e2 / 0.14580e5 * t75
  t84 = t37 ** 2
  t86 = 0.1e1 / t40 / t39
  t87 = t84 * t86
  t88 = t20 * t44
  t89 = t22 ** 2
  t90 = t89 * r0
  t92 = 0.1e1 / t18 / t90
  t93 = t88 * t92
  t97 = jnp.sqrt(0.100e3 * t87 * t93 + 0.162e3 * t28)
  t100 = 0.1e1 / params.kappa
  t102 = t100 * t84 * t86
  t105 = jnp.sqrt(params.e)
  t106 = t105 * t20
  t109 = params.e * params.mu
  t110 = t39 ** 2
  t111 = 0.1e1 / t110
  t112 = t20 * s0
  t113 = t111 * t112
  t114 = t89 ** 2
  t115 = 0.1e1 / t114
  t119 = t43 * t50 / 0.24e2 + 0.146e3 / 0.2025e4 * t78 - t82 * t97 / 0.240e3 + 0.25e2 / 0.472392e6 * t102 * t93 + t106 * t26 / 0.720e3 + t109 * t113 * t115 / 0.576e3
  t124 = 0.1e1 + t105 * t37 * t42 * t50 / 0.24e2
  t125 = t124 ** 2
  t126 = 0.1e1 / t125
  t129 = jnp.exp(-t119 * t126 * t100)
  t132 = 0.1e1 + params.kappa * (0.1e1 - t129)
  t136 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t132)
  t142 = t6 * t17
  t143 = t18 * params.kappa
  t144 = t22 * r0
  t145 = 0.1e1 / t144
  t146 = t145 * t25
  t150 = t20 ** 2
  t151 = params.c * t150
  t153 = t24 ** 2
  t154 = 0.1e1 / t153
  t157 = 0.1e1 / t31 / t30
  t168 = t46 / t47 / t144
  t174 = -0.5e1 / 0.3e1 * t53 * t49 + t168 / 0.3e1
  t177 = t174 * t37 * t42 * t72
  t181 = t62 / t71 / t70
  t189 = t181 * (0.5e1 * params.b * t174 * t67 + 0.25e2 / 0.9e1 * t63 * t87 * t174)
  t191 = t64 * t168
  t203 = t82 / t97
  t210 = t88 / t18 / t89 / t22
  t232 = t119 / t125 / t124 * t100 * t105
  t241 = f.my_piecewise3(t2, 0, -t6 * t17 / t47 * t132 / 0.8e1 + 0.3e1 / 0.8e1 * t142 * t143 * (-((-t21 * t146 * t32 / 0.32e2 + t151 / t90 * t154 * t157 / 0.1024e4) * t37 * t42 * t50 / 0.24e2 - t43 * t168 / 0.9e1 + 0.292e3 / 0.2025e4 * t77 * (0.3e1 / 0.4e1 * t177 - 0.3e1 / 0.2e1 * t189 - 0.2e1 / 0.27e2 * t191) - (0.73e2 / 0.540e3 * t177 - 0.73e2 / 0.270e3 * t189 - 0.146e3 / 0.10935e5 * t191) * t97 / 0.240e3 - t203 * (-0.324e3 * t20 * t145 * t25 - 0.1600e4 / 0.3e1 * t87 * t210) / 0.480e3 - 0.50e2 / 0.177147e6 * t102 * t210 - t106 * t146 / 0.360e3 - t109 * t113 / t114 / r0 / 0.72e2) * t126 * t100 - 0.2e1 / 0.9e1 * t232 * t191) * t129)
  vrho_0_ = 0.2e1 * r0 * t241 + 0.2e1 * t136
  t248 = 0.1e1 / t89
  t262 = t45 * t49
  t263 = t64 * t72
  t264 = t262 * t263
  t266 = params.b * t45
  t270 = t63 * t84
  t271 = t86 * t45
  t276 = t181 * (-0.5e1 / 0.8e1 * t266 * t49 * t67 - 0.25e2 / 0.72e2 * t270 * t271 * t49)
  t278 = t262 * t64
  t293 = s0 * t44 * t92
  t318 = f.my_piecewise3(t2, 0, 0.3e1 / 0.8e1 * t142 * t143 * (-((params.c * s0 * t33 / 0.32e2 - params.c * t112 * t248 * t154 * t157 / 0.1024e4) * t37 * t42 * t50 / 0.24e2 + t38 * t42 * t45 * t49 / 0.24e2 + 0.292e3 / 0.2025e4 * t77 * (-0.3e1 / 0.32e2 * t264 - 0.3e1 / 0.2e1 * t276 + t278 / 0.36e2) - (-0.73e2 / 0.4320e4 * t264 - 0.73e2 / 0.270e3 * t276 + 0.73e2 / 0.14580e5 * t278) * t97 / 0.240e3 - t203 * (0.324e3 * s0 * t23 * t25 + 0.200e3 * t87 * t293) / 0.480e3 + 0.25e2 / 0.236196e6 * t102 * t293 + t105 * s0 * t26 / 0.360e3 + t109 * t111 * t20 * t115 / 0.192e3) * t126 * t100 + t232 * t278 / 0.12e2) * t129)
  vsigma_0_ = 0.2e1 * r0 * t318
  vlapl_0_ = 0.0e0
  t321 = 0.1e1 / t24 / tau0
  t322 = t23 * t321
  t338 = t45 * t55 * t263
  t347 = t181 * (0.5e1 * t266 * t55 * t67 + 0.25e2 / 0.9e1 * t270 * t271 * t55)
  t368 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t142 * t18 * ((-t21 * t322 * t32 / 0.32e2 + t151 * t248 / t153 / tau0 * t157 / 0.1024e4) * t37 * t42 * t50 / 0.24e2 + 0.292e3 / 0.2025e4 * t77 * (0.3e1 / 0.4e1 * t338 - 0.3e1 / 0.2e1 * t347) - (0.73e2 / 0.540e3 * t338 - 0.73e2 / 0.270e3 * t347) * t97 / 0.240e3 + 0.27e2 / 0.40e2 * t203 * t27 * t321 - t106 * t322 / 0.360e3) * t126 * t129)
  vtau_0_ = 0.2e1 * r0 * t368
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
  t22 = s0 ** 2
  t23 = params.c * t22
  t24 = r0 ** 2
  t25 = 0.1e1 / t24
  t26 = tau0 ** 2
  t27 = 0.1e1 / t26
  t28 = t25 * t27
  t30 = t22 * t25 * t27
  t32 = 0.1e1 + t30 / 0.64e2
  t33 = t32 ** 2
  t34 = 0.1e1 / t33
  t39 = 6 ** (0.1e1 / 0.3e1)
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t45 = (0.10e2 / 0.81e2 + t23 * t28 * t34 / 0.64e2) * t39 * t44
  t46 = 2 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = s0 * t47
  t50 = 0.1e1 / t19 / t24
  t51 = t48 * t50
  t54 = tau0 * t47
  t56 = 0.1e1 / t19 / r0
  t59 = t54 * t56 - t51 / 0.8e1
  t63 = 0.5e1 / 0.9e1 * t59 * t39 * t44 - 0.1e1
  t64 = params.b * t59
  t65 = t39 * t44
  t66 = t65 * t63
  t69 = 0.5e1 * t64 * t66 + 0.9e1
  t70 = jnp.sqrt(t69)
  t71 = 0.1e1 / t70
  t76 = 0.27e2 / 0.20e2 * t63 * t71 + t65 * t51 / 0.36e2
  t77 = t76 ** 2
  t80 = t39 ** 2
  t82 = 0.1e1 / t42 / t41
  t83 = t80 * t82
  t84 = t22 * t46
  t85 = t24 ** 2
  t86 = t85 * r0
  t89 = t84 / t18 / t86
  t92 = 0.100e3 * t83 * t89 + 0.162e3 * t30
  t93 = jnp.sqrt(t92)
  t96 = 0.1e1 / params.kappa
  t98 = t96 * t80 * t82
  t101 = jnp.sqrt(params.e)
  t102 = t101 * t22
  t105 = params.e * params.mu
  t106 = t41 ** 2
  t109 = 0.1e1 / t106 * t22 * s0
  t110 = t85 ** 2
  t111 = 0.1e1 / t110
  t115 = t45 * t51 / 0.24e2 + 0.146e3 / 0.2025e4 * t77 - 0.73e2 / 0.97200e5 * t76 * t93 + 0.25e2 / 0.472392e6 * t98 * t89 + t102 * t28 / 0.720e3 + t105 * t109 * t111 / 0.576e3
  t120 = 0.1e1 + t101 * t39 * t44 * t51 / 0.24e2
  t121 = t120 ** 2
  t122 = 0.1e1 / t121
  t125 = jnp.exp(-t115 * t122 * t96)
  t128 = 0.1e1 + params.kappa * (0.1e1 - t125)
  t132 = t6 * t17
  t133 = t18 * params.kappa
  t134 = t24 * r0
  t135 = 0.1e1 / t134
  t136 = t135 * t27
  t140 = t22 ** 2
  t141 = params.c * t140
  t143 = t26 ** 2
  t144 = 0.1e1 / t143
  t147 = 0.1e1 / t33 / t32
  t153 = (-t23 * t136 * t34 / 0.32e2 + t141 / t86 * t144 * t147 / 0.1024e4) * t39 * t44
  t157 = 0.1e1 / t19 / t134
  t158 = t48 * t157
  t164 = -0.5e1 / 0.3e1 * t54 * t50 + t158 / 0.3e1
  t165 = t164 * t39
  t166 = t44 * t71
  t170 = 0.1e1 / t70 / t69
  t171 = t63 * t170
  t178 = 0.5e1 * params.b * t164 * t66 + 0.25e2 / 0.9e1 * t64 * t83 * t164
  t181 = t65 * t158
  t183 = 0.3e1 / 0.4e1 * t165 * t166 - 0.27e2 / 0.40e2 * t171 * t178 - 0.2e1 / 0.27e2 * t181
  t188 = 0.1e1 / t93
  t189 = t76 * t188
  t193 = t85 * t24
  t196 = t84 / t18 / t193
  t199 = -0.324e3 * t22 * t135 * t27 - 0.1600e4 / 0.3e1 * t83 * t196
  t211 = t153 * t51 / 0.24e2 - t45 * t158 / 0.9e1 + 0.292e3 / 0.2025e4 * t76 * t183 - 0.73e2 / 0.97200e5 * t183 * t93 - 0.73e2 / 0.194400e6 * t189 * t199 - 0.50e2 / 0.177147e6 * t98 * t196 - t102 * t136 / 0.360e3 - t105 * t109 / t110 / r0 / 0.72e2
  t215 = 0.1e1 / t121 / t120
  t217 = t96 * t101
  t218 = t115 * t215 * t217
  t221 = -t211 * t122 * t96 - 0.2e1 / 0.9e1 * t218 * t181
  t222 = t221 * t125
  t227 = f.my_piecewise3(t2, 0, -t6 * t17 * t20 * t128 / 0.8e1 + 0.3e1 / 0.8e1 * t132 * t133 * t222)
  t237 = 0.1e1 / t85
  t238 = t237 * t27
  t252 = t33 ** 2
  t266 = t48 / t19 / t85
  t269 = t183 ** 2
  t274 = 0.40e2 / 0.9e1 * t54 * t157 - 0.11e2 / 0.9e1 * t266
  t282 = t69 ** 2
  t286 = t178 ** 2
  t292 = t164 ** 2
  t302 = t65 * t266
  t304 = 0.3e1 / 0.4e1 * t274 * t39 * t166 - 0.3e1 / 0.4e1 * t165 * t44 * t170 * t178 + 0.81e2 / 0.80e2 * t63 / t70 / t282 * t286 - 0.27e2 / 0.40e2 * t171 * (0.5e1 * params.b * t274 * t66 + 0.50e2 / 0.9e1 * params.b * t292 * t83 + 0.25e2 / 0.9e1 * t64 * t83 * t274) + 0.22e2 / 0.81e2 * t302
  t315 = t199 ** 2
  t324 = t84 / t18 / t85 / t134
  t325 = t83 * t324
  t339 = (0.3e1 / 0.32e2 * t23 * t238 * t34 - 0.7e1 / 0.1024e4 * t141 / t193 * t144 * t147 + 0.3e1 / 0.32768e5 * params.c * t140 * t22 * t111 / t143 / t26 / t252) * t39 * t44 * t51 / 0.24e2 - 0.2e1 / 0.9e1 * t153 * t158 + 0.11e2 / 0.27e2 * t45 * t266 + 0.292e3 / 0.2025e4 * t269 + 0.292e3 / 0.2025e4 * t76 * t304 - 0.73e2 / 0.97200e5 * t304 * t93 - 0.73e2 / 0.97200e5 * t183 * t188 * t199 + 0.73e2 / 0.388800e6 * t76 / t93 / t92 * t315 - 0.73e2 / 0.194400e6 * t189 * (0.972e3 * t22 * t237 * t27 + 0.30400e5 / 0.9e1 * t325) + 0.950e3 / 0.531441e6 * t98 * t324 + t102 * t238 / 0.120e3 + t105 * t109 / t110 / t24 / 0.8e1
  t346 = t121 ** 2
  t360 = t221 ** 2
  t366 = f.my_piecewise3(t2, 0, t6 * t17 * t56 * t128 / 0.12e2 + t132 * t20 * params.kappa * t222 / 0.4e1 + 0.3e1 / 0.8e1 * t132 * t133 * (-t339 * t122 * t96 - 0.4e1 / 0.9e1 * t211 * t215 * t217 * t181 - 0.4e1 / 0.27e2 * t115 / t346 * t96 * params.e * t325 + 0.22e2 / 0.27e2 * t218 * t302) * t125 + 0.3e1 / 0.8e1 * t132 * t133 * t360 * t125)
  v2rho2_0_ = 0.2e1 * r0 * t366 + 0.4e1 * t227
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
  t23 = s0 ** 2
  t24 = params.c * t23
  t25 = r0 ** 2
  t26 = 0.1e1 / t25
  t27 = tau0 ** 2
  t28 = 0.1e1 / t27
  t29 = t26 * t28
  t31 = t23 * t26 * t28
  t33 = 0.1e1 + t31 / 0.64e2
  t34 = t33 ** 2
  t35 = 0.1e1 / t34
  t40 = 6 ** (0.1e1 / 0.3e1)
  t42 = jnp.pi ** 2
  t43 = t42 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t46 = (0.10e2 / 0.81e2 + t24 * t29 * t35 / 0.64e2) * t40 * t45
  t47 = 2 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = s0 * t48
  t51 = 0.1e1 / t19 / t25
  t52 = t49 * t51
  t55 = tau0 * t48
  t58 = t55 * t21 - t52 / 0.8e1
  t62 = 0.5e1 / 0.9e1 * t58 * t40 * t45 - 0.1e1
  t63 = params.b * t58
  t64 = t40 * t45
  t65 = t64 * t62
  t68 = 0.5e1 * t63 * t65 + 0.9e1
  t69 = jnp.sqrt(t68)
  t70 = 0.1e1 / t69
  t75 = 0.27e2 / 0.20e2 * t62 * t70 + t64 * t52 / 0.36e2
  t76 = t75 ** 2
  t79 = t40 ** 2
  t81 = 0.1e1 / t43 / t42
  t82 = t79 * t81
  t83 = t23 * t47
  t84 = t25 ** 2
  t85 = t84 * r0
  t88 = t83 / t18 / t85
  t91 = 0.100e3 * t82 * t88 + 0.162e3 * t31
  t92 = jnp.sqrt(t91)
  t95 = 0.1e1 / params.kappa
  t97 = t95 * t79 * t81
  t100 = jnp.sqrt(params.e)
  t101 = t100 * t23
  t104 = params.e * params.mu
  t105 = t42 ** 2
  t106 = 0.1e1 / t105
  t107 = t23 * s0
  t108 = t106 * t107
  t109 = t84 ** 2
  t110 = 0.1e1 / t109
  t114 = t46 * t52 / 0.24e2 + 0.146e3 / 0.2025e4 * t76 - 0.73e2 / 0.97200e5 * t75 * t92 + 0.25e2 / 0.472392e6 * t97 * t88 + t101 * t29 / 0.720e3 + t104 * t108 * t110 / 0.576e3
  t119 = 0.1e1 + t100 * t40 * t45 * t52 / 0.24e2
  t120 = t119 ** 2
  t121 = 0.1e1 / t120
  t124 = jnp.exp(-t114 * t121 * t95)
  t127 = 0.1e1 + params.kappa * (0.1e1 - t124)
  t131 = t6 * t17
  t133 = 0.1e1 / t19 * params.kappa
  t134 = t25 * r0
  t135 = 0.1e1 / t134
  t136 = t135 * t28
  t140 = t23 ** 2
  t141 = params.c * t140
  t142 = 0.1e1 / t85
  t143 = t27 ** 2
  t144 = 0.1e1 / t143
  t147 = 0.1e1 / t34 / t33
  t153 = (-t24 * t136 * t35 / 0.32e2 + t141 * t142 * t144 * t147 / 0.1024e4) * t40 * t45
  t157 = 0.1e1 / t19 / t134
  t158 = t49 * t157
  t164 = -0.5e1 / 0.3e1 * t55 * t51 + t158 / 0.3e1
  t165 = t164 * t40
  t166 = t45 * t70
  t170 = 0.1e1 / t69 / t68
  t171 = t62 * t170
  t175 = t82 * t164
  t178 = 0.5e1 * params.b * t164 * t65 + 0.25e2 / 0.9e1 * t63 * t175
  t181 = t64 * t158
  t183 = 0.3e1 / 0.4e1 * t165 * t166 - 0.27e2 / 0.40e2 * t171 * t178 - 0.2e1 / 0.27e2 * t181
  t188 = 0.1e1 / t92
  t189 = t75 * t188
  t193 = t84 * t25
  t196 = t83 / t18 / t193
  t199 = -0.324e3 * t23 * t135 * t28 - 0.1600e4 / 0.3e1 * t82 * t196
  t207 = 0.1e1 / t109 / r0
  t211 = t153 * t52 / 0.24e2 - t46 * t158 / 0.9e1 + 0.292e3 / 0.2025e4 * t75 * t183 - 0.73e2 / 0.97200e5 * t183 * t92 - 0.73e2 / 0.194400e6 * t189 * t199 - 0.50e2 / 0.177147e6 * t97 * t196 - t101 * t136 / 0.360e3 - t104 * t108 * t207 / 0.72e2
  t215 = 0.1e1 / t120 / t119
  t217 = t95 * t100
  t218 = t114 * t215 * t217
  t221 = -t211 * t121 * t95 - 0.2e1 / 0.9e1 * t218 * t181
  t222 = t221 * t124
  t226 = t18 * params.kappa
  t227 = 0.1e1 / t84
  t228 = t227 * t28
  t238 = params.c * t140 * t23
  t240 = 0.1e1 / t143 / t27
  t242 = t34 ** 2
  t243 = 0.1e1 / t242
  t249 = (0.3e1 / 0.32e2 * t24 * t228 * t35 - 0.7e1 / 0.1024e4 * t141 / t193 * t144 * t147 + 0.3e1 / 0.32768e5 * t238 * t110 * t240 * t243) * t40 * t45
  t255 = 0.1e1 / t19 / t84
  t256 = t49 * t255
  t259 = t183 ** 2
  t264 = 0.40e2 / 0.9e1 * t55 * t157 - 0.11e2 / 0.9e1 * t256
  t265 = t264 * t40
  t268 = t45 * t170
  t269 = t268 * t178
  t272 = t68 ** 2
  t274 = 0.1e1 / t69 / t272
  t275 = t62 * t274
  t276 = t178 ** 2
  t279 = params.b * t264
  t282 = t164 ** 2
  t289 = 0.5e1 * t279 * t65 + 0.50e2 / 0.9e1 * params.b * t282 * t82 + 0.25e2 / 0.9e1 * t63 * t82 * t264
  t292 = t64 * t256
  t294 = 0.3e1 / 0.4e1 * t265 * t166 - 0.3e1 / 0.4e1 * t165 * t269 + 0.81e2 / 0.80e2 * t275 * t276 - 0.27e2 / 0.40e2 * t171 * t289 + 0.22e2 / 0.81e2 * t292
  t299 = t183 * t188
  t303 = 0.1e1 / t92 / t91
  t304 = t75 * t303
  t305 = t199 ** 2
  t311 = t84 * t134
  t314 = t83 / t18 / t311
  t315 = t82 * t314
  t317 = 0.972e3 * t23 * t227 * t28 + 0.30400e5 / 0.9e1 * t315
  t329 = t249 * t52 / 0.24e2 - 0.2e1 / 0.9e1 * t153 * t158 + 0.11e2 / 0.27e2 * t46 * t256 + 0.292e3 / 0.2025e4 * t259 + 0.292e3 / 0.2025e4 * t75 * t294 - 0.73e2 / 0.97200e5 * t294 * t92 - 0.73e2 / 0.97200e5 * t299 * t199 + 0.73e2 / 0.388800e6 * t304 * t305 - 0.73e2 / 0.194400e6 * t189 * t317 + 0.950e3 / 0.531441e6 * t97 * t314 + t101 * t228 / 0.120e3 + t104 * t108 / t109 / t25 / 0.8e1
  t333 = t211 * t215 * t217
  t336 = t120 ** 2
  t337 = 0.1e1 / t336
  t339 = t95 * params.e
  t340 = t114 * t337 * t339
  t345 = -t329 * t121 * t95 - 0.4e1 / 0.9e1 * t333 * t181 - 0.4e1 / 0.27e2 * t340 * t315 + 0.22e2 / 0.27e2 * t218 * t292
  t346 = t345 * t124
  t350 = t221 ** 2
  t351 = t350 * t124
  t356 = f.my_piecewise3(t2, 0, t6 * t17 * t21 * t127 / 0.12e2 + t131 * t133 * t222 / 0.4e1 + 0.3e1 / 0.8e1 * t131 * t226 * t346 + 0.3e1 / 0.8e1 * t131 * t226 * t351)
  t372 = t142 * t28
  t385 = t140 ** 2
  t388 = 0.1e1 / t109 / t134
  t389 = t143 ** 2
  t408 = t49 / t19 / t85
  t416 = -0.440e3 / 0.27e2 * t55 * t255 + 0.154e3 / 0.27e2 * t408
  t450 = t64 * t408
  t452 = 0.3e1 / 0.4e1 * t416 * t40 * t166 - 0.9e1 / 0.8e1 * t265 * t269 + 0.27e2 / 0.16e2 * t165 * t45 * t274 * t276 - 0.9e1 / 0.8e1 * t165 * t268 * t289 - 0.81e2 / 0.32e2 * t62 / t69 / t272 / t68 * t276 * t178 + 0.243e3 / 0.80e2 * t275 * t178 * t289 - 0.27e2 / 0.40e2 * t171 * (0.5e1 * params.b * t416 * t65 + 0.50e2 / 0.3e1 * t279 * t175 + 0.25e2 / 0.9e1 * t63 * t82 * t416) - 0.308e3 / 0.243e3 * t450
  t465 = t91 ** 2
  t480 = t83 / t18 / t109
  t481 = t82 * t480
  t493 = (-0.3e1 / 0.8e1 * t24 * t372 * t35 + 0.3e1 / 0.64e2 * t141 / t311 * t144 * t147 - 0.45e2 / 0.32768e5 * t238 * t207 * t240 * t243 + 0.3e1 / 0.262144e6 * params.c * t385 * t388 / t389 / t242 / t33) * t40 * t45 * t52 / 0.24e2 - t249 * t158 / 0.3e1 + 0.11e2 / 0.9e1 * t153 * t256 - 0.154e3 / 0.81e2 * t46 * t408 + 0.292e3 / 0.675e3 * t183 * t294 + 0.292e3 / 0.2025e4 * t75 * t452 - 0.73e2 / 0.97200e5 * t452 * t92 - 0.73e2 / 0.64800e5 * t294 * t188 * t199 + 0.73e2 / 0.129600e6 * t183 * t303 * t305 - 0.73e2 / 0.64800e5 * t299 * t317 - 0.73e2 / 0.259200e6 * t75 / t92 / t465 * t305 * t199 + 0.73e2 / 0.129600e6 * t304 * t199 * t317 - 0.73e2 / 0.194400e6 * t189 * (-0.3888e4 * t23 * t142 * t28 - 0.668800e6 / 0.27e2 * t481) - 0.20900e5 / 0.1594323e7 * t97 * t480 - t101 * t372 / 0.30e2 - 0.5e1 / 0.4e1 * t104 * t108 * t388
  t537 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t51 * t127 - t131 * t21 * params.kappa * t222 / 0.4e1 + 0.3e1 / 0.8e1 * t131 * t133 * t346 + 0.3e1 / 0.8e1 * t131 * t133 * t351 + 0.3e1 / 0.8e1 * t131 * t226 * (-t493 * t121 * t95 - 0.2e1 / 0.3e1 * t329 * t215 * t217 * t181 - 0.4e1 / 0.9e1 * t211 * t337 * t339 * t315 + 0.22e2 / 0.9e1 * t333 * t292 - 0.64e2 / 0.81e2 * t114 / t336 / t119 * t95 * t100 * params.e * t106 * t107 * t388 + 0.44e2 / 0.27e2 * t340 * t481 - 0.308e3 / 0.81e2 * t218 * t450) * t124 + 0.9e1 / 0.8e1 * t6 * t17 * t18 * params.kappa * t345 * t222 + 0.3e1 / 0.8e1 * t131 * t226 * t350 * t221 * t124)
  v3rho3_0_ = 0.2e1 * r0 * t537 + 0.6e1 * t356

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
  t24 = s0 ** 2
  t25 = params.c * t24
  t26 = 0.1e1 / t18
  t27 = tau0 ** 2
  t28 = 0.1e1 / t27
  t29 = t26 * t28
  t31 = t24 * t26 * t28
  t33 = 0.1e1 + t31 / 0.64e2
  t34 = t33 ** 2
  t35 = 0.1e1 / t34
  t40 = 6 ** (0.1e1 / 0.3e1)
  t42 = jnp.pi ** 2
  t43 = t42 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t46 = (0.10e2 / 0.81e2 + t25 * t29 * t35 / 0.64e2) * t40 * t45
  t47 = 2 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = s0 * t48
  t50 = t49 * t22
  t53 = tau0 * t48
  t55 = 0.1e1 / t20 / r0
  t58 = t53 * t55 - t50 / 0.8e1
  t62 = 0.5e1 / 0.9e1 * t58 * t40 * t45 - 0.1e1
  t63 = params.b * t58
  t64 = t40 * t45
  t65 = t64 * t62
  t68 = 0.5e1 * t63 * t65 + 0.9e1
  t69 = jnp.sqrt(t68)
  t70 = 0.1e1 / t69
  t75 = 0.27e2 / 0.20e2 * t62 * t70 + t64 * t50 / 0.36e2
  t76 = t75 ** 2
  t79 = t40 ** 2
  t81 = 0.1e1 / t43 / t42
  t82 = t79 * t81
  t83 = t24 * t47
  t84 = t18 ** 2
  t85 = t84 * r0
  t88 = t83 / t19 / t85
  t91 = 0.100e3 * t82 * t88 + 0.162e3 * t31
  t92 = jnp.sqrt(t91)
  t95 = 0.1e1 / params.kappa
  t97 = t95 * t79 * t81
  t100 = jnp.sqrt(params.e)
  t101 = t100 * t24
  t104 = params.e * params.mu
  t105 = t42 ** 2
  t106 = 0.1e1 / t105
  t107 = t24 * s0
  t108 = t106 * t107
  t109 = t84 ** 2
  t110 = 0.1e1 / t109
  t114 = t46 * t50 / 0.24e2 + 0.146e3 / 0.2025e4 * t76 - 0.73e2 / 0.97200e5 * t75 * t92 + 0.25e2 / 0.472392e6 * t97 * t88 + t101 * t29 / 0.720e3 + t104 * t108 * t110 / 0.576e3
  t119 = 0.1e1 + t100 * t40 * t45 * t50 / 0.24e2
  t120 = t119 ** 2
  t121 = 0.1e1 / t120
  t124 = jnp.exp(-t114 * t121 * t95)
  t127 = 0.1e1 + params.kappa * (0.1e1 - t124)
  t131 = t6 * t17
  t132 = t55 * params.kappa
  t133 = t18 * r0
  t134 = 0.1e1 / t133
  t135 = t134 * t28
  t139 = t24 ** 2
  t140 = params.c * t139
  t141 = 0.1e1 / t85
  t142 = t27 ** 2
  t143 = 0.1e1 / t142
  t146 = 0.1e1 / t34 / t33
  t152 = (-t25 * t135 * t35 / 0.32e2 + t140 * t141 * t143 * t146 / 0.1024e4) * t40 * t45
  t156 = 0.1e1 / t20 / t133
  t157 = t49 * t156
  t163 = -0.5e1 / 0.3e1 * t53 * t22 + t157 / 0.3e1
  t164 = t163 * t40
  t165 = t45 * t70
  t169 = 0.1e1 / t69 / t68
  t170 = t62 * t169
  t174 = t82 * t163
  t177 = 0.5e1 * params.b * t163 * t65 + 0.25e2 / 0.9e1 * t63 * t174
  t180 = t64 * t157
  t182 = 0.3e1 / 0.4e1 * t164 * t165 - 0.27e2 / 0.40e2 * t170 * t177 - 0.2e1 / 0.27e2 * t180
  t187 = 0.1e1 / t92
  t188 = t75 * t187
  t192 = t84 * t18
  t195 = t83 / t19 / t192
  t198 = -0.324e3 * t24 * t134 * t28 - 0.1600e4 / 0.3e1 * t82 * t195
  t205 = t109 * r0
  t206 = 0.1e1 / t205
  t210 = t152 * t50 / 0.24e2 - t46 * t157 / 0.9e1 + 0.292e3 / 0.2025e4 * t75 * t182 - 0.73e2 / 0.97200e5 * t182 * t92 - 0.73e2 / 0.194400e6 * t188 * t198 - 0.50e2 / 0.177147e6 * t97 * t195 - t101 * t135 / 0.360e3 - t104 * t108 * t206 / 0.72e2
  t214 = 0.1e1 / t120 / t119
  t216 = t95 * t100
  t217 = t114 * t214 * t216
  t220 = -t210 * t121 * t95 - 0.2e1 / 0.9e1 * t217 * t180
  t221 = t220 * t124
  t225 = 0.1e1 / t20
  t226 = t225 * params.kappa
  t227 = 0.1e1 / t84
  t228 = t227 * t28
  t232 = 0.1e1 / t192
  t238 = params.c * t139 * t24
  t240 = 0.1e1 / t142 / t27
  t242 = t34 ** 2
  t243 = 0.1e1 / t242
  t249 = (0.3e1 / 0.32e2 * t25 * t228 * t35 - 0.7e1 / 0.1024e4 * t140 * t232 * t143 * t146 + 0.3e1 / 0.32768e5 * t238 * t110 * t240 * t243) * t40 * t45
  t255 = 0.1e1 / t20 / t84
  t256 = t49 * t255
  t259 = t182 ** 2
  t264 = 0.40e2 / 0.9e1 * t53 * t156 - 0.11e2 / 0.9e1 * t256
  t265 = t264 * t40
  t268 = t45 * t169
  t269 = t268 * t177
  t272 = t68 ** 2
  t274 = 0.1e1 / t69 / t272
  t275 = t62 * t274
  t276 = t177 ** 2
  t279 = params.b * t264
  t282 = t163 ** 2
  t289 = 0.5e1 * t279 * t65 + 0.50e2 / 0.9e1 * params.b * t282 * t82 + 0.25e2 / 0.9e1 * t63 * t82 * t264
  t292 = t64 * t256
  t294 = 0.3e1 / 0.4e1 * t265 * t165 - 0.3e1 / 0.4e1 * t164 * t269 + 0.81e2 / 0.80e2 * t275 * t276 - 0.27e2 / 0.40e2 * t170 * t289 + 0.22e2 / 0.81e2 * t292
  t299 = t182 * t187
  t303 = 0.1e1 / t92 / t91
  t304 = t75 * t303
  t305 = t198 ** 2
  t311 = t84 * t133
  t314 = t83 / t19 / t311
  t315 = t82 * t314
  t317 = 0.972e3 * t24 * t227 * t28 + 0.30400e5 / 0.9e1 * t315
  t325 = 0.1e1 / t109 / t18
  t329 = t249 * t50 / 0.24e2 - 0.2e1 / 0.9e1 * t152 * t157 + 0.11e2 / 0.27e2 * t46 * t256 + 0.292e3 / 0.2025e4 * t259 + 0.292e3 / 0.2025e4 * t75 * t294 - 0.73e2 / 0.97200e5 * t294 * t92 - 0.73e2 / 0.97200e5 * t299 * t198 + 0.73e2 / 0.388800e6 * t304 * t305 - 0.73e2 / 0.194400e6 * t188 * t317 + 0.950e3 / 0.531441e6 * t97 * t314 + t101 * t228 / 0.120e3 + t104 * t108 * t325 / 0.8e1
  t333 = t210 * t214 * t216
  t336 = t120 ** 2
  t337 = 0.1e1 / t336
  t339 = t95 * params.e
  t340 = t114 * t337 * t339
  t345 = -t329 * t121 * t95 - 0.4e1 / 0.9e1 * t333 * t180 - 0.4e1 / 0.27e2 * t340 * t315 + 0.22e2 / 0.27e2 * t217 * t292
  t346 = t345 * t124
  t350 = t220 ** 2
  t351 = t350 * t124
  t355 = t19 * params.kappa
  t356 = t141 * t28
  t369 = t139 ** 2
  t370 = params.c * t369
  t372 = 0.1e1 / t109 / t133
  t373 = t142 ** 2
  t374 = 0.1e1 / t373
  t377 = 0.1e1 / t242 / t33
  t383 = (-0.3e1 / 0.8e1 * t25 * t356 * t35 + 0.3e1 / 0.64e2 * t140 / t311 * t143 * t146 - 0.45e2 / 0.32768e5 * t238 * t206 * t240 * t243 + 0.3e1 / 0.262144e6 * t370 * t372 * t374 * t377) * t40 * t45
  t391 = 0.1e1 / t20 / t85
  t392 = t49 * t391
  t400 = -0.440e3 / 0.27e2 * t53 * t255 + 0.154e3 / 0.27e2 * t392
  t401 = t400 * t40
  t407 = t45 * t274 * t276
  t410 = t268 * t289
  t415 = 0.1e1 / t69 / t272 / t68
  t416 = t62 * t415
  t417 = t276 * t177
  t423 = params.b * t400
  t431 = 0.5e1 * t423 * t65 + 0.50e2 / 0.3e1 * t279 * t174 + 0.25e2 / 0.9e1 * t63 * t82 * t400
  t434 = t64 * t392
  t436 = 0.3e1 / 0.4e1 * t401 * t165 - 0.9e1 / 0.8e1 * t265 * t269 + 0.27e2 / 0.16e2 * t164 * t407 - 0.9e1 / 0.8e1 * t164 * t410 - 0.81e2 / 0.32e2 * t416 * t417 + 0.243e3 / 0.80e2 * t275 * t177 * t289 - 0.27e2 / 0.40e2 * t170 * t431 - 0.308e3 / 0.243e3 * t434
  t441 = t294 * t187
  t444 = t182 * t303
  t449 = t91 ** 2
  t451 = 0.1e1 / t92 / t449
  t452 = t75 * t451
  t453 = t305 * t198
  t456 = t198 * t317
  t464 = t83 / t19 / t109
  t465 = t82 * t464
  t467 = -0.3888e4 * t24 * t141 * t28 - 0.668800e6 / 0.27e2 * t465
  t477 = t383 * t50 / 0.24e2 - t249 * t157 / 0.3e1 + 0.11e2 / 0.9e1 * t152 * t256 - 0.154e3 / 0.81e2 * t46 * t392 + 0.292e3 / 0.675e3 * t182 * t294 + 0.292e3 / 0.2025e4 * t75 * t436 - 0.73e2 / 0.97200e5 * t436 * t92 - 0.73e2 / 0.64800e5 * t441 * t198 + 0.73e2 / 0.129600e6 * t444 * t305 - 0.73e2 / 0.64800e5 * t299 * t317 - 0.73e2 / 0.259200e6 * t452 * t453 + 0.73e2 / 0.129600e6 * t304 * t456 - 0.73e2 / 0.194400e6 * t188 * t467 - 0.20900e5 / 0.1594323e7 * t97 * t464 - t101 * t356 / 0.30e2 - 0.5e1 / 0.4e1 * t104 * t108 * t372
  t481 = t329 * t214 * t216
  t485 = t210 * t337 * t339
  t491 = 0.1e1 / t336 / t119
  t493 = t114 * t491 * t95
  t495 = t100 * params.e * t106
  t497 = t495 * t107 * t372
  t504 = -t477 * t121 * t95 - 0.2e1 / 0.3e1 * t481 * t180 - 0.4e1 / 0.9e1 * t485 * t315 + 0.22e2 / 0.9e1 * t333 * t292 - 0.64e2 / 0.81e2 * t493 * t497 + 0.44e2 / 0.27e2 * t340 * t465 - 0.308e3 / 0.81e2 * t217 * t434
  t505 = t504 * t124
  t510 = t6 * t17 * t19
  t511 = params.kappa * t345
  t512 = t511 * t221
  t516 = t350 * t220 * t124
  t521 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t127 - t131 * t132 * t221 / 0.4e1 + 0.3e1 / 0.8e1 * t131 * t226 * t346 + 0.3e1 / 0.8e1 * t131 * t226 * t351 + 0.3e1 / 0.8e1 * t131 * t355 * t505 + 0.9e1 / 0.8e1 * t510 * t512 + 0.3e1 / 0.8e1 * t131 * t355 * t516)
  t547 = t294 ** 2
  t555 = t49 / t20 / t192
  t557 = 0.6160e4 / 0.81e2 * t53 * t391 - 0.2618e4 / 0.81e2 * t555
  t579 = t272 ** 2
  t583 = t276 ** 2
  t589 = t289 ** 2
  t600 = t264 ** 2
  t610 = t64 * t555
  t612 = 0.3e1 / 0.4e1 * t557 * t40 * t165 - 0.3e1 / 0.2e1 * t401 * t269 + 0.27e2 / 0.8e1 * t265 * t407 - 0.9e1 / 0.4e1 * t265 * t410 - 0.45e2 / 0.8e1 * t164 * t45 * t415 * t417 + 0.27e2 / 0.4e1 * t164 * t45 * t274 * t177 * t289 - 0.3e1 / 0.2e1 * t164 * t268 * t431 + 0.567e3 / 0.64e2 * t62 / t69 / t579 * t583 - 0.243e3 / 0.16e2 * t416 * t276 * t289 + 0.243e3 / 0.80e2 * t275 * t589 + 0.81e2 / 0.20e2 * t275 * t177 * t431 - 0.27e2 / 0.40e2 * t170 * (0.5e1 * params.b * t557 * t65 + 0.200e3 / 0.9e1 * t423 * t174 + 0.50e2 / 0.3e1 * params.b * t600 * t82 + 0.25e2 / 0.9e1 * t63 * t82 * t557) + 0.5236e4 / 0.729e3 * t610
  t629 = t305 ** 2
  t635 = t317 ** 2
  t641 = 0.292e3 / 0.675e3 * t547 + 0.1168e4 / 0.2025e4 * t182 * t436 + 0.292e3 / 0.2025e4 * t75 * t612 - 0.73e2 / 0.97200e5 * t612 * t92 + 0.73e2 / 0.64800e5 * t294 * t303 * t305 - 0.73e2 / 0.64800e5 * t182 * t451 * t453 + 0.73e2 / 0.32400e5 * t444 * t456 + 0.73e2 / 0.103680e6 * t75 / t92 / t449 / t91 * t629 - 0.73e2 / 0.43200e5 * t452 * t305 * t317 + 0.73e2 / 0.129600e6 * t304 * t635 + 0.73e2 / 0.97200e5 * t304 * t198 * t467
  t642 = t232 * t28
  t646 = 0.1e1 / t109 / t84
  t662 = t83 / t19 / t205
  t663 = t82 * t662
  t693 = t109 * t192
  t710 = t101 * t642 / 0.6e1 + 0.55e2 / 0.4e1 * t104 * t108 * t646 - 0.73e2 / 0.48600e5 * t436 * t187 * t198 - 0.73e2 / 0.32400e5 * t441 * t317 - 0.73e2 / 0.48600e5 * t299 * t467 - 0.73e2 / 0.194400e6 * t188 * (0.19440e5 * t24 * t232 * t28 + 0.16720000e8 / 0.81e2 * t663) - 0.4e1 / 0.9e1 * t383 * t157 + 0.22e2 / 0.9e1 * t249 * t256 - 0.616e3 / 0.81e2 * t152 * t392 + 0.2618e4 / 0.243e3 * t46 * t555 + (0.15e2 / 0.8e1 * t25 * t642 * t35 - 0.45e2 / 0.128e3 * t140 * t110 * t143 * t146 + 0.549e3 / 0.32768e5 * t238 * t325 * t240 * t243 - 0.39e2 / 0.131072e6 * t370 * t646 * t374 * t377 + 0.15e2 / 0.8388608e7 * params.c * t369 * t24 / t693 / t373 / t27 / t242 / t34) * t40 * t45 * t50 / 0.24e2 + 0.522500e6 / 0.4782969e7 * t97 * t662
  t735 = params.e ** 2
  t754 = -(t641 + t710) * t121 * t95 - 0.8e1 / 0.9e1 * t477 * t214 * t216 * t180 - 0.8e1 / 0.9e1 * t329 * t337 * t339 * t315 + 0.44e2 / 0.9e1 * t481 * t292 - 0.256e3 / 0.81e2 * t210 * t491 * t95 * t497 + 0.176e3 / 0.27e2 * t485 * t465 - 0.1232e4 / 0.81e2 * t333 * t434 - 0.320e3 / 0.729e3 * t114 / t336 / t120 * t95 * t735 * t106 * t139 / t20 / t693 * t64 * t48 + 0.1408e4 / 0.81e2 * t493 * t495 * t107 * t646 - 0.3916e4 / 0.243e3 * t340 * t663 + 0.5236e4 / 0.243e3 * t217 * t610
  t763 = t345 ** 2
  t771 = t350 ** 2
  t776 = 0.10e2 / 0.27e2 * t6 * t17 * t156 * t127 + 0.5e1 / 0.9e1 * t131 * t22 * params.kappa * t221 - t131 * t132 * t346 / 0.2e1 - t131 * t132 * t351 / 0.2e1 + t131 * t226 * t505 / 0.2e1 + 0.3e1 / 0.2e1 * t6 * t17 * t225 * t512 + t131 * t226 * t516 / 0.2e1 + 0.3e1 / 0.8e1 * t131 * t355 * t754 * t124 + 0.3e1 / 0.2e1 * t510 * params.kappa * t504 * t221 + 0.9e1 / 0.8e1 * t131 * t355 * t763 * t124 + 0.9e1 / 0.4e1 * t510 * t511 * t351 + 0.3e1 / 0.8e1 * t131 * t355 * t771 * t124
  t777 = f.my_piecewise3(t2, 0, t776)
  v4rho4_0_ = 0.2e1 * r0 * t777 + 0.8e1 * t521

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
  t32 = s0 ** 2
  t33 = params.c * t32
  t34 = r0 ** 2
  t35 = 0.1e1 / t34
  t36 = tau0 ** 2
  t37 = 0.1e1 / t36
  t38 = t35 * t37
  t40 = t32 * t35 * t37
  t42 = 0.1e1 + t40 / 0.64e2
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t49 = 6 ** (0.1e1 / 0.3e1)
  t50 = (0.10e2 / 0.81e2 + t33 * t38 * t44 / 0.64e2) * t49
  t51 = jnp.pi ** 2
  t52 = t51 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t54 = 0.1e1 / t53
  t55 = t54 * s0
  t56 = r0 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t59 = 0.1e1 / t57 / t34
  t60 = t55 * t59
  t66 = s0 * t59
  t68 = tau0 / t57 / r0 - t66 / 0.8e1
  t72 = 0.5e1 / 0.9e1 * t68 * t49 * t54 - 0.1e1
  t73 = params.b * t68
  t74 = t49 * t54
  t75 = t74 * t72
  t78 = 0.5e1 * t73 * t75 + 0.9e1
  t79 = jnp.sqrt(t78)
  t80 = 0.1e1 / t79
  t85 = 0.27e2 / 0.20e2 * t72 * t80 + t74 * t66 / 0.36e2
  t86 = t85 ** 2
  t89 = t49 ** 2
  t91 = 0.1e1 / t52 / t51
  t92 = t89 * t91
  t93 = t34 ** 2
  t94 = t93 * r0
  t96 = 0.1e1 / t56 / t94
  t100 = 0.50e2 * t92 * t32 * t96 + 0.162e3 * t40
  t101 = jnp.sqrt(t100)
  t104 = 0.1e1 / params.kappa
  t105 = t104 * t89
  t106 = t91 * t32
  t110 = jnp.sqrt(params.e)
  t111 = t110 * t32
  t114 = params.e * params.mu
  t115 = t51 ** 2
  t116 = 0.1e1 / t115
  t118 = t116 * t32 * s0
  t119 = t93 ** 2
  t120 = 0.1e1 / t119
  t124 = t50 * t60 / 0.24e2 + 0.146e3 / 0.2025e4 * t86 - 0.73e2 / 0.97200e5 * t85 * t101 + 0.25e2 / 0.944784e6 * t105 * t106 * t96 + t111 * t38 / 0.720e3 + t114 * t118 * t120 / 0.2304e4
  t125 = t110 * t49
  t128 = 0.1e1 + t125 * t60 / 0.24e2
  t129 = t128 ** 2
  t130 = 0.1e1 / t129
  t133 = jnp.exp(-t124 * t130 * t104)
  t136 = 0.1e1 + params.kappa * (0.1e1 - t133)
  t140 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t141 = t140 * f.p.zeta_threshold
  t143 = f.my_piecewise3(t20, t141, t21 * t19)
  t144 = t30 ** 2
  t145 = 0.1e1 / t144
  t149 = t5 * t143 * t145 * t136 / 0.8e1
  t150 = t5 * t143
  t151 = t30 * params.kappa
  t152 = t34 * r0
  t153 = 0.1e1 / t152
  t154 = t153 * t37
  t158 = t32 ** 2
  t159 = params.c * t158
  t161 = t36 ** 2
  t162 = 0.1e1 / t161
  t165 = 0.1e1 / t43 / t42
  t170 = (-t33 * t154 * t44 / 0.32e2 + t159 / t94 * t162 * t165 / 0.1024e4) * t49
  t174 = 0.1e1 / t57 / t152
  t175 = t55 * t174
  t180 = s0 * t174
  t182 = -0.5e1 / 0.3e1 * tau0 * t59 + t180 / 0.3e1
  t183 = t182 * t49
  t184 = t54 * t80
  t188 = 0.1e1 / t79 / t78
  t189 = t72 * t188
  t196 = 0.5e1 * params.b * t182 * t75 + 0.25e2 / 0.9e1 * t73 * t92 * t182
  t199 = t74 * t180
  t201 = 0.3e1 / 0.4e1 * t183 * t184 - 0.27e2 / 0.40e2 * t189 * t196 - 0.2e1 / 0.27e2 * t199
  t206 = 0.1e1 / t101
  t207 = t85 * t206
  t211 = t93 * t34
  t213 = 0.1e1 / t56 / t211
  t217 = -0.324e3 * t32 * t153 * t37 - 0.800e3 / 0.3e1 * t92 * t32 * t213
  t230 = t170 * t60 / 0.24e2 - t50 * t175 / 0.9e1 + 0.292e3 / 0.2025e4 * t85 * t201 - 0.73e2 / 0.97200e5 * t201 * t101 - 0.73e2 / 0.194400e6 * t207 * t217 - 0.25e2 / 0.177147e6 * t105 * t106 * t213 - t111 * t154 / 0.360e3 - t114 * t118 / t119 / r0 / 0.288e3
  t234 = 0.1e1 / t129 / t128
  t236 = t104 * t110
  t237 = t124 * t234 * t236
  t240 = -t230 * t130 * t104 - 0.2e1 / 0.9e1 * t237 * t199
  t241 = t240 * t133
  t242 = t151 * t241
  t246 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t136 - t149 + 0.3e1 / 0.8e1 * t150 * t242)
  t248 = r1 <= f.p.dens_threshold
  t249 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t250 = 0.1e1 + t249
  t251 = t250 <= f.p.zeta_threshold
  t252 = t250 ** (0.1e1 / 0.3e1)
  t254 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t257 = f.my_piecewise3(t251, 0, 0.4e1 / 0.3e1 * t252 * t254)
  t259 = s2 ** 2
  t260 = params.c * t259
  t261 = r1 ** 2
  t262 = 0.1e1 / t261
  t263 = tau1 ** 2
  t264 = 0.1e1 / t263
  t265 = t262 * t264
  t267 = t259 * t262 * t264
  t269 = 0.1e1 + t267 / 0.64e2
  t270 = t269 ** 2
  t271 = 0.1e1 / t270
  t276 = (0.10e2 / 0.81e2 + t260 * t265 * t271 / 0.64e2) * t49
  t277 = t54 * s2
  t278 = r1 ** (0.1e1 / 0.3e1)
  t279 = t278 ** 2
  t281 = 0.1e1 / t279 / t261
  t282 = t277 * t281
  t288 = s2 * t281
  t290 = tau1 / t279 / r1 - t288 / 0.8e1
  t294 = 0.5e1 / 0.9e1 * t290 * t49 * t54 - 0.1e1
  t295 = params.b * t290
  t296 = t74 * t294
  t299 = 0.5e1 * t295 * t296 + 0.9e1
  t300 = jnp.sqrt(t299)
  t301 = 0.1e1 / t300
  t306 = 0.27e2 / 0.20e2 * t294 * t301 + t74 * t288 / 0.36e2
  t307 = t306 ** 2
  t310 = t261 ** 2
  t311 = t310 * r1
  t313 = 0.1e1 / t278 / t311
  t317 = 0.50e2 * t92 * t259 * t313 + 0.162e3 * t267
  t318 = jnp.sqrt(t317)
  t321 = t91 * t259
  t325 = t110 * t259
  t329 = t116 * t259 * s2
  t330 = t310 ** 2
  t331 = 0.1e1 / t330
  t335 = t276 * t282 / 0.24e2 + 0.146e3 / 0.2025e4 * t307 - 0.73e2 / 0.97200e5 * t306 * t318 + 0.25e2 / 0.944784e6 * t105 * t321 * t313 + t325 * t265 / 0.720e3 + t114 * t329 * t331 / 0.2304e4
  t338 = 0.1e1 + t125 * t282 / 0.24e2
  t339 = t338 ** 2
  t340 = 0.1e1 / t339
  t343 = jnp.exp(-t335 * t340 * t104)
  t346 = 0.1e1 + params.kappa * (0.1e1 - t343)
  t351 = f.my_piecewise3(t251, t141, t252 * t250)
  t355 = t5 * t351 * t145 * t346 / 0.8e1
  t357 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t5 * t257 * t30 * t346 - t355)
  t359 = t21 ** 2
  t360 = 0.1e1 / t359
  t361 = t26 ** 2
  t366 = t16 / t22 / t6
  t368 = -0.2e1 * t23 + 0.2e1 * t366
  t369 = f.my_piecewise5(t10, 0, t14, 0, t368)
  t373 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t360 * t361 + 0.4e1 / 0.3e1 * t21 * t369)
  t380 = t5 * t29 * t145 * t136
  t386 = 0.1e1 / t144 / t6
  t390 = t5 * t143 * t386 * t136 / 0.12e2
  t391 = t145 * params.kappa
  t393 = t150 * t391 * t241
  t395 = 0.1e1 / t93
  t396 = t395 * t37
  t410 = t43 ** 2
  t422 = 0.1e1 / t57 / t93
  t426 = t201 ** 2
  t430 = s0 * t422
  t432 = 0.40e2 / 0.9e1 * tau0 * t174 - 0.11e2 / 0.9e1 * t430
  t440 = t78 ** 2
  t444 = t196 ** 2
  t450 = t182 ** 2
  t460 = t74 * t430
  t462 = 0.3e1 / 0.4e1 * t432 * t49 * t184 - 0.3e1 / 0.4e1 * t183 * t54 * t188 * t196 + 0.81e2 / 0.80e2 * t72 / t79 / t440 * t444 - 0.27e2 / 0.40e2 * t189 * (0.5e1 * params.b * t432 * t75 + 0.50e2 / 0.9e1 * params.b * t450 * t92 + 0.25e2 / 0.9e1 * t73 * t92 * t432) + 0.22e2 / 0.81e2 * t460
  t473 = t217 ** 2
  t481 = 0.1e1 / t56 / t93 / t152
  t483 = t92 * t32 * t481
  t498 = (0.3e1 / 0.32e2 * t33 * t396 * t44 - 0.7e1 / 0.1024e4 * t159 / t211 * t162 * t165 + 0.3e1 / 0.32768e5 * params.c * t158 * t32 * t120 / t161 / t36 / t410) * t49 * t60 / 0.24e2 - 0.2e1 / 0.9e1 * t170 * t175 + 0.11e2 / 0.27e2 * t50 * t55 * t422 + 0.292e3 / 0.2025e4 * t426 + 0.292e3 / 0.2025e4 * t85 * t462 - 0.73e2 / 0.97200e5 * t462 * t101 - 0.73e2 / 0.97200e5 * t201 * t206 * t217 + 0.73e2 / 0.388800e6 * t85 / t101 / t100 * t473 - 0.73e2 / 0.194400e6 * t207 * (0.972e3 * t32 * t395 * t37 + 0.15200e5 / 0.9e1 * t483) + 0.475e3 / 0.531441e6 * t105 * t106 * t481 + t111 * t396 / 0.120e3 + t114 * t118 / t119 / t34 / 0.32e2
  t505 = t129 ** 2
  t508 = t104 * params.e
  t519 = t240 ** 2
  t525 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t373 * t30 * t136 - t380 / 0.4e1 + 0.3e1 / 0.4e1 * t5 * t29 * t242 + t390 + t393 / 0.4e1 + 0.3e1 / 0.8e1 * t150 * t151 * (-t498 * t130 * t104 - 0.4e1 / 0.9e1 * t230 * t234 * t236 * t199 - 0.2e1 / 0.27e2 * t124 / t505 * t508 * t483 + 0.22e2 / 0.27e2 * t237 * t460) * t133 + 0.3e1 / 0.8e1 * t150 * t151 * t519 * t133)
  t526 = t252 ** 2
  t527 = 0.1e1 / t526
  t528 = t254 ** 2
  t532 = f.my_piecewise5(t14, 0, t10, 0, -t368)
  t536 = f.my_piecewise3(t251, 0, 0.4e1 / 0.9e1 * t527 * t528 + 0.4e1 / 0.3e1 * t252 * t532)
  t543 = t5 * t257 * t145 * t346
  t548 = t5 * t351 * t386 * t346 / 0.12e2
  t550 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t5 * t536 * t30 * t346 - t543 / 0.4e1 + t548)
  d11 = 0.2e1 * t246 + 0.2e1 * t357 + t6 * (t525 + t550)
  t553 = -t7 - t24
  t554 = f.my_piecewise5(t10, 0, t14, 0, t553)
  t557 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t554)
  t563 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t557 * t30 * t136 - t149)
  t565 = f.my_piecewise5(t14, 0, t10, 0, -t553)
  t568 = f.my_piecewise3(t251, 0, 0.4e1 / 0.3e1 * t252 * t565)
  t573 = t5 * t351
  t574 = t261 * r1
  t575 = 0.1e1 / t574
  t576 = t575 * t264
  t580 = t259 ** 2
  t581 = params.c * t580
  t583 = t263 ** 2
  t584 = 0.1e1 / t583
  t587 = 0.1e1 / t270 / t269
  t592 = (-t260 * t576 * t271 / 0.32e2 + t581 / t311 * t584 * t587 / 0.1024e4) * t49
  t596 = 0.1e1 / t279 / t574
  t597 = t277 * t596
  t602 = s2 * t596
  t604 = -0.5e1 / 0.3e1 * tau1 * t281 + t602 / 0.3e1
  t605 = t604 * t49
  t606 = t54 * t301
  t610 = 0.1e1 / t300 / t299
  t611 = t294 * t610
  t618 = 0.5e1 * params.b * t604 * t296 + 0.25e2 / 0.9e1 * t295 * t92 * t604
  t621 = t74 * t602
  t623 = 0.3e1 / 0.4e1 * t605 * t606 - 0.27e2 / 0.40e2 * t611 * t618 - 0.2e1 / 0.27e2 * t621
  t628 = 0.1e1 / t318
  t629 = t306 * t628
  t633 = t310 * t261
  t635 = 0.1e1 / t278 / t633
  t639 = -0.324e3 * t259 * t575 * t264 - 0.800e3 / 0.3e1 * t92 * t259 * t635
  t652 = t592 * t282 / 0.24e2 - t276 * t597 / 0.9e1 + 0.292e3 / 0.2025e4 * t306 * t623 - 0.73e2 / 0.97200e5 * t623 * t318 - 0.73e2 / 0.194400e6 * t629 * t639 - 0.25e2 / 0.177147e6 * t105 * t321 * t635 - t325 * t576 / 0.360e3 - t114 * t329 / t330 / r1 / 0.288e3
  t656 = 0.1e1 / t339 / t338
  t658 = t335 * t656 * t236
  t661 = -t652 * t340 * t104 - 0.2e1 / 0.9e1 * t658 * t621
  t662 = t661 * t343
  t663 = t151 * t662
  t667 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t5 * t568 * t30 * t346 - t355 + 0.3e1 / 0.8e1 * t573 * t663)
  t671 = 0.2e1 * t366
  t672 = f.my_piecewise5(t10, 0, t14, 0, t671)
  t676 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t360 * t554 * t26 + 0.4e1 / 0.3e1 * t21 * t672)
  t683 = t5 * t557 * t145 * t136
  t691 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t676 * t30 * t136 - t683 / 0.8e1 + 0.3e1 / 0.8e1 * t5 * t557 * t242 - t380 / 0.8e1 + t390 + t393 / 0.8e1)
  t695 = f.my_piecewise5(t14, 0, t10, 0, -t671)
  t699 = f.my_piecewise3(t251, 0, 0.4e1 / 0.9e1 * t527 * t565 * t254 + 0.4e1 / 0.3e1 * t252 * t695)
  t706 = t5 * t568 * t145 * t346
  t713 = t573 * t391 * t662
  t716 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t5 * t699 * t30 * t346 - t706 / 0.8e1 - t543 / 0.8e1 + t548 + 0.3e1 / 0.8e1 * t5 * t257 * t663 + t713 / 0.8e1)
  d12 = t246 + t357 + t563 + t667 + t6 * (t691 + t716)
  t721 = t554 ** 2
  t725 = 0.2e1 * t23 + 0.2e1 * t366
  t726 = f.my_piecewise5(t10, 0, t14, 0, t725)
  t730 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t360 * t721 + 0.4e1 / 0.3e1 * t21 * t726)
  t737 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t730 * t30 * t136 - t683 / 0.4e1 + t390)
  t738 = t565 ** 2
  t742 = f.my_piecewise5(t14, 0, t10, 0, -t725)
  t746 = f.my_piecewise3(t251, 0, 0.4e1 / 0.9e1 * t527 * t738 + 0.4e1 / 0.3e1 * t252 * t742)
  t756 = 0.1e1 / t310
  t757 = t756 * t264
  t771 = t270 ** 2
  t783 = 0.1e1 / t279 / t310
  t787 = t623 ** 2
  t791 = s2 * t783
  t793 = 0.40e2 / 0.9e1 * tau1 * t596 - 0.11e2 / 0.9e1 * t791
  t801 = t299 ** 2
  t805 = t618 ** 2
  t811 = t604 ** 2
  t821 = t74 * t791
  t823 = 0.3e1 / 0.4e1 * t793 * t49 * t606 - 0.3e1 / 0.4e1 * t605 * t54 * t610 * t618 + 0.81e2 / 0.80e2 * t294 / t300 / t801 * t805 - 0.27e2 / 0.40e2 * t611 * (0.5e1 * params.b * t793 * t296 + 0.50e2 / 0.9e1 * params.b * t811 * t92 + 0.25e2 / 0.9e1 * t295 * t92 * t793) + 0.22e2 / 0.81e2 * t821
  t834 = t639 ** 2
  t842 = 0.1e1 / t278 / t310 / t574
  t844 = t92 * t259 * t842
  t859 = (0.3e1 / 0.32e2 * t260 * t757 * t271 - 0.7e1 / 0.1024e4 * t581 / t633 * t584 * t587 + 0.3e1 / 0.32768e5 * params.c * t580 * t259 * t331 / t583 / t263 / t771) * t49 * t282 / 0.24e2 - 0.2e1 / 0.9e1 * t592 * t597 + 0.11e2 / 0.27e2 * t276 * t277 * t783 + 0.292e3 / 0.2025e4 * t787 + 0.292e3 / 0.2025e4 * t306 * t823 - 0.73e2 / 0.97200e5 * t823 * t318 - 0.73e2 / 0.97200e5 * t623 * t628 * t639 + 0.73e2 / 0.388800e6 * t306 / t318 / t317 * t834 - 0.73e2 / 0.194400e6 * t629 * (0.972e3 * t259 * t756 * t264 + 0.15200e5 / 0.9e1 * t844) + 0.475e3 / 0.531441e6 * t105 * t321 * t842 + t325 * t757 / 0.120e3 + t114 * t329 / t330 / t261 / 0.32e2
  t866 = t339 ** 2
  t879 = t661 ** 2
  t885 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t5 * t746 * t30 * t346 - t706 / 0.4e1 + 0.3e1 / 0.4e1 * t5 * t568 * t663 + t548 + t713 / 0.4e1 + 0.3e1 / 0.8e1 * t573 * t151 * (-t859 * t340 * t104 - 0.4e1 / 0.9e1 * t652 * t656 * t236 * t621 - 0.2e1 / 0.27e2 * t335 / t866 * t508 * t844 + 0.22e2 / 0.27e2 * t658 * t821) * t343 + 0.3e1 / 0.8e1 * t573 * t151 * t879 * t343)
  d22 = 0.2e1 * t563 + 0.2e1 * t667 + t6 * (t737 + t885)
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
  t44 = s0 ** 2
  t45 = params.c * t44
  t46 = r0 ** 2
  t47 = 0.1e1 / t46
  t48 = tau0 ** 2
  t49 = 0.1e1 / t48
  t50 = t47 * t49
  t52 = t44 * t47 * t49
  t54 = 0.1e1 + t52 / 0.64e2
  t55 = t54 ** 2
  t56 = 0.1e1 / t55
  t61 = 6 ** (0.1e1 / 0.3e1)
  t62 = (0.10e2 / 0.81e2 + t45 * t50 * t56 / 0.64e2) * t61
  t63 = jnp.pi ** 2
  t64 = t63 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t66 = 0.1e1 / t65
  t67 = t66 * s0
  t68 = r0 ** (0.1e1 / 0.3e1)
  t69 = t68 ** 2
  t71 = 0.1e1 / t69 / t46
  t72 = t67 * t71
  t78 = s0 * t71
  t80 = tau0 / t69 / r0 - t78 / 0.8e1
  t84 = 0.5e1 / 0.9e1 * t80 * t61 * t66 - 0.1e1
  t85 = params.b * t80
  t86 = t61 * t66
  t87 = t86 * t84
  t90 = 0.5e1 * t85 * t87 + 0.9e1
  t91 = jnp.sqrt(t90)
  t92 = 0.1e1 / t91
  t97 = 0.27e2 / 0.20e2 * t84 * t92 + t86 * t78 / 0.36e2
  t98 = t97 ** 2
  t101 = t61 ** 2
  t103 = 0.1e1 / t64 / t63
  t104 = t101 * t103
  t105 = t46 ** 2
  t106 = t105 * r0
  t108 = 0.1e1 / t68 / t106
  t112 = 0.50e2 * t104 * t44 * t108 + 0.162e3 * t52
  t113 = jnp.sqrt(t112)
  t116 = 0.1e1 / params.kappa
  t117 = t116 * t101
  t118 = t103 * t44
  t122 = jnp.sqrt(params.e)
  t123 = t122 * t44
  t126 = params.e * params.mu
  t127 = t63 ** 2
  t128 = 0.1e1 / t127
  t129 = t44 * s0
  t130 = t128 * t129
  t131 = t105 ** 2
  t132 = 0.1e1 / t131
  t136 = t62 * t72 / 0.24e2 + 0.146e3 / 0.2025e4 * t98 - 0.73e2 / 0.97200e5 * t97 * t113 + 0.25e2 / 0.944784e6 * t117 * t118 * t108 + t123 * t50 / 0.720e3 + t126 * t130 * t132 / 0.2304e4
  t137 = t122 * t61
  t140 = 0.1e1 + t137 * t72 / 0.24e2
  t141 = t140 ** 2
  t142 = 0.1e1 / t141
  t145 = jnp.exp(-t136 * t142 * t116)
  t148 = 0.1e1 + params.kappa * (0.1e1 - t145)
  t154 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t155 = t42 ** 2
  t156 = 0.1e1 / t155
  t161 = t5 * t154
  t162 = t42 * params.kappa
  t163 = t46 * r0
  t164 = 0.1e1 / t163
  t165 = t164 * t49
  t169 = t44 ** 2
  t170 = params.c * t169
  t171 = 0.1e1 / t106
  t172 = t48 ** 2
  t173 = 0.1e1 / t172
  t176 = 0.1e1 / t55 / t54
  t181 = (-t45 * t165 * t56 / 0.32e2 + t170 * t171 * t173 * t176 / 0.1024e4) * t61
  t185 = 0.1e1 / t69 / t163
  t186 = t67 * t185
  t191 = s0 * t185
  t193 = -0.5e1 / 0.3e1 * tau0 * t71 + t191 / 0.3e1
  t194 = t193 * t61
  t195 = t66 * t92
  t199 = 0.1e1 / t91 / t90
  t200 = t84 * t199
  t204 = t104 * t193
  t207 = 0.5e1 * params.b * t193 * t87 + 0.25e2 / 0.9e1 * t85 * t204
  t210 = t86 * t191
  t212 = 0.3e1 / 0.4e1 * t194 * t195 - 0.27e2 / 0.40e2 * t200 * t207 - 0.2e1 / 0.27e2 * t210
  t217 = 0.1e1 / t113
  t218 = t97 * t217
  t222 = t105 * t46
  t224 = 0.1e1 / t68 / t222
  t228 = -0.324e3 * t44 * t164 * t49 - 0.800e3 / 0.3e1 * t104 * t44 * t224
  t237 = 0.1e1 / t131 / r0
  t241 = t181 * t72 / 0.24e2 - t62 * t186 / 0.9e1 + 0.292e3 / 0.2025e4 * t97 * t212 - 0.73e2 / 0.97200e5 * t212 * t113 - 0.73e2 / 0.194400e6 * t218 * t228 - 0.25e2 / 0.177147e6 * t117 * t118 * t224 - t123 * t165 / 0.360e3 - t126 * t130 * t237 / 0.288e3
  t245 = 0.1e1 / t141 / t140
  t247 = t116 * t122
  t248 = t136 * t245 * t247
  t251 = -t241 * t142 * t116 - 0.2e1 / 0.9e1 * t248 * t210
  t252 = t251 * t145
  t253 = t162 * t252
  t256 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t257 = t256 * f.p.zeta_threshold
  t259 = f.my_piecewise3(t20, t257, t21 * t19)
  t261 = 0.1e1 / t155 / t6
  t266 = t5 * t259
  t267 = t156 * params.kappa
  t268 = t267 * t252
  t271 = 0.1e1 / t105
  t272 = t271 * t49
  t282 = params.c * t169 * t44
  t284 = 0.1e1 / t172 / t48
  t286 = t55 ** 2
  t287 = 0.1e1 / t286
  t292 = (0.3e1 / 0.32e2 * t45 * t272 * t56 - 0.7e1 / 0.1024e4 * t170 / t222 * t173 * t176 + 0.3e1 / 0.32768e5 * t282 * t132 * t284 * t287) * t61
  t298 = 0.1e1 / t69 / t105
  t299 = t67 * t298
  t302 = t212 ** 2
  t306 = s0 * t298
  t308 = 0.40e2 / 0.9e1 * tau0 * t185 - 0.11e2 / 0.9e1 * t306
  t309 = t308 * t61
  t312 = t66 * t199
  t313 = t312 * t207
  t316 = t90 ** 2
  t318 = 0.1e1 / t91 / t316
  t319 = t84 * t318
  t320 = t207 ** 2
  t323 = params.b * t308
  t326 = t193 ** 2
  t333 = 0.5e1 * t323 * t87 + 0.50e2 / 0.9e1 * params.b * t326 * t104 + 0.25e2 / 0.9e1 * t85 * t104 * t308
  t336 = t86 * t306
  t338 = 0.3e1 / 0.4e1 * t309 * t195 - 0.3e1 / 0.4e1 * t194 * t313 + 0.81e2 / 0.80e2 * t319 * t320 - 0.27e2 / 0.40e2 * t200 * t333 + 0.22e2 / 0.81e2 * t336
  t343 = t212 * t217
  t347 = 0.1e1 / t113 / t112
  t348 = t97 * t347
  t349 = t228 ** 2
  t355 = t105 * t163
  t357 = 0.1e1 / t68 / t355
  t359 = t104 * t44 * t357
  t361 = 0.972e3 * t44 * t271 * t49 + 0.15200e5 / 0.9e1 * t359
  t374 = t292 * t72 / 0.24e2 - 0.2e1 / 0.9e1 * t181 * t186 + 0.11e2 / 0.27e2 * t62 * t299 + 0.292e3 / 0.2025e4 * t302 + 0.292e3 / 0.2025e4 * t97 * t338 - 0.73e2 / 0.97200e5 * t338 * t113 - 0.73e2 / 0.97200e5 * t343 * t228 + 0.73e2 / 0.388800e6 * t348 * t349 - 0.73e2 / 0.194400e6 * t218 * t361 + 0.475e3 / 0.531441e6 * t117 * t118 * t357 + t123 * t272 / 0.120e3 + t126 * t130 / t131 / t46 / 0.32e2
  t378 = t241 * t245 * t247
  t381 = t141 ** 2
  t382 = 0.1e1 / t381
  t384 = t116 * params.e
  t385 = t136 * t382 * t384
  t390 = -t374 * t142 * t116 - 0.4e1 / 0.9e1 * t378 * t210 - 0.2e1 / 0.27e2 * t385 * t359 + 0.22e2 / 0.27e2 * t248 * t336
  t391 = t390 * t145
  t392 = t162 * t391
  t395 = t251 ** 2
  t396 = t395 * t145
  t397 = t162 * t396
  t401 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t148 - t5 * t154 * t156 * t148 / 0.4e1 + 0.3e1 / 0.4e1 * t161 * t253 + t5 * t259 * t261 * t148 / 0.12e2 + t266 * t268 / 0.4e1 + 0.3e1 / 0.8e1 * t266 * t392 + 0.3e1 / 0.8e1 * t266 * t397)
  t403 = r1 <= f.p.dens_threshold
  t404 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t405 = 0.1e1 + t404
  t406 = t405 <= f.p.zeta_threshold
  t407 = t405 ** (0.1e1 / 0.3e1)
  t408 = t407 ** 2
  t409 = 0.1e1 / t408
  t411 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t412 = t411 ** 2
  t416 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t420 = f.my_piecewise3(t406, 0, 0.4e1 / 0.9e1 * t409 * t412 + 0.4e1 / 0.3e1 * t407 * t416)
  t422 = s2 ** 2
  t424 = r1 ** 2
  t425 = 0.1e1 / t424
  t426 = tau1 ** 2
  t427 = 0.1e1 / t426
  t428 = t425 * t427
  t430 = t422 * t425 * t427
  t433 = (0.1e1 + t430 / 0.64e2) ** 2
  t441 = r1 ** (0.1e1 / 0.3e1)
  t442 = t441 ** 2
  t444 = 0.1e1 / t442 / t424
  t445 = t66 * s2 * t444
  t451 = s2 * t444
  t453 = tau1 / t442 / r1 - t451 / 0.8e1
  t457 = 0.5e1 / 0.9e1 * t453 * t61 * t66 - 0.1e1
  t463 = jnp.sqrt(0.5e1 * params.b * t453 * t86 * t457 + 0.9e1)
  t469 = 0.27e2 / 0.20e2 * t457 / t463 + t86 * t451 / 0.36e2
  t470 = t469 ** 2
  t473 = t424 ** 2
  t476 = 0.1e1 / t441 / t473 / r1
  t481 = jnp.sqrt(0.50e2 * t104 * t422 * t476 + 0.162e3 * t430)
  t493 = t473 ** 2
  t502 = (0.1e1 + t137 * t445 / 0.24e2) ** 2
  t506 = jnp.exp(-((0.10e2 / 0.81e2 + params.c * t422 * t428 / t433 / 0.64e2) * t61 * t445 / 0.24e2 + 0.146e3 / 0.2025e4 * t470 - 0.73e2 / 0.97200e5 * t469 * t481 + 0.25e2 / 0.944784e6 * t117 * t103 * t422 * t476 + t122 * t422 * t428 / 0.720e3 + t126 * t128 * t422 * s2 / t493 / 0.2304e4) / t502 * t116)
  t509 = 0.1e1 + params.kappa * (0.1e1 - t506)
  t515 = f.my_piecewise3(t406, 0, 0.4e1 / 0.3e1 * t407 * t411)
  t521 = f.my_piecewise3(t406, t257, t407 * t405)
  t527 = f.my_piecewise3(t403, 0, -0.3e1 / 0.8e1 * t5 * t420 * t42 * t509 - t5 * t515 * t156 * t509 / 0.4e1 + t5 * t521 * t261 * t509 / 0.12e2)
  t554 = 0.1e1 / t155 / t24
  t567 = t24 ** 2
  t571 = 0.6e1 * t33 - 0.6e1 * t16 / t567
  t572 = f.my_piecewise5(t10, 0, t14, 0, t571)
  t576 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t572)
  t581 = t171 * t49
  t594 = t169 ** 2
  t597 = 0.1e1 / t131 / t163
  t598 = t172 ** 2
  t615 = 0.1e1 / t69 / t106
  t623 = s0 * t615
  t625 = -0.440e3 / 0.27e2 * tau0 * t298 + 0.154e3 / 0.27e2 * t623
  t659 = t86 * t623
  t661 = 0.3e1 / 0.4e1 * t625 * t61 * t195 - 0.9e1 / 0.8e1 * t309 * t313 + 0.27e2 / 0.16e2 * t194 * t66 * t318 * t320 - 0.9e1 / 0.8e1 * t194 * t312 * t333 - 0.81e2 / 0.32e2 * t84 / t91 / t316 / t90 * t320 * t207 + 0.243e3 / 0.80e2 * t319 * t207 * t333 - 0.27e2 / 0.40e2 * t200 * (0.5e1 * params.b * t625 * t87 + 0.50e2 / 0.3e1 * t323 * t204 + 0.25e2 / 0.9e1 * t85 * t104 * t625) - 0.308e3 / 0.243e3 * t659
  t674 = t112 ** 2
  t688 = 0.1e1 / t68 / t131
  t690 = t104 * t44 * t688
  t703 = (-0.3e1 / 0.8e1 * t45 * t581 * t56 + 0.3e1 / 0.64e2 * t170 / t355 * t173 * t176 - 0.45e2 / 0.32768e5 * t282 * t237 * t284 * t287 + 0.3e1 / 0.262144e6 * params.c * t594 * t597 / t598 / t286 / t54) * t61 * t72 / 0.24e2 - t292 * t186 / 0.3e1 + 0.11e2 / 0.9e1 * t181 * t299 - 0.154e3 / 0.81e2 * t62 * t67 * t615 + 0.292e3 / 0.675e3 * t212 * t338 + 0.292e3 / 0.2025e4 * t97 * t661 - 0.73e2 / 0.97200e5 * t661 * t113 - 0.73e2 / 0.64800e5 * t338 * t217 * t228 + 0.73e2 / 0.129600e6 * t212 * t347 * t349 - 0.73e2 / 0.64800e5 * t343 * t361 - 0.73e2 / 0.259200e6 * t97 / t113 / t674 * t349 * t228 + 0.73e2 / 0.129600e6 * t348 * t228 * t361 - 0.73e2 / 0.194400e6 * t218 * (-0.3888e4 * t44 * t171 * t49 - 0.334400e6 / 0.27e2 * t690) - 0.10450e5 / 0.1594323e7 * t117 * t118 * t688 - t123 * t581 / 0.30e2 - 0.5e1 / 0.16e2 * t126 * t130 * t597
  t749 = 0.9e1 / 0.8e1 * t5 * t259 * t42 * params.kappa * t390 * t252 + 0.3e1 / 0.8e1 * t266 * t162 * t395 * t251 * t145 + 0.9e1 / 0.8e1 * t161 * t397 + 0.3e1 / 0.8e1 * t266 * t267 * t396 - 0.3e1 / 0.8e1 * t5 * t41 * t156 * t148 + t5 * t154 * t261 * t148 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t259 * t554 * t148 - 0.3e1 / 0.8e1 * t5 * t576 * t42 * t148 + 0.3e1 / 0.8e1 * t266 * t162 * (-t703 * t142 * t116 - 0.2e1 / 0.3e1 * t374 * t245 * t247 * t210 - 0.2e1 / 0.9e1 * t241 * t382 * t384 * t359 + 0.22e2 / 0.9e1 * t378 * t336 - 0.16e2 / 0.81e2 * t136 / t381 / t140 * t116 * t122 * params.e * t128 * t129 * t597 + 0.22e2 / 0.27e2 * t385 * t690 - 0.308e3 / 0.81e2 * t248 * t659) * t145 + 0.9e1 / 0.8e1 * t5 * t41 * t253 + 0.3e1 / 0.4e1 * t161 * t268 + 0.9e1 / 0.8e1 * t161 * t392 - t266 * t261 * params.kappa * t252 / 0.4e1 + 0.3e1 / 0.8e1 * t266 * t267 * t391
  t750 = f.my_piecewise3(t1, 0, t749)
  t760 = f.my_piecewise5(t14, 0, t10, 0, -t571)
  t764 = f.my_piecewise3(t406, 0, -0.8e1 / 0.27e2 / t408 / t405 * t412 * t411 + 0.4e1 / 0.3e1 * t409 * t411 * t416 + 0.4e1 / 0.3e1 * t407 * t760)
  t782 = f.my_piecewise3(t403, 0, -0.3e1 / 0.8e1 * t5 * t764 * t42 * t509 - 0.3e1 / 0.8e1 * t5 * t420 * t156 * t509 + t5 * t515 * t261 * t509 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t521 * t554 * t509)
  d111 = 0.3e1 * t401 + 0.3e1 * t527 + t6 * (t750 + t782)

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
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = t21 * f.p.zeta_threshold
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t20, t22, t23 * t19)
  t26 = t6 ** (0.1e1 / 0.3e1)
  t28 = t5 * t25 * t26
  t29 = s0 ** 2
  t30 = params.c * t29
  t31 = r0 ** 2
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = tau0 ** 2
  t35 = 0.1e1 / t34
  t36 = t33 * t35
  t37 = 0.1e1 / t31
  t39 = t29 * t37 * t35
  t41 = 0.1e1 + t39 / 0.64e2
  t42 = t41 ** 2
  t43 = 0.1e1 / t42
  t47 = t29 ** 2
  t48 = params.c * t47
  t49 = t32 * t31
  t50 = 0.1e1 / t49
  t51 = t34 ** 2
  t52 = 0.1e1 / t51
  t55 = 0.1e1 / t42 / t41
  t60 = params.c * t47 * t29
  t61 = t32 ** 2
  t62 = 0.1e1 / t61
  t64 = 0.1e1 / t51 / t34
  t66 = t42 ** 2
  t67 = 0.1e1 / t66
  t72 = 6 ** (0.1e1 / 0.3e1)
  t73 = (0.3e1 / 0.32e2 * t30 * t36 * t43 - 0.7e1 / 0.1024e4 * t48 * t50 * t52 * t55 + 0.3e1 / 0.32768e5 * t60 * t62 * t64 * t67) * t72
  t74 = jnp.pi ** 2
  t75 = t74 ** (0.1e1 / 0.3e1)
  t76 = t75 ** 2
  t77 = 0.1e1 / t76
  t78 = t77 * s0
  t79 = r0 ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t82 = 0.1e1 / t80 / t31
  t83 = t78 * t82
  t86 = t31 * r0
  t87 = 0.1e1 / t86
  t88 = t87 * t35
  t92 = t32 * r0
  t93 = 0.1e1 / t92
  t99 = (-t30 * t88 * t43 / 0.32e2 + t48 * t93 * t52 * t55 / 0.1024e4) * t72
  t101 = 0.1e1 / t80 / t86
  t102 = t78 * t101
  t105 = t37 * t35
  t110 = (0.10e2 / 0.81e2 + t30 * t105 * t43 / 0.64e2) * t72
  t112 = 0.1e1 / t80 / t32
  t113 = t78 * t112
  t118 = s0 * t101
  t120 = -0.5e1 / 0.3e1 * tau0 * t82 + t118 / 0.3e1
  t121 = t120 * t72
  t125 = s0 * t82
  t127 = tau0 / t80 / r0 - t125 / 0.8e1
  t128 = params.b * t127
  t129 = t72 * t77
  t133 = 0.5e1 / 0.9e1 * t127 * t72 * t77 - 0.1e1
  t134 = t129 * t133
  t137 = 0.5e1 * t128 * t134 + 0.9e1
  t138 = jnp.sqrt(t137)
  t139 = 0.1e1 / t138
  t140 = t77 * t139
  t144 = 0.1e1 / t138 / t137
  t145 = t133 * t144
  t149 = t72 ** 2
  t151 = 0.1e1 / t75 / t74
  t152 = t149 * t151
  t153 = t152 * t120
  t156 = 0.5e1 * params.b * t120 * t134 + 0.25e2 / 0.9e1 * t128 * t153
  t159 = t129 * t118
  t161 = 0.3e1 / 0.4e1 * t121 * t140 - 0.27e2 / 0.40e2 * t145 * t156 - 0.2e1 / 0.27e2 * t159
  t162 = t161 ** 2
  t168 = 0.27e2 / 0.20e2 * t133 * t139 + t129 * t125 / 0.36e2
  t171 = s0 * t112
  t173 = 0.40e2 / 0.9e1 * tau0 * t101 - 0.11e2 / 0.9e1 * t171
  t174 = t173 * t72
  t177 = t77 * t144
  t178 = t177 * t156
  t181 = t137 ** 2
  t183 = 0.1e1 / t138 / t181
  t184 = t133 * t183
  t185 = t156 ** 2
  t188 = params.b * t173
  t191 = t120 ** 2
  t198 = 0.5e1 * t188 * t134 + 0.50e2 / 0.9e1 * params.b * t191 * t152 + 0.25e2 / 0.9e1 * t128 * t152 * t173
  t201 = t129 * t171
  t203 = 0.3e1 / 0.4e1 * t174 * t140 - 0.3e1 / 0.4e1 * t121 * t178 + 0.81e2 / 0.80e2 * t184 * t185 - 0.27e2 / 0.40e2 * t145 * t198 + 0.22e2 / 0.81e2 * t201
  t208 = 0.1e1 / t79 / t92
  t212 = 0.50e2 * t152 * t29 * t208 + 0.162e3 * t39
  t213 = jnp.sqrt(t212)
  t216 = 0.1e1 / t213
  t217 = t161 * t216
  t222 = 0.1e1 / t79 / t49
  t226 = -0.324e3 * t29 * t87 * t35 - 0.800e3 / 0.3e1 * t152 * t29 * t222
  t230 = 0.1e1 / t213 / t212
  t231 = t168 * t230
  t232 = t226 ** 2
  t235 = t168 * t216
  t239 = t32 * t86
  t241 = 0.1e1 / t79 / t239
  t243 = t152 * t29 * t241
  t245 = 0.972e3 * t29 * t33 * t35 + 0.15200e5 / 0.9e1 * t243
  t248 = 0.1e1 / params.kappa
  t249 = t248 * t149
  t250 = t151 * t29
  t254 = jnp.sqrt(params.e)
  t255 = t254 * t29
  t258 = params.e * params.mu
  t259 = t74 ** 2
  t260 = 0.1e1 / t259
  t261 = t29 * s0
  t262 = t260 * t261
  t264 = 0.1e1 / t61 / t31
  t268 = t73 * t83 / 0.24e2 - 0.2e1 / 0.9e1 * t99 * t102 + 0.11e2 / 0.27e2 * t110 * t113 + 0.292e3 / 0.2025e4 * t162 + 0.292e3 / 0.2025e4 * t168 * t203 - 0.73e2 / 0.97200e5 * t203 * t213 - 0.73e2 / 0.97200e5 * t217 * t226 + 0.73e2 / 0.388800e6 * t231 * t232 - 0.73e2 / 0.194400e6 * t235 * t245 + 0.475e3 / 0.531441e6 * t249 * t250 * t241 + t255 * t36 / 0.120e3 + t258 * t262 * t264 / 0.32e2
  t269 = t254 * t72
  t272 = 0.1e1 + t269 * t83 / 0.24e2
  t273 = t272 ** 2
  t274 = 0.1e1 / t273
  t292 = t61 * r0
  t293 = 0.1e1 / t292
  t297 = t99 * t83 / 0.24e2 - t110 * t102 / 0.9e1 + 0.292e3 / 0.2025e4 * t168 * t161 - 0.73e2 / 0.97200e5 * t161 * t213 - 0.73e2 / 0.194400e6 * t235 * t226 - 0.25e2 / 0.177147e6 * t249 * t250 * t222 - t255 * t88 / 0.360e3 - t258 * t262 * t293 / 0.288e3
  t299 = 0.1e1 / t273 / t272
  t301 = t248 * t254
  t302 = t297 * t299 * t301
  t307 = t168 ** 2
  t319 = t110 * t83 / 0.24e2 + 0.146e3 / 0.2025e4 * t307 - 0.73e2 / 0.97200e5 * t168 * t213 + 0.25e2 / 0.944784e6 * t249 * t250 * t208 + t255 * t105 / 0.720e3 + t258 * t262 * t62 / 0.2304e4
  t320 = t273 ** 2
  t321 = 0.1e1 / t320
  t323 = t248 * params.e
  t324 = t319 * t321 * t323
  t328 = t319 * t299 * t301
  t331 = -t268 * t274 * t248 - 0.4e1 / 0.9e1 * t302 * t159 - 0.2e1 / 0.27e2 * t324 * t243 + 0.22e2 / 0.27e2 * t328 * t201
  t332 = params.kappa * t331
  t337 = -t297 * t274 * t248 - 0.2e1 / 0.9e1 * t328 * t159
  t340 = jnp.exp(-t319 * t274 * t248)
  t341 = t337 * t340
  t342 = t332 * t341
  t345 = t5 * t25
  t346 = t26 * params.kappa
  t347 = t337 ** 2
  t349 = t347 * t337 * t340
  t350 = t346 * t349
  t353 = t26 ** 2
  t354 = 0.1e1 / t353
  t355 = t354 * params.kappa
  t356 = t347 * t340
  t357 = t355 * t356
  t360 = t6 ** 2
  t361 = 0.1e1 / t360
  t363 = -t16 * t361 + t7
  t364 = f.my_piecewise5(t10, 0, t14, 0, t363)
  t367 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t364)
  t368 = t5 * t367
  t369 = t346 * t356
  t372 = t23 ** 2
  t373 = 0.1e1 / t372
  t374 = t364 ** 2
  t377 = t360 * t6
  t378 = 0.1e1 / t377
  t381 = 0.2e1 * t16 * t378 - 0.2e1 * t361
  t382 = f.my_piecewise5(t10, 0, t14, 0, t381)
  t386 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t373 * t374 + 0.4e1 / 0.3e1 * t23 * t382)
  t390 = 0.1e1 + params.kappa * (0.1e1 - t340)
  t395 = 0.1e1 / t353 / t6
  t401 = 0.1e1 / t353 / t360
  t407 = 0.1e1 / t372 / t19
  t411 = t373 * t364
  t414 = t360 ** 2
  t415 = 0.1e1 / t414
  t418 = -0.6e1 * t16 * t415 + 0.6e1 * t378
  t419 = f.my_piecewise5(t10, 0, t14, 0, t418)
  t423 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t407 * t374 * t364 + 0.4e1 / 0.3e1 * t411 * t382 + 0.4e1 / 0.3e1 * t23 * t419)
  t428 = t93 * t35
  t441 = t47 ** 2
  t442 = params.c * t441
  t444 = 0.1e1 / t61 / t86
  t445 = t51 ** 2
  t446 = 0.1e1 / t445
  t449 = 0.1e1 / t66 / t41
  t454 = (-0.3e1 / 0.8e1 * t30 * t428 * t43 + 0.3e1 / 0.64e2 * t48 / t239 * t52 * t55 - 0.45e2 / 0.32768e5 * t60 * t293 * t64 * t67 + 0.3e1 / 0.262144e6 * t442 * t444 * t446 * t449) * t72
  t462 = 0.1e1 / t80 / t92
  t463 = t78 * t462
  t470 = s0 * t462
  t472 = -0.440e3 / 0.27e2 * tau0 * t112 + 0.154e3 / 0.27e2 * t470
  t473 = t472 * t72
  t479 = t77 * t183 * t185
  t482 = t177 * t198
  t487 = 0.1e1 / t138 / t181 / t137
  t488 = t133 * t487
  t489 = t185 * t156
  t495 = params.b * t472
  t503 = 0.5e1 * t495 * t134 + 0.50e2 / 0.3e1 * t188 * t153 + 0.25e2 / 0.9e1 * t128 * t152 * t472
  t506 = t129 * t470
  t508 = 0.3e1 / 0.4e1 * t473 * t140 - 0.9e1 / 0.8e1 * t174 * t178 + 0.27e2 / 0.16e2 * t121 * t479 - 0.9e1 / 0.8e1 * t121 * t482 - 0.81e2 / 0.32e2 * t488 * t489 + 0.243e3 / 0.80e2 * t184 * t156 * t198 - 0.27e2 / 0.40e2 * t145 * t503 - 0.308e3 / 0.243e3 * t506
  t513 = t203 * t216
  t516 = t161 * t230
  t521 = t212 ** 2
  t523 = 0.1e1 / t213 / t521
  t524 = t168 * t523
  t525 = t232 * t226
  t528 = t226 * t245
  t535 = 0.1e1 / t79 / t61
  t537 = t152 * t29 * t535
  t539 = -0.3888e4 * t29 * t93 * t35 - 0.334400e6 / 0.27e2 * t537
  t550 = t454 * t83 / 0.24e2 - t73 * t102 / 0.3e1 + 0.11e2 / 0.9e1 * t99 * t113 - 0.154e3 / 0.81e2 * t110 * t463 + 0.292e3 / 0.675e3 * t161 * t203 + 0.292e3 / 0.2025e4 * t168 * t508 - 0.73e2 / 0.97200e5 * t508 * t213 - 0.73e2 / 0.64800e5 * t513 * t226 + 0.73e2 / 0.129600e6 * t516 * t232 - 0.73e2 / 0.64800e5 * t217 * t245 - 0.73e2 / 0.259200e6 * t524 * t525 + 0.73e2 / 0.129600e6 * t231 * t528 - 0.73e2 / 0.194400e6 * t235 * t539 - 0.10450e5 / 0.1594323e7 * t249 * t250 * t535 - t255 * t428 / 0.30e2 - 0.5e1 / 0.16e2 * t258 * t262 * t444
  t554 = t268 * t299 * t301
  t558 = t297 * t321 * t323
  t564 = 0.1e1 / t320 / t272
  t566 = t319 * t564 * t248
  t568 = t254 * params.e * t260
  t570 = t568 * t261 * t444
  t577 = -t550 * t274 * t248 - 0.2e1 / 0.3e1 * t554 * t159 - 0.2e1 / 0.9e1 * t558 * t243 + 0.22e2 / 0.9e1 * t302 * t201 - 0.16e2 / 0.81e2 * t566 * t570 + 0.22e2 / 0.27e2 * t324 * t537 - 0.308e3 / 0.81e2 * t328 * t506
  t578 = t577 * t340
  t579 = t346 * t578
  t582 = t5 * t386
  t583 = t346 * t341
  t586 = t355 * t341
  t589 = t331 * t340
  t590 = t346 * t589
  t593 = t395 * params.kappa
  t594 = t593 * t341
  t597 = t355 * t589
  t600 = 0.9e1 / 0.8e1 * t28 * t342 + 0.3e1 / 0.8e1 * t345 * t350 + 0.3e1 / 0.8e1 * t345 * t357 + 0.9e1 / 0.8e1 * t368 * t369 - 0.3e1 / 0.8e1 * t5 * t386 * t354 * t390 + t5 * t367 * t395 * t390 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t25 * t401 * t390 - 0.3e1 / 0.8e1 * t5 * t423 * t26 * t390 + 0.3e1 / 0.8e1 * t345 * t579 + 0.9e1 / 0.8e1 * t582 * t583 + 0.3e1 / 0.4e1 * t368 * t586 + 0.9e1 / 0.8e1 * t368 * t590 - t345 * t594 / 0.4e1 + 0.3e1 / 0.8e1 * t345 * t597
  t601 = f.my_piecewise3(t1, 0, t600)
  t603 = r1 <= f.p.dens_threshold
  t604 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t605 = 0.1e1 + t604
  t606 = t605 <= f.p.zeta_threshold
  t607 = t605 ** (0.1e1 / 0.3e1)
  t608 = t607 ** 2
  t610 = 0.1e1 / t608 / t605
  t612 = f.my_piecewise5(t14, 0, t10, 0, -t363)
  t613 = t612 ** 2
  t617 = 0.1e1 / t608
  t618 = t617 * t612
  t620 = f.my_piecewise5(t14, 0, t10, 0, -t381)
  t624 = f.my_piecewise5(t14, 0, t10, 0, -t418)
  t628 = f.my_piecewise3(t606, 0, -0.8e1 / 0.27e2 * t610 * t613 * t612 + 0.4e1 / 0.3e1 * t618 * t620 + 0.4e1 / 0.3e1 * t607 * t624)
  t630 = s2 ** 2
  t632 = r1 ** 2
  t633 = 0.1e1 / t632
  t634 = tau1 ** 2
  t635 = 0.1e1 / t634
  t636 = t633 * t635
  t638 = t630 * t633 * t635
  t641 = (0.1e1 + t638 / 0.64e2) ** 2
  t649 = r1 ** (0.1e1 / 0.3e1)
  t650 = t649 ** 2
  t652 = 0.1e1 / t650 / t632
  t653 = t77 * s2 * t652
  t659 = s2 * t652
  t661 = tau1 / t650 / r1 - t659 / 0.8e1
  t665 = 0.5e1 / 0.9e1 * t661 * t72 * t77 - 0.1e1
  t671 = jnp.sqrt(0.5e1 * params.b * t661 * t129 * t665 + 0.9e1)
  t677 = 0.27e2 / 0.20e2 * t665 / t671 + t129 * t659 / 0.36e2
  t678 = t677 ** 2
  t681 = t632 ** 2
  t684 = 0.1e1 / t649 / t681 / r1
  t689 = jnp.sqrt(0.50e2 * t152 * t630 * t684 + 0.162e3 * t638)
  t701 = t681 ** 2
  t710 = (0.1e1 + t269 * t653 / 0.24e2) ** 2
  t714 = jnp.exp(-((0.10e2 / 0.81e2 + params.c * t630 * t636 / t641 / 0.64e2) * t72 * t653 / 0.24e2 + 0.146e3 / 0.2025e4 * t678 - 0.73e2 / 0.97200e5 * t677 * t689 + 0.25e2 / 0.944784e6 * t249 * t151 * t630 * t684 + t254 * t630 * t636 / 0.720e3 + t258 * t260 * t630 * s2 / t701 / 0.2304e4) / t710 * t248)
  t717 = 0.1e1 + params.kappa * (0.1e1 - t714)
  t726 = f.my_piecewise3(t606, 0, 0.4e1 / 0.9e1 * t617 * t613 + 0.4e1 / 0.3e1 * t607 * t620)
  t733 = f.my_piecewise3(t606, 0, 0.4e1 / 0.3e1 * t607 * t612)
  t739 = f.my_piecewise3(t606, t22, t607 * t605)
  t745 = f.my_piecewise3(t603, 0, -0.3e1 / 0.8e1 * t5 * t628 * t26 * t717 - 0.3e1 / 0.8e1 * t5 * t726 * t354 * t717 + t5 * t733 * t395 * t717 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t739 * t401 * t717)
  t763 = 0.1e1 / t353 / t377
  t772 = t19 ** 2
  t775 = t374 ** 2
  t781 = t382 ** 2
  t790 = -0.24e2 * t415 + 0.24e2 * t16 / t414 / t6
  t791 = f.my_piecewise5(t10, 0, t14, 0, t790)
  t795 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t372 / t772 * t775 - 0.16e2 / 0.9e1 * t407 * t374 * t382 + 0.4e1 / 0.3e1 * t373 * t781 + 0.16e2 / 0.9e1 * t411 * t419 + 0.4e1 / 0.3e1 * t23 * t791)
  t811 = t331 ** 2
  t819 = t347 ** 2
  t824 = 0.3e1 / 0.2e1 * t28 * params.kappa * t577 * t341 + 0.9e1 / 0.4e1 * t28 * t332 * t356 + 0.3e1 / 0.2e1 * t5 * t25 * t354 * t342 + 0.9e1 / 0.2e1 * t5 * t367 * t26 * t342 + 0.10e2 / 0.27e2 * t5 * t25 * t763 * t390 - t5 * t423 * t354 * t390 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t795 * t26 * t390 + t5 * t386 * t395 * t390 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t367 * t401 * t390 + t345 * t355 * t578 / 0.2e1 + 0.9e1 / 0.8e1 * t345 * t346 * t811 * t340 + t345 * t355 * t349 / 0.2e1 + 0.3e1 / 0.8e1 * t345 * t346 * t819 * t340
  t842 = t203 ** 2
  t849 = 0.1e1 / t80 / t49
  t850 = s0 * t849
  t852 = 0.6160e4 / 0.81e2 * tau0 * t462 - 0.2618e4 / 0.81e2 * t850
  t874 = t181 ** 2
  t878 = t185 ** 2
  t884 = t198 ** 2
  t895 = t173 ** 2
  t905 = t129 * t850
  t907 = 0.3e1 / 0.4e1 * t852 * t72 * t140 - 0.3e1 / 0.2e1 * t473 * t178 + 0.27e2 / 0.8e1 * t174 * t479 - 0.9e1 / 0.4e1 * t174 * t482 - 0.45e2 / 0.8e1 * t121 * t77 * t487 * t489 + 0.27e2 / 0.4e1 * t121 * t77 * t183 * t156 * t198 - 0.3e1 / 0.2e1 * t121 * t177 * t503 + 0.567e3 / 0.64e2 * t133 / t138 / t874 * t878 - 0.243e3 / 0.16e2 * t488 * t185 * t198 + 0.243e3 / 0.80e2 * t184 * t884 + 0.81e2 / 0.20e2 * t184 * t156 * t503 - 0.27e2 / 0.40e2 * t145 * (0.5e1 * params.b * t852 * t134 + 0.200e3 / 0.9e1 * t495 * t153 + 0.50e2 / 0.3e1 * params.b * t895 * t152 + 0.25e2 / 0.9e1 * t128 * t152 * t852) + 0.5236e4 / 0.729e3 * t905
  t923 = 0.1e1 / t79 / t292
  t925 = t152 * t29 * t923
  t934 = 0.1e1 / t61 / t32
  t938 = t50 * t35
  t956 = t61 * t49
  t970 = 0.292e3 / 0.675e3 * t842 + 0.1168e4 / 0.2025e4 * t161 * t508 + 0.292e3 / 0.2025e4 * t168 * t907 - 0.73e2 / 0.97200e5 * t907 * t213 - 0.73e2 / 0.48600e5 * t508 * t216 * t226 - 0.73e2 / 0.32400e5 * t513 * t245 - 0.73e2 / 0.48600e5 * t217 * t539 - 0.73e2 / 0.194400e6 * t235 * (0.19440e5 * t29 * t50 * t35 + 0.8360000e7 / 0.81e2 * t925) + 0.261250e6 / 0.4782969e7 * t249 * t250 * t923 + 0.55e2 / 0.16e2 * t258 * t262 * t934 + (0.15e2 / 0.8e1 * t30 * t938 * t43 - 0.45e2 / 0.128e3 * t48 * t62 * t52 * t55 + 0.549e3 / 0.32768e5 * t60 * t264 * t64 * t67 - 0.39e2 / 0.131072e6 * t442 * t934 * t446 * t449 + 0.15e2 / 0.8388608e7 * params.c * t441 * t29 / t956 / t445 / t34 / t66 / t42) * t72 * t83 / 0.24e2
  t983 = t232 ** 2
  t989 = t245 ** 2
  t1006 = 0.73e2 / 0.64800e5 * t203 * t230 * t232 - 0.73e2 / 0.64800e5 * t161 * t523 * t525 + 0.73e2 / 0.32400e5 * t516 * t528 + 0.73e2 / 0.103680e6 * t168 / t213 / t521 / t212 * t983 - 0.73e2 / 0.43200e5 * t524 * t232 * t245 + 0.73e2 / 0.129600e6 * t231 * t989 + 0.73e2 / 0.97200e5 * t231 * t226 * t539 + t255 * t938 / 0.6e1 - 0.4e1 / 0.9e1 * t454 * t102 + 0.22e2 / 0.9e1 * t73 * t113 - 0.616e3 / 0.81e2 * t99 * t463 + 0.2618e4 / 0.243e3 * t110 * t78 * t849
  t1031 = params.e ** 2
  t1050 = -(t970 + t1006) * t274 * t248 - 0.8e1 / 0.9e1 * t550 * t299 * t301 * t159 - 0.4e1 / 0.9e1 * t268 * t321 * t323 * t243 + 0.44e2 / 0.9e1 * t554 * t201 - 0.64e2 / 0.81e2 * t297 * t564 * t248 * t570 + 0.88e2 / 0.27e2 * t558 * t537 - 0.1232e4 / 0.81e2 * t302 * t506 - 0.80e2 / 0.729e3 * t319 / t320 / t273 * t248 * t1031 * t260 * t47 / t80 / t956 * t72 * t77 + 0.352e3 / 0.81e2 * t566 * t568 * t261 * t934 - 0.1958e4 / 0.243e3 * t324 * t925 + 0.5236e4 / 0.243e3 * t328 * t905
  t1066 = -t345 * t593 * t356 / 0.2e1 + 0.3e1 / 0.2e1 * t368 * t597 - t345 * t593 * t589 / 0.2e1 + 0.5e1 / 0.9e1 * t345 * t401 * params.kappa * t341 + 0.3e1 / 0.2e1 * t5 * t423 * t583 + 0.3e1 / 0.2e1 * t368 * t579 + 0.3e1 / 0.8e1 * t345 * t346 * t1050 * t340 + 0.9e1 / 0.4e1 * t582 * t590 + 0.3e1 / 0.2e1 * t368 * t350 + 0.3e1 / 0.2e1 * t368 * t357 + 0.9e1 / 0.4e1 * t582 * t369 + 0.3e1 / 0.2e1 * t582 * t586 - t368 * t594
  t1068 = f.my_piecewise3(t1, 0, t824 + t1066)
  t1069 = t605 ** 2
  t1072 = t613 ** 2
  t1078 = t620 ** 2
  t1084 = f.my_piecewise5(t14, 0, t10, 0, -t790)
  t1088 = f.my_piecewise3(t606, 0, 0.40e2 / 0.81e2 / t608 / t1069 * t1072 - 0.16e2 / 0.9e1 * t610 * t613 * t620 + 0.4e1 / 0.3e1 * t617 * t1078 + 0.16e2 / 0.9e1 * t618 * t624 + 0.4e1 / 0.3e1 * t607 * t1084)
  t1110 = f.my_piecewise3(t603, 0, -0.3e1 / 0.8e1 * t5 * t1088 * t26 * t717 - t5 * t628 * t354 * t717 / 0.2e1 + t5 * t726 * t395 * t717 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t733 * t401 * t717 + 0.10e2 / 0.27e2 * t5 * t739 * t763 * t717)
  d1111 = 0.4e1 * t601 + 0.4e1 * t745 + t6 * (t1068 + t1110)

  res = {'v4rho4': d1111}
  return res
