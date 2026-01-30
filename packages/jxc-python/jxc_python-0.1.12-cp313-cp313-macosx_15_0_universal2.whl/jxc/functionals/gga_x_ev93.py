"""Generated from gga_x_ev93.mpl."""

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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))
  params_b2_raw = params.b2
  if isinstance(params_b2_raw, (str, bytes, dict)):
    params_b2 = params_b2_raw
  else:
    try:
      params_b2_seq = list(params_b2_raw)
    except TypeError:
      params_b2 = params_b2_raw
    else:
      params_b2_seq = np.asarray(params_b2_seq, dtype=np.float64)
      params_b2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2_seq))
  params_b3_raw = params.b3
  if isinstance(params_b3_raw, (str, bytes, dict)):
    params_b3 = params_b3_raw
  else:
    try:
      params_b3_seq = list(params_b3_raw)
    except TypeError:
      params_b3 = params_b3_raw
    else:
      params_b3_seq = np.asarray(params_b3_seq, dtype=np.float64)
      params_b3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b3_seq))

  ev93_f0 = lambda s: (1 + params_a1 * s ** 2 + params_a2 * s ** 4 + params_a3 * s ** 6) / (1 + params_b1 * s ** 2 + params_b2 * s ** 4 + params_b3 * s ** 6)

  ev93_f = lambda x: ev93_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, ev93_f, rs, z, xs0, xs1)

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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))
  params_b2_raw = params.b2
  if isinstance(params_b2_raw, (str, bytes, dict)):
    params_b2 = params_b2_raw
  else:
    try:
      params_b2_seq = list(params_b2_raw)
    except TypeError:
      params_b2 = params_b2_raw
    else:
      params_b2_seq = np.asarray(params_b2_seq, dtype=np.float64)
      params_b2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2_seq))
  params_b3_raw = params.b3
  if isinstance(params_b3_raw, (str, bytes, dict)):
    params_b3 = params_b3_raw
  else:
    try:
      params_b3_seq = list(params_b3_raw)
    except TypeError:
      params_b3 = params_b3_raw
    else:
      params_b3_seq = np.asarray(params_b3_seq, dtype=np.float64)
      params_b3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b3_seq))

  ev93_f0 = lambda s: (1 + params_a1 * s ** 2 + params_a2 * s ** 4 + params_a3 * s ** 6) / (1 + params_b1 * s ** 2 + params_b2 * s ** 4 + params_b3 * s ** 6)

  ev93_f = lambda x: ev93_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, ev93_f, rs, z, xs0, xs1)

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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))
  params_b2_raw = params.b2
  if isinstance(params_b2_raw, (str, bytes, dict)):
    params_b2 = params_b2_raw
  else:
    try:
      params_b2_seq = list(params_b2_raw)
    except TypeError:
      params_b2 = params_b2_raw
    else:
      params_b2_seq = np.asarray(params_b2_seq, dtype=np.float64)
      params_b2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2_seq))
  params_b3_raw = params.b3
  if isinstance(params_b3_raw, (str, bytes, dict)):
    params_b3 = params_b3_raw
  else:
    try:
      params_b3_seq = list(params_b3_raw)
    except TypeError:
      params_b3 = params_b3_raw
    else:
      params_b3_seq = np.asarray(params_b3_seq, dtype=np.float64)
      params_b3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b3_seq))

  ev93_f0 = lambda s: (1 + params_a1 * s ** 2 + params_a2 * s ** 4 + params_a3 * s ** 6) / (1 + params_b1 * s ** 2 + params_b2 * s ** 4 + params_b3 * s ** 6)

  ev93_f = lambda x: ev93_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, ev93_f, rs, z, xs0, xs1)

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
  t28 = 6 ** (0.1e1 / 0.3e1)
  t29 = params.a1 * t28
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = t33 * s0
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t40 = t34 * t39
  t43 = t28 ** 2
  t44 = params.a2 * t43
  t46 = 0.1e1 / t31 / t30
  t47 = s0 ** 2
  t48 = t46 * t47
  t49 = t35 ** 2
  t52 = 0.1e1 / t36 / t49 / r0
  t53 = t48 * t52
  t56 = t30 ** 2
  t57 = 0.1e1 / t56
  t58 = params.a3 * t57
  t59 = t47 * s0
  t60 = t49 ** 2
  t61 = 0.1e1 / t60
  t62 = t59 * t61
  t65 = 0.1e1 + t29 * t40 / 0.24e2 + t44 * t53 / 0.576e3 + t58 * t62 / 0.2304e4
  t66 = t27 * t65
  t67 = params.b1 * t28
  t70 = params.b2 * t43
  t73 = params.b3 * t57
  t76 = 0.1e1 + t67 * t40 / 0.24e2 + t70 * t53 / 0.576e3 + t73 * t62 / 0.2304e4
  t77 = 0.1e1 / t76
  t78 = t66 * t77
  t81 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t78)
  t82 = r1 <= f.p.dens_threshold
  t83 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t84 = 0.1e1 + t83
  t85 = t84 <= f.p.zeta_threshold
  t86 = t84 ** (0.1e1 / 0.3e1)
  t88 = f.my_piecewise3(t85, t22, t86 * t84)
  t89 = t5 * t88
  t90 = t33 * s2
  t91 = r1 ** 2
  t92 = r1 ** (0.1e1 / 0.3e1)
  t93 = t92 ** 2
  t95 = 0.1e1 / t93 / t91
  t96 = t90 * t95
  t99 = s2 ** 2
  t100 = t46 * t99
  t101 = t91 ** 2
  t104 = 0.1e1 / t92 / t101 / r1
  t105 = t100 * t104
  t108 = t99 * s2
  t109 = t101 ** 2
  t110 = 0.1e1 / t109
  t111 = t108 * t110
  t114 = 0.1e1 + t29 * t96 / 0.24e2 + t44 * t105 / 0.576e3 + t58 * t111 / 0.2304e4
  t115 = t27 * t114
  t122 = 0.1e1 + t67 * t96 / 0.24e2 + t70 * t105 / 0.576e3 + t73 * t111 / 0.2304e4
  t123 = 0.1e1 / t122
  t124 = t115 * t123
  t127 = f.my_piecewise3(t82, 0, -0.3e1 / 0.8e1 * t89 * t124)
  t128 = t6 ** 2
  t130 = t16 / t128
  t131 = t7 - t130
  t132 = f.my_piecewise5(t10, 0, t14, 0, t131)
  t135 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t132)
  t139 = t27 ** 2
  t140 = 0.1e1 / t139
  t144 = t26 * t140 * t65 * t77 / 0.8e1
  t148 = t34 / t37 / t35 / r0
  t154 = t48 / t36 / t49 / t35
  t159 = t59 / t60 / r0
  t167 = t76 ** 2
  t168 = 0.1e1 / t167
  t181 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t135 * t78 - t144 - 0.3e1 / 0.8e1 * t26 * t27 * (-t29 * t148 / 0.9e1 - t44 * t154 / 0.108e3 - t58 * t159 / 0.288e3) * t77 + 0.3e1 / 0.8e1 * t26 * t66 * t168 * (-t67 * t148 / 0.9e1 - t70 * t154 / 0.108e3 - t73 * t159 / 0.288e3))
  t183 = f.my_piecewise5(t14, 0, t10, 0, -t131)
  t186 = f.my_piecewise3(t85, 0, 0.4e1 / 0.3e1 * t86 * t183)
  t193 = t89 * t140 * t114 * t123 / 0.8e1
  t195 = f.my_piecewise3(t82, 0, -0.3e1 / 0.8e1 * t5 * t186 * t124 - t193)
  vrho_0_ = t81 + t127 + t6 * (t181 + t195)
  t198 = -t7 - t130
  t199 = f.my_piecewise5(t10, 0, t14, 0, t198)
  t202 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t199)
  t207 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t202 * t78 - t144)
  t209 = f.my_piecewise5(t14, 0, t10, 0, -t198)
  t212 = f.my_piecewise3(t85, 0, 0.4e1 / 0.3e1 * t86 * t209)
  t219 = t90 / t93 / t91 / r1
  t225 = t100 / t92 / t101 / t91
  t230 = t108 / t109 / r1
  t238 = t122 ** 2
  t239 = 0.1e1 / t238
  t252 = f.my_piecewise3(t82, 0, -0.3e1 / 0.8e1 * t5 * t212 * t124 - t193 - 0.3e1 / 0.8e1 * t89 * t27 * (-t29 * t219 / 0.9e1 - t44 * t225 / 0.108e3 - t58 * t230 / 0.288e3) * t123 + 0.3e1 / 0.8e1 * t89 * t115 * t239 * (-t67 * t219 / 0.9e1 - t70 * t225 / 0.108e3 - t73 * t230 / 0.288e3))
  vrho_1_ = t81 + t127 + t6 * (t207 + t252)
  t255 = t33 * t39
  t259 = t46 * s0 * t52
  t262 = t47 * t61
  t281 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (t29 * t255 / 0.24e2 + t44 * t259 / 0.288e3 + t58 * t262 / 0.768e3) * t77 + 0.3e1 / 0.8e1 * t26 * t66 * t168 * (t67 * t255 / 0.24e2 + t70 * t259 / 0.288e3 + t73 * t262 / 0.768e3))
  vsigma_0_ = t6 * t281
  vsigma_1_ = 0.0e0
  t282 = t33 * t95
  t286 = t46 * s2 * t104
  t289 = t99 * t110
  t308 = f.my_piecewise3(t82, 0, -0.3e1 / 0.8e1 * t89 * t27 * (t29 * t282 / 0.24e2 + t44 * t286 / 0.288e3 + t58 * t289 / 0.768e3) * t123 + 0.3e1 / 0.8e1 * t89 * t115 * t239 * (t67 * t282 / 0.24e2 + t70 * t286 / 0.288e3 + t73 * t289 / 0.768e3))
  vsigma_2_ = t6 * t308
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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))
  params_b2_raw = params.b2
  if isinstance(params_b2_raw, (str, bytes, dict)):
    params_b2 = params_b2_raw
  else:
    try:
      params_b2_seq = list(params_b2_raw)
    except TypeError:
      params_b2 = params_b2_raw
    else:
      params_b2_seq = np.asarray(params_b2_seq, dtype=np.float64)
      params_b2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2_seq))
  params_b3_raw = params.b3
  if isinstance(params_b3_raw, (str, bytes, dict)):
    params_b3 = params_b3_raw
  else:
    try:
      params_b3_seq = list(params_b3_raw)
    except TypeError:
      params_b3 = params_b3_raw
    else:
      params_b3_seq = np.asarray(params_b3_seq, dtype=np.float64)
      params_b3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b3_seq))

  ev93_f0 = lambda s: (1 + params_a1 * s ** 2 + params_a2 * s ** 4 + params_a3 * s ** 6) / (1 + params_b1 * s ** 2 + params_b2 * s ** 4 + params_b3 * s ** 6)

  ev93_f = lambda x: ev93_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, ev93_f, rs, z, xs0, xs1)

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
  t20 = 6 ** (0.1e1 / 0.3e1)
  t21 = params.a1 * t20
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t26 = t21 * t25
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t19 ** 2
  t33 = 0.1e1 / t31 / t30
  t34 = t29 * t33
  t37 = t20 ** 2
  t40 = 0.1e1 / t23 / t22
  t41 = params.a2 * t37 * t40
  t42 = s0 ** 2
  t43 = t42 * t27
  t44 = t30 ** 2
  t47 = 0.1e1 / t19 / t44 / r0
  t48 = t43 * t47
  t51 = t22 ** 2
  t52 = 0.1e1 / t51
  t53 = params.a3 * t52
  t54 = t42 * s0
  t55 = t44 ** 2
  t56 = 0.1e1 / t55
  t57 = t54 * t56
  t60 = 0.1e1 + t26 * t34 / 0.24e2 + t41 * t48 / 0.288e3 + t53 * t57 / 0.576e3
  t61 = t19 * t60
  t62 = params.b1 * t20
  t63 = t62 * t25
  t67 = params.b2 * t37 * t40
  t70 = params.b3 * t52
  t73 = 0.1e1 + t63 * t34 / 0.24e2 + t67 * t48 / 0.288e3 + t70 * t57 / 0.576e3
  t74 = 0.1e1 / t73
  t78 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t61 * t74)
  t87 = t29 / t31 / t30 / r0
  t93 = t43 / t19 / t44 / t30
  t98 = t54 / t55 / r0
  t106 = t73 ** 2
  t107 = 0.1e1 / t106
  t120 = f.my_piecewise3(t2, 0, -t18 / t31 * t60 * t74 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (-t26 * t87 / 0.9e1 - t41 * t93 / 0.54e2 - t53 * t98 / 0.72e2) * t74 + 0.3e1 / 0.8e1 * t18 * t61 * t107 * (-t63 * t87 / 0.9e1 - t67 * t93 / 0.54e2 - t70 * t98 / 0.72e2))
  vrho_0_ = 0.2e1 * r0 * t120 + 0.2e1 * t78
  t124 = t25 * t28 * t33
  t128 = s0 * t27 * t47
  t131 = t42 * t56
  t150 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (t21 * t124 / 0.24e2 + t41 * t128 / 0.144e3 + t53 * t131 / 0.192e3) * t74 + 0.3e1 / 0.8e1 * t18 * t61 * t107 * (t62 * t124 / 0.24e2 + t67 * t128 / 0.144e3 + t70 * t131 / 0.192e3))
  vsigma_0_ = 0.2e1 * r0 * t150
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
  t18 = t6 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = params.a1 * t22
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
  t38 = t22 ** 2
  t39 = params.a2 * t38
  t41 = 0.1e1 / t25 / t24
  t42 = t39 * t41
  t43 = s0 ** 2
  t44 = t43 * t29
  t45 = t32 ** 2
  t48 = 0.1e1 / t19 / t45 / r0
  t49 = t44 * t48
  t52 = t24 ** 2
  t53 = 0.1e1 / t52
  t54 = params.a3 * t53
  t55 = t43 * s0
  t56 = t45 ** 2
  t57 = 0.1e1 / t56
  t58 = t55 * t57
  t61 = 0.1e1 + t28 * t35 / 0.24e2 + t42 * t49 / 0.288e3 + t54 * t58 / 0.576e3
  t62 = t21 * t61
  t63 = params.b1 * t22
  t64 = t63 * t27
  t67 = params.b2 * t38
  t68 = t67 * t41
  t71 = params.b3 * t53
  t74 = 0.1e1 + t64 * t35 / 0.24e2 + t68 * t49 / 0.288e3 + t71 * t58 / 0.576e3
  t75 = 0.1e1 / t74
  t79 = t32 * r0
  t81 = 0.1e1 / t20 / t79
  t82 = t31 * t81
  t87 = 0.1e1 / t19 / t45 / t32
  t88 = t44 * t87
  t92 = 0.1e1 / t56 / r0
  t93 = t55 * t92
  t96 = -t28 * t82 / 0.9e1 - t42 * t88 / 0.54e2 - t54 * t93 / 0.72e2
  t97 = t19 * t96
  t101 = t19 * t61
  t102 = t74 ** 2
  t103 = 0.1e1 / t102
  t110 = -t64 * t82 / 0.9e1 - t68 * t88 / 0.54e2 - t71 * t93 / 0.72e2
  t111 = t103 * t110
  t116 = f.my_piecewise3(t2, 0, -t18 * t62 * t75 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t97 * t75 + 0.3e1 / 0.8e1 * t18 * t101 * t111)
  t133 = t31 / t20 / t45
  t139 = t44 / t19 / t45 / t79
  t144 = t55 / t56 / t32
  t156 = 0.1e1 / t102 / t74
  t157 = t110 ** 2
  t174 = f.my_piecewise3(t2, 0, t18 / t20 / r0 * t61 * t75 / 0.12e2 - t18 * t21 * t96 * t75 / 0.4e1 + t18 * t62 * t111 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t19 * (0.11e2 / 0.27e2 * t28 * t133 + 0.19e2 / 0.162e3 * t42 * t139 + t54 * t144 / 0.8e1) * t75 + 0.3e1 / 0.4e1 * t18 * t97 * t111 - 0.3e1 / 0.4e1 * t18 * t101 * t156 * t157 + 0.3e1 / 0.8e1 * t18 * t101 * t103 * (0.11e2 / 0.27e2 * t64 * t133 + 0.19e2 / 0.162e3 * t68 * t139 + t71 * t144 / 0.8e1))
  v2rho2_0_ = 0.2e1 * r0 * t174 + 0.4e1 * t116
  t177 = t27 * t30
  t178 = t177 * t34
  t181 = s0 * t29
  t182 = t181 * t48
  t185 = t43 * t57
  t188 = t23 * t178 / 0.24e2 + t42 * t182 / 0.144e3 + t54 * t185 / 0.192e3
  t189 = t19 * t188
  t198 = t63 * t178 / 0.24e2 + t68 * t182 / 0.144e3 + t71 * t185 / 0.192e3
  t199 = t103 * t198
  t204 = f.my_piecewise3(t2, 0, 0.3e1 / 0.8e1 * t18 * t101 * t199 - 0.3e1 / 0.8e1 * t18 * t189 * t75)
  t209 = t177 * t81
  t212 = t181 * t87
  t215 = t43 * t92
  t251 = f.my_piecewise3(t2, 0, -t18 * t21 * t188 * t75 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (-t23 * t209 / 0.9e1 - t42 * t212 / 0.27e2 - t54 * t215 / 0.24e2) * t75 + 0.3e1 / 0.8e1 * t18 * t189 * t111 + t18 * t62 * t199 / 0.8e1 + 0.3e1 / 0.8e1 * t18 * t97 * t199 - 0.3e1 / 0.4e1 * t6 * t17 * t19 * t61 * t156 * t198 * t110 + 0.3e1 / 0.8e1 * t18 * t101 * t103 * (-t63 * t209 / 0.9e1 - t68 * t212 / 0.27e2 - t71 * t215 / 0.24e2))
  v2rhosigma_0_ = 0.2e1 * r0 * t251 + 0.2e1 * t204
  t255 = t41 * t29 * t48
  t258 = s0 * t57
  t269 = t198 ** 2
  t284 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (t39 * t255 / 0.144e3 + t54 * t258 / 0.96e2) * t75 + 0.3e1 / 0.4e1 * t18 * t189 * t199 - 0.3e1 / 0.4e1 * t18 * t101 * t156 * t269 + 0.3e1 / 0.8e1 * t18 * t101 * t103 * (t67 * t255 / 0.144e3 + t71 * t258 / 0.96e2))
  v2sigma2_0_ = 0.2e1 * r0 * t284
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
  t18 = t6 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / r0
  t23 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = params.a1 * t23 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t20 / t33
  t36 = t32 * t35
  t39 = t23 ** 2
  t42 = 0.1e1 / t26 / t25
  t43 = params.a2 * t39 * t42
  t44 = s0 ** 2
  t45 = t44 * t30
  t46 = t33 ** 2
  t47 = t46 * r0
  t50 = t45 / t19 / t47
  t53 = t25 ** 2
  t54 = 0.1e1 / t53
  t55 = params.a3 * t54
  t56 = t44 * s0
  t57 = t46 ** 2
  t59 = t56 / t57
  t62 = 0.1e1 + t29 * t36 / 0.24e2 + t43 * t50 / 0.288e3 + t55 * t59 / 0.576e3
  t63 = t22 * t62
  t65 = params.b1 * t23 * t28
  t69 = params.b2 * t39 * t42
  t72 = params.b3 * t54
  t75 = 0.1e1 + t65 * t36 / 0.24e2 + t69 * t50 / 0.288e3 + t72 * t59 / 0.576e3
  t76 = 0.1e1 / t75
  t80 = 0.1e1 / t20
  t81 = t33 * r0
  t84 = t32 / t20 / t81
  t90 = t45 / t19 / t46 / t33
  t95 = t56 / t57 / r0
  t98 = -t29 * t84 / 0.9e1 - t43 * t90 / 0.54e2 - t55 * t95 / 0.72e2
  t99 = t80 * t98
  t103 = t80 * t62
  t104 = t75 ** 2
  t105 = 0.1e1 / t104
  t112 = -t65 * t84 / 0.9e1 - t69 * t90 / 0.54e2 - t72 * t95 / 0.72e2
  t113 = t105 * t112
  t119 = t32 / t20 / t46
  t125 = t45 / t19 / t46 / t81
  t130 = t56 / t57 / t33
  t133 = 0.11e2 / 0.27e2 * t29 * t119 + 0.19e2 / 0.162e3 * t43 * t125 + t55 * t130 / 0.8e1
  t134 = t19 * t133
  t138 = t19 * t98
  t142 = t19 * t62
  t144 = 0.1e1 / t104 / t75
  t145 = t112 ** 2
  t146 = t144 * t145
  t156 = 0.11e2 / 0.27e2 * t65 * t119 + 0.19e2 / 0.162e3 * t69 * t125 + t72 * t130 / 0.8e1
  t157 = t105 * t156
  t162 = f.my_piecewise3(t2, 0, t18 * t63 * t76 / 0.12e2 - t18 * t99 * t76 / 0.4e1 + t18 * t103 * t113 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t134 * t76 + 0.3e1 / 0.4e1 * t18 * t138 * t113 - 0.3e1 / 0.4e1 * t18 * t142 * t146 + 0.3e1 / 0.8e1 * t18 * t142 * t157)
  t170 = t104 ** 2
  t194 = t32 / t20 / t47
  t199 = t45 / t19 / t57
  t204 = t56 / t57 / t81
  t242 = -0.3e1 / 0.4e1 * t18 * t103 * t146 - 0.9e1 / 0.4e1 * t18 * t138 * t146 + 0.9e1 / 0.4e1 * t18 * t142 / t170 * t145 * t112 - 0.9e1 / 0.4e1 * t6 * t17 * t19 * t62 * t144 * t112 * t156 + t18 * t22 * t98 * t76 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t80 * t133 * t76 - 0.3e1 / 0.8e1 * t18 * t19 * (-0.154e3 / 0.81e2 * t29 * t194 - 0.209e3 / 0.243e3 * t43 * t199 - 0.5e1 / 0.4e1 * t55 * t204) * t76 - 0.5e1 / 0.36e2 * t18 * t35 * t62 * t76 - t18 * t63 * t113 / 0.4e1 + 0.3e1 / 0.4e1 * t18 * t99 * t113 + 0.3e1 / 0.8e1 * t18 * t103 * t157 + 0.9e1 / 0.8e1 * t18 * t134 * t113 + 0.9e1 / 0.8e1 * t18 * t138 * t157 + 0.3e1 / 0.8e1 * t18 * t142 * t105 * (-0.154e3 / 0.81e2 * t65 * t194 - 0.209e3 / 0.243e3 * t69 * t199 - 0.5e1 / 0.4e1 * t72 * t204)
  t243 = f.my_piecewise3(t2, 0, t242)
  v3rho3_0_ = 0.2e1 * r0 * t243 + 0.6e1 * t162

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
  t18 = r0 ** (0.1e1 / 0.3e1)
  t20 = t6 * t17 * t18
  t21 = 6 ** (0.1e1 / 0.3e1)
  t23 = jnp.pi ** 2
  t24 = t23 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = 0.1e1 / t25
  t27 = params.a1 * t21 * t26
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = s0 * t29
  t31 = r0 ** 2
  t32 = t18 ** 2
  t34 = 0.1e1 / t32 / t31
  t35 = t30 * t34
  t38 = t21 ** 2
  t41 = 0.1e1 / t24 / t23
  t42 = params.a2 * t38 * t41
  t43 = s0 ** 2
  t44 = t43 * t28
  t45 = t31 ** 2
  t46 = t45 * r0
  t49 = t44 / t18 / t46
  t52 = t23 ** 2
  t53 = 0.1e1 / t52
  t54 = params.a3 * t53
  t55 = t43 * s0
  t56 = t45 ** 2
  t58 = t55 / t56
  t61 = 0.1e1 + t27 * t35 / 0.24e2 + t42 * t49 / 0.288e3 + t54 * t58 / 0.576e3
  t63 = params.b1 * t21 * t26
  t67 = params.b2 * t38 * t41
  t70 = params.b3 * t53
  t73 = 0.1e1 + t63 * t35 / 0.24e2 + t67 * t49 / 0.288e3 + t70 * t58 / 0.576e3
  t74 = t73 ** 2
  t76 = 0.1e1 / t74 / t73
  t77 = t61 * t76
  t78 = t31 * r0
  t80 = 0.1e1 / t32 / t78
  t81 = t30 * t80
  t84 = t45 * t31
  t87 = t44 / t18 / t84
  t90 = t56 * r0
  t92 = t55 / t90
  t95 = -t63 * t81 / 0.9e1 - t67 * t87 / 0.54e2 - t70 * t92 / 0.72e2
  t98 = t30 / t32 / t45
  t104 = t44 / t18 / t45 / t78
  t109 = t55 / t56 / t31
  t112 = 0.11e2 / 0.27e2 * t63 * t98 + 0.19e2 / 0.162e3 * t67 * t104 + t70 * t109 / 0.8e1
  t113 = t95 * t112
  t114 = t77 * t113
  t117 = t6 * t17
  t118 = 0.1e1 / t32
  t119 = t118 * t61
  t120 = t95 ** 2
  t121 = t76 * t120
  t131 = -t27 * t81 / 0.9e1 - t42 * t87 / 0.54e2 - t54 * t92 / 0.72e2
  t132 = t18 * t131
  t136 = t18 * t61
  t137 = t74 ** 2
  t138 = 0.1e1 / t137
  t140 = t138 * t120 * t95
  t145 = 0.1e1 / t32 / r0
  t146 = t145 * t131
  t147 = 0.1e1 / t73
  t157 = 0.11e2 / 0.27e2 * t27 * t98 + 0.19e2 / 0.162e3 * t42 * t104 + t54 * t109 / 0.8e1
  t158 = t118 * t157
  t164 = t30 / t32 / t46
  t169 = t44 / t18 / t56
  t174 = t55 / t56 / t78
  t177 = -0.154e3 / 0.81e2 * t27 * t164 - 0.209e3 / 0.243e3 * t42 * t169 - 0.5e1 / 0.4e1 * t54 * t174
  t178 = t18 * t177
  t182 = t34 * t61
  t186 = t145 * t61
  t187 = 0.1e1 / t74
  t188 = t187 * t95
  t192 = t118 * t131
  t196 = t187 * t112
  t200 = t18 * t157
  t213 = -0.154e3 / 0.81e2 * t63 * t164 - 0.209e3 / 0.243e3 * t67 * t169 - 0.5e1 / 0.4e1 * t70 * t174
  t214 = t187 * t213
  t218 = -0.9e1 / 0.4e1 * t20 * t114 - 0.3e1 / 0.4e1 * t117 * t119 * t121 - 0.9e1 / 0.4e1 * t117 * t132 * t121 + 0.9e1 / 0.4e1 * t117 * t136 * t140 + t117 * t146 * t147 / 0.4e1 - 0.3e1 / 0.8e1 * t117 * t158 * t147 - 0.3e1 / 0.8e1 * t117 * t178 * t147 - 0.5e1 / 0.36e2 * t117 * t182 * t147 - t117 * t186 * t188 / 0.4e1 + 0.3e1 / 0.4e1 * t117 * t192 * t188 + 0.3e1 / 0.8e1 * t117 * t119 * t196 + 0.9e1 / 0.8e1 * t117 * t200 * t188 + 0.9e1 / 0.8e1 * t117 * t132 * t196 + 0.3e1 / 0.8e1 * t117 * t136 * t214
  t219 = f.my_piecewise3(t2, 0, t218)
  t223 = t30 / t32 / t84
  t228 = t44 / t18 / t90
  t233 = t55 / t56 / t45
  t270 = t112 ** 2
  t277 = 0.3e1 / 0.8e1 * t117 * t136 * t187 * (0.2618e4 / 0.243e3 * t63 * t223 + 0.5225e4 / 0.729e3 * t67 * t228 + 0.55e2 / 0.4e1 * t70 * t233) - t117 * t186 * t196 / 0.2e1 + 0.3e1 / 0.2e1 * t117 * t192 * t196 + t117 * t119 * t214 / 0.2e1 + 0.9e1 / 0.4e1 * t117 * t200 * t196 + 0.3e1 / 0.2e1 * t117 * t132 * t214 - 0.9e1 / 0.2e1 * t117 * t200 * t121 - t117 * t146 * t188 + 0.3e1 / 0.2e1 * t117 * t158 * t188 + 0.3e1 / 0.2e1 * t117 * t178 * t188 + 0.5e1 / 0.9e1 * t117 * t182 * t188 - 0.9e1 / 0.4e1 * t117 * t136 * t76 * t270 + t117 * t186 * t121
  t289 = t120 ** 2
  t338 = 0.3e1 * t117 * t119 * t140 + 0.9e1 * t117 * t132 * t140 - 0.3e1 * t117 * t192 * t121 - 0.9e1 * t117 * t136 / t137 / t73 * t289 - t117 * t118 * t177 * t147 / 0.2e1 - 0.3e1 / 0.8e1 * t117 * t18 * (0.2618e4 / 0.243e3 * t27 * t223 + 0.5225e4 / 0.729e3 * t42 * t228 + 0.55e2 / 0.4e1 * t54 * t233) * t147 - 0.5e1 / 0.9e1 * t117 * t34 * t131 * t147 + 0.10e2 / 0.27e2 * t117 * t80 * t61 * t147 + t117 * t145 * t157 * t147 / 0.2e1 - 0.3e1 * t6 * t17 * t118 * t114 + 0.27e2 / 0.2e1 * t20 * t61 * t138 * t120 * t112 - 0.9e1 * t20 * t131 * t76 * t113 - 0.3e1 * t20 * t77 * t95 * t213
  t340 = f.my_piecewise3(t2, 0, t277 + t338)
  v4rho4_0_ = 0.2e1 * r0 * t340 + 0.8e1 * t219

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
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = params.a1 * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t44 = t38 / t41 / t39
  t47 = t32 ** 2
  t48 = params.a2 * t47
  t50 = 0.1e1 / t35 / t34
  t51 = s0 ** 2
  t52 = t50 * t51
  t53 = t39 ** 2
  t57 = t52 / t40 / t53 / r0
  t60 = t34 ** 2
  t61 = 0.1e1 / t60
  t62 = params.a3 * t61
  t63 = t51 * s0
  t64 = t53 ** 2
  t66 = t63 / t64
  t69 = 0.1e1 + t33 * t44 / 0.24e2 + t48 * t57 / 0.576e3 + t62 * t66 / 0.2304e4
  t70 = t31 * t69
  t71 = params.b1 * t32
  t74 = params.b2 * t47
  t77 = params.b3 * t61
  t80 = 0.1e1 + t71 * t44 / 0.24e2 + t74 * t57 / 0.576e3 + t77 * t66 / 0.2304e4
  t81 = 0.1e1 / t80
  t82 = t70 * t81
  t85 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t86 = t85 * f.p.zeta_threshold
  t88 = f.my_piecewise3(t20, t86, t21 * t19)
  t89 = t5 * t88
  t90 = t31 ** 2
  t91 = 0.1e1 / t90
  t92 = t91 * t69
  t93 = t92 * t81
  t95 = t89 * t93 / 0.8e1
  t96 = t39 * r0
  t99 = t38 / t41 / t96
  t105 = t52 / t40 / t53 / t39
  t110 = t63 / t64 / r0
  t113 = -t33 * t99 / 0.9e1 - t48 * t105 / 0.108e3 - t62 * t110 / 0.288e3
  t114 = t31 * t113
  t115 = t114 * t81
  t118 = t80 ** 2
  t119 = 0.1e1 / t118
  t126 = -t71 * t99 / 0.9e1 - t74 * t105 / 0.108e3 - t77 * t110 / 0.288e3
  t127 = t119 * t126
  t128 = t70 * t127
  t132 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t82 - t95 - 0.3e1 / 0.8e1 * t89 * t115 + 0.3e1 / 0.8e1 * t89 * t128)
  t134 = r1 <= f.p.dens_threshold
  t135 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t136 = 0.1e1 + t135
  t137 = t136 <= f.p.zeta_threshold
  t138 = t136 ** (0.1e1 / 0.3e1)
  t140 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t143 = f.my_piecewise3(t137, 0, 0.4e1 / 0.3e1 * t138 * t140)
  t144 = t5 * t143
  t145 = t37 * s2
  t146 = r1 ** 2
  t147 = r1 ** (0.1e1 / 0.3e1)
  t148 = t147 ** 2
  t151 = t145 / t148 / t146
  t154 = s2 ** 2
  t155 = t50 * t154
  t156 = t146 ** 2
  t160 = t155 / t147 / t156 / r1
  t163 = t154 * s2
  t164 = t156 ** 2
  t166 = t163 / t164
  t169 = 0.1e1 + t33 * t151 / 0.24e2 + t48 * t160 / 0.576e3 + t62 * t166 / 0.2304e4
  t170 = t31 * t169
  t177 = 0.1e1 + t71 * t151 / 0.24e2 + t74 * t160 / 0.576e3 + t77 * t166 / 0.2304e4
  t178 = 0.1e1 / t177
  t179 = t170 * t178
  t183 = f.my_piecewise3(t137, t86, t138 * t136)
  t184 = t5 * t183
  t185 = t91 * t169
  t186 = t185 * t178
  t188 = t184 * t186 / 0.8e1
  t190 = f.my_piecewise3(t134, 0, -0.3e1 / 0.8e1 * t144 * t179 - t188)
  t192 = t21 ** 2
  t193 = 0.1e1 / t192
  t194 = t26 ** 2
  t199 = t16 / t22 / t6
  t201 = -0.2e1 * t23 + 0.2e1 * t199
  t202 = f.my_piecewise5(t10, 0, t14, 0, t201)
  t206 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t193 * t194 + 0.4e1 / 0.3e1 * t21 * t202)
  t210 = t30 * t93
  t217 = 0.1e1 / t90 / t6
  t221 = t89 * t217 * t69 * t81 / 0.12e2
  t224 = t89 * t91 * t113 * t81
  t227 = t89 * t92 * t127
  t231 = t38 / t41 / t53
  t237 = t52 / t40 / t53 / t96
  t242 = t63 / t64 / t39
  t255 = t126 ** 2
  t271 = -0.3e1 / 0.8e1 * t5 * t206 * t82 - t210 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t115 + 0.3e1 / 0.4e1 * t30 * t128 + t221 - t224 / 0.4e1 + t227 / 0.4e1 - 0.3e1 / 0.8e1 * t89 * t31 * (0.11e2 / 0.27e2 * t33 * t231 + 0.19e2 / 0.324e3 * t48 * t237 + t62 * t242 / 0.32e2) * t81 + 0.3e1 / 0.4e1 * t89 * t114 * t127 - 0.3e1 / 0.4e1 * t89 * t70 / t118 / t80 * t255 + 0.3e1 / 0.8e1 * t89 * t70 * t119 * (0.11e2 / 0.27e2 * t71 * t231 + 0.19e2 / 0.324e3 * t74 * t237 + t77 * t242 / 0.32e2)
  t272 = f.my_piecewise3(t1, 0, t271)
  t273 = t138 ** 2
  t274 = 0.1e1 / t273
  t275 = t140 ** 2
  t279 = f.my_piecewise5(t14, 0, t10, 0, -t201)
  t283 = f.my_piecewise3(t137, 0, 0.4e1 / 0.9e1 * t274 * t275 + 0.4e1 / 0.3e1 * t138 * t279)
  t287 = t144 * t186
  t292 = t184 * t217 * t169 * t178 / 0.12e2
  t294 = f.my_piecewise3(t134, 0, -0.3e1 / 0.8e1 * t5 * t283 * t179 - t287 / 0.4e1 + t292)
  d11 = 0.2e1 * t132 + 0.2e1 * t190 + t6 * (t272 + t294)
  t297 = -t7 - t24
  t298 = f.my_piecewise5(t10, 0, t14, 0, t297)
  t301 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t298)
  t302 = t5 * t301
  t306 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t302 * t82 - t95)
  t308 = f.my_piecewise5(t14, 0, t10, 0, -t297)
  t311 = f.my_piecewise3(t137, 0, 0.4e1 / 0.3e1 * t138 * t308)
  t312 = t5 * t311
  t315 = t146 * r1
  t318 = t145 / t148 / t315
  t324 = t155 / t147 / t156 / t146
  t329 = t163 / t164 / r1
  t332 = -t33 * t318 / 0.9e1 - t48 * t324 / 0.108e3 - t62 * t329 / 0.288e3
  t333 = t31 * t332
  t334 = t333 * t178
  t337 = t177 ** 2
  t338 = 0.1e1 / t337
  t345 = -t71 * t318 / 0.9e1 - t74 * t324 / 0.108e3 - t77 * t329 / 0.288e3
  t346 = t338 * t345
  t347 = t170 * t346
  t351 = f.my_piecewise3(t134, 0, -0.3e1 / 0.8e1 * t312 * t179 - t188 - 0.3e1 / 0.8e1 * t184 * t334 + 0.3e1 / 0.8e1 * t184 * t347)
  t355 = 0.2e1 * t199
  t356 = f.my_piecewise5(t10, 0, t14, 0, t355)
  t360 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t193 * t298 * t26 + 0.4e1 / 0.3e1 * t21 * t356)
  t364 = t302 * t93
  t374 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t360 * t82 - t364 / 0.8e1 - 0.3e1 / 0.8e1 * t302 * t115 + 0.3e1 / 0.8e1 * t302 * t128 - t210 / 0.8e1 + t221 - t224 / 0.8e1 + t227 / 0.8e1)
  t378 = f.my_piecewise5(t14, 0, t10, 0, -t355)
  t382 = f.my_piecewise3(t137, 0, 0.4e1 / 0.9e1 * t274 * t308 * t140 + 0.4e1 / 0.3e1 * t138 * t378)
  t386 = t312 * t186
  t393 = t184 * t91 * t332 * t178
  t398 = t184 * t185 * t346
  t401 = f.my_piecewise3(t134, 0, -0.3e1 / 0.8e1 * t5 * t382 * t179 - t386 / 0.8e1 - t287 / 0.8e1 + t292 - 0.3e1 / 0.8e1 * t144 * t334 - t393 / 0.8e1 + 0.3e1 / 0.8e1 * t144 * t347 + t398 / 0.8e1)
  d12 = t132 + t190 + t306 + t351 + t6 * (t374 + t401)
  t406 = t298 ** 2
  t410 = 0.2e1 * t23 + 0.2e1 * t199
  t411 = f.my_piecewise5(t10, 0, t14, 0, t410)
  t415 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t193 * t406 + 0.4e1 / 0.3e1 * t21 * t411)
  t421 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t415 * t82 - t364 / 0.4e1 + t221)
  t422 = t308 ** 2
  t426 = f.my_piecewise5(t14, 0, t10, 0, -t410)
  t430 = f.my_piecewise3(t137, 0, 0.4e1 / 0.9e1 * t274 * t422 + 0.4e1 / 0.3e1 * t138 * t426)
  t443 = t145 / t148 / t156
  t449 = t155 / t147 / t156 / t315
  t454 = t163 / t164 / t146
  t467 = t345 ** 2
  t483 = -0.3e1 / 0.8e1 * t5 * t430 * t179 - t386 / 0.4e1 - 0.3e1 / 0.4e1 * t312 * t334 + 0.3e1 / 0.4e1 * t312 * t347 + t292 - t393 / 0.4e1 + t398 / 0.4e1 - 0.3e1 / 0.8e1 * t184 * t31 * (0.11e2 / 0.27e2 * t33 * t443 + 0.19e2 / 0.324e3 * t48 * t449 + t62 * t454 / 0.32e2) * t178 + 0.3e1 / 0.4e1 * t184 * t333 * t346 - 0.3e1 / 0.4e1 * t184 * t170 / t337 / t177 * t467 + 0.3e1 / 0.8e1 * t184 * t170 * t338 * (0.11e2 / 0.27e2 * t71 * t443 + 0.19e2 / 0.324e3 * t74 * t449 + t77 * t454 / 0.32e2)
  t484 = f.my_piecewise3(t134, 0, t483)
  d22 = 0.2e1 * t306 + 0.2e1 * t351 + t6 * (t421 + t484)
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
  t44 = 6 ** (0.1e1 / 0.3e1)
  t45 = params.a1 * t44
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t50 = t49 * s0
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t56 = t50 / t53 / t51
  t59 = t44 ** 2
  t60 = params.a2 * t59
  t62 = 0.1e1 / t47 / t46
  t63 = s0 ** 2
  t64 = t62 * t63
  t65 = t51 ** 2
  t66 = t65 * r0
  t69 = t64 / t52 / t66
  t72 = t46 ** 2
  t73 = 0.1e1 / t72
  t74 = params.a3 * t73
  t75 = t63 * s0
  t76 = t65 ** 2
  t78 = t75 / t76
  t81 = 0.1e1 + t45 * t56 / 0.24e2 + t60 * t69 / 0.576e3 + t74 * t78 / 0.2304e4
  t82 = t43 * t81
  t83 = params.b1 * t44
  t86 = params.b2 * t59
  t89 = params.b3 * t73
  t92 = 0.1e1 + t83 * t56 / 0.24e2 + t86 * t69 / 0.576e3 + t89 * t78 / 0.2304e4
  t93 = 0.1e1 / t92
  t94 = t82 * t93
  t99 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t100 = t5 * t99
  t101 = t43 ** 2
  t102 = 0.1e1 / t101
  t103 = t102 * t81
  t104 = t103 * t93
  t107 = t51 * r0
  t110 = t50 / t53 / t107
  t116 = t64 / t52 / t65 / t51
  t121 = t75 / t76 / r0
  t124 = -t45 * t110 / 0.9e1 - t60 * t116 / 0.108e3 - t74 * t121 / 0.288e3
  t125 = t43 * t124
  t126 = t125 * t93
  t129 = t92 ** 2
  t130 = 0.1e1 / t129
  t137 = -t83 * t110 / 0.9e1 - t86 * t116 / 0.108e3 - t89 * t121 / 0.288e3
  t138 = t130 * t137
  t139 = t82 * t138
  t142 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t143 = t142 * f.p.zeta_threshold
  t145 = f.my_piecewise3(t20, t143, t21 * t19)
  t146 = t5 * t145
  t148 = 0.1e1 / t101 / t6
  t149 = t148 * t81
  t150 = t149 * t93
  t153 = t102 * t124
  t154 = t153 * t93
  t157 = t103 * t138
  t162 = t50 / t53 / t65
  t168 = t64 / t52 / t65 / t107
  t173 = t75 / t76 / t51
  t176 = 0.11e2 / 0.27e2 * t45 * t162 + 0.19e2 / 0.324e3 * t60 * t168 + t74 * t173 / 0.32e2
  t177 = t43 * t176
  t178 = t177 * t93
  t181 = t125 * t138
  t185 = 0.1e1 / t129 / t92
  t186 = t137 ** 2
  t187 = t185 * t186
  t188 = t82 * t187
  t197 = 0.11e2 / 0.27e2 * t83 * t162 + 0.19e2 / 0.324e3 * t86 * t168 + t89 * t173 / 0.32e2
  t198 = t130 * t197
  t199 = t82 * t198
  t202 = -0.3e1 / 0.8e1 * t42 * t94 - t100 * t104 / 0.4e1 - 0.3e1 / 0.4e1 * t100 * t126 + 0.3e1 / 0.4e1 * t100 * t139 + t146 * t150 / 0.12e2 - t146 * t154 / 0.4e1 + t146 * t157 / 0.4e1 - 0.3e1 / 0.8e1 * t146 * t178 + 0.3e1 / 0.4e1 * t146 * t181 - 0.3e1 / 0.4e1 * t146 * t188 + 0.3e1 / 0.8e1 * t146 * t199
  t203 = f.my_piecewise3(t1, 0, t202)
  t205 = r1 <= f.p.dens_threshold
  t206 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t207 = 0.1e1 + t206
  t208 = t207 <= f.p.zeta_threshold
  t209 = t207 ** (0.1e1 / 0.3e1)
  t210 = t209 ** 2
  t211 = 0.1e1 / t210
  t213 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t214 = t213 ** 2
  t218 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t222 = f.my_piecewise3(t208, 0, 0.4e1 / 0.9e1 * t211 * t214 + 0.4e1 / 0.3e1 * t209 * t218)
  t223 = t5 * t222
  t225 = r1 ** 2
  t226 = r1 ** (0.1e1 / 0.3e1)
  t227 = t226 ** 2
  t230 = t49 * s2 / t227 / t225
  t233 = s2 ** 2
  t235 = t225 ** 2
  t239 = t62 * t233 / t226 / t235 / r1
  t243 = t235 ** 2
  t245 = t233 * s2 / t243
  t248 = 0.1e1 + t45 * t230 / 0.24e2 + t60 * t239 / 0.576e3 + t74 * t245 / 0.2304e4
  t257 = 0.1e1 / (0.1e1 + t83 * t230 / 0.24e2 + t86 * t239 / 0.576e3 + t89 * t245 / 0.2304e4)
  t258 = t43 * t248 * t257
  t263 = f.my_piecewise3(t208, 0, 0.4e1 / 0.3e1 * t209 * t213)
  t264 = t5 * t263
  t266 = t102 * t248 * t257
  t270 = f.my_piecewise3(t208, t143, t209 * t207)
  t271 = t5 * t270
  t273 = t148 * t248 * t257
  t277 = f.my_piecewise3(t205, 0, -0.3e1 / 0.8e1 * t223 * t258 - t264 * t266 / 0.4e1 + t271 * t273 / 0.12e2)
  t285 = t50 / t53 / t66
  t290 = t64 / t52 / t76
  t295 = t75 / t76 / t107
  t306 = 0.1e1 / t101 / t24
  t319 = t24 ** 2
  t323 = 0.6e1 * t33 - 0.6e1 * t16 / t319
  t324 = f.my_piecewise5(t10, 0, t14, 0, t323)
  t328 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t324)
  t353 = -0.3e1 / 0.8e1 * t146 * t102 * t176 * t93 - 0.3e1 / 0.8e1 * t146 * t43 * (-0.154e3 / 0.81e2 * t45 * t285 - 0.209e3 / 0.486e3 * t60 * t290 - 0.5e1 / 0.16e2 * t74 * t295) * t93 + t100 * t150 / 0.4e1 - 0.5e1 / 0.36e2 * t146 * t306 * t81 * t93 - 0.3e1 / 0.8e1 * t5 * t328 * t94 - 0.9e1 / 0.8e1 * t42 * t126 - 0.3e1 / 0.4e1 * t100 * t154 - 0.9e1 / 0.8e1 * t100 * t178 + t146 * t148 * t124 * t93 / 0.4e1 - 0.9e1 / 0.4e1 * t5 * t145 * t43 * t81 * t185 * t137 * t197 + 0.3e1 / 0.4e1 * t100 * t157 + 0.9e1 / 0.4e1 * t100 * t181
  t365 = t129 ** 2
  t401 = 0.9e1 / 0.8e1 * t100 * t199 - t146 * t149 * t138 / 0.4e1 + 0.3e1 / 0.4e1 * t146 * t153 * t138 + 0.3e1 / 0.8e1 * t146 * t103 * t198 + 0.9e1 / 0.4e1 * t146 * t82 / t365 * t186 * t137 - 0.9e1 / 0.4e1 * t100 * t188 - 0.3e1 / 0.4e1 * t146 * t103 * t187 - 0.9e1 / 0.4e1 * t146 * t125 * t187 + 0.9e1 / 0.8e1 * t146 * t177 * t138 + 0.9e1 / 0.8e1 * t146 * t125 * t198 + 0.3e1 / 0.8e1 * t146 * t82 * t130 * (-0.154e3 / 0.81e2 * t83 * t285 - 0.209e3 / 0.486e3 * t86 * t290 - 0.5e1 / 0.16e2 * t89 * t295) + 0.9e1 / 0.8e1 * t42 * t139 - 0.3e1 / 0.8e1 * t42 * t104
  t403 = f.my_piecewise3(t1, 0, t353 + t401)
  t413 = f.my_piecewise5(t14, 0, t10, 0, -t323)
  t417 = f.my_piecewise3(t208, 0, -0.8e1 / 0.27e2 / t210 / t207 * t214 * t213 + 0.4e1 / 0.3e1 * t211 * t213 * t218 + 0.4e1 / 0.3e1 * t209 * t413)
  t430 = f.my_piecewise3(t205, 0, -0.3e1 / 0.8e1 * t5 * t417 * t258 - 0.3e1 / 0.8e1 * t223 * t266 + t264 * t273 / 0.4e1 - 0.5e1 / 0.36e2 * t271 * t306 * t248 * t257)
  d111 = 0.3e1 * t203 + 0.3e1 * t277 + t6 * (t403 + t430)

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
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = t21 * f.p.zeta_threshold
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t20, t22, t23 * t19)
  t26 = t6 ** (0.1e1 / 0.3e1)
  t28 = t5 * t25 * t26
  t29 = 6 ** (0.1e1 / 0.3e1)
  t30 = params.a1 * t29
  t31 = jnp.pi ** 2
  t32 = t31 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = 0.1e1 / t33
  t35 = t34 * s0
  t36 = r0 ** 2
  t37 = r0 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t41 = t35 / t38 / t36
  t44 = t29 ** 2
  t45 = params.a2 * t44
  t47 = 0.1e1 / t32 / t31
  t48 = s0 ** 2
  t49 = t47 * t48
  t50 = t36 ** 2
  t51 = t50 * r0
  t54 = t49 / t37 / t51
  t57 = t31 ** 2
  t58 = 0.1e1 / t57
  t59 = params.a3 * t58
  t60 = t48 * s0
  t61 = t50 ** 2
  t63 = t60 / t61
  t66 = 0.1e1 + t30 * t41 / 0.24e2 + t45 * t54 / 0.576e3 + t59 * t63 / 0.2304e4
  t67 = params.b1 * t29
  t70 = params.b2 * t44
  t73 = params.b3 * t58
  t76 = 0.1e1 + t67 * t41 / 0.24e2 + t70 * t54 / 0.576e3 + t73 * t63 / 0.2304e4
  t77 = t76 ** 2
  t79 = 0.1e1 / t77 / t76
  t80 = t66 * t79
  t81 = t36 * r0
  t84 = t35 / t38 / t81
  t87 = t50 * t36
  t90 = t49 / t37 / t87
  t93 = t61 * r0
  t95 = t60 / t93
  t98 = -t67 * t84 / 0.9e1 - t70 * t90 / 0.108e3 - t73 * t95 / 0.288e3
  t101 = t35 / t38 / t50
  t107 = t49 / t37 / t50 / t81
  t112 = t60 / t61 / t36
  t115 = 0.11e2 / 0.27e2 * t67 * t101 + 0.19e2 / 0.324e3 * t70 * t107 + t73 * t112 / 0.32e2
  t116 = t98 * t115
  t117 = t80 * t116
  t120 = t23 ** 2
  t121 = 0.1e1 / t120
  t122 = t6 ** 2
  t123 = 0.1e1 / t122
  t125 = -t16 * t123 + t7
  t126 = f.my_piecewise5(t10, 0, t14, 0, t125)
  t127 = t126 ** 2
  t130 = t122 * t6
  t131 = 0.1e1 / t130
  t134 = 0.2e1 * t16 * t131 - 0.2e1 * t123
  t135 = f.my_piecewise5(t10, 0, t14, 0, t134)
  t139 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t121 * t127 + 0.4e1 / 0.3e1 * t23 * t135)
  t140 = t5 * t139
  t141 = t26 ** 2
  t142 = 0.1e1 / t141
  t143 = t142 * t66
  t144 = 0.1e1 / t76
  t145 = t143 * t144
  t150 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t126)
  t151 = t5 * t150
  t153 = 0.1e1 / t141 / t6
  t154 = t153 * t66
  t155 = t154 * t144
  t164 = -t30 * t84 / 0.9e1 - t45 * t90 / 0.108e3 - t59 * t95 / 0.288e3
  t165 = t142 * t164
  t166 = t165 * t144
  t175 = 0.11e2 / 0.27e2 * t30 * t101 + 0.19e2 / 0.324e3 * t45 * t107 + t59 * t112 / 0.32e2
  t176 = t26 * t175
  t177 = t176 * t144
  t180 = t5 * t25
  t181 = t153 * t164
  t182 = t181 * t144
  t185 = t142 * t175
  t186 = t185 * t144
  t191 = t35 / t38 / t51
  t196 = t49 / t37 / t61
  t201 = t60 / t61 / t81
  t204 = -0.154e3 / 0.81e2 * t30 * t191 - 0.209e3 / 0.486e3 * t45 * t196 - 0.5e1 / 0.16e2 * t59 * t201
  t205 = t26 * t204
  t206 = t205 * t144
  t210 = 0.1e1 / t141 / t122
  t211 = t210 * t66
  t212 = t211 * t144
  t216 = 0.1e1 / t120 / t19
  t220 = t121 * t126
  t223 = t122 ** 2
  t224 = 0.1e1 / t223
  t227 = -0.6e1 * t16 * t224 + 0.6e1 * t131
  t228 = f.my_piecewise5(t10, 0, t14, 0, t227)
  t232 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t216 * t127 * t126 + 0.4e1 / 0.3e1 * t220 * t135 + 0.4e1 / 0.3e1 * t23 * t228)
  t233 = t5 * t232
  t234 = t26 * t66
  t235 = t234 * t144
  t238 = t26 * t164
  t239 = t238 * t144
  t242 = t98 ** 2
  t243 = t79 * t242
  t244 = t143 * t243
  t247 = -0.9e1 / 0.4e1 * t28 * t117 - 0.3e1 / 0.8e1 * t140 * t145 + t151 * t155 / 0.4e1 - 0.3e1 / 0.4e1 * t151 * t166 - 0.9e1 / 0.8e1 * t151 * t177 + t180 * t182 / 0.4e1 - 0.3e1 / 0.8e1 * t180 * t186 - 0.3e1 / 0.8e1 * t180 * t206 - 0.5e1 / 0.36e2 * t180 * t212 - 0.3e1 / 0.8e1 * t233 * t235 - 0.9e1 / 0.8e1 * t140 * t239 - 0.3e1 / 0.4e1 * t180 * t244
  t248 = t238 * t243
  t251 = 0.1e1 / t77
  t252 = t251 * t98
  t253 = t176 * t252
  t256 = t251 * t115
  t257 = t238 * t256
  t266 = -0.154e3 / 0.81e2 * t67 * t191 - 0.209e3 / 0.486e3 * t70 * t196 - 0.5e1 / 0.16e2 * t73 * t201
  t267 = t251 * t266
  t268 = t234 * t267
  t271 = t234 * t252
  t274 = t143 * t252
  t277 = t238 * t252
  t280 = t234 * t256
  t283 = t154 * t252
  t286 = t165 * t252
  t289 = t143 * t256
  t292 = t77 ** 2
  t293 = 0.1e1 / t292
  t295 = t293 * t242 * t98
  t296 = t234 * t295
  t299 = t234 * t243
  t302 = -0.9e1 / 0.4e1 * t180 * t248 + 0.9e1 / 0.8e1 * t180 * t253 + 0.9e1 / 0.8e1 * t180 * t257 + 0.3e1 / 0.8e1 * t180 * t268 + 0.9e1 / 0.8e1 * t140 * t271 + 0.3e1 / 0.4e1 * t151 * t274 + 0.9e1 / 0.4e1 * t151 * t277 + 0.9e1 / 0.8e1 * t151 * t280 - t180 * t283 / 0.4e1 + 0.3e1 / 0.4e1 * t180 * t286 + 0.3e1 / 0.8e1 * t180 * t289 + 0.9e1 / 0.4e1 * t180 * t296 - 0.9e1 / 0.4e1 * t151 * t299
  t304 = f.my_piecewise3(t1, 0, t247 + t302)
  t306 = r1 <= f.p.dens_threshold
  t307 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t308 = 0.1e1 + t307
  t309 = t308 <= f.p.zeta_threshold
  t310 = t308 ** (0.1e1 / 0.3e1)
  t311 = t310 ** 2
  t313 = 0.1e1 / t311 / t308
  t315 = f.my_piecewise5(t14, 0, t10, 0, -t125)
  t316 = t315 ** 2
  t320 = 0.1e1 / t311
  t321 = t320 * t315
  t323 = f.my_piecewise5(t14, 0, t10, 0, -t134)
  t327 = f.my_piecewise5(t14, 0, t10, 0, -t227)
  t331 = f.my_piecewise3(t309, 0, -0.8e1 / 0.27e2 * t313 * t316 * t315 + 0.4e1 / 0.3e1 * t321 * t323 + 0.4e1 / 0.3e1 * t310 * t327)
  t332 = t5 * t331
  t334 = r1 ** 2
  t335 = r1 ** (0.1e1 / 0.3e1)
  t336 = t335 ** 2
  t339 = t34 * s2 / t336 / t334
  t342 = s2 ** 2
  t344 = t334 ** 2
  t348 = t47 * t342 / t335 / t344 / r1
  t352 = t344 ** 2
  t354 = t342 * s2 / t352
  t357 = 0.1e1 + t30 * t339 / 0.24e2 + t45 * t348 / 0.576e3 + t59 * t354 / 0.2304e4
  t366 = 0.1e1 / (0.1e1 + t67 * t339 / 0.24e2 + t70 * t348 / 0.576e3 + t73 * t354 / 0.2304e4)
  t367 = t26 * t357 * t366
  t375 = f.my_piecewise3(t309, 0, 0.4e1 / 0.9e1 * t320 * t316 + 0.4e1 / 0.3e1 * t310 * t323)
  t376 = t5 * t375
  t378 = t142 * t357 * t366
  t383 = f.my_piecewise3(t309, 0, 0.4e1 / 0.3e1 * t310 * t315)
  t384 = t5 * t383
  t386 = t153 * t357 * t366
  t390 = f.my_piecewise3(t309, t22, t310 * t308)
  t391 = t5 * t390
  t393 = t210 * t357 * t366
  t397 = f.my_piecewise3(t306, 0, -0.3e1 / 0.8e1 * t332 * t367 - 0.3e1 / 0.8e1 * t376 * t378 + t384 * t386 / 0.4e1 - 0.5e1 / 0.36e2 * t391 * t393)
  t409 = t242 ** 2
  t422 = t115 ** 2
  t432 = 0.9e1 / 0.2e1 * t140 * t277 + 0.9e1 / 0.4e1 * t140 * t280 + 0.3e1 * t151 * t286 + 0.3e1 / 0.2e1 * t151 * t289 - 0.9e1 * t180 * t234 / t292 / t76 * t409 + 0.3e1 / 0.2e1 * t140 * t274 - 0.9e1 / 0.2e1 * t140 * t299 - t151 * t283 + 0.5e1 / 0.9e1 * t180 * t211 * t252 - 0.9e1 / 0.4e1 * t180 * t234 * t79 * t422 + t180 * t154 * t243 + 0.3e1 * t180 * t143 * t295
  t467 = 0.9e1 * t180 * t238 * t295 + 0.3e1 / 0.2e1 * t180 * t185 * t252 + 0.3e1 / 0.2e1 * t180 * t165 * t256 + t180 * t143 * t267 / 0.2e1 - t180 * t181 * t252 - t180 * t154 * t256 / 0.2e1 + 0.9e1 * t151 * t296 - 0.3e1 * t151 * t244 - 0.3e1 * t180 * t165 * t243 - 0.9e1 * t151 * t248 - 0.9e1 / 0.2e1 * t180 * t176 * t243 + 0.9e1 / 0.2e1 * t151 * t253 + 0.3e1 / 0.2e1 * t180 * t205 * t252
  t481 = t35 / t38 / t87
  t486 = t49 / t37 / t93
  t491 = t60 / t61 / t50
  t526 = t19 ** 2
  t529 = t127 ** 2
  t535 = t135 ** 2
  t544 = -0.24e2 * t224 + 0.24e2 * t16 / t223 / t6
  t545 = f.my_piecewise5(t10, 0, t14, 0, t544)
  t549 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t120 / t526 * t529 - 0.16e2 / 0.9e1 * t216 * t127 * t135 + 0.4e1 / 0.3e1 * t121 * t535 + 0.16e2 / 0.9e1 * t220 * t228 + 0.4e1 / 0.3e1 * t23 * t545)
  t553 = 0.9e1 / 0.4e1 * t180 * t176 * t256 + 0.9e1 / 0.2e1 * t151 * t257 + 0.3e1 / 0.2e1 * t180 * t238 * t267 + 0.3e1 / 0.2e1 * t151 * t268 + 0.3e1 / 0.8e1 * t180 * t234 * t251 * (0.2618e4 / 0.243e3 * t67 * t481 + 0.5225e4 / 0.1458e4 * t70 * t486 + 0.55e2 / 0.16e2 * t73 * t491) + 0.3e1 / 0.2e1 * t233 * t271 - 0.9e1 * t28 * t164 * t79 * t116 - 0.3e1 * t28 * t80 * t98 * t266 - 0.3e1 * t5 * t25 * t142 * t117 + 0.27e2 / 0.2e1 * t28 * t66 * t293 * t242 * t115 - 0.9e1 * t5 * t150 * t26 * t117 - 0.5e1 / 0.9e1 * t180 * t210 * t164 * t144 - 0.3e1 / 0.8e1 * t5 * t549 * t235
  t580 = 0.1e1 / t141 / t130
  t596 = -0.3e1 / 0.2e1 * t233 * t239 - 0.9e1 / 0.4e1 * t140 * t177 - 0.3e1 / 0.2e1 * t151 * t186 - t180 * t142 * t204 * t144 / 0.2e1 - 0.3e1 / 0.8e1 * t180 * t26 * (0.2618e4 / 0.243e3 * t30 * t481 + 0.5225e4 / 0.1458e4 * t45 * t486 + 0.55e2 / 0.16e2 * t59 * t491) * t144 - t233 * t145 / 0.2e1 - 0.3e1 / 0.2e1 * t140 * t166 + 0.10e2 / 0.27e2 * t180 * t580 * t66 * t144 + t140 * t155 / 0.2e1 - 0.5e1 / 0.9e1 * t151 * t212 + t151 * t182 - 0.3e1 / 0.2e1 * t151 * t206 + t180 * t153 * t175 * t144 / 0.2e1
  t599 = f.my_piecewise3(t1, 0, t432 + t467 + t553 + t596)
  t600 = t308 ** 2
  t603 = t316 ** 2
  t609 = t323 ** 2
  t615 = f.my_piecewise5(t14, 0, t10, 0, -t544)
  t619 = f.my_piecewise3(t309, 0, 0.40e2 / 0.81e2 / t311 / t600 * t603 - 0.16e2 / 0.9e1 * t313 * t316 * t323 + 0.4e1 / 0.3e1 * t320 * t609 + 0.16e2 / 0.9e1 * t321 * t327 + 0.4e1 / 0.3e1 * t310 * t615)
  t634 = f.my_piecewise3(t306, 0, -0.3e1 / 0.8e1 * t5 * t619 * t367 - t332 * t378 / 0.2e1 + t376 * t386 / 0.2e1 - 0.5e1 / 0.9e1 * t384 * t393 + 0.10e2 / 0.27e2 * t391 * t580 * t357 * t366)
  d1111 = 0.4e1 * t304 + 0.4e1 * t397 + t6 * (t599 + t634)

  res = {'v4rho4': d1111}
  return res
