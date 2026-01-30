"""Generated from gga_x_rpbe.mpl."""

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
  params_rpbe_kappa_raw = params.rpbe_kappa
  if isinstance(params_rpbe_kappa_raw, (str, bytes, dict)):
    params_rpbe_kappa = params_rpbe_kappa_raw
  else:
    try:
      params_rpbe_kappa_seq = list(params_rpbe_kappa_raw)
    except TypeError:
      params_rpbe_kappa = params_rpbe_kappa_raw
    else:
      params_rpbe_kappa_seq = np.asarray(params_rpbe_kappa_seq, dtype=np.float64)
      params_rpbe_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_rpbe_kappa_seq))
  params_rpbe_mu_raw = params.rpbe_mu
  if isinstance(params_rpbe_mu_raw, (str, bytes, dict)):
    params_rpbe_mu = params_rpbe_mu_raw
  else:
    try:
      params_rpbe_mu_seq = list(params_rpbe_mu_raw)
    except TypeError:
      params_rpbe_mu = params_rpbe_mu_raw
    else:
      params_rpbe_mu_seq = np.asarray(params_rpbe_mu_seq, dtype=np.float64)
      params_rpbe_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_rpbe_mu_seq))

  rpbe_f0 = lambda s: 1 + params_rpbe_kappa * (1 - jnp.exp(-params_rpbe_mu * s ** 2 / params_rpbe_kappa))

  rpbe_f = lambda x: rpbe_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, rpbe_f, rs, zeta, xs0, xs1)

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
  params_rpbe_kappa_raw = params.rpbe_kappa
  if isinstance(params_rpbe_kappa_raw, (str, bytes, dict)):
    params_rpbe_kappa = params_rpbe_kappa_raw
  else:
    try:
      params_rpbe_kappa_seq = list(params_rpbe_kappa_raw)
    except TypeError:
      params_rpbe_kappa = params_rpbe_kappa_raw
    else:
      params_rpbe_kappa_seq = np.asarray(params_rpbe_kappa_seq, dtype=np.float64)
      params_rpbe_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_rpbe_kappa_seq))
  params_rpbe_mu_raw = params.rpbe_mu
  if isinstance(params_rpbe_mu_raw, (str, bytes, dict)):
    params_rpbe_mu = params_rpbe_mu_raw
  else:
    try:
      params_rpbe_mu_seq = list(params_rpbe_mu_raw)
    except TypeError:
      params_rpbe_mu = params_rpbe_mu_raw
    else:
      params_rpbe_mu_seq = np.asarray(params_rpbe_mu_seq, dtype=np.float64)
      params_rpbe_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_rpbe_mu_seq))

  rpbe_f0 = lambda s: 1 + params_rpbe_kappa * (1 - jnp.exp(-params_rpbe_mu * s ** 2 / params_rpbe_kappa))

  rpbe_f = lambda x: rpbe_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, rpbe_f, rs, zeta, xs0, xs1)

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
  params_rpbe_kappa_raw = params.rpbe_kappa
  if isinstance(params_rpbe_kappa_raw, (str, bytes, dict)):
    params_rpbe_kappa = params_rpbe_kappa_raw
  else:
    try:
      params_rpbe_kappa_seq = list(params_rpbe_kappa_raw)
    except TypeError:
      params_rpbe_kappa = params_rpbe_kappa_raw
    else:
      params_rpbe_kappa_seq = np.asarray(params_rpbe_kappa_seq, dtype=np.float64)
      params_rpbe_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_rpbe_kappa_seq))
  params_rpbe_mu_raw = params.rpbe_mu
  if isinstance(params_rpbe_mu_raw, (str, bytes, dict)):
    params_rpbe_mu = params_rpbe_mu_raw
  else:
    try:
      params_rpbe_mu_seq = list(params_rpbe_mu_raw)
    except TypeError:
      params_rpbe_mu = params_rpbe_mu_raw
    else:
      params_rpbe_mu_seq = np.asarray(params_rpbe_mu_seq, dtype=np.float64)
      params_rpbe_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_rpbe_mu_seq))

  rpbe_f0 = lambda s: 1 + params_rpbe_kappa * (1 - jnp.exp(-params_rpbe_mu * s ** 2 / params_rpbe_kappa))

  rpbe_f = lambda x: rpbe_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, rpbe_f, rs, zeta, xs0, xs1)

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
  t28 = 6 ** (0.1e1 / 0.3e1)
  t29 = params.rpbe_mu * t28
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = t29 * t33
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t41 = 0.1e1 / params.rpbe_kappa
  t45 = jnp.exp(-t34 * s0 * t39 * t41 / 0.24e2)
  t48 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t45)
  t52 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t48)
  t53 = r1 <= f.p.dens_threshold
  t54 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t55 = 0.1e1 + t54
  t56 = t55 <= f.p.zeta_threshold
  t57 = t55 ** (0.1e1 / 0.3e1)
  t59 = f.my_piecewise3(t56, t22, t57 * t55)
  t60 = t59 * t26
  t61 = r1 ** 2
  t62 = r1 ** (0.1e1 / 0.3e1)
  t63 = t62 ** 2
  t65 = 0.1e1 / t63 / t61
  t70 = jnp.exp(-t34 * s2 * t65 * t41 / 0.24e2)
  t73 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t70)
  t77 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t60 * t73)
  t78 = t6 ** 2
  t80 = t16 / t78
  t81 = t7 - t80
  t82 = f.my_piecewise5(t10, 0, t14, 0, t81)
  t85 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t82)
  t90 = t26 ** 2
  t91 = 0.1e1 / t90
  t95 = t5 * t25 * t91 * t48 / 0.8e1
  t98 = t28 * t33
  t108 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t85 * t26 * t48 - t95 + t5 * t27 * params.rpbe_mu * t98 * s0 / t37 / t35 / r0 * t45 / 0.24e2)
  t110 = f.my_piecewise5(t14, 0, t10, 0, -t81)
  t113 = f.my_piecewise3(t56, 0, 0.4e1 / 0.3e1 * t57 * t110)
  t121 = t5 * t59 * t91 * t73 / 0.8e1
  t123 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t113 * t26 * t73 - t121)
  vrho_0_ = t52 + t77 + t6 * (t108 + t123)
  t126 = -t7 - t80
  t127 = f.my_piecewise5(t10, 0, t14, 0, t126)
  t130 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t127)
  t136 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t130 * t26 * t48 - t95)
  t138 = f.my_piecewise5(t14, 0, t10, 0, -t126)
  t141 = f.my_piecewise3(t56, 0, 0.4e1 / 0.3e1 * t57 * t138)
  t157 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t141 * t26 * t73 - t121 + t5 * t60 * params.rpbe_mu * t98 * s2 / t63 / t61 / r1 * t70 / 0.24e2)
  vrho_1_ = t52 + t77 + t6 * (t136 + t157)
  t166 = f.my_piecewise3(t1, 0, -t5 * t27 * t29 * t33 * t39 * t45 / 0.64e2)
  vsigma_0_ = t6 * t166
  vsigma_1_ = 0.0e0
  t173 = f.my_piecewise3(t53, 0, -t5 * t60 * t29 * t33 * t65 * t70 / 0.64e2)
  vsigma_2_ = t6 * t173
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
  params_rpbe_kappa_raw = params.rpbe_kappa
  if isinstance(params_rpbe_kappa_raw, (str, bytes, dict)):
    params_rpbe_kappa = params_rpbe_kappa_raw
  else:
    try:
      params_rpbe_kappa_seq = list(params_rpbe_kappa_raw)
    except TypeError:
      params_rpbe_kappa = params_rpbe_kappa_raw
    else:
      params_rpbe_kappa_seq = np.asarray(params_rpbe_kappa_seq, dtype=np.float64)
      params_rpbe_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_rpbe_kappa_seq))
  params_rpbe_mu_raw = params.rpbe_mu
  if isinstance(params_rpbe_mu_raw, (str, bytes, dict)):
    params_rpbe_mu = params_rpbe_mu_raw
  else:
    try:
      params_rpbe_mu_seq = list(params_rpbe_mu_raw)
    except TypeError:
      params_rpbe_mu = params_rpbe_mu_raw
    else:
      params_rpbe_mu_seq = np.asarray(params_rpbe_mu_seq, dtype=np.float64)
      params_rpbe_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_rpbe_mu_seq))

  rpbe_f0 = lambda s: 1 + params_rpbe_kappa * (1 - jnp.exp(-params_rpbe_mu * s ** 2 / params_rpbe_kappa))

  rpbe_f = lambda x: rpbe_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, rpbe_f, rs, zeta, xs0, xs1)

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
  t20 = 6 ** (0.1e1 / 0.3e1)
  t21 = params.rpbe_mu * t20
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t18 ** 2
  t39 = jnp.exp(-t21 * t25 * t29 / t31 / t30 / params.rpbe_kappa / 0.24e2)
  t42 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t39)
  t46 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t42)
  t64 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t42 / 0.8e1 + t6 * t17 / t18 / t30 / r0 * params.rpbe_mu * t20 * t25 * t29 * t39 / 0.24e2)
  vrho_0_ = 0.2e1 * r0 * t64 + 0.2e1 * t46
  t76 = f.my_piecewise3(t2, 0, -t6 * t17 / t18 / t30 * t21 * t25 * t28 * t39 / 0.64e2)
  vsigma_0_ = 0.2e1 * r0 * t76
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
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = params.rpbe_mu * t22
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t35 = 0.1e1 / params.rpbe_kappa
  t40 = jnp.exp(-t23 * t27 * t31 / t19 / t32 * t35 / 0.24e2)
  t43 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t40)
  t47 = t32 * r0
  t50 = t17 / t18 / t47
  t55 = t22 * t27 * t31 * t40
  t59 = f.my_piecewise3(t2, 0, -t6 * t17 / t19 * t43 / 0.8e1 + t6 * t50 * params.rpbe_mu * t55 / 0.24e2)
  t67 = t32 ** 2
  t78 = params.rpbe_mu ** 2
  t81 = t22 ** 2
  t84 = t81 / t25 / t24
  t85 = s0 ** 2
  t88 = t29 * t35 * t40
  t93 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t43 / 0.12e2 - t6 * t17 / t18 / t67 * params.rpbe_mu * t55 / 0.8e1 + t6 * t17 / t67 / t47 * t78 * t84 * t85 * t88 / 0.108e3)
  v2rho2_0_ = 0.2e1 * r0 * t93 + 0.4e1 * t59
  t102 = t23 * t27 * t30 * t40
  t105 = f.my_piecewise3(t2, 0, -t6 * t17 / t18 / t32 * t102 / 0.64e2)
  t121 = f.my_piecewise3(t2, 0, 0.7e1 / 0.192e3 * t6 * t50 * t102 - t6 * t17 / t67 / t32 * t78 * t84 * t29 * s0 * t35 * t40 / 0.288e3)
  v2rhosigma_0_ = 0.2e1 * r0 * t121 + 0.2e1 * t105
  t132 = f.my_piecewise3(t2, 0, t6 * t17 / t67 / r0 * t78 * t84 * t88 / 0.768e3)
  v2sigma2_0_ = 0.2e1 * r0 * t132
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
  t23 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t36 = 0.1e1 / params.rpbe_kappa
  t41 = jnp.exp(-params.rpbe_mu * t23 * t28 * t32 * t35 * t36 / 0.24e2)
  t44 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t41)
  t48 = t33 ** 2
  t56 = t23 * t28 * t32 * t41
  t63 = params.rpbe_mu ** 2
  t66 = t23 ** 2
  t70 = s0 ** 2
  t74 = t66 / t26 / t25 * t70 * t30 * t36 * t41
  t78 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t44 / 0.12e2 - t6 * t17 / t18 / t48 * params.rpbe_mu * t56 / 0.8e1 + t6 * t17 / t48 / t33 / r0 * t63 * t74 / 0.108e3)
  t92 = t48 ** 2
  t99 = t25 ** 2
  t111 = params.rpbe_kappa ** 2
  t118 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t44 + 0.115e3 / 0.216e3 * t6 * t17 / t18 / t48 / r0 * params.rpbe_mu * t56 - 0.5e1 / 0.54e2 * t6 * t17 / t92 * t63 * t74 + t3 / t4 / t99 * t17 / t19 / t92 / t33 * t63 * params.rpbe_mu * t70 * s0 / t111 * t41 / 0.81e2)
  v3rho3_0_ = 0.2e1 * r0 * t118 + 0.6e1 * t78

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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = 0.1e1 / params.rpbe_kappa
  t39 = jnp.exp(-params.rpbe_mu * t24 * t29 * t33 * t22 * t34 / 0.24e2)
  t42 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t39)
  t46 = t18 ** 2
  t55 = t24 * t29 * t33 * t39
  t58 = t46 ** 2
  t61 = params.rpbe_mu ** 2
  t64 = t24 ** 2
  t68 = s0 ** 2
  t72 = t64 / t27 / t26 * t68 * t31 * t34 * t39
  t75 = t26 ** 2
  t78 = t3 / t4 / t75
  t87 = params.rpbe_kappa ** 2
  t90 = t61 * params.rpbe_mu * t68 * s0 / t87 * t39
  t94 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t42 + 0.115e3 / 0.216e3 * t6 * t17 / t19 / t46 / r0 * params.rpbe_mu * t55 - 0.5e1 / 0.54e2 * t6 * t17 / t58 * t61 * t72 + t78 * t17 / t20 / t58 / t18 * t90 / 0.81e2)
  t96 = t18 * r0
  t103 = t46 * t18
  t129 = t61 ** 2
  t132 = t68 ** 2
  t143 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 / t20 / t96 * t42 - 0.305e3 / 0.108e3 * t6 * t17 / t19 / t103 * params.rpbe_mu * t55 + 0.835e3 / 0.972e3 * t6 * t17 / t58 / r0 * t61 * t72 - 0.62e2 / 0.243e3 * t78 * t17 / t20 / t58 / t96 * t90 + t78 * t17 / t19 / t58 / t103 * t129 * t132 / t87 / params.rpbe_kappa * t24 * t29 * t32 * t39 / 0.729e3)
  v4rho4_0_ = 0.2e1 * r0 * t143 + 0.8e1 * t94

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
  t32 = 6 ** (0.1e1 / 0.3e1)
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = params.rpbe_mu * t32 * t37
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t45 = 0.1e1 / params.rpbe_kappa
  t49 = jnp.exp(-t38 * s0 / t41 / t39 * t45 / 0.24e2)
  t52 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t49)
  t56 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t57 = t56 * f.p.zeta_threshold
  t59 = f.my_piecewise3(t20, t57, t21 * t19)
  t60 = t30 ** 2
  t61 = 0.1e1 / t60
  t62 = t59 * t61
  t65 = t5 * t62 * t52 / 0.8e1
  t66 = t59 * t30
  t68 = t5 * t66 * params.rpbe_mu
  t69 = t32 * t37
  t70 = t39 * r0
  t75 = t69 * s0 / t41 / t70 * t49
  t79 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t52 - t65 + t68 * t75 / 0.24e2)
  t81 = r1 <= f.p.dens_threshold
  t82 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t83 = 0.1e1 + t82
  t84 = t83 <= f.p.zeta_threshold
  t85 = t83 ** (0.1e1 / 0.3e1)
  t87 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t90 = f.my_piecewise3(t84, 0, 0.4e1 / 0.3e1 * t85 * t87)
  t91 = t90 * t30
  t92 = r1 ** 2
  t93 = r1 ** (0.1e1 / 0.3e1)
  t94 = t93 ** 2
  t101 = jnp.exp(-t38 * s2 / t94 / t92 * t45 / 0.24e2)
  t104 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t101)
  t109 = f.my_piecewise3(t84, t57, t85 * t83)
  t110 = t109 * t61
  t113 = t5 * t110 * t104 / 0.8e1
  t115 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t91 * t104 - t113)
  t117 = t21 ** 2
  t118 = 0.1e1 / t117
  t119 = t26 ** 2
  t124 = t16 / t22 / t6
  t126 = -0.2e1 * t23 + 0.2e1 * t124
  t127 = f.my_piecewise5(t10, 0, t14, 0, t126)
  t131 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t118 * t119 + 0.4e1 / 0.3e1 * t21 * t127)
  t138 = t5 * t29 * t61 * t52
  t145 = 0.1e1 / t60 / t6
  t149 = t5 * t59 * t145 * t52 / 0.12e2
  t152 = t5 * t62 * params.rpbe_mu * t75
  t154 = t39 ** 2
  t162 = params.rpbe_mu ** 2
  t165 = t32 ** 2
  t168 = t165 / t35 / t34
  t169 = s0 ** 2
  t180 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t131 * t30 * t52 - t138 / 0.4e1 + t5 * t31 * params.rpbe_mu * t75 / 0.12e2 + t149 + t152 / 0.36e2 - 0.11e2 / 0.72e2 * t68 * t69 * s0 / t41 / t154 * t49 + t5 * t66 * t162 * t168 * t169 / t40 / t154 / t70 * t45 * t49 / 0.216e3)
  t181 = t85 ** 2
  t182 = 0.1e1 / t181
  t183 = t87 ** 2
  t187 = f.my_piecewise5(t14, 0, t10, 0, -t126)
  t191 = f.my_piecewise3(t84, 0, 0.4e1 / 0.9e1 * t182 * t183 + 0.4e1 / 0.3e1 * t85 * t187)
  t198 = t5 * t90 * t61 * t104
  t203 = t5 * t109 * t145 * t104 / 0.12e2
  t205 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t191 * t30 * t104 - t198 / 0.4e1 + t203)
  d11 = 0.2e1 * t79 + 0.2e1 * t115 + t6 * (t180 + t205)
  t208 = -t7 - t24
  t209 = f.my_piecewise5(t10, 0, t14, 0, t208)
  t212 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t209)
  t213 = t212 * t30
  t218 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t213 * t52 - t65)
  t220 = f.my_piecewise5(t14, 0, t10, 0, -t208)
  t223 = f.my_piecewise3(t84, 0, 0.4e1 / 0.3e1 * t85 * t220)
  t224 = t223 * t30
  t228 = t109 * t30
  t230 = t5 * t228 * params.rpbe_mu
  t231 = t92 * r1
  t236 = t69 * s2 / t94 / t231 * t101
  t240 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t224 * t104 - t113 + t230 * t236 / 0.24e2)
  t244 = 0.2e1 * t124
  t245 = f.my_piecewise5(t10, 0, t14, 0, t244)
  t249 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t118 * t209 * t26 + 0.4e1 / 0.3e1 * t21 * t245)
  t256 = t5 * t212 * t61 * t52
  t265 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t249 * t30 * t52 - t256 / 0.8e1 + t5 * t213 * params.rpbe_mu * t75 / 0.24e2 - t138 / 0.8e1 + t149 + t152 / 0.72e2)
  t269 = f.my_piecewise5(t14, 0, t10, 0, -t244)
  t273 = f.my_piecewise3(t84, 0, 0.4e1 / 0.9e1 * t182 * t220 * t87 + 0.4e1 / 0.3e1 * t85 * t269)
  t280 = t5 * t223 * t61 * t104
  t289 = t5 * t110 * params.rpbe_mu * t236
  t292 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t273 * t30 * t104 - t280 / 0.8e1 - t198 / 0.8e1 + t203 + t5 * t91 * params.rpbe_mu * t236 / 0.24e2 + t289 / 0.72e2)
  d12 = t79 + t115 + t218 + t240 + t6 * (t265 + t292)
  t297 = t209 ** 2
  t301 = 0.2e1 * t23 + 0.2e1 * t124
  t302 = f.my_piecewise5(t10, 0, t14, 0, t301)
  t306 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t118 * t297 + 0.4e1 / 0.3e1 * t21 * t302)
  t313 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t306 * t30 * t52 - t256 / 0.4e1 + t149)
  t314 = t220 ** 2
  t318 = f.my_piecewise5(t14, 0, t10, 0, -t301)
  t322 = f.my_piecewise3(t84, 0, 0.4e1 / 0.9e1 * t182 * t314 + 0.4e1 / 0.3e1 * t85 * t318)
  t333 = t92 ** 2
  t343 = s2 ** 2
  t354 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t322 * t30 * t104 - t280 / 0.4e1 + t5 * t224 * params.rpbe_mu * t236 / 0.12e2 + t203 + t289 / 0.36e2 - 0.11e2 / 0.72e2 * t230 * t69 * s2 / t94 / t333 * t101 + t5 * t228 * t162 * t168 * t343 / t93 / t333 / t231 * t45 * t101 / 0.216e3)
  d22 = 0.2e1 * t218 + 0.2e1 * t240 + t6 * (t313 + t354)
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
  t44 = 6 ** (0.1e1 / 0.3e1)
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t50 = params.rpbe_mu * t44 * t49
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t57 = 0.1e1 / params.rpbe_kappa
  t61 = jnp.exp(-t50 * s0 / t53 / t51 * t57 / 0.24e2)
  t64 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t61)
  t70 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t71 = t42 ** 2
  t72 = 0.1e1 / t71
  t73 = t70 * t72
  t77 = t70 * t42
  t79 = t5 * t77 * params.rpbe_mu
  t80 = t44 * t49
  t81 = t51 * r0
  t86 = t80 * s0 / t53 / t81 * t61
  t89 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t90 = t89 * f.p.zeta_threshold
  t92 = f.my_piecewise3(t20, t90, t21 * t19)
  t94 = 0.1e1 / t71 / t6
  t95 = t92 * t94
  t99 = t92 * t72
  t101 = t5 * t99 * params.rpbe_mu
  t104 = t92 * t42
  t106 = t5 * t104 * params.rpbe_mu
  t107 = t51 ** 2
  t112 = t80 * s0 / t53 / t107 * t61
  t115 = params.rpbe_mu ** 2
  t117 = t5 * t104 * t115
  t118 = t44 ** 2
  t122 = s0 ** 2
  t123 = t118 / t47 / t46 * t122
  t129 = t123 / t52 / t107 / t81 * t57 * t61
  t133 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t64 - t5 * t73 * t64 / 0.4e1 + t79 * t86 / 0.12e2 + t5 * t95 * t64 / 0.12e2 + t101 * t86 / 0.36e2 - 0.11e2 / 0.72e2 * t106 * t112 + t117 * t129 / 0.216e3)
  t135 = r1 <= f.p.dens_threshold
  t136 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t137 = 0.1e1 + t136
  t138 = t137 <= f.p.zeta_threshold
  t139 = t137 ** (0.1e1 / 0.3e1)
  t140 = t139 ** 2
  t141 = 0.1e1 / t140
  t143 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t144 = t143 ** 2
  t148 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t152 = f.my_piecewise3(t138, 0, 0.4e1 / 0.9e1 * t141 * t144 + 0.4e1 / 0.3e1 * t139 * t148)
  t154 = r1 ** 2
  t155 = r1 ** (0.1e1 / 0.3e1)
  t156 = t155 ** 2
  t163 = jnp.exp(-t50 * s2 / t156 / t154 * t57 / 0.24e2)
  t166 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t163)
  t172 = f.my_piecewise3(t138, 0, 0.4e1 / 0.3e1 * t139 * t143)
  t178 = f.my_piecewise3(t138, t90, t139 * t137)
  t184 = f.my_piecewise3(t135, 0, -0.3e1 / 0.8e1 * t5 * t152 * t42 * t166 - t5 * t172 * t72 * t166 / 0.4e1 + t5 * t178 * t94 * t166 / 0.12e2)
  t200 = t107 ** 2
  t228 = t24 ** 2
  t232 = 0.6e1 * t33 - 0.6e1 * t16 / t228
  t233 = f.my_piecewise5(t10, 0, t14, 0, t232)
  t237 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t233)
  t251 = 0.1e1 / t71 / t24
  t256 = t46 ** 2
  t266 = params.rpbe_kappa ** 2
  t279 = -0.11e2 / 0.72e2 * t101 * t112 + t5 * t99 * t115 * t129 / 0.216e3 + 0.77e2 / 0.108e3 * t106 * t80 * s0 / t53 / t107 / r0 * t61 - 0.11e2 / 0.216e3 * t117 * t123 / t52 / t200 * t57 * t61 - t5 * t95 * params.rpbe_mu * t86 / 0.36e2 + t5 * t43 * params.rpbe_mu * t86 / 0.8e1 + t5 * t73 * params.rpbe_mu * t86 / 0.12e2 - 0.3e1 / 0.8e1 * t5 * t237 * t42 * t64 - 0.3e1 / 0.8e1 * t5 * t41 * t72 * t64 + t5 * t70 * t94 * t64 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t92 * t251 * t64 + t2 / t3 / t256 * t104 * t115 * params.rpbe_mu * t122 * s0 / t200 / t81 / t266 * t61 / 0.324e3 - 0.11e2 / 0.24e2 * t79 * t112 + t5 * t77 * t115 * t129 / 0.72e2
  t280 = f.my_piecewise3(t1, 0, t279)
  t290 = f.my_piecewise5(t14, 0, t10, 0, -t232)
  t294 = f.my_piecewise3(t138, 0, -0.8e1 / 0.27e2 / t140 / t137 * t144 * t143 + 0.4e1 / 0.3e1 * t141 * t143 * t148 + 0.4e1 / 0.3e1 * t139 * t290)
  t312 = f.my_piecewise3(t135, 0, -0.3e1 / 0.8e1 * t5 * t294 * t42 * t166 - 0.3e1 / 0.8e1 * t5 * t152 * t72 * t166 + t5 * t172 * t94 * t166 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t178 * t251 * t166)
  d111 = 0.3e1 * t133 + 0.3e1 * t184 + t6 * (t280 + t312)

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
  t22 = t6 ** 2
  t23 = 0.1e1 / t22
  t25 = -t16 * t23 + t7
  t26 = f.my_piecewise5(t10, 0, t14, 0, t25)
  t29 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t26)
  t30 = t6 ** (0.1e1 / 0.3e1)
  t31 = t29 * t30
  t32 = params.rpbe_mu ** 2
  t34 = t5 * t31 * t32
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t42 = s0 ** 2
  t43 = t36 / t38 / t37 * t42
  t44 = r0 ** 2
  t45 = t44 * r0
  t46 = t44 ** 2
  t48 = r0 ** (0.1e1 / 0.3e1)
  t51 = 0.1e1 / params.rpbe_kappa
  t54 = t38 ** 2
  t55 = 0.1e1 / t54
  t56 = params.rpbe_mu * t35 * t55
  t57 = t48 ** 2
  t64 = jnp.exp(-t56 * s0 / t57 / t44 * t51 / 0.24e2)
  t66 = t43 / t48 / t46 / t45 * t51 * t64
  t69 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t70 = t69 * f.p.zeta_threshold
  t72 = f.my_piecewise3(t20, t70, t21 * t19)
  t73 = t30 ** 2
  t74 = 0.1e1 / t73
  t75 = t72 * t74
  t77 = t5 * t75 * params.rpbe_mu
  t78 = t35 * t55
  t83 = t78 * s0 / t57 / t46 * t64
  t87 = t5 * t75 * t32
  t90 = t72 * t30
  t92 = t5 * t90 * params.rpbe_mu
  t98 = t78 * s0 / t57 / t46 / r0 * t64
  t102 = t5 * t90 * t32
  t103 = t46 ** 2
  t108 = t43 / t48 / t103 * t51 * t64
  t112 = 0.1e1 / t73 / t6
  t113 = t72 * t112
  t115 = t5 * t113 * params.rpbe_mu
  t120 = t78 * s0 / t57 / t45 * t64
  t123 = t21 ** 2
  t124 = 0.1e1 / t123
  t125 = t26 ** 2
  t128 = t22 * t6
  t129 = 0.1e1 / t128
  t132 = 0.2e1 * t16 * t129 - 0.2e1 * t23
  t133 = f.my_piecewise5(t10, 0, t14, 0, t132)
  t137 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t124 * t125 + 0.4e1 / 0.3e1 * t21 * t133)
  t138 = t137 * t30
  t140 = t5 * t138 * params.rpbe_mu
  t143 = t29 * t74
  t145 = t5 * t143 * params.rpbe_mu
  t149 = 0.1e1 / t123 / t19
  t153 = t124 * t26
  t156 = t22 ** 2
  t157 = 0.1e1 / t156
  t160 = -0.6e1 * t16 * t157 + 0.6e1 * t129
  t161 = f.my_piecewise5(t10, 0, t14, 0, t160)
  t165 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t149 * t125 * t26 + 0.4e1 / 0.3e1 * t153 * t133 + 0.4e1 / 0.3e1 * t21 * t161)
  t166 = t165 * t30
  t169 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t64)
  t173 = t137 * t74
  t177 = t29 * t112
  t182 = 0.1e1 / t73 / t22
  t183 = t72 * t182
  t187 = t37 ** 2
  t190 = t2 / t3 / t187
  t191 = t190 * t90
  t194 = t32 * params.rpbe_mu * t42 * s0
  t197 = params.rpbe_kappa ** 2
  t198 = 0.1e1 / t197
  t201 = t194 / t103 / t45 * t198 * t64
  t205 = t5 * t31 * params.rpbe_mu
  t208 = t34 * t66 / 0.72e2 - 0.11e2 / 0.72e2 * t77 * t83 + t87 * t66 / 0.216e3 + 0.77e2 / 0.108e3 * t92 * t98 - 0.11e2 / 0.216e3 * t102 * t108 - t115 * t120 / 0.36e2 + t140 * t120 / 0.8e1 + t145 * t120 / 0.12e2 - 0.3e1 / 0.8e1 * t5 * t166 * t169 - 0.3e1 / 0.8e1 * t5 * t173 * t169 + t5 * t177 * t169 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t183 * t169 + t191 * t201 / 0.324e3 - 0.11e2 / 0.24e2 * t205 * t83
  t209 = f.my_piecewise3(t1, 0, t208)
  t211 = r1 <= f.p.dens_threshold
  t212 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t213 = 0.1e1 + t212
  t214 = t213 <= f.p.zeta_threshold
  t215 = t213 ** (0.1e1 / 0.3e1)
  t216 = t215 ** 2
  t218 = 0.1e1 / t216 / t213
  t220 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t221 = t220 ** 2
  t225 = 0.1e1 / t216
  t226 = t225 * t220
  t228 = f.my_piecewise5(t14, 0, t10, 0, -t132)
  t232 = f.my_piecewise5(t14, 0, t10, 0, -t160)
  t236 = f.my_piecewise3(t214, 0, -0.8e1 / 0.27e2 * t218 * t221 * t220 + 0.4e1 / 0.3e1 * t226 * t228 + 0.4e1 / 0.3e1 * t215 * t232)
  t238 = r1 ** 2
  t239 = r1 ** (0.1e1 / 0.3e1)
  t240 = t239 ** 2
  t247 = jnp.exp(-t56 * s2 / t240 / t238 * t51 / 0.24e2)
  t250 = 0.1e1 + params.rpbe_kappa * (0.1e1 - t247)
  t259 = f.my_piecewise3(t214, 0, 0.4e1 / 0.9e1 * t225 * t221 + 0.4e1 / 0.3e1 * t215 * t228)
  t266 = f.my_piecewise3(t214, 0, 0.4e1 / 0.3e1 * t215 * t220)
  t272 = f.my_piecewise3(t214, t70, t215 * t213)
  t278 = f.my_piecewise3(t211, 0, -0.3e1 / 0.8e1 * t5 * t236 * t30 * t250 - 0.3e1 / 0.8e1 * t5 * t259 * t74 * t250 + t5 * t266 * t112 * t250 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t272 * t182 * t250)
  t280 = t19 ** 2
  t283 = t125 ** 2
  t289 = t133 ** 2
  t298 = -0.24e2 * t157 + 0.24e2 * t16 / t156 / t6
  t299 = f.my_piecewise5(t10, 0, t14, 0, t298)
  t303 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t123 / t280 * t283 - 0.16e2 / 0.9e1 * t149 * t125 * t133 + 0.4e1 / 0.3e1 * t124 * t289 + 0.16e2 / 0.9e1 * t153 * t161 + 0.4e1 / 0.3e1 * t21 * t299)
  t321 = 0.1e1 / t73 / t128
  t326 = t32 ** 2
  t329 = t42 ** 2
  t330 = t46 * t44
  t366 = -0.3e1 / 0.8e1 * t5 * t303 * t30 * t169 - t5 * t165 * t74 * t169 / 0.2e1 + t5 * t137 * t112 * t169 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t29 * t182 * t169 + 0.10e2 / 0.27e2 * t5 * t72 * t321 * t169 + t190 * t90 * t326 * t329 / t57 / t103 / t330 / t197 / params.rpbe_kappa * t78 * t64 / 0.2916e4 + 0.979e3 / 0.1944e4 * t102 * t43 / t48 / t103 / r0 * t51 * t64 + t5 * t138 * t32 * t66 / 0.36e2 - 0.11e2 / 0.162e3 * t87 * t108 - 0.11e2 / 0.54e2 * t34 * t108 - t5 * t113 * t32 * t66 / 0.162e3 + t5 * t143 * t32 * t66 / 0.54e2
  t413 = 0.5e1 / 0.81e2 * t5 * t183 * params.rpbe_mu * t120 + t5 * t173 * params.rpbe_mu * t120 / 0.6e1 + 0.11e2 / 0.54e2 * t115 * t83 + 0.77e2 / 0.81e2 * t77 * t98 - 0.11e2 / 0.18e2 * t145 * t83 + 0.77e2 / 0.27e2 * t205 * t98 - t5 * t177 * params.rpbe_mu * t120 / 0.9e1 + t5 * t166 * params.rpbe_mu * t120 / 0.6e1 - 0.11e2 / 0.12e2 * t140 * t83 - 0.1309e4 / 0.324e3 * t92 * t78 * s0 / t57 / t330 * t64 + t190 * t31 * t201 / 0.81e2 + t190 * t75 * t201 / 0.243e3 - 0.11e2 / 0.162e3 * t191 * t194 / t103 / t46 * t198 * t64
  t415 = f.my_piecewise3(t1, 0, t366 + t413)
  t416 = t213 ** 2
  t419 = t221 ** 2
  t425 = t228 ** 2
  t431 = f.my_piecewise5(t14, 0, t10, 0, -t298)
  t435 = f.my_piecewise3(t214, 0, 0.40e2 / 0.81e2 / t216 / t416 * t419 - 0.16e2 / 0.9e1 * t218 * t221 * t228 + 0.4e1 / 0.3e1 * t225 * t425 + 0.16e2 / 0.9e1 * t226 * t232 + 0.4e1 / 0.3e1 * t215 * t431)
  t457 = f.my_piecewise3(t211, 0, -0.3e1 / 0.8e1 * t5 * t435 * t30 * t250 - t5 * t236 * t74 * t250 / 0.2e1 + t5 * t259 * t112 * t250 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t266 * t182 * t250 + 0.10e2 / 0.27e2 * t5 * t272 * t321 * t250)
  d1111 = 0.4e1 * t209 + 0.4e1 * t278 + t6 * (t415 + t457)

  res = {'v4rho4': d1111}
  return res
