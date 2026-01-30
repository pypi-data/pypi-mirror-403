"""Generated from gga_x_bkl.mpl."""

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
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu1_raw = params.mu1
  if isinstance(params_mu1_raw, (str, bytes, dict)):
    params_mu1 = params_mu1_raw
  else:
    try:
      params_mu1_seq = list(params_mu1_raw)
    except TypeError:
      params_mu1 = params_mu1_raw
    else:
      params_mu1_seq = np.asarray(params_mu1_seq, dtype=np.float64)
      params_mu1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu1_seq))

  bkl_f0 = lambda s: 1 + params_gamma * params_kappa * (jnp.exp(-params_alpha * params_mu1 * s ** 2) - jnp.exp(-params_beta * params_mu1 * s ** 2))

  bkl_f = lambda x: bkl_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, bkl_f, rs, z, xs0, xs1)

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
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu1_raw = params.mu1
  if isinstance(params_mu1_raw, (str, bytes, dict)):
    params_mu1 = params_mu1_raw
  else:
    try:
      params_mu1_seq = list(params_mu1_raw)
    except TypeError:
      params_mu1 = params_mu1_raw
    else:
      params_mu1_seq = np.asarray(params_mu1_seq, dtype=np.float64)
      params_mu1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu1_seq))

  bkl_f0 = lambda s: 1 + params_gamma * params_kappa * (jnp.exp(-params_alpha * params_mu1 * s ** 2) - jnp.exp(-params_beta * params_mu1 * s ** 2))

  bkl_f = lambda x: bkl_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, bkl_f, rs, z, xs0, xs1)

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
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu1_raw = params.mu1
  if isinstance(params_mu1_raw, (str, bytes, dict)):
    params_mu1 = params_mu1_raw
  else:
    try:
      params_mu1_seq = list(params_mu1_raw)
    except TypeError:
      params_mu1 = params_mu1_raw
    else:
      params_mu1_seq = np.asarray(params_mu1_seq, dtype=np.float64)
      params_mu1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu1_seq))

  bkl_f0 = lambda s: 1 + params_gamma * params_kappa * (jnp.exp(-params_alpha * params_mu1 * s ** 2) - jnp.exp(-params_beta * params_mu1 * s ** 2))

  bkl_f = lambda x: bkl_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, bkl_f, rs, z, xs0, xs1)

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
  t28 = params.gamma * params.kappa
  t30 = 6 ** (0.1e1 / 0.3e1)
  t31 = params.alpha * params.mu1 * t30
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = 0.1e1 / t34
  t36 = t35 * s0
  t37 = r0 ** 2
  t38 = r0 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t41 = 0.1e1 / t39 / t37
  t42 = t36 * t41
  t45 = jnp.exp(-t31 * t42 / 0.24e2)
  t47 = params.beta * params.mu1 * t30
  t50 = jnp.exp(-t47 * t42 / 0.24e2)
  t53 = 0.1e1 + t28 * (t45 - t50)
  t57 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t53)
  t58 = r1 <= f.p.dens_threshold
  t59 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t60 = 0.1e1 + t59
  t61 = t60 <= f.p.zeta_threshold
  t62 = t60 ** (0.1e1 / 0.3e1)
  t64 = f.my_piecewise3(t61, t22, t62 * t60)
  t66 = t35 * s2
  t67 = r1 ** 2
  t68 = r1 ** (0.1e1 / 0.3e1)
  t69 = t68 ** 2
  t71 = 0.1e1 / t69 / t67
  t72 = t66 * t71
  t75 = jnp.exp(-t31 * t72 / 0.24e2)
  t78 = jnp.exp(-t47 * t72 / 0.24e2)
  t81 = 0.1e1 + t28 * (t75 - t78)
  t85 = f.my_piecewise3(t58, 0, -0.3e1 / 0.8e1 * t5 * t64 * t26 * t81)
  t86 = t6 ** 2
  t88 = t16 / t86
  t89 = t7 - t88
  t90 = f.my_piecewise5(t10, 0, t14, 0, t89)
  t93 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t90)
  t98 = t26 ** 2
  t99 = 0.1e1 / t98
  t103 = t5 * t25 * t99 * t53 / 0.8e1
  t104 = t5 * t25
  t105 = t26 * params.gamma
  t108 = 0.1e1 / t39 / t37 / r0
  t122 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t93 * t26 * t53 - t103 - 0.3e1 / 0.8e1 * t104 * t105 * params.kappa * (t31 * t36 * t108 * t45 / 0.9e1 - t47 * t36 * t108 * t50 / 0.9e1))
  t124 = f.my_piecewise5(t14, 0, t10, 0, -t89)
  t127 = f.my_piecewise3(t61, 0, 0.4e1 / 0.3e1 * t62 * t124)
  t135 = t5 * t64 * t99 * t81 / 0.8e1
  t137 = f.my_piecewise3(t58, 0, -0.3e1 / 0.8e1 * t5 * t127 * t26 * t81 - t135)
  vrho_0_ = t57 + t85 + t6 * (t122 + t137)
  t140 = -t7 - t88
  t141 = f.my_piecewise5(t10, 0, t14, 0, t140)
  t144 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t141)
  t150 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t144 * t26 * t53 - t103)
  t152 = f.my_piecewise5(t14, 0, t10, 0, -t140)
  t155 = f.my_piecewise3(t61, 0, 0.4e1 / 0.3e1 * t62 * t152)
  t160 = t5 * t64
  t163 = 0.1e1 / t69 / t67 / r1
  t177 = f.my_piecewise3(t58, 0, -0.3e1 / 0.8e1 * t5 * t155 * t26 * t81 - t135 - 0.3e1 / 0.8e1 * t160 * t105 * params.kappa * (t31 * t66 * t163 * t75 / 0.9e1 - t47 * t66 * t163 * t78 / 0.9e1))
  vrho_1_ = t57 + t85 + t6 * (t150 + t177)
  t180 = t35 * t41
  t191 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t104 * t105 * params.kappa * (-t31 * t180 * t45 / 0.24e2 + t47 * t180 * t50 / 0.24e2))
  vsigma_0_ = t6 * t191
  vsigma_1_ = 0.0e0
  t192 = t35 * t71
  t203 = f.my_piecewise3(t58, 0, -0.3e1 / 0.8e1 * t160 * t105 * params.kappa * (-t31 * t192 * t75 / 0.24e2 + t47 * t192 * t78 / 0.24e2))
  vsigma_2_ = t6 * t203
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
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu1_raw = params.mu1
  if isinstance(params_mu1_raw, (str, bytes, dict)):
    params_mu1 = params_mu1_raw
  else:
    try:
      params_mu1_seq = list(params_mu1_raw)
    except TypeError:
      params_mu1 = params_mu1_raw
    else:
      params_mu1_seq = np.asarray(params_mu1_seq, dtype=np.float64)
      params_mu1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu1_seq))

  bkl_f0 = lambda s: 1 + params_gamma * params_kappa * (jnp.exp(-params_alpha * params_mu1 * s ** 2) - jnp.exp(-params_beta * params_mu1 * s ** 2))

  bkl_f = lambda x: bkl_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, bkl_f, rs, z, xs0, xs1)

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
  t21 = params.alpha * params.mu1
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = t21 * t22
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = r0 ** 2
  t32 = t18 ** 2
  t34 = 0.1e1 / t32 / t31
  t36 = t27 * s0 * t30 * t34
  t39 = jnp.exp(-t23 * t36 / 0.24e2)
  t40 = params.beta * params.mu1
  t41 = t40 * t22
  t44 = jnp.exp(-t41 * t36 / 0.24e2)
  t47 = 0.1e1 + params.gamma * params.kappa * (t39 - t44)
  t51 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t47)
  t57 = t6 * t17
  t58 = t18 * params.gamma
  t59 = t22 * t27
  t61 = s0 * t30
  t64 = 0.1e1 / t32 / t31 / r0
  t79 = f.my_piecewise3(t2, 0, -t6 * t17 / t32 * t47 / 0.8e1 - 0.3e1 / 0.8e1 * t57 * t58 * params.kappa * (t21 * t59 * t61 * t64 * t39 / 0.9e1 - t40 * t59 * t61 * t64 * t44 / 0.9e1))
  vrho_0_ = 0.2e1 * r0 * t79 + 0.2e1 * t51
  t82 = t27 * t30
  t95 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t57 * t58 * params.kappa * (-t23 * t82 * t34 * t39 / 0.24e2 + t41 * t82 * t34 * t44 / 0.24e2))
  vsigma_0_ = 0.2e1 * r0 * t95
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
  t20 = 0.1e1 / t19
  t23 = params.alpha * params.mu1
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = t23 * t24
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t37 = t29 * s0 * t32 * t35
  t40 = jnp.exp(-t25 * t37 / 0.24e2)
  t41 = params.beta * params.mu1
  t42 = t41 * t24
  t45 = jnp.exp(-t42 * t37 / 0.24e2)
  t48 = 0.1e1 + params.gamma * params.kappa * (t40 - t45)
  t52 = t6 * t17
  t53 = t18 * params.gamma
  t54 = t24 * t29
  t55 = t23 * t54
  t56 = s0 * t32
  t57 = t33 * r0
  t59 = 0.1e1 / t19 / t57
  t60 = t59 * t40
  t63 = t41 * t54
  t64 = t59 * t45
  t69 = params.kappa * (t55 * t56 * t60 / 0.9e1 - t63 * t56 * t64 / 0.9e1)
  t74 = f.my_piecewise3(t2, 0, -t6 * t17 * t20 * t48 / 0.8e1 - 0.3e1 / 0.8e1 * t52 * t53 * t69)
  t82 = t20 * params.gamma
  t86 = t33 ** 2
  t88 = 0.1e1 / t19 / t86
  t93 = params.alpha ** 2
  t94 = params.mu1 ** 2
  t95 = t93 * t94
  t96 = t24 ** 2
  t98 = 0.1e1 / t27 / t26
  t99 = t96 * t98
  t100 = t95 * t99
  t101 = s0 ** 2
  t102 = t101 * t31
  t105 = 0.1e1 / t18 / t86 / t57
  t114 = params.beta ** 2
  t115 = t114 * t94
  t116 = t115 * t99
  t127 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t48 / 0.12e2 - t52 * t82 * t69 / 0.4e1 - 0.3e1 / 0.8e1 * t52 * t53 * params.kappa * (-0.11e2 / 0.27e2 * t55 * t56 * t88 * t40 + 0.2e1 / 0.81e2 * t100 * t102 * t105 * t40 + 0.11e2 / 0.27e2 * t63 * t56 * t88 * t45 - 0.2e1 / 0.81e2 * t116 * t102 * t105 * t45))
  v2rho2_0_ = 0.2e1 * r0 * t127 + 0.4e1 * t74
  t130 = t29 * t32
  t139 = params.kappa * (-t25 * t130 * t35 * t40 / 0.24e2 + t42 * t130 * t35 * t45 / 0.24e2)
  t143 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t52 * t53 * t139)
  t153 = t31 / t18 / t86 / t33
  t171 = f.my_piecewise3(t2, 0, -t52 * t82 * t139 / 0.8e1 - 0.3e1 / 0.8e1 * t52 * t53 * params.kappa * (t25 * t130 * t60 / 0.9e1 - t100 * t153 * s0 * t40 / 0.108e3 - t42 * t130 * t64 / 0.9e1 + t116 * t153 * s0 * t45 / 0.108e3))
  v2rhosigma_0_ = 0.2e1 * r0 * t171 + 0.2e1 * t143
  t175 = t98 * t31
  t178 = 0.1e1 / t18 / t86 / r0
  t192 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t52 * t53 * params.kappa * (-t115 * t96 * t175 * t178 * t45 / 0.288e3 + t95 * t96 * t175 * t178 * t40 / 0.288e3))
  v2sigma2_0_ = 0.2e1 * r0 * t192
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
  t21 = 0.1e1 / t19 / r0
  t24 = params.alpha * params.mu1
  t25 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = r0 ** 2
  t36 = 0.1e1 / t19 / t34
  t38 = t30 * s0 * t33 * t36
  t41 = jnp.exp(-t24 * t25 * t38 / 0.24e2)
  t42 = params.beta * params.mu1
  t46 = jnp.exp(-t42 * t25 * t38 / 0.24e2)
  t49 = 0.1e1 + params.gamma * params.kappa * (t41 - t46)
  t53 = t6 * t17
  t55 = 0.1e1 / t19 * params.gamma
  t56 = t25 * t30
  t57 = t24 * t56
  t58 = s0 * t33
  t59 = t34 * r0
  t61 = 0.1e1 / t19 / t59
  t65 = t42 * t56
  t71 = params.kappa * (t57 * t58 * t61 * t41 / 0.9e1 - t65 * t58 * t61 * t46 / 0.9e1)
  t75 = t18 * params.gamma
  t76 = t34 ** 2
  t78 = 0.1e1 / t19 / t76
  t83 = params.alpha ** 2
  t84 = params.mu1 ** 2
  t86 = t25 ** 2
  t89 = t86 / t28 / t27
  t90 = t83 * t84 * t89
  t91 = s0 ** 2
  t92 = t91 * t32
  t95 = 0.1e1 / t18 / t76 / t59
  t104 = params.beta ** 2
  t106 = t104 * t84 * t89
  t112 = params.kappa * (-0.11e2 / 0.27e2 * t57 * t58 * t78 * t41 + 0.2e1 / 0.81e2 * t90 * t92 * t95 * t41 + 0.11e2 / 0.27e2 * t65 * t58 * t78 * t46 - 0.2e1 / 0.81e2 * t106 * t92 * t95 * t46)
  t117 = f.my_piecewise3(t2, 0, t6 * t17 * t21 * t49 / 0.12e2 - t53 * t55 * t71 / 0.4e1 - 0.3e1 / 0.8e1 * t53 * t75 * t112)
  t132 = 0.1e1 / t19 / t76 / r0
  t137 = t76 ** 2
  t139 = 0.1e1 / t18 / t137
  t145 = t84 * params.mu1
  t147 = t27 ** 2
  t148 = 0.1e1 / t147
  t153 = t91 * s0 / t137 / t59
  t177 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t36 * t49 + t53 * t21 * params.gamma * t71 / 0.4e1 - 0.3e1 / 0.8e1 * t53 * t55 * t112 - 0.3e1 / 0.8e1 * t53 * t75 * params.kappa * (0.154e3 / 0.81e2 * t57 * t58 * t132 * t41 - 0.22e2 / 0.81e2 * t90 * t92 * t139 * t41 + 0.8e1 / 0.243e3 * t83 * params.alpha * t145 * t148 * t153 * t41 - 0.154e3 / 0.81e2 * t65 * t58 * t132 * t46 + 0.22e2 / 0.81e2 * t106 * t92 * t139 * t46 - 0.8e1 / 0.243e3 * t104 * params.beta * t145 * t148 * t153 * t46))
  v3rho3_0_ = 0.2e1 * r0 * t177 + 0.6e1 * t117

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
  t25 = params.alpha * params.mu1
  t26 = 6 ** (0.1e1 / 0.3e1)
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = 0.1e1 / t30
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t36 = t31 * s0 * t34 * t22
  t39 = jnp.exp(-t25 * t26 * t36 / 0.24e2)
  t40 = params.beta * params.mu1
  t44 = jnp.exp(-t40 * t26 * t36 / 0.24e2)
  t47 = 0.1e1 + params.gamma * params.kappa * (t39 - t44)
  t51 = t6 * t17
  t54 = 0.1e1 / t20 / r0 * params.gamma
  t55 = t26 * t31
  t56 = t25 * t55
  t57 = s0 * t34
  t58 = t18 * r0
  t60 = 0.1e1 / t20 / t58
  t64 = t40 * t55
  t70 = params.kappa * (t56 * t57 * t60 * t39 / 0.9e1 - t64 * t57 * t60 * t44 / 0.9e1)
  t75 = 0.1e1 / t20 * params.gamma
  t76 = t18 ** 2
  t78 = 0.1e1 / t20 / t76
  t83 = params.alpha ** 2
  t84 = params.mu1 ** 2
  t86 = t26 ** 2
  t89 = t86 / t29 / t28
  t90 = t83 * t84 * t89
  t91 = s0 ** 2
  t92 = t91 * t33
  t95 = 0.1e1 / t19 / t76 / t58
  t104 = params.beta ** 2
  t106 = t104 * t84 * t89
  t112 = params.kappa * (-0.11e2 / 0.27e2 * t56 * t57 * t78 * t39 + 0.2e1 / 0.81e2 * t90 * t92 * t95 * t39 + 0.11e2 / 0.27e2 * t64 * t57 * t78 * t44 - 0.2e1 / 0.81e2 * t106 * t92 * t95 * t44)
  t116 = t19 * params.gamma
  t119 = 0.1e1 / t20 / t76 / r0
  t124 = t76 ** 2
  t126 = 0.1e1 / t19 / t124
  t132 = t84 * params.mu1
  t134 = t28 ** 2
  t135 = 0.1e1 / t134
  t136 = t83 * params.alpha * t132 * t135
  t137 = t91 * s0
  t140 = t137 / t124 / t58
  t154 = t104 * params.beta * t132 * t135
  t159 = params.kappa * (0.154e3 / 0.81e2 * t56 * t57 * t119 * t39 - 0.22e2 / 0.81e2 * t90 * t92 * t126 * t39 + 0.8e1 / 0.243e3 * t136 * t140 * t39 - 0.154e3 / 0.81e2 * t64 * t57 * t119 * t44 + 0.22e2 / 0.81e2 * t106 * t92 * t126 * t44 - 0.8e1 / 0.243e3 * t154 * t140 * t44)
  t164 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t47 + t51 * t54 * t70 / 0.4e1 - 0.3e1 / 0.8e1 * t51 * t75 * t112 - 0.3e1 / 0.8e1 * t51 * t116 * t159)
  t180 = t76 * t18
  t182 = 0.1e1 / t20 / t180
  t189 = 0.1e1 / t19 / t124 / r0
  t196 = t137 / t124 / t76
  t200 = t83 ** 2
  t201 = t84 ** 2
  t203 = t91 ** 2
  t204 = t135 * t203
  t209 = 0.1e1 / t20 / t124 / t180 * t26
  t210 = t31 * t34
  t226 = t104 ** 2
  t239 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t60 * t47 - 0.5e1 / 0.9e1 * t51 * t22 * params.gamma * t70 + t51 * t54 * t112 / 0.2e1 - t51 * t75 * t159 / 0.2e1 - 0.3e1 / 0.8e1 * t51 * t116 * params.kappa * (-0.2618e4 / 0.243e3 * t56 * t57 * t182 * t39 + 0.1958e4 / 0.729e3 * t90 * t92 * t189 * t39 - 0.176e3 / 0.243e3 * t136 * t196 * t39 + 0.8e1 / 0.2187e4 * t200 * t201 * t204 * t209 * t210 * t39 + 0.2618e4 / 0.243e3 * t64 * t57 * t182 * t44 - 0.1958e4 / 0.729e3 * t106 * t92 * t189 * t44 + 0.176e3 / 0.243e3 * t154 * t196 * t44 - 0.8e1 / 0.2187e4 * t226 * t201 * t204 * t209 * t210 * t44))
  v4rho4_0_ = 0.2e1 * r0 * t239 + 0.8e1 * t164

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
  t32 = params.gamma * params.kappa
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = params.alpha * params.mu1 * t34
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t40 = t39 * s0
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t46 = t40 / t43 / t41
  t49 = jnp.exp(-t35 * t46 / 0.24e2)
  t51 = params.beta * params.mu1 * t34
  t54 = jnp.exp(-t51 * t46 / 0.24e2)
  t57 = 0.1e1 + t32 * (t49 - t54)
  t61 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t62 = t61 * f.p.zeta_threshold
  t64 = f.my_piecewise3(t20, t62, t21 * t19)
  t65 = t30 ** 2
  t66 = 0.1e1 / t65
  t70 = t5 * t64 * t66 * t57 / 0.8e1
  t71 = t5 * t64
  t72 = t30 * params.gamma
  t73 = t41 * r0
  t75 = 0.1e1 / t43 / t73
  t84 = params.kappa * (t35 * t40 * t75 * t49 / 0.9e1 - t51 * t40 * t75 * t54 / 0.9e1)
  t85 = t72 * t84
  t89 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t57 - t70 - 0.3e1 / 0.8e1 * t71 * t85)
  t91 = r1 <= f.p.dens_threshold
  t92 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t93 = 0.1e1 + t92
  t94 = t93 <= f.p.zeta_threshold
  t95 = t93 ** (0.1e1 / 0.3e1)
  t97 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t100 = f.my_piecewise3(t94, 0, 0.4e1 / 0.3e1 * t95 * t97)
  t102 = t39 * s2
  t103 = r1 ** 2
  t104 = r1 ** (0.1e1 / 0.3e1)
  t105 = t104 ** 2
  t108 = t102 / t105 / t103
  t111 = jnp.exp(-t35 * t108 / 0.24e2)
  t114 = jnp.exp(-t51 * t108 / 0.24e2)
  t117 = 0.1e1 + t32 * (t111 - t114)
  t122 = f.my_piecewise3(t94, t62, t95 * t93)
  t126 = t5 * t122 * t66 * t117 / 0.8e1
  t128 = f.my_piecewise3(t91, 0, -0.3e1 / 0.8e1 * t5 * t100 * t30 * t117 - t126)
  t130 = t21 ** 2
  t131 = 0.1e1 / t130
  t132 = t26 ** 2
  t137 = t16 / t22 / t6
  t139 = -0.2e1 * t23 + 0.2e1 * t137
  t140 = f.my_piecewise5(t10, 0, t14, 0, t139)
  t144 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t131 * t132 + 0.4e1 / 0.3e1 * t21 * t140)
  t151 = t5 * t29 * t66 * t57
  t157 = 0.1e1 / t65 / t6
  t161 = t5 * t64 * t157 * t57 / 0.12e2
  t162 = t66 * params.gamma
  t164 = t71 * t162 * t84
  t166 = t41 ** 2
  t168 = 0.1e1 / t43 / t166
  t173 = params.alpha ** 2
  t174 = params.mu1 ** 2
  t176 = t34 ** 2
  t177 = t173 * t174 * t176
  t179 = 0.1e1 / t37 / t36
  t180 = s0 ** 2
  t181 = t179 * t180
  t184 = 0.1e1 / t42 / t166 / t73
  t193 = params.beta ** 2
  t195 = t193 * t174 * t176
  t206 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t144 * t30 * t57 - t151 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t29 * t85 + t161 - t164 / 0.4e1 - 0.3e1 / 0.8e1 * t71 * t72 * params.kappa * (-0.11e2 / 0.27e2 * t35 * t40 * t168 * t49 + t177 * t181 * t184 * t49 / 0.81e2 + 0.11e2 / 0.27e2 * t51 * t40 * t168 * t54 - t195 * t181 * t184 * t54 / 0.81e2))
  t207 = t95 ** 2
  t208 = 0.1e1 / t207
  t209 = t97 ** 2
  t213 = f.my_piecewise5(t14, 0, t10, 0, -t139)
  t217 = f.my_piecewise3(t94, 0, 0.4e1 / 0.9e1 * t208 * t209 + 0.4e1 / 0.3e1 * t95 * t213)
  t224 = t5 * t100 * t66 * t117
  t229 = t5 * t122 * t157 * t117 / 0.12e2
  t231 = f.my_piecewise3(t91, 0, -0.3e1 / 0.8e1 * t5 * t217 * t30 * t117 - t224 / 0.4e1 + t229)
  d11 = 0.2e1 * t89 + 0.2e1 * t128 + t6 * (t206 + t231)
  t234 = -t7 - t24
  t235 = f.my_piecewise5(t10, 0, t14, 0, t234)
  t238 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t235)
  t244 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t238 * t30 * t57 - t70)
  t246 = f.my_piecewise5(t14, 0, t10, 0, -t234)
  t249 = f.my_piecewise3(t94, 0, 0.4e1 / 0.3e1 * t95 * t246)
  t254 = t5 * t122
  t255 = t103 * r1
  t257 = 0.1e1 / t105 / t255
  t266 = params.kappa * (t35 * t102 * t257 * t111 / 0.9e1 - t51 * t102 * t257 * t114 / 0.9e1)
  t267 = t72 * t266
  t271 = f.my_piecewise3(t91, 0, -0.3e1 / 0.8e1 * t5 * t249 * t30 * t117 - t126 - 0.3e1 / 0.8e1 * t254 * t267)
  t275 = 0.2e1 * t137
  t276 = f.my_piecewise5(t10, 0, t14, 0, t275)
  t280 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t131 * t235 * t26 + 0.4e1 / 0.3e1 * t21 * t276)
  t287 = t5 * t238 * t66 * t57
  t295 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t280 * t30 * t57 - t287 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t238 * t85 - t151 / 0.8e1 + t161 - t164 / 0.8e1)
  t299 = f.my_piecewise5(t14, 0, t10, 0, -t275)
  t303 = f.my_piecewise3(t94, 0, 0.4e1 / 0.9e1 * t208 * t246 * t97 + 0.4e1 / 0.3e1 * t95 * t299)
  t310 = t5 * t249 * t66 * t117
  t317 = t254 * t162 * t266
  t320 = f.my_piecewise3(t91, 0, -0.3e1 / 0.8e1 * t5 * t303 * t30 * t117 - t310 / 0.8e1 - t224 / 0.8e1 + t229 - 0.3e1 / 0.8e1 * t5 * t100 * t267 - t317 / 0.8e1)
  d12 = t89 + t128 + t244 + t271 + t6 * (t295 + t320)
  t325 = t235 ** 2
  t329 = 0.2e1 * t23 + 0.2e1 * t137
  t330 = f.my_piecewise5(t10, 0, t14, 0, t329)
  t334 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t131 * t325 + 0.4e1 / 0.3e1 * t21 * t330)
  t341 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t334 * t30 * t57 - t287 / 0.4e1 + t161)
  t342 = t246 ** 2
  t346 = f.my_piecewise5(t14, 0, t10, 0, -t329)
  t350 = f.my_piecewise3(t94, 0, 0.4e1 / 0.9e1 * t208 * t342 + 0.4e1 / 0.3e1 * t95 * t346)
  t360 = t103 ** 2
  t362 = 0.1e1 / t105 / t360
  t367 = s2 ** 2
  t368 = t179 * t367
  t371 = 0.1e1 / t104 / t360 / t255
  t390 = f.my_piecewise3(t91, 0, -0.3e1 / 0.8e1 * t5 * t350 * t30 * t117 - t310 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t249 * t267 + t229 - t317 / 0.4e1 - 0.3e1 / 0.8e1 * t254 * t72 * params.kappa * (-0.11e2 / 0.27e2 * t35 * t102 * t362 * t111 + t177 * t368 * t371 * t111 / 0.81e2 + 0.11e2 / 0.27e2 * t51 * t102 * t362 * t114 - t195 * t368 * t371 * t114 / 0.81e2))
  d22 = 0.2e1 * t244 + 0.2e1 * t271 + t6 * (t341 + t390)
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
  t44 = params.gamma * params.kappa
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = params.alpha * params.mu1 * t46
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t52 = t51 * s0
  t53 = r0 ** 2
  t54 = r0 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t58 = t52 / t55 / t53
  t61 = jnp.exp(-t47 * t58 / 0.24e2)
  t63 = params.beta * params.mu1 * t46
  t66 = jnp.exp(-t63 * t58 / 0.24e2)
  t69 = 0.1e1 + t44 * (t61 - t66)
  t75 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t76 = t42 ** 2
  t77 = 0.1e1 / t76
  t82 = t5 * t75
  t83 = t42 * params.gamma
  t84 = t53 * r0
  t86 = 0.1e1 / t55 / t84
  t95 = params.kappa * (t47 * t52 * t86 * t61 / 0.9e1 - t63 * t52 * t86 * t66 / 0.9e1)
  t96 = t83 * t95
  t99 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t100 = t99 * f.p.zeta_threshold
  t102 = f.my_piecewise3(t20, t100, t21 * t19)
  t104 = 0.1e1 / t76 / t6
  t109 = t5 * t102
  t110 = t77 * params.gamma
  t111 = t110 * t95
  t114 = t53 ** 2
  t116 = 0.1e1 / t55 / t114
  t121 = params.alpha ** 2
  t122 = params.mu1 ** 2
  t124 = t46 ** 2
  t125 = t121 * t122 * t124
  t128 = s0 ** 2
  t129 = 0.1e1 / t49 / t48 * t128
  t132 = 0.1e1 / t54 / t114 / t84
  t141 = params.beta ** 2
  t143 = t141 * t122 * t124
  t149 = params.kappa * (-0.11e2 / 0.27e2 * t47 * t52 * t116 * t61 + t125 * t129 * t132 * t61 / 0.81e2 + 0.11e2 / 0.27e2 * t63 * t52 * t116 * t66 - t143 * t129 * t132 * t66 / 0.81e2)
  t150 = t83 * t149
  t154 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t69 - t5 * t75 * t77 * t69 / 0.4e1 - 0.3e1 / 0.4e1 * t82 * t96 + t5 * t102 * t104 * t69 / 0.12e2 - t109 * t111 / 0.4e1 - 0.3e1 / 0.8e1 * t109 * t150)
  t156 = r1 <= f.p.dens_threshold
  t157 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t158 = 0.1e1 + t157
  t159 = t158 <= f.p.zeta_threshold
  t160 = t158 ** (0.1e1 / 0.3e1)
  t161 = t160 ** 2
  t162 = 0.1e1 / t161
  t164 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t165 = t164 ** 2
  t169 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t173 = f.my_piecewise3(t159, 0, 0.4e1 / 0.9e1 * t162 * t165 + 0.4e1 / 0.3e1 * t160 * t169)
  t176 = r1 ** 2
  t177 = r1 ** (0.1e1 / 0.3e1)
  t178 = t177 ** 2
  t181 = t51 * s2 / t178 / t176
  t184 = jnp.exp(-t47 * t181 / 0.24e2)
  t187 = jnp.exp(-t63 * t181 / 0.24e2)
  t190 = 0.1e1 + t44 * (t184 - t187)
  t196 = f.my_piecewise3(t159, 0, 0.4e1 / 0.3e1 * t160 * t164)
  t202 = f.my_piecewise3(t159, t100, t160 * t158)
  t208 = f.my_piecewise3(t156, 0, -0.3e1 / 0.8e1 * t5 * t173 * t42 * t190 - t5 * t196 * t77 * t190 / 0.4e1 + t5 * t202 * t104 * t190 / 0.12e2)
  t218 = t24 ** 2
  t222 = 0.6e1 * t33 - 0.6e1 * t16 / t218
  t223 = f.my_piecewise5(t10, 0, t14, 0, t222)
  t227 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t223)
  t248 = 0.1e1 / t76 / t24
  t262 = 0.1e1 / t55 / t114 / r0
  t267 = t114 ** 2
  t269 = 0.1e1 / t54 / t267
  t275 = t122 * params.mu1
  t277 = t48 ** 2
  t278 = 0.1e1 / t277
  t283 = t128 * s0 / t267 / t84
  t307 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t227 * t42 * t69 - 0.3e1 / 0.8e1 * t5 * t41 * t77 * t69 - 0.9e1 / 0.8e1 * t5 * t41 * t96 + t5 * t75 * t104 * t69 / 0.4e1 - 0.3e1 / 0.4e1 * t82 * t111 - 0.9e1 / 0.8e1 * t82 * t150 - 0.5e1 / 0.36e2 * t5 * t102 * t248 * t69 + t109 * t104 * params.gamma * t95 / 0.4e1 - 0.3e1 / 0.8e1 * t109 * t110 * t149 - 0.3e1 / 0.8e1 * t109 * t83 * params.kappa * (0.154e3 / 0.81e2 * t47 * t52 * t262 * t61 - 0.11e2 / 0.81e2 * t125 * t129 * t269 * t61 + 0.2e1 / 0.243e3 * t121 * params.alpha * t275 * t278 * t283 * t61 - 0.154e3 / 0.81e2 * t63 * t52 * t262 * t66 + 0.11e2 / 0.81e2 * t143 * t129 * t269 * t66 - 0.2e1 / 0.243e3 * t141 * params.beta * t275 * t278 * t283 * t66))
  t317 = f.my_piecewise5(t14, 0, t10, 0, -t222)
  t321 = f.my_piecewise3(t159, 0, -0.8e1 / 0.27e2 / t161 / t158 * t165 * t164 + 0.4e1 / 0.3e1 * t162 * t164 * t169 + 0.4e1 / 0.3e1 * t160 * t317)
  t339 = f.my_piecewise3(t156, 0, -0.3e1 / 0.8e1 * t5 * t321 * t42 * t190 - 0.3e1 / 0.8e1 * t5 * t173 * t77 * t190 + t5 * t196 * t104 * t190 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t202 * t248 * t190)
  d111 = 0.3e1 * t154 + 0.3e1 * t208 + t6 * (t307 + t339)

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
  t56 = params.gamma * params.kappa
  t58 = 6 ** (0.1e1 / 0.3e1)
  t59 = params.alpha * params.mu1 * t58
  t60 = jnp.pi ** 2
  t61 = t60 ** (0.1e1 / 0.3e1)
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t64 = t63 * s0
  t65 = r0 ** 2
  t66 = r0 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t70 = t64 / t67 / t65
  t73 = jnp.exp(-t59 * t70 / 0.24e2)
  t75 = params.beta * params.mu1 * t58
  t78 = jnp.exp(-t75 * t70 / 0.24e2)
  t81 = 0.1e1 + t56 * (t73 - t78)
  t90 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t91 = t54 ** 2
  t92 = 0.1e1 / t91
  t97 = t5 * t90
  t98 = t54 * params.gamma
  t99 = t65 * r0
  t101 = 0.1e1 / t67 / t99
  t110 = params.kappa * (t59 * t64 * t101 * t73 / 0.9e1 - t75 * t64 * t101 * t78 / 0.9e1)
  t111 = t98 * t110
  t116 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t118 = 0.1e1 / t91 / t6
  t123 = t5 * t116
  t124 = t92 * params.gamma
  t125 = t124 * t110
  t128 = t65 ** 2
  t130 = 0.1e1 / t67 / t128
  t135 = params.alpha ** 2
  t136 = params.mu1 ** 2
  t138 = t58 ** 2
  t139 = t135 * t136 * t138
  t142 = s0 ** 2
  t143 = 0.1e1 / t61 / t60 * t142
  t146 = 0.1e1 / t66 / t128 / t99
  t155 = params.beta ** 2
  t157 = t155 * t136 * t138
  t163 = params.kappa * (-0.11e2 / 0.27e2 * t59 * t64 * t130 * t73 + t139 * t143 * t146 * t73 / 0.81e2 + 0.11e2 / 0.27e2 * t75 * t64 * t130 * t78 - t157 * t143 * t146 * t78 / 0.81e2)
  t164 = t98 * t163
  t167 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t168 = t167 * f.p.zeta_threshold
  t170 = f.my_piecewise3(t20, t168, t21 * t19)
  t172 = 0.1e1 / t91 / t25
  t177 = t5 * t170
  t178 = t118 * params.gamma
  t179 = t178 * t110
  t182 = t124 * t163
  t187 = 0.1e1 / t67 / t128 / r0
  t192 = t128 ** 2
  t194 = 0.1e1 / t66 / t192
  t200 = t136 * params.mu1
  t202 = t60 ** 2
  t203 = 0.1e1 / t202
  t204 = t135 * params.alpha * t200 * t203
  t205 = t142 * s0
  t208 = t205 / t192 / t99
  t222 = t155 * params.beta * t200 * t203
  t227 = params.kappa * (0.154e3 / 0.81e2 * t59 * t64 * t187 * t73 - 0.11e2 / 0.81e2 * t139 * t143 * t194 * t73 + 0.2e1 / 0.243e3 * t204 * t208 * t73 - 0.154e3 / 0.81e2 * t75 * t64 * t187 * t78 + 0.11e2 / 0.81e2 * t157 * t143 * t194 * t78 - 0.2e1 / 0.243e3 * t222 * t208 * t78)
  t228 = t98 * t227
  t232 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t53 * t54 * t81 - 0.3e1 / 0.8e1 * t5 * t90 * t92 * t81 - 0.9e1 / 0.8e1 * t97 * t111 + t5 * t116 * t118 * t81 / 0.4e1 - 0.3e1 / 0.4e1 * t123 * t125 - 0.9e1 / 0.8e1 * t123 * t164 - 0.5e1 / 0.36e2 * t5 * t170 * t172 * t81 + t177 * t179 / 0.4e1 - 0.3e1 / 0.8e1 * t177 * t182 - 0.3e1 / 0.8e1 * t177 * t228)
  t234 = r1 <= f.p.dens_threshold
  t235 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t236 = 0.1e1 + t235
  t237 = t236 <= f.p.zeta_threshold
  t238 = t236 ** (0.1e1 / 0.3e1)
  t239 = t238 ** 2
  t241 = 0.1e1 / t239 / t236
  t243 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t244 = t243 ** 2
  t248 = 0.1e1 / t239
  t249 = t248 * t243
  t251 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t255 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t259 = f.my_piecewise3(t237, 0, -0.8e1 / 0.27e2 * t241 * t244 * t243 + 0.4e1 / 0.3e1 * t249 * t251 + 0.4e1 / 0.3e1 * t238 * t255)
  t262 = r1 ** 2
  t263 = r1 ** (0.1e1 / 0.3e1)
  t264 = t263 ** 2
  t267 = t63 * s2 / t264 / t262
  t270 = jnp.exp(-t59 * t267 / 0.24e2)
  t273 = jnp.exp(-t75 * t267 / 0.24e2)
  t276 = 0.1e1 + t56 * (t270 - t273)
  t285 = f.my_piecewise3(t237, 0, 0.4e1 / 0.9e1 * t248 * t244 + 0.4e1 / 0.3e1 * t238 * t251)
  t292 = f.my_piecewise3(t237, 0, 0.4e1 / 0.3e1 * t238 * t243)
  t298 = f.my_piecewise3(t237, t168, t238 * t236)
  t304 = f.my_piecewise3(t234, 0, -0.3e1 / 0.8e1 * t5 * t259 * t54 * t276 - 0.3e1 / 0.8e1 * t5 * t285 * t92 * t276 + t5 * t292 * t118 * t276 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t298 * t172 * t276)
  t306 = t19 ** 2
  t309 = t30 ** 2
  t315 = t41 ** 2
  t324 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t325 = f.my_piecewise5(t10, 0, t14, 0, t324)
  t329 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t306 * t309 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t315 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t325)
  t334 = t128 * t65
  t336 = 0.1e1 / t67 / t334
  t343 = 0.1e1 / t66 / t192 / r0
  t350 = t205 / t192 / t128
  t354 = t135 ** 2
  t355 = t136 ** 2
  t357 = t142 ** 2
  t358 = t203 * t357
  t363 = 0.1e1 / t67 / t192 / t334 * t58
  t379 = t155 ** 2
  t426 = 0.1e1 / t91 / t36
  t431 = -0.3e1 / 0.8e1 * t5 * t329 * t54 * t81 - 0.3e1 / 0.8e1 * t177 * t98 * params.kappa * (-0.2618e4 / 0.243e3 * t59 * t64 * t336 * t73 + 0.979e3 / 0.729e3 * t139 * t143 * t343 * t73 - 0.44e2 / 0.243e3 * t204 * t350 * t73 + 0.2e1 / 0.2187e4 * t354 * t355 * t358 * t363 * t63 * t73 + 0.2618e4 / 0.243e3 * t75 * t64 * t336 * t78 - 0.979e3 / 0.729e3 * t157 * t143 * t343 * t78 + 0.44e2 / 0.243e3 * t222 * t350 * t78 - 0.2e1 / 0.2187e4 * t379 * t355 * t358 * t363 * t63 * t78) - 0.3e1 / 0.2e1 * t5 * t53 * t111 - 0.3e1 / 0.2e1 * t97 * t125 - 0.9e1 / 0.4e1 * t97 * t164 + t123 * t179 - 0.3e1 / 0.2e1 * t123 * t182 - 0.3e1 / 0.2e1 * t123 * t228 - 0.5e1 / 0.9e1 * t177 * t172 * params.gamma * t110 + t177 * t178 * t163 / 0.2e1 - t177 * t124 * t227 / 0.2e1 - t5 * t53 * t92 * t81 / 0.2e1 + t5 * t90 * t118 * t81 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t116 * t172 * t81 + 0.10e2 / 0.27e2 * t5 * t170 * t426 * t81
  t432 = f.my_piecewise3(t1, 0, t431)
  t433 = t236 ** 2
  t436 = t244 ** 2
  t442 = t251 ** 2
  t448 = f.my_piecewise5(t14, 0, t10, 0, -t324)
  t452 = f.my_piecewise3(t237, 0, 0.40e2 / 0.81e2 / t239 / t433 * t436 - 0.16e2 / 0.9e1 * t241 * t244 * t251 + 0.4e1 / 0.3e1 * t248 * t442 + 0.16e2 / 0.9e1 * t249 * t255 + 0.4e1 / 0.3e1 * t238 * t448)
  t474 = f.my_piecewise3(t234, 0, -0.3e1 / 0.8e1 * t5 * t452 * t54 * t276 - t5 * t259 * t92 * t276 / 0.2e1 + t5 * t285 * t118 * t276 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t292 * t172 * t276 + 0.10e2 / 0.27e2 * t5 * t298 * t426 * t276)
  d1111 = 0.4e1 * t232 + 0.4e1 * t304 + t6 * (t432 + t474)

  res = {'v4rho4': d1111}
  return res
