"""Generated from gga_c_wi.mpl."""

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
  params_k_raw = params.k
  if isinstance(params_k_raw, (str, bytes, dict)):
    params_k = params_k_raw
  else:
    try:
      params_k_seq = list(params_k_raw)
    except TypeError:
      params_k = params_k_raw
    else:
      params_k_seq = np.asarray(params_k_seq, dtype=np.float64)
      params_k = np.concatenate((np.array([np.nan], dtype=np.float64), params_k_seq))

  f_num = lambda xt: params_a + params_b * xt ** 2 * jnp.exp(-params_k * xt ** 2)

  f_den = lambda rs, xt: params_c + rs * (1 + params_d * (4 * jnp.pi / 3) ** (1 / 3) * xt ** (7 / 2))

  functional_body = lambda rs, zeta, xt, xs0=None, xs1=None: f_num(xt) / f_den(rs, xt)

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
  params_k_raw = params.k
  if isinstance(params_k_raw, (str, bytes, dict)):
    params_k = params_k_raw
  else:
    try:
      params_k_seq = list(params_k_raw)
    except TypeError:
      params_k = params_k_raw
    else:
      params_k_seq = np.asarray(params_k_seq, dtype=np.float64)
      params_k = np.concatenate((np.array([np.nan], dtype=np.float64), params_k_seq))

  f_num = lambda xt: params_a + params_b * xt ** 2 * jnp.exp(-params_k * xt ** 2)

  f_den = lambda rs, xt: params_c + rs * (1 + params_d * (4 * jnp.pi / 3) ** (1 / 3) * xt ** (7 / 2))

  functional_body = lambda rs, zeta, xt, xs0=None, xs1=None: f_num(xt) / f_den(rs, xt)

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
  params_k_raw = params.k
  if isinstance(params_k_raw, (str, bytes, dict)):
    params_k = params_k_raw
  else:
    try:
      params_k_seq = list(params_k_raw)
    except TypeError:
      params_k = params_k_raw
    else:
      params_k_seq = np.asarray(params_k_seq, dtype=np.float64)
      params_k = np.concatenate((np.array([np.nan], dtype=np.float64), params_k_seq))

  f_num = lambda xt: params_a + params_b * xt ** 2 * jnp.exp(-params_k * xt ** 2)

  f_den = lambda rs, xt: params_c + rs * (1 + params_d * (4 * jnp.pi / 3) ** (1 / 3) * xt ** (7 / 2))

  functional_body = lambda rs, zeta, xt, xs0=None, xs1=None: f_num(xt) / f_den(rs, xt)

  t2 = s0 + 0.2e1 * s1 + s2
  t3 = params.b * t2
  t4 = r0 + r1
  t5 = t4 ** 2
  t6 = t4 ** (0.1e1 / 0.3e1)
  t7 = t6 ** 2
  t9 = 0.1e1 / t7 / t5
  t12 = jnp.exp(-params.k * t2 * t9)
  t15 = t3 * t9 * t12 + params.a
  t16 = 3 ** (0.1e1 / 0.3e1)
  t18 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t19 = t16 * t18
  t20 = 4 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t25 = t16 ** 2
  t26 = jnp.pi ** (0.1e1 / 0.3e1)
  t28 = jnp.sqrt(t2)
  t30 = t5 ** 2
  t34 = 0.1e1 / t6 / t4
  t36 = jnp.sqrt(t28 * t34)
  t41 = 0.1e1 + params.d * t20 * t25 * t26 * t36 * t28 * t2 / t30 / 0.3e1
  t45 = params.c + t19 * t21 / t6 * t41 / 0.4e1
  t46 = 0.1e1 / t45
  t53 = t2 ** 2
  t66 = t45 ** 2
  t67 = 0.1e1 / t66
  t75 = t36 * t2 * t9
  vrho_0_ = t15 * t46 + t4 * (-0.8e1 / 0.3e1 * t3 / t7 / t5 / t4 * t12 + 0.8e1 / 0.3e1 * params.b * t53 / t6 / t30 / t5 * params.k * t12) * t46 - t4 * t15 * t67 * (-t19 * t21 * t34 * t41 / 0.12e2 - 0.14e2 / 0.3e1 * t18 * t9 * params.d * t26 * t75 * t28)
  vrho_1_ = vrho_0_
  t91 = params.b * t9 * t12 - t3 / t6 / t30 / t4 * params.k * t12
  t102 = 0.1e1 / t7 * t15 * t67 * t18 * params.d * t26 * t75 / t28
  vsigma_0_ = t4 * t91 * t46 - 0.7e1 / 0.4e1 * t102
  vsigma_1_ = 0.2e1 * t4 * t91 * t46 - 0.7e1 / 0.2e1 * t102
  vsigma_2_ = vsigma_0_
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
  params_k_raw = params.k
  if isinstance(params_k_raw, (str, bytes, dict)):
    params_k = params_k_raw
  else:
    try:
      params_k_seq = list(params_k_raw)
    except TypeError:
      params_k = params_k_raw
    else:
      params_k_seq = np.asarray(params_k_seq, dtype=np.float64)
      params_k = np.concatenate((np.array([np.nan], dtype=np.float64), params_k_seq))

  f_num = lambda xt: params_a + params_b * xt ** 2 * jnp.exp(-params_k * xt ** 2)

  f_den = lambda rs, xt: params_c + rs * (1 + params_d * (4 * jnp.pi / 3) ** (1 / 3) * xt ** (7 / 2))

  functional_body = lambda rs, zeta, xt, xs0=None, xs1=None: f_num(xt) / f_den(rs, xt)

  t1 = params.b * s0
  t2 = r0 ** 2
  t3 = r0 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t6 = 0.1e1 / t4 / t2
  t9 = jnp.exp(-params.k * s0 * t6)
  t12 = t1 * t6 * t9 + params.a
  t13 = 3 ** (0.1e1 / 0.3e1)
  t15 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t16 = t13 * t15
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t22 = t13 ** 2
  t23 = jnp.pi ** (0.1e1 / 0.3e1)
  t25 = jnp.sqrt(s0)
  t27 = t2 ** 2
  t31 = 0.1e1 / t3 / r0
  t33 = jnp.sqrt(t25 * t31)
  t38 = 0.1e1 + params.d * t17 * t22 * t23 * t33 * t25 * s0 / t27 / 0.3e1
  t42 = params.c + t16 * t18 / t3 * t38 / 0.4e1
  t43 = 0.1e1 / t42
  t50 = s0 ** 2
  t63 = t42 ** 2
  t64 = 0.1e1 / t63
  t72 = t33 * s0 * t6
  vrho_0_ = t12 * t43 + r0 * (-0.8e1 / 0.3e1 * t1 / t4 / t2 / r0 * t9 + 0.8e1 / 0.3e1 * params.b * t50 / t3 / t27 / t2 * params.k * t9) * t43 - r0 * t12 * t64 * (-t16 * t18 * t31 * t38 / 0.12e2 - 0.14e2 / 0.3e1 * t15 * t6 * params.d * t23 * t72 * t25)
  vsigma_0_ = r0 * (params.b * t6 * t9 - t1 / t3 / t27 / r0 * params.k * t9) * t43 - 0.7e1 / 0.4e1 / t4 * t12 * t64 * t15 * params.d * t23 * t72 / t25
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = params.b * s0
  t2 = r0 ** 2
  t3 = t2 * r0
  t4 = r0 ** (0.1e1 / 0.3e1)
  t5 = t4 ** 2
  t7 = 0.1e1 / t5 / t3
  t8 = params.k * s0
  t10 = 0.1e1 / t5 / t2
  t12 = jnp.exp(-t8 * t10)
  t15 = s0 ** 2
  t16 = params.b * t15
  t17 = t2 ** 2
  t20 = 0.1e1 / t4 / t17 / t2
  t25 = 0.8e1 / 0.3e1 * t16 * t20 * params.k * t12 - 0.8e1 / 0.3e1 * t1 * t7 * t12
  t26 = 3 ** (0.1e1 / 0.3e1)
  t28 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t29 = t26 * t28
  t30 = 4 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t35 = t26 ** 2
  t36 = jnp.pi ** (0.1e1 / 0.3e1)
  t38 = jnp.sqrt(s0)
  t39 = t38 * s0
  t43 = 0.1e1 / t4 / r0
  t44 = t38 * t43
  t45 = jnp.sqrt(t44)
  t50 = 0.1e1 + params.d * t30 * t35 * t36 * t45 * t39 / t17 / 0.3e1
  t54 = params.c + t29 * t31 / t4 * t50 / 0.4e1
  t55 = 0.1e1 / t54
  t60 = t1 * t10 * t12 + params.a
  t61 = t54 ** 2
  t62 = 0.1e1 / t61
  t71 = t45 * s0 * t10
  t73 = t36 * t71 * t38
  t76 = -t29 * t31 * t43 * t50 / 0.12e2 - 0.14e2 / 0.3e1 * t28 * t10 * params.d * t73
  t93 = t17 ** 2
  t96 = params.k ** 2
  t105 = t62 * t76
  t108 = r0 * t60
  t110 = 0.1e1 / t61 / t54
  t111 = t76 ** 2
  t125 = t17 * r0
  t129 = t45 * t44
  t130 = t36 * t129
  v2rho2_0_ = 0.2e1 * t25 * t55 - 0.2e1 * t60 * t62 * t76 + r0 * (0.88e2 / 0.9e1 * t1 / t5 / t17 * t12 - 0.24e2 * t16 / t4 / t17 / t3 * params.k * t12 + 0.64e2 / 0.9e1 * params.b * t15 * s0 / t93 / t2 * t96 * t12) * t55 - 0.2e1 * r0 * t25 * t105 + 0.2e1 * t108 * t110 * t111 - t108 * t62 * (t29 * t31 / t4 / t2 * t50 / 0.9e1 + 0.14e2 * t28 * t7 * params.d * t73 + 0.140e3 / 0.9e1 * t28 / t125 * params.d * t130 * s0)
  t140 = 0.1e1 / t4 / t125
  t144 = -t1 * t140 * params.k * t12 + params.b * t10 * t12
  t154 = 0.1e1 / t93 / r0
  t167 = t62 * t28
  t169 = params.d * t36
  t171 = t71 / t38
  t172 = t169 * t171
  t175 = 0.1e1 / t5
  t180 = t175 * t60
  v2rhosigma_0_ = t144 * t55 + r0 * (-0.8e1 / 0.3e1 * params.b * t7 * t12 + 0.8e1 * params.b * t20 * t8 * t12 - 0.8e1 / 0.3e1 * t16 * t154 * t96 * t12) * t55 - r0 * t144 * t105 + 0.7e1 / 0.6e1 / t5 / r0 * t60 * t167 * t172 - 0.7e1 / 0.4e1 * t175 * t25 * t167 * t172 + 0.7e1 / 0.2e1 * t180 * t110 * t28 * t169 * t171 * t76 + 0.35e2 / 0.6e1 / t3 * t60 * t62 * t28 * params.d * t130
  t211 = t28 ** 2
  t212 = params.d ** 2
  t214 = t36 ** 2
  v2sigma2_0_ = r0 * (-0.2e1 * params.b * t140 * params.k * t12 + t1 / t93 * t96 * t12) * t55 - 0.7e1 / 0.2e1 * t175 * t144 * t167 * t172 + 0.49e2 / 0.8e1 * t154 * t60 * t110 * t211 * t212 * t214 * t39 - 0.35e2 / 0.16e2 / t2 * t60 * t167 * t169 * t129 / s0 + 0.7e1 / 0.8e1 * t180 * t167 * t169 * t71 / t39
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.b * s0
  t2 = r0 ** 2
  t3 = t2 ** 2
  t4 = r0 ** (0.1e1 / 0.3e1)
  t5 = t4 ** 2
  t7 = 0.1e1 / t5 / t3
  t10 = 0.1e1 / t5 / t2
  t12 = jnp.exp(-params.k * s0 * t10)
  t16 = s0 ** 2
  t17 = params.b * t16
  t18 = t2 * r0
  t21 = 0.1e1 / t4 / t3 / t18
  t27 = params.b * t16 * s0
  t28 = t3 ** 2
  t31 = params.k ** 2
  t36 = 0.88e2 / 0.9e1 * t1 * t7 * t12 - 0.24e2 * t17 * t21 * params.k * t12 + 0.64e2 / 0.9e1 * t27 / t28 / t2 * t31 * t12
  t37 = 3 ** (0.1e1 / 0.3e1)
  t39 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t40 = t37 * t39
  t41 = 4 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t46 = t37 ** 2
  t47 = jnp.pi ** (0.1e1 / 0.3e1)
  t49 = jnp.sqrt(s0)
  t50 = t49 * s0
  t54 = 0.1e1 / t4 / r0
  t55 = t49 * t54
  t56 = jnp.sqrt(t55)
  t61 = 0.1e1 + params.d * t41 * t46 * t47 * t56 * t50 / t3 / 0.3e1
  t65 = params.c + t40 * t42 / t4 * t61 / 0.4e1
  t66 = 0.1e1 / t65
  t70 = 0.1e1 / t5 / t18
  t73 = t3 * t2
  t80 = -0.8e1 / 0.3e1 * t1 * t70 * t12 + 0.8e1 / 0.3e1 * t17 / t4 / t73 * params.k * t12
  t81 = t65 ** 2
  t82 = 0.1e1 / t81
  t93 = t47 * t56 * s0 * t10 * t49
  t96 = -t40 * t42 * t54 * t61 / 0.12e2 - 0.14e2 / 0.3e1 * t39 * t10 * params.d * t93
  t101 = t1 * t10 * t12 + params.a
  t103 = 0.1e1 / t81 / t65
  t105 = t96 ** 2
  t119 = t3 * r0
  t125 = t47 * t56 * t55 * s0
  t128 = t40 * t42 / t4 / t2 * t61 / 0.9e1 + 0.14e2 * t39 * t70 * params.d * t93 + 0.140e3 / 0.9e1 * t39 / t119 * params.d * t125
  t148 = t16 ** 2
  t165 = r0 * t80
  t172 = r0 * t101
  t173 = t81 ** 2
  v3rho3_0_ = 0.3e1 * t36 * t66 - 0.6e1 * t80 * t82 * t96 + 0.6e1 * t101 * t103 * t105 - 0.3e1 * t101 * t82 * t128 + r0 * (-0.1232e4 / 0.27e2 * t1 / t5 / t119 * t12 + 0.5456e4 / 0.27e2 * t17 / t4 / t28 * params.k * t12 - 0.1216e4 / 0.9e1 * t27 / t28 / t18 * t31 * t12 + 0.512e3 / 0.27e2 * params.b * t148 / t5 / t28 / t119 * t31 * params.k * t12) * t66 - 0.3e1 * r0 * t36 * t82 * t96 + 0.6e1 * t165 * t103 * t105 - 0.3e1 * t165 * t82 * t128 - 0.6e1 * t172 / t173 * t105 * t96 + 0.6e1 * t172 * t103 * t96 * t128 - t172 * t82 * (-0.7e1 / 0.27e2 * t40 * t42 / t4 / t18 * t61 - 0.1442e4 / 0.27e2 * t39 * t7 * params.d * t93 - 0.1120e4 / 0.9e1 * t39 / t73 * params.d * t125 - 0.280e3 / 0.9e1 * t39 * t21 * params.d * t47 * t56 * t50)

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.b * s0
  t2 = r0 ** 2
  t3 = t2 ** 2
  t4 = t3 * r0
  t5 = r0 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t8 = 0.1e1 / t6 / t4
  t11 = 0.1e1 / t6 / t2
  t13 = jnp.exp(-params.k * s0 * t11)
  t17 = s0 ** 2
  t18 = params.b * t17
  t19 = t3 ** 2
  t21 = 0.1e1 / t5 / t19
  t27 = params.b * t17 * s0
  t28 = t2 * r0
  t31 = params.k ** 2
  t36 = t17 ** 2
  t37 = params.b * t36
  t41 = t31 * params.k
  t46 = -0.1232e4 / 0.27e2 * t1 * t8 * t13 + 0.5456e4 / 0.27e2 * t18 * t21 * params.k * t13 - 0.1216e4 / 0.9e1 * t27 / t19 / t28 * t31 * t13 + 0.512e3 / 0.27e2 * t37 / t6 / t19 / t4 * t41 * t13
  t47 = 3 ** (0.1e1 / 0.3e1)
  t49 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t50 = t47 * t49
  t51 = 4 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t56 = t47 ** 2
  t57 = jnp.pi ** (0.1e1 / 0.3e1)
  t59 = jnp.sqrt(s0)
  t60 = t59 * s0
  t64 = 0.1e1 / t5 / r0
  t65 = t59 * t64
  t66 = jnp.sqrt(t65)
  t71 = 0.1e1 + params.d * t51 * t56 * t57 * t66 * t60 / t3 / 0.3e1
  t75 = params.c + t50 * t52 / t5 * t71 / 0.4e1
  t76 = 0.1e1 / t75
  t80 = 0.1e1 / t6 / t3
  t84 = t3 * t28
  t86 = 0.1e1 / t5 / t84
  t97 = 0.88e2 / 0.9e1 * t1 * t80 * t13 - 0.24e2 * t18 * t86 * params.k * t13 + 0.64e2 / 0.9e1 * t27 / t19 / t2 * t31 * t13
  t98 = r0 * t97
  t99 = t75 ** 2
  t101 = 0.1e1 / t99 / t75
  t111 = t57 * t66 * s0 * t11 * t59
  t114 = -t50 * t52 * t64 * t71 / 0.12e2 - 0.14e2 / 0.3e1 * t49 * t11 * params.d * t111
  t115 = t114 ** 2
  t120 = 0.1e1 / t6 / t28
  t123 = t3 * t2
  t130 = -0.8e1 / 0.3e1 * t1 * t120 * t13 + 0.8e1 / 0.3e1 * t18 / t5 / t123 * params.k * t13
  t131 = r0 * t130
  t132 = t99 ** 2
  t133 = 0.1e1 / t132
  t134 = t115 * t114
  t138 = t101 * t114
  t154 = t57 * t66 * t65 * s0
  t157 = t50 * t52 / t5 / t2 * t71 / 0.9e1 + 0.14e2 * t49 * t120 * params.d * t111 + 0.140e3 / 0.9e1 * t49 / t4 * params.d * t154
  t163 = t1 * t11 * t13 + params.a
  t164 = r0 * t163
  t167 = t115 ** 2
  t175 = t157 ** 2
  t197 = t57 * t66 * t60
  t200 = -0.7e1 / 0.27e2 * t50 * t52 / t5 / t28 * t71 - 0.1442e4 / 0.27e2 * t49 * t80 * params.d * t111 - 0.1120e4 / 0.9e1 * t49 / t123 * params.d * t154 - 0.280e3 / 0.9e1 * t49 * t86 * params.d * t197
  t215 = 0.1e1 / t99
  t244 = t19 * r0
  t292 = t19 ** 2
  t296 = t31 ** 2
  v4rho4_0_ = 0.4e1 * t46 * t76 + 0.12e2 * t98 * t101 * t115 - 0.24e2 * t131 * t133 * t134 + 0.24e2 * t131 * t138 * t157 + 0.24e2 * t164 / t132 / t75 * t167 - 0.36e2 * t164 * t133 * t115 * t157 + 0.6e1 * t164 * t101 * t175 + 0.8e1 * t164 * t138 * t200 + 0.24e2 * t130 * t101 * t115 - 0.24e2 * t163 * t133 * t134 + 0.24e2 * t163 * t101 * t114 * t157 - 0.4e1 * r0 * t46 * t215 * t114 - 0.6e1 * t98 * t215 * t157 - 0.4e1 * t131 * t215 * t200 - t164 * t215 * (0.70e2 / 0.81e2 * t50 * t52 / t5 / t3 * t71 + 0.6860e4 / 0.27e2 * t49 * t8 * params.d * t111 + 0.74900e5 / 0.81e2 * t49 / t84 * params.d * t154 + 0.12880e5 / 0.27e2 * t49 * t21 * params.d * t197 + 0.560e3 / 0.27e2 * t49 / t6 / t244 * params.d * t57 / t66 * t17) - 0.12e2 * t97 * t215 * t114 - 0.12e2 * t130 * t215 * t157 - 0.4e1 * t163 * t215 * t200 + r0 * (0.20944e5 / 0.81e2 * t1 / t6 / t123 * t13 - 0.48752e5 / 0.27e2 * t18 / t5 / t244 * params.k * t13 + 0.164032e6 / 0.81e2 * t27 / t19 / t3 * t31 * t13 - 0.50176e5 / 0.81e2 * t37 / t6 / t19 / t123 * t41 * t13 + 0.4096e4 / 0.81e2 * params.b * t36 * s0 / t5 / t292 / r0 * t296 * t13) * t76

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t2 = s0 + 0.2e1 * s1 + s2
  t3 = params.b * t2
  t4 = r0 + r1
  t5 = t4 ** 2
  t6 = t5 * t4
  t7 = t4 ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t10 = 0.1e1 / t8 / t6
  t13 = 0.1e1 / t8 / t5
  t15 = jnp.exp(-params.k * t2 * t13)
  t18 = t2 ** 2
  t19 = params.b * t18
  t20 = t5 ** 2
  t28 = -0.8e1 / 0.3e1 * t3 * t10 * t15 + 0.8e1 / 0.3e1 * t19 / t7 / t20 / t5 * params.k * t15
  t29 = 3 ** (0.1e1 / 0.3e1)
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = t29 * t31
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t38 = t29 ** 2
  t39 = jnp.pi ** (0.1e1 / 0.3e1)
  t41 = jnp.sqrt(t2)
  t46 = 0.1e1 / t7 / t4
  t47 = t41 * t46
  t48 = jnp.sqrt(t47)
  t53 = 0.1e1 + params.d * t33 * t38 * t39 * t48 * t41 * t2 / t20 / 0.3e1
  t57 = params.c + t32 * t34 / t7 * t53 / 0.4e1
  t58 = 0.1e1 / t57
  t63 = t3 * t13 * t15 + params.a
  t64 = t57 ** 2
  t65 = 0.1e1 / t64
  t76 = t39 * t48 * t2 * t13 * t41
  t79 = -t32 * t34 * t46 * t53 / 0.12e2 - 0.14e2 / 0.3e1 * t31 * t13 * params.d * t76
  t96 = t20 ** 2
  t99 = params.k ** 2
  t111 = t4 * t63
  t114 = t79 ** 2
  d11 = 0.2e1 * t28 * t58 - 0.2e1 * t63 * t65 * t79 + t4 * (0.88e2 / 0.9e1 * t3 / t8 / t20 * t15 - 0.24e2 * t19 / t7 / t20 / t6 * params.k * t15 + 0.64e2 / 0.9e1 * params.b * t18 * t2 / t96 / t5 * t99 * t15) * t58 - 0.2e1 * t4 * t28 * t65 * t79 + 0.2e1 * t111 / t64 / t57 * t114 - t111 * t65 * (t32 * t34 / t7 / t5 * t53 / 0.9e1 + 0.14e2 * t31 * t10 * params.d * t76 + 0.140e3 / 0.9e1 * t31 / t20 / t4 * params.d * t39 * t48 * t47 * t2)
  d12 = d11
  d22 = d12
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

  t2 = s0 + 0.2e1 * s1 + s2
  t3 = params.b * t2
  t4 = r0 + r1
  t5 = t4 ** 2
  t6 = t5 ** 2
  t7 = t4 ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t10 = 0.1e1 / t8 / t6
  t13 = 0.1e1 / t8 / t5
  t15 = jnp.exp(-params.k * t2 * t13)
  t19 = t2 ** 2
  t20 = params.b * t19
  t21 = t5 * t4
  t24 = 0.1e1 / t7 / t6 / t21
  t30 = params.b * t19 * t2
  t31 = t6 ** 2
  t34 = params.k ** 2
  t39 = 0.88e2 / 0.9e1 * t3 * t10 * t15 - 0.24e2 * t20 * t24 * params.k * t15 + 0.64e2 / 0.9e1 * t30 / t31 / t5 * t34 * t15
  t40 = 3 ** (0.1e1 / 0.3e1)
  t42 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t43 = t40 * t42
  t44 = 4 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t49 = t40 ** 2
  t50 = jnp.pi ** (0.1e1 / 0.3e1)
  t52 = jnp.sqrt(t2)
  t53 = t52 * t2
  t57 = 0.1e1 / t7 / t4
  t58 = t52 * t57
  t59 = jnp.sqrt(t58)
  t64 = 0.1e1 + params.d * t44 * t49 * t50 * t59 * t53 / t6 / 0.3e1
  t68 = params.c + t43 * t45 / t7 * t64 / 0.4e1
  t69 = 0.1e1 / t68
  t73 = 0.1e1 / t8 / t21
  t76 = t6 * t5
  t83 = -0.8e1 / 0.3e1 * t3 * t73 * t15 + 0.8e1 / 0.3e1 * t20 / t7 / t76 * params.k * t15
  t84 = t68 ** 2
  t85 = 0.1e1 / t84
  t96 = t50 * t59 * t2 * t13 * t52
  t99 = -t43 * t45 * t57 * t64 / 0.12e2 - 0.14e2 / 0.3e1 * t42 * t13 * params.d * t96
  t104 = t3 * t13 * t15 + params.a
  t106 = 0.1e1 / t84 / t68
  t108 = t99 ** 2
  t122 = t6 * t4
  t128 = t50 * t59 * t58 * t2
  t131 = t43 * t45 / t7 / t5 * t64 / 0.9e1 + 0.14e2 * t42 * t73 * params.d * t96 + 0.140e3 / 0.9e1 * t42 / t122 * params.d * t128
  t151 = t19 ** 2
  t168 = t4 * t83
  t175 = t4 * t104
  t176 = t84 ** 2
  d111 = 0.3e1 * t39 * t69 - 0.6e1 * t83 * t85 * t99 + 0.6e1 * t104 * t106 * t108 - 0.3e1 * t104 * t85 * t131 + t4 * (-0.1232e4 / 0.27e2 * t3 / t8 / t122 * t15 + 0.5456e4 / 0.27e2 * t20 / t7 / t31 * params.k * t15 - 0.1216e4 / 0.9e1 * t30 / t31 / t21 * t34 * t15 + 0.512e3 / 0.27e2 * params.b * t151 / t8 / t31 / t122 * t34 * params.k * t15) * t69 - 0.3e1 * t4 * t39 * t85 * t99 + 0.6e1 * t168 * t106 * t108 - 0.3e1 * t168 * t85 * t131 - 0.6e1 * t175 / t176 * t108 * t99 + 0.6e1 * t175 * t106 * t99 * t131 - t175 * t85 * (-0.7e1 / 0.27e2 * t43 * t45 / t7 / t21 * t64 - 0.1442e4 / 0.27e2 * t42 * t10 * params.d * t96 - 0.1120e4 / 0.9e1 * t42 / t76 * params.d * t128 - 0.280e3 / 0.9e1 * t42 * t24 * params.d * t50 * t59 * t53)

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

  t2 = s0 + 0.2e1 * s1 + s2
  t3 = params.b * t2
  t4 = r0 + r1
  t5 = t4 ** 2
  t6 = t5 ** 2
  t7 = t6 * t4
  t8 = t4 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t11 = 0.1e1 / t9 / t7
  t14 = 0.1e1 / t9 / t5
  t16 = jnp.exp(-params.k * t2 * t14)
  t20 = t2 ** 2
  t21 = params.b * t20
  t22 = t6 ** 2
  t24 = 0.1e1 / t8 / t22
  t30 = params.b * t20 * t2
  t31 = t5 * t4
  t34 = params.k ** 2
  t39 = t20 ** 2
  t40 = params.b * t39
  t44 = t34 * params.k
  t49 = -0.1232e4 / 0.27e2 * t3 * t11 * t16 + 0.5456e4 / 0.27e2 * t21 * t24 * params.k * t16 - 0.1216e4 / 0.9e1 * t30 / t22 / t31 * t34 * t16 + 0.512e3 / 0.27e2 * t40 / t9 / t22 / t7 * t44 * t16
  t50 = 3 ** (0.1e1 / 0.3e1)
  t52 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t53 = t50 * t52
  t54 = 4 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t59 = t50 ** 2
  t60 = jnp.pi ** (0.1e1 / 0.3e1)
  t62 = jnp.sqrt(t2)
  t63 = t62 * t2
  t67 = 0.1e1 / t8 / t4
  t68 = t62 * t67
  t69 = jnp.sqrt(t68)
  t74 = 0.1e1 + params.d * t54 * t59 * t60 * t69 * t63 / t6 / 0.3e1
  t78 = params.c + t53 * t55 / t8 * t74 / 0.4e1
  t79 = 0.1e1 / t78
  t83 = 0.1e1 / t9 / t6
  t87 = t6 * t31
  t89 = 0.1e1 / t8 / t87
  t100 = 0.88e2 / 0.9e1 * t3 * t83 * t16 - 0.24e2 * t21 * t89 * params.k * t16 + 0.64e2 / 0.9e1 * t30 / t22 / t5 * t34 * t16
  t101 = t78 ** 2
  t102 = 0.1e1 / t101
  t113 = t60 * t69 * t2 * t14 * t62
  t116 = -t53 * t55 * t67 * t74 / 0.12e2 - 0.14e2 / 0.3e1 * t52 * t14 * params.d * t113
  t120 = 0.1e1 / t9 / t31
  t123 = t6 * t5
  t130 = -0.8e1 / 0.3e1 * t3 * t120 * t16 + 0.8e1 / 0.3e1 * t21 / t8 / t123 * params.k * t16
  t147 = t60 * t69 * t68 * t2
  t150 = t53 * t55 / t8 / t5 * t74 / 0.9e1 + 0.14e2 * t52 * t120 * params.d * t113 + 0.140e3 / 0.9e1 * t52 / t7 * params.d * t147
  t155 = t3 * t14 * t16 + params.a
  t175 = t60 * t69 * t63
  t178 = -0.7e1 / 0.27e2 * t53 * t55 / t8 / t31 * t74 - 0.1442e4 / 0.27e2 * t52 * t83 * params.d * t113 - 0.1120e4 / 0.9e1 * t52 / t123 * params.d * t147 - 0.280e3 / 0.9e1 * t52 * t89 * params.d * t175
  t186 = t22 * t4
  t208 = t22 ** 2
  t212 = t34 ** 2
  t220 = t4 * t100
  t222 = 0.1e1 / t101 / t78
  t223 = t116 ** 2
  t227 = t4 * t130
  t228 = t101 ** 2
  t229 = 0.1e1 / t228
  t230 = t223 * t116
  t234 = t222 * t116
  t238 = t4 * t155
  t241 = t223 ** 2
  t249 = t150 ** 2
  d1111 = 0.4e1 * t49 * t79 - 0.12e2 * t100 * t102 * t116 - 0.12e2 * t130 * t102 * t150 - 0.4e1 * t155 * t102 * t178 + t4 * (0.20944e5 / 0.81e2 * t3 / t9 / t123 * t16 - 0.48752e5 / 0.27e2 * t21 / t8 / t186 * params.k * t16 + 0.164032e6 / 0.81e2 * t30 / t22 / t6 * t34 * t16 - 0.50176e5 / 0.81e2 * t40 / t9 / t22 / t123 * t44 * t16 + 0.4096e4 / 0.81e2 * params.b * t39 * t2 / t8 / t208 / t4 * t212 * t16) * t79 + 0.12e2 * t220 * t222 * t223 - 0.24e2 * t227 * t229 * t230 + 0.24e2 * t227 * t234 * t150 + 0.24e2 * t238 / t228 / t78 * t241 - 0.36e2 * t238 * t229 * t223 * t150 + 0.6e1 * t238 * t222 * t249 + 0.8e1 * t238 * t234 * t178 + 0.24e2 * t130 * t222 * t223 - 0.24e2 * t155 * t229 * t230 + 0.24e2 * t155 * t222 * t116 * t150 - 0.4e1 * t4 * t49 * t102 * t116 - 0.6e1 * t220 * t102 * t150 - 0.4e1 * t227 * t102 * t178 - t238 * t102 * (0.70e2 / 0.81e2 * t53 * t55 / t8 / t6 * t74 + 0.6860e4 / 0.27e2 * t52 * t11 * params.d * t113 + 0.74900e5 / 0.81e2 * t52 / t87 * params.d * t147 + 0.12880e5 / 0.27e2 * t52 * t24 * params.d * t175 + 0.560e3 / 0.27e2 * t52 / t9 / t186 * params.d * t60 / t69 * t20)

  res = {'v4rho4': d1111}
  return res
