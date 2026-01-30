"""Generated from gga_x_vmt.mpl."""

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

  vmt_f = lambda x: vmt_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, vmt_f, rs, zeta, xs0, xs1)

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

  vmt_f = lambda x: vmt_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, vmt_f, rs, zeta, xs0, xs1)

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

  vmt_f = lambda x: vmt_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, vmt_f, rs, zeta, xs0, xs1)

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
  t41 = params.alpha * t28
  t43 = t33 * s0 * t39
  t46 = jnp.exp(-t41 * t43 / 0.24e2)
  t49 = 0.1e1 + t29 * t43 / 0.24e2
  t50 = 0.1e1 / t49
  t51 = t46 * t50
  t55 = 0.1e1 + t34 * s0 * t39 * t51 / 0.24e2
  t59 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t55)
  t60 = r1 <= f.p.dens_threshold
  t61 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t62 = 0.1e1 + t61
  t63 = t62 <= f.p.zeta_threshold
  t64 = t62 ** (0.1e1 / 0.3e1)
  t66 = f.my_piecewise3(t63, t22, t64 * t62)
  t67 = t66 * t26
  t68 = r1 ** 2
  t69 = r1 ** (0.1e1 / 0.3e1)
  t70 = t69 ** 2
  t72 = 0.1e1 / t70 / t68
  t75 = t33 * s2 * t72
  t78 = jnp.exp(-t41 * t75 / 0.24e2)
  t81 = 0.1e1 + t29 * t75 / 0.24e2
  t82 = 0.1e1 / t81
  t83 = t78 * t82
  t87 = 0.1e1 + t34 * s2 * t72 * t83 / 0.24e2
  t91 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t67 * t87)
  t92 = t6 ** 2
  t94 = t16 / t92
  t95 = t7 - t94
  t96 = f.my_piecewise5(t10, 0, t14, 0, t95)
  t99 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t96)
  t104 = t26 ** 2
  t105 = 0.1e1 / t104
  t109 = t5 * t25 * t105 * t55 / 0.8e1
  t117 = t28 ** 2
  t118 = params.mu * t117
  t120 = 0.1e1 / t31 / t30
  t121 = s0 ** 2
  t124 = t35 ** 2
  t127 = 0.1e1 / t36 / t124 / t35
  t132 = params.mu ** 2
  t134 = t132 * t117 * t120
  t136 = t49 ** 2
  t138 = t46 / t136
  t147 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t99 * t26 * t55 - t109 - 0.3e1 / 0.8e1 * t5 * t27 * (-t34 * s0 / t37 / t35 / r0 * t51 / 0.9e1 + t118 * t120 * t121 * t127 * params.alpha * t51 / 0.216e3 + t134 * t121 * t127 * t138 / 0.216e3))
  t149 = f.my_piecewise5(t14, 0, t10, 0, -t95)
  t152 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t149)
  t160 = t5 * t66 * t105 * t87 / 0.8e1
  t162 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t152 * t26 * t87 - t160)
  vrho_0_ = t59 + t91 + t6 * (t147 + t162)
  t165 = -t7 - t94
  t166 = f.my_piecewise5(t10, 0, t14, 0, t165)
  t169 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t166)
  t175 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t169 * t26 * t55 - t109)
  t177 = f.my_piecewise5(t14, 0, t10, 0, -t165)
  t180 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t177)
  t192 = s2 ** 2
  t195 = t68 ** 2
  t198 = 0.1e1 / t69 / t195 / t68
  t204 = t81 ** 2
  t206 = t78 / t204
  t215 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t180 * t26 * t87 - t160 - 0.3e1 / 0.8e1 * t5 * t67 * (-t34 * s2 / t70 / t68 / r1 * t83 / 0.9e1 + t118 * t120 * t192 * t198 * params.alpha * t83 / 0.216e3 + t134 * t192 * t198 * t206 / 0.216e3))
  vrho_1_ = t59 + t91 + t6 * (t175 + t215)
  t226 = 0.1e1 / t36 / t124 / r0
  t239 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t34 * t39 * t46 * t50 / 0.24e2 - t118 * t120 * s0 * t226 * params.alpha * t51 / 0.576e3 - t134 * s0 * t226 * t138 / 0.576e3))
  vsigma_0_ = t6 * t239
  vsigma_1_ = 0.0e0
  t248 = 0.1e1 / t69 / t195 / r1
  t261 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t67 * (t34 * t72 * t78 * t82 / 0.24e2 - t118 * t120 * s2 * t248 * params.alpha * t83 / 0.576e3 - t134 * s2 * t248 * t206 / 0.576e3))
  vsigma_2_ = t6 * t261
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

  vmt_f = lambda x: vmt_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, vmt_f, rs, zeta, xs0, xs1)

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
  t33 = 0.1e1 / t31 / t30
  t38 = s0 * t29 * t33
  t41 = jnp.exp(-params.alpha * t20 * t25 * t38 / 0.24e2)
  t42 = t21 * t25
  t45 = 0.1e1 + t42 * t38 / 0.24e2
  t46 = 0.1e1 / t45
  t47 = t41 * t46
  t48 = t29 * t33 * t47
  t51 = 0.1e1 + t27 * t48 / 0.24e2
  t55 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t51)
  t68 = t20 ** 2
  t69 = params.mu * t68
  t71 = 0.1e1 / t23 / t22
  t72 = s0 ** 2
  t73 = t71 * t72
  t75 = t30 ** 2
  t79 = t28 / t18 / t75 / t30
  t81 = params.alpha * t41 * t46
  t85 = params.mu ** 2
  t86 = t85 * t68
  t88 = t45 ** 2
  t90 = t41 / t88
  t99 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t51 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t27 * t29 / t31 / t30 / r0 * t47 / 0.9e1 + t69 * t73 * t79 * t81 / 0.108e3 + t86 * t73 * t79 * t90 / 0.108e3))
  vrho_0_ = 0.2e1 * r0 * t99 + 0.2e1 * t55
  t104 = t71 * s0
  t109 = t28 / t18 / t75 / r0
  t121 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t42 * t48 / 0.24e2 - t69 * t104 * t109 * t81 / 0.288e3 - t86 * t104 * t109 * t90 / 0.288e3))
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
  t34 = 0.1e1 / t19 / t32
  t39 = s0 * t31 * t34
  t42 = jnp.exp(-params.alpha * t22 * t27 * t39 / 0.24e2)
  t43 = t23 * t27
  t46 = 0.1e1 + t43 * t39 / 0.24e2
  t47 = 0.1e1 / t46
  t48 = t42 * t47
  t49 = t31 * t34 * t48
  t52 = 0.1e1 + t29 * t49 / 0.24e2
  t56 = t17 * t18
  t57 = t32 * r0
  t61 = t31 / t19 / t57 * t48
  t64 = t22 ** 2
  t65 = params.mu * t64
  t67 = 0.1e1 / t25 / t24
  t68 = s0 ** 2
  t69 = t67 * t68
  t70 = t65 * t69
  t71 = t32 ** 2
  t74 = 0.1e1 / t18 / t71 / t32
  t75 = t30 * t74
  t77 = params.alpha * t42 * t47
  t81 = params.mu ** 2
  t82 = t81 * t64
  t83 = t82 * t69
  t84 = t46 ** 2
  t85 = 0.1e1 / t84
  t86 = t42 * t85
  t90 = -t29 * t61 / 0.9e1 + t70 * t75 * t77 / 0.108e3 + t83 * t75 * t86 / 0.108e3
  t95 = f.my_piecewise3(t2, 0, -t6 * t21 * t52 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t56 * t90)
  t115 = t30 / t18 / t71 / t57
  t122 = t24 ** 2
  t123 = 0.1e1 / t122
  t124 = params.mu * t123
  t125 = t68 * s0
  t127 = t71 ** 2
  t129 = 0.1e1 / t127 / t32
  t130 = params.alpha ** 2
  t135 = t81 * t123
  t142 = t81 * params.mu * t123
  t146 = 0.1e1 / t84 / t46
  t155 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t52 / 0.12e2 - t6 * t21 * t90 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t56 * (0.11e2 / 0.27e2 * t29 * t31 / t19 / t71 * t48 - t70 * t115 * t77 / 0.12e2 - t83 * t115 * t86 / 0.12e2 + t124 * t125 * t129 * t130 * t48 / 0.81e2 + 0.2e1 / 0.81e2 * t135 * t125 * t129 * params.alpha * t86 + 0.2e1 / 0.81e2 * t142 * t125 * t129 * t42 * t146))
  v2rho2_0_ = 0.2e1 * r0 * t155 + 0.4e1 * t95
  t160 = t67 * s0
  t164 = 0.1e1 / t18 / t71 / r0
  t165 = t30 * t164
  t170 = t165 * t86
  t173 = t43 * t49 / 0.24e2 - t65 * t160 * t165 * t77 / 0.288e3 - t82 * t160 * t170 / 0.288e3
  t177 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t56 * t173)
  t183 = t67 * t30
  t184 = t65 * t183
  t199 = 0.1e1 / t127 / r0
  t219 = f.my_piecewise3(t2, 0, -t6 * t21 * t173 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t56 * (-t43 * t61 / 0.9e1 + t184 * t74 * params.alpha * s0 * t42 * t47 / 0.36e2 + t82 * t183 * t74 * t42 * t85 * s0 / 0.36e2 - t124 * t68 * t199 * t130 * t48 / 0.216e3 - t135 * t68 * t199 * params.alpha * t86 / 0.108e3 - t142 * t68 * t199 * t42 * t146 / 0.108e3))
  v2rhosigma_0_ = 0.2e1 * r0 * t219 + 0.2e1 * t177
  t230 = 0.1e1 / t127
  t249 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t56 * (-t184 * t164 * params.alpha * t48 / 0.144e3 - t82 * t67 * t170 / 0.144e3 + t124 * s0 * t230 * t130 * t48 / 0.576e3 + t135 * s0 * t230 * params.alpha * t86 / 0.288e3 + t142 * s0 * t230 * t42 * t146 / 0.288e3))
  v2sigma2_0_ = 0.2e1 * r0 * t249
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
  t30 = t24 * t28 * s0
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t40 = s0 * t32 * t35
  t43 = jnp.exp(-params.alpha * t23 * t28 * t40 / 0.24e2)
  t47 = 0.1e1 + t24 * t28 * t40 / 0.24e2
  t48 = 0.1e1 / t47
  t49 = t43 * t48
  t53 = 0.1e1 + t30 * t32 * t35 * t49 / 0.24e2
  t58 = t17 / t19
  t59 = t33 * r0
  t66 = t23 ** 2
  t70 = s0 ** 2
  t71 = 0.1e1 / t26 / t25 * t70
  t72 = params.mu * t66 * t71
  t73 = t33 ** 2
  t77 = t31 / t18 / t73 / t33
  t79 = params.alpha * t43 * t48
  t83 = params.mu ** 2
  t85 = t83 * t66 * t71
  t86 = t47 ** 2
  t88 = t43 / t86
  t92 = -t30 * t32 / t19 / t59 * t49 / 0.9e1 + t72 * t77 * t79 / 0.108e3 + t85 * t77 * t88 / 0.108e3
  t96 = t17 * t18
  t106 = t31 / t18 / t73 / t59
  t113 = t25 ** 2
  t114 = 0.1e1 / t113
  t115 = params.mu * t114
  t116 = t70 * s0
  t117 = t115 * t116
  t118 = t73 ** 2
  t120 = 0.1e1 / t118 / t33
  t121 = params.alpha ** 2
  t126 = t83 * t114
  t127 = t126 * t116
  t133 = t83 * params.mu * t114
  t134 = t133 * t116
  t137 = 0.1e1 / t86 / t47
  t141 = 0.11e2 / 0.27e2 * t30 * t32 / t19 / t73 * t49 - t72 * t106 * t79 / 0.12e2 - t85 * t106 * t88 / 0.12e2 + t117 * t120 * t121 * t49 / 0.81e2 + 0.2e1 / 0.81e2 * t127 * t120 * params.alpha * t88 + 0.2e1 / 0.81e2 * t134 * t120 * t43 * t137
  t146 = f.my_piecewise3(t2, 0, t6 * t22 * t53 / 0.12e2 - t6 * t58 * t92 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t96 * t141)
  t158 = t73 * r0
  t167 = t31 / t18 / t118
  t175 = 0.1e1 / t118 / t59
  t188 = t70 ** 2
  t192 = t188 / t19 / t118 / t158
  t196 = t23 * t28
  t204 = t196 * t32
  t214 = t83 ** 2
  t217 = t86 ** 2
  t228 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t53 + t6 * t22 * t92 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t58 * t141 - 0.3e1 / 0.8e1 * t6 * t96 * (-0.154e3 / 0.81e2 * t30 * t32 / t19 / t158 * t49 + 0.341e3 / 0.486e3 * t72 * t167 * t79 + 0.341e3 / 0.486e3 * t85 * t167 * t88 - 0.19e2 / 0.81e2 * t117 * t175 * t121 * t49 - 0.38e2 / 0.81e2 * t127 * t175 * params.alpha * t88 - 0.38e2 / 0.81e2 * t134 * t175 * t43 * t137 + t115 * t192 * t121 * params.alpha * t196 * t32 * t43 * t48 / 0.729e3 + t126 * t192 * t121 * t88 * t204 / 0.243e3 + 0.2e1 / 0.243e3 * t133 * t192 * params.alpha * t43 * t137 * t204 + 0.2e1 / 0.243e3 * t214 * t114 * t192 * t43 / t217 * t204))
  v3rho3_0_ = 0.2e1 * r0 * t228 + 0.6e1 * t146

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
  t31 = t25 * t29 * s0
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t38 = s0 * t33 * t22
  t41 = jnp.exp(-params.alpha * t24 * t29 * t38 / 0.24e2)
  t45 = 0.1e1 + t25 * t29 * t38 / 0.24e2
  t46 = 0.1e1 / t45
  t47 = t41 * t46
  t51 = 0.1e1 + t31 * t33 * t22 * t47 / 0.24e2
  t57 = t17 / t20 / r0
  t58 = t18 * r0
  t60 = 0.1e1 / t20 / t58
  t65 = t24 ** 2
  t68 = 0.1e1 / t27 / t26
  t69 = s0 ** 2
  t70 = t68 * t69
  t71 = params.mu * t65 * t70
  t72 = t18 ** 2
  t73 = t72 * t18
  t76 = t32 / t19 / t73
  t78 = params.alpha * t41 * t46
  t82 = params.mu ** 2
  t84 = t82 * t65 * t70
  t85 = t45 ** 2
  t86 = 0.1e1 / t85
  t87 = t41 * t86
  t91 = -t31 * t33 * t60 * t47 / 0.9e1 + t71 * t76 * t78 / 0.108e3 + t84 * t76 * t87 / 0.108e3
  t96 = t17 / t20
  t106 = t32 / t19 / t72 / t58
  t113 = t26 ** 2
  t114 = 0.1e1 / t113
  t115 = params.mu * t114
  t116 = t69 * s0
  t117 = t115 * t116
  t118 = t72 ** 2
  t120 = 0.1e1 / t118 / t18
  t121 = params.alpha ** 2
  t126 = t82 * t114
  t127 = t126 * t116
  t133 = t82 * params.mu * t114
  t134 = t133 * t116
  t137 = 0.1e1 / t85 / t45
  t141 = 0.11e2 / 0.27e2 * t31 * t33 / t20 / t72 * t47 - t71 * t106 * t78 / 0.12e2 - t84 * t106 * t87 / 0.12e2 + t117 * t120 * t121 * t47 / 0.81e2 + 0.2e1 / 0.81e2 * t127 * t120 * params.alpha * t87 + 0.2e1 / 0.81e2 * t134 * t120 * t41 * t137
  t145 = t17 * t19
  t146 = t72 * r0
  t155 = t32 / t19 / t118
  t163 = 0.1e1 / t118 / t58
  t176 = t69 ** 2
  t180 = t176 / t20 / t118 / t146
  t181 = t121 * params.alpha
  t184 = t24 * t29
  t187 = t184 * t33 * t41 * t46
  t192 = t184 * t33
  t193 = t87 * t192
  t198 = t41 * t137
  t199 = t198 * t192
  t202 = t82 ** 2
  t203 = t202 * t114
  t205 = t85 ** 2
  t207 = t41 / t205
  t208 = t207 * t192
  t211 = -0.154e3 / 0.81e2 * t31 * t33 / t20 / t146 * t47 + 0.341e3 / 0.486e3 * t71 * t155 * t78 + 0.341e3 / 0.486e3 * t84 * t155 * t87 - 0.19e2 / 0.81e2 * t117 * t163 * t121 * t47 - 0.38e2 / 0.81e2 * t127 * t163 * params.alpha * t87 - 0.38e2 / 0.81e2 * t134 * t163 * t41 * t137 + t115 * t180 * t181 * t187 / 0.729e3 + t126 * t180 * t121 * t193 / 0.243e3 + 0.2e1 / 0.243e3 * t133 * t180 * params.alpha * t199 + 0.2e1 / 0.243e3 * t203 * t180 * t208
  t216 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t51 + t6 * t57 * t91 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t96 * t141 - 0.3e1 / 0.8e1 * t6 * t145 * t211)
  t234 = t32 / t19 / t118 / r0
  t241 = t176 / t20 / t118 / t73
  t255 = t118 ** 2
  t259 = t176 * s0 / t19 / t255 / r0
  t260 = t121 ** 2
  t263 = t65 * t68
  t264 = t32 * t41
  t277 = t263 * t32
  t287 = 0.1e1 / t118 / t72
  t321 = -0.3047e4 / 0.486e3 * t84 * t234 * t87 - 0.98e2 / 0.2187e4 * t115 * t241 * t181 * t187 - 0.98e2 / 0.729e3 * t126 * t241 * t121 * t193 - 0.196e3 / 0.729e3 * t133 * t241 * params.alpha * t199 + 0.2e1 / 0.6561e4 * t115 * t259 * t260 * t263 * t264 * t46 + 0.8e1 / 0.6561e4 * t126 * t259 * t181 * t263 * t264 * t86 + 0.8e1 / 0.2187e4 * t133 * t259 * t121 * t198 * t277 + 0.16e2 / 0.2187e4 * t203 * t259 * params.alpha * t207 * t277 + 0.2563e4 / 0.729e3 * t117 * t287 * t121 * t47 + 0.5126e4 / 0.729e3 * t127 * t287 * params.alpha * t87 + 0.5126e4 / 0.729e3 * t134 * t287 * t41 * t137 + 0.2618e4 / 0.243e3 * t31 * t33 / t20 / t73 * t47 - 0.3047e4 / 0.486e3 * t71 * t234 * t78 - 0.196e3 / 0.729e3 * t203 * t241 * t208 + 0.16e2 / 0.2187e4 * t202 * params.mu * t114 * t259 * t41 / t205 / t45 * t277
  t326 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t60 * t51 - 0.5e1 / 0.9e1 * t6 * t23 * t91 + t6 * t57 * t141 / 0.2e1 - t6 * t96 * t211 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t145 * t321)
  v4rho4_0_ = 0.2e1 * r0 * t326 + 0.8e1 * t216

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
  t43 = 0.1e1 / t41 / t39
  t45 = params.alpha * t32
  t47 = t37 * s0 * t43
  t50 = jnp.exp(-t45 * t47 / 0.24e2)
  t53 = 0.1e1 + t33 * t47 / 0.24e2
  t55 = t50 / t53
  t59 = 0.1e1 + t38 * s0 * t43 * t55 / 0.24e2
  t63 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t64 = t63 * f.p.zeta_threshold
  t66 = f.my_piecewise3(t20, t64, t21 * t19)
  t67 = t30 ** 2
  t68 = 0.1e1 / t67
  t69 = t66 * t68
  t72 = t5 * t69 * t59 / 0.8e1
  t73 = t66 * t30
  t74 = t39 * r0
  t81 = t32 ** 2
  t82 = params.mu * t81
  t84 = 0.1e1 / t35 / t34
  t85 = s0 ** 2
  t87 = t82 * t84 * t85
  t88 = t39 ** 2
  t91 = 0.1e1 / t40 / t88 / t39
  t96 = params.mu ** 2
  t98 = t96 * t81 * t84
  t100 = t53 ** 2
  t102 = t50 / t100
  t106 = -t38 * s0 / t41 / t74 * t55 / 0.9e1 + t87 * t91 * params.alpha * t55 / 0.216e3 + t98 * t85 * t91 * t102 / 0.216e3
  t111 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t59 - t72 - 0.3e1 / 0.8e1 * t5 * t73 * t106)
  t113 = r1 <= f.p.dens_threshold
  t114 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t115 = 0.1e1 + t114
  t116 = t115 <= f.p.zeta_threshold
  t117 = t115 ** (0.1e1 / 0.3e1)
  t119 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t122 = f.my_piecewise3(t116, 0, 0.4e1 / 0.3e1 * t117 * t119)
  t123 = t122 * t30
  t124 = r1 ** 2
  t125 = r1 ** (0.1e1 / 0.3e1)
  t126 = t125 ** 2
  t128 = 0.1e1 / t126 / t124
  t131 = t37 * s2 * t128
  t134 = jnp.exp(-t45 * t131 / 0.24e2)
  t137 = 0.1e1 + t33 * t131 / 0.24e2
  t139 = t134 / t137
  t143 = 0.1e1 + t38 * s2 * t128 * t139 / 0.24e2
  t148 = f.my_piecewise3(t116, t64, t117 * t115)
  t149 = t148 * t68
  t152 = t5 * t149 * t143 / 0.8e1
  t154 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t123 * t143 - t152)
  t156 = t21 ** 2
  t157 = 0.1e1 / t156
  t158 = t26 ** 2
  t163 = t16 / t22 / t6
  t165 = -0.2e1 * t23 + 0.2e1 * t163
  t166 = f.my_piecewise5(t10, 0, t14, 0, t165)
  t170 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t157 * t158 + 0.4e1 / 0.3e1 * t21 * t166)
  t177 = t5 * t29 * t68 * t59
  t183 = 0.1e1 / t67 / t6
  t187 = t5 * t66 * t183 * t59 / 0.12e2
  t189 = t5 * t69 * t106
  t199 = 0.1e1 / t40 / t88 / t74
  t208 = t34 ** 2
  t209 = 0.1e1 / t208
  t210 = params.mu * t209
  t211 = t85 * s0
  t213 = t88 ** 2
  t215 = 0.1e1 / t213 / t39
  t216 = params.alpha ** 2
  t221 = t96 * t209
  t228 = t96 * params.mu * t209
  t241 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t170 * t30 * t59 - t177 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t106 + t187 - t189 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t73 * (0.11e2 / 0.27e2 * t38 * s0 / t41 / t88 * t55 - t87 * t199 * params.alpha * t55 / 0.24e2 - t98 * t85 * t199 * t102 / 0.24e2 + t210 * t211 * t215 * t216 * t55 / 0.324e3 + t221 * t211 * t215 * params.alpha * t102 / 0.162e3 + t228 * t211 * t215 * t50 / t100 / t53 / 0.162e3))
  t242 = t117 ** 2
  t243 = 0.1e1 / t242
  t244 = t119 ** 2
  t248 = f.my_piecewise5(t14, 0, t10, 0, -t165)
  t252 = f.my_piecewise3(t116, 0, 0.4e1 / 0.9e1 * t243 * t244 + 0.4e1 / 0.3e1 * t117 * t248)
  t259 = t5 * t122 * t68 * t143
  t264 = t5 * t148 * t183 * t143 / 0.12e2
  t266 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t252 * t30 * t143 - t259 / 0.4e1 + t264)
  d11 = 0.2e1 * t111 + 0.2e1 * t154 + t6 * (t241 + t266)
  t269 = -t7 - t24
  t270 = f.my_piecewise5(t10, 0, t14, 0, t269)
  t273 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t270)
  t274 = t273 * t30
  t279 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t274 * t59 - t72)
  t281 = f.my_piecewise5(t14, 0, t10, 0, -t269)
  t284 = f.my_piecewise3(t116, 0, 0.4e1 / 0.3e1 * t117 * t281)
  t285 = t284 * t30
  t289 = t148 * t30
  t290 = t124 * r1
  t297 = s2 ** 2
  t299 = t82 * t84 * t297
  t300 = t124 ** 2
  t303 = 0.1e1 / t125 / t300 / t124
  t309 = t137 ** 2
  t311 = t134 / t309
  t315 = -t38 * s2 / t126 / t290 * t139 / 0.9e1 + t299 * t303 * params.alpha * t139 / 0.216e3 + t98 * t297 * t303 * t311 / 0.216e3
  t320 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t285 * t143 - t152 - 0.3e1 / 0.8e1 * t5 * t289 * t315)
  t324 = 0.2e1 * t163
  t325 = f.my_piecewise5(t10, 0, t14, 0, t324)
  t329 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t157 * t270 * t26 + 0.4e1 / 0.3e1 * t21 * t325)
  t336 = t5 * t273 * t68 * t59
  t344 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t329 * t30 * t59 - t336 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t274 * t106 - t177 / 0.8e1 + t187 - t189 / 0.8e1)
  t348 = f.my_piecewise5(t14, 0, t10, 0, -t324)
  t352 = f.my_piecewise3(t116, 0, 0.4e1 / 0.9e1 * t243 * t281 * t119 + 0.4e1 / 0.3e1 * t117 * t348)
  t359 = t5 * t284 * t68 * t143
  t366 = t5 * t149 * t315
  t369 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t352 * t30 * t143 - t359 / 0.8e1 - t259 / 0.8e1 + t264 - 0.3e1 / 0.8e1 * t5 * t123 * t315 - t366 / 0.8e1)
  d12 = t111 + t154 + t279 + t320 + t6 * (t344 + t369)
  t374 = t270 ** 2
  t378 = 0.2e1 * t23 + 0.2e1 * t163
  t379 = f.my_piecewise5(t10, 0, t14, 0, t378)
  t383 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t157 * t374 + 0.4e1 / 0.3e1 * t21 * t379)
  t390 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t383 * t30 * t59 - t336 / 0.4e1 + t187)
  t391 = t281 ** 2
  t395 = f.my_piecewise5(t14, 0, t10, 0, -t378)
  t399 = f.my_piecewise3(t116, 0, 0.4e1 / 0.9e1 * t243 * t391 + 0.4e1 / 0.3e1 * t117 * t395)
  t417 = 0.1e1 / t125 / t300 / t290
  t426 = t297 * s2
  t428 = t300 ** 2
  t430 = 0.1e1 / t428 / t124
  t452 = f.my_piecewise3(t113, 0, -0.3e1 / 0.8e1 * t5 * t399 * t30 * t143 - t359 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t285 * t315 + t264 - t366 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t289 * (0.11e2 / 0.27e2 * t38 * s2 / t126 / t300 * t139 - t299 * t417 * params.alpha * t139 / 0.24e2 - t98 * t297 * t417 * t311 / 0.24e2 + t210 * t426 * t430 * t216 * t139 / 0.324e3 + t221 * t426 * t430 * params.alpha * t311 / 0.162e3 + t228 * t426 * t430 * t134 / t309 / t137 / 0.162e3))
  d22 = 0.2e1 * t279 + 0.2e1 * t320 + t6 * (t390 + t452)
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
  t55 = 0.1e1 / t53 / t51
  t57 = params.alpha * t44
  t59 = t49 * s0 * t55
  t62 = jnp.exp(-t57 * t59 / 0.24e2)
  t65 = 0.1e1 + t45 * t59 / 0.24e2
  t66 = 0.1e1 / t65
  t67 = t62 * t66
  t71 = 0.1e1 + t50 * s0 * t55 * t67 / 0.24e2
  t77 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t78 = t42 ** 2
  t79 = 0.1e1 / t78
  t80 = t77 * t79
  t84 = t77 * t42
  t85 = t51 * r0
  t92 = t44 ** 2
  t95 = 0.1e1 / t47 / t46
  t96 = s0 ** 2
  t98 = params.mu * t92 * t95 * t96
  t99 = t51 ** 2
  t102 = 0.1e1 / t52 / t99 / t51
  t107 = params.mu ** 2
  t109 = t107 * t92 * t95
  t111 = t65 ** 2
  t112 = 0.1e1 / t111
  t113 = t62 * t112
  t117 = -t50 * s0 / t53 / t85 * t67 / 0.9e1 + t98 * t102 * params.alpha * t67 / 0.216e3 + t109 * t96 * t102 * t113 / 0.216e3
  t121 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t122 = t121 * f.p.zeta_threshold
  t124 = f.my_piecewise3(t20, t122, t21 * t19)
  t126 = 0.1e1 / t78 / t6
  t127 = t124 * t126
  t131 = t124 * t79
  t135 = t124 * t42
  t144 = 0.1e1 / t52 / t99 / t85
  t153 = t46 ** 2
  t154 = 0.1e1 / t153
  t155 = params.mu * t154
  t156 = t96 * s0
  t157 = t155 * t156
  t158 = t99 ** 2
  t160 = 0.1e1 / t158 / t51
  t161 = params.alpha ** 2
  t166 = t107 * t154
  t167 = t166 * t156
  t173 = t107 * params.mu * t154
  t174 = t173 * t156
  t177 = 0.1e1 / t111 / t65
  t181 = 0.11e2 / 0.27e2 * t50 * s0 / t53 / t99 * t67 - t98 * t144 * params.alpha * t67 / 0.24e2 - t109 * t96 * t144 * t113 / 0.24e2 + t157 * t160 * t161 * t67 / 0.324e3 + t167 * t160 * params.alpha * t113 / 0.162e3 + t174 * t160 * t62 * t177 / 0.162e3
  t186 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t71 - t5 * t80 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t84 * t117 + t5 * t127 * t71 / 0.12e2 - t5 * t131 * t117 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t135 * t181)
  t188 = r1 <= f.p.dens_threshold
  t189 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t190 = 0.1e1 + t189
  t191 = t190 <= f.p.zeta_threshold
  t192 = t190 ** (0.1e1 / 0.3e1)
  t193 = t192 ** 2
  t194 = 0.1e1 / t193
  t196 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t197 = t196 ** 2
  t201 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t205 = f.my_piecewise3(t191, 0, 0.4e1 / 0.9e1 * t194 * t197 + 0.4e1 / 0.3e1 * t192 * t201)
  t207 = r1 ** 2
  t208 = r1 ** (0.1e1 / 0.3e1)
  t209 = t208 ** 2
  t211 = 0.1e1 / t209 / t207
  t214 = t49 * s2 * t211
  t217 = jnp.exp(-t57 * t214 / 0.24e2)
  t226 = 0.1e1 + t50 * s2 * t211 * t217 / (0.1e1 + t45 * t214 / 0.24e2) / 0.24e2
  t232 = f.my_piecewise3(t191, 0, 0.4e1 / 0.3e1 * t192 * t196)
  t238 = f.my_piecewise3(t191, t122, t192 * t190)
  t244 = f.my_piecewise3(t188, 0, -0.3e1 / 0.8e1 * t5 * t205 * t42 * t226 - t5 * t232 * t79 * t226 / 0.4e1 + t5 * t238 * t126 * t226 / 0.12e2)
  t254 = t24 ** 2
  t258 = 0.6e1 * t33 - 0.6e1 * t16 / t254
  t259 = f.my_piecewise5(t10, 0, t14, 0, t258)
  t263 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t259)
  t286 = 0.1e1 / t78 / t24
  t297 = t99 * r0
  t305 = 0.1e1 / t52 / t158
  t315 = 0.1e1 / t158 / t85
  t328 = t96 ** 2
  t332 = t328 / t53 / t158 / t297
  t355 = t107 ** 2
  t358 = t111 ** 2
  t370 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t263 * t42 * t71 - 0.3e1 / 0.8e1 * t5 * t41 * t79 * t71 - 0.9e1 / 0.8e1 * t5 * t43 * t117 + t5 * t77 * t126 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t80 * t117 - 0.9e1 / 0.8e1 * t5 * t84 * t181 - 0.5e1 / 0.36e2 * t5 * t124 * t286 * t71 + t5 * t127 * t117 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t131 * t181 - 0.3e1 / 0.8e1 * t5 * t135 * (-0.154e3 / 0.81e2 * t50 * s0 / t53 / t297 * t67 + 0.341e3 / 0.972e3 * t98 * t305 * params.alpha * t67 + 0.341e3 / 0.972e3 * t109 * t96 * t305 * t113 - 0.19e2 / 0.324e3 * t157 * t315 * t161 * t67 - 0.19e2 / 0.162e3 * t167 * t315 * params.alpha * t113 - 0.19e2 / 0.162e3 * t174 * t315 * t62 * t177 + t155 * t332 * t161 * params.alpha * t44 * t49 * t62 * t66 / 0.2916e4 + t166 * t332 * t161 * t62 * t112 * t44 * t49 / 0.972e3 + t173 * t332 * params.alpha * t62 * t177 * t44 * t49 / 0.486e3 + t355 * t154 * t332 * t62 / t358 * t44 * t49 / 0.486e3))
  t380 = f.my_piecewise5(t14, 0, t10, 0, -t258)
  t384 = f.my_piecewise3(t191, 0, -0.8e1 / 0.27e2 / t193 / t190 * t197 * t196 + 0.4e1 / 0.3e1 * t194 * t196 * t201 + 0.4e1 / 0.3e1 * t192 * t380)
  t402 = f.my_piecewise3(t188, 0, -0.3e1 / 0.8e1 * t5 * t384 * t42 * t226 - 0.3e1 / 0.8e1 * t5 * t205 * t79 * t226 + t5 * t232 * t126 * t226 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t238 * t286 * t226)
  d111 = 0.3e1 * t186 + 0.3e1 * t244 + t6 * (t370 + t402)

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
  t67 = 0.1e1 / t65 / t63
  t69 = params.alpha * t56
  t71 = t61 * s0 * t67
  t74 = jnp.exp(-t69 * t71 / 0.24e2)
  t77 = 0.1e1 + t57 * t71 / 0.24e2
  t78 = 0.1e1 / t77
  t79 = t74 * t78
  t83 = 0.1e1 + t62 * s0 * t67 * t79 / 0.24e2
  t92 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t93 = t54 ** 2
  t94 = 0.1e1 / t93
  t95 = t92 * t94
  t99 = t92 * t54
  t100 = t63 * r0
  t107 = t56 ** 2
  t110 = 0.1e1 / t59 / t58
  t111 = s0 ** 2
  t113 = params.mu * t107 * t110 * t111
  t114 = t63 ** 2
  t115 = t114 * t63
  t117 = 0.1e1 / t64 / t115
  t122 = params.mu ** 2
  t124 = t122 * t107 * t110
  t126 = t77 ** 2
  t127 = 0.1e1 / t126
  t128 = t74 * t127
  t132 = -t62 * s0 / t65 / t100 * t79 / 0.9e1 + t113 * t117 * params.alpha * t79 / 0.216e3 + t124 * t111 * t117 * t128 / 0.216e3
  t138 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t140 = 0.1e1 / t93 / t6
  t141 = t138 * t140
  t145 = t138 * t94
  t149 = t138 * t54
  t158 = 0.1e1 / t64 / t114 / t100
  t167 = t58 ** 2
  t168 = 0.1e1 / t167
  t169 = params.mu * t168
  t170 = t111 * s0
  t171 = t169 * t170
  t172 = t114 ** 2
  t174 = 0.1e1 / t172 / t63
  t175 = params.alpha ** 2
  t180 = t122 * t168
  t181 = t180 * t170
  t187 = t122 * params.mu * t168
  t188 = t187 * t170
  t191 = 0.1e1 / t126 / t77
  t195 = 0.11e2 / 0.27e2 * t62 * s0 / t65 / t114 * t79 - t113 * t158 * params.alpha * t79 / 0.24e2 - t124 * t111 * t158 * t128 / 0.24e2 + t171 * t174 * t175 * t79 / 0.324e3 + t181 * t174 * params.alpha * t128 / 0.162e3 + t188 * t174 * t74 * t191 / 0.162e3
  t199 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t200 = t199 * f.p.zeta_threshold
  t202 = f.my_piecewise3(t20, t200, t21 * t19)
  t204 = 0.1e1 / t93 / t25
  t205 = t202 * t204
  t209 = t202 * t140
  t213 = t202 * t94
  t217 = t202 * t54
  t218 = t114 * r0
  t226 = 0.1e1 / t64 / t172
  t236 = 0.1e1 / t172 / t100
  t249 = t111 ** 2
  t253 = t249 / t65 / t172 / t218
  t255 = t175 * params.alpha
  t259 = t255 * t56 * t61 * t74 * t78
  t263 = t175 * t74
  t266 = t263 * t127 * t56 * t61
  t270 = params.alpha * t74
  t273 = t270 * t191 * t56 * t61
  t276 = t122 ** 2
  t277 = t276 * t168
  t279 = t126 ** 2
  t280 = 0.1e1 / t279
  t283 = t74 * t280 * t56 * t61
  t286 = -0.154e3 / 0.81e2 * t62 * s0 / t65 / t218 * t79 + 0.341e3 / 0.972e3 * t113 * t226 * params.alpha * t79 + 0.341e3 / 0.972e3 * t124 * t111 * t226 * t128 - 0.19e2 / 0.324e3 * t171 * t236 * t175 * t79 - 0.19e2 / 0.162e3 * t181 * t236 * params.alpha * t128 - 0.19e2 / 0.162e3 * t188 * t236 * t74 * t191 + t169 * t253 * t259 / 0.2916e4 + t180 * t253 * t266 / 0.972e3 + t187 * t253 * t273 / 0.486e3 + t277 * t253 * t283 / 0.486e3
  t291 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t83 - 0.3e1 / 0.8e1 * t5 * t95 * t83 - 0.9e1 / 0.8e1 * t5 * t99 * t132 + t5 * t141 * t83 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t145 * t132 - 0.9e1 / 0.8e1 * t5 * t149 * t195 - 0.5e1 / 0.36e2 * t5 * t205 * t83 + t5 * t209 * t132 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t213 * t195 - 0.3e1 / 0.8e1 * t5 * t217 * t286)
  t293 = r1 <= f.p.dens_threshold
  t294 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t295 = 0.1e1 + t294
  t296 = t295 <= f.p.zeta_threshold
  t297 = t295 ** (0.1e1 / 0.3e1)
  t298 = t297 ** 2
  t300 = 0.1e1 / t298 / t295
  t302 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t303 = t302 ** 2
  t307 = 0.1e1 / t298
  t308 = t307 * t302
  t310 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t314 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t318 = f.my_piecewise3(t296, 0, -0.8e1 / 0.27e2 * t300 * t303 * t302 + 0.4e1 / 0.3e1 * t308 * t310 + 0.4e1 / 0.3e1 * t297 * t314)
  t320 = r1 ** 2
  t321 = r1 ** (0.1e1 / 0.3e1)
  t322 = t321 ** 2
  t324 = 0.1e1 / t322 / t320
  t327 = t61 * s2 * t324
  t330 = jnp.exp(-t69 * t327 / 0.24e2)
  t339 = 0.1e1 + t62 * s2 * t324 * t330 / (0.1e1 + t57 * t327 / 0.24e2) / 0.24e2
  t348 = f.my_piecewise3(t296, 0, 0.4e1 / 0.9e1 * t307 * t303 + 0.4e1 / 0.3e1 * t297 * t310)
  t355 = f.my_piecewise3(t296, 0, 0.4e1 / 0.3e1 * t297 * t302)
  t361 = f.my_piecewise3(t296, t200, t297 * t295)
  t367 = f.my_piecewise3(t293, 0, -0.3e1 / 0.8e1 * t5 * t318 * t54 * t339 - 0.3e1 / 0.8e1 * t5 * t348 * t94 * t339 + t5 * t355 * t140 * t339 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t361 * t204 * t339)
  t378 = t172 ** 2
  t382 = t249 * s0 / t64 / t378 / r0
  t399 = 0.1e1 / t64 / t172 / r0
  t407 = t249 / t65 / t172 / t115
  t416 = 0.1e1 / t172 / t114
  t439 = t175 ** 2
  t441 = t110 * t74
  t464 = 0.2e1 / 0.2187e4 * t276 * params.mu * t168 * t382 * t74 / t279 / t77 * t107 * t110 + 0.2618e4 / 0.243e3 * t62 * s0 / t65 / t115 * t79 - 0.3047e4 / 0.972e3 * t113 * t399 * params.alpha * t79 - 0.49e2 / 0.729e3 * t277 * t407 * t283 - 0.3047e4 / 0.972e3 * t124 * t111 * t399 * t128 + 0.2563e4 / 0.2916e4 * t171 * t416 * t175 * t79 + 0.2563e4 / 0.1458e4 * t181 * t416 * params.alpha * t128 + 0.2563e4 / 0.1458e4 * t188 * t416 * t74 * t191 - 0.49e2 / 0.4374e4 * t169 * t407 * t259 - 0.49e2 / 0.1458e4 * t180 * t407 * t266 - 0.49e2 / 0.729e3 * t187 * t407 * t273 + t169 * t382 * t439 * t107 * t441 * t78 / 0.26244e5 + t180 * t382 * t255 * t107 * t441 * t127 / 0.6561e4 + t187 * t382 * t263 * t191 * t107 * t110 / 0.2187e4 + 0.2e1 / 0.2187e4 * t277 * t382 * t270 * t280 * t107 * t110
  t468 = t19 ** 2
  t471 = t30 ** 2
  t477 = t41 ** 2
  t486 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t487 = f.my_piecewise5(t10, 0, t14, 0, t486)
  t491 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t468 * t471 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t477 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t487)
  t529 = 0.1e1 / t93 / t36
  t534 = t5 * t209 * t195 / 0.2e1 - t5 * t213 * t286 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t217 * t464 - 0.3e1 / 0.8e1 * t5 * t491 * t54 * t83 - 0.3e1 / 0.2e1 * t5 * t55 * t132 - 0.3e1 / 0.2e1 * t5 * t95 * t132 - 0.9e1 / 0.4e1 * t5 * t99 * t195 + t5 * t141 * t132 - 0.3e1 / 0.2e1 * t5 * t145 * t195 - 0.3e1 / 0.2e1 * t5 * t149 * t286 - 0.5e1 / 0.9e1 * t5 * t205 * t132 - t5 * t53 * t94 * t83 / 0.2e1 + t5 * t92 * t140 * t83 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t138 * t204 * t83 + 0.10e2 / 0.27e2 * t5 * t202 * t529 * t83
  t535 = f.my_piecewise3(t1, 0, t534)
  t536 = t295 ** 2
  t539 = t303 ** 2
  t545 = t310 ** 2
  t551 = f.my_piecewise5(t14, 0, t10, 0, -t486)
  t555 = f.my_piecewise3(t296, 0, 0.40e2 / 0.81e2 / t298 / t536 * t539 - 0.16e2 / 0.9e1 * t300 * t303 * t310 + 0.4e1 / 0.3e1 * t307 * t545 + 0.16e2 / 0.9e1 * t308 * t314 + 0.4e1 / 0.3e1 * t297 * t551)
  t577 = f.my_piecewise3(t293, 0, -0.3e1 / 0.8e1 * t5 * t555 * t54 * t339 - t5 * t318 * t94 * t339 / 0.2e1 + t5 * t348 * t140 * t339 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t355 * t204 * t339 + 0.10e2 / 0.27e2 * t5 * t361 * t529 * t339)
  d1111 = 0.4e1 * t291 + 0.4e1 * t367 + t6 * (t535 + t577)

  res = {'v4rho4': d1111}
  return res
