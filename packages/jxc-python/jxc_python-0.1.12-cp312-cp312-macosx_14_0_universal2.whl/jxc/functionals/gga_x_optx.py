"""Generated from gga_x_optx.mpl."""

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

  optx_f = lambda x: params_a + params_b * (params_gamma * x ** 2 / (1 + params_gamma * x ** 2)) ** 2

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, optx_f, rs, z, xs0, xs1)

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

  optx_f = lambda x: params_a + params_b * (params_gamma * x ** 2 / (1 + params_gamma * x ** 2)) ** 2

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, optx_f, rs, z, xs0, xs1)

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

  optx_f = lambda x: params_a + params_b * (params_gamma * x ** 2 / (1 + params_gamma * x ** 2)) ** 2

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, optx_f, rs, z, xs0, xs1)

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
  t28 = params.gamma ** 2
  t29 = params.b * t28
  t30 = s0 ** 2
  t31 = r0 ** 2
  t32 = t31 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t36 = 0.1e1 / t34 / t32 / r0
  t39 = t34 ** 2
  t43 = 0.1e1 + params.gamma * s0 / t39 / t31
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t48 = t29 * t30 * t36 * t45 + params.a
  t52 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t48)
  t53 = r1 <= f.p.dens_threshold
  t54 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t55 = 0.1e1 + t54
  t56 = t55 <= f.p.zeta_threshold
  t57 = t55 ** (0.1e1 / 0.3e1)
  t59 = f.my_piecewise3(t56, t22, t57 * t55)
  t60 = t59 * t26
  t61 = s2 ** 2
  t62 = r1 ** 2
  t63 = t62 ** 2
  t65 = r1 ** (0.1e1 / 0.3e1)
  t67 = 0.1e1 / t65 / t63 / r1
  t70 = t65 ** 2
  t74 = 0.1e1 + params.gamma * s2 / t70 / t62
  t75 = t74 ** 2
  t76 = 0.1e1 / t75
  t79 = t29 * t61 * t67 * t76 + params.a
  t83 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t60 * t79)
  t84 = t6 ** 2
  t86 = t16 / t84
  t87 = t7 - t86
  t88 = f.my_piecewise5(t10, 0, t14, 0, t87)
  t91 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t88)
  t96 = t26 ** 2
  t97 = 0.1e1 / t96
  t101 = t5 * t25 * t97 * t48 / 0.8e1
  t109 = params.b * t28 * params.gamma
  t111 = t32 ** 2
  t116 = 0.1e1 / t44 / t43
  t125 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t91 * t26 * t48 - t101 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.16e2 / 0.3e1 * t29 * t30 / t34 / t32 / t31 * t45 + 0.16e2 / 0.3e1 * t109 * t30 * s0 / t111 / r0 * t116))
  t127 = f.my_piecewise5(t14, 0, t10, 0, -t87)
  t130 = f.my_piecewise3(t56, 0, 0.4e1 / 0.3e1 * t57 * t127)
  t138 = t5 * t59 * t97 * t79 / 0.8e1
  t140 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t130 * t26 * t79 - t138)
  vrho_0_ = t52 + t83 + t6 * (t125 + t140)
  t143 = -t7 - t86
  t144 = f.my_piecewise5(t10, 0, t14, 0, t143)
  t147 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t144)
  t153 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t147 * t26 * t48 - t101)
  t155 = f.my_piecewise5(t14, 0, t10, 0, -t143)
  t158 = f.my_piecewise3(t56, 0, 0.4e1 / 0.3e1 * t57 * t155)
  t170 = t63 ** 2
  t175 = 0.1e1 / t75 / t74
  t184 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t158 * t26 * t79 - t138 - 0.3e1 / 0.8e1 * t5 * t60 * (-0.16e2 / 0.3e1 * t29 * t61 / t65 / t63 / t62 * t76 + 0.16e2 / 0.3e1 * t109 * t61 * s2 / t170 / r1 * t175))
  vrho_1_ = t52 + t83 + t6 * (t153 + t184)
  t199 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.2e1 * t29 * s0 * t36 * t45 - 0.2e1 * t109 * t30 / t111 * t116))
  vsigma_0_ = t6 * t199
  vsigma_1_ = 0.0e0
  t212 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t60 * (0.2e1 * t29 * s2 * t67 * t76 - 0.2e1 * t109 * t61 / t170 * t175))
  vsigma_2_ = t6 * t212
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

  optx_f = lambda x: params_a + params_b * (params_gamma * x ** 2 / (1 + params_gamma * x ** 2)) ** 2

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, optx_f, rs, z, xs0, xs1)

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
  t20 = params.gamma ** 2
  t21 = params.b * t20
  t22 = s0 ** 2
  t23 = t21 * t22
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = r0 ** 2
  t26 = t25 ** 2
  t32 = t24 ** 2
  t33 = t18 ** 2
  t38 = 0.1e1 + params.gamma * s0 * t32 / t33 / t25
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t41 = t24 / t18 / t26 / r0 * t40
  t44 = 0.2e1 * t23 * t41 + params.a
  t48 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t44)
  t62 = params.b * t20 * params.gamma
  t64 = t26 ** 2
  t69 = 0.1e1 / t39 / t38
  t78 = f.my_piecewise3(t2, 0, -t6 * t17 / t33 * t44 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.32e2 / 0.3e1 * t23 * t24 / t18 / t26 / t25 * t40 + 0.64e2 / 0.3e1 * t62 * t22 * s0 / t64 / r0 * t69))
  vrho_0_ = 0.2e1 * r0 * t78 + 0.2e1 * t48
  t93 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.4e1 * t21 * s0 * t41 - 0.8e1 * t62 * t22 / t64 * t69))
  vsigma_0_ = 0.2e1 * r0 * t93
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
  t22 = params.gamma ** 2
  t23 = params.b * t22
  t24 = s0 ** 2
  t25 = t23 * t24
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = r0 ** 2
  t28 = t27 ** 2
  t34 = t26 ** 2
  t39 = 0.1e1 + params.gamma * s0 * t34 / t19 / t27
  t40 = t39 ** 2
  t41 = 0.1e1 / t40
  t42 = t26 / t18 / t28 / r0 * t41
  t45 = 0.2e1 * t25 * t42 + params.a
  t49 = t17 * t18
  t54 = t26 / t18 / t28 / t27 * t41
  t58 = params.b * t22 * params.gamma
  t59 = t24 * s0
  t60 = t28 ** 2
  t62 = 0.1e1 / t60 / r0
  t65 = 0.1e1 / t40 / t39
  t69 = -0.32e2 / 0.3e1 * t25 * t54 + 0.64e2 / 0.3e1 * t58 * t59 * t62 * t65
  t74 = f.my_piecewise3(t2, 0, -t6 * t21 * t45 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t49 * t69)
  t85 = t27 * r0
  t93 = t60 * t27
  t99 = t22 ** 2
  t100 = params.b * t99
  t101 = t24 ** 2
  t106 = t40 ** 2
  t107 = 0.1e1 / t106
  t117 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t45 / 0.12e2 - t6 * t21 * t69 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t49 * (0.608e3 / 0.9e1 * t25 * t26 / t18 / t28 / t85 * t41 - 0.2752e4 / 0.9e1 * t58 * t59 / t93 * t65 + 0.512e3 / 0.3e1 * t100 * t101 / t19 / t60 / t28 * t107 * t34))
  v2rho2_0_ = 0.2e1 * r0 * t117 + 0.4e1 * t74
  t120 = t23 * s0
  t123 = 0.1e1 / t60
  t128 = -0.8e1 * t58 * t24 * t123 * t65 + 0.4e1 * t120 * t42
  t132 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t49 * t128)
  t155 = f.my_piecewise3(t2, 0, -t6 * t21 * t128 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t49 * (-0.64e2 / 0.3e1 * t120 * t54 + 0.320e3 / 0.3e1 * t58 * t24 * t62 * t65 - 0.64e2 * t100 * t59 / t19 / t60 / t85 * t107 * t34))
  v2rhosigma_0_ = 0.2e1 * r0 * t155 + 0.2e1 * t132
  t175 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t49 * (0.4e1 * t23 * t42 - 0.32e2 * t58 * s0 * t123 * t65 + 0.24e2 * t100 * t24 / t19 / t93 * t107 * t34))
  v2sigma2_0_ = 0.2e1 * r0 * t175
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
  t23 = params.gamma ** 2
  t25 = s0 ** 2
  t26 = params.b * t23 * t25
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = r0 ** 2
  t29 = t28 ** 2
  t30 = t29 * r0
  t35 = t27 ** 2
  t37 = 0.1e1 / t19 / t28
  t40 = params.gamma * s0 * t35 * t37 + 0.1e1
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t46 = params.a + 0.2e1 * t26 * t27 / t18 / t30 * t42
  t51 = t17 / t19
  t60 = params.b * t23 * params.gamma
  t61 = t25 * s0
  t62 = t29 ** 2
  t67 = 0.1e1 / t41 / t40
  t71 = -0.32e2 / 0.3e1 * t26 * t27 / t18 / t29 / t28 * t42 + 0.64e2 / 0.3e1 * t60 * t61 / t62 / r0 * t67
  t75 = t17 * t18
  t76 = t28 * r0
  t90 = t23 ** 2
  t92 = t25 ** 2
  t93 = params.b * t90 * t92
  t97 = t41 ** 2
  t98 = 0.1e1 / t97
  t103 = 0.608e3 / 0.9e1 * t26 * t27 / t18 / t29 / t76 * t42 - 0.2752e4 / 0.9e1 * t60 * t61 / t62 / t28 * t67 + 0.512e3 / 0.3e1 * t93 / t19 / t62 / t29 * t98 * t35
  t108 = f.my_piecewise3(t2, 0, t6 * t22 * t46 / 0.12e2 - t6 * t51 * t71 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t75 * t103)
  t143 = t62 ** 2
  t157 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t37 * t46 + t6 * t22 * t71 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t51 * t103 - 0.3e1 / 0.8e1 * t6 * t75 * (-0.13376e5 / 0.27e2 * t26 * t27 / t18 / t62 * t42 + 0.102016e6 / 0.27e2 * t60 * t61 / t62 / t76 * t67 - 0.4608e4 * t93 / t19 / t62 / t30 * t98 * t35 + 0.32768e5 / 0.9e1 * params.b * t90 * params.gamma * t92 * s0 / t18 / t143 / t97 / t40 * t27))
  v3rho3_0_ = 0.2e1 * r0 * t157 + 0.6e1 * t108

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
  t24 = params.gamma ** 2
  t26 = s0 ** 2
  t27 = params.b * t24 * t26
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t18 ** 2
  t30 = t29 * r0
  t35 = t28 ** 2
  t38 = params.gamma * s0 * t35 * t22 + 0.1e1
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t44 = params.a + 0.2e1 * t27 * t28 / t19 / t30 * t40
  t50 = t17 / t20 / r0
  t51 = t29 * t18
  t59 = params.b * t24 * params.gamma
  t60 = t26 * s0
  t61 = t29 ** 2
  t62 = t61 * r0
  t66 = 0.1e1 / t39 / t38
  t70 = -0.32e2 / 0.3e1 * t27 * t28 / t19 / t51 * t40 + 0.64e2 / 0.3e1 * t59 * t60 / t62 * t66
  t75 = t17 / t20
  t76 = t18 * r0
  t90 = t24 ** 2
  t92 = t26 ** 2
  t93 = params.b * t90 * t92
  t94 = t61 * t29
  t97 = t39 ** 2
  t98 = 0.1e1 / t97
  t103 = 0.608e3 / 0.9e1 * t27 * t28 / t19 / t29 / t76 * t40 - 0.2752e4 / 0.9e1 * t59 * t60 / t61 / t18 * t66 + 0.512e3 / 0.3e1 * t93 / t20 / t94 * t98 * t35
  t107 = t17 * t19
  t130 = params.b * t90 * params.gamma * t92 * s0
  t131 = t61 ** 2
  t135 = 0.1e1 / t97 / t38
  t140 = -0.13376e5 / 0.27e2 * t27 * t28 / t19 / t61 * t40 + 0.102016e6 / 0.27e2 * t59 * t60 / t61 / t76 * t66 - 0.4608e4 * t93 / t20 / t61 / t30 * t98 * t35 + 0.32768e5 / 0.9e1 * t130 / t19 / t131 * t135 * t28
  t145 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t44 + t6 * t50 * t70 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t75 * t103 - 0.3e1 / 0.8e1 * t6 * t107 * t140)
  t203 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 / t20 / t76 * t44 - 0.5e1 / 0.9e1 * t6 * t23 * t70 + t6 * t50 * t103 / 0.2e1 - t6 * t75 * t140 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t107 * (0.334400e6 / 0.81e2 * t27 * t28 / t19 / t62 * t40 - 0.3794560e7 / 0.81e2 * t59 * t60 / t94 * t66 + 0.2516480e7 / 0.27e2 * t93 / t20 / t61 / t51 * t98 * t35 - 0.4259840e7 / 0.27e2 * t130 / t19 / t131 / r0 * t135 * t28 + 0.2621440e7 / 0.27e2 * params.b * t90 * t24 * t92 * t26 / t131 / t29 / t97 / t39))
  v4rho4_0_ = 0.2e1 * r0 * t203 + 0.8e1 * t145

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
  t32 = params.gamma ** 2
  t33 = params.b * t32
  t34 = s0 ** 2
  t35 = r0 ** 2
  t36 = t35 ** 2
  t38 = r0 ** (0.1e1 / 0.3e1)
  t43 = t38 ** 2
  t47 = 0.1e1 + params.gamma * s0 / t43 / t35
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t52 = params.a + t33 * t34 / t38 / t36 / r0 * t49
  t56 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t57 = t56 * f.p.zeta_threshold
  t59 = f.my_piecewise3(t20, t57, t21 * t19)
  t60 = t30 ** 2
  t61 = 0.1e1 / t60
  t62 = t59 * t61
  t65 = t5 * t62 * t52 / 0.8e1
  t66 = t59 * t30
  t74 = params.b * t32 * params.gamma
  t75 = t34 * s0
  t76 = t36 ** 2
  t81 = 0.1e1 / t48 / t47
  t85 = -0.16e2 / 0.3e1 * t33 * t34 / t38 / t36 / t35 * t49 + 0.16e2 / 0.3e1 * t74 * t75 / t76 / r0 * t81
  t90 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t52 - t65 - 0.3e1 / 0.8e1 * t5 * t66 * t85)
  t92 = r1 <= f.p.dens_threshold
  t93 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t94 = 0.1e1 + t93
  t95 = t94 <= f.p.zeta_threshold
  t96 = t94 ** (0.1e1 / 0.3e1)
  t98 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t101 = f.my_piecewise3(t95, 0, 0.4e1 / 0.3e1 * t96 * t98)
  t102 = t101 * t30
  t103 = s2 ** 2
  t104 = r1 ** 2
  t105 = t104 ** 2
  t107 = r1 ** (0.1e1 / 0.3e1)
  t112 = t107 ** 2
  t116 = 0.1e1 + params.gamma * s2 / t112 / t104
  t117 = t116 ** 2
  t118 = 0.1e1 / t117
  t121 = params.a + t33 * t103 / t107 / t105 / r1 * t118
  t126 = f.my_piecewise3(t95, t57, t96 * t94)
  t127 = t126 * t61
  t130 = t5 * t127 * t121 / 0.8e1
  t132 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t102 * t121 - t130)
  t134 = t21 ** 2
  t135 = 0.1e1 / t134
  t136 = t26 ** 2
  t141 = t16 / t22 / t6
  t143 = -0.2e1 * t23 + 0.2e1 * t141
  t144 = f.my_piecewise5(t10, 0, t14, 0, t143)
  t148 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t135 * t136 + 0.4e1 / 0.3e1 * t21 * t144)
  t155 = t5 * t29 * t61 * t52
  t161 = 0.1e1 / t60 / t6
  t165 = t5 * t59 * t161 * t52 / 0.12e2
  t167 = t5 * t62 * t85
  t183 = t32 ** 2
  t184 = params.b * t183
  t185 = t34 ** 2
  t190 = t48 ** 2
  t200 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t148 * t30 * t52 - t155 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t85 + t165 - t167 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t66 * (0.304e3 / 0.9e1 * t33 * t34 / t38 / t36 / t35 / r0 * t49 - 0.688e3 / 0.9e1 * t74 * t75 / t76 / t35 * t81 + 0.128e3 / 0.3e1 * t184 * t185 / t43 / t76 / t36 / t190))
  t201 = t96 ** 2
  t202 = 0.1e1 / t201
  t203 = t98 ** 2
  t207 = f.my_piecewise5(t14, 0, t10, 0, -t143)
  t211 = f.my_piecewise3(t95, 0, 0.4e1 / 0.9e1 * t202 * t203 + 0.4e1 / 0.3e1 * t96 * t207)
  t218 = t5 * t101 * t61 * t121
  t223 = t5 * t126 * t161 * t121 / 0.12e2
  t225 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t211 * t30 * t121 - t218 / 0.4e1 + t223)
  d11 = 0.2e1 * t90 + 0.2e1 * t132 + t6 * (t200 + t225)
  t228 = -t7 - t24
  t229 = f.my_piecewise5(t10, 0, t14, 0, t228)
  t232 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t229)
  t233 = t232 * t30
  t238 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t233 * t52 - t65)
  t240 = f.my_piecewise5(t14, 0, t10, 0, -t228)
  t243 = f.my_piecewise3(t95, 0, 0.4e1 / 0.3e1 * t96 * t240)
  t244 = t243 * t30
  t248 = t126 * t30
  t255 = t103 * s2
  t256 = t105 ** 2
  t261 = 0.1e1 / t117 / t116
  t265 = -0.16e2 / 0.3e1 * t33 * t103 / t107 / t105 / t104 * t118 + 0.16e2 / 0.3e1 * t74 * t255 / t256 / r1 * t261
  t270 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t244 * t121 - t130 - 0.3e1 / 0.8e1 * t5 * t248 * t265)
  t274 = 0.2e1 * t141
  t275 = f.my_piecewise5(t10, 0, t14, 0, t274)
  t279 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t135 * t229 * t26 + 0.4e1 / 0.3e1 * t21 * t275)
  t286 = t5 * t232 * t61 * t52
  t294 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t279 * t30 * t52 - t286 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t233 * t85 - t155 / 0.8e1 + t165 - t167 / 0.8e1)
  t298 = f.my_piecewise5(t14, 0, t10, 0, -t274)
  t302 = f.my_piecewise3(t95, 0, 0.4e1 / 0.9e1 * t202 * t240 * t98 + 0.4e1 / 0.3e1 * t96 * t298)
  t309 = t5 * t243 * t61 * t121
  t316 = t5 * t127 * t265
  t319 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t302 * t30 * t121 - t309 / 0.8e1 - t218 / 0.8e1 + t223 - 0.3e1 / 0.8e1 * t5 * t102 * t265 - t316 / 0.8e1)
  d12 = t90 + t132 + t238 + t270 + t6 * (t294 + t319)
  t324 = t229 ** 2
  t328 = 0.2e1 * t23 + 0.2e1 * t141
  t329 = f.my_piecewise5(t10, 0, t14, 0, t328)
  t333 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t135 * t324 + 0.4e1 / 0.3e1 * t21 * t329)
  t340 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t333 * t30 * t52 - t286 / 0.4e1 + t165)
  t341 = t240 ** 2
  t345 = f.my_piecewise5(t14, 0, t10, 0, -t328)
  t349 = f.my_piecewise3(t95, 0, 0.4e1 / 0.9e1 * t202 * t341 + 0.4e1 / 0.3e1 * t96 * t345)
  t373 = t103 ** 2
  t378 = t117 ** 2
  t388 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t349 * t30 * t121 - t309 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t244 * t265 + t223 - t316 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t248 * (0.304e3 / 0.9e1 * t33 * t103 / t107 / t105 / t104 / r1 * t118 - 0.688e3 / 0.9e1 * t74 * t255 / t256 / t104 * t261 + 0.128e3 / 0.3e1 * t184 * t373 / t112 / t256 / t105 / t378))
  d22 = 0.2e1 * t238 + 0.2e1 * t270 + t6 * (t340 + t388)
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
  t44 = params.gamma ** 2
  t45 = params.b * t44
  t46 = s0 ** 2
  t47 = r0 ** 2
  t48 = t47 ** 2
  t49 = t48 * r0
  t50 = r0 ** (0.1e1 / 0.3e1)
  t55 = t50 ** 2
  t59 = 0.1e1 + params.gamma * s0 / t55 / t47
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t64 = params.a + t45 * t46 / t50 / t49 * t61
  t70 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t71 = t42 ** 2
  t72 = 0.1e1 / t71
  t73 = t70 * t72
  t77 = t70 * t42
  t85 = params.b * t44 * params.gamma
  t86 = t46 * s0
  t87 = t48 ** 2
  t92 = 0.1e1 / t60 / t59
  t96 = -0.16e2 / 0.3e1 * t45 * t46 / t50 / t48 / t47 * t61 + 0.16e2 / 0.3e1 * t85 * t86 / t87 / r0 * t92
  t100 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t101 = t100 * f.p.zeta_threshold
  t103 = f.my_piecewise3(t20, t101, t21 * t19)
  t105 = 0.1e1 / t71 / t6
  t106 = t103 * t105
  t110 = t103 * t72
  t114 = t103 * t42
  t115 = t47 * r0
  t129 = t44 ** 2
  t130 = params.b * t129
  t131 = t46 ** 2
  t136 = t60 ** 2
  t137 = 0.1e1 / t136
  t141 = 0.304e3 / 0.9e1 * t45 * t46 / t50 / t48 / t115 * t61 - 0.688e3 / 0.9e1 * t85 * t86 / t87 / t47 * t92 + 0.128e3 / 0.3e1 * t130 * t131 / t55 / t87 / t48 * t137
  t146 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t64 - t5 * t73 * t64 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t77 * t96 + t5 * t106 * t64 / 0.12e2 - t5 * t110 * t96 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t114 * t141)
  t148 = r1 <= f.p.dens_threshold
  t149 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t150 = 0.1e1 + t149
  t151 = t150 <= f.p.zeta_threshold
  t152 = t150 ** (0.1e1 / 0.3e1)
  t153 = t152 ** 2
  t154 = 0.1e1 / t153
  t156 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t157 = t156 ** 2
  t161 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t165 = f.my_piecewise3(t151, 0, 0.4e1 / 0.9e1 * t154 * t157 + 0.4e1 / 0.3e1 * t152 * t161)
  t167 = s2 ** 2
  t168 = r1 ** 2
  t169 = t168 ** 2
  t171 = r1 ** (0.1e1 / 0.3e1)
  t176 = t171 ** 2
  t181 = (0.1e1 + params.gamma * s2 / t176 / t168) ** 2
  t185 = params.a + t45 * t167 / t171 / t169 / r1 / t181
  t191 = f.my_piecewise3(t151, 0, 0.4e1 / 0.3e1 * t152 * t156)
  t197 = f.my_piecewise3(t151, t101, t152 * t150)
  t203 = f.my_piecewise3(t148, 0, -0.3e1 / 0.8e1 * t5 * t165 * t42 * t185 - t5 * t191 * t72 * t185 / 0.4e1 + t5 * t197 * t105 * t185 / 0.12e2)
  t213 = t24 ** 2
  t217 = 0.6e1 * t33 - 0.6e1 * t16 / t213
  t218 = f.my_piecewise5(t10, 0, t14, 0, t217)
  t222 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t218)
  t245 = 0.1e1 / t71 / t24
  t278 = t87 ** 2
  t292 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t222 * t42 * t64 - 0.3e1 / 0.8e1 * t5 * t41 * t72 * t64 - 0.9e1 / 0.8e1 * t5 * t43 * t96 + t5 * t70 * t105 * t64 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t73 * t96 - 0.9e1 / 0.8e1 * t5 * t77 * t141 - 0.5e1 / 0.36e2 * t5 * t103 * t245 * t64 + t5 * t106 * t96 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t110 * t141 - 0.3e1 / 0.8e1 * t5 * t114 * (-0.6688e4 / 0.27e2 * t45 * t46 / t50 / t87 * t61 + 0.25504e5 / 0.27e2 * t85 * t86 / t87 / t115 * t92 - 0.1152e4 * t130 * t131 / t55 / t87 / t49 * t137 + 0.4096e4 / 0.9e1 * params.b * t129 * params.gamma * t131 * s0 / t50 / t278 / t136 / t59))
  t302 = f.my_piecewise5(t14, 0, t10, 0, -t217)
  t306 = f.my_piecewise3(t151, 0, -0.8e1 / 0.27e2 / t153 / t150 * t157 * t156 + 0.4e1 / 0.3e1 * t154 * t156 * t161 + 0.4e1 / 0.3e1 * t152 * t302)
  t324 = f.my_piecewise3(t148, 0, -0.3e1 / 0.8e1 * t5 * t306 * t42 * t185 - 0.3e1 / 0.8e1 * t5 * t165 * t72 * t185 + t5 * t191 * t105 * t185 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t197 * t245 * t185)
  d111 = 0.3e1 * t146 + 0.3e1 * t203 + t6 * (t292 + t324)

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
  t56 = params.gamma ** 2
  t57 = params.b * t56
  t58 = s0 ** 2
  t59 = r0 ** 2
  t60 = t59 ** 2
  t61 = t60 * r0
  t62 = r0 ** (0.1e1 / 0.3e1)
  t67 = t62 ** 2
  t71 = 0.1e1 + params.gamma * s0 / t67 / t59
  t72 = t71 ** 2
  t73 = 0.1e1 / t72
  t76 = params.a + t57 * t58 / t62 / t61 * t73
  t85 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t86 = t54 ** 2
  t87 = 0.1e1 / t86
  t88 = t85 * t87
  t92 = t85 * t54
  t93 = t60 * t59
  t100 = params.b * t56 * params.gamma
  t101 = t58 * s0
  t102 = t60 ** 2
  t103 = t102 * r0
  t107 = 0.1e1 / t72 / t71
  t111 = -0.16e2 / 0.3e1 * t57 * t58 / t62 / t93 * t73 + 0.16e2 / 0.3e1 * t100 * t101 / t103 * t107
  t117 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t119 = 0.1e1 / t86 / t6
  t120 = t117 * t119
  t124 = t117 * t87
  t128 = t117 * t54
  t129 = t59 * r0
  t143 = t56 ** 2
  t144 = params.b * t143
  t145 = t58 ** 2
  t146 = t102 * t60
  t150 = t72 ** 2
  t151 = 0.1e1 / t150
  t155 = 0.304e3 / 0.9e1 * t57 * t58 / t62 / t60 / t129 * t73 - 0.688e3 / 0.9e1 * t100 * t101 / t102 / t59 * t107 + 0.128e3 / 0.3e1 * t144 * t145 / t67 / t146 * t151
  t159 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t160 = t159 * f.p.zeta_threshold
  t162 = f.my_piecewise3(t20, t160, t21 * t19)
  t164 = 0.1e1 / t86 / t25
  t165 = t162 * t164
  t169 = t162 * t119
  t173 = t162 * t87
  t177 = t162 * t54
  t198 = params.b * t143 * params.gamma
  t199 = t145 * s0
  t200 = t102 ** 2
  t205 = 0.1e1 / t150 / t71
  t209 = -0.6688e4 / 0.27e2 * t57 * t58 / t62 / t102 * t73 + 0.25504e5 / 0.27e2 * t100 * t101 / t102 / t129 * t107 - 0.1152e4 * t144 * t145 / t67 / t102 / t61 * t151 + 0.4096e4 / 0.9e1 * t198 * t199 / t62 / t200 * t205
  t214 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t76 - 0.3e1 / 0.8e1 * t5 * t88 * t76 - 0.9e1 / 0.8e1 * t5 * t92 * t111 + t5 * t120 * t76 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t124 * t111 - 0.9e1 / 0.8e1 * t5 * t128 * t155 - 0.5e1 / 0.36e2 * t5 * t165 * t76 + t5 * t169 * t111 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t173 * t155 - 0.3e1 / 0.8e1 * t5 * t177 * t209)
  t216 = r1 <= f.p.dens_threshold
  t217 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t218 = 0.1e1 + t217
  t219 = t218 <= f.p.zeta_threshold
  t220 = t218 ** (0.1e1 / 0.3e1)
  t221 = t220 ** 2
  t223 = 0.1e1 / t221 / t218
  t225 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t226 = t225 ** 2
  t230 = 0.1e1 / t221
  t231 = t230 * t225
  t233 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t237 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t241 = f.my_piecewise3(t219, 0, -0.8e1 / 0.27e2 * t223 * t226 * t225 + 0.4e1 / 0.3e1 * t231 * t233 + 0.4e1 / 0.3e1 * t220 * t237)
  t243 = s2 ** 2
  t244 = r1 ** 2
  t245 = t244 ** 2
  t247 = r1 ** (0.1e1 / 0.3e1)
  t252 = t247 ** 2
  t257 = (0.1e1 + params.gamma * s2 / t252 / t244) ** 2
  t261 = params.a + t57 * t243 / t247 / t245 / r1 / t257
  t270 = f.my_piecewise3(t219, 0, 0.4e1 / 0.9e1 * t230 * t226 + 0.4e1 / 0.3e1 * t220 * t233)
  t277 = f.my_piecewise3(t219, 0, 0.4e1 / 0.3e1 * t220 * t225)
  t283 = f.my_piecewise3(t219, t160, t220 * t218)
  t289 = f.my_piecewise3(t216, 0, -0.3e1 / 0.8e1 * t5 * t241 * t54 * t261 - 0.3e1 / 0.8e1 * t5 * t270 * t87 * t261 + t5 * t277 * t119 * t261 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t283 * t164 * t261)
  t291 = t19 ** 2
  t294 = t30 ** 2
  t300 = t41 ** 2
  t309 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t310 = f.my_piecewise5(t10, 0, t14, 0, t309)
  t314 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t291 * t294 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t300 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t310)
  t398 = 0.1e1 / t86 / t36
  t403 = -0.3e1 / 0.8e1 * t5 * t314 * t54 * t76 - 0.3e1 / 0.2e1 * t5 * t55 * t111 - 0.3e1 / 0.2e1 * t5 * t88 * t111 - 0.9e1 / 0.4e1 * t5 * t92 * t155 + t5 * t120 * t111 - 0.3e1 / 0.2e1 * t5 * t124 * t155 - 0.3e1 / 0.2e1 * t5 * t128 * t209 - 0.5e1 / 0.9e1 * t5 * t165 * t111 + t5 * t169 * t155 / 0.2e1 - t5 * t173 * t209 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t177 * (0.167200e6 / 0.81e2 * t57 * t58 / t62 / t103 * t73 - 0.948640e6 / 0.81e2 * t100 * t101 / t146 * t107 + 0.629120e6 / 0.27e2 * t144 * t145 / t67 / t102 / t93 * t151 - 0.532480e6 / 0.27e2 * t198 * t199 / t62 / t200 / r0 * t205 + 0.163840e6 / 0.27e2 * params.b * t143 * t56 * t145 * t58 / t200 / t60 / t150 / t72) - t5 * t53 * t87 * t76 / 0.2e1 + t5 * t85 * t119 * t76 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t117 * t164 * t76 + 0.10e2 / 0.27e2 * t5 * t162 * t398 * t76
  t404 = f.my_piecewise3(t1, 0, t403)
  t405 = t218 ** 2
  t408 = t226 ** 2
  t414 = t233 ** 2
  t420 = f.my_piecewise5(t14, 0, t10, 0, -t309)
  t424 = f.my_piecewise3(t219, 0, 0.40e2 / 0.81e2 / t221 / t405 * t408 - 0.16e2 / 0.9e1 * t223 * t226 * t233 + 0.4e1 / 0.3e1 * t230 * t414 + 0.16e2 / 0.9e1 * t231 * t237 + 0.4e1 / 0.3e1 * t220 * t420)
  t446 = f.my_piecewise3(t216, 0, -0.3e1 / 0.8e1 * t5 * t424 * t54 * t261 - t5 * t241 * t87 * t261 / 0.2e1 + t5 * t270 * t119 * t261 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t277 * t164 * t261 + 0.10e2 / 0.27e2 * t5 * t283 * t398 * t261)
  d1111 = 0.4e1 * t214 + 0.4e1 * t289 + t6 * (t404 + t446)

  res = {'v4rho4': d1111}
  return res
