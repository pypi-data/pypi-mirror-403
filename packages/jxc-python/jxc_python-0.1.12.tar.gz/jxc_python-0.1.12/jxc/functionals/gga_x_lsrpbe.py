"""Generated from gga_x_lsrpbe.mpl."""

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

  lsrpbe_f0 = lambda s: 1 + params_kappa * (1 - jnp.exp(-params_mu * s ** 2 / params_kappa)) - (params_kappa + 1) * (1 - jnp.exp(-params_alpha * s ** 2))

  lsrpbe_f = lambda x: lsrpbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, lsrpbe_f, rs, z, xs0, xs1)

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

  lsrpbe_f0 = lambda s: 1 + params_kappa * (1 - jnp.exp(-params_mu * s ** 2 / params_kappa)) - (params_kappa + 1) * (1 - jnp.exp(-params_alpha * s ** 2))

  lsrpbe_f = lambda x: lsrpbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, lsrpbe_f, rs, z, xs0, xs1)

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

  lsrpbe_f0 = lambda s: 1 + params_kappa * (1 - jnp.exp(-params_mu * s ** 2 / params_kappa)) - (params_kappa + 1) * (1 - jnp.exp(-params_alpha * s ** 2))

  lsrpbe_f = lambda x: lsrpbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, lsrpbe_f, rs, z, xs0, xs1)

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
  t29 = params.mu * t28
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = t29 * t33
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t41 = 0.1e1 / params.kappa
  t45 = jnp.exp(-t34 * s0 * t39 * t41 / 0.24e2)
  t48 = params.kappa + 0.1e1
  t49 = params.alpha * t28
  t50 = t33 * s0
  t54 = jnp.exp(-t49 * t50 * t39 / 0.24e2)
  t57 = 0.1e1 + params.kappa * (0.1e1 - t45) - t48 * (0.1e1 - t54)
  t61 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t57)
  t62 = r1 <= f.p.dens_threshold
  t63 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t64 = 0.1e1 + t63
  t65 = t64 <= f.p.zeta_threshold
  t66 = t64 ** (0.1e1 / 0.3e1)
  t68 = f.my_piecewise3(t65, t22, t66 * t64)
  t69 = t68 * t26
  t70 = r1 ** 2
  t71 = r1 ** (0.1e1 / 0.3e1)
  t72 = t71 ** 2
  t74 = 0.1e1 / t72 / t70
  t79 = jnp.exp(-t34 * s2 * t74 * t41 / 0.24e2)
  t82 = t33 * s2
  t86 = jnp.exp(-t49 * t82 * t74 / 0.24e2)
  t89 = 0.1e1 + params.kappa * (0.1e1 - t79) - t48 * (0.1e1 - t86)
  t93 = f.my_piecewise3(t62, 0, -0.3e1 / 0.8e1 * t5 * t69 * t89)
  t94 = t6 ** 2
  t96 = t16 / t94
  t97 = t7 - t96
  t98 = f.my_piecewise5(t10, 0, t14, 0, t97)
  t101 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t98)
  t106 = t26 ** 2
  t107 = 0.1e1 / t106
  t111 = t5 * t25 * t107 * t57 / 0.8e1
  t114 = 0.1e1 / t37 / t35 / r0
  t119 = t48 * params.alpha * t28
  t129 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t101 * t26 * t57 - t111 - 0.3e1 / 0.8e1 * t5 * t27 * (-t34 * s0 * t114 * t45 / 0.9e1 + t119 * t50 * t114 * t54 / 0.9e1))
  t131 = f.my_piecewise5(t14, 0, t10, 0, -t97)
  t134 = f.my_piecewise3(t65, 0, 0.4e1 / 0.3e1 * t66 * t131)
  t142 = t5 * t68 * t107 * t89 / 0.8e1
  t144 = f.my_piecewise3(t62, 0, -0.3e1 / 0.8e1 * t5 * t134 * t26 * t89 - t142)
  vrho_0_ = t61 + t93 + t6 * (t129 + t144)
  t147 = -t7 - t96
  t148 = f.my_piecewise5(t10, 0, t14, 0, t147)
  t151 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t148)
  t157 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t151 * t26 * t57 - t111)
  t159 = f.my_piecewise5(t14, 0, t10, 0, -t147)
  t162 = f.my_piecewise3(t65, 0, 0.4e1 / 0.3e1 * t66 * t159)
  t169 = 0.1e1 / t72 / t70 / r1
  t182 = f.my_piecewise3(t62, 0, -0.3e1 / 0.8e1 * t5 * t162 * t26 * t89 - t142 - 0.3e1 / 0.8e1 * t5 * t69 * (-t34 * s2 * t169 * t79 / 0.9e1 + t119 * t82 * t169 * t86 / 0.9e1))
  vrho_1_ = t61 + t93 + t6 * (t157 + t182)
  t185 = t33 * t39
  t195 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-t119 * t185 * t54 / 0.24e2 + t29 * t185 * t45 / 0.24e2))
  vsigma_0_ = t6 * t195
  vsigma_1_ = 0.0e0
  t196 = t33 * t74
  t206 = f.my_piecewise3(t62, 0, -0.3e1 / 0.8e1 * t5 * t69 * (-t119 * t196 * t86 / 0.24e2 + t29 * t196 * t79 / 0.24e2))
  vsigma_2_ = t6 * t206
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

  lsrpbe_f0 = lambda s: 1 + params_kappa * (1 - jnp.exp(-params_mu * s ** 2 / params_kappa)) - (params_kappa + 1) * (1 - jnp.exp(-params_alpha * s ** 2))

  lsrpbe_f = lambda x: lsrpbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, lsrpbe_f, rs, z, xs0, xs1)

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
  t20 = 6 ** (0.1e1 / 0.3e1)
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t26 = params.mu * t20 * t25
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t18 ** 2
  t33 = 0.1e1 / t31 / t30
  t39 = jnp.exp(-t26 * t29 * t33 / params.kappa / 0.24e2)
  t42 = params.kappa + 0.1e1
  t48 = jnp.exp(-params.alpha * t20 * t25 * t29 * t33 / 0.24e2)
  t51 = 0.1e1 + params.kappa * (0.1e1 - t39) - t42 * (0.1e1 - t48)
  t55 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t51)
  t63 = 0.1e1 / t31 / t30 / r0
  t67 = t42 * params.alpha
  t79 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t51 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (t67 * t20 * t25 * t29 * t63 * t48 / 0.9e1 - t26 * t29 * t63 * t39 / 0.9e1))
  vrho_0_ = 0.2e1 * r0 * t79 + 0.2e1 * t55
  t95 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-t67 * t20 * t25 * t28 * t33 * t48 / 0.24e2 + t26 * t28 * t33 * t39 / 0.24e2))
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
  t21 = t17 / t19
  t22 = 6 ** (0.1e1 / 0.3e1)
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = params.mu * t22 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t35 = 0.1e1 / params.kappa
  t40 = jnp.exp(-t28 * t31 * t34 * t35 / 0.24e2)
  t43 = params.kappa + 0.1e1
  t49 = jnp.exp(-params.alpha * t22 * t27 * t31 * t34 / 0.24e2)
  t52 = 0.1e1 + params.kappa * (0.1e1 - t40) - t43 * (0.1e1 - t49)
  t56 = t17 * t18
  t57 = t32 * r0
  t59 = 0.1e1 / t19 / t57
  t63 = t43 * params.alpha
  t65 = t63 * t22 * t27
  t66 = t59 * t49
  t70 = -t28 * t31 * t59 * t40 / 0.9e1 + t65 * t31 * t66 / 0.9e1
  t75 = f.my_piecewise3(t2, 0, -t6 * t21 * t52 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t56 * t70)
  t86 = t32 ** 2
  t88 = 0.1e1 / t19 / t86
  t93 = params.mu ** 2
  t94 = t22 ** 2
  t95 = t93 * t94
  t97 = 0.1e1 / t25 / t24
  t98 = s0 ** 2
  t103 = 0.1e1 / t18 / t86 / t57
  t105 = t35 * t40
  t113 = params.alpha ** 2
  t114 = t43 * t113
  t116 = t114 * t94 * t97
  t127 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t52 / 0.12e2 - t6 * t21 * t70 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t56 * (0.11e2 / 0.27e2 * t28 * t31 * t88 * t40 - 0.2e1 / 0.81e2 * t95 * t97 * t98 * t29 * t103 * t105 - 0.11e2 / 0.27e2 * t65 * t31 * t88 * t49 + 0.2e1 / 0.81e2 * t116 * t98 * t29 * t103 * t49))
  v2rho2_0_ = 0.2e1 * r0 * t127 + 0.4e1 * t75
  t133 = t63 * t22
  t134 = t27 * t30
  t139 = -t133 * t134 * t34 * t49 / 0.24e2 + t28 * t30 * t34 * t40 / 0.24e2
  t143 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t56 * t139)
  t151 = t97 * t29
  t155 = 0.1e1 / t18 / t86 / t32
  t173 = f.my_piecewise3(t2, 0, -t6 * t21 * t139 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t56 * (-t28 * t30 * t59 * t40 / 0.9e1 + t95 * t151 * t155 * s0 * t105 / 0.108e3 + t133 * t134 * t66 / 0.9e1 - t116 * t29 * t155 * s0 * t49 / 0.108e3))
  v2rhosigma_0_ = 0.2e1 * r0 * t173 + 0.2e1 * t143
  t179 = 0.1e1 / t18 / t86 / r0
  t192 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t56 * (-t95 * t97 * t29 * t179 * t105 / 0.288e3 + t114 * t94 * t151 * t179 * t49 / 0.288e3))
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
  t22 = t17 / t19 / r0
  t23 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = params.mu * t23 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t36 = 0.1e1 / params.kappa
  t41 = jnp.exp(-t29 * t32 * t35 * t36 / 0.24e2)
  t44 = params.kappa + 0.1e1
  t50 = jnp.exp(-params.alpha * t23 * t28 * t32 * t35 / 0.24e2)
  t53 = 0.1e1 + params.kappa * (0.1e1 - t41) - t44 * (0.1e1 - t50)
  t58 = t17 / t19
  t59 = t33 * r0
  t61 = 0.1e1 / t19 / t59
  t67 = t44 * params.alpha * t23 * t28
  t72 = -t29 * t32 * t61 * t41 / 0.9e1 + t67 * t32 * t61 * t50 / 0.9e1
  t76 = t17 * t18
  t77 = t33 ** 2
  t79 = 0.1e1 / t19 / t77
  t84 = params.mu ** 2
  t85 = t23 ** 2
  t88 = 0.1e1 / t26 / t25
  t89 = s0 ** 2
  t91 = t84 * t85 * t88 * t89
  t94 = 0.1e1 / t18 / t77 / t59
  t96 = t36 * t41
  t104 = params.alpha ** 2
  t107 = t44 * t104 * t85 * t88
  t108 = t89 * t30
  t113 = 0.11e2 / 0.27e2 * t29 * t32 * t79 * t41 - 0.2e1 / 0.81e2 * t91 * t30 * t94 * t96 - 0.11e2 / 0.27e2 * t67 * t32 * t79 * t50 + 0.2e1 / 0.81e2 * t107 * t108 * t94 * t50
  t118 = f.my_piecewise3(t2, 0, t6 * t22 * t53 / 0.12e2 - t6 * t58 * t72 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t76 * t113)
  t132 = 0.1e1 / t19 / t77 / r0
  t137 = t77 ** 2
  t139 = 0.1e1 / t18 / t137
  t145 = t25 ** 2
  t146 = 0.1e1 / t145
  t148 = t89 * s0
  t151 = 0.1e1 / t137 / t59
  t152 = params.kappa ** 2
  t178 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t53 + t6 * t22 * t72 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t58 * t113 - 0.3e1 / 0.8e1 * t6 * t76 * (-0.154e3 / 0.81e2 * t29 * t32 * t132 * t41 + 0.22e2 / 0.81e2 * t91 * t30 * t139 * t96 - 0.8e1 / 0.243e3 * t84 * params.mu * t146 * t148 * t151 / t152 * t41 + 0.154e3 / 0.81e2 * t67 * t32 * t132 * t50 - 0.22e2 / 0.81e2 * t107 * t108 * t139 * t50 + 0.8e1 / 0.243e3 * t44 * t104 * params.alpha * t146 * t148 * t151 * t50))
  v3rho3_0_ = 0.2e1 * r0 * t178 + 0.6e1 * t118

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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = params.mu * t24 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = 0.1e1 / params.kappa
  t39 = jnp.exp(-t30 * t33 * t22 * t34 / 0.24e2)
  t42 = params.kappa + 0.1e1
  t48 = jnp.exp(-params.alpha * t24 * t29 * t33 * t22 / 0.24e2)
  t51 = 0.1e1 + params.kappa * (0.1e1 - t39) - t42 * (0.1e1 - t48)
  t57 = t17 / t20 / r0
  t58 = t18 * r0
  t60 = 0.1e1 / t20 / t58
  t66 = t42 * params.alpha * t24 * t29
  t71 = -t30 * t33 * t60 * t39 / 0.9e1 + t66 * t33 * t60 * t48 / 0.9e1
  t76 = t17 / t20
  t77 = t18 ** 2
  t79 = 0.1e1 / t20 / t77
  t84 = params.mu ** 2
  t85 = t24 ** 2
  t88 = 0.1e1 / t27 / t26
  t89 = s0 ** 2
  t91 = t84 * t85 * t88 * t89
  t94 = 0.1e1 / t19 / t77 / t58
  t96 = t34 * t39
  t104 = params.alpha ** 2
  t107 = t42 * t104 * t85 * t88
  t108 = t89 * t31
  t113 = 0.11e2 / 0.27e2 * t30 * t33 * t79 * t39 - 0.2e1 / 0.81e2 * t91 * t31 * t94 * t96 - 0.11e2 / 0.27e2 * t66 * t33 * t79 * t48 + 0.2e1 / 0.81e2 * t107 * t108 * t94 * t48
  t117 = t17 * t19
  t120 = 0.1e1 / t20 / t77 / r0
  t125 = t77 ** 2
  t127 = 0.1e1 / t19 / t125
  t133 = t26 ** 2
  t134 = 0.1e1 / t133
  t136 = t89 * s0
  t137 = t84 * params.mu * t134 * t136
  t139 = 0.1e1 / t125 / t58
  t140 = params.kappa ** 2
  t141 = 0.1e1 / t140
  t156 = t42 * t104 * params.alpha * t134
  t161 = -0.154e3 / 0.81e2 * t30 * t33 * t120 * t39 + 0.22e2 / 0.81e2 * t91 * t31 * t127 * t96 - 0.8e1 / 0.243e3 * t137 * t139 * t141 * t39 + 0.154e3 / 0.81e2 * t66 * t33 * t120 * t48 - 0.22e2 / 0.81e2 * t107 * t108 * t127 * t48 + 0.8e1 / 0.243e3 * t156 * t136 * t139 * t48
  t166 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t51 + t6 * t57 * t71 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t76 * t113 - 0.3e1 / 0.8e1 * t6 * t117 * t161)
  t181 = t77 * t18
  t183 = 0.1e1 / t20 / t181
  t190 = 0.1e1 / t19 / t125 / r0
  t196 = 0.1e1 / t125 / t77
  t201 = t84 ** 2
  t203 = t89 ** 2
  t206 = 0.1e1 / t20 / t125 / t181
  t212 = t29 * t32
  t229 = t104 ** 2
  t243 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t60 * t51 - 0.5e1 / 0.9e1 * t6 * t23 * t71 + t6 * t57 * t113 / 0.2e1 - t6 * t76 * t161 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t117 * (0.2618e4 / 0.243e3 * t30 * t33 * t183 * t39 - 0.1958e4 / 0.729e3 * t91 * t31 * t190 * t96 + 0.176e3 / 0.243e3 * t137 * t196 * t141 * t39 - 0.8e1 / 0.2187e4 * t201 * t134 * t203 * t206 / t140 / params.kappa * t24 * t212 * t39 - 0.2618e4 / 0.243e3 * t66 * t33 * t183 * t48 + 0.1958e4 / 0.729e3 * t107 * t108 * t190 * t48 - 0.176e3 / 0.243e3 * t156 * t136 * t196 * t48 + 0.8e1 / 0.2187e4 * t42 * t229 * t134 * t203 * t206 * t24 * t212 * t48))
  v4rho4_0_ = 0.2e1 * r0 * t243 + 0.8e1 * t166

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
  t38 = params.mu * t32 * t37
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t45 = 0.1e1 / params.kappa
  t49 = jnp.exp(-t38 * s0 * t43 * t45 / 0.24e2)
  t52 = params.kappa + 0.1e1
  t53 = params.alpha * t32
  t54 = t37 * s0
  t58 = jnp.exp(-t53 * t54 * t43 / 0.24e2)
  t61 = 0.1e1 + params.kappa * (0.1e1 - t49) - t52 * (0.1e1 - t58)
  t65 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t66 = t65 * f.p.zeta_threshold
  t68 = f.my_piecewise3(t20, t66, t21 * t19)
  t69 = t30 ** 2
  t70 = 0.1e1 / t69
  t71 = t68 * t70
  t74 = t5 * t71 * t61 / 0.8e1
  t75 = t68 * t30
  t76 = t39 * r0
  t78 = 0.1e1 / t41 / t76
  t83 = t52 * params.alpha * t32
  t88 = -t38 * s0 * t78 * t49 / 0.9e1 + t83 * t54 * t78 * t58 / 0.9e1
  t93 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t61 - t74 - 0.3e1 / 0.8e1 * t5 * t75 * t88)
  t95 = r1 <= f.p.dens_threshold
  t96 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t97 = 0.1e1 + t96
  t98 = t97 <= f.p.zeta_threshold
  t99 = t97 ** (0.1e1 / 0.3e1)
  t101 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t104 = f.my_piecewise3(t98, 0, 0.4e1 / 0.3e1 * t99 * t101)
  t105 = t104 * t30
  t106 = r1 ** 2
  t107 = r1 ** (0.1e1 / 0.3e1)
  t108 = t107 ** 2
  t110 = 0.1e1 / t108 / t106
  t115 = jnp.exp(-t38 * s2 * t110 * t45 / 0.24e2)
  t118 = t37 * s2
  t122 = jnp.exp(-t53 * t118 * t110 / 0.24e2)
  t125 = 0.1e1 + params.kappa * (0.1e1 - t115) - t52 * (0.1e1 - t122)
  t130 = f.my_piecewise3(t98, t66, t99 * t97)
  t131 = t130 * t70
  t134 = t5 * t131 * t125 / 0.8e1
  t136 = f.my_piecewise3(t95, 0, -0.3e1 / 0.8e1 * t5 * t105 * t125 - t134)
  t138 = t21 ** 2
  t139 = 0.1e1 / t138
  t140 = t26 ** 2
  t145 = t16 / t22 / t6
  t147 = -0.2e1 * t23 + 0.2e1 * t145
  t148 = f.my_piecewise5(t10, 0, t14, 0, t147)
  t152 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t139 * t140 + 0.4e1 / 0.3e1 * t21 * t148)
  t159 = t5 * t29 * t70 * t61
  t165 = 0.1e1 / t69 / t6
  t169 = t5 * t68 * t165 * t61 / 0.12e2
  t171 = t5 * t71 * t88
  t173 = t39 ** 2
  t175 = 0.1e1 / t41 / t173
  t180 = params.mu ** 2
  t181 = t32 ** 2
  t184 = 0.1e1 / t35 / t34
  t185 = t180 * t181 * t184
  t186 = s0 ** 2
  t189 = 0.1e1 / t40 / t173 / t76
  t199 = params.alpha ** 2
  t201 = t52 * t199 * t181
  t212 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t152 * t30 * t61 - t159 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t88 + t169 - t171 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t75 * (0.11e2 / 0.27e2 * t38 * s0 * t175 * t49 - t185 * t186 * t189 * t45 * t49 / 0.81e2 - 0.11e2 / 0.27e2 * t83 * t54 * t175 * t58 + t201 * t184 * t186 * t189 * t58 / 0.81e2))
  t213 = t99 ** 2
  t214 = 0.1e1 / t213
  t215 = t101 ** 2
  t219 = f.my_piecewise5(t14, 0, t10, 0, -t147)
  t223 = f.my_piecewise3(t98, 0, 0.4e1 / 0.9e1 * t214 * t215 + 0.4e1 / 0.3e1 * t99 * t219)
  t230 = t5 * t104 * t70 * t125
  t235 = t5 * t130 * t165 * t125 / 0.12e2
  t237 = f.my_piecewise3(t95, 0, -0.3e1 / 0.8e1 * t5 * t223 * t30 * t125 - t230 / 0.4e1 + t235)
  d11 = 0.2e1 * t93 + 0.2e1 * t136 + t6 * (t212 + t237)
  t240 = -t7 - t24
  t241 = f.my_piecewise5(t10, 0, t14, 0, t240)
  t244 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t241)
  t245 = t244 * t30
  t250 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t245 * t61 - t74)
  t252 = f.my_piecewise5(t14, 0, t10, 0, -t240)
  t255 = f.my_piecewise3(t98, 0, 0.4e1 / 0.3e1 * t99 * t252)
  t256 = t255 * t30
  t260 = t130 * t30
  t261 = t106 * r1
  t263 = 0.1e1 / t108 / t261
  t271 = -t38 * s2 * t263 * t115 / 0.9e1 + t83 * t118 * t263 * t122 / 0.9e1
  t276 = f.my_piecewise3(t95, 0, -0.3e1 / 0.8e1 * t5 * t256 * t125 - t134 - 0.3e1 / 0.8e1 * t5 * t260 * t271)
  t280 = 0.2e1 * t145
  t281 = f.my_piecewise5(t10, 0, t14, 0, t280)
  t285 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t139 * t241 * t26 + 0.4e1 / 0.3e1 * t21 * t281)
  t292 = t5 * t244 * t70 * t61
  t300 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t285 * t30 * t61 - t292 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t245 * t88 - t159 / 0.8e1 + t169 - t171 / 0.8e1)
  t304 = f.my_piecewise5(t14, 0, t10, 0, -t280)
  t308 = f.my_piecewise3(t98, 0, 0.4e1 / 0.9e1 * t214 * t252 * t101 + 0.4e1 / 0.3e1 * t99 * t304)
  t315 = t5 * t255 * t70 * t125
  t322 = t5 * t131 * t271
  t325 = f.my_piecewise3(t95, 0, -0.3e1 / 0.8e1 * t5 * t308 * t30 * t125 - t315 / 0.8e1 - t230 / 0.8e1 + t235 - 0.3e1 / 0.8e1 * t5 * t105 * t271 - t322 / 0.8e1)
  d12 = t93 + t136 + t250 + t276 + t6 * (t300 + t325)
  t330 = t241 ** 2
  t334 = 0.2e1 * t23 + 0.2e1 * t145
  t335 = f.my_piecewise5(t10, 0, t14, 0, t334)
  t339 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t139 * t330 + 0.4e1 / 0.3e1 * t21 * t335)
  t346 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t339 * t30 * t61 - t292 / 0.4e1 + t169)
  t347 = t252 ** 2
  t351 = f.my_piecewise5(t14, 0, t10, 0, -t334)
  t355 = f.my_piecewise3(t98, 0, 0.4e1 / 0.9e1 * t214 * t347 + 0.4e1 / 0.3e1 * t99 * t351)
  t365 = t106 ** 2
  t367 = 0.1e1 / t108 / t365
  t372 = s2 ** 2
  t375 = 0.1e1 / t107 / t365 / t261
  t395 = f.my_piecewise3(t95, 0, -0.3e1 / 0.8e1 * t5 * t355 * t30 * t125 - t315 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t256 * t271 + t235 - t322 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t260 * (0.11e2 / 0.27e2 * t38 * s2 * t367 * t115 - t185 * t372 * t375 * t45 * t115 / 0.81e2 - 0.11e2 / 0.27e2 * t83 * t118 * t367 * t122 + t201 * t184 * t372 * t375 * t122 / 0.81e2))
  d22 = 0.2e1 * t250 + 0.2e1 * t276 + t6 * (t346 + t395)
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
  t50 = params.mu * t44 * t49
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t55 = 0.1e1 / t53 / t51
  t57 = 0.1e1 / params.kappa
  t61 = jnp.exp(-t50 * s0 * t55 * t57 / 0.24e2)
  t64 = params.kappa + 0.1e1
  t65 = params.alpha * t44
  t66 = t49 * s0
  t70 = jnp.exp(-t65 * t66 * t55 / 0.24e2)
  t73 = 0.1e1 + params.kappa * (0.1e1 - t61) - t64 * (0.1e1 - t70)
  t79 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t80 = t42 ** 2
  t81 = 0.1e1 / t80
  t82 = t79 * t81
  t86 = t79 * t42
  t87 = t51 * r0
  t89 = 0.1e1 / t53 / t87
  t94 = t64 * params.alpha * t44
  t99 = -t50 * s0 * t89 * t61 / 0.9e1 + t94 * t66 * t89 * t70 / 0.9e1
  t103 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t104 = t103 * f.p.zeta_threshold
  t106 = f.my_piecewise3(t20, t104, t21 * t19)
  t108 = 0.1e1 / t80 / t6
  t109 = t106 * t108
  t113 = t106 * t81
  t117 = t106 * t42
  t118 = t51 ** 2
  t120 = 0.1e1 / t53 / t118
  t125 = params.mu ** 2
  t126 = t44 ** 2
  t129 = 0.1e1 / t47 / t46
  t130 = t125 * t126 * t129
  t131 = s0 ** 2
  t134 = 0.1e1 / t52 / t118 / t87
  t136 = t57 * t61
  t144 = params.alpha ** 2
  t146 = t64 * t144 * t126
  t147 = t129 * t131
  t152 = 0.11e2 / 0.27e2 * t50 * s0 * t120 * t61 - t130 * t131 * t134 * t136 / 0.81e2 - 0.11e2 / 0.27e2 * t94 * t66 * t120 * t70 + t146 * t147 * t134 * t70 / 0.81e2
  t157 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t73 - t5 * t82 * t73 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t86 * t99 + t5 * t109 * t73 / 0.12e2 - t5 * t113 * t99 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t117 * t152)
  t159 = r1 <= f.p.dens_threshold
  t160 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t161 = 0.1e1 + t160
  t162 = t161 <= f.p.zeta_threshold
  t163 = t161 ** (0.1e1 / 0.3e1)
  t164 = t163 ** 2
  t165 = 0.1e1 / t164
  t167 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t168 = t167 ** 2
  t172 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t176 = f.my_piecewise3(t162, 0, 0.4e1 / 0.9e1 * t165 * t168 + 0.4e1 / 0.3e1 * t163 * t172)
  t178 = r1 ** 2
  t179 = r1 ** (0.1e1 / 0.3e1)
  t180 = t179 ** 2
  t182 = 0.1e1 / t180 / t178
  t187 = jnp.exp(-t50 * s2 * t182 * t57 / 0.24e2)
  t194 = jnp.exp(-t65 * t49 * s2 * t182 / 0.24e2)
  t197 = 0.1e1 + params.kappa * (0.1e1 - t187) - t64 * (0.1e1 - t194)
  t203 = f.my_piecewise3(t162, 0, 0.4e1 / 0.3e1 * t163 * t167)
  t209 = f.my_piecewise3(t162, t104, t163 * t161)
  t215 = f.my_piecewise3(t159, 0, -0.3e1 / 0.8e1 * t5 * t176 * t42 * t197 - t5 * t203 * t81 * t197 / 0.4e1 + t5 * t209 * t108 * t197 / 0.12e2)
  t225 = t24 ** 2
  t229 = 0.6e1 * t33 - 0.6e1 * t16 / t225
  t230 = f.my_piecewise5(t10, 0, t14, 0, t229)
  t234 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t230)
  t257 = 0.1e1 / t80 / t24
  t270 = 0.1e1 / t53 / t118 / r0
  t275 = t118 ** 2
  t277 = 0.1e1 / t52 / t275
  t283 = t46 ** 2
  t284 = 0.1e1 / t283
  t286 = t131 * s0
  t289 = 0.1e1 / t275 / t87
  t290 = params.kappa ** 2
  t316 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t234 * t42 * t73 - 0.3e1 / 0.8e1 * t5 * t41 * t81 * t73 - 0.9e1 / 0.8e1 * t5 * t43 * t99 + t5 * t79 * t108 * t73 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t82 * t99 - 0.9e1 / 0.8e1 * t5 * t86 * t152 - 0.5e1 / 0.36e2 * t5 * t106 * t257 * t73 + t5 * t109 * t99 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t113 * t152 - 0.3e1 / 0.8e1 * t5 * t117 * (-0.154e3 / 0.81e2 * t50 * s0 * t270 * t61 + 0.11e2 / 0.81e2 * t130 * t131 * t277 * t136 - 0.2e1 / 0.243e3 * t125 * params.mu * t284 * t286 * t289 / t290 * t61 + 0.154e3 / 0.81e2 * t94 * t66 * t270 * t70 - 0.11e2 / 0.81e2 * t146 * t147 * t277 * t70 + 0.2e1 / 0.243e3 * t64 * t144 * params.alpha * t284 * t286 * t289 * t70))
  t326 = f.my_piecewise5(t14, 0, t10, 0, -t229)
  t330 = f.my_piecewise3(t162, 0, -0.8e1 / 0.27e2 / t164 / t161 * t168 * t167 + 0.4e1 / 0.3e1 * t165 * t167 * t172 + 0.4e1 / 0.3e1 * t163 * t326)
  t348 = f.my_piecewise3(t159, 0, -0.3e1 / 0.8e1 * t5 * t330 * t42 * t197 - 0.3e1 / 0.8e1 * t5 * t176 * t81 * t197 + t5 * t203 * t108 * t197 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t209 * t257 * t197)
  d111 = 0.3e1 * t157 + 0.3e1 * t215 + t6 * (t316 + t348)

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
  t56 = 6 ** (0.1e1 / 0.3e1)
  t58 = jnp.pi ** 2
  t59 = t58 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t62 = params.mu * t56 * t61
  t63 = r0 ** 2
  t64 = r0 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t67 = 0.1e1 / t65 / t63
  t69 = 0.1e1 / params.kappa
  t73 = jnp.exp(-t62 * s0 * t67 * t69 / 0.24e2)
  t76 = params.kappa + 0.1e1
  t77 = params.alpha * t56
  t78 = t61 * s0
  t82 = jnp.exp(-t77 * t78 * t67 / 0.24e2)
  t85 = 0.1e1 + params.kappa * (0.1e1 - t73) - t76 * (0.1e1 - t82)
  t94 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t95 = t54 ** 2
  t96 = 0.1e1 / t95
  t97 = t94 * t96
  t101 = t94 * t54
  t102 = t63 * r0
  t104 = 0.1e1 / t65 / t102
  t109 = t76 * params.alpha * t56
  t114 = -t62 * s0 * t104 * t73 / 0.9e1 + t109 * t78 * t104 * t82 / 0.9e1
  t120 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t122 = 0.1e1 / t95 / t6
  t123 = t120 * t122
  t127 = t120 * t96
  t131 = t120 * t54
  t132 = t63 ** 2
  t134 = 0.1e1 / t65 / t132
  t139 = params.mu ** 2
  t140 = t56 ** 2
  t143 = 0.1e1 / t59 / t58
  t144 = t139 * t140 * t143
  t145 = s0 ** 2
  t148 = 0.1e1 / t64 / t132 / t102
  t150 = t69 * t73
  t158 = params.alpha ** 2
  t160 = t76 * t158 * t140
  t161 = t143 * t145
  t166 = 0.11e2 / 0.27e2 * t62 * s0 * t134 * t73 - t144 * t145 * t148 * t150 / 0.81e2 - 0.11e2 / 0.27e2 * t109 * t78 * t134 * t82 + t160 * t161 * t148 * t82 / 0.81e2
  t170 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t171 = t170 * f.p.zeta_threshold
  t173 = f.my_piecewise3(t20, t171, t21 * t19)
  t175 = 0.1e1 / t95 / t25
  t176 = t173 * t175
  t180 = t173 * t122
  t184 = t173 * t96
  t188 = t173 * t54
  t191 = 0.1e1 / t65 / t132 / r0
  t196 = t132 ** 2
  t198 = 0.1e1 / t64 / t196
  t204 = t58 ** 2
  t205 = 0.1e1 / t204
  t207 = t145 * s0
  t208 = t139 * params.mu * t205 * t207
  t210 = 0.1e1 / t196 / t102
  t211 = params.kappa ** 2
  t212 = 0.1e1 / t211
  t227 = t76 * t158 * params.alpha * t205
  t232 = -0.154e3 / 0.81e2 * t62 * s0 * t191 * t73 + 0.11e2 / 0.81e2 * t144 * t145 * t198 * t150 - 0.2e1 / 0.243e3 * t208 * t210 * t212 * t73 + 0.154e3 / 0.81e2 * t109 * t78 * t191 * t82 - 0.11e2 / 0.81e2 * t160 * t161 * t198 * t82 + 0.2e1 / 0.243e3 * t227 * t207 * t210 * t82
  t237 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t85 - 0.3e1 / 0.8e1 * t5 * t97 * t85 - 0.9e1 / 0.8e1 * t5 * t101 * t114 + t5 * t123 * t85 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t127 * t114 - 0.9e1 / 0.8e1 * t5 * t131 * t166 - 0.5e1 / 0.36e2 * t5 * t176 * t85 + t5 * t180 * t114 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t184 * t166 - 0.3e1 / 0.8e1 * t5 * t188 * t232)
  t239 = r1 <= f.p.dens_threshold
  t240 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t241 = 0.1e1 + t240
  t242 = t241 <= f.p.zeta_threshold
  t243 = t241 ** (0.1e1 / 0.3e1)
  t244 = t243 ** 2
  t246 = 0.1e1 / t244 / t241
  t248 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t249 = t248 ** 2
  t253 = 0.1e1 / t244
  t254 = t253 * t248
  t256 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t260 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t264 = f.my_piecewise3(t242, 0, -0.8e1 / 0.27e2 * t246 * t249 * t248 + 0.4e1 / 0.3e1 * t254 * t256 + 0.4e1 / 0.3e1 * t243 * t260)
  t266 = r1 ** 2
  t267 = r1 ** (0.1e1 / 0.3e1)
  t268 = t267 ** 2
  t270 = 0.1e1 / t268 / t266
  t275 = jnp.exp(-t62 * s2 * t270 * t69 / 0.24e2)
  t282 = jnp.exp(-t77 * t61 * s2 * t270 / 0.24e2)
  t285 = 0.1e1 + params.kappa * (0.1e1 - t275) - t76 * (0.1e1 - t282)
  t294 = f.my_piecewise3(t242, 0, 0.4e1 / 0.9e1 * t253 * t249 + 0.4e1 / 0.3e1 * t243 * t256)
  t301 = f.my_piecewise3(t242, 0, 0.4e1 / 0.3e1 * t243 * t248)
  t307 = f.my_piecewise3(t242, t171, t243 * t241)
  t313 = f.my_piecewise3(t239, 0, -0.3e1 / 0.8e1 * t5 * t264 * t54 * t285 - 0.3e1 / 0.8e1 * t5 * t294 * t96 * t285 + t5 * t301 * t122 * t285 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t307 * t175 * t285)
  t327 = t132 * t63
  t329 = 0.1e1 / t65 / t327
  t336 = 0.1e1 / t64 / t196 / r0
  t342 = 0.1e1 / t196 / t132
  t347 = t139 ** 2
  t349 = t145 ** 2
  t352 = 0.1e1 / t65 / t196 / t327
  t374 = t158 ** 2
  t387 = t19 ** 2
  t390 = t30 ** 2
  t396 = t41 ** 2
  t405 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t406 = f.my_piecewise5(t10, 0, t14, 0, t405)
  t410 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t387 * t390 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t396 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t406)
  t442 = 0.1e1 / t95 / t36
  t447 = -0.3e1 / 0.2e1 * t5 * t131 * t232 - 0.5e1 / 0.9e1 * t5 * t176 * t114 + t5 * t180 * t166 / 0.2e1 - t5 * t184 * t232 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t188 * (0.2618e4 / 0.243e3 * t62 * s0 * t329 * t73 - 0.979e3 / 0.729e3 * t144 * t145 * t336 * t150 + 0.44e2 / 0.243e3 * t208 * t342 * t212 * t73 - 0.2e1 / 0.2187e4 * t347 * t205 * t349 * t352 / t211 / params.kappa * t56 * t61 * t73 - 0.2618e4 / 0.243e3 * t109 * t78 * t329 * t82 + 0.979e3 / 0.729e3 * t160 * t161 * t336 * t82 - 0.44e2 / 0.243e3 * t227 * t207 * t342 * t82 + 0.2e1 / 0.2187e4 * t76 * t374 * t205 * t349 * t352 * t56 * t61 * t82) - 0.3e1 / 0.8e1 * t5 * t410 * t54 * t85 - 0.3e1 / 0.2e1 * t5 * t55 * t114 - 0.3e1 / 0.2e1 * t5 * t97 * t114 - 0.9e1 / 0.4e1 * t5 * t101 * t166 + t5 * t123 * t114 - 0.3e1 / 0.2e1 * t5 * t127 * t166 - t5 * t53 * t96 * t85 / 0.2e1 + t5 * t94 * t122 * t85 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t120 * t175 * t85 + 0.10e2 / 0.27e2 * t5 * t173 * t442 * t85
  t448 = f.my_piecewise3(t1, 0, t447)
  t449 = t241 ** 2
  t452 = t249 ** 2
  t458 = t256 ** 2
  t464 = f.my_piecewise5(t14, 0, t10, 0, -t405)
  t468 = f.my_piecewise3(t242, 0, 0.40e2 / 0.81e2 / t244 / t449 * t452 - 0.16e2 / 0.9e1 * t246 * t249 * t256 + 0.4e1 / 0.3e1 * t253 * t458 + 0.16e2 / 0.9e1 * t254 * t260 + 0.4e1 / 0.3e1 * t243 * t464)
  t490 = f.my_piecewise3(t239, 0, -0.3e1 / 0.8e1 * t5 * t468 * t54 * t285 - t5 * t264 * t96 * t285 / 0.2e1 + t5 * t294 * t122 * t285 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t301 * t175 * t285 + 0.10e2 / 0.27e2 * t5 * t307 * t442 * t285)
  d1111 = 0.4e1 * t237 + 0.4e1 * t313 + t6 * (t448 + t490)

  res = {'v4rho4': d1111}
  return res
