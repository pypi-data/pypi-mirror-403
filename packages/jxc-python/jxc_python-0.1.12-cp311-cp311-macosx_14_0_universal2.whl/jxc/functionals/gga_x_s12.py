"""Generated from gga_x_s12.mpl."""

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
  params_bx_raw = params.bx
  if isinstance(params_bx_raw, (str, bytes, dict)):
    params_bx = params_bx_raw
  else:
    try:
      params_bx_seq = list(params_bx_raw)
    except TypeError:
      params_bx = params_bx_raw
    else:
      params_bx_seq = np.asarray(params_bx_seq, dtype=np.float64)
      params_bx = np.concatenate((np.array([np.nan], dtype=np.float64), params_bx_seq))

  s12g_f = lambda x: params_bx * (params_A + params_B * (1 - 1 / (1 + params_C * x ** 2 + params_D * x ** 4)) * (1 - 1 / (1 + params_E * x ** 2)))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, s12g_f, rs, z, xs0, xs1)

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
  params_bx_raw = params.bx
  if isinstance(params_bx_raw, (str, bytes, dict)):
    params_bx = params_bx_raw
  else:
    try:
      params_bx_seq = list(params_bx_raw)
    except TypeError:
      params_bx = params_bx_raw
    else:
      params_bx_seq = np.asarray(params_bx_seq, dtype=np.float64)
      params_bx = np.concatenate((np.array([np.nan], dtype=np.float64), params_bx_seq))

  s12g_f = lambda x: params_bx * (params_A + params_B * (1 - 1 / (1 + params_C * x ** 2 + params_D * x ** 4)) * (1 - 1 / (1 + params_E * x ** 2)))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, s12g_f, rs, z, xs0, xs1)

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
  params_bx_raw = params.bx
  if isinstance(params_bx_raw, (str, bytes, dict)):
    params_bx = params_bx_raw
  else:
    try:
      params_bx_seq = list(params_bx_raw)
    except TypeError:
      params_bx = params_bx_raw
    else:
      params_bx_seq = np.asarray(params_bx_seq, dtype=np.float64)
      params_bx = np.concatenate((np.array([np.nan], dtype=np.float64), params_bx_seq))

  s12g_f = lambda x: params_bx * (params_A + params_B * (1 - 1 / (1 + params_C * x ** 2 + params_D * x ** 4)) * (1 - 1 / (1 + params_E * x ** 2)))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, s12g_f, rs, z, xs0, xs1)

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
  t26 = t5 * t25
  t27 = t6 ** (0.1e1 / 0.3e1)
  t28 = t27 * params.bx
  t29 = params.C * s0
  t30 = r0 ** 2
  t31 = r0 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t34 = 0.1e1 / t32 / t30
  t36 = s0 ** 2
  t37 = params.D * t36
  t38 = t30 ** 2
  t41 = 0.1e1 / t31 / t38 / r0
  t43 = t29 * t34 + t37 * t41 + 0.1e1
  t46 = params.B * (0.1e1 - 0.1e1 / t43)
  t47 = params.E * s0
  t49 = t47 * t34 + 0.1e1
  t51 = 0.1e1 - 0.1e1 / t49
  t53 = t46 * t51 + params.A
  t54 = t28 * t53
  t57 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t54)
  t58 = r1 <= f.p.dens_threshold
  t59 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t60 = 0.1e1 + t59
  t61 = t60 <= f.p.zeta_threshold
  t62 = t60 ** (0.1e1 / 0.3e1)
  t64 = f.my_piecewise3(t61, t22, t62 * t60)
  t65 = t5 * t64
  t66 = params.C * s2
  t67 = r1 ** 2
  t68 = r1 ** (0.1e1 / 0.3e1)
  t69 = t68 ** 2
  t71 = 0.1e1 / t69 / t67
  t73 = s2 ** 2
  t74 = params.D * t73
  t75 = t67 ** 2
  t78 = 0.1e1 / t68 / t75 / r1
  t80 = t66 * t71 + t74 * t78 + 0.1e1
  t83 = params.B * (0.1e1 - 0.1e1 / t80)
  t84 = params.E * s2
  t86 = t84 * t71 + 0.1e1
  t88 = 0.1e1 - 0.1e1 / t86
  t90 = t83 * t88 + params.A
  t91 = t28 * t90
  t94 = f.my_piecewise3(t58, 0, -0.3e1 / 0.8e1 * t65 * t91)
  t95 = t6 ** 2
  t97 = t16 / t95
  t98 = t7 - t97
  t99 = f.my_piecewise5(t10, 0, t14, 0, t98)
  t102 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t99)
  t106 = t27 ** 2
  t108 = 0.1e1 / t106 * params.bx
  t111 = t26 * t108 * t53 / 0.8e1
  t112 = t43 ** 2
  t114 = params.B / t112
  t117 = 0.1e1 / t32 / t30 / r0
  t128 = t49 ** 2
  t129 = 0.1e1 / t128
  t139 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t102 * t54 - t111 - 0.3e1 / 0.8e1 * t26 * t28 * (t114 * (-0.8e1 / 0.3e1 * t29 * t117 - 0.16e2 / 0.3e1 * t37 / t31 / t38 / t30) * t51 - 0.8e1 / 0.3e1 * t46 * t129 * t47 * t117))
  t141 = f.my_piecewise5(t14, 0, t10, 0, -t98)
  t144 = f.my_piecewise3(t61, 0, 0.4e1 / 0.3e1 * t62 * t141)
  t150 = t65 * t108 * t90 / 0.8e1
  t152 = f.my_piecewise3(t58, 0, -0.3e1 / 0.8e1 * t5 * t144 * t91 - t150)
  vrho_0_ = t57 + t94 + t6 * (t139 + t152)
  t155 = -t7 - t97
  t156 = f.my_piecewise5(t10, 0, t14, 0, t155)
  t159 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t156)
  t164 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t159 * t54 - t111)
  t166 = f.my_piecewise5(t14, 0, t10, 0, -t155)
  t169 = f.my_piecewise3(t61, 0, 0.4e1 / 0.3e1 * t62 * t166)
  t173 = t80 ** 2
  t175 = params.B / t173
  t178 = 0.1e1 / t69 / t67 / r1
  t189 = t86 ** 2
  t190 = 0.1e1 / t189
  t200 = f.my_piecewise3(t58, 0, -0.3e1 / 0.8e1 * t5 * t169 * t91 - t150 - 0.3e1 / 0.8e1 * t65 * t28 * (t175 * (-0.8e1 / 0.3e1 * t66 * t178 - 0.16e2 / 0.3e1 * t74 / t68 / t75 / t67) * t88 - 0.8e1 / 0.3e1 * t83 * t190 * t84 * t178))
  vrho_1_ = t57 + t94 + t6 * (t164 + t200)
  t217 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t28 * (t114 * (0.2e1 * params.D * s0 * t41 + params.C * t34) * t51 + t46 * t129 * params.E * t34))
  vsigma_0_ = t6 * t217
  vsigma_1_ = 0.0e0
  t232 = f.my_piecewise3(t58, 0, -0.3e1 / 0.8e1 * t65 * t28 * (t175 * (0.2e1 * params.D * s2 * t78 + params.C * t71) * t88 + t83 * t190 * params.E * t71))
  vsigma_2_ = t6 * t232
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
  params_bx_raw = params.bx
  if isinstance(params_bx_raw, (str, bytes, dict)):
    params_bx = params_bx_raw
  else:
    try:
      params_bx_seq = list(params_bx_raw)
    except TypeError:
      params_bx = params_bx_raw
    else:
      params_bx_seq = np.asarray(params_bx_seq, dtype=np.float64)
      params_bx = np.concatenate((np.array([np.nan], dtype=np.float64), params_bx_seq))

  s12g_f = lambda x: params_bx * (params_A + params_B * (1 - 1 / (1 + params_C * x ** 2 + params_D * x ** 4)) * (1 - 1 / (1 + params_E * x ** 2)))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, s12g_f, rs, z, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 * params.bx
  t21 = params.C * s0
  t22 = 2 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = r0 ** 2
  t25 = t19 ** 2
  t27 = 0.1e1 / t25 / t24
  t28 = t23 * t27
  t30 = s0 ** 2
  t31 = params.D * t30
  t32 = t24 ** 2
  t36 = t22 / t19 / t32 / r0
  t39 = t21 * t28 + 0.2e1 * t31 * t36 + 0.1e1
  t42 = params.B * (0.1e1 - 0.1e1 / t39)
  t43 = params.E * s0
  t45 = t43 * t28 + 0.1e1
  t47 = 0.1e1 - 0.1e1 / t45
  t49 = t42 * t47 + params.A
  t53 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t20 * t49)
  t59 = t39 ** 2
  t61 = params.B / t59
  t65 = t23 / t25 / t24 / r0
  t77 = t45 ** 2
  t79 = t42 / t77
  t88 = f.my_piecewise3(t2, 0, -t18 / t25 * params.bx * t49 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t20 * (t61 * (-0.8e1 / 0.3e1 * t21 * t65 - 0.32e2 / 0.3e1 * t31 * t22 / t19 / t32 / t24) * t47 - 0.8e1 / 0.3e1 * t79 * t43 * t65))
  vrho_0_ = 0.2e1 * r0 * t88 + 0.2e1 * t53
  t106 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t20 * (t61 * (0.4e1 * params.D * s0 * t36 + params.C * t23 * t27) * t47 + t79 * params.E * t23 * t27))
  vsigma_0_ = 0.2e1 * r0 * t106
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
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 * params.bx
  t23 = params.C * s0
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = r0 ** 2
  t28 = 0.1e1 / t20 / t26
  t29 = t25 * t28
  t31 = s0 ** 2
  t32 = params.D * t31
  t33 = t26 ** 2
  t36 = 0.1e1 / t19 / t33 / r0
  t37 = t24 * t36
  t40 = t23 * t29 + 0.2e1 * t32 * t37 + 0.1e1
  t43 = params.B * (0.1e1 - 0.1e1 / t40)
  t44 = params.E * s0
  t46 = t44 * t29 + 0.1e1
  t48 = 0.1e1 - 0.1e1 / t46
  t50 = t43 * t48 + params.A
  t54 = t19 * params.bx
  t55 = t40 ** 2
  t57 = params.B / t55
  t58 = t26 * r0
  t60 = 0.1e1 / t20 / t58
  t61 = t25 * t60
  t66 = 0.1e1 / t19 / t33 / t26
  t67 = t24 * t66
  t70 = -0.8e1 / 0.3e1 * t23 * t61 - 0.32e2 / 0.3e1 * t32 * t67
  t73 = t46 ** 2
  t74 = 0.1e1 / t73
  t75 = t43 * t74
  t76 = t44 * t61
  t79 = t57 * t70 * t48 - 0.8e1 / 0.3e1 * t75 * t76
  t84 = f.my_piecewise3(t2, 0, -t18 * t22 * t50 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t54 * t79)
  t97 = params.B / t55 / t40
  t98 = t70 ** 2
  t104 = t25 / t20 / t33
  t110 = t24 / t19 / t33 / t58
  t122 = t43 / t73 / t46
  t123 = params.E ** 2
  t136 = f.my_piecewise3(t2, 0, t18 / t20 / r0 * params.bx * t50 / 0.12e2 - t18 * t22 * t79 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t54 * (-0.2e1 * t97 * t98 * t48 + t57 * (0.88e2 / 0.9e1 * t23 * t104 + 0.608e3 / 0.9e1 * t32 * t110) * t48 - 0.16e2 / 0.3e1 * t57 * t70 * t74 * t76 - 0.256e3 / 0.9e1 * t122 * t123 * t31 * t110 + 0.88e2 / 0.9e1 * t75 * t44 * t104))
  v2rho2_0_ = 0.2e1 * r0 * t136 + 0.4e1 * t84
  t139 = params.C * t25
  t141 = params.D * s0
  t144 = t139 * t28 + 0.4e1 * t141 * t37
  t145 = t144 * t48
  t147 = params.E * t25
  t150 = t75 * t147 * t28 + t57 * t145
  t154 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t54 * t150)
  t174 = t74 * params.E * t29
  t176 = t123 * t24
  t189 = f.my_piecewise3(t2, 0, -t18 * t22 * t150 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t54 * (-0.2e1 * t97 * t145 * t70 + t57 * (-0.8e1 / 0.3e1 * t139 * t60 - 0.64e2 / 0.3e1 * t141 * t67) * t48 - 0.8e1 / 0.3e1 * t57 * t144 * t74 * t76 + t57 * t70 * t174 + 0.32e2 / 0.3e1 * t122 * t176 * t66 * s0 - 0.8e1 / 0.3e1 * t75 * t147 * t60))
  v2rhosigma_0_ = 0.2e1 * r0 * t189 + 0.2e1 * t154
  t192 = t144 ** 2
  t210 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t54 * (0.4e1 * t57 * params.D * t37 * t48 - 0.4e1 * t122 * t176 * t36 + 0.2e1 * t57 * t144 * t174 - 0.2e1 * t97 * t192 * t48))
  v2sigma2_0_ = 0.2e1 * r0 * t210
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t23 = 0.1e1 / t20 / r0 * params.bx
  t24 = params.C * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = r0 ** 2
  t29 = 0.1e1 / t20 / t27
  t30 = t26 * t29
  t32 = s0 ** 2
  t33 = params.D * t32
  t34 = t27 ** 2
  t35 = t34 * r0
  t41 = 0.1e1 + t24 * t30 + 0.2e1 * t33 * t25 / t19 / t35
  t44 = params.B * (0.1e1 - 0.1e1 / t41)
  t45 = params.E * s0
  t47 = t45 * t30 + 0.1e1
  t49 = 0.1e1 - 0.1e1 / t47
  t51 = t44 * t49 + params.A
  t56 = 0.1e1 / t20 * params.bx
  t57 = t41 ** 2
  t59 = params.B / t57
  t60 = t27 * r0
  t63 = t26 / t20 / t60
  t72 = -0.8e1 / 0.3e1 * t24 * t63 - 0.32e2 / 0.3e1 * t33 * t25 / t19 / t34 / t27
  t73 = t72 * t49
  t75 = t47 ** 2
  t76 = 0.1e1 / t75
  t77 = t44 * t76
  t78 = t45 * t63
  t81 = t59 * t73 - 0.8e1 / 0.3e1 * t77 * t78
  t85 = t19 * params.bx
  t88 = params.B / t57 / t41
  t89 = t72 ** 2
  t95 = t26 / t20 / t34
  t101 = t25 / t19 / t34 / t60
  t104 = 0.88e2 / 0.9e1 * t24 * t95 + 0.608e3 / 0.9e1 * t33 * t101
  t108 = t59 * t72 * t76
  t112 = 0.1e1 / t75 / t47
  t113 = t44 * t112
  t114 = params.E ** 2
  t115 = t114 * t32
  t116 = t115 * t101
  t119 = t45 * t95
  t122 = -0.2e1 * t88 * t89 * t49 + t59 * t104 * t49 - 0.16e2 / 0.3e1 * t108 * t78 - 0.256e3 / 0.9e1 * t113 * t116 + 0.88e2 / 0.9e1 * t77 * t119
  t127 = f.my_piecewise3(t2, 0, t18 * t23 * t51 / 0.12e2 - t18 * t56 * t81 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t85 * t122)
  t139 = t57 ** 2
  t155 = t26 / t20 / t35
  t158 = t34 ** 2
  t161 = t25 / t19 / t158
  t177 = t75 ** 2
  t199 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t29 * params.bx * t51 + t18 * t23 * t81 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t56 * t122 - 0.3e1 / 0.8e1 * t18 * t85 * (0.6e1 * params.B / t139 * t89 * t72 * t49 - 0.6e1 * t88 * t73 * t104 + 0.16e2 * t88 * t89 * t76 * t78 + t59 * (-0.1232e4 / 0.27e2 * t24 * t155 - 0.13376e5 / 0.27e2 * t33 * t161) * t49 - 0.8e1 * t59 * t104 * t76 * t78 - 0.256e3 / 0.3e1 * t59 * t72 * t112 * t116 + 0.88e2 / 0.3e1 * t108 * t119 - 0.4096e4 / 0.9e1 * t44 / t177 * t114 * params.E * t32 * s0 / t158 / t60 + 0.2816e4 / 0.9e1 * t113 * t115 * t161 - 0.1232e4 / 0.27e2 * t77 * t45 * t155))
  v3rho3_0_ = 0.2e1 * r0 * t199 + 0.6e1 * t127

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** 2
  t20 = r0 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t23 = 0.1e1 / t21 / t19
  t24 = t23 * params.bx
  t25 = params.C * s0
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = t27 * t23
  t30 = s0 ** 2
  t31 = params.D * t30
  t32 = t19 ** 2
  t33 = t32 * r0
  t39 = 0.1e1 + t25 * t28 + 0.2e1 * t31 * t26 / t20 / t33
  t42 = params.B * (0.1e1 - 0.1e1 / t39)
  t43 = params.E * s0
  t45 = t43 * t28 + 0.1e1
  t47 = 0.1e1 - 0.1e1 / t45
  t49 = t42 * t47 + params.A
  t55 = 0.1e1 / t21 / r0 * params.bx
  t56 = t39 ** 2
  t58 = params.B / t56
  t59 = t19 * r0
  t61 = 0.1e1 / t21 / t59
  t62 = t27 * t61
  t65 = t32 * t19
  t71 = -0.8e1 / 0.3e1 * t25 * t62 - 0.32e2 / 0.3e1 * t31 * t26 / t20 / t65
  t72 = t71 * t47
  t74 = t45 ** 2
  t75 = 0.1e1 / t74
  t76 = t42 * t75
  t77 = t43 * t62
  t80 = t58 * t72 - 0.8e1 / 0.3e1 * t76 * t77
  t85 = 0.1e1 / t21 * params.bx
  t88 = params.B / t56 / t39
  t89 = t71 ** 2
  t90 = t89 * t47
  t95 = t27 / t21 / t32
  t101 = t26 / t20 / t32 / t59
  t104 = 0.88e2 / 0.9e1 * t25 * t95 + 0.608e3 / 0.9e1 * t31 * t101
  t107 = t71 * t75
  t108 = t58 * t107
  t112 = 0.1e1 / t74 / t45
  t113 = t42 * t112
  t114 = params.E ** 2
  t115 = t114 * t30
  t116 = t115 * t101
  t119 = t43 * t95
  t122 = -0.2e1 * t88 * t90 + t58 * t104 * t47 - 0.16e2 / 0.3e1 * t108 * t77 - 0.256e3 / 0.9e1 * t113 * t116 + 0.88e2 / 0.9e1 * t76 * t119
  t126 = t20 * params.bx
  t127 = t56 ** 2
  t129 = params.B / t127
  t130 = t89 * t71
  t138 = t88 * t89 * t75
  t143 = t27 / t21 / t33
  t146 = t32 ** 2
  t149 = t26 / t20 / t146
  t152 = -0.1232e4 / 0.27e2 * t25 * t143 - 0.13376e5 / 0.27e2 * t31 * t149
  t156 = t58 * t104 * t75
  t160 = t58 * t71 * t112
  t165 = t74 ** 2
  t166 = 0.1e1 / t165
  t167 = t42 * t166
  t168 = t114 * params.E
  t169 = t30 * s0
  t170 = t168 * t169
  t172 = 0.1e1 / t146 / t59
  t176 = t115 * t149
  t179 = t43 * t143
  t182 = 0.6e1 * t129 * t130 * t47 - 0.6e1 * t88 * t72 * t104 + 0.16e2 * t138 * t77 + t58 * t152 * t47 - 0.8e1 * t156 * t77 - 0.256e3 / 0.3e1 * t160 * t116 + 0.88e2 / 0.3e1 * t108 * t119 - 0.4096e4 / 0.9e1 * t167 * t170 * t172 + 0.2816e4 / 0.9e1 * t113 * t176 - 0.1232e4 / 0.27e2 * t76 * t179
  t187 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t24 * t49 + t18 * t55 * t80 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t85 * t122 - 0.3e1 / 0.8e1 * t18 * t126 * t182)
  t209 = t26 / t20 / t146 / r0
  t215 = t27 / t21 / t65
  t245 = t114 ** 2
  t246 = t30 ** 2
  t271 = t89 ** 2
  t278 = t104 ** 2
  t292 = -0.512e3 / 0.3e1 * t58 * t104 * t112 * t116 - 0.250624e6 / 0.81e2 * t113 * t115 * t209 + 0.20944e5 / 0.81e2 * t76 * t43 * t215 - 0.64e2 * t129 * t130 * t75 * t77 + 0.1024e4 / 0.3e1 * t88 * t89 * t112 * t116 - 0.32e2 / 0.3e1 * t58 * t152 * t75 * t77 - 0.16384e5 / 0.9e1 * t58 * t71 * t166 * t168 * t169 * t172 + 0.90112e5 / 0.9e1 * t167 * t170 / t146 / t32 - 0.131072e6 / 0.27e2 * t42 / t165 / t45 * t245 * t246 / t21 / t146 / t65 * t27 + 0.176e3 / 0.3e1 * t156 * t119 + 0.11264e5 / 0.9e1 * t160 * t176 - 0.4928e4 / 0.27e2 * t108 * t179 + 0.64e2 * t88 * t107 * t43 * t62 * t104 - 0.352e3 / 0.3e1 * t138 * t119 - 0.24e2 * params.B / t127 / t39 * t271 * t47 + 0.36e2 * t129 * t90 * t104 - 0.6e1 * t88 * t278 * t47 - 0.8e1 * t88 * t72 * t152 + t58 * (0.20944e5 / 0.81e2 * t25 * t215 + 0.334400e6 / 0.81e2 * t31 * t209) * t47
  t297 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t18 * t61 * params.bx * t49 - 0.5e1 / 0.9e1 * t18 * t24 * t80 + t18 * t55 * t122 / 0.2e1 - t18 * t85 * t182 / 0.2e1 - 0.3e1 / 0.8e1 * t18 * t126 * t292)
  v4rho4_0_ = 0.2e1 * r0 * t297 + 0.8e1 * t187

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
  t30 = t5 * t29
  t31 = t6 ** (0.1e1 / 0.3e1)
  t32 = t31 * params.bx
  t33 = params.C * s0
  t34 = r0 ** 2
  t35 = r0 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t38 = 0.1e1 / t36 / t34
  t40 = s0 ** 2
  t41 = params.D * t40
  t42 = t34 ** 2
  t47 = 0.1e1 + t33 * t38 + t41 / t35 / t42 / r0
  t50 = params.B * (0.1e1 - 0.1e1 / t47)
  t51 = params.E * s0
  t53 = t51 * t38 + 0.1e1
  t55 = 0.1e1 - 0.1e1 / t53
  t57 = t50 * t55 + params.A
  t58 = t32 * t57
  t61 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t62 = t61 * f.p.zeta_threshold
  t64 = f.my_piecewise3(t20, t62, t21 * t19)
  t65 = t5 * t64
  t66 = t31 ** 2
  t68 = 0.1e1 / t66 * params.bx
  t69 = t68 * t57
  t71 = t65 * t69 / 0.8e1
  t72 = t47 ** 2
  t74 = params.B / t72
  t75 = t34 * r0
  t77 = 0.1e1 / t36 / t75
  t85 = -0.8e1 / 0.3e1 * t33 * t77 - 0.16e2 / 0.3e1 * t41 / t35 / t42 / t34
  t88 = t53 ** 2
  t89 = 0.1e1 / t88
  t90 = t50 * t89
  t94 = t74 * t85 * t55 - 0.8e1 / 0.3e1 * t90 * t51 * t77
  t95 = t32 * t94
  t99 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t58 - t71 - 0.3e1 / 0.8e1 * t65 * t95)
  t101 = r1 <= f.p.dens_threshold
  t102 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t103 = 0.1e1 + t102
  t104 = t103 <= f.p.zeta_threshold
  t105 = t103 ** (0.1e1 / 0.3e1)
  t107 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t110 = f.my_piecewise3(t104, 0, 0.4e1 / 0.3e1 * t105 * t107)
  t111 = t5 * t110
  t112 = params.C * s2
  t113 = r1 ** 2
  t114 = r1 ** (0.1e1 / 0.3e1)
  t115 = t114 ** 2
  t117 = 0.1e1 / t115 / t113
  t119 = s2 ** 2
  t120 = params.D * t119
  t121 = t113 ** 2
  t126 = 0.1e1 + t112 * t117 + t120 / t114 / t121 / r1
  t129 = params.B * (0.1e1 - 0.1e1 / t126)
  t130 = params.E * s2
  t132 = t130 * t117 + 0.1e1
  t134 = 0.1e1 - 0.1e1 / t132
  t136 = t129 * t134 + params.A
  t137 = t32 * t136
  t141 = f.my_piecewise3(t104, t62, t105 * t103)
  t142 = t5 * t141
  t143 = t68 * t136
  t145 = t142 * t143 / 0.8e1
  t147 = f.my_piecewise3(t101, 0, -0.3e1 / 0.8e1 * t111 * t137 - t145)
  t149 = t21 ** 2
  t150 = 0.1e1 / t149
  t151 = t26 ** 2
  t156 = t16 / t22 / t6
  t158 = -0.2e1 * t23 + 0.2e1 * t156
  t159 = f.my_piecewise5(t10, 0, t14, 0, t158)
  t163 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t150 * t151 + 0.4e1 / 0.3e1 * t21 * t159)
  t167 = t30 * t69
  t173 = 0.1e1 / t66 / t6 * params.bx
  t176 = t65 * t173 * t57 / 0.12e2
  t178 = t65 * t68 * t94
  t183 = t85 ** 2
  t188 = 0.1e1 / t36 / t42
  t193 = 0.1e1 / t35 / t42 / t75
  t208 = params.E ** 2
  t221 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t163 * t58 - t167 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t95 + t176 - t178 / 0.4e1 - 0.3e1 / 0.8e1 * t65 * t32 * (-0.2e1 * params.B / t72 / t47 * t183 * t55 + t74 * (0.88e2 / 0.9e1 * t33 * t188 + 0.304e3 / 0.9e1 * t41 * t193) * t55 - 0.16e2 / 0.3e1 * t74 * t85 * t89 * params.E * s0 * t77 - 0.128e3 / 0.9e1 * t50 / t88 / t53 * t208 * t40 * t193 + 0.88e2 / 0.9e1 * t90 * t51 * t188))
  t222 = t105 ** 2
  t223 = 0.1e1 / t222
  t224 = t107 ** 2
  t228 = f.my_piecewise5(t14, 0, t10, 0, -t158)
  t232 = f.my_piecewise3(t104, 0, 0.4e1 / 0.9e1 * t223 * t224 + 0.4e1 / 0.3e1 * t105 * t228)
  t236 = t111 * t143
  t240 = t142 * t173 * t136 / 0.12e2
  t242 = f.my_piecewise3(t101, 0, -0.3e1 / 0.8e1 * t5 * t232 * t137 - t236 / 0.4e1 + t240)
  d11 = 0.2e1 * t99 + 0.2e1 * t147 + t6 * (t221 + t242)
  t245 = -t7 - t24
  t246 = f.my_piecewise5(t10, 0, t14, 0, t245)
  t249 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t246)
  t250 = t5 * t249
  t254 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t250 * t58 - t71)
  t256 = f.my_piecewise5(t14, 0, t10, 0, -t245)
  t259 = f.my_piecewise3(t104, 0, 0.4e1 / 0.3e1 * t105 * t256)
  t260 = t5 * t259
  t263 = t126 ** 2
  t265 = params.B / t263
  t266 = t113 * r1
  t268 = 0.1e1 / t115 / t266
  t276 = -0.8e1 / 0.3e1 * t112 * t268 - 0.16e2 / 0.3e1 * t120 / t114 / t121 / t113
  t279 = t132 ** 2
  t280 = 0.1e1 / t279
  t281 = t129 * t280
  t285 = t265 * t276 * t134 - 0.8e1 / 0.3e1 * t281 * t130 * t268
  t286 = t32 * t285
  t290 = f.my_piecewise3(t101, 0, -0.3e1 / 0.8e1 * t260 * t137 - t145 - 0.3e1 / 0.8e1 * t142 * t286)
  t294 = 0.2e1 * t156
  t295 = f.my_piecewise5(t10, 0, t14, 0, t294)
  t299 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t150 * t246 * t26 + 0.4e1 / 0.3e1 * t21 * t295)
  t303 = t250 * t69
  t310 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t299 * t58 - t303 / 0.8e1 - 0.3e1 / 0.8e1 * t250 * t95 - t167 / 0.8e1 + t176 - t178 / 0.8e1)
  t314 = f.my_piecewise5(t14, 0, t10, 0, -t294)
  t318 = f.my_piecewise3(t104, 0, 0.4e1 / 0.9e1 * t223 * t256 * t107 + 0.4e1 / 0.3e1 * t105 * t314)
  t322 = t260 * t143
  t328 = t142 * t68 * t285
  t331 = f.my_piecewise3(t101, 0, -0.3e1 / 0.8e1 * t5 * t318 * t137 - t322 / 0.8e1 - t236 / 0.8e1 + t240 - 0.3e1 / 0.8e1 * t111 * t286 - t328 / 0.8e1)
  d12 = t99 + t147 + t254 + t290 + t6 * (t310 + t331)
  t336 = t246 ** 2
  t340 = 0.2e1 * t23 + 0.2e1 * t156
  t341 = f.my_piecewise5(t10, 0, t14, 0, t340)
  t345 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t150 * t336 + 0.4e1 / 0.3e1 * t21 * t341)
  t351 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t345 * t58 - t303 / 0.4e1 + t176)
  t352 = t256 ** 2
  t356 = f.my_piecewise5(t14, 0, t10, 0, -t340)
  t360 = f.my_piecewise3(t104, 0, 0.4e1 / 0.9e1 * t223 * t352 + 0.4e1 / 0.3e1 * t105 * t356)
  t371 = t276 ** 2
  t376 = 0.1e1 / t115 / t121
  t381 = 0.1e1 / t114 / t121 / t266
  t408 = f.my_piecewise3(t101, 0, -0.3e1 / 0.8e1 * t5 * t360 * t137 - t322 / 0.4e1 - 0.3e1 / 0.4e1 * t260 * t286 + t240 - t328 / 0.4e1 - 0.3e1 / 0.8e1 * t142 * t32 * (-0.2e1 * params.B / t263 / t126 * t371 * t134 + t265 * (0.88e2 / 0.9e1 * t112 * t376 + 0.304e3 / 0.9e1 * t120 * t381) * t134 - 0.16e2 / 0.3e1 * t265 * t276 * t280 * params.E * s2 * t268 - 0.128e3 / 0.9e1 * t129 / t279 / t132 * t208 * t119 * t381 + 0.88e2 / 0.9e1 * t281 * t130 * t376))
  d22 = 0.2e1 * t254 + 0.2e1 * t290 + t6 * (t351 + t408)
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
  t42 = t5 * t41
  t43 = t6 ** (0.1e1 / 0.3e1)
  t44 = t43 * params.bx
  t45 = params.C * s0
  t46 = r0 ** 2
  t47 = r0 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t50 = 0.1e1 / t48 / t46
  t52 = s0 ** 2
  t53 = params.D * t52
  t54 = t46 ** 2
  t55 = t54 * r0
  t59 = 0.1e1 + t45 * t50 + t53 / t47 / t55
  t62 = params.B * (0.1e1 - 0.1e1 / t59)
  t63 = params.E * s0
  t65 = t63 * t50 + 0.1e1
  t67 = 0.1e1 - 0.1e1 / t65
  t69 = t62 * t67 + params.A
  t70 = t44 * t69
  t75 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t76 = t5 * t75
  t77 = t43 ** 2
  t79 = 0.1e1 / t77 * params.bx
  t80 = t79 * t69
  t83 = t59 ** 2
  t85 = params.B / t83
  t86 = t46 * r0
  t88 = 0.1e1 / t48 / t86
  t96 = -0.8e1 / 0.3e1 * t45 * t88 - 0.16e2 / 0.3e1 * t53 / t47 / t54 / t46
  t97 = t96 * t67
  t99 = t65 ** 2
  t100 = 0.1e1 / t99
  t101 = t62 * t100
  t105 = t85 * t97 - 0.8e1 / 0.3e1 * t101 * t63 * t88
  t106 = t44 * t105
  t109 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t110 = t109 * f.p.zeta_threshold
  t112 = f.my_piecewise3(t20, t110, t21 * t19)
  t113 = t5 * t112
  t116 = 0.1e1 / t77 / t6 * params.bx
  t117 = t116 * t69
  t120 = t79 * t105
  t125 = params.B / t83 / t59
  t126 = t96 ** 2
  t131 = 0.1e1 / t48 / t54
  t136 = 0.1e1 / t47 / t54 / t86
  t139 = 0.88e2 / 0.9e1 * t45 * t131 + 0.304e3 / 0.9e1 * t53 * t136
  t142 = t85 * t96
  t143 = t100 * params.E
  t145 = t143 * s0 * t88
  t149 = 0.1e1 / t99 / t65
  t150 = t62 * t149
  t151 = params.E ** 2
  t152 = t151 * t52
  t159 = -0.2e1 * t125 * t126 * t67 + t85 * t139 * t67 - 0.16e2 / 0.3e1 * t142 * t145 - 0.128e3 / 0.9e1 * t150 * t152 * t136 + 0.88e2 / 0.9e1 * t101 * t63 * t131
  t160 = t44 * t159
  t164 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t42 * t70 - t76 * t80 / 0.4e1 - 0.3e1 / 0.4e1 * t76 * t106 + t113 * t117 / 0.12e2 - t113 * t120 / 0.4e1 - 0.3e1 / 0.8e1 * t113 * t160)
  t166 = r1 <= f.p.dens_threshold
  t167 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t168 = 0.1e1 + t167
  t169 = t168 <= f.p.zeta_threshold
  t170 = t168 ** (0.1e1 / 0.3e1)
  t171 = t170 ** 2
  t172 = 0.1e1 / t171
  t174 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t175 = t174 ** 2
  t179 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t183 = f.my_piecewise3(t169, 0, 0.4e1 / 0.9e1 * t172 * t175 + 0.4e1 / 0.3e1 * t170 * t179)
  t184 = t5 * t183
  t186 = r1 ** 2
  t187 = r1 ** (0.1e1 / 0.3e1)
  t188 = t187 ** 2
  t190 = 0.1e1 / t188 / t186
  t192 = s2 ** 2
  t194 = t186 ** 2
  t209 = params.A + params.B * (0.1e1 - 0.1e1 / (0.1e1 + params.C * s2 * t190 + params.D * t192 / t187 / t194 / r1)) * (0.1e1 - 0.1e1 / (params.E * s2 * t190 + 0.1e1))
  t210 = t44 * t209
  t215 = f.my_piecewise3(t169, 0, 0.4e1 / 0.3e1 * t170 * t174)
  t216 = t5 * t215
  t217 = t79 * t209
  t221 = f.my_piecewise3(t169, t110, t170 * t168)
  t222 = t5 * t221
  t223 = t116 * t209
  t227 = f.my_piecewise3(t166, 0, -0.3e1 / 0.8e1 * t184 * t210 - t216 * t217 / 0.4e1 + t222 * t223 / 0.12e2)
  t237 = t24 ** 2
  t241 = 0.6e1 * t33 - 0.6e1 * t16 / t237
  t242 = f.my_piecewise5(t10, 0, t14, 0, t241)
  t246 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t242)
  t262 = 0.1e1 / t77 / t24 * params.bx
  t272 = t83 ** 2
  t286 = 0.1e1 / t48 / t55
  t289 = t54 ** 2
  t291 = 0.1e1 / t47 / t289
  t309 = t99 ** 2
  t331 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t246 * t70 - 0.3e1 / 0.8e1 * t42 * t80 - 0.9e1 / 0.8e1 * t42 * t106 + t76 * t117 / 0.4e1 - 0.3e1 / 0.4e1 * t76 * t120 - 0.9e1 / 0.8e1 * t76 * t160 - 0.5e1 / 0.36e2 * t113 * t262 * t69 + t113 * t116 * t105 / 0.4e1 - 0.3e1 / 0.8e1 * t113 * t79 * t159 - 0.3e1 / 0.8e1 * t113 * t44 * (0.6e1 * params.B / t272 * t126 * t96 * t67 - 0.6e1 * t125 * t97 * t139 + 0.16e2 * t125 * t126 * t145 + t85 * (-0.1232e4 / 0.27e2 * t45 * t286 - 0.6688e4 / 0.27e2 * t53 * t291) * t67 - 0.8e1 * t85 * t139 * t145 - 0.128e3 / 0.3e1 * t142 * t149 * t151 * t52 * t136 + 0.88e2 / 0.3e1 * t142 * t143 * s0 * t131 - 0.1024e4 / 0.9e1 * t62 / t309 * t151 * params.E * t52 * s0 / t289 / t86 + 0.1408e4 / 0.9e1 * t150 * t152 * t291 - 0.1232e4 / 0.27e2 * t101 * t63 * t286))
  t341 = f.my_piecewise5(t14, 0, t10, 0, -t241)
  t345 = f.my_piecewise3(t169, 0, -0.8e1 / 0.27e2 / t171 / t168 * t175 * t174 + 0.4e1 / 0.3e1 * t172 * t174 * t179 + 0.4e1 / 0.3e1 * t170 * t341)
  t357 = f.my_piecewise3(t166, 0, -0.3e1 / 0.8e1 * t5 * t345 * t210 - 0.3e1 / 0.8e1 * t184 * t217 + t216 * t223 / 0.4e1 - 0.5e1 / 0.36e2 * t222 * t262 * t209)
  d111 = 0.3e1 * t164 + 0.3e1 * t227 + t6 * (t331 + t357)

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
  t54 = t5 * t53
  t55 = t6 ** (0.1e1 / 0.3e1)
  t56 = t55 * params.bx
  t57 = params.C * s0
  t58 = r0 ** 2
  t59 = r0 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t62 = 0.1e1 / t60 / t58
  t64 = s0 ** 2
  t65 = params.D * t64
  t66 = t58 ** 2
  t67 = t66 * r0
  t71 = 0.1e1 + t57 * t62 + t65 / t59 / t67
  t74 = params.B * (0.1e1 - 0.1e1 / t71)
  t75 = params.E * s0
  t77 = t75 * t62 + 0.1e1
  t79 = 0.1e1 - 0.1e1 / t77
  t81 = t74 * t79 + params.A
  t82 = t56 * t81
  t90 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t91 = t5 * t90
  t92 = t55 ** 2
  t94 = 0.1e1 / t92 * params.bx
  t95 = t94 * t81
  t98 = t71 ** 2
  t100 = params.B / t98
  t101 = t58 * r0
  t103 = 0.1e1 / t60 / t101
  t106 = t66 * t58
  t111 = -0.8e1 / 0.3e1 * t57 * t103 - 0.16e2 / 0.3e1 * t65 / t59 / t106
  t112 = t111 * t79
  t114 = t77 ** 2
  t115 = 0.1e1 / t114
  t116 = t74 * t115
  t120 = t100 * t112 - 0.8e1 / 0.3e1 * t116 * t75 * t103
  t121 = t56 * t120
  t126 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t127 = t5 * t126
  t130 = 0.1e1 / t92 / t6 * params.bx
  t131 = t130 * t81
  t134 = t94 * t120
  t139 = params.B / t98 / t71
  t140 = t111 ** 2
  t141 = t140 * t79
  t145 = 0.1e1 / t60 / t66
  t150 = 0.1e1 / t59 / t66 / t101
  t153 = 0.88e2 / 0.9e1 * t57 * t145 + 0.304e3 / 0.9e1 * t65 * t150
  t156 = t100 * t111
  t157 = t115 * params.E
  t159 = t157 * s0 * t103
  t163 = 0.1e1 / t114 / t77
  t164 = t74 * t163
  t165 = params.E ** 2
  t166 = t165 * t64
  t173 = -0.2e1 * t139 * t141 + t100 * t153 * t79 - 0.16e2 / 0.3e1 * t156 * t159 - 0.128e3 / 0.9e1 * t164 * t166 * t150 + 0.88e2 / 0.9e1 * t116 * t75 * t145
  t174 = t56 * t173
  t177 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t178 = t177 * f.p.zeta_threshold
  t180 = f.my_piecewise3(t20, t178, t21 * t19)
  t181 = t5 * t180
  t184 = 0.1e1 / t92 / t25 * params.bx
  t185 = t184 * t81
  t188 = t130 * t120
  t191 = t94 * t173
  t194 = t98 ** 2
  t196 = params.B / t194
  t197 = t140 * t111
  t204 = t139 * t140
  t208 = 0.1e1 / t60 / t67
  t211 = t66 ** 2
  t213 = 0.1e1 / t59 / t211
  t216 = -0.1232e4 / 0.27e2 * t57 * t208 - 0.6688e4 / 0.27e2 * t65 * t213
  t219 = t100 * t153
  t222 = t163 * t165
  t224 = t222 * t64 * t150
  t228 = t157 * s0 * t145
  t231 = t114 ** 2
  t232 = 0.1e1 / t231
  t233 = t74 * t232
  t234 = t165 * params.E
  t235 = t64 * s0
  t236 = t234 * t235
  t238 = 0.1e1 / t211 / t101
  t248 = 0.6e1 * t196 * t197 * t79 - 0.6e1 * t139 * t112 * t153 + 0.16e2 * t204 * t159 + t100 * t216 * t79 - 0.8e1 * t219 * t159 - 0.128e3 / 0.3e1 * t156 * t224 + 0.88e2 / 0.3e1 * t156 * t228 - 0.1024e4 / 0.9e1 * t233 * t236 * t238 + 0.1408e4 / 0.9e1 * t164 * t166 * t213 - 0.1232e4 / 0.27e2 * t116 * t75 * t208
  t249 = t56 * t248
  t253 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t54 * t82 - 0.3e1 / 0.8e1 * t91 * t95 - 0.9e1 / 0.8e1 * t91 * t121 + t127 * t131 / 0.4e1 - 0.3e1 / 0.4e1 * t127 * t134 - 0.9e1 / 0.8e1 * t127 * t174 - 0.5e1 / 0.36e2 * t181 * t185 + t181 * t188 / 0.4e1 - 0.3e1 / 0.8e1 * t181 * t191 - 0.3e1 / 0.8e1 * t181 * t249)
  t255 = r1 <= f.p.dens_threshold
  t256 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t257 = 0.1e1 + t256
  t258 = t257 <= f.p.zeta_threshold
  t259 = t257 ** (0.1e1 / 0.3e1)
  t260 = t259 ** 2
  t262 = 0.1e1 / t260 / t257
  t264 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t265 = t264 ** 2
  t269 = 0.1e1 / t260
  t270 = t269 * t264
  t272 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t276 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t280 = f.my_piecewise3(t258, 0, -0.8e1 / 0.27e2 * t262 * t265 * t264 + 0.4e1 / 0.3e1 * t270 * t272 + 0.4e1 / 0.3e1 * t259 * t276)
  t281 = t5 * t280
  t283 = r1 ** 2
  t284 = r1 ** (0.1e1 / 0.3e1)
  t285 = t284 ** 2
  t287 = 0.1e1 / t285 / t283
  t289 = s2 ** 2
  t291 = t283 ** 2
  t306 = params.A + params.B * (0.1e1 - 0.1e1 / (0.1e1 + params.C * s2 * t287 + params.D * t289 / t284 / t291 / r1)) * (0.1e1 - 0.1e1 / (params.E * s2 * t287 + 0.1e1))
  t307 = t56 * t306
  t315 = f.my_piecewise3(t258, 0, 0.4e1 / 0.9e1 * t269 * t265 + 0.4e1 / 0.3e1 * t259 * t272)
  t316 = t5 * t315
  t317 = t94 * t306
  t322 = f.my_piecewise3(t258, 0, 0.4e1 / 0.3e1 * t259 * t264)
  t323 = t5 * t322
  t324 = t130 * t306
  t328 = f.my_piecewise3(t258, t178, t259 * t257)
  t329 = t5 * t328
  t330 = t184 * t306
  t334 = f.my_piecewise3(t255, 0, -0.3e1 / 0.8e1 * t281 * t307 - 0.3e1 / 0.8e1 * t316 * t317 + t323 * t324 / 0.4e1 - 0.5e1 / 0.36e2 * t329 * t330)
  t344 = 0.1e1 / t92 / t36 * params.bx
  t348 = t19 ** 2
  t351 = t30 ** 2
  t357 = t41 ** 2
  t366 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t367 = f.my_piecewise5(t10, 0, t14, 0, t366)
  t371 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t348 * t351 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t357 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t367)
  t430 = 0.1e1 / t59 / t211 / r0
  t435 = 0.1e1 / t60 / t106
  t447 = t140 ** 2
  t454 = t153 ** 2
  t471 = t165 ** 2
  t472 = t64 ** 2
  t480 = -0.352e3 / 0.3e1 * t204 * t228 + 0.176e3 / 0.3e1 * t219 * t228 + 0.5632e4 / 0.9e1 * t156 * t222 * t64 * t213 - 0.4928e4 / 0.27e2 * t156 * t157 * s0 * t208 + 0.64e2 * t139 * t111 * t115 * t75 * t103 * t153 - 0.32e2 / 0.3e1 * t100 * t216 * t159 - 0.256e3 / 0.3e1 * t219 * t224 - 0.4096e4 / 0.9e1 * t156 * t232 * t234 * t235 * t238 + 0.22528e5 / 0.9e1 * t233 * t236 / t211 / t66 - 0.125312e6 / 0.81e2 * t164 * t166 * t430 + 0.20944e5 / 0.81e2 * t116 * t75 * t435 - 0.64e2 * t196 * t197 * t159 + 0.512e3 / 0.3e1 * t204 * t224 - 0.24e2 * params.B / t194 / t71 * t447 * t79 + 0.36e2 * t196 * t141 * t153 - 0.6e1 * t139 * t454 * t79 - 0.8e1 * t139 * t112 * t216 + t100 * (0.20944e5 / 0.81e2 * t57 * t435 + 0.167200e6 / 0.81e2 * t65 * t430) * t79 - 0.32768e5 / 0.27e2 * t74 / t231 / t77 * t471 * t472 / t60 / t211 / t106
  t484 = -t54 * t95 / 0.2e1 + t91 * t131 / 0.2e1 - 0.5e1 / 0.9e1 * t127 * t185 + 0.10e2 / 0.27e2 * t181 * t344 * t81 - 0.3e1 / 0.8e1 * t5 * t371 * t82 - 0.3e1 / 0.2e1 * t54 * t121 - 0.3e1 / 0.2e1 * t91 * t134 - 0.9e1 / 0.4e1 * t91 * t174 + t127 * t188 - 0.3e1 / 0.2e1 * t127 * t191 - 0.3e1 / 0.2e1 * t127 * t249 - 0.5e1 / 0.9e1 * t181 * t184 * t120 + t181 * t130 * t173 / 0.2e1 - t181 * t94 * t248 / 0.2e1 - 0.3e1 / 0.8e1 * t181 * t56 * t480
  t485 = f.my_piecewise3(t1, 0, t484)
  t486 = t257 ** 2
  t489 = t265 ** 2
  t495 = t272 ** 2
  t501 = f.my_piecewise5(t14, 0, t10, 0, -t366)
  t505 = f.my_piecewise3(t258, 0, 0.40e2 / 0.81e2 / t260 / t486 * t489 - 0.16e2 / 0.9e1 * t262 * t265 * t272 + 0.4e1 / 0.3e1 * t269 * t495 + 0.16e2 / 0.9e1 * t270 * t276 + 0.4e1 / 0.3e1 * t259 * t501)
  t519 = f.my_piecewise3(t255, 0, -0.3e1 / 0.8e1 * t5 * t505 * t307 - t281 * t317 / 0.2e1 + t316 * t324 / 0.2e1 - 0.5e1 / 0.9e1 * t323 * t330 + 0.10e2 / 0.27e2 * t329 * t344 * t306)
  d1111 = 0.4e1 * t253 + 0.4e1 * t334 + t6 * (t485 + t519)

  res = {'v4rho4': d1111}
  return res
