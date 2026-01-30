"""Generated from lda_x_sloc.mpl."""

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

  f_sloc = lambda rs, z: -params_a / (2 * (params_b + 1)) * f.n_total(rs) ** params_b * (f.opz_pow_n(z, params_b + 1) + f.opz_pow_n(-z, params_b + 1))

  functional_body = lambda rs, z: f_sloc(rs, z)

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

  f_sloc = lambda rs, z: -params_a / (2 * (params_b + 1)) * f.n_total(rs) ** params_b * (f.opz_pow_n(z, params_b + 1) + f.opz_pow_n(-z, params_b + 1))

  functional_body = lambda rs, z: f_sloc(rs, z)

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

  f_sloc = lambda rs, z: -params_a / (2 * (params_b + 1)) * f.n_total(rs) ** params_b * (f.opz_pow_n(z, params_b + 1) + f.opz_pow_n(-z, params_b + 1))

  functional_body = lambda rs, z: f_sloc(rs, z)

  t1 = params.b + 0.1e1
  t3 = 0.1e1 / t1 / 0.2e1
  t4 = params.a * t3
  t5 = r0 + r1
  t6 = t5 ** params.b
  t7 = r0 - r1
  t8 = 0.1e1 / t5
  t9 = t7 * t8
  t10 = 0.1e1 + t9
  t11 = t10 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold ** t1
  t13 = t10 ** t1
  t14 = f.my_piecewise3(t11, t12, t13)
  t15 = 0.1e1 - t9
  t16 = t15 <= f.p.zeta_threshold
  t17 = t15 ** t1
  t18 = f.my_piecewise3(t16, t12, t17)
  t19 = t14 + t18
  t21 = t4 * t6 * t19
  t24 = t4 * t6 * params.b * t19
  t25 = t5 * params.a
  t26 = t3 * t6
  t27 = t13 * t1
  t28 = t5 ** 2
  t30 = t7 / t28
  t31 = t8 - t30
  t32 = 0.1e1 / t10
  t35 = f.my_piecewise3(t11, 0, t27 * t31 * t32)
  t36 = t17 * t1
  t38 = 0.1e1 / t15
  t41 = f.my_piecewise3(t16, 0, -t36 * t31 * t38)
  vrho_0_ = -t21 - t24 - t25 * t26 * (t35 + t41)
  t45 = -t8 - t30
  t48 = f.my_piecewise3(t11, 0, t27 * t45 * t32)
  t52 = f.my_piecewise3(t16, 0, -t36 * t45 * t38)
  vrho_1_ = -t21 - t24 - t25 * t26 * (t48 + t52)
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

  f_sloc = lambda rs, z: -params_a / (2 * (params_b + 1)) * f.n_total(rs) ** params_b * (f.opz_pow_n(z, params_b + 1) + f.opz_pow_n(-z, params_b + 1))

  functional_body = lambda rs, z: f_sloc(rs, z)

  t1 = params.b + 0.1e1
  t4 = params.a / t1 / 0.2e1
  t5 = r0 ** params.b
  t7 = f.p.zeta_threshold ** t1
  t8 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t7, 1)
  vrho_0_ = -0.2e1 * t4 * t5 * params.b * t8 - 0.2e1 * t4 * t5 * t8
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = params.b + 0.1e1
  t5 = r0 ** params.b
  t6 = params.a / t1 * t5 / 0.2e1
  t7 = 0.1e1 / r0
  t10 = f.p.zeta_threshold ** t1
  t11 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t10, 1)
  t14 = params.b ** 2
  v2rho2_0_ = -0.2e1 * t6 * t14 * t7 * t11 - 0.2e1 * t6 * params.b * t7 * t11
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.b + 0.1e1
  t5 = r0 ** params.b
  t6 = params.a / t1 * t5 / 0.2e1
  t7 = r0 ** 2
  t8 = 0.1e1 / t7
  t11 = f.p.zeta_threshold ** t1
  t12 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t11, 1)
  t15 = params.b ** 2
  v3rho3_0_ = -0.2e1 * t6 * t15 * params.b * t8 * t12 + 0.2e1 * t6 * params.b * t8 * t12

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.b + 0.1e1
  t5 = r0 ** params.b
  t6 = params.a / t1 * t5 / 0.2e1
  t7 = params.b ** 2
  t8 = r0 ** 2
  t10 = 0.1e1 / t8 / r0
  t13 = f.p.zeta_threshold ** t1
  t14 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t13, 1)
  t22 = t7 ** 2
  v4rho4_0_ = 0.4e1 * t6 * t7 * params.b * t10 * t14 - 0.2e1 * t6 * t22 * t10 * t14 + 0.2e1 * t6 * t7 * t10 * t14 - 0.4e1 * t6 * params.b * t10 * t14

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = params.b + 0.1e1
  t3 = 0.1e1 / t1 / 0.2e1
  t4 = params.a * t3
  t5 = r0 + r1
  t6 = t5 ** params.b
  t7 = t4 * t6
  t8 = 0.1e1 / t5
  t10 = r0 - r1
  t11 = t10 * t8
  t12 = 0.1e1 + t11
  t13 = t12 <= f.p.zeta_threshold
  t14 = f.p.zeta_threshold ** t1
  t15 = t12 ** t1
  t16 = f.my_piecewise3(t13, t14, t15)
  t17 = 0.1e1 - t11
  t18 = t17 <= f.p.zeta_threshold
  t19 = t17 ** t1
  t20 = f.my_piecewise3(t18, t14, t19)
  t21 = t16 + t20
  t23 = t7 * params.b * t8 * t21
  t24 = t15 * t1
  t25 = t5 ** 2
  t26 = 0.1e1 / t25
  t27 = t10 * t26
  t28 = t8 - t27
  t29 = 0.1e1 / t12
  t32 = f.my_piecewise3(t13, 0, t24 * t28 * t29)
  t33 = t19 * t1
  t34 = -t28
  t35 = 0.1e1 / t17
  t38 = f.my_piecewise3(t18, 0, t33 * t34 * t35)
  t39 = t32 + t38
  t41 = t4 * t6 * t39
  t43 = params.b ** 2
  t46 = t7 * t43 * t8 * t21
  t47 = t6 * params.b
  t49 = t4 * t47 * t39
  t51 = t5 * params.a
  t52 = t3 * t6
  t53 = t1 ** 2
  t54 = t15 * t53
  t55 = t28 ** 2
  t56 = t12 ** 2
  t57 = 0.1e1 / t56
  t58 = t55 * t57
  t62 = t10 / t25 / t5
  t64 = -0.2e1 * t26 + 0.2e1 * t62
  t69 = f.my_piecewise3(t13, 0, t24 * t64 * t29 - t24 * t58 + t54 * t58)
  t70 = t19 * t53
  t71 = t34 ** 2
  t72 = t17 ** 2
  t73 = 0.1e1 / t72
  t74 = t71 * t73
  t81 = f.my_piecewise3(t18, 0, -t33 * t64 * t35 - t33 * t74 + t70 * t74)
  d11 = -t23 - 0.2e1 * t41 - t46 - 0.2e1 * t49 - t51 * t52 * (t69 + t81)
  t85 = -t8 - t27
  t88 = f.my_piecewise3(t13, 0, t24 * t85 * t29)
  t89 = -t85
  t92 = f.my_piecewise3(t18, 0, t33 * t89 * t35)
  t93 = t88 + t92
  t95 = t4 * t6 * t93
  t97 = t4 * t47 * t93
  t99 = t28 * t57 * t85
  t106 = f.my_piecewise3(t13, 0, 0.2e1 * t24 * t62 * t29 - t24 * t99 + t54 * t99)
  t108 = t34 * t73 * t89
  t115 = f.my_piecewise3(t18, 0, -0.2e1 * t33 * t62 * t35 - t33 * t108 + t70 * t108)
  d12 = -t23 - t41 - t46 - t49 - t95 - t97 - t51 * t52 * (t106 + t115)
  t121 = t85 ** 2
  t122 = t121 * t57
  t125 = 0.2e1 * t26 + 0.2e1 * t62
  t130 = f.my_piecewise3(t13, 0, t24 * t125 * t29 - t24 * t122 + t54 * t122)
  t131 = t89 ** 2
  t132 = t131 * t73
  t139 = f.my_piecewise3(t18, 0, -t33 * t125 * t35 - t33 * t132 + t70 * t132)
  d22 = -t23 - 0.2e1 * t95 - t46 - 0.2e1 * t97 - t51 * t52 * (t130 + t139)
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = params.b + 0.1e1
  t3 = 0.1e1 / t1 / 0.2e1
  t4 = params.a * t3
  t5 = r0 + r1
  t6 = t5 ** params.b
  t7 = t4 * t6
  t8 = t5 ** 2
  t9 = 0.1e1 / t8
  t11 = r0 - r1
  t12 = 0.1e1 / t5
  t13 = t11 * t12
  t14 = 0.1e1 + t13
  t15 = t14 <= f.p.zeta_threshold
  t16 = f.p.zeta_threshold ** t1
  t17 = t14 ** t1
  t18 = f.my_piecewise3(t15, t16, t17)
  t19 = 0.1e1 - t13
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** t1
  t22 = f.my_piecewise3(t20, t16, t21)
  t23 = t18 + t22
  t27 = t17 * t1
  t29 = -t11 * t9 + t12
  t30 = 0.1e1 / t14
  t33 = f.my_piecewise3(t15, 0, t27 * t29 * t30)
  t34 = t21 * t1
  t35 = -t29
  t36 = 0.1e1 / t19
  t39 = f.my_piecewise3(t20, 0, t34 * t35 * t36)
  t40 = t33 + t39
  t44 = t1 ** 2
  t45 = t17 * t44
  t46 = t29 ** 2
  t47 = t14 ** 2
  t48 = 0.1e1 / t47
  t49 = t46 * t48
  t52 = 0.1e1 / t8 / t5
  t55 = 0.2e1 * t11 * t52 - 0.2e1 * t9
  t60 = f.my_piecewise3(t15, 0, t27 * t55 * t30 - t27 * t49 + t45 * t49)
  t61 = t21 * t44
  t62 = t35 ** 2
  t63 = t19 ** 2
  t64 = 0.1e1 / t63
  t65 = t62 * t64
  t67 = -t55
  t72 = f.my_piecewise3(t20, 0, t34 * t67 * t36 - t34 * t65 + t61 * t65)
  t73 = t60 + t72
  t77 = params.b ** 2
  t92 = t44 * t1
  t97 = t46 * t29 / t47 / t14
  t100 = t29 * t48 * t55
  t105 = t8 ** 2
  t109 = 0.6e1 * t52 - 0.6e1 * t11 / t105
  t117 = f.my_piecewise3(t15, 0, t27 * t109 * t30 + t17 * t92 * t97 - 0.3e1 * t27 * t100 + 0.3e1 * t45 * t100 + 0.2e1 * t27 * t97 - 0.3e1 * t45 * t97)
  t122 = t62 * t35 / t63 / t19
  t125 = t35 * t64 * t67
  t138 = f.my_piecewise3(t20, 0, -t34 * t109 * t36 + t21 * t92 * t122 + 0.2e1 * t34 * t122 - 0.3e1 * t61 * t122 - 0.3e1 * t34 * t125 + 0.3e1 * t61 * t125)
  d111 = t7 * params.b * t9 * t23 - 0.3e1 * t7 * params.b * t12 * t40 - 0.3e1 * t4 * t6 * t73 - t7 * t77 * params.b * t9 * t23 - 0.3e1 * t7 * t77 * t12 * t40 - 0.3e1 * t4 * t6 * params.b * t73 - t5 * params.a * t3 * t6 * (t117 + t138)

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = params.b + 0.1e1
  t3 = 0.1e1 / t1 / 0.2e1
  t4 = params.a * t3
  t5 = r0 + r1
  t6 = t5 ** params.b
  t7 = t4 * t6
  t8 = params.b ** 2
  t9 = t5 ** 2
  t11 = 0.1e1 / t9 / t5
  t13 = r0 - r1
  t14 = 0.1e1 / t5
  t15 = t13 * t14
  t16 = 0.1e1 + t15
  t17 = t16 <= f.p.zeta_threshold
  t18 = f.p.zeta_threshold ** t1
  t19 = t16 ** t1
  t20 = f.my_piecewise3(t17, t18, t19)
  t21 = 0.1e1 - t15
  t22 = t21 <= f.p.zeta_threshold
  t23 = t21 ** t1
  t24 = f.my_piecewise3(t22, t18, t23)
  t25 = t20 + t24
  t32 = 0.1e1 / t9
  t34 = t19 * t1
  t36 = -t13 * t32 + t14
  t37 = 0.1e1 / t16
  t40 = f.my_piecewise3(t17, 0, t34 * t36 * t37)
  t41 = t23 * t1
  t42 = -t36
  t43 = 0.1e1 / t21
  t46 = f.my_piecewise3(t22, 0, t41 * t42 * t43)
  t47 = t40 + t46
  t52 = t1 ** 2
  t53 = t19 * t52
  t54 = t36 ** 2
  t55 = t16 ** 2
  t56 = 0.1e1 / t55
  t57 = t54 * t56
  t61 = 0.2e1 * t13 * t11 - 0.2e1 * t32
  t66 = f.my_piecewise3(t17, 0, t34 * t61 * t37 - t34 * t57 + t53 * t57)
  t67 = t23 * t52
  t68 = t42 ** 2
  t69 = t21 ** 2
  t70 = 0.1e1 / t69
  t71 = t68 * t70
  t73 = -t61
  t78 = f.my_piecewise3(t22, 0, t41 * t73 * t43 - t41 * t71 + t67 * t71)
  t79 = t66 + t78
  t83 = t52 * t1
  t84 = t19 * t83
  t87 = 0.1e1 / t55 / t16
  t88 = t54 * t36 * t87
  t90 = t36 * t56
  t91 = t90 * t61
  t96 = t9 ** 2
  t97 = 0.1e1 / t96
  t100 = -0.6e1 * t13 * t97 + 0.6e1 * t11
  t108 = f.my_piecewise3(t17, 0, t34 * t100 * t37 + 0.2e1 * t34 * t88 - 0.3e1 * t34 * t91 - 0.3e1 * t53 * t88 + 0.3e1 * t53 * t91 + t84 * t88)
  t109 = t23 * t83
  t112 = 0.1e1 / t69 / t21
  t113 = t68 * t42 * t112
  t115 = t42 * t70
  t116 = t115 * t73
  t121 = -t100
  t129 = f.my_piecewise3(t22, 0, t41 * t121 * t43 + t109 * t113 + 0.2e1 * t41 * t113 - 0.3e1 * t67 * t113 - 0.3e1 * t41 * t116 + 0.3e1 * t67 * t116)
  t130 = t108 + t129
  t134 = t8 ** 2
  t138 = t8 * params.b
  t157 = t52 ** 2
  t159 = t54 ** 2
  t160 = t55 ** 2
  t162 = t159 / t160
  t165 = t54 * t87 * t61
  t170 = t61 ** 2
  t171 = t170 * t56
  t176 = t90 * t100
  t185 = -0.24e2 * t97 + 0.24e2 * t13 / t96 / t5
  t196 = t19 * t157 * t162 + t34 * t185 * t37 - 0.6e1 * t34 * t162 + 0.11e2 * t53 * t162 - 0.6e1 * t84 * t162 + 0.12e2 * t34 * t165 - 0.18e2 * t53 * t165 + 0.6e1 * t84 * t165 - 0.3e1 * t34 * t171 + 0.3e1 * t53 * t171 - 0.4e1 * t34 * t176 + 0.4e1 * t53 * t176
  t197 = f.my_piecewise3(t17, 0, t196)
  t199 = t68 ** 2
  t200 = t69 ** 2
  t202 = t199 / t200
  t205 = t68 * t112 * t73
  t210 = t73 ** 2
  t211 = t210 * t70
  t216 = t115 * t121
  t232 = t23 * t157 * t202 - t41 * t185 * t43 - 0.6e1 * t109 * t202 + 0.6e1 * t109 * t205 - 0.6e1 * t41 * t202 + 0.11e2 * t67 * t202 + 0.12e2 * t41 * t205 - 0.18e2 * t67 * t205 - 0.3e1 * t41 * t211 + 0.3e1 * t67 * t211 - 0.4e1 * t41 * t216 + 0.4e1 * t67 * t216
  t233 = f.my_piecewise3(t22, 0, t232)
  d1111 = t7 * t8 * t11 * t25 - 0.2e1 * t7 * params.b * t11 * t25 + 0.4e1 * t7 * params.b * t32 * t47 - 0.6e1 * t7 * params.b * t14 * t79 - 0.4e1 * t4 * t6 * t130 - t7 * t134 * t11 * t25 + 0.2e1 * t7 * t138 * t11 * t25 - 0.4e1 * t7 * t138 * t32 * t47 - 0.6e1 * t7 * t8 * t14 * t79 - 0.4e1 * t4 * t6 * params.b * t130 - t5 * params.a * t3 * t6 * (t197 + t233)

  res = {'v4rho4': d1111}
  return res
