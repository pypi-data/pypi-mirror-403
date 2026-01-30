"""Generated from gga_x_hcth_a.mpl."""

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
  
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t17 = (r0 - r1) * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = t21 * f.p.zeta_threshold
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t19 <= f.p.zeta_threshold, t22, t23 * t19)
  t26 = t6 ** (0.1e1 / 0.3e1)
  t28 = t2 ** 2
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t31 * t33
  t35 = params.c1 * t28 * t34
  t37 = r0 ** 2
  t38 = r0 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t41 = 0.1e1 / t39 / t37
  t42 = params.gamma * params.beta
  t43 = jnp.sqrt(s0)
  t46 = t43 / t38 / r0
  t47 = jnp.arcsinh(t46)
  t50 = t42 * t46 * t47 + 0.1e1
  t51 = 0.1e1 / t50
  t56 = params.c2 * t28
  t61 = t37 ** 2
  t64 = t50 ** 2
  t77 = f.my_piecewise3(r0 <= f.p.dens_threshold, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * (params.c0 - 0.2e1 / 0.9e1 * t35 * params.beta * s0 * t41 * t51 - 0.2e1 / 0.9e1 * t56 * t34 * (s0 * t41 * t51 - params.beta * t43 * s0 / t61 / t64 * params.gamma * t47)))
  t79 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t80 = 0.1e1 + t79
  t82 = t80 ** (0.1e1 / 0.3e1)
  t84 = f.my_piecewise3(t80 <= f.p.zeta_threshold, t22, t82 * t80)
  t87 = r1 ** 2
  t88 = r1 ** (0.1e1 / 0.3e1)
  t89 = t88 ** 2
  t91 = 0.1e1 / t89 / t87
  t92 = jnp.sqrt(s2)
  t95 = t92 / t88 / r1
  t96 = jnp.arcsinh(t95)
  t99 = t42 * t95 * t96 + 0.1e1
  t100 = 0.1e1 / t99
  t109 = t87 ** 2
  t112 = t99 ** 2
  t125 = f.my_piecewise3(r1 <= f.p.dens_threshold, 0, -0.3e1 / 0.8e1 * t5 * t84 * t26 * (params.c0 - 0.2e1 / 0.9e1 * t35 * params.beta * s2 * t91 * t100 - 0.2e1 / 0.9e1 * t56 * t34 * (s2 * t91 * t100 - params.beta * t92 * s2 / t109 / t112 * params.gamma * t96)))
  res = t77 + t125
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t20 = t3 ** 2
  t23 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t25 = 4 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t23 * t25
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = r0 ** 2
  t32 = t18 ** 2
  t34 = 0.1e1 / t32 / t31
  t37 = jnp.sqrt(s0)
  t40 = 0.1e1 / t18 / r0
  t44 = jnp.arcsinh(t37 * t29 * t40)
  t47 = params.gamma * params.beta * t37 * t29 * t40 * t44 + 0.1e1
  t48 = 0.1e1 / t47
  t59 = t31 ** 2
  t62 = t47 ** 2
  t76 = f.my_piecewise3(r0 / 0.2e1 <= f.p.dens_threshold, 0, -0.3e1 / 0.8e1 * t3 / t4 * t17 * t18 * (params.c0 - 0.2e1 / 0.9e1 * params.c1 * t20 * t26 * params.beta * s0 * t30 * t34 * t48 - 0.2e1 / 0.9e1 * params.c2 * t20 * t26 * (s0 * t30 * t34 * t48 - 0.2e1 * params.beta * t37 * s0 / t59 / t62 * params.gamma * t44)))
  res = 0.2e1 * t76
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
  params_c0_raw = params.c0
  if isinstance(params_c0_raw, (str, bytes, dict)):
    params_c0 = params_c0_raw
  else:
    try:
      params_c0_seq = list(params_c0_raw)
    except TypeError:
      params_c0 = params_c0_raw
    else:
      params_c0_seq = np.asarray(params_c0_seq, dtype=np.float64)
      params_c0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c0_seq))
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
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

  hcth_b88x = lambda beta, x: beta * x ** 2 / (1 + params_gamma * beta * x * jnp.arcsinh(x))

  hcth_a_f = lambda x: params_c0 - params_c1 / X_FACTOR_C * hcth_b88x(params_beta, x) - params_c2 / X_FACTOR_C * (lambda _jac: jnp.diag(_jac) if _jac.ndim == 2 else _jac)(jax.jacfwd(lambda beta: hcth_b88x(beta, x))(params_beta))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, hcth_a_f, rs, z, xs0, xs1)

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
  t28 = t2 ** 2
  t29 = params.c1 * t28
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = t32 * t33
  t35 = t29 * t34
  t36 = params.beta * s0
  t37 = r0 ** 2
  t38 = r0 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t41 = 0.1e1 / t39 / t37
  t42 = params.gamma * params.beta
  t43 = jnp.sqrt(s0)
  t45 = 0.1e1 / t38 / r0
  t46 = t43 * t45
  t47 = jnp.arcsinh(t46)
  t50 = t42 * t46 * t47 + 0.1e1
  t51 = 0.1e1 / t50
  t52 = t41 * t51
  t56 = params.c2 * t28
  t57 = s0 * t41
  t60 = params.beta * t43 * s0
  t61 = t37 ** 2
  t62 = 0.1e1 / t61
  t63 = t60 * t62
  t64 = t50 ** 2
  t65 = 0.1e1 / t64
  t66 = t65 * params.gamma
  t67 = t66 * t47
  t73 = params.c0 - 0.2e1 / 0.9e1 * t35 * t36 * t52 - 0.2e1 / 0.9e1 * t56 * t34 * (t57 * t51 - t63 * t67)
  t77 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t73)
  t78 = r1 <= f.p.dens_threshold
  t79 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t80 = 0.1e1 + t79
  t81 = t80 <= f.p.zeta_threshold
  t82 = t80 ** (0.1e1 / 0.3e1)
  t84 = f.my_piecewise3(t81, t22, t82 * t80)
  t85 = t84 * t26
  t86 = params.beta * s2
  t87 = r1 ** 2
  t88 = r1 ** (0.1e1 / 0.3e1)
  t89 = t88 ** 2
  t91 = 0.1e1 / t89 / t87
  t92 = jnp.sqrt(s2)
  t94 = 0.1e1 / t88 / r1
  t95 = t92 * t94
  t96 = jnp.arcsinh(t95)
  t99 = t42 * t95 * t96 + 0.1e1
  t100 = 0.1e1 / t99
  t101 = t91 * t100
  t105 = s2 * t91
  t108 = params.beta * t92 * s2
  t109 = t87 ** 2
  t110 = 0.1e1 / t109
  t111 = t108 * t110
  t112 = t99 ** 2
  t113 = 0.1e1 / t112
  t114 = t113 * params.gamma
  t115 = t114 * t96
  t121 = params.c0 - 0.2e1 / 0.9e1 * t35 * t86 * t101 - 0.2e1 / 0.9e1 * t56 * t34 * (t105 * t100 - t111 * t115)
  t125 = f.my_piecewise3(t78, 0, -0.3e1 / 0.8e1 * t5 * t85 * t121)
  t126 = t6 ** 2
  t128 = t16 / t126
  t129 = t7 - t128
  t130 = f.my_piecewise5(t10, 0, t14, 0, t129)
  t133 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t130)
  t138 = t26 ** 2
  t139 = 0.1e1 / t138
  t143 = t5 * t25 * t139 * t73 / 0.8e1
  t146 = 0.1e1 / t39 / t37 / r0
  t151 = t41 * t65
  t157 = s0 * t146
  t159 = jnp.sqrt(0.1e1 + t57)
  t160 = 0.1e1 / t159
  t164 = -0.4e1 / 0.3e1 * t42 * t43 / t38 / t37 * t47 - 0.4e1 / 0.3e1 * t42 * t157 * t160
  t173 = t61 * r0
  t180 = 0.1e1 / t64 / t50 * params.gamma
  t185 = s0 ** 2
  t191 = t66 * t160
  t203 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t133 * t26 * t73 - t143 - 0.3e1 / 0.8e1 * t5 * t27 * (0.16e2 / 0.27e2 * t35 * t36 * t146 * t51 + 0.2e1 / 0.9e1 * t35 * t36 * t151 * t164 - 0.2e1 / 0.9e1 * t56 * t34 * (-0.8e1 / 0.3e1 * t157 * t51 - t57 * t65 * t164 + 0.4e1 * t60 / t173 * t67 + 0.2e1 * t63 * t180 * t47 * t164 + 0.4e1 / 0.3e1 * params.beta * t185 / t38 / t61 / t37 * t191)))
  t205 = f.my_piecewise5(t14, 0, t10, 0, -t129)
  t208 = f.my_piecewise3(t81, 0, 0.4e1 / 0.3e1 * t82 * t205)
  t216 = t5 * t84 * t139 * t121 / 0.8e1
  t218 = f.my_piecewise3(t78, 0, -0.3e1 / 0.8e1 * t5 * t208 * t26 * t121 - t216)
  vrho_0_ = t77 + t125 + t6 * (t203 + t218)
  t221 = -t7 - t128
  t222 = f.my_piecewise5(t10, 0, t14, 0, t221)
  t225 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t222)
  t231 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t225 * t26 * t73 - t143)
  t233 = f.my_piecewise5(t14, 0, t10, 0, -t221)
  t236 = f.my_piecewise3(t81, 0, 0.4e1 / 0.3e1 * t82 * t233)
  t243 = 0.1e1 / t89 / t87 / r1
  t248 = t91 * t113
  t254 = s2 * t243
  t256 = jnp.sqrt(0.1e1 + t105)
  t257 = 0.1e1 / t256
  t261 = -0.4e1 / 0.3e1 * t42 * t92 / t88 / t87 * t96 - 0.4e1 / 0.3e1 * t42 * t254 * t257
  t270 = t109 * r1
  t277 = 0.1e1 / t112 / t99 * params.gamma
  t282 = s2 ** 2
  t288 = t114 * t257
  t300 = f.my_piecewise3(t78, 0, -0.3e1 / 0.8e1 * t5 * t236 * t26 * t121 - t216 - 0.3e1 / 0.8e1 * t5 * t85 * (0.16e2 / 0.27e2 * t35 * t86 * t243 * t100 + 0.2e1 / 0.9e1 * t35 * t86 * t248 * t261 - 0.2e1 / 0.9e1 * t56 * t34 * (-0.8e1 / 0.3e1 * t254 * t100 - t105 * t113 * t261 + 0.4e1 * t108 / t270 * t115 + 0.2e1 * t111 * t277 * t96 * t261 + 0.4e1 / 0.3e1 * params.beta * t282 / t88 / t109 / t87 * t288)))
  vrho_1_ = t77 + t125 + t6 * (t231 + t300)
  t303 = t29 * t32
  t304 = t33 * params.beta
  t314 = t42 / t43 * t45 * t47 / 0.2e1 + t42 * t41 * t160 / 0.2e1
  t341 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-0.2e1 / 0.9e1 * t303 * t304 * t52 + 0.2e1 / 0.9e1 * t35 * t36 * t151 * t314 - 0.2e1 / 0.9e1 * t56 * t34 * (t52 - t57 * t65 * t314 - 0.3e1 / 0.2e1 * params.beta * t43 * t62 * t67 + 0.2e1 * t63 * t180 * t47 * t314 - t36 / t38 / t173 * t191 / 0.2e1)))
  vsigma_0_ = t6 * t341
  vsigma_1_ = 0.0e0
  t351 = t42 / t92 * t94 * t96 / 0.2e1 + t42 * t91 * t257 / 0.2e1
  t378 = f.my_piecewise3(t78, 0, -0.3e1 / 0.8e1 * t5 * t85 * (-0.2e1 / 0.9e1 * t303 * t304 * t101 + 0.2e1 / 0.9e1 * t35 * t86 * t248 * t351 - 0.2e1 / 0.9e1 * t56 * t34 * (t101 - t105 * t113 * t351 - 0.3e1 / 0.2e1 * params.beta * t92 * t110 * t115 + 0.2e1 * t111 * t277 * t96 * t351 - t86 / t88 / t270 * t288 / 0.2e1)))
  vsigma_2_ = t6 * t378
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
  params_c0_raw = params.c0
  if isinstance(params_c0_raw, (str, bytes, dict)):
    params_c0 = params_c0_raw
  else:
    try:
      params_c0_seq = list(params_c0_raw)
    except TypeError:
      params_c0 = params_c0_raw
    else:
      params_c0_seq = np.asarray(params_c0_seq, dtype=np.float64)
      params_c0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c0_seq))
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
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

  hcth_b88x = lambda beta, x: beta * x ** 2 / (1 + params_gamma * beta * x * jnp.arcsinh(x))

  hcth_a_f = lambda x: params_c0 - params_c1 / X_FACTOR_C * hcth_b88x(params_beta, x) - params_c2 / X_FACTOR_C * (lambda _jac: jnp.diag(_jac) if _jac.ndim == 2 else _jac)(jax.jacfwd(lambda beta: hcth_b88x(beta, x))(params_beta))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, hcth_a_f, rs, z, xs0, xs1)

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
  t20 = t3 ** 2
  t21 = params.c1 * t20
  t23 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t25 = 4 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t23 * t25
  t27 = t21 * t26
  t28 = params.beta * s0
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = r0 ** 2
  t32 = t18 ** 2
  t34 = 0.1e1 / t32 / t31
  t35 = t30 * t34
  t36 = params.gamma * params.beta
  t37 = jnp.sqrt(s0)
  t38 = t36 * t37
  t40 = 0.1e1 / t18 / r0
  t44 = jnp.arcsinh(t37 * t29 * t40)
  t45 = t29 * t40 * t44
  t47 = t38 * t45 + 0.1e1
  t48 = 0.1e1 / t47
  t49 = t35 * t48
  t53 = params.c2 * t20
  t54 = s0 * t30
  t55 = t34 * t48
  t58 = params.beta * t37 * s0
  t59 = t31 ** 2
  t60 = 0.1e1 / t59
  t61 = t58 * t60
  t62 = t47 ** 2
  t63 = 0.1e1 / t62
  t64 = t63 * params.gamma
  t65 = t64 * t44
  t72 = params.c0 - 0.2e1 / 0.9e1 * t27 * t28 * t49 - 0.2e1 / 0.9e1 * t53 * t26 * (t54 * t55 - 0.2e1 * t61 * t65)
  t76 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t72)
  t84 = 0.1e1 / t32 / t31 / r0
  t85 = t30 * t84
  t91 = t21 * t26 * params.beta
  t92 = t34 * t63
  t101 = jnp.sqrt(t54 * t34 + 0.1e1)
  t102 = 0.1e1 / t101
  t106 = -0.4e1 / 0.3e1 * t38 * t29 / t18 / t31 * t44 - 0.4e1 / 0.3e1 * t36 * s0 * t85 * t102
  t108 = t54 * t92 * t106
  t114 = t59 * r0
  t121 = 0.1e1 / t62 / t47 * params.gamma
  t126 = s0 ** 2
  t133 = t64 * t29 * t102
  t145 = f.my_piecewise3(t2, 0, -t6 * t17 / t32 * t72 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (0.16e2 / 0.27e2 * t27 * t28 * t85 * t48 + 0.2e1 / 0.9e1 * t91 * t108 - 0.2e1 / 0.9e1 * t53 * t26 * (-0.8e1 / 0.3e1 * t54 * t84 * t48 - t108 + 0.8e1 * t58 / t114 * t65 + 0.4e1 * t61 * t121 * t44 * t106 + 0.8e1 / 0.3e1 * params.beta * t126 / t18 / t59 / t31 * t133)))
  vrho_0_ = 0.2e1 * r0 * t145 + 0.2e1 * t76
  t157 = t36 / t37 * t45 / 0.2e1 + t36 * t35 * t102 / 0.2e1
  t159 = t54 * t92 * t157
  t181 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-0.2e1 / 0.9e1 * t27 * params.beta * t30 * t55 + 0.2e1 / 0.9e1 * t91 * t159 - 0.2e1 / 0.9e1 * t53 * t26 * (t49 - t159 - 0.3e1 * params.beta * t37 * t60 * t65 + 0.4e1 * t61 * t121 * t44 * t157 - t28 / t18 / t114 * t133)))
  vsigma_0_ = 0.2e1 * r0 * t181
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
  t22 = t3 ** 2
  t23 = params.c1 * t22
  t25 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t27 = 4 ** (0.1e1 / 0.3e1)
  t28 = 0.1e1 / t25 * t27
  t29 = t23 * t28
  t30 = params.beta * s0
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t36 = t32 * t35
  t37 = params.gamma * params.beta
  t38 = jnp.sqrt(s0)
  t39 = t37 * t38
  t41 = 0.1e1 / t18 / r0
  t45 = jnp.arcsinh(t38 * t31 * t41)
  t46 = t31 * t41 * t45
  t48 = t39 * t46 + 0.1e1
  t49 = 0.1e1 / t48
  t50 = t36 * t49
  t54 = params.c2 * t22
  t55 = s0 * t32
  t56 = t35 * t49
  t58 = t38 * s0
  t59 = params.beta * t58
  t60 = t33 ** 2
  t61 = 0.1e1 / t60
  t62 = t59 * t61
  t63 = t48 ** 2
  t64 = 0.1e1 / t63
  t65 = t64 * params.gamma
  t66 = t65 * t45
  t73 = params.c0 - 0.2e1 / 0.9e1 * t29 * t30 * t50 - 0.2e1 / 0.9e1 * t54 * t28 * (t55 * t56 - 0.2e1 * t62 * t66)
  t77 = t17 * t18
  t78 = t33 * r0
  t80 = 0.1e1 / t19 / t78
  t81 = t32 * t80
  t82 = t81 * t49
  t87 = t23 * t28 * params.beta
  t88 = t35 * t64
  t92 = t31 / t18 / t33 * t45
  t94 = t37 * s0
  t95 = t55 * t35
  t96 = 0.1e1 + t95
  t97 = jnp.sqrt(t96)
  t98 = 0.1e1 / t97
  t99 = t81 * t98
  t102 = -0.4e1 / 0.3e1 * t39 * t92 - 0.4e1 / 0.3e1 * t94 * t99
  t103 = t88 * t102
  t104 = t55 * t103
  t107 = t80 * t49
  t110 = t60 * r0
  t111 = 0.1e1 / t110
  t112 = t59 * t111
  t116 = 0.1e1 / t63 / t48
  t117 = t116 * params.gamma
  t119 = t117 * t45 * t102
  t122 = s0 ** 2
  t123 = params.beta * t122
  t124 = t60 * t33
  t126 = 0.1e1 / t18 / t124
  t129 = t65 * t31 * t98
  t136 = 0.16e2 / 0.27e2 * t29 * t30 * t82 + 0.2e1 / 0.9e1 * t87 * t104 - 0.2e1 / 0.9e1 * t54 * t28 * (-0.8e1 / 0.3e1 * t55 * t107 - t104 + 0.8e1 * t112 * t66 + 0.4e1 * t62 * t119 + 0.8e1 / 0.3e1 * t123 * t126 * t129)
  t141 = f.my_piecewise3(t2, 0, -t6 * t21 * t73 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t77 * t136)
  t153 = 0.1e1 / t19 / t60
  t154 = t32 * t153
  t159 = t80 * t64
  t161 = t55 * t159 * t102
  t164 = t35 * t116
  t165 = t102 ** 2
  t167 = t55 * t164 * t165
  t182 = 0.1e1 / t18 / t60 / t78
  t185 = 0.1e1 / t97 / t96
  t189 = 0.28e2 / 0.9e1 * t39 * t31 / t18 / t78 * t45 + 0.20e2 / 0.3e1 * t94 * t154 * t98 - 0.32e2 / 0.9e1 * t37 * t122 * t31 * t182 * t185
  t191 = t55 * t88 * t189
  t208 = t63 ** 2
  t209 = 0.1e1 / t208
  t210 = t209 * params.gamma
  t216 = t123 * t126 * t116
  t217 = params.gamma * t31
  t219 = t217 * t98 * t102
  t228 = t60 ** 2
  t232 = t65 * t185
  t235 = 0.88e2 / 0.9e1 * t55 * t153 * t49 + 0.16e2 / 0.3e1 * t161 + 0.2e1 * t167 - t191 - 0.40e2 * t59 / t124 * t66 - 0.32e2 * t112 * t119 - 0.248e3 / 0.9e1 * t123 * t182 * t129 - 0.12e2 * t62 * t210 * t45 * t165 - 0.32e2 / 0.3e1 * t216 * t219 + 0.4e1 * t62 * t117 * t45 * t189 + 0.64e2 / 0.9e1 * params.beta * t122 * s0 / t228 / t33 * t232
  t244 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t73 / 0.12e2 - t6 * t21 * t136 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t77 * (-0.176e3 / 0.81e2 * t29 * t30 * t154 * t49 - 0.32e2 / 0.27e2 * t87 * t161 - 0.4e1 / 0.9e1 * t87 * t167 + 0.2e1 / 0.9e1 * t87 * t191 - 0.2e1 / 0.9e1 * t54 * t28 * t235))
  v2rho2_0_ = 0.2e1 * r0 * t244 + 0.4e1 * t141
  t247 = params.beta * t32
  t250 = 0.1e1 / t38
  t251 = t37 * t250
  t253 = t36 * t98
  t256 = t251 * t46 / 0.2e1 + t37 * t253 / 0.2e1
  t257 = t88 * t256
  t258 = t55 * t257
  t260 = params.beta * t38
  t261 = t260 * t61
  t265 = t117 * t45 * t256
  t269 = 0.1e1 / t18 / t110
  t276 = -0.2e1 / 0.9e1 * t29 * t247 * t56 + 0.2e1 / 0.9e1 * t87 * t258 - 0.2e1 / 0.9e1 * t54 * t28 * (-t30 * t269 * t129 - 0.3e1 * t261 * t66 + 0.4e1 * t62 * t265 - t258 + t50)
  t280 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t77 * t276)
  t291 = t55 * t159 * t256
  t296 = t95 * t116 * t256 * t102
  t308 = -0.2e1 / 0.3e1 * t251 * t92 - 0.2e1 * t37 * t99 + 0.4e1 / 0.3e1 * t37 * t31 * t126 * t185 * s0
  t310 = t55 * t88 * t308
  t336 = t217 * t98 * t256
  t344 = t30 * t269 * t116
  t352 = -0.8e1 / 0.3e1 * t82 - t36 * t64 * t102 + 0.8e1 / 0.3e1 * t291 + 0.2e1 * t296 - t310 + 0.12e2 * t260 * t111 * t66 + 0.6e1 * t261 * t119 + 0.28e2 / 0.3e1 * t30 * t126 * t129 - 0.16e2 * t112 * t265 - 0.12e2 * t59 * t61 * t209 * params.gamma * t45 * t256 * t102 - 0.16e2 / 0.3e1 * t216 * t336 + 0.4e1 * t62 * t117 * t45 * t308 + 0.2e1 * t344 * t219 - 0.8e1 / 0.3e1 * t123 / t228 / r0 * t232
  t361 = f.my_piecewise3(t2, 0, -t6 * t21 * t276 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t77 * (0.16e2 / 0.27e2 * t29 * t247 * t107 + 0.2e1 / 0.9e1 * t29 * t247 * t103 - 0.16e2 / 0.27e2 * t87 * t291 - 0.4e1 / 0.9e1 * t87 * t296 + 0.2e1 / 0.9e1 * t87 * t310 - 0.2e1 / 0.9e1 * t54 * t28 * t352))
  v2rhosigma_0_ = 0.2e1 * r0 * t361 + 0.2e1 * t280
  t367 = t256 ** 2
  t369 = t55 * t164 * t367
  t384 = -t37 / t58 * t46 / 0.4e1 + t37 / s0 * t253 / 0.4e1 - t37 * t31 * t269 * t185 / 0.2e1
  t386 = t55 * t88 * t384
  t425 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t77 * (0.4e1 / 0.9e1 * t29 * t247 * t257 - 0.4e1 / 0.9e1 * t87 * t369 + 0.2e1 / 0.9e1 * t87 * t386 - 0.2e1 / 0.9e1 * t54 * t28 * (-0.2e1 * t36 * t64 * t256 + 0.2e1 * t369 - t386 - 0.3e1 / 0.2e1 * params.beta * t250 * t61 * t66 + 0.12e2 * t261 * t265 - 0.5e1 / 0.2e1 * params.beta * t269 * t64 * t217 * t98 - 0.12e2 * t62 * t210 * t45 * t367 + 0.4e1 * t344 * t336 + 0.4e1 * t62 * t117 * t45 * t384 + t30 / t228 * t232)))
  v2sigma2_0_ = 0.2e1 * r0 * t425
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
  t23 = t3 ** 2
  t24 = params.c1 * t23
  t26 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t26 * t28
  t30 = t24 * t29
  t31 = params.beta * s0
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = r0 ** 2
  t36 = 0.1e1 / t19 / t34
  t38 = params.gamma * params.beta
  t39 = jnp.sqrt(s0)
  t40 = t38 * t39
  t42 = 0.1e1 / t18 / r0
  t46 = jnp.asinh(t39 * t32 * t42)
  t49 = t40 * t32 * t42 * t46 + 0.1e1
  t50 = 0.1e1 / t49
  t55 = params.c2 * t23
  t56 = s0 * t33
  t60 = params.beta * t39 * s0
  t61 = t34 ** 2
  t62 = 0.1e1 / t61
  t63 = t60 * t62
  t64 = t49 ** 2
  t65 = 0.1e1 / t64
  t66 = t65 * params.gamma
  t67 = t66 * t46
  t74 = params.c0 - 0.2e1 / 0.9e1 * t30 * t31 * t33 * t36 * t50 - 0.2e1 / 0.9e1 * t55 * t29 * (t56 * t36 * t50 - 0.2e1 * t63 * t67)
  t79 = t17 / t19
  t80 = t34 * r0
  t82 = 0.1e1 / t19 / t80
  t83 = t33 * t82
  t89 = t24 * t29 * params.beta
  t90 = t36 * t65
  t96 = t38 * s0
  t97 = t56 * t36
  t98 = 0.1e1 + t97
  t99 = jnp.sqrt(t98)
  t100 = 0.1e1 / t99
  t104 = -0.4e1 / 0.3e1 * t40 * t32 / t18 / t34 * t46 - 0.4e1 / 0.3e1 * t96 * t83 * t100
  t106 = t56 * t90 * t104
  t112 = t61 * r0
  t114 = t60 / t112
  t118 = 0.1e1 / t64 / t49
  t119 = t118 * params.gamma
  t121 = t119 * t46 * t104
  t124 = s0 ** 2
  t125 = params.beta * t124
  t126 = t61 * t34
  t128 = 0.1e1 / t18 / t126
  t131 = t66 * t32 * t100
  t138 = 0.16e2 / 0.27e2 * t30 * t31 * t83 * t50 + 0.2e1 / 0.9e1 * t89 * t106 - 0.2e1 / 0.9e1 * t55 * t29 * (-0.8e1 / 0.3e1 * t56 * t82 * t50 - t106 + 0.8e1 * t114 * t67 + 0.4e1 * t63 * t121 + 0.8e1 / 0.3e1 * t125 * t128 * t131)
  t142 = t17 * t18
  t144 = 0.1e1 / t19 / t61
  t145 = t33 * t144
  t150 = t82 * t65
  t152 = t56 * t150 * t104
  t156 = t104 ** 2
  t158 = t56 * t36 * t118 * t156
  t170 = t38 * t124
  t171 = t61 * t80
  t173 = 0.1e1 / t18 / t171
  t176 = 0.1e1 / t99 / t98
  t180 = 0.28e2 / 0.9e1 * t40 * t32 / t18 / t80 * t46 + 0.20e2 / 0.3e1 * t96 * t145 * t100 - 0.32e2 / 0.9e1 * t170 * t32 * t173 * t176
  t182 = t56 * t90 * t180
  t191 = t60 / t126
  t199 = t64 ** 2
  t200 = 0.1e1 / t199
  t203 = t200 * params.gamma * t46 * t156
  t207 = t125 * t128 * t118
  t208 = params.gamma * t32
  t210 = t208 * t100 * t104
  t214 = t119 * t46 * t180
  t217 = t124 * s0
  t218 = params.beta * t217
  t219 = t61 ** 2
  t222 = t218 / t219 / t34
  t223 = t66 * t176
  t226 = 0.88e2 / 0.9e1 * t56 * t144 * t50 + 0.16e2 / 0.3e1 * t152 + 0.2e1 * t158 - t182 - 0.40e2 * t191 * t67 - 0.32e2 * t114 * t121 - 0.248e3 / 0.9e1 * t125 * t173 * t131 - 0.12e2 * t63 * t203 - 0.32e2 / 0.3e1 * t207 * t210 + 0.4e1 * t63 * t214 + 0.64e2 / 0.9e1 * t222 * t223
  t230 = -0.176e3 / 0.81e2 * t30 * t31 * t145 * t50 - 0.32e2 / 0.27e2 * t89 * t152 - 0.4e1 / 0.9e1 * t89 * t158 + 0.2e1 / 0.9e1 * t89 * t182 - 0.2e1 / 0.9e1 * t55 * t29 * t226
  t235 = f.my_piecewise3(t2, 0, t6 * t22 * t74 / 0.12e2 - t6 * t79 * t138 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t142 * t230)
  t248 = 0.1e1 / t19 / t112
  t249 = t33 * t248
  t256 = t56 * t144 * t65 * t104
  t261 = t56 * t82 * t118 * t156
  t265 = t56 * t150 * t180
  t269 = t156 * t104
  t271 = t56 * t36 * t200 * t269
  t276 = t97 * t118 * t104 * t180
  t289 = 0.1e1 / t18 / t219
  t295 = 0.1e1 / t219 / t80
  t297 = t98 ** 2
  t299 = 0.1e1 / t99 / t297
  t303 = -0.280e3 / 0.27e2 * t40 * t32 / t18 / t61 * t46 - 0.952e3 / 0.27e2 * t96 * t249 * t100 + 0.1184e4 / 0.27e2 * t170 * t32 * t289 * t176 - 0.256e3 / 0.9e1 * t38 * t217 * t295 * t299
  t305 = t56 * t90 * t303
  t327 = t124 ** 2
  t379 = -t305 + 0.144e3 * t114 * t203 + 0.496e3 / 0.3e1 * t125 * t173 * t118 * t210 + 0.48e2 * t63 / t199 / t49 * params.gamma * t46 * t269 - 0.36e2 * t60 * t62 * t200 * params.gamma * t46 * t104 * t180 + 0.48e2 * t125 * t128 * t200 * t208 * t100 * t156 - 0.16e2 * t207 * t208 * t100 * t180 - 0.16e2 * t261 - 0.6e1 * t271 + 0.6e1 * t276 - 0.3904e4 / 0.27e2 * t218 * t295 * t223
  t389 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t36 * t74 + t6 * t22 * t138 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t79 * t230 - 0.3e1 / 0.8e1 * t6 * t142 * (0.2464e4 / 0.243e3 * t30 * t31 * t249 * t50 + 0.176e3 / 0.27e2 * t89 * t256 + 0.32e2 / 0.9e1 * t89 * t261 - 0.16e2 / 0.9e1 * t89 * t265 + 0.4e1 / 0.3e1 * t89 * t271 - 0.4e1 / 0.3e1 * t89 * t276 + 0.2e1 / 0.9e1 * t89 * t305 - 0.2e1 / 0.9e1 * t55 * t29 * (0.240e3 * t60 / t171 * t67 + 0.240e3 * t191 * t121 + 0.6896e4 / 0.27e2 * t125 * t289 * t131 - 0.48e2 * t114 * t214 - 0.128e3 / 0.3e1 * t222 * t119 * t176 * t104 + 0.4e1 * t63 * t119 * t46 * t303 + 0.256e3 / 0.9e1 * params.beta * t327 / t19 / t219 / t112 * t66 * t299 * t33 - 0.1232e4 / 0.27e2 * t56 * t248 * t50 - 0.88e2 / 0.3e1 * t256 + 0.8e1 * t265 + t379)))
  v3rho3_0_ = 0.2e1 * r0 * t389 + 0.6e1 * t235

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
  t24 = t3 ** 2
  t25 = params.c1 * t24
  t27 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / t27 * t29
  t31 = t25 * t30
  t32 = params.beta * s0
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t36 = params.gamma * params.beta
  t37 = jnp.sqrt(s0)
  t38 = t36 * t37
  t40 = 0.1e1 / t19 / r0
  t44 = jnp.asinh(t37 * t33 * t40)
  t47 = t38 * t33 * t40 * t44 + 0.1e1
  t48 = 0.1e1 / t47
  t53 = params.c2 * t24
  t54 = s0 * t34
  t58 = params.beta * t37 * s0
  t59 = t18 ** 2
  t60 = 0.1e1 / t59
  t61 = t58 * t60
  t62 = t47 ** 2
  t63 = 0.1e1 / t62
  t64 = t63 * params.gamma
  t65 = t64 * t44
  t72 = params.c0 - 0.2e1 / 0.9e1 * t31 * t32 * t34 * t22 * t48 - 0.2e1 / 0.9e1 * t53 * t30 * (t54 * t22 * t48 - 0.2e1 * t61 * t65)
  t78 = t17 / t20 / r0
  t79 = t18 * r0
  t81 = 0.1e1 / t20 / t79
  t82 = t34 * t81
  t88 = t25 * t30 * params.beta
  t89 = t22 * t63
  t95 = t36 * s0
  t96 = t54 * t22
  t97 = 0.1e1 + t96
  t98 = jnp.sqrt(t97)
  t99 = 0.1e1 / t98
  t103 = -0.4e1 / 0.3e1 * t38 * t33 / t19 / t18 * t44 - 0.4e1 / 0.3e1 * t95 * t82 * t99
  t105 = t54 * t89 * t103
  t111 = t59 * r0
  t112 = 0.1e1 / t111
  t113 = t58 * t112
  t117 = 0.1e1 / t62 / t47
  t118 = t117 * params.gamma
  t120 = t118 * t44 * t103
  t123 = s0 ** 2
  t124 = params.beta * t123
  t125 = t59 * t18
  t127 = 0.1e1 / t19 / t125
  t130 = t64 * t33 * t99
  t137 = 0.16e2 / 0.27e2 * t31 * t32 * t82 * t48 + 0.2e1 / 0.9e1 * t88 * t105 - 0.2e1 / 0.9e1 * t53 * t30 * (-0.8e1 / 0.3e1 * t54 * t81 * t48 - t105 + 0.8e1 * t113 * t65 + 0.4e1 * t61 * t120 + 0.8e1 / 0.3e1 * t124 * t127 * t130)
  t142 = t17 / t20
  t144 = 0.1e1 / t20 / t59
  t145 = t34 * t144
  t150 = t81 * t63
  t152 = t54 * t150 * t103
  t155 = t22 * t117
  t156 = t103 ** 2
  t158 = t54 * t155 * t156
  t170 = t36 * t123
  t171 = t59 * t79
  t173 = 0.1e1 / t19 / t171
  t176 = 0.1e1 / t98 / t97
  t180 = 0.28e2 / 0.9e1 * t38 * t33 / t19 / t79 * t44 + 0.20e2 / 0.3e1 * t95 * t145 * t99 - 0.32e2 / 0.9e1 * t170 * t33 * t173 * t176
  t182 = t54 * t89 * t180
  t191 = t58 / t125
  t199 = t62 ** 2
  t200 = 0.1e1 / t199
  t201 = t200 * params.gamma
  t203 = t201 * t44 * t156
  t207 = t124 * t127 * t117
  t208 = params.gamma * t33
  t209 = t99 * t103
  t210 = t208 * t209
  t214 = t118 * t44 * t180
  t217 = t123 * s0
  t218 = params.beta * t217
  t219 = t59 ** 2
  t222 = t218 / t219 / t18
  t223 = t64 * t176
  t226 = 0.88e2 / 0.9e1 * t54 * t144 * t48 + 0.16e2 / 0.3e1 * t152 + 0.2e1 * t158 - t182 - 0.40e2 * t191 * t65 - 0.32e2 * t113 * t120 - 0.248e3 / 0.9e1 * t124 * t173 * t130 - 0.12e2 * t61 * t203 - 0.32e2 / 0.3e1 * t207 * t210 + 0.4e1 * t61 * t214 + 0.64e2 / 0.9e1 * t222 * t223
  t230 = -0.176e3 / 0.81e2 * t31 * t32 * t145 * t48 - 0.32e2 / 0.27e2 * t88 * t152 - 0.4e1 / 0.9e1 * t88 * t158 + 0.2e1 / 0.9e1 * t88 * t182 - 0.2e1 / 0.9e1 * t53 * t30 * t226
  t234 = t17 * t19
  t236 = 0.1e1 / t20 / t111
  t237 = t34 * t236
  t242 = t144 * t63
  t244 = t54 * t242 * t103
  t249 = t54 * t81 * t117 * t156
  t253 = t54 * t150 * t180
  t257 = t156 * t103
  t259 = t54 * t22 * t200 * t257
  t263 = t117 * t103 * t180
  t264 = t96 * t263
  t277 = 0.1e1 / t19 / t219
  t283 = 0.1e1 / t219 / t79
  t285 = t97 ** 2
  t287 = 0.1e1 / t98 / t285
  t291 = -0.280e3 / 0.27e2 * t38 * t33 / t19 / t59 * t44 - 0.952e3 / 0.27e2 * t95 * t237 * t99 + 0.1184e4 / 0.27e2 * t170 * t33 * t277 * t176 - 0.256e3 / 0.9e1 * t36 * t217 * t283 * t287
  t293 = t54 * t89 * t291
  t297 = t58 / t171
  t308 = t118 * t176 * t103
  t312 = t118 * t44 * t291
  t315 = t123 ** 2
  t316 = params.beta * t315
  t319 = 0.1e1 / t20 / t219 / t111
  t322 = t64 * t287 * t34
  t332 = 0.1e1 / t199 / t47
  t335 = t332 * params.gamma * t44 * t257
  t339 = t58 * t60 * t200
  t340 = params.gamma * t44
  t342 = t340 * t103 * t180
  t346 = t124 * t127 * t200
  t348 = t208 * t99 * t156
  t352 = t208 * t99 * t180
  t358 = t124 * t173 * t117
  t364 = t218 * t283
  t367 = -t293 + 0.48e2 * t61 * t335 - 0.36e2 * t339 * t342 + 0.48e2 * t346 * t348 - 0.16e2 * t207 * t352 + 0.144e3 * t113 * t203 + 0.496e3 / 0.3e1 * t358 * t210 - 0.16e2 * t249 - 0.6e1 * t259 + 0.6e1 * t264 - 0.3904e4 / 0.27e2 * t364 * t223
  t372 = 0.2464e4 / 0.243e3 * t31 * t32 * t237 * t48 + 0.176e3 / 0.27e2 * t88 * t244 + 0.32e2 / 0.9e1 * t88 * t249 - 0.16e2 / 0.9e1 * t88 * t253 + 0.4e1 / 0.3e1 * t88 * t259 - 0.4e1 / 0.3e1 * t88 * t264 + 0.2e1 / 0.9e1 * t88 * t293 - 0.2e1 / 0.9e1 * t53 * t30 * (0.240e3 * t297 * t65 + 0.240e3 * t191 * t120 + 0.6896e4 / 0.27e2 * t124 * t277 * t130 - 0.48e2 * t113 * t214 - 0.128e3 / 0.3e1 * t222 * t308 + 0.4e1 * t61 * t312 + 0.256e3 / 0.9e1 * t316 * t319 * t322 - 0.1232e4 / 0.27e2 * t54 * t236 * t48 - 0.88e2 / 0.3e1 * t244 + 0.8e1 * t253 + t367)
  t377 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t72 + t6 * t78 * t137 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t142 * t230 - 0.3e1 / 0.8e1 * t6 * t234 * t372)
  t393 = 0.1e1 / t20 / t125
  t394 = t34 * t393
  t401 = t54 * t236 * t63 * t103
  t406 = t54 * t144 * t117 * t156
  t410 = t54 * t242 * t180
  t415 = t54 * t81 * t200 * t257
  t419 = t54 * t81 * t263
  t423 = t54 * t150 * t291
  t427 = t156 ** 2
  t429 = t54 * t22 * t332 * t427
  t434 = t96 * t200 * t156 * t180
  t437 = t180 ** 2
  t439 = t54 * t155 * t437
  t444 = t96 * t117 * t291 * t103
  t458 = 0.1e1 / t19 / t219 / r0
  t464 = 0.1e1 / t219 / t59
  t472 = 0.1e1 / t20 / t219 / t125
  t475 = 0.1e1 / t98 / t285 / t97
  t480 = 0.3640e4 / 0.81e2 * t38 * t33 / t19 / t111 * t44 + 0.5768e4 / 0.27e2 * t95 * t394 * t99 - 0.37216e5 / 0.81e2 * t170 * t33 * t458 * t176 + 0.17920e5 / 0.27e2 * t36 * t217 * t464 * t287 - 0.5120e4 / 0.27e2 * t36 * t315 * t472 * t475 * t34
  t482 = t54 * t89 * t480
  t538 = -0.36e2 * t434 + 0.352e3 / 0.3e1 * t406 + 0.64e2 * t415 + 0.24e2 * t429 + 0.6e1 * t439 + 0.4928e4 / 0.27e2 * t401 - 0.176e3 / 0.3e1 * t410 + 0.32e2 / 0.3e1 * t423 - t482 + 0.288e3 * t58 * t60 * t332 * t340 * t156 * t180 - 0.256e3 * t124 * t127 * t332 * t208 * t99 * t257 - 0.55168e5 / 0.27e2 * t124 * t277 * t117 * t210 + 0.576e3 * t58 * t112 * t200 * t342 + 0.992e3 / 0.3e1 * t358 * t352 - 0.2048e4 / 0.9e1 * t316 * t319 * t117 * params.gamma * t287 * t103 * t34 - 0.48e2 * t339 * t340 * t291 * t103 - 0.64e2 / 0.3e1 * t207 * t208 * t99 * t291 - 0.992e3 * t124 * t173 * t200 * t348 - 0.1680e4 * t58 / t219 * t65
  t556 = t219 ** 2
  t603 = 0.184000e6 / 0.81e2 * t218 * t464 * t223 - 0.64e2 * t419 + 0.8e1 * t444 - 0.64e2 * t113 * t312 - 0.256e3 / 0.3e1 * t222 * t118 * t176 * t180 + 0.4e1 * t61 * t118 * t44 * t480 + 0.10240e5 / 0.27e2 * params.beta * t315 * s0 / t19 / t556 / r0 * t64 * t475 * t33 - 0.1920e4 * t297 * t120 - 0.768e3 * t113 * t335 - 0.240e3 * t61 / t199 / t62 * params.gamma * t44 * t427 - 0.36e2 * t61 * t201 * t44 * t437 - 0.1440e4 * t191 * t203 + 0.31232e5 / 0.27e2 * t364 * t308 + 0.256e3 * t222 * t201 * t176 * t156 - 0.8704e4 / 0.9e1 * t316 * t472 * t322 - 0.198320e6 / 0.81e2 * t124 * t458 * t130 + 0.480e3 * t191 * t214 + 0.20944e5 / 0.81e2 * t54 * t393 * t48 + 0.192e3 * t346 * t208 * t209 * t180
  t608 = -0.41888e5 / 0.729e3 * t31 * t32 * t394 * t48 - 0.9856e4 / 0.243e3 * t88 * t401 - 0.704e3 / 0.27e2 * t88 * t406 + 0.352e3 / 0.27e2 * t88 * t410 - 0.128e3 / 0.9e1 * t88 * t415 + 0.128e3 / 0.9e1 * t88 * t419 - 0.64e2 / 0.27e2 * t88 * t423 - 0.16e2 / 0.3e1 * t88 * t429 + 0.8e1 * t88 * t434 - 0.4e1 / 0.3e1 * t88 * t439 - 0.16e2 / 0.9e1 * t88 * t444 + 0.2e1 / 0.9e1 * t88 * t482 - 0.2e1 / 0.9e1 * t53 * t30 * (t538 + t603)
  t613 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t81 * t72 - 0.5e1 / 0.9e1 * t6 * t23 * t137 + t6 * t78 * t230 / 0.2e1 - t6 * t142 * t372 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t234 * t608)
  v4rho4_0_ = 0.2e1 * r0 * t613 + 0.8e1 * t377

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
  t35 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t37 = 4 ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t35 * t37
  t39 = params.c1 * t32 * t38
  t40 = params.beta * s0
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t46 = params.gamma * params.beta
  t47 = jnp.sqrt(s0)
  t50 = t47 / t42 / r0
  t51 = jnp.arcsinh(t50)
  t54 = t46 * t50 * t51 + 0.1e1
  t55 = 0.1e1 / t54
  t60 = params.c2 * t32
  t61 = s0 * t45
  t64 = params.beta * t47 * s0
  t65 = t41 ** 2
  t67 = t64 / t65
  t68 = t54 ** 2
  t69 = 0.1e1 / t68
  t70 = t69 * params.gamma
  t71 = t70 * t51
  t77 = params.c0 - 0.2e1 / 0.9e1 * t39 * t40 * t45 * t55 - 0.2e1 / 0.9e1 * t60 * t38 * (t61 * t55 - t67 * t71)
  t81 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t82 = t81 * f.p.zeta_threshold
  t84 = f.my_piecewise3(t20, t82, t21 * t19)
  t85 = t30 ** 2
  t86 = 0.1e1 / t85
  t87 = t84 * t86
  t90 = t5 * t87 * t77 / 0.8e1
  t91 = t84 * t30
  t92 = t41 * r0
  t94 = 0.1e1 / t43 / t92
  t99 = t45 * t69
  t105 = s0 * t94
  t106 = 0.1e1 + t61
  t107 = jnp.sqrt(t106)
  t108 = 0.1e1 / t107
  t112 = -0.4e1 / 0.3e1 * t46 * t47 / t42 / t41 * t51 - 0.4e1 / 0.3e1 * t46 * t105 * t108
  t119 = t69 * t112
  t123 = t64 / t65 / r0
  t127 = 0.1e1 / t68 / t54
  t128 = t127 * params.gamma
  t130 = t128 * t51 * t112
  t133 = s0 ** 2
  t134 = params.beta * t133
  t135 = t65 * t41
  t138 = t134 / t42 / t135
  t139 = t70 * t108
  t146 = 0.16e2 / 0.27e2 * t39 * t40 * t94 * t55 + 0.2e1 / 0.9e1 * t39 * t40 * t99 * t112 - 0.2e1 / 0.9e1 * t60 * t38 * (-0.8e1 / 0.3e1 * t105 * t55 - t61 * t119 + 0.4e1 * t123 * t71 + 0.2e1 * t67 * t130 + 0.4e1 / 0.3e1 * t138 * t139)
  t151 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t77 - t90 - 0.3e1 / 0.8e1 * t5 * t91 * t146)
  t153 = r1 <= f.p.dens_threshold
  t154 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t155 = 0.1e1 + t154
  t156 = t155 <= f.p.zeta_threshold
  t157 = t155 ** (0.1e1 / 0.3e1)
  t159 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t162 = f.my_piecewise3(t156, 0, 0.4e1 / 0.3e1 * t157 * t159)
  t163 = t162 * t30
  t164 = params.beta * s2
  t165 = r1 ** 2
  t166 = r1 ** (0.1e1 / 0.3e1)
  t167 = t166 ** 2
  t169 = 0.1e1 / t167 / t165
  t170 = jnp.sqrt(s2)
  t173 = t170 / t166 / r1
  t174 = jnp.arcsinh(t173)
  t177 = t46 * t173 * t174 + 0.1e1
  t178 = 0.1e1 / t177
  t183 = s2 * t169
  t186 = params.beta * t170 * s2
  t187 = t165 ** 2
  t189 = t186 / t187
  t190 = t177 ** 2
  t191 = 0.1e1 / t190
  t192 = t191 * params.gamma
  t193 = t192 * t174
  t199 = params.c0 - 0.2e1 / 0.9e1 * t39 * t164 * t169 * t178 - 0.2e1 / 0.9e1 * t60 * t38 * (t183 * t178 - t189 * t193)
  t204 = f.my_piecewise3(t156, t82, t157 * t155)
  t205 = t204 * t86
  t208 = t5 * t205 * t199 / 0.8e1
  t210 = f.my_piecewise3(t153, 0, -0.3e1 / 0.8e1 * t5 * t163 * t199 - t208)
  t212 = t21 ** 2
  t213 = 0.1e1 / t212
  t214 = t26 ** 2
  t219 = t16 / t22 / t6
  t221 = -0.2e1 * t23 + 0.2e1 * t219
  t222 = f.my_piecewise5(t10, 0, t14, 0, t221)
  t226 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t213 * t214 + 0.4e1 / 0.3e1 * t21 * t222)
  t233 = t5 * t29 * t86 * t77
  t239 = 0.1e1 / t85 / t6
  t243 = t5 * t84 * t239 * t77 / 0.12e2
  t245 = t5 * t87 * t146
  t248 = 0.1e1 / t43 / t65
  t259 = t112 ** 2
  t270 = s0 * t248
  t276 = 0.1e1 / t42 / t65 / t92
  t279 = 0.1e1 / t107 / t106
  t283 = 0.28e2 / 0.9e1 * t46 * t47 / t42 / t92 * t51 + 0.20e2 / 0.3e1 * t46 * t270 * t108 - 0.16e2 / 0.9e1 * t46 * t133 * t276 * t279
  t306 = t68 ** 2
  t323 = t65 ** 2
  t330 = 0.88e2 / 0.9e1 * t270 * t55 + 0.16e2 / 0.3e1 * t105 * t119 + 0.2e1 * t61 * t127 * t259 - t61 * t69 * t283 - 0.20e2 * t64 / t135 * t71 - 0.16e2 * t123 * t130 - 0.124e3 / 0.9e1 * t134 * t276 * t139 - 0.6e1 * t67 / t306 * params.gamma * t51 * t259 - 0.16e2 / 0.3e1 * t138 * t128 * t108 * t112 + 0.2e1 * t67 * t128 * t51 * t283 + 0.16e2 / 0.9e1 * params.beta * t133 * s0 / t323 / t41 * t70 * t279
  t339 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t226 * t30 * t77 - t233 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t146 + t243 - t245 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t91 * (-0.176e3 / 0.81e2 * t39 * t40 * t248 * t55 - 0.32e2 / 0.27e2 * t39 * t40 * t94 * t69 * t112 - 0.4e1 / 0.9e1 * t39 * t40 * t45 * t127 * t259 + 0.2e1 / 0.9e1 * t39 * t40 * t99 * t283 - 0.2e1 / 0.9e1 * t60 * t38 * t330))
  t340 = t157 ** 2
  t341 = 0.1e1 / t340
  t342 = t159 ** 2
  t346 = f.my_piecewise5(t14, 0, t10, 0, -t221)
  t350 = f.my_piecewise3(t156, 0, 0.4e1 / 0.9e1 * t341 * t342 + 0.4e1 / 0.3e1 * t157 * t346)
  t357 = t5 * t162 * t86 * t199
  t362 = t5 * t204 * t239 * t199 / 0.12e2
  t364 = f.my_piecewise3(t153, 0, -0.3e1 / 0.8e1 * t5 * t350 * t30 * t199 - t357 / 0.4e1 + t362)
  d11 = 0.2e1 * t151 + 0.2e1 * t210 + t6 * (t339 + t364)
  t367 = -t7 - t24
  t368 = f.my_piecewise5(t10, 0, t14, 0, t367)
  t371 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t368)
  t372 = t371 * t30
  t377 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t372 * t77 - t90)
  t379 = f.my_piecewise5(t14, 0, t10, 0, -t367)
  t382 = f.my_piecewise3(t156, 0, 0.4e1 / 0.3e1 * t157 * t379)
  t383 = t382 * t30
  t387 = t204 * t30
  t388 = t165 * r1
  t390 = 0.1e1 / t167 / t388
  t395 = t169 * t191
  t401 = s2 * t390
  t402 = 0.1e1 + t183
  t403 = jnp.sqrt(t402)
  t404 = 0.1e1 / t403
  t408 = -0.4e1 / 0.3e1 * t46 * t170 / t166 / t165 * t174 - 0.4e1 / 0.3e1 * t46 * t401 * t404
  t415 = t191 * t408
  t419 = t186 / t187 / r1
  t423 = 0.1e1 / t190 / t177
  t424 = t423 * params.gamma
  t426 = t424 * t174 * t408
  t429 = s2 ** 2
  t430 = params.beta * t429
  t431 = t187 * t165
  t434 = t430 / t166 / t431
  t435 = t192 * t404
  t442 = 0.16e2 / 0.27e2 * t39 * t164 * t390 * t178 + 0.2e1 / 0.9e1 * t39 * t164 * t395 * t408 - 0.2e1 / 0.9e1 * t60 * t38 * (-0.8e1 / 0.3e1 * t401 * t178 - t183 * t415 + 0.4e1 * t419 * t193 + 0.2e1 * t189 * t426 + 0.4e1 / 0.3e1 * t434 * t435)
  t447 = f.my_piecewise3(t153, 0, -0.3e1 / 0.8e1 * t5 * t383 * t199 - t208 - 0.3e1 / 0.8e1 * t5 * t387 * t442)
  t451 = 0.2e1 * t219
  t452 = f.my_piecewise5(t10, 0, t14, 0, t451)
  t456 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t213 * t368 * t26 + 0.4e1 / 0.3e1 * t21 * t452)
  t463 = t5 * t371 * t86 * t77
  t471 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t456 * t30 * t77 - t463 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t372 * t146 - t233 / 0.8e1 + t243 - t245 / 0.8e1)
  t475 = f.my_piecewise5(t14, 0, t10, 0, -t451)
  t479 = f.my_piecewise3(t156, 0, 0.4e1 / 0.9e1 * t341 * t379 * t159 + 0.4e1 / 0.3e1 * t157 * t475)
  t486 = t5 * t382 * t86 * t199
  t493 = t5 * t205 * t442
  t496 = f.my_piecewise3(t153, 0, -0.3e1 / 0.8e1 * t5 * t479 * t30 * t199 - t486 / 0.8e1 - t357 / 0.8e1 + t362 - 0.3e1 / 0.8e1 * t5 * t163 * t442 - t493 / 0.8e1)
  d12 = t151 + t210 + t377 + t447 + t6 * (t471 + t496)
  t501 = t368 ** 2
  t505 = 0.2e1 * t23 + 0.2e1 * t219
  t506 = f.my_piecewise5(t10, 0, t14, 0, t505)
  t510 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t213 * t501 + 0.4e1 / 0.3e1 * t21 * t506)
  t517 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t510 * t30 * t77 - t463 / 0.4e1 + t243)
  t518 = t379 ** 2
  t522 = f.my_piecewise5(t14, 0, t10, 0, -t505)
  t526 = f.my_piecewise3(t156, 0, 0.4e1 / 0.9e1 * t341 * t518 + 0.4e1 / 0.3e1 * t157 * t522)
  t537 = 0.1e1 / t167 / t187
  t548 = t408 ** 2
  t559 = s2 * t537
  t565 = 0.1e1 / t166 / t187 / t388
  t568 = 0.1e1 / t403 / t402
  t572 = 0.28e2 / 0.9e1 * t46 * t170 / t166 / t388 * t174 + 0.20e2 / 0.3e1 * t46 * t559 * t404 - 0.16e2 / 0.9e1 * t46 * t429 * t565 * t568
  t595 = t190 ** 2
  t612 = t187 ** 2
  t619 = 0.88e2 / 0.9e1 * t559 * t178 + 0.16e2 / 0.3e1 * t401 * t415 + 0.2e1 * t183 * t423 * t548 - t183 * t191 * t572 - 0.20e2 * t186 / t431 * t193 - 0.16e2 * t419 * t426 - 0.124e3 / 0.9e1 * t430 * t565 * t435 - 0.6e1 * t189 / t595 * params.gamma * t174 * t548 - 0.16e2 / 0.3e1 * t434 * t424 * t404 * t408 + 0.2e1 * t189 * t424 * t174 * t572 + 0.16e2 / 0.9e1 * params.beta * t429 * s2 / t612 / t165 * t192 * t568
  t628 = f.my_piecewise3(t153, 0, -0.3e1 / 0.8e1 * t5 * t526 * t30 * t199 - t486 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t383 * t442 + t362 - t493 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t387 * (-0.176e3 / 0.81e2 * t39 * t164 * t537 * t178 - 0.32e2 / 0.27e2 * t39 * t164 * t390 * t191 * t408 - 0.4e1 / 0.9e1 * t39 * t164 * t169 * t423 * t548 + 0.2e1 / 0.9e1 * t39 * t164 * t395 * t572 - 0.2e1 / 0.9e1 * t60 * t38 * t619))
  d22 = 0.2e1 * t377 + 0.2e1 * t447 + t6 * (t517 + t628)
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
  t45 = params.c1 * t44
  t47 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t49 = 4 ** (0.1e1 / 0.3e1)
  t50 = 0.1e1 / t47 * t49
  t51 = t45 * t50
  t52 = params.beta * s0
  t53 = r0 ** 2
  t54 = r0 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t57 = 0.1e1 / t55 / t53
  t58 = params.gamma * params.beta
  t59 = jnp.sqrt(s0)
  t62 = t59 / t54 / r0
  t63 = jnp.asinh(t62)
  t66 = t58 * t62 * t63 + 0.1e1
  t67 = 0.1e1 / t66
  t72 = params.c2 * t44
  t73 = s0 * t57
  t76 = params.beta * t59 * s0
  t77 = t53 ** 2
  t78 = 0.1e1 / t77
  t79 = t76 * t78
  t80 = t66 ** 2
  t81 = 0.1e1 / t80
  t82 = t81 * params.gamma
  t83 = t82 * t63
  t89 = params.c0 - 0.2e1 / 0.9e1 * t51 * t52 * t57 * t67 - 0.2e1 / 0.9e1 * t72 * t50 * (t73 * t67 - t79 * t83)
  t95 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t96 = t42 ** 2
  t97 = 0.1e1 / t96
  t98 = t95 * t97
  t102 = t95 * t42
  t103 = t53 * r0
  t105 = 0.1e1 / t55 / t103
  t110 = t57 * t81
  t116 = s0 * t105
  t117 = 0.1e1 + t73
  t118 = jnp.sqrt(t117)
  t119 = 0.1e1 / t118
  t123 = -0.4e1 / 0.3e1 * t58 * t59 / t54 / t53 * t63 - 0.4e1 / 0.3e1 * t58 * t116 * t119
  t130 = t81 * t123
  t132 = t77 * r0
  t134 = t76 / t132
  t138 = 0.1e1 / t80 / t66
  t139 = t138 * params.gamma
  t141 = t139 * t63 * t123
  t144 = s0 ** 2
  t145 = params.beta * t144
  t146 = t77 * t53
  t149 = t145 / t54 / t146
  t150 = t82 * t119
  t157 = 0.16e2 / 0.27e2 * t51 * t52 * t105 * t67 + 0.2e1 / 0.9e1 * t51 * t52 * t110 * t123 - 0.2e1 / 0.9e1 * t72 * t50 * (-0.8e1 / 0.3e1 * t116 * t67 - t73 * t130 + 0.4e1 * t134 * t83 + 0.2e1 * t79 * t141 + 0.4e1 / 0.3e1 * t149 * t150)
  t161 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t162 = t161 * f.p.zeta_threshold
  t164 = f.my_piecewise3(t20, t162, t21 * t19)
  t166 = 0.1e1 / t96 / t6
  t167 = t164 * t166
  t171 = t164 * t97
  t175 = t164 * t42
  t177 = 0.1e1 / t55 / t77
  t182 = t105 * t81
  t188 = t123 ** 2
  t199 = s0 * t177
  t203 = t77 * t103
  t205 = 0.1e1 / t54 / t203
  t208 = 0.1e1 / t118 / t117
  t212 = 0.28e2 / 0.9e1 * t58 * t59 / t54 / t103 * t63 + 0.20e2 / 0.3e1 * t58 * t199 * t119 - 0.16e2 / 0.9e1 * t58 * t144 * t205 * t208
  t221 = t138 * t188
  t224 = t81 * t212
  t227 = t76 / t146
  t232 = t145 * t205
  t235 = t80 ** 2
  t236 = 0.1e1 / t235
  t237 = t236 * params.gamma
  t239 = t237 * t63 * t188
  t243 = t139 * t119 * t123
  t247 = t139 * t63 * t212
  t250 = t144 * s0
  t251 = params.beta * t250
  t252 = t77 ** 2
  t255 = t251 / t252 / t53
  t256 = t82 * t208
  t259 = 0.88e2 / 0.9e1 * t199 * t67 + 0.16e2 / 0.3e1 * t116 * t130 + 0.2e1 * t73 * t221 - t73 * t224 - 0.20e2 * t227 * t83 - 0.16e2 * t134 * t141 - 0.124e3 / 0.9e1 * t232 * t150 - 0.6e1 * t79 * t239 - 0.16e2 / 0.3e1 * t149 * t243 + 0.2e1 * t79 * t247 + 0.16e2 / 0.9e1 * t255 * t256
  t263 = -0.176e3 / 0.81e2 * t51 * t52 * t177 * t67 - 0.32e2 / 0.27e2 * t51 * t52 * t182 * t123 - 0.4e1 / 0.9e1 * t51 * t52 * t57 * t138 * t188 + 0.2e1 / 0.9e1 * t51 * t52 * t110 * t212 - 0.2e1 / 0.9e1 * t72 * t50 * t259
  t268 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t89 - t5 * t98 * t89 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t102 * t157 + t5 * t167 * t89 / 0.12e2 - t5 * t171 * t157 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t175 * t263)
  t270 = r1 <= f.p.dens_threshold
  t271 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t272 = 0.1e1 + t271
  t273 = t272 <= f.p.zeta_threshold
  t274 = t272 ** (0.1e1 / 0.3e1)
  t275 = t274 ** 2
  t276 = 0.1e1 / t275
  t278 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t279 = t278 ** 2
  t283 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t287 = f.my_piecewise3(t273, 0, 0.4e1 / 0.9e1 * t276 * t279 + 0.4e1 / 0.3e1 * t274 * t283)
  t290 = r1 ** 2
  t291 = r1 ** (0.1e1 / 0.3e1)
  t292 = t291 ** 2
  t294 = 0.1e1 / t292 / t290
  t295 = jnp.sqrt(s2)
  t298 = t295 / t291 / r1
  t299 = jnp.asinh(t298)
  t302 = t58 * t298 * t299 + 0.1e1
  t303 = 0.1e1 / t302
  t312 = t290 ** 2
  t315 = t302 ** 2
  t324 = params.c0 - 0.2e1 / 0.9e1 * t51 * params.beta * s2 * t294 * t303 - 0.2e1 / 0.9e1 * t72 * t50 * (s2 * t294 * t303 - params.beta * t295 * s2 / t312 / t315 * params.gamma * t299)
  t330 = f.my_piecewise3(t273, 0, 0.4e1 / 0.3e1 * t274 * t278)
  t336 = f.my_piecewise3(t273, t162, t274 * t272)
  t342 = f.my_piecewise3(t270, 0, -0.3e1 / 0.8e1 * t5 * t287 * t42 * t324 - t5 * t330 * t97 * t324 / 0.4e1 + t5 * t336 * t166 * t324 / 0.12e2)
  t352 = t24 ** 2
  t356 = 0.6e1 * t33 - 0.6e1 * t16 / t352
  t357 = f.my_piecewise5(t10, 0, t14, 0, t356)
  t361 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t357)
  t384 = 0.1e1 / t96 / t24
  t396 = 0.1e1 / t55 / t132
  t416 = t188 * t123
  t425 = t73 * t138 * t123 * t212
  t434 = s0 * t396
  t439 = 0.1e1 / t54 / t252
  t445 = 0.1e1 / t252 / t103
  t447 = t117 ** 2
  t449 = 0.1e1 / t118 / t447
  t453 = -0.280e3 / 0.27e2 * t58 * t59 / t54 / t77 * t63 - 0.952e3 / 0.27e2 * t58 * t434 * t119 + 0.592e3 / 0.27e2 * t58 * t144 * t439 * t208 - 0.64e2 / 0.9e1 * t58 * t250 * t445 * t449
  t521 = t144 ** 2
  t530 = 0.248e3 / 0.3e1 * t232 * t243 - 0.16e2 * t116 * t221 - 0.6e1 * t73 * t236 * t416 + 0.6e1 * t425 - 0.1232e4 / 0.27e2 * t434 * t67 - 0.88e2 / 0.3e1 * t199 * t130 + 0.8e1 * t116 * t224 - t73 * t81 * t453 + 0.3448e4 / 0.27e2 * t145 * t439 * t150 - 0.976e3 / 0.27e2 * t251 * t445 * t256 + 0.64e2 / 0.9e1 * params.beta * t521 / t55 / t252 / t132 * t82 * t449
  t540 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t361 * t42 * t89 - 0.3e1 / 0.8e1 * t5 * t41 * t97 * t89 - 0.9e1 / 0.8e1 * t5 * t43 * t157 + t5 * t95 * t166 * t89 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t98 * t157 - 0.9e1 / 0.8e1 * t5 * t102 * t263 - 0.5e1 / 0.36e2 * t5 * t164 * t384 * t89 + t5 * t167 * t157 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t171 * t263 - 0.3e1 / 0.8e1 * t5 * t175 * (0.2464e4 / 0.243e3 * t51 * t52 * t396 * t67 + 0.176e3 / 0.27e2 * t51 * t52 * t177 * t81 * t123 + 0.32e2 / 0.9e1 * t51 * t52 * t105 * t138 * t188 - 0.16e2 / 0.9e1 * t51 * t52 * t182 * t212 + 0.4e1 / 0.3e1 * t51 * t52 * t57 * t236 * t416 - 0.4e1 / 0.3e1 * t45 * t50 * params.beta * t425 + 0.2e1 / 0.9e1 * t51 * t52 * t110 * t453 - 0.2e1 / 0.9e1 * t72 * t50 * (0.72e2 * t134 * t239 + 0.24e2 * t79 / t235 / t66 * params.gamma * t63 * t416 - 0.18e2 * t76 * t78 * t236 * params.gamma * t63 * t123 * t212 + 0.24e2 * t149 * t237 * t119 * t188 - 0.8e1 * t149 * t139 * t119 * t212 - 0.32e2 / 0.3e1 * t255 * t139 * t208 * t123 + 0.2e1 * t79 * t139 * t63 * t453 + 0.120e3 * t76 / t203 * t83 + 0.120e3 * t227 * t141 - 0.24e2 * t134 * t247 + t530)))
  t550 = f.my_piecewise5(t14, 0, t10, 0, -t356)
  t554 = f.my_piecewise3(t273, 0, -0.8e1 / 0.27e2 / t275 / t272 * t279 * t278 + 0.4e1 / 0.3e1 * t276 * t278 * t283 + 0.4e1 / 0.3e1 * t274 * t550)
  t572 = f.my_piecewise3(t270, 0, -0.3e1 / 0.8e1 * t5 * t554 * t42 * t324 - 0.3e1 / 0.8e1 * t5 * t287 * t97 * t324 + t5 * t330 * t166 * t324 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t336 * t384 * t324)
  d111 = 0.3e1 * t268 + 0.3e1 * t342 + t6 * (t540 + t572)

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
  t57 = params.c1 * t56
  t59 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t61 = 4 ** (0.1e1 / 0.3e1)
  t62 = 0.1e1 / t59 * t61
  t63 = t57 * t62
  t64 = params.beta * s0
  t65 = r0 ** 2
  t66 = r0 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t69 = 0.1e1 / t67 / t65
  t70 = params.gamma * params.beta
  t71 = jnp.sqrt(s0)
  t74 = t71 / t66 / r0
  t75 = jnp.asinh(t74)
  t78 = t70 * t74 * t75 + 0.1e1
  t79 = 0.1e1 / t78
  t84 = params.c2 * t56
  t85 = s0 * t69
  t88 = params.beta * t71 * s0
  t89 = t65 ** 2
  t90 = 0.1e1 / t89
  t91 = t88 * t90
  t92 = t78 ** 2
  t93 = 0.1e1 / t92
  t94 = t93 * params.gamma
  t95 = t94 * t75
  t101 = params.c0 - 0.2e1 / 0.9e1 * t63 * t64 * t69 * t79 - 0.2e1 / 0.9e1 * t84 * t62 * (t85 * t79 - t91 * t95)
  t110 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t111 = t54 ** 2
  t112 = 0.1e1 / t111
  t113 = t110 * t112
  t117 = t110 * t54
  t118 = t65 * r0
  t120 = 0.1e1 / t67 / t118
  t125 = t69 * t93
  t131 = s0 * t120
  t132 = 0.1e1 + t85
  t133 = jnp.sqrt(t132)
  t134 = 0.1e1 / t133
  t138 = -0.4e1 / 0.3e1 * t70 * t71 / t66 / t65 * t75 - 0.4e1 / 0.3e1 * t70 * t131 * t134
  t145 = t93 * t138
  t147 = t89 * r0
  t148 = 0.1e1 / t147
  t149 = t88 * t148
  t153 = 0.1e1 / t92 / t78
  t154 = t153 * params.gamma
  t156 = t154 * t75 * t138
  t159 = s0 ** 2
  t160 = params.beta * t159
  t161 = t89 * t65
  t163 = 0.1e1 / t66 / t161
  t164 = t160 * t163
  t165 = t94 * t134
  t172 = 0.16e2 / 0.27e2 * t63 * t64 * t120 * t79 + 0.2e1 / 0.9e1 * t63 * t64 * t125 * t138 - 0.2e1 / 0.9e1 * t84 * t62 * (-0.8e1 / 0.3e1 * t131 * t79 - t85 * t145 + 0.4e1 * t149 * t95 + 0.2e1 * t91 * t156 + 0.4e1 / 0.3e1 * t164 * t165)
  t178 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t180 = 0.1e1 / t111 / t6
  t181 = t178 * t180
  t185 = t178 * t112
  t189 = t178 * t54
  t191 = 0.1e1 / t67 / t89
  t196 = t120 * t93
  t201 = t69 * t153
  t202 = t138 ** 2
  t213 = s0 * t191
  t217 = t89 * t118
  t219 = 0.1e1 / t66 / t217
  t222 = 0.1e1 / t133 / t132
  t226 = 0.28e2 / 0.9e1 * t70 * t71 / t66 / t118 * t75 + 0.20e2 / 0.3e1 * t70 * t213 * t134 - 0.16e2 / 0.9e1 * t70 * t159 * t219 * t222
  t235 = t153 * t202
  t238 = t93 * t226
  t241 = t88 / t161
  t246 = t160 * t219
  t249 = t92 ** 2
  t250 = 0.1e1 / t249
  t251 = t250 * params.gamma
  t253 = t251 * t75 * t202
  t257 = t154 * t134 * t138
  t261 = t154 * t75 * t226
  t264 = t159 * s0
  t265 = params.beta * t264
  t266 = t89 ** 2
  t269 = t265 / t266 / t65
  t270 = t94 * t222
  t273 = 0.88e2 / 0.9e1 * t213 * t79 + 0.16e2 / 0.3e1 * t131 * t145 + 0.2e1 * t85 * t235 - t85 * t238 - 0.20e2 * t241 * t95 - 0.16e2 * t149 * t156 - 0.124e3 / 0.9e1 * t246 * t165 - 0.6e1 * t91 * t253 - 0.16e2 / 0.3e1 * t164 * t257 + 0.2e1 * t91 * t261 + 0.16e2 / 0.9e1 * t269 * t270
  t277 = -0.176e3 / 0.81e2 * t63 * t64 * t191 * t79 - 0.32e2 / 0.27e2 * t63 * t64 * t196 * t138 - 0.4e1 / 0.9e1 * t63 * t64 * t201 * t202 + 0.2e1 / 0.9e1 * t63 * t64 * t125 * t226 - 0.2e1 / 0.9e1 * t84 * t62 * t273
  t281 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t282 = t281 * f.p.zeta_threshold
  t284 = f.my_piecewise3(t20, t282, t21 * t19)
  t286 = 0.1e1 / t111 / t25
  t287 = t284 * t286
  t291 = t284 * t180
  t295 = t284 * t112
  t299 = t284 * t54
  t301 = 0.1e1 / t67 / t147
  t306 = t191 * t93
  t321 = t202 * t138
  t327 = t57 * t62 * params.beta
  t328 = t153 * t138
  t329 = t328 * t226
  t330 = t85 * t329
  t339 = s0 * t301
  t344 = 0.1e1 / t66 / t266
  t350 = 0.1e1 / t266 / t118
  t352 = t132 ** 2
  t354 = 0.1e1 / t133 / t352
  t358 = -0.280e3 / 0.27e2 * t70 * t71 / t66 / t89 * t75 - 0.952e3 / 0.27e2 * t70 * t339 * t134 + 0.592e3 / 0.27e2 * t70 * t159 * t344 * t222 - 0.64e2 / 0.9e1 * t70 * t264 * t350 * t354
  t364 = 0.1e1 / t249 / t78
  t365 = t364 * params.gamma
  t367 = t365 * t75 * t321
  t371 = t88 * t90 * t250
  t372 = params.gamma * t75
  t373 = t138 * t226
  t374 = t372 * t373
  t380 = t251 * t134 * t202
  t384 = t154 * t134 * t226
  t388 = t154 * t222 * t138
  t392 = t154 * t75 * t358
  t396 = t88 / t217
  t408 = t250 * t321
  t418 = t93 * t358
  t420 = t160 * t344
  t423 = t265 * t350
  t426 = t159 ** 2
  t427 = params.beta * t426
  t431 = t427 / t67 / t266 / t147
  t432 = t94 * t354
  t435 = 0.248e3 / 0.3e1 * t246 * t257 - 0.16e2 * t131 * t235 - 0.6e1 * t85 * t408 + 0.6e1 * t330 - 0.1232e4 / 0.27e2 * t339 * t79 - 0.88e2 / 0.3e1 * t213 * t145 + 0.8e1 * t131 * t238 - t85 * t418 + 0.3448e4 / 0.27e2 * t420 * t165 - 0.976e3 / 0.27e2 * t423 * t270 + 0.64e2 / 0.9e1 * t431 * t432
  t440 = 0.2464e4 / 0.243e3 * t63 * t64 * t301 * t79 + 0.176e3 / 0.27e2 * t63 * t64 * t306 * t138 + 0.32e2 / 0.9e1 * t63 * t64 * t120 * t153 * t202 - 0.16e2 / 0.9e1 * t63 * t64 * t196 * t226 + 0.4e1 / 0.3e1 * t63 * t64 * t69 * t250 * t321 - 0.4e1 / 0.3e1 * t327 * t330 + 0.2e1 / 0.9e1 * t63 * t64 * t125 * t358 - 0.2e1 / 0.9e1 * t84 * t62 * (0.24e2 * t91 * t367 - 0.18e2 * t371 * t374 + 0.72e2 * t149 * t253 + 0.24e2 * t164 * t380 - 0.8e1 * t164 * t384 - 0.32e2 / 0.3e1 * t269 * t388 + 0.2e1 * t91 * t392 + 0.120e3 * t396 * t95 + 0.120e3 * t241 * t156 - 0.24e2 * t149 * t261 + t435)
  t445 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t101 - 0.3e1 / 0.8e1 * t5 * t113 * t101 - 0.9e1 / 0.8e1 * t5 * t117 * t172 + t5 * t181 * t101 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t185 * t172 - 0.9e1 / 0.8e1 * t5 * t189 * t277 - 0.5e1 / 0.36e2 * t5 * t287 * t101 + t5 * t291 * t172 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t295 * t277 - 0.3e1 / 0.8e1 * t5 * t299 * t440)
  t447 = r1 <= f.p.dens_threshold
  t448 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t449 = 0.1e1 + t448
  t450 = t449 <= f.p.zeta_threshold
  t451 = t449 ** (0.1e1 / 0.3e1)
  t452 = t451 ** 2
  t454 = 0.1e1 / t452 / t449
  t456 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t457 = t456 ** 2
  t461 = 0.1e1 / t452
  t462 = t461 * t456
  t464 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t468 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t472 = f.my_piecewise3(t450, 0, -0.8e1 / 0.27e2 * t454 * t457 * t456 + 0.4e1 / 0.3e1 * t462 * t464 + 0.4e1 / 0.3e1 * t451 * t468)
  t475 = r1 ** 2
  t476 = r1 ** (0.1e1 / 0.3e1)
  t477 = t476 ** 2
  t479 = 0.1e1 / t477 / t475
  t480 = jnp.sqrt(s2)
  t483 = t480 / t476 / r1
  t484 = jnp.asinh(t483)
  t487 = t70 * t483 * t484 + 0.1e1
  t488 = 0.1e1 / t487
  t497 = t475 ** 2
  t500 = t487 ** 2
  t509 = params.c0 - 0.2e1 / 0.9e1 * t63 * params.beta * s2 * t479 * t488 - 0.2e1 / 0.9e1 * t84 * t62 * (s2 * t479 * t488 - params.beta * t480 * s2 / t497 / t500 * params.gamma * t484)
  t518 = f.my_piecewise3(t450, 0, 0.4e1 / 0.9e1 * t461 * t457 + 0.4e1 / 0.3e1 * t451 * t464)
  t525 = f.my_piecewise3(t450, 0, 0.4e1 / 0.3e1 * t451 * t456)
  t531 = f.my_piecewise3(t450, t282, t451 * t449)
  t537 = f.my_piecewise3(t447, 0, -0.3e1 / 0.8e1 * t5 * t472 * t54 * t509 - 0.3e1 / 0.8e1 * t5 * t518 * t112 * t509 + t5 * t525 * t180 * t509 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t531 * t286 * t509)
  t540 = 0.1e1 / t67 / t161
  t564 = t131 * t329
  t572 = t202 ** 2
  t579 = t85 * t250 * t202 * t226
  t582 = t226 ** 2
  t588 = t85 * t328 * t358
  t597 = s0 * t540
  t603 = 0.1e1 / t66 / t266 / r0
  t609 = 0.1e1 / t266 / t89
  t616 = 0.1e1 / t67 / t266 / t161
  t620 = 0.1e1 / t133 / t352 / t132
  t624 = 0.3640e4 / 0.81e2 * t70 * t71 / t66 / t147 * t75 + 0.5768e4 / 0.27e2 * t70 * t597 * t134 - 0.18608e5 / 0.81e2 * t70 * t159 * t603 * t222 + 0.4480e4 / 0.27e2 * t70 * t264 * t609 * t354 - 0.1280e4 / 0.27e2 * t70 * t426 * t616 * t620
  t691 = -t85 * t93 * t624 + 0.352e3 / 0.3e1 * t213 * t235 + 0.64e2 * t131 * t408 + 0.24e2 * t85 * t364 * t572 + 0.6e1 * t85 * t153 * t582 + 0.4928e4 / 0.27e2 * t339 * t145 - 0.176e3 / 0.3e1 * t213 * t238 + 0.32e2 / 0.3e1 * t131 * t418 + 0.144e3 * t88 * t90 * t364 * t372 * t202 * t226 - 0.24e2 * t371 * t372 * t138 * t358 + 0.96e2 * t160 * t163 * t250 * params.gamma * t134 * t373 + 0.288e3 * t88 * t148 * t250 * t374 + 0.64e2 * t269 * t251 * t222 * t202 - 0.32e2 / 0.3e1 * t164 * t154 * t134 * t358 - 0.64e2 / 0.3e1 * t269 * t154 * t222 * t226 - 0.512e3 / 0.9e1 * t431 * t154 * t354 * t138 + 0.2e1 * t91 * t154 * t75 * t624 - 0.960e3 * t396 * t156 - 0.32e2 * t149 * t392
  t731 = t266 ** 2
  t749 = -0.384e3 * t149 * t367 - 0.120e3 * t91 / t249 / t92 * params.gamma * t75 * t572 - 0.18e2 * t91 * t251 * t75 * t582 - 0.720e3 * t241 * t253 + 0.496e3 / 0.3e1 * t246 * t384 + 0.7808e4 / 0.27e2 * t423 * t388 + 0.240e3 * t241 * t261 - 0.27584e5 / 0.27e2 * t420 * t257 - 0.128e3 * t164 * t365 * t134 * t321 - 0.496e3 * t246 * t380 - 0.64e2 * t564 - 0.36e2 * t579 + 0.8e1 * t588 + 0.20944e5 / 0.81e2 * t597 * t79 - 0.2176e4 / 0.9e1 * t427 * t616 * t432 + 0.1280e4 / 0.27e2 * params.beta * t426 * s0 / t66 / t731 / r0 * t94 * t620 - 0.840e3 * t88 / t266 * t95 - 0.99160e5 / 0.81e2 * t160 * t603 * t165 + 0.46000e5 / 0.81e2 * t265 * t609 * t270
  t754 = -0.41888e5 / 0.729e3 * t63 * t64 * t540 * t79 - 0.9856e4 / 0.243e3 * t63 * t64 * t301 * t93 * t138 - 0.704e3 / 0.27e2 * t63 * t64 * t191 * t153 * t202 + 0.352e3 / 0.27e2 * t63 * t64 * t306 * t226 - 0.128e3 / 0.9e1 * t63 * t64 * t120 * t250 * t321 + 0.128e3 / 0.9e1 * t327 * t564 - 0.64e2 / 0.27e2 * t63 * t64 * t196 * t358 - 0.16e2 / 0.3e1 * t63 * t64 * t69 * t364 * t572 + 0.8e1 * t327 * t579 - 0.4e1 / 0.3e1 * t63 * t64 * t201 * t582 - 0.16e2 / 0.9e1 * t327 * t588 + 0.2e1 / 0.9e1 * t63 * t64 * t125 * t624 - 0.2e1 / 0.9e1 * t84 * t62 * (t691 + t749)
  t758 = t19 ** 2
  t761 = t30 ** 2
  t767 = t41 ** 2
  t776 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t777 = f.my_piecewise5(t10, 0, t14, 0, t776)
  t781 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t758 * t761 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t767 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t777)
  t825 = 0.1e1 / t111 / t36
  t830 = -0.3e1 / 0.8e1 * t5 * t299 * t754 - 0.3e1 / 0.8e1 * t5 * t781 * t54 * t101 - 0.3e1 / 0.2e1 * t5 * t55 * t172 - 0.3e1 / 0.2e1 * t5 * t113 * t172 - 0.9e1 / 0.4e1 * t5 * t117 * t277 + t5 * t181 * t172 - 0.3e1 / 0.2e1 * t5 * t185 * t277 - 0.3e1 / 0.2e1 * t5 * t189 * t440 - 0.5e1 / 0.9e1 * t5 * t287 * t172 + t5 * t291 * t277 / 0.2e1 - t5 * t295 * t440 / 0.2e1 - t5 * t53 * t112 * t101 / 0.2e1 + t5 * t110 * t180 * t101 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t178 * t286 * t101 + 0.10e2 / 0.27e2 * t5 * t284 * t825 * t101
  t831 = f.my_piecewise3(t1, 0, t830)
  t832 = t449 ** 2
  t835 = t457 ** 2
  t841 = t464 ** 2
  t847 = f.my_piecewise5(t14, 0, t10, 0, -t776)
  t851 = f.my_piecewise3(t450, 0, 0.40e2 / 0.81e2 / t452 / t832 * t835 - 0.16e2 / 0.9e1 * t454 * t457 * t464 + 0.4e1 / 0.3e1 * t461 * t841 + 0.16e2 / 0.9e1 * t462 * t468 + 0.4e1 / 0.3e1 * t451 * t847)
  t873 = f.my_piecewise3(t447, 0, -0.3e1 / 0.8e1 * t5 * t851 * t54 * t509 - t5 * t472 * t112 * t509 / 0.2e1 + t5 * t518 * t180 * t509 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t525 * t286 * t509 + 0.10e2 / 0.27e2 * t5 * t531 * t825 * t509)
  d1111 = 0.4e1 * t445 + 0.4e1 * t537 + t6 * (t831 + t873)

  res = {'v4rho4': d1111}
  return res
