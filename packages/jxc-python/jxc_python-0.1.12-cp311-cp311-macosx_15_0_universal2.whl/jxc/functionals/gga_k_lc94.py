"""Generated from gga_k_lc94.mpl."""

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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
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
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))
  params_expo_raw = params.expo
  if isinstance(params_expo_raw, (str, bytes, dict)):
    params_expo = params_expo_raw
  else:
    try:
      params_expo_seq = list(params_expo_raw)
    except TypeError:
      params_expo = params_expo_raw
    else:
      params_expo_seq = np.asarray(params_expo_seq, dtype=np.float64)
      params_expo = np.concatenate((np.array([np.nan], dtype=np.float64), params_expo_seq))
  params_f_raw = params.f
  if isinstance(params_f_raw, (str, bytes, dict)):
    params_f = params_f_raw
  else:
    try:
      params_f_seq = list(params_f_raw)
    except TypeError:
      params_f = params_f_raw
    else:
      params_f_seq = np.asarray(params_f_seq, dtype=np.float64)
      params_f = np.concatenate((np.array([np.nan], dtype=np.float64), params_f_seq))

  pw91_num = lambda s: (params_c + params_d * jnp.exp(-params_alpha * s ** 2)) * s ** 2 - params_f * s ** params_expo

  pw91_den = lambda s: 1 + s * params_a * jnp.arcsinh(params_b * s) + params_f * s ** params_expo

  pw91_f = lambda x: 1 + pw91_num(X2S * x) / pw91_den(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pw91_f, rs, z, xs0, xs1)

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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
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
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))
  params_expo_raw = params.expo
  if isinstance(params_expo_raw, (str, bytes, dict)):
    params_expo = params_expo_raw
  else:
    try:
      params_expo_seq = list(params_expo_raw)
    except TypeError:
      params_expo = params_expo_raw
    else:
      params_expo_seq = np.asarray(params_expo_seq, dtype=np.float64)
      params_expo = np.concatenate((np.array([np.nan], dtype=np.float64), params_expo_seq))
  params_f_raw = params.f
  if isinstance(params_f_raw, (str, bytes, dict)):
    params_f = params_f_raw
  else:
    try:
      params_f_seq = list(params_f_raw)
    except TypeError:
      params_f = params_f_raw
    else:
      params_f_seq = np.asarray(params_f_seq, dtype=np.float64)
      params_f = np.concatenate((np.array([np.nan], dtype=np.float64), params_f_seq))

  pw91_num = lambda s: (params_c + params_d * jnp.exp(-params_alpha * s ** 2)) * s ** 2 - params_f * s ** params_expo

  pw91_den = lambda s: 1 + s * params_a * jnp.arcsinh(params_b * s) + params_f * s ** params_expo

  pw91_f = lambda x: 1 + pw91_num(X2S * x) / pw91_den(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pw91_f, rs, z, xs0, xs1)

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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
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
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))
  params_expo_raw = params.expo
  if isinstance(params_expo_raw, (str, bytes, dict)):
    params_expo = params_expo_raw
  else:
    try:
      params_expo_seq = list(params_expo_raw)
    except TypeError:
      params_expo = params_expo_raw
    else:
      params_expo_seq = np.asarray(params_expo_seq, dtype=np.float64)
      params_expo = np.concatenate((np.array([np.nan], dtype=np.float64), params_expo_seq))
  params_f_raw = params.f
  if isinstance(params_f_raw, (str, bytes, dict)):
    params_f = params_f_raw
  else:
    try:
      params_f_seq = list(params_f_raw)
    except TypeError:
      params_f = params_f_raw
    else:
      params_f_seq = np.asarray(params_f_seq, dtype=np.float64)
      params_f = np.concatenate((np.array([np.nan], dtype=np.float64), params_f_seq))

  pw91_num = lambda s: (params_c + params_d * jnp.exp(-params_alpha * s ** 2)) * s ** 2 - params_f * s ** params_expo

  pw91_den = lambda s: 1 + s * params_a * jnp.arcsinh(params_b * s) + params_f * s ** params_expo

  pw91_f = lambda x: 1 + pw91_num(X2S * x) / pw91_den(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pw91_f, rs, z, xs0, xs1)

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
  t33 = params.alpha * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t44 = t38 * t43
  t47 = jnp.exp(-t33 * t44 / 0.24e2)
  t50 = (params.d * t47 + params.c) * t32
  t53 = t32 ** 2
  t54 = 0.1e1 / t35
  t55 = t53 * t54
  t56 = jnp.sqrt(s0)
  t58 = 0.1e1 / t40 / r0
  t62 = (t55 * t56 * t58 / 0.12e2) ** params.expo
  t63 = params.f * t62
  t64 = t50 * t44 / 0.24e2 - t63
  t65 = t55 * t56
  t67 = params.b * t53
  t72 = jnp.arcsinh(t67 * t54 * t56 * t58 / 0.12e2)
  t73 = t58 * params.a * t72
  t76 = 0.1e1 + t65 * t73 / 0.12e2 + t63
  t77 = 0.1e1 / t76
  t79 = t64 * t77 + 0.1e1
  t83 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t79)
  t84 = r1 <= f.p.dens_threshold
  t85 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t86 = 0.1e1 + t85
  t87 = t86 <= f.p.zeta_threshold
  t88 = t86 ** (0.1e1 / 0.3e1)
  t89 = t88 ** 2
  t91 = f.my_piecewise3(t87, t24, t89 * t86)
  t92 = t91 * t30
  t93 = t37 * s2
  t94 = r1 ** 2
  t95 = r1 ** (0.1e1 / 0.3e1)
  t96 = t95 ** 2
  t98 = 0.1e1 / t96 / t94
  t99 = t93 * t98
  t102 = jnp.exp(-t33 * t99 / 0.24e2)
  t105 = (params.d * t102 + params.c) * t32
  t108 = jnp.sqrt(s2)
  t110 = 0.1e1 / t95 / r1
  t114 = (t55 * t108 * t110 / 0.12e2) ** params.expo
  t115 = params.f * t114
  t116 = t105 * t99 / 0.24e2 - t115
  t117 = t55 * t108
  t123 = jnp.arcsinh(t67 * t54 * t108 * t110 / 0.12e2)
  t124 = t110 * params.a * t123
  t127 = 0.1e1 + t117 * t124 / 0.12e2 + t115
  t128 = 0.1e1 / t127
  t130 = t116 * t128 + 0.1e1
  t134 = f.my_piecewise3(t84, 0, 0.3e1 / 0.20e2 * t6 * t92 * t130)
  t135 = t7 ** 2
  t137 = t17 / t135
  t138 = t8 - t137
  t139 = f.my_piecewise5(t11, 0, t15, 0, t138)
  t142 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t139)
  t147 = 0.1e1 / t29
  t151 = t6 * t28 * t147 * t79 / 0.10e2
  t153 = params.d * params.alpha * t53
  t155 = 0.1e1 / t35 / t34
  t156 = s0 ** 2
  t158 = t39 ** 2
  t168 = 0.1e1 / t41 / t39 / r0
  t175 = 0.4e1 / 0.3e1 * t63 * params.expo / r0
  t178 = t76 ** 2
  t180 = t64 / t178
  t187 = t32 * t37
  t190 = params.b ** 2
  t191 = t190 * t32
  t195 = jnp.sqrt(0.6e1 * t191 * t44 + 0.144e3)
  t196 = 0.1e1 / t195
  t208 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t142 * t30 * t79 + t151 + 0.3e1 / 0.20e2 * t6 * t31 * ((t153 * t155 * t156 / t40 / t158 / t39 * t47 / 0.216e3 - t50 * t38 * t168 / 0.9e1 + t175) * t77 - t180 * (-t65 / t40 / t39 * params.a * t72 / 0.9e1 - 0.2e1 / 0.3e1 * t187 * s0 * t168 * params.a * params.b * t196 - t175)))
  t210 = f.my_piecewise5(t15, 0, t11, 0, -t138)
  t213 = f.my_piecewise3(t87, 0, 0.5e1 / 0.3e1 * t89 * t210)
  t221 = t6 * t91 * t147 * t130 / 0.10e2
  t223 = f.my_piecewise3(t84, 0, 0.3e1 / 0.20e2 * t6 * t213 * t30 * t130 + t221)
  vrho_0_ = t83 + t134 + t7 * (t208 + t223)
  t226 = -t8 - t137
  t227 = f.my_piecewise5(t11, 0, t15, 0, t226)
  t230 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t227)
  t236 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t230 * t30 * t79 + t151)
  t238 = f.my_piecewise5(t15, 0, t11, 0, -t226)
  t241 = f.my_piecewise3(t87, 0, 0.5e1 / 0.3e1 * t89 * t238)
  t246 = s2 ** 2
  t248 = t94 ** 2
  t258 = 0.1e1 / t96 / t94 / r1
  t265 = 0.4e1 / 0.3e1 * t115 * params.expo / r1
  t268 = t127 ** 2
  t270 = t116 / t268
  t282 = jnp.sqrt(0.6e1 * t191 * t99 + 0.144e3)
  t283 = 0.1e1 / t282
  t295 = f.my_piecewise3(t84, 0, 0.3e1 / 0.20e2 * t6 * t241 * t30 * t130 + t221 + 0.3e1 / 0.20e2 * t6 * t92 * ((t153 * t155 * t246 / t95 / t248 / t94 * t102 / 0.216e3 - t105 * t93 * t258 / 0.9e1 + t265) * t128 - t270 * (-t117 / t95 / t94 * params.a * t123 / 0.9e1 - 0.2e1 / 0.3e1 * t187 * s2 * t258 * params.a * params.b * t283 - t265)))
  vrho_1_ = t83 + t134 + t7 * (t236 + t295)
  t312 = t63 * params.expo / s0 / 0.2e1
  t320 = params.a * params.b
  t330 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * ((-t153 * t155 / t40 / t158 / r0 * t47 * s0 / 0.576e3 + t50 * t37 * t43 / 0.24e2 - t312) * t77 - t180 * (t55 / t56 * t73 / 0.24e2 + t187 * t43 * t320 * t196 / 0.4e1 + t312)))
  vsigma_0_ = t7 * t330
  vsigma_1_ = 0.0e0
  t345 = t115 * params.expo / s2 / 0.2e1
  t362 = f.my_piecewise3(t84, 0, 0.3e1 / 0.20e2 * t6 * t92 * ((-t153 * t155 / t95 / t248 / r1 * t102 * s2 / 0.576e3 + t105 * t37 * t98 / 0.24e2 - t345) * t128 - t270 * (t55 / t108 * t124 / 0.24e2 + t187 * t98 * t320 * t283 / 0.4e1 + t345)))
  vsigma_2_ = t7 * t362
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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
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
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))
  params_expo_raw = params.expo
  if isinstance(params_expo_raw, (str, bytes, dict)):
    params_expo = params_expo_raw
  else:
    try:
      params_expo_seq = list(params_expo_raw)
    except TypeError:
      params_expo = params_expo_raw
    else:
      params_expo_seq = np.asarray(params_expo_seq, dtype=np.float64)
      params_expo = np.concatenate((np.array([np.nan], dtype=np.float64), params_expo_seq))
  params_f_raw = params.f
  if isinstance(params_f_raw, (str, bytes, dict)):
    params_f = params_f_raw
  else:
    try:
      params_f_seq = list(params_f_raw)
    except TypeError:
      params_f = params_f_raw
    else:
      params_f_seq = np.asarray(params_f_seq, dtype=np.float64)
      params_f = np.concatenate((np.array([np.nan], dtype=np.float64), params_f_seq))

  pw91_num = lambda s: (params_c + params_d * jnp.exp(-params_alpha * s ** 2)) * s ** 2 - params_f * s ** params_expo

  pw91_den = lambda s: 1 + s * params_a * jnp.arcsinh(params_b * s) + params_f * s ** params_expo

  pw91_f = lambda x: 1 + pw91_num(X2S * x) / pw91_den(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pw91_f, rs, z, xs0, xs1)

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
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t36 = 0.1e1 / t22 / t34
  t37 = t33 * t36
  t40 = jnp.exp(-params.alpha * t24 * t29 * t37 / 0.24e2)
  t43 = (params.d * t40 + params.c) * t24
  t44 = t43 * t29
  t47 = t24 ** 2
  t48 = 0.1e1 / t27
  t49 = t47 * t48
  t50 = jnp.sqrt(s0)
  t53 = 0.1e1 / t21 / r0
  t54 = t50 * t31 * t53
  t57 = (t49 * t54 / 0.12e2) ** params.expo
  t58 = params.f * t57
  t59 = t44 * t37 / 0.24e2 - t58
  t60 = t49 * t50
  t66 = jnp.arcsinh(params.b * t47 * t48 * t54 / 0.12e2)
  t67 = params.a * t66
  t68 = t31 * t53 * t67
  t71 = 0.1e1 + t60 * t68 / 0.12e2 + t58
  t72 = 0.1e1 / t71
  t74 = t59 * t72 + 0.1e1
  t78 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t74)
  t88 = params.d * params.alpha * t47 / t27 / t26
  t89 = s0 ** 2
  t91 = t34 ** 2
  t101 = 0.1e1 / t22 / t34 / r0
  t108 = 0.4e1 / 0.3e1 * t58 * params.expo / r0
  t111 = t71 ** 2
  t113 = t59 / t111
  t120 = t24 * t29
  t123 = params.b ** 2
  t129 = jnp.sqrt(0.6e1 * t123 * t24 * t29 * t37 + 0.144e3)
  t131 = params.b / t129
  t142 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t74 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * ((t88 * t89 * t31 / t21 / t91 / t34 * t40 / 0.108e3 - t44 * t33 * t101 / 0.9e1 + t108) * t72 - t113 * (-t60 * t31 / t21 / t34 * t67 / 0.9e1 - 0.2e1 / 0.3e1 * t120 * t33 * t101 * params.a * t131 - t108)))
  vrho_0_ = 0.2e1 * r0 * t142 + 0.2e1 * t78
  t160 = t58 * params.expo / s0 / 0.2e1
  t178 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * ((-t88 * t31 / t21 / t91 / r0 * t40 * s0 / 0.288e3 + t43 * t29 * t32 * t36 / 0.24e2 - t160) * t72 - t113 * (t49 / t50 * t68 / 0.24e2 + t120 * t32 * t36 * params.a * t131 / 0.4e1 + t160)))
  vsigma_0_ = 0.2e1 * r0 * t178
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
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t37 = 0.1e1 / t35 / t34
  t38 = t33 * t37
  t41 = jnp.exp(-params.alpha * t24 * t29 * t38 / 0.24e2)
  t44 = (params.d * t41 + params.c) * t24
  t45 = t44 * t29
  t48 = t24 ** 2
  t49 = 0.1e1 / t27
  t50 = t48 * t49
  t51 = jnp.sqrt(s0)
  t54 = 0.1e1 / t21 / r0
  t55 = t51 * t31 * t54
  t58 = (t50 * t55 / 0.12e2) ** params.expo
  t59 = params.f * t58
  t60 = t45 * t38 / 0.24e2 - t59
  t61 = t50 * t51
  t67 = jnp.arcsinh(params.b * t48 * t49 * t55 / 0.12e2)
  t68 = params.a * t67
  t69 = t31 * t54 * t68
  t72 = 0.1e1 + t61 * t69 / 0.12e2 + t59
  t73 = 0.1e1 / t72
  t75 = t60 * t73 + 0.1e1
  t79 = t20 * t35
  t80 = params.d * params.alpha
  t82 = 0.1e1 / t27 / t26
  t83 = t48 * t82
  t84 = t80 * t83
  t85 = s0 ** 2
  t86 = t85 * t31
  t87 = t34 ** 2
  t90 = 0.1e1 / t21 / t87 / t34
  t95 = t34 * r0
  t97 = 0.1e1 / t35 / t95
  t101 = 0.1e1 / r0
  t104 = 0.4e1 / 0.3e1 * t59 * params.expo * t101
  t105 = t84 * t86 * t90 * t41 / 0.108e3 - t45 * t33 * t97 / 0.9e1 + t104
  t107 = t72 ** 2
  t108 = 0.1e1 / t107
  t109 = t60 * t108
  t113 = t31 / t21 / t34 * t68
  t116 = t24 * t29
  t117 = t116 * t33
  t119 = params.b ** 2
  t124 = 0.6e1 * t119 * t24 * t29 * t38 + 0.144e3
  t125 = jnp.sqrt(t124)
  t127 = params.b / t125
  t128 = t97 * params.a * t127
  t131 = -t61 * t113 / 0.9e1 - 0.2e1 / 0.3e1 * t117 * t128 - t104
  t133 = t105 * t73 - t109 * t131
  t138 = f.my_piecewise3(t2, 0, t7 * t23 * t75 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t79 * t133)
  t149 = 0.1e1 / t21 / t87 / t95
  t154 = params.alpha ** 2
  t156 = t26 ** 2
  t158 = params.d * t154 / t156
  t160 = t87 ** 2
  t168 = 0.1e1 / t35 / t87
  t172 = params.expo ** 2
  t173 = 0.1e1 / t34
  t176 = 0.16e2 / 0.9e1 * t59 * t172 * t173
  t179 = 0.4e1 / 0.3e1 * t59 * params.expo * t173
  t182 = t105 * t108
  t187 = t60 / t107 / t72
  t188 = t131 ** 2
  t203 = t119 * params.b
  t205 = 0.1e1 / t125 / t124
  t206 = t203 * t205
  t217 = f.my_piecewise3(t2, 0, -t7 * t20 * t54 * t75 / 0.30e2 + t7 * t23 * t133 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t79 * ((-t84 * t86 * t149 * t41 / 0.12e2 + t158 * t85 * s0 / t160 / t34 * t41 / 0.81e2 + 0.11e2 / 0.27e2 * t45 * t33 * t168 - t176 - t179) * t73 - 0.2e1 * t182 * t131 + 0.2e1 * t187 * t188 - t109 * (0.7e1 / 0.27e2 * t61 * t31 / t21 / t95 * t68 + 0.10e2 / 0.3e1 * t117 * t168 * params.a * t127 - 0.32e2 / 0.3e1 * t83 * t86 * t149 * params.a * t206 + t176 + t179)))
  v2rho2_0_ = 0.2e1 * r0 * t217 + 0.4e1 * t138
  t222 = 0.1e1 / t21 / t87 / r0
  t224 = t41 * s0
  t228 = t29 * t32
  t232 = 0.1e1 / s0
  t235 = t59 * params.expo * t232 / 0.2e1
  t236 = -t84 * t31 * t222 * t224 / 0.288e3 + t44 * t228 * t37 / 0.24e2 - t235
  t239 = t50 / t51
  t242 = t116 * t32
  t244 = t37 * params.a * t127
  t247 = t239 * t69 / 0.24e2 + t242 * t244 / 0.4e1 + t235
  t249 = -t109 * t247 + t236 * t73
  t253 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t79 * t249)
  t257 = t31 * t90
  t273 = 0.2e1 / 0.3e1 * t59 * t172 * t101 * t232
  t276 = t236 * t108
  t298 = f.my_piecewise3(t2, 0, t7 * t23 * t249 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t79 * ((t84 * t257 * t224 / 0.36e2 - t158 / t160 / r0 * t85 * t41 / 0.216e3 - t44 * t228 * t97 / 0.9e1 + t273) * t73 - t276 * t131 - t182 * t247 + 0.2e1 * t187 * t247 * t131 - t109 * (-t239 * t113 / 0.18e2 - t242 * t128 + 0.4e1 * t83 * t257 * params.a * t203 * t205 * s0 - t273)))
  v2rhosigma_0_ = 0.2e1 * r0 * t298 + 0.2e1 * t253
  t312 = 0.1e1 / t85
  t315 = t59 * t172 * t312 / 0.4e1
  t318 = t59 * params.expo * t312 / 0.2e1
  t323 = t247 ** 2
  t346 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t79 * ((t158 / t160 * t41 * s0 / 0.576e3 - t80 * t48 * t82 * t31 * t222 * t41 / 0.144e3 - t315 + t318) * t73 - 0.2e1 * t276 * t247 + 0.2e1 * t187 * t323 - t109 * (-t50 / t51 / s0 * t69 / 0.48e2 + t116 * t232 * t32 * t244 / 0.8e1 - 0.3e1 / 0.2e1 * t83 * t31 * t222 * params.a * t206 + t315 - t318)))
  v2sigma2_0_ = 0.2e1 * r0 * t346
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
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
  t24 = t20 * t23
  t25 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = r0 ** 2
  t36 = t21 ** 2
  t39 = t34 / t36 / t35
  t42 = jnp.exp(-params.alpha * t25 * t30 * t39 / 0.24e2)
  t46 = (params.d * t42 + params.c) * t25 * t30
  t49 = t25 ** 2
  t50 = 0.1e1 / t28
  t51 = t49 * t50
  t52 = jnp.sqrt(s0)
  t54 = t52 * t32 * t23
  t57 = (t51 * t54 / 0.12e2) ** params.expo
  t58 = params.f * t57
  t59 = t46 * t39 / 0.24e2 - t58
  t60 = t51 * t52
  t66 = jnp.asinh(params.b * t49 * t50 * t54 / 0.12e2)
  t67 = params.a * t66
  t71 = 0.1e1 + t60 * t32 * t23 * t67 / 0.12e2 + t58
  t72 = 0.1e1 / t71
  t74 = t59 * t72 + 0.1e1
  t79 = t20 / t21
  t83 = t49 / t28 / t27
  t84 = params.d * params.alpha * t83
  t85 = s0 ** 2
  t86 = t85 * t32
  t87 = t35 ** 2
  t95 = t35 * r0
  t97 = 0.1e1 / t36 / t95
  t104 = 0.4e1 / 0.3e1 * t58 * params.expo / r0
  t105 = t84 * t86 / t21 / t87 / t35 * t42 / 0.108e3 - t46 * t34 * t97 / 0.9e1 + t104
  t107 = t71 ** 2
  t108 = 0.1e1 / t107
  t109 = t59 * t108
  t111 = 0.1e1 / t21 / t35
  t117 = t25 * t30 * t34
  t119 = params.b ** 2
  t124 = 0.6e1 * t119 * t25 * t30 * t39 + 0.144e3
  t125 = jnp.sqrt(t124)
  t127 = params.b / t125
  t131 = -t60 * t32 * t111 * t67 / 0.9e1 - 0.2e1 / 0.3e1 * t117 * t97 * params.a * t127 - t104
  t133 = t105 * t72 - t109 * t131
  t137 = t20 * t36
  t140 = 0.1e1 / t21 / t87 / t95
  t145 = params.alpha ** 2
  t147 = t27 ** 2
  t148 = 0.1e1 / t147
  t149 = params.d * t145 * t148
  t150 = t85 * s0
  t151 = t87 ** 2
  t159 = 0.1e1 / t36 / t87
  t163 = params.expo ** 2
  t164 = 0.1e1 / t35
  t167 = 0.16e2 / 0.9e1 * t58 * t163 * t164
  t170 = 0.4e1 / 0.3e1 * t58 * params.expo * t164
  t171 = -t84 * t86 * t140 * t42 / 0.12e2 + t149 * t150 / t151 / t35 * t42 / 0.81e2 + 0.11e2 / 0.27e2 * t46 * t34 * t159 - t167 - t170
  t173 = t105 * t108
  t177 = 0.1e1 / t107 / t71
  t178 = t59 * t177
  t179 = t131 ** 2
  t192 = t83 * t86
  t197 = t119 * params.b / t125 / t124
  t201 = 0.7e1 / 0.27e2 * t60 * t32 / t21 / t95 * t67 + 0.10e2 / 0.3e1 * t117 * t159 * params.a * t127 - 0.32e2 / 0.3e1 * t192 * t140 * params.a * t197 + t167 + t170
  t203 = -t109 * t201 - 0.2e1 * t173 * t131 + t171 * t72 + 0.2e1 * t178 * t179
  t208 = f.my_piecewise3(t2, 0, -t7 * t24 * t74 / 0.30e2 + t7 * t79 * t133 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t137 * t203)
  t221 = 0.1e1 / t21 / t151
  t227 = 0.1e1 / t151 / t95
  t234 = t85 ** 2
  t237 = t87 * r0
  t248 = 0.1e1 / t36 / t237
  t253 = 0.1e1 / t95
  t256 = 0.64e2 / 0.27e2 * t58 * t163 * params.expo * t253
  t259 = 0.16e2 / 0.3e1 * t58 * t163 * t253
  t262 = 0.8e1 / 0.3e1 * t58 * params.expo * t253
  t273 = t107 ** 2
  t298 = t119 ** 2
  t301 = t124 ** 2
  t314 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t111 * t74 - t7 * t24 * t133 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t79 * t203 + 0.3e1 / 0.20e2 * t7 * t137 * ((0.341e3 / 0.486e3 * t84 * t86 * t221 * t42 - 0.19e2 / 0.81e2 * t149 * t150 * t227 * t42 + params.d * t145 * params.alpha * t148 * t234 / t36 / t151 / t237 * t25 * t30 * t33 * t42 / 0.729e3 - 0.154e3 / 0.81e2 * t46 * t34 * t248 + t256 + t259 + t262) * t72 - 0.3e1 * t171 * t108 * t131 + 0.6e1 * t105 * t177 * t179 - 0.3e1 * t173 * t201 - 0.6e1 * t59 / t273 * t179 * t131 + 0.6e1 * t178 * t131 * t201 - t109 * (-0.70e2 / 0.81e2 * t60 * t32 / t21 / t87 * t67 - 0.476e3 / 0.27e2 * t117 * t248 * params.a * t127 + 0.1184e4 / 0.9e1 * t192 * t221 * params.a * t197 - 0.3072e4 * t148 * t150 * t227 * params.a * t298 * params.b / t125 / t301 - t256 - t259 - t262)))
  v3rho3_0_ = 0.2e1 * r0 * t314 + 0.6e1 * t208

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
  t25 = t20 * t24
  t26 = 6 ** (0.1e1 / 0.3e1)
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = 0.1e1 / t30
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = s0 * t34
  t36 = t22 ** 2
  t39 = t35 / t36 / t21
  t42 = jnp.exp(-params.alpha * t26 * t31 * t39 / 0.24e2)
  t46 = (params.d * t42 + params.c) * t26 * t31
  t49 = t26 ** 2
  t50 = 0.1e1 / t29
  t51 = t49 * t50
  t52 = jnp.sqrt(s0)
  t55 = 0.1e1 / t22 / r0
  t56 = t52 * t33 * t55
  t59 = (t51 * t56 / 0.12e2) ** params.expo
  t60 = params.f * t59
  t61 = t46 * t39 / 0.24e2 - t60
  t62 = t51 * t52
  t68 = jnp.asinh(params.b * t49 * t50 * t56 / 0.12e2)
  t69 = params.a * t68
  t73 = 0.1e1 + t62 * t33 * t55 * t69 / 0.12e2 + t60
  t74 = 0.1e1 / t73
  t76 = t61 * t74 + 0.1e1
  t80 = t20 * t55
  t83 = 0.1e1 / t29 / t28
  t84 = t49 * t83
  t85 = params.d * params.alpha * t84
  t86 = s0 ** 2
  t87 = t86 * t33
  t88 = t21 ** 2
  t89 = t88 * t21
  t96 = t21 * r0
  t98 = 0.1e1 / t36 / t96
  t105 = 0.4e1 / 0.3e1 * t60 * params.expo / r0
  t106 = t85 * t87 / t22 / t89 * t42 / 0.108e3 - t46 * t35 * t98 / 0.9e1 + t105
  t108 = t73 ** 2
  t109 = 0.1e1 / t108
  t110 = t61 * t109
  t115 = t26 * t31
  t116 = t115 * t35
  t118 = params.b ** 2
  t123 = 0.6e1 * t118 * t26 * t31 * t39 + 0.144e3
  t124 = jnp.sqrt(t123)
  t126 = params.b / t124
  t130 = -t62 * t33 * t24 * t69 / 0.9e1 - 0.2e1 / 0.3e1 * t116 * t98 * params.a * t126 - t105
  t132 = t106 * t74 - t110 * t130
  t137 = t20 / t22
  t140 = 0.1e1 / t22 / t88 / t96
  t145 = params.alpha ** 2
  t147 = t28 ** 2
  t148 = 0.1e1 / t147
  t149 = params.d * t145 * t148
  t150 = t86 * s0
  t151 = t88 ** 2
  t159 = 0.1e1 / t36 / t88
  t163 = params.expo ** 2
  t164 = 0.1e1 / t21
  t167 = 0.16e2 / 0.9e1 * t60 * t163 * t164
  t170 = 0.4e1 / 0.3e1 * t60 * params.expo * t164
  t171 = -t85 * t87 * t140 * t42 / 0.12e2 + t149 * t150 / t151 / t21 * t42 / 0.81e2 + 0.11e2 / 0.27e2 * t46 * t35 * t159 - t167 - t170
  t173 = t106 * t109
  t177 = 0.1e1 / t108 / t73
  t178 = t61 * t177
  t179 = t130 ** 2
  t183 = 0.1e1 / t22 / t96
  t192 = t84 * t87
  t194 = t118 * params.b
  t197 = t194 / t124 / t123
  t201 = 0.7e1 / 0.27e2 * t62 * t33 * t183 * t69 + 0.10e2 / 0.3e1 * t116 * t159 * params.a * t126 - 0.32e2 / 0.3e1 * t192 * t140 * params.a * t197 + t167 + t170
  t203 = -t110 * t201 - 0.2e1 * t173 * t130 + t171 * t74 + 0.2e1 * t178 * t179
  t207 = t20 * t36
  t209 = 0.1e1 / t22 / t151
  t215 = 0.1e1 / t151 / t96
  t222 = t86 ** 2
  t223 = t148 * t222
  t224 = params.d * t145 * params.alpha * t223
  t225 = t88 * r0
  t231 = t31 * t34 * t42
  t236 = 0.1e1 / t36 / t225
  t240 = t163 * params.expo
  t241 = 0.1e1 / t96
  t244 = 0.64e2 / 0.27e2 * t60 * t240 * t241
  t247 = 0.16e2 / 0.3e1 * t60 * t163 * t241
  t250 = 0.8e1 / 0.3e1 * t60 * params.expo * t241
  t251 = 0.341e3 / 0.486e3 * t85 * t87 * t209 * t42 - 0.19e2 / 0.81e2 * t149 * t150 * t215 * t42 + t224 / t36 / t151 / t225 * t26 * t231 / 0.729e3 - 0.154e3 / 0.81e2 * t46 * t35 * t236 + t244 + t247 + t250
  t253 = t171 * t109
  t256 = t106 * t177
  t261 = t108 ** 2
  t262 = 0.1e1 / t261
  t263 = t61 * t262
  t264 = t179 * t130
  t267 = t130 * t201
  t284 = t148 * t150
  t286 = t118 ** 2
  t289 = t123 ** 2
  t292 = params.a * t286 * params.b / t124 / t289
  t295 = -0.70e2 / 0.81e2 * t62 * t33 / t22 / t88 * t69 - 0.476e3 / 0.27e2 * t116 * t236 * params.a * t126 + 0.1184e4 / 0.9e1 * t192 * t209 * params.a * t197 - 0.3072e4 * t284 * t215 * t292 - t244 - t247 - t250
  t297 = -t110 * t295 - 0.3e1 * t253 * t130 - 0.3e1 * t173 * t201 + 0.6e1 * t178 * t267 + 0.6e1 * t256 * t179 + t251 * t74 - 0.6e1 * t263 * t264
  t302 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t76 - t7 * t80 * t132 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t137 * t203 + 0.3e1 / 0.20e2 * t7 * t207 * t297)
  t319 = 0.1e1 / t22 / t151 / r0
  t325 = 0.1e1 / t151 / t88
  t332 = 0.1e1 / t36 / t151 / t89
  t337 = t145 ** 2
  t342 = t151 ** 2
  t353 = 0.1e1 / t36 / t89
  t357 = t163 ** 2
  t358 = 0.1e1 / t88
  t361 = 0.256e3 / 0.81e2 * t60 * t357 * t358
  t364 = 0.128e3 / 0.9e1 * t60 * t240 * t358
  t367 = 0.176e3 / 0.9e1 * t60 * t163 * t358
  t370 = 0.8e1 * t60 * params.expo * t358
  t391 = t179 ** 2
  t397 = t201 ** 2
  t433 = (-0.3047e4 / 0.486e3 * t85 * t87 * t319 * t42 + 0.2563e4 / 0.729e3 * t149 * t150 * t325 * t42 - 0.98e2 / 0.2187e4 * t224 * t332 * t26 * t231 + 0.2e1 / 0.6561e4 * params.d * t337 * t148 * t222 * s0 / t22 / t342 / r0 * t49 * t83 * t33 * t42 + 0.2618e4 / 0.243e3 * t46 * t35 * t353 - t361 - t364 - t367 - t370) * t74 - 0.4e1 * t251 * t109 * t130 + 0.12e2 * t171 * t177 * t179 - 0.6e1 * t253 * t201 - 0.24e2 * t106 * t262 * t264 + 0.24e2 * t256 * t267 - 0.4e1 * t173 * t295 + 0.24e2 * t61 / t261 / t73 * t391 - 0.36e2 * t263 * t179 * t201 + 0.6e1 * t178 * t397 + 0.8e1 * t178 * t130 * t295 - t110 * (0.910e3 / 0.243e3 * t62 * t33 / t22 / t225 * t69 + 0.2884e4 / 0.27e2 * t116 * t353 * params.a * t126 - 0.37216e5 / 0.27e2 * t192 * t319 * params.a * t197 + 0.71680e5 * t284 * t325 * t292 - 0.122880e6 * t223 * t332 * params.a * t286 * t194 / t124 / t289 / t123 * t115 * t34 + t361 + t364 + t367 + t370)
  t438 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t183 * t76 + 0.8e1 / 0.45e2 * t7 * t25 * t132 - t7 * t80 * t203 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t137 * t297 + 0.3e1 / 0.20e2 * t7 * t207 * t433)
  v4rho4_0_ = 0.2e1 * r0 * t438 + 0.8e1 * t302

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
  t36 = params.alpha * t35
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t41 = t40 * s0
  t42 = r0 ** 2
  t43 = r0 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t47 = t41 / t44 / t42
  t50 = jnp.exp(-t36 * t47 / 0.24e2)
  t53 = (params.d * t50 + params.c) * t35
  t56 = t35 ** 2
  t57 = 0.1e1 / t38
  t58 = t56 * t57
  t59 = jnp.sqrt(s0)
  t61 = 0.1e1 / t43 / r0
  t65 = (t58 * t59 * t61 / 0.12e2) ** params.expo
  t66 = params.f * t65
  t67 = t53 * t47 / 0.24e2 - t66
  t68 = t58 * t59
  t70 = params.b * t56
  t75 = jnp.arcsinh(t70 * t57 * t59 * t61 / 0.12e2)
  t79 = 0.1e1 + t68 * t61 * params.a * t75 / 0.12e2 + t66
  t80 = 0.1e1 / t79
  t82 = t67 * t80 + 0.1e1
  t86 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t87 = t86 ** 2
  t88 = t87 * f.p.zeta_threshold
  t90 = f.my_piecewise3(t21, t88, t23 * t20)
  t91 = 0.1e1 / t32
  t92 = t90 * t91
  t95 = t6 * t92 * t82 / 0.10e2
  t96 = t90 * t33
  t98 = params.d * params.alpha * t56
  t100 = 0.1e1 / t38 / t37
  t101 = s0 ** 2
  t102 = t100 * t101
  t103 = t42 ** 2
  t111 = t42 * r0
  t113 = 0.1e1 / t44 / t111
  t120 = 0.4e1 / 0.3e1 * t66 * params.expo / r0
  t121 = t98 * t102 / t43 / t103 / t42 * t50 / 0.216e3 - t53 * t41 * t113 / 0.9e1 + t120
  t123 = t79 ** 2
  t124 = 0.1e1 / t123
  t125 = t67 * t124
  t132 = t35 * t40
  t133 = t132 * s0
  t135 = params.b ** 2
  t136 = t135 * t35
  t139 = 0.6e1 * t136 * t47 + 0.144e3
  t140 = jnp.sqrt(t139)
  t142 = params.b / t140
  t146 = -t68 / t43 / t42 * params.a * t75 / 0.9e1 - 0.2e1 / 0.3e1 * t133 * t113 * params.a * t142 - t120
  t148 = t121 * t80 - t125 * t146
  t153 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t82 + t95 + 0.3e1 / 0.20e2 * t6 * t96 * t148)
  t155 = r1 <= f.p.dens_threshold
  t156 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t157 = 0.1e1 + t156
  t158 = t157 <= f.p.zeta_threshold
  t159 = t157 ** (0.1e1 / 0.3e1)
  t160 = t159 ** 2
  t162 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t165 = f.my_piecewise3(t158, 0, 0.5e1 / 0.3e1 * t160 * t162)
  t166 = t165 * t33
  t167 = t40 * s2
  t168 = r1 ** 2
  t169 = r1 ** (0.1e1 / 0.3e1)
  t170 = t169 ** 2
  t173 = t167 / t170 / t168
  t176 = jnp.exp(-t36 * t173 / 0.24e2)
  t179 = (params.d * t176 + params.c) * t35
  t182 = jnp.sqrt(s2)
  t184 = 0.1e1 / t169 / r1
  t188 = (t58 * t182 * t184 / 0.12e2) ** params.expo
  t189 = params.f * t188
  t190 = t179 * t173 / 0.24e2 - t189
  t191 = t58 * t182
  t197 = jnp.arcsinh(t70 * t57 * t182 * t184 / 0.12e2)
  t201 = 0.1e1 + t191 * t184 * params.a * t197 / 0.12e2 + t189
  t202 = 0.1e1 / t201
  t204 = t190 * t202 + 0.1e1
  t209 = f.my_piecewise3(t158, t88, t160 * t157)
  t210 = t209 * t91
  t213 = t6 * t210 * t204 / 0.10e2
  t215 = f.my_piecewise3(t155, 0, 0.3e1 / 0.20e2 * t6 * t166 * t204 + t213)
  t217 = 0.1e1 / t22
  t218 = t28 ** 2
  t223 = t17 / t24 / t7
  t225 = -0.2e1 * t25 + 0.2e1 * t223
  t226 = f.my_piecewise5(t11, 0, t15, 0, t225)
  t230 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t217 * t218 + 0.5e1 / 0.3e1 * t23 * t226)
  t237 = t6 * t31 * t91 * t82
  t243 = 0.1e1 / t32 / t7
  t247 = t6 * t90 * t243 * t82 / 0.30e2
  t249 = t6 * t92 * t148
  t253 = 0.1e1 / t43 / t103 / t111
  t258 = params.alpha ** 2
  t260 = t37 ** 2
  t262 = params.d * t258 / t260
  t264 = t103 ** 2
  t272 = 0.1e1 / t44 / t103
  t276 = params.expo ** 2
  t277 = 0.1e1 / t42
  t280 = 0.16e2 / 0.9e1 * t66 * t276 * t277
  t283 = 0.4e1 / 0.3e1 * t66 * params.expo * t277
  t292 = t146 ** 2
  t305 = t56 * t100
  t308 = t135 * params.b
  t322 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t230 * t33 * t82 + t237 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t148 - t247 + t249 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t96 * ((-t98 * t102 * t253 * t50 / 0.24e2 + t262 * t101 * s0 / t264 / t42 * t50 / 0.324e3 + 0.11e2 / 0.27e2 * t53 * t41 * t272 - t280 - t283) * t80 - 0.2e1 * t121 * t124 * t146 + 0.2e1 * t67 / t123 / t79 * t292 - t125 * (0.7e1 / 0.27e2 * t68 / t43 / t111 * params.a * t75 + 0.10e2 / 0.3e1 * t133 * t272 * params.a * t142 - 0.16e2 / 0.3e1 * t305 * t101 * t253 * params.a * t308 / t140 / t139 + t280 + t283)))
  t323 = 0.1e1 / t159
  t324 = t162 ** 2
  t328 = f.my_piecewise5(t15, 0, t11, 0, -t225)
  t332 = f.my_piecewise3(t158, 0, 0.10e2 / 0.9e1 * t323 * t324 + 0.5e1 / 0.3e1 * t160 * t328)
  t339 = t6 * t165 * t91 * t204
  t344 = t6 * t209 * t243 * t204 / 0.30e2
  t346 = f.my_piecewise3(t155, 0, 0.3e1 / 0.20e2 * t6 * t332 * t33 * t204 + t339 / 0.5e1 - t344)
  d11 = 0.2e1 * t153 + 0.2e1 * t215 + t7 * (t322 + t346)
  t349 = -t8 - t26
  t350 = f.my_piecewise5(t11, 0, t15, 0, t349)
  t353 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t350)
  t354 = t353 * t33
  t359 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t354 * t82 + t95)
  t361 = f.my_piecewise5(t15, 0, t11, 0, -t349)
  t364 = f.my_piecewise3(t158, 0, 0.5e1 / 0.3e1 * t160 * t361)
  t365 = t364 * t33
  t369 = t209 * t33
  t370 = s2 ** 2
  t371 = t100 * t370
  t372 = t168 ** 2
  t380 = t168 * r1
  t382 = 0.1e1 / t170 / t380
  t389 = 0.4e1 / 0.3e1 * t189 * params.expo / r1
  t390 = t98 * t371 / t169 / t372 / t168 * t176 / 0.216e3 - t179 * t167 * t382 / 0.9e1 + t389
  t392 = t201 ** 2
  t393 = 0.1e1 / t392
  t394 = t190 * t393
  t401 = t132 * s2
  t405 = 0.6e1 * t136 * t173 + 0.144e3
  t406 = jnp.sqrt(t405)
  t408 = params.b / t406
  t412 = -t191 / t169 / t168 * params.a * t197 / 0.9e1 - 0.2e1 / 0.3e1 * t401 * t382 * params.a * t408 - t389
  t414 = t390 * t202 - t394 * t412
  t419 = f.my_piecewise3(t155, 0, 0.3e1 / 0.20e2 * t6 * t365 * t204 + t213 + 0.3e1 / 0.20e2 * t6 * t369 * t414)
  t423 = 0.2e1 * t223
  t424 = f.my_piecewise5(t11, 0, t15, 0, t423)
  t428 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t217 * t350 * t28 + 0.5e1 / 0.3e1 * t23 * t424)
  t435 = t6 * t353 * t91 * t82
  t443 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t428 * t33 * t82 + t435 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t354 * t148 + t237 / 0.10e2 - t247 + t249 / 0.10e2)
  t447 = f.my_piecewise5(t15, 0, t11, 0, -t423)
  t451 = f.my_piecewise3(t158, 0, 0.10e2 / 0.9e1 * t323 * t361 * t162 + 0.5e1 / 0.3e1 * t160 * t447)
  t458 = t6 * t364 * t91 * t204
  t465 = t6 * t210 * t414
  t468 = f.my_piecewise3(t155, 0, 0.3e1 / 0.20e2 * t6 * t451 * t33 * t204 + t458 / 0.10e2 + t339 / 0.10e2 - t344 + 0.3e1 / 0.20e2 * t6 * t166 * t414 + t465 / 0.10e2)
  d12 = t153 + t215 + t359 + t419 + t7 * (t443 + t468)
  t473 = t350 ** 2
  t477 = 0.2e1 * t25 + 0.2e1 * t223
  t478 = f.my_piecewise5(t11, 0, t15, 0, t477)
  t482 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t217 * t473 + 0.5e1 / 0.3e1 * t23 * t478)
  t489 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t482 * t33 * t82 + t435 / 0.5e1 - t247)
  t490 = t361 ** 2
  t494 = f.my_piecewise5(t15, 0, t11, 0, -t477)
  t498 = f.my_piecewise3(t158, 0, 0.10e2 / 0.9e1 * t323 * t490 + 0.5e1 / 0.3e1 * t160 * t494)
  t510 = 0.1e1 / t169 / t372 / t380
  t516 = t372 ** 2
  t524 = 0.1e1 / t170 / t372
  t528 = 0.1e1 / t168
  t531 = 0.16e2 / 0.9e1 * t189 * t276 * t528
  t534 = 0.4e1 / 0.3e1 * t189 * params.expo * t528
  t543 = t412 ** 2
  t571 = f.my_piecewise3(t155, 0, 0.3e1 / 0.20e2 * t6 * t498 * t33 * t204 + t458 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t365 * t414 - t344 + t465 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t369 * ((-t98 * t371 * t510 * t176 / 0.24e2 + t262 * t370 * s2 / t516 / t168 * t176 / 0.324e3 + 0.11e2 / 0.27e2 * t179 * t167 * t524 - t531 - t534) * t202 - 0.2e1 * t390 * t393 * t412 + 0.2e1 * t190 / t392 / t201 * t543 - t394 * (0.7e1 / 0.27e2 * t191 / t169 / t380 * params.a * t197 + 0.10e2 / 0.3e1 * t401 * t524 * params.a * t408 - 0.16e2 / 0.3e1 * t305 * t370 * t510 * params.a * t308 / t406 / t405 + t531 + t534)))
  d22 = 0.2e1 * t359 + 0.2e1 * t419 + t7 * (t489 + t571)
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
  t47 = params.alpha * t46
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t52 = t51 * s0
  t53 = r0 ** 2
  t54 = r0 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t58 = t52 / t55 / t53
  t61 = jnp.exp(-t47 * t58 / 0.24e2)
  t64 = (params.d * t61 + params.c) * t46
  t67 = t46 ** 2
  t68 = 0.1e1 / t49
  t69 = t67 * t68
  t70 = jnp.sqrt(s0)
  t72 = 0.1e1 / t54 / r0
  t76 = (t69 * t70 * t72 / 0.12e2) ** params.expo
  t77 = params.f * t76
  t78 = t64 * t58 / 0.24e2 - t77
  t79 = t69 * t70
  t81 = params.b * t67
  t86 = jnp.asinh(t81 * t68 * t70 * t72 / 0.12e2)
  t90 = 0.1e1 + t79 * t72 * params.a * t86 / 0.12e2 + t77
  t91 = 0.1e1 / t90
  t93 = t78 * t91 + 0.1e1
  t99 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t100 = 0.1e1 / t43
  t101 = t99 * t100
  t105 = t99 * t44
  t107 = params.d * params.alpha * t67
  t109 = 0.1e1 / t49 / t48
  t110 = s0 ** 2
  t111 = t109 * t110
  t112 = t53 ** 2
  t120 = t53 * r0
  t122 = 0.1e1 / t55 / t120
  t129 = 0.4e1 / 0.3e1 * t77 * params.expo / r0
  t130 = t107 * t111 / t54 / t112 / t53 * t61 / 0.216e3 - t64 * t52 * t122 / 0.9e1 + t129
  t132 = t90 ** 2
  t133 = 0.1e1 / t132
  t134 = t78 * t133
  t142 = t46 * t51 * s0
  t144 = params.b ** 2
  t148 = 0.6e1 * t144 * t46 * t58 + 0.144e3
  t149 = jnp.sqrt(t148)
  t151 = params.b / t149
  t155 = -t79 / t54 / t53 * params.a * t86 / 0.9e1 - 0.2e1 / 0.3e1 * t142 * t122 * params.a * t151 - t129
  t157 = t130 * t91 - t134 * t155
  t161 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t162 = t161 ** 2
  t163 = t162 * f.p.zeta_threshold
  t165 = f.my_piecewise3(t21, t163, t32 * t20)
  t167 = 0.1e1 / t43 / t7
  t168 = t165 * t167
  t172 = t165 * t100
  t176 = t165 * t44
  t179 = 0.1e1 / t54 / t112 / t120
  t184 = params.alpha ** 2
  t186 = t48 ** 2
  t187 = 0.1e1 / t186
  t188 = params.d * t184 * t187
  t189 = t110 * s0
  t190 = t112 ** 2
  t198 = 0.1e1 / t55 / t112
  t202 = params.expo ** 2
  t203 = 0.1e1 / t53
  t206 = 0.16e2 / 0.9e1 * t77 * t202 * t203
  t209 = 0.4e1 / 0.3e1 * t77 * params.expo * t203
  t210 = -t107 * t111 * t179 * t61 / 0.24e2 + t188 * t189 / t190 / t53 * t61 / 0.324e3 + 0.11e2 / 0.27e2 * t64 * t52 * t198 - t206 - t209
  t212 = t130 * t133
  t216 = 0.1e1 / t132 / t90
  t217 = t78 * t216
  t218 = t155 ** 2
  t232 = t67 * t109 * t110
  t237 = t144 * params.b / t149 / t148
  t241 = 0.7e1 / 0.27e2 * t79 / t54 / t120 * params.a * t86 + 0.10e2 / 0.3e1 * t142 * t198 * params.a * t151 - 0.16e2 / 0.3e1 * t232 * t179 * params.a * t237 + t206 + t209
  t243 = -t134 * t241 - 0.2e1 * t212 * t155 + t210 * t91 + 0.2e1 * t217 * t218
  t248 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t93 + t6 * t101 * t93 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t105 * t157 - t6 * t168 * t93 / 0.30e2 + t6 * t172 * t157 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t176 * t243)
  t250 = r1 <= f.p.dens_threshold
  t251 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t252 = 0.1e1 + t251
  t253 = t252 <= f.p.zeta_threshold
  t254 = t252 ** (0.1e1 / 0.3e1)
  t255 = 0.1e1 / t254
  t257 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t258 = t257 ** 2
  t261 = t254 ** 2
  t263 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t267 = f.my_piecewise3(t253, 0, 0.10e2 / 0.9e1 * t255 * t258 + 0.5e1 / 0.3e1 * t261 * t263)
  t270 = r1 ** 2
  t271 = r1 ** (0.1e1 / 0.3e1)
  t272 = t271 ** 2
  t275 = t51 * s2 / t272 / t270
  t278 = jnp.exp(-t47 * t275 / 0.24e2)
  t284 = jnp.sqrt(s2)
  t286 = 0.1e1 / t271 / r1
  t290 = (t69 * t284 * t286 / 0.12e2) ** params.expo
  t291 = params.f * t290
  t299 = jnp.asinh(t81 * t68 * t284 * t286 / 0.12e2)
  t306 = 0.1e1 + ((params.d * t278 + params.c) * t46 * t275 / 0.24e2 - t291) / (0.1e1 + t69 * t284 * t286 * params.a * t299 / 0.12e2 + t291)
  t312 = f.my_piecewise3(t253, 0, 0.5e1 / 0.3e1 * t261 * t257)
  t318 = f.my_piecewise3(t253, t163, t261 * t252)
  t324 = f.my_piecewise3(t250, 0, 0.3e1 / 0.20e2 * t6 * t267 * t44 * t306 + t6 * t312 * t100 * t306 / 0.5e1 - t6 * t318 * t167 * t306 / 0.30e2)
  t334 = t24 ** 2
  t338 = 0.6e1 * t34 - 0.6e1 * t17 / t334
  t339 = f.my_piecewise5(t11, 0, t15, 0, t338)
  t343 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t339)
  t366 = 0.1e1 / t43 / t24
  t378 = 0.1e1 / t54 / t190
  t384 = 0.1e1 / t190 / t120
  t391 = t110 ** 2
  t394 = t112 * r0
  t404 = 0.1e1 / t55 / t394
  t409 = 0.1e1 / t120
  t412 = 0.64e2 / 0.27e2 * t77 * t202 * params.expo * t409
  t415 = 0.16e2 / 0.3e1 * t77 * t202 * t409
  t418 = 0.8e1 / 0.3e1 * t77 * params.expo * t409
  t429 = t132 ** 2
  t454 = t144 ** 2
  t457 = t148 ** 2
  t470 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t343 * t44 * t93 + 0.3e1 / 0.10e2 * t6 * t42 * t100 * t93 + 0.9e1 / 0.20e2 * t6 * t45 * t157 - t6 * t99 * t167 * t93 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t101 * t157 + 0.9e1 / 0.20e2 * t6 * t105 * t243 + 0.2e1 / 0.45e2 * t6 * t165 * t366 * t93 - t6 * t168 * t157 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t172 * t243 + 0.3e1 / 0.20e2 * t6 * t176 * ((0.341e3 / 0.972e3 * t107 * t111 * t378 * t61 - 0.19e2 / 0.324e3 * t188 * t189 * t384 * t61 + params.d * t184 * params.alpha * t187 * t391 / t55 / t190 / t394 * t46 * t51 * t61 / 0.2916e4 - 0.154e3 / 0.81e2 * t64 * t52 * t404 + t412 + t415 + t418) * t91 - 0.3e1 * t210 * t133 * t155 + 0.6e1 * t130 * t216 * t218 - 0.3e1 * t212 * t241 - 0.6e1 * t78 / t429 * t218 * t155 + 0.6e1 * t217 * t155 * t241 - t134 * (-0.70e2 / 0.81e2 * t79 / t54 / t112 * params.a * t86 - 0.476e3 / 0.27e2 * t142 * t404 * params.a * t151 + 0.592e3 / 0.9e1 * t232 * t378 * params.a * t237 - 0.768e3 * t187 * t189 * t384 * params.a * t454 * params.b / t149 / t457 - t412 - t415 - t418)))
  t480 = f.my_piecewise5(t15, 0, t11, 0, -t338)
  t484 = f.my_piecewise3(t253, 0, -0.10e2 / 0.27e2 / t254 / t252 * t258 * t257 + 0.10e2 / 0.3e1 * t255 * t257 * t263 + 0.5e1 / 0.3e1 * t261 * t480)
  t502 = f.my_piecewise3(t250, 0, 0.3e1 / 0.20e2 * t6 * t484 * t44 * t306 + 0.3e1 / 0.10e2 * t6 * t267 * t100 * t306 - t6 * t312 * t167 * t306 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t318 * t366 * t306)
  d111 = 0.3e1 * t248 + 0.3e1 * t324 + t7 * (t470 + t502)

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
  t59 = params.alpha * t58
  t60 = jnp.pi ** 2
  t61 = t60 ** (0.1e1 / 0.3e1)
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t64 = t63 * s0
  t65 = r0 ** 2
  t66 = r0 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t70 = t64 / t67 / t65
  t73 = jnp.exp(-t59 * t70 / 0.24e2)
  t76 = (params.d * t73 + params.c) * t58
  t79 = t58 ** 2
  t80 = 0.1e1 / t61
  t81 = t79 * t80
  t82 = jnp.sqrt(s0)
  t84 = 0.1e1 / t66 / r0
  t88 = (t81 * t82 * t84 / 0.12e2) ** params.expo
  t89 = params.f * t88
  t90 = t76 * t70 / 0.24e2 - t89
  t91 = t81 * t82
  t93 = params.b * t79
  t98 = jnp.asinh(t93 * t80 * t82 * t84 / 0.12e2)
  t102 = 0.1e1 + t91 * t84 * params.a * t98 / 0.12e2 + t89
  t103 = 0.1e1 / t102
  t105 = t90 * t103 + 0.1e1
  t114 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t115 = 0.1e1 / t55
  t116 = t114 * t115
  t120 = t114 * t56
  t122 = params.d * params.alpha * t79
  t124 = 0.1e1 / t61 / t60
  t125 = s0 ** 2
  t126 = t124 * t125
  t127 = t65 ** 2
  t128 = t127 * t65
  t135 = t65 * r0
  t137 = 0.1e1 / t67 / t135
  t144 = 0.4e1 / 0.3e1 * t89 * params.expo / r0
  t145 = t122 * t126 / t66 / t128 * t73 / 0.216e3 - t76 * t64 * t137 / 0.9e1 + t144
  t147 = t102 ** 2
  t148 = 0.1e1 / t147
  t149 = t90 * t148
  t156 = t58 * t63
  t157 = t156 * s0
  t159 = params.b ** 2
  t163 = 0.6e1 * t159 * t58 * t70 + 0.144e3
  t164 = jnp.sqrt(t163)
  t166 = params.b / t164
  t170 = -t91 / t66 / t65 * params.a * t98 / 0.9e1 - 0.2e1 / 0.3e1 * t157 * t137 * params.a * t166 - t144
  t172 = t145 * t103 - t149 * t170
  t178 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t180 = 0.1e1 / t55 / t7
  t181 = t178 * t180
  t185 = t178 * t115
  t189 = t178 * t56
  t192 = 0.1e1 / t66 / t127 / t135
  t197 = params.alpha ** 2
  t199 = t60 ** 2
  t200 = 0.1e1 / t199
  t201 = params.d * t197 * t200
  t202 = t125 * s0
  t203 = t127 ** 2
  t211 = 0.1e1 / t67 / t127
  t215 = params.expo ** 2
  t216 = 0.1e1 / t65
  t219 = 0.16e2 / 0.9e1 * t89 * t215 * t216
  t222 = 0.4e1 / 0.3e1 * t89 * params.expo * t216
  t223 = -t122 * t126 * t192 * t73 / 0.24e2 + t201 * t202 / t203 / t65 * t73 / 0.324e3 + 0.11e2 / 0.27e2 * t76 * t64 * t211 - t219 - t222
  t225 = t145 * t148
  t229 = 0.1e1 / t147 / t102
  t230 = t90 * t229
  t231 = t170 ** 2
  t245 = t79 * t124 * t125
  t247 = t159 * params.b
  t250 = t247 / t164 / t163
  t254 = 0.7e1 / 0.27e2 * t91 / t66 / t135 * params.a * t98 + 0.10e2 / 0.3e1 * t157 * t211 * params.a * t166 - 0.16e2 / 0.3e1 * t245 * t192 * params.a * t250 + t219 + t222
  t256 = t223 * t103 - t149 * t254 - 0.2e1 * t225 * t170 + 0.2e1 * t230 * t231
  t260 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t261 = t260 ** 2
  t262 = t261 * f.p.zeta_threshold
  t264 = f.my_piecewise3(t21, t262, t44 * t20)
  t266 = 0.1e1 / t55 / t25
  t267 = t264 * t266
  t271 = t264 * t180
  t275 = t264 * t115
  t279 = t264 * t56
  t281 = 0.1e1 / t66 / t203
  t287 = 0.1e1 / t203 / t135
  t294 = t125 ** 2
  t295 = t200 * t294
  t296 = params.d * t197 * params.alpha * t295
  t297 = t127 * r0
  t302 = t63 * t73
  t307 = 0.1e1 / t67 / t297
  t311 = t215 * params.expo
  t312 = 0.1e1 / t135
  t315 = 0.64e2 / 0.27e2 * t89 * t311 * t312
  t318 = 0.16e2 / 0.3e1 * t89 * t215 * t312
  t321 = 0.8e1 / 0.3e1 * t89 * params.expo * t312
  t322 = 0.341e3 / 0.972e3 * t122 * t126 * t281 * t73 - 0.19e2 / 0.324e3 * t201 * t202 * t287 * t73 + t296 / t67 / t203 / t297 * t58 * t302 / 0.2916e4 - 0.154e3 / 0.81e2 * t76 * t64 * t307 + t315 + t318 + t321
  t324 = t223 * t148
  t327 = t145 * t229
  t332 = t147 ** 2
  t333 = 0.1e1 / t332
  t334 = t90 * t333
  t335 = t231 * t170
  t338 = t170 * t254
  t355 = t200 * t202
  t357 = t159 ** 2
  t360 = t163 ** 2
  t363 = params.a * t357 * params.b / t164 / t360
  t366 = -0.70e2 / 0.81e2 * t91 / t66 / t127 * params.a * t98 - 0.476e3 / 0.27e2 * t157 * t307 * params.a * t166 + 0.592e3 / 0.9e1 * t245 * t281 * params.a * t250 - 0.768e3 * t355 * t287 * t363 - t315 - t318 - t321
  t368 = t322 * t103 - t149 * t366 - 0.3e1 * t324 * t170 - 0.3e1 * t225 * t254 + 0.6e1 * t230 * t338 + 0.6e1 * t327 * t231 - 0.6e1 * t334 * t335
  t373 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t105 + 0.3e1 / 0.10e2 * t6 * t116 * t105 + 0.9e1 / 0.20e2 * t6 * t120 * t172 - t6 * t181 * t105 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t185 * t172 + 0.9e1 / 0.20e2 * t6 * t189 * t256 + 0.2e1 / 0.45e2 * t6 * t267 * t105 - t6 * t271 * t172 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t275 * t256 + 0.3e1 / 0.20e2 * t6 * t279 * t368)
  t375 = r1 <= f.p.dens_threshold
  t376 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t377 = 0.1e1 + t376
  t378 = t377 <= f.p.zeta_threshold
  t379 = t377 ** (0.1e1 / 0.3e1)
  t381 = 0.1e1 / t379 / t377
  t383 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t384 = t383 ** 2
  t388 = 0.1e1 / t379
  t389 = t388 * t383
  t391 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t394 = t379 ** 2
  t396 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t400 = f.my_piecewise3(t378, 0, -0.10e2 / 0.27e2 * t381 * t384 * t383 + 0.10e2 / 0.3e1 * t389 * t391 + 0.5e1 / 0.3e1 * t394 * t396)
  t403 = r1 ** 2
  t404 = r1 ** (0.1e1 / 0.3e1)
  t405 = t404 ** 2
  t408 = t63 * s2 / t405 / t403
  t411 = jnp.exp(-t59 * t408 / 0.24e2)
  t417 = jnp.sqrt(s2)
  t419 = 0.1e1 / t404 / r1
  t423 = (t81 * t417 * t419 / 0.12e2) ** params.expo
  t424 = params.f * t423
  t432 = jnp.asinh(t93 * t80 * t417 * t419 / 0.12e2)
  t439 = 0.1e1 + ((params.d * t411 + params.c) * t58 * t408 / 0.24e2 - t424) / (0.1e1 + t81 * t417 * t419 * params.a * t432 / 0.12e2 + t424)
  t448 = f.my_piecewise3(t378, 0, 0.10e2 / 0.9e1 * t388 * t384 + 0.5e1 / 0.3e1 * t394 * t391)
  t455 = f.my_piecewise3(t378, 0, 0.5e1 / 0.3e1 * t394 * t383)
  t461 = f.my_piecewise3(t378, t262, t394 * t377)
  t467 = f.my_piecewise3(t375, 0, 0.3e1 / 0.20e2 * t6 * t400 * t56 * t439 + 0.3e1 / 0.10e2 * t6 * t448 * t115 * t439 - t6 * t455 * t180 * t439 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t461 * t266 * t439)
  t470 = 0.1e1 / t55 / t36
  t492 = 0.1e1 / t66 / t203 / r0
  t498 = 0.1e1 / t203 / t127
  t505 = 0.1e1 / t67 / t203 / t128
  t510 = t197 ** 2
  t515 = t203 ** 2
  t525 = 0.1e1 / t67 / t128
  t529 = t215 ** 2
  t530 = 0.1e1 / t127
  t533 = 0.256e3 / 0.81e2 * t89 * t529 * t530
  t536 = 0.128e3 / 0.9e1 * t89 * t311 * t530
  t539 = 0.176e3 / 0.9e1 * t89 * t215 * t530
  t542 = 0.8e1 * t89 * params.expo * t530
  t563 = t231 ** 2
  t569 = t254 ** 2
  t604 = (-0.3047e4 / 0.972e3 * t122 * t126 * t492 * t73 + 0.2563e4 / 0.2916e4 * t201 * t202 * t498 * t73 - 0.49e2 / 0.4374e4 * t296 * t505 * t58 * t302 + params.d * t510 * t200 * t294 * s0 / t66 / t515 / r0 * t79 * t124 * t73 / 0.26244e5 + 0.2618e4 / 0.243e3 * t76 * t64 * t525 - t533 - t536 - t539 - t542) * t103 - 0.4e1 * t322 * t148 * t170 + 0.12e2 * t223 * t229 * t231 - 0.6e1 * t324 * t254 - 0.24e2 * t145 * t333 * t335 + 0.24e2 * t327 * t338 - 0.4e1 * t225 * t366 + 0.24e2 * t90 / t332 / t102 * t563 - 0.36e2 * t334 * t231 * t254 + 0.6e1 * t230 * t569 + 0.8e1 * t230 * t170 * t366 - t149 * (0.910e3 / 0.243e3 * t91 / t66 / t297 * params.a * t98 + 0.2884e4 / 0.27e2 * t157 * t525 * params.a * t166 - 0.18608e5 / 0.27e2 * t245 * t492 * params.a * t250 + 0.17920e5 * t355 * t498 * t363 - 0.30720e5 * t295 * t505 * params.a * t357 * t247 / t164 / t360 / t163 * t156 + t533 + t536 + t539 + t542)
  t608 = t20 ** 2
  t611 = t30 ** 2
  t617 = t41 ** 2
  t626 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t627 = f.my_piecewise5(t11, 0, t15, 0, t626)
  t631 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t608 * t611 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t617 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t627)
  t660 = -0.14e2 / 0.135e3 * t6 * t264 * t470 * t105 + 0.2e1 / 0.5e1 * t6 * t54 * t115 * t105 - t6 * t114 * t180 * t105 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t178 * t266 * t105 + 0.2e1 / 0.5e1 * t6 * t275 * t368 + 0.3e1 / 0.20e2 * t6 * t279 * t604 + 0.3e1 / 0.20e2 * t6 * t631 * t56 * t105 + 0.3e1 / 0.5e1 * t6 * t57 * t172 + 0.6e1 / 0.5e1 * t6 * t116 * t172 + 0.9e1 / 0.10e2 * t6 * t120 * t256 - 0.2e1 / 0.5e1 * t6 * t181 * t172 + 0.6e1 / 0.5e1 * t6 * t185 * t256 + 0.3e1 / 0.5e1 * t6 * t189 * t368 + 0.8e1 / 0.45e2 * t6 * t267 * t172 - t6 * t271 * t256 / 0.5e1
  t661 = f.my_piecewise3(t1, 0, t660)
  t662 = t377 ** 2
  t665 = t384 ** 2
  t671 = t391 ** 2
  t677 = f.my_piecewise5(t15, 0, t11, 0, -t626)
  t681 = f.my_piecewise3(t378, 0, 0.40e2 / 0.81e2 / t379 / t662 * t665 - 0.20e2 / 0.9e1 * t381 * t384 * t391 + 0.10e2 / 0.3e1 * t388 * t671 + 0.40e2 / 0.9e1 * t389 * t396 + 0.5e1 / 0.3e1 * t394 * t677)
  t703 = f.my_piecewise3(t375, 0, 0.3e1 / 0.20e2 * t6 * t681 * t56 * t439 + 0.2e1 / 0.5e1 * t6 * t400 * t115 * t439 - t6 * t448 * t180 * t439 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t455 * t266 * t439 - 0.14e2 / 0.135e3 * t6 * t461 * t470 * t439)
  d1111 = 0.4e1 * t373 + 0.4e1 * t467 + t7 * (t661 + t703)

  res = {'v4rho4': d1111}
  return res
