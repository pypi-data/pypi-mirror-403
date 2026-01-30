"""Generated from gga_x_vmt84.mpl."""

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

  vmt_f0 = lambda s: 1 + params_mu * s ** 2 * jnp.exp(-params_alpha * s ** 2) / (1 + params_mu * s ** 2)

  vmt84_f0 = lambda s: (1 - jnp.exp(-params_alpha * s ** 4)) / s ** 2 - 1 + jnp.exp(-params_alpha * s ** 4)

  vmt_f = lambda x: vmt_f0(X2S * x)

  vmt84_f = lambda x: vmt_f(x) + vmt84_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, vmt84_f, rs, zeta, xs0, xs1)

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

  vmt_f0 = lambda s: 1 + params_mu * s ** 2 * jnp.exp(-params_alpha * s ** 2) / (1 + params_mu * s ** 2)

  vmt84_f0 = lambda s: (1 - jnp.exp(-params_alpha * s ** 4)) / s ** 2 - 1 + jnp.exp(-params_alpha * s ** 4)

  vmt_f = lambda x: vmt_f0(X2S * x)

  vmt84_f = lambda x: vmt_f(x) + vmt84_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, vmt84_f, rs, zeta, xs0, xs1)

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

  vmt_f0 = lambda s: 1 + params_mu * s ** 2 * jnp.exp(-params_alpha * s ** 2) / (1 + params_mu * s ** 2)

  vmt84_f0 = lambda s: (1 - jnp.exp(-params_alpha * s ** 4)) / s ** 2 - 1 + jnp.exp(-params_alpha * s ** 4)

  vmt_f = lambda x: vmt_f0(X2S * x)

  vmt84_f = lambda x: vmt_f(x) + vmt84_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, vmt84_f, rs, zeta, xs0, xs1)

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
  t38 = t37 * t35
  t39 = 0.1e1 / t38
  t41 = params.alpha * t28
  t43 = t33 * s0 * t39
  t46 = jnp.exp(-t41 * t43 / 0.24e2)
  t49 = 0.1e1 + t29 * t43 / 0.24e2
  t50 = 0.1e1 / t49
  t51 = t46 * t50
  t55 = t28 ** 2
  t56 = params.alpha * t55
  t58 = 0.1e1 / t31 / t30
  t59 = s0 ** 2
  t60 = t58 * t59
  t61 = t35 ** 2
  t64 = 0.1e1 / t36 / t61 / r0
  t68 = jnp.exp(-t56 * t60 * t64 / 0.576e3)
  t70 = (0.1e1 - t68) * t55
  t72 = t32 / s0
  t76 = t34 * s0 * t39 * t51 / 0.24e2 + 0.4e1 * t70 * t72 * t38 + t68
  t80 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t76)
  t81 = r1 <= f.p.dens_threshold
  t82 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t83 = 0.1e1 + t82
  t84 = t83 <= f.p.zeta_threshold
  t85 = t83 ** (0.1e1 / 0.3e1)
  t87 = f.my_piecewise3(t84, t22, t85 * t83)
  t88 = t87 * t26
  t89 = r1 ** 2
  t90 = r1 ** (0.1e1 / 0.3e1)
  t91 = t90 ** 2
  t92 = t91 * t89
  t93 = 0.1e1 / t92
  t96 = t33 * s2 * t93
  t99 = jnp.exp(-t41 * t96 / 0.24e2)
  t102 = 0.1e1 + t29 * t96 / 0.24e2
  t103 = 0.1e1 / t102
  t104 = t99 * t103
  t108 = s2 ** 2
  t109 = t58 * t108
  t110 = t89 ** 2
  t113 = 0.1e1 / t90 / t110 / r1
  t117 = jnp.exp(-t56 * t109 * t113 / 0.576e3)
  t119 = (0.1e1 - t117) * t55
  t121 = t32 / s2
  t125 = t34 * s2 * t93 * t104 / 0.24e2 + 0.4e1 * t119 * t121 * t92 + t117
  t129 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t88 * t125)
  t130 = t6 ** 2
  t132 = t16 / t130
  t133 = t7 - t132
  t134 = f.my_piecewise5(t10, 0, t14, 0, t133)
  t137 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t134)
  t142 = t26 ** 2
  t143 = 0.1e1 / t142
  t147 = t5 * t25 * t143 * t76 / 0.8e1
  t151 = s0 / t37 / t35 / r0
  t155 = params.mu * t55
  t159 = 0.1e1 / t36 / t61 / t35
  t164 = params.mu ** 2
  t166 = t164 * t55 * t58
  t167 = t59 * t159
  t168 = t49 ** 2
  t170 = t46 / t168
  t174 = t41 * t33
  t182 = t56 * t58
  t191 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t137 * t26 * t76 - t147 - 0.3e1 / 0.8e1 * t5 * t27 * (-t34 * t151 * t51 / 0.9e1 + t155 * t60 * t159 * params.alpha * t51 / 0.216e3 + t166 * t167 * t170 / 0.216e3 - 0.2e1 / 0.9e1 * t174 * t151 * t68 + 0.32e2 / 0.3e1 * t70 * t72 * t37 * r0 + t182 * t167 * t68 / 0.108e3))
  t193 = f.my_piecewise5(t14, 0, t10, 0, -t133)
  t196 = f.my_piecewise3(t84, 0, 0.4e1 / 0.3e1 * t85 * t193)
  t204 = t5 * t87 * t143 * t125 / 0.8e1
  t206 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t196 * t26 * t125 - t204)
  vrho_0_ = t80 + t129 + t6 * (t191 + t206)
  t209 = -t7 - t132
  t210 = f.my_piecewise5(t10, 0, t14, 0, t209)
  t213 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t210)
  t219 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t213 * t26 * t76 - t147)
  t221 = f.my_piecewise5(t14, 0, t10, 0, -t209)
  t224 = f.my_piecewise3(t84, 0, 0.4e1 / 0.3e1 * t85 * t221)
  t232 = s2 / t91 / t89 / r1
  t239 = 0.1e1 / t90 / t110 / t89
  t244 = t108 * t239
  t245 = t102 ** 2
  t247 = t99 / t245
  t266 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t224 * t26 * t125 - t204 - 0.3e1 / 0.8e1 * t5 * t88 * (-t34 * t232 * t104 / 0.9e1 + t155 * t109 * t239 * params.alpha * t104 / 0.216e3 + t166 * t244 * t247 / 0.216e3 - 0.2e1 / 0.9e1 * t174 * t232 * t117 + 0.32e2 / 0.3e1 * t119 * t121 * t91 * r1 + t182 * t244 * t117 / 0.108e3))
  vrho_1_ = t80 + t129 + t6 * (t219 + t266)
  t279 = s0 * t64
  t299 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t34 * t39 * t46 * t50 / 0.24e2 - t155 * t58 * s0 * t64 * params.alpha * t51 / 0.576e3 - t166 * t279 * t170 / 0.576e3 + t41 * t33 * t39 * t68 / 0.12e2 - 0.4e1 * t70 * t32 / t59 * t38 - t182 * t279 * t68 / 0.288e3))
  vsigma_0_ = t6 * t299
  vsigma_1_ = 0.0e0
  t310 = s2 * t113
  t330 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t88 * (t34 * t93 * t99 * t103 / 0.24e2 - t155 * t58 * s2 * t113 * params.alpha * t104 / 0.576e3 - t166 * t310 * t247 / 0.576e3 + t41 * t33 * t93 * t117 / 0.12e2 - 0.4e1 * t119 * t32 / t108 * t92 - t182 * t310 * t117 / 0.288e3))
  vsigma_2_ = t6 * t330
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

  vmt_f0 = lambda s: 1 + params_mu * s ** 2 * jnp.exp(-params_alpha * s ** 2) / (1 + params_mu * s ** 2)

  vmt84_f0 = lambda s: (1 - jnp.exp(-params_alpha * s ** 4)) / s ** 2 - 1 + jnp.exp(-params_alpha * s ** 4)

  vmt_f = lambda x: vmt_f0(X2S * x)

  vmt84_f = lambda x: vmt_f(x) + vmt84_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, vmt84_f, rs, zeta, xs0, xs1)

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
  t27 = t21 * t25 * s0
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = r0 ** 2
  t31 = t18 ** 2
  t32 = t31 * t30
  t33 = 0.1e1 / t32
  t34 = t29 * t33
  t36 = params.alpha * t20 * t25
  t37 = s0 * t29
  t38 = t37 * t33
  t41 = jnp.exp(-t36 * t38 / 0.24e2)
  t42 = t21 * t25
  t45 = 0.1e1 + t42 * t38 / 0.24e2
  t46 = 0.1e1 / t45
  t47 = t41 * t46
  t48 = t34 * t47
  t51 = t20 ** 2
  t54 = 0.1e1 / t23 / t22
  t55 = params.alpha * t51 * t54
  t56 = s0 ** 2
  t57 = t56 * t28
  t58 = t30 ** 2
  t61 = 0.1e1 / t18 / t58 / r0
  t65 = jnp.exp(-t55 * t57 * t61 / 0.288e3)
  t68 = (0.1e1 - t65) * t51 * t24
  t70 = 0.1e1 / s0 * t28
  t74 = t27 * t48 / 0.24e2 + 0.2e1 * t68 * t70 * t32 + t65
  t78 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t74)
  t86 = 0.1e1 / t31 / t30 / r0
  t91 = params.mu * t51
  t92 = t54 * t56
  t96 = 0.1e1 / t18 / t58 / t30
  t97 = t28 * t96
  t99 = params.alpha * t41 * t46
  t103 = params.mu ** 2
  t104 = t103 * t51
  t106 = t45 ** 2
  t108 = t41 / t106
  t129 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t74 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t27 * t29 * t86 * t47 / 0.9e1 + t91 * t92 * t97 * t99 / 0.108e3 + t104 * t92 * t97 * t108 / 0.108e3 - 0.2e1 / 0.9e1 * t36 * t37 * t86 * t65 + 0.16e2 / 0.3e1 * t68 * t70 * t31 * r0 + t55 * t57 * t96 * t65 / 0.54e2))
  vrho_0_ = 0.2e1 * r0 * t129 + 0.2e1 * t78
  t134 = t54 * s0
  t136 = t28 * t61
  t161 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t42 * t48 / 0.24e2 - t91 * t134 * t136 * t99 / 0.288e3 - t104 * t134 * t136 * t108 / 0.288e3 + t36 * t34 * t65 / 0.12e2 - 0.2e1 * t68 / t56 * t28 * t32 - t55 * s0 * t28 * t61 * t65 / 0.144e3))
  vsigma_0_ = 0.2e1 * r0 * t161
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
  t29 = t23 * t27 * s0
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = r0 ** 2
  t33 = t19 * t32
  t34 = 0.1e1 / t33
  t35 = t31 * t34
  t37 = params.alpha * t22 * t27
  t38 = s0 * t31
  t39 = t38 * t34
  t42 = jnp.exp(-t37 * t39 / 0.24e2)
  t43 = t23 * t27
  t46 = 0.1e1 + t43 * t39 / 0.24e2
  t47 = 0.1e1 / t46
  t48 = t42 * t47
  t49 = t35 * t48
  t52 = t22 ** 2
  t55 = 0.1e1 / t25 / t24
  t56 = params.alpha * t52 * t55
  t57 = s0 ** 2
  t58 = t57 * t30
  t59 = t32 ** 2
  t62 = 0.1e1 / t18 / t59 / r0
  t66 = jnp.exp(-t56 * t58 * t62 / 0.288e3)
  t69 = (0.1e1 - t66) * t52 * t26
  t70 = 0.1e1 / s0
  t71 = t70 * t30
  t75 = t29 * t49 / 0.24e2 + 0.2e1 * t69 * t71 * t33 + t66
  t79 = t17 * t18
  t80 = t32 * r0
  t82 = 0.1e1 / t19 / t80
  t84 = t31 * t82 * t48
  t87 = params.mu * t52
  t88 = t55 * t57
  t89 = t87 * t88
  t92 = 0.1e1 / t18 / t59 / t32
  t93 = t30 * t92
  t95 = params.alpha * t42 * t47
  t99 = params.mu ** 2
  t100 = t99 * t52
  t101 = t100 * t88
  t102 = t46 ** 2
  t103 = 0.1e1 / t102
  t104 = t42 * t103
  t112 = t19 * r0
  t116 = t92 * t66
  t120 = -t29 * t84 / 0.9e1 + t89 * t93 * t95 / 0.108e3 + t101 * t93 * t104 / 0.108e3 - 0.2e1 / 0.9e1 * t37 * t38 * t82 * t66 + 0.16e2 / 0.3e1 * t69 * t71 * t112 + t56 * t58 * t116 / 0.54e2
  t125 = f.my_piecewise3(t2, 0, -t6 * t21 * t75 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t79 * t120)
  t136 = 0.1e1 / t19 / t59
  t143 = 0.1e1 / t18 / t59 / t80
  t144 = t30 * t143
  t151 = t24 ** 2
  t152 = 0.1e1 / t151
  t153 = params.mu * t152
  t154 = t57 * s0
  t156 = t59 ** 2
  t157 = t156 * t32
  t158 = 0.1e1 / t157
  t159 = params.alpha ** 2
  t164 = t99 * t152
  t171 = t99 * params.mu * t152
  t175 = 0.1e1 / t102 / t46
  t183 = t159 * t152
  t198 = t159 * t22 / t26 / t151
  t199 = t57 ** 2
  t208 = 0.11e2 / 0.27e2 * t29 * t31 * t136 * t48 - t89 * t144 * t95 / 0.12e2 - t101 * t144 * t104 / 0.12e2 + t153 * t154 * t158 * t159 * t48 / 0.81e2 + 0.2e1 / 0.81e2 * t164 * t154 * t158 * params.alpha * t104 + 0.2e1 / 0.81e2 * t171 * t154 * t158 * t42 * t175 + 0.2e1 / 0.9e1 * t37 * t38 * t136 * t66 - 0.4e1 / 0.81e2 * t183 * t154 * t158 * t66 + 0.80e2 / 0.9e1 * t69 * t71 * t19 - 0.19e2 / 0.162e3 * t56 * t58 * t143 * t66 + t198 * t199 * t31 / t19 / t156 / t59 * t66 / 0.486e3
  t213 = f.my_piecewise3(t2, 0, t6 * t17 / t112 * t75 / 0.12e2 - t6 * t21 * t120 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t79 * t208)
  v2rho2_0_ = 0.2e1 * r0 * t213 + 0.4e1 * t125
  t218 = t55 * s0
  t220 = t30 * t62
  t225 = t220 * t104
  t232 = 0.1e1 / t57 * t30
  t236 = s0 * t30
  t241 = t43 * t49 / 0.24e2 - t87 * t218 * t220 * t95 / 0.288e3 - t100 * t218 * t225 / 0.288e3 + t37 * t35 * t66 / 0.12e2 - 0.2e1 * t69 * t232 * t33 - t56 * t236 * t62 * t66 / 0.144e3
  t245 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t79 * t241)
  t251 = t55 * t30
  t252 = t87 * t251
  t267 = 0.1e1 / t156 / r0
  t305 = f.my_piecewise3(t2, 0, -t6 * t21 * t241 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t79 * (-t43 * t84 / 0.9e1 + t252 * t92 * params.alpha * s0 * t42 * t47 / 0.36e2 + t100 * t251 * t92 * t42 * t103 * s0 / 0.36e2 - t153 * t57 * t267 * t159 * t48 / 0.216e3 - t164 * t57 * t267 * params.alpha * t104 / 0.108e3 - t171 * t57 * t267 * t42 * t175 / 0.108e3 + t183 * t267 * t57 * t66 / 0.54e2 - 0.16e2 / 0.3e1 * t69 * t232 * t112 + t56 * t236 * t116 / 0.27e2 - t198 * t154 * t31 / t19 / t156 / t80 * t66 / 0.1296e4))
  v2rhosigma_0_ = 0.2e1 * r0 * t305 + 0.2e1 * t245
  t316 = 0.1e1 / t156
  t359 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t79 * (-t252 * t62 * params.alpha * t48 / 0.144e3 - t100 * t55 * t225 / 0.144e3 + t153 * s0 * t316 * t159 * t48 / 0.576e3 + t164 * s0 * t316 * params.alpha * t104 / 0.288e3 + t171 * s0 * t316 * t42 * t175 / 0.288e3 - t183 * t316 * s0 * t66 / 0.144e3 - t37 * t70 * t31 * t34 * t66 / 0.12e2 + 0.4e1 * t69 / t154 * t30 * t33 - t56 * t220 * t66 / 0.144e3 + t198 * t57 * t31 / t19 / t157 * t66 / 0.3456e4))
  v2sigma2_0_ = 0.2e1 * r0 * t359
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
  t20 = t19 * r0
  t22 = t17 / t20
  t23 = 6 ** (0.1e1 / 0.3e1)
  t24 = params.mu * t23
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t30 = t24 * t28 * s0
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = r0 ** 2
  t34 = t19 * t33
  t35 = 0.1e1 / t34
  t38 = params.alpha * t23 * t28
  t39 = s0 * t32
  t40 = t39 * t35
  t43 = jnp.exp(-t38 * t40 / 0.24e2)
  t47 = 0.1e1 + t24 * t28 * t40 / 0.24e2
  t48 = 0.1e1 / t47
  t49 = t43 * t48
  t53 = t23 ** 2
  t56 = 0.1e1 / t26 / t25
  t57 = params.alpha * t53 * t56
  t58 = s0 ** 2
  t59 = t58 * t31
  t60 = t33 ** 2
  t61 = t60 * r0
  t67 = jnp.exp(-t57 * t59 / t18 / t61 / 0.288e3)
  t70 = (0.1e1 - t67) * t53 * t27
  t72 = 0.1e1 / s0 * t31
  t76 = t30 * t32 * t35 * t49 / 0.24e2 + 0.2e1 * t70 * t72 * t34 + t67
  t81 = t17 / t19
  t82 = t33 * r0
  t84 = 0.1e1 / t19 / t82
  t90 = t56 * t58
  t91 = params.mu * t53 * t90
  t94 = 0.1e1 / t18 / t60 / t33
  t95 = t31 * t94
  t97 = params.alpha * t43 * t48
  t101 = params.mu ** 2
  t103 = t101 * t53 * t90
  t104 = t47 ** 2
  t106 = t43 / t104
  t121 = -t30 * t32 * t84 * t49 / 0.9e1 + t91 * t95 * t97 / 0.108e3 + t103 * t95 * t106 / 0.108e3 - 0.2e1 / 0.9e1 * t38 * t39 * t84 * t67 + 0.16e2 / 0.3e1 * t70 * t72 * t20 + t57 * t59 * t94 * t67 / 0.54e2
  t125 = t17 * t18
  t127 = 0.1e1 / t19 / t60
  t134 = 0.1e1 / t18 / t60 / t82
  t135 = t31 * t134
  t142 = t25 ** 2
  t143 = 0.1e1 / t142
  t144 = params.mu * t143
  t145 = t58 * s0
  t146 = t144 * t145
  t147 = t60 ** 2
  t149 = 0.1e1 / t147 / t33
  t150 = params.alpha ** 2
  t155 = t101 * t143
  t156 = t155 * t145
  t162 = t101 * params.mu * t143
  t163 = t162 * t145
  t166 = 0.1e1 / t104 / t47
  t174 = t150 * t143
  t189 = t150 * t23 / t27 / t142
  t190 = t58 ** 2
  t191 = t190 * t32
  t199 = 0.11e2 / 0.27e2 * t30 * t32 * t127 * t49 - t91 * t135 * t97 / 0.12e2 - t103 * t135 * t106 / 0.12e2 + t146 * t149 * t150 * t49 / 0.81e2 + 0.2e1 / 0.81e2 * t156 * t149 * params.alpha * t106 + 0.2e1 / 0.81e2 * t163 * t149 * t43 * t166 + 0.2e1 / 0.9e1 * t38 * t39 * t127 * t67 - 0.4e1 / 0.81e2 * t174 * t145 * t149 * t67 + 0.80e2 / 0.9e1 * t70 * t72 * t19 - 0.19e2 / 0.162e3 * t57 * t59 * t134 * t67 + t189 * t191 / t19 / t147 / t60 * t67 / 0.486e3
  t204 = f.my_piecewise3(t2, 0, t6 * t22 * t76 / 0.12e2 - t6 * t81 * t121 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t125 * t199)
  t218 = 0.1e1 / t19 / t147 / t61
  t219 = t190 * t218
  t220 = t150 * params.alpha
  t223 = t23 * t28
  t231 = t223 * t32
  t241 = t142 ** 2
  t245 = t147 ** 2
  t253 = 0.1e1 / t147 / t82
  t259 = 0.1e1 / t19 / t61
  t276 = 0.1e1 / t18 / t147
  t281 = t31 * t276
  t312 = t101 ** 2
  t315 = t104 ** 2
  t321 = t144 * t219 * t220 * t223 * t32 * t43 * t48 / 0.729e3 + t155 * t219 * t150 * t106 * t231 / 0.243e3 + 0.2e1 / 0.243e3 * t162 * t219 * params.alpha * t43 * t166 * t231 + t220 / t241 * t190 * t58 / t245 / t82 * t67 / 0.2187e4 + 0.44e2 / 0.81e2 * t174 * t145 * t253 * t67 - 0.164e3 / 0.81e2 * t38 * t39 * t259 * t67 - 0.2e1 / 0.2187e4 * t220 * t143 * t190 * s0 / t18 / t245 * t53 * t56 * t31 * t67 + 0.209e3 / 0.243e3 * t57 * t59 * t276 * t67 + 0.341e3 / 0.486e3 * t103 * t281 * t106 + 0.160e3 / 0.27e2 * t70 * t72 / t18 - 0.19e2 / 0.486e3 * t189 * t191 * t218 * t67 - 0.19e2 / 0.81e2 * t146 * t253 * t150 * t49 - 0.38e2 / 0.81e2 * t156 * t253 * params.alpha * t106 - 0.38e2 / 0.81e2 * t163 * t253 * t43 * t166 - 0.154e3 / 0.81e2 * t30 * t32 * t259 * t49 + 0.341e3 / 0.486e3 * t91 * t281 * t97 + 0.2e1 / 0.243e3 * t312 * t143 * t219 * t43 / t315 * t231
  t326 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t76 + t6 * t22 * t121 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t81 * t199 - 0.3e1 / 0.8e1 * t6 * t125 * t321)
  v3rho3_0_ = 0.2e1 * r0 * t326 + 0.6e1 * t204

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
  t21 = t20 * t18
  t22 = 0.1e1 / t21
  t23 = t17 * t22
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = params.mu * t24
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t31 = t25 * t29 * s0
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t36 = params.alpha * t24 * t29
  t37 = s0 * t33
  t38 = t37 * t22
  t41 = jnp.exp(-t36 * t38 / 0.24e2)
  t45 = 0.1e1 + t25 * t29 * t38 / 0.24e2
  t46 = 0.1e1 / t45
  t47 = t41 * t46
  t51 = t24 ** 2
  t54 = 0.1e1 / t27 / t26
  t55 = params.alpha * t51 * t54
  t56 = s0 ** 2
  t57 = t56 * t32
  t58 = t18 ** 2
  t59 = t58 * r0
  t65 = jnp.exp(-t55 * t57 / t19 / t59 / 0.288e3)
  t68 = (0.1e1 - t65) * t51 * t28
  t70 = 0.1e1 / s0 * t32
  t74 = t31 * t33 * t22 * t47 / 0.24e2 + 0.2e1 * t68 * t70 * t21 + t65
  t78 = t20 * r0
  t80 = t17 / t78
  t81 = t18 * r0
  t83 = 0.1e1 / t20 / t81
  t89 = t54 * t56
  t90 = params.mu * t51 * t89
  t91 = t58 * t18
  t93 = 0.1e1 / t19 / t91
  t94 = t32 * t93
  t96 = params.alpha * t41 * t46
  t100 = params.mu ** 2
  t102 = t100 * t51 * t89
  t103 = t45 ** 2
  t104 = 0.1e1 / t103
  t105 = t41 * t104
  t120 = -t31 * t33 * t83 * t47 / 0.9e1 + t90 * t94 * t96 / 0.108e3 + t102 * t94 * t105 / 0.108e3 - 0.2e1 / 0.9e1 * t36 * t37 * t83 * t65 + 0.16e2 / 0.3e1 * t68 * t70 * t78 + t55 * t57 * t93 * t65 / 0.54e2
  t125 = t17 / t20
  t127 = 0.1e1 / t20 / t58
  t134 = 0.1e1 / t19 / t58 / t81
  t135 = t32 * t134
  t142 = t26 ** 2
  t143 = 0.1e1 / t142
  t144 = params.mu * t143
  t145 = t56 * s0
  t146 = t144 * t145
  t147 = t58 ** 2
  t149 = 0.1e1 / t147 / t18
  t150 = params.alpha ** 2
  t155 = t100 * t143
  t156 = t155 * t145
  t162 = t100 * params.mu * t143
  t163 = t162 * t145
  t166 = 0.1e1 / t103 / t45
  t174 = t150 * t143
  t188 = 0.1e1 / t28 / t142
  t189 = t150 * t24 * t188
  t190 = t56 ** 2
  t191 = t190 * t33
  t192 = t147 * t58
  t199 = 0.11e2 / 0.27e2 * t31 * t33 * t127 * t47 - t90 * t135 * t96 / 0.12e2 - t102 * t135 * t105 / 0.12e2 + t146 * t149 * t150 * t47 / 0.81e2 + 0.2e1 / 0.81e2 * t156 * t149 * params.alpha * t105 + 0.2e1 / 0.81e2 * t163 * t149 * t41 * t166 + 0.2e1 / 0.9e1 * t36 * t37 * t127 * t65 - 0.4e1 / 0.81e2 * t174 * t145 * t149 * t65 + 0.80e2 / 0.9e1 * t68 * t70 * t20 - 0.19e2 / 0.162e3 * t55 * t57 * t134 * t65 + t189 * t191 / t20 / t192 * t65 / 0.486e3
  t203 = t17 * t19
  t206 = 0.1e1 / t20 / t147 / t59
  t207 = t190 * t206
  t208 = t150 * params.alpha
  t211 = t24 * t29
  t214 = t211 * t33 * t41 * t46
  t219 = t211 * t33
  t220 = t105 * t219
  t225 = t41 * t166
  t226 = t225 * t219
  t229 = t142 ** 2
  t230 = 0.1e1 / t229
  t231 = t208 * t230
  t232 = t190 * t56
  t233 = t147 ** 2
  t241 = 0.1e1 / t147 / t81
  t247 = 0.1e1 / t20 / t59
  t252 = t208 * t143
  t253 = t190 * s0
  t258 = t51 * t54
  t260 = t258 * t32 * t65
  t264 = 0.1e1 / t19 / t147
  t269 = t32 * t264
  t300 = t100 ** 2
  t301 = t300 * t143
  t303 = t103 ** 2
  t305 = t41 / t303
  t306 = t305 * t219
  t309 = t144 * t207 * t208 * t214 / 0.729e3 + t155 * t207 * t150 * t220 / 0.243e3 + 0.2e1 / 0.243e3 * t162 * t207 * params.alpha * t226 + t231 * t232 / t233 / t81 * t65 / 0.2187e4 + 0.44e2 / 0.81e2 * t174 * t145 * t241 * t65 - 0.164e3 / 0.81e2 * t36 * t37 * t247 * t65 - 0.2e1 / 0.2187e4 * t252 * t253 / t19 / t233 * t260 + 0.209e3 / 0.243e3 * t55 * t57 * t264 * t65 + 0.341e3 / 0.486e3 * t102 * t269 * t105 + 0.160e3 / 0.27e2 * t68 * t70 / t19 - 0.19e2 / 0.486e3 * t189 * t191 * t206 * t65 - 0.19e2 / 0.81e2 * t146 * t241 * t150 * t47 - 0.38e2 / 0.81e2 * t156 * t241 * params.alpha * t105 - 0.38e2 / 0.81e2 * t163 * t241 * t41 * t166 - 0.154e3 / 0.81e2 * t31 * t33 * t247 * t47 + 0.341e3 / 0.486e3 * t90 * t269 * t96 + 0.2e1 / 0.243e3 * t301 * t207 * t306
  t314 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t74 + t6 * t80 * t120 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t125 * t199 - 0.3e1 / 0.8e1 * t6 * t203 * t309)
  t329 = t147 * r0
  t331 = 0.1e1 / t19 / t329
  t336 = 0.1e1 / t192
  t341 = t150 ** 2
  t343 = t190 ** 2
  t354 = t253 / t19 / t233 / r0
  t359 = 0.1e1 / t20 / t91
  t378 = t32 * t41
  t391 = t258 * t32
  t407 = 0.1e1 / t20 / t147 / t91
  t412 = -0.5225e4 / 0.729e3 * t55 * t57 * t331 * t65 + 0.2563e4 / 0.729e3 * t146 * t336 * t150 * t47 + t341 * t230 * t343 / t19 / t233 / t329 * t260 / 0.118098e6 + 0.164e3 / 0.6561e4 * t252 * t354 * t260 + 0.292e3 / 0.27e2 * t36 * t37 * t359 * t65 - 0.2e1 / 0.19683e5 * t341 * t143 * t190 * t145 / t20 / t233 / t91 * t24 * t188 * t33 * t65 + 0.2e1 / 0.6561e4 * t144 * t354 * t341 * t258 * t378 * t46 + 0.8e1 / 0.6561e4 * t155 * t354 * t208 * t258 * t378 * t104 + 0.8e1 / 0.2187e4 * t162 * t354 * t150 * t225 * t391 + 0.16e2 / 0.2187e4 * t301 * t354 * params.alpha * t305 * t391 - 0.160e3 / 0.81e2 * t68 * t70 / t19 / r0 + 0.2755e4 / 0.4374e4 * t189 * t191 * t407 * t65
  t431 = t190 * t407
  t444 = t32 * t331
  t467 = 0.5126e4 / 0.729e3 * t156 * t336 * params.alpha * t105 - 0.38e2 / 0.2187e4 * t231 * t232 / t233 / t58 * t65 - 0.4684e4 / 0.729e3 * t174 * t145 * t336 * t65 + 0.5126e4 / 0.729e3 * t163 * t336 * t41 * t166 - 0.98e2 / 0.2187e4 * t144 * t431 * t208 * t214 - 0.98e2 / 0.729e3 * t155 * t431 * t150 * t220 - 0.196e3 / 0.729e3 * t162 * t431 * params.alpha * t226 - 0.3047e4 / 0.486e3 * t102 * t444 * t105 - 0.196e3 / 0.729e3 * t301 * t431 * t306 + 0.2618e4 / 0.243e3 * t31 * t33 * t359 * t47 - 0.3047e4 / 0.486e3 * t90 * t444 * t96 + 0.16e2 / 0.2187e4 * t300 * params.mu * t143 * t354 * t41 / t303 / t45 * t391
  t473 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t83 * t74 - 0.5e1 / 0.9e1 * t6 * t23 * t120 + t6 * t80 * t199 / 0.2e1 - t6 * t125 * t309 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t203 * (t412 + t467))
  v4rho4_0_ = 0.2e1 * r0 * t473 + 0.8e1 * t314

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
  t38 = t33 * t37
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t42 = t41 * t39
  t43 = 0.1e1 / t42
  t45 = params.alpha * t32
  t47 = t37 * s0 * t43
  t50 = jnp.exp(-t45 * t47 / 0.24e2)
  t53 = 0.1e1 + t33 * t47 / 0.24e2
  t55 = t50 / t53
  t59 = t32 ** 2
  t60 = params.alpha * t59
  t62 = 0.1e1 / t35 / t34
  t63 = s0 ** 2
  t64 = t62 * t63
  t65 = t39 ** 2
  t72 = jnp.exp(-t60 * t64 / t40 / t65 / r0 / 0.576e3)
  t74 = (0.1e1 - t72) * t59
  t76 = t36 / s0
  t80 = t38 * s0 * t43 * t55 / 0.24e2 + 0.4e1 * t74 * t76 * t42 + t72
  t84 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t85 = t84 * f.p.zeta_threshold
  t87 = f.my_piecewise3(t20, t85, t21 * t19)
  t88 = t30 ** 2
  t89 = 0.1e1 / t88
  t90 = t87 * t89
  t93 = t5 * t90 * t80 / 0.8e1
  t94 = t87 * t30
  t95 = t39 * r0
  t98 = s0 / t41 / t95
  t102 = params.mu * t59
  t103 = t102 * t64
  t106 = 0.1e1 / t40 / t65 / t39
  t111 = params.mu ** 2
  t113 = t111 * t59 * t62
  t114 = t63 * t106
  t115 = t53 ** 2
  t117 = t50 / t115
  t121 = t45 * t37
  t129 = t60 * t62
  t133 = -t38 * t98 * t55 / 0.9e1 + t103 * t106 * params.alpha * t55 / 0.216e3 + t113 * t114 * t117 / 0.216e3 - 0.2e1 / 0.9e1 * t121 * t98 * t72 + 0.32e2 / 0.3e1 * t74 * t76 * t41 * r0 + t129 * t114 * t72 / 0.108e3
  t138 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t80 - t93 - 0.3e1 / 0.8e1 * t5 * t94 * t133)
  t140 = r1 <= f.p.dens_threshold
  t141 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t142 = 0.1e1 + t141
  t143 = t142 <= f.p.zeta_threshold
  t144 = t142 ** (0.1e1 / 0.3e1)
  t146 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t149 = f.my_piecewise3(t143, 0, 0.4e1 / 0.3e1 * t144 * t146)
  t150 = t149 * t30
  t151 = r1 ** 2
  t152 = r1 ** (0.1e1 / 0.3e1)
  t153 = t152 ** 2
  t154 = t153 * t151
  t155 = 0.1e1 / t154
  t158 = t37 * s2 * t155
  t161 = jnp.exp(-t45 * t158 / 0.24e2)
  t164 = 0.1e1 + t33 * t158 / 0.24e2
  t166 = t161 / t164
  t170 = s2 ** 2
  t171 = t62 * t170
  t172 = t151 ** 2
  t179 = jnp.exp(-t60 * t171 / t152 / t172 / r1 / 0.576e3)
  t181 = (0.1e1 - t179) * t59
  t183 = t36 / s2
  t187 = t38 * s2 * t155 * t166 / 0.24e2 + 0.4e1 * t181 * t183 * t154 + t179
  t192 = f.my_piecewise3(t143, t85, t144 * t142)
  t193 = t192 * t89
  t196 = t5 * t193 * t187 / 0.8e1
  t198 = f.my_piecewise3(t140, 0, -0.3e1 / 0.8e1 * t5 * t150 * t187 - t196)
  t200 = t21 ** 2
  t201 = 0.1e1 / t200
  t202 = t26 ** 2
  t207 = t16 / t22 / t6
  t209 = -0.2e1 * t23 + 0.2e1 * t207
  t210 = f.my_piecewise5(t10, 0, t14, 0, t209)
  t214 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t201 * t202 + 0.4e1 / 0.3e1 * t21 * t210)
  t221 = t5 * t29 * t89 * t80
  t227 = 0.1e1 / t88 / t6
  t231 = t5 * t87 * t227 * t80 / 0.12e2
  t233 = t5 * t90 * t133
  t237 = s0 / t41 / t65
  t243 = 0.1e1 / t40 / t65 / t95
  t248 = t63 * t243
  t252 = t34 ** 2
  t253 = 0.1e1 / t252
  t254 = params.mu * t253
  t255 = t63 * s0
  t257 = t65 ** 2
  t259 = 0.1e1 / t257 / t39
  t260 = params.alpha ** 2
  t265 = t111 * t253
  t272 = t111 * params.mu * t253
  t283 = t260 * t253
  t297 = t260 * t32 / t36 / t252
  t298 = t63 ** 2
  t306 = 0.11e2 / 0.27e2 * t38 * t237 * t55 - t103 * t243 * params.alpha * t55 / 0.24e2 - t113 * t248 * t117 / 0.24e2 + t254 * t255 * t259 * t260 * t55 / 0.324e3 + t265 * t255 * t259 * params.alpha * t117 / 0.162e3 + t272 * t255 * t259 * t50 / t115 / t53 / 0.162e3 + 0.2e1 / 0.9e1 * t121 * t237 * t72 - t283 * t255 * t259 * t72 / 0.81e2 + 0.160e3 / 0.9e1 * t74 * t76 * t41 - 0.19e2 / 0.324e3 * t129 * t248 * t72 + t297 * t298 / t41 / t257 / t65 * t72 / 0.1944e4
  t311 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t214 * t30 * t80 - t221 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t133 + t231 - t233 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t94 * t306)
  t312 = t144 ** 2
  t313 = 0.1e1 / t312
  t314 = t146 ** 2
  t318 = f.my_piecewise5(t14, 0, t10, 0, -t209)
  t322 = f.my_piecewise3(t143, 0, 0.4e1 / 0.9e1 * t313 * t314 + 0.4e1 / 0.3e1 * t144 * t318)
  t329 = t5 * t149 * t89 * t187
  t334 = t5 * t192 * t227 * t187 / 0.12e2
  t336 = f.my_piecewise3(t140, 0, -0.3e1 / 0.8e1 * t5 * t322 * t30 * t187 - t329 / 0.4e1 + t334)
  d11 = 0.2e1 * t138 + 0.2e1 * t198 + t6 * (t311 + t336)
  t339 = -t7 - t24
  t340 = f.my_piecewise5(t10, 0, t14, 0, t339)
  t343 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t340)
  t344 = t343 * t30
  t349 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t344 * t80 - t93)
  t351 = f.my_piecewise5(t14, 0, t10, 0, -t339)
  t354 = f.my_piecewise3(t143, 0, 0.4e1 / 0.3e1 * t144 * t351)
  t355 = t354 * t30
  t359 = t192 * t30
  t360 = t151 * r1
  t363 = s2 / t153 / t360
  t367 = t102 * t171
  t370 = 0.1e1 / t152 / t172 / t151
  t375 = t170 * t370
  t376 = t164 ** 2
  t378 = t161 / t376
  t392 = -t38 * t363 * t166 / 0.9e1 + t367 * t370 * params.alpha * t166 / 0.216e3 + t113 * t375 * t378 / 0.216e3 - 0.2e1 / 0.9e1 * t121 * t363 * t179 + 0.32e2 / 0.3e1 * t181 * t183 * t153 * r1 + t129 * t375 * t179 / 0.108e3
  t397 = f.my_piecewise3(t140, 0, -0.3e1 / 0.8e1 * t5 * t355 * t187 - t196 - 0.3e1 / 0.8e1 * t5 * t359 * t392)
  t401 = 0.2e1 * t207
  t402 = f.my_piecewise5(t10, 0, t14, 0, t401)
  t406 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t201 * t340 * t26 + 0.4e1 / 0.3e1 * t21 * t402)
  t413 = t5 * t343 * t89 * t80
  t421 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t406 * t30 * t80 - t413 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t344 * t133 - t221 / 0.8e1 + t231 - t233 / 0.8e1)
  t425 = f.my_piecewise5(t14, 0, t10, 0, -t401)
  t429 = f.my_piecewise3(t143, 0, 0.4e1 / 0.9e1 * t313 * t351 * t146 + 0.4e1 / 0.3e1 * t144 * t425)
  t436 = t5 * t354 * t89 * t187
  t443 = t5 * t193 * t392
  t446 = f.my_piecewise3(t140, 0, -0.3e1 / 0.8e1 * t5 * t429 * t30 * t187 - t436 / 0.8e1 - t329 / 0.8e1 + t334 - 0.3e1 / 0.8e1 * t5 * t150 * t392 - t443 / 0.8e1)
  d12 = t138 + t198 + t349 + t397 + t6 * (t421 + t446)
  t451 = t340 ** 2
  t455 = 0.2e1 * t23 + 0.2e1 * t207
  t456 = f.my_piecewise5(t10, 0, t14, 0, t455)
  t460 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t201 * t451 + 0.4e1 / 0.3e1 * t21 * t456)
  t467 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t460 * t30 * t80 - t413 / 0.4e1 + t231)
  t468 = t351 ** 2
  t472 = f.my_piecewise5(t14, 0, t10, 0, -t455)
  t476 = f.my_piecewise3(t143, 0, 0.4e1 / 0.9e1 * t313 * t468 + 0.4e1 / 0.3e1 * t144 * t472)
  t488 = s2 / t153 / t172
  t494 = 0.1e1 / t152 / t172 / t360
  t499 = t170 * t494
  t503 = t170 * s2
  t505 = t172 ** 2
  t507 = 0.1e1 / t505 / t151
  t537 = t170 ** 2
  t545 = 0.11e2 / 0.27e2 * t38 * t488 * t166 - t367 * t494 * params.alpha * t166 / 0.24e2 - t113 * t499 * t378 / 0.24e2 + t254 * t503 * t507 * t260 * t166 / 0.324e3 + t265 * t503 * t507 * params.alpha * t378 / 0.162e3 + t272 * t503 * t507 * t161 / t376 / t164 / 0.162e3 + 0.2e1 / 0.9e1 * t121 * t488 * t179 - t283 * t503 * t507 * t179 / 0.81e2 + 0.160e3 / 0.9e1 * t181 * t183 * t153 - 0.19e2 / 0.324e3 * t129 * t499 * t179 + t297 * t537 / t153 / t505 / t172 * t179 / 0.1944e4
  t550 = f.my_piecewise3(t140, 0, -0.3e1 / 0.8e1 * t5 * t476 * t30 * t187 - t436 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t355 * t392 + t334 - t443 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t359 * t545)
  d22 = 0.2e1 * t349 + 0.2e1 * t397 + t6 * (t467 + t550)
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
  t50 = t45 * t49
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t54 = t53 * t51
  t55 = 0.1e1 / t54
  t57 = params.alpha * t44
  t59 = t49 * s0 * t55
  t62 = jnp.exp(-t57 * t59 / 0.24e2)
  t65 = 0.1e1 + t45 * t59 / 0.24e2
  t66 = 0.1e1 / t65
  t67 = t62 * t66
  t71 = t44 ** 2
  t72 = params.alpha * t71
  t74 = 0.1e1 / t47 / t46
  t75 = s0 ** 2
  t76 = t74 * t75
  t77 = t51 ** 2
  t78 = t77 * r0
  t84 = jnp.exp(-t72 * t76 / t52 / t78 / 0.576e3)
  t86 = (0.1e1 - t84) * t71
  t88 = t48 / s0
  t92 = t50 * s0 * t55 * t67 / 0.24e2 + 0.4e1 * t86 * t88 * t54 + t84
  t98 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t99 = t42 ** 2
  t100 = 0.1e1 / t99
  t101 = t98 * t100
  t105 = t98 * t42
  t106 = t51 * r0
  t109 = s0 / t53 / t106
  t114 = params.mu * t71 * t76
  t117 = 0.1e1 / t52 / t77 / t51
  t122 = params.mu ** 2
  t124 = t122 * t71 * t74
  t125 = t75 * t117
  t126 = t65 ** 2
  t127 = 0.1e1 / t126
  t128 = t62 * t127
  t132 = t57 * t49
  t140 = t72 * t74
  t144 = -t50 * t109 * t67 / 0.9e1 + t114 * t117 * params.alpha * t67 / 0.216e3 + t124 * t125 * t128 / 0.216e3 - 0.2e1 / 0.9e1 * t132 * t109 * t84 + 0.32e2 / 0.3e1 * t86 * t88 * t53 * r0 + t140 * t125 * t84 / 0.108e3
  t148 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t149 = t148 * f.p.zeta_threshold
  t151 = f.my_piecewise3(t20, t149, t21 * t19)
  t153 = 0.1e1 / t99 / t6
  t154 = t151 * t153
  t158 = t151 * t100
  t162 = t151 * t42
  t165 = s0 / t53 / t77
  t171 = 0.1e1 / t52 / t77 / t106
  t176 = t75 * t171
  t180 = t46 ** 2
  t181 = 0.1e1 / t180
  t182 = params.mu * t181
  t183 = t75 * s0
  t184 = t182 * t183
  t185 = t77 ** 2
  t187 = 0.1e1 / t185 / t51
  t188 = params.alpha ** 2
  t193 = t122 * t181
  t194 = t193 * t183
  t200 = t122 * params.mu * t181
  t201 = t200 * t183
  t204 = 0.1e1 / t126 / t65
  t211 = t188 * t181
  t225 = t188 * t44 / t48 / t180
  t226 = t75 ** 2
  t234 = 0.11e2 / 0.27e2 * t50 * t165 * t67 - t114 * t171 * params.alpha * t67 / 0.24e2 - t124 * t176 * t128 / 0.24e2 + t184 * t187 * t188 * t67 / 0.324e3 + t194 * t187 * params.alpha * t128 / 0.162e3 + t201 * t187 * t62 * t204 / 0.162e3 + 0.2e1 / 0.9e1 * t132 * t165 * t84 - t211 * t183 * t187 * t84 / 0.81e2 + 0.160e3 / 0.9e1 * t86 * t88 * t53 - 0.19e2 / 0.324e3 * t140 * t176 * t84 + t225 * t226 / t53 / t185 / t77 * t84 / 0.1944e4
  t239 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t92 - t5 * t101 * t92 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t105 * t144 + t5 * t154 * t92 / 0.12e2 - t5 * t158 * t144 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t162 * t234)
  t241 = r1 <= f.p.dens_threshold
  t242 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t243 = 0.1e1 + t242
  t244 = t243 <= f.p.zeta_threshold
  t245 = t243 ** (0.1e1 / 0.3e1)
  t246 = t245 ** 2
  t247 = 0.1e1 / t246
  t249 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t250 = t249 ** 2
  t254 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t258 = f.my_piecewise3(t244, 0, 0.4e1 / 0.9e1 * t247 * t250 + 0.4e1 / 0.3e1 * t245 * t254)
  t260 = r1 ** 2
  t261 = r1 ** (0.1e1 / 0.3e1)
  t262 = t261 ** 2
  t263 = t262 * t260
  t264 = 0.1e1 / t263
  t267 = t49 * s2 * t264
  t270 = jnp.exp(-t57 * t267 / 0.24e2)
  t279 = s2 ** 2
  t281 = t260 ** 2
  t288 = jnp.exp(-t72 * t74 * t279 / t261 / t281 / r1 / 0.576e3)
  t296 = t50 * s2 * t264 * t270 / (0.1e1 + t45 * t267 / 0.24e2) / 0.24e2 + 0.4e1 * (0.1e1 - t288) * t71 * t48 / s2 * t263 + t288
  t302 = f.my_piecewise3(t244, 0, 0.4e1 / 0.3e1 * t245 * t249)
  t308 = f.my_piecewise3(t244, t149, t245 * t243)
  t314 = f.my_piecewise3(t241, 0, -0.3e1 / 0.8e1 * t5 * t258 * t42 * t296 - t5 * t302 * t100 * t296 / 0.4e1 + t5 * t308 * t153 * t296 / 0.12e2)
  t324 = t24 ** 2
  t328 = 0.6e1 * t33 - 0.6e1 * t16 / t324
  t329 = f.my_piecewise5(t10, 0, t14, 0, t328)
  t333 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t329)
  t356 = 0.1e1 / t99 / t24
  t367 = t122 ** 2
  t372 = t226 / t53 / t185 / t78
  t374 = t126 ** 2
  t383 = s0 / t53 / t78
  t388 = 0.1e1 / t52 / t185
  t394 = 0.1e1 / t185 / t106
  t399 = t188 * params.alpha
  t400 = t180 ** 2
  t404 = t185 ** 2
  t424 = t75 * t388
  t471 = t367 * t181 * t372 * t62 / t374 * t44 * t49 / 0.486e3 - 0.154e3 / 0.81e2 * t50 * t383 * t67 + 0.341e3 / 0.972e3 * t114 * t388 * params.alpha * t67 + 0.11e2 / 0.81e2 * t211 * t183 * t394 * t84 + t399 / t400 * t226 * t75 / t404 / t106 * t84 / 0.34992e5 - 0.164e3 / 0.81e2 * t132 * t383 * t84 - t399 * t181 * t226 * s0 / t52 / t404 * t71 * t74 * t84 / 0.8748e4 + 0.209e3 / 0.486e3 * t140 * t424 * t84 + 0.341e3 / 0.972e3 * t124 * t424 * t128 - 0.19e2 / 0.324e3 * t184 * t394 * t188 * t67 - 0.19e2 / 0.162e3 * t194 * t394 * params.alpha * t128 - 0.19e2 / 0.162e3 * t201 * t394 * t62 * t204 + 0.320e3 / 0.27e2 * t86 * t88 / t52 - 0.19e2 / 0.1944e4 * t225 * t372 * t84 + t182 * t372 * t399 * t44 * t49 * t62 * t66 / 0.2916e4 + t193 * t372 * t188 * t62 * t127 * t44 * t49 / 0.972e3 + t200 * t372 * params.alpha * t62 * t204 * t44 * t49 / 0.486e3
  t476 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t333 * t42 * t92 - 0.3e1 / 0.8e1 * t5 * t41 * t100 * t92 - 0.9e1 / 0.8e1 * t5 * t43 * t144 + t5 * t98 * t153 * t92 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t101 * t144 - 0.9e1 / 0.8e1 * t5 * t105 * t234 - 0.5e1 / 0.36e2 * t5 * t151 * t356 * t92 + t5 * t154 * t144 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t158 * t234 - 0.3e1 / 0.8e1 * t5 * t162 * t471)
  t486 = f.my_piecewise5(t14, 0, t10, 0, -t328)
  t490 = f.my_piecewise3(t244, 0, -0.8e1 / 0.27e2 / t246 / t243 * t250 * t249 + 0.4e1 / 0.3e1 * t247 * t249 * t254 + 0.4e1 / 0.3e1 * t245 * t486)
  t508 = f.my_piecewise3(t241, 0, -0.3e1 / 0.8e1 * t5 * t490 * t42 * t296 - 0.3e1 / 0.8e1 * t5 * t258 * t100 * t296 + t5 * t302 * t153 * t296 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t308 * t356 * t296)
  d111 = 0.3e1 * t239 + 0.3e1 * t314 + t6 * (t476 + t508)

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
  t62 = t57 * t61
  t63 = r0 ** 2
  t64 = r0 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t66 = t65 * t63
  t67 = 0.1e1 / t66
  t69 = params.alpha * t56
  t71 = t61 * s0 * t67
  t74 = jnp.exp(-t69 * t71 / 0.24e2)
  t77 = 0.1e1 + t57 * t71 / 0.24e2
  t78 = 0.1e1 / t77
  t79 = t74 * t78
  t83 = t56 ** 2
  t84 = params.alpha * t83
  t86 = 0.1e1 / t59 / t58
  t87 = s0 ** 2
  t88 = t86 * t87
  t89 = t63 ** 2
  t90 = t89 * r0
  t96 = jnp.exp(-t84 * t88 / t64 / t90 / 0.576e3)
  t98 = (0.1e1 - t96) * t83
  t100 = t60 / s0
  t104 = t62 * s0 * t67 * t79 / 0.24e2 + 0.4e1 * t98 * t100 * t66 + t96
  t113 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t114 = t54 ** 2
  t115 = 0.1e1 / t114
  t116 = t113 * t115
  t120 = t113 * t54
  t121 = t63 * r0
  t124 = s0 / t65 / t121
  t129 = params.mu * t83 * t88
  t130 = t89 * t63
  t132 = 0.1e1 / t64 / t130
  t137 = params.mu ** 2
  t139 = t137 * t83 * t86
  t140 = t87 * t132
  t141 = t77 ** 2
  t142 = 0.1e1 / t141
  t143 = t74 * t142
  t147 = t69 * t61
  t155 = t84 * t86
  t159 = -t62 * t124 * t79 / 0.9e1 + t129 * t132 * params.alpha * t79 / 0.216e3 + t139 * t140 * t143 / 0.216e3 - 0.2e1 / 0.9e1 * t147 * t124 * t96 + 0.32e2 / 0.3e1 * t98 * t100 * t65 * r0 + t155 * t140 * t96 / 0.108e3
  t165 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t167 = 0.1e1 / t114 / t6
  t168 = t165 * t167
  t172 = t165 * t115
  t176 = t165 * t54
  t179 = s0 / t65 / t89
  t185 = 0.1e1 / t64 / t89 / t121
  t190 = t87 * t185
  t194 = t58 ** 2
  t195 = 0.1e1 / t194
  t196 = params.mu * t195
  t197 = t87 * s0
  t198 = t196 * t197
  t199 = t89 ** 2
  t201 = 0.1e1 / t199 / t63
  t202 = params.alpha ** 2
  t207 = t137 * t195
  t208 = t207 * t197
  t214 = t137 * params.mu * t195
  t215 = t214 * t197
  t218 = 0.1e1 / t141 / t77
  t225 = t202 * t195
  t238 = 0.1e1 / t60 / t194
  t239 = t202 * t56 * t238
  t240 = t87 ** 2
  t241 = t199 * t89
  t248 = 0.11e2 / 0.27e2 * t62 * t179 * t79 - t129 * t185 * params.alpha * t79 / 0.24e2 - t139 * t190 * t143 / 0.24e2 + t198 * t201 * t202 * t79 / 0.324e3 + t208 * t201 * params.alpha * t143 / 0.162e3 + t215 * t201 * t74 * t218 / 0.162e3 + 0.2e1 / 0.9e1 * t147 * t179 * t96 - t225 * t197 * t201 * t96 / 0.81e2 + 0.160e3 / 0.9e1 * t98 * t100 * t65 - 0.19e2 / 0.324e3 * t155 * t190 * t96 + t239 * t240 / t65 / t241 * t96 / 0.1944e4
  t252 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t253 = t252 * f.p.zeta_threshold
  t255 = f.my_piecewise3(t20, t253, t21 * t19)
  t257 = 0.1e1 / t114 / t25
  t258 = t255 * t257
  t262 = t255 * t167
  t266 = t255 * t115
  t270 = t255 * t54
  t271 = t137 ** 2
  t272 = t271 * t195
  t276 = t240 / t65 / t199 / t90
  t278 = t141 ** 2
  t279 = 0.1e1 / t278
  t282 = t74 * t279 * t56 * t61
  t287 = s0 / t65 / t90
  t292 = 0.1e1 / t64 / t199
  t298 = 0.1e1 / t199 / t121
  t303 = t202 * params.alpha
  t304 = t194 ** 2
  t305 = 0.1e1 / t304
  t306 = t303 * t305
  t307 = t240 * t87
  t308 = t199 ** 2
  t319 = t240 * s0
  t320 = t303 * t195 * t319
  t324 = t86 * t96
  t328 = t87 * t292
  t358 = t303 * t56 * t61 * t74 * t78
  t362 = t202 * t74
  t365 = t362 * t142 * t56 * t61
  t372 = params.alpha * t74 * t218 * t56 * t61
  t375 = t272 * t276 * t282 / 0.486e3 - 0.154e3 / 0.81e2 * t62 * t287 * t79 + 0.341e3 / 0.972e3 * t129 * t292 * params.alpha * t79 + 0.11e2 / 0.81e2 * t225 * t197 * t298 * t96 + t306 * t307 / t308 / t121 * t96 / 0.34992e5 - 0.164e3 / 0.81e2 * t147 * t287 * t96 - t320 / t64 / t308 * t83 * t324 / 0.8748e4 + 0.209e3 / 0.486e3 * t155 * t328 * t96 + 0.341e3 / 0.972e3 * t139 * t328 * t143 - 0.19e2 / 0.324e3 * t198 * t298 * t202 * t79 - 0.19e2 / 0.162e3 * t208 * t298 * params.alpha * t143 - 0.19e2 / 0.162e3 * t215 * t298 * t74 * t218 + 0.320e3 / 0.27e2 * t98 * t100 / t64 - 0.19e2 / 0.1944e4 * t239 * t276 * t96 + t196 * t276 * t358 / 0.2916e4 + t207 * t276 * t365 / 0.972e3 + t214 * t276 * t372 / 0.486e3
  t380 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t104 - 0.3e1 / 0.8e1 * t5 * t116 * t104 - 0.9e1 / 0.8e1 * t5 * t120 * t159 + t5 * t168 * t104 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t172 * t159 - 0.9e1 / 0.8e1 * t5 * t176 * t248 - 0.5e1 / 0.36e2 * t5 * t258 * t104 + t5 * t262 * t159 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t266 * t248 - 0.3e1 / 0.8e1 * t5 * t270 * t375)
  t382 = r1 <= f.p.dens_threshold
  t383 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t384 = 0.1e1 + t383
  t385 = t384 <= f.p.zeta_threshold
  t386 = t384 ** (0.1e1 / 0.3e1)
  t387 = t386 ** 2
  t389 = 0.1e1 / t387 / t384
  t391 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t392 = t391 ** 2
  t396 = 0.1e1 / t387
  t397 = t396 * t391
  t399 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t403 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t407 = f.my_piecewise3(t385, 0, -0.8e1 / 0.27e2 * t389 * t392 * t391 + 0.4e1 / 0.3e1 * t397 * t399 + 0.4e1 / 0.3e1 * t386 * t403)
  t409 = r1 ** 2
  t410 = r1 ** (0.1e1 / 0.3e1)
  t411 = t410 ** 2
  t412 = t411 * t409
  t413 = 0.1e1 / t412
  t416 = t61 * s2 * t413
  t419 = jnp.exp(-t69 * t416 / 0.24e2)
  t428 = s2 ** 2
  t430 = t409 ** 2
  t437 = jnp.exp(-t84 * t86 * t428 / t410 / t430 / r1 / 0.576e3)
  t445 = t62 * s2 * t413 * t419 / (0.1e1 + t57 * t416 / 0.24e2) / 0.24e2 + 0.4e1 * (0.1e1 - t437) * t83 * t60 / s2 * t412 + t437
  t454 = f.my_piecewise3(t385, 0, 0.4e1 / 0.9e1 * t396 * t392 + 0.4e1 / 0.3e1 * t386 * t399)
  t461 = f.my_piecewise3(t385, 0, 0.4e1 / 0.3e1 * t386 * t391)
  t467 = f.my_piecewise3(t385, t253, t386 * t384)
  t473 = f.my_piecewise3(t382, 0, -0.3e1 / 0.8e1 * t5 * t407 * t54 * t445 - 0.3e1 / 0.8e1 * t5 * t454 * t115 * t445 + t5 * t461 * t167 * t445 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t467 * t257 * t445)
  t488 = 0.1e1 / t114 / t36
  t493 = t19 ** 2
  t496 = t30 ** 2
  t502 = t41 ** 2
  t511 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t512 = f.my_piecewise5(t10, 0, t14, 0, t511)
  t516 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t493 * t496 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t502 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t512)
  t547 = 0.1e1 / t241
  t561 = t240 / t65 / t199 / t130
  t578 = 0.1e1 / t64 / t308 / r0
  t579 = t319 * t578
  t590 = s0 / t65 / t130
  t594 = t199 * r0
  t596 = 0.1e1 / t64 / t594
  t601 = t202 ** 2
  t603 = t240 ** 2
  t626 = t87 * t596
  t630 = -0.1171e4 / 0.729e3 * t225 * t197 * t547 * t96 - 0.19e2 / 0.17496e5 * t306 * t307 / t308 / t89 * t96 + 0.2755e4 / 0.17496e5 * t239 * t561 * t96 + 0.2563e4 / 0.1458e4 * t215 * t547 * t74 * t218 - 0.320e3 / 0.81e2 * t98 * t100 / t64 / r0 + 0.2e1 / 0.2187e4 * t271 * params.mu * t195 * t579 * t74 / t278 / t77 * t83 * t86 + 0.2618e4 / 0.243e3 * t62 * t590 * t79 - 0.3047e4 / 0.972e3 * t129 * t596 * params.alpha * t79 + t601 * t305 * t603 / t64 / t308 / t594 * t83 * t324 / 0.3779136e7 + 0.292e3 / 0.27e2 * t147 * t590 * t96 - t601 * t195 * t240 * t197 / t65 / t308 / t130 * t56 * t238 * t96 / 0.157464e6 - 0.5225e4 / 0.1458e4 * t155 * t626 * t96
  t650 = t86 * t74
  t682 = -0.3047e4 / 0.972e3 * t139 * t626 * t143 + 0.2563e4 / 0.2916e4 * t198 * t547 * t202 * t79 + 0.2563e4 / 0.1458e4 * t208 * t547 * params.alpha * t143 + 0.41e2 / 0.13122e5 * t320 * t578 * t83 * t324 - 0.49e2 / 0.729e3 * t272 * t561 * t282 + 0.2e1 / 0.2187e4 * t272 * t579 * t84 * t650 * t279 - 0.49e2 / 0.4374e4 * t196 * t561 * t358 - 0.49e2 / 0.1458e4 * t207 * t561 * t365 - 0.49e2 / 0.729e3 * t214 * t561 * t372 + t196 * t579 * t601 * t83 * t650 * t78 / 0.26244e5 + t207 * t579 * t303 * t83 * t650 * t142 / 0.6561e4 + t214 * t579 * t362 * t218 * t83 * t86 / 0.2187e4
  t687 = -t5 * t53 * t115 * t104 / 0.2e1 + t5 * t113 * t167 * t104 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t165 * t257 * t104 + 0.10e2 / 0.27e2 * t5 * t255 * t488 * t104 - 0.3e1 / 0.8e1 * t5 * t516 * t54 * t104 - 0.3e1 / 0.2e1 * t5 * t55 * t159 - 0.3e1 / 0.2e1 * t5 * t116 * t159 - 0.9e1 / 0.4e1 * t5 * t120 * t248 + t5 * t168 * t159 - 0.3e1 / 0.2e1 * t5 * t172 * t248 - 0.3e1 / 0.2e1 * t5 * t176 * t375 - 0.5e1 / 0.9e1 * t5 * t258 * t159 + t5 * t262 * t248 / 0.2e1 - t5 * t266 * t375 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t270 * (t630 + t682)
  t688 = f.my_piecewise3(t1, 0, t687)
  t689 = t384 ** 2
  t692 = t392 ** 2
  t698 = t399 ** 2
  t704 = f.my_piecewise5(t14, 0, t10, 0, -t511)
  t708 = f.my_piecewise3(t385, 0, 0.40e2 / 0.81e2 / t387 / t689 * t692 - 0.16e2 / 0.9e1 * t389 * t392 * t399 + 0.4e1 / 0.3e1 * t396 * t698 + 0.16e2 / 0.9e1 * t397 * t403 + 0.4e1 / 0.3e1 * t386 * t704)
  t730 = f.my_piecewise3(t382, 0, -0.3e1 / 0.8e1 * t5 * t708 * t54 * t445 - t5 * t407 * t115 * t445 / 0.2e1 + t5 * t454 * t167 * t445 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t461 * t257 * t445 + 0.10e2 / 0.27e2 * t5 * t467 * t488 * t445)
  d1111 = 0.4e1 * t380 + 0.4e1 * t473 + t6 * (t688 + t730)

  res = {'v4rho4': d1111}
  return res
