"""Generated from gga_x_lb.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import numpy as np
from jax.numpy import array as array
from jax.numpy import int32 as int32
from jax.numpy import nan as nan
from typing import Callable, Optional
from .utils import *

def pol(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
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

  lb_f0 = lambda rs, z, x: -f.my_piecewise3(x < 300, params_beta * x ** 2 / (1 + 3 * params_beta * x * jnp.arcsinh(params_gamma * x)), x / (3 * jnp.log(2 * params_gamma * x)))

  lb_f = lambda rs, z, x: (params_alpha * (4 / 3) * f.LDA_X_FACTOR + lb_f0(rs, z, x)) * f.n_spin(rs, z) ** (1 / 3)

  functional_body = lambda rs, z, xt, xs0, xs1=None: lb_f(rs, z, xs0)
  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
      f.xt(r0, r1, s0, s1, s2),
      f.xs0(r0, r1, s0, s2),
      f.xs1(r0, r1, s0, s2),
  )
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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
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

  lb_f0 = lambda rs, z, x: -f.my_piecewise3(x < 300, params_beta * x ** 2 / (1 + 3 * params_beta * x * jnp.arcsinh(params_gamma * x)), x / (3 * jnp.log(2 * params_gamma * x)))

  lb_f = lambda rs, z, x: (params_alpha * (4 / 3) * f.LDA_X_FACTOR + lb_f0(rs, z, x)) * f.n_spin(rs, z) ** (1 / 3)

  functional_body = lambda rs, z, xt, xs0, xs1=None: lb_f(rs, z, xs0)
  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
      f.xt(r0 / 2, r0 / 2, s0 / 4, s0 / 4, s0 / 4),
      f.xs0(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.xs1(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
  )
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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
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

  lb_f0 = lambda rs, z, x: -f.my_piecewise3(x < 300, params_beta * x ** 2 / (1 + 3 * params_beta * x * jnp.arcsinh(params_gamma * x)), x / (3 * jnp.log(2 * params_gamma * x)))

  lb_f = lambda rs, z, x: (params_alpha * (4 / 3) * f.LDA_X_FACTOR + lb_f0(rs, z, x)) * f.n_spin(rs, z) ** (1 / 3)

  functional_body = lambda rs, z, xt, xs0, xs1=None: lb_f(rs, z, xs0)

  t1 = 3 ** (0.1e1 / 0.3e1)
  t4 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t10 = jnp.sqrt(s0)
  t11 = r0 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / t11 / r0
  t14 = t10 * t13
  t15 = t14 < 0.300e3
  t16 = params.beta * s0
  t17 = r0 ** 2
  t18 = t11 ** 2
  t20 = 0.1e1 / t18 / t17
  t21 = params.beta * t10
  t23 = params.gamma * t10 * t13
  t24 = jnp.arcsinh(t23)
  t25 = t13 * t24
  t28 = 0.3e1 * t21 * t25 + 0.1e1
  t29 = 0.1e1 / t28
  t33 = jnp.log(0.2e1 * t23)
  t34 = 0.1e1 / t33
  t37 = f.my_piecewise3(t15, t16 * t20 * t29, t14 * t34 / 0.3e1)
  t38 = -params.alpha * t1 * t4 * t6 / 0.2e1 - t37
  t39 = t38 * t11
  t40 = r0 + r1
  t43 = 0.1e1 / t18 / t17 / r0
  t47 = t28 ** 2
  t49 = t20 / t47
  t51 = 0.1e1 / t11 / t17
  t55 = params.gamma ** 2
  t59 = jnp.sqrt(t55 * s0 * t20 + 0.1e1)
  t60 = 0.1e1 / t59
  t68 = t10 * t51
  t70 = t33 ** 2
  t71 = 0.1e1 / t70
  t75 = f.my_piecewise3(t15, -0.8e1 / 0.3e1 * t16 * t43 * t29 - t16 * t49 * (-0.4e1 * t16 * t43 * params.gamma * t60 - 0.4e1 * t21 * t51 * t24), -0.4e1 / 0.9e1 * t68 * t34 + 0.4e1 / 0.9e1 * t68 * t71)
  vrho_0_ = t39 - t40 * t75 * t11 + t40 * t38 / t18 / 0.3e1
  vrho_1_ = t39
  t82 = params.beta * t20
  t84 = 0.1e1 / t10
  t94 = t84 * t13
  t99 = f.my_piecewise3(t15, t82 * t29 - t16 * t49 * (0.3e1 / 0.2e1 * params.beta * t84 * t25 + 0.3e1 / 0.2e1 * t82 * params.gamma * t60), t94 * t34 / 0.6e1 - t94 * t71 / 0.6e1)
  vsigma_0_ = -t40 * t99 * t11
  vsigma_1_ = 0.0e0
  vsigma_2_ = 0.0e0
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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
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

  lb_f0 = lambda rs, z, x: -f.my_piecewise3(x < 300, params_beta * x ** 2 / (1 + 3 * params_beta * x * jnp.arcsinh(params_gamma * x)), x / (3 * jnp.log(2 * params_gamma * x)))

  lb_f = lambda rs, z, x: (params_alpha * (4 / 3) * f.LDA_X_FACTOR + lb_f0(rs, z, x)) * f.n_spin(rs, z) ** (1 / 3)

  functional_body = lambda rs, z, xt, xs0, xs1=None: lb_f(rs, z, xs0)

  t1 = 3 ** (0.1e1 / 0.3e1)
  t4 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t10 = jnp.sqrt(s0)
  t11 = 2 ** (0.1e1 / 0.3e1)
  t12 = t10 * t11
  t13 = r0 ** (0.1e1 / 0.3e1)
  t14 = t13 * r0
  t15 = 0.1e1 / t14
  t17 = t12 * t15 < 0.300e3
  t18 = params.beta * s0
  t19 = t11 ** 2
  t20 = r0 ** 2
  t21 = t13 ** 2
  t23 = 0.1e1 / t21 / t20
  t24 = t19 * t23
  t25 = params.beta * t10
  t26 = t11 * t15
  t28 = params.gamma * t10 * t26
  t29 = jnp.arcsinh(t28)
  t30 = t26 * t29
  t33 = 0.3e1 * t25 * t30 + 0.1e1
  t34 = 0.1e1 / t33
  t38 = jnp.log(0.2e1 * t28)
  t39 = 0.1e1 / t38
  t40 = t15 * t39
  t43 = f.my_piecewise3(t17, t18 * t24 * t34, t12 * t40 / 0.3e1)
  t50 = 0.1e1 / t21 / t20 / r0
  t55 = t18 * t19
  t56 = t33 ** 2
  t58 = t23 / t56
  t60 = 0.1e1 / t13 / t20
  t65 = params.gamma ** 2
  t69 = jnp.sqrt(t65 * s0 * t24 + 0.1e1)
  t70 = 0.1e1 / t69
  t80 = t38 ** 2
  t81 = 0.1e1 / t80
  t86 = f.my_piecewise3(t17, -0.8e1 / 0.3e1 * t18 * t19 * t50 * t34 - t55 * t58 * (-0.4e1 * t25 * t11 * t60 * t29 - 0.4e1 * t55 * t50 * params.gamma * t70), -0.4e1 / 0.9e1 * t12 * t60 * t39 + 0.4e1 / 0.9e1 * t12 * t60 * t81)
  vrho_0_ = 0.2e1 / 0.3e1 * (-params.alpha * t1 * t4 * t6 / 0.2e1 - t43) * t19 * t13 - t14 * t86 * t19 / 0.2e1
  t90 = params.beta * t19
  t93 = 0.1e1 / t10
  t104 = t93 * t11
  t110 = f.my_piecewise3(t17, t90 * t23 * t34 - t55 * t58 * (0.3e1 / 0.2e1 * t90 * t23 * params.gamma * t70 + 0.3e1 / 0.2e1 * params.beta * t93 * t30), -t104 * t15 * t81 / 0.6e1 + t104 * t40 / 0.6e1)
  vsigma_0_ = -t14 * t110 * t19 / 0.2e1
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = jnp.sqrt(s0)
  t2 = r0 ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t2 / r0
  t5 = t1 * t4
  t6 = t5 < 0.300e3
  t7 = params.beta * s0
  t8 = r0 ** 2
  t9 = t8 * r0
  t10 = t2 ** 2
  t12 = 0.1e1 / t10 / t9
  t13 = params.beta * t1
  t15 = params.gamma * t1 * t4
  t16 = jnp.arcsinh(t15)
  t20 = 0.3e1 * t13 * t4 * t16 + 0.1e1
  t21 = 0.1e1 / t20
  t26 = 0.1e1 / t10 / t8
  t27 = t20 ** 2
  t28 = 0.1e1 / t27
  t29 = t26 * t28
  t31 = 0.1e1 / t2 / t8
  t35 = params.gamma ** 2
  t38 = t35 * s0 * t26 + 0.1e1
  t39 = jnp.sqrt(t38)
  t40 = 0.1e1 / t39
  t44 = -0.4e1 * t7 * t12 * params.gamma * t40 - 0.4e1 * t13 * t31 * t16
  t48 = t1 * t31
  t50 = jnp.log(0.2e1 * t15)
  t51 = 0.1e1 / t50
  t53 = t50 ** 2
  t54 = 0.1e1 / t53
  t58 = f.my_piecewise3(t6, -0.8e1 / 0.3e1 * t7 * t12 * t21 - t7 * t29 * t44, -0.4e1 / 0.9e1 * t48 * t51 + 0.4e1 / 0.9e1 * t48 * t54)
  t59 = t58 * t2
  t61 = 3 ** (0.1e1 / 0.3e1)
  t64 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t65 = 4 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t74 = f.my_piecewise3(t6, t7 * t26 * t21, t5 * t51 / 0.3e1)
  t75 = -params.alpha * t61 * t64 * t66 / 0.2e1 - t74
  t76 = 0.1e1 / t10
  t77 = t75 * t76
  t79 = r0 + r1
  t80 = t8 ** 2
  t82 = 0.1e1 / t10 / t80
  t93 = t44 ** 2
  t98 = 0.1e1 / t2 / t9
  t106 = s0 ** 2
  t122 = t1 * t98
  t132 = f.my_piecewise3(t6, 0.88e2 / 0.9e1 * t7 * t82 * t21 + 0.16e2 / 0.3e1 * t7 * t12 * t28 * t44 + 0.2e1 * t7 * t26 / t27 / t20 * t93 - t7 * t29 * (0.28e2 / 0.3e1 * t13 * t98 * t16 + 0.20e2 * t7 * t82 * params.gamma * t40 - 0.16e2 / 0.3e1 * params.beta * t106 / t2 / t80 / t9 * t35 * params.gamma / t39 / t38), 0.28e2 / 0.27e2 * t122 * t51 - 0.44e2 / 0.27e2 * t122 * t54 + 0.32e2 / 0.27e2 * t122 / t53 / t50)
  d11 = -0.2e1 * t59 + 0.2e1 / 0.3e1 * t77 - t79 * t132 * t2 - 0.2e1 / 0.3e1 * t79 * t58 * t76 - 0.2e1 / 0.9e1 * t79 * t75 / t10 / r0
  d12 = -t59 + t77 / 0.3e1
  d22 = 0.0e0
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t4 = 3 ** (0.1e1 / 0.3e1)
  t7 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t8 = 4 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t13 = jnp.sqrt(s0)
  t14 = 2 ** (0.1e1 / 0.3e1)
  t15 = t13 * t14
  t16 = t1 * r0
  t17 = 0.1e1 / t16
  t19 = t15 * t17 < 0.300e3
  t20 = params.beta * s0
  t21 = t14 ** 2
  t22 = r0 ** 2
  t24 = 0.1e1 / t2 / t22
  t25 = t21 * t24
  t26 = params.beta * t13
  t27 = t14 * t17
  t29 = params.gamma * t13 * t27
  t30 = jnp.arcsinh(t29)
  t31 = t27 * t30
  t34 = 0.3e1 * t26 * t31 + 0.1e1
  t35 = 0.1e1 / t34
  t39 = jnp.log(0.2e1 * t29)
  t40 = 0.1e1 / t39
  t41 = t17 * t40
  t44 = f.my_piecewise3(t19, t20 * t25 * t35, t15 * t41 / 0.3e1)
  t49 = t22 * r0
  t51 = 0.1e1 / t2 / t49
  t56 = t20 * t21
  t57 = t34 ** 2
  t58 = 0.1e1 / t57
  t59 = t24 * t58
  t61 = 0.1e1 / t1 / t22
  t63 = t14 * t61 * t30
  t66 = params.gamma ** 2
  t69 = t66 * s0 * t25 + 0.1e1
  t70 = jnp.sqrt(t69)
  t71 = 0.1e1 / t70
  t72 = t51 * params.gamma * t71
  t75 = -0.4e1 * t26 * t63 - 0.4e1 * t56 * t72
  t76 = t59 * t75
  t79 = t61 * t40
  t81 = t39 ** 2
  t82 = 0.1e1 / t81
  t83 = t61 * t82
  t87 = f.my_piecewise3(t19, -0.8e1 / 0.3e1 * t20 * t21 * t51 * t35 - t56 * t76, -0.4e1 / 0.9e1 * t15 * t79 + 0.4e1 / 0.9e1 * t15 * t83)
  t91 = t22 ** 2
  t93 = 0.1e1 / t2 / t91
  t98 = t51 * t58
  t104 = t24 / t57 / t34
  t105 = t75 ** 2
  t110 = 0.1e1 / t1 / t49
  t119 = s0 ** 2
  t125 = t66 * params.gamma
  t128 = 0.1e1 / t70 / t69
  t143 = 0.1e1 / t81 / t39
  t148 = f.my_piecewise3(t19, 0.88e2 / 0.9e1 * t20 * t21 * t93 * t35 + 0.16e2 / 0.3e1 * t56 * t98 * t75 + 0.2e1 * t56 * t104 * t105 - t56 * t59 * (0.28e2 / 0.3e1 * t26 * t14 * t110 * t30 + 0.20e2 * t56 * t93 * params.gamma * t71 - 0.32e2 / 0.3e1 * params.beta * t119 * t14 / t1 / t91 / t49 * t125 * t128), 0.28e2 / 0.27e2 * t15 * t110 * t40 - 0.44e2 / 0.27e2 * t15 * t110 * t82 + 0.32e2 / 0.27e2 * t15 * t110 * t143)
  v2rho2_0_ = 0.2e1 / 0.9e1 / t2 * (-params.alpha * t4 * t7 * t9 / 0.2e1 - t44) * t21 - 0.4e1 / 0.3e1 * t1 * t87 * t21 - t16 * t148 * t21 / 0.2e1
  t152 = params.beta * t21
  t155 = 0.1e1 / t13
  t156 = params.beta * t155
  t159 = t24 * params.gamma * t71
  t162 = 0.3e1 / 0.2e1 * t152 * t159 + 0.3e1 / 0.2e1 * t156 * t31
  t163 = t59 * t162
  t166 = t155 * t14
  t172 = f.my_piecewise3(t19, t152 * t24 * t35 - t56 * t163, -t166 * t17 * t82 / 0.6e1 + t166 * t41 / 0.6e1)
  t191 = params.beta * t14
  t212 = f.my_piecewise3(t19, -0.8e1 / 0.3e1 * t152 * t51 * t35 - t152 * t76 + 0.8e1 / 0.3e1 * t56 * t98 * t162 + 0.2e1 * t56 * t104 * t162 * t75 - t56 * t59 * (-0.2e1 * t156 * t63 - 0.6e1 * t152 * t72 + 0.4e1 * t191 / t1 / t91 / t22 * t125 * t128 * s0), -0.2e1 / 0.9e1 * t166 * t79 + 0.4e1 / 0.9e1 * t166 * t83 - 0.4e1 / 0.9e1 * t166 * t61 * t143)
  v2rhosigma_0_ = -0.2e1 / 0.3e1 * t1 * t172 * t21 - t16 * t212 * t21 / 0.2e1
  t218 = t162 ** 2
  t223 = 0.1e1 / t13 / s0
  t243 = t223 * t14
  t250 = f.my_piecewise3(t19, -0.2e1 * t152 * t163 + 0.2e1 * t56 * t104 * t218 - t56 * t59 * (-0.3e1 / 0.4e1 * params.beta * t223 * t31 + 0.3e1 / 0.4e1 * params.beta / s0 * t21 * t159 - 0.3e1 / 0.2e1 * t191 / t1 / t91 / r0 * t125 * t128), -t243 * t41 / 0.12e2 + t243 * t17 * t143 / 0.6e1)
  v2sigma2_0_ = -t16 * t250 * t21 / 0.2e1
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

