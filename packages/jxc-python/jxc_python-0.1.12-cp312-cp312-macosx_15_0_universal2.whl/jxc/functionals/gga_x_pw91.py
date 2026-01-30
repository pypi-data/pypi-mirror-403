"""Generated from gga_x_pw91.mpl."""

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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pw91_f, rs, z, xs0, xs1)

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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pw91_f, rs, z, xs0, xs1)

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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pw91_f, rs, z, xs0, xs1)

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
  t29 = params.alpha * t28
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
  t43 = jnp.exp(-t29 * t40 / 0.24e2)
  t46 = (params.d * t43 + params.c) * t28
  t49 = t28 ** 2
  t50 = 0.1e1 / t31
  t51 = t49 * t50
  t52 = jnp.sqrt(s0)
  t54 = 0.1e1 / t36 / r0
  t58 = (t51 * t52 * t54 / 0.12e2) ** params.expo
  t59 = params.f * t58
  t60 = t46 * t40 / 0.24e2 - t59
  t61 = t51 * t52
  t63 = params.b * t49
  t68 = jnp.arcsinh(t63 * t50 * t52 * t54 / 0.12e2)
  t69 = t54 * params.a * t68
  t72 = 0.1e1 + t61 * t69 / 0.12e2 + t59
  t73 = 0.1e1 / t72
  t75 = t60 * t73 + 0.1e1
  t79 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t75)
  t80 = r1 <= f.p.dens_threshold
  t81 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t82 = 0.1e1 + t81
  t83 = t82 <= f.p.zeta_threshold
  t84 = t82 ** (0.1e1 / 0.3e1)
  t86 = f.my_piecewise3(t83, t22, t84 * t82)
  t87 = t86 * t26
  t88 = t33 * s2
  t89 = r1 ** 2
  t90 = r1 ** (0.1e1 / 0.3e1)
  t91 = t90 ** 2
  t93 = 0.1e1 / t91 / t89
  t94 = t88 * t93
  t97 = jnp.exp(-t29 * t94 / 0.24e2)
  t100 = (params.d * t97 + params.c) * t28
  t103 = jnp.sqrt(s2)
  t105 = 0.1e1 / t90 / r1
  t109 = (t51 * t103 * t105 / 0.12e2) ** params.expo
  t110 = params.f * t109
  t111 = t100 * t94 / 0.24e2 - t110
  t112 = t51 * t103
  t118 = jnp.arcsinh(t63 * t50 * t103 * t105 / 0.12e2)
  t119 = t105 * params.a * t118
  t122 = 0.1e1 + t112 * t119 / 0.12e2 + t110
  t123 = 0.1e1 / t122
  t125 = t111 * t123 + 0.1e1
  t129 = f.my_piecewise3(t80, 0, -0.3e1 / 0.8e1 * t5 * t87 * t125)
  t130 = t6 ** 2
  t132 = t16 / t130
  t133 = t7 - t132
  t134 = f.my_piecewise5(t10, 0, t14, 0, t133)
  t137 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t134)
  t142 = t26 ** 2
  t143 = 0.1e1 / t142
  t147 = t5 * t25 * t143 * t75 / 0.8e1
  t149 = params.d * params.alpha * t49
  t151 = 0.1e1 / t31 / t30
  t152 = s0 ** 2
  t154 = t35 ** 2
  t164 = 0.1e1 / t37 / t35 / r0
  t171 = 0.4e1 / 0.3e1 * t59 * params.expo / r0
  t174 = t72 ** 2
  t176 = t60 / t174
  t183 = t28 * t33
  t186 = params.b ** 2
  t187 = t186 * t28
  t191 = jnp.sqrt(0.6e1 * t187 * t40 + 0.144e3)
  t192 = 0.1e1 / t191
  t204 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t137 * t26 * t75 - t147 - 0.3e1 / 0.8e1 * t5 * t27 * ((t149 * t151 * t152 / t36 / t154 / t35 * t43 / 0.216e3 - t46 * t34 * t164 / 0.9e1 + t171) * t73 - t176 * (-t61 / t36 / t35 * params.a * t68 / 0.9e1 - 0.2e1 / 0.3e1 * t183 * s0 * t164 * params.a * params.b * t192 - t171)))
  t206 = f.my_piecewise5(t14, 0, t10, 0, -t133)
  t209 = f.my_piecewise3(t83, 0, 0.4e1 / 0.3e1 * t84 * t206)
  t217 = t5 * t86 * t143 * t125 / 0.8e1
  t219 = f.my_piecewise3(t80, 0, -0.3e1 / 0.8e1 * t5 * t209 * t26 * t125 - t217)
  vrho_0_ = t79 + t129 + t6 * (t204 + t219)
  t222 = -t7 - t132
  t223 = f.my_piecewise5(t10, 0, t14, 0, t222)
  t226 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t223)
  t232 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t226 * t26 * t75 - t147)
  t234 = f.my_piecewise5(t14, 0, t10, 0, -t222)
  t237 = f.my_piecewise3(t83, 0, 0.4e1 / 0.3e1 * t84 * t234)
  t242 = s2 ** 2
  t244 = t89 ** 2
  t254 = 0.1e1 / t91 / t89 / r1
  t261 = 0.4e1 / 0.3e1 * t110 * params.expo / r1
  t264 = t122 ** 2
  t266 = t111 / t264
  t278 = jnp.sqrt(0.6e1 * t187 * t94 + 0.144e3)
  t279 = 0.1e1 / t278
  t291 = f.my_piecewise3(t80, 0, -0.3e1 / 0.8e1 * t5 * t237 * t26 * t125 - t217 - 0.3e1 / 0.8e1 * t5 * t87 * ((t149 * t151 * t242 / t90 / t244 / t89 * t97 / 0.216e3 - t100 * t88 * t254 / 0.9e1 + t261) * t123 - t266 * (-t112 / t90 / t89 * params.a * t118 / 0.9e1 - 0.2e1 / 0.3e1 * t183 * s2 * t254 * params.a * params.b * t279 - t261)))
  vrho_1_ = t79 + t129 + t6 * (t232 + t291)
  t308 = t59 * params.expo / s0 / 0.2e1
  t316 = params.a * params.b
  t326 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * ((-t149 * t151 / t36 / t154 / r0 * t43 * s0 / 0.576e3 + t46 * t33 * t39 / 0.24e2 - t308) * t73 - t176 * (t51 / t52 * t69 / 0.24e2 + t183 * t39 * t316 * t192 / 0.4e1 + t308)))
  vsigma_0_ = t6 * t326
  vsigma_1_ = 0.0e0
  t341 = t110 * params.expo / s2 / 0.2e1
  t358 = f.my_piecewise3(t80, 0, -0.3e1 / 0.8e1 * t5 * t87 * ((-t149 * t151 / t90 / t244 / r1 * t97 * s2 / 0.576e3 + t100 * t33 * t93 / 0.24e2 - t341) * t123 - t266 * (t51 / t103 * t119 / 0.24e2 + t183 * t93 * t316 * t279 / 0.4e1 + t341)))
  vsigma_2_ = t6 * t358
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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pw91_f, rs, z, xs0, xs1)

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
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t18 ** 2
  t33 = 0.1e1 / t31 / t30
  t34 = t29 * t33
  t37 = jnp.exp(-params.alpha * t20 * t25 * t34 / 0.24e2)
  t40 = (params.d * t37 + params.c) * t20
  t41 = t40 * t25
  t44 = t20 ** 2
  t45 = 0.1e1 / t23
  t46 = t44 * t45
  t47 = jnp.sqrt(s0)
  t50 = 0.1e1 / t18 / r0
  t51 = t47 * t27 * t50
  t54 = (t46 * t51 / 0.12e2) ** params.expo
  t55 = params.f * t54
  t56 = t41 * t34 / 0.24e2 - t55
  t57 = t46 * t47
  t63 = jnp.arcsinh(params.b * t44 * t45 * t51 / 0.12e2)
  t64 = params.a * t63
  t65 = t27 * t50 * t64
  t68 = 0.1e1 + t57 * t65 / 0.12e2 + t55
  t69 = 0.1e1 / t68
  t71 = t56 * t69 + 0.1e1
  t75 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t71)
  t85 = params.d * params.alpha * t44 / t23 / t22
  t86 = s0 ** 2
  t88 = t30 ** 2
  t98 = 0.1e1 / t31 / t30 / r0
  t105 = 0.4e1 / 0.3e1 * t55 * params.expo / r0
  t108 = t68 ** 2
  t110 = t56 / t108
  t117 = t20 * t25
  t120 = params.b ** 2
  t126 = jnp.sqrt(0.6e1 * t120 * t20 * t25 * t34 + 0.144e3)
  t128 = params.b / t126
  t139 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t71 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * ((t85 * t86 * t27 / t18 / t88 / t30 * t37 / 0.108e3 - t41 * t29 * t98 / 0.9e1 + t105) * t69 - t110 * (-t57 * t27 / t18 / t30 * t64 / 0.9e1 - 0.2e1 / 0.3e1 * t117 * t29 * t98 * params.a * t128 - t105)))
  vrho_0_ = 0.2e1 * r0 * t139 + 0.2e1 * t75
  t157 = t55 * params.expo / s0 / 0.2e1
  t175 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * ((-t85 * t27 / t18 / t88 / r0 * t37 * s0 / 0.288e3 + t40 * t25 * t28 * t33 / 0.24e2 - t157) * t69 - t110 * (t46 / t47 * t65 / 0.24e2 + t117 * t28 * t33 * params.a * t128 / 0.4e1 + t157)))
  vsigma_0_ = 0.2e1 * r0 * t175
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
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t35 = t31 * t34
  t38 = jnp.exp(-params.alpha * t22 * t27 * t35 / 0.24e2)
  t41 = (params.d * t38 + params.c) * t22
  t42 = t41 * t27
  t45 = t22 ** 2
  t46 = 0.1e1 / t25
  t47 = t45 * t46
  t48 = jnp.sqrt(s0)
  t51 = 0.1e1 / t18 / r0
  t52 = t48 * t29 * t51
  t55 = (t47 * t52 / 0.12e2) ** params.expo
  t56 = params.f * t55
  t57 = t42 * t35 / 0.24e2 - t56
  t58 = t47 * t48
  t64 = jnp.arcsinh(params.b * t45 * t46 * t52 / 0.12e2)
  t65 = params.a * t64
  t66 = t29 * t51 * t65
  t69 = 0.1e1 + t58 * t66 / 0.12e2 + t56
  t70 = 0.1e1 / t69
  t72 = t57 * t70 + 0.1e1
  t76 = t17 * t18
  t77 = params.d * params.alpha
  t79 = 0.1e1 / t25 / t24
  t80 = t45 * t79
  t81 = t77 * t80
  t82 = s0 ** 2
  t83 = t82 * t29
  t84 = t32 ** 2
  t87 = 0.1e1 / t18 / t84 / t32
  t92 = t32 * r0
  t94 = 0.1e1 / t19 / t92
  t98 = 0.1e1 / r0
  t101 = 0.4e1 / 0.3e1 * t56 * params.expo * t98
  t102 = t81 * t83 * t87 * t38 / 0.108e3 - t42 * t31 * t94 / 0.9e1 + t101
  t104 = t69 ** 2
  t105 = 0.1e1 / t104
  t106 = t57 * t105
  t110 = t29 / t18 / t32 * t65
  t113 = t22 * t27
  t114 = t113 * t31
  t116 = params.b ** 2
  t121 = 0.6e1 * t116 * t22 * t27 * t35 + 0.144e3
  t122 = jnp.sqrt(t121)
  t124 = params.b / t122
  t125 = t94 * params.a * t124
  t128 = -t58 * t110 / 0.9e1 - 0.2e1 / 0.3e1 * t114 * t125 - t101
  t130 = t102 * t70 - t106 * t128
  t135 = f.my_piecewise3(t2, 0, -t6 * t21 * t72 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t76 * t130)
  t148 = 0.1e1 / t18 / t84 / t92
  t153 = params.alpha ** 2
  t155 = t24 ** 2
  t157 = params.d * t153 / t155
  t159 = t84 ** 2
  t167 = 0.1e1 / t19 / t84
  t171 = params.expo ** 2
  t172 = 0.1e1 / t32
  t175 = 0.16e2 / 0.9e1 * t56 * t171 * t172
  t178 = 0.4e1 / 0.3e1 * t56 * params.expo * t172
  t181 = t102 * t105
  t186 = t57 / t104 / t69
  t187 = t128 ** 2
  t202 = t116 * params.b
  t204 = 0.1e1 / t122 / t121
  t205 = t202 * t204
  t216 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t72 / 0.12e2 - t6 * t21 * t130 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t76 * ((-t81 * t83 * t148 * t38 / 0.12e2 + t157 * t82 * s0 / t159 / t32 * t38 / 0.81e2 + 0.11e2 / 0.27e2 * t42 * t31 * t167 - t175 - t178) * t70 - 0.2e1 * t181 * t128 + 0.2e1 * t186 * t187 - t106 * (0.7e1 / 0.27e2 * t58 * t29 / t18 / t92 * t65 + 0.10e2 / 0.3e1 * t114 * t167 * params.a * t124 - 0.32e2 / 0.3e1 * t80 * t83 * t148 * params.a * t205 + t175 + t178)))
  v2rho2_0_ = 0.2e1 * r0 * t216 + 0.4e1 * t135
  t221 = 0.1e1 / t18 / t84 / r0
  t223 = t38 * s0
  t227 = t27 * t30
  t231 = 0.1e1 / s0
  t234 = t56 * params.expo * t231 / 0.2e1
  t235 = -t81 * t29 * t221 * t223 / 0.288e3 + t41 * t227 * t34 / 0.24e2 - t234
  t238 = t47 / t48
  t241 = t113 * t30
  t243 = t34 * params.a * t124
  t246 = t238 * t66 / 0.24e2 + t241 * t243 / 0.4e1 + t234
  t248 = -t106 * t246 + t235 * t70
  t252 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t76 * t248)
  t256 = t29 * t87
  t272 = 0.2e1 / 0.3e1 * t56 * t171 * t98 * t231
  t275 = t235 * t105
  t297 = f.my_piecewise3(t2, 0, -t6 * t21 * t248 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t76 * ((t81 * t256 * t223 / 0.36e2 - t157 / t159 / r0 * t82 * t38 / 0.216e3 - t41 * t227 * t94 / 0.9e1 + t272) * t70 - t275 * t128 - t181 * t246 + 0.2e1 * t186 * t246 * t128 - t106 * (-t238 * t110 / 0.18e2 - t241 * t125 + 0.4e1 * t80 * t256 * params.a * t202 * t204 * s0 - t272)))
  v2rhosigma_0_ = 0.2e1 * r0 * t297 + 0.2e1 * t252
  t311 = 0.1e1 / t82
  t314 = t56 * t171 * t311 / 0.4e1
  t317 = t56 * params.expo * t311 / 0.2e1
  t322 = t246 ** 2
  t345 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t76 * ((t157 / t159 * t38 * s0 / 0.576e3 - t77 * t45 * t79 * t29 * t221 * t38 / 0.144e3 - t314 + t317) * t70 - 0.2e1 * t275 * t246 + 0.2e1 * t186 * t322 - t106 * (-t47 / t48 / s0 * t66 / 0.48e2 + t113 * t231 * t30 * t243 / 0.8e1 - 0.3e1 / 0.2e1 * t80 * t29 * t221 * params.a * t205 + t314 - t317)))
  v2sigma2_0_ = 0.2e1 * r0 * t345
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
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t36 = t32 * t35
  t39 = jnp.exp(-params.alpha * t23 * t28 * t36 / 0.24e2)
  t43 = (params.d * t39 + params.c) * t23 * t28
  t46 = t23 ** 2
  t47 = 0.1e1 / t26
  t48 = t46 * t47
  t49 = jnp.sqrt(s0)
  t52 = 0.1e1 / t18 / r0
  t53 = t49 * t30 * t52
  t56 = (t48 * t53 / 0.12e2) ** params.expo
  t57 = params.f * t56
  t58 = t43 * t36 / 0.24e2 - t57
  t59 = t48 * t49
  t65 = jnp.asinh(params.b * t46 * t47 * t53 / 0.12e2)
  t66 = params.a * t65
  t70 = 0.1e1 + t59 * t30 * t52 * t66 / 0.12e2 + t57
  t71 = 0.1e1 / t70
  t73 = t58 * t71 + 0.1e1
  t78 = t17 / t19
  t82 = t46 / t26 / t25
  t83 = params.d * params.alpha * t82
  t84 = s0 ** 2
  t85 = t84 * t30
  t86 = t33 ** 2
  t94 = t33 * r0
  t96 = 0.1e1 / t19 / t94
  t103 = 0.4e1 / 0.3e1 * t57 * params.expo / r0
  t104 = t83 * t85 / t18 / t86 / t33 * t39 / 0.108e3 - t43 * t32 * t96 / 0.9e1 + t103
  t106 = t70 ** 2
  t107 = 0.1e1 / t106
  t108 = t58 * t107
  t116 = t23 * t28 * t32
  t118 = params.b ** 2
  t123 = 0.6e1 * t118 * t23 * t28 * t36 + 0.144e3
  t124 = jnp.sqrt(t123)
  t126 = params.b / t124
  t130 = -t59 * t30 / t18 / t33 * t66 / 0.9e1 - 0.2e1 / 0.3e1 * t116 * t96 * params.a * t126 - t103
  t132 = t104 * t71 - t108 * t130
  t136 = t17 * t18
  t139 = 0.1e1 / t18 / t86 / t94
  t144 = params.alpha ** 2
  t146 = t25 ** 2
  t147 = 0.1e1 / t146
  t148 = params.d * t144 * t147
  t149 = t84 * s0
  t150 = t86 ** 2
  t158 = 0.1e1 / t19 / t86
  t162 = params.expo ** 2
  t163 = 0.1e1 / t33
  t166 = 0.16e2 / 0.9e1 * t57 * t162 * t163
  t169 = 0.4e1 / 0.3e1 * t57 * params.expo * t163
  t170 = -t83 * t85 * t139 * t39 / 0.12e2 + t148 * t149 / t150 / t33 * t39 / 0.81e2 + 0.11e2 / 0.27e2 * t43 * t32 * t158 - t166 - t169
  t172 = t104 * t107
  t176 = 0.1e1 / t106 / t70
  t177 = t58 * t176
  t178 = t130 ** 2
  t191 = t82 * t85
  t196 = t118 * params.b / t124 / t123
  t200 = 0.7e1 / 0.27e2 * t59 * t30 / t18 / t94 * t66 + 0.10e2 / 0.3e1 * t116 * t158 * params.a * t126 - 0.32e2 / 0.3e1 * t191 * t139 * params.a * t196 + t166 + t169
  t202 = -t108 * t200 - 0.2e1 * t172 * t130 + t170 * t71 + 0.2e1 * t177 * t178
  t207 = f.my_piecewise3(t2, 0, t6 * t22 * t73 / 0.12e2 - t6 * t78 * t132 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t136 * t202)
  t220 = 0.1e1 / t18 / t150
  t226 = 0.1e1 / t150 / t94
  t233 = t84 ** 2
  t236 = t86 * r0
  t247 = 0.1e1 / t19 / t236
  t252 = 0.1e1 / t94
  t255 = 0.64e2 / 0.27e2 * t57 * t162 * params.expo * t252
  t258 = 0.16e2 / 0.3e1 * t57 * t162 * t252
  t261 = 0.8e1 / 0.3e1 * t57 * params.expo * t252
  t272 = t106 ** 2
  t297 = t118 ** 2
  t300 = t123 ** 2
  t313 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t73 + t6 * t22 * t132 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t78 * t202 - 0.3e1 / 0.8e1 * t6 * t136 * ((0.341e3 / 0.486e3 * t83 * t85 * t220 * t39 - 0.19e2 / 0.81e2 * t148 * t149 * t226 * t39 + params.d * t144 * params.alpha * t147 * t233 / t19 / t150 / t236 * t23 * t28 * t31 * t39 / 0.729e3 - 0.154e3 / 0.81e2 * t43 * t32 * t247 + t255 + t258 + t261) * t71 - 0.3e1 * t170 * t107 * t130 + 0.6e1 * t104 * t176 * t178 - 0.3e1 * t172 * t200 - 0.6e1 * t58 / t272 * t178 * t130 + 0.6e1 * t177 * t130 * t200 - t108 * (-0.70e2 / 0.81e2 * t59 * t30 / t18 / t86 * t66 - 0.476e3 / 0.27e2 * t116 * t247 * params.a * t126 + 0.1184e4 / 0.9e1 * t191 * t220 * params.a * t196 - 0.3072e4 * t147 * t149 * t226 * params.a * t297 * params.b / t124 / t300 - t255 - t258 - t261)))
  v3rho3_0_ = 0.2e1 * r0 * t313 + 0.6e1 * t207

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
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = t33 * t22
  t37 = jnp.exp(-params.alpha * t24 * t29 * t34 / 0.24e2)
  t41 = (params.d * t37 + params.c) * t24 * t29
  t44 = t24 ** 2
  t45 = 0.1e1 / t27
  t46 = t44 * t45
  t47 = jnp.sqrt(s0)
  t50 = 0.1e1 / t19 / r0
  t51 = t47 * t31 * t50
  t54 = (t46 * t51 / 0.12e2) ** params.expo
  t55 = params.f * t54
  t56 = t41 * t34 / 0.24e2 - t55
  t57 = t46 * t47
  t63 = jnp.asinh(params.b * t44 * t45 * t51 / 0.12e2)
  t64 = params.a * t63
  t68 = 0.1e1 + t57 * t31 * t50 * t64 / 0.12e2 + t55
  t69 = 0.1e1 / t68
  t71 = t56 * t69 + 0.1e1
  t77 = t17 / t20 / r0
  t80 = 0.1e1 / t27 / t26
  t81 = t44 * t80
  t82 = params.d * params.alpha * t81
  t83 = s0 ** 2
  t84 = t83 * t31
  t85 = t18 ** 2
  t86 = t85 * t18
  t93 = t18 * r0
  t95 = 0.1e1 / t20 / t93
  t102 = 0.4e1 / 0.3e1 * t55 * params.expo / r0
  t103 = t82 * t84 / t19 / t86 * t37 / 0.108e3 - t41 * t33 * t95 / 0.9e1 + t102
  t105 = t68 ** 2
  t106 = 0.1e1 / t105
  t107 = t56 * t106
  t114 = t24 * t29
  t115 = t114 * t33
  t117 = params.b ** 2
  t122 = 0.6e1 * t117 * t24 * t29 * t34 + 0.144e3
  t123 = jnp.sqrt(t122)
  t125 = params.b / t123
  t129 = -t57 * t31 / t19 / t18 * t64 / 0.9e1 - 0.2e1 / 0.3e1 * t115 * t95 * params.a * t125 - t102
  t131 = t103 * t69 - t107 * t129
  t136 = t17 / t20
  t139 = 0.1e1 / t19 / t85 / t93
  t144 = params.alpha ** 2
  t146 = t26 ** 2
  t147 = 0.1e1 / t146
  t148 = params.d * t144 * t147
  t149 = t83 * s0
  t150 = t85 ** 2
  t158 = 0.1e1 / t20 / t85
  t162 = params.expo ** 2
  t163 = 0.1e1 / t18
  t166 = 0.16e2 / 0.9e1 * t55 * t162 * t163
  t169 = 0.4e1 / 0.3e1 * t55 * params.expo * t163
  t170 = -t82 * t84 * t139 * t37 / 0.12e2 + t148 * t149 / t150 / t18 * t37 / 0.81e2 + 0.11e2 / 0.27e2 * t41 * t33 * t158 - t166 - t169
  t172 = t103 * t106
  t176 = 0.1e1 / t105 / t68
  t177 = t56 * t176
  t178 = t129 ** 2
  t191 = t81 * t84
  t193 = t117 * params.b
  t196 = t193 / t123 / t122
  t200 = 0.7e1 / 0.27e2 * t57 * t31 / t19 / t93 * t64 + 0.10e2 / 0.3e1 * t115 * t158 * params.a * t125 - 0.32e2 / 0.3e1 * t191 * t139 * params.a * t196 + t166 + t169
  t202 = -t107 * t200 - 0.2e1 * t172 * t129 + t170 * t69 + 0.2e1 * t177 * t178
  t206 = t17 * t19
  t208 = 0.1e1 / t19 / t150
  t214 = 0.1e1 / t150 / t93
  t221 = t83 ** 2
  t222 = t147 * t221
  t223 = params.d * t144 * params.alpha * t222
  t224 = t85 * r0
  t230 = t29 * t32 * t37
  t235 = 0.1e1 / t20 / t224
  t239 = t162 * params.expo
  t240 = 0.1e1 / t93
  t243 = 0.64e2 / 0.27e2 * t55 * t239 * t240
  t246 = 0.16e2 / 0.3e1 * t55 * t162 * t240
  t249 = 0.8e1 / 0.3e1 * t55 * params.expo * t240
  t250 = 0.341e3 / 0.486e3 * t82 * t84 * t208 * t37 - 0.19e2 / 0.81e2 * t148 * t149 * t214 * t37 + t223 / t20 / t150 / t224 * t24 * t230 / 0.729e3 - 0.154e3 / 0.81e2 * t41 * t33 * t235 + t243 + t246 + t249
  t252 = t170 * t106
  t255 = t103 * t176
  t260 = t105 ** 2
  t261 = 0.1e1 / t260
  t262 = t56 * t261
  t263 = t178 * t129
  t266 = t129 * t200
  t283 = t147 * t149
  t285 = t117 ** 2
  t288 = t122 ** 2
  t291 = params.a * t285 * params.b / t123 / t288
  t294 = -0.70e2 / 0.81e2 * t57 * t31 / t19 / t85 * t64 - 0.476e3 / 0.27e2 * t115 * t235 * params.a * t125 + 0.1184e4 / 0.9e1 * t191 * t208 * params.a * t196 - 0.3072e4 * t283 * t214 * t291 - t243 - t246 - t249
  t296 = -t107 * t294 - 0.3e1 * t252 * t129 - 0.3e1 * t172 * t200 + 0.6e1 * t177 * t266 + 0.6e1 * t255 * t178 + t250 * t69 - 0.6e1 * t262 * t263
  t301 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t71 + t6 * t77 * t131 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t136 * t202 - 0.3e1 / 0.8e1 * t6 * t206 * t296)
  t318 = 0.1e1 / t19 / t150 / r0
  t324 = 0.1e1 / t150 / t85
  t331 = 0.1e1 / t20 / t150 / t86
  t336 = t144 ** 2
  t341 = t150 ** 2
  t352 = 0.1e1 / t20 / t86
  t356 = t162 ** 2
  t357 = 0.1e1 / t85
  t360 = 0.256e3 / 0.81e2 * t55 * t356 * t357
  t363 = 0.128e3 / 0.9e1 * t55 * t239 * t357
  t366 = 0.176e3 / 0.9e1 * t55 * t162 * t357
  t369 = 0.8e1 * t55 * params.expo * t357
  t390 = t178 ** 2
  t396 = t200 ** 2
  t432 = (-0.3047e4 / 0.486e3 * t82 * t84 * t318 * t37 + 0.2563e4 / 0.729e3 * t148 * t149 * t324 * t37 - 0.98e2 / 0.2187e4 * t223 * t331 * t24 * t230 + 0.2e1 / 0.6561e4 * params.d * t336 * t147 * t221 * s0 / t19 / t341 / r0 * t44 * t80 * t31 * t37 + 0.2618e4 / 0.243e3 * t41 * t33 * t352 - t360 - t363 - t366 - t369) * t69 - 0.4e1 * t250 * t106 * t129 + 0.12e2 * t170 * t176 * t178 - 0.6e1 * t252 * t200 - 0.24e2 * t103 * t261 * t263 + 0.24e2 * t255 * t266 - 0.4e1 * t172 * t294 + 0.24e2 * t56 / t260 / t68 * t390 - 0.36e2 * t262 * t178 * t200 + 0.6e1 * t177 * t396 + 0.8e1 * t177 * t129 * t294 - t107 * (0.910e3 / 0.243e3 * t57 * t31 / t19 / t224 * t64 + 0.2884e4 / 0.27e2 * t115 * t352 * params.a * t125 - 0.37216e5 / 0.27e2 * t191 * t318 * params.a * t196 + 0.71680e5 * t283 * t324 * t291 - 0.122880e6 * t222 * t331 * params.a * t285 * t193 / t123 / t288 / t122 * t114 * t32 + t360 + t363 + t366 + t369)
  t437 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t95 * t71 - 0.5e1 / 0.9e1 * t6 * t23 * t131 + t6 * t77 * t202 / 0.2e1 - t6 * t136 * t296 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t206 * t432)
  v4rho4_0_ = 0.2e1 * r0 * t437 + 0.8e1 * t301

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
  t33 = params.alpha * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t44 = t38 / t41 / t39
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
  t76 = 0.1e1 + t65 * t58 * params.a * t72 / 0.12e2 + t63
  t77 = 0.1e1 / t76
  t79 = t64 * t77 + 0.1e1
  t83 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t84 = t83 * f.p.zeta_threshold
  t86 = f.my_piecewise3(t20, t84, t21 * t19)
  t87 = t30 ** 2
  t88 = 0.1e1 / t87
  t89 = t86 * t88
  t92 = t5 * t89 * t79 / 0.8e1
  t93 = t86 * t30
  t95 = params.d * params.alpha * t53
  t97 = 0.1e1 / t35 / t34
  t98 = s0 ** 2
  t99 = t97 * t98
  t100 = t39 ** 2
  t108 = t39 * r0
  t110 = 0.1e1 / t41 / t108
  t117 = 0.4e1 / 0.3e1 * t63 * params.expo / r0
  t118 = t95 * t99 / t40 / t100 / t39 * t47 / 0.216e3 - t50 * t38 * t110 / 0.9e1 + t117
  t120 = t76 ** 2
  t121 = 0.1e1 / t120
  t122 = t64 * t121
  t129 = t32 * t37
  t130 = t129 * s0
  t132 = params.b ** 2
  t133 = t132 * t32
  t136 = 0.6e1 * t133 * t44 + 0.144e3
  t137 = jnp.sqrt(t136)
  t139 = params.b / t137
  t143 = -t65 / t40 / t39 * params.a * t72 / 0.9e1 - 0.2e1 / 0.3e1 * t130 * t110 * params.a * t139 - t117
  t145 = t118 * t77 - t122 * t143
  t150 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t79 - t92 - 0.3e1 / 0.8e1 * t5 * t93 * t145)
  t152 = r1 <= f.p.dens_threshold
  t153 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t154 = 0.1e1 + t153
  t155 = t154 <= f.p.zeta_threshold
  t156 = t154 ** (0.1e1 / 0.3e1)
  t158 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t161 = f.my_piecewise3(t155, 0, 0.4e1 / 0.3e1 * t156 * t158)
  t162 = t161 * t30
  t163 = t37 * s2
  t164 = r1 ** 2
  t165 = r1 ** (0.1e1 / 0.3e1)
  t166 = t165 ** 2
  t169 = t163 / t166 / t164
  t172 = jnp.exp(-t33 * t169 / 0.24e2)
  t175 = (params.d * t172 + params.c) * t32
  t178 = jnp.sqrt(s2)
  t180 = 0.1e1 / t165 / r1
  t184 = (t55 * t178 * t180 / 0.12e2) ** params.expo
  t185 = params.f * t184
  t186 = t175 * t169 / 0.24e2 - t185
  t187 = t55 * t178
  t193 = jnp.arcsinh(t67 * t54 * t178 * t180 / 0.12e2)
  t197 = 0.1e1 + t187 * t180 * params.a * t193 / 0.12e2 + t185
  t198 = 0.1e1 / t197
  t200 = t186 * t198 + 0.1e1
  t205 = f.my_piecewise3(t155, t84, t156 * t154)
  t206 = t205 * t88
  t209 = t5 * t206 * t200 / 0.8e1
  t211 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t5 * t162 * t200 - t209)
  t213 = t21 ** 2
  t214 = 0.1e1 / t213
  t215 = t26 ** 2
  t220 = t16 / t22 / t6
  t222 = -0.2e1 * t23 + 0.2e1 * t220
  t223 = f.my_piecewise5(t10, 0, t14, 0, t222)
  t227 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t214 * t215 + 0.4e1 / 0.3e1 * t21 * t223)
  t234 = t5 * t29 * t88 * t79
  t240 = 0.1e1 / t87 / t6
  t244 = t5 * t86 * t240 * t79 / 0.12e2
  t246 = t5 * t89 * t145
  t250 = 0.1e1 / t40 / t100 / t108
  t255 = params.alpha ** 2
  t257 = t34 ** 2
  t259 = params.d * t255 / t257
  t261 = t100 ** 2
  t269 = 0.1e1 / t41 / t100
  t273 = params.expo ** 2
  t274 = 0.1e1 / t39
  t277 = 0.16e2 / 0.9e1 * t63 * t273 * t274
  t280 = 0.4e1 / 0.3e1 * t63 * params.expo * t274
  t289 = t143 ** 2
  t302 = t53 * t97
  t305 = t132 * params.b
  t319 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t227 * t30 * t79 - t234 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t145 + t244 - t246 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t93 * ((-t95 * t99 * t250 * t47 / 0.24e2 + t259 * t98 * s0 / t261 / t39 * t47 / 0.324e3 + 0.11e2 / 0.27e2 * t50 * t38 * t269 - t277 - t280) * t77 - 0.2e1 * t118 * t121 * t143 + 0.2e1 * t64 / t120 / t76 * t289 - t122 * (0.7e1 / 0.27e2 * t65 / t40 / t108 * params.a * t72 + 0.10e2 / 0.3e1 * t130 * t269 * params.a * t139 - 0.16e2 / 0.3e1 * t302 * t98 * t250 * params.a * t305 / t137 / t136 + t277 + t280)))
  t320 = t156 ** 2
  t321 = 0.1e1 / t320
  t322 = t158 ** 2
  t326 = f.my_piecewise5(t14, 0, t10, 0, -t222)
  t330 = f.my_piecewise3(t155, 0, 0.4e1 / 0.9e1 * t321 * t322 + 0.4e1 / 0.3e1 * t156 * t326)
  t337 = t5 * t161 * t88 * t200
  t342 = t5 * t205 * t240 * t200 / 0.12e2
  t344 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t5 * t330 * t30 * t200 - t337 / 0.4e1 + t342)
  d11 = 0.2e1 * t150 + 0.2e1 * t211 + t6 * (t319 + t344)
  t347 = -t7 - t24
  t348 = f.my_piecewise5(t10, 0, t14, 0, t347)
  t351 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t348)
  t352 = t351 * t30
  t357 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t352 * t79 - t92)
  t359 = f.my_piecewise5(t14, 0, t10, 0, -t347)
  t362 = f.my_piecewise3(t155, 0, 0.4e1 / 0.3e1 * t156 * t359)
  t363 = t362 * t30
  t367 = t205 * t30
  t368 = s2 ** 2
  t369 = t97 * t368
  t370 = t164 ** 2
  t378 = t164 * r1
  t380 = 0.1e1 / t166 / t378
  t387 = 0.4e1 / 0.3e1 * t185 * params.expo / r1
  t388 = t95 * t369 / t165 / t370 / t164 * t172 / 0.216e3 - t175 * t163 * t380 / 0.9e1 + t387
  t390 = t197 ** 2
  t391 = 0.1e1 / t390
  t392 = t186 * t391
  t399 = t129 * s2
  t403 = 0.6e1 * t133 * t169 + 0.144e3
  t404 = jnp.sqrt(t403)
  t406 = params.b / t404
  t410 = -t187 / t165 / t164 * params.a * t193 / 0.9e1 - 0.2e1 / 0.3e1 * t399 * t380 * params.a * t406 - t387
  t412 = t388 * t198 - t392 * t410
  t417 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t5 * t363 * t200 - t209 - 0.3e1 / 0.8e1 * t5 * t367 * t412)
  t421 = 0.2e1 * t220
  t422 = f.my_piecewise5(t10, 0, t14, 0, t421)
  t426 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t214 * t348 * t26 + 0.4e1 / 0.3e1 * t21 * t422)
  t433 = t5 * t351 * t88 * t79
  t441 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t426 * t30 * t79 - t433 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t352 * t145 - t234 / 0.8e1 + t244 - t246 / 0.8e1)
  t445 = f.my_piecewise5(t14, 0, t10, 0, -t421)
  t449 = f.my_piecewise3(t155, 0, 0.4e1 / 0.9e1 * t321 * t359 * t158 + 0.4e1 / 0.3e1 * t156 * t445)
  t456 = t5 * t362 * t88 * t200
  t463 = t5 * t206 * t412
  t466 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t5 * t449 * t30 * t200 - t456 / 0.8e1 - t337 / 0.8e1 + t342 - 0.3e1 / 0.8e1 * t5 * t162 * t412 - t463 / 0.8e1)
  d12 = t150 + t211 + t357 + t417 + t6 * (t441 + t466)
  t471 = t348 ** 2
  t475 = 0.2e1 * t23 + 0.2e1 * t220
  t476 = f.my_piecewise5(t10, 0, t14, 0, t475)
  t480 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t214 * t471 + 0.4e1 / 0.3e1 * t21 * t476)
  t487 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t480 * t30 * t79 - t433 / 0.4e1 + t244)
  t488 = t359 ** 2
  t492 = f.my_piecewise5(t14, 0, t10, 0, -t475)
  t496 = f.my_piecewise3(t155, 0, 0.4e1 / 0.9e1 * t321 * t488 + 0.4e1 / 0.3e1 * t156 * t492)
  t508 = 0.1e1 / t165 / t370 / t378
  t514 = t370 ** 2
  t522 = 0.1e1 / t166 / t370
  t526 = 0.1e1 / t164
  t529 = 0.16e2 / 0.9e1 * t185 * t273 * t526
  t532 = 0.4e1 / 0.3e1 * t185 * params.expo * t526
  t541 = t410 ** 2
  t569 = f.my_piecewise3(t152, 0, -0.3e1 / 0.8e1 * t5 * t496 * t30 * t200 - t456 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t363 * t412 + t342 - t463 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t367 * ((-t95 * t369 * t508 * t172 / 0.24e2 + t259 * t368 * s2 / t514 / t164 * t172 / 0.324e3 + 0.11e2 / 0.27e2 * t175 * t163 * t522 - t529 - t532) * t198 - 0.2e1 * t388 * t391 * t410 + 0.2e1 * t186 / t390 / t197 * t541 - t392 * (0.7e1 / 0.27e2 * t187 / t165 / t378 * params.a * t193 + 0.10e2 / 0.3e1 * t399 * t522 * params.a * t406 - 0.16e2 / 0.3e1 * t302 * t368 * t508 * params.a * t305 / t404 / t403 + t529 + t532)))
  d22 = 0.2e1 * t357 + 0.2e1 * t417 + t6 * (t487 + t569)
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
  t45 = params.alpha * t44
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t50 = t49 * s0
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t56 = t50 / t53 / t51
  t59 = jnp.exp(-t45 * t56 / 0.24e2)
  t62 = (params.d * t59 + params.c) * t44
  t65 = t44 ** 2
  t66 = 0.1e1 / t47
  t67 = t65 * t66
  t68 = jnp.sqrt(s0)
  t70 = 0.1e1 / t52 / r0
  t74 = (t67 * t68 * t70 / 0.12e2) ** params.expo
  t75 = params.f * t74
  t76 = t62 * t56 / 0.24e2 - t75
  t77 = t67 * t68
  t79 = params.b * t65
  t84 = jnp.asinh(t79 * t66 * t68 * t70 / 0.12e2)
  t88 = 0.1e1 + t77 * t70 * params.a * t84 / 0.12e2 + t75
  t89 = 0.1e1 / t88
  t91 = t76 * t89 + 0.1e1
  t97 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t98 = t42 ** 2
  t99 = 0.1e1 / t98
  t100 = t97 * t99
  t104 = t97 * t42
  t106 = params.d * params.alpha * t65
  t108 = 0.1e1 / t47 / t46
  t109 = s0 ** 2
  t110 = t108 * t109
  t111 = t51 ** 2
  t119 = t51 * r0
  t121 = 0.1e1 / t53 / t119
  t128 = 0.4e1 / 0.3e1 * t75 * params.expo / r0
  t129 = t106 * t110 / t52 / t111 / t51 * t59 / 0.216e3 - t62 * t50 * t121 / 0.9e1 + t128
  t131 = t88 ** 2
  t132 = 0.1e1 / t131
  t133 = t76 * t132
  t141 = t44 * t49 * s0
  t143 = params.b ** 2
  t147 = 0.6e1 * t143 * t44 * t56 + 0.144e3
  t148 = jnp.sqrt(t147)
  t150 = params.b / t148
  t154 = -t77 / t52 / t51 * params.a * t84 / 0.9e1 - 0.2e1 / 0.3e1 * t141 * t121 * params.a * t150 - t128
  t156 = t129 * t89 - t133 * t154
  t160 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t161 = t160 * f.p.zeta_threshold
  t163 = f.my_piecewise3(t20, t161, t21 * t19)
  t165 = 0.1e1 / t98 / t6
  t166 = t163 * t165
  t170 = t163 * t99
  t174 = t163 * t42
  t177 = 0.1e1 / t52 / t111 / t119
  t182 = params.alpha ** 2
  t184 = t46 ** 2
  t185 = 0.1e1 / t184
  t186 = params.d * t182 * t185
  t187 = t109 * s0
  t188 = t111 ** 2
  t196 = 0.1e1 / t53 / t111
  t200 = params.expo ** 2
  t201 = 0.1e1 / t51
  t204 = 0.16e2 / 0.9e1 * t75 * t200 * t201
  t207 = 0.4e1 / 0.3e1 * t75 * params.expo * t201
  t208 = -t106 * t110 * t177 * t59 / 0.24e2 + t186 * t187 / t188 / t51 * t59 / 0.324e3 + 0.11e2 / 0.27e2 * t62 * t50 * t196 - t204 - t207
  t210 = t129 * t132
  t214 = 0.1e1 / t131 / t88
  t215 = t76 * t214
  t216 = t154 ** 2
  t230 = t65 * t108 * t109
  t235 = t143 * params.b / t148 / t147
  t239 = 0.7e1 / 0.27e2 * t77 / t52 / t119 * params.a * t84 + 0.10e2 / 0.3e1 * t141 * t196 * params.a * t150 - 0.16e2 / 0.3e1 * t230 * t177 * params.a * t235 + t204 + t207
  t241 = -t133 * t239 - 0.2e1 * t210 * t154 + t208 * t89 + 0.2e1 * t215 * t216
  t246 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t91 - t5 * t100 * t91 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t104 * t156 + t5 * t166 * t91 / 0.12e2 - t5 * t170 * t156 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t174 * t241)
  t248 = r1 <= f.p.dens_threshold
  t249 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t250 = 0.1e1 + t249
  t251 = t250 <= f.p.zeta_threshold
  t252 = t250 ** (0.1e1 / 0.3e1)
  t253 = t252 ** 2
  t254 = 0.1e1 / t253
  t256 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t257 = t256 ** 2
  t261 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t265 = f.my_piecewise3(t251, 0, 0.4e1 / 0.9e1 * t254 * t257 + 0.4e1 / 0.3e1 * t252 * t261)
  t268 = r1 ** 2
  t269 = r1 ** (0.1e1 / 0.3e1)
  t270 = t269 ** 2
  t273 = t49 * s2 / t270 / t268
  t276 = jnp.exp(-t45 * t273 / 0.24e2)
  t282 = jnp.sqrt(s2)
  t284 = 0.1e1 / t269 / r1
  t288 = (t67 * t282 * t284 / 0.12e2) ** params.expo
  t289 = params.f * t288
  t297 = jnp.asinh(t79 * t66 * t282 * t284 / 0.12e2)
  t304 = 0.1e1 + ((params.d * t276 + params.c) * t44 * t273 / 0.24e2 - t289) / (0.1e1 + t67 * t282 * t284 * params.a * t297 / 0.12e2 + t289)
  t310 = f.my_piecewise3(t251, 0, 0.4e1 / 0.3e1 * t252 * t256)
  t316 = f.my_piecewise3(t251, t161, t252 * t250)
  t322 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t5 * t265 * t42 * t304 - t5 * t310 * t99 * t304 / 0.4e1 + t5 * t316 * t165 * t304 / 0.12e2)
  t332 = t24 ** 2
  t336 = 0.6e1 * t33 - 0.6e1 * t16 / t332
  t337 = f.my_piecewise5(t10, 0, t14, 0, t336)
  t341 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t337)
  t364 = 0.1e1 / t98 / t24
  t376 = 0.1e1 / t52 / t188
  t382 = 0.1e1 / t188 / t119
  t389 = t109 ** 2
  t392 = t111 * r0
  t402 = 0.1e1 / t53 / t392
  t407 = 0.1e1 / t119
  t410 = 0.64e2 / 0.27e2 * t75 * t200 * params.expo * t407
  t413 = 0.16e2 / 0.3e1 * t75 * t200 * t407
  t416 = 0.8e1 / 0.3e1 * t75 * params.expo * t407
  t427 = t131 ** 2
  t452 = t143 ** 2
  t455 = t147 ** 2
  t468 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t341 * t42 * t91 - 0.3e1 / 0.8e1 * t5 * t41 * t99 * t91 - 0.9e1 / 0.8e1 * t5 * t43 * t156 + t5 * t97 * t165 * t91 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t100 * t156 - 0.9e1 / 0.8e1 * t5 * t104 * t241 - 0.5e1 / 0.36e2 * t5 * t163 * t364 * t91 + t5 * t166 * t156 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t170 * t241 - 0.3e1 / 0.8e1 * t5 * t174 * ((0.341e3 / 0.972e3 * t106 * t110 * t376 * t59 - 0.19e2 / 0.324e3 * t186 * t187 * t382 * t59 + params.d * t182 * params.alpha * t185 * t389 / t53 / t188 / t392 * t44 * t49 * t59 / 0.2916e4 - 0.154e3 / 0.81e2 * t62 * t50 * t402 + t410 + t413 + t416) * t89 - 0.3e1 * t208 * t132 * t154 + 0.6e1 * t129 * t214 * t216 - 0.3e1 * t210 * t239 - 0.6e1 * t76 / t427 * t216 * t154 + 0.6e1 * t215 * t154 * t239 - t133 * (-0.70e2 / 0.81e2 * t77 / t52 / t111 * params.a * t84 - 0.476e3 / 0.27e2 * t141 * t402 * params.a * t150 + 0.592e3 / 0.9e1 * t230 * t376 * params.a * t235 - 0.768e3 * t185 * t187 * t382 * params.a * t452 * params.b / t148 / t455 - t410 - t413 - t416)))
  t478 = f.my_piecewise5(t14, 0, t10, 0, -t336)
  t482 = f.my_piecewise3(t251, 0, -0.8e1 / 0.27e2 / t253 / t250 * t257 * t256 + 0.4e1 / 0.3e1 * t254 * t256 * t261 + 0.4e1 / 0.3e1 * t252 * t478)
  t500 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t5 * t482 * t42 * t304 - 0.3e1 / 0.8e1 * t5 * t265 * t99 * t304 + t5 * t310 * t165 * t304 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t316 * t364 * t304)
  d111 = 0.3e1 * t246 + 0.3e1 * t322 + t6 * (t468 + t500)

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
  t57 = params.alpha * t56
  t58 = jnp.pi ** 2
  t59 = t58 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t62 = t61 * s0
  t63 = r0 ** 2
  t64 = r0 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t68 = t62 / t65 / t63
  t71 = jnp.exp(-t57 * t68 / 0.24e2)
  t74 = (params.d * t71 + params.c) * t56
  t77 = t56 ** 2
  t78 = 0.1e1 / t59
  t79 = t77 * t78
  t80 = jnp.sqrt(s0)
  t82 = 0.1e1 / t64 / r0
  t86 = (t79 * t80 * t82 / 0.12e2) ** params.expo
  t87 = params.f * t86
  t88 = t74 * t68 / 0.24e2 - t87
  t89 = t79 * t80
  t91 = params.b * t77
  t96 = jnp.asinh(t91 * t78 * t80 * t82 / 0.12e2)
  t100 = 0.1e1 + t89 * t82 * params.a * t96 / 0.12e2 + t87
  t101 = 0.1e1 / t100
  t103 = t88 * t101 + 0.1e1
  t112 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t113 = t54 ** 2
  t114 = 0.1e1 / t113
  t115 = t112 * t114
  t119 = t112 * t54
  t121 = params.d * params.alpha * t77
  t123 = 0.1e1 / t59 / t58
  t124 = s0 ** 2
  t125 = t123 * t124
  t126 = t63 ** 2
  t127 = t126 * t63
  t134 = t63 * r0
  t136 = 0.1e1 / t65 / t134
  t143 = 0.4e1 / 0.3e1 * t87 * params.expo / r0
  t144 = t121 * t125 / t64 / t127 * t71 / 0.216e3 - t74 * t62 * t136 / 0.9e1 + t143
  t146 = t100 ** 2
  t147 = 0.1e1 / t146
  t148 = t88 * t147
  t155 = t56 * t61
  t156 = t155 * s0
  t158 = params.b ** 2
  t162 = 0.6e1 * t158 * t56 * t68 + 0.144e3
  t163 = jnp.sqrt(t162)
  t165 = params.b / t163
  t169 = -t89 / t64 / t63 * params.a * t96 / 0.9e1 - 0.2e1 / 0.3e1 * t156 * t136 * params.a * t165 - t143
  t171 = t144 * t101 - t148 * t169
  t177 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t179 = 0.1e1 / t113 / t6
  t180 = t177 * t179
  t184 = t177 * t114
  t188 = t177 * t54
  t191 = 0.1e1 / t64 / t126 / t134
  t196 = params.alpha ** 2
  t198 = t58 ** 2
  t199 = 0.1e1 / t198
  t200 = params.d * t196 * t199
  t201 = t124 * s0
  t202 = t126 ** 2
  t210 = 0.1e1 / t65 / t126
  t214 = params.expo ** 2
  t215 = 0.1e1 / t63
  t218 = 0.16e2 / 0.9e1 * t87 * t214 * t215
  t221 = 0.4e1 / 0.3e1 * t87 * params.expo * t215
  t222 = -t121 * t125 * t191 * t71 / 0.24e2 + t200 * t201 / t202 / t63 * t71 / 0.324e3 + 0.11e2 / 0.27e2 * t74 * t62 * t210 - t218 - t221
  t224 = t144 * t147
  t228 = 0.1e1 / t146 / t100
  t229 = t88 * t228
  t230 = t169 ** 2
  t244 = t77 * t123 * t124
  t246 = t158 * params.b
  t249 = t246 / t163 / t162
  t253 = 0.7e1 / 0.27e2 * t89 / t64 / t134 * params.a * t96 + 0.10e2 / 0.3e1 * t156 * t210 * params.a * t165 - 0.16e2 / 0.3e1 * t244 * t191 * params.a * t249 + t218 + t221
  t255 = t222 * t101 - t148 * t253 - 0.2e1 * t224 * t169 + 0.2e1 * t229 * t230
  t259 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t260 = t259 * f.p.zeta_threshold
  t262 = f.my_piecewise3(t20, t260, t21 * t19)
  t264 = 0.1e1 / t113 / t25
  t265 = t262 * t264
  t269 = t262 * t179
  t273 = t262 * t114
  t277 = t262 * t54
  t279 = 0.1e1 / t64 / t202
  t285 = 0.1e1 / t202 / t134
  t292 = t124 ** 2
  t293 = t199 * t292
  t294 = params.d * t196 * params.alpha * t293
  t295 = t126 * r0
  t300 = t61 * t71
  t305 = 0.1e1 / t65 / t295
  t309 = t214 * params.expo
  t310 = 0.1e1 / t134
  t313 = 0.64e2 / 0.27e2 * t87 * t309 * t310
  t316 = 0.16e2 / 0.3e1 * t87 * t214 * t310
  t319 = 0.8e1 / 0.3e1 * t87 * params.expo * t310
  t320 = 0.341e3 / 0.972e3 * t121 * t125 * t279 * t71 - 0.19e2 / 0.324e3 * t200 * t201 * t285 * t71 + t294 / t65 / t202 / t295 * t56 * t300 / 0.2916e4 - 0.154e3 / 0.81e2 * t74 * t62 * t305 + t313 + t316 + t319
  t322 = t222 * t147
  t325 = t144 * t228
  t330 = t146 ** 2
  t331 = 0.1e1 / t330
  t332 = t88 * t331
  t333 = t230 * t169
  t336 = t169 * t253
  t353 = t199 * t201
  t355 = t158 ** 2
  t358 = t162 ** 2
  t361 = params.a * t355 * params.b / t163 / t358
  t364 = -0.70e2 / 0.81e2 * t89 / t64 / t126 * params.a * t96 - 0.476e3 / 0.27e2 * t156 * t305 * params.a * t165 + 0.592e3 / 0.9e1 * t244 * t279 * params.a * t249 - 0.768e3 * t353 * t285 * t361 - t313 - t316 - t319
  t366 = t320 * t101 - t148 * t364 - 0.3e1 * t322 * t169 - 0.3e1 * t224 * t253 + 0.6e1 * t229 * t336 + 0.6e1 * t325 * t230 - 0.6e1 * t332 * t333
  t371 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t103 - 0.3e1 / 0.8e1 * t5 * t115 * t103 - 0.9e1 / 0.8e1 * t5 * t119 * t171 + t5 * t180 * t103 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t184 * t171 - 0.9e1 / 0.8e1 * t5 * t188 * t255 - 0.5e1 / 0.36e2 * t5 * t265 * t103 + t5 * t269 * t171 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t273 * t255 - 0.3e1 / 0.8e1 * t5 * t277 * t366)
  t373 = r1 <= f.p.dens_threshold
  t374 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t375 = 0.1e1 + t374
  t376 = t375 <= f.p.zeta_threshold
  t377 = t375 ** (0.1e1 / 0.3e1)
  t378 = t377 ** 2
  t380 = 0.1e1 / t378 / t375
  t382 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t383 = t382 ** 2
  t387 = 0.1e1 / t378
  t388 = t387 * t382
  t390 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t394 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t398 = f.my_piecewise3(t376, 0, -0.8e1 / 0.27e2 * t380 * t383 * t382 + 0.4e1 / 0.3e1 * t388 * t390 + 0.4e1 / 0.3e1 * t377 * t394)
  t401 = r1 ** 2
  t402 = r1 ** (0.1e1 / 0.3e1)
  t403 = t402 ** 2
  t406 = t61 * s2 / t403 / t401
  t409 = jnp.exp(-t57 * t406 / 0.24e2)
  t415 = jnp.sqrt(s2)
  t417 = 0.1e1 / t402 / r1
  t421 = (t79 * t415 * t417 / 0.12e2) ** params.expo
  t422 = params.f * t421
  t430 = jnp.asinh(t91 * t78 * t415 * t417 / 0.12e2)
  t437 = 0.1e1 + ((params.d * t409 + params.c) * t56 * t406 / 0.24e2 - t422) / (0.1e1 + t79 * t415 * t417 * params.a * t430 / 0.12e2 + t422)
  t446 = f.my_piecewise3(t376, 0, 0.4e1 / 0.9e1 * t387 * t383 + 0.4e1 / 0.3e1 * t377 * t390)
  t453 = f.my_piecewise3(t376, 0, 0.4e1 / 0.3e1 * t377 * t382)
  t459 = f.my_piecewise3(t376, t260, t377 * t375)
  t465 = f.my_piecewise3(t373, 0, -0.3e1 / 0.8e1 * t5 * t398 * t54 * t437 - 0.3e1 / 0.8e1 * t5 * t446 * t114 * t437 + t5 * t453 * t179 * t437 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t459 * t264 * t437)
  t480 = 0.1e1 / t113 / t36
  t510 = 0.1e1 / t64 / t202 / r0
  t516 = 0.1e1 / t202 / t126
  t523 = 0.1e1 / t65 / t202 / t127
  t528 = t196 ** 2
  t533 = t202 ** 2
  t543 = 0.1e1 / t65 / t127
  t547 = t214 ** 2
  t548 = 0.1e1 / t126
  t551 = 0.256e3 / 0.81e2 * t87 * t547 * t548
  t554 = 0.128e3 / 0.9e1 * t87 * t309 * t548
  t557 = 0.176e3 / 0.9e1 * t87 * t214 * t548
  t560 = 0.8e1 * t87 * params.expo * t548
  t581 = t230 ** 2
  t587 = t253 ** 2
  t622 = (-0.3047e4 / 0.972e3 * t121 * t125 * t510 * t71 + 0.2563e4 / 0.2916e4 * t200 * t201 * t516 * t71 - 0.49e2 / 0.4374e4 * t294 * t523 * t56 * t300 + params.d * t528 * t199 * t292 * s0 / t64 / t533 / r0 * t77 * t123 * t71 / 0.26244e5 + 0.2618e4 / 0.243e3 * t74 * t62 * t543 - t551 - t554 - t557 - t560) * t101 - 0.4e1 * t320 * t147 * t169 + 0.12e2 * t222 * t228 * t230 - 0.6e1 * t322 * t253 - 0.24e2 * t144 * t331 * t333 + 0.24e2 * t325 * t336 - 0.4e1 * t224 * t364 + 0.24e2 * t88 / t330 / t100 * t581 - 0.36e2 * t332 * t230 * t253 + 0.6e1 * t229 * t587 + 0.8e1 * t229 * t169 * t364 - t148 * (0.910e3 / 0.243e3 * t89 / t64 / t295 * params.a * t96 + 0.2884e4 / 0.27e2 * t156 * t543 * params.a * t165 - 0.18608e5 / 0.27e2 * t244 * t510 * params.a * t249 + 0.17920e5 * t353 * t516 * t361 - 0.30720e5 * t293 * t523 * params.a * t355 * t246 / t163 / t358 / t162 * t155 + t551 + t554 + t557 + t560)
  t626 = t19 ** 2
  t629 = t30 ** 2
  t635 = t41 ** 2
  t644 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t645 = f.my_piecewise5(t10, 0, t14, 0, t644)
  t649 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t626 * t629 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t635 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t645)
  t657 = -t5 * t53 * t114 * t103 / 0.2e1 + t5 * t112 * t179 * t103 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t177 * t264 * t103 + 0.10e2 / 0.27e2 * t5 * t262 * t480 * t103 - 0.3e1 / 0.2e1 * t5 * t115 * t171 - 0.9e1 / 0.4e1 * t5 * t119 * t255 + t5 * t180 * t171 - 0.3e1 / 0.2e1 * t5 * t184 * t255 - 0.3e1 / 0.2e1 * t5 * t188 * t366 - 0.5e1 / 0.9e1 * t5 * t265 * t171 + t5 * t269 * t255 / 0.2e1 - t5 * t273 * t366 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t277 * t622 - 0.3e1 / 0.8e1 * t5 * t649 * t54 * t103 - 0.3e1 / 0.2e1 * t5 * t55 * t171
  t658 = f.my_piecewise3(t1, 0, t657)
  t659 = t375 ** 2
  t662 = t383 ** 2
  t668 = t390 ** 2
  t674 = f.my_piecewise5(t14, 0, t10, 0, -t644)
  t678 = f.my_piecewise3(t376, 0, 0.40e2 / 0.81e2 / t378 / t659 * t662 - 0.16e2 / 0.9e1 * t380 * t383 * t390 + 0.4e1 / 0.3e1 * t387 * t668 + 0.16e2 / 0.9e1 * t388 * t394 + 0.4e1 / 0.3e1 * t377 * t674)
  t700 = f.my_piecewise3(t373, 0, -0.3e1 / 0.8e1 * t5 * t678 * t54 * t437 - t5 * t398 * t114 * t437 / 0.2e1 + t5 * t446 * t179 * t437 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t453 * t264 * t437 + 0.10e2 / 0.27e2 * t5 * t459 * t480 * t437)
  d1111 = 0.4e1 * t371 + 0.4e1 * t465 + t6 * (t658 + t700)

  res = {'v4rho4': d1111}
  return res
