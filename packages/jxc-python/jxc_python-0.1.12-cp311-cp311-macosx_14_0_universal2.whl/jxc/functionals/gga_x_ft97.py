"""Generated from gga_x_ft97.mpl."""

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
  params_beta0_raw = params.beta0
  if isinstance(params_beta0_raw, (str, bytes, dict)):
    params_beta0 = params_beta0_raw
  else:
    try:
      params_beta0_seq = list(params_beta0_raw)
    except TypeError:
      params_beta0 = params_beta0_raw
    else:
      params_beta0_seq = np.asarray(params_beta0_seq, dtype=np.float64)
      params_beta0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta0_seq))
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))

  ft97_beta = lambda rs, z, xs: params_beta0 + params_beta1 * f.sigma_spin(rs, z, xs) / (params_beta2 + f.sigma_spin(rs, z, xs))

  ft97_fx = lambda rs, z, xs: 1 + ft97_beta(rs, z, xs) * xs ** 2 / (X_FACTOR_C * jnp.sqrt(1 + 9 * xs ** 2 * ft97_beta(rs, z, xs) ** 2 * jnp.arcsinh(xs ** 2) ** 2))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, ft97_fx, rs, zeta, xs0, xs1)

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
  params_beta0_raw = params.beta0
  if isinstance(params_beta0_raw, (str, bytes, dict)):
    params_beta0 = params_beta0_raw
  else:
    try:
      params_beta0_seq = list(params_beta0_raw)
    except TypeError:
      params_beta0 = params_beta0_raw
    else:
      params_beta0_seq = np.asarray(params_beta0_seq, dtype=np.float64)
      params_beta0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta0_seq))
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))

  ft97_beta = lambda rs, z, xs: params_beta0 + params_beta1 * f.sigma_spin(rs, z, xs) / (params_beta2 + f.sigma_spin(rs, z, xs))

  ft97_fx = lambda rs, z, xs: 1 + ft97_beta(rs, z, xs) * xs ** 2 / (X_FACTOR_C * jnp.sqrt(1 + 9 * xs ** 2 * ft97_beta(rs, z, xs) ** 2 * jnp.arcsinh(xs ** 2) ** 2))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, ft97_fx, rs, zeta, xs0, xs1)

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
  params_beta0_raw = params.beta0
  if isinstance(params_beta0_raw, (str, bytes, dict)):
    params_beta0 = params_beta0_raw
  else:
    try:
      params_beta0_seq = list(params_beta0_raw)
    except TypeError:
      params_beta0 = params_beta0_raw
    else:
      params_beta0_seq = np.asarray(params_beta0_seq, dtype=np.float64)
      params_beta0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta0_seq))
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))

  ft97_beta = lambda rs, z, xs: params_beta0 + params_beta1 * f.sigma_spin(rs, z, xs) / (params_beta2 + f.sigma_spin(rs, z, xs))

  ft97_fx = lambda rs, z, xs: 1 + ft97_beta(rs, z, xs) * xs ** 2 / (X_FACTOR_C * jnp.sqrt(1 + 9 * xs ** 2 * ft97_beta(rs, z, xs) ** 2 * jnp.arcsinh(xs ** 2) ** 2))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, ft97_fx, rs, zeta, xs0, xs1)

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
  t28 = params.beta1 * s0
  t29 = r0 ** 2
  t30 = r0 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t33 = 0.1e1 / t31 / t29
  t34 = 2 ** (0.1e1 / 0.3e1)
  t36 = t28 * t33 * t34
  t37 = t19 ** 2
  t38 = t6 ** 2
  t39 = t37 * t38
  t40 = t19 * t6
  t41 = t40 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t43 = s0 * t33
  t44 = t43 * t34
  t45 = t39 * t42
  t48 = params.beta2 + t44 * t45 / 0.8e1
  t49 = 0.1e1 / t48
  t50 = t42 * t49
  t51 = t39 * t50
  t54 = params.beta0 + t36 * t51 / 0.8e1
  t55 = t54 * s0
  t57 = t2 ** 2
  t59 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t60 = 0.1e1 / t59
  t61 = t57 * t60
  t62 = 4 ** (0.1e1 / 0.3e1)
  t63 = t54 ** 2
  t64 = jnp.arcsinh(t43)
  t65 = t64 ** 2
  t66 = t63 * t65
  t69 = 0.9e1 * t43 * t66 + 0.1e1
  t70 = jnp.sqrt(t69)
  t71 = 0.1e1 / t70
  t73 = t61 * t62 * t71
  t76 = 0.1e1 + 0.2e1 / 0.9e1 * t55 * t33 * t73
  t80 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t76)
  t81 = r1 <= f.p.dens_threshold
  t82 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t83 = 0.1e1 + t82
  t84 = t83 <= f.p.zeta_threshold
  t85 = t83 ** (0.1e1 / 0.3e1)
  t87 = f.my_piecewise3(t84, t22, t85 * t83)
  t88 = t87 * t26
  t89 = params.beta1 * s2
  t90 = r1 ** 2
  t91 = r1 ** (0.1e1 / 0.3e1)
  t92 = t91 ** 2
  t94 = 0.1e1 / t92 / t90
  t96 = t89 * t94 * t34
  t97 = t83 ** 2
  t98 = t97 * t38
  t99 = t83 * t6
  t100 = t99 ** (0.1e1 / 0.3e1)
  t101 = t100 ** 2
  t102 = s2 * t94
  t103 = t102 * t34
  t104 = t98 * t101
  t107 = params.beta2 + t103 * t104 / 0.8e1
  t108 = 0.1e1 / t107
  t109 = t101 * t108
  t110 = t98 * t109
  t113 = params.beta0 + t96 * t110 / 0.8e1
  t114 = t113 * s2
  t116 = t113 ** 2
  t117 = jnp.arcsinh(t102)
  t118 = t117 ** 2
  t119 = t116 * t118
  t122 = 0.9e1 * t102 * t119 + 0.1e1
  t123 = jnp.sqrt(t122)
  t124 = 0.1e1 / t123
  t126 = t61 * t62 * t124
  t129 = 0.1e1 + 0.2e1 / 0.9e1 * t114 * t94 * t126
  t133 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t88 * t129)
  t135 = t16 / t38
  t136 = t7 - t135
  t137 = f.my_piecewise5(t10, 0, t14, 0, t136)
  t140 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t137)
  t145 = t26 ** 2
  t146 = 0.1e1 / t145
  t150 = t5 * t25 * t146 * t76 / 0.8e1
  t153 = 0.1e1 / t31 / t29 / r0
  t158 = t19 * t38
  t163 = t37 * t6
  t166 = t36 * t163 * t50 / 0.4e1
  t167 = 0.1e1 / t41
  t168 = t167 * t49
  t170 = t137 * t6 + t18 + 0.1e1
  t175 = t48 ** 2
  t176 = 0.1e1 / t175
  t177 = t42 * t176
  t178 = s0 * t153
  t188 = t44 * t163 * t42 / 0.4e1
  t198 = -t28 * t153 * t34 * t51 / 0.3e1 + t36 * t158 * t50 * t137 / 0.4e1 + t166 + t36 * t39 * t168 * t170 / 0.12e2 - t36 * t39 * t177 * (-t178 * t34 * t45 / 0.3e1 + t44 * t158 * t42 * t137 / 0.4e1 + t188 + t44 * t39 * t167 * t170 / 0.12e2) / 0.8e1
  t207 = t55 * t33 * t57
  t208 = t60 * t62
  t210 = 0.1e1 / t70 / t69
  t213 = t54 * t65
  t217 = s0 ** 2
  t218 = t29 ** 2
  t226 = 0.1e1 / t30 / t218 / r0
  t229 = jnp.sqrt(t217 * t226 + 0.1e1)
  t231 = t63 * t64 / t229
  t244 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t140 * t26 * t76 - t150 - 0.3e1 / 0.8e1 * t5 * t27 * (0.2e1 / 0.9e1 * t198 * s0 * t33 * t73 - 0.16e2 / 0.27e2 * t55 * t153 * t73 - t207 * t208 * t210 * (-0.24e2 * t178 * t66 + 0.18e2 * t43 * t213 * t198 - 0.48e2 * t217 / t30 / t218 / t29 * t231) / 0.9e1))
  t246 = f.my_piecewise5(t14, 0, t10, 0, -t136)
  t249 = f.my_piecewise3(t84, 0, 0.4e1 / 0.3e1 * t85 * t246)
  t257 = t5 * t87 * t146 * t129 / 0.8e1
  t258 = t83 * t38
  t263 = t97 * t6
  t266 = t96 * t263 * t109 / 0.4e1
  t267 = 0.1e1 / t100
  t268 = t267 * t108
  t270 = t246 * t6 + t82 + 0.1e1
  t275 = t107 ** 2
  t276 = 0.1e1 / t275
  t277 = t101 * t276
  t284 = t103 * t263 * t101 / 0.4e1
  t294 = t96 * t258 * t109 * t246 / 0.4e1 + t266 + t96 * t98 * t268 * t270 / 0.12e2 - t96 * t98 * t277 * (t103 * t258 * t101 * t246 / 0.4e1 + t284 + t103 * t98 * t267 * t270 / 0.12e2) / 0.8e1
  t299 = s2 ** 2
  t301 = t90 ** 2
  t304 = 0.1e1 / t91 / t301 / r1
  t308 = 0.1e1 / t123 / t122
  t319 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t249 * t26 * t129 - t257 - 0.3e1 / 0.8e1 * t5 * t88 * (0.2e1 / 0.9e1 * t294 * s2 * t94 * t126 - 0.2e1 * t116 * t299 * t304 * t57 * t208 * t308 * t118 * t294))
  vrho_0_ = t80 + t133 + t6 * (t244 + t319)
  t322 = -t7 - t135
  t323 = f.my_piecewise5(t10, 0, t14, 0, t322)
  t326 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t323)
  t336 = t323 * t6 + t18 + 0.1e1
  t354 = t36 * t158 * t50 * t323 / 0.4e1 + t166 + t36 * t39 * t168 * t336 / 0.12e2 - t36 * t39 * t177 * (t44 * t158 * t42 * t323 / 0.4e1 + t188 + t44 * t39 * t167 * t336 / 0.12e2) / 0.8e1
  t372 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t326 * t26 * t76 - t150 - 0.3e1 / 0.8e1 * t5 * t27 * (0.2e1 / 0.9e1 * t354 * s0 * t33 * t73 - 0.2e1 * t63 * t217 * t226 * t57 * t208 * t210 * t65 * t354))
  t374 = f.my_piecewise5(t14, 0, t10, 0, -t322)
  t377 = f.my_piecewise3(t84, 0, 0.4e1 / 0.3e1 * t85 * t374)
  t384 = 0.1e1 / t92 / t90 / r1
  t394 = t374 * t6 + t82 + 0.1e1
  t399 = s2 * t384
  t416 = -t89 * t384 * t34 * t110 / 0.3e1 + t96 * t258 * t109 * t374 / 0.4e1 + t266 + t96 * t98 * t268 * t394 / 0.12e2 - t96 * t98 * t277 * (-t399 * t34 * t104 / 0.3e1 + t103 * t258 * t101 * t374 / 0.4e1 + t284 + t103 * t98 * t267 * t394 / 0.12e2) / 0.8e1
  t425 = t114 * t94 * t57
  t428 = t113 * t118
  t439 = jnp.sqrt(t299 * t304 + 0.1e1)
  t441 = t116 * t117 / t439
  t454 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t377 * t26 * t129 - t257 - 0.3e1 / 0.8e1 * t5 * t88 * (0.2e1 / 0.9e1 * t416 * s2 * t94 * t126 - 0.16e2 / 0.27e2 * t114 * t384 * t126 - t425 * t208 * t308 * (-0.24e2 * t399 * t119 + 0.18e2 * t102 * t428 * t416 - 0.48e2 * t299 / t91 / t301 / t90 * t441) / 0.9e1))
  vrho_1_ = t80 + t133 + t6 * (t372 + t454)
  t461 = t34 ** 2
  t464 = t37 ** 2
  t465 = t38 ** 2
  t472 = params.beta1 * t33 * t34 * t51 / 0.8e1 - t28 * t226 * t461 * t464 * t465 * t41 * t40 * t176 / 0.64e2
  t500 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.2e1 / 0.9e1 * t472 * s0 * t33 * t73 + 0.2e1 / 0.9e1 * t54 * t33 * t57 * t208 * t71 - t207 * t208 * t210 * (0.18e2 * s0 * t226 * t231 + 0.18e2 * t43 * t213 * t472 + 0.9e1 * t33 * t63 * t65) / 0.9e1))
  vsigma_0_ = t6 * t500
  vsigma_1_ = 0.0e0
  t507 = t97 ** 2
  t514 = params.beta1 * t94 * t34 * t110 / 0.8e1 - t89 * t304 * t461 * t507 * t465 * t100 * t99 * t276 / 0.64e2
  t542 = f.my_piecewise3(t81, 0, -0.3e1 / 0.8e1 * t5 * t88 * (0.2e1 / 0.9e1 * t514 * s2 * t94 * t126 + 0.2e1 / 0.9e1 * t113 * t94 * t57 * t208 * t124 - t425 * t208 * t308 * (0.18e2 * s2 * t304 * t441 + 0.18e2 * t102 * t428 * t514 + 0.9e1 * t94 * t116 * t118) / 0.9e1))
  vsigma_2_ = t6 * t542
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
  params_beta0_raw = params.beta0
  if isinstance(params_beta0_raw, (str, bytes, dict)):
    params_beta0 = params_beta0_raw
  else:
    try:
      params_beta0_seq = list(params_beta0_raw)
    except TypeError:
      params_beta0 = params_beta0_raw
    else:
      params_beta0_seq = np.asarray(params_beta0_seq, dtype=np.float64)
      params_beta0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta0_seq))
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))

  ft97_beta = lambda rs, z, xs: params_beta0 + params_beta1 * f.sigma_spin(rs, z, xs) / (params_beta2 + f.sigma_spin(rs, z, xs))

  ft97_fx = lambda rs, z, xs: 1 + ft97_beta(rs, z, xs) * xs ** 2 / (X_FACTOR_C * jnp.sqrt(1 + 9 * xs ** 2 * ft97_beta(rs, z, xs) ** 2 * jnp.arcsinh(xs ** 2) ** 2))

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, ft97_fx, rs, zeta, xs0, xs1)

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
  t20 = params.beta1 * s0
  t21 = t18 ** 2
  t22 = 0.1e1 / t21
  t23 = t20 * t22
  t24 = t11 ** 2
  t25 = t11 * r0
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = t24 * t27
  t29 = s0 * t22
  t32 = params.beta2 + t29 * t28 / 0.4e1
  t33 = 0.1e1 / t32
  t34 = t28 * t33
  t37 = params.beta0 + t23 * t34 / 0.4e1
  t38 = t37 * s0
  t39 = 2 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t41 = r0 ** 2
  t43 = 0.1e1 / t21 / t41
  t44 = t40 * t43
  t45 = t38 * t44
  t46 = t3 ** 2
  t48 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t50 = t46 / t48
  t51 = 4 ** (0.1e1 / 0.3e1)
  t52 = s0 * t40
  t53 = t37 ** 2
  t55 = t52 * t43
  t56 = jnp.arcsinh(t55)
  t57 = t56 ** 2
  t61 = 0.9e1 * t52 * t43 * t53 * t57 + 0.1e1
  t62 = jnp.sqrt(t61)
  t65 = t50 * t51 / t62
  t68 = 0.1e1 + 0.2e1 / 0.9e1 * t45 * t65
  t72 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t68)
  t78 = 0.1e1 / t21 / r0
  t84 = t24 * t11 / t26
  t88 = t32 ** 2
  t89 = 0.1e1 / t88
  t99 = -t20 * t78 * t34 / 0.6e1 + t23 * t84 * t33 / 0.6e1 - t23 * t28 * t89 * (-s0 * t78 * t28 / 0.6e1 + t29 * t84 / 0.6e1) / 0.4e1
  t106 = 0.1e1 / t21 / t41 / r0
  t113 = t51 / t62 / t61
  t118 = t37 * t57
  t122 = s0 ** 2
  t123 = t122 * t39
  t124 = t41 ** 2
  t132 = 0.1e1 / t18 / t124 / r0
  t136 = jnp.sqrt(0.2e1 * t123 * t132 + 0.1e1)
  t138 = t53 * t56 / t136
  t151 = f.my_piecewise3(t2, 0, -t6 * t17 * t22 * t68 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (0.2e1 / 0.9e1 * t99 * s0 * t44 * t65 - 0.16e2 / 0.27e2 * t38 * t40 * t106 * t65 - t45 * t50 * t113 * (-0.24e2 * t52 * t106 * t53 * t57 + 0.18e2 * t55 * t118 * t99 - 0.96e2 * t123 / t18 / t124 / t41 * t138) / 0.9e1))
  vrho_0_ = 0.2e1 * r0 * t151 + 0.2e1 * t72
  t160 = t24 ** 2
  t166 = params.beta1 * t22 * t34 / 0.4e1 - t20 / t18 / r0 * t160 * t26 * t25 * t89 / 0.16e2
  t194 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.2e1 / 0.9e1 * t166 * s0 * t44 * t65 + 0.2e1 / 0.9e1 * t37 * t40 * t43 * t65 - t45 * t50 * t113 * (0.36e2 * s0 * t39 * t132 * t138 + 0.18e2 * t55 * t118 * t166 + 0.9e1 * t44 * t53 * t57) / 0.9e1))
  vsigma_0_ = 0.2e1 * r0 * t194
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
  t20 = 0.1e1 / t19
  t21 = t17 * t20
  t22 = params.beta1 * s0
  t23 = t22 * t20
  t24 = t11 ** 2
  t25 = t11 * r0
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = t24 * t27
  t29 = s0 * t20
  t32 = params.beta2 + t29 * t28 / 0.4e1
  t33 = 0.1e1 / t32
  t34 = t28 * t33
  t37 = params.beta0 + t23 * t34 / 0.4e1
  t38 = t37 * s0
  t39 = 2 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t41 = r0 ** 2
  t43 = 0.1e1 / t19 / t41
  t44 = t40 * t43
  t45 = t38 * t44
  t46 = t3 ** 2
  t48 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t49 = 0.1e1 / t48
  t50 = t46 * t49
  t51 = 4 ** (0.1e1 / 0.3e1)
  t52 = s0 * t40
  t53 = t37 ** 2
  t55 = t52 * t43
  t56 = jnp.arcsinh(t55)
  t57 = t56 ** 2
  t61 = 0.9e1 * t52 * t43 * t53 * t57 + 0.1e1
  t62 = jnp.sqrt(t61)
  t65 = t50 * t51 / t62
  t68 = 0.1e1 + 0.2e1 / 0.9e1 * t45 * t65
  t72 = t17 * t18
  t74 = 0.1e1 / t19 / r0
  t75 = t22 * t74
  t80 = t24 * t11 / t26
  t81 = t80 * t33
  t84 = t32 ** 2
  t85 = 0.1e1 / t84
  t86 = s0 * t74
  t90 = -t86 * t28 / 0.6e1 + t29 * t80 / 0.6e1
  t91 = t85 * t90
  t92 = t28 * t91
  t95 = -t75 * t34 / 0.6e1 + t23 * t81 / 0.6e1 - t23 * t92 / 0.4e1
  t96 = t95 * s0
  t97 = t96 * t44
  t100 = t41 * r0
  t102 = 0.1e1 / t19 / t100
  t103 = t40 * t102
  t104 = t38 * t103
  t108 = 0.1e1 / t62 / t61
  t109 = t51 * t108
  t114 = t37 * t57
  t115 = t114 * t95
  t118 = s0 ** 2
  t119 = t118 * t39
  t120 = t41 ** 2
  t123 = 0.1e1 / t18 / t120 / t41
  t124 = t119 * t123
  t125 = t53 * t56
  t128 = 0.1e1 / t18 / t120 / r0
  t131 = 0.2e1 * t119 * t128 + 0.1e1
  t132 = jnp.sqrt(t131)
  t133 = 0.1e1 / t132
  t134 = t125 * t133
  t137 = -0.24e2 * t52 * t102 * t53 * t57 + 0.18e2 * t55 * t115 - 0.96e2 * t124 * t134
  t139 = t50 * t109 * t137
  t142 = 0.2e1 / 0.9e1 * t97 * t65 - 0.16e2 / 0.27e2 * t104 * t65 - t45 * t139 / 0.9e1
  t147 = f.my_piecewise3(t2, 0, -t6 * t21 * t68 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t72 * t142)
  t163 = t24 ** 2
  t164 = t26 * t25
  t166 = t163 / t164
  t174 = 0.1e1 / t84 / t32
  t175 = t90 ** 2
  t192 = 0.5e1 / 0.18e2 * t22 * t43 * t34 - 0.2e1 / 0.9e1 * t75 * t81 + t75 * t92 / 0.3e1 - t23 * t166 * t33 / 0.18e2 - t23 * t80 * t91 / 0.3e1 + t23 * t28 * t174 * t175 / 0.2e1 - t23 * t28 * t85 * (0.5e1 / 0.18e2 * s0 * t43 * t28 - 0.2e1 / 0.9e1 * t86 * t80 - t29 * t166 / 0.18e2) / 0.4e1
  t203 = 0.1e1 / t19 / t120
  t210 = t61 ** 2
  t212 = 0.1e1 / t62 / t210
  t213 = t51 * t212
  t214 = t137 ** 2
  t223 = t52 * t102
  t232 = t95 ** 2
  t237 = t37 * t56
  t239 = t237 * t95 * t133
  t245 = t118 * s0
  t246 = t120 ** 2
  t247 = t246 * t41
  t251 = t53 / t131
  t254 = t118 ** 2
  t262 = t125 / t132 / t131
  t275 = f.my_piecewise3(t2, 0, t6 * t17 * t74 * t68 / 0.12e2 - t6 * t21 * t142 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t72 * (0.2e1 / 0.9e1 * t192 * s0 * t44 * t65 - 0.32e2 / 0.27e2 * t96 * t103 * t65 - 0.2e1 / 0.9e1 * t97 * t139 + 0.176e3 / 0.81e2 * t38 * t40 * t203 * t65 + 0.16e2 / 0.27e2 * t104 * t139 + t45 * t50 * t213 * t214 / 0.6e1 - t45 * t50 * t109 * (0.88e2 * t52 * t203 * t53 * t57 - 0.96e2 * t223 * t115 + 0.864e3 * t119 / t18 / t120 / t100 * t134 + 0.18e2 * t52 * t43 * t232 * t57 - 0.384e3 * t124 * t239 + 0.18e2 * t55 * t114 * t192 + 0.512e3 * t245 / t247 * t251 - 0.512e3 * t254 * t40 / t19 / t246 / t120 * t262) / 0.9e1))
  v2rho2_0_ = 0.2e1 * r0 * t275 + 0.4e1 * t147
  t278 = params.beta1 * t20
  t282 = 0.1e1 / t18 / r0
  t283 = t22 * t282
  t284 = t163 * t164
  t285 = t284 * t85
  t288 = t278 * t34 / 0.4e1 - t283 * t285 / 0.16e2
  t289 = t288 * s0
  t290 = t289 * t44
  t293 = t37 * t40
  t297 = t53 * t57
  t300 = t114 * t288
  t304 = s0 * t39 * t128
  t307 = 0.36e2 * t304 * t134 + 0.9e1 * t44 * t297 + 0.18e2 * t55 * t300
  t309 = t50 * t109 * t307
  t312 = 0.2e1 / 0.9e1 * t290 * t65 + 0.2e1 / 0.9e1 * t293 * t43 * t65 - t45 * t309 / 0.9e1
  t316 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t72 * t312)
  t344 = -params.beta1 * t74 * t34 / 0.6e1 + t278 * t81 / 0.6e1 - t278 * t24 * t27 * t85 * t90 / 0.4e1 + t22 / t18 / t41 * t285 / 0.12e2 - t283 * t163 * t11 * t26 * t85 / 0.12e2 + t283 * t284 * t174 * t90 / 0.8e1
  t362 = t293 * t43 * t46
  t363 = t49 * t51
  t396 = t237 * t288 * t133
  t426 = f.my_piecewise3(t2, 0, -t6 * t21 * t312 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t72 * (0.2e1 / 0.9e1 * t344 * s0 * t44 * t65 - 0.16e2 / 0.27e2 * t289 * t103 * t65 - t290 * t139 / 0.9e1 + 0.2e1 / 0.9e1 * t95 * t40 * t43 * t65 - 0.16e2 / 0.27e2 * t293 * t102 * t65 - t362 * t363 * t108 * t137 / 0.9e1 - t97 * t309 / 0.9e1 + 0.8e1 / 0.27e2 * t104 * t309 + t38 * t44 * t46 * t363 * t212 * t307 * t137 / 0.6e1 - t45 * t50 * t109 * (-0.24e2 * t103 * t297 + 0.18e2 * t44 * t115 - 0.288e3 * t39 * t123 * t53 * t56 * s0 * t133 - 0.48e2 * t223 * t300 + 0.18e2 * t55 * t95 * t57 * t288 - 0.192e3 * t124 * t396 + 0.18e2 * t55 * t114 * t344 + 0.72e2 * t304 * t239 - 0.192e3 * t118 / t246 / r0 * t251 + 0.192e3 * t245 * t40 / t19 / t246 / t100 * t262) / 0.9e1))
  v2rhosigma_0_ = 0.2e1 * r0 * t426 + 0.2e1 * t316
  t432 = t163 ** 2
  t436 = -params.beta1 * t282 * t285 / 0.8e1 + t22 * t432 * t174 / 0.32e2
  t451 = t307 ** 2
  t461 = t288 ** 2
  t490 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t72 * (0.2e1 / 0.9e1 * t436 * s0 * t44 * t65 + 0.4e1 / 0.9e1 * t288 * t40 * t43 * t65 - 0.2e1 / 0.9e1 * t290 * t309 - 0.2e1 / 0.9e1 * t362 * t363 * t108 * t307 + t45 * t50 * t213 * t451 / 0.6e1 - t45 * t50 * t109 * (0.36e2 * t44 * t300 + 0.72e2 * t39 * t128 * t134 + 0.18e2 * t52 * t43 * t461 * t57 + 0.144e3 * t304 * t396 + 0.18e2 * t55 * t114 * t436 + 0.72e2 * s0 / t246 * t251 - 0.72e2 * t118 * t40 / t19 / t247 * t262) / 0.9e1))
  v2sigma2_0_ = 0.2e1 * r0 * t490
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
  t21 = 0.1e1 / t19 / r0
  t22 = t17 * t21
  t23 = params.beta1 * s0
  t24 = 0.1e1 / t19
  t25 = t23 * t24
  t26 = t11 ** 2
  t27 = t11 * r0
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = t26 * t29
  t31 = s0 * t24
  t34 = params.beta2 + t31 * t30 / 0.4e1
  t35 = 0.1e1 / t34
  t36 = t30 * t35
  t39 = params.beta0 + t25 * t36 / 0.4e1
  t40 = t39 * s0
  t41 = 2 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t43 = r0 ** 2
  t45 = 0.1e1 / t19 / t43
  t46 = t42 * t45
  t47 = t40 * t46
  t48 = t3 ** 2
  t50 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t51 = 0.1e1 / t50
  t52 = t48 * t51
  t53 = 4 ** (0.1e1 / 0.3e1)
  t54 = s0 * t42
  t55 = t39 ** 2
  t57 = t54 * t45
  t58 = jnp.asinh(t57)
  t59 = t58 ** 2
  t63 = 0.9e1 * t54 * t45 * t55 * t59 + 0.1e1
  t64 = jnp.sqrt(t63)
  t67 = t52 * t53 / t64
  t70 = 0.1e1 + 0.2e1 / 0.9e1 * t47 * t67
  t74 = t17 * t24
  t75 = t23 * t21
  t80 = t26 * t11 / t28
  t81 = t80 * t35
  t84 = t34 ** 2
  t85 = 0.1e1 / t84
  t86 = s0 * t21
  t90 = -t86 * t30 / 0.6e1 + t31 * t80 / 0.6e1
  t91 = t85 * t90
  t92 = t30 * t91
  t95 = -t75 * t36 / 0.6e1 + t25 * t81 / 0.6e1 - t25 * t92 / 0.4e1
  t96 = t95 * s0
  t97 = t96 * t46
  t100 = t43 * r0
  t102 = 0.1e1 / t19 / t100
  t103 = t42 * t102
  t104 = t40 * t103
  t109 = t53 / t64 / t63
  t114 = t39 * t59
  t115 = t114 * t95
  t118 = s0 ** 2
  t119 = t118 * t41
  t120 = t43 ** 2
  t124 = t119 / t18 / t120 / t43
  t125 = t55 * t58
  t126 = t120 * r0
  t131 = 0.1e1 + 0.2e1 * t119 / t18 / t126
  t132 = jnp.sqrt(t131)
  t133 = 0.1e1 / t132
  t134 = t125 * t133
  t137 = -0.24e2 * t54 * t102 * t55 * t59 + 0.18e2 * t57 * t115 - 0.96e2 * t124 * t134
  t139 = t52 * t109 * t137
  t142 = 0.2e1 / 0.9e1 * t97 * t67 - 0.16e2 / 0.27e2 * t104 * t67 - t47 * t139 / 0.9e1
  t146 = t17 * t18
  t147 = t23 * t45
  t154 = t26 ** 2
  t157 = t154 / t28 / t27
  t158 = t157 * t35
  t161 = t80 * t91
  t165 = 0.1e1 / t84 / t34
  t166 = t90 ** 2
  t167 = t165 * t166
  t168 = t30 * t167
  t171 = s0 * t45
  t178 = 0.5e1 / 0.18e2 * t171 * t30 - 0.2e1 / 0.9e1 * t86 * t80 - t31 * t157 / 0.18e2
  t179 = t85 * t178
  t180 = t30 * t179
  t183 = 0.5e1 / 0.18e2 * t147 * t36 - 0.2e1 / 0.9e1 * t75 * t81 + t75 * t92 / 0.3e1 - t25 * t158 / 0.18e2 - t25 * t161 / 0.3e1 + t25 * t168 / 0.2e1 - t25 * t180 / 0.4e1
  t184 = t183 * s0
  t185 = t184 * t46
  t188 = t96 * t103
  t194 = 0.1e1 / t19 / t120
  t195 = t42 * t194
  t196 = t40 * t195
  t201 = t63 ** 2
  t203 = 0.1e1 / t64 / t201
  t205 = t137 ** 2
  t207 = t52 * t53 * t203 * t205
  t214 = t54 * t102
  t220 = t119 / t18 / t120 / t100
  t223 = t95 ** 2
  t228 = t39 * t58
  t230 = t228 * t95 * t133
  t233 = t114 * t183
  t236 = t118 * s0
  t237 = t120 ** 2
  t240 = t236 / t237 / t43
  t241 = 0.1e1 / t131
  t242 = t55 * t241
  t245 = t118 ** 2
  t246 = t245 * t42
  t250 = t246 / t19 / t237 / t120
  t252 = 0.1e1 / t132 / t131
  t253 = t125 * t252
  t256 = 0.88e2 * t54 * t194 * t55 * t59 + 0.18e2 * t54 * t45 * t223 * t59 - 0.96e2 * t214 * t115 - 0.384e3 * t124 * t230 + 0.864e3 * t220 * t134 + 0.18e2 * t57 * t233 + 0.512e3 * t240 * t242 - 0.512e3 * t250 * t253
  t258 = t52 * t109 * t256
  t261 = 0.2e1 / 0.9e1 * t185 * t67 - 0.32e2 / 0.27e2 * t188 * t67 - 0.2e1 / 0.9e1 * t97 * t139 + 0.176e3 / 0.81e2 * t196 * t67 + 0.16e2 / 0.27e2 * t104 * t139 + t47 * t207 / 0.6e1 - t47 * t258 / 0.9e1
  t266 = f.my_piecewise3(t2, 0, t6 * t22 * t70 / 0.12e2 - t6 * t74 * t142 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t146 * t261)
  t281 = t84 ** 2
  t309 = t154 * t11 / t28 / t26 / t43
  t336 = -t75 * t168 + t25 * t80 * t167 - 0.3e1 / 0.2e1 * t25 * t30 / t281 * t166 * t90 + 0.3e1 / 0.2e1 * t23 * t24 * t26 * t29 * t165 * t90 * t178 - t25 * t80 * t179 / 0.2e1 - t25 * t30 * t85 * (-0.20e2 / 0.27e2 * s0 * t102 * t30 + 0.5e1 / 0.9e1 * t171 * t80 + t86 * t157 / 0.9e1 + 0.2e1 / 0.27e2 * t31 * t309) / 0.4e1 - 0.20e2 / 0.27e2 * t23 * t102 * t36 + 0.5e1 / 0.9e1 * t147 * t81 - 0.5e1 / 0.6e1 * t147 * t92 + t75 * t158 / 0.9e1 + 0.2e1 / 0.3e1 * t75 * t161 + t75 * t180 / 0.2e1 + 0.2e1 / 0.27e2 * t25 * t309 * t35 + t25 * t157 * t91 / 0.6e1
  t380 = 0.1e1 / t19 / t126
  t405 = t237 ** 2
  t409 = t131 ** 2
  t438 = 0.33280e5 / 0.3e1 * t246 / t19 / t237 / t126 * t253 + 0.54e2 * t57 * t95 * t59 * t183 - 0.576e3 * t124 * t223 * t58 * t133 + 0.18e2 * t57 * t114 * t336 - 0.1232e4 / 0.3e1 * t54 * t380 * t55 * t59 + 0.528e3 * t54 * t194 * t115 - 0.21824e5 / 0.3e1 * t119 / t18 / t237 * t134 - 0.144e3 * t54 * t102 * t223 * t59 - 0.144e3 * t214 * t233 - 0.9728e4 * t236 / t237 / t100 * t242 + 0.8192e4 * t245 * s0 / t18 / t405 * t55 / t409 * t41 - 0.16384e5 * t245 * t118 / t405 / t100 * t125 / t132 / t409 + 0.3072e4 * t240 * t39 * t241 * t95 + 0.5184e4 * t220 * t230 - 0.576e3 * t124 * t228 * t183 * t133 - 0.3072e4 * t250 * t228 * t95 * t252
  t463 = 0.2e1 / 0.9e1 * t336 * s0 * t46 * t67 - 0.4e1 / 0.3e1 * t104 * t207 - 0.5e1 / 0.12e2 * t47 * t52 * t53 / t64 / t201 / t63 * t205 * t137 + t40 * t46 * t48 * t51 * t53 * t203 * t137 * t256 / 0.2e1 + t97 * t207 / 0.2e1 - t47 * t52 * t109 * t438 / 0.9e1 - t185 * t139 / 0.3e1 + 0.176e3 / 0.27e2 * t96 * t195 * t67 + 0.16e2 / 0.9e1 * t188 * t139 - t97 * t258 / 0.3e1 - 0.2464e4 / 0.243e3 * t40 * t42 * t380 * t67 - 0.88e2 / 0.27e2 * t196 * t139 + 0.8e1 / 0.9e1 * t104 * t258 - 0.16e2 / 0.9e1 * t184 * t103 * t67
  t468 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t45 * t70 + t6 * t22 * t142 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t74 * t261 - 0.3e1 / 0.8e1 * t6 * t146 * t463)
  v3rho3_0_ = 0.2e1 * r0 * t468 + 0.6e1 * t266

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
  t24 = params.beta1 * s0
  t25 = 0.1e1 / t20
  t26 = t24 * t25
  t27 = t11 ** 2
  t28 = t11 * r0
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = t27 * t30
  t32 = s0 * t25
  t35 = params.beta2 + t32 * t31 / 0.4e1
  t36 = 0.1e1 / t35
  t37 = t31 * t36
  t40 = params.beta0 + t26 * t37 / 0.4e1
  t41 = t40 * s0
  t42 = 2 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = t43 * t22
  t45 = t41 * t44
  t46 = t3 ** 2
  t48 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t49 = 0.1e1 / t48
  t50 = t46 * t49
  t51 = 4 ** (0.1e1 / 0.3e1)
  t52 = s0 * t43
  t53 = t40 ** 2
  t55 = t52 * t22
  t56 = jnp.asinh(t55)
  t57 = t56 ** 2
  t61 = 0.9e1 * t52 * t22 * t53 * t57 + 0.1e1
  t62 = jnp.sqrt(t61)
  t65 = t50 * t51 / t62
  t68 = 0.1e1 + 0.2e1 / 0.9e1 * t45 * t65
  t73 = 0.1e1 / t20 / r0
  t74 = t17 * t73
  t75 = t24 * t73
  t78 = t27 * t11
  t79 = 0.1e1 / t29
  t80 = t78 * t79
  t81 = t80 * t36
  t84 = t35 ** 2
  t85 = 0.1e1 / t84
  t86 = s0 * t73
  t90 = -t86 * t31 / 0.6e1 + t32 * t80 / 0.6e1
  t91 = t85 * t90
  t92 = t31 * t91
  t95 = -t75 * t37 / 0.6e1 + t26 * t81 / 0.6e1 - t26 * t92 / 0.4e1
  t96 = t95 * s0
  t97 = t96 * t44
  t100 = t18 * r0
  t102 = 0.1e1 / t20 / t100
  t103 = t43 * t102
  t104 = t41 * t103
  t109 = t51 / t62 / t61
  t114 = t40 * t57
  t115 = t114 * t95
  t118 = s0 ** 2
  t119 = t118 * t42
  t120 = t18 ** 2
  t121 = t120 * t18
  t124 = t119 / t19 / t121
  t125 = t53 * t56
  t126 = t120 * r0
  t131 = 0.1e1 + 0.2e1 * t119 / t19 / t126
  t132 = jnp.sqrt(t131)
  t133 = 0.1e1 / t132
  t134 = t125 * t133
  t137 = -0.24e2 * t52 * t102 * t53 * t57 + 0.18e2 * t55 * t115 - 0.96e2 * t124 * t134
  t139 = t50 * t109 * t137
  t142 = 0.2e1 / 0.9e1 * t97 * t65 - 0.16e2 / 0.27e2 * t104 * t65 - t45 * t139 / 0.9e1
  t146 = t17 * t25
  t147 = t24 * t22
  t154 = t27 ** 2
  t157 = t154 / t29 / t28
  t158 = t157 * t36
  t161 = t80 * t91
  t165 = 0.1e1 / t84 / t35
  t166 = t90 ** 2
  t167 = t165 * t166
  t168 = t31 * t167
  t171 = s0 * t22
  t178 = 0.5e1 / 0.18e2 * t171 * t31 - 0.2e1 / 0.9e1 * t86 * t80 - t32 * t157 / 0.18e2
  t179 = t85 * t178
  t180 = t31 * t179
  t183 = 0.5e1 / 0.18e2 * t147 * t37 - 0.2e1 / 0.9e1 * t75 * t81 + t75 * t92 / 0.3e1 - t26 * t158 / 0.18e2 - t26 * t161 / 0.3e1 + t26 * t168 / 0.2e1 - t26 * t180 / 0.4e1
  t184 = t183 * s0
  t185 = t184 * t44
  t188 = t96 * t103
  t194 = 0.1e1 / t20 / t120
  t195 = t43 * t194
  t196 = t41 * t195
  t201 = t61 ** 2
  t203 = 0.1e1 / t62 / t201
  t204 = t51 * t203
  t205 = t137 ** 2
  t207 = t50 * t204 * t205
  t214 = t52 * t102
  t220 = t119 / t19 / t120 / t100
  t223 = t95 ** 2
  t228 = t40 * t56
  t230 = t228 * t95 * t133
  t233 = t114 * t183
  t236 = t118 * s0
  t237 = t120 ** 2
  t240 = t236 / t237 / t18
  t241 = 0.1e1 / t131
  t242 = t53 * t241
  t245 = t118 ** 2
  t246 = t245 * t43
  t247 = t237 * t120
  t250 = t246 / t20 / t247
  t252 = 0.1e1 / t132 / t131
  t253 = t125 * t252
  t256 = 0.88e2 * t52 * t194 * t53 * t57 + 0.18e2 * t52 * t22 * t223 * t57 - 0.96e2 * t214 * t115 - 0.384e3 * t124 * t230 + 0.864e3 * t220 * t134 + 0.18e2 * t55 * t233 + 0.512e3 * t240 * t242 - 0.512e3 * t250 * t253
  t258 = t50 * t109 * t256
  t261 = 0.2e1 / 0.9e1 * t185 * t65 - 0.32e2 / 0.27e2 * t188 * t65 - 0.2e1 / 0.9e1 * t97 * t139 + 0.176e3 / 0.81e2 * t196 * t65 + 0.16e2 / 0.27e2 * t104 * t139 + t45 * t207 / 0.6e1 - t45 * t258 / 0.9e1
  t265 = t17 * t19
  t267 = t80 * t167
  t269 = t84 ** 2
  t270 = 0.1e1 / t269
  t272 = t270 * t166 * t90
  t273 = t31 * t272
  t277 = t24 * t25 * t27
  t278 = t30 * t165
  t279 = t90 * t178
  t280 = t278 * t279
  t283 = t80 * t179
  t286 = s0 * t102
  t297 = t154 * t11 / t29 / t27 / t18
  t300 = -0.20e2 / 0.27e2 * t286 * t31 + 0.5e1 / 0.9e1 * t171 * t80 + t86 * t157 / 0.9e1 + 0.2e1 / 0.27e2 * t32 * t297
  t301 = t85 * t300
  t302 = t31 * t301
  t305 = t24 * t102
  t318 = t297 * t36
  t321 = t157 * t91
  t324 = -t75 * t168 + t26 * t267 - 0.3e1 / 0.2e1 * t26 * t273 + 0.3e1 / 0.2e1 * t277 * t280 - t26 * t283 / 0.2e1 - t26 * t302 / 0.4e1 - 0.20e2 / 0.27e2 * t305 * t37 + 0.5e1 / 0.9e1 * t147 * t81 - 0.5e1 / 0.6e1 * t147 * t92 + t75 * t158 / 0.9e1 + 0.2e1 / 0.3e1 * t75 * t161 + t75 * t180 / 0.2e1 + 0.2e1 / 0.27e2 * t26 * t318 + t26 * t321 / 0.6e1
  t325 = t324 * s0
  t326 = t325 * t44
  t333 = 0.1e1 / t62 / t201 / t61
  t337 = t50 * t51 * t333 * t205 * t137
  t340 = t44 * t46
  t341 = t41 * t340
  t342 = t49 * t51
  t343 = t203 * t137
  t345 = t342 * t343 * t256
  t353 = t246 / t20 / t237 / t126
  t356 = t95 * t57
  t357 = t356 * t183
  t360 = t223 * t56
  t361 = t360 * t133
  t364 = t114 * t324
  t368 = 0.1e1 / t20 / t126
  t373 = t52 * t194
  t378 = t119 / t19 / t237
  t389 = t236 / t237 / t100
  t392 = t245 * s0
  t393 = t237 ** 2
  t396 = t392 / t19 / t393
  t397 = t131 ** 2
  t398 = 0.1e1 / t397
  t403 = t245 * t118
  t406 = t403 / t393 / t100
  t408 = 0.1e1 / t132 / t397
  t409 = t125 * t408
  t412 = t40 * t241
  t413 = t412 * t95
  t418 = t183 * t133
  t419 = t228 * t418
  t423 = t228 * t95 * t252
  t426 = 0.33280e5 / 0.3e1 * t353 * t253 + 0.54e2 * t55 * t357 - 0.576e3 * t124 * t361 + 0.18e2 * t55 * t364 - 0.1232e4 / 0.3e1 * t52 * t368 * t53 * t57 + 0.528e3 * t373 * t115 - 0.21824e5 / 0.3e1 * t378 * t134 - 0.144e3 * t52 * t102 * t223 * t57 - 0.144e3 * t214 * t233 - 0.9728e4 * t389 * t242 + 0.8192e4 * t396 * t53 * t398 * t42 - 0.16384e5 * t406 * t409 + 0.3072e4 * t240 * t413 + 0.5184e4 * t220 * t230 - 0.576e3 * t124 * t419 - 0.3072e4 * t250 * t423
  t428 = t50 * t109 * t426
  t433 = t96 * t195
  t440 = t43 * t368
  t441 = t41 * t440
  t448 = t184 * t103
  t451 = 0.2e1 / 0.9e1 * t326 * t65 - 0.4e1 / 0.3e1 * t104 * t207 - 0.5e1 / 0.12e2 * t45 * t337 + t341 * t345 / 0.2e1 + t97 * t207 / 0.2e1 - t45 * t428 / 0.9e1 - t185 * t139 / 0.3e1 + 0.176e3 / 0.27e2 * t433 * t65 + 0.16e2 / 0.9e1 * t188 * t139 - t97 * t258 / 0.3e1 - 0.2464e4 / 0.243e3 * t441 * t65 - 0.88e2 / 0.27e2 * t196 * t139 + 0.8e1 / 0.9e1 * t104 * t258 - 0.16e2 / 0.9e1 * t448 * t65
  t456 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t68 + t6 * t74 * t142 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t146 * t261 - 0.3e1 / 0.8e1 * t6 * t265 * t451)
  t496 = t245 ** 2
  t497 = t237 * r0
  t503 = t397 * t131
  t551 = t154 * t27 / t29 / t78 / t100
  t572 = -0.4e1 * t24 * t73 * t27 * t280 + 0.4e1 * t24 * t25 * t78 * t79 * t165 * t279 - 0.9e1 * t277 * t30 * t270 * t166 * t178 + 0.2e1 * t277 * t278 * t90 * t300 - 0.14e2 / 0.81e2 * t26 * t551 * t36 + 0.220e3 / 0.81e2 * t24 * t194 * t37 - 0.160e3 / 0.81e2 * t305 * t81 - 0.10e2 / 0.27e2 * t147 * t158 - 0.16e2 / 0.81e2 * t75 * t318 + 0.80e2 / 0.27e2 * t305 * t92 - 0.20e2 / 0.9e1 * t147 * t161 - 0.5e1 / 0.3e1 * t147 * t180 - 0.4e1 / 0.9e1 * t75 * t321
  t589 = t166 ** 2
  t594 = t178 ** 2
  t626 = 0.2e1 / 0.3e1 * t75 * t302 + 0.10e2 / 0.3e1 * t147 * t168 - 0.8e1 / 0.3e1 * t75 * t267 + 0.4e1 * t75 * t273 - 0.2e1 / 0.3e1 * t26 * t157 * t167 - 0.4e1 * t26 * t80 * t272 + 0.6e1 * t26 * t31 / t269 / t35 * t589 + 0.3e1 / 0.2e1 * t26 * t31 * t165 * t594 + 0.4e1 / 0.3e1 * t75 * t283 + t26 * t157 * t179 / 0.3e1 - 0.8e1 / 0.27e2 * t26 * t297 * t91 - 0.2e1 / 0.3e1 * t26 * t80 * t301 - t26 * t31 * t85 * (0.220e3 / 0.81e2 * s0 * t194 * t31 - 0.160e3 / 0.81e2 * t286 * t80 - 0.10e2 / 0.27e2 * t171 * t157 - 0.16e2 / 0.81e2 * t86 * t297 - 0.14e2 / 0.81e2 * t32 * t551) / 0.4e1
  t627 = t572 + t626
  t646 = 0.6144e4 * t240 * t223 * t241 + 0.1312256e7 / 0.9e1 * t236 / t247 * t242 - 0.1310720e7 / 0.3e1 * t496 / t19 / t393 / t497 * t53 * t56 / t132 / t503 * t42 + 0.10368e5 * t220 * t361 - 0.192e3 * t214 * t364 - 0.1713664e7 / 0.9e1 * t246 / t20 / t237 / t121 * t253 - 0.576e3 * t214 * t357 + 0.72e2 * t55 * t356 * t324 - 0.6144e4 * t250 * t360 * t252 + 0.18e2 * t55 * t114 * t627 - 0.9856e4 / 0.3e1 * t52 * t368 * t115 + 0.195008e6 / 0.3e1 * t119 / t19 / t497 * t134 + 0.1056e4 * t373 * t233 + 0.65536e5 * t396 * t40 * t398 * t42 * t95
  t692 = t183 ** 2
  t698 = 0.1e1 / t20 / t121
  t713 = -0.131072e6 * t406 * t40 * t56 * t408 * t95 - 0.174592e6 / 0.3e1 * t378 * t230 + 0.266240e6 / 0.3e1 * t353 * t423 - 0.2304e4 * t124 * t95 * t56 * t418 + 0.1056e4 * t52 * t194 * t223 * t57 - 0.77824e5 * t389 * t413 + 0.655360e6 / 0.3e1 * t245 * t236 / t20 / t393 / t121 * t53 / t503 * t43 + 0.6144e4 * t240 * t412 * t183 - 0.2670592e7 / 0.9e1 * t392 * t42 / t19 / t393 / r0 * t53 * t398 + 0.1998848e7 / 0.3e1 * t403 / t393 / t120 * t409 + 0.54e2 * t52 * t22 * t692 * t57 + 0.20944e5 / 0.9e1 * t52 * t698 * t53 * t57 - 0.768e3 * t124 * t228 * t324 * t133 + 0.10368e5 * t220 * t419 - 0.6144e4 * t250 * t228 * t183 * t252
  t721 = t201 ** 2
  t725 = t205 ** 2
  t730 = t256 ** 2
  t743 = -0.5e1 / 0.2e1 * t341 * t342 * t333 * t205 * t256 + 0.2e1 * t96 * t340 * t345 + 0.2e1 / 0.3e1 * t341 * t342 * t343 * t426 - 0.16e2 / 0.3e1 * t41 * t103 * t46 * t345 - 0.4e1 / 0.9e1 * t97 * t428 - t45 * t50 * t109 * (t646 + t713) / 0.9e1 + 0.32e2 / 0.9e1 * t448 * t139 + 0.35e2 / 0.24e2 * t45 * t50 * t51 / t62 / t721 * t725 + t45 * t50 * t204 * t730 / 0.2e1 + 0.32e2 / 0.27e2 * t104 * t428 + 0.88e2 / 0.9e1 * t196 * t207 + 0.40e2 / 0.9e1 * t104 * t337 + 0.4928e4 / 0.243e3 * t441 * t139
  t776 = -0.176e3 / 0.27e2 * t196 * t258 - 0.2e1 / 0.3e1 * t185 * t258 - 0.352e3 / 0.27e2 * t433 * t139 + 0.32e2 / 0.9e1 * t188 * t258 - 0.4e1 / 0.9e1 * t326 * t139 - 0.16e2 / 0.3e1 * t188 * t207 - 0.5e1 / 0.3e1 * t97 * t337 + t185 * t207 + 0.2e1 / 0.9e1 * t627 * s0 * t44 * t65 + 0.41888e5 / 0.729e3 * t41 * t43 * t698 * t65 - 0.9856e4 / 0.243e3 * t96 * t440 * t65 - 0.64e2 / 0.27e2 * t325 * t103 * t65 + 0.352e3 / 0.27e2 * t184 * t195 * t65
  t782 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t102 * t68 - 0.5e1 / 0.9e1 * t6 * t23 * t142 + t6 * t74 * t261 / 0.2e1 - t6 * t146 * t451 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t265 * (t743 + t776))
  v4rho4_0_ = 0.2e1 * r0 * t782 + 0.8e1 * t456

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
  t32 = params.beta1 * s0
  t33 = r0 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / t33
  t38 = 2 ** (0.1e1 / 0.3e1)
  t39 = t37 * t38
  t40 = t32 * t39
  t41 = t19 ** 2
  t42 = t41 * t22
  t43 = t19 * t6
  t44 = t43 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = s0 * t37
  t47 = t46 * t38
  t48 = t42 * t45
  t51 = params.beta2 + t47 * t48 / 0.8e1
  t52 = 0.1e1 / t51
  t53 = t45 * t52
  t54 = t42 * t53
  t57 = params.beta0 + t40 * t54 / 0.8e1
  t58 = t57 * s0
  t60 = t2 ** 2
  t62 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t63 = 0.1e1 / t62
  t64 = t60 * t63
  t65 = 4 ** (0.1e1 / 0.3e1)
  t66 = t57 ** 2
  t67 = jnp.arcsinh(t46)
  t68 = t67 ** 2
  t69 = t66 * t68
  t72 = 0.9e1 * t46 * t69 + 0.1e1
  t73 = jnp.sqrt(t72)
  t76 = t64 * t65 / t73
  t79 = 0.1e1 + 0.2e1 / 0.9e1 * t58 * t37 * t76
  t83 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t84 = t83 * f.p.zeta_threshold
  t86 = f.my_piecewise3(t20, t84, t21 * t19)
  t87 = t30 ** 2
  t88 = 0.1e1 / t87
  t89 = t86 * t88
  t92 = t5 * t89 * t79 / 0.8e1
  t93 = t86 * t30
  t94 = t33 * r0
  t96 = 0.1e1 / t35 / t94
  t98 = t32 * t96 * t38
  t101 = t19 * t22
  t102 = t53 * t26
  t103 = t101 * t102
  t106 = t41 * t6
  t107 = t106 * t53
  t109 = t40 * t107 / 0.4e1
  t110 = 0.1e1 / t44
  t111 = t110 * t52
  t113 = t26 * t6 + t18 + 0.1e1
  t114 = t111 * t113
  t115 = t42 * t114
  t118 = t51 ** 2
  t119 = 0.1e1 / t118
  t120 = t45 * t119
  t121 = s0 * t96
  t122 = t121 * t38
  t125 = t45 * t26
  t126 = t101 * t125
  t129 = t106 * t45
  t131 = t47 * t129 / 0.4e1
  t132 = t110 * t113
  t133 = t42 * t132
  t136 = -t122 * t48 / 0.3e1 + t47 * t126 / 0.4e1 + t131 + t47 * t133 / 0.12e2
  t137 = t120 * t136
  t138 = t42 * t137
  t141 = -t98 * t54 / 0.3e1 + t40 * t103 / 0.4e1 + t109 + t40 * t115 / 0.12e2 - t40 * t138 / 0.8e1
  t142 = t141 * s0
  t149 = t37 * t60
  t150 = t58 * t149
  t151 = t63 * t65
  t153 = 0.1e1 / t73 / t72
  t156 = t57 * t68
  t157 = t156 * t141
  t160 = s0 ** 2
  t161 = t33 ** 2
  t164 = 0.1e1 / t34 / t161 / t33
  t165 = t160 * t164
  t166 = t66 * t67
  t169 = 0.1e1 / t34 / t161 / r0
  t171 = t160 * t169 + 0.1e1
  t172 = jnp.sqrt(t171)
  t173 = 0.1e1 / t172
  t174 = t166 * t173
  t177 = -0.24e2 * t121 * t69 + 0.18e2 * t46 * t157 - 0.48e2 * t165 * t174
  t179 = t151 * t153 * t177
  t182 = 0.2e1 / 0.9e1 * t142 * t37 * t76 - 0.16e2 / 0.27e2 * t58 * t96 * t76 - t150 * t179 / 0.9e1
  t187 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t79 - t92 - 0.3e1 / 0.8e1 * t5 * t93 * t182)
  t189 = r1 <= f.p.dens_threshold
  t190 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t191 = 0.1e1 + t190
  t192 = t191 <= f.p.zeta_threshold
  t193 = t191 ** (0.1e1 / 0.3e1)
  t195 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t198 = f.my_piecewise3(t192, 0, 0.4e1 / 0.3e1 * t193 * t195)
  t199 = t198 * t30
  t200 = params.beta1 * s2
  t201 = r1 ** 2
  t202 = r1 ** (0.1e1 / 0.3e1)
  t203 = t202 ** 2
  t205 = 0.1e1 / t203 / t201
  t206 = t205 * t38
  t207 = t200 * t206
  t208 = t191 ** 2
  t209 = t208 * t22
  t210 = t191 * t6
  t211 = t210 ** (0.1e1 / 0.3e1)
  t212 = t211 ** 2
  t213 = s2 * t205
  t214 = t213 * t38
  t215 = t209 * t212
  t218 = params.beta2 + t214 * t215 / 0.8e1
  t219 = 0.1e1 / t218
  t220 = t212 * t219
  t221 = t209 * t220
  t224 = params.beta0 + t207 * t221 / 0.8e1
  t225 = t224 * s2
  t227 = t224 ** 2
  t228 = jnp.arcsinh(t213)
  t229 = t228 ** 2
  t230 = t227 * t229
  t233 = 0.9e1 * t213 * t230 + 0.1e1
  t234 = jnp.sqrt(t233)
  t237 = t64 * t65 / t234
  t240 = 0.1e1 + 0.2e1 / 0.9e1 * t225 * t205 * t237
  t245 = f.my_piecewise3(t192, t84, t193 * t191)
  t246 = t245 * t88
  t249 = t5 * t246 * t240 / 0.8e1
  t250 = t245 * t30
  t251 = t191 * t22
  t252 = t220 * t195
  t253 = t251 * t252
  t256 = t208 * t6
  t257 = t256 * t220
  t259 = t207 * t257 / 0.4e1
  t260 = 0.1e1 / t211
  t261 = t260 * t219
  t263 = t195 * t6 + t190 + 0.1e1
  t264 = t261 * t263
  t265 = t209 * t264
  t268 = t218 ** 2
  t269 = 0.1e1 / t268
  t270 = t212 * t269
  t271 = t212 * t195
  t272 = t251 * t271
  t275 = t256 * t212
  t277 = t214 * t275 / 0.4e1
  t278 = t260 * t263
  t279 = t209 * t278
  t282 = t214 * t272 / 0.4e1 + t277 + t214 * t279 / 0.12e2
  t283 = t270 * t282
  t284 = t209 * t283
  t287 = t207 * t253 / 0.4e1 + t259 + t207 * t265 / 0.12e2 - t207 * t284 / 0.8e1
  t288 = t287 * s2
  t292 = s2 ** 2
  t293 = t227 * t292
  t294 = t201 ** 2
  t297 = 0.1e1 / t202 / t294 / r1
  t298 = t297 * t60
  t299 = t293 * t298
  t301 = 0.1e1 / t234 / t233
  t302 = t301 * t229
  t304 = t151 * t302 * t287
  t307 = 0.2e1 / 0.9e1 * t288 * t205 * t237 - 0.2e1 * t299 * t304
  t312 = f.my_piecewise3(t189, 0, -0.3e1 / 0.8e1 * t5 * t199 * t240 - t249 - 0.3e1 / 0.8e1 * t5 * t250 * t307)
  t314 = t21 ** 2
  t315 = 0.1e1 / t314
  t316 = t26 ** 2
  t321 = t16 / t22 / t6
  t323 = -0.2e1 * t23 + 0.2e1 * t321
  t324 = f.my_piecewise5(t10, 0, t14, 0, t323)
  t328 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t315 * t316 + 0.4e1 / 0.3e1 * t21 * t324)
  t335 = t5 * t29 * t88 * t79
  t341 = 0.1e1 / t87 / t6
  t345 = t5 * t86 * t341 * t79 / 0.12e2
  t347 = t5 * t89 * t182
  t350 = t38 * t41
  t353 = t32 * t37 * t350 * t53 / 0.4e1
  t356 = t98 * t107
  t362 = t316 * t22
  t371 = t40 * t106 * t114
  t374 = t40 * t106 * t137
  t378 = t324 * t6 + 0.2e1 * t26
  t384 = 0.1e1 / t35 / t161
  t385 = s0 * t384
  t391 = t122 * t129
  t399 = t47 * t43 * t125
  t401 = t46 * t38 * t19
  t402 = t22 * t110
  t413 = t46 * t350 * t45 / 0.4e1
  t415 = t47 * t106 * t132
  t418 = 0.1e1 / t44 / t43
  t419 = t113 ** 2
  t428 = 0.11e2 / 0.9e1 * t385 * t38 * t48 - 0.4e1 / 0.3e1 * t122 * t126 - 0.4e1 / 0.3e1 * t391 - 0.4e1 / 0.9e1 * t122 * t133 + t47 * t362 * t45 / 0.4e1 + t399 + t401 * t402 * t26 * t113 / 0.3e1 + t47 * t101 * t45 * t324 / 0.4e1 + t413 + t415 / 0.3e1 - t47 * t42 * t418 * t419 / 0.36e2 + t47 * t42 * t110 * t378 / 0.12e2
  t437 = t418 * t52
  t443 = t32 * t39 * t41
  t450 = 0.1e1 / t118 / t51
  t451 = t45 * t450
  t452 = t136 ** 2
  t458 = t40 * t43 * t102
  t460 = t32 * t39 * t19
  t466 = t22 * t45
  t472 = t353 - 0.4e1 / 0.3e1 * t98 * t103 - 0.4e1 / 0.3e1 * t356 - 0.4e1 / 0.9e1 * t98 * t115 + 0.2e1 / 0.3e1 * t98 * t138 + t40 * t362 * t53 / 0.4e1 + t40 * t101 * t53 * t324 / 0.4e1 + t371 / 0.3e1 - t374 / 0.2e1 + t40 * t42 * t111 * t378 / 0.12e2 - t40 * t42 * t120 * t428 / 0.8e1 + 0.11e2 / 0.9e1 * t32 * t384 * t38 * t54 - t40 * t42 * t437 * t419 / 0.36e2 - t443 * t402 * t119 * t113 * t136 / 0.6e1 + t40 * t42 * t451 * t452 / 0.4e1 + t458 + t460 * t402 * t52 * t26 * t113 / 0.3e1 - t460 * t466 * t119 * t26 * t136 / 0.2e1
  t490 = t72 ** 2
  t492 = 0.1e1 / t73 / t490
  t493 = t177 ** 2
  t508 = t141 ** 2
  t520 = t160 * s0
  t521 = t161 ** 2
  t529 = t160 ** 2
  t549 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t328 * t30 * t79 - t335 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t182 + t345 - t347 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t93 * (0.2e1 / 0.9e1 * t472 * s0 * t37 * t76 - 0.32e2 / 0.27e2 * t142 * t96 * t76 - 0.2e1 / 0.9e1 * t142 * t149 * t179 + 0.176e3 / 0.81e2 * t58 * t384 * t76 + 0.16e2 / 0.27e2 * t58 * t96 * t60 * t179 + t150 * t151 * t492 * t493 / 0.6e1 - t150 * t151 * t153 * (0.88e2 * t385 * t69 - 0.96e2 * t121 * t157 + 0.432e3 * t160 / t34 / t161 / t94 * t174 + 0.18e2 * t46 * t508 * t68 - 0.192e3 * t165 * t57 * t67 * t141 * t173 + 0.18e2 * t46 * t156 * t472 + 0.128e3 * t520 / t521 / t33 * t66 / t171 - 0.128e3 * t529 / t35 / t521 / t161 * t166 / t172 / t171) / 0.9e1))
  t550 = t193 ** 2
  t551 = 0.1e1 / t550
  t552 = t195 ** 2
  t556 = f.my_piecewise5(t14, 0, t10, 0, -t323)
  t560 = f.my_piecewise3(t192, 0, 0.4e1 / 0.9e1 * t551 * t552 + 0.4e1 / 0.3e1 * t193 * t556)
  t567 = t5 * t198 * t88 * t240
  t575 = t5 * t245 * t341 * t240 / 0.12e2
  t577 = t5 * t246 * t307
  t579 = t552 * t22
  t584 = t207 * t210 * t252
  t586 = t200 * t206 * t191
  t587 = t22 * t260
  t593 = t22 * t212
  t604 = t38 * t208
  t607 = t200 * t205 * t604 * t220 / 0.4e1
  t609 = t207 * t256 * t264
  t612 = t207 * t256 * t283
  t615 = 0.1e1 / t211 / t210
  t616 = t615 * t219
  t617 = t263 ** 2
  t623 = t200 * t206 * t208
  t631 = t556 * t6 + 0.2e1 * t195
  t637 = 0.1e1 / t268 / t218
  t638 = t212 * t637
  t639 = t282 ** 2
  t648 = t214 * t210 * t271
  t650 = t213 * t38 * t191
  t661 = t213 * t604 * t212 / 0.4e1
  t663 = t214 * t256 * t278
  t678 = t207 * t579 * t220 / 0.4e1 + t584 + t586 * t587 * t219 * t195 * t263 / 0.3e1 - t586 * t593 * t269 * t195 * t282 / 0.2e1 + t207 * t251 * t220 * t556 / 0.4e1 + t607 + t609 / 0.3e1 - t612 / 0.2e1 - t207 * t209 * t616 * t617 / 0.36e2 - t623 * t587 * t269 * t263 * t282 / 0.6e1 + t207 * t209 * t261 * t631 / 0.12e2 + t207 * t209 * t638 * t639 / 0.4e1 - t207 * t209 * t270 * (t214 * t579 * t212 / 0.4e1 + t648 + t650 * t587 * t195 * t263 / 0.3e1 + t214 * t251 * t212 * t556 / 0.4e1 + t661 + t663 / 0.3e1 - t214 * t209 * t615 * t617 / 0.36e2 + t214 * t209 * t260 * t631 / 0.12e2) / 0.8e1
  t683 = t287 ** 2
  t692 = t292 * s2
  t694 = t294 ** 2
  t698 = t233 ** 2
  t700 = 0.1e1 / t234 / t698
  t701 = t229 ** 2
  t716 = f.my_piecewise3(t189, 0, -0.3e1 / 0.8e1 * t5 * t560 * t30 * t240 - t567 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t199 * t307 + t575 - t577 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t250 * (0.2e1 / 0.9e1 * t678 * s2 * t205 * t237 - 0.6e1 * t683 * t292 * t298 * t151 * t301 * t224 * t229 + 0.54e2 * t227 * t224 * t692 / t694 * t60 * t151 * t700 * t701 * t683 - 0.2e1 * t299 * t151 * t302 * t678))
  d11 = 0.2e1 * t187 + 0.2e1 * t312 + t6 * (t549 + t716)
  t719 = -t7 - t24
  t720 = f.my_piecewise5(t10, 0, t14, 0, t719)
  t723 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t720)
  t724 = t723 * t30
  t728 = t53 * t720
  t729 = t101 * t728
  t733 = t720 * t6 + t18 + 0.1e1
  t734 = t111 * t733
  t735 = t42 * t734
  t738 = t45 * t720
  t739 = t101 * t738
  t742 = t110 * t733
  t743 = t42 * t742
  t746 = t47 * t739 / 0.4e1 + t131 + t47 * t743 / 0.12e2
  t747 = t120 * t746
  t748 = t42 * t747
  t751 = t40 * t729 / 0.4e1 + t109 + t40 * t735 / 0.12e2 - t40 * t748 / 0.8e1
  t752 = t751 * s0
  t756 = t66 * t160
  t757 = t169 * t60
  t758 = t756 * t757
  t759 = t153 * t68
  t761 = t151 * t759 * t751
  t764 = 0.2e1 / 0.9e1 * t752 * t37 * t76 - 0.2e1 * t758 * t761
  t769 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t724 * t79 - t92 - 0.3e1 / 0.8e1 * t5 * t93 * t764)
  t771 = f.my_piecewise5(t14, 0, t10, 0, -t719)
  t774 = f.my_piecewise3(t192, 0, 0.4e1 / 0.3e1 * t193 * t771)
  t775 = t774 * t30
  t779 = t201 * r1
  t781 = 0.1e1 / t203 / t779
  t783 = t200 * t781 * t38
  t786 = t220 * t771
  t787 = t251 * t786
  t791 = t771 * t6 + t190 + 0.1e1
  t792 = t261 * t791
  t793 = t209 * t792
  t796 = s2 * t781
  t797 = t796 * t38
  t800 = t212 * t771
  t801 = t251 * t800
  t804 = t260 * t791
  t805 = t209 * t804
  t808 = -t797 * t215 / 0.3e1 + t214 * t801 / 0.4e1 + t277 + t214 * t805 / 0.12e2
  t809 = t270 * t808
  t810 = t209 * t809
  t813 = -t783 * t221 / 0.3e1 + t207 * t787 / 0.4e1 + t259 + t207 * t793 / 0.12e2 - t207 * t810 / 0.8e1
  t814 = t813 * s2
  t821 = t205 * t60
  t822 = t225 * t821
  t825 = t224 * t229
  t826 = t825 * t813
  t831 = 0.1e1 / t202 / t294 / t201
  t832 = t292 * t831
  t833 = t227 * t228
  t835 = t292 * t297 + 0.1e1
  t836 = jnp.sqrt(t835)
  t837 = 0.1e1 / t836
  t838 = t833 * t837
  t841 = 0.18e2 * t213 * t826 - 0.24e2 * t796 * t230 - 0.48e2 * t832 * t838
  t843 = t151 * t301 * t841
  t846 = 0.2e1 / 0.9e1 * t814 * t205 * t237 - 0.16e2 / 0.27e2 * t225 * t781 * t237 - t822 * t843 / 0.9e1
  t851 = f.my_piecewise3(t189, 0, -0.3e1 / 0.8e1 * t5 * t775 * t240 - t249 - 0.3e1 / 0.8e1 * t5 * t250 * t846)
  t855 = 0.2e1 * t321
  t856 = f.my_piecewise5(t10, 0, t14, 0, t855)
  t860 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t315 * t720 * t26 + 0.4e1 / 0.3e1 * t21 * t856)
  t867 = t5 * t723 * t88 * t79
  t878 = t5 * t89 * t764
  t882 = t26 * t22
  t887 = t40 * t43 * t728
  t889 = t52 * t720
  t894 = t119 * t720
  t907 = -0.2e1 / 0.3e1 * t98 * t729 + t40 * t882 * t728 / 0.4e1 + t887 / 0.2e1 + t460 * t402 * t889 * t113 / 0.6e1 - t460 * t466 * t894 * t136 / 0.4e1 + t40 * t101 * t53 * t856 / 0.4e1 - 0.2e1 / 0.3e1 * t356 + t458 / 0.2e1 + t353 + t371 / 0.6e1 - t374 / 0.4e1
  t910 = t52 * t733
  t916 = t40 * t106 * t734
  t918 = t22 * t418
  t923 = t119 * t733
  t929 = t856 * t6 + t26 + t720
  t936 = t119 * t746
  t942 = t40 * t106 * t747
  t959 = t47 * t43 * t738
  t979 = t47 * t106 * t742
  t990 = -0.2e1 / 0.3e1 * t122 * t739 + t47 * t882 * t738 / 0.4e1 + t959 / 0.2e1 + t401 * t402 * t720 * t113 / 0.6e1 + t47 * t101 * t45 * t856 / 0.4e1 - 0.2e1 / 0.3e1 * t391 + t399 / 0.2e1 + t413 + t415 / 0.6e1 - 0.2e1 / 0.9e1 * t122 * t743 + t401 * t402 * t733 * t26 / 0.6e1 + t979 / 0.6e1 - t46 * t350 * t918 * t733 * t113 / 0.36e2 + t47 * t42 * t110 * t929 / 0.12e2
  t995 = -0.2e1 / 0.9e1 * t98 * t735 + t460 * t402 * t910 * t26 / 0.6e1 + t916 / 0.6e1 - t443 * t918 * t910 * t113 / 0.36e2 - t443 * t402 * t923 * t136 / 0.12e2 + t40 * t42 * t111 * t929 / 0.12e2 + t98 * t748 / 0.3e1 - t460 * t466 * t936 * t26 / 0.4e1 - t942 / 0.4e1 - t443 * t402 * t936 * t113 / 0.12e2 + t443 * t466 * t450 * t746 * t136 / 0.4e1 - t40 * t42 * t120 * t990 / 0.8e1
  t996 = t907 + t995
  t1008 = t757 * t63
  t1010 = t65 * t153
  t1011 = t68 * t751
  t1046 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t860 * t30 * t79 - t867 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t724 * t182 - t335 / 0.8e1 + t345 - t347 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t31 * t764 - t878 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t93 * (0.2e1 / 0.9e1 * t996 * s0 * t37 * t76 - 0.16e2 / 0.27e2 * t752 * t96 * t76 - t752 * t149 * t179 / 0.9e1 - 0.4e1 * t57 * t160 * t1008 * t1010 * t1011 * t141 + 0.32e2 / 0.3e1 * t756 * t164 * t60 * t761 + 0.3e1 * t756 * t1008 * t65 * t492 * t1011 * t177 + 0.32e2 / 0.3e1 * t66 * t520 / t521 / r0 * t60 * t63 * t1010 * t67 * t751 * t173 - 0.2e1 * t758 * t151 * t759 * t996))
  t1050 = f.my_piecewise5(t14, 0, t10, 0, -t855)
  t1054 = f.my_piecewise3(t192, 0, 0.4e1 / 0.9e1 * t551 * t771 * t195 + 0.4e1 / 0.3e1 * t193 * t1050)
  t1061 = t5 * t774 * t88 * t240
  t1072 = t5 * t246 * t846
  t1076 = t783 * t257
  t1082 = t195 * t22
  t1087 = t207 * t210 * t786
  t1089 = t219 * t771
  t1094 = t269 * t771
  t1104 = -0.2e1 / 0.3e1 * t783 * t253 - 0.2e1 / 0.3e1 * t1076 - 0.2e1 / 0.9e1 * t783 * t265 + t783 * t284 / 0.3e1 + t207 * t1082 * t786 / 0.4e1 + t1087 / 0.2e1 + t586 * t587 * t1089 * t263 / 0.6e1 - t586 * t593 * t1094 * t282 / 0.4e1 + t207 * t251 * t220 * t1050 / 0.4e1 + t584 / 0.2e1 + t607
  t1107 = t219 * t791
  t1113 = t207 * t256 * t792
  t1115 = t22 * t615
  t1120 = t269 * t791
  t1126 = t1050 * t6 + t195 + t771
  t1131 = t269 * t808
  t1137 = t207 * t256 * t809
  t1150 = t797 * t275
  t1158 = t214 * t210 * t800
  t1175 = t214 * t256 * t804
  t1186 = -0.2e1 / 0.3e1 * t797 * t272 - 0.2e1 / 0.3e1 * t1150 - 0.2e1 / 0.9e1 * t797 * t279 + t214 * t1082 * t800 / 0.4e1 + t1158 / 0.2e1 + t650 * t587 * t771 * t263 / 0.6e1 + t214 * t251 * t212 * t1050 / 0.4e1 + t648 / 0.2e1 + t661 + t663 / 0.6e1 + t650 * t587 * t791 * t195 / 0.6e1 + t1175 / 0.6e1 - t213 * t604 * t1115 * t791 * t263 / 0.36e2 + t214 * t209 * t260 * t1126 / 0.12e2
  t1191 = t609 / 0.6e1 - t612 / 0.4e1 + t586 * t587 * t1107 * t195 / 0.6e1 + t1113 / 0.6e1 - t623 * t1115 * t1107 * t263 / 0.36e2 - t623 * t587 * t1120 * t282 / 0.12e2 + t207 * t209 * t261 * t1126 / 0.12e2 - t586 * t593 * t1131 * t195 / 0.4e1 - t1137 / 0.4e1 - t623 * t587 * t1131 * t263 / 0.12e2 + t623 * t593 * t637 * t808 * t282 / 0.4e1 - t207 * t209 * t270 * t1186 / 0.8e1
  t1192 = t1104 + t1191
  t1198 = t298 * t63
  t1201 = t825 * t287
  t1231 = t832 * t224
  t1246 = f.my_piecewise3(t189, 0, -0.3e1 / 0.8e1 * t5 * t1054 * t30 * t240 - t1061 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t775 * t307 - t567 / 0.8e1 + t575 - t577 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t199 * t846 - t1072 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t250 * (0.2e1 / 0.9e1 * t1192 * s2 * t205 * t237 - 0.2e1 * t813 * t292 * t1198 * t65 * t301 * t1201 - 0.16e2 / 0.27e2 * t288 * t781 * t237 + 0.16e2 / 0.3e1 * t293 * t831 * t60 * t304 - t288 * t821 * t843 / 0.9e1 + 0.3e1 * t293 * t1198 * t65 * t700 * t841 * t229 * t287 - t822 * t151 * t301 * (-0.96e2 * t1231 * t228 * t837 * t287 + 0.18e2 * t213 * t287 * t229 * t813 + 0.18e2 * t213 * t825 * t1192 - 0.48e2 * t796 * t1201) / 0.9e1))
  d12 = t187 + t312 + t769 + t851 + t6 * (t1046 + t1246)
  t1251 = t720 ** 2
  t1255 = 0.2e1 * t23 + 0.2e1 * t321
  t1256 = f.my_piecewise5(t10, 0, t14, 0, t1255)
  t1260 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t315 * t1251 + 0.4e1 / 0.3e1 * t21 * t1256)
  t1270 = t1251 * t22
  t1288 = t733 ** 2
  t1299 = t1256 * t6 + 0.2e1 * t720
  t1304 = t746 ** 2
  t1334 = t40 * t1270 * t53 / 0.4e1 + t887 + t460 * t402 * t889 * t733 / 0.3e1 - t460 * t466 * t894 * t746 / 0.2e1 + t40 * t101 * t53 * t1256 / 0.4e1 + t353 + t916 / 0.3e1 - t942 / 0.2e1 - t40 * t42 * t437 * t1288 / 0.36e2 - t443 * t402 * t923 * t746 / 0.6e1 + t40 * t42 * t111 * t1299 / 0.12e2 + t40 * t42 * t451 * t1304 / 0.4e1 - t40 * t42 * t120 * (t47 * t1270 * t45 / 0.4e1 + t959 + t401 * t402 * t720 * t733 / 0.3e1 + t47 * t101 * t45 * t1256 / 0.4e1 + t413 + t979 / 0.3e1 - t47 * t42 * t418 * t1288 / 0.36e2 + t47 * t42 * t110 * t1299 / 0.12e2) / 0.8e1
  t1339 = t751 ** 2
  t1352 = t68 ** 2
  t1367 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t1260 * t30 * t79 - t867 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t724 * t764 + t345 - t878 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t93 * (0.2e1 / 0.9e1 * t1334 * s0 * t37 * t76 - 0.6e1 * t1339 * t160 * t757 * t151 * t153 * t57 * t68 + 0.54e2 * t66 * t57 * t520 / t521 * t60 * t151 * t492 * t1352 * t1339 - 0.2e1 * t758 * t151 * t759 * t1334))
  t1368 = t771 ** 2
  t1372 = f.my_piecewise5(t14, 0, t10, 0, -t1255)
  t1376 = f.my_piecewise3(t192, 0, 0.4e1 / 0.9e1 * t551 * t1368 + 0.4e1 / 0.3e1 * t193 * t1372)
  t1389 = 0.1e1 / t203 / t294
  t1401 = t1368 * t22
  t1413 = t808 ** 2
  t1420 = t1372 * t6 + 0.2e1 * t771
  t1425 = s2 * t1389
  t1446 = t791 ** 2
  t1455 = 0.11e2 / 0.9e1 * t1425 * t38 * t215 - 0.4e1 / 0.3e1 * t797 * t801 - 0.4e1 / 0.3e1 * t1150 - 0.4e1 / 0.9e1 * t797 * t805 + t214 * t1401 * t212 / 0.4e1 + t1158 + t650 * t587 * t771 * t791 / 0.3e1 + t214 * t251 * t212 * t1372 / 0.4e1 + t661 + t1175 / 0.3e1 - t214 * t209 * t615 * t1446 / 0.36e2 + t214 * t209 * t260 * t1420 / 0.12e2
  t1472 = t1113 / 0.3e1 - t1137 / 0.2e1 + 0.11e2 / 0.9e1 * t200 * t1389 * t38 * t221 - 0.4e1 / 0.3e1 * t783 * t787 - 0.4e1 / 0.3e1 * t1076 - 0.4e1 / 0.9e1 * t783 * t793 + 0.2e1 / 0.3e1 * t783 * t810 + t207 * t1401 * t220 / 0.4e1 + t207 * t251 * t220 * t1372 / 0.4e1 + t607 + t1087 + t586 * t587 * t1089 * t791 / 0.3e1 + t207 * t209 * t638 * t1413 / 0.4e1 + t207 * t209 * t261 * t1420 / 0.12e2 - t207 * t209 * t270 * t1455 / 0.8e1 - t586 * t593 * t1094 * t808 / 0.2e1 - t207 * t209 * t616 * t1446 / 0.36e2 - t623 * t587 * t1120 * t808 / 0.6e1
  t1490 = t841 ** 2
  t1505 = t813 ** 2
  t1523 = t292 ** 2
  t1543 = f.my_piecewise3(t189, 0, -0.3e1 / 0.8e1 * t5 * t1376 * t30 * t240 - t1061 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t775 * t846 + t575 - t1072 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t250 * (0.2e1 / 0.9e1 * t1472 * s2 * t205 * t237 - 0.32e2 / 0.27e2 * t814 * t781 * t237 - 0.2e1 / 0.9e1 * t814 * t821 * t843 + 0.176e3 / 0.81e2 * t225 * t1389 * t237 + 0.16e2 / 0.27e2 * t225 * t781 * t60 * t843 + t822 * t151 * t700 * t1490 / 0.6e1 - t822 * t151 * t301 * (0.88e2 * t1425 * t230 - 0.96e2 * t796 * t826 + 0.432e3 * t292 / t202 / t294 / t779 * t838 + 0.18e2 * t213 * t1505 * t229 - 0.192e3 * t1231 * t228 * t813 * t837 + 0.18e2 * t213 * t825 * t1472 + 0.128e3 * t692 / t694 / t201 * t227 / t835 - 0.128e3 * t1523 / t203 / t694 / t294 * t833 / t836 / t835) / 0.9e1))
  d22 = 0.2e1 * t769 + 0.2e1 * t851 + t6 * (t1367 + t1543)
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
  t44 = params.beta1 * s0
  t45 = r0 ** 2
  t46 = r0 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t49 = 0.1e1 / t47 / t45
  t50 = 2 ** (0.1e1 / 0.3e1)
  t51 = t49 * t50
  t52 = t44 * t51
  t53 = t19 ** 2
  t54 = t53 * t24
  t55 = t19 * t6
  t56 = t55 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t58 = s0 * t49
  t59 = t58 * t50
  t60 = t54 * t57
  t63 = params.beta2 + t59 * t60 / 0.8e1
  t64 = 0.1e1 / t63
  t65 = t57 * t64
  t66 = t54 * t65
  t69 = params.beta0 + t52 * t66 / 0.8e1
  t70 = t69 * s0
  t72 = t2 ** 2
  t74 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t75 = 0.1e1 / t74
  t76 = t72 * t75
  t77 = 4 ** (0.1e1 / 0.3e1)
  t78 = t69 ** 2
  t79 = jnp.asinh(t58)
  t80 = t79 ** 2
  t81 = t78 * t80
  t84 = 0.9e1 * t58 * t81 + 0.1e1
  t85 = jnp.sqrt(t84)
  t88 = t76 * t77 / t85
  t91 = 0.1e1 + 0.2e1 / 0.9e1 * t70 * t49 * t88
  t97 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t98 = t42 ** 2
  t99 = 0.1e1 / t98
  t100 = t97 * t99
  t104 = t97 * t42
  t105 = t45 * r0
  t107 = 0.1e1 / t47 / t105
  t108 = t107 * t50
  t109 = t44 * t108
  t112 = t19 * t24
  t113 = t65 * t28
  t114 = t112 * t113
  t117 = t53 * t6
  t118 = t117 * t65
  t121 = 0.1e1 / t56
  t122 = t121 * t64
  t124 = t28 * t6 + t18 + 0.1e1
  t125 = t122 * t124
  t126 = t54 * t125
  t129 = t63 ** 2
  t130 = 0.1e1 / t129
  t131 = t57 * t130
  t132 = s0 * t107
  t133 = t132 * t50
  t136 = t57 * t28
  t137 = t112 * t136
  t140 = t117 * t57
  t143 = t121 * t124
  t144 = t54 * t143
  t147 = -t133 * t60 / 0.3e1 + t59 * t137 / 0.4e1 + t59 * t140 / 0.4e1 + t59 * t144 / 0.12e2
  t148 = t131 * t147
  t149 = t54 * t148
  t152 = -t109 * t66 / 0.3e1 + t52 * t114 / 0.4e1 + t52 * t118 / 0.4e1 + t52 * t126 / 0.12e2 - t52 * t149 / 0.8e1
  t153 = t152 * s0
  t160 = t49 * t72
  t161 = t70 * t160
  t162 = t75 * t77
  t164 = 0.1e1 / t85 / t84
  t167 = t69 * t80
  t168 = t167 * t152
  t171 = s0 ** 2
  t172 = t45 ** 2
  t176 = t171 / t46 / t172 / t45
  t177 = t78 * t79
  t178 = t172 * r0
  t182 = 0.1e1 + t171 / t46 / t178
  t183 = jnp.sqrt(t182)
  t184 = 0.1e1 / t183
  t185 = t177 * t184
  t188 = -0.24e2 * t132 * t81 + 0.18e2 * t58 * t168 - 0.48e2 * t176 * t185
  t190 = t162 * t164 * t188
  t193 = 0.2e1 / 0.9e1 * t153 * t49 * t88 - 0.16e2 / 0.27e2 * t70 * t107 * t88 - t161 * t190 / 0.9e1
  t197 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t198 = t197 * f.p.zeta_threshold
  t200 = f.my_piecewise3(t20, t198, t21 * t19)
  t202 = 0.1e1 / t98 / t6
  t203 = t200 * t202
  t207 = t200 * t99
  t211 = t200 * t42
  t213 = t50 * t53
  t214 = t213 * t65
  t225 = t29 * t24
  t226 = t225 * t65
  t229 = t65 * t37
  t230 = t112 * t229
  t233 = t117 * t125
  t236 = t117 * t148
  t241 = t37 * t6 + 0.2e1 * t28
  t242 = t122 * t241
  t243 = t54 * t242
  t247 = 0.1e1 / t47 / t172
  t248 = s0 * t247
  t249 = t248 * t50
  t258 = t225 * t57
  t261 = t55 * t136
  t263 = t50 * t19
  t264 = t58 * t263
  t265 = t24 * t121
  t266 = t28 * t124
  t267 = t265 * t266
  t270 = t57 * t37
  t271 = t112 * t270
  t274 = t213 * t57
  t277 = t117 * t143
  t281 = 0.1e1 / t56 / t55
  t282 = t124 ** 2
  t283 = t281 * t282
  t284 = t54 * t283
  t287 = t121 * t241
  t288 = t54 * t287
  t291 = 0.11e2 / 0.9e1 * t249 * t60 - 0.4e1 / 0.3e1 * t133 * t137 - 0.4e1 / 0.3e1 * t133 * t140 - 0.4e1 / 0.9e1 * t133 * t144 + t59 * t258 / 0.4e1 + t59 * t261 + t264 * t267 / 0.3e1 + t59 * t271 / 0.4e1 + t58 * t274 / 0.4e1 + t59 * t277 / 0.3e1 - t59 * t284 / 0.36e2 + t59 * t288 / 0.12e2
  t292 = t131 * t291
  t293 = t54 * t292
  t297 = t44 * t247 * t50
  t301 = t281 * t64 * t282
  t302 = t54 * t301
  t306 = t44 * t51 * t53
  t308 = t130 * t124 * t147
  t309 = t265 * t308
  t313 = 0.1e1 / t129 / t63
  t315 = t147 ** 2
  t316 = t57 * t313 * t315
  t317 = t54 * t316
  t320 = t55 * t113
  t323 = t44 * t51 * t19
  t324 = t64 * t28
  t325 = t324 * t124
  t326 = t265 * t325
  t329 = t24 * t57
  t331 = t130 * t28 * t147
  t332 = t329 * t331
  t335 = t44 * t49 * t214 / 0.4e1 - 0.4e1 / 0.3e1 * t109 * t114 - 0.4e1 / 0.3e1 * t109 * t118 - 0.4e1 / 0.9e1 * t109 * t126 + 0.2e1 / 0.3e1 * t109 * t149 + t52 * t226 / 0.4e1 + t52 * t230 / 0.4e1 + t52 * t233 / 0.3e1 - t52 * t236 / 0.2e1 + t52 * t243 / 0.12e2 - t52 * t293 / 0.8e1 + 0.11e2 / 0.9e1 * t297 * t66 - t52 * t302 / 0.36e2 - t306 * t309 / 0.6e1 + t52 * t317 / 0.4e1 + t52 * t320 + t323 * t326 / 0.3e1 - t323 * t332 / 0.2e1
  t336 = t335 * s0
  t343 = t153 * t160
  t349 = t107 * t72
  t350 = t70 * t349
  t353 = t84 ** 2
  t355 = 0.1e1 / t85 / t353
  t356 = t188 ** 2
  t358 = t162 * t355 * t356
  t368 = t171 / t46 / t172 / t105
  t371 = t152 ** 2
  t372 = t371 * t80
  t375 = t176 * t69
  t376 = t79 * t152
  t377 = t376 * t184
  t380 = t167 * t335
  t383 = t171 * s0
  t384 = t172 ** 2
  t387 = t383 / t384 / t45
  t388 = 0.1e1 / t182
  t389 = t78 * t388
  t392 = t171 ** 2
  t396 = t392 / t47 / t384 / t172
  t398 = 0.1e1 / t183 / t182
  t399 = t177 * t398
  t402 = -0.96e2 * t132 * t168 + 0.432e3 * t368 * t185 + 0.88e2 * t248 * t81 + 0.18e2 * t58 * t372 - 0.192e3 * t375 * t377 + 0.18e2 * t58 * t380 + 0.128e3 * t387 * t389 - 0.128e3 * t396 * t399
  t404 = t162 * t164 * t402
  t407 = 0.2e1 / 0.9e1 * t336 * t49 * t88 - 0.32e2 / 0.27e2 * t153 * t107 * t88 - 0.2e1 / 0.9e1 * t343 * t190 + 0.176e3 / 0.81e2 * t70 * t247 * t88 + 0.16e2 / 0.27e2 * t350 * t190 + t161 * t358 / 0.6e1 - t161 * t404 / 0.9e1
  t412 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t91 - t5 * t100 * t91 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t104 * t193 + t5 * t203 * t91 / 0.12e2 - t5 * t207 * t193 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t211 * t407)
  t414 = r1 <= f.p.dens_threshold
  t415 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t416 = 0.1e1 + t415
  t417 = t416 <= f.p.zeta_threshold
  t418 = t416 ** (0.1e1 / 0.3e1)
  t419 = t418 ** 2
  t420 = 0.1e1 / t419
  t422 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t423 = t422 ** 2
  t427 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t431 = f.my_piecewise3(t417, 0, 0.4e1 / 0.9e1 * t420 * t423 + 0.4e1 / 0.3e1 * t418 * t427)
  t432 = t431 * t42
  t433 = params.beta1 * s2
  t434 = r1 ** 2
  t435 = r1 ** (0.1e1 / 0.3e1)
  t436 = t435 ** 2
  t438 = 0.1e1 / t436 / t434
  t439 = t438 * t50
  t440 = t433 * t439
  t441 = t416 ** 2
  t442 = t441 * t24
  t443 = t416 * t6
  t444 = t443 ** (0.1e1 / 0.3e1)
  t445 = t444 ** 2
  t446 = s2 * t438
  t447 = t446 * t50
  t451 = params.beta2 + t447 * t442 * t445 / 0.8e1
  t452 = 0.1e1 / t451
  t453 = t445 * t452
  t457 = params.beta0 + t440 * t442 * t453 / 0.8e1
  t460 = t457 ** 2
  t461 = jnp.asinh(t446)
  t462 = t461 ** 2
  t466 = 0.9e1 * t446 * t460 * t462 + 0.1e1
  t467 = jnp.sqrt(t466)
  t470 = t76 * t77 / t467
  t473 = 0.1e1 + 0.2e1 / 0.9e1 * t457 * s2 * t438 * t470
  t479 = f.my_piecewise3(t417, 0, 0.4e1 / 0.3e1 * t418 * t422)
  t480 = t479 * t99
  t484 = t479 * t42
  t485 = t416 * t24
  t486 = t453 * t422
  t490 = t441 * t6
  t494 = 0.1e1 / t444
  t495 = t494 * t452
  t497 = t422 * t6 + t415 + 0.1e1
  t498 = t495 * t497
  t502 = t451 ** 2
  t503 = 0.1e1 / t502
  t504 = t445 * t503
  t505 = t445 * t422
  t512 = t494 * t497
  t516 = t447 * t485 * t505 / 0.4e1 + t447 * t490 * t445 / 0.4e1 + t447 * t442 * t512 / 0.12e2
  t517 = t504 * t516
  t521 = t440 * t485 * t486 / 0.4e1 + t440 * t490 * t453 / 0.4e1 + t440 * t442 * t498 / 0.12e2 - t440 * t442 * t517 / 0.8e1
  t526 = s2 ** 2
  t528 = t434 ** 2
  t532 = 0.1e1 / t435 / t528 / r1 * t72
  t533 = t460 * t526 * t532
  t535 = 0.1e1 / t467 / t466
  t536 = t535 * t462
  t541 = 0.2e1 / 0.9e1 * t521 * s2 * t438 * t470 - 0.2e1 * t533 * t162 * t536 * t521
  t546 = f.my_piecewise3(t417, t198, t418 * t416)
  t547 = t546 * t202
  t551 = t546 * t99
  t555 = t546 * t42
  t556 = t423 * t24
  t563 = t433 * t439 * t416
  t564 = t24 * t494
  t565 = t452 * t422
  t566 = t565 * t497
  t570 = t24 * t445
  t571 = t503 * t422
  t572 = t571 * t516
  t576 = t453 * t427
  t581 = t50 * t441
  t592 = 0.1e1 / t444 / t443
  t594 = t497 ** 2
  t595 = t592 * t452 * t594
  t600 = t433 * t439 * t441
  t601 = t503 * t497
  t602 = t601 * t516
  t608 = t427 * t6 + 0.2e1 * t422
  t609 = t495 * t608
  t614 = 0.1e1 / t502 / t451
  t616 = t516 ** 2
  t617 = t445 * t614 * t616
  t627 = t446 * t50 * t416
  t628 = t422 * t497
  t632 = t445 * t427
  t642 = t592 * t594
  t646 = t494 * t608
  t650 = t447 * t556 * t445 / 0.4e1 + t447 * t443 * t505 + t627 * t564 * t628 / 0.3e1 + t447 * t485 * t632 / 0.4e1 + t446 * t581 * t445 / 0.4e1 + t447 * t490 * t512 / 0.3e1 - t447 * t442 * t642 / 0.36e2 + t447 * t442 * t646 / 0.12e2
  t651 = t504 * t650
  t655 = t440 * t556 * t453 / 0.4e1 + t440 * t443 * t486 + t563 * t564 * t566 / 0.3e1 - t563 * t570 * t572 / 0.2e1 + t440 * t485 * t576 / 0.4e1 + t433 * t438 * t581 * t453 / 0.4e1 + t440 * t490 * t498 / 0.3e1 - t440 * t490 * t517 / 0.2e1 - t440 * t442 * t595 / 0.36e2 - t600 * t564 * t602 / 0.6e1 + t440 * t442 * t609 / 0.12e2 + t440 * t442 * t617 / 0.4e1 - t440 * t442 * t651 / 0.8e1
  t660 = t521 ** 2
  t669 = t526 * s2
  t670 = t460 * t457 * t669
  t671 = t528 ** 2
  t673 = 0.1e1 / t671 * t72
  t675 = t466 ** 2
  t677 = 0.1e1 / t467 / t675
  t678 = t462 ** 2
  t688 = 0.2e1 / 0.9e1 * t655 * s2 * t438 * t470 - 0.6e1 * t660 * t526 * t532 * t162 * t535 * t457 * t462 + 0.54e2 * t670 * t673 * t162 * t677 * t678 * t660 - 0.2e1 * t533 * t162 * t536 * t655
  t693 = f.my_piecewise3(t414, 0, -0.3e1 / 0.8e1 * t5 * t432 * t473 - t5 * t480 * t473 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t484 * t541 + t5 * t547 * t473 / 0.12e2 - t5 * t551 * t541 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t555 * t688)
  t703 = t24 ** 2
  t707 = 0.6e1 * t33 - 0.6e1 * t16 / t703
  t708 = f.my_piecewise5(t10, 0, t14, 0, t707)
  t712 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t708)
  t735 = 0.1e1 / t98 / t24
  t746 = t53 * t121
  t757 = 0.1e1 / t47 / t178
  t766 = t29 * t6
  t770 = t19 * t57
  t783 = s0 * t757
  t808 = 0.1e1 / t56 / t54
  t809 = t282 * t124
  t814 = t28 * t24
  t818 = 0.3e1 / 0.2e1 * t59 * t766 * t57 + 0.3e1 / 0.2e1 * t59 * t770 * t28 - 0.154e3 / 0.27e2 * t783 * t50 * t60 + 0.22e2 / 0.3e1 * t249 * t140 - 0.2e1 * t133 * t258 + t59 * t746 * t124 / 0.2e1 - 0.2e1 * t133 * t271 - 0.8e1 / 0.3e1 * t133 * t277 - 0.2e1 / 0.3e1 * t133 * t288 - 0.8e1 * t133 * t261 + 0.2e1 / 0.9e1 * t133 * t284 - t59 * t117 * t283 / 0.6e1 + t59 * t54 * t808 * t809 / 0.27e2 + 0.3e1 / 0.4e1 * t59 * t814 * t270
  t834 = t708 * t6 + 0.3e1 * t37
  t852 = t24 * t281
  t864 = t6 * t121
  t870 = t59 * t225 * t143 / 0.2e1 + 0.3e1 / 0.2e1 * t59 * t55 * t270 + t59 * t112 * t57 * t708 / 0.4e1 + t59 * t117 * t287 / 0.2e1 + t59 * t54 * t121 * t834 / 0.12e2 + 0.22e2 / 0.3e1 * t249 * t137 + 0.22e2 / 0.9e1 * t249 * t144 + t264 * t265 * t37 * t124 / 0.2e1 + t264 * t265 * t28 * t241 / 0.2e1 - t58 * t213 * t852 * t124 * t241 / 0.12e2 - t264 * t852 * t28 * t282 / 0.6e1 - 0.8e1 / 0.3e1 * t132 * t263 * t267 + 0.2e1 * t264 * t864 * t266 - 0.2e1 * t132 * t274
  t882 = t52 * t746 * t64 * t124 / 0.2e1 - 0.3e1 / 0.4e1 * t52 * t53 * t57 * t130 * t147 - 0.154e3 / 0.27e2 * t44 * t757 * t50 * t66 - 0.2e1 * t109 * t226 + 0.22e2 / 0.3e1 * t297 * t118 + 0.3e1 / 0.2e1 * t52 * t766 * t65 + 0.3e1 / 0.2e1 * t52 * t770 * t324 - 0.2e1 * t44 * t107 * t214 - t52 * t54 * t131 * (t818 + t870) / 0.8e1 - 0.2e1 * t109 * t230 - 0.8e1 / 0.3e1 * t109 * t233 + 0.4e1 * t109 * t236
  t894 = t129 ** 2
  t921 = -0.2e1 / 0.3e1 * t109 * t243 + t109 * t293 + 0.3e1 / 0.4e1 * t52 * t814 * t229 + t52 * t54 * t808 * t64 * t809 / 0.27e2 - 0.3e1 / 0.4e1 * t52 * t54 * t57 / t894 * t315 * t147 + 0.3e1 / 0.2e1 * t52 * t117 * t316 + 0.2e1 / 0.9e1 * t109 * t302 - 0.11e2 / 0.3e1 * t297 * t149 - 0.2e1 * t109 * t317 + 0.3e1 / 0.2e1 * t52 * t55 * t229 - t52 * t117 * t301 / 0.6e1 + 0.22e2 / 0.3e1 * t297 * t114 - 0.8e1 * t109 * t320
  t950 = t130 * t291
  t974 = 0.22e2 / 0.9e1 * t297 * t126 + t52 * t225 * t125 / 0.2e1 - 0.3e1 / 0.4e1 * t52 * t225 * t148 + t52 * t112 * t65 * t708 / 0.4e1 + t52 * t117 * t242 / 0.2e1 - 0.3e1 / 0.4e1 * t52 * t117 * t292 + t52 * t54 * t122 * t834 / 0.12e2 - t323 * t265 * t130 * t124 * t147 * t28 - t306 * t265 * t950 * t124 / 0.4e1 + 0.3e1 / 0.4e1 * t306 * t329 * t313 * t291 * t147 - t323 * t852 * t64 * t282 * t28 / 0.6e1 + 0.4e1 / 0.3e1 * t44 * t108 * t53 * t309 + t323 * t265 * t64 * t37 * t124 / 0.2e1
  t986 = t44 * t108 * t19
  t1010 = t64 * t241
  t1028 = -0.3e1 / 0.4e1 * t323 * t329 * t130 * t37 * t147 + 0.2e1 * t323 * t864 * t325 - t306 * t864 * t308 - 0.8e1 / 0.3e1 * t986 * t326 + 0.4e1 * t986 * t332 + t306 * t265 * t313 * t124 * t315 / 0.2e1 + t306 * t852 * t130 * t282 * t147 / 0.12e2 + 0.3e1 / 0.2e1 * t323 * t329 * t313 * t315 * t28 - 0.3e1 * t323 * t6 * t57 * t331 + t323 * t265 * t1010 * t28 / 0.2e1 - t306 * t852 * t1010 * t124 / 0.12e2 - t306 * t265 * t130 * t241 * t147 / 0.4e1 - 0.3e1 / 0.4e1 * t323 * t329 * t950 * t28
  t1030 = t882 + t921 + t974 + t1028
  t1055 = t384 ** 2
  t1059 = t182 ** 2
  t1118 = -0.2432e4 * t383 / t384 / t105 * t389 + 0.1024e4 * t392 * s0 / t46 / t1055 * t78 / t1059 - 0.144e3 * t132 * t372 - 0.144e3 * t132 * t380 + 0.8320e4 / 0.3e1 * t392 / t47 / t384 / t178 * t399 + 0.54e2 * t58 * t152 * t80 * t335 - 0.288e3 * t176 * t371 * t79 * t184 + 0.768e3 * t387 * t69 * t388 * t152 + 0.18e2 * t58 * t167 * t1030 - 0.1024e4 * t392 * t171 / t1055 / t105 * t177 / t183 / t1059 - 0.1232e4 / 0.3e1 * t783 * t81 + 0.528e3 * t248 * t168 - 0.10912e5 / 0.3e1 * t171 / t46 / t384 * t185 + 0.2592e4 * t368 * t69 * t377 - 0.288e3 * t375 * t79 * t335 * t184 - 0.768e3 * t396 * t69 * t376 * t398
  t1149 = 0.2e1 / 0.9e1 * t1030 * s0 * t49 * t88 + 0.16e2 / 0.9e1 * t153 * t349 * t190 - t343 * t404 / 0.3e1 - 0.2464e4 / 0.243e3 * t70 * t757 * t88 - 0.88e2 / 0.27e2 * t70 * t247 * t72 * t190 + 0.8e1 / 0.9e1 * t350 * t404 - t161 * t162 * t164 * t1118 / 0.9e1 + t343 * t358 / 0.2e1 - 0.4e1 / 0.3e1 * t350 * t358 - 0.5e1 / 0.12e2 * t161 * t162 / t85 / t353 / t84 * t356 * t188 + t161 * t162 * t355 * t188 * t402 / 0.2e1 - 0.16e2 / 0.9e1 * t336 * t107 * t88 - t336 * t160 * t190 / 0.3e1 + 0.176e3 / 0.27e2 * t153 * t247 * t88
  t1154 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t712 * t42 * t91 - 0.3e1 / 0.8e1 * t5 * t41 * t99 * t91 - 0.9e1 / 0.8e1 * t5 * t43 * t193 + t5 * t97 * t202 * t91 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t100 * t193 - 0.9e1 / 0.8e1 * t5 * t104 * t407 - 0.5e1 / 0.36e2 * t5 * t200 * t735 * t91 + t5 * t203 * t193 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t207 * t407 - 0.3e1 / 0.8e1 * t5 * t211 * t1149)
  t1164 = f.my_piecewise5(t14, 0, t10, 0, -t707)
  t1168 = f.my_piecewise3(t417, 0, -0.8e1 / 0.27e2 / t419 / t416 * t423 * t422 + 0.4e1 / 0.3e1 * t420 * t422 * t427 + 0.4e1 / 0.3e1 * t418 * t1164)
  t1200 = t502 ** 2
  t1212 = 0.1e1 / t444 / t442
  t1214 = t594 * t497
  t1230 = t1164 * t6 + 0.3e1 * t427
  t1235 = t422 * t24
  t1239 = t423 * t6
  t1246 = t6 * t494
  t1266 = t24 * t592
  t1271 = t416 * t445
  t1293 = t441 * t494
  t1297 = 0.3e1 / 0.4e1 * t447 * t1235 * t632 + 0.3e1 / 0.2e1 * t447 * t1239 * t445 + t447 * t556 * t512 / 0.2e1 + 0.2e1 * t627 * t1246 * t628 + t627 * t564 * t427 * t497 / 0.2e1 + t627 * t564 * t422 * t608 / 0.2e1 - t447 * t490 * t642 / 0.6e1 + t447 * t442 * t1212 * t1214 / 0.27e2 - t446 * t581 * t1266 * t497 * t608 / 0.12e2 + 0.3e1 / 0.2e1 * t447 * t1271 * t422 + 0.3e1 / 0.2e1 * t447 * t443 * t632 + t447 * t485 * t445 * t1164 / 0.4e1 + t447 * t490 * t646 / 0.2e1 + t447 * t442 * t494 * t1230 / 0.12e2 - t627 * t1266 * t422 * t594 / 0.6e1 + t447 * t1293 * t497 / 0.2e1
  t1332 = -0.3e1 / 0.4e1 * t440 * t442 * t445 / t1200 * t616 * t516 + 0.3e1 / 0.2e1 * t440 * t490 * t617 + t440 * t442 * t1212 * t452 * t1214 / 0.27e2 - t440 * t490 * t595 / 0.6e1 + t440 * t490 * t609 / 0.2e1 - 0.3e1 / 0.4e1 * t440 * t490 * t651 + t440 * t442 * t495 * t1230 / 0.12e2 - t440 * t442 * t504 * t1297 / 0.8e1 + 0.3e1 / 0.4e1 * t440 * t1235 * t576 + t440 * t556 * t498 / 0.2e1 - 0.3e1 / 0.4e1 * t440 * t556 * t517 + 0.3e1 / 0.2e1 * t440 * t443 * t576 + t440 * t485 * t453 * t1164 / 0.4e1 - t563 * t1266 * t565 * t594 / 0.6e1 + 0.3e1 / 0.2e1 * t563 * t570 * t614 * t422 * t616 + 0.3e1 / 0.4e1 * t600 * t570 * t614 * t516 * t650
  t1338 = t452 * t497
  t1402 = t600 * t1266 * t503 * t594 * t516 / 0.12e2 - t600 * t1266 * t1338 * t608 / 0.12e2 - t600 * t564 * t503 * t608 * t516 / 0.4e1 - t600 * t564 * t601 * t650 / 0.4e1 + t563 * t564 * t452 * t427 * t497 / 0.2e1 + t563 * t564 * t565 * t608 / 0.2e1 - 0.3e1 / 0.4e1 * t563 * t570 * t503 * t427 * t516 - 0.3e1 / 0.4e1 * t563 * t570 * t571 * t650 - t600 * t1246 * t602 + 0.2e1 * t563 * t1246 * t566 - 0.3e1 * t563 * t6 * t445 * t572 + t600 * t564 * t614 * t497 * t616 / 0.2e1 - t563 * t564 * t503 * t628 * t516 + 0.3e1 / 0.2e1 * t440 * t1271 * t565 + t440 * t1293 * t1338 / 0.2e1 - 0.3e1 / 0.4e1 * t440 * t441 * t445 * t503 * t516 + 0.3e1 / 0.2e1 * t440 * t1239 * t453
  t1403 = t1332 + t1402
  t1417 = t660 * t521
  t1430 = t460 ** 2
  t1431 = t526 ** 2
  t1464 = f.my_piecewise3(t414, 0, -0.3e1 / 0.8e1 * t5 * t1168 * t42 * t473 - 0.3e1 / 0.8e1 * t5 * t431 * t99 * t473 - 0.9e1 / 0.8e1 * t5 * t432 * t541 + t5 * t479 * t202 * t473 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t480 * t541 - 0.9e1 / 0.8e1 * t5 * t484 * t688 - 0.5e1 / 0.36e2 * t5 * t546 * t735 * t473 + t5 * t547 * t541 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t551 * t688 - 0.3e1 / 0.8e1 * t5 * t555 * (0.2e1 / 0.9e1 * t1403 * s2 * t438 * t470 - 0.18e2 * t655 * t526 * t532 * t75 * t77 * t535 * t457 * t462 * t521 + 0.324e3 * t1417 * t669 * t673 * t162 * t677 * t460 * t678 - 0.6e1 * t1417 * t526 * t532 * t162 * t536 - 0.2430e4 * t1430 * t1431 / t436 / t671 / t434 * t72 * t162 / t467 / t675 / t466 * t678 * t462 * t1417 + 0.162e3 * t670 * t673 * t75 * t77 * t677 * t678 * t521 * t655 - 0.2e1 * t533 * t162 * t536 * t1403))
  d111 = 0.3e1 * t412 + 0.3e1 * t693 + t6 * (t1154 + t1464)

  res = {'v3rho3': d111}
  return res
