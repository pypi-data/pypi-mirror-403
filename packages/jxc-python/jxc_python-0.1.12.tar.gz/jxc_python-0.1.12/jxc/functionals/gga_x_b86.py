"""Generated from gga_x_b86.mpl."""

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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  b86_f = lambda x: 1 + params_beta * x ** 2 / (1 + params_gamma * x ** 2) ** params_omega

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, b86_f, rs, zeta, xs0, xs1)

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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  b86_f = lambda x: 1 + params_beta * x ** 2 / (1 + params_gamma * x ** 2) ** params_omega

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, b86_f, rs, zeta, xs0, xs1)

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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  b86_f = lambda x: 1 + params_beta * x ** 2 / (1 + params_gamma * x ** 2) ** params_omega

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, b86_f, rs, zeta, xs0, xs1)

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
  t28 = params.beta * s0
  t29 = r0 ** 2
  t30 = r0 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t33 = 0.1e1 / t31 / t29
  t36 = params.gamma * s0 * t33 + 0.1e1
  t37 = t36 ** params.omega
  t38 = 0.1e1 / t37
  t41 = t28 * t33 * t38 + 0.1e1
  t45 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t41)
  t46 = r1 <= f.p.dens_threshold
  t47 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t48 = 0.1e1 + t47
  t49 = t48 <= f.p.zeta_threshold
  t50 = t48 ** (0.1e1 / 0.3e1)
  t52 = f.my_piecewise3(t49, t22, t50 * t48)
  t53 = t52 * t26
  t54 = params.beta * s2
  t55 = r1 ** 2
  t56 = r1 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t59 = 0.1e1 / t57 / t55
  t62 = params.gamma * s2 * t59 + 0.1e1
  t63 = t62 ** params.omega
  t64 = 0.1e1 / t63
  t67 = t54 * t59 * t64 + 0.1e1
  t71 = f.my_piecewise3(t46, 0, -0.3e1 / 0.8e1 * t5 * t53 * t67)
  t72 = t6 ** 2
  t74 = t16 / t72
  t75 = t7 - t74
  t76 = f.my_piecewise5(t10, 0, t14, 0, t75)
  t79 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t76)
  t84 = t26 ** 2
  t85 = 0.1e1 / t84
  t89 = t5 * t25 * t85 * t41 / 0.8e1
  t95 = s0 ** 2
  t97 = t29 ** 2
  t105 = t38 * params.omega * params.gamma / t36
  t113 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t79 * t26 * t41 - t89 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.8e1 / 0.3e1 * t28 / t31 / t29 / r0 * t38 + 0.8e1 / 0.3e1 * params.beta * t95 / t30 / t97 / t29 * t105))
  t115 = f.my_piecewise5(t14, 0, t10, 0, -t75)
  t118 = f.my_piecewise3(t49, 0, 0.4e1 / 0.3e1 * t50 * t115)
  t126 = t5 * t52 * t85 * t67 / 0.8e1
  t128 = f.my_piecewise3(t46, 0, -0.3e1 / 0.8e1 * t5 * t118 * t26 * t67 - t126)
  vrho_0_ = t45 + t71 + t6 * (t113 + t128)
  t131 = -t7 - t74
  t132 = f.my_piecewise5(t10, 0, t14, 0, t131)
  t135 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t132)
  t141 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t135 * t26 * t41 - t89)
  t143 = f.my_piecewise5(t14, 0, t10, 0, -t131)
  t146 = f.my_piecewise3(t49, 0, 0.4e1 / 0.3e1 * t50 * t143)
  t156 = s2 ** 2
  t158 = t55 ** 2
  t166 = t64 * params.omega * params.gamma / t62
  t174 = f.my_piecewise3(t46, 0, -0.3e1 / 0.8e1 * t5 * t146 * t26 * t67 - t126 - 0.3e1 / 0.8e1 * t5 * t53 * (-0.8e1 / 0.3e1 * t54 / t57 / t55 / r1 * t64 + 0.8e1 / 0.3e1 * params.beta * t156 / t56 / t158 / t55 * t166))
  vrho_1_ = t45 + t71 + t6 * (t141 + t174)
  t188 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (params.beta * t33 * t38 - t28 / t30 / t97 / r0 * t105))
  vsigma_0_ = t6 * t188
  vsigma_1_ = 0.0e0
  t200 = f.my_piecewise3(t46, 0, -0.3e1 / 0.8e1 * t5 * t53 * (params.beta * t59 * t64 - t54 / t56 / t158 / r1 * t166))
  vsigma_2_ = t6 * t200
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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  b86_f = lambda x: 1 + params_beta * x ** 2 / (1 + params_gamma * x ** 2) ** params_omega

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, b86_f, rs, zeta, xs0, xs1)

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
  t20 = params.beta * s0
  t21 = 2 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = r0 ** 2
  t24 = t18 ** 2
  t26 = 0.1e1 / t24 / t23
  t27 = t22 * t26
  t30 = params.gamma * s0 * t27 + 0.1e1
  t31 = t30 ** params.omega
  t32 = 0.1e1 / t31
  t35 = t20 * t27 * t32 + 0.1e1
  t39 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t35)
  t52 = s0 ** 2
  t54 = t23 ** 2
  t63 = t32 * params.omega * params.gamma / t30
  t71 = f.my_piecewise3(t2, 0, -t6 * t17 / t24 * t35 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.8e1 / 0.3e1 * t20 * t22 / t24 / t23 / r0 * t32 + 0.16e2 / 0.3e1 * params.beta * t52 * t21 / t18 / t54 / t23 * t63))
  vrho_0_ = 0.2e1 * r0 * t71 + 0.2e1 * t39
  t88 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (params.beta * t22 * t26 * t32 - 0.2e1 * t20 * t21 / t18 / t54 / r0 * t63))
  vsigma_0_ = 0.2e1 * r0 * t88
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
  t22 = params.beta * s0
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = r0 ** 2
  t27 = 0.1e1 / t19 / t25
  t28 = t24 * t27
  t31 = params.gamma * s0 * t28 + 0.1e1
  t32 = t31 ** params.omega
  t33 = 0.1e1 / t32
  t36 = t22 * t28 * t33 + 0.1e1
  t40 = t17 * t18
  t41 = t25 * r0
  t43 = 0.1e1 / t19 / t41
  t48 = s0 ** 2
  t49 = params.beta * t48
  t50 = t25 ** 2
  t53 = 0.1e1 / t18 / t50 / t25
  t56 = t33 * params.omega
  t57 = 0.1e1 / t31
  t59 = t56 * params.gamma * t57
  t62 = -0.8e1 / 0.3e1 * t22 * t24 * t43 * t33 + 0.16e2 / 0.3e1 * t49 * t23 * t53 * t59
  t67 = f.my_piecewise3(t2, 0, -t6 * t21 * t36 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t40 * t62)
  t93 = t50 ** 2
  t96 = params.beta * t48 * s0 / t93 / t25
  t97 = params.omega ** 2
  t99 = params.gamma ** 2
  t100 = t31 ** 2
  t102 = t99 / t100
  t103 = t33 * t97 * t102
  t106 = t56 * t102
  t114 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t36 / 0.12e2 - t6 * t21 * t62 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t40 * (0.88e2 / 0.9e1 * t22 * t24 / t19 / t50 * t33 - 0.48e2 * t49 * t23 / t18 / t50 / t41 * t59 + 0.256e3 / 0.9e1 * t96 * t103 + 0.256e3 / 0.9e1 * t96 * t106))
  v2rho2_0_ = 0.2e1 * r0 * t114 + 0.4e1 * t67
  t117 = params.beta * t24
  t122 = 0.1e1 / t18 / t50 / r0
  t127 = -0.2e1 * t22 * t23 * t122 * t59 + t117 * t27 * t33
  t131 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t40 * t127)
  t138 = params.beta * t23
  t148 = t49 / t93 / r0
  t158 = f.my_piecewise3(t2, 0, -t6 * t21 * t127 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t40 * (-0.8e1 / 0.3e1 * t117 * t43 * t33 + 0.16e2 * t138 * t53 * t33 * params.omega * params.gamma * s0 * t57 - 0.32e2 / 0.3e1 * t148 * t103 - 0.32e2 / 0.3e1 * t148 * t106))
  v2rhosigma_0_ = 0.2e1 * r0 * t158 + 0.2e1 * t131
  t164 = t22 / t93
  t172 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t40 * (-0.4e1 * t138 * t122 * t59 + 0.4e1 * t164 * t103 + 0.4e1 * t164 * t106))
  v2sigma2_0_ = 0.2e1 * r0 * t172
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
  t23 = params.beta * s0
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = r0 ** 2
  t28 = 0.1e1 / t19 / t26
  t29 = t25 * t28
  t32 = params.gamma * s0 * t29 + 0.1e1
  t33 = t32 ** params.omega
  t34 = 0.1e1 / t33
  t37 = t23 * t29 * t34 + 0.1e1
  t42 = t17 / t19
  t43 = t26 * r0
  t50 = s0 ** 2
  t51 = params.beta * t50
  t52 = t26 ** 2
  t58 = t34 * params.omega
  t61 = t58 * params.gamma / t32
  t64 = -0.8e1 / 0.3e1 * t23 * t25 / t19 / t43 * t34 + 0.16e2 / 0.3e1 * t51 * t24 / t18 / t52 / t26 * t61
  t68 = t17 * t18
  t83 = params.beta * t50 * s0
  t84 = t52 ** 2
  t87 = t83 / t84 / t26
  t88 = params.omega ** 2
  t90 = params.gamma ** 2
  t91 = t32 ** 2
  t93 = t90 / t91
  t94 = t34 * t88 * t93
  t97 = t58 * t93
  t100 = 0.88e2 / 0.9e1 * t23 * t25 / t19 / t52 * t34 - 0.48e2 * t51 * t24 / t18 / t52 / t43 * t61 + 0.256e3 / 0.9e1 * t87 * t94 + 0.256e3 / 0.9e1 * t87 * t97
  t105 = f.my_piecewise3(t2, 0, t6 * t22 * t37 / 0.12e2 - t6 * t42 * t64 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t68 * t100)
  t117 = t52 * r0
  t132 = t83 / t84 / t43
  t137 = t50 ** 2
  t143 = params.beta * t137 / t19 / t84 / t117 * t34
  t145 = t90 * params.gamma
  t149 = 0.1e1 / t91 / t32 * t25
  t166 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t28 * t37 + t6 * t22 * t64 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t42 * t100 - 0.3e1 / 0.8e1 * t6 * t68 * (-0.1232e4 / 0.27e2 * t23 * t25 / t19 / t117 * t34 + 0.10912e5 / 0.27e2 * t51 * t24 / t18 / t84 * t61 - 0.4864e4 / 0.9e1 * t132 * t94 - 0.4864e4 / 0.9e1 * t132 * t97 + 0.2048e4 / 0.27e2 * t143 * t88 * params.omega * t145 * t149 + 0.2048e4 / 0.9e1 * t143 * t88 * t145 * t149 + 0.4096e4 / 0.27e2 * t143 * params.omega * t145 * t149))
  v3rho3_0_ = 0.2e1 * r0 * t166 + 0.6e1 * t105

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
  t24 = params.beta * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = t26 * t22
  t30 = params.gamma * s0 * t27 + 0.1e1
  t31 = t30 ** params.omega
  t32 = 0.1e1 / t31
  t35 = t24 * t27 * t32 + 0.1e1
  t41 = t17 / t20 / r0
  t42 = t18 * r0
  t44 = 0.1e1 / t20 / t42
  t49 = s0 ** 2
  t50 = params.beta * t49
  t51 = t18 ** 2
  t52 = t51 * t18
  t57 = t32 * params.omega
  t60 = t57 * params.gamma / t30
  t63 = -0.8e1 / 0.3e1 * t24 * t26 * t44 * t32 + 0.16e2 / 0.3e1 * t50 * t25 / t19 / t52 * t60
  t68 = t17 / t20
  t83 = params.beta * t49 * s0
  t84 = t51 ** 2
  t87 = t83 / t84 / t18
  t88 = params.omega ** 2
  t90 = params.gamma ** 2
  t91 = t30 ** 2
  t93 = t90 / t91
  t94 = t32 * t88 * t93
  t97 = t57 * t93
  t100 = 0.88e2 / 0.9e1 * t24 * t26 / t20 / t51 * t32 - 0.48e2 * t50 * t25 / t19 / t51 / t42 * t60 + 0.256e3 / 0.9e1 * t87 * t94 + 0.256e3 / 0.9e1 * t87 * t97
  t104 = t17 * t19
  t105 = t51 * r0
  t120 = t83 / t84 / t42
  t125 = t49 ** 2
  t126 = params.beta * t125
  t131 = t126 / t20 / t84 / t105 * t32
  t132 = t88 * params.omega
  t133 = t90 * params.gamma
  t137 = 0.1e1 / t91 / t30 * t26
  t138 = t132 * t133 * t137
  t142 = t88 * t133 * t137
  t146 = params.omega * t133 * t137
  t149 = -0.1232e4 / 0.27e2 * t24 * t26 / t20 / t105 * t32 + 0.10912e5 / 0.27e2 * t50 * t25 / t19 / t84 * t60 - 0.4864e4 / 0.9e1 * t120 * t94 - 0.4864e4 / 0.9e1 * t120 * t97 + 0.2048e4 / 0.27e2 * t131 * t138 + 0.2048e4 / 0.9e1 * t131 * t142 + 0.4096e4 / 0.27e2 * t131 * t146
  t154 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t35 + t6 * t41 * t63 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t68 * t100 - 0.3e1 / 0.8e1 * t6 * t104 * t149)
  t184 = t83 / t84 / t51
  t193 = t126 / t20 / t84 / t52 * t32
  t202 = t84 ** 2
  t207 = params.beta * t125 * s0 / t19 / t202 / r0 * t32
  t208 = t88 ** 2
  t209 = t90 ** 2
  t211 = t91 ** 2
  t213 = 0.1e1 / t211 * t25
  t229 = 0.20944e5 / 0.81e2 * t24 * t26 / t20 / t52 * t32 - 0.97504e5 / 0.27e2 * t50 * t25 / t19 / t84 / r0 * t60 + 0.656128e6 / 0.81e2 * t184 * t94 + 0.656128e6 / 0.81e2 * t184 * t97 - 0.200704e6 / 0.81e2 * t193 * t138 - 0.200704e6 / 0.27e2 * t193 * t142 - 0.401408e6 / 0.81e2 * t193 * t146 + 0.32768e5 / 0.81e2 * t207 * t208 * t209 * t213 + 0.65536e5 / 0.27e2 * t207 * t132 * t209 * t213 + 0.360448e6 / 0.81e2 * t207 * t88 * t209 * t213 + 0.65536e5 / 0.27e2 * t207 * params.omega * t209 * t213
  t234 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t44 * t35 - 0.5e1 / 0.9e1 * t6 * t23 * t63 + t6 * t41 * t100 / 0.2e1 - t6 * t68 * t149 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t104 * t229)
  v4rho4_0_ = 0.2e1 * r0 * t234 + 0.8e1 * t154

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
  t32 = params.beta * s0
  t33 = r0 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / t33
  t40 = params.gamma * s0 * t37 + 0.1e1
  t41 = t40 ** params.omega
  t42 = 0.1e1 / t41
  t45 = t32 * t37 * t42 + 0.1e1
  t49 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t50 = t49 * f.p.zeta_threshold
  t52 = f.my_piecewise3(t20, t50, t21 * t19)
  t53 = t30 ** 2
  t54 = 0.1e1 / t53
  t55 = t52 * t54
  t58 = t5 * t55 * t45 / 0.8e1
  t59 = t52 * t30
  t60 = t33 * r0
  t65 = s0 ** 2
  t66 = params.beta * t65
  t67 = t33 ** 2
  t72 = t42 * params.omega
  t75 = t72 * params.gamma / t40
  t78 = -0.8e1 / 0.3e1 * t32 / t35 / t60 * t42 + 0.8e1 / 0.3e1 * t66 / t34 / t67 / t33 * t75
  t83 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t45 - t58 - 0.3e1 / 0.8e1 * t5 * t59 * t78)
  t85 = r1 <= f.p.dens_threshold
  t86 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t87 = 0.1e1 + t86
  t88 = t87 <= f.p.zeta_threshold
  t89 = t87 ** (0.1e1 / 0.3e1)
  t91 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t94 = f.my_piecewise3(t88, 0, 0.4e1 / 0.3e1 * t89 * t91)
  t95 = t94 * t30
  t96 = params.beta * s2
  t97 = r1 ** 2
  t98 = r1 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t101 = 0.1e1 / t99 / t97
  t104 = params.gamma * s2 * t101 + 0.1e1
  t105 = t104 ** params.omega
  t106 = 0.1e1 / t105
  t109 = t96 * t101 * t106 + 0.1e1
  t114 = f.my_piecewise3(t88, t50, t89 * t87)
  t115 = t114 * t54
  t118 = t5 * t115 * t109 / 0.8e1
  t120 = f.my_piecewise3(t85, 0, -0.3e1 / 0.8e1 * t5 * t95 * t109 - t118)
  t122 = t21 ** 2
  t123 = 0.1e1 / t122
  t124 = t26 ** 2
  t129 = t16 / t22 / t6
  t131 = -0.2e1 * t23 + 0.2e1 * t129
  t132 = f.my_piecewise5(t10, 0, t14, 0, t131)
  t136 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t123 * t124 + 0.4e1 / 0.3e1 * t21 * t132)
  t143 = t5 * t29 * t54 * t45
  t149 = 0.1e1 / t53 / t6
  t153 = t5 * t52 * t149 * t45 / 0.12e2
  t155 = t5 * t55 * t78
  t170 = t67 ** 2
  t173 = params.beta * t65 * s0 / t170 / t33
  t174 = params.omega ** 2
  t176 = params.gamma ** 2
  t177 = t40 ** 2
  t179 = t176 / t177
  t191 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t136 * t30 * t45 - t143 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t78 + t153 - t155 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t59 * (0.88e2 / 0.9e1 * t32 / t35 / t67 * t42 - 0.24e2 * t66 / t34 / t67 / t60 * t75 + 0.64e2 / 0.9e1 * t173 * t42 * t174 * t179 + 0.64e2 / 0.9e1 * t173 * t72 * t179))
  t192 = t89 ** 2
  t193 = 0.1e1 / t192
  t194 = t91 ** 2
  t198 = f.my_piecewise5(t14, 0, t10, 0, -t131)
  t202 = f.my_piecewise3(t88, 0, 0.4e1 / 0.9e1 * t193 * t194 + 0.4e1 / 0.3e1 * t89 * t198)
  t209 = t5 * t94 * t54 * t109
  t214 = t5 * t114 * t149 * t109 / 0.12e2
  t216 = f.my_piecewise3(t85, 0, -0.3e1 / 0.8e1 * t5 * t202 * t30 * t109 - t209 / 0.4e1 + t214)
  d11 = 0.2e1 * t83 + 0.2e1 * t120 + t6 * (t191 + t216)
  t219 = -t7 - t24
  t220 = f.my_piecewise5(t10, 0, t14, 0, t219)
  t223 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t220)
  t224 = t223 * t30
  t229 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t224 * t45 - t58)
  t231 = f.my_piecewise5(t14, 0, t10, 0, -t219)
  t234 = f.my_piecewise3(t88, 0, 0.4e1 / 0.3e1 * t89 * t231)
  t235 = t234 * t30
  t239 = t114 * t30
  t240 = t97 * r1
  t245 = s2 ** 2
  t246 = params.beta * t245
  t247 = t97 ** 2
  t252 = t106 * params.omega
  t255 = t252 * params.gamma / t104
  t258 = -0.8e1 / 0.3e1 * t96 / t99 / t240 * t106 + 0.8e1 / 0.3e1 * t246 / t98 / t247 / t97 * t255
  t263 = f.my_piecewise3(t85, 0, -0.3e1 / 0.8e1 * t5 * t235 * t109 - t118 - 0.3e1 / 0.8e1 * t5 * t239 * t258)
  t267 = 0.2e1 * t129
  t268 = f.my_piecewise5(t10, 0, t14, 0, t267)
  t272 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t123 * t220 * t26 + 0.4e1 / 0.3e1 * t21 * t268)
  t279 = t5 * t223 * t54 * t45
  t287 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t272 * t30 * t45 - t279 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t224 * t78 - t143 / 0.8e1 + t153 - t155 / 0.8e1)
  t291 = f.my_piecewise5(t14, 0, t10, 0, -t267)
  t295 = f.my_piecewise3(t88, 0, 0.4e1 / 0.9e1 * t193 * t231 * t91 + 0.4e1 / 0.3e1 * t89 * t291)
  t302 = t5 * t234 * t54 * t109
  t309 = t5 * t115 * t258
  t312 = f.my_piecewise3(t85, 0, -0.3e1 / 0.8e1 * t5 * t295 * t30 * t109 - t302 / 0.8e1 - t209 / 0.8e1 + t214 - 0.3e1 / 0.8e1 * t5 * t95 * t258 - t309 / 0.8e1)
  d12 = t83 + t120 + t229 + t263 + t6 * (t287 + t312)
  t317 = t220 ** 2
  t321 = 0.2e1 * t23 + 0.2e1 * t129
  t322 = f.my_piecewise5(t10, 0, t14, 0, t321)
  t326 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t123 * t317 + 0.4e1 / 0.3e1 * t21 * t322)
  t333 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t326 * t30 * t45 - t279 / 0.4e1 + t153)
  t334 = t231 ** 2
  t338 = f.my_piecewise5(t14, 0, t10, 0, -t321)
  t342 = f.my_piecewise3(t88, 0, 0.4e1 / 0.9e1 * t193 * t334 + 0.4e1 / 0.3e1 * t89 * t338)
  t365 = t247 ** 2
  t368 = params.beta * t245 * s2 / t365 / t97
  t370 = t104 ** 2
  t372 = t176 / t370
  t384 = f.my_piecewise3(t85, 0, -0.3e1 / 0.8e1 * t5 * t342 * t30 * t109 - t302 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t235 * t258 + t214 - t309 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t239 * (0.88e2 / 0.9e1 * t96 / t99 / t247 * t106 - 0.24e2 * t246 / t98 / t247 / t240 * t255 + 0.64e2 / 0.9e1 * t368 * t106 * t174 * t372 + 0.64e2 / 0.9e1 * t368 * t252 * t372))
  d22 = 0.2e1 * t229 + 0.2e1 * t263 + t6 * (t333 + t384)
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
  t44 = params.beta * s0
  t45 = r0 ** 2
  t46 = r0 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t49 = 0.1e1 / t47 / t45
  t52 = params.gamma * s0 * t49 + 0.1e1
  t53 = t52 ** params.omega
  t54 = 0.1e1 / t53
  t57 = t44 * t49 * t54 + 0.1e1
  t63 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t64 = t42 ** 2
  t65 = 0.1e1 / t64
  t66 = t63 * t65
  t70 = t63 * t42
  t71 = t45 * r0
  t76 = s0 ** 2
  t77 = params.beta * t76
  t78 = t45 ** 2
  t83 = t54 * params.omega
  t86 = t83 * params.gamma / t52
  t89 = -0.8e1 / 0.3e1 * t44 / t47 / t71 * t54 + 0.8e1 / 0.3e1 * t77 / t46 / t78 / t45 * t86
  t93 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t94 = t93 * f.p.zeta_threshold
  t96 = f.my_piecewise3(t20, t94, t21 * t19)
  t98 = 0.1e1 / t64 / t6
  t99 = t96 * t98
  t103 = t96 * t65
  t107 = t96 * t42
  t120 = params.beta * t76 * s0
  t121 = t78 ** 2
  t124 = t120 / t121 / t45
  t125 = params.omega ** 2
  t126 = t54 * t125
  t127 = params.gamma ** 2
  t128 = t52 ** 2
  t130 = t127 / t128
  t131 = t126 * t130
  t134 = t83 * t130
  t137 = 0.88e2 / 0.9e1 * t44 / t47 / t78 * t54 - 0.24e2 * t77 / t46 / t78 / t71 * t86 + 0.64e2 / 0.9e1 * t124 * t131 + 0.64e2 / 0.9e1 * t124 * t134
  t142 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t57 - t5 * t66 * t57 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t70 * t89 + t5 * t99 * t57 / 0.12e2 - t5 * t103 * t89 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t107 * t137)
  t144 = r1 <= f.p.dens_threshold
  t145 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t146 = 0.1e1 + t145
  t147 = t146 <= f.p.zeta_threshold
  t148 = t146 ** (0.1e1 / 0.3e1)
  t149 = t148 ** 2
  t150 = 0.1e1 / t149
  t152 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t153 = t152 ** 2
  t157 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t161 = f.my_piecewise3(t147, 0, 0.4e1 / 0.9e1 * t150 * t153 + 0.4e1 / 0.3e1 * t148 * t157)
  t164 = r1 ** 2
  t165 = r1 ** (0.1e1 / 0.3e1)
  t166 = t165 ** 2
  t168 = 0.1e1 / t166 / t164
  t172 = (params.gamma * s2 * t168 + 0.1e1) ** params.omega
  t176 = 0.1e1 + params.beta * s2 * t168 / t172
  t182 = f.my_piecewise3(t147, 0, 0.4e1 / 0.3e1 * t148 * t152)
  t188 = f.my_piecewise3(t147, t94, t148 * t146)
  t194 = f.my_piecewise3(t144, 0, -0.3e1 / 0.8e1 * t5 * t161 * t42 * t176 - t5 * t182 * t65 * t176 / 0.4e1 + t5 * t188 * t98 * t176 / 0.12e2)
  t204 = t24 ** 2
  t208 = 0.6e1 * t33 - 0.6e1 * t16 / t204
  t209 = f.my_piecewise5(t10, 0, t14, 0, t208)
  t213 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t209)
  t236 = 0.1e1 / t64 / t24
  t247 = t78 * r0
  t260 = t120 / t121 / t71
  t265 = t76 ** 2
  t270 = params.beta * t265 / t47 / t121 / t247
  t276 = t127 * params.gamma / t128 / t52
  t291 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t213 * t42 * t57 - 0.3e1 / 0.8e1 * t5 * t41 * t65 * t57 - 0.9e1 / 0.8e1 * t5 * t43 * t89 + t5 * t63 * t98 * t57 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t66 * t89 - 0.9e1 / 0.8e1 * t5 * t70 * t137 - 0.5e1 / 0.36e2 * t5 * t96 * t236 * t57 + t5 * t99 * t89 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t103 * t137 - 0.3e1 / 0.8e1 * t5 * t107 * (-0.1232e4 / 0.27e2 * t44 / t47 / t247 * t54 + 0.5456e4 / 0.27e2 * t77 / t46 / t121 * t86 - 0.1216e4 / 0.9e1 * t260 * t131 - 0.1216e4 / 0.9e1 * t260 * t134 + 0.512e3 / 0.27e2 * t270 * t54 * t125 * params.omega * t276 + 0.512e3 / 0.9e1 * t270 * t126 * t276 + 0.1024e4 / 0.27e2 * t270 * t83 * t276))
  t301 = f.my_piecewise5(t14, 0, t10, 0, -t208)
  t305 = f.my_piecewise3(t147, 0, -0.8e1 / 0.27e2 / t149 / t146 * t153 * t152 + 0.4e1 / 0.3e1 * t150 * t152 * t157 + 0.4e1 / 0.3e1 * t148 * t301)
  t323 = f.my_piecewise3(t144, 0, -0.3e1 / 0.8e1 * t5 * t305 * t42 * t176 - 0.3e1 / 0.8e1 * t5 * t161 * t65 * t176 + t5 * t182 * t98 * t176 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t188 * t236 * t176)
  d111 = 0.3e1 * t142 + 0.3e1 * t194 + t6 * (t291 + t323)

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
  t56 = params.beta * s0
  t57 = r0 ** 2
  t58 = r0 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t61 = 0.1e1 / t59 / t57
  t64 = params.gamma * s0 * t61 + 0.1e1
  t65 = t64 ** params.omega
  t66 = 0.1e1 / t65
  t69 = t56 * t61 * t66 + 0.1e1
  t78 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t79 = t54 ** 2
  t80 = 0.1e1 / t79
  t81 = t78 * t80
  t85 = t78 * t54
  t86 = t57 * r0
  t91 = s0 ** 2
  t92 = params.beta * t91
  t93 = t57 ** 2
  t94 = t93 * t57
  t98 = t66 * params.omega
  t101 = t98 * params.gamma / t64
  t104 = -0.8e1 / 0.3e1 * t56 / t59 / t86 * t66 + 0.8e1 / 0.3e1 * t92 / t58 / t94 * t101
  t110 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t112 = 0.1e1 / t79 / t6
  t113 = t110 * t112
  t117 = t110 * t80
  t121 = t110 * t54
  t134 = params.beta * t91 * s0
  t135 = t93 ** 2
  t138 = t134 / t135 / t57
  t139 = params.omega ** 2
  t140 = t66 * t139
  t141 = params.gamma ** 2
  t142 = t64 ** 2
  t144 = t141 / t142
  t145 = t140 * t144
  t148 = t98 * t144
  t151 = 0.88e2 / 0.9e1 * t56 / t59 / t93 * t66 - 0.24e2 * t92 / t58 / t93 / t86 * t101 + 0.64e2 / 0.9e1 * t138 * t145 + 0.64e2 / 0.9e1 * t138 * t148
  t155 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t156 = t155 * f.p.zeta_threshold
  t158 = f.my_piecewise3(t20, t156, t21 * t19)
  t160 = 0.1e1 / t79 / t25
  t161 = t158 * t160
  t165 = t158 * t112
  t169 = t158 * t80
  t173 = t158 * t54
  t174 = t93 * r0
  t187 = t134 / t135 / t86
  t192 = t91 ** 2
  t193 = params.beta * t192
  t197 = t193 / t59 / t135 / t174
  t199 = t66 * t139 * params.omega
  t203 = t141 * params.gamma / t142 / t64
  t204 = t199 * t203
  t207 = t140 * t203
  t210 = t98 * t203
  t213 = -0.1232e4 / 0.27e2 * t56 / t59 / t174 * t66 + 0.5456e4 / 0.27e2 * t92 / t58 / t135 * t101 - 0.1216e4 / 0.9e1 * t187 * t145 - 0.1216e4 / 0.9e1 * t187 * t148 + 0.512e3 / 0.27e2 * t197 * t204 + 0.512e3 / 0.9e1 * t197 * t207 + 0.1024e4 / 0.27e2 * t197 * t210
  t218 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t69 - 0.3e1 / 0.8e1 * t5 * t81 * t69 - 0.9e1 / 0.8e1 * t5 * t85 * t104 + t5 * t113 * t69 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t117 * t104 - 0.9e1 / 0.8e1 * t5 * t121 * t151 - 0.5e1 / 0.36e2 * t5 * t161 * t69 + t5 * t165 * t104 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t169 * t151 - 0.3e1 / 0.8e1 * t5 * t173 * t213)
  t220 = r1 <= f.p.dens_threshold
  t221 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t222 = 0.1e1 + t221
  t223 = t222 <= f.p.zeta_threshold
  t224 = t222 ** (0.1e1 / 0.3e1)
  t225 = t224 ** 2
  t227 = 0.1e1 / t225 / t222
  t229 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t230 = t229 ** 2
  t234 = 0.1e1 / t225
  t235 = t234 * t229
  t237 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t241 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t245 = f.my_piecewise3(t223, 0, -0.8e1 / 0.27e2 * t227 * t230 * t229 + 0.4e1 / 0.3e1 * t235 * t237 + 0.4e1 / 0.3e1 * t224 * t241)
  t248 = r1 ** 2
  t249 = r1 ** (0.1e1 / 0.3e1)
  t250 = t249 ** 2
  t252 = 0.1e1 / t250 / t248
  t256 = (params.gamma * s2 * t252 + 0.1e1) ** params.omega
  t260 = 0.1e1 + params.beta * s2 * t252 / t256
  t269 = f.my_piecewise3(t223, 0, 0.4e1 / 0.9e1 * t234 * t230 + 0.4e1 / 0.3e1 * t224 * t237)
  t276 = f.my_piecewise3(t223, 0, 0.4e1 / 0.3e1 * t224 * t229)
  t282 = f.my_piecewise3(t223, t156, t224 * t222)
  t288 = f.my_piecewise3(t220, 0, -0.3e1 / 0.8e1 * t5 * t245 * t54 * t260 - 0.3e1 / 0.8e1 * t5 * t269 * t80 * t260 + t5 * t276 * t112 * t260 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t282 * t160 * t260)
  t320 = t134 / t135 / t93
  t328 = t193 / t59 / t135 / t94
  t337 = t135 ** 2
  t341 = params.beta * t192 * s0 / t58 / t337 / r0
  t342 = t139 ** 2
  t344 = t141 ** 2
  t345 = t142 ** 2
  t347 = t344 / t345
  t360 = 0.20944e5 / 0.81e2 * t56 / t59 / t94 * t66 - 0.48752e5 / 0.27e2 * t92 / t58 / t135 / r0 * t101 + 0.164032e6 / 0.81e2 * t320 * t145 + 0.164032e6 / 0.81e2 * t320 * t148 - 0.50176e5 / 0.81e2 * t328 * t204 - 0.50176e5 / 0.27e2 * t328 * t207 - 0.100352e6 / 0.81e2 * t328 * t210 + 0.4096e4 / 0.81e2 * t341 * t66 * t342 * t347 + 0.8192e4 / 0.27e2 * t341 * t199 * t347 + 0.45056e5 / 0.81e2 * t341 * t140 * t347 + 0.8192e4 / 0.27e2 * t341 * t98 * t347
  t364 = t19 ** 2
  t367 = t30 ** 2
  t373 = t41 ** 2
  t382 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t383 = f.my_piecewise5(t10, 0, t14, 0, t382)
  t387 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t364 * t367 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t373 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t383)
  t414 = 0.1e1 / t79 / t36
  t419 = t5 * t113 * t104 - 0.3e1 / 0.2e1 * t5 * t117 * t151 - 0.3e1 / 0.2e1 * t5 * t121 * t213 - 0.5e1 / 0.9e1 * t5 * t161 * t104 + t5 * t165 * t151 / 0.2e1 - t5 * t169 * t213 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t173 * t360 - 0.3e1 / 0.8e1 * t5 * t387 * t54 * t69 - 0.3e1 / 0.2e1 * t5 * t55 * t104 - 0.3e1 / 0.2e1 * t5 * t81 * t104 - 0.9e1 / 0.4e1 * t5 * t85 * t151 - t5 * t53 * t80 * t69 / 0.2e1 + t5 * t78 * t112 * t69 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t110 * t160 * t69 + 0.10e2 / 0.27e2 * t5 * t158 * t414 * t69
  t420 = f.my_piecewise3(t1, 0, t419)
  t421 = t222 ** 2
  t424 = t230 ** 2
  t430 = t237 ** 2
  t436 = f.my_piecewise5(t14, 0, t10, 0, -t382)
  t440 = f.my_piecewise3(t223, 0, 0.40e2 / 0.81e2 / t225 / t421 * t424 - 0.16e2 / 0.9e1 * t227 * t230 * t237 + 0.4e1 / 0.3e1 * t234 * t430 + 0.16e2 / 0.9e1 * t235 * t241 + 0.4e1 / 0.3e1 * t224 * t436)
  t462 = f.my_piecewise3(t220, 0, -0.3e1 / 0.8e1 * t5 * t440 * t54 * t260 - t5 * t245 * t80 * t260 / 0.2e1 + t5 * t269 * t112 * t260 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t276 * t160 * t260 + 0.10e2 / 0.27e2 * t5 * t282 * t414 * t260)
  d1111 = 0.4e1 * t218 + 0.4e1 * t288 + t6 * (t420 + t462)

  res = {'v4rho4': d1111}
  return res
