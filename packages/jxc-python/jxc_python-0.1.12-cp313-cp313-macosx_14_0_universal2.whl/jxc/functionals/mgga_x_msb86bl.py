"""Generated from mgga_x_msb86bl.mpl."""

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

  msb86bl_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  msb86bl_f0 = lambda p, c: 1 + (MU_GE * p + c) / (1 + (MU_GE * p + c) / params_kappa) ** (4 / 5)

  msb86bl_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  msb86bl_f = lambda x, u, t: msb86bl_f0(X2S ** 2 * x ** 2, 0) + msb86bl_fa(msb86bl_alpha(t, x)) * (msb86bl_f0(X2S ** 2 * x ** 2, params_c) - msb86bl_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msb86bl_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  msb86bl_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  msb86bl_f0 = lambda p, c: 1 + (MU_GE * p + c) / (1 + (MU_GE * p + c) / params_kappa) ** (4 / 5)

  msb86bl_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  msb86bl_f = lambda x, u, t: msb86bl_f0(X2S ** 2 * x ** 2, 0) + msb86bl_fa(msb86bl_alpha(t, x)) * (msb86bl_f0(X2S ** 2 * x ** 2, params_c) - msb86bl_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msb86bl_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  msb86bl_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  msb86bl_f0 = lambda p, c: 1 + (MU_GE * p + c) / (1 + (MU_GE * p + c) / params_kappa) ** (4 / 5)

  msb86bl_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  msb86bl_f = lambda x, u, t: msb86bl_f0(X2S ** 2 * x ** 2, 0) + msb86bl_fa(msb86bl_alpha(t, x)) * (msb86bl_f0(X2S ** 2 * x ** 2, params_c) - msb86bl_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msb86bl_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t40 = 0.1e1 / params.kappa
  t44 = 0.1e1 + 0.5e1 / 0.972e3 * t33 * t39 * t40
  t45 = t44 ** (0.1e1 / 0.5e1)
  t46 = t45 ** 2
  t47 = t46 ** 2
  t48 = 0.1e1 / t47
  t51 = 0.5e1 / 0.972e3 * t33 * t39 * t48
  t53 = 0.1e1 / t36 / r0
  t56 = tau0 * t53 - t39 / 0.8e1
  t57 = t56 ** 2
  t58 = t28 ** 2
  t60 = 0.3e1 / 0.10e2 * t58 * t31
  t61 = params.eta * s0
  t64 = t60 + t61 * t38 / 0.8e1
  t65 = t64 ** 2
  t66 = 0.1e1 / t65
  t68 = -t57 * t66 + 0.1e1
  t69 = t68 ** 2
  t70 = t69 * t68
  t71 = t57 * t56
  t72 = t65 * t64
  t73 = 0.1e1 / t72
  t75 = t57 ** 2
  t77 = params.b * t75 * t57
  t78 = t65 ** 2
  t80 = 0.1e1 / t78 / t65
  t82 = t71 * t73 + t77 * t80 + 0.1e1
  t83 = 0.1e1 / t82
  t84 = t70 * t83
  t87 = 0.5e1 / 0.972e3 * t33 * t39 + params.c
  t89 = t87 * t40 + 0.1e1
  t90 = t89 ** (0.1e1 / 0.5e1)
  t91 = t90 ** 2
  t92 = t91 ** 2
  t93 = 0.1e1 / t92
  t95 = t87 * t93 - t51
  t97 = t84 * t95 + t51 + 0.1e1
  t101 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t97)
  t102 = r1 <= f.p.dens_threshold
  t103 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t104 = 0.1e1 + t103
  t105 = t104 <= f.p.zeta_threshold
  t106 = t104 ** (0.1e1 / 0.3e1)
  t108 = f.my_piecewise3(t105, t22, t106 * t104)
  t109 = t108 * t26
  t110 = r1 ** 2
  t111 = r1 ** (0.1e1 / 0.3e1)
  t112 = t111 ** 2
  t114 = 0.1e1 / t112 / t110
  t115 = s2 * t114
  t119 = 0.1e1 + 0.5e1 / 0.972e3 * t33 * t115 * t40
  t120 = t119 ** (0.1e1 / 0.5e1)
  t121 = t120 ** 2
  t122 = t121 ** 2
  t123 = 0.1e1 / t122
  t126 = 0.5e1 / 0.972e3 * t33 * t115 * t123
  t128 = 0.1e1 / t112 / r1
  t131 = tau1 * t128 - t115 / 0.8e1
  t132 = t131 ** 2
  t133 = params.eta * s2
  t136 = t60 + t133 * t114 / 0.8e1
  t137 = t136 ** 2
  t138 = 0.1e1 / t137
  t140 = -t132 * t138 + 0.1e1
  t141 = t140 ** 2
  t142 = t141 * t140
  t143 = t132 * t131
  t144 = t137 * t136
  t145 = 0.1e1 / t144
  t147 = t132 ** 2
  t149 = params.b * t147 * t132
  t150 = t137 ** 2
  t152 = 0.1e1 / t150 / t137
  t154 = t143 * t145 + t149 * t152 + 0.1e1
  t155 = 0.1e1 / t154
  t156 = t142 * t155
  t159 = 0.5e1 / 0.972e3 * t33 * t115 + params.c
  t161 = t159 * t40 + 0.1e1
  t162 = t161 ** (0.1e1 / 0.5e1)
  t163 = t162 ** 2
  t164 = t163 ** 2
  t165 = 0.1e1 / t164
  t167 = t159 * t165 - t126
  t169 = t156 * t167 + t126 + 0.1e1
  t173 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t5 * t109 * t169)
  t174 = t6 ** 2
  t176 = t16 / t174
  t177 = t7 - t176
  t178 = f.my_piecewise5(t10, 0, t14, 0, t177)
  t181 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t178)
  t186 = t26 ** 2
  t187 = 0.1e1 / t186
  t191 = t5 * t25 * t187 * t97 / 0.8e1
  t194 = 0.1e1 / t36 / t34 / r0
  t195 = s0 * t194
  t198 = 0.10e2 / 0.729e3 * t33 * t195 * t48
  t201 = t58 / t30 / t29
  t202 = s0 ** 2
  t204 = t34 ** 2
  t209 = 0.1e1 / t47 / t44
  t213 = 0.10e2 / 0.177147e6 * t201 * t202 / t35 / t204 / t34 * t209 * t40
  t214 = t69 * t83
  t215 = t56 * t66
  t219 = -0.5e1 / 0.3e1 * tau0 * t38 + t195 / 0.3e1
  t222 = t57 * t73
  t223 = t61 * t194
  t230 = t82 ** 2
  t232 = t70 / t230
  t236 = t71 / t78
  t239 = params.b * t75 * t56
  t244 = 0.1e1 / t78 / t72
  t257 = t87 / t92 / t89 * t28
  t270 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t181 * t26 * t97 - t191 - 0.3e1 / 0.8e1 * t5 * t27 * (-t198 + t213 + 0.3e1 * t214 * t95 * (-0.2e1 * t215 * t219 - 0.2e1 / 0.3e1 * t222 * t223) - t232 * t95 * (0.6e1 * t239 * t80 * t219 + 0.2e1 * t77 * t244 * t223 + 0.3e1 * t222 * t219 + t236 * t223) + t84 * (-0.10e2 / 0.729e3 * t33 * t195 * t93 + 0.8e1 / 0.729e3 * t257 * t32 * s0 * t194 * t40 + t198 - t213)))
  t272 = f.my_piecewise5(t14, 0, t10, 0, -t177)
  t275 = f.my_piecewise3(t105, 0, 0.4e1 / 0.3e1 * t106 * t272)
  t283 = t5 * t108 * t187 * t169 / 0.8e1
  t285 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t5 * t275 * t26 * t169 - t283)
  vrho_0_ = t101 + t173 + t6 * (t270 + t285)
  t288 = -t7 - t176
  t289 = f.my_piecewise5(t10, 0, t14, 0, t288)
  t292 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t289)
  t298 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t292 * t26 * t97 - t191)
  t300 = f.my_piecewise5(t14, 0, t10, 0, -t288)
  t303 = f.my_piecewise3(t105, 0, 0.4e1 / 0.3e1 * t106 * t300)
  t310 = 0.1e1 / t112 / t110 / r1
  t311 = s2 * t310
  t314 = 0.10e2 / 0.729e3 * t33 * t311 * t123
  t315 = s2 ** 2
  t317 = t110 ** 2
  t322 = 0.1e1 / t122 / t119
  t326 = 0.10e2 / 0.177147e6 * t201 * t315 / t111 / t317 / t110 * t322 * t40
  t327 = t141 * t155
  t328 = t131 * t138
  t332 = -0.5e1 / 0.3e1 * tau1 * t114 + t311 / 0.3e1
  t335 = t132 * t145
  t336 = t133 * t310
  t343 = t154 ** 2
  t345 = t142 / t343
  t349 = t143 / t150
  t352 = params.b * t147 * t131
  t357 = 0.1e1 / t150 / t144
  t370 = t159 / t164 / t161 * t28
  t383 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t5 * t303 * t26 * t169 - t283 - 0.3e1 / 0.8e1 * t5 * t109 * (-t314 + t326 + 0.3e1 * t327 * t167 * (-0.2e1 * t328 * t332 - 0.2e1 / 0.3e1 * t335 * t336) - t345 * t167 * (0.2e1 * t149 * t357 * t336 + 0.6e1 * t352 * t152 * t332 + 0.3e1 * t335 * t332 + t349 * t336) + t156 * (-0.10e2 / 0.729e3 * t33 * t311 * t165 + 0.8e1 / 0.729e3 * t370 * t32 * s2 * t310 * t40 + t314 - t326)))
  vrho_1_ = t101 + t173 + t6 * (t298 + t383)
  t388 = 0.5e1 / 0.972e3 * t33 * t38 * t48
  t396 = 0.5e1 / 0.236196e6 * t201 * s0 / t35 / t204 / r0 * t209 * t40
  t398 = params.eta * t38
  t432 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t388 - t396 + 0.3e1 * t214 * t95 * (t215 * t38 / 0.4e1 + t222 * t398 / 0.4e1) - t232 * t95 * (-0.3e1 / 0.8e1 * t222 * t38 - 0.3e1 / 0.8e1 * t236 * t398 - 0.3e1 / 0.4e1 * t239 * t80 * t38 - 0.3e1 / 0.4e1 * t77 * t244 * params.eta * t38) + t84 * (0.5e1 / 0.972e3 * t33 * t38 * t93 - t257 * t32 * t38 * t40 / 0.243e3 - t388 + t396)))
  vsigma_0_ = t6 * t432
  vsigma_1_ = 0.0e0
  t435 = 0.5e1 / 0.972e3 * t33 * t114 * t123
  t443 = 0.5e1 / 0.236196e6 * t201 * s2 / t111 / t317 / r1 * t322 * t40
  t445 = params.eta * t114
  t479 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t5 * t109 * (t435 - t443 + 0.3e1 * t327 * t167 * (t328 * t114 / 0.4e1 + t335 * t445 / 0.4e1) - t345 * t167 * (-0.3e1 / 0.8e1 * t335 * t114 - 0.3e1 / 0.8e1 * t349 * t445 - 0.3e1 / 0.4e1 * t352 * t152 * t114 - 0.3e1 / 0.4e1 * t149 * t357 * params.eta * t114) + t156 * (0.5e1 / 0.972e3 * t33 * t114 * t165 - t370 * t32 * t114 * t40 / 0.243e3 - t435 + t443)))
  vsigma_2_ = t6 * t479
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t496 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-0.6e1 * t214 * t95 * t215 * t53 - t232 * t95 * (0.6e1 * t239 * t80 * t53 + 0.3e1 * t222 * t53)))
  vtau_0_ = t6 * t496
  t513 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t5 * t109 * (-0.6e1 * t327 * t167 * t328 * t128 - t345 * t167 * (0.6e1 * t352 * t152 * t128 + 0.3e1 * t335 * t128)))
  vtau_1_ = t6 * t513
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

  msb86bl_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  msb86bl_f0 = lambda p, c: 1 + (MU_GE * p + c) / (1 + (MU_GE * p + c) / params_kappa) ** (4 / 5)

  msb86bl_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  msb86bl_f = lambda x, u, t: msb86bl_f0(X2S ** 2 * x ** 2, 0) + msb86bl_fa(msb86bl_alpha(t, x)) * (msb86bl_f0(X2S ** 2 * x ** 2, params_c) - msb86bl_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msb86bl_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t20 = 6 ** (0.1e1 / 0.3e1)
  t21 = jnp.pi ** 2
  t22 = t21 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = 0.1e1 / t23
  t25 = t20 * t24
  t26 = t25 * s0
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = r0 ** 2
  t30 = t18 ** 2
  t32 = 0.1e1 / t30 / t29
  t33 = t28 * t32
  t34 = 0.1e1 / params.kappa
  t38 = 0.1e1 + 0.5e1 / 0.972e3 * t26 * t33 * t34
  t39 = t38 ** (0.1e1 / 0.5e1)
  t40 = t39 ** 2
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t43 = t33 * t42
  t45 = 0.5e1 / 0.972e3 * t26 * t43
  t46 = tau0 * t28
  t48 = 0.1e1 / t30 / r0
  t50 = s0 * t28
  t51 = t50 * t32
  t53 = t46 * t48 - t51 / 0.8e1
  t54 = t53 ** 2
  t55 = t20 ** 2
  t58 = params.eta * s0
  t61 = 0.3e1 / 0.10e2 * t55 * t23 + t58 * t33 / 0.8e1
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t65 = -t54 * t63 + 0.1e1
  t66 = t65 ** 2
  t67 = t66 * t65
  t68 = t54 * t53
  t69 = t62 * t61
  t70 = 0.1e1 / t69
  t72 = t54 ** 2
  t74 = params.b * t72 * t54
  t75 = t62 ** 2
  t77 = 0.1e1 / t75 / t62
  t79 = t68 * t70 + t74 * t77 + 0.1e1
  t80 = 0.1e1 / t79
  t81 = t67 * t80
  t84 = 0.5e1 / 0.972e3 * t25 * t51 + params.c
  t86 = t84 * t34 + 0.1e1
  t87 = t86 ** (0.1e1 / 0.5e1)
  t88 = t87 ** 2
  t89 = t88 ** 2
  t90 = 0.1e1 / t89
  t92 = t84 * t90 - t45
  t94 = t81 * t92 + t45 + 0.1e1
  t98 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t94)
  t106 = 0.1e1 / t30 / t29 / r0
  t107 = t28 * t106
  t110 = 0.10e2 / 0.729e3 * t26 * t107 * t42
  t113 = t55 / t22 / t21
  t114 = s0 ** 2
  t116 = t29 ** 2
  t123 = 0.1e1 / t41 / t38 * t34
  t126 = 0.20e2 / 0.177147e6 * t113 * t114 * t27 / t18 / t116 / t29 * t123
  t127 = t66 * t80
  t128 = t53 * t63
  t131 = t50 * t106
  t133 = -0.5e1 / 0.3e1 * t46 * t32 + t131 / 0.3e1
  t136 = t54 * t70
  t144 = t79 ** 2
  t146 = t67 / t144
  t150 = t68 / t75
  t154 = params.b * t72 * t53
  t160 = t74 / t75 / t69
  t172 = t84 / t89 / t86
  t185 = f.my_piecewise3(t2, 0, -t6 * t17 / t30 * t94 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t110 + t126 + 0.3e1 * t127 * t92 * (-0.2e1 * t128 * t133 - 0.2e1 / 0.3e1 * t136 * params.eta * t131) - t146 * t92 * (0.2e1 * t160 * t58 * t107 + t150 * params.eta * t131 + 0.6e1 * t154 * t77 * t133 + 0.3e1 * t136 * t133) + t81 * (-0.10e2 / 0.729e3 * t26 * t107 * t90 + 0.8e1 / 0.729e3 * t172 * t25 * t50 * t106 * t34 + t110 - t126)))
  vrho_0_ = 0.2e1 * r0 * t185 + 0.2e1 * t98
  t189 = 0.5e1 / 0.972e3 * t25 * t43
  t197 = 0.5e1 / 0.118098e6 * t113 * s0 * t27 / t18 / t116 / r0 * t123
  t200 = params.eta * t28 * t32
  t211 = t77 * t28
  t235 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t189 - t197 + 0.3e1 * t127 * t92 * (t128 * t33 / 0.4e1 + t136 * t200 / 0.4e1) - t146 * t92 * (-0.3e1 / 0.8e1 * t136 * t33 - 0.3e1 / 0.8e1 * t150 * t200 - 0.3e1 / 0.4e1 * t154 * t211 * t32 - 0.3e1 / 0.4e1 * t160 * t200) + t81 * (0.5e1 / 0.972e3 * t25 * t33 * t90 - t172 * t20 * t24 * t28 * t32 * t34 / 0.243e3 - t189 + t197)))
  vsigma_0_ = 0.2e1 * r0 * t235
  vlapl_0_ = 0.0e0
  t238 = t28 * t48
  t254 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-0.6e1 * t127 * t92 * t128 * t238 - t146 * t92 * (0.6e1 * t154 * t211 * t48 + 0.3e1 * t136 * t238)))
  vtau_0_ = 0.2e1 * r0 * t254
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
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = jnp.pi ** 2
  t24 = t23 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t27 = t22 / t25
  t28 = t27 * s0
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = r0 ** 2
  t33 = 0.1e1 / t19 / t31
  t34 = t30 * t33
  t35 = 0.1e1 / params.kappa
  t39 = 0.1e1 + 0.5e1 / 0.972e3 * t28 * t34 * t35
  t40 = t39 ** (0.1e1 / 0.5e1)
  t41 = t40 ** 2
  t42 = t41 ** 2
  t43 = 0.1e1 / t42
  t46 = 0.5e1 / 0.972e3 * t28 * t34 * t43
  t47 = tau0 * t30
  t49 = 0.1e1 / t19 / r0
  t51 = s0 * t30
  t52 = t51 * t33
  t54 = t47 * t49 - t52 / 0.8e1
  t55 = t54 ** 2
  t56 = t22 ** 2
  t59 = params.eta * s0
  t62 = 0.3e1 / 0.10e2 * t56 * t25 + t59 * t34 / 0.8e1
  t63 = t62 ** 2
  t64 = 0.1e1 / t63
  t66 = -t55 * t64 + 0.1e1
  t67 = t66 ** 2
  t68 = t67 * t66
  t69 = t55 * t54
  t70 = t63 * t62
  t71 = 0.1e1 / t70
  t73 = t55 ** 2
  t75 = params.b * t73 * t55
  t76 = t63 ** 2
  t78 = 0.1e1 / t76 / t63
  t80 = t69 * t71 + t75 * t78 + 0.1e1
  t81 = 0.1e1 / t80
  t82 = t68 * t81
  t85 = 0.5e1 / 0.972e3 * t27 * t52 + params.c
  t87 = t85 * t35 + 0.1e1
  t88 = t87 ** (0.1e1 / 0.5e1)
  t89 = t88 ** 2
  t90 = t89 ** 2
  t91 = 0.1e1 / t90
  t93 = t85 * t91 - t46
  t95 = t82 * t93 + t46 + 0.1e1
  t99 = t17 * t18
  t100 = t31 * r0
  t102 = 0.1e1 / t19 / t100
  t103 = t30 * t102
  t106 = 0.10e2 / 0.729e3 * t28 * t103 * t43
  t109 = t56 / t24 / t23
  t110 = s0 ** 2
  t111 = t109 * t110
  t112 = t31 ** 2
  t119 = 0.1e1 / t42 / t39 * t35
  t122 = 0.20e2 / 0.177147e6 * t111 * t29 / t18 / t112 / t31 * t119
  t123 = t67 * t81
  t124 = t54 * t64
  t127 = t51 * t102
  t129 = -0.5e1 / 0.3e1 * t47 * t33 + t127 / 0.3e1
  t132 = t55 * t71
  t133 = t132 * params.eta
  t136 = -0.2e1 * t124 * t129 - 0.2e1 / 0.3e1 * t133 * t127
  t137 = t93 * t136
  t140 = t80 ** 2
  t141 = 0.1e1 / t140
  t142 = t68 * t141
  t145 = 0.1e1 / t76
  t147 = t69 * t145 * params.eta
  t150 = params.b * t73 * t54
  t155 = 0.1e1 / t76 / t70
  t156 = t75 * t155
  t157 = t59 * t103
  t160 = 0.6e1 * t150 * t78 * t129 + t147 * t127 + 0.3e1 * t132 * t129 + 0.2e1 * t156 * t157
  t167 = 0.1e1 / t90 / t87
  t169 = t85 * t167 * t27
  t174 = -0.10e2 / 0.729e3 * t28 * t103 * t91 + 0.8e1 / 0.729e3 * t169 * t51 * t102 * t35 + t106 - t122
  t176 = -t142 * t93 * t160 + 0.3e1 * t123 * t137 + t82 * t174 - t106 + t122
  t181 = f.my_piecewise3(t2, 0, -t6 * t21 * t95 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t99 * t176)
  t191 = 0.1e1 / t19 / t112
  t192 = t30 * t191
  t195 = 0.110e3 / 0.2187e4 * t28 * t192 * t43
  t198 = 0.1e1 / t18 / t112 / t100
  t199 = t29 * t198
  t202 = 0.20e2 / 0.19683e5 * t111 * t199 * t119
  t203 = t23 ** 2
  t207 = t112 ** 2
  t210 = t39 ** 2
  t214 = params.kappa ** 2
  t215 = 0.1e1 / t214
  t218 = 0.160e3 / 0.4782969e7 / t203 * t110 * s0 / t207 / t31 / t42 / t210 * t215
  t220 = t136 ** 2
  t231 = t129 ** 2
  t234 = t54 * t71
  t240 = t51 * t191
  t242 = 0.40e2 / 0.9e1 * t47 * t102 - 0.11e2 / 0.9e1 * t240
  t245 = t55 * t145
  t246 = params.eta ** 2
  t248 = t110 * t29
  t249 = t248 * t198
  t261 = t160 ** 2
  t294 = t76 ** 2
  t314 = t87 ** 2
  t329 = t195 - t202 + t218 + 0.6e1 * t66 * t81 * t93 * t220 - 0.6e1 * t67 * t141 * t137 * t160 + 0.6e1 * t123 * t174 * t136 + 0.3e1 * t123 * t93 * (-0.2e1 * t231 * t64 - 0.8e1 / 0.3e1 * t234 * t129 * t157 - 0.2e1 * t124 * t242 - 0.4e1 / 0.3e1 * t245 * t246 * t249 + 0.22e2 / 0.9e1 * t133 * t240) + 0.2e1 * t68 / t140 / t80 * t93 * t261 - 0.2e1 * t142 * t174 * t160 - t142 * t93 * (0.6e1 * t234 * t231 + 0.6e1 * t245 * t129 * t157 + 0.3e1 * t132 * t242 + 0.8e1 / 0.3e1 * t69 / t76 / t62 * t246 * t249 - 0.11e2 / 0.3e1 * t147 * t240 + 0.30e2 * params.b * t73 * t78 * t231 + 0.24e2 * t150 * t155 * t129 * t157 + 0.6e1 * t150 * t78 * t242 + 0.28e2 / 0.3e1 * t75 / t294 * t246 * t110 * t199 - 0.22e2 / 0.3e1 * t156 * t59 * t192) + t82 * (0.110e3 / 0.2187e4 * t28 * t192 * t91 - 0.320e3 / 0.531441e6 * t111 * t199 * t167 * t35 + 0.32e2 / 0.59049e5 * t85 / t90 / t314 * t109 * t248 * t198 * t215 - 0.88e2 / 0.2187e4 * t169 * t51 * t191 * t35 - t195 + t202 - t218)
  t334 = f.my_piecewise3(t2, 0, t6 * t17 * t49 * t95 / 0.12e2 - t6 * t21 * t176 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t99 * t329)
  v2rho2_0_ = 0.2e1 * r0 * t334 + 0.4e1 * t181
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
  t23 = 6 ** (0.1e1 / 0.3e1)
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = t23 * t27
  t29 = t28 * s0
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t35 = t31 * t34
  t36 = 0.1e1 / params.kappa
  t40 = 0.1e1 + 0.5e1 / 0.972e3 * t29 * t35 * t36
  t41 = t40 ** (0.1e1 / 0.5e1)
  t42 = t41 ** 2
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t47 = 0.5e1 / 0.972e3 * t29 * t35 * t44
  t48 = tau0 * t31
  t50 = s0 * t31
  t51 = t50 * t34
  t53 = t48 * t21 - t51 / 0.8e1
  t54 = t53 ** 2
  t55 = t23 ** 2
  t58 = params.eta * s0
  t61 = 0.3e1 / 0.10e2 * t55 * t26 + t58 * t35 / 0.8e1
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t65 = -t54 * t63 + 0.1e1
  t66 = t65 ** 2
  t67 = t66 * t65
  t68 = t54 * t53
  t69 = t62 * t61
  t70 = 0.1e1 / t69
  t72 = t54 ** 2
  t74 = params.b * t72 * t54
  t75 = t62 ** 2
  t77 = 0.1e1 / t75 / t62
  t79 = t68 * t70 + t74 * t77 + 0.1e1
  t80 = 0.1e1 / t79
  t81 = t67 * t80
  t84 = 0.5e1 / 0.972e3 * t28 * t51 + params.c
  t86 = t84 * t36 + 0.1e1
  t87 = t86 ** (0.1e1 / 0.5e1)
  t88 = t87 ** 2
  t89 = t88 ** 2
  t90 = 0.1e1 / t89
  t92 = t84 * t90 - t47
  t94 = t81 * t92 + t47 + 0.1e1
  t99 = t17 / t19
  t100 = t32 * r0
  t102 = 0.1e1 / t19 / t100
  t103 = t31 * t102
  t106 = 0.10e2 / 0.729e3 * t29 * t103 * t44
  t109 = t55 / t25 / t24
  t110 = s0 ** 2
  t111 = t109 * t110
  t112 = t32 ** 2
  t119 = 0.1e1 / t43 / t40 * t36
  t122 = 0.20e2 / 0.177147e6 * t111 * t30 / t18 / t112 / t32 * t119
  t123 = t66 * t80
  t124 = t53 * t63
  t127 = t50 * t102
  t129 = -0.5e1 / 0.3e1 * t48 * t34 + t127 / 0.3e1
  t132 = t54 * t70
  t133 = t132 * params.eta
  t136 = -0.2e1 * t124 * t129 - 0.2e1 / 0.3e1 * t133 * t127
  t137 = t92 * t136
  t140 = t79 ** 2
  t141 = 0.1e1 / t140
  t142 = t67 * t141
  t145 = 0.1e1 / t75
  t147 = t68 * t145 * params.eta
  t150 = params.b * t72 * t53
  t151 = t77 * t129
  t155 = 0.1e1 / t75 / t69
  t156 = t74 * t155
  t157 = t58 * t103
  t160 = t147 * t127 + 0.3e1 * t132 * t129 + 0.6e1 * t150 * t151 + 0.2e1 * t156 * t157
  t161 = t92 * t160
  t167 = 0.1e1 / t89 / t86
  t169 = t84 * t167 * t28
  t174 = -0.10e2 / 0.729e3 * t29 * t103 * t90 + 0.8e1 / 0.729e3 * t169 * t50 * t102 * t36 + t106 - t122
  t176 = 0.3e1 * t123 * t137 - t142 * t161 + t81 * t174 - t106 + t122
  t180 = t17 * t18
  t182 = 0.1e1 / t19 / t112
  t183 = t31 * t182
  t186 = 0.110e3 / 0.2187e4 * t29 * t183 * t44
  t189 = 0.1e1 / t18 / t112 / t100
  t190 = t30 * t189
  t193 = 0.20e2 / 0.19683e5 * t111 * t190 * t119
  t194 = t24 ** 2
  t195 = 0.1e1 / t194
  t196 = t110 * s0
  t197 = t195 * t196
  t198 = t112 ** 2
  t201 = t40 ** 2
  t203 = 0.1e1 / t43 / t201
  t205 = params.kappa ** 2
  t206 = 0.1e1 / t205
  t209 = 0.160e3 / 0.4782969e7 * t197 / t198 / t32 * t203 * t206
  t210 = t65 * t80
  t211 = t136 ** 2
  t212 = t92 * t211
  t215 = t66 * t141
  t219 = t174 * t136
  t222 = t129 ** 2
  t225 = t53 * t70
  t226 = t225 * t129
  t231 = t50 * t182
  t233 = 0.40e2 / 0.9e1 * t48 * t102 - 0.11e2 / 0.9e1 * t231
  t236 = t54 * t145
  t237 = params.eta ** 2
  t238 = t236 * t237
  t239 = t110 * t30
  t240 = t239 * t189
  t245 = -0.2e1 * t222 * t63 - 0.8e1 / 0.3e1 * t226 * t157 - 0.2e1 * t124 * t233 - 0.4e1 / 0.3e1 * t238 * t240 + 0.22e2 / 0.9e1 * t133 * t231
  t246 = t92 * t245
  t250 = 0.1e1 / t140 / t79
  t251 = t67 * t250
  t252 = t160 ** 2
  t261 = t236 * t129
  t267 = 0.1e1 / t75 / t61
  t269 = t68 * t267 * t237
  t274 = params.b * t72
  t279 = t150 * t155 * t129
  t285 = t75 ** 2
  t286 = 0.1e1 / t285
  t287 = t74 * t286
  t288 = t237 * t110
  t289 = t288 * t190
  t292 = t58 * t183
  t295 = 0.6e1 * t225 * t222 + 0.6e1 * t261 * t157 + 0.3e1 * t132 * t233 + 0.8e1 / 0.3e1 * t269 * t240 - 0.11e2 / 0.3e1 * t147 * t231 + 0.30e2 * t274 * t77 * t222 + 0.24e2 * t279 * t157 + 0.6e1 * t150 * t77 * t233 + 0.28e2 / 0.3e1 * t287 * t289 - 0.22e2 / 0.3e1 * t156 * t292
  t301 = t167 * t36
  t305 = t86 ** 2
  t307 = 0.1e1 / t89 / t305
  t309 = t84 * t307 * t109
  t318 = 0.110e3 / 0.2187e4 * t29 * t183 * t90 - 0.320e3 / 0.531441e6 * t111 * t190 * t301 + 0.32e2 / 0.59049e5 * t309 * t239 * t189 * t206 - 0.88e2 / 0.2187e4 * t169 * t50 * t182 * t36 - t186 + t193 - t209
  t320 = -0.6e1 * t215 * t137 * t160 - 0.2e1 * t142 * t174 * t160 - t142 * t92 * t295 + 0.2e1 * t251 * t92 * t252 + 0.6e1 * t123 * t219 + 0.3e1 * t123 * t246 + 0.6e1 * t210 * t212 + t81 * t318 + t186 - t193 + t209
  t325 = f.my_piecewise3(t2, 0, t6 * t22 * t94 / 0.12e2 - t6 * t99 * t176 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t180 * t320)
  t357 = t53 * t145
  t368 = t112 * r0
  t370 = 0.1e1 / t19 / t368
  t371 = t50 * t370
  t373 = -0.440e3 / 0.27e2 * t48 * t182 + 0.154e3 / 0.27e2 * t371
  t376 = t54 * t267
  t380 = 0.1e1 / t198 / t100
  t381 = t237 * params.eta * t196 * t380
  t385 = 0.1e1 / t18 / t198
  t386 = t239 * t385
  t410 = t222 * t129
  t452 = t30 * t385
  t456 = t31 * t370
  t467 = 0.6e1 * t150 * t77 * t373 + 0.18e2 * t225 * t129 * t233 + 0.6e1 * t410 * t70 + 0.3e1 * t132 * t373 - 0.132e3 * t279 * t292 + 0.80e2 / 0.9e1 * t68 * t77 * t381 + 0.120e3 * params.b * t68 * t77 * t410 + 0.90e2 * t274 * t151 * t233 + 0.18e2 * t357 * t222 * t157 + 0.9e1 * t236 * t233 * t157 + 0.24e2 * t376 * t129 * t289 - 0.88e2 / 0.3e1 * t269 * t386 + 0.154e3 / 0.9e1 * t147 * t371 + 0.180e3 * t274 * t155 * t222 * t157 + 0.36e2 * t150 * t155 * t233 * t157 + 0.168e3 * t150 * t286 * t129 * t289 - 0.308e3 / 0.3e1 * t287 * t288 * t452 + 0.308e3 / 0.9e1 * t156 * t58 * t456 - 0.33e2 * t261 * t292 + 0.448e3 / 0.9e1 * t74 / t285 / t61 * t381
  t487 = 0.1e1 / t205 / params.kappa
  t501 = 0.1540e4 / 0.6561e4 * t29 * t456 * t44
  t504 = 0.13640e5 / 0.1594323e7 * t111 * t452 * t119
  t508 = 0.3040e4 / 0.4782969e7 * t197 * t380 * t203 * t206
  t509 = t110 ** 2
  t523 = 0.4480e4 / 0.3486784401e10 * t195 * t509 / t19 / t198 / t368 / t43 / t201 / t40 * t487 * t23 * t27 * t31
  t526 = 0.6e1 * t211 * t136 * t80 * t92 + 0.18e2 * t210 * t174 * t211 + 0.9e1 * t123 * t318 * t136 + 0.9e1 * t123 * t174 * t245 + 0.3e1 * t123 * t92 * (-0.6e1 * t129 * t63 * t233 - 0.4e1 * t222 * t70 * params.eta * t127 - 0.8e1 * t357 * t129 * t289 - 0.4e1 * t225 * t233 * t157 + 0.44e2 / 0.3e1 * t226 * t292 - 0.2e1 * t124 * t373 - 0.32e2 / 0.9e1 * t376 * t381 + 0.44e2 / 0.3e1 * t238 * t386 - 0.308e3 / 0.27e2 * t133 * t371) + 0.6e1 * t251 * t174 * t252 - 0.3e1 * t142 * t318 * t160 - 0.3e1 * t142 * t174 * t295 - t142 * t92 * t467 + t81 * (-0.1540e4 / 0.6561e4 * t29 * t456 * t90 + 0.3520e4 / 0.531441e6 * t111 * t452 * t301 - 0.1280e4 / 0.4782969e7 * t197 * t380 * t307 * t206 + 0.3584e4 / 0.14348907e8 * t84 / t89 / t305 / t86 * t195 * t196 * t380 * t487 - 0.352e3 / 0.59049e5 * t309 * t239 * t385 * t206 + 0.1232e4 / 0.6561e4 * t169 * t50 * t370 * t36 + t501 - t504 + t508 - t523) - t508
  t543 = t140 ** 2
  t557 = -0.18e2 * t65 * t141 * t212 * t160 + 0.18e2 * t210 * t137 * t245 - 0.18e2 * t215 * t219 * t160 - 0.9e1 * t215 * t246 * t160 - 0.9e1 * t215 * t137 * t295 - 0.6e1 * t67 / t543 * t92 * t252 * t160 + 0.6e1 * t251 * t161 * t295 - t501 + t504 + t523 + 0.18e2 * t66 * t250 * t137 * t252
  t563 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t34 * t94 + t6 * t22 * t176 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t99 * t320 - 0.3e1 / 0.8e1 * t6 * t180 * (t526 + t557))
  v3rho3_0_ = 0.2e1 * r0 * t563 + 0.6e1 * t325

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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = t29 * s0
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = t32 * t22
  t34 = 0.1e1 / params.kappa
  t38 = 0.1e1 + 0.5e1 / 0.972e3 * t30 * t33 * t34
  t39 = t38 ** (0.1e1 / 0.5e1)
  t40 = t39 ** 2
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t45 = 0.5e1 / 0.972e3 * t30 * t33 * t42
  t46 = tau0 * t32
  t48 = 0.1e1 / t20 / r0
  t50 = s0 * t32
  t51 = t50 * t22
  t53 = t46 * t48 - t51 / 0.8e1
  t54 = t53 ** 2
  t55 = t24 ** 2
  t58 = params.eta * s0
  t61 = 0.3e1 / 0.10e2 * t55 * t27 + t58 * t33 / 0.8e1
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t65 = -t54 * t63 + 0.1e1
  t66 = t65 ** 2
  t67 = t66 * t65
  t68 = t54 * t53
  t69 = t62 * t61
  t70 = 0.1e1 / t69
  t72 = t54 ** 2
  t74 = params.b * t72 * t54
  t75 = t62 ** 2
  t77 = 0.1e1 / t75 / t62
  t79 = t68 * t70 + t74 * t77 + 0.1e1
  t80 = 0.1e1 / t79
  t81 = t67 * t80
  t84 = 0.5e1 / 0.972e3 * t29 * t51 + params.c
  t86 = t84 * t34 + 0.1e1
  t87 = t86 ** (0.1e1 / 0.5e1)
  t88 = t87 ** 2
  t89 = t88 ** 2
  t90 = 0.1e1 / t89
  t92 = t84 * t90 - t45
  t94 = t81 * t92 + t45 + 0.1e1
  t98 = t17 * t48
  t99 = t18 * r0
  t101 = 0.1e1 / t20 / t99
  t102 = t32 * t101
  t105 = 0.10e2 / 0.729e3 * t30 * t102 * t42
  t107 = 0.1e1 / t26 / t25
  t108 = t55 * t107
  t109 = s0 ** 2
  t110 = t108 * t109
  t111 = t18 ** 2
  t112 = t111 * t18
  t118 = 0.1e1 / t41 / t38 * t34
  t121 = 0.20e2 / 0.177147e6 * t110 * t31 / t19 / t112 * t118
  t122 = t66 * t80
  t123 = t53 * t63
  t126 = t50 * t101
  t128 = -0.5e1 / 0.3e1 * t46 * t22 + t126 / 0.3e1
  t131 = t54 * t70
  t132 = t131 * params.eta
  t135 = -0.2e1 * t123 * t128 - 0.2e1 / 0.3e1 * t132 * t126
  t136 = t92 * t135
  t139 = t79 ** 2
  t140 = 0.1e1 / t139
  t141 = t67 * t140
  t144 = 0.1e1 / t75
  t146 = t68 * t144 * params.eta
  t149 = params.b * t72 * t53
  t150 = t77 * t128
  t154 = 0.1e1 / t75 / t69
  t155 = t74 * t154
  t156 = t58 * t102
  t159 = t146 * t126 + 0.3e1 * t131 * t128 + 0.6e1 * t149 * t150 + 0.2e1 * t155 * t156
  t160 = t92 * t159
  t166 = 0.1e1 / t89 / t86
  t168 = t84 * t166 * t29
  t173 = -0.10e2 / 0.729e3 * t30 * t102 * t90 + 0.8e1 / 0.729e3 * t168 * t50 * t101 * t34 + t105 - t121
  t175 = 0.3e1 * t122 * t136 - t141 * t160 + t81 * t173 - t105 + t121
  t180 = t17 / t20
  t182 = 0.1e1 / t20 / t111
  t183 = t32 * t182
  t186 = 0.110e3 / 0.2187e4 * t30 * t183 * t42
  t189 = 0.1e1 / t19 / t111 / t99
  t190 = t31 * t189
  t193 = 0.20e2 / 0.19683e5 * t110 * t190 * t118
  t194 = t25 ** 2
  t195 = 0.1e1 / t194
  t196 = t109 * s0
  t197 = t195 * t196
  t198 = t111 ** 2
  t201 = t38 ** 2
  t203 = 0.1e1 / t41 / t201
  t205 = params.kappa ** 2
  t206 = 0.1e1 / t205
  t209 = 0.160e3 / 0.4782969e7 * t197 / t198 / t18 * t203 * t206
  t210 = t65 * t80
  t211 = t135 ** 2
  t212 = t92 * t211
  t215 = t66 * t140
  t219 = t173 * t135
  t222 = t128 ** 2
  t225 = t53 * t70
  t226 = t225 * t128
  t231 = t50 * t182
  t233 = 0.40e2 / 0.9e1 * t46 * t101 - 0.11e2 / 0.9e1 * t231
  t236 = t54 * t144
  t237 = params.eta ** 2
  t238 = t236 * t237
  t239 = t109 * t31
  t240 = t239 * t189
  t245 = -0.2e1 * t222 * t63 - 0.8e1 / 0.3e1 * t226 * t156 - 0.2e1 * t123 * t233 - 0.4e1 / 0.3e1 * t238 * t240 + 0.22e2 / 0.9e1 * t132 * t231
  t246 = t92 * t245
  t250 = 0.1e1 / t139 / t79
  t251 = t67 * t250
  t252 = t159 ** 2
  t253 = t92 * t252
  t256 = t173 * t159
  t261 = t236 * t128
  t267 = 0.1e1 / t75 / t61
  t269 = t68 * t267 * t237
  t274 = params.b * t72
  t275 = t77 * t222
  t278 = t154 * t128
  t279 = t149 * t278
  t285 = t75 ** 2
  t286 = 0.1e1 / t285
  t287 = t74 * t286
  t288 = t237 * t109
  t289 = t288 * t190
  t292 = t58 * t183
  t295 = 0.6e1 * t225 * t222 + 0.6e1 * t261 * t156 + 0.3e1 * t131 * t233 + 0.8e1 / 0.3e1 * t269 * t240 - 0.11e2 / 0.3e1 * t146 * t231 + 0.30e2 * t274 * t275 + 0.24e2 * t279 * t156 + 0.6e1 * t149 * t77 * t233 + 0.28e2 / 0.3e1 * t287 * t289 - 0.22e2 / 0.3e1 * t155 * t292
  t301 = t166 * t34
  t305 = t86 ** 2
  t307 = 0.1e1 / t89 / t305
  t309 = t84 * t307 * t108
  t318 = 0.110e3 / 0.2187e4 * t30 * t183 * t90 - 0.320e3 / 0.531441e6 * t110 * t190 * t301 + 0.32e2 / 0.59049e5 * t309 * t239 * t189 * t206 - 0.88e2 / 0.2187e4 * t168 * t50 * t182 * t34 - t186 + t193 - t209
  t320 = -0.6e1 * t215 * t136 * t159 - t141 * t92 * t295 + 0.6e1 * t122 * t219 + 0.3e1 * t122 * t246 - 0.2e1 * t141 * t256 + 0.6e1 * t210 * t212 + 0.2e1 * t251 * t253 + t81 * t318 + t186 - t193 + t209
  t324 = t17 * t19
  t325 = t211 * t135
  t326 = t325 * t80
  t329 = t173 * t211
  t332 = t318 * t135
  t335 = t173 * t245
  t338 = t128 * t63
  t341 = t222 * t70
  t342 = t341 * params.eta
  t345 = t53 * t144
  t346 = t345 * t128
  t349 = t225 * t233
  t356 = t111 * r0
  t358 = 0.1e1 / t20 / t356
  t359 = t50 * t358
  t361 = -0.440e3 / 0.27e2 * t46 * t182 + 0.154e3 / 0.27e2 * t359
  t364 = t54 * t267
  t365 = t237 * params.eta
  t366 = t365 * t196
  t368 = 0.1e1 / t198 / t99
  t369 = t366 * t368
  t373 = 0.1e1 / t19 / t198
  t374 = t239 * t373
  t379 = -0.6e1 * t338 * t233 - 0.4e1 * t342 * t126 - 0.8e1 * t346 * t289 - 0.4e1 * t349 * t156 + 0.44e2 / 0.3e1 * t226 * t292 - 0.2e1 * t123 * t361 - 0.32e2 / 0.9e1 * t364 * t369 + 0.44e2 / 0.3e1 * t238 * t374 - 0.308e3 / 0.27e2 * t132 * t359
  t380 = t92 * t379
  t383 = t173 * t252
  t389 = t173 * t295
  t392 = t77 * t361
  t395 = t128 * t233
  t398 = t222 * t128
  t405 = t68 * t77
  t408 = params.b * t68
  t415 = t345 * t222
  t418 = t236 * t233
  t421 = t364 * t128
  t428 = t31 * t373
  t429 = t288 * t428
  t432 = t32 * t358
  t433 = t58 * t432
  t439 = t274 * t154 * t222
  t443 = t149 * t154 * t233
  t447 = t149 * t286 * t128
  t451 = 0.1e1 / t285 / t61
  t452 = t74 * t451
  t455 = 0.6e1 * t149 * t392 + 0.18e2 * t225 * t395 + 0.6e1 * t398 * t70 + 0.3e1 * t131 * t361 - 0.132e3 * t279 * t292 + 0.80e2 / 0.9e1 * t405 * t369 + 0.120e3 * t408 * t77 * t398 + 0.90e2 * t274 * t150 * t233 + 0.18e2 * t415 * t156 + 0.9e1 * t418 * t156 + 0.24e2 * t421 * t289 - 0.88e2 / 0.3e1 * t269 * t374 + 0.154e3 / 0.9e1 * t146 * t359 - 0.308e3 / 0.3e1 * t287 * t429 + 0.308e3 / 0.9e1 * t155 * t433 - 0.33e2 * t261 * t292 + 0.180e3 * t439 * t156 + 0.36e2 * t443 * t156 + 0.168e3 * t447 * t289 + 0.448e3 / 0.9e1 * t452 * t369
  t456 = t92 * t455
  t470 = 0.1e1 / t89 / t305 / t86
  t472 = t84 * t470 * t195
  t473 = t196 * t368
  t475 = 0.1e1 / t205 / params.kappa
  t489 = 0.1540e4 / 0.6561e4 * t30 * t432 * t42
  t492 = 0.13640e5 / 0.1594323e7 * t110 * t428 * t118
  t496 = 0.3040e4 / 0.4782969e7 * t197 * t368 * t203 * t206
  t497 = t109 ** 2
  t498 = t195 * t497
  t504 = 0.1e1 / t41 / t201 / t38
  t509 = t475 * t24 * t28 * t32
  t511 = 0.4480e4 / 0.3486784401e10 * t498 / t20 / t198 / t356 * t504 * t509
  t512 = -0.1540e4 / 0.6561e4 * t30 * t432 * t90 + 0.3520e4 / 0.531441e6 * t110 * t428 * t301 - 0.1280e4 / 0.4782969e7 * t197 * t368 * t307 * t206 + 0.3584e4 / 0.14348907e8 * t472 * t473 * t475 - 0.352e3 / 0.59049e5 * t309 * t239 * t373 * t206 + 0.1232e4 / 0.6561e4 * t168 * t50 * t358 * t34 + t489 - t492 + t496 - t511
  t514 = -0.3e1 * t141 * t318 * t159 + 0.9e1 * t122 * t332 + 0.9e1 * t122 * t335 + 0.3e1 * t122 * t380 - 0.3e1 * t141 * t389 - t141 * t456 + 0.18e2 * t210 * t329 + 0.6e1 * t251 * t383 + 0.6e1 * t326 * t92 + t81 * t512 - t496
  t515 = t65 * t140
  t531 = t139 ** 2
  t532 = 0.1e1 / t531
  t533 = t67 * t532
  t534 = t252 * t159
  t535 = t92 * t534
  t541 = t66 * t250
  t545 = 0.18e2 * t210 * t136 * t245 - 0.9e1 * t215 * t136 * t295 + 0.18e2 * t541 * t136 * t252 - 0.18e2 * t515 * t212 * t159 - 0.18e2 * t215 * t219 * t159 - 0.9e1 * t215 * t246 * t159 + 0.6e1 * t251 * t160 * t295 - 0.6e1 * t533 * t535 - t489 + t492 + t511
  t546 = t514 + t545
  t551 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t94 + t6 * t98 * t175 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t180 * t320 - 0.3e1 / 0.8e1 * t6 * t324 * t546)
  t619 = 0.1e1 / t19 / t198 / r0
  t620 = t31 * t619
  t623 = 0.121880e6 / 0.1594323e7 * t110 * t620 * t118
  t635 = 0.1e1 / t20 / t112
  t636 = t32 * t635
  t639 = 0.26180e5 / 0.19683e5 * t30 * t636 * t42
  t640 = t295 ** 2
  t644 = -0.72e2 * t515 * t92 * t135 * t159 * t245 + 0.72e2 * t541 * t92 * t135 * t295 * t159 - 0.36e2 * t215 * t389 * t135 - 0.12e2 * t215 * t456 * t135 - 0.36e2 * t215 * t332 * t159 - 0.36e2 * t215 * t335 * t159 - 0.12e2 * t215 * t380 * t159 + 0.72e2 * t210 * t219 * t245 + 0.6e1 * t251 * t92 * t640 - t623 + t639
  t654 = t237 ** 2
  t658 = 0.1e1 / t20 / t198 / t112
  t666 = t53 * t267
  t692 = t233 ** 2
  t697 = t50 * t635
  t699 = 0.6160e4 / 0.81e2 * t46 * t358 - 0.2618e4 / 0.81e2 * t697
  t704 = t239 * t619
  t711 = t54 * t77
  t716 = 0.3584e4 / 0.3e1 * t149 * t451 * t128 * t365 * t473 + 0.448e3 / 0.3e1 * t74 / t285 / t62 * t654 * t497 * t658 * t32 + 0.12e2 * t236 * t361 * t156 + 0.96e2 * t666 * t222 * t289 + 0.48e2 * t364 * t233 * t289 + 0.616e3 / 0.3e1 * t236 * params.eta * t50 * t358 * t128 + 0.27412e5 / 0.27e2 * t287 * t288 * t620 - 0.5236e4 / 0.27e2 * t155 * t58 * t636 - 0.132e3 * t415 * t292 - 0.66e2 * t418 * t292 - 0.352e3 * t421 * t429 + 0.36e2 * t341 * t233 + 0.18e2 * t225 * t692 + 0.3e1 * t131 * t699 - 0.2618e4 / 0.27e2 * t146 * t697 + 0.7832e4 / 0.27e2 * t269 * t704 + 0.24e2 * t398 * t144 * params.eta * t126 + 0.320e3 / 0.3e1 * t711 * t365 * t473 * t128
  t720 = t497 * t658 * t32
  t724 = 0.1e1 / t198 / t111
  t725 = t366 * t724
  t735 = t222 ** 2
  t782 = 0.160e3 / 0.9e1 * t68 * t154 * t654 * t720 - 0.9856e4 / 0.9e1 * t452 * t725 + 0.6e1 * t149 * t77 * t699 + 0.24e2 * t225 * t128 * t361 + 0.360e3 * params.b * t54 * t77 * t735 + 0.90e2 * t274 * t77 * t692 - 0.2464e4 * t447 * t429 + 0.960e3 * t408 * t154 * t398 * t156 - 0.1320e4 * t439 * t292 + 0.2464e4 / 0.3e1 * t279 * t433 + 0.1680e4 * t274 * t286 * t222 * t289 + 0.336e3 * t149 * t286 * t233 * t289 + 0.48e2 * t149 * t154 * t361 * t156 + 0.72e2 * t345 * t395 * t156 - 0.264e3 * t443 * t292 + 0.120e3 * t274 * t392 * t128 + 0.720e3 * t408 * t275 * t233 - 0.1760e4 / 0.9e1 * t405 * t725 + 0.720e3 * t274 * t278 * t233 * params.eta * t126
  t832 = -0.3916e4 / 0.27e2 * t238 * t704 + 0.5236e4 / 0.81e2 * t132 * t697 - 0.16e2 * t128 * t70 * t233 * t156 + 0.88e2 / 0.3e1 * t342 * t231 - 0.16e2 * t345 * t233 * t289 - 0.16e2 / 0.3e1 * t225 * t361 * t156 + 0.352e3 / 0.3e1 * t346 * t429 + 0.88e2 / 0.3e1 * t349 * t292 - 0.2464e4 / 0.27e2 * t226 * t433 - 0.16e2 * t222 * t144 * t237 * t240 - 0.256e3 / 0.9e1 * t666 * t128 * t369 + 0.704e3 / 0.9e1 * t364 * t725 - 0.160e3 / 0.27e2 * t711 * t654 * t720 - 0.6e1 * t692 * t63 - 0.8e1 * t338 * t361 - 0.2e1 * t123 * t699
  t858 = 0.439040e6 / 0.10460353203e11 * t498 * t658 * t504 * t509
  t861 = t198 ** 2
  t865 = t201 ** 2
  t870 = t205 ** 2
  t871 = 0.1e1 / t870
  t876 = 0.340480e6 / 0.2541865828329e13 * t195 * t497 * s0 / t19 / t861 / r0 / t41 / t865 * t871 * t55 * t107 * t31
  t893 = t305 ** 2
  t918 = 0.410080e6 / 0.43046721e8 * t197 * t724 * t203 * t206
  t919 = 0.26180e5 / 0.19683e5 * t30 * t636 * t90 - 0.313280e6 / 0.4782969e7 * t110 * t620 * t301 + 0.28160e5 / 0.4782969e7 * t197 * t724 * t307 * t206 - 0.143360e6 / 0.10460353203e11 * t498 * t658 * t470 * t509 + 0.136192e6 / 0.10460353203e11 * t84 / t89 / t893 * t498 * t658 * t871 * t29 * t32 - 0.78848e5 / 0.14348907e8 * t472 * t196 * t724 * t475 + 0.31328e5 / 0.531441e6 * t309 * t239 * t619 * t206 - 0.20944e5 / 0.19683e5 * t168 * t50 * t635 * t34 - t639 + t623 - t918 + t858 - t876
  t924 = t245 ** 2
  t937 = t252 ** 2
  t944 = -t858 + t876 + 0.24e2 * t326 * t173 + t81 * t919 + t918 + 0.8e1 * t251 * t456 * t159 + 0.18e2 * t210 * t92 * t924 - 0.24e2 * t533 * t173 * t534 - 0.4e1 * t141 * t173 * t455 + 0.24e2 * t67 / t531 / t79 * t92 * t937 - 0.6e1 * t141 * t318 * t295
  t951 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t101 * t94 - 0.5e1 / 0.9e1 * t6 * t23 * t175 + t6 * t98 * t320 / 0.2e1 - t6 * t180 * t546 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t324 * (-0.72e2 * t66 * t532 * t535 * t135 + 0.72e2 * t65 * t250 * t212 * t252 + 0.24e2 * t210 * t380 * t135 + 0.72e2 * t541 * t383 * t135 - 0.72e2 * t515 * t329 * t159 - 0.36e2 * t515 * t212 * t295 - 0.18e2 * t215 * t246 * t295 + 0.36e2 * t541 * t246 * t252 + 0.24e2 * t251 * t256 * t295 - 0.36e2 * t533 * t253 * t295 + t644 - t141 * t92 * (t716 + t782) + 0.36e2 * t211 * t80 * t246 - 0.24e2 * t325 * t140 * t160 + 0.3e1 * t122 * t92 * t832 + 0.12e2 * t251 * t318 * t252 - 0.4e1 * t141 * t512 * t159 + 0.12e2 * t122 * t173 * t379 + 0.36e2 * t210 * t318 * t211 + 0.12e2 * t122 * t512 * t135 + 0.18e2 * t122 * t318 * t245 + t944))
  v4rho4_0_ = 0.2e1 * r0 * t951 + 0.8e1 * t551

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
  t44 = 0.1e1 / params.kappa
  t48 = 0.1e1 + 0.5e1 / 0.972e3 * t37 * t43 * t44
  t49 = t48 ** (0.1e1 / 0.5e1)
  t50 = t49 ** 2
  t51 = t50 ** 2
  t52 = 0.1e1 / t51
  t55 = 0.5e1 / 0.972e3 * t37 * t43 * t52
  t60 = tau0 / t40 / r0 - t43 / 0.8e1
  t61 = t60 ** 2
  t62 = t32 ** 2
  t64 = 0.3e1 / 0.10e2 * t62 * t35
  t65 = params.eta * s0
  t68 = t64 + t65 * t42 / 0.8e1
  t69 = t68 ** 2
  t70 = 0.1e1 / t69
  t72 = -t61 * t70 + 0.1e1
  t73 = t72 ** 2
  t74 = t73 * t72
  t75 = t61 * t60
  t76 = t69 * t68
  t77 = 0.1e1 / t76
  t79 = t61 ** 2
  t81 = params.b * t79 * t61
  t82 = t69 ** 2
  t84 = 0.1e1 / t82 / t69
  t86 = t75 * t77 + t81 * t84 + 0.1e1
  t87 = 0.1e1 / t86
  t88 = t74 * t87
  t91 = 0.5e1 / 0.972e3 * t37 * t43 + params.c
  t93 = t91 * t44 + 0.1e1
  t94 = t93 ** (0.1e1 / 0.5e1)
  t95 = t94 ** 2
  t96 = t95 ** 2
  t97 = 0.1e1 / t96
  t99 = t91 * t97 - t55
  t101 = t88 * t99 + t55 + 0.1e1
  t105 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t106 = t105 * f.p.zeta_threshold
  t108 = f.my_piecewise3(t20, t106, t21 * t19)
  t109 = t30 ** 2
  t110 = 0.1e1 / t109
  t111 = t108 * t110
  t114 = t5 * t111 * t101 / 0.8e1
  t115 = t108 * t30
  t116 = t38 * r0
  t118 = 0.1e1 / t40 / t116
  t119 = s0 * t118
  t122 = 0.10e2 / 0.729e3 * t37 * t119 * t52
  t124 = 0.1e1 / t34 / t33
  t125 = t62 * t124
  t126 = s0 ** 2
  t127 = t125 * t126
  t128 = t38 ** 2
  t133 = 0.1e1 / t51 / t48
  t137 = 0.10e2 / 0.177147e6 * t127 / t39 / t128 / t38 * t133 * t44
  t138 = t73 * t87
  t139 = t60 * t70
  t143 = -0.5e1 / 0.3e1 * tau0 * t42 + t119 / 0.3e1
  t146 = t61 * t77
  t147 = t65 * t118
  t150 = -0.2e1 * t139 * t143 - 0.2e1 / 0.3e1 * t146 * t147
  t151 = t99 * t150
  t154 = t86 ** 2
  t155 = 0.1e1 / t154
  t156 = t74 * t155
  t159 = 0.1e1 / t82
  t160 = t75 * t159
  t163 = params.b * t79 * t60
  t168 = 0.1e1 / t82 / t76
  t169 = t81 * t168
  t172 = 0.6e1 * t163 * t84 * t143 + 0.3e1 * t146 * t143 + t160 * t147 + 0.2e1 * t169 * t147
  t179 = 0.1e1 / t96 / t93
  t181 = t91 * t179 * t32
  t182 = t36 * s0
  t187 = -0.10e2 / 0.729e3 * t37 * t119 * t97 + 0.8e1 / 0.729e3 * t181 * t182 * t118 * t44 + t122 - t137
  t189 = -t156 * t99 * t172 + 0.3e1 * t138 * t151 + t88 * t187 - t122 + t137
  t194 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t101 - t114 - 0.3e1 / 0.8e1 * t5 * t115 * t189)
  t196 = r1 <= f.p.dens_threshold
  t197 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t198 = 0.1e1 + t197
  t199 = t198 <= f.p.zeta_threshold
  t200 = t198 ** (0.1e1 / 0.3e1)
  t202 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t205 = f.my_piecewise3(t199, 0, 0.4e1 / 0.3e1 * t200 * t202)
  t206 = t205 * t30
  t207 = r1 ** 2
  t208 = r1 ** (0.1e1 / 0.3e1)
  t209 = t208 ** 2
  t211 = 0.1e1 / t209 / t207
  t212 = s2 * t211
  t216 = 0.1e1 + 0.5e1 / 0.972e3 * t37 * t212 * t44
  t217 = t216 ** (0.1e1 / 0.5e1)
  t218 = t217 ** 2
  t219 = t218 ** 2
  t220 = 0.1e1 / t219
  t223 = 0.5e1 / 0.972e3 * t37 * t212 * t220
  t228 = tau1 / t209 / r1 - t212 / 0.8e1
  t229 = t228 ** 2
  t230 = params.eta * s2
  t233 = t64 + t230 * t211 / 0.8e1
  t234 = t233 ** 2
  t235 = 0.1e1 / t234
  t237 = -t229 * t235 + 0.1e1
  t238 = t237 ** 2
  t239 = t238 * t237
  t240 = t229 * t228
  t241 = t234 * t233
  t242 = 0.1e1 / t241
  t244 = t229 ** 2
  t246 = params.b * t244 * t229
  t247 = t234 ** 2
  t249 = 0.1e1 / t247 / t234
  t251 = t240 * t242 + t246 * t249 + 0.1e1
  t252 = 0.1e1 / t251
  t253 = t239 * t252
  t256 = 0.5e1 / 0.972e3 * t37 * t212 + params.c
  t258 = t256 * t44 + 0.1e1
  t259 = t258 ** (0.1e1 / 0.5e1)
  t260 = t259 ** 2
  t261 = t260 ** 2
  t262 = 0.1e1 / t261
  t264 = t256 * t262 - t223
  t266 = t253 * t264 + t223 + 0.1e1
  t271 = f.my_piecewise3(t199, t106, t200 * t198)
  t272 = t271 * t110
  t275 = t5 * t272 * t266 / 0.8e1
  t277 = f.my_piecewise3(t196, 0, -0.3e1 / 0.8e1 * t5 * t206 * t266 - t275)
  t279 = t21 ** 2
  t280 = 0.1e1 / t279
  t281 = t26 ** 2
  t286 = t16 / t22 / t6
  t288 = -0.2e1 * t23 + 0.2e1 * t286
  t289 = f.my_piecewise5(t10, 0, t14, 0, t288)
  t293 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t280 * t281 + 0.4e1 / 0.3e1 * t21 * t289)
  t300 = t5 * t29 * t110 * t101
  t306 = 0.1e1 / t109 / t6
  t310 = t5 * t108 * t306 * t101 / 0.12e2
  t312 = t5 * t111 * t189
  t315 = 0.1e1 / t40 / t128
  t316 = s0 * t315
  t319 = 0.110e3 / 0.2187e4 * t37 * t316 * t52
  t322 = 0.1e1 / t39 / t128 / t116
  t326 = 0.10e2 / 0.19683e5 * t127 * t322 * t133 * t44
  t327 = t33 ** 2
  t328 = 0.1e1 / t327
  t331 = t128 ** 2
  t334 = t48 ** 2
  t338 = params.kappa ** 2
  t339 = 0.1e1 / t338
  t342 = 0.40e2 / 0.4782969e7 * t328 * t126 * s0 / t331 / t38 / t51 / t334 * t339
  t344 = t150 ** 2
  t355 = t143 ** 2
  t358 = t60 * t77
  t365 = 0.40e2 / 0.9e1 * tau0 * t118 - 0.11e2 / 0.9e1 * t316
  t368 = t61 * t159
  t369 = params.eta ** 2
  t371 = t369 * t126 * t322
  t374 = t65 * t315
  t384 = t172 ** 2
  t417 = t82 ** 2
  t434 = t93 ** 2
  t450 = t319 - t326 + t342 + 0.6e1 * t72 * t87 * t99 * t344 - 0.6e1 * t73 * t155 * t151 * t172 + 0.6e1 * t138 * t187 * t150 + 0.3e1 * t138 * t99 * (-0.2e1 * t355 * t70 - 0.8e1 / 0.3e1 * t358 * t143 * t147 - 0.2e1 * t139 * t365 - 0.2e1 / 0.3e1 * t368 * t371 + 0.22e2 / 0.9e1 * t146 * t374) + 0.2e1 * t74 / t154 / t86 * t99 * t384 - 0.2e1 * t156 * t187 * t172 - t156 * t99 * (0.6e1 * t358 * t355 + 0.6e1 * t368 * t143 * t147 + 0.3e1 * t146 * t365 + 0.4e1 / 0.3e1 * t75 / t82 / t68 * t371 - 0.11e2 / 0.3e1 * t160 * t374 + 0.30e2 * params.b * t79 * t84 * t355 + 0.24e2 * t163 * t168 * t143 * params.eta * t119 + 0.6e1 * t163 * t84 * t365 + 0.14e2 / 0.3e1 * t81 / t417 * t371 - 0.22e2 / 0.3e1 * t169 * t374) + t88 * (0.110e3 / 0.2187e4 * t37 * t316 * t97 - 0.160e3 / 0.531441e6 * t127 * t322 * t179 * t44 + 0.16e2 / 0.59049e5 * t91 / t96 / t434 * t62 * t124 * t126 * t322 * t339 - 0.88e2 / 0.2187e4 * t181 * t182 * t315 * t44 - t319 + t326 - t342)
  t455 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t293 * t30 * t101 - t300 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t189 + t310 - t312 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t115 * t450)
  t456 = t200 ** 2
  t457 = 0.1e1 / t456
  t458 = t202 ** 2
  t462 = f.my_piecewise5(t14, 0, t10, 0, -t288)
  t466 = f.my_piecewise3(t199, 0, 0.4e1 / 0.9e1 * t457 * t458 + 0.4e1 / 0.3e1 * t200 * t462)
  t473 = t5 * t205 * t110 * t266
  t478 = t5 * t271 * t306 * t266 / 0.12e2
  t480 = f.my_piecewise3(t196, 0, -0.3e1 / 0.8e1 * t5 * t466 * t30 * t266 - t473 / 0.4e1 + t478)
  d11 = 0.2e1 * t194 + 0.2e1 * t277 + t6 * (t455 + t480)
  t483 = -t7 - t24
  t484 = f.my_piecewise5(t10, 0, t14, 0, t483)
  t487 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t484)
  t488 = t487 * t30
  t493 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t488 * t101 - t114)
  t495 = f.my_piecewise5(t14, 0, t10, 0, -t483)
  t498 = f.my_piecewise3(t199, 0, 0.4e1 / 0.3e1 * t200 * t495)
  t499 = t498 * t30
  t503 = t271 * t30
  t504 = t207 * r1
  t506 = 0.1e1 / t209 / t504
  t507 = s2 * t506
  t510 = 0.10e2 / 0.729e3 * t37 * t507 * t220
  t511 = s2 ** 2
  t512 = t125 * t511
  t513 = t207 ** 2
  t518 = 0.1e1 / t219 / t216
  t522 = 0.10e2 / 0.177147e6 * t512 / t208 / t513 / t207 * t518 * t44
  t523 = t238 * t252
  t524 = t228 * t235
  t528 = -0.5e1 / 0.3e1 * tau1 * t211 + t507 / 0.3e1
  t531 = t229 * t242
  t532 = t230 * t506
  t535 = -0.2e1 * t524 * t528 - 0.2e1 / 0.3e1 * t531 * t532
  t536 = t264 * t535
  t539 = t251 ** 2
  t540 = 0.1e1 / t539
  t541 = t239 * t540
  t544 = 0.1e1 / t247
  t545 = t240 * t544
  t548 = params.b * t244 * t228
  t553 = 0.1e1 / t247 / t241
  t554 = t246 * t553
  t557 = 0.6e1 * t548 * t249 * t528 + 0.3e1 * t531 * t528 + t545 * t532 + 0.2e1 * t554 * t532
  t564 = 0.1e1 / t261 / t258
  t566 = t256 * t564 * t32
  t567 = t36 * s2
  t572 = -0.10e2 / 0.729e3 * t37 * t507 * t262 + 0.8e1 / 0.729e3 * t566 * t567 * t506 * t44 + t510 - t522
  t574 = -t541 * t264 * t557 + t253 * t572 + 0.3e1 * t523 * t536 - t510 + t522
  t579 = f.my_piecewise3(t196, 0, -0.3e1 / 0.8e1 * t5 * t499 * t266 - t275 - 0.3e1 / 0.8e1 * t5 * t503 * t574)
  t583 = 0.2e1 * t286
  t584 = f.my_piecewise5(t10, 0, t14, 0, t583)
  t588 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t280 * t484 * t26 + 0.4e1 / 0.3e1 * t21 * t584)
  t595 = t5 * t487 * t110 * t101
  t603 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t588 * t30 * t101 - t595 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t488 * t189 - t300 / 0.8e1 + t310 - t312 / 0.8e1)
  t607 = f.my_piecewise5(t14, 0, t10, 0, -t583)
  t611 = f.my_piecewise3(t199, 0, 0.4e1 / 0.9e1 * t457 * t495 * t202 + 0.4e1 / 0.3e1 * t200 * t607)
  t618 = t5 * t498 * t110 * t266
  t625 = t5 * t272 * t574
  t628 = f.my_piecewise3(t196, 0, -0.3e1 / 0.8e1 * t5 * t611 * t30 * t266 - t618 / 0.8e1 - t473 / 0.8e1 + t478 - 0.3e1 / 0.8e1 * t5 * t206 * t574 - t625 / 0.8e1)
  d12 = t194 + t277 + t493 + t579 + t6 * (t603 + t628)
  t633 = t484 ** 2
  t637 = 0.2e1 * t23 + 0.2e1 * t286
  t638 = f.my_piecewise5(t10, 0, t14, 0, t637)
  t642 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t280 * t633 + 0.4e1 / 0.3e1 * t21 * t638)
  t649 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t642 * t30 * t101 - t595 / 0.4e1 + t310)
  t650 = t495 ** 2
  t654 = f.my_piecewise5(t14, 0, t10, 0, -t637)
  t658 = f.my_piecewise3(t199, 0, 0.4e1 / 0.9e1 * t457 * t650 + 0.4e1 / 0.3e1 * t200 * t654)
  t669 = 0.1e1 / t209 / t513
  t670 = s2 * t669
  t673 = 0.110e3 / 0.2187e4 * t37 * t670 * t220
  t676 = 0.1e1 / t208 / t513 / t504
  t680 = 0.10e2 / 0.19683e5 * t512 * t676 * t518 * t44
  t683 = t513 ** 2
  t686 = t216 ** 2
  t692 = 0.40e2 / 0.4782969e7 * t328 * t511 * s2 / t683 / t207 / t219 / t686 * t339
  t694 = t535 ** 2
  t705 = t528 ** 2
  t708 = t228 * t242
  t715 = 0.40e2 / 0.9e1 * tau1 * t506 - 0.11e2 / 0.9e1 * t670
  t718 = t229 * t544
  t720 = t369 * t511 * t676
  t723 = t230 * t669
  t733 = t557 ** 2
  t766 = t247 ** 2
  t783 = t258 ** 2
  t799 = t673 - t680 + t692 + 0.6e1 * t237 * t252 * t264 * t694 - 0.6e1 * t238 * t540 * t536 * t557 + 0.6e1 * t523 * t572 * t535 + 0.3e1 * t523 * t264 * (-0.2e1 * t705 * t235 - 0.8e1 / 0.3e1 * t708 * t528 * t532 - 0.2e1 * t524 * t715 - 0.2e1 / 0.3e1 * t718 * t720 + 0.22e2 / 0.9e1 * t531 * t723) + 0.2e1 * t239 / t539 / t251 * t264 * t733 - 0.2e1 * t541 * t572 * t557 - t541 * t264 * (0.6e1 * t708 * t705 + 0.6e1 * t718 * t528 * t532 + 0.3e1 * t531 * t715 + 0.4e1 / 0.3e1 * t240 / t247 / t233 * t720 - 0.11e2 / 0.3e1 * t545 * t723 + 0.30e2 * params.b * t244 * t249 * t705 + 0.24e2 * t548 * t553 * t528 * params.eta * t507 + 0.6e1 * t548 * t249 * t715 + 0.14e2 / 0.3e1 * t246 / t766 * t720 - 0.22e2 / 0.3e1 * t554 * t723) + t253 * (0.110e3 / 0.2187e4 * t37 * t670 * t262 - 0.160e3 / 0.531441e6 * t512 * t676 * t564 * t44 + 0.16e2 / 0.59049e5 * t256 / t261 / t783 * t62 * t124 * t511 * t676 * t339 - 0.88e2 / 0.2187e4 * t566 * t567 * t669 * t44 - t673 + t680 - t692)
  t804 = f.my_piecewise3(t196, 0, -0.3e1 / 0.8e1 * t5 * t658 * t30 * t266 - t618 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t499 * t574 + t478 - t625 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t503 * t799)
  d22 = 0.2e1 * t493 + 0.2e1 * t579 + t6 * (t649 + t804)
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
  t56 = 0.1e1 / params.kappa
  t60 = 0.1e1 + 0.5e1 / 0.972e3 * t49 * t55 * t56
  t61 = t60 ** (0.1e1 / 0.5e1)
  t62 = t61 ** 2
  t63 = t62 ** 2
  t64 = 0.1e1 / t63
  t67 = 0.5e1 / 0.972e3 * t49 * t55 * t64
  t72 = tau0 / t52 / r0 - t55 / 0.8e1
  t73 = t72 ** 2
  t74 = t44 ** 2
  t76 = 0.3e1 / 0.10e2 * t74 * t47
  t77 = params.eta * s0
  t80 = t76 + t77 * t54 / 0.8e1
  t81 = t80 ** 2
  t82 = 0.1e1 / t81
  t84 = -t73 * t82 + 0.1e1
  t85 = t84 ** 2
  t86 = t85 * t84
  t87 = t73 * t72
  t88 = t81 * t80
  t89 = 0.1e1 / t88
  t91 = t73 ** 2
  t93 = params.b * t91 * t73
  t94 = t81 ** 2
  t96 = 0.1e1 / t94 / t81
  t98 = t87 * t89 + t93 * t96 + 0.1e1
  t99 = 0.1e1 / t98
  t100 = t86 * t99
  t103 = 0.5e1 / 0.972e3 * t49 * t55 + params.c
  t105 = t103 * t56 + 0.1e1
  t106 = t105 ** (0.1e1 / 0.5e1)
  t107 = t106 ** 2
  t108 = t107 ** 2
  t109 = 0.1e1 / t108
  t111 = t103 * t109 - t67
  t113 = t100 * t111 + t67 + 0.1e1
  t119 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t120 = t42 ** 2
  t121 = 0.1e1 / t120
  t122 = t119 * t121
  t126 = t119 * t42
  t127 = t50 * r0
  t129 = 0.1e1 / t52 / t127
  t130 = s0 * t129
  t133 = 0.10e2 / 0.729e3 * t49 * t130 * t64
  t135 = 0.1e1 / t46 / t45
  t137 = s0 ** 2
  t138 = t74 * t135 * t137
  t139 = t50 ** 2
  t144 = 0.1e1 / t63 / t60
  t148 = 0.10e2 / 0.177147e6 * t138 / t51 / t139 / t50 * t144 * t56
  t149 = t85 * t99
  t150 = t72 * t82
  t154 = -0.5e1 / 0.3e1 * tau0 * t54 + t130 / 0.3e1
  t157 = t73 * t89
  t158 = t77 * t129
  t161 = -0.2e1 * t150 * t154 - 0.2e1 / 0.3e1 * t157 * t158
  t162 = t111 * t161
  t165 = t98 ** 2
  t166 = 0.1e1 / t165
  t167 = t86 * t166
  t170 = 0.1e1 / t94
  t171 = t87 * t170
  t174 = params.b * t91 * t72
  t175 = t96 * t154
  t179 = 0.1e1 / t94 / t88
  t180 = t93 * t179
  t183 = 0.3e1 * t157 * t154 + t171 * t158 + 0.2e1 * t180 * t158 + 0.6e1 * t174 * t175
  t184 = t111 * t183
  t190 = 0.1e1 / t108 / t105
  t192 = t103 * t190 * t44
  t193 = t48 * s0
  t198 = -0.10e2 / 0.729e3 * t49 * t130 * t109 + 0.8e1 / 0.729e3 * t192 * t193 * t129 * t56 + t133 - t148
  t200 = t100 * t198 + 0.3e1 * t149 * t162 - t167 * t184 - t133 + t148
  t204 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t205 = t204 * f.p.zeta_threshold
  t207 = f.my_piecewise3(t20, t205, t21 * t19)
  t209 = 0.1e1 / t120 / t6
  t210 = t207 * t209
  t214 = t207 * t121
  t218 = t207 * t42
  t220 = 0.1e1 / t52 / t139
  t221 = s0 * t220
  t224 = 0.110e3 / 0.2187e4 * t49 * t221 * t64
  t227 = 0.1e1 / t51 / t139 / t127
  t231 = 0.10e2 / 0.19683e5 * t138 * t227 * t144 * t56
  t232 = t45 ** 2
  t233 = 0.1e1 / t232
  t234 = t137 * s0
  t235 = t233 * t234
  t236 = t139 ** 2
  t239 = t60 ** 2
  t241 = 0.1e1 / t63 / t239
  t243 = params.kappa ** 2
  t244 = 0.1e1 / t243
  t247 = 0.40e2 / 0.4782969e7 * t235 / t236 / t50 * t241 * t244
  t248 = t84 * t99
  t249 = t161 ** 2
  t250 = t111 * t249
  t253 = t85 * t166
  t257 = t198 * t161
  t260 = t154 ** 2
  t263 = t72 * t89
  t264 = t263 * t154
  t270 = 0.40e2 / 0.9e1 * tau0 * t129 - 0.11e2 / 0.9e1 * t221
  t273 = t73 * t170
  t274 = params.eta ** 2
  t275 = t274 * t137
  t276 = t275 * t227
  t279 = t77 * t220
  t282 = -0.2e1 * t260 * t82 - 0.8e1 / 0.3e1 * t264 * t158 - 0.2e1 * t150 * t270 - 0.2e1 / 0.3e1 * t273 * t276 + 0.22e2 / 0.9e1 * t157 * t279
  t283 = t111 * t282
  t287 = 0.1e1 / t165 / t98
  t288 = t86 * t287
  t289 = t183 ** 2
  t298 = t273 * t154
  t304 = 0.1e1 / t94 / t80
  t305 = t87 * t304
  t310 = params.b * t91
  t314 = t174 * t179
  t315 = t154 * params.eta
  t322 = t94 ** 2
  t323 = 0.1e1 / t322
  t324 = t93 * t323
  t329 = 0.6e1 * t263 * t260 + 0.6e1 * t298 * t158 + 0.3e1 * t157 * t270 + 0.4e1 / 0.3e1 * t305 * t276 - 0.11e2 / 0.3e1 * t171 * t279 + 0.30e2 * t310 * t96 * t260 + 0.24e2 * t314 * t315 * t130 + 0.6e1 * t174 * t96 * t270 + 0.14e2 / 0.3e1 * t324 * t276 - 0.22e2 / 0.3e1 * t180 * t279
  t339 = t105 ** 2
  t341 = 0.1e1 / t108 / t339
  t343 = t103 * t341 * t74
  t344 = t135 * t137
  t353 = 0.110e3 / 0.2187e4 * t49 * t221 * t109 - 0.160e3 / 0.531441e6 * t138 * t227 * t190 * t56 + 0.16e2 / 0.59049e5 * t343 * t344 * t227 * t244 - 0.88e2 / 0.2187e4 * t192 * t193 * t220 * t56 - t224 + t231 - t247
  t355 = -t167 * t111 * t329 + 0.2e1 * t288 * t111 * t289 - 0.6e1 * t253 * t162 * t183 - 0.2e1 * t167 * t198 * t183 + t100 * t353 + 0.6e1 * t149 * t257 + 0.3e1 * t149 * t283 + 0.6e1 * t248 * t250 + t224 - t231 + t247
  t360 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t113 - t5 * t122 * t113 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t126 * t200 + t5 * t210 * t113 / 0.12e2 - t5 * t214 * t200 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t218 * t355)
  t362 = r1 <= f.p.dens_threshold
  t363 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t364 = 0.1e1 + t363
  t365 = t364 <= f.p.zeta_threshold
  t366 = t364 ** (0.1e1 / 0.3e1)
  t367 = t366 ** 2
  t368 = 0.1e1 / t367
  t370 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t371 = t370 ** 2
  t375 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t379 = f.my_piecewise3(t365, 0, 0.4e1 / 0.9e1 * t368 * t371 + 0.4e1 / 0.3e1 * t366 * t375)
  t381 = r1 ** 2
  t382 = r1 ** (0.1e1 / 0.3e1)
  t383 = t382 ** 2
  t385 = 0.1e1 / t383 / t381
  t386 = s2 * t385
  t391 = (0.1e1 + 0.5e1 / 0.972e3 * t49 * t386 * t56) ** (0.1e1 / 0.5e1)
  t392 = t391 ** 2
  t393 = t392 ** 2
  t397 = 0.5e1 / 0.972e3 * t49 * t386 / t393
  t402 = tau1 / t383 / r1 - t386 / 0.8e1
  t403 = t402 ** 2
  t407 = t76 + params.eta * s2 * t385 / 0.8e1
  t408 = t407 ** 2
  t411 = 0.1e1 - t403 / t408
  t412 = t411 ** 2
  t418 = t403 ** 2
  t421 = t408 ** 2
  t430 = 0.5e1 / 0.972e3 * t49 * t386 + params.c
  t433 = (t430 * t56 + 0.1e1) ** (0.1e1 / 0.5e1)
  t434 = t433 ** 2
  t435 = t434 ** 2
  t440 = 0.1e1 + t397 + t412 * t411 / (0.1e1 + t403 * t402 / t408 / t407 + params.b * t418 * t403 / t421 / t408) * (t430 / t435 - t397)
  t446 = f.my_piecewise3(t365, 0, 0.4e1 / 0.3e1 * t366 * t370)
  t452 = f.my_piecewise3(t365, t205, t366 * t364)
  t458 = f.my_piecewise3(t362, 0, -0.3e1 / 0.8e1 * t5 * t379 * t42 * t440 - t5 * t446 * t121 * t440 / 0.4e1 + t5 * t452 * t209 * t440 / 0.12e2)
  t468 = t24 ** 2
  t472 = 0.6e1 * t33 - 0.6e1 * t16 / t468
  t473 = f.my_piecewise5(t10, 0, t14, 0, t472)
  t477 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t473)
  t500 = 0.1e1 / t120 / t24
  t522 = t139 * r0
  t524 = 0.1e1 / t52 / t522
  t525 = s0 * t524
  t527 = -0.440e3 / 0.27e2 * tau0 * t220 + 0.154e3 / 0.27e2 * t525
  t535 = 0.1e1 / t236 / t127
  t536 = t274 * params.eta * t234 * t535
  t540 = t260 * t154
  t569 = 0.1e1 / t51 / t236
  t570 = t275 * t569
  t573 = t77 * t524
  t579 = t72 * t170
  t586 = t73 * t304
  t599 = 0.18e2 * t263 * t154 * t270 + 0.6e1 * t174 * t96 * t527 + 0.20e2 / 0.9e1 * t87 * t96 * t536 + 0.120e3 * params.b * t87 * t96 * t540 + 0.90e2 * t310 * t175 * t270 + 0.6e1 * t540 * t89 + 0.3e1 * t157 * t527 - 0.33e2 * t298 * t279 + 0.180e3 * t310 * t179 * t260 * params.eta * t130 + 0.36e2 * t314 * t270 * params.eta * t130 + 0.84e2 * t174 * t323 * t154 * t274 * t137 * t227 - 0.154e3 / 0.3e1 * t324 * t570 + 0.308e3 / 0.9e1 * t180 * t573 - 0.132e3 * t314 * t315 * t221 + 0.18e2 * t579 * t260 * t158 + 0.9e1 * t273 * t270 * t158 + 0.12e2 * t586 * t154 * t276 - 0.44e2 / 0.3e1 * t305 * t570 + 0.154e3 / 0.9e1 * t171 * t573 + 0.112e3 / 0.9e1 * t93 / t322 / t80 * t536
  t605 = 0.760e3 / 0.4782969e7 * t235 * t535 * t241 * t244
  t622 = t165 ** 2
  t632 = -0.3e1 * t167 * t353 * t183 - 0.3e1 * t167 * t198 * t329 - t167 * t111 * t599 - t605 - 0.18e2 * t84 * t166 * t250 * t183 + 0.18e2 * t248 * t162 * t282 - 0.18e2 * t253 * t257 * t183 - 0.9e1 * t253 * t283 * t183 - 0.9e1 * t253 * t162 * t329 - 0.6e1 * t86 / t622 * t111 * t289 * t183 + 0.6e1 * t288 * t184 * t329
  t651 = 0.1e1 / t243 / params.kappa
  t665 = 0.1540e4 / 0.6561e4 * t49 * t525 * t64
  t669 = 0.6820e4 / 0.1594323e7 * t138 * t569 * t144 * t56
  t670 = t137 ** 2
  t682 = 0.1120e4 / 0.3486784401e10 * t233 * t670 / t52 / t236 / t522 / t63 / t239 / t60 * t651 * t49
  t731 = t100 * (-0.1540e4 / 0.6561e4 * t49 * t525 * t109 + 0.1760e4 / 0.531441e6 * t138 * t569 * t190 * t56 - 0.320e3 / 0.4782969e7 * t235 * t535 * t341 * t244 + 0.896e3 / 0.14348907e8 * t103 / t108 / t339 / t105 * t233 * t234 * t535 * t651 - 0.176e3 / 0.59049e5 * t343 * t344 * t569 * t244 + 0.1232e4 / 0.6561e4 * t192 * t193 * t524 * t56 + t665 - t669 + t605 - t682) + t682 + 0.6e1 * t249 * t161 * t99 * t111 + 0.18e2 * t248 * t198 * t249 + 0.9e1 * t149 * t353 * t161 + 0.9e1 * t149 * t198 * t282 + 0.3e1 * t149 * t111 * (-0.6e1 * t154 * t82 * t270 - 0.4e1 * t260 * t89 * t158 - 0.4e1 * t579 * t154 * t276 - 0.4e1 * t263 * t270 * t158 + 0.44e2 / 0.3e1 * t264 * t279 - 0.2e1 * t150 * t527 - 0.8e1 / 0.9e1 * t586 * t536 + 0.22e2 / 0.3e1 * t273 * t570 - 0.308e3 / 0.27e2 * t157 * t573) + 0.6e1 * t288 * t198 * t289 - t665 + t669 + 0.18e2 * t85 * t287 * t162 * t289
  t737 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t477 * t42 * t113 - 0.3e1 / 0.8e1 * t5 * t41 * t121 * t113 - 0.9e1 / 0.8e1 * t5 * t43 * t200 + t5 * t119 * t209 * t113 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t122 * t200 - 0.9e1 / 0.8e1 * t5 * t126 * t355 - 0.5e1 / 0.36e2 * t5 * t207 * t500 * t113 + t5 * t210 * t200 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t214 * t355 - 0.3e1 / 0.8e1 * t5 * t218 * (t632 + t731))
  t747 = f.my_piecewise5(t14, 0, t10, 0, -t472)
  t751 = f.my_piecewise3(t365, 0, -0.8e1 / 0.27e2 / t367 / t364 * t371 * t370 + 0.4e1 / 0.3e1 * t368 * t370 * t375 + 0.4e1 / 0.3e1 * t366 * t747)
  t769 = f.my_piecewise3(t362, 0, -0.3e1 / 0.8e1 * t5 * t751 * t42 * t440 - 0.3e1 / 0.8e1 * t5 * t379 * t121 * t440 + t5 * t446 * t209 * t440 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t452 * t500 * t440)
  d111 = 0.3e1 * t360 + 0.3e1 * t458 + t6 * (t737 + t769)

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
  t56 = 6 ** (0.1e1 / 0.3e1)
  t57 = jnp.pi ** 2
  t58 = t57 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t60 = 0.1e1 / t59
  t61 = t56 * t60
  t62 = r0 ** 2
  t63 = r0 ** (0.1e1 / 0.3e1)
  t64 = t63 ** 2
  t66 = 0.1e1 / t64 / t62
  t67 = s0 * t66
  t68 = 0.1e1 / params.kappa
  t72 = 0.1e1 + 0.5e1 / 0.972e3 * t61 * t67 * t68
  t73 = t72 ** (0.1e1 / 0.5e1)
  t74 = t73 ** 2
  t75 = t74 ** 2
  t76 = 0.1e1 / t75
  t79 = 0.5e1 / 0.972e3 * t61 * t67 * t76
  t84 = tau0 / t64 / r0 - t67 / 0.8e1
  t85 = t84 ** 2
  t86 = t56 ** 2
  t88 = 0.3e1 / 0.10e2 * t86 * t59
  t89 = params.eta * s0
  t92 = t88 + t89 * t66 / 0.8e1
  t93 = t92 ** 2
  t94 = 0.1e1 / t93
  t96 = -t85 * t94 + 0.1e1
  t97 = t96 ** 2
  t98 = t97 * t96
  t99 = t85 * t84
  t100 = t93 * t92
  t101 = 0.1e1 / t100
  t103 = t85 ** 2
  t105 = params.b * t103 * t85
  t106 = t93 ** 2
  t108 = 0.1e1 / t106 / t93
  t110 = t99 * t101 + t105 * t108 + 0.1e1
  t111 = 0.1e1 / t110
  t112 = t98 * t111
  t115 = 0.5e1 / 0.972e3 * t61 * t67 + params.c
  t117 = t115 * t68 + 0.1e1
  t118 = t117 ** (0.1e1 / 0.5e1)
  t119 = t118 ** 2
  t120 = t119 ** 2
  t121 = 0.1e1 / t120
  t123 = t115 * t121 - t79
  t125 = t112 * t123 + t79 + 0.1e1
  t134 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t135 = t54 ** 2
  t136 = 0.1e1 / t135
  t137 = t134 * t136
  t141 = t134 * t54
  t142 = t62 * r0
  t144 = 0.1e1 / t64 / t142
  t145 = s0 * t144
  t148 = 0.10e2 / 0.729e3 * t61 * t145 * t76
  t150 = 0.1e1 / t58 / t57
  t151 = t86 * t150
  t152 = s0 ** 2
  t153 = t151 * t152
  t154 = t62 ** 2
  t155 = t154 * t62
  t159 = 0.1e1 / t75 / t72
  t163 = 0.10e2 / 0.177147e6 * t153 / t63 / t155 * t159 * t68
  t164 = t97 * t111
  t165 = t84 * t94
  t169 = -0.5e1 / 0.3e1 * tau0 * t66 + t145 / 0.3e1
  t172 = t85 * t101
  t173 = t89 * t144
  t176 = -0.2e1 * t165 * t169 - 0.2e1 / 0.3e1 * t172 * t173
  t177 = t123 * t176
  t180 = t110 ** 2
  t181 = 0.1e1 / t180
  t182 = t98 * t181
  t185 = 0.1e1 / t106
  t186 = t99 * t185
  t189 = params.b * t103 * t84
  t190 = t108 * t169
  t194 = 0.1e1 / t106 / t100
  t195 = t105 * t194
  t198 = 0.3e1 * t172 * t169 + t186 * t173 + 0.2e1 * t195 * t173 + 0.6e1 * t189 * t190
  t199 = t123 * t198
  t205 = 0.1e1 / t120 / t117
  t207 = t115 * t205 * t56
  t208 = t60 * s0
  t213 = -0.10e2 / 0.729e3 * t61 * t145 * t121 + 0.8e1 / 0.729e3 * t207 * t208 * t144 * t68 + t148 - t163
  t215 = t112 * t213 + 0.3e1 * t164 * t177 - t182 * t199 - t148 + t163
  t221 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t223 = 0.1e1 / t135 / t6
  t224 = t221 * t223
  t228 = t221 * t136
  t232 = t221 * t54
  t234 = 0.1e1 / t64 / t154
  t235 = s0 * t234
  t238 = 0.110e3 / 0.2187e4 * t61 * t235 * t76
  t241 = 0.1e1 / t63 / t154 / t142
  t245 = 0.10e2 / 0.19683e5 * t153 * t241 * t159 * t68
  t246 = t57 ** 2
  t247 = 0.1e1 / t246
  t248 = t152 * s0
  t249 = t247 * t248
  t250 = t154 ** 2
  t253 = t72 ** 2
  t255 = 0.1e1 / t75 / t253
  t257 = params.kappa ** 2
  t258 = 0.1e1 / t257
  t261 = 0.40e2 / 0.4782969e7 * t249 / t250 / t62 * t255 * t258
  t262 = t96 * t111
  t263 = t176 ** 2
  t264 = t123 * t263
  t267 = t97 * t181
  t271 = t213 * t176
  t274 = t169 ** 2
  t277 = t84 * t101
  t278 = t277 * t169
  t284 = 0.40e2 / 0.9e1 * tau0 * t144 - 0.11e2 / 0.9e1 * t235
  t287 = t85 * t185
  t288 = params.eta ** 2
  t289 = t288 * t152
  t290 = t289 * t241
  t293 = t89 * t234
  t296 = -0.2e1 * t274 * t94 - 0.8e1 / 0.3e1 * t278 * t173 - 0.2e1 * t165 * t284 - 0.2e1 / 0.3e1 * t287 * t290 + 0.22e2 / 0.9e1 * t172 * t293
  t297 = t123 * t296
  t301 = 0.1e1 / t180 / t110
  t302 = t98 * t301
  t303 = t198 ** 2
  t304 = t123 * t303
  t312 = t287 * t169
  t318 = 0.1e1 / t106 / t92
  t319 = t99 * t318
  t324 = params.b * t103
  t325 = t108 * t274
  t328 = t189 * t194
  t329 = t169 * params.eta
  t336 = t106 ** 2
  t337 = 0.1e1 / t336
  t338 = t105 * t337
  t343 = 0.6e1 * t277 * t274 + 0.6e1 * t312 * t173 + 0.3e1 * t172 * t284 + 0.4e1 / 0.3e1 * t319 * t290 - 0.11e2 / 0.3e1 * t186 * t293 + 0.30e2 * t324 * t325 + 0.24e2 * t328 * t329 * t145 + 0.6e1 * t189 * t108 * t284 + 0.14e2 / 0.3e1 * t338 * t290 - 0.22e2 / 0.3e1 * t195 * t293
  t353 = t117 ** 2
  t355 = 0.1e1 / t120 / t353
  t357 = t115 * t355 * t86
  t358 = t150 * t152
  t367 = 0.110e3 / 0.2187e4 * t61 * t235 * t121 - 0.160e3 / 0.531441e6 * t153 * t241 * t205 * t68 + 0.16e2 / 0.59049e5 * t357 * t358 * t241 * t258 - 0.88e2 / 0.2187e4 * t207 * t208 * t234 * t68 - t238 + t245 - t261
  t369 = -t182 * t123 * t343 - 0.6e1 * t267 * t177 * t198 - 0.2e1 * t182 * t213 * t198 + t112 * t367 + 0.6e1 * t164 * t271 + 0.3e1 * t164 * t297 + 0.6e1 * t262 * t264 + 0.2e1 * t302 * t304 + t238 - t245 + t261
  t373 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t374 = t373 * f.p.zeta_threshold
  t376 = f.my_piecewise3(t20, t374, t21 * t19)
  t378 = 0.1e1 / t135 / t25
  t379 = t376 * t378
  t383 = t376 * t223
  t387 = t376 * t136
  t391 = t376 * t54
  t392 = t367 * t198
  t395 = t213 * t343
  t403 = t154 * r0
  t405 = 0.1e1 / t64 / t403
  t406 = s0 * t405
  t408 = -0.440e3 / 0.27e2 * tau0 * t234 + 0.154e3 / 0.27e2 * t406
  t409 = t108 * t408
  t412 = t99 * t108
  t413 = t288 * params.eta
  t414 = t413 * t248
  t416 = 0.1e1 / t250 / t142
  t417 = t414 * t416
  t420 = params.b * t99
  t421 = t274 * t169
  t434 = t324 * t194
  t435 = t274 * params.eta
  t439 = t284 * params.eta
  t440 = t439 * t145
  t443 = t189 * t337
  t444 = t169 * t288
  t445 = t152 * t241
  t450 = 0.1e1 / t63 / t250
  t451 = t289 * t450
  t454 = t89 * t405
  t460 = t84 * t185
  t461 = t460 * t274
  t464 = t287 * t284
  t467 = t85 * t318
  t468 = t467 * t169
  t476 = 0.1e1 / t336 / t92
  t477 = t105 * t476
  t480 = 0.18e2 * t277 * t169 * t284 + 0.6e1 * t189 * t409 + 0.20e2 / 0.9e1 * t412 * t417 + 0.120e3 * t420 * t108 * t421 + 0.90e2 * t324 * t190 * t284 + 0.6e1 * t421 * t101 + 0.3e1 * t172 * t408 - 0.33e2 * t312 * t293 + 0.180e3 * t434 * t435 * t145 + 0.36e2 * t328 * t440 + 0.84e2 * t443 * t444 * t445 - 0.154e3 / 0.3e1 * t338 * t451 + 0.308e3 / 0.9e1 * t195 * t454 - 0.132e3 * t328 * t329 * t235 + 0.18e2 * t461 * t173 + 0.9e1 * t464 * t173 + 0.12e2 * t468 * t290 - 0.44e2 / 0.3e1 * t319 * t451 + 0.154e3 / 0.9e1 * t186 * t454 + 0.112e3 / 0.9e1 * t477 * t417
  t481 = t123 * t480
  t486 = 0.760e3 / 0.4782969e7 * t249 * t416 * t255 * t258
  t487 = t96 * t181
  t503 = t180 ** 2
  t504 = 0.1e1 / t503
  t505 = t98 * t504
  t506 = t303 * t198
  t507 = t123 * t506
  t513 = 0.18e2 * t262 * t177 * t296 - 0.9e1 * t267 * t177 * t343 - 0.18e2 * t487 * t264 * t198 - 0.18e2 * t267 * t271 * t198 - 0.9e1 * t267 * t297 * t198 + 0.6e1 * t302 * t199 * t343 - 0.3e1 * t182 * t392 - 0.3e1 * t182 * t395 - t182 * t481 - 0.6e1 * t505 * t507 - t486
  t527 = 0.1e1 / t120 / t353 / t117
  t529 = t115 * t527 * t247
  t530 = t248 * t416
  t532 = 0.1e1 / t257 / params.kappa
  t546 = 0.1540e4 / 0.6561e4 * t61 * t406 * t76
  t550 = 0.6820e4 / 0.1594323e7 * t153 * t450 * t159 * t68
  t551 = t152 ** 2
  t552 = t247 * t551
  t561 = 0.1e1 / t75 / t253 / t72 * t532 * t61
  t563 = 0.1120e4 / 0.3486784401e10 * t552 / t64 / t250 / t403 * t561
  t564 = -0.1540e4 / 0.6561e4 * t61 * t406 * t121 + 0.1760e4 / 0.531441e6 * t153 * t450 * t205 * t68 - 0.320e3 / 0.4782969e7 * t249 * t416 * t355 * t258 + 0.896e3 / 0.14348907e8 * t529 * t530 * t532 - 0.176e3 / 0.59049e5 * t357 * t358 * t450 * t258 + 0.1232e4 / 0.6561e4 * t207 * t208 * t405 * t68 + t546 - t550 + t486 - t563
  t566 = t263 * t176
  t567 = t566 * t111
  t570 = t213 * t263
  t576 = t213 * t296
  t579 = t169 * t94
  t582 = t274 * t101
  t585 = t460 * t169
  t588 = t277 * t284
  t601 = -0.6e1 * t579 * t284 - 0.4e1 * t582 * t173 - 0.4e1 * t585 * t290 - 0.4e1 * t588 * t173 + 0.44e2 / 0.3e1 * t278 * t293 - 0.2e1 * t165 * t408 - 0.8e1 / 0.9e1 * t467 * t417 + 0.22e2 / 0.3e1 * t287 * t451 - 0.308e3 / 0.27e2 * t172 * t454
  t602 = t123 * t601
  t608 = t97 * t301
  t612 = 0.9e1 * t164 * t367 * t176 + 0.18e2 * t608 * t177 * t303 + 0.6e1 * t302 * t213 * t303 + t112 * t564 + 0.6e1 * t567 * t123 + 0.9e1 * t164 * t576 + 0.3e1 * t164 * t602 + 0.18e2 * t262 * t570 - t546 + t550 + t563
  t613 = t513 + t612
  t618 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t125 - 0.3e1 / 0.8e1 * t5 * t137 * t125 - 0.9e1 / 0.8e1 * t5 * t141 * t215 + t5 * t224 * t125 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t228 * t215 - 0.9e1 / 0.8e1 * t5 * t232 * t369 - 0.5e1 / 0.36e2 * t5 * t379 * t125 + t5 * t383 * t215 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t387 * t369 - 0.3e1 / 0.8e1 * t5 * t391 * t613)
  t620 = r1 <= f.p.dens_threshold
  t621 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t622 = 0.1e1 + t621
  t623 = t622 <= f.p.zeta_threshold
  t624 = t622 ** (0.1e1 / 0.3e1)
  t625 = t624 ** 2
  t627 = 0.1e1 / t625 / t622
  t629 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t630 = t629 ** 2
  t634 = 0.1e1 / t625
  t635 = t634 * t629
  t637 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t641 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t645 = f.my_piecewise3(t623, 0, -0.8e1 / 0.27e2 * t627 * t630 * t629 + 0.4e1 / 0.3e1 * t635 * t637 + 0.4e1 / 0.3e1 * t624 * t641)
  t647 = r1 ** 2
  t648 = r1 ** (0.1e1 / 0.3e1)
  t649 = t648 ** 2
  t651 = 0.1e1 / t649 / t647
  t652 = s2 * t651
  t657 = (0.1e1 + 0.5e1 / 0.972e3 * t61 * t652 * t68) ** (0.1e1 / 0.5e1)
  t658 = t657 ** 2
  t659 = t658 ** 2
  t663 = 0.5e1 / 0.972e3 * t61 * t652 / t659
  t668 = tau1 / t649 / r1 - t652 / 0.8e1
  t669 = t668 ** 2
  t673 = t88 + params.eta * s2 * t651 / 0.8e1
  t674 = t673 ** 2
  t677 = 0.1e1 - t669 / t674
  t678 = t677 ** 2
  t684 = t669 ** 2
  t687 = t674 ** 2
  t696 = 0.5e1 / 0.972e3 * t61 * t652 + params.c
  t699 = (t696 * t68 + 0.1e1) ** (0.1e1 / 0.5e1)
  t700 = t699 ** 2
  t701 = t700 ** 2
  t706 = 0.1e1 + t663 + t678 * t677 / (0.1e1 + t669 * t668 / t674 / t673 + params.b * t684 * t669 / t687 / t674) * (t696 / t701 - t663)
  t715 = f.my_piecewise3(t623, 0, 0.4e1 / 0.9e1 * t634 * t630 + 0.4e1 / 0.3e1 * t624 * t637)
  t722 = f.my_piecewise3(t623, 0, 0.4e1 / 0.3e1 * t624 * t629)
  t728 = f.my_piecewise3(t623, t374, t624 * t622)
  t734 = f.my_piecewise3(t620, 0, -0.3e1 / 0.8e1 * t5 * t645 * t54 * t706 - 0.3e1 / 0.8e1 * t5 * t715 * t136 * t706 + t5 * t722 * t223 * t706 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t728 * t378 * t706)
  t754 = 0.1e1 / t64 / t155
  t755 = s0 * t754
  t761 = 0.1e1 / t63 / t250 / r0
  t767 = 0.1e1 / t250 / t154
  t774 = 0.1e1 / t64 / t250 / t155
  t775 = t552 * t774
  t780 = t353 ** 2
  t785 = t257 ** 2
  t786 = 0.1e1 / t785
  t805 = 0.26180e5 / 0.19683e5 * t61 * t755 * t76
  t809 = 0.60940e5 / 0.1594323e7 * t153 * t761 * t159 * t68
  t813 = 0.102520e6 / 0.43046721e8 * t249 * t767 * t255 * t258
  t815 = 0.109760e6 / 0.10460353203e11 * t775 * t561
  t818 = t250 ** 2
  t823 = t253 ** 2
  t829 = 0.42560e5 / 0.2541865828329e13 * t247 * t551 * s0 / t63 / t818 / r0 / t75 / t823 * t786 * t151
  t830 = 0.26180e5 / 0.19683e5 * t61 * t755 * t121 - 0.156640e6 / 0.4782969e7 * t153 * t761 * t205 * t68 + 0.7040e4 / 0.4782969e7 * t249 * t767 * t355 * t258 - 0.35840e5 / 0.10460353203e11 * t775 * t527 * t532 * t61 + 0.34048e5 / 0.10460353203e11 * t115 / t120 / t780 * t552 * t774 * t786 * t61 - 0.19712e5 / 0.14348907e8 * t529 * t248 * t767 * t532 + 0.15664e5 / 0.531441e6 * t357 * t358 * t761 * t258 - 0.20944e5 / 0.19683e5 * t207 * t208 * t754 * t68 - t805 + t809 - t813 + t815 - t829
  t883 = -0.72e2 * t97 * t504 * t507 * t176 + 0.72e2 * t96 * t301 * t264 * t303 - 0.36e2 * t267 * t392 * t176 - 0.36e2 * t267 * t395 * t176 - 0.36e2 * t267 * t576 * t198 - 0.72e2 * t487 * t570 * t198 - 0.36e2 * t487 * t264 * t343 - 0.18e2 * t267 * t297 * t343 + 0.72e2 * t608 * t271 * t303 - 0.36e2 * t505 * t304 * t343 + t813
  t891 = 0.6160e4 / 0.81e2 * tau0 * t405 - 0.2618e4 / 0.81e2 * t755
  t896 = t284 ** 2
  t903 = t288 ** 2
  t905 = t903 * t551 * t774
  t914 = t414 * t767
  t917 = t289 * t761
  t920 = t89 * t754
  t955 = 0.3e1 * t172 * t891 + 0.36e2 * t582 * t284 + 0.18e2 * t277 * t896 + 0.120e3 * t324 * t409 * t169 + 0.40e2 / 0.9e1 * t99 * t194 * t905 + 0.720e3 * t420 * t325 * t284 + 0.24e2 * t421 * t185 * t173 - 0.440e3 / 0.9e1 * t412 * t914 + 0.3916e4 / 0.27e2 * t319 * t917 - 0.2618e4 / 0.27e2 * t186 * t920 + 0.840e3 * t324 * t337 * t274 * t288 * t445 + 0.168e3 * t443 * t284 * t288 * t445 + 0.896e3 / 0.3e1 * t189 * t476 * t169 * t413 * t530 + 0.2464e4 / 0.3e1 * t328 * t89 * t405 * t169 + 0.72e2 * t585 * t440 + 0.48e2 * t328 * t408 * params.eta * t145 + 0.960e3 * t420 * t194 * t421 * params.eta * t145 - 0.1320e4 * t434 * t435 * t235
  t964 = t274 ** 2
  t989 = t85 * t108
  t1003 = t84 * t318
  t1015 = -0.264e3 * t328 * t439 * t235 - 0.1232e4 * t443 * t444 * t152 * t450 + 0.360e3 * params.b * t85 * t108 * t964 + 0.90e2 * t324 * t108 * t896 + 0.24e2 * t277 * t169 * t408 + 0.6e1 * t189 * t108 * t891 + 0.720e3 * t324 * t194 * t169 * t440 + 0.13706e5 / 0.27e2 * t338 * t917 - 0.5236e4 / 0.27e2 * t195 * t920 - 0.132e3 * t461 * t293 + 0.616e3 / 0.3e1 * t312 * t454 + 0.80e2 / 0.3e1 * t989 * t413 * t530 * t169 + 0.12e2 * t287 * t408 * t173 - 0.66e2 * t464 * t293 - 0.176e3 * t468 * t451 - 0.2464e4 / 0.9e1 * t477 * t914 + 0.48e2 * t1003 * t274 * t290 + 0.24e2 * t467 * t284 * t290 + 0.112e3 / 0.3e1 * t105 / t336 / t93 * t905
  t1037 = t303 ** 2
  t1042 = t343 ** 2
  t1058 = t296 ** 2
  t1100 = -0.8e1 * t274 * t185 * t290 - 0.40e2 / 0.27e2 * t989 * t905 - 0.6e1 * t896 * t94 - 0.8e1 * t579 * t408 - 0.2e1 * t165 * t891 + 0.88e2 / 0.3e1 * t588 * t293 - 0.2464e4 / 0.27e2 * t278 * t454 + 0.176e3 / 0.3e1 * t585 * t451 - 0.16e2 * t169 * t101 * t284 * t173 + 0.88e2 / 0.3e1 * t582 * t293 - 0.8e1 * t460 * t284 * t290 - 0.64e2 / 0.9e1 * t1003 * t169 * t417 - 0.16e2 / 0.3e1 * t277 * t408 * t173 + 0.176e3 / 0.9e1 * t467 * t914 - 0.1958e4 / 0.27e2 * t287 * t917 + 0.5236e4 / 0.81e2 * t172 * t920
  t1120 = -0.72e2 * t487 * t123 * t176 * t198 * t296 + 0.72e2 * t608 * t123 * t176 * t343 * t198 + 0.6e1 * t302 * t123 * t1042 + 0.18e2 * t262 * t123 * t1058 + 0.3e1 * t164 * t123 * t1100 + 0.36e2 * t263 * t111 * t297 + 0.12e2 * t164 * t564 * t176 + 0.18e2 * t164 * t367 * t296 - 0.24e2 * t566 * t181 * t199 + 0.36e2 * t262 * t367 * t263 + 0.12e2 * t302 * t367 * t303
  t1126 = t19 ** 2
  t1129 = t30 ** 2
  t1135 = t41 ** 2
  t1144 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t1145 = f.my_piecewise5(t10, 0, t14, 0, t1144)
  t1149 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t1126 * t1129 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t1135 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t1145)
  t1178 = 0.1e1 / t135 / t36
  t1183 = -0.3e1 / 0.2e1 * t5 * t228 * t369 - 0.3e1 / 0.2e1 * t5 * t232 * t613 - 0.5e1 / 0.9e1 * t5 * t379 * t215 + t5 * t383 * t369 / 0.2e1 - t5 * t387 * t613 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t391 * (-0.12e2 * t267 * t481 * t176 + 0.24e2 * t262 * t177 * t601 + 0.24e2 * t302 * t395 * t198 + 0.8e1 * t302 * t481 * t198 + 0.72e2 * t262 * t271 * t296 + 0.36e2 * t608 * t297 * t303 + t112 * t830 + 0.24e2 * t567 * t213 + t805 - t809 + t883 - 0.12e2 * t267 * t602 * t198 - t815 + t829 - t182 * t123 * (t955 + t1015) - 0.24e2 * t505 * t213 * t506 - 0.4e1 * t182 * t213 * t480 + 0.12e2 * t164 * t213 * t601 - 0.4e1 * t182 * t564 * t198 - 0.6e1 * t182 * t367 * t343 + 0.24e2 * t98 / t503 / t110 * t123 * t1037 + t1120) - 0.3e1 / 0.8e1 * t5 * t1149 * t54 * t125 - 0.3e1 / 0.2e1 * t5 * t55 * t215 - 0.3e1 / 0.2e1 * t5 * t137 * t215 - 0.9e1 / 0.4e1 * t5 * t141 * t369 + t5 * t224 * t215 - t5 * t53 * t136 * t125 / 0.2e1 + t5 * t134 * t223 * t125 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t221 * t378 * t125 + 0.10e2 / 0.27e2 * t5 * t376 * t1178 * t125
  t1184 = f.my_piecewise3(t1, 0, t1183)
  t1185 = t622 ** 2
  t1188 = t630 ** 2
  t1194 = t637 ** 2
  t1200 = f.my_piecewise5(t14, 0, t10, 0, -t1144)
  t1204 = f.my_piecewise3(t623, 0, 0.40e2 / 0.81e2 / t625 / t1185 * t1188 - 0.16e2 / 0.9e1 * t627 * t630 * t637 + 0.4e1 / 0.3e1 * t634 * t1194 + 0.16e2 / 0.9e1 * t635 * t641 + 0.4e1 / 0.3e1 * t624 * t1200)
  t1226 = f.my_piecewise3(t620, 0, -0.3e1 / 0.8e1 * t5 * t1204 * t54 * t706 - t5 * t645 * t136 * t706 / 0.2e1 + t5 * t715 * t223 * t706 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t722 * t378 * t706 + 0.10e2 / 0.27e2 * t5 * t728 * t1178 * t706)
  d1111 = 0.4e1 * t618 + 0.4e1 * t734 + t6 * (t1184 + t1226)

  res = {'v4rho4': d1111}
  return res
