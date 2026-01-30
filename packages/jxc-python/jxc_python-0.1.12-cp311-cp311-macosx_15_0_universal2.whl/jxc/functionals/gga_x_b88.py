"""Generated from gga_x_b88.mpl."""

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

  b88_f = lambda x: 1 + params_beta / X_FACTOR_C * x ** 2 / (1 + params_gamma * params_beta * x * jnp.arcsinh(x))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, b88_f, rs, zeta, xs0, xs1)

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

  b88_f = lambda x: 1 + params_beta / X_FACTOR_C * x ** 2 / (1 + params_gamma * params_beta * x * jnp.arcsinh(x))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, b88_f, rs, zeta, xs0, xs1)

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

  b88_f = lambda x: 1 + params_beta / X_FACTOR_C * x ** 2 / (1 + params_gamma * params_beta * x * jnp.arcsinh(x))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, b88_f, rs, zeta, xs0, xs1)

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
  t28 = t2 ** 2
  t29 = params.beta * t28
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = t29 * t32
  t34 = 4 ** (0.1e1 / 0.3e1)
  t35 = t34 * s0
  t36 = r0 ** 2
  t37 = r0 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t40 = 0.1e1 / t38 / t36
  t41 = params.gamma * params.beta
  t42 = jnp.sqrt(s0)
  t44 = 0.1e1 / t37 / r0
  t45 = t42 * t44
  t46 = jnp.arcsinh(t45)
  t49 = t41 * t45 * t46 + 0.1e1
  t50 = 0.1e1 / t49
  t55 = 0.1e1 + 0.2e1 / 0.9e1 * t33 * t35 * t40 * t50
  t59 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t55)
  t60 = r1 <= f.p.dens_threshold
  t61 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t62 = 0.1e1 + t61
  t63 = t62 <= f.p.zeta_threshold
  t64 = t62 ** (0.1e1 / 0.3e1)
  t66 = f.my_piecewise3(t63, t22, t64 * t62)
  t67 = t66 * t26
  t68 = t34 * s2
  t69 = r1 ** 2
  t70 = r1 ** (0.1e1 / 0.3e1)
  t71 = t70 ** 2
  t73 = 0.1e1 / t71 / t69
  t74 = jnp.sqrt(s2)
  t76 = 0.1e1 / t70 / r1
  t77 = t74 * t76
  t78 = jnp.arcsinh(t77)
  t81 = t41 * t77 * t78 + 0.1e1
  t82 = 0.1e1 / t81
  t87 = 0.1e1 + 0.2e1 / 0.9e1 * t33 * t68 * t73 * t82
  t91 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t67 * t87)
  t92 = t6 ** 2
  t94 = t16 / t92
  t95 = t7 - t94
  t96 = f.my_piecewise5(t10, 0, t14, 0, t95)
  t99 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t96)
  t104 = t26 ** 2
  t105 = 0.1e1 / t104
  t109 = t5 * t25 * t105 * t55 / 0.8e1
  t112 = 0.1e1 / t38 / t36 / r0
  t118 = t29 * t32 * t34
  t119 = s0 * t40
  t120 = t49 ** 2
  t121 = 0.1e1 / t120
  t129 = jnp.sqrt(0.1e1 + t119)
  t130 = 0.1e1 / t129
  t144 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t99 * t26 * t55 - t109 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.16e2 / 0.27e2 * t33 * t35 * t112 * t50 - 0.2e1 / 0.9e1 * t118 * t119 * t121 * (-0.4e1 / 0.3e1 * t41 * t42 / t37 / t36 * t46 - 0.4e1 / 0.3e1 * t41 * s0 * t112 * t130)))
  t146 = f.my_piecewise5(t14, 0, t10, 0, -t95)
  t149 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t146)
  t157 = t5 * t66 * t105 * t87 / 0.8e1
  t159 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t149 * t26 * t87 - t157)
  vrho_0_ = t59 + t91 + t6 * (t144 + t159)
  t162 = -t7 - t94
  t163 = f.my_piecewise5(t10, 0, t14, 0, t162)
  t166 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t163)
  t172 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t166 * t26 * t55 - t109)
  t174 = f.my_piecewise5(t14, 0, t10, 0, -t162)
  t177 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t174)
  t184 = 0.1e1 / t71 / t69 / r1
  t189 = s2 * t73
  t190 = t81 ** 2
  t191 = 0.1e1 / t190
  t199 = jnp.sqrt(0.1e1 + t189)
  t200 = 0.1e1 / t199
  t214 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t177 * t26 * t87 - t157 - 0.3e1 / 0.8e1 * t5 * t67 * (-0.16e2 / 0.27e2 * t33 * t68 * t184 * t82 - 0.2e1 / 0.9e1 * t118 * t189 * t191 * (-0.4e1 / 0.3e1 * t41 * t74 / t70 / t69 * t78 - 0.4e1 / 0.3e1 * t41 * s2 * t184 * t200)))
  vrho_1_ = t59 + t91 + t6 * (t172 + t214)
  t236 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.2e1 / 0.9e1 * t33 * t34 * t40 * t50 - 0.2e1 / 0.9e1 * t118 * t119 * t121 * (t41 / t42 * t44 * t46 / 0.2e1 + t41 * t40 * t130 / 0.2e1)))
  vsigma_0_ = t6 * t236
  vsigma_1_ = 0.0e0
  t256 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t67 * (0.2e1 / 0.9e1 * t33 * t34 * t73 * t82 - 0.2e1 / 0.9e1 * t118 * t189 * t191 * (t41 / t74 * t76 * t78 / 0.2e1 + t41 * t73 * t200 / 0.2e1)))
  vsigma_2_ = t6 * t256
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

  b88_f = lambda x: 1 + params_beta / X_FACTOR_C * x ** 2 / (1 + params_gamma * params_beta * x * jnp.arcsinh(x))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, b88_f, rs, zeta, xs0, xs1)

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
  t20 = t3 ** 2
  t21 = params.beta * t20
  t23 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t23
  t25 = 4 ** (0.1e1 / 0.3e1)
  t27 = t21 * t24 * t25
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = s0 * t29
  t31 = r0 ** 2
  t32 = t18 ** 2
  t34 = 0.1e1 / t32 / t31
  t35 = params.gamma * params.beta
  t36 = jnp.sqrt(s0)
  t37 = t35 * t36
  t39 = 0.1e1 / t18 / r0
  t43 = jnp.arcsinh(t36 * t28 * t39)
  t44 = t28 * t39 * t43
  t46 = t37 * t44 + 0.1e1
  t47 = 0.1e1 / t46
  t48 = t34 * t47
  t52 = 0.1e1 + 0.2e1 / 0.9e1 * t27 * t30 * t48
  t56 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t52)
  t64 = 0.1e1 / t32 / t31 / r0
  t69 = t46 ** 2
  t71 = t34 / t69
  t81 = jnp.sqrt(t30 * t34 + 0.1e1)
  t82 = 0.1e1 / t81
  t96 = f.my_piecewise3(t2, 0, -t6 * t17 / t32 * t52 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.16e2 / 0.27e2 * t27 * t30 * t64 * t47 - 0.2e1 / 0.9e1 * t27 * t30 * t71 * (-0.4e1 / 0.3e1 * t37 * t28 / t18 / t31 * t43 - 0.4e1 / 0.3e1 * t35 * s0 * t29 * t64 * t82)))
  vrho_0_ = 0.2e1 * r0 * t96 + 0.2e1 * t56
  t119 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.2e1 / 0.9e1 * t21 * t24 * t25 * t29 * t48 - 0.2e1 / 0.9e1 * t27 * t30 * t71 * (t35 / t36 * t44 / 0.2e1 + t35 * t29 * t34 * t82 / 0.2e1)))
  vsigma_0_ = 0.2e1 * r0 * t119
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  r0 = r
  pol = pol_fxc(p, (r0/2, r0/2), (s/4 if s is not None else None, s/4 if s is not None else None, s/4 if s is not None else None), (None, None), (None, None))
  res = {}
  # Extract v2rho2 from polarized output
  v2rho2_pol = pol.get('v2rho2', None)
  if v2rho2_pol is not None:
    d11, d12, d22 = v2rho2_pol[..., 0], v2rho2_pol[..., 1], v2rho2_pol[..., 2]
    res['v2rho2'] = 0.25 * (d11 + 2*d12 + d22)
  # Extract v2rhosigma from polarized output
  v2rhosigma_pol = pol.get('v2rhosigma', None)
  if v2rhosigma_pol is not None:
    # Broadcast scalars to match array shape (Maple may emit some derivatives as scalar 0)
    d13 = jnp.asarray(v2rhosigma_pol[..., 0]) + jnp.zeros_like(r0)
    d14 = jnp.asarray(v2rhosigma_pol[..., 1]) + jnp.zeros_like(r0)
    d15 = jnp.asarray(v2rhosigma_pol[..., 2]) + jnp.zeros_like(r0)
    d23 = jnp.asarray(v2rhosigma_pol[..., 3]) + jnp.zeros_like(r0)
    d24 = jnp.asarray(v2rhosigma_pol[..., 4]) + jnp.zeros_like(r0)
    d25 = jnp.asarray(v2rhosigma_pol[..., 5]) + jnp.zeros_like(r0)
    res['v2rhosigma'] = (1/8) * (d13 + d14 + d15 + d23 + d24 + d25)
  # Extract v2sigma2 from polarized output
  v2sigma2_pol = pol.get('v2sigma2', None)
  if v2sigma2_pol is not None:
    # Broadcast scalars to match array shape
    d33 = jnp.asarray(v2sigma2_pol[..., 0]) + jnp.zeros_like(r0)
    d34 = jnp.asarray(v2sigma2_pol[..., 1]) + jnp.zeros_like(r0)
    d35 = jnp.asarray(v2sigma2_pol[..., 2]) + jnp.zeros_like(r0)
    d44 = jnp.asarray(v2sigma2_pol[..., 3]) + jnp.zeros_like(r0)
    d45 = jnp.asarray(v2sigma2_pol[..., 4]) + jnp.zeros_like(r0)
    d55 = jnp.asarray(v2sigma2_pol[..., 5]) + jnp.zeros_like(r0)
    res['v2sigma2'] = (1/16) * (d33 + 2*d34 + 2*d35 + d44 + 2*d45 + d55)
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
  t23 = t3 ** 2
  t24 = params.beta * t23
  t26 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t26 * t28
  t30 = t24 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t36 = 0.1e1 / t19 / t34
  t37 = params.gamma * params.beta
  t38 = jnp.sqrt(s0)
  t39 = t37 * t38
  t41 = 0.1e1 / t18 / r0
  t45 = jnp.asinh(t38 * t31 * t41)
  t48 = t39 * t31 * t41 * t45 + 0.1e1
  t49 = 0.1e1 / t48
  t54 = 0.1e1 + 0.2e1 / 0.9e1 * t30 * t33 * t36 * t49
  t59 = t17 / t19
  t60 = t34 * r0
  t62 = 0.1e1 / t19 / t60
  t67 = t48 ** 2
  t68 = 0.1e1 / t67
  t69 = t36 * t68
  t75 = t37 * s0
  t78 = t33 * t36 + 0.1e1
  t79 = jnp.sqrt(t78)
  t80 = 0.1e1 / t79
  t84 = -0.4e1 / 0.3e1 * t39 * t31 / t18 / t34 * t45 - 0.4e1 / 0.3e1 * t75 * t32 * t62 * t80
  t89 = -0.16e2 / 0.27e2 * t30 * t33 * t62 * t49 - 0.2e1 / 0.9e1 * t30 * t33 * t69 * t84
  t93 = t17 * t18
  t94 = t34 ** 2
  t96 = 0.1e1 / t19 / t94
  t101 = t62 * t68
  t107 = 0.1e1 / t67 / t48
  t109 = t84 ** 2
  t124 = s0 ** 2
  t125 = t37 * t124
  t131 = 0.1e1 / t79 / t78
  t135 = 0.28e2 / 0.9e1 * t39 * t31 / t18 / t60 * t45 + 0.20e2 / 0.3e1 * t75 * t32 * t96 * t80 - 0.32e2 / 0.9e1 * t125 * t31 / t18 / t94 / t60 * t131
  t140 = 0.176e3 / 0.81e2 * t30 * t33 * t96 * t49 + 0.32e2 / 0.27e2 * t30 * t33 * t101 * t84 + 0.4e1 / 0.9e1 * t30 * t33 * t36 * t107 * t109 - 0.2e1 / 0.9e1 * t30 * t33 * t69 * t135
  t145 = f.my_piecewise3(t2, 0, t6 * t22 * t54 / 0.12e2 - t6 * t59 * t89 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t93 * t140)
  t159 = 0.1e1 / t19 / t94 / r0
  t178 = t67 ** 2
  t204 = t94 ** 2
  t215 = t78 ** 2
  t231 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t36 * t54 + t6 * t22 * t89 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t59 * t140 - 0.3e1 / 0.8e1 * t6 * t93 * (-0.2464e4 / 0.243e3 * t30 * t33 * t159 * t49 - 0.176e3 / 0.27e2 * t30 * t33 * t96 * t68 * t84 - 0.32e2 / 0.9e1 * t30 * t33 * t62 * t107 * t109 + 0.16e2 / 0.9e1 * t30 * t33 * t101 * t135 - 0.4e1 / 0.3e1 * t30 * t33 * t36 / t178 * t109 * t84 + 0.4e1 / 0.3e1 * t24 * t29 * s0 * t32 * t36 * t107 * t84 * t135 - 0.2e1 / 0.9e1 * t30 * t33 * t69 * (-0.280e3 / 0.27e2 * t39 * t31 / t18 / t94 * t45 - 0.952e3 / 0.27e2 * t75 * t32 * t159 * t80 + 0.1184e4 / 0.27e2 * t125 * t31 / t18 / t204 * t131 - 0.256e3 / 0.9e1 * t37 * t124 * s0 / t204 / t60 / t79 / t215)))
  v3rho3_0_ = 0.2e1 * r0 * t231 + 0.6e1 * t145

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
  t24 = t3 ** 2
  t25 = params.beta * t24
  t27 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / t27 * t29
  t31 = t25 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = params.gamma * params.beta
  t36 = jnp.sqrt(s0)
  t37 = t35 * t36
  t39 = 0.1e1 / t19 / r0
  t43 = jnp.asinh(t36 * t32 * t39)
  t46 = t37 * t32 * t39 * t43 + 0.1e1
  t47 = 0.1e1 / t46
  t52 = 0.1e1 + 0.2e1 / 0.9e1 * t31 * t34 * t22 * t47
  t58 = t17 / t20 / r0
  t59 = t18 * r0
  t61 = 0.1e1 / t20 / t59
  t66 = t46 ** 2
  t67 = 0.1e1 / t66
  t68 = t22 * t67
  t74 = t35 * s0
  t75 = t33 * t61
  t77 = t34 * t22 + 0.1e1
  t78 = jnp.sqrt(t77)
  t79 = 0.1e1 / t78
  t83 = -0.4e1 / 0.3e1 * t37 * t32 / t19 / t18 * t43 - 0.4e1 / 0.3e1 * t74 * t75 * t79
  t88 = -0.16e2 / 0.27e2 * t31 * t34 * t61 * t47 - 0.2e1 / 0.9e1 * t31 * t34 * t68 * t83
  t93 = t17 / t20
  t94 = t18 ** 2
  t96 = 0.1e1 / t20 / t94
  t101 = t61 * t67
  t107 = 0.1e1 / t66 / t46
  t108 = t22 * t107
  t109 = t83 ** 2
  t124 = s0 ** 2
  t125 = t35 * t124
  t131 = 0.1e1 / t78 / t77
  t135 = 0.28e2 / 0.9e1 * t37 * t32 / t19 / t59 * t43 + 0.20e2 / 0.3e1 * t74 * t33 * t96 * t79 - 0.32e2 / 0.9e1 * t125 * t32 / t19 / t94 / t59 * t131
  t140 = 0.176e3 / 0.81e2 * t31 * t34 * t96 * t47 + 0.32e2 / 0.27e2 * t31 * t34 * t101 * t83 + 0.4e1 / 0.9e1 * t31 * t34 * t108 * t109 - 0.2e1 / 0.9e1 * t31 * t34 * t68 * t135
  t144 = t17 * t19
  t145 = t94 * r0
  t147 = 0.1e1 / t20 / t145
  t152 = t96 * t67
  t166 = t66 ** 2
  t167 = 0.1e1 / t166
  t169 = t109 * t83
  t175 = t25 * t30 * s0
  t176 = t33 * t22
  t177 = t107 * t83
  t178 = t177 * t135
  t192 = t94 ** 2
  t199 = t124 * s0
  t203 = t77 ** 2
  t205 = 0.1e1 / t78 / t203
  t209 = -0.280e3 / 0.27e2 * t37 * t32 / t19 / t94 * t43 - 0.952e3 / 0.27e2 * t74 * t33 * t147 * t79 + 0.1184e4 / 0.27e2 * t125 * t32 / t19 / t192 * t131 - 0.256e3 / 0.9e1 * t35 * t199 / t192 / t59 * t205
  t214 = -0.2464e4 / 0.243e3 * t31 * t34 * t147 * t47 - 0.176e3 / 0.27e2 * t31 * t34 * t152 * t83 - 0.32e2 / 0.9e1 * t31 * t34 * t61 * t107 * t109 + 0.16e2 / 0.9e1 * t31 * t34 * t101 * t135 - 0.4e1 / 0.3e1 * t31 * t34 * t22 * t167 * t169 + 0.4e1 / 0.3e1 * t175 * t176 * t178 - 0.2e1 / 0.9e1 * t31 * t34 * t68 * t209
  t219 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t52 + t6 * t58 * t88 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t93 * t140 - 0.3e1 / 0.8e1 * t6 * t144 * t214)
  t234 = t94 * t18
  t236 = 0.1e1 / t20 / t234
  t270 = t109 ** 2
  t280 = t135 ** 2
  t312 = t124 ** 2
  t329 = 0.41888e5 / 0.729e3 * t31 * t34 * t236 * t47 + 0.9856e4 / 0.243e3 * t31 * t34 * t147 * t67 * t83 + 0.704e3 / 0.27e2 * t31 * t34 * t96 * t107 * t109 - 0.352e3 / 0.27e2 * t31 * t34 * t152 * t135 + 0.128e3 / 0.9e1 * t31 * t34 * t61 * t167 * t169 - 0.128e3 / 0.9e1 * t175 * t75 * t178 + 0.64e2 / 0.27e2 * t31 * t34 * t101 * t209 + 0.16e2 / 0.3e1 * t31 * t34 * t22 / t166 / t46 * t270 - 0.8e1 * t175 * t176 * t167 * t109 * t135 + 0.4e1 / 0.3e1 * t31 * t34 * t108 * t280 + 0.16e2 / 0.9e1 * t175 * t176 * t177 * t209 - 0.2e1 / 0.9e1 * t31 * t34 * t68 * (0.3640e4 / 0.81e2 * t37 * t32 / t19 / t145 * t43 + 0.5768e4 / 0.27e2 * t74 * t33 * t236 * t79 - 0.37216e5 / 0.81e2 * t125 * t32 / t19 / t192 / r0 * t131 + 0.17920e5 / 0.27e2 * t35 * t199 / t192 / t94 * t205 - 0.5120e4 / 0.27e2 * t35 * t312 / t20 / t192 / t234 / t78 / t203 / t77 * t33)
  t334 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t61 * t52 - 0.5e1 / 0.9e1 * t6 * t23 * t88 + t6 * t58 * t140 / 0.2e1 - t6 * t93 * t214 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t144 * t329)
  v4rho4_0_ = 0.2e1 * r0 * t334 + 0.8e1 * t219

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
  t32 = t2 ** 2
  t33 = params.beta * t32
  t35 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t36 = 0.1e1 / t35
  t37 = t33 * t36
  t38 = 4 ** (0.1e1 / 0.3e1)
  t39 = t38 * s0
  t40 = r0 ** 2
  t41 = r0 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t44 = 0.1e1 / t42 / t40
  t45 = params.gamma * params.beta
  t46 = jnp.sqrt(s0)
  t49 = t46 / t41 / r0
  t50 = jnp.arcsinh(t49)
  t53 = t45 * t49 * t50 + 0.1e1
  t54 = 0.1e1 / t53
  t59 = 0.1e1 + 0.2e1 / 0.9e1 * t37 * t39 * t44 * t54
  t63 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t64 = t63 * f.p.zeta_threshold
  t66 = f.my_piecewise3(t20, t64, t21 * t19)
  t67 = t30 ** 2
  t68 = 0.1e1 / t67
  t69 = t66 * t68
  t72 = t5 * t69 * t59 / 0.8e1
  t73 = t66 * t30
  t74 = t40 * r0
  t76 = 0.1e1 / t42 / t74
  t82 = t33 * t36 * t38
  t83 = s0 * t44
  t84 = t53 ** 2
  t85 = 0.1e1 / t84
  t91 = s0 * t76
  t92 = 0.1e1 + t83
  t93 = jnp.sqrt(t92)
  t94 = 0.1e1 / t93
  t98 = -0.4e1 / 0.3e1 * t45 * t46 / t41 / t40 * t50 - 0.4e1 / 0.3e1 * t45 * t91 * t94
  t99 = t85 * t98
  t103 = -0.16e2 / 0.27e2 * t37 * t39 * t76 * t54 - 0.2e1 / 0.9e1 * t82 * t83 * t99
  t108 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t59 - t72 - 0.3e1 / 0.8e1 * t5 * t73 * t103)
  t110 = r1 <= f.p.dens_threshold
  t111 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t112 = 0.1e1 + t111
  t113 = t112 <= f.p.zeta_threshold
  t114 = t112 ** (0.1e1 / 0.3e1)
  t116 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t119 = f.my_piecewise3(t113, 0, 0.4e1 / 0.3e1 * t114 * t116)
  t120 = t119 * t30
  t121 = t38 * s2
  t122 = r1 ** 2
  t123 = r1 ** (0.1e1 / 0.3e1)
  t124 = t123 ** 2
  t126 = 0.1e1 / t124 / t122
  t127 = jnp.sqrt(s2)
  t130 = t127 / t123 / r1
  t131 = jnp.arcsinh(t130)
  t134 = t45 * t130 * t131 + 0.1e1
  t135 = 0.1e1 / t134
  t140 = 0.1e1 + 0.2e1 / 0.9e1 * t37 * t121 * t126 * t135
  t145 = f.my_piecewise3(t113, t64, t114 * t112)
  t146 = t145 * t68
  t149 = t5 * t146 * t140 / 0.8e1
  t151 = f.my_piecewise3(t110, 0, -0.3e1 / 0.8e1 * t5 * t120 * t140 - t149)
  t153 = t21 ** 2
  t154 = 0.1e1 / t153
  t155 = t26 ** 2
  t160 = t16 / t22 / t6
  t162 = -0.2e1 * t23 + 0.2e1 * t160
  t163 = f.my_piecewise5(t10, 0, t14, 0, t162)
  t167 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t154 * t155 + 0.4e1 / 0.3e1 * t21 * t163)
  t174 = t5 * t29 * t68 * t59
  t180 = 0.1e1 / t67 / t6
  t184 = t5 * t66 * t180 * t59 / 0.12e2
  t186 = t5 * t69 * t103
  t188 = t40 ** 2
  t190 = 0.1e1 / t42 / t188
  t200 = t98 ** 2
  t215 = s0 ** 2
  t235 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t167 * t30 * t59 - t174 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t103 + t184 - t186 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t73 * (0.176e3 / 0.81e2 * t37 * t39 * t190 * t54 + 0.32e2 / 0.27e2 * t82 * t91 * t99 + 0.4e1 / 0.9e1 * t82 * t83 / t84 / t53 * t200 - 0.2e1 / 0.9e1 * t82 * t83 * t85 * (0.28e2 / 0.9e1 * t45 * t46 / t41 / t74 * t50 + 0.20e2 / 0.3e1 * t45 * s0 * t190 * t94 - 0.16e2 / 0.9e1 * t45 * t215 / t41 / t188 / t74 / t93 / t92)))
  t236 = t114 ** 2
  t237 = 0.1e1 / t236
  t238 = t116 ** 2
  t242 = f.my_piecewise5(t14, 0, t10, 0, -t162)
  t246 = f.my_piecewise3(t113, 0, 0.4e1 / 0.9e1 * t237 * t238 + 0.4e1 / 0.3e1 * t114 * t242)
  t253 = t5 * t119 * t68 * t140
  t258 = t5 * t145 * t180 * t140 / 0.12e2
  t260 = f.my_piecewise3(t110, 0, -0.3e1 / 0.8e1 * t5 * t246 * t30 * t140 - t253 / 0.4e1 + t258)
  d11 = 0.2e1 * t108 + 0.2e1 * t151 + t6 * (t235 + t260)
  t263 = -t7 - t24
  t264 = f.my_piecewise5(t10, 0, t14, 0, t263)
  t267 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t264)
  t268 = t267 * t30
  t273 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t268 * t59 - t72)
  t275 = f.my_piecewise5(t14, 0, t10, 0, -t263)
  t278 = f.my_piecewise3(t113, 0, 0.4e1 / 0.3e1 * t114 * t275)
  t279 = t278 * t30
  t283 = t145 * t30
  t284 = t122 * r1
  t286 = 0.1e1 / t124 / t284
  t291 = s2 * t126
  t292 = t134 ** 2
  t293 = 0.1e1 / t292
  t299 = s2 * t286
  t300 = 0.1e1 + t291
  t301 = jnp.sqrt(t300)
  t302 = 0.1e1 / t301
  t306 = -0.4e1 / 0.3e1 * t45 * t127 / t123 / t122 * t131 - 0.4e1 / 0.3e1 * t45 * t299 * t302
  t307 = t293 * t306
  t311 = -0.16e2 / 0.27e2 * t37 * t121 * t286 * t135 - 0.2e1 / 0.9e1 * t82 * t291 * t307
  t316 = f.my_piecewise3(t110, 0, -0.3e1 / 0.8e1 * t5 * t279 * t140 - t149 - 0.3e1 / 0.8e1 * t5 * t283 * t311)
  t320 = 0.2e1 * t160
  t321 = f.my_piecewise5(t10, 0, t14, 0, t320)
  t325 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t154 * t264 * t26 + 0.4e1 / 0.3e1 * t21 * t321)
  t332 = t5 * t267 * t68 * t59
  t340 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t325 * t30 * t59 - t332 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t268 * t103 - t174 / 0.8e1 + t184 - t186 / 0.8e1)
  t344 = f.my_piecewise5(t14, 0, t10, 0, -t320)
  t348 = f.my_piecewise3(t113, 0, 0.4e1 / 0.9e1 * t237 * t275 * t116 + 0.4e1 / 0.3e1 * t114 * t344)
  t355 = t5 * t278 * t68 * t140
  t362 = t5 * t146 * t311
  t365 = f.my_piecewise3(t110, 0, -0.3e1 / 0.8e1 * t5 * t348 * t30 * t140 - t355 / 0.8e1 - t253 / 0.8e1 + t258 - 0.3e1 / 0.8e1 * t5 * t120 * t311 - t362 / 0.8e1)
  d12 = t108 + t151 + t273 + t316 + t6 * (t340 + t365)
  t370 = t264 ** 2
  t374 = 0.2e1 * t23 + 0.2e1 * t160
  t375 = f.my_piecewise5(t10, 0, t14, 0, t374)
  t379 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t154 * t370 + 0.4e1 / 0.3e1 * t21 * t375)
  t386 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t379 * t30 * t59 - t332 / 0.4e1 + t184)
  t387 = t275 ** 2
  t391 = f.my_piecewise5(t14, 0, t10, 0, -t374)
  t395 = f.my_piecewise3(t113, 0, 0.4e1 / 0.9e1 * t237 * t387 + 0.4e1 / 0.3e1 * t114 * t391)
  t405 = t122 ** 2
  t407 = 0.1e1 / t124 / t405
  t417 = t306 ** 2
  t432 = s2 ** 2
  t452 = f.my_piecewise3(t110, 0, -0.3e1 / 0.8e1 * t5 * t395 * t30 * t140 - t355 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t279 * t311 + t258 - t362 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t283 * (0.176e3 / 0.81e2 * t37 * t121 * t407 * t135 + 0.32e2 / 0.27e2 * t82 * t299 * t307 + 0.4e1 / 0.9e1 * t82 * t291 / t292 / t134 * t417 - 0.2e1 / 0.9e1 * t82 * t291 * t293 * (0.28e2 / 0.9e1 * t45 * t127 / t123 / t284 * t131 + 0.20e2 / 0.3e1 * t45 * s2 * t407 * t302 - 0.16e2 / 0.9e1 * t45 * t432 / t123 / t405 / t284 / t301 / t300)))
  d22 = 0.2e1 * t273 + 0.2e1 * t316 + t6 * (t386 + t452)
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
  t28 = t2 ** 2
  t29 = params.beta * t28
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = t29 * t32
  t34 = 4 ** (0.1e1 / 0.3e1)
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t40 = t34 * t39
  t41 = params.gamma * params.beta
  t42 = jnp.sqrt(s0)
  t44 = 0.1e1 / t36 / r0
  t45 = t42 * t44
  t46 = jnp.arcsinh(t45)
  t49 = t41 * t45 * t46 + 0.1e1
  t50 = 0.1e1 / t49
  t54 = t29 * t32 * t34
  t55 = s0 * t39
  t56 = t49 ** 2
  t57 = 0.1e1 / t56
  t58 = 0.1e1 / t42
  t62 = 0.1e1 + t55
  t63 = jnp.sqrt(t62)
  t64 = 0.1e1 / t63
  t68 = t41 * t58 * t44 * t46 / 0.2e1 + t41 * t39 * t64 / 0.2e1
  t69 = t57 * t68
  t73 = 0.2e1 / 0.9e1 * t33 * t40 * t50 - 0.2e1 / 0.9e1 * t54 * t55 * t69
  t77 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t73)
  t78 = t6 ** 2
  t81 = t7 - t16 / t78
  t82 = f.my_piecewise5(t10, 0, t14, 0, t81)
  t85 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t82)
  t90 = t26 ** 2
  t91 = 0.1e1 / t90
  t98 = 0.1e1 / t37 / t35 / r0
  t104 = 0.1e1 / t36 / t35
  t108 = s0 * t98
  t112 = -0.4e1 / 0.3e1 * t41 * t42 * t104 * t46 - 0.4e1 / 0.3e1 * t41 * t108 * t64
  t134 = t35 ** 2
  t154 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t85 * t26 * t73 - t5 * t25 * t91 * t73 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.16e2 / 0.27e2 * t33 * t34 * t98 * t50 - 0.2e1 / 0.9e1 * t33 * t40 * t57 * t112 + 0.16e2 / 0.27e2 * t54 * t108 * t69 + 0.4e1 / 0.9e1 * t54 * t55 / t56 / t49 * t68 * t112 - 0.2e1 / 0.9e1 * t54 * t55 * t57 * (-0.2e1 / 0.3e1 * t41 * t58 * t104 * t46 - 0.2e1 * t41 * t98 * t64 + 0.2e1 / 0.3e1 * t41 / t36 / t134 / t35 / t63 / t62 * s0)))
  d13 = t6 * t154 + t77
  d14 = 0.0e0
  t156 = r1 <= f.p.dens_threshold
  t157 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t158 = 0.1e1 + t157
  t159 = t158 <= f.p.zeta_threshold
  t160 = t158 ** (0.1e1 / 0.3e1)
  t162 = f.my_piecewise3(t159, t22, t160 * t158)
  t164 = r1 ** 2
  t165 = r1 ** (0.1e1 / 0.3e1)
  t166 = t165 ** 2
  t168 = 0.1e1 / t166 / t164
  t170 = jnp.sqrt(s2)
  t172 = 0.1e1 / t165 / r1
  t173 = t170 * t172
  t174 = jnp.arcsinh(t173)
  t177 = t41 * t173 * t174 + 0.1e1
  t181 = s2 * t168
  t182 = t177 ** 2
  t189 = jnp.sqrt(0.1e1 + t181)
  t199 = 0.2e1 / 0.9e1 * t33 * t34 * t168 / t177 - 0.2e1 / 0.9e1 * t54 * t181 / t182 * (t41 / t170 * t172 * t174 / 0.2e1 + t41 * t168 / t189 / 0.2e1)
  t203 = f.my_piecewise3(t156, 0, -0.3e1 / 0.8e1 * t5 * t162 * t26 * t199)
  t205 = f.my_piecewise5(t14, 0, t10, 0, -t81)
  t208 = f.my_piecewise3(t159, 0, 0.4e1 / 0.3e1 * t160 * t205)
  t218 = f.my_piecewise3(t156, 0, -0.3e1 / 0.8e1 * t5 * t208 * t26 * t199 - t5 * t162 * t91 * t199 / 0.8e1)
  d15 = t6 * t218 + t203
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
  t28 = t2 ** 2
  t29 = params.beta * t28
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = t29 * t32
  t34 = 4 ** (0.1e1 / 0.3e1)
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t41 = params.gamma * params.beta
  t42 = jnp.sqrt(s0)
  t44 = 0.1e1 / t36 / r0
  t45 = t42 * t44
  t46 = jnp.arcsinh(t45)
  t49 = t41 * t45 * t46 + 0.1e1
  t54 = t29 * t32 * t34
  t55 = s0 * t39
  t56 = t49 ** 2
  t63 = jnp.sqrt(0.1e1 + t55)
  t73 = 0.2e1 / 0.9e1 * t33 * t34 * t39 / t49 - 0.2e1 / 0.9e1 * t54 * t55 / t56 * (t41 / t42 * t44 * t46 / 0.2e1 + t41 * t39 / t63 / 0.2e1)
  t77 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t73)
  t78 = t6 ** 2
  t81 = -t7 - t16 / t78
  t82 = f.my_piecewise5(t10, 0, t14, 0, t81)
  t85 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t82)
  t90 = t26 ** 2
  t91 = 0.1e1 / t90
  t97 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t85 * t26 * t73 - t5 * t25 * t91 * t73 / 0.8e1)
  d23 = t6 * t97 + t77
  d24 = 0.0e0
  t99 = r1 <= f.p.dens_threshold
  t100 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t101 = 0.1e1 + t100
  t102 = t101 <= f.p.zeta_threshold
  t103 = t101 ** (0.1e1 / 0.3e1)
  t105 = f.my_piecewise3(t102, t22, t103 * t101)
  t106 = t105 * t26
  t107 = r1 ** 2
  t108 = r1 ** (0.1e1 / 0.3e1)
  t109 = t108 ** 2
  t111 = 0.1e1 / t109 / t107
  t112 = t34 * t111
  t113 = jnp.sqrt(s2)
  t115 = 0.1e1 / t108 / r1
  t116 = t113 * t115
  t117 = jnp.arcsinh(t116)
  t120 = t41 * t116 * t117 + 0.1e1
  t121 = 0.1e1 / t120
  t124 = s2 * t111
  t125 = t120 ** 2
  t126 = 0.1e1 / t125
  t127 = 0.1e1 / t113
  t131 = 0.1e1 + t124
  t132 = jnp.sqrt(t131)
  t133 = 0.1e1 / t132
  t137 = t41 * t127 * t115 * t117 / 0.2e1 + t41 * t111 * t133 / 0.2e1
  t138 = t126 * t137
  t142 = 0.2e1 / 0.9e1 * t33 * t112 * t121 - 0.2e1 / 0.9e1 * t54 * t124 * t138
  t146 = f.my_piecewise3(t99, 0, -0.3e1 / 0.8e1 * t5 * t106 * t142)
  t148 = f.my_piecewise5(t14, 0, t10, 0, -t81)
  t151 = f.my_piecewise3(t102, 0, 0.4e1 / 0.3e1 * t103 * t148)
  t162 = 0.1e1 / t109 / t107 / r1
  t168 = 0.1e1 / t108 / t107
  t172 = s2 * t162
  t176 = -0.4e1 / 0.3e1 * t41 * t113 * t168 * t117 - 0.4e1 / 0.3e1 * t41 * t172 * t133
  t198 = t107 ** 2
  t218 = f.my_piecewise3(t99, 0, -0.3e1 / 0.8e1 * t5 * t151 * t26 * t142 - t5 * t105 * t91 * t142 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t106 * (-0.16e2 / 0.27e2 * t33 * t34 * t162 * t121 - 0.2e1 / 0.9e1 * t33 * t112 * t126 * t176 + 0.16e2 / 0.27e2 * t54 * t172 * t138 + 0.4e1 / 0.9e1 * t54 * t124 / t125 / t120 * t137 * t176 - 0.2e1 / 0.9e1 * t54 * t124 * t126 * (-0.2e1 / 0.3e1 * t41 * t127 * t168 * t117 - 0.2e1 * t41 * t162 * t133 + 0.2e1 / 0.3e1 * t41 / t108 / t198 / t107 / t132 / t131 * s2)))
  d25 = t6 * t218 + t146
  t1 = r0 + r1
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 / t1
  t11 = f.p.zeta_threshold - 0.1e1
  t18 = f.my_piecewise5(0.2e1 * r0 * t7 <= f.p.zeta_threshold, t11, 0.2e1 * r1 * t7 <= f.p.zeta_threshold, -t11, (r0 - r1) * t7)
  t19 = 0.1e1 + t18
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t19 <= f.p.zeta_threshold, t21 * f.p.zeta_threshold, t23 * t19)
  t26 = t1 ** (0.1e1 / 0.3e1)
  t28 = t3 ** 2
  t29 = params.beta * t28
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t34 = 4 ** (0.1e1 / 0.3e1)
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t41 = params.gamma * params.beta
  t42 = jnp.sqrt(s0)
  t44 = 0.1e1 / t36 / r0
  t45 = t42 * t44
  t46 = jnp.arcsinh(t45)
  t49 = t41 * t45 * t46 + 0.1e1
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t56 = s0 * t39
  t57 = 0.1e1 + t56
  t58 = jnp.sqrt(t57)
  t59 = 0.1e1 / t58
  t63 = t41 / t42 * t44 * t46 / 0.2e1 + t41 * t39 * t59 / 0.2e1
  t69 = t29 * t32 * t34
  t72 = t63 ** 2
  t86 = t35 ** 2
  t104 = f.my_piecewise3(r0 <= f.p.dens_threshold, 0, -0.3e1 / 0.8e1 * t3 / t4 * t25 * t26 * (-0.4e1 / 0.9e1 * t29 * t32 * t34 * t39 * t51 * t63 + 0.4e1 / 0.9e1 * t69 * t56 / t50 / t49 * t72 - 0.2e1 / 0.9e1 * t69 * t56 * t51 * (-t41 / t42 / s0 * t44 * t46 / 0.4e1 + t41 / s0 * t39 * t59 / 0.4e1 - t41 / t36 / t86 / r0 / t58 / t57 / 0.4e1)))
  d33 = t1 * t104
  d34 = 0.0e0
  d35 = 0.0e0
  d44 = 0.0e0
  d45 = 0.0e0
  t1 = r0 + r1
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 / t1
  t11 = f.p.zeta_threshold - 0.1e1
  t18 = f.my_piecewise5(0.2e1 * r1 * t7 <= f.p.zeta_threshold, t11, 0.2e1 * r0 * t7 <= f.p.zeta_threshold, -t11, -(r0 - r1) * t7)
  t19 = 0.1e1 + t18
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t19 <= f.p.zeta_threshold, t21 * f.p.zeta_threshold, t23 * t19)
  t26 = t1 ** (0.1e1 / 0.3e1)
  t28 = t3 ** 2
  t29 = params.beta * t28
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t34 = 4 ** (0.1e1 / 0.3e1)
  t35 = r1 ** 2
  t36 = r1 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t41 = params.gamma * params.beta
  t42 = jnp.sqrt(s2)
  t44 = 0.1e1 / t36 / r1
  t45 = t42 * t44
  t46 = jnp.arcsinh(t45)
  t49 = t41 * t45 * t46 + 0.1e1
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t56 = s2 * t39
  t57 = 0.1e1 + t56
  t58 = jnp.sqrt(t57)
  t59 = 0.1e1 / t58
  t63 = t41 / t42 * t44 * t46 / 0.2e1 + t41 * t39 * t59 / 0.2e1
  t69 = t29 * t32 * t34
  t72 = t63 ** 2
  t86 = t35 ** 2
  t104 = f.my_piecewise3(r1 <= f.p.dens_threshold, 0, -0.3e1 / 0.8e1 * t3 / t4 * t25 * t26 * (-0.4e1 / 0.9e1 * t29 * t32 * t34 * t39 * t51 * t63 + 0.4e1 / 0.9e1 * t69 * t56 / t50 / t49 * t72 - 0.2e1 / 0.9e1 * t69 * t56 * t51 * (-t41 / t42 / s2 * t44 * t46 / 0.4e1 + t41 / s2 * t39 * t59 / 0.4e1 - t41 / t36 / t86 / r1 / t58 / t57 / 0.4e1)))
  d55 = t1 * t104
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
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
  t44 = t2 ** 2
  t45 = params.beta * t44
  t47 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t48 = 0.1e1 / t47
  t49 = t45 * t48
  t50 = 4 ** (0.1e1 / 0.3e1)
  t51 = t50 * s0
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / t52
  t57 = params.gamma * params.beta
  t58 = jnp.sqrt(s0)
  t61 = t58 / t53 / r0
  t62 = jnp.asinh(t61)
  t65 = t57 * t61 * t62 + 0.1e1
  t66 = 0.1e1 / t65
  t71 = 0.1e1 + 0.2e1 / 0.9e1 * t49 * t51 * t56 * t66
  t77 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t78 = t42 ** 2
  t79 = 0.1e1 / t78
  t80 = t77 * t79
  t84 = t77 * t42
  t85 = t52 * r0
  t87 = 0.1e1 / t54 / t85
  t93 = t45 * t48 * t50
  t94 = s0 * t56
  t95 = t65 ** 2
  t96 = 0.1e1 / t95
  t102 = s0 * t87
  t103 = 0.1e1 + t94
  t104 = jnp.sqrt(t103)
  t105 = 0.1e1 / t104
  t109 = -0.4e1 / 0.3e1 * t57 * t58 / t53 / t52 * t62 - 0.4e1 / 0.3e1 * t57 * t102 * t105
  t110 = t96 * t109
  t114 = -0.16e2 / 0.27e2 * t49 * t51 * t87 * t66 - 0.2e1 / 0.9e1 * t93 * t94 * t110
  t118 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t119 = t118 * f.p.zeta_threshold
  t121 = f.my_piecewise3(t20, t119, t21 * t19)
  t123 = 0.1e1 / t78 / t6
  t124 = t121 * t123
  t128 = t121 * t79
  t132 = t121 * t42
  t133 = t52 ** 2
  t135 = 0.1e1 / t54 / t133
  t144 = 0.1e1 / t95 / t65
  t145 = t109 ** 2
  t146 = t144 * t145
  t156 = s0 * t135
  t160 = s0 ** 2
  t166 = 0.1e1 / t104 / t103
  t170 = 0.28e2 / 0.9e1 * t57 * t58 / t53 / t85 * t62 + 0.20e2 / 0.3e1 * t57 * t156 * t105 - 0.16e2 / 0.9e1 * t57 * t160 / t53 / t133 / t85 * t166
  t171 = t96 * t170
  t175 = 0.176e3 / 0.81e2 * t49 * t51 * t135 * t66 + 0.32e2 / 0.27e2 * t93 * t102 * t110 + 0.4e1 / 0.9e1 * t93 * t94 * t146 - 0.2e1 / 0.9e1 * t93 * t94 * t171
  t180 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t71 - t5 * t80 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t84 * t114 + t5 * t124 * t71 / 0.12e2 - t5 * t128 * t114 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t132 * t175)
  t182 = r1 <= f.p.dens_threshold
  t183 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t184 = 0.1e1 + t183
  t185 = t184 <= f.p.zeta_threshold
  t186 = t184 ** (0.1e1 / 0.3e1)
  t187 = t186 ** 2
  t188 = 0.1e1 / t187
  t190 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t191 = t190 ** 2
  t195 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t199 = f.my_piecewise3(t185, 0, 0.4e1 / 0.9e1 * t188 * t191 + 0.4e1 / 0.3e1 * t186 * t195)
  t202 = r1 ** 2
  t203 = r1 ** (0.1e1 / 0.3e1)
  t204 = t203 ** 2
  t207 = jnp.sqrt(s2)
  t210 = t207 / t203 / r1
  t211 = jnp.asinh(t210)
  t220 = 0.1e1 + 0.2e1 / 0.9e1 * t49 * t50 * s2 / t204 / t202 / (t57 * t210 * t211 + 0.1e1)
  t226 = f.my_piecewise3(t185, 0, 0.4e1 / 0.3e1 * t186 * t190)
  t232 = f.my_piecewise3(t185, t119, t186 * t184)
  t238 = f.my_piecewise3(t182, 0, -0.3e1 / 0.8e1 * t5 * t199 * t42 * t220 - t5 * t226 * t79 * t220 / 0.4e1 + t5 * t232 * t123 * t220 / 0.12e2)
  t248 = t24 ** 2
  t252 = 0.6e1 * t33 - 0.6e1 * t16 / t248
  t253 = f.my_piecewise5(t10, 0, t14, 0, t252)
  t257 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t253)
  t280 = 0.1e1 / t78 / t24
  t293 = 0.1e1 / t54 / t133 / r0
  t307 = t95 ** 2
  t329 = t133 ** 2
  t340 = t103 ** 2
  t356 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t257 * t42 * t71 - 0.3e1 / 0.8e1 * t5 * t41 * t79 * t71 - 0.9e1 / 0.8e1 * t5 * t43 * t114 + t5 * t77 * t123 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t80 * t114 - 0.9e1 / 0.8e1 * t5 * t84 * t175 - 0.5e1 / 0.36e2 * t5 * t121 * t280 * t71 + t5 * t124 * t114 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t128 * t175 - 0.3e1 / 0.8e1 * t5 * t132 * (-0.2464e4 / 0.243e3 * t49 * t51 * t293 * t66 - 0.176e3 / 0.27e2 * t93 * t156 * t110 - 0.32e2 / 0.9e1 * t93 * t102 * t146 + 0.16e2 / 0.9e1 * t93 * t102 * t171 - 0.4e1 / 0.3e1 * t93 * t94 / t307 * t145 * t109 + 0.4e1 / 0.3e1 * t93 * t94 * t144 * t109 * t170 - 0.2e1 / 0.9e1 * t93 * t94 * t96 * (-0.280e3 / 0.27e2 * t57 * t58 / t53 / t133 * t62 - 0.952e3 / 0.27e2 * t57 * s0 * t293 * t105 + 0.592e3 / 0.27e2 * t57 * t160 / t53 / t329 * t166 - 0.64e2 / 0.9e1 * t57 * t160 * s0 / t329 / t85 / t104 / t340)))
  t366 = f.my_piecewise5(t14, 0, t10, 0, -t252)
  t370 = f.my_piecewise3(t185, 0, -0.8e1 / 0.27e2 / t187 / t184 * t191 * t190 + 0.4e1 / 0.3e1 * t188 * t190 * t195 + 0.4e1 / 0.3e1 * t186 * t366)
  t388 = f.my_piecewise3(t182, 0, -0.3e1 / 0.8e1 * t5 * t370 * t42 * t220 - 0.3e1 / 0.8e1 * t5 * t199 * t79 * t220 + t5 * t226 * t123 * t220 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t232 * t280 * t220)
  d111 = 0.3e1 * t180 + 0.3e1 * t238 + t6 * (t356 + t388)

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
  t56 = t2 ** 2
  t57 = params.beta * t56
  t59 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t60 = 0.1e1 / t59
  t61 = t57 * t60
  t62 = 4 ** (0.1e1 / 0.3e1)
  t63 = t62 * s0
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t69 = params.gamma * params.beta
  t70 = jnp.sqrt(s0)
  t73 = t70 / t65 / r0
  t74 = jnp.asinh(t73)
  t77 = t69 * t73 * t74 + 0.1e1
  t78 = 0.1e1 / t77
  t83 = 0.1e1 + 0.2e1 / 0.9e1 * t61 * t63 * t68 * t78
  t92 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t93 = t54 ** 2
  t94 = 0.1e1 / t93
  t95 = t92 * t94
  t99 = t92 * t54
  t100 = t64 * r0
  t102 = 0.1e1 / t66 / t100
  t108 = t57 * t60 * t62
  t109 = s0 * t68
  t110 = t77 ** 2
  t111 = 0.1e1 / t110
  t117 = s0 * t102
  t118 = 0.1e1 + t109
  t119 = jnp.sqrt(t118)
  t120 = 0.1e1 / t119
  t124 = -0.4e1 / 0.3e1 * t69 * t70 / t65 / t64 * t74 - 0.4e1 / 0.3e1 * t69 * t117 * t120
  t125 = t111 * t124
  t129 = -0.16e2 / 0.27e2 * t61 * t63 * t102 * t78 - 0.2e1 / 0.9e1 * t108 * t109 * t125
  t135 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t137 = 0.1e1 / t93 / t6
  t138 = t135 * t137
  t142 = t135 * t94
  t146 = t135 * t54
  t147 = t64 ** 2
  t149 = 0.1e1 / t66 / t147
  t158 = 0.1e1 / t110 / t77
  t159 = t124 ** 2
  t160 = t158 * t159
  t170 = s0 * t149
  t174 = s0 ** 2
  t180 = 0.1e1 / t119 / t118
  t184 = 0.28e2 / 0.9e1 * t69 * t70 / t65 / t100 * t74 + 0.20e2 / 0.3e1 * t69 * t170 * t120 - 0.16e2 / 0.9e1 * t69 * t174 / t65 / t147 / t100 * t180
  t185 = t111 * t184
  t189 = 0.176e3 / 0.81e2 * t61 * t63 * t149 * t78 + 0.32e2 / 0.27e2 * t108 * t117 * t125 + 0.4e1 / 0.9e1 * t108 * t109 * t160 - 0.2e1 / 0.9e1 * t108 * t109 * t185
  t193 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t194 = t193 * f.p.zeta_threshold
  t196 = f.my_piecewise3(t20, t194, t21 * t19)
  t198 = 0.1e1 / t93 / t25
  t199 = t196 * t198
  t203 = t196 * t137
  t207 = t196 * t94
  t211 = t196 * t54
  t212 = t147 * r0
  t214 = 0.1e1 / t66 / t212
  t228 = t110 ** 2
  t229 = 0.1e1 / t228
  t231 = t229 * t159 * t124
  t235 = t158 * t124
  t236 = t235 * t184
  t246 = s0 * t214
  t250 = t147 ** 2
  t257 = t174 * s0
  t261 = t118 ** 2
  t263 = 0.1e1 / t119 / t261
  t267 = -0.280e3 / 0.27e2 * t69 * t70 / t65 / t147 * t74 - 0.952e3 / 0.27e2 * t69 * t246 * t120 + 0.592e3 / 0.27e2 * t69 * t174 / t65 / t250 * t180 - 0.64e2 / 0.9e1 * t69 * t257 / t250 / t100 * t263
  t268 = t111 * t267
  t272 = -0.2464e4 / 0.243e3 * t61 * t63 * t214 * t78 - 0.176e3 / 0.27e2 * t108 * t170 * t125 - 0.32e2 / 0.9e1 * t108 * t117 * t160 + 0.16e2 / 0.9e1 * t108 * t117 * t185 - 0.4e1 / 0.3e1 * t108 * t109 * t231 + 0.4e1 / 0.3e1 * t108 * t109 * t236 - 0.2e1 / 0.9e1 * t108 * t109 * t268
  t277 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t83 - 0.3e1 / 0.8e1 * t5 * t95 * t83 - 0.9e1 / 0.8e1 * t5 * t99 * t129 + t5 * t138 * t83 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t142 * t129 - 0.9e1 / 0.8e1 * t5 * t146 * t189 - 0.5e1 / 0.36e2 * t5 * t199 * t83 + t5 * t203 * t129 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t207 * t189 - 0.3e1 / 0.8e1 * t5 * t211 * t272)
  t279 = r1 <= f.p.dens_threshold
  t280 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t281 = 0.1e1 + t280
  t282 = t281 <= f.p.zeta_threshold
  t283 = t281 ** (0.1e1 / 0.3e1)
  t284 = t283 ** 2
  t286 = 0.1e1 / t284 / t281
  t288 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t289 = t288 ** 2
  t293 = 0.1e1 / t284
  t294 = t293 * t288
  t296 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t300 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t304 = f.my_piecewise3(t282, 0, -0.8e1 / 0.27e2 * t286 * t289 * t288 + 0.4e1 / 0.3e1 * t294 * t296 + 0.4e1 / 0.3e1 * t283 * t300)
  t307 = r1 ** 2
  t308 = r1 ** (0.1e1 / 0.3e1)
  t309 = t308 ** 2
  t312 = jnp.sqrt(s2)
  t315 = t312 / t308 / r1
  t316 = jnp.asinh(t315)
  t325 = 0.1e1 + 0.2e1 / 0.9e1 * t61 * t62 * s2 / t309 / t307 / (t69 * t315 * t316 + 0.1e1)
  t334 = f.my_piecewise3(t282, 0, 0.4e1 / 0.9e1 * t293 * t289 + 0.4e1 / 0.3e1 * t283 * t296)
  t341 = f.my_piecewise3(t282, 0, 0.4e1 / 0.3e1 * t283 * t288)
  t347 = f.my_piecewise3(t282, t194, t283 * t281)
  t353 = f.my_piecewise3(t279, 0, -0.3e1 / 0.8e1 * t5 * t304 * t54 * t325 - 0.3e1 / 0.8e1 * t5 * t334 * t94 * t325 + t5 * t341 * t137 * t325 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t347 * t198 * t325)
  t378 = t147 * t64
  t380 = 0.1e1 / t66 / t378
  t405 = t159 ** 2
  t415 = t184 ** 2
  t447 = t174 ** 2
  t463 = 0.41888e5 / 0.729e3 * t61 * t63 * t380 * t78 + 0.9856e4 / 0.243e3 * t108 * t246 * t125 + 0.704e3 / 0.27e2 * t108 * t170 * t160 - 0.352e3 / 0.27e2 * t108 * t170 * t185 + 0.128e3 / 0.9e1 * t108 * t117 * t231 - 0.128e3 / 0.9e1 * t108 * t117 * t236 + 0.64e2 / 0.27e2 * t108 * t117 * t268 + 0.16e2 / 0.3e1 * t108 * t109 / t228 / t77 * t405 - 0.8e1 * t108 * t109 * t229 * t159 * t184 + 0.4e1 / 0.3e1 * t108 * t109 * t158 * t415 + 0.16e2 / 0.9e1 * t108 * t109 * t235 * t267 - 0.2e1 / 0.9e1 * t108 * t109 * t111 * (0.3640e4 / 0.81e2 * t69 * t70 / t65 / t212 * t74 + 0.5768e4 / 0.27e2 * t69 * s0 * t380 * t120 - 0.18608e5 / 0.81e2 * t69 * t174 / t65 / t250 / r0 * t180 + 0.4480e4 / 0.27e2 * t69 * t257 / t250 / t147 * t263 - 0.1280e4 / 0.27e2 * t69 * t447 / t66 / t250 / t378 / t119 / t261 / t118)
  t467 = t19 ** 2
  t470 = t30 ** 2
  t476 = t41 ** 2
  t485 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t486 = f.my_piecewise5(t10, 0, t14, 0, t485)
  t490 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t467 * t470 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t476 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t486)
  t511 = 0.1e1 / t93 / t36
  t516 = -0.3e1 / 0.2e1 * t5 * t95 * t129 - 0.9e1 / 0.4e1 * t5 * t99 * t189 + t5 * t138 * t129 - 0.3e1 / 0.2e1 * t5 * t142 * t189 - 0.3e1 / 0.2e1 * t5 * t146 * t272 - 0.5e1 / 0.9e1 * t5 * t199 * t129 + t5 * t203 * t189 / 0.2e1 - t5 * t207 * t272 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t211 * t463 - 0.3e1 / 0.8e1 * t5 * t490 * t54 * t83 - 0.3e1 / 0.2e1 * t5 * t55 * t129 - t5 * t53 * t94 * t83 / 0.2e1 + t5 * t92 * t137 * t83 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t135 * t198 * t83 + 0.10e2 / 0.27e2 * t5 * t196 * t511 * t83
  t517 = f.my_piecewise3(t1, 0, t516)
  t518 = t281 ** 2
  t521 = t289 ** 2
  t527 = t296 ** 2
  t533 = f.my_piecewise5(t14, 0, t10, 0, -t485)
  t537 = f.my_piecewise3(t282, 0, 0.40e2 / 0.81e2 / t284 / t518 * t521 - 0.16e2 / 0.9e1 * t286 * t289 * t296 + 0.4e1 / 0.3e1 * t293 * t527 + 0.16e2 / 0.9e1 * t294 * t300 + 0.4e1 / 0.3e1 * t283 * t533)
  t559 = f.my_piecewise3(t279, 0, -0.3e1 / 0.8e1 * t5 * t537 * t54 * t325 - t5 * t304 * t94 * t325 / 0.2e1 + t5 * t334 * t137 * t325 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t341 * t198 * t325 + 0.10e2 / 0.27e2 * t5 * t347 * t511 * t325)
  d1111 = 0.4e1 * t277 + 0.4e1 * t353 + t6 * (t517 + t559)

  res = {'v4rho4': d1111}
  return res