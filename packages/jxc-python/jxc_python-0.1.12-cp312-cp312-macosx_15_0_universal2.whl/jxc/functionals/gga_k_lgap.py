"""Generated from gga_k_lgap.mpl."""

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

  lgap_f0 = lambda s: 1 + params_kappa * (1 - jnp.exp(-jnp.sum(jnp.array([params_mu[i] * s ** i for i in range(1, 3 + 1)]), axis=0)))

  lgap_f = lambda x: lgap_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lgap_f, rs, z, xs0, xs1)

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

  lgap_f0 = lambda s: 1 + params_kappa * (1 - jnp.exp(-jnp.sum(jnp.array([params_mu[i] * s ** i for i in range(1, 3 + 1)]), axis=0)))

  lgap_f = lambda x: lgap_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lgap_f, rs, z, xs0, xs1)

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

  lgap_f0 = lambda s: 1 + params_kappa * (1 - jnp.exp(-jnp.sum(jnp.array([params_mu[i] * s ** i for i in range(1, 3 + 1)]), axis=0)))

  lgap_f = lambda x: lgap_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lgap_f, rs, z, xs0, xs1)

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
  t33 = 6 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = params.mu[0] * t34
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t37
  t39 = jnp.sqrt(s0)
  t40 = t38 * t39
  t41 = r0 ** (0.1e1 / 0.3e1)
  t43 = 0.1e1 / t41 / r0
  t48 = params.mu[1] * t33
  t49 = t37 ** 2
  t50 = 0.1e1 / t49
  t51 = t50 * s0
  t52 = r0 ** 2
  t53 = t41 ** 2
  t55 = 0.1e1 / t53 / t52
  t61 = params.mu[2] / t36
  t62 = t39 * s0
  t63 = t52 ** 2
  t64 = 0.1e1 / t63
  t69 = jnp.exp(-t35 * t40 * t43 / 0.12e2 - t48 * t51 * t55 / 0.24e2 - t61 * t62 * t64 / 0.48e2)
  t72 = 0.1e1 + params.kappa * (0.1e1 - t69)
  t76 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t28 * t30 * t72)
  t77 = r1 <= f.p.dens_threshold
  t78 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t79 = 0.1e1 + t78
  t80 = t79 <= f.p.zeta_threshold
  t81 = t79 ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t84 = f.my_piecewise3(t80, t24, t82 * t79)
  t86 = jnp.sqrt(s2)
  t87 = t38 * t86
  t88 = r1 ** (0.1e1 / 0.3e1)
  t90 = 0.1e1 / t88 / r1
  t94 = t50 * s2
  t95 = r1 ** 2
  t96 = t88 ** 2
  t98 = 0.1e1 / t96 / t95
  t102 = t86 * s2
  t103 = t95 ** 2
  t104 = 0.1e1 / t103
  t109 = jnp.exp(-t35 * t87 * t90 / 0.12e2 - t48 * t94 * t98 / 0.24e2 - t61 * t102 * t104 / 0.48e2)
  t112 = 0.1e1 + params.kappa * (0.1e1 - t109)
  t116 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t84 * t30 * t112)
  t117 = t7 ** 2
  t119 = t17 / t117
  t120 = t8 - t119
  t121 = f.my_piecewise5(t11, 0, t15, 0, t120)
  t124 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t121)
  t129 = 0.1e1 / t29
  t133 = t6 * t28 * t129 * t72 / 0.10e2
  t134 = t6 * t28
  t135 = t30 * params.kappa
  t158 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t124 * t30 * t72 + t133 - 0.3e1 / 0.20e2 * t134 * t135 * (t35 * t40 / t41 / t52 / 0.9e1 + t48 * t51 / t53 / t52 / r0 / 0.9e1 + t61 * t62 / t63 / r0 / 0.12e2) * t69)
  t160 = f.my_piecewise5(t15, 0, t11, 0, -t120)
  t163 = f.my_piecewise3(t80, 0, 0.5e1 / 0.3e1 * t82 * t160)
  t171 = t6 * t84 * t129 * t112 / 0.10e2
  t173 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t163 * t30 * t112 + t171)
  vrho_0_ = t76 + t116 + t7 * (t158 + t173)
  t176 = -t8 - t119
  t177 = f.my_piecewise5(t11, 0, t15, 0, t176)
  t180 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t177)
  t186 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t180 * t30 * t72 + t133)
  t188 = f.my_piecewise5(t15, 0, t11, 0, -t176)
  t191 = f.my_piecewise3(t80, 0, 0.5e1 / 0.3e1 * t82 * t188)
  t196 = t6 * t84
  t219 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t191 * t30 * t112 + t171 - 0.3e1 / 0.20e2 * t196 * t135 * (t35 * t87 / t88 / t95 / 0.9e1 + t48 * t94 / t96 / t95 / r1 / 0.9e1 + t61 * t102 / t103 / r1 / 0.12e2) * t109)
  vrho_1_ = t76 + t116 + t7 * (t186 + t219)
  t238 = f.my_piecewise3(t1, 0, -0.3e1 / 0.20e2 * t134 * t135 * (-t35 * t38 / t39 * t43 / 0.24e2 - t48 * t50 * t55 / 0.24e2 - t61 * t39 * t64 / 0.32e2) * t69)
  vsigma_0_ = t7 * t238
  vsigma_1_ = 0.0e0
  t255 = f.my_piecewise3(t77, 0, -0.3e1 / 0.20e2 * t196 * t135 * (-t35 * t38 / t86 * t90 / 0.24e2 - t48 * t50 * t98 / 0.24e2 - t61 * t86 * t104 / 0.32e2) * t109)
  vsigma_2_ = t7 * t255
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

  lgap_f0 = lambda s: 1 + params_kappa * (1 - jnp.exp(-jnp.sum(jnp.array([params_mu[i] * s ** i for i in range(1, 3 + 1)]), axis=0)))

  lgap_f = lambda x: lgap_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lgap_f, rs, z, xs0, xs1)

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
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t31 = params.mu[0] * t26 / t29
  t32 = jnp.sqrt(s0)
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t32 * t33
  t36 = 0.1e1 / t21 / r0
  t41 = params.mu[1] * t25
  t42 = t29 ** 2
  t43 = 0.1e1 / t42
  t44 = t41 * t43
  t45 = t33 ** 2
  t46 = s0 * t45
  t47 = r0 ** 2
  t49 = 0.1e1 / t22 / t47
  t55 = params.mu[2] / t28
  t56 = t32 * s0
  t57 = t47 ** 2
  t58 = 0.1e1 / t57
  t63 = jnp.exp(-t31 * t34 * t36 / 0.12e2 - t44 * t46 * t49 / 0.24e2 - t55 * t56 * t58 / 0.24e2)
  t66 = 0.1e1 + params.kappa * (0.1e1 - t63)
  t70 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t20 * t22 * t66)
  t76 = t7 * t20
  t77 = t22 * params.kappa
  t100 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t66 / 0.10e2 - 0.3e1 / 0.20e2 * t76 * t77 * (t31 * t34 / t21 / t47 / 0.9e1 + t44 * t46 / t22 / t47 / r0 / 0.9e1 + t55 * t56 / t57 / r0 / 0.6e1) * t63)
  vrho_0_ = 0.2e1 * r0 * t100 + 0.2e1 * t70
  t120 = f.my_piecewise3(t2, 0, -0.3e1 / 0.20e2 * t76 * t77 * (-t31 / t32 * t33 * t36 / 0.24e2 - t41 * t43 * t45 * t49 / 0.24e2 - t55 * t32 * t58 / 0.16e2) * t63)
  vsigma_0_ = 0.2e1 * r0 * t120
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
  t22 = 0.1e1 / t21
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t31 = params.mu[0] * t26 / t29
  t32 = jnp.sqrt(s0)
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t32 * t33
  t36 = 0.1e1 / t21 / r0
  t41 = params.mu[1] * t25
  t42 = t29 ** 2
  t43 = 0.1e1 / t42
  t44 = t41 * t43
  t45 = t33 ** 2
  t46 = s0 * t45
  t47 = r0 ** 2
  t48 = t21 ** 2
  t50 = 0.1e1 / t48 / t47
  t56 = params.mu[2] / t28
  t57 = t32 * s0
  t58 = t47 ** 2
  t59 = 0.1e1 / t58
  t64 = jnp.exp(-t31 * t34 * t36 / 0.12e2 - t44 * t46 * t50 / 0.24e2 - t56 * t57 * t59 / 0.24e2)
  t67 = 0.1e1 + params.kappa * (0.1e1 - t64)
  t71 = t7 * t20
  t72 = t48 * params.kappa
  t74 = 0.1e1 / t21 / t47
  t78 = t47 * r0
  t80 = 0.1e1 / t48 / t78
  t85 = 0.1e1 / t58 / r0
  t89 = t31 * t34 * t74 / 0.9e1 + t44 * t46 * t80 / 0.9e1 + t56 * t57 * t85 / 0.6e1
  t90 = t89 * t64
  t95 = f.my_piecewise3(t2, 0, t7 * t20 * t22 * t67 / 0.10e2 - 0.3e1 / 0.20e2 * t71 * t72 * t90)
  t101 = t22 * params.kappa
  t125 = t89 ** 2
  t131 = f.my_piecewise3(t2, 0, -t7 * t20 * t36 * t67 / 0.30e2 - t71 * t101 * t90 / 0.5e1 - 0.3e1 / 0.20e2 * t71 * t72 * (-0.7e1 / 0.27e2 * t31 * t34 / t21 / t78 - 0.11e2 / 0.27e2 * t44 * t46 / t48 / t58 - 0.5e1 / 0.6e1 * t56 * t57 / t58 / t47) * t64 - 0.3e1 / 0.20e2 * t71 * t72 * t125 * t64)
  v2rho2_0_ = 0.2e1 * r0 * t131 + 0.4e1 * t95
  t134 = 0.1e1 / t32
  t135 = t134 * t33
  t139 = t43 * t45
  t146 = -t31 * t135 * t36 / 0.24e2 - t41 * t139 * t50 / 0.24e2 - t56 * t32 * t59 / 0.16e2
  t147 = t146 * t64
  t151 = f.my_piecewise3(t2, 0, -0.3e1 / 0.20e2 * t71 * t72 * t147)
  t176 = f.my_piecewise3(t2, 0, -t71 * t101 * t147 / 0.10e2 - 0.3e1 / 0.20e2 * t71 * t72 * (t31 * t135 * t74 / 0.18e2 + t41 * t139 * t80 / 0.9e1 + t56 * t32 * t85 / 0.4e1) * t64 - 0.3e1 / 0.20e2 * t7 * t20 * t48 * params.kappa * t146 * t90)
  v2rhosigma_0_ = 0.2e1 * r0 * t176 + 0.2e1 * t151
  t191 = t146 ** 2
  t197 = f.my_piecewise3(t2, 0, -0.3e1 / 0.20e2 * t71 * t72 * (t31 / t57 * t33 * t36 / 0.48e2 - t56 * t134 * t59 / 0.32e2) * t64 - 0.3e1 / 0.20e2 * t71 * t72 * t191 * t64)
  v2sigma2_0_ = 0.2e1 * r0 * t197
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
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t29 = jnp.pi ** 2
  t30 = t29 ** (0.1e1 / 0.3e1)
  t32 = params.mu[0] * t27 / t30
  t33 = jnp.sqrt(s0)
  t34 = 2 ** (0.1e1 / 0.3e1)
  t35 = t33 * t34
  t41 = t30 ** 2
  t43 = params.mu[1] * t26 / t41
  t44 = t34 ** 2
  t45 = s0 * t44
  t46 = r0 ** 2
  t47 = t21 ** 2
  t55 = params.mu[2] / t29
  t56 = t33 * s0
  t57 = t46 ** 2
  t63 = jnp.exp(-t32 * t35 * t23 / 0.12e2 - t43 * t45 / t47 / t46 / 0.24e2 - t55 * t56 / t57 / 0.24e2)
  t66 = 0.1e1 + params.kappa * (0.1e1 - t63)
  t70 = t7 * t20
  t72 = 0.1e1 / t21 * params.kappa
  t74 = 0.1e1 / t21 / t46
  t78 = t46 * r0
  t84 = t57 * r0
  t89 = t32 * t35 * t74 / 0.9e1 + t43 * t45 / t47 / t78 / 0.9e1 + t55 * t56 / t84 / 0.6e1
  t90 = t89 * t63
  t94 = t47 * params.kappa
  t110 = -0.7e1 / 0.27e2 * t32 * t35 / t21 / t78 - 0.11e2 / 0.27e2 * t43 * t45 / t47 / t57 - 0.5e1 / 0.6e1 * t55 * t56 / t57 / t46
  t111 = t110 * t63
  t115 = t89 ** 2
  t116 = t115 * t63
  t121 = f.my_piecewise3(t2, 0, -t7 * t20 * t23 * t66 / 0.30e2 - t70 * t72 * t90 / 0.5e1 - 0.3e1 / 0.20e2 * t70 * t94 * t111 - 0.3e1 / 0.20e2 * t70 * t94 * t116)
  t169 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t74 * t66 + t70 * t23 * params.kappa * t90 / 0.10e2 - 0.3e1 / 0.10e2 * t70 * t72 * t111 - 0.3e1 / 0.10e2 * t70 * t72 * t116 - 0.3e1 / 0.20e2 * t70 * t94 * (0.70e2 / 0.81e2 * t32 * t35 / t21 / t57 + 0.154e3 / 0.81e2 * t43 * t45 / t47 / t84 + 0.5e1 * t55 * t56 / t57 / t78) * t63 - 0.9e1 / 0.20e2 * t7 * t20 * t47 * params.kappa * t110 * t90 - 0.3e1 / 0.20e2 * t70 * t94 * t115 * t89 * t63)
  v3rho3_0_ = 0.2e1 * r0 * t169 + 0.6e1 * t121

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
  t27 = 6 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t33 = params.mu[0] * t28 / t31
  t34 = jnp.sqrt(s0)
  t35 = 2 ** (0.1e1 / 0.3e1)
  t36 = t34 * t35
  t38 = 0.1e1 / t22 / r0
  t44 = t31 ** 2
  t46 = params.mu[1] * t27 / t44
  t47 = t35 ** 2
  t48 = s0 * t47
  t49 = t22 ** 2
  t57 = params.mu[2] / t30
  t58 = t34 * s0
  t59 = t21 ** 2
  t65 = jnp.exp(-t33 * t36 * t38 / 0.12e2 - t46 * t48 / t49 / t21 / 0.24e2 - t57 * t58 / t59 / 0.24e2)
  t68 = 0.1e1 + params.kappa * (0.1e1 - t65)
  t72 = t7 * t20
  t73 = t38 * params.kappa
  t77 = t21 * r0
  t83 = t59 * r0
  t88 = t33 * t36 * t24 / 0.9e1 + t46 * t48 / t49 / t77 / 0.9e1 + t57 * t58 / t83 / 0.6e1
  t89 = t88 * t65
  t93 = 0.1e1 / t22
  t94 = t93 * params.kappa
  t96 = 0.1e1 / t22 / t77
  t105 = t59 * t21
  t110 = -0.7e1 / 0.27e2 * t33 * t36 * t96 - 0.11e2 / 0.27e2 * t46 * t48 / t49 / t59 - 0.5e1 / 0.6e1 * t57 * t58 / t105
  t111 = t110 * t65
  t115 = t88 ** 2
  t116 = t115 * t65
  t120 = t49 * params.kappa
  t136 = 0.70e2 / 0.81e2 * t33 * t36 / t22 / t59 + 0.154e3 / 0.81e2 * t46 * t48 / t49 / t83 + 0.5e1 * t57 * t58 / t59 / t77
  t137 = t136 * t65
  t142 = t7 * t20 * t49
  t143 = params.kappa * t110
  t144 = t143 * t89
  t148 = t115 * t88 * t65
  t153 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t24 * t68 + t72 * t73 * t89 / 0.10e2 - 0.3e1 / 0.10e2 * t72 * t94 * t111 - 0.3e1 / 0.10e2 * t72 * t94 * t116 - 0.3e1 / 0.20e2 * t72 * t120 * t137 - 0.9e1 / 0.20e2 * t142 * t144 - 0.3e1 / 0.20e2 * t72 * t120 * t148)
  t189 = t59 ** 2
  t203 = t110 ** 2
  t211 = t115 ** 2
  t216 = -0.14e2 / 0.135e3 * t7 * t20 * t96 * t68 - 0.8e1 / 0.45e2 * t72 * t24 * params.kappa * t89 + t72 * t73 * t111 / 0.5e1 + t72 * t73 * t116 / 0.5e1 - 0.2e1 / 0.5e1 * t72 * t94 * t137 - 0.6e1 / 0.5e1 * t7 * t20 * t93 * t144 - 0.2e1 / 0.5e1 * t72 * t94 * t148 - 0.3e1 / 0.20e2 * t72 * t120 * (-0.910e3 / 0.243e3 * t33 * t36 / t22 / t83 - 0.2618e4 / 0.243e3 * t46 * t48 / t49 / t105 - 0.35e2 * t57 * t58 / t189) * t65 - 0.3e1 / 0.5e1 * t142 * params.kappa * t136 * t89 - 0.9e1 / 0.20e2 * t72 * t120 * t203 * t65 - 0.9e1 / 0.10e2 * t142 * t143 * t116 - 0.3e1 / 0.20e2 * t72 * t120 * t211 * t65
  t217 = f.my_piecewise3(t2, 0, t216)
  v4rho4_0_ = 0.2e1 * r0 * t217 + 0.8e1 * t153

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
  t36 = 6 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = params.mu[0] * t37
  t39 = jnp.pi ** 2
  t40 = t39 ** (0.1e1 / 0.3e1)
  t41 = 0.1e1 / t40
  t42 = jnp.sqrt(s0)
  t43 = t41 * t42
  t44 = r0 ** (0.1e1 / 0.3e1)
  t51 = params.mu[1] * t36
  t52 = t40 ** 2
  t53 = 0.1e1 / t52
  t54 = t53 * s0
  t55 = r0 ** 2
  t56 = t44 ** 2
  t64 = params.mu[2] / t39
  t65 = t42 * s0
  t66 = t55 ** 2
  t72 = jnp.exp(-t38 * t43 / t44 / r0 / 0.12e2 - t51 * t54 / t56 / t55 / 0.24e2 - t64 * t65 / t66 / 0.48e2)
  t75 = 0.1e1 + params.kappa * (0.1e1 - t72)
  t79 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t81 = t80 * f.p.zeta_threshold
  t83 = f.my_piecewise3(t21, t81, t23 * t20)
  t84 = 0.1e1 / t32
  t88 = t6 * t83 * t84 * t75 / 0.10e2
  t89 = t6 * t83
  t90 = t33 * params.kappa
  t96 = t55 * r0
  t107 = t38 * t43 / t44 / t55 / 0.9e1 + t51 * t54 / t56 / t96 / 0.9e1 + t64 * t65 / t66 / r0 / 0.12e2
  t108 = t107 * t72
  t109 = t90 * t108
  t113 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t33 * t75 + t88 - 0.3e1 / 0.20e2 * t89 * t109)
  t115 = r1 <= f.p.dens_threshold
  t116 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t117 = 0.1e1 + t116
  t118 = t117 <= f.p.zeta_threshold
  t119 = t117 ** (0.1e1 / 0.3e1)
  t120 = t119 ** 2
  t122 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t125 = f.my_piecewise3(t118, 0, 0.5e1 / 0.3e1 * t120 * t122)
  t127 = jnp.sqrt(s2)
  t128 = t41 * t127
  t129 = r1 ** (0.1e1 / 0.3e1)
  t135 = t53 * s2
  t136 = r1 ** 2
  t137 = t129 ** 2
  t143 = t127 * s2
  t144 = t136 ** 2
  t150 = jnp.exp(-t38 * t128 / t129 / r1 / 0.12e2 - t51 * t135 / t137 / t136 / 0.24e2 - t64 * t143 / t144 / 0.48e2)
  t153 = 0.1e1 + params.kappa * (0.1e1 - t150)
  t158 = f.my_piecewise3(t118, t81, t120 * t117)
  t162 = t6 * t158 * t84 * t153 / 0.10e2
  t164 = f.my_piecewise3(t115, 0, 0.3e1 / 0.20e2 * t6 * t125 * t33 * t153 + t162)
  t166 = 0.1e1 / t22
  t167 = t28 ** 2
  t172 = t17 / t24 / t7
  t174 = -0.2e1 * t25 + 0.2e1 * t172
  t175 = f.my_piecewise5(t11, 0, t15, 0, t174)
  t179 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t166 * t167 + 0.5e1 / 0.3e1 * t23 * t175)
  t186 = t6 * t31 * t84 * t75
  t192 = 0.1e1 / t32 / t7
  t196 = t6 * t83 * t192 * t75 / 0.30e2
  t197 = t84 * params.kappa
  t199 = t89 * t197 * t108
  t221 = t107 ** 2
  t227 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t179 * t33 * t75 + t186 / 0.5e1 - 0.3e1 / 0.10e2 * t6 * t31 * t109 - t196 - t199 / 0.5e1 - 0.3e1 / 0.20e2 * t89 * t90 * (-0.7e1 / 0.27e2 * t38 * t43 / t44 / t96 - 0.11e2 / 0.27e2 * t51 * t54 / t56 / t66 - 0.5e1 / 0.12e2 * t64 * t65 / t66 / t55) * t72 - 0.3e1 / 0.20e2 * t89 * t90 * t221 * t72)
  t228 = 0.1e1 / t119
  t229 = t122 ** 2
  t233 = f.my_piecewise5(t15, 0, t11, 0, -t174)
  t237 = f.my_piecewise3(t118, 0, 0.10e2 / 0.9e1 * t228 * t229 + 0.5e1 / 0.3e1 * t120 * t233)
  t244 = t6 * t125 * t84 * t153
  t249 = t6 * t158 * t192 * t153 / 0.30e2
  t251 = f.my_piecewise3(t115, 0, 0.3e1 / 0.20e2 * t6 * t237 * t33 * t153 + t244 / 0.5e1 - t249)
  d11 = 0.2e1 * t113 + 0.2e1 * t164 + t7 * (t227 + t251)
  t254 = -t8 - t26
  t255 = f.my_piecewise5(t11, 0, t15, 0, t254)
  t258 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t255)
  t264 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t258 * t33 * t75 + t88)
  t266 = f.my_piecewise5(t15, 0, t11, 0, -t254)
  t269 = f.my_piecewise3(t118, 0, 0.5e1 / 0.3e1 * t120 * t266)
  t274 = t6 * t158
  t280 = t136 * r1
  t291 = t38 * t128 / t129 / t136 / 0.9e1 + t51 * t135 / t137 / t280 / 0.9e1 + t64 * t143 / t144 / r1 / 0.12e2
  t292 = t291 * t150
  t293 = t90 * t292
  t297 = f.my_piecewise3(t115, 0, 0.3e1 / 0.20e2 * t6 * t269 * t33 * t153 + t162 - 0.3e1 / 0.20e2 * t274 * t293)
  t301 = 0.2e1 * t172
  t302 = f.my_piecewise5(t11, 0, t15, 0, t301)
  t306 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t166 * t255 * t28 + 0.5e1 / 0.3e1 * t23 * t302)
  t313 = t6 * t258 * t84 * t75
  t321 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t306 * t33 * t75 + t313 / 0.10e2 - 0.3e1 / 0.20e2 * t6 * t258 * t109 + t186 / 0.10e2 - t196 - t199 / 0.10e2)
  t325 = f.my_piecewise5(t15, 0, t11, 0, -t301)
  t329 = f.my_piecewise3(t118, 0, 0.10e2 / 0.9e1 * t228 * t266 * t122 + 0.5e1 / 0.3e1 * t120 * t325)
  t336 = t6 * t269 * t84 * t153
  t343 = t274 * t197 * t292
  t346 = f.my_piecewise3(t115, 0, 0.3e1 / 0.20e2 * t6 * t329 * t33 * t153 + t336 / 0.10e2 + t244 / 0.10e2 - t249 - 0.3e1 / 0.20e2 * t6 * t125 * t293 - t343 / 0.10e2)
  d12 = t113 + t164 + t264 + t297 + t7 * (t321 + t346)
  t351 = t255 ** 2
  t355 = 0.2e1 * t25 + 0.2e1 * t172
  t356 = f.my_piecewise5(t11, 0, t15, 0, t355)
  t360 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t166 * t351 + 0.5e1 / 0.3e1 * t23 * t356)
  t367 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t360 * t33 * t75 + t313 / 0.5e1 - t196)
  t368 = t266 ** 2
  t372 = f.my_piecewise5(t15, 0, t11, 0, -t355)
  t376 = f.my_piecewise3(t118, 0, 0.10e2 / 0.9e1 * t228 * t368 + 0.5e1 / 0.3e1 * t120 * t372)
  t406 = t291 ** 2
  t412 = f.my_piecewise3(t115, 0, 0.3e1 / 0.20e2 * t6 * t376 * t33 * t153 + t336 / 0.5e1 - 0.3e1 / 0.10e2 * t6 * t269 * t293 - t249 - t343 / 0.5e1 - 0.3e1 / 0.20e2 * t274 * t90 * (-0.7e1 / 0.27e2 * t38 * t128 / t129 / t280 - 0.11e2 / 0.27e2 * t51 * t135 / t137 / t144 - 0.5e1 / 0.12e2 * t64 * t143 / t144 / t136) * t150 - 0.3e1 / 0.20e2 * t274 * t90 * t406 * t150)
  d22 = 0.2e1 * t264 + 0.2e1 * t297 + t7 * (t367 + t412)
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
  t47 = 6 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = params.mu[0] * t48
  t50 = jnp.pi ** 2
  t51 = t50 ** (0.1e1 / 0.3e1)
  t52 = 0.1e1 / t51
  t53 = jnp.sqrt(s0)
  t54 = t52 * t53
  t55 = r0 ** (0.1e1 / 0.3e1)
  t62 = params.mu[1] * t47
  t63 = t51 ** 2
  t64 = 0.1e1 / t63
  t65 = t64 * s0
  t66 = r0 ** 2
  t67 = t55 ** 2
  t75 = params.mu[2] / t50
  t76 = t53 * s0
  t77 = t66 ** 2
  t83 = jnp.exp(-t49 * t54 / t55 / r0 / 0.12e2 - t62 * t65 / t67 / t66 / 0.24e2 - t75 * t76 / t77 / 0.48e2)
  t86 = 0.1e1 + params.kappa * (0.1e1 - t83)
  t92 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t93 = 0.1e1 / t43
  t98 = t6 * t92
  t99 = t44 * params.kappa
  t105 = t66 * r0
  t111 = t77 * r0
  t116 = t49 * t54 / t55 / t66 / 0.9e1 + t62 * t65 / t67 / t105 / 0.9e1 + t75 * t76 / t111 / 0.12e2
  t117 = t116 * t83
  t118 = t99 * t117
  t121 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t122 = t121 ** 2
  t123 = t122 * f.p.zeta_threshold
  t125 = f.my_piecewise3(t21, t123, t32 * t20)
  t127 = 0.1e1 / t43 / t7
  t132 = t6 * t125
  t133 = t93 * params.kappa
  t134 = t133 * t117
  t152 = -0.7e1 / 0.27e2 * t49 * t54 / t55 / t105 - 0.11e2 / 0.27e2 * t62 * t65 / t67 / t77 - 0.5e1 / 0.12e2 * t75 * t76 / t77 / t66
  t153 = t152 * t83
  t154 = t99 * t153
  t157 = t116 ** 2
  t158 = t157 * t83
  t159 = t99 * t158
  t163 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t42 * t44 * t86 + t6 * t92 * t93 * t86 / 0.5e1 - 0.3e1 / 0.10e2 * t98 * t118 - t6 * t125 * t127 * t86 / 0.30e2 - t132 * t134 / 0.5e1 - 0.3e1 / 0.20e2 * t132 * t154 - 0.3e1 / 0.20e2 * t132 * t159)
  t165 = r1 <= f.p.dens_threshold
  t166 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t167 = 0.1e1 + t166
  t168 = t167 <= f.p.zeta_threshold
  t169 = t167 ** (0.1e1 / 0.3e1)
  t170 = 0.1e1 / t169
  t172 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t173 = t172 ** 2
  t176 = t169 ** 2
  t178 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t182 = f.my_piecewise3(t168, 0, 0.10e2 / 0.9e1 * t170 * t173 + 0.5e1 / 0.3e1 * t176 * t178)
  t184 = jnp.sqrt(s2)
  t186 = r1 ** (0.1e1 / 0.3e1)
  t193 = r1 ** 2
  t194 = t186 ** 2
  t201 = t193 ** 2
  t207 = jnp.exp(-t49 * t52 * t184 / t186 / r1 / 0.12e2 - t62 * t64 * s2 / t194 / t193 / 0.24e2 - t75 * t184 * s2 / t201 / 0.48e2)
  t210 = 0.1e1 + params.kappa * (0.1e1 - t207)
  t216 = f.my_piecewise3(t168, 0, 0.5e1 / 0.3e1 * t176 * t172)
  t222 = f.my_piecewise3(t168, t123, t176 * t167)
  t228 = f.my_piecewise3(t165, 0, 0.3e1 / 0.20e2 * t6 * t182 * t44 * t210 + t6 * t216 * t93 * t210 / 0.5e1 - t6 * t222 * t127 * t210 / 0.30e2)
  t288 = t24 ** 2
  t292 = 0.6e1 * t34 - 0.6e1 * t17 / t288
  t293 = f.my_piecewise5(t11, 0, t15, 0, t292)
  t297 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t293)
  t311 = 0.1e1 / t43 / t24
  t316 = -0.9e1 / 0.20e2 * t6 * t42 * t118 - 0.3e1 / 0.5e1 * t98 * t134 - 0.9e1 / 0.20e2 * t98 * t154 + t132 * t127 * params.kappa * t117 / 0.10e2 - 0.3e1 / 0.10e2 * t132 * t133 * t153 - 0.3e1 / 0.20e2 * t132 * t99 * (0.70e2 / 0.81e2 * t49 * t54 / t55 / t77 + 0.154e3 / 0.81e2 * t62 * t65 / t67 / t111 + 0.5e1 / 0.2e1 * t75 * t76 / t77 / t105) * t83 - 0.9e1 / 0.20e2 * t98 * t159 - 0.3e1 / 0.10e2 * t132 * t133 * t158 - 0.9e1 / 0.20e2 * t6 * t125 * t44 * params.kappa * t152 * t117 - 0.3e1 / 0.20e2 * t132 * t99 * t157 * t116 * t83 + 0.3e1 / 0.20e2 * t6 * t297 * t44 * t86 + 0.3e1 / 0.10e2 * t6 * t42 * t93 * t86 - t6 * t92 * t127 * t86 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t125 * t311 * t86
  t317 = f.my_piecewise3(t1, 0, t316)
  t327 = f.my_piecewise5(t15, 0, t11, 0, -t292)
  t331 = f.my_piecewise3(t168, 0, -0.10e2 / 0.27e2 / t169 / t167 * t173 * t172 + 0.10e2 / 0.3e1 * t170 * t172 * t178 + 0.5e1 / 0.3e1 * t176 * t327)
  t349 = f.my_piecewise3(t165, 0, 0.3e1 / 0.20e2 * t6 * t331 * t44 * t210 + 0.3e1 / 0.10e2 * t6 * t182 * t93 * t210 - t6 * t216 * t127 * t210 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t222 * t311 * t210)
  d111 = 0.3e1 * t163 + 0.3e1 * t228 + t7 * (t317 + t349)

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
  t23 = 0.1e1 / t22
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t27 = -t17 * t25 + t8
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t29 = t28 ** 2
  t32 = t22 ** 2
  t33 = t24 * t7
  t34 = 0.1e1 / t33
  t37 = 0.2e1 * t17 * t34 - 0.2e1 * t25
  t38 = f.my_piecewise5(t11, 0, t15, 0, t37)
  t42 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t23 * t29 + 0.5e1 / 0.3e1 * t32 * t38)
  t43 = t6 * t42
  t44 = t7 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = t45 * params.kappa
  t48 = 6 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = params.mu[0] * t49
  t51 = jnp.pi ** 2
  t52 = t51 ** (0.1e1 / 0.3e1)
  t53 = 0.1e1 / t52
  t54 = jnp.sqrt(s0)
  t55 = t53 * t54
  t56 = r0 ** 2
  t57 = r0 ** (0.1e1 / 0.3e1)
  t64 = params.mu[1] * t48
  t65 = t52 ** 2
  t66 = 0.1e1 / t65
  t67 = t66 * s0
  t68 = t56 * r0
  t69 = t57 ** 2
  t77 = params.mu[2] / t51
  t78 = t54 * s0
  t79 = t56 ** 2
  t80 = t79 * r0
  t85 = t50 * t55 / t57 / t56 / 0.9e1 + t64 * t67 / t69 / t68 / 0.9e1 + t77 * t78 / t80 / 0.12e2
  t101 = jnp.exp(-t50 * t55 / t57 / r0 / 0.12e2 - t64 * t67 / t69 / t56 / 0.24e2 - t77 * t78 / t79 / 0.48e2)
  t102 = t85 * t101
  t103 = t46 * t102
  t108 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t109 = t6 * t108
  t110 = 0.1e1 / t44
  t111 = t110 * params.kappa
  t112 = t111 * t102
  t125 = t79 * t56
  t130 = -0.7e1 / 0.27e2 * t50 * t55 / t57 / t68 - 0.11e2 / 0.27e2 * t64 * t67 / t69 / t79 - 0.5e1 / 0.12e2 * t77 * t78 / t125
  t131 = t130 * t101
  t132 = t46 * t131
  t135 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t136 = t135 ** 2
  t137 = t136 * f.p.zeta_threshold
  t139 = f.my_piecewise3(t21, t137, t32 * t20)
  t140 = t6 * t139
  t142 = 0.1e1 / t44 / t7
  t143 = t142 * params.kappa
  t144 = t143 * t102
  t147 = t111 * t131
  t165 = 0.70e2 / 0.81e2 * t50 * t55 / t57 / t79 + 0.154e3 / 0.81e2 * t64 * t67 / t69 / t80 + 0.5e1 / 0.2e1 * t77 * t78 / t79 / t68
  t166 = t165 * t101
  t167 = t46 * t166
  t170 = t85 ** 2
  t171 = t170 * t101
  t172 = t111 * t171
  t176 = t6 * t139 * t45
  t177 = params.kappa * t130
  t178 = t177 * t102
  t182 = t170 * t85 * t101
  t183 = t46 * t182
  t186 = t46 * t171
  t190 = 0.1e1 / t22 / t20
  t194 = t23 * t28
  t197 = t24 ** 2
  t198 = 0.1e1 / t197
  t201 = -0.6e1 * t17 * t198 + 0.6e1 * t34
  t202 = f.my_piecewise5(t11, 0, t15, 0, t201)
  t206 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 * t190 * t29 * t28 + 0.10e2 / 0.3e1 * t194 * t38 + 0.5e1 / 0.3e1 * t32 * t202)
  t210 = 0.1e1 + params.kappa * (0.1e1 - t101)
  t223 = 0.1e1 / t44 / t24
  t228 = -0.9e1 / 0.20e2 * t43 * t103 - 0.3e1 / 0.5e1 * t109 * t112 - 0.9e1 / 0.20e2 * t109 * t132 + t140 * t144 / 0.10e2 - 0.3e1 / 0.10e2 * t140 * t147 - 0.3e1 / 0.20e2 * t140 * t167 - 0.3e1 / 0.10e2 * t140 * t172 - 0.9e1 / 0.20e2 * t176 * t178 - 0.3e1 / 0.20e2 * t140 * t183 - 0.9e1 / 0.20e2 * t109 * t186 + 0.3e1 / 0.20e2 * t6 * t206 * t45 * t210 + 0.3e1 / 0.10e2 * t6 * t42 * t110 * t210 - t6 * t108 * t142 * t210 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t139 * t223 * t210
  t229 = f.my_piecewise3(t1, 0, t228)
  t231 = r1 <= f.p.dens_threshold
  t232 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t233 = 0.1e1 + t232
  t234 = t233 <= f.p.zeta_threshold
  t235 = t233 ** (0.1e1 / 0.3e1)
  t237 = 0.1e1 / t235 / t233
  t239 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t240 = t239 ** 2
  t244 = 0.1e1 / t235
  t245 = t244 * t239
  t247 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t250 = t235 ** 2
  t252 = f.my_piecewise5(t15, 0, t11, 0, -t201)
  t256 = f.my_piecewise3(t234, 0, -0.10e2 / 0.27e2 * t237 * t240 * t239 + 0.10e2 / 0.3e1 * t245 * t247 + 0.5e1 / 0.3e1 * t250 * t252)
  t258 = jnp.sqrt(s2)
  t260 = r1 ** (0.1e1 / 0.3e1)
  t267 = r1 ** 2
  t268 = t260 ** 2
  t275 = t267 ** 2
  t281 = jnp.exp(-t50 * t53 * t258 / t260 / r1 / 0.12e2 - t64 * t66 * s2 / t268 / t267 / 0.24e2 - t77 * t258 * s2 / t275 / 0.48e2)
  t284 = 0.1e1 + params.kappa * (0.1e1 - t281)
  t293 = f.my_piecewise3(t234, 0, 0.10e2 / 0.9e1 * t244 * t240 + 0.5e1 / 0.3e1 * t250 * t247)
  t300 = f.my_piecewise3(t234, 0, 0.5e1 / 0.3e1 * t250 * t239)
  t306 = f.my_piecewise3(t234, t137, t250 * t233)
  t312 = f.my_piecewise3(t231, 0, 0.3e1 / 0.20e2 * t6 * t256 * t45 * t284 + 0.3e1 / 0.10e2 * t6 * t293 * t110 * t284 - t6 * t300 * t142 * t284 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t306 * t223 * t284)
  t314 = t20 ** 2
  t317 = t29 ** 2
  t323 = t38 ** 2
  t332 = -0.24e2 * t198 + 0.24e2 * t17 / t197 / t7
  t333 = f.my_piecewise5(t11, 0, t15, 0, t332)
  t337 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t314 * t317 - 0.20e2 / 0.9e1 * t190 * t29 * t38 + 0.10e2 / 0.3e1 * t23 * t323 + 0.40e2 / 0.9e1 * t194 * t202 + 0.5e1 / 0.3e1 * t32 * t333)
  t355 = 0.1e1 / t44 / t33
  t385 = t79 ** 2
  t402 = 0.3e1 / 0.20e2 * t6 * t337 * t45 * t210 + 0.2e1 / 0.5e1 * t6 * t206 * t110 * t210 - t6 * t42 * t142 * t210 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t108 * t223 * t210 - 0.14e2 / 0.135e3 * t6 * t139 * t355 * t210 - 0.9e1 / 0.5e1 * t6 * t108 * t45 * t178 - 0.6e1 / 0.5e1 * t6 * t139 * t110 * t178 - 0.3e1 / 0.5e1 * t176 * params.kappa * t165 * t102 - 0.9e1 / 0.10e2 * t176 * t177 * t171 - 0.3e1 / 0.20e2 * t140 * t46 * (-0.910e3 / 0.243e3 * t50 * t55 / t57 / t80 - 0.2618e4 / 0.243e3 * t64 * t67 / t69 / t125 - 0.35e2 / 0.2e1 * t77 * t78 / t385) * t101 - 0.3e1 / 0.5e1 * t109 * t183 - 0.3e1 / 0.5e1 * t6 * t206 * t103 - 0.6e1 / 0.5e1 * t43 * t112
  t405 = t170 ** 2
  t424 = t130 ** 2
  t441 = -0.9e1 / 0.10e2 * t43 * t186 - 0.3e1 / 0.20e2 * t140 * t46 * t405 * t101 + 0.2e1 / 0.5e1 * t109 * t144 - 0.6e1 / 0.5e1 * t109 * t172 - 0.8e1 / 0.45e2 * t140 * t223 * params.kappa * t102 + t140 * t143 * t171 / 0.5e1 - 0.2e1 / 0.5e1 * t140 * t111 * t182 - 0.9e1 / 0.20e2 * t140 * t46 * t424 * t101 - 0.9e1 / 0.10e2 * t43 * t132 - 0.6e1 / 0.5e1 * t109 * t147 - 0.3e1 / 0.5e1 * t109 * t167 + t140 * t143 * t131 / 0.5e1 - 0.2e1 / 0.5e1 * t140 * t111 * t166
  t443 = f.my_piecewise3(t1, 0, t402 + t441)
  t444 = t233 ** 2
  t447 = t240 ** 2
  t453 = t247 ** 2
  t459 = f.my_piecewise5(t15, 0, t11, 0, -t332)
  t463 = f.my_piecewise3(t234, 0, 0.40e2 / 0.81e2 / t235 / t444 * t447 - 0.20e2 / 0.9e1 * t237 * t240 * t247 + 0.10e2 / 0.3e1 * t244 * t453 + 0.40e2 / 0.9e1 * t245 * t252 + 0.5e1 / 0.3e1 * t250 * t459)
  t485 = f.my_piecewise3(t231, 0, 0.3e1 / 0.20e2 * t6 * t463 * t45 * t284 + 0.2e1 / 0.5e1 * t6 * t256 * t110 * t284 - t6 * t293 * t142 * t284 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t300 * t223 * t284 - 0.14e2 / 0.135e3 * t6 * t306 * t355 * t284)
  d1111 = 0.4e1 * t229 + 0.4e1 * t312 + t7 * (t443 + t485)

  res = {'v4rho4': d1111}
  return res
