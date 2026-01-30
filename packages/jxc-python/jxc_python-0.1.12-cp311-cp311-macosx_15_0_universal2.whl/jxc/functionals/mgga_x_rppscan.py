"""Generated from mgga_x_rppscan.mpl."""

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

  params_c1 = 0.667
  params_dp2 = 0.361

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

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  r2scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx)))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r2scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  params_c1 = 0.667
  params_dp2 = 0.361

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

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  r2scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx)))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r2scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  params_c1 = 0.667
  params_dp2 = 0.361

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

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  r2scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx)))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r2scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t28 = 6 ** (0.1e1 / 0.3e1)
  t29 = jnp.pi ** 2
  t30 = t29 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = 0.1e1 / t31
  t33 = t28 * t32
  t34 = r0 ** 2
  t35 = r0 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t38 = 0.1e1 / t36 / t34
  t39 = s0 * t38
  t44 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t45 = t28 ** 2
  t49 = t44 * t45 / t30 / t29
  t50 = s0 ** 2
  t51 = t34 ** 2
  t54 = 0.1e1 / t35 / t51 / r0
  t56 = t44 * t28
  t57 = t32 * s0
  t58 = t57 * t38
  t61 = jnp.exp(-0.27e2 / 0.80e2 * t56 * t58)
  t65 = jnp.sqrt(0.146e3)
  t66 = t65 * t28
  t70 = 0.1e1 / t36 / r0
  t73 = tau0 * t70 - t39 / 0.8e1
  t75 = 0.3e1 / 0.10e2 * t45 * t31
  t76 = params.eta * s0
  t79 = t75 + t76 * t38 / 0.8e1
  t80 = 0.1e1 / t79
  t81 = t73 * t80
  t82 = 0.1e1 - t81
  t84 = t82 ** 2
  t86 = jnp.exp(-t84 / 0.2e1)
  t89 = 0.7e1 / 0.12960e5 * t66 * t58 + t65 * t82 * t86 / 0.100e3
  t90 = t89 ** 2
  t91 = params.k1 + 0.5e1 / 0.972e3 * t33 * t39 + t49 * t50 * t54 * t61 / 0.576e3 + t90
  t96 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t91)
  t97 = t81 <= 0.25e1
  t98 = 0.25e1 < t81
  t99 = f.my_piecewise3(t98, 0.25e1, t81)
  t101 = t99 ** 2
  t103 = t101 * t99
  t105 = t101 ** 2
  t107 = t105 * t99
  t109 = t105 * t101
  t114 = f.my_piecewise3(t98, t81, 0.25e1)
  t115 = 0.1e1 - t114
  t118 = jnp.exp(params.c2 / t115)
  t120 = f.my_piecewise3(t97, 0.1e1 - 0.667e0 * t99 - 0.4445555e0 * t101 - 0.663086601049e0 * t103 + 0.1451297044490e1 * t105 - 0.887998041597e0 * t107 + 0.234528941479e0 * t109 - 0.23185843322e-1 * t105 * t103, -params.d * t118)
  t121 = 0.1e1 - t120
  t124 = t96 * t121 + 0.1174e1 * t120
  t126 = jnp.sqrt(0.3e1)
  t127 = 0.1e1 / t30
  t128 = t45 * t127
  t129 = jnp.sqrt(s0)
  t131 = 0.1e1 / t35 / r0
  t133 = t128 * t129 * t131
  t134 = jnp.sqrt(t133)
  t138 = jnp.exp(-0.98958e1 * t126 / t134)
  t139 = 0.1e1 - t138
  t140 = t27 * t124 * t139
  t143 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t140)
  t144 = r1 <= f.p.dens_threshold
  t145 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t146 = 0.1e1 + t145
  t147 = t146 <= f.p.zeta_threshold
  t148 = t146 ** (0.1e1 / 0.3e1)
  t150 = f.my_piecewise3(t147, t22, t148 * t146)
  t151 = t5 * t150
  t152 = r1 ** 2
  t153 = r1 ** (0.1e1 / 0.3e1)
  t154 = t153 ** 2
  t156 = 0.1e1 / t154 / t152
  t157 = s2 * t156
  t160 = s2 ** 2
  t161 = t152 ** 2
  t164 = 0.1e1 / t153 / t161 / r1
  t166 = t32 * s2
  t167 = t166 * t156
  t170 = jnp.exp(-0.27e2 / 0.80e2 * t56 * t167)
  t177 = 0.1e1 / t154 / r1
  t180 = tau1 * t177 - t157 / 0.8e1
  t181 = params.eta * s2
  t184 = t75 + t181 * t156 / 0.8e1
  t185 = 0.1e1 / t184
  t186 = t180 * t185
  t187 = 0.1e1 - t186
  t189 = t187 ** 2
  t191 = jnp.exp(-t189 / 0.2e1)
  t194 = 0.7e1 / 0.12960e5 * t66 * t167 + t65 * t187 * t191 / 0.100e3
  t195 = t194 ** 2
  t196 = params.k1 + 0.5e1 / 0.972e3 * t33 * t157 + t49 * t160 * t164 * t170 / 0.576e3 + t195
  t201 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t196)
  t202 = t186 <= 0.25e1
  t203 = 0.25e1 < t186
  t204 = f.my_piecewise3(t203, 0.25e1, t186)
  t206 = t204 ** 2
  t208 = t206 * t204
  t210 = t206 ** 2
  t212 = t210 * t204
  t214 = t210 * t206
  t219 = f.my_piecewise3(t203, t186, 0.25e1)
  t220 = 0.1e1 - t219
  t223 = jnp.exp(params.c2 / t220)
  t225 = f.my_piecewise3(t202, 0.1e1 - 0.667e0 * t204 - 0.4445555e0 * t206 - 0.663086601049e0 * t208 + 0.1451297044490e1 * t210 - 0.887998041597e0 * t212 + 0.234528941479e0 * t214 - 0.23185843322e-1 * t210 * t208, -params.d * t223)
  t226 = 0.1e1 - t225
  t229 = t201 * t226 + 0.1174e1 * t225
  t231 = jnp.sqrt(s2)
  t233 = 0.1e1 / t153 / r1
  t235 = t128 * t231 * t233
  t236 = jnp.sqrt(t235)
  t240 = jnp.exp(-0.98958e1 * t126 / t236)
  t241 = 0.1e1 - t240
  t242 = t27 * t229 * t241
  t245 = f.my_piecewise3(t144, 0, -0.3e1 / 0.8e1 * t151 * t242)
  t246 = t6 ** 2
  t248 = t16 / t246
  t249 = t7 - t248
  t250 = f.my_piecewise5(t10, 0, t14, 0, t249)
  t253 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t250)
  t257 = t27 ** 2
  t258 = 0.1e1 / t257
  t262 = t26 * t258 * t124 * t139 / 0.8e1
  t263 = params.k1 ** 2
  t264 = t91 ** 2
  t266 = t263 / t264
  t269 = 0.1e1 / t36 / t34 / r0
  t270 = s0 * t269
  t280 = t44 ** 2
  t281 = t29 ** 2
  t283 = t280 / t281
  t285 = t51 ** 2
  t300 = t79 ** 2
  t302 = t73 / t300
  t306 = -(-0.5e1 / 0.3e1 * tau0 * t38 + t270 / 0.3e1) * t80 - t302 * t76 * t269 / 0.3e1
  t310 = t65 * t84
  t320 = -t306
  t321 = f.my_piecewise3(t98, 0, t320)
  t336 = params.d * params.c2
  t337 = t115 ** 2
  t338 = 0.1e1 / t337
  t339 = f.my_piecewise3(t98, t320, 0)
  t343 = f.my_piecewise3(t97, -0.667e0 * t321 - 0.8891110e0 * t99 * t321 - 0.1989259803147e1 * t101 * t321 + 0.5805188177960e1 * t103 * t321 - 0.4439990207985e1 * t105 * t321 + 0.1407173648874e1 * t107 * t321 - 0.162300903254e0 * t109 * t321, -t336 * t338 * t339 * t118)
  t351 = 3 ** (0.1e1 / 0.6e1)
  t352 = t351 ** 2
  t353 = t352 ** 2
  t355 = t353 * t351 * t4
  t358 = t355 * t25 * t27 * t124
  t362 = 0.1e1 / t134 / t133 * t45 * t127
  t371 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t253 * t140 - t262 - 0.3e1 / 0.8e1 * t26 * t27 * (t266 * (-0.10e2 / 0.729e3 * t33 * t270 - t49 * t50 / t35 / t51 / t34 * t61 / 0.108e3 + 0.3e1 / 0.320e3 * t283 * t50 * s0 / t285 / r0 * t61 + 0.2e1 * t89 * (-0.7e1 / 0.4860e4 * t66 * t57 * t269 + t65 * t306 * t86 / 0.100e3 - t310 * t306 * t86 / 0.100e3)) * t121 - t96 * t343 + 0.1174e1 * t343) * t139 - 0.24739500000000000000000000000000000000000000000000e1 * t358 * t362 * t129 / t35 / t34 * t138)
  t373 = f.my_piecewise5(t14, 0, t10, 0, -t249)
  t376 = f.my_piecewise3(t147, 0, 0.4e1 / 0.3e1 * t148 * t373)
  t383 = t151 * t258 * t229 * t241 / 0.8e1
  t385 = f.my_piecewise3(t144, 0, -0.3e1 / 0.8e1 * t5 * t376 * t242 - t383)
  vrho_0_ = t143 + t245 + t6 * (t371 + t385)
  t388 = -t7 - t248
  t389 = f.my_piecewise5(t10, 0, t14, 0, t388)
  t392 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t389)
  t397 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t392 * t140 - t262)
  t399 = f.my_piecewise5(t14, 0, t10, 0, -t388)
  t402 = f.my_piecewise3(t147, 0, 0.4e1 / 0.3e1 * t148 * t399)
  t406 = t196 ** 2
  t408 = t263 / t406
  t411 = 0.1e1 / t154 / t152 / r1
  t412 = s2 * t411
  t423 = t161 ** 2
  t438 = t184 ** 2
  t440 = t180 / t438
  t444 = -(-0.5e1 / 0.3e1 * tau1 * t156 + t412 / 0.3e1) * t185 - t440 * t181 * t411 / 0.3e1
  t448 = t65 * t189
  t458 = -t444
  t459 = f.my_piecewise3(t203, 0, t458)
  t474 = t220 ** 2
  t475 = 0.1e1 / t474
  t476 = f.my_piecewise3(t203, t458, 0)
  t480 = f.my_piecewise3(t202, -0.667e0 * t459 - 0.8891110e0 * t204 * t459 - 0.1989259803147e1 * t206 * t459 + 0.5805188177960e1 * t208 * t459 - 0.4439990207985e1 * t210 * t459 + 0.1407173648874e1 * t212 * t459 - 0.162300903254e0 * t214 * t459, -t336 * t475 * t476 * t223)
  t490 = t355 * t150 * t27 * t229
  t494 = 0.1e1 / t236 / t235 * t45 * t127
  t503 = f.my_piecewise3(t144, 0, -0.3e1 / 0.8e1 * t5 * t402 * t242 - t383 - 0.3e1 / 0.8e1 * t151 * t27 * (t408 * (-0.10e2 / 0.729e3 * t33 * t412 - t49 * t160 / t153 / t161 / t152 * t170 / 0.108e3 + 0.3e1 / 0.320e3 * t283 * t160 * s2 / t423 / r1 * t170 + 0.2e1 * t194 * (-0.7e1 / 0.4860e4 * t66 * t166 * t411 + t65 * t444 * t191 / 0.100e3 - t448 * t444 * t191 / 0.100e3)) * t226 - t201 * t480 + 0.1174e1 * t480) * t241 - 0.24739500000000000000000000000000000000000000000000e1 * t490 * t494 * t231 / t153 / t152 * t240)
  vrho_1_ = t143 + t245 + t6 * (t397 + t503)
  t524 = t302 * params.eta * t38 / 0.8e1 + t38 * t80 / 0.8e1
  t537 = -t524
  t538 = f.my_piecewise3(t98, 0, t537)
  t553 = f.my_piecewise3(t98, t537, 0)
  t557 = f.my_piecewise3(t97, -0.667e0 * t538 - 0.8891110e0 * t99 * t538 - 0.1989259803147e1 * t101 * t538 + 0.5805188177960e1 * t103 * t538 - 0.4439990207985e1 * t105 * t538 + 0.1407173648874e1 * t107 * t538 - 0.162300903254e0 * t109 * t538, -t336 * t338 * t553 * t118)
  t572 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (t266 * (0.5e1 / 0.972e3 * t33 * t38 + t49 * s0 * t54 * t61 / 0.288e3 - 0.9e1 / 0.2560e4 * t283 * t50 / t285 * t61 + 0.2e1 * t89 * (0.7e1 / 0.12960e5 * t66 * t32 * t38 + t65 * t524 * t86 / 0.100e3 - t310 * t524 * t86 / 0.100e3)) * t121 - t96 * t557 + 0.1174e1 * t557) * t139 + 0.92773125000000000000000000000000000000000000000000e0 * t358 * t362 / t129 * t131 * t138)
  vsigma_0_ = t6 * t572
  vsigma_1_ = 0.0e0
  t591 = t440 * params.eta * t156 / 0.8e1 + t156 * t185 / 0.8e1
  t604 = -t591
  t605 = f.my_piecewise3(t203, 0, t604)
  t620 = f.my_piecewise3(t203, t604, 0)
  t624 = f.my_piecewise3(t202, -0.667e0 * t605 - 0.8891110e0 * t204 * t605 - 0.1989259803147e1 * t206 * t605 + 0.5805188177960e1 * t208 * t605 - 0.4439990207985e1 * t210 * t605 + 0.1407173648874e1 * t212 * t605 - 0.162300903254e0 * t214 * t605, -t336 * t475 * t620 * t223)
  t639 = f.my_piecewise3(t144, 0, -0.3e1 / 0.8e1 * t151 * t27 * (t408 * (0.5e1 / 0.972e3 * t33 * t156 + t49 * s2 * t164 * t170 / 0.288e3 - 0.9e1 / 0.2560e4 * t283 * t160 / t423 * t170 + 0.2e1 * t194 * (0.7e1 / 0.12960e5 * t66 * t32 * t156 + t65 * t591 * t191 / 0.100e3 - t448 * t591 * t191 / 0.100e3)) * t226 - t201 * t624 + 0.1174e1 * t624) * t241 + 0.92773125000000000000000000000000000000000000000000e0 * t490 * t494 / t231 * t233 * t240)
  vsigma_2_ = t6 * t639
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t643 = t70 * t80
  t652 = f.my_piecewise3(t98, 0, t643)
  t667 = f.my_piecewise3(t98, t643, 0)
  t671 = f.my_piecewise3(t97, -0.667e0 * t652 - 0.8891110e0 * t99 * t652 - 0.1989259803147e1 * t101 * t652 + 0.5805188177960e1 * t103 * t652 - 0.4439990207985e1 * t105 * t652 + 0.1407173648874e1 * t107 * t652 - 0.162300903254e0 * t109 * t652, -t336 * t338 * t667 * t118)
  t679 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (0.2e1 * t266 * t89 * (-t65 * t70 * t80 * t86 / 0.100e3 + t310 * t643 * t86 / 0.100e3) * t121 - t96 * t671 + 0.1174e1 * t671) * t139)
  vtau_0_ = t6 * t679
  t683 = t177 * t185
  t692 = f.my_piecewise3(t203, 0, t683)
  t707 = f.my_piecewise3(t203, t683, 0)
  t711 = f.my_piecewise3(t202, -0.667e0 * t692 - 0.8891110e0 * t204 * t692 - 0.1989259803147e1 * t206 * t692 + 0.5805188177960e1 * t208 * t692 - 0.4439990207985e1 * t210 * t692 + 0.1407173648874e1 * t212 * t692 - 0.162300903254e0 * t214 * t692, -t336 * t475 * t707 * t223)
  t719 = f.my_piecewise3(t144, 0, -0.3e1 / 0.8e1 * t151 * t27 * (0.2e1 * t408 * t194 * (-t65 * t177 * t185 * t191 / 0.100e3 + t448 * t683 * t191 / 0.100e3) * t226 - t201 * t711 + 0.1174e1 * t711) * t241)
  vtau_1_ = t6 * t719
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

  params_c1 = 0.667
  params_dp2 = 0.361

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

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  r2scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx)))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r2scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t20 = 6 ** (0.1e1 / 0.3e1)
  t21 = jnp.pi ** 2
  t22 = t21 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = 0.1e1 / t23
  t25 = t20 * t24
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = s0 * t27
  t29 = r0 ** 2
  t30 = t19 ** 2
  t32 = 0.1e1 / t30 / t29
  t33 = t28 * t32
  t38 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t39 = t20 ** 2
  t43 = t38 * t39 / t22 / t21
  t44 = s0 ** 2
  t45 = t44 * t26
  t46 = t29 ** 2
  t54 = jnp.exp(-0.27e2 / 0.80e2 * t38 * t20 * t24 * t33)
  t55 = 0.1e1 / t19 / t46 / r0 * t54
  t59 = jnp.sqrt(0.146e3)
  t60 = t59 * t20
  t61 = t60 * t24
  t64 = tau0 * t27
  t66 = 0.1e1 / t30 / r0
  t69 = t64 * t66 - t33 / 0.8e1
  t73 = t27 * t32
  t76 = 0.3e1 / 0.10e2 * t39 * t23 + params.eta * s0 * t73 / 0.8e1
  t77 = 0.1e1 / t76
  t78 = t69 * t77
  t79 = 0.1e1 - t78
  t81 = t79 ** 2
  t83 = jnp.exp(-t81 / 0.2e1)
  t86 = 0.7e1 / 0.12960e5 * t61 * t33 + t59 * t79 * t83 / 0.100e3
  t87 = t86 ** 2
  t88 = params.k1 + 0.5e1 / 0.972e3 * t25 * t33 + t43 * t45 * t55 / 0.288e3 + t87
  t93 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t88)
  t94 = t78 <= 0.25e1
  t95 = 0.25e1 < t78
  t96 = f.my_piecewise3(t95, 0.25e1, t78)
  t98 = t96 ** 2
  t100 = t98 * t96
  t102 = t98 ** 2
  t104 = t102 * t96
  t106 = t102 * t98
  t111 = f.my_piecewise3(t95, t78, 0.25e1)
  t112 = 0.1e1 - t111
  t115 = jnp.exp(params.c2 / t112)
  t117 = f.my_piecewise3(t94, 0.1e1 - 0.667e0 * t96 - 0.4445555e0 * t98 - 0.663086601049e0 * t100 + 0.1451297044490e1 * t102 - 0.887998041597e0 * t104 + 0.234528941479e0 * t106 - 0.23185843322e-1 * t102 * t100, -params.d * t115)
  t118 = 0.1e1 - t117
  t121 = t93 * t118 + 0.1174e1 * t117
  t123 = jnp.sqrt(0.3e1)
  t124 = 0.1e1 / t22
  t126 = jnp.sqrt(s0)
  t127 = t126 * t26
  t131 = t39 * t124 * t127 / t19 / r0
  t132 = jnp.sqrt(t131)
  t136 = jnp.exp(-0.98958e1 * t123 / t132)
  t137 = 0.1e1 - t136
  t141 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t121 * t137)
  t147 = params.k1 ** 2
  t148 = t88 ** 2
  t150 = t147 / t148
  t154 = t28 / t30 / t29 / r0
  t164 = t38 ** 2
  t165 = t21 ** 2
  t167 = t164 / t165
  t169 = t46 ** 2
  t183 = t76 ** 2
  t185 = t69 / t183
  t189 = -(-0.5e1 / 0.3e1 * t64 * t32 + t154 / 0.3e1) * t77 - t185 * params.eta * t154 / 0.3e1
  t193 = t59 * t81
  t203 = -t189
  t204 = f.my_piecewise3(t95, 0, t203)
  t219 = params.d * params.c2
  t220 = t112 ** 2
  t221 = 0.1e1 / t220
  t222 = f.my_piecewise3(t95, t203, 0)
  t226 = f.my_piecewise3(t94, -0.667e0 * t204 - 0.8891110e0 * t96 * t204 - 0.1989259803147e1 * t98 * t204 + 0.5805188177960e1 * t100 * t204 - 0.4439990207985e1 * t102 * t204 + 0.1407173648874e1 * t104 * t204 - 0.162300903254e0 * t106 * t204, -t219 * t221 * t222 * t115)
  t234 = 3 ** (0.1e1 / 0.6e1)
  t235 = t234 ** 2
  t236 = t235 ** 2
  t238 = t236 * t234 * t5
  t246 = 0.1e1 / t132 / t131 * t39 * t124
  t252 = f.my_piecewise3(t2, 0, -t18 / t30 * t121 * t137 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (t150 * (-0.10e2 / 0.729e3 * t25 * t154 - t43 * t45 / t19 / t46 / t29 * t54 / 0.54e2 + 0.3e1 / 0.80e2 * t167 * t44 * s0 / t169 / r0 * t54 + 0.2e1 * t86 * (-0.7e1 / 0.4860e4 * t61 * t154 + t59 * t189 * t83 / 0.100e3 - t193 * t189 * t83 / 0.100e3)) * t118 - t93 * t226 + 0.1174e1 * t226) * t137 - 0.24739500000000000000000000000000000000000000000000e1 * t238 * t17 / t29 * t121 * t246 * t127 * t136)
  vrho_0_ = 0.2e1 * r0 * t252 + 0.2e1 * t141
  t275 = t185 * params.eta * t27 * t32 / 0.8e1 + t73 * t77 / 0.8e1
  t288 = -t275
  t289 = f.my_piecewise3(t95, 0, t288)
  t304 = f.my_piecewise3(t95, t288, 0)
  t308 = f.my_piecewise3(t94, -0.667e0 * t289 - 0.8891110e0 * t96 * t289 - 0.1989259803147e1 * t98 * t289 + 0.5805188177960e1 * t100 * t289 - 0.4439990207985e1 * t102 * t289 + 0.1407173648874e1 * t104 * t289 - 0.162300903254e0 * t106 * t289, -t219 * t221 * t304 * t115)
  t327 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (t150 * (0.5e1 / 0.972e3 * t25 * t73 + t43 * s0 * t26 * t55 / 0.144e3 - 0.9e1 / 0.640e3 * t167 * t44 / t169 * t54 + 0.2e1 * t86 * (0.7e1 / 0.12960e5 * t60 * t24 * t27 * t32 + t59 * t275 * t83 / 0.100e3 - t193 * t275 * t83 / 0.100e3)) * t118 - t93 * t308 + 0.1174e1 * t308) * t137 + 0.92773125000000000000000000000000000000000000000000e0 * t238 * t17 / r0 * t121 * t246 / t126 * t26 * t136)
  vsigma_0_ = 0.2e1 * r0 * t327
  vlapl_0_ = 0.0e0
  t331 = t66 * t77 * t83
  t342 = t27 * t66 * t77
  t343 = f.my_piecewise3(t95, 0, t342)
  t358 = f.my_piecewise3(t95, t342, 0)
  t362 = f.my_piecewise3(t94, -0.667e0 * t343 - 0.8891110e0 * t96 * t343 - 0.1989259803147e1 * t98 * t343 + 0.5805188177960e1 * t100 * t343 - 0.4439990207985e1 * t102 * t343 + 0.1407173648874e1 * t104 * t343 - 0.162300903254e0 * t106 * t343, -t219 * t221 * t358 * t115)
  t370 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (0.2e1 * t150 * t86 * (t193 * t27 * t331 / 0.100e3 - t59 * t27 * t331 / 0.100e3) * t118 - t93 * t362 + 0.1174e1 * t362) * t137)
  vtau_0_ = 0.2e1 * r0 * t370
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
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = jnp.pi ** 2
  t24 = t23 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = 0.1e1 / t25
  t27 = t22 * t26
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = s0 * t29
  t31 = r0 ** 2
  t33 = 0.1e1 / t20 / t31
  t34 = t30 * t33
  t35 = t27 * t34
  t39 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t40 = t22 ** 2
  t44 = t39 * t40 / t24 / t23
  t45 = s0 ** 2
  t46 = t45 * t28
  t47 = t31 ** 2
  t55 = jnp.exp(-0.27e2 / 0.80e2 * t39 * t22 * t26 * t34)
  t60 = jnp.sqrt(0.146e3)
  t62 = t60 * t22 * t26
  t65 = tau0 * t29
  t67 = 0.1e1 / t20 / r0
  t70 = t65 * t67 - t34 / 0.8e1
  t77 = 0.3e1 / 0.10e2 * t40 * t25 + params.eta * s0 * t29 * t33 / 0.8e1
  t78 = 0.1e1 / t77
  t79 = t70 * t78
  t80 = 0.1e1 - t79
  t82 = t80 ** 2
  t84 = jnp.exp(-t82 / 0.2e1)
  t87 = 0.7e1 / 0.12960e5 * t62 * t34 + t60 * t80 * t84 / 0.100e3
  t88 = t87 ** 2
  t89 = params.k1 + 0.5e1 / 0.972e3 * t35 + t44 * t46 / t19 / t47 / r0 * t55 / 0.288e3 + t88
  t94 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t89)
  t95 = t79 <= 0.25e1
  t96 = 0.25e1 < t79
  t97 = f.my_piecewise3(t96, 0.25e1, t79)
  t99 = t97 ** 2
  t101 = t99 * t97
  t103 = t99 ** 2
  t105 = t103 * t97
  t107 = t103 * t99
  t112 = f.my_piecewise3(t96, t79, 0.25e1)
  t113 = 0.1e1 - t112
  t116 = jnp.exp(params.c2 / t113)
  t118 = f.my_piecewise3(t95, 0.1e1 - 0.667e0 * t97 - 0.4445555e0 * t99 - 0.663086601049e0 * t101 + 0.1451297044490e1 * t103 - 0.887998041597e0 * t105 + 0.234528941479e0 * t107 - 0.23185843322e-1 * t103 * t101, -params.d * t116)
  t119 = 0.1e1 - t118
  t122 = t94 * t119 + 0.1174e1 * t118
  t124 = jnp.sqrt(0.3e1)
  t125 = 0.1e1 / t24
  t127 = jnp.sqrt(s0)
  t128 = t127 * t28
  t132 = t40 * t125 * t128 / t19 / r0
  t133 = jnp.sqrt(t132)
  t137 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t124 / t133)
  t138 = 0.1e1 - t137
  t142 = params.k1 ** 2
  t143 = t89 ** 2
  t145 = t142 / t143
  t146 = t31 * r0
  t148 = 0.1e1 / t20 / t146
  t149 = t30 * t148
  t159 = t39 ** 2
  t160 = t23 ** 2
  t161 = 0.1e1 / t160
  t162 = t159 * t161
  t163 = t45 * s0
  t164 = t47 ** 2
  t176 = -0.5e1 / 0.3e1 * t65 * t33 + t149 / 0.3e1
  t178 = t77 ** 2
  t179 = 0.1e1 / t178
  t181 = t70 * t179 * params.eta
  t184 = -t176 * t78 - t181 * t149 / 0.3e1
  t188 = t60 * t82
  t192 = -0.7e1 / 0.4860e4 * t62 * t149 + t60 * t184 * t84 / 0.100e3 - t188 * t184 * t84 / 0.100e3
  t195 = -0.10e2 / 0.729e3 * t27 * t149 - t44 * t46 / t19 / t47 / t31 * t55 / 0.54e2 + 0.3e1 / 0.80e2 * t162 * t163 / t164 / r0 * t55 + 0.2e1 * t87 * t192
  t198 = -t184
  t199 = f.my_piecewise3(t96, 0, t198)
  t214 = params.d * params.c2
  t215 = t113 ** 2
  t216 = 0.1e1 / t215
  t217 = f.my_piecewise3(t96, t198, 0)
  t221 = f.my_piecewise3(t95, -0.667e0 * t199 - 0.8891110e0 * t97 * t199 - 0.1989259803147e1 * t99 * t199 + 0.5805188177960e1 * t101 * t199 - 0.4439990207985e1 * t103 * t199 + 0.1407173648874e1 * t105 * t199 - 0.162300903254e0 * t107 * t199, -t214 * t216 * t217 * t116)
  t224 = t145 * t195 * t119 - t94 * t221 + 0.1174e1 * t221
  t229 = 3 ** (0.1e1 / 0.6e1)
  t230 = t229 ** 2
  t231 = t230 ** 2
  t233 = t231 * t229 * t5
  t235 = t17 / t31
  t243 = 0.1e1 / t133 / t132 * t40 * t125 * t128 * t137
  t247 = f.my_piecewise3(t2, 0, -t18 * t21 * t122 * t138 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t224 * t138 - 0.24739500000000000000000000000000000000000000000000e1 * t233 * t235 * t122 * t243)
  t266 = t195 ** 2
  t272 = t30 / t20 / t47
  t277 = 0.1e1 / t19 / t47 / t146
  t290 = t45 ** 2
  t300 = t192 ** 2
  t316 = params.eta ** 2
  t323 = -(0.40e2 / 0.9e1 * t65 * t148 - 0.11e2 / 0.9e1 * t272) * t78 - 0.2e1 / 0.3e1 * t176 * t179 * params.eta * t149 - 0.4e1 / 0.9e1 * t70 / t178 / t77 * t316 * t46 * t277 + 0.11e2 / 0.9e1 * t181 * t272
  t327 = t184 ** 2
  t349 = -t323
  t350 = f.my_piecewise3(t96, 0, t349)
  t352 = t199 ** 2
  t376 = -0.667e0 * t350 - 0.8891110e0 * t352 - 0.8891110e0 * t97 * t350 - 0.3978519606294e1 * t97 * t352 - 0.1989259803147e1 * t99 * t350 + 0.17415564533880e2 * t99 * t352 + 0.5805188177960e1 * t101 * t350 - 0.17759960831940e2 * t101 * t352 - 0.4439990207985e1 * t103 * t350 + 0.7035868244370e1 * t103 * t352 + 0.1407173648874e1 * t105 * t350 - 0.973805419524e0 * t105 * t352 - 0.162300903254e0 * t107 * t350
  t379 = t217 ** 2
  t384 = f.my_piecewise3(t96, t349, 0)
  t388 = params.c2 ** 2
  t390 = t215 ** 2
  t396 = f.my_piecewise3(t95, t376, -0.2e1 * t214 / t215 / t113 * t379 * t116 - t214 * t216 * t384 * t116 - params.d * t388 / t390 * t379 * t116)
  t422 = t4 ** 2
  t437 = f.my_piecewise3(t2, 0, t18 * t67 * t122 * t138 / 0.12e2 - t18 * t21 * t224 * t138 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t233 * t17 / t146 * t122 * t243 - 0.3e1 / 0.8e1 * t18 * t19 * (-0.2e1 * t142 / t143 / t89 * t266 * t119 + t145 * (0.110e3 / 0.2187e4 * t27 * t272 + 0.19e2 / 0.162e3 * t44 * t46 * t277 * t55 - 0.43e2 / 0.80e2 * t162 * t163 / t164 / t31 * t55 + 0.27e2 / 0.800e3 * t159 * t39 * t161 * t290 / t20 / t164 / t47 * t27 * t29 * t55 + 0.2e1 * t300 + 0.2e1 * t87 * (0.77e2 / 0.14580e5 * t62 * t272 + t60 * t323 * t84 / 0.100e3 - 0.3e1 / 0.100e3 * t60 * t327 * t80 * t84 - t188 * t323 * t84 / 0.100e3 + t60 * t82 * t80 * t327 * t84 / 0.100e3)) * t119 - 0.2e1 * t145 * t195 * t221 - t94 * t396 + 0.1174e1 * t396) * t138 - 0.49479000000000000000000000000000000000000000000000e1 * t233 * t235 * t224 * t243 - 0.49479000000000000000000000000000000000000000000000e1 * t233 * t17 / t19 / t47 * t122 / t133 / t35 * t22 * t26 * t30 * t137 + 0.40802857350000000000000000000000000000000000000000e1 * t3 * t422 * jnp.pi * t17 / t19 * t122 / t127 * t22 * t26 * t29 * t137)
  v2rho2_0_ = 0.2e1 * r0 * t437 + 0.4e1 * t247

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
  t23 = 6 ** (0.1e1 / 0.3e1)
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = t23 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t20 / t32
  t35 = t31 * t34
  t36 = t28 * t35
  t40 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t41 = t23 ** 2
  t43 = t25 * t24
  t44 = 0.1e1 / t43
  t45 = t40 * t41 * t44
  t46 = s0 ** 2
  t47 = t46 * t29
  t48 = t32 ** 2
  t49 = t48 * r0
  t51 = 0.1e1 / t19 / t49
  t56 = jnp.exp(-0.27e2 / 0.80e2 * t40 * t23 * t27 * t35)
  t61 = jnp.sqrt(0.146e3)
  t63 = t61 * t23 * t27
  t66 = tau0 * t30
  t69 = t66 * t22 - t35 / 0.8e1
  t76 = 0.3e1 / 0.10e2 * t41 * t26 + params.eta * s0 * t30 * t34 / 0.8e1
  t77 = 0.1e1 / t76
  t78 = t69 * t77
  t79 = 0.1e1 - t78
  t81 = t79 ** 2
  t83 = jnp.exp(-t81 / 0.2e1)
  t86 = 0.7e1 / 0.12960e5 * t63 * t35 + t61 * t79 * t83 / 0.100e3
  t87 = t86 ** 2
  t88 = params.k1 + 0.5e1 / 0.972e3 * t36 + t45 * t47 * t51 * t56 / 0.288e3 + t87
  t93 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t88)
  t94 = t78 <= 0.25e1
  t95 = 0.25e1 < t78
  t96 = f.my_piecewise3(t95, 0.25e1, t78)
  t98 = t96 ** 2
  t100 = t98 * t96
  t102 = t98 ** 2
  t104 = t102 * t96
  t106 = t102 * t98
  t111 = f.my_piecewise3(t95, t78, 0.25e1)
  t112 = 0.1e1 - t111
  t115 = jnp.exp(params.c2 / t112)
  t117 = f.my_piecewise3(t94, 0.1e1 - 0.667e0 * t96 - 0.4445555e0 * t98 - 0.663086601049e0 * t100 + 0.1451297044490e1 * t102 - 0.887998041597e0 * t104 + 0.234528941479e0 * t106 - 0.23185843322e-1 * t102 * t100, -params.d * t115)
  t118 = 0.1e1 - t117
  t121 = t93 * t118 + 0.1174e1 * t117
  t123 = jnp.sqrt(0.3e1)
  t124 = 0.1e1 / t25
  t126 = jnp.sqrt(s0)
  t127 = t126 * t29
  t129 = 0.1e1 / t19 / r0
  t131 = t41 * t124 * t127 * t129
  t132 = jnp.sqrt(t131)
  t136 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t123 / t132)
  t137 = 0.1e1 - t136
  t141 = 0.1e1 / t20
  t142 = params.k1 ** 2
  t143 = t88 ** 2
  t145 = t142 / t143
  t146 = t32 * r0
  t148 = 0.1e1 / t20 / t146
  t149 = t31 * t148
  t152 = t48 * t32
  t159 = t40 ** 2
  t160 = t24 ** 2
  t161 = 0.1e1 / t160
  t162 = t159 * t161
  t163 = t46 * s0
  t164 = t48 ** 2
  t176 = -0.5e1 / 0.3e1 * t66 * t34 + t149 / 0.3e1
  t178 = t76 ** 2
  t179 = 0.1e1 / t178
  t181 = t69 * t179 * params.eta
  t184 = -t176 * t77 - t181 * t149 / 0.3e1
  t188 = t61 * t81
  t192 = -0.7e1 / 0.4860e4 * t63 * t149 + t61 * t184 * t83 / 0.100e3 - t188 * t184 * t83 / 0.100e3
  t195 = -0.10e2 / 0.729e3 * t28 * t149 - t45 * t47 / t19 / t152 * t56 / 0.54e2 + 0.3e1 / 0.80e2 * t162 * t163 / t164 / r0 * t56 + 0.2e1 * t86 * t192
  t196 = t195 * t118
  t198 = -t184
  t199 = f.my_piecewise3(t95, 0, t198)
  t201 = t96 * t199
  t203 = t98 * t199
  t205 = t100 * t199
  t207 = t102 * t199
  t209 = t104 * t199
  t214 = params.d * params.c2
  t215 = t112 ** 2
  t216 = 0.1e1 / t215
  t217 = f.my_piecewise3(t95, t198, 0)
  t221 = f.my_piecewise3(t94, -0.667e0 * t199 - 0.8891110e0 * t201 - 0.1989259803147e1 * t203 + 0.5805188177960e1 * t205 - 0.4439990207985e1 * t207 + 0.1407173648874e1 * t209 - 0.162300903254e0 * t106 * t199, -t214 * t216 * t217 * t115)
  t224 = t145 * t196 - t93 * t221 + 0.1174e1 * t221
  t229 = 3 ** (0.1e1 / 0.6e1)
  t230 = t229 ** 2
  t231 = t230 ** 2
  t232 = t231 * t229
  t233 = t232 * t5
  t235 = t17 / t146
  t239 = 0.1e1 / t132 / t131
  t243 = t239 * t41 * t124 * t127 * t136
  t248 = t142 / t143 / t88
  t249 = t195 ** 2
  t254 = 0.1e1 / t20 / t48
  t255 = t31 * t254
  t260 = 0.1e1 / t19 / t48 / t146
  t272 = t159 * t40 * t161
  t273 = t46 ** 2
  t280 = t28 * t30 * t56
  t283 = t192 ** 2
  t290 = 0.40e2 / 0.9e1 * t66 * t148 - 0.11e2 / 0.9e1 * t255
  t293 = t176 * t179 * params.eta
  t297 = 0.1e1 / t178 / t76
  t299 = params.eta ** 2
  t300 = t69 * t297 * t299
  t301 = t47 * t260
  t306 = -t290 * t77 - 0.2e1 / 0.3e1 * t293 * t149 - 0.4e1 / 0.9e1 * t300 * t301 + 0.11e2 / 0.9e1 * t181 * t255
  t307 = t61 * t306
  t310 = t184 ** 2
  t319 = t61 * t81 * t79
  t323 = 0.77e2 / 0.14580e5 * t63 * t255 + t307 * t83 / 0.100e3 - 0.3e1 / 0.100e3 * t61 * t310 * t79 * t83 - t188 * t306 * t83 / 0.100e3 + t319 * t310 * t83 / 0.100e3
  t326 = 0.110e3 / 0.2187e4 * t28 * t255 + 0.19e2 / 0.162e3 * t45 * t47 * t260 * t56 - 0.43e2 / 0.80e2 * t162 * t163 / t164 / t32 * t56 + 0.27e2 / 0.800e3 * t272 * t273 / t20 / t164 / t48 * t280 + 0.2e1 * t283 + 0.2e1 * t86 * t323
  t332 = -t306
  t333 = f.my_piecewise3(t95, 0, t332)
  t335 = t199 ** 2
  t359 = -0.667e0 * t333 - 0.8891110e0 * t335 - 0.8891110e0 * t96 * t333 - 0.3978519606294e1 * t96 * t335 - 0.1989259803147e1 * t98 * t333 + 0.17415564533880e2 * t98 * t335 + 0.5805188177960e1 * t100 * t333 - 0.17759960831940e2 * t100 * t335 - 0.4439990207985e1 * t102 * t333 + 0.7035868244370e1 * t102 * t335 + 0.1407173648874e1 * t104 * t333 - 0.973805419524e0 * t104 * t335 - 0.162300903254e0 * t106 * t333
  t361 = 0.1e1 / t215 / t112
  t362 = t217 ** 2
  t367 = f.my_piecewise3(t95, t332, 0)
  t371 = params.c2 ** 2
  t372 = params.d * t371
  t373 = t215 ** 2
  t374 = 0.1e1 / t373
  t379 = f.my_piecewise3(t94, t359, -t214 * t216 * t367 * t115 - 0.2e1 * t214 * t361 * t362 * t115 - t372 * t374 * t362 * t115)
  t382 = -0.2e1 * t248 * t249 * t118 + t145 * t326 * t118 - 0.2e1 * t145 * t195 * t221 - t93 * t379 + 0.1174e1 * t379
  t388 = t17 / t32
  t395 = t17 / t19 / t48
  t404 = 0.1e1 / t132 / t36 * t23 * t27 * t31 * t136 / 0.6e1
  t407 = t4 ** 2
  t409 = t3 * t407 * jnp.pi
  t411 = t17 / t19
  t414 = 0.1e1 / t126
  t418 = t414 * t23 * t27 * t30 * t136
  t422 = f.my_piecewise3(t2, 0, t18 * t22 * t121 * t137 / 0.12e2 - t18 * t141 * t224 * t137 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t233 * t235 * t121 * t243 - 0.3e1 / 0.8e1 * t18 * t19 * t382 * t137 - 0.49479000000000000000000000000000000000000000000000e1 * t233 * t388 * t224 * t243 - 0.29687400000000000000000000000000000000000000000000e2 * t233 * t395 * t121 * t404 + 0.40802857350000000000000000000000000000000000000000e1 * t409 * t411 * t121 * t418)
  t424 = t34 * t121
  t432 = 0.1e1 / t48
  t452 = t17 * t129 * t121
  t456 = t143 ** 2
  t471 = t31 / t20 / t49
  t475 = 0.1e1 / t19 / t164
  t481 = 0.1e1 / t164 / t146
  t493 = t159 ** 2
  t496 = t164 ** 2
  t524 = t178 ** 2
  t537 = -(-0.440e3 / 0.27e2 * t66 * t254 + 0.154e3 / 0.27e2 * t471) * t77 - t290 * t179 * params.eta * t149 - 0.4e1 / 0.3e1 * t176 * t297 * t299 * t301 + 0.11e2 / 0.3e1 * t293 * t255 - 0.8e1 / 0.9e1 * t69 / t524 * t299 * params.eta * t163 * t481 + 0.44e2 / 0.9e1 * t300 * t47 * t475 - 0.154e3 / 0.27e2 * t181 * t471
  t545 = t310 * t184
  t546 = t61 * t545
  t559 = t81 ** 2
  t576 = -t537
  t577 = f.my_piecewise3(t95, 0, t576)
  t583 = t335 * t199
  t613 = -0.667e0 * t577 - 0.26673330e1 * t199 * t333 - 0.8891110e0 * t96 * t577 - 0.3978519606294e1 * t583 - 0.11935558818882e2 * t201 * t333 - 0.1989259803147e1 * t98 * t577 + 0.34831129067760e2 * t96 * t583 + 0.52246693601640e2 * t203 * t333 + 0.5805188177960e1 * t100 * t577 - 0.53279882495820e2 * t98 * t583 - 0.53279882495820e2 * t205 * t333 - 0.4439990207985e1 * t102 * t577 + 0.28143472977480e2 * t100 * t583 + 0.21107604733110e2 * t207 * t333 + 0.1407173648874e1 * t104 * t577 - 0.4869027097620e1 * t102 * t583 - 0.2921416258572e1 * t209 * t333 - 0.162300903254e0 * t106 * t577
  t614 = t362 * t217
  t621 = t217 * t115 * t367
  t630 = f.my_piecewise3(t95, t576, 0)
  t645 = f.my_piecewise3(t94, t613, -0.6e1 * t214 * t374 * t614 * t115 - 0.6e1 * t214 * t361 * t621 - 0.6e1 * t372 / t373 / t112 * t614 * t115 - t214 * t216 * t630 * t115 - 0.3e1 * t372 * t374 * t621 - params.d * t371 * params.c2 / t373 / t215 * t614 * t115)
  t666 = 0.1e1 / t4 / t24
  t673 = t126 * s0
  t697 = -0.5e1 / 0.36e2 * t18 * t424 * t137 + t18 * t22 * t224 * t137 / 0.4e1 - 0.11819983333333333333333333333333333333333333333333e2 * t233 * t17 * t432 * t121 * t243 - 0.3e1 / 0.8e1 * t18 * t141 * t382 * t137 + 0.12369750000000000000000000000000000000000000000000e2 * t233 * t235 * t224 * t243 + 0.17812440000000000000000000000000000000000000000000e3 * t233 * t17 * t51 * t121 * t404 - 0.81605714700000000000000000000000000000000000000000e1 * t409 * t452 * t418 - 0.3e1 / 0.8e1 * t18 * t19 * (0.6e1 * t142 / t456 * t249 * t195 * t118 - 0.6e1 * t248 * t196 * t326 + 0.6e1 * t248 * t249 * t221 + t145 * (-0.1540e4 / 0.6561e4 * t28 * t471 - 0.209e3 / 0.243e3 * t45 * t47 * t475 * t56 + 0.797e3 / 0.120e3 * t162 * t163 * t481 * t56 - 0.729e3 / 0.800e3 * t272 * t273 / t20 / t164 / t49 * t280 + 0.243e3 / 0.4000e4 * t493 * t161 * t273 * s0 / t19 / t496 * t41 * t44 * t29 * t56 + 0.6e1 * t192 * t323 + 0.2e1 * t86 * (-0.539e3 / 0.21870e5 * t63 * t471 + t61 * t537 * t83 / 0.100e3 - 0.9e1 / 0.100e3 * t307 * t79 * t184 * t83 - 0.3e1 / 0.100e3 * t546 * t83 + 0.3e1 / 0.50e2 * t546 * t81 * t83 - t188 * t537 * t83 / 0.100e3 + 0.3e1 / 0.100e3 * t319 * t306 * t184 * t83 - t61 * t559 * t545 * t83 / 0.100e3)) * t118 - 0.3e1 * t145 * t326 * t221 - 0.3e1 * t145 * t195 * t379 - t93 * t645 + 0.1174e1 * t645) * t137 - 0.74218500000000000000000000000000000000000000000000e1 * t233 * t388 * t382 * t243 - 0.89062200000000000000000000000000000000000000000000e2 * t233 * t395 * t224 * t404 + 0.12240857205000000000000000000000000000000000000000e2 * t409 * t411 * t224 * t418 - 0.16493000000000000000000000000000000000000000000000e2 * t232 * t666 * t17 / t20 / t152 * t121 / t132 * t24 / t432 * t136 + 0.81605714699999999999999999999999999999999999999999e1 * t3 * t666 * t452 * t23 * t43 * t414 * t30 * t136 - 0.32302153261130400000000000000000000000000000000000e3 * t233 * t17 * t424 * t239 * t136
  t698 = f.my_piecewise3(t2, 0, t697)
  v3rho3_0_ = 0.2e1 * r0 * t698 + 0.6e1 * t422

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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = t32 * t23
  t34 = t29 * t33
  t38 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t39 = t24 ** 2
  t41 = t26 * t25
  t42 = 0.1e1 / t41
  t43 = t38 * t39 * t42
  t44 = s0 ** 2
  t45 = t44 * t30
  t46 = t19 ** 2
  t47 = t46 * r0
  t49 = 0.1e1 / t20 / t47
  t54 = jnp.exp(-0.27e2 / 0.80e2 * t38 * t24 * t28 * t33)
  t59 = jnp.sqrt(0.146e3)
  t61 = t59 * t24 * t28
  t64 = tau0 * t31
  t66 = 0.1e1 / t21 / r0
  t69 = t64 * t66 - t33 / 0.8e1
  t76 = 0.3e1 / 0.10e2 * t39 * t27 + params.eta * s0 * t31 * t23 / 0.8e1
  t77 = 0.1e1 / t76
  t78 = t69 * t77
  t79 = 0.1e1 - t78
  t81 = t79 ** 2
  t83 = jnp.exp(-t81 / 0.2e1)
  t86 = 0.7e1 / 0.12960e5 * t61 * t33 + t59 * t79 * t83 / 0.100e3
  t87 = t86 ** 2
  t88 = params.k1 + 0.5e1 / 0.972e3 * t34 + t43 * t45 * t49 * t54 / 0.288e3 + t87
  t93 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t88)
  t94 = t78 <= 0.25e1
  t95 = 0.25e1 < t78
  t96 = f.my_piecewise3(t95, 0.25e1, t78)
  t98 = t96 ** 2
  t100 = t98 * t96
  t102 = t98 ** 2
  t104 = t102 * t96
  t106 = t102 * t98
  t111 = f.my_piecewise3(t95, t78, 0.25e1)
  t112 = 0.1e1 - t111
  t115 = jnp.exp(params.c2 / t112)
  t117 = f.my_piecewise3(t94, 0.1e1 - 0.667e0 * t96 - 0.4445555e0 * t98 - 0.663086601049e0 * t100 + 0.1451297044490e1 * t102 - 0.887998041597e0 * t104 + 0.234528941479e0 * t106 - 0.23185843322e-1 * t102 * t100, -params.d * t115)
  t118 = 0.1e1 - t117
  t121 = t93 * t118 + 0.1174e1 * t117
  t122 = t23 * t121
  t123 = jnp.sqrt(0.3e1)
  t124 = 0.1e1 / t26
  t125 = t39 * t124
  t126 = jnp.sqrt(s0)
  t127 = t126 * t30
  t129 = 0.1e1 / t20 / r0
  t131 = t125 * t127 * t129
  t132 = jnp.sqrt(t131)
  t136 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t123 / t132)
  t137 = 0.1e1 - t136
  t141 = params.k1 ** 2
  t142 = t88 ** 2
  t144 = t141 / t142
  t145 = t19 * r0
  t147 = 0.1e1 / t21 / t145
  t148 = t32 * t147
  t151 = t46 * t19
  t153 = 0.1e1 / t20 / t151
  t158 = t38 ** 2
  t159 = t25 ** 2
  t160 = 0.1e1 / t159
  t161 = t158 * t160
  t162 = t44 * s0
  t163 = t46 ** 2
  t164 = t163 * r0
  t165 = 0.1e1 / t164
  t175 = -0.5e1 / 0.3e1 * t64 * t23 + t148 / 0.3e1
  t177 = t76 ** 2
  t178 = 0.1e1 / t177
  t180 = t69 * t178 * params.eta
  t183 = -t175 * t77 - t180 * t148 / 0.3e1
  t187 = t59 * t81
  t191 = -0.7e1 / 0.4860e4 * t61 * t148 + t59 * t183 * t83 / 0.100e3 - t187 * t183 * t83 / 0.100e3
  t194 = -0.10e2 / 0.729e3 * t29 * t148 - t43 * t45 * t153 * t54 / 0.54e2 + 0.3e1 / 0.80e2 * t161 * t162 * t165 * t54 + 0.2e1 * t86 * t191
  t195 = t194 * t118
  t197 = -t183
  t198 = f.my_piecewise3(t95, 0, t197)
  t200 = t96 * t198
  t202 = t98 * t198
  t204 = t100 * t198
  t206 = t102 * t198
  t208 = t104 * t198
  t213 = params.d * params.c2
  t214 = t112 ** 2
  t215 = 0.1e1 / t214
  t216 = f.my_piecewise3(t95, t197, 0)
  t220 = f.my_piecewise3(t94, -0.667e0 * t198 - 0.8891110e0 * t200 - 0.1989259803147e1 * t202 + 0.5805188177960e1 * t204 - 0.4439990207985e1 * t206 + 0.1407173648874e1 * t208 - 0.162300903254e0 * t106 * t198, -t213 * t215 * t216 * t115)
  t223 = t144 * t195 - t93 * t220 + 0.1174e1 * t220
  t228 = 3 ** (0.1e1 / 0.6e1)
  t229 = t228 ** 2
  t230 = t229 ** 2
  t231 = t230 * t228
  t232 = t231 * t5
  t233 = 0.1e1 / t46
  t234 = t17 * t233
  t238 = 0.1e1 / t132 / t131
  t242 = t238 * t39 * t124 * t127 * t136
  t245 = 0.1e1 / t21
  t248 = t141 / t142 / t88
  t249 = t194 ** 2
  t250 = t249 * t118
  t254 = 0.1e1 / t21 / t46
  t255 = t32 * t254
  t258 = t46 * t145
  t260 = 0.1e1 / t20 / t258
  t272 = t158 * t38 * t160
  t273 = t44 ** 2
  t274 = t163 * t46
  t280 = t29 * t31 * t54
  t283 = t191 ** 2
  t290 = 0.40e2 / 0.9e1 * t64 * t147 - 0.11e2 / 0.9e1 * t255
  t293 = t175 * t178 * params.eta
  t297 = 0.1e1 / t177 / t76
  t299 = params.eta ** 2
  t300 = t69 * t297 * t299
  t301 = t45 * t260
  t306 = -t290 * t77 - 0.2e1 / 0.3e1 * t293 * t148 - 0.4e1 / 0.9e1 * t300 * t301 + 0.11e2 / 0.9e1 * t180 * t255
  t307 = t59 * t306
  t310 = t183 ** 2
  t312 = t79 * t83
  t318 = t81 * t79
  t319 = t59 * t318
  t320 = t310 * t83
  t323 = 0.77e2 / 0.14580e5 * t61 * t255 + t307 * t83 / 0.100e3 - 0.3e1 / 0.100e3 * t59 * t310 * t312 - t187 * t306 * t83 / 0.100e3 + t319 * t320 / 0.100e3
  t326 = 0.110e3 / 0.2187e4 * t29 * t255 + 0.19e2 / 0.162e3 * t43 * t45 * t260 * t54 - 0.43e2 / 0.80e2 * t161 * t162 / t163 / t19 * t54 + 0.27e2 / 0.800e3 * t272 * t273 / t21 / t274 * t280 + 0.2e1 * t283 + 0.2e1 * t86 * t323
  t329 = t194 * t220
  t332 = -t306
  t333 = f.my_piecewise3(t95, 0, t332)
  t335 = t198 ** 2
  t339 = t96 * t335
  t343 = t98 * t335
  t347 = t100 * t335
  t351 = t102 * t335
  t359 = -0.667e0 * t333 - 0.8891110e0 * t335 - 0.8891110e0 * t96 * t333 - 0.3978519606294e1 * t339 - 0.1989259803147e1 * t98 * t333 + 0.17415564533880e2 * t343 + 0.5805188177960e1 * t100 * t333 - 0.17759960831940e2 * t347 - 0.4439990207985e1 * t102 * t333 + 0.7035868244370e1 * t351 + 0.1407173648874e1 * t104 * t333 - 0.973805419524e0 * t104 * t335 - 0.162300903254e0 * t106 * t333
  t360 = t214 * t112
  t361 = 0.1e1 / t360
  t362 = t216 ** 2
  t367 = f.my_piecewise3(t95, t332, 0)
  t371 = params.c2 ** 2
  t372 = params.d * t371
  t373 = t214 ** 2
  t374 = 0.1e1 / t373
  t379 = f.my_piecewise3(t94, t359, -t213 * t215 * t367 * t115 - 0.2e1 * t213 * t361 * t362 * t115 - t372 * t374 * t362 * t115)
  t382 = -0.2e1 * t248 * t250 + t144 * t326 * t118 - 0.2e1 * t144 * t329 - t93 * t379 + 0.1174e1 * t379
  t388 = t17 / t145
  t393 = t17 * t49
  t398 = 0.1e1 / t132 / t34 / 0.6e1
  t402 = t398 * t24 * t28 * t32 * t136
  t405 = t4 ** 2
  t407 = t3 * t405 * jnp.pi
  t408 = t17 * t129
  t409 = t408 * t121
  t411 = 0.1e1 / t126
  t415 = t411 * t24 * t28 * t31 * t136
  t418 = t142 ** 2
  t420 = t141 / t418
  t421 = t249 * t194
  t432 = 0.1e1 / t21 / t47
  t433 = t32 * t432
  t437 = 0.1e1 / t20 / t163
  t443 = 0.1e1 / t163 / t145
  t455 = t158 ** 2
  t456 = t455 * t160
  t457 = t273 * s0
  t458 = t163 ** 2
  t463 = t39 * t42
  t465 = t463 * t30 * t54
  t475 = -0.440e3 / 0.27e2 * t64 * t254 + 0.154e3 / 0.27e2 * t433
  t478 = t290 * t178 * params.eta
  t481 = t175 * t297 * t299
  t486 = t177 ** 2
  t487 = 0.1e1 / t486
  t488 = t69 * t487
  t490 = t299 * params.eta * t162
  t491 = t490 * t443
  t494 = t45 * t437
  t499 = -t475 * t77 - t478 * t148 - 0.4e1 / 0.3e1 * t481 * t301 + 0.11e2 / 0.3e1 * t293 * t255 - 0.8e1 / 0.9e1 * t488 * t491 + 0.44e2 / 0.9e1 * t300 * t494 - 0.154e3 / 0.27e2 * t180 * t433
  t500 = t59 * t499
  t504 = t79 * t183 * t83
  t507 = t310 * t183
  t508 = t59 * t507
  t521 = t81 ** 2
  t522 = t59 * t521
  t526 = -0.539e3 / 0.21870e5 * t61 * t433 + t500 * t83 / 0.100e3 - 0.9e1 / 0.100e3 * t307 * t504 - 0.3e1 / 0.100e3 * t508 * t83 + 0.3e1 / 0.50e2 * t508 * t81 * t83 - t187 * t499 * t83 / 0.100e3 + 0.3e1 / 0.100e3 * t319 * t306 * t183 * t83 - t522 * t507 * t83 / 0.100e3
  t529 = -0.1540e4 / 0.6561e4 * t29 * t433 - 0.209e3 / 0.243e3 * t43 * t45 * t437 * t54 + 0.797e3 / 0.120e3 * t161 * t162 * t443 * t54 - 0.729e3 / 0.800e3 * t272 * t273 / t21 / t163 / t47 * t280 + 0.243e3 / 0.4000e4 * t456 * t457 / t20 / t458 * t465 + 0.6e1 * t191 * t323 + 0.2e1 * t86 * t526
  t538 = -t499
  t539 = f.my_piecewise3(t95, 0, t538)
  t545 = t335 * t198
  t575 = -0.667e0 * t539 - 0.26673330e1 * t198 * t333 - 0.8891110e0 * t96 * t539 - 0.3978519606294e1 * t545 - 0.11935558818882e2 * t200 * t333 - 0.1989259803147e1 * t98 * t539 + 0.34831129067760e2 * t96 * t545 + 0.52246693601640e2 * t202 * t333 + 0.5805188177960e1 * t100 * t539 - 0.53279882495820e2 * t98 * t545 - 0.53279882495820e2 * t204 * t333 - 0.4439990207985e1 * t102 * t539 + 0.28143472977480e2 * t100 * t545 + 0.21107604733110e2 * t206 * t333 + 0.1407173648874e1 * t104 * t539 - 0.4869027097620e1 * t102 * t545 - 0.2921416258572e1 * t208 * t333 - 0.162300903254e0 * t106 * t539
  t576 = t362 * t216
  t581 = t213 * t361
  t582 = t216 * t115
  t583 = t582 * t367
  t587 = 0.1e1 / t373 / t112
  t592 = f.my_piecewise3(t95, t538, 0)
  t596 = t372 * t374
  t600 = params.d * t371 * params.c2
  t602 = 0.1e1 / t373 / t214
  t607 = f.my_piecewise3(t94, t575, -t213 * t215 * t592 * t115 - 0.6e1 * t213 * t374 * t576 * t115 - 0.6e1 * t372 * t587 * t576 * t115 - t600 * t602 * t576 * t115 - 0.6e1 * t581 * t583 - 0.3e1 * t596 * t583)
  t610 = 0.6e1 * t420 * t421 * t118 - 0.6e1 * t248 * t195 * t326 + 0.6e1 * t248 * t249 * t220 + t144 * t529 * t118 - 0.3e1 * t144 * t326 * t220 - 0.3e1 * t144 * t194 * t379 - t93 * t607 + 0.1174e1 * t607
  t616 = t17 / t19
  t623 = t17 / t20 / t46
  t629 = t17 / t20
  t635 = 0.1e1 / t4 / t25
  t636 = t231 * t635
  t638 = 0.1e1 / t21 / t151
  t640 = t636 * t17 * t638
  t642 = t126 * s0
  t647 = 0.1e1 / t132 * t25 / t642 / t233 / 0.72e2
  t649 = t642 * t136
  t650 = t121 * t647 * t649
  t653 = t3 * t635
  t658 = t24 * t41 * t411 * t31 * t136
  t661 = t232 * t17
  t662 = t238 * t136
  t666 = -0.5e1 / 0.36e2 * t18 * t122 * t137 + t18 * t66 * t223 * t137 / 0.4e1 - 0.11819983333333333333333333333333333333333333333333e2 * t232 * t234 * t121 * t242 - 0.3e1 / 0.8e1 * t18 * t245 * t382 * t137 + 0.12369750000000000000000000000000000000000000000000e2 * t232 * t388 * t223 * t242 + 0.17812440000000000000000000000000000000000000000000e3 * t232 * t393 * t121 * t402 - 0.81605714700000000000000000000000000000000000000000e1 * t407 * t409 * t415 - 0.3e1 / 0.8e1 * t18 * t20 * t610 * t137 - 0.74218500000000000000000000000000000000000000000000e1 * t232 * t616 * t382 * t242 - 0.89062200000000000000000000000000000000000000000000e2 * t232 * t623 * t223 * t402 + 0.12240857205000000000000000000000000000000000000000e2 * t407 * t629 * t223 * t415 - 0.11874960000000000000000000000000000000000000000000e4 * t640 * t650 + 0.81605714699999999999999999999999999999999999999999e1 * t653 * t409 * t658 - 0.32302153261130400000000000000000000000000000000000e3 * t661 * t122 * t662
  t667 = f.my_piecewise3(t2, 0, t666)
  t669 = t147 * t121
  t677 = t408 * t223
  t699 = t17 / t20 / t19 * t121
  t712 = t249 ** 2
  t722 = t326 ** 2
  t735 = t32 * t638
  t739 = 0.1e1 / t20 / t164
  t744 = 0.1e1 / t274
  t752 = t273 / t21 / t163 / t151
  t764 = t159 ** 2
  t774 = t323 ** 2
  t805 = t299 ** 2
  t818 = -(0.6160e4 / 0.81e2 * t64 * t432 - 0.2618e4 / 0.81e2 * t735) * t77 - 0.4e1 / 0.3e1 * t475 * t178 * params.eta * t148 - 0.8e1 / 0.3e1 * t290 * t297 * t299 * t301 + 0.22e2 / 0.3e1 * t478 * t255 - 0.32e2 / 0.9e1 * t175 * t487 * t491 + 0.176e3 / 0.9e1 * t481 * t494 - 0.616e3 / 0.27e2 * t293 * t433 - 0.32e2 / 0.27e2 * t69 / t486 / t76 * t805 * t752 * t31 + 0.176e3 / 0.9e1 * t488 * t490 * t744 - 0.3916e4 / 0.81e2 * t300 * t45 * t739 + 0.2618e4 / 0.81e2 * t180 * t735
  t826 = t306 ** 2
  t834 = t310 ** 2
  t835 = t59 * t834
  t860 = 0.9163e4 / 0.65610e5 * t61 * t735 + t59 * t818 * t83 / 0.100e3 - 0.3e1 / 0.25e2 * t500 * t504 - 0.9e1 / 0.50e2 * t307 * t320 - 0.9e1 / 0.100e3 * t59 * t826 * t312 + 0.9e1 / 0.25e2 * t307 * t81 * t310 * t83 + 0.3e1 / 0.20e2 * t835 * t312 - t835 * t318 * t83 / 0.10e2 - t187 * t818 * t83 / 0.100e3 + t319 * t499 * t183 * t83 / 0.25e2 + 0.3e1 / 0.100e3 * t319 * t826 * t83 - 0.3e1 / 0.50e2 * t522 * t306 * t310 * t83 + t59 * t521 * t79 * t834 * t83 / 0.100e3
  t875 = t333 ** 2
  t877 = t335 ** 2
  t879 = -t818
  t880 = f.my_piecewise3(t95, 0, t879)
  t904 = -0.26673330e1 * t875 + 0.34831129067760e2 * t877 - 0.667e0 * t880 + 0.52246693601640e2 * t98 * t875 - 0.106559764991640e3 * t96 * t877 - 0.2921416258572e1 * t104 * t875 + 0.21107604733110e2 * t102 * t875 - 0.19476108390480e2 * t100 * t877 - 0.53279882495820e2 * t100 * t875 + 0.84430418932440e2 * t98 * t877 - 0.8891110e0 * t96 * t880 - 0.23871117637764e2 * t335 * t333 - 0.1989259803147e1 * t98 * t880 - 0.4439990207985e1 * t102 * t880
  t933 = 0.1407173648874e1 * t104 * t880 - 0.162300903254e0 * t106 * t880 - 0.11935558818882e2 * t96 * t875 + 0.5805188177960e1 * t100 * t880 - 0.35564440e1 * t198 * t539 - 0.15914078425176e2 * t200 * t539 + 0.69662258135520e2 * t202 * t539 - 0.319679294974920e3 * t343 * t333 - 0.29214162585720e2 * t351 * t333 - 0.71039843327760e2 * t204 * t539 + 0.168860837864880e3 * t347 * t333 - 0.3895221678096e1 * t208 * t539 + 0.28143472977480e2 * t206 * t539 + 0.208986774406560e3 * t339 * t333
  t935 = t362 ** 2
  t942 = t362 * t115 * t367
  t949 = t367 ** 2
  t957 = t582 * t592
  t966 = f.my_piecewise3(t95, t879, 0)
  t979 = t371 ** 2
  t981 = t373 ** 2
  t986 = -0.24e2 * t213 * t587 * t935 * t115 - 0.36e2 * t213 * t374 * t942 - 0.36e2 * t372 * t602 * t935 * t115 - 0.6e1 * t213 * t361 * t949 * t115 - 0.36e2 * t372 * t587 * t942 - 0.8e1 * t581 * t957 - 0.12e2 * t600 / t373 / t360 * t935 * t115 - t213 * t215 * t966 * t115 - 0.4e1 * t596 * t957 - 0.3e1 * t372 * t374 * t949 * t115 - 0.6e1 * t600 * t602 * t942 - params.d * t979 / t981 * t935 * t115
  t987 = f.my_piecewise3(t94, t904 + t933, t986)
  t990 = -0.24e2 * t141 / t418 / t88 * t712 * t118 + 0.36e2 * t420 * t250 * t326 - 0.24e2 * t420 * t421 * t220 - 0.6e1 * t248 * t722 * t118 + 0.24e2 * t248 * t329 * t326 - 0.8e1 * t248 * t195 * t529 + 0.12e2 * t248 * t249 * t379 + t144 * (0.26180e5 / 0.19683e5 * t29 * t735 + 0.5225e4 / 0.729e3 * t43 * t45 * t739 * t54 - 0.5929e4 / 0.72e2 * t161 * t162 * t744 * t54 + 0.2949e4 / 0.160e3 * t272 * t752 * t280 - 0.1053e4 / 0.400e3 * t456 * t457 / t20 / t458 / r0 * t465 + 0.6561e4 / 0.10000e5 * t455 * t38 / t764 * t273 * t44 / t458 / t46 * t54 + 0.6e1 * t774 + 0.8e1 * t191 * t526 + 0.2e1 * t86 * t860) * t118 - 0.4e1 * t144 * t529 * t220 - 0.6e1 * t144 * t326 * t379 - 0.4e1 * t144 * t194 * t607 - t93 * t987 + 0.1174e1 * t987
  t999 = t23 * t223
  t1007 = 0.86139075363014400000000000000000000000000000000001e3 * t661 * t669 * t662 - 0.47499840000000000000000000000000000000000000000000e4 * t640 * t223 * t647 * t649 + 0.32642285880000000000000000000000000000000000000000e2 * t653 * t677 * t658 + 0.88793235622637281199999999999999999999999999999999e2 * t407 * t17 / r0 * t121 / s0 * t39 * t124 * t30 * t136 + 0.24481714410000000000000000000000000000000000000000e2 * t407 * t629 * t382 * t415 + 0.30375460471666666666666666666666666666666666666666e2 * t407 * t699 * t415 - 0.32642285880000000000000000000000000000000000000000e2 * t407 * t677 * t415 - 0.32642285879999999999999999999999999999999999999998e2 * t653 * t699 * t658 - 0.3e1 / 0.8e1 * t18 * t20 * t990 * t137 - t18 * t245 * t610 * t137 / 0.2e1 - 0.5e1 / 0.9e1 * t18 * t999 * t137 + t18 * t66 * t382 * t137 / 0.2e1
  t1023 = t232 * t17 / t47 * t121
  t1072 = -0.12920861304452160000000000000000000000000000000000e4 * t661 * t999 * t662 + 0.15041616000000000000000000000000000000000000000000e5 * t636 * t17 / t21 / t258 * t650 + 0.10e2 / 0.27e2 * t18 * t669 * t137 - 0.64604306522260800000000000000000000000000000000000e3 * t1023 * t398 * t136 * t39 * t124 * t126 * t30 - 0.17812440000000000000000000000000000000000000000000e3 * t232 * t623 * t382 * t402 - 0.76967333333333333333333333333333333333333333333333e2 * t636 * t17 * t165 * t121 / t132 / t463 / t45 / t49 * t44 * t136 * t125 * t30 - 0.98958000000000000000000000000000000000000000000000e1 * t232 * t616 * t610 * t242 + 0.71249760000000000000000000000000000000000000000000e3 * t232 * t393 * t223 * t402 + 0.46363655555555555555555555555555555555555555555554e2 * t1023 * t242 - 0.47279933333333333333333333333333333333333333333333e2 * t232 * t234 * t223 * t242 - 0.10918366000000000000000000000000000000000000000000e4 * t232 * t17 * t153 * t121 * t402 + 0.24739500000000000000000000000000000000000000000000e2 * t232 * t388 * t382 * t242
  t1074 = f.my_piecewise3(t2, 0, t1007 + t1072)
  v4rho4_0_ = 0.2e1 * r0 * t1074 + 0.8e1 * t667

  res = {'v4rho4': v4rho4_0_}
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
  t44 = 6 ** (0.1e1 / 0.3e1)
  t45 = jnp.pi ** 2
  t46 = t45 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = 0.1e1 / t47
  t49 = t44 * t48
  t50 = r0 ** 2
  t51 = r0 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t54 = 0.1e1 / t52 / t50
  t55 = s0 * t54
  t56 = t49 * t55
  t60 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t61 = t44 ** 2
  t63 = t46 * t45
  t64 = 0.1e1 / t63
  t65 = t60 * t61 * t64
  t66 = s0 ** 2
  t67 = t50 ** 2
  t68 = t67 * r0
  t72 = t60 * t44
  t73 = t48 * s0
  t74 = t73 * t54
  t77 = jnp.exp(-0.27e2 / 0.80e2 * t72 * t74)
  t81 = jnp.sqrt(0.146e3)
  t82 = t81 * t44
  t86 = 0.1e1 / t52 / r0
  t89 = tau0 * t86 - t55 / 0.8e1
  t91 = 0.3e1 / 0.10e2 * t61 * t47
  t92 = params.eta * s0
  t95 = t91 + t92 * t54 / 0.8e1
  t96 = 0.1e1 / t95
  t97 = t89 * t96
  t98 = 0.1e1 - t97
  t100 = t98 ** 2
  t102 = jnp.exp(-t100 / 0.2e1)
  t105 = 0.7e1 / 0.12960e5 * t82 * t74 + t81 * t98 * t102 / 0.100e3
  t106 = t105 ** 2
  t107 = params.k1 + 0.5e1 / 0.972e3 * t56 + t65 * t66 / t51 / t68 * t77 / 0.576e3 + t106
  t112 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t107)
  t113 = t97 <= 0.25e1
  t114 = 0.25e1 < t97
  t115 = f.my_piecewise3(t114, 0.25e1, t97)
  t117 = t115 ** 2
  t119 = t117 * t115
  t121 = t117 ** 2
  t123 = t121 * t115
  t125 = t121 * t117
  t130 = f.my_piecewise3(t114, t97, 0.25e1)
  t131 = 0.1e1 - t130
  t134 = jnp.exp(params.c2 / t131)
  t136 = f.my_piecewise3(t113, 0.1e1 - 0.667e0 * t115 - 0.4445555e0 * t117 - 0.663086601049e0 * t119 + 0.1451297044490e1 * t121 - 0.887998041597e0 * t123 + 0.234528941479e0 * t125 - 0.23185843322e-1 * t121 * t119, -params.d * t134)
  t137 = 0.1e1 - t136
  t140 = t112 * t137 + 0.1174e1 * t136
  t142 = jnp.sqrt(0.3e1)
  t143 = 0.1e1 / t46
  t144 = t61 * t143
  t145 = jnp.sqrt(s0)
  t149 = t144 * t145 / t51 / r0
  t150 = jnp.sqrt(t149)
  t154 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t142 / t150)
  t155 = 0.1e1 - t154
  t156 = t43 * t140 * t155
  t161 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t162 = t5 * t161
  t163 = t43 ** 2
  t164 = 0.1e1 / t163
  t166 = t164 * t140 * t155
  t169 = params.k1 ** 2
  t170 = t107 ** 2
  t172 = t169 / t170
  t173 = t50 * r0
  t175 = 0.1e1 / t52 / t173
  t176 = s0 * t175
  t186 = t60 ** 2
  t187 = t45 ** 2
  t188 = 0.1e1 / t187
  t189 = t186 * t188
  t190 = t66 * s0
  t191 = t67 ** 2
  t204 = -0.5e1 / 0.3e1 * tau0 * t54 + t176 / 0.3e1
  t206 = t95 ** 2
  t207 = 0.1e1 / t206
  t208 = t89 * t207
  t209 = t92 * t175
  t212 = -t204 * t96 - t208 * t209 / 0.3e1
  t216 = t81 * t100
  t220 = -0.7e1 / 0.4860e4 * t82 * t73 * t175 + t81 * t212 * t102 / 0.100e3 - t216 * t212 * t102 / 0.100e3
  t223 = -0.10e2 / 0.729e3 * t49 * t176 - t65 * t66 / t51 / t67 / t50 * t77 / 0.108e3 + 0.3e1 / 0.320e3 * t189 * t190 / t191 / r0 * t77 + 0.2e1 * t105 * t220
  t224 = t223 * t137
  t226 = -t212
  t227 = f.my_piecewise3(t114, 0, t226)
  t229 = t115 * t227
  t231 = t117 * t227
  t233 = t119 * t227
  t235 = t121 * t227
  t237 = t123 * t227
  t242 = params.d * params.c2
  t243 = t131 ** 2
  t244 = 0.1e1 / t243
  t245 = f.my_piecewise3(t114, t226, 0)
  t249 = f.my_piecewise3(t113, -0.667e0 * t227 - 0.8891110e0 * t229 - 0.1989259803147e1 * t231 + 0.5805188177960e1 * t233 - 0.4439990207985e1 * t235 + 0.1407173648874e1 * t237 - 0.162300903254e0 * t125 * t227, -t242 * t244 * t245 * t134)
  t252 = t172 * t224 - t112 * t249 + 0.1174e1 * t249
  t254 = t43 * t252 * t155
  t257 = 3 ** (0.1e1 / 0.6e1)
  t258 = t257 ** 2
  t259 = t258 ** 2
  t260 = t259 * t257
  t261 = t260 * t4
  t262 = t161 * t43
  t263 = t262 * t140
  t264 = t261 * t263
  t266 = 0.1e1 / t150 / t149
  t268 = t266 * t61 * t143
  t273 = t268 * t145 / t51 / t50 * t154
  t276 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t277 = t276 * f.p.zeta_threshold
  t279 = f.my_piecewise3(t20, t277, t21 * t19)
  t280 = t5 * t279
  t282 = 0.1e1 / t163 / t6
  t284 = t282 * t140 * t155
  t288 = t164 * t252 * t155
  t291 = t279 * t164
  t292 = t291 * t140
  t293 = t261 * t292
  t298 = t169 / t170 / t107
  t299 = t223 ** 2
  t304 = 0.1e1 / t52 / t67
  t305 = s0 * t304
  t308 = t67 * t173
  t310 = 0.1e1 / t51 / t308
  t323 = t66 ** 2
  t324 = t186 * t60 * t188 * t323
  t329 = t48 * t77
  t333 = t220 ** 2
  t341 = 0.40e2 / 0.9e1 * tau0 * t175 - 0.11e2 / 0.9e1 * t305
  t343 = t204 * t207
  t347 = 0.1e1 / t206 / t95
  t348 = t89 * t347
  t349 = params.eta ** 2
  t350 = t349 * t66
  t351 = t350 * t310
  t354 = t92 * t304
  t357 = -t341 * t96 - 0.2e1 / 0.3e1 * t343 * t209 - 0.2e1 / 0.9e1 * t348 * t351 + 0.11e2 / 0.9e1 * t208 * t354
  t358 = t81 * t357
  t361 = t212 ** 2
  t370 = t81 * t100 * t98
  t374 = 0.77e2 / 0.14580e5 * t82 * t73 * t304 + t358 * t102 / 0.100e3 - 0.3e1 / 0.100e3 * t81 * t361 * t98 * t102 - t216 * t357 * t102 / 0.100e3 + t370 * t361 * t102 / 0.100e3
  t377 = 0.110e3 / 0.2187e4 * t49 * t305 + 0.19e2 / 0.324e3 * t65 * t66 * t310 * t77 - 0.43e2 / 0.320e3 * t189 * t190 / t191 / t50 * t77 + 0.27e2 / 0.3200e4 * t324 / t52 / t191 / t67 * t44 * t329 + 0.2e1 * t333 + 0.2e1 * t105 * t374
  t383 = -t357
  t384 = f.my_piecewise3(t114, 0, t383)
  t386 = t227 ** 2
  t410 = -0.667e0 * t384 - 0.8891110e0 * t386 - 0.8891110e0 * t115 * t384 - 0.3978519606294e1 * t115 * t386 - 0.1989259803147e1 * t117 * t384 + 0.17415564533880e2 * t117 * t386 + 0.5805188177960e1 * t119 * t384 - 0.17759960831940e2 * t119 * t386 - 0.4439990207985e1 * t121 * t384 + 0.7035868244370e1 * t121 * t386 + 0.1407173648874e1 * t123 * t384 - 0.973805419524e0 * t123 * t386 - 0.162300903254e0 * t125 * t384
  t412 = 0.1e1 / t243 / t131
  t413 = t245 ** 2
  t418 = f.my_piecewise3(t114, t383, 0)
  t422 = params.c2 ** 2
  t423 = params.d * t422
  t424 = t243 ** 2
  t425 = 0.1e1 / t424
  t430 = f.my_piecewise3(t113, t410, -t242 * t244 * t418 * t134 - 0.2e1 * t242 * t412 * t413 * t134 - t423 * t425 * t413 * t134)
  t433 = -0.2e1 * t298 * t299 * t137 + t172 * t377 * t137 - 0.2e1 * t172 * t223 * t249 - t112 * t430 + 0.1174e1 * t430
  t435 = t43 * t433 * t155
  t438 = t279 * t43
  t439 = t438 * t252
  t440 = t261 * t439
  t443 = t438 * t140
  t444 = t261 * t443
  t449 = 0.1e1 / t150 / t56 * t44 * t48 / 0.6e1
  t451 = t449 * t305 * t154
  t458 = t268 * t145 / t51 / t173 * t154
  t461 = t3 ** 2
  t463 = t2 * t461 * jnp.pi
  t464 = t463 * t443
  t465 = 0.1e1 / t145
  t468 = t49 * t154
  t469 = t465 / t52 * t468
  t472 = -0.3e1 / 0.8e1 * t42 * t156 - t162 * t166 / 0.4e1 - 0.3e1 / 0.4e1 * t162 * t254 - 0.49479000000000000000000000000000000000000000000000e1 * t264 * t273 + t280 * t284 / 0.12e2 - t280 * t288 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t293 * t273 - 0.3e1 / 0.8e1 * t280 * t435 - 0.49479000000000000000000000000000000000000000000000e1 * t440 * t273 - 0.29687400000000000000000000000000000000000000000000e2 * t444 * t451 + 0.57725500000000000000000000000000000000000000000000e1 * t444 * t458 + 0.81605714700000000000000000000000000000000000000000e1 * t464 * t469
  t473 = f.my_piecewise3(t1, 0, t472)
  t475 = r1 <= f.p.dens_threshold
  t476 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t477 = 0.1e1 + t476
  t478 = t477 <= f.p.zeta_threshold
  t479 = t477 ** (0.1e1 / 0.3e1)
  t480 = t479 ** 2
  t481 = 0.1e1 / t480
  t483 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t484 = t483 ** 2
  t488 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t492 = f.my_piecewise3(t478, 0, 0.4e1 / 0.9e1 * t481 * t484 + 0.4e1 / 0.3e1 * t479 * t488)
  t493 = t5 * t492
  t494 = r1 ** 2
  t495 = r1 ** (0.1e1 / 0.3e1)
  t496 = t495 ** 2
  t498 = 0.1e1 / t496 / t494
  t499 = s2 * t498
  t502 = s2 ** 2
  t503 = t494 ** 2
  t509 = t48 * s2 * t498
  t512 = jnp.exp(-0.27e2 / 0.80e2 * t72 * t509)
  t528 = (tau1 / t496 / r1 - t499 / 0.8e1) / (t91 + params.eta * s2 * t498 / 0.8e1)
  t529 = 0.1e1 - t528
  t531 = t529 ** 2
  t533 = jnp.exp(-t531 / 0.2e1)
  t537 = (0.7e1 / 0.12960e5 * t82 * t509 + t81 * t529 * t533 / 0.100e3) ** 2
  t545 = 0.25e1 < t528
  t546 = f.my_piecewise3(t545, 0.25e1, t528)
  t548 = t546 ** 2
  t550 = t548 * t546
  t552 = t548 ** 2
  t561 = f.my_piecewise3(t545, t528, 0.25e1)
  t565 = jnp.exp(params.c2 / (0.1e1 - t561))
  t567 = f.my_piecewise3(t528 <= 0.25e1, 0.1e1 - 0.667e0 * t546 - 0.4445555e0 * t548 - 0.663086601049e0 * t550 + 0.1451297044490e1 * t552 - 0.887998041597e0 * t552 * t546 + 0.234528941479e0 * t552 * t548 - 0.23185843322e-1 * t552 * t550, -params.d * t565)
  t571 = (0.1e1 + params.k1 * (0.1e1 - params.k1 / (params.k1 + 0.5e1 / 0.972e3 * t49 * t499 + t65 * t502 / t495 / t503 / r1 * t512 / 0.576e3 + t537))) * (0.1e1 - t567) + 0.1174e1 * t567
  t573 = jnp.sqrt(s2)
  t578 = jnp.sqrt(t144 * t573 / t495 / r1)
  t582 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t142 / t578)
  t583 = 0.1e1 - t582
  t584 = t43 * t571 * t583
  t589 = f.my_piecewise3(t478, 0, 0.4e1 / 0.3e1 * t479 * t483)
  t590 = t5 * t589
  t592 = t164 * t571 * t583
  t596 = f.my_piecewise3(t478, t277, t479 * t477)
  t597 = t5 * t596
  t599 = t282 * t571 * t583
  t603 = f.my_piecewise3(t475, 0, -0.3e1 / 0.8e1 * t493 * t584 - t590 * t592 / 0.4e1 + t597 * t599 / 0.12e2)
  t606 = 0.1e1 / t3 / t45
  t610 = t145 * s0
  t636 = t465 * t86
  t644 = t170 ** 2
  t658 = 0.1e1 / t52 / t68
  t659 = s0 * t658
  t663 = 0.1e1 / t51 / t191
  t669 = 0.1e1 / t191 / t173
  t681 = t186 ** 2
  t685 = t191 ** 2
  t710 = t206 ** 2
  t724 = -(-0.440e3 / 0.27e2 * tau0 * t304 + 0.154e3 / 0.27e2 * t659) * t96 - t341 * t207 * t209 - 0.2e1 / 0.3e1 * t204 * t347 * t351 + 0.11e2 / 0.3e1 * t343 * t354 - 0.2e1 / 0.9e1 * t89 / t710 * t349 * params.eta * t190 * t669 + 0.22e2 / 0.9e1 * t348 * t350 * t663 - 0.154e3 / 0.27e2 * t208 * t92 * t658
  t732 = t361 * t212
  t733 = t81 * t732
  t746 = t100 ** 2
  t763 = -t724
  t764 = f.my_piecewise3(t114, 0, t763)
  t770 = t386 * t227
  t800 = -0.667e0 * t764 - 0.26673330e1 * t227 * t384 - 0.8891110e0 * t115 * t764 - 0.3978519606294e1 * t770 - 0.11935558818882e2 * t229 * t384 - 0.1989259803147e1 * t117 * t764 + 0.34831129067760e2 * t115 * t770 + 0.52246693601640e2 * t231 * t384 + 0.5805188177960e1 * t119 * t764 - 0.53279882495820e2 * t117 * t770 - 0.53279882495820e2 * t233 * t384 - 0.4439990207985e1 * t121 * t764 + 0.28143472977480e2 * t119 * t770 + 0.21107604733110e2 * t235 * t384 + 0.1407173648874e1 * t123 * t764 - 0.4869027097620e1 * t121 * t770 - 0.2921416258572e1 * t237 * t384 - 0.162300903254e0 * t125 * t764
  t801 = t413 * t245
  t808 = t245 * t134 * t418
  t817 = f.my_piecewise3(t114, t763, 0)
  t832 = f.my_piecewise3(t113, t800, -0.6e1 * t242 * t425 * t801 * t134 - 0.6e1 * t242 * t412 * t808 - 0.6e1 * t423 / t424 / t131 * t801 * t134 - t242 * t244 * t817 * t134 - 0.3e1 * t423 * t425 * t808 - params.d * t422 * params.c2 / t424 / t243 * t801 * t134)
  t848 = t24 ** 2
  t852 = 0.6e1 * t33 - 0.6e1 * t16 / t848
  t853 = f.my_piecewise5(t10, 0, t14, 0, t852)
  t857 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t853)
  t884 = -0.16493000000000000000000000000000000000000000000000e2 * t260 * t606 * t438 * t140 / t150 * t45 * t67 / t308 * t154 + 0.24481714410000000000000000000000000000000000000000e2 * t463 * t263 * t469 + 0.81605714700000000000000000000000000000000000000000e1 * t463 * t292 * t469 + 0.24481714410000000000000000000000000000000000000000e2 * t463 * t439 * t469 + 0.16321142940000000000000000000000000000000000000000e2 * t2 * t606 * t443 * t44 * t63 * t636 * t154 - 0.24481714410000000000000000000000000000000000000000e2 * t464 * t636 * t468 - 0.3e1 / 0.8e1 * t280 * t43 * (0.6e1 * t169 / t644 * t299 * t223 * t137 - 0.6e1 * t298 * t224 * t377 + 0.6e1 * t298 * t299 * t249 + t172 * (-0.1540e4 / 0.6561e4 * t49 * t659 - 0.209e3 / 0.486e3 * t65 * t66 * t663 * t77 + 0.797e3 / 0.480e3 * t189 * t190 * t669 * t77 - 0.729e3 / 0.3200e4 * t324 / t52 / t191 / t68 * t44 * t329 + 0.243e3 / 0.32000e5 * t681 * t188 * t323 * s0 / t51 / t685 * t61 * t64 * t77 + 0.6e1 * t220 * t374 + 0.2e1 * t105 * (-0.539e3 / 0.21870e5 * t82 * t73 * t658 + t81 * t724 * t102 / 0.100e3 - 0.9e1 / 0.100e3 * t358 * t98 * t212 * t102 - 0.3e1 / 0.100e3 * t733 * t102 + 0.3e1 / 0.50e2 * t733 * t100 * t102 - t216 * t724 * t102 / 0.100e3 + 0.3e1 / 0.100e3 * t370 * t357 * t212 * t102 - t81 * t746 * t732 * t102 / 0.100e3)) * t137 - 0.3e1 * t172 * t377 * t249 - 0.3e1 * t172 * t223 * t430 - t112 * t832 + 0.1174e1 * t832) * t155 - 0.3e1 / 0.8e1 * t5 * t857 * t156 - 0.9e1 / 0.8e1 * t42 * t254 - 0.32302153261130400000000000000000000000000000000000e3 * t261 * t438 * t140 / t173 * t266 * t154 + 0.17317650000000000000000000000000000000000000000000e2 * t440 * t458 + 0.20781180000000000000000000000000000000000000000000e3 * t444 * t449 * t659 * t154 + 0.57725500000000000000000000000000000000000000000000e1 * t293 * t458 + 0.17317650000000000000000000000000000000000000000000e2 * t264 * t458 - 0.74218500000000000000000000000000000000000000000000e1 * t261 * t438 * t433 * t273
  t934 = 0.1e1 / t163 / t24
  t943 = -0.89062200000000000000000000000000000000000000000000e2 * t440 * t451 - 0.74218500000000000000000000000000000000000000000000e1 * t261 * t41 * t43 * t140 * t273 - 0.49479000000000000000000000000000000000000000000000e1 * t261 * t161 * t164 * t140 * t273 - 0.14843700000000000000000000000000000000000000000000e2 * t261 * t262 * t252 * t273 - 0.89062200000000000000000000000000000000000000000000e2 * t264 * t451 + 0.16493000000000000000000000000000000000000000000000e1 * t261 * t279 * t282 * t140 * t273 - 0.49479000000000000000000000000000000000000000000000e1 * t261 * t291 * t252 * t273 - 0.29687400000000000000000000000000000000000000000000e2 * t293 * t451 - 0.19241833333333333333333333333333333333333333333333e2 * t444 * t268 * t145 / t51 / t67 * t154 + t280 * t282 * t252 * t155 / 0.4e1 - 0.3e1 / 0.8e1 * t280 * t164 * t433 * t155 - 0.3e1 / 0.4e1 * t162 * t288 - 0.9e1 / 0.8e1 * t162 * t435 - 0.5e1 / 0.36e2 * t280 * t934 * t140 * t155 - 0.3e1 / 0.8e1 * t42 * t166 + t162 * t284 / 0.4e1
  t945 = f.my_piecewise3(t1, 0, t884 + t943)
  t955 = f.my_piecewise5(t14, 0, t10, 0, -t852)
  t959 = f.my_piecewise3(t478, 0, -0.8e1 / 0.27e2 / t480 / t477 * t484 * t483 + 0.4e1 / 0.3e1 * t481 * t483 * t488 + 0.4e1 / 0.3e1 * t479 * t955)
  t972 = f.my_piecewise3(t475, 0, -0.3e1 / 0.8e1 * t5 * t959 * t584 - 0.3e1 / 0.8e1 * t493 * t592 + t590 * t599 / 0.4e1 - 0.5e1 / 0.36e2 * t597 * t934 * t571 * t583)
  d111 = 0.3e1 * t473 + 0.3e1 * t603 + t6 * (t945 + t972)

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
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = t6 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t34 * t37
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t44 = s0 * t43
  t45 = t38 * t44
  t49 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t50 = t34 ** 2
  t52 = t35 * t6
  t53 = 0.1e1 / t52
  t54 = t49 * t50 * t53
  t55 = s0 ** 2
  t56 = t39 ** 2
  t57 = t56 * r0
  t59 = 0.1e1 / t40 / t57
  t60 = t55 * t59
  t61 = t49 * t34
  t62 = t37 * s0
  t63 = t62 * t43
  t66 = jnp.exp(-0.27e2 / 0.80e2 * t61 * t63)
  t70 = jnp.sqrt(0.146e3)
  t71 = t70 * t34
  t75 = 0.1e1 / t41 / r0
  t78 = tau0 * t75 - t44 / 0.8e1
  t80 = 0.3e1 / 0.10e2 * t50 * t36
  t81 = params.eta * s0
  t84 = t80 + t81 * t43 / 0.8e1
  t85 = 0.1e1 / t84
  t86 = t78 * t85
  t87 = 0.1e1 - t86
  t89 = t87 ** 2
  t91 = jnp.exp(-t89 / 0.2e1)
  t94 = 0.7e1 / 0.12960e5 * t71 * t63 + t70 * t87 * t91 / 0.100e3
  t95 = t94 ** 2
  t96 = params.k1 + 0.5e1 / 0.972e3 * t45 + t54 * t60 * t66 / 0.576e3 + t95
  t101 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t96)
  t102 = t86 <= 0.25e1
  t103 = 0.25e1 < t86
  t104 = f.my_piecewise3(t103, 0.25e1, t86)
  t106 = t104 ** 2
  t108 = t106 * t104
  t110 = t106 ** 2
  t112 = t110 * t104
  t114 = t110 * t106
  t119 = f.my_piecewise3(t103, t86, 0.25e1)
  t120 = 0.1e1 - t119
  t123 = jnp.exp(params.c2 / t120)
  t125 = f.my_piecewise3(t102, 0.1e1 - 0.667e0 * t104 - 0.4445555e0 * t106 - 0.663086601049e0 * t108 + 0.1451297044490e1 * t110 - 0.887998041597e0 * t112 + 0.234528941479e0 * t114 - 0.23185843322e-1 * t110 * t108, -params.d * t123)
  t126 = 0.1e1 - t125
  t129 = t101 * t126 + 0.1174e1 * t125
  t131 = jnp.sqrt(s0)
  t132 = t131 * s0
  t134 = 0.1e1 / t56
  t137 = 0.1e1 / t35
  t138 = t50 * t137
  t140 = 0.1e1 / t40 / r0
  t142 = t138 * t131 * t140
  t143 = jnp.sqrt(t142)
  t145 = 0.1e1 / t143 * t6 / t132 / t134 / 0.36e2
  t146 = t129 * t145
  t147 = t39 * r0
  t148 = t56 * t147
  t151 = jnp.sqrt(0.3e1)
  t155 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t151 / t143)
  t156 = t132 / t148 * t155
  t157 = t146 * t156
  t160 = 3 ** (0.1e1 / 0.3e1)
  t161 = t7 ** 2
  t163 = t160 * t161 * jnp.pi
  t164 = t11 ** 2
  t165 = 0.1e1 / t164
  t167 = -t21 * t165 + t12
  t168 = f.my_piecewise5(t15, 0, t19, 0, t167)
  t171 = f.my_piecewise3(t25, 0, 0.4e1 / 0.3e1 * t28 * t168)
  t172 = t171 * t31
  t173 = t172 * t129
  t174 = t163 * t173
  t175 = 0.1e1 / t131
  t178 = t38 * t155
  t179 = t175 / t41 * t178
  t182 = t31 ** 2
  t183 = 0.1e1 / t182
  t184 = t30 * t183
  t185 = t184 * t129
  t186 = t163 * t185
  t189 = params.k1 ** 2
  t190 = t96 ** 2
  t192 = t189 / t190
  t194 = 0.1e1 / t41 / t147
  t195 = s0 * t194
  t198 = t56 * t39
  t205 = t49 ** 2
  t206 = t6 ** 2
  t207 = 0.1e1 / t206
  t208 = t205 * t207
  t209 = t55 * s0
  t210 = t56 ** 2
  t211 = t210 * r0
  t223 = -0.5e1 / 0.3e1 * tau0 * t43 + t195 / 0.3e1
  t225 = t84 ** 2
  t226 = 0.1e1 / t225
  t227 = t78 * t226
  t228 = t81 * t194
  t231 = -t223 * t85 - t227 * t228 / 0.3e1
  t235 = t70 * t89
  t239 = -0.7e1 / 0.4860e4 * t71 * t62 * t194 + t70 * t231 * t91 / 0.100e3 - t235 * t231 * t91 / 0.100e3
  t242 = -0.10e2 / 0.729e3 * t38 * t195 - t54 * t55 / t40 / t198 * t66 / 0.108e3 + 0.3e1 / 0.320e3 * t208 * t209 / t211 * t66 + 0.2e1 * t94 * t239
  t243 = t242 * t126
  t245 = -t231
  t246 = f.my_piecewise3(t103, 0, t245)
  t248 = t104 * t246
  t250 = t106 * t246
  t252 = t108 * t246
  t254 = t110 * t246
  t256 = t112 * t246
  t261 = params.d * params.c2
  t262 = t120 ** 2
  t263 = 0.1e1 / t262
  t264 = f.my_piecewise3(t103, t245, 0)
  t268 = f.my_piecewise3(t102, -0.667e0 * t246 - 0.8891110e0 * t248 - 0.1989259803147e1 * t250 + 0.5805188177960e1 * t252 - 0.4439990207985e1 * t254 + 0.1407173648874e1 * t256 - 0.162300903254e0 * t114 * t246, -t261 * t263 * t264 * t123)
  t271 = t192 * t243 - t101 * t268 + 0.1174e1 * t268
  t272 = t32 * t271
  t273 = t163 * t272
  t276 = t160 * t9
  t277 = t32 * t129
  t278 = t276 * t277
  t279 = t34 * t52
  t280 = t175 * t75
  t282 = t279 * t280 * t155
  t285 = t163 * t277
  t286 = t280 * t178
  t289 = 0.1e1 / t7
  t290 = t5 * t289
  t291 = t290 * t32
  t292 = 0.1e1 / t147
  t295 = 0.1e1 / t143 / t142
  t296 = t295 * t155
  t297 = t129 * t292 * t296
  t300 = t160 * t289
  t301 = t300 * t171
  t304 = t189 / t190 / t96
  t305 = t242 ** 2
  t306 = t305 * t126
  t310 = 0.1e1 / t41 / t56
  t311 = s0 * t310
  t315 = 0.1e1 / t40 / t148
  t328 = t55 ** 2
  t329 = t205 * t49 * t207 * t328
  t330 = t210 * t56
  t334 = t37 * t66
  t338 = t239 ** 2
  t346 = 0.40e2 / 0.9e1 * tau0 * t194 - 0.11e2 / 0.9e1 * t311
  t348 = t223 * t226
  t352 = 0.1e1 / t225 / t84
  t353 = t78 * t352
  t354 = params.eta ** 2
  t355 = t354 * t55
  t356 = t355 * t315
  t359 = t81 * t310
  t362 = -t346 * t85 - 0.2e1 / 0.3e1 * t348 * t228 - 0.2e1 / 0.9e1 * t353 * t356 + 0.11e2 / 0.9e1 * t227 * t359
  t363 = t70 * t362
  t366 = t231 ** 2
  t368 = t87 * t91
  t374 = t89 * t87
  t375 = t70 * t374
  t376 = t366 * t91
  t379 = 0.77e2 / 0.14580e5 * t71 * t62 * t310 + t363 * t91 / 0.100e3 - 0.3e1 / 0.100e3 * t70 * t366 * t368 - t235 * t362 * t91 / 0.100e3 + t375 * t376 / 0.100e3
  t382 = 0.110e3 / 0.2187e4 * t38 * t311 + 0.19e2 / 0.324e3 * t54 * t55 * t315 * t66 - 0.43e2 / 0.320e3 * t208 * t209 / t210 / t39 * t66 + 0.27e2 / 0.3200e4 * t329 / t41 / t330 * t34 * t334 + 0.2e1 * t338 + 0.2e1 * t94 * t379
  t385 = t242 * t268
  t388 = -t362
  t389 = f.my_piecewise3(t103, 0, t388)
  t391 = t246 ** 2
  t395 = t104 * t391
  t399 = t106 * t391
  t403 = t108 * t391
  t407 = t110 * t391
  t415 = -0.667e0 * t389 - 0.8891110e0 * t391 - 0.8891110e0 * t104 * t389 - 0.3978519606294e1 * t395 - 0.1989259803147e1 * t106 * t389 + 0.17415564533880e2 * t399 + 0.5805188177960e1 * t108 * t389 - 0.17759960831940e2 * t403 - 0.4439990207985e1 * t110 * t389 + 0.7035868244370e1 * t407 + 0.1407173648874e1 * t112 * t389 - 0.973805419524e0 * t112 * t391 - 0.162300903254e0 * t114 * t389
  t416 = t262 * t120
  t417 = 0.1e1 / t416
  t418 = t264 ** 2
  t423 = f.my_piecewise3(t103, t388, 0)
  t427 = params.c2 ** 2
  t428 = params.d * t427
  t429 = t262 ** 2
  t430 = 0.1e1 / t429
  t435 = f.my_piecewise3(t102, t415, -t261 * t263 * t423 * t123 - 0.2e1 * t261 * t417 * t418 * t123 - t428 * t430 * t418 * t123)
  t438 = -0.2e1 * t304 * t306 + t192 * t382 * t126 - 0.2e1 * t192 * t385 - t101 * t435 + 0.1174e1 * t435
  t440 = 0.1e1 - t155
  t441 = t31 * t438 * t440
  t444 = t300 * t30
  t446 = 0.1e1 / t182 / t164
  t448 = t446 * t129 * t440
  t451 = t28 ** 2
  t452 = 0.1e1 / t451
  t453 = t168 ** 2
  t456 = t164 * t11
  t457 = 0.1e1 / t456
  t460 = 0.2e1 * t21 * t457 - 0.2e1 * t165
  t461 = f.my_piecewise5(t15, 0, t19, 0, t460)
  t465 = f.my_piecewise3(t25, 0, 0.4e1 / 0.9e1 * t452 * t453 + 0.4e1 / 0.3e1 * t28 * t461)
  t466 = t300 * t465
  t468 = t183 * t129 * t440
  t472 = 0.1e1 / t182 / t11
  t474 = t472 * t129 * t440
  t477 = t190 ** 2
  t479 = t189 / t477
  t480 = t305 * t242
  t491 = 0.1e1 / t41 / t57
  t492 = s0 * t491
  t496 = 0.1e1 / t40 / t210
  t502 = 0.1e1 / t210 / t147
  t514 = t205 ** 2
  t517 = t514 * t207 * t328 * s0
  t518 = t210 ** 2
  t522 = t53 * t66
  t534 = -0.440e3 / 0.27e2 * tau0 * t310 + 0.154e3 / 0.27e2 * t492
  t536 = t346 * t226
  t538 = t223 * t352
  t543 = t225 ** 2
  t544 = 0.1e1 / t543
  t545 = t78 * t544
  t547 = t354 * params.eta * t209
  t548 = t547 * t502
  t551 = t355 * t496
  t554 = t81 * t491
  t557 = -t534 * t85 - t536 * t228 - 0.2e1 / 0.3e1 * t538 * t356 + 0.11e2 / 0.3e1 * t348 * t359 - 0.2e1 / 0.9e1 * t545 * t548 + 0.22e2 / 0.9e1 * t353 * t551 - 0.154e3 / 0.27e2 * t227 * t554
  t558 = t70 * t557
  t562 = t87 * t231 * t91
  t565 = t366 * t231
  t566 = t70 * t565
  t579 = t89 ** 2
  t580 = t70 * t579
  t584 = -0.539e3 / 0.21870e5 * t71 * t62 * t491 + t558 * t91 / 0.100e3 - 0.9e1 / 0.100e3 * t363 * t562 - 0.3e1 / 0.100e3 * t566 * t91 + 0.3e1 / 0.50e2 * t566 * t89 * t91 - t235 * t557 * t91 / 0.100e3 + 0.3e1 / 0.100e3 * t375 * t362 * t231 * t91 - t580 * t565 * t91 / 0.100e3
  t587 = -0.1540e4 / 0.6561e4 * t38 * t492 - 0.209e3 / 0.486e3 * t54 * t55 * t496 * t66 + 0.797e3 / 0.480e3 * t208 * t209 * t502 * t66 - 0.729e3 / 0.3200e4 * t329 / t41 / t210 / t57 * t34 * t334 + 0.243e3 / 0.32000e5 * t517 / t40 / t518 * t50 * t522 + 0.6e1 * t239 * t379 + 0.2e1 * t94 * t584
  t596 = -t557
  t597 = f.my_piecewise3(t103, 0, t596)
  t603 = t391 * t246
  t633 = -0.667e0 * t597 - 0.26673330e1 * t246 * t389 - 0.8891110e0 * t104 * t597 - 0.3978519606294e1 * t603 - 0.11935558818882e2 * t248 * t389 - 0.1989259803147e1 * t106 * t597 + 0.34831129067760e2 * t104 * t603 + 0.52246693601640e2 * t250 * t389 + 0.5805188177960e1 * t108 * t597 - 0.53279882495820e2 * t106 * t603 - 0.53279882495820e2 * t252 * t389 - 0.4439990207985e1 * t110 * t597 + 0.28143472977480e2 * t108 * t603 + 0.21107604733110e2 * t254 * t389 + 0.1407173648874e1 * t112 * t597 - 0.4869027097620e1 * t110 * t603 - 0.2921416258572e1 * t256 * t389 - 0.162300903254e0 * t114 * t597
  t634 = t418 * t264
  t639 = t261 * t417
  t640 = t264 * t123
  t641 = t640 * t423
  t645 = 0.1e1 / t429 / t120
  t650 = f.my_piecewise3(t103, t596, 0)
  t654 = t428 * t430
  t658 = params.d * t427 * params.c2
  t660 = 0.1e1 / t429 / t262
  t665 = f.my_piecewise3(t102, t633, -t261 * t263 * t650 * t123 - 0.6e1 * t261 * t430 * t634 * t123 - 0.6e1 * t428 * t645 * t634 * t123 - t658 * t660 * t634 * t123 - 0.6e1 * t639 * t641 - 0.3e1 * t654 * t641)
  t668 = 0.6e1 * t479 * t480 * t126 - 0.6e1 * t304 * t243 * t382 + 0.6e1 * t304 * t305 * t268 + t192 * t587 * t126 - 0.3e1 * t192 * t382 * t268 - 0.3e1 * t192 * t242 * t435 - t101 * t665 + 0.1174e1 * t665
  t670 = t31 * t668 * t440
  t674 = t472 * t271 * t440
  t677 = t32 * t438
  t678 = t290 * t677
  t680 = t295 * t50 * t137
  t685 = t680 * t131 / t40 / t39 * t155
  t688 = t290 * t272
  t691 = 0.1e1 / t143 / t45 / 0.6e1
  t693 = t691 * t34 * t37
  t695 = t693 * t311 * t155
  t698 = -0.59374800000000000000000000000000000000000000000000e3 * t33 * t157 + 0.24481714410000000000000000000000000000000000000000e2 * t174 * t179 + 0.81605714700000000000000000000000000000000000000000e1 * t186 * t179 + 0.24481714410000000000000000000000000000000000000000e2 * t273 * t179 + 0.16321142940000000000000000000000000000000000000000e2 * t278 * t282 - 0.24481714410000000000000000000000000000000000000000e2 * t285 * t286 - 0.32302153261130400000000000000000000000000000000000e3 * t291 * t297 - 0.9e1 / 0.8e1 * t301 * t441 - 0.5e1 / 0.36e2 * t444 * t448 - 0.3e1 / 0.8e1 * t466 * t468 + t301 * t474 / 0.4e1 - 0.3e1 / 0.8e1 * t444 * t670 + t444 * t674 / 0.4e1 - 0.74218500000000000000000000000000000000000000000000e1 * t678 * t685 - 0.89062200000000000000000000000000000000000000000000e2 * t688 * t695
  t699 = t465 * t31
  t700 = t699 * t129
  t701 = t290 * t700
  t704 = t171 * t183
  t705 = t704 * t129
  t706 = t290 * t705
  t709 = t172 * t271
  t710 = t290 * t709
  t713 = t290 * t173
  t716 = t30 * t472
  t717 = t716 * t129
  t718 = t290 * t717
  t721 = t184 * t271
  t722 = t290 * t721
  t725 = t290 * t185
  t728 = t290 * t277
  t733 = t680 * t131 / t40 / t56 * t155
  t740 = t680 * t131 / t40 / t147 * t155
  t744 = t693 * t492 * t155
  t752 = 0.1e1 / t451 / t24
  t756 = t452 * t168
  t759 = t164 ** 2
  t760 = 0.1e1 / t759
  t763 = -0.6e1 * t21 * t760 + 0.6e1 * t457
  t764 = f.my_piecewise5(t15, 0, t19, 0, t763)
  t768 = f.my_piecewise3(t25, 0, -0.8e1 / 0.27e2 * t752 * t453 * t168 + 0.4e1 / 0.3e1 * t756 * t461 + 0.4e1 / 0.3e1 * t28 * t764)
  t769 = t300 * t768
  t771 = t31 * t129 * t440
  t775 = t31 * t271 * t440
  t779 = t183 * t271 * t440
  t783 = t183 * t438 * t440
  t786 = -0.74218500000000000000000000000000000000000000000000e1 * t701 * t685 - 0.49479000000000000000000000000000000000000000000000e1 * t706 * t685 - 0.14843700000000000000000000000000000000000000000000e2 * t710 * t685 - 0.89062200000000000000000000000000000000000000000000e2 * t713 * t695 + 0.16493000000000000000000000000000000000000000000000e1 * t718 * t685 - 0.49479000000000000000000000000000000000000000000000e1 * t722 * t685 - 0.29687400000000000000000000000000000000000000000000e2 * t725 * t695 - 0.19241833333333333333333333333333333333333333333333e2 * t728 * t733 + 0.17317650000000000000000000000000000000000000000000e2 * t688 * t740 + 0.20781180000000000000000000000000000000000000000000e3 * t728 * t744 + 0.57725500000000000000000000000000000000000000000000e1 * t725 * t740 + 0.17317650000000000000000000000000000000000000000000e2 * t713 * t740 - 0.3e1 / 0.8e1 * t769 * t771 - 0.9e1 / 0.8e1 * t466 * t775 - 0.3e1 / 0.4e1 * t301 * t779 - 0.3e1 / 0.8e1 * t444 * t783
  t788 = f.my_piecewise3(t1, 0, t698 + t786)
  t790 = r1 <= f.p.dens_threshold
  t791 = f.my_piecewise5(t19, t16, t15, t20, -t22)
  t792 = 0.1e1 + t791
  t793 = t792 <= f.p.zeta_threshold
  t794 = t792 ** (0.1e1 / 0.3e1)
  t795 = t794 ** 2
  t797 = 0.1e1 / t795 / t792
  t799 = f.my_piecewise5(t19, 0, t15, 0, -t167)
  t800 = t799 ** 2
  t804 = 0.1e1 / t795
  t805 = t804 * t799
  t807 = f.my_piecewise5(t19, 0, t15, 0, -t460)
  t811 = f.my_piecewise5(t19, 0, t15, 0, -t763)
  t815 = f.my_piecewise3(t793, 0, -0.8e1 / 0.27e2 * t797 * t800 * t799 + 0.4e1 / 0.3e1 * t805 * t807 + 0.4e1 / 0.3e1 * t794 * t811)
  t816 = t300 * t815
  t817 = r1 ** 2
  t818 = r1 ** (0.1e1 / 0.3e1)
  t819 = t818 ** 2
  t821 = 0.1e1 / t819 / t817
  t822 = s2 * t821
  t825 = s2 ** 2
  t826 = t817 ** 2
  t832 = t37 * s2 * t821
  t835 = jnp.exp(-0.27e2 / 0.80e2 * t61 * t832)
  t851 = (tau1 / t819 / r1 - t822 / 0.8e1) / (t80 + params.eta * s2 * t821 / 0.8e1)
  t852 = 0.1e1 - t851
  t854 = t852 ** 2
  t856 = jnp.exp(-t854 / 0.2e1)
  t860 = (0.7e1 / 0.12960e5 * t71 * t832 + t70 * t852 * t856 / 0.100e3) ** 2
  t868 = 0.25e1 < t851
  t869 = f.my_piecewise3(t868, 0.25e1, t851)
  t871 = t869 ** 2
  t873 = t871 * t869
  t875 = t871 ** 2
  t884 = f.my_piecewise3(t868, t851, 0.25e1)
  t888 = jnp.exp(params.c2 / (0.1e1 - t884))
  t890 = f.my_piecewise3(t851 <= 0.25e1, 0.1e1 - 0.667e0 * t869 - 0.4445555e0 * t871 - 0.663086601049e0 * t873 + 0.1451297044490e1 * t875 - 0.887998041597e0 * t875 * t869 + 0.234528941479e0 * t875 * t871 - 0.23185843322e-1 * t875 * t873, -params.d * t888)
  t894 = (0.1e1 + params.k1 * (0.1e1 - params.k1 / (params.k1 + 0.5e1 / 0.972e3 * t38 * t822 + t54 * t825 / t818 / t826 / r1 * t835 / 0.576e3 + t860))) * (0.1e1 - t890) + 0.1174e1 * t890
  t896 = jnp.sqrt(s2)
  t901 = jnp.sqrt(t138 * t896 / t818 / r1)
  t905 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t151 / t901)
  t906 = 0.1e1 - t905
  t907 = t31 * t894 * t906
  t915 = f.my_piecewise3(t793, 0, 0.4e1 / 0.9e1 * t804 * t800 + 0.4e1 / 0.3e1 * t794 * t807)
  t916 = t300 * t915
  t918 = t183 * t894 * t906
  t923 = f.my_piecewise3(t793, 0, 0.4e1 / 0.3e1 * t794 * t799)
  t924 = t300 * t923
  t926 = t472 * t894 * t906
  t930 = f.my_piecewise3(t793, t27, t794 * t792)
  t931 = t300 * t930
  t933 = t446 * t894 * t906
  t937 = f.my_piecewise3(t790, 0, -0.3e1 / 0.8e1 * t816 * t907 - 0.3e1 / 0.8e1 * t916 * t918 + t924 * t926 / 0.4e1 - 0.5e1 / 0.36e2 * t931 * t933)
  t976 = t138 * t155
  t995 = -0.12920861304452160000000000000000000000000000000000e4 * t290 * t172 * t297 - 0.12920861304452160000000000000000000000000000000000e4 * t291 * t271 * t292 * t296 - 0.23749920000000000000000000000000000000000000000000e4 * t10 * t172 * t157 - 0.23749920000000000000000000000000000000000000000000e4 * t33 * t271 * t145 * t156 - 0.79166400000000000000000000000000000000000000000000e3 * t10 * t184 * t157 + 0.83124720000000000000000000000000000000000000000000e4 * t33 * t146 * t132 / t210 * t155 - 0.32642285880000000000000000000000000000000000000000e2 * t186 * t286 - 0.97926857640000000000000000000000000000000000000000e2 * t273 * t286 + 0.21761523920000000000000000000000000000000000000000e2 * t276 * t185 * t282 + 0.32642285880000000000000000000000000000000000000000e2 * t163 * t705 * t179 - 0.97926857640000000000000000000000000000000000000000e2 * t174 * t286 + 0.17758647124527456240000000000000000000000000000000e3 * t285 * t140 / s0 * t976 + 0.48963428820000000000000000000000000000000000000000e2 * t163 * t700 * t179 + 0.97926857640000000000000000000000000000000000000000e2 * t163 * t709 * t179 + 0.32642285880000000000000000000000000000000000000000e2 * t163 * t721 * t179 + 0.48963428820000000000000000000000000000000000000000e2 * t163 * t677 * t179 + 0.65284571760000000000000000000000000000000000000000e2 * t276 * t173 * t282
  t999 = t175 * t43
  t1013 = t305 ** 2
  t1023 = t382 ** 2
  t1037 = 0.1e1 / t41 / t198
  t1038 = s0 * t1037
  t1042 = 0.1e1 / t40 / t211
  t1047 = 0.1e1 / t330
  t1054 = 0.1e1 / t41 / t210 / t198
  t1067 = t206 ** 2
  t1077 = t379 ** 2
  t1107 = t354 ** 2
  t1121 = -(0.6160e4 / 0.81e2 * tau0 * t491 - 0.2618e4 / 0.81e2 * t1038) * t85 - 0.4e1 / 0.3e1 * t534 * t226 * t228 - 0.4e1 / 0.3e1 * t346 * t352 * t356 + 0.22e2 / 0.3e1 * t536 * t359 - 0.8e1 / 0.9e1 * t223 * t544 * t548 + 0.88e2 / 0.9e1 * t538 * t551 - 0.616e3 / 0.27e2 * t348 * t554 - 0.8e1 / 0.27e2 * t78 / t543 / t84 * t1107 * t328 * t1054 + 0.44e2 / 0.9e1 * t545 * t547 * t1047 - 0.1958e4 / 0.81e2 * t353 * t355 * t1042 + 0.2618e4 / 0.81e2 * t227 * t81 * t1037
  t1129 = t362 ** 2
  t1137 = t366 ** 2
  t1138 = t70 * t1137
  t1163 = 0.9163e4 / 0.65610e5 * t71 * t62 * t1037 + t70 * t1121 * t91 / 0.100e3 - 0.3e1 / 0.25e2 * t558 * t562 - 0.9e1 / 0.50e2 * t363 * t376 - 0.9e1 / 0.100e3 * t70 * t1129 * t368 + 0.9e1 / 0.25e2 * t363 * t89 * t366 * t91 + 0.3e1 / 0.20e2 * t1138 * t368 - t1138 * t374 * t91 / 0.10e2 - t235 * t1121 * t91 / 0.100e3 + t375 * t557 * t231 * t91 / 0.25e2 + 0.3e1 / 0.100e3 * t375 * t1129 * t91 - 0.3e1 / 0.50e2 * t580 * t362 * t366 * t91 + t70 * t579 * t87 * t1137 * t91 / 0.100e3
  t1200 = -t1121
  t1201 = f.my_piecewise3(t103, 0, t1200)
  t1204 = t389 ** 2
  t1209 = 0.28143472977480e2 * t254 * t597 - 0.15914078425176e2 * t248 * t597 + 0.208986774406560e3 * t395 * t389 + 0.69662258135520e2 * t250 * t597 - 0.29214162585720e2 * t407 * t389 - 0.3895221678096e1 * t256 * t597 - 0.319679294974920e3 * t399 * t389 - 0.71039843327760e2 * t252 * t597 + 0.168860837864880e3 * t403 * t389 - 0.23871117637764e2 * t391 * t389 - 0.35564440e1 * t246 * t597 - 0.4439990207985e1 * t110 * t1201 - 0.53279882495820e2 * t108 * t1204 - 0.1989259803147e1 * t106 * t1201
  t1216 = t391 ** 2
  t1236 = 0.5805188177960e1 * t108 * t1201 + 0.1407173648874e1 * t112 * t1201 - 0.162300903254e0 * t114 * t1201 - 0.106559764991640e3 * t104 * t1216 - 0.8891110e0 * t104 * t1201 + 0.84430418932440e2 * t106 * t1216 + 0.52246693601640e2 * t106 * t1204 - 0.11935558818882e2 * t104 * t1204 - 0.19476108390480e2 * t108 * t1216 - 0.2921416258572e1 * t112 * t1204 + 0.21107604733110e2 * t110 * t1204 - 0.667e0 * t1201 - 0.26673330e1 * t1204 + 0.34831129067760e2 * t1216
  t1238 = t418 ** 2
  t1245 = t418 * t123 * t423
  t1252 = t423 ** 2
  t1260 = t640 * t650
  t1269 = f.my_piecewise3(t103, t1200, 0)
  t1282 = t427 ** 2
  t1284 = t429 ** 2
  t1289 = -0.24e2 * t261 * t645 * t1238 * t123 - 0.36e2 * t261 * t430 * t1245 - 0.36e2 * t428 * t660 * t1238 * t123 - 0.6e1 * t261 * t417 * t1252 * t123 - 0.36e2 * t428 * t645 * t1245 - 0.8e1 * t639 * t1260 - 0.12e2 * t658 / t429 / t416 * t1238 * t123 - t261 * t263 * t1269 * t123 - 0.4e1 * t654 * t1260 - 0.3e1 * t428 * t430 * t1252 * t123 - 0.6e1 * t658 * t660 * t1245 - params.d * t1282 / t1284 * t1238 * t123
  t1290 = f.my_piecewise3(t102, t1209 + t1236, t1289)
  t1293 = -0.24e2 * t189 / t477 / t96 * t1013 * t126 + 0.36e2 * t479 * t306 * t382 - 0.24e2 * t479 * t480 * t268 - 0.6e1 * t304 * t1023 * t126 + 0.24e2 * t304 * t385 * t382 - 0.8e1 * t304 * t243 * t587 + 0.12e2 * t304 * t305 * t435 + t192 * (0.26180e5 / 0.19683e5 * t38 * t1038 + 0.5225e4 / 0.1458e4 * t54 * t55 * t1042 * t66 - 0.5929e4 / 0.288e3 * t208 * t209 * t1047 * t66 + 0.2949e4 / 0.640e3 * t329 * t1054 * t34 * t334 - 0.1053e4 / 0.3200e4 * t517 / t40 / t518 / r0 * t50 * t522 + 0.6561e4 / 0.160000e6 * t514 * t49 / t1067 * t328 * t55 / t518 / t56 * t66 + 0.6e1 * t1077 + 0.8e1 * t239 * t584 + 0.2e1 * t94 * t1163) * t126 - 0.4e1 * t192 * t587 * t268 - 0.6e1 * t192 * t382 * t435 - 0.4e1 * t192 * t242 * t665 - t101 * t1290 + 0.1174e1 * t1290
  t1308 = 0.1e1 / t182 / t456
  t1331 = t24 ** 2
  t1334 = t453 ** 2
  t1340 = t461 ** 2
  t1349 = -0.24e2 * t760 + 0.24e2 * t21 / t759 / t11
  t1350 = f.my_piecewise5(t15, 0, t19, 0, t1349)
  t1354 = f.my_piecewise3(t25, 0, 0.40e2 / 0.81e2 / t451 / t1331 * t1334 - 0.16e2 / 0.9e1 * t752 * t453 * t461 + 0.4e1 / 0.3e1 * t452 * t1340 + 0.16e2 / 0.9e1 * t756 * t764 + 0.4e1 / 0.3e1 * t28 * t1350)
  t1360 = 0.65284571760000000000000000000000000000000000000000e2 * t276 * t272 * t282 - 0.87046095680000000000000000000000000000000000000001e2 * t278 * t279 * t999 * t155 + 0.10427396878333333333333333333333333333333333333333e3 * t285 * t999 * t178 - 0.10880761960000000000000000000000000000000000000000e2 * t163 * t717 * t179 - 0.3e1 / 0.8e1 * t444 * t31 * t1293 * t440 + 0.12920861304452160000000000000000000000000000000000e4 * t291 * t129 * t134 * t296 - 0.43069537681507200000000000000000000000000000000000e3 * t290 * t184 * t297 - 0.3e1 / 0.2e1 * t301 * t783 + 0.10e2 / 0.27e2 * t444 * t1308 * t129 * t440 - 0.5e1 / 0.9e1 * t301 * t448 + t466 * t474 / 0.2e1 + t444 * t472 * t438 * t440 / 0.2e1 - 0.3e1 / 0.2e1 * t466 * t779 - 0.9e1 / 0.4e1 * t466 * t441 - t444 * t183 * t668 * t440 / 0.2e1 - 0.3e1 / 0.2e1 * t301 * t670 - 0.3e1 / 0.8e1 * t300 * t1354 * t771 - t769 * t468 / 0.2e1
  t1417 = -0.5e1 / 0.9e1 * t444 * t446 * t271 * t440 - 0.3e1 / 0.2e1 * t769 * t775 + t301 * t674 - 0.98958000000000000000000000000000000000000000000000e1 * t290 * t184 * t438 * t685 + 0.34635300000000000000000000000000000000000000000000e2 * t701 * t740 + 0.23090200000000000000000000000000000000000000000000e2 * t706 * t740 + 0.34635300000000000000000000000000000000000000000000e2 * t678 * t740 - 0.17812440000000000000000000000000000000000000000000e3 * t701 * t695 - 0.11874960000000000000000000000000000000000000000000e3 * t706 * t695 - 0.35624880000000000000000000000000000000000000000000e3 * t710 * t695 - 0.98958000000000000000000000000000000000000000000000e1 * t290 * t32 * t668 * t685 - 0.98958000000000000000000000000000000000000000000000e1 * t290 * t465 * t183 * t129 * t685 + 0.65972000000000000000000000000000000000000000000000e1 * t290 * t171 * t472 * t129 * t685 - 0.98958000000000000000000000000000000000000000000000e1 * t290 * t768 * t31 * t129 * t685 - 0.29687400000000000000000000000000000000000000000000e2 * t290 * t172 * t438 * t685 - 0.36651111111111111111111111111111111111111111111111e1 * t290 * t30 * t446 * t129 * t685 + 0.65972000000000000000000000000000000000000000000000e1 * t290 * t716 * t271 * t685
  t1476 = -0.19791600000000000000000000000000000000000000000000e2 * t290 * t704 * t271 * t685 - 0.29687400000000000000000000000000000000000000000000e2 * t290 * t699 * t271 * t685 - 0.76967333333333333333333333333333333333333333333333e2 * t10 * t277 / t143 / t50 / t53 / t60 * t55 * t1042 * t976 - 0.64604306522260800000000000000000000000000000000000e3 * t728 * t59 * t691 * t155 * t138 * t131 - 0.17812440000000000000000000000000000000000000000000e3 * t678 * t695 + 0.83124720000000000000000000000000000000000000000000e3 * t688 * t744 + 0.39583200000000000000000000000000000000000000000000e2 * t718 * t695 - 0.76967333333333333333333333333333333333333333333333e2 * t713 * t733 - 0.76967333333333333333333333333333333333333333333333e2 * t688 * t733 - 0.14085022000000000000000000000000000000000000000000e4 * t728 * t693 * t1038 * t155 + 0.27708240000000000000000000000000000000000000000000e3 * t725 * t744 - 0.25655777777777777777777777777777777777777777777777e2 * t725 * t733 + 0.83381277777777777777777777777777777777777777777776e2 * t728 * t680 * t131 * t59 * t155 - 0.76967333333333333333333333333333333333333333333334e1 * t718 * t740 + 0.23090200000000000000000000000000000000000000000000e2 * t722 * t740 + 0.69270600000000000000000000000000000000000000000000e2 * t710 * t740 + 0.83124720000000000000000000000000000000000000000000e3 * t713 * t744 - 0.11874960000000000000000000000000000000000000000000e3 * t722 * t695
  t1479 = f.my_piecewise3(t1, 0, t995 + t1360 + t1417 + t1476)
  t1480 = t792 ** 2
  t1483 = t800 ** 2
  t1489 = t807 ** 2
  t1495 = f.my_piecewise5(t19, 0, t15, 0, -t1349)
  t1499 = f.my_piecewise3(t793, 0, 0.40e2 / 0.81e2 / t795 / t1480 * t1483 - 0.16e2 / 0.9e1 * t797 * t800 * t807 + 0.4e1 / 0.3e1 * t804 * t1489 + 0.16e2 / 0.9e1 * t805 * t811 + 0.4e1 / 0.3e1 * t794 * t1495)
  t1514 = f.my_piecewise3(t790, 0, -0.3e1 / 0.8e1 * t300 * t1499 * t907 - t816 * t918 / 0.2e1 + t916 * t926 / 0.2e1 - 0.5e1 / 0.9e1 * t924 * t933 + 0.10e2 / 0.27e2 * t931 * t1308 * t894 * t906)
  d1111 = 0.4e1 * t788 + 0.4e1 * t937 + t11 * (t1479 + t1514)

  res = {'v4rho4': d1111}
  return res
