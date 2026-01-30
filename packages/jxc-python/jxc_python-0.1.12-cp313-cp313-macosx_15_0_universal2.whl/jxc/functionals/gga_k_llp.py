"""Generated from gga_k_llp.mpl."""

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

  llp_f = lambda x: 1.0 + params_beta / X_FACTOR_C * x ** 2 / (1.0 + params_gamma * params_beta * x * jnp.arcsinh(x))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, llp_f, rs, zeta, xs0, xs1)

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

  llp_f = lambda x: 1.0 + params_beta / X_FACTOR_C * x ** 2 / (1.0 + params_gamma * params_beta * x * jnp.arcsinh(x))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, llp_f, rs, zeta, xs0, xs1)

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

  llp_f = lambda x: 1.0 + params_beta / X_FACTOR_C * x ** 2 / (1.0 + params_gamma * params_beta * x * jnp.arcsinh(x))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, llp_f, rs, zeta, xs0, xs1)

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
  t32 = params.beta * t3
  t34 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t35 = 0.1e1 / t34
  t36 = t32 * t35
  t37 = 4 ** (0.1e1 / 0.3e1)
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t44 = params.gamma * params.beta
  t45 = jnp.sqrt(s0)
  t47 = 0.1e1 / t40 / r0
  t48 = t45 * t47
  t49 = jnp.arcsinh(t48)
  t52 = 0.10e1 + t44 * t48 * t49
  t53 = 0.1e1 / t52
  t58 = 0.10e1 + 0.2e1 / 0.9e1 * t36 * t38 * t43 * t53
  t62 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t58)
  t63 = r1 <= f.p.dens_threshold
  t64 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t65 = 0.1e1 + t64
  t66 = t65 <= f.p.zeta_threshold
  t67 = t65 ** (0.1e1 / 0.3e1)
  t68 = t67 ** 2
  t70 = f.my_piecewise3(t66, t24, t68 * t65)
  t71 = t70 * t30
  t72 = t37 * s2
  t73 = r1 ** 2
  t74 = r1 ** (0.1e1 / 0.3e1)
  t75 = t74 ** 2
  t77 = 0.1e1 / t75 / t73
  t78 = jnp.sqrt(s2)
  t80 = 0.1e1 / t74 / r1
  t81 = t78 * t80
  t82 = jnp.arcsinh(t81)
  t85 = 0.10e1 + t44 * t81 * t82
  t86 = 0.1e1 / t85
  t91 = 0.10e1 + 0.2e1 / 0.9e1 * t36 * t72 * t77 * t86
  t95 = f.my_piecewise3(t63, 0, 0.3e1 / 0.20e2 * t6 * t71 * t91)
  t96 = t7 ** 2
  t98 = t17 / t96
  t99 = t8 - t98
  t100 = f.my_piecewise5(t11, 0, t15, 0, t99)
  t103 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t100)
  t108 = 0.1e1 / t29
  t112 = t6 * t28 * t108 * t58 / 0.10e2
  t115 = 0.1e1 / t41 / t39 / r0
  t121 = t32 * t35 * t37
  t122 = s0 * t43
  t123 = t52 ** 2
  t124 = 0.1e1 / t123
  t132 = jnp.sqrt(0.1e1 + t122)
  t133 = 0.1e1 / t132
  t147 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t103 * t30 * t58 + t112 + 0.3e1 / 0.20e2 * t6 * t31 * (-0.16e2 / 0.27e2 * t36 * t38 * t115 * t53 - 0.2e1 / 0.9e1 * t121 * t122 * t124 * (-0.4e1 / 0.3e1 * t44 * t45 / t40 / t39 * t49 - 0.4e1 / 0.3e1 * t44 * s0 * t115 * t133)))
  t149 = f.my_piecewise5(t15, 0, t11, 0, -t99)
  t152 = f.my_piecewise3(t66, 0, 0.5e1 / 0.3e1 * t68 * t149)
  t160 = t6 * t70 * t108 * t91 / 0.10e2
  t162 = f.my_piecewise3(t63, 0, 0.3e1 / 0.20e2 * t6 * t152 * t30 * t91 + t160)
  vrho_0_ = t62 + t95 + t7 * (t147 + t162)
  t165 = -t8 - t98
  t166 = f.my_piecewise5(t11, 0, t15, 0, t165)
  t169 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t166)
  t175 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t169 * t30 * t58 + t112)
  t177 = f.my_piecewise5(t15, 0, t11, 0, -t165)
  t180 = f.my_piecewise3(t66, 0, 0.5e1 / 0.3e1 * t68 * t177)
  t187 = 0.1e1 / t75 / t73 / r1
  t192 = s2 * t77
  t193 = t85 ** 2
  t194 = 0.1e1 / t193
  t202 = jnp.sqrt(0.1e1 + t192)
  t203 = 0.1e1 / t202
  t217 = f.my_piecewise3(t63, 0, 0.3e1 / 0.20e2 * t6 * t180 * t30 * t91 + t160 + 0.3e1 / 0.20e2 * t6 * t71 * (-0.16e2 / 0.27e2 * t36 * t72 * t187 * t86 - 0.2e1 / 0.9e1 * t121 * t192 * t194 * (-0.4e1 / 0.3e1 * t44 * t78 / t74 / t73 * t82 - 0.4e1 / 0.3e1 * t44 * s2 * t187 * t203)))
  vrho_1_ = t62 + t95 + t7 * (t175 + t217)
  t239 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.2e1 / 0.9e1 * t36 * t37 * t43 * t53 - 0.2e1 / 0.9e1 * t121 * t122 * t124 * (t44 / t45 * t47 * t49 / 0.2e1 + t44 * t43 * t133 / 0.2e1)))
  vsigma_0_ = t7 * t239
  vsigma_1_ = 0.0e0
  t259 = f.my_piecewise3(t63, 0, 0.3e1 / 0.20e2 * t6 * t71 * (0.2e1 / 0.9e1 * t36 * t37 * t77 * t86 - 0.2e1 / 0.9e1 * t121 * t192 * t194 * (t44 / t78 * t80 * t82 / 0.2e1 + t44 * t77 * t203 / 0.2e1)))
  vsigma_2_ = t7 * t259
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

  llp_f = lambda x: 1.0 + params_beta / X_FACTOR_C * x ** 2 / (1.0 + params_gamma * params_beta * x * jnp.arcsinh(x))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, llp_f, rs, zeta, xs0, xs1)

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
  t23 = t20 * t22
  t24 = params.beta * t4
  t26 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t26
  t28 = 4 ** (0.1e1 / 0.3e1)
  t30 = t24 * t27 * t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t36 = 0.1e1 / t22 / t34
  t37 = params.gamma * params.beta
  t38 = jnp.sqrt(s0)
  t39 = t37 * t38
  t41 = 0.1e1 / t21 / r0
  t45 = jnp.arcsinh(t38 * t31 * t41)
  t46 = t31 * t41 * t45
  t48 = 0.10e1 + t39 * t46
  t49 = 0.1e1 / t48
  t50 = t36 * t49
  t54 = 0.10e1 + 0.2e1 / 0.9e1 * t30 * t33 * t50
  t58 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t54)
  t66 = 0.1e1 / t22 / t34 / r0
  t71 = t48 ** 2
  t73 = t36 / t71
  t83 = jnp.sqrt(t33 * t36 + 0.1e1)
  t84 = 0.1e1 / t83
  t98 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t54 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-0.16e2 / 0.27e2 * t30 * t33 * t66 * t49 - 0.2e1 / 0.9e1 * t30 * t33 * t73 * (-0.4e1 / 0.3e1 * t39 * t31 / t21 / t34 * t45 - 0.4e1 / 0.3e1 * t37 * s0 * t32 * t66 * t84)))
  vrho_0_ = 0.2e1 * r0 * t98 + 0.2e1 * t58
  t121 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.2e1 / 0.9e1 * t24 * t27 * t28 * t32 * t50 - 0.2e1 / 0.9e1 * t30 * t33 * t73 * (t37 / t38 * t46 / 0.2e1 + t37 * t32 * t36 * t84 / 0.2e1)))
  vsigma_0_ = 0.2e1 * r0 * t121
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
  t23 = t20 / t21
  t24 = params.beta * t4
  t26 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t26
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = t27 * t28
  t30 = t24 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t37 = 0.1e1 / t35 / t34
  t38 = params.gamma * params.beta
  t39 = jnp.sqrt(s0)
  t40 = t38 * t39
  t42 = 0.1e1 / t21 / r0
  t46 = jnp.arcsinh(t39 * t31 * t42)
  t47 = t31 * t42 * t46
  t49 = 0.10e1 + t40 * t47
  t50 = 0.1e1 / t49
  t51 = t37 * t50
  t55 = 0.10e1 + 0.2e1 / 0.9e1 * t30 * t33 * t51
  t59 = t20 * t35
  t60 = t34 * r0
  t62 = 0.1e1 / t35 / t60
  t63 = t62 * t50
  t67 = t49 ** 2
  t68 = 0.1e1 / t67
  t69 = t37 * t68
  t73 = t31 / t21 / t34 * t46
  t75 = t38 * s0
  t78 = t33 * t37 + 0.1e1
  t79 = jnp.sqrt(t78)
  t80 = 0.1e1 / t79
  t81 = t32 * t62 * t80
  t84 = -0.4e1 / 0.3e1 * t40 * t73 - 0.4e1 / 0.3e1 * t75 * t81
  t89 = -0.16e2 / 0.27e2 * t30 * t33 * t63 - 0.2e1 / 0.9e1 * t30 * t33 * t69 * t84
  t94 = f.my_piecewise3(t2, 0, t7 * t23 * t55 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t59 * t89)
  t103 = t34 ** 2
  t105 = 0.1e1 / t35 / t103
  t110 = t62 * t68
  t116 = 0.1e1 / t67 / t49
  t117 = t37 * t116
  t118 = t84 ** 2
  t133 = s0 ** 2
  t140 = 0.1e1 / t79 / t78
  t154 = f.my_piecewise3(t2, 0, -t7 * t20 * t42 * t55 / 0.30e2 + t7 * t23 * t89 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t59 * (0.176e3 / 0.81e2 * t30 * t33 * t105 * t50 + 0.32e2 / 0.27e2 * t30 * t33 * t110 * t84 + 0.4e1 / 0.9e1 * t30 * t33 * t117 * t118 - 0.2e1 / 0.9e1 * t30 * t33 * t69 * (0.28e2 / 0.9e1 * t40 * t31 / t21 / t60 * t46 + 0.20e2 / 0.3e1 * t75 * t32 * t105 * t80 - 0.32e2 / 0.9e1 * t38 * t133 * t31 / t21 / t103 / t60 * t140)))
  v2rho2_0_ = 0.2e1 * r0 * t154 + 0.4e1 * t94
  t157 = t24 * t27
  t158 = t28 * t32
  t162 = t38 / t39
  t164 = t32 * t37
  t165 = t164 * t80
  t168 = t162 * t47 / 0.2e1 + t38 * t165 / 0.2e1
  t173 = -0.2e1 / 0.9e1 * t30 * t33 * t69 * t168 + 0.2e1 / 0.9e1 * t157 * t158 * t51
  t177 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t59 * t173)
  t221 = f.my_piecewise3(t2, 0, t7 * t23 * t173 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t59 * (-0.16e2 / 0.27e2 * t157 * t158 * t63 - 0.2e1 / 0.9e1 * t30 * t164 * t68 * t84 + 0.16e2 / 0.27e2 * t30 * t33 * t110 * t168 + 0.4e1 / 0.9e1 * t24 * t29 * s0 * t164 * t116 * t168 * t84 - 0.2e1 / 0.9e1 * t30 * t33 * t69 * (-0.2e1 / 0.3e1 * t162 * t73 - 0.2e1 * t38 * t81 + 0.4e1 / 0.3e1 * t38 * t31 / t21 / t103 / t34 * t140 * s0)))
  v2rhosigma_0_ = 0.2e1 * r0 * t221 + 0.2e1 * t177
  t228 = t168 ** 2
  t258 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t59 * (-0.4e1 / 0.9e1 * t30 * t164 * t68 * t168 + 0.4e1 / 0.9e1 * t30 * t33 * t117 * t228 - 0.2e1 / 0.9e1 * t30 * t33 * t69 * (-t38 / t39 / s0 * t47 / 0.4e1 + t38 / s0 * t165 / 0.4e1 - t38 * t31 / t21 / t103 / r0 * t140 / 0.2e1)))
  v2sigma2_0_ = 0.2e1 * r0 * t258
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
  t23 = 0.1e1 / t21 / r0
  t24 = t20 * t23
  t25 = params.beta * t4
  t27 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / t27 * t29
  t31 = t25 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = r0 ** 2
  t36 = t21 ** 2
  t38 = 0.1e1 / t36 / t35
  t39 = params.gamma * params.beta
  t40 = jnp.sqrt(s0)
  t41 = t39 * t40
  t45 = jnp.asinh(t40 * t32 * t23)
  t48 = 0.10e1 + t41 * t32 * t23 * t45
  t49 = 0.1e1 / t48
  t54 = 0.10e1 + 0.2e1 / 0.9e1 * t31 * t34 * t38 * t49
  t59 = t20 / t21
  t60 = t35 * r0
  t62 = 0.1e1 / t36 / t60
  t67 = t48 ** 2
  t68 = 0.1e1 / t67
  t69 = t38 * t68
  t71 = 0.1e1 / t21 / t35
  t75 = t39 * s0
  t78 = t34 * t38 + 0.1e1
  t79 = jnp.sqrt(t78)
  t80 = 0.1e1 / t79
  t84 = -0.4e1 / 0.3e1 * t41 * t32 * t71 * t45 - 0.4e1 / 0.3e1 * t75 * t33 * t62 * t80
  t89 = -0.16e2 / 0.27e2 * t31 * t34 * t62 * t49 - 0.2e1 / 0.9e1 * t31 * t34 * t69 * t84
  t93 = t20 * t36
  t94 = t35 ** 2
  t96 = 0.1e1 / t36 / t94
  t101 = t62 * t68
  t107 = 0.1e1 / t67 / t48
  t109 = t84 ** 2
  t124 = s0 ** 2
  t125 = t39 * t124
  t131 = 0.1e1 / t79 / t78
  t135 = 0.28e2 / 0.9e1 * t41 * t32 / t21 / t60 * t45 + 0.20e2 / 0.3e1 * t75 * t33 * t96 * t80 - 0.32e2 / 0.9e1 * t125 * t32 / t21 / t94 / t60 * t131
  t140 = 0.176e3 / 0.81e2 * t31 * t34 * t96 * t49 + 0.32e2 / 0.27e2 * t31 * t34 * t101 * t84 + 0.4e1 / 0.9e1 * t31 * t34 * t38 * t107 * t109 - 0.2e1 / 0.9e1 * t31 * t34 * t69 * t135
  t145 = f.my_piecewise3(t2, 0, -t7 * t24 * t54 / 0.30e2 + t7 * t59 * t89 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t93 * t140)
  t159 = 0.1e1 / t36 / t94 / r0
  t178 = t67 ** 2
  t204 = t94 ** 2
  t215 = t78 ** 2
  t231 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t71 * t54 - t7 * t24 * t89 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t59 * t140 + 0.3e1 / 0.20e2 * t7 * t93 * (-0.2464e4 / 0.243e3 * t31 * t34 * t159 * t49 - 0.176e3 / 0.27e2 * t31 * t34 * t96 * t68 * t84 - 0.32e2 / 0.9e1 * t31 * t34 * t62 * t107 * t109 + 0.16e2 / 0.9e1 * t31 * t34 * t101 * t135 - 0.4e1 / 0.3e1 * t31 * t34 * t38 / t178 * t109 * t84 + 0.4e1 / 0.3e1 * t25 * t30 * s0 * t33 * t38 * t107 * t84 * t135 - 0.2e1 / 0.9e1 * t31 * t34 * t69 * (-0.280e3 / 0.27e2 * t41 * t32 / t21 / t94 * t45 - 0.952e3 / 0.27e2 * t75 * t33 * t159 * t80 + 0.1184e4 / 0.27e2 * t125 * t32 / t21 / t204 * t131 - 0.256e3 / 0.9e1 * t39 * t124 * s0 / t204 / t60 / t79 / t215)))
  v3rho3_0_ = 0.2e1 * r0 * t231 + 0.6e1 * t145

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
  t24 = 0.1e1 / t22 / t21
  t25 = t20 * t24
  t26 = params.beta * t4
  t28 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t30 = 4 ** (0.1e1 / 0.3e1)
  t31 = 0.1e1 / t28 * t30
  t32 = t26 * t31
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = s0 * t34
  t36 = t22 ** 2
  t38 = 0.1e1 / t36 / t21
  t39 = params.gamma * params.beta
  t40 = jnp.sqrt(s0)
  t41 = t39 * t40
  t43 = 0.1e1 / t22 / r0
  t47 = jnp.asinh(t40 * t33 * t43)
  t50 = 0.10e1 + t41 * t33 * t43 * t47
  t51 = 0.1e1 / t50
  t56 = 0.10e1 + 0.2e1 / 0.9e1 * t32 * t35 * t38 * t51
  t60 = t20 * t43
  t61 = t21 * r0
  t63 = 0.1e1 / t36 / t61
  t68 = t50 ** 2
  t69 = 0.1e1 / t68
  t70 = t38 * t69
  t74 = t39 * s0
  t75 = t34 * t63
  t77 = t35 * t38 + 0.1e1
  t78 = jnp.sqrt(t77)
  t79 = 0.1e1 / t78
  t83 = -0.4e1 / 0.3e1 * t41 * t33 * t24 * t47 - 0.4e1 / 0.3e1 * t74 * t75 * t79
  t88 = -0.16e2 / 0.27e2 * t32 * t35 * t63 * t51 - 0.2e1 / 0.9e1 * t32 * t35 * t70 * t83
  t93 = t20 / t22
  t94 = t21 ** 2
  t96 = 0.1e1 / t36 / t94
  t101 = t63 * t69
  t107 = 0.1e1 / t68 / t50
  t108 = t38 * t107
  t109 = t83 ** 2
  t115 = 0.1e1 / t22 / t61
  t124 = s0 ** 2
  t125 = t39 * t124
  t131 = 0.1e1 / t78 / t77
  t135 = 0.28e2 / 0.9e1 * t41 * t33 * t115 * t47 + 0.20e2 / 0.3e1 * t74 * t34 * t96 * t79 - 0.32e2 / 0.9e1 * t125 * t33 / t22 / t94 / t61 * t131
  t140 = 0.176e3 / 0.81e2 * t32 * t35 * t96 * t51 + 0.32e2 / 0.27e2 * t32 * t35 * t101 * t83 + 0.4e1 / 0.9e1 * t32 * t35 * t108 * t109 - 0.2e1 / 0.9e1 * t32 * t35 * t70 * t135
  t144 = t20 * t36
  t145 = t94 * r0
  t147 = 0.1e1 / t36 / t145
  t152 = t96 * t69
  t166 = t68 ** 2
  t167 = 0.1e1 / t166
  t169 = t109 * t83
  t175 = t26 * t31 * s0
  t176 = t34 * t38
  t177 = t107 * t83
  t178 = t177 * t135
  t192 = t94 ** 2
  t199 = t124 * s0
  t203 = t77 ** 2
  t205 = 0.1e1 / t78 / t203
  t209 = -0.280e3 / 0.27e2 * t41 * t33 / t22 / t94 * t47 - 0.952e3 / 0.27e2 * t74 * t34 * t147 * t79 + 0.1184e4 / 0.27e2 * t125 * t33 / t22 / t192 * t131 - 0.256e3 / 0.9e1 * t39 * t199 / t192 / t61 * t205
  t214 = -0.2464e4 / 0.243e3 * t32 * t35 * t147 * t51 - 0.176e3 / 0.27e2 * t32 * t35 * t152 * t83 - 0.32e2 / 0.9e1 * t32 * t35 * t63 * t107 * t109 + 0.16e2 / 0.9e1 * t32 * t35 * t101 * t135 - 0.4e1 / 0.3e1 * t32 * t35 * t38 * t167 * t169 + 0.4e1 / 0.3e1 * t175 * t176 * t178 - 0.2e1 / 0.9e1 * t32 * t35 * t70 * t209
  t219 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t56 - t7 * t60 * t88 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t93 * t140 + 0.3e1 / 0.20e2 * t7 * t144 * t214)
  t234 = t94 * t21
  t236 = 0.1e1 / t36 / t234
  t270 = t109 ** 2
  t280 = t135 ** 2
  t312 = t124 ** 2
  t329 = 0.41888e5 / 0.729e3 * t32 * t35 * t236 * t51 + 0.9856e4 / 0.243e3 * t32 * t35 * t147 * t69 * t83 + 0.704e3 / 0.27e2 * t32 * t35 * t96 * t107 * t109 - 0.352e3 / 0.27e2 * t32 * t35 * t152 * t135 + 0.128e3 / 0.9e1 * t32 * t35 * t63 * t167 * t169 - 0.128e3 / 0.9e1 * t175 * t75 * t178 + 0.64e2 / 0.27e2 * t32 * t35 * t101 * t209 + 0.16e2 / 0.3e1 * t32 * t35 * t38 / t166 / t50 * t270 - 0.8e1 * t175 * t176 * t167 * t109 * t135 + 0.4e1 / 0.3e1 * t32 * t35 * t108 * t280 + 0.16e2 / 0.9e1 * t175 * t176 * t177 * t209 - 0.2e1 / 0.9e1 * t32 * t35 * t70 * (0.3640e4 / 0.81e2 * t41 * t33 / t22 / t145 * t47 + 0.5768e4 / 0.27e2 * t74 * t34 * t236 * t79 - 0.37216e5 / 0.81e2 * t125 * t33 / t22 / t192 / r0 * t131 + 0.17920e5 / 0.27e2 * t39 * t199 / t192 / t94 * t205 - 0.5120e4 / 0.27e2 * t39 * t312 / t36 / t192 / t234 / t78 / t203 / t77 * t34)
  t334 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t115 * t56 + 0.8e1 / 0.45e2 * t7 * t25 * t88 - t7 * t60 * t140 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t93 * t214 + 0.3e1 / 0.20e2 * t7 * t144 * t329)
  v4rho4_0_ = 0.2e1 * r0 * t334 + 0.8e1 * t219

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
  t35 = params.beta * t3
  t37 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t37
  t39 = t35 * t38
  t40 = 4 ** (0.1e1 / 0.3e1)
  t41 = t40 * s0
  t42 = r0 ** 2
  t43 = r0 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t46 = 0.1e1 / t44 / t42
  t47 = params.gamma * params.beta
  t48 = jnp.sqrt(s0)
  t51 = t48 / t43 / r0
  t52 = jnp.arcsinh(t51)
  t55 = 0.10e1 + t47 * t51 * t52
  t56 = 0.1e1 / t55
  t61 = 0.10e1 + 0.2e1 / 0.9e1 * t39 * t41 * t46 * t56
  t65 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t67 = t66 * f.p.zeta_threshold
  t69 = f.my_piecewise3(t21, t67, t23 * t20)
  t70 = 0.1e1 / t32
  t71 = t69 * t70
  t74 = t6 * t71 * t61 / 0.10e2
  t75 = t69 * t33
  t76 = t42 * r0
  t78 = 0.1e1 / t44 / t76
  t84 = t35 * t38 * t40
  t85 = s0 * t46
  t86 = t55 ** 2
  t87 = 0.1e1 / t86
  t93 = s0 * t78
  t94 = 0.1e1 + t85
  t95 = jnp.sqrt(t94)
  t96 = 0.1e1 / t95
  t100 = -0.4e1 / 0.3e1 * t47 * t48 / t43 / t42 * t52 - 0.4e1 / 0.3e1 * t47 * t93 * t96
  t101 = t87 * t100
  t105 = -0.16e2 / 0.27e2 * t39 * t41 * t78 * t56 - 0.2e1 / 0.9e1 * t84 * t85 * t101
  t110 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t61 + t74 + 0.3e1 / 0.20e2 * t6 * t75 * t105)
  t112 = r1 <= f.p.dens_threshold
  t113 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t114 = 0.1e1 + t113
  t115 = t114 <= f.p.zeta_threshold
  t116 = t114 ** (0.1e1 / 0.3e1)
  t117 = t116 ** 2
  t119 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t122 = f.my_piecewise3(t115, 0, 0.5e1 / 0.3e1 * t117 * t119)
  t123 = t122 * t33
  t124 = t40 * s2
  t125 = r1 ** 2
  t126 = r1 ** (0.1e1 / 0.3e1)
  t127 = t126 ** 2
  t129 = 0.1e1 / t127 / t125
  t130 = jnp.sqrt(s2)
  t133 = t130 / t126 / r1
  t134 = jnp.arcsinh(t133)
  t137 = 0.10e1 + t47 * t133 * t134
  t138 = 0.1e1 / t137
  t143 = 0.10e1 + 0.2e1 / 0.9e1 * t39 * t124 * t129 * t138
  t148 = f.my_piecewise3(t115, t67, t117 * t114)
  t149 = t148 * t70
  t152 = t6 * t149 * t143 / 0.10e2
  t154 = f.my_piecewise3(t112, 0, 0.3e1 / 0.20e2 * t6 * t123 * t143 + t152)
  t156 = 0.1e1 / t22
  t157 = t28 ** 2
  t162 = t17 / t24 / t7
  t164 = -0.2e1 * t25 + 0.2e1 * t162
  t165 = f.my_piecewise5(t11, 0, t15, 0, t164)
  t169 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t156 * t157 + 0.5e1 / 0.3e1 * t23 * t165)
  t176 = t6 * t31 * t70 * t61
  t182 = 0.1e1 / t32 / t7
  t186 = t6 * t69 * t182 * t61 / 0.30e2
  t188 = t6 * t71 * t105
  t190 = t42 ** 2
  t192 = 0.1e1 / t44 / t190
  t202 = t100 ** 2
  t217 = s0 ** 2
  t237 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t169 * t33 * t61 + t176 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t105 - t186 + t188 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t75 * (0.176e3 / 0.81e2 * t39 * t41 * t192 * t56 + 0.32e2 / 0.27e2 * t84 * t93 * t101 + 0.4e1 / 0.9e1 * t84 * t85 / t86 / t55 * t202 - 0.2e1 / 0.9e1 * t84 * t85 * t87 * (0.28e2 / 0.9e1 * t47 * t48 / t43 / t76 * t52 + 0.20e2 / 0.3e1 * t47 * s0 * t192 * t96 - 0.16e2 / 0.9e1 * t47 * t217 / t43 / t190 / t76 / t95 / t94)))
  t238 = 0.1e1 / t116
  t239 = t119 ** 2
  t243 = f.my_piecewise5(t15, 0, t11, 0, -t164)
  t247 = f.my_piecewise3(t115, 0, 0.10e2 / 0.9e1 * t238 * t239 + 0.5e1 / 0.3e1 * t117 * t243)
  t254 = t6 * t122 * t70 * t143
  t259 = t6 * t148 * t182 * t143 / 0.30e2
  t261 = f.my_piecewise3(t112, 0, 0.3e1 / 0.20e2 * t6 * t247 * t33 * t143 + t254 / 0.5e1 - t259)
  d11 = 0.2e1 * t110 + 0.2e1 * t154 + t7 * (t237 + t261)
  t264 = -t8 - t26
  t265 = f.my_piecewise5(t11, 0, t15, 0, t264)
  t268 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t265)
  t269 = t268 * t33
  t274 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t269 * t61 + t74)
  t276 = f.my_piecewise5(t15, 0, t11, 0, -t264)
  t279 = f.my_piecewise3(t115, 0, 0.5e1 / 0.3e1 * t117 * t276)
  t280 = t279 * t33
  t284 = t148 * t33
  t285 = t125 * r1
  t287 = 0.1e1 / t127 / t285
  t292 = s2 * t129
  t293 = t137 ** 2
  t294 = 0.1e1 / t293
  t300 = s2 * t287
  t301 = 0.1e1 + t292
  t302 = jnp.sqrt(t301)
  t303 = 0.1e1 / t302
  t307 = -0.4e1 / 0.3e1 * t47 * t130 / t126 / t125 * t134 - 0.4e1 / 0.3e1 * t47 * t300 * t303
  t308 = t294 * t307
  t312 = -0.16e2 / 0.27e2 * t39 * t124 * t287 * t138 - 0.2e1 / 0.9e1 * t84 * t292 * t308
  t317 = f.my_piecewise3(t112, 0, 0.3e1 / 0.20e2 * t6 * t280 * t143 + t152 + 0.3e1 / 0.20e2 * t6 * t284 * t312)
  t321 = 0.2e1 * t162
  t322 = f.my_piecewise5(t11, 0, t15, 0, t321)
  t326 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t156 * t265 * t28 + 0.5e1 / 0.3e1 * t23 * t322)
  t333 = t6 * t268 * t70 * t61
  t341 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t326 * t33 * t61 + t333 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t269 * t105 + t176 / 0.10e2 - t186 + t188 / 0.10e2)
  t345 = f.my_piecewise5(t15, 0, t11, 0, -t321)
  t349 = f.my_piecewise3(t115, 0, 0.10e2 / 0.9e1 * t238 * t276 * t119 + 0.5e1 / 0.3e1 * t117 * t345)
  t356 = t6 * t279 * t70 * t143
  t363 = t6 * t149 * t312
  t366 = f.my_piecewise3(t112, 0, 0.3e1 / 0.20e2 * t6 * t349 * t33 * t143 + t356 / 0.10e2 + t254 / 0.10e2 - t259 + 0.3e1 / 0.20e2 * t6 * t123 * t312 + t363 / 0.10e2)
  d12 = t110 + t154 + t274 + t317 + t7 * (t341 + t366)
  t371 = t265 ** 2
  t375 = 0.2e1 * t25 + 0.2e1 * t162
  t376 = f.my_piecewise5(t11, 0, t15, 0, t375)
  t380 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t156 * t371 + 0.5e1 / 0.3e1 * t23 * t376)
  t387 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t380 * t33 * t61 + t333 / 0.5e1 - t186)
  t388 = t276 ** 2
  t392 = f.my_piecewise5(t15, 0, t11, 0, -t375)
  t396 = f.my_piecewise3(t115, 0, 0.10e2 / 0.9e1 * t238 * t388 + 0.5e1 / 0.3e1 * t117 * t392)
  t406 = t125 ** 2
  t408 = 0.1e1 / t127 / t406
  t418 = t307 ** 2
  t433 = s2 ** 2
  t453 = f.my_piecewise3(t112, 0, 0.3e1 / 0.20e2 * t6 * t396 * t33 * t143 + t356 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t280 * t312 - t259 + t363 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t284 * (0.176e3 / 0.81e2 * t39 * t124 * t408 * t138 + 0.32e2 / 0.27e2 * t84 * t300 * t308 + 0.4e1 / 0.9e1 * t84 * t292 / t293 / t137 * t418 - 0.2e1 / 0.9e1 * t84 * t292 * t294 * (0.28e2 / 0.9e1 * t47 * t130 / t126 / t285 * t134 + 0.20e2 / 0.3e1 * t47 * s2 * t408 * t303 - 0.16e2 / 0.9e1 * t47 * t433 / t126 / t406 / t285 / t302 / t301)))
  d22 = 0.2e1 * t274 + 0.2e1 * t317 + t7 * (t387 + t453)
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
  t46 = params.beta * t3
  t48 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t49 = 0.1e1 / t48
  t50 = t46 * t49
  t51 = 4 ** (0.1e1 / 0.3e1)
  t52 = t51 * s0
  t53 = r0 ** 2
  t54 = r0 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t57 = 0.1e1 / t55 / t53
  t58 = params.gamma * params.beta
  t59 = jnp.sqrt(s0)
  t62 = t59 / t54 / r0
  t63 = jnp.asinh(t62)
  t66 = 0.10e1 + t58 * t62 * t63
  t67 = 0.1e1 / t66
  t72 = 0.10e1 + 0.2e1 / 0.9e1 * t50 * t52 * t57 * t67
  t78 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t79 = 0.1e1 / t43
  t80 = t78 * t79
  t84 = t78 * t44
  t85 = t53 * r0
  t87 = 0.1e1 / t55 / t85
  t93 = t46 * t49 * t51
  t94 = s0 * t57
  t95 = t66 ** 2
  t96 = 0.1e1 / t95
  t102 = s0 * t87
  t103 = 0.1e1 + t94
  t104 = jnp.sqrt(t103)
  t105 = 0.1e1 / t104
  t109 = -0.4e1 / 0.3e1 * t58 * t59 / t54 / t53 * t63 - 0.4e1 / 0.3e1 * t58 * t102 * t105
  t110 = t96 * t109
  t114 = -0.16e2 / 0.27e2 * t50 * t52 * t87 * t67 - 0.2e1 / 0.9e1 * t93 * t94 * t110
  t118 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t119 = t118 ** 2
  t120 = t119 * f.p.zeta_threshold
  t122 = f.my_piecewise3(t21, t120, t32 * t20)
  t124 = 0.1e1 / t43 / t7
  t125 = t122 * t124
  t129 = t122 * t79
  t133 = t122 * t44
  t134 = t53 ** 2
  t136 = 0.1e1 / t55 / t134
  t145 = 0.1e1 / t95 / t66
  t146 = t109 ** 2
  t147 = t145 * t146
  t157 = s0 * t136
  t161 = s0 ** 2
  t167 = 0.1e1 / t104 / t103
  t171 = 0.28e2 / 0.9e1 * t58 * t59 / t54 / t85 * t63 + 0.20e2 / 0.3e1 * t58 * t157 * t105 - 0.16e2 / 0.9e1 * t58 * t161 / t54 / t134 / t85 * t167
  t172 = t96 * t171
  t176 = 0.176e3 / 0.81e2 * t50 * t52 * t136 * t67 + 0.32e2 / 0.27e2 * t93 * t102 * t110 + 0.4e1 / 0.9e1 * t93 * t94 * t147 - 0.2e1 / 0.9e1 * t93 * t94 * t172
  t181 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t72 + t6 * t80 * t72 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t84 * t114 - t6 * t125 * t72 / 0.30e2 + t6 * t129 * t114 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t133 * t176)
  t183 = r1 <= f.p.dens_threshold
  t184 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t185 = 0.1e1 + t184
  t186 = t185 <= f.p.zeta_threshold
  t187 = t185 ** (0.1e1 / 0.3e1)
  t188 = 0.1e1 / t187
  t190 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t191 = t190 ** 2
  t194 = t187 ** 2
  t196 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t200 = f.my_piecewise3(t186, 0, 0.10e2 / 0.9e1 * t188 * t191 + 0.5e1 / 0.3e1 * t194 * t196)
  t203 = r1 ** 2
  t204 = r1 ** (0.1e1 / 0.3e1)
  t205 = t204 ** 2
  t208 = jnp.sqrt(s2)
  t211 = t208 / t204 / r1
  t212 = jnp.asinh(t211)
  t221 = 0.10e1 + 0.2e1 / 0.9e1 * t50 * t51 * s2 / t205 / t203 / (0.10e1 + t58 * t211 * t212)
  t227 = f.my_piecewise3(t186, 0, 0.5e1 / 0.3e1 * t194 * t190)
  t233 = f.my_piecewise3(t186, t120, t194 * t185)
  t239 = f.my_piecewise3(t183, 0, 0.3e1 / 0.20e2 * t6 * t200 * t44 * t221 + t6 * t227 * t79 * t221 / 0.5e1 - t6 * t233 * t124 * t221 / 0.30e2)
  t249 = t24 ** 2
  t253 = 0.6e1 * t34 - 0.6e1 * t17 / t249
  t254 = f.my_piecewise5(t11, 0, t15, 0, t253)
  t258 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t254)
  t281 = 0.1e1 / t43 / t24
  t294 = 0.1e1 / t55 / t134 / r0
  t308 = t95 ** 2
  t330 = t134 ** 2
  t341 = t103 ** 2
  t357 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t258 * t44 * t72 + 0.3e1 / 0.10e2 * t6 * t42 * t79 * t72 + 0.9e1 / 0.20e2 * t6 * t45 * t114 - t6 * t78 * t124 * t72 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t80 * t114 + 0.9e1 / 0.20e2 * t6 * t84 * t176 + 0.2e1 / 0.45e2 * t6 * t122 * t281 * t72 - t6 * t125 * t114 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t129 * t176 + 0.3e1 / 0.20e2 * t6 * t133 * (-0.2464e4 / 0.243e3 * t50 * t52 * t294 * t67 - 0.176e3 / 0.27e2 * t93 * t157 * t110 - 0.32e2 / 0.9e1 * t93 * t102 * t147 + 0.16e2 / 0.9e1 * t93 * t102 * t172 - 0.4e1 / 0.3e1 * t93 * t94 / t308 * t146 * t109 + 0.4e1 / 0.3e1 * t93 * t94 * t145 * t109 * t171 - 0.2e1 / 0.9e1 * t93 * t94 * t96 * (-0.280e3 / 0.27e2 * t58 * t59 / t54 / t134 * t63 - 0.952e3 / 0.27e2 * t58 * s0 * t294 * t105 + 0.592e3 / 0.27e2 * t58 * t161 / t54 / t330 * t167 - 0.64e2 / 0.9e1 * t58 * t161 * s0 / t330 / t85 / t104 / t341)))
  t367 = f.my_piecewise5(t15, 0, t11, 0, -t253)
  t371 = f.my_piecewise3(t186, 0, -0.10e2 / 0.27e2 / t187 / t185 * t191 * t190 + 0.10e2 / 0.3e1 * t188 * t190 * t196 + 0.5e1 / 0.3e1 * t194 * t367)
  t389 = f.my_piecewise3(t183, 0, 0.3e1 / 0.20e2 * t6 * t371 * t44 * t221 + 0.3e1 / 0.10e2 * t6 * t200 * t79 * t221 - t6 * t227 * t124 * t221 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t233 * t281 * t221)
  d111 = 0.3e1 * t181 + 0.3e1 * t239 + t7 * (t357 + t389)

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
  t58 = params.beta * t3
  t60 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t61 = 0.1e1 / t60
  t62 = t58 * t61
  t63 = 4 ** (0.1e1 / 0.3e1)
  t64 = t63 * s0
  t65 = r0 ** 2
  t66 = r0 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t69 = 0.1e1 / t67 / t65
  t70 = params.gamma * params.beta
  t71 = jnp.sqrt(s0)
  t74 = t71 / t66 / r0
  t75 = jnp.asinh(t74)
  t78 = 0.10e1 + t70 * t74 * t75
  t79 = 0.1e1 / t78
  t84 = 0.10e1 + 0.2e1 / 0.9e1 * t62 * t64 * t69 * t79
  t93 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t94 = 0.1e1 / t55
  t95 = t93 * t94
  t99 = t93 * t56
  t100 = t65 * r0
  t102 = 0.1e1 / t67 / t100
  t108 = t58 * t61 * t63
  t109 = s0 * t69
  t110 = t78 ** 2
  t111 = 0.1e1 / t110
  t117 = s0 * t102
  t118 = 0.1e1 + t109
  t119 = jnp.sqrt(t118)
  t120 = 0.1e1 / t119
  t124 = -0.4e1 / 0.3e1 * t70 * t71 / t66 / t65 * t75 - 0.4e1 / 0.3e1 * t70 * t117 * t120
  t125 = t111 * t124
  t129 = -0.16e2 / 0.27e2 * t62 * t64 * t102 * t79 - 0.2e1 / 0.9e1 * t108 * t109 * t125
  t135 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t137 = 0.1e1 / t55 / t7
  t138 = t135 * t137
  t142 = t135 * t94
  t146 = t135 * t56
  t147 = t65 ** 2
  t149 = 0.1e1 / t67 / t147
  t158 = 0.1e1 / t110 / t78
  t159 = t124 ** 2
  t160 = t158 * t159
  t170 = s0 * t149
  t174 = s0 ** 2
  t180 = 0.1e1 / t119 / t118
  t184 = 0.28e2 / 0.9e1 * t70 * t71 / t66 / t100 * t75 + 0.20e2 / 0.3e1 * t70 * t170 * t120 - 0.16e2 / 0.9e1 * t70 * t174 / t66 / t147 / t100 * t180
  t185 = t111 * t184
  t189 = 0.176e3 / 0.81e2 * t62 * t64 * t149 * t79 + 0.32e2 / 0.27e2 * t108 * t117 * t125 + 0.4e1 / 0.9e1 * t108 * t109 * t160 - 0.2e1 / 0.9e1 * t108 * t109 * t185
  t193 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t194 = t193 ** 2
  t195 = t194 * f.p.zeta_threshold
  t197 = f.my_piecewise3(t21, t195, t44 * t20)
  t199 = 0.1e1 / t55 / t25
  t200 = t197 * t199
  t204 = t197 * t137
  t208 = t197 * t94
  t212 = t197 * t56
  t213 = t147 * r0
  t215 = 0.1e1 / t67 / t213
  t229 = t110 ** 2
  t230 = 0.1e1 / t229
  t232 = t230 * t159 * t124
  t236 = t158 * t124
  t237 = t236 * t184
  t247 = s0 * t215
  t251 = t147 ** 2
  t258 = t174 * s0
  t262 = t118 ** 2
  t264 = 0.1e1 / t119 / t262
  t268 = -0.280e3 / 0.27e2 * t70 * t71 / t66 / t147 * t75 - 0.952e3 / 0.27e2 * t70 * t247 * t120 + 0.592e3 / 0.27e2 * t70 * t174 / t66 / t251 * t180 - 0.64e2 / 0.9e1 * t70 * t258 / t251 / t100 * t264
  t269 = t111 * t268
  t273 = -0.2464e4 / 0.243e3 * t62 * t64 * t215 * t79 - 0.176e3 / 0.27e2 * t108 * t170 * t125 - 0.32e2 / 0.9e1 * t108 * t117 * t160 + 0.16e2 / 0.9e1 * t108 * t117 * t185 - 0.4e1 / 0.3e1 * t108 * t109 * t232 + 0.4e1 / 0.3e1 * t108 * t109 * t237 - 0.2e1 / 0.9e1 * t108 * t109 * t269
  t278 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t84 + 0.3e1 / 0.10e2 * t6 * t95 * t84 + 0.9e1 / 0.20e2 * t6 * t99 * t129 - t6 * t138 * t84 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t142 * t129 + 0.9e1 / 0.20e2 * t6 * t146 * t189 + 0.2e1 / 0.45e2 * t6 * t200 * t84 - t6 * t204 * t129 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t208 * t189 + 0.3e1 / 0.20e2 * t6 * t212 * t273)
  t280 = r1 <= f.p.dens_threshold
  t281 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t282 = 0.1e1 + t281
  t283 = t282 <= f.p.zeta_threshold
  t284 = t282 ** (0.1e1 / 0.3e1)
  t286 = 0.1e1 / t284 / t282
  t288 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t289 = t288 ** 2
  t293 = 0.1e1 / t284
  t294 = t293 * t288
  t296 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t299 = t284 ** 2
  t301 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t305 = f.my_piecewise3(t283, 0, -0.10e2 / 0.27e2 * t286 * t289 * t288 + 0.10e2 / 0.3e1 * t294 * t296 + 0.5e1 / 0.3e1 * t299 * t301)
  t308 = r1 ** 2
  t309 = r1 ** (0.1e1 / 0.3e1)
  t310 = t309 ** 2
  t313 = jnp.sqrt(s2)
  t316 = t313 / t309 / r1
  t317 = jnp.asinh(t316)
  t326 = 0.10e1 + 0.2e1 / 0.9e1 * t62 * t63 * s2 / t310 / t308 / (0.10e1 + t70 * t316 * t317)
  t335 = f.my_piecewise3(t283, 0, 0.10e2 / 0.9e1 * t293 * t289 + 0.5e1 / 0.3e1 * t299 * t296)
  t342 = f.my_piecewise3(t283, 0, 0.5e1 / 0.3e1 * t299 * t288)
  t348 = f.my_piecewise3(t283, t195, t299 * t282)
  t354 = f.my_piecewise3(t280, 0, 0.3e1 / 0.20e2 * t6 * t305 * t56 * t326 + 0.3e1 / 0.10e2 * t6 * t335 * t94 * t326 - t6 * t342 * t137 * t326 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t348 * t199 * t326)
  t356 = t147 * t65
  t358 = 0.1e1 / t67 / t356
  t383 = t159 ** 2
  t393 = t184 ** 2
  t425 = t174 ** 2
  t441 = 0.41888e5 / 0.729e3 * t62 * t64 * t358 * t79 + 0.9856e4 / 0.243e3 * t108 * t247 * t125 + 0.704e3 / 0.27e2 * t108 * t170 * t160 - 0.352e3 / 0.27e2 * t108 * t170 * t185 + 0.128e3 / 0.9e1 * t108 * t117 * t232 - 0.128e3 / 0.9e1 * t108 * t117 * t237 + 0.64e2 / 0.27e2 * t108 * t117 * t269 + 0.16e2 / 0.3e1 * t108 * t109 / t229 / t78 * t383 - 0.8e1 * t108 * t109 * t230 * t159 * t184 + 0.4e1 / 0.3e1 * t108 * t109 * t158 * t393 + 0.16e2 / 0.9e1 * t108 * t109 * t236 * t268 - 0.2e1 / 0.9e1 * t108 * t109 * t111 * (0.3640e4 / 0.81e2 * t70 * t71 / t66 / t213 * t75 + 0.5768e4 / 0.27e2 * t70 * s0 * t358 * t120 - 0.18608e5 / 0.81e2 * t70 * t174 / t66 / t251 / r0 * t180 + 0.4480e4 / 0.27e2 * t70 * t258 / t251 / t147 * t264 - 0.1280e4 / 0.27e2 * t70 * t425 / t67 / t251 / t356 / t119 / t262 / t118)
  t460 = t20 ** 2
  t463 = t30 ** 2
  t469 = t41 ** 2
  t478 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t479 = f.my_piecewise5(t11, 0, t15, 0, t478)
  t483 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t460 * t463 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t469 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t479)
  t513 = 0.1e1 / t55 / t36
  t518 = 0.3e1 / 0.20e2 * t6 * t212 * t441 - t6 * t204 * t189 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t208 * t273 + 0.8e1 / 0.45e2 * t6 * t200 * t129 + 0.6e1 / 0.5e1 * t6 * t142 * t189 + 0.3e1 / 0.5e1 * t6 * t146 * t273 + 0.3e1 / 0.20e2 * t6 * t483 * t56 * t84 + 0.3e1 / 0.5e1 * t6 * t57 * t129 + 0.6e1 / 0.5e1 * t6 * t95 * t129 + 0.9e1 / 0.10e2 * t6 * t99 * t189 - 0.2e1 / 0.5e1 * t6 * t138 * t129 + 0.2e1 / 0.5e1 * t6 * t54 * t94 * t84 - t6 * t93 * t137 * t84 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t135 * t199 * t84 - 0.14e2 / 0.135e3 * t6 * t197 * t513 * t84
  t519 = f.my_piecewise3(t1, 0, t518)
  t520 = t282 ** 2
  t523 = t289 ** 2
  t529 = t296 ** 2
  t535 = f.my_piecewise5(t15, 0, t11, 0, -t478)
  t539 = f.my_piecewise3(t283, 0, 0.40e2 / 0.81e2 / t284 / t520 * t523 - 0.20e2 / 0.9e1 * t286 * t289 * t296 + 0.10e2 / 0.3e1 * t293 * t529 + 0.40e2 / 0.9e1 * t294 * t301 + 0.5e1 / 0.3e1 * t299 * t535)
  t561 = f.my_piecewise3(t280, 0, 0.3e1 / 0.20e2 * t6 * t539 * t56 * t326 + 0.2e1 / 0.5e1 * t6 * t305 * t94 * t326 - t6 * t335 * t137 * t326 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t342 * t199 * t326 - 0.14e2 / 0.135e3 * t6 * t348 * t513 * t326)
  d1111 = 0.4e1 * t278 + 0.4e1 * t354 + t7 * (t519 + t561)

  res = {'v4rho4': d1111}
  return res
