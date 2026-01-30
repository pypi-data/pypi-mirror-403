"""Generated from mgga_k_lk.mpl."""

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

  lk_p = lambda x: X2S ** 2 * x ** 2

  lk_q = lambda u: X2S ** 2 * u

  lk_delta = lambda p, q: 8 / 81 * q ** 2 - 1 / 9 * p * q + 8 / 243 * p ** 2

  lk_f0 = lambda x1, x2: 1 + params_kappa * (2 - 1 / (1 + x1 / params_kappa) - 1 / (1 + x2 / params_kappa))

  lk_x1 = lambda p, q: 5 / 27 * p + lk_delta(p, q) + (5 / 27 * p) ** 2 / params_kappa

  lk_x2 = lambda p, q: 2 * (5 / 27 * p) * lk_delta(p, q) / params_kappa + (5 / 27 * p) ** 3 / params_kappa ** 2

  lk_f = lambda x, u: lk_f0(lk_x1(lk_p(x), lk_q(u)), lk_x2(lk_p(x), lk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, lk_f, rs, z, xs0, xs1, u0, u1)

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

  lk_p = lambda x: X2S ** 2 * x ** 2

  lk_q = lambda u: X2S ** 2 * u

  lk_delta = lambda p, q: 8 / 81 * q ** 2 - 1 / 9 * p * q + 8 / 243 * p ** 2

  lk_f0 = lambda x1, x2: 1 + params_kappa * (2 - 1 / (1 + x1 / params_kappa) - 1 / (1 + x2 / params_kappa))

  lk_x1 = lambda p, q: 5 / 27 * p + lk_delta(p, q) + (5 / 27 * p) ** 2 / params_kappa

  lk_x2 = lambda p, q: 2 * (5 / 27 * p) * lk_delta(p, q) / params_kappa + (5 / 27 * p) ** 3 / params_kappa ** 2

  lk_f = lambda x, u: lk_f0(lk_x1(lk_p(x), lk_q(u)), lk_x2(lk_p(x), lk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, lk_f, rs, z, xs0, xs1, u0, u1)

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

  lk_p = lambda x: X2S ** 2 * x ** 2

  lk_q = lambda u: X2S ** 2 * u

  lk_delta = lambda p, q: 8 / 81 * q ** 2 - 1 / 9 * p * q + 8 / 243 * p ** 2

  lk_f0 = lambda x1, x2: 1 + params_kappa * (2 - 1 / (1 + x1 / params_kappa) - 1 / (1 + x2 / params_kappa))

  lk_x1 = lambda p, q: 5 / 27 * p + lk_delta(p, q) + (5 / 27 * p) ** 2 / params_kappa

  lk_x2 = lambda p, q: 2 * (5 / 27 * p) * lk_delta(p, q) / params_kappa + (5 / 27 * p) ** 3 / params_kappa ** 2

  lk_f = lambda x, u: lk_f0(lk_x1(lk_p(x), lk_q(u)), lk_x2(lk_p(x), lk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, lk_f, rs, z, xs0, xs1, u0, u1)

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
  t46 = t32 ** 2
  t49 = t46 / t34 / t33
  t50 = l0 ** 2
  t51 = t38 * r0
  t53 = 0.1e1 / t39 / t51
  t56 = t49 * t50 * t53 / 0.5832e4
  t57 = t38 ** 2
  t59 = 0.1e1 / t39 / t57
  t60 = s0 * t59
  t63 = t49 * t60 * l0 / 0.5184e4
  t64 = s0 ** 2
  t67 = 0.1e1 / t39 / t57 / r0
  t68 = t64 * t67
  t70 = t49 * t68 / 0.17496e5
  t71 = 0.1e1 / params.kappa
  t77 = 0.1e1 + (0.5e1 / 0.648e3 * t37 * t43 + t56 - t63 + t70 + 0.25e2 / 0.419904e6 * t49 * t68 * t71) * t71
  t79 = t37 * s0
  t80 = t56 - t63 + t70
  t82 = t42 * t80 * t71
  t85 = t33 ** 2
  t86 = 0.1e1 / t85
  t88 = t86 * t64 * s0
  t89 = t57 ** 2
  t91 = params.kappa ** 2
  t92 = 0.1e1 / t91
  t93 = 0.1e1 / t89 * t92
  t98 = 0.1e1 + (0.5e1 / 0.324e3 * t79 * t82 + 0.125e3 / 0.45349632e8 * t88 * t93) * t71
  t102 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t77 - 0.1e1 / t98)
  t106 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t28 * t30 * t102)
  t107 = r1 <= f.p.dens_threshold
  t108 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t109 = 0.1e1 + t108
  t110 = t109 <= f.p.zeta_threshold
  t111 = t109 ** (0.1e1 / 0.3e1)
  t112 = t111 ** 2
  t114 = f.my_piecewise3(t110, t24, t112 * t109)
  t116 = r1 ** 2
  t117 = r1 ** (0.1e1 / 0.3e1)
  t118 = t117 ** 2
  t120 = 0.1e1 / t118 / t116
  t121 = s2 * t120
  t124 = l1 ** 2
  t125 = t116 * r1
  t127 = 0.1e1 / t117 / t125
  t130 = t49 * t124 * t127 / 0.5832e4
  t131 = t116 ** 2
  t133 = 0.1e1 / t117 / t131
  t134 = s2 * t133
  t137 = t49 * t134 * l1 / 0.5184e4
  t138 = s2 ** 2
  t141 = 0.1e1 / t117 / t131 / r1
  t142 = t138 * t141
  t144 = t49 * t142 / 0.17496e5
  t150 = 0.1e1 + (0.5e1 / 0.648e3 * t37 * t121 + t130 - t137 + t144 + 0.25e2 / 0.419904e6 * t49 * t142 * t71) * t71
  t152 = t37 * s2
  t153 = t130 - t137 + t144
  t155 = t120 * t153 * t71
  t159 = t86 * t138 * s2
  t160 = t131 ** 2
  t162 = 0.1e1 / t160 * t92
  t167 = 0.1e1 + (0.5e1 / 0.324e3 * t152 * t155 + 0.125e3 / 0.45349632e8 * t159 * t162) * t71
  t171 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t150 - 0.1e1 / t167)
  t175 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t6 * t114 * t30 * t171)
  t176 = t7 ** 2
  t178 = t17 / t176
  t179 = t8 - t178
  t180 = f.my_piecewise5(t11, 0, t15, 0, t179)
  t183 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t180)
  t188 = 0.1e1 / t29
  t192 = t6 * t28 * t188 * t102 / 0.10e2
  t193 = t6 * t28
  t194 = t30 * params.kappa
  t195 = t77 ** 2
  t196 = 0.1e1 / t195
  t198 = 0.1e1 / t40 / t51
  t204 = 0.5e1 / 0.8748e4 * t49 * t50 * t59
  t205 = s0 * t67
  t208 = 0.13e2 / 0.15552e5 * t49 * t205 * l0
  t212 = t64 / t39 / t57 / t38
  t214 = 0.2e1 / 0.6561e4 * t49 * t212
  t221 = t98 ** 2
  t222 = 0.1e1 / t221
  t245 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t183 * t30 * t102 + t192 + 0.3e1 / 0.20e2 * t193 * t194 * (t196 * (-0.5e1 / 0.243e3 * t37 * s0 * t198 - t204 + t208 - t214 - 0.25e2 / 0.78732e5 * t49 * t212 * t71) * t71 + t222 * (-0.10e2 / 0.243e3 * t79 * t198 * t80 * t71 + 0.5e1 / 0.324e3 * t79 * t42 * (-t204 + t208 - t214) * t71 - 0.125e3 / 0.5668704e7 * t88 / t89 / r0 * t92) * t71))
  t247 = f.my_piecewise5(t15, 0, t11, 0, -t179)
  t250 = f.my_piecewise3(t110, 0, 0.5e1 / 0.3e1 * t112 * t247)
  t258 = t6 * t114 * t188 * t171 / 0.10e2
  t260 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t6 * t250 * t30 * t171 + t258)
  vrho_0_ = t106 + t175 + t7 * (t245 + t260)
  t263 = -t8 - t178
  t264 = f.my_piecewise5(t11, 0, t15, 0, t263)
  t267 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t264)
  t273 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t267 * t30 * t102 + t192)
  t275 = f.my_piecewise5(t15, 0, t11, 0, -t263)
  t278 = f.my_piecewise3(t110, 0, 0.5e1 / 0.3e1 * t112 * t275)
  t283 = t6 * t114
  t284 = t150 ** 2
  t285 = 0.1e1 / t284
  t287 = 0.1e1 / t118 / t125
  t293 = 0.5e1 / 0.8748e4 * t49 * t124 * t133
  t294 = s2 * t141
  t297 = 0.13e2 / 0.15552e5 * t49 * t294 * l1
  t301 = t138 / t117 / t131 / t116
  t303 = 0.2e1 / 0.6561e4 * t49 * t301
  t310 = t167 ** 2
  t311 = 0.1e1 / t310
  t334 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t6 * t278 * t30 * t171 + t258 + 0.3e1 / 0.20e2 * t283 * t194 * (t285 * (-0.5e1 / 0.243e3 * t37 * s2 * t287 - t293 + t297 - t303 - 0.25e2 / 0.78732e5 * t49 * t301 * t71) * t71 + t311 * (-0.10e2 / 0.243e3 * t152 * t287 * t153 * t71 + 0.5e1 / 0.324e3 * t152 * t120 * (-t293 + t297 - t303) * t71 - 0.125e3 / 0.5668704e7 * t159 / t160 / r1 * t92) * t71))
  vrho_1_ = t106 + t175 + t7 * (t273 + t334)
  t341 = t49 * t59 * l0 / 0.5184e4
  t343 = t49 * t205 / 0.8748e4
  t367 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t193 * t194 * (t196 * (0.5e1 / 0.648e3 * t37 * t42 - t341 + t343 + 0.25e2 / 0.209952e6 * t49 * t205 * t71) * t71 + t222 * (0.5e1 / 0.324e3 * t37 * t82 + 0.5e1 / 0.324e3 * t79 * t42 * (-t341 + t343) * t71 + 0.125e3 / 0.15116544e8 * t86 * t64 * t93) * t71))
  vsigma_0_ = t7 * t367
  vsigma_1_ = 0.0e0
  t372 = t49 * t133 * l1 / 0.5184e4
  t374 = t49 * t294 / 0.8748e4
  t398 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t283 * t194 * (t285 * (0.5e1 / 0.648e3 * t37 * t120 - t372 + t374 + 0.25e2 / 0.209952e6 * t49 * t294 * t71) * t71 + t311 * (0.5e1 / 0.324e3 * t37 * t155 + 0.5e1 / 0.324e3 * t152 * t120 * (-t372 + t374) * t71 + 0.125e3 / 0.15116544e8 * t86 * t138 * t162) * t71))
  vsigma_2_ = t7 * t398
  t404 = t49 * l0 * t53 / 0.2916e4 - t49 * t60 / 0.5184e4
  t417 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t193 * t194 * (t196 * t404 * t71 + 0.5e1 / 0.324e3 * t222 * t32 * t36 * t43 * t404 * t92))
  vlapl_0_ = t7 * t417
  t423 = t49 * l1 * t127 / 0.2916e4 - t49 * t134 / 0.5184e4
  t436 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t283 * t194 * (t285 * t423 * t71 + 0.5e1 / 0.324e3 * t311 * t32 * t36 * t121 * t423 * t92))
  vlapl_1_ = t7 * t436
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

  lk_p = lambda x: X2S ** 2 * x ** 2

  lk_q = lambda u: X2S ** 2 * u

  lk_delta = lambda p, q: 8 / 81 * q ** 2 - 1 / 9 * p * q + 8 / 243 * p ** 2

  lk_f0 = lambda x1, x2: 1 + params_kappa * (2 - 1 / (1 + x1 / params_kappa) - 1 / (1 + x2 / params_kappa))

  lk_x1 = lambda p, q: 5 / 27 * p + lk_delta(p, q) + (5 / 27 * p) ** 2 / params_kappa

  lk_x2 = lambda p, q: 2 * (5 / 27 * p) * lk_delta(p, q) / params_kappa + (5 / 27 * p) ** 3 / params_kappa ** 2

  lk_f = lambda x, u: lk_f0(lk_x1(lk_p(x), lk_q(u)), lk_x2(lk_p(x), lk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, lk_f, rs, z, xs0, xs1, u0, u1)

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
  t39 = t24 ** 2
  t42 = t39 / t26 / t25
  t43 = l0 ** 2
  t44 = t43 * t30
  t45 = t33 * r0
  t47 = 0.1e1 / t21 / t45
  t50 = t42 * t44 * t47 / 0.2916e4
  t51 = t42 * s0
  t52 = t33 ** 2
  t54 = 0.1e1 / t21 / t52
  t56 = t30 * t54 * l0
  t58 = t51 * t56 / 0.2592e4
  t59 = s0 ** 2
  t60 = t59 * t30
  t63 = 0.1e1 / t21 / t52 / r0
  t66 = t42 * t60 * t63 / 0.8748e4
  t67 = t42 * t59
  t68 = t30 * t63
  t69 = 0.1e1 / params.kappa
  t70 = t68 * t69
  t75 = 0.1e1 + (0.5e1 / 0.648e3 * t29 * t32 * t35 + t50 - t58 + t66 + 0.25e2 / 0.209952e6 * t67 * t70) * t69
  t77 = t29 * s0
  t78 = t31 * t35
  t79 = t50 - t58 + t66
  t80 = t79 * t69
  t84 = t25 ** 2
  t85 = 0.1e1 / t84
  t87 = t85 * t59 * s0
  t88 = t52 ** 2
  t90 = params.kappa ** 2
  t91 = 0.1e1 / t90
  t92 = 0.1e1 / t88 * t91
  t97 = 0.1e1 + (0.5e1 / 0.324e3 * t77 * t78 * t80 + 0.125e3 / 0.11337408e8 * t87 * t92) * t69
  t101 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t75 - 0.1e1 / t97)
  t105 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t20 * t22 * t101)
  t111 = t7 * t20
  t112 = t22 * params.kappa
  t113 = t75 ** 2
  t114 = 0.1e1 / t113
  t116 = 0.1e1 / t22 / t45
  t122 = 0.5e1 / 0.4374e4 * t42 * t44 * t54
  t125 = 0.13e2 / 0.7776e4 * t51 * t68 * l0
  t128 = 0.1e1 / t21 / t52 / t33
  t131 = 0.4e1 / 0.6561e4 * t42 * t60 * t128
  t139 = t97 ** 2
  t140 = 0.1e1 / t139
  t163 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t101 / 0.10e2 + 0.3e1 / 0.20e2 * t111 * t112 * (t114 * (-0.5e1 / 0.243e3 * t29 * t32 * t116 - t122 + t125 - t131 - 0.25e2 / 0.39366e5 * t67 * t30 * t128 * t69) * t69 + t140 * (-0.10e2 / 0.243e3 * t77 * t31 * t116 * t80 + 0.5e1 / 0.324e3 * t77 * t78 * (-t122 + t125 - t131) * t69 - 0.125e3 / 0.1417176e7 * t87 / t88 / r0 * t91) * t69))
  vrho_0_ = 0.2e1 * r0 * t163 + 0.2e1 * t105
  t169 = t42 * t56 / 0.2592e4
  t170 = s0 * t30
  t173 = t42 * t170 * t63 / 0.4374e4
  t199 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t111 * t112 * (t114 * (0.5e1 / 0.648e3 * t29 * t78 - t169 + t173 + 0.25e2 / 0.104976e6 * t51 * t70) * t69 + t140 * (0.5e1 / 0.324e3 * t29 * t31 * t35 * t79 * t69 + 0.5e1 / 0.324e3 * t77 * t78 * (-t169 + t173) * t69 + 0.125e3 / 0.3779136e7 * t85 * t59 * t92) * t69))
  vsigma_0_ = 0.2e1 * r0 * t199
  t208 = t42 * l0 * t30 * t47 / 0.1458e4 - t42 * t170 * t54 / 0.2592e4
  t222 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t111 * t112 * (t114 * t208 * t69 + 0.5e1 / 0.324e3 * t140 * t24 * t28 * s0 * t78 * t208 * t91))
  vlapl_0_ = 0.2e1 * r0 * t222
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
  t22 = 0.1e1 / t21
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t29 = t24 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t34 = t21 ** 2
  t36 = 0.1e1 / t34 / t33
  t40 = t24 ** 2
  t43 = t40 / t26 / t25
  t44 = l0 ** 2
  t45 = t44 * t30
  t46 = t33 * r0
  t51 = t43 * t45 / t21 / t46 / 0.2916e4
  t52 = t43 * s0
  t53 = t33 ** 2
  t55 = 0.1e1 / t21 / t53
  t59 = t52 * t30 * t55 * l0 / 0.2592e4
  t60 = s0 ** 2
  t61 = t60 * t30
  t64 = 0.1e1 / t21 / t53 / r0
  t67 = t43 * t61 * t64 / 0.8748e4
  t68 = t43 * t60
  t69 = t30 * t64
  t70 = 0.1e1 / params.kappa
  t76 = 0.1e1 + (0.5e1 / 0.648e3 * t29 * t32 * t36 + t51 - t59 + t67 + 0.25e2 / 0.209952e6 * t68 * t69 * t70) * t70
  t78 = t29 * s0
  t79 = t31 * t36
  t81 = (t51 - t59 + t67) * t70
  t85 = t25 ** 2
  t88 = 0.1e1 / t85 * t60 * s0
  t89 = t53 ** 2
  t91 = params.kappa ** 2
  t92 = 0.1e1 / t91
  t98 = 0.1e1 + (0.5e1 / 0.324e3 * t78 * t79 * t81 + 0.125e3 / 0.11337408e8 * t88 / t89 * t92) * t70
  t102 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t76 - 0.1e1 / t98)
  t106 = t7 * t20
  t107 = t34 * params.kappa
  t108 = t76 ** 2
  t109 = 0.1e1 / t108
  t111 = 0.1e1 / t34 / t46
  t117 = 0.5e1 / 0.4374e4 * t43 * t45 * t55
  t120 = 0.13e2 / 0.7776e4 * t52 * t69 * l0
  t123 = 0.1e1 / t21 / t53 / t33
  t126 = 0.4e1 / 0.6561e4 * t43 * t61 * t123
  t127 = t30 * t123
  t131 = -0.5e1 / 0.243e3 * t29 * t32 * t111 - t117 + t120 - t126 - 0.25e2 / 0.39366e5 * t68 * t127 * t70
  t134 = t98 ** 2
  t135 = 0.1e1 / t134
  t136 = t31 * t111
  t141 = (-t117 + t120 - t126) * t70
  t150 = -0.10e2 / 0.243e3 * t78 * t136 * t81 + 0.5e1 / 0.324e3 * t78 * t79 * t141 - 0.125e3 / 0.1417176e7 * t88 / t89 / r0 * t92
  t153 = t109 * t131 * t70 + t135 * t150 * t70
  t158 = f.my_piecewise3(t2, 0, t7 * t20 * t22 * t102 / 0.10e2 + 0.3e1 / 0.20e2 * t106 * t107 * t153)
  t172 = t131 ** 2
  t177 = 0.1e1 / t34 / t53
  t183 = 0.65e2 / 0.13122e5 * t43 * t45 * t64
  t186 = 0.13e2 / 0.1458e4 * t52 * t127 * l0
  t189 = 0.1e1 / t21 / t53 / t46
  t192 = 0.76e2 / 0.19683e5 * t43 * t61 * t189
  t202 = t150 ** 2
  t231 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t102 / 0.30e2 + t106 * t22 * params.kappa * t153 / 0.5e1 + 0.3e1 / 0.20e2 * t106 * t107 * (-0.2e1 / t108 / t76 * t172 * t92 + t109 * (0.55e2 / 0.729e3 * t29 * t32 * t177 + t183 - t186 + t192 + 0.475e3 / 0.118098e6 * t68 * t30 * t189 * t70) * t70 - 0.2e1 / t134 / t98 * t202 * t92 + t135 * (0.110e3 / 0.729e3 * t78 * t31 * t177 * t81 - 0.20e2 / 0.243e3 * t78 * t136 * t141 + 0.5e1 / 0.324e3 * t78 * t79 * (t183 - t186 + t192) * t70 + 0.125e3 / 0.157464e6 * t88 / t89 / t33 * t92) * t70))
  v2rho2_0_ = 0.2e1 * r0 * t231 + 0.4e1 * t158
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
  t23 = 0.1e1 / t21 / r0
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t30 = t25 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t37 = 0.1e1 / t35 / t34
  t41 = t25 ** 2
  t44 = t41 / t27 / t26
  t45 = l0 ** 2
  t46 = t45 * t31
  t47 = t34 * r0
  t52 = t44 * t46 / t21 / t47 / 0.2916e4
  t53 = t44 * s0
  t54 = t34 ** 2
  t56 = 0.1e1 / t21 / t54
  t60 = t53 * t31 * t56 * l0 / 0.2592e4
  t61 = s0 ** 2
  t62 = t61 * t31
  t63 = t54 * r0
  t65 = 0.1e1 / t21 / t63
  t68 = t44 * t62 * t65 / 0.8748e4
  t69 = t44 * t61
  t70 = t31 * t65
  t71 = 0.1e1 / params.kappa
  t77 = 0.1e1 + (0.5e1 / 0.648e3 * t30 * t33 * t37 + t52 - t60 + t68 + 0.25e2 / 0.209952e6 * t69 * t70 * t71) * t71
  t79 = t30 * s0
  t80 = t32 * t37
  t82 = (t52 - t60 + t68) * t71
  t86 = t26 ** 2
  t89 = 0.1e1 / t86 * t61 * s0
  t90 = t54 ** 2
  t92 = params.kappa ** 2
  t93 = 0.1e1 / t92
  t99 = 0.1e1 + (0.5e1 / 0.324e3 * t79 * t80 * t82 + 0.125e3 / 0.11337408e8 * t89 / t90 * t93) * t71
  t103 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t77 - 0.1e1 / t99)
  t107 = t7 * t20
  t109 = 0.1e1 / t21 * params.kappa
  t110 = t77 ** 2
  t111 = 0.1e1 / t110
  t113 = 0.1e1 / t35 / t47
  t119 = 0.5e1 / 0.4374e4 * t44 * t46 * t56
  t122 = 0.13e2 / 0.7776e4 * t53 * t70 * l0
  t125 = 0.1e1 / t21 / t54 / t34
  t128 = 0.4e1 / 0.6561e4 * t44 * t62 * t125
  t129 = t31 * t125
  t133 = -0.5e1 / 0.243e3 * t30 * t33 * t113 - t119 + t122 - t128 - 0.25e2 / 0.39366e5 * t69 * t129 * t71
  t136 = t99 ** 2
  t137 = 0.1e1 / t136
  t138 = t32 * t113
  t143 = (-t119 + t122 - t128) * t71
  t152 = -0.10e2 / 0.243e3 * t79 * t138 * t82 + 0.5e1 / 0.324e3 * t79 * t80 * t143 - 0.125e3 / 0.1417176e7 * t89 / t90 / r0 * t93
  t155 = t111 * t133 * t71 + t137 * t152 * t71
  t159 = t35 * params.kappa
  t161 = 0.1e1 / t110 / t77
  t162 = t133 ** 2
  t167 = 0.1e1 / t35 / t54
  t173 = 0.65e2 / 0.13122e5 * t44 * t46 * t65
  t176 = 0.13e2 / 0.1458e4 * t53 * t129 * l0
  t179 = 0.1e1 / t21 / t54 / t47
  t182 = 0.76e2 / 0.19683e5 * t44 * t62 * t179
  t183 = t31 * t179
  t187 = 0.55e2 / 0.729e3 * t30 * t33 * t167 + t173 - t176 + t182 + 0.475e3 / 0.118098e6 * t69 * t183 * t71
  t191 = 0.1e1 / t136 / t99
  t192 = t152 ** 2
  t196 = t32 * t167
  t204 = (t173 - t176 + t182) * t71
  t213 = 0.110e3 / 0.729e3 * t79 * t196 * t82 - 0.20e2 / 0.243e3 * t79 * t138 * t143 + 0.5e1 / 0.324e3 * t79 * t80 * t204 + 0.125e3 / 0.157464e6 * t89 / t90 / t34 * t93
  t216 = t111 * t187 * t71 + t137 * t213 * t71 - 0.2e1 * t161 * t162 * t93 - 0.2e1 * t191 * t192 * t93
  t221 = f.my_piecewise3(t2, 0, -t7 * t20 * t23 * t103 / 0.30e2 + t107 * t109 * t155 / 0.5e1 + 0.3e1 / 0.20e2 * t107 * t159 * t216)
  t236 = t110 ** 2
  t241 = 0.1e1 / t92 / params.kappa
  t249 = 0.1e1 / t35 / t63
  t255 = 0.520e3 / 0.19683e5 * t44 * t46 * t125
  t258 = 0.247e3 / 0.4374e4 * t53 * t183 * l0
  t260 = 0.1e1 / t21 / t90
  t263 = 0.1672e4 / 0.59049e5 * t44 * t62 * t260
  t271 = t136 ** 2
  t309 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t103 - t107 * t23 * params.kappa * t155 / 0.10e2 + 0.3e1 / 0.10e2 * t107 * t109 * t216 + 0.3e1 / 0.20e2 * t107 * t159 * (0.6e1 / t236 * t162 * t133 * t241 - 0.6e1 * t161 * t133 * t93 * t187 + t111 * (-0.770e3 / 0.2187e4 * t30 * t33 * t249 - t255 + t258 - t263 - 0.5225e4 / 0.177147e6 * t69 * t31 * t260 * t71) * t71 + 0.6e1 / t271 * t192 * t152 * t241 - 0.6e1 * t191 * t152 * t93 * t213 + t137 * (-0.1540e4 / 0.2187e4 * t79 * t32 * t249 * t82 + 0.110e3 / 0.243e3 * t79 * t196 * t143 - 0.10e2 / 0.81e2 * t79 * t138 * t204 + 0.5e1 / 0.324e3 * t79 * t80 * (-t255 + t258 - t263) * t71 - 0.625e3 / 0.78732e5 * t89 / t90 / t47 * t93) * t71))
  v3rho3_0_ = 0.2e1 * r0 * t309 + 0.6e1 * t221

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
  t24 = 0.1e1 / t22 / t21
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t31 = t26 / t29
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = t22 ** 2
  t37 = 0.1e1 / t35 / t21
  t41 = t26 ** 2
  t44 = t41 / t28 / t27
  t45 = l0 ** 2
  t46 = t45 * t32
  t47 = t21 * r0
  t49 = 0.1e1 / t22 / t47
  t52 = t44 * t46 * t49 / 0.2916e4
  t53 = t44 * s0
  t54 = t21 ** 2
  t56 = 0.1e1 / t22 / t54
  t60 = t53 * t32 * t56 * l0 / 0.2592e4
  t61 = s0 ** 2
  t62 = t61 * t32
  t63 = t54 * r0
  t65 = 0.1e1 / t22 / t63
  t68 = t44 * t62 * t65 / 0.8748e4
  t69 = t44 * t61
  t70 = t32 * t65
  t71 = 0.1e1 / params.kappa
  t77 = 0.1e1 + (0.5e1 / 0.648e3 * t31 * t34 * t37 + t52 - t60 + t68 + 0.25e2 / 0.209952e6 * t69 * t70 * t71) * t71
  t79 = t31 * s0
  t80 = t33 * t37
  t82 = (t52 - t60 + t68) * t71
  t86 = t27 ** 2
  t89 = 0.1e1 / t86 * t61 * s0
  t90 = t54 ** 2
  t92 = params.kappa ** 2
  t93 = 0.1e1 / t92
  t99 = 0.1e1 + (0.5e1 / 0.324e3 * t79 * t80 * t82 + 0.125e3 / 0.11337408e8 * t89 / t90 * t93) * t71
  t103 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t77 - 0.1e1 / t99)
  t107 = t7 * t20
  t110 = 0.1e1 / t22 / r0 * params.kappa
  t111 = t77 ** 2
  t112 = 0.1e1 / t111
  t114 = 0.1e1 / t35 / t47
  t120 = 0.5e1 / 0.4374e4 * t44 * t46 * t56
  t123 = 0.13e2 / 0.7776e4 * t53 * t70 * l0
  t124 = t54 * t21
  t126 = 0.1e1 / t22 / t124
  t129 = 0.4e1 / 0.6561e4 * t44 * t62 * t126
  t130 = t32 * t126
  t134 = -0.5e1 / 0.243e3 * t31 * t34 * t114 - t120 + t123 - t129 - 0.25e2 / 0.39366e5 * t69 * t130 * t71
  t137 = t99 ** 2
  t138 = 0.1e1 / t137
  t139 = t33 * t114
  t144 = (-t120 + t123 - t129) * t71
  t148 = t90 * r0
  t153 = -0.10e2 / 0.243e3 * t79 * t139 * t82 + 0.5e1 / 0.324e3 * t79 * t80 * t144 - 0.125e3 / 0.1417176e7 * t89 / t148 * t93
  t156 = t112 * t134 * t71 + t138 * t153 * t71
  t161 = 0.1e1 / t22 * params.kappa
  t163 = 0.1e1 / t111 / t77
  t164 = t134 ** 2
  t169 = 0.1e1 / t35 / t54
  t175 = 0.65e2 / 0.13122e5 * t44 * t46 * t65
  t178 = 0.13e2 / 0.1458e4 * t53 * t130 * l0
  t181 = 0.1e1 / t22 / t54 / t47
  t184 = 0.76e2 / 0.19683e5 * t44 * t62 * t181
  t185 = t32 * t181
  t189 = 0.55e2 / 0.729e3 * t31 * t34 * t169 + t175 - t178 + t184 + 0.475e3 / 0.118098e6 * t69 * t185 * t71
  t193 = 0.1e1 / t137 / t99
  t194 = t153 ** 2
  t198 = t33 * t169
  t206 = (t175 - t178 + t184) * t71
  t215 = 0.110e3 / 0.729e3 * t79 * t198 * t82 - 0.20e2 / 0.243e3 * t79 * t139 * t144 + 0.5e1 / 0.324e3 * t79 * t80 * t206 + 0.125e3 / 0.157464e6 * t89 / t90 / t21 * t93
  t218 = t112 * t189 * t71 + t138 * t215 * t71 - 0.2e1 * t163 * t164 * t93 - 0.2e1 * t193 * t194 * t93
  t222 = t35 * params.kappa
  t223 = t111 ** 2
  t224 = 0.1e1 / t223
  t228 = 0.1e1 / t92 / params.kappa
  t231 = t163 * t134
  t236 = 0.1e1 / t35 / t63
  t242 = 0.520e3 / 0.19683e5 * t44 * t46 * t126
  t245 = 0.247e3 / 0.4374e4 * t53 * t185 * l0
  t247 = 0.1e1 / t22 / t90
  t250 = 0.1672e4 / 0.59049e5 * t44 * t62 * t247
  t251 = t32 * t247
  t255 = -0.770e3 / 0.2187e4 * t31 * t34 * t236 - t242 + t245 - t250 - 0.5225e4 / 0.177147e6 * t69 * t251 * t71
  t258 = t137 ** 2
  t259 = 0.1e1 / t258
  t264 = t193 * t153
  t268 = t33 * t236
  t279 = (-t242 + t245 - t250) * t71
  t288 = -0.1540e4 / 0.2187e4 * t79 * t268 * t82 + 0.110e3 / 0.243e3 * t79 * t198 * t144 - 0.10e2 / 0.81e2 * t79 * t139 * t206 + 0.5e1 / 0.324e3 * t79 * t80 * t279 - 0.625e3 / 0.78732e5 * t89 / t90 / t47 * t93
  t291 = 0.6e1 * t224 * t164 * t134 * t228 + 0.6e1 * t259 * t194 * t153 * t228 + t112 * t255 * t71 + t138 * t288 * t71 - 0.6e1 * t231 * t93 * t189 - 0.6e1 * t264 * t93 * t215
  t296 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t24 * t103 - t107 * t110 * t156 / 0.10e2 + 0.3e1 / 0.10e2 * t107 * t161 * t218 + 0.3e1 / 0.20e2 * t107 * t222 * t291)
  t314 = t164 ** 2
  t316 = t92 ** 2
  t317 = 0.1e1 / t316
  t324 = t189 ** 2
  t332 = 0.1e1 / t35 / t124
  t338 = 0.9880e4 / 0.59049e5 * t44 * t46 * t181
  t341 = 0.2717e4 / 0.6561e4 * t53 * t251 * l0
  t343 = 0.1e1 / t22 / t148
  t346 = 0.41800e5 / 0.177147e6 * t44 * t62 * t343
  t356 = t194 ** 2
  t364 = t215 ** 2
  t402 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t49 * t103 + 0.8e1 / 0.45e2 * t107 * t24 * params.kappa * t156 - t107 * t110 * t218 / 0.5e1 + 0.2e1 / 0.5e1 * t107 * t161 * t291 + 0.3e1 / 0.20e2 * t107 * t222 * (-0.24e2 / t223 / t77 * t314 * t317 + 0.36e2 * t224 * t164 * t228 * t189 - 0.6e1 * t163 * t324 * t93 - 0.8e1 * t231 * t93 * t255 + t112 * (0.13090e5 / 0.6561e4 * t31 * t34 * t332 + t338 - t341 + t346 + 0.130625e6 / 0.531441e6 * t69 * t32 * t343 * t71) * t71 - 0.24e2 / t258 / t99 * t356 * t317 + 0.36e2 * t259 * t194 * t228 * t215 - 0.6e1 * t193 * t364 * t93 - 0.8e1 * t264 * t93 * t288 + t138 * (0.26180e5 / 0.6561e4 * t79 * t33 * t332 * t82 - 0.6160e4 / 0.2187e4 * t79 * t268 * t144 + 0.220e3 / 0.243e3 * t79 * t198 * t206 - 0.40e2 / 0.243e3 * t79 * t139 * t279 + 0.5e1 / 0.324e3 * t79 * t80 * (t338 - t341 + t346) * t71 + 0.6875e4 / 0.78732e5 * t89 / t90 / t54 * t93) * t71))
  v4rho4_0_ = 0.2e1 * r0 * t402 + 0.8e1 * t296

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
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t40 = t35 / t38
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t49 = t35 ** 2
  t52 = t49 / t37 / t36
  t53 = l0 ** 2
  t54 = t41 * r0
  t59 = t52 * t53 / t42 / t54 / 0.5832e4
  t60 = t41 ** 2
  t62 = 0.1e1 / t42 / t60
  t66 = t52 * s0 * t62 * l0 / 0.5184e4
  t67 = s0 ** 2
  t70 = 0.1e1 / t42 / t60 / r0
  t71 = t67 * t70
  t73 = t52 * t71 / 0.17496e5
  t74 = 0.1e1 / params.kappa
  t80 = 0.1e1 + (0.5e1 / 0.648e3 * t40 * s0 * t45 + t59 - t66 + t73 + 0.25e2 / 0.419904e6 * t52 * t71 * t74) * t74
  t82 = t40 * s0
  t83 = t59 - t66 + t73
  t88 = t36 ** 2
  t89 = 0.1e1 / t88
  t91 = t89 * t67 * s0
  t92 = t60 ** 2
  t94 = params.kappa ** 2
  t95 = 0.1e1 / t94
  t101 = 0.1e1 + (0.5e1 / 0.324e3 * t82 * t45 * t83 * t74 + 0.125e3 / 0.45349632e8 * t91 / t92 * t95) * t74
  t105 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t80 - 0.1e1 / t101)
  t109 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t110 = t109 ** 2
  t111 = t110 * f.p.zeta_threshold
  t113 = f.my_piecewise3(t21, t111, t23 * t20)
  t114 = 0.1e1 / t32
  t118 = t6 * t113 * t114 * t105 / 0.10e2
  t119 = t6 * t113
  t120 = t33 * params.kappa
  t121 = t80 ** 2
  t122 = 0.1e1 / t121
  t124 = 0.1e1 / t43 / t54
  t130 = 0.5e1 / 0.8748e4 * t52 * t53 * t62
  t134 = 0.13e2 / 0.15552e5 * t52 * s0 * t70 * l0
  t137 = 0.1e1 / t42 / t60 / t41
  t138 = t67 * t137
  t140 = 0.2e1 / 0.6561e4 * t52 * t138
  t144 = -0.5e1 / 0.243e3 * t40 * s0 * t124 - t130 + t134 - t140 - 0.25e2 / 0.78732e5 * t52 * t138 * t74
  t147 = t101 ** 2
  t148 = 0.1e1 / t147
  t153 = -t130 + t134 - t140
  t163 = -0.10e2 / 0.243e3 * t82 * t124 * t83 * t74 + 0.5e1 / 0.324e3 * t82 * t45 * t153 * t74 - 0.125e3 / 0.5668704e7 * t91 / t92 / r0 * t95
  t166 = t122 * t144 * t74 + t148 * t163 * t74
  t167 = t120 * t166
  t171 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t33 * t105 + t118 + 0.3e1 / 0.20e2 * t119 * t167)
  t173 = r1 <= f.p.dens_threshold
  t174 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t175 = 0.1e1 + t174
  t176 = t175 <= f.p.zeta_threshold
  t177 = t175 ** (0.1e1 / 0.3e1)
  t178 = t177 ** 2
  t180 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t183 = f.my_piecewise3(t176, 0, 0.5e1 / 0.3e1 * t178 * t180)
  t185 = r1 ** 2
  t186 = r1 ** (0.1e1 / 0.3e1)
  t187 = t186 ** 2
  t189 = 0.1e1 / t187 / t185
  t193 = l1 ** 2
  t194 = t185 * r1
  t199 = t52 * t193 / t186 / t194 / 0.5832e4
  t200 = t185 ** 2
  t202 = 0.1e1 / t186 / t200
  t206 = t52 * s2 * t202 * l1 / 0.5184e4
  t207 = s2 ** 2
  t210 = 0.1e1 / t186 / t200 / r1
  t211 = t207 * t210
  t213 = t52 * t211 / 0.17496e5
  t219 = 0.1e1 + (0.5e1 / 0.648e3 * t40 * s2 * t189 + t199 - t206 + t213 + 0.25e2 / 0.419904e6 * t52 * t211 * t74) * t74
  t221 = t40 * s2
  t222 = t199 - t206 + t213
  t228 = t89 * t207 * s2
  t229 = t200 ** 2
  t236 = 0.1e1 + (0.5e1 / 0.324e3 * t221 * t189 * t222 * t74 + 0.125e3 / 0.45349632e8 * t228 / t229 * t95) * t74
  t240 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t219 - 0.1e1 / t236)
  t245 = f.my_piecewise3(t176, t111, t178 * t175)
  t249 = t6 * t245 * t114 * t240 / 0.10e2
  t251 = f.my_piecewise3(t173, 0, 0.3e1 / 0.20e2 * t6 * t183 * t33 * t240 + t249)
  t253 = 0.1e1 / t22
  t254 = t28 ** 2
  t259 = t17 / t24 / t7
  t261 = -0.2e1 * t25 + 0.2e1 * t259
  t262 = f.my_piecewise5(t11, 0, t15, 0, t261)
  t266 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t253 * t254 + 0.5e1 / 0.3e1 * t23 * t262)
  t273 = t6 * t31 * t114 * t105
  t279 = 0.1e1 / t32 / t7
  t283 = t6 * t113 * t279 * t105 / 0.30e2
  t284 = t114 * params.kappa
  t286 = t119 * t284 * t166
  t290 = t144 ** 2
  t295 = 0.1e1 / t43 / t60
  t301 = 0.65e2 / 0.26244e5 * t52 * t53 * t70
  t305 = 0.13e2 / 0.2916e4 * t52 * s0 * t137 * l0
  t309 = t67 / t42 / t60 / t54
  t311 = 0.38e2 / 0.19683e5 * t52 * t309
  t320 = t163 ** 2
  t350 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t266 * t33 * t105 + t273 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t31 * t167 - t283 + t286 / 0.5e1 + 0.3e1 / 0.20e2 * t119 * t120 * (-0.2e1 / t121 / t80 * t290 * t95 + t122 * (0.55e2 / 0.729e3 * t40 * s0 * t295 + t301 - t305 + t311 + 0.475e3 / 0.236196e6 * t52 * t309 * t74) * t74 - 0.2e1 / t147 / t101 * t320 * t95 + t148 * (0.110e3 / 0.729e3 * t82 * t295 * t83 * t74 - 0.20e2 / 0.243e3 * t82 * t124 * t153 * t74 + 0.5e1 / 0.324e3 * t82 * t45 * (t301 - t305 + t311) * t74 + 0.125e3 / 0.629856e6 * t91 / t92 / t41 * t95) * t74))
  t351 = 0.1e1 / t177
  t352 = t180 ** 2
  t356 = f.my_piecewise5(t15, 0, t11, 0, -t261)
  t360 = f.my_piecewise3(t176, 0, 0.10e2 / 0.9e1 * t351 * t352 + 0.5e1 / 0.3e1 * t178 * t356)
  t367 = t6 * t183 * t114 * t240
  t372 = t6 * t245 * t279 * t240 / 0.30e2
  t374 = f.my_piecewise3(t173, 0, 0.3e1 / 0.20e2 * t6 * t360 * t33 * t240 + t367 / 0.5e1 - t372)
  d11 = 0.2e1 * t171 + 0.2e1 * t251 + t7 * (t350 + t374)
  t377 = -t8 - t26
  t378 = f.my_piecewise5(t11, 0, t15, 0, t377)
  t381 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t378)
  t387 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t381 * t33 * t105 + t118)
  t389 = f.my_piecewise5(t15, 0, t11, 0, -t377)
  t392 = f.my_piecewise3(t176, 0, 0.5e1 / 0.3e1 * t178 * t389)
  t397 = t6 * t245
  t398 = t219 ** 2
  t399 = 0.1e1 / t398
  t401 = 0.1e1 / t187 / t194
  t407 = 0.5e1 / 0.8748e4 * t52 * t193 * t202
  t411 = 0.13e2 / 0.15552e5 * t52 * s2 * t210 * l1
  t414 = 0.1e1 / t186 / t200 / t185
  t415 = t207 * t414
  t417 = 0.2e1 / 0.6561e4 * t52 * t415
  t421 = -0.5e1 / 0.243e3 * t40 * s2 * t401 - t407 + t411 - t417 - 0.25e2 / 0.78732e5 * t52 * t415 * t74
  t424 = t236 ** 2
  t425 = 0.1e1 / t424
  t430 = -t407 + t411 - t417
  t440 = -0.10e2 / 0.243e3 * t221 * t401 * t222 * t74 + 0.5e1 / 0.324e3 * t221 * t189 * t430 * t74 - 0.125e3 / 0.5668704e7 * t228 / t229 / r1 * t95
  t443 = t399 * t421 * t74 + t425 * t440 * t74
  t444 = t120 * t443
  t448 = f.my_piecewise3(t173, 0, 0.3e1 / 0.20e2 * t6 * t392 * t33 * t240 + t249 + 0.3e1 / 0.20e2 * t397 * t444)
  t452 = 0.2e1 * t259
  t453 = f.my_piecewise5(t11, 0, t15, 0, t452)
  t457 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t253 * t378 * t28 + 0.5e1 / 0.3e1 * t23 * t453)
  t464 = t6 * t381 * t114 * t105
  t472 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t457 * t33 * t105 + t464 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t381 * t167 + t273 / 0.10e2 - t283 + t286 / 0.10e2)
  t476 = f.my_piecewise5(t15, 0, t11, 0, -t452)
  t480 = f.my_piecewise3(t176, 0, 0.10e2 / 0.9e1 * t351 * t389 * t180 + 0.5e1 / 0.3e1 * t178 * t476)
  t487 = t6 * t392 * t114 * t240
  t494 = t397 * t284 * t443
  t497 = f.my_piecewise3(t173, 0, 0.3e1 / 0.20e2 * t6 * t480 * t33 * t240 + t487 / 0.10e2 + t367 / 0.10e2 - t372 + 0.3e1 / 0.20e2 * t6 * t183 * t444 + t494 / 0.10e2)
  d12 = t171 + t251 + t387 + t448 + t7 * (t472 + t497)
  t502 = t378 ** 2
  t506 = 0.2e1 * t25 + 0.2e1 * t259
  t507 = f.my_piecewise5(t11, 0, t15, 0, t506)
  t511 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t253 * t502 + 0.5e1 / 0.3e1 * t23 * t507)
  t518 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t511 * t33 * t105 + t464 / 0.5e1 - t283)
  t519 = t389 ** 2
  t523 = f.my_piecewise5(t15, 0, t11, 0, -t506)
  t527 = f.my_piecewise3(t176, 0, 0.10e2 / 0.9e1 * t351 * t519 + 0.5e1 / 0.3e1 * t178 * t523)
  t539 = t421 ** 2
  t544 = 0.1e1 / t187 / t200
  t550 = 0.65e2 / 0.26244e5 * t52 * t193 * t210
  t554 = 0.13e2 / 0.2916e4 * t52 * s2 * t414 * l1
  t558 = t207 / t186 / t200 / t194
  t560 = 0.38e2 / 0.19683e5 * t52 * t558
  t569 = t440 ** 2
  t599 = f.my_piecewise3(t173, 0, 0.3e1 / 0.20e2 * t6 * t527 * t33 * t240 + t487 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t392 * t444 - t372 + t494 / 0.5e1 + 0.3e1 / 0.20e2 * t397 * t120 * (-0.2e1 / t398 / t219 * t539 * t95 + t399 * (0.55e2 / 0.729e3 * t40 * s2 * t544 + t550 - t554 + t560 + 0.475e3 / 0.236196e6 * t52 * t558 * t74) * t74 - 0.2e1 / t424 / t236 * t569 * t95 + t425 * (0.110e3 / 0.729e3 * t221 * t544 * t222 * t74 - 0.20e2 / 0.243e3 * t221 * t401 * t430 * t74 + 0.5e1 / 0.324e3 * t221 * t189 * (t550 - t554 + t560) * t74 + 0.125e3 / 0.629856e6 * t228 / t229 / t185 * t95) * t74))
  d22 = 0.2e1 * t387 + 0.2e1 * t448 + t7 * (t518 + t599)
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
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t51 = t46 / t49
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / t52
  t60 = t46 ** 2
  t63 = t60 / t48 / t47
  t64 = l0 ** 2
  t65 = t52 * r0
  t70 = t63 * t64 / t53 / t65 / 0.5832e4
  t71 = t52 ** 2
  t73 = 0.1e1 / t53 / t71
  t77 = t63 * s0 * t73 * l0 / 0.5184e4
  t78 = s0 ** 2
  t79 = t71 * r0
  t81 = 0.1e1 / t53 / t79
  t82 = t78 * t81
  t84 = t63 * t82 / 0.17496e5
  t85 = 0.1e1 / params.kappa
  t91 = 0.1e1 + (0.5e1 / 0.648e3 * t51 * s0 * t56 + t70 - t77 + t84 + 0.25e2 / 0.419904e6 * t63 * t82 * t85) * t85
  t93 = t51 * s0
  t94 = t70 - t77 + t84
  t99 = t47 ** 2
  t100 = 0.1e1 / t99
  t102 = t100 * t78 * s0
  t103 = t71 ** 2
  t105 = params.kappa ** 2
  t106 = 0.1e1 / t105
  t112 = 0.1e1 + (0.5e1 / 0.324e3 * t93 * t56 * t94 * t85 + 0.125e3 / 0.45349632e8 * t102 / t103 * t106) * t85
  t116 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t91 - 0.1e1 / t112)
  t122 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t123 = 0.1e1 / t43
  t128 = t6 * t122
  t129 = t44 * params.kappa
  t130 = t91 ** 2
  t131 = 0.1e1 / t130
  t133 = 0.1e1 / t54 / t65
  t139 = 0.5e1 / 0.8748e4 * t63 * t64 * t73
  t143 = 0.13e2 / 0.15552e5 * t63 * s0 * t81 * l0
  t146 = 0.1e1 / t53 / t71 / t52
  t147 = t78 * t146
  t149 = 0.2e1 / 0.6561e4 * t63 * t147
  t153 = -0.5e1 / 0.243e3 * t51 * s0 * t133 - t139 + t143 - t149 - 0.25e2 / 0.78732e5 * t63 * t147 * t85
  t156 = t112 ** 2
  t157 = 0.1e1 / t156
  t162 = -t139 + t143 - t149
  t172 = -0.10e2 / 0.243e3 * t93 * t133 * t94 * t85 + 0.5e1 / 0.324e3 * t93 * t56 * t162 * t85 - 0.125e3 / 0.5668704e7 * t102 / t103 / r0 * t106
  t175 = t131 * t153 * t85 + t157 * t172 * t85
  t176 = t129 * t175
  t179 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t180 = t179 ** 2
  t181 = t180 * f.p.zeta_threshold
  t183 = f.my_piecewise3(t21, t181, t32 * t20)
  t185 = 0.1e1 / t43 / t7
  t190 = t6 * t183
  t191 = t123 * params.kappa
  t192 = t191 * t175
  t196 = 0.1e1 / t130 / t91
  t197 = t153 ** 2
  t202 = 0.1e1 / t54 / t71
  t208 = 0.65e2 / 0.26244e5 * t63 * t64 * t81
  t212 = 0.13e2 / 0.2916e4 * t63 * s0 * t146 * l0
  t215 = 0.1e1 / t53 / t71 / t65
  t216 = t78 * t215
  t218 = 0.38e2 / 0.19683e5 * t63 * t216
  t222 = 0.55e2 / 0.729e3 * t51 * s0 * t202 + t208 - t212 + t218 + 0.475e3 / 0.236196e6 * t63 * t216 * t85
  t226 = 0.1e1 / t156 / t112
  t227 = t172 ** 2
  t239 = t208 - t212 + t218
  t249 = 0.110e3 / 0.729e3 * t93 * t202 * t94 * t85 - 0.20e2 / 0.243e3 * t93 * t133 * t162 * t85 + 0.5e1 / 0.324e3 * t93 * t56 * t239 * t85 + 0.125e3 / 0.629856e6 * t102 / t103 / t52 * t106
  t252 = -0.2e1 * t196 * t197 * t106 - 0.2e1 * t226 * t227 * t106 + t131 * t222 * t85 + t157 * t249 * t85
  t253 = t129 * t252
  t257 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t42 * t44 * t116 + t6 * t122 * t123 * t116 / 0.5e1 + 0.3e1 / 0.10e2 * t128 * t176 - t6 * t183 * t185 * t116 / 0.30e2 + t190 * t192 / 0.5e1 + 0.3e1 / 0.20e2 * t190 * t253)
  t259 = r1 <= f.p.dens_threshold
  t260 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t261 = 0.1e1 + t260
  t262 = t261 <= f.p.zeta_threshold
  t263 = t261 ** (0.1e1 / 0.3e1)
  t264 = 0.1e1 / t263
  t266 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t267 = t266 ** 2
  t270 = t263 ** 2
  t272 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t276 = f.my_piecewise3(t262, 0, 0.10e2 / 0.9e1 * t264 * t267 + 0.5e1 / 0.3e1 * t270 * t272)
  t278 = r1 ** 2
  t279 = r1 ** (0.1e1 / 0.3e1)
  t280 = t279 ** 2
  t282 = 0.1e1 / t280 / t278
  t286 = l1 ** 2
  t292 = t63 * t286 / t279 / t278 / r1 / 0.5832e4
  t293 = t278 ** 2
  t299 = t63 * s2 / t279 / t293 * l1 / 0.5184e4
  t300 = s2 ** 2
  t304 = t300 / t279 / t293 / r1
  t306 = t63 * t304 / 0.17496e5
  t322 = t293 ** 2
  t333 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / (0.1e1 + (0.5e1 / 0.648e3 * t51 * s2 * t282 + t292 - t299 + t306 + 0.25e2 / 0.419904e6 * t63 * t304 * t85) * t85) - 0.1e1 / (0.1e1 + (0.5e1 / 0.324e3 * t51 * s2 * t282 * (t292 - t299 + t306) * t85 + 0.125e3 / 0.45349632e8 * t100 * t300 * s2 / t322 * t106) * t85))
  t339 = f.my_piecewise3(t262, 0, 0.5e1 / 0.3e1 * t270 * t266)
  t345 = f.my_piecewise3(t262, t181, t270 * t261)
  t351 = f.my_piecewise3(t259, 0, 0.3e1 / 0.20e2 * t6 * t276 * t44 * t333 + t6 * t339 * t123 * t333 / 0.5e1 - t6 * t345 * t185 * t333 / 0.30e2)
  t361 = t24 ** 2
  t365 = 0.6e1 * t34 - 0.6e1 * t17 / t361
  t366 = f.my_piecewise5(t11, 0, t15, 0, t365)
  t370 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t366)
  t391 = 0.1e1 / t43 / t24
  t403 = t130 ** 2
  t408 = 0.1e1 / t105 / params.kappa
  t416 = 0.1e1 / t54 / t79
  t422 = 0.260e3 / 0.19683e5 * t63 * t64 * t146
  t426 = 0.247e3 / 0.8748e4 * t63 * s0 * t215 * l0
  t429 = t78 / t53 / t103
  t431 = 0.836e3 / 0.59049e5 * t63 * t429
  t438 = t156 ** 2
  t478 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t370 * t44 * t116 + 0.3e1 / 0.10e2 * t6 * t42 * t123 * t116 + 0.9e1 / 0.20e2 * t6 * t42 * t176 - t6 * t122 * t185 * t116 / 0.10e2 + 0.3e1 / 0.5e1 * t128 * t192 + 0.9e1 / 0.20e2 * t128 * t253 + 0.2e1 / 0.45e2 * t6 * t183 * t391 * t116 - t190 * t185 * params.kappa * t175 / 0.10e2 + 0.3e1 / 0.10e2 * t190 * t191 * t252 + 0.3e1 / 0.20e2 * t190 * t129 * (0.6e1 / t403 * t197 * t153 * t408 - 0.6e1 * t196 * t153 * t106 * t222 + t131 * (-0.770e3 / 0.2187e4 * t51 * s0 * t416 - t422 + t426 - t431 - 0.5225e4 / 0.354294e6 * t63 * t429 * t85) * t85 + 0.6e1 / t438 * t227 * t172 * t408 - 0.6e1 * t226 * t172 * t106 * t249 + t157 * (-0.1540e4 / 0.2187e4 * t93 * t416 * t94 * t85 + 0.110e3 / 0.243e3 * t93 * t202 * t162 * t85 - 0.10e2 / 0.81e2 * t93 * t133 * t239 * t85 + 0.5e1 / 0.324e3 * t93 * t56 * (-t422 + t426 - t431) * t85 - 0.625e3 / 0.314928e6 * t102 / t103 / t65 * t106) * t85))
  t488 = f.my_piecewise5(t15, 0, t11, 0, -t365)
  t492 = f.my_piecewise3(t262, 0, -0.10e2 / 0.27e2 / t263 / t261 * t267 * t266 + 0.10e2 / 0.3e1 * t264 * t266 * t272 + 0.5e1 / 0.3e1 * t270 * t488)
  t510 = f.my_piecewise3(t259, 0, 0.3e1 / 0.20e2 * t6 * t492 * t44 * t333 + 0.3e1 / 0.10e2 * t6 * t276 * t123 * t333 - t6 * t339 * t185 * t333 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t345 * t391 * t333)
  d111 = 0.3e1 * t257 + 0.3e1 * t351 + t7 * (t478 + t510)

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
  t58 = 6 ** (0.1e1 / 0.3e1)
  t59 = jnp.pi ** 2
  t60 = t59 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t63 = t58 / t61
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t72 = t58 ** 2
  t75 = t72 / t60 / t59
  t76 = l0 ** 2
  t77 = t64 * r0
  t82 = t75 * t76 / t65 / t77 / 0.5832e4
  t83 = t64 ** 2
  t85 = 0.1e1 / t65 / t83
  t89 = t75 * s0 * t85 * l0 / 0.5184e4
  t90 = s0 ** 2
  t91 = t83 * r0
  t93 = 0.1e1 / t65 / t91
  t94 = t90 * t93
  t96 = t75 * t94 / 0.17496e5
  t97 = 0.1e1 / params.kappa
  t103 = 0.1e1 + (0.5e1 / 0.648e3 * t63 * s0 * t68 + t82 - t89 + t96 + 0.25e2 / 0.419904e6 * t75 * t94 * t97) * t97
  t105 = t63 * s0
  t106 = t82 - t89 + t96
  t111 = t59 ** 2
  t112 = 0.1e1 / t111
  t114 = t112 * t90 * s0
  t115 = t83 ** 2
  t117 = params.kappa ** 2
  t118 = 0.1e1 / t117
  t124 = 0.1e1 + (0.5e1 / 0.324e3 * t105 * t68 * t106 * t97 + 0.125e3 / 0.45349632e8 * t114 / t115 * t118) * t97
  t128 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / t103 - 0.1e1 / t124)
  t137 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t138 = 0.1e1 / t55
  t143 = t6 * t137
  t144 = t56 * params.kappa
  t145 = t103 ** 2
  t146 = 0.1e1 / t145
  t148 = 0.1e1 / t66 / t77
  t154 = 0.5e1 / 0.8748e4 * t75 * t76 * t85
  t158 = 0.13e2 / 0.15552e5 * t75 * s0 * t93 * l0
  t159 = t83 * t64
  t161 = 0.1e1 / t65 / t159
  t162 = t90 * t161
  t164 = 0.2e1 / 0.6561e4 * t75 * t162
  t168 = -0.5e1 / 0.243e3 * t63 * s0 * t148 - t154 + t158 - t164 - 0.25e2 / 0.78732e5 * t75 * t162 * t97
  t171 = t124 ** 2
  t172 = 0.1e1 / t171
  t177 = -t154 + t158 - t164
  t182 = t115 * r0
  t187 = -0.10e2 / 0.243e3 * t105 * t148 * t106 * t97 + 0.5e1 / 0.324e3 * t105 * t68 * t177 * t97 - 0.125e3 / 0.5668704e7 * t114 / t182 * t118
  t190 = t146 * t168 * t97 + t172 * t187 * t97
  t191 = t144 * t190
  t196 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t198 = 0.1e1 / t55 / t7
  t203 = t6 * t196
  t204 = t138 * params.kappa
  t205 = t204 * t190
  t209 = 0.1e1 / t145 / t103
  t210 = t168 ** 2
  t215 = 0.1e1 / t66 / t83
  t221 = 0.65e2 / 0.26244e5 * t75 * t76 * t93
  t225 = 0.13e2 / 0.2916e4 * t75 * s0 * t161 * l0
  t228 = 0.1e1 / t65 / t83 / t77
  t229 = t90 * t228
  t231 = 0.38e2 / 0.19683e5 * t75 * t229
  t235 = 0.55e2 / 0.729e3 * t63 * s0 * t215 + t221 - t225 + t231 + 0.475e3 / 0.236196e6 * t75 * t229 * t97
  t239 = 0.1e1 / t171 / t124
  t240 = t187 ** 2
  t252 = t221 - t225 + t231
  t262 = 0.110e3 / 0.729e3 * t105 * t215 * t106 * t97 - 0.20e2 / 0.243e3 * t105 * t148 * t177 * t97 + 0.5e1 / 0.324e3 * t105 * t68 * t252 * t97 + 0.125e3 / 0.629856e6 * t114 / t115 / t64 * t118
  t265 = -0.2e1 * t209 * t210 * t118 - 0.2e1 * t239 * t240 * t118 + t146 * t235 * t97 + t172 * t262 * t97
  t266 = t144 * t265
  t269 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t270 = t269 ** 2
  t271 = t270 * f.p.zeta_threshold
  t273 = f.my_piecewise3(t21, t271, t44 * t20)
  t275 = 0.1e1 / t55 / t25
  t280 = t6 * t273
  t281 = t198 * params.kappa
  t282 = t281 * t190
  t285 = t204 * t265
  t288 = t145 ** 2
  t289 = 0.1e1 / t288
  t293 = 0.1e1 / t117 / params.kappa
  t296 = t209 * t168
  t301 = 0.1e1 / t66 / t91
  t307 = 0.260e3 / 0.19683e5 * t75 * t76 * t161
  t311 = 0.247e3 / 0.8748e4 * t75 * s0 * t228 * l0
  t313 = 0.1e1 / t65 / t115
  t314 = t90 * t313
  t316 = 0.836e3 / 0.59049e5 * t75 * t314
  t320 = -0.770e3 / 0.2187e4 * t63 * s0 * t301 - t307 + t311 - t316 - 0.5225e4 / 0.354294e6 * t75 * t314 * t97
  t323 = t171 ** 2
  t324 = 0.1e1 / t323
  t329 = t239 * t187
  t345 = -t307 + t311 - t316
  t355 = -0.1540e4 / 0.2187e4 * t105 * t301 * t106 * t97 + 0.110e3 / 0.243e3 * t105 * t215 * t177 * t97 - 0.10e2 / 0.81e2 * t105 * t148 * t252 * t97 + 0.5e1 / 0.324e3 * t105 * t68 * t345 * t97 - 0.625e3 / 0.314928e6 * t114 / t115 / t77 * t118
  t358 = 0.6e1 * t289 * t210 * t168 * t293 + 0.6e1 * t324 * t240 * t187 * t293 - 0.6e1 * t296 * t118 * t235 - 0.6e1 * t329 * t118 * t262 + t146 * t320 * t97 + t172 * t355 * t97
  t359 = t144 * t358
  t363 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t54 * t56 * t128 + 0.3e1 / 0.10e2 * t6 * t137 * t138 * t128 + 0.9e1 / 0.20e2 * t143 * t191 - t6 * t196 * t198 * t128 / 0.10e2 + 0.3e1 / 0.5e1 * t203 * t205 + 0.9e1 / 0.20e2 * t203 * t266 + 0.2e1 / 0.45e2 * t6 * t273 * t275 * t128 - t280 * t282 / 0.10e2 + 0.3e1 / 0.10e2 * t280 * t285 + 0.3e1 / 0.20e2 * t280 * t359)
  t365 = r1 <= f.p.dens_threshold
  t366 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t367 = 0.1e1 + t366
  t368 = t367 <= f.p.zeta_threshold
  t369 = t367 ** (0.1e1 / 0.3e1)
  t371 = 0.1e1 / t369 / t367
  t373 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t374 = t373 ** 2
  t378 = 0.1e1 / t369
  t379 = t378 * t373
  t381 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t384 = t369 ** 2
  t386 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t390 = f.my_piecewise3(t368, 0, -0.10e2 / 0.27e2 * t371 * t374 * t373 + 0.10e2 / 0.3e1 * t379 * t381 + 0.5e1 / 0.3e1 * t384 * t386)
  t392 = r1 ** 2
  t393 = r1 ** (0.1e1 / 0.3e1)
  t394 = t393 ** 2
  t396 = 0.1e1 / t394 / t392
  t400 = l1 ** 2
  t406 = t75 * t400 / t393 / t392 / r1 / 0.5832e4
  t407 = t392 ** 2
  t413 = t75 * s2 / t393 / t407 * l1 / 0.5184e4
  t414 = s2 ** 2
  t418 = t414 / t393 / t407 / r1
  t420 = t75 * t418 / 0.17496e5
  t436 = t407 ** 2
  t447 = 0.1e1 + params.kappa * (0.2e1 - 0.1e1 / (0.1e1 + (0.5e1 / 0.648e3 * t63 * s2 * t396 + t406 - t413 + t420 + 0.25e2 / 0.419904e6 * t75 * t418 * t97) * t97) - 0.1e1 / (0.1e1 + (0.5e1 / 0.324e3 * t63 * s2 * t396 * (t406 - t413 + t420) * t97 + 0.125e3 / 0.45349632e8 * t112 * t414 * s2 / t436 * t118) * t97))
  t456 = f.my_piecewise3(t368, 0, 0.10e2 / 0.9e1 * t378 * t374 + 0.5e1 / 0.3e1 * t384 * t381)
  t463 = f.my_piecewise3(t368, 0, 0.5e1 / 0.3e1 * t384 * t373)
  t469 = f.my_piecewise3(t368, t271, t384 * t367)
  t475 = f.my_piecewise3(t365, 0, 0.3e1 / 0.20e2 * t6 * t390 * t56 * t447 + 0.3e1 / 0.10e2 * t6 * t456 * t138 * t447 - t6 * t463 * t198 * t447 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t469 * t275 * t447)
  t477 = t20 ** 2
  t480 = t30 ** 2
  t486 = t41 ** 2
  t495 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t496 = f.my_piecewise5(t11, 0, t15, 0, t495)
  t500 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t477 * t480 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t486 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t496)
  t516 = 0.1e1 / t55 / t36
  t533 = t210 ** 2
  t535 = t117 ** 2
  t536 = 0.1e1 / t535
  t543 = t235 ** 2
  t551 = 0.1e1 / t66 / t159
  t557 = 0.4940e4 / 0.59049e5 * t75 * t76 * t228
  t561 = 0.2717e4 / 0.13122e5 * t75 * s0 * t313 * l0
  t564 = t90 / t65 / t182
  t566 = 0.20900e5 / 0.177147e6 * t75 * t564
  t575 = t240 ** 2
  t583 = t262 ** 2
  t638 = 0.3e1 / 0.20e2 * t6 * t500 * t56 * t128 + 0.8e1 / 0.45e2 * t6 * t196 * t275 * t128 - 0.2e1 / 0.5e1 * t203 * t282 + 0.6e1 / 0.5e1 * t203 * t285 + 0.3e1 / 0.5e1 * t203 * t359 - 0.14e2 / 0.135e3 * t6 * t273 * t516 * t128 + 0.8e1 / 0.45e2 * t280 * t275 * params.kappa * t190 - t280 * t281 * t265 / 0.5e1 + 0.2e1 / 0.5e1 * t280 * t204 * t358 + 0.3e1 / 0.20e2 * t280 * t144 * (-0.24e2 / t288 / t103 * t533 * t536 + 0.36e2 * t289 * t210 * t293 * t235 - 0.6e1 * t209 * t543 * t118 - 0.8e1 * t296 * t118 * t320 + t146 * (0.13090e5 / 0.6561e4 * t63 * s0 * t551 + t557 - t561 + t566 + 0.130625e6 / 0.1062882e7 * t75 * t564 * t97) * t97 - 0.24e2 / t323 / t124 * t575 * t536 + 0.36e2 * t324 * t240 * t293 * t262 - 0.6e1 * t239 * t583 * t118 - 0.8e1 * t329 * t118 * t355 + t172 * (0.26180e5 / 0.6561e4 * t105 * t551 * t106 * t97 - 0.6160e4 / 0.2187e4 * t105 * t301 * t177 * t97 + 0.220e3 / 0.243e3 * t105 * t215 * t252 * t97 - 0.40e2 / 0.243e3 * t105 * t148 * t345 * t97 + 0.5e1 / 0.324e3 * t105 * t68 * (t557 - t561 + t566) * t97 + 0.6875e4 / 0.314928e6 * t114 / t115 / t83 * t118) * t97) + 0.2e1 / 0.5e1 * t6 * t54 * t138 * t128 + 0.3e1 / 0.5e1 * t6 * t54 * t191 - t6 * t137 * t198 * t128 / 0.5e1 + 0.6e1 / 0.5e1 * t143 * t205 + 0.9e1 / 0.10e2 * t143 * t266
  t639 = f.my_piecewise3(t1, 0, t638)
  t640 = t367 ** 2
  t643 = t374 ** 2
  t649 = t381 ** 2
  t655 = f.my_piecewise5(t15, 0, t11, 0, -t495)
  t659 = f.my_piecewise3(t368, 0, 0.40e2 / 0.81e2 / t369 / t640 * t643 - 0.20e2 / 0.9e1 * t371 * t374 * t381 + 0.10e2 / 0.3e1 * t378 * t649 + 0.40e2 / 0.9e1 * t379 * t386 + 0.5e1 / 0.3e1 * t384 * t655)
  t681 = f.my_piecewise3(t365, 0, 0.3e1 / 0.20e2 * t6 * t659 * t56 * t447 + 0.2e1 / 0.5e1 * t6 * t390 * t138 * t447 - t6 * t456 * t198 * t447 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t463 * t275 * t447 - 0.14e2 / 0.135e3 * t6 * t469 * t516 * t447)
  d1111 = 0.4e1 * t363 + 0.4e1 * t475 + t7 * (t639 + t681)

  res = {'v4rho4': d1111}
  return res
