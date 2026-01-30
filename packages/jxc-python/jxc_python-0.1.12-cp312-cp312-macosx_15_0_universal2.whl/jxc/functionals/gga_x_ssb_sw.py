"""Generated from gga_x_ssb_sw.mpl."""

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
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))
  params_D_raw = params.D
  if isinstance(params_D_raw, (str, bytes, dict)):
    params_D = params_D_raw
  else:
    try:
      params_D_seq = list(params_D_raw)
    except TypeError:
      params_D = params_D_raw
    else:
      params_D_seq = np.asarray(params_D_seq, dtype=np.float64)
      params_D = np.concatenate((np.array([np.nan], dtype=np.float64), params_D_seq))
  params_E_raw = params.E
  if isinstance(params_E_raw, (str, bytes, dict)):
    params_E = params_E_raw
  else:
    try:
      params_E_seq = list(params_E_raw)
    except TypeError:
      params_E = params_E_raw
    else:
      params_E_seq = np.asarray(params_E_seq, dtype=np.float64)
      params_E = np.concatenate((np.array([np.nan], dtype=np.float64), params_E_seq))

  ssb_sw_f0 = lambda s: params_A + params_B * s ** 2 / (1 + params_C * s ** 2) - params_D * s ** 2 / (1 + params_E * s ** 4)

  ssb_sw_f = lambda x: ssb_sw_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ssb_sw_f, rs, zeta, xs0, xs1)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
      f.xt(r0, r1, s0, s1, s2),
      f.xs0(r0, r1, s0, s2),
      f.xs1(r0, r1, s0, s2),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))
  params_D_raw = params.D
  if isinstance(params_D_raw, (str, bytes, dict)):
    params_D = params_D_raw
  else:
    try:
      params_D_seq = list(params_D_raw)
    except TypeError:
      params_D = params_D_raw
    else:
      params_D_seq = np.asarray(params_D_seq, dtype=np.float64)
      params_D = np.concatenate((np.array([np.nan], dtype=np.float64), params_D_seq))
  params_E_raw = params.E
  if isinstance(params_E_raw, (str, bytes, dict)):
    params_E = params_E_raw
  else:
    try:
      params_E_seq = list(params_E_raw)
    except TypeError:
      params_E = params_E_raw
    else:
      params_E_seq = np.asarray(params_E_seq, dtype=np.float64)
      params_E = np.concatenate((np.array([np.nan], dtype=np.float64), params_E_seq))

  ssb_sw_f0 = lambda s: params_A + params_B * s ** 2 / (1 + params_C * s ** 2) - params_D * s ** 2 / (1 + params_E * s ** 4)

  ssb_sw_f = lambda x: ssb_sw_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ssb_sw_f, rs, zeta, xs0, xs1)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
      f.xt(r0 / 2, r0 / 2, s0 / 4, s0 / 4, s0 / 4),
      f.xs0(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.xs1(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))
  params_D_raw = params.D
  if isinstance(params_D_raw, (str, bytes, dict)):
    params_D = params_D_raw
  else:
    try:
      params_D_seq = list(params_D_raw)
    except TypeError:
      params_D = params_D_raw
    else:
      params_D_seq = np.asarray(params_D_seq, dtype=np.float64)
      params_D = np.concatenate((np.array([np.nan], dtype=np.float64), params_D_seq))
  params_E_raw = params.E
  if isinstance(params_E_raw, (str, bytes, dict)):
    params_E = params_E_raw
  else:
    try:
      params_E_seq = list(params_E_raw)
    except TypeError:
      params_E = params_E_raw
    else:
      params_E_seq = np.asarray(params_E_seq, dtype=np.float64)
      params_E = np.concatenate((np.array([np.nan], dtype=np.float64), params_E_seq))

  ssb_sw_f0 = lambda s: params_A + params_B * s ** 2 / (1 + params_C * s ** 2) - params_D * s ** 2 / (1 + params_E * s ** 4)

  ssb_sw_f = lambda x: ssb_sw_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ssb_sw_f, rs, zeta, xs0, xs1)

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
  t29 = params.B * t28
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
  t41 = params.C * t28
  t46 = 0.1e1 + t41 * t33 * s0 * t39 / 0.24e2
  t47 = 0.1e1 / t46
  t51 = params.D * t28
  t52 = t51 * t33
  t53 = t28 ** 2
  t54 = params.E * t53
  t56 = 0.1e1 / t31 / t30
  t57 = s0 ** 2
  t59 = t35 ** 2
  t62 = 0.1e1 / t36 / t59 / r0
  t66 = 0.1e1 + t54 * t56 * t57 * t62 / 0.576e3
  t67 = 0.1e1 / t66
  t71 = params.A + t34 * t40 * t47 / 0.24e2 - t52 * t40 * t67 / 0.24e2
  t75 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t71)
  t76 = r1 <= f.p.dens_threshold
  t77 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t78 = 0.1e1 + t77
  t79 = t78 <= f.p.zeta_threshold
  t80 = t78 ** (0.1e1 / 0.3e1)
  t82 = f.my_piecewise3(t79, t22, t80 * t78)
  t83 = t82 * t26
  t84 = r1 ** 2
  t85 = r1 ** (0.1e1 / 0.3e1)
  t86 = t85 ** 2
  t88 = 0.1e1 / t86 / t84
  t89 = s2 * t88
  t94 = 0.1e1 + t41 * t33 * s2 * t88 / 0.24e2
  t95 = 0.1e1 / t94
  t99 = s2 ** 2
  t101 = t84 ** 2
  t104 = 0.1e1 / t85 / t101 / r1
  t108 = 0.1e1 + t54 * t56 * t99 * t104 / 0.576e3
  t109 = 0.1e1 / t108
  t113 = params.A + t34 * t89 * t95 / 0.24e2 - t52 * t89 * t109 / 0.24e2
  t117 = f.my_piecewise3(t76, 0, -0.3e1 / 0.8e1 * t5 * t83 * t113)
  t118 = t6 ** 2
  t120 = t16 / t118
  t121 = t7 - t120
  t122 = f.my_piecewise5(t10, 0, t14, 0, t121)
  t125 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t122)
  t130 = t26 ** 2
  t131 = 0.1e1 / t130
  t135 = t5 * t25 * t131 * t71 / 0.8e1
  t139 = s0 / t37 / t35 / r0
  t144 = params.B * t53 * t56
  t149 = t46 ** 2
  t151 = 0.1e1 / t149 * params.C
  t158 = t30 ** 2
  t160 = params.D / t158
  t163 = t59 ** 2
  t166 = t66 ** 2
  t167 = 0.1e1 / t166
  t177 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t125 * t26 * t71 - t135 - 0.3e1 / 0.8e1 * t5 * t27 * (-t34 * t139 * t47 / 0.9e1 + t144 * t57 / t36 / t59 / t35 * t151 / 0.216e3 + t52 * t139 * t67 / 0.9e1 - t160 * t57 * s0 / t163 / r0 * t167 * params.E / 0.432e3))
  t179 = f.my_piecewise5(t14, 0, t10, 0, -t121)
  t182 = f.my_piecewise3(t79, 0, 0.4e1 / 0.3e1 * t80 * t179)
  t190 = t5 * t82 * t131 * t113 / 0.8e1
  t192 = f.my_piecewise3(t76, 0, -0.3e1 / 0.8e1 * t5 * t182 * t26 * t113 - t190)
  vrho_0_ = t75 + t117 + t6 * (t177 + t192)
  t195 = -t7 - t120
  t196 = f.my_piecewise5(t10, 0, t14, 0, t195)
  t199 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t196)
  t205 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t199 * t26 * t71 - t135)
  t207 = f.my_piecewise5(t14, 0, t10, 0, -t195)
  t210 = f.my_piecewise3(t79, 0, 0.4e1 / 0.3e1 * t80 * t207)
  t218 = s2 / t86 / t84 / r1
  t226 = t94 ** 2
  t228 = 0.1e1 / t226 * params.C
  t237 = t101 ** 2
  t240 = t108 ** 2
  t241 = 0.1e1 / t240
  t251 = f.my_piecewise3(t76, 0, -0.3e1 / 0.8e1 * t5 * t210 * t26 * t113 - t190 - 0.3e1 / 0.8e1 * t5 * t83 * (-t34 * t218 * t95 / 0.9e1 + t144 * t99 / t85 / t101 / t84 * t228 / 0.216e3 + t52 * t218 * t109 / 0.9e1 - t160 * t99 * s2 / t237 / r1 * t241 * params.E / 0.432e3))
  vrho_1_ = t75 + t117 + t6 * (t205 + t251)
  t254 = t33 * t39
  t275 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t29 * t254 * t47 / 0.24e2 - t144 * s0 * t62 * t151 / 0.576e3 - t51 * t254 * t67 / 0.24e2 + t160 * t57 / t163 * t167 * params.E / 0.1152e4))
  vsigma_0_ = t6 * t275
  vsigma_1_ = 0.0e0
  t276 = t33 * t88
  t297 = f.my_piecewise3(t76, 0, -0.3e1 / 0.8e1 * t5 * t83 * (t29 * t276 * t95 / 0.24e2 - t144 * s2 * t104 * t228 / 0.576e3 - t51 * t276 * t109 / 0.24e2 + t160 * t99 / t237 * t241 * params.E / 0.1152e4))
  vsigma_2_ = t6 * t297
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  vsigma_0_ = _b(vsigma_0_)
  vsigma_1_ = _b(vsigma_1_)
  vsigma_2_ = _b(vsigma_2_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1), 'vsigma': jnp.stack([vsigma_0_, vsigma_1_, vsigma_2_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))
  params_D_raw = params.D
  if isinstance(params_D_raw, (str, bytes, dict)):
    params_D = params_D_raw
  else:
    try:
      params_D_seq = list(params_D_raw)
    except TypeError:
      params_D = params_D_raw
    else:
      params_D_seq = np.asarray(params_D_seq, dtype=np.float64)
      params_D = np.concatenate((np.array([np.nan], dtype=np.float64), params_D_seq))
  params_E_raw = params.E
  if isinstance(params_E_raw, (str, bytes, dict)):
    params_E = params_E_raw
  else:
    try:
      params_E_seq = list(params_E_raw)
    except TypeError:
      params_E = params_E_raw
    else:
      params_E_seq = np.asarray(params_E_seq, dtype=np.float64)
      params_E = np.concatenate((np.array([np.nan], dtype=np.float64), params_E_seq))

  ssb_sw_f0 = lambda s: params_A + params_B * s ** 2 / (1 + params_C * s ** 2) - params_D * s ** 2 / (1 + params_E * s ** 4)

  ssb_sw_f = lambda x: ssb_sw_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ssb_sw_f, rs, zeta, xs0, xs1)

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
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t26 = params.B * t20 * t25
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t18 ** 2
  t33 = 0.1e1 / t31 / t30
  t39 = 0.1e1 + params.C * t20 * t25 * t29 * t33 / 0.24e2
  t40 = 0.1e1 / t39
  t46 = params.D * t20 * t25
  t47 = t20 ** 2
  t50 = 0.1e1 / t23 / t22
  t52 = s0 ** 2
  t54 = t30 ** 2
  t57 = 0.1e1 / t18 / t54 / r0
  t61 = 0.1e1 + params.E * t47 * t50 * t52 * t27 * t57 / 0.288e3
  t62 = 0.1e1 / t61
  t67 = params.A + t26 * t29 * t33 * t40 / 0.24e2 - t46 * t29 * t33 * t62 / 0.24e2
  t71 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t67)
  t79 = 0.1e1 / t31 / t30 / r0
  t84 = params.B * t47
  t91 = t39 ** 2
  t93 = 0.1e1 / t91 * params.C
  t101 = t22 ** 2
  t103 = params.D / t101
  t106 = t54 ** 2
  t109 = t61 ** 2
  t110 = 0.1e1 / t109
  t120 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t67 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t26 * t29 * t79 * t40 / 0.9e1 + t84 * t50 * t52 * t27 / t18 / t54 / t30 * t93 / 0.108e3 + t46 * t29 * t79 * t62 / 0.9e1 - t103 * t52 * s0 / t106 / r0 * t110 * params.E / 0.108e3))
  vrho_0_ = 0.2e1 * r0 * t120 + 0.2e1 * t71
  t123 = t28 * t33
  t146 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t26 * t123 * t40 / 0.24e2 - t84 * t50 * s0 * t27 * t57 * t93 / 0.288e3 - t46 * t123 * t62 / 0.24e2 + t103 * t52 / t106 * t110 * params.E / 0.288e3))
  vsigma_0_ = 0.2e1 * r0 * t146
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
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
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = params.B * t22 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t40 = 0.1e1 + params.C * t22 * t27 * t31 * t34 / 0.24e2
  t41 = 0.1e1 / t40
  t47 = params.D * t22 * t27
  t48 = t22 ** 2
  t51 = 0.1e1 / t25 / t24
  t53 = s0 ** 2
  t55 = t32 ** 2
  t56 = t55 * r0
  t58 = 0.1e1 / t18 / t56
  t62 = 0.1e1 + params.E * t48 * t51 * t53 * t29 * t58 / 0.288e3
  t63 = 0.1e1 / t62
  t68 = params.A + t28 * t31 * t34 * t41 / 0.24e2 - t47 * t31 * t34 * t63 / 0.24e2
  t72 = t17 * t18
  t73 = t32 * r0
  t75 = 0.1e1 / t19 / t73
  t80 = params.B * t48
  t82 = t80 * t51 * t53
  t83 = t55 * t32
  t85 = 0.1e1 / t18 / t83
  t87 = t40 ** 2
  t88 = 0.1e1 / t87
  t89 = t88 * params.C
  t97 = t24 ** 2
  t98 = 0.1e1 / t97
  t99 = params.D * t98
  t100 = t53 * s0
  t101 = t99 * t100
  t102 = t55 ** 2
  t104 = 0.1e1 / t102 / r0
  t105 = t62 ** 2
  t106 = 0.1e1 / t105
  t111 = -t28 * t31 * t75 * t41 / 0.9e1 + t82 * t29 * t85 * t89 / 0.108e3 + t47 * t31 * t75 * t63 / 0.9e1 - t101 * t104 * t106 * params.E / 0.108e3
  t116 = f.my_piecewise3(t2, 0, -t6 * t21 * t68 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t72 * t111)
  t128 = 0.1e1 / t19 / t55
  t133 = t55 * t73
  t140 = params.B * t98
  t143 = 0.1e1 / t102 / t32
  t145 = 0.1e1 / t87 / t40
  t147 = params.C ** 2
  t159 = t53 ** 2
  t168 = params.E ** 2
  t172 = 0.1e1 / t105 / t62 * t168 * t48 * t51 * t29
  t180 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t68 / 0.12e2 - t6 * t21 * t111 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t72 * (0.11e2 / 0.27e2 * t28 * t31 * t128 * t41 - t82 * t29 / t18 / t133 * t89 / 0.12e2 + 0.2e1 / 0.81e2 * t140 * t100 * t143 * t145 * t147 - 0.11e2 / 0.27e2 * t47 * t31 * t128 * t63 + 0.35e2 / 0.324e3 * t101 * t143 * t106 * params.E - t99 * t159 * s0 / t18 / t102 / t133 * t172 / 0.2916e4))
  v2rho2_0_ = 0.2e1 * r0 * t180 + 0.4e1 * t116
  t183 = t30 * t34
  t190 = t29 * t58 * t89
  t197 = 0.1e1 / t102
  t202 = t28 * t183 * t41 / 0.24e2 - t80 * t51 * s0 * t190 / 0.288e3 - t47 * t183 * t63 / 0.24e2 + t99 * t53 * t197 * t106 * params.E / 0.288e3
  t206 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t72 * t202)
  t210 = t30 * t75
  t230 = t106 * params.E
  t246 = f.my_piecewise3(t2, 0, -t6 * t21 * t202 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t72 * (-t28 * t210 * t41 / 0.9e1 + t80 * t51 * t29 * t85 * t88 * params.C * s0 / 0.36e2 - t140 * t53 * t104 * t145 * t147 / 0.108e3 + t47 * t210 * t63 / 0.9e1 - t99 * t104 * t230 * t53 / 0.27e2 + t99 * t159 / t18 / t102 / t83 * t172 / 0.7776e4))
  v2rhosigma_0_ = 0.2e1 * r0 * t246 + 0.2e1 * t206
  t272 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t72 * (-t80 * t51 * t190 / 0.144e3 + t140 * s0 * t197 * t145 * t147 / 0.288e3 + t99 * t197 * t230 * s0 / 0.96e2 - t99 * t100 / t18 / t102 / t56 * t172 / 0.20736e5))
  v2sigma2_0_ = 0.2e1 * r0 * t272
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
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
  t22 = t17 / t19 / r0
  t23 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = params.B * t23 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t41 = 0.1e1 + params.C * t23 * t28 * t32 * t35 / 0.24e2
  t42 = 0.1e1 / t41
  t48 = params.D * t23 * t28
  t49 = t23 ** 2
  t52 = 0.1e1 / t26 / t25
  t54 = s0 ** 2
  t56 = t33 ** 2
  t57 = t56 * r0
  t63 = 0.1e1 + params.E * t49 * t52 * t54 * t30 / t18 / t57 / 0.288e3
  t64 = 0.1e1 / t63
  t69 = params.A + t29 * t32 * t35 * t42 / 0.24e2 - t48 * t32 * t35 * t64 / 0.24e2
  t74 = t17 / t19
  t75 = t33 * r0
  t77 = 0.1e1 / t19 / t75
  t84 = params.B * t49 * t52 * t54
  t89 = t41 ** 2
  t91 = 0.1e1 / t89 * params.C
  t99 = t25 ** 2
  t100 = 0.1e1 / t99
  t101 = params.D * t100
  t102 = t54 * s0
  t103 = t101 * t102
  t104 = t56 ** 2
  t107 = t63 ** 2
  t108 = 0.1e1 / t107
  t113 = -t29 * t32 * t77 * t42 / 0.9e1 + t84 * t30 / t18 / t56 / t33 * t91 / 0.108e3 + t48 * t32 * t77 * t64 / 0.9e1 - t103 / t104 / r0 * t108 * params.E / 0.108e3
  t117 = t17 * t18
  t119 = 0.1e1 / t19 / t56
  t124 = t56 * t75
  t131 = params.B * t100
  t132 = t131 * t102
  t134 = 0.1e1 / t104 / t33
  t136 = 0.1e1 / t89 / t41
  t138 = params.C ** 2
  t150 = t54 ** 2
  t151 = t150 * s0
  t159 = params.E ** 2
  t163 = 0.1e1 / t107 / t63 * t159 * t49 * t52 * t30
  t166 = 0.11e2 / 0.27e2 * t29 * t32 * t119 * t42 - t84 * t30 / t18 / t124 * t91 / 0.12e2 + 0.2e1 / 0.81e2 * t132 * t134 * t136 * t138 - 0.11e2 / 0.27e2 * t48 * t32 * t119 * t64 + 0.35e2 / 0.324e3 * t103 * t134 * t108 * params.E - t101 * t151 / t18 / t104 / t124 * t163 / 0.2916e4
  t171 = f.my_piecewise3(t2, 0, t6 * t22 * t69 / 0.12e2 - t6 * t74 * t113 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t117 * t166)
  t184 = 0.1e1 / t19 / t57
  t196 = 0.1e1 / t104 / t75
  t206 = t89 ** 2
  t223 = t104 ** 2
  t236 = t107 ** 2
  t252 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t69 + t6 * t22 * t113 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t74 * t166 - 0.3e1 / 0.8e1 * t6 * t117 * (-0.154e3 / 0.81e2 * t29 * t32 * t184 * t42 + 0.341e3 / 0.486e3 * t84 * t30 / t18 / t104 * t91 - 0.38e2 / 0.81e2 * t132 * t196 * t136 * t138 + 0.2e1 / 0.243e3 * t131 * t150 / t19 / t104 / t57 / t206 * t138 * params.C * t23 * t28 * t31 + 0.154e3 / 0.81e2 * t48 * t32 * t184 * t64 - 0.569e3 / 0.486e3 * t103 * t196 * t108 * params.E + t101 * t151 / t18 / t223 * t163 / 0.108e3 - t101 * t150 * t102 / t19 / t223 / t57 / t236 * t159 * params.E * t23 / t27 / t99 * t31 / 0.8748e4))
  v3rho3_0_ = 0.2e1 * r0 * t252 + 0.6e1 * t171

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
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = params.B * t24 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t39 = 0.1e1 + params.C * t24 * t29 * t33 * t22 / 0.24e2
  t40 = 0.1e1 / t39
  t46 = params.D * t24 * t29
  t47 = t24 ** 2
  t50 = 0.1e1 / t27 / t26
  t52 = s0 ** 2
  t54 = t18 ** 2
  t55 = t54 * r0
  t61 = 0.1e1 + params.E * t47 * t50 * t52 * t31 / t19 / t55 / 0.288e3
  t62 = 0.1e1 / t61
  t67 = params.A + t30 * t33 * t22 * t40 / 0.24e2 - t46 * t33 * t22 * t62 / 0.24e2
  t73 = t17 / t20 / r0
  t74 = t18 * r0
  t76 = 0.1e1 / t20 / t74
  t83 = params.B * t47 * t50 * t52
  t84 = t54 * t18
  t88 = t39 ** 2
  t90 = 0.1e1 / t88 * params.C
  t98 = t26 ** 2
  t99 = 0.1e1 / t98
  t100 = params.D * t99
  t101 = t52 * s0
  t102 = t100 * t101
  t103 = t54 ** 2
  t104 = t103 * r0
  t106 = t61 ** 2
  t107 = 0.1e1 / t106
  t112 = -t30 * t33 * t76 * t40 / 0.9e1 + t83 * t31 / t19 / t84 * t90 / 0.108e3 + t46 * t33 * t76 * t62 / 0.9e1 - t102 / t104 * t107 * params.E / 0.108e3
  t117 = t17 / t20
  t119 = 0.1e1 / t20 / t54
  t124 = t54 * t74
  t131 = params.B * t99
  t132 = t131 * t101
  t134 = 0.1e1 / t103 / t18
  t136 = 0.1e1 / t88 / t39
  t138 = params.C ** 2
  t150 = t52 ** 2
  t151 = t150 * s0
  t159 = params.E ** 2
  t162 = t47 * t50 * t31
  t163 = 0.1e1 / t106 / t61 * t159 * t162
  t166 = 0.11e2 / 0.27e2 * t30 * t33 * t119 * t40 - t83 * t31 / t19 / t124 * t90 / 0.12e2 + 0.2e1 / 0.81e2 * t132 * t134 * t136 * t138 - 0.11e2 / 0.27e2 * t46 * t33 * t119 * t62 + 0.35e2 / 0.324e3 * t102 * t134 * t107 * params.E - t100 * t151 / t19 / t103 / t124 * t163 / 0.2916e4
  t170 = t17 * t19
  t172 = 0.1e1 / t20 / t55
  t184 = 0.1e1 / t103 / t74
  t194 = t88 ** 2
  t200 = 0.1e1 / t194 * t138 * params.C * t24 * t29 * t32
  t211 = t103 ** 2
  t218 = t150 * t101
  t224 = t106 ** 2
  t232 = 0.1e1 / t224 * t159 * params.E * t24 / t28 / t98 * t32
  t235 = -0.154e3 / 0.81e2 * t30 * t33 * t172 * t40 + 0.341e3 / 0.486e3 * t83 * t31 / t19 / t103 * t90 - 0.38e2 / 0.81e2 * t132 * t184 * t136 * t138 + 0.2e1 / 0.243e3 * t131 * t150 / t20 / t103 / t55 * t200 + 0.154e3 / 0.81e2 * t46 * t33 * t172 * t62 - 0.569e3 / 0.486e3 * t102 * t184 * t107 * params.E + t100 * t151 / t19 / t211 * t163 / 0.108e3 - t100 * t218 / t20 / t211 / t55 * t232 / 0.8748e4
  t240 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t67 + t6 * t73 * t112 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t117 * t166 - 0.3e1 / 0.8e1 * t6 * t170 * t235)
  t256 = 0.1e1 / t20 / t84
  t267 = t103 * t54
  t268 = 0.1e1 / t267
  t283 = t151 / t19 / t211 / r0
  t287 = t138 ** 2
  t310 = t98 ** 2
  t314 = t150 ** 2
  t322 = t159 ** 2
  t331 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t76 * t67 - 0.5e1 / 0.9e1 * t6 * t23 * t112 + t6 * t73 * t166 / 0.2e1 - t6 * t117 * t235 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t170 * (0.2618e4 / 0.243e3 * t30 * t33 * t256 * t40 - 0.3047e4 / 0.486e3 * t83 * t31 / t19 / t104 * t90 + 0.5126e4 / 0.729e3 * t132 * t268 * t136 * t138 - 0.196e3 / 0.729e3 * t131 * t150 / t20 / t103 / t84 * t200 + 0.16e2 / 0.2187e4 * t131 * t283 / t194 / t39 * t287 * t162 - 0.2618e4 / 0.243e3 * t46 * t33 * t256 * t62 + 0.19393e5 / 0.1458e4 * t102 * t268 * t107 * params.E - 0.5107e4 / 0.26244e5 * t100 * t283 * t163 + 0.73e2 / 0.13122e5 * t100 * t218 / t20 / t211 / t84 * t232 - 0.2e1 / 0.19683e5 * params.D / t310 / t98 * t314 * s0 / t211 / t267 / t224 / t61 * t322))
  v4rho4_0_ = 0.2e1 * r0 * t331 + 0.8e1 * t240

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
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = params.B * t32 * t37
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t44 = s0 * t43
  t45 = params.C * t32
  t50 = 0.1e1 + t45 * t37 * s0 * t43 / 0.24e2
  t51 = 0.1e1 / t50
  t56 = params.D * t32 * t37
  t57 = t32 ** 2
  t58 = params.E * t57
  t60 = 0.1e1 / t35 / t34
  t61 = s0 ** 2
  t63 = t39 ** 2
  t70 = 0.1e1 + t58 * t60 * t61 / t40 / t63 / r0 / 0.576e3
  t71 = 0.1e1 / t70
  t75 = params.A + t38 * t44 * t51 / 0.24e2 - t56 * t44 * t71 / 0.24e2
  t79 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t80 = t79 * f.p.zeta_threshold
  t82 = f.my_piecewise3(t20, t80, t21 * t19)
  t83 = t30 ** 2
  t84 = 0.1e1 / t83
  t85 = t82 * t84
  t88 = t5 * t85 * t75 / 0.8e1
  t89 = t82 * t30
  t90 = t39 * r0
  t93 = s0 / t41 / t90
  t98 = params.B * t57 * t60
  t103 = t50 ** 2
  t105 = 0.1e1 / t103 * params.C
  t112 = t34 ** 2
  t113 = 0.1e1 / t112
  t114 = params.D * t113
  t115 = t61 * s0
  t116 = t114 * t115
  t117 = t63 ** 2
  t120 = t70 ** 2
  t121 = 0.1e1 / t120
  t126 = -t38 * t93 * t51 / 0.9e1 + t98 * t61 / t40 / t63 / t39 * t105 / 0.216e3 + t56 * t93 * t71 / 0.9e1 - t116 / t117 / r0 * t121 * params.E / 0.432e3
  t131 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t75 - t88 - 0.3e1 / 0.8e1 * t5 * t89 * t126)
  t133 = r1 <= f.p.dens_threshold
  t134 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t135 = 0.1e1 + t134
  t136 = t135 <= f.p.zeta_threshold
  t137 = t135 ** (0.1e1 / 0.3e1)
  t139 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t142 = f.my_piecewise3(t136, 0, 0.4e1 / 0.3e1 * t137 * t139)
  t143 = t142 * t30
  t144 = r1 ** 2
  t145 = r1 ** (0.1e1 / 0.3e1)
  t146 = t145 ** 2
  t148 = 0.1e1 / t146 / t144
  t149 = s2 * t148
  t154 = 0.1e1 + t45 * t37 * s2 * t148 / 0.24e2
  t155 = 0.1e1 / t154
  t159 = s2 ** 2
  t161 = t144 ** 2
  t168 = 0.1e1 + t58 * t60 * t159 / t145 / t161 / r1 / 0.576e3
  t169 = 0.1e1 / t168
  t173 = params.A + t38 * t149 * t155 / 0.24e2 - t56 * t149 * t169 / 0.24e2
  t178 = f.my_piecewise3(t136, t80, t137 * t135)
  t179 = t178 * t84
  t182 = t5 * t179 * t173 / 0.8e1
  t184 = f.my_piecewise3(t133, 0, -0.3e1 / 0.8e1 * t5 * t143 * t173 - t182)
  t186 = t21 ** 2
  t187 = 0.1e1 / t186
  t188 = t26 ** 2
  t193 = t16 / t22 / t6
  t195 = -0.2e1 * t23 + 0.2e1 * t193
  t196 = f.my_piecewise5(t10, 0, t14, 0, t195)
  t200 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t187 * t188 + 0.4e1 / 0.3e1 * t21 * t196)
  t207 = t5 * t29 * t84 * t75
  t213 = 0.1e1 / t83 / t6
  t217 = t5 * t82 * t213 * t75 / 0.12e2
  t219 = t5 * t85 * t126
  t223 = s0 / t41 / t63
  t227 = t63 * t90
  t234 = params.B * t113
  t237 = 0.1e1 / t117 / t39
  t241 = params.C ** 2
  t252 = t61 ** 2
  t261 = params.E ** 2
  t263 = t57 * t60
  t272 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t200 * t30 * t75 - t207 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t126 + t217 - t219 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t89 * (0.11e2 / 0.27e2 * t38 * t223 * t51 - t98 * t61 / t40 / t227 * t105 / 0.24e2 + t234 * t115 * t237 / t103 / t50 * t241 / 0.162e3 - 0.11e2 / 0.27e2 * t56 * t223 * t71 + 0.35e2 / 0.1296e4 * t116 * t237 * t121 * params.E - t114 * t252 * s0 / t40 / t117 / t227 / t120 / t70 * t261 * t263 / 0.23328e5))
  t273 = t137 ** 2
  t274 = 0.1e1 / t273
  t275 = t139 ** 2
  t279 = f.my_piecewise5(t14, 0, t10, 0, -t195)
  t283 = f.my_piecewise3(t136, 0, 0.4e1 / 0.9e1 * t274 * t275 + 0.4e1 / 0.3e1 * t137 * t279)
  t290 = t5 * t142 * t84 * t173
  t295 = t5 * t178 * t213 * t173 / 0.12e2
  t297 = f.my_piecewise3(t133, 0, -0.3e1 / 0.8e1 * t5 * t283 * t30 * t173 - t290 / 0.4e1 + t295)
  d11 = 0.2e1 * t131 + 0.2e1 * t184 + t6 * (t272 + t297)
  t300 = -t7 - t24
  t301 = f.my_piecewise5(t10, 0, t14, 0, t300)
  t304 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t301)
  t305 = t304 * t30
  t310 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t305 * t75 - t88)
  t312 = f.my_piecewise5(t14, 0, t10, 0, -t300)
  t315 = f.my_piecewise3(t136, 0, 0.4e1 / 0.3e1 * t137 * t312)
  t316 = t315 * t30
  t320 = t178 * t30
  t321 = t144 * r1
  t324 = s2 / t146 / t321
  t332 = t154 ** 2
  t334 = 0.1e1 / t332 * params.C
  t341 = t159 * s2
  t342 = t114 * t341
  t343 = t161 ** 2
  t346 = t168 ** 2
  t347 = 0.1e1 / t346
  t352 = -t38 * t324 * t155 / 0.9e1 + t98 * t159 / t145 / t161 / t144 * t334 / 0.216e3 + t56 * t324 * t169 / 0.9e1 - t342 / t343 / r1 * t347 * params.E / 0.432e3
  t357 = f.my_piecewise3(t133, 0, -0.3e1 / 0.8e1 * t5 * t316 * t173 - t182 - 0.3e1 / 0.8e1 * t5 * t320 * t352)
  t361 = 0.2e1 * t193
  t362 = f.my_piecewise5(t10, 0, t14, 0, t361)
  t366 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t187 * t301 * t26 + 0.4e1 / 0.3e1 * t21 * t362)
  t373 = t5 * t304 * t84 * t75
  t381 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t366 * t30 * t75 - t373 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t305 * t126 - t207 / 0.8e1 + t217 - t219 / 0.8e1)
  t385 = f.my_piecewise5(t14, 0, t10, 0, -t361)
  t389 = f.my_piecewise3(t136, 0, 0.4e1 / 0.9e1 * t274 * t312 * t139 + 0.4e1 / 0.3e1 * t137 * t385)
  t396 = t5 * t315 * t84 * t173
  t403 = t5 * t179 * t352
  t406 = f.my_piecewise3(t133, 0, -0.3e1 / 0.8e1 * t5 * t389 * t30 * t173 - t396 / 0.8e1 - t290 / 0.8e1 + t295 - 0.3e1 / 0.8e1 * t5 * t143 * t352 - t403 / 0.8e1)
  d12 = t131 + t184 + t310 + t357 + t6 * (t381 + t406)
  t411 = t301 ** 2
  t415 = 0.2e1 * t23 + 0.2e1 * t193
  t416 = f.my_piecewise5(t10, 0, t14, 0, t415)
  t420 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t187 * t411 + 0.4e1 / 0.3e1 * t21 * t416)
  t427 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t420 * t30 * t75 - t373 / 0.4e1 + t217)
  t428 = t312 ** 2
  t432 = f.my_piecewise5(t14, 0, t10, 0, -t415)
  t436 = f.my_piecewise3(t136, 0, 0.4e1 / 0.9e1 * t274 * t428 + 0.4e1 / 0.3e1 * t137 * t432)
  t448 = s2 / t146 / t161
  t452 = t161 * t321
  t461 = 0.1e1 / t343 / t144
  t475 = t159 ** 2
  t493 = f.my_piecewise3(t133, 0, -0.3e1 / 0.8e1 * t5 * t436 * t30 * t173 - t396 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t316 * t352 + t295 - t403 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t320 * (0.11e2 / 0.27e2 * t38 * t448 * t155 - t98 * t159 / t145 / t452 * t334 / 0.24e2 + t234 * t341 * t461 / t332 / t154 * t241 / 0.162e3 - 0.11e2 / 0.27e2 * t56 * t448 * t169 + 0.35e2 / 0.1296e4 * t342 * t461 * t347 * params.E - t114 * t475 * s2 / t145 / t343 / t452 / t346 / t168 * t261 * t263 / 0.23328e5))
  d22 = 0.2e1 * t310 + 0.2e1 * t357 + t6 * (t427 + t493)
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
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t50 = params.B * t44 * t49
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t55 = 0.1e1 / t53 / t51
  t56 = s0 * t55
  t57 = params.C * t44
  t62 = 0.1e1 + t57 * t49 * s0 * t55 / 0.24e2
  t63 = 0.1e1 / t62
  t68 = params.D * t44 * t49
  t69 = t44 ** 2
  t70 = params.E * t69
  t72 = 0.1e1 / t47 / t46
  t73 = s0 ** 2
  t75 = t51 ** 2
  t76 = t75 * r0
  t82 = 0.1e1 + t70 * t72 * t73 / t52 / t76 / 0.576e3
  t83 = 0.1e1 / t82
  t87 = params.A + t50 * t56 * t63 / 0.24e2 - t68 * t56 * t83 / 0.24e2
  t93 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t94 = t42 ** 2
  t95 = 0.1e1 / t94
  t96 = t93 * t95
  t100 = t93 * t42
  t101 = t51 * r0
  t104 = s0 / t53 / t101
  t109 = params.B * t69 * t72
  t114 = t62 ** 2
  t116 = 0.1e1 / t114 * params.C
  t123 = t46 ** 2
  t124 = 0.1e1 / t123
  t125 = params.D * t124
  t126 = t73 * s0
  t127 = t125 * t126
  t128 = t75 ** 2
  t131 = t82 ** 2
  t132 = 0.1e1 / t131
  t137 = -t50 * t104 * t63 / 0.9e1 + t109 * t73 / t52 / t75 / t51 * t116 / 0.216e3 + t68 * t104 * t83 / 0.9e1 - t127 / t128 / r0 * t132 * params.E / 0.432e3
  t141 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t142 = t141 * f.p.zeta_threshold
  t144 = f.my_piecewise3(t20, t142, t21 * t19)
  t146 = 0.1e1 / t94 / t6
  t147 = t144 * t146
  t151 = t144 * t95
  t155 = t144 * t42
  t158 = s0 / t53 / t75
  t162 = t75 * t101
  t169 = params.B * t124
  t170 = t169 * t126
  t172 = 0.1e1 / t128 / t51
  t174 = 0.1e1 / t114 / t62
  t176 = params.C ** 2
  t187 = t73 ** 2
  t188 = t187 * s0
  t196 = params.E ** 2
  t199 = 0.1e1 / t131 / t82 * t196 * t69 * t72
  t202 = 0.11e2 / 0.27e2 * t50 * t158 * t63 - t109 * t73 / t52 / t162 * t116 / 0.24e2 + t170 * t172 * t174 * t176 / 0.162e3 - 0.11e2 / 0.27e2 * t68 * t158 * t83 + 0.35e2 / 0.1296e4 * t127 * t172 * t132 * params.E - t125 * t188 / t52 / t128 / t162 * t199 / 0.23328e5
  t207 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t87 - t5 * t96 * t87 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t100 * t137 + t5 * t147 * t87 / 0.12e2 - t5 * t151 * t137 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t155 * t202)
  t209 = r1 <= f.p.dens_threshold
  t210 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t211 = 0.1e1 + t210
  t212 = t211 <= f.p.zeta_threshold
  t213 = t211 ** (0.1e1 / 0.3e1)
  t214 = t213 ** 2
  t215 = 0.1e1 / t214
  t217 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t218 = t217 ** 2
  t222 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t226 = f.my_piecewise3(t212, 0, 0.4e1 / 0.9e1 * t215 * t218 + 0.4e1 / 0.3e1 * t213 * t222)
  t228 = r1 ** 2
  t229 = r1 ** (0.1e1 / 0.3e1)
  t230 = t229 ** 2
  t232 = 0.1e1 / t230 / t228
  t233 = s2 * t232
  t243 = s2 ** 2
  t245 = t228 ** 2
  t257 = params.A + t50 * t233 / (0.1e1 + t57 * t49 * s2 * t232 / 0.24e2) / 0.24e2 - t68 * t233 / (0.1e1 + t70 * t72 * t243 / t229 / t245 / r1 / 0.576e3) / 0.24e2
  t263 = f.my_piecewise3(t212, 0, 0.4e1 / 0.3e1 * t213 * t217)
  t269 = f.my_piecewise3(t212, t142, t213 * t211)
  t275 = f.my_piecewise3(t209, 0, -0.3e1 / 0.8e1 * t5 * t226 * t42 * t257 - t5 * t263 * t95 * t257 / 0.4e1 + t5 * t269 * t146 * t257 / 0.12e2)
  t285 = t24 ** 2
  t289 = 0.6e1 * t33 - 0.6e1 * t16 / t285
  t290 = f.my_piecewise5(t10, 0, t14, 0, t289)
  t294 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t290)
  t317 = 0.1e1 / t94 / t24
  t330 = s0 / t53 / t76
  t341 = 0.1e1 / t128 / t101
  t351 = t114 ** 2
  t366 = t128 ** 2
  t379 = t131 ** 2
  t394 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t294 * t42 * t87 - 0.3e1 / 0.8e1 * t5 * t41 * t95 * t87 - 0.9e1 / 0.8e1 * t5 * t43 * t137 + t5 * t93 * t146 * t87 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t96 * t137 - 0.9e1 / 0.8e1 * t5 * t100 * t202 - 0.5e1 / 0.36e2 * t5 * t144 * t317 * t87 + t5 * t147 * t137 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t151 * t202 - 0.3e1 / 0.8e1 * t5 * t155 * (-0.154e3 / 0.81e2 * t50 * t330 * t63 + 0.341e3 / 0.972e3 * t109 * t73 / t52 / t128 * t116 - 0.19e2 / 0.162e3 * t170 * t341 * t174 * t176 + t169 * t187 / t53 / t128 / t76 / t351 * t176 * params.C * t44 * t49 / 0.486e3 + 0.154e3 / 0.81e2 * t68 * t330 * t83 - 0.569e3 / 0.1944e4 * t127 * t341 * t132 * params.E + t125 * t188 / t52 / t366 * t199 / 0.864e3 - t125 * t187 * t126 / t53 / t366 / t76 / t379 * t196 * params.E * t44 / t48 / t123 / 0.139968e6))
  t404 = f.my_piecewise5(t14, 0, t10, 0, -t289)
  t408 = f.my_piecewise3(t212, 0, -0.8e1 / 0.27e2 / t214 / t211 * t218 * t217 + 0.4e1 / 0.3e1 * t215 * t217 * t222 + 0.4e1 / 0.3e1 * t213 * t404)
  t426 = f.my_piecewise3(t209, 0, -0.3e1 / 0.8e1 * t5 * t408 * t42 * t257 - 0.3e1 / 0.8e1 * t5 * t226 * t95 * t257 + t5 * t263 * t146 * t257 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t269 * t317 * t257)
  d111 = 0.3e1 * t207 + 0.3e1 * t275 + t6 * (t394 + t426)

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
  t58 = jnp.pi ** 2
  t59 = t58 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t62 = params.B * t56 * t61
  t63 = r0 ** 2
  t64 = r0 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t67 = 0.1e1 / t65 / t63
  t68 = s0 * t67
  t69 = params.C * t56
  t74 = 0.1e1 + t69 * t61 * s0 * t67 / 0.24e2
  t75 = 0.1e1 / t74
  t80 = params.D * t56 * t61
  t81 = t56 ** 2
  t82 = params.E * t81
  t84 = 0.1e1 / t59 / t58
  t85 = s0 ** 2
  t87 = t63 ** 2
  t88 = t87 * r0
  t94 = 0.1e1 + t82 * t84 * t85 / t64 / t88 / 0.576e3
  t95 = 0.1e1 / t94
  t99 = params.A + t62 * t68 * t75 / 0.24e2 - t80 * t68 * t95 / 0.24e2
  t108 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t109 = t54 ** 2
  t110 = 0.1e1 / t109
  t111 = t108 * t110
  t115 = t108 * t54
  t116 = t63 * r0
  t119 = s0 / t65 / t116
  t124 = params.B * t81 * t84
  t125 = t87 * t63
  t129 = t74 ** 2
  t131 = 0.1e1 / t129 * params.C
  t138 = t58 ** 2
  t139 = 0.1e1 / t138
  t140 = params.D * t139
  t141 = t85 * s0
  t142 = t140 * t141
  t143 = t87 ** 2
  t144 = t143 * r0
  t146 = t94 ** 2
  t147 = 0.1e1 / t146
  t152 = -t62 * t119 * t75 / 0.9e1 + t124 * t85 / t64 / t125 * t131 / 0.216e3 + t80 * t119 * t95 / 0.9e1 - t142 / t144 * t147 * params.E / 0.432e3
  t158 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t160 = 0.1e1 / t109 / t6
  t161 = t158 * t160
  t165 = t158 * t110
  t169 = t158 * t54
  t172 = s0 / t65 / t87
  t176 = t87 * t116
  t183 = params.B * t139
  t184 = t183 * t141
  t186 = 0.1e1 / t143 / t63
  t188 = 0.1e1 / t129 / t74
  t190 = params.C ** 2
  t201 = t85 ** 2
  t202 = t201 * s0
  t210 = params.E ** 2
  t212 = t81 * t84
  t213 = 0.1e1 / t146 / t94 * t210 * t212
  t216 = 0.11e2 / 0.27e2 * t62 * t172 * t75 - t124 * t85 / t64 / t176 * t131 / 0.24e2 + t184 * t186 * t188 * t190 / 0.162e3 - 0.11e2 / 0.27e2 * t80 * t172 * t95 + 0.35e2 / 0.1296e4 * t142 * t186 * t147 * params.E - t140 * t202 / t64 / t143 / t176 * t213 / 0.23328e5
  t220 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t221 = t220 * f.p.zeta_threshold
  t223 = f.my_piecewise3(t20, t221, t21 * t19)
  t225 = 0.1e1 / t109 / t25
  t226 = t223 * t225
  t230 = t223 * t160
  t234 = t223 * t110
  t238 = t223 * t54
  t241 = s0 / t65 / t88
  t252 = 0.1e1 / t143 / t116
  t262 = t129 ** 2
  t267 = 0.1e1 / t262 * t190 * params.C * t56 * t61
  t277 = t143 ** 2
  t284 = t201 * t141
  t290 = t146 ** 2
  t297 = 0.1e1 / t290 * t210 * params.E * t56 / t60 / t138
  t300 = -0.154e3 / 0.81e2 * t62 * t241 * t75 + 0.341e3 / 0.972e3 * t124 * t85 / t64 / t143 * t131 - 0.19e2 / 0.162e3 * t184 * t252 * t188 * t190 + t183 * t201 / t65 / t143 / t88 * t267 / 0.486e3 + 0.154e3 / 0.81e2 * t80 * t241 * t95 - 0.569e3 / 0.1944e4 * t142 * t252 * t147 * params.E + t140 * t202 / t64 / t277 * t213 / 0.864e3 - t140 * t284 / t65 / t277 / t88 * t297 / 0.139968e6
  t305 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t99 - 0.3e1 / 0.8e1 * t5 * t111 * t99 - 0.9e1 / 0.8e1 * t5 * t115 * t152 + t5 * t161 * t99 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t165 * t152 - 0.9e1 / 0.8e1 * t5 * t169 * t216 - 0.5e1 / 0.36e2 * t5 * t226 * t99 + t5 * t230 * t152 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t234 * t216 - 0.3e1 / 0.8e1 * t5 * t238 * t300)
  t307 = r1 <= f.p.dens_threshold
  t308 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t309 = 0.1e1 + t308
  t310 = t309 <= f.p.zeta_threshold
  t311 = t309 ** (0.1e1 / 0.3e1)
  t312 = t311 ** 2
  t314 = 0.1e1 / t312 / t309
  t316 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t317 = t316 ** 2
  t321 = 0.1e1 / t312
  t322 = t321 * t316
  t324 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t328 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t332 = f.my_piecewise3(t310, 0, -0.8e1 / 0.27e2 * t314 * t317 * t316 + 0.4e1 / 0.3e1 * t322 * t324 + 0.4e1 / 0.3e1 * t311 * t328)
  t334 = r1 ** 2
  t335 = r1 ** (0.1e1 / 0.3e1)
  t336 = t335 ** 2
  t338 = 0.1e1 / t336 / t334
  t339 = s2 * t338
  t349 = s2 ** 2
  t351 = t334 ** 2
  t363 = params.A + t62 * t339 / (0.1e1 + t69 * t61 * s2 * t338 / 0.24e2) / 0.24e2 - t80 * t339 / (0.1e1 + t82 * t84 * t349 / t335 / t351 / r1 / 0.576e3) / 0.24e2
  t372 = f.my_piecewise3(t310, 0, 0.4e1 / 0.9e1 * t321 * t317 + 0.4e1 / 0.3e1 * t311 * t324)
  t379 = f.my_piecewise3(t310, 0, 0.4e1 / 0.3e1 * t311 * t316)
  t385 = f.my_piecewise3(t310, t221, t311 * t309)
  t391 = f.my_piecewise3(t307, 0, -0.3e1 / 0.8e1 * t5 * t332 * t54 * t363 - 0.3e1 / 0.8e1 * t5 * t372 * t110 * t363 + t5 * t379 * t160 * t363 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t385 * t225 * t363)
  t394 = 0.1e1 / t109 / t36
  t411 = t19 ** 2
  t414 = t30 ** 2
  t420 = t41 ** 2
  t429 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t430 = f.my_piecewise5(t10, 0, t14, 0, t429)
  t434 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t411 * t414 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t420 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t430)
  t467 = s0 / t65 / t125
  t477 = t143 * t87
  t478 = 0.1e1 / t477
  t493 = t202 / t64 / t277 / r0
  t497 = t190 ** 2
  t519 = t138 ** 2
  t523 = t201 ** 2
  t531 = t210 ** 2
  t539 = 0.10e2 / 0.27e2 * t5 * t223 * t394 * t99 - t5 * t53 * t110 * t99 / 0.2e1 + t5 * t108 * t160 * t99 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t158 * t225 * t99 - 0.3e1 / 0.8e1 * t5 * t434 * t54 * t99 - 0.3e1 / 0.2e1 * t5 * t55 * t152 - 0.3e1 / 0.2e1 * t5 * t111 * t152 - 0.9e1 / 0.4e1 * t5 * t115 * t216 + t5 * t161 * t152 - 0.3e1 / 0.2e1 * t5 * t165 * t216 - 0.3e1 / 0.2e1 * t5 * t169 * t300 - 0.5e1 / 0.9e1 * t5 * t226 * t152 + t5 * t230 * t216 / 0.2e1 - t5 * t234 * t300 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t238 * (0.2618e4 / 0.243e3 * t62 * t467 * t75 - 0.3047e4 / 0.972e3 * t124 * t85 / t64 / t144 * t131 + 0.2563e4 / 0.1458e4 * t184 * t478 * t188 * t190 - 0.49e2 / 0.729e3 * t183 * t201 / t65 / t143 / t125 * t267 + 0.2e1 / 0.2187e4 * t183 * t493 / t262 / t74 * t497 * t212 - 0.2618e4 / 0.243e3 * t80 * t467 * t95 + 0.19393e5 / 0.5832e4 * t142 * t478 * t147 * params.E - 0.5107e4 / 0.209952e6 * t140 * t493 * t213 + 0.73e2 / 0.209952e6 * t140 * t284 / t65 / t277 / t125 * t297 - params.D / t519 / t138 * t523 * s0 / t277 / t477 / t290 / t94 * t531 / 0.629856e6)
  t540 = f.my_piecewise3(t1, 0, t539)
  t541 = t309 ** 2
  t544 = t317 ** 2
  t550 = t324 ** 2
  t556 = f.my_piecewise5(t14, 0, t10, 0, -t429)
  t560 = f.my_piecewise3(t310, 0, 0.40e2 / 0.81e2 / t312 / t541 * t544 - 0.16e2 / 0.9e1 * t314 * t317 * t324 + 0.4e1 / 0.3e1 * t321 * t550 + 0.16e2 / 0.9e1 * t322 * t328 + 0.4e1 / 0.3e1 * t311 * t556)
  t582 = f.my_piecewise3(t307, 0, -0.3e1 / 0.8e1 * t5 * t560 * t54 * t363 - t5 * t332 * t110 * t363 / 0.2e1 + t5 * t372 * t160 * t363 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t379 * t225 * t363 + 0.10e2 / 0.27e2 * t5 * t385 * t394 * t363)
  d1111 = 0.4e1 * t305 + 0.4e1 * t391 + t6 * (t540 + t582)

  res = {'v4rho4': d1111}
  return res
