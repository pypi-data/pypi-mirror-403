"""Generated from gga_k_lgap_ge.mpl."""

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

  lgap_ge_f0 = lambda s: 1 + jnp.sum(jnp.array([params_mu[i] * s ** i for i in range(1, 3 + 1)]), axis=0)

  lgap_ge_f = lambda x: lgap_ge_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lgap_ge_f, rs, z, xs0, xs1)

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

  lgap_ge_f0 = lambda s: 1 + jnp.sum(jnp.array([params_mu[i] * s ** i for i in range(1, 3 + 1)]), axis=0)

  lgap_ge_f = lambda x: lgap_ge_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lgap_ge_f, rs, z, xs0, xs1)

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

  lgap_ge_f0 = lambda s: 1 + jnp.sum(jnp.array([params_mu[i] * s ** i for i in range(1, 3 + 1)]), axis=0)

  lgap_ge_f = lambda x: lgap_ge_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lgap_ge_f, rs, z, xs0, xs1)

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
  t68 = 0.1e1 + t35 * t40 * t43 / 0.12e2 + t48 * t51 * t55 / 0.24e2 + t61 * t62 * t64 / 0.48e2
  t72 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t68)
  t73 = r1 <= f.p.dens_threshold
  t74 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t75 = 0.1e1 + t74
  t76 = t75 <= f.p.zeta_threshold
  t77 = t75 ** (0.1e1 / 0.3e1)
  t78 = t77 ** 2
  t80 = f.my_piecewise3(t76, t24, t78 * t75)
  t81 = t80 * t30
  t82 = jnp.sqrt(s2)
  t83 = t38 * t82
  t84 = r1 ** (0.1e1 / 0.3e1)
  t86 = 0.1e1 / t84 / r1
  t90 = t50 * s2
  t91 = r1 ** 2
  t92 = t84 ** 2
  t94 = 0.1e1 / t92 / t91
  t98 = t82 * s2
  t99 = t91 ** 2
  t100 = 0.1e1 / t99
  t104 = 0.1e1 + t35 * t83 * t86 / 0.12e2 + t48 * t90 * t94 / 0.24e2 + t61 * t98 * t100 / 0.48e2
  t108 = f.my_piecewise3(t73, 0, 0.3e1 / 0.20e2 * t6 * t81 * t104)
  t109 = t7 ** 2
  t111 = t17 / t109
  t112 = t8 - t111
  t113 = f.my_piecewise5(t11, 0, t15, 0, t112)
  t116 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t113)
  t121 = 0.1e1 / t29
  t125 = t6 * t28 * t121 * t68 / 0.10e2
  t147 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t116 * t30 * t68 + t125 + 0.3e1 / 0.20e2 * t6 * t31 * (-t35 * t40 / t41 / t52 / 0.9e1 - t48 * t51 / t53 / t52 / r0 / 0.9e1 - t61 * t62 / t63 / r0 / 0.12e2))
  t149 = f.my_piecewise5(t15, 0, t11, 0, -t112)
  t152 = f.my_piecewise3(t76, 0, 0.5e1 / 0.3e1 * t78 * t149)
  t160 = t6 * t80 * t121 * t104 / 0.10e2
  t162 = f.my_piecewise3(t73, 0, 0.3e1 / 0.20e2 * t6 * t152 * t30 * t104 + t160)
  vrho_0_ = t72 + t108 + t7 * (t147 + t162)
  t165 = -t8 - t111
  t166 = f.my_piecewise5(t11, 0, t15, 0, t165)
  t169 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t166)
  t175 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t169 * t30 * t68 + t125)
  t177 = f.my_piecewise5(t15, 0, t11, 0, -t165)
  t180 = f.my_piecewise3(t76, 0, 0.5e1 / 0.3e1 * t78 * t177)
  t206 = f.my_piecewise3(t73, 0, 0.3e1 / 0.20e2 * t6 * t180 * t30 * t104 + t160 + 0.3e1 / 0.20e2 * t6 * t81 * (-t35 * t83 / t84 / t91 / 0.9e1 - t48 * t90 / t92 / t91 / r1 / 0.9e1 - t61 * t98 / t99 / r1 / 0.12e2))
  vrho_1_ = t72 + t108 + t7 * (t175 + t206)
  t224 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (t35 * t38 / t39 * t43 / 0.24e2 + t48 * t50 * t55 / 0.24e2 + t61 * t39 * t64 / 0.32e2))
  vsigma_0_ = t7 * t224
  vsigma_1_ = 0.0e0
  t240 = f.my_piecewise3(t73, 0, 0.3e1 / 0.20e2 * t6 * t81 * (t35 * t38 / t82 * t86 / 0.24e2 + t48 * t50 * t94 / 0.24e2 + t61 * t82 * t100 / 0.32e2))
  vsigma_2_ = t7 * t240
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

  lgap_ge_f0 = lambda s: 1 + jnp.sum(jnp.array([params_mu[i] * s ** i for i in range(1, 3 + 1)]), axis=0)

  lgap_ge_f = lambda x: lgap_ge_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lgap_ge_f, rs, z, xs0, xs1)

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
  t62 = 0.1e1 + t31 * t34 * t36 / 0.12e2 + t44 * t46 * t49 / 0.24e2 + t55 * t56 * t58 / 0.24e2
  t66 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t62)
  t93 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t62 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-t31 * t34 / t21 / t47 / 0.9e1 - t44 * t46 / t22 / t47 / r0 / 0.9e1 - t55 * t56 / t57 / r0 / 0.6e1))
  vrho_0_ = 0.2e1 * r0 * t93 + 0.2e1 * t66
  t112 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (t31 / t32 * t33 * t36 / 0.24e2 + t41 * t43 * t45 * t49 / 0.24e2 + t55 * t32 * t58 / 0.16e2))
  vsigma_0_ = 0.2e1 * r0 * t112
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
  t63 = 0.1e1 + t31 * t34 * t36 / 0.12e2 + t44 * t46 * t50 / 0.24e2 + t56 * t57 * t59 / 0.24e2
  t67 = t20 * t48
  t69 = 0.1e1 / t21 / t47
  t73 = t47 * r0
  t75 = 0.1e1 / t48 / t73
  t80 = 0.1e1 / t58 / r0
  t84 = -t31 * t34 * t69 / 0.9e1 - t44 * t46 * t75 / 0.9e1 - t56 * t57 * t80 / 0.6e1
  t89 = f.my_piecewise3(t2, 0, t7 * t23 * t63 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t67 * t84)
  t118 = f.my_piecewise3(t2, 0, -t7 * t20 * t36 * t63 / 0.30e2 + t7 * t23 * t84 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t67 * (0.7e1 / 0.27e2 * t31 * t34 / t21 / t73 + 0.11e2 / 0.27e2 * t44 * t46 / t48 / t58 + 0.5e1 / 0.6e1 * t56 * t57 / t58 / t47))
  v2rho2_0_ = 0.2e1 * r0 * t118 + 0.4e1 * t89
  t121 = 0.1e1 / t32
  t122 = t121 * t33
  t126 = t43 * t45
  t133 = t31 * t122 * t36 / 0.24e2 + t41 * t126 * t50 / 0.24e2 + t56 * t32 * t59 / 0.16e2
  t137 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t67 * t133)
  t155 = f.my_piecewise3(t2, 0, t7 * t23 * t133 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t67 * (-t31 * t122 * t69 / 0.18e2 - t41 * t126 * t75 / 0.9e1 - t56 * t32 * t80 / 0.4e1))
  v2rhosigma_0_ = 0.2e1 * r0 * t155 + 0.2e1 * t137
  t170 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t67 * (-t31 / t57 * t33 * t36 / 0.48e2 + t56 * t121 * t59 / 0.32e2))
  v2sigma2_0_ = 0.2e1 * r0 * t170
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
  t62 = 0.1e1 + t32 * t35 * t23 / 0.12e2 + t43 * t45 / t47 / t46 / 0.24e2 + t55 * t56 / t57 / 0.24e2
  t67 = t20 / t21
  t69 = 0.1e1 / t21 / t46
  t73 = t46 * r0
  t79 = t57 * r0
  t84 = -t32 * t35 * t69 / 0.9e1 - t43 * t45 / t47 / t73 / 0.9e1 - t55 * t56 / t79 / 0.6e1
  t88 = t20 * t47
  t104 = 0.7e1 / 0.27e2 * t32 * t35 / t21 / t73 + 0.11e2 / 0.27e2 * t43 * t45 / t47 / t57 + 0.5e1 / 0.6e1 * t55 * t56 / t57 / t46
  t109 = f.my_piecewise3(t2, 0, -t7 * t24 * t62 / 0.30e2 + t7 * t67 * t84 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t88 * t104)
  t141 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t69 * t62 - t7 * t24 * t84 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t67 * t104 + 0.3e1 / 0.20e2 * t7 * t88 * (-0.70e2 / 0.81e2 * t32 * t35 / t21 / t57 - 0.154e3 / 0.81e2 * t43 * t45 / t47 / t79 - 0.5e1 * t55 * t56 / t57 / t73))
  v3rho3_0_ = 0.2e1 * r0 * t141 + 0.6e1 * t109

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
  t64 = 0.1e1 + t33 * t36 * t38 / 0.12e2 + t46 * t48 / t49 / t21 / 0.24e2 + t57 * t58 / t59 / 0.24e2
  t68 = t20 * t38
  t72 = t21 * r0
  t78 = t59 * r0
  t83 = -t33 * t36 * t24 / 0.9e1 - t46 * t48 / t49 / t72 / 0.9e1 - t57 * t58 / t78 / 0.6e1
  t88 = t20 / t22
  t90 = 0.1e1 / t22 / t72
  t99 = t59 * t21
  t104 = 0.7e1 / 0.27e2 * t33 * t36 * t90 + 0.11e2 / 0.27e2 * t46 * t48 / t49 / t59 + 0.5e1 / 0.6e1 * t57 * t58 / t99
  t108 = t20 * t49
  t124 = -0.70e2 / 0.81e2 * t33 * t36 / t22 / t59 - 0.154e3 / 0.81e2 * t46 * t48 / t49 / t78 - 0.5e1 * t57 * t58 / t59 / t72
  t129 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t64 - t7 * t68 * t83 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t88 * t104 + 0.3e1 / 0.20e2 * t7 * t108 * t124)
  t154 = t59 ** 2
  t164 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t90 * t64 + 0.8e1 / 0.45e2 * t7 * t25 * t83 - t7 * t68 * t104 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t88 * t124 + 0.3e1 / 0.20e2 * t7 * t108 * (0.910e3 / 0.243e3 * t33 * t36 / t22 / t78 + 0.2618e4 / 0.243e3 * t46 * t48 / t49 / t99 + 0.35e2 * t57 * t58 / t154))
  v4rho4_0_ = 0.2e1 * r0 * t164 + 0.8e1 * t129

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
  t71 = 0.1e1 + t38 * t43 / t44 / r0 / 0.12e2 + t51 * t54 / t56 / t55 / 0.24e2 + t64 * t65 / t66 / 0.48e2
  t75 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t76 = t75 ** 2
  t77 = t76 * f.p.zeta_threshold
  t79 = f.my_piecewise3(t21, t77, t23 * t20)
  t80 = 0.1e1 / t32
  t81 = t79 * t80
  t84 = t6 * t81 * t71 / 0.10e2
  t85 = t79 * t33
  t91 = t55 * r0
  t102 = -t38 * t43 / t44 / t55 / 0.9e1 - t51 * t54 / t56 / t91 / 0.9e1 - t64 * t65 / t66 / r0 / 0.12e2
  t107 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t71 + t84 + 0.3e1 / 0.20e2 * t6 * t85 * t102)
  t109 = r1 <= f.p.dens_threshold
  t110 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t111 = 0.1e1 + t110
  t112 = t111 <= f.p.zeta_threshold
  t113 = t111 ** (0.1e1 / 0.3e1)
  t114 = t113 ** 2
  t116 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t119 = f.my_piecewise3(t112, 0, 0.5e1 / 0.3e1 * t114 * t116)
  t120 = t119 * t33
  t121 = jnp.sqrt(s2)
  t122 = t41 * t121
  t123 = r1 ** (0.1e1 / 0.3e1)
  t129 = t53 * s2
  t130 = r1 ** 2
  t131 = t123 ** 2
  t137 = t121 * s2
  t138 = t130 ** 2
  t143 = 0.1e1 + t38 * t122 / t123 / r1 / 0.12e2 + t51 * t129 / t131 / t130 / 0.24e2 + t64 * t137 / t138 / 0.48e2
  t148 = f.my_piecewise3(t112, t77, t114 * t111)
  t149 = t148 * t80
  t152 = t6 * t149 * t143 / 0.10e2
  t154 = f.my_piecewise3(t109, 0, 0.3e1 / 0.20e2 * t6 * t120 * t143 + t152)
  t156 = 0.1e1 / t22
  t157 = t28 ** 2
  t162 = t17 / t24 / t7
  t164 = -0.2e1 * t25 + 0.2e1 * t162
  t165 = f.my_piecewise5(t11, 0, t15, 0, t164)
  t169 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t156 * t157 + 0.5e1 / 0.3e1 * t23 * t165)
  t176 = t6 * t31 * t80 * t71
  t182 = 0.1e1 / t32 / t7
  t186 = t6 * t79 * t182 * t71 / 0.30e2
  t188 = t6 * t81 * t102
  t210 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t169 * t33 * t71 + t176 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t102 - t186 + t188 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t85 * (0.7e1 / 0.27e2 * t38 * t43 / t44 / t91 + 0.11e2 / 0.27e2 * t51 * t54 / t56 / t66 + 0.5e1 / 0.12e2 * t64 * t65 / t66 / t55))
  t211 = 0.1e1 / t113
  t212 = t116 ** 2
  t216 = f.my_piecewise5(t15, 0, t11, 0, -t164)
  t220 = f.my_piecewise3(t112, 0, 0.10e2 / 0.9e1 * t211 * t212 + 0.5e1 / 0.3e1 * t114 * t216)
  t227 = t6 * t119 * t80 * t143
  t232 = t6 * t148 * t182 * t143 / 0.30e2
  t234 = f.my_piecewise3(t109, 0, 0.3e1 / 0.20e2 * t6 * t220 * t33 * t143 + t227 / 0.5e1 - t232)
  d11 = 0.2e1 * t107 + 0.2e1 * t154 + t7 * (t210 + t234)
  t237 = -t8 - t26
  t238 = f.my_piecewise5(t11, 0, t15, 0, t237)
  t241 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t238)
  t242 = t241 * t33
  t247 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t242 * t71 + t84)
  t249 = f.my_piecewise5(t15, 0, t11, 0, -t237)
  t252 = f.my_piecewise3(t112, 0, 0.5e1 / 0.3e1 * t114 * t249)
  t253 = t252 * t33
  t257 = t148 * t33
  t263 = t130 * r1
  t274 = -t38 * t122 / t123 / t130 / 0.9e1 - t51 * t129 / t131 / t263 / 0.9e1 - t64 * t137 / t138 / r1 / 0.12e2
  t279 = f.my_piecewise3(t109, 0, 0.3e1 / 0.20e2 * t6 * t253 * t143 + t152 + 0.3e1 / 0.20e2 * t6 * t257 * t274)
  t283 = 0.2e1 * t162
  t284 = f.my_piecewise5(t11, 0, t15, 0, t283)
  t288 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t156 * t238 * t28 + 0.5e1 / 0.3e1 * t23 * t284)
  t295 = t6 * t241 * t80 * t71
  t303 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t288 * t33 * t71 + t295 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t242 * t102 + t176 / 0.10e2 - t186 + t188 / 0.10e2)
  t307 = f.my_piecewise5(t15, 0, t11, 0, -t283)
  t311 = f.my_piecewise3(t112, 0, 0.10e2 / 0.9e1 * t211 * t249 * t116 + 0.5e1 / 0.3e1 * t114 * t307)
  t318 = t6 * t252 * t80 * t143
  t325 = t6 * t149 * t274
  t328 = f.my_piecewise3(t109, 0, 0.3e1 / 0.20e2 * t6 * t311 * t33 * t143 + t318 / 0.10e2 + t227 / 0.10e2 - t232 + 0.3e1 / 0.20e2 * t6 * t120 * t274 + t325 / 0.10e2)
  d12 = t107 + t154 + t247 + t279 + t7 * (t303 + t328)
  t333 = t238 ** 2
  t337 = 0.2e1 * t25 + 0.2e1 * t162
  t338 = f.my_piecewise5(t11, 0, t15, 0, t337)
  t342 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t156 * t333 + 0.5e1 / 0.3e1 * t23 * t338)
  t349 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t342 * t33 * t71 + t295 / 0.5e1 - t186)
  t350 = t249 ** 2
  t354 = f.my_piecewise5(t15, 0, t11, 0, -t337)
  t358 = f.my_piecewise3(t112, 0, 0.10e2 / 0.9e1 * t211 * t350 + 0.5e1 / 0.3e1 * t114 * t354)
  t388 = f.my_piecewise3(t109, 0, 0.3e1 / 0.20e2 * t6 * t358 * t33 * t143 + t318 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t253 * t274 - t232 + t325 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t257 * (0.7e1 / 0.27e2 * t38 * t122 / t123 / t263 + 0.11e2 / 0.27e2 * t51 * t129 / t131 / t138 + 0.5e1 / 0.12e2 * t64 * t137 / t138 / t130))
  d22 = 0.2e1 * t247 + 0.2e1 * t279 + t7 * (t349 + t388)
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
  t82 = 0.1e1 + t49 * t54 / t55 / r0 / 0.12e2 + t62 * t65 / t67 / t66 / 0.24e2 + t75 * t76 / t77 / 0.48e2
  t88 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t89 = 0.1e1 / t43
  t90 = t88 * t89
  t94 = t88 * t44
  t100 = t66 * r0
  t106 = t77 * r0
  t111 = -t49 * t54 / t55 / t66 / 0.9e1 - t62 * t65 / t67 / t100 / 0.9e1 - t75 * t76 / t106 / 0.12e2
  t115 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t116 = t115 ** 2
  t117 = t116 * f.p.zeta_threshold
  t119 = f.my_piecewise3(t21, t117, t32 * t20)
  t121 = 0.1e1 / t43 / t7
  t122 = t119 * t121
  t126 = t119 * t89
  t130 = t119 * t44
  t146 = 0.7e1 / 0.27e2 * t49 * t54 / t55 / t100 + 0.11e2 / 0.27e2 * t62 * t65 / t67 / t77 + 0.5e1 / 0.12e2 * t75 * t76 / t77 / t66
  t151 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t82 + t6 * t90 * t82 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t94 * t111 - t6 * t122 * t82 / 0.30e2 + t6 * t126 * t111 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t130 * t146)
  t153 = r1 <= f.p.dens_threshold
  t154 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t155 = 0.1e1 + t154
  t156 = t155 <= f.p.zeta_threshold
  t157 = t155 ** (0.1e1 / 0.3e1)
  t158 = 0.1e1 / t157
  t160 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t161 = t160 ** 2
  t164 = t157 ** 2
  t166 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t170 = f.my_piecewise3(t156, 0, 0.10e2 / 0.9e1 * t158 * t161 + 0.5e1 / 0.3e1 * t164 * t166)
  t172 = jnp.sqrt(s2)
  t174 = r1 ** (0.1e1 / 0.3e1)
  t181 = r1 ** 2
  t182 = t174 ** 2
  t189 = t181 ** 2
  t194 = 0.1e1 + t49 * t52 * t172 / t174 / r1 / 0.12e2 + t62 * t64 * s2 / t182 / t181 / 0.24e2 + t75 * t172 * s2 / t189 / 0.48e2
  t200 = f.my_piecewise3(t156, 0, 0.5e1 / 0.3e1 * t164 * t160)
  t206 = f.my_piecewise3(t156, t117, t164 * t155)
  t212 = f.my_piecewise3(t153, 0, 0.3e1 / 0.20e2 * t6 * t170 * t44 * t194 + t6 * t200 * t89 * t194 / 0.5e1 - t6 * t206 * t121 * t194 / 0.30e2)
  t222 = t24 ** 2
  t226 = 0.6e1 * t34 - 0.6e1 * t17 / t222
  t227 = f.my_piecewise5(t11, 0, t15, 0, t226)
  t231 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t227)
  t254 = 0.1e1 / t43 / t24
  t285 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t231 * t44 * t82 + 0.3e1 / 0.10e2 * t6 * t42 * t89 * t82 + 0.9e1 / 0.20e2 * t6 * t45 * t111 - t6 * t88 * t121 * t82 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t90 * t111 + 0.9e1 / 0.20e2 * t6 * t94 * t146 + 0.2e1 / 0.45e2 * t6 * t119 * t254 * t82 - t6 * t122 * t111 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t126 * t146 + 0.3e1 / 0.20e2 * t6 * t130 * (-0.70e2 / 0.81e2 * t49 * t54 / t55 / t77 - 0.154e3 / 0.81e2 * t62 * t65 / t67 / t106 - 0.5e1 / 0.2e1 * t75 * t76 / t77 / t100))
  t295 = f.my_piecewise5(t15, 0, t11, 0, -t226)
  t299 = f.my_piecewise3(t156, 0, -0.10e2 / 0.27e2 / t157 / t155 * t161 * t160 + 0.10e2 / 0.3e1 * t158 * t160 * t166 + 0.5e1 / 0.3e1 * t164 * t295)
  t317 = f.my_piecewise3(t153, 0, 0.3e1 / 0.20e2 * t6 * t299 * t44 * t194 + 0.3e1 / 0.10e2 * t6 * t170 * t89 * t194 - t6 * t200 * t121 * t194 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t206 * t254 * t194)
  d111 = 0.3e1 * t151 + 0.3e1 * t212 + t7 * (t285 + t317)

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
  t59 = 6 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = params.mu[0] * t60
  t62 = jnp.pi ** 2
  t63 = t62 ** (0.1e1 / 0.3e1)
  t64 = 0.1e1 / t63
  t65 = jnp.sqrt(s0)
  t66 = t64 * t65
  t67 = r0 ** (0.1e1 / 0.3e1)
  t74 = params.mu[1] * t59
  t75 = t63 ** 2
  t76 = 0.1e1 / t75
  t77 = t76 * s0
  t78 = r0 ** 2
  t79 = t67 ** 2
  t87 = params.mu[2] / t62
  t88 = t65 * s0
  t89 = t78 ** 2
  t94 = 0.1e1 + t61 * t66 / t67 / r0 / 0.12e2 + t74 * t77 / t79 / t78 / 0.24e2 + t87 * t88 / t89 / 0.48e2
  t103 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t104 = 0.1e1 / t55
  t105 = t103 * t104
  t109 = t103 * t56
  t115 = t78 * r0
  t121 = t89 * r0
  t126 = -t61 * t66 / t67 / t78 / 0.9e1 - t74 * t77 / t79 / t115 / 0.9e1 - t87 * t88 / t121 / 0.12e2
  t132 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t134 = 0.1e1 / t55 / t7
  t135 = t132 * t134
  t139 = t132 * t104
  t143 = t132 * t56
  t154 = t89 * t78
  t159 = 0.7e1 / 0.27e2 * t61 * t66 / t67 / t115 + 0.11e2 / 0.27e2 * t74 * t77 / t79 / t89 + 0.5e1 / 0.12e2 * t87 * t88 / t154
  t163 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t164 = t163 ** 2
  t165 = t164 * f.p.zeta_threshold
  t167 = f.my_piecewise3(t21, t165, t44 * t20)
  t169 = 0.1e1 / t55 / t25
  t170 = t167 * t169
  t174 = t167 * t134
  t178 = t167 * t104
  t182 = t167 * t56
  t198 = -0.70e2 / 0.81e2 * t61 * t66 / t67 / t89 - 0.154e3 / 0.81e2 * t74 * t77 / t79 / t121 - 0.5e1 / 0.2e1 * t87 * t88 / t89 / t115
  t203 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t94 + 0.3e1 / 0.10e2 * t6 * t105 * t94 + 0.9e1 / 0.20e2 * t6 * t109 * t126 - t6 * t135 * t94 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t139 * t126 + 0.9e1 / 0.20e2 * t6 * t143 * t159 + 0.2e1 / 0.45e2 * t6 * t170 * t94 - t6 * t174 * t126 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t178 * t159 + 0.3e1 / 0.20e2 * t6 * t182 * t198)
  t205 = r1 <= f.p.dens_threshold
  t206 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t207 = 0.1e1 + t206
  t208 = t207 <= f.p.zeta_threshold
  t209 = t207 ** (0.1e1 / 0.3e1)
  t211 = 0.1e1 / t209 / t207
  t213 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t214 = t213 ** 2
  t218 = 0.1e1 / t209
  t219 = t218 * t213
  t221 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t224 = t209 ** 2
  t226 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t230 = f.my_piecewise3(t208, 0, -0.10e2 / 0.27e2 * t211 * t214 * t213 + 0.10e2 / 0.3e1 * t219 * t221 + 0.5e1 / 0.3e1 * t224 * t226)
  t232 = jnp.sqrt(s2)
  t234 = r1 ** (0.1e1 / 0.3e1)
  t241 = r1 ** 2
  t242 = t234 ** 2
  t249 = t241 ** 2
  t254 = 0.1e1 + t61 * t64 * t232 / t234 / r1 / 0.12e2 + t74 * t76 * s2 / t242 / t241 / 0.24e2 + t87 * t232 * s2 / t249 / 0.48e2
  t263 = f.my_piecewise3(t208, 0, 0.10e2 / 0.9e1 * t218 * t214 + 0.5e1 / 0.3e1 * t224 * t221)
  t270 = f.my_piecewise3(t208, 0, 0.5e1 / 0.3e1 * t224 * t213)
  t276 = f.my_piecewise3(t208, t165, t224 * t207)
  t282 = f.my_piecewise3(t205, 0, 0.3e1 / 0.20e2 * t6 * t230 * t56 * t254 + 0.3e1 / 0.10e2 * t6 * t263 * t104 * t254 - t6 * t270 * t134 * t254 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t276 * t169 * t254)
  t284 = t20 ** 2
  t287 = t30 ** 2
  t293 = t41 ** 2
  t302 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t303 = f.my_piecewise5(t11, 0, t15, 0, t302)
  t307 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t284 * t287 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t293 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t303)
  t349 = t89 ** 2
  t371 = 0.1e1 / t55 / t36
  t376 = 0.3e1 / 0.20e2 * t6 * t307 * t56 * t94 + 0.3e1 / 0.5e1 * t6 * t57 * t126 + 0.6e1 / 0.5e1 * t6 * t105 * t126 + 0.9e1 / 0.10e2 * t6 * t109 * t159 - 0.2e1 / 0.5e1 * t6 * t135 * t126 + 0.6e1 / 0.5e1 * t6 * t139 * t159 + 0.3e1 / 0.5e1 * t6 * t143 * t198 + 0.8e1 / 0.45e2 * t6 * t170 * t126 - t6 * t174 * t159 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t178 * t198 + 0.3e1 / 0.20e2 * t6 * t182 * (0.910e3 / 0.243e3 * t61 * t66 / t67 / t121 + 0.2618e4 / 0.243e3 * t74 * t77 / t79 / t154 + 0.35e2 / 0.2e1 * t87 * t88 / t349) + 0.2e1 / 0.5e1 * t6 * t54 * t104 * t94 - t6 * t103 * t134 * t94 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t132 * t169 * t94 - 0.14e2 / 0.135e3 * t6 * t167 * t371 * t94
  t377 = f.my_piecewise3(t1, 0, t376)
  t378 = t207 ** 2
  t381 = t214 ** 2
  t387 = t221 ** 2
  t393 = f.my_piecewise5(t15, 0, t11, 0, -t302)
  t397 = f.my_piecewise3(t208, 0, 0.40e2 / 0.81e2 / t209 / t378 * t381 - 0.20e2 / 0.9e1 * t211 * t214 * t221 + 0.10e2 / 0.3e1 * t218 * t387 + 0.40e2 / 0.9e1 * t219 * t226 + 0.5e1 / 0.3e1 * t224 * t393)
  t419 = f.my_piecewise3(t205, 0, 0.3e1 / 0.20e2 * t6 * t397 * t56 * t254 + 0.2e1 / 0.5e1 * t6 * t230 * t104 * t254 - t6 * t263 * t134 * t254 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t270 * t169 * t254 - 0.14e2 / 0.135e3 * t6 * t276 * t371 * t254)
  d1111 = 0.4e1 * t203 + 0.4e1 * t282 + t7 * (t377 + t419)

  res = {'v4rho4': d1111}
  return res
