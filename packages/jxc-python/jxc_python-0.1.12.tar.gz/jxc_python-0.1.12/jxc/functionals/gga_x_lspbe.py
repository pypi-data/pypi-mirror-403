"""Generated from gga_x_lspbe.mpl."""

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

  lspbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2)) - (params_kappa + 1) * (1 - jnp.exp(-params_alpha * s ** 2))

  lspbe_f = lambda x: lspbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, lspbe_f, rs, z, xs0, xs1)

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

  lspbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2)) - (params_kappa + 1) * (1 - jnp.exp(-params_alpha * s ** 2))

  lspbe_f = lambda x: lspbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, lspbe_f, rs, z, xs0, xs1)

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

  lspbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2)) - (params_kappa + 1) * (1 - jnp.exp(-params_alpha * s ** 2))

  lspbe_f = lambda x: lspbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, lspbe_f, rs, z, xs0, xs1)

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
  t34 = t33 * s0
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t40 = t34 * t39
  t43 = params.kappa + t29 * t40 / 0.24e2
  t48 = params.kappa + 0.1e1
  t49 = params.alpha * t28
  t52 = jnp.exp(-t49 * t40 / 0.24e2)
  t55 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t43) - t48 * (0.1e1 - t52)
  t59 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t55)
  t60 = r1 <= f.p.dens_threshold
  t61 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t62 = 0.1e1 + t61
  t63 = t62 <= f.p.zeta_threshold
  t64 = t62 ** (0.1e1 / 0.3e1)
  t66 = f.my_piecewise3(t63, t22, t64 * t62)
  t67 = t66 * t26
  t68 = t33 * s2
  t69 = r1 ** 2
  t70 = r1 ** (0.1e1 / 0.3e1)
  t71 = t70 ** 2
  t73 = 0.1e1 / t71 / t69
  t74 = t68 * t73
  t77 = params.kappa + t29 * t74 / 0.24e2
  t84 = jnp.exp(-t49 * t74 / 0.24e2)
  t87 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t77) - t48 * (0.1e1 - t84)
  t91 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t67 * t87)
  t92 = t6 ** 2
  t94 = t16 / t92
  t95 = t7 - t94
  t96 = f.my_piecewise5(t10, 0, t14, 0, t95)
  t99 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t96)
  t104 = t26 ** 2
  t105 = 0.1e1 / t104
  t109 = t5 * t25 * t105 * t55 / 0.8e1
  t110 = params.kappa ** 2
  t111 = t43 ** 2
  t114 = t110 / t111 * params.mu
  t115 = t28 * t33
  t118 = 0.1e1 / t37 / t35 / r0
  t123 = t48 * params.alpha * t28
  t133 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t99 * t26 * t55 - t109 - 0.3e1 / 0.8e1 * t5 * t27 * (-t114 * t115 * s0 * t118 / 0.9e1 + t123 * t34 * t118 * t52 / 0.9e1))
  t135 = f.my_piecewise5(t14, 0, t10, 0, -t95)
  t138 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t135)
  t146 = t5 * t66 * t105 * t87 / 0.8e1
  t148 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t138 * t26 * t87 - t146)
  vrho_0_ = t59 + t91 + t6 * (t133 + t148)
  t151 = -t7 - t94
  t152 = f.my_piecewise5(t10, 0, t14, 0, t151)
  t155 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t152)
  t161 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t155 * t26 * t55 - t109)
  t163 = f.my_piecewise5(t14, 0, t10, 0, -t151)
  t166 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t163)
  t171 = t77 ** 2
  t174 = t110 / t171 * params.mu
  t177 = 0.1e1 / t71 / t69 / r1
  t190 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t166 * t26 * t87 - t146 - 0.3e1 / 0.8e1 * t5 * t67 * (-t174 * t115 * s2 * t177 / 0.9e1 + t123 * t68 * t177 * t84 / 0.9e1))
  vrho_1_ = t59 + t91 + t6 * (t161 + t190)
  t203 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-t123 * t33 * t39 * t52 / 0.24e2 + t114 * t115 * t39 / 0.24e2))
  vsigma_0_ = t6 * t203
  vsigma_1_ = 0.0e0
  t214 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t67 * (-t123 * t33 * t73 * t84 / 0.24e2 + t174 * t115 * t73 / 0.24e2))
  vsigma_2_ = t6 * t214
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

  lspbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2)) - (params_kappa + 1) * (1 - jnp.exp(-params_alpha * s ** 2))

  lspbe_f = lambda x: lspbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, lspbe_f, rs, z, xs0, xs1)

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
  t21 = params.mu * t20
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t18 ** 2
  t33 = 0.1e1 / t31 / t30
  t34 = t29 * t33
  t37 = params.kappa + t21 * t25 * t34 / 0.24e2
  t42 = params.kappa + 0.1e1
  t47 = jnp.exp(-params.alpha * t20 * t25 * t34 / 0.24e2)
  t50 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t37) - t42 * (0.1e1 - t47)
  t54 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t50)
  t60 = params.kappa ** 2
  t61 = t37 ** 2
  t63 = t60 / t61
  t68 = 0.1e1 / t31 / t30 / r0
  t72 = t42 * params.alpha
  t73 = t20 * t25
  t84 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t50 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t63 * t21 * t25 * s0 * t28 * t68 / 0.9e1 + t72 * t73 * t29 * t68 * t47 / 0.9e1))
  vrho_0_ = 0.2e1 * r0 * t84 + 0.2e1 * t54
  t101 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-t72 * t20 * t25 * t28 * t33 * t47 / 0.24e2 + t63 * params.mu * t73 * t28 * t33 / 0.24e2))
  vsigma_0_ = 0.2e1 * r0 * t101
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
  t23 = params.mu * t22
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t35 = t31 * t34
  t38 = params.kappa + t23 * t27 * t35 / 0.24e2
  t43 = params.kappa + 0.1e1
  t48 = jnp.exp(-params.alpha * t22 * t27 * t35 / 0.24e2)
  t51 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t38) - t43 * (0.1e1 - t48)
  t55 = t17 * t18
  t56 = params.kappa ** 2
  t57 = t38 ** 2
  t59 = t56 / t57
  t60 = t59 * t23
  t61 = t27 * s0
  t62 = t32 * r0
  t64 = 0.1e1 / t19 / t62
  t65 = t30 * t64
  t68 = t43 * params.alpha
  t69 = t22 * t27
  t70 = t68 * t69
  t71 = t64 * t48
  t75 = t70 * t31 * t71 / 0.9e1 - t60 * t61 * t65 / 0.9e1
  t80 = f.my_piecewise3(t2, 0, -t6 * t21 * t51 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t55 * t75)
  t93 = t56 / t57 / t38
  t94 = params.mu ** 2
  t95 = t22 ** 2
  t97 = t93 * t94 * t95
  t99 = 0.1e1 / t25 / t24
  t100 = s0 ** 2
  t102 = t32 ** 2
  t105 = 0.1e1 / t18 / t102 / t62
  t111 = 0.1e1 / t19 / t102
  t120 = params.alpha ** 2
  t121 = t43 * t120
  t122 = t95 * t99
  t123 = t121 * t122
  t134 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t51 / 0.12e2 - t6 * t21 * t75 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t55 * (-0.4e1 / 0.81e2 * t97 * t99 * t100 * t29 * t105 + 0.11e2 / 0.27e2 * t60 * t61 * t30 * t111 - 0.11e2 / 0.27e2 * t70 * t31 * t111 * t48 + 0.2e1 / 0.81e2 * t123 * t100 * t29 * t105 * t48))
  v2rho2_0_ = 0.2e1 * r0 * t134 + 0.4e1 * t80
  t137 = t59 * params.mu
  t141 = t68 * t22
  t142 = t27 * t30
  t147 = t137 * t69 * t30 * t34 / 0.24e2 - t141 * t142 * t34 * t48 / 0.24e2
  t151 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t55 * t147)
  t155 = t99 * t29
  t158 = 0.1e1 / t18 / t102 / t32
  t179 = f.my_piecewise3(t2, 0, -t6 * t21 * t147 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t55 * (t97 * t155 * t158 * s0 / 0.54e2 - t137 * t69 * t65 / 0.9e1 + t141 * t142 * t71 / 0.9e1 - t123 * t29 * t158 * s0 * t48 / 0.108e3))
  v2rhosigma_0_ = 0.2e1 * r0 * t179 + 0.2e1 * t151
  t185 = 0.1e1 / t18 / t102 / r0
  t199 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t55 * (-t93 * t94 * t122 * t29 * t185 / 0.144e3 + t121 * t95 * t155 * t185 * t48 / 0.288e3))
  v2sigma2_0_ = 0.2e1 * r0 * t199
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
  t24 = params.mu * t23
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t36 = t32 * t35
  t39 = params.kappa + t24 * t28 * t36 / 0.24e2
  t44 = params.kappa + 0.1e1
  t49 = jnp.exp(-params.alpha * t23 * t28 * t36 / 0.24e2)
  t52 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t39) - t44 * (0.1e1 - t49)
  t57 = t17 / t19
  t58 = params.kappa ** 2
  t59 = t39 ** 2
  t62 = t58 / t59 * t24
  t63 = t28 * s0
  t64 = t33 * r0
  t66 = 0.1e1 / t19 / t64
  t72 = t44 * params.alpha * t23 * t28
  t77 = -t62 * t63 * t31 * t66 / 0.9e1 + t72 * t32 * t66 * t49 / 0.9e1
  t81 = t17 * t18
  t85 = params.mu ** 2
  t86 = t23 ** 2
  t88 = t58 / t59 / t39 * t85 * t86
  t90 = 0.1e1 / t26 / t25
  t91 = s0 ** 2
  t92 = t90 * t91
  t93 = t33 ** 2
  t96 = 0.1e1 / t18 / t93 / t64
  t102 = 0.1e1 / t19 / t93
  t111 = params.alpha ** 2
  t114 = t44 * t111 * t86 * t90
  t115 = t91 * t30
  t120 = -0.4e1 / 0.81e2 * t88 * t92 * t30 * t96 + 0.11e2 / 0.27e2 * t62 * t63 * t31 * t102 - 0.11e2 / 0.27e2 * t72 * t32 * t102 * t49 + 0.2e1 / 0.81e2 * t114 * t115 * t96 * t49
  t125 = f.my_piecewise3(t2, 0, t6 * t22 * t52 / 0.12e2 - t6 * t57 * t77 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t81 * t120)
  t137 = t59 ** 2
  t142 = t25 ** 2
  t143 = 0.1e1 / t142
  t144 = t91 * s0
  t146 = t93 ** 2
  t148 = 0.1e1 / t146 / t64
  t153 = 0.1e1 / t18 / t146
  t160 = 0.1e1 / t19 / t93 / r0
  t185 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t52 + t6 * t22 * t77 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t57 * t120 - 0.3e1 / 0.8e1 * t6 * t81 * (-0.16e2 / 0.81e2 * t58 / t137 * t85 * params.mu * t143 * t144 * t148 + 0.44e2 / 0.81e2 * t88 * t92 * t30 * t153 - 0.154e3 / 0.81e2 * t62 * t63 * t31 * t160 + 0.154e3 / 0.81e2 * t72 * t32 * t160 * t49 - 0.22e2 / 0.81e2 * t114 * t115 * t153 * t49 + 0.8e1 / 0.243e3 * t44 * t111 * params.alpha * t143 * t144 * t148 * t49))
  v3rho3_0_ = 0.2e1 * r0 * t185 + 0.6e1 * t125

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
  t25 = params.mu * t24
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = t33 * t22
  t37 = params.kappa + t25 * t29 * t34 / 0.24e2
  t42 = params.kappa + 0.1e1
  t47 = jnp.exp(-params.alpha * t24 * t29 * t34 / 0.24e2)
  t50 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t37) - t42 * (0.1e1 - t47)
  t56 = t17 / t20 / r0
  t57 = params.kappa ** 2
  t58 = t37 ** 2
  t61 = t57 / t58 * t25
  t62 = t29 * s0
  t63 = t18 * r0
  t65 = 0.1e1 / t20 / t63
  t70 = t24 * t29
  t71 = t42 * params.alpha * t70
  t76 = -t61 * t62 * t32 * t65 / 0.9e1 + t71 * t33 * t65 * t47 / 0.9e1
  t81 = t17 / t20
  t85 = params.mu ** 2
  t86 = t24 ** 2
  t88 = t57 / t58 / t37 * t85 * t86
  t90 = 0.1e1 / t27 / t26
  t91 = s0 ** 2
  t92 = t90 * t91
  t93 = t18 ** 2
  t96 = 0.1e1 / t19 / t93 / t63
  t102 = 0.1e1 / t20 / t93
  t111 = params.alpha ** 2
  t114 = t42 * t111 * t86 * t90
  t115 = t91 * t31
  t120 = -0.4e1 / 0.81e2 * t88 * t92 * t31 * t96 + 0.11e2 / 0.27e2 * t61 * t62 * t32 * t102 - 0.11e2 / 0.27e2 * t71 * t33 * t102 * t47 + 0.2e1 / 0.81e2 * t114 * t115 * t96 * t47
  t124 = t17 * t19
  t125 = t58 ** 2
  t129 = t57 / t125 * t85 * params.mu
  t130 = t26 ** 2
  t131 = 0.1e1 / t130
  t132 = t91 * s0
  t133 = t131 * t132
  t134 = t93 ** 2
  t136 = 0.1e1 / t134 / t63
  t141 = 0.1e1 / t19 / t134
  t148 = 0.1e1 / t20 / t93 / r0
  t163 = t42 * t111 * params.alpha * t131
  t168 = -0.16e2 / 0.81e2 * t129 * t133 * t136 + 0.44e2 / 0.81e2 * t88 * t92 * t31 * t141 - 0.154e3 / 0.81e2 * t61 * t62 * t32 * t148 + 0.154e3 / 0.81e2 * t71 * t33 * t148 * t47 - 0.22e2 / 0.81e2 * t114 * t115 * t141 * t47 + 0.8e1 / 0.243e3 * t163 * t132 * t136 * t47
  t173 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t50 + t6 * t56 * t76 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t81 * t120 - 0.3e1 / 0.8e1 * t6 * t124 * t168)
  t191 = t85 ** 2
  t194 = t91 ** 2
  t195 = t93 * t18
  t198 = 0.1e1 / t20 / t134 / t195
  t205 = 0.1e1 / t134 / t93
  t211 = 0.1e1 / t19 / t134 / r0
  t217 = 0.1e1 / t20 / t195
  t234 = t111 ** 2
  t249 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t65 * t50 - 0.5e1 / 0.9e1 * t6 * t23 * t76 + t6 * t56 * t120 / 0.2e1 - t6 * t81 * t168 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t124 * (-0.64e2 / 0.729e3 * t57 / t125 / t37 * t191 * t131 * t194 * t198 * t70 * t32 + 0.352e3 / 0.81e2 * t129 * t133 * t205 - 0.3916e4 / 0.729e3 * t88 * t92 * t31 * t211 + 0.2618e4 / 0.243e3 * t61 * t62 * t32 * t217 - 0.2618e4 / 0.243e3 * t71 * t33 * t217 * t47 + 0.1958e4 / 0.729e3 * t114 * t115 * t211 * t47 - 0.176e3 / 0.243e3 * t163 * t132 * t205 * t47 + 0.8e1 / 0.2187e4 * t42 * t234 * t131 * t194 * t198 * t24 * t29 * t32 * t47))
  v4rho4_0_ = 0.2e1 * r0 * t249 + 0.8e1 * t173

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
  t33 = params.mu * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t44 = t38 / t41 / t39
  t47 = params.kappa + t33 * t44 / 0.24e2
  t52 = params.kappa + 0.1e1
  t53 = params.alpha * t32
  t56 = jnp.exp(-t53 * t44 / 0.24e2)
  t59 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t47) - t52 * (0.1e1 - t56)
  t63 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t64 = t63 * f.p.zeta_threshold
  t66 = f.my_piecewise3(t20, t64, t21 * t19)
  t67 = t30 ** 2
  t68 = 0.1e1 / t67
  t69 = t66 * t68
  t72 = t5 * t69 * t59 / 0.8e1
  t73 = t66 * t30
  t74 = params.kappa ** 2
  t75 = t47 ** 2
  t78 = t74 / t75 * params.mu
  t79 = t32 * t37
  t80 = t39 * r0
  t82 = 0.1e1 / t41 / t80
  t87 = t52 * params.alpha * t32
  t92 = -t78 * t79 * s0 * t82 / 0.9e1 + t87 * t38 * t82 * t56 / 0.9e1
  t97 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t59 - t72 - 0.3e1 / 0.8e1 * t5 * t73 * t92)
  t99 = r1 <= f.p.dens_threshold
  t100 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t101 = 0.1e1 + t100
  t102 = t101 <= f.p.zeta_threshold
  t103 = t101 ** (0.1e1 / 0.3e1)
  t105 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t108 = f.my_piecewise3(t102, 0, 0.4e1 / 0.3e1 * t103 * t105)
  t109 = t108 * t30
  t110 = t37 * s2
  t111 = r1 ** 2
  t112 = r1 ** (0.1e1 / 0.3e1)
  t113 = t112 ** 2
  t116 = t110 / t113 / t111
  t119 = params.kappa + t33 * t116 / 0.24e2
  t126 = jnp.exp(-t53 * t116 / 0.24e2)
  t129 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t119) - t52 * (0.1e1 - t126)
  t134 = f.my_piecewise3(t102, t64, t103 * t101)
  t135 = t134 * t68
  t138 = t5 * t135 * t129 / 0.8e1
  t140 = f.my_piecewise3(t99, 0, -0.3e1 / 0.8e1 * t5 * t109 * t129 - t138)
  t142 = t21 ** 2
  t143 = 0.1e1 / t142
  t144 = t26 ** 2
  t149 = t16 / t22 / t6
  t151 = -0.2e1 * t23 + 0.2e1 * t149
  t152 = f.my_piecewise5(t10, 0, t14, 0, t151)
  t156 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t143 * t144 + 0.4e1 / 0.3e1 * t21 * t152)
  t163 = t5 * t29 * t68 * t59
  t169 = 0.1e1 / t67 / t6
  t173 = t5 * t66 * t169 * t59 / 0.12e2
  t175 = t5 * t69 * t92
  t180 = params.mu ** 2
  t182 = t32 ** 2
  t184 = 0.1e1 / t35 / t34
  t185 = t182 * t184
  t186 = s0 ** 2
  t187 = t39 ** 2
  t190 = 0.1e1 / t40 / t187 / t80
  t196 = 0.1e1 / t41 / t187
  t205 = params.alpha ** 2
  t207 = t52 * t205 * t182
  t218 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t156 * t30 * t59 - t163 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t92 + t173 - t175 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t73 * (-0.2e1 / 0.81e2 * t74 / t75 / t47 * t180 * t185 * t186 * t190 + 0.11e2 / 0.27e2 * t78 * t79 * s0 * t196 - 0.11e2 / 0.27e2 * t87 * t38 * t196 * t56 + t207 * t184 * t186 * t190 * t56 / 0.81e2))
  t219 = t103 ** 2
  t220 = 0.1e1 / t219
  t221 = t105 ** 2
  t225 = f.my_piecewise5(t14, 0, t10, 0, -t151)
  t229 = f.my_piecewise3(t102, 0, 0.4e1 / 0.9e1 * t220 * t221 + 0.4e1 / 0.3e1 * t103 * t225)
  t236 = t5 * t108 * t68 * t129
  t241 = t5 * t134 * t169 * t129 / 0.12e2
  t243 = f.my_piecewise3(t99, 0, -0.3e1 / 0.8e1 * t5 * t229 * t30 * t129 - t236 / 0.4e1 + t241)
  d11 = 0.2e1 * t97 + 0.2e1 * t140 + t6 * (t218 + t243)
  t246 = -t7 - t24
  t247 = f.my_piecewise5(t10, 0, t14, 0, t246)
  t250 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t247)
  t251 = t250 * t30
  t256 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t251 * t59 - t72)
  t258 = f.my_piecewise5(t14, 0, t10, 0, -t246)
  t261 = f.my_piecewise3(t102, 0, 0.4e1 / 0.3e1 * t103 * t258)
  t262 = t261 * t30
  t266 = t134 * t30
  t267 = t119 ** 2
  t270 = t74 / t267 * params.mu
  t271 = t111 * r1
  t273 = 0.1e1 / t113 / t271
  t281 = -t270 * t79 * s2 * t273 / 0.9e1 + t87 * t110 * t273 * t126 / 0.9e1
  t286 = f.my_piecewise3(t99, 0, -0.3e1 / 0.8e1 * t5 * t262 * t129 - t138 - 0.3e1 / 0.8e1 * t5 * t266 * t281)
  t290 = 0.2e1 * t149
  t291 = f.my_piecewise5(t10, 0, t14, 0, t290)
  t295 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t143 * t247 * t26 + 0.4e1 / 0.3e1 * t21 * t291)
  t302 = t5 * t250 * t68 * t59
  t310 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t295 * t30 * t59 - t302 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t251 * t92 - t163 / 0.8e1 + t173 - t175 / 0.8e1)
  t314 = f.my_piecewise5(t14, 0, t10, 0, -t290)
  t318 = f.my_piecewise3(t102, 0, 0.4e1 / 0.9e1 * t220 * t258 * t105 + 0.4e1 / 0.3e1 * t103 * t314)
  t325 = t5 * t261 * t68 * t129
  t332 = t5 * t135 * t281
  t335 = f.my_piecewise3(t99, 0, -0.3e1 / 0.8e1 * t5 * t318 * t30 * t129 - t325 / 0.8e1 - t236 / 0.8e1 + t241 - 0.3e1 / 0.8e1 * t5 * t109 * t281 - t332 / 0.8e1)
  d12 = t97 + t140 + t256 + t286 + t6 * (t310 + t335)
  t340 = t247 ** 2
  t344 = 0.2e1 * t23 + 0.2e1 * t149
  t345 = f.my_piecewise5(t10, 0, t14, 0, t344)
  t349 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t143 * t340 + 0.4e1 / 0.3e1 * t21 * t345)
  t356 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t349 * t30 * t59 - t302 / 0.4e1 + t173)
  t357 = t258 ** 2
  t361 = f.my_piecewise5(t14, 0, t10, 0, -t344)
  t365 = f.my_piecewise3(t102, 0, 0.4e1 / 0.9e1 * t220 * t357 + 0.4e1 / 0.3e1 * t103 * t361)
  t379 = s2 ** 2
  t380 = t111 ** 2
  t383 = 0.1e1 / t112 / t380 / t271
  t389 = 0.1e1 / t113 / t380
  t408 = f.my_piecewise3(t99, 0, -0.3e1 / 0.8e1 * t5 * t365 * t30 * t129 - t325 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t262 * t281 + t241 - t332 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t266 * (-0.2e1 / 0.81e2 * t74 / t267 / t119 * t180 * t185 * t379 * t383 + 0.11e2 / 0.27e2 * t270 * t79 * s2 * t389 - 0.11e2 / 0.27e2 * t87 * t110 * t389 * t126 + t207 * t184 * t379 * t383 * t126 / 0.81e2))
  d22 = 0.2e1 * t256 + 0.2e1 * t286 + t6 * (t356 + t408)
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
  t45 = params.mu * t44
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t50 = t49 * s0
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t56 = t50 / t53 / t51
  t59 = params.kappa + t45 * t56 / 0.24e2
  t64 = params.kappa + 0.1e1
  t65 = params.alpha * t44
  t68 = jnp.exp(-t65 * t56 / 0.24e2)
  t71 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t59) - t64 * (0.1e1 - t68)
  t77 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t78 = t42 ** 2
  t79 = 0.1e1 / t78
  t80 = t77 * t79
  t84 = t77 * t42
  t85 = params.kappa ** 2
  t86 = t59 ** 2
  t89 = t85 / t86 * params.mu
  t90 = t44 * t49
  t91 = t51 * r0
  t93 = 0.1e1 / t53 / t91
  t98 = t64 * params.alpha * t44
  t103 = -t89 * t90 * s0 * t93 / 0.9e1 + t98 * t50 * t93 * t68 / 0.9e1
  t107 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t108 = t107 * f.p.zeta_threshold
  t110 = f.my_piecewise3(t20, t108, t21 * t19)
  t112 = 0.1e1 / t78 / t6
  t113 = t110 * t112
  t117 = t110 * t79
  t121 = t110 * t42
  t125 = params.mu ** 2
  t126 = t85 / t86 / t59 * t125
  t127 = t44 ** 2
  t129 = 0.1e1 / t47 / t46
  t130 = t127 * t129
  t131 = s0 ** 2
  t132 = t51 ** 2
  t135 = 0.1e1 / t52 / t132 / t91
  t141 = 0.1e1 / t53 / t132
  t150 = params.alpha ** 2
  t152 = t64 * t150 * t127
  t153 = t129 * t131
  t158 = -0.2e1 / 0.81e2 * t126 * t130 * t131 * t135 + 0.11e2 / 0.27e2 * t89 * t90 * s0 * t141 - 0.11e2 / 0.27e2 * t98 * t50 * t141 * t68 + t152 * t153 * t135 * t68 / 0.81e2
  t163 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t71 - t5 * t80 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t84 * t103 + t5 * t113 * t71 / 0.12e2 - t5 * t117 * t103 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t121 * t158)
  t165 = r1 <= f.p.dens_threshold
  t166 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t167 = 0.1e1 + t166
  t168 = t167 <= f.p.zeta_threshold
  t169 = t167 ** (0.1e1 / 0.3e1)
  t170 = t169 ** 2
  t171 = 0.1e1 / t170
  t173 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t174 = t173 ** 2
  t178 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t182 = f.my_piecewise3(t168, 0, 0.4e1 / 0.9e1 * t171 * t174 + 0.4e1 / 0.3e1 * t169 * t178)
  t185 = r1 ** 2
  t186 = r1 ** (0.1e1 / 0.3e1)
  t187 = t186 ** 2
  t190 = t49 * s2 / t187 / t185
  t200 = jnp.exp(-t65 * t190 / 0.24e2)
  t203 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + t45 * t190 / 0.24e2)) - t64 * (0.1e1 - t200)
  t209 = f.my_piecewise3(t168, 0, 0.4e1 / 0.3e1 * t169 * t173)
  t215 = f.my_piecewise3(t168, t108, t169 * t167)
  t221 = f.my_piecewise3(t165, 0, -0.3e1 / 0.8e1 * t5 * t182 * t42 * t203 - t5 * t209 * t79 * t203 / 0.4e1 + t5 * t215 * t112 * t203 / 0.12e2)
  t231 = t24 ** 2
  t235 = 0.6e1 * t33 - 0.6e1 * t16 / t231
  t236 = f.my_piecewise5(t10, 0, t14, 0, t235)
  t240 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t236)
  t263 = 0.1e1 / t78 / t24
  t274 = t86 ** 2
  t279 = t46 ** 2
  t280 = 0.1e1 / t279
  t281 = t131 * s0
  t283 = t132 ** 2
  t285 = 0.1e1 / t283 / t91
  t290 = 0.1e1 / t52 / t283
  t297 = 0.1e1 / t53 / t132 / r0
  t322 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t240 * t42 * t71 - 0.3e1 / 0.8e1 * t5 * t41 * t79 * t71 - 0.9e1 / 0.8e1 * t5 * t43 * t103 + t5 * t77 * t112 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t80 * t103 - 0.9e1 / 0.8e1 * t5 * t84 * t158 - 0.5e1 / 0.36e2 * t5 * t110 * t263 * t71 + t5 * t113 * t103 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t117 * t158 - 0.3e1 / 0.8e1 * t5 * t121 * (-0.4e1 / 0.81e2 * t85 / t274 * t125 * params.mu * t280 * t281 * t285 + 0.22e2 / 0.81e2 * t126 * t130 * t131 * t290 - 0.154e3 / 0.81e2 * t89 * t90 * s0 * t297 + 0.154e3 / 0.81e2 * t98 * t50 * t297 * t68 - 0.11e2 / 0.81e2 * t152 * t153 * t290 * t68 + 0.2e1 / 0.243e3 * t64 * t150 * params.alpha * t280 * t281 * t285 * t68))
  t332 = f.my_piecewise5(t14, 0, t10, 0, -t235)
  t336 = f.my_piecewise3(t168, 0, -0.8e1 / 0.27e2 / t170 / t167 * t174 * t173 + 0.4e1 / 0.3e1 * t171 * t173 * t178 + 0.4e1 / 0.3e1 * t169 * t332)
  t354 = f.my_piecewise3(t165, 0, -0.3e1 / 0.8e1 * t5 * t336 * t42 * t203 - 0.3e1 / 0.8e1 * t5 * t182 * t79 * t203 + t5 * t209 * t112 * t203 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t215 * t263 * t203)
  d111 = 0.3e1 * t163 + 0.3e1 * t221 + t6 * (t322 + t354)

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
  t57 = params.mu * t56
  t58 = jnp.pi ** 2
  t59 = t58 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t62 = t61 * s0
  t63 = r0 ** 2
  t64 = r0 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t68 = t62 / t65 / t63
  t71 = params.kappa + t57 * t68 / 0.24e2
  t76 = params.kappa + 0.1e1
  t77 = params.alpha * t56
  t80 = jnp.exp(-t77 * t68 / 0.24e2)
  t83 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t71) - t76 * (0.1e1 - t80)
  t92 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t93 = t54 ** 2
  t94 = 0.1e1 / t93
  t95 = t92 * t94
  t99 = t92 * t54
  t100 = params.kappa ** 2
  t101 = t71 ** 2
  t104 = t100 / t101 * params.mu
  t105 = t56 * t61
  t106 = t63 * r0
  t108 = 0.1e1 / t65 / t106
  t113 = t76 * params.alpha * t56
  t118 = -t104 * t105 * s0 * t108 / 0.9e1 + t113 * t62 * t108 * t80 / 0.9e1
  t124 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t126 = 0.1e1 / t93 / t6
  t127 = t124 * t126
  t131 = t124 * t94
  t135 = t124 * t54
  t139 = params.mu ** 2
  t140 = t100 / t101 / t71 * t139
  t141 = t56 ** 2
  t143 = 0.1e1 / t59 / t58
  t144 = t141 * t143
  t145 = s0 ** 2
  t146 = t63 ** 2
  t149 = 0.1e1 / t64 / t146 / t106
  t155 = 0.1e1 / t65 / t146
  t164 = params.alpha ** 2
  t166 = t76 * t164 * t141
  t167 = t143 * t145
  t172 = -0.2e1 / 0.81e2 * t140 * t144 * t145 * t149 + 0.11e2 / 0.27e2 * t104 * t105 * s0 * t155 - 0.11e2 / 0.27e2 * t113 * t62 * t155 * t80 + t166 * t167 * t149 * t80 / 0.81e2
  t176 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t177 = t176 * f.p.zeta_threshold
  t179 = f.my_piecewise3(t20, t177, t21 * t19)
  t181 = 0.1e1 / t93 / t25
  t182 = t179 * t181
  t186 = t179 * t126
  t190 = t179 * t94
  t194 = t179 * t54
  t195 = t101 ** 2
  t199 = t100 / t195 * t139 * params.mu
  t200 = t58 ** 2
  t201 = 0.1e1 / t200
  t202 = t145 * s0
  t203 = t201 * t202
  t204 = t146 ** 2
  t206 = 0.1e1 / t204 / t106
  t211 = 0.1e1 / t64 / t204
  t218 = 0.1e1 / t65 / t146 / r0
  t233 = t76 * t164 * params.alpha * t201
  t238 = -0.4e1 / 0.81e2 * t199 * t203 * t206 + 0.22e2 / 0.81e2 * t140 * t144 * t145 * t211 - 0.154e3 / 0.81e2 * t104 * t105 * s0 * t218 + 0.154e3 / 0.81e2 * t113 * t62 * t218 * t80 - 0.11e2 / 0.81e2 * t166 * t167 * t211 * t80 + 0.2e1 / 0.243e3 * t233 * t202 * t206 * t80
  t243 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t83 - 0.3e1 / 0.8e1 * t5 * t95 * t83 - 0.9e1 / 0.8e1 * t5 * t99 * t118 + t5 * t127 * t83 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t131 * t118 - 0.9e1 / 0.8e1 * t5 * t135 * t172 - 0.5e1 / 0.36e2 * t5 * t182 * t83 + t5 * t186 * t118 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t190 * t172 - 0.3e1 / 0.8e1 * t5 * t194 * t238)
  t245 = r1 <= f.p.dens_threshold
  t246 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t247 = 0.1e1 + t246
  t248 = t247 <= f.p.zeta_threshold
  t249 = t247 ** (0.1e1 / 0.3e1)
  t250 = t249 ** 2
  t252 = 0.1e1 / t250 / t247
  t254 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t255 = t254 ** 2
  t259 = 0.1e1 / t250
  t260 = t259 * t254
  t262 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t266 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t270 = f.my_piecewise3(t248, 0, -0.8e1 / 0.27e2 * t252 * t255 * t254 + 0.4e1 / 0.3e1 * t260 * t262 + 0.4e1 / 0.3e1 * t249 * t266)
  t273 = r1 ** 2
  t274 = r1 ** (0.1e1 / 0.3e1)
  t275 = t274 ** 2
  t278 = t61 * s2 / t275 / t273
  t288 = jnp.exp(-t77 * t278 / 0.24e2)
  t291 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + t57 * t278 / 0.24e2)) - t76 * (0.1e1 - t288)
  t300 = f.my_piecewise3(t248, 0, 0.4e1 / 0.9e1 * t259 * t255 + 0.4e1 / 0.3e1 * t249 * t262)
  t307 = f.my_piecewise3(t248, 0, 0.4e1 / 0.3e1 * t249 * t254)
  t313 = f.my_piecewise3(t248, t177, t249 * t247)
  t319 = f.my_piecewise3(t245, 0, -0.3e1 / 0.8e1 * t5 * t270 * t54 * t291 - 0.3e1 / 0.8e1 * t5 * t300 * t94 * t291 + t5 * t307 * t126 * t291 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t313 * t181 * t291)
  t341 = t139 ** 2
  t344 = t145 ** 2
  t345 = t146 * t63
  t348 = 0.1e1 / t65 / t204 / t345
  t354 = 0.1e1 / t204 / t146
  t360 = 0.1e1 / t64 / t204 / r0
  t366 = 0.1e1 / t65 / t345
  t383 = t164 ** 2
  t396 = t19 ** 2
  t399 = t30 ** 2
  t405 = t41 ** 2
  t414 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t415 = f.my_piecewise5(t10, 0, t14, 0, t414)
  t419 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t396 * t399 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t405 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t415)
  t446 = 0.1e1 / t93 / t36
  t451 = t5 * t127 * t118 - 0.3e1 / 0.2e1 * t5 * t131 * t172 - 0.3e1 / 0.2e1 * t5 * t135 * t238 - 0.5e1 / 0.9e1 * t5 * t182 * t118 + t5 * t186 * t172 / 0.2e1 - t5 * t190 * t238 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t194 * (-0.16e2 / 0.729e3 * t100 / t195 / t71 * t341 * t201 * t344 * t348 * t105 + 0.88e2 / 0.81e2 * t199 * t203 * t354 - 0.1958e4 / 0.729e3 * t140 * t144 * t145 * t360 + 0.2618e4 / 0.243e3 * t104 * t105 * s0 * t366 - 0.2618e4 / 0.243e3 * t113 * t62 * t366 * t80 + 0.979e3 / 0.729e3 * t166 * t167 * t360 * t80 - 0.44e2 / 0.243e3 * t233 * t202 * t354 * t80 + 0.2e1 / 0.2187e4 * t76 * t383 * t201 * t344 * t348 * t56 * t61 * t80) - 0.3e1 / 0.8e1 * t5 * t419 * t54 * t83 - 0.3e1 / 0.2e1 * t5 * t55 * t118 - 0.3e1 / 0.2e1 * t5 * t95 * t118 - 0.9e1 / 0.4e1 * t5 * t99 * t172 - t5 * t53 * t94 * t83 / 0.2e1 + t5 * t92 * t126 * t83 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t124 * t181 * t83 + 0.10e2 / 0.27e2 * t5 * t179 * t446 * t83
  t452 = f.my_piecewise3(t1, 0, t451)
  t453 = t247 ** 2
  t456 = t255 ** 2
  t462 = t262 ** 2
  t468 = f.my_piecewise5(t14, 0, t10, 0, -t414)
  t472 = f.my_piecewise3(t248, 0, 0.40e2 / 0.81e2 / t250 / t453 * t456 - 0.16e2 / 0.9e1 * t252 * t255 * t262 + 0.4e1 / 0.3e1 * t259 * t462 + 0.16e2 / 0.9e1 * t260 * t266 + 0.4e1 / 0.3e1 * t249 * t468)
  t494 = f.my_piecewise3(t245, 0, -0.3e1 / 0.8e1 * t5 * t472 * t54 * t291 - t5 * t270 * t94 * t291 / 0.2e1 + t5 * t300 * t126 * t291 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t307 * t181 * t291 + 0.10e2 / 0.27e2 * t5 * t313 * t446 * t291)
  d1111 = 0.4e1 * t243 + 0.4e1 * t319 + t6 * (t452 + t494)

  res = {'v4rho4': d1111}
  return res
