"""Generated from mgga_x_gx.mpl."""

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
  params_alphainf_raw = params.alphainf
  if isinstance(params_alphainf_raw, (str, bytes, dict)):
    params_alphainf = params_alphainf_raw
  else:
    try:
      params_alphainf_seq = list(params_alphainf_raw)
    except TypeError:
      params_alphainf = params_alphainf_raw
    else:
      params_alphainf_seq = np.asarray(params_alphainf_seq, dtype=np.float64)
      params_alphainf = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphainf_seq))
  params_c0_raw = params.c0
  if isinstance(params_c0_raw, (str, bytes, dict)):
    params_c0 = params_c0_raw
  else:
    try:
      params_c0_seq = list(params_c0_raw)
    except TypeError:
      params_c0 = params_c0_raw
    else:
      params_c0_seq = np.asarray(params_c0_seq, dtype=np.float64)
      params_c0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c0_seq))
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

  gx_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  gx_cx0 = 4 / 3 * (2 / jnp.pi) ** (1 / 3)

  gx_cx1 = X_FACTOR_C

  gx_gx1 = lambda a: 1 + (1 - params_alphainf) * (1 - a) / (1 + a)

  gx_gx0 = lambda a: +gx_cx0 / gx_cx1 + a * (params_c0 + params_c1 * a) / (1.0 + (params_c0 + params_c1 - 1) * a) * (1 - gx_cx0 / gx_cx1)

  gx_f_a = lambda a: +gx_gx0(a) * Heaviside(1 - a) + gx_gx1(a) * Heaviside(a - 1)

  gx_f = lambda x, u, t: gx_f_a(gx_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, gx_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_alphainf_raw = params.alphainf
  if isinstance(params_alphainf_raw, (str, bytes, dict)):
    params_alphainf = params_alphainf_raw
  else:
    try:
      params_alphainf_seq = list(params_alphainf_raw)
    except TypeError:
      params_alphainf = params_alphainf_raw
    else:
      params_alphainf_seq = np.asarray(params_alphainf_seq, dtype=np.float64)
      params_alphainf = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphainf_seq))
  params_c0_raw = params.c0
  if isinstance(params_c0_raw, (str, bytes, dict)):
    params_c0 = params_c0_raw
  else:
    try:
      params_c0_seq = list(params_c0_raw)
    except TypeError:
      params_c0 = params_c0_raw
    else:
      params_c0_seq = np.asarray(params_c0_seq, dtype=np.float64)
      params_c0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c0_seq))
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

  gx_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  gx_cx0 = 4 / 3 * (2 / jnp.pi) ** (1 / 3)

  gx_cx1 = X_FACTOR_C

  gx_gx1 = lambda a: 1 + (1 - params_alphainf) * (1 - a) / (1 + a)

  gx_gx0 = lambda a: +gx_cx0 / gx_cx1 + a * (params_c0 + params_c1 * a) / (1.0 + (params_c0 + params_c1 - 1) * a) * (1 - gx_cx0 / gx_cx1)

  gx_f_a = lambda a: +gx_gx0(a) * Heaviside(1 - a) + gx_gx1(a) * Heaviside(a - 1)

  gx_f = lambda x, u, t: gx_f_a(gx_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, gx_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_alphainf_raw = params.alphainf
  if isinstance(params_alphainf_raw, (str, bytes, dict)):
    params_alphainf = params_alphainf_raw
  else:
    try:
      params_alphainf_seq = list(params_alphainf_raw)
    except TypeError:
      params_alphainf = params_alphainf_raw
    else:
      params_alphainf_seq = np.asarray(params_alphainf_seq, dtype=np.float64)
      params_alphainf = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphainf_seq))
  params_c0_raw = params.c0
  if isinstance(params_c0_raw, (str, bytes, dict)):
    params_c0 = params_c0_raw
  else:
    try:
      params_c0_seq = list(params_c0_raw)
    except TypeError:
      params_c0 = params_c0_raw
    else:
      params_c0_seq = np.asarray(params_c0_seq, dtype=np.float64)
      params_c0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c0_seq))
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

  gx_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  gx_cx0 = 4 / 3 * (2 / jnp.pi) ** (1 / 3)

  gx_cx1 = X_FACTOR_C

  gx_gx1 = lambda a: 1 + (1 - params_alphainf) * (1 - a) / (1 + a)

  gx_gx0 = lambda a: +gx_cx0 / gx_cx1 + a * (params_c0 + params_c1 * a) / (1.0 + (params_c0 + params_c1 - 1) * a) * (1 - gx_cx0 / gx_cx1)

  gx_f_a = lambda a: +gx_gx0(a) * Heaviside(1 - a) + gx_gx1(a) * Heaviside(a - 1)

  gx_f = lambda x, u, t: gx_f_a(gx_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, gx_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  Dirac = lambda *args: jnp.zeros_like(args[-1])

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
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t2 ** 2
  t31 = 4 ** (0.1e1 / 0.3e1)
  t33 = 0.8e1 / 0.27e2 * t28 * t29 * t31
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / r0
  t39 = r0 ** 2
  t41 = 0.1e1 / t35 / t39
  t44 = tau0 * t37 - s0 * t41 / 0.8e1
  t45 = 6 ** (0.1e1 / 0.3e1)
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t51 = t44 * t45 * t50
  t53 = t45 * t50
  t56 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t44 * t53
  t57 = params.c0 + params.c1 - 0.1e1
  t61 = 0.10e1 + 0.5e1 / 0.9e1 * t57 * t44 * t53
  t62 = 0.1e1 / t61
  t64 = 0.1e1 - t33
  t65 = t56 * t62 * t64
  t68 = t33 + 0.5e1 / 0.9e1 * t51 * t65
  t69 = 0.5e1 / 0.9e1 * t51
  t70 = 0.1e1 - t69
  t71 = Heaviside(t70)
  t73 = 0.1e1 - params.alphainf
  t74 = t73 * t70
  t75 = 0.1e1 + t69
  t76 = 0.1e1 / t75
  t78 = t74 * t76 + 0.1e1
  t79 = -t70
  t80 = Heaviside(t79)
  t82 = t68 * t71 + t78 * t80
  t86 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t82)
  t87 = r1 <= f.p.dens_threshold
  t88 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t89 = 0.1e1 + t88
  t90 = t89 <= f.p.zeta_threshold
  t91 = t89 ** (0.1e1 / 0.3e1)
  t93 = f.my_piecewise3(t90, t22, t91 * t89)
  t94 = t93 * t26
  t95 = r1 ** (0.1e1 / 0.3e1)
  t96 = t95 ** 2
  t98 = 0.1e1 / t96 / r1
  t100 = r1 ** 2
  t102 = 0.1e1 / t96 / t100
  t105 = tau1 * t98 - s2 * t102 / 0.8e1
  t107 = t105 * t45 * t50
  t111 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t105 * t53
  t115 = 0.10e1 + 0.5e1 / 0.9e1 * t57 * t105 * t53
  t116 = 0.1e1 / t115
  t118 = t111 * t116 * t64
  t121 = t33 + 0.5e1 / 0.9e1 * t107 * t118
  t122 = 0.5e1 / 0.9e1 * t107
  t123 = 0.1e1 - t122
  t124 = Heaviside(t123)
  t126 = t73 * t123
  t127 = 0.1e1 + t122
  t128 = 0.1e1 / t127
  t130 = t126 * t128 + 0.1e1
  t131 = -t123
  t132 = Heaviside(t131)
  t134 = t121 * t124 + t130 * t132
  t138 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t94 * t134)
  t139 = t6 ** 2
  t141 = t16 / t139
  t142 = t7 - t141
  t143 = f.my_piecewise5(t10, 0, t14, 0, t142)
  t146 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t143)
  t151 = t26 ** 2
  t152 = 0.1e1 / t151
  t156 = t5 * t25 * t152 * t82 / 0.8e1
  t164 = -0.5e1 / 0.3e1 * tau0 * t41 + s0 / t35 / t39 / r0 / 0.3e1
  t166 = t164 * t45 * t50
  t169 = t45 ** 2
  t170 = t44 * t169
  t172 = 0.1e1 / t48 / t47
  t173 = t170 * t172
  t175 = t62 * t64
  t180 = t170 * t172 * t56
  t181 = t61 ** 2
  t183 = 0.1e1 / t181 * t64
  t190 = Dirac(t70)
  t191 = t68 * t190
  t195 = t53 * t76
  t197 = t75 ** 2
  t199 = t74 / t197
  t204 = Dirac(t79)
  t205 = t78 * t204
  t213 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t146 * t26 * t82 - t156 - 0.3e1 / 0.8e1 * t5 * t27 * ((0.5e1 / 0.9e1 * t166 * t65 + 0.25e2 / 0.81e2 * t173 * params.c1 * t164 * t175 - 0.25e2 / 0.81e2 * t180 * t183 * t57 * t164) * t71 - 0.5e1 / 0.9e1 * t191 * t166 + (-0.5e1 / 0.9e1 * t73 * t164 * t195 - 0.5e1 / 0.9e1 * t199 * t166) * t80 + 0.5e1 / 0.9e1 * t205 * t166))
  t215 = f.my_piecewise5(t14, 0, t10, 0, -t142)
  t218 = f.my_piecewise3(t90, 0, 0.4e1 / 0.3e1 * t91 * t215)
  t226 = t5 * t93 * t152 * t134 / 0.8e1
  t228 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t218 * t26 * t134 - t226)
  vrho_0_ = t86 + t138 + t6 * (t213 + t228)
  t231 = -t7 - t141
  t232 = f.my_piecewise5(t10, 0, t14, 0, t231)
  t235 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t232)
  t241 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t235 * t26 * t82 - t156)
  t243 = f.my_piecewise5(t14, 0, t10, 0, -t231)
  t246 = f.my_piecewise3(t90, 0, 0.4e1 / 0.3e1 * t91 * t243)
  t258 = -0.5e1 / 0.3e1 * tau1 * t102 + s2 / t96 / t100 / r1 / 0.3e1
  t260 = t258 * t45 * t50
  t263 = t105 * t169
  t264 = t263 * t172
  t266 = t116 * t64
  t271 = t263 * t172 * t111
  t272 = t115 ** 2
  t274 = 0.1e1 / t272 * t64
  t281 = Dirac(t123)
  t282 = t121 * t281
  t286 = t53 * t128
  t288 = t127 ** 2
  t290 = t126 / t288
  t295 = Dirac(t131)
  t296 = t130 * t295
  t304 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t246 * t26 * t134 - t226 - 0.3e1 / 0.8e1 * t5 * t94 * ((0.5e1 / 0.9e1 * t260 * t118 + 0.25e2 / 0.81e2 * t264 * params.c1 * t258 * t266 - 0.25e2 / 0.81e2 * t271 * t274 * t57 * t258) * t124 - 0.5e1 / 0.9e1 * t282 * t260 + (-0.5e1 / 0.9e1 * t73 * t258 * t286 - 0.5e1 / 0.9e1 * t290 * t260) * t132 + 0.5e1 / 0.9e1 * t296 * t260))
  vrho_1_ = t86 + t138 + t6 * (t241 + t304)
  t308 = t41 * t45 * t50
  t335 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * ((-0.5e1 / 0.72e2 * t308 * t65 - 0.25e2 / 0.648e3 * t173 * params.c1 * t41 * t175 + 0.25e2 / 0.648e3 * t180 * t183 * t57 * t41) * t71 + 0.5e1 / 0.72e2 * t191 * t308 + (0.5e1 / 0.72e2 * t73 * t41 * t195 + 0.5e1 / 0.72e2 * t199 * t308) * t80 - 0.5e1 / 0.72e2 * t205 * t308))
  vsigma_0_ = t6 * t335
  vsigma_1_ = 0.0e0
  t337 = t102 * t45 * t50
  t364 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t94 * ((-0.5e1 / 0.72e2 * t337 * t118 - 0.25e2 / 0.648e3 * t264 * params.c1 * t102 * t266 + 0.25e2 / 0.648e3 * t271 * t274 * t57 * t102) * t124 + 0.5e1 / 0.72e2 * t282 * t337 + (0.5e1 / 0.72e2 * t73 * t102 * t286 + 0.5e1 / 0.72e2 * t290 * t337) * t132 - 0.5e1 / 0.72e2 * t296 * t337))
  vsigma_2_ = t6 * t364
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t366 = t37 * t45 * t50
  t393 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * ((0.5e1 / 0.9e1 * t366 * t65 + 0.25e2 / 0.81e2 * t173 * params.c1 * t37 * t175 - 0.25e2 / 0.81e2 * t180 * t183 * t57 * t37) * t71 - 0.5e1 / 0.9e1 * t191 * t366 + (-0.5e1 / 0.9e1 * t73 * t37 * t195 - 0.5e1 / 0.9e1 * t199 * t366) * t80 + 0.5e1 / 0.9e1 * t205 * t366))
  vtau_0_ = t6 * t393
  t395 = t98 * t45 * t50
  t422 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t94 * ((0.5e1 / 0.9e1 * t395 * t118 + 0.25e2 / 0.81e2 * t264 * params.c1 * t98 * t266 - 0.25e2 / 0.81e2 * t271 * t274 * t57 * t98) * t124 - 0.5e1 / 0.9e1 * t282 * t395 + (-0.5e1 / 0.9e1 * t73 * t98 * t286 - 0.5e1 / 0.9e1 * t290 * t395) * t132 + 0.5e1 / 0.9e1 * t296 * t395))
  vtau_1_ = t6 * t422
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
  params_alphainf_raw = params.alphainf
  if isinstance(params_alphainf_raw, (str, bytes, dict)):
    params_alphainf = params_alphainf_raw
  else:
    try:
      params_alphainf_seq = list(params_alphainf_raw)
    except TypeError:
      params_alphainf = params_alphainf_raw
    else:
      params_alphainf_seq = np.asarray(params_alphainf_seq, dtype=np.float64)
      params_alphainf = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphainf_seq))
  params_c0_raw = params.c0
  if isinstance(params_c0_raw, (str, bytes, dict)):
    params_c0 = params_c0_raw
  else:
    try:
      params_c0_seq = list(params_c0_raw)
    except TypeError:
      params_c0 = params_c0_raw
    else:
      params_c0_seq = np.asarray(params_c0_seq, dtype=np.float64)
      params_c0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c0_seq))
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

  gx_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  gx_cx0 = 4 / 3 * (2 / jnp.pi) ** (1 / 3)

  gx_cx1 = X_FACTOR_C

  gx_gx1 = lambda a: 1 + (1 - params_alphainf) * (1 - a) / (1 + a)

  gx_gx0 = lambda a: +gx_cx0 / gx_cx1 + a * (params_c0 + params_c1 * a) / (1.0 + (params_c0 + params_c1 - 1) * a) * (1 - gx_cx0 / gx_cx1)

  gx_f_a = lambda a: +gx_gx0(a) * Heaviside(1 - a) + gx_gx1(a) * Heaviside(a - 1)

  gx_f = lambda x, u, t: gx_f_a(gx_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, gx_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  Dirac = lambda *args: jnp.zeros_like(args[-1])

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
  t20 = 2 ** (0.1e1 / 0.3e1)
  t21 = t3 ** 2
  t23 = 4 ** (0.1e1 / 0.3e1)
  t25 = 0.8e1 / 0.27e2 * t20 * t21 * t23
  t26 = t20 ** 2
  t27 = tau0 * t26
  t28 = t18 ** 2
  t30 = 0.1e1 / t28 / r0
  t32 = s0 * t26
  t33 = r0 ** 2
  t35 = 0.1e1 / t28 / t33
  t38 = t27 * t30 - t32 * t35 / 0.8e1
  t39 = 6 ** (0.1e1 / 0.3e1)
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t45 = t38 * t39 * t44
  t47 = t39 * t44
  t50 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t38 * t47
  t51 = params.c0 + params.c1 - 0.1e1
  t55 = 0.10e1 + 0.5e1 / 0.9e1 * t51 * t38 * t47
  t56 = 0.1e1 / t55
  t58 = 0.1e1 - t25
  t59 = t50 * t56 * t58
  t62 = t25 + 0.5e1 / 0.9e1 * t45 * t59
  t63 = 0.5e1 / 0.9e1 * t45
  t64 = 0.1e1 - t63
  t65 = Heaviside(t64)
  t67 = 0.1e1 - params.alphainf
  t68 = t67 * t64
  t69 = 0.1e1 + t63
  t70 = 0.1e1 / t69
  t72 = t68 * t70 + 0.1e1
  t73 = -t64
  t74 = Heaviside(t73)
  t76 = t62 * t65 + t72 * t74
  t80 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t76)
  t93 = -0.5e1 / 0.3e1 * t27 * t35 + t32 / t28 / t33 / r0 / 0.3e1
  t95 = t93 * t39 * t44
  t98 = t39 ** 2
  t99 = t38 * t98
  t101 = 0.1e1 / t42 / t41
  t104 = t56 * t58
  t109 = t99 * t101 * t50
  t110 = t55 ** 2
  t112 = 0.1e1 / t110 * t58
  t119 = Dirac(t64)
  t120 = t62 * t119
  t124 = t47 * t70
  t126 = t69 ** 2
  t128 = t68 / t126
  t133 = Dirac(t73)
  t134 = t72 * t133
  t142 = f.my_piecewise3(t2, 0, -t6 * t17 / t28 * t76 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * ((0.5e1 / 0.9e1 * t95 * t59 + 0.25e2 / 0.81e2 * t99 * t101 * params.c1 * t93 * t104 - 0.25e2 / 0.81e2 * t109 * t112 * t51 * t93) * t65 - 0.5e1 / 0.9e1 * t120 * t95 + (-0.5e1 / 0.9e1 * t67 * t93 * t124 - 0.5e1 / 0.9e1 * t128 * t95) * t74 + 0.5e1 / 0.9e1 * t134 * t95))
  vrho_0_ = 0.2e1 * r0 * t142 + 0.2e1 * t80
  t145 = t26 * t35
  t148 = t44 * t50 * t104
  t152 = t99 * t101 * params.c1
  t156 = t51 * t26
  t163 = t120 * t26
  t165 = t35 * t39 * t44
  t168 = t67 * t26
  t176 = t134 * t26
  t183 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * ((-0.5e1 / 0.72e2 * t145 * t39 * t148 - 0.25e2 / 0.648e3 * t152 * t145 * t104 + 0.25e2 / 0.648e3 * t109 * t112 * t156 * t35) * t65 + 0.5e1 / 0.72e2 * t163 * t165 + (0.5e1 / 0.72e2 * t168 * t35 * t124 + 0.5e1 / 0.72e2 * t128 * t145 * t47) * t74 - 0.5e1 / 0.72e2 * t176 * t165))
  vsigma_0_ = 0.2e1 * r0 * t183
  vlapl_0_ = 0.0e0
  t185 = t26 * t30
  t199 = t30 * t39 * t44
  t215 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * ((0.5e1 / 0.9e1 * t185 * t39 * t148 + 0.25e2 / 0.81e2 * t152 * t185 * t104 - 0.25e2 / 0.81e2 * t109 * t112 * t156 * t30) * t65 - 0.5e1 / 0.9e1 * t163 * t199 + (-0.5e1 / 0.9e1 * t168 * t30 * t124 - 0.5e1 / 0.9e1 * t128 * t185 * t47) * t74 + 0.5e1 / 0.9e1 * t176 * t199))
  vtau_0_ = 0.2e1 * r0 * t215
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
  t21 = t17 / t19
  t22 = 2 ** (0.1e1 / 0.3e1)
  t23 = t3 ** 2
  t25 = 4 ** (0.1e1 / 0.3e1)
  t27 = 0.8e1 / 0.27e2 * t22 * t23 * t25
  t28 = t22 ** 2
  t29 = tau0 * t28
  t31 = 0.1e1 / t19 / r0
  t33 = s0 * t28
  t34 = r0 ** 2
  t36 = 0.1e1 / t19 / t34
  t39 = t29 * t31 - t33 * t36 / 0.8e1
  t40 = 6 ** (0.1e1 / 0.3e1)
  t42 = jnp.pi ** 2
  t43 = t42 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t46 = t39 * t40 * t45
  t48 = t40 * t45
  t51 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t39 * t48
  t52 = params.c0 + params.c1 - 0.1e1
  t56 = 0.10e1 + 0.5e1 / 0.9e1 * t52 * t39 * t48
  t57 = 0.1e1 / t56
  t59 = 0.1e1 - t27
  t60 = t51 * t57 * t59
  t63 = t27 + 0.5e1 / 0.9e1 * t46 * t60
  t64 = 0.5e1 / 0.9e1 * t46
  t65 = 0.1e1 - t64
  t66 = Heaviside(t65)
  t68 = 0.1e1 - params.alphainf
  t69 = t68 * t65
  t70 = 0.1e1 + t64
  t71 = 0.1e1 / t70
  t73 = t69 * t71 + 0.1e1
  t75 = Heaviside(-t65)
  t77 = t63 * t66 + t73 * t75
  t81 = t17 * t18
  t86 = 0.1e1 / t19 / t34 / r0
  t89 = -0.5e1 / 0.3e1 * t29 * t36 + t33 * t86 / 0.3e1
  t91 = t89 * t40 * t45
  t94 = t40 ** 2
  t95 = t39 * t94
  t97 = 0.1e1 / t43 / t42
  t98 = t95 * t97
  t100 = t57 * t59
  t105 = t95 * t97 * t51
  t106 = t56 ** 2
  t107 = 0.1e1 / t106
  t108 = t107 * t59
  t113 = 0.5e1 / 0.9e1 * t91 * t60 + 0.25e2 / 0.81e2 * t98 * params.c1 * t89 * t100 - 0.25e2 / 0.81e2 * t105 * t108 * t52 * t89
  t115 = Dirac(t65)
  t116 = t63 * t115
  t120 = t48 * t71
  t122 = t70 ** 2
  t123 = 0.1e1 / t122
  t124 = t69 * t123
  t127 = -0.5e1 / 0.9e1 * t68 * t89 * t120 - 0.5e1 / 0.9e1 * t124 * t91
  t129 = t73 * t115
  t132 = t113 * t66 - 0.5e1 / 0.9e1 * t116 * t91 + t127 * t75 + 0.5e1 / 0.9e1 * t129 * t91
  t137 = f.my_piecewise3(t2, 0, -t6 * t21 * t77 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t81 * t132)
  t148 = t34 ** 2
  t153 = 0.40e2 / 0.9e1 * t29 * t86 - 0.11e2 / 0.9e1 * t33 / t19 / t148
  t155 = t153 * t40 * t45
  t158 = t89 ** 2
  t160 = t158 * t94 * t97
  t166 = t59 * t52
  t174 = t42 ** 2
  t176 = t39 / t174
  t186 = t52 ** 2
  t200 = Dirac(1, t65)
  t236 = f.my_piecewise3(t2, 0, t6 * t17 * t31 * t77 / 0.12e2 - t6 * t21 * t132 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t81 * ((0.5e1 / 0.9e1 * t155 * t60 + 0.50e2 / 0.81e2 * t160 * params.c1 * t57 * t59 - 0.50e2 / 0.81e2 * t160 * t51 * t107 * t166 + 0.25e2 / 0.81e2 * t98 * params.c1 * t153 * t100 - 0.500e3 / 0.243e3 * t176 * params.c1 * t158 * t107 * t166 + 0.500e3 / 0.243e3 * t176 * t51 / t106 / t56 * t59 * t186 * t158 - 0.25e2 / 0.81e2 * t105 * t108 * t52 * t153) * t66 - 0.10e2 / 0.9e1 * t113 * t115 * t91 + 0.25e2 / 0.81e2 * t63 * t200 * t160 - 0.5e1 / 0.9e1 * t116 * t155 + (-0.5e1 / 0.9e1 * t68 * t153 * t120 + 0.50e2 / 0.81e2 * t68 * t158 * t94 * t97 * t123 + 0.50e2 / 0.81e2 * t69 / t122 / t70 * t160 - 0.5e1 / 0.9e1 * t124 * t155) * t75 + 0.10e2 / 0.9e1 * t127 * t115 * t91 - 0.25e2 / 0.81e2 * t73 * t200 * t160 + 0.5e1 / 0.9e1 * t129 * t155))
  v2rho2_0_ = 0.2e1 * r0 * t236 + 0.4e1 * t137
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
  t22 = t17 * t21
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t3 ** 2
  t26 = 4 ** (0.1e1 / 0.3e1)
  t28 = 0.8e1 / 0.27e2 * t23 * t24 * t26
  t29 = t23 ** 2
  t30 = tau0 * t29
  t32 = s0 * t29
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t38 = t30 * t21 - t32 * t35 / 0.8e1
  t39 = 6 ** (0.1e1 / 0.3e1)
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t45 = t38 * t39 * t44
  t47 = t39 * t44
  t50 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t38 * t47
  t51 = params.c0 + params.c1 - 0.1e1
  t55 = 0.10e1 + 0.5e1 / 0.9e1 * t51 * t38 * t47
  t56 = 0.1e1 / t55
  t58 = 0.1e1 - t28
  t59 = t50 * t56 * t58
  t62 = t28 + 0.5e1 / 0.9e1 * t45 * t59
  t63 = 0.5e1 / 0.9e1 * t45
  t64 = 0.1e1 - t63
  t65 = Heaviside(t64)
  t67 = 0.1e1 - params.alphainf
  t68 = t67 * t64
  t69 = 0.1e1 + t63
  t70 = 0.1e1 / t69
  t72 = t68 * t70 + 0.1e1
  t74 = Heaviside(-t64)
  t76 = t62 * t65 + t72 * t74
  t81 = t17 / t19
  t86 = 0.1e1 / t19 / t33 / r0
  t89 = -0.5e1 / 0.3e1 * t30 * t35 + t32 * t86 / 0.3e1
  t91 = t89 * t39 * t44
  t94 = t39 ** 2
  t95 = t38 * t94
  t97 = 0.1e1 / t42 / t41
  t98 = t95 * t97
  t100 = t56 * t58
  t101 = params.c1 * t89 * t100
  t104 = t97 * t50
  t105 = t95 * t104
  t106 = t55 ** 2
  t107 = 0.1e1 / t106
  t108 = t107 * t58
  t110 = t108 * t51 * t89
  t113 = 0.5e1 / 0.9e1 * t91 * t59 + 0.25e2 / 0.81e2 * t98 * t101 - 0.25e2 / 0.81e2 * t105 * t110
  t115 = Dirac(t64)
  t116 = t62 * t115
  t120 = t47 * t70
  t122 = t69 ** 2
  t123 = 0.1e1 / t122
  t124 = t68 * t123
  t127 = -0.5e1 / 0.9e1 * t67 * t89 * t120 - 0.5e1 / 0.9e1 * t124 * t91
  t129 = t72 * t115
  t132 = t113 * t65 - 0.5e1 / 0.9e1 * t116 * t91 + t127 * t74 + 0.5e1 / 0.9e1 * t129 * t91
  t136 = t17 * t18
  t139 = t33 ** 2
  t141 = 0.1e1 / t19 / t139
  t144 = 0.40e2 / 0.9e1 * t30 * t86 - 0.11e2 / 0.9e1 * t32 * t141
  t146 = t144 * t39 * t44
  t149 = t89 ** 2
  t151 = t149 * t94 * t97
  t157 = t58 * t51
  t161 = params.c1 * t144
  t165 = t41 ** 2
  t166 = 0.1e1 / t165
  t167 = t38 * t166
  t175 = 0.1e1 / t106 / t55
  t176 = t175 * t58
  t177 = t51 ** 2
  t186 = 0.5e1 / 0.9e1 * t146 * t59 + 0.50e2 / 0.81e2 * t151 * params.c1 * t56 * t58 - 0.50e2 / 0.81e2 * t151 * t50 * t107 * t157 + 0.25e2 / 0.81e2 * t98 * t161 * t100 - 0.500e3 / 0.243e3 * t167 * params.c1 * t149 * t107 * t157 + 0.500e3 / 0.243e3 * t167 * t50 * t176 * t177 * t149 - 0.25e2 / 0.81e2 * t105 * t108 * t51 * t144
  t188 = t113 * t115
  t191 = Dirac(1, t64)
  t192 = t62 * t191
  t197 = t67 * t144
  t206 = 0.1e1 / t122 / t69
  t207 = t68 * t206
  t212 = -0.5e1 / 0.9e1 * t197 * t120 + 0.50e2 / 0.81e2 * t67 * t149 * t94 * t97 * t123 + 0.50e2 / 0.81e2 * t207 * t151 - 0.5e1 / 0.9e1 * t124 * t146
  t214 = t127 * t115
  t217 = t72 * t191
  t222 = t186 * t65 - 0.10e2 / 0.9e1 * t188 * t91 + 0.25e2 / 0.81e2 * t192 * t151 - 0.5e1 / 0.9e1 * t116 * t146 + t212 * t74 + 0.10e2 / 0.9e1 * t214 * t91 - 0.25e2 / 0.81e2 * t217 * t151 + 0.5e1 / 0.9e1 * t129 * t146
  t227 = f.my_piecewise3(t2, 0, t6 * t22 * t76 / 0.12e2 - t6 * t81 * t132 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t136 * t222)
  t246 = -0.440e3 / 0.27e2 * t30 * t141 + 0.154e3 / 0.27e2 * t32 / t19 / t139 / r0
  t248 = t246 * t39 * t44
  t251 = t144 * t94
  t252 = t251 * t97
  t258 = t149 * t89
  t259 = t258 * t166
  t282 = t106 ** 2
  t304 = 0.5e1 / 0.9e1 * t248 * t59 + 0.50e2 / 0.27e2 * t252 * t101 - 0.50e2 / 0.27e2 * t251 * t104 * t110 - 0.500e3 / 0.81e2 * t259 * params.c1 * t108 * t51 + 0.500e3 / 0.81e2 * t259 * t50 * t176 * t177 + 0.25e2 / 0.81e2 * t98 * params.c1 * t246 * t100 - 0.500e3 / 0.81e2 * t167 * t161 * t110 + 0.2500e4 / 0.729e3 * t167 * params.c1 * t258 * t176 * t177 * t39 * t44 - 0.2500e4 / 0.729e3 * t167 * t50 / t282 * t58 * t177 * t51 * t258 * t39 * t44 + 0.500e3 / 0.81e2 * t167 * t50 * t175 * t58 * t177 * t89 * t144 - 0.25e2 / 0.81e2 * t105 * t108 * t51 * t246
  t314 = Dirac(2, t64)
  t335 = t122 ** 2
  t366 = t304 * t65 - 0.5e1 / 0.3e1 * t186 * t115 * t91 + 0.25e2 / 0.27e2 * t113 * t191 * t151 - 0.5e1 / 0.3e1 * t188 * t146 - 0.250e3 / 0.243e3 * t62 * t314 * t259 + 0.25e2 / 0.27e2 * t192 * t89 * t252 - 0.5e1 / 0.9e1 * t116 * t248 + (-0.5e1 / 0.9e1 * t67 * t246 * t120 + 0.50e2 / 0.27e2 * t197 * t94 * t97 * t123 * t89 - 0.500e3 / 0.81e2 * t67 * t258 * t166 * t206 - 0.500e3 / 0.81e2 * t68 / t335 * t258 * t166 + 0.50e2 / 0.27e2 * t207 * t89 * t94 * t97 * t144 - 0.5e1 / 0.9e1 * t124 * t248) * t74 + 0.5e1 / 0.3e1 * t212 * t115 * t91 - 0.25e2 / 0.27e2 * t127 * t191 * t151 + 0.5e1 / 0.3e1 * t214 * t146 + 0.250e3 / 0.243e3 * t72 * t314 * t259 - 0.25e2 / 0.27e2 * t217 * t89 * t252 + 0.5e1 / 0.9e1 * t129 * t248
  t371 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t76 + t6 * t22 * t132 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t81 * t222 - 0.3e1 / 0.8e1 * t6 * t136 * t366)
  v3rho3_0_ = 0.2e1 * r0 * t371 + 0.6e1 * t227

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
  t23 = t17 * t22
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t3 ** 2
  t27 = 4 ** (0.1e1 / 0.3e1)
  t29 = 0.8e1 / 0.27e2 * t24 * t25 * t27
  t30 = t24 ** 2
  t31 = tau0 * t30
  t33 = 0.1e1 / t20 / r0
  t35 = s0 * t30
  t38 = t31 * t33 - t35 * t22 / 0.8e1
  t39 = 6 ** (0.1e1 / 0.3e1)
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t45 = t38 * t39 * t44
  t47 = t39 * t44
  t50 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t38 * t47
  t51 = params.c0 + params.c1 - 0.1e1
  t55 = 0.10e1 + 0.5e1 / 0.9e1 * t51 * t38 * t47
  t56 = 0.1e1 / t55
  t58 = 0.1e1 - t29
  t59 = t50 * t56 * t58
  t62 = t29 + 0.5e1 / 0.9e1 * t45 * t59
  t63 = 0.5e1 / 0.9e1 * t45
  t64 = 0.1e1 - t63
  t65 = Heaviside(t64)
  t67 = 0.1e1 - params.alphainf
  t68 = t67 * t64
  t69 = 0.1e1 + t63
  t70 = 0.1e1 / t69
  t72 = t68 * t70 + 0.1e1
  t74 = Heaviside(-t64)
  t76 = t62 * t65 + t72 * t74
  t80 = t17 * t33
  t85 = 0.1e1 / t20 / t18 / r0
  t88 = -0.5e1 / 0.3e1 * t31 * t22 + t35 * t85 / 0.3e1
  t90 = t88 * t39 * t44
  t93 = t39 ** 2
  t94 = t38 * t93
  t96 = 0.1e1 / t42 / t41
  t97 = t94 * t96
  t99 = t56 * t58
  t100 = params.c1 * t88 * t99
  t103 = t96 * t50
  t104 = t94 * t103
  t105 = t55 ** 2
  t106 = 0.1e1 / t105
  t107 = t106 * t58
  t109 = t107 * t51 * t88
  t112 = 0.5e1 / 0.9e1 * t90 * t59 + 0.25e2 / 0.81e2 * t97 * t100 - 0.25e2 / 0.81e2 * t104 * t109
  t114 = Dirac(t64)
  t115 = t62 * t114
  t119 = t47 * t70
  t121 = t69 ** 2
  t122 = 0.1e1 / t121
  t123 = t68 * t122
  t126 = -0.5e1 / 0.9e1 * t67 * t88 * t119 - 0.5e1 / 0.9e1 * t123 * t90
  t128 = t72 * t114
  t131 = t112 * t65 - 0.5e1 / 0.9e1 * t115 * t90 + t126 * t74 + 0.5e1 / 0.9e1 * t128 * t90
  t136 = t17 / t20
  t139 = t18 ** 2
  t141 = 0.1e1 / t20 / t139
  t144 = 0.40e2 / 0.9e1 * t31 * t85 - 0.11e2 / 0.9e1 * t35 * t141
  t146 = t144 * t39 * t44
  t149 = t88 ** 2
  t151 = t149 * t93 * t96
  t153 = params.c1 * t56 * t58
  t157 = t58 * t51
  t158 = t50 * t106 * t157
  t161 = params.c1 * t144
  t165 = t41 ** 2
  t166 = 0.1e1 / t165
  t167 = t38 * t166
  t168 = t167 * params.c1
  t170 = t149 * t106 * t157
  t173 = t167 * t50
  t175 = 0.1e1 / t105 / t55
  t176 = t175 * t58
  t177 = t51 ** 2
  t179 = t176 * t177 * t149
  t186 = 0.5e1 / 0.9e1 * t146 * t59 + 0.50e2 / 0.81e2 * t151 * t153 - 0.50e2 / 0.81e2 * t151 * t158 + 0.25e2 / 0.81e2 * t97 * t161 * t99 - 0.500e3 / 0.243e3 * t168 * t170 + 0.500e3 / 0.243e3 * t173 * t179 - 0.25e2 / 0.81e2 * t104 * t107 * t51 * t144
  t188 = t112 * t114
  t191 = Dirac(1, t64)
  t192 = t62 * t191
  t197 = t67 * t144
  t202 = t93 * t96 * t122
  t206 = 0.1e1 / t121 / t69
  t207 = t68 * t206
  t212 = -0.5e1 / 0.9e1 * t197 * t119 + 0.50e2 / 0.81e2 * t67 * t149 * t202 + 0.50e2 / 0.81e2 * t207 * t151 - 0.5e1 / 0.9e1 * t123 * t146
  t214 = t126 * t114
  t217 = t72 * t191
  t222 = t186 * t65 - 0.10e2 / 0.9e1 * t188 * t90 + 0.25e2 / 0.81e2 * t192 * t151 - 0.5e1 / 0.9e1 * t115 * t146 + t212 * t74 + 0.10e2 / 0.9e1 * t214 * t90 - 0.25e2 / 0.81e2 * t217 * t151 + 0.5e1 / 0.9e1 * t128 * t146
  t226 = t17 * t19
  t231 = 0.1e1 / t20 / t139 / r0
  t234 = -0.440e3 / 0.27e2 * t31 * t141 + 0.154e3 / 0.27e2 * t35 * t231
  t236 = t234 * t39 * t44
  t239 = t144 * t93
  t240 = t239 * t96
  t246 = t149 * t88
  t247 = t246 * t166
  t256 = params.c1 * t234
  t270 = t105 ** 2
  t271 = 0.1e1 / t270
  t272 = t50 * t271
  t274 = t177 * t51
  t275 = t58 * t274
  t282 = t167 * t50 * t175
  t283 = t58 * t177
  t292 = 0.5e1 / 0.9e1 * t236 * t59 + 0.50e2 / 0.27e2 * t240 * t100 - 0.50e2 / 0.27e2 * t239 * t103 * t109 - 0.500e3 / 0.81e2 * t247 * params.c1 * t107 * t51 + 0.500e3 / 0.81e2 * t247 * t50 * t176 * t177 + 0.25e2 / 0.81e2 * t97 * t256 * t99 - 0.500e3 / 0.81e2 * t167 * t161 * t109 + 0.2500e4 / 0.729e3 * t167 * params.c1 * t246 * t176 * t177 * t39 * t44 - 0.2500e4 / 0.729e3 * t167 * t272 * t275 * t246 * t39 * t44 + 0.500e3 / 0.81e2 * t282 * t283 * t88 * t144 - 0.25e2 / 0.81e2 * t104 * t107 * t51 * t234
  t294 = t186 * t114
  t297 = t112 * t191
  t302 = Dirac(2, t64)
  t303 = t62 * t302
  t306 = t192 * t88
  t311 = t67 * t234
  t316 = t96 * t122 * t88
  t320 = t166 * t206
  t323 = t121 ** 2
  t324 = 0.1e1 / t323
  t329 = t88 * t93
  t336 = -0.5e1 / 0.9e1 * t311 * t119 + 0.50e2 / 0.27e2 * t197 * t93 * t316 - 0.500e3 / 0.81e2 * t67 * t246 * t320 - 0.500e3 / 0.81e2 * t68 * t324 * t246 * t166 + 0.50e2 / 0.27e2 * t207 * t329 * t96 * t144 - 0.5e1 / 0.9e1 * t123 * t236
  t338 = t212 * t114
  t341 = t126 * t191
  t346 = t72 * t302
  t349 = t217 * t88
  t354 = t292 * t65 - 0.5e1 / 0.3e1 * t294 * t90 + 0.25e2 / 0.27e2 * t297 * t151 - 0.5e1 / 0.3e1 * t188 * t146 - 0.250e3 / 0.243e3 * t303 * t247 + 0.25e2 / 0.27e2 * t306 * t240 - 0.5e1 / 0.9e1 * t115 * t236 + t336 * t74 + 0.5e1 / 0.3e1 * t338 * t90 - 0.25e2 / 0.27e2 * t341 * t151 + 0.5e1 / 0.3e1 * t214 * t146 + 0.250e3 / 0.243e3 * t346 * t247 - 0.25e2 / 0.27e2 * t349 * t240 + 0.5e1 / 0.9e1 * t128 * t236
  t359 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t76 + t6 * t80 * t131 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t136 * t222 - 0.3e1 / 0.8e1 * t6 * t226 * t354)
  t387 = 0.6160e4 / 0.81e2 * t31 * t231 - 0.2618e4 / 0.81e2 * t35 / t20 / t139 / t18
  t397 = t144 ** 2
  t401 = t149 ** 2
  t411 = t401 * t166
  t417 = t149 * t166 * t144
  t421 = t397 * t93 * t96
  t429 = t387 * t39 * t44
  t446 = t234 * t93
  t470 = t144 * t166
  t481 = t446 * t96
  t503 = t177 ** 2
  t518 = 0.500e3 / 0.81e2 * t173 * t176 * t177 * t397 + 0.2000e4 / 0.243e3 * t282 * t283 * t88 * t234 - 0.25e2 / 0.81e2 * t104 * t107 * t51 * t387 - 0.200e3 / 0.81e2 * t446 * t103 * t109 - 0.50e2 / 0.27e2 * t421 * t158 + 0.10000e5 / 0.729e3 * t411 * params.c1 * t175 * t283 * t47 - 0.10000e5 / 0.729e3 * t411 * t272 * t275 * t47 - 0.2000e4 / 0.243e3 * t167 * t256 * t109 - 0.500e3 / 0.81e2 * t168 * t397 * t106 * t157 + 0.50e2 / 0.27e2 * t421 * t153 - 0.1000e4 / 0.27e2 * t470 * params.c1 * t170 + 0.1000e4 / 0.27e2 * t470 * t50 * t179 + 0.25e2 / 0.81e2 * t97 * params.c1 * t387 * t99 + 0.200e3 / 0.81e2 * t481 * t100 + 0.5e1 / 0.9e1 * t429 * t59 + 0.5000e4 / 0.243e3 * t167 * t161 * t175 * t283 * t149 * t39 * t44 - 0.5000e4 / 0.243e3 * t167 * t272 * t58 * t274 * t149 * t146 + 0.50000e5 / 0.6561e4 * t167 * t50 / t270 / t55 * t58 * t503 * t401 * t93 * t96 - 0.50000e5 / 0.6561e4 * t167 * params.c1 * t401 * t271 * t58 * t274 * t93 * t96
  t520 = Dirac(3, t64)
  t523 = t47 * t166
  t544 = 0.1000e4 / 0.243e3 * t126 * t302 * t247 - 0.1000e4 / 0.243e3 * t112 * t302 * t247 + (-0.5e1 / 0.9e1 * t67 * t387 * t119 + 0.200e3 / 0.81e2 * t311 * t93 * t316 - 0.1000e4 / 0.27e2 * t197 * t320 * t149 + 0.50e2 / 0.27e2 * t67 * t397 * t202 + 0.10000e5 / 0.729e3 * t67 * t401 * t166 * t324 * t39 * t44 + 0.10000e5 / 0.729e3 * t68 / t323 / t69 * t411 * t47 - 0.1000e4 / 0.27e2 * t68 * t324 * t417 + 0.50e2 / 0.27e2 * t207 * t421 + 0.200e3 / 0.81e2 * t207 * t329 * t96 * t234 - 0.5e1 / 0.9e1 * t123 * t429) * t74 + t518 * t65 - 0.1250e4 / 0.2187e4 * t72 * t520 * t401 * t523 - 0.25e2 / 0.27e2 * t217 * t421 - 0.100e3 / 0.81e2 * t349 * t481 - 0.100e3 / 0.27e2 * t341 * t88 * t240 + 0.25e2 / 0.27e2 * t192 * t421 + 0.100e3 / 0.81e2 * t306 * t481 + 0.100e3 / 0.27e2 * t297 * t88 * t240 + 0.1250e4 / 0.2187e4 * t62 * t520 * t401 * t523
  t573 = 0.20e2 / 0.9e1 * t214 * t236 + 0.500e3 / 0.81e2 * t346 * t417 + 0.5e1 / 0.9e1 * t128 * t429 - 0.5e1 / 0.9e1 * t115 * t429 + 0.20e2 / 0.9e1 * t336 * t114 * t90 + 0.10e2 / 0.3e1 * t338 * t146 - 0.50e2 / 0.27e2 * t212 * t191 * t151 - 0.20e2 / 0.9e1 * t188 * t236 - 0.500e3 / 0.81e2 * t303 * t417 - 0.20e2 / 0.9e1 * t292 * t114 * t90 - 0.10e2 / 0.3e1 * t294 * t146 + 0.50e2 / 0.27e2 * t186 * t191 * t151
  t579 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t85 * t76 - 0.5e1 / 0.9e1 * t6 * t23 * t131 + t6 * t80 * t222 / 0.2e1 - t6 * t136 * t354 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t226 * (t544 + t573))
  v4rho4_0_ = 0.2e1 * r0 * t579 + 0.8e1 * t359

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
  t31 = t29 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t2 ** 2
  t35 = 4 ** (0.1e1 / 0.3e1)
  t37 = 0.8e1 / 0.27e2 * t32 * t33 * t35
  t38 = r0 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t43 = r0 ** 2
  t45 = 0.1e1 / t39 / t43
  t48 = tau0 / t39 / r0 - s0 * t45 / 0.8e1
  t49 = 6 ** (0.1e1 / 0.3e1)
  t51 = jnp.pi ** 2
  t52 = t51 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t54 = 0.1e1 / t53
  t55 = t48 * t49 * t54
  t57 = t49 * t54
  t60 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t48 * t57
  t61 = params.c0 + params.c1 - 0.1e1
  t65 = 0.10e1 + 0.5e1 / 0.9e1 * t61 * t48 * t57
  t66 = 0.1e1 / t65
  t68 = 0.1e1 - t37
  t69 = t60 * t66 * t68
  t72 = t37 + 0.5e1 / 0.9e1 * t55 * t69
  t73 = 0.5e1 / 0.9e1 * t55
  t74 = 0.1e1 - t73
  t75 = Heaviside(t74)
  t77 = 0.1e1 - params.alphainf
  t78 = t77 * t74
  t79 = 0.1e1 + t73
  t80 = 0.1e1 / t79
  t82 = t78 * t80 + 0.1e1
  t84 = Heaviside(-t74)
  t86 = t72 * t75 + t82 * t84
  t90 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t91 = t90 * f.p.zeta_threshold
  t93 = f.my_piecewise3(t20, t91, t21 * t19)
  t94 = t30 ** 2
  t95 = 0.1e1 / t94
  t96 = t93 * t95
  t99 = t5 * t96 * t86 / 0.8e1
  t100 = t93 * t30
  t105 = 0.1e1 / t39 / t43 / r0
  t108 = -0.5e1 / 0.3e1 * tau0 * t45 + s0 * t105 / 0.3e1
  t110 = t108 * t49 * t54
  t113 = t49 ** 2
  t114 = t48 * t113
  t116 = 0.1e1 / t52 / t51
  t117 = t114 * t116
  t119 = t66 * t68
  t124 = t114 * t116 * t60
  t125 = t65 ** 2
  t126 = 0.1e1 / t125
  t127 = t126 * t68
  t132 = 0.5e1 / 0.9e1 * t110 * t69 + 0.25e2 / 0.81e2 * t117 * params.c1 * t108 * t119 - 0.25e2 / 0.81e2 * t124 * t127 * t61 * t108
  t134 = Dirac(t74)
  t135 = t72 * t134
  t139 = t57 * t80
  t141 = t79 ** 2
  t142 = 0.1e1 / t141
  t143 = t78 * t142
  t146 = -0.5e1 / 0.9e1 * t77 * t108 * t139 - 0.5e1 / 0.9e1 * t143 * t110
  t148 = t82 * t134
  t151 = t132 * t75 - 0.5e1 / 0.9e1 * t135 * t110 + t146 * t84 + 0.5e1 / 0.9e1 * t148 * t110
  t156 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t86 - t99 - 0.3e1 / 0.8e1 * t5 * t100 * t151)
  t158 = r1 <= f.p.dens_threshold
  t159 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t160 = 0.1e1 + t159
  t161 = t160 <= f.p.zeta_threshold
  t162 = t160 ** (0.1e1 / 0.3e1)
  t164 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t167 = f.my_piecewise3(t161, 0, 0.4e1 / 0.3e1 * t162 * t164)
  t168 = t167 * t30
  t169 = r1 ** (0.1e1 / 0.3e1)
  t170 = t169 ** 2
  t174 = r1 ** 2
  t176 = 0.1e1 / t170 / t174
  t179 = tau1 / t170 / r1 - s2 * t176 / 0.8e1
  t181 = t179 * t49 * t54
  t185 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t179 * t57
  t189 = 0.10e1 + 0.5e1 / 0.9e1 * t61 * t179 * t57
  t190 = 0.1e1 / t189
  t192 = t185 * t190 * t68
  t195 = t37 + 0.5e1 / 0.9e1 * t181 * t192
  t196 = 0.5e1 / 0.9e1 * t181
  t197 = 0.1e1 - t196
  t198 = Heaviside(t197)
  t200 = t77 * t197
  t201 = 0.1e1 + t196
  t202 = 0.1e1 / t201
  t204 = t200 * t202 + 0.1e1
  t206 = Heaviside(-t197)
  t208 = t195 * t198 + t204 * t206
  t213 = f.my_piecewise3(t161, t91, t162 * t160)
  t214 = t213 * t95
  t217 = t5 * t214 * t208 / 0.8e1
  t219 = f.my_piecewise3(t158, 0, -0.3e1 / 0.8e1 * t5 * t168 * t208 - t217)
  t221 = t21 ** 2
  t222 = 0.1e1 / t221
  t223 = t26 ** 2
  t228 = t16 / t22 / t6
  t230 = -0.2e1 * t23 + 0.2e1 * t228
  t231 = f.my_piecewise5(t10, 0, t14, 0, t230)
  t235 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t222 * t223 + 0.4e1 / 0.3e1 * t21 * t231)
  t242 = t5 * t29 * t95 * t86
  t248 = 0.1e1 / t94 / t6
  t252 = t5 * t93 * t248 * t86 / 0.12e2
  t254 = t5 * t96 * t151
  t258 = t43 ** 2
  t263 = 0.40e2 / 0.9e1 * tau0 * t105 - 0.11e2 / 0.9e1 * s0 / t39 / t258
  t265 = t263 * t49 * t54
  t268 = t108 ** 2
  t270 = t268 * t113 * t116
  t276 = t68 * t61
  t284 = t51 ** 2
  t285 = 0.1e1 / t284
  t286 = t48 * t285
  t296 = t61 ** 2
  t310 = Dirac(1, t74)
  t320 = t113 * t116
  t346 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t235 * t30 * t86 - t242 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t151 + t252 - t254 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t100 * ((0.5e1 / 0.9e1 * t265 * t69 + 0.50e2 / 0.81e2 * t270 * params.c1 * t66 * t68 - 0.50e2 / 0.81e2 * t270 * t60 * t126 * t276 + 0.25e2 / 0.81e2 * t117 * params.c1 * t263 * t119 - 0.500e3 / 0.243e3 * t286 * params.c1 * t268 * t126 * t276 + 0.500e3 / 0.243e3 * t286 * t60 / t125 / t65 * t68 * t296 * t268 - 0.25e2 / 0.81e2 * t124 * t127 * t61 * t263) * t75 - 0.10e2 / 0.9e1 * t132 * t134 * t110 + 0.25e2 / 0.81e2 * t72 * t310 * t270 - 0.5e1 / 0.9e1 * t135 * t265 + (-0.5e1 / 0.9e1 * t77 * t263 * t139 + 0.50e2 / 0.81e2 * t77 * t268 * t320 * t142 + 0.50e2 / 0.81e2 * t78 / t141 / t79 * t270 - 0.5e1 / 0.9e1 * t143 * t265) * t84 + 0.10e2 / 0.9e1 * t146 * t134 * t110 - 0.25e2 / 0.81e2 * t82 * t310 * t270 + 0.5e1 / 0.9e1 * t148 * t265))
  t347 = t162 ** 2
  t348 = 0.1e1 / t347
  t349 = t164 ** 2
  t353 = f.my_piecewise5(t14, 0, t10, 0, -t230)
  t357 = f.my_piecewise3(t161, 0, 0.4e1 / 0.9e1 * t348 * t349 + 0.4e1 / 0.3e1 * t162 * t353)
  t364 = t5 * t167 * t95 * t208
  t369 = t5 * t213 * t248 * t208 / 0.12e2
  t371 = f.my_piecewise3(t158, 0, -0.3e1 / 0.8e1 * t5 * t357 * t30 * t208 - t364 / 0.4e1 + t369)
  d11 = 0.2e1 * t156 + 0.2e1 * t219 + t6 * (t346 + t371)
  t374 = -t7 - t24
  t375 = f.my_piecewise5(t10, 0, t14, 0, t374)
  t378 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t375)
  t379 = t378 * t30
  t384 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t379 * t86 - t99)
  t386 = f.my_piecewise5(t14, 0, t10, 0, -t374)
  t389 = f.my_piecewise3(t161, 0, 0.4e1 / 0.3e1 * t162 * t386)
  t390 = t389 * t30
  t394 = t213 * t30
  t399 = 0.1e1 / t170 / t174 / r1
  t402 = -0.5e1 / 0.3e1 * tau1 * t176 + s2 * t399 / 0.3e1
  t404 = t402 * t49 * t54
  t407 = t179 * t113
  t408 = t407 * t116
  t410 = t190 * t68
  t415 = t407 * t116 * t185
  t416 = t189 ** 2
  t417 = 0.1e1 / t416
  t418 = t417 * t68
  t423 = 0.5e1 / 0.9e1 * t404 * t192 + 0.25e2 / 0.81e2 * t408 * params.c1 * t402 * t410 - 0.25e2 / 0.81e2 * t415 * t418 * t61 * t402
  t425 = Dirac(t197)
  t426 = t195 * t425
  t430 = t57 * t202
  t432 = t201 ** 2
  t433 = 0.1e1 / t432
  t434 = t200 * t433
  t437 = -0.5e1 / 0.9e1 * t77 * t402 * t430 - 0.5e1 / 0.9e1 * t434 * t404
  t439 = t204 * t425
  t442 = t423 * t198 - 0.5e1 / 0.9e1 * t426 * t404 + t437 * t206 + 0.5e1 / 0.9e1 * t439 * t404
  t447 = f.my_piecewise3(t158, 0, -0.3e1 / 0.8e1 * t5 * t390 * t208 - t217 - 0.3e1 / 0.8e1 * t5 * t394 * t442)
  t451 = 0.2e1 * t228
  t452 = f.my_piecewise5(t10, 0, t14, 0, t451)
  t456 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t222 * t375 * t26 + 0.4e1 / 0.3e1 * t21 * t452)
  t463 = t5 * t378 * t95 * t86
  t471 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t456 * t30 * t86 - t463 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t379 * t151 - t242 / 0.8e1 + t252 - t254 / 0.8e1)
  t475 = f.my_piecewise5(t14, 0, t10, 0, -t451)
  t479 = f.my_piecewise3(t161, 0, 0.4e1 / 0.9e1 * t348 * t386 * t164 + 0.4e1 / 0.3e1 * t162 * t475)
  t486 = t5 * t389 * t95 * t208
  t493 = t5 * t214 * t442
  t496 = f.my_piecewise3(t158, 0, -0.3e1 / 0.8e1 * t5 * t479 * t30 * t208 - t486 / 0.8e1 - t364 / 0.8e1 + t369 - 0.3e1 / 0.8e1 * t5 * t168 * t442 - t493 / 0.8e1)
  d12 = t156 + t219 + t384 + t447 + t6 * (t471 + t496)
  t501 = t375 ** 2
  t505 = 0.2e1 * t23 + 0.2e1 * t228
  t506 = f.my_piecewise5(t10, 0, t14, 0, t505)
  t510 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t222 * t501 + 0.4e1 / 0.3e1 * t21 * t506)
  t517 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t510 * t30 * t86 - t463 / 0.4e1 + t252)
  t518 = t386 ** 2
  t522 = f.my_piecewise5(t14, 0, t10, 0, -t505)
  t526 = f.my_piecewise3(t161, 0, 0.4e1 / 0.9e1 * t348 * t518 + 0.4e1 / 0.3e1 * t162 * t522)
  t538 = t174 ** 2
  t543 = 0.40e2 / 0.9e1 * tau1 * t399 - 0.11e2 / 0.9e1 * s2 / t170 / t538
  t545 = t543 * t49 * t54
  t548 = t402 ** 2
  t550 = t548 * t113 * t116
  t563 = t179 * t285
  t586 = Dirac(1, t197)
  t621 = f.my_piecewise3(t158, 0, -0.3e1 / 0.8e1 * t5 * t526 * t30 * t208 - t486 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t390 * t442 + t369 - t493 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t394 * ((0.5e1 / 0.9e1 * t545 * t192 + 0.50e2 / 0.81e2 * t550 * params.c1 * t190 * t68 - 0.50e2 / 0.81e2 * t550 * t185 * t417 * t276 + 0.25e2 / 0.81e2 * t408 * params.c1 * t543 * t410 - 0.500e3 / 0.243e3 * t563 * params.c1 * t548 * t417 * t276 + 0.500e3 / 0.243e3 * t563 * t185 / t416 / t189 * t68 * t296 * t548 - 0.25e2 / 0.81e2 * t415 * t418 * t61 * t543) * t198 - 0.10e2 / 0.9e1 * t423 * t425 * t404 + 0.25e2 / 0.81e2 * t195 * t586 * t550 - 0.5e1 / 0.9e1 * t426 * t545 + (-0.5e1 / 0.9e1 * t77 * t543 * t430 + 0.50e2 / 0.81e2 * t77 * t548 * t320 * t433 + 0.50e2 / 0.81e2 * t200 / t432 / t201 * t550 - 0.5e1 / 0.9e1 * t434 * t545) * t206 + 0.10e2 / 0.9e1 * t437 * t425 * t404 - 0.25e2 / 0.81e2 * t204 * t586 * t550 + 0.5e1 / 0.9e1 * t439 * t545))
  d22 = 0.2e1 * t384 + 0.2e1 * t447 + t6 * (t517 + t621)
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
  t43 = t41 * t42
  t44 = 2 ** (0.1e1 / 0.3e1)
  t45 = t2 ** 2
  t47 = 4 ** (0.1e1 / 0.3e1)
  t49 = 0.8e1 / 0.27e2 * t44 * t45 * t47
  t50 = r0 ** (0.1e1 / 0.3e1)
  t51 = t50 ** 2
  t55 = r0 ** 2
  t57 = 0.1e1 / t51 / t55
  t60 = tau0 / t51 / r0 - s0 * t57 / 0.8e1
  t61 = 6 ** (0.1e1 / 0.3e1)
  t63 = jnp.pi ** 2
  t64 = t63 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t66 = 0.1e1 / t65
  t67 = t60 * t61 * t66
  t69 = t61 * t66
  t72 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t60 * t69
  t73 = params.c0 + params.c1 - 0.1e1
  t77 = 0.10e1 + 0.5e1 / 0.9e1 * t73 * t60 * t69
  t78 = 0.1e1 / t77
  t80 = 0.1e1 - t49
  t81 = t72 * t78 * t80
  t84 = t49 + 0.5e1 / 0.9e1 * t67 * t81
  t85 = 0.5e1 / 0.9e1 * t67
  t86 = 0.1e1 - t85
  t87 = Heaviside(t86)
  t89 = 0.1e1 - params.alphainf
  t90 = t89 * t86
  t91 = 0.1e1 + t85
  t92 = 0.1e1 / t91
  t94 = t90 * t92 + 0.1e1
  t96 = Heaviside(-t86)
  t98 = t84 * t87 + t94 * t96
  t104 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t105 = t42 ** 2
  t106 = 0.1e1 / t105
  t107 = t104 * t106
  t111 = t104 * t42
  t116 = 0.1e1 / t51 / t55 / r0
  t119 = -0.5e1 / 0.3e1 * tau0 * t57 + s0 * t116 / 0.3e1
  t121 = t119 * t61 * t66
  t124 = t61 ** 2
  t125 = t60 * t124
  t127 = 0.1e1 / t64 / t63
  t128 = t125 * t127
  t130 = t78 * t80
  t131 = params.c1 * t119 * t130
  t134 = t127 * t72
  t135 = t125 * t134
  t136 = t77 ** 2
  t137 = 0.1e1 / t136
  t138 = t137 * t80
  t140 = t138 * t73 * t119
  t143 = 0.5e1 / 0.9e1 * t121 * t81 + 0.25e2 / 0.81e2 * t128 * t131 - 0.25e2 / 0.81e2 * t135 * t140
  t145 = Dirac(t86)
  t146 = t84 * t145
  t150 = t69 * t92
  t152 = t91 ** 2
  t153 = 0.1e1 / t152
  t154 = t90 * t153
  t157 = -0.5e1 / 0.9e1 * t89 * t119 * t150 - 0.5e1 / 0.9e1 * t154 * t121
  t159 = t94 * t145
  t162 = t143 * t87 - 0.5e1 / 0.9e1 * t146 * t121 + t157 * t96 + 0.5e1 / 0.9e1 * t159 * t121
  t166 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t167 = t166 * f.p.zeta_threshold
  t169 = f.my_piecewise3(t20, t167, t21 * t19)
  t171 = 0.1e1 / t105 / t6
  t172 = t169 * t171
  t176 = t169 * t106
  t180 = t169 * t42
  t183 = t55 ** 2
  t185 = 0.1e1 / t51 / t183
  t188 = 0.40e2 / 0.9e1 * tau0 * t116 - 0.11e2 / 0.9e1 * s0 * t185
  t190 = t188 * t61 * t66
  t193 = t119 ** 2
  t195 = t193 * t124 * t127
  t201 = t80 * t73
  t205 = params.c1 * t188
  t209 = t63 ** 2
  t210 = 0.1e1 / t209
  t211 = t60 * t210
  t219 = 0.1e1 / t136 / t77
  t220 = t219 * t80
  t221 = t73 ** 2
  t230 = 0.5e1 / 0.9e1 * t190 * t81 + 0.50e2 / 0.81e2 * t195 * params.c1 * t78 * t80 - 0.50e2 / 0.81e2 * t195 * t72 * t137 * t201 + 0.25e2 / 0.81e2 * t128 * t205 * t130 - 0.500e3 / 0.243e3 * t211 * params.c1 * t193 * t137 * t201 + 0.500e3 / 0.243e3 * t211 * t72 * t220 * t221 * t193 - 0.25e2 / 0.81e2 * t135 * t138 * t73 * t188
  t232 = t143 * t145
  t235 = Dirac(1, t86)
  t236 = t84 * t235
  t241 = t89 * t188
  t250 = 0.1e1 / t152 / t91
  t251 = t90 * t250
  t256 = -0.5e1 / 0.9e1 * t241 * t150 + 0.50e2 / 0.81e2 * t89 * t193 * t124 * t127 * t153 + 0.50e2 / 0.81e2 * t251 * t195 - 0.5e1 / 0.9e1 * t154 * t190
  t258 = t157 * t145
  t261 = t94 * t235
  t266 = t230 * t87 - 0.10e2 / 0.9e1 * t232 * t121 + 0.25e2 / 0.81e2 * t236 * t195 - 0.5e1 / 0.9e1 * t146 * t190 + t256 * t96 + 0.10e2 / 0.9e1 * t258 * t121 - 0.25e2 / 0.81e2 * t261 * t195 + 0.5e1 / 0.9e1 * t159 * t190
  t271 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t98 - t5 * t107 * t98 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t111 * t162 + t5 * t172 * t98 / 0.12e2 - t5 * t176 * t162 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t180 * t266)
  t273 = r1 <= f.p.dens_threshold
  t274 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t275 = 0.1e1 + t274
  t276 = t275 <= f.p.zeta_threshold
  t277 = t275 ** (0.1e1 / 0.3e1)
  t278 = t277 ** 2
  t279 = 0.1e1 / t278
  t281 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t282 = t281 ** 2
  t286 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t290 = f.my_piecewise3(t276, 0, 0.4e1 / 0.9e1 * t279 * t282 + 0.4e1 / 0.3e1 * t277 * t286)
  t292 = r1 ** (0.1e1 / 0.3e1)
  t293 = t292 ** 2
  t297 = r1 ** 2
  t302 = tau1 / t293 / r1 - s2 / t293 / t297 / 0.8e1
  t304 = t302 * t61 * t66
  t319 = 0.5e1 / 0.9e1 * t304
  t320 = 0.1e1 - t319
  t321 = Heaviside(t320)
  t329 = Heaviside(-t320)
  t331 = (t49 + 0.5e1 / 0.9e1 * t304 * (params.c0 + 0.5e1 / 0.9e1 * params.c1 * t302 * t69) / (0.10e1 + 0.5e1 / 0.9e1 * t73 * t302 * t69) * t80) * t321 + (0.1e1 + t89 * t320 / (0.1e1 + t319)) * t329
  t337 = f.my_piecewise3(t276, 0, 0.4e1 / 0.3e1 * t277 * t281)
  t343 = f.my_piecewise3(t276, t167, t277 * t275)
  t349 = f.my_piecewise3(t273, 0, -0.3e1 / 0.8e1 * t5 * t290 * t42 * t331 - t5 * t337 * t106 * t331 / 0.4e1 + t5 * t343 * t171 * t331 / 0.12e2)
  t359 = t24 ** 2
  t363 = 0.6e1 * t33 - 0.6e1 * t16 / t359
  t364 = f.my_piecewise5(t10, 0, t14, 0, t363)
  t368 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t364)
  t391 = 0.1e1 / t105 / t24
  t409 = -0.440e3 / 0.27e2 * tau0 * t185 + 0.154e3 / 0.27e2 * s0 / t51 / t183 / r0
  t411 = t409 * t61 * t66
  t414 = t188 * t124
  t415 = t414 * t127
  t421 = t193 * t119
  t422 = t421 * t210
  t445 = t136 ** 2
  t467 = 0.5e1 / 0.9e1 * t411 * t81 + 0.50e2 / 0.27e2 * t415 * t131 - 0.50e2 / 0.27e2 * t414 * t134 * t140 - 0.500e3 / 0.81e2 * t422 * params.c1 * t138 * t73 + 0.500e3 / 0.81e2 * t422 * t72 * t220 * t221 + 0.25e2 / 0.81e2 * t128 * params.c1 * t409 * t130 - 0.500e3 / 0.81e2 * t211 * t205 * t140 + 0.2500e4 / 0.729e3 * t211 * params.c1 * t421 * t220 * t221 * t61 * t66 - 0.2500e4 / 0.729e3 * t211 * t72 / t445 * t80 * t221 * t73 * t421 * t61 * t66 + 0.500e3 / 0.81e2 * t211 * t72 * t219 * t80 * t221 * t119 * t188 - 0.25e2 / 0.81e2 * t135 * t138 * t73 * t409
  t477 = Dirac(2, t86)
  t498 = t152 ** 2
  t529 = t467 * t87 - 0.5e1 / 0.3e1 * t230 * t145 * t121 + 0.25e2 / 0.27e2 * t143 * t235 * t195 - 0.5e1 / 0.3e1 * t232 * t190 - 0.250e3 / 0.243e3 * t84 * t477 * t422 + 0.25e2 / 0.27e2 * t236 * t119 * t415 - 0.5e1 / 0.9e1 * t146 * t411 + (-0.5e1 / 0.9e1 * t89 * t409 * t150 + 0.50e2 / 0.27e2 * t241 * t124 * t127 * t153 * t119 - 0.500e3 / 0.81e2 * t89 * t421 * t210 * t250 - 0.500e3 / 0.81e2 * t90 / t498 * t421 * t210 + 0.50e2 / 0.27e2 * t251 * t119 * t124 * t127 * t188 - 0.5e1 / 0.9e1 * t154 * t411) * t96 + 0.5e1 / 0.3e1 * t256 * t145 * t121 - 0.25e2 / 0.27e2 * t157 * t235 * t195 + 0.5e1 / 0.3e1 * t258 * t190 + 0.250e3 / 0.243e3 * t94 * t477 * t422 - 0.25e2 / 0.27e2 * t261 * t119 * t415 + 0.5e1 / 0.9e1 * t159 * t411
  t534 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t368 * t42 * t98 - 0.3e1 / 0.8e1 * t5 * t41 * t106 * t98 - 0.9e1 / 0.8e1 * t5 * t43 * t162 + t5 * t104 * t171 * t98 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t107 * t162 - 0.9e1 / 0.8e1 * t5 * t111 * t266 - 0.5e1 / 0.36e2 * t5 * t169 * t391 * t98 + t5 * t172 * t162 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t176 * t266 - 0.3e1 / 0.8e1 * t5 * t180 * t529)
  t544 = f.my_piecewise5(t14, 0, t10, 0, -t363)
  t548 = f.my_piecewise3(t276, 0, -0.8e1 / 0.27e2 / t278 / t275 * t282 * t281 + 0.4e1 / 0.3e1 * t279 * t281 * t286 + 0.4e1 / 0.3e1 * t277 * t544)
  t566 = f.my_piecewise3(t273, 0, -0.3e1 / 0.8e1 * t5 * t548 * t42 * t331 - 0.3e1 / 0.8e1 * t5 * t290 * t106 * t331 + t5 * t337 * t171 * t331 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t343 * t391 * t331)
  d111 = 0.3e1 * t271 + 0.3e1 * t349 + t6 * (t534 + t566)

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
  t22 = t21 ** 2
  t24 = 0.1e1 / t22 / t19
  t25 = t6 ** 2
  t26 = 0.1e1 / t25
  t28 = -t16 * t26 + t7
  t29 = f.my_piecewise5(t10, 0, t14, 0, t28)
  t30 = t29 ** 2
  t34 = 0.1e1 / t22
  t35 = t34 * t29
  t36 = t25 * t6
  t37 = 0.1e1 / t36
  t40 = 0.2e1 * t16 * t37 - 0.2e1 * t26
  t41 = f.my_piecewise5(t10, 0, t14, 0, t40)
  t44 = t25 ** 2
  t45 = 0.1e1 / t44
  t48 = -0.6e1 * t16 * t45 + 0.6e1 * t37
  t49 = f.my_piecewise5(t10, 0, t14, 0, t48)
  t53 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t24 * t30 * t29 + 0.4e1 / 0.3e1 * t35 * t41 + 0.4e1 / 0.3e1 * t21 * t49)
  t54 = t6 ** (0.1e1 / 0.3e1)
  t55 = t53 * t54
  t56 = 2 ** (0.1e1 / 0.3e1)
  t57 = t2 ** 2
  t59 = 4 ** (0.1e1 / 0.3e1)
  t61 = 0.8e1 / 0.27e2 * t56 * t57 * t59
  t62 = r0 ** (0.1e1 / 0.3e1)
  t63 = t62 ** 2
  t67 = r0 ** 2
  t69 = 0.1e1 / t63 / t67
  t72 = tau0 / t63 / r0 - s0 * t69 / 0.8e1
  t73 = 6 ** (0.1e1 / 0.3e1)
  t75 = jnp.pi ** 2
  t76 = t75 ** (0.1e1 / 0.3e1)
  t77 = t76 ** 2
  t78 = 0.1e1 / t77
  t79 = t72 * t73 * t78
  t81 = t73 * t78
  t84 = params.c0 + 0.5e1 / 0.9e1 * params.c1 * t72 * t81
  t85 = params.c0 + params.c1 - 0.1e1
  t89 = 0.10e1 + 0.5e1 / 0.9e1 * t85 * t72 * t81
  t90 = 0.1e1 / t89
  t92 = 0.1e1 - t61
  t93 = t84 * t90 * t92
  t96 = t61 + 0.5e1 / 0.9e1 * t79 * t93
  t97 = 0.5e1 / 0.9e1 * t79
  t98 = 0.1e1 - t97
  t99 = Heaviside(t98)
  t101 = 0.1e1 - params.alphainf
  t102 = t101 * t98
  t103 = 0.1e1 + t97
  t104 = 0.1e1 / t103
  t106 = t102 * t104 + 0.1e1
  t108 = Heaviside(-t98)
  t110 = t106 * t108 + t96 * t99
  t119 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t120 = t54 ** 2
  t121 = 0.1e1 / t120
  t122 = t119 * t121
  t126 = t119 * t54
  t131 = 0.1e1 / t63 / t67 / r0
  t134 = -0.5e1 / 0.3e1 * tau0 * t69 + s0 * t131 / 0.3e1
  t136 = t134 * t73 * t78
  t139 = t73 ** 2
  t140 = t72 * t139
  t142 = 0.1e1 / t76 / t75
  t143 = t140 * t142
  t145 = t90 * t92
  t146 = params.c1 * t134 * t145
  t149 = t142 * t84
  t150 = t140 * t149
  t151 = t89 ** 2
  t152 = 0.1e1 / t151
  t153 = t152 * t92
  t155 = t153 * t85 * t134
  t158 = 0.5e1 / 0.9e1 * t136 * t93 + 0.25e2 / 0.81e2 * t143 * t146 - 0.25e2 / 0.81e2 * t150 * t155
  t160 = Dirac(t98)
  t161 = t96 * t160
  t165 = t81 * t104
  t167 = t103 ** 2
  t168 = 0.1e1 / t167
  t169 = t102 * t168
  t172 = -0.5e1 / 0.9e1 * t101 * t134 * t165 - 0.5e1 / 0.9e1 * t169 * t136
  t174 = t106 * t160
  t177 = t158 * t99 - 0.5e1 / 0.9e1 * t161 * t136 + t172 * t108 + 0.5e1 / 0.9e1 * t174 * t136
  t183 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t185 = 0.1e1 / t120 / t6
  t186 = t183 * t185
  t190 = t183 * t121
  t194 = t183 * t54
  t197 = t67 ** 2
  t199 = 0.1e1 / t63 / t197
  t202 = 0.40e2 / 0.9e1 * tau0 * t131 - 0.11e2 / 0.9e1 * s0 * t199
  t204 = t202 * t73 * t78
  t207 = t134 ** 2
  t209 = t207 * t139 * t142
  t211 = params.c1 * t90 * t92
  t215 = t92 * t85
  t216 = t84 * t152 * t215
  t219 = params.c1 * t202
  t223 = t75 ** 2
  t224 = 0.1e1 / t223
  t225 = t72 * t224
  t226 = t225 * params.c1
  t228 = t207 * t152 * t215
  t231 = t225 * t84
  t233 = 0.1e1 / t151 / t89
  t234 = t233 * t92
  t235 = t85 ** 2
  t237 = t234 * t235 * t207
  t244 = 0.5e1 / 0.9e1 * t204 * t93 + 0.50e2 / 0.81e2 * t209 * t211 - 0.50e2 / 0.81e2 * t209 * t216 + 0.25e2 / 0.81e2 * t143 * t219 * t145 - 0.500e3 / 0.243e3 * t226 * t228 + 0.500e3 / 0.243e3 * t231 * t237 - 0.25e2 / 0.81e2 * t150 * t153 * t85 * t202
  t246 = t158 * t160
  t249 = Dirac(1, t98)
  t250 = t96 * t249
  t255 = t101 * t202
  t259 = t139 * t142
  t260 = t259 * t168
  t264 = 0.1e1 / t167 / t103
  t265 = t102 * t264
  t270 = -0.5e1 / 0.9e1 * t255 * t165 + 0.50e2 / 0.81e2 * t101 * t207 * t260 + 0.50e2 / 0.81e2 * t265 * t209 - 0.5e1 / 0.9e1 * t169 * t204
  t272 = t172 * t160
  t275 = t106 * t249
  t280 = t244 * t99 - 0.10e2 / 0.9e1 * t246 * t136 + 0.25e2 / 0.81e2 * t250 * t209 - 0.5e1 / 0.9e1 * t161 * t204 + t270 * t108 + 0.10e2 / 0.9e1 * t272 * t136 - 0.25e2 / 0.81e2 * t275 * t209 + 0.5e1 / 0.9e1 * t174 * t204
  t284 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t285 = t284 * f.p.zeta_threshold
  t287 = f.my_piecewise3(t20, t285, t21 * t19)
  t289 = 0.1e1 / t120 / t25
  t290 = t287 * t289
  t294 = t287 * t185
  t298 = t287 * t121
  t302 = t287 * t54
  t307 = 0.1e1 / t63 / t197 / r0
  t310 = -0.440e3 / 0.27e2 * tau0 * t199 + 0.154e3 / 0.27e2 * s0 * t307
  t312 = t310 * t73 * t78
  t315 = t202 * t139
  t316 = t315 * t142
  t322 = t207 * t134
  t323 = t322 * t224
  t332 = params.c1 * t310
  t346 = t151 ** 2
  t347 = 0.1e1 / t346
  t348 = t84 * t347
  t350 = t235 * t85
  t351 = t92 * t350
  t358 = t225 * t84 * t233
  t359 = t92 * t235
  t368 = 0.5e1 / 0.9e1 * t312 * t93 + 0.50e2 / 0.27e2 * t316 * t146 - 0.50e2 / 0.27e2 * t315 * t149 * t155 - 0.500e3 / 0.81e2 * t323 * params.c1 * t153 * t85 + 0.500e3 / 0.81e2 * t323 * t84 * t234 * t235 + 0.25e2 / 0.81e2 * t143 * t332 * t145 - 0.500e3 / 0.81e2 * t225 * t219 * t155 + 0.2500e4 / 0.729e3 * t225 * params.c1 * t322 * t234 * t235 * t73 * t78 - 0.2500e4 / 0.729e3 * t225 * t348 * t351 * t322 * t73 * t78 + 0.500e3 / 0.81e2 * t358 * t359 * t134 * t202 - 0.25e2 / 0.81e2 * t150 * t153 * t85 * t310
  t370 = t244 * t160
  t373 = t158 * t249
  t378 = Dirac(2, t98)
  t379 = t96 * t378
  t382 = t250 * t134
  t387 = t101 * t310
  t392 = t142 * t168 * t134
  t396 = t224 * t264
  t399 = t167 ** 2
  t400 = 0.1e1 / t399
  t405 = t134 * t139
  t412 = -0.5e1 / 0.9e1 * t387 * t165 + 0.50e2 / 0.27e2 * t255 * t139 * t392 - 0.500e3 / 0.81e2 * t101 * t322 * t396 - 0.500e3 / 0.81e2 * t102 * t400 * t322 * t224 + 0.50e2 / 0.27e2 * t265 * t405 * t142 * t202 - 0.5e1 / 0.9e1 * t169 * t312
  t414 = t270 * t160
  t417 = t172 * t249
  t422 = t106 * t378
  t425 = t275 * t134
  t430 = t368 * t99 - 0.5e1 / 0.3e1 * t370 * t136 + 0.25e2 / 0.27e2 * t373 * t209 - 0.5e1 / 0.3e1 * t246 * t204 - 0.250e3 / 0.243e3 * t379 * t323 + 0.25e2 / 0.27e2 * t382 * t316 - 0.5e1 / 0.9e1 * t161 * t312 + t412 * t108 + 0.5e1 / 0.3e1 * t414 * t136 - 0.25e2 / 0.27e2 * t417 * t209 + 0.5e1 / 0.3e1 * t272 * t204 + 0.250e3 / 0.243e3 * t422 * t323 - 0.25e2 / 0.27e2 * t425 * t316 + 0.5e1 / 0.9e1 * t174 * t312
  t435 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t110 - 0.3e1 / 0.8e1 * t5 * t122 * t110 - 0.9e1 / 0.8e1 * t5 * t126 * t177 + t5 * t186 * t110 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t190 * t177 - 0.9e1 / 0.8e1 * t5 * t194 * t280 - 0.5e1 / 0.36e2 * t5 * t290 * t110 + t5 * t294 * t177 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t298 * t280 - 0.3e1 / 0.8e1 * t5 * t302 * t430)
  t437 = r1 <= f.p.dens_threshold
  t438 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t439 = 0.1e1 + t438
  t440 = t439 <= f.p.zeta_threshold
  t441 = t439 ** (0.1e1 / 0.3e1)
  t442 = t441 ** 2
  t444 = 0.1e1 / t442 / t439
  t446 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t447 = t446 ** 2
  t451 = 0.1e1 / t442
  t452 = t451 * t446
  t454 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t458 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t462 = f.my_piecewise3(t440, 0, -0.8e1 / 0.27e2 * t444 * t447 * t446 + 0.4e1 / 0.3e1 * t452 * t454 + 0.4e1 / 0.3e1 * t441 * t458)
  t464 = r1 ** (0.1e1 / 0.3e1)
  t465 = t464 ** 2
  t469 = r1 ** 2
  t474 = tau1 / t465 / r1 - s2 / t465 / t469 / 0.8e1
  t476 = t474 * t73 * t78
  t491 = 0.5e1 / 0.9e1 * t476
  t492 = 0.1e1 - t491
  t493 = Heaviside(t492)
  t501 = Heaviside(-t492)
  t503 = (t61 + 0.5e1 / 0.9e1 * t476 * (params.c0 + 0.5e1 / 0.9e1 * params.c1 * t474 * t81) / (0.10e1 + 0.5e1 / 0.9e1 * t85 * t474 * t81) * t92) * t493 + (0.1e1 + t101 * t492 / (0.1e1 + t491)) * t501
  t512 = f.my_piecewise3(t440, 0, 0.4e1 / 0.9e1 * t451 * t447 + 0.4e1 / 0.3e1 * t441 * t454)
  t519 = f.my_piecewise3(t440, 0, 0.4e1 / 0.3e1 * t441 * t446)
  t525 = f.my_piecewise3(t440, t285, t441 * t439)
  t531 = f.my_piecewise3(t437, 0, -0.3e1 / 0.8e1 * t5 * t462 * t54 * t503 - 0.3e1 / 0.8e1 * t5 * t512 * t121 * t503 + t5 * t519 * t185 * t503 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t525 * t289 * t503)
  t533 = t19 ** 2
  t536 = t30 ** 2
  t542 = t41 ** 2
  t551 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t552 = f.my_piecewise5(t10, 0, t14, 0, t551)
  t556 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t533 * t536 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t542 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t552)
  t570 = t207 * t224 * t202
  t580 = 0.6160e4 / 0.81e2 * tau0 * t307 - 0.2618e4 / 0.81e2 * s0 / t63 / t197 / t67
  t582 = t580 * t73 * t78
  t604 = t202 ** 2
  t608 = t207 ** 2
  t618 = t608 * t224
  t626 = t604 * t139 * t142
  t640 = Dirac(3, t98)
  t643 = t81 * t224
  t648 = t259 * t310
  t651 = 0.20e2 / 0.9e1 * t272 * t312 + 0.500e3 / 0.81e2 * t422 * t570 + 0.5e1 / 0.9e1 * t174 * t582 - 0.5e1 / 0.9e1 * t161 * t582 + 0.20e2 / 0.9e1 * t412 * t160 * t136 + 0.10e2 / 0.3e1 * t414 * t204 - 0.50e2 / 0.27e2 * t270 * t249 * t209 + (-0.5e1 / 0.9e1 * t101 * t580 * t165 + 0.200e3 / 0.81e2 * t387 * t139 * t392 - 0.1000e4 / 0.27e2 * t255 * t396 * t207 + 0.50e2 / 0.27e2 * t101 * t604 * t260 + 0.10000e5 / 0.729e3 * t101 * t608 * t224 * t400 * t73 * t78 + 0.10000e5 / 0.729e3 * t102 / t399 / t103 * t618 * t81 - 0.1000e4 / 0.27e2 * t102 * t400 * t570 + 0.50e2 / 0.27e2 * t265 * t626 + 0.200e3 / 0.81e2 * t265 * t405 * t142 * t310 - 0.5e1 / 0.9e1 * t169 * t582) * t108 - 0.100e3 / 0.27e2 * t417 * t134 * t316 - 0.1250e4 / 0.2187e4 * t106 * t640 * t608 * t643 - 0.25e2 / 0.27e2 * t275 * t626 - 0.100e3 / 0.81e2 * t425 * t648
  t673 = t202 * t224
  t739 = t235 ** 2
  t746 = 0.5e1 / 0.9e1 * t582 * t93 + 0.25e2 / 0.81e2 * t143 * params.c1 * t580 * t145 + 0.200e3 / 0.81e2 * t648 * t146 + 0.50e2 / 0.27e2 * t626 * t211 - 0.1000e4 / 0.27e2 * t673 * params.c1 * t228 + 0.1000e4 / 0.27e2 * t673 * t84 * t237 - 0.25e2 / 0.81e2 * t150 * t153 * t85 * t580 + 0.10000e5 / 0.729e3 * t618 * params.c1 * t233 * t359 * t81 - 0.10000e5 / 0.729e3 * t618 * t348 * t351 * t81 - 0.2000e4 / 0.243e3 * t225 * t332 * t155 - 0.500e3 / 0.81e2 * t226 * t604 * t152 * t215 + 0.500e3 / 0.81e2 * t231 * t234 * t235 * t604 + 0.2000e4 / 0.243e3 * t358 * t359 * t134 * t310 + 0.5000e4 / 0.243e3 * t225 * t219 * t233 * t359 * t207 * t73 * t78 - 0.5000e4 / 0.243e3 * t225 * t348 * t92 * t350 * t207 * t204 - 0.200e3 / 0.81e2 * t310 * t139 * t149 * t155 - 0.50e2 / 0.27e2 * t626 * t216 - 0.50000e5 / 0.6561e4 * t225 * params.c1 * t608 * t347 * t92 * t350 * t139 * t142 + 0.50000e5 / 0.6561e4 * t225 * t84 / t346 / t89 * t92 * t739 * t608 * t139 * t142
  t766 = 0.1250e4 / 0.2187e4 * t96 * t640 * t608 * t643 + 0.25e2 / 0.27e2 * t250 * t626 + 0.100e3 / 0.81e2 * t382 * t648 + 0.100e3 / 0.27e2 * t373 * t134 * t316 + t746 * t99 - 0.10e2 / 0.3e1 * t370 * t204 + 0.50e2 / 0.27e2 * t244 * t249 * t209 - 0.20e2 / 0.9e1 * t246 * t312 - 0.500e3 / 0.81e2 * t379 * t570 - 0.20e2 / 0.9e1 * t368 * t160 * t136 - 0.1000e4 / 0.243e3 * t158 * t378 * t323 + 0.1000e4 / 0.243e3 * t172 * t378 * t323
  t804 = 0.1e1 / t120 / t36
  t809 = -0.3e1 / 0.8e1 * t5 * t556 * t54 * t110 - 0.3e1 / 0.2e1 * t5 * t55 * t177 - 0.3e1 / 0.2e1 * t5 * t122 * t177 - 0.3e1 / 0.8e1 * t5 * t302 * (t651 + t766) - t5 * t53 * t121 * t110 / 0.2e1 + t5 * t119 * t185 * t110 / 0.2e1 - t5 * t298 * t430 / 0.2e1 + t5 * t294 * t280 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t290 * t177 - 0.9e1 / 0.4e1 * t5 * t126 * t280 + t5 * t186 * t177 - 0.3e1 / 0.2e1 * t5 * t190 * t280 - 0.3e1 / 0.2e1 * t5 * t194 * t430 - 0.5e1 / 0.9e1 * t5 * t183 * t289 * t110 + 0.10e2 / 0.27e2 * t5 * t287 * t804 * t110
  t810 = f.my_piecewise3(t1, 0, t809)
  t811 = t439 ** 2
  t814 = t447 ** 2
  t820 = t454 ** 2
  t826 = f.my_piecewise5(t14, 0, t10, 0, -t551)
  t830 = f.my_piecewise3(t440, 0, 0.40e2 / 0.81e2 / t442 / t811 * t814 - 0.16e2 / 0.9e1 * t444 * t447 * t454 + 0.4e1 / 0.3e1 * t451 * t820 + 0.16e2 / 0.9e1 * t452 * t458 + 0.4e1 / 0.3e1 * t441 * t826)
  t852 = f.my_piecewise3(t437, 0, -0.3e1 / 0.8e1 * t5 * t830 * t54 * t503 - t5 * t462 * t121 * t503 / 0.2e1 + t5 * t512 * t185 * t503 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t519 * t289 * t503 + 0.10e2 / 0.27e2 * t5 * t525 * t804 * t503)
  d1111 = 0.4e1 * t435 + 0.4e1 * t531 + t6 * (t810 + t852)

  res = {'v4rho4': d1111}
  return res
