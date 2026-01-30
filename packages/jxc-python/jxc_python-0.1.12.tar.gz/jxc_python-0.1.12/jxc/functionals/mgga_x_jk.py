"""Generated from mgga_x_jk.mpl."""

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

  y = lambda x, u: x ** 2 - u

  gBecke = lambda x: b88_f(x) - 1

  jk_f = lambda x, u, t=None: 1 + gBecke(x) / (1 + 2 * y(x, u) / x ** 2)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, jk_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
      f.xt(r0, r1, s0, s1, s2),
      f.xs0(r0, r1, s0, s2),
      f.xs1(r0, r1, s0, s2),
      f.u0(r0, r1, l0, l1),
      f.u1(r0, r1, l0, l1),
      f.tt0(r0, r1, tau0, tau1),
      f.tt1(r0, r1, tau0, tau1),
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

  y = lambda x, u: x ** 2 - u

  gBecke = lambda x: b88_f(x) - 1

  jk_f = lambda x, u, t=None: 1 + gBecke(x) / (1 + 2 * y(x, u) / x ** 2)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, jk_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
      f.xt(r0 / 2, r0 / 2, s0 / 4, s0 / 4, s0 / 4),
      f.xs0(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.xs1(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.u0(r0 / 2, r0 / 2, l0 / 2, l0 / 2),
      f.u1(r0 / 2, r0 / 2, l0 / 2, l0 / 2),
      f.tt0(r0 / 2, r0 / 2, tau0 / 2, tau0 / 2),
      f.tt1(r0 / 2, r0 / 2, tau0 / 2, tau0 / 2),
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

  y = lambda x, u: x ** 2 - u

  gBecke = lambda x: b88_f(x) - 1

  jk_f = lambda x, u, t=None: 1 + gBecke(x) / (1 + 2 * y(x, u) / x ** 2)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, jk_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
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
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = t32 * t33
  t35 = t29 * t34
  t36 = r0 ** 2
  t37 = r0 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = t38 * t36
  t40 = 0.1e1 / t39
  t41 = s0 * t40
  t42 = params.gamma * params.beta
  t43 = jnp.sqrt(s0)
  t45 = 0.1e1 / t37 / r0
  t46 = t43 * t45
  t47 = jnp.arcsinh(t46)
  t50 = t42 * t46 * t47 + 0.1e1
  t51 = 0.1e1 / t50
  t52 = t38 * r0
  t53 = 0.1e1 / t52
  t56 = -0.2e1 * l0 * t53 + 0.2e1 * t41
  t57 = 0.1e1 / s0
  t58 = t56 * t57
  t60 = t58 * t39 + 0.1e1
  t61 = 0.1e1 / t60
  t62 = t51 * t61
  t66 = 0.1e1 + 0.2e1 / 0.9e1 * t35 * t41 * t62
  t70 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t66)
  t71 = r1 <= f.p.dens_threshold
  t72 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t73 = 0.1e1 + t72
  t74 = t73 <= f.p.zeta_threshold
  t75 = t73 ** (0.1e1 / 0.3e1)
  t77 = f.my_piecewise3(t74, t22, t75 * t73)
  t78 = t77 * t26
  t79 = r1 ** 2
  t80 = r1 ** (0.1e1 / 0.3e1)
  t81 = t80 ** 2
  t82 = t81 * t79
  t83 = 0.1e1 / t82
  t84 = s2 * t83
  t85 = jnp.sqrt(s2)
  t87 = 0.1e1 / t80 / r1
  t88 = t85 * t87
  t89 = jnp.arcsinh(t88)
  t92 = t42 * t88 * t89 + 0.1e1
  t93 = 0.1e1 / t92
  t94 = t81 * r1
  t95 = 0.1e1 / t94
  t98 = -0.2e1 * l1 * t95 + 0.2e1 * t84
  t99 = 0.1e1 / s2
  t100 = t98 * t99
  t102 = t100 * t82 + 0.1e1
  t103 = 0.1e1 / t102
  t104 = t93 * t103
  t108 = 0.1e1 + 0.2e1 / 0.9e1 * t35 * t84 * t104
  t112 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t78 * t108)
  t113 = t6 ** 2
  t115 = t16 / t113
  t116 = t7 - t115
  t117 = f.my_piecewise5(t10, 0, t14, 0, t116)
  t120 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t117)
  t125 = t26 ** 2
  t126 = 0.1e1 / t125
  t130 = t5 * t25 * t126 * t66 / 0.8e1
  t134 = s0 / t38 / t36 / r0
  t138 = t50 ** 2
  t140 = 0.1e1 / t138 * t61
  t147 = jnp.sqrt(0.1e1 + t41)
  t148 = 0.1e1 / t147
  t157 = t60 ** 2
  t158 = 0.1e1 / t157
  t159 = t51 * t158
  t178 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t120 * t26 * t66 - t130 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.16e2 / 0.27e2 * t35 * t134 * t62 - 0.2e1 / 0.9e1 * t35 * t41 * t140 * (-0.4e1 / 0.3e1 * t42 * t43 / t37 / t36 * t47 - 0.4e1 / 0.3e1 * t42 * t134 * t148) - 0.2e1 / 0.9e1 * t35 * t41 * t159 * ((-0.16e2 / 0.3e1 * t134 + 0.10e2 / 0.3e1 * l0 * t40) * t57 * t39 + 0.8e1 / 0.3e1 * t58 * t52)))
  t180 = f.my_piecewise5(t14, 0, t10, 0, -t116)
  t183 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t75 * t180)
  t191 = t5 * t77 * t126 * t108 / 0.8e1
  t193 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t183 * t26 * t108 - t191)
  vrho_0_ = t70 + t112 + t6 * (t178 + t193)
  t196 = -t7 - t115
  t197 = f.my_piecewise5(t10, 0, t14, 0, t196)
  t200 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t197)
  t206 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t200 * t26 * t66 - t130)
  t208 = f.my_piecewise5(t14, 0, t10, 0, -t196)
  t211 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t75 * t208)
  t219 = s2 / t81 / t79 / r1
  t223 = t92 ** 2
  t225 = 0.1e1 / t223 * t103
  t232 = jnp.sqrt(0.1e1 + t84)
  t233 = 0.1e1 / t232
  t242 = t102 ** 2
  t243 = 0.1e1 / t242
  t244 = t93 * t243
  t263 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t211 * t26 * t108 - t191 - 0.3e1 / 0.8e1 * t5 * t78 * (-0.16e2 / 0.27e2 * t35 * t219 * t104 - 0.2e1 / 0.9e1 * t35 * t84 * t225 * (-0.4e1 / 0.3e1 * t42 * t85 / t80 / t79 * t89 - 0.4e1 / 0.3e1 * t42 * t219 * t233) - 0.2e1 / 0.9e1 * t35 * t84 * t244 * ((-0.16e2 / 0.3e1 * t219 + 0.10e2 / 0.3e1 * l1 * t83) * t99 * t82 + 0.8e1 / 0.3e1 * t100 * t94)))
  vrho_1_ = t70 + t112 + t6 * (t206 + t263)
  t266 = t29 * t32
  t282 = s0 ** 2
  t295 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.2e1 / 0.9e1 * t266 * t33 * t40 * t62 - 0.2e1 / 0.9e1 * t35 * t41 * t140 * (t42 / t43 * t45 * t47 / 0.2e1 + t42 * t40 * t148 / 0.2e1) - 0.2e1 / 0.9e1 * t35 * t41 * t159 * (0.2e1 * t57 - t56 / t282 * t39)))
  vsigma_0_ = t6 * t295
  vsigma_1_ = 0.0e0
  t311 = s2 ** 2
  t324 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t78 * (0.2e1 / 0.9e1 * t266 * t33 * t83 * t104 - 0.2e1 / 0.9e1 * t35 * t84 * t225 * (t42 / t85 * t87 * t89 / 0.2e1 + t42 * t83 * t233 / 0.2e1) - 0.2e1 / 0.9e1 * t35 * t84 * t244 * (0.2e1 * t99 - t98 / t311 * t82)))
  vsigma_2_ = t6 * t324
  t326 = t26 * params.beta
  t333 = f.my_piecewise3(t1, 0, -t4 * t25 * t326 * t34 * t53 * t51 * t158 / 0.2e1)
  vlapl_0_ = t6 * t333
  t341 = f.my_piecewise3(t71, 0, -t4 * t77 * t326 * t34 * t95 * t93 * t243 / 0.2e1)
  vlapl_1_ = t6 * t341
  vtau_0_ = 0.0e0
  vtau_1_ = 0.0e0
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  vsigma_0_ = _b(vsigma_0_)
  vsigma_1_ = _b(vsigma_1_)
  vsigma_2_ = _b(vsigma_2_)
  vlapl_0_ = _b(vlapl_0_)
  vlapl_1_ = _b(vlapl_1_)
  vtau_0_ = _b(vtau_0_)
  vtau_1_ = _b(vtau_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1), 'vsigma': jnp.stack([vsigma_0_, vsigma_1_, vsigma_2_], axis=-1), 'vlapl': jnp.stack([vlapl_0_, vlapl_1_], axis=-1), 'vtau':  jnp.stack([vtau_0_, vtau_1_], axis=-1)}
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

  y = lambda x, u: x ** 2 - u

  gBecke = lambda x: b88_f(x) - 1

  jk_f = lambda x, u, t=None: 1 + gBecke(x) / (1 + 2 * y(x, u) / x ** 2)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, jk_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t6 = t3 * t5
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
  t25 = 4 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t23 * t25
  t27 = t21 * t26
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = s0 * t29
  t31 = r0 ** 2
  t32 = t18 ** 2
  t33 = t32 * t31
  t34 = 0.1e1 / t33
  t35 = params.gamma * params.beta
  t36 = jnp.sqrt(s0)
  t37 = t35 * t36
  t39 = 0.1e1 / t18 / r0
  t43 = jnp.arcsinh(t36 * t28 * t39)
  t44 = t28 * t39 * t43
  t46 = t37 * t44 + 0.1e1
  t47 = 0.1e1 / t46
  t49 = t30 * t34
  t50 = l0 * t29
  t51 = t32 * r0
  t55 = 0.2e1 * t49 - 0.2e1 * t50 / t51
  t56 = 0.1e1 / s0
  t57 = t55 * t56
  t58 = t28 * t33
  t61 = 0.1e1 + t57 * t58 / 0.2e1
  t62 = 0.1e1 / t61
  t67 = 0.1e1 + 0.2e1 / 0.9e1 * t27 * t30 * t34 * t47 * t62
  t71 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t67)
  t79 = 0.1e1 / t32 / t31 / r0
  t86 = t21 * t26 * s0
  t87 = t29 * t34
  t88 = t46 ** 2
  t90 = 0.1e1 / t88 * t62
  t99 = jnp.sqrt(0.1e1 + t49)
  t100 = 0.1e1 / t99
  t109 = t61 ** 2
  t110 = 0.1e1 / t109
  t111 = t47 * t110
  t133 = f.my_piecewise3(t2, 0, -t6 * t17 / t32 * t67 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.16e2 / 0.27e2 * t27 * t30 * t79 * t47 * t62 - 0.2e1 / 0.9e1 * t86 * t87 * t90 * (-0.4e1 / 0.3e1 * t37 * t28 / t18 / t31 * t43 - 0.4e1 / 0.3e1 * t35 * s0 * t29 * t79 * t100) - 0.2e1 / 0.9e1 * t86 * t87 * t111 * ((-0.16e2 / 0.3e1 * t30 * t79 + 0.10e2 / 0.3e1 * t50 * t34) * t56 * t58 / 0.2e1 + 0.4e1 / 0.3e1 * t57 * t28 * t51)))
  vrho_0_ = 0.2e1 * r0 * t133 + 0.2e1 * t71
  t150 = s0 ** 2
  t164 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.2e1 / 0.9e1 * t27 * t87 * t47 * t62 - 0.2e1 / 0.9e1 * t86 * t87 * t90 * (t35 / t36 * t44 / 0.2e1 + t35 * t87 * t100 / 0.2e1) - 0.2e1 / 0.9e1 * t86 * t87 * t111 * (0.2e1 * t56 - t55 / t150 * t58 / 0.2e1)))
  vsigma_0_ = 0.2e1 * r0 * t164
  t174 = f.my_piecewise3(t2, 0, -t5 * t17 * t39 * params.beta * t26 * t29 * t47 * t110 / 0.2e1)
  vlapl_0_ = 0.2e1 * r0 * t174
  vtau_0_ = 0.0e0
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
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
  t22 = t3 ** 2
  t23 = params.beta * t22
  t25 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t27 = 4 ** (0.1e1 / 0.3e1)
  t28 = 0.1e1 / t25 * t27
  t29 = t23 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t34 = t19 * t33
  t35 = 0.1e1 / t34
  t36 = params.gamma * params.beta
  t37 = jnp.sqrt(s0)
  t38 = t36 * t37
  t40 = 0.1e1 / t18 / r0
  t44 = jnp.arcsinh(t37 * t30 * t40)
  t47 = t38 * t30 * t40 * t44 + 0.1e1
  t48 = 0.1e1 / t47
  t50 = t32 * t35
  t51 = l0 * t31
  t52 = t19 * r0
  t53 = 0.1e1 / t52
  t56 = 0.1e1 / s0
  t57 = (-t51 * t53 + t50) * t56
  t58 = t30 * t34
  t60 = t57 * t58 + 0.1e1
  t61 = 0.1e1 / t60
  t66 = 0.1e1 + 0.2e1 / 0.9e1 * t29 * t32 * t35 * t48 * t61
  t70 = t17 * t18
  t71 = t33 * r0
  t73 = 0.1e1 / t19 / t71
  t80 = t23 * t28 * s0
  t81 = t31 * t35
  t82 = t47 ** 2
  t83 = 0.1e1 / t82
  t84 = t83 * t61
  t90 = t36 * s0
  t91 = t31 * t73
  t92 = 0.1e1 + t50
  t93 = jnp.sqrt(t92)
  t94 = 0.1e1 / t93
  t98 = -0.4e1 / 0.3e1 * t38 * t30 / t18 / t33 * t44 - 0.4e1 / 0.3e1 * t90 * t91 * t94
  t99 = t84 * t98
  t103 = t60 ** 2
  t104 = 0.1e1 / t103
  t105 = t48 * t104
  t111 = (-0.8e1 / 0.3e1 * t32 * t73 + 0.5e1 / 0.3e1 * t51 * t35) * t56
  t113 = t30 * t52
  t116 = t111 * t58 + 0.8e1 / 0.3e1 * t57 * t113
  t117 = t105 * t116
  t121 = -0.16e2 / 0.27e2 * t29 * t32 * t73 * t48 * t61 - 0.2e1 / 0.9e1 * t80 * t81 * t99 - 0.2e1 / 0.9e1 * t80 * t81 * t117
  t126 = f.my_piecewise3(t2, 0, -t6 * t21 * t66 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t70 * t121)
  t135 = t33 ** 2
  t137 = 0.1e1 / t19 / t135
  t152 = t98 ** 2
  t173 = s0 ** 2
  t192 = t116 ** 2
  t219 = f.my_piecewise3(t2, 0, t6 * t17 * t53 * t66 / 0.12e2 - t6 * t21 * t121 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t70 * (0.176e3 / 0.81e2 * t29 * t32 * t137 * t48 * t61 + 0.32e2 / 0.27e2 * t80 * t91 * t99 + 0.32e2 / 0.27e2 * t80 * t91 * t117 + 0.4e1 / 0.9e1 * t80 * t81 / t82 / t47 * t61 * t152 + 0.4e1 / 0.9e1 * t80 * t81 * t83 * t104 * t98 * t116 - 0.2e1 / 0.9e1 * t80 * t81 * t84 * (0.28e2 / 0.9e1 * t38 * t30 / t18 / t71 * t44 + 0.20e2 / 0.3e1 * t90 * t31 * t137 * t94 - 0.32e2 / 0.9e1 * t36 * t173 * t30 / t18 / t135 / t71 / t93 / t92) + 0.4e1 / 0.9e1 * t80 * t81 * t48 / t103 / t60 * t192 - 0.2e1 / 0.9e1 * t80 * t81 * t105 * ((0.88e2 / 0.9e1 * t32 * t137 - 0.40e2 / 0.9e1 * t51 * t73) * t56 * t58 + 0.16e2 / 0.3e1 * t111 * t113 + 0.40e2 / 0.9e1 * t57 * t30 * t19)))
  v2rho2_0_ = 0.2e1 * r0 * t219 + 0.4e1 * t126
  res = {'v2rho2': v2rho2_0_}
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
  t21 = 0.1e1 / t20
  t22 = t17 * t21
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
  t35 = t19 * t34
  t36 = 0.1e1 / t35
  t37 = params.gamma * params.beta
  t38 = jnp.sqrt(s0)
  t39 = t37 * t38
  t41 = 0.1e1 / t18 / r0
  t45 = jnp.asinh(t38 * t31 * t41)
  t48 = t39 * t31 * t41 * t45 + 0.1e1
  t49 = 0.1e1 / t48
  t51 = t33 * t36
  t52 = l0 * t32
  t55 = 0.1e1 / s0
  t56 = (-t52 * t21 + t51) * t55
  t57 = t31 * t35
  t59 = t56 * t57 + 0.1e1
  t60 = 0.1e1 / t59
  t65 = 0.1e1 + 0.2e1 / 0.9e1 * t30 * t33 * t36 * t49 * t60
  t70 = t17 / t19
  t71 = t34 * r0
  t73 = 0.1e1 / t19 / t71
  t80 = t24 * t29 * s0
  t81 = t32 * t36
  t82 = t48 ** 2
  t83 = 0.1e1 / t82
  t84 = t83 * t60
  t90 = t37 * s0
  t91 = t32 * t73
  t92 = 0.1e1 + t51
  t93 = jnp.sqrt(t92)
  t94 = 0.1e1 / t93
  t98 = -0.4e1 / 0.3e1 * t39 * t31 / t18 / t34 * t45 - 0.4e1 / 0.3e1 * t90 * t91 * t94
  t99 = t84 * t98
  t103 = t59 ** 2
  t104 = 0.1e1 / t103
  t105 = t49 * t104
  t111 = (-0.8e1 / 0.3e1 * t33 * t73 + 0.5e1 / 0.3e1 * t52 * t36) * t55
  t113 = t31 * t20
  t116 = t111 * t57 + 0.8e1 / 0.3e1 * t56 * t113
  t117 = t105 * t116
  t121 = -0.16e2 / 0.27e2 * t30 * t33 * t73 * t49 * t60 - 0.2e1 / 0.9e1 * t80 * t81 * t99 - 0.2e1 / 0.9e1 * t80 * t81 * t117
  t125 = t17 * t18
  t126 = t34 ** 2
  t128 = 0.1e1 / t19 / t126
  t141 = 0.1e1 / t82 / t48
  t143 = t98 ** 2
  t144 = t141 * t60 * t143
  t148 = t81 * t83
  t149 = t104 * t98
  t150 = t149 * t116
  t160 = t32 * t128
  t164 = s0 ** 2
  t165 = t37 * t164
  t171 = 0.1e1 / t93 / t92
  t175 = 0.28e2 / 0.9e1 * t39 * t31 / t18 / t71 * t45 + 0.20e2 / 0.3e1 * t90 * t160 * t94 - 0.32e2 / 0.9e1 * t165 * t31 / t18 / t126 / t71 * t171
  t176 = t84 * t175
  t181 = 0.1e1 / t103 / t59
  t183 = t116 ** 2
  t184 = t49 * t181 * t183
  t193 = (0.88e2 / 0.9e1 * t33 * t128 - 0.40e2 / 0.9e1 * t52 * t73) * t55
  t197 = t31 * t19
  t200 = t193 * t57 + 0.16e2 / 0.3e1 * t111 * t113 + 0.40e2 / 0.9e1 * t56 * t197
  t201 = t105 * t200
  t205 = 0.176e3 / 0.81e2 * t30 * t33 * t128 * t49 * t60 + 0.32e2 / 0.27e2 * t80 * t91 * t99 + 0.32e2 / 0.27e2 * t80 * t91 * t117 + 0.4e1 / 0.9e1 * t80 * t81 * t144 + 0.4e1 / 0.9e1 * t80 * t148 * t150 - 0.2e1 / 0.9e1 * t80 * t81 * t176 + 0.4e1 / 0.9e1 * t80 * t81 * t184 - 0.2e1 / 0.9e1 * t80 * t81 * t201
  t210 = f.my_piecewise3(t2, 0, t6 * t22 * t65 / 0.12e2 - t6 * t70 * t121 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t125 * t205)
  t241 = 0.1e1 / t19 / t126 / r0
  t246 = t126 ** 2
  t257 = t92 ** 2
  t309 = t82 ** 2
  t317 = t81 * t141
  t337 = t103 ** 2
  t351 = -0.4e1 / 0.3e1 * t80 * t148 * t181 * t98 * t183 + 0.16e2 / 0.9e1 * t80 * t91 * t176 + 0.16e2 / 0.9e1 * t80 * t91 * t201 - 0.2e1 / 0.9e1 * t80 * t81 * t84 * (-0.280e3 / 0.27e2 * t39 * t31 / t18 / t126 * t45 - 0.952e3 / 0.27e2 * t90 * t32 * t241 * t94 + 0.1184e4 / 0.27e2 * t165 * t31 / t18 / t246 * t171 - 0.256e3 / 0.9e1 * t37 * t164 * s0 / t246 / t71 / t93 / t257) - 0.2e1 / 0.9e1 * t80 * t81 * t105 * ((-0.1232e4 / 0.27e2 * t33 * t241 + 0.440e3 / 0.27e2 * t52 * t128) * t55 * t57 + 0.8e1 * t193 * t113 + 0.40e2 / 0.3e1 * t111 * t197 + 0.80e2 / 0.27e2 * t56 * t31 / t18) - 0.2464e4 / 0.243e3 * t30 * t33 * t241 * t49 * t60 - 0.176e3 / 0.27e2 * t80 * t160 * t99 - 0.176e3 / 0.27e2 * t80 * t160 * t117 - 0.32e2 / 0.9e1 * t80 * t91 * t144 - 0.32e2 / 0.9e1 * t80 * t91 * t83 * t150 - 0.32e2 / 0.9e1 * t80 * t91 * t184 - 0.4e1 / 0.3e1 * t80 * t81 / t309 * t60 * t143 * t98 - 0.4e1 / 0.3e1 * t80 * t317 * t104 * t143 * t116 + 0.4e1 / 0.3e1 * t80 * t317 * t60 * t98 * t175 + 0.2e1 / 0.3e1 * t80 * t148 * t104 * t175 * t116 + 0.2e1 / 0.3e1 * t80 * t148 * t149 * t200 - 0.4e1 / 0.3e1 * t80 * t81 * t49 / t337 * t183 * t116 + 0.4e1 / 0.3e1 * t80 * t81 * t49 * t181 * t116 * t200
  t356 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t36 * t65 + t6 * t22 * t121 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t70 * t205 - 0.3e1 / 0.8e1 * t6 * t125 * t351)
  v3rho3_0_ = 0.2e1 * r0 * t356 + 0.6e1 * t210

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
  t24 = t3 ** 2
  t25 = params.beta * t24
  t27 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t28 = 0.1e1 / t27
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = t28 * t29
  t31 = t25 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = params.gamma * params.beta
  t36 = jnp.sqrt(s0)
  t37 = t35 * t36
  t39 = 0.1e1 / t19 / r0
  t40 = t32 * t39
  t43 = jnp.asinh(t36 * t32 * t39)
  t46 = t37 * t40 * t43 + 0.1e1
  t47 = 0.1e1 / t46
  t49 = t34 * t22
  t50 = l0 * t33
  t51 = t20 * r0
  t52 = 0.1e1 / t51
  t55 = 0.1e1 / s0
  t56 = (-t50 * t52 + t49) * t55
  t57 = t32 * t21
  t59 = t56 * t57 + 0.1e1
  t60 = 0.1e1 / t59
  t65 = 0.1e1 + 0.2e1 / 0.9e1 * t31 * t34 * t22 * t47 * t60
  t69 = t17 * t52
  t70 = t18 * r0
  t72 = 0.1e1 / t20 / t70
  t79 = t25 * t30 * s0
  t80 = t33 * t22
  t81 = t46 ** 2
  t82 = 0.1e1 / t81
  t83 = t82 * t60
  t89 = t35 * s0
  t90 = t33 * t72
  t91 = 0.1e1 + t49
  t92 = jnp.sqrt(t91)
  t93 = 0.1e1 / t92
  t97 = -0.4e1 / 0.3e1 * t37 * t32 / t19 / t18 * t43 - 0.4e1 / 0.3e1 * t89 * t90 * t93
  t98 = t83 * t97
  t102 = t59 ** 2
  t103 = 0.1e1 / t102
  t104 = t47 * t103
  t110 = (-0.8e1 / 0.3e1 * t34 * t72 + 0.5e1 / 0.3e1 * t50 * t22) * t55
  t112 = t32 * t51
  t115 = t110 * t57 + 0.8e1 / 0.3e1 * t56 * t112
  t116 = t104 * t115
  t120 = -0.16e2 / 0.27e2 * t31 * t34 * t72 * t47 * t60 - 0.2e1 / 0.9e1 * t79 * t80 * t98 - 0.2e1 / 0.9e1 * t79 * t80 * t116
  t125 = t17 / t20
  t126 = t18 ** 2
  t128 = 0.1e1 / t20 / t126
  t141 = 0.1e1 / t81 / t46
  t142 = t141 * t60
  t143 = t97 ** 2
  t144 = t142 * t143
  t148 = t80 * t82
  t149 = t103 * t97
  t150 = t149 * t115
  t160 = t33 * t128
  t164 = s0 ** 2
  t165 = t35 * t164
  t171 = 0.1e1 / t92 / t91
  t175 = 0.28e2 / 0.9e1 * t37 * t32 / t19 / t70 * t43 + 0.20e2 / 0.3e1 * t89 * t160 * t93 - 0.32e2 / 0.9e1 * t165 * t32 / t19 / t126 / t70 * t171
  t176 = t83 * t175
  t181 = 0.1e1 / t102 / t59
  t182 = t47 * t181
  t183 = t115 ** 2
  t184 = t182 * t183
  t193 = (0.88e2 / 0.9e1 * t34 * t128 - 0.40e2 / 0.9e1 * t50 * t72) * t55
  t197 = t32 * t20
  t200 = t193 * t57 + 0.16e2 / 0.3e1 * t110 * t112 + 0.40e2 / 0.9e1 * t56 * t197
  t201 = t104 * t200
  t205 = 0.176e3 / 0.81e2 * t31 * t34 * t128 * t47 * t60 + 0.32e2 / 0.27e2 * t79 * t90 * t98 + 0.32e2 / 0.27e2 * t79 * t90 * t116 + 0.4e1 / 0.9e1 * t79 * t80 * t144 + 0.4e1 / 0.9e1 * t79 * t148 * t150 - 0.2e1 / 0.9e1 * t79 * t80 * t176 + 0.4e1 / 0.9e1 * t79 * t80 * t184 - 0.2e1 / 0.9e1 * t79 * t80 * t201
  t209 = t17 * t19
  t211 = t181 * t97 * t183
  t227 = t126 * r0
  t229 = 0.1e1 / t20 / t227
  t230 = t33 * t229
  t234 = t126 ** 2
  t241 = t164 * s0
  t245 = t91 ** 2
  t247 = 0.1e1 / t92 / t245
  t251 = -0.280e3 / 0.27e2 * t37 * t32 / t19 / t126 * t43 - 0.952e3 / 0.27e2 * t89 * t230 * t93 + 0.1184e4 / 0.27e2 * t165 * t32 / t19 / t234 * t171 - 0.256e3 / 0.9e1 * t35 * t241 / t234 / t70 * t247
  t252 = t83 * t251
  t261 = (-0.1232e4 / 0.27e2 * t34 * t229 + 0.440e3 / 0.27e2 * t50 * t128) * t55
  t268 = t32 / t19
  t271 = t261 * t57 + 0.8e1 * t193 * t112 + 0.40e2 / 0.3e1 * t110 * t197 + 0.80e2 / 0.27e2 * t56 * t268
  t272 = t104 * t271
  t290 = t90 * t82
  t297 = t81 ** 2
  t298 = 0.1e1 / t297
  t300 = t143 * t97
  t301 = t298 * t60 * t300
  t305 = t80 * t141
  t306 = t103 * t143
  t307 = t306 * t115
  t312 = t60 * t97 * t175
  t316 = t103 * t175
  t317 = t316 * t115
  t321 = t149 * t200
  t325 = t102 ** 2
  t326 = 0.1e1 / t325
  t328 = t183 * t115
  t329 = t47 * t326 * t328
  t333 = t80 * t47
  t335 = t181 * t115 * t200
  t339 = -0.4e1 / 0.3e1 * t79 * t148 * t211 + 0.16e2 / 0.9e1 * t79 * t90 * t176 + 0.16e2 / 0.9e1 * t79 * t90 * t201 - 0.2e1 / 0.9e1 * t79 * t80 * t252 - 0.2e1 / 0.9e1 * t79 * t80 * t272 - 0.2464e4 / 0.243e3 * t31 * t34 * t229 * t47 * t60 - 0.176e3 / 0.27e2 * t79 * t160 * t98 - 0.176e3 / 0.27e2 * t79 * t160 * t116 - 0.32e2 / 0.9e1 * t79 * t90 * t144 - 0.32e2 / 0.9e1 * t79 * t290 * t150 - 0.32e2 / 0.9e1 * t79 * t90 * t184 - 0.4e1 / 0.3e1 * t79 * t80 * t301 - 0.4e1 / 0.3e1 * t79 * t305 * t307 + 0.4e1 / 0.3e1 * t79 * t305 * t312 + 0.2e1 / 0.3e1 * t79 * t148 * t317 + 0.2e1 / 0.3e1 * t79 * t148 * t321 - 0.4e1 / 0.3e1 * t79 * t80 * t329 + 0.4e1 / 0.3e1 * t79 * t333 * t335
  t344 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t65 + t6 * t69 * t120 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t125 * t205 - 0.3e1 / 0.8e1 * t6 * t209 * t339)
  t368 = t90 * t141
  t372 = t80 * t298
  t399 = t25 * t28 * t29 * s0 * t33
  t402 = t97 * t115
  t422 = t126 * t18
  t424 = 0.1e1 / t20 / t422
  t442 = t164 ** 2
  t497 = 0.16e2 / 0.9e1 * t79 * t333 * t181 * t271 * t115 + 0.704e3 / 0.27e2 * t79 * t160 * t82 * t150 + 0.128e3 / 0.9e1 * t79 * t368 * t307 + 0.16e2 / 0.3e1 * t79 * t372 * t103 * t300 * t115 - 0.8e1 * t79 * t372 * t60 * t143 * t175 - 0.8e1 / 0.3e1 * t79 * t305 * t306 * t200 + 0.4e1 / 0.3e1 * t79 * t148 * t316 * t200 - 0.8e1 * t79 * t333 * t326 * t183 * t200 - 0.16e2 / 0.3e1 * t399 * t22 * t141 * t103 * t402 * t175 - 0.16e2 / 0.3e1 * t399 * t22 * t82 * t181 * t402 * t200 + 0.64e2 / 0.27e2 * t79 * t90 * t272 - 0.2e1 / 0.9e1 * t79 * t80 * t83 * (0.3640e4 / 0.81e2 * t37 * t32 / t19 / t227 * t43 + 0.5768e4 / 0.27e2 * t89 * t33 * t424 * t93 - 0.37216e5 / 0.81e2 * t165 * t32 / t19 / t234 / r0 * t171 + 0.17920e5 / 0.27e2 * t35 * t241 / t234 / t126 * t247 - 0.5120e4 / 0.27e2 * t35 * t442 / t20 / t234 / t422 / t92 / t245 / t91 * t33) - 0.2e1 / 0.9e1 * t79 * t80 * t104 * ((0.20944e5 / 0.81e2 * t34 * t424 - 0.6160e4 / 0.81e2 * t50 * t229) * t55 * t57 + 0.32e2 / 0.3e1 * t261 * t112 + 0.80e2 / 0.3e1 * t193 * t197 + 0.320e3 / 0.27e2 * t110 * t268 - 0.80e2 / 0.81e2 * t56 * t40) + 0.9856e4 / 0.243e3 * t79 * t230 * t98 + 0.9856e4 / 0.243e3 * t79 * t230 * t116 + 0.64e2 / 0.27e2 * t79 * t90 * t252 - 0.352e3 / 0.27e2 * t79 * t160 * t176 - 0.352e3 / 0.27e2 * t79 * t160 * t201 + 0.704e3 / 0.27e2 * t79 * t160 * t144
  t510 = t143 ** 2
  t515 = t175 ** 2
  t523 = t183 ** 2
  t528 = t200 ** 2
  t584 = 0.704e3 / 0.27e2 * t79 * t160 * t184 + 0.128e3 / 0.9e1 * t79 * t90 * t301 + 0.128e3 / 0.9e1 * t79 * t90 * t329 + 0.16e2 / 0.3e1 * t79 * t80 / t297 / t46 * t60 * t510 + 0.4e1 / 0.3e1 * t79 * t80 * t142 * t515 + 0.16e2 / 0.3e1 * t79 * t80 * t47 / t325 / t59 * t523 + 0.4e1 / 0.3e1 * t79 * t80 * t182 * t528 + 0.128e3 / 0.9e1 * t79 * t290 * t211 + 0.16e2 / 0.3e1 * t79 * t305 * t181 * t143 * t183 + 0.16e2 / 0.3e1 * t79 * t148 * t326 * t97 * t328 - 0.8e1 / 0.3e1 * t79 * t148 * t181 * t175 * t183 - 0.128e3 / 0.9e1 * t79 * t368 * t312 - 0.64e2 / 0.9e1 * t79 * t290 * t317 - 0.64e2 / 0.9e1 * t79 * t290 * t321 - 0.128e3 / 0.9e1 * t79 * t90 * t47 * t335 + 0.16e2 / 0.9e1 * t79 * t305 * t60 * t251 * t97 + 0.8e1 / 0.9e1 * t79 * t148 * t103 * t251 * t115 + 0.8e1 / 0.9e1 * t79 * t148 * t103 * t271 * t97 + 0.41888e5 / 0.729e3 * t31 * t34 * t424 * t47 * t60
  t590 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t72 * t65 - 0.5e1 / 0.9e1 * t6 * t23 * t120 + t6 * t69 * t205 / 0.2e1 - t6 * t125 * t339 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t209 * (t497 + t584))
  v4rho4_0_ = 0.2e1 * r0 * t590 + 0.8e1 * t344

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
  t37 = 4 ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t35 * t37
  t39 = t33 * t38
  t40 = r0 ** 2
  t41 = r0 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t43 = t42 * t40
  t44 = 0.1e1 / t43
  t45 = s0 * t44
  t46 = params.gamma * params.beta
  t47 = jnp.sqrt(s0)
  t50 = t47 / t41 / r0
  t51 = jnp.arcsinh(t50)
  t54 = t46 * t50 * t51 + 0.1e1
  t55 = 0.1e1 / t54
  t56 = t42 * r0
  t60 = 0.1e1 / s0
  t61 = (t45 - l0 / t56) * t60
  t64 = 0.2e1 * t61 * t43 + 0.1e1
  t65 = 0.1e1 / t64
  t66 = t55 * t65
  t70 = 0.1e1 + 0.2e1 / 0.9e1 * t39 * t45 * t66
  t74 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t75 = t74 * f.p.zeta_threshold
  t77 = f.my_piecewise3(t20, t75, t21 * t19)
  t78 = t30 ** 2
  t79 = 0.1e1 / t78
  t80 = t77 * t79
  t83 = t5 * t80 * t70 / 0.8e1
  t84 = t77 * t30
  t85 = t40 * r0
  t87 = 0.1e1 / t42 / t85
  t88 = s0 * t87
  t92 = t54 ** 2
  t93 = 0.1e1 / t92
  t94 = t93 * t65
  t100 = 0.1e1 + t45
  t101 = jnp.sqrt(t100)
  t102 = 0.1e1 / t101
  t106 = -0.4e1 / 0.3e1 * t46 * t47 / t41 / t40 * t51 - 0.4e1 / 0.3e1 * t46 * t88 * t102
  t107 = t94 * t106
  t111 = t64 ** 2
  t112 = 0.1e1 / t111
  t113 = t55 * t112
  t118 = (-0.8e1 / 0.3e1 * t88 + 0.5e1 / 0.3e1 * l0 * t44) * t60
  t123 = 0.2e1 * t118 * t43 + 0.16e2 / 0.3e1 * t61 * t56
  t124 = t113 * t123
  t128 = -0.16e2 / 0.27e2 * t39 * t88 * t66 - 0.2e1 / 0.9e1 * t39 * t45 * t107 - 0.2e1 / 0.9e1 * t39 * t45 * t124
  t133 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t70 - t83 - 0.3e1 / 0.8e1 * t5 * t84 * t128)
  t135 = r1 <= f.p.dens_threshold
  t136 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t137 = 0.1e1 + t136
  t138 = t137 <= f.p.zeta_threshold
  t139 = t137 ** (0.1e1 / 0.3e1)
  t141 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t144 = f.my_piecewise3(t138, 0, 0.4e1 / 0.3e1 * t139 * t141)
  t145 = t144 * t30
  t146 = r1 ** 2
  t147 = r1 ** (0.1e1 / 0.3e1)
  t148 = t147 ** 2
  t149 = t148 * t146
  t150 = 0.1e1 / t149
  t151 = s2 * t150
  t152 = jnp.sqrt(s2)
  t155 = t152 / t147 / r1
  t156 = jnp.arcsinh(t155)
  t159 = t46 * t155 * t156 + 0.1e1
  t160 = 0.1e1 / t159
  t161 = t148 * r1
  t165 = 0.1e1 / s2
  t166 = (t151 - l1 / t161) * t165
  t169 = 0.2e1 * t166 * t149 + 0.1e1
  t170 = 0.1e1 / t169
  t171 = t160 * t170
  t175 = 0.1e1 + 0.2e1 / 0.9e1 * t39 * t151 * t171
  t180 = f.my_piecewise3(t138, t75, t139 * t137)
  t181 = t180 * t79
  t184 = t5 * t181 * t175 / 0.8e1
  t186 = f.my_piecewise3(t135, 0, -0.3e1 / 0.8e1 * t5 * t145 * t175 - t184)
  t188 = t21 ** 2
  t189 = 0.1e1 / t188
  t190 = t26 ** 2
  t195 = t16 / t22 / t6
  t197 = -0.2e1 * t23 + 0.2e1 * t195
  t198 = f.my_piecewise5(t10, 0, t14, 0, t197)
  t202 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t189 * t190 + 0.4e1 / 0.3e1 * t21 * t198)
  t209 = t5 * t29 * t79 * t70
  t215 = 0.1e1 / t78 / t6
  t219 = t5 * t77 * t215 * t70 / 0.12e2
  t221 = t5 * t80 * t128
  t223 = t40 ** 2
  t226 = s0 / t42 / t223
  t239 = t106 ** 2
  t261 = s0 ** 2
  t279 = t123 ** 2
  t305 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t202 * t30 * t70 - t209 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t128 + t219 - t221 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t84 * (0.176e3 / 0.81e2 * t39 * t226 * t66 + 0.32e2 / 0.27e2 * t39 * t88 * t107 + 0.32e2 / 0.27e2 * t39 * t88 * t124 + 0.4e1 / 0.9e1 * t39 * t45 / t92 / t54 * t65 * t239 + 0.4e1 / 0.9e1 * t33 * t38 * s0 * t44 * t93 * t112 * t106 * t123 - 0.2e1 / 0.9e1 * t39 * t45 * t94 * (0.28e2 / 0.9e1 * t46 * t47 / t41 / t85 * t51 + 0.20e2 / 0.3e1 * t46 * t226 * t102 - 0.16e2 / 0.9e1 * t46 * t261 / t41 / t223 / t85 / t101 / t100) + 0.4e1 / 0.9e1 * t39 * t45 * t55 / t111 / t64 * t279 - 0.2e1 / 0.9e1 * t39 * t45 * t113 * (0.2e1 * (0.88e2 / 0.9e1 * t226 - 0.40e2 / 0.9e1 * l0 * t87) * t60 * t43 + 0.32e2 / 0.3e1 * t118 * t56 + 0.80e2 / 0.9e1 * t61 * t42)))
  t306 = t139 ** 2
  t307 = 0.1e1 / t306
  t308 = t141 ** 2
  t312 = f.my_piecewise5(t14, 0, t10, 0, -t197)
  t316 = f.my_piecewise3(t138, 0, 0.4e1 / 0.9e1 * t307 * t308 + 0.4e1 / 0.3e1 * t139 * t312)
  t323 = t5 * t144 * t79 * t175
  t328 = t5 * t180 * t215 * t175 / 0.12e2
  t330 = f.my_piecewise3(t135, 0, -0.3e1 / 0.8e1 * t5 * t316 * t30 * t175 - t323 / 0.4e1 + t328)
  d11 = 0.2e1 * t133 + 0.2e1 * t186 + t6 * (t305 + t330)
  t333 = -t7 - t24
  t334 = f.my_piecewise5(t10, 0, t14, 0, t333)
  t337 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t334)
  t338 = t337 * t30
  t343 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t338 * t70 - t83)
  t345 = f.my_piecewise5(t14, 0, t10, 0, -t333)
  t348 = f.my_piecewise3(t138, 0, 0.4e1 / 0.3e1 * t139 * t345)
  t349 = t348 * t30
  t353 = t180 * t30
  t354 = t146 * r1
  t356 = 0.1e1 / t148 / t354
  t357 = s2 * t356
  t361 = t159 ** 2
  t362 = 0.1e1 / t361
  t363 = t362 * t170
  t369 = 0.1e1 + t151
  t370 = jnp.sqrt(t369)
  t371 = 0.1e1 / t370
  t375 = -0.4e1 / 0.3e1 * t46 * t152 / t147 / t146 * t156 - 0.4e1 / 0.3e1 * t46 * t357 * t371
  t376 = t363 * t375
  t380 = t169 ** 2
  t381 = 0.1e1 / t380
  t382 = t160 * t381
  t387 = (-0.8e1 / 0.3e1 * t357 + 0.5e1 / 0.3e1 * l1 * t150) * t165
  t392 = 0.2e1 * t387 * t149 + 0.16e2 / 0.3e1 * t166 * t161
  t393 = t382 * t392
  t397 = -0.16e2 / 0.27e2 * t39 * t357 * t171 - 0.2e1 / 0.9e1 * t39 * t151 * t376 - 0.2e1 / 0.9e1 * t39 * t151 * t393
  t402 = f.my_piecewise3(t135, 0, -0.3e1 / 0.8e1 * t5 * t349 * t175 - t184 - 0.3e1 / 0.8e1 * t5 * t353 * t397)
  t406 = 0.2e1 * t195
  t407 = f.my_piecewise5(t10, 0, t14, 0, t406)
  t411 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t189 * t334 * t26 + 0.4e1 / 0.3e1 * t21 * t407)
  t418 = t5 * t337 * t79 * t70
  t426 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t411 * t30 * t70 - t418 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t338 * t128 - t209 / 0.8e1 + t219 - t221 / 0.8e1)
  t430 = f.my_piecewise5(t14, 0, t10, 0, -t406)
  t434 = f.my_piecewise3(t138, 0, 0.4e1 / 0.9e1 * t307 * t345 * t141 + 0.4e1 / 0.3e1 * t139 * t430)
  t441 = t5 * t348 * t79 * t175
  t448 = t5 * t181 * t397
  t451 = f.my_piecewise3(t135, 0, -0.3e1 / 0.8e1 * t5 * t434 * t30 * t175 - t441 / 0.8e1 - t323 / 0.8e1 + t328 - 0.3e1 / 0.8e1 * t5 * t145 * t397 - t448 / 0.8e1)
  d12 = t133 + t186 + t343 + t402 + t6 * (t426 + t451)
  t456 = t334 ** 2
  t460 = 0.2e1 * t23 + 0.2e1 * t195
  t461 = f.my_piecewise5(t10, 0, t14, 0, t460)
  t465 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t189 * t456 + 0.4e1 / 0.3e1 * t21 * t461)
  t472 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t465 * t30 * t70 - t418 / 0.4e1 + t219)
  t473 = t345 ** 2
  t477 = f.my_piecewise5(t14, 0, t10, 0, -t460)
  t481 = f.my_piecewise3(t138, 0, 0.4e1 / 0.9e1 * t307 * t473 + 0.4e1 / 0.3e1 * t139 * t477)
  t491 = t146 ** 2
  t494 = s2 / t148 / t491
  t507 = t375 ** 2
  t529 = s2 ** 2
  t547 = t392 ** 2
  t573 = f.my_piecewise3(t135, 0, -0.3e1 / 0.8e1 * t5 * t481 * t30 * t175 - t441 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t349 * t397 + t328 - t448 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t353 * (0.176e3 / 0.81e2 * t39 * t494 * t171 + 0.32e2 / 0.27e2 * t39 * t357 * t376 + 0.32e2 / 0.27e2 * t39 * t357 * t393 + 0.4e1 / 0.9e1 * t39 * t151 / t361 / t159 * t170 * t507 + 0.4e1 / 0.9e1 * t33 * t38 * s2 * t150 * t362 * t381 * t375 * t392 - 0.2e1 / 0.9e1 * t39 * t151 * t363 * (0.28e2 / 0.9e1 * t46 * t152 / t147 / t354 * t156 + 0.20e2 / 0.3e1 * t46 * t494 * t371 - 0.16e2 / 0.9e1 * t46 * t529 / t147 / t491 / t354 / t370 / t369) + 0.4e1 / 0.9e1 * t39 * t151 * t160 / t380 / t169 * t547 - 0.2e1 / 0.9e1 * t39 * t151 * t382 * (0.2e1 * (0.88e2 / 0.9e1 * t494 - 0.40e2 / 0.9e1 * l1 * t356) * t165 * t149 + 0.32e2 / 0.3e1 * t387 * t161 + 0.80e2 / 0.9e1 * t166 * t148)))
  d22 = 0.2e1 * t343 + 0.2e1 * t402 + t6 * (t472 + t573)
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
  t44 = t2 ** 2
  t45 = params.beta * t44
  t47 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t49 = 4 ** (0.1e1 / 0.3e1)
  t50 = 0.1e1 / t47 * t49
  t51 = t45 * t50
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t55 = t54 * t52
  t56 = 0.1e1 / t55
  t57 = s0 * t56
  t58 = params.gamma * params.beta
  t59 = jnp.sqrt(s0)
  t62 = t59 / t53 / r0
  t63 = jnp.asinh(t62)
  t66 = t58 * t62 * t63 + 0.1e1
  t67 = 0.1e1 / t66
  t68 = t54 * r0
  t72 = 0.1e1 / s0
  t73 = (t57 - l0 / t68) * t72
  t76 = 0.2e1 * t73 * t55 + 0.1e1
  t77 = 0.1e1 / t76
  t78 = t67 * t77
  t82 = 0.1e1 + 0.2e1 / 0.9e1 * t51 * t57 * t78
  t88 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t89 = t42 ** 2
  t90 = 0.1e1 / t89
  t91 = t88 * t90
  t95 = t88 * t42
  t96 = t52 * r0
  t98 = 0.1e1 / t54 / t96
  t99 = s0 * t98
  t103 = t66 ** 2
  t104 = 0.1e1 / t103
  t105 = t104 * t77
  t111 = 0.1e1 + t57
  t112 = jnp.sqrt(t111)
  t113 = 0.1e1 / t112
  t117 = -0.4e1 / 0.3e1 * t58 * t59 / t53 / t52 * t63 - 0.4e1 / 0.3e1 * t58 * t99 * t113
  t118 = t105 * t117
  t122 = t76 ** 2
  t123 = 0.1e1 / t122
  t124 = t67 * t123
  t129 = (-0.8e1 / 0.3e1 * t99 + 0.5e1 / 0.3e1 * l0 * t56) * t72
  t134 = 0.2e1 * t129 * t55 + 0.16e2 / 0.3e1 * t73 * t68
  t135 = t124 * t134
  t139 = -0.16e2 / 0.27e2 * t51 * t99 * t78 - 0.2e1 / 0.9e1 * t51 * t57 * t118 - 0.2e1 / 0.9e1 * t51 * t57 * t135
  t143 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t144 = t143 * f.p.zeta_threshold
  t146 = f.my_piecewise3(t20, t144, t21 * t19)
  t148 = 0.1e1 / t89 / t6
  t149 = t146 * t148
  t153 = t146 * t90
  t157 = t146 * t42
  t158 = t52 ** 2
  t160 = 0.1e1 / t54 / t158
  t161 = s0 * t160
  t172 = 0.1e1 / t103 / t66
  t174 = t117 ** 2
  t175 = t172 * t77 * t174
  t180 = t45 * t50 * s0
  t181 = t56 * t104
  t182 = t123 * t117
  t183 = t182 * t134
  t196 = s0 ** 2
  t202 = 0.1e1 / t112 / t111
  t206 = 0.28e2 / 0.9e1 * t58 * t59 / t53 / t96 * t63 + 0.20e2 / 0.3e1 * t58 * t161 * t113 - 0.16e2 / 0.9e1 * t58 * t196 / t53 / t158 / t96 * t202
  t207 = t105 * t206
  t212 = 0.1e1 / t122 / t76
  t214 = t134 ** 2
  t215 = t67 * t212 * t214
  t223 = (0.88e2 / 0.9e1 * t161 - 0.40e2 / 0.9e1 * l0 * t98) * t72
  t230 = 0.2e1 * t223 * t55 + 0.32e2 / 0.3e1 * t129 * t68 + 0.80e2 / 0.9e1 * t73 * t54
  t231 = t124 * t230
  t235 = 0.176e3 / 0.81e2 * t51 * t161 * t78 + 0.32e2 / 0.27e2 * t51 * t99 * t118 + 0.32e2 / 0.27e2 * t51 * t99 * t135 + 0.4e1 / 0.9e1 * t51 * t57 * t175 + 0.4e1 / 0.9e1 * t180 * t181 * t183 - 0.2e1 / 0.9e1 * t51 * t57 * t207 + 0.4e1 / 0.9e1 * t51 * t57 * t215 - 0.2e1 / 0.9e1 * t51 * t57 * t231
  t240 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t82 - t5 * t91 * t82 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t95 * t139 + t5 * t149 * t82 / 0.12e2 - t5 * t153 * t139 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t157 * t235)
  t242 = r1 <= f.p.dens_threshold
  t243 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t244 = 0.1e1 + t243
  t245 = t244 <= f.p.zeta_threshold
  t246 = t244 ** (0.1e1 / 0.3e1)
  t247 = t246 ** 2
  t248 = 0.1e1 / t247
  t250 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t251 = t250 ** 2
  t255 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t259 = f.my_piecewise3(t245, 0, 0.4e1 / 0.9e1 * t248 * t251 + 0.4e1 / 0.3e1 * t246 * t255)
  t261 = r1 ** 2
  t262 = r1 ** (0.1e1 / 0.3e1)
  t263 = t262 ** 2
  t264 = t263 * t261
  t266 = s2 / t264
  t267 = jnp.sqrt(s2)
  t270 = t267 / t262 / r1
  t271 = jnp.asinh(t270)
  t290 = 0.1e1 + 0.2e1 / 0.9e1 * t51 * t266 / (t58 * t270 * t271 + 0.1e1) / (0.1e1 + 0.2e1 * (t266 - l1 / t263 / r1) / s2 * t264)
  t296 = f.my_piecewise3(t245, 0, 0.4e1 / 0.3e1 * t246 * t250)
  t302 = f.my_piecewise3(t245, t144, t246 * t244)
  t308 = f.my_piecewise3(t242, 0, -0.3e1 / 0.8e1 * t5 * t259 * t42 * t290 - t5 * t296 * t90 * t290 / 0.4e1 + t5 * t302 * t148 * t290 / 0.12e2)
  t318 = t24 ** 2
  t322 = 0.6e1 * t33 - 0.6e1 * t16 / t318
  t323 = f.my_piecewise5(t10, 0, t14, 0, t322)
  t327 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t323)
  t350 = 0.1e1 / t89 / t24
  t366 = t122 ** 2
  t390 = t103 ** 2
  t398 = t56 * t172
  t421 = s0 / t54 / t158 / r0
  t446 = t158 ** 2
  t457 = t111 ** 2
  t487 = -0.4e1 / 0.3e1 * t180 * t181 * t212 * t117 * t214 - 0.4e1 / 0.3e1 * t51 * t57 * t67 / t366 * t214 * t134 + 0.4e1 / 0.3e1 * t180 * t56 * t67 * t212 * t134 * t230 - 0.32e2 / 0.9e1 * t51 * t99 * t175 - 0.32e2 / 0.9e1 * t180 * t98 * t104 * t183 - 0.32e2 / 0.9e1 * t51 * t99 * t215 - 0.4e1 / 0.3e1 * t51 * t57 / t390 * t77 * t174 * t117 - 0.4e1 / 0.3e1 * t180 * t398 * t123 * t174 * t134 + 0.4e1 / 0.3e1 * t180 * t398 * t77 * t117 * t206 + 0.2e1 / 0.3e1 * t180 * t181 * t123 * t206 * t134 + 0.2e1 / 0.3e1 * t180 * t181 * t182 * t230 - 0.2464e4 / 0.243e3 * t51 * t421 * t78 - 0.176e3 / 0.27e2 * t51 * t161 * t118 - 0.176e3 / 0.27e2 * t51 * t161 * t135 + 0.16e2 / 0.9e1 * t51 * t99 * t207 + 0.16e2 / 0.9e1 * t51 * t99 * t231 - 0.2e1 / 0.9e1 * t51 * t57 * t105 * (-0.280e3 / 0.27e2 * t58 * t59 / t53 / t158 * t63 - 0.952e3 / 0.27e2 * t58 * t421 * t113 + 0.592e3 / 0.27e2 * t58 * t196 / t53 / t446 * t202 - 0.64e2 / 0.9e1 * t58 * t196 * s0 / t446 / t96 / t112 / t457) - 0.2e1 / 0.9e1 * t51 * t57 * t124 * (0.2e1 * (-0.1232e4 / 0.27e2 * t421 + 0.440e3 / 0.27e2 * l0 * t160) * t72 * t55 + 0.16e2 * t223 * t68 + 0.80e2 / 0.3e1 * t129 * t54 + 0.160e3 / 0.27e2 * t73 / t53)
  t492 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t327 * t42 * t82 - 0.3e1 / 0.8e1 * t5 * t41 * t90 * t82 - 0.9e1 / 0.8e1 * t5 * t43 * t139 + t5 * t88 * t148 * t82 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t91 * t139 - 0.9e1 / 0.8e1 * t5 * t95 * t235 - 0.5e1 / 0.36e2 * t5 * t146 * t350 * t82 + t5 * t149 * t139 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t153 * t235 - 0.3e1 / 0.8e1 * t5 * t157 * t487)
  t502 = f.my_piecewise5(t14, 0, t10, 0, -t322)
  t506 = f.my_piecewise3(t245, 0, -0.8e1 / 0.27e2 / t247 / t244 * t251 * t250 + 0.4e1 / 0.3e1 * t248 * t250 * t255 + 0.4e1 / 0.3e1 * t246 * t502)
  t524 = f.my_piecewise3(t242, 0, -0.3e1 / 0.8e1 * t5 * t506 * t42 * t290 - 0.3e1 / 0.8e1 * t5 * t259 * t90 * t290 + t5 * t296 * t148 * t290 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t302 * t350 * t290)
  d111 = 0.3e1 * t240 + 0.3e1 * t308 + t6 * (t492 + t524)

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
  t61 = 4 ** (0.1e1 / 0.3e1)
  t62 = 0.1e1 / t59 * t61
  t63 = t57 * t62
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t67 = t66 * t64
  t68 = 0.1e1 / t67
  t69 = s0 * t68
  t70 = params.gamma * params.beta
  t71 = jnp.sqrt(s0)
  t73 = 0.1e1 / t65 / r0
  t74 = t71 * t73
  t75 = jnp.asinh(t74)
  t78 = t70 * t74 * t75 + 0.1e1
  t79 = 0.1e1 / t78
  t80 = t66 * r0
  t84 = 0.1e1 / s0
  t85 = (t69 - l0 / t80) * t84
  t88 = 0.2e1 * t85 * t67 + 0.1e1
  t89 = 0.1e1 / t88
  t90 = t79 * t89
  t94 = 0.1e1 + 0.2e1 / 0.9e1 * t63 * t69 * t90
  t103 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t104 = t54 ** 2
  t105 = 0.1e1 / t104
  t106 = t103 * t105
  t110 = t103 * t54
  t111 = t64 * r0
  t113 = 0.1e1 / t66 / t111
  t114 = s0 * t113
  t118 = t78 ** 2
  t119 = 0.1e1 / t118
  t120 = t119 * t89
  t126 = 0.1e1 + t69
  t127 = jnp.sqrt(t126)
  t128 = 0.1e1 / t127
  t132 = -0.4e1 / 0.3e1 * t70 * t71 / t65 / t64 * t75 - 0.4e1 / 0.3e1 * t70 * t114 * t128
  t133 = t120 * t132
  t137 = t88 ** 2
  t138 = 0.1e1 / t137
  t139 = t79 * t138
  t144 = (-0.8e1 / 0.3e1 * t114 + 0.5e1 / 0.3e1 * l0 * t68) * t84
  t149 = 0.2e1 * t144 * t67 + 0.16e2 / 0.3e1 * t85 * t80
  t150 = t139 * t149
  t154 = -0.16e2 / 0.27e2 * t63 * t114 * t90 - 0.2e1 / 0.9e1 * t63 * t69 * t133 - 0.2e1 / 0.9e1 * t63 * t69 * t150
  t160 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t162 = 0.1e1 / t104 / t6
  t163 = t160 * t162
  t167 = t160 * t105
  t171 = t160 * t54
  t172 = t64 ** 2
  t174 = 0.1e1 / t66 / t172
  t175 = s0 * t174
  t186 = 0.1e1 / t118 / t78
  t187 = t186 * t89
  t188 = t132 ** 2
  t189 = t187 * t188
  t194 = t57 * t62 * s0
  t195 = t68 * t119
  t196 = t138 * t132
  t197 = t196 * t149
  t210 = s0 ** 2
  t216 = 0.1e1 / t127 / t126
  t220 = 0.28e2 / 0.9e1 * t70 * t71 / t65 / t111 * t75 + 0.20e2 / 0.3e1 * t70 * t175 * t128 - 0.16e2 / 0.9e1 * t70 * t210 / t65 / t172 / t111 * t216
  t221 = t120 * t220
  t226 = 0.1e1 / t137 / t88
  t227 = t79 * t226
  t228 = t149 ** 2
  t229 = t227 * t228
  t237 = (0.88e2 / 0.9e1 * t175 - 0.40e2 / 0.9e1 * l0 * t113) * t84
  t244 = 0.2e1 * t237 * t67 + 0.32e2 / 0.3e1 * t144 * t80 + 0.80e2 / 0.9e1 * t85 * t66
  t245 = t139 * t244
  t249 = 0.176e3 / 0.81e2 * t63 * t175 * t90 + 0.32e2 / 0.27e2 * t63 * t114 * t133 + 0.32e2 / 0.27e2 * t63 * t114 * t150 + 0.4e1 / 0.9e1 * t63 * t69 * t189 + 0.4e1 / 0.9e1 * t194 * t195 * t197 - 0.2e1 / 0.9e1 * t63 * t69 * t221 + 0.4e1 / 0.9e1 * t63 * t69 * t229 - 0.2e1 / 0.9e1 * t63 * t69 * t245
  t253 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t254 = t253 * f.p.zeta_threshold
  t256 = f.my_piecewise3(t20, t254, t21 * t19)
  t258 = 0.1e1 / t104 / t25
  t259 = t256 * t258
  t263 = t256 * t162
  t267 = t256 * t105
  t271 = t256 * t54
  t273 = t226 * t132 * t228
  t277 = t137 ** 2
  t278 = 0.1e1 / t277
  t280 = t228 * t149
  t281 = t79 * t278 * t280
  t285 = t68 * t79
  t286 = t226 * t149
  t287 = t286 * t244
  t294 = t113 * t119
  t301 = t118 ** 2
  t302 = 0.1e1 / t301
  t304 = t188 * t132
  t305 = t302 * t89 * t304
  t309 = t68 * t186
  t310 = t138 * t188
  t311 = t310 * t149
  t315 = t89 * t132
  t316 = t315 * t220
  t320 = t138 * t220
  t321 = t320 * t149
  t325 = t196 * t244
  t329 = t172 * r0
  t331 = 0.1e1 / t66 / t329
  t332 = s0 * t331
  t357 = t172 ** 2
  t364 = t210 * s0
  t368 = t126 ** 2
  t370 = 0.1e1 / t127 / t368
  t374 = -0.280e3 / 0.27e2 * t70 * t71 / t65 / t172 * t75 - 0.952e3 / 0.27e2 * t70 * t332 * t128 + 0.592e3 / 0.27e2 * t70 * t210 / t65 / t357 * t216 - 0.64e2 / 0.9e1 * t70 * t364 / t357 / t111 * t370
  t375 = t120 * t374
  t383 = (-0.1232e4 / 0.27e2 * t332 + 0.440e3 / 0.27e2 * l0 * t174) * t84
  t390 = 0.1e1 / t65
  t393 = 0.2e1 * t383 * t67 + 0.16e2 * t237 * t80 + 0.80e2 / 0.3e1 * t144 * t66 + 0.160e3 / 0.27e2 * t85 * t390
  t394 = t139 * t393
  t398 = -0.4e1 / 0.3e1 * t194 * t195 * t273 - 0.4e1 / 0.3e1 * t63 * t69 * t281 + 0.4e1 / 0.3e1 * t194 * t285 * t287 - 0.32e2 / 0.9e1 * t63 * t114 * t189 - 0.32e2 / 0.9e1 * t194 * t294 * t197 - 0.32e2 / 0.9e1 * t63 * t114 * t229 - 0.4e1 / 0.3e1 * t63 * t69 * t305 - 0.4e1 / 0.3e1 * t194 * t309 * t311 + 0.4e1 / 0.3e1 * t194 * t309 * t316 + 0.2e1 / 0.3e1 * t194 * t195 * t321 + 0.2e1 / 0.3e1 * t194 * t195 * t325 - 0.2464e4 / 0.243e3 * t63 * t332 * t90 - 0.176e3 / 0.27e2 * t63 * t175 * t133 - 0.176e3 / 0.27e2 * t63 * t175 * t150 + 0.16e2 / 0.9e1 * t63 * t114 * t221 + 0.16e2 / 0.9e1 * t63 * t114 * t245 - 0.2e1 / 0.9e1 * t63 * t69 * t375 - 0.2e1 / 0.9e1 * t63 * t69 * t394
  t403 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t94 - 0.3e1 / 0.8e1 * t5 * t106 * t94 - 0.9e1 / 0.8e1 * t5 * t110 * t154 + t5 * t163 * t94 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t167 * t154 - 0.9e1 / 0.8e1 * t5 * t171 * t249 - 0.5e1 / 0.36e2 * t5 * t259 * t94 + t5 * t263 * t154 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t267 * t249 - 0.3e1 / 0.8e1 * t5 * t271 * t398)
  t405 = r1 <= f.p.dens_threshold
  t406 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t407 = 0.1e1 + t406
  t408 = t407 <= f.p.zeta_threshold
  t409 = t407 ** (0.1e1 / 0.3e1)
  t410 = t409 ** 2
  t412 = 0.1e1 / t410 / t407
  t414 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t415 = t414 ** 2
  t419 = 0.1e1 / t410
  t420 = t419 * t414
  t422 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t426 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t430 = f.my_piecewise3(t408, 0, -0.8e1 / 0.27e2 * t412 * t415 * t414 + 0.4e1 / 0.3e1 * t420 * t422 + 0.4e1 / 0.3e1 * t409 * t426)
  t432 = r1 ** 2
  t433 = r1 ** (0.1e1 / 0.3e1)
  t434 = t433 ** 2
  t435 = t434 * t432
  t437 = s2 / t435
  t438 = jnp.sqrt(s2)
  t441 = t438 / t433 / r1
  t442 = jnp.asinh(t441)
  t461 = 0.1e1 + 0.2e1 / 0.9e1 * t63 * t437 / (t70 * t441 * t442 + 0.1e1) / (0.1e1 + 0.2e1 * (t437 - l1 / t434 / r1) / s2 * t435)
  t470 = f.my_piecewise3(t408, 0, 0.4e1 / 0.9e1 * t419 * t415 + 0.4e1 / 0.3e1 * t409 * t422)
  t477 = f.my_piecewise3(t408, 0, 0.4e1 / 0.3e1 * t409 * t414)
  t483 = f.my_piecewise3(t408, t254, t409 * t407)
  t489 = f.my_piecewise3(t405, 0, -0.3e1 / 0.8e1 * t5 * t430 * t54 * t461 - 0.3e1 / 0.8e1 * t5 * t470 * t105 * t461 + t5 * t477 * t162 * t461 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t483 * t258 * t461)
  t491 = t19 ** 2
  t494 = t30 ** 2
  t500 = t41 ** 2
  t509 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t510 = f.my_piecewise5(t10, 0, t14, 0, t509)
  t514 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t491 * t494 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t500 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t510)
  t571 = t68 * t302
  t599 = t113 * t186
  t625 = 0.128e3 / 0.9e1 * t194 * t294 * t273 + 0.16e2 / 0.3e1 * t194 * t309 * t226 * t188 * t228 + 0.16e2 / 0.3e1 * t194 * t195 * t278 * t132 * t280 + 0.8e1 / 0.9e1 * t194 * t195 * t138 * t374 * t149 + 0.4e1 / 0.3e1 * t194 * t195 * t320 * t244 + 0.8e1 / 0.9e1 * t194 * t195 * t196 * t393 + 0.16e2 / 0.3e1 * t194 * t571 * t138 * t304 * t149 - 0.8e1 * t194 * t571 * t89 * t188 * t220 - 0.8e1 / 0.3e1 * t194 * t309 * t310 * t244 + 0.16e2 / 0.9e1 * t194 * t309 * t315 * t374 - 0.8e1 * t194 * t285 * t278 * t228 * t244 + 0.16e2 / 0.9e1 * t194 * t285 * t286 * t393 + 0.128e3 / 0.9e1 * t194 * t599 * t311 - 0.128e3 / 0.9e1 * t194 * t599 * t316 - 0.64e2 / 0.9e1 * t194 * t294 * t321 - 0.64e2 / 0.9e1 * t194 * t294 * t325 - 0.8e1 / 0.3e1 * t194 * t195 * t226 * t220 * t228 - 0.128e3 / 0.9e1 * t194 * t113 * t79 * t287 + 0.704e3 / 0.27e2 * t194 * t174 * t119 * t197
  t626 = t172 * t64
  t629 = s0 / t66 / t626
  t670 = t210 ** 2
  t712 = t188 ** 2
  t717 = t220 ** 2
  t728 = t228 ** 2
  t733 = t244 ** 2
  t748 = t132 * t149
  t758 = 0.41888e5 / 0.729e3 * t63 * t629 * t90 + 0.9856e4 / 0.243e3 * t63 * t332 * t150 - 0.352e3 / 0.27e2 * t63 * t175 * t221 - 0.352e3 / 0.27e2 * t63 * t175 * t245 + 0.64e2 / 0.27e2 * t63 * t114 * t375 + 0.64e2 / 0.27e2 * t63 * t114 * t394 - 0.2e1 / 0.9e1 * t63 * t69 * t120 * (0.3640e4 / 0.81e2 * t70 * t71 / t65 / t329 * t75 + 0.5768e4 / 0.27e2 * t70 * t629 * t128 - 0.18608e5 / 0.81e2 * t70 * t210 / t65 / t357 / r0 * t216 + 0.4480e4 / 0.27e2 * t70 * t364 / t357 / t172 * t370 - 0.1280e4 / 0.27e2 * t70 * t670 / t66 / t357 / t626 / t127 / t368 / t126) - 0.2e1 / 0.9e1 * t63 * t69 * t139 * (0.2e1 * (0.20944e5 / 0.81e2 * t629 - 0.6160e4 / 0.81e2 * l0 * t331) * t84 * t67 + 0.64e2 / 0.3e1 * t383 * t80 + 0.160e3 / 0.3e1 * t237 * t66 + 0.640e3 / 0.27e2 * t144 * t390 - 0.160e3 / 0.81e2 * t85 * t73) + 0.704e3 / 0.27e2 * t63 * t175 * t229 + 0.16e2 / 0.3e1 * t63 * t69 / t301 / t78 * t89 * t712 + 0.4e1 / 0.3e1 * t63 * t69 * t187 * t717 + 0.128e3 / 0.9e1 * t63 * t114 * t281 + 0.16e2 / 0.3e1 * t63 * t69 * t79 / t277 / t88 * t728 + 0.4e1 / 0.3e1 * t63 * t69 * t227 * t733 + 0.704e3 / 0.27e2 * t63 * t175 * t189 + 0.128e3 / 0.9e1 * t63 * t114 * t305 + 0.9856e4 / 0.243e3 * t63 * t332 * t133 - 0.16e2 / 0.3e1 * t194 * t309 * t138 * t748 * t220 - 0.16e2 / 0.3e1 * t194 * t195 * t226 * t748 * t244
  t776 = 0.1e1 / t104 / t36
  t781 = -0.3e1 / 0.8e1 * t5 * t514 * t54 * t94 - 0.3e1 / 0.2e1 * t5 * t55 * t154 - 0.3e1 / 0.2e1 * t5 * t106 * t154 - 0.9e1 / 0.4e1 * t5 * t110 * t249 + t5 * t163 * t154 - 0.3e1 / 0.2e1 * t5 * t167 * t249 - 0.3e1 / 0.2e1 * t5 * t171 * t398 - 0.5e1 / 0.9e1 * t5 * t259 * t154 + t5 * t263 * t249 / 0.2e1 - t5 * t267 * t398 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t271 * (t625 + t758) - t5 * t53 * t105 * t94 / 0.2e1 + t5 * t103 * t162 * t94 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t160 * t258 * t94 + 0.10e2 / 0.27e2 * t5 * t256 * t776 * t94
  t782 = f.my_piecewise3(t1, 0, t781)
  t783 = t407 ** 2
  t786 = t415 ** 2
  t792 = t422 ** 2
  t798 = f.my_piecewise5(t14, 0, t10, 0, -t509)
  t802 = f.my_piecewise3(t408, 0, 0.40e2 / 0.81e2 / t410 / t783 * t786 - 0.16e2 / 0.9e1 * t412 * t415 * t422 + 0.4e1 / 0.3e1 * t419 * t792 + 0.16e2 / 0.9e1 * t420 * t426 + 0.4e1 / 0.3e1 * t409 * t798)
  t824 = f.my_piecewise3(t405, 0, -0.3e1 / 0.8e1 * t5 * t802 * t54 * t461 - t5 * t430 * t105 * t461 / 0.2e1 + t5 * t470 * t162 * t461 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t477 * t258 * t461 + 0.10e2 / 0.27e2 * t5 * t483 * t776 * t461)
  d1111 = 0.4e1 * t403 + 0.4e1 * t489 + t6 * (t782 + t824)

  res = {'v4rho4': d1111}
  return res
