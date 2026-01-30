"""Generated from mgga_k_csk_loc.mpl."""

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
  CSK_P_SCALE = np.float64(0.11183527356860551)
  params_csk_a_raw = params.csk_a
  if isinstance(params_csk_a_raw, (str, bytes, dict)):
    params_csk_a = params_csk_a_raw
  else:
    try:
      params_csk_a_seq = list(params_csk_a_raw)
    except TypeError:
      params_csk_a = params_csk_a_raw
    else:
      params_csk_a_seq = np.asarray(params_csk_a_seq, dtype=np.float64)
      params_csk_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_a_seq))
  params_csk_cp_raw = params.csk_cp
  if isinstance(params_csk_cp_raw, (str, bytes, dict)):
    params_csk_cp = params_csk_cp_raw
  else:
    try:
      params_csk_cp_seq = list(params_csk_cp_raw)
    except TypeError:
      params_csk_cp = params_csk_cp_raw
    else:
      params_csk_cp_seq = np.asarray(params_csk_cp_seq, dtype=np.float64)
      params_csk_cp = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_cp_seq))
  params_csk_cq_raw = params.csk_cq
  if isinstance(params_csk_cq_raw, (str, bytes, dict)):
    params_csk_cq = params_csk_cq_raw
  else:
    try:
      params_csk_cq_seq = list(params_csk_cq_raw)
    except TypeError:
      params_csk_cq = params_csk_cq_raw
    else:
      params_csk_cq_seq = np.asarray(params_csk_cq_seq, dtype=np.float64)
      params_csk_cq = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_cq_seq))

  csk_p = lambda x: X2S ** 2 * x ** 2 * CSK_P_SCALE

  csk_q = lambda u: jnp.zeros_like(u)

  csk_z = lambda p, q: 1 + params_csk_cp * p + params_csk_cq * q - (1 + 5 * p / 3)

  csk_I_negz = lambda z: (1 - jnp.exp(-1 / jnp.abs(z) ** params_csk_a)) ** (1 / params_csk_a)

  csk_I_cutoff_small = (-jnp.log(DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I_cutoff_large = (-jnp.log(1 - DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I = lambda z: f.my_piecewise5(z < -csk_I_cutoff_large, 0, z > -csk_I_cutoff_small, 1, csk_I_negz(jnp.maximum(jnp.minimum(z, -csk_I_cutoff_small), -csk_I_cutoff_large)))

  csk_f0 = lambda p, q, z: 1 + 5 * p / 3 + z * csk_I(z)

  csk_f = lambda x, u: csk_f0(csk_p(x), csk_q(u), csk_z(csk_p(x), csk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, csk_f, rs, z, xs0, xs1, u0, u1)

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
  CSK_P_SCALE = np.float64(0.11183527356860551)
  params_csk_a_raw = params.csk_a
  if isinstance(params_csk_a_raw, (str, bytes, dict)):
    params_csk_a = params_csk_a_raw
  else:
    try:
      params_csk_a_seq = list(params_csk_a_raw)
    except TypeError:
      params_csk_a = params_csk_a_raw
    else:
      params_csk_a_seq = np.asarray(params_csk_a_seq, dtype=np.float64)
      params_csk_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_a_seq))
  params_csk_cp_raw = params.csk_cp
  if isinstance(params_csk_cp_raw, (str, bytes, dict)):
    params_csk_cp = params_csk_cp_raw
  else:
    try:
      params_csk_cp_seq = list(params_csk_cp_raw)
    except TypeError:
      params_csk_cp = params_csk_cp_raw
    else:
      params_csk_cp_seq = np.asarray(params_csk_cp_seq, dtype=np.float64)
      params_csk_cp = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_cp_seq))
  params_csk_cq_raw = params.csk_cq
  if isinstance(params_csk_cq_raw, (str, bytes, dict)):
    params_csk_cq = params_csk_cq_raw
  else:
    try:
      params_csk_cq_seq = list(params_csk_cq_raw)
    except TypeError:
      params_csk_cq = params_csk_cq_raw
    else:
      params_csk_cq_seq = np.asarray(params_csk_cq_seq, dtype=np.float64)
      params_csk_cq = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_cq_seq))

  csk_p = lambda x: X2S ** 2 * x ** 2 * CSK_P_SCALE

  csk_q = lambda u: jnp.zeros_like(u)

  csk_z = lambda p, q: 1 + params_csk_cp * p + params_csk_cq * q - (1 + 5 * p / 3)

  csk_I_negz = lambda z: (1 - jnp.exp(-1 / jnp.abs(z) ** params_csk_a)) ** (1 / params_csk_a)

  csk_I_cutoff_small = (-jnp.log(DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I_cutoff_large = (-jnp.log(1 - DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I = lambda z: f.my_piecewise5(z < -csk_I_cutoff_large, 0, z > -csk_I_cutoff_small, 1, csk_I_negz(jnp.maximum(jnp.minimum(z, -csk_I_cutoff_small), -csk_I_cutoff_large)))

  csk_f0 = lambda p, q, z: 1 + 5 * p / 3 + z * csk_I(z)

  csk_f = lambda x, u: csk_f0(csk_p(x), csk_q(u), csk_z(csk_p(x), csk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, csk_f, rs, z, xs0, xs1, u0, u1)

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
  CSK_P_SCALE = np.float64(0.11183527356860551)
  params_csk_a_raw = params.csk_a
  if isinstance(params_csk_a_raw, (str, bytes, dict)):
    params_csk_a = params_csk_a_raw
  else:
    try:
      params_csk_a_seq = list(params_csk_a_raw)
    except TypeError:
      params_csk_a = params_csk_a_raw
    else:
      params_csk_a_seq = np.asarray(params_csk_a_seq, dtype=np.float64)
      params_csk_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_a_seq))
  params_csk_cp_raw = params.csk_cp
  if isinstance(params_csk_cp_raw, (str, bytes, dict)):
    params_csk_cp = params_csk_cp_raw
  else:
    try:
      params_csk_cp_seq = list(params_csk_cp_raw)
    except TypeError:
      params_csk_cp = params_csk_cp_raw
    else:
      params_csk_cp_seq = np.asarray(params_csk_cp_seq, dtype=np.float64)
      params_csk_cp = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_cp_seq))
  params_csk_cq_raw = params.csk_cq
  if isinstance(params_csk_cq_raw, (str, bytes, dict)):
    params_csk_cq = params_csk_cq_raw
  else:
    try:
      params_csk_cq_seq = list(params_csk_cq_raw)
    except TypeError:
      params_csk_cq = params_csk_cq_raw
    else:
      params_csk_cq_seq = np.asarray(params_csk_cq_seq, dtype=np.float64)
      params_csk_cq = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_cq_seq))

  csk_p = lambda x: X2S ** 2 * x ** 2 * CSK_P_SCALE
  csk_q = lambda u: jnp.zeros_like(u)

  csk_z = lambda p, q: 1 + params_csk_cp * p + params_csk_cq * q - (1 + 5 * p / 3)

  csk_I_negz = lambda z: (1 - jnp.exp(-1 / jnp.abs(z) ** params_csk_a)) ** (1 / params_csk_a)

  csk_I_cutoff_small = (-jnp.log(DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I_cutoff_large = (-jnp.log(1 - DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_f0 = lambda p, q, z: 1 + 5 * p / 3 + z * csk_I(z)

  csk_f = lambda x, u: csk_f0(csk_p(x), csk_q(u), csk_z(csk_p(x), csk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, csk_f, rs, z, xs0, xs1, u0, u1)

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
  t45 = 0.5e1 / 0.72e2 * t37 * s0 * t42
  t46 = params.csk_cp * t32
  t47 = t36 * s0
  t51 = params.csk_cq * t32
  t52 = t36 * l0
  t54 = 0.1e1 / t40 / r0
  t58 = t46 * t47 * t42 / 0.24e2 + t51 * t52 * t54 / 0.24e2 - t45
  t60 = jnp.log(0.1e1 - DBL_EPSILON)
  t61 = 0.1e1 / params.csk_a
  t62 = (-t60) ** (-t61)
  t63 = t58 < -t62
  t64 = jnp.log(DBL_EPSILON)
  t65 = (-t64) ** (-t61)
  t66 = -t65 < t58
  t67 = f.my_piecewise3(t66, -t65, t58)
  t68 = -t62 < t67
  t69 = f.my_piecewise3(t68, t67, -t62)
  t70 = abs(t69)
  t71 = t70 ** params.csk_a
  t72 = 0.1e1 / t71
  t73 = jnp.exp(-t72)
  t74 = 0.1e1 - t73
  t75 = t74 ** t61
  t76 = f.my_piecewise5(t63, 0, t66, 1, t75)
  t78 = t58 * t76 + t45 + 0.1e1
  t82 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t78)
  t83 = r1 <= f.p.dens_threshold
  t84 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t85 = 0.1e1 + t84
  t86 = t85 <= f.p.zeta_threshold
  t87 = t85 ** (0.1e1 / 0.3e1)
  t88 = t87 ** 2
  t90 = f.my_piecewise3(t86, t24, t88 * t85)
  t91 = t90 * t30
  t92 = r1 ** 2
  t93 = r1 ** (0.1e1 / 0.3e1)
  t94 = t93 ** 2
  t96 = 0.1e1 / t94 / t92
  t99 = 0.5e1 / 0.72e2 * t37 * s2 * t96
  t100 = t36 * s2
  t104 = t36 * l1
  t106 = 0.1e1 / t94 / r1
  t110 = t46 * t100 * t96 / 0.24e2 + t51 * t104 * t106 / 0.24e2 - t99
  t111 = t110 < -t62
  t112 = -t65 < t110
  t113 = f.my_piecewise3(t112, -t65, t110)
  t114 = -t62 < t113
  t115 = f.my_piecewise3(t114, t113, -t62)
  t116 = abs(t115)
  t117 = t116 ** params.csk_a
  t118 = 0.1e1 / t117
  t119 = jnp.exp(-t118)
  t120 = 0.1e1 - t119
  t121 = t120 ** t61
  t122 = f.my_piecewise5(t111, 0, t112, 1, t121)
  t124 = t110 * t122 + t99 + 0.1e1
  t128 = f.my_piecewise3(t83, 0, 0.3e1 / 0.20e2 * t6 * t91 * t124)
  t129 = t7 ** 2
  t131 = t17 / t129
  t132 = t8 - t131
  t133 = f.my_piecewise5(t11, 0, t15, 0, t132)
  t136 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t133)
  t141 = 0.1e1 / t29
  t145 = t6 * t28 * t141 * t78 / 0.10e2
  t148 = 0.1e1 / t40 / t38 / r0
  t151 = 0.5e1 / 0.27e2 * t37 * s0 * t148
  t158 = -t46 * t47 * t148 / 0.9e1 - 0.5e1 / 0.72e2 * t51 * t52 * t42 + t151
  t161 = jnp.abs(1 - t69)
  t162 = t75 * t72 * t161
  t163 = f.my_piecewise3(t66, 0, t158)
  t164 = f.my_piecewise3(t68, t163, 0)
  t165 = 0.1e1 / t70
  t168 = t73 / t74
  t171 = f.my_piecewise5(t63, 0, t66, 0, -t162 * t164 * t165 * t168)
  t178 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t136 * t30 * t78 + t145 + 0.3e1 / 0.20e2 * t6 * t31 * (t158 * t76 + t58 * t171 - t151))
  t180 = f.my_piecewise5(t15, 0, t11, 0, -t132)
  t183 = f.my_piecewise3(t86, 0, 0.5e1 / 0.3e1 * t88 * t180)
  t191 = t6 * t90 * t141 * t124 / 0.10e2
  t193 = f.my_piecewise3(t83, 0, 0.3e1 / 0.20e2 * t6 * t183 * t30 * t124 + t191)
  vrho_0_ = t82 + t128 + t7 * (t178 + t193)
  t196 = -t8 - t131
  t197 = f.my_piecewise5(t11, 0, t15, 0, t196)
  t200 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t197)
  t206 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t200 * t30 * t78 + t145)
  t208 = f.my_piecewise5(t15, 0, t11, 0, -t196)
  t211 = f.my_piecewise3(t86, 0, 0.5e1 / 0.3e1 * t88 * t208)
  t218 = 0.1e1 / t94 / t92 / r1
  t221 = 0.5e1 / 0.27e2 * t37 * s2 * t218
  t228 = -t46 * t100 * t218 / 0.9e1 - 0.5e1 / 0.72e2 * t51 * t104 * t96 + t221
  t231 = jnp.abs(1 - t115)
  t232 = t121 * t118 * t231
  t233 = f.my_piecewise3(t112, 0, t228)
  t234 = f.my_piecewise3(t114, t233, 0)
  t235 = 0.1e1 / t116
  t238 = t119 / t120
  t241 = f.my_piecewise5(t111, 0, t112, 0, -t232 * t234 * t235 * t238)
  t248 = f.my_piecewise3(t83, 0, 0.3e1 / 0.20e2 * t6 * t211 * t30 * t124 + t191 + 0.3e1 / 0.20e2 * t6 * t91 * (t110 * t241 + t228 * t122 - t221))
  vrho_1_ = t82 + t128 + t7 * (t206 + t248)
  t252 = 0.5e1 / 0.72e2 * t37 * t42
  t256 = t46 * t36 * t42 / 0.24e2 - t252
  t258 = f.my_piecewise3(t66, 0, t256)
  t259 = f.my_piecewise3(t68, t258, 0)
  t263 = f.my_piecewise5(t63, 0, t66, 0, -t162 * t259 * t165 * t168)
  t269 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (t256 * t76 + t58 * t263 + t252))
  vsigma_0_ = t7 * t269
  vsigma_1_ = 0.0e0
  t271 = 0.5e1 / 0.72e2 * t37 * t96
  t275 = t46 * t36 * t96 / 0.24e2 - t271
  t277 = f.my_piecewise3(t112, 0, t275)
  t278 = f.my_piecewise3(t114, t277, 0)
  t282 = f.my_piecewise5(t111, 0, t112, 0, -t232 * t278 * t235 * t238)
  t288 = f.my_piecewise3(t83, 0, 0.3e1 / 0.20e2 * t6 * t91 * (t110 * t282 + t275 * t122 + t271))
  vsigma_2_ = t7 * t288
  t289 = t36 * t54
  t295 = f.my_piecewise3(t66, 0, t51 * t289 / 0.24e2)
  t296 = f.my_piecewise3(t68, t295, 0)
  t300 = f.my_piecewise5(t63, 0, t66, 0, -t162 * t296 * t165 * t168)
  t306 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (t51 * t289 * t76 / 0.24e2 + t58 * t300))
  vlapl_0_ = t7 * t306
  t307 = t36 * t106
  t313 = f.my_piecewise3(t112, 0, t51 * t307 / 0.24e2)
  t314 = f.my_piecewise3(t114, t313, 0)
  t318 = f.my_piecewise5(t111, 0, t112, 0, -t232 * t314 * t235 * t238)
  t324 = f.my_piecewise3(t83, 0, 0.3e1 / 0.20e2 * t6 * t91 * (t51 * t307 * t122 / 0.24e2 + t110 * t318))
  vlapl_1_ = t7 * t324
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
  CSK_P_SCALE = np.float64(0.11183527356860551)
  params_csk_a_raw = params.csk_a
  if isinstance(params_csk_a_raw, (str, bytes, dict)):
    params_csk_a = params_csk_a_raw
  else:
    try:
      params_csk_a_seq = list(params_csk_a_raw)
    except TypeError:
      params_csk_a = params_csk_a_raw
    else:
      params_csk_a_seq = np.asarray(params_csk_a_seq, dtype=np.float64)
      params_csk_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_a_seq))
  params_csk_cp_raw = params.csk_cp
  if isinstance(params_csk_cp_raw, (str, bytes, dict)):
    params_csk_cp = params_csk_cp_raw
  else:
    try:
      params_csk_cp_seq = list(params_csk_cp_raw)
    except TypeError:
      params_csk_cp = params_csk_cp_raw
    else:
      params_csk_cp_seq = np.asarray(params_csk_cp_seq, dtype=np.float64)
      params_csk_cp = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_cp_seq))
  params_csk_cq_raw = params.csk_cq
  if isinstance(params_csk_cq_raw, (str, bytes, dict)):
    params_csk_cq = params_csk_cq_raw
  else:
    try:
      params_csk_cq_seq = list(params_csk_cq_raw)
    except TypeError:
      params_csk_cq = params_csk_cq_raw
    else:
      params_csk_cq_seq = np.asarray(params_csk_cq_seq, dtype=np.float64)
      params_csk_cq = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_cq_seq))

  csk_p = lambda x: X2S ** 2 * x ** 2 * CSK_P_SCALE
  csk_q = lambda u: jnp.zeros_like(u)

  csk_z = lambda p, q: 1 + params_csk_cp * p + params_csk_cq * q - (1 + 5 * p / 3)

  csk_I_negz = lambda z: (1 - jnp.exp(-1 / jnp.abs(z) ** params_csk_a)) ** (1 / params_csk_a)

  csk_I_cutoff_small = (-jnp.log(DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I_cutoff_large = (-jnp.log(1 - DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_f0 = lambda p, q, z: 1 + 5 * p / 3 + z * csk_I(z)

  csk_f = lambda x, u: csk_f0(csk_p(x), csk_q(u), csk_z(csk_p(x), csk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, csk_f, rs, z, xs0, xs1, u0, u1)

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
  t36 = t32 * t35
  t38 = 0.5e1 / 0.72e2 * t29 * t36
  t39 = params.csk_cp * t24
  t40 = t39 * t28
  t43 = params.csk_cq * t24
  t44 = t43 * t28
  t45 = l0 * t31
  t47 = 0.1e1 / t22 / r0
  t51 = t40 * t36 / 0.24e2 + t44 * t45 * t47 / 0.24e2 - t38
  t53 = jnp.log(0.1e1 - DBL_EPSILON)
  t54 = 0.1e1 / params.csk_a
  t55 = (-t53) ** (-t54)
  t56 = t51 < -t55
  t57 = jnp.log(DBL_EPSILON)
  t58 = (-t57) ** (-t54)
  t59 = -t58 < t51
  t60 = f.my_piecewise3(t59, -t58, t51)
  t61 = -t55 < t60
  t62 = f.my_piecewise3(t61, t60, -t55)
  t63 = abs(t62)
  t64 = t63 ** params.csk_a
  t65 = 0.1e1 / t64
  t66 = jnp.exp(-t65)
  t67 = 0.1e1 - t66
  t68 = t67 ** t54
  t69 = f.my_piecewise5(t56, 0, t59, 1, t68)
  t71 = t51 * t69 + t38 + 0.1e1
  t75 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t71)
  t84 = t32 / t22 / t33 / r0
  t86 = 0.5e1 / 0.27e2 * t29 * t84
  t92 = -t40 * t84 / 0.9e1 - 0.5e1 / 0.72e2 * t44 * t45 * t35 + t86
  t95 = jnp.abs(1 - t62)
  t96 = t68 * t65 * t95
  t97 = f.my_piecewise3(t59, 0, t92)
  t98 = f.my_piecewise3(t61, t97, 0)
  t99 = 0.1e1 / t63
  t102 = t66 / t67
  t105 = f.my_piecewise5(t56, 0, t59, 0, -t96 * t98 * t99 * t102)
  t112 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t71 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (t51 * t105 + t92 * t69 - t86))
  vrho_0_ = 0.2e1 * r0 * t112 + 0.2e1 * t75
  t117 = 0.5e1 / 0.72e2 * t29 * t31 * t35
  t118 = t28 * t31
  t122 = t39 * t118 * t35 / 0.24e2 - t117
  t124 = f.my_piecewise3(t59, 0, t122)
  t125 = f.my_piecewise3(t61, t124, 0)
  t129 = f.my_piecewise5(t56, 0, t59, 0, -t96 * t125 * t99 * t102)
  t135 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (t122 * t69 + t51 * t129 + t117))
  vsigma_0_ = 0.2e1 * r0 * t135
  t144 = f.my_piecewise3(t59, 0, t43 * t118 * t47 / 0.24e2)
  t145 = f.my_piecewise3(t61, t144, 0)
  t149 = f.my_piecewise5(t56, 0, t59, 0, -t96 * t145 * t99 * t102)
  t155 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (t44 * t31 * t47 * t69 / 0.24e2 + t51 * t149))
  vlapl_0_ = 0.2e1 * r0 * t155
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
  t37 = t32 * t36
  t39 = 0.5e1 / 0.72e2 * t29 * t37
  t41 = params.csk_cp * t24 * t28
  t45 = params.csk_cq * t24 * t28
  t46 = l0 * t31
  t52 = t41 * t37 / 0.24e2 + t45 * t46 / t34 / r0 / 0.24e2 - t39
  t54 = jnp.log(0.1e1 - DBL_EPSILON)
  t55 = 0.1e1 / params.csk_a
  t56 = (-t54) ** (-t55)
  t57 = t52 < -t56
  t58 = jnp.log(DBL_EPSILON)
  t59 = (-t58) ** (-t55)
  t60 = -t59 < t52
  t61 = f.my_piecewise3(t60, -t59, t52)
  t62 = -t56 < t61
  t63 = f.my_piecewise3(t62, t61, -t56)
  t64 = abs(t63)
  t65 = t64 ** params.csk_a
  t66 = 0.1e1 / t65
  t67 = jnp.exp(-t66)
  t68 = 0.1e1 - t67
  t69 = t68 ** t55
  t70 = f.my_piecewise5(t57, 0, t60, 1, t69)
  t72 = t52 * t70 + t39 + 0.1e1
  t76 = t20 * t34
  t79 = 0.1e1 / t34 / t33 / r0
  t80 = t32 * t79
  t82 = 0.5e1 / 0.27e2 * t29 * t80
  t88 = -t41 * t80 / 0.9e1 - 0.5e1 / 0.72e2 * t45 * t46 * t36 + t82
  t90 = t69 * t66
  t91 = jnp.abs(1 - t63)
  t92 = t90 * t91
  t93 = f.my_piecewise3(t60, 0, t88)
  t94 = f.my_piecewise3(t62, t93, 0)
  t95 = 0.1e1 / t64
  t97 = 0.1e1 / t68
  t98 = t67 * t97
  t99 = t94 * t95 * t98
  t101 = f.my_piecewise5(t57, 0, t60, 0, -t92 * t99)
  t103 = t52 * t101 + t88 * t70 - t82
  t108 = f.my_piecewise3(t2, 0, t7 * t23 * t72 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t76 * t103)
  t119 = t33 ** 2
  t122 = t32 / t34 / t119
  t124 = 0.55e2 / 0.81e2 * t29 * t122
  t130 = 0.11e2 / 0.27e2 * t41 * t122 + 0.5e1 / 0.27e2 * t45 * t46 * t79 - t124
  t134 = t65 ** 2
  t136 = t69 / t134
  t137 = t91 ** 2
  t139 = t94 ** 2
  t140 = t64 ** 2
  t141 = 0.1e1 / t140
  t142 = t139 * t141
  t143 = t67 ** 2
  t144 = t68 ** 2
  t145 = 0.1e1 / t144
  t149 = t137 * t139
  t153 = t141 * t67 * t97 * params.csk_a
  t155 = signum(1, t63)
  t158 = f.my_piecewise3(t60, 0, t130)
  t159 = f.my_piecewise3(t62, t158, 0)
  t166 = t136 * t149
  t173 = f.my_piecewise5(t57, 0, t60, 0, t136 * t137 * t142 * t143 * t145 - t166 * t141 * t143 * t145 * params.csk_a + t90 * t137 * t142 * t98 - t92 * t159 * t95 * t98 + t90 * t149 * t153 - t90 * t155 * t99 - t166 * t153)
  t180 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t72 / 0.30e2 + t7 * t23 * t103 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t76 * (0.2e1 * t88 * t101 + t130 * t70 + t52 * t173 + t124))
  v2rho2_0_ = 0.2e1 * r0 * t180 + 0.4e1 * t108
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
  t38 = t33 * t37
  t40 = 0.5e1 / 0.72e2 * t30 * t38
  t42 = params.csk_cp * t25 * t29
  t46 = params.csk_cq * t25 * t29
  t47 = l0 * t32
  t53 = t42 * t38 / 0.24e2 + t46 * t47 / t35 / r0 / 0.24e2 - t40
  t55 = jnp.log(0.1e1 - DBL_EPSILON)
  t56 = 0.1e1 / params.csk_a
  t57 = (-t55) ** (-t56)
  t58 = t53 < -t57
  t59 = jnp.log(DBL_EPSILON)
  t60 = (-t59) ** (-t56)
  t61 = -t60 < t53
  t62 = f.my_piecewise3(t61, -t60, t53)
  t63 = -t57 < t62
  t64 = f.my_piecewise3(t63, t62, -t57)
  t65 = abs(t64)
  t66 = t65 ** params.csk_a
  t67 = 0.1e1 / t66
  t68 = jnp.exp(-t67)
  t69 = 0.1e1 - t68
  t70 = t69 ** t56
  t71 = f.my_piecewise5(t58, 0, t61, 1, t70)
  t73 = t53 * t71 + t40 + 0.1e1
  t78 = t20 / t21
  t81 = 0.1e1 / t35 / t34 / r0
  t82 = t33 * t81
  t84 = 0.5e1 / 0.27e2 * t30 * t82
  t90 = -t42 * t82 / 0.9e1 - 0.5e1 / 0.72e2 * t46 * t47 * t37 + t84
  t92 = t70 * t67
  t93 = abs(1, t64)
  t94 = t92 * t93
  t95 = f.my_piecewise3(t61, 0, t90)
  t96 = f.my_piecewise3(t63, t95, 0)
  t97 = 0.1e1 / t65
  t99 = 0.1e1 / t69
  t100 = t68 * t99
  t101 = t96 * t97 * t100
  t103 = f.my_piecewise5(t58, 0, t61, 0, -t94 * t101)
  t105 = t53 * t103 + t90 * t71 - t84
  t109 = t20 * t35
  t110 = t34 ** 2
  t112 = 0.1e1 / t35 / t110
  t113 = t33 * t112
  t115 = 0.55e2 / 0.81e2 * t30 * t113
  t121 = 0.11e2 / 0.27e2 * t42 * t113 + 0.5e1 / 0.27e2 * t46 * t47 * t81 - t115
  t125 = t66 ** 2
  t127 = t70 / t125
  t128 = t93 ** 2
  t130 = t96 ** 2
  t131 = t65 ** 2
  t132 = 0.1e1 / t131
  t133 = t130 * t132
  t134 = t68 ** 2
  t135 = t69 ** 2
  t136 = 0.1e1 / t135
  t137 = t134 * t136
  t140 = t128 * t130
  t142 = t132 * t68
  t143 = t99 * params.csk_a
  t144 = t142 * t143
  t146 = signum(1, t64)
  t147 = t92 * t146
  t148 = t147 * t101
  t149 = f.my_piecewise3(t61, 0, t121)
  t150 = f.my_piecewise3(t63, t149, 0)
  t152 = t150 * t97 * t100
  t157 = t127 * t140
  t159 = t132 * t134
  t160 = t136 * params.csk_a
  t164 = f.my_piecewise5(t58, 0, t61, 0, t92 * t128 * t133 * t100 + t127 * t128 * t133 * t137 + t92 * t140 * t144 - t157 * t159 * t160 - t157 * t144 - t94 * t152 - t148)
  t166 = 0.2e1 * t90 * t103 + t121 * t71 + t53 * t164 + t115
  t171 = f.my_piecewise3(t2, 0, -t7 * t24 * t73 / 0.30e2 + t7 * t78 * t105 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t109 * t166)
  t188 = t33 / t35 / t110 / r0
  t190 = 0.770e3 / 0.243e3 * t30 * t188
  t196 = -0.154e3 / 0.81e2 * t42 * t188 - 0.55e2 / 0.81e2 * t46 * t47 * t112 + t190
  t202 = t93 * t130
  t208 = t128 * t96
  t214 = t146 * t130
  t215 = t127 * t214
  t220 = t128 * t150
  t221 = t127 * t220
  t226 = t132 * params.csk_a
  t237 = f.my_piecewise3(t61, 0, t196)
  t238 = f.my_piecewise3(t63, t237, 0)
  t242 = t128 * t93
  t244 = t130 * t96
  t246 = 0.1e1 / t131 / t65
  t247 = t244 * t246
  t257 = t70 / t125 / t66
  t259 = t134 * t68
  t261 = 0.1e1 / t135 / t69
  t267 = t242 * t244
  t268 = t257 * t267
  t269 = params.csk_a ** 2
  t271 = t246 * t269 * t137
  t274 = 0.3e1 * t92 * t202 * t142 * t143 * t146 + 0.3e1 * t92 * t208 * t142 * t143 * t150 - 0.3e1 * t215 * t159 * t160 * t93 - 0.3e1 * t221 * t159 * t160 * t96 - 0.3e1 * t221 * t226 * t96 * t68 * t99 - 0.3e1 * t215 * t226 * t93 * t68 * t99 - t94 * t238 * t97 * t100 - 0.2e1 * t92 * t242 * t247 * t100 - 0.3e1 * t127 * t242 * t247 * t137 - t257 * t242 * t247 * t259 * t261 - 0.2e1 * t147 * t152 - t148 - 0.3e1 * t268 * t271
  t275 = t246 * t259
  t294 = t127 * t267
  t297 = t92 * t267
  t298 = t246 * t68
  t299 = t298 * t143
  t309 = t298 * t99 * t269
  t324 = 0.3e1 * t127 * t202 * t159 * t136 * t146 + 0.3e1 * t127 * t208 * t159 * t136 * t150 + 0.3e1 * t92 * t214 * t142 * t99 * t93 + 0.3e1 * t92 * t220 * t142 * t99 * t96 + 0.3e1 * t268 * t246 * t134 * t160 - 0.2e1 * t268 * t275 * t261 * t269 + 0.3e1 * t268 * t275 * t261 * params.csk_a - t268 * t309 + 0.3e1 * t294 * t271 + 0.3e1 * t294 * t299 + 0.3e1 * t294 * t309 - 0.3e1 * t297 * t299 - t297 * t309
  t326 = f.my_piecewise5(t58, 0, t61, 0, t274 + t324)
  t333 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t73 - t7 * t24 * t105 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t78 * t166 + 0.3e1 / 0.20e2 * t7 * t109 * (0.3e1 * t121 * t103 + 0.3e1 * t90 * t164 + t196 * t71 + t53 * t326 - t190))
  v3rho3_0_ = 0.2e1 * r0 * t333 + 0.6e1 * t171

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
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
  t21 = r0 ** 2
  t22 = r0 ** (0.1e1 / 0.3e1)
  t25 = t20 / t22 / t21
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = t26 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = t22 ** 2
  t37 = 0.1e1 / t35 / t21
  t38 = t34 * t37
  t40 = 0.5e1 / 0.72e2 * t31 * t38
  t42 = params.csk_cp * t26 * t30
  t46 = params.csk_cq * t26 * t30
  t47 = l0 * t33
  t53 = t42 * t38 / 0.24e2 + t46 * t47 / t35 / r0 / 0.24e2 - t40
  t55 = jnp.log(0.1e1 - DBL_EPSILON)
  t56 = 0.1e1 / params.csk_a
  t57 = (-t55) ** (-t56)
  t58 = t53 < -t57
  t59 = jnp.log(DBL_EPSILON)
  t60 = (-t59) ** (-t56)
  t61 = -t60 < t53
  t62 = f.my_piecewise3(t61, -t60, t53)
  t63 = -t57 < t62
  t64 = f.my_piecewise3(t63, t62, -t57)
  t65 = abs(t64)
  t66 = t65 ** params.csk_a
  t67 = 0.1e1 / t66
  t68 = jnp.exp(-t67)
  t69 = 0.1e1 - t68
  t70 = t69 ** t56
  t71 = f.my_piecewise5(t58, 0, t61, 1, t70)
  t73 = t53 * t71 + t40 + 0.1e1
  t79 = t20 / t22 / r0
  t80 = t21 * r0
  t82 = 0.1e1 / t35 / t80
  t83 = t34 * t82
  t85 = 0.5e1 / 0.27e2 * t31 * t83
  t91 = -t42 * t83 / 0.9e1 - 0.5e1 / 0.72e2 * t46 * t47 * t37 + t85
  t93 = t70 * t67
  t94 = abs(1, t64)
  t95 = t93 * t94
  t96 = f.my_piecewise3(t61, 0, t91)
  t97 = f.my_piecewise3(t63, t96, 0)
  t98 = 0.1e1 / t65
  t100 = 0.1e1 / t69
  t101 = t68 * t100
  t102 = t97 * t98 * t101
  t104 = f.my_piecewise5(t58, 0, t61, 0, -t95 * t102)
  t106 = t53 * t104 + t91 * t71 - t85
  t111 = t20 / t22
  t112 = t21 ** 2
  t114 = 0.1e1 / t35 / t112
  t115 = t34 * t114
  t117 = 0.55e2 / 0.81e2 * t31 * t115
  t123 = 0.11e2 / 0.27e2 * t42 * t115 + 0.5e1 / 0.27e2 * t46 * t47 * t82 - t117
  t127 = t66 ** 2
  t129 = t70 / t127
  t130 = t94 ** 2
  t131 = t129 * t130
  t132 = t97 ** 2
  t133 = t65 ** 2
  t134 = 0.1e1 / t133
  t135 = t132 * t134
  t136 = t68 ** 2
  t137 = t69 ** 2
  t138 = 0.1e1 / t137
  t139 = t136 * t138
  t140 = t135 * t139
  t142 = t130 * t132
  t144 = t134 * t68
  t145 = t100 * params.csk_a
  t146 = t144 * t145
  t148 = signum(1, t64)
  t149 = t93 * t148
  t150 = t149 * t102
  t151 = f.my_piecewise3(t61, 0, t123)
  t152 = f.my_piecewise3(t63, t151, 0)
  t154 = t152 * t98 * t101
  t156 = t93 * t130
  t157 = t135 * t101
  t159 = t129 * t142
  t161 = t134 * t136
  t162 = t138 * params.csk_a
  t163 = t161 * t162
  t166 = f.my_piecewise5(t58, 0, t61, 0, t93 * t142 * t146 + t131 * t140 - t159 * t146 - t95 * t154 + t156 * t157 - t159 * t163 - t150)
  t168 = 0.2e1 * t91 * t104 + t123 * t71 + t53 * t166 + t117
  t172 = t20 * t35
  t175 = 0.1e1 / t35 / t112 / r0
  t176 = t34 * t175
  t178 = 0.770e3 / 0.243e3 * t31 * t176
  t184 = -0.154e3 / 0.81e2 * t42 * t176 - 0.55e2 / 0.81e2 * t46 * t47 * t114 + t178
  t190 = t130 * t94
  t192 = t132 * t97
  t194 = 0.1e1 / t133 / t65
  t195 = t192 * t194
  t205 = t70 / t127 / t66
  t207 = t136 * t68
  t209 = 0.1e1 / t137 / t69
  t210 = t207 * t209
  t213 = t149 * t154
  t215 = f.my_piecewise3(t61, 0, t184)
  t216 = f.my_piecewise3(t63, t215, 0)
  t218 = t216 * t98 * t101
  t220 = t190 * t192
  t221 = t129 * t220
  t222 = t194 * params.csk_a
  t223 = t222 * t101
  t226 = t205 * t220
  t227 = t194 * t136
  t231 = t93 * t220
  t232 = t194 * t68
  t233 = params.csk_a ** 2
  t234 = t100 * t233
  t235 = t232 * t234
  t240 = t148 * t132
  t242 = t100 * t94
  t244 = t93 * t240 * t144 * t242
  t246 = t130 * t152
  t249 = t144 * t100 * t97
  t252 = t194 * t233
  t253 = t252 * t139
  t256 = -0.2e1 * t93 * t190 * t195 * t101 - 0.3e1 * t129 * t190 * t195 * t139 - t205 * t190 * t195 * t210 + 0.3e1 * t226 * t227 * t162 + 0.3e1 * t93 * t246 * t249 - t95 * t218 + 0.3e1 * t221 * t223 + 0.3e1 * t221 * t235 - t226 * t235 - 0.3e1 * t226 * t253 - t231 * t235 - 0.2e1 * t213 + 0.3e1 * t244
  t257 = t194 * t207
  t258 = t209 * t233
  t262 = t94 * t132
  t264 = t138 * t148
  t266 = t129 * t262 * t161 * t264
  t268 = t130 * t97
  t269 = t129 * t268
  t270 = t138 * t152
  t274 = t209 * params.csk_a
  t283 = t145 * t148
  t285 = t93 * t262 * t144 * t283
  t287 = t93 * t268
  t288 = t145 * t152
  t292 = t129 * t240
  t295 = t292 * t161 * t162 * t94
  t297 = t129 * t246
  t299 = t161 * t162 * t97
  t302 = t134 * params.csk_a
  t305 = t302 * t97 * t68 * t100
  t311 = t292 * t302 * t94 * t68 * t100
  t313 = 0.3e1 * t287 * t144 * t288 + 0.3e1 * t269 * t161 * t270 - 0.2e1 * t226 * t257 * t258 + 0.3e1 * t226 * t257 * t274 + 0.3e1 * t221 * t253 - 0.3e1 * t231 * t223 - 0.3e1 * t297 * t299 - 0.3e1 * t297 * t305 - t150 + 0.3e1 * t266 + 0.3e1 * t285 - 0.3e1 * t295 - 0.3e1 * t311
  t315 = f.my_piecewise5(t58, 0, t61, 0, t256 + t313)
  t317 = 0.3e1 * t123 * t104 + 0.3e1 * t91 * t166 + t184 * t71 + t53 * t315 - t178
  t322 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t73 - t7 * t79 * t106 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t111 * t168 + 0.3e1 / 0.20e2 * t7 * t172 * t317)
  t342 = t34 / t35 / t112 / t21
  t344 = 0.13090e5 / 0.729e3 * t31 * t342
  t350 = 0.2618e4 / 0.243e3 * t42 * t342 + 0.770e3 / 0.243e3 * t46 * t47 * t175 - t344
  t358 = t130 ** 2
  t360 = t132 ** 2
  t361 = t133 ** 2
  t362 = 0.1e1 / t361
  t363 = t360 * t362
  t378 = t358 * t360
  t379 = t205 * t378
  t380 = t362 * t207
  t381 = t380 * t274
  t384 = t93 * t378
  t385 = t362 * t68
  t386 = t233 * params.csk_a
  t388 = t385 * t100 * t386
  t390 = t129 * t378
  t396 = t127 ** 2
  t398 = t70 / t396
  t399 = t398 * t378
  t402 = t380 * t209 * t386
  t405 = t380 * t258
  t408 = t362 * t136
  t409 = t138 * t233
  t410 = t408 * t409
  t423 = t190 * t132
  t424 = t129 * t423
  t429 = t130 * t192
  t430 = t205 * t429
  t431 = t209 * t148
  t436 = t148 * t192
  t437 = t205 * t436
  t442 = t130 * t216
  t443 = t129 * t442
  t446 = t205 * t423
  t447 = t209 * t152
  t452 = 0.14e2 * t93 * t148 * t152 * t144 * t242 * t97 - 0.12e2 * t437 * t257 * t258 * t130 + 0.4e1 * t287 * t144 * t145 * t216 + 0.18e2 * t424 * t227 * t409 * t152 + 0.18e2 * t430 * t257 * t431 * params.csk_a + 0.18e2 * t446 * t257 * t447 * params.csk_a - 0.4e1 * t443 * t299 + 0.12e2 * t379 * t402 - t399 * t388 - 0.11e2 * t390 * t410 + 0.18e2 * t399 * t405
  t454 = t190 * t152
  t455 = t205 * t454
  t462 = t129 * t429
  t475 = t93 * t429
  t477 = t232 * t234 * t148
  t482 = t93 * t423
  t484 = t232 * t234 * t152
  t491 = t132 * t68 * t100
  t496 = t130 * t68 * t100
  t522 = t94 * t97
  t544 = -0.14e2 * t129 * t94 * t152 * t134 * params.csk_a * t97 * t101 * t148 - 0.14e2 * t129 * t148 * t97 * t134 * t139 * params.csk_a * t94 * t152 + 0.14e2 * t129 * t522 * t161 * t264 * t152 + 0.18e2 * t129 * t436 * t222 * t496 + 0.18e2 * t129 * t454 * t222 * t491 + 0.18e2 * t430 * t227 * t264 * params.csk_a + 0.18e2 * t446 * t227 * t270 * params.csk_a - 0.18e2 * t475 * t232 * t283 - 0.18e2 * t482 * t232 * t288 - 0.6e1 * t437 * t252 * t496 - 0.6e1 * t455 * t252 * t491
  t554 = t148 ** 2
  t558 = t152 ** 2
  t559 = t558 * t134
  t571 = f.my_piecewise3(t61, 0, t350)
  t572 = f.my_piecewise3(t63, t571, 0)
  t577 = t136 ** 2
  t578 = t137 ** 2
  t579 = 0.1e1 / t578
  t588 = t408 * t138 * t386
  t603 = t408 * t162
  t616 = t362 * t577
  t621 = -0.12e2 * t475 * t232 * t100 * t148 - 0.12e2 * t482 * t232 * t100 * t152 + 0.4e1 * t269 * t161 * t138 * t216 - 0.6e1 * t399 * t616 * t579 * params.csk_a - 0.6e1 * t430 * t257 * t431 - 0.6e1 * t446 * t257 * t447 + 0.18e2 * t379 * t588 - 0.18e2 * t379 * t603 - 0.6e1 * t399 * t381 - 0.7e1 * t390 * t588 - 0.4e1 * t311
  t631 = t554 * t132
  t632 = t129 * t631
  t638 = t130 * t558
  t644 = t129 * t638
  t665 = t385 * t234
  t676 = t385 * t145
  t681 = 0.11e2 * t399 * t616 * t579 * t233 - 0.6e1 * t399 * t616 * t579 * t386 - 0.6e1 * t379 * t405 + 0.6e1 * t379 * t665 + 0.6e1 * t384 * t665 + 0.11e2 * t384 * t676 + 0.7e1 * t390 * t603 - 0.18e2 * t390 * t665 - 0.11e2 * t390 * t676 - 0.12e2 * t399 * t402 - 0.7e1 * t399 * t588
  t685 = f.my_piecewise5(t58, 0, t61, 0, -t150 + 0.4e1 * t244 - 0.3e1 * t213 - 0.4e1 * t295 + 0.4e1 * t285 + 0.4e1 * t266 + t452 + 0.14e2 * t93 * t522 * t134 * t101 * params.csk_a * t148 * t152 + t398 * t358 * t363 * t577 * t579 + t544 + 0.3e1 * t129 * t554 * t140 + 0.3e1 * t131 * t559 * t139 + 0.3e1 * t156 * t559 * t101 + 0.3e1 * t93 * t554 * t157 - 0.18e2 * t462 * t227 * t264 - 0.18e2 * t424 * t227 * t270 + 0.4e1 * t93 * t442 * t249 + 0.3e1 * t93 * t638 * t146 + 0.3e1 * t93 * t631 * t146 - 0.6e1 * t482 * t484 + 0.18e2 * t424 * t484 + 0.7e1 * t399 * t410 - 0.3e1 * t632 * t146 - 0.3e1 * t632 * t163 - 0.3e1 * t644 * t163 - 0.3e1 * t644 * t146 - 0.6e1 * t475 * t477 + 0.18e2 * t462 * t477 - 0.4e1 * t443 * t305 - 0.12e2 * t379 * t381 + t384 * t388 - 0.7e1 * t390 * t388 + 0.6e1 * t379 * t388 - 0.3e1 * t149 * t218 + t681 + 0.11e2 * t129 * t358 * t363 * t139 + 0.6e1 * t93 * t358 * t363 * t101 - 0.12e2 * t455 * t257 * t258 * t132 + 0.18e2 * t462 * t227 * t409 * t148 - 0.18e2 * t437 * t227 * t409 * t130 - 0.18e2 * t455 * t227 * t409 * t132 - t95 * t572 * t98 * t101 + 0.6e1 * t205 * t358 * t363 * t210 + t621)
  t692 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 / t22 / t80 * t73 + 0.8e1 / 0.45e2 * t7 * t25 * t106 - t7 * t79 * t168 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t111 * t317 + 0.3e1 / 0.20e2 * t7 * t172 * (0.4e1 * t184 * t104 + 0.6e1 * t123 * t166 + 0.4e1 * t91 * t315 + t350 * t71 + t53 * t685 + t344))
  v4rho4_0_ = 0.2e1 * r0 * t692 + 0.8e1 * t322

  res = {'v4rho4': v4rho4_0_}
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
  t48 = 0.5e1 / 0.72e2 * t40 * s0 * t45
  t49 = params.csk_cp * t35
  t50 = t39 * s0
  t54 = params.csk_cq * t35
  t55 = t39 * l0
  t61 = t49 * t50 * t45 / 0.24e2 + t54 * t55 / t43 / r0 / 0.24e2 - t48
  t63 = jnp.log(0.1e1 - DBL_EPSILON)
  t64 = 0.1e1 / params.csk_a
  t65 = (-t63) ** (-t64)
  t66 = t61 < -t65
  t67 = jnp.log(DBL_EPSILON)
  t68 = (-t67) ** (-t64)
  t69 = -t68 < t61
  t70 = f.my_piecewise3(t69, -t68, t61)
  t71 = -t65 < t70
  t72 = f.my_piecewise3(t71, t70, -t65)
  t73 = abs(t72)
  t74 = t73 ** params.csk_a
  t75 = 0.1e1 / t74
  t76 = jnp.exp(-t75)
  t77 = 0.1e1 - t76
  t78 = t77 ** t64
  t79 = f.my_piecewise5(t66, 0, t69, 1, t78)
  t81 = t61 * t79 + t48 + 0.1e1
  t85 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t86 = t85 ** 2
  t87 = t86 * f.p.zeta_threshold
  t89 = f.my_piecewise3(t21, t87, t23 * t20)
  t90 = 0.1e1 / t32
  t91 = t89 * t90
  t94 = t6 * t91 * t81 / 0.10e2
  t95 = t89 * t33
  t98 = 0.1e1 / t43 / t41 / r0
  t101 = 0.5e1 / 0.27e2 * t40 * s0 * t98
  t108 = -t49 * t50 * t98 / 0.9e1 - 0.5e1 / 0.72e2 * t54 * t55 * t45 + t101
  t110 = t78 * t75
  t111 = jnp.abs(1 - t72)
  t112 = t110 * t111
  t113 = f.my_piecewise3(t69, 0, t108)
  t114 = f.my_piecewise3(t71, t113, 0)
  t115 = 0.1e1 / t73
  t117 = 0.1e1 / t77
  t118 = t76 * t117
  t119 = t114 * t115 * t118
  t121 = f.my_piecewise5(t66, 0, t69, 0, -t112 * t119)
  t123 = t108 * t79 + t61 * t121 - t101
  t128 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t81 + t94 + 0.3e1 / 0.20e2 * t6 * t95 * t123)
  t130 = r1 <= f.p.dens_threshold
  t131 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t132 = 0.1e1 + t131
  t133 = t132 <= f.p.zeta_threshold
  t134 = t132 ** (0.1e1 / 0.3e1)
  t135 = t134 ** 2
  t137 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t140 = f.my_piecewise3(t133, 0, 0.5e1 / 0.3e1 * t135 * t137)
  t141 = t140 * t33
  t142 = r1 ** 2
  t143 = r1 ** (0.1e1 / 0.3e1)
  t144 = t143 ** 2
  t146 = 0.1e1 / t144 / t142
  t149 = 0.5e1 / 0.72e2 * t40 * s2 * t146
  t150 = t39 * s2
  t154 = t39 * l1
  t160 = t49 * t150 * t146 / 0.24e2 + t54 * t154 / t144 / r1 / 0.24e2 - t149
  t161 = t160 < -t65
  t162 = -t68 < t160
  t163 = f.my_piecewise3(t162, -t68, t160)
  t164 = -t65 < t163
  t165 = f.my_piecewise3(t164, t163, -t65)
  t166 = abs(t165)
  t167 = t166 ** params.csk_a
  t168 = 0.1e1 / t167
  t169 = jnp.exp(-t168)
  t170 = 0.1e1 - t169
  t171 = t170 ** t64
  t172 = f.my_piecewise5(t161, 0, t162, 1, t171)
  t174 = t160 * t172 + t149 + 0.1e1
  t179 = f.my_piecewise3(t133, t87, t135 * t132)
  t180 = t179 * t90
  t183 = t6 * t180 * t174 / 0.10e2
  t185 = f.my_piecewise3(t130, 0, 0.3e1 / 0.20e2 * t6 * t141 * t174 + t183)
  t187 = 0.1e1 / t22
  t188 = t28 ** 2
  t193 = t17 / t24 / t7
  t195 = -0.2e1 * t25 + 0.2e1 * t193
  t196 = f.my_piecewise5(t11, 0, t15, 0, t195)
  t200 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t187 * t188 + 0.5e1 / 0.3e1 * t23 * t196)
  t207 = t6 * t31 * t90 * t81
  t213 = 0.1e1 / t32 / t7
  t217 = t6 * t89 * t213 * t81 / 0.30e2
  t219 = t6 * t91 * t123
  t221 = t41 ** 2
  t223 = 0.1e1 / t43 / t221
  t226 = 0.55e2 / 0.81e2 * t40 * s0 * t223
  t233 = 0.11e2 / 0.27e2 * t49 * t50 * t223 + 0.5e1 / 0.27e2 * t54 * t55 * t98 - t226
  t237 = t74 ** 2
  t239 = t78 / t237
  t240 = t111 ** 2
  t242 = t114 ** 2
  t243 = t73 ** 2
  t244 = 0.1e1 / t243
  t245 = t242 * t244
  t246 = t76 ** 2
  t247 = t77 ** 2
  t248 = 0.1e1 / t247
  t252 = t240 * t242
  t256 = t244 * t76 * t117 * params.csk_a
  t258 = signum(1, t72)
  t261 = f.my_piecewise3(t69, 0, t233)
  t262 = f.my_piecewise3(t71, t261, 0)
  t269 = t239 * t252
  t276 = f.my_piecewise5(t66, 0, t69, 0, t239 * t240 * t245 * t246 * t248 - t269 * t244 * t246 * t248 * params.csk_a + t110 * t240 * t245 * t118 - t112 * t262 * t115 * t118 - t110 * t258 * t119 + t110 * t252 * t256 - t269 * t256)
  t283 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t200 * t33 * t81 + t207 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t123 - t217 + t219 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t95 * (0.2e1 * t108 * t121 + t233 * t79 + t61 * t276 + t226))
  t284 = 0.1e1 / t134
  t285 = t137 ** 2
  t289 = f.my_piecewise5(t15, 0, t11, 0, -t195)
  t293 = f.my_piecewise3(t133, 0, 0.10e2 / 0.9e1 * t284 * t285 + 0.5e1 / 0.3e1 * t135 * t289)
  t300 = t6 * t140 * t90 * t174
  t305 = t6 * t179 * t213 * t174 / 0.30e2
  t307 = f.my_piecewise3(t130, 0, 0.3e1 / 0.20e2 * t6 * t293 * t33 * t174 + t300 / 0.5e1 - t305)
  d11 = 0.2e1 * t128 + 0.2e1 * t185 + t7 * (t283 + t307)
  t310 = -t8 - t26
  t311 = f.my_piecewise5(t11, 0, t15, 0, t310)
  t314 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t311)
  t315 = t314 * t33
  t320 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t315 * t81 + t94)
  t322 = f.my_piecewise5(t15, 0, t11, 0, -t310)
  t325 = f.my_piecewise3(t133, 0, 0.5e1 / 0.3e1 * t135 * t322)
  t326 = t325 * t33
  t330 = t179 * t33
  t333 = 0.1e1 / t144 / t142 / r1
  t336 = 0.5e1 / 0.27e2 * t40 * s2 * t333
  t343 = -t49 * t150 * t333 / 0.9e1 - 0.5e1 / 0.72e2 * t54 * t154 * t146 + t336
  t345 = t171 * t168
  t346 = jnp.abs(1 - t165)
  t347 = t345 * t346
  t348 = f.my_piecewise3(t162, 0, t343)
  t349 = f.my_piecewise3(t164, t348, 0)
  t350 = 0.1e1 / t166
  t352 = 0.1e1 / t170
  t353 = t169 * t352
  t354 = t349 * t350 * t353
  t356 = f.my_piecewise5(t161, 0, t162, 0, -t347 * t354)
  t358 = t160 * t356 + t343 * t172 - t336
  t363 = f.my_piecewise3(t130, 0, 0.3e1 / 0.20e2 * t6 * t326 * t174 + t183 + 0.3e1 / 0.20e2 * t6 * t330 * t358)
  t367 = 0.2e1 * t193
  t368 = f.my_piecewise5(t11, 0, t15, 0, t367)
  t372 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t187 * t311 * t28 + 0.5e1 / 0.3e1 * t23 * t368)
  t379 = t6 * t314 * t90 * t81
  t387 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t372 * t33 * t81 + t379 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t315 * t123 + t207 / 0.10e2 - t217 + t219 / 0.10e2)
  t391 = f.my_piecewise5(t15, 0, t11, 0, -t367)
  t395 = f.my_piecewise3(t133, 0, 0.10e2 / 0.9e1 * t284 * t322 * t137 + 0.5e1 / 0.3e1 * t135 * t391)
  t402 = t6 * t325 * t90 * t174
  t409 = t6 * t180 * t358
  t412 = f.my_piecewise3(t130, 0, 0.3e1 / 0.20e2 * t6 * t395 * t33 * t174 + t402 / 0.10e2 + t300 / 0.10e2 - t305 + 0.3e1 / 0.20e2 * t6 * t141 * t358 + t409 / 0.10e2)
  d12 = t128 + t185 + t320 + t363 + t7 * (t387 + t412)
  t417 = t311 ** 2
  t421 = 0.2e1 * t25 + 0.2e1 * t193
  t422 = f.my_piecewise5(t11, 0, t15, 0, t421)
  t426 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t187 * t417 + 0.5e1 / 0.3e1 * t23 * t422)
  t433 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t426 * t33 * t81 + t379 / 0.5e1 - t217)
  t434 = t322 ** 2
  t438 = f.my_piecewise5(t15, 0, t11, 0, -t421)
  t442 = f.my_piecewise3(t133, 0, 0.10e2 / 0.9e1 * t284 * t434 + 0.5e1 / 0.3e1 * t135 * t438)
  t452 = t142 ** 2
  t454 = 0.1e1 / t144 / t452
  t457 = 0.55e2 / 0.81e2 * t40 * s2 * t454
  t464 = 0.11e2 / 0.27e2 * t49 * t150 * t454 + 0.5e1 / 0.27e2 * t54 * t154 * t333 - t457
  t468 = t167 ** 2
  t470 = t171 / t468
  t471 = t346 ** 2
  t473 = t349 ** 2
  t474 = t166 ** 2
  t475 = 0.1e1 / t474
  t476 = t473 * t475
  t477 = t169 ** 2
  t478 = t170 ** 2
  t479 = 0.1e1 / t478
  t483 = t471 * t473
  t487 = t475 * t169 * t352 * params.csk_a
  t489 = signum(1, t165)
  t492 = f.my_piecewise3(t162, 0, t464)
  t493 = f.my_piecewise3(t164, t492, 0)
  t500 = t470 * t483
  t507 = f.my_piecewise5(t161, 0, t162, 0, t470 * t471 * t476 * t477 * t479 - t500 * t475 * t477 * t479 * params.csk_a + t345 * t471 * t476 * t353 - t347 * t493 * t350 * t353 - t345 * t489 * t354 + t345 * t483 * t487 - t500 * t487)
  t514 = f.my_piecewise3(t130, 0, 0.3e1 / 0.20e2 * t6 * t442 * t33 * t174 + t402 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t326 * t358 - t305 + t409 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t330 * (t160 * t507 + t464 * t172 + 0.2e1 * t343 * t356 + t457))
  d22 = 0.2e1 * t320 + 0.2e1 * t363 + t7 * (t433 + t514)
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
  t59 = 0.5e1 / 0.72e2 * t51 * s0 * t56
  t60 = params.csk_cp * t46
  t61 = t50 * s0
  t65 = params.csk_cq * t46
  t66 = t50 * l0
  t72 = t60 * t61 * t56 / 0.24e2 + t65 * t66 / t54 / r0 / 0.24e2 - t59
  t74 = jnp.log(0.1e1 - DBL_EPSILON)
  t75 = 0.1e1 / params.csk_a
  t76 = (-t74) ** (-t75)
  t77 = t72 < -t76
  t78 = jnp.log(DBL_EPSILON)
  t79 = (-t78) ** (-t75)
  t80 = -t79 < t72
  t81 = f.my_piecewise3(t80, -t79, t72)
  t82 = -t76 < t81
  t83 = f.my_piecewise3(t82, t81, -t76)
  t84 = abs(t83)
  t85 = t84 ** params.csk_a
  t86 = 0.1e1 / t85
  t87 = jnp.exp(-t86)
  t88 = 0.1e1 - t87
  t89 = t88 ** t75
  t90 = f.my_piecewise5(t77, 0, t80, 1, t89)
  t92 = t72 * t90 + t59 + 0.1e1
  t98 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t99 = 0.1e1 / t43
  t100 = t98 * t99
  t104 = t98 * t44
  t107 = 0.1e1 / t54 / t52 / r0
  t110 = 0.5e1 / 0.27e2 * t51 * s0 * t107
  t117 = -t60 * t61 * t107 / 0.9e1 - 0.5e1 / 0.72e2 * t65 * t66 * t56 + t110
  t119 = t89 * t86
  t120 = abs(1, t83)
  t121 = t119 * t120
  t122 = f.my_piecewise3(t80, 0, t117)
  t123 = f.my_piecewise3(t82, t122, 0)
  t124 = 0.1e1 / t84
  t126 = 0.1e1 / t88
  t127 = t87 * t126
  t128 = t123 * t124 * t127
  t130 = f.my_piecewise5(t77, 0, t80, 0, -t121 * t128)
  t132 = t117 * t90 + t72 * t130 - t110
  t136 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t137 = t136 ** 2
  t138 = t137 * f.p.zeta_threshold
  t140 = f.my_piecewise3(t21, t138, t32 * t20)
  t142 = 0.1e1 / t43 / t7
  t143 = t140 * t142
  t147 = t140 * t99
  t151 = t140 * t44
  t152 = t52 ** 2
  t154 = 0.1e1 / t54 / t152
  t157 = 0.55e2 / 0.81e2 * t51 * s0 * t154
  t164 = 0.11e2 / 0.27e2 * t60 * t61 * t154 + 0.5e1 / 0.27e2 * t65 * t66 * t107 - t157
  t168 = t85 ** 2
  t170 = t89 / t168
  t171 = t120 ** 2
  t173 = t123 ** 2
  t174 = t84 ** 2
  t175 = 0.1e1 / t174
  t176 = t173 * t175
  t177 = t87 ** 2
  t178 = t88 ** 2
  t179 = 0.1e1 / t178
  t180 = t177 * t179
  t183 = t171 * t173
  t185 = t175 * t87
  t186 = t126 * params.csk_a
  t187 = t185 * t186
  t189 = signum(1, t83)
  t190 = t119 * t189
  t191 = t190 * t128
  t192 = f.my_piecewise3(t80, 0, t164)
  t193 = f.my_piecewise3(t82, t192, 0)
  t195 = t193 * t124 * t127
  t200 = t170 * t183
  t202 = t175 * t177
  t203 = t179 * params.csk_a
  t207 = f.my_piecewise5(t77, 0, t80, 0, t119 * t171 * t176 * t127 + t170 * t171 * t176 * t180 + t119 * t183 * t187 - t200 * t202 * t203 - t121 * t195 - t200 * t187 - t191)
  t209 = 0.2e1 * t117 * t130 + t164 * t90 + t72 * t207 + t157
  t214 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t92 + t6 * t100 * t92 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t104 * t132 - t6 * t143 * t92 / 0.30e2 + t6 * t147 * t132 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t151 * t209)
  t216 = r1 <= f.p.dens_threshold
  t217 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t218 = 0.1e1 + t217
  t219 = t218 <= f.p.zeta_threshold
  t220 = t218 ** (0.1e1 / 0.3e1)
  t221 = 0.1e1 / t220
  t223 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t224 = t223 ** 2
  t227 = t220 ** 2
  t229 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t233 = f.my_piecewise3(t219, 0, 0.10e2 / 0.9e1 * t221 * t224 + 0.5e1 / 0.3e1 * t227 * t229)
  t235 = r1 ** 2
  t236 = r1 ** (0.1e1 / 0.3e1)
  t237 = t236 ** 2
  t239 = 0.1e1 / t237 / t235
  t242 = 0.5e1 / 0.72e2 * t51 * s2 * t239
  t253 = t60 * t50 * s2 * t239 / 0.24e2 + t65 * t50 * l1 / t237 / r1 / 0.24e2 - t242
  t255 = -t79 < t253
  t256 = f.my_piecewise3(t255, -t79, t253)
  t258 = f.my_piecewise3(-t76 < t256, t256, -t76)
  t259 = abs(t258)
  t260 = t259 ** params.csk_a
  t262 = jnp.exp(-0.1e1 / t260)
  t264 = (0.1e1 - t262) ** t75
  t265 = f.my_piecewise5(t253 < -t76, 0, t255, 1, t264)
  t267 = t253 * t265 + t242 + 0.1e1
  t273 = f.my_piecewise3(t219, 0, 0.5e1 / 0.3e1 * t227 * t223)
  t279 = f.my_piecewise3(t219, t138, t227 * t218)
  t285 = f.my_piecewise3(t216, 0, 0.3e1 / 0.20e2 * t6 * t233 * t44 * t267 + t6 * t273 * t99 * t267 / 0.5e1 - t6 * t279 * t142 * t267 / 0.30e2)
  t295 = t24 ** 2
  t299 = 0.6e1 * t34 - 0.6e1 * t17 / t295
  t300 = f.my_piecewise5(t11, 0, t15, 0, t299)
  t304 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t300)
  t327 = 0.1e1 / t43 / t24
  t340 = 0.1e1 / t54 / t152 / r0
  t343 = 0.770e3 / 0.243e3 * t51 * s0 * t340
  t350 = -0.154e3 / 0.81e2 * t60 * t61 * t340 - 0.55e2 / 0.81e2 * t65 * t66 * t154 + t343
  t356 = t189 * t173
  t357 = t170 * t356
  t358 = t175 * params.csk_a
  t364 = t171 * t193
  t365 = t170 * t364
  t371 = t120 * t173
  t377 = t171 * t123
  t391 = t171 * t120
  t393 = t173 * t123
  t395 = 0.1e1 / t174 / t84
  t396 = t393 * t395
  t406 = t89 / t168 / t85
  t408 = t177 * t87
  t410 = 0.1e1 / t178 / t88
  t416 = f.my_piecewise3(t80, 0, t350)
  t417 = f.my_piecewise3(t82, t416, 0)
  t426 = -0.3e1 * t357 * t358 * t120 * t87 * t126 - 0.3e1 * t365 * t358 * t123 * t87 * t126 + 0.3e1 * t119 * t371 * t185 * t186 * t189 + 0.3e1 * t119 * t377 * t185 * t186 * t193 - 0.3e1 * t357 * t202 * t203 * t120 - 0.3e1 * t365 * t202 * t203 * t123 - t191 - 0.3e1 * t170 * t391 * t396 * t180 - 0.2e1 * t119 * t391 * t396 * t127 - t406 * t391 * t396 * t408 * t410 - 0.2e1 * t190 * t195 - t121 * t417 * t124 * t127 + 0.3e1 * t119 * t356 * t185 * t126 * t120
  t432 = t391 * t393
  t433 = t406 * t432
  t438 = t119 * t432
  t440 = params.csk_a ** 2
  t442 = t395 * t87 * t126 * t440
  t444 = t170 * t432
  t454 = t395 * params.csk_a * t127
  t458 = t395 * t440 * t180
  t461 = t395 * t408
  t479 = 0.3e1 * t119 * t364 * t185 * t126 * t123 + 0.3e1 * t170 * t371 * t202 * t179 * t189 + 0.3e1 * t170 * t377 * t202 * t179 * t193 + 0.3e1 * t433 * t395 * t177 * t203 - 0.2e1 * t433 * t461 * t410 * t440 + 0.3e1 * t433 * t461 * t410 * params.csk_a - t433 * t442 - 0.3e1 * t433 * t458 - t438 * t442 - 0.3e1 * t438 * t454 + 0.3e1 * t444 * t442 + 0.3e1 * t444 * t454 + 0.3e1 * t444 * t458
  t481 = f.my_piecewise5(t77, 0, t80, 0, t426 + t479)
  t488 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t304 * t44 * t92 + 0.3e1 / 0.10e2 * t6 * t42 * t99 * t92 + 0.9e1 / 0.20e2 * t6 * t45 * t132 - t6 * t98 * t142 * t92 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t100 * t132 + 0.9e1 / 0.20e2 * t6 * t104 * t209 + 0.2e1 / 0.45e2 * t6 * t140 * t327 * t92 - t6 * t143 * t132 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t147 * t209 + 0.3e1 / 0.20e2 * t6 * t151 * (0.3e1 * t117 * t207 + 0.3e1 * t164 * t130 + t350 * t90 + t72 * t481 - t343))
  t498 = f.my_piecewise5(t15, 0, t11, 0, -t299)
  t502 = f.my_piecewise3(t219, 0, -0.10e2 / 0.27e2 / t220 / t218 * t224 * t223 + 0.10e2 / 0.3e1 * t221 * t223 * t229 + 0.5e1 / 0.3e1 * t227 * t498)
  t520 = f.my_piecewise3(t216, 0, 0.3e1 / 0.20e2 * t6 * t502 * t44 * t267 + 0.3e1 / 0.10e2 * t6 * t233 * t99 * t267 - t6 * t273 * t142 * t267 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t279 * t327 * t267)
  d111 = 0.3e1 * t214 + 0.3e1 * t285 + t7 * (t488 + t520)

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
  t24 = 0.1e1 / t22 / t20
  t25 = t7 ** 2
  t26 = 0.1e1 / t25
  t28 = -t17 * t26 + t8
  t29 = f.my_piecewise5(t11, 0, t15, 0, t28)
  t30 = t29 ** 2
  t34 = 0.1e1 / t22
  t35 = t34 * t29
  t36 = t25 * t7
  t37 = 0.1e1 / t36
  t40 = 0.2e1 * t17 * t37 - 0.2e1 * t26
  t41 = f.my_piecewise5(t11, 0, t15, 0, t40)
  t44 = t22 ** 2
  t45 = t25 ** 2
  t46 = 0.1e1 / t45
  t49 = -0.6e1 * t17 * t46 + 0.6e1 * t37
  t50 = f.my_piecewise5(t11, 0, t15, 0, t49)
  t54 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 * t24 * t30 * t29 + 0.10e2 / 0.3e1 * t35 * t41 + 0.5e1 / 0.3e1 * t44 * t50)
  t55 = t7 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = t54 * t56
  t58 = 6 ** (0.1e1 / 0.3e1)
  t59 = jnp.pi ** 2
  t60 = t59 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t62 = 0.1e1 / t61
  t63 = t58 * t62
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t71 = 0.5e1 / 0.72e2 * t63 * s0 * t68
  t72 = params.csk_cp * t58
  t73 = t62 * s0
  t77 = params.csk_cq * t58
  t78 = t62 * l0
  t84 = t72 * t73 * t68 / 0.24e2 + t77 * t78 / t66 / r0 / 0.24e2 - t71
  t86 = jnp.log(0.1e1 - DBL_EPSILON)
  t87 = 0.1e1 / params.csk_a
  t88 = (-t86) ** (-t87)
  t89 = t84 < -t88
  t90 = jnp.log(DBL_EPSILON)
  t91 = (-t90) ** (-t87)
  t92 = -t91 < t84
  t93 = f.my_piecewise3(t92, -t91, t84)
  t94 = -t88 < t93
  t95 = f.my_piecewise3(t94, t93, -t88)
  t96 = abs(t95)
  t97 = t96 ** params.csk_a
  t98 = 0.1e1 / t97
  t99 = jnp.exp(-t98)
  t100 = 0.1e1 - t99
  t101 = t100 ** t87
  t102 = f.my_piecewise5(t89, 0, t92, 1, t101)
  t104 = t84 * t102 + t71 + 0.1e1
  t113 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t114 = 0.1e1 / t55
  t115 = t113 * t114
  t119 = t113 * t56
  t122 = 0.1e1 / t66 / t64 / r0
  t125 = 0.5e1 / 0.27e2 * t63 * s0 * t122
  t132 = -t72 * t73 * t122 / 0.9e1 - 0.5e1 / 0.72e2 * t77 * t78 * t68 + t125
  t134 = t101 * t98
  t135 = abs(1, t95)
  t136 = t134 * t135
  t137 = f.my_piecewise3(t92, 0, t132)
  t138 = f.my_piecewise3(t94, t137, 0)
  t139 = 0.1e1 / t96
  t141 = 0.1e1 / t100
  t142 = t99 * t141
  t143 = t138 * t139 * t142
  t145 = f.my_piecewise5(t89, 0, t92, 0, -t136 * t143)
  t147 = t132 * t102 + t84 * t145 - t125
  t153 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t155 = 0.1e1 / t55 / t7
  t156 = t153 * t155
  t160 = t153 * t114
  t164 = t153 * t56
  t165 = t64 ** 2
  t167 = 0.1e1 / t66 / t165
  t170 = 0.55e2 / 0.81e2 * t63 * s0 * t167
  t177 = 0.11e2 / 0.27e2 * t72 * t73 * t167 + 0.5e1 / 0.27e2 * t77 * t78 * t122 - t170
  t181 = t97 ** 2
  t183 = t101 / t181
  t184 = t135 ** 2
  t185 = t183 * t184
  t186 = t138 ** 2
  t187 = t96 ** 2
  t188 = 0.1e1 / t187
  t189 = t186 * t188
  t190 = t99 ** 2
  t191 = t100 ** 2
  t192 = 0.1e1 / t191
  t193 = t190 * t192
  t194 = t189 * t193
  t196 = t184 * t186
  t198 = t188 * t99
  t199 = t141 * params.csk_a
  t200 = t198 * t199
  t202 = signum(1, t95)
  t203 = t134 * t202
  t204 = t203 * t143
  t205 = f.my_piecewise3(t92, 0, t177)
  t206 = f.my_piecewise3(t94, t205, 0)
  t208 = t206 * t139 * t142
  t210 = t134 * t184
  t211 = t189 * t142
  t213 = t183 * t196
  t215 = t188 * t190
  t216 = t192 * params.csk_a
  t217 = t215 * t216
  t220 = f.my_piecewise5(t89, 0, t92, 0, t134 * t196 * t200 - t136 * t208 + t185 * t194 - t213 * t200 + t210 * t211 - t213 * t217 - t204)
  t222 = t177 * t102 + 0.2e1 * t132 * t145 + t84 * t220 + t170
  t226 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t227 = t226 ** 2
  t228 = t227 * f.p.zeta_threshold
  t230 = f.my_piecewise3(t21, t228, t44 * t20)
  t232 = 0.1e1 / t55 / t25
  t233 = t230 * t232
  t237 = t230 * t155
  t241 = t230 * t114
  t245 = t230 * t56
  t248 = 0.1e1 / t66 / t165 / r0
  t251 = 0.770e3 / 0.243e3 * t63 * s0 * t248
  t258 = -0.154e3 / 0.81e2 * t72 * t73 * t248 - 0.55e2 / 0.81e2 * t77 * t78 * t167 + t251
  t264 = t184 * t135
  t266 = t186 * t138
  t268 = 0.1e1 / t187 / t96
  t269 = t266 * t268
  t277 = t135 * t186
  t279 = t199 * t202
  t281 = t134 * t277 * t198 * t279
  t283 = t184 * t138
  t284 = t134 * t283
  t285 = t199 * t206
  t289 = t202 * t186
  t290 = t183 * t289
  t293 = t290 * t215 * t216 * t135
  t295 = t184 * t206
  t296 = t183 * t295
  t298 = t215 * t216 * t138
  t301 = t188 * params.csk_a
  t305 = t290 * t301 * t135 * t99 * t141
  t307 = t264 * t266
  t308 = t134 * t307
  t309 = t268 * t99
  t310 = t309 * t199
  t313 = t183 * t307
  t318 = t101 / t181 / t97
  t319 = t318 * t307
  t320 = params.csk_a ** 2
  t321 = t268 * t320
  t322 = t321 * t193
  t325 = t190 * t99
  t326 = t268 * t325
  t328 = 0.1e1 / t191 / t100
  t329 = t328 * t320
  t333 = t328 * params.csk_a
  t339 = -0.2e1 * t134 * t264 * t269 * t142 - 0.3e1 * t183 * t264 * t269 * t193 + 0.3e1 * t284 * t198 * t285 - 0.2e1 * t319 * t326 * t329 + 0.3e1 * t319 * t326 * t333 - 0.3e1 * t296 * t298 - 0.3e1 * t308 * t310 + 0.3e1 * t313 * t310 + 0.3e1 * t313 * t322 - 0.3e1 * t319 * t322 + 0.3e1 * t281 - 0.3e1 * t293 - 0.3e1 * t305
  t341 = t192 * t202
  t343 = t183 * t277 * t215 * t341
  t345 = t183 * t283
  t346 = t192 * t206
  t350 = t268 * t190
  t355 = t309 * t141 * t320
  t361 = t141 * t135
  t363 = t134 * t289 * t198 * t361
  t367 = t198 * t141 * t138
  t371 = t325 * t328
  t374 = t203 * t208
  t376 = f.my_piecewise3(t92, 0, t258)
  t377 = f.my_piecewise3(t94, t376, 0)
  t379 = t377 * t139 * t142
  t383 = t301 * t138 * t99 * t141
  t386 = -t318 * t264 * t269 * t371 + 0.3e1 * t134 * t295 * t367 + 0.3e1 * t345 * t215 * t346 + 0.3e1 * t319 * t350 * t216 - t136 * t379 - 0.3e1 * t296 * t383 - t308 * t355 + 0.3e1 * t313 * t355 - t319 * t355 - t204 + 0.3e1 * t343 + 0.3e1 * t363 - 0.2e1 * t374
  t388 = f.my_piecewise5(t89, 0, t92, 0, t339 + t386)
  t390 = t258 * t102 + 0.3e1 * t132 * t220 + 0.3e1 * t177 * t145 + t84 * t388 - t251
  t395 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t104 + 0.3e1 / 0.10e2 * t6 * t115 * t104 + 0.9e1 / 0.20e2 * t6 * t119 * t147 - t6 * t156 * t104 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t160 * t147 + 0.9e1 / 0.20e2 * t6 * t164 * t222 + 0.2e1 / 0.45e2 * t6 * t233 * t104 - t6 * t237 * t147 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t241 * t222 + 0.3e1 / 0.20e2 * t6 * t245 * t390)
  t397 = r1 <= f.p.dens_threshold
  t398 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t399 = 0.1e1 + t398
  t400 = t399 <= f.p.zeta_threshold
  t401 = t399 ** (0.1e1 / 0.3e1)
  t403 = 0.1e1 / t401 / t399
  t405 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t406 = t405 ** 2
  t410 = 0.1e1 / t401
  t411 = t410 * t405
  t413 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t416 = t401 ** 2
  t418 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t422 = f.my_piecewise3(t400, 0, -0.10e2 / 0.27e2 * t403 * t406 * t405 + 0.10e2 / 0.3e1 * t411 * t413 + 0.5e1 / 0.3e1 * t416 * t418)
  t424 = r1 ** 2
  t425 = r1 ** (0.1e1 / 0.3e1)
  t426 = t425 ** 2
  t428 = 0.1e1 / t426 / t424
  t431 = 0.5e1 / 0.72e2 * t63 * s2 * t428
  t442 = t72 * t62 * s2 * t428 / 0.24e2 + t77 * t62 * l1 / t426 / r1 / 0.24e2 - t431
  t444 = -t91 < t442
  t445 = f.my_piecewise3(t444, -t91, t442)
  t447 = f.my_piecewise3(-t88 < t445, t445, -t88)
  t448 = abs(t447)
  t449 = t448 ** params.csk_a
  t451 = jnp.exp(-0.1e1 / t449)
  t453 = (0.1e1 - t451) ** t87
  t454 = f.my_piecewise5(t442 < -t88, 0, t444, 1, t453)
  t456 = t442 * t454 + t431 + 0.1e1
  t465 = f.my_piecewise3(t400, 0, 0.10e2 / 0.9e1 * t410 * t406 + 0.5e1 / 0.3e1 * t416 * t413)
  t472 = f.my_piecewise3(t400, 0, 0.5e1 / 0.3e1 * t416 * t405)
  t478 = f.my_piecewise3(t400, t228, t416 * t399)
  t484 = f.my_piecewise3(t397, 0, 0.3e1 / 0.20e2 * t6 * t422 * t56 * t456 + 0.3e1 / 0.10e2 * t6 * t465 * t114 * t456 - t6 * t472 * t155 * t456 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t478 * t232 * t456)
  t491 = 0.1e1 / t55 / t36
  t504 = t20 ** 2
  t507 = t30 ** 2
  t513 = t41 ** 2
  t522 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t523 = f.my_piecewise5(t11, 0, t15, 0, t522)
  t527 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t504 * t507 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t513 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t523)
  t561 = 0.1e1 / t66 / t165 / t64
  t564 = 0.13090e5 / 0.729e3 * t63 * s0 * t561
  t571 = 0.2618e4 / 0.243e3 * t72 * t73 * t561 + 0.770e3 / 0.243e3 * t77 * t78 * t248 - t564
  t579 = f.my_piecewise3(t92, 0, t571)
  t580 = f.my_piecewise3(t94, t579, 0)
  t584 = t181 ** 2
  t586 = t101 / t584
  t587 = t184 ** 2
  t589 = t186 ** 2
  t590 = t187 ** 2
  t591 = 0.1e1 / t590
  t592 = t589 * t591
  t593 = t190 ** 2
  t594 = t191 ** 2
  t595 = 0.1e1 / t594
  t601 = t202 ** 2
  t608 = t206 ** 2
  t609 = t608 * t188
  t635 = t587 * t589
  t636 = t318 * t635
  t637 = t591 * t325
  t638 = t637 * t333
  t641 = t591 * t190
  t642 = t641 * t216
  t645 = t264 * t186
  t646 = t183 * t645
  t650 = t183 * t635
  t652 = t591 * params.csk_a * t142
  t656 = t591 * t320 * t142
  t661 = t134 * t635
  t663 = t320 * params.csk_a
  t665 = t591 * t99 * t141 * t663
  t671 = t586 * t635
  t673 = -0.12e2 * t134 * t264 * t206 * t309 * t141 * t186 - 0.18e2 * t646 * t350 * t346 - 0.12e2 * t636 * t638 - 0.18e2 * t636 * t642 + 0.6e1 * t636 * t656 + 0.6e1 * t636 * t665 - 0.11e2 * t650 * t652 - 0.18e2 * t650 * t656 - 0.7e1 * t650 * t665 + t661 * t665 - t671 * t665
  t676 = t637 * t328 * t663
  t679 = t184 * t266
  t680 = t318 * t679
  t687 = t183 * t679
  t691 = t184 * t377
  t695 = t192 * t320
  t696 = t641 * t695
  t705 = t601 * t186
  t709 = t184 * t608
  t713 = t637 * t329
  t723 = t641 * t192 * t663
  t730 = t591 * t593
  t739 = -0.6e1 * t671 * t730 * t595 * t663 - 0.6e1 * t671 * t730 * t595 * params.csk_a + 0.3e1 * t134 * t705 * t200 + 0.3e1 * t134 * t709 * t200 - 0.6e1 * t636 * t713 + 0.18e2 * t636 * t723 - 0.7e1 * t650 * t723 - 0.12e2 * t671 * t676 + 0.7e1 * t671 * t696 + 0.18e2 * t671 * t713 - 0.7e1 * t671 * t723
  t752 = t318 * t645
  t757 = t183 * t709
  t760 = t183 * t705
  t778 = t135 * t138
  t786 = t202 * t138
  t788 = t183 * t786 * t188
  t789 = params.csk_a * t135
  t794 = t142 * t206
  t800 = t321 * t142 * t202
  t803 = t321 * t794
  t814 = 0.14e2 * t134 * t778 * t188 * t142 * params.csk_a * t202 * t206 - 0.14e2 * t788 * t193 * t789 * t206 - 0.12e2 * t680 * t326 * t329 * t202 - 0.12e2 * t752 * t326 * t329 * t206 - 0.14e2 * t788 * t789 * t794 - 0.6e1 * t680 * t800 - 0.6e1 * t752 * t803 - t204 + 0.4e1 * t343 + 0.4e1 * t363 - 0.3e1 * t374
  t816 = t134 * t679
  t817 = t309 * t279
  t820 = t134 * t645
  t821 = t309 * t285
  t854 = t183 * t691
  t860 = t350 * t695 * t202
  t864 = t350 * t695 * t206
  t884 = 0.14e2 * t134 * t786 * t198 * t361 * t206 + 0.4e1 * t284 * t198 * t199 * t377 + 0.18e2 * t752 * t326 * t333 * t206 - 0.4e1 * t854 * t298 - 0.4e1 * t854 * t383 + 0.18e2 * t646 * t803 + 0.18e2 * t646 * t864 - 0.18e2 * t680 * t860 + 0.18e2 * t687 * t800 + 0.18e2 * t687 * t860 - 0.18e2 * t752 * t864
  t888 = f.my_piecewise5(t89, 0, t92, 0, -0.4e1 * t305 - 0.4e1 * t293 + 0.4e1 * t281 - 0.18e2 * t816 * t817 - 0.18e2 * t820 * t821 - 0.3e1 * t757 * t200 - 0.3e1 * t760 * t217 - 0.3e1 * t757 * t217 - 0.3e1 * t760 * t200 + 0.11e2 * t661 * t652 - 0.6e1 * t671 * t638 - 0.11e2 * t650 * t696 + 0.6e1 * t661 * t656 + 0.12e2 * t636 * t676 + 0.7e1 * t650 * t642 + 0.18e2 * t687 * t817 + 0.18e2 * t646 * t821 - 0.6e1 * t816 * t800 - 0.6e1 * t820 * t803 - 0.3e1 * t203 * t379 + t673 - 0.18e2 * t687 * t350 * t341 + 0.4e1 * t134 * t691 * t367 + 0.3e1 * t183 * t601 * t194 + 0.3e1 * t134 * t601 * t211 + 0.3e1 * t210 * t609 * t142 + 0.3e1 * t185 * t609 * t193 - t136 * t580 * t139 * t142 + 0.6e1 * t318 * t587 * t592 * t371 + 0.11e2 * t183 * t587 * t592 * t193 + 0.6e1 * t134 * t587 * t592 * t142 - 0.6e1 * t680 * t326 * t328 * t202 + 0.11e2 * t671 * t730 * t595 * t320 + 0.4e1 * t345 * t215 * t192 * t377 - 0.6e1 * t752 * t326 * t328 * t206 + 0.18e2 * t680 * t350 * t216 * t202 + 0.18e2 * t752 * t350 * t216 * t206 + 0.18e2 * t680 * t326 * t333 * t202 + t739 + t814 + t884 + t586 * t587 * t592 * t593 * t595 + 0.14e2 * t183 * t778 * t215 * t346 * t202 - 0.12e2 * t134 * t202 * t266 * t309 * t141 * t184)
  t894 = 0.8e1 / 0.45e2 * t6 * t153 * t232 * t104 - 0.14e2 / 0.135e3 * t6 * t230 * t491 * t104 + 0.2e1 / 0.5e1 * t6 * t54 * t114 * t104 - t6 * t113 * t155 * t104 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t527 * t56 * t104 + 0.3e1 / 0.5e1 * t6 * t57 * t147 + 0.6e1 / 0.5e1 * t6 * t115 * t147 + 0.9e1 / 0.10e2 * t6 * t119 * t222 - 0.2e1 / 0.5e1 * t6 * t156 * t147 + 0.6e1 / 0.5e1 * t6 * t160 * t222 + 0.3e1 / 0.5e1 * t6 * t164 * t390 + 0.8e1 / 0.45e2 * t6 * t233 * t147 - t6 * t237 * t222 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t241 * t390 + 0.3e1 / 0.20e2 * t6 * t245 * (t571 * t102 + 0.4e1 * t132 * t388 + 0.4e1 * t258 * t145 + 0.6e1 * t177 * t220 + t84 * t888 + t564)
  t895 = f.my_piecewise3(t1, 0, t894)
  t896 = t399 ** 2
  t899 = t406 ** 2
  t905 = t413 ** 2
  t911 = f.my_piecewise5(t15, 0, t11, 0, -t522)
  t915 = f.my_piecewise3(t400, 0, 0.40e2 / 0.81e2 / t401 / t896 * t899 - 0.20e2 / 0.9e1 * t403 * t406 * t413 + 0.10e2 / 0.3e1 * t410 * t905 + 0.40e2 / 0.9e1 * t411 * t418 + 0.5e1 / 0.3e1 * t416 * t911)
  t937 = f.my_piecewise3(t397, 0, 0.3e1 / 0.20e2 * t6 * t915 * t56 * t456 + 0.2e1 / 0.5e1 * t6 * t422 * t114 * t456 - t6 * t465 * t155 * t456 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t472 * t232 * t456 - 0.14e2 / 0.135e3 * t6 * t478 * t491 * t456)
  d1111 = 0.4e1 * t395 + 0.4e1 * t484 + t7 * (t895 + t937)

  res = {'v4rho4': d1111}
  return res
