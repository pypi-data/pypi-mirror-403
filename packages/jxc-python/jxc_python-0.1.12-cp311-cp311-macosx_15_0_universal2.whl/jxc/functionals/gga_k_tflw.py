"""Generated from gga_k_tflw.mpl."""

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
  params_lambda_raw = params.lambda_
  if isinstance(params_lambda_raw, (str, bytes, dict)):
    params_lambda_ = params_lambda_raw
  else:
    try:
      params_lambda_seq = list(params_lambda_raw)
    except TypeError:
      params_lambda_ = params_lambda_raw
    else:
      params_lambda_seq = np.asarray(params_lambda_seq, dtype=np.float64)
      params_lambda_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_lambda_seq))

  tflw_f = lambda x: params_gamma + params_lambda_ / 8 * x ** 2 / K_FACTOR_C

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, tflw_f, rs, zeta, xs0, xs1)

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
  params_lambda_raw = params.lambda_
  if isinstance(params_lambda_raw, (str, bytes, dict)):
    params_lambda_ = params_lambda_raw
  else:
    try:
      params_lambda_seq = list(params_lambda_raw)
    except TypeError:
      params_lambda_ = params_lambda_raw
    else:
      params_lambda_seq = np.asarray(params_lambda_seq, dtype=np.float64)
      params_lambda_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_lambda_seq))

  tflw_f = lambda x: params_gamma + params_lambda_ / 8 * x ** 2 / K_FACTOR_C

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, tflw_f, rs, zeta, xs0, xs1)

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
  params_lambda_raw = params.lambda_
  if isinstance(params_lambda_raw, (str, bytes, dict)):
    params_lambda_ = params_lambda_raw
  else:
    try:
      params_lambda_seq = list(params_lambda_raw)
    except TypeError:
      params_lambda_ = params_lambda_raw
    else:
      params_lambda_seq = np.asarray(params_lambda_seq, dtype=np.float64)
      params_lambda_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_lambda_seq))

  tflw_f = lambda x: params_gamma + params_lambda_ / 8 * x ** 2 / K_FACTOR_C

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, tflw_f, rs, zeta, xs0, xs1)

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
  t32 = params.lambda_ * s0
  t33 = r0 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / t33
  t38 = 6 ** (0.1e1 / 0.3e1)
  t40 = jnp.pi ** 2
  t41 = t40 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t43 = 0.1e1 / t42
  t47 = params.gamma + 0.5e1 / 0.72e2 * t32 * t37 * t38 * t43
  t51 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t47)
  t52 = r1 <= f.p.dens_threshold
  t53 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t54 = 0.1e1 + t53
  t55 = t54 <= f.p.zeta_threshold
  t56 = t54 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t59 = f.my_piecewise3(t55, t24, t57 * t54)
  t60 = t59 * t30
  t61 = params.lambda_ * s2
  t62 = r1 ** 2
  t63 = r1 ** (0.1e1 / 0.3e1)
  t64 = t63 ** 2
  t66 = 0.1e1 / t64 / t62
  t71 = params.gamma + 0.5e1 / 0.72e2 * t61 * t66 * t38 * t43
  t75 = f.my_piecewise3(t52, 0, 0.3e1 / 0.20e2 * t6 * t60 * t71)
  t76 = t7 ** 2
  t78 = t17 / t76
  t79 = t8 - t78
  t80 = f.my_piecewise5(t11, 0, t15, 0, t79)
  t83 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t80)
  t88 = 0.1e1 / t29
  t92 = t6 * t28 * t88 * t47 / 0.10e2
  t93 = t6 * t31
  t103 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t83 * t30 * t47 + t92 - t93 * t32 / t35 / t33 / r0 * t38 * t43 / 0.36e2)
  t105 = f.my_piecewise5(t15, 0, t11, 0, -t79)
  t108 = f.my_piecewise3(t55, 0, 0.5e1 / 0.3e1 * t57 * t105)
  t116 = t6 * t59 * t88 * t71 / 0.10e2
  t118 = f.my_piecewise3(t52, 0, 0.3e1 / 0.20e2 * t6 * t108 * t30 * t71 + t116)
  vrho_0_ = t51 + t75 + t7 * (t103 + t118)
  t121 = -t8 - t78
  t122 = f.my_piecewise5(t11, 0, t15, 0, t121)
  t125 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t122)
  t131 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t125 * t30 * t47 + t92)
  t133 = f.my_piecewise5(t15, 0, t11, 0, -t121)
  t136 = f.my_piecewise3(t55, 0, 0.5e1 / 0.3e1 * t57 * t133)
  t141 = t6 * t60
  t151 = f.my_piecewise3(t52, 0, 0.3e1 / 0.20e2 * t6 * t136 * t30 * t71 + t116 - t141 * t61 / t64 / t62 / r1 * t38 * t43 / 0.36e2)
  vrho_1_ = t51 + t75 + t7 * (t131 + t151)
  t155 = t38 * t43
  t159 = f.my_piecewise3(t1, 0, t93 * params.lambda_ * t37 * t155 / 0.96e2)
  vsigma_0_ = t7 * t159
  vsigma_1_ = 0.0e0
  t164 = f.my_piecewise3(t52, 0, t141 * params.lambda_ * t66 * t155 / 0.96e2)
  vsigma_2_ = t7 * t164
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
  params_lambda_raw = params.lambda_
  if isinstance(params_lambda_raw, (str, bytes, dict)):
    params_lambda_ = params_lambda_raw
  else:
    try:
      params_lambda_seq = list(params_lambda_raw)
    except TypeError:
      params_lambda_ = params_lambda_raw
    else:
      params_lambda_seq = np.asarray(params_lambda_seq, dtype=np.float64)
      params_lambda_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_lambda_seq))

  tflw_f = lambda x: params_gamma + params_lambda_ / 8 * x ** 2 / K_FACTOR_C

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, tflw_f, rs, zeta, xs0, xs1)

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
  t24 = params.lambda_ * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = r0 ** 2
  t31 = 6 ** (0.1e1 / 0.3e1)
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = 0.1e1 / t35
  t40 = params.gamma + 0.5e1 / 0.72e2 * t24 * t26 / t22 / t28 * t31 * t36
  t44 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t20 * t22 * t40)
  t60 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t40 / 0.10e2 - t7 * t20 / t28 / r0 * t24 * t26 * t31 * t36 / 0.36e2)
  vrho_0_ = 0.2e1 * r0 * t60 + 0.2e1 * t44
  t71 = f.my_piecewise3(t2, 0, t7 * t20 / t28 * params.lambda_ * t26 * t31 * t36 / 0.96e2)
  vsigma_0_ = 0.2e1 * r0 * t71
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
  t24 = params.lambda_ * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = r0 ** 2
  t29 = t21 ** 2
  t32 = 6 ** (0.1e1 / 0.3e1)
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t41 = params.gamma + 0.5e1 / 0.72e2 * t24 * t26 / t29 / t28 * t32 * t37
  t48 = t7 * t20 / t28 / r0
  t51 = t24 * t26 * t32 * t37
  t55 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t41 / 0.10e2 - t48 * t51 / 0.36e2)
  t63 = t28 ** 2
  t70 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t41 / 0.30e2 + 0.7e1 / 0.108e3 * t7 * t20 / t63 * t51)
  v2rho2_0_ = 0.2e1 * r0 * t70 + 0.4e1 * t55
  t78 = params.lambda_ * t26 * t32 * t37
  t81 = f.my_piecewise3(t2, 0, t7 * t20 / t28 * t78 / 0.96e2)
  t84 = f.my_piecewise3(t2, 0, -t48 * t78 / 0.48e2)
  v2rhosigma_0_ = 0.2e1 * r0 * t84 + 0.2e1 * t81
  v2sigma2_0_ = 0.0e0
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
  t25 = params.lambda_ * s0
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t29 = r0 ** 2
  t30 = t21 ** 2
  t33 = 6 ** (0.1e1 / 0.3e1)
  t35 = jnp.pi ** 2
  t36 = t35 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = 0.1e1 / t37
  t42 = params.gamma + 0.5e1 / 0.72e2 * t25 * t27 / t30 / t29 * t33 * t38
  t46 = t29 ** 2
  t52 = t25 * t27 * t33 * t38
  t56 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t42 / 0.30e2 + 0.7e1 / 0.108e3 * t7 * t20 / t46 * t52)
  t71 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t29 * t42 - 0.41e2 / 0.162e3 * t7 * t20 / t46 / r0 * t52)
  v3rho3_0_ = 0.2e1 * r0 * t71 + 0.6e1 * t56

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
  t26 = params.lambda_ * s0
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t30 = t22 ** 2
  t33 = 6 ** (0.1e1 / 0.3e1)
  t35 = jnp.pi ** 2
  t36 = t35 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = 0.1e1 / t37
  t42 = params.gamma + 0.5e1 / 0.72e2 * t26 * t28 / t30 / t21 * t33 * t38
  t46 = t21 ** 2
  t53 = t26 * t28 * t33 * t38
  t57 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t22 / t21 * t42 - 0.41e2 / 0.162e3 * t7 * t20 / t46 / r0 * t53)
  t73 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 / t22 / t21 / r0 * t42 + 0.611e3 / 0.486e3 * t7 * t20 / t46 / t21 * t53)
  v4rho4_0_ = 0.2e1 * r0 * t73 + 0.8e1 * t57

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
  t35 = params.lambda_ * s0
  t36 = r0 ** 2
  t37 = r0 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t41 = 6 ** (0.1e1 / 0.3e1)
  t43 = jnp.pi ** 2
  t44 = t43 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = 0.1e1 / t45
  t50 = params.gamma + 0.5e1 / 0.72e2 * t35 / t38 / t36 * t41 * t46
  t54 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t56 = t55 * f.p.zeta_threshold
  t58 = f.my_piecewise3(t21, t56, t23 * t20)
  t59 = 0.1e1 / t32
  t60 = t58 * t59
  t63 = t6 * t60 * t50 / 0.10e2
  t65 = t6 * t58 * t33
  t71 = t35 / t38 / t36 / r0 * t41 * t46
  t75 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t50 + t63 - t65 * t71 / 0.36e2)
  t77 = r1 <= f.p.dens_threshold
  t78 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t79 = 0.1e1 + t78
  t80 = t79 <= f.p.zeta_threshold
  t81 = t79 ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t84 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t87 = f.my_piecewise3(t80, 0, 0.5e1 / 0.3e1 * t82 * t84)
  t88 = t87 * t33
  t89 = params.lambda_ * s2
  t90 = r1 ** 2
  t91 = r1 ** (0.1e1 / 0.3e1)
  t92 = t91 ** 2
  t99 = params.gamma + 0.5e1 / 0.72e2 * t89 / t92 / t90 * t41 * t46
  t104 = f.my_piecewise3(t80, t56, t82 * t79)
  t105 = t104 * t59
  t108 = t6 * t105 * t99 / 0.10e2
  t110 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t88 * t99 + t108)
  t112 = 0.1e1 / t22
  t113 = t28 ** 2
  t118 = t17 / t24 / t7
  t120 = -0.2e1 * t25 + 0.2e1 * t118
  t121 = f.my_piecewise5(t11, 0, t15, 0, t120)
  t125 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t112 * t113 + 0.5e1 / 0.3e1 * t23 * t121)
  t132 = t6 * t31 * t59 * t50
  t138 = 0.1e1 / t32 / t7
  t142 = t6 * t58 * t138 * t50 / 0.30e2
  t144 = t6 * t60 * t71
  t146 = t36 ** 2
  t155 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t125 * t33 * t50 + t132 / 0.5e1 - t6 * t34 * t71 / 0.18e2 - t142 - t144 / 0.27e2 + 0.11e2 / 0.108e3 * t65 * t35 / t38 / t146 * t41 * t46)
  t156 = 0.1e1 / t81
  t157 = t84 ** 2
  t161 = f.my_piecewise5(t15, 0, t11, 0, -t120)
  t165 = f.my_piecewise3(t80, 0, 0.10e2 / 0.9e1 * t156 * t157 + 0.5e1 / 0.3e1 * t82 * t161)
  t172 = t6 * t87 * t59 * t99
  t177 = t6 * t104 * t138 * t99 / 0.30e2
  t179 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t165 * t33 * t99 + t172 / 0.5e1 - t177)
  d11 = 0.2e1 * t75 + 0.2e1 * t110 + t7 * (t155 + t179)
  t182 = -t8 - t26
  t183 = f.my_piecewise5(t11, 0, t15, 0, t182)
  t186 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t183)
  t187 = t186 * t33
  t192 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t187 * t50 + t63)
  t194 = f.my_piecewise5(t15, 0, t11, 0, -t182)
  t197 = f.my_piecewise3(t80, 0, 0.5e1 / 0.3e1 * t82 * t194)
  t198 = t197 * t33
  t203 = t6 * t104 * t33
  t209 = t89 / t92 / t90 / r1 * t41 * t46
  t213 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t198 * t99 + t108 - t203 * t209 / 0.36e2)
  t217 = 0.2e1 * t118
  t218 = f.my_piecewise5(t11, 0, t15, 0, t217)
  t222 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t112 * t183 * t28 + 0.5e1 / 0.3e1 * t23 * t218)
  t229 = t6 * t186 * t59 * t50
  t237 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t222 * t33 * t50 + t229 / 0.10e2 - t6 * t187 * t71 / 0.36e2 + t132 / 0.10e2 - t142 - t144 / 0.54e2)
  t241 = f.my_piecewise5(t15, 0, t11, 0, -t217)
  t245 = f.my_piecewise3(t80, 0, 0.10e2 / 0.9e1 * t156 * t194 * t84 + 0.5e1 / 0.3e1 * t82 * t241)
  t252 = t6 * t197 * t59 * t99
  t259 = t6 * t105 * t209
  t262 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t245 * t33 * t99 + t252 / 0.10e2 + t172 / 0.10e2 - t177 - t6 * t88 * t209 / 0.36e2 - t259 / 0.54e2)
  d12 = t75 + t110 + t192 + t213 + t7 * (t237 + t262)
  t267 = t183 ** 2
  t271 = 0.2e1 * t25 + 0.2e1 * t118
  t272 = f.my_piecewise5(t11, 0, t15, 0, t271)
  t276 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t112 * t267 + 0.5e1 / 0.3e1 * t23 * t272)
  t283 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t276 * t33 * t50 + t229 / 0.5e1 - t142)
  t284 = t194 ** 2
  t288 = f.my_piecewise5(t15, 0, t11, 0, -t271)
  t292 = f.my_piecewise3(t80, 0, 0.10e2 / 0.9e1 * t156 * t284 + 0.5e1 / 0.3e1 * t82 * t288)
  t302 = t90 ** 2
  t311 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t292 * t33 * t99 + t252 / 0.5e1 - t6 * t198 * t209 / 0.18e2 - t177 - t259 / 0.27e2 + 0.11e2 / 0.108e3 * t203 * t89 / t92 / t302 * t41 * t46)
  d22 = 0.2e1 * t192 + 0.2e1 * t213 + t7 * (t283 + t311)
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
  t46 = params.lambda_ * s0
  t47 = r0 ** 2
  t48 = r0 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t52 = 6 ** (0.1e1 / 0.3e1)
  t54 = jnp.pi ** 2
  t55 = t54 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = 0.1e1 / t56
  t61 = params.gamma + 0.5e1 / 0.72e2 * t46 / t49 / t47 * t52 * t57
  t67 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t68 = 0.1e1 / t43
  t69 = t67 * t68
  t74 = t6 * t67 * t44
  t80 = t46 / t49 / t47 / r0 * t52 * t57
  t83 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t84 = t83 ** 2
  t85 = t84 * f.p.zeta_threshold
  t87 = f.my_piecewise3(t21, t85, t32 * t20)
  t89 = 0.1e1 / t43 / t7
  t90 = t87 * t89
  t95 = t6 * t87 * t68
  t99 = t6 * t87 * t44
  t100 = t47 ** 2
  t105 = t46 / t49 / t100 * t52 * t57
  t109 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t61 + t6 * t69 * t61 / 0.5e1 - t74 * t80 / 0.18e2 - t6 * t90 * t61 / 0.30e2 - t95 * t80 / 0.27e2 + 0.11e2 / 0.108e3 * t99 * t105)
  t111 = r1 <= f.p.dens_threshold
  t112 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t113 = 0.1e1 + t112
  t114 = t113 <= f.p.zeta_threshold
  t115 = t113 ** (0.1e1 / 0.3e1)
  t116 = 0.1e1 / t115
  t118 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t119 = t118 ** 2
  t122 = t115 ** 2
  t124 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t128 = f.my_piecewise3(t114, 0, 0.10e2 / 0.9e1 * t116 * t119 + 0.5e1 / 0.3e1 * t122 * t124)
  t131 = r1 ** 2
  t132 = r1 ** (0.1e1 / 0.3e1)
  t133 = t132 ** 2
  t140 = params.gamma + 0.5e1 / 0.72e2 * params.lambda_ * s2 / t133 / t131 * t52 * t57
  t146 = f.my_piecewise3(t114, 0, 0.5e1 / 0.3e1 * t122 * t118)
  t152 = f.my_piecewise3(t114, t85, t122 * t113)
  t158 = f.my_piecewise3(t111, 0, 0.3e1 / 0.20e2 * t6 * t128 * t44 * t140 + t6 * t146 * t68 * t140 / 0.5e1 - t6 * t152 * t89 * t140 / 0.30e2)
  t168 = t24 ** 2
  t172 = 0.6e1 * t34 - 0.6e1 * t17 / t168
  t173 = f.my_piecewise5(t11, 0, t15, 0, t172)
  t177 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t173)
  t199 = 0.1e1 / t43 / t24
  t218 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t177 * t44 * t61 + 0.3e1 / 0.10e2 * t6 * t42 * t68 * t61 - t6 * t45 * t80 / 0.12e2 - t6 * t67 * t89 * t61 / 0.10e2 - t6 * t69 * t80 / 0.9e1 + 0.11e2 / 0.36e2 * t74 * t105 + 0.2e1 / 0.45e2 * t6 * t87 * t199 * t61 + t6 * t90 * t80 / 0.54e2 + 0.11e2 / 0.54e2 * t95 * t105 - 0.77e2 / 0.162e3 * t99 * t46 / t49 / t100 / r0 * t52 * t57)
  t228 = f.my_piecewise5(t15, 0, t11, 0, -t172)
  t232 = f.my_piecewise3(t114, 0, -0.10e2 / 0.27e2 / t115 / t113 * t119 * t118 + 0.10e2 / 0.3e1 * t116 * t118 * t124 + 0.5e1 / 0.3e1 * t122 * t228)
  t250 = f.my_piecewise3(t111, 0, 0.3e1 / 0.20e2 * t6 * t232 * t44 * t140 + 0.3e1 / 0.10e2 * t6 * t128 * t68 * t140 - t6 * t146 * t89 * t140 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t152 * t199 * t140)
  d111 = 0.3e1 * t109 + 0.3e1 * t158 + t7 * (t218 + t250)

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
  t58 = params.lambda_ * s0
  t59 = r0 ** 2
  t60 = r0 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t64 = 6 ** (0.1e1 / 0.3e1)
  t66 = jnp.pi ** 2
  t67 = t66 ** (0.1e1 / 0.3e1)
  t68 = t67 ** 2
  t69 = 0.1e1 / t68
  t73 = params.gamma + 0.5e1 / 0.72e2 * t58 / t61 / t59 * t64 * t69
  t82 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t83 = 0.1e1 / t55
  t84 = t82 * t83
  t89 = t6 * t82 * t56
  t95 = t58 / t61 / t59 / r0 * t64 * t69
  t100 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t102 = 0.1e1 / t55 / t7
  t103 = t100 * t102
  t108 = t6 * t100 * t83
  t112 = t6 * t100 * t56
  t113 = t59 ** 2
  t118 = t58 / t61 / t113 * t64 * t69
  t121 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t122 = t121 ** 2
  t123 = t122 * f.p.zeta_threshold
  t125 = f.my_piecewise3(t21, t123, t44 * t20)
  t127 = 0.1e1 / t55 / t25
  t128 = t125 * t127
  t133 = t6 * t125 * t102
  t137 = t6 * t125 * t83
  t141 = t6 * t125 * t56
  t147 = t58 / t61 / t113 / r0 * t64 * t69
  t151 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t73 + 0.3e1 / 0.10e2 * t6 * t84 * t73 - t89 * t95 / 0.12e2 - t6 * t103 * t73 / 0.10e2 - t108 * t95 / 0.9e1 + 0.11e2 / 0.36e2 * t112 * t118 + 0.2e1 / 0.45e2 * t6 * t128 * t73 + t133 * t95 / 0.54e2 + 0.11e2 / 0.54e2 * t137 * t118 - 0.77e2 / 0.162e3 * t141 * t147)
  t153 = r1 <= f.p.dens_threshold
  t154 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t155 = 0.1e1 + t154
  t156 = t155 <= f.p.zeta_threshold
  t157 = t155 ** (0.1e1 / 0.3e1)
  t159 = 0.1e1 / t157 / t155
  t161 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t162 = t161 ** 2
  t166 = 0.1e1 / t157
  t167 = t166 * t161
  t169 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t172 = t157 ** 2
  t174 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t178 = f.my_piecewise3(t156, 0, -0.10e2 / 0.27e2 * t159 * t162 * t161 + 0.10e2 / 0.3e1 * t167 * t169 + 0.5e1 / 0.3e1 * t172 * t174)
  t181 = r1 ** 2
  t182 = r1 ** (0.1e1 / 0.3e1)
  t183 = t182 ** 2
  t190 = params.gamma + 0.5e1 / 0.72e2 * params.lambda_ * s2 / t183 / t181 * t64 * t69
  t199 = f.my_piecewise3(t156, 0, 0.10e2 / 0.9e1 * t166 * t162 + 0.5e1 / 0.3e1 * t172 * t169)
  t206 = f.my_piecewise3(t156, 0, 0.5e1 / 0.3e1 * t172 * t161)
  t212 = f.my_piecewise3(t156, t123, t172 * t155)
  t218 = f.my_piecewise3(t153, 0, 0.3e1 / 0.20e2 * t6 * t178 * t56 * t190 + 0.3e1 / 0.10e2 * t6 * t199 * t83 * t190 - t6 * t206 * t102 * t190 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t212 * t127 * t190)
  t250 = t20 ** 2
  t253 = t30 ** 2
  t259 = t41 ** 2
  t268 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t269 = f.my_piecewise5(t11, 0, t15, 0, t268)
  t273 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t250 * t253 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t259 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t269)
  t291 = 0.1e1 / t55 / t36
  t296 = -0.154e3 / 0.81e2 * t112 * t147 - 0.11e2 / 0.81e2 * t133 * t118 - 0.308e3 / 0.243e3 * t137 * t147 + 0.1309e4 / 0.486e3 * t141 * t58 / t61 / t113 / t59 * t64 * t69 + 0.11e2 / 0.18e2 * t89 * t118 + 0.22e2 / 0.27e2 * t108 * t118 - t6 * t57 * t95 / 0.9e1 - 0.2e1 / 0.9e1 * t6 * t84 * t95 + 0.2e1 / 0.27e2 * t6 * t103 * t95 - 0.8e1 / 0.243e3 * t6 * t128 * t95 + 0.3e1 / 0.20e2 * t6 * t273 * t56 * t73 + 0.2e1 / 0.5e1 * t6 * t54 * t83 * t73 - t6 * t82 * t102 * t73 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t100 * t127 * t73 - 0.14e2 / 0.135e3 * t6 * t125 * t291 * t73
  t297 = f.my_piecewise3(t1, 0, t296)
  t298 = t155 ** 2
  t301 = t162 ** 2
  t307 = t169 ** 2
  t313 = f.my_piecewise5(t15, 0, t11, 0, -t268)
  t317 = f.my_piecewise3(t156, 0, 0.40e2 / 0.81e2 / t157 / t298 * t301 - 0.20e2 / 0.9e1 * t159 * t162 * t169 + 0.10e2 / 0.3e1 * t166 * t307 + 0.40e2 / 0.9e1 * t167 * t174 + 0.5e1 / 0.3e1 * t172 * t313)
  t339 = f.my_piecewise3(t153, 0, 0.3e1 / 0.20e2 * t6 * t317 * t56 * t190 + 0.2e1 / 0.5e1 * t6 * t178 * t83 * t190 - t6 * t199 * t102 * t190 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t206 * t127 * t190 - 0.14e2 / 0.135e3 * t6 * t212 * t291 * t190)
  d1111 = 0.4e1 * t151 + 0.4e1 * t218 + t7 * (t297 + t339)

  res = {'v4rho4': d1111}
  return res
