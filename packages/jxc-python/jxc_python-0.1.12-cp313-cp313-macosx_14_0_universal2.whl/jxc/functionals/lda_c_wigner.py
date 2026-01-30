"""Generated from lda_c_wigner.mpl."""

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

  functional_body = lambda rs, z: (1 - z ** 2) * params_a / (params_b + rs)

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

  functional_body = lambda rs, z: (1 - z ** 2) * params_a / (params_b + rs)

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

  functional_body = lambda rs, z: (1 - z ** 2) * params_a / (params_b + rs)

  t1 = r0 - r1
  t2 = t1 ** 2
  t3 = r0 + r1
  t4 = t3 ** 2
  t5 = 0.1e1 / t4
  t7 = -t2 * t5 + 0.1e1
  t9 = 3 ** (0.1e1 / 0.3e1)
  t11 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t13 = 4 ** (0.1e1 / 0.3e1)
  t14 = t13 ** 2
  t15 = t3 ** (0.1e1 / 0.3e1)
  t16 = 0.1e1 / t15
  t20 = params.b + t9 * t11 * t14 * t16 / 0.4e1
  t21 = 0.1e1 / t20
  t22 = t7 * params.a * t21
  t23 = t1 * t5
  t26 = t2 / t4 / t3
  t30 = params.a * t21
  t34 = t20 ** 2
  t40 = t16 * t7 * params.a / t34 * t9 * t11 * t14 / 0.12e2
  vrho_0_ = t22 + t3 * (-0.2e1 * t23 + 0.2e1 * t26) * t30 + t40
  vrho_1_ = t22 + t3 * (0.2e1 * t23 + 0.2e1 * t26) * t30 + t40
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

  functional_body = lambda rs, z: (1 - z ** 2) * params_a / (params_b + rs)

  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t7
  t12 = params.b + t4 * t6 * t8 / 0.4e1
  t16 = t12 ** 2
  vrho_0_ = params.a / t12 + t8 * params.a / t16 * t4 * t6 / 0.12e2
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
  t12 = params.b + t1 * t3 * t6 / t7 / 0.4e1
  t13 = t12 ** 2
  t22 = t7 ** 2
  t29 = t1 ** 2
  t30 = t3 ** 2
  v2rho2_0_ = params.a / t13 * t1 * t3 * t6 / t7 / r0 / 0.18e2 + 0.1e1 / t22 / r0 * params.a / t13 / t12 * t29 * t30 * t5 / 0.18e2
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
  t12 = params.b + t1 * t3 * t6 / t7 / 0.4e1
  t13 = t12 ** 2
  t17 = t1 ** 2
  t19 = t3 ** 2
  t21 = r0 ** 2
  t22 = t7 ** 2
  t40 = t13 ** 2
  v3rho3_0_ = -params.a / t13 / t12 * t17 * t19 * t5 / t22 / t21 / 0.18e2 - 0.2e1 / 0.27e2 * params.a / t13 * t1 * t3 * t6 / t7 / t21 + 0.1e1 / t21 / r0 * params.a / t40 * t2 / 0.6e1

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
  t12 = params.b + t1 * t3 * t6 / t7 / 0.4e1
  t13 = t12 ** 2
  t14 = t13 ** 2
  t17 = r0 ** 2
  t18 = t17 ** 2
  t26 = t1 ** 2
  t28 = t3 ** 2
  t30 = t17 * r0
  t31 = t7 ** 2
  t40 = t3 * t6
  v4rho4_0_ = -0.2e1 / 0.3e1 * params.a / t14 * t2 / t18 + 0.8e1 / 0.81e2 * params.a / t13 / t12 * t26 * t28 * t5 / t31 / t30 + 0.14e2 / 0.81e2 * params.a / t13 * t1 * t40 / t7 / t30 + 0.1e1 / t7 / t18 * params.a / t14 / t12 * t2 * t1 * t40 / 0.18e2

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 - r1
  t2 = r0 + r1
  t3 = t2 ** 2
  t4 = 0.1e1 / t3
  t5 = t1 * t4
  t6 = t1 ** 2
  t8 = 0.1e1 / t3 / t2
  t9 = t6 * t8
  t11 = -0.2e1 * t5 + 0.2e1 * t9
  t13 = 3 ** (0.1e1 / 0.3e1)
  t15 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t16 = t13 * t15
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t19 = t2 ** (0.1e1 / 0.3e1)
  t20 = 0.1e1 / t19
  t24 = params.b + t16 * t18 * t20 / 0.4e1
  t25 = 0.1e1 / t24
  t26 = t11 * params.a * t25
  t29 = -t6 * t4 + 0.1e1
  t31 = t24 ** 2
  t32 = 0.1e1 / t31
  t39 = t29 * params.a * t32 * t16 * t18 / t19 / t2 / 0.18e2
  t40 = 0.2e1 * t4
  t42 = 0.8e1 * t1 * t8
  t43 = t3 ** 2
  t46 = 0.6e1 * t6 / t43
  t49 = params.a * t25
  t55 = t32 * t13 * t15 * t18
  t56 = t20 * t11 * params.a * t55
  t58 = t19 ** 2
  t65 = t13 ** 2
  t67 = t15 ** 2
  t71 = 0.1e1 / t58 / t2 * t29 * params.a / t31 / t24 * t65 * t67 * t17 / 0.18e2
  d11 = 0.2e1 * t26 + t39 + t2 * (-t40 + t42 - t46) * t49 + t56 / 0.6e1 + t71
  t73 = 0.2e1 * t5 + 0.2e1 * t9
  t75 = t73 * params.a * t25
  t81 = t20 * t73 * params.a * t55
  d12 = t26 + t39 + t75 + t2 * (t40 - t46) * t49 + t81 / 0.12e2 + t56 / 0.12e2 + t71
  d22 = 0.2e1 * t75 + t39 + t2 * (-t40 - t42 - t46) * t49 + t81 / 0.6e1 + t71
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** 2
  t3 = 0.1e1 / t2
  t5 = r0 - r1
  t7 = 0.1e1 / t2 / t1
  t10 = t5 ** 2
  t11 = t2 ** 2
  t12 = 0.1e1 / t11
  t15 = -0.6e1 * t10 * t12 + 0.8e1 * t5 * t7 - 0.2e1 * t3
  t17 = 3 ** (0.1e1 / 0.3e1)
  t18 = 0.1e1 / jnp.pi
  t19 = t18 ** (0.1e1 / 0.3e1)
  t20 = t17 * t19
  t21 = 4 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = t1 ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t23
  t28 = params.b + t20 * t22 * t24 / 0.4e1
  t29 = 0.1e1 / t28
  t35 = 0.2e1 * t10 * t7 - 0.2e1 * t5 * t3
  t37 = t28 ** 2
  t38 = 0.1e1 / t37
  t47 = -t10 * t3 + 0.1e1
  t48 = t47 * params.a
  t50 = 0.1e1 / t37 / t28
  t52 = t17 ** 2
  t53 = t19 ** 2
  t55 = t23 ** 2
  t97 = t37 ** 2
  d111 = 0.3e1 * t15 * params.a * t29 + t35 * params.a * t38 * t20 * t22 / t23 / t1 / 0.6e1 - t48 * t50 * t52 * t53 * t21 / t55 / t2 / 0.18e2 - 0.2e1 / 0.27e2 * t48 * t38 * t20 * t22 / t23 / t2 + t1 * (0.12e2 * t7 - 0.36e2 * t5 * t12 + 0.24e2 * t10 / t11 / t1) * params.a * t29 + t24 * t15 * params.a * t38 * t17 * t19 * t22 / 0.4e1 + 0.1e1 / t55 / t1 * t35 * params.a * t50 * t52 * t53 * t21 / 0.6e1 + t7 * t47 * params.a / t97 * t18 / 0.6e1

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** 2
  t3 = t2 * t1
  t4 = 0.1e1 / t3
  t6 = r0 - r1
  t7 = t2 ** 2
  t8 = 0.1e1 / t7
  t11 = t6 ** 2
  t13 = 0.1e1 / t7 / t1
  t16 = 0.24e2 * t11 * t13 - 0.36e2 * t6 * t8 + 0.12e2 * t4
  t18 = 3 ** (0.1e1 / 0.3e1)
  t19 = 0.1e1 / jnp.pi
  t20 = t19 ** (0.1e1 / 0.3e1)
  t21 = t18 * t20
  t22 = 4 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t1 ** (0.1e1 / 0.3e1)
  t25 = 0.1e1 / t24
  t29 = params.b + t21 * t23 * t25 / 0.4e1
  t30 = 0.1e1 / t29
  t33 = 0.1e1 / t2
  t39 = -0.6e1 * t11 * t8 + 0.8e1 * t6 * t4 - 0.2e1 * t33
  t41 = t29 ** 2
  t42 = 0.1e1 / t41
  t53 = 0.2e1 * t11 * t4 - 0.2e1 * t6 * t33
  t54 = t53 * params.a
  t56 = 0.1e1 / t41 / t29
  t58 = t18 ** 2
  t59 = t20 ** 2
  t60 = t58 * t59
  t61 = t24 ** 2
  t76 = -t11 * t33 + 0.1e1
  t77 = t76 * params.a
  t78 = t41 ** 2
  t79 = 0.1e1 / t78
  t112 = t20 * t23
  d1111 = 0.4e1 * t16 * params.a * t30 + t39 * params.a * t42 * t21 * t23 / t24 / t1 / 0.3e1 - 0.2e1 / 0.9e1 * t54 * t56 * t60 * t22 / t61 / t2 - 0.8e1 / 0.27e2 * t54 * t42 * t21 * t23 / t24 / t2 - 0.2e1 / 0.3e1 * t77 * t79 * t19 * t8 + 0.8e1 / 0.81e2 * t77 * t56 * t60 * t22 / t61 / t3 + 0.14e2 / 0.81e2 * t77 * t42 * t21 * t23 / t24 / t3 + t1 * (-0.72e2 * t8 + 0.192e3 * t6 * t13 - 0.120e3 * t11 / t7 / t2) * params.a * t30 + t25 * t16 * params.a * t42 * t18 * t112 / 0.3e1 + 0.1e1 / t61 / t1 * t39 * params.a * t56 * t58 * t59 * t22 / 0.3e1 + 0.2e1 / 0.3e1 * t4 * t53 * params.a * t79 * t19 + 0.1e1 / t24 / t7 * t76 * params.a / t78 / t29 * t19 * t18 * t112 / 0.18e2

  res = {'v4rho4': d1111}
  return res
