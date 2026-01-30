"""Generated from mgga_x_tau_hcth.mpl."""

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
  params_cx_local_raw = params.cx_local
  if isinstance(params_cx_local_raw, (str, bytes, dict)):
    params_cx_local = params_cx_local_raw
  else:
    try:
      params_cx_local_seq = list(params_cx_local_raw)
    except TypeError:
      params_cx_local = params_cx_local_raw
    else:
      params_cx_local_seq = np.asarray(params_cx_local_seq, dtype=np.float64)
      params_cx_local = np.concatenate((np.array([np.nan], dtype=np.float64), params_cx_local_seq))
  params_cx_nlocal_raw = params.cx_nlocal
  if isinstance(params_cx_nlocal_raw, (str, bytes, dict)):
    params_cx_nlocal = params_cx_nlocal_raw
  else:
    try:
      params_cx_nlocal_seq = list(params_cx_nlocal_raw)
    except TypeError:
      params_cx_nlocal = params_cx_nlocal_raw
    else:
      params_cx_nlocal_seq = np.asarray(params_cx_nlocal_seq, dtype=np.float64)
      params_cx_nlocal = np.concatenate((np.array([np.nan], dtype=np.float64), params_cx_nlocal_seq))

  hcth_coeff_a = np.array([np.nan, 0, 1, 0, -2, 0, 1], dtype=np.float64)

  hcth_gamX = 0.004

  hcth_ux = lambda x: hcth_gamX * x ** 2 / (1 + hcth_gamX * x ** 2)

  hcth_gxl = lambda x: jnp.sum(jnp.array([params_cx_local[i] * hcth_ux(x) ** (i - 1) for i in range(1, 4 + 1)]), axis=0)

  hcth_gxnl = lambda x: jnp.sum(jnp.array([params_cx_nlocal[i] * hcth_ux(x) ** (i - 1) for i in range(1, 4 + 1)]), axis=0)

  hcth_f = lambda x, u, t: hcth_gxl(x) + hcth_gxnl(x) * mgga_series_w(hcth_coeff_a, 6, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, hcth_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_cx_local_raw = params.cx_local
  if isinstance(params_cx_local_raw, (str, bytes, dict)):
    params_cx_local = params_cx_local_raw
  else:
    try:
      params_cx_local_seq = list(params_cx_local_raw)
    except TypeError:
      params_cx_local = params_cx_local_raw
    else:
      params_cx_local_seq = np.asarray(params_cx_local_seq, dtype=np.float64)
      params_cx_local = np.concatenate((np.array([np.nan], dtype=np.float64), params_cx_local_seq))
  params_cx_nlocal_raw = params.cx_nlocal
  if isinstance(params_cx_nlocal_raw, (str, bytes, dict)):
    params_cx_nlocal = params_cx_nlocal_raw
  else:
    try:
      params_cx_nlocal_seq = list(params_cx_nlocal_raw)
    except TypeError:
      params_cx_nlocal = params_cx_nlocal_raw
    else:
      params_cx_nlocal_seq = np.asarray(params_cx_nlocal_seq, dtype=np.float64)
      params_cx_nlocal = np.concatenate((np.array([np.nan], dtype=np.float64), params_cx_nlocal_seq))

  hcth_coeff_a = np.array([np.nan, 0, 1, 0, -2, 0, 1], dtype=np.float64)

  hcth_gamX = 0.004

  hcth_ux = lambda x: hcth_gamX * x ** 2 / (1 + hcth_gamX * x ** 2)

  hcth_gxl = lambda x: jnp.sum(jnp.array([params_cx_local[i] * hcth_ux(x) ** (i - 1) for i in range(1, 4 + 1)]), axis=0)

  hcth_gxnl = lambda x: jnp.sum(jnp.array([params_cx_nlocal[i] * hcth_ux(x) ** (i - 1) for i in range(1, 4 + 1)]), axis=0)

  hcth_f = lambda x, u, t: hcth_gxl(x) + hcth_gxnl(x) * mgga_series_w(hcth_coeff_a, 6, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, hcth_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_cx_local_raw = params.cx_local
  if isinstance(params_cx_local_raw, (str, bytes, dict)):
    params_cx_local = params_cx_local_raw
  else:
    try:
      params_cx_local_seq = list(params_cx_local_raw)
    except TypeError:
      params_cx_local = params_cx_local_raw
    else:
      params_cx_local_seq = np.asarray(params_cx_local_seq, dtype=np.float64)
      params_cx_local = np.concatenate((np.array([np.nan], dtype=np.float64), params_cx_local_seq))
  params_cx_nlocal_raw = params.cx_nlocal
  if isinstance(params_cx_nlocal_raw, (str, bytes, dict)):
    params_cx_nlocal = params_cx_nlocal_raw
  else:
    try:
      params_cx_nlocal_seq = list(params_cx_nlocal_raw)
    except TypeError:
      params_cx_nlocal = params_cx_nlocal_raw
    else:
      params_cx_nlocal_seq = np.asarray(params_cx_nlocal_seq, dtype=np.float64)
      params_cx_nlocal = np.concatenate((np.array([np.nan], dtype=np.float64), params_cx_nlocal_seq))

  hcth_coeff_a = np.array([np.nan, 0, 1, 0, -2, 0, 1], dtype=np.float64)

  hcth_gamX = 0.004

  hcth_ux = lambda x: hcth_gamX * x ** 2 / (1 + hcth_gamX * x ** 2)

  hcth_gxl = lambda x: jnp.sum(jnp.array([params_cx_local[i] * hcth_ux(x) ** (i - 1) for i in range(1, 4 + 1)]), axis=0)

  hcth_gxnl = lambda x: jnp.sum(jnp.array([params_cx_nlocal[i] * hcth_ux(x) ** (i - 1) for i in range(1, 4 + 1)]), axis=0)

  hcth_f = lambda x, u, t: hcth_gxl(x) + hcth_gxnl(x) * mgga_series_w(hcth_coeff_a, 6, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, hcth_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t28 = params.cx_local[0]
  t29 = params.cx_local[1]
  t30 = t29 * s0
  t31 = r0 ** 2
  t32 = r0 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t35 = 0.1e1 / t33 / t31
  t38 = 0.1e1 + 0.4e-2 * s0 * t35
  t39 = 0.1e1 / t38
  t40 = t35 * t39
  t43 = params.cx_local[2]
  t44 = s0 ** 2
  t45 = t43 * t44
  t46 = t31 ** 2
  t50 = t38 ** 2
  t51 = 0.1e1 / t50
  t52 = 0.1e1 / t32 / t46 / r0 * t51
  t55 = params.cx_local[3]
  t56 = t44 * s0
  t57 = t55 * t56
  t58 = t46 ** 2
  t61 = 0.1e1 / t50 / t38
  t62 = 0.1e1 / t58 * t61
  t65 = params.cx_nlocal[0]
  t66 = params.cx_nlocal[1]
  t67 = t66 * s0
  t70 = params.cx_nlocal[2]
  t71 = t70 * t44
  t74 = params.cx_nlocal[3]
  t75 = t74 * t56
  t78 = t65 + 0.4e-2 * t67 * t40 + 0.16e-4 * t71 * t52 + 0.64e-7 * t75 * t62
  t79 = 6 ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t81 = jnp.pi ** 2
  t82 = t81 ** (0.1e1 / 0.3e1)
  t83 = t82 ** 2
  t85 = 0.3e1 / 0.10e2 * t80 * t83
  t87 = 0.1e1 / t33 / r0
  t88 = tau0 * t87
  t89 = t85 - t88
  t90 = t85 + t88
  t91 = 0.1e1 / t90
  t93 = t89 ** 2
  t94 = t93 * t89
  t95 = t90 ** 2
  t97 = 0.1e1 / t95 / t90
  t100 = t93 ** 2
  t101 = t100 * t89
  t102 = t95 ** 2
  t104 = 0.1e1 / t102 / t90
  t106 = t101 * t104 + t89 * t91 - 0.2e1 * t94 * t97
  t108 = t28 + 0.4e-2 * t30 * t40 + 0.16e-4 * t45 * t52 + 0.64e-7 * t57 * t62 + t78 * t106
  t112 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t108)
  t113 = r1 <= f.p.dens_threshold
  t114 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t115 = 0.1e1 + t114
  t116 = t115 <= f.p.zeta_threshold
  t117 = t115 ** (0.1e1 / 0.3e1)
  t119 = f.my_piecewise3(t116, t22, t117 * t115)
  t120 = t119 * t26
  t121 = t29 * s2
  t122 = r1 ** 2
  t123 = r1 ** (0.1e1 / 0.3e1)
  t124 = t123 ** 2
  t126 = 0.1e1 / t124 / t122
  t129 = 0.1e1 + 0.4e-2 * s2 * t126
  t130 = 0.1e1 / t129
  t131 = t126 * t130
  t134 = s2 ** 2
  t135 = t43 * t134
  t136 = t122 ** 2
  t140 = t129 ** 2
  t141 = 0.1e1 / t140
  t142 = 0.1e1 / t123 / t136 / r1 * t141
  t145 = t134 * s2
  t146 = t55 * t145
  t147 = t136 ** 2
  t150 = 0.1e1 / t140 / t129
  t151 = 0.1e1 / t147 * t150
  t154 = t66 * s2
  t157 = t70 * t134
  t160 = t74 * t145
  t163 = t65 + 0.4e-2 * t154 * t131 + 0.16e-4 * t157 * t142 + 0.64e-7 * t160 * t151
  t165 = 0.1e1 / t124 / r1
  t166 = tau1 * t165
  t167 = t85 - t166
  t168 = t85 + t166
  t169 = 0.1e1 / t168
  t171 = t167 ** 2
  t172 = t171 * t167
  t173 = t168 ** 2
  t175 = 0.1e1 / t173 / t168
  t178 = t171 ** 2
  t179 = t178 * t167
  t180 = t173 ** 2
  t182 = 0.1e1 / t180 / t168
  t184 = t167 * t169 - 0.2e1 * t172 * t175 + t179 * t182
  t186 = t28 + 0.4e-2 * t121 * t131 + 0.16e-4 * t135 * t142 + 0.64e-7 * t146 * t151 + t163 * t184
  t190 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t120 * t186)
  t191 = t6 ** 2
  t193 = t16 / t191
  t194 = t7 - t193
  t195 = f.my_piecewise5(t10, 0, t14, 0, t194)
  t198 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t195)
  t203 = t26 ** 2
  t204 = 0.1e1 / t203
  t208 = t5 * t25 * t204 * t108 / 0.8e1
  t209 = t31 * r0
  t212 = 0.1e1 / t33 / t209 * t39
  t219 = 0.1e1 / t32 / t46 / t31 * t51
  t227 = 0.1e1 / t58 / r0 * t61
  t232 = t44 ** 2
  t237 = t50 ** 2
  t238 = 0.1e1 / t237
  t239 = 0.1e1 / t33 / t58 / t209 * t238
  t259 = tau0 * t35
  t263 = t89 / t95
  t266 = t93 * t97
  t270 = t94 / t102
  t273 = t100 * t104
  t278 = t101 / t102 / t95
  t288 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t198 * t26 * t108 - t208 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.10666666666666666666666666666666666666666666666667e-1 * t30 * t212 + 0.42666666666666666666666666666666666666666666666668e-4 * t29 * t44 * t219 - 0.85333333333333333333333333333333333333333333333333e-4 * t45 * t219 + 0.34133333333333333333333333333333333333333333333334e-6 * t43 * t56 * t227 - 0.512e-6 * t57 * t227 + 0.20480000000000000000000000000000000000000000000001e-8 * t55 * t232 * t239 + (-0.10666666666666666666666666666666666666666666666667e-1 * t67 * t212 + 0.42666666666666666666666666666666666666666666666668e-4 * t66 * t44 * t219 - 0.85333333333333333333333333333333333333333333333333e-4 * t71 * t219 + 0.34133333333333333333333333333333333333333333333334e-6 * t70 * t56 * t227 - 0.512e-6 * t75 * t227 + 0.20480000000000000000000000000000000000000000000001e-8 * t74 * t232 * t239) * t106 + t78 * (0.5e1 / 0.3e1 * t259 * t91 + 0.5e1 / 0.3e1 * t263 * t259 - 0.10e2 * t266 * t259 - 0.10e2 * t270 * t259 + 0.25e2 / 0.3e1 * t273 * t259 + 0.25e2 / 0.3e1 * t278 * t259)))
  t290 = f.my_piecewise5(t14, 0, t10, 0, -t194)
  t293 = f.my_piecewise3(t116, 0, 0.4e1 / 0.3e1 * t117 * t290)
  t301 = t5 * t119 * t204 * t186 / 0.8e1
  t303 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t293 * t26 * t186 - t301)
  vrho_0_ = t112 + t190 + t6 * (t288 + t303)
  t306 = -t7 - t193
  t307 = f.my_piecewise5(t10, 0, t14, 0, t306)
  t310 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t307)
  t316 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t310 * t26 * t108 - t208)
  t318 = f.my_piecewise5(t14, 0, t10, 0, -t306)
  t321 = f.my_piecewise3(t116, 0, 0.4e1 / 0.3e1 * t117 * t318)
  t326 = t122 * r1
  t329 = 0.1e1 / t124 / t326 * t130
  t336 = 0.1e1 / t123 / t136 / t122 * t141
  t344 = 0.1e1 / t147 / r1 * t150
  t349 = t134 ** 2
  t354 = t140 ** 2
  t355 = 0.1e1 / t354
  t356 = 0.1e1 / t124 / t147 / t326 * t355
  t376 = tau1 * t126
  t380 = t167 / t173
  t383 = t171 * t175
  t387 = t172 / t180
  t390 = t178 * t182
  t395 = t179 / t180 / t173
  t405 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t321 * t26 * t186 - t301 - 0.3e1 / 0.8e1 * t5 * t120 * (-0.10666666666666666666666666666666666666666666666667e-1 * t121 * t329 + 0.42666666666666666666666666666666666666666666666668e-4 * t29 * t134 * t336 - 0.85333333333333333333333333333333333333333333333333e-4 * t135 * t336 + 0.34133333333333333333333333333333333333333333333334e-6 * t43 * t145 * t344 - 0.512e-6 * t146 * t344 + 0.20480000000000000000000000000000000000000000000001e-8 * t55 * t349 * t356 + (-0.10666666666666666666666666666666666666666666666667e-1 * t154 * t329 + 0.42666666666666666666666666666666666666666666666668e-4 * t66 * t134 * t336 - 0.85333333333333333333333333333333333333333333333333e-4 * t157 * t336 + 0.34133333333333333333333333333333333333333333333334e-6 * t70 * t145 * t344 - 0.512e-6 * t160 * t344 + 0.20480000000000000000000000000000000000000000000001e-8 * t74 * t349 * t356) * t184 + t163 * (0.5e1 / 0.3e1 * t376 * t169 + 0.5e1 / 0.3e1 * t380 * t376 - 0.10e2 * t383 * t376 - 0.10e2 * t387 * t376 + 0.25e2 / 0.3e1 * t390 * t376 + 0.25e2 / 0.3e1 * t395 * t376)))
  vrho_1_ = t112 + t190 + t6 * (t316 + t405)
  t424 = 0.1e1 / t33 / t58 / t31 * t238
  t448 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.4e-2 * t29 * t35 * t39 - 0.16e-4 * t30 * t52 + 0.32e-4 * t43 * s0 * t52 - 0.128e-6 * t45 * t62 + 0.192e-6 * t55 * t44 * t62 - 0.768e-9 * t57 * t424 + (0.4e-2 * t66 * t35 * t39 - 0.16e-4 * t67 * t52 + 0.32e-4 * t70 * s0 * t52 - 0.128e-6 * t71 * t62 + 0.192e-6 * t74 * t44 * t62 - 0.768e-9 * t75 * t424) * t106))
  vsigma_0_ = t6 * t448
  vsigma_1_ = 0.0e0
  t465 = 0.1e1 / t124 / t147 / t122 * t355
  t489 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t120 * (0.4e-2 * t29 * t126 * t130 - 0.16e-4 * t121 * t142 + 0.32e-4 * t43 * s2 * t142 - 0.128e-6 * t135 * t151 + 0.192e-6 * t55 * t134 * t151 - 0.768e-9 * t146 * t465 + (0.4e-2 * t66 * t126 * t130 - 0.16e-4 * t154 * t142 + 0.32e-4 * t70 * s2 * t142 - 0.128e-6 * t157 * t151 + 0.192e-6 * t74 * t134 * t151 - 0.768e-9 * t160 * t465) * t184))
  vsigma_2_ = t6 * t489
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t506 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t78 * (-t263 * t87 + 0.6e1 * t266 * t87 + 0.6e1 * t270 * t87 - 0.5e1 * t273 * t87 - 0.5e1 * t278 * t87 - t87 * t91))
  vtau_0_ = t6 * t506
  t523 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t119 * t26 * t163 * (-t165 * t169 - t380 * t165 + 0.6e1 * t383 * t165 + 0.6e1 * t387 * t165 - 0.5e1 * t390 * t165 - 0.5e1 * t395 * t165))
  vtau_1_ = t6 * t523
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
  params_cx_local_raw = params.cx_local
  if isinstance(params_cx_local_raw, (str, bytes, dict)):
    params_cx_local = params_cx_local_raw
  else:
    try:
      params_cx_local_seq = list(params_cx_local_raw)
    except TypeError:
      params_cx_local = params_cx_local_raw
    else:
      params_cx_local_seq = np.asarray(params_cx_local_seq, dtype=np.float64)
      params_cx_local = np.concatenate((np.array([np.nan], dtype=np.float64), params_cx_local_seq))
  params_cx_nlocal_raw = params.cx_nlocal
  if isinstance(params_cx_nlocal_raw, (str, bytes, dict)):
    params_cx_nlocal = params_cx_nlocal_raw
  else:
    try:
      params_cx_nlocal_seq = list(params_cx_nlocal_raw)
    except TypeError:
      params_cx_nlocal = params_cx_nlocal_raw
    else:
      params_cx_nlocal_seq = np.asarray(params_cx_nlocal_seq, dtype=np.float64)
      params_cx_nlocal = np.concatenate((np.array([np.nan], dtype=np.float64), params_cx_nlocal_seq))

  hcth_coeff_a = np.array([np.nan, 0, 1, 0, -2, 0, 1], dtype=np.float64)

  hcth_gamX = 0.004

  hcth_ux = lambda x: hcth_gamX * x ** 2 / (1 + hcth_gamX * x ** 2)

  hcth_gxl = lambda x: jnp.sum(jnp.array([params_cx_local[i] * hcth_ux(x) ** (i - 1) for i in range(1, 4 + 1)]), axis=0)

  hcth_gxnl = lambda x: jnp.sum(jnp.array([params_cx_nlocal[i] * hcth_ux(x) ** (i - 1) for i in range(1, 4 + 1)]), axis=0)

  hcth_f = lambda x, u, t: hcth_gxl(x) + hcth_gxnl(x) * mgga_series_w(hcth_coeff_a, 6, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, hcth_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t21 = params.cx_local[1]
  t22 = t21 * s0
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = r0 ** 2
  t26 = t18 ** 2
  t28 = 0.1e1 / t26 / t25
  t33 = 0.1e1 + 0.4e-2 * s0 * t24 * t28
  t34 = 0.1e1 / t33
  t35 = t24 * t28 * t34
  t38 = params.cx_local[2]
  t39 = s0 ** 2
  t40 = t38 * t39
  t41 = t25 ** 2
  t46 = t33 ** 2
  t47 = 0.1e1 / t46
  t48 = t23 / t18 / t41 / r0 * t47
  t51 = params.cx_local[3]
  t52 = t39 * s0
  t53 = t51 * t52
  t54 = t41 ** 2
  t57 = 0.1e1 / t46 / t33
  t58 = 0.1e1 / t54 * t57
  t62 = params.cx_nlocal[1]
  t63 = t62 * s0
  t66 = params.cx_nlocal[2]
  t67 = t66 * t39
  t70 = params.cx_nlocal[3]
  t71 = t70 * t52
  t74 = params.cx_nlocal[0] + 0.4e-2 * t63 * t35 + 0.32e-4 * t67 * t48 + 0.256e-6 * t71 * t58
  t75 = 6 ** (0.1e1 / 0.3e1)
  t76 = t75 ** 2
  t77 = jnp.pi ** 2
  t78 = t77 ** (0.1e1 / 0.3e1)
  t79 = t78 ** 2
  t81 = 0.3e1 / 0.10e2 * t76 * t79
  t82 = tau0 * t24
  t84 = 0.1e1 / t26 / r0
  t85 = t82 * t84
  t86 = t81 - t85
  t87 = t81 + t85
  t88 = 0.1e1 / t87
  t90 = t86 ** 2
  t91 = t90 * t86
  t92 = t87 ** 2
  t94 = 0.1e1 / t92 / t87
  t97 = t90 ** 2
  t98 = t97 * t86
  t99 = t92 ** 2
  t101 = 0.1e1 / t99 / t87
  t103 = t98 * t101 + t86 * t88 - 0.2e1 * t91 * t94
  t105 = params.cx_local[0] + 0.4e-2 * t22 * t35 + 0.32e-4 * t40 * t48 + 0.256e-6 * t53 * t58 + t74 * t103
  t109 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t105)
  t115 = t25 * r0
  t119 = t24 / t26 / t115 * t34
  t127 = t23 / t18 / t41 / t25 * t47
  t135 = 0.1e1 / t54 / r0 * t57
  t140 = t39 ** 2
  t145 = t46 ** 2
  t146 = 0.1e1 / t145
  t148 = 0.1e1 / t26 / t54 / t115 * t146 * t24
  t172 = t86 / t92
  t173 = t82 * t28
  t176 = t90 * t94
  t180 = t91 / t99
  t183 = t97 * t101
  t188 = t98 / t99 / t92
  t198 = f.my_piecewise3(t2, 0, -t6 * t17 / t26 * t105 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.10666666666666666666666666666666666666666666666667e-1 * t22 * t119 + 0.85333333333333333333333333333333333333333333333336e-4 * t21 * t39 * t127 - 0.17066666666666666666666666666666666666666666666667e-3 * t40 * t127 + 0.13653333333333333333333333333333333333333333333334e-5 * t38 * t52 * t135 - 0.2048e-5 * t53 * t135 + 0.81920000000000000000000000000000000000000000000003e-8 * t51 * t140 * t148 + (-0.10666666666666666666666666666666666666666666666667e-1 * t63 * t119 + 0.85333333333333333333333333333333333333333333333336e-4 * t62 * t39 * t127 - 0.17066666666666666666666666666666666666666666666667e-3 * t67 * t127 + 0.13653333333333333333333333333333333333333333333334e-5 * t66 * t52 * t135 - 0.2048e-5 * t71 * t135 + 0.81920000000000000000000000000000000000000000000003e-8 * t70 * t140 * t148) * t103 + t74 * (0.5e1 / 0.3e1 * t82 * t28 * t88 + 0.5e1 / 0.3e1 * t172 * t173 - 0.10e2 * t176 * t173 - 0.10e2 * t180 * t173 + 0.25e2 / 0.3e1 * t183 * t173 + 0.25e2 / 0.3e1 * t188 * t173)))
  vrho_0_ = 0.2e1 * r0 * t198 + 0.2e1 * t109
  t202 = t28 * t34
  t219 = 0.1e1 / t26 / t54 / t25 * t146 * t24
  t243 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.4e-2 * t21 * t24 * t202 - 0.32e-4 * t22 * t48 + 0.64e-4 * t38 * s0 * t48 - 0.512e-6 * t40 * t58 + 0.768e-6 * t51 * t39 * t58 - 0.3072e-8 * t53 * t219 + (0.4e-2 * t62 * t24 * t202 - 0.32e-4 * t63 * t48 + 0.64e-4 * t66 * s0 * t48 - 0.512e-6 * t67 * t58 + 0.768e-6 * t70 * t39 * t58 - 0.3072e-8 * t71 * t219) * t103))
  vsigma_0_ = 0.2e1 * r0 * t243
  vlapl_0_ = 0.0e0
  t247 = t24 * t84
  t262 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t74 * (-t172 * t247 + 0.6e1 * t176 * t247 + 0.6e1 * t180 * t247 - 0.5e1 * t183 * t247 - 0.5e1 * t188 * t247 - t247 * t88))
  vtau_0_ = 0.2e1 * r0 * t262
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
  t23 = params.cx_local[1]
  t24 = t23 * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = r0 ** 2
  t29 = 0.1e1 / t19 / t27
  t34 = 0.1e1 + 0.4e-2 * s0 * t26 * t29
  t35 = 0.1e1 / t34
  t36 = t26 * t29 * t35
  t39 = params.cx_local[2]
  t40 = s0 ** 2
  t41 = t39 * t40
  t42 = t27 ** 2
  t45 = 0.1e1 / t18 / t42 / r0
  t47 = t34 ** 2
  t48 = 0.1e1 / t47
  t49 = t25 * t45 * t48
  t52 = params.cx_local[3]
  t53 = t40 * s0
  t54 = t52 * t53
  t55 = t42 ** 2
  t58 = 0.1e1 / t47 / t34
  t59 = 0.1e1 / t55 * t58
  t63 = params.cx_nlocal[1]
  t64 = t63 * s0
  t67 = params.cx_nlocal[2]
  t68 = t67 * t40
  t71 = params.cx_nlocal[3]
  t72 = t71 * t53
  t75 = params.cx_nlocal[0] + 0.4e-2 * t64 * t36 + 0.32e-4 * t68 * t49 + 0.256e-6 * t72 * t59
  t76 = 6 ** (0.1e1 / 0.3e1)
  t77 = t76 ** 2
  t78 = jnp.pi ** 2
  t79 = t78 ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t82 = 0.3e1 / 0.10e2 * t77 * t80
  t83 = tau0 * t26
  t85 = 0.1e1 / t19 / r0
  t86 = t83 * t85
  t87 = t82 - t86
  t88 = t82 + t86
  t89 = 0.1e1 / t88
  t91 = t87 ** 2
  t92 = t91 * t87
  t93 = t88 ** 2
  t94 = t93 * t88
  t95 = 0.1e1 / t94
  t98 = t91 ** 2
  t99 = t98 * t87
  t100 = t93 ** 2
  t102 = 0.1e1 / t100 / t88
  t104 = t99 * t102 + t87 * t89 - 0.2e1 * t92 * t95
  t106 = params.cx_local[0] + 0.4e-2 * t24 * t36 + 0.32e-4 * t41 * t49 + 0.256e-6 * t54 * t59 + t75 * t104
  t110 = t17 * t18
  t111 = t27 * r0
  t113 = 0.1e1 / t19 / t111
  t115 = t26 * t113 * t35
  t118 = t23 * t40
  t123 = t25 / t18 / t42 / t27 * t48
  t128 = t39 * t53
  t131 = 0.1e1 / t55 / r0 * t58
  t136 = t40 ** 2
  t137 = t52 * t136
  t141 = t47 ** 2
  t142 = 0.1e1 / t141
  t144 = 0.1e1 / t19 / t55 / t111 * t142 * t26
  t149 = t63 * t40
  t154 = t67 * t53
  t159 = t71 * t136
  t162 = -0.10666666666666666666666666666666666666666666666667e-1 * t64 * t115 + 0.85333333333333333333333333333333333333333333333336e-4 * t149 * t123 - 0.17066666666666666666666666666666666666666666666667e-3 * t68 * t123 + 0.13653333333333333333333333333333333333333333333334e-5 * t154 * t131 - 0.2048e-5 * t72 * t131 + 0.81920000000000000000000000000000000000000000000003e-8 * t159 * t144
  t167 = 0.1e1 / t93
  t168 = t87 * t167
  t169 = t83 * t29
  t172 = t91 * t95
  t175 = 0.1e1 / t100
  t176 = t92 * t175
  t179 = t98 * t102
  t183 = 0.1e1 / t100 / t93
  t184 = t99 * t183
  t187 = 0.5e1 / 0.3e1 * t83 * t29 * t89 + 0.5e1 / 0.3e1 * t168 * t169 - 0.10e2 * t172 * t169 - 0.10e2 * t176 * t169 + 0.25e2 / 0.3e1 * t179 * t169 + 0.25e2 / 0.3e1 * t184 * t169
  t189 = -0.10666666666666666666666666666666666666666666666667e-1 * t24 * t115 + 0.85333333333333333333333333333333333333333333333336e-4 * t118 * t123 - 0.17066666666666666666666666666666666666666666666667e-3 * t41 * t123 + 0.13653333333333333333333333333333333333333333333334e-5 * t128 * t131 - 0.2048e-5 * t54 * t131 + 0.81920000000000000000000000000000000000000000000003e-8 * t137 * t144 + t162 * t104 + t75 * t187
  t194 = f.my_piecewise3(t2, 0, -t6 * t21 * t106 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t110 * t189)
  t206 = t26 / t19 / t42 * t35
  t209 = t42 * t111
  t213 = t25 / t18 / t209 * t48
  t219 = 0.1e1 / t55 / t27 * t58
  t231 = 0.1e1 / t19 / t55 / t42 * t142 * t26
  t238 = t136 * s0
  t246 = 0.1e1 / t18 / t55 / t209 / t141 / t34 * t25
  t277 = tau0 ** 2
  t278 = t277 * t25
  t283 = t278 * t45
  t286 = t83 * t113
  t311 = -0.40e2 / 0.9e1 * t83 * t113 * t89 + 0.100e3 / 0.9e1 * t278 * t45 * t167 - 0.500e3 / 0.9e1 * t87 * t95 * t283 - 0.40e2 / 0.9e1 * t168 * t286 - 0.200e3 * t91 * t175 * t283 + 0.80e2 / 0.3e1 * t172 * t286 - 0.200e3 / 0.9e1 * t92 * t102 * t283 + 0.80e2 / 0.3e1 * t176 * t286 + 0.2500e4 / 0.9e1 * t98 * t183 * t283 - 0.200e3 / 0.9e1 * t179 * t286 + 0.500e3 / 0.3e1 * t99 / t100 / t94 * t283 - 0.200e3 / 0.9e1 * t184 * t286
  t313 = 0.39111111111111111111111111111111111111111111111112e-1 * t24 * t206 - 0.76800000000000000000000000000000000000000000000003e-3 * t118 * t213 + 0.36408888888888888888888888888888888888888888888891e-5 * t23 * t53 * t219 + 0.10808888888888888888888888888888888888888888888889e-2 * t41 * t213 - 0.19569777777777777777777777777777777777777777777779e-4 * t128 * t219 + 0.43690666666666666666666666666666666666666666666670e-7 * t39 * t136 * t231 + 0.18432e-4 * t54 * t219 - 0.16110933333333333333333333333333333333333333333334e-6 * t137 * t231 + 0.69905066666666666666666666666666666666666666666671e-9 * t52 * t238 * t246 + (0.39111111111111111111111111111111111111111111111112e-1 * t64 * t206 - 0.76800000000000000000000000000000000000000000000003e-3 * t149 * t213 + 0.36408888888888888888888888888888888888888888888891e-5 * t63 * t53 * t219 + 0.10808888888888888888888888888888888888888888888889e-2 * t68 * t213 - 0.19569777777777777777777777777777777777777777777779e-4 * t154 * t219 + 0.43690666666666666666666666666666666666666666666670e-7 * t67 * t136 * t231 + 0.18432e-4 * t72 * t219 - 0.16110933333333333333333333333333333333333333333334e-6 * t159 * t231 + 0.69905066666666666666666666666666666666666666666671e-9 * t71 * t238 * t246) * t104 + 0.2e1 * t162 * t187 + t75 * t311
  t318 = f.my_piecewise3(t2, 0, t6 * t17 * t85 * t106 / 0.12e2 - t6 * t21 * t189 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t110 * t313)
  v2rho2_0_ = 0.2e1 * r0 * t318 + 0.4e1 * t194
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
  t24 = params.cx_local[1]
  t25 = t24 * s0
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = r0 ** 2
  t30 = 0.1e1 / t19 / t28
  t35 = 0.1e1 + 0.4e-2 * s0 * t27 * t30
  t36 = 0.1e1 / t35
  t37 = t27 * t30 * t36
  t40 = params.cx_local[2]
  t41 = s0 ** 2
  t42 = t40 * t41
  t43 = t28 ** 2
  t44 = t43 * r0
  t46 = 0.1e1 / t18 / t44
  t48 = t35 ** 2
  t49 = 0.1e1 / t48
  t50 = t26 * t46 * t49
  t53 = params.cx_local[3]
  t54 = t41 * s0
  t55 = t53 * t54
  t56 = t43 ** 2
  t57 = 0.1e1 / t56
  t59 = 0.1e1 / t48 / t35
  t60 = t57 * t59
  t64 = params.cx_nlocal[1]
  t65 = t64 * s0
  t68 = params.cx_nlocal[2]
  t69 = t68 * t41
  t72 = params.cx_nlocal[3]
  t73 = t72 * t54
  t76 = params.cx_nlocal[0] + 0.4e-2 * t65 * t37 + 0.32e-4 * t69 * t50 + 0.256e-6 * t73 * t60
  t77 = 6 ** (0.1e1 / 0.3e1)
  t78 = t77 ** 2
  t79 = jnp.pi ** 2
  t80 = t79 ** (0.1e1 / 0.3e1)
  t81 = t80 ** 2
  t83 = 0.3e1 / 0.10e2 * t78 * t81
  t84 = tau0 * t27
  t85 = t84 * t21
  t86 = t83 - t85
  t87 = t83 + t85
  t88 = 0.1e1 / t87
  t90 = t86 ** 2
  t91 = t90 * t86
  t92 = t87 ** 2
  t93 = t92 * t87
  t94 = 0.1e1 / t93
  t97 = t90 ** 2
  t98 = t97 * t86
  t99 = t92 ** 2
  t101 = 0.1e1 / t99 / t87
  t103 = t98 * t101 + t86 * t88 - 0.2e1 * t91 * t94
  t105 = params.cx_local[0] + 0.4e-2 * t25 * t37 + 0.32e-4 * t42 * t50 + 0.256e-6 * t55 * t60 + t76 * t103
  t110 = t17 / t19
  t111 = t28 * r0
  t113 = 0.1e1 / t19 / t111
  t115 = t27 * t113 * t36
  t118 = t24 * t41
  t121 = 0.1e1 / t18 / t43 / t28
  t123 = t26 * t121 * t49
  t128 = t40 * t54
  t131 = 0.1e1 / t56 / r0 * t59
  t136 = t41 ** 2
  t137 = t53 * t136
  t138 = t56 * t111
  t141 = t48 ** 2
  t142 = 0.1e1 / t141
  t144 = 0.1e1 / t19 / t138 * t142 * t27
  t149 = t64 * t41
  t154 = t68 * t54
  t159 = t72 * t136
  t162 = -0.10666666666666666666666666666666666666666666666667e-1 * t65 * t115 + 0.85333333333333333333333333333333333333333333333336e-4 * t149 * t123 - 0.17066666666666666666666666666666666666666666666667e-3 * t69 * t123 + 0.13653333333333333333333333333333333333333333333334e-5 * t154 * t131 - 0.2048e-5 * t73 * t131 + 0.81920000000000000000000000000000000000000000000003e-8 * t159 * t144
  t167 = 0.1e1 / t92
  t168 = t86 * t167
  t169 = t84 * t30
  t172 = t90 * t94
  t175 = 0.1e1 / t99
  t176 = t91 * t175
  t179 = t97 * t101
  t183 = 0.1e1 / t99 / t92
  t184 = t98 * t183
  t187 = 0.5e1 / 0.3e1 * t84 * t30 * t88 + 0.5e1 / 0.3e1 * t168 * t169 - 0.10e2 * t172 * t169 - 0.10e2 * t176 * t169 + 0.25e2 / 0.3e1 * t179 * t169 + 0.25e2 / 0.3e1 * t184 * t169
  t189 = -0.10666666666666666666666666666666666666666666666667e-1 * t25 * t115 + 0.85333333333333333333333333333333333333333333333336e-4 * t118 * t123 - 0.17066666666666666666666666666666666666666666666667e-3 * t42 * t123 + 0.13653333333333333333333333333333333333333333333334e-5 * t128 * t131 - 0.2048e-5 * t55 * t131 + 0.81920000000000000000000000000000000000000000000003e-8 * t137 * t144 + t162 * t103 + t76 * t187
  t193 = t17 * t18
  t195 = 0.1e1 / t19 / t43
  t197 = t27 * t195 * t36
  t200 = t43 * t111
  t204 = t26 / t18 / t200 * t49
  t207 = t24 * t54
  t210 = 0.1e1 / t56 / t28 * t59
  t217 = t40 * t136
  t222 = 0.1e1 / t19 / t56 / t43 * t142 * t27
  t229 = t136 * s0
  t230 = t53 * t229
  t235 = 0.1e1 / t141 / t35
  t237 = 0.1e1 / t18 / t56 / t200 * t235 * t26
  t244 = t64 * t54
  t251 = t68 * t136
  t258 = t72 * t229
  t261 = 0.39111111111111111111111111111111111111111111111112e-1 * t65 * t197 - 0.76800000000000000000000000000000000000000000000003e-3 * t149 * t204 + 0.36408888888888888888888888888888888888888888888891e-5 * t244 * t210 + 0.10808888888888888888888888888888888888888888888889e-2 * t69 * t204 - 0.19569777777777777777777777777777777777777777777779e-4 * t154 * t210 + 0.43690666666666666666666666666666666666666666666670e-7 * t251 * t222 + 0.18432e-4 * t73 * t210 - 0.16110933333333333333333333333333333333333333333334e-6 * t159 * t222 + 0.69905066666666666666666666666666666666666666666671e-9 * t258 * t237
  t268 = tau0 ** 2
  t269 = t268 * t26
  t273 = t86 * t94
  t274 = t269 * t46
  t277 = t84 * t113
  t280 = t90 * t175
  t285 = t91 * t101
  t290 = t97 * t183
  t296 = 0.1e1 / t99 / t93
  t297 = t98 * t296
  t302 = -0.40e2 / 0.9e1 * t84 * t113 * t88 + 0.100e3 / 0.9e1 * t269 * t46 * t167 - 0.500e3 / 0.9e1 * t273 * t274 - 0.40e2 / 0.9e1 * t168 * t277 - 0.200e3 * t280 * t274 + 0.80e2 / 0.3e1 * t172 * t277 - 0.200e3 / 0.9e1 * t285 * t274 + 0.80e2 / 0.3e1 * t176 * t277 + 0.2500e4 / 0.9e1 * t290 * t274 - 0.200e3 / 0.9e1 * t179 * t277 + 0.500e3 / 0.3e1 * t297 * t274 - 0.200e3 / 0.9e1 * t184 * t277
  t304 = 0.39111111111111111111111111111111111111111111111112e-1 * t25 * t197 - 0.76800000000000000000000000000000000000000000000003e-3 * t118 * t204 + 0.36408888888888888888888888888888888888888888888891e-5 * t207 * t210 + 0.10808888888888888888888888888888888888888888888889e-2 * t42 * t204 - 0.19569777777777777777777777777777777777777777777779e-4 * t128 * t210 + 0.43690666666666666666666666666666666666666666666670e-7 * t217 * t222 + 0.18432e-4 * t55 * t210 - 0.16110933333333333333333333333333333333333333333334e-6 * t137 * t222 + 0.69905066666666666666666666666666666666666666666671e-9 * t230 * t237 + t261 * t103 + 0.2e1 * t162 * t187 + t76 * t302
  t309 = f.my_piecewise3(t2, 0, t6 * t22 * t105 / 0.12e2 - t6 * t110 * t189 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t193 * t304)
  t324 = t27 / t19 / t44 * t36
  t330 = t26 / t18 / t56 * t49
  t334 = 0.1e1 / t138 * t59
  t342 = 0.1e1 / t19 / t56 / t44 * t142 * t27
  t352 = t56 ** 2
  t356 = 0.1e1 / t18 / t352 * t235 * t26
  t365 = t136 * t41
  t371 = 0.1e1 / t352 / t111 / t141 / t48
  t401 = -0.18251851851851851851851851851851851851851851851852e0 * t65 * t324 + 0.64663703703703703703703703703703703703703703703706e-2 * t149 * t330 - 0.69176888888888888888888888888888888888888888888893e-4 * t244 * t334 + 0.11650844444444444444444444444444444444444444444445e-6 * t64 * t136 * t342 - 0.79265185185185185185185185185185185185185185185186e-2 * t69 * t330 + 0.24181570370370370370370370370370370370370370370372e-3 * t154 * t334 - 0.11796480000000000000000000000000000000000000000001e-5 * t251 * t342 + 0.37282702222222222222222222222222222222222222222226e-8 * t68 * t229 * t356 - 0.184320e-3 * t73 * t334 + 0.26305422222222222222222222222222222222222222222223e-5 * t159 * t342 - 0.24466773333333333333333333333333333333333333333335e-7 * t258 * t356 + 0.74565404444444444444444444444444444444444444444451e-10 * t72 * t365 * t371
  t407 = t84 * t195
  t410 = t269 * t121
  t434 = t268 * tau0 * t57
  t443 = t99 ** 2
  t456 = -0.880e3 / 0.9e1 * t176 * t407 - 0.20000e5 / 0.9e1 * t290 * t410 + 0.2200e4 / 0.27e2 * t179 * t407 - 0.4000e4 / 0.3e1 * t297 * t410 + 0.2200e4 / 0.27e2 * t184 * t407 + 0.4000e4 / 0.9e1 * t273 * t410 + 0.440e3 / 0.27e2 * t168 * t407 + 0.1600e4 * t280 * t410 - 0.880e3 / 0.9e1 * t172 * t407 + 0.1600e4 / 0.9e1 * t285 * t410 + 0.440e3 / 0.27e2 * t84 * t195 * t88 - 0.26000e5 / 0.9e1 * t90 * t101 * t434 + 0.10000e5 / 0.3e1 * t91 * t183 * t434 + 0.25000e5 / 0.3e1 * t97 * t296 * t434 + 0.35000e5 / 0.9e1 * t98 / t443 * t434 - 0.800e3 / 0.9e1 * t269 * t121 * t167 - 0.17000e5 / 0.9e1 * t86 * t175 * t434 - 0.1000e4 / 0.9e1 * t434 * t94
  t458 = -0.18251851851851851851851851851851851851851851851852e0 * t25 * t324 + 0.64663703703703703703703703703703703703703703703706e-2 * t118 * t330 - 0.69176888888888888888888888888888888888888888888893e-4 * t207 * t334 + 0.11650844444444444444444444444444444444444444444445e-6 * t24 * t136 * t342 - 0.79265185185185185185185185185185185185185185185186e-2 * t42 * t330 + 0.24181570370370370370370370370370370370370370370372e-3 * t128 * t334 - 0.11796480000000000000000000000000000000000000000001e-5 * t217 * t342 + 0.37282702222222222222222222222222222222222222222226e-8 * t40 * t229 * t356 - 0.184320e-3 * t55 * t334 + 0.26305422222222222222222222222222222222222222222223e-5 * t137 * t342 - 0.24466773333333333333333333333333333333333333333335e-7 * t230 * t356 + 0.74565404444444444444444444444444444444444444444451e-10 * t53 * t365 * t371 + t401 * t103 + 0.3e1 * t261 * t187 + 0.3e1 * t162 * t302 + t76 * t456
  t463 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t30 * t105 + t6 * t22 * t189 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t110 * t304 - 0.3e1 / 0.8e1 * t6 * t193 * t458)
  v3rho3_0_ = 0.2e1 * r0 * t463 + 0.6e1 * t309

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
  t25 = params.cx_local[1]
  t26 = t25 * s0
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t33 = 0.1e1 + 0.4e-2 * s0 * t28 * t22
  t34 = 0.1e1 / t33
  t35 = t28 * t22 * t34
  t38 = params.cx_local[2]
  t39 = s0 ** 2
  t40 = t38 * t39
  t41 = t18 ** 2
  t42 = t41 * r0
  t44 = 0.1e1 / t19 / t42
  t46 = t33 ** 2
  t47 = 0.1e1 / t46
  t48 = t27 * t44 * t47
  t51 = params.cx_local[3]
  t52 = t39 * s0
  t53 = t51 * t52
  t54 = t41 ** 2
  t55 = 0.1e1 / t54
  t56 = t46 * t33
  t57 = 0.1e1 / t56
  t58 = t55 * t57
  t62 = params.cx_nlocal[1]
  t63 = t62 * s0
  t66 = params.cx_nlocal[2]
  t67 = t66 * t39
  t70 = params.cx_nlocal[3]
  t71 = t70 * t52
  t74 = params.cx_nlocal[0] + 0.4e-2 * t63 * t35 + 0.32e-4 * t67 * t48 + 0.256e-6 * t71 * t58
  t75 = 6 ** (0.1e1 / 0.3e1)
  t76 = t75 ** 2
  t77 = jnp.pi ** 2
  t78 = t77 ** (0.1e1 / 0.3e1)
  t79 = t78 ** 2
  t81 = 0.3e1 / 0.10e2 * t76 * t79
  t82 = tau0 * t28
  t84 = 0.1e1 / t20 / r0
  t85 = t82 * t84
  t86 = t81 - t85
  t87 = t81 + t85
  t88 = 0.1e1 / t87
  t90 = t86 ** 2
  t91 = t90 * t86
  t92 = t87 ** 2
  t93 = t92 * t87
  t94 = 0.1e1 / t93
  t97 = t90 ** 2
  t98 = t97 * t86
  t99 = t92 ** 2
  t101 = 0.1e1 / t99 / t87
  t103 = t98 * t101 + t86 * t88 - 0.2e1 * t91 * t94
  t105 = params.cx_local[0] + 0.4e-2 * t26 * t35 + 0.32e-4 * t40 * t48 + 0.256e-6 * t53 * t58 + t74 * t103
  t109 = t17 * t84
  t110 = t18 * r0
  t112 = 0.1e1 / t20 / t110
  t114 = t28 * t112 * t34
  t117 = t25 * t39
  t118 = t41 * t18
  t120 = 0.1e1 / t19 / t118
  t122 = t27 * t120 * t47
  t127 = t38 * t52
  t128 = t54 * r0
  t129 = 0.1e1 / t128
  t130 = t129 * t57
  t135 = t39 ** 2
  t136 = t51 * t135
  t137 = t54 * t110
  t140 = t46 ** 2
  t141 = 0.1e1 / t140
  t143 = 0.1e1 / t20 / t137 * t141 * t28
  t148 = t62 * t39
  t153 = t66 * t52
  t158 = t70 * t135
  t161 = -0.10666666666666666666666666666666666666666666666667e-1 * t63 * t114 + 0.85333333333333333333333333333333333333333333333336e-4 * t148 * t122 - 0.17066666666666666666666666666666666666666666666667e-3 * t67 * t122 + 0.13653333333333333333333333333333333333333333333334e-5 * t153 * t130 - 0.2048e-5 * t71 * t130 + 0.81920000000000000000000000000000000000000000000003e-8 * t158 * t143
  t166 = 0.1e1 / t92
  t167 = t86 * t166
  t168 = t82 * t22
  t171 = t90 * t94
  t174 = 0.1e1 / t99
  t175 = t91 * t174
  t178 = t97 * t101
  t182 = 0.1e1 / t99 / t92
  t183 = t98 * t182
  t186 = 0.5e1 / 0.3e1 * t82 * t22 * t88 + 0.5e1 / 0.3e1 * t167 * t168 - 0.10e2 * t171 * t168 - 0.10e2 * t175 * t168 + 0.25e2 / 0.3e1 * t178 * t168 + 0.25e2 / 0.3e1 * t183 * t168
  t188 = -0.10666666666666666666666666666666666666666666666667e-1 * t26 * t114 + 0.85333333333333333333333333333333333333333333333336e-4 * t117 * t122 - 0.17066666666666666666666666666666666666666666666667e-3 * t40 * t122 + 0.13653333333333333333333333333333333333333333333334e-5 * t127 * t130 - 0.2048e-5 * t53 * t130 + 0.81920000000000000000000000000000000000000000000003e-8 * t136 * t143 + t161 * t103 + t74 * t186
  t193 = t17 / t20
  t195 = 0.1e1 / t20 / t41
  t197 = t28 * t195 * t34
  t200 = t41 * t110
  t202 = 0.1e1 / t19 / t200
  t204 = t27 * t202 * t47
  t207 = t25 * t52
  t208 = t54 * t18
  t210 = 0.1e1 / t208 * t57
  t217 = t38 * t135
  t218 = t54 * t41
  t222 = 0.1e1 / t20 / t218 * t141 * t28
  t229 = t135 * s0
  t230 = t51 * t229
  t235 = 0.1e1 / t140 / t33
  t237 = 0.1e1 / t19 / t54 / t200 * t235 * t27
  t244 = t62 * t52
  t251 = t66 * t135
  t258 = t70 * t229
  t261 = 0.39111111111111111111111111111111111111111111111112e-1 * t63 * t197 - 0.76800000000000000000000000000000000000000000000003e-3 * t148 * t204 + 0.36408888888888888888888888888888888888888888888891e-5 * t244 * t210 + 0.10808888888888888888888888888888888888888888888889e-2 * t67 * t204 - 0.19569777777777777777777777777777777777777777777779e-4 * t153 * t210 + 0.43690666666666666666666666666666666666666666666670e-7 * t251 * t222 + 0.18432e-4 * t71 * t210 - 0.16110933333333333333333333333333333333333333333334e-6 * t158 * t222 + 0.69905066666666666666666666666666666666666666666671e-9 * t258 * t237
  t268 = tau0 ** 2
  t269 = t268 * t27
  t273 = t86 * t94
  t274 = t269 * t44
  t277 = t82 * t112
  t280 = t90 * t174
  t285 = t91 * t101
  t290 = t97 * t182
  t296 = 0.1e1 / t99 / t93
  t297 = t98 * t296
  t302 = -0.40e2 / 0.9e1 * t82 * t112 * t88 + 0.100e3 / 0.9e1 * t269 * t44 * t166 - 0.500e3 / 0.9e1 * t273 * t274 - 0.40e2 / 0.9e1 * t167 * t277 - 0.200e3 * t280 * t274 + 0.80e2 / 0.3e1 * t171 * t277 - 0.200e3 / 0.9e1 * t285 * t274 + 0.80e2 / 0.3e1 * t175 * t277 + 0.2500e4 / 0.9e1 * t290 * t274 - 0.200e3 / 0.9e1 * t178 * t277 + 0.500e3 / 0.3e1 * t297 * t274 - 0.200e3 / 0.9e1 * t183 * t277
  t304 = 0.39111111111111111111111111111111111111111111111112e-1 * t26 * t197 - 0.76800000000000000000000000000000000000000000000003e-3 * t117 * t204 + 0.36408888888888888888888888888888888888888888888891e-5 * t207 * t210 + 0.10808888888888888888888888888888888888888888888889e-2 * t40 * t204 - 0.19569777777777777777777777777777777777777777777779e-4 * t127 * t210 + 0.43690666666666666666666666666666666666666666666670e-7 * t217 * t222 + 0.18432e-4 * t53 * t210 - 0.16110933333333333333333333333333333333333333333334e-6 * t136 * t222 + 0.69905066666666666666666666666666666666666666666671e-9 * t230 * t237 + t261 * t103 + 0.2e1 * t161 * t186 + t74 * t302
  t308 = t17 * t19
  t310 = 0.1e1 / t20 / t42
  t312 = t28 * t310 * t34
  t318 = t27 / t19 / t54 * t47
  t322 = 0.1e1 / t137 * t57
  t325 = t25 * t135
  t330 = 0.1e1 / t20 / t54 / t42 * t141 * t28
  t339 = t38 * t229
  t340 = t54 ** 2
  t344 = 0.1e1 / t19 / t340 * t235 * t27
  t353 = t135 * t39
  t354 = t51 * t353
  t358 = 0.1e1 / t140 / t46
  t359 = 0.1e1 / t340 / t110 * t358
  t368 = t62 * t135
  t377 = t66 * t229
  t386 = t70 * t353
  t389 = -0.18251851851851851851851851851851851851851851851852e0 * t63 * t312 + 0.64663703703703703703703703703703703703703703703706e-2 * t148 * t318 - 0.69176888888888888888888888888888888888888888888893e-4 * t244 * t322 + 0.11650844444444444444444444444444444444444444444445e-6 * t368 * t330 - 0.79265185185185185185185185185185185185185185185186e-2 * t67 * t318 + 0.24181570370370370370370370370370370370370370370372e-3 * t153 * t322 - 0.11796480000000000000000000000000000000000000000001e-5 * t251 * t330 + 0.37282702222222222222222222222222222222222222222226e-8 * t377 * t344 - 0.184320e-3 * t71 * t322 + 0.26305422222222222222222222222222222222222222222223e-5 * t158 * t330 - 0.24466773333333333333333333333333333333333333333335e-7 * t258 * t344 + 0.74565404444444444444444444444444444444444444444451e-10 * t386 * t359
  t395 = t82 * t195
  t398 = t269 * t120
  t420 = t90 * t101
  t421 = t268 * tau0
  t422 = t421 * t55
  t425 = t91 * t182
  t428 = t97 * t296
  t431 = t99 ** 2
  t432 = 0.1e1 / t431
  t433 = t98 * t432
  t439 = t86 * t174
  t444 = -0.880e3 / 0.9e1 * t175 * t395 - 0.20000e5 / 0.9e1 * t290 * t398 + 0.2200e4 / 0.27e2 * t178 * t395 - 0.4000e4 / 0.3e1 * t297 * t398 + 0.2200e4 / 0.27e2 * t183 * t395 + 0.4000e4 / 0.9e1 * t273 * t398 + 0.440e3 / 0.27e2 * t167 * t395 + 0.1600e4 * t280 * t398 - 0.880e3 / 0.9e1 * t171 * t395 + 0.1600e4 / 0.9e1 * t285 * t398 + 0.440e3 / 0.27e2 * t82 * t195 * t88 - 0.26000e5 / 0.9e1 * t420 * t422 + 0.10000e5 / 0.3e1 * t425 * t422 + 0.25000e5 / 0.3e1 * t428 * t422 + 0.35000e5 / 0.9e1 * t433 * t422 - 0.800e3 / 0.9e1 * t269 * t120 * t166 - 0.17000e5 / 0.9e1 * t439 * t422 - 0.1000e4 / 0.9e1 * t422 * t94
  t446 = -0.18251851851851851851851851851851851851851851851852e0 * t26 * t312 + 0.64663703703703703703703703703703703703703703703706e-2 * t117 * t318 - 0.69176888888888888888888888888888888888888888888893e-4 * t207 * t322 + 0.11650844444444444444444444444444444444444444444445e-6 * t325 * t330 - 0.79265185185185185185185185185185185185185185185186e-2 * t40 * t318 + 0.24181570370370370370370370370370370370370370370372e-3 * t127 * t322 - 0.11796480000000000000000000000000000000000000000001e-5 * t217 * t330 + 0.37282702222222222222222222222222222222222222222226e-8 * t339 * t344 - 0.184320e-3 * t53 * t322 + 0.26305422222222222222222222222222222222222222222223e-5 * t136 * t330 - 0.24466773333333333333333333333333333333333333333335e-7 * t230 * t344 + 0.74565404444444444444444444444444444444444444444451e-10 * t354 * t359 + t389 * t103 + 0.3e1 * t261 * t186 + 0.3e1 * t161 * t302 + t74 * t444
  t451 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t105 + t6 * t109 * t188 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t193 * t304 - 0.3e1 / 0.8e1 * t6 * t308 * t446)
  t469 = t27 / t19 / t128 * t47
  t475 = t28 / t20 / t118 * t34
  t482 = 0.1e1 / t20 / t54 / t118 * t141 * t28
  t489 = 0.1e1 / t19 / t340 / r0 * t235 * t27
  t493 = 0.1e1 / t218 * t57
  t500 = t135 * t52
  t508 = 0.1e1 / t20 / t340 / t118 / t140 / t56 * t28
  t540 = 0.1e1 / t340 / t41 * t358
  t554 = 0.10342716049382716049382716049382716049382716049383e1 * t63 * t475 - 0.57780148148148148148148148148148148148148148148150e-1 * t148 * t469 + 0.10368442469135802469135802469135802469135802469136e-2 * t244 * t493 - 0.38059425185185185185185185185185185185185185185188e-5 * t368 * t482 + 0.99420539259259259259259259259259259259259259259267e-8 * t62 * t229 * t489 + 0.66054320987654320987654320987654320987654320987655e-1 * t67 * t469 - 0.29981708641975308641975308641975308641975308641977e-2 * t153 * t493 + 0.23859958518518518518518518518518518518518518518520e-4 * t251 * t482 - 0.16155837629629629629629629629629629629629629629631e-6 * t377 * t489 + 0.39768215703703703703703703703703703703703703703709e-9 * t66 * t353 * t540 + 0.2027520e-2 * t71 * t493 - 0.41848983703703703703703703703703703703703703703705e-4 * t158 * t482 + 0.62409690074074074074074074074074074074074074074078e-6 * t258 * t489 - 0.40265318400000000000000000000000000000000000000004e-8 * t386 * t540 + 0.47721858844444444444444444444444444444444444444450e-11 * t70 * t500 * t508
  t562 = t268 ** 2
  t565 = 0.1e1 / t20 / t208
  t569 = t421 * t129
  t585 = t269 * t202
  t588 = t82 * t310
  t595 = -0.100000e6 / 0.27e2 * t562 * t28 * t565 * t174 - 0.160000e6 / 0.3e1 * t425 * t569 - 0.400000e6 / 0.3e1 * t428 * t569 - 0.560000e6 / 0.9e1 * t433 * t569 + 0.272000e6 / 0.9e1 * t439 * t569 + 0.54400e5 / 0.81e2 * t269 * t202 * t166 + 0.416000e6 / 0.9e1 * t420 * t569 + 0.16000e5 / 0.9e1 * t569 * t94 + 0.1360000e7 / 0.81e2 * t290 * t585 - 0.30800e5 / 0.81e2 * t178 * t588 + 0.272000e6 / 0.27e2 * t297 * t585 - 0.30800e5 / 0.81e2 * t183 * t588
  t609 = t562 * t565 * t28
  t630 = -0.272000e6 / 0.81e2 * t273 * t585 - 0.6160e4 / 0.81e2 * t167 * t588 + 0.12320e5 / 0.27e2 * t171 * t588 + 0.12320e5 / 0.27e2 * t175 * t588 - 0.6160e4 / 0.81e2 * t82 * t310 * t88 - 0.200000e6 / 0.9e1 * t86 * t101 * t609 - 0.200000e6 / 0.27e2 * t90 * t182 * t609 + 0.800000e6 / 0.9e1 * t91 * t296 * t609 + 0.3500000e7 / 0.27e2 * t97 * t432 * t609 + 0.1400000e7 / 0.27e2 * t98 / t431 / t87 * t609 - 0.108800e6 / 0.9e1 * t280 * t585 - 0.108800e6 / 0.81e2 * t285 * t585
  t642 = 0.66054320987654320987654320987654320987654320987655e-1 * t40 * t469 + 0.10342716049382716049382716049382716049382716049383e1 * t26 * t475 + 0.23859958518518518518518518518518518518518518518520e-4 * t217 * t482 - 0.16155837629629629629629629629629629629629629629631e-6 * t339 * t489 + 0.2027520e-2 * t53 * t493 - 0.41848983703703703703703703703703703703703703703705e-4 * t136 * t482 + 0.62409690074074074074074074074074074074074074074078e-6 * t230 * t489 + 0.47721858844444444444444444444444444444444444444450e-11 * t51 * t500 * t508 - 0.57780148148148148148148148148148148148148148148150e-1 * t117 * t469 - 0.38059425185185185185185185185185185185185185185188e-5 * t325 * t482 + 0.99420539259259259259259259259259259259259259259267e-8 * t25 * t229 * t489 + t554 * t103 + 0.4e1 * t389 * t186 + 0.6e1 * t261 * t302 + 0.4e1 * t161 * t444 + t74 * (t595 + t630) + 0.10368442469135802469135802469135802469135802469136e-2 * t207 * t493 - 0.29981708641975308641975308641975308641975308641977e-2 * t127 * t493 + 0.39768215703703703703703703703703703703703703703709e-9 * t38 * t353 * t540 - 0.40265318400000000000000000000000000000000000000004e-8 * t354 * t540
  t647 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t112 * t105 - 0.5e1 / 0.9e1 * t6 * t23 * t188 + t6 * t109 * t304 / 0.2e1 - t6 * t193 * t446 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t308 * t642)
  v4rho4_0_ = 0.2e1 * r0 * t647 + 0.8e1 * t451

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
  t32 = params.cx_local[0]
  t33 = params.cx_local[1]
  t34 = t33 * s0
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t42 = 0.1e1 + 0.4e-2 * s0 * t39
  t43 = 0.1e1 / t42
  t44 = t39 * t43
  t47 = params.cx_local[2]
  t48 = s0 ** 2
  t49 = t47 * t48
  t50 = t35 ** 2
  t53 = 0.1e1 / t36 / t50 / r0
  t54 = t42 ** 2
  t55 = 0.1e1 / t54
  t56 = t53 * t55
  t59 = params.cx_local[3]
  t60 = t48 * s0
  t61 = t59 * t60
  t62 = t50 ** 2
  t65 = 0.1e1 / t54 / t42
  t66 = 0.1e1 / t62 * t65
  t69 = params.cx_nlocal[0]
  t70 = params.cx_nlocal[1]
  t71 = t70 * s0
  t74 = params.cx_nlocal[2]
  t75 = t74 * t48
  t78 = params.cx_nlocal[3]
  t79 = t78 * t60
  t82 = t69 + 0.4e-2 * t71 * t44 + 0.16e-4 * t75 * t56 + 0.64e-7 * t79 * t66
  t83 = 6 ** (0.1e1 / 0.3e1)
  t84 = t83 ** 2
  t85 = jnp.pi ** 2
  t86 = t85 ** (0.1e1 / 0.3e1)
  t87 = t86 ** 2
  t89 = 0.3e1 / 0.10e2 * t84 * t87
  t92 = tau0 / t37 / r0
  t93 = t89 - t92
  t94 = t89 + t92
  t95 = 0.1e1 / t94
  t97 = t93 ** 2
  t98 = t97 * t93
  t99 = t94 ** 2
  t100 = t99 * t94
  t101 = 0.1e1 / t100
  t104 = t97 ** 2
  t105 = t104 * t93
  t106 = t99 ** 2
  t108 = 0.1e1 / t106 / t94
  t110 = -0.2e1 * t98 * t101 + t105 * t108 + t93 * t95
  t112 = t32 + 0.4e-2 * t34 * t44 + 0.16e-4 * t49 * t56 + 0.64e-7 * t61 * t66 + t82 * t110
  t116 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t117 = t116 * f.p.zeta_threshold
  t119 = f.my_piecewise3(t20, t117, t21 * t19)
  t120 = t30 ** 2
  t121 = 0.1e1 / t120
  t122 = t119 * t121
  t125 = t5 * t122 * t112 / 0.8e1
  t126 = t119 * t30
  t127 = t35 * r0
  t129 = 0.1e1 / t37 / t127
  t130 = t129 * t43
  t133 = t33 * t48
  t137 = 0.1e1 / t36 / t50 / t35 * t55
  t142 = t47 * t60
  t145 = 0.1e1 / t62 / r0 * t65
  t150 = t48 ** 2
  t151 = t59 * t150
  t155 = t54 ** 2
  t156 = 0.1e1 / t155
  t157 = 0.1e1 / t37 / t62 / t127 * t156
  t162 = t70 * t48
  t167 = t74 * t60
  t172 = t78 * t150
  t175 = -0.10666666666666666666666666666666666666666666666667e-1 * t71 * t130 + 0.42666666666666666666666666666666666666666666666668e-4 * t162 * t137 - 0.85333333333333333333333333333333333333333333333333e-4 * t75 * t137 + 0.34133333333333333333333333333333333333333333333334e-6 * t167 * t145 - 0.512e-6 * t79 * t145 + 0.20480000000000000000000000000000000000000000000001e-8 * t172 * t157
  t177 = tau0 * t39
  t180 = 0.1e1 / t99
  t181 = t93 * t180
  t184 = t97 * t101
  t187 = 0.1e1 / t106
  t188 = t98 * t187
  t191 = t104 * t108
  t195 = 0.1e1 / t106 / t99
  t196 = t105 * t195
  t199 = 0.5e1 / 0.3e1 * t177 * t95 + 0.5e1 / 0.3e1 * t181 * t177 - 0.10e2 * t184 * t177 - 0.10e2 * t188 * t177 + 0.25e2 / 0.3e1 * t191 * t177 + 0.25e2 / 0.3e1 * t196 * t177
  t201 = -0.10666666666666666666666666666666666666666666666667e-1 * t34 * t130 + 0.42666666666666666666666666666666666666666666666668e-4 * t133 * t137 - 0.85333333333333333333333333333333333333333333333333e-4 * t49 * t137 + 0.34133333333333333333333333333333333333333333333334e-6 * t142 * t145 - 0.512e-6 * t61 * t145 + 0.20480000000000000000000000000000000000000000000001e-8 * t151 * t157 + t175 * t110 + t82 * t199
  t206 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t112 - t125 - 0.3e1 / 0.8e1 * t5 * t126 * t201)
  t208 = r1 <= f.p.dens_threshold
  t209 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t210 = 0.1e1 + t209
  t211 = t210 <= f.p.zeta_threshold
  t212 = t210 ** (0.1e1 / 0.3e1)
  t214 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t217 = f.my_piecewise3(t211, 0, 0.4e1 / 0.3e1 * t212 * t214)
  t218 = t217 * t30
  t219 = t33 * s2
  t220 = r1 ** 2
  t221 = r1 ** (0.1e1 / 0.3e1)
  t222 = t221 ** 2
  t224 = 0.1e1 / t222 / t220
  t227 = 0.1e1 + 0.4e-2 * s2 * t224
  t228 = 0.1e1 / t227
  t229 = t224 * t228
  t232 = s2 ** 2
  t233 = t47 * t232
  t234 = t220 ** 2
  t237 = 0.1e1 / t221 / t234 / r1
  t238 = t227 ** 2
  t239 = 0.1e1 / t238
  t240 = t237 * t239
  t243 = t232 * s2
  t244 = t59 * t243
  t245 = t234 ** 2
  t248 = 0.1e1 / t238 / t227
  t249 = 0.1e1 / t245 * t248
  t252 = t70 * s2
  t255 = t74 * t232
  t258 = t78 * t243
  t261 = t69 + 0.4e-2 * t252 * t229 + 0.16e-4 * t255 * t240 + 0.64e-7 * t258 * t249
  t264 = tau1 / t222 / r1
  t265 = t89 - t264
  t266 = t89 + t264
  t267 = 0.1e1 / t266
  t269 = t265 ** 2
  t270 = t269 * t265
  t271 = t266 ** 2
  t272 = t271 * t266
  t273 = 0.1e1 / t272
  t276 = t269 ** 2
  t277 = t276 * t265
  t278 = t271 ** 2
  t280 = 0.1e1 / t278 / t266
  t282 = t265 * t267 - 0.2e1 * t270 * t273 + t277 * t280
  t284 = t32 + 0.4e-2 * t219 * t229 + 0.16e-4 * t233 * t240 + 0.64e-7 * t244 * t249 + t261 * t282
  t289 = f.my_piecewise3(t211, t117, t212 * t210)
  t290 = t289 * t121
  t293 = t5 * t290 * t284 / 0.8e1
  t295 = f.my_piecewise3(t208, 0, -0.3e1 / 0.8e1 * t5 * t218 * t284 - t293)
  t297 = t21 ** 2
  t298 = 0.1e1 / t297
  t299 = t26 ** 2
  t304 = t16 / t22 / t6
  t306 = -0.2e1 * t23 + 0.2e1 * t304
  t307 = f.my_piecewise5(t10, 0, t14, 0, t306)
  t311 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t298 * t299 + 0.4e1 / 0.3e1 * t21 * t307)
  t318 = t5 * t29 * t121 * t112
  t324 = 0.1e1 / t120 / t6
  t328 = t5 * t119 * t324 * t112 / 0.12e2
  t330 = t5 * t122 * t201
  t334 = 0.1e1 / t37 / t50 * t43
  t337 = t50 * t127
  t340 = 0.1e1 / t36 / t337 * t55
  t346 = 0.1e1 / t62 / t35 * t65
  t357 = 0.1e1 / t37 / t62 / t50 * t156
  t364 = t150 * s0
  t371 = 0.1e1 / t36 / t62 / t337 / t155 / t42
  t399 = tau0 * t129
  t402 = tau0 ** 2
  t403 = t402 * t53
  t433 = -0.40e2 / 0.9e1 * t399 * t95 + 0.50e2 / 0.9e1 * t403 * t180 - 0.250e3 / 0.9e1 * t93 * t101 * t403 - 0.40e2 / 0.9e1 * t181 * t399 - 0.100e3 * t97 * t187 * t403 + 0.80e2 / 0.3e1 * t184 * t399 - 0.100e3 / 0.9e1 * t98 * t108 * t403 + 0.80e2 / 0.3e1 * t188 * t399 + 0.1250e4 / 0.9e1 * t104 * t195 * t403 - 0.200e3 / 0.9e1 * t191 * t399 + 0.250e3 / 0.3e1 * t105 / t106 / t100 * t403 - 0.200e3 / 0.9e1 * t196 * t399
  t435 = 0.39111111111111111111111111111111111111111111111112e-1 * t34 * t334 - 0.38400000000000000000000000000000000000000000000001e-3 * t133 * t340 + 0.91022222222222222222222222222222222222222222222228e-6 * t33 * t60 * t346 + 0.54044444444444444444444444444444444444444444444444e-3 * t49 * t340 - 0.48924444444444444444444444444444444444444444444446e-5 * t142 * t346 + 0.10922666666666666666666666666666666666666666666667e-7 * t47 * t150 * t357 + 0.4608e-5 * t61 * t346 - 0.40277333333333333333333333333333333333333333333336e-7 * t151 * t357 + 0.87381333333333333333333333333333333333333333333340e-10 * t59 * t364 * t371 + (0.39111111111111111111111111111111111111111111111112e-1 * t71 * t334 - 0.38400000000000000000000000000000000000000000000001e-3 * t162 * t340 + 0.91022222222222222222222222222222222222222222222228e-6 * t70 * t60 * t346 + 0.54044444444444444444444444444444444444444444444444e-3 * t75 * t340 - 0.48924444444444444444444444444444444444444444444446e-5 * t167 * t346 + 0.10922666666666666666666666666666666666666666666667e-7 * t74 * t150 * t357 + 0.4608e-5 * t79 * t346 - 0.40277333333333333333333333333333333333333333333336e-7 * t172 * t357 + 0.87381333333333333333333333333333333333333333333340e-10 * t78 * t364 * t371) * t110 + 0.2e1 * t175 * t199 + t82 * t433
  t440 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t311 * t30 * t112 - t318 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t201 + t328 - t330 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t126 * t435)
  t441 = t212 ** 2
  t442 = 0.1e1 / t441
  t443 = t214 ** 2
  t447 = f.my_piecewise5(t14, 0, t10, 0, -t306)
  t451 = f.my_piecewise3(t211, 0, 0.4e1 / 0.9e1 * t442 * t443 + 0.4e1 / 0.3e1 * t212 * t447)
  t458 = t5 * t217 * t121 * t284
  t463 = t5 * t289 * t324 * t284 / 0.12e2
  t465 = f.my_piecewise3(t208, 0, -0.3e1 / 0.8e1 * t5 * t451 * t30 * t284 - t458 / 0.4e1 + t463)
  d11 = 0.2e1 * t206 + 0.2e1 * t295 + t6 * (t440 + t465)
  t468 = -t7 - t24
  t469 = f.my_piecewise5(t10, 0, t14, 0, t468)
  t472 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t469)
  t473 = t472 * t30
  t478 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t473 * t112 - t125)
  t480 = f.my_piecewise5(t14, 0, t10, 0, -t468)
  t483 = f.my_piecewise3(t211, 0, 0.4e1 / 0.3e1 * t212 * t480)
  t484 = t483 * t30
  t488 = t289 * t30
  t489 = t220 * r1
  t491 = 0.1e1 / t222 / t489
  t492 = t491 * t228
  t495 = t33 * t232
  t499 = 0.1e1 / t221 / t234 / t220 * t239
  t504 = t47 * t243
  t507 = 0.1e1 / t245 / r1 * t248
  t512 = t232 ** 2
  t513 = t59 * t512
  t517 = t238 ** 2
  t518 = 0.1e1 / t517
  t519 = 0.1e1 / t222 / t245 / t489 * t518
  t524 = t70 * t232
  t529 = t74 * t243
  t534 = t78 * t512
  t537 = -0.10666666666666666666666666666666666666666666666667e-1 * t252 * t492 + 0.42666666666666666666666666666666666666666666666668e-4 * t524 * t499 - 0.85333333333333333333333333333333333333333333333333e-4 * t255 * t499 + 0.34133333333333333333333333333333333333333333333334e-6 * t529 * t507 - 0.512e-6 * t258 * t507 + 0.20480000000000000000000000000000000000000000000001e-8 * t534 * t519
  t539 = tau1 * t224
  t542 = 0.1e1 / t271
  t543 = t265 * t542
  t546 = t269 * t273
  t549 = 0.1e1 / t278
  t550 = t270 * t549
  t553 = t276 * t280
  t557 = 0.1e1 / t278 / t271
  t558 = t277 * t557
  t561 = 0.5e1 / 0.3e1 * t539 * t267 + 0.5e1 / 0.3e1 * t543 * t539 - 0.10e2 * t546 * t539 - 0.10e2 * t550 * t539 + 0.25e2 / 0.3e1 * t553 * t539 + 0.25e2 / 0.3e1 * t558 * t539
  t563 = -0.10666666666666666666666666666666666666666666666667e-1 * t219 * t492 + 0.42666666666666666666666666666666666666666666666668e-4 * t495 * t499 - 0.85333333333333333333333333333333333333333333333333e-4 * t233 * t499 + 0.34133333333333333333333333333333333333333333333334e-6 * t504 * t507 - 0.512e-6 * t244 * t507 + 0.20480000000000000000000000000000000000000000000001e-8 * t513 * t519 + t537 * t282 + t261 * t561
  t568 = f.my_piecewise3(t208, 0, -0.3e1 / 0.8e1 * t5 * t484 * t284 - t293 - 0.3e1 / 0.8e1 * t5 * t488 * t563)
  t572 = 0.2e1 * t304
  t573 = f.my_piecewise5(t10, 0, t14, 0, t572)
  t577 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t298 * t469 * t26 + 0.4e1 / 0.3e1 * t21 * t573)
  t584 = t5 * t472 * t121 * t112
  t592 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t577 * t30 * t112 - t584 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t473 * t201 - t318 / 0.8e1 + t328 - t330 / 0.8e1)
  t596 = f.my_piecewise5(t14, 0, t10, 0, -t572)
  t600 = f.my_piecewise3(t211, 0, 0.4e1 / 0.9e1 * t442 * t480 * t214 + 0.4e1 / 0.3e1 * t212 * t596)
  t607 = t5 * t483 * t121 * t284
  t614 = t5 * t290 * t563
  t617 = f.my_piecewise3(t208, 0, -0.3e1 / 0.8e1 * t5 * t600 * t30 * t284 - t607 / 0.8e1 - t458 / 0.8e1 + t463 - 0.3e1 / 0.8e1 * t5 * t218 * t563 - t614 / 0.8e1)
  d12 = t206 + t295 + t478 + t568 + t6 * (t592 + t617)
  t622 = t469 ** 2
  t626 = 0.2e1 * t23 + 0.2e1 * t304
  t627 = f.my_piecewise5(t10, 0, t14, 0, t626)
  t631 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t298 * t622 + 0.4e1 / 0.3e1 * t21 * t627)
  t638 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t631 * t30 * t112 - t584 / 0.4e1 + t328)
  t639 = t480 ** 2
  t643 = f.my_piecewise5(t14, 0, t10, 0, -t626)
  t647 = f.my_piecewise3(t211, 0, 0.4e1 / 0.9e1 * t442 * t639 + 0.4e1 / 0.3e1 * t212 * t643)
  t659 = 0.1e1 / t222 / t234 * t228
  t662 = t234 * t489
  t665 = 0.1e1 / t221 / t662 * t239
  t671 = 0.1e1 / t245 / t220 * t248
  t682 = 0.1e1 / t222 / t245 / t234 * t518
  t689 = t512 * s2
  t696 = 0.1e1 / t221 / t245 / t662 / t517 / t227
  t724 = tau1 * t491
  t727 = tau1 ** 2
  t728 = t727 * t237
  t758 = -0.40e2 / 0.9e1 * t724 * t267 + 0.50e2 / 0.9e1 * t728 * t542 - 0.250e3 / 0.9e1 * t265 * t273 * t728 - 0.40e2 / 0.9e1 * t543 * t724 - 0.100e3 * t269 * t549 * t728 + 0.80e2 / 0.3e1 * t546 * t724 - 0.100e3 / 0.9e1 * t270 * t280 * t728 + 0.80e2 / 0.3e1 * t550 * t724 + 0.1250e4 / 0.9e1 * t276 * t557 * t728 - 0.200e3 / 0.9e1 * t553 * t724 + 0.250e3 / 0.3e1 * t277 / t278 / t272 * t728 - 0.200e3 / 0.9e1 * t558 * t724
  t760 = 0.39111111111111111111111111111111111111111111111112e-1 * t219 * t659 - 0.38400000000000000000000000000000000000000000000001e-3 * t495 * t665 + 0.91022222222222222222222222222222222222222222222228e-6 * t33 * t243 * t671 + 0.54044444444444444444444444444444444444444444444444e-3 * t233 * t665 - 0.48924444444444444444444444444444444444444444444446e-5 * t504 * t671 + 0.10922666666666666666666666666666666666666666666667e-7 * t47 * t512 * t682 + 0.4608e-5 * t244 * t671 - 0.40277333333333333333333333333333333333333333333336e-7 * t513 * t682 + 0.87381333333333333333333333333333333333333333333340e-10 * t59 * t689 * t696 + (0.39111111111111111111111111111111111111111111111112e-1 * t252 * t659 - 0.38400000000000000000000000000000000000000000000001e-3 * t524 * t665 + 0.91022222222222222222222222222222222222222222222228e-6 * t70 * t243 * t671 + 0.54044444444444444444444444444444444444444444444444e-3 * t255 * t665 - 0.48924444444444444444444444444444444444444444444446e-5 * t529 * t671 + 0.10922666666666666666666666666666666666666666666667e-7 * t74 * t512 * t682 + 0.4608e-5 * t258 * t671 - 0.40277333333333333333333333333333333333333333333336e-7 * t534 * t682 + 0.87381333333333333333333333333333333333333333333340e-10 * t78 * t689 * t696) * t282 + 0.2e1 * t537 * t561 + t261 * t758
  t765 = f.my_piecewise3(t208, 0, -0.3e1 / 0.8e1 * t5 * t647 * t30 * t284 - t607 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t484 * t563 + t463 - t614 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t488 * t760)
  d22 = 0.2e1 * t478 + 0.2e1 * t568 + t6 * (t638 + t765)
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
  t44 = params.cx_local[0]
  t45 = params.cx_local[1]
  t46 = t45 * s0
  t47 = r0 ** 2
  t48 = r0 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t51 = 0.1e1 / t49 / t47
  t54 = 0.1e1 + 0.4e-2 * s0 * t51
  t55 = 0.1e1 / t54
  t56 = t51 * t55
  t59 = params.cx_local[2]
  t60 = s0 ** 2
  t61 = t59 * t60
  t62 = t47 ** 2
  t63 = t62 * r0
  t65 = 0.1e1 / t48 / t63
  t66 = t54 ** 2
  t67 = 0.1e1 / t66
  t68 = t65 * t67
  t71 = params.cx_local[3]
  t72 = t60 * s0
  t73 = t71 * t72
  t74 = t62 ** 2
  t75 = 0.1e1 / t74
  t77 = 0.1e1 / t66 / t54
  t78 = t75 * t77
  t81 = params.cx_nlocal[0]
  t82 = params.cx_nlocal[1]
  t83 = t82 * s0
  t86 = params.cx_nlocal[2]
  t87 = t86 * t60
  t90 = params.cx_nlocal[3]
  t91 = t90 * t72
  t94 = t81 + 0.4e-2 * t83 * t56 + 0.16e-4 * t87 * t68 + 0.64e-7 * t91 * t78
  t95 = 6 ** (0.1e1 / 0.3e1)
  t96 = t95 ** 2
  t97 = jnp.pi ** 2
  t98 = t97 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t101 = 0.3e1 / 0.10e2 * t96 * t99
  t104 = tau0 / t49 / r0
  t105 = t101 - t104
  t106 = t101 + t104
  t107 = 0.1e1 / t106
  t109 = t105 ** 2
  t110 = t109 * t105
  t111 = t106 ** 2
  t112 = t111 * t106
  t113 = 0.1e1 / t112
  t116 = t109 ** 2
  t117 = t116 * t105
  t118 = t111 ** 2
  t120 = 0.1e1 / t118 / t106
  t122 = t105 * t107 - 0.2e1 * t110 * t113 + t117 * t120
  t124 = t44 + 0.4e-2 * t46 * t56 + 0.16e-4 * t61 * t68 + 0.64e-7 * t73 * t78 + t94 * t122
  t130 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t131 = t42 ** 2
  t132 = 0.1e1 / t131
  t133 = t130 * t132
  t137 = t130 * t42
  t138 = t47 * r0
  t140 = 0.1e1 / t49 / t138
  t141 = t140 * t55
  t144 = t45 * t60
  t147 = 0.1e1 / t48 / t62 / t47
  t148 = t147 * t67
  t153 = t59 * t72
  t156 = 0.1e1 / t74 / r0 * t77
  t161 = t60 ** 2
  t162 = t71 * t161
  t163 = t74 * t138
  t166 = t66 ** 2
  t167 = 0.1e1 / t166
  t168 = 0.1e1 / t49 / t163 * t167
  t173 = t82 * t60
  t178 = t86 * t72
  t183 = t90 * t161
  t186 = -0.10666666666666666666666666666666666666666666666667e-1 * t83 * t141 + 0.42666666666666666666666666666666666666666666666668e-4 * t173 * t148 - 0.85333333333333333333333333333333333333333333333333e-4 * t87 * t148 + 0.34133333333333333333333333333333333333333333333334e-6 * t178 * t156 - 0.512e-6 * t91 * t156 + 0.20480000000000000000000000000000000000000000000001e-8 * t183 * t168
  t188 = tau0 * t51
  t191 = 0.1e1 / t111
  t192 = t105 * t191
  t195 = t109 * t113
  t198 = 0.1e1 / t118
  t199 = t110 * t198
  t202 = t116 * t120
  t206 = 0.1e1 / t118 / t111
  t207 = t117 * t206
  t210 = 0.5e1 / 0.3e1 * t188 * t107 + 0.5e1 / 0.3e1 * t192 * t188 - 0.10e2 * t195 * t188 - 0.10e2 * t199 * t188 + 0.25e2 / 0.3e1 * t202 * t188 + 0.25e2 / 0.3e1 * t207 * t188
  t212 = -0.10666666666666666666666666666666666666666666666667e-1 * t46 * t141 + 0.42666666666666666666666666666666666666666666666668e-4 * t144 * t148 - 0.85333333333333333333333333333333333333333333333333e-4 * t61 * t148 + 0.34133333333333333333333333333333333333333333333334e-6 * t153 * t156 - 0.512e-6 * t73 * t156 + 0.20480000000000000000000000000000000000000000000001e-8 * t162 * t168 + t186 * t122 + t94 * t210
  t216 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t217 = t216 * f.p.zeta_threshold
  t219 = f.my_piecewise3(t20, t217, t21 * t19)
  t221 = 0.1e1 / t131 / t6
  t222 = t219 * t221
  t226 = t219 * t132
  t230 = t219 * t42
  t232 = 0.1e1 / t49 / t62
  t233 = t232 * t55
  t236 = t62 * t138
  t239 = 0.1e1 / t48 / t236 * t67
  t242 = t45 * t72
  t245 = 0.1e1 / t74 / t47 * t77
  t252 = t59 * t161
  t256 = 0.1e1 / t49 / t74 / t62 * t167
  t263 = t161 * s0
  t264 = t71 * t263
  t269 = 0.1e1 / t166 / t54
  t270 = 0.1e1 / t48 / t74 / t236 * t269
  t277 = t82 * t72
  t284 = t86 * t161
  t291 = t90 * t263
  t294 = 0.39111111111111111111111111111111111111111111111112e-1 * t83 * t233 - 0.38400000000000000000000000000000000000000000000001e-3 * t173 * t239 + 0.91022222222222222222222222222222222222222222222228e-6 * t277 * t245 + 0.54044444444444444444444444444444444444444444444444e-3 * t87 * t239 - 0.48924444444444444444444444444444444444444444444446e-5 * t178 * t245 + 0.10922666666666666666666666666666666666666666666667e-7 * t284 * t256 + 0.4608e-5 * t91 * t245 - 0.40277333333333333333333333333333333333333333333336e-7 * t183 * t256 + 0.87381333333333333333333333333333333333333333333340e-10 * t291 * t270
  t298 = tau0 * t140
  t301 = tau0 ** 2
  t302 = t301 * t65
  t305 = t105 * t113
  t310 = t109 * t198
  t315 = t110 * t120
  t320 = t116 * t206
  t326 = 0.1e1 / t118 / t112
  t327 = t117 * t326
  t332 = -0.40e2 / 0.9e1 * t298 * t107 + 0.50e2 / 0.9e1 * t302 * t191 - 0.250e3 / 0.9e1 * t305 * t302 - 0.40e2 / 0.9e1 * t192 * t298 - 0.100e3 * t310 * t302 + 0.80e2 / 0.3e1 * t195 * t298 - 0.100e3 / 0.9e1 * t315 * t302 + 0.80e2 / 0.3e1 * t199 * t298 + 0.1250e4 / 0.9e1 * t320 * t302 - 0.200e3 / 0.9e1 * t202 * t298 + 0.250e3 / 0.3e1 * t327 * t302 - 0.200e3 / 0.9e1 * t207 * t298
  t334 = 0.39111111111111111111111111111111111111111111111112e-1 * t46 * t233 - 0.38400000000000000000000000000000000000000000000001e-3 * t144 * t239 + 0.91022222222222222222222222222222222222222222222228e-6 * t242 * t245 + 0.54044444444444444444444444444444444444444444444444e-3 * t61 * t239 - 0.48924444444444444444444444444444444444444444444446e-5 * t153 * t245 + 0.10922666666666666666666666666666666666666666666667e-7 * t252 * t256 + 0.4608e-5 * t73 * t245 - 0.40277333333333333333333333333333333333333333333336e-7 * t162 * t256 + 0.87381333333333333333333333333333333333333333333340e-10 * t264 * t270 + t294 * t122 + 0.2e1 * t186 * t210 + t94 * t332
  t339 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t124 - t5 * t133 * t124 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t137 * t212 + t5 * t222 * t124 / 0.12e2 - t5 * t226 * t212 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t230 * t334)
  t341 = r1 <= f.p.dens_threshold
  t342 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t343 = 0.1e1 + t342
  t344 = t343 <= f.p.zeta_threshold
  t345 = t343 ** (0.1e1 / 0.3e1)
  t346 = t345 ** 2
  t347 = 0.1e1 / t346
  t349 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t350 = t349 ** 2
  t354 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t358 = f.my_piecewise3(t344, 0, 0.4e1 / 0.9e1 * t347 * t350 + 0.4e1 / 0.3e1 * t345 * t354)
  t361 = r1 ** 2
  t362 = r1 ** (0.1e1 / 0.3e1)
  t363 = t362 ** 2
  t365 = 0.1e1 / t363 / t361
  t368 = 0.1e1 + 0.4e-2 * s2 * t365
  t370 = t365 / t368
  t373 = s2 ** 2
  t375 = t361 ** 2
  t379 = t368 ** 2
  t381 = 0.1e1 / t362 / t375 / r1 / t379
  t384 = t373 * s2
  t386 = t375 ** 2
  t390 = 0.1e1 / t386 / t379 / t368
  t405 = tau1 / t363 / r1
  t406 = t101 - t405
  t407 = t101 + t405
  t410 = t406 ** 2
  t412 = t407 ** 2
  t417 = t410 ** 2
  t419 = t412 ** 2
  t425 = t44 + 0.4e-2 * t45 * s2 * t370 + 0.16e-4 * t59 * t373 * t381 + 0.64e-7 * t71 * t384 * t390 + (t81 + 0.4e-2 * t82 * s2 * t370 + 0.16e-4 * t86 * t373 * t381 + 0.64e-7 * t90 * t384 * t390) * (t406 / t407 - 0.2e1 * t410 * t406 / t412 / t407 + t417 * t406 / t419 / t407)
  t431 = f.my_piecewise3(t344, 0, 0.4e1 / 0.3e1 * t345 * t349)
  t437 = f.my_piecewise3(t344, t217, t345 * t343)
  t443 = f.my_piecewise3(t341, 0, -0.3e1 / 0.8e1 * t5 * t358 * t42 * t425 - t5 * t431 * t132 * t425 / 0.4e1 + t5 * t437 * t221 * t425 / 0.12e2)
  t453 = t24 ** 2
  t457 = 0.6e1 * t33 - 0.6e1 * t16 / t453
  t458 = f.my_piecewise5(t10, 0, t14, 0, t457)
  t462 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t458)
  t485 = 0.1e1 / t131 / t24
  t498 = 0.1e1 / t49 / t63 * t55
  t503 = 0.1e1 / t48 / t74 * t67
  t507 = 0.1e1 / t163 * t77
  t514 = 0.1e1 / t49 / t74 / t63 * t167
  t524 = t74 ** 2
  t527 = 0.1e1 / t48 / t524 * t269
  t536 = t161 * t60
  t542 = 0.1e1 / t524 / t138 / t166 / t66
  t572 = -0.18251851851851851851851851851851851851851851851852e0 * t83 * t498 + 0.32331851851851851851851851851851851851851851851853e-2 * t173 * t503 - 0.17294222222222222222222222222222222222222222222223e-4 * t277 * t507 + 0.29127111111111111111111111111111111111111111111114e-7 * t82 * t161 * t514 - 0.39632592592592592592592592592592592592592592592592e-2 * t87 * t503 + 0.60453925925925925925925925925925925925925925925928e-4 * t178 * t507 - 0.29491200000000000000000000000000000000000000000001e-6 * t284 * t514 + 0.46603377777777777777777777777777777777777777777781e-9 * t86 * t263 * t527 - 0.46080e-4 * t91 * t507 + 0.65763555555555555555555555555555555555555555555559e-6 * t183 * t514 - 0.30583466666666666666666666666666666666666666666669e-8 * t291 * t527 + 0.46603377777777777777777777777777777777777777777783e-11 * t90 * t536 * t542
  t578 = t118 ** 2
  t582 = t301 * tau0 * t75
  t585 = tau0 * t232
  t600 = t301 * t147
  t625 = 0.8750e4 / 0.9e1 * t117 / t578 * t582 + 0.440e3 / 0.27e2 * t585 * t107 - 0.4250e4 / 0.9e1 * t105 * t198 * t582 - 0.6500e4 / 0.9e1 * t109 * t120 * t582 + 0.2500e4 / 0.3e1 * t110 * t206 * t582 + 0.6250e4 / 0.3e1 * t116 * t326 * t582 - 0.400e3 / 0.9e1 * t600 * t191 - 0.250e3 / 0.9e1 * t582 * t113 + 0.2000e4 / 0.9e1 * t305 * t600 + 0.440e3 / 0.27e2 * t192 * t585 + 0.800e3 * t310 * t600 - 0.880e3 / 0.9e1 * t195 * t585 + 0.800e3 / 0.9e1 * t315 * t600 - 0.880e3 / 0.9e1 * t199 * t585 - 0.10000e5 / 0.9e1 * t320 * t600 + 0.2200e4 / 0.27e2 * t202 * t585 - 0.2000e4 / 0.3e1 * t327 * t600 + 0.2200e4 / 0.27e2 * t207 * t585
  t627 = -0.18251851851851851851851851851851851851851851851852e0 * t46 * t498 + 0.32331851851851851851851851851851851851851851851853e-2 * t144 * t503 - 0.17294222222222222222222222222222222222222222222223e-4 * t242 * t507 + 0.29127111111111111111111111111111111111111111111114e-7 * t45 * t161 * t514 - 0.39632592592592592592592592592592592592592592592592e-2 * t61 * t503 + 0.60453925925925925925925925925925925925925925925928e-4 * t153 * t507 - 0.29491200000000000000000000000000000000000000000001e-6 * t252 * t514 + 0.46603377777777777777777777777777777777777777777781e-9 * t59 * t263 * t527 - 0.46080e-4 * t73 * t507 + 0.65763555555555555555555555555555555555555555555559e-6 * t162 * t514 - 0.30583466666666666666666666666666666666666666666669e-8 * t264 * t527 + 0.46603377777777777777777777777777777777777777777783e-11 * t71 * t536 * t542 + t572 * t122 + 0.3e1 * t294 * t210 + 0.3e1 * t186 * t332 + t94 * t625
  t632 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t462 * t42 * t124 - 0.3e1 / 0.8e1 * t5 * t41 * t132 * t124 - 0.9e1 / 0.8e1 * t5 * t43 * t212 + t5 * t130 * t221 * t124 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t133 * t212 - 0.9e1 / 0.8e1 * t5 * t137 * t334 - 0.5e1 / 0.36e2 * t5 * t219 * t485 * t124 + t5 * t222 * t212 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t226 * t334 - 0.3e1 / 0.8e1 * t5 * t230 * t627)
  t642 = f.my_piecewise5(t14, 0, t10, 0, -t457)
  t646 = f.my_piecewise3(t344, 0, -0.8e1 / 0.27e2 / t346 / t343 * t350 * t349 + 0.4e1 / 0.3e1 * t347 * t349 * t354 + 0.4e1 / 0.3e1 * t345 * t642)
  t664 = f.my_piecewise3(t341, 0, -0.3e1 / 0.8e1 * t5 * t646 * t42 * t425 - 0.3e1 / 0.8e1 * t5 * t358 * t132 * t425 + t5 * t431 * t221 * t425 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t437 * t485 * t425)
  d111 = 0.3e1 * t339 + 0.3e1 * t443 + t6 * (t632 + t664)

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
  t56 = params.cx_local[0]
  t57 = params.cx_local[1]
  t58 = t57 * s0
  t59 = r0 ** 2
  t60 = r0 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t63 = 0.1e1 / t61 / t59
  t66 = 0.1e1 + 0.4e-2 * s0 * t63
  t67 = 0.1e1 / t66
  t68 = t63 * t67
  t71 = params.cx_local[2]
  t72 = s0 ** 2
  t73 = t71 * t72
  t74 = t59 ** 2
  t75 = t74 * r0
  t77 = 0.1e1 / t60 / t75
  t78 = t66 ** 2
  t79 = 0.1e1 / t78
  t80 = t77 * t79
  t83 = params.cx_local[3]
  t84 = t72 * s0
  t85 = t83 * t84
  t86 = t74 ** 2
  t87 = 0.1e1 / t86
  t88 = t78 * t66
  t89 = 0.1e1 / t88
  t90 = t87 * t89
  t93 = params.cx_nlocal[0]
  t94 = params.cx_nlocal[1]
  t95 = t94 * s0
  t98 = params.cx_nlocal[2]
  t99 = t98 * t72
  t102 = params.cx_nlocal[3]
  t103 = t102 * t84
  t106 = t93 + 0.4e-2 * t95 * t68 + 0.16e-4 * t99 * t80 + 0.64e-7 * t103 * t90
  t107 = 6 ** (0.1e1 / 0.3e1)
  t108 = t107 ** 2
  t109 = jnp.pi ** 2
  t110 = t109 ** (0.1e1 / 0.3e1)
  t111 = t110 ** 2
  t113 = 0.3e1 / 0.10e2 * t108 * t111
  t116 = tau0 / t61 / r0
  t117 = t113 - t116
  t118 = t113 + t116
  t119 = 0.1e1 / t118
  t121 = t117 ** 2
  t122 = t121 * t117
  t123 = t118 ** 2
  t124 = t123 * t118
  t125 = 0.1e1 / t124
  t128 = t121 ** 2
  t129 = t128 * t117
  t130 = t123 ** 2
  t132 = 0.1e1 / t130 / t118
  t134 = t117 * t119 - 0.2e1 * t122 * t125 + t129 * t132
  t136 = t56 + 0.4e-2 * t58 * t68 + 0.16e-4 * t73 * t80 + 0.64e-7 * t85 * t90 + t106 * t134
  t145 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t146 = t54 ** 2
  t147 = 0.1e1 / t146
  t148 = t145 * t147
  t152 = t145 * t54
  t153 = t59 * r0
  t155 = 0.1e1 / t61 / t153
  t156 = t155 * t67
  t159 = t57 * t72
  t160 = t74 * t59
  t162 = 0.1e1 / t60 / t160
  t163 = t162 * t79
  t168 = t71 * t84
  t169 = t86 * r0
  t170 = 0.1e1 / t169
  t171 = t170 * t89
  t176 = t72 ** 2
  t177 = t83 * t176
  t178 = t86 * t153
  t181 = t78 ** 2
  t182 = 0.1e1 / t181
  t183 = 0.1e1 / t61 / t178 * t182
  t188 = t94 * t72
  t193 = t98 * t84
  t198 = t102 * t176
  t201 = -0.10666666666666666666666666666666666666666666666667e-1 * t95 * t156 + 0.42666666666666666666666666666666666666666666666668e-4 * t188 * t163 - 0.85333333333333333333333333333333333333333333333333e-4 * t99 * t163 + 0.34133333333333333333333333333333333333333333333334e-6 * t193 * t171 - 0.512e-6 * t103 * t171 + 0.20480000000000000000000000000000000000000000000001e-8 * t198 * t183
  t203 = tau0 * t63
  t206 = 0.1e1 / t123
  t207 = t117 * t206
  t210 = t121 * t125
  t213 = 0.1e1 / t130
  t214 = t122 * t213
  t217 = t128 * t132
  t221 = 0.1e1 / t130 / t123
  t222 = t129 * t221
  t225 = 0.5e1 / 0.3e1 * t203 * t119 + 0.5e1 / 0.3e1 * t207 * t203 - 0.10e2 * t210 * t203 - 0.10e2 * t214 * t203 + 0.25e2 / 0.3e1 * t217 * t203 + 0.25e2 / 0.3e1 * t222 * t203
  t227 = -0.10666666666666666666666666666666666666666666666667e-1 * t58 * t156 + 0.42666666666666666666666666666666666666666666666668e-4 * t159 * t163 - 0.85333333333333333333333333333333333333333333333333e-4 * t73 * t163 + 0.34133333333333333333333333333333333333333333333334e-6 * t168 * t171 - 0.512e-6 * t85 * t171 + 0.20480000000000000000000000000000000000000000000001e-8 * t177 * t183 + t201 * t134 + t106 * t225
  t233 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t235 = 0.1e1 / t146 / t6
  t236 = t233 * t235
  t240 = t233 * t147
  t244 = t233 * t54
  t246 = 0.1e1 / t61 / t74
  t247 = t246 * t67
  t250 = t74 * t153
  t252 = 0.1e1 / t60 / t250
  t253 = t252 * t79
  t256 = t57 * t84
  t257 = t86 * t59
  t259 = 0.1e1 / t257 * t89
  t266 = t71 * t176
  t267 = t86 * t74
  t270 = 0.1e1 / t61 / t267 * t182
  t277 = t176 * s0
  t278 = t83 * t277
  t283 = 0.1e1 / t181 / t66
  t284 = 0.1e1 / t60 / t86 / t250 * t283
  t291 = t94 * t84
  t298 = t98 * t176
  t305 = t102 * t277
  t308 = 0.39111111111111111111111111111111111111111111111112e-1 * t95 * t247 - 0.38400000000000000000000000000000000000000000000001e-3 * t188 * t253 + 0.91022222222222222222222222222222222222222222222228e-6 * t291 * t259 + 0.54044444444444444444444444444444444444444444444444e-3 * t99 * t253 - 0.48924444444444444444444444444444444444444444444446e-5 * t193 * t259 + 0.10922666666666666666666666666666666666666666666667e-7 * t298 * t270 + 0.4608e-5 * t103 * t259 - 0.40277333333333333333333333333333333333333333333336e-7 * t198 * t270 + 0.87381333333333333333333333333333333333333333333340e-10 * t305 * t284
  t312 = tau0 * t155
  t315 = tau0 ** 2
  t316 = t315 * t77
  t319 = t117 * t125
  t324 = t121 * t213
  t329 = t122 * t132
  t334 = t128 * t221
  t340 = 0.1e1 / t130 / t124
  t341 = t129 * t340
  t346 = -0.40e2 / 0.9e1 * t312 * t119 + 0.50e2 / 0.9e1 * t316 * t206 - 0.250e3 / 0.9e1 * t319 * t316 - 0.40e2 / 0.9e1 * t207 * t312 - 0.100e3 * t324 * t316 + 0.80e2 / 0.3e1 * t210 * t312 - 0.100e3 / 0.9e1 * t329 * t316 + 0.80e2 / 0.3e1 * t214 * t312 + 0.1250e4 / 0.9e1 * t334 * t316 - 0.200e3 / 0.9e1 * t217 * t312 + 0.250e3 / 0.3e1 * t341 * t316 - 0.200e3 / 0.9e1 * t222 * t312
  t348 = 0.39111111111111111111111111111111111111111111111112e-1 * t58 * t247 - 0.38400000000000000000000000000000000000000000000001e-3 * t159 * t253 + 0.91022222222222222222222222222222222222222222222228e-6 * t256 * t259 + 0.54044444444444444444444444444444444444444444444444e-3 * t73 * t253 - 0.48924444444444444444444444444444444444444444444446e-5 * t168 * t259 + 0.10922666666666666666666666666666666666666666666667e-7 * t266 * t270 + 0.4608e-5 * t85 * t259 - 0.40277333333333333333333333333333333333333333333336e-7 * t177 * t270 + 0.87381333333333333333333333333333333333333333333340e-10 * t278 * t284 + t308 * t134 + 0.2e1 * t201 * t225 + t106 * t346
  t352 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t353 = t352 * f.p.zeta_threshold
  t355 = f.my_piecewise3(t20, t353, t21 * t19)
  t357 = 0.1e1 / t146 / t25
  t358 = t355 * t357
  t362 = t355 * t235
  t366 = t355 * t147
  t370 = t355 * t54
  t372 = 0.1e1 / t61 / t75
  t373 = t372 * t67
  t378 = 0.1e1 / t60 / t86 * t79
  t382 = 0.1e1 / t178 * t89
  t385 = t57 * t176
  t389 = 0.1e1 / t61 / t86 / t75 * t182
  t398 = t71 * t277
  t399 = t86 ** 2
  t402 = 0.1e1 / t60 / t399 * t283
  t411 = t176 * t72
  t412 = t83 * t411
  t416 = 0.1e1 / t181 / t78
  t417 = 0.1e1 / t399 / t153 * t416
  t426 = t94 * t176
  t435 = t98 * t277
  t444 = t102 * t411
  t447 = -0.18251851851851851851851851851851851851851851851852e0 * t95 * t373 + 0.32331851851851851851851851851851851851851851851853e-2 * t188 * t378 - 0.17294222222222222222222222222222222222222222222223e-4 * t291 * t382 + 0.29127111111111111111111111111111111111111111111114e-7 * t426 * t389 - 0.39632592592592592592592592592592592592592592592592e-2 * t99 * t378 + 0.60453925925925925925925925925925925925925925925928e-4 * t193 * t382 - 0.29491200000000000000000000000000000000000000000001e-6 * t298 * t389 + 0.46603377777777777777777777777777777777777777777781e-9 * t435 * t402 - 0.46080e-4 * t103 * t382 + 0.65763555555555555555555555555555555555555555555559e-6 * t198 * t389 - 0.30583466666666666666666666666666666666666666666669e-8 * t305 * t402 + 0.46603377777777777777777777777777777777777777777783e-11 * t444 * t417
  t453 = t130 ** 2
  t454 = 0.1e1 / t453
  t455 = t129 * t454
  t456 = t315 * tau0
  t457 = t456 * t87
  t460 = tau0 * t246
  t463 = t117 * t213
  t466 = t121 * t132
  t469 = t122 * t221
  t472 = t128 * t340
  t475 = t315 * t162
  t500 = 0.8750e4 / 0.9e1 * t455 * t457 + 0.440e3 / 0.27e2 * t460 * t119 - 0.4250e4 / 0.9e1 * t463 * t457 - 0.6500e4 / 0.9e1 * t466 * t457 + 0.2500e4 / 0.3e1 * t469 * t457 + 0.6250e4 / 0.3e1 * t472 * t457 - 0.400e3 / 0.9e1 * t475 * t206 - 0.250e3 / 0.9e1 * t457 * t125 + 0.2000e4 / 0.9e1 * t319 * t475 + 0.440e3 / 0.27e2 * t207 * t460 + 0.800e3 * t324 * t475 - 0.880e3 / 0.9e1 * t210 * t460 + 0.800e3 / 0.9e1 * t329 * t475 - 0.880e3 / 0.9e1 * t214 * t460 - 0.10000e5 / 0.9e1 * t334 * t475 + 0.2200e4 / 0.27e2 * t217 * t460 - 0.2000e4 / 0.3e1 * t341 * t475 + 0.2200e4 / 0.27e2 * t222 * t460
  t502 = -0.18251851851851851851851851851851851851851851851852e0 * t58 * t373 + 0.32331851851851851851851851851851851851851851851853e-2 * t159 * t378 - 0.17294222222222222222222222222222222222222222222223e-4 * t256 * t382 + 0.29127111111111111111111111111111111111111111111114e-7 * t385 * t389 - 0.39632592592592592592592592592592592592592592592592e-2 * t73 * t378 + 0.60453925925925925925925925925925925925925925925928e-4 * t168 * t382 - 0.29491200000000000000000000000000000000000000000001e-6 * t266 * t389 + 0.46603377777777777777777777777777777777777777777781e-9 * t398 * t402 - 0.46080e-4 * t85 * t382 + 0.65763555555555555555555555555555555555555555555559e-6 * t177 * t389 - 0.30583466666666666666666666666666666666666666666669e-8 * t278 * t402 + 0.46603377777777777777777777777777777777777777777783e-11 * t412 * t417 + t447 * t134 + 0.3e1 * t308 * t225 + 0.3e1 * t201 * t346 + t106 * t500
  t507 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t136 - 0.3e1 / 0.8e1 * t5 * t148 * t136 - 0.9e1 / 0.8e1 * t5 * t152 * t227 + t5 * t236 * t136 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t240 * t227 - 0.9e1 / 0.8e1 * t5 * t244 * t348 - 0.5e1 / 0.36e2 * t5 * t358 * t136 + t5 * t362 * t227 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t366 * t348 - 0.3e1 / 0.8e1 * t5 * t370 * t502)
  t509 = r1 <= f.p.dens_threshold
  t510 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t511 = 0.1e1 + t510
  t512 = t511 <= f.p.zeta_threshold
  t513 = t511 ** (0.1e1 / 0.3e1)
  t514 = t513 ** 2
  t516 = 0.1e1 / t514 / t511
  t518 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t519 = t518 ** 2
  t523 = 0.1e1 / t514
  t524 = t523 * t518
  t526 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t530 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t534 = f.my_piecewise3(t512, 0, -0.8e1 / 0.27e2 * t516 * t519 * t518 + 0.4e1 / 0.3e1 * t524 * t526 + 0.4e1 / 0.3e1 * t513 * t530)
  t537 = r1 ** 2
  t538 = r1 ** (0.1e1 / 0.3e1)
  t539 = t538 ** 2
  t541 = 0.1e1 / t539 / t537
  t544 = 0.1e1 + 0.4e-2 * s2 * t541
  t546 = t541 / t544
  t549 = s2 ** 2
  t551 = t537 ** 2
  t555 = t544 ** 2
  t557 = 0.1e1 / t538 / t551 / r1 / t555
  t560 = t549 * s2
  t562 = t551 ** 2
  t566 = 0.1e1 / t562 / t555 / t544
  t581 = tau1 / t539 / r1
  t582 = t113 - t581
  t583 = t113 + t581
  t586 = t582 ** 2
  t588 = t583 ** 2
  t593 = t586 ** 2
  t595 = t588 ** 2
  t601 = t56 + 0.4e-2 * t57 * s2 * t546 + 0.16e-4 * t71 * t549 * t557 + 0.64e-7 * t83 * t560 * t566 + (t93 + 0.4e-2 * t94 * s2 * t546 + 0.16e-4 * t98 * t549 * t557 + 0.64e-7 * t102 * t560 * t566) * (t582 / t583 - 0.2e1 * t586 * t582 / t588 / t583 + t593 * t582 / t595 / t583)
  t610 = f.my_piecewise3(t512, 0, 0.4e1 / 0.9e1 * t523 * t519 + 0.4e1 / 0.3e1 * t513 * t526)
  t617 = f.my_piecewise3(t512, 0, 0.4e1 / 0.3e1 * t513 * t518)
  t623 = f.my_piecewise3(t512, t353, t513 * t511)
  t629 = f.my_piecewise3(t509, 0, -0.3e1 / 0.8e1 * t5 * t534 * t54 * t601 - 0.3e1 / 0.8e1 * t5 * t610 * t147 * t601 + t5 * t617 * t235 * t601 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t623 * t357 * t601)
  t634 = t19 ** 2
  t637 = t30 ** 2
  t643 = t41 ** 2
  t652 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t653 = f.my_piecewise5(t10, 0, t14, 0, t652)
  t657 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t634 * t637 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t643 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t653)
  t666 = 0.1e1 / t146 / t36
  t677 = 0.1e1 / t60 / t169 * t79
  t681 = 0.1e1 / t267 * t89
  t687 = 0.1e1 / t61 / t86 / t160 * t182
  t694 = 0.1e1 / t60 / t399 / r0 * t283
  t706 = 0.1e1 / t399 / t74 * t416
  t715 = t176 * t84
  t722 = 0.1e1 / t61 / t399 / t160 / t181 / t88
  t729 = 0.1e1 / t61 / t160 * t67
  t734 = t315 * t252
  t737 = tau0 * t372
  t753 = t315 ** 2
  t756 = t753 / t61 / t257
  t769 = -0.54400e5 / 0.9e1 * t324 * t734 + 0.12320e5 / 0.27e2 * t210 * t737 - 0.54400e5 / 0.81e2 * t329 * t734 + 0.12320e5 / 0.27e2 * t214 * t737 + 0.680000e6 / 0.81e2 * t334 * t734 - 0.30800e5 / 0.81e2 * t217 * t737 + 0.136000e6 / 0.27e2 * t341 * t734 - 0.30800e5 / 0.81e2 * t222 * t737 + 0.875000e6 / 0.27e2 * t128 * t454 * t756 + 0.350000e6 / 0.27e2 * t129 / t453 / t118 * t756 - 0.6160e4 / 0.81e2 * t737 * t119 - 0.50000e5 / 0.9e1 * t117 * t132 * t756
  t776 = t456 * t170
  t797 = -0.50000e5 / 0.27e2 * t121 * t221 * t756 + 0.200000e6 / 0.9e1 * t122 * t340 * t756 - 0.140000e6 / 0.9e1 * t455 * t776 + 0.68000e5 / 0.9e1 * t463 * t776 + 0.104000e6 / 0.9e1 * t466 * t776 - 0.40000e5 / 0.3e1 * t469 * t776 - 0.100000e6 / 0.3e1 * t472 * t776 - 0.136000e6 / 0.81e2 * t319 * t734 - 0.6160e4 / 0.81e2 * t207 * t737 + 0.27200e5 / 0.81e2 * t734 * t206 - 0.25000e5 / 0.27e2 * t756 * t213 + 0.4000e4 / 0.9e1 * t776 * t125
  t833 = 0.10342716049382716049382716049382716049382716049383e1 * t95 * t729 - 0.28890074074074074074074074074074074074074074074075e-1 * t188 * t677 + 0.25921106172839506172839506172839506172839506172840e-3 * t291 * t681 - 0.95148562962962962962962962962962962962962962962971e-6 * t426 * t687 + 0.12427567407407407407407407407407407407407407407409e-8 * t94 * t277 * t694 + 0.33027160493827160493827160493827160493827160493827e-1 * t99 * t677 - 0.74954271604938271604938271604938271604938271604941e-3 * t193 * t681 + 0.59649896296296296296296296296296296296296296296299e-5 * t298 * t687 - 0.20194797037037037037037037037037037037037037037038e-7 * t435 * t694 + 0.24855134814814814814814814814814814814814814814817e-10 * t98 * t411 * t706 + 0.506880e-3 * t103 * t681 - 0.10462245925925925925925925925925925925925925925926e-4 * t198 * t687 + 0.78012112592592592592592592592592592592592592592598e-7 * t305 * t694 - 0.25165824000000000000000000000000000000000000000003e-9 * t444 * t706 + 0.29826161777777777777777777777777777777777777777782e-12 * t102 * t715 * t722
  t841 = -0.28890074074074074074074074074074074074074074074075e-1 * t159 * t677 + 0.25921106172839506172839506172839506172839506172840e-3 * t256 * t681 - 0.95148562962962962962962962962962962962962962962971e-6 * t385 * t687 + 0.12427567407407407407407407407407407407407407407409e-8 * t57 * t277 * t694 - 0.74954271604938271604938271604938271604938271604941e-3 * t168 * t681 + 0.59649896296296296296296296296296296296296296296299e-5 * t266 * t687 - 0.20194797037037037037037037037037037037037037037038e-7 * t398 * t694 + 0.24855134814814814814814814814814814814814814814817e-10 * t71 * t411 * t706 - 0.10462245925925925925925925925925925925925925925926e-4 * t177 * t687 + 0.78012112592592592592592592592592592592592592592598e-7 * t278 * t694 - 0.25165824000000000000000000000000000000000000000003e-9 * t412 * t706 + 0.29826161777777777777777777777777777777777777777782e-12 * t83 * t715 * t722 + 0.506880e-3 * t85 * t681 + 0.10342716049382716049382716049382716049382716049383e1 * t58 * t729 + 0.33027160493827160493827160493827160493827160493827e-1 * t73 * t677 + t106 * (t769 + t797) + t833 * t134 + 0.4e1 * t447 * t225 + 0.6e1 * t308 * t346 + 0.4e1 * t201 * t500
  t873 = -0.3e1 / 0.2e1 * t5 * t148 * t227 - 0.3e1 / 0.8e1 * t5 * t657 * t54 * t136 - 0.3e1 / 0.2e1 * t5 * t55 * t227 + 0.10e2 / 0.27e2 * t5 * t355 * t666 * t136 - 0.5e1 / 0.9e1 * t5 * t233 * t357 * t136 - 0.3e1 / 0.8e1 * t5 * t370 * t841 - t5 * t366 * t502 / 0.2e1 + t5 * t362 * t348 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t358 * t227 - 0.3e1 / 0.2e1 * t5 * t244 * t502 - 0.3e1 / 0.2e1 * t5 * t240 * t348 + t5 * t236 * t227 - 0.9e1 / 0.4e1 * t5 * t152 * t348 - t5 * t53 * t147 * t136 / 0.2e1 + t5 * t145 * t235 * t136 / 0.2e1
  t874 = f.my_piecewise3(t1, 0, t873)
  t875 = t511 ** 2
  t878 = t519 ** 2
  t884 = t526 ** 2
  t890 = f.my_piecewise5(t14, 0, t10, 0, -t652)
  t894 = f.my_piecewise3(t512, 0, 0.40e2 / 0.81e2 / t514 / t875 * t878 - 0.16e2 / 0.9e1 * t516 * t519 * t526 + 0.4e1 / 0.3e1 * t523 * t884 + 0.16e2 / 0.9e1 * t524 * t530 + 0.4e1 / 0.3e1 * t513 * t890)
  t916 = f.my_piecewise3(t509, 0, -0.3e1 / 0.8e1 * t5 * t894 * t54 * t601 - t5 * t534 * t147 * t601 / 0.2e1 + t5 * t610 * t235 * t601 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t617 * t357 * t601 + 0.10e2 / 0.27e2 * t5 * t623 * t666 * t601)
  d1111 = 0.4e1 * t507 + 0.4e1 * t629 + t6 * (t874 + t916)

  res = {'v4rho4': d1111}
  return res
