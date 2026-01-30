"""Generated from gga_k_apbe.mpl."""

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
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  pbe_f = lambda x: pbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pbe_f, rs, z, xs0, xs1)

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
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  pbe_f = lambda x: pbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pbe_f, rs, z, xs0, xs1)

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
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  pbe_f = lambda x: pbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pbe_f, rs, z, xs0, xs1)

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
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = params.mu * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t47 = params.kappa + t33 * t38 * t43 / 0.24e2
  t52 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t47)
  t56 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t52)
  t57 = r1 <= f.p.dens_threshold
  t58 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t59 = 0.1e1 + t58
  t60 = t59 <= f.p.zeta_threshold
  t61 = t59 ** (0.1e1 / 0.3e1)
  t62 = t61 ** 2
  t64 = f.my_piecewise3(t60, t24, t62 * t59)
  t65 = t64 * t30
  t66 = t37 * s2
  t67 = r1 ** 2
  t68 = r1 ** (0.1e1 / 0.3e1)
  t69 = t68 ** 2
  t71 = 0.1e1 / t69 / t67
  t75 = params.kappa + t33 * t66 * t71 / 0.24e2
  t80 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t75)
  t84 = f.my_piecewise3(t57, 0, 0.3e1 / 0.20e2 * t6 * t65 * t80)
  t85 = t7 ** 2
  t87 = t17 / t85
  t88 = t8 - t87
  t89 = f.my_piecewise5(t11, 0, t15, 0, t88)
  t92 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t89)
  t97 = 0.1e1 / t29
  t101 = t6 * t28 * t97 * t52 / 0.10e2
  t102 = params.kappa ** 2
  t104 = t6 * t31 * t102
  t105 = t47 ** 2
  t107 = 0.1e1 / t105 * params.mu
  t117 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t92 * t30 * t52 + t101 - t104 * t107 * t32 * t38 / t41 / t39 / r0 / 0.60e2)
  t119 = f.my_piecewise5(t15, 0, t11, 0, -t88)
  t122 = f.my_piecewise3(t60, 0, 0.5e1 / 0.3e1 * t62 * t119)
  t130 = t6 * t64 * t97 * t80 / 0.10e2
  t132 = f.my_piecewise3(t57, 0, 0.3e1 / 0.20e2 * t6 * t122 * t30 * t80 + t130)
  vrho_0_ = t56 + t84 + t7 * (t117 + t132)
  t135 = -t8 - t87
  t136 = f.my_piecewise5(t11, 0, t15, 0, t135)
  t139 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t136)
  t145 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t139 * t30 * t52 + t101)
  t147 = f.my_piecewise5(t15, 0, t11, 0, -t135)
  t150 = f.my_piecewise3(t60, 0, 0.5e1 / 0.3e1 * t62 * t147)
  t156 = t6 * t65 * t102
  t157 = t75 ** 2
  t159 = 0.1e1 / t157 * params.mu
  t169 = f.my_piecewise3(t57, 0, 0.3e1 / 0.20e2 * t6 * t150 * t30 * t80 + t130 - t156 * t159 * t32 * t66 / t69 / t67 / r1 / 0.60e2)
  vrho_1_ = t56 + t84 + t7 * (t145 + t169)
  t172 = t32 * t37
  t177 = f.my_piecewise3(t1, 0, t104 * t107 * t172 * t43 / 0.160e3)
  vsigma_0_ = t7 * t177
  vsigma_1_ = 0.0e0
  t182 = f.my_piecewise3(t57, 0, t156 * t159 * t172 * t71 / 0.160e3)
  vsigma_2_ = t7 * t182
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
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  pbe_f = lambda x: pbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pbe_f, rs, z, xs0, xs1)

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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t34 = r0 ** 2
  t40 = params.kappa + params.mu * t24 * t29 * s0 * t32 / t22 / t34 / 0.24e2
  t45 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t40)
  t49 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t20 * t22 * t45)
  t58 = params.kappa ** 2
  t61 = t40 ** 2
  t63 = 0.1e1 / t61 * params.mu
  t71 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t45 / 0.10e2 - t7 * t20 / t34 / r0 * t58 * t63 * t24 * t29 * s0 * t32 / 0.60e2)
  vrho_0_ = 0.2e1 * r0 * t71 + 0.2e1 * t49
  t83 = f.my_piecewise3(t2, 0, t7 * t20 / t34 * t58 * t63 * t24 * t29 * t32 / 0.160e3)
  vsigma_0_ = 0.2e1 * r0 * t83
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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t34 = r0 ** 2
  t35 = t21 ** 2
  t41 = params.kappa + params.mu * t24 * t29 * s0 * t32 / t35 / t34 / 0.24e2
  t46 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t41)
  t53 = params.kappa ** 2
  t55 = t7 * t20 / t34 / r0 * t53
  t56 = t41 ** 2
  t58 = 0.1e1 / t56 * params.mu
  t62 = t58 * t24 * t29 * s0 * t32
  t66 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t46 / 0.10e2 - t55 * t62 / 0.60e2)
  t74 = t34 ** 2
  t89 = params.mu ** 2
  t90 = 0.1e1 / t56 / t41 * t89
  t91 = t24 ** 2
  t92 = t90 * t91
  t94 = 0.1e1 / t27 / t26
  t95 = s0 ** 2
  t102 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t46 / 0.30e2 + 0.7e1 / 0.180e3 * t7 * t20 / t74 * t53 * t62 - t7 * t20 / t35 / t74 / t34 * t53 * t92 * t94 * t95 * t31 / 0.135e3)
  v2rho2_0_ = 0.2e1 * r0 * t102 + 0.4e1 * t66
  t111 = t58 * t24 * t29 * t32
  t114 = f.my_piecewise3(t2, 0, t7 * t20 / t34 * t53 * t111 / 0.160e3)
  t129 = f.my_piecewise3(t2, 0, -t55 * t111 / 0.80e2 + t7 * t20 / t35 / t74 / r0 * t53 * t92 * t94 * t31 * s0 / 0.360e3)
  v2rhosigma_0_ = 0.2e1 * r0 * t129 + 0.2e1 * t114
  t142 = f.my_piecewise3(t2, 0, -t7 * t20 / t35 / t74 * t53 * t90 * t91 * t94 * t31 / 0.960e3)
  v2sigma2_0_ = 0.2e1 * r0 * t142
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
  t25 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t35 = r0 ** 2
  t36 = t21 ** 2
  t42 = params.kappa + params.mu * t25 * t30 * s0 * t33 / t36 / t35 / 0.24e2
  t47 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t42)
  t51 = t35 ** 2
  t54 = params.kappa ** 2
  t57 = t42 ** 2
  t63 = 0.1e1 / t57 * params.mu * t25 * t30 * s0 * t33
  t74 = params.mu ** 2
  t76 = t25 ** 2
  t80 = s0 ** 2
  t83 = 0.1e1 / t57 / t42 * t74 * t76 / t28 / t27 * t80 * t32
  t87 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t47 / 0.30e2 + 0.7e1 / 0.180e3 * t7 * t20 / t51 * t54 * t63 - t7 * t20 / t36 / t51 / t35 * t54 * t83 / 0.135e3)
  t111 = t5 ** 2
  t115 = t51 ** 2
  t121 = t57 ** 2
  t131 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t35 * t47 - 0.41e2 / 0.270e3 * t7 * t20 / t51 / r0 * t54 * t63 + t7 * t20 / t36 / t51 / t35 / r0 * t54 * t83 / 0.15e2 - 0.4e1 / 0.135e3 * t4 / t111 / t27 * t20 / t21 / t115 / t35 * t54 / t121 * t74 * params.mu * t80 * s0)
  v3rho3_0_ = 0.2e1 * r0 * t131 + 0.6e1 * t87

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
  t26 = 6 ** (0.1e1 / 0.3e1)
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = 0.1e1 / t30
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t36 = t22 ** 2
  t42 = params.kappa + params.mu * t26 * t31 * s0 * t34 / t36 / t21 / 0.24e2
  t47 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t42)
  t51 = t21 ** 2
  t55 = params.kappa ** 2
  t58 = t42 ** 2
  t64 = 0.1e1 / t58 * params.mu * t26 * t31 * s0 * t34
  t67 = t21 * r0
  t76 = params.mu ** 2
  t78 = t26 ** 2
  t82 = s0 ** 2
  t85 = 0.1e1 / t58 / t42 * t76 * t78 / t29 / t28 * t82 * t33
  t88 = t5 ** 2
  t91 = t4 / t88 / t28
  t92 = t51 ** 2
  t98 = t58 ** 2
  t104 = t55 / t98 * t76 * params.mu * t82 * s0
  t108 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t22 / t21 * t47 - 0.41e2 / 0.270e3 * t7 * t20 / t51 / r0 * t55 * t64 + t7 * t20 / t36 / t51 / t67 * t55 * t85 / 0.15e2 - 0.4e1 / 0.135e3 * t91 * t20 / t22 / t92 / t21 * t104)
  t116 = t51 * t21
  t144 = t76 ** 2
  t146 = t82 ** 2
  t154 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 / t22 / t67 * t47 + 0.611e3 / 0.810e3 * t7 * t20 / t116 * t55 * t64 - 0.703e3 / 0.1215e4 * t7 * t20 / t36 / t92 * t55 * t85 + 0.232e3 / 0.405e3 * t91 * t20 / t22 / t92 / t67 * t104 - 0.16e2 / 0.1215e4 * t91 * t20 / t92 / t116 * t55 / t98 / t42 * t144 * t146 * t26 * t31 * t34)
  v4rho4_0_ = 0.2e1 * r0 * t154 + 0.8e1 * t108

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
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = params.mu * t35
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t41 = t40 * s0
  t42 = r0 ** 2
  t43 = r0 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t50 = params.kappa + t36 * t41 / t44 / t42 / 0.24e2
  t55 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t50)
  t59 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = t60 * f.p.zeta_threshold
  t63 = f.my_piecewise3(t21, t61, t23 * t20)
  t64 = 0.1e1 / t32
  t65 = t63 * t64
  t68 = t6 * t65 * t55 / 0.10e2
  t70 = params.kappa ** 2
  t72 = t6 * t63 * t33 * t70
  t73 = t50 ** 2
  t76 = 0.1e1 / t73 * params.mu * t35
  t77 = t42 * r0
  t81 = t76 * t41 / t44 / t77
  t85 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t55 + t68 - t72 * t81 / 0.60e2)
  t87 = r1 <= f.p.dens_threshold
  t88 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t89 = 0.1e1 + t88
  t90 = t89 <= f.p.zeta_threshold
  t91 = t89 ** (0.1e1 / 0.3e1)
  t92 = t91 ** 2
  t94 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t97 = f.my_piecewise3(t90, 0, 0.5e1 / 0.3e1 * t92 * t94)
  t98 = t97 * t33
  t99 = t40 * s2
  t100 = r1 ** 2
  t101 = r1 ** (0.1e1 / 0.3e1)
  t102 = t101 ** 2
  t108 = params.kappa + t36 * t99 / t102 / t100 / 0.24e2
  t113 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t108)
  t118 = f.my_piecewise3(t90, t61, t92 * t89)
  t119 = t118 * t64
  t122 = t6 * t119 * t113 / 0.10e2
  t124 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t98 * t113 + t122)
  t126 = 0.1e1 / t22
  t127 = t28 ** 2
  t132 = t17 / t24 / t7
  t134 = -0.2e1 * t25 + 0.2e1 * t132
  t135 = f.my_piecewise5(t11, 0, t15, 0, t134)
  t139 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t126 * t127 + 0.5e1 / 0.3e1 * t23 * t135)
  t146 = t6 * t31 * t64 * t55
  t153 = 0.1e1 / t32 / t7
  t157 = t6 * t63 * t153 * t55 / 0.30e2
  t160 = t6 * t65 * t70 * t81
  t164 = params.mu ** 2
  t166 = t35 ** 2
  t169 = 0.1e1 / t38 / t37
  t170 = s0 ** 2
  t172 = t42 ** 2
  t187 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t139 * t33 * t55 + t146 / 0.5e1 - t6 * t34 * t70 * t81 / 0.30e2 - t157 - t160 / 0.45e2 - t72 / t73 / t50 * t164 * t166 * t169 * t170 / t43 / t172 / t77 / 0.270e3 + 0.11e2 / 0.180e3 * t72 * t76 * t41 / t44 / t172)
  t188 = 0.1e1 / t91
  t189 = t94 ** 2
  t193 = f.my_piecewise5(t15, 0, t11, 0, -t134)
  t197 = f.my_piecewise3(t90, 0, 0.10e2 / 0.9e1 * t188 * t189 + 0.5e1 / 0.3e1 * t92 * t193)
  t204 = t6 * t97 * t64 * t113
  t209 = t6 * t118 * t153 * t113 / 0.30e2
  t211 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t197 * t33 * t113 + t204 / 0.5e1 - t209)
  d11 = 0.2e1 * t85 + 0.2e1 * t124 + t7 * (t187 + t211)
  t214 = -t8 - t26
  t215 = f.my_piecewise5(t11, 0, t15, 0, t214)
  t218 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t215)
  t219 = t218 * t33
  t224 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t219 * t55 + t68)
  t226 = f.my_piecewise5(t15, 0, t11, 0, -t214)
  t229 = f.my_piecewise3(t90, 0, 0.5e1 / 0.3e1 * t92 * t226)
  t230 = t229 * t33
  t236 = t6 * t118 * t33 * t70
  t237 = t108 ** 2
  t240 = 0.1e1 / t237 * params.mu * t35
  t241 = t100 * r1
  t245 = t240 * t99 / t102 / t241
  t249 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t230 * t113 + t122 - t236 * t245 / 0.60e2)
  t253 = 0.2e1 * t132
  t254 = f.my_piecewise5(t11, 0, t15, 0, t253)
  t258 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t126 * t215 * t28 + 0.5e1 / 0.3e1 * t23 * t254)
  t265 = t6 * t218 * t64 * t55
  t274 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t258 * t33 * t55 + t265 / 0.10e2 - t6 * t219 * t70 * t81 / 0.60e2 + t146 / 0.10e2 - t157 - t160 / 0.90e2)
  t278 = f.my_piecewise5(t15, 0, t11, 0, -t253)
  t282 = f.my_piecewise3(t90, 0, 0.10e2 / 0.9e1 * t188 * t226 * t94 + 0.5e1 / 0.3e1 * t92 * t278)
  t289 = t6 * t229 * t64 * t113
  t298 = t6 * t119 * t70 * t245
  t301 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t282 * t33 * t113 + t289 / 0.10e2 + t204 / 0.10e2 - t209 - t6 * t98 * t70 * t245 / 0.60e2 - t298 / 0.90e2)
  d12 = t85 + t124 + t224 + t249 + t7 * (t274 + t301)
  t306 = t215 ** 2
  t310 = 0.2e1 * t25 + 0.2e1 * t132
  t311 = f.my_piecewise5(t11, 0, t15, 0, t310)
  t315 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t126 * t306 + 0.5e1 / 0.3e1 * t23 * t311)
  t322 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t315 * t33 * t55 + t265 / 0.5e1 - t157)
  t323 = t226 ** 2
  t327 = f.my_piecewise5(t15, 0, t11, 0, -t310)
  t331 = f.my_piecewise3(t90, 0, 0.10e2 / 0.9e1 * t188 * t323 + 0.5e1 / 0.3e1 * t92 * t327)
  t346 = s2 ** 2
  t348 = t100 ** 2
  t363 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t331 * t33 * t113 + t289 / 0.5e1 - t6 * t230 * t70 * t245 / 0.30e2 - t209 - t298 / 0.45e2 - t236 / t237 / t108 * t164 * t166 * t169 * t346 / t101 / t348 / t241 / 0.270e3 + 0.11e2 / 0.180e3 * t236 * t240 * t99 / t102 / t348)
  d22 = 0.2e1 * t224 + 0.2e1 * t249 + t7 * (t322 + t363)
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
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = params.mu * t46
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t52 = t51 * s0
  t53 = r0 ** 2
  t54 = r0 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t61 = params.kappa + t47 * t52 / t55 / t53 / 0.24e2
  t66 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t61)
  t72 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t73 = 0.1e1 / t43
  t74 = t72 * t73
  t79 = params.kappa ** 2
  t81 = t6 * t72 * t44 * t79
  t82 = t61 ** 2
  t85 = 0.1e1 / t82 * params.mu * t46
  t86 = t53 * r0
  t90 = t85 * t52 / t55 / t86
  t93 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t94 = t93 ** 2
  t95 = t94 * f.p.zeta_threshold
  t97 = f.my_piecewise3(t21, t95, t32 * t20)
  t99 = 0.1e1 / t43 / t7
  t100 = t97 * t99
  t106 = t6 * t97 * t73 * t79
  t109 = t97 * t44
  t111 = t6 * t109 * t79
  t114 = params.mu ** 2
  t116 = t46 ** 2
  t117 = 0.1e1 / t82 / t61 * t114 * t116
  t120 = s0 ** 2
  t121 = 0.1e1 / t49 / t48 * t120
  t122 = t53 ** 2
  t127 = t117 * t121 / t54 / t122 / t86
  t133 = t85 * t52 / t55 / t122
  t137 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t66 + t6 * t74 * t66 / 0.5e1 - t81 * t90 / 0.30e2 - t6 * t100 * t66 / 0.30e2 - t106 * t90 / 0.45e2 - t111 * t127 / 0.270e3 + 0.11e2 / 0.180e3 * t111 * t133)
  t139 = r1 <= f.p.dens_threshold
  t140 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t141 = 0.1e1 + t140
  t142 = t141 <= f.p.zeta_threshold
  t143 = t141 ** (0.1e1 / 0.3e1)
  t144 = 0.1e1 / t143
  t146 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t147 = t146 ** 2
  t150 = t143 ** 2
  t152 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t156 = f.my_piecewise3(t142, 0, 0.10e2 / 0.9e1 * t144 * t147 + 0.5e1 / 0.3e1 * t150 * t152)
  t159 = r1 ** 2
  t160 = r1 ** (0.1e1 / 0.3e1)
  t161 = t160 ** 2
  t172 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + t47 * t51 * s2 / t161 / t159 / 0.24e2))
  t178 = f.my_piecewise3(t142, 0, 0.5e1 / 0.3e1 * t150 * t146)
  t184 = f.my_piecewise3(t142, t95, t150 * t141)
  t190 = f.my_piecewise3(t139, 0, 0.3e1 / 0.20e2 * t6 * t156 * t44 * t172 + t6 * t178 * t73 * t172 / 0.5e1 - t6 * t184 * t99 * t172 / 0.30e2)
  t209 = t122 ** 2
  t218 = t4 ** 2
  t223 = t82 ** 2
  t243 = t24 ** 2
  t247 = 0.6e1 * t34 - 0.6e1 * t17 / t243
  t248 = f.my_piecewise5(t11, 0, t15, 0, t247)
  t252 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t248)
  t274 = 0.1e1 / t43 / t24
  t279 = -t81 * t127 / 0.90e2 + t6 * t100 * t79 * t90 / 0.90e2 - t106 * t127 / 0.135e3 - 0.77e2 / 0.270e3 * t111 * t85 * t52 / t55 / t122 / r0 + 0.11e2 / 0.90e2 * t106 * t133 + 0.11e2 / 0.270e3 * t111 * t117 * t121 / t54 / t209 + 0.11e2 / 0.60e2 * t81 * t133 - t3 / t218 / t48 * t109 * t79 / t223 * t114 * params.mu * t120 * s0 / t209 / t86 / 0.135e3 + 0.3e1 / 0.20e2 * t6 * t252 * t44 * t66 - t6 * t45 * t79 * t90 / 0.20e2 - t6 * t74 * t79 * t90 / 0.15e2 + 0.3e1 / 0.10e2 * t6 * t42 * t73 * t66 - t6 * t72 * t99 * t66 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t97 * t274 * t66
  t280 = f.my_piecewise3(t1, 0, t279)
  t290 = f.my_piecewise5(t15, 0, t11, 0, -t247)
  t294 = f.my_piecewise3(t142, 0, -0.10e2 / 0.27e2 / t143 / t141 * t147 * t146 + 0.10e2 / 0.3e1 * t144 * t146 * t152 + 0.5e1 / 0.3e1 * t150 * t290)
  t312 = f.my_piecewise3(t139, 0, 0.3e1 / 0.20e2 * t6 * t294 * t44 * t172 + 0.3e1 / 0.10e2 * t6 * t156 * t73 * t172 - t6 * t178 * t99 * t172 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t184 * t274 * t172)
  d111 = 0.3e1 * t137 + 0.3e1 * t190 + t7 * (t280 + t312)

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
  t23 = t22 ** 2
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t27 = -t17 * t25 + t8
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t31 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t28)
  t32 = t7 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = t31 * t33
  t35 = params.kappa ** 2
  t37 = t6 * t34 * t35
  t38 = 6 ** (0.1e1 / 0.3e1)
  t39 = params.mu * t38
  t40 = jnp.pi ** 2
  t41 = t40 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t43 = 0.1e1 / t42
  t44 = t43 * s0
  t45 = r0 ** 2
  t46 = r0 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t53 = params.kappa + t39 * t44 / t47 / t45 / 0.24e2
  t54 = t53 ** 2
  t57 = params.mu ** 2
  t59 = t38 ** 2
  t60 = 0.1e1 / t54 / t53 * t57 * t59
  t63 = s0 ** 2
  t64 = 0.1e1 / t41 / t40 * t63
  t65 = t45 * r0
  t66 = t45 ** 2
  t71 = t60 * t64 / t46 / t66 / t65
  t74 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t75 = t74 ** 2
  t76 = t75 * f.p.zeta_threshold
  t78 = f.my_piecewise3(t21, t76, t23 * t20)
  t80 = 0.1e1 / t32 / t7
  t83 = t6 * t78 * t80 * t35
  t86 = 0.1e1 / t54 * params.mu * t38
  t90 = t86 * t44 / t47 / t65
  t93 = 0.1e1 / t32
  t94 = t78 * t93
  t96 = t6 * t94 * t35
  t99 = t78 * t33
  t100 = t99 * t35
  t101 = t6 * t100
  t106 = t86 * t44 / t47 / t66 / r0
  t112 = t86 * t44 / t47 / t66
  t115 = t66 ** 2
  t119 = t60 * t64 / t46 / t115
  t124 = t4 ** 2
  t127 = t3 / t124 / t40
  t128 = t127 * t99
  t129 = t54 ** 2
  t131 = t35 / t129
  t134 = t57 * params.mu * t63 * s0
  t138 = t131 * t134 / t115 / t65
  t142 = 0.1e1 / t22 / t20
  t143 = t28 ** 2
  t147 = 0.1e1 / t22
  t148 = t147 * t28
  t149 = t24 * t7
  t150 = 0.1e1 / t149
  t153 = 0.2e1 * t17 * t150 - 0.2e1 * t25
  t154 = f.my_piecewise5(t11, 0, t15, 0, t153)
  t157 = t24 ** 2
  t158 = 0.1e1 / t157
  t161 = -0.6e1 * t17 * t158 + 0.6e1 * t150
  t162 = f.my_piecewise5(t11, 0, t15, 0, t161)
  t166 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 * t142 * t143 * t28 + 0.10e2 / 0.3e1 * t148 * t154 + 0.5e1 / 0.3e1 * t23 * t162)
  t167 = t166 * t33
  t172 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t53)
  t181 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t147 * t143 + 0.5e1 / 0.3e1 * t23 * t154)
  t184 = t6 * t181 * t33 * t35
  t189 = t6 * t31 * t93 * t35
  t192 = t181 * t93
  t196 = t31 * t80
  t201 = 0.1e1 / t32 / t24
  t202 = t78 * t201
  t206 = -t37 * t71 / 0.90e2 + t83 * t90 / 0.90e2 - t96 * t71 / 0.135e3 - 0.77e2 / 0.270e3 * t101 * t106 + 0.11e2 / 0.90e2 * t96 * t112 + 0.11e2 / 0.270e3 * t101 * t119 + 0.11e2 / 0.60e2 * t37 * t112 - t128 * t138 / 0.135e3 + 0.3e1 / 0.20e2 * t6 * t167 * t172 - t184 * t90 / 0.20e2 - t189 * t90 / 0.15e2 + 0.3e1 / 0.10e2 * t6 * t192 * t172 - t6 * t196 * t172 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t202 * t172
  t207 = f.my_piecewise3(t1, 0, t206)
  t209 = r1 <= f.p.dens_threshold
  t210 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t211 = 0.1e1 + t210
  t212 = t211 <= f.p.zeta_threshold
  t213 = t211 ** (0.1e1 / 0.3e1)
  t215 = 0.1e1 / t213 / t211
  t217 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t218 = t217 ** 2
  t222 = 0.1e1 / t213
  t223 = t222 * t217
  t225 = f.my_piecewise5(t15, 0, t11, 0, -t153)
  t228 = t213 ** 2
  t230 = f.my_piecewise5(t15, 0, t11, 0, -t161)
  t234 = f.my_piecewise3(t212, 0, -0.10e2 / 0.27e2 * t215 * t218 * t217 + 0.10e2 / 0.3e1 * t223 * t225 + 0.5e1 / 0.3e1 * t228 * t230)
  t237 = r1 ** 2
  t238 = r1 ** (0.1e1 / 0.3e1)
  t239 = t238 ** 2
  t250 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + t39 * t43 * s2 / t239 / t237 / 0.24e2))
  t259 = f.my_piecewise3(t212, 0, 0.10e2 / 0.9e1 * t222 * t218 + 0.5e1 / 0.3e1 * t228 * t225)
  t266 = f.my_piecewise3(t212, 0, 0.5e1 / 0.3e1 * t228 * t217)
  t272 = f.my_piecewise3(t212, t76, t228 * t211)
  t278 = f.my_piecewise3(t209, 0, 0.3e1 / 0.20e2 * t6 * t234 * t33 * t250 + 0.3e1 / 0.10e2 * t6 * t259 * t93 * t250 - t6 * t266 * t80 * t250 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t272 * t201 * t250)
  t281 = 0.1e1 / t32 / t149
  t286 = t20 ** 2
  t289 = t143 ** 2
  t295 = t154 ** 2
  t304 = -0.24e2 * t158 + 0.24e2 * t17 / t157 / t7
  t305 = f.my_piecewise5(t11, 0, t15, 0, t304)
  t309 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t286 * t289 - 0.20e2 / 0.9e1 * t142 * t143 * t154 + 0.10e2 / 0.3e1 * t147 * t295 + 0.40e2 / 0.9e1 * t148 * t162 + 0.5e1 / 0.3e1 * t23 * t305)
  t333 = t57 ** 2
  t335 = t63 ** 2
  t337 = t66 * t45
  t361 = -0.14e2 / 0.135e3 * t6 * t78 * t281 * t172 + 0.3e1 / 0.20e2 * t6 * t309 * t33 * t172 + 0.2e1 / 0.5e1 * t6 * t166 * t93 * t172 - t6 * t181 * t80 * t172 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t31 * t201 * t172 - 0.11e2 / 0.135e3 * t83 * t112 - 0.4e1 / 0.135e3 * t189 * t71 - 0.4e1 / 0.1215e4 * t127 * t100 / t129 / t53 * t333 * t335 / t47 / t115 / t337 * t38 * t43 - t6 * t167 * t35 * t90 / 0.15e2 + 0.2e1 / 0.405e3 * t83 * t71 - 0.154e3 / 0.135e3 * t37 * t106 - 0.979e3 / 0.2430e4 * t101 * t60 * t64 / t46 / t115 / r0
  t404 = 0.22e2 / 0.45e2 * t189 * t112 + 0.11e2 / 0.30e2 * t184 * t112 - t184 * t71 / 0.45e2 + 0.2e1 / 0.45e2 * t6 * t196 * t35 * t90 - 0.2e1 / 0.15e2 * t6 * t192 * t35 * t90 + 0.44e2 / 0.405e3 * t96 * t119 - 0.308e3 / 0.405e3 * t96 * t106 + 0.1309e4 / 0.810e3 * t101 * t86 * t44 / t47 / t337 + 0.22e2 / 0.135e3 * t37 * t119 - 0.8e1 / 0.405e3 * t6 * t202 * t35 * t90 - 0.4e1 / 0.135e3 * t127 * t34 * t138 - 0.8e1 / 0.405e3 * t127 * t94 * t138 + 0.22e2 / 0.135e3 * t128 * t131 * t134 / t115 / t66
  t406 = f.my_piecewise3(t1, 0, t361 + t404)
  t407 = t211 ** 2
  t410 = t218 ** 2
  t416 = t225 ** 2
  t422 = f.my_piecewise5(t15, 0, t11, 0, -t304)
  t426 = f.my_piecewise3(t212, 0, 0.40e2 / 0.81e2 / t213 / t407 * t410 - 0.20e2 / 0.9e1 * t215 * t218 * t225 + 0.10e2 / 0.3e1 * t222 * t416 + 0.40e2 / 0.9e1 * t223 * t230 + 0.5e1 / 0.3e1 * t228 * t422)
  t448 = f.my_piecewise3(t209, 0, 0.3e1 / 0.20e2 * t6 * t426 * t33 * t250 + 0.2e1 / 0.5e1 * t6 * t234 * t93 * t250 - t6 * t259 * t80 * t250 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t266 * t201 * t250 - 0.14e2 / 0.135e3 * t6 * t272 * t281 * t250)
  d1111 = 0.4e1 * t207 + 0.4e1 * t278 + t7 * (t406 + t448)

  res = {'v4rho4': d1111}
  return res
