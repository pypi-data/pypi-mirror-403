"""Generated from mgga_x_mbr.mpl."""

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))
  params_lambda__raw = params.lambda__
  if isinstance(params_lambda__raw, (str, bytes, dict)):
    params_lambda_ = params_lambda__raw
  else:
    try:
      params_lambda__seq = list(params_lambda__raw)
    except TypeError:
      params_lambda_ = params_lambda__raw
    else:
      params_lambda__seq = np.asarray(params_lambda__seq, dtype=np.float64)
      params_lambda_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_lambda__seq))

  br89_min_Q = 5e-13

  br89_v = lambda x: -2 * jnp.pi ** (1 / 3) / X_FACTOR_C * jnp.exp(x / 3) * (1 - jnp.exp(-x) * (1 + x / 2)) / x

  br89_mx = lambda Q: br89_x(Q)

  params_at = 0

  tm_p = lambda x: (X2S * x) ** 2

  mbr_D = lambda ts, xs: 2 * ts - 1 / 4 * (2 * params_lambda_ - 1) ** 2 * xs ** 2

  k_sigma = (6 * jnp.pi ** 2) ** (1 / 3)

  br89_cQ = lambda Q: f.my_piecewise3(jnp.abs(Q) < br89_min_Q, f.my_piecewise3(Q > 0, br89_min_Q, -br89_min_Q), Q)

  tm_y = lambda x: (2 * params_lambda_ - 1) ** 2 * tm_p(x)

  tm_f0 = lambda x: (1 + 10 * (70 / 27) * tm_y(x) + params_beta * tm_y(x) ** 2) ** (1 / 10)

  br89_Q = lambda x, u, t: 1 / 6 * (+6 * (params_lambda_ ** 2 - params_lambda_ + 1 / 2) * (2 * t - 2 * K_FACTOR_C - 1 / 36 * x ** 2) + 6 / 5 * k_sigma ** 2 * (tm_f0(x) ** 2 - 1) - 2 * params_gamma * mbr_D(t, x))

  br89_f = lambda x, u, t: -br89_v(br89_mx(br89_cQ(br89_Q(x, u, t)))) / 2 * (1 + params_at * mgga_series_w(np.array([np.nan, 0, 1, 0, -2, 0, 1], dtype=np.float64), 6, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, br89_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))
  params_lambda__raw = params.lambda__
  if isinstance(params_lambda__raw, (str, bytes, dict)):
    params_lambda_ = params_lambda__raw
  else:
    try:
      params_lambda__seq = list(params_lambda__raw)
    except TypeError:
      params_lambda_ = params_lambda__raw
    else:
      params_lambda__seq = np.asarray(params_lambda__seq, dtype=np.float64)
      params_lambda_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_lambda__seq))

  br89_min_Q = 5e-13

  br89_v = lambda x: -2 * jnp.pi ** (1 / 3) / X_FACTOR_C * jnp.exp(x / 3) * (1 - jnp.exp(-x) * (1 + x / 2)) / x

  br89_mx = lambda Q: br89_x(Q)

  params_at = 0

  tm_p = lambda x: (X2S * x) ** 2

  mbr_D = lambda ts, xs: 2 * ts - 1 / 4 * (2 * params_lambda_ - 1) ** 2 * xs ** 2

  k_sigma = (6 * jnp.pi ** 2) ** (1 / 3)

  br89_cQ = lambda Q: f.my_piecewise3(jnp.abs(Q) < br89_min_Q, f.my_piecewise3(Q > 0, br89_min_Q, -br89_min_Q), Q)

  tm_y = lambda x: (2 * params_lambda_ - 1) ** 2 * tm_p(x)

  tm_f0 = lambda x: (1 + 10 * (70 / 27) * tm_y(x) + params_beta * tm_y(x) ** 2) ** (1 / 10)

  br89_Q = lambda x, u, t: 1 / 6 * (+6 * (params_lambda_ ** 2 - params_lambda_ + 1 / 2) * (2 * t - 2 * K_FACTOR_C - 1 / 36 * x ** 2) + 6 / 5 * k_sigma ** 2 * (tm_f0(x) ** 2 - 1) - 2 * params_gamma * mbr_D(t, x))

  br89_f = lambda x, u, t: -br89_v(br89_mx(br89_cQ(br89_Q(x, u, t)))) / 2 * (1 + params_at * mgga_series_w(np.array([np.nan, 0, 1, 0, -2, 0, 1], dtype=np.float64), 6, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, br89_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))
  params_lambda__raw = params.lambda__
  if isinstance(params_lambda__raw, (str, bytes, dict)):
    params_lambda_ = params_lambda__raw
  else:
    try:
      params_lambda__seq = list(params_lambda__raw)
    except TypeError:
      params_lambda_ = params_lambda__raw
    else:
      params_lambda__seq = np.asarray(params_lambda__seq, dtype=np.float64)
      params_lambda_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_lambda__seq))

  br89_min_Q = 5e-13

  br89_v = lambda x: -2 * jnp.pi ** (1 / 3) / X_FACTOR_C * jnp.exp(x / 3) * (1 - jnp.exp(-x) * (1 + x / 2)) / x

  br89_mx = lambda Q: br89_x(Q)

  params_at = 0

  tm_p = lambda x: (X2S * x) ** 2

  mbr_D = lambda ts, xs: 2 * ts - 1 / 4 * (2 * params_lambda_ - 1) ** 2 * xs ** 2

  k_sigma = (6 * jnp.pi ** 2) ** (1 / 3)

  tm_y = lambda x: (2 * params_lambda_ - 1) ** 2 * tm_p(x)

  tm_f0 = lambda x: (1 + 10 * (70 / 27) * tm_y(x) + params_beta * tm_y(x) ** 2) ** (1 / 10)

  br89_Q = lambda x, u, t: 1 / 6 * (+6 * (params_lambda_ ** 2 - params_lambda_ + 1 / 2) * (2 * t - 2 * K_FACTOR_C - 1 / 36 * x ** 2) + 6 / 5 * k_sigma ** 2 * (tm_f0(x) ** 2 - 1) - 2 * params_gamma * mbr_D(t, x))

  br89_f = lambda x, u, t: -br89_v(br89_mx(br89_cQ(br89_Q(x, u, t)))) / 2 * (1 + params_at * mgga_series_w(np.array([np.nan, 0, 1, 0, -2, 0, 1], dtype=np.float64), 6, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, br89_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t1 = r0 <= f.p.dens_threshold
  t2 = r0 + r1
  t3 = 0.1e1 / t2
  t6 = 0.2e1 * r0 * t3 <= f.p.zeta_threshold
  t7 = f.p.zeta_threshold - 0.1e1
  t10 = 0.2e1 * r1 * t3 <= f.p.zeta_threshold
  t11 = -t7
  t12 = r0 - r1
  t13 = t12 * t3
  t14 = f.my_piecewise5(t6, t7, t10, t11, t13)
  t15 = 0.1e1 + t14
  t16 = t15 <= f.p.zeta_threshold
  t17 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t18 = t17 * f.p.zeta_threshold
  t19 = t15 ** (0.1e1 / 0.3e1)
  t21 = f.my_piecewise3(t16, t18, t19 * t15)
  t22 = t2 ** (0.1e1 / 0.3e1)
  t25 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t27 = t21 * t22 * t26
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = params.lambda__ ** 2
  t32 = 0.6e1 * t29 - 0.6e1 * params.lambda__ + 0.3e1
  t33 = r0 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t36 = 0.1e1 / t34 / r0
  t38 = 0.2e1 * tau0 * t36
  t39 = 6 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = t40 * t43
  t45 = 0.3e1 / 0.5e1 * t44
  t46 = r0 ** 2
  t48 = 0.1e1 / t34 / t46
  t56 = (0.2e1 * params.lambda__ - 0.1e1) ** 2
  t57 = t56 * t39
  t58 = 0.1e1 / t43
  t59 = t58 * s0
  t63 = t56 ** 2
  t65 = params.beta * t63 * t40
  t67 = 0.1e1 / t42 / t41
  t68 = s0 ** 2
  t69 = t67 * t68
  t70 = t46 ** 2
  t73 = 0.1e1 / t33 / t70 / r0
  t78 = (0.1e1 + 0.175e3 / 0.162e3 * t57 * t59 * t48 + t65 * t69 * t73 / 0.576e3) ** (0.1e1 / 0.5e1)
  t82 = t56 * s0
  t88 = t32 * (t38 - t45 - s0 * t48 / 0.36e2) / 0.6e1 + t44 * (t78 - 0.1e1) / 0.5e1 - params.gamma * (t38 - t82 * t48 / 0.4e1) / 0.3e1
  t89 = abs(t88)
  t90 = t89 < 0.50e-12
  t91 = 0.0e0 < t88
  t92 = f.my_piecewise3(t91, 0.50e-12, -0.50e-12)
  t93 = f.my_piecewise3(t90, t92, t88)
  t94 = br89_x(t93)
  t96 = jnp.exp(t94 / 0.3e1)
  t97 = t28 * t96
  t98 = jnp.exp(-t94)
  t101 = t98 * (0.1e1 + t94 / 0.2e1)
  t102 = 0.1e1 - t101
  t103 = 0.1e1 / t94
  t104 = t102 * t103
  t105 = t97 * t104
  t108 = f.my_piecewise3(t1, 0, -t27 * t105 / 0.4e1)
  t109 = r1 <= f.p.dens_threshold
  t110 = f.my_piecewise5(t10, t7, t6, t11, -t13)
  t111 = 0.1e1 + t110
  t112 = t111 <= f.p.zeta_threshold
  t113 = t111 ** (0.1e1 / 0.3e1)
  t115 = f.my_piecewise3(t112, t18, t113 * t111)
  t117 = t115 * t22 * t26
  t118 = r1 ** (0.1e1 / 0.3e1)
  t119 = t118 ** 2
  t121 = 0.1e1 / t119 / r1
  t123 = 0.2e1 * tau1 * t121
  t124 = r1 ** 2
  t126 = 0.1e1 / t119 / t124
  t132 = t58 * s2
  t136 = s2 ** 2
  t137 = t67 * t136
  t138 = t124 ** 2
  t141 = 0.1e1 / t118 / t138 / r1
  t146 = (0.1e1 + 0.175e3 / 0.162e3 * t57 * t132 * t126 + t65 * t137 * t141 / 0.576e3) ** (0.1e1 / 0.5e1)
  t150 = t56 * s2
  t156 = t32 * (t123 - t45 - s2 * t126 / 0.36e2) / 0.6e1 + t44 * (t146 - 0.1e1) / 0.5e1 - params.gamma * (t123 - t150 * t126 / 0.4e1) / 0.3e1
  t157 = abs(t156)
  t158 = t157 < 0.50e-12
  t159 = 0.0e0 < t156
  t160 = f.my_piecewise3(t159, 0.50e-12, -0.50e-12)
  t161 = f.my_piecewise3(t158, t160, t156)
  t162 = br89_x(t161)
  t164 = jnp.exp(t162 / 0.3e1)
  t165 = t28 * t164
  t166 = jnp.exp(-t162)
  t169 = t166 * (0.1e1 + t162 / 0.2e1)
  t170 = 0.1e1 - t169
  t171 = 0.1e1 / t162
  t172 = t170 * t171
  t173 = t165 * t172
  t176 = f.my_piecewise3(t109, 0, -t117 * t173 / 0.4e1)
  t177 = t2 ** 2
  t179 = t12 / t177
  t180 = t3 - t179
  t181 = f.my_piecewise5(t6, 0, t10, 0, t180)
  t184 = f.my_piecewise3(t16, 0, 0.4e1 / 0.3e1 * t19 * t181)
  t189 = t22 ** 2
  t190 = 0.1e1 / t189
  t194 = t21 * t190 * t26 * t105 / 0.12e2
  t195 = jnp.pi ** (0.1e1 / 0.3e1)
  t196 = t195 ** 2
  t197 = t28 * t196
  t198 = f.my_piecewise3(t91, 0, 0)
  t200 = 0.10e2 / 0.3e1 * tau0 * t48
  t203 = 0.1e1 / t34 / t46 / r0
  t209 = t78 ** 2
  t210 = t209 ** 2
  t211 = 0.1e1 / t210
  t231 = f.my_piecewise3(t90, t198, t32 * (-t200 + 0.2e1 / 0.27e2 * s0 * t203) / 0.6e1 + t44 * t211 * (-0.700e3 / 0.243e3 * t57 * t59 * t203 - t65 * t69 / t33 / t70 / t46 / 0.108e3) / 0.25e2 - params.gamma * (-t200 + 0.2e1 / 0.3e1 * t82 * t203) / 0.3e1)
  t234 = t93 ** 2
  t235 = 0.1e1 / t234
  t237 = jnp.exp(-0.2e1 / 0.3e1 * t94)
  t238 = 0.1e1 / t237
  t239 = t235 * t238
  t240 = t94 ** 2
  t243 = 0.1e1 / (t240 - 0.2e1 * t94 + 0.3e1)
  t246 = (t94 - 0.2e1) ** 2
  t249 = t239 * t243 * t246 * t96 * t104
  t252 = t196 * t231
  t254 = t243 * t246
  t255 = t254 * t101
  t260 = t238 * t243 * t246 * t98
  t269 = t27 * t97 * t102
  t271 = 0.1e1 / t240 * t196
  t273 = t239 * t254
  t278 = f.my_piecewise3(t1, 0, -t184 * t22 * t26 * t105 / 0.4e1 - t194 - t27 * t197 * t231 * t249 / 0.12e2 - t27 * t97 * (t252 * t239 * t255 - t252 * t235 * t260 / 0.2e1) * t103 / 0.4e1 + t269 * t271 * t231 * t273 / 0.4e1)
  t280 = f.my_piecewise5(t10, 0, t6, 0, -t180)
  t283 = f.my_piecewise3(t112, 0, 0.4e1 / 0.3e1 * t113 * t280)
  t291 = t115 * t190 * t26 * t173 / 0.12e2
  t293 = f.my_piecewise3(t109, 0, -t283 * t22 * t26 * t173 / 0.4e1 - t291)
  vrho_0_ = t108 + t176 + t2 * (t278 + t293)
  t296 = -t3 - t179
  t297 = f.my_piecewise5(t6, 0, t10, 0, t296)
  t300 = f.my_piecewise3(t16, 0, 0.4e1 / 0.3e1 * t19 * t297)
  t306 = f.my_piecewise3(t1, 0, -t300 * t22 * t26 * t105 / 0.4e1 - t194)
  t308 = f.my_piecewise5(t10, 0, t6, 0, -t296)
  t311 = f.my_piecewise3(t112, 0, 0.4e1 / 0.3e1 * t113 * t308)
  t316 = f.my_piecewise3(t159, 0, 0)
  t318 = 0.10e2 / 0.3e1 * tau1 * t126
  t321 = 0.1e1 / t119 / t124 / r1
  t327 = t146 ** 2
  t328 = t327 ** 2
  t329 = 0.1e1 / t328
  t349 = f.my_piecewise3(t158, t316, t32 * (-t318 + 0.2e1 / 0.27e2 * s2 * t321) / 0.6e1 + t44 * t329 * (-0.700e3 / 0.243e3 * t57 * t132 * t321 - t65 * t137 / t118 / t138 / t124 / 0.108e3) / 0.25e2 - params.gamma * (-t318 + 0.2e1 / 0.3e1 * t150 * t321) / 0.3e1)
  t352 = t161 ** 2
  t353 = 0.1e1 / t352
  t355 = jnp.exp(-0.2e1 / 0.3e1 * t162)
  t356 = 0.1e1 / t355
  t357 = t353 * t356
  t358 = t162 ** 2
  t361 = 0.1e1 / (t358 - 0.2e1 * t162 + 0.3e1)
  t364 = (t162 - 0.2e1) ** 2
  t367 = t357 * t361 * t364 * t164 * t172
  t370 = t196 * t349
  t372 = t361 * t364
  t373 = t372 * t169
  t378 = t356 * t361 * t364 * t166
  t387 = t117 * t165 * t170
  t389 = 0.1e1 / t358 * t196
  t391 = t357 * t372
  t396 = f.my_piecewise3(t109, 0, -t311 * t22 * t26 * t173 / 0.4e1 - t291 - t117 * t197 * t349 * t367 / 0.12e2 - t117 * t165 * (t370 * t357 * t373 - t370 * t353 * t378 / 0.2e1) * t171 / 0.4e1 + t387 * t389 * t349 * t391 / 0.4e1)
  vrho_1_ = t108 + t176 + t2 * (t306 + t396)
  t412 = params.gamma * t56
  t416 = f.my_piecewise3(t90, t198, -t32 * t48 / 0.216e3 + t44 * t211 * (0.175e3 / 0.162e3 * t57 * t58 * t48 + t65 * t67 * s0 * t73 / 0.288e3) / 0.25e2 + t412 * t48 / 0.12e2)
  t421 = t196 * t416
  t437 = f.my_piecewise3(t1, 0, -t27 * t197 * t416 * t249 / 0.12e2 - t27 * t97 * (t421 * t239 * t255 - t421 * t235 * t260 / 0.2e1) * t103 / 0.4e1 + t269 * t271 * t416 * t273 / 0.4e1)
  vsigma_0_ = t2 * t437
  vsigma_1_ = 0.0e0
  t454 = f.my_piecewise3(t158, t316, -t32 * t126 / 0.216e3 + t44 * t329 * (0.175e3 / 0.162e3 * t57 * t58 * t126 + t65 * t67 * s2 * t141 / 0.288e3) / 0.25e2 + t412 * t126 / 0.12e2)
  t459 = t196 * t454
  t475 = f.my_piecewise3(t109, 0, -t117 * t197 * t454 * t367 / 0.12e2 - t117 * t165 * (t459 * t357 * t373 - t459 * t353 * t378 / 0.2e1) * t171 / 0.4e1 + t387 * t389 * t454 * t391 / 0.4e1)
  vsigma_2_ = t2 * t475
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t481 = f.my_piecewise3(t90, t198, t32 * t36 / 0.3e1 - 0.2e1 / 0.3e1 * params.gamma * t36)
  t486 = t196 * t481
  t502 = f.my_piecewise3(t1, 0, -t27 * t197 * t481 * t249 / 0.12e2 - t27 * t97 * (t486 * t239 * t255 - t486 * t235 * t260 / 0.2e1) * t103 / 0.4e1 + t269 * t271 * t481 * t273 / 0.4e1)
  vtau_0_ = t2 * t502
  t508 = f.my_piecewise3(t158, t316, t32 * t121 / 0.3e1 - 0.2e1 / 0.3e1 * params.gamma * t121)
  t513 = t196 * t508
  t529 = f.my_piecewise3(t109, 0, -t117 * t197 * t508 * t367 / 0.12e2 - t117 * t165 * (t513 * t357 * t373 - t513 * t353 * t378 / 0.2e1) * t171 / 0.4e1 + t387 * t389 * t508 * t391 / 0.4e1)
  vtau_1_ = t2 * t529
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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))
  params_lambda__raw = params.lambda__
  if isinstance(params_lambda__raw, (str, bytes, dict)):
    params_lambda_ = params_lambda__raw
  else:
    try:
      params_lambda__seq = list(params_lambda__raw)
    except TypeError:
      params_lambda_ = params_lambda__raw
    else:
      params_lambda__seq = np.asarray(params_lambda__seq, dtype=np.float64)
      params_lambda_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_lambda__seq))

  br89_min_Q = 5e-13

  br89_v = lambda x: -2 * jnp.pi ** (1 / 3) / X_FACTOR_C * jnp.exp(x / 3) * (1 - jnp.exp(-x) * (1 + x / 2)) / x

  br89_mx = lambda Q: br89_x(Q)

  params_at = 0

  tm_p = lambda x: (X2S * x) ** 2

  mbr_D = lambda ts, xs: 2 * ts - 1 / 4 * (2 * params_lambda_ - 1) ** 2 * xs ** 2

  k_sigma = (6 * jnp.pi ** 2) ** (1 / 3)

  tm_y = lambda x: (2 * params_lambda_ - 1) ** 2 * tm_p(x)

  tm_f0 = lambda x: (1 + 10 * (70 / 27) * tm_y(x) + params_beta * tm_y(x) ** 2) ** (1 / 10)

  br89_Q = lambda x, u, t: 1 / 6 * (+6 * (params_lambda_ ** 2 - params_lambda_ + 1 / 2) * (2 * t - 2 * K_FACTOR_C - 1 / 36 * x ** 2) + 6 / 5 * k_sigma ** 2 * (tm_f0(x) ** 2 - 1) - 2 * params_gamma * mbr_D(t, x))

  br89_f = lambda x, u, t: -br89_v(br89_mx(br89_cQ(br89_Q(x, u, t)))) / 2 * (1 + params_at * mgga_series_w(np.array([np.nan, 0, 1, 0, -2, 0, 1], dtype=np.float64), 6, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, br89_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = f.p.zeta_threshold - 0.1e1
  t6 = f.my_piecewise5(t3, t4, t3, -t4, 0)
  t7 = 0.1e1 + t6
  t9 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t11 = t7 ** (0.1e1 / 0.3e1)
  t13 = f.my_piecewise3(t7 <= f.p.zeta_threshold, t9 * f.p.zeta_threshold, t11 * t7)
  t14 = r0 ** (0.1e1 / 0.3e1)
  t17 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t18 = 0.1e1 / t17
  t19 = t13 * t14 * t18
  t20 = 4 ** (0.1e1 / 0.3e1)
  t21 = params.lambda__ ** 2
  t24 = 0.6e1 * t21 - 0.6e1 * params.lambda__ + 0.3e1
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = tau0 * t26
  t28 = t14 ** 2
  t30 = 0.1e1 / t28 / r0
  t32 = 0.2e1 * t27 * t30
  t33 = 6 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = jnp.pi ** 2
  t36 = t35 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = t34 * t37
  t40 = s0 * t26
  t41 = r0 ** 2
  t43 = 0.1e1 / t28 / t41
  t44 = t40 * t43
  t51 = (0.2e1 * params.lambda__ - 0.1e1) ** 2
  t52 = t51 * t33
  t53 = 0.1e1 / t37
  t54 = t52 * t53
  t57 = t51 ** 2
  t59 = params.beta * t57 * t34
  t61 = 0.1e1 / t36 / t35
  t62 = s0 ** 2
  t63 = t61 * t62
  t64 = t41 ** 2
  t68 = t25 / t14 / t64 / r0
  t73 = (0.1e1 + 0.175e3 / 0.162e3 * t54 * t44 + t59 * t63 * t68 / 0.288e3) ** (0.1e1 / 0.5e1)
  t77 = t51 * s0
  t78 = t26 * t43
  t84 = t24 * (t32 - 0.3e1 / 0.5e1 * t38 - t44 / 0.36e2) / 0.6e1 + t38 * (t73 - 0.1e1) / 0.5e1 - params.gamma * (t32 - t77 * t78 / 0.4e1) / 0.3e1
  t85 = abs(t84)
  t86 = t85 < 0.50e-12
  t87 = 0.0e0 < t84
  t88 = f.my_piecewise3(t87, 0.50e-12, -0.50e-12)
  t89 = f.my_piecewise3(t86, t88, t84)
  t90 = br89_x(t89)
  t92 = jnp.exp(t90 / 0.3e1)
  t93 = t20 * t92
  t94 = jnp.exp(-t90)
  t97 = t94 * (0.1e1 + t90 / 0.2e1)
  t98 = 0.1e1 - t97
  t99 = 0.1e1 / t90
  t100 = t98 * t99
  t101 = t93 * t100
  t104 = f.my_piecewise3(t2, 0, -t19 * t101 / 0.4e1)
  t110 = jnp.pi ** (0.1e1 / 0.3e1)
  t111 = t110 ** 2
  t112 = t20 * t111
  t113 = f.my_piecewise3(t87, 0, 0)
  t115 = 0.10e2 / 0.3e1 * t27 * t43
  t118 = 0.1e1 / t28 / t41 / r0
  t119 = t40 * t118
  t124 = t73 ** 2
  t125 = t124 ** 2
  t126 = 0.1e1 / t125
  t147 = f.my_piecewise3(t86, t113, t24 * (-t115 + 0.2e1 / 0.27e2 * t119) / 0.6e1 + t38 * t126 * (-0.700e3 / 0.243e3 * t54 * t119 - t59 * t63 * t25 / t14 / t64 / t41 / 0.54e2) / 0.25e2 - params.gamma * (-t115 + 0.2e1 / 0.3e1 * t77 * t26 * t118) / 0.3e1)
  t150 = t89 ** 2
  t151 = 0.1e1 / t150
  t153 = jnp.exp(-0.2e1 / 0.3e1 * t90)
  t154 = 0.1e1 / t153
  t155 = t151 * t154
  t156 = t90 ** 2
  t159 = 0.1e1 / (t156 - 0.2e1 * t90 + 0.3e1)
  t162 = (t90 - 0.2e1) ** 2
  t165 = t155 * t159 * t162 * t92 * t100
  t168 = t111 * t147
  t170 = t159 * t162
  t171 = t170 * t97
  t176 = t154 * t159 * t162 * t94
  t185 = t19 * t93 * t98
  t187 = 0.1e1 / t156 * t111
  t189 = t155 * t170
  t194 = f.my_piecewise3(t2, 0, -t13 / t28 * t18 * t101 / 0.12e2 - t19 * t112 * t147 * t165 / 0.12e2 - t19 * t93 * (t168 * t155 * t171 - t168 * t151 * t176 / 0.2e1) * t99 / 0.4e1 + t185 * t187 * t147 * t189 / 0.4e1)
  vrho_0_ = 0.2e1 * r0 * t194 + 0.2e1 * t104
  t197 = t24 * t26
  t216 = f.my_piecewise3(t86, t113, -t197 * t43 / 0.216e3 + t38 * t126 * (0.175e3 / 0.162e3 * t52 * t53 * t26 * t43 + t59 * t61 * s0 * t68 / 0.144e3) / 0.25e2 + params.gamma * t51 * t78 / 0.12e2)
  t221 = t111 * t216
  t237 = f.my_piecewise3(t2, 0, -t19 * t112 * t216 * t165 / 0.12e2 - t19 * t93 * (t221 * t155 * t171 - t221 * t151 * t176 / 0.2e1) * t99 / 0.4e1 + t185 * t187 * t216 * t189 / 0.4e1)
  vsigma_0_ = 0.2e1 * r0 * t237
  vlapl_0_ = 0.0e0
  t245 = f.my_piecewise3(t86, t113, t197 * t30 / 0.3e1 - 0.2e1 / 0.3e1 * params.gamma * t26 * t30)
  t250 = t111 * t245
  t266 = f.my_piecewise3(t2, 0, -t19 * t112 * t245 * t165 / 0.12e2 - t19 * t93 * (t250 * t155 * t171 - t250 * t151 * t176 / 0.2e1) * t99 / 0.4e1 + t185 * t187 * t245 * t189 / 0.4e1)
  vtau_0_ = 0.2e1 * r0 * t266
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
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = f.p.zeta_threshold - 0.1e1
  t6 = f.my_piecewise5(t3, t4, t3, -t4, 0)
  t7 = 0.1e1 + t6
  t9 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t11 = t7 ** (0.1e1 / 0.3e1)
  t13 = f.my_piecewise3(t7 <= f.p.zeta_threshold, t9 * f.p.zeta_threshold, t11 * t7)
  t14 = r0 ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t19 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t20 = 0.1e1 / t19
  t21 = t13 / t15 * t20
  t22 = 4 ** (0.1e1 / 0.3e1)
  t23 = params.lambda__ ** 2
  t24 = t23 - params.lambda__ + 0.1e1 / 0.2e1
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = tau0 * t26
  t29 = 0.1e1 / t15 / r0
  t31 = 0.2e1 * t27 * t29
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = t33 * t36
  t39 = s0 * t26
  t40 = r0 ** 2
  t42 = 0.1e1 / t15 / t40
  t43 = t39 * t42
  t49 = (0.2e1 * params.lambda__ - 0.1e1) ** 2
  t52 = t49 * t32 / t36
  t55 = t49 ** 2
  t57 = params.beta * t55 * t33
  t60 = s0 ** 2
  t61 = 0.1e1 / t35 / t34 * t60
  t62 = t40 ** 2
  t70 = 0.1e1 + 0.175e3 / 0.162e3 * t52 * t43 + t57 * t61 * t25 / t14 / t62 / r0 / 0.288e3
  t71 = t70 ** (0.1e1 / 0.5e1)
  t75 = t49 * s0
  t82 = t24 * (t31 - 0.3e1 / 0.5e1 * t37 - t43 / 0.36e2) + t37 * (t71 - 0.1e1) / 0.5e1 - params.gamma * (t31 - t75 * t26 * t42 / 0.4e1) / 0.3e1
  t83 = abs(t82)
  t84 = t83 < 0.50e-12
  t85 = 0.0e0 < t82
  t86 = f.my_piecewise3(t85, 0.50e-12, -0.50e-12)
  t87 = f.my_piecewise3(t84, t86, t82)
  t88 = br89_x(t87)
  t90 = jnp.exp(t88 / 0.3e1)
  t91 = t22 * t90
  t92 = jnp.exp(-t88)
  t95 = t92 * (0.1e1 + t88 / 0.2e1)
  t96 = 0.1e1 - t95
  t97 = 0.1e1 / t88
  t98 = t96 * t97
  t99 = t91 * t98
  t103 = t13 * t14 * t20
  t104 = jnp.pi ** (0.1e1 / 0.3e1)
  t105 = t104 ** 2
  t106 = t22 * t105
  t107 = f.my_piecewise3(t85, 0, 0)
  t109 = 0.10e2 / 0.3e1 * t27 * t42
  t110 = t40 * r0
  t112 = 0.1e1 / t15 / t110
  t113 = t39 * t112
  t117 = t71 ** 2
  t118 = t117 ** 2
  t119 = 0.1e1 / t118
  t129 = -0.700e3 / 0.243e3 * t52 * t113 - t57 * t61 * t25 / t14 / t62 / t40 / 0.54e2
  t140 = f.my_piecewise3(t84, t107, t24 * (-t109 + 0.2e1 / 0.27e2 * t113) + t37 * t119 * t129 / 0.25e2 - params.gamma * (-t109 + 0.2e1 / 0.3e1 * t75 * t26 * t112) / 0.3e1)
  t141 = t106 * t140
  t142 = t103 * t141
  t143 = t87 ** 2
  t144 = 0.1e1 / t143
  t146 = jnp.exp(-0.2e1 / 0.3e1 * t88)
  t147 = 0.1e1 / t146
  t148 = t144 * t147
  t149 = t88 ** 2
  t151 = t149 - 0.2e1 * t88 + 0.3e1
  t152 = 0.1e1 / t151
  t153 = t148 * t152
  t154 = t88 - 0.2e1
  t155 = t154 ** 2
  t156 = t155 * t90
  t157 = t156 * t98
  t158 = t153 * t157
  t161 = t105 * t140
  t162 = t161 * t148
  t163 = t152 * t155
  t164 = t163 * t95
  t166 = t161 * t144
  t167 = t147 * t152
  t169 = t167 * t155 * t92
  t172 = t162 * t164 - t166 * t169 / 0.2e1
  t173 = t172 * t97
  t174 = t91 * t173
  t177 = t91 * t96
  t178 = t103 * t177
  t179 = 0.1e1 / t149
  t180 = t179 * t105
  t182 = t148 * t163
  t183 = t180 * t140 * t182
  t187 = f.my_piecewise3(t2, 0, -t21 * t99 / 0.12e2 - t142 * t158 / 0.12e2 - t103 * t174 / 0.4e1 + t178 * t183 / 0.4e1)
  t202 = 0.80e2 / 0.9e1 * t27 * t112
  t204 = 0.1e1 / t15 / t62
  t205 = t39 * t204
  t211 = t129 ** 2
  t235 = f.my_piecewise3(t84, t107, t24 * (t202 - 0.22e2 / 0.81e2 * t205) - 0.4e1 / 0.125e3 * t37 / t118 / t70 * t211 + t37 * t119 * (0.7700e4 / 0.729e3 * t52 * t205 + 0.19e2 / 0.162e3 * t57 * t61 * t25 / t14 / t62 / t110) / 0.25e2 - params.gamma * (t202 - 0.22e2 / 0.9e1 * t75 * t26 * t204) / 0.3e1)
  t240 = t140 ** 2
  t244 = 0.1e1 / t143 / t87
  t245 = t244 * t147
  t250 = t104 * jnp.pi
  t253 = t103 * t22 * t250 * t240
  t254 = t143 ** 2
  t255 = 0.1e1 / t254
  t256 = t146 ** 2
  t257 = 0.1e1 / t256
  t258 = t255 * t257
  t259 = t151 ** 2
  t260 = 0.1e1 / t259
  t261 = t258 * t260
  t262 = t155 ** 2
  t263 = t262 * t90
  t271 = t147 * t260
  t280 = 0.2e1 * t88 * t105 * t140 * t182 - 0.2e1 * t166 * t167 * t155
  t286 = t155 * t154
  t296 = t96 * t179
  t301 = t105 * t235
  t304 = t105 * t240
  t308 = t250 * t240
  t309 = t308 * t258
  t310 = t260 * t262
  t314 = t260 * t155
  t318 = t260 * t286
  t322 = t308 * t255
  t323 = t257 * t260
  t379 = t13 * t29 * t20 * t99 / 0.18e2 - t21 * t141 * t158 / 0.18e2 - t21 * t174 / 0.6e1 + t21 * t177 * t183 / 0.6e1 - t103 * t106 * t235 * t158 / 0.12e2 + t103 * t106 * t240 * t245 * t152 * t157 / 0.6e1 - t253 * t261 * t263 * t98 / 0.12e2 + t103 * t106 * t140 * t144 * t271 * t155 * t90 * t96 * t97 * t280 / 0.12e2 - t253 * t261 * t286 * t90 * t98 / 0.6e1 - t142 * t153 * t156 * t173 / 0.6e1 + t253 * t261 * t263 * t296 / 0.3e1 - t103 * t91 * (t301 * t148 * t164 - 0.2e1 * t304 * t245 * t164 - t309 * t310 * t95 / 0.3e1 - t162 * t314 * t95 * t280 + 0.2e1 * t309 * t318 * t95 + 0.2e1 / 0.3e1 * t322 * t323 * t262 * t92 - t301 * t144 * t169 / 0.2e1 + t304 * t244 * t169 + t162 * t314 * t92 * t280 / 0.2e1 - t322 * t323 * t286 * t92) * t97 / 0.4e1 + t103 * t91 * t172 * t183 / 0.2e1 - t178 / t149 / t88 * t250 * t240 * t258 * t310 / 0.2e1 + t178 * t180 * t235 * t182 / 0.4e1 - t178 * t180 * t240 * t245 * t163 / 0.2e1 - t103 * t91 * t296 * t166 * t271 * t155 * t280 / 0.4e1 + t178 * t179 * t250 * t240 * t258 * t318 / 0.2e1
  t380 = f.my_piecewise3(t2, 0, t379)
  v2rho2_0_ = 0.2e1 * r0 * t380 + 0.4e1 * t187
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = f.p.zeta_threshold - 0.1e1
  t6 = f.my_piecewise5(t3, t4, t3, -t4, 0)
  t7 = 0.1e1 + t6
  t9 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t11 = t7 ** (0.1e1 / 0.3e1)
  t13 = f.my_piecewise3(t7 <= f.p.zeta_threshold, t9 * f.p.zeta_threshold, t11 * t7)
  t14 = r0 ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = 0.1e1 / t15 / r0
  t20 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t21 = 0.1e1 / t20
  t22 = t13 * t17 * t21
  t23 = 4 ** (0.1e1 / 0.3e1)
  t24 = params.lambda__ ** 2
  t25 = t24 - params.lambda__ + 0.1e1 / 0.2e1
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = tau0 * t27
  t30 = 0.2e1 * t28 * t17
  t31 = 6 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = t32 * t35
  t38 = s0 * t27
  t39 = r0 ** 2
  t41 = 0.1e1 / t15 / t39
  t42 = t38 * t41
  t48 = (0.2e1 * params.lambda__ - 0.1e1) ** 2
  t51 = t48 * t31 / t35
  t54 = t48 ** 2
  t56 = params.beta * t54 * t32
  t59 = s0 ** 2
  t60 = 0.1e1 / t34 / t33 * t59
  t61 = t39 ** 2
  t62 = t61 * r0
  t69 = 0.1e1 + 0.175e3 / 0.162e3 * t51 * t42 + t56 * t60 * t26 / t14 / t62 / 0.288e3
  t70 = t69 ** (0.1e1 / 0.5e1)
  t74 = t48 * s0
  t81 = t25 * (t30 - 0.3e1 / 0.5e1 * t36 - t42 / 0.36e2) + t36 * (t70 - 0.1e1) / 0.5e1 - params.gamma * (t30 - t74 * t27 * t41 / 0.4e1) / 0.3e1
  t82 = abs(t81)
  t83 = t82 < 0.50e-12
  t84 = 0.0e0 < t81
  t85 = f.my_piecewise3(t84, 0.50e-12, -0.50e-12)
  t86 = f.my_piecewise3(t83, t85, t81)
  t87 = br89_x(t86)
  t89 = jnp.exp(t87 / 0.3e1)
  t90 = t23 * t89
  t91 = jnp.exp(-t87)
  t94 = t91 * (0.1e1 + t87 / 0.2e1)
  t95 = 0.1e1 - t94
  t96 = 0.1e1 / t87
  t97 = t95 * t96
  t98 = t90 * t97
  t103 = t13 / t15 * t21
  t104 = jnp.pi ** (0.1e1 / 0.3e1)
  t105 = t104 ** 2
  t106 = t23 * t105
  t107 = f.my_piecewise3(t84, 0, 0)
  t109 = 0.10e2 / 0.3e1 * t28 * t41
  t110 = t39 * r0
  t112 = 0.1e1 / t15 / t110
  t113 = t38 * t112
  t117 = t70 ** 2
  t118 = t117 ** 2
  t119 = 0.1e1 / t118
  t129 = -0.700e3 / 0.243e3 * t51 * t113 - t56 * t60 * t26 / t14 / t61 / t39 / 0.54e2
  t140 = f.my_piecewise3(t83, t107, t25 * (-t109 + 0.2e1 / 0.27e2 * t113) + t36 * t119 * t129 / 0.25e2 - params.gamma * (-t109 + 0.2e1 / 0.3e1 * t74 * t27 * t112) / 0.3e1)
  t141 = t106 * t140
  t142 = t103 * t141
  t143 = t86 ** 2
  t144 = 0.1e1 / t143
  t146 = jnp.exp(-0.2e1 / 0.3e1 * t87)
  t147 = 0.1e1 / t146
  t148 = t144 * t147
  t149 = t87 ** 2
  t151 = t149 - 0.2e1 * t87 + 0.3e1
  t152 = 0.1e1 / t151
  t153 = t148 * t152
  t154 = t87 - 0.2e1
  t155 = t154 ** 2
  t156 = t155 * t89
  t157 = t156 * t97
  t158 = t153 * t157
  t161 = t105 * t140
  t162 = t161 * t148
  t163 = t152 * t155
  t164 = t163 * t94
  t166 = t161 * t144
  t167 = t147 * t152
  t169 = t167 * t155 * t91
  t172 = t162 * t164 - t166 * t169 / 0.2e1
  t173 = t172 * t96
  t174 = t90 * t173
  t177 = t90 * t95
  t178 = t103 * t177
  t179 = 0.1e1 / t149
  t180 = t179 * t105
  t182 = t148 * t163
  t183 = t180 * t140 * t182
  t187 = t13 * t14 * t21
  t189 = 0.80e2 / 0.9e1 * t28 * t112
  t191 = 0.1e1 / t15 / t61
  t192 = t38 * t191
  t197 = 0.1e1 / t118 / t69
  t198 = t129 ** 2
  t211 = 0.7700e4 / 0.729e3 * t51 * t192 + 0.19e2 / 0.162e3 * t56 * t60 * t26 / t14 / t61 / t110
  t222 = f.my_piecewise3(t83, t107, t25 * (t189 - 0.22e2 / 0.81e2 * t192) - 0.4e1 / 0.125e3 * t36 * t197 * t198 + t36 * t119 * t211 / 0.25e2 - params.gamma * (t189 - 0.22e2 / 0.9e1 * t74 * t27 * t191) / 0.3e1)
  t223 = t106 * t222
  t224 = t187 * t223
  t227 = t140 ** 2
  t228 = t106 * t227
  t229 = t187 * t228
  t231 = 0.1e1 / t143 / t86
  t232 = t231 * t147
  t233 = t232 * t152
  t234 = t233 * t157
  t237 = t104 * jnp.pi
  t238 = t23 * t237
  t239 = t238 * t227
  t240 = t187 * t239
  t241 = t143 ** 2
  t242 = 0.1e1 / t241
  t243 = t146 ** 2
  t244 = 0.1e1 / t243
  t245 = t242 * t244
  t246 = t151 ** 2
  t247 = 0.1e1 / t246
  t248 = t245 * t247
  t249 = t155 ** 2
  t250 = t249 * t89
  t251 = t250 * t97
  t252 = t248 * t251
  t255 = t140 * t144
  t256 = t106 * t255
  t257 = t187 * t256
  t258 = t147 * t247
  t259 = t258 * t155
  t260 = t89 * t95
  t261 = t87 * t105
  t264 = t167 * t155
  t267 = 0.2e1 * t261 * t140 * t182 - 0.2e1 * t166 * t264
  t268 = t96 * t267
  t269 = t260 * t268
  t270 = t259 * t269
  t273 = t155 * t154
  t274 = t273 * t89
  t275 = t274 * t97
  t276 = t248 * t275
  t279 = t187 * t141
  t280 = t156 * t173
  t281 = t153 * t280
  t284 = t95 * t179
  t285 = t250 * t284
  t286 = t248 * t285
  t289 = t105 * t222
  t290 = t289 * t148
  t292 = t105 * t227
  t293 = t292 * t232
  t296 = t237 * t227
  t297 = t296 * t245
  t298 = t247 * t249
  t299 = t298 * t94
  t302 = t247 * t155
  t303 = t94 * t267
  t304 = t302 * t303
  t306 = t247 * t273
  t307 = t306 * t94
  t310 = t296 * t242
  t311 = t244 * t247
  t312 = t249 * t91
  t313 = t311 * t312
  t316 = t289 * t144
  t319 = t292 * t231
  t321 = t91 * t267
  t322 = t302 * t321
  t326 = t311 * t273 * t91
  t328 = t290 * t164 - 0.2e1 * t293 * t164 - t297 * t299 / 0.3e1 - t162 * t304 + 0.2e1 * t297 * t307 + 0.2e1 / 0.3e1 * t310 * t313 - t316 * t169 / 0.2e1 + t319 * t169 + t162 * t322 / 0.2e1 - t310 * t326
  t329 = t328 * t96
  t330 = t90 * t329
  t333 = t90 * t172
  t334 = t187 * t333
  t337 = t187 * t177
  t339 = 0.1e1 / t149 / t87
  t340 = t339 * t237
  t342 = t245 * t298
  t343 = t340 * t227 * t342
  t347 = t180 * t222 * t182
  t351 = t232 * t163
  t352 = t180 * t227 * t351
  t355 = t90 * t284
  t356 = t187 * t355
  t358 = t258 * t155 * t267
  t359 = t166 * t358
  t362 = t179 * t237
  t364 = t245 * t306
  t365 = t362 * t227 * t364
  t368 = t22 * t98 / 0.18e2 - t142 * t158 / 0.18e2 - t103 * t174 / 0.6e1 + t178 * t183 / 0.6e1 - t224 * t158 / 0.12e2 + t229 * t234 / 0.6e1 - t240 * t252 / 0.12e2 + t257 * t270 / 0.12e2 - t240 * t276 / 0.6e1 - t279 * t281 / 0.6e1 + t240 * t286 / 0.3e1 - t187 * t330 / 0.4e1 + t334 * t183 / 0.2e1 - t337 * t343 / 0.2e1 + t337 * t347 / 0.4e1 - t337 * t352 / 0.2e1 - t356 * t359 / 0.4e1 + t337 * t365 / 0.2e1
  t369 = f.my_piecewise3(t2, 0, t368)
  t382 = t227 * t140
  t385 = t242 * t147
  t392 = t149 ** 2
  t397 = 0.1e1 / t241 / t143
  t399 = 0.1e1 / t243 / t146
  t400 = t397 * t399
  t402 = 0.1e1 / t246 / t151
  t403 = t249 * t155
  t404 = t402 * t403
  t411 = t249 * t154
  t412 = t402 * t411
  t420 = t187 * t238 * t382
  t422 = 0.1e1 / t241 / t86
  t423 = t422 * t244
  t424 = t423 * t247
  t432 = t187 * t23 * t33 * t382
  t433 = t400 * t402
  t434 = t411 * t89
  t439 = t403 * t89
  t451 = t103 * t239
  t456 = -t103 * t330 / 0.4e1 + t22 * t174 / 0.6e1 - 0.5e1 / 0.54e2 * t13 * t41 * t21 * t98 + t229 * t233 * t280 / 0.2e1 - t187 * t106 * t382 * t385 * t152 * t157 / 0.2e1 + 0.3e1 / 0.2e1 * t334 * t365 + 0.3e1 / 0.2e1 * t337 / t392 * t33 * t382 * t400 * t404 - 0.3e1 * t337 * t339 * t33 * t382 * t400 * t412 + 0.3e1 / 0.4e1 * t334 * t347 + t420 * t424 * t275 - 0.2e1 * t420 * t424 * t285 - 0.11e2 / 0.18e2 * t432 * t433 * t434 * t97 + 0.23e2 / 0.36e2 * t432 * t433 * t439 * t284 - t432 * t433 * t251 / 0.2e1 + 0.7e1 / 0.3e1 * t432 * t433 * t434 * t284 - t451 * t276 / 0.6e1 + t451 * t286 / 0.3e1
  t479 = 0.880e3 / 0.27e2 * t28 * t191
  t481 = 0.1e1 / t15 / t62
  t482 = t38 * t481
  t486 = t69 ** 2
  t499 = t61 ** 2
  t517 = f.my_piecewise3(t83, t107, t25 * (-t479 + 0.308e3 / 0.243e3 * t482) + 0.36e2 / 0.625e3 * t36 / t118 / t486 * t198 * t129 - 0.12e2 / 0.125e3 * t36 * t197 * t129 * t211 + t36 * t119 * (-0.107800e6 / 0.2187e4 * t51 * t482 - 0.209e3 / 0.243e3 * t56 * t60 * t26 / t14 / t499) / 0.25e2 - params.gamma * (-t479 + 0.308e3 / 0.27e2 * t74 * t27 * t481) / 0.3e1)
  t552 = -t178 * t343 / 0.2e1 + t178 * t365 / 0.2e1 - 0.3e1 / 0.2e1 * t334 * t352 + 0.3e1 * t337 * t340 * t382 * t423 * t298 + 0.3e1 / 0.2e1 * t337 * t180 * t382 * t385 * t163 + t103 * t228 * t234 / 0.6e1 - t178 * t352 / 0.2e1 - t187 * t106 * t517 * t158 / 0.12e2 - t224 * t281 / 0.4e1 - t279 * t153 * t156 * t329 / 0.4e1 + t420 * t424 * t251 / 0.2e1 - t240 * t248 * t250 * t173 / 0.4e1 - 0.5e1 / 0.36e2 * t432 * t433 * t439 * t97 + t22 * t141 * t158 / 0.18e2 - t22 * t177 * t183 / 0.6e1 - t103 * t223 * t158 / 0.12e2 - t142 * t281 / 0.6e1 - t451 * t252 / 0.12e2
  t566 = t402 * t249
  t571 = t172 * t179
  t575 = t95 * t339
  t594 = t105 * t382
  t598 = t237 * t382
  t599 = t598 * t422
  t602 = t33 * t382
  t603 = t602 * t397
  t604 = t399 * t402
  t611 = t105 * t517
  t622 = t602 * t400
  t626 = t237 * t222
  t627 = t626 * t245
  t628 = t91 * t140
  t632 = t289 * t232
  t639 = t598 * t423
  t650 = -0.3e1 * t594 * t242 * t169 + 0.6e1 * t599 * t326 + t603 * t604 * t403 * t91 / 0.18e2 - 0.4e1 * t599 * t313 - t611 * t144 * t169 / 0.2e1 + 0.10e2 / 0.3e1 * t603 * t604 * t411 * t91 - 0.3e1 * t603 * t604 * t312 + 0.6e1 * t622 * t566 * t94 - 0.3e1 * t627 * t306 * t628 + 0.3e1 * t632 * t163 * t628 + t290 * t322 - 0.2e1 * t293 * t322 + 0.2e1 * t639 * t299 - t622 * t404 * t94 / 0.9e1 - 0.2e1 * t297 * t566 * t321 + t611 * t148 * t164
  t654 = t311 * t249
  t664 = t87 * t237 * t227
  t677 = t311 * t273
  t680 = 0.2e1 / 0.3e1 * t310 * t654 + 0.2e1 * t261 * t222 * t182 - 0.4e1 * t261 * t227 * t351 + 0.4e1 / 0.3e1 * t664 * t342 - 0.2e1 * t261 * t255 * t358 + 0.4e1 * t664 * t364 - 0.2e1 * t316 * t264 + 0.4e1 * t319 * t264 + 0.2e1 * t359 - 0.4e1 * t310 * t677
  t685 = t402 * t155
  t686 = t267 ** 2
  t693 = t402 * t273
  t705 = t94 * t140
  t727 = 0.2e1 * t627 * t298 * t628 + t162 * t302 * t91 * t680 / 0.2e1 - t162 * t685 * t91 * t686 + 0.6e1 * t594 * t385 * t164 + 0.3e1 * t297 * t693 * t321 - 0.12e2 * t639 * t307 - 0.2e1 / 0.3e1 * t622 * t412 * t94 - t162 * t302 * t94 * t680 - 0.6e1 * t632 * t163 * t705 - 0.2e1 * t290 * t304 - t627 * t298 * t705 + 0.4e1 * t293 * t304 + t297 * t566 * t303 + 0.2e1 * t162 * t685 * t94 * t686 + 0.6e1 * t627 * t306 * t705 - 0.6e1 * t297 * t693 * t303
  t740 = t187 * t238 * t227 * t242
  t741 = t244 * t402
  t742 = t741 * t249
  t756 = t187 * t90 * t575
  t769 = t103 * t333 * t183 / 0.2e1 + t178 * t347 / 0.4e1 - 0.3e1 * t337 * t362 * t382 * t423 * t306 + 0.3e1 / 0.2e1 * t337 * t179 * t33 * t382 * t400 * t566 + t240 * t248 * t250 * t571 - 0.3e1 / 0.2e1 * t432 * t433 * t439 * t575 - 0.3e1 / 0.2e1 * t334 * t343 + t337 * t180 * t517 * t182 / 0.4e1 + 0.3e1 / 0.4e1 * t187 * t90 * t328 * t183 - t240 * t248 * t274 * t173 / 0.2e1 - t187 * t90 * (t650 + t727) * t96 / 0.4e1 + t257 * t259 * t260 * t96 * t680 / 0.12e2 - t740 * t742 * t260 * t179 * t267 + t740 * t741 * t273 * t269 / 0.2e1 - 0.3e1 / 0.4e1 * t187 * t90 * t571 * t359 - 0.3e1 / 0.2e1 * t756 * t237 * t140 * t242 * t311 * t249 * t222 + 0.3e1 / 0.2e1 * t756 * t310 * t741 * t249 * t267
  t796 = t260 * t96 * t140
  t807 = t187 * t238 * t222 * t242
  t829 = t147 * t402
  t854 = -0.3e1 / 0.2e1 * t356 * t289 * t231 * t167 * t155 * t140 - t356 * t316 * t358 / 0.2e1 + t356 * t319 * t358 - t356 * t166 * t258 * t155 * t680 / 0.4e1 + t103 * t256 * t270 / 0.12e2 - t103 * t355 * t359 / 0.4e1 + t187 * t106 * t222 * t231 * t264 * t796 / 0.2e1 + t187 * t106 * t222 * t144 * t270 / 0.6e1 - t807 * t654 * t796 / 0.4e1 - t187 * t106 * t227 * t231 * t270 / 0.3e1 + t740 * t742 * t269 / 0.4e1 + t257 * t259 * t89 * t172 * t268 / 0.4e1 - 0.3e1 / 0.2e1 * t356 * t310 * t741 * t273 * t267 + t356 * t166 * t829 * t155 * t686 / 0.2e1 - t257 * t829 * t155 * t260 * t96 * t686 / 0.6e1 + 0.3e1 / 0.2e1 * t356 * t626 * t242 * t311 * t273 * t140 - t807 * t677 * t796 / 0.2e1 + t807 * t654 * t260 * t179 * t140
  t857 = f.my_piecewise3(t2, 0, t456 + t552 + t769 + t854)
  v3rho3_0_ = 0.2e1 * r0 * t857 + 0.6e1 * t369

  res = {'v3rho3': v3rho3_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = r0 + r1
  t3 = 0.1e1 / t2
  t6 = 0.2e1 * r0 * t3 <= f.p.zeta_threshold
  t7 = f.p.zeta_threshold - 0.1e1
  t10 = 0.2e1 * r1 * t3 <= f.p.zeta_threshold
  t11 = -t7
  t12 = r0 - r1
  t13 = t12 * t3
  t14 = f.my_piecewise5(t6, t7, t10, t11, t13)
  t15 = 0.1e1 + t14
  t16 = t15 <= f.p.zeta_threshold
  t17 = t15 ** (0.1e1 / 0.3e1)
  t18 = t2 ** 2
  t19 = 0.1e1 / t18
  t20 = t12 * t19
  t21 = t3 - t20
  t22 = f.my_piecewise5(t6, 0, t10, 0, t21)
  t25 = f.my_piecewise3(t16, 0, 0.4e1 / 0.3e1 * t17 * t22)
  t26 = t2 ** (0.1e1 / 0.3e1)
  t29 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / t29
  t31 = t25 * t26 * t30
  t32 = 4 ** (0.1e1 / 0.3e1)
  t33 = params.lambda__ ** 2
  t34 = t33 - params.lambda__ + 0.1e1 / 0.2e1
  t35 = r0 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t40 = 0.2e1 * tau0 / t36 / r0
  t41 = 6 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t43 = jnp.pi ** 2
  t44 = t43 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = t42 * t45
  t47 = 0.3e1 / 0.5e1 * t46
  t48 = r0 ** 2
  t50 = 0.1e1 / t36 / t48
  t57 = (0.2e1 * params.lambda__ - 0.1e1) ** 2
  t58 = t57 * t41
  t59 = 0.1e1 / t45
  t60 = t59 * s0
  t64 = t57 ** 2
  t66 = params.beta * t64 * t42
  t68 = 0.1e1 / t44 / t43
  t69 = s0 ** 2
  t70 = t68 * t69
  t71 = t48 ** 2
  t78 = 0.1e1 + 0.175e3 / 0.162e3 * t58 * t60 * t50 + t66 * t70 / t35 / t71 / r0 / 0.576e3
  t79 = t78 ** (0.1e1 / 0.5e1)
  t83 = t57 * s0
  t89 = t34 * (t40 - t47 - s0 * t50 / 0.36e2) + t46 * (t79 - 0.1e1) / 0.5e1 - params.gamma * (t40 - t83 * t50 / 0.4e1) / 0.3e1
  t90 = abs(t89)
  t91 = t90 < 0.50e-12
  t92 = 0.0e0 < t89
  t93 = f.my_piecewise3(t92, 0.50e-12, -0.50e-12)
  t94 = f.my_piecewise3(t91, t93, t89)
  t95 = br89_x(t94)
  t97 = jnp.exp(t95 / 0.3e1)
  t98 = t32 * t97
  t99 = jnp.exp(-t95)
  t102 = t99 * (0.1e1 + t95 / 0.2e1)
  t103 = 0.1e1 - t102
  t104 = 0.1e1 / t95
  t105 = t103 * t104
  t106 = t98 * t105
  t109 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t110 = t109 * f.p.zeta_threshold
  t112 = f.my_piecewise3(t16, t110, t17 * t15)
  t113 = t26 ** 2
  t114 = 0.1e1 / t113
  t116 = t112 * t114 * t30
  t118 = t116 * t106 / 0.12e2
  t120 = t112 * t26 * t30
  t121 = jnp.pi ** (0.1e1 / 0.3e1)
  t122 = t121 ** 2
  t123 = t32 * t122
  t124 = f.my_piecewise3(t92, 0, 0)
  t126 = 0.10e2 / 0.3e1 * tau0 * t50
  t127 = t48 * r0
  t129 = 0.1e1 / t36 / t127
  t134 = t79 ** 2
  t135 = t134 ** 2
  t136 = 0.1e1 / t135
  t146 = -0.700e3 / 0.243e3 * t58 * t60 * t129 - t66 * t70 / t35 / t71 / t48 / 0.108e3
  t156 = f.my_piecewise3(t91, t124, t34 * (-t126 + 0.2e1 / 0.27e2 * s0 * t129) + t46 * t136 * t146 / 0.25e2 - params.gamma * (-t126 + 0.2e1 / 0.3e1 * t83 * t129) / 0.3e1)
  t157 = t123 * t156
  t158 = t120 * t157
  t159 = t94 ** 2
  t160 = 0.1e1 / t159
  t162 = jnp.exp(-0.2e1 / 0.3e1 * t95)
  t163 = 0.1e1 / t162
  t164 = t160 * t163
  t165 = t95 ** 2
  t167 = t165 - 0.2e1 * t95 + 0.3e1
  t168 = 0.1e1 / t167
  t169 = t164 * t168
  t170 = t95 - 0.2e1
  t171 = t170 ** 2
  t172 = t171 * t97
  t173 = t172 * t105
  t174 = t169 * t173
  t177 = t122 * t156
  t178 = t177 * t164
  t179 = t168 * t171
  t180 = t179 * t102
  t182 = t177 * t160
  t183 = t163 * t168
  t185 = t183 * t171 * t99
  t188 = t178 * t180 - t182 * t185 / 0.2e1
  t189 = t188 * t104
  t190 = t98 * t189
  t193 = t98 * t103
  t194 = t120 * t193
  t195 = 0.1e1 / t165
  t196 = t195 * t122
  t198 = t164 * t179
  t199 = t196 * t156 * t198
  t203 = f.my_piecewise3(t1, 0, -t31 * t106 / 0.4e1 - t118 - t158 * t174 / 0.12e2 - t120 * t190 / 0.4e1 + t194 * t199 / 0.4e1)
  t205 = r1 <= f.p.dens_threshold
  t206 = f.my_piecewise5(t10, t7, t6, t11, -t13)
  t207 = 0.1e1 + t206
  t208 = t207 <= f.p.zeta_threshold
  t209 = t207 ** (0.1e1 / 0.3e1)
  t211 = f.my_piecewise5(t10, 0, t6, 0, -t21)
  t214 = f.my_piecewise3(t208, 0, 0.4e1 / 0.3e1 * t209 * t211)
  t216 = t214 * t26 * t30
  t217 = r1 ** (0.1e1 / 0.3e1)
  t218 = t217 ** 2
  t222 = 0.2e1 * tau1 / t218 / r1
  t223 = r1 ** 2
  t225 = 0.1e1 / t218 / t223
  t230 = t59 * s2
  t234 = s2 ** 2
  t235 = t68 * t234
  t236 = t223 ** 2
  t243 = 0.1e1 + 0.175e3 / 0.162e3 * t58 * t230 * t225 + t66 * t235 / t217 / t236 / r1 / 0.576e3
  t244 = t243 ** (0.1e1 / 0.5e1)
  t248 = t57 * s2
  t254 = t34 * (t222 - t47 - s2 * t225 / 0.36e2) + t46 * (t244 - 0.1e1) / 0.5e1 - params.gamma * (t222 - t248 * t225 / 0.4e1) / 0.3e1
  t255 = abs(t254)
  t256 = t255 < 0.50e-12
  t257 = 0.0e0 < t254
  t258 = f.my_piecewise3(t257, 0.50e-12, -0.50e-12)
  t259 = f.my_piecewise3(t256, t258, t254)
  t260 = br89_x(t259)
  t262 = jnp.exp(t260 / 0.3e1)
  t263 = t32 * t262
  t264 = jnp.exp(-t260)
  t267 = t264 * (0.1e1 + t260 / 0.2e1)
  t268 = 0.1e1 - t267
  t269 = 0.1e1 / t260
  t270 = t268 * t269
  t271 = t263 * t270
  t275 = f.my_piecewise3(t208, t110, t209 * t207)
  t277 = t275 * t114 * t30
  t279 = t277 * t271 / 0.12e2
  t281 = f.my_piecewise3(t205, 0, -t216 * t271 / 0.4e1 - t279)
  t287 = t121 * jnp.pi
  t288 = t32 * t287
  t289 = t156 ** 2
  t291 = t120 * t288 * t289
  t292 = t159 ** 2
  t293 = 0.1e1 / t292
  t294 = t162 ** 2
  t295 = 0.1e1 / t294
  t296 = t293 * t295
  t297 = t167 ** 2
  t298 = 0.1e1 / t297
  t299 = t296 * t298
  t300 = t171 ** 2
  t301 = t300 * t97
  t311 = 0.80e2 / 0.9e1 * tau0 * t129
  t313 = 0.1e1 / t36 / t71
  t320 = t146 ** 2
  t343 = f.my_piecewise3(t91, t124, t34 * (t311 - 0.22e2 / 0.81e2 * s0 * t313) - 0.4e1 / 0.125e3 * t46 / t135 / t78 * t320 + t46 * t136 * (0.7700e4 / 0.729e3 * t58 * t60 * t313 + 0.19e2 / 0.324e3 * t66 * t70 / t35 / t71 / t127) / 0.25e2 - params.gamma * (t311 - 0.22e2 / 0.9e1 * t83 * t313) / 0.3e1)
  t350 = t25 * t114 * t30 * t106
  t353 = 0.1e1 / t113 / t2
  t357 = t112 * t353 * t30 * t106 / 0.18e2
  t358 = t122 * t343
  t361 = t122 * t289
  t363 = 0.1e1 / t159 / t94
  t364 = t363 * t163
  t368 = t287 * t289
  t369 = t368 * t296
  t370 = t298 * t300
  t374 = t298 * t171
  t381 = 0.2e1 * t95 * t122 * t156 * t198 - 0.2e1 * t182 * t183 * t171
  t385 = t171 * t170
  t386 = t298 * t385
  t390 = t368 * t293
  t391 = t295 * t298
  t413 = t17 ** 2
  t414 = 0.1e1 / t413
  t415 = t22 ** 2
  t420 = t12 / t18 / t2
  t422 = -0.2e1 * t19 + 0.2e1 * t420
  t423 = f.my_piecewise5(t6, 0, t10, 0, t422)
  t427 = f.my_piecewise3(t16, 0, 0.4e1 / 0.9e1 * t414 * t415 + 0.4e1 / 0.3e1 * t17 * t423)
  t434 = t116 * t190
  t439 = -t158 * t169 * t172 * t189 / 0.6e1 - t291 * t299 * t301 * t105 / 0.12e2 + t120 * t98 * t188 * t199 / 0.2e1 + t194 * t196 * t343 * t198 / 0.4e1 - t350 / 0.6e1 + t357 - t120 * t98 * (t358 * t164 * t180 - 0.2e1 * t361 * t364 * t180 - t369 * t370 * t102 / 0.3e1 - t178 * t374 * t102 * t381 + 0.2e1 * t369 * t386 * t102 + 0.2e1 / 0.3e1 * t390 * t391 * t300 * t99 - t358 * t160 * t185 / 0.2e1 + t361 * t363 * t185 + t178 * t374 * t99 * t381 / 0.2e1 - t390 * t391 * t385 * t99) * t104 / 0.4e1 - t427 * t26 * t30 * t106 / 0.4e1 - t31 * t190 / 0.2e1 - t434 / 0.6e1 - t31 * t157 * t174 / 0.6e1
  t444 = t116 * t157 * t174
  t447 = t116 * t193 * t199
  t458 = t103 * t195
  t486 = t163 * t298
  t506 = t31 * t193 * t199 / 0.2e1 - t444 / 0.18e2 + t447 / 0.6e1 - t120 * t123 * t343 * t174 / 0.12e2 - t291 * t299 * t385 * t97 * t105 / 0.6e1 + t291 * t299 * t301 * t458 / 0.3e1 - t194 / t165 / t95 * t287 * t289 * t296 * t370 / 0.2e1 + t194 * t195 * t287 * t289 * t296 * t386 / 0.2e1 + t120 * t123 * t289 * t364 * t168 * t173 / 0.6e1 + t120 * t123 * t156 * t160 * t486 * t171 * t97 * t103 * t104 * t381 / 0.12e2 - t194 * t196 * t289 * t364 * t179 / 0.2e1 - t120 * t98 * t458 * t182 * t486 * t171 * t381 / 0.4e1
  t508 = f.my_piecewise3(t1, 0, t439 + t506)
  t509 = t209 ** 2
  t510 = 0.1e1 / t509
  t511 = t211 ** 2
  t515 = f.my_piecewise5(t10, 0, t6, 0, -t422)
  t519 = f.my_piecewise3(t208, 0, 0.4e1 / 0.9e1 * t510 * t511 + 0.4e1 / 0.3e1 * t209 * t515)
  t526 = t214 * t114 * t30 * t271
  t531 = t275 * t353 * t30 * t271 / 0.18e2
  t533 = f.my_piecewise3(t205, 0, -t519 * t26 * t30 * t271 / 0.4e1 - t526 / 0.6e1 + t531)
  d11 = 0.2e1 * t203 + 0.2e1 * t281 + t2 * (t508 + t533)
  t536 = -t3 - t20
  t537 = f.my_piecewise5(t6, 0, t10, 0, t536)
  t540 = f.my_piecewise3(t16, 0, 0.4e1 / 0.3e1 * t17 * t537)
  t542 = t540 * t26 * t30
  t546 = f.my_piecewise3(t1, 0, -t542 * t106 / 0.4e1 - t118)
  t548 = f.my_piecewise5(t10, 0, t6, 0, -t536)
  t551 = f.my_piecewise3(t208, 0, 0.4e1 / 0.3e1 * t209 * t548)
  t553 = t551 * t26 * t30
  t557 = t275 * t26 * t30
  t558 = f.my_piecewise3(t257, 0, 0)
  t560 = 0.10e2 / 0.3e1 * tau1 * t225
  t561 = t223 * r1
  t563 = 0.1e1 / t218 / t561
  t568 = t244 ** 2
  t569 = t568 ** 2
  t570 = 0.1e1 / t569
  t580 = -0.700e3 / 0.243e3 * t58 * t230 * t563 - t66 * t235 / t217 / t236 / t223 / 0.108e3
  t590 = f.my_piecewise3(t256, t558, t34 * (-t560 + 0.2e1 / 0.27e2 * s2 * t563) + t46 * t570 * t580 / 0.25e2 - params.gamma * (-t560 + 0.2e1 / 0.3e1 * t248 * t563) / 0.3e1)
  t591 = t123 * t590
  t592 = t557 * t591
  t593 = t259 ** 2
  t594 = 0.1e1 / t593
  t596 = jnp.exp(-0.2e1 / 0.3e1 * t260)
  t597 = 0.1e1 / t596
  t598 = t594 * t597
  t599 = t260 ** 2
  t601 = t599 - 0.2e1 * t260 + 0.3e1
  t602 = 0.1e1 / t601
  t603 = t598 * t602
  t604 = t260 - 0.2e1
  t605 = t604 ** 2
  t606 = t605 * t262
  t607 = t606 * t270
  t608 = t603 * t607
  t611 = t122 * t590
  t612 = t611 * t598
  t613 = t602 * t605
  t614 = t613 * t267
  t616 = t611 * t594
  t617 = t597 * t602
  t619 = t617 * t605 * t264
  t622 = t612 * t614 - t616 * t619 / 0.2e1
  t623 = t622 * t269
  t624 = t263 * t623
  t627 = t263 * t268
  t628 = t557 * t627
  t629 = 0.1e1 / t599
  t630 = t629 * t122
  t632 = t598 * t613
  t633 = t630 * t590 * t632
  t637 = f.my_piecewise3(t205, 0, -t553 * t271 / 0.4e1 - t279 - t592 * t608 / 0.12e2 - t557 * t624 / 0.4e1 + t628 * t633 / 0.4e1)
  t641 = 0.2e1 * t420
  t642 = f.my_piecewise5(t6, 0, t10, 0, t641)
  t646 = f.my_piecewise3(t16, 0, 0.4e1 / 0.9e1 * t414 * t537 * t22 + 0.4e1 / 0.3e1 * t17 * t642)
  t653 = t540 * t114 * t30 * t106
  t668 = f.my_piecewise3(t1, 0, -t646 * t26 * t30 * t106 / 0.4e1 - t653 / 0.12e2 - t542 * t157 * t174 / 0.12e2 - t542 * t190 / 0.4e1 + t542 * t193 * t199 / 0.4e1 - t350 / 0.12e2 + t357 - t444 / 0.36e2 - t434 / 0.12e2 + t447 / 0.12e2)
  t672 = f.my_piecewise5(t10, 0, t6, 0, -t641)
  t676 = f.my_piecewise3(t208, 0, 0.4e1 / 0.9e1 * t510 * t548 * t211 + 0.4e1 / 0.3e1 * t209 * t672)
  t683 = t551 * t114 * t30 * t271
  t690 = t277 * t591 * t608
  t694 = t277 * t624
  t700 = t277 * t627 * t633
  t703 = f.my_piecewise3(t205, 0, -t676 * t26 * t30 * t271 / 0.4e1 - t683 / 0.12e2 - t526 / 0.12e2 + t531 - t216 * t591 * t608 / 0.12e2 - t690 / 0.36e2 - t216 * t624 / 0.4e1 - t694 / 0.12e2 + t216 * t627 * t633 / 0.4e1 + t700 / 0.12e2)
  d12 = t203 + t281 + t546 + t637 + t2 * (t668 + t703)
  t708 = t537 ** 2
  t712 = 0.2e1 * t19 + 0.2e1 * t420
  t713 = f.my_piecewise5(t6, 0, t10, 0, t712)
  t717 = f.my_piecewise3(t16, 0, 0.4e1 / 0.9e1 * t414 * t708 + 0.4e1 / 0.3e1 * t17 * t713)
  t724 = f.my_piecewise3(t1, 0, -t717 * t26 * t30 * t106 / 0.4e1 - t653 / 0.6e1 + t357)
  t728 = 0.80e2 / 0.9e1 * tau1 * t563
  t730 = 0.1e1 / t218 / t236
  t737 = t580 ** 2
  t760 = f.my_piecewise3(t256, t558, t34 * (t728 - 0.22e2 / 0.81e2 * s2 * t730) - 0.4e1 / 0.125e3 * t46 / t569 / t243 * t737 + t46 * t570 * (0.7700e4 / 0.729e3 * t58 * t230 * t730 + 0.19e2 / 0.324e3 * t66 * t235 / t217 / t236 / t561) / 0.25e2 - params.gamma * (t728 - 0.22e2 / 0.9e1 * t248 * t730) / 0.3e1)
  t769 = t590 ** 2
  t771 = t557 * t288 * t769
  t772 = t593 ** 2
  t773 = 0.1e1 / t772
  t774 = t596 ** 2
  t775 = 0.1e1 / t774
  t776 = t773 * t775
  t777 = t601 ** 2
  t778 = 0.1e1 / t777
  t779 = t776 * t778
  t780 = t605 ** 2
  t781 = t780 * t262
  t800 = t122 * t760
  t803 = t122 * t769
  t805 = 0.1e1 / t593 / t259
  t806 = t805 * t597
  t810 = t287 * t769
  t811 = t810 * t776
  t812 = t778 * t780
  t816 = t778 * t605
  t823 = 0.2e1 * t260 * t122 * t590 * t632 - 0.2e1 * t616 * t617 * t605
  t827 = t605 * t604
  t828 = t778 * t827
  t832 = t810 * t773
  t833 = t775 * t778
  t856 = -t690 / 0.18e2 + t700 / 0.6e1 - t557 * t123 * t760 * t608 / 0.12e2 - t592 * t603 * t606 * t623 / 0.6e1 - t771 * t779 * t781 * t270 / 0.12e2 + t557 * t263 * t622 * t633 / 0.2e1 + t628 * t630 * t760 * t632 / 0.4e1 - t553 * t591 * t608 / 0.6e1 + t553 * t627 * t633 / 0.2e1 - t557 * t263 * (t800 * t598 * t614 - 0.2e1 * t803 * t806 * t614 - t811 * t812 * t267 / 0.3e1 - t612 * t816 * t267 * t823 + 0.2e1 * t811 * t828 * t267 + 0.2e1 / 0.3e1 * t832 * t833 * t780 * t264 - t800 * t594 * t619 / 0.2e1 + t803 * t805 * t619 + t612 * t816 * t264 * t823 / 0.2e1 - t832 * t833 * t827 * t264) * t269 / 0.4e1 - t694 / 0.6e1
  t857 = t548 ** 2
  t861 = f.my_piecewise5(t10, 0, t6, 0, -t712)
  t865 = f.my_piecewise3(t208, 0, 0.4e1 / 0.9e1 * t510 * t857 + 0.4e1 / 0.3e1 * t209 * t861)
  t877 = t268 * t629
  t906 = t597 * t778
  t926 = -t865 * t26 * t30 * t271 / 0.4e1 - t553 * t624 / 0.2e1 - t771 * t779 * t827 * t262 * t270 / 0.6e1 + t771 * t779 * t781 * t877 / 0.3e1 - t628 / t599 / t260 * t287 * t769 * t776 * t812 / 0.2e1 + t628 * t629 * t287 * t769 * t776 * t828 / 0.2e1 - t683 / 0.6e1 + t531 + t557 * t123 * t769 * t806 * t602 * t607 / 0.6e1 + t557 * t123 * t590 * t594 * t906 * t605 * t262 * t268 * t269 * t823 / 0.12e2 - t628 * t630 * t769 * t806 * t613 / 0.2e1 - t557 * t263 * t877 * t616 * t906 * t605 * t823 / 0.4e1
  t928 = f.my_piecewise3(t205, 0, t856 + t926)
  d22 = 0.2e1 * t546 + 0.2e1 * t637 + t2 * (t724 + t928)
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
  t2 = r0 + r1
  t3 = 0.1e1 / t2
  t6 = 0.2e1 * r0 * t3 <= f.p.zeta_threshold
  t7 = f.p.zeta_threshold - 0.1e1
  t10 = 0.2e1 * r1 * t3 <= f.p.zeta_threshold
  t11 = -t7
  t12 = r0 - r1
  t13 = t12 * t3
  t14 = f.my_piecewise5(t6, t7, t10, t11, t13)
  t15 = 0.1e1 + t14
  t16 = t15 <= f.p.zeta_threshold
  t17 = t15 ** (0.1e1 / 0.3e1)
  t18 = t2 ** 2
  t19 = 0.1e1 / t18
  t21 = -t12 * t19 + t3
  t22 = f.my_piecewise5(t6, 0, t10, 0, t21)
  t25 = f.my_piecewise3(t16, 0, 0.4e1 / 0.3e1 * t17 * t22)
  t26 = t2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = t25 * t28 * t32
  t34 = 4 ** (0.1e1 / 0.3e1)
  t35 = params.lambda__ ** 2
  t36 = t35 - params.lambda__ + 0.1e1 / 0.2e1
  t37 = r0 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t42 = 0.2e1 * tau0 / t38 / r0
  t43 = 6 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = jnp.pi ** 2
  t46 = t45 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = t44 * t47
  t49 = 0.3e1 / 0.5e1 * t48
  t50 = r0 ** 2
  t52 = 0.1e1 / t38 / t50
  t59 = (0.2e1 * params.lambda__ - 0.1e1) ** 2
  t60 = t59 * t43
  t61 = 0.1e1 / t47
  t62 = t61 * s0
  t66 = t59 ** 2
  t68 = params.beta * t66 * t44
  t70 = 0.1e1 / t46 / t45
  t71 = s0 ** 2
  t72 = t70 * t71
  t73 = t50 ** 2
  t74 = t73 * r0
  t80 = 0.1e1 + 0.175e3 / 0.162e3 * t60 * t62 * t52 + t68 * t72 / t37 / t74 / 0.576e3
  t81 = t80 ** (0.1e1 / 0.5e1)
  t85 = t59 * s0
  t91 = t36 * (t42 - t49 - s0 * t52 / 0.36e2) + t48 * (t81 - 0.1e1) / 0.5e1 - params.gamma * (t42 - t85 * t52 / 0.4e1) / 0.3e1
  t92 = abs(t91)
  t93 = t92 < 0.50e-12
  t94 = 0.0e0 < t91
  t95 = f.my_piecewise3(t94, 0.50e-12, -0.50e-12)
  t96 = f.my_piecewise3(t93, t95, t91)
  t97 = br89_x(t96)
  t99 = jnp.exp(t97 / 0.3e1)
  t100 = t34 * t99
  t101 = jnp.exp(-t97)
  t104 = t101 * (0.1e1 + t97 / 0.2e1)
  t105 = 0.1e1 - t104
  t106 = 0.1e1 / t97
  t107 = t105 * t106
  t108 = t100 * t107
  t111 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t112 = t111 * f.p.zeta_threshold
  t114 = f.my_piecewise3(t16, t112, t17 * t15)
  t116 = 0.1e1 / t27 / t2
  t118 = t114 * t116 * t32
  t122 = t114 * t26 * t32
  t123 = jnp.pi ** (0.1e1 / 0.3e1)
  t124 = t123 ** 2
  t125 = t34 * t124
  t126 = f.my_piecewise3(t94, 0, 0)
  t128 = 0.10e2 / 0.3e1 * tau0 * t52
  t129 = t50 * r0
  t131 = 0.1e1 / t38 / t129
  t136 = t81 ** 2
  t137 = t136 ** 2
  t138 = 0.1e1 / t137
  t148 = -0.700e3 / 0.243e3 * t60 * t62 * t131 - t68 * t72 / t37 / t73 / t50 / 0.108e3
  t158 = f.my_piecewise3(t93, t126, t36 * (-t128 + 0.2e1 / 0.27e2 * s0 * t131) + t48 * t138 * t148 / 0.25e2 - params.gamma * (-t128 + 0.2e1 / 0.3e1 * t85 * t131) / 0.3e1)
  t159 = t125 * t158
  t160 = t122 * t159
  t161 = t96 ** 2
  t162 = 0.1e1 / t161
  t164 = jnp.exp(-0.2e1 / 0.3e1 * t97)
  t165 = 0.1e1 / t164
  t166 = t162 * t165
  t167 = t97 ** 2
  t169 = t167 - 0.2e1 * t97 + 0.3e1
  t170 = 0.1e1 / t169
  t171 = t166 * t170
  t172 = t97 - 0.2e1
  t173 = t172 ** 2
  t174 = t173 * t99
  t175 = t124 * t158
  t176 = t175 * t166
  t177 = t170 * t173
  t178 = t177 * t104
  t180 = t175 * t162
  t181 = t165 * t170
  t183 = t181 * t173 * t101
  t186 = t176 * t178 - t180 * t183 / 0.2e1
  t187 = t186 * t106
  t188 = t174 * t187
  t189 = t171 * t188
  t192 = t123 * jnp.pi
  t193 = t34 * t192
  t194 = t158 ** 2
  t195 = t193 * t194
  t196 = t122 * t195
  t197 = t161 ** 2
  t198 = 0.1e1 / t197
  t199 = t164 ** 2
  t200 = 0.1e1 / t199
  t201 = t198 * t200
  t202 = t169 ** 2
  t203 = 0.1e1 / t202
  t204 = t201 * t203
  t205 = t173 ** 2
  t206 = t205 * t99
  t207 = t206 * t107
  t208 = t204 * t207
  t211 = t100 * t186
  t212 = t122 * t211
  t213 = 0.1e1 / t167
  t214 = t213 * t124
  t216 = t166 * t177
  t217 = t214 * t158 * t216
  t220 = t100 * t105
  t221 = t122 * t220
  t223 = 0.80e2 / 0.9e1 * tau0 * t131
  t225 = 0.1e1 / t38 / t73
  t231 = 0.1e1 / t137 / t80
  t232 = t148 ** 2
  t245 = 0.7700e4 / 0.729e3 * t60 * t62 * t225 + 0.19e2 / 0.324e3 * t68 * t72 / t37 / t73 / t129
  t255 = f.my_piecewise3(t93, t126, t36 * (t223 - 0.22e2 / 0.81e2 * s0 * t225) - 0.4e1 / 0.125e3 * t48 * t231 * t232 + t48 * t138 * t245 / 0.25e2 - params.gamma * (t223 - 0.22e2 / 0.9e1 * t85 * t225) / 0.3e1)
  t257 = t214 * t255 * t216
  t261 = t114 * t28 * t32
  t262 = t100 * t187
  t265 = t124 * t255
  t266 = t265 * t166
  t268 = t124 * t194
  t270 = 0.1e1 / t161 / t96
  t271 = t270 * t165
  t272 = t268 * t271
  t275 = t192 * t194
  t276 = t275 * t201
  t277 = t203 * t205
  t278 = t277 * t104
  t281 = t203 * t173
  t282 = t97 * t124
  t285 = t181 * t173
  t288 = 0.2e1 * t282 * t158 * t216 - 0.2e1 * t180 * t285
  t289 = t104 * t288
  t290 = t281 * t289
  t292 = t173 * t172
  t293 = t203 * t292
  t294 = t293 * t104
  t297 = t275 * t198
  t298 = t200 * t203
  t299 = t205 * t101
  t300 = t298 * t299
  t303 = t265 * t162
  t306 = t268 * t270
  t308 = t101 * t288
  t309 = t281 * t308
  t313 = t298 * t292 * t101
  t315 = t266 * t178 - 0.2e1 * t272 * t178 - t276 * t278 / 0.3e1 - t176 * t290 + 0.2e1 * t276 * t294 + 0.2e1 / 0.3e1 * t297 * t300 - t303 * t183 / 0.2e1 + t306 * t183 + t176 * t309 / 0.2e1 - t297 * t313
  t316 = t315 * t106
  t317 = t100 * t316
  t320 = t17 ** 2
  t321 = 0.1e1 / t320
  t322 = t22 ** 2
  t326 = 0.1e1 / t18 / t2
  t329 = 0.2e1 * t12 * t326 - 0.2e1 * t19
  t330 = f.my_piecewise5(t6, 0, t10, 0, t329)
  t334 = f.my_piecewise3(t16, 0, 0.4e1 / 0.9e1 * t321 * t322 + 0.4e1 / 0.3e1 * t17 * t330)
  t336 = t334 * t26 * t32
  t340 = t25 * t26 * t32
  t343 = t340 * t159
  t344 = t174 * t107
  t345 = t171 * t344
  t348 = -t33 * t108 / 0.6e1 + t118 * t108 / 0.18e2 - t160 * t189 / 0.6e1 - t196 * t208 / 0.12e2 + t212 * t217 / 0.2e1 + t221 * t257 / 0.4e1 - t261 * t262 / 0.6e1 - t122 * t317 / 0.4e1 - t336 * t108 / 0.4e1 - t340 * t262 / 0.2e1 - t343 * t345 / 0.6e1
  t349 = t340 * t220
  t352 = t261 * t159
  t355 = t261 * t220
  t358 = t125 * t255
  t359 = t122 * t358
  t362 = t292 * t99
  t363 = t362 * t107
  t364 = t204 * t363
  t367 = t105 * t213
  t368 = t206 * t367
  t369 = t204 * t368
  t373 = 0.1e1 / t167 / t97
  t374 = t373 * t192
  t376 = t201 * t277
  t377 = t374 * t194 * t376
  t380 = t213 * t192
  t382 = t201 * t293
  t383 = t380 * t194 * t382
  t386 = t125 * t194
  t387 = t122 * t386
  t388 = t271 * t170
  t389 = t388 * t344
  t392 = t158 * t162
  t393 = t125 * t392
  t394 = t122 * t393
  t395 = t165 * t203
  t396 = t395 * t173
  t397 = t99 * t105
  t398 = t106 * t288
  t399 = t397 * t398
  t400 = t396 * t399
  t404 = t271 * t177
  t405 = t214 * t194 * t404
  t408 = t100 * t367
  t409 = t122 * t408
  t411 = t395 * t173 * t288
  t412 = t180 * t411
  t415 = t349 * t217 / 0.2e1 - t352 * t345 / 0.18e2 + t355 * t217 / 0.6e1 - t359 * t345 / 0.12e2 - t196 * t364 / 0.6e1 + t196 * t369 / 0.3e1 - t221 * t377 / 0.2e1 + t221 * t383 / 0.2e1 + t387 * t389 / 0.6e1 + t394 * t400 / 0.12e2 - t221 * t405 / 0.2e1 - t409 * t412 / 0.4e1
  t417 = f.my_piecewise3(t1, 0, t348 + t415)
  t419 = r1 <= f.p.dens_threshold
  t420 = f.my_piecewise5(t10, t7, t6, t11, -t13)
  t421 = 0.1e1 + t420
  t422 = t421 <= f.p.zeta_threshold
  t423 = t421 ** (0.1e1 / 0.3e1)
  t424 = t423 ** 2
  t425 = 0.1e1 / t424
  t427 = f.my_piecewise5(t10, 0, t6, 0, -t21)
  t428 = t427 ** 2
  t432 = f.my_piecewise5(t10, 0, t6, 0, -t329)
  t436 = f.my_piecewise3(t422, 0, 0.4e1 / 0.9e1 * t425 * t428 + 0.4e1 / 0.3e1 * t423 * t432)
  t439 = r1 ** (0.1e1 / 0.3e1)
  t440 = t439 ** 2
  t444 = 0.2e1 * tau1 / t440 / r1
  t445 = r1 ** 2
  t447 = 0.1e1 / t440 / t445
  t456 = s2 ** 2
  t458 = t445 ** 2
  t466 = (0.1e1 + 0.175e3 / 0.162e3 * t60 * t61 * s2 * t447 + t68 * t70 * t456 / t439 / t458 / r1 / 0.576e3) ** (0.1e1 / 0.5e1)
  t476 = t36 * (t444 - t49 - s2 * t447 / 0.36e2) + t48 * (t466 - 0.1e1) / 0.5e1 - params.gamma * (t444 - t59 * s2 * t447 / 0.4e1) / 0.3e1
  t477 = abs(t476)
  t480 = f.my_piecewise3(0.0e0 < t476, 0.50e-12, -0.50e-12)
  t481 = f.my_piecewise3(t477 < 0.50e-12, t480, t476)
  t482 = br89_x(t481)
  t484 = jnp.exp(t482 / 0.3e1)
  t486 = jnp.exp(-t482)
  t493 = t34 * t484 * (0.1e1 - t486 * (0.1e1 + t482 / 0.2e1)) / t482
  t498 = f.my_piecewise3(t422, 0, 0.4e1 / 0.3e1 * t423 * t427)
  t504 = f.my_piecewise3(t422, t112, t423 * t421)
  t510 = f.my_piecewise3(t419, 0, -t436 * t26 * t32 * t493 / 0.4e1 - t498 * t28 * t32 * t493 / 0.6e1 + t504 * t116 * t32 * t493 / 0.18e2)
  t514 = t122 * t193 * t158 * t198
  t515 = t298 * t205
  t523 = t122 * t193 * t194 * t198
  t525 = 0.1e1 / t202 / t169
  t526 = t200 * t525
  t527 = t526 * t205
  t531 = t186 * t213
  t555 = t298 * t292
  t557 = t397 * t106 * t158
  t561 = t105 * t373
  t563 = t122 * t100 * t561
  t564 = t192 * t255
  t565 = t564 * t198
  t579 = -t514 * t515 * t397 * t106 * t255 / 0.4e1 + t523 * t527 * t399 / 0.4e1 - 0.3e1 / 0.4e1 * t122 * t100 * t531 * t412 - 0.3e1 / 0.2e1 * t409 * t265 * t270 * t181 * t173 * t158 - t409 * t303 * t411 / 0.2e1 + t514 * t515 * t397 * t213 * t255 + t340 * t393 * t400 / 0.4e1 - t122 * t193 * t255 * t198 * t555 * t557 / 0.2e1 - 0.3e1 / 0.2e1 * t563 * t565 * t298 * t205 * t158 + 0.3e1 / 0.2e1 * t409 * t565 * t298 * t292 * t158 - 0.3e1 / 0.4e1 * t340 * t408 * t412
  t629 = t97 * t192 * t194
  t644 = 0.2e1 / 0.3e1 * t297 * t515 + 0.2e1 * t282 * t255 * t216 - 0.4e1 * t282 * t194 * t404 + 0.4e1 / 0.3e1 * t629 * t376 - 0.2e1 * t282 * t392 * t411 + 0.4e1 * t629 * t382 - 0.2e1 * t303 * t285 + 0.4e1 * t306 * t285 + 0.2e1 * t412 - 0.4e1 * t297 * t555
  t657 = t261 * t393 * t400 / 0.12e2 - t261 * t408 * t412 / 0.4e1 + t122 * t125 * t255 * t270 * t285 * t557 / 0.2e1 + t122 * t125 * t255 * t162 * t400 / 0.6e1 + t523 * t526 * t292 * t399 / 0.2e1 - t523 * t527 * t397 * t213 * t288 + 0.3e1 / 0.2e1 * t563 * t297 * t526 * t205 * t288 - 0.3e1 / 0.2e1 * t409 * t297 * t526 * t292 * t288 - t122 * t125 * t194 * t270 * t400 / 0.3e1 + t394 * t396 * t397 * t106 * t644 / 0.12e2 + t409 * t306 * t411 - t409 * t180 * t395 * t173 * t644 / 0.4e1
  t664 = t165 * t525
  t665 = t288 ** 2
  t685 = t18 ** 2
  t689 = 0.6e1 * t326 - 0.6e1 * t12 / t685
  t690 = f.my_piecewise5(t6, 0, t10, 0, t689)
  t694 = f.my_piecewise3(t16, 0, -0.8e1 / 0.27e2 / t320 / t15 * t322 * t22 + 0.4e1 / 0.3e1 * t321 * t22 * t330 + 0.4e1 / 0.3e1 * t17 * t690)
  t705 = t194 * t158
  t707 = t122 * t193 * t705
  t709 = 0.1e1 / t197 / t96
  t710 = t709 * t200
  t711 = t710 * t203
  t727 = t394 * t396 * t99 * t186 * t398 / 0.4e1 + t409 * t180 * t664 * t173 * t665 / 0.2e1 - t394 * t664 * t173 * t397 * t106 * t665 / 0.6e1 - t694 * t26 * t32 * t108 / 0.4e1 - 0.3e1 / 0.4e1 * t336 * t262 - t261 * t317 / 0.4e1 - t355 * t405 / 0.2e1 + t707 * t711 * t363 - 0.2e1 * t707 * t711 * t368 + 0.3e1 * t221 * t374 * t705 * t710 * t277 - 0.3e1 * t221 * t380 * t705 * t710 * t293
  t730 = t198 * t165
  t738 = 0.1e1 / t197 / t161
  t740 = 0.1e1 / t199 / t164
  t741 = t738 * t740
  t742 = t525 * t205
  t747 = t261 * t195
  t758 = t122 * t34 * t45 * t705
  t759 = t741 * t525
  t763 = t205 * t172
  t764 = t763 * t99
  t779 = -t122 * t125 * t705 * t730 * t170 * t344 / 0.2e1 + 0.3e1 / 0.2e1 * t221 * t213 * t45 * t705 * t741 * t742 - t747 * t364 / 0.6e1 + t747 * t369 / 0.3e1 - t355 * t377 / 0.2e1 + t355 * t383 / 0.2e1 - t758 * t759 * t207 / 0.2e1 + 0.7e1 / 0.3e1 * t758 * t759 * t764 * t367 + t261 * t211 * t217 / 0.2e1 - 0.3e1 / 0.2e1 * t212 * t405 + t355 * t257 / 0.4e1 + t340 * t386 * t389 / 0.2e1
  t795 = t205 * t173
  t796 = t795 * t99
  t815 = 0.880e3 / 0.27e2 * tau0 * t225
  t817 = 0.1e1 / t38 / t74
  t822 = t80 ** 2
  t836 = t73 ** 2
  t852 = f.my_piecewise3(t93, t126, t36 * (-t815 + 0.308e3 / 0.243e3 * s0 * t817) + 0.36e2 / 0.625e3 * t48 / t137 / t822 * t232 * t148 - 0.12e2 / 0.125e3 * t48 * t231 * t148 * t245 + t48 * t138 * (-0.107800e6 / 0.2187e4 * t60 * t62 * t817 - 0.209e3 / 0.486e3 * t68 * t72 / t37 / t836) / 0.25e2 - params.gamma * (-t815 + 0.308e3 / 0.27e2 * t85 * t817) / 0.3e1)
  t857 = 0.3e1 / 0.2e1 * t349 * t383 - t196 * t204 * t362 * t187 / 0.2e1 + t196 * t204 * t206 * t531 - 0.11e2 / 0.18e2 * t758 * t759 * t764 * t107 + 0.23e2 / 0.36e2 * t758 * t759 * t796 * t367 - 0.3e1 / 0.2e1 * t349 * t405 + t261 * t386 * t389 / 0.6e1 + 0.3e1 / 0.4e1 * t122 * t100 * t315 * t217 + 0.3e1 / 0.4e1 * t212 * t257 + 0.3e1 / 0.4e1 * t349 * t257 + t221 * t214 * t852 * t216 / 0.4e1
  t882 = t340 * t195
  t896 = t33 * t220 * t217 / 0.2e1 + t118 * t159 * t345 / 0.18e2 - t118 * t220 * t217 / 0.6e1 + 0.3e1 / 0.2e1 * t221 * t214 * t705 * t730 * t177 - t352 * t189 / 0.6e1 + t387 * t388 * t188 / 0.2e1 - t747 * t208 / 0.12e2 + t707 * t711 * t207 / 0.2e1 - t882 * t208 / 0.4e1 - 0.5e1 / 0.36e2 * t758 * t759 * t796 * t107 - t33 * t159 * t345 / 0.6e1 - 0.3e1 / 0.2e1 * t758 * t759 * t796 * t561
  t898 = t167 ** 2
  t902 = t525 * t795
  t909 = t525 * t763
  t938 = 0.3e1 / 0.2e1 * t221 / t898 * t45 * t705 * t741 * t902 - 0.3e1 * t221 * t373 * t45 * t705 * t741 * t909 - t343 * t189 / 0.2e1 - t359 * t189 / 0.4e1 - t160 * t171 * t174 * t316 / 0.4e1 - t196 * t204 * t206 * t187 / 0.4e1 - 0.3e1 / 0.2e1 * t212 * t377 + 0.3e1 / 0.2e1 * t212 * t383 - t882 * t364 / 0.2e1 + t882 * t369 - 0.3e1 / 0.2e1 * t349 * t377 - t261 * t358 * t345 / 0.12e2
  t955 = t124 * t852
  t959 = t192 * t705
  t960 = t959 * t709
  t963 = t45 * t705
  t964 = t963 * t738
  t965 = t740 * t525
  t975 = t124 * t705
  t985 = t564 * t201
  t986 = t101 * t158
  t990 = t959 * t710
  t993 = t963 * t741
  t1000 = t265 * t271
  t1011 = -t955 * t162 * t183 / 0.2e1 - 0.4e1 * t960 * t300 + t964 * t965 * t795 * t101 / 0.18e2 + 0.6e1 * t960 * t313 - 0.3e1 * t964 * t965 * t299 - 0.3e1 * t975 * t198 * t183 + 0.10e2 / 0.3e1 * t964 * t965 * t763 * t101 + t955 * t166 * t178 + 0.2e1 * t985 * t277 * t986 + 0.2e1 * t990 * t278 - t993 * t902 * t104 / 0.9e1 - 0.2e1 * t276 * t742 * t308 + 0.3e1 * t1000 * t177 * t986 + t266 * t309 - 0.2e1 * t272 * t309 + t176 * t281 * t101 * t644 / 0.2e1
  t1015 = t525 * t173
  t1027 = t525 * t292
  t1041 = t104 * t158
  t1059 = 0.6e1 * t975 * t730 * t178 - t176 * t1015 * t101 * t665 - 0.12e2 * t990 * t294 - 0.2e1 / 0.3e1 * t993 * t909 * t104 + 0.6e1 * t993 * t742 * t104 + 0.3e1 * t276 * t1027 * t308 - 0.3e1 * t985 * t293 * t986 - 0.6e1 * t276 * t1027 * t289 + 0.2e1 * t176 * t1015 * t104 * t665 - 0.6e1 * t1000 * t177 * t1041 - 0.2e1 * t266 * t290 - t985 * t277 * t1041 + 0.4e1 * t272 * t290 + t276 * t742 * t289 - t176 * t281 * t104 * t644 + 0.6e1 * t985 * t293 * t1041
  t1078 = 0.1e1 / t27 / t18
  t1085 = -t122 * t125 * t852 * t345 / 0.12e2 - t340 * t358 * t345 / 0.4e1 - t336 * t159 * t345 / 0.4e1 + 0.3e1 / 0.4e1 * t336 * t220 * t217 + 0.3e1 / 0.2e1 * t340 * t211 * t217 - t122 * t100 * (t1011 + t1059) * t106 / 0.4e1 + t118 * t262 / 0.6e1 - t334 * t28 * t32 * t108 / 0.4e1 - t33 * t262 / 0.2e1 + t25 * t116 * t32 * t108 / 0.6e1 - 0.5e1 / 0.54e2 * t114 * t1078 * t32 * t108 - 0.3e1 / 0.4e1 * t340 * t317
  t1089 = f.my_piecewise3(t1, 0, t579 + t657 + t727 + t779 + t857 + t896 + t938 + t1085)
  t1099 = f.my_piecewise5(t10, 0, t6, 0, -t689)
  t1103 = f.my_piecewise3(t422, 0, -0.8e1 / 0.27e2 / t424 / t421 * t428 * t427 + 0.4e1 / 0.3e1 * t425 * t427 * t432 + 0.4e1 / 0.3e1 * t423 * t1099)
  t1121 = f.my_piecewise3(t419, 0, -t1103 * t26 * t32 * t493 / 0.4e1 - t436 * t28 * t32 * t493 / 0.4e1 + t498 * t116 * t32 * t493 / 0.6e1 - 0.5e1 / 0.54e2 * t504 * t1078 * t32 * t493)
  d111 = 0.3e1 * t417 + 0.3e1 * t510 + t2 * (t1089 + t1121)

  res = {'v3rho3': d111}
  return res
