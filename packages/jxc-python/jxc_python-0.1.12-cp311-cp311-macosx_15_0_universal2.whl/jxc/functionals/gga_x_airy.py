"""Generated from gga_x_airy.mpl."""

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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a10_raw = params.a10
  if isinstance(params_a10_raw, (str, bytes, dict)):
    params_a10 = params_a10_raw
  else:
    try:
      params_a10_seq = list(params_a10_raw)
    except TypeError:
      params_a10 = params_a10_raw
    else:
      params_a10_seq = np.asarray(params_a10_seq, dtype=np.float64)
      params_a10 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a10_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
  params_a3_raw = params.a3
  if isinstance(params_a3_raw, (str, bytes, dict)):
    params_a3 = params_a3_raw
  else:
    try:
      params_a3_seq = list(params_a3_raw)
    except TypeError:
      params_a3 = params_a3_raw
    else:
      params_a3_seq = np.asarray(params_a3_seq, dtype=np.float64)
      params_a3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a3_seq))
  params_a4_raw = params.a4
  if isinstance(params_a4_raw, (str, bytes, dict)):
    params_a4 = params_a4_raw
  else:
    try:
      params_a4_seq = list(params_a4_raw)
    except TypeError:
      params_a4 = params_a4_raw
    else:
      params_a4_seq = np.asarray(params_a4_seq, dtype=np.float64)
      params_a4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a4_seq))
  params_a5_raw = params.a5
  if isinstance(params_a5_raw, (str, bytes, dict)):
    params_a5 = params_a5_raw
  else:
    try:
      params_a5_seq = list(params_a5_raw)
    except TypeError:
      params_a5 = params_a5_raw
    else:
      params_a5_seq = np.asarray(params_a5_seq, dtype=np.float64)
      params_a5 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a5_seq))
  params_a6_raw = params.a6
  if isinstance(params_a6_raw, (str, bytes, dict)):
    params_a6 = params_a6_raw
  else:
    try:
      params_a6_seq = list(params_a6_raw)
    except TypeError:
      params_a6 = params_a6_raw
    else:
      params_a6_seq = np.asarray(params_a6_seq, dtype=np.float64)
      params_a6 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a6_seq))
  params_a7_raw = params.a7
  if isinstance(params_a7_raw, (str, bytes, dict)):
    params_a7 = params_a7_raw
  else:
    try:
      params_a7_seq = list(params_a7_raw)
    except TypeError:
      params_a7 = params_a7_raw
    else:
      params_a7_seq = np.asarray(params_a7_seq, dtype=np.float64)
      params_a7 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a7_seq))
  params_a8_raw = params.a8
  if isinstance(params_a8_raw, (str, bytes, dict)):
    params_a8 = params_a8_raw
  else:
    try:
      params_a8_seq = list(params_a8_raw)
    except TypeError:
      params_a8 = params_a8_raw
    else:
      params_a8_seq = np.asarray(params_a8_seq, dtype=np.float64)
      params_a8 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a8_seq))
  params_a9_raw = params.a9
  if isinstance(params_a9_raw, (str, bytes, dict)):
    params_a9 = params_a9_raw
  else:
    try:
      params_a9_seq = list(params_a9_raw)
    except TypeError:
      params_a9 = params_a9_raw
    else:
      params_a9_seq = np.asarray(params_a9_seq, dtype=np.float64)
      params_a9 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a9_seq))

  airy_f0 = lambda s: params_a1 * s ** params_a2 / (1 + params_a3 * s ** params_a2) ** params_a4 + (1 - params_a5 * s ** params_a6 + params_a7 * s ** params_a8) / (1 + params_a9 * s ** params_a10)

  airy_f = lambda x: airy_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, airy_f, rs, zeta, xs0, xs1)

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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a10_raw = params.a10
  if isinstance(params_a10_raw, (str, bytes, dict)):
    params_a10 = params_a10_raw
  else:
    try:
      params_a10_seq = list(params_a10_raw)
    except TypeError:
      params_a10 = params_a10_raw
    else:
      params_a10_seq = np.asarray(params_a10_seq, dtype=np.float64)
      params_a10 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a10_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
  params_a3_raw = params.a3
  if isinstance(params_a3_raw, (str, bytes, dict)):
    params_a3 = params_a3_raw
  else:
    try:
      params_a3_seq = list(params_a3_raw)
    except TypeError:
      params_a3 = params_a3_raw
    else:
      params_a3_seq = np.asarray(params_a3_seq, dtype=np.float64)
      params_a3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a3_seq))
  params_a4_raw = params.a4
  if isinstance(params_a4_raw, (str, bytes, dict)):
    params_a4 = params_a4_raw
  else:
    try:
      params_a4_seq = list(params_a4_raw)
    except TypeError:
      params_a4 = params_a4_raw
    else:
      params_a4_seq = np.asarray(params_a4_seq, dtype=np.float64)
      params_a4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a4_seq))
  params_a5_raw = params.a5
  if isinstance(params_a5_raw, (str, bytes, dict)):
    params_a5 = params_a5_raw
  else:
    try:
      params_a5_seq = list(params_a5_raw)
    except TypeError:
      params_a5 = params_a5_raw
    else:
      params_a5_seq = np.asarray(params_a5_seq, dtype=np.float64)
      params_a5 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a5_seq))
  params_a6_raw = params.a6
  if isinstance(params_a6_raw, (str, bytes, dict)):
    params_a6 = params_a6_raw
  else:
    try:
      params_a6_seq = list(params_a6_raw)
    except TypeError:
      params_a6 = params_a6_raw
    else:
      params_a6_seq = np.asarray(params_a6_seq, dtype=np.float64)
      params_a6 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a6_seq))
  params_a7_raw = params.a7
  if isinstance(params_a7_raw, (str, bytes, dict)):
    params_a7 = params_a7_raw
  else:
    try:
      params_a7_seq = list(params_a7_raw)
    except TypeError:
      params_a7 = params_a7_raw
    else:
      params_a7_seq = np.asarray(params_a7_seq, dtype=np.float64)
      params_a7 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a7_seq))
  params_a8_raw = params.a8
  if isinstance(params_a8_raw, (str, bytes, dict)):
    params_a8 = params_a8_raw
  else:
    try:
      params_a8_seq = list(params_a8_raw)
    except TypeError:
      params_a8 = params_a8_raw
    else:
      params_a8_seq = np.asarray(params_a8_seq, dtype=np.float64)
      params_a8 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a8_seq))
  params_a9_raw = params.a9
  if isinstance(params_a9_raw, (str, bytes, dict)):
    params_a9 = params_a9_raw
  else:
    try:
      params_a9_seq = list(params_a9_raw)
    except TypeError:
      params_a9 = params_a9_raw
    else:
      params_a9_seq = np.asarray(params_a9_seq, dtype=np.float64)
      params_a9 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a9_seq))

  airy_f0 = lambda s: params_a1 * s ** params_a2 / (1 + params_a3 * s ** params_a2) ** params_a4 + (1 - params_a5 * s ** params_a6 + params_a7 * s ** params_a8) / (1 + params_a9 * s ** params_a10)

  airy_f = lambda x: airy_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, airy_f, rs, zeta, xs0, xs1)

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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a10_raw = params.a10
  if isinstance(params_a10_raw, (str, bytes, dict)):
    params_a10 = params_a10_raw
  else:
    try:
      params_a10_seq = list(params_a10_raw)
    except TypeError:
      params_a10 = params_a10_raw
    else:
      params_a10_seq = np.asarray(params_a10_seq, dtype=np.float64)
      params_a10 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a10_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
  params_a3_raw = params.a3
  if isinstance(params_a3_raw, (str, bytes, dict)):
    params_a3 = params_a3_raw
  else:
    try:
      params_a3_seq = list(params_a3_raw)
    except TypeError:
      params_a3 = params_a3_raw
    else:
      params_a3_seq = np.asarray(params_a3_seq, dtype=np.float64)
      params_a3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a3_seq))
  params_a4_raw = params.a4
  if isinstance(params_a4_raw, (str, bytes, dict)):
    params_a4 = params_a4_raw
  else:
    try:
      params_a4_seq = list(params_a4_raw)
    except TypeError:
      params_a4 = params_a4_raw
    else:
      params_a4_seq = np.asarray(params_a4_seq, dtype=np.float64)
      params_a4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a4_seq))
  params_a5_raw = params.a5
  if isinstance(params_a5_raw, (str, bytes, dict)):
    params_a5 = params_a5_raw
  else:
    try:
      params_a5_seq = list(params_a5_raw)
    except TypeError:
      params_a5 = params_a5_raw
    else:
      params_a5_seq = np.asarray(params_a5_seq, dtype=np.float64)
      params_a5 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a5_seq))
  params_a6_raw = params.a6
  if isinstance(params_a6_raw, (str, bytes, dict)):
    params_a6 = params_a6_raw
  else:
    try:
      params_a6_seq = list(params_a6_raw)
    except TypeError:
      params_a6 = params_a6_raw
    else:
      params_a6_seq = np.asarray(params_a6_seq, dtype=np.float64)
      params_a6 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a6_seq))
  params_a7_raw = params.a7
  if isinstance(params_a7_raw, (str, bytes, dict)):
    params_a7 = params_a7_raw
  else:
    try:
      params_a7_seq = list(params_a7_raw)
    except TypeError:
      params_a7 = params_a7_raw
    else:
      params_a7_seq = np.asarray(params_a7_seq, dtype=np.float64)
      params_a7 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a7_seq))
  params_a8_raw = params.a8
  if isinstance(params_a8_raw, (str, bytes, dict)):
    params_a8 = params_a8_raw
  else:
    try:
      params_a8_seq = list(params_a8_raw)
    except TypeError:
      params_a8 = params_a8_raw
    else:
      params_a8_seq = np.asarray(params_a8_seq, dtype=np.float64)
      params_a8 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a8_seq))
  params_a9_raw = params.a9
  if isinstance(params_a9_raw, (str, bytes, dict)):
    params_a9 = params_a9_raw
  else:
    try:
      params_a9_seq = list(params_a9_raw)
    except TypeError:
      params_a9 = params_a9_raw
    else:
      params_a9_seq = np.asarray(params_a9_seq, dtype=np.float64)
      params_a9 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a9_seq))

  airy_f0 = lambda s: params_a1 * s ** params_a2 / (1 + params_a3 * s ** params_a2) ** params_a4 + (1 - params_a5 * s ** params_a6 + params_a7 * s ** params_a8) / (1 + params_a9 * s ** params_a10)

  airy_f = lambda x: airy_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, airy_f, rs, zeta, xs0, xs1)

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
  t29 = t28 ** 2
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t33 = t29 / t31
  t34 = jnp.sqrt(s0)
  t35 = r0 ** (0.1e1 / 0.3e1)
  t40 = t33 * t34 / t35 / r0 / 0.12e2
  t41 = t40 ** params.a2
  t42 = params.a1 * t41
  t44 = params.a3 * t41 + 0.1e1
  t45 = t44 ** params.a4
  t46 = 0.1e1 / t45
  t48 = t40 ** params.a6
  t49 = params.a5 * t48
  t50 = t40 ** params.a8
  t51 = params.a7 * t50
  t52 = 0.1e1 - t49 + t51
  t53 = t40 ** params.a10
  t55 = params.a9 * t53 + 0.1e1
  t56 = 0.1e1 / t55
  t58 = t42 * t46 + t52 * t56
  t62 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t58)
  t63 = r1 <= f.p.dens_threshold
  t64 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t65 = 0.1e1 + t64
  t66 = t65 <= f.p.zeta_threshold
  t67 = t65 ** (0.1e1 / 0.3e1)
  t69 = f.my_piecewise3(t66, t22, t67 * t65)
  t70 = t69 * t26
  t71 = jnp.sqrt(s2)
  t72 = r1 ** (0.1e1 / 0.3e1)
  t77 = t33 * t71 / t72 / r1 / 0.12e2
  t78 = t77 ** params.a2
  t79 = params.a1 * t78
  t81 = params.a3 * t78 + 0.1e1
  t82 = t81 ** params.a4
  t83 = 0.1e1 / t82
  t85 = t77 ** params.a6
  t86 = params.a5 * t85
  t87 = t77 ** params.a8
  t88 = params.a7 * t87
  t89 = 0.1e1 - t86 + t88
  t90 = t77 ** params.a10
  t92 = params.a9 * t90 + 0.1e1
  t93 = 0.1e1 / t92
  t95 = t79 * t83 + t89 * t93
  t99 = f.my_piecewise3(t63, 0, -0.3e1 / 0.8e1 * t5 * t70 * t95)
  t100 = t6 ** 2
  t102 = t16 / t100
  t103 = t7 - t102
  t104 = f.my_piecewise5(t10, 0, t14, 0, t103)
  t107 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t104)
  t112 = t26 ** 2
  t113 = 0.1e1 / t112
  t117 = t5 * t25 * t113 * t58 / 0.8e1
  t118 = 0.1e1 / r0
  t123 = t41 ** 2
  t126 = params.a1 * t123 * t46 * params.a4
  t127 = params.a3 * params.a2
  t128 = 0.1e1 / t44
  t140 = t55 ** 2
  t143 = t52 / t140 * params.a9
  t144 = t53 * params.a10
  t153 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t107 * t26 * t58 - t117 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.4e1 / 0.3e1 * t42 * params.a2 * t118 * t46 + 0.4e1 / 0.3e1 * t126 * t127 * t118 * t128 + (0.4e1 / 0.3e1 * t49 * params.a6 * t118 - 0.4e1 / 0.3e1 * t51 * params.a8 * t118) * t56 + 0.4e1 / 0.3e1 * t143 * t144 * t118))
  t155 = f.my_piecewise5(t14, 0, t10, 0, -t103)
  t158 = f.my_piecewise3(t66, 0, 0.4e1 / 0.3e1 * t67 * t155)
  t166 = t5 * t69 * t113 * t95 / 0.8e1
  t168 = f.my_piecewise3(t63, 0, -0.3e1 / 0.8e1 * t5 * t158 * t26 * t95 - t166)
  vrho_0_ = t62 + t99 + t6 * (t153 + t168)
  t171 = -t7 - t102
  t172 = f.my_piecewise5(t10, 0, t14, 0, t171)
  t175 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t172)
  t181 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t175 * t26 * t58 - t117)
  t183 = f.my_piecewise5(t14, 0, t10, 0, -t171)
  t186 = f.my_piecewise3(t66, 0, 0.4e1 / 0.3e1 * t67 * t183)
  t191 = 0.1e1 / r1
  t196 = t78 ** 2
  t199 = params.a1 * t196 * t83 * params.a4
  t200 = 0.1e1 / t81
  t212 = t92 ** 2
  t215 = t89 / t212 * params.a9
  t216 = t90 * params.a10
  t225 = f.my_piecewise3(t63, 0, -0.3e1 / 0.8e1 * t5 * t186 * t26 * t95 - t166 - 0.3e1 / 0.8e1 * t5 * t70 * (-0.4e1 / 0.3e1 * t79 * params.a2 * t191 * t83 + 0.4e1 / 0.3e1 * t199 * t127 * t191 * t200 + (0.4e1 / 0.3e1 * t86 * params.a6 * t191 - 0.4e1 / 0.3e1 * t88 * params.a8 * t191) * t93 + 0.4e1 / 0.3e1 * t215 * t216 * t191))
  vrho_1_ = t62 + t99 + t6 * (t181 + t225)
  t228 = 0.1e1 / s0
  t251 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t42 * params.a2 * t228 * t46 / 0.2e1 - t126 * t127 * t228 * t128 / 0.2e1 + (-t49 * params.a6 * t228 / 0.2e1 + t51 * params.a8 * t228 / 0.2e1) * t56 - t143 * t144 * t228 / 0.2e1))
  vsigma_0_ = t6 * t251
  vsigma_1_ = 0.0e0
  t252 = 0.1e1 / s2
  t275 = f.my_piecewise3(t63, 0, -0.3e1 / 0.8e1 * t5 * t70 * (t79 * params.a2 * t252 * t83 / 0.2e1 - t199 * t127 * t252 * t200 / 0.2e1 + (-t86 * params.a6 * t252 / 0.2e1 + t88 * params.a8 * t252 / 0.2e1) * t93 - t215 * t216 * t252 / 0.2e1))
  vsigma_2_ = t6 * t275
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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a10_raw = params.a10
  if isinstance(params_a10_raw, (str, bytes, dict)):
    params_a10 = params_a10_raw
  else:
    try:
      params_a10_seq = list(params_a10_raw)
    except TypeError:
      params_a10 = params_a10_raw
    else:
      params_a10_seq = np.asarray(params_a10_seq, dtype=np.float64)
      params_a10 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a10_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
  params_a3_raw = params.a3
  if isinstance(params_a3_raw, (str, bytes, dict)):
    params_a3 = params_a3_raw
  else:
    try:
      params_a3_seq = list(params_a3_raw)
    except TypeError:
      params_a3 = params_a3_raw
    else:
      params_a3_seq = np.asarray(params_a3_seq, dtype=np.float64)
      params_a3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a3_seq))
  params_a4_raw = params.a4
  if isinstance(params_a4_raw, (str, bytes, dict)):
    params_a4 = params_a4_raw
  else:
    try:
      params_a4_seq = list(params_a4_raw)
    except TypeError:
      params_a4 = params_a4_raw
    else:
      params_a4_seq = np.asarray(params_a4_seq, dtype=np.float64)
      params_a4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a4_seq))
  params_a5_raw = params.a5
  if isinstance(params_a5_raw, (str, bytes, dict)):
    params_a5 = params_a5_raw
  else:
    try:
      params_a5_seq = list(params_a5_raw)
    except TypeError:
      params_a5 = params_a5_raw
    else:
      params_a5_seq = np.asarray(params_a5_seq, dtype=np.float64)
      params_a5 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a5_seq))
  params_a6_raw = params.a6
  if isinstance(params_a6_raw, (str, bytes, dict)):
    params_a6 = params_a6_raw
  else:
    try:
      params_a6_seq = list(params_a6_raw)
    except TypeError:
      params_a6 = params_a6_raw
    else:
      params_a6_seq = np.asarray(params_a6_seq, dtype=np.float64)
      params_a6 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a6_seq))
  params_a7_raw = params.a7
  if isinstance(params_a7_raw, (str, bytes, dict)):
    params_a7 = params_a7_raw
  else:
    try:
      params_a7_seq = list(params_a7_raw)
    except TypeError:
      params_a7 = params_a7_raw
    else:
      params_a7_seq = np.asarray(params_a7_seq, dtype=np.float64)
      params_a7 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a7_seq))
  params_a8_raw = params.a8
  if isinstance(params_a8_raw, (str, bytes, dict)):
    params_a8 = params_a8_raw
  else:
    try:
      params_a8_seq = list(params_a8_raw)
    except TypeError:
      params_a8 = params_a8_raw
    else:
      params_a8_seq = np.asarray(params_a8_seq, dtype=np.float64)
      params_a8 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a8_seq))
  params_a9_raw = params.a9
  if isinstance(params_a9_raw, (str, bytes, dict)):
    params_a9 = params_a9_raw
  else:
    try:
      params_a9_seq = list(params_a9_raw)
    except TypeError:
      params_a9 = params_a9_raw
    else:
      params_a9_seq = np.asarray(params_a9_seq, dtype=np.float64)
      params_a9 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a9_seq))

  airy_f0 = lambda s: params_a1 * s ** params_a2 / (1 + params_a3 * s ** params_a2) ** params_a4 + (1 - params_a5 * s ** params_a6 + params_a7 * s ** params_a8) / (1 + params_a9 * s ** params_a10)

  airy_f = lambda x: airy_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, airy_f, rs, zeta, xs0, xs1)

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
  t21 = t20 ** 2
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t26 = jnp.sqrt(s0)
  t27 = 2 ** (0.1e1 / 0.3e1)
  t33 = t21 / t23 * t26 * t27 / t18 / r0 / 0.12e2
  t34 = t33 ** params.a2
  t35 = params.a1 * t34
  t37 = params.a3 * t34 + 0.1e1
  t38 = t37 ** params.a4
  t39 = 0.1e1 / t38
  t41 = t33 ** params.a6
  t42 = params.a5 * t41
  t43 = t33 ** params.a8
  t44 = params.a7 * t43
  t45 = 0.1e1 - t42 + t44
  t46 = t33 ** params.a10
  t48 = params.a9 * t46 + 0.1e1
  t49 = 0.1e1 / t48
  t51 = t35 * t39 + t45 * t49
  t55 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t51)
  t56 = t18 ** 2
  t62 = 0.1e1 / r0
  t67 = t34 ** 2
  t70 = params.a1 * t67 * t39 * params.a4
  t71 = params.a3 * params.a2
  t72 = 0.1e1 / t37
  t84 = t48 ** 2
  t87 = t45 / t84 * params.a9
  t88 = t46 * params.a10
  t97 = f.my_piecewise3(t2, 0, -t6 * t17 / t56 * t51 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.4e1 / 0.3e1 * t35 * params.a2 * t62 * t39 + 0.4e1 / 0.3e1 * t70 * t71 * t62 * t72 + (0.4e1 / 0.3e1 * t42 * params.a6 * t62 - 0.4e1 / 0.3e1 * t44 * params.a8 * t62) * t49 + 0.4e1 / 0.3e1 * t87 * t88 * t62))
  vrho_0_ = 0.2e1 * r0 * t97 + 0.2e1 * t55
  t100 = 0.1e1 / s0
  t123 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t35 * params.a2 * t100 * t39 / 0.2e1 - t70 * t71 * t100 * t72 / 0.2e1 + (-t42 * params.a6 * t100 / 0.2e1 + t44 * params.a8 * t100 / 0.2e1) * t49 - t87 * t88 * t100 / 0.2e1))
  vsigma_0_ = 0.2e1 * r0 * t123
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
  t23 = t22 ** 2
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t28 = jnp.sqrt(s0)
  t29 = 2 ** (0.1e1 / 0.3e1)
  t35 = t23 / t25 * t28 * t29 / t18 / r0 / 0.12e2
  t36 = t35 ** params.a2
  t37 = params.a1 * t36
  t39 = params.a3 * t36 + 0.1e1
  t40 = t39 ** params.a4
  t41 = 0.1e1 / t40
  t43 = t35 ** params.a6
  t44 = params.a5 * t43
  t45 = t35 ** params.a8
  t46 = params.a7 * t45
  t47 = 0.1e1 - t44 + t46
  t48 = t35 ** params.a10
  t50 = params.a9 * t48 + 0.1e1
  t51 = 0.1e1 / t50
  t53 = t37 * t41 + t47 * t51
  t57 = t17 * t18
  t58 = 0.1e1 / r0
  t63 = t36 ** 2
  t64 = params.a1 * t63
  t65 = t41 * params.a4
  t66 = t64 * t65
  t67 = params.a3 * params.a2
  t68 = 0.1e1 / t39
  t78 = 0.4e1 / 0.3e1 * t44 * params.a6 * t58 - 0.4e1 / 0.3e1 * t46 * params.a8 * t58
  t80 = t50 ** 2
  t81 = 0.1e1 / t80
  t83 = t47 * t81 * params.a9
  t84 = t48 * params.a10
  t85 = t84 * t58
  t88 = -0.4e1 / 0.3e1 * t37 * params.a2 * t58 * t41 + 0.4e1 / 0.3e1 * t66 * t67 * t58 * t68 + t78 * t51 + 0.4e1 / 0.3e1 * t83 * t85
  t93 = f.my_piecewise3(t2, 0, -t6 * t21 * t53 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t57 * t88)
  t104 = params.a2 ** 2
  t105 = r0 ** 2
  t106 = 0.1e1 / t105
  t107 = t104 * t106
  t117 = t65 * params.a3 * t68
  t121 = params.a1 * t63 * t36
  t122 = params.a4 ** 2
  t124 = t121 * t41 * t122
  t125 = params.a3 ** 2
  t126 = t125 * t104
  t127 = t39 ** 2
  t128 = 0.1e1 / t127
  t130 = t126 * t106 * t128
  t137 = t121 * t65
  t140 = params.a6 ** 2
  t147 = params.a8 ** 2
  t157 = t78 * t81 * params.a9
  t163 = params.a9 ** 2
  t164 = t47 / t80 / t50 * t163
  t165 = t48 ** 2
  t166 = params.a10 ** 2
  t167 = t165 * t166
  t171 = t48 * t166
  t178 = 0.16e2 / 0.9e1 * t37 * t107 * t41 + 0.4e1 / 0.3e1 * t37 * params.a2 * t106 * t41 - 0.16e2 / 0.3e1 * t64 * t107 * t117 + 0.16e2 / 0.9e1 * t124 * t130 - 0.4e1 / 0.3e1 * t66 * t67 * t106 * t68 + 0.16e2 / 0.9e1 * t137 * t130 + (-0.16e2 / 0.9e1 * t44 * t140 * t106 - 0.4e1 / 0.3e1 * t44 * params.a6 * t106 + 0.16e2 / 0.9e1 * t46 * t147 * t106 + 0.4e1 / 0.3e1 * t46 * params.a8 * t106) * t51 + 0.8e1 / 0.3e1 * t157 * t85 + 0.32e2 / 0.9e1 * t164 * t167 * t106 - 0.16e2 / 0.9e1 * t83 * t171 * t106 - 0.4e1 / 0.3e1 * t83 * t84 * t106
  t183 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t53 / 0.12e2 - t6 * t21 * t88 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t57 * t178)
  v2rho2_0_ = 0.2e1 * r0 * t183 + 0.4e1 * t93
  t186 = 0.1e1 / s0
  t200 = -t44 * params.a6 * t186 / 0.2e1 + t46 * params.a8 * t186 / 0.2e1
  t202 = t84 * t186
  t205 = t37 * params.a2 * t186 * t41 / 0.2e1 - t66 * t67 * t186 * t68 / 0.2e1 + t200 * t51 - t83 * t202 / 0.2e1
  t209 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t57 * t205)
  t214 = t58 * t186
  t227 = t126 * t186 * t128 * t58
  t242 = t200 * t81 * params.a9
  t258 = f.my_piecewise3(t2, 0, -t6 * t21 * t205 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t57 * (-0.2e1 / 0.3e1 * t37 * t104 * t214 * t41 + 0.2e1 * t64 * t104 * t186 * t65 * params.a3 * t58 * t68 - 0.2e1 / 0.3e1 * t124 * t227 - 0.2e1 / 0.3e1 * t137 * t227 + (0.2e1 / 0.3e1 * t44 * t140 * t58 * t186 - 0.2e1 / 0.3e1 * t46 * t147 * t58 * t186) * t51 + 0.4e1 / 0.3e1 * t242 * t85 - t157 * t202 / 0.2e1 - 0.4e1 / 0.3e1 * t164 * t167 * t214 + 0.2e1 / 0.3e1 * t83 * t171 * t214))
  v2rhosigma_0_ = 0.2e1 * r0 * t258 + 0.2e1 * t209
  t261 = s0 ** 2
  t262 = 0.1e1 / t261
  t263 = t104 * t262
  t275 = t126 * t262 * t128
  t308 = t37 * t263 * t41 / 0.4e1 - t37 * params.a2 * t262 * t41 / 0.2e1 - 0.3e1 / 0.4e1 * t64 * t263 * t117 + t124 * t275 / 0.4e1 + t66 * t67 * t262 * t68 / 0.2e1 + t137 * t275 / 0.4e1 + (-t44 * t140 * t262 / 0.4e1 + t44 * params.a6 * t262 / 0.2e1 + t46 * t147 * t262 / 0.4e1 - t46 * params.a8 * t262 / 0.2e1) * t51 - t242 * t202 + t164 * t167 * t262 / 0.2e1 - t83 * t171 * t262 / 0.4e1 + t83 * t84 * t262 / 0.2e1
  t312 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t57 * t308)
  v2sigma2_0_ = 0.2e1 * r0 * t312
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
  t24 = t23 ** 2
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t29 = jnp.sqrt(s0)
  t30 = 2 ** (0.1e1 / 0.3e1)
  t36 = t24 / t26 * t29 * t30 / t18 / r0 / 0.12e2
  t37 = t36 ** params.a2
  t38 = params.a1 * t37
  t40 = params.a3 * t37 + 0.1e1
  t41 = t40 ** params.a4
  t42 = 0.1e1 / t41
  t44 = t36 ** params.a6
  t45 = params.a5 * t44
  t46 = t36 ** params.a8
  t47 = params.a7 * t46
  t48 = 0.1e1 - t45 + t47
  t49 = t36 ** params.a10
  t51 = params.a9 * t49 + 0.1e1
  t52 = 0.1e1 / t51
  t54 = t38 * t42 + t48 * t52
  t59 = t17 / t19
  t60 = 0.1e1 / r0
  t65 = t37 ** 2
  t66 = params.a1 * t65
  t67 = t42 * params.a4
  t68 = t66 * t67
  t69 = params.a3 * params.a2
  t70 = 0.1e1 / t40
  t80 = 0.4e1 / 0.3e1 * t45 * params.a6 * t60 - 0.4e1 / 0.3e1 * t47 * params.a8 * t60
  t82 = t51 ** 2
  t83 = 0.1e1 / t82
  t85 = t48 * t83 * params.a9
  t86 = t49 * params.a10
  t87 = t86 * t60
  t90 = -0.4e1 / 0.3e1 * t38 * params.a2 * t60 * t42 + 0.4e1 / 0.3e1 * t68 * t69 * t60 * t70 + t80 * t52 + 0.4e1 / 0.3e1 * t85 * t87
  t94 = t17 * t18
  t95 = params.a2 ** 2
  t96 = r0 ** 2
  t97 = 0.1e1 / t96
  t98 = t95 * t97
  t108 = t67 * params.a3 * t70
  t112 = params.a1 * t65 * t37
  t113 = params.a4 ** 2
  t114 = t42 * t113
  t115 = t112 * t114
  t116 = params.a3 ** 2
  t117 = t116 * t95
  t118 = t40 ** 2
  t119 = 0.1e1 / t118
  t121 = t117 * t97 * t119
  t128 = t112 * t67
  t131 = params.a6 ** 2
  t138 = params.a8 ** 2
  t145 = -0.16e2 / 0.9e1 * t45 * t131 * t97 - 0.4e1 / 0.3e1 * t45 * params.a6 * t97 + 0.16e2 / 0.9e1 * t47 * t138 * t97 + 0.4e1 / 0.3e1 * t47 * params.a8 * t97
  t148 = t80 * t83 * params.a9
  t152 = 0.1e1 / t82 / t51
  t154 = params.a9 ** 2
  t155 = t48 * t152 * t154
  t156 = t49 ** 2
  t157 = params.a10 ** 2
  t158 = t156 * t157
  t159 = t158 * t97
  t162 = t49 * t157
  t163 = t162 * t97
  t166 = t86 * t97
  t169 = 0.16e2 / 0.9e1 * t38 * t98 * t42 + 0.4e1 / 0.3e1 * t38 * params.a2 * t97 * t42 - 0.16e2 / 0.3e1 * t66 * t98 * t108 + 0.16e2 / 0.9e1 * t115 * t121 - 0.4e1 / 0.3e1 * t68 * t69 * t97 * t70 + 0.16e2 / 0.9e1 * t128 * t121 + t145 * t52 + 0.8e1 / 0.3e1 * t148 * t87 + 0.32e2 / 0.9e1 * t155 * t159 - 0.16e2 / 0.9e1 * t85 * t163 - 0.4e1 / 0.3e1 * t85 * t166
  t174 = f.my_piecewise3(t2, 0, t6 * t22 * t54 / 0.12e2 - t6 * t59 * t90 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t94 * t169)
  t190 = 0.1e1 / t96 / r0
  t224 = t117 * t190 * t119
  t227 = t65 ** 2
  t228 = params.a1 * t227
  t231 = t95 * params.a2
  t236 = t116 * params.a3 * t231 * t190 / t118 / t40
  t239 = t231 * t190
  t243 = t95 * t190
  t247 = t112 * t239
  t248 = t116 * t119
  t260 = (0.64e2 / 0.27e2 * t45 * t131 * params.a6 * t190 + 0.16e2 / 0.3e1 * t45 * t131 * t190 + 0.8e1 / 0.3e1 * t45 * params.a6 * t190 - 0.64e2 / 0.27e2 * t47 * t138 * params.a8 * t190 - 0.16e2 / 0.3e1 * t47 * t138 * t190 - 0.8e1 / 0.3e1 * t47 * params.a8 * t190) * t52 - 0.4e1 * t148 * t166 - 0.32e2 / 0.3e1 * t155 * t158 * t190 + 0.16e2 / 0.3e1 * t85 * t162 * t190 + 0.8e1 / 0.3e1 * t85 * t86 * t190 - 0.16e2 / 0.3e1 * t128 * t224 + 0.128e3 / 0.27e2 * t228 * t67 * t236 + 0.448e3 / 0.27e2 * t66 * t239 * t108 + 0.16e2 * t66 * t243 * t108 - 0.128e3 / 0.9e1 * t247 * t114 * t248 - 0.128e3 / 0.9e1 * t247 * t67 * t248 + 0.64e2 / 0.27e2 * t228 * t42 * t113 * params.a4 * t236
  t290 = t82 ** 2
  t296 = t157 * params.a10
  t309 = 0.64e2 / 0.9e1 * t228 * t114 * t236 - 0.16e2 / 0.3e1 * t115 * t224 + 0.8e1 / 0.3e1 * t68 * t69 * t190 * t70 - 0.64e2 / 0.27e2 * t38 * t239 * t42 - 0.16e2 / 0.3e1 * t38 * t243 * t42 - 0.8e1 / 0.3e1 * t38 * params.a2 * t190 * t42 + 0.4e1 * t145 * t83 * params.a9 * t87 + 0.32e2 / 0.3e1 * t80 * t152 * t154 * t159 - 0.16e2 / 0.3e1 * t148 * t163 + 0.128e3 / 0.9e1 * t48 / t290 * t154 * params.a9 * t156 * t49 * t296 * t190 - 0.128e3 / 0.9e1 * t155 * t156 * t296 * t190 + 0.64e2 / 0.27e2 * t85 * t49 * t296 * t190
  t315 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 / t19 / t96 * t54 + t6 * t22 * t90 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t59 * t169 - 0.3e1 / 0.8e1 * t6 * t94 * (t260 + t309))
  v3rho3_0_ = 0.2e1 * r0 * t315 + 0.6e1 * t174

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
  t23 = t17 / t20 / t18
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t30 = jnp.sqrt(s0)
  t31 = 2 ** (0.1e1 / 0.3e1)
  t37 = t25 / t27 * t30 * t31 / t19 / r0 / 0.12e2
  t38 = t37 ** params.a2
  t39 = params.a1 * t38
  t41 = params.a3 * t38 + 0.1e1
  t42 = t41 ** params.a4
  t43 = 0.1e1 / t42
  t45 = t37 ** params.a6
  t46 = params.a5 * t45
  t47 = t37 ** params.a8
  t48 = params.a7 * t47
  t49 = 0.1e1 - t46 + t48
  t50 = t37 ** params.a10
  t52 = params.a9 * t50 + 0.1e1
  t53 = 0.1e1 / t52
  t55 = t39 * t43 + t49 * t53
  t61 = t17 / t20 / r0
  t62 = 0.1e1 / r0
  t67 = t38 ** 2
  t68 = params.a1 * t67
  t69 = t43 * params.a4
  t70 = t68 * t69
  t71 = params.a3 * params.a2
  t72 = 0.1e1 / t41
  t82 = 0.4e1 / 0.3e1 * t46 * params.a6 * t62 - 0.4e1 / 0.3e1 * t48 * params.a8 * t62
  t84 = t52 ** 2
  t85 = 0.1e1 / t84
  t87 = t49 * t85 * params.a9
  t88 = t50 * params.a10
  t89 = t88 * t62
  t92 = -0.4e1 / 0.3e1 * t39 * params.a2 * t62 * t43 + 0.4e1 / 0.3e1 * t70 * t71 * t62 * t72 + t82 * t53 + 0.4e1 / 0.3e1 * t87 * t89
  t97 = t17 / t20
  t98 = params.a2 ** 2
  t99 = 0.1e1 / t18
  t100 = t98 * t99
  t110 = t69 * params.a3 * t72
  t114 = params.a1 * t67 * t38
  t115 = params.a4 ** 2
  t116 = t43 * t115
  t117 = t114 * t116
  t118 = params.a3 ** 2
  t119 = t118 * t98
  t120 = t41 ** 2
  t121 = 0.1e1 / t120
  t123 = t119 * t99 * t121
  t130 = t114 * t69
  t133 = params.a6 ** 2
  t140 = params.a8 ** 2
  t147 = -0.16e2 / 0.9e1 * t46 * t133 * t99 - 0.4e1 / 0.3e1 * t46 * params.a6 * t99 + 0.16e2 / 0.9e1 * t48 * t140 * t99 + 0.4e1 / 0.3e1 * t48 * params.a8 * t99
  t150 = t82 * t85 * params.a9
  t154 = 0.1e1 / t84 / t52
  t156 = params.a9 ** 2
  t157 = t49 * t154 * t156
  t158 = t50 ** 2
  t159 = params.a10 ** 2
  t160 = t158 * t159
  t161 = t160 * t99
  t164 = t50 * t159
  t165 = t164 * t99
  t168 = t88 * t99
  t171 = 0.16e2 / 0.9e1 * t39 * t100 * t43 + 0.4e1 / 0.3e1 * t39 * params.a2 * t99 * t43 - 0.16e2 / 0.3e1 * t68 * t100 * t110 + 0.16e2 / 0.9e1 * t117 * t123 - 0.4e1 / 0.3e1 * t70 * t71 * t99 * t72 + 0.16e2 / 0.9e1 * t130 * t123 + t147 * t53 + 0.8e1 / 0.3e1 * t150 * t89 + 0.32e2 / 0.9e1 * t157 * t161 - 0.16e2 / 0.9e1 * t87 * t165 - 0.4e1 / 0.3e1 * t87 * t168
  t175 = t17 * t19
  t176 = t133 * params.a6
  t177 = t18 * r0
  t178 = 0.1e1 / t177
  t188 = t140 * params.a8
  t198 = 0.64e2 / 0.27e2 * t46 * t176 * t178 + 0.16e2 / 0.3e1 * t46 * t133 * t178 + 0.8e1 / 0.3e1 * t46 * params.a6 * t178 - 0.64e2 / 0.27e2 * t48 * t188 * t178 - 0.16e2 / 0.3e1 * t48 * t140 * t178 - 0.8e1 / 0.3e1 * t48 * params.a8 * t178
  t202 = t160 * t178
  t205 = t164 * t178
  t208 = t88 * t178
  t212 = t119 * t178 * t121
  t215 = t67 ** 2
  t216 = params.a1 * t215
  t217 = t216 * t69
  t218 = t118 * params.a3
  t219 = t98 * params.a2
  t220 = t218 * t219
  t222 = 0.1e1 / t120 / t41
  t224 = t220 * t178 * t222
  t227 = t219 * t178
  t231 = t98 * t178
  t235 = t114 * t227
  t236 = t118 * t121
  t237 = t116 * t236
  t240 = t69 * t236
  t244 = t43 * t115 * params.a4
  t245 = t216 * t244
  t248 = t198 * t53 - 0.4e1 * t150 * t168 - 0.32e2 / 0.3e1 * t157 * t202 + 0.16e2 / 0.3e1 * t87 * t205 + 0.8e1 / 0.3e1 * t87 * t208 - 0.16e2 / 0.3e1 * t130 * t212 + 0.128e3 / 0.27e2 * t217 * t224 + 0.448e3 / 0.27e2 * t68 * t227 * t110 + 0.16e2 * t68 * t231 * t110 - 0.128e3 / 0.9e1 * t235 * t237 - 0.128e3 / 0.9e1 * t235 * t240 + 0.64e2 / 0.27e2 * t245 * t224
  t249 = t216 * t116
  t269 = t147 * t85 * params.a9
  t273 = t82 * t154 * t156
  t278 = t84 ** 2
  t279 = 0.1e1 / t278
  t281 = t156 * params.a9
  t282 = t49 * t279 * t281
  t283 = t158 * t50
  t284 = t159 * params.a10
  t285 = t283 * t284
  t286 = t285 * t178
  t289 = t158 * t284
  t290 = t289 * t178
  t293 = t50 * t284
  t294 = t293 * t178
  t297 = 0.64e2 / 0.9e1 * t249 * t224 - 0.16e2 / 0.3e1 * t117 * t212 + 0.8e1 / 0.3e1 * t70 * t71 * t178 * t72 - 0.64e2 / 0.27e2 * t39 * t227 * t43 - 0.16e2 / 0.3e1 * t39 * t231 * t43 - 0.8e1 / 0.3e1 * t39 * params.a2 * t178 * t43 + 0.4e1 * t269 * t89 + 0.32e2 / 0.3e1 * t273 * t161 - 0.16e2 / 0.3e1 * t150 * t165 + 0.128e3 / 0.9e1 * t282 * t286 - 0.128e3 / 0.9e1 * t157 * t290 + 0.64e2 / 0.27e2 * t87 * t294
  t298 = t248 + t297
  t303 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t55 + t6 * t61 * t92 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t97 * t171 - 0.3e1 / 0.8e1 * t6 * t175 * t298)
  t320 = t18 ** 2
  t321 = 0.1e1 / t320
  t330 = t98 ** 2
  t331 = t330 * t321
  t332 = t216 * t331
  t333 = t218 * t222
  t341 = params.a1 * t215 * t38
  t342 = t115 ** 2
  t345 = t118 ** 2
  t347 = t120 ** 2
  t350 = t345 * t330 * t321 / t347
  t357 = t321 * t121
  t361 = t321 * t222
  t362 = t220 * t361
  t371 = -0.176e3 / 0.9e1 * t87 * t164 * t321 - 0.8e1 * t87 * t88 * t321 + 0.32e2 / 0.3e1 * t150 * t208 - 0.2560e4 / 0.81e2 * t332 * t244 * t333 - 0.2560e4 / 0.27e2 * t332 * t116 * t333 + 0.256e3 / 0.81e2 * t341 * t43 * t342 * t350 + 0.512e3 / 0.27e2 * t341 * t244 * t350 + 0.256e3 / 0.3e1 * t130 * t118 * t219 * t357 - 0.128e3 / 0.3e1 * t249 * t362 - 0.256e3 / 0.9e1 * t217 * t362 - 0.5120e4 / 0.81e2 * t217 * t218 * t330 * t361
  t378 = t119 * t357
  t389 = t219 * t321
  t393 = t98 * t321
  t400 = t114 * t331
  t405 = 0.2816e4 / 0.81e2 * t341 * t116 * t350 + 0.512e3 / 0.27e2 * t341 * t69 * t350 + 0.176e3 / 0.9e1 * t117 * t378 - 0.8e1 * t70 * t71 * t321 * t72 - 0.128e3 / 0.9e1 * t245 * t362 + 0.176e3 / 0.9e1 * t130 * t378 - 0.896e3 / 0.9e1 * t68 * t389 * t110 - 0.176e3 / 0.3e1 * t68 * t393 * t110 - 0.1280e4 / 0.27e2 * t68 * t331 * t110 + 0.6400e4 / 0.81e2 * t400 * t237 + 0.6400e4 / 0.81e2 * t400 * t240
  t423 = t133 ** 2
  t436 = t140 ** 2
  t458 = t156 ** 2
  t460 = t158 ** 2
  t461 = t159 ** 2
  t474 = 0.256e3 / 0.3e1 * t114 * t389 * t237 + 0.256e3 / 0.81e2 * t39 * t331 * t43 + 0.128e3 / 0.9e1 * t39 * t389 * t43 + 0.176e3 / 0.9e1 * t39 * t393 * t43 + 0.8e1 * t39 * params.a2 * t321 * t43 + (-0.256e3 / 0.81e2 * t46 * t423 * t321 - 0.128e3 / 0.9e1 * t46 * t176 * t321 - 0.176e3 / 0.9e1 * t46 * t133 * t321 - 0.8e1 * t46 * params.a6 * t321 + 0.256e3 / 0.81e2 * t48 * t436 * t321 + 0.128e3 / 0.9e1 * t48 * t188 * t321 + 0.176e3 / 0.9e1 * t48 * t140 * t321 + 0.8e1 * t48 * params.a8 * t321) * t53 - 0.512e3 / 0.9e1 * t273 * t290 + 0.256e3 / 0.27e2 * t150 * t294 + 0.2048e4 / 0.27e2 * t49 / t278 / t52 * t458 * t460 * t461 * t321 - 0.1024e4 / 0.9e1 * t282 * t283 * t461 * t321 + 0.3584e4 / 0.81e2 * t157 * t158 * t461 * t321
  t511 = -0.256e3 / 0.81e2 * t87 * t50 * t461 * t321 + 0.352e3 / 0.9e1 * t157 * t160 * t321 + 0.64e2 / 0.3e1 * t150 * t205 - 0.256e3 / 0.3e1 * t282 * t285 * t321 + 0.256e3 / 0.3e1 * t157 * t289 * t321 - 0.128e3 / 0.9e1 * t87 * t293 * t321 + 0.64e2 / 0.3e1 * t147 * t154 * t156 * t161 - 0.32e2 / 0.3e1 * t269 * t165 + 0.512e3 / 0.9e1 * t82 * t279 * t281 * t286 + 0.16e2 / 0.3e1 * t198 * t85 * params.a9 * t89 - 0.8e1 * t269 * t168 - 0.128e3 / 0.3e1 * t273 * t202
  t518 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 / t20 / t177 * t55 - 0.5e1 / 0.9e1 * t6 * t23 * t92 + t6 * t61 * t171 / 0.2e1 - t6 * t97 * t298 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t175 * (t371 + t405 + t474 + t511))
  v4rho4_0_ = 0.2e1 * r0 * t518 + 0.8e1 * t303

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
  t33 = t32 ** 2
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t37 = t33 / t35
  t38 = jnp.sqrt(s0)
  t39 = r0 ** (0.1e1 / 0.3e1)
  t44 = t37 * t38 / t39 / r0 / 0.12e2
  t45 = t44 ** params.a2
  t46 = params.a1 * t45
  t48 = params.a3 * t45 + 0.1e1
  t49 = t48 ** params.a4
  t50 = 0.1e1 / t49
  t52 = t44 ** params.a6
  t53 = params.a5 * t52
  t54 = t44 ** params.a8
  t55 = params.a7 * t54
  t56 = 0.1e1 - t53 + t55
  t57 = t44 ** params.a10
  t59 = params.a9 * t57 + 0.1e1
  t60 = 0.1e1 / t59
  t62 = t46 * t50 + t56 * t60
  t66 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t67 = t66 * f.p.zeta_threshold
  t69 = f.my_piecewise3(t20, t67, t21 * t19)
  t70 = t30 ** 2
  t71 = 0.1e1 / t70
  t72 = t69 * t71
  t75 = t5 * t72 * t62 / 0.8e1
  t76 = t69 * t30
  t77 = 0.1e1 / r0
  t82 = t45 ** 2
  t83 = params.a1 * t82
  t84 = t50 * params.a4
  t85 = t83 * t84
  t86 = params.a3 * params.a2
  t87 = 0.1e1 / t48
  t97 = 0.4e1 / 0.3e1 * t53 * params.a6 * t77 - 0.4e1 / 0.3e1 * t55 * params.a8 * t77
  t99 = t59 ** 2
  t100 = 0.1e1 / t99
  t102 = t56 * t100 * params.a9
  t103 = t57 * params.a10
  t104 = t103 * t77
  t107 = -0.4e1 / 0.3e1 * t46 * params.a2 * t77 * t50 + 0.4e1 / 0.3e1 * t85 * t86 * t77 * t87 + t97 * t60 + 0.4e1 / 0.3e1 * t102 * t104
  t112 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t62 - t75 - 0.3e1 / 0.8e1 * t5 * t76 * t107)
  t114 = r1 <= f.p.dens_threshold
  t115 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t116 = 0.1e1 + t115
  t117 = t116 <= f.p.zeta_threshold
  t118 = t116 ** (0.1e1 / 0.3e1)
  t120 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t123 = f.my_piecewise3(t117, 0, 0.4e1 / 0.3e1 * t118 * t120)
  t124 = t123 * t30
  t125 = jnp.sqrt(s2)
  t126 = r1 ** (0.1e1 / 0.3e1)
  t131 = t37 * t125 / t126 / r1 / 0.12e2
  t132 = t131 ** params.a2
  t133 = params.a1 * t132
  t135 = params.a3 * t132 + 0.1e1
  t136 = t135 ** params.a4
  t137 = 0.1e1 / t136
  t139 = t131 ** params.a6
  t140 = params.a5 * t139
  t141 = t131 ** params.a8
  t142 = params.a7 * t141
  t143 = 0.1e1 - t140 + t142
  t144 = t131 ** params.a10
  t146 = params.a9 * t144 + 0.1e1
  t147 = 0.1e1 / t146
  t149 = t133 * t137 + t143 * t147
  t154 = f.my_piecewise3(t117, t67, t118 * t116)
  t155 = t154 * t71
  t158 = t5 * t155 * t149 / 0.8e1
  t160 = f.my_piecewise3(t114, 0, -0.3e1 / 0.8e1 * t5 * t124 * t149 - t158)
  t162 = t21 ** 2
  t163 = 0.1e1 / t162
  t164 = t26 ** 2
  t169 = t16 / t22 / t6
  t171 = -0.2e1 * t23 + 0.2e1 * t169
  t172 = f.my_piecewise5(t10, 0, t14, 0, t171)
  t176 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t163 * t164 + 0.4e1 / 0.3e1 * t21 * t172)
  t183 = t5 * t29 * t71 * t62
  t189 = 0.1e1 / t70 / t6
  t193 = t5 * t69 * t189 * t62 / 0.12e2
  t195 = t5 * t72 * t107
  t197 = params.a2 ** 2
  t198 = r0 ** 2
  t199 = 0.1e1 / t198
  t200 = t197 * t199
  t214 = params.a1 * t82 * t45
  t215 = params.a4 ** 2
  t218 = params.a3 ** 2
  t219 = t218 * t197
  t220 = t48 ** 2
  t223 = t219 * t199 / t220
  t233 = params.a6 ** 2
  t240 = params.a8 ** 2
  t256 = params.a9 ** 2
  t258 = t57 ** 2
  t259 = params.a10 ** 2
  t271 = 0.16e2 / 0.9e1 * t46 * t200 * t50 + 0.4e1 / 0.3e1 * t46 * params.a2 * t199 * t50 - 0.16e2 / 0.3e1 * t83 * t200 * t84 * params.a3 * t87 + 0.16e2 / 0.9e1 * t214 * t50 * t215 * t223 - 0.4e1 / 0.3e1 * t85 * t86 * t199 * t87 + 0.16e2 / 0.9e1 * t214 * t84 * t223 + (-0.16e2 / 0.9e1 * t53 * t233 * t199 - 0.4e1 / 0.3e1 * t53 * params.a6 * t199 + 0.16e2 / 0.9e1 * t55 * t240 * t199 + 0.4e1 / 0.3e1 * t55 * params.a8 * t199) * t60 + 0.8e1 / 0.3e1 * t97 * t100 * params.a9 * t104 + 0.32e2 / 0.9e1 * t56 / t99 / t59 * t256 * t258 * t259 * t199 - 0.16e2 / 0.9e1 * t102 * t57 * t259 * t199 - 0.4e1 / 0.3e1 * t102 * t103 * t199
  t276 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t176 * t30 * t62 - t183 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t107 + t193 - t195 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t76 * t271)
  t277 = t118 ** 2
  t278 = 0.1e1 / t277
  t279 = t120 ** 2
  t283 = f.my_piecewise5(t14, 0, t10, 0, -t171)
  t287 = f.my_piecewise3(t117, 0, 0.4e1 / 0.9e1 * t278 * t279 + 0.4e1 / 0.3e1 * t118 * t283)
  t294 = t5 * t123 * t71 * t149
  t299 = t5 * t154 * t189 * t149 / 0.12e2
  t301 = f.my_piecewise3(t114, 0, -0.3e1 / 0.8e1 * t5 * t287 * t30 * t149 - t294 / 0.4e1 + t299)
  d11 = 0.2e1 * t112 + 0.2e1 * t160 + t6 * (t276 + t301)
  t304 = -t7 - t24
  t305 = f.my_piecewise5(t10, 0, t14, 0, t304)
  t308 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t305)
  t309 = t308 * t30
  t314 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t309 * t62 - t75)
  t316 = f.my_piecewise5(t14, 0, t10, 0, -t304)
  t319 = f.my_piecewise3(t117, 0, 0.4e1 / 0.3e1 * t118 * t316)
  t320 = t319 * t30
  t324 = t154 * t30
  t325 = 0.1e1 / r1
  t330 = t132 ** 2
  t331 = params.a1 * t330
  t332 = t137 * params.a4
  t333 = t331 * t332
  t334 = 0.1e1 / t135
  t344 = 0.4e1 / 0.3e1 * t140 * params.a6 * t325 - 0.4e1 / 0.3e1 * t142 * params.a8 * t325
  t346 = t146 ** 2
  t347 = 0.1e1 / t346
  t349 = t143 * t347 * params.a9
  t350 = t144 * params.a10
  t351 = t350 * t325
  t354 = -0.4e1 / 0.3e1 * t133 * params.a2 * t325 * t137 + 0.4e1 / 0.3e1 * t333 * t86 * t325 * t334 + t344 * t147 + 0.4e1 / 0.3e1 * t349 * t351
  t359 = f.my_piecewise3(t114, 0, -0.3e1 / 0.8e1 * t5 * t320 * t149 - t158 - 0.3e1 / 0.8e1 * t5 * t324 * t354)
  t363 = 0.2e1 * t169
  t364 = f.my_piecewise5(t10, 0, t14, 0, t363)
  t368 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t163 * t305 * t26 + 0.4e1 / 0.3e1 * t21 * t364)
  t375 = t5 * t308 * t71 * t62
  t383 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t368 * t30 * t62 - t375 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t309 * t107 - t183 / 0.8e1 + t193 - t195 / 0.8e1)
  t387 = f.my_piecewise5(t14, 0, t10, 0, -t363)
  t391 = f.my_piecewise3(t117, 0, 0.4e1 / 0.9e1 * t278 * t316 * t120 + 0.4e1 / 0.3e1 * t118 * t387)
  t398 = t5 * t319 * t71 * t149
  t405 = t5 * t155 * t354
  t408 = f.my_piecewise3(t114, 0, -0.3e1 / 0.8e1 * t5 * t391 * t30 * t149 - t398 / 0.8e1 - t294 / 0.8e1 + t299 - 0.3e1 / 0.8e1 * t5 * t124 * t354 - t405 / 0.8e1)
  d12 = t112 + t160 + t314 + t359 + t6 * (t383 + t408)
  t413 = t305 ** 2
  t417 = 0.2e1 * t23 + 0.2e1 * t169
  t418 = f.my_piecewise5(t10, 0, t14, 0, t417)
  t422 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t163 * t413 + 0.4e1 / 0.3e1 * t21 * t418)
  t429 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t422 * t30 * t62 - t375 / 0.4e1 + t193)
  t430 = t316 ** 2
  t434 = f.my_piecewise5(t14, 0, t10, 0, -t417)
  t438 = f.my_piecewise3(t117, 0, 0.4e1 / 0.9e1 * t278 * t430 + 0.4e1 / 0.3e1 * t118 * t434)
  t448 = r1 ** 2
  t449 = 0.1e1 / t448
  t450 = t197 * t449
  t464 = params.a1 * t330 * t132
  t467 = t135 ** 2
  t470 = t219 * t449 / t467
  t502 = t144 ** 2
  t514 = 0.16e2 / 0.9e1 * t133 * t450 * t137 + 0.4e1 / 0.3e1 * t133 * params.a2 * t449 * t137 - 0.16e2 / 0.3e1 * t331 * t450 * t332 * params.a3 * t334 + 0.16e2 / 0.9e1 * t464 * t137 * t215 * t470 - 0.4e1 / 0.3e1 * t333 * t86 * t449 * t334 + 0.16e2 / 0.9e1 * t464 * t332 * t470 + (-0.16e2 / 0.9e1 * t140 * t233 * t449 - 0.4e1 / 0.3e1 * t140 * params.a6 * t449 + 0.16e2 / 0.9e1 * t142 * t240 * t449 + 0.4e1 / 0.3e1 * t142 * params.a8 * t449) * t147 + 0.8e1 / 0.3e1 * t344 * t347 * params.a9 * t351 + 0.32e2 / 0.9e1 * t143 / t346 / t146 * t256 * t502 * t259 * t449 - 0.16e2 / 0.9e1 * t349 * t144 * t259 * t449 - 0.4e1 / 0.3e1 * t349 * t350 * t449
  t519 = f.my_piecewise3(t114, 0, -0.3e1 / 0.8e1 * t5 * t438 * t30 * t149 - t398 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t320 * t354 + t299 - t405 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t324 * t514)
  d22 = 0.2e1 * t314 + 0.2e1 * t359 + t6 * (t429 + t519)
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
  t45 = t44 ** 2
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t49 = t45 / t47
  t50 = jnp.sqrt(s0)
  t51 = r0 ** (0.1e1 / 0.3e1)
  t56 = t49 * t50 / t51 / r0 / 0.12e2
  t57 = t56 ** params.a2
  t58 = params.a1 * t57
  t60 = params.a3 * t57 + 0.1e1
  t61 = t60 ** params.a4
  t62 = 0.1e1 / t61
  t64 = t56 ** params.a6
  t65 = params.a5 * t64
  t66 = t56 ** params.a8
  t67 = params.a7 * t66
  t68 = 0.1e1 - t65 + t67
  t69 = t56 ** params.a10
  t71 = params.a9 * t69 + 0.1e1
  t72 = 0.1e1 / t71
  t74 = t58 * t62 + t68 * t72
  t80 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t81 = t42 ** 2
  t82 = 0.1e1 / t81
  t83 = t80 * t82
  t87 = t80 * t42
  t88 = 0.1e1 / r0
  t93 = t57 ** 2
  t94 = params.a1 * t93
  t95 = t62 * params.a4
  t96 = t94 * t95
  t97 = params.a3 * params.a2
  t98 = 0.1e1 / t60
  t108 = 0.4e1 / 0.3e1 * t65 * params.a6 * t88 - 0.4e1 / 0.3e1 * t67 * params.a8 * t88
  t110 = t71 ** 2
  t111 = 0.1e1 / t110
  t113 = t68 * t111 * params.a9
  t114 = t69 * params.a10
  t115 = t114 * t88
  t118 = -0.4e1 / 0.3e1 * t58 * params.a2 * t88 * t62 + 0.4e1 / 0.3e1 * t96 * t97 * t88 * t98 + t108 * t72 + 0.4e1 / 0.3e1 * t113 * t115
  t122 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t123 = t122 * f.p.zeta_threshold
  t125 = f.my_piecewise3(t20, t123, t21 * t19)
  t127 = 0.1e1 / t81 / t6
  t128 = t125 * t127
  t132 = t125 * t82
  t136 = t125 * t42
  t137 = params.a2 ** 2
  t138 = r0 ** 2
  t139 = 0.1e1 / t138
  t140 = t137 * t139
  t150 = t95 * params.a3 * t98
  t154 = params.a1 * t93 * t57
  t155 = params.a4 ** 2
  t156 = t62 * t155
  t157 = t154 * t156
  t158 = params.a3 ** 2
  t159 = t158 * t137
  t160 = t60 ** 2
  t161 = 0.1e1 / t160
  t163 = t159 * t139 * t161
  t170 = t154 * t95
  t173 = params.a6 ** 2
  t180 = params.a8 ** 2
  t187 = -0.16e2 / 0.9e1 * t65 * t173 * t139 - 0.4e1 / 0.3e1 * t65 * params.a6 * t139 + 0.16e2 / 0.9e1 * t67 * t180 * t139 + 0.4e1 / 0.3e1 * t67 * params.a8 * t139
  t190 = t108 * t111 * params.a9
  t194 = 0.1e1 / t110 / t71
  t196 = params.a9 ** 2
  t197 = t68 * t194 * t196
  t198 = t69 ** 2
  t199 = params.a10 ** 2
  t200 = t198 * t199
  t201 = t200 * t139
  t204 = t69 * t199
  t205 = t204 * t139
  t208 = t114 * t139
  t211 = 0.16e2 / 0.9e1 * t58 * t140 * t62 + 0.4e1 / 0.3e1 * t58 * params.a2 * t139 * t62 - 0.16e2 / 0.3e1 * t94 * t140 * t150 + 0.16e2 / 0.9e1 * t157 * t163 - 0.4e1 / 0.3e1 * t96 * t97 * t139 * t98 + 0.16e2 / 0.9e1 * t170 * t163 + t187 * t72 + 0.8e1 / 0.3e1 * t190 * t115 + 0.32e2 / 0.9e1 * t197 * t201 - 0.16e2 / 0.9e1 * t113 * t205 - 0.4e1 / 0.3e1 * t113 * t208
  t216 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t74 - t5 * t83 * t74 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t87 * t118 + t5 * t128 * t74 / 0.12e2 - t5 * t132 * t118 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t136 * t211)
  t218 = r1 <= f.p.dens_threshold
  t219 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t220 = 0.1e1 + t219
  t221 = t220 <= f.p.zeta_threshold
  t222 = t220 ** (0.1e1 / 0.3e1)
  t223 = t222 ** 2
  t224 = 0.1e1 / t223
  t226 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t227 = t226 ** 2
  t231 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t235 = f.my_piecewise3(t221, 0, 0.4e1 / 0.9e1 * t224 * t227 + 0.4e1 / 0.3e1 * t222 * t231)
  t237 = jnp.sqrt(s2)
  t238 = r1 ** (0.1e1 / 0.3e1)
  t243 = t49 * t237 / t238 / r1 / 0.12e2
  t244 = t243 ** params.a2
  t248 = (params.a3 * t244 + 0.1e1) ** params.a4
  t251 = t243 ** params.a6
  t253 = t243 ** params.a8
  t256 = t243 ** params.a10
  t261 = params.a1 * t244 / t248 + (-params.a5 * t251 + params.a7 * t253 + 0.1e1) / (params.a9 * t256 + 0.1e1)
  t267 = f.my_piecewise3(t221, 0, 0.4e1 / 0.3e1 * t222 * t226)
  t273 = f.my_piecewise3(t221, t123, t222 * t220)
  t279 = f.my_piecewise3(t218, 0, -0.3e1 / 0.8e1 * t5 * t235 * t42 * t261 - t5 * t267 * t82 * t261 / 0.4e1 + t5 * t273 * t127 * t261 / 0.12e2)
  t289 = t24 ** 2
  t293 = 0.6e1 * t33 - 0.6e1 * t16 / t289
  t294 = f.my_piecewise5(t10, 0, t14, 0, t293)
  t298 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t294)
  t321 = 0.1e1 / t81 / t24
  t334 = 0.1e1 / t138 / r0
  t367 = t137 * params.a2
  t368 = t367 * t334
  t373 = t159 * t334 * t161
  t376 = t93 ** 2
  t377 = params.a1 * t376
  t384 = t158 * params.a3 * t367 * t334 / t160 / t60
  t390 = t137 * t334
  t394 = t154 * t368
  t395 = t158 * t161
  t402 = (0.64e2 / 0.27e2 * t65 * t173 * params.a6 * t334 + 0.16e2 / 0.3e1 * t65 * t173 * t334 + 0.8e1 / 0.3e1 * t65 * params.a6 * t334 - 0.64e2 / 0.27e2 * t67 * t180 * params.a8 * t334 - 0.16e2 / 0.3e1 * t67 * t180 * t334 - 0.8e1 / 0.3e1 * t67 * params.a8 * t334) * t72 - 0.4e1 * t190 * t208 - 0.32e2 / 0.3e1 * t197 * t200 * t334 + 0.16e2 / 0.3e1 * t113 * t204 * t334 + 0.8e1 / 0.3e1 * t113 * t114 * t334 - 0.64e2 / 0.27e2 * t58 * t368 * t62 - 0.16e2 / 0.3e1 * t170 * t373 + 0.128e3 / 0.27e2 * t377 * t95 * t384 + 0.448e3 / 0.27e2 * t94 * t368 * t150 + 0.16e2 * t94 * t390 * t150 - 0.128e3 / 0.9e1 * t394 * t156 * t395 - 0.128e3 / 0.9e1 * t394 * t95 * t395
  t428 = t110 ** 2
  t434 = t199 * params.a10
  t453 = 0.64e2 / 0.27e2 * t377 * t62 * t155 * params.a4 * t384 + 0.64e2 / 0.9e1 * t377 * t156 * t384 - 0.16e2 / 0.3e1 * t58 * t390 * t62 - 0.8e1 / 0.3e1 * t58 * params.a2 * t334 * t62 + 0.4e1 * t187 * t111 * params.a9 * t115 + 0.32e2 / 0.3e1 * t108 * t194 * t196 * t201 - 0.16e2 / 0.3e1 * t190 * t205 + 0.128e3 / 0.9e1 * t68 / t428 * t196 * params.a9 * t198 * t69 * t434 * t334 - 0.128e3 / 0.9e1 * t197 * t198 * t434 * t334 + 0.64e2 / 0.27e2 * t113 * t69 * t434 * t334 - 0.16e2 / 0.3e1 * t157 * t373 + 0.8e1 / 0.3e1 * t96 * t97 * t334 * t98
  t459 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t298 * t42 * t74 - 0.3e1 / 0.8e1 * t5 * t41 * t82 * t74 - 0.9e1 / 0.8e1 * t5 * t43 * t118 + t5 * t80 * t127 * t74 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t83 * t118 - 0.9e1 / 0.8e1 * t5 * t87 * t211 - 0.5e1 / 0.36e2 * t5 * t125 * t321 * t74 + t5 * t128 * t118 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t132 * t211 - 0.3e1 / 0.8e1 * t5 * t136 * (t402 + t453))
  t469 = f.my_piecewise5(t14, 0, t10, 0, -t293)
  t473 = f.my_piecewise3(t221, 0, -0.8e1 / 0.27e2 / t223 / t220 * t227 * t226 + 0.4e1 / 0.3e1 * t224 * t226 * t231 + 0.4e1 / 0.3e1 * t222 * t469)
  t491 = f.my_piecewise3(t218, 0, -0.3e1 / 0.8e1 * t5 * t473 * t42 * t261 - 0.3e1 / 0.8e1 * t5 * t235 * t82 * t261 + t5 * t267 * t127 * t261 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t273 * t321 * t261)
  d111 = 0.3e1 * t216 + 0.3e1 * t279 + t6 * (t459 + t491)

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
  t57 = t56 ** 2
  t58 = jnp.pi ** 2
  t59 = t58 ** (0.1e1 / 0.3e1)
  t61 = t57 / t59
  t62 = jnp.sqrt(s0)
  t63 = r0 ** (0.1e1 / 0.3e1)
  t68 = t61 * t62 / t63 / r0 / 0.12e2
  t69 = t68 ** params.a2
  t70 = params.a1 * t69
  t72 = params.a3 * t69 + 0.1e1
  t73 = t72 ** params.a4
  t74 = 0.1e1 / t73
  t76 = t68 ** params.a6
  t77 = params.a5 * t76
  t78 = t68 ** params.a8
  t79 = params.a7 * t78
  t80 = 0.1e1 - t77 + t79
  t81 = t68 ** params.a10
  t83 = params.a9 * t81 + 0.1e1
  t84 = 0.1e1 / t83
  t86 = t70 * t74 + t80 * t84
  t95 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t96 = t54 ** 2
  t97 = 0.1e1 / t96
  t98 = t95 * t97
  t102 = t95 * t54
  t103 = 0.1e1 / r0
  t108 = t69 ** 2
  t109 = params.a1 * t108
  t110 = t74 * params.a4
  t111 = t109 * t110
  t112 = params.a3 * params.a2
  t113 = 0.1e1 / t72
  t123 = 0.4e1 / 0.3e1 * t77 * params.a6 * t103 - 0.4e1 / 0.3e1 * t79 * params.a8 * t103
  t125 = t83 ** 2
  t126 = 0.1e1 / t125
  t128 = t80 * t126 * params.a9
  t129 = t81 * params.a10
  t130 = t129 * t103
  t133 = -0.4e1 / 0.3e1 * t70 * params.a2 * t103 * t74 + 0.4e1 / 0.3e1 * t111 * t112 * t103 * t113 + t123 * t84 + 0.4e1 / 0.3e1 * t128 * t130
  t139 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t141 = 0.1e1 / t96 / t6
  t142 = t139 * t141
  t146 = t139 * t97
  t150 = t139 * t54
  t151 = params.a2 ** 2
  t152 = r0 ** 2
  t153 = 0.1e1 / t152
  t154 = t151 * t153
  t164 = t110 * params.a3 * t113
  t168 = params.a1 * t108 * t69
  t169 = params.a4 ** 2
  t170 = t74 * t169
  t171 = t168 * t170
  t172 = params.a3 ** 2
  t173 = t172 * t151
  t174 = t72 ** 2
  t175 = 0.1e1 / t174
  t177 = t173 * t153 * t175
  t184 = t168 * t110
  t187 = params.a6 ** 2
  t194 = params.a8 ** 2
  t201 = -0.16e2 / 0.9e1 * t77 * t187 * t153 - 0.4e1 / 0.3e1 * t77 * params.a6 * t153 + 0.16e2 / 0.9e1 * t79 * t194 * t153 + 0.4e1 / 0.3e1 * t79 * params.a8 * t153
  t204 = t123 * t126 * params.a9
  t208 = 0.1e1 / t125 / t83
  t210 = params.a9 ** 2
  t211 = t80 * t208 * t210
  t212 = t81 ** 2
  t213 = params.a10 ** 2
  t214 = t212 * t213
  t215 = t214 * t153
  t218 = t81 * t213
  t219 = t218 * t153
  t222 = t129 * t153
  t225 = 0.16e2 / 0.9e1 * t70 * t154 * t74 + 0.4e1 / 0.3e1 * t70 * params.a2 * t153 * t74 - 0.16e2 / 0.3e1 * t109 * t154 * t164 + 0.16e2 / 0.9e1 * t171 * t177 - 0.4e1 / 0.3e1 * t111 * t112 * t153 * t113 + 0.16e2 / 0.9e1 * t184 * t177 + t201 * t84 + 0.8e1 / 0.3e1 * t204 * t130 + 0.32e2 / 0.9e1 * t211 * t215 - 0.16e2 / 0.9e1 * t128 * t219 - 0.4e1 / 0.3e1 * t128 * t222
  t229 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t230 = t229 * f.p.zeta_threshold
  t232 = f.my_piecewise3(t20, t230, t21 * t19)
  t234 = 0.1e1 / t96 / t25
  t235 = t232 * t234
  t239 = t232 * t141
  t243 = t232 * t97
  t247 = t232 * t54
  t248 = t187 * params.a6
  t250 = 0.1e1 / t152 / r0
  t260 = t194 * params.a8
  t270 = 0.64e2 / 0.27e2 * t77 * t248 * t250 + 0.16e2 / 0.3e1 * t77 * t187 * t250 + 0.8e1 / 0.3e1 * t77 * params.a6 * t250 - 0.64e2 / 0.27e2 * t79 * t260 * t250 - 0.16e2 / 0.3e1 * t79 * t194 * t250 - 0.8e1 / 0.3e1 * t79 * params.a8 * t250
  t274 = t214 * t250
  t277 = t218 * t250
  t280 = t129 * t250
  t283 = t151 * params.a2
  t284 = t283 * t250
  t288 = t108 ** 2
  t289 = params.a1 * t288
  t291 = t74 * t169 * params.a4
  t292 = t289 * t291
  t293 = t172 * params.a3
  t294 = t293 * t283
  t296 = 0.1e1 / t174 / t72
  t298 = t294 * t250 * t296
  t301 = t289 * t170
  t305 = t173 * t250 * t175
  t308 = t289 * t110
  t314 = t151 * t250
  t318 = t270 * t84 - 0.4e1 * t204 * t222 - 0.32e2 / 0.3e1 * t211 * t274 + 0.16e2 / 0.3e1 * t128 * t277 + 0.8e1 / 0.3e1 * t128 * t280 - 0.64e2 / 0.27e2 * t70 * t284 * t74 + 0.64e2 / 0.27e2 * t292 * t298 + 0.64e2 / 0.9e1 * t301 * t298 - 0.16e2 / 0.3e1 * t184 * t305 + 0.128e3 / 0.27e2 * t308 * t298 + 0.448e3 / 0.27e2 * t109 * t284 * t164 + 0.16e2 * t109 * t314 * t164
  t319 = t168 * t284
  t320 = t172 * t175
  t321 = t170 * t320
  t324 = t110 * t320
  t335 = t201 * t126 * params.a9
  t339 = t123 * t208 * t210
  t344 = t125 ** 2
  t345 = 0.1e1 / t344
  t347 = t210 * params.a9
  t348 = t80 * t345 * t347
  t349 = t212 * t81
  t350 = t213 * params.a10
  t351 = t349 * t350
  t352 = t351 * t250
  t355 = t212 * t350
  t356 = t355 * t250
  t359 = t81 * t350
  t360 = t359 * t250
  t369 = -0.128e3 / 0.9e1 * t319 * t321 - 0.128e3 / 0.9e1 * t319 * t324 - 0.16e2 / 0.3e1 * t70 * t314 * t74 - 0.8e1 / 0.3e1 * t70 * params.a2 * t250 * t74 + 0.4e1 * t335 * t130 + 0.32e2 / 0.3e1 * t339 * t215 - 0.16e2 / 0.3e1 * t204 * t219 + 0.128e3 / 0.9e1 * t348 * t352 - 0.128e3 / 0.9e1 * t211 * t356 + 0.64e2 / 0.27e2 * t128 * t360 - 0.16e2 / 0.3e1 * t171 * t305 + 0.8e1 / 0.3e1 * t111 * t112 * t250 * t113
  t370 = t318 + t369
  t375 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t86 - 0.3e1 / 0.8e1 * t5 * t98 * t86 - 0.9e1 / 0.8e1 * t5 * t102 * t133 + t5 * t142 * t86 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t146 * t133 - 0.9e1 / 0.8e1 * t5 * t150 * t225 - 0.5e1 / 0.36e2 * t5 * t235 * t86 + t5 * t239 * t133 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t243 * t225 - 0.3e1 / 0.8e1 * t5 * t247 * t370)
  t377 = r1 <= f.p.dens_threshold
  t378 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t379 = 0.1e1 + t378
  t380 = t379 <= f.p.zeta_threshold
  t381 = t379 ** (0.1e1 / 0.3e1)
  t382 = t381 ** 2
  t384 = 0.1e1 / t382 / t379
  t386 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t387 = t386 ** 2
  t391 = 0.1e1 / t382
  t392 = t391 * t386
  t394 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t398 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t402 = f.my_piecewise3(t380, 0, -0.8e1 / 0.27e2 * t384 * t387 * t386 + 0.4e1 / 0.3e1 * t392 * t394 + 0.4e1 / 0.3e1 * t381 * t398)
  t404 = jnp.sqrt(s2)
  t405 = r1 ** (0.1e1 / 0.3e1)
  t410 = t61 * t404 / t405 / r1 / 0.12e2
  t411 = t410 ** params.a2
  t415 = (params.a3 * t411 + 0.1e1) ** params.a4
  t418 = t410 ** params.a6
  t420 = t410 ** params.a8
  t423 = t410 ** params.a10
  t428 = params.a1 * t411 / t415 + (-params.a5 * t418 + params.a7 * t420 + 0.1e1) / (params.a9 * t423 + 0.1e1)
  t437 = f.my_piecewise3(t380, 0, 0.4e1 / 0.9e1 * t391 * t387 + 0.4e1 / 0.3e1 * t381 * t394)
  t444 = f.my_piecewise3(t380, 0, 0.4e1 / 0.3e1 * t381 * t386)
  t450 = f.my_piecewise3(t380, t230, t381 * t379)
  t456 = f.my_piecewise3(t377, 0, -0.3e1 / 0.8e1 * t5 * t402 * t54 * t428 - 0.3e1 / 0.8e1 * t5 * t437 * t97 * t428 + t5 * t444 * t141 * t428 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t450 * t234 * t428)
  t458 = t19 ** 2
  t461 = t30 ** 2
  t467 = t41 ** 2
  t476 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t477 = f.my_piecewise5(t10, 0, t14, 0, t476)
  t481 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t458 * t461 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t467 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t477)
  t512 = t152 ** 2
  t513 = 0.1e1 / t512
  t514 = t151 * t513
  t522 = t151 ** 2
  t523 = t522 * t513
  t527 = t283 * t513
  t531 = t187 ** 2
  t544 = t194 ** 2
  t560 = t513 * t296
  t561 = t293 * t522 * t560
  t565 = params.a1 * t288 * t69
  t567 = t172 ** 2
  t569 = t174 ** 2
  t572 = t567 * t522 * t513 / t569
  t576 = t513 * t175
  t580 = t294 * t560
  t588 = 0.176e3 / 0.9e1 * t70 * t514 * t74 + 0.8e1 * t70 * params.a2 * t513 * t74 + 0.256e3 / 0.81e2 * t70 * t523 * t74 + 0.128e3 / 0.9e1 * t70 * t527 * t74 + (-0.256e3 / 0.81e2 * t77 * t531 * t513 - 0.128e3 / 0.9e1 * t77 * t248 * t513 - 0.176e3 / 0.9e1 * t77 * t187 * t513 - 0.8e1 * t77 * params.a6 * t513 + 0.256e3 / 0.81e2 * t79 * t544 * t513 + 0.128e3 / 0.9e1 * t79 * t260 * t513 + 0.176e3 / 0.9e1 * t79 * t194 * t513 + 0.8e1 * t79 * params.a8 * t513) * t84 - 0.2560e4 / 0.27e2 * t301 * t561 + 0.2816e4 / 0.81e2 * t565 * t170 * t572 + 0.256e3 / 0.3e1 * t184 * t172 * t283 * t576 - 0.256e3 / 0.9e1 * t308 * t580 - 0.5120e4 / 0.81e2 * t308 * t561 + 0.512e3 / 0.27e2 * t565 * t110 * t572
  t589 = t168 * t523
  t599 = t169 ** 2
  t611 = t173 * t576
  t620 = 0.6400e4 / 0.81e2 * t589 * t321 + 0.6400e4 / 0.81e2 * t589 * t324 - 0.1280e4 / 0.27e2 * t109 * t523 * t164 - 0.2560e4 / 0.81e2 * t292 * t561 + 0.256e3 / 0.81e2 * t565 * t74 * t599 * t572 + 0.512e3 / 0.27e2 * t565 * t291 * t572 - 0.128e3 / 0.9e1 * t292 * t580 - 0.128e3 / 0.3e1 * t301 * t580 + 0.176e3 / 0.9e1 * t184 * t611 - 0.896e3 / 0.9e1 * t109 * t527 * t164 - 0.176e3 / 0.3e1 * t109 * t514 * t164
  t653 = 0.176e3 / 0.9e1 * t171 * t611 - 0.8e1 * t111 * t112 * t513 * t113 + 0.256e3 / 0.3e1 * t168 * t527 * t321 + 0.352e3 / 0.9e1 * t211 * t214 * t513 - 0.176e3 / 0.9e1 * t128 * t218 * t513 - 0.8e1 * t128 * t129 * t513 + 0.16e2 / 0.3e1 * t270 * t126 * params.a9 * t130 - 0.8e1 * t335 * t222 - 0.128e3 / 0.3e1 * t339 * t274 + 0.64e2 / 0.3e1 * t204 * t277 - 0.256e3 / 0.3e1 * t348 * t351 * t513
  t677 = t210 ** 2
  t679 = t212 ** 2
  t680 = t213 ** 2
  t699 = 0.256e3 / 0.3e1 * t211 * t355 * t513 - 0.128e3 / 0.9e1 * t128 * t359 * t513 + 0.64e2 / 0.3e1 * t201 * t208 * t210 * t215 - 0.32e2 / 0.3e1 * t335 * t219 + 0.512e3 / 0.9e1 * t123 * t345 * t347 * t352 - 0.512e3 / 0.9e1 * t339 * t356 + 0.256e3 / 0.27e2 * t204 * t360 + 0.2048e4 / 0.27e2 * t80 / t344 / t83 * t677 * t679 * t680 * t513 - 0.1024e4 / 0.9e1 * t348 * t349 * t680 * t513 + 0.3584e4 / 0.81e2 * t211 * t212 * t680 * t513 - 0.256e3 / 0.81e2 * t128 * t81 * t680 * t513 + 0.32e2 / 0.3e1 * t204 * t280
  t718 = 0.1e1 / t96 / t36
  t723 = -0.3e1 / 0.8e1 * t5 * t481 * t54 * t86 - 0.3e1 / 0.2e1 * t5 * t55 * t133 - 0.3e1 / 0.2e1 * t5 * t98 * t133 - 0.9e1 / 0.4e1 * t5 * t102 * t225 + t5 * t142 * t133 - 0.3e1 / 0.2e1 * t5 * t146 * t225 - 0.3e1 / 0.2e1 * t5 * t150 * t370 - 0.5e1 / 0.9e1 * t5 * t235 * t133 + t5 * t239 * t225 / 0.2e1 - t5 * t243 * t370 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t247 * (t588 + t620 + t653 + t699) - t5 * t53 * t97 * t86 / 0.2e1 + t5 * t95 * t141 * t86 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t139 * t234 * t86 + 0.10e2 / 0.27e2 * t5 * t232 * t718 * t86
  t724 = f.my_piecewise3(t1, 0, t723)
  t725 = t379 ** 2
  t728 = t387 ** 2
  t734 = t394 ** 2
  t740 = f.my_piecewise5(t14, 0, t10, 0, -t476)
  t744 = f.my_piecewise3(t380, 0, 0.40e2 / 0.81e2 / t382 / t725 * t728 - 0.16e2 / 0.9e1 * t384 * t387 * t394 + 0.4e1 / 0.3e1 * t391 * t734 + 0.16e2 / 0.9e1 * t392 * t398 + 0.4e1 / 0.3e1 * t381 * t740)
  t766 = f.my_piecewise3(t377, 0, -0.3e1 / 0.8e1 * t5 * t744 * t54 * t428 - t5 * t402 * t97 * t428 / 0.2e1 + t5 * t437 * t141 * t428 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t444 * t234 * t428 + 0.10e2 / 0.27e2 * t5 * t450 * t718 * t428)
  d1111 = 0.4e1 * t375 + 0.4e1 * t456 + t6 * (t724 + t766)

  res = {'v4rho4': d1111}
  return res
