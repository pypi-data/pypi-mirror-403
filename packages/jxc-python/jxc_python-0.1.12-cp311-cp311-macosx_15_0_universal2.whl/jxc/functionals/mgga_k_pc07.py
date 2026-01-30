"""Generated from mgga_k_pc07.mpl."""

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

  pc07_p = lambda x: X2S ** 2 * x ** 2
  pc07_q = lambda u: X2S ** 2 * u

  pc07_fab0 = lambda z: jnp.exp(-params_a * params_b / z) * (1 + jnp.exp(-params_a / (params_a - z))) ** params_b / (jnp.exp(-params_a / z) + jnp.exp(-params_a / (params_a - z))) ** params_b

  pc07_thr = 1 / 40

  pc07_f_W = lambda x: 5 * pc07_p(x) / 3

  pc07_Delta = lambda x, u: 8 * pc07_q(u) ** 2 / 81 - pc07_p(x) * pc07_q(u) / 9 + 8 * pc07_p(x) ** 2 / 243

  pc07_zlo = pc07_thr * params_a

  pc07_zhi = (1 - pc07_thr) * params_a

  pc07_GE4 = lambda x, u: 1 + 5 * pc07_p(x) / 27 + 20 * pc07_q(u) / 9 + pc07_Delta(x, u)

  pc07_fab = lambda z: f.my_piecewise5(z <= pc07_zlo, 0, z >= pc07_zhi, 1, pc07_fab0(jnp.minimum(pc07_zhi, jnp.maximum(pc07_zlo, z))))

  pc07_GE4_M = lambda x, u: pc07_GE4(x, u) / jnp.sqrt(1 + pc07_Delta(x, u) ** 2 / (1 + pc07_f_W(x)) ** 2)

  pc07_f = lambda x, u: pc07_f_W(x) + (pc07_GE4_M(x, u) - pc07_f_W(x)) * pc07_fab(pc07_GE4_M(x, u) - pc07_f_W(x))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, pc07_f, rs, z, xs0, xs1, u0, u1)

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

  pc07_p = lambda x: X2S ** 2 * x ** 2
  pc07_q = lambda u: X2S ** 2 * u

  pc07_fab0 = lambda z: jnp.exp(-params_a * params_b / z) * (1 + jnp.exp(-params_a / (params_a - z))) ** params_b / (jnp.exp(-params_a / z) + jnp.exp(-params_a / (params_a - z))) ** params_b

  pc07_thr = 1 / 40

  pc07_f_W = lambda x: 5 * pc07_p(x) / 3

  pc07_Delta = lambda x, u: 8 * pc07_q(u) ** 2 / 81 - pc07_p(x) * pc07_q(u) / 9 + 8 * pc07_p(x) ** 2 / 243

  pc07_zlo = pc07_thr * params_a

  pc07_zhi = (1 - pc07_thr) * params_a

  pc07_GE4 = lambda x, u: 1 + 5 * pc07_p(x) / 27 + 20 * pc07_q(u) / 9 + pc07_Delta(x, u)

  pc07_fab = lambda z: f.my_piecewise5(z <= pc07_zlo, 0, z >= pc07_zhi, 1, pc07_fab0(jnp.minimum(pc07_zhi, jnp.maximum(pc07_zlo, z))))

  pc07_GE4_M = lambda x, u: pc07_GE4(x, u) / jnp.sqrt(1 + pc07_Delta(x, u) ** 2 / (1 + pc07_f_W(x)) ** 2)

  pc07_f = lambda x, u: pc07_f_W(x) + (pc07_GE4_M(x, u) - pc07_f_W(x)) * pc07_fab(pc07_GE4_M(x, u) - pc07_f_W(x))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, pc07_f, rs, z, xs0, xs1, u0, u1)

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

  pc07_p = lambda x: X2S ** 2 * x ** 2
  pc07_q = lambda u: jnp.zeros_like(u)

  pc07_fab0 = lambda z: jnp.exp(-params_a * params_b / z) * (1 + jnp.exp(-params_a / (params_a - z))) ** params_b / (jnp.exp(-params_a / z) + jnp.exp(-params_a / (params_a - z))) ** params_b

  pc07_thr = 1 / 40

  pc07_f_W = lambda x: 5 * pc07_p(x) / 3

  pc07_Delta = lambda x, u: 8 * pc07_q(u) ** 2 / 81 - pc07_p(x) * pc07_q(u) / 9 + 8 * pc07_p(x) ** 2 / 243

  pc07_zlo = pc07_thr * params_a

  pc07_zhi = (1 - pc07_thr) * params_a

  pc07_GE4 = lambda x, u: 1 + 5 * pc07_p(x) / 27 + 20 * pc07_q(u) / 9 + pc07_Delta(x, u)

  pc07_fab = lambda z: f.my_piecewise5(z <= pc07_zlo, 0, z >= pc07_zhi, 1, pc07_fab0(jnp.minimum(pc07_zhi, jnp.maximum(pc07_zlo, z))))

  pc07_GE4_M = lambda x, u: pc07_GE4(x, u) / jnp.sqrt(1 + pc07_Delta(x, u) ** 2 / (1 + pc07_f_W(x)) ** 2)

  pc07_f = lambda x, u: pc07_f_W(x) + (pc07_GE4_M(x, u) - pc07_f_W(x)) * pc07_fab(pc07_GE4_M(x, u) - pc07_f_W(x))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, pc07_f, rs, z, xs0, xs1, u0, u1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t23 * f.p.zeta_threshold
  t25 = t20 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = f.my_piecewise3(t21, t24, t26 * t20)
  t29 = t7 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = t28 * t30
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
  t44 = t37 * s0 * t42
  t45 = 0.5e1 / 0.72e2 * t44
  t48 = 0.1e1 / t40 / r0
  t52 = t32 ** 2
  t55 = t52 / t34 / t33
  t56 = l0 ** 2
  t57 = t38 * r0
  t59 = 0.1e1 / t39 / t57
  t62 = t55 * t56 * t59 / 0.5832e4
  t63 = t38 ** 2
  t65 = 0.1e1 / t39 / t63
  t66 = s0 * t65
  t69 = t55 * t66 * l0 / 0.5184e4
  t70 = s0 ** 2
  t73 = 0.1e1 / t39 / t63 / r0
  t76 = t55 * t70 * t73 / 0.17496e5
  t77 = 0.1e1 + 0.5e1 / 0.648e3 * t44 + 0.5e1 / 0.54e2 * t37 * l0 * t48 + t62 - t69 + t76
  t78 = t62 - t69 + t76
  t79 = t78 ** 2
  t80 = 0.1e1 + t45
  t81 = t80 ** 2
  t82 = 0.1e1 / t81
  t84 = t79 * t82 + 0.1e1
  t85 = jnp.sqrt(t84)
  t86 = 0.1e1 / t85
  t88 = t77 * t86 - t45
  t89 = params.a / 0.40e2
  t90 = t88 <= t89
  t91 = 0.39e2 / 0.40e2 * params.a
  t92 = t91 <= t88
  t93 = params.a * params.b
  t94 = t88 < t89
  t95 = f.my_piecewise3(t94, t89, t88)
  t96 = t95 < t91
  t97 = f.my_piecewise3(t96, t95, t91)
  t98 = 0.1e1 / t97
  t100 = jnp.exp(-t93 * t98)
  t101 = params.a - t97
  t104 = jnp.exp(-params.a / t101)
  t105 = 0.1e1 + t104
  t106 = t105 ** params.b
  t107 = t100 * t106
  t109 = jnp.exp(-params.a * t98)
  t110 = t109 + t104
  t111 = t110 ** params.b
  t112 = 0.1e1 / t111
  t113 = t107 * t112
  t114 = f.my_piecewise5(t90, 0, t92, 1, t113)
  t116 = t88 * t114 + t45
  t120 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t116)
  t121 = r1 <= f.p.dens_threshold
  t122 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t123 = 0.1e1 + t122
  t124 = t123 <= f.p.zeta_threshold
  t125 = t123 ** (0.1e1 / 0.3e1)
  t126 = t125 ** 2
  t128 = f.my_piecewise3(t124, t24, t126 * t123)
  t129 = t128 * t30
  t130 = r1 ** 2
  t131 = r1 ** (0.1e1 / 0.3e1)
  t132 = t131 ** 2
  t134 = 0.1e1 / t132 / t130
  t136 = t37 * s2 * t134
  t137 = 0.5e1 / 0.72e2 * t136
  t140 = 0.1e1 / t132 / r1
  t144 = l1 ** 2
  t145 = t130 * r1
  t147 = 0.1e1 / t131 / t145
  t150 = t55 * t144 * t147 / 0.5832e4
  t151 = t130 ** 2
  t153 = 0.1e1 / t131 / t151
  t154 = s2 * t153
  t157 = t55 * t154 * l1 / 0.5184e4
  t158 = s2 ** 2
  t161 = 0.1e1 / t131 / t151 / r1
  t164 = t55 * t158 * t161 / 0.17496e5
  t165 = 0.1e1 + 0.5e1 / 0.648e3 * t136 + 0.5e1 / 0.54e2 * t37 * l1 * t140 + t150 - t157 + t164
  t166 = t150 - t157 + t164
  t167 = t166 ** 2
  t168 = 0.1e1 + t137
  t169 = t168 ** 2
  t170 = 0.1e1 / t169
  t172 = t167 * t170 + 0.1e1
  t173 = jnp.sqrt(t172)
  t174 = 0.1e1 / t173
  t176 = t165 * t174 - t137
  t177 = t176 <= t89
  t178 = t91 <= t176
  t179 = t176 < t89
  t180 = f.my_piecewise3(t179, t89, t176)
  t181 = t180 < t91
  t182 = f.my_piecewise3(t181, t180, t91)
  t183 = 0.1e1 / t182
  t185 = jnp.exp(-t93 * t183)
  t186 = params.a - t182
  t189 = jnp.exp(-params.a / t186)
  t190 = 0.1e1 + t189
  t191 = t190 ** params.b
  t192 = t185 * t191
  t194 = jnp.exp(-params.a * t183)
  t195 = t194 + t189
  t196 = t195 ** params.b
  t197 = 0.1e1 / t196
  t198 = t192 * t197
  t199 = f.my_piecewise5(t177, 0, t178, 1, t198)
  t201 = t176 * t199 + t137
  t205 = f.my_piecewise3(t121, 0, 0.3e1 / 0.20e2 * t6 * t129 * t201)
  t206 = t7 ** 2
  t208 = t17 / t206
  t209 = t8 - t208
  t210 = f.my_piecewise5(t11, 0, t15, 0, t209)
  t213 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t210)
  t218 = 0.1e1 / t29
  t222 = t6 * t28 * t218 * t116 / 0.10e2
  t224 = 0.1e1 / t40 / t57
  t226 = t37 * s0 * t224
  t227 = 0.5e1 / 0.27e2 * t226
  t234 = 0.5e1 / 0.8748e4 * t55 * t56 * t65
  t235 = s0 * t73
  t238 = 0.13e2 / 0.15552e5 * t55 * t235 * l0
  t244 = 0.2e1 / 0.6561e4 * t55 * t70 / t39 / t63 / t38
  t249 = t77 / t85 / t84
  t250 = t78 * t82
  t256 = t79 / t81 / t80
  t265 = (-0.5e1 / 0.243e3 * t226 - 0.25e2 / 0.162e3 * t37 * l0 * t42 - t234 + t238 - t244) * t86 - t249 * (0.2e1 * t250 * (-t234 + t238 - t244) + 0.10e2 / 0.27e2 * t256 * t32 * t36 * s0 * t224) / 0.2e1 + t227
  t267 = t97 ** 2
  t268 = 0.1e1 / t267
  t269 = t93 * t268
  t270 = f.my_piecewise3(t94, 0, t265)
  t271 = f.my_piecewise3(t96, t270, 0)
  t273 = t106 * t112
  t276 = t107 * t93
  t277 = t101 ** 2
  t278 = 0.1e1 / t277
  t282 = t104 / t105 * t112
  t285 = params.a * t268
  t288 = params.a * t278
  t293 = 0.1e1 / t110
  t297 = f.my_piecewise5(t90, 0, t92, 0, t269 * t271 * t100 * t273 - t276 * t278 * t271 * t282 - t113 * params.b * (-t288 * t271 * t104 + t285 * t271 * t109) * t293)
  t304 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t213 * t30 * t116 + t222 + 0.3e1 / 0.20e2 * t6 * t31 * (t265 * t114 + t88 * t297 - t227))
  t306 = f.my_piecewise5(t15, 0, t11, 0, -t209)
  t309 = f.my_piecewise3(t124, 0, 0.5e1 / 0.3e1 * t126 * t306)
  t317 = t6 * t128 * t218 * t201 / 0.10e2
  t319 = f.my_piecewise3(t121, 0, 0.3e1 / 0.20e2 * t6 * t309 * t30 * t201 + t317)
  vrho_0_ = t120 + t205 + t7 * (t304 + t319)
  t322 = -t8 - t208
  t323 = f.my_piecewise5(t11, 0, t15, 0, t322)
  t326 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t323)
  t332 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t326 * t30 * t116 + t222)
  t334 = f.my_piecewise5(t15, 0, t11, 0, -t322)
  t337 = f.my_piecewise3(t124, 0, 0.5e1 / 0.3e1 * t126 * t334)
  t343 = 0.1e1 / t132 / t145
  t345 = t37 * s2 * t343
  t346 = 0.5e1 / 0.27e2 * t345
  t353 = 0.5e1 / 0.8748e4 * t55 * t144 * t153
  t354 = s2 * t161
  t357 = 0.13e2 / 0.15552e5 * t55 * t354 * l1
  t363 = 0.2e1 / 0.6561e4 * t55 * t158 / t131 / t151 / t130
  t368 = t165 / t173 / t172
  t369 = t166 * t170
  t375 = t167 / t169 / t168
  t384 = (-0.5e1 / 0.243e3 * t345 - 0.25e2 / 0.162e3 * t37 * l1 * t134 - t353 + t357 - t363) * t174 - t368 * (0.2e1 * t369 * (-t353 + t357 - t363) + 0.10e2 / 0.27e2 * t375 * t32 * t36 * s2 * t343) / 0.2e1 + t346
  t386 = t182 ** 2
  t387 = 0.1e1 / t386
  t388 = t93 * t387
  t389 = f.my_piecewise3(t179, 0, t384)
  t390 = f.my_piecewise3(t181, t389, 0)
  t392 = t191 * t197
  t395 = t192 * t93
  t396 = t186 ** 2
  t397 = 0.1e1 / t396
  t401 = t189 / t190 * t197
  t404 = params.a * t387
  t407 = params.a * t397
  t412 = 0.1e1 / t195
  t416 = f.my_piecewise5(t177, 0, t178, 0, t388 * t390 * t185 * t392 - t395 * t397 * t390 * t401 - t198 * params.b * (-t407 * t390 * t189 + t404 * t390 * t194) * t412)
  t423 = f.my_piecewise3(t121, 0, 0.3e1 / 0.20e2 * t6 * t337 * t30 * t201 + t317 + 0.3e1 / 0.20e2 * t6 * t129 * (t176 * t416 + t384 * t199 - t346))
  vrho_1_ = t120 + t205 + t7 * (t332 + t423)
  t426 = t37 * t42
  t427 = 0.5e1 / 0.72e2 * t426
  t431 = t55 * t65 * l0 / 0.5184e4
  t433 = t55 * t235 / 0.8748e4
  t444 = (0.5e1 / 0.648e3 * t426 - t431 + t433) * t86 - t249 * (0.2e1 * t250 * (-t431 + t433) - 0.5e1 / 0.36e2 * t256 * t426) / 0.2e1 - t427
  t446 = f.my_piecewise3(t94, 0, t444)
  t447 = f.my_piecewise3(t96, t446, 0)
  t463 = f.my_piecewise5(t90, 0, t92, 0, t269 * t447 * t100 * t273 - t276 * t278 * t447 * t282 - t113 * params.b * (-t288 * t447 * t104 + t285 * t447 * t109) * t293)
  t469 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (t444 * t114 + t88 * t463 + t427))
  vsigma_0_ = t7 * t469
  vsigma_1_ = 0.0e0
  t470 = t37 * t134
  t471 = 0.5e1 / 0.72e2 * t470
  t475 = t55 * t153 * l1 / 0.5184e4
  t477 = t55 * t354 / 0.8748e4
  t488 = (0.5e1 / 0.648e3 * t470 - t475 + t477) * t174 - t368 * (0.2e1 * t369 * (-t475 + t477) - 0.5e1 / 0.36e2 * t375 * t470) / 0.2e1 - t471
  t490 = f.my_piecewise3(t179, 0, t488)
  t491 = f.my_piecewise3(t181, t490, 0)
  t507 = f.my_piecewise5(t177, 0, t178, 0, t388 * t491 * t185 * t392 - t395 * t397 * t491 * t401 - t198 * params.b * (-t407 * t491 * t189 + t404 * t491 * t194) * t412)
  t513 = f.my_piecewise3(t121, 0, 0.3e1 / 0.20e2 * t6 * t129 * (t176 * t507 + t488 * t199 + t471))
  vsigma_2_ = t7 * t513
  t518 = t55 * l0 * t59 / 0.2916e4
  t520 = t55 * t66 / 0.5184e4
  t526 = (0.5e1 / 0.54e2 * t37 * t48 + t518 - t520) * t86 - t249 * t250 * (t518 - t520)
  t528 = f.my_piecewise3(t94, 0, t526)
  t529 = f.my_piecewise3(t96, t528, 0)
  t545 = f.my_piecewise5(t90, 0, t92, 0, t269 * t529 * t100 * t273 - t276 * t278 * t529 * t282 - t113 * params.b * (-t288 * t529 * t104 + t285 * t529 * t109) * t293)
  t551 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (t526 * t114 + t88 * t545))
  vlapl_0_ = t7 * t551
  t556 = t55 * l1 * t147 / 0.2916e4
  t558 = t55 * t154 / 0.5184e4
  t564 = (0.5e1 / 0.54e2 * t37 * t140 + t556 - t558) * t174 - t368 * t369 * (t556 - t558)
  t566 = f.my_piecewise3(t179, 0, t564)
  t567 = f.my_piecewise3(t181, t566, 0)
  t583 = f.my_piecewise5(t177, 0, t178, 0, t388 * t567 * t185 * t392 - t395 * t397 * t567 * t401 - t198 * params.b * (-t407 * t567 * t189 + t404 * t567 * t194) * t412)
  t589 = f.my_piecewise3(t121, 0, 0.3e1 / 0.20e2 * t6 * t129 * (t176 * t583 + t564 * t199))
  vlapl_1_ = t7 * t589
  vtau_0_ = 0.0e0
  vtau_1_ = 0.0e0
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

  pc07_p = lambda x: X2S ** 2 * x ** 2
  pc07_q = lambda u: jnp.zeros_like(u)

  pc07_fab0 = lambda z: jnp.exp(-params_a * params_b / z) * (1 + jnp.exp(-params_a / (params_a - z))) ** params_b / (jnp.exp(-params_a / z) + jnp.exp(-params_a / (params_a - z))) ** params_b

  pc07_thr = 1 / 40

  pc07_f_W = lambda x: 5 * pc07_p(x) / 3

  pc07_Delta = lambda x, u: 8 * pc07_q(u) ** 2 / 81 - pc07_p(x) * pc07_q(u) / 9 + 8 * pc07_p(x) ** 2 / 243

  pc07_zlo = pc07_thr * params_a

  pc07_zhi = (1 - pc07_thr) * params_a

  pc07_GE4 = lambda x, u: 1 + 5 * pc07_p(x) / 27 + 20 * pc07_q(u) / 9 + pc07_Delta(x, u)

  pc07_fab = lambda z: f.my_piecewise5(z <= pc07_zlo, 0, z >= pc07_zhi, 1, pc07_fab0(jnp.minimum(pc07_zhi, jnp.maximum(pc07_zlo, z))))

  pc07_GE4_M = lambda x, u: pc07_GE4(x, u) / jnp.sqrt(1 + pc07_Delta(x, u) ** 2 / (1 + pc07_f_W(x)) ** 2)

  pc07_f = lambda x, u: pc07_f_W(x) + (pc07_GE4_M(x, u) - pc07_f_W(x)) * pc07_fab(pc07_GE4_M(x, u) - pc07_f_W(x))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, pc07_f, rs, z, xs0, xs1, u0, u1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = t20 * t22
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t22 / t33
  t37 = t29 * t32 * t35
  t38 = 0.5e1 / 0.72e2 * t37
  t40 = l0 * t31
  t42 = 0.1e1 / t22 / r0
  t46 = t24 ** 2
  t49 = t46 / t26 / t25
  t50 = l0 ** 2
  t51 = t50 * t30
  t52 = t33 * r0
  t54 = 0.1e1 / t21 / t52
  t57 = t49 * t51 * t54 / 0.2916e4
  t58 = t49 * s0
  t59 = t33 ** 2
  t61 = 0.1e1 / t21 / t59
  t63 = t30 * t61 * l0
  t65 = t58 * t63 / 0.2592e4
  t66 = s0 ** 2
  t67 = t66 * t30
  t70 = 0.1e1 / t21 / t59 / r0
  t73 = t49 * t67 * t70 / 0.8748e4
  t74 = 0.1e1 + 0.5e1 / 0.648e3 * t37 + 0.5e1 / 0.54e2 * t29 * t40 * t42 + t57 - t65 + t73
  t75 = t57 - t65 + t73
  t76 = t75 ** 2
  t77 = 0.1e1 + t38
  t78 = t77 ** 2
  t79 = 0.1e1 / t78
  t81 = t76 * t79 + 0.1e1
  t82 = jnp.sqrt(t81)
  t83 = 0.1e1 / t82
  t85 = t74 * t83 - t38
  t86 = params.a / 0.40e2
  t87 = t85 <= t86
  t88 = 0.39e2 / 0.40e2 * params.a
  t89 = t88 <= t85
  t90 = params.a * params.b
  t91 = t85 < t86
  t92 = f.my_piecewise3(t91, t86, t85)
  t93 = t92 < t88
  t94 = f.my_piecewise3(t93, t92, t88)
  t95 = 0.1e1 / t94
  t97 = jnp.exp(-t90 * t95)
  t98 = params.a - t94
  t101 = jnp.exp(-params.a / t98)
  t102 = 0.1e1 + t101
  t103 = t102 ** params.b
  t104 = t97 * t103
  t106 = jnp.exp(-params.a * t95)
  t107 = t106 + t101
  t108 = t107 ** params.b
  t109 = 0.1e1 / t108
  t110 = t104 * t109
  t111 = f.my_piecewise5(t87, 0, t89, 1, t110)
  t113 = t85 * t111 + t38
  t117 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t113)
  t124 = 0.1e1 / t22 / t52
  t126 = t29 * t32 * t124
  t127 = 0.5e1 / 0.27e2 * t126
  t134 = 0.5e1 / 0.4374e4 * t49 * t51 * t61
  t138 = 0.13e2 / 0.7776e4 * t58 * t30 * t70 * l0
  t144 = 0.4e1 / 0.6561e4 * t49 * t67 / t21 / t59 / t33
  t149 = t74 / t82 / t81
  t150 = t75 * t79
  t157 = t76 / t78 / t77 * t24
  t166 = (-0.5e1 / 0.243e3 * t126 - 0.25e2 / 0.162e3 * t29 * t40 * t35 - t134 + t138 - t144) * t83 - t149 * (0.2e1 * t150 * (-t134 + t138 - t144) + 0.10e2 / 0.27e2 * t157 * t28 * s0 * t31 * t124) / 0.2e1 + t127
  t168 = t94 ** 2
  t169 = 0.1e1 / t168
  t170 = t90 * t169
  t171 = f.my_piecewise3(t91, 0, t166)
  t172 = f.my_piecewise3(t93, t171, 0)
  t174 = t103 * t109
  t177 = t104 * t90
  t178 = t98 ** 2
  t179 = 0.1e1 / t178
  t183 = t101 / t102 * t109
  t186 = params.a * t169
  t189 = params.a * t179
  t194 = 0.1e1 / t107
  t198 = f.my_piecewise5(t87, 0, t89, 0, t170 * t172 * t97 * t174 - t177 * t179 * t172 * t183 - t110 * params.b * (-t189 * t172 * t101 + t186 * t172 * t106) * t194)
  t205 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t113 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (t166 * t111 + t85 * t198 - t127))
  vrho_0_ = 0.2e1 * r0 * t205 + 0.2e1 * t117
  t209 = t29 * t31 * t35
  t210 = 0.5e1 / 0.72e2 * t209
  t213 = t49 * t63 / 0.2592e4
  t214 = s0 * t30
  t217 = t49 * t214 * t70 / 0.4374e4
  t230 = (0.5e1 / 0.648e3 * t209 - t213 + t217) * t83 - t149 * (0.2e1 * t150 * (-t213 + t217) - 0.5e1 / 0.36e2 * t157 * t28 * t31 * t35) / 0.2e1 - t210
  t232 = f.my_piecewise3(t91, 0, t230)
  t233 = f.my_piecewise3(t93, t232, 0)
  t249 = f.my_piecewise5(t87, 0, t89, 0, t170 * t233 * t97 * t174 - t177 * t179 * t233 * t183 - t110 * params.b * (-t189 * t233 * t101 + t186 * t233 * t106) * t194)
  t255 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (t230 * t111 + t85 * t249 + t210))
  vsigma_0_ = 0.2e1 * r0 * t255
  t263 = t49 * l0 * t30 * t54 / 0.1458e4
  t266 = t49 * t214 * t61 / 0.2592e4
  t272 = (0.5e1 / 0.54e2 * t29 * t31 * t42 + t263 - t266) * t83 - t149 * t150 * (t263 - t266)
  t274 = f.my_piecewise3(t91, 0, t272)
  t275 = f.my_piecewise3(t93, t274, 0)
  t291 = f.my_piecewise5(t87, 0, t89, 0, t170 * t275 * t97 * t174 - t177 * t179 * t275 * t183 - t110 * params.b * (-t189 * t275 * t101 + t186 * t275 * t106) * t194)
  t297 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (t272 * t111 + t85 * t291))
  vlapl_0_ = 0.2e1 * r0 * t297
  vtau_0_ = 0.0e0
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
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t23 = t20 / t21
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t34 = t21 ** 2
  t36 = 0.1e1 / t34 / t33
  t38 = t29 * t32 * t36
  t39 = 0.5e1 / 0.72e2 * t38
  t41 = l0 * t31
  t47 = t24 ** 2
  t49 = 0.1e1 / t26 / t25
  t50 = t47 * t49
  t51 = l0 ** 2
  t52 = t51 * t30
  t53 = t33 * r0
  t58 = t50 * t52 / t21 / t53 / 0.2916e4
  t59 = t50 * s0
  t60 = t33 ** 2
  t62 = 0.1e1 / t21 / t60
  t66 = t59 * t30 * t62 * l0 / 0.2592e4
  t67 = s0 ** 2
  t68 = t67 * t30
  t71 = 0.1e1 / t21 / t60 / r0
  t74 = t50 * t68 * t71 / 0.8748e4
  t75 = 0.1e1 + 0.5e1 / 0.648e3 * t38 + 0.5e1 / 0.54e2 * t29 * t41 / t34 / r0 + t58 - t66 + t74
  t76 = t58 - t66 + t74
  t77 = t76 ** 2
  t78 = 0.1e1 + t39
  t79 = t78 ** 2
  t80 = 0.1e1 / t79
  t82 = t77 * t80 + 0.1e1
  t83 = jnp.sqrt(t82)
  t84 = 0.1e1 / t83
  t86 = t75 * t84 - t39
  t87 = params.a / 0.40e2
  t88 = t86 <= t87
  t89 = 0.39e2 / 0.40e2 * params.a
  t90 = t89 <= t86
  t91 = params.a * params.b
  t92 = t86 < t87
  t93 = f.my_piecewise3(t92, t87, t86)
  t94 = t93 < t89
  t95 = f.my_piecewise3(t94, t93, t89)
  t96 = 0.1e1 / t95
  t98 = jnp.exp(-t91 * t96)
  t99 = params.a - t95
  t102 = jnp.exp(-params.a / t99)
  t103 = 0.1e1 + t102
  t104 = t103 ** params.b
  t105 = t98 * t104
  t107 = jnp.exp(-params.a * t96)
  t108 = t107 + t102
  t109 = t108 ** params.b
  t110 = 0.1e1 / t109
  t111 = t105 * t110
  t112 = f.my_piecewise5(t88, 0, t90, 1, t111)
  t114 = t86 * t112 + t39
  t118 = t20 * t34
  t120 = 0.1e1 / t34 / t53
  t122 = t29 * t32 * t120
  t123 = 0.5e1 / 0.27e2 * t122
  t130 = 0.5e1 / 0.4374e4 * t50 * t52 * t62
  t134 = 0.13e2 / 0.7776e4 * t59 * t30 * t71 * l0
  t137 = 0.1e1 / t21 / t60 / t33
  t140 = 0.4e1 / 0.6561e4 * t50 * t68 * t137
  t141 = -0.5e1 / 0.243e3 * t122 - 0.25e2 / 0.162e3 * t29 * t41 * t36 - t130 + t134 - t140
  t144 = 0.1e1 / t83 / t82
  t145 = t75 * t144
  t146 = t76 * t80
  t147 = -t130 + t134 - t140
  t151 = 0.1e1 / t79 / t78
  t153 = t77 * t151 * t24
  t154 = t28 * s0
  t156 = t154 * t31 * t120
  t159 = 0.2e1 * t146 * t147 + 0.10e2 / 0.27e2 * t153 * t156
  t162 = t141 * t84 - t145 * t159 / 0.2e1 + t123
  t164 = t95 ** 2
  t165 = 0.1e1 / t164
  t166 = t91 * t165
  t167 = f.my_piecewise3(t92, 0, t162)
  t168 = f.my_piecewise3(t94, t167, 0)
  t170 = t104 * t110
  t173 = t105 * t91
  t174 = t99 ** 2
  t175 = 0.1e1 / t174
  t177 = 0.1e1 / t103
  t179 = t102 * t177 * t110
  t182 = params.a * t165
  t185 = params.a * t175
  t186 = t168 * t102
  t188 = t182 * t168 * t107 - t185 * t186
  t190 = 0.1e1 / t108
  t194 = f.my_piecewise5(t88, 0, t90, 0, -t111 * params.b * t188 * t190 + t166 * t168 * t98 * t170 - t173 * t175 * t168 * t179)
  t196 = t162 * t112 + t86 * t194 - t123
  t201 = f.my_piecewise3(t2, 0, t7 * t23 * t114 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t118 * t196)
  t213 = 0.1e1 / t34 / t60
  t215 = t29 * t32 * t213
  t216 = 0.55e2 / 0.81e2 * t215
  t223 = 0.65e2 / 0.13122e5 * t50 * t52 * t71
  t227 = 0.13e2 / 0.1458e4 * t59 * t30 * t137 * l0
  t230 = 0.1e1 / t21 / t60 / t53
  t233 = 0.76e2 / 0.19683e5 * t50 * t68 * t230
  t238 = t82 ** 2
  t242 = t159 ** 2
  t245 = t147 ** 2
  t256 = t79 ** 2
  t272 = (0.55e2 / 0.729e3 * t215 + 0.100e3 / 0.243e3 * t29 * t41 * t120 + t223 - t227 + t233) * t84 - t141 * t144 * t159 + 0.3e1 / 0.4e1 * t75 / t83 / t238 * t242 - t145 * (0.2e1 * t245 * t80 + 0.40e2 / 0.27e2 * t76 * t151 * t147 * t24 * t156 + 0.2e1 * t146 * (t223 - t227 + t233) + 0.100e3 / 0.243e3 * t77 / t256 * t47 * t49 * t67 * t30 * t230 - 0.110e3 / 0.81e2 * t153 * t154 * t31 * t213) / 0.2e1 - t216
  t277 = 0.1e1 / t164 / t95
  t279 = t168 ** 2
  t281 = t279 * t98 * t170
  t284 = f.my_piecewise3(t92, 0, t272)
  t285 = f.my_piecewise3(t94, t284, 0)
  t289 = params.a ** 2
  t290 = params.b ** 2
  t291 = t289 * t290
  t292 = t164 ** 2
  t293 = 0.1e1 / t292
  t303 = params.a * t290
  t307 = t110 * t188 * t190
  t312 = t174 ** 2
  t313 = 0.1e1 / t312
  t314 = t313 * t279
  t315 = t102 ** 2
  t316 = t103 ** 2
  t320 = t314 * t315 / t316 * t110
  t323 = 0.1e1 / t174 / t99
  t332 = t105 * params.b * t289
  t342 = t188 ** 2
  t344 = t108 ** 2
  t345 = 0.1e1 / t344
  t349 = t279 * t107
  t357 = t279 * t102
  t371 = -0.2e1 * t91 * t277 * t281 + t166 * t285 * t98 * t170 + t291 * t293 * t281 - 0.2e1 * t291 * t165 * t279 * t98 * t104 * t175 * t179 - 0.2e1 * t303 * t165 * t168 * t105 * t307 + t105 * t291 * t320 - 0.2e1 * t173 * t323 * t279 * t179 - t173 * t175 * t285 * t179 + t332 * t314 * t179 - t332 * t320 + 0.2e1 * t105 * t303 * t175 * t186 * t177 * t307 + t111 * t290 * t342 * t345 - t111 * params.b * (-t185 * t285 * t102 + t182 * t285 * t107 - 0.2e1 * params.a * t277 * t349 + t289 * t293 * t349 + t289 * t313 * t357 - 0.2e1 * params.a * t323 * t357) * t190 + t111 * params.b * t342 * t345
  t372 = f.my_piecewise5(t88, 0, t90, 0, t371)
  t379 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t114 / 0.30e2 + t7 * t23 * t196 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t118 * (t272 * t112 + 0.2e1 * t162 * t194 + t86 * t372 + t216))
  v2rho2_0_ = 0.2e1 * r0 * t379 + 0.4e1 * t201
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t24 = t20 / t21 / r0
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = t25 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t37 = 0.1e1 / t35 / t34
  t39 = t30 * t33 * t37
  t40 = 0.5e1 / 0.72e2 * t39
  t42 = l0 * t32
  t48 = t25 ** 2
  t50 = 0.1e1 / t27 / t26
  t51 = t48 * t50
  t52 = l0 ** 2
  t53 = t52 * t31
  t54 = t34 * r0
  t59 = t51 * t53 / t21 / t54 / 0.2916e4
  t60 = t51 * s0
  t61 = t34 ** 2
  t63 = 0.1e1 / t21 / t61
  t67 = t60 * t31 * t63 * l0 / 0.2592e4
  t68 = s0 ** 2
  t69 = t68 * t31
  t70 = t61 * r0
  t72 = 0.1e1 / t21 / t70
  t75 = t51 * t69 * t72 / 0.8748e4
  t76 = 0.1e1 + 0.5e1 / 0.648e3 * t39 + 0.5e1 / 0.54e2 * t30 * t42 / t35 / r0 + t59 - t67 + t75
  t77 = t59 - t67 + t75
  t78 = t77 ** 2
  t79 = 0.1e1 + t40
  t80 = t79 ** 2
  t81 = 0.1e1 / t80
  t83 = t78 * t81 + 0.1e1
  t84 = jnp.sqrt(t83)
  t85 = 0.1e1 / t84
  t87 = t76 * t85 - t40
  t88 = params.a / 0.40e2
  t89 = t87 <= t88
  t90 = 0.39e2 / 0.40e2 * params.a
  t91 = t90 <= t87
  t92 = params.a * params.b
  t93 = t87 < t88
  t94 = f.my_piecewise3(t93, t88, t87)
  t95 = t94 < t90
  t96 = f.my_piecewise3(t95, t94, t90)
  t97 = 0.1e1 / t96
  t99 = jnp.exp(-t92 * t97)
  t100 = params.a - t96
  t103 = jnp.exp(-params.a / t100)
  t104 = 0.1e1 + t103
  t105 = t104 ** params.b
  t106 = t99 * t105
  t108 = jnp.exp(-params.a * t97)
  t109 = t108 + t103
  t110 = t109 ** params.b
  t111 = 0.1e1 / t110
  t112 = t106 * t111
  t113 = f.my_piecewise5(t89, 0, t91, 1, t112)
  t115 = t87 * t113 + t40
  t120 = t20 / t21
  t122 = 0.1e1 / t35 / t54
  t124 = t30 * t33 * t122
  t125 = 0.5e1 / 0.27e2 * t124
  t132 = 0.5e1 / 0.4374e4 * t51 * t53 * t63
  t136 = 0.13e2 / 0.7776e4 * t60 * t31 * t72 * l0
  t139 = 0.1e1 / t21 / t61 / t34
  t142 = 0.4e1 / 0.6561e4 * t51 * t69 * t139
  t143 = -0.5e1 / 0.243e3 * t124 - 0.25e2 / 0.162e3 * t30 * t42 * t37 - t132 + t136 - t142
  t146 = 0.1e1 / t84 / t83
  t147 = t76 * t146
  t148 = t77 * t81
  t149 = -t132 + t136 - t142
  t153 = 0.1e1 / t80 / t79
  t155 = t78 * t153 * t25
  t156 = t29 * s0
  t158 = t156 * t32 * t122
  t161 = 0.2e1 * t148 * t149 + 0.10e2 / 0.27e2 * t155 * t158
  t164 = t143 * t85 - t147 * t161 / 0.2e1 + t125
  t166 = t96 ** 2
  t167 = 0.1e1 / t166
  t168 = t92 * t167
  t169 = f.my_piecewise3(t93, 0, t164)
  t170 = f.my_piecewise3(t95, t169, 0)
  t172 = t105 * t111
  t173 = t170 * t99 * t172
  t175 = t106 * t92
  t176 = t100 ** 2
  t177 = 0.1e1 / t176
  t179 = 0.1e1 / t104
  t181 = t103 * t179 * t111
  t184 = params.a * t167
  t185 = t170 * t108
  t187 = params.a * t177
  t188 = t170 * t103
  t190 = t184 * t185 - t187 * t188
  t192 = 0.1e1 / t109
  t196 = f.my_piecewise5(t89, 0, t91, 0, -t112 * params.b * t190 * t192 - t175 * t177 * t170 * t181 + t168 * t173)
  t198 = t164 * t113 + t87 * t196 - t125
  t202 = t20 * t35
  t204 = 0.1e1 / t35 / t61
  t206 = t30 * t33 * t204
  t207 = 0.55e2 / 0.81e2 * t206
  t214 = 0.65e2 / 0.13122e5 * t51 * t53 * t72
  t218 = 0.13e2 / 0.1458e4 * t60 * t31 * t139 * l0
  t221 = 0.1e1 / t21 / t61 / t54
  t224 = 0.76e2 / 0.19683e5 * t51 * t69 * t221
  t225 = 0.55e2 / 0.729e3 * t206 + 0.100e3 / 0.243e3 * t30 * t42 * t122 + t214 - t218 + t224
  t227 = t143 * t146
  t229 = t83 ** 2
  t231 = 0.1e1 / t84 / t229
  t232 = t76 * t231
  t233 = t161 ** 2
  t236 = t149 ** 2
  t239 = t77 * t153
  t241 = t239 * t149 * t25
  t244 = t214 - t218 + t224
  t247 = t80 ** 2
  t248 = 0.1e1 / t247
  t250 = t78 * t248 * t48
  t251 = t50 * t68
  t252 = t31 * t221
  t253 = t251 * t252
  t257 = t156 * t32 * t204
  t260 = 0.2e1 * t236 * t81 + 0.40e2 / 0.27e2 * t241 * t158 + 0.2e1 * t148 * t244 + 0.100e3 / 0.243e3 * t250 * t253 - 0.110e3 / 0.81e2 * t155 * t257
  t263 = t225 * t85 - t227 * t161 + 0.3e1 / 0.4e1 * t232 * t233 - t147 * t260 / 0.2e1 - t207
  t268 = 0.1e1 / t166 / t96
  t270 = t170 ** 2
  t271 = t270 * t99
  t272 = t271 * t172
  t275 = f.my_piecewise3(t93, 0, t263)
  t276 = f.my_piecewise3(t95, t275, 0)
  t278 = t276 * t99 * t172
  t280 = params.a ** 2
  t281 = params.b ** 2
  t282 = t280 * t281
  t283 = t166 ** 2
  t284 = 0.1e1 / t283
  t290 = t105 * t177
  t291 = t290 * t181
  t294 = params.a * t281
  t295 = t167 * t170
  t296 = t294 * t295
  t298 = t111 * t190 * t192
  t299 = t106 * t298
  t302 = t106 * t282
  t303 = t176 ** 2
  t304 = 0.1e1 / t303
  t305 = t304 * t270
  t306 = t103 ** 2
  t307 = t104 ** 2
  t308 = 0.1e1 / t307
  t310 = t306 * t308 * t111
  t311 = t305 * t310
  t314 = 0.1e1 / t176 / t100
  t322 = params.b * t280
  t323 = t106 * t322
  t328 = t106 * t294 * t177
  t329 = t188 * t179
  t333 = t190 ** 2
  t335 = t109 ** 2
  t336 = 0.1e1 / t335
  t339 = params.a * t268
  t340 = t270 * t108
  t345 = t280 * t284
  t347 = params.a * t314
  t348 = t270 * t103
  t351 = t276 * t103
  t353 = t280 * t304
  t355 = t184 * t276 * t108 - t187 * t351 - 0.2e1 * t339 * t340 + t345 * t340 - 0.2e1 * t347 * t348 + t353 * t348
  t356 = params.b * t355
  t362 = -0.2e1 * t92 * t268 * t272 + t168 * t278 + t282 * t284 * t272 - 0.2e1 * t282 * t167 * t270 * t99 * t291 - 0.2e1 * t296 * t299 + t302 * t311 - 0.2e1 * t175 * t314 * t270 * t181 - t175 * t177 * t276 * t181 + t323 * t305 * t181 - t323 * t311 + 0.2e1 * t328 * t329 * t298 + t112 * t281 * t333 * t336 - t112 * t356 * t192 + t112 * params.b * t333 * t336
  t363 = f.my_piecewise5(t89, 0, t91, 0, t362)
  t365 = t263 * t113 + 0.2e1 * t164 * t196 + t87 * t363 + t207
  t370 = f.my_piecewise3(t2, 0, -t7 * t24 * t115 / 0.30e2 + t7 * t120 * t198 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t202 * t365)
  t385 = 0.1e1 / t35 / t70
  t387 = t30 * t33 * t385
  t388 = 0.770e3 / 0.243e3 * t387
  t395 = 0.520e3 / 0.19683e5 * t51 * t53 * t139
  t398 = 0.247e3 / 0.4374e4 * t60 * t252 * l0
  t399 = t61 ** 2
  t401 = 0.1e1 / t21 / t399
  t404 = 0.1672e4 / 0.59049e5 * t51 * t69 * t401
  t449 = t26 ** 2
  t469 = (-0.770e3 / 0.2187e4 * t387 - 0.1100e4 / 0.729e3 * t30 * t42 * t204 - t395 + t398 - t404) * t85 - 0.3e1 / 0.2e1 * t225 * t146 * t161 + 0.9e1 / 0.4e1 * t143 * t231 * t233 - 0.3e1 / 0.2e1 * t227 * t260 - 0.15e2 / 0.8e1 * t76 / t84 / t229 / t83 * t233 * t161 + 0.9e1 / 0.4e1 * t232 * t161 * t260 - t147 * (0.6e1 * t149 * t81 * t244 + 0.20e2 / 0.9e1 * t236 * t153 * t25 * t158 + 0.200e3 / 0.81e2 * t77 * t248 * t149 * t48 * t253 + 0.20e2 / 0.9e1 * t239 * t244 * t25 * t158 - 0.220e3 / 0.27e2 * t241 * t257 + 0.2e1 * t148 * (-t395 + t398 - t404) + 0.8000e4 / 0.2187e4 * t78 / t247 / t79 / t449 * t68 * s0 / t399 / t54 - 0.1100e4 / 0.243e3 * t250 * t251 * t31 * t401 + 0.1540e4 / 0.243e3 * t155 * t156 * t32 * t385) / 0.2e1 + t388
  t476 = t270 * t170
  t477 = t476 * t108
  t480 = t185 * t276
  t484 = 0.1e1 / t283 / t96
  t488 = f.my_piecewise3(t93, 0, t469)
  t489 = f.my_piecewise3(t95, t488, 0)
  t494 = t280 * params.a
  t496 = 0.1e1 / t283 / t166
  t500 = t476 * t103
  t503 = t188 * t276
  t507 = 0.1e1 / t303 / t100
  t516 = 0.1e1 / t303 / t176
  t519 = -t187 * t489 * t103 + t184 * t489 * t108 - 0.6e1 * t280 * t484 * t477 + 0.6e1 * t280 * t507 * t500 + 0.6e1 * params.a * t284 * t477 - 0.6e1 * params.a * t304 * t500 + t494 * t496 * t477 - t494 * t516 * t500 - 0.6e1 * t339 * t480 + 0.3e1 * t345 * t480 - 0.6e1 * t347 * t503 + 0.3e1 * t353 * t503
  t523 = t333 * t190
  t526 = 0.1e1 / t335 / t109
  t534 = t281 * params.b
  t538 = t281 * t494
  t539 = t106 * t538
  t540 = t516 * t476
  t546 = t540 * t306 * t103 / t307 / t104 * t111
  t549 = params.a * t534
  t552 = t111 * t333 * t336
  t553 = t106 * t552
  t560 = t167 * t276
  t564 = t280 * t534
  t572 = t106 * params.b * t494
  t579 = -t112 * params.b * t519 * t192 - 0.3e1 * t112 * t281 * t523 * t526 - t112 * t534 * t523 * t526 - 0.2e1 * t112 * params.b * t523 * t526 - 0.6e1 * t175 * t304 * t476 * t181 + 0.6e1 * t294 * t268 * t270 * t299 - 0.3e1 * t564 * t284 * t270 * t299 - 0.3e1 * t294 * t560 * t299 + 0.3e1 * t549 * t295 * t553 + 0.3e1 * t296 * t553 + 0.3e1 * t539 * t546 - 0.2e1 * t572 * t546
  t580 = t507 * t476
  t584 = t580 * t310
  t592 = t540 * t310
  t596 = t111 * t355 * t192
  t600 = t534 * t494
  t613 = t167 * t476 * t99
  t615 = t105 * t304
  t616 = t615 * t310
  t624 = -0.6e1 * t282 * t613 * t105 * t314 * t181 - 0.3e1 * t600 * t284 * t476 * t99 * t291 - t175 * t177 * t489 * t181 - 0.3e1 * t296 * t106 * t596 - t106 * t600 * t546 + 0.6e1 * t323 * t580 * t181 - t572 * t540 * t181 + 0.3e1 * t600 * t613 * t616 + 0.6e1 * t302 * t584 - 0.6e1 * t323 * t584 - 0.3e1 * t539 * t592 + 0.3e1 * t572 * t592
  t626 = t538 * t613
  t633 = t106 * t282 * t304
  t637 = t170 * t306 * t308 * t111 * t276
  t644 = t188 * t179 * t111 * t276
  t648 = t106 * t322 * t304
  t668 = t476 * t99 * t172
  t676 = 0.6e1 * t282 * t268 * t476 * t99 * t291 - 0.6e1 * t106 * t92 * t314 * t644 + t168 * t489 * t99 * t172 - 0.6e1 * t92 * t268 * t170 * t278 + 0.3e1 * t282 * t284 * t276 * t173 + 0.3e1 * t626 * t615 * t181 + 0.6e1 * t92 * t284 * t668 + t600 * t496 * t668 - 0.3e1 * t626 * t616 + 0.3e1 * t633 * t637 - 0.3e1 * t648 * t637 + 0.3e1 * t648 * t644
  t702 = t348 * t179 * t298
  t707 = t270 * t306 * t308 * t298
  t710 = t329 * t552
  t734 = 0.3e1 * t112 * t281 * t190 * t336 * t355 + 0.3e1 * t112 * t356 * t336 * t190 - 0.6e1 * t282 * t484 * t668 + 0.6e1 * t564 * t167 * t271 * t105 * t177 * t103 * t179 * t298 + 0.3e1 * t328 * t351 * t179 * t298 - 0.3e1 * t633 * t702 + 0.3e1 * t633 * t707 - 0.3e1 * t328 * t710 - 0.3e1 * t106 * t564 * t304 * t707 + 0.6e1 * t106 * t294 * t314 * t702 - 0.3e1 * t106 * t549 * t177 * t710 - 0.6e1 * t282 * t560 * t99 * t290 * t170 * t181 + 0.3e1 * t328 * t329 * t596
  t737 = f.my_piecewise5(t89, 0, t91, 0, t579 + t624 + t676 + t734)
  t744 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t115 - t7 * t24 * t198 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t120 * t365 + 0.3e1 / 0.20e2 * t7 * t202 * (t469 * t113 + 0.3e1 * t164 * t363 + 0.3e1 * t263 * t196 + t87 * t737 - t388))
  v3rho3_0_ = 0.2e1 * r0 * t744 + 0.6e1 * t370

  res = {'v3rho3': v3rho3_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t26 = t17 * t25
  t27 = t8 - t26
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t31 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t28)
  t32 = t7 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = t31 * t33
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t40 = t35 * t39
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t47 = t40 * s0 * t45
  t48 = 0.5e1 / 0.72e2 * t47
  t55 = t35 ** 2
  t57 = 0.1e1 / t37 / t36
  t58 = t55 * t57
  t59 = l0 ** 2
  t60 = t41 * r0
  t65 = t58 * t59 / t42 / t60 / 0.5832e4
  t66 = t41 ** 2
  t68 = 0.1e1 / t42 / t66
  t72 = t58 * s0 * t68 * l0 / 0.5184e4
  t73 = s0 ** 2
  t76 = 0.1e1 / t42 / t66 / r0
  t79 = t58 * t73 * t76 / 0.17496e5
  t80 = 0.1e1 + 0.5e1 / 0.648e3 * t47 + 0.5e1 / 0.54e2 * t40 * l0 / t43 / r0 + t65 - t72 + t79
  t81 = t65 - t72 + t79
  t82 = t81 ** 2
  t83 = 0.1e1 + t48
  t84 = t83 ** 2
  t85 = 0.1e1 / t84
  t87 = t82 * t85 + 0.1e1
  t88 = jnp.sqrt(t87)
  t89 = 0.1e1 / t88
  t91 = t80 * t89 - t48
  t92 = params.a / 0.40e2
  t93 = t91 <= t92
  t94 = 0.39e2 / 0.40e2 * params.a
  t95 = t94 <= t91
  t96 = params.a * params.b
  t97 = t91 < t92
  t98 = f.my_piecewise3(t97, t92, t91)
  t99 = t98 < t94
  t100 = f.my_piecewise3(t99, t98, t94)
  t101 = 0.1e1 / t100
  t103 = jnp.exp(-t96 * t101)
  t104 = params.a - t100
  t107 = jnp.exp(-params.a / t104)
  t108 = 0.1e1 + t107
  t109 = t108 ** params.b
  t110 = t103 * t109
  t112 = jnp.exp(-params.a * t101)
  t113 = t112 + t107
  t114 = t113 ** params.b
  t115 = 0.1e1 / t114
  t116 = t110 * t115
  t117 = f.my_piecewise5(t93, 0, t95, 1, t116)
  t119 = t91 * t117 + t48
  t123 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t124 = t123 ** 2
  t125 = t124 * f.p.zeta_threshold
  t127 = f.my_piecewise3(t21, t125, t23 * t20)
  t128 = 0.1e1 / t32
  t129 = t127 * t128
  t132 = t6 * t129 * t119 / 0.10e2
  t133 = t127 * t33
  t135 = 0.1e1 / t43 / t60
  t137 = t40 * s0 * t135
  t138 = 0.5e1 / 0.27e2 * t137
  t145 = 0.5e1 / 0.8748e4 * t58 * t59 * t68
  t149 = 0.13e2 / 0.15552e5 * t58 * s0 * t76 * l0
  t152 = 0.1e1 / t42 / t66 / t41
  t155 = 0.2e1 / 0.6561e4 * t58 * t73 * t152
  t156 = -0.5e1 / 0.243e3 * t137 - 0.25e2 / 0.162e3 * t40 * l0 * t45 - t145 + t149 - t155
  t159 = 0.1e1 / t88 / t87
  t160 = t80 * t159
  t161 = t81 * t85
  t162 = -t145 + t149 - t155
  t166 = 0.1e1 / t84 / t83
  t168 = t82 * t166 * t35
  t169 = t39 * s0
  t173 = 0.2e1 * t161 * t162 + 0.10e2 / 0.27e2 * t168 * t169 * t135
  t176 = t156 * t89 - t160 * t173 / 0.2e1 + t138
  t178 = t100 ** 2
  t179 = 0.1e1 / t178
  t180 = t96 * t179
  t181 = f.my_piecewise3(t97, 0, t176)
  t182 = f.my_piecewise3(t99, t181, 0)
  t184 = t109 * t115
  t187 = t110 * t96
  t188 = t104 ** 2
  t189 = 0.1e1 / t188
  t191 = 0.1e1 / t108
  t193 = t107 * t191 * t115
  t196 = params.a * t179
  t199 = params.a * t189
  t200 = t182 * t107
  t202 = t196 * t182 * t112 - t199 * t200
  t204 = 0.1e1 / t113
  t208 = f.my_piecewise5(t93, 0, t95, 0, t180 * t182 * t103 * t184 - t116 * params.b * t202 * t204 - t187 * t189 * t182 * t193)
  t210 = t176 * t117 + t91 * t208 - t138
  t215 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t119 + t132 + 0.3e1 / 0.20e2 * t6 * t133 * t210)
  t217 = r1 <= f.p.dens_threshold
  t218 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t219 = 0.1e1 + t218
  t220 = t219 <= f.p.zeta_threshold
  t221 = t219 ** (0.1e1 / 0.3e1)
  t222 = t221 ** 2
  t224 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t227 = f.my_piecewise3(t220, 0, 0.5e1 / 0.3e1 * t222 * t224)
  t228 = t227 * t33
  t229 = r1 ** 2
  t230 = r1 ** (0.1e1 / 0.3e1)
  t231 = t230 ** 2
  t233 = 0.1e1 / t231 / t229
  t235 = t40 * s2 * t233
  t236 = 0.5e1 / 0.72e2 * t235
  t243 = l1 ** 2
  t244 = t229 * r1
  t249 = t58 * t243 / t230 / t244 / 0.5832e4
  t250 = t229 ** 2
  t252 = 0.1e1 / t230 / t250
  t256 = t58 * s2 * t252 * l1 / 0.5184e4
  t257 = s2 ** 2
  t260 = 0.1e1 / t230 / t250 / r1
  t263 = t58 * t257 * t260 / 0.17496e5
  t264 = 0.1e1 + 0.5e1 / 0.648e3 * t235 + 0.5e1 / 0.54e2 * t40 * l1 / t231 / r1 + t249 - t256 + t263
  t265 = t249 - t256 + t263
  t266 = t265 ** 2
  t267 = 0.1e1 + t236
  t268 = t267 ** 2
  t269 = 0.1e1 / t268
  t271 = t266 * t269 + 0.1e1
  t272 = jnp.sqrt(t271)
  t273 = 0.1e1 / t272
  t275 = t264 * t273 - t236
  t276 = t275 <= t92
  t277 = t94 <= t275
  t278 = t275 < t92
  t279 = f.my_piecewise3(t278, t92, t275)
  t280 = t279 < t94
  t281 = f.my_piecewise3(t280, t279, t94)
  t282 = 0.1e1 / t281
  t284 = jnp.exp(-t96 * t282)
  t285 = params.a - t281
  t288 = jnp.exp(-params.a / t285)
  t289 = 0.1e1 + t288
  t290 = t289 ** params.b
  t291 = t284 * t290
  t293 = jnp.exp(-params.a * t282)
  t294 = t293 + t288
  t295 = t294 ** params.b
  t296 = 0.1e1 / t295
  t297 = t291 * t296
  t298 = f.my_piecewise5(t276, 0, t277, 1, t297)
  t300 = t275 * t298 + t236
  t305 = f.my_piecewise3(t220, t125, t222 * t219)
  t306 = t305 * t128
  t309 = t6 * t306 * t300 / 0.10e2
  t311 = f.my_piecewise3(t217, 0, 0.3e1 / 0.20e2 * t6 * t228 * t300 + t309)
  t313 = 0.1e1 / t22
  t314 = t28 ** 2
  t319 = t17 / t24 / t7
  t321 = -0.2e1 * t25 + 0.2e1 * t319
  t322 = f.my_piecewise5(t11, 0, t15, 0, t321)
  t326 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t313 * t314 + 0.5e1 / 0.3e1 * t23 * t322)
  t333 = t6 * t31 * t128 * t119
  t339 = 0.1e1 / t32 / t7
  t343 = t6 * t127 * t339 * t119 / 0.30e2
  t345 = t6 * t129 * t210
  t348 = 0.1e1 / t43 / t66
  t350 = t40 * s0 * t348
  t351 = 0.55e2 / 0.81e2 * t350
  t358 = 0.65e2 / 0.26244e5 * t58 * t59 * t76
  t362 = 0.13e2 / 0.2916e4 * t58 * s0 * t152 * l0
  t365 = 0.1e1 / t42 / t66 / t60
  t368 = 0.38e2 / 0.19683e5 * t58 * t73 * t365
  t373 = t87 ** 2
  t377 = t173 ** 2
  t380 = t162 ** 2
  t390 = t84 ** 2
  t404 = (0.55e2 / 0.729e3 * t350 + 0.100e3 / 0.243e3 * t40 * l0 * t135 + t358 - t362 + t368) * t89 - t156 * t159 * t173 + 0.3e1 / 0.4e1 * t80 / t88 / t373 * t377 - t160 * (0.2e1 * t380 * t85 + 0.40e2 / 0.27e2 * t81 * t166 * t162 * t137 + 0.2e1 * t161 * (t358 - t362 + t368) + 0.50e2 / 0.243e3 * t82 / t390 * t55 * t57 * t73 * t365 - 0.110e3 / 0.81e2 * t168 * t169 * t348) / 0.2e1 - t351
  t409 = 0.1e1 / t178 / t100
  t411 = t182 ** 2
  t413 = t411 * t103 * t184
  t416 = f.my_piecewise3(t97, 0, t404)
  t417 = f.my_piecewise3(t99, t416, 0)
  t421 = params.a ** 2
  t422 = params.b ** 2
  t423 = t421 * t422
  t424 = t178 ** 2
  t425 = 0.1e1 / t424
  t435 = params.a * t422
  t439 = t115 * t202 * t204
  t444 = t188 ** 2
  t445 = 0.1e1 / t444
  t446 = t445 * t411
  t447 = t107 ** 2
  t448 = t108 ** 2
  t452 = t446 * t447 / t448 * t115
  t455 = 0.1e1 / t188 / t104
  t463 = params.b * t421
  t464 = t110 * t463
  t474 = t202 ** 2
  t476 = t113 ** 2
  t477 = 0.1e1 / t476
  t481 = t411 * t112
  t489 = t411 * t107
  t503 = -0.2e1 * t96 * t409 * t413 + t180 * t417 * t103 * t184 + t423 * t425 * t413 - 0.2e1 * t423 * t179 * t411 * t103 * t109 * t189 * t193 - 0.2e1 * t435 * t179 * t182 * t110 * t439 + t110 * t423 * t452 - 0.2e1 * t187 * t455 * t411 * t193 - t187 * t189 * t417 * t193 + t464 * t446 * t193 - t464 * t452 + 0.2e1 * t110 * t435 * t189 * t200 * t191 * t439 + t116 * t422 * t474 * t477 - t116 * params.b * (-t199 * t417 * t107 + t196 * t417 * t112 - 0.2e1 * params.a * t409 * t481 + t421 * t425 * t481 + t421 * t445 * t489 - 0.2e1 * params.a * t455 * t489) * t204 + t116 * params.b * t474 * t477
  t504 = f.my_piecewise5(t93, 0, t95, 0, t503)
  t511 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t326 * t33 * t119 + t333 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t210 - t343 + t345 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t133 * (t404 * t117 + 0.2e1 * t176 * t208 + t91 * t504 + t351))
  t512 = 0.1e1 / t221
  t513 = t224 ** 2
  t517 = f.my_piecewise5(t15, 0, t11, 0, -t321)
  t521 = f.my_piecewise3(t220, 0, 0.10e2 / 0.9e1 * t512 * t513 + 0.5e1 / 0.3e1 * t222 * t517)
  t528 = t6 * t227 * t128 * t300
  t533 = t6 * t305 * t339 * t300 / 0.30e2
  t535 = f.my_piecewise3(t217, 0, 0.3e1 / 0.20e2 * t6 * t521 * t33 * t300 + t528 / 0.5e1 - t533)
  d11 = 0.2e1 * t215 + 0.2e1 * t311 + t7 * (t511 + t535)
  t538 = -t8 - t26
  t539 = f.my_piecewise5(t11, 0, t15, 0, t538)
  t542 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t539)
  t543 = t542 * t33
  t548 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t543 * t119 + t132)
  t550 = f.my_piecewise5(t15, 0, t11, 0, -t538)
  t553 = f.my_piecewise3(t220, 0, 0.5e1 / 0.3e1 * t222 * t550)
  t554 = t553 * t33
  t558 = t305 * t33
  t560 = 0.1e1 / t231 / t244
  t562 = t40 * s2 * t560
  t563 = 0.5e1 / 0.27e2 * t562
  t570 = 0.5e1 / 0.8748e4 * t58 * t243 * t252
  t574 = 0.13e2 / 0.15552e5 * t58 * s2 * t260 * l1
  t577 = 0.1e1 / t230 / t250 / t229
  t580 = 0.2e1 / 0.6561e4 * t58 * t257 * t577
  t581 = -0.5e1 / 0.243e3 * t562 - 0.25e2 / 0.162e3 * t40 * l1 * t233 - t570 + t574 - t580
  t584 = 0.1e1 / t272 / t271
  t585 = t264 * t584
  t586 = t265 * t269
  t587 = -t570 + t574 - t580
  t591 = 0.1e1 / t268 / t267
  t593 = t266 * t591 * t35
  t594 = t39 * s2
  t598 = 0.2e1 * t586 * t587 + 0.10e2 / 0.27e2 * t593 * t594 * t560
  t601 = t581 * t273 - t585 * t598 / 0.2e1 + t563
  t603 = t281 ** 2
  t604 = 0.1e1 / t603
  t605 = t96 * t604
  t606 = f.my_piecewise3(t278, 0, t601)
  t607 = f.my_piecewise3(t280, t606, 0)
  t609 = t290 * t296
  t612 = t291 * t96
  t613 = t285 ** 2
  t614 = 0.1e1 / t613
  t616 = 0.1e1 / t289
  t618 = t288 * t616 * t296
  t621 = params.a * t604
  t624 = params.a * t614
  t625 = t607 * t288
  t627 = t621 * t607 * t293 - t624 * t625
  t629 = 0.1e1 / t294
  t633 = f.my_piecewise5(t276, 0, t277, 0, t605 * t607 * t284 * t609 - t297 * params.b * t627 * t629 - t612 * t614 * t607 * t618)
  t635 = t275 * t633 + t601 * t298 - t563
  t640 = f.my_piecewise3(t217, 0, 0.3e1 / 0.20e2 * t6 * t554 * t300 + t309 + 0.3e1 / 0.20e2 * t6 * t558 * t635)
  t644 = 0.2e1 * t319
  t645 = f.my_piecewise5(t11, 0, t15, 0, t644)
  t649 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t313 * t539 * t28 + 0.5e1 / 0.3e1 * t23 * t645)
  t656 = t6 * t542 * t128 * t119
  t664 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t649 * t33 * t119 + t656 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t543 * t210 + t333 / 0.10e2 - t343 + t345 / 0.10e2)
  t668 = f.my_piecewise5(t15, 0, t11, 0, -t644)
  t672 = f.my_piecewise3(t220, 0, 0.10e2 / 0.9e1 * t512 * t550 * t224 + 0.5e1 / 0.3e1 * t222 * t668)
  t679 = t6 * t553 * t128 * t300
  t686 = t6 * t306 * t635
  t689 = f.my_piecewise3(t217, 0, 0.3e1 / 0.20e2 * t6 * t672 * t33 * t300 + t679 / 0.10e2 + t528 / 0.10e2 - t533 + 0.3e1 / 0.20e2 * t6 * t228 * t635 + t686 / 0.10e2)
  d12 = t215 + t311 + t548 + t640 + t7 * (t664 + t689)
  t694 = t539 ** 2
  t698 = 0.2e1 * t25 + 0.2e1 * t319
  t699 = f.my_piecewise5(t11, 0, t15, 0, t698)
  t703 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t313 * t694 + 0.5e1 / 0.3e1 * t23 * t699)
  t710 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t703 * t33 * t119 + t656 / 0.5e1 - t343)
  t711 = t550 ** 2
  t715 = f.my_piecewise5(t15, 0, t11, 0, -t698)
  t719 = f.my_piecewise3(t220, 0, 0.10e2 / 0.9e1 * t512 * t711 + 0.5e1 / 0.3e1 * t222 * t715)
  t730 = 0.1e1 / t231 / t250
  t732 = t40 * s2 * t730
  t733 = 0.55e2 / 0.81e2 * t732
  t740 = 0.65e2 / 0.26244e5 * t58 * t243 * t260
  t744 = 0.13e2 / 0.2916e4 * t58 * s2 * t577 * l1
  t747 = 0.1e1 / t230 / t250 / t244
  t750 = 0.38e2 / 0.19683e5 * t58 * t257 * t747
  t755 = t271 ** 2
  t759 = t598 ** 2
  t762 = t587 ** 2
  t772 = t268 ** 2
  t786 = (0.55e2 / 0.729e3 * t732 + 0.100e3 / 0.243e3 * t40 * l1 * t560 + t740 - t744 + t750) * t273 - t581 * t584 * t598 + 0.3e1 / 0.4e1 * t264 / t272 / t755 * t759 - t585 * (0.2e1 * t762 * t269 + 0.40e2 / 0.27e2 * t265 * t591 * t587 * t562 + 0.2e1 * t586 * (t740 - t744 + t750) + 0.50e2 / 0.243e3 * t266 / t772 * t55 * t57 * t257 * t747 - 0.110e3 / 0.81e2 * t593 * t594 * t730) / 0.2e1 - t733
  t791 = 0.1e1 / t603 / t281
  t793 = t607 ** 2
  t795 = t793 * t284 * t609
  t798 = f.my_piecewise3(t278, 0, t786)
  t799 = f.my_piecewise3(t280, t798, 0)
  t803 = t603 ** 2
  t804 = 0.1e1 / t803
  t817 = t296 * t627 * t629
  t822 = t613 ** 2
  t823 = 0.1e1 / t822
  t824 = t823 * t793
  t825 = t288 ** 2
  t826 = t289 ** 2
  t830 = t824 * t825 / t826 * t296
  t833 = 0.1e1 / t613 / t285
  t841 = t291 * t463
  t851 = t627 ** 2
  t853 = t294 ** 2
  t854 = 0.1e1 / t853
  t858 = t793 * t293
  t866 = t793 * t288
  t880 = -0.2e1 * t96 * t791 * t795 + t605 * t799 * t284 * t609 + t423 * t804 * t795 - 0.2e1 * t423 * t604 * t793 * t284 * t290 * t614 * t618 - 0.2e1 * t435 * t604 * t607 * t291 * t817 + t291 * t423 * t830 - 0.2e1 * t612 * t833 * t793 * t618 - t612 * t614 * t799 * t618 + t841 * t824 * t618 - t841 * t830 + 0.2e1 * t291 * t435 * t614 * t625 * t616 * t817 + t297 * t422 * t851 * t854 - t297 * params.b * (-t624 * t799 * t288 + t621 * t799 * t293 + t421 * t804 * t858 + t421 * t823 * t866 - 0.2e1 * params.a * t791 * t858 - 0.2e1 * params.a * t833 * t866) * t629 + t297 * params.b * t851 * t854
  t881 = f.my_piecewise5(t276, 0, t277, 0, t880)
  t888 = f.my_piecewise3(t217, 0, 0.3e1 / 0.20e2 * t6 * t719 * t33 * t300 + t679 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t554 * t635 - t533 + t686 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t558 * (t275 * t881 + t786 * t298 + 0.2e1 * t601 * t633 + t733))
  d22 = 0.2e1 * t548 + 0.2e1 * t640 + t7 * (t710 + t888)
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
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = 0.1e1 / t22
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t27 = -t17 * t25 + t8
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t29 = t28 ** 2
  t32 = t22 ** 2
  t34 = 0.1e1 / t24 / t7
  t37 = 0.2e1 * t17 * t34 - 0.2e1 * t25
  t38 = f.my_piecewise5(t11, 0, t15, 0, t37)
  t42 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t23 * t29 + 0.5e1 / 0.3e1 * t32 * t38)
  t43 = t7 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = t42 * t44
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t51 = t46 * t50
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / t52
  t58 = t51 * s0 * t56
  t59 = 0.5e1 / 0.72e2 * t58
  t66 = t46 ** 2
  t68 = 0.1e1 / t48 / t47
  t69 = t66 * t68
  t70 = l0 ** 2
  t71 = t52 * r0
  t76 = t69 * t70 / t53 / t71 / 0.5832e4
  t77 = t52 ** 2
  t79 = 0.1e1 / t53 / t77
  t83 = t69 * s0 * t79 * l0 / 0.5184e4
  t84 = s0 ** 2
  t85 = t77 * r0
  t87 = 0.1e1 / t53 / t85
  t90 = t69 * t84 * t87 / 0.17496e5
  t91 = 0.1e1 + 0.5e1 / 0.648e3 * t58 + 0.5e1 / 0.54e2 * t51 * l0 / t54 / r0 + t76 - t83 + t90
  t92 = t76 - t83 + t90
  t93 = t92 ** 2
  t94 = 0.1e1 + t59
  t95 = t94 ** 2
  t96 = 0.1e1 / t95
  t98 = t93 * t96 + 0.1e1
  t99 = jnp.sqrt(t98)
  t100 = 0.1e1 / t99
  t102 = t91 * t100 - t59
  t103 = params.a / 0.40e2
  t104 = t102 <= t103
  t105 = 0.39e2 / 0.40e2 * params.a
  t106 = t105 <= t102
  t107 = params.a * params.b
  t108 = t102 < t103
  t109 = f.my_piecewise3(t108, t103, t102)
  t110 = t109 < t105
  t111 = f.my_piecewise3(t110, t109, t105)
  t112 = 0.1e1 / t111
  t114 = jnp.exp(-t107 * t112)
  t115 = params.a - t111
  t118 = jnp.exp(-params.a / t115)
  t119 = 0.1e1 + t118
  t120 = t119 ** params.b
  t121 = t114 * t120
  t123 = jnp.exp(-params.a * t112)
  t124 = t123 + t118
  t125 = t124 ** params.b
  t126 = 0.1e1 / t125
  t127 = t121 * t126
  t128 = f.my_piecewise5(t104, 0, t106, 1, t127)
  t130 = t102 * t128 + t59
  t136 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t137 = 0.1e1 / t43
  t138 = t136 * t137
  t142 = t136 * t44
  t144 = 0.1e1 / t54 / t71
  t146 = t51 * s0 * t144
  t147 = 0.5e1 / 0.27e2 * t146
  t154 = 0.5e1 / 0.8748e4 * t69 * t70 * t79
  t158 = 0.13e2 / 0.15552e5 * t69 * s0 * t87 * l0
  t161 = 0.1e1 / t53 / t77 / t52
  t164 = 0.2e1 / 0.6561e4 * t69 * t84 * t161
  t165 = -0.5e1 / 0.243e3 * t146 - 0.25e2 / 0.162e3 * t51 * l0 * t56 - t154 + t158 - t164
  t168 = 0.1e1 / t99 / t98
  t169 = t91 * t168
  t170 = t92 * t96
  t171 = -t154 + t158 - t164
  t175 = 0.1e1 / t95 / t94
  t177 = t93 * t175 * t46
  t178 = t50 * s0
  t179 = t178 * t144
  t182 = 0.2e1 * t170 * t171 + 0.10e2 / 0.27e2 * t177 * t179
  t185 = t165 * t100 - t169 * t182 / 0.2e1 + t147
  t187 = t111 ** 2
  t188 = 0.1e1 / t187
  t189 = t107 * t188
  t190 = f.my_piecewise3(t108, 0, t185)
  t191 = f.my_piecewise3(t110, t190, 0)
  t193 = t120 * t126
  t194 = t191 * t114 * t193
  t196 = t121 * t107
  t197 = t115 ** 2
  t198 = 0.1e1 / t197
  t200 = 0.1e1 / t119
  t202 = t118 * t200 * t126
  t205 = params.a * t188
  t206 = t191 * t123
  t208 = params.a * t198
  t209 = t191 * t118
  t211 = t205 * t206 - t208 * t209
  t213 = 0.1e1 / t124
  t217 = f.my_piecewise5(t104, 0, t106, 0, -t127 * params.b * t211 * t213 - t196 * t198 * t191 * t202 + t189 * t194)
  t219 = t102 * t217 + t185 * t128 - t147
  t223 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t224 = t223 ** 2
  t225 = t224 * f.p.zeta_threshold
  t227 = f.my_piecewise3(t21, t225, t32 * t20)
  t229 = 0.1e1 / t43 / t7
  t230 = t227 * t229
  t234 = t227 * t137
  t238 = t227 * t44
  t240 = 0.1e1 / t54 / t77
  t242 = t51 * s0 * t240
  t243 = 0.55e2 / 0.81e2 * t242
  t250 = 0.65e2 / 0.26244e5 * t69 * t70 * t87
  t254 = 0.13e2 / 0.2916e4 * t69 * s0 * t161 * l0
  t257 = 0.1e1 / t53 / t77 / t71
  t259 = t69 * t84 * t257
  t260 = 0.38e2 / 0.19683e5 * t259
  t261 = 0.55e2 / 0.729e3 * t242 + 0.100e3 / 0.243e3 * t51 * l0 * t144 + t250 - t254 + t260
  t263 = t165 * t168
  t265 = t98 ** 2
  t267 = 0.1e1 / t99 / t265
  t268 = t91 * t267
  t269 = t182 ** 2
  t272 = t171 ** 2
  t275 = t92 * t175
  t276 = t275 * t171
  t279 = t250 - t254 + t260
  t282 = t95 ** 2
  t283 = 0.1e1 / t282
  t285 = t93 * t283 * t66
  t286 = t68 * t84
  t293 = 0.2e1 * t272 * t96 + 0.40e2 / 0.27e2 * t276 * t146 + 0.2e1 * t170 * t279 + 0.50e2 / 0.243e3 * t285 * t286 * t257 - 0.110e3 / 0.81e2 * t177 * t178 * t240
  t296 = t261 * t100 - t263 * t182 + 0.3e1 / 0.4e1 * t268 * t269 - t169 * t293 / 0.2e1 - t243
  t301 = 0.1e1 / t187 / t111
  t303 = t191 ** 2
  t304 = t303 * t114
  t305 = t304 * t193
  t308 = f.my_piecewise3(t108, 0, t296)
  t309 = f.my_piecewise3(t110, t308, 0)
  t311 = t309 * t114 * t193
  t313 = params.a ** 2
  t314 = params.b ** 2
  t315 = t313 * t314
  t316 = t187 ** 2
  t317 = 0.1e1 / t316
  t323 = t120 * t198
  t324 = t323 * t202
  t327 = params.a * t314
  t328 = t188 * t191
  t329 = t327 * t328
  t331 = t126 * t211 * t213
  t332 = t121 * t331
  t335 = t121 * t315
  t336 = t197 ** 2
  t337 = 0.1e1 / t336
  t338 = t337 * t303
  t339 = t118 ** 2
  t340 = t119 ** 2
  t341 = 0.1e1 / t340
  t343 = t339 * t341 * t126
  t344 = t338 * t343
  t347 = 0.1e1 / t197 / t115
  t355 = params.b * t313
  t356 = t121 * t355
  t361 = t121 * t327 * t198
  t362 = t209 * t200
  t366 = t211 ** 2
  t368 = t124 ** 2
  t369 = 0.1e1 / t368
  t372 = params.a * t301
  t373 = t303 * t123
  t378 = t313 * t317
  t380 = params.a * t347
  t381 = t303 * t118
  t384 = t309 * t118
  t386 = t313 * t337
  t388 = t205 * t309 * t123 - t208 * t384 - 0.2e1 * t372 * t373 + t378 * t373 - 0.2e1 * t380 * t381 + t386 * t381
  t389 = params.b * t388
  t395 = -0.2e1 * t107 * t301 * t305 + t189 * t311 + t315 * t317 * t305 - 0.2e1 * t315 * t188 * t303 * t114 * t324 - 0.2e1 * t329 * t332 + t335 * t344 - 0.2e1 * t196 * t347 * t303 * t202 - t196 * t198 * t309 * t202 + t356 * t338 * t202 - t356 * t344 + 0.2e1 * t361 * t362 * t331 + t127 * t314 * t366 * t369 - t127 * t389 * t213 + t127 * params.b * t366 * t369
  t396 = f.my_piecewise5(t104, 0, t106, 0, t395)
  t398 = t102 * t396 + t296 * t128 + 0.2e1 * t185 * t217 + t243
  t403 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t130 + t6 * t138 * t130 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t142 * t219 - t6 * t230 * t130 / 0.30e2 + t6 * t234 * t219 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t238 * t398)
  t405 = r1 <= f.p.dens_threshold
  t406 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t407 = 0.1e1 + t406
  t408 = t407 <= f.p.zeta_threshold
  t409 = t407 ** (0.1e1 / 0.3e1)
  t410 = 0.1e1 / t409
  t412 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t413 = t412 ** 2
  t416 = t409 ** 2
  t418 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t422 = f.my_piecewise3(t408, 0, 0.10e2 / 0.9e1 * t410 * t413 + 0.5e1 / 0.3e1 * t416 * t418)
  t424 = r1 ** 2
  t425 = r1 ** (0.1e1 / 0.3e1)
  t426 = t425 ** 2
  t430 = t51 * s2 / t426 / t424
  t431 = 0.5e1 / 0.72e2 * t430
  t438 = l1 ** 2
  t444 = t69 * t438 / t425 / t424 / r1 / 0.5832e4
  t445 = t424 ** 2
  t451 = t69 * s2 / t425 / t445 * l1 / 0.5184e4
  t452 = s2 ** 2
  t458 = t69 * t452 / t425 / t445 / r1 / 0.17496e5
  t461 = (t444 - t451 + t458) ** 2
  t463 = (0.1e1 + t431) ** 2
  t467 = jnp.sqrt(0.1e1 + t461 / t463)
  t470 = (0.1e1 + 0.5e1 / 0.648e3 * t430 + 0.5e1 / 0.54e2 * t51 * l1 / t426 / r1 + t444 - t451 + t458) / t467 - t431
  t474 = f.my_piecewise3(t470 < t103, t103, t470)
  t476 = f.my_piecewise3(t474 < t105, t474, t105)
  t477 = 0.1e1 / t476
  t479 = jnp.exp(-t107 * t477)
  t483 = jnp.exp(-params.a / (params.a - t476))
  t485 = (0.1e1 + t483) ** params.b
  t488 = jnp.exp(-params.a * t477)
  t490 = (t488 + t483) ** params.b
  t493 = f.my_piecewise5(t470 <= t103, 0, t105 <= t470, 1, t479 * t485 / t490)
  t495 = t470 * t493 + t431
  t501 = f.my_piecewise3(t408, 0, 0.5e1 / 0.3e1 * t416 * t412)
  t507 = f.my_piecewise3(t408, t225, t416 * t407)
  t513 = f.my_piecewise3(t405, 0, 0.3e1 / 0.20e2 * t6 * t422 * t44 * t495 + t6 * t501 * t137 * t495 / 0.5e1 - t6 * t507 * t229 * t495 / 0.30e2)
  t523 = t24 ** 2
  t527 = 0.6e1 * t34 - 0.6e1 * t17 / t523
  t528 = f.my_piecewise5(t11, 0, t15, 0, t527)
  t532 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t528)
  t555 = 0.1e1 / t43 / t24
  t567 = 0.1e1 / t54 / t85
  t569 = t51 * s0 * t567
  t570 = 0.770e3 / 0.243e3 * t569
  t577 = 0.260e3 / 0.19683e5 * t69 * t70 * t161
  t581 = 0.247e3 / 0.8748e4 * t69 * s0 * t257 * l0
  t582 = t77 ** 2
  t584 = 0.1e1 / t53 / t582
  t587 = 0.836e3 / 0.59049e5 * t69 * t84 * t584
  t630 = t47 ** 2
  t648 = (-0.770e3 / 0.2187e4 * t569 - 0.1100e4 / 0.729e3 * t51 * l0 * t240 - t577 + t581 - t587) * t100 - 0.3e1 / 0.2e1 * t261 * t168 * t182 + 0.9e1 / 0.4e1 * t165 * t267 * t269 - 0.3e1 / 0.2e1 * t263 * t293 - 0.15e2 / 0.8e1 * t91 / t99 / t265 / t98 * t269 * t182 + 0.9e1 / 0.4e1 * t268 * t182 * t293 - t169 * (0.6e1 * t171 * t96 * t279 + 0.20e2 / 0.9e1 * t272 * t175 * t46 * t179 + 0.100e3 / 0.81e2 * t92 * t283 * t171 * t259 + 0.20e2 / 0.9e1 * t275 * t279 * t146 - 0.220e3 / 0.27e2 * t276 * t242 + 0.2e1 * t170 * (-t577 + t581 - t587) + 0.2000e4 / 0.2187e4 * t93 / t282 / t94 / t630 * t84 * s0 / t582 / t71 - 0.550e3 / 0.243e3 * t285 * t286 * t584 + 0.1540e4 / 0.243e3 * t177 * t178 * t567) / 0.2e1 + t570
  t654 = t314 * params.b
  t655 = t313 * t654
  t665 = t303 * t191
  t666 = t665 * t123
  t669 = t206 * t309
  t673 = 0.1e1 / t316 / t111
  t677 = f.my_piecewise3(t108, 0, t648)
  t678 = f.my_piecewise3(t110, t677, 0)
  t683 = t313 * params.a
  t685 = 0.1e1 / t316 / t187
  t689 = t665 * t118
  t692 = t209 * t309
  t696 = 0.1e1 / t336 / t115
  t705 = 0.1e1 / t336 / t197
  t708 = -t208 * t678 * t118 + t205 * t678 * t123 - 0.6e1 * t313 * t673 * t666 + 0.6e1 * t313 * t696 * t689 + 0.6e1 * params.a * t317 * t666 - 0.6e1 * params.a * t337 * t689 + t683 * t685 * t666 - t683 * t705 * t689 - 0.6e1 * t372 * t669 + 0.3e1 * t378 * t669 - 0.6e1 * t380 * t692 + 0.3e1 * t386 * t692
  t712 = t366 * t211
  t715 = 0.1e1 / t368 / t124
  t727 = t121 * t355 * t337
  t729 = t309 * t191 * t202
  t735 = t309 * t339 * t341 * t126 * t191
  t743 = t683 * t654
  t750 = t188 * t665 * t114
  t752 = t120 * t337
  t753 = t752 * t343
  t761 = t683 * t314
  t762 = t761 * t750
  t766 = 0.6e1 * t655 * t188 * t304 * t120 * t198 * t118 * t200 * t331 - t127 * params.b * t708 * t213 - 0.3e1 * t127 * t314 * t712 * t715 - 0.2e1 * t127 * params.b * t712 * t715 - t127 * t654 * t712 * t715 + 0.3e1 * t727 * t729 - 0.3e1 * t727 * t735 + 0.6e1 * t315 * t301 * t665 * t114 * t324 - 0.3e1 * t743 * t317 * t665 * t114 * t324 + 0.3e1 * t743 * t750 * t753 - 0.6e1 * t315 * t750 * t120 * t347 * t202 + 0.3e1 * t762 * t752 * t202
  t770 = t121 * t315 * t337
  t777 = params.a * t654
  t780 = t126 * t366 * t369
  t781 = t121 * t780
  t790 = t121 * params.b * t683
  t791 = t705 * t665
  t794 = t791 * t343
  t802 = t791 * t339 * t118 / t340 / t119 * t126
  t806 = t126 * t388 * t213
  t812 = t696 * t665
  t813 = t812 * t343
  t816 = -0.6e1 * t121 * t107 * t347 * t729 - t196 * t198 * t678 * t202 - 0.3e1 * t329 * t121 * t806 - t121 * t743 * t802 - t790 * t791 * t202 + 0.3e1 * t777 * t328 * t781 + 0.3e1 * t329 * t781 + 0.6e1 * t335 * t813 + 0.3e1 * t770 * t735 - 0.3e1 * t762 * t753 + 0.3e1 * t790 * t794 - 0.2e1 * t790 * t802
  t818 = t121 * t761
  t836 = t188 * t309
  t846 = t665 * t114 * t193
  t859 = 0.3e1 * t127 * t314 * t211 * t369 * t388 + t189 * t678 * t114 * t193 - 0.6e1 * t196 * t337 * t665 * t202 + 0.6e1 * t327 * t301 * t303 * t332 - 0.3e1 * t655 * t317 * t303 * t332 + 0.6e1 * t107 * t317 * t846 + 0.6e1 * t356 * t812 * t202 - 0.3e1 * t327 * t836 * t332 + t743 * t685 * t846 - 0.6e1 * t356 * t813 - 0.3e1 * t818 * t794 + 0.3e1 * t818 * t802
  t868 = t381 * t200 * t331
  t873 = t303 * t339 * t341 * t331
  t885 = t362 * t780
  t912 = 0.3e1 * t127 * t389 * t369 * t211 - 0.6e1 * t315 * t673 * t846 - 0.3e1 * t770 * t868 + 0.3e1 * t770 * t873 + 0.3e1 * t361 * t362 * t806 - 0.6e1 * t315 * t836 * t114 * t323 * t191 * t202 - 0.3e1 * t361 * t885 - 0.3e1 * t121 * t655 * t337 * t873 + 0.6e1 * t121 * t327 * t347 * t868 + 0.3e1 * t361 * t384 * t200 * t331 - 0.3e1 * t121 * t777 * t198 * t885 - 0.6e1 * t107 * t301 * t191 * t311 + 0.3e1 * t315 * t317 * t309 * t194
  t915 = f.my_piecewise5(t104, 0, t106, 0, t766 + t816 + t859 + t912)
  t922 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t532 * t44 * t130 + 0.3e1 / 0.10e2 * t6 * t42 * t137 * t130 + 0.9e1 / 0.20e2 * t6 * t45 * t219 - t6 * t136 * t229 * t130 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t138 * t219 + 0.9e1 / 0.20e2 * t6 * t142 * t398 + 0.2e1 / 0.45e2 * t6 * t227 * t555 * t130 - t6 * t230 * t219 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t234 * t398 + 0.3e1 / 0.20e2 * t6 * t238 * (t102 * t915 + t648 * t128 + 0.3e1 * t185 * t396 + 0.3e1 * t296 * t217 - t570))
  t932 = f.my_piecewise5(t15, 0, t11, 0, -t527)
  t936 = f.my_piecewise3(t408, 0, -0.10e2 / 0.27e2 / t409 / t407 * t413 * t412 + 0.10e2 / 0.3e1 * t410 * t412 * t418 + 0.5e1 / 0.3e1 * t416 * t932)
  t954 = f.my_piecewise3(t405, 0, 0.3e1 / 0.20e2 * t6 * t936 * t44 * t495 + 0.3e1 / 0.10e2 * t6 * t422 * t137 * t495 - t6 * t501 * t229 * t495 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t507 * t555 * t495)
  d111 = 0.3e1 * t403 + 0.3e1 * t513 + t7 * (t922 + t954)

  res = {'v3rho3': d111}
  return res
