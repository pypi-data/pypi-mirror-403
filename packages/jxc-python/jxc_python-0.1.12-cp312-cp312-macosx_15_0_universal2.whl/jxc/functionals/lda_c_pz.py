"""Generated from lda_c_pz.mpl."""

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
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  ec_low = lambda i, rs: params_gamma[i] / (1 + params_beta1[i] * jnp.sqrt(rs) + params_beta2[i] * rs)

  ec_high = lambda i, rs: params_a[i] * jnp.log(rs) + params_b[i] + params_c[i] * rs * jnp.log(rs) + params_d[i] * rs

  ec = lambda i, x: f.my_piecewise3(x >= 1, ec_low(i, x), ec_high(i, x))

  f_pz = lambda rs, zeta: ec(1, rs) + (ec(2, rs) - ec(1, rs)) * f.f_zeta(zeta)

  functional_body = lambda rs, zeta: f_pz(rs, zeta)

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
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  ec_low = lambda i, rs: params_gamma[i] / (1 + params_beta1[i] * jnp.sqrt(rs) + params_beta2[i] * rs)

  ec_high = lambda i, rs: params_a[i] * jnp.log(rs) + params_b[i] + params_c[i] * rs * jnp.log(rs) + params_d[i] * rs

  ec = lambda i, x: f.my_piecewise3(x >= 1, ec_low(i, x), ec_high(i, x))

  f_pz = lambda rs, zeta: ec(1, rs) + (ec(2, rs) - ec(1, rs)) * f.f_zeta(zeta)

  functional_body = lambda rs, zeta: f_pz(rs, zeta)

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
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  ec_low = lambda i, rs: params_gamma[i] / (1 + params_beta1[i] * jnp.sqrt(rs) + params_beta2[i] * rs)

  ec_high = lambda i, rs: params_a[i] * jnp.log(rs) + params_b[i] + params_c[i] * rs * jnp.log(rs) + params_d[i] * rs

  ec = lambda i, x: f.my_piecewise3(x >= 1, ec_low(i, x), ec_high(i, x))

  f_pz = lambda rs, zeta: ec(1, rs) + (ec(2, rs) - ec(1, rs)) * f.f_zeta(zeta)

  functional_body = lambda rs, zeta: f_pz(rs, zeta)

  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t9 = 0.1e1 / t8
  t10 = t6 * t9
  t11 = t1 * t3 * t10
  t12 = t11 / 0.4e1
  t13 = 0.1e1 <= t12
  t14 = params.gamma[0]
  t15 = params.beta1[0]
  t16 = jnp.sqrt(t11)
  t20 = params.beta2[0] * t1
  t21 = t3 * t6
  t22 = t21 * t9
  t25 = 0.1e1 + t15 * t16 / 0.2e1 + t20 * t22 / 0.4e1
  t28 = params.a[0]
  t29 = jnp.log(t12)
  t33 = params.c[0] * t1
  t34 = t33 * t3
  t35 = t10 * t29
  t39 = params.d[0] * t1
  t43 = f.my_piecewise3(t13, t14 / t25, t28 * t29 + params.b[0] + t34 * t35 / 0.4e1 + t39 * t22 / 0.4e1)
  t44 = params.gamma[1]
  t45 = params.beta1[1]
  t49 = params.beta2[1] * t1
  t52 = 0.1e1 + t45 * t16 / 0.2e1 + t49 * t22 / 0.4e1
  t55 = params.a[1]
  t59 = params.c[1] * t1
  t60 = t59 * t3
  t64 = params.d[1] * t1
  t68 = f.my_piecewise3(t13, t44 / t52, t55 * t29 + params.b[1] + t60 * t35 / 0.4e1 + t64 * t22 / 0.4e1)
  t69 = t68 - t43
  t70 = r0 - r1
  t71 = 0.1e1 / t7
  t72 = t70 * t71
  t73 = 0.1e1 + t72
  t74 = t73 <= f.p.zeta_threshold
  t75 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t76 = t75 * f.p.zeta_threshold
  t77 = t73 ** (0.1e1 / 0.3e1)
  t79 = f.my_piecewise3(t74, t76, t77 * t73)
  t80 = 0.1e1 - t72
  t81 = t80 <= f.p.zeta_threshold
  t82 = t80 ** (0.1e1 / 0.3e1)
  t84 = f.my_piecewise3(t81, t76, t82 * t80)
  t85 = t79 + t84 - 0.2e1
  t87 = 2 ** (0.1e1 / 0.3e1)
  t90 = 0.1e1 / (0.2e1 * t87 - 0.2e1)
  t91 = t69 * t85 * t90
  t92 = t25 ** 2
  t95 = 0.1e1 / t16
  t99 = 0.1e1 / t8 / t7
  t100 = t21 * t99
  t109 = t6 * t99 * t29
  t117 = f.my_piecewise3(t13, -t14 / t92 * (-t15 * t95 * t1 * t100 / 0.12e2 - t20 * t100 / 0.12e2), -t28 * t71 / 0.3e1 - t34 * t109 / 0.12e2 - t33 * t100 / 0.12e2 - t39 * t100 / 0.12e2)
  t118 = t52 ** 2
  t137 = f.my_piecewise3(t13, -t44 / t118 * (-t45 * t95 * t1 * t100 / 0.12e2 - t49 * t100 / 0.12e2), -t55 * t71 / 0.3e1 - t60 * t109 / 0.12e2 - t59 * t100 / 0.12e2 - t64 * t100 / 0.12e2)
  t140 = (t137 - t117) * t85 * t90
  t141 = t7 ** 2
  t143 = t70 / t141
  t144 = t71 - t143
  t147 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t77 * t144)
  t151 = f.my_piecewise3(t81, 0, -0.4e1 / 0.3e1 * t82 * t144)
  vrho_0_ = t43 + t91 + t7 * (t117 + t140 + t69 * (t147 + t151) * t90)
  t157 = -t71 - t143
  t160 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t77 * t157)
  t164 = f.my_piecewise3(t81, 0, -0.4e1 / 0.3e1 * t82 * t157)
  vrho_1_ = t43 + t91 + t7 * (t117 + t140 + t69 * (t160 + t164) * t90)
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
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  ec_low = lambda i, rs: params_gamma[i] / (1 + params_beta1[i] * jnp.sqrt(rs) + params_beta2[i] * rs)

  ec_high = lambda i, rs: params_a[i] * jnp.log(rs) + params_b[i] + params_c[i] * rs * jnp.log(rs) + params_d[i] * rs

  ec = lambda i, x: f.my_piecewise3(x >= 1, ec_low(i, x), ec_high(i, x))

  f_pz = lambda rs, zeta: ec(1, rs) + (ec(2, rs) - ec(1, rs)) * f.f_zeta(zeta)

  functional_body = lambda rs, zeta: f_pz(rs, zeta)

  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t7
  t9 = t6 * t8
  t10 = t1 * t3 * t9
  t11 = t10 / 0.4e1
  t12 = 0.1e1 <= t11
  t13 = params.gamma[0]
  t14 = params.beta1[0]
  t15 = jnp.sqrt(t10)
  t19 = params.beta2[0] * t1
  t20 = t3 * t6
  t21 = t20 * t8
  t24 = 0.1e1 + t14 * t15 / 0.2e1 + t19 * t21 / 0.4e1
  t27 = params.a[0]
  t28 = jnp.log(t11)
  t32 = params.c[0] * t1
  t33 = t32 * t3
  t34 = t9 * t28
  t38 = params.d[0] * t1
  t42 = f.my_piecewise3(t12, t13 / t24, t27 * t28 + params.b[0] + t33 * t34 / 0.4e1 + t38 * t21 / 0.4e1)
  t43 = params.gamma[1]
  t44 = params.beta1[1]
  t48 = params.beta2[1] * t1
  t51 = 0.1e1 + t44 * t15 / 0.2e1 + t48 * t21 / 0.4e1
  t54 = params.a[1]
  t58 = params.c[1] * t1
  t59 = t58 * t3
  t63 = params.d[1] * t1
  t67 = f.my_piecewise3(t12, t43 / t51, t54 * t28 + params.b[1] + t59 * t34 / 0.4e1 + t63 * t21 / 0.4e1)
  t70 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t72 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t70 * f.p.zeta_threshold, 1)
  t74 = 0.2e1 * t72 - 0.2e1
  t76 = 2 ** (0.1e1 / 0.3e1)
  t79 = 0.1e1 / (0.2e1 * t76 - 0.2e1)
  t81 = t24 ** 2
  t84 = 0.1e1 / t15
  t88 = 0.1e1 / t7 / r0
  t89 = t20 * t88
  t95 = 0.1e1 / r0
  t99 = t6 * t88 * t28
  t107 = f.my_piecewise3(t12, -t13 / t81 * (-t14 * t84 * t1 * t89 / 0.12e2 - t19 * t89 / 0.12e2), -t27 * t95 / 0.3e1 - t33 * t99 / 0.12e2 - t32 * t89 / 0.12e2 - t38 * t89 / 0.12e2)
  t108 = t51 ** 2
  t127 = f.my_piecewise3(t12, -t43 / t108 * (-t44 * t84 * t1 * t89 / 0.12e2 - t48 * t89 / 0.12e2), -t54 * t95 / 0.3e1 - t59 * t99 / 0.12e2 - t58 * t89 / 0.12e2 - t63 * t89 / 0.12e2)
  vrho_0_ = t42 + (t67 - t42) * t74 * t79 + r0 * (t107 + (t127 - t107) * t74 * t79)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t7
  t10 = t1 * t3 * t6 * t8
  t11 = t10 / 0.4e1
  t12 = 0.1e1 <= t11
  t13 = params.gamma[0]
  t14 = params.beta1[0]
  t15 = jnp.sqrt(t10)
  t19 = params.beta2[0] * t1
  t20 = t3 * t6
  t21 = t20 * t8
  t24 = 0.1e1 + t14 * t15 / 0.2e1 + t19 * t21 / 0.4e1
  t25 = t24 ** 2
  t27 = t13 / t25
  t28 = 0.1e1 / t15
  t30 = t14 * t28 * t1
  t32 = 0.1e1 / t7 / r0
  t33 = t20 * t32
  t37 = -t19 * t33 / 0.12e2 - t30 * t33 / 0.12e2
  t39 = params.a[0]
  t40 = 0.1e1 / r0
  t44 = params.c[0] * t1
  t45 = t44 * t3
  t47 = jnp.log(t11)
  t48 = t6 * t32 * t47
  t54 = params.d[0] * t1
  t58 = f.my_piecewise3(t12, -t27 * t37, -t39 * t40 / 0.3e1 - t45 * t48 / 0.12e2 - t44 * t33 / 0.12e2 - t54 * t33 / 0.12e2)
  t60 = params.gamma[1]
  t61 = params.beta1[1]
  t65 = params.beta2[1] * t1
  t68 = 0.1e1 + t61 * t15 / 0.2e1 + t65 * t21 / 0.4e1
  t69 = t68 ** 2
  t71 = t60 / t69
  t73 = t61 * t28 * t1
  t77 = -t65 * t33 / 0.12e2 - t73 * t33 / 0.12e2
  t79 = params.a[1]
  t83 = params.c[1] * t1
  t84 = t83 * t3
  t90 = params.d[1] * t1
  t94 = f.my_piecewise3(t12, -t71 * t77, -t79 * t40 / 0.3e1 - t84 * t48 / 0.12e2 - t83 * t33 / 0.12e2 - t90 * t33 / 0.12e2)
  t97 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t99 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t97 * f.p.zeta_threshold, 1)
  t101 = 0.2e1 * t99 - 0.2e1
  t103 = 2 ** (0.1e1 / 0.3e1)
  t106 = 0.1e1 / (0.2e1 * t103 - 0.2e1)
  t112 = t37 ** 2
  t116 = 0.1e1 / t15 / t10
  t118 = t1 ** 2
  t120 = t3 ** 2
  t122 = r0 ** 2
  t123 = t7 ** 2
  t126 = t120 * t5 / t123 / t122
  t130 = 0.1e1 / t7 / t122
  t131 = t20 * t130
  t139 = 0.1e1 / t122
  t143 = t6 * t130 * t47
  t151 = f.my_piecewise3(t12, 0.2e1 * t13 / t25 / t24 * t112 - t27 * (-t14 * t116 * t118 * t126 / 0.18e2 + t30 * t131 / 0.9e1 + t19 * t131 / 0.9e1), t39 * t139 / 0.3e1 + t45 * t143 / 0.9e1 + 0.5e1 / 0.36e2 * t44 * t131 + t54 * t131 / 0.9e1)
  t155 = t77 ** 2
  t178 = f.my_piecewise3(t12, 0.2e1 * t60 / t69 / t68 * t155 - t71 * (-t61 * t116 * t118 * t126 / 0.18e2 + t73 * t131 / 0.9e1 + t65 * t131 / 0.9e1), t79 * t139 / 0.3e1 + t84 * t143 / 0.9e1 + 0.5e1 / 0.36e2 * t83 * t131 + t90 * t131 / 0.9e1)
  v2rho2_0_ = 0.2e1 * t58 + 0.2e1 * (t94 - t58) * t101 * t106 + r0 * (t151 + (t178 - t151) * t101 * t106)
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t7
  t10 = t1 * t3 * t6 * t8
  t11 = t10 / 0.4e1
  t12 = 0.1e1 <= t11
  t13 = params.gamma[0]
  t14 = params.beta1[0]
  t15 = jnp.sqrt(t10)
  t19 = params.beta2[0] * t1
  t20 = t3 * t6
  t21 = t20 * t8
  t24 = 0.1e1 + t14 * t15 / 0.2e1 + t19 * t21 / 0.4e1
  t25 = t24 ** 2
  t28 = t13 / t25 / t24
  t29 = 0.1e1 / t15
  t31 = t14 * t29 * t1
  t34 = t20 / t7 / r0
  t38 = -t19 * t34 / 0.12e2 - t31 * t34 / 0.12e2
  t39 = t38 ** 2
  t43 = t13 / t25
  t45 = 0.1e1 / t15 / t10
  t47 = t1 ** 2
  t48 = t14 * t45 * t47
  t49 = t3 ** 2
  t50 = t49 * t5
  t51 = r0 ** 2
  t52 = t7 ** 2
  t55 = t50 / t52 / t51
  t59 = 0.1e1 / t7 / t51
  t60 = t20 * t59
  t65 = -t48 * t55 / 0.18e2 + t31 * t60 / 0.9e1 + t19 * t60 / 0.9e1
  t68 = params.a[0]
  t69 = 0.1e1 / t51
  t73 = params.c[0] * t1
  t74 = t73 * t3
  t76 = jnp.log(t11)
  t77 = t6 * t59 * t76
  t83 = params.d[0] * t1
  t87 = f.my_piecewise3(t12, 0.2e1 * t28 * t39 - t43 * t65, t68 * t69 / 0.3e1 + t74 * t77 / 0.9e1 + 0.5e1 / 0.36e2 * t73 * t60 + t83 * t60 / 0.9e1)
  t89 = params.gamma[1]
  t90 = params.beta1[1]
  t94 = params.beta2[1] * t1
  t97 = 0.1e1 + t90 * t15 / 0.2e1 + t94 * t21 / 0.4e1
  t98 = t97 ** 2
  t101 = t89 / t98 / t97
  t103 = t90 * t29 * t1
  t107 = -t103 * t34 / 0.12e2 - t94 * t34 / 0.12e2
  t108 = t107 ** 2
  t112 = t89 / t98
  t114 = t90 * t45 * t47
  t121 = -t114 * t55 / 0.18e2 + t103 * t60 / 0.9e1 + t94 * t60 / 0.9e1
  t124 = params.a[1]
  t128 = params.c[1] * t1
  t129 = t128 * t3
  t135 = params.d[1] * t1
  t139 = f.my_piecewise3(t12, 0.2e1 * t101 * t108 - t112 * t121, t124 * t69 / 0.3e1 + t129 * t77 / 0.9e1 + 0.5e1 / 0.36e2 * t128 * t60 + t135 * t60 / 0.9e1)
  t142 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t144 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t142 * f.p.zeta_threshold, 1)
  t146 = 0.2e1 * t144 - 0.2e1
  t148 = 2 ** (0.1e1 / 0.3e1)
  t151 = 0.1e1 / (0.2e1 * t148 - 0.2e1)
  t154 = t25 ** 2
  t169 = 0.1e1 / t15 / t47 / t49 / t5 * t52 / 0.4e1
  t171 = t51 ** 2
  t173 = t2 / t171
  t176 = t51 * r0
  t179 = t50 / t52 / t176
  t183 = 0.1e1 / t7 / t176
  t184 = t20 * t183
  t192 = 0.1e1 / t176
  t196 = t6 * t183 * t76
  t204 = f.my_piecewise3(t12, -0.6e1 * t13 / t154 * t39 * t38 + 0.6e1 * t28 * t38 * t65 - t43 * (-t14 * t169 * t173 / 0.3e1 + 0.2e1 / 0.9e1 * t48 * t179 - 0.7e1 / 0.27e2 * t31 * t184 - 0.7e1 / 0.27e2 * t19 * t184), -0.2e1 / 0.3e1 * t68 * t192 - 0.7e1 / 0.27e2 * t74 * t196 - 0.13e2 / 0.36e2 * t73 * t184 - 0.7e1 / 0.27e2 * t83 * t184)
  t205 = t98 ** 2
  t235 = f.my_piecewise3(t12, -0.6e1 * t89 / t205 * t108 * t107 + 0.6e1 * t101 * t107 * t121 - t112 * (-t90 * t169 * t173 / 0.3e1 + 0.2e1 / 0.9e1 * t114 * t179 - 0.7e1 / 0.27e2 * t103 * t184 - 0.7e1 / 0.27e2 * t94 * t184), -0.2e1 / 0.3e1 * t124 * t192 - 0.7e1 / 0.27e2 * t129 * t196 - 0.13e2 / 0.36e2 * t128 * t184 - 0.7e1 / 0.27e2 * t135 * t184)
  v3rho3_0_ = 0.3e1 * t87 + 0.3e1 * (t139 - t87) * t146 * t151 + r0 * (t204 + (t235 - t204) * t146 * t151)

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t7
  t10 = t1 * t3 * t6 * t8
  t11 = t10 / 0.4e1
  t12 = 0.1e1 <= t11
  t13 = params.gamma[0]
  t14 = params.beta1[0]
  t15 = jnp.sqrt(t10)
  t19 = params.beta2[0] * t1
  t20 = t3 * t6
  t21 = t20 * t8
  t24 = 0.1e1 + t14 * t15 / 0.2e1 + t19 * t21 / 0.4e1
  t25 = t24 ** 2
  t26 = t25 ** 2
  t28 = t13 / t26
  t29 = 0.1e1 / t15
  t31 = t14 * t29 * t1
  t34 = t20 / t7 / r0
  t38 = -t19 * t34 / 0.12e2 - t31 * t34 / 0.12e2
  t39 = t38 ** 2
  t45 = t13 / t25 / t24
  t47 = 0.1e1 / t15 / t10
  t49 = t1 ** 2
  t50 = t14 * t47 * t49
  t51 = t3 ** 2
  t52 = t51 * t5
  t53 = r0 ** 2
  t54 = t7 ** 2
  t57 = t52 / t54 / t53
  t62 = t20 / t7 / t53
  t67 = -t50 * t57 / 0.18e2 + t31 * t62 / 0.9e1 + t19 * t62 / 0.9e1
  t72 = t13 / t25
  t79 = 0.1e1 / t15 / t49 / t51 / t5 * t54 / 0.4e1
  t80 = t14 * t79
  t81 = t53 ** 2
  t82 = 0.1e1 / t81
  t83 = t2 * t82
  t86 = t53 * r0
  t89 = t52 / t54 / t86
  t93 = 0.1e1 / t7 / t86
  t94 = t20 * t93
  t99 = -t80 * t83 / 0.3e1 + 0.2e1 / 0.9e1 * t50 * t89 - 0.7e1 / 0.27e2 * t31 * t94 - 0.7e1 / 0.27e2 * t19 * t94
  t102 = params.a[0]
  t103 = 0.1e1 / t86
  t107 = params.c[0] * t1
  t108 = t107 * t3
  t110 = jnp.log(t11)
  t111 = t6 * t93 * t110
  t117 = params.d[0] * t1
  t121 = f.my_piecewise3(t12, -0.6e1 * t28 * t39 * t38 + 0.6e1 * t45 * t38 * t67 - t72 * t99, -0.2e1 / 0.3e1 * t102 * t103 - 0.7e1 / 0.27e2 * t108 * t111 - 0.13e2 / 0.36e2 * t107 * t94 - 0.7e1 / 0.27e2 * t117 * t94)
  t123 = params.gamma[1]
  t124 = params.beta1[1]
  t128 = params.beta2[1] * t1
  t131 = 0.1e1 + t124 * t15 / 0.2e1 + t128 * t21 / 0.4e1
  t132 = t131 ** 2
  t133 = t132 ** 2
  t135 = t123 / t133
  t137 = t124 * t29 * t1
  t141 = -t128 * t34 / 0.12e2 - t137 * t34 / 0.12e2
  t142 = t141 ** 2
  t148 = t123 / t132 / t131
  t150 = t124 * t47 * t49
  t157 = -t150 * t57 / 0.18e2 + t137 * t62 / 0.9e1 + t128 * t62 / 0.9e1
  t162 = t123 / t132
  t163 = t124 * t79
  t172 = -t163 * t83 / 0.3e1 + 0.2e1 / 0.9e1 * t150 * t89 - 0.7e1 / 0.27e2 * t137 * t94 - 0.7e1 / 0.27e2 * t128 * t94
  t175 = params.a[1]
  t179 = params.c[1] * t1
  t180 = t179 * t3
  t186 = params.d[1] * t1
  t190 = f.my_piecewise3(t12, -0.6e1 * t135 * t142 * t141 + 0.6e1 * t148 * t141 * t157 - t162 * t172, -0.2e1 / 0.3e1 * t175 * t103 - 0.7e1 / 0.27e2 * t180 * t111 - 0.13e2 / 0.36e2 * t179 * t94 - 0.7e1 / 0.27e2 * t186 * t94)
  t193 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t195 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t193 * f.p.zeta_threshold, 1)
  t197 = 0.2e1 * t195 - 0.2e1
  t199 = 2 ** (0.1e1 / 0.3e1)
  t202 = 0.1e1 / (0.2e1 * t199 - 0.2e1)
  t208 = t39 ** 2
  t214 = t67 ** 2
  t224 = 0.1e1 / t15 / t2 * r0 / 0.48e2
  t227 = t81 * r0
  t231 = 0.1e1 / t7 / t227 * t1 * t20
  t235 = t2 / t227
  t240 = t52 / t54 / t81
  t244 = 0.1e1 / t7 / t81
  t245 = t20 * t244
  t256 = t6 * t244 * t110
  t264 = f.my_piecewise3(t12, 0.24e2 * t13 / t26 / t24 * t208 - 0.36e2 * t28 * t39 * t67 + 0.6e1 * t45 * t214 + 0.8e1 * t45 * t38 * t99 - t72 * (-0.5e1 / 0.18e2 * t14 * t224 * t2 * t231 + 0.8e1 / 0.3e1 * t80 * t235 - 0.80e2 / 0.81e2 * t50 * t240 + 0.70e2 / 0.81e2 * t31 * t245 + 0.70e2 / 0.81e2 * t19 * t245), 0.2e1 * t102 * t82 + 0.70e2 / 0.81e2 * t108 * t256 + 0.209e3 / 0.162e3 * t107 * t245 + 0.70e2 / 0.81e2 * t117 * t245)
  t268 = t142 ** 2
  t274 = t157 ** 2
  t304 = f.my_piecewise3(t12, 0.24e2 * t123 / t133 / t131 * t268 - 0.36e2 * t135 * t142 * t157 + 0.6e1 * t148 * t274 + 0.8e1 * t148 * t141 * t172 - t162 * (-0.5e1 / 0.18e2 * t124 * t224 * t2 * t231 + 0.8e1 / 0.3e1 * t163 * t235 - 0.80e2 / 0.81e2 * t150 * t240 + 0.70e2 / 0.81e2 * t137 * t245 + 0.70e2 / 0.81e2 * t128 * t245), 0.2e1 * t175 * t82 + 0.70e2 / 0.81e2 * t180 * t256 + 0.209e3 / 0.162e3 * t179 * t245 + 0.70e2 / 0.81e2 * t186 * t245)
  v4rho4_0_ = 0.4e1 * t121 + 0.4e1 * (t190 - t121) * t197 * t202 + r0 * (t264 + (t304 - t264) * t197 * t202)

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t9 = 0.1e1 / t8
  t10 = t6 * t9
  t11 = t1 * t3 * t10
  t12 = t11 / 0.4e1
  t13 = 0.1e1 <= t12
  t14 = params.gamma[0]
  t15 = params.beta1[0]
  t16 = jnp.sqrt(t11)
  t20 = params.beta2[0] * t1
  t21 = t3 * t6
  t22 = t21 * t9
  t25 = 0.1e1 + t15 * t16 / 0.2e1 + t20 * t22 / 0.4e1
  t26 = t25 ** 2
  t28 = t14 / t26
  t29 = 0.1e1 / t16
  t31 = t15 * t29 * t1
  t33 = 0.1e1 / t8 / t7
  t34 = t21 * t33
  t38 = -t20 * t34 / 0.12e2 - t31 * t34 / 0.12e2
  t40 = params.a[0]
  t41 = 0.1e1 / t7
  t45 = params.c[0] * t1
  t46 = t45 * t3
  t48 = jnp.log(t12)
  t49 = t6 * t33 * t48
  t55 = params.d[0] * t1
  t59 = f.my_piecewise3(t13, -t28 * t38, -t40 * t41 / 0.3e1 - t46 * t49 / 0.12e2 - t45 * t34 / 0.12e2 - t55 * t34 / 0.12e2)
  t60 = 0.2e1 * t59
  t61 = params.gamma[1]
  t62 = params.beta1[1]
  t66 = params.beta2[1] * t1
  t69 = 0.1e1 + t62 * t16 / 0.2e1 + t66 * t22 / 0.4e1
  t70 = t69 ** 2
  t72 = t61 / t70
  t74 = t62 * t29 * t1
  t78 = -t66 * t34 / 0.12e2 - t74 * t34 / 0.12e2
  t80 = params.a[1]
  t84 = params.c[1] * t1
  t85 = t84 * t3
  t91 = params.d[1] * t1
  t95 = f.my_piecewise3(t13, -t72 * t78, -t80 * t41 / 0.3e1 - t85 * t49 / 0.12e2 - t84 * t34 / 0.12e2 - t91 * t34 / 0.12e2)
  t96 = t95 - t59
  t97 = r0 - r1
  t98 = t97 * t41
  t99 = 0.1e1 + t98
  t100 = t99 <= f.p.zeta_threshold
  t101 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t102 = t101 * f.p.zeta_threshold
  t103 = t99 ** (0.1e1 / 0.3e1)
  t105 = f.my_piecewise3(t100, t102, t103 * t99)
  t106 = 0.1e1 - t98
  t107 = t106 <= f.p.zeta_threshold
  t108 = t106 ** (0.1e1 / 0.3e1)
  t110 = f.my_piecewise3(t107, t102, t108 * t106)
  t111 = t105 + t110 - 0.2e1
  t113 = 2 ** (0.1e1 / 0.3e1)
  t116 = 0.1e1 / (0.2e1 * t113 - 0.2e1)
  t118 = 0.2e1 * t96 * t111 * t116
  t123 = t10 * t48
  t129 = f.my_piecewise3(t13, t61 / t69, t80 * t48 + params.b[1] + t85 * t123 / 0.4e1 + t91 * t22 / 0.4e1)
  t139 = f.my_piecewise3(t13, t14 / t25, t40 * t48 + params.b[0] + t46 * t123 / 0.4e1 + t55 * t22 / 0.4e1)
  t140 = t129 - t139
  t141 = t7 ** 2
  t142 = 0.1e1 / t141
  t143 = t97 * t142
  t144 = t41 - t143
  t147 = f.my_piecewise3(t100, 0, 0.4e1 / 0.3e1 * t103 * t144)
  t148 = -t144
  t151 = f.my_piecewise3(t107, 0, 0.4e1 / 0.3e1 * t108 * t148)
  t152 = t147 + t151
  t154 = t140 * t152 * t116
  t159 = t38 ** 2
  t163 = 0.1e1 / t16 / t11
  t165 = t1 ** 2
  t167 = t3 ** 2
  t169 = t8 ** 2
  t172 = t167 * t5 / t169 / t141
  t176 = 0.1e1 / t8 / t141
  t177 = t21 * t176
  t188 = t6 * t176 * t48
  t196 = f.my_piecewise3(t13, 0.2e1 * t14 / t26 / t25 * t159 - t28 * (-t15 * t163 * t165 * t172 / 0.18e2 + t31 * t177 / 0.9e1 + t20 * t177 / 0.9e1), t40 * t142 / 0.3e1 + t46 * t188 / 0.9e1 + 0.5e1 / 0.36e2 * t45 * t177 + t55 * t177 / 0.9e1)
  t200 = t78 ** 2
  t223 = f.my_piecewise3(t13, 0.2e1 * t61 / t70 / t69 * t200 - t72 * (-t62 * t163 * t165 * t172 / 0.18e2 + t74 * t177 / 0.9e1 + t66 * t177 / 0.9e1), t80 * t142 / 0.3e1 + t85 * t188 / 0.9e1 + 0.5e1 / 0.36e2 * t84 * t177 + t91 * t177 / 0.9e1)
  t226 = (t223 - t196) * t111 * t116
  t228 = t96 * t152 * t116
  t230 = t103 ** 2
  t231 = 0.1e1 / t230
  t232 = t144 ** 2
  t236 = 0.1e1 / t141 / t7
  t237 = t97 * t236
  t239 = -0.2e1 * t142 + 0.2e1 * t237
  t243 = f.my_piecewise3(t100, 0, 0.4e1 / 0.9e1 * t231 * t232 + 0.4e1 / 0.3e1 * t103 * t239)
  t244 = t108 ** 2
  t245 = 0.1e1 / t244
  t246 = t148 ** 2
  t253 = f.my_piecewise3(t107, 0, 0.4e1 / 0.9e1 * t245 * t246 - 0.4e1 / 0.3e1 * t108 * t239)
  d11 = t60 + t118 + 0.2e1 * t154 + t7 * (t196 + t226 + 0.2e1 * t228 + t140 * (t243 + t253) * t116)
  t259 = -t41 - t143
  t262 = f.my_piecewise3(t100, 0, 0.4e1 / 0.3e1 * t103 * t259)
  t263 = -t259
  t266 = f.my_piecewise3(t107, 0, 0.4e1 / 0.3e1 * t108 * t263)
  t267 = t262 + t266
  t269 = t140 * t267 * t116
  t271 = t96 * t267 * t116
  t279 = f.my_piecewise3(t100, 0, 0.4e1 / 0.9e1 * t231 * t259 * t144 + 0.8e1 / 0.3e1 * t103 * t97 * t236)
  t287 = f.my_piecewise3(t107, 0, 0.4e1 / 0.9e1 * t245 * t263 * t148 - 0.8e1 / 0.3e1 * t108 * t97 * t236)
  d12 = t60 + t118 + t154 + t269 + t7 * (t196 + t226 + t228 + t271 + t140 * (t279 + t287) * t116)
  t295 = t259 ** 2
  t299 = 0.2e1 * t142 + 0.2e1 * t237
  t303 = f.my_piecewise3(t100, 0, 0.4e1 / 0.9e1 * t231 * t295 + 0.4e1 / 0.3e1 * t103 * t299)
  t304 = t263 ** 2
  t311 = f.my_piecewise3(t107, 0, 0.4e1 / 0.9e1 * t245 * t304 - 0.4e1 / 0.3e1 * t108 * t299)
  d22 = t60 + t118 + 0.2e1 * t269 + t7 * (t196 + t226 + 0.2e1 * t271 + t140 * (t303 + t311) * t116)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t9 = 0.1e1 / t8
  t10 = t6 * t9
  t11 = t1 * t3 * t10
  t12 = t11 / 0.4e1
  t13 = 0.1e1 <= t12
  t14 = params.gamma[0]
  t15 = params.beta1[0]
  t16 = jnp.sqrt(t11)
  t20 = params.beta2[0] * t1
  t21 = t3 * t6
  t22 = t21 * t9
  t25 = 0.1e1 + t15 * t16 / 0.2e1 + t20 * t22 / 0.4e1
  t26 = t25 ** 2
  t29 = t14 / t26 / t25
  t30 = 0.1e1 / t16
  t32 = t15 * t30 * t1
  t34 = 0.1e1 / t8 / t7
  t35 = t21 * t34
  t39 = -t20 * t35 / 0.12e2 - t32 * t35 / 0.12e2
  t40 = t39 ** 2
  t44 = t14 / t26
  t46 = 0.1e1 / t16 / t11
  t48 = t1 ** 2
  t49 = t15 * t46 * t48
  t50 = t3 ** 2
  t51 = t50 * t5
  t52 = t7 ** 2
  t53 = t8 ** 2
  t56 = t51 / t53 / t52
  t60 = 0.1e1 / t8 / t52
  t61 = t21 * t60
  t66 = -t49 * t56 / 0.18e2 + t32 * t61 / 0.9e1 + t20 * t61 / 0.9e1
  t69 = params.a[0]
  t70 = 0.1e1 / t52
  t74 = params.c[0] * t1
  t75 = t74 * t3
  t77 = jnp.log(t12)
  t78 = t6 * t60 * t77
  t84 = params.d[0] * t1
  t88 = f.my_piecewise3(t13, 0.2e1 * t29 * t40 - t44 * t66, t69 * t70 / 0.3e1 + t75 * t78 / 0.9e1 + 0.5e1 / 0.36e2 * t74 * t61 + t84 * t61 / 0.9e1)
  t90 = params.gamma[1]
  t91 = params.beta1[1]
  t95 = params.beta2[1] * t1
  t98 = 0.1e1 + t91 * t16 / 0.2e1 + t95 * t22 / 0.4e1
  t99 = t98 ** 2
  t102 = t90 / t99 / t98
  t104 = t91 * t30 * t1
  t108 = -t104 * t35 / 0.12e2 - t95 * t35 / 0.12e2
  t109 = t108 ** 2
  t113 = t90 / t99
  t115 = t91 * t46 * t48
  t122 = -t115 * t56 / 0.18e2 + t104 * t61 / 0.9e1 + t95 * t61 / 0.9e1
  t125 = params.a[1]
  t129 = params.c[1] * t1
  t130 = t129 * t3
  t136 = params.d[1] * t1
  t140 = f.my_piecewise3(t13, 0.2e1 * t102 * t109 - t113 * t122, t125 * t70 / 0.3e1 + t130 * t78 / 0.9e1 + 0.5e1 / 0.36e2 * t129 * t61 + t136 * t61 / 0.9e1)
  t141 = t140 - t88
  t142 = r0 - r1
  t143 = 0.1e1 / t7
  t144 = t142 * t143
  t145 = 0.1e1 + t144
  t146 = t145 <= f.p.zeta_threshold
  t147 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t148 = t147 * f.p.zeta_threshold
  t149 = t145 ** (0.1e1 / 0.3e1)
  t151 = f.my_piecewise3(t146, t148, t149 * t145)
  t152 = 0.1e1 - t144
  t153 = t152 <= f.p.zeta_threshold
  t154 = t152 ** (0.1e1 / 0.3e1)
  t156 = f.my_piecewise3(t153, t148, t154 * t152)
  t157 = t151 + t156 - 0.2e1
  t159 = 2 ** (0.1e1 / 0.3e1)
  t162 = 0.1e1 / (0.2e1 * t159 - 0.2e1)
  t169 = t6 * t34 * t77
  t177 = f.my_piecewise3(t13, -t113 * t108, -t125 * t143 / 0.3e1 - t130 * t169 / 0.12e2 - t129 * t35 / 0.12e2 - t136 * t35 / 0.12e2)
  t188 = f.my_piecewise3(t13, -t44 * t39, -t69 * t143 / 0.3e1 - t75 * t169 / 0.12e2 - t74 * t35 / 0.12e2 - t84 * t35 / 0.12e2)
  t189 = t177 - t188
  t191 = -t142 * t70 + t143
  t194 = f.my_piecewise3(t146, 0, 0.4e1 / 0.3e1 * t149 * t191)
  t195 = -t191
  t198 = f.my_piecewise3(t153, 0, 0.4e1 / 0.3e1 * t154 * t195)
  t199 = t194 + t198
  t207 = t10 * t77
  t213 = f.my_piecewise3(t13, t90 / t98, t125 * t77 + params.b[1] + t130 * t207 / 0.4e1 + t136 * t22 / 0.4e1)
  t223 = f.my_piecewise3(t13, t14 / t25, t69 * t77 + params.b[0] + t75 * t207 / 0.4e1 + t84 * t22 / 0.4e1)
  t224 = t213 - t223
  t225 = t149 ** 2
  t226 = 0.1e1 / t225
  t227 = t191 ** 2
  t230 = t52 * t7
  t231 = 0.1e1 / t230
  t234 = 0.2e1 * t142 * t231 - 0.2e1 * t70
  t238 = f.my_piecewise3(t146, 0, 0.4e1 / 0.9e1 * t226 * t227 + 0.4e1 / 0.3e1 * t149 * t234)
  t239 = t154 ** 2
  t240 = 0.1e1 / t239
  t241 = t195 ** 2
  t244 = -t234
  t248 = f.my_piecewise3(t153, 0, 0.4e1 / 0.9e1 * t240 * t241 + 0.4e1 / 0.3e1 * t154 * t244)
  t249 = t238 + t248
  t253 = t26 ** 2
  t268 = 0.1e1 / t16 / t48 / t50 / t5 * t53 / 0.4e1
  t270 = t52 ** 2
  t271 = 0.1e1 / t270
  t272 = t2 * t271
  t277 = t51 / t53 / t230
  t281 = 0.1e1 / t8 / t230
  t282 = t21 * t281
  t293 = t6 * t281 * t77
  t301 = f.my_piecewise3(t13, -0.6e1 * t14 / t253 * t40 * t39 + 0.6e1 * t29 * t39 * t66 - t44 * (-t15 * t268 * t272 / 0.3e1 + 0.2e1 / 0.9e1 * t49 * t277 - 0.7e1 / 0.27e2 * t32 * t282 - 0.7e1 / 0.27e2 * t20 * t282), -0.2e1 / 0.3e1 * t69 * t231 - 0.7e1 / 0.27e2 * t75 * t293 - 0.13e2 / 0.36e2 * t74 * t282 - 0.7e1 / 0.27e2 * t84 * t282)
  t302 = t99 ** 2
  t332 = f.my_piecewise3(t13, -0.6e1 * t90 / t302 * t109 * t108 + 0.6e1 * t102 * t108 * t122 - t113 * (-t91 * t268 * t272 / 0.3e1 + 0.2e1 / 0.9e1 * t115 * t277 - 0.7e1 / 0.27e2 * t104 * t282 - 0.7e1 / 0.27e2 * t95 * t282), -0.2e1 / 0.3e1 * t125 * t231 - 0.7e1 / 0.27e2 * t130 * t293 - 0.13e2 / 0.36e2 * t129 * t282 - 0.7e1 / 0.27e2 * t136 * t282)
  t352 = -0.6e1 * t142 * t271 + 0.6e1 * t231
  t356 = f.my_piecewise3(t146, 0, -0.8e1 / 0.27e2 / t225 / t145 * t227 * t191 + 0.4e1 / 0.3e1 * t226 * t191 * t234 + 0.4e1 / 0.3e1 * t149 * t352)
  t369 = f.my_piecewise3(t153, 0, -0.8e1 / 0.27e2 / t239 / t152 * t241 * t195 + 0.4e1 / 0.3e1 * t240 * t195 * t244 - 0.4e1 / 0.3e1 * t154 * t352)
  d111 = 0.3e1 * t88 + 0.3e1 * t141 * t157 * t162 + 0.6e1 * t189 * t199 * t162 + 0.3e1 * t224 * t249 * t162 + t7 * (t301 + (t332 - t301) * t157 * t162 + 0.3e1 * t141 * t199 * t162 + 0.3e1 * t189 * t249 * t162 + t224 * (t356 + t369) * t162)

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t9 = 0.1e1 / t8
  t10 = t6 * t9
  t11 = t1 * t3 * t10
  t12 = t11 / 0.4e1
  t13 = 0.1e1 <= t12
  t14 = params.gamma[0]
  t15 = params.beta1[0]
  t16 = jnp.sqrt(t11)
  t20 = params.beta2[0] * t1
  t21 = t3 * t6
  t22 = t21 * t9
  t25 = 0.1e1 + t15 * t16 / 0.2e1 + t20 * t22 / 0.4e1
  t26 = t25 ** 2
  t27 = t26 ** 2
  t29 = t14 / t27
  t30 = 0.1e1 / t16
  t32 = t15 * t30 * t1
  t34 = 0.1e1 / t8 / t7
  t35 = t21 * t34
  t39 = -t20 * t35 / 0.12e2 - t32 * t35 / 0.12e2
  t40 = t39 ** 2
  t46 = t14 / t26 / t25
  t48 = 0.1e1 / t16 / t11
  t50 = t1 ** 2
  t51 = t15 * t48 * t50
  t52 = t3 ** 2
  t53 = t52 * t5
  t54 = t7 ** 2
  t55 = t8 ** 2
  t58 = t53 / t55 / t54
  t62 = 0.1e1 / t8 / t54
  t63 = t21 * t62
  t68 = -t51 * t58 / 0.18e2 + t32 * t63 / 0.9e1 + t20 * t63 / 0.9e1
  t73 = t14 / t26
  t80 = 0.1e1 / t16 / t50 / t52 / t5 * t55 / 0.4e1
  t81 = t15 * t80
  t82 = t54 ** 2
  t83 = 0.1e1 / t82
  t84 = t2 * t83
  t87 = t54 * t7
  t90 = t53 / t55 / t87
  t94 = 0.1e1 / t8 / t87
  t95 = t21 * t94
  t100 = -t81 * t84 / 0.3e1 + 0.2e1 / 0.9e1 * t51 * t90 - 0.7e1 / 0.27e2 * t32 * t95 - 0.7e1 / 0.27e2 * t20 * t95
  t103 = params.a[0]
  t104 = 0.1e1 / t87
  t108 = params.c[0] * t1
  t109 = t108 * t3
  t111 = jnp.log(t12)
  t112 = t6 * t94 * t111
  t118 = params.d[0] * t1
  t122 = f.my_piecewise3(t13, -0.6e1 * t29 * t40 * t39 + 0.6e1 * t46 * t39 * t68 - t73 * t100, -0.2e1 / 0.3e1 * t103 * t104 - 0.7e1 / 0.27e2 * t109 * t112 - 0.13e2 / 0.36e2 * t108 * t95 - 0.7e1 / 0.27e2 * t118 * t95)
  t124 = params.gamma[1]
  t125 = params.beta1[1]
  t129 = params.beta2[1] * t1
  t132 = 0.1e1 + t125 * t16 / 0.2e1 + t129 * t22 / 0.4e1
  t133 = t132 ** 2
  t134 = t133 ** 2
  t136 = t124 / t134
  t138 = t125 * t30 * t1
  t142 = -t129 * t35 / 0.12e2 - t138 * t35 / 0.12e2
  t143 = t142 ** 2
  t149 = t124 / t133 / t132
  t151 = t125 * t48 * t50
  t158 = -t151 * t58 / 0.18e2 + t138 * t63 / 0.9e1 + t129 * t63 / 0.9e1
  t163 = t124 / t133
  t164 = t125 * t80
  t173 = -t164 * t84 / 0.3e1 + 0.2e1 / 0.9e1 * t151 * t90 - 0.7e1 / 0.27e2 * t138 * t95 - 0.7e1 / 0.27e2 * t129 * t95
  t176 = params.a[1]
  t180 = params.c[1] * t1
  t181 = t180 * t3
  t187 = params.d[1] * t1
  t191 = f.my_piecewise3(t13, -0.6e1 * t136 * t143 * t142 + 0.6e1 * t149 * t142 * t158 - t163 * t173, -0.2e1 / 0.3e1 * t176 * t104 - 0.7e1 / 0.27e2 * t181 * t112 - 0.13e2 / 0.36e2 * t180 * t95 - 0.7e1 / 0.27e2 * t187 * t95)
  t192 = t191 - t122
  t193 = r0 - r1
  t194 = 0.1e1 / t7
  t195 = t193 * t194
  t196 = 0.1e1 + t195
  t197 = t196 <= f.p.zeta_threshold
  t198 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t199 = t198 * f.p.zeta_threshold
  t200 = t196 ** (0.1e1 / 0.3e1)
  t202 = f.my_piecewise3(t197, t199, t200 * t196)
  t203 = 0.1e1 - t195
  t204 = t203 <= f.p.zeta_threshold
  t205 = t203 ** (0.1e1 / 0.3e1)
  t207 = f.my_piecewise3(t204, t199, t205 * t203)
  t208 = t202 + t207 - 0.2e1
  t210 = 2 ** (0.1e1 / 0.3e1)
  t213 = 0.1e1 / (0.2e1 * t210 - 0.2e1)
  t220 = 0.1e1 / t54
  t224 = t6 * t62 * t111
  t232 = f.my_piecewise3(t13, 0.2e1 * t149 * t143 - t163 * t158, t176 * t220 / 0.3e1 + t181 * t224 / 0.9e1 + 0.5e1 / 0.36e2 * t180 * t63 + t187 * t63 / 0.9e1)
  t246 = f.my_piecewise3(t13, 0.2e1 * t46 * t40 - t73 * t68, t103 * t220 / 0.3e1 + t109 * t224 / 0.9e1 + 0.5e1 / 0.36e2 * t108 * t63 + t118 * t63 / 0.9e1)
  t247 = t232 - t246
  t249 = -t193 * t220 + t194
  t252 = f.my_piecewise3(t197, 0, 0.4e1 / 0.3e1 * t200 * t249)
  t253 = -t249
  t256 = f.my_piecewise3(t204, 0, 0.4e1 / 0.3e1 * t205 * t253)
  t257 = t252 + t256
  t265 = t6 * t34 * t111
  t273 = f.my_piecewise3(t13, -t163 * t142, -t176 * t194 / 0.3e1 - t181 * t265 / 0.12e2 - t180 * t35 / 0.12e2 - t187 * t35 / 0.12e2)
  t284 = f.my_piecewise3(t13, -t73 * t39, -t103 * t194 / 0.3e1 - t109 * t265 / 0.12e2 - t108 * t35 / 0.12e2 - t118 * t35 / 0.12e2)
  t285 = t273 - t284
  t286 = t200 ** 2
  t287 = 0.1e1 / t286
  t288 = t249 ** 2
  t293 = 0.2e1 * t193 * t104 - 0.2e1 * t220
  t297 = f.my_piecewise3(t197, 0, 0.4e1 / 0.9e1 * t287 * t288 + 0.4e1 / 0.3e1 * t200 * t293)
  t298 = t205 ** 2
  t299 = 0.1e1 / t298
  t300 = t253 ** 2
  t303 = -t293
  t307 = f.my_piecewise3(t204, 0, 0.4e1 / 0.9e1 * t299 * t300 + 0.4e1 / 0.3e1 * t205 * t303)
  t308 = t297 + t307
  t316 = t10 * t111
  t322 = f.my_piecewise3(t13, t124 / t132, t176 * t111 + params.b[1] + t181 * t316 / 0.4e1 + t187 * t22 / 0.4e1)
  t332 = f.my_piecewise3(t13, t14 / t25, t103 * t111 + params.b[0] + t109 * t316 / 0.4e1 + t118 * t22 / 0.4e1)
  t333 = t322 - t332
  t335 = 0.1e1 / t286 / t196
  t339 = t287 * t249
  t344 = -0.6e1 * t193 * t83 + 0.6e1 * t104
  t348 = f.my_piecewise3(t197, 0, -0.8e1 / 0.27e2 * t335 * t288 * t249 + 0.4e1 / 0.3e1 * t339 * t293 + 0.4e1 / 0.3e1 * t200 * t344)
  t350 = 0.1e1 / t298 / t203
  t354 = t299 * t253
  t357 = -t344
  t361 = f.my_piecewise3(t204, 0, -0.8e1 / 0.27e2 * t350 * t300 * t253 + 0.4e1 / 0.3e1 * t354 * t303 + 0.4e1 / 0.3e1 * t205 * t357)
  t362 = t348 + t361
  t369 = t40 ** 2
  t375 = t68 ** 2
  t384 = 0.1e1 / t16 / t2 / t194 / 0.48e2
  t387 = t82 * t7
  t391 = 0.1e1 / t8 / t387 * t1 * t21
  t394 = 0.1e1 / t387
  t395 = t2 * t394
  t400 = t53 / t55 / t82
  t404 = 0.1e1 / t8 / t82
  t405 = t21 * t404
  t416 = t6 * t404 * t111
  t424 = f.my_piecewise3(t13, 0.24e2 * t14 / t27 / t25 * t369 - 0.36e2 * t29 * t40 * t68 + 0.6e1 * t46 * t375 + 0.8e1 * t46 * t39 * t100 - t73 * (-0.5e1 / 0.18e2 * t15 * t384 * t2 * t391 + 0.8e1 / 0.3e1 * t81 * t395 - 0.80e2 / 0.81e2 * t51 * t400 + 0.70e2 / 0.81e2 * t32 * t405 + 0.70e2 / 0.81e2 * t20 * t405), 0.2e1 * t103 * t83 + 0.70e2 / 0.81e2 * t109 * t416 + 0.209e3 / 0.162e3 * t108 * t405 + 0.70e2 / 0.81e2 * t118 * t405)
  t428 = t143 ** 2
  t434 = t158 ** 2
  t464 = f.my_piecewise3(t13, 0.24e2 * t124 / t134 / t132 * t428 - 0.36e2 * t136 * t143 * t158 + 0.6e1 * t149 * t434 + 0.8e1 * t149 * t142 * t173 - t163 * (-0.5e1 / 0.18e2 * t125 * t384 * t2 * t391 + 0.8e1 / 0.3e1 * t164 * t395 - 0.80e2 / 0.81e2 * t151 * t400 + 0.70e2 / 0.81e2 * t138 * t405 + 0.70e2 / 0.81e2 * t129 * t405), 0.2e1 * t176 * t83 + 0.70e2 / 0.81e2 * t181 * t416 + 0.209e3 / 0.162e3 * t180 * t405 + 0.70e2 / 0.81e2 * t187 * t405)
  t477 = t196 ** 2
  t480 = t288 ** 2
  t486 = t293 ** 2
  t493 = 0.24e2 * t193 * t394 - 0.24e2 * t83
  t497 = f.my_piecewise3(t197, 0, 0.40e2 / 0.81e2 / t286 / t477 * t480 - 0.16e2 / 0.9e1 * t335 * t288 * t293 + 0.4e1 / 0.3e1 * t287 * t486 + 0.16e2 / 0.9e1 * t339 * t344 + 0.4e1 / 0.3e1 * t200 * t493)
  t498 = t203 ** 2
  t501 = t300 ** 2
  t507 = t303 ** 2
  t516 = f.my_piecewise3(t204, 0, 0.40e2 / 0.81e2 / t298 / t498 * t501 - 0.16e2 / 0.9e1 * t350 * t300 * t303 + 0.4e1 / 0.3e1 * t299 * t507 + 0.16e2 / 0.9e1 * t354 * t357 - 0.4e1 / 0.3e1 * t205 * t493)
  d1111 = 0.4e1 * t122 + 0.4e1 * t192 * t208 * t213 + 0.12e2 * t247 * t257 * t213 + 0.12e2 * t285 * t308 * t213 + 0.4e1 * t333 * t362 * t213 + t7 * (t424 + (t464 - t424) * t208 * t213 + 0.4e1 * t192 * t257 * t213 + 0.6e1 * t247 * t308 * t213 + 0.4e1 * t285 * t362 * t213 + t333 * (t497 + t516) * t213)

  res = {'v4rho4': d1111}
  return res