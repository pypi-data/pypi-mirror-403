"""Generated from mgga_x_scan.mpl."""

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

  scan_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  scan_f_alpha_left0 = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  scan_f_alpha_left_cutoff = -jnp.log(DBL_EPSILON) / (-jnp.log(DBL_EPSILON) + params_c1)

  scan_f_alpha_right0 = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  scan_f_alpha_right_cutoff = (-jnp.log(DBL_EPSILON / jnp.abs(params_d)) + params_c2) / -jnp.log(DBL_EPSILON / jnp.abs(params_d))

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_b2 = jnp.sqrt(5913 / 405000)

  scan_b3 = 1 / 2

  scan_a1 = 4.9479

  scan_h0x = 1.174

  scan_f_alpha_left = lambda a: f.my_piecewise3(a > scan_f_alpha_left_cutoff, 0, scan_f_alpha_left0(jnp.minimum(scan_f_alpha_left_cutoff, a)))

  scan_f_alpha_right = lambda a: f.my_piecewise3(a < scan_f_alpha_right_cutoff, 0, scan_f_alpha_right0(jnp.maximum(scan_f_alpha_right_cutoff, a)))

  scan_b1 = 511 / 13500 / (2 * scan_b2)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  scan_f_alpha = lambda a: f.my_piecewise3(a <= 1, scan_f_alpha_left(a), scan_f_alpha_right(a))

  scan_b4 = MU_GE ** 2 / params_k1 - 1606 / 18225 - scan_b1 ** 2

  scan_y = lambda x, a: MU_GE * scan_p(x) + scan_b4 * scan_p(x) ** 2 * jnp.exp(-scan_b4 * scan_p(x) / MU_GE) + (scan_b1 * scan_p(x) + scan_b2 * (1 - a) * jnp.exp(-scan_b3 * (1 - a) ** 2)) ** 2

  scan_f = lambda x, u, t: (scan_h1x(scan_y(x, scan_alpha(x, t))) * (1 - scan_f_alpha(scan_alpha(x, t))) + scan_h0x * scan_f_alpha(scan_alpha(x, t))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  scan_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  scan_f_alpha_left0 = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  scan_f_alpha_left_cutoff = -jnp.log(DBL_EPSILON) / (-jnp.log(DBL_EPSILON) + params_c1)

  scan_f_alpha_right0 = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  scan_f_alpha_right_cutoff = (-jnp.log(DBL_EPSILON / jnp.abs(params_d)) + params_c2) / -jnp.log(DBL_EPSILON / jnp.abs(params_d))

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_b2 = jnp.sqrt(5913 / 405000)

  scan_b3 = 1 / 2

  scan_a1 = 4.9479

  scan_h0x = 1.174

  scan_f_alpha_left = lambda a: f.my_piecewise3(a > scan_f_alpha_left_cutoff, 0, scan_f_alpha_left0(jnp.minimum(scan_f_alpha_left_cutoff, a)))

  scan_f_alpha_right = lambda a: f.my_piecewise3(a < scan_f_alpha_right_cutoff, 0, scan_f_alpha_right0(jnp.maximum(scan_f_alpha_right_cutoff, a)))

  scan_b1 = 511 / 13500 / (2 * scan_b2)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  scan_f_alpha = lambda a: f.my_piecewise3(a <= 1, scan_f_alpha_left(a), scan_f_alpha_right(a))

  scan_b4 = MU_GE ** 2 / params_k1 - 1606 / 18225 - scan_b1 ** 2

  scan_y = lambda x, a: MU_GE * scan_p(x) + scan_b4 * scan_p(x) ** 2 * jnp.exp(-scan_b4 * scan_p(x) / MU_GE) + (scan_b1 * scan_p(x) + scan_b2 * (1 - a) * jnp.exp(-scan_b3 * (1 - a) ** 2)) ** 2

  scan_f = lambda x, u, t: (scan_h1x(scan_y(x, scan_alpha(x, t))) * (1 - scan_f_alpha(scan_alpha(x, t))) + scan_h0x * scan_f_alpha(scan_alpha(x, t))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  scan_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  scan_f_alpha_left0 = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  scan_f_alpha_left_cutoff = -jnp.log(DBL_EPSILON) / (-jnp.log(DBL_EPSILON) + params_c1)

  scan_f_alpha_right0 = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  scan_f_alpha_right_cutoff = (-jnp.log(DBL_EPSILON / jnp.abs(params_d)) + params_c2) / -jnp.log(DBL_EPSILON / jnp.abs(params_d))

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_b2 = jnp.sqrt(5913 / 405000)

  scan_b3 = 1 / 2

  scan_a1 = 4.9479

  scan_h0x = 1.174

  scan_f_alpha_left = lambda a: f.my_piecewise3(a > scan_f_alpha_left_cutoff, 0, scan_f_alpha_left0(jnp.minimum(scan_f_alpha_left_cutoff, a)))

  scan_f_alpha_right = lambda a: f.my_piecewise3(a < scan_f_alpha_right_cutoff, 0, scan_f_alpha_right0(jnp.maximum(scan_f_alpha_right_cutoff, a)))

  scan_b1 = 511 / 13500 / (2 * scan_b2)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  scan_f_alpha = lambda a: f.my_piecewise3(a <= 1, scan_f_alpha_left(a), scan_f_alpha_right(a))

  scan_b4 = MU_GE ** 2 / params_k1 - 1606 / 18225 - scan_b1 ** 2

  scan_y = lambda x, a: MU_GE * scan_p(x) + scan_b4 * scan_p(x) ** 2 * jnp.exp(-scan_b4 * scan_p(x) / MU_GE) + (scan_b1 * scan_p(x) + scan_b2 * (1 - a) * jnp.exp(-scan_b3 * (1 - a) ** 2)) ** 2

  scan_f = lambda x, u, t: (scan_h1x(scan_y(x, scan_alpha(x, t))) * (1 - scan_f_alpha(scan_alpha(x, t))) + scan_h0x * scan_f_alpha(scan_alpha(x, t))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t76 = 0.5e1 / 0.9e1 * (tau0 * t70 - t39 / 0.8e1) * t28 * t32
  t77 = 0.1e1 - t76
  t79 = t77 ** 2
  t81 = jnp.exp(-t79 / 0.2e1)
  t84 = 0.7e1 / 0.12960e5 * t66 * t58 + t65 * t77 * t81 / 0.100e3
  t85 = t84 ** 2
  t86 = params.k1 + 0.5e1 / 0.972e3 * t33 * t39 + t49 * t50 * t54 * t61 / 0.576e3 + t85
  t91 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t86)
  t92 = t76 <= 0.1e1
  t93 = jnp.log(DBL_EPSILON)
  t96 = t93 / (-t93 + params.c1)
  t97 = -t96 < t76
  t98 = t76 < -t96
  t99 = f.my_piecewise3(t98, t76, -t96)
  t100 = params.c1 * t99
  t101 = 0.1e1 - t99
  t102 = 0.1e1 / t101
  t104 = jnp.exp(-t100 * t102)
  t105 = f.my_piecewise3(t97, 0, t104)
  t106 = abs(params.d)
  t109 = jnp.log(DBL_EPSILON / t106)
  t112 = (-t109 + params.c2) / t109
  t113 = t76 < -t112
  t114 = f.my_piecewise3(t113, -t112, t76)
  t115 = 0.1e1 - t114
  t118 = jnp.exp(params.c2 / t115)
  t120 = f.my_piecewise3(t113, 0, -params.d * t118)
  t121 = f.my_piecewise3(t92, t105, t120)
  t122 = 0.1e1 - t121
  t125 = t91 * t122 + 0.1174e1 * t121
  t127 = jnp.sqrt(0.3e1)
  t128 = 0.1e1 / t30
  t129 = t45 * t128
  t130 = jnp.sqrt(s0)
  t132 = 0.1e1 / t35 / r0
  t134 = t129 * t130 * t132
  t135 = jnp.sqrt(t134)
  t139 = jnp.exp(-0.98958e1 * t127 / t135)
  t140 = 0.1e1 - t139
  t141 = t27 * t125 * t140
  t144 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t141)
  t145 = r1 <= f.p.dens_threshold
  t146 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t147 = 0.1e1 + t146
  t148 = t147 <= f.p.zeta_threshold
  t149 = t147 ** (0.1e1 / 0.3e1)
  t151 = f.my_piecewise3(t148, t22, t149 * t147)
  t152 = t5 * t151
  t153 = r1 ** 2
  t154 = r1 ** (0.1e1 / 0.3e1)
  t155 = t154 ** 2
  t157 = 0.1e1 / t155 / t153
  t158 = s2 * t157
  t161 = s2 ** 2
  t162 = t153 ** 2
  t165 = 0.1e1 / t154 / t162 / r1
  t167 = t32 * s2
  t168 = t167 * t157
  t171 = jnp.exp(-0.27e2 / 0.80e2 * t56 * t168)
  t178 = 0.1e1 / t155 / r1
  t184 = 0.5e1 / 0.9e1 * (tau1 * t178 - t158 / 0.8e1) * t28 * t32
  t185 = 0.1e1 - t184
  t187 = t185 ** 2
  t189 = jnp.exp(-t187 / 0.2e1)
  t192 = 0.7e1 / 0.12960e5 * t66 * t168 + t65 * t185 * t189 / 0.100e3
  t193 = t192 ** 2
  t194 = params.k1 + 0.5e1 / 0.972e3 * t33 * t158 + t49 * t161 * t165 * t171 / 0.576e3 + t193
  t199 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t194)
  t200 = t184 <= 0.1e1
  t201 = -t96 < t184
  t202 = t184 < -t96
  t203 = f.my_piecewise3(t202, t184, -t96)
  t204 = params.c1 * t203
  t205 = 0.1e1 - t203
  t206 = 0.1e1 / t205
  t208 = jnp.exp(-t204 * t206)
  t209 = f.my_piecewise3(t201, 0, t208)
  t210 = t184 < -t112
  t211 = f.my_piecewise3(t210, -t112, t184)
  t212 = 0.1e1 - t211
  t215 = jnp.exp(params.c2 / t212)
  t217 = f.my_piecewise3(t210, 0, -params.d * t215)
  t218 = f.my_piecewise3(t200, t209, t217)
  t219 = 0.1e1 - t218
  t222 = t199 * t219 + 0.1174e1 * t218
  t224 = jnp.sqrt(s2)
  t226 = 0.1e1 / t154 / r1
  t228 = t129 * t224 * t226
  t229 = jnp.sqrt(t228)
  t233 = jnp.exp(-0.98958e1 * t127 / t229)
  t234 = 0.1e1 - t233
  t235 = t27 * t222 * t234
  t238 = f.my_piecewise3(t145, 0, -0.3e1 / 0.8e1 * t152 * t235)
  t239 = t6 ** 2
  t241 = t16 / t239
  t242 = t7 - t241
  t243 = f.my_piecewise5(t10, 0, t14, 0, t242)
  t246 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t243)
  t250 = t27 ** 2
  t251 = 0.1e1 / t250
  t255 = t26 * t251 * t125 * t140 / 0.8e1
  t256 = params.k1 ** 2
  t257 = t86 ** 2
  t259 = t256 / t257
  t262 = 0.1e1 / t36 / t34 / r0
  t263 = s0 * t262
  t273 = t44 ** 2
  t274 = t29 ** 2
  t276 = t273 / t274
  t278 = t51 ** 2
  t291 = -0.5e1 / 0.3e1 * tau0 * t38 + t263 / 0.3e1
  t293 = t33 * t81
  t296 = t65 * t79
  t308 = 0.5e1 / 0.9e1 * t291 * t28 * t32
  t309 = f.my_piecewise3(t98, t308, 0)
  t312 = t101 ** 2
  t313 = 0.1e1 / t312
  t318 = f.my_piecewise3(t97, 0, (-t100 * t313 * t309 - params.c1 * t309 * t102) * t104)
  t319 = params.d * params.c2
  t320 = t115 ** 2
  t321 = 0.1e1 / t320
  t322 = f.my_piecewise3(t113, 0, t308)
  t326 = f.my_piecewise3(t113, 0, -t319 * t321 * t322 * t118)
  t327 = f.my_piecewise3(t92, t318, t326)
  t335 = 3 ** (0.1e1 / 0.6e1)
  t336 = t335 ** 2
  t337 = t336 ** 2
  t339 = t337 * t335 * t4
  t342 = t339 * t25 * t27 * t125
  t346 = 0.1e1 / t135 / t134 * t45 * t128
  t355 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t246 * t141 - t255 - 0.3e1 / 0.8e1 * t26 * t27 * (t259 * (-0.10e2 / 0.729e3 * t33 * t263 - t49 * t50 / t35 / t51 / t34 * t61 / 0.108e3 + 0.3e1 / 0.320e3 * t276 * t50 * s0 / t278 / r0 * t61 + 0.2e1 * t84 * (-0.7e1 / 0.4860e4 * t66 * t57 * t262 - t65 * t291 * t293 / 0.180e3 + t296 * t291 * t293 / 0.180e3)) * t122 - t91 * t327 + 0.1174e1 * t327) * t140 - 0.24739500000000000000000000000000000000000000000000e1 * t342 * t346 * t130 / t35 / t34 * t139)
  t357 = f.my_piecewise5(t14, 0, t10, 0, -t242)
  t360 = f.my_piecewise3(t148, 0, 0.4e1 / 0.3e1 * t149 * t357)
  t367 = t152 * t251 * t222 * t234 / 0.8e1
  t369 = f.my_piecewise3(t145, 0, -0.3e1 / 0.8e1 * t5 * t360 * t235 - t367)
  vrho_0_ = t144 + t238 + t6 * (t355 + t369)
  t372 = -t7 - t241
  t373 = f.my_piecewise5(t10, 0, t14, 0, t372)
  t376 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t373)
  t381 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t376 * t141 - t255)
  t383 = f.my_piecewise5(t14, 0, t10, 0, -t372)
  t386 = f.my_piecewise3(t148, 0, 0.4e1 / 0.3e1 * t149 * t383)
  t390 = t194 ** 2
  t392 = t256 / t390
  t395 = 0.1e1 / t155 / t153 / r1
  t396 = s2 * t395
  t407 = t162 ** 2
  t420 = -0.5e1 / 0.3e1 * tau1 * t157 + t396 / 0.3e1
  t422 = t33 * t189
  t425 = t65 * t187
  t437 = 0.5e1 / 0.9e1 * t420 * t28 * t32
  t438 = f.my_piecewise3(t202, t437, 0)
  t441 = t205 ** 2
  t442 = 0.1e1 / t441
  t447 = f.my_piecewise3(t201, 0, (-t204 * t442 * t438 - params.c1 * t438 * t206) * t208)
  t448 = t212 ** 2
  t449 = 0.1e1 / t448
  t450 = f.my_piecewise3(t210, 0, t437)
  t454 = f.my_piecewise3(t210, 0, -t319 * t449 * t450 * t215)
  t455 = f.my_piecewise3(t200, t447, t454)
  t465 = t339 * t151 * t27 * t222
  t469 = 0.1e1 / t229 / t228 * t45 * t128
  t478 = f.my_piecewise3(t145, 0, -0.3e1 / 0.8e1 * t5 * t386 * t235 - t367 - 0.3e1 / 0.8e1 * t152 * t27 * (t392 * (-0.10e2 / 0.729e3 * t33 * t396 - t49 * t161 / t154 / t162 / t153 * t171 / 0.108e3 + 0.3e1 / 0.320e3 * t276 * t161 * s2 / t407 / r1 * t171 + 0.2e1 * t192 * (-0.7e1 / 0.4860e4 * t66 * t167 * t395 - t65 * t420 * t422 / 0.180e3 + t425 * t420 * t422 / 0.180e3)) * t219 - t199 * t455 + 0.1174e1 * t455) * t234 - 0.24739500000000000000000000000000000000000000000000e1 * t465 * t469 * t224 / t154 / t153 * t233)
  vrho_1_ = t144 + t238 + t6 * (t381 + t478)
  t482 = t38 * t28 * t32
  t508 = 0.5e1 / 0.72e2 * t482
  t509 = f.my_piecewise3(t98, -t508, 0)
  t516 = f.my_piecewise3(t97, 0, (-t100 * t313 * t509 - params.c1 * t509 * t102) * t104)
  t517 = f.my_piecewise3(t113, 0, -t508)
  t521 = f.my_piecewise3(t113, 0, -t319 * t321 * t517 * t118)
  t522 = f.my_piecewise3(t92, t516, t521)
  t537 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (t259 * (0.5e1 / 0.972e3 * t482 + t49 * s0 * t54 * t61 / 0.288e3 - 0.9e1 / 0.2560e4 * t276 * t50 / t278 * t61 + 0.2e1 * t84 * (0.7e1 / 0.12960e5 * t66 * t32 * t38 + t65 * t38 * t293 / 0.1440e4 - t296 * t38 * t293 / 0.1440e4)) * t122 - t91 * t522 + 0.1174e1 * t522) * t140 + 0.92773125000000000000000000000000000000000000000000e0 * t342 * t346 / t130 * t132 * t139)
  vsigma_0_ = t6 * t537
  vsigma_1_ = 0.0e0
  t539 = t157 * t28 * t32
  t565 = 0.5e1 / 0.72e2 * t539
  t566 = f.my_piecewise3(t202, -t565, 0)
  t573 = f.my_piecewise3(t201, 0, (-t204 * t442 * t566 - params.c1 * t566 * t206) * t208)
  t574 = f.my_piecewise3(t210, 0, -t565)
  t578 = f.my_piecewise3(t210, 0, -t319 * t449 * t574 * t215)
  t579 = f.my_piecewise3(t200, t573, t578)
  t594 = f.my_piecewise3(t145, 0, -0.3e1 / 0.8e1 * t152 * t27 * (t392 * (0.5e1 / 0.972e3 * t539 + t49 * s2 * t165 * t171 / 0.288e3 - 0.9e1 / 0.2560e4 * t276 * t161 / t407 * t171 + 0.2e1 * t192 * (0.7e1 / 0.12960e5 * t66 * t32 * t157 + t65 * t157 * t422 / 0.1440e4 - t425 * t157 * t422 / 0.1440e4)) * t219 - t199 * t579 + 0.1174e1 * t579) * t234 + 0.92773125000000000000000000000000000000000000000000e0 * t465 * t469 / t224 * t226 * t233)
  vsigma_2_ = t6 * t594
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t607 = 0.5e1 / 0.9e1 * t70 * t28 * t32
  t608 = f.my_piecewise3(t98, t607, 0)
  t615 = f.my_piecewise3(t97, 0, (-t100 * t313 * t608 - params.c1 * t608 * t102) * t104)
  t616 = f.my_piecewise3(t113, 0, t607)
  t620 = f.my_piecewise3(t113, 0, -t319 * t321 * t616 * t118)
  t621 = f.my_piecewise3(t92, t615, t620)
  t629 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (0.2e1 * t259 * t84 * (t296 * t70 * t293 / 0.180e3 - t65 * t70 * t293 / 0.180e3) * t122 - t91 * t621 + 0.1174e1 * t621) * t140)
  vtau_0_ = t6 * t629
  t642 = 0.5e1 / 0.9e1 * t178 * t28 * t32
  t643 = f.my_piecewise3(t202, t642, 0)
  t650 = f.my_piecewise3(t201, 0, (-t204 * t442 * t643 - params.c1 * t643 * t206) * t208)
  t651 = f.my_piecewise3(t210, 0, t642)
  t655 = f.my_piecewise3(t210, 0, -t319 * t449 * t651 * t215)
  t656 = f.my_piecewise3(t200, t650, t655)
  t664 = f.my_piecewise3(t145, 0, -0.3e1 / 0.8e1 * t152 * t27 * (0.2e1 * t392 * t192 * (t425 * t178 * t422 / 0.180e3 - t65 * t178 * t422 / 0.180e3) * t219 - t199 * t656 + 0.1174e1 * t656) * t234)
  vtau_1_ = t6 * t664
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

  scan_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  scan_f_alpha_left0 = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  scan_f_alpha_left_cutoff = -jnp.log(DBL_EPSILON) / (-jnp.log(DBL_EPSILON) + params_c1)

  scan_f_alpha_right0 = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  scan_f_alpha_right_cutoff = (-jnp.log(DBL_EPSILON / jnp.abs(params_d)) + params_c2) / -jnp.log(DBL_EPSILON / jnp.abs(params_d))

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_b2 = jnp.sqrt(5913 / 405000)

  scan_b3 = 1 / 2

  scan_a1 = 4.9479

  scan_h0x = 1.174

  scan_f_alpha_left = lambda a: f.my_piecewise3(a > scan_f_alpha_left_cutoff, 0, scan_f_alpha_left0(jnp.minimum(scan_f_alpha_left_cutoff, a)))

  scan_f_alpha_right = lambda a: f.my_piecewise3(a < scan_f_alpha_right_cutoff, 0, scan_f_alpha_right0(jnp.maximum(scan_f_alpha_right_cutoff, a)))

  scan_b1 = 511 / 13500 / (2 * scan_b2)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  scan_f_alpha = lambda a: f.my_piecewise3(a <= 1, scan_f_alpha_left(a), scan_f_alpha_right(a))

  scan_b4 = MU_GE ** 2 / params_k1 - 1606 / 18225 - scan_b1 ** 2

  scan_y = lambda x, a: MU_GE * scan_p(x) + scan_b4 * scan_p(x) ** 2 * jnp.exp(-scan_b4 * scan_p(x) / MU_GE) + (scan_b1 * scan_p(x) + scan_b2 * (1 - a) * jnp.exp(-scan_b3 * (1 - a) ** 2)) ** 2

  scan_f = lambda x, u, t: (scan_h1x(scan_y(x, scan_alpha(x, t))) * (1 - scan_f_alpha(scan_alpha(x, t))) + scan_h0x * scan_f_alpha(scan_alpha(x, t))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t72 = 0.5e1 / 0.9e1 * (t64 * t66 - t33 / 0.8e1) * t20 * t24
  t73 = 0.1e1 - t72
  t75 = t73 ** 2
  t77 = jnp.exp(-t75 / 0.2e1)
  t80 = 0.7e1 / 0.12960e5 * t61 * t33 + t59 * t73 * t77 / 0.100e3
  t81 = t80 ** 2
  t82 = params.k1 + 0.5e1 / 0.972e3 * t25 * t33 + t43 * t45 * t55 / 0.288e3 + t81
  t87 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t82)
  t88 = t72 <= 0.1e1
  t89 = jnp.log(DBL_EPSILON)
  t92 = t89 / (-t89 + params.c1)
  t93 = -t92 < t72
  t94 = t72 < -t92
  t95 = f.my_piecewise3(t94, t72, -t92)
  t96 = params.c1 * t95
  t97 = 0.1e1 - t95
  t98 = 0.1e1 / t97
  t100 = jnp.exp(-t96 * t98)
  t101 = f.my_piecewise3(t93, 0, t100)
  t102 = abs(params.d)
  t105 = jnp.log(DBL_EPSILON / t102)
  t108 = (-t105 + params.c2) / t105
  t109 = t72 < -t108
  t110 = f.my_piecewise3(t109, -t108, t72)
  t111 = 0.1e1 - t110
  t114 = jnp.exp(params.c2 / t111)
  t116 = f.my_piecewise3(t109, 0, -params.d * t114)
  t117 = f.my_piecewise3(t88, t101, t116)
  t118 = 0.1e1 - t117
  t121 = t87 * t118 + 0.1174e1 * t117
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
  t148 = t82 ** 2
  t150 = t147 / t148
  t154 = t28 / t30 / t29 / r0
  t164 = t38 ** 2
  t165 = t21 ** 2
  t167 = t164 / t165
  t169 = t46 ** 2
  t181 = -0.5e1 / 0.3e1 * t64 * t32 + t154 / 0.3e1
  t183 = t25 * t77
  t186 = t59 * t75
  t198 = 0.5e1 / 0.9e1 * t181 * t20 * t24
  t199 = f.my_piecewise3(t94, t198, 0)
  t202 = t97 ** 2
  t203 = 0.1e1 / t202
  t208 = f.my_piecewise3(t93, 0, (-t96 * t203 * t199 - params.c1 * t199 * t98) * t100)
  t209 = params.d * params.c2
  t210 = t111 ** 2
  t211 = 0.1e1 / t210
  t212 = f.my_piecewise3(t109, 0, t198)
  t216 = f.my_piecewise3(t109, 0, -t209 * t211 * t212 * t114)
  t217 = f.my_piecewise3(t88, t208, t216)
  t225 = 3 ** (0.1e1 / 0.6e1)
  t226 = t225 ** 2
  t227 = t226 ** 2
  t229 = t227 * t225 * t5
  t237 = 0.1e1 / t132 / t131 * t39 * t124
  t243 = f.my_piecewise3(t2, 0, -t18 / t30 * t121 * t137 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (t150 * (-0.10e2 / 0.729e3 * t25 * t154 - t43 * t45 / t19 / t46 / t29 * t54 / 0.54e2 + 0.3e1 / 0.80e2 * t167 * t44 * s0 / t169 / r0 * t54 + 0.2e1 * t80 * (-0.7e1 / 0.4860e4 * t61 * t154 - t59 * t181 * t183 / 0.180e3 + t186 * t181 * t183 / 0.180e3)) * t118 - t87 * t217 + 0.1174e1 * t217) * t137 - 0.24739500000000000000000000000000000000000000000000e1 * t229 * t17 / t29 * t121 * t237 * t127 * t136)
  vrho_0_ = 0.2e1 * r0 * t243 + 0.2e1 * t141
  t247 = t27 * t32 * t25
  t262 = t59 * t27
  t266 = t186 * t27
  t268 = t24 * t77
  t278 = 0.5e1 / 0.72e2 * t247
  t279 = f.my_piecewise3(t94, -t278, 0)
  t286 = f.my_piecewise3(t93, 0, (-t96 * t203 * t279 - params.c1 * t279 * t98) * t100)
  t287 = f.my_piecewise3(t109, 0, -t278)
  t291 = f.my_piecewise3(t109, 0, -t209 * t211 * t287 * t114)
  t292 = f.my_piecewise3(t88, t286, t291)
  t311 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (t150 * (0.5e1 / 0.972e3 * t247 + t43 * s0 * t26 * t55 / 0.144e3 - 0.9e1 / 0.640e3 * t167 * t44 / t169 * t54 + 0.2e1 * t80 * (0.7e1 / 0.12960e5 * t60 * t24 * t27 * t32 + t262 * t32 * t183 / 0.1440e4 - t266 * t32 * t20 * t268 / 0.1440e4)) * t118 - t87 * t292 + 0.1174e1 * t292) * t137 + 0.92773125000000000000000000000000000000000000000000e0 * t229 * t17 / r0 * t121 * t237 / t126 * t26 * t136)
  vsigma_0_ = 0.2e1 * r0 * t311
  vlapl_0_ = 0.0e0
  t326 = 0.5e1 / 0.9e1 * t27 * t66 * t25
  t327 = f.my_piecewise3(t94, t326, 0)
  t334 = f.my_piecewise3(t93, 0, (-t96 * t203 * t327 - params.c1 * t327 * t98) * t100)
  t335 = f.my_piecewise3(t109, 0, t326)
  t339 = f.my_piecewise3(t109, 0, -t209 * t211 * t335 * t114)
  t340 = f.my_piecewise3(t88, t334, t339)
  t348 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (0.2e1 * t150 * t80 * (t266 * t66 * t20 * t268 / 0.180e3 - t262 * t66 * t183 / 0.180e3) * t118 - t87 * t340 + 0.1174e1 * t340) * t137)
  vtau_0_ = 0.2e1 * r0 * t348
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
  t43 = 0.1e1 / t24 / t23
  t44 = t39 * t40 * t43
  t45 = s0 ** 2
  t46 = t45 * t28
  t47 = t31 ** 2
  t55 = jnp.exp(-0.27e2 / 0.80e2 * t39 * t22 * t26 * t34)
  t60 = jnp.sqrt(0.146e3)
  t62 = t60 * t22 * t26
  t65 = tau0 * t29
  t67 = 0.1e1 / t20 / r0
  t73 = 0.5e1 / 0.9e1 * (t65 * t67 - t34 / 0.8e1) * t22 * t26
  t74 = 0.1e1 - t73
  t76 = t74 ** 2
  t78 = jnp.exp(-t76 / 0.2e1)
  t81 = 0.7e1 / 0.12960e5 * t62 * t34 + t60 * t74 * t78 / 0.100e3
  t82 = t81 ** 2
  t83 = params.k1 + 0.5e1 / 0.972e3 * t35 + t44 * t46 / t19 / t47 / r0 * t55 / 0.288e3 + t82
  t88 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t83)
  t89 = t73 <= 0.1e1
  t90 = jnp.log(DBL_EPSILON)
  t93 = t90 / (-t90 + params.c1)
  t94 = -t93 < t73
  t95 = t73 < -t93
  t96 = f.my_piecewise3(t95, t73, -t93)
  t97 = params.c1 * t96
  t98 = 0.1e1 - t96
  t99 = 0.1e1 / t98
  t101 = jnp.exp(-t97 * t99)
  t102 = f.my_piecewise3(t94, 0, t101)
  t103 = abs(params.d)
  t106 = jnp.log(DBL_EPSILON / t103)
  t109 = (-t106 + params.c2) / t106
  t110 = t73 < -t109
  t111 = f.my_piecewise3(t110, -t109, t73)
  t112 = 0.1e1 - t111
  t115 = jnp.exp(params.c2 / t112)
  t117 = f.my_piecewise3(t110, 0, -params.d * t115)
  t118 = f.my_piecewise3(t89, t102, t117)
  t119 = 0.1e1 - t118
  t122 = t88 * t119 + 0.1174e1 * t118
  t124 = jnp.sqrt(0.3e1)
  t125 = 0.1e1 / t24
  t127 = jnp.sqrt(s0)
  t128 = t127 * t28
  t132 = t40 * t125 * t128 / t19 / r0
  t133 = jnp.sqrt(t132)
  t137 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t124 / t133)
  t138 = 0.1e1 - t137
  t142 = params.k1 ** 2
  t143 = t83 ** 2
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
  t178 = t27 * t78
  t181 = t60 * t76
  t185 = -0.7e1 / 0.4860e4 * t62 * t149 - t60 * t176 * t178 / 0.180e3 + t181 * t176 * t178 / 0.180e3
  t188 = -0.10e2 / 0.729e3 * t27 * t149 - t44 * t46 / t19 / t47 / t31 * t55 / 0.54e2 + 0.3e1 / 0.80e2 * t162 * t163 / t164 / r0 * t55 + 0.2e1 * t81 * t185
  t193 = 0.5e1 / 0.9e1 * t176 * t22 * t26
  t194 = f.my_piecewise3(t95, t193, 0)
  t197 = t98 ** 2
  t198 = 0.1e1 / t197
  t201 = -t97 * t198 * t194 - params.c1 * t194 * t99
  t203 = f.my_piecewise3(t94, 0, t201 * t101)
  t204 = params.d * params.c2
  t205 = t112 ** 2
  t206 = 0.1e1 / t205
  t207 = f.my_piecewise3(t110, 0, t193)
  t211 = f.my_piecewise3(t110, 0, -t204 * t206 * t207 * t115)
  t212 = f.my_piecewise3(t89, t203, t211)
  t215 = t145 * t188 * t119 - t88 * t212 + 0.1174e1 * t212
  t220 = 3 ** (0.1e1 / 0.6e1)
  t221 = t220 ** 2
  t222 = t221 ** 2
  t224 = t222 * t220 * t5
  t226 = t17 / t31
  t234 = 0.1e1 / t133 / t132 * t40 * t125 * t128 * t137
  t238 = f.my_piecewise3(t2, 0, -t18 * t21 * t122 * t138 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t215 * t138 - 0.24739500000000000000000000000000000000000000000000e1 * t224 * t226 * t122 * t234)
  t257 = t188 ** 2
  t263 = t30 / t20 / t47
  t281 = t45 ** 2
  t291 = t185 ** 2
  t298 = 0.40e2 / 0.9e1 * t65 * t148 - 0.11e2 / 0.9e1 * t263
  t302 = t176 ** 2
  t330 = 0.5e1 / 0.9e1 * t298 * t22 * t26
  t331 = f.my_piecewise3(t95, t330, 0)
  t334 = t194 ** 2
  t347 = t201 ** 2
  t350 = f.my_piecewise3(t94, 0, (-params.c1 * t331 * t99 - 0.2e1 * params.c1 * t334 * t198 - 0.2e1 * t97 / t197 / t98 * t334 - t97 * t198 * t331) * t101 + t347 * t101)
  t353 = t207 ** 2
  t358 = f.my_piecewise3(t110, 0, t330)
  t362 = params.c2 ** 2
  t364 = t205 ** 2
  t370 = f.my_piecewise3(t110, 0, -0.2e1 * t204 / t205 / t112 * t353 * t115 - t204 * t206 * t358 * t115 - params.d * t362 / t364 * t353 * t115)
  t371 = f.my_piecewise3(t89, t350, t370)
  t397 = t4 ** 2
  t412 = f.my_piecewise3(t2, 0, t18 * t67 * t122 * t138 / 0.12e2 - t18 * t21 * t215 * t138 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t224 * t17 / t146 * t122 * t234 - 0.3e1 / 0.8e1 * t18 * t19 * (-0.2e1 * t142 / t143 / t83 * t257 * t119 + t145 * (0.110e3 / 0.2187e4 * t27 * t263 + 0.19e2 / 0.162e3 * t44 * t46 / t19 / t47 / t146 * t55 - 0.43e2 / 0.80e2 * t162 * t163 / t164 / t31 * t55 + 0.27e2 / 0.800e3 * t159 * t39 * t161 * t281 / t20 / t164 / t47 * t27 * t29 * t55 + 0.2e1 * t291 + 0.2e1 * t81 * (0.77e2 / 0.14580e5 * t62 * t263 - t60 * t298 * t178 / 0.180e3 - t60 * t302 * t40 * t43 * t74 * t78 / 0.108e3 + t181 * t298 * t178 / 0.180e3 + t60 * t76 * t74 * t302 * t40 * t43 * t78 / 0.324e3)) * t119 - 0.2e1 * t145 * t188 * t212 - t88 * t371 + 0.1174e1 * t371) * t138 - 0.49479000000000000000000000000000000000000000000000e1 * t224 * t226 * t215 * t234 - 0.49479000000000000000000000000000000000000000000000e1 * t224 * t17 / t19 / t47 * t122 / t133 / t35 * t22 * t26 * t30 * t137 + 0.40802857350000000000000000000000000000000000000000e1 * t3 * t397 * jnp.pi * t17 / t19 * t122 / t127 * t22 * t26 * t29 * t137)
  v2rho2_0_ = 0.2e1 * r0 * t412 + 0.4e1 * t238
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
  t72 = 0.5e1 / 0.9e1 * (t66 * t22 - t35 / 0.8e1) * t23 * t27
  t73 = 0.1e1 - t72
  t75 = t73 ** 2
  t77 = jnp.exp(-t75 / 0.2e1)
  t80 = 0.7e1 / 0.12960e5 * t63 * t35 + t61 * t73 * t77 / 0.100e3
  t81 = t80 ** 2
  t82 = params.k1 + 0.5e1 / 0.972e3 * t36 + t45 * t47 * t51 * t56 / 0.288e3 + t81
  t87 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t82)
  t88 = t72 <= 0.1e1
  t89 = jnp.log(DBL_EPSILON)
  t92 = t89 / (-t89 + params.c1)
  t93 = -t92 < t72
  t94 = t72 < -t92
  t95 = f.my_piecewise3(t94, t72, -t92)
  t96 = params.c1 * t95
  t97 = 0.1e1 - t95
  t98 = 0.1e1 / t97
  t100 = jnp.exp(-t96 * t98)
  t101 = f.my_piecewise3(t93, 0, t100)
  t102 = abs(params.d)
  t105 = jnp.log(DBL_EPSILON / t102)
  t108 = (-t105 + params.c2) / t105
  t109 = t72 < -t108
  t110 = f.my_piecewise3(t109, -t108, t72)
  t111 = 0.1e1 - t110
  t114 = jnp.exp(params.c2 / t111)
  t116 = f.my_piecewise3(t109, 0, -params.d * t114)
  t117 = f.my_piecewise3(t88, t101, t116)
  t118 = 0.1e1 - t117
  t121 = t87 * t118 + 0.1174e1 * t117
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
  t143 = t82 ** 2
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
  t178 = t28 * t77
  t181 = t61 * t75
  t185 = -0.7e1 / 0.4860e4 * t63 * t149 - t61 * t176 * t178 / 0.180e3 + t181 * t176 * t178 / 0.180e3
  t188 = -0.10e2 / 0.729e3 * t28 * t149 - t45 * t47 / t19 / t152 * t56 / 0.54e2 + 0.3e1 / 0.80e2 * t162 * t163 / t164 / r0 * t56 + 0.2e1 * t80 * t185
  t189 = t188 * t118
  t193 = 0.5e1 / 0.9e1 * t176 * t23 * t27
  t194 = f.my_piecewise3(t94, t193, 0)
  t197 = t97 ** 2
  t198 = 0.1e1 / t197
  t199 = t198 * t194
  t201 = -params.c1 * t194 * t98 - t96 * t199
  t203 = f.my_piecewise3(t93, 0, t201 * t100)
  t204 = params.d * params.c2
  t205 = t111 ** 2
  t206 = 0.1e1 / t205
  t207 = f.my_piecewise3(t109, 0, t193)
  t211 = f.my_piecewise3(t109, 0, -t204 * t206 * t207 * t114)
  t212 = f.my_piecewise3(t88, t203, t211)
  t215 = t145 * t189 - t87 * t212 + 0.1174e1 * t212
  t220 = 3 ** (0.1e1 / 0.6e1)
  t221 = t220 ** 2
  t222 = t221 ** 2
  t223 = t222 * t220
  t224 = t223 * t5
  t226 = t17 / t146
  t230 = 0.1e1 / t132 / t131
  t234 = t230 * t41 * t124 * t127 * t136
  t239 = t142 / t143 / t82
  t240 = t188 ** 2
  t245 = 0.1e1 / t20 / t48
  t246 = t31 * t245
  t263 = t159 * t40 * t161
  t264 = t46 ** 2
  t271 = t28 * t30 * t56
  t274 = t185 ** 2
  t281 = 0.40e2 / 0.9e1 * t66 * t148 - 0.11e2 / 0.9e1 * t246
  t282 = t61 * t281
  t285 = t176 ** 2
  t288 = t44 * t73
  t296 = t61 * t75 * t73
  t298 = t41 * t44
  t302 = 0.77e2 / 0.14580e5 * t63 * t246 - t282 * t178 / 0.180e3 - t61 * t285 * t41 * t288 * t77 / 0.108e3 + t181 * t281 * t178 / 0.180e3 + t296 * t285 * t298 * t77 / 0.324e3
  t305 = 0.110e3 / 0.2187e4 * t28 * t246 + 0.19e2 / 0.162e3 * t45 * t47 / t19 / t48 / t146 * t56 - 0.43e2 / 0.80e2 * t162 * t163 / t164 / t32 * t56 + 0.27e2 / 0.800e3 * t263 * t264 / t20 / t164 / t48 * t271 + 0.2e1 * t274 + 0.2e1 * t80 * t302
  t313 = 0.5e1 / 0.9e1 * t281 * t23 * t27
  t314 = f.my_piecewise3(t94, t313, 0)
  t315 = params.c1 * t314
  t317 = t194 ** 2
  t322 = 0.1e1 / t197 / t97
  t328 = -t96 * t198 * t314 - 0.2e1 * params.c1 * t317 * t198 - 0.2e1 * t96 * t322 * t317 - t315 * t98
  t330 = t201 ** 2
  t333 = f.my_piecewise3(t93, 0, t328 * t100 + t330 * t100)
  t335 = 0.1e1 / t205 / t111
  t336 = t207 ** 2
  t341 = f.my_piecewise3(t109, 0, t313)
  t345 = params.c2 ** 2
  t346 = params.d * t345
  t347 = t205 ** 2
  t348 = 0.1e1 / t347
  t353 = f.my_piecewise3(t109, 0, -t204 * t206 * t341 * t114 - 0.2e1 * t204 * t335 * t336 * t114 - t346 * t348 * t336 * t114)
  t354 = f.my_piecewise3(t88, t333, t353)
  t357 = -0.2e1 * t239 * t240 * t118 + t145 * t305 * t118 - 0.2e1 * t145 * t188 * t212 - t87 * t354 + 0.1174e1 * t354
  t363 = t17 / t32
  t370 = t17 / t19 / t48
  t379 = 0.1e1 / t132 / t36 * t23 * t27 * t31 * t136 / 0.6e1
  t382 = t4 ** 2
  t384 = t3 * t382 * jnp.pi
  t386 = t17 / t19
  t389 = 0.1e1 / t126
  t393 = t389 * t23 * t27 * t30 * t136
  t397 = f.my_piecewise3(t2, 0, t18 * t22 * t121 * t137 / 0.12e2 - t18 * t141 * t215 * t137 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t224 * t226 * t121 * t234 - 0.3e1 / 0.8e1 * t18 * t19 * t357 * t137 - 0.49479000000000000000000000000000000000000000000000e1 * t224 * t363 * t215 * t234 - 0.29687400000000000000000000000000000000000000000000e2 * t224 * t370 * t121 * t379 + 0.40802857350000000000000000000000000000000000000000e1 * t384 * t386 * t121 * t393)
  t399 = t34 * t121
  t407 = 0.1e1 / t48
  t427 = t17 * t129 * t121
  t431 = t143 ** 2
  t446 = t31 / t20 / t49
  t468 = t159 ** 2
  t471 = t164 ** 2
  t487 = -0.440e3 / 0.27e2 * t66 * t245 + 0.154e3 / 0.27e2 * t446
  t492 = t176 * t77
  t496 = t285 * t176
  t497 = t61 * t496
  t512 = t75 ** 2
  t532 = 0.5e1 / 0.9e1 * t487 * t23 * t27
  t533 = f.my_piecewise3(t94, t532, 0)
  t538 = t317 * t194
  t542 = t197 ** 2
  t561 = f.my_piecewise3(t93, 0, (-params.c1 * t533 * t98 - 0.6e1 * t315 * t199 - 0.6e1 * params.c1 * t538 * t322 - 0.6e1 * t96 / t542 * t538 - 0.6e1 * t96 * t322 * t194 * t314 - t96 * t198 * t533) * t100 + 0.3e1 * t328 * t201 * t100 + t330 * t201 * t100)
  t562 = t336 * t207
  t569 = t207 * t114 * t341
  t578 = f.my_piecewise3(t109, 0, t532)
  t593 = f.my_piecewise3(t109, 0, -0.6e1 * t204 * t348 * t562 * t114 - 0.6e1 * t204 * t335 * t569 - 0.6e1 * t346 / t347 / t111 * t562 * t114 - t204 * t206 * t578 * t114 - 0.3e1 * t346 * t348 * t569 - params.d * t345 * params.c2 / t347 / t205 * t562 * t114)
  t594 = f.my_piecewise3(t88, t561, t593)
  t615 = 0.1e1 / t4 / t24
  t622 = t126 * s0
  t646 = -0.5e1 / 0.36e2 * t18 * t399 * t137 + t18 * t22 * t215 * t137 / 0.4e1 - 0.11819983333333333333333333333333333333333333333333e2 * t224 * t17 * t407 * t121 * t234 - 0.3e1 / 0.8e1 * t18 * t141 * t357 * t137 + 0.12369750000000000000000000000000000000000000000000e2 * t224 * t226 * t215 * t234 + 0.17812440000000000000000000000000000000000000000000e3 * t224 * t17 * t51 * t121 * t379 - 0.81605714700000000000000000000000000000000000000000e1 * t384 * t427 * t393 - 0.3e1 / 0.8e1 * t18 * t19 * (0.6e1 * t142 / t431 * t240 * t188 * t118 - 0.6e1 * t239 * t189 * t305 + 0.6e1 * t239 * t240 * t212 + t145 * (-0.1540e4 / 0.6561e4 * t28 * t446 - 0.209e3 / 0.243e3 * t45 * t47 / t19 / t164 * t56 + 0.797e3 / 0.120e3 * t162 * t163 / t164 / t146 * t56 - 0.729e3 / 0.800e3 * t263 * t264 / t20 / t164 / t49 * t271 + 0.243e3 / 0.4000e4 * t468 * t161 * t264 * s0 / t19 / t471 * t298 * t29 * t56 + 0.6e1 * t185 * t302 + 0.2e1 * t80 * (-0.539e3 / 0.21870e5 * t63 * t446 - t61 * t487 * t178 / 0.180e3 - t282 * t41 * t288 * t492 / 0.36e2 + 0.5e1 / 0.162e3 * t497 * t161 * t77 - 0.5e1 / 0.81e2 * t497 * t161 * t75 * t77 + t181 * t487 * t178 / 0.180e3 + t296 * t281 * t298 * t492 / 0.108e3 + 0.5e1 / 0.486e3 * t61 * t512 * t496 * t161 * t77)) * t118 - 0.3e1 * t145 * t305 * t212 - 0.3e1 * t145 * t188 * t354 - t87 * t594 + 0.1174e1 * t594) * t137 - 0.74218500000000000000000000000000000000000000000000e1 * t224 * t363 * t357 * t234 - 0.89062200000000000000000000000000000000000000000000e2 * t224 * t370 * t215 * t379 + 0.12240857205000000000000000000000000000000000000000e2 * t384 * t386 * t215 * t393 - 0.16493000000000000000000000000000000000000000000000e2 * t223 * t615 * t17 / t20 / t152 * t121 / t132 * t24 / t407 * t136 + 0.81605714699999999999999999999999999999999999999999e1 * t3 * t615 * t427 * t23 * t43 * t389 * t30 * t136 - 0.32302153261130400000000000000000000000000000000000e3 * t224 * t17 * t399 * t230 * t136
  t647 = f.my_piecewise3(t2, 0, t646)
  v3rho3_0_ = 0.2e1 * r0 * t647 + 0.6e1 * t397

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
  t72 = 0.5e1 / 0.9e1 * (t64 * t66 - t33 / 0.8e1) * t24 * t28
  t73 = 0.1e1 - t72
  t75 = t73 ** 2
  t77 = jnp.exp(-t75 / 0.2e1)
  t80 = 0.7e1 / 0.12960e5 * t61 * t33 + t59 * t73 * t77 / 0.100e3
  t81 = t80 ** 2
  t82 = params.k1 + 0.5e1 / 0.972e3 * t34 + t43 * t45 * t49 * t54 / 0.288e3 + t81
  t87 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t82)
  t88 = t72 <= 0.1e1
  t89 = jnp.log(DBL_EPSILON)
  t92 = t89 / (-t89 + params.c1)
  t93 = -t92 < t72
  t94 = t72 < -t92
  t95 = f.my_piecewise3(t94, t72, -t92)
  t96 = params.c1 * t95
  t97 = 0.1e1 - t95
  t98 = 0.1e1 / t97
  t100 = jnp.exp(-t96 * t98)
  t101 = f.my_piecewise3(t93, 0, t100)
  t102 = abs(params.d)
  t105 = jnp.log(DBL_EPSILON / t102)
  t108 = (-t105 + params.c2) / t105
  t109 = t72 < -t108
  t110 = f.my_piecewise3(t109, -t108, t72)
  t111 = 0.1e1 - t110
  t114 = jnp.exp(params.c2 / t111)
  t116 = f.my_piecewise3(t109, 0, -params.d * t114)
  t117 = f.my_piecewise3(t88, t101, t116)
  t118 = 0.1e1 - t117
  t121 = t87 * t118 + 0.1174e1 * t117
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
  t142 = t82 ** 2
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
  t177 = t29 * t77
  t180 = t59 * t75
  t184 = -0.7e1 / 0.4860e4 * t61 * t148 - t59 * t175 * t177 / 0.180e3 + t180 * t175 * t177 / 0.180e3
  t187 = -0.10e2 / 0.729e3 * t29 * t148 - t43 * t45 * t153 * t54 / 0.54e2 + 0.3e1 / 0.80e2 * t161 * t162 * t165 * t54 + 0.2e1 * t80 * t184
  t188 = t187 * t118
  t192 = 0.5e1 / 0.9e1 * t175 * t24 * t28
  t193 = f.my_piecewise3(t94, t192, 0)
  t196 = t97 ** 2
  t197 = 0.1e1 / t196
  t198 = t197 * t193
  t200 = -params.c1 * t193 * t98 - t96 * t198
  t202 = f.my_piecewise3(t93, 0, t200 * t100)
  t203 = params.d * params.c2
  t204 = t111 ** 2
  t205 = 0.1e1 / t204
  t206 = f.my_piecewise3(t109, 0, t192)
  t210 = f.my_piecewise3(t109, 0, -t203 * t205 * t206 * t114)
  t211 = f.my_piecewise3(t88, t202, t210)
  t214 = t144 * t188 - t87 * t211 + 0.1174e1 * t211
  t219 = 3 ** (0.1e1 / 0.6e1)
  t220 = t219 ** 2
  t221 = t220 ** 2
  t222 = t221 * t219
  t223 = t222 * t5
  t224 = 0.1e1 / t46
  t225 = t17 * t224
  t229 = 0.1e1 / t132 / t131
  t233 = t229 * t39 * t124 * t127 * t136
  t236 = 0.1e1 / t21
  t239 = t141 / t142 / t82
  t240 = t187 ** 2
  t241 = t240 * t118
  t245 = 0.1e1 / t21 / t46
  t246 = t32 * t245
  t249 = t46 * t145
  t263 = t158 * t38 * t160
  t264 = t44 ** 2
  t265 = t163 * t46
  t271 = t29 * t31 * t54
  t274 = t184 ** 2
  t281 = 0.40e2 / 0.9e1 * t64 * t147 - 0.11e2 / 0.9e1 * t246
  t282 = t59 * t281
  t285 = t175 ** 2
  t288 = t42 * t73
  t289 = t288 * t77
  t295 = t75 * t73
  t296 = t59 * t295
  t298 = t39 * t42
  t299 = t298 * t77
  t302 = 0.77e2 / 0.14580e5 * t61 * t246 - t282 * t177 / 0.180e3 - t59 * t285 * t39 * t289 / 0.108e3 + t180 * t281 * t177 / 0.180e3 + t296 * t285 * t299 / 0.324e3
  t305 = 0.110e3 / 0.2187e4 * t29 * t246 + 0.19e2 / 0.162e3 * t43 * t45 / t20 / t249 * t54 - 0.43e2 / 0.80e2 * t161 * t162 / t163 / t19 * t54 + 0.27e2 / 0.800e3 * t263 * t264 / t21 / t265 * t271 + 0.2e1 * t274 + 0.2e1 * t80 * t302
  t308 = t187 * t211
  t313 = 0.5e1 / 0.9e1 * t281 * t24 * t28
  t314 = f.my_piecewise3(t94, t313, 0)
  t315 = params.c1 * t314
  t317 = t193 ** 2
  t322 = 0.1e1 / t196 / t97
  t323 = t322 * t317
  t328 = -t96 * t197 * t314 - 0.2e1 * params.c1 * t317 * t197 - t315 * t98 - 0.2e1 * t96 * t323
  t330 = t200 ** 2
  t333 = f.my_piecewise3(t93, 0, t328 * t100 + t330 * t100)
  t334 = t204 * t111
  t335 = 0.1e1 / t334
  t336 = t206 ** 2
  t341 = f.my_piecewise3(t109, 0, t313)
  t345 = params.c2 ** 2
  t346 = params.d * t345
  t347 = t204 ** 2
  t348 = 0.1e1 / t347
  t353 = f.my_piecewise3(t109, 0, -t203 * t205 * t341 * t114 - 0.2e1 * t203 * t335 * t336 * t114 - t346 * t348 * t336 * t114)
  t354 = f.my_piecewise3(t88, t333, t353)
  t357 = -0.2e1 * t239 * t241 + t144 * t305 * t118 - 0.2e1 * t144 * t308 - t87 * t354 + 0.1174e1 * t354
  t363 = t17 / t145
  t368 = t17 * t49
  t373 = 0.1e1 / t132 / t34 / 0.6e1
  t377 = t373 * t24 * t28 * t32 * t136
  t380 = t4 ** 2
  t382 = t3 * t380 * jnp.pi
  t383 = t17 * t129
  t384 = t383 * t121
  t386 = 0.1e1 / t126
  t390 = t386 * t24 * t28 * t31 * t136
  t393 = t142 ** 2
  t395 = t141 / t393
  t396 = t240 * t187
  t407 = 0.1e1 / t21 / t47
  t408 = t32 * t407
  t430 = t158 ** 2
  t431 = t430 * t160
  t432 = t264 * s0
  t433 = t163 ** 2
  t439 = t298 * t30 * t54
  t449 = -0.440e3 / 0.27e2 * t64 * t245 + 0.154e3 / 0.27e2 * t408
  t450 = t59 * t449
  t454 = t175 * t77
  t455 = t288 * t454
  t458 = t285 * t175
  t459 = t59 * t458
  t471 = t298 * t454
  t474 = t75 ** 2
  t475 = t59 * t474
  t480 = -0.539e3 / 0.21870e5 * t61 * t408 - t450 * t177 / 0.180e3 - t282 * t39 * t455 / 0.36e2 + 0.5e1 / 0.162e3 * t459 * t160 * t77 - 0.5e1 / 0.81e2 * t459 * t160 * t75 * t77 + t180 * t449 * t177 / 0.180e3 + t296 * t281 * t471 / 0.108e3 + 0.5e1 / 0.486e3 * t475 * t458 * t160 * t77
  t483 = -0.1540e4 / 0.6561e4 * t29 * t408 - 0.209e3 / 0.243e3 * t43 * t45 / t20 / t163 * t54 + 0.797e3 / 0.120e3 * t161 * t162 / t163 / t145 * t54 - 0.729e3 / 0.800e3 * t263 * t264 / t21 / t163 / t47 * t271 + 0.243e3 / 0.4000e4 * t431 * t432 / t20 / t433 * t439 + 0.6e1 * t184 * t302 + 0.2e1 * t80 * t480
  t494 = 0.5e1 / 0.9e1 * t449 * t24 * t28
  t495 = f.my_piecewise3(t94, t494, 0)
  t496 = params.c1 * t495
  t500 = t317 * t193
  t504 = t196 ** 2
  t505 = 0.1e1 / t504
  t509 = t322 * t193
  t515 = -t96 * t197 * t495 - 0.6e1 * t96 * t509 * t314 - 0.6e1 * params.c1 * t500 * t322 - 0.6e1 * t96 * t505 * t500 - 0.6e1 * t315 * t198 - t496 * t98
  t523 = f.my_piecewise3(t93, 0, 0.3e1 * t328 * t200 * t100 + t330 * t200 * t100 + t515 * t100)
  t524 = t336 * t206
  t529 = t203 * t335
  t530 = t206 * t114
  t531 = t530 * t341
  t535 = 0.1e1 / t347 / t111
  t540 = f.my_piecewise3(t109, 0, t494)
  t544 = t346 * t348
  t548 = params.d * t345 * params.c2
  t550 = 0.1e1 / t347 / t204
  t555 = f.my_piecewise3(t109, 0, -t203 * t205 * t540 * t114 - 0.6e1 * t203 * t348 * t524 * t114 - 0.6e1 * t346 * t535 * t524 * t114 - t548 * t550 * t524 * t114 - 0.6e1 * t529 * t531 - 0.3e1 * t544 * t531)
  t556 = f.my_piecewise3(t88, t523, t555)
  t559 = 0.6e1 * t395 * t396 * t118 - 0.6e1 * t239 * t188 * t305 + 0.6e1 * t239 * t240 * t211 + t144 * t483 * t118 - 0.3e1 * t144 * t305 * t211 - 0.3e1 * t144 * t187 * t354 - t87 * t556 + 0.1174e1 * t556
  t565 = t17 / t19
  t572 = t17 / t20 / t46
  t578 = t17 / t20
  t584 = 0.1e1 / t4 / t25
  t585 = t222 * t584
  t587 = 0.1e1 / t21 / t151
  t589 = t585 * t17 * t587
  t591 = t126 * s0
  t596 = 0.1e1 / t132 * t25 / t591 / t224 / 0.72e2
  t598 = t591 * t136
  t599 = t121 * t596 * t598
  t602 = t3 * t584
  t607 = t24 * t41 * t386 * t31 * t136
  t610 = t223 * t17
  t611 = t229 * t136
  t615 = -0.5e1 / 0.36e2 * t18 * t122 * t137 + t18 * t66 * t214 * t137 / 0.4e1 - 0.11819983333333333333333333333333333333333333333333e2 * t223 * t225 * t121 * t233 - 0.3e1 / 0.8e1 * t18 * t236 * t357 * t137 + 0.12369750000000000000000000000000000000000000000000e2 * t223 * t363 * t214 * t233 + 0.17812440000000000000000000000000000000000000000000e3 * t223 * t368 * t121 * t377 - 0.81605714700000000000000000000000000000000000000000e1 * t382 * t384 * t390 - 0.3e1 / 0.8e1 * t18 * t20 * t559 * t137 - 0.74218500000000000000000000000000000000000000000000e1 * t223 * t565 * t357 * t233 - 0.89062200000000000000000000000000000000000000000000e2 * t223 * t572 * t214 * t377 + 0.12240857205000000000000000000000000000000000000000e2 * t382 * t578 * t214 * t390 - 0.11874960000000000000000000000000000000000000000000e4 * t589 * t599 + 0.81605714699999999999999999999999999999999999999999e1 * t602 * t384 * t607 - 0.32302153261130400000000000000000000000000000000000e3 * t610 * t122 * t611
  t616 = f.my_piecewise3(t2, 0, t615)
  t625 = t240 ** 2
  t635 = t305 ** 2
  t648 = t32 * t587
  t677 = t159 ** 2
  t687 = t302 ** 2
  t696 = 0.6160e4 / 0.81e2 * t64 * t407 - 0.2618e4 / 0.81e2 * t648
  t704 = t160 * t285 * t77
  t707 = t281 ** 2
  t717 = t285 ** 2
  t719 = t59 * t717 * t160
  t721 = t28 * t77
  t748 = 0.9163e4 / 0.65610e5 * t61 * t648 - t59 * t696 * t177 / 0.180e3 - t450 * t39 * t455 / 0.27e2 + 0.5e1 / 0.27e2 * t282 * t704 - t59 * t707 * t39 * t289 / 0.36e2 - 0.10e2 / 0.27e2 * t282 * t160 * t75 * t285 * t77 + 0.125e3 / 0.1458e4 * t719 * t73 * t24 * t721 - 0.125e3 / 0.2187e4 * t719 * t295 * t24 * t721 + t180 * t696 * t177 / 0.180e3 + t296 * t449 * t471 / 0.81e2 + t296 * t707 * t299 / 0.108e3 + 0.5e1 / 0.81e2 * t475 * t281 * t704 + 0.25e2 / 0.4374e4 * t59 * t474 * t73 * t717 * t160 * t24 * t721
  t765 = 0.5e1 / 0.9e1 * t696 * t24 * t28
  t766 = f.my_piecewise3(t94, t765, 0)
  t773 = t314 ** 2
  t777 = t317 ** 2
  t803 = t328 ** 2
  t809 = t330 ** 2
  t812 = f.my_piecewise3(t93, 0, (-params.c1 * t766 * t98 - 0.8e1 * t496 * t198 - 0.36e2 * t315 * t323 - 0.6e1 * params.c1 * t773 * t197 - 0.24e2 * params.c1 * t777 * t505 - 0.24e2 * t96 / t504 / t97 * t777 - 0.36e2 * t96 * t505 * t317 * t314 - 0.6e1 * t96 * t322 * t773 - 0.8e1 * t96 * t509 * t495 - t96 * t197 * t766) * t100 + 0.4e1 * t515 * t200 * t100 + 0.3e1 * t803 * t100 + 0.6e1 * t328 * t330 * t100 + t809 * t100)
  t813 = t336 ** 2
  t820 = t336 * t114 * t341
  t827 = t341 ** 2
  t835 = t530 * t540
  t844 = f.my_piecewise3(t109, 0, t765)
  t857 = t345 ** 2
  t859 = t347 ** 2
  t864 = -0.24e2 * t203 * t535 * t813 * t114 - 0.36e2 * t203 * t348 * t820 - 0.36e2 * t346 * t550 * t813 * t114 - 0.6e1 * t203 * t335 * t827 * t114 - 0.36e2 * t346 * t535 * t820 - 0.8e1 * t529 * t835 - 0.12e2 * t548 / t347 / t334 * t813 * t114 - t203 * t205 * t844 * t114 - 0.4e1 * t544 * t835 - 0.3e1 * t346 * t348 * t827 * t114 - 0.6e1 * t548 * t550 * t820 - params.d * t857 / t859 * t813 * t114
  t865 = f.my_piecewise3(t109, 0, t864)
  t866 = f.my_piecewise3(t88, t812, t865)
  t869 = -0.24e2 * t141 / t393 / t82 * t625 * t118 + 0.36e2 * t395 * t241 * t305 - 0.24e2 * t395 * t396 * t211 - 0.6e1 * t239 * t635 * t118 + 0.24e2 * t239 * t308 * t305 - 0.8e1 * t239 * t188 * t483 + 0.12e2 * t239 * t240 * t354 + t144 * (0.26180e5 / 0.19683e5 * t29 * t648 + 0.5225e4 / 0.729e3 * t43 * t45 / t20 / t164 * t54 - 0.5929e4 / 0.72e2 * t161 * t162 / t265 * t54 + 0.2949e4 / 0.160e3 * t263 * t264 / t21 / t163 / t151 * t271 - 0.1053e4 / 0.400e3 * t431 * t432 / t20 / t433 / r0 * t439 + 0.6561e4 / 0.10000e5 * t430 * t38 / t677 * t264 * t44 / t433 / t46 * t54 + 0.6e1 * t687 + 0.8e1 * t184 * t480 + 0.2e1 * t80 * t748) * t118 - 0.4e1 * t144 * t483 * t211 - 0.6e1 * t144 * t305 * t354 - 0.4e1 * t144 * t187 * t556 - t87 * t866 + 0.1174e1 * t866
  t878 = t23 * t214
  t889 = t147 * t121
  t893 = t383 * t214
  t918 = t17 / t20 / t19 * t121
  t922 = -0.47499840000000000000000000000000000000000000000000e4 * t589 * t214 * t596 * t598 - 0.3e1 / 0.8e1 * t18 * t20 * t869 * t137 - t18 * t236 * t559 * t137 / 0.2e1 - 0.5e1 / 0.9e1 * t18 * t878 * t137 + t18 * t66 * t357 * t137 / 0.2e1 - 0.12920861304452160000000000000000000000000000000000e4 * t610 * t878 * t611 + 0.86139075363014400000000000000000000000000000000001e3 * t610 * t889 * t611 + 0.32642285880000000000000000000000000000000000000000e2 * t602 * t893 * t607 + 0.88793235622637281199999999999999999999999999999999e2 * t382 * t17 / r0 * t121 / s0 * t39 * t124 * t30 * t136 + 0.24481714410000000000000000000000000000000000000000e2 * t382 * t578 * t357 * t390 - 0.32642285880000000000000000000000000000000000000000e2 * t382 * t893 * t390 - 0.32642285879999999999999999999999999999999999999998e2 * t602 * t918 * t607
  t938 = t223 * t17 / t47 * t121
  t987 = 0.30375460471666666666666666666666666666666666666666e2 * t382 * t918 * t390 + 0.15041616000000000000000000000000000000000000000000e5 * t585 * t17 / t21 / t249 * t599 + 0.10e2 / 0.27e2 * t18 * t889 * t137 + 0.46363655555555555555555555555555555555555555555554e2 * t938 * t233 - 0.47279933333333333333333333333333333333333333333333e2 * t223 * t225 * t214 * t233 - 0.10918366000000000000000000000000000000000000000000e4 * t223 * t17 * t153 * t121 * t377 + 0.24739500000000000000000000000000000000000000000000e2 * t223 * t363 * t357 * t233 + 0.71249760000000000000000000000000000000000000000000e3 * t223 * t368 * t214 * t377 - 0.98958000000000000000000000000000000000000000000000e1 * t223 * t565 * t559 * t233 - 0.17812440000000000000000000000000000000000000000000e3 * t223 * t572 * t357 * t377 - 0.76967333333333333333333333333333333333333333333333e2 * t585 * t17 * t165 * t121 / t132 / t298 / t45 / t49 * t44 * t136 * t125 * t30 - 0.64604306522260800000000000000000000000000000000000e3 * t938 * t373 * t136 * t39 * t124 * t126 * t30
  t989 = f.my_piecewise3(t2, 0, t922 + t987)
  v4rho4_0_ = 0.2e1 * r0 * t989 + 0.8e1 * t616

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
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = 0.1e1 / t35
  t37 = t32 * t36
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t43 = s0 * t42
  t44 = t37 * t43
  t48 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t49 = t32 ** 2
  t52 = 0.1e1 / t34 / t33
  t53 = t48 * t49 * t52
  t54 = s0 ** 2
  t55 = t38 ** 2
  t60 = t48 * t32
  t61 = t36 * s0
  t62 = t61 * t42
  t65 = jnp.exp(-0.27e2 / 0.80e2 * t60 * t62)
  t69 = jnp.sqrt(0.146e3)
  t70 = t69 * t32
  t80 = 0.5e1 / 0.9e1 * (tau0 / t40 / r0 - t43 / 0.8e1) * t32 * t36
  t81 = 0.1e1 - t80
  t83 = t81 ** 2
  t85 = jnp.exp(-t83 / 0.2e1)
  t88 = 0.7e1 / 0.12960e5 * t70 * t62 + t69 * t81 * t85 / 0.100e3
  t89 = t88 ** 2
  t90 = params.k1 + 0.5e1 / 0.972e3 * t44 + t53 * t54 / t39 / t55 / r0 * t65 / 0.576e3 + t89
  t95 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t90)
  t96 = t80 <= 0.1e1
  t97 = jnp.log(DBL_EPSILON)
  t100 = t97 / (-t97 + params.c1)
  t101 = -t100 < t80
  t102 = t80 < -t100
  t103 = f.my_piecewise3(t102, t80, -t100)
  t104 = params.c1 * t103
  t105 = 0.1e1 - t103
  t106 = 0.1e1 / t105
  t108 = jnp.exp(-t104 * t106)
  t109 = f.my_piecewise3(t101, 0, t108)
  t110 = abs(params.d)
  t113 = jnp.log(DBL_EPSILON / t110)
  t116 = (-t113 + params.c2) / t113
  t117 = t80 < -t116
  t118 = f.my_piecewise3(t117, -t116, t80)
  t119 = 0.1e1 - t118
  t122 = jnp.exp(params.c2 / t119)
  t124 = f.my_piecewise3(t117, 0, -params.d * t122)
  t125 = f.my_piecewise3(t96, t109, t124)
  t126 = 0.1e1 - t125
  t129 = t95 * t126 + 0.1174e1 * t125
  t131 = jnp.sqrt(0.3e1)
  t132 = 0.1e1 / t34
  t133 = t49 * t132
  t134 = jnp.sqrt(s0)
  t138 = t133 * t134 / t39 / r0
  t139 = jnp.sqrt(t138)
  t143 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t131 / t139)
  t144 = 0.1e1 - t143
  t145 = t31 * t129 * t144
  t148 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t149 = t148 * f.p.zeta_threshold
  t151 = f.my_piecewise3(t20, t149, t21 * t19)
  t152 = t5 * t151
  t153 = t31 ** 2
  t154 = 0.1e1 / t153
  t156 = t154 * t129 * t144
  t158 = t152 * t156 / 0.8e1
  t159 = params.k1 ** 2
  t160 = t90 ** 2
  t162 = t159 / t160
  t163 = t38 * r0
  t165 = 0.1e1 / t40 / t163
  t166 = s0 * t165
  t176 = t48 ** 2
  t177 = t33 ** 2
  t178 = 0.1e1 / t177
  t179 = t176 * t178
  t180 = t54 * s0
  t181 = t55 ** 2
  t194 = -0.5e1 / 0.3e1 * tau0 * t42 + t166 / 0.3e1
  t196 = t37 * t85
  t199 = t69 * t83
  t203 = -0.7e1 / 0.4860e4 * t70 * t61 * t165 - t69 * t194 * t196 / 0.180e3 + t199 * t194 * t196 / 0.180e3
  t206 = -0.10e2 / 0.729e3 * t37 * t166 - t53 * t54 / t39 / t55 / t38 * t65 / 0.108e3 + 0.3e1 / 0.320e3 * t179 * t180 / t181 / r0 * t65 + 0.2e1 * t88 * t203
  t211 = 0.5e1 / 0.9e1 * t194 * t32 * t36
  t212 = f.my_piecewise3(t102, t211, 0)
  t215 = t105 ** 2
  t216 = 0.1e1 / t215
  t219 = -t104 * t216 * t212 - params.c1 * t212 * t106
  t221 = f.my_piecewise3(t101, 0, t219 * t108)
  t222 = params.d * params.c2
  t223 = t119 ** 2
  t224 = 0.1e1 / t223
  t225 = f.my_piecewise3(t117, 0, t211)
  t229 = f.my_piecewise3(t117, 0, -t222 * t224 * t225 * t122)
  t230 = f.my_piecewise3(t96, t221, t229)
  t233 = t162 * t206 * t126 - t95 * t230 + 0.1174e1 * t230
  t235 = t31 * t233 * t144
  t238 = 3 ** (0.1e1 / 0.6e1)
  t239 = t238 ** 2
  t240 = t239 ** 2
  t242 = t240 * t238 * t4
  t243 = t151 * t31
  t244 = t243 * t129
  t245 = t242 * t244
  t249 = 0.1e1 / t139 / t138 * t49 * t132
  t254 = t249 * t134 / t39 / t38 * t143
  t258 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t145 - t158 - 0.3e1 / 0.8e1 * t152 * t235 - 0.24739500000000000000000000000000000000000000000000e1 * t245 * t254)
  t260 = r1 <= f.p.dens_threshold
  t261 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t262 = 0.1e1 + t261
  t263 = t262 <= f.p.zeta_threshold
  t264 = t262 ** (0.1e1 / 0.3e1)
  t266 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t269 = f.my_piecewise3(t263, 0, 0.4e1 / 0.3e1 * t264 * t266)
  t270 = t5 * t269
  t271 = r1 ** 2
  t272 = r1 ** (0.1e1 / 0.3e1)
  t273 = t272 ** 2
  t275 = 0.1e1 / t273 / t271
  t276 = s2 * t275
  t277 = t37 * t276
  t279 = s2 ** 2
  t280 = t271 ** 2
  t285 = t36 * s2
  t286 = t285 * t275
  t289 = jnp.exp(-0.27e2 / 0.80e2 * t60 * t286)
  t302 = 0.5e1 / 0.9e1 * (tau1 / t273 / r1 - t276 / 0.8e1) * t32 * t36
  t303 = 0.1e1 - t302
  t305 = t303 ** 2
  t307 = jnp.exp(-t305 / 0.2e1)
  t310 = 0.7e1 / 0.12960e5 * t70 * t286 + t69 * t303 * t307 / 0.100e3
  t311 = t310 ** 2
  t312 = params.k1 + 0.5e1 / 0.972e3 * t277 + t53 * t279 / t272 / t280 / r1 * t289 / 0.576e3 + t311
  t317 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t312)
  t318 = t302 <= 0.1e1
  t319 = -t100 < t302
  t320 = t302 < -t100
  t321 = f.my_piecewise3(t320, t302, -t100)
  t322 = params.c1 * t321
  t323 = 0.1e1 - t321
  t324 = 0.1e1 / t323
  t326 = jnp.exp(-t322 * t324)
  t327 = f.my_piecewise3(t319, 0, t326)
  t328 = t302 < -t116
  t329 = f.my_piecewise3(t328, -t116, t302)
  t330 = 0.1e1 - t329
  t333 = jnp.exp(params.c2 / t330)
  t335 = f.my_piecewise3(t328, 0, -params.d * t333)
  t336 = f.my_piecewise3(t318, t327, t335)
  t337 = 0.1e1 - t336
  t340 = t317 * t337 + 0.1174e1 * t336
  t342 = jnp.sqrt(s2)
  t346 = t133 * t342 / t272 / r1
  t347 = jnp.sqrt(t346)
  t351 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t131 / t347)
  t352 = 0.1e1 - t351
  t353 = t31 * t340 * t352
  t357 = f.my_piecewise3(t263, t149, t264 * t262)
  t358 = t5 * t357
  t360 = t154 * t340 * t352
  t362 = t358 * t360 / 0.8e1
  t364 = f.my_piecewise3(t260, 0, -0.3e1 / 0.8e1 * t270 * t353 - t362)
  t366 = t21 ** 2
  t367 = 0.1e1 / t366
  t368 = t26 ** 2
  t373 = t16 / t22 / t6
  t375 = -0.2e1 * t23 + 0.2e1 * t373
  t376 = f.my_piecewise5(t10, 0, t14, 0, t375)
  t380 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t367 * t368 + 0.4e1 / 0.3e1 * t21 * t376)
  t384 = t30 * t156
  t394 = 0.1e1 / t153 / t6
  t398 = t152 * t394 * t129 * t144 / 0.12e2
  t401 = t152 * t154 * t233 * t144
  t406 = t242 * t151 * t154 * t129 * t254
  t411 = t206 ** 2
  t416 = 0.1e1 / t40 / t55
  t417 = s0 * t416
  t434 = t176 * t48 * t178
  t435 = t54 ** 2
  t445 = t203 ** 2
  t453 = 0.40e2 / 0.9e1 * tau0 * t165 - 0.11e2 / 0.9e1 * t417
  t457 = t194 ** 2
  t470 = t49 * t52
  t485 = 0.5e1 / 0.9e1 * t453 * t32 * t36
  t486 = f.my_piecewise3(t102, t485, 0)
  t489 = t212 ** 2
  t502 = t219 ** 2
  t505 = f.my_piecewise3(t101, 0, (-params.c1 * t486 * t106 - 0.2e1 * params.c1 * t489 * t216 - 0.2e1 * t104 / t215 / t105 * t489 - t104 * t216 * t486) * t108 + t502 * t108)
  t508 = t225 ** 2
  t513 = f.my_piecewise3(t117, 0, t485)
  t517 = params.c2 ** 2
  t518 = params.d * t517
  t519 = t223 ** 2
  t525 = f.my_piecewise3(t117, 0, -0.2e1 * t222 / t223 / t119 * t508 * t122 - t222 * t224 * t513 * t122 - t518 / t519 * t508 * t122)
  t526 = f.my_piecewise3(t96, t505, t525)
  t554 = t3 ** 2
  t556 = t2 * t554 * jnp.pi
  t565 = -0.3e1 / 0.8e1 * t5 * t380 * t145 - t384 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t235 - 0.49479000000000000000000000000000000000000000000000e1 * t242 * t29 * t31 * t129 * t254 + t398 - t401 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t406 - 0.3e1 / 0.8e1 * t152 * t31 * (-0.2e1 * t159 / t160 / t90 * t411 * t126 + t162 * (0.110e3 / 0.2187e4 * t37 * t417 + 0.19e2 / 0.324e3 * t53 * t54 / t39 / t55 / t163 * t65 - 0.43e2 / 0.320e3 * t179 * t180 / t181 / t38 * t65 + 0.27e2 / 0.3200e4 * t434 * t435 / t40 / t181 / t55 * t32 * t36 * t65 + 0.2e1 * t445 + 0.2e1 * t88 * (0.77e2 / 0.14580e5 * t70 * t61 * t416 - t69 * t453 * t196 / 0.180e3 - t69 * t457 * t49 * t52 * t81 * t85 / 0.108e3 + t199 * t453 * t196 / 0.180e3 + t69 * t83 * t81 * t457 * t470 * t85 / 0.324e3)) * t126 - 0.2e1 * t162 * t206 * t230 - t95 * t526 + 0.1174e1 * t526) * t144 - 0.49479000000000000000000000000000000000000000000000e1 * t242 * t243 * t233 * t254 - 0.49479000000000000000000000000000000000000000000000e1 * t245 / t139 / t44 * t32 * t36 * t417 * t143 + 0.57725500000000000000000000000000000000000000000000e1 * t245 * t249 * t134 / t39 / t163 * t143 + 0.81605714700000000000000000000000000000000000000000e1 * t556 * t244 / t134 / t40 * t37 * t143
  t566 = f.my_piecewise3(t1, 0, t565)
  t567 = t264 ** 2
  t568 = 0.1e1 / t567
  t569 = t266 ** 2
  t573 = f.my_piecewise5(t14, 0, t10, 0, -t375)
  t577 = f.my_piecewise3(t263, 0, 0.4e1 / 0.9e1 * t568 * t569 + 0.4e1 / 0.3e1 * t264 * t573)
  t581 = t270 * t360
  t586 = t358 * t394 * t340 * t352 / 0.12e2
  t588 = f.my_piecewise3(t260, 0, -0.3e1 / 0.8e1 * t5 * t577 * t353 - t581 / 0.4e1 + t586)
  d11 = 0.2e1 * t258 + 0.2e1 * t364 + t6 * (t566 + t588)
  t591 = -t7 - t24
  t592 = f.my_piecewise5(t10, 0, t14, 0, t591)
  t595 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t592)
  t596 = t5 * t595
  t600 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t596 * t145 - t158)
  t602 = f.my_piecewise5(t14, 0, t10, 0, -t591)
  t605 = f.my_piecewise3(t263, 0, 0.4e1 / 0.3e1 * t264 * t602)
  t606 = t5 * t605
  t609 = t312 ** 2
  t611 = t159 / t609
  t612 = t271 * r1
  t614 = 0.1e1 / t273 / t612
  t615 = s2 * t614
  t625 = t279 * s2
  t626 = t280 ** 2
  t639 = -0.5e1 / 0.3e1 * tau1 * t275 + t615 / 0.3e1
  t641 = t37 * t307
  t644 = t69 * t305
  t648 = -0.7e1 / 0.4860e4 * t70 * t285 * t614 - t69 * t639 * t641 / 0.180e3 + t644 * t639 * t641 / 0.180e3
  t651 = -0.10e2 / 0.729e3 * t37 * t615 - t53 * t279 / t272 / t280 / t271 * t289 / 0.108e3 + 0.3e1 / 0.320e3 * t179 * t625 / t626 / r1 * t289 + 0.2e1 * t310 * t648
  t656 = 0.5e1 / 0.9e1 * t639 * t32 * t36
  t657 = f.my_piecewise3(t320, t656, 0)
  t660 = t323 ** 2
  t661 = 0.1e1 / t660
  t664 = -t322 * t661 * t657 - params.c1 * t657 * t324
  t666 = f.my_piecewise3(t319, 0, t664 * t326)
  t667 = t330 ** 2
  t668 = 0.1e1 / t667
  t669 = f.my_piecewise3(t328, 0, t656)
  t673 = f.my_piecewise3(t328, 0, -t222 * t668 * t669 * t333)
  t674 = f.my_piecewise3(t318, t666, t673)
  t677 = t611 * t651 * t337 - t317 * t674 + 0.1174e1 * t674
  t679 = t31 * t677 * t352
  t682 = t357 * t31
  t683 = t682 * t340
  t684 = t242 * t683
  t688 = 0.1e1 / t347 / t346 * t49 * t132
  t693 = t688 * t342 / t272 / t271 * t351
  t697 = f.my_piecewise3(t260, 0, -0.3e1 / 0.8e1 * t606 * t353 - t362 - 0.3e1 / 0.8e1 * t358 * t679 - 0.24739500000000000000000000000000000000000000000000e1 * t684 * t693)
  t701 = 0.2e1 * t373
  t702 = f.my_piecewise5(t10, 0, t14, 0, t701)
  t706 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t367 * t592 * t26 + 0.4e1 / 0.3e1 * t21 * t702)
  t710 = t596 * t156
  t723 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t706 * t145 - t710 / 0.8e1 - 0.3e1 / 0.8e1 * t596 * t235 - 0.24739500000000000000000000000000000000000000000000e1 * t242 * t595 * t31 * t129 * t254 - t384 / 0.8e1 + t398 - t401 / 0.8e1 - 0.82465000000000000000000000000000000000000000000000e0 * t406)
  t727 = f.my_piecewise5(t14, 0, t10, 0, -t701)
  t731 = f.my_piecewise3(t263, 0, 0.4e1 / 0.9e1 * t568 * t602 * t266 + 0.4e1 / 0.3e1 * t264 * t727)
  t735 = t606 * t360
  t742 = t358 * t154 * t677 * t352
  t752 = t242 * t357 * t154 * t340 * t693
  t755 = f.my_piecewise3(t260, 0, -0.3e1 / 0.8e1 * t5 * t731 * t353 - t735 / 0.8e1 - t581 / 0.8e1 + t586 - 0.3e1 / 0.8e1 * t270 * t679 - t742 / 0.8e1 - 0.24739500000000000000000000000000000000000000000000e1 * t242 * t269 * t31 * t340 * t693 - 0.82465000000000000000000000000000000000000000000000e0 * t752)
  d12 = t258 + t364 + t600 + t697 + t6 * (t723 + t755)
  t760 = t592 ** 2
  t764 = 0.2e1 * t23 + 0.2e1 * t373
  t765 = f.my_piecewise5(t10, 0, t14, 0, t764)
  t769 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t367 * t760 + 0.4e1 / 0.3e1 * t21 * t765)
  t775 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t769 * t145 - t710 / 0.4e1 + t398)
  t776 = t602 ** 2
  t780 = f.my_piecewise5(t14, 0, t10, 0, -t764)
  t784 = f.my_piecewise3(t263, 0, 0.4e1 / 0.9e1 * t568 * t776 + 0.4e1 / 0.3e1 * t264 * t780)
  t801 = t651 ** 2
  t806 = 0.1e1 / t273 / t280
  t807 = s2 * t806
  t823 = t279 ** 2
  t833 = t648 ** 2
  t841 = 0.40e2 / 0.9e1 * tau1 * t614 - 0.11e2 / 0.9e1 * t807
  t845 = t639 ** 2
  t872 = 0.5e1 / 0.9e1 * t841 * t32 * t36
  t873 = f.my_piecewise3(t320, t872, 0)
  t876 = t657 ** 2
  t889 = t664 ** 2
  t892 = f.my_piecewise3(t319, 0, (-params.c1 * t873 * t324 - 0.2e1 * params.c1 * t876 * t661 - 0.2e1 * t322 / t660 / t323 * t876 - t322 * t661 * t873) * t326 + t889 * t326)
  t895 = t669 ** 2
  t900 = f.my_piecewise3(t328, 0, t872)
  t904 = t667 ** 2
  t910 = f.my_piecewise3(t328, 0, -0.2e1 * t222 / t667 / t330 * t895 * t333 - t222 * t668 * t900 * t333 - t518 / t904 * t895 * t333)
  t911 = f.my_piecewise3(t318, t892, t910)
  t947 = -0.3e1 / 0.8e1 * t5 * t784 * t353 - t735 / 0.4e1 - 0.3e1 / 0.4e1 * t606 * t679 - 0.49479000000000000000000000000000000000000000000000e1 * t242 * t605 * t31 * t340 * t693 + t586 - t742 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t752 - 0.3e1 / 0.8e1 * t358 * t31 * (-0.2e1 * t159 / t609 / t312 * t801 * t337 + t611 * (0.110e3 / 0.2187e4 * t37 * t807 + 0.19e2 / 0.324e3 * t53 * t279 / t272 / t280 / t612 * t289 - 0.43e2 / 0.320e3 * t179 * t625 / t626 / t271 * t289 + 0.27e2 / 0.3200e4 * t434 * t823 / t273 / t626 / t280 * t32 * t36 * t289 + 0.2e1 * t833 + 0.2e1 * t310 * (0.77e2 / 0.14580e5 * t70 * t285 * t806 - t69 * t841 * t641 / 0.180e3 - t69 * t845 * t49 * t52 * t303 * t307 / 0.108e3 + t644 * t841 * t641 / 0.180e3 + t69 * t305 * t303 * t845 * t470 * t307 / 0.324e3)) * t337 - 0.2e1 * t611 * t651 * t674 - t317 * t911 + 0.1174e1 * t911) * t352 - 0.49479000000000000000000000000000000000000000000000e1 * t242 * t682 * t677 * t693 - 0.49479000000000000000000000000000000000000000000000e1 * t684 / t347 / t277 * t32 * t36 * t807 * t351 + 0.57725500000000000000000000000000000000000000000000e1 * t684 * t688 * t342 / t272 / t612 * t351 + 0.81605714700000000000000000000000000000000000000000e1 * t556 * t683 / t342 / t273 * t37 * t351
  t948 = f.my_piecewise3(t260, 0, t947)
  d22 = 0.2e1 * t600 + 0.2e1 * t697 + t6 * (t775 + t948)
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
  t92 = 0.5e1 / 0.9e1 * (tau0 * t86 - t55 / 0.8e1) * t44 * t48
  t93 = 0.1e1 - t92
  t95 = t93 ** 2
  t97 = jnp.exp(-t95 / 0.2e1)
  t100 = 0.7e1 / 0.12960e5 * t82 * t74 + t81 * t93 * t97 / 0.100e3
  t101 = t100 ** 2
  t102 = params.k1 + 0.5e1 / 0.972e3 * t56 + t65 * t66 / t51 / t68 * t77 / 0.576e3 + t101
  t107 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t102)
  t108 = t92 <= 0.1e1
  t109 = jnp.log(DBL_EPSILON)
  t112 = t109 / (-t109 + params.c1)
  t113 = -t112 < t92
  t114 = t92 < -t112
  t115 = f.my_piecewise3(t114, t92, -t112)
  t116 = params.c1 * t115
  t117 = 0.1e1 - t115
  t118 = 0.1e1 / t117
  t120 = jnp.exp(-t116 * t118)
  t121 = f.my_piecewise3(t113, 0, t120)
  t122 = abs(params.d)
  t125 = jnp.log(DBL_EPSILON / t122)
  t128 = (-t125 + params.c2) / t125
  t129 = t92 < -t128
  t130 = f.my_piecewise3(t129, -t128, t92)
  t131 = 0.1e1 - t130
  t134 = jnp.exp(params.c2 / t131)
  t136 = f.my_piecewise3(t129, 0, -params.d * t134)
  t137 = f.my_piecewise3(t108, t121, t136)
  t138 = 0.1e1 - t137
  t141 = t107 * t138 + 0.1174e1 * t137
  t143 = jnp.sqrt(0.3e1)
  t144 = 0.1e1 / t46
  t145 = t61 * t144
  t146 = jnp.sqrt(s0)
  t150 = t145 * t146 / t51 / r0
  t151 = jnp.sqrt(t150)
  t155 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t143 / t151)
  t156 = 0.1e1 - t155
  t157 = t43 * t141 * t156
  t162 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t163 = t5 * t162
  t164 = t43 ** 2
  t165 = 0.1e1 / t164
  t167 = t165 * t141 * t156
  t170 = params.k1 ** 2
  t171 = t102 ** 2
  t173 = t170 / t171
  t174 = t50 * r0
  t176 = 0.1e1 / t52 / t174
  t177 = s0 * t176
  t187 = t60 ** 2
  t188 = t45 ** 2
  t189 = 0.1e1 / t188
  t190 = t187 * t189
  t191 = t66 * s0
  t192 = t67 ** 2
  t205 = -0.5e1 / 0.3e1 * tau0 * t54 + t177 / 0.3e1
  t207 = t49 * t97
  t210 = t81 * t95
  t214 = -0.7e1 / 0.4860e4 * t82 * t73 * t176 - t81 * t205 * t207 / 0.180e3 + t210 * t205 * t207 / 0.180e3
  t217 = -0.10e2 / 0.729e3 * t49 * t177 - t65 * t66 / t51 / t67 / t50 * t77 / 0.108e3 + 0.3e1 / 0.320e3 * t190 * t191 / t192 / r0 * t77 + 0.2e1 * t100 * t214
  t218 = t217 * t138
  t222 = 0.5e1 / 0.9e1 * t205 * t44 * t48
  t223 = f.my_piecewise3(t114, t222, 0)
  t226 = t117 ** 2
  t227 = 0.1e1 / t226
  t228 = t227 * t223
  t230 = -params.c1 * t223 * t118 - t116 * t228
  t232 = f.my_piecewise3(t113, 0, t230 * t120)
  t233 = params.d * params.c2
  t234 = t131 ** 2
  t235 = 0.1e1 / t234
  t236 = f.my_piecewise3(t129, 0, t222)
  t240 = f.my_piecewise3(t129, 0, -t233 * t235 * t236 * t134)
  t241 = f.my_piecewise3(t108, t232, t240)
  t244 = t173 * t218 - t107 * t241 + 0.1174e1 * t241
  t246 = t43 * t244 * t156
  t249 = 3 ** (0.1e1 / 0.6e1)
  t250 = t249 ** 2
  t251 = t250 ** 2
  t252 = t251 * t249
  t253 = t252 * t4
  t254 = t162 * t43
  t255 = t254 * t141
  t256 = t253 * t255
  t258 = 0.1e1 / t151 / t150
  t260 = t258 * t61 * t144
  t265 = t260 * t146 / t51 / t50 * t155
  t268 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t269 = t268 * f.p.zeta_threshold
  t271 = f.my_piecewise3(t20, t269, t21 * t19)
  t272 = t5 * t271
  t274 = 0.1e1 / t164 / t6
  t276 = t274 * t141 * t156
  t280 = t165 * t244 * t156
  t283 = t271 * t165
  t284 = t283 * t141
  t285 = t253 * t284
  t290 = t170 / t171 / t102
  t291 = t217 ** 2
  t296 = 0.1e1 / t52 / t67
  t297 = s0 * t296
  t300 = t67 * t174
  t315 = t66 ** 2
  t316 = t187 * t60 * t189 * t315
  t321 = t48 * t77
  t325 = t214 ** 2
  t333 = 0.40e2 / 0.9e1 * tau0 * t176 - 0.11e2 / 0.9e1 * t297
  t334 = t81 * t333
  t337 = t205 ** 2
  t340 = t64 * t93
  t348 = t81 * t95 * t93
  t350 = t61 * t64
  t354 = 0.77e2 / 0.14580e5 * t82 * t73 * t296 - t334 * t207 / 0.180e3 - t81 * t337 * t61 * t340 * t97 / 0.108e3 + t210 * t333 * t207 / 0.180e3 + t348 * t337 * t350 * t97 / 0.324e3
  t357 = 0.110e3 / 0.2187e4 * t49 * t297 + 0.19e2 / 0.324e3 * t65 * t66 / t51 / t300 * t77 - 0.43e2 / 0.320e3 * t190 * t191 / t192 / t50 * t77 + 0.27e2 / 0.3200e4 * t316 / t52 / t192 / t67 * t44 * t321 + 0.2e1 * t325 + 0.2e1 * t100 * t354
  t365 = 0.5e1 / 0.9e1 * t333 * t44 * t48
  t366 = f.my_piecewise3(t114, t365, 0)
  t367 = params.c1 * t366
  t369 = t223 ** 2
  t374 = 0.1e1 / t226 / t117
  t380 = -t116 * t227 * t366 - 0.2e1 * t116 * t374 * t369 - 0.2e1 * params.c1 * t369 * t227 - t367 * t118
  t382 = t230 ** 2
  t385 = f.my_piecewise3(t113, 0, t380 * t120 + t382 * t120)
  t387 = 0.1e1 / t234 / t131
  t388 = t236 ** 2
  t393 = f.my_piecewise3(t129, 0, t365)
  t397 = params.c2 ** 2
  t398 = params.d * t397
  t399 = t234 ** 2
  t400 = 0.1e1 / t399
  t405 = f.my_piecewise3(t129, 0, -t233 * t235 * t393 * t134 - 0.2e1 * t233 * t387 * t388 * t134 - t398 * t400 * t388 * t134)
  t406 = f.my_piecewise3(t108, t385, t405)
  t409 = -0.2e1 * t290 * t291 * t138 + t173 * t357 * t138 - 0.2e1 * t173 * t217 * t241 - t107 * t406 + 0.1174e1 * t406
  t411 = t43 * t409 * t156
  t414 = t271 * t43
  t415 = t414 * t244
  t416 = t253 * t415
  t419 = t414 * t141
  t420 = t253 * t419
  t425 = 0.1e1 / t151 / t56 * t44 * t48 / 0.6e1
  t427 = t425 * t297 * t155
  t434 = t260 * t146 / t51 / t174 * t155
  t437 = t3 ** 2
  t439 = t2 * t437 * jnp.pi
  t440 = t439 * t419
  t441 = 0.1e1 / t146
  t444 = t49 * t155
  t445 = t441 / t52 * t444
  t448 = -0.3e1 / 0.8e1 * t42 * t157 - t163 * t167 / 0.4e1 - 0.3e1 / 0.4e1 * t163 * t246 - 0.49479000000000000000000000000000000000000000000000e1 * t256 * t265 + t272 * t276 / 0.12e2 - t272 * t280 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t285 * t265 - 0.3e1 / 0.8e1 * t272 * t411 - 0.49479000000000000000000000000000000000000000000000e1 * t416 * t265 - 0.29687400000000000000000000000000000000000000000000e2 * t420 * t427 + 0.57725500000000000000000000000000000000000000000000e1 * t420 * t434 + 0.81605714700000000000000000000000000000000000000000e1 * t440 * t445
  t449 = f.my_piecewise3(t1, 0, t448)
  t451 = r1 <= f.p.dens_threshold
  t452 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t453 = 0.1e1 + t452
  t454 = t453 <= f.p.zeta_threshold
  t455 = t453 ** (0.1e1 / 0.3e1)
  t456 = t455 ** 2
  t457 = 0.1e1 / t456
  t459 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t460 = t459 ** 2
  t464 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t468 = f.my_piecewise3(t454, 0, 0.4e1 / 0.9e1 * t457 * t460 + 0.4e1 / 0.3e1 * t455 * t464)
  t469 = t5 * t468
  t470 = r1 ** 2
  t471 = r1 ** (0.1e1 / 0.3e1)
  t472 = t471 ** 2
  t474 = 0.1e1 / t472 / t470
  t475 = s2 * t474
  t478 = s2 ** 2
  t479 = t470 ** 2
  t485 = t48 * s2 * t474
  t488 = jnp.exp(-0.27e2 / 0.80e2 * t72 * t485)
  t501 = 0.5e1 / 0.9e1 * (tau1 / t472 / r1 - t475 / 0.8e1) * t44 * t48
  t502 = 0.1e1 - t501
  t504 = t502 ** 2
  t506 = jnp.exp(-t504 / 0.2e1)
  t510 = (0.7e1 / 0.12960e5 * t82 * t485 + t81 * t502 * t506 / 0.100e3) ** 2
  t520 = f.my_piecewise3(t501 < -t112, t501, -t112)
  t525 = jnp.exp(-params.c1 * t520 / (0.1e1 - t520))
  t526 = f.my_piecewise3(-t112 < t501, 0, t525)
  t527 = t501 < -t128
  t528 = f.my_piecewise3(t527, -t128, t501)
  t532 = jnp.exp(params.c2 / (0.1e1 - t528))
  t534 = f.my_piecewise3(t527, 0, -params.d * t532)
  t535 = f.my_piecewise3(t501 <= 0.1e1, t526, t534)
  t539 = (0.1e1 + params.k1 * (0.1e1 - params.k1 / (params.k1 + 0.5e1 / 0.972e3 * t49 * t475 + t65 * t478 / t471 / t479 / r1 * t488 / 0.576e3 + t510))) * (0.1e1 - t535) + 0.1174e1 * t535
  t541 = jnp.sqrt(s2)
  t546 = jnp.sqrt(t145 * t541 / t471 / r1)
  t550 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t143 / t546)
  t551 = 0.1e1 - t550
  t552 = t43 * t539 * t551
  t557 = f.my_piecewise3(t454, 0, 0.4e1 / 0.3e1 * t455 * t459)
  t558 = t5 * t557
  t560 = t165 * t539 * t551
  t564 = f.my_piecewise3(t454, t269, t455 * t453)
  t565 = t5 * t564
  t567 = t274 * t539 * t551
  t571 = f.my_piecewise3(t451, 0, -0.3e1 / 0.8e1 * t469 * t552 - t558 * t560 / 0.4e1 + t565 * t567 / 0.12e2)
  t576 = 0.1e1 / t164 / t24
  t595 = t24 ** 2
  t599 = 0.6e1 * t33 - 0.6e1 * t16 / t595
  t600 = f.my_piecewise5(t10, 0, t14, 0, t599)
  t604 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t600)
  t614 = t171 ** 2
  t628 = 0.1e1 / t52 / t68
  t629 = s0 * t628
  t651 = t187 ** 2
  t655 = t192 ** 2
  t671 = -0.440e3 / 0.27e2 * tau0 * t296 + 0.154e3 / 0.27e2 * t629
  t676 = t205 * t97
  t680 = t337 * t205
  t681 = t81 * t680
  t696 = t95 ** 2
  t716 = 0.5e1 / 0.9e1 * t671 * t44 * t48
  t717 = f.my_piecewise3(t114, t716, 0)
  t722 = t369 * t223
  t726 = t226 ** 2
  t745 = f.my_piecewise3(t113, 0, (-params.c1 * t717 * t118 - 0.6e1 * t367 * t228 - 0.6e1 * params.c1 * t722 * t374 - 0.6e1 * t116 / t726 * t722 - 0.6e1 * t116 * t374 * t223 * t366 - t116 * t227 * t717) * t120 + 0.3e1 * t380 * t230 * t120 + t382 * t230 * t120)
  t746 = t388 * t236
  t753 = t236 * t134 * t393
  t762 = f.my_piecewise3(t129, 0, t716)
  t777 = f.my_piecewise3(t129, 0, -0.6e1 * t233 * t400 * t746 * t134 - 0.6e1 * t233 * t387 * t753 - 0.6e1 * t398 / t399 / t131 * t746 * t134 - t233 * t235 * t762 * t134 - 0.3e1 * t398 * t400 * t753 - params.d * t397 * params.c2 / t399 / t234 * t746 * t134)
  t778 = f.my_piecewise3(t108, t745, t777)
  t797 = t441 * t86
  t810 = -0.3e1 / 0.4e1 * t163 * t280 - 0.5e1 / 0.36e2 * t272 * t576 * t141 * t156 - 0.3e1 / 0.8e1 * t42 * t167 + t163 * t276 / 0.4e1 - 0.9e1 / 0.8e1 * t163 * t411 - 0.3e1 / 0.8e1 * t5 * t604 * t157 - 0.9e1 / 0.8e1 * t42 * t246 - 0.3e1 / 0.8e1 * t272 * t165 * t409 * t156 - 0.3e1 / 0.8e1 * t272 * t43 * (0.6e1 * t170 / t614 * t291 * t217 * t138 - 0.6e1 * t290 * t218 * t357 + 0.6e1 * t290 * t291 * t241 + t173 * (-0.1540e4 / 0.6561e4 * t49 * t629 - 0.209e3 / 0.486e3 * t65 * t66 / t51 / t192 * t77 + 0.797e3 / 0.480e3 * t190 * t191 / t192 / t174 * t77 - 0.729e3 / 0.3200e4 * t316 / t52 / t192 / t68 * t44 * t321 + 0.243e3 / 0.32000e5 * t651 * t189 * t315 * s0 / t51 / t655 * t61 * t64 * t77 + 0.6e1 * t214 * t354 + 0.2e1 * t100 * (-0.539e3 / 0.21870e5 * t82 * t73 * t628 - t81 * t671 * t207 / 0.180e3 - t334 * t61 * t340 * t676 / 0.36e2 + 0.5e1 / 0.162e3 * t681 * t189 * t97 - 0.5e1 / 0.81e2 * t681 * t189 * t95 * t97 + t210 * t671 * t207 / 0.180e3 + t348 * t333 * t350 * t676 / 0.108e3 + 0.5e1 / 0.486e3 * t81 * t696 * t680 * t189 * t97)) * t138 - 0.3e1 * t173 * t357 * t241 - 0.3e1 * t173 * t217 * t406 - t107 * t778 + 0.1174e1 * t778) * t156 + t272 * t274 * t244 * t156 / 0.4e1 - 0.32302153261130400000000000000000000000000000000000e3 * t253 * t414 * t141 / t174 * t258 * t155 - 0.24481714410000000000000000000000000000000000000000e2 * t440 * t797 * t444 + 0.24481714410000000000000000000000000000000000000000e2 * t439 * t255 * t445 + 0.81605714700000000000000000000000000000000000000000e1 * t439 * t284 * t445 + 0.24481714410000000000000000000000000000000000000000e2 * t439 * t415 * t445
  t812 = 0.1e1 / t3 / t45
  t873 = t146 * s0
  t887 = 0.16321142940000000000000000000000000000000000000000e2 * t2 * t812 * t419 * t44 * t63 * t797 * t155 - 0.29687400000000000000000000000000000000000000000000e2 * t285 * t427 - 0.74218500000000000000000000000000000000000000000000e1 * t253 * t414 * t409 * t265 - 0.74218500000000000000000000000000000000000000000000e1 * t253 * t41 * t43 * t141 * t265 - 0.49479000000000000000000000000000000000000000000000e1 * t253 * t162 * t165 * t141 * t265 - 0.14843700000000000000000000000000000000000000000000e2 * t253 * t254 * t244 * t265 - 0.89062200000000000000000000000000000000000000000000e2 * t256 * t427 + 0.20781180000000000000000000000000000000000000000000e3 * t420 * t425 * t629 * t155 - 0.19241833333333333333333333333333333333333333333333e2 * t420 * t260 * t146 / t51 / t67 * t155 + 0.17317650000000000000000000000000000000000000000000e2 * t416 * t434 + 0.17317650000000000000000000000000000000000000000000e2 * t256 * t434 + 0.57725500000000000000000000000000000000000000000000e1 * t285 * t434 - 0.89062200000000000000000000000000000000000000000000e2 * t416 * t427 + 0.16493000000000000000000000000000000000000000000000e1 * t253 * t271 * t274 * t141 * t265 - 0.49479000000000000000000000000000000000000000000000e1 * t253 * t283 * t244 * t265 - 0.16493000000000000000000000000000000000000000000000e2 * t252 * t812 * t414 * t141 / t151 * t45 * t67 / t300 * t155
  t889 = f.my_piecewise3(t1, 0, t810 + t887)
  t899 = f.my_piecewise5(t14, 0, t10, 0, -t599)
  t903 = f.my_piecewise3(t454, 0, -0.8e1 / 0.27e2 / t456 / t453 * t460 * t459 + 0.4e1 / 0.3e1 * t457 * t459 * t464 + 0.4e1 / 0.3e1 * t455 * t899)
  t916 = f.my_piecewise3(t451, 0, -0.3e1 / 0.8e1 * t5 * t903 * t552 - 0.3e1 / 0.8e1 * t469 * t560 + t558 * t567 / 0.4e1 - 0.5e1 / 0.36e2 * t565 * t576 * t539 * t551)
  d111 = 0.3e1 * t449 + 0.3e1 * t571 + t6 * (t889 + t916)

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
  t28 = params.k1 ** 2
  t29 = 6 ** (0.1e1 / 0.3e1)
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = t29 * t33
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t40 = s0 * t39
  t41 = t34 * t40
  t45 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t46 = t29 ** 2
  t48 = t31 * t30
  t49 = 0.1e1 / t48
  t50 = t45 * t46 * t49
  t51 = s0 ** 2
  t52 = t35 ** 2
  t53 = t52 * r0
  t55 = 0.1e1 / t36 / t53
  t56 = t51 * t55
  t57 = t45 * t29
  t58 = t33 * s0
  t59 = t58 * t39
  t62 = jnp.exp(-0.27e2 / 0.80e2 * t57 * t59)
  t66 = jnp.sqrt(0.146e3)
  t67 = t66 * t29
  t71 = 0.1e1 / t37 / r0
  t77 = 0.5e1 / 0.9e1 * (tau0 * t71 - t40 / 0.8e1) * t29 * t33
  t78 = 0.1e1 - t77
  t80 = t78 ** 2
  t82 = jnp.exp(-t80 / 0.2e1)
  t85 = 0.7e1 / 0.12960e5 * t67 * t59 + t66 * t78 * t82 / 0.100e3
  t86 = t85 ** 2
  t87 = params.k1 + 0.5e1 / 0.972e3 * t41 + t50 * t56 * t62 / 0.576e3 + t86
  t88 = t87 ** 2
  t89 = t88 ** 2
  t91 = t28 / t89
  t92 = t35 * r0
  t94 = 0.1e1 / t37 / t92
  t95 = s0 * t94
  t98 = t52 * t35
  t105 = t45 ** 2
  t106 = t30 ** 2
  t107 = 0.1e1 / t106
  t108 = t105 * t107
  t109 = t51 * s0
  t110 = t52 ** 2
  t111 = t110 * r0
  t123 = -0.5e1 / 0.3e1 * tau0 * t39 + t95 / 0.3e1
  t125 = t34 * t82
  t128 = t66 * t80
  t132 = -0.7e1 / 0.4860e4 * t67 * t58 * t94 - t66 * t123 * t125 / 0.180e3 + t128 * t123 * t125 / 0.180e3
  t135 = -0.10e2 / 0.729e3 * t34 * t95 - t50 * t51 / t36 / t98 * t62 / 0.108e3 + 0.3e1 / 0.320e3 * t108 * t109 / t111 * t62 + 0.2e1 * t85 * t132
  t136 = t135 ** 2
  t137 = t136 * t135
  t138 = t77 <= 0.1e1
  t139 = jnp.log(DBL_EPSILON)
  t142 = t139 / (-t139 + params.c1)
  t143 = -t142 < t77
  t144 = t77 < -t142
  t145 = f.my_piecewise3(t144, t77, -t142)
  t146 = params.c1 * t145
  t147 = 0.1e1 - t145
  t148 = 0.1e1 / t147
  t150 = jnp.exp(-t146 * t148)
  t151 = f.my_piecewise3(t143, 0, t150)
  t152 = abs(params.d)
  t155 = jnp.log(DBL_EPSILON / t152)
  t158 = (-t155 + params.c2) / t155
  t159 = t77 < -t158
  t160 = f.my_piecewise3(t159, -t158, t77)
  t161 = 0.1e1 - t160
  t164 = jnp.exp(params.c2 / t161)
  t166 = f.my_piecewise3(t159, 0, -params.d * t164)
  t167 = f.my_piecewise3(t138, t151, t166)
  t168 = 0.1e1 - t167
  t174 = t28 / t88 / t87
  t175 = t135 * t168
  t177 = 0.1e1 / t37 / t52
  t178 = s0 * t177
  t181 = t52 * t92
  t196 = t51 ** 2
  t197 = t105 * t45 * t107 * t196
  t198 = t110 * t52
  t202 = t33 * t62
  t206 = t132 ** 2
  t214 = 0.40e2 / 0.9e1 * tau0 * t94 - 0.11e2 / 0.9e1 * t178
  t215 = t66 * t214
  t218 = t123 ** 2
  t221 = t49 * t78
  t222 = t221 * t82
  t228 = t80 * t78
  t229 = t66 * t228
  t231 = t46 * t49
  t232 = t231 * t82
  t235 = 0.77e2 / 0.14580e5 * t67 * t58 * t177 - t215 * t125 / 0.180e3 - t66 * t218 * t46 * t222 / 0.108e3 + t128 * t214 * t125 / 0.180e3 + t229 * t218 * t232 / 0.324e3
  t238 = 0.110e3 / 0.2187e4 * t34 * t178 + 0.19e2 / 0.324e3 * t50 * t51 / t36 / t181 * t62 - 0.43e2 / 0.320e3 * t108 * t109 / t110 / t35 * t62 + 0.27e2 / 0.3200e4 * t197 / t37 / t198 * t29 * t202 + 0.2e1 * t206 + 0.2e1 * t85 * t235
  t244 = 0.5e1 / 0.9e1 * t123 * t29 * t33
  t245 = f.my_piecewise3(t144, t244, 0)
  t248 = t147 ** 2
  t249 = 0.1e1 / t248
  t250 = t249 * t245
  t252 = -params.c1 * t245 * t148 - t146 * t250
  t254 = f.my_piecewise3(t143, 0, t252 * t150)
  t255 = params.d * params.c2
  t256 = t161 ** 2
  t257 = 0.1e1 / t256
  t258 = f.my_piecewise3(t159, 0, t244)
  t262 = f.my_piecewise3(t159, 0, -t255 * t257 * t258 * t164)
  t263 = f.my_piecewise3(t138, t254, t262)
  t268 = t28 / t88
  t270 = 0.1e1 / t37 / t53
  t271 = s0 * t270
  t293 = t105 ** 2
  t296 = t293 * t107 * t196 * s0
  t297 = t110 ** 2
  t301 = t49 * t62
  t313 = -0.440e3 / 0.27e2 * tau0 * t177 + 0.154e3 / 0.27e2 * t271
  t314 = t66 * t313
  t318 = t123 * t82
  t319 = t221 * t318
  t322 = t218 * t123
  t323 = t66 * t322
  t335 = t231 * t318
  t338 = t80 ** 2
  t339 = t66 * t338
  t344 = -0.539e3 / 0.21870e5 * t67 * t58 * t270 - t314 * t125 / 0.180e3 - t215 * t46 * t319 / 0.36e2 + 0.5e1 / 0.162e3 * t323 * t107 * t82 - 0.5e1 / 0.81e2 * t323 * t107 * t80 * t82 + t128 * t313 * t125 / 0.180e3 + t229 * t214 * t335 / 0.108e3 + 0.5e1 / 0.486e3 * t339 * t322 * t107 * t82
  t347 = -0.1540e4 / 0.6561e4 * t34 * t271 - 0.209e3 / 0.486e3 * t50 * t51 / t36 / t110 * t62 + 0.797e3 / 0.480e3 * t108 * t109 / t110 / t92 * t62 - 0.729e3 / 0.3200e4 * t197 / t37 / t110 / t53 * t29 * t202 + 0.243e3 / 0.32000e5 * t296 / t36 / t297 * t46 * t301 + 0.6e1 * t132 * t235 + 0.2e1 * t85 * t344
  t355 = 0.5e1 / 0.9e1 * t214 * t29 * t33
  t356 = f.my_piecewise3(t144, t355, 0)
  t357 = params.c1 * t356
  t359 = t245 ** 2
  t364 = 0.1e1 / t248 / t147
  t365 = t364 * t359
  t370 = -t146 * t249 * t356 - 0.2e1 * params.c1 * t359 * t249 - 0.2e1 * t146 * t365 - t357 * t148
  t372 = t252 ** 2
  t375 = f.my_piecewise3(t143, 0, t370 * t150 + t372 * t150)
  t376 = t256 * t161
  t377 = 0.1e1 / t376
  t378 = t258 ** 2
  t383 = f.my_piecewise3(t159, 0, t355)
  t387 = params.c2 ** 2
  t388 = params.d * t387
  t389 = t256 ** 2
  t390 = 0.1e1 / t389
  t395 = f.my_piecewise3(t159, 0, -t255 * t257 * t383 * t164 - 0.2e1 * t255 * t377 * t378 * t164 - t388 * t390 * t378 * t164)
  t396 = f.my_piecewise3(t138, t375, t395)
  t404 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t87)
  t407 = 0.5e1 / 0.9e1 * t313 * t29 * t33
  t408 = f.my_piecewise3(t144, t407, 0)
  t409 = params.c1 * t408
  t413 = t359 * t245
  t417 = t248 ** 2
  t418 = 0.1e1 / t417
  t422 = t364 * t245
  t428 = -t146 * t249 * t408 - 0.6e1 * t146 * t422 * t356 - 0.6e1 * t146 * t418 * t413 - 0.6e1 * params.c1 * t413 * t364 - t409 * t148 - 0.6e1 * t357 * t250
  t436 = f.my_piecewise3(t143, 0, 0.3e1 * t370 * t252 * t150 + t372 * t252 * t150 + t428 * t150)
  t437 = t378 * t258
  t442 = t255 * t377
  t443 = t258 * t164
  t444 = t443 * t383
  t448 = 0.1e1 / t389 / t161
  t453 = f.my_piecewise3(t159, 0, t407)
  t457 = t388 * t390
  t461 = params.d * t387 * params.c2
  t463 = 0.1e1 / t389 / t256
  t468 = f.my_piecewise3(t159, 0, -t255 * t257 * t453 * t164 - 0.6e1 * t255 * t390 * t437 * t164 - 0.6e1 * t388 * t448 * t437 * t164 - t461 * t463 * t437 * t164 - 0.6e1 * t442 * t444 - 0.3e1 * t457 * t444)
  t469 = f.my_piecewise3(t138, t436, t468)
  t472 = 0.6e1 * t91 * t137 * t168 - 0.6e1 * t174 * t175 * t238 + 0.6e1 * t174 * t136 * t263 + t268 * t347 * t168 - 0.3e1 * t268 * t238 * t263 - 0.3e1 * t268 * t135 * t396 - t404 * t469 + 0.1174e1 * t469
  t474 = jnp.sqrt(0.3e1)
  t475 = 0.1e1 / t31
  t476 = t46 * t475
  t477 = jnp.sqrt(s0)
  t479 = 0.1e1 / t36 / r0
  t481 = t476 * t477 * t479
  t482 = jnp.sqrt(t481)
  t486 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t474 / t482)
  t487 = 0.1e1 - t486
  t488 = t27 * t472 * t487
  t491 = 3 ** (0.1e1 / 0.6e1)
  t492 = t491 ** 2
  t493 = t492 ** 2
  t494 = t493 * t491
  t495 = t494 * t4
  t496 = t25 * t27
  t497 = t495 * t496
  t500 = t404 * t168 + 0.1174e1 * t167
  t501 = 0.1e1 / t92
  t504 = 0.1e1 / t482 / t481
  t505 = t504 * t486
  t506 = t500 * t501 * t505
  t509 = t23 ** 2
  t510 = 0.1e1 / t509
  t511 = t6 ** 2
  t512 = 0.1e1 / t511
  t514 = -t16 * t512 + t7
  t515 = f.my_piecewise5(t10, 0, t14, 0, t514)
  t516 = t515 ** 2
  t519 = t511 * t6
  t520 = 0.1e1 / t519
  t523 = 0.2e1 * t16 * t520 - 0.2e1 * t512
  t524 = f.my_piecewise5(t10, 0, t14, 0, t523)
  t528 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t510 * t516 + 0.4e1 / 0.3e1 * t23 * t524)
  t529 = t5 * t528
  t530 = t27 ** 2
  t531 = 0.1e1 / t530
  t533 = t531 * t500 * t487
  t538 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t515)
  t539 = t5 * t538
  t541 = 0.1e1 / t530 / t6
  t543 = t541 * t500 * t487
  t549 = t268 * t175 - t404 * t263 + 0.1174e1 * t263
  t551 = t541 * t549 * t487
  t554 = t136 * t168
  t559 = t135 * t263
  t564 = -0.2e1 * t174 * t554 + t268 * t238 * t168 - 0.2e1 * t268 * t559 - t404 * t396 + 0.1174e1 * t396
  t566 = t531 * t564 * t487
  t569 = t3 ** 2
  t571 = t2 * t569 * jnp.pi
  t572 = t496 * t500
  t573 = t571 * t572
  t574 = 0.1e1 / t477
  t575 = t574 * t71
  t576 = t34 * t486
  t577 = t575 * t576
  t580 = t538 * t27
  t581 = t580 * t500
  t582 = t571 * t581
  t585 = t574 / t37 * t576
  t588 = t25 * t531
  t589 = t588 * t500
  t590 = t571 * t589
  t593 = t496 * t549
  t594 = t571 * t593
  t598 = 0.1e1 / t3 / t30
  t599 = t2 * t598
  t600 = t599 * t572
  t601 = t29 * t48
  t603 = t601 * t575 * t486
  t606 = t495 * t572
  t609 = 0.1e1 / t482 / t41 / 0.6e1
  t611 = t609 * t29 * t33
  t613 = t611 * t271 * t486
  t617 = t504 * t46 * t475
  t622 = t617 * t477 / t36 / t52 * t486
  t625 = t495 * t593
  t630 = t617 * t477 / t36 / t92 * t486
  t633 = t495 * t581
  t636 = -0.3e1 / 0.8e1 * t26 * t488 - 0.32302153261130400000000000000000000000000000000000e3 * t497 * t506 - 0.3e1 / 0.8e1 * t529 * t533 + t539 * t543 / 0.4e1 + t26 * t551 / 0.4e1 - 0.3e1 / 0.8e1 * t26 * t566 - 0.24481714410000000000000000000000000000000000000000e2 * t573 * t577 + 0.24481714410000000000000000000000000000000000000000e2 * t582 * t585 + 0.81605714700000000000000000000000000000000000000000e1 * t590 * t585 + 0.24481714410000000000000000000000000000000000000000e2 * t594 * t585 + 0.16321142940000000000000000000000000000000000000000e2 * t600 * t603 + 0.20781180000000000000000000000000000000000000000000e3 * t606 * t613 - 0.19241833333333333333333333333333333333333333333333e2 * t606 * t622 + 0.17317650000000000000000000000000000000000000000000e2 * t625 * t630 + 0.17317650000000000000000000000000000000000000000000e2 * t633 * t630
  t637 = t495 * t589
  t641 = t611 * t178 * t486
  t644 = t25 * t541
  t645 = t644 * t500
  t646 = t495 * t645
  t651 = t617 * t477 / t36 / t35 * t486
  t654 = t588 * t549
  t655 = t495 * t654
  t660 = t496 * t564
  t661 = t495 * t660
  t664 = t528 * t27
  t665 = t664 * t500
  t666 = t495 * t665
  t669 = t538 * t531
  t670 = t669 * t500
  t671 = t495 * t670
  t674 = t580 * t549
  t675 = t495 * t674
  t681 = t27 * t564 * t487
  t685 = 0.1e1 / t509 / t19
  t689 = t510 * t515
  t692 = t511 ** 2
  t693 = 0.1e1 / t692
  t696 = -0.6e1 * t16 * t693 + 0.6e1 * t520
  t697 = f.my_piecewise5(t10, 0, t14, 0, t696)
  t701 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t685 * t516 * t515 + 0.4e1 / 0.3e1 * t689 * t524 + 0.4e1 / 0.3e1 * t23 * t697)
  t702 = t5 * t701
  t704 = t27 * t500 * t487
  t708 = t27 * t549 * t487
  t712 = t531 * t549 * t487
  t716 = 0.1e1 / t530 / t511
  t718 = t716 * t500 * t487
  t721 = t494 * t598
  t722 = t721 * t496
  t724 = t477 * s0
  t726 = 0.1e1 / t52
  t730 = 0.1e1 / t482 * t30 / t724 / t726 / 0.36e2
  t731 = t500 * t730
  t734 = t724 / t181 * t486
  t735 = t731 * t734
  t738 = 0.57725500000000000000000000000000000000000000000000e1 * t637 * t630 - 0.89062200000000000000000000000000000000000000000000e2 * t625 * t641 + 0.16493000000000000000000000000000000000000000000000e1 * t646 * t651 - 0.49479000000000000000000000000000000000000000000000e1 * t655 * t651 - 0.29687400000000000000000000000000000000000000000000e2 * t637 * t641 - 0.74218500000000000000000000000000000000000000000000e1 * t661 * t651 - 0.74218500000000000000000000000000000000000000000000e1 * t666 * t651 - 0.49479000000000000000000000000000000000000000000000e1 * t671 * t651 - 0.14843700000000000000000000000000000000000000000000e2 * t675 * t651 - 0.89062200000000000000000000000000000000000000000000e2 * t633 * t641 - 0.9e1 / 0.8e1 * t539 * t681 - 0.3e1 / 0.8e1 * t702 * t704 - 0.9e1 / 0.8e1 * t529 * t708 - 0.3e1 / 0.4e1 * t539 * t712 - 0.5e1 / 0.36e2 * t26 * t718 - 0.59374800000000000000000000000000000000000000000000e3 * t722 * t735
  t740 = f.my_piecewise3(t1, 0, t636 + t738)
  t742 = r1 <= f.p.dens_threshold
  t743 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t744 = 0.1e1 + t743
  t745 = t744 <= f.p.zeta_threshold
  t746 = t744 ** (0.1e1 / 0.3e1)
  t747 = t746 ** 2
  t749 = 0.1e1 / t747 / t744
  t751 = f.my_piecewise5(t14, 0, t10, 0, -t514)
  t752 = t751 ** 2
  t756 = 0.1e1 / t747
  t757 = t756 * t751
  t759 = f.my_piecewise5(t14, 0, t10, 0, -t523)
  t763 = f.my_piecewise5(t14, 0, t10, 0, -t696)
  t767 = f.my_piecewise3(t745, 0, -0.8e1 / 0.27e2 * t749 * t752 * t751 + 0.4e1 / 0.3e1 * t757 * t759 + 0.4e1 / 0.3e1 * t746 * t763)
  t768 = t5 * t767
  t769 = r1 ** 2
  t770 = r1 ** (0.1e1 / 0.3e1)
  t771 = t770 ** 2
  t773 = 0.1e1 / t771 / t769
  t774 = s2 * t773
  t777 = s2 ** 2
  t778 = t769 ** 2
  t784 = t33 * s2 * t773
  t787 = jnp.exp(-0.27e2 / 0.80e2 * t57 * t784)
  t800 = 0.5e1 / 0.9e1 * (tau1 / t771 / r1 - t774 / 0.8e1) * t29 * t33
  t801 = 0.1e1 - t800
  t803 = t801 ** 2
  t805 = jnp.exp(-t803 / 0.2e1)
  t809 = (0.7e1 / 0.12960e5 * t67 * t784 + t66 * t801 * t805 / 0.100e3) ** 2
  t819 = f.my_piecewise3(t800 < -t142, t800, -t142)
  t824 = jnp.exp(-params.c1 * t819 / (0.1e1 - t819))
  t825 = f.my_piecewise3(-t142 < t800, 0, t824)
  t826 = t800 < -t158
  t827 = f.my_piecewise3(t826, -t158, t800)
  t831 = jnp.exp(params.c2 / (0.1e1 - t827))
  t833 = f.my_piecewise3(t826, 0, -params.d * t831)
  t834 = f.my_piecewise3(t800 <= 0.1e1, t825, t833)
  t838 = (0.1e1 + params.k1 * (0.1e1 - params.k1 / (params.k1 + 0.5e1 / 0.972e3 * t34 * t774 + t50 * t777 / t770 / t778 / r1 * t787 / 0.576e3 + t809))) * (0.1e1 - t834) + 0.1174e1 * t834
  t840 = jnp.sqrt(s2)
  t845 = jnp.sqrt(t476 * t840 / t770 / r1)
  t849 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t474 / t845)
  t850 = 0.1e1 - t849
  t851 = t27 * t838 * t850
  t859 = f.my_piecewise3(t745, 0, 0.4e1 / 0.9e1 * t756 * t752 + 0.4e1 / 0.3e1 * t746 * t759)
  t860 = t5 * t859
  t862 = t531 * t838 * t850
  t867 = f.my_piecewise3(t745, 0, 0.4e1 / 0.3e1 * t746 * t751)
  t868 = t5 * t867
  t870 = t541 * t838 * t850
  t874 = f.my_piecewise3(t745, t22, t746 * t744)
  t875 = t5 * t874
  t877 = t716 * t838 * t850
  t881 = f.my_piecewise3(t742, 0, -0.3e1 / 0.8e1 * t768 * t851 - 0.3e1 / 0.8e1 * t860 * t862 + t868 * t870 / 0.4e1 - 0.5e1 / 0.36e2 * t875 * t877)
  t884 = 0.1e1 / t530 / t519
  t895 = t136 ** 2
  t905 = t238 ** 2
  t919 = 0.1e1 / t37 / t98
  t920 = s0 * t919
  t924 = 0.1e1 / t36 / t111
  t949 = t106 ** 2
  t959 = t235 ** 2
  t969 = 0.6160e4 / 0.81e2 * tau0 * t270 - 0.2618e4 / 0.81e2 * t920
  t977 = t107 * t218 * t82
  t980 = t214 ** 2
  t990 = t218 ** 2
  t992 = t66 * t990 * t107
  t994 = t33 * t82
  t1021 = 0.9163e4 / 0.65610e5 * t67 * t58 * t919 - t66 * t969 * t125 / 0.180e3 - t314 * t46 * t319 / 0.27e2 + 0.5e1 / 0.27e2 * t215 * t977 - t66 * t980 * t46 * t222 / 0.36e2 - 0.10e2 / 0.27e2 * t215 * t107 * t80 * t218 * t82 + 0.125e3 / 0.1458e4 * t992 * t78 * t29 * t994 - 0.125e3 / 0.2187e4 * t992 * t228 * t29 * t994 + t128 * t969 * t125 / 0.180e3 + t229 * t313 * t335 / 0.81e2 + t229 * t980 * t232 / 0.108e3 + 0.5e1 / 0.81e2 * t339 * t214 * t977 + 0.25e2 / 0.4374e4 * t66 * t338 * t78 * t990 * t107 * t29 * t994
  t1038 = 0.5e1 / 0.9e1 * t969 * t29 * t33
  t1039 = f.my_piecewise3(t144, t1038, 0)
  t1046 = t356 ** 2
  t1050 = t359 ** 2
  t1076 = t370 ** 2
  t1082 = t372 ** 2
  t1085 = f.my_piecewise3(t143, 0, (-params.c1 * t1039 * t148 - 0.8e1 * t409 * t250 - 0.36e2 * t357 * t365 - 0.6e1 * params.c1 * t1046 * t249 - 0.24e2 * params.c1 * t1050 * t418 - 0.24e2 * t146 / t417 / t147 * t1050 - 0.36e2 * t146 * t418 * t359 * t356 - 0.6e1 * t146 * t364 * t1046 - 0.8e1 * t146 * t422 * t408 - t146 * t249 * t1039) * t150 + 0.4e1 * t428 * t252 * t150 + 0.3e1 * t1076 * t150 + 0.6e1 * t370 * t372 * t150 + t1082 * t150)
  t1086 = t378 ** 2
  t1093 = t378 * t164 * t383
  t1100 = t383 ** 2
  t1108 = t443 * t453
  t1117 = f.my_piecewise3(t159, 0, t1038)
  t1130 = t387 ** 2
  t1132 = t389 ** 2
  t1137 = -0.24e2 * t255 * t448 * t1086 * t164 - 0.36e2 * t255 * t390 * t1093 - 0.36e2 * t388 * t463 * t1086 * t164 - 0.6e1 * t255 * t377 * t1100 * t164 - 0.36e2 * t388 * t448 * t1093 - 0.8e1 * t442 * t1108 - 0.12e2 * t461 / t389 / t376 * t1086 * t164 - t255 * t257 * t1117 * t164 - 0.4e1 * t457 * t1108 - 0.3e1 * t388 * t390 * t1100 * t164 - 0.6e1 * t461 * t463 * t1093 - params.d * t1130 / t1132 * t1086 * t164
  t1138 = f.my_piecewise3(t159, 0, t1137)
  t1139 = f.my_piecewise3(t138, t1085, t1138)
  t1142 = -0.24e2 * t28 / t89 / t87 * t895 * t168 + 0.36e2 * t91 * t554 * t238 - 0.24e2 * t91 * t137 * t263 - 0.6e1 * t174 * t905 * t168 + 0.24e2 * t174 * t559 * t238 - 0.8e1 * t174 * t175 * t347 + 0.12e2 * t174 * t136 * t396 + t268 * (0.26180e5 / 0.19683e5 * t34 * t920 + 0.5225e4 / 0.1458e4 * t50 * t51 * t924 * t62 - 0.5929e4 / 0.288e3 * t108 * t109 / t198 * t62 + 0.2949e4 / 0.640e3 * t197 / t37 / t110 / t98 * t29 * t202 - 0.1053e4 / 0.3200e4 * t296 / t36 / t297 / r0 * t46 * t301 + 0.6561e4 / 0.160000e6 * t293 * t45 / t949 * t196 * t51 / t297 / t52 * t62 + 0.6e1 * t959 + 0.8e1 * t132 * t344 + 0.2e1 * t85 * t1021) * t168 - 0.4e1 * t268 * t347 * t263 - 0.6e1 * t268 * t238 * t396 - 0.4e1 * t268 * t135 * t469 - t404 * t1139 + 0.1174e1 * t1139
  t1187 = 0.10e2 / 0.27e2 * t26 * t884 * t500 * t487 + t539 * t551 - 0.9e1 / 0.4e1 * t529 * t681 - 0.3e1 / 0.8e1 * t26 * t27 * t1142 * t487 - t702 * t533 / 0.2e1 - 0.3e1 / 0.2e1 * t529 * t712 - 0.3e1 / 0.2e1 * t539 * t488 + 0.12920861304452160000000000000000000000000000000000e4 * t497 * t500 * t726 * t505 - 0.12920861304452160000000000000000000000000000000000e4 * t495 * t580 * t506 - 0.43069537681507200000000000000000000000000000000000e3 * t495 * t588 * t506 - 0.12920861304452160000000000000000000000000000000000e4 * t497 * t549 * t501 * t505 + 0.39583200000000000000000000000000000000000000000000e2 * t646 * t641 - 0.19791600000000000000000000000000000000000000000000e2 * t495 * t669 * t549 * t651 - 0.98958000000000000000000000000000000000000000000000e1 * t495 * t588 * t564 * t651 - 0.11874960000000000000000000000000000000000000000000e3 * t671 * t641 - 0.29687400000000000000000000000000000000000000000000e2 * t495 * t580 * t564 * t651 - 0.98958000000000000000000000000000000000000000000000e1 * t495 * t496 * t472 * t651
  t1238 = 0.83124720000000000000000000000000000000000000000000e3 * t633 * t613 + 0.83124720000000000000000000000000000000000000000000e3 * t625 * t613 - 0.17812440000000000000000000000000000000000000000000e3 * t661 * t641 + 0.65972000000000000000000000000000000000000000000000e1 * t495 * t538 * t541 * t500 * t651 - 0.98958000000000000000000000000000000000000000000000e1 * t495 * t528 * t531 * t500 * t651 - 0.11874960000000000000000000000000000000000000000000e3 * t655 * t641 - 0.36651111111111111111111111111111111111111111111111e1 * t495 * t25 * t716 * t500 * t651 + 0.23090200000000000000000000000000000000000000000000e2 * t671 * t630 - 0.76967333333333333333333333333333333333333333333333e2 * t633 * t622 - 0.76967333333333333333333333333333333333333333333333e2 * t625 * t622 + 0.69270600000000000000000000000000000000000000000000e2 * t675 * t630 + 0.34635300000000000000000000000000000000000000000000e2 * t661 * t630 - 0.76967333333333333333333333333333333333333333333334e1 * t646 * t630 - 0.25655777777777777777777777777777777777777777777777e2 * t637 * t622 + 0.83381277777777777777777777777777777777777777777776e2 * t606 * t617 * t477 * t55 * t486 + 0.23090200000000000000000000000000000000000000000000e2 * t655 * t630 + 0.27708240000000000000000000000000000000000000000000e3 * t637 * t613 - 0.14085022000000000000000000000000000000000000000000e4 * t606 * t611 * t920 * t486
  t1248 = t486 * t46 * t475
  t1285 = t574 * t39
  t1307 = -0.76967333333333333333333333333333333333333333333333e2 * t721 * t572 / t482 / t231 / t56 * t51 * t924 * t1248 - 0.64604306522260800000000000000000000000000000000000e3 * t606 * t55 * t609 * t486 * t476 * t477 - 0.98958000000000000000000000000000000000000000000000e1 * t495 * t701 * t27 * t500 * t651 - 0.29687400000000000000000000000000000000000000000000e2 * t495 * t664 * t549 * t651 - 0.17812440000000000000000000000000000000000000000000e3 * t666 * t641 + 0.65972000000000000000000000000000000000000000000000e1 * t495 * t644 * t549 * t651 - 0.3e1 / 0.2e1 * t539 * t566 + t529 * t543 / 0.2e1 - t26 * t531 * t472 * t487 / 0.2e1 + t26 * t541 * t564 * t487 / 0.2e1 + 0.10427396878333333333333333333333333333333333333333e3 * t573 * t1285 * t576 + 0.32642285880000000000000000000000000000000000000000e2 * t571 * t670 * t585 + 0.17758647124527456240000000000000000000000000000000e3 * t573 * t479 / s0 * t1248 - 0.97926857640000000000000000000000000000000000000000e2 * t582 * t577 - 0.97926857640000000000000000000000000000000000000000e2 * t594 * t577 + 0.48963428820000000000000000000000000000000000000000e2 * t571 * t665 * t585 + 0.97926857640000000000000000000000000000000000000000e2 * t571 * t674 * t585
  t1336 = t19 ** 2
  t1339 = t516 ** 2
  t1345 = t524 ** 2
  t1354 = -0.24e2 * t693 + 0.24e2 * t16 / t692 / t6
  t1355 = f.my_piecewise5(t10, 0, t14, 0, t1354)
  t1359 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t509 / t1336 * t1339 - 0.16e2 / 0.9e1 * t685 * t516 * t524 + 0.4e1 / 0.3e1 * t510 * t1345 + 0.16e2 / 0.9e1 * t689 * t697 + 0.4e1 / 0.3e1 * t23 * t1355)
  t1387 = 0.32642285880000000000000000000000000000000000000000e2 * t571 * t654 * t585 + 0.48963428820000000000000000000000000000000000000000e2 * t571 * t660 * t585 + 0.65284571760000000000000000000000000000000000000000e2 * t599 * t581 * t603 + 0.65284571760000000000000000000000000000000000000000e2 * t599 * t593 * t603 + 0.21761523920000000000000000000000000000000000000000e2 * t599 * t589 * t603 - 0.87046095680000000000000000000000000000000000000001e2 * t600 * t601 * t1285 * t486 - 0.10880761960000000000000000000000000000000000000000e2 * t571 * t645 * t585 - 0.32642285880000000000000000000000000000000000000000e2 * t590 * t577 + 0.34635300000000000000000000000000000000000000000000e2 * t666 * t630 - 0.35624880000000000000000000000000000000000000000000e3 * t675 * t641 - 0.3e1 / 0.8e1 * t5 * t1359 * t704 - 0.3e1 / 0.2e1 * t702 * t708 - 0.5e1 / 0.9e1 * t539 * t718 - 0.5e1 / 0.9e1 * t26 * t716 * t549 * t487 + 0.83124720000000000000000000000000000000000000000000e4 * t722 * t731 * t724 / t110 * t486 - 0.23749920000000000000000000000000000000000000000000e4 * t722 * t549 * t730 * t734 - 0.79166400000000000000000000000000000000000000000000e3 * t721 * t588 * t735 - 0.23749920000000000000000000000000000000000000000000e4 * t721 * t580 * t735
  t1390 = f.my_piecewise3(t1, 0, t1187 + t1238 + t1307 + t1387)
  t1391 = t744 ** 2
  t1394 = t752 ** 2
  t1400 = t759 ** 2
  t1406 = f.my_piecewise5(t14, 0, t10, 0, -t1354)
  t1410 = f.my_piecewise3(t745, 0, 0.40e2 / 0.81e2 / t747 / t1391 * t1394 - 0.16e2 / 0.9e1 * t749 * t752 * t759 + 0.4e1 / 0.3e1 * t756 * t1400 + 0.16e2 / 0.9e1 * t757 * t763 + 0.4e1 / 0.3e1 * t746 * t1406)
  t1425 = f.my_piecewise3(t742, 0, -0.3e1 / 0.8e1 * t5 * t1410 * t851 - t768 * t862 / 0.2e1 + t860 * t870 / 0.2e1 - 0.5e1 / 0.9e1 * t868 * t877 + 0.10e2 / 0.27e2 * t875 * t884 * t838 * t850)
  d1111 = 0.4e1 * t740 + 0.4e1 * t881 + t6 * (t1390 + t1425)

  res = {'v4rho4': d1111}
  return res
