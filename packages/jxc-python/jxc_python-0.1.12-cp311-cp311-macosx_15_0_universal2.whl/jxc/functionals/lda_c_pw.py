"""Generated from lda_c_pw.mpl."""

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
  params_alpha1_raw = params.alpha1
  if isinstance(params_alpha1_raw, (str, bytes, dict)):
    params_alpha1 = params_alpha1_raw
  else:
    try:
      params_alpha1_seq = list(params_alpha1_raw)
    except TypeError:
      params_alpha1 = params_alpha1_raw
    else:
      params_alpha1_seq = np.asarray(params_alpha1_seq, dtype=np.float64)
      params_alpha1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha1_seq))
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))
  params_beta3_raw = params.beta3
  if isinstance(params_beta3_raw, (str, bytes, dict)):
    params_beta3 = params_beta3_raw
  else:
    try:
      params_beta3_seq = list(params_beta3_raw)
    except TypeError:
      params_beta3 = params_beta3_raw
    else:
      params_beta3_seq = np.asarray(params_beta3_seq, dtype=np.float64)
      params_beta3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta3_seq))
  params_beta4_raw = params.beta4
  if isinstance(params_beta4_raw, (str, bytes, dict)):
    params_beta4 = params_beta4_raw
  else:
    try:
      params_beta4_seq = list(params_beta4_raw)
    except TypeError:
      params_beta4 = params_beta4_raw
    else:
      params_beta4_seq = np.asarray(params_beta4_seq, dtype=np.float64)
      params_beta4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta4_seq))
  params_fz20_raw = params.fz20
  if isinstance(params_fz20_raw, (str, bytes, dict)):
    params_fz20 = params_fz20_raw
  else:
    try:
      params_fz20_seq = list(params_fz20_raw)
    except TypeError:
      params_fz20 = params_fz20_raw
    else:
      params_fz20_seq = np.asarray(params_fz20_seq, dtype=np.float64)
      params_fz20 = np.concatenate((np.array([np.nan], dtype=np.float64), params_fz20_seq))
  params_pp_raw = params.pp
  if isinstance(params_pp_raw, (str, bytes, dict)):
    params_pp = params_pp_raw
  else:
    try:
      params_pp_seq = list(params_pp_raw)
    except TypeError:
      params_pp = params_pp_raw
    else:
      params_pp_seq = np.asarray(params_pp_seq, dtype=np.float64)
      params_pp = np.concatenate((np.array([np.nan], dtype=np.float64), params_pp_seq))

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  functional_body = lambda rs, zeta: f_pw(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
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
  params_alpha1_raw = params.alpha1
  if isinstance(params_alpha1_raw, (str, bytes, dict)):
    params_alpha1 = params_alpha1_raw
  else:
    try:
      params_alpha1_seq = list(params_alpha1_raw)
    except TypeError:
      params_alpha1 = params_alpha1_raw
    else:
      params_alpha1_seq = np.asarray(params_alpha1_seq, dtype=np.float64)
      params_alpha1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha1_seq))
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))
  params_beta3_raw = params.beta3
  if isinstance(params_beta3_raw, (str, bytes, dict)):
    params_beta3 = params_beta3_raw
  else:
    try:
      params_beta3_seq = list(params_beta3_raw)
    except TypeError:
      params_beta3 = params_beta3_raw
    else:
      params_beta3_seq = np.asarray(params_beta3_seq, dtype=np.float64)
      params_beta3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta3_seq))
  params_beta4_raw = params.beta4
  if isinstance(params_beta4_raw, (str, bytes, dict)):
    params_beta4 = params_beta4_raw
  else:
    try:
      params_beta4_seq = list(params_beta4_raw)
    except TypeError:
      params_beta4 = params_beta4_raw
    else:
      params_beta4_seq = np.asarray(params_beta4_seq, dtype=np.float64)
      params_beta4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta4_seq))
  params_fz20_raw = params.fz20
  if isinstance(params_fz20_raw, (str, bytes, dict)):
    params_fz20 = params_fz20_raw
  else:
    try:
      params_fz20_seq = list(params_fz20_raw)
    except TypeError:
      params_fz20 = params_fz20_raw
    else:
      params_fz20_seq = np.asarray(params_fz20_seq, dtype=np.float64)
      params_fz20 = np.concatenate((np.array([np.nan], dtype=np.float64), params_fz20_seq))
  params_pp_raw = params.pp
  if isinstance(params_pp_raw, (str, bytes, dict)):
    params_pp = params_pp_raw
  else:
    try:
      params_pp_seq = list(params_pp_raw)
    except TypeError:
      params_pp = params_pp_raw
    else:
      params_pp_seq = np.asarray(params_pp_seq, dtype=np.float64)
      params_pp = np.concatenate((np.array([np.nan], dtype=np.float64), params_pp_seq))

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  functional_body = lambda rs, zeta: f_pw(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
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
  params_alpha1_raw = params.alpha1
  if isinstance(params_alpha1_raw, (str, bytes, dict)):
    params_alpha1 = params_alpha1_raw
  else:
    try:
      params_alpha1_seq = list(params_alpha1_raw)
    except TypeError:
      params_alpha1 = params_alpha1_raw
    else:
      params_alpha1_seq = np.asarray(params_alpha1_seq, dtype=np.float64)
      params_alpha1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha1_seq))
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))
  params_beta3_raw = params.beta3
  if isinstance(params_beta3_raw, (str, bytes, dict)):
    params_beta3 = params_beta3_raw
  else:
    try:
      params_beta3_seq = list(params_beta3_raw)
    except TypeError:
      params_beta3 = params_beta3_raw
    else:
      params_beta3_seq = np.asarray(params_beta3_seq, dtype=np.float64)
      params_beta3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta3_seq))
  params_beta4_raw = params.beta4
  if isinstance(params_beta4_raw, (str, bytes, dict)):
    params_beta4 = params_beta4_raw
  else:
    try:
      params_beta4_seq = list(params_beta4_raw)
    except TypeError:
      params_beta4 = params_beta4_raw
    else:
      params_beta4_seq = np.asarray(params_beta4_seq, dtype=np.float64)
      params_beta4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta4_seq))
  params_fz20_raw = params.fz20
  if isinstance(params_fz20_raw, (str, bytes, dict)):
    params_fz20 = params_fz20_raw
  else:
    try:
      params_fz20_seq = list(params_fz20_raw)
    except TypeError:
      params_fz20 = params_fz20_raw
    else:
      params_fz20_seq = np.asarray(params_fz20_seq, dtype=np.float64)
      params_fz20 = np.concatenate((np.array([np.nan], dtype=np.float64), params_fz20_seq))
  params_pp_raw = params.pp
  if isinstance(params_pp_raw, (str, bytes, dict)):
    params_pp = params_pp_raw
  else:
    try:
      params_pp_seq = list(params_pp_raw)
    except TypeError:
      params_pp = params_pp_raw
    else:
      params_pp_seq = np.asarray(params_pp_seq, dtype=np.float64)
      params_pp = np.concatenate((np.array([np.nan], dtype=np.float64), params_pp_seq))

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  functional_body = lambda rs, zeta: f_pw(rs, zeta)

  t1 = params.a[0]
  t2 = params.alpha1[0]
  t3 = 3 ** (0.1e1 / 0.3e1)
  t6 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t9 = t6 * t8
  t10 = r0 + r1
  t11 = t10 ** (0.1e1 / 0.3e1)
  t12 = 0.1e1 / t11
  t13 = t9 * t12
  t16 = 0.1e1 + t2 * t3 * t13 / 0.4e1
  t19 = params.beta1[0]
  t20 = t3 * t6
  t22 = t20 * t8 * t12
  t23 = jnp.sqrt(t22)
  t27 = params.beta2[0] * t3
  t30 = params.beta3[0]
  t31 = t22 ** 0.15e1
  t35 = t22 / 0.4e1
  t37 = params.pp[0] + 0.1e1
  t38 = t35 ** t37
  t39 = params.beta4[0] * t38
  t40 = t19 * t23 / 0.2e1 + t27 * t13 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t30 * t31 + t39
  t44 = 0.1e1 + 0.1e1 / t1 / t40 / 0.2e1
  t45 = jnp.log(t44)
  t46 = t1 * t16 * t45
  t47 = 0.2e1 * t46
  t48 = r0 - r1
  t49 = t48 ** 2
  t50 = t49 ** 2
  t51 = t10 ** 2
  t52 = t51 ** 2
  t53 = 0.1e1 / t52
  t54 = t50 * t53
  t55 = 0.1e1 / t10
  t56 = t48 * t55
  t57 = 0.1e1 + t56
  t58 = t57 <= f.p.zeta_threshold
  t59 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t60 = t59 * f.p.zeta_threshold
  t61 = t57 ** (0.1e1 / 0.3e1)
  t63 = f.my_piecewise3(t58, t60, t61 * t57)
  t64 = 0.1e1 - t56
  t65 = t64 <= f.p.zeta_threshold
  t66 = t64 ** (0.1e1 / 0.3e1)
  t68 = f.my_piecewise3(t65, t60, t66 * t64)
  t70 = 2 ** (0.1e1 / 0.3e1)
  t73 = 0.1e1 / (0.2e1 * t70 - 0.2e1)
  t74 = (t63 + t68 - 0.2e1) * t73
  t75 = params.a[1]
  t76 = params.alpha1[1]
  t80 = 0.1e1 + t76 * t3 * t13 / 0.4e1
  t83 = params.beta1[1]
  t87 = params.beta2[1] * t3
  t90 = params.beta3[1]
  t95 = params.pp[1] + 0.1e1
  t96 = t35 ** t95
  t97 = params.beta4[1] * t96
  t98 = t83 * t23 / 0.2e1 + t87 * t13 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t90 * t31 + t97
  t102 = 0.1e1 + 0.1e1 / t75 / t98 / 0.2e1
  t103 = jnp.log(t102)
  t105 = params.a[2]
  t106 = params.alpha1[2]
  t110 = 0.1e1 + t106 * t3 * t13 / 0.4e1
  t113 = params.beta1[2]
  t117 = params.beta2[2] * t3
  t120 = params.beta3[2]
  t125 = params.pp[2] + 0.1e1
  t126 = t35 ** t125
  t127 = params.beta4[2] * t126
  t128 = t113 * t23 / 0.2e1 + t117 * t13 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t120 * t31 + t127
  t132 = 0.1e1 + 0.1e1 / t105 / t128 / 0.2e1
  t133 = jnp.log(t132)
  t134 = 0.1e1 / params.fz20
  t135 = t133 * t134
  t138 = -0.2e1 * t75 * t80 * t103 - 0.2e1 * t105 * t110 * t135 + 0.2e1 * t46
  t139 = t74 * t138
  t140 = t54 * t139
  t143 = t110 * t133 * t134
  t145 = 0.2e1 * t74 * t105 * t143
  t149 = 0.1e1 / t11 / t10
  t153 = t1 * t2 * t3 * t9 * t149 * t45 / 0.6e1
  t154 = t40 ** 2
  t157 = 0.1e1 / t23
  t160 = t9 * t149
  t165 = t22 ** 0.5e0
  t176 = t16 / t154 * (-t19 * t157 * t3 * t160 / 0.12e2 - t27 * t160 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t30 * t165 * t3 * t160 - t39 * t37 * t55 / 0.3e1) / t44
  t180 = 0.4e1 * t49 * t48 * t53 * t139
  t185 = 0.4e1 * t50 / t52 / t10 * t139
  t187 = t48 / t51
  t188 = t55 - t187
  t191 = f.my_piecewise3(t58, 0, 0.4e1 / 0.3e1 * t61 * t188)
  t195 = f.my_piecewise3(t65, 0, -0.4e1 / 0.3e1 * t66 * t188)
  t197 = (t191 + t195) * t73
  t206 = t98 ** 2
  t226 = t105 * t106
  t232 = t128 ** 2
  t233 = 0.1e1 / t232
  t248 = -t113 * t157 * t3 * t160 / 0.12e2 - t117 * t160 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t120 * t165 * t3 * t160 - t127 * t125 * t55 / 0.3e1
  t249 = 0.1e1 / t132
  t255 = t54 * t74 * (t75 * t76 * t3 * t9 * t149 * t103 / 0.6e1 + t80 / t206 * (-t83 * t157 * t3 * t160 / 0.12e2 - t87 * t160 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t90 * t165 * t3 * t160 - t97 * t95 * t55 / 0.3e1) / t102 - t153 - t176 + t226 * t20 * t8 * t149 * t135 / 0.6e1 + t110 * t233 * t248 * t249 * t134)
  t265 = t74 * t226 * t3 * t9 * t149 * t133 * t134 / 0.6e1
  t270 = t74 * t110 * t233 * t248 * t249 * t134
  vrho_0_ = -t47 + t140 + t145 + t10 * (0.2e1 * t197 * t105 * t143 + t54 * t197 * t138 + t153 + t176 + t180 - t185 + t255 - t265 - t270)
  t273 = -t55 - t187
  t276 = f.my_piecewise3(t58, 0, 0.4e1 / 0.3e1 * t61 * t273)
  t280 = f.my_piecewise3(t65, 0, -0.4e1 / 0.3e1 * t66 * t273)
  t282 = (t276 + t280) * t73
  vrho_1_ = -t47 + t140 + t145 + t10 * (0.2e1 * t282 * t105 * t143 + t54 * t282 * t138 + t153 + t176 - t180 - t185 + t255 - t265 - t270)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
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
  params_alpha1_raw = params.alpha1
  if isinstance(params_alpha1_raw, (str, bytes, dict)):
    params_alpha1 = params_alpha1_raw
  else:
    try:
      params_alpha1_seq = list(params_alpha1_raw)
    except TypeError:
      params_alpha1 = params_alpha1_raw
    else:
      params_alpha1_seq = np.asarray(params_alpha1_seq, dtype=np.float64)
      params_alpha1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha1_seq))
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))
  params_beta3_raw = params.beta3
  if isinstance(params_beta3_raw, (str, bytes, dict)):
    params_beta3 = params_beta3_raw
  else:
    try:
      params_beta3_seq = list(params_beta3_raw)
    except TypeError:
      params_beta3 = params_beta3_raw
    else:
      params_beta3_seq = np.asarray(params_beta3_seq, dtype=np.float64)
      params_beta3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta3_seq))
  params_beta4_raw = params.beta4
  if isinstance(params_beta4_raw, (str, bytes, dict)):
    params_beta4 = params_beta4_raw
  else:
    try:
      params_beta4_seq = list(params_beta4_raw)
    except TypeError:
      params_beta4 = params_beta4_raw
    else:
      params_beta4_seq = np.asarray(params_beta4_seq, dtype=np.float64)
      params_beta4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta4_seq))
  params_fz20_raw = params.fz20
  if isinstance(params_fz20_raw, (str, bytes, dict)):
    params_fz20 = params_fz20_raw
  else:
    try:
      params_fz20_seq = list(params_fz20_raw)
    except TypeError:
      params_fz20 = params_fz20_raw
    else:
      params_fz20_seq = np.asarray(params_fz20_seq, dtype=np.float64)
      params_fz20 = np.concatenate((np.array([np.nan], dtype=np.float64), params_fz20_seq))
  params_pp_raw = params.pp
  if isinstance(params_pp_raw, (str, bytes, dict)):
    params_pp = params_pp_raw
  else:
    try:
      params_pp_seq = list(params_pp_raw)
    except TypeError:
      params_pp = params_pp_raw
    else:
      params_pp_seq = np.asarray(params_pp_seq, dtype=np.float64)
      params_pp = np.concatenate((np.array([np.nan], dtype=np.float64), params_pp_seq))

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  functional_body = lambda rs, zeta: f_pw(rs, zeta)

  t1 = params.a[0]
  t2 = params.alpha1[0]
  t3 = 3 ** (0.1e1 / 0.3e1)
  t6 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t9 = t6 * t8
  t10 = r0 ** (0.1e1 / 0.3e1)
  t11 = 0.1e1 / t10
  t12 = t9 * t11
  t15 = 0.1e1 + t2 * t3 * t12 / 0.4e1
  t18 = params.beta1[0]
  t21 = t3 * t6 * t8 * t11
  t22 = jnp.sqrt(t21)
  t26 = params.beta2[0] * t3
  t29 = params.beta3[0]
  t30 = t21 ** 0.15e1
  t34 = t21 / 0.4e1
  t36 = params.pp[0] + 0.1e1
  t37 = t34 ** t36
  t38 = params.beta4[0] * t37
  t39 = t18 * t22 / 0.2e1 + t26 * t12 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t29 * t30 + t38
  t43 = 0.1e1 + 0.1e1 / t1 / t39 / 0.2e1
  t44 = jnp.log(t43)
  t48 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t50 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t48 * f.p.zeta_threshold, 1)
  t53 = 2 ** (0.1e1 / 0.3e1)
  t57 = (0.2e1 * t50 - 0.2e1) / (0.2e1 * t53 - 0.2e1)
  t58 = params.a[2]
  t60 = params.alpha1[2]
  t64 = 0.1e1 + t60 * t3 * t12 / 0.4e1
  t66 = params.beta1[2]
  t70 = params.beta2[2] * t3
  t73 = params.beta3[2]
  t78 = params.pp[2] + 0.1e1
  t79 = t34 ** t78
  t80 = params.beta4[2] * t79
  t81 = t66 * t22 / 0.2e1 + t70 * t12 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t73 * t30 + t80
  t85 = 0.1e1 + 0.1e1 / t58 / t81 / 0.2e1
  t86 = jnp.log(t85)
  t88 = 0.1e1 / params.fz20
  t95 = 0.1e1 / t10 / r0
  t100 = t39 ** 2
  t103 = 0.1e1 / t22
  t106 = t9 * t95
  t111 = t21 ** 0.5e0
  t116 = 0.1e1 / r0
  t133 = t81 ** 2
  vrho_0_ = -0.2e1 * t1 * t15 * t44 + 0.2e1 * t57 * t58 * t64 * t86 * t88 + r0 * (t1 * t2 * t3 * t9 * t95 * t44 / 0.6e1 + t15 / t100 * (-t18 * t103 * t3 * t106 / 0.12e2 - t26 * t106 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t29 * t111 * t3 * t106 - t38 * t36 * t116 / 0.3e1) / t43 - t57 * t58 * t60 * t3 * t9 * t95 * t86 * t88 / 0.6e1 - t57 * t64 / t133 * (-t66 * t103 * t3 * t106 / 0.12e2 - t70 * t106 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t73 * t111 * t3 * t106 - t80 * t78 * t116 / 0.3e1) / t85 * t88)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = params.a[0]
  t2 = params.alpha1[0]
  t4 = 3 ** (0.1e1 / 0.3e1)
  t5 = t1 * t2 * t4
  t7 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t8 = 4 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t10 = t7 * t9
  t11 = r0 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / t11 / r0
  t14 = 0.1e1 / t1
  t15 = params.beta1[0]
  t17 = 0.1e1 / t11
  t19 = t4 * t7 * t9 * t17
  t20 = jnp.sqrt(t19)
  t24 = params.beta2[0] * t4
  t25 = t10 * t17
  t28 = params.beta3[0]
  t29 = t19 ** 0.15e1
  t33 = t19 / 0.4e1
  t35 = params.pp[0] + 0.1e1
  t36 = t33 ** t35
  t37 = params.beta4[0] * t36
  t38 = t15 * t20 / 0.2e1 + t24 * t25 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t28 * t29 + t37
  t42 = 0.1e1 + t14 / t38 / 0.2e1
  t43 = jnp.log(t42)
  t48 = t2 * t4
  t51 = 0.1e1 + t48 * t25 / 0.4e1
  t52 = t38 ** 2
  t53 = 0.1e1 / t52
  t54 = t51 * t53
  t55 = 0.1e1 / t20
  t57 = t15 * t55 * t4
  t58 = t10 * t13
  t63 = t19 ** 0.5e0
  t65 = t28 * t63 * t4
  t68 = 0.1e1 / r0
  t72 = -t57 * t58 / 0.12e2 - t24 * t58 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t65 * t58 - t37 * t35 * t68 / 0.3e1
  t73 = 0.1e1 / t42
  t74 = t72 * t73
  t78 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t80 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t78 * f.p.zeta_threshold, 1)
  t83 = 2 ** (0.1e1 / 0.3e1)
  t87 = (0.2e1 * t80 - 0.2e1) / (0.2e1 * t83 - 0.2e1)
  t88 = params.a[2]
  t89 = params.alpha1[2]
  t92 = t87 * t88 * t89 * t4
  t93 = 0.1e1 / t88
  t94 = params.beta1[2]
  t98 = params.beta2[2] * t4
  t101 = params.beta3[2]
  t106 = params.pp[2] + 0.1e1
  t107 = t33 ** t106
  t108 = params.beta4[2] * t107
  t109 = t94 * t20 / 0.2e1 + t98 * t25 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t101 * t29 + t108
  t113 = 0.1e1 + t93 / t109 / 0.2e1
  t114 = jnp.log(t113)
  t116 = 0.1e1 / params.fz20
  t121 = t89 * t4
  t124 = 0.1e1 + t121 * t25 / 0.4e1
  t125 = t87 * t124
  t126 = t109 ** 2
  t127 = 0.1e1 / t126
  t129 = t94 * t55 * t4
  t135 = t101 * t63 * t4
  t141 = -t129 * t58 / 0.12e2 - t98 * t58 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t135 * t58 - t108 * t106 * t68 / 0.3e1
  t143 = 0.1e1 / t113
  t144 = t143 * t116
  t148 = r0 ** 2
  t150 = 0.1e1 / t11 / t148
  t163 = t72 ** 2
  t168 = 0.1e1 / t20 / t19
  t170 = t4 ** 2
  t172 = t7 ** 2
  t174 = t11 ** 2
  t177 = t172 * t8 / t174 / t148
  t180 = t10 * t150
  t185 = t19 ** (-0.5e0)
  t192 = t35 ** 2
  t193 = 0.1e1 / t148
  t203 = t52 ** 2
  t206 = t42 ** 2
  t228 = t141 ** 2
  t247 = t106 ** 2
  t258 = t126 ** 2
  t262 = t113 ** 2
  v2rho2_0_ = t5 * t10 * t13 * t43 / 0.3e1 + 0.2e1 * t54 * t74 - t92 * t10 * t13 * t114 * t116 / 0.3e1 - 0.2e1 * t125 * t127 * t141 * t144 + r0 * (-0.2e1 / 0.9e1 * t5 * t10 * t150 * t43 - t48 * t10 * t13 * t53 * t74 / 0.6e1 - 0.2e1 * t51 / t52 / t38 * t163 * t73 + t54 * (-t15 * t168 * t170 * t177 / 0.18e2 + t57 * t180 / 0.9e1 + t24 * t180 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t28 * t185 * t170 * t177 + 0.83333333333333333333333333333333333333333333333333e-1 * t65 * t180 + t37 * t192 * t193 / 0.9e1 + t37 * t35 * t193 / 0.3e1) * t73 + t51 / t203 * t163 / t206 * t14 / 0.2e1 + 0.2e1 / 0.9e1 * t92 * t10 * t150 * t114 * t116 + t87 * t121 * t7 * t9 * t13 * t127 * t141 * t143 * t116 / 0.6e1 + 0.2e1 * t125 / t126 / t109 * t228 * t144 - t125 * t127 * (-t94 * t168 * t170 * t177 / 0.18e2 + t129 * t180 / 0.9e1 + t98 * t180 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t101 * t185 * t170 * t177 + 0.83333333333333333333333333333333333333333333333333e-1 * t135 * t180 + t108 * t247 * t193 / 0.9e1 + t108 * t106 * t193 / 0.3e1) * t144 - t87 * t124 / t258 * t228 / t262 * t116 * t93 / 0.2e1)
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.a[0]
  t2 = params.alpha1[0]
  t4 = 3 ** (0.1e1 / 0.3e1)
  t5 = t1 * t2 * t4
  t6 = 0.1e1 / jnp.pi
  t7 = t6 ** (0.1e1 / 0.3e1)
  t8 = 4 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t10 = t7 * t9
  t11 = r0 ** 2
  t12 = r0 ** (0.1e1 / 0.3e1)
  t14 = 0.1e1 / t12 / t11
  t15 = 0.1e1 / t1
  t16 = params.beta1[0]
  t17 = t4 * t7
  t18 = 0.1e1 / t12
  t20 = t17 * t9 * t18
  t21 = jnp.sqrt(t20)
  t25 = params.beta2[0] * t4
  t26 = t10 * t18
  t29 = params.beta3[0]
  t30 = t20 ** 0.15e1
  t34 = t20 / 0.4e1
  t36 = params.pp[0] + 0.1e1
  t37 = t34 ** t36
  t38 = params.beta4[0] * t37
  t39 = t16 * t21 / 0.2e1 + t25 * t26 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t29 * t30 + t38
  t43 = 0.1e1 + t15 / t39 / 0.2e1
  t44 = jnp.log(t43)
  t49 = t2 * t4
  t50 = t49 * t10
  t52 = 0.1e1 / t12 / r0
  t53 = t39 ** 2
  t54 = 0.1e1 / t53
  t55 = t52 * t54
  t56 = 0.1e1 / t21
  t58 = t16 * t56 * t4
  t59 = t10 * t52
  t64 = t20 ** 0.5e0
  t66 = t29 * t64 * t4
  t69 = 0.1e1 / r0
  t73 = -t58 * t59 / 0.12e2 - t25 * t59 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t66 * t59 - t38 * t36 * t69 / 0.3e1
  t74 = 0.1e1 / t43
  t75 = t73 * t74
  t81 = 0.1e1 + t49 * t26 / 0.4e1
  t83 = 0.1e1 / t53 / t39
  t84 = t81 * t83
  t85 = t73 ** 2
  t86 = t85 * t74
  t89 = t81 * t54
  t91 = 0.1e1 / t21 / t20
  t93 = t4 ** 2
  t94 = t16 * t91 * t93
  t95 = t7 ** 2
  t96 = t95 * t8
  t97 = t12 ** 2
  t100 = t96 / t97 / t11
  t103 = t10 * t14
  t108 = t20 ** (-0.5e0)
  t110 = t29 * t108 * t93
  t115 = t36 ** 2
  t116 = 0.1e1 / t11
  t123 = -t94 * t100 / 0.18e2 + t58 * t103 / 0.9e1 + t25 * t103 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t110 * t100 + 0.83333333333333333333333333333333333333333333333333e-1 * t66 * t103 + t38 * t115 * t116 / 0.9e1 + t38 * t36 * t116 / 0.3e1
  t124 = t123 * t74
  t127 = t53 ** 2
  t128 = 0.1e1 / t127
  t129 = t81 * t128
  t130 = t43 ** 2
  t131 = 0.1e1 / t130
  t133 = t85 * t131 * t15
  t137 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t139 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t137 * f.p.zeta_threshold, 1)
  t142 = 2 ** (0.1e1 / 0.3e1)
  t146 = (0.2e1 * t139 - 0.2e1) / (0.2e1 * t142 - 0.2e1)
  t147 = params.a[2]
  t148 = params.alpha1[2]
  t151 = t146 * t147 * t148 * t4
  t152 = 0.1e1 / t147
  t153 = params.beta1[2]
  t157 = params.beta2[2] * t4
  t160 = params.beta3[2]
  t165 = params.pp[2] + 0.1e1
  t166 = t34 ** t165
  t167 = params.beta4[2] * t166
  t168 = t153 * t21 / 0.2e1 + t157 * t26 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t160 * t30 + t167
  t172 = 0.1e1 + t152 / t168 / 0.2e1
  t173 = jnp.log(t172)
  t175 = 0.1e1 / params.fz20
  t180 = t148 * t4
  t182 = t146 * t180 * t7
  t183 = t9 * t52
  t184 = t168 ** 2
  t185 = 0.1e1 / t184
  t186 = t183 * t185
  t188 = t153 * t56 * t4
  t194 = t160 * t64 * t4
  t200 = -t188 * t59 / 0.12e2 - t157 * t59 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t194 * t59 - t167 * t165 * t69 / 0.3e1
  t201 = 0.1e1 / t172
  t202 = t200 * t201
  t203 = t202 * t175
  t209 = 0.1e1 + t180 * t26 / 0.4e1
  t210 = t146 * t209
  t212 = 0.1e1 / t184 / t168
  t213 = t200 ** 2
  t215 = t201 * t175
  t220 = t153 * t91 * t93
  t228 = t160 * t108 * t93
  t233 = t165 ** 2
  t240 = -t220 * t100 / 0.18e2 + t188 * t103 / 0.9e1 + t157 * t103 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t228 * t100 + 0.83333333333333333333333333333333333333333333333333e-1 * t194 * t103 + t167 * t233 * t116 / 0.9e1 + t167 * t165 * t116 / 0.3e1
  t245 = t184 ** 2
  t246 = 0.1e1 / t245
  t248 = t146 * t209 * t246
  t249 = t172 ** 2
  t250 = 0.1e1 / t249
  t252 = t175 * t152
  t265 = t11 * r0
  t267 = 0.1e1 / t12 / t265
  t286 = t85 * t73
  t290 = t1 ** 2
  t318 = -t50 * t52 * t128 * t133 / 0.8e1 - 0.3e1 / 0.2e1 * t248 * t240 * t250 * t252 * t200 - 0.14e2 / 0.27e2 * t151 * t10 * t267 * t173 * t175 - t182 * t9 * t14 * t185 * t203 / 0.3e1 + t182 * t186 * t240 * t201 * t175 / 0.4e1 + t81 / t127 / t53 * t286 / t130 / t43 / t290 / 0.2e1 - 0.6e1 * t84 * t75 * t123 - 0.3e1 * t81 / t127 / t39 * t286 * t131 * t15 + 0.6e1 * t129 * t286 * t74 + t50 * t52 * t83 * t86 / 0.2e1 - t182 * t183 * t212 * t213 * t201 * t175 / 0.2e1
  t335 = 0.1e1 / t21 / t93 / t95 / t8 * t97 / 0.4e1
  t337 = t11 ** 2
  t339 = t6 / t337
  t344 = t96 / t97 / t265
  t347 = t10 * t267
  t352 = t20 ** (-0.15e1)
  t361 = 0.1e1 / t265
  t390 = t213 * t200
  t416 = t147 ** 2
  t452 = t146 * t148 * t17 * t9 * t52 * t246 * t213 * t250 * t175 * t152 / 0.8e1 + t89 * (-t16 * t335 * t339 / 0.3e1 + 0.2e1 / 0.9e1 * t94 * t344 - 0.7e1 / 0.27e2 * t58 * t347 - 0.7e1 / 0.27e2 * t25 * t347 + 0.83333333333333333333333333333333333333333333333332e-1 * t29 * t352 * t339 - 0.16666666666666666666666666666666666666666666666666e0 * t110 * t344 - 0.19444444444444444444444444444444444444444444444444e0 * t66 * t347 - t38 * t115 * t36 * t361 / 0.27e2 - t38 * t115 * t361 / 0.3e1 - 0.2e1 / 0.3e1 * t38 * t36 * t361) * t74 + 0.3e1 / 0.2e1 * t129 * t123 * t131 * t15 * t73 + 0.14e2 / 0.27e2 * t5 * t10 * t267 * t44 + t50 * t14 * t54 * t75 / 0.3e1 - t50 * t55 * t124 / 0.4e1 - 0.6e1 * t210 * t246 * t390 * t215 + 0.6e1 * t146 * t209 * t212 * t202 * t175 * t240 + 0.3e1 * t146 * t209 / t245 / t168 * t390 * t250 * t252 - t146 * t209 / t245 / t184 * t390 / t249 / t172 * t175 / t416 / 0.2e1 - t210 * t185 * (-t153 * t335 * t339 / 0.3e1 + 0.2e1 / 0.9e1 * t220 * t344 - 0.7e1 / 0.27e2 * t188 * t347 - 0.7e1 / 0.27e2 * t157 * t347 + 0.83333333333333333333333333333333333333333333333332e-1 * t160 * t352 * t339 - 0.16666666666666666666666666666666666666666666666666e0 * t228 * t344 - 0.19444444444444444444444444444444444444444444444444e0 * t194 * t347 - t167 * t233 * t165 * t361 / 0.27e2 - t167 * t233 * t361 / 0.3e1 - 0.2e1 / 0.3e1 * t167 * t165 * t361) * t215
  v3rho3_0_ = -0.2e1 / 0.3e1 * t5 * t10 * t14 * t44 - t50 * t55 * t75 / 0.2e1 - 0.6e1 * t84 * t86 + 0.3e1 * t89 * t124 + 0.3e1 / 0.2e1 * t129 * t133 + 0.2e1 / 0.3e1 * t151 * t10 * t14 * t173 * t175 + t182 * t186 * t203 / 0.2e1 + 0.6e1 * t210 * t212 * t213 * t215 - 0.3e1 * t210 * t185 * t240 * t215 - 0.3e1 / 0.2e1 * t248 * t213 * t250 * t252 + r0 * (t318 + t452)

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.alpha1[0]
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t1 * t2
  t4 = 0.1e1 / jnp.pi
  t5 = t4 ** (0.1e1 / 0.3e1)
  t6 = 4 ** (0.1e1 / 0.3e1)
  t7 = t6 ** 2
  t8 = t5 * t7
  t9 = r0 ** (0.1e1 / 0.3e1)
  t10 = 0.1e1 / t9
  t11 = t8 * t10
  t14 = 0.1e1 + t3 * t11 / 0.4e1
  t15 = params.beta1[0]
  t16 = t2 * t5
  t18 = t16 * t7 * t10
  t19 = jnp.sqrt(t18)
  t23 = params.beta2[0] * t2
  t26 = params.beta3[0]
  t27 = t18 ** 0.15e1
  t31 = t18 / 0.4e1
  t33 = params.pp[0] + 0.1e1
  t34 = t31 ** t33
  t35 = params.beta4[0] * t34
  t36 = t15 * t19 / 0.2e1 + t23 * t11 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t26 * t27 + t35
  t37 = t36 ** 2
  t38 = t37 * t36
  t39 = 0.1e1 / t38
  t40 = t14 * t39
  t41 = 0.1e1 / t19
  t43 = t15 * t41 * t2
  t45 = 0.1e1 / t9 / r0
  t46 = t8 * t45
  t51 = t18 ** 0.5e0
  t53 = t26 * t51 * t2
  t56 = 0.1e1 / r0
  t60 = -t43 * t46 / 0.12e2 - t23 * t46 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t53 * t46 - t35 * t33 * t56 / 0.3e1
  t61 = params.a[0]
  t62 = 0.1e1 / t61
  t66 = 0.1e1 + t62 / t36 / 0.2e1
  t67 = 0.1e1 / t66
  t68 = t60 * t67
  t69 = t2 ** 2
  t70 = t5 ** 2
  t72 = t9 ** 2
  t78 = 0.1e1 / t19 / t69 / t70 / t6 * t72 / 0.4e1
  t79 = t15 * t78
  t80 = r0 ** 2
  t81 = t80 ** 2
  t82 = 0.1e1 / t81
  t83 = t4 * t82
  t87 = 0.1e1 / t19 / t18
  t89 = t15 * t87 * t69
  t90 = t70 * t6
  t91 = t80 * r0
  t94 = t90 / t72 / t91
  t98 = 0.1e1 / t9 / t91
  t99 = t8 * t98
  t104 = t18 ** (-0.15e1)
  t105 = t26 * t104
  t108 = t18 ** (-0.5e0)
  t110 = t26 * t108 * t69
  t115 = t33 ** 2
  t116 = t115 * t33
  t117 = 0.1e1 / t91
  t127 = -t79 * t83 / 0.3e1 + 0.2e1 / 0.9e1 * t89 * t94 - 0.7e1 / 0.27e2 * t43 * t99 - 0.7e1 / 0.27e2 * t23 * t99 + 0.83333333333333333333333333333333333333333333333332e-1 * t105 * t83 - 0.16666666666666666666666666666666666666666666666666e0 * t110 * t94 - 0.19444444444444444444444444444444444444444444444444e0 * t53 * t99 - t35 * t116 * t117 / 0.27e2 - t35 * t115 * t117 / 0.3e1 - 0.2e1 / 0.3e1 * t35 * t33 * t117
  t131 = t37 ** 2
  t132 = t131 ** 2
  t135 = t60 ** 2
  t136 = t135 ** 2
  t137 = t66 ** 2
  t138 = t137 ** 2
  t141 = t61 ** 2
  t151 = 0.1e1 / t137 / t66
  t153 = 0.1e1 / t141
  t158 = 0.1e1 / t131 / t37
  t159 = t14 * t158
  t160 = 0.1e1 / t137
  t165 = 0.1e1 / t131
  t166 = t14 * t165
  t167 = t135 * t67
  t170 = t90 / t72 / t80
  t174 = 0.1e1 / t9 / t80
  t175 = t8 * t174
  t184 = 0.1e1 / t80
  t191 = -t89 * t170 / 0.18e2 + t43 * t175 / 0.9e1 + t23 * t175 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t110 * t170 + 0.83333333333333333333333333333333333333333333333333e-1 * t53 * t175 + t35 * t115 * t184 / 0.9e1 + t35 * t33 * t184 / 0.3e1
  t195 = t191 ** 2
  t204 = 0.1e1 / t131 / t36
  t205 = t14 * t204
  t209 = 0.1e1 / t37
  t210 = t14 * t209
  t214 = 0.1e1 / t19 / t4 / t56 / 0.48e2
  t217 = t81 * r0
  t221 = 0.1e1 / t9 / t217 * t2 * t8
  t225 = t4 / t217
  t230 = t90 / t72 / t81
  t234 = 0.1e1 / t9 / t81
  t235 = t8 * t234
  t240 = t18 ** (-0.25e1)
  t251 = t115 ** 2
  t264 = -0.5e1 / 0.18e2 * t15 * t214 * t4 * t221 + 0.8e1 / 0.3e1 * t79 * t225 - 0.80e2 / 0.81e2 * t89 * t230 + 0.70e2 / 0.81e2 * t43 * t235 + 0.70e2 / 0.81e2 * t23 * t235 + 0.41666666666666666666666666666666666666666666666666e-1 * t26 * t240 * t4 * t221 - 0.66666666666666666666666666666666666666666666666665e0 * t105 * t225 + 0.74074074074074074074074074074074074074074074074072e0 * t110 * t230 + 0.64814814814814814814814814814814814814814814814813e0 * t53 * t235 + t35 * t251 * t82 / 0.81e2 + 0.2e1 / 0.9e1 * t35 * t116 * t82 + 0.11e2 / 0.9e1 * t35 * t115 * t82 + 0.2e1 * t35 * t33 * t82
  t268 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t270 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t268 * f.p.zeta_threshold, 1)
  t273 = 2 ** (0.1e1 / 0.3e1)
  t277 = (0.2e1 * t270 - 0.2e1) / (0.2e1 * t273 - 0.2e1)
  t278 = params.alpha1[2]
  t279 = t278 * t2
  t282 = 0.1e1 + t279 * t11 / 0.4e1
  t283 = params.beta1[2]
  t287 = params.beta2[2] * t2
  t290 = params.beta3[2]
  t295 = params.pp[2] + 0.1e1
  t296 = t31 ** t295
  t297 = params.beta4[2] * t296
  t298 = t283 * t19 / 0.2e1 + t287 * t11 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t290 * t27 + t297
  t299 = t298 ** 2
  t300 = t299 ** 2
  t302 = 0.1e1 / t300 / t299
  t304 = t277 * t282 * t302
  t306 = t283 * t41 * t2
  t312 = t290 * t51 * t2
  t318 = -t306 * t46 / 0.12e2 - t287 * t46 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t312 * t46 - t297 * t295 * t56 / 0.3e1
  t319 = t318 ** 2
  t320 = t319 ** 2
  t321 = params.a[2]
  t322 = 0.1e1 / t321
  t326 = 0.1e1 + t322 / t298 / 0.2e1
  t327 = t326 ** 2
  t328 = 0.1e1 / t327
  t330 = 0.1e1 / params.fz20
  t331 = t330 * t322
  t335 = t3 * t8
  t336 = t174 * t209
  t337 = t191 * t67
  t341 = -0.8e1 * t40 * t68 * t127 + 0.3e1 / 0.4e1 * t14 / t132 * t136 / t138 / t141 / t61 - 0.6e1 * t14 / t131 / t38 * t136 * t151 * t153 + 0.18e2 * t159 * t136 * t160 * t62 + 0.36e2 * t166 * t167 * t191 + 0.3e1 / 0.2e1 * t166 * t195 * t160 * t62 - 0.6e1 * t40 * t195 * t67 - 0.24e2 * t205 * t136 * t67 + t210 * t264 * t67 - 0.18e2 * t304 * t320 * t328 * t331 + 0.2e1 / 0.3e1 * t335 * t336 * t337
  t346 = t45 * t209
  t347 = t127 * t67
  t351 = t45 * t165
  t352 = t135 * t60
  t353 = t352 * t67
  t357 = 0.1e1 / t300
  t359 = t277 * t282 * t357
  t361 = t283 * t87 * t69
  t369 = t290 * t108 * t69
  t374 = t295 ** 2
  t381 = -t361 * t170 / 0.18e2 + t306 * t175 / 0.9e1 + t287 * t175 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t369 * t170 + 0.83333333333333333333333333333333333333333333333333e-1 * t312 * t175 + t297 * t374 * t184 / 0.9e1 + t297 * t295 * t184 / 0.3e1
  t382 = t381 ** 2
  t391 = t299 * t298
  t397 = 0.1e1 / t327 / t326
  t399 = t321 ** 2
  t400 = 0.1e1 / t399
  t401 = t330 * t400
  t405 = t300 ** 2
  t409 = t327 ** 2
  t418 = 0.1e1 / t391
  t420 = t277 * t282 * t418
  t421 = 0.1e1 / t326
  t422 = t318 * t421
  t423 = t283 * t78
  t432 = t290 * t104
  t439 = t374 * t295
  t449 = -t423 * t83 / 0.3e1 + 0.2e1 / 0.9e1 * t361 * t94 - 0.7e1 / 0.27e2 * t306 * t99 - 0.7e1 / 0.27e2 * t287 * t99 + 0.83333333333333333333333333333333333333333333333332e-1 * t432 * t83 - 0.16666666666666666666666666666666666666666666666666e0 * t369 * t94 - 0.19444444444444444444444444444444444444444444444444e0 * t312 * t99 - t297 * t439 * t117 / 0.27e2 - t297 * t374 * t117 / 0.3e1 - 0.2e1 / 0.3e1 * t297 * t295 * t117
  t454 = t319 * t421
  t455 = t330 * t381
  t461 = t160 * t191 * t62
  t471 = t160 * t62 * t60
  t474 = -0.28e2 / 0.27e2 * t335 * t98 * t209 * t68 - t335 * t346 * t347 / 0.3e1 - 0.2e1 * t335 * t351 * t353 - 0.3e1 / 0.2e1 * t359 * t382 * t328 * t331 - 0.4e1 / 0.3e1 * t335 * t174 * t39 * t167 + 0.6e1 * t277 * t282 / t300 / t391 * t320 * t397 * t401 - 0.3e1 / 0.4e1 * t277 * t282 / t405 * t320 / t409 * t330 / t399 / t321 + 0.8e1 * t420 * t422 * t330 * t449 - 0.36e2 * t359 * t454 * t455 - 0.18e2 * t205 * t135 * t461 + 0.3e1 * t159 * t135 * t151 * t153 * t191 + 0.2e1 * t166 * t127 * t471
  t476 = t277 * t282
  t477 = 0.1e1 / t299
  t500 = t374 ** 2
  t513 = -0.5e1 / 0.18e2 * t283 * t214 * t4 * t221 + 0.8e1 / 0.3e1 * t423 * t225 - 0.80e2 / 0.81e2 * t361 * t230 + 0.70e2 / 0.81e2 * t306 * t235 + 0.70e2 / 0.81e2 * t287 * t235 + 0.41666666666666666666666666666666666666666666666666e-1 * t290 * t240 * t4 * t221 - 0.66666666666666666666666666666666666666666666666665e0 * t432 * t225 + 0.74074074074074074074074074074074074074074074074072e0 * t369 * t230 + 0.64814814814814814814814814814814814814814814814813e0 * t312 * t235 + t297 * t500 * t82 / 0.81e2 + 0.2e1 / 0.9e1 * t297 * t439 * t82 + 0.11e2 / 0.9e1 * t297 * t374 * t82 + 0.2e1 * t297 * t295 * t82
  t515 = t421 * t330
  t519 = 0.1e1 / t300 / t298
  t529 = t61 * t1 * t2
  t530 = jnp.log(t66)
  t537 = t277 * t278 * t16 * t7
  t538 = t45 * t357
  t540 = t328 * t330
  t547 = t319 * t318
  t556 = t515 * t318
  t562 = t540 * t322
  t571 = t331 * t318
  t580 = -t476 * t477 * t513 * t515 + 0.24e2 * t476 * t519 * t320 * t515 + 0.6e1 * t476 * t418 * t382 * t515 - 0.140e3 / 0.81e2 * t529 * t8 * t234 * t530 + t537 * t538 * t381 * t540 * t322 * t318 / 0.2e1 + t537 * t45 * t302 * t547 * t397 * t330 * t400 / 0.6e1 - 0.2e1 * t537 * t45 * t418 * t381 * t556 - t537 * t45 * t519 * t547 * t562 - t537 * t174 * t357 * t319 * t562 / 0.3e1 - 0.2e1 * t359 * t449 * t328 * t571 - 0.3e1 * t304 * t381 * t397 * t401 * t319
  t581 = t45 * t39
  t582 = t68 * t191
  t588 = t135 * t160 * t62
  t594 = t352 * t160 * t62
  t598 = t277 * t282 * t519
  t599 = t381 * t328
  t606 = t352 * t151 * t153
  t611 = t277 * t279 * t5
  t612 = t7 * t45
  t619 = t7 * t174
  t621 = t454 * t330
  t625 = t612 * t477
  t636 = t619 * t477
  t638 = t381 * t421 * t330
  t644 = t277 * t321 * t278 * t2
  t645 = jnp.log(t326)
  t656 = 0.2e1 * t335 * t581 * t582 + t335 * t174 * t165 * t588 / 0.3e1 + t335 * t45 * t204 * t594 + 0.18e2 * t598 * t599 * t331 * t319 - t335 * t45 * t158 * t606 / 0.6e1 + 0.2e1 * t611 * t612 * t357 * t547 * t421 * t330 + 0.4e1 / 0.3e1 * t611 * t619 * t418 * t621 + t611 * t625 * t449 * t421 * t330 / 0.3e1 + 0.28e2 / 0.27e2 * t611 * t7 * t98 * t477 * t556 - 0.2e1 / 0.3e1 * t611 * t636 * t638 + 0.140e3 / 0.81e2 * t644 * t8 * t234 * t645 * t330 - t3 * t46 * t165 * t60 * t461 / 0.2e1
  t687 = r0 * (t341 + t474 + t580 + t656) + 0.4e1 * t210 * t347 + 0.6e1 * t166 * t191 * t471 - 0.24e2 * t40 * t582 - 0.12e2 * t205 * t594 + 0.2e1 * t159 * t606 + t537 * t538 * t319 * t562 / 0.2e1 + 0.24e2 * t166 * t353 - t335 * t351 * t588 / 0.2e1 - 0.6e1 * t359 * t599 * t571 - 0.2e1 * t611 * t612 * t418 * t621
  t729 = -0.4e1 / 0.3e1 * t611 * t636 * t556 + t611 * t625 * t638 - 0.56e2 / 0.27e2 * t644 * t8 * t98 * t645 * t330 + 0.24e2 * t420 * t422 * t455 + 0.12e2 * t598 * t547 * t328 * t331 - 0.2e1 * t304 * t547 * t397 * t401 + 0.2e1 * t335 * t581 * t167 + 0.4e1 / 0.3e1 * t335 * t336 * t68 - t335 * t346 * t337 + 0.56e2 / 0.27e2 * t529 * t8 * t98 * t530 - 0.24e2 * t476 * t357 * t547 * t515 - 0.4e1 * t476 * t477 * t449 * t515
  v4rho4_0_ = t687 + t729

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = params.a[0]
  t2 = params.alpha1[0]
  t4 = 3 ** (0.1e1 / 0.3e1)
  t5 = t1 * t2 * t4
  t7 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t8 = 4 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t10 = t7 * t9
  t11 = r0 + r1
  t12 = t11 ** (0.1e1 / 0.3e1)
  t14 = 0.1e1 / t12 / t11
  t15 = 0.1e1 / t1
  t16 = params.beta1[0]
  t17 = t4 * t7
  t18 = 0.1e1 / t12
  t20 = t17 * t9 * t18
  t21 = jnp.sqrt(t20)
  t25 = params.beta2[0] * t4
  t26 = t10 * t18
  t29 = params.beta3[0]
  t30 = t20 ** 0.15e1
  t34 = t20 / 0.4e1
  t36 = params.pp[0] + 0.1e1
  t37 = t34 ** t36
  t38 = params.beta4[0] * t37
  t39 = t16 * t21 / 0.2e1 + t25 * t26 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t29 * t30 + t38
  t43 = 0.1e1 + t15 / t39 / 0.2e1
  t44 = jnp.log(t43)
  t47 = t5 * t10 * t14 * t44
  t48 = t47 / 0.3e1
  t49 = t2 * t4
  t52 = 0.1e1 + t49 * t26 / 0.4e1
  t53 = t39 ** 2
  t54 = 0.1e1 / t53
  t55 = t52 * t54
  t56 = 0.1e1 / t21
  t58 = t16 * t56 * t4
  t59 = t10 * t14
  t64 = t20 ** 0.5e0
  t66 = t29 * t64 * t4
  t69 = 0.1e1 / t11
  t73 = -t58 * t59 / 0.12e2 - t25 * t59 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t66 * t59 - t38 * t36 * t69 / 0.3e1
  t74 = 0.1e1 / t43
  t75 = t73 * t74
  t76 = t55 * t75
  t77 = 0.2e1 * t76
  t78 = r0 - r1
  t79 = t78 ** 2
  t80 = t79 * t78
  t81 = t11 ** 2
  t82 = t81 ** 2
  t83 = 0.1e1 / t82
  t84 = t80 * t83
  t85 = t78 * t69
  t86 = 0.1e1 + t85
  t87 = t86 <= f.p.zeta_threshold
  t88 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t89 = t88 * f.p.zeta_threshold
  t90 = t86 ** (0.1e1 / 0.3e1)
  t92 = f.my_piecewise3(t87, t89, t90 * t86)
  t93 = 0.1e1 - t85
  t94 = t93 <= f.p.zeta_threshold
  t95 = t93 ** (0.1e1 / 0.3e1)
  t97 = f.my_piecewise3(t94, t89, t95 * t93)
  t99 = 2 ** (0.1e1 / 0.3e1)
  t102 = 0.1e1 / (0.2e1 * t99 - 0.2e1)
  t103 = (t92 + t97 - 0.2e1) * t102
  t104 = params.a[1]
  t105 = params.alpha1[1]
  t106 = t105 * t4
  t109 = 0.1e1 + t106 * t26 / 0.4e1
  t111 = 0.1e1 / t104
  t112 = params.beta1[1]
  t116 = params.beta2[1] * t4
  t119 = params.beta3[1]
  t124 = params.pp[1] + 0.1e1
  t125 = t34 ** t124
  t126 = params.beta4[1] * t125
  t127 = t112 * t21 / 0.2e1 + t116 * t26 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t119 * t30 + t126
  t131 = 0.1e1 + t111 / t127 / 0.2e1
  t132 = jnp.log(t131)
  t136 = params.a[2]
  t137 = params.alpha1[2]
  t138 = t137 * t4
  t141 = 0.1e1 + t138 * t26 / 0.4e1
  t143 = 0.1e1 / t136
  t144 = params.beta1[2]
  t148 = params.beta2[2] * t4
  t151 = params.beta3[2]
  t156 = params.pp[2] + 0.1e1
  t157 = t34 ** t156
  t158 = params.beta4[2] * t157
  t159 = t144 * t21 / 0.2e1 + t148 * t26 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t151 * t30 + t158
  t163 = 0.1e1 + t143 / t159 / 0.2e1
  t164 = jnp.log(t163)
  t165 = 0.1e1 / params.fz20
  t166 = t164 * t165
  t169 = 0.2e1 * t1 * t52 * t44 - 0.2e1 * t104 * t109 * t132 - 0.2e1 * t136 * t141 * t166
  t170 = t103 * t169
  t172 = 0.8e1 * t84 * t170
  t173 = t79 ** 2
  t175 = 0.1e1 / t82 / t11
  t176 = t173 * t175
  t178 = 0.8e1 * t176 * t170
  t179 = t173 * t83
  t180 = 0.1e1 / t81
  t181 = t78 * t180
  t182 = t69 - t181
  t185 = f.my_piecewise3(t87, 0, 0.4e1 / 0.3e1 * t90 * t182)
  t186 = -t182
  t189 = f.my_piecewise3(t94, 0, 0.4e1 / 0.3e1 * t95 * t186)
  t191 = (t185 + t189) * t102
  t192 = t191 * t169
  t193 = t179 * t192
  t196 = t104 * t105 * t4
  t201 = t127 ** 2
  t202 = 0.1e1 / t201
  t203 = t109 * t202
  t205 = t112 * t56 * t4
  t211 = t119 * t64 * t4
  t217 = -t205 * t59 / 0.12e2 - t116 * t59 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t211 * t59 - t126 * t124 * t69 / 0.3e1
  t218 = 0.1e1 / t131
  t219 = t217 * t218
  t222 = t136 * t137
  t223 = t222 * t17
  t224 = t9 * t14
  t228 = t159 ** 2
  t229 = 0.1e1 / t228
  t230 = t141 * t229
  t232 = t144 * t56 * t4
  t238 = t151 * t64 * t4
  t244 = -t232 * t59 / 0.12e2 - t148 * t59 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t238 * t59 - t158 * t156 * t69 / 0.3e1
  t245 = 0.1e1 / t163
  t247 = t244 * t245 * t165
  t249 = t196 * t10 * t14 * t132 / 0.6e1 + t203 * t219 - t47 / 0.6e1 - t76 + t223 * t224 * t166 / 0.6e1 + t230 * t247
  t250 = t103 * t249
  t252 = 0.2e1 * t179 * t250
  t255 = t141 * t164 * t165
  t256 = t191 * t136 * t255
  t258 = t222 * t4
  t259 = t103 * t258
  t262 = t10 * t14 * t164 * t165
  t264 = t259 * t262 / 0.3e1
  t265 = t103 * t141
  t267 = t245 * t165
  t268 = t229 * t244 * t267
  t270 = 0.2e1 * t265 * t268
  t272 = t191 * t258 * t262
  t275 = 0.1e1 / t12 / t81
  t288 = t217 ** 2
  t293 = 0.1e1 / t21 / t20
  t295 = t4 ** 2
  t297 = t7 ** 2
  t299 = t12 ** 2
  t302 = t297 * t8 / t299 / t81
  t305 = t10 * t275
  t310 = t20 ** (-0.5e0)
  t317 = t124 ** 2
  t327 = t201 ** 2
  t330 = t131 ** 2
  t339 = 0.2e1 / 0.9e1 * t5 * t10 * t275 * t44
  t344 = t49 * t10 * t14 * t54 * t75 / 0.6e1
  t348 = t73 ** 2
  t351 = 0.2e1 * t52 / t53 / t39 * t348 * t74
  t366 = t36 ** 2
  t375 = t55 * (-t16 * t293 * t295 * t302 / 0.18e2 + t58 * t305 / 0.9e1 + t25 * t305 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t29 * t310 * t295 * t302 + 0.83333333333333333333333333333333333333333333333333e-1 * t66 * t305 + t38 * t366 * t180 / 0.9e1 + t38 * t36 * t180 / 0.3e1) * t74
  t376 = t53 ** 2
  t379 = t43 ** 2
  t384 = t52 / t376 * t348 / t379 * t15 / 0.2e1
  t395 = 0.1e1 / t228 / t159
  t397 = t244 ** 2
  t416 = t156 ** 2
  t423 = -t144 * t293 * t295 * t302 / 0.18e2 + t232 * t305 / 0.9e1 + t148 * t305 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t151 * t310 * t295 * t302 + 0.83333333333333333333333333333333333333333333333333e-1 * t238 * t305 + t158 * t416 * t180 / 0.9e1 + t158 * t156 * t180 / 0.3e1
  t427 = t228 ** 2
  t429 = t141 / t427
  t431 = t163 ** 2
  t432 = 0.1e1 / t431
  t437 = -0.2e1 / 0.9e1 * t196 * t10 * t275 * t132 - t106 * t10 * t14 * t202 * t219 / 0.6e1 - 0.2e1 * t109 / t201 / t127 * t288 * t218 + t203 * (-t112 * t293 * t295 * t302 / 0.18e2 + t205 * t305 / 0.9e1 + t116 * t305 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t119 * t310 * t295 * t302 + 0.83333333333333333333333333333333333333333333333333e-1 * t211 * t305 + t126 * t317 * t180 / 0.9e1 + t126 * t124 * t180 / 0.3e1) * t218 + t109 / t327 * t288 / t330 * t111 / 0.2e1 + t339 + t344 + t351 - t375 - t384 - 0.2e1 / 0.9e1 * t223 * t9 * t275 * t166 - t138 * t10 * t14 * t229 * t247 / 0.6e1 - 0.2e1 * t141 * t395 * t397 * t245 * t165 + t230 * t423 * t245 * t165 + t429 * t397 * t432 * t165 * t143 / 0.2e1
  t439 = t179 * t103 * t437
  t440 = t90 ** 2
  t441 = 0.1e1 / t440
  t442 = t182 ** 2
  t446 = 0.1e1 / t81 / t11
  t447 = t78 * t446
  t449 = -0.2e1 * t180 + 0.2e1 * t447
  t453 = f.my_piecewise3(t87, 0, 0.4e1 / 0.9e1 * t441 * t442 + 0.4e1 / 0.3e1 * t90 * t449)
  t454 = t95 ** 2
  t455 = 0.1e1 / t454
  t456 = t186 ** 2
  t463 = f.my_piecewise3(t94, 0, 0.4e1 / 0.9e1 * t455 * t456 - 0.4e1 / 0.3e1 * t95 * t449)
  t465 = (t453 + t463) * t102
  t469 = t179 * t191 * t249
  t471 = t176 * t192
  t474 = 0.8e1 * t176 * t250
  t475 = t84 * t192
  t478 = 0.8e1 * t84 * t250
  t484 = t103 * t138 * t7 * t224 * t229 * t247 / 0.6e1
  t485 = -t272 / 0.3e1 + t439 + t179 * t465 * t169 + 0.2e1 * t469 - 0.8e1 * t471 - t474 + t384 + 0.8e1 * t475 + t478 - t351 + t484
  t490 = 0.2e1 / 0.9e1 * t259 * t10 * t275 * t164 * t165
  t496 = 0.12e2 * t79 * t83 * t170
  t499 = 0.32e2 * t80 * t175 * t170
  t504 = 0.20e2 * t173 / t82 / t81 * t170
  t508 = 0.2e1 * t265 * t395 * t397 * t267
  t514 = t103 * t429 * t397 * t432 * t165 * t143 / 0.2e1
  t516 = t191 * t141 * t268
  t520 = t265 * t229 * t423 * t267
  t521 = 0.2e1 * t465 * t136 * t255 - t339 - t344 + t375 + t490 + t496 - t499 + t504 + t508 - t514 - 0.2e1 * t516 - t520
  d11 = t48 + t77 + t172 - t178 + 0.2e1 * t193 + t252 + 0.4e1 * t256 - t264 - t270 + t11 * (t485 + t521)
  t525 = -t69 - t181
  t528 = f.my_piecewise3(t87, 0, 0.4e1 / 0.3e1 * t90 * t525)
  t529 = -t525
  t532 = f.my_piecewise3(t94, 0, 0.4e1 / 0.3e1 * t95 * t529)
  t534 = (t528 + t532) * t102
  t535 = t534 * t169
  t536 = t179 * t535
  t538 = t534 * t136 * t255
  t540 = t84 * t535
  t542 = t176 * t535
  t551 = f.my_piecewise3(t87, 0, 0.4e1 / 0.9e1 * t441 * t525 * t182 + 0.8e1 / 0.3e1 * t90 * t78 * t446)
  t559 = f.my_piecewise3(t94, 0, 0.4e1 / 0.9e1 * t455 * t529 * t186 - 0.8e1 / 0.3e1 * t95 * t78 * t446)
  t561 = (t551 + t559) * t102
  t565 = t179 * t534 * t249
  t568 = t179 * t561 * t169 - t351 + t375 + t384 + t469 - 0.4e1 * t471 - t474 - 0.4e1 * t475 - t496 + t504 + 0.4e1 * t540 - 0.4e1 * t542 + t565
  t573 = t534 * t141 * t268
  t576 = t534 * t258 * t262
  t578 = t439 - t514 - t344 + 0.2e1 * t561 * t136 * t255 - t573 + t508 - t516 - t520 - t339 + t484 - t272 / 0.6e1 + t490 - t576 / 0.6e1
  d12 = t48 + t77 - t178 + t193 + t252 + 0.2e1 * t256 - t264 - t270 + t536 + 0.2e1 * t538 + t11 * (t568 + t578)
  t584 = t525 ** 2
  t588 = 0.2e1 * t180 + 0.2e1 * t447
  t592 = f.my_piecewise3(t87, 0, 0.4e1 / 0.9e1 * t441 * t584 + 0.4e1 / 0.3e1 * t90 * t588)
  t593 = t529 ** 2
  t600 = f.my_piecewise3(t94, 0, 0.4e1 / 0.9e1 * t455 * t593 - 0.4e1 / 0.3e1 * t95 * t588)
  t602 = (t592 + t600) * t102
  t608 = t179 * t602 * t169 + t384 + t439 - t474 - t478 + t496 - t520 - 0.8e1 * t540 - 0.8e1 * t542 + 0.2e1 * t565 - 0.2e1 * t573
  t613 = -t351 + 0.2e1 * t602 * t136 * t255 + t504 + t499 + t375 + t508 - t514 - t344 - t339 + t490 + t484 - t576 / 0.3e1
  d22 = t48 + t77 - t172 - t178 + 0.2e1 * t536 + t252 + 0.4e1 * t538 - t264 - t270 + t11 * (t608 + t613)
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = params.alpha1[0]
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t1 * t2
  t4 = 0.1e1 / jnp.pi
  t5 = t4 ** (0.1e1 / 0.3e1)
  t6 = 4 ** (0.1e1 / 0.3e1)
  t7 = t6 ** 2
  t8 = t5 * t7
  t9 = r0 + r1
  t10 = t9 ** (0.1e1 / 0.3e1)
  t11 = 0.1e1 / t10
  t12 = t8 * t11
  t15 = 0.1e1 + t3 * t12 / 0.4e1
  t16 = params.beta1[0]
  t17 = t2 * t5
  t19 = t17 * t7 * t11
  t20 = jnp.sqrt(t19)
  t24 = params.beta2[0] * t2
  t27 = params.beta3[0]
  t28 = t19 ** 0.15e1
  t32 = t19 / 0.4e1
  t34 = params.pp[0] + 0.1e1
  t35 = t32 ** t34
  t36 = params.beta4[0] * t35
  t37 = t16 * t20 / 0.2e1 + t24 * t12 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t27 * t28 + t36
  t38 = t37 ** 2
  t40 = 0.1e1 / t38 / t37
  t41 = t15 * t40
  t42 = 0.1e1 / t20
  t44 = t16 * t42 * t2
  t46 = 0.1e1 / t10 / t9
  t47 = t8 * t46
  t52 = t19 ** 0.5e0
  t54 = t27 * t52 * t2
  t57 = 0.1e1 / t9
  t61 = -t44 * t47 / 0.12e2 - t24 * t47 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t54 * t47 - t36 * t34 * t57 / 0.3e1
  t62 = t61 ** 2
  t63 = params.a[0]
  t64 = 0.1e1 / t63
  t68 = 0.1e1 + t64 / t37 / 0.2e1
  t69 = 0.1e1 / t68
  t70 = t62 * t69
  t71 = t41 * t70
  t73 = 0.1e1 / t38
  t74 = t15 * t73
  t76 = 0.1e1 / t20 / t19
  t78 = t2 ** 2
  t79 = t16 * t76 * t78
  t80 = t5 ** 2
  t81 = t80 * t6
  t82 = t9 ** 2
  t83 = t10 ** 2
  t86 = t81 / t83 / t82
  t90 = 0.1e1 / t10 / t82
  t91 = t8 * t90
  t96 = t19 ** (-0.5e0)
  t98 = t27 * t96 * t78
  t103 = t34 ** 2
  t104 = 0.1e1 / t82
  t111 = -t79 * t86 / 0.18e2 + t44 * t91 / 0.9e1 + t24 * t91 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t98 * t86 + 0.83333333333333333333333333333333333333333333333333e-1 * t54 * t91 + t36 * t103 * t104 / 0.9e1 + t36 * t34 * t104 / 0.3e1
  t112 = t111 * t69
  t113 = t74 * t112
  t115 = r0 - r1
  t116 = t115 ** 2
  t117 = t82 ** 2
  t118 = 0.1e1 / t117
  t119 = t116 * t118
  t120 = t115 * t57
  t121 = 0.1e1 + t120
  t122 = t121 <= f.p.zeta_threshold
  t123 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t124 = t123 * f.p.zeta_threshold
  t125 = t121 ** (0.1e1 / 0.3e1)
  t127 = f.my_piecewise3(t122, t124, t125 * t121)
  t128 = 0.1e1 - t120
  t129 = t128 <= f.p.zeta_threshold
  t130 = t128 ** (0.1e1 / 0.3e1)
  t132 = f.my_piecewise3(t129, t124, t130 * t128)
  t134 = 2 ** (0.1e1 / 0.3e1)
  t137 = 0.1e1 / (0.2e1 * t134 - 0.2e1)
  t138 = (t127 + t132 - 0.2e1) * t137
  t139 = params.a[1]
  t140 = params.alpha1[1]
  t141 = t140 * t2
  t144 = 0.1e1 + t141 * t12 / 0.4e1
  t146 = 0.1e1 / t139
  t147 = params.beta1[1]
  t151 = params.beta2[1] * t2
  t154 = params.beta3[1]
  t159 = params.pp[1] + 0.1e1
  t160 = t32 ** t159
  t161 = params.beta4[1] * t160
  t162 = t147 * t20 / 0.2e1 + t151 * t12 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t154 * t28 + t161
  t166 = 0.1e1 + t146 / t162 / 0.2e1
  t167 = jnp.log(t166)
  t170 = jnp.log(t68)
  t172 = params.a[2]
  t173 = params.alpha1[2]
  t174 = t173 * t2
  t177 = 0.1e1 + t174 * t12 / 0.4e1
  t179 = 0.1e1 / t172
  t180 = params.beta1[2]
  t184 = params.beta2[2] * t2
  t187 = params.beta3[2]
  t192 = params.pp[2] + 0.1e1
  t193 = t32 ** t192
  t194 = params.beta4[2] * t193
  t195 = t180 * t20 / 0.2e1 + t184 * t12 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t187 * t28 + t194
  t199 = 0.1e1 + t179 / t195 / 0.2e1
  t200 = jnp.log(t199)
  t201 = 0.1e1 / params.fz20
  t202 = t200 * t201
  t205 = -0.2e1 * t139 * t144 * t167 + 0.2e1 * t63 * t15 * t170 - 0.2e1 * t172 * t177 * t202
  t206 = t138 * t205
  t209 = t116 * t115
  t211 = 0.1e1 / t117 / t9
  t212 = t209 * t211
  t215 = t209 * t118
  t217 = t139 * t140 * t2
  t222 = t162 ** 2
  t223 = 0.1e1 / t222
  t224 = t144 * t223
  t226 = t147 * t42 * t2
  t232 = t154 * t52 * t2
  t238 = -t226 * t47 / 0.12e2 - t151 * t47 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t232 * t47 - t161 * t159 * t57 / 0.3e1
  t239 = 0.1e1 / t166
  t240 = t238 * t239
  t243 = t63 * t1 * t2
  t248 = t61 * t69
  t250 = t172 * t173
  t251 = t250 * t17
  t252 = t7 * t46
  t256 = t195 ** 2
  t257 = 0.1e1 / t256
  t258 = t177 * t257
  t260 = t180 * t42 * t2
  t266 = t187 * t52 * t2
  t272 = -t260 * t47 / 0.12e2 - t184 * t47 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t266 * t47 - t194 * t192 * t57 / 0.3e1
  t273 = 0.1e1 / t199
  t274 = t272 * t273
  t275 = t274 * t201
  t277 = t217 * t8 * t46 * t167 / 0.6e1 + t224 * t240 - t243 * t8 * t46 * t170 / 0.6e1 - t74 * t248 + t251 * t252 * t202 / 0.6e1 + t258 * t275
  t278 = t138 * t277
  t282 = -t115 * t104 + t57
  t285 = f.my_piecewise3(t122, 0, 0.4e1 / 0.3e1 * t125 * t282)
  t286 = -t282
  t289 = f.my_piecewise3(t129, 0, 0.4e1 / 0.3e1 * t130 * t286)
  t291 = (t285 + t289) * t137
  t292 = t291 * t205
  t295 = t116 ** 2
  t296 = t295 * t211
  t299 = t295 * t118
  t300 = t291 * t277
  t309 = t141 * t8
  t310 = t46 * t223
  t315 = 0.1e1 / t222 / t162
  t316 = t144 * t315
  t317 = t238 ** 2
  t318 = t317 * t239
  t322 = t147 * t76 * t78
  t330 = t154 * t96 * t78
  t335 = t159 ** 2
  t342 = -t322 * t86 / 0.18e2 + t226 * t91 / 0.9e1 + t151 * t91 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t330 * t86 + 0.83333333333333333333333333333333333333333333333333e-1 * t232 * t91 + t161 * t335 * t104 / 0.9e1 + t161 * t159 * t104 / 0.3e1
  t343 = t342 * t239
  t345 = t222 ** 2
  t346 = 0.1e1 / t345
  t347 = t144 * t346
  t348 = t166 ** 2
  t349 = 0.1e1 / t348
  t351 = t317 * t349 * t146
  t356 = t243 * t8 * t90 * t170
  t358 = t3 * t8
  t359 = t46 * t73
  t361 = t358 * t359 * t248
  t364 = t38 ** 2
  t365 = 0.1e1 / t364
  t366 = t15 * t365
  t367 = t68 ** 2
  t368 = 0.1e1 / t367
  t370 = t62 * t368 * t64
  t371 = t366 * t370
  t373 = t7 * t90
  t377 = t174 * t8
  t378 = t46 * t257
  t383 = 0.1e1 / t256 / t195
  t384 = t177 * t383
  t385 = t272 ** 2
  t387 = t385 * t273 * t201
  t391 = t180 * t76 * t78
  t399 = t187 * t96 * t78
  t404 = t192 ** 2
  t411 = -t391 * t86 / 0.18e2 + t260 * t91 / 0.9e1 + t184 * t91 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t399 * t86 + 0.83333333333333333333333333333333333333333333333333e-1 * t266 * t91 + t194 * t404 * t104 / 0.9e1 + t194 * t192 * t104 / 0.3e1
  t413 = t411 * t273 * t201
  t415 = t256 ** 2
  t416 = 0.1e1 / t415
  t417 = t177 * t416
  t419 = t199 ** 2
  t420 = 0.1e1 / t419
  t421 = t420 * t201
  t422 = t421 * t179
  t425 = -0.2e1 / 0.9e1 * t217 * t8 * t90 * t167 - t309 * t310 * t240 / 0.6e1 - 0.2e1 * t316 * t318 + t224 * t343 + t347 * t351 / 0.2e1 + 0.2e1 / 0.9e1 * t356 + t361 / 0.6e1 + 0.2e1 * t71 - t113 - t371 / 0.2e1 - 0.2e1 / 0.9e1 * t251 * t373 * t202 - t377 * t378 * t275 / 0.6e1 - 0.2e1 * t384 * t387 + t258 * t413 + t417 * t385 * t422 / 0.2e1
  t426 = t138 * t425
  t429 = t125 ** 2
  t430 = 0.1e1 / t429
  t431 = t282 ** 2
  t434 = t82 * t9
  t435 = 0.1e1 / t434
  t438 = 0.2e1 * t115 * t435 - 0.2e1 * t104
  t442 = f.my_piecewise3(t122, 0, 0.4e1 / 0.9e1 * t430 * t431 + 0.4e1 / 0.3e1 * t125 * t438)
  t443 = t130 ** 2
  t444 = 0.1e1 / t443
  t445 = t286 ** 2
  t448 = -t438
  t452 = f.my_piecewise3(t129, 0, 0.4e1 / 0.9e1 * t444 * t445 + 0.4e1 / 0.3e1 * t130 * t448)
  t454 = (t442 + t452) * t137
  t455 = t454 * t205
  t459 = -0.6e1 * t71 + 0.3e1 * t113 + 0.36e2 * t119 * t206 - 0.96e2 * t212 * t206 + 0.24e2 * t215 * t278 + 0.24e2 * t215 * t292 - 0.24e2 * t296 * t278 + 0.6e1 * t299 * t300 - 0.24e2 * t296 * t292 + 0.3e1 * t299 * t426 + 0.3e1 * t299 * t455 + 0.3e1 / 0.2e1 * t371
  t460 = t174 * t5
  t461 = t138 * t460
  t462 = t252 * t257
  t463 = t462 * t275
  t468 = t177 * t200 * t201
  t471 = t250 * t2
  t472 = t291 * t471
  t475 = t8 * t46 * t200 * t201
  t477 = t138 * t471
  t480 = t8 * t90 * t200 * t201
  t487 = 0.6e1 * t41 * t248 * t111
  t491 = t62 * t61
  t495 = t63 ** 2
  t499 = t15 / t364 / t38 * t491 / t367 / t68 / t495 / 0.2e1
  t506 = 0.3e1 * t15 / t364 / t37 * t491 * t368 * t64
  t520 = 0.1e1 / t117 / t82
  t521 = t295 * t520
  t528 = 0.3e1 * t299 * t454 * t277 + 0.3e1 * t299 * t291 * t425 - 0.96e2 * t212 * t292 + 0.24e2 * t215 * t300 + 0.12e2 * t215 * t455 + 0.60e2 * t521 * t278 + 0.60e2 * t521 * t292 - 0.24e2 * t296 * t300 - 0.12e2 * t296 * t455 - t487 + t499 - t506
  t537 = t115 * t118
  t539 = 0.6e1 * t435 - 0.6e1 * t537
  t543 = f.my_piecewise3(t122, 0, -0.8e1 / 0.27e2 / t429 / t121 * t431 * t282 + 0.4e1 / 0.3e1 * t430 * t282 * t438 + 0.4e1 / 0.3e1 * t125 * t539)
  t556 = f.my_piecewise3(t129, 0, -0.8e1 / 0.27e2 / t443 / t128 * t445 * t286 + 0.4e1 / 0.3e1 * t444 * t286 * t448 - 0.4e1 / 0.3e1 * t130 * t539)
  t558 = (t543 + t556) * t137
  t586 = t358 * t46 * t40 * t70 / 0.2e1
  t590 = t358 * t90 * t73 * t248 / 0.3e1
  t593 = t358 * t359 * t112 / 0.4e1
  t596 = t177 / t415 / t256
  t598 = t385 * t272
  t600 = 0.1e1 / t419 / t199
  t602 = t172 ** 2
  t603 = 0.1e1 / t602
  t608 = t299 * t558 * t205 + 0.36e2 * t119 * t278 + 0.36e2 * t119 * t292 - 0.96e2 * t212 * t278 - 0.120e3 * t295 / t117 / t434 * t206 + 0.240e3 * t209 * t520 * t206 + 0.24e2 * t537 * t206 - 0.144e3 * t116 * t211 * t206 + 0.2e1 * t558 * t172 * t468 + t586 + t590 - t593 - t138 * t596 * t598 * t600 * t201 * t603 / 0.2e1
  t617 = t177 / t415 / t195
  t620 = t201 * t179
  t626 = t385 * t420 * t620
  t629 = t291 * t177
  t631 = t273 * t201
  t632 = t257 * t411 * t631
  t636 = t383 * t385 * t631
  t641 = t257 * t272 * t631
  t644 = t138 * t177
  t655 = 0.1e1 / t20 / t78 / t80 / t6 * t83 / 0.4e1
  t657 = t4 * t118
  t662 = t81 / t83 / t434
  t666 = 0.1e1 / t10 / t434
  t667 = t8 * t666
  t672 = t19 ** (-0.15e1)
  t690 = -t180 * t655 * t657 / 0.3e1 + 0.2e1 / 0.9e1 * t391 * t662 - 0.7e1 / 0.27e2 * t260 * t667 - 0.7e1 / 0.27e2 * t184 * t667 + 0.83333333333333333333333333333333333333333333333332e-1 * t187 * t672 * t657 - 0.16666666666666666666666666666666666666666666666666e0 * t399 * t662 - 0.19444444444444444444444444444444444444444444444444e0 * t266 * t667 - t194 * t404 * t192 * t435 / 0.27e2 - t194 * t404 * t435 / 0.3e1 - 0.2e1 / 0.3e1 * t194 * t192 * t435
  t697 = 0.14e2 / 0.27e2 * t243 * t8 * t666 * t170
  t712 = 0.6e1 * t138 * t384 * t274 * t201 * t411 + 0.3e1 * t138 * t617 * t598 * t420 * t620 - 0.3e1 / 0.2e1 * t291 * t417 * t626 - 0.3e1 * t629 * t632 + 0.6e1 * t629 * t636 - 0.3e1 * t454 * t177 * t641 - 0.6e1 * t644 * t416 * t598 * t631 - t644 * t257 * t690 * t631 + t697 + t138 * t173 * t17 * t7 * t46 * t416 * t385 * t422 / 0.8e1 + t461 * t462 * t413 / 0.4e1 + t291 * t460 * t463 / 0.2e1
  t721 = t138 * t417
  t730 = t358 * t46 * t365 * t370 / 0.8e1
  t776 = t487 - t499 + t506 - t586 - t590 + t593 + 0.14e2 / 0.27e2 * t251 * t7 * t666 * t202 + t309 * t46 * t315 * t318 / 0.2e1 + t309 * t90 * t223 * t240 / 0.3e1 - t309 * t310 * t343 / 0.4e1 + 0.3e1 / 0.2e1 * t417 * t411 * t421 * t179 * t272 + 0.14e2 / 0.27e2 * t217 * t8 * t666 * t167 - t697 - t377 * t378 * t413 / 0.4e1 - t309 * t46 * t346 * t351 / 0.8e1 + t730
  t793 = t317 * t238
  t797 = t139 ** 2
  t826 = 0.3e1 / 0.2e1 * t366 * t111 * t368 * t64 * t61
  t874 = 0.6e1 * t366 * t491 * t69
  t903 = t74 * (-t16 * t655 * t657 / 0.3e1 + 0.2e1 / 0.9e1 * t79 * t662 - 0.7e1 / 0.27e2 * t44 * t667 - 0.7e1 / 0.27e2 * t24 * t667 + 0.83333333333333333333333333333333333333333333333332e-1 * t27 * t672 * t657 - 0.16666666666666666666666666666666666666666666666666e0 * t98 * t662 - 0.19444444444444444444444444444444444444444444444444e0 * t54 * t667 - t36 * t103 * t34 * t435 / 0.27e2 - t36 * t103 * t435 / 0.3e1 - 0.2e1 / 0.3e1 * t36 * t34 * t435) * t69
  t904 = t377 * t90 * t257 * t275 / 0.3e1 + t377 * t46 * t383 * t387 / 0.2e1 - t174 * t47 * t416 * t385 * t422 / 0.8e1 + t144 / t345 / t222 * t793 / t348 / t166 / t797 / 0.2e1 - 0.3e1 * t144 / t345 / t162 * t793 * t349 * t146 + t258 * t690 * t273 * t201 - 0.6e1 * t316 * t240 * t342 + 0.6e1 * t417 * t598 * t273 * t201 - 0.6e1 * t384 * t272 * t413 - t826 + 0.3e1 / 0.2e1 * t347 * t342 * t349 * t146 * t238 + t596 * t598 * t600 * t201 * t603 / 0.2e1 - 0.3e1 * t617 * t598 * t422 + 0.6e1 * t347 * t793 * t239 + t224 * (-t147 * t655 * t657 / 0.3e1 + 0.2e1 / 0.9e1 * t322 * t662 - 0.7e1 / 0.27e2 * t226 * t667 - 0.7e1 / 0.27e2 * t151 * t667 + 0.83333333333333333333333333333333333333333333333332e-1 * t154 * t672 * t657 - 0.16666666666666666666666666666666666666666666666666e0 * t330 * t662 - 0.19444444444444444444444444444444444444444444444444e0 * t232 * t667 - t161 * t335 * t159 * t435 / 0.27e2 - t161 * t335 * t435 / 0.3e1 - 0.2e1 / 0.3e1 * t161 * t159 * t435) * t239 - t874 - t903
  t908 = -t461 * t373 * t257 * t275 / 0.3e1 - t461 * t252 * t383 * t387 / 0.2e1 - 0.3e1 / 0.2e1 * t721 * t272 * t420 * t620 * t411 - t730 - 0.14e2 / 0.27e2 * t477 * t8 * t666 * t200 * t201 + 0.2e1 / 0.3e1 * t472 * t480 - t454 * t471 * t475 / 0.2e1 - 0.12e2 * t296 * t426 + 0.12e2 * t215 * t426 + t299 * t138 * (t776 + t904) + t826 + t874 + t903
  t924 = t461 * t463 / 0.2e1 + 0.6e1 * t454 * t172 * t468 - t472 * t475 + 0.2e1 / 0.3e1 * t477 * t480 + t9 * (t528 + t608 + t712 + t908) + 0.60e2 * t521 * t206 - t361 / 0.2e1 - 0.3e1 / 0.2e1 * t721 * t626 - 0.2e1 / 0.3e1 * t356 + 0.6e1 * t644 * t636 - 0.6e1 * t629 * t641 - 0.3e1 * t644 * t632
  d111 = t459 + t924

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 - r1
  t2 = r0 + r1
  t3 = 0.1e1 / t2
  t4 = t1 * t3
  t5 = 0.1e1 + t4
  t6 = t5 <= f.p.zeta_threshold
  t7 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t8 = t7 * f.p.zeta_threshold
  t9 = t5 ** (0.1e1 / 0.3e1)
  t11 = f.my_piecewise3(t6, t8, t9 * t5)
  t12 = 0.1e1 - t4
  t13 = t12 <= f.p.zeta_threshold
  t14 = t12 ** (0.1e1 / 0.3e1)
  t16 = f.my_piecewise3(t13, t8, t14 * t12)
  t17 = t11 + t16 - 0.2e1
  t18 = 2 ** (0.1e1 / 0.3e1)
  t21 = 0.1e1 / (0.2e1 * t18 - 0.2e1)
  t22 = t17 * t21
  t23 = params.alpha1[2]
  t24 = 3 ** (0.1e1 / 0.3e1)
  t25 = t23 * t24
  t26 = 0.1e1 / jnp.pi
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = t27 * t29
  t31 = t2 ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = t30 * t32
  t36 = 0.1e1 + t25 * t33 / 0.4e1
  t37 = t22 * t36
  t38 = params.beta1[2]
  t39 = t24 * t27
  t41 = t39 * t29 * t32
  t42 = jnp.sqrt(t41)
  t46 = params.beta2[2] * t24
  t49 = params.beta3[2]
  t50 = t41 ** 0.15e1
  t54 = t41 / 0.4e1
  t56 = params.pp[2] + 0.1e1
  t57 = t54 ** t56
  t58 = params.beta4[2] * t57
  t59 = t38 * t42 / 0.2e1 + t46 * t33 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t49 * t50 + t58
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t62 = t24 ** 2
  t63 = t27 ** 2
  t65 = t31 ** 2
  t71 = 0.1e1 / t42 / t62 / t63 / t28 * t65 / 0.4e1
  t72 = t38 * t71
  t73 = t2 ** 2
  t74 = t73 ** 2
  t75 = 0.1e1 / t74
  t76 = t26 * t75
  t80 = 0.1e1 / t42 / t41
  t82 = t38 * t80 * t62
  t83 = t63 * t28
  t84 = t73 * t2
  t87 = t83 / t65 / t84
  t90 = 0.1e1 / t42
  t92 = t38 * t90 * t24
  t94 = 0.1e1 / t31 / t84
  t95 = t30 * t94
  t100 = t41 ** (-0.15e1)
  t101 = t49 * t100
  t104 = t41 ** (-0.5e0)
  t106 = t49 * t104 * t62
  t109 = t41 ** 0.5e0
  t111 = t49 * t109 * t24
  t114 = t56 ** 2
  t115 = t114 * t56
  t116 = 0.1e1 / t84
  t126 = -t72 * t76 / 0.3e1 + 0.2e1 / 0.9e1 * t82 * t87 - 0.7e1 / 0.27e2 * t92 * t95 - 0.7e1 / 0.27e2 * t46 * t95 + 0.83333333333333333333333333333333333333333333333332e-1 * t101 * t76 - 0.16666666666666666666666666666666666666666666666666e0 * t106 * t87 - 0.19444444444444444444444444444444444444444444444444e0 * t111 * t95 - t58 * t115 * t116 / 0.27e2 - t58 * t114 * t116 / 0.3e1 - 0.2e1 / 0.3e1 * t58 * t56 * t116
  t128 = params.a[2]
  t129 = 0.1e1 / t128
  t133 = 0.1e1 + t129 / t59 / 0.2e1
  t134 = 0.1e1 / t133
  t135 = 0.1e1 / params.fz20
  t136 = t134 * t135
  t137 = t61 * t126 * t136
  t140 = 0.1e1 / t73
  t142 = -t1 * t140 + t3
  t145 = f.my_piecewise3(t6, 0, 0.4e1 / 0.3e1 * t9 * t142)
  t146 = -t142
  t149 = f.my_piecewise3(t13, 0, 0.4e1 / 0.3e1 * t14 * t146)
  t151 = (t145 + t149) * t21
  t152 = t151 * t36
  t155 = t83 / t65 / t73
  t159 = 0.1e1 / t31 / t73
  t160 = t30 * t159
  t175 = -t82 * t155 / 0.18e2 + t92 * t160 / 0.9e1 + t46 * t160 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t106 * t155 + 0.83333333333333333333333333333333333333333333333333e-1 * t111 * t160 + t58 * t114 * t140 / 0.9e1 + t58 * t56 * t140 / 0.3e1
  t177 = t61 * t175 * t136
  t180 = t60 * t59
  t181 = 0.1e1 / t180
  t183 = 0.1e1 / t31 / t2
  t184 = t30 * t183
  t194 = -t92 * t184 / 0.12e2 - t46 * t184 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t111 * t184 - t58 * t56 * t3 / 0.3e1
  t195 = t194 ** 2
  t197 = t181 * t195 * t136
  t200 = t9 ** 2
  t201 = 0.1e1 / t200
  t202 = t142 ** 2
  t207 = 0.2e1 * t1 * t116 - 0.2e1 * t140
  t211 = f.my_piecewise3(t6, 0, 0.4e1 / 0.9e1 * t201 * t202 + 0.4e1 / 0.3e1 * t9 * t207)
  t212 = t14 ** 2
  t213 = 0.1e1 / t212
  t214 = t146 ** 2
  t217 = -t207
  t221 = f.my_piecewise3(t13, 0, 0.4e1 / 0.9e1 * t213 * t214 + 0.4e1 / 0.3e1 * t14 * t217)
  t223 = (t211 + t221) * t21
  t224 = t223 * t36
  t226 = t61 * t194 * t136
  t229 = t60 ** 2
  t230 = 0.1e1 / t229
  t231 = t195 * t194
  t233 = t230 * t231 * t136
  t236 = params.a[0]
  t237 = params.alpha1[0]
  t239 = t236 * t237 * t24
  t240 = 0.1e1 / t236
  t241 = params.beta1[0]
  t245 = params.beta2[0] * t24
  t248 = params.beta3[0]
  t253 = params.pp[0] + 0.1e1
  t254 = t54 ** t253
  t255 = params.beta4[0] * t254
  t256 = t241 * t42 / 0.2e1 + t245 * t33 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t248 * t50 + t255
  t260 = 0.1e1 + t240 / t256 / 0.2e1
  t261 = jnp.log(t260)
  t264 = t239 * t30 * t94 * t261
  t266 = t128 * t23
  t267 = t266 * t24
  t268 = t22 * t267
  t269 = jnp.log(t133)
  t272 = t30 * t94 * t269 * t135
  t275 = t151 * t267
  t278 = t30 * t159 * t269 * t135
  t281 = t223 * t267
  t284 = t30 * t183 * t269 * t135
  t287 = t1 ** 2
  t288 = t287 * t1
  t290 = 0.1e1 / t74 / t73
  t291 = t288 * t290
  t292 = params.a[1]
  t293 = params.alpha1[1]
  t294 = t293 * t24
  t297 = 0.1e1 + t294 * t33 / 0.4e1
  t299 = 0.1e1 / t292
  t300 = params.beta1[1]
  t304 = params.beta2[1] * t24
  t307 = params.beta3[1]
  t312 = params.pp[1] + 0.1e1
  t313 = t54 ** t312
  t314 = params.beta4[1] * t313
  t315 = t300 * t42 / 0.2e1 + t304 * t33 / 0.4e1 + 0.12500000000000000000000000000000000000000000000000e0 * t307 * t50 + t314
  t319 = 0.1e1 + t299 / t315 / 0.2e1
  t320 = jnp.log(t319)
  t322 = t237 * t24
  t325 = 0.1e1 + t322 * t33 / 0.4e1
  t329 = t269 * t135
  t332 = -0.2e1 * t128 * t36 * t329 + 0.2e1 * t236 * t325 * t261 - 0.2e1 * t292 * t297 * t320
  t333 = t22 * t332
  t336 = t36 * t230
  t337 = t22 * t336
  t338 = t133 ** 2
  t339 = 0.1e1 / t338
  t341 = t135 * t129
  t342 = t341 * t175
  t343 = t194 * t339 * t342
  t346 = t322 * t30
  t347 = t256 ** 2
  t348 = t347 ** 2
  t349 = 0.1e1 / t348
  t350 = t183 * t349
  t352 = t241 * t90 * t24
  t358 = t248 * t109 * t24
  t364 = -t352 * t184 / 0.12e2 - t245 * t184 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t358 * t184 - t255 * t253 * t3 / 0.3e1
  t365 = t364 ** 2
  t366 = t260 ** 2
  t367 = 0.1e1 / t366
  t369 = t365 * t367 * t240
  t371 = t346 * t350 * t369
  t373 = -0.4e1 * t37 * t137 - 0.12e2 * t152 * t177 + 0.24e2 * t152 * t197 - 0.12e2 * t224 * t226 - 0.24e2 * t37 * t233 + 0.56e2 / 0.27e2 * t264 - 0.56e2 / 0.27e2 * t268 * t272 + 0.8e1 / 0.3e1 * t275 * t278 - 0.2e1 * t281 * t284 + 0.960e3 * t291 * t333 - 0.6e1 * t337 * t343 - t371 / 0.2e1
  t375 = 0.1e1 / t200 / t5
  t379 = t201 * t142
  t382 = t1 * t75
  t384 = 0.6e1 * t116 - 0.6e1 * t382
  t388 = f.my_piecewise3(t6, 0, -0.8e1 / 0.27e2 * t375 * t202 * t142 + 0.4e1 / 0.3e1 * t379 * t207 + 0.4e1 / 0.3e1 * t9 * t384)
  t390 = 0.1e1 / t212 / t12
  t394 = t213 * t146
  t397 = -t384
  t401 = f.my_piecewise3(t13, 0, -0.8e1 / 0.27e2 * t390 * t214 * t146 + 0.4e1 / 0.3e1 * t394 * t217 + 0.4e1 / 0.3e1 * t14 * t397)
  t403 = (t388 + t401) * t21
  t406 = t36 * t269 * t135
  t409 = t347 * t256
  t410 = 0.1e1 / t409
  t411 = t183 * t410
  t412 = 0.1e1 / t260
  t413 = t365 * t412
  t415 = t346 * t411 * t413
  t417 = 0.1e1 / t347
  t418 = t159 * t417
  t419 = t364 * t412
  t421 = t346 * t418 * t419
  t423 = t183 * t417
  t425 = t241 * t80 * t62
  t433 = t248 * t104 * t62
  t438 = t253 ** 2
  t445 = -t425 * t155 / 0.18e2 + t352 * t160 / 0.9e1 + t245 * t160 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t433 * t155 + 0.83333333333333333333333333333333333333333333333333e-1 * t358 * t160 + t255 * t438 * t140 / 0.9e1 + t255 * t253 * t140 / 0.3e1
  t446 = t445 * t412
  t448 = t346 * t423 * t446
  t450 = t39 * t29
  t451 = t22 * t23 * t450
  t452 = t183 * t230
  t454 = t339 * t135
  t455 = t454 * t129
  t456 = t452 * t195 * t455
  t459 = t287 ** 2
  t461 = 0.1e1 / t74 / t84
  t462 = t459 * t461
  t465 = t325 * t349
  t466 = t241 * t71
  t475 = t248 * t100
  t482 = t438 * t253
  t492 = -t466 * t76 / 0.3e1 + 0.2e1 / 0.9e1 * t425 * t87 - 0.7e1 / 0.27e2 * t352 * t95 - 0.7e1 / 0.27e2 * t245 * t95 + 0.83333333333333333333333333333333333333333333333332e-1 * t475 * t76 - 0.16666666666666666666666666666666666666666666666666e0 * t433 * t87 - 0.19444444444444444444444444444444444444444444444444e0 * t358 * t95 - t255 * t482 * t116 / 0.27e2 - t255 * t438 * t116 / 0.3e1 - 0.2e1 / 0.3e1 * t255 * t253 * t116
  t494 = t367 * t240
  t495 = t494 * t364
  t497 = 0.2e1 * t465 * t492 * t495
  t499 = 0.1e1 / t31 / t74
  t503 = 0.140e3 / 0.81e2 * t239 * t30 * t499 * t261
  t507 = 0.1e1 / t42 / t26 / t3 / 0.48e2
  t510 = t74 * t2
  t514 = 0.1e1 / t31 / t510 * t24 * t30
  t517 = 0.1e1 / t510
  t518 = t26 * t517
  t523 = t83 / t65 / t74
  t526 = t30 * t499
  t531 = t41 ** (-0.25e1)
  t542 = t114 ** 2
  t555 = -0.5e1 / 0.18e2 * t38 * t507 * t26 * t514 + 0.8e1 / 0.3e1 * t72 * t518 - 0.80e2 / 0.81e2 * t82 * t523 + 0.70e2 / 0.81e2 * t92 * t526 + 0.70e2 / 0.81e2 * t46 * t526 + 0.41666666666666666666666666666666666666666666666666e-1 * t49 * t531 * t26 * t514 - 0.66666666666666666666666666666666666666666666666665e0 * t101 * t518 + 0.74074074074074074074074074074074074074074074074072e0 * t106 * t523 + 0.64814814814814814814814814814814814814814814814813e0 * t111 * t526 + t58 * t542 * t75 / 0.81e2 + 0.2e1 / 0.9e1 * t58 * t115 * t75 + 0.11e2 / 0.9e1 * t58 * t114 * t75 + 0.2e1 * t58 * t56 * t75
  t561 = t175 ** 2
  t574 = 0.1e1 / t229 / t59
  t575 = t195 ** 2
  t582 = t459 * t75
  t584 = t292 * t293 * t24
  t589 = t315 ** 2
  t590 = 0.1e1 / t589
  t591 = t297 * t590
  t593 = t300 * t90 * t24
  t599 = t307 * t109 * t24
  t605 = -t593 * t184 / 0.12e2 - t304 * t184 / 0.12e2 - 0.62500000000000000000000000000000000000000000000000e-1 * t599 * t184 - t314 * t312 * t3 / 0.3e1
  t606 = 0.1e1 / t319
  t607 = t605 * t606
  t613 = t325 * t417
  t615 = t266 * t39
  t616 = t29 * t183
  t620 = t36 * t61
  t621 = t194 * t134
  t622 = t621 * t135
  t624 = t584 * t30 * t183 * t320 / 0.6e1 + t591 * t607 - t239 * t30 * t183 * t261 / 0.6e1 - t613 * t419 + t615 * t616 * t329 / 0.6e1 + t620 * t622
  t628 = t589 ** 2
  t629 = 0.1e1 / t628
  t630 = t297 * t629
  t631 = t300 * t71
  t635 = t300 * t80 * t62
  t642 = t307 * t100
  t646 = t307 * t104 * t62
  t651 = t312 ** 2
  t652 = t651 * t312
  t662 = -t631 * t76 / 0.3e1 + 0.2e1 / 0.9e1 * t635 * t87 - 0.7e1 / 0.27e2 * t593 * t95 - 0.7e1 / 0.27e2 * t304 * t95 + 0.83333333333333333333333333333333333333333333333332e-1 * t642 * t76 - 0.16666666666666666666666666666666666666666666666666e0 * t646 * t87 - 0.19444444444444444444444444444444444444444444444444e0 * t599 * t95 - t314 * t652 * t116 / 0.27e2 - t314 * t651 * t116 / 0.3e1 - 0.2e1 / 0.3e1 * t314 * t312 * t116
  t664 = t319 ** 2
  t665 = 0.1e1 / t664
  t666 = t665 * t299
  t667 = t666 * t605
  t671 = 0.1e1 / t628 / t315
  t672 = t297 * t671
  t673 = t605 ** 2
  t691 = -t635 * t155 / 0.18e2 + t593 * t160 / 0.9e1 + t304 * t160 / 0.9e1 + 0.41666666666666666666666666666666666666666666666666e-1 * t646 * t155 + 0.83333333333333333333333333333333333333333333333333e-1 * t599 * t160 + t314 * t651 * t140 / 0.9e1 + t314 * t312 * t140 / 0.3e1
  t695 = t36 * t181
  t700 = 0.1e1 / t628 / t589
  t701 = t297 * t700
  t704 = 0.1e1 / t664 / t319
  t705 = t292 ** 2
  t706 = 0.1e1 / t705
  t711 = t229 ** 2
  t713 = t36 / t711
  t715 = t338 ** 2
  t716 = 0.1e1 / t715
  t718 = t128 ** 2
  t720 = 0.1e1 / t718 / t128
  t729 = t36 / t229 / t180
  t732 = 0.1e1 / t338 / t133
  t733 = t732 * t135
  t734 = 0.1e1 / t718
  t735 = t733 * t734
  t742 = t589 * t315
  t746 = t673 ** 2
  t751 = t628 ** 2
  t754 = t664 ** 2
  t765 = t691 ** 2
  t770 = 0.1e1 / t742
  t771 = t297 * t770
  t777 = 0.36e2 * t465 * t413 * t445
  t778 = t325 * t410
  t781 = 0.8e1 * t778 * t419 * t492
  t782 = 0.2e1 * t630 * t662 * t667 - 0.18e2 * t672 * t673 * t666 * t691 - 0.8e1 * t695 * t126 * t622 + 0.3e1 * t701 * t673 * t704 * t706 * t691 + 0.3e1 / 0.4e1 * t713 * t575 * t716 * t135 * t720 - t497 + 0.3e1 / 0.2e1 * t336 * t561 * t455 - 0.6e1 * t729 * t575 * t735 + t503 - 0.6e1 * t695 * t561 * t134 * t135 - 0.6e1 * t297 / t628 / t742 * t746 * t704 * t706 + 0.3e1 / 0.4e1 * t297 / t751 * t746 / t754 / t705 / t292 + t620 * t555 * t134 * t135 + 0.3e1 / 0.2e1 * t630 * t765 * t665 * t299 - 0.8e1 * t771 * t607 * t662 - t777 + t781
  t783 = t348 ** 2
  t786 = t365 ** 2
  t787 = t366 ** 2
  t790 = t236 ** 2
  t795 = 0.3e1 / 0.4e1 * t325 / t783 * t786 / t787 / t790 / t236
  t800 = 0.1e1 / t366 / t260
  t802 = 0.1e1 / t790
  t805 = 0.6e1 * t325 / t348 / t409 * t786 * t800 * t802
  t806 = t445 ** 2
  t810 = 0.3e1 / 0.2e1 * t465 * t806 * t367 * t240
  t812 = 0.1e1 / t229 / t60
  t813 = t36 * t812
  t819 = t36 * t574
  t822 = t454 * t175 * t129
  t827 = t454 * t129 * t194
  t834 = t294 * t30
  t837 = t673 * t665 * t299
  t842 = t673 * t605
  t844 = t842 * t704 * t706
  t848 = t25 * t30
  t849 = t183 * t61
  t851 = t126 * t134 * t135
  t857 = t842 * t665 * t299
  t860 = t183 * t770
  t861 = t607 * t691
  t866 = t231 * t134 * t135
  t871 = t195 * t134
  t872 = t871 * t135
  t876 = t25 * t184
  t882 = t230 * t195 * t455
  t886 = t136 * t175
  t890 = -t795 + t805 - t810 + 0.3e1 * t813 * t195 * t733 * t734 * t175 - 0.18e2 * t819 * t195 * t822 + 0.2e1 * t336 * t126 * t827 - 0.140e3 / 0.81e2 * t584 * t30 * t499 * t320 + t834 * t159 * t629 * t837 / 0.3e1 - t834 * t183 * t700 * t844 / 0.6e1 - t848 * t849 * t851 / 0.3e1 + t834 * t183 * t671 * t857 + 0.2e1 * t834 * t860 * t861 - 0.2e1 * t848 * t452 * t866 - 0.4e1 / 0.3e1 * t848 * t159 * t181 * t872 + t876 * t574 * t231 * t455 + t25 * t160 * t882 / 0.3e1 + 0.2e1 * t876 * t181 * t194 * t886
  t905 = t322 * t184 * t349 * t445 * t495 / 0.2e1
  t907 = 0.1e1 / t348 / t256
  t908 = t325 * t907
  t912 = 0.18e2 * t908 * t365 * t494 * t445
  t916 = t336 * t195
  t922 = t346 * t159 * t349 * t369 / 0.3e1
  t924 = 0.1e1 / t348 / t347
  t926 = t365 * t364
  t928 = t926 * t800 * t802
  t931 = t346 * t183 * t924 * t928 / 0.6e1
  t934 = t926 * t367 * t240
  t936 = t346 * t183 * t907 * t934
  t937 = t419 * t445
  t940 = 0.2e1 * t346 * t411 * t937
  t941 = t159 * t61
  t954 = 0.6e1 * t778 * t806 * t412
  t957 = 0.24e2 * t908 * t786 * t412
  t958 = t325 * t924
  t963 = 0.3e1 * t958 * t365 * t800 * t802 * t445
  t964 = t159 * t590
  t965 = t691 * t606
  t969 = -t294 * t184 * t629 * t691 * t667 / 0.2e1 - t876 * t812 * t231 * t735 / 0.6e1 + t905 + t912 + 0.18e2 * t813 * t575 * t455 + 0.36e2 * t916 * t886 - t922 + t931 - t936 - t940 + 0.2e1 / 0.3e1 * t848 * t941 * t886 - 0.28e2 / 0.27e2 * t848 * t94 * t61 * t622 - 0.24e2 * t672 * t746 * t606 + t954 + t957 - t963 + 0.2e1 / 0.3e1 * t834 * t964 * t965
  t970 = t492 * t412
  t973 = t346 * t423 * t970 / 0.3e1
  t974 = t926 * t412
  t977 = 0.2e1 * t346 * t350 * t974
  t978 = t183 * t629
  t979 = t842 * t606
  t992 = t673 * t606
  t998 = 0.2e1 / 0.3e1 * t346 * t418 * t446
  t1002 = 0.28e2 / 0.27e2 * t346 * t94 * t417 * t419
  t1006 = 0.4e1 / 0.3e1 * t346 * t159 * t410 * t413
  t1007 = t183 * t590
  t1008 = t662 * t606
  t1037 = t438 ** 2
  t1050 = -0.5e1 / 0.18e2 * t241 * t507 * t26 * t514 + 0.8e1 / 0.3e1 * t466 * t518 - 0.80e2 / 0.81e2 * t425 * t523 + 0.70e2 / 0.81e2 * t352 * t526 + 0.70e2 / 0.81e2 * t245 * t526 + 0.41666666666666666666666666666666666666666666666666e-1 * t248 * t531 * t26 * t514 - 0.66666666666666666666666666666666666666666666666665e0 * t475 * t518 + 0.74074074074074074074074074074074074074074074074072e0 * t433 * t523 + 0.64814814814814814814814814814814814814814814814813e0 * t358 * t526 + t255 * t1037 * t75 / 0.81e2 + 0.2e1 / 0.9e1 * t255 * t482 * t75 + 0.11e2 / 0.9e1 * t255 * t438 * t75 + 0.2e1 * t255 * t253 * t75
  t1052 = t613 * t1050 * t412
  t1075 = t651 ** 2
  t1088 = -0.5e1 / 0.18e2 * t300 * t507 * t26 * t514 + 0.8e1 / 0.3e1 * t631 * t518 - 0.80e2 / 0.81e2 * t635 * t523 + 0.70e2 / 0.81e2 * t593 * t526 + 0.70e2 / 0.81e2 * t304 * t526 + 0.41666666666666666666666666666666666666666666666666e-1 * t307 * t531 * t26 * t514 - 0.66666666666666666666666666666666666666666666666665e0 * t642 * t518 + 0.74074074074074074074074074074074074074074074074072e0 * t646 * t523 + 0.64814814814814814814814814814814814814814814814813e0 * t599 * t526 + t314 * t1075 * t75 / 0.81e2 + 0.2e1 / 0.9e1 * t314 * t652 * t75 + 0.11e2 / 0.9e1 * t314 * t651 * t75 + 0.2e1 * t314 * t312 * t75
  t1093 = t341 * t194
  t1111 = 0.18e2 * t958 * t786 * t367 * t240
  t1112 = t973 + t977 - 0.2e1 * t834 * t978 * t979 - 0.140e3 / 0.81e2 * t615 * t29 * t499 * t329 - 0.28e2 / 0.27e2 * t834 * t94 * t590 * t607 - 0.4e1 / 0.3e1 * t834 * t159 * t770 * t992 - t998 + t1002 + t1006 - t834 * t1007 * t1008 / 0.3e1 - 0.6e1 * t771 * t765 * t606 - t1052 + t591 * t1088 * t606 - t876 * t230 * t175 * t339 * t1093 / 0.2e1 + 0.36e2 * t630 * t992 * t691 + 0.18e2 * t701 * t746 * t665 * t299 - 0.24e2 * t819 * t575 * t134 * t135 - t1111
  t1117 = t497 - t503 - t37 * t61 * t555 * t136 - 0.4e1 * t152 * t137 + 0.6e1 * t37 * t181 * t561 * t136 - 0.6e1 * t224 * t177 + 0.12e2 * t224 * t197 - 0.4e1 * t403 * t36 * t226 + 0.24e2 * t37 * t574 * t575 * t136 - 0.24e2 * t152 * t233 + 0.4e1 * t582 * t403 * t624 + t582 * t22 * (t782 + t890 + t969 + t1112)
  t1118 = t74 ** 2
  t1123 = t5 ** 2
  t1126 = t202 ** 2
  t1132 = t207 ** 2
  t1137 = t1 * t517
  t1139 = -0.24e2 * t75 + 0.24e2 * t1137
  t1143 = f.my_piecewise3(t6, 0, 0.40e2 / 0.81e2 / t200 / t1123 * t1126 - 0.16e2 / 0.9e1 * t375 * t202 * t207 + 0.4e1 / 0.3e1 * t201 * t1132 + 0.16e2 / 0.9e1 * t379 * t384 + 0.4e1 / 0.3e1 * t9 * t1139)
  t1144 = t12 ** 2
  t1147 = t214 ** 2
  t1153 = t217 ** 2
  t1162 = f.my_piecewise3(t13, 0, 0.40e2 / 0.81e2 / t212 / t1144 * t1147 - 0.16e2 / 0.9e1 * t390 * t214 * t217 + 0.4e1 / 0.3e1 * t213 * t1153 + 0.16e2 / 0.9e1 * t394 * t397 - 0.4e1 / 0.3e1 * t14 * t1139)
  t1164 = (t1143 + t1162) * t21
  t1167 = t459 * t290
  t1192 = t29 * t159
  t1204 = -0.2e1 / 0.9e1 * t584 * t30 * t159 * t320 - t834 * t1007 * t607 / 0.6e1 - 0.2e1 * t771 * t992 + t591 * t965 + t630 * t837 / 0.2e1 + 0.2e1 / 0.9e1 * t239 * t30 * t159 * t261 + t346 * t423 * t419 / 0.6e1 + 0.2e1 * t778 * t413 - t613 * t446 - t465 * t369 / 0.2e1 - 0.2e1 / 0.9e1 * t615 * t1192 * t329 - t848 * t849 * t622 / 0.6e1 - 0.2e1 * t695 * t872 + t620 * t886 + t916 * t455 / 0.2e1
  t1205 = t22 * t1204
  t1228 = t183 * t181
  t1233 = t29 * t94
  t1248 = 0.3e1 / 0.2e1 * t336 * t175 * t827 + 0.14e2 / 0.27e2 * t584 * t30 * t94 * t320 - 0.14e2 / 0.27e2 * t264 - t876 * t882 / 0.8e1 + t371 / 0.8e1 - t848 * t849 * t886 / 0.4e1 - t834 * t978 * t837 / 0.8e1 + t848 * t941 * t622 / 0.3e1 + t848 * t1228 * t872 / 0.2e1 - t415 / 0.2e1 + 0.14e2 / 0.27e2 * t615 * t1233 * t329 + t834 * t860 * t992 / 0.2e1 + t834 * t964 * t607 / 0.3e1 - t834 * t1007 * t965 / 0.4e1 - t421 / 0.3e1 + t448 / 0.4e1
  t1262 = t465 * t445 * t495
  t1273 = t908 * t934
  t1275 = t778 * t937
  t1277 = t958 * t928
  t1282 = t465 * t974
  t1284 = t613 * t970
  t1285 = -0.3e1 * t672 * t857 - 0.6e1 * t771 * t861 + 0.6e1 * t336 * t866 + t701 * t844 / 0.2e1 + t620 * t851 - 0.6e1 * t695 * t194 * t886 - 0.3e1 / 0.2e1 * t1262 + 0.3e1 / 0.2e1 * t630 * t691 * t667 + t813 * t231 * t735 / 0.2e1 - 0.3e1 * t819 * t231 * t455 + 0.3e1 * t1273 + 0.6e1 * t1275 - t1277 / 0.2e1 + 0.6e1 * t630 * t979 + t591 * t1008 - 0.6e1 * t1282 - t1284
  t1286 = t1248 + t1285
  t1290 = t288 * t75
  t1291 = t403 * t332
  t1294 = t288 * t517
  t1295 = t223 * t332
  t1298 = t223 * t624
  t1301 = t287 * t75
  t1304 = t777 - t781 + t795 - t805 + 0.840e3 * t459 / t1118 * t333 + t582 * t1164 * t332 + t810 + 0.120e3 * t1167 * t1205 + 0.4e1 * t582 * t151 * t1286 + 0.16e2 * t1290 * t1291 - 0.192e3 * t1294 * t1295 + 0.48e2 * t1290 * t1298 + 0.72e2 * t1301 * t1295
  t1325 = t451 * t452 * t194 * t822 / 0.2e1 + 0.2e1 * t1164 * t128 * t406 - t905 - 0.2e1 / 0.3e1 * t403 * t267 * t284 + 0.140e3 / 0.81e2 * t268 * t30 * t499 * t269 * t135 - 0.56e2 / 0.27e2 * t275 * t272 + 0.4e1 / 0.3e1 * t281 * t278 - t912 + t922 - t931 + t936 + t940
  t1330 = t22 * t819
  t1331 = t195 * t339
  t1335 = t151 * t336
  t1338 = t22 * t813
  t1340 = t135 * t734
  t1347 = -0.3e1 * t1338 * t195 * t732 * t1340 * t175 - 0.2e1 * t337 * t126 * t339 * t1093 + 0.18e2 * t1330 * t1331 * t342 - 0.192e3 * t1294 * t1205 - 0.6e1 * t1335 * t343 - t1002 - t1006 - t954 - t957 + t963 - t973 - t977 + t998
  t1356 = t151 * t1204
  t1359 = t22 * t1286
  t1362 = t287 * t517
  t1363 = t151 * t332
  t1366 = t459 * t517
  t1372 = t22 * t624
  t1375 = t151 * t624
  t1382 = 0.24e2 * t75 * t17 * t21 * t332 - 0.1920e4 * t288 * t461 * t333 - 0.384e3 * t1137 * t333 + 0.240e3 * t1167 * t1375 + 0.72e2 * t1301 * t1205 + 0.48e2 * t1290 * t1356 + 0.16e2 * t1290 * t1359 - 0.16e2 * t1366 * t1291 - 0.16e2 * t1366 * t1359 - 0.576e3 * t1362 * t1363 - 0.576e3 * t1362 * t1372 + t1052
  t1423 = 0.1440e4 * t287 * t290 * t333 - 0.48e2 * t1366 * t1298 + 0.120e3 * t1167 * t1295 + 0.960e3 * t291 * t1372 - 0.384e3 * t1294 * t1375 + 0.96e2 * t382 * t1372 + 0.960e3 * t291 * t1363 - 0.2e1 * t451 * t1228 * t194 * t886 - t451 * t183 * t574 * t231 * t455 + t151 * t23 * t450 * t456 / 0.2e1 - t451 * t159 * t230 * t195 * t455 / 0.3e1 + t451 * t183 * t812 * t231 * t735 / 0.6e1 + 0.6e1 * t582 * t223 * t1204
  t1425 = t25 * t27
  t1427 = t616 * t61
  t1428 = t1427 * t622
  t1430 = t22 * t1425
  t1438 = t151 * t1425
  t1439 = t1192 * t61
  t1440 = t1439 * t622
  t1454 = t1427 * t886
  t1457 = t616 * t181 * t872
  t1466 = t223 * t1425 * t1428 + 0.2e1 * t1430 * t616 * t230 * t866 + t1430 * t1427 * t851 / 0.3e1 - 0.4e1 / 0.3e1 * t1438 * t1440 + 0.28e2 / 0.27e2 * t1430 * t1233 * t61 * t622 + 0.4e1 / 0.3e1 * t1430 * t1192 * t181 * t872 - 0.2e1 / 0.3e1 * t1430 * t1439 * t886 + t1438 * t1454 - 0.2e1 * t1438 * t1457 + 0.96e2 * t382 * t1363 - 0.48e2 * t1366 * t1356 + 0.144e3 * t1301 * t1375
  t1476 = t135 * t175
  t1485 = t1331 * t341
  t1488 = t22 * t695
  t1495 = t231 * t339 * t341
  t1500 = t231 * t732 * t1340
  t1510 = t621 * t1476
  t1517 = -0.480e3 * t462 * t1363 - 0.480e3 * t462 * t1372 + 0.6e1 * t22 * t729 * t575 * t732 * t1340 - 0.36e2 * t337 * t871 * t1476 - 0.3e1 / 0.2e1 * t337 * t561 * t339 * t341 - 0.3e1 * t223 * t336 * t1485 + 0.8e1 * t1488 * t621 * t135 * t126 + 0.12e2 * t151 * t819 * t1495 - 0.2e1 * t151 * t813 * t1500 - 0.3e1 / 0.4e1 * t22 * t713 * t575 * t716 * t135 * t720 + 0.24e2 * t151 * t695 * t1510 - 0.18e2 * t1338 * t575 * t339 * t341 + t1111
  t1533 = 0.8e1 * t403 * t128 * t406 + 0.2e1 * t415 + 0.4e1 / 0.3e1 * t421 - t448 + t451 * t456 / 0.2e1 - 0.480e3 * t462 * t333 + t2 * (t1117 + t1304 + t1325 + t1347 + t1382 + t1423 + t1466 + t1517) + t1430 * t1454 + 0.2e1 * t1438 * t1428 - 0.4e1 / 0.3e1 * t1430 * t1440 - 0.2e1 * t1430 * t1457 + 0.96e2 * t382 * t333 + 0.240e3 * t1167 * t1363
  t1557 = 0.48e2 * t1290 * t1205 - 0.48e2 * t1366 * t1205 + 0.4e1 * t582 * t1291 - 0.384e3 * t1294 * t1372 - 0.48e2 * t1366 * t1295 + 0.12e2 * t582 * t1298 + 0.12e2 * t582 * t1356 + 0.4e1 * t582 * t1359 - 0.96e2 * t1366 * t1375 + 0.6e1 * t1262 - 0.12e2 * t1273 - 0.24e2 * t1275 + 0.2e1 * t1277
  t1582 = 0.240e3 * t1167 * t1372 + 0.48e2 * t1290 * t1295 + 0.96e2 * t1290 * t1375 - 0.384e3 * t1294 * t1363 + 0.144e3 * t1301 * t1363 + 0.144e3 * t1301 * t1372 + 0.12e2 * t1330 * t1495 - 0.6e1 * t1335 * t1485 - 0.2e1 * t1338 * t1500 - 0.576e3 * t1362 * t333 + 0.24e2 * t1488 * t1510 + 0.24e2 * t1282 + 0.4e1 * t1284
  d1111 = t373 + t1533 + t1557 + t1582

  res = {'v4rho4': d1111}
  return res
