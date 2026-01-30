"""Generated from gga_x_ncap.mpl."""

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
  params_zeta_raw = params.zeta
  if isinstance(params_zeta_raw, (str, bytes, dict)):
    params_zeta = params_zeta_raw
  else:
    try:
      params_zeta_seq = list(params_zeta_raw)
    except TypeError:
      params_zeta = params_zeta_raw
    else:
      params_zeta_seq = np.asarray(params_zeta_seq, dtype=np.float64)
      params_zeta = np.concatenate((np.array([np.nan], dtype=np.float64), params_zeta_seq))

  ncap_f0 = lambda s: 1 + params_mu * jnp.tanh(s) * jnp.arcsinh(s) * (1 + params_alpha * ((1 - params_zeta) * s * jnp.log(1 + s) + params_zeta * s)) / (1 + params_beta * jnp.tanh(s) * jnp.arcsinh(s))

  ncap_f = lambda x: ncap_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ncap_f, rs, zeta, xs0, xs1)

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
  params_zeta_raw = params.zeta
  if isinstance(params_zeta_raw, (str, bytes, dict)):
    params_zeta = params_zeta_raw
  else:
    try:
      params_zeta_seq = list(params_zeta_raw)
    except TypeError:
      params_zeta = params_zeta_raw
    else:
      params_zeta_seq = np.asarray(params_zeta_seq, dtype=np.float64)
      params_zeta = np.concatenate((np.array([np.nan], dtype=np.float64), params_zeta_seq))

  ncap_f0 = lambda s: 1 + params_mu * jnp.tanh(s) * jnp.arcsinh(s) * (1 + params_alpha * ((1 - params_zeta) * s * jnp.log(1 + s) + params_zeta * s)) / (1 + params_beta * jnp.tanh(s) * jnp.arcsinh(s))

  ncap_f = lambda x: ncap_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ncap_f, rs, zeta, xs0, xs1)

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
  params_zeta_raw = params.zeta
  if isinstance(params_zeta_raw, (str, bytes, dict)):
    params_zeta = params_zeta_raw
  else:
    try:
      params_zeta_seq = list(params_zeta_raw)
    except TypeError:
      params_zeta = params_zeta_raw
    else:
      params_zeta_seq = np.asarray(params_zeta_seq, dtype=np.float64)
      params_zeta = np.concatenate((np.array([np.nan], dtype=np.float64), params_zeta_seq))

  ncap_f0 = lambda s: 1 + params_mu * jnp.tanh(s) * jnp.arcsinh(s) * (1 + params_alpha * ((1 - params_zeta) * s * jnp.log(1 + s) + params_zeta * s)) / (1 + params_beta * jnp.tanh(s) * jnp.arcsinh(s))

  ncap_f = lambda x: ncap_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ncap_f, rs, zeta, xs0, xs1)

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
  t29 = t28 ** 2
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = t29 * t32
  t34 = jnp.sqrt(s0)
  t35 = r0 ** (0.1e1 / 0.3e1)
  t37 = 0.1e1 / t35 / r0
  t38 = t34 * t37
  t40 = t33 * t38 / 0.12e2
  t41 = jnp.tanh(t40)
  t42 = params.mu * t41
  t43 = jnp.arcsinh(t40)
  t44 = 0.1e1 - params.zeta
  t46 = t44 * t29 * t32
  t47 = 0.1e1 + t40
  t48 = jnp.log(t47)
  t51 = params.zeta * t29
  t52 = t32 * t34
  t58 = 0.1e1 + params.alpha * (t51 * t52 * t37 / 0.12e2 + t46 * t38 * t48 / 0.12e2)
  t60 = params.beta * t41
  t62 = t60 * t43 + 0.1e1
  t63 = 0.1e1 / t62
  t64 = t43 * t58 * t63
  t66 = t42 * t64 + 0.1e1
  t70 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t66)
  t71 = r1 <= f.p.dens_threshold
  t72 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t73 = 0.1e1 + t72
  t74 = t73 <= f.p.zeta_threshold
  t75 = t73 ** (0.1e1 / 0.3e1)
  t77 = f.my_piecewise3(t74, t22, t75 * t73)
  t78 = t77 * t26
  t79 = jnp.sqrt(s2)
  t80 = r1 ** (0.1e1 / 0.3e1)
  t82 = 0.1e1 / t80 / r1
  t83 = t79 * t82
  t85 = t33 * t83 / 0.12e2
  t86 = jnp.tanh(t85)
  t87 = params.mu * t86
  t88 = jnp.arcsinh(t85)
  t89 = 0.1e1 + t85
  t90 = jnp.log(t89)
  t93 = t32 * t79
  t99 = 0.1e1 + params.alpha * (t46 * t83 * t90 / 0.12e2 + t51 * t93 * t82 / 0.12e2)
  t101 = params.beta * t86
  t103 = t101 * t88 + 0.1e1
  t104 = 0.1e1 / t103
  t105 = t88 * t99 * t104
  t107 = t87 * t105 + 0.1e1
  t111 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t78 * t107)
  t112 = t6 ** 2
  t114 = t16 / t112
  t115 = t7 - t114
  t116 = f.my_piecewise5(t10, 0, t14, 0, t115)
  t119 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t116)
  t124 = t26 ** 2
  t125 = 0.1e1 / t124
  t129 = t5 * t25 * t125 * t66 / 0.8e1
  t130 = t41 ** 2
  t131 = 0.1e1 - t130
  t133 = params.mu * t131 * t33
  t134 = r0 ** 2
  t136 = 0.1e1 / t35 / t134
  t137 = t34 * t136
  t141 = t42 * t33
  t142 = t31 ** 2
  t143 = 0.1e1 / t142
  t144 = t28 * t143
  t145 = t35 ** 2
  t147 = 0.1e1 / t145 / t134
  t152 = jnp.sqrt(0.6e1 * t144 * s0 * t147 + 0.144e3)
  t153 = 0.1e1 / t152
  t155 = t153 * t58 * t63
  t159 = t42 * t43
  t163 = t44 * t28
  t164 = t163 * t143
  t169 = 0.1e1 / t47
  t180 = t62 ** 2
  t182 = t58 / t180
  t184 = params.beta * t131 * t29
  t189 = t60 * t29
  t202 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t119 * t26 * t66 - t129 - 0.3e1 / 0.8e1 * t5 * t27 * (-t133 * t137 * t64 / 0.9e1 - 0.4e1 / 0.3e1 * t141 * t137 * t155 + t159 * params.alpha * (-t46 * t137 * t48 / 0.9e1 - t164 * s0 / t145 / t134 / r0 * t169 / 0.18e2 - t51 * t52 * t136 / 0.9e1) * t63 - t159 * t182 * (-t184 * t52 * t136 * t43 / 0.9e1 - 0.4e1 / 0.3e1 * t189 * t52 * t136 * t153)))
  t204 = f.my_piecewise5(t14, 0, t10, 0, -t115)
  t207 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t75 * t204)
  t215 = t5 * t77 * t125 * t107 / 0.8e1
  t217 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t207 * t26 * t107 - t215)
  vrho_0_ = t70 + t111 + t6 * (t202 + t217)
  t220 = -t7 - t114
  t221 = f.my_piecewise5(t10, 0, t14, 0, t220)
  t224 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t221)
  t230 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t224 * t26 * t66 - t129)
  t232 = f.my_piecewise5(t14, 0, t10, 0, -t220)
  t235 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t75 * t232)
  t240 = t86 ** 2
  t241 = 0.1e1 - t240
  t243 = params.mu * t241 * t33
  t244 = r1 ** 2
  t246 = 0.1e1 / t80 / t244
  t247 = t79 * t246
  t251 = t87 * t33
  t252 = t80 ** 2
  t254 = 0.1e1 / t252 / t244
  t259 = jnp.sqrt(0.6e1 * t144 * s2 * t254 + 0.144e3)
  t260 = 0.1e1 / t259
  t262 = t260 * t99 * t104
  t266 = t87 * t88
  t274 = 0.1e1 / t89
  t285 = t103 ** 2
  t287 = t99 / t285
  t289 = params.beta * t241 * t29
  t294 = t101 * t29
  t307 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t235 * t26 * t107 - t215 - 0.3e1 / 0.8e1 * t5 * t78 * (-t243 * t247 * t105 / 0.9e1 - 0.4e1 / 0.3e1 * t251 * t247 * t262 + t266 * params.alpha * (-t46 * t247 * t90 / 0.9e1 - t164 * s2 / t252 / t244 / r1 * t274 / 0.18e2 - t51 * t93 * t246 / 0.9e1) * t104 - t266 * t287 * (-t289 * t93 * t246 * t88 / 0.9e1 - 0.4e1 / 0.3e1 * t294 * t93 * t246 * t260)))
  vrho_1_ = t70 + t111 + t6 * (t230 + t307)
  t310 = 0.1e1 / t34
  t311 = t310 * t37
  t325 = t32 * t310
  t348 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t133 * t311 * t64 / 0.24e2 + t141 * t311 * t155 / 0.2e1 + t159 * params.alpha * (t46 * t311 * t48 / 0.24e2 + t163 * t143 * t147 * t169 / 0.48e2 + t51 * t325 * t37 / 0.24e2) * t63 - t159 * t182 * (t184 * t325 * t37 * t43 / 0.24e2 + t189 * t325 * t37 * t153 / 0.2e1)))
  vsigma_0_ = t6 * t348
  vsigma_1_ = 0.0e0
  t349 = 0.1e1 / t79
  t350 = t349 * t82
  t364 = t32 * t349
  t387 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t78 * (t243 * t350 * t105 / 0.24e2 + t251 * t350 * t262 / 0.2e1 + t266 * params.alpha * (t46 * t350 * t90 / 0.24e2 + t163 * t143 * t254 * t274 / 0.48e2 + t51 * t364 * t82 / 0.24e2) * t104 - t266 * t287 * (t289 * t364 * t82 * t88 / 0.24e2 + t294 * t364 * t82 * t260 / 0.2e1)))
  vsigma_2_ = t6 * t387
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
  params_zeta_raw = params.zeta
  if isinstance(params_zeta_raw, (str, bytes, dict)):
    params_zeta = params_zeta_raw
  else:
    try:
      params_zeta_seq = list(params_zeta_raw)
    except TypeError:
      params_zeta = params_zeta_raw
    else:
      params_zeta_seq = np.asarray(params_zeta_seq, dtype=np.float64)
      params_zeta = np.concatenate((np.array([np.nan], dtype=np.float64), params_zeta_seq))

  ncap_f0 = lambda s: 1 + params_mu * jnp.tanh(s) * jnp.arcsinh(s) * (1 + params_alpha * ((1 - params_zeta) * s * jnp.log(1 + s) + params_zeta * s)) / (1 + params_beta * jnp.tanh(s) * jnp.arcsinh(s))

  ncap_f = lambda x: ncap_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ncap_f, rs, zeta, xs0, xs1)

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
  t21 = t20 ** 2
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t23
  t25 = t21 * t24
  t26 = jnp.sqrt(s0)
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t26 * t27
  t30 = 0.1e1 / t18 / r0
  t31 = t28 * t30
  t33 = t25 * t31 / 0.12e2
  t34 = jnp.tanh(t33)
  t35 = params.mu * t34
  t36 = jnp.arcsinh(t33)
  t37 = 0.1e1 - params.zeta
  t39 = t37 * t21 * t24
  t40 = 0.1e1 + t33
  t41 = jnp.log(t40)
  t42 = t30 * t41
  t46 = params.zeta * t21 * t24
  t51 = 0.1e1 + params.alpha * (t39 * t28 * t42 / 0.12e2 + t46 * t31 / 0.12e2)
  t53 = params.beta * t34
  t55 = t53 * t36 + 0.1e1
  t56 = 0.1e1 / t55
  t57 = t36 * t51 * t56
  t59 = t35 * t57 + 0.1e1
  t63 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t59)
  t64 = t18 ** 2
  t70 = t34 ** 2
  t71 = 0.1e1 - t70
  t72 = params.mu * t71
  t73 = t25 * t26
  t75 = r0 ** 2
  t77 = 0.1e1 / t18 / t75
  t78 = t27 * t77
  t83 = t23 ** 2
  t84 = 0.1e1 / t83
  t86 = t27 ** 2
  t87 = s0 * t86
  t89 = 0.1e1 / t64 / t75
  t94 = jnp.sqrt(0.6e1 * t20 * t84 * t87 * t89 + 0.144e3)
  t95 = 0.1e1 / t94
  t97 = t95 * t51 * t56
  t101 = t35 * t36
  t107 = t37 * t20 * t84
  t111 = 0.1e1 / t40
  t123 = t55 ** 2
  t125 = t51 / t123
  t127 = params.beta * t71 * t25
  t132 = t53 * t25
  t145 = f.my_piecewise3(t2, 0, -t6 * t17 / t64 * t59 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t72 * t73 * t78 * t57 / 0.9e1 - 0.4e1 / 0.3e1 * t35 * t73 * t78 * t97 + t101 * params.alpha * (-t39 * t28 * t77 * t41 / 0.9e1 - t107 * t87 / t64 / t75 / r0 * t111 / 0.18e2 - t46 * t28 * t77 / 0.9e1) * t56 - t101 * t125 * (-t127 * t28 * t77 * t36 / 0.9e1 - 0.4e1 / 0.3e1 * t132 * t28 * t77 * t95)))
  vrho_0_ = 0.2e1 * r0 * t145 + 0.2e1 * t63
  t148 = 0.1e1 / t26
  t149 = t25 * t148
  t151 = t27 * t30
  t159 = t148 * t27
  t189 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t72 * t149 * t151 * t57 / 0.24e2 + t35 * t149 * t151 * t97 / 0.2e1 + t101 * params.alpha * (t39 * t159 * t42 / 0.24e2 + t107 * t86 * t89 * t111 / 0.48e2 + t46 * t159 * t30 / 0.24e2) * t56 - t101 * t125 * (t127 * t159 * t30 * t36 / 0.24e2 + t132 * t159 * t30 * t95 / 0.2e1)))
  vsigma_0_ = 0.2e1 * r0 * t189
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
  t23 = t22 ** 2
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t27 = t23 * t26
  t28 = jnp.sqrt(s0)
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t28 * t29
  t32 = 0.1e1 / t18 / r0
  t33 = t30 * t32
  t35 = t27 * t33 / 0.12e2
  t36 = jnp.tanh(t35)
  t37 = params.mu * t36
  t38 = jnp.arcsinh(t35)
  t39 = 0.1e1 - params.zeta
  t41 = t39 * t23 * t26
  t42 = 0.1e1 + t35
  t43 = jnp.log(t42)
  t44 = t32 * t43
  t48 = params.zeta * t23 * t26
  t53 = 0.1e1 + params.alpha * (t41 * t30 * t44 / 0.12e2 + t48 * t33 / 0.12e2)
  t55 = params.beta * t36
  t57 = t55 * t38 + 0.1e1
  t58 = 0.1e1 / t57
  t59 = t38 * t53 * t58
  t61 = t37 * t59 + 0.1e1
  t65 = t17 * t18
  t66 = t36 ** 2
  t67 = 0.1e1 - t66
  t68 = params.mu * t67
  t69 = t27 * t28
  t70 = t68 * t69
  t71 = r0 ** 2
  t73 = 0.1e1 / t18 / t71
  t74 = t29 * t73
  t75 = t74 * t59
  t78 = t37 * t69
  t79 = t25 ** 2
  t80 = 0.1e1 / t79
  t81 = t22 * t80
  t82 = t29 ** 2
  t83 = s0 * t82
  t85 = 0.1e1 / t19 / t71
  t89 = 0.6e1 * t81 * t83 * t85 + 0.144e3
  t90 = jnp.sqrt(t89)
  t91 = 0.1e1 / t90
  t93 = t91 * t53 * t58
  t94 = t74 * t93
  t97 = t37 * t38
  t98 = t73 * t43
  t103 = t39 * t22 * t80
  t104 = t71 * r0
  t106 = 0.1e1 / t19 / t104
  t107 = 0.1e1 / t42
  t116 = params.alpha * (-t41 * t30 * t98 / 0.9e1 - t103 * t83 * t106 * t107 / 0.18e2 - t48 * t30 * t73 / 0.9e1)
  t117 = t116 * t58
  t119 = t57 ** 2
  t120 = 0.1e1 / t119
  t121 = t53 * t120
  t122 = params.beta * t67
  t123 = t122 * t27
  t124 = t73 * t38
  t128 = t55 * t27
  t129 = t73 * t91
  t133 = -t123 * t30 * t124 / 0.9e1 - 0.4e1 / 0.3e1 * t128 * t30 * t129
  t134 = t121 * t133
  t136 = -t70 * t75 / 0.9e1 - 0.4e1 / 0.3e1 * t78 * t94 + t97 * t117 - t97 * t134
  t141 = f.my_piecewise3(t2, 0, -t6 * t21 * t61 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t65 * t136)
  t152 = t67 * t22
  t154 = t37 * t152 * t80
  t155 = t71 ** 2
  t157 = 0.1e1 / t19 / t155
  t163 = 0.1e1 / t18 / t104
  t164 = t29 * t163
  t170 = t82 * t157
  t174 = t74 * t38
  t184 = 0.1e1 / t24
  t185 = t28 * s0
  t189 = 0.1e1 / t155 / t71
  t191 = 0.1e1 / t90 / t89
  t193 = t53 * t58
  t197 = t74 * t91
  t212 = t39 * t184
  t213 = t185 * t189
  t214 = t42 ** 2
  t215 = 0.1e1 / t214
  t226 = t120 * t133
  t232 = t53 / t119 / t57
  t233 = t133 ** 2
  t237 = t55 * t152
  t247 = t122 * t81
  t256 = t55 * t184
  t263 = -0.4e1 / 0.27e2 * t154 * t83 * t157 * t59 + 0.7e1 / 0.27e2 * t70 * t164 * t59 + 0.16e2 / 0.9e1 * t68 * t81 * s0 * t170 * t93 - 0.2e1 / 0.9e1 * t70 * t174 * t117 + 0.2e1 / 0.9e1 * t70 * t174 * t134 + 0.28e2 / 0.9e1 * t78 * t164 * t93 - 0.128e3 * t37 * t184 * t185 * t189 * t191 * t193 - 0.8e1 / 0.3e1 * t78 * t197 * t117 + 0.8e1 / 0.3e1 * t78 * t197 * t134 + t97 * params.alpha * (0.7e1 / 0.27e2 * t41 * t30 * t163 * t43 + 0.5e1 / 0.18e2 * t103 * t83 * t157 * t107 - 0.2e1 / 0.27e2 * t212 * t213 * t215 + 0.7e1 / 0.27e2 * t48 * t30 * t163) * t58 - 0.2e1 * t97 * t116 * t226 + 0.2e1 * t97 * t232 * t233 - t97 * t121 * (-0.4e1 / 0.27e2 * t237 * t80 * s0 * t170 * t38 + 0.7e1 / 0.27e2 * t123 * t30 * t163 * t38 + 0.16e2 / 0.9e1 * t247 * t83 * t157 * t91 + 0.28e2 / 0.9e1 * t128 * t30 * t163 * t91 - 0.128e3 * t256 * t213 * t191)
  t268 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t61 / 0.12e2 - t6 * t21 * t136 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t65 * t263)
  v2rho2_0_ = 0.2e1 * r0 * t268 + 0.4e1 * t141
  t271 = 0.1e1 / t28
  t272 = t27 * t271
  t273 = t68 * t272
  t274 = t29 * t32
  t275 = t274 * t59
  t278 = t37 * t272
  t279 = t274 * t93
  t282 = t271 * t29
  t286 = t82 * t85
  t294 = params.alpha * (t41 * t282 * t44 / 0.24e2 + t103 * t286 * t107 / 0.48e2 + t48 * t282 * t32 / 0.24e2)
  t295 = t294 * t58
  t297 = t32 * t38
  t301 = t32 * t91
  t305 = t123 * t282 * t297 / 0.24e2 + t128 * t282 * t301 / 0.2e1
  t306 = t121 * t305
  t308 = t273 * t275 / 0.24e2 + t278 * t279 / 0.2e1 + t97 * t295 - t97 * t306
  t312 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t65 * t308)
  t316 = t82 * t106
  t326 = t274 * t38
  t338 = 0.1e1 / t155 / r0
  t343 = t274 * t91
  t381 = t120 * t305
  t388 = t80 * t82
  t411 = t154 * t316 * t59 / 0.18e2 - t273 * t75 / 0.18e2 - 0.2e1 / 0.3e1 * t68 * t81 * t316 * t93 + t273 * t326 * t117 / 0.24e2 - t273 * t326 * t134 / 0.24e2 - 0.2e1 / 0.3e1 * t278 * t94 + 0.48e2 * t37 * t184 * t28 * t338 * t191 * t193 + t278 * t343 * t117 / 0.2e1 - t278 * t343 * t134 / 0.2e1 - t70 * t174 * t295 / 0.9e1 - 0.4e1 / 0.3e1 * t78 * t197 * t295 + t97 * params.alpha * (-t41 * t282 * t98 / 0.18e2 - t103 * t316 * t107 / 0.12e2 + t212 * t338 * t215 * t28 / 0.36e2 - t48 * t282 * t73 / 0.18e2) * t58 - t97 * t294 * t226 + t70 * t174 * t306 / 0.9e1 + 0.4e1 / 0.3e1 * t78 * t197 * t306 - t97 * t116 * t381 + 0.2e1 * t97 * t232 * t305 * t133 - t97 * t121 * (t237 * t388 * t106 * t38 / 0.18e2 - t123 * t282 * t124 / 0.18e2 - 0.2e1 / 0.3e1 * t122 * t22 * t388 * t106 * t91 - 0.2e1 / 0.3e1 * t128 * t282 * t129 + 0.48e2 * t256 * t28 * t338 * t191)
  t416 = f.my_piecewise3(t2, 0, -t6 * t21 * t308 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t65 * t411)
  v2rhosigma_0_ = 0.2e1 * r0 * t416 + 0.2e1 * t312
  t419 = 0.1e1 / s0
  t420 = t419 * t82
  t425 = 0.1e1 / t185
  t426 = t27 * t425
  t446 = 0.1e1 / t155
  t455 = t425 * t29
  t477 = t305 ** 2
  t503 = -t154 * t420 * t85 * t59 / 0.48e2 - t68 * t426 * t275 / 0.48e2 + t68 * t81 * t419 * t286 * t93 / 0.4e1 + t273 * t326 * t295 / 0.12e2 - t273 * t326 * t306 / 0.12e2 - t37 * t426 * t279 / 0.4e1 - 0.18e2 * t37 * t184 * t271 * t446 * t191 * t193 + t278 * t343 * t295 - t278 * t343 * t306 + t97 * params.alpha * (-t41 * t455 * t44 / 0.48e2 + t103 * t420 * t85 * t107 / 0.96e2 - t212 * t446 * t215 * t271 / 0.96e2 - t48 * t455 * t32 / 0.48e2) * t58 - 0.2e1 * t97 * t294 * t381 + 0.2e1 * t97 * t232 * t477 - t97 * t121 * (-t237 * t80 * t419 * t286 * t38 / 0.48e2 - t123 * t455 * t297 / 0.48e2 + t247 * t420 * t85 * t91 / 0.4e1 - t128 * t455 * t301 / 0.4e1 - 0.18e2 * t256 * t271 * t446 * t191)
  t507 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t65 * t503)
  v2sigma2_0_ = 0.2e1 * r0 * t507
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
  t24 = t23 ** 2
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t26
  t28 = t24 * t27
  t29 = jnp.sqrt(s0)
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t29 * t30
  t33 = 0.1e1 / t18 / r0
  t34 = t31 * t33
  t36 = t28 * t34 / 0.12e2
  t37 = jnp.tanh(t36)
  t38 = params.mu * t37
  t39 = jnp.asinh(t36)
  t40 = 0.1e1 - params.zeta
  t42 = t40 * t24 * t27
  t43 = 0.1e1 + t36
  t44 = jnp.log(t43)
  t49 = params.zeta * t24 * t27
  t54 = 0.1e1 + params.alpha * (t42 * t31 * t33 * t44 / 0.12e2 + t49 * t34 / 0.12e2)
  t56 = params.beta * t37
  t58 = t56 * t39 + 0.1e1
  t59 = 0.1e1 / t58
  t60 = t39 * t54 * t59
  t62 = t38 * t60 + 0.1e1
  t67 = t17 / t19
  t68 = t37 ** 2
  t69 = 0.1e1 - t68
  t70 = params.mu * t69
  t71 = t28 * t29
  t72 = t70 * t71
  t73 = r0 ** 2
  t75 = 0.1e1 / t18 / t73
  t76 = t30 * t75
  t80 = t38 * t71
  t81 = t26 ** 2
  t82 = 0.1e1 / t81
  t83 = t23 * t82
  t84 = t30 ** 2
  t85 = s0 * t84
  t87 = 0.1e1 / t19 / t73
  t91 = 0.6e1 * t83 * t85 * t87 + 0.144e3
  t92 = jnp.sqrt(t91)
  t93 = 0.1e1 / t92
  t95 = t93 * t54 * t59
  t99 = t38 * t39
  t105 = t40 * t23 * t82
  t106 = t73 * r0
  t109 = 0.1e1 / t43
  t117 = -t42 * t31 * t75 * t44 / 0.9e1 - t105 * t85 / t19 / t106 * t109 / 0.18e2 - t49 * t31 * t75 / 0.9e1
  t118 = params.alpha * t117
  t119 = t118 * t59
  t121 = t58 ** 2
  t122 = 0.1e1 / t121
  t123 = t54 * t122
  t124 = params.beta * t69
  t125 = t124 * t28
  t126 = t75 * t39
  t130 = t56 * t28
  t131 = t75 * t93
  t135 = -t125 * t31 * t126 / 0.9e1 - 0.4e1 / 0.3e1 * t130 * t31 * t131
  t136 = t123 * t135
  t138 = -t72 * t76 * t60 / 0.9e1 - 0.4e1 / 0.3e1 * t80 * t76 * t95 + t99 * t119 - t99 * t136
  t142 = t17 * t18
  t143 = t69 * t23
  t145 = t38 * t143 * t82
  t146 = t73 ** 2
  t148 = 0.1e1 / t19 / t146
  t154 = 0.1e1 / t18 / t106
  t155 = t30 * t154
  t159 = t83 * s0
  t160 = t70 * t159
  t161 = t84 * t148
  t165 = t76 * t39
  t175 = 0.1e1 / t25
  t176 = t29 * s0
  t177 = t175 * t176
  t178 = t38 * t177
  t180 = 0.1e1 / t146 / t73
  t182 = 0.1e1 / t92 / t91
  t183 = t180 * t182
  t184 = t54 * t59
  t188 = t76 * t93
  t203 = t40 * t175
  t204 = t176 * t180
  t205 = t43 ** 2
  t206 = 0.1e1 / t205
  t214 = params.alpha * (0.7e1 / 0.27e2 * t42 * t31 * t154 * t44 + 0.5e1 / 0.18e2 * t105 * t85 * t148 * t109 - 0.2e1 / 0.27e2 * t203 * t204 * t206 + 0.7e1 / 0.27e2 * t49 * t31 * t154)
  t215 = t214 * t59
  t217 = t122 * t135
  t222 = 0.1e1 / t121 / t58
  t223 = t54 * t222
  t224 = t135 ** 2
  t225 = t223 * t224
  t228 = t56 * t143
  t229 = t82 * s0
  t230 = t161 * t39
  t238 = t124 * t83
  t247 = t56 * t175
  t251 = -0.4e1 / 0.27e2 * t228 * t229 * t230 + 0.7e1 / 0.27e2 * t125 * t31 * t154 * t39 + 0.16e2 / 0.9e1 * t238 * t85 * t148 * t93 + 0.28e2 / 0.9e1 * t130 * t31 * t154 * t93 - 0.128e3 * t247 * t204 * t182
  t252 = t123 * t251
  t254 = -0.4e1 / 0.27e2 * t145 * t85 * t148 * t60 + 0.7e1 / 0.27e2 * t72 * t155 * t60 + 0.16e2 / 0.9e1 * t160 * t161 * t95 - 0.2e1 / 0.9e1 * t72 * t165 * t119 + 0.2e1 / 0.9e1 * t72 * t165 * t136 + 0.28e2 / 0.9e1 * t80 * t155 * t95 - 0.128e3 * t178 * t183 * t184 - 0.8e1 / 0.3e1 * t80 * t188 * t119 + 0.8e1 / 0.3e1 * t80 * t188 * t136 + t99 * t215 - 0.2e1 * t99 * t118 * t217 + 0.2e1 * t99 * t225 - t99 * t252
  t259 = f.my_piecewise3(t2, 0, t6 * t22 * t62 / 0.12e2 - t6 * t67 * t138 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t142 * t254)
  t286 = t69 ** 2
  t290 = 0.1e1 / t146 / t106
  t291 = t290 * t39
  t301 = t176 * t290
  t312 = 0.1e1 / t19 / t146 / r0
  t313 = t84 * t312
  t324 = 0.1e1 / t18 / t146
  t335 = t24 / t26 / t25
  t337 = s0 ** 2
  t338 = t337 * t30
  t339 = t146 ** 2
  t341 = 0.1e1 / t18 / t339
  t359 = t175 * t29 * t337
  t363 = 0.1e1 / t19 / t339 / r0
  t364 = t91 ** 2
  t366 = 0.1e1 / t92 / t364
  t368 = t83 * t84
  t372 = 0.16e2 / 0.81e2 * params.beta * t286 * t175 * t301 * t39 - 0.32e2 / 0.81e2 * params.beta * t68 * t69 * t177 * t291 + 0.28e2 / 0.27e2 * t228 * t229 * t313 * t39 + 0.64e2 / 0.9e1 * t56 * t69 * t177 * t290 * t93 - 0.70e2 / 0.81e2 * t125 * t31 * t324 * t39 - 0.112e3 / 0.9e1 * t238 * t85 * t312 * t93 + 0.256e3 / 0.9e1 * t124 * t335 * t338 * t341 * t182 - 0.280e3 / 0.27e2 * t130 * t31 * t324 * t93 + 0.3200e4 / 0.3e1 * t247 * t301 * t182 + 0.128e3 / 0.9e1 * t125 * t338 * t341 * t175 * t182 - 0.3072e4 * t56 * t359 * t363 * t366 * t368
  t375 = t121 ** 2
  t411 = t27 * t29 * t30
  t415 = t117 * t122 * t135
  t426 = t38 * t69 * t159
  t438 = t30 * t341
  t440 = t182 * t54 * t59
  t444 = t30 * t324
  t452 = t69 * t175
  t457 = -0.3e1 * t99 * t214 * t217 - 0.3e1 * t99 * t118 * t122 * t251 + 0.6e1 * t99 * t223 * t135 * t251 + 0.6e1 * t99 * t118 * t222 * t224 + 0.16e2 / 0.81e2 * params.mu * t286 * t177 * t291 * t184 + 0.3200e4 / 0.3e1 * t178 * t290 * t182 * t184 - t99 * t123 * t372 - 0.6e1 * t99 * t54 / t375 * t224 * t135 + t99 * params.alpha * (-0.70e2 / 0.81e2 * t42 * t31 * t324 * t44 - 0.119e3 / 0.81e2 * t105 * t85 * t312 * t109 + 0.22e2 / 0.27e2 * t203 * t301 * t206 - 0.4e1 / 0.243e3 * t203 * t337 * t341 / t205 / t43 * t24 * t27 * t30 - 0.70e2 / 0.81e2 * t49 * t31 * t324) * t59 + 0.8e1 * t38 * t24 * t411 * t131 * params.alpha * t415 + 0.2e1 / 0.3e1 * t70 * t24 * t411 * t126 * params.alpha * t415 + 0.4e1 / 0.9e1 * t426 * t230 * t136 - 0.4e1 / 0.9e1 * t426 * t230 * t119 - 0.112e3 / 0.9e1 * t160 * t313 * t95 + 0.256e3 / 0.9e1 * t70 * t335 * t337 * t438 * t440 - 0.70e2 / 0.81e2 * t72 * t444 * t60 - 0.280e3 / 0.27e2 * t80 * t444 * t95 - 0.32e2 / 0.81e2 * params.mu * t68 * t452 * t301 * t60
  t478 = t155 * t39
  t485 = t161 * t93
  t498 = t155 * t93
  t524 = 0.64e2 / 0.9e1 * t38 * t452 * t301 * t95 + 0.384e3 * t178 * t183 * t136 - 0.384e3 * t178 * t183 * t119 - 0.8e1 * t80 * t188 * t225 - 0.2e1 / 0.3e1 * t72 * t165 * t225 + 0.28e2 / 0.27e2 * t145 * t85 * t312 * t60 - 0.7e1 / 0.9e1 * t72 * t478 * t136 + 0.7e1 / 0.9e1 * t72 * t478 * t119 - 0.16e2 / 0.3e1 * t160 * t485 * t136 + 0.16e2 / 0.3e1 * t160 * t485 * t119 - t72 * t165 * t215 / 0.3e1 + t72 * t165 * t252 / 0.3e1 - 0.28e2 / 0.3e1 * t80 * t498 * t136 + 0.28e2 / 0.3e1 * t80 * t498 * t119 + 0.128e3 / 0.9e1 * t70 * t28 * t337 * t438 * t175 * t440 - 0.3072e4 * t38 * t359 * t363 * t366 * t54 * t59 * t368 - 0.4e1 * t80 * t188 * t215 + 0.4e1 * t80 * t188 * t252
  t530 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t87 * t62 + t6 * t22 * t138 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t67 * t254 - 0.3e1 / 0.8e1 * t6 * t142 * (t457 + t524))
  v3rho3_0_ = 0.2e1 * r0 * t530 + 0.6e1 * t259

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
  t25 = t24 ** 2
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = 0.1e1 / t27
  t29 = t25 * t28
  t30 = jnp.sqrt(s0)
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t30 * t31
  t34 = 0.1e1 / t19 / r0
  t35 = t32 * t34
  t37 = t29 * t35 / 0.12e2
  t38 = jnp.tanh(t37)
  t39 = params.mu * t38
  t40 = jnp.asinh(t37)
  t41 = 0.1e1 - params.zeta
  t43 = t41 * t25 * t28
  t44 = 0.1e1 + t37
  t45 = jnp.log(t44)
  t50 = params.zeta * t25 * t28
  t55 = 0.1e1 + params.alpha * (t43 * t32 * t34 * t45 / 0.12e2 + t50 * t35 / 0.12e2)
  t57 = params.beta * t38
  t59 = t57 * t40 + 0.1e1
  t60 = 0.1e1 / t59
  t61 = t40 * t55 * t60
  t63 = t39 * t61 + 0.1e1
  t69 = t17 / t20 / r0
  t70 = t38 ** 2
  t71 = 0.1e1 - t70
  t72 = params.mu * t71
  t73 = t29 * t30
  t74 = t72 * t73
  t76 = 0.1e1 / t19 / t18
  t77 = t31 * t76
  t81 = t39 * t73
  t82 = t27 ** 2
  t83 = 0.1e1 / t82
  t84 = t24 * t83
  t85 = t31 ** 2
  t86 = s0 * t85
  t90 = 0.6e1 * t84 * t86 * t22 + 0.144e3
  t91 = jnp.sqrt(t90)
  t92 = 0.1e1 / t91
  t94 = t92 * t55 * t60
  t98 = t39 * t40
  t104 = t41 * t24 * t83
  t105 = t18 * r0
  t107 = 0.1e1 / t20 / t105
  t108 = 0.1e1 / t44
  t116 = -t43 * t32 * t76 * t45 / 0.9e1 - t104 * t86 * t107 * t108 / 0.18e2 - t50 * t32 * t76 / 0.9e1
  t117 = params.alpha * t116
  t118 = t117 * t60
  t120 = t59 ** 2
  t121 = 0.1e1 / t120
  t122 = t55 * t121
  t123 = params.beta * t71
  t124 = t123 * t29
  t125 = t76 * t40
  t129 = t57 * t29
  t130 = t76 * t92
  t134 = -t124 * t32 * t125 / 0.9e1 - 0.4e1 / 0.3e1 * t129 * t32 * t130
  t135 = t122 * t134
  t137 = -t74 * t77 * t61 / 0.9e1 - 0.4e1 / 0.3e1 * t81 * t77 * t94 + t98 * t118 - t98 * t135
  t142 = t17 / t20
  t143 = t71 * t24
  t145 = t39 * t143 * t83
  t146 = t18 ** 2
  t148 = 0.1e1 / t20 / t146
  t154 = 0.1e1 / t19 / t105
  t155 = t31 * t154
  t159 = t84 * s0
  t160 = t72 * t159
  t161 = t85 * t148
  t165 = t77 * t40
  t175 = 0.1e1 / t26
  t176 = t30 * s0
  t177 = t175 * t176
  t178 = t39 * t177
  t179 = t146 * t18
  t180 = 0.1e1 / t179
  t182 = 0.1e1 / t91 / t90
  t183 = t180 * t182
  t184 = t55 * t60
  t188 = t77 * t92
  t203 = t41 * t175
  t204 = t176 * t180
  t205 = t44 ** 2
  t206 = 0.1e1 / t205
  t213 = 0.7e1 / 0.27e2 * t43 * t32 * t154 * t45 + 0.5e1 / 0.18e2 * t104 * t86 * t148 * t108 - 0.2e1 / 0.27e2 * t203 * t204 * t206 + 0.7e1 / 0.27e2 * t50 * t32 * t154
  t214 = params.alpha * t213
  t215 = t214 * t60
  t217 = t121 * t134
  t218 = t117 * t217
  t222 = 0.1e1 / t120 / t59
  t223 = t55 * t222
  t224 = t134 ** 2
  t225 = t223 * t224
  t228 = t57 * t143
  t229 = t83 * s0
  t230 = t161 * t40
  t234 = t154 * t40
  t238 = t123 * t84
  t239 = t148 * t92
  t243 = t154 * t92
  t247 = t57 * t175
  t251 = -0.4e1 / 0.27e2 * t228 * t229 * t230 + 0.7e1 / 0.27e2 * t124 * t32 * t234 + 0.16e2 / 0.9e1 * t238 * t86 * t239 + 0.28e2 / 0.9e1 * t129 * t32 * t243 - 0.128e3 * t247 * t204 * t182
  t252 = t122 * t251
  t254 = -0.4e1 / 0.27e2 * t145 * t86 * t148 * t61 + 0.7e1 / 0.27e2 * t74 * t155 * t61 + 0.16e2 / 0.9e1 * t160 * t161 * t94 - 0.2e1 / 0.9e1 * t74 * t165 * t118 + 0.2e1 / 0.9e1 * t74 * t165 * t135 + 0.28e2 / 0.9e1 * t81 * t155 * t94 - 0.128e3 * t178 * t183 * t184 - 0.8e1 / 0.3e1 * t81 * t188 * t118 + 0.8e1 / 0.3e1 * t81 * t188 * t135 + t98 * t215 - 0.2e1 * t98 * t218 + 0.2e1 * t98 * t225 - t98 * t252
  t258 = t17 * t19
  t262 = t121 * t251
  t266 = t134 * t251
  t270 = t222 * t224
  t274 = t71 ** 2
  t275 = params.mu * t274
  t276 = t275 * t177
  t278 = 0.1e1 / t146 / t105
  t279 = t278 * t40
  t283 = t278 * t182
  t289 = t28 * t30 * t31
  t290 = t39 * t25 * t289
  t291 = t130 * params.alpha
  t292 = t116 * t121
  t293 = t292 * t134
  t297 = t72 * t25
  t298 = t297 * t289
  t299 = t125 * params.alpha
  t303 = t39 * t71
  t304 = t303 * t159
  t311 = t146 * r0
  t313 = 0.1e1 / t20 / t311
  t314 = t85 * t313
  t320 = t25 / t27 / t26
  t321 = s0 ** 2
  t323 = t72 * t320 * t321
  t324 = t146 ** 2
  t326 = 0.1e1 / t19 / t324
  t327 = t31 * t326
  t329 = t182 * t55 * t60
  t334 = 0.1e1 / t19 / t146
  t335 = t31 * t334
  t342 = params.mu * t70
  t343 = t71 * t175
  t344 = t342 * t343
  t345 = t176 * t278
  t349 = t39 * t343
  t359 = -0.3e1 * t98 * t214 * t217 - 0.3e1 * t98 * t117 * t262 + 0.6e1 * t98 * t223 * t266 + 0.6e1 * t98 * t117 * t270 + 0.16e2 / 0.81e2 * t276 * t279 * t184 + 0.3200e4 / 0.3e1 * t178 * t283 * t184 + 0.8e1 * t290 * t291 * t293 + 0.2e1 / 0.3e1 * t298 * t299 * t293 + 0.4e1 / 0.9e1 * t304 * t230 * t135 - 0.4e1 / 0.9e1 * t304 * t230 * t118 - 0.112e3 / 0.9e1 * t160 * t314 * t94 + 0.256e3 / 0.9e1 * t323 * t327 * t329 - 0.70e2 / 0.81e2 * t74 * t335 * t61 - 0.280e3 / 0.27e2 * t81 * t335 * t94 - 0.32e2 / 0.81e2 * t344 * t345 * t61 + 0.64e2 / 0.9e1 * t349 * t345 * t94 + 0.384e3 * t178 * t183 * t135 - 0.384e3 * t178 * t183 * t118
  t360 = t120 ** 2
  t361 = 0.1e1 / t360
  t362 = t55 * t361
  t363 = t224 * t134
  t364 = t362 * t363
  t383 = t28 * t31
  t384 = 0.1e1 / t205 / t44 * t25 * t383
  t391 = params.alpha * (-0.70e2 / 0.81e2 * t43 * t32 * t334 * t45 - 0.119e3 / 0.81e2 * t104 * t86 * t313 * t108 + 0.22e2 / 0.27e2 * t203 * t345 * t206 - 0.4e1 / 0.243e3 * t203 * t321 * t326 * t384 - 0.70e2 / 0.81e2 * t50 * t32 * t334)
  t392 = t391 * t60
  t394 = params.beta * t274
  t395 = t394 * t175
  t399 = params.beta * t70
  t400 = t399 * t71
  t404 = t314 * t40
  t408 = t57 * t71
  t409 = t278 * t92
  t421 = t123 * t320
  t422 = t321 * t31
  t435 = t326 * t175 * t182
  t439 = t30 * t321
  t440 = t175 * t439
  t441 = t57 * t440
  t442 = t324 * r0
  t444 = 0.1e1 / t20 / t442
  t445 = t90 ** 2
  t447 = 0.1e1 / t91 / t445
  t449 = t84 * t85
  t453 = 0.16e2 / 0.81e2 * t395 * t345 * t40 - 0.32e2 / 0.81e2 * t400 * t177 * t279 + 0.28e2 / 0.27e2 * t228 * t229 * t404 + 0.64e2 / 0.9e1 * t408 * t177 * t409 - 0.70e2 / 0.81e2 * t124 * t32 * t334 * t40 - 0.112e3 / 0.9e1 * t238 * t86 * t313 * t92 + 0.256e3 / 0.9e1 * t421 * t422 * t326 * t182 - 0.280e3 / 0.27e2 * t129 * t32 * t334 * t92 + 0.3200e4 / 0.3e1 * t247 * t345 * t182 + 0.128e3 / 0.9e1 * t124 * t422 * t435 - 0.3072e4 * t441 * t444 * t447 * t449
  t454 = t122 * t453
  t466 = t155 * t40
  t473 = t161 * t92
  t486 = t155 * t92
  t493 = t29 * t321
  t494 = t72 * t493
  t503 = t447 * t55 * t60 * t449
  t512 = -0.6e1 * t98 * t364 + t98 * t392 - t98 * t454 - 0.8e1 * t81 * t188 * t225 - 0.2e1 / 0.3e1 * t74 * t165 * t225 + 0.28e2 / 0.27e2 * t145 * t86 * t313 * t61 - 0.7e1 / 0.9e1 * t74 * t466 * t135 + 0.7e1 / 0.9e1 * t74 * t466 * t118 - 0.16e2 / 0.3e1 * t160 * t473 * t135 + 0.16e2 / 0.3e1 * t160 * t473 * t118 - t74 * t165 * t215 / 0.3e1 + t74 * t165 * t252 / 0.3e1 - 0.28e2 / 0.3e1 * t81 * t486 * t135 + 0.28e2 / 0.3e1 * t81 * t486 * t118 + 0.128e3 / 0.9e1 * t494 * t327 * t175 * t329 - 0.3072e4 * t39 * t440 * t444 * t503 - 0.4e1 * t81 * t188 * t215 + 0.4e1 * t81 * t188 * t252
  t513 = t359 + t512
  t518 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t63 + t6 * t69 * t137 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t142 * t254 - 0.3e1 / 0.8e1 * t6 * t258 * t513)
  t536 = 0.1e1 / t324
  t537 = t176 * t536
  t553 = t279 * t135
  t556 = t279 * t118
  t569 = t26 ** 2
  t570 = 0.1e1 / t569
  t572 = t321 * s0
  t574 = 0.1e1 / t324 / t146
  t582 = t536 * t40
  t587 = 0.1e1 / t20 / t179
  t593 = 0.1e1 / t19 / t442
  t602 = 0.1e1 / t20 / t324 / t18
  t607 = t175 * t321
  t608 = t607 * t593
  t611 = t29 * t31
  t615 = t70 * t38
  t620 = t593 * t175
  t629 = t593 * t25 * t383 * t92
  t632 = t85 * t587
  t642 = t175 * t30 * t572
  t646 = 0.1e1 / t19 / t324 / t311
  t649 = 0.1e1 / t91 / t445 / t90
  t651 = t320 * t31
  t656 = 0.1e1 / t19 / t311
  t662 = 0.1e1 / t82 / t26
  t680 = -0.896e3 / 0.9e1 * t408 * t177 * t536 * t92 - 0.224e3 / 0.81e2 * t395 * t537 * t40 + 0.16384e5 * t123 * t570 * t572 * t574 * t447 - 0.76160e5 / 0.9e1 * t247 * t537 * t182 + 0.448e3 / 0.81e2 * t400 * t177 * t582 + 0.6832e4 / 0.81e2 * t238 * t86 * t587 * t92 - 0.11776e5 / 0.27e2 * t421 * t422 * t593 * t182 + 0.2048e4 / 0.27e2 * t57 * t343 * t439 * t602 * t182 * t449 + 0.128e3 / 0.729e3 * t394 * t608 * t40 * t38 * t611 - 0.64e2 / 0.729e3 * params.beta * t615 * t71 * t25 * t28 * t422 * t620 * t40 + 0.512e3 / 0.243e3 * t399 * t343 * t321 * t629 - 0.1708e4 / 0.243e3 * t228 * t229 * t632 * t40 + 0.55296e5 * t441 * t602 * t447 * t449 - 0.245760e6 * t57 * t642 * t646 * t649 * t651 + 0.910e3 / 0.243e3 * t124 * t32 * t656 * t40 + 0.1024e4 / 0.27e2 * t228 * t662 * t439 * t85 * t602 * t182 + 0.3640e4 / 0.81e2 * t129 * t32 * t656 * t92 - 0.6400e4 / 0.27e2 * t124 * t422 * t620 * t182 - 0.256e3 / 0.243e3 * t394 * t607 * t629
  t684 = t251 ** 2
  t691 = t224 ** 2
  t706 = t321 * t593
  t712 = t205 ** 2
  t754 = 0.6e1 * t98 * t223 * t684 + 0.24e2 * t98 * t55 / t360 / t59 * t691 + t98 * params.alpha * (0.910e3 / 0.243e3 * t43 * t32 * t656 * t45 + 0.721e3 / 0.81e2 * t104 * t86 * t587 * t108 - 0.1862e4 / 0.243e3 * t203 * t537 * t206 + 0.232e3 / 0.729e3 * t203 * t706 * t384 - 0.8e1 / 0.243e3 * t203 * t439 * t602 / t712 * t24 * t83 * t85 + 0.910e3 / 0.243e3 * t50 * t32 * t656) * t60 - 0.14e2 / 0.9e1 * t74 * t466 * t252 + 0.14e2 / 0.9e1 * t74 * t466 * t215 - 0.32e2 / 0.3e1 * t160 * t473 * t252 + 0.32e2 / 0.3e1 * t160 * t473 * t215 - 0.56e2 / 0.3e1 * t81 * t486 * t252 + 0.56e2 / 0.3e1 * t81 * t486 * t215 - 0.245760e6 * t39 * t642 * t646 * t649 * t55 * t60 * t651 + 0.4e1 / 0.9e1 * t74 * t165 * t454
  t771 = t31 * t593
  t772 = t771 * t175
  t776 = t440 * t602
  t781 = t611 * t94
  t784 = t314 * t92
  t791 = t327 * t182
  t795 = 0.16e2 / 0.3e1 * t81 * t188 * t454 - 0.4e1 / 0.9e1 * t74 * t165 * t392 - 0.16e2 / 0.3e1 * t81 * t188 * t392 + 0.8e1 / 0.3e1 * t74 * t165 * t364 + 0.32e2 * t81 * t188 * t364 - 0.6400e4 / 0.27e2 * t494 * t772 * t329 + 0.55296e5 * t39 * t776 * t503 - 0.256e3 / 0.243e3 * t275 * t608 * t781 + 0.448e3 / 0.9e1 * t160 * t784 * t135 - 0.448e3 / 0.9e1 * t160 * t784 * t118 - 0.1024e4 / 0.9e1 * t323 * t791 * t135
  t806 = t335 * t40
  t817 = t335 * t92
  t837 = 0.1024e4 / 0.27e2 * t39 * t143 * t662 * t439 * t85 * t602 * t329 + 0.1024e4 / 0.9e1 * t323 * t791 * t118 + 0.280e3 / 0.81e2 * t74 * t806 * t135 - 0.1708e4 / 0.243e3 * t145 * t86 * t587 * t61 - 0.280e3 / 0.81e2 * t74 * t806 * t118 + 0.1120e4 / 0.27e2 * t81 * t817 * t135 - 0.1120e4 / 0.27e2 * t81 * t817 * t118 + 0.64e2 / 0.3e1 * t160 * t473 * t225 + 0.112e3 / 0.3e1 * t81 * t486 * t225 + 0.28e2 / 0.9e1 * t74 * t466 * t225 - 0.36e2 * t98 * t362 * t224 * t251
  t872 = t116 * t222
  t883 = 0.8e1 * t98 * t223 * t453 * t134 - 0.24e2 * t98 * t117 * t361 * t363 - 0.6e1 * t98 * t214 * t262 - 0.4e1 * t98 * t117 * t121 * t453 - 0.4e1 * t98 * t391 * t217 + 0.12e2 * t98 * t214 * t270 + 0.16e2 / 0.9e1 * t304 * t230 * t218 + 0.16384e5 * t72 * t570 * t572 * t574 * t447 * t184 + 0.24e2 * t39 * t40 * params.alpha * t872 * t266 - 0.224e3 / 0.81e2 * t276 * t582 * t184 - 0.76160e5 / 0.9e1 * t178 * t536 * t182 * t184
  t884 = t292 * t251
  t896 = t213 * t121 * t134
  t926 = t872 * t224
  t930 = 0.16e2 * t290 * t291 * t884 - 0.64e2 / 0.3e1 * t72 * t24 * t229 * t85 * t239 * params.alpha * t293 + 0.4e1 / 0.3e1 * t298 * t299 * t896 + 0.4e1 / 0.3e1 * t298 * t299 * t884 + 0.8e1 / 0.9e1 * t304 * t230 * t252 + 0.128e3 / 0.729e3 * t275 * t175 * t706 * t40 * t184 * t38 * t611 + 0.16e2 * t290 * t291 * t896 - 0.16e2 / 0.9e1 * t304 * t230 * t225 + 0.112e3 / 0.27e2 * t304 * t404 * t118 - 0.112e3 / 0.3e1 * t290 * t243 * params.alpha * t293 - 0.32e2 * t290 * t291 * t926
  t941 = t222 * t134 * t251
  t961 = t297 * t28 * t321 * t31
  t968 = t39 * t175 * t439 * t444 * t447
  t981 = -0.28e2 / 0.9e1 * t298 * t234 * params.alpha * t293 - 0.8e1 / 0.3e1 * t298 * t299 * t926 - 0.32e2 * t290 * t130 * t55 * t941 - 0.64e2 / 0.729e3 * params.mu * t615 * t71 * t493 * t772 * t61 + 0.512e3 / 0.243e3 * t342 * t71 * t608 * t781 + 0.2048e4 / 0.27e2 * t303 * t776 * t329 * t449 - 0.512e3 / 0.9e1 * t961 * t435 * t135 + 0.12288e5 * t968 * t135 * t449 + 0.512e3 / 0.9e1 * t961 * t435 * t118 - 0.12288e5 * t968 * t118 * t449 - 0.8e1 / 0.9e1 * t304 * t230 * t215
  t995 = t343 * t176
  t996 = t342 * t995
  t999 = t39 * t995
  t1011 = t31 * t656
  t1021 = -0.8e1 / 0.3e1 * t298 * t125 * t55 * t941 - 0.112e3 / 0.27e2 * t304 * t404 * t135 + 0.1536e4 * t39 * t177 * t180 * t182 * params.alpha * t293 + 0.128e3 / 0.81e2 * t996 * t553 - 0.256e3 / 0.9e1 * t999 * t409 * t135 - 0.128e3 / 0.81e2 * t996 * t556 + 0.256e3 / 0.9e1 * t999 * t409 * t118 + 0.6832e4 / 0.81e2 * t160 * t632 * t94 + 0.910e3 / 0.243e3 * t74 * t1011 * t61 + 0.3640e4 / 0.81e2 * t81 * t1011 * t94 - 0.11776e5 / 0.27e2 * t323 * t771 * t329
  t1029 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t107 * t63 - 0.5e1 / 0.9e1 * t6 * t23 * t137 + t6 * t69 * t254 / 0.2e1 - t6 * t142 * t513 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t258 * (-0.1536e4 * t178 * t183 * t225 + 0.448e3 / 0.81e2 * t344 * t537 * t61 + 0.768e3 * t178 * t183 * t252 - 0.768e3 * t178 * t183 * t215 - 0.12800e5 / 0.3e1 * t178 * t283 * t135 + 0.12800e5 / 0.3e1 * t178 * t283 * t118 - 0.64e2 / 0.81e2 * t276 * t553 + 0.64e2 / 0.81e2 * t276 * t556 - 0.896e3 / 0.9e1 * t349 * t537 * t94 - t98 * t122 * t680 + t754 + t795 + t837 + t883 + t930 + t981 + t1021))
  v4rho4_0_ = 0.2e1 * r0 * t1029 + 0.8e1 * t518

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
  t33 = t32 ** 2
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = 0.1e1 / t35
  t37 = t33 * t36
  t38 = jnp.sqrt(s0)
  t39 = r0 ** (0.1e1 / 0.3e1)
  t41 = 0.1e1 / t39 / r0
  t42 = t38 * t41
  t44 = t37 * t42 / 0.12e2
  t45 = jnp.tanh(t44)
  t46 = params.mu * t45
  t47 = jnp.arcsinh(t44)
  t48 = 0.1e1 - params.zeta
  t50 = t48 * t33 * t36
  t51 = 0.1e1 + t44
  t52 = jnp.log(t51)
  t55 = params.zeta * t33
  t56 = t36 * t38
  t62 = 0.1e1 + params.alpha * (t55 * t56 * t41 / 0.12e2 + t50 * t42 * t52 / 0.12e2)
  t64 = params.beta * t45
  t66 = t64 * t47 + 0.1e1
  t67 = 0.1e1 / t66
  t68 = t47 * t62 * t67
  t70 = t46 * t68 + 0.1e1
  t74 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t75 = t74 * f.p.zeta_threshold
  t77 = f.my_piecewise3(t20, t75, t21 * t19)
  t78 = t30 ** 2
  t79 = 0.1e1 / t78
  t80 = t77 * t79
  t83 = t5 * t80 * t70 / 0.8e1
  t84 = t77 * t30
  t85 = t45 ** 2
  t86 = 0.1e1 - t85
  t87 = params.mu * t86
  t88 = t87 * t37
  t89 = r0 ** 2
  t91 = 0.1e1 / t39 / t89
  t92 = t38 * t91
  t96 = t46 * t37
  t97 = t35 ** 2
  t98 = 0.1e1 / t97
  t99 = t32 * t98
  t100 = t39 ** 2
  t106 = 0.144e3 + 0.6e1 * t99 * s0 / t100 / t89
  t107 = jnp.sqrt(t106)
  t108 = 0.1e1 / t107
  t110 = t108 * t62 * t67
  t114 = t46 * t47
  t119 = t48 * t32 * t98
  t120 = t89 * r0
  t124 = 0.1e1 / t51
  t132 = params.alpha * (-t50 * t92 * t52 / 0.9e1 - t119 * s0 / t100 / t120 * t124 / 0.18e2 - t55 * t56 * t91 / 0.9e1)
  t133 = t132 * t67
  t135 = t66 ** 2
  t136 = 0.1e1 / t135
  t137 = t62 * t136
  t138 = params.beta * t86
  t139 = t138 * t33
  t140 = t91 * t47
  t144 = t64 * t33
  t145 = t91 * t108
  t149 = -t139 * t56 * t140 / 0.9e1 - 0.4e1 / 0.3e1 * t144 * t56 * t145
  t150 = t137 * t149
  t152 = -t88 * t92 * t68 / 0.9e1 - 0.4e1 / 0.3e1 * t96 * t92 * t110 + t114 * t133 - t114 * t150
  t157 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t70 - t83 - 0.3e1 / 0.8e1 * t5 * t84 * t152)
  t159 = r1 <= f.p.dens_threshold
  t160 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t161 = 0.1e1 + t160
  t162 = t161 <= f.p.zeta_threshold
  t163 = t161 ** (0.1e1 / 0.3e1)
  t165 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t168 = f.my_piecewise3(t162, 0, 0.4e1 / 0.3e1 * t163 * t165)
  t169 = t168 * t30
  t170 = jnp.sqrt(s2)
  t171 = r1 ** (0.1e1 / 0.3e1)
  t173 = 0.1e1 / t171 / r1
  t174 = t170 * t173
  t176 = t37 * t174 / 0.12e2
  t177 = jnp.tanh(t176)
  t178 = params.mu * t177
  t179 = jnp.arcsinh(t176)
  t180 = 0.1e1 + t176
  t181 = jnp.log(t180)
  t184 = t36 * t170
  t190 = 0.1e1 + params.alpha * (t55 * t184 * t173 / 0.12e2 + t50 * t174 * t181 / 0.12e2)
  t192 = params.beta * t177
  t194 = t192 * t179 + 0.1e1
  t195 = 0.1e1 / t194
  t196 = t179 * t190 * t195
  t198 = t178 * t196 + 0.1e1
  t203 = f.my_piecewise3(t162, t75, t163 * t161)
  t204 = t203 * t79
  t207 = t5 * t204 * t198 / 0.8e1
  t209 = f.my_piecewise3(t159, 0, -0.3e1 / 0.8e1 * t5 * t169 * t198 - t207)
  t211 = t21 ** 2
  t212 = 0.1e1 / t211
  t213 = t26 ** 2
  t218 = t16 / t22 / t6
  t220 = -0.2e1 * t23 + 0.2e1 * t218
  t221 = f.my_piecewise5(t10, 0, t14, 0, t220)
  t225 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t212 * t213 + 0.4e1 / 0.3e1 * t21 * t221)
  t232 = t5 * t29 * t79 * t70
  t238 = 0.1e1 / t78 / t6
  t242 = t5 * t77 * t238 * t70 / 0.12e2
  t244 = t5 * t80 * t152
  t246 = t86 * t32
  t249 = t89 ** 2
  t251 = 0.1e1 / t100 / t249
  t252 = s0 * t251
  t257 = 0.1e1 / t39 / t120
  t258 = t38 * t257
  t266 = t37 * t38
  t267 = t87 * t266
  t277 = 0.1e1 / t34
  t278 = t38 * s0
  t282 = 0.1e1 / t249 / t89
  t284 = 0.1e1 / t107 / t106
  t290 = t46 * t266
  t303 = t48 * t277
  t304 = t278 * t282
  t305 = t51 ** 2
  t324 = t149 ** 2
  t329 = t98 * s0
  t354 = -0.4e1 / 0.27e2 * t46 * t246 * t98 * t252 * t68 + 0.7e1 / 0.27e2 * t88 * t258 * t68 + 0.16e2 / 0.9e1 * t87 * t99 * t252 * t110 - 0.2e1 / 0.9e1 * t267 * t140 * t133 + 0.2e1 / 0.9e1 * t267 * t140 * t150 + 0.28e2 / 0.9e1 * t96 * t258 * t110 - 0.64e2 * t46 * t277 * t278 * t282 * t284 * t62 * t67 - 0.8e1 / 0.3e1 * t290 * t145 * t133 + 0.8e1 / 0.3e1 * t290 * t145 * t150 + t114 * params.alpha * (0.7e1 / 0.27e2 * t50 * t258 * t52 + 0.5e1 / 0.18e2 * t119 * t252 * t124 - t303 * t304 / t305 / 0.27e2 + 0.7e1 / 0.27e2 * t55 * t56 * t257) * t67 - 0.2e1 * t114 * t132 * t136 * t149 + 0.2e1 * t114 * t62 / t135 / t66 * t324 - t114 * t137 * (-0.4e1 / 0.27e2 * t64 * t246 * t329 * t251 * t47 + 0.7e1 / 0.27e2 * t139 * t56 * t257 * t47 + 0.16e2 / 0.9e1 * t138 * t32 * t329 * t251 * t108 + 0.28e2 / 0.9e1 * t144 * t56 * t257 * t108 - 0.64e2 * t64 * t277 * t304 * t284)
  t359 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t225 * t30 * t70 - t232 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t152 + t242 - t244 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t84 * t354)
  t360 = t163 ** 2
  t361 = 0.1e1 / t360
  t362 = t165 ** 2
  t366 = f.my_piecewise5(t14, 0, t10, 0, -t220)
  t370 = f.my_piecewise3(t162, 0, 0.4e1 / 0.9e1 * t361 * t362 + 0.4e1 / 0.3e1 * t163 * t366)
  t377 = t5 * t168 * t79 * t198
  t382 = t5 * t203 * t238 * t198 / 0.12e2
  t384 = f.my_piecewise3(t159, 0, -0.3e1 / 0.8e1 * t5 * t370 * t30 * t198 - t377 / 0.4e1 + t382)
  d11 = 0.2e1 * t157 + 0.2e1 * t209 + t6 * (t359 + t384)
  t387 = -t7 - t24
  t388 = f.my_piecewise5(t10, 0, t14, 0, t387)
  t391 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t388)
  t392 = t391 * t30
  t397 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t392 * t70 - t83)
  t399 = f.my_piecewise5(t14, 0, t10, 0, -t387)
  t402 = f.my_piecewise3(t162, 0, 0.4e1 / 0.3e1 * t163 * t399)
  t403 = t402 * t30
  t407 = t203 * t30
  t408 = t177 ** 2
  t409 = 0.1e1 - t408
  t410 = params.mu * t409
  t411 = t410 * t37
  t412 = r1 ** 2
  t414 = 0.1e1 / t171 / t412
  t415 = t170 * t414
  t419 = t178 * t37
  t420 = t171 ** 2
  t426 = 0.144e3 + 0.6e1 * t99 * s2 / t420 / t412
  t427 = jnp.sqrt(t426)
  t428 = 0.1e1 / t427
  t430 = t428 * t190 * t195
  t434 = t178 * t179
  t438 = t412 * r1
  t442 = 0.1e1 / t180
  t450 = params.alpha * (-t50 * t415 * t181 / 0.9e1 - t119 * s2 / t420 / t438 * t442 / 0.18e2 - t55 * t184 * t414 / 0.9e1)
  t451 = t450 * t195
  t453 = t194 ** 2
  t454 = 0.1e1 / t453
  t455 = t190 * t454
  t456 = params.beta * t409
  t457 = t456 * t33
  t458 = t414 * t179
  t462 = t192 * t33
  t463 = t414 * t428
  t467 = -t457 * t184 * t458 / 0.9e1 - 0.4e1 / 0.3e1 * t462 * t184 * t463
  t468 = t455 * t467
  t470 = -t411 * t415 * t196 / 0.9e1 - 0.4e1 / 0.3e1 * t419 * t415 * t430 + t434 * t451 - t434 * t468
  t475 = f.my_piecewise3(t159, 0, -0.3e1 / 0.8e1 * t5 * t403 * t198 - t207 - 0.3e1 / 0.8e1 * t5 * t407 * t470)
  t479 = 0.2e1 * t218
  t480 = f.my_piecewise5(t10, 0, t14, 0, t479)
  t484 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t212 * t388 * t26 + 0.4e1 / 0.3e1 * t21 * t480)
  t491 = t5 * t391 * t79 * t70
  t499 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t484 * t30 * t70 - t491 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t392 * t152 - t232 / 0.8e1 + t242 - t244 / 0.8e1)
  t503 = f.my_piecewise5(t14, 0, t10, 0, -t479)
  t507 = f.my_piecewise3(t162, 0, 0.4e1 / 0.9e1 * t361 * t399 * t165 + 0.4e1 / 0.3e1 * t163 * t503)
  t514 = t5 * t402 * t79 * t198
  t521 = t5 * t204 * t470
  t524 = f.my_piecewise3(t159, 0, -0.3e1 / 0.8e1 * t5 * t507 * t30 * t198 - t514 / 0.8e1 - t377 / 0.8e1 + t382 - 0.3e1 / 0.8e1 * t5 * t169 * t470 - t521 / 0.8e1)
  d12 = t157 + t209 + t397 + t475 + t6 * (t499 + t524)
  t529 = t388 ** 2
  t533 = 0.2e1 * t23 + 0.2e1 * t218
  t534 = f.my_piecewise5(t10, 0, t14, 0, t533)
  t538 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t212 * t529 + 0.4e1 / 0.3e1 * t21 * t534)
  t545 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t538 * t30 * t70 - t491 / 0.4e1 + t242)
  t546 = t399 ** 2
  t550 = f.my_piecewise5(t14, 0, t10, 0, -t533)
  t554 = f.my_piecewise3(t162, 0, 0.4e1 / 0.9e1 * t361 * t546 + 0.4e1 / 0.3e1 * t163 * t550)
  t564 = t409 * t32
  t567 = t412 ** 2
  t569 = 0.1e1 / t420 / t567
  t570 = s2 * t569
  t575 = 0.1e1 / t171 / t438
  t576 = t170 * t575
  t584 = t37 * t170
  t585 = t410 * t584
  t595 = t170 * s2
  t599 = 0.1e1 / t567 / t412
  t601 = 0.1e1 / t427 / t426
  t607 = t178 * t584
  t620 = t595 * t599
  t621 = t180 ** 2
  t640 = t467 ** 2
  t645 = t98 * s2
  t670 = -0.4e1 / 0.27e2 * t178 * t564 * t98 * t570 * t196 + 0.7e1 / 0.27e2 * t411 * t576 * t196 + 0.16e2 / 0.9e1 * t410 * t99 * t570 * t430 - 0.2e1 / 0.9e1 * t585 * t458 * t451 + 0.2e1 / 0.9e1 * t585 * t458 * t468 + 0.28e2 / 0.9e1 * t419 * t576 * t430 - 0.64e2 * t178 * t277 * t595 * t599 * t601 * t190 * t195 - 0.8e1 / 0.3e1 * t607 * t463 * t451 + 0.8e1 / 0.3e1 * t607 * t463 * t468 + t434 * params.alpha * (0.7e1 / 0.27e2 * t50 * t576 * t181 + 0.5e1 / 0.18e2 * t119 * t570 * t442 - t303 * t620 / t621 / 0.27e2 + 0.7e1 / 0.27e2 * t55 * t184 * t575) * t195 - 0.2e1 * t434 * t450 * t454 * t467 + 0.2e1 * t434 * t190 / t453 / t194 * t640 - t434 * t455 * (-0.4e1 / 0.27e2 * t192 * t564 * t645 * t569 * t179 + 0.7e1 / 0.27e2 * t457 * t184 * t575 * t179 + 0.16e2 / 0.9e1 * t456 * t32 * t645 * t569 * t428 + 0.28e2 / 0.9e1 * t462 * t184 * t575 * t428 - 0.64e2 * t192 * t277 * t620 * t601)
  t675 = f.my_piecewise3(t159, 0, -0.3e1 / 0.8e1 * t5 * t554 * t30 * t198 - t514 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t403 * t470 + t382 - t521 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t407 * t670)
  d22 = 0.2e1 * t397 + 0.2e1 * t475 + t6 * (t545 + t675)
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
  t45 = t44 ** 2
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = 0.1e1 / t47
  t49 = t45 * t48
  t50 = jnp.sqrt(s0)
  t51 = r0 ** (0.1e1 / 0.3e1)
  t53 = 0.1e1 / t51 / r0
  t54 = t50 * t53
  t56 = t49 * t54 / 0.12e2
  t57 = jnp.tanh(t56)
  t58 = params.mu * t57
  t59 = jnp.asinh(t56)
  t60 = 0.1e1 - params.zeta
  t62 = t60 * t45 * t48
  t63 = 0.1e1 + t56
  t64 = jnp.log(t63)
  t67 = params.zeta * t45
  t68 = t48 * t50
  t74 = 0.1e1 + params.alpha * (t67 * t68 * t53 / 0.12e2 + t62 * t54 * t64 / 0.12e2)
  t76 = params.beta * t57
  t78 = t76 * t59 + 0.1e1
  t79 = 0.1e1 / t78
  t80 = t59 * t74 * t79
  t82 = t58 * t80 + 0.1e1
  t88 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t89 = t42 ** 2
  t90 = 0.1e1 / t89
  t91 = t88 * t90
  t95 = t88 * t42
  t96 = t57 ** 2
  t97 = 0.1e1 - t96
  t98 = params.mu * t97
  t99 = t98 * t49
  t100 = r0 ** 2
  t102 = 0.1e1 / t51 / t100
  t103 = t50 * t102
  t107 = t58 * t49
  t108 = t47 ** 2
  t109 = 0.1e1 / t108
  t110 = t44 * t109
  t111 = t51 ** 2
  t117 = 0.144e3 + 0.6e1 * t110 * s0 / t111 / t100
  t118 = jnp.sqrt(t117)
  t119 = 0.1e1 / t118
  t121 = t119 * t74 * t79
  t125 = t58 * t59
  t130 = t60 * t44 * t109
  t131 = t100 * r0
  t135 = 0.1e1 / t63
  t142 = -t62 * t103 * t64 / 0.9e1 - t130 * s0 / t111 / t131 * t135 / 0.18e2 - t67 * t68 * t102 / 0.9e1
  t143 = params.alpha * t142
  t144 = t143 * t79
  t146 = t78 ** 2
  t147 = 0.1e1 / t146
  t148 = t74 * t147
  t149 = params.beta * t97
  t150 = t149 * t45
  t151 = t102 * t59
  t155 = t76 * t45
  t156 = t102 * t119
  t160 = -t150 * t68 * t151 / 0.9e1 - 0.4e1 / 0.3e1 * t155 * t68 * t156
  t161 = t148 * t160
  t163 = -t99 * t103 * t80 / 0.9e1 - 0.4e1 / 0.3e1 * t107 * t103 * t121 + t125 * t144 - t125 * t161
  t167 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t168 = t167 * f.p.zeta_threshold
  t170 = f.my_piecewise3(t20, t168, t21 * t19)
  t172 = 0.1e1 / t89 / t6
  t173 = t170 * t172
  t177 = t170 * t90
  t181 = t170 * t42
  t182 = t97 * t44
  t184 = t58 * t182 * t109
  t185 = t100 ** 2
  t187 = 0.1e1 / t111 / t185
  t188 = s0 * t187
  t193 = 0.1e1 / t51 / t131
  t194 = t50 * t193
  t198 = t98 * t110
  t202 = t49 * t50
  t203 = t98 * t202
  t213 = 0.1e1 / t46
  t214 = t50 * s0
  t215 = t213 * t214
  t216 = t58 * t215
  t218 = 0.1e1 / t185 / t100
  t220 = 0.1e1 / t118 / t117
  t221 = t218 * t220
  t222 = t74 * t79
  t226 = t58 * t202
  t239 = t60 * t213
  t240 = t214 * t218
  t241 = t63 ** 2
  t242 = 0.1e1 / t241
  t250 = params.alpha * (0.7e1 / 0.27e2 * t62 * t194 * t64 + 0.5e1 / 0.18e2 * t130 * t188 * t135 - t239 * t240 * t242 / 0.27e2 + 0.7e1 / 0.27e2 * t67 * t68 * t193)
  t251 = t250 * t79
  t253 = t147 * t160
  t258 = 0.1e1 / t146 / t78
  t259 = t74 * t258
  t260 = t160 ** 2
  t261 = t259 * t260
  t264 = t76 * t182
  t265 = t109 * s0
  t270 = t193 * t59
  t274 = t149 * t44
  t275 = t187 * t119
  t279 = t193 * t119
  t283 = t76 * t213
  t287 = -0.4e1 / 0.27e2 * t264 * t265 * t187 * t59 + 0.7e1 / 0.27e2 * t150 * t68 * t270 + 0.16e2 / 0.9e1 * t274 * t265 * t275 + 0.28e2 / 0.9e1 * t155 * t68 * t279 - 0.64e2 * t283 * t240 * t220
  t288 = t148 * t287
  t290 = -0.4e1 / 0.27e2 * t184 * t188 * t80 + 0.7e1 / 0.27e2 * t99 * t194 * t80 + 0.16e2 / 0.9e1 * t198 * t188 * t121 - 0.2e1 / 0.9e1 * t203 * t151 * t144 + 0.2e1 / 0.9e1 * t203 * t151 * t161 + 0.28e2 / 0.9e1 * t107 * t194 * t121 - 0.64e2 * t216 * t221 * t222 - 0.8e1 / 0.3e1 * t226 * t156 * t144 + 0.8e1 / 0.3e1 * t226 * t156 * t161 + t125 * t251 - 0.2e1 * t125 * t143 * t253 + 0.2e1 * t125 * t261 - t125 * t288
  t295 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t82 - t5 * t91 * t82 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t95 * t163 + t5 * t173 * t82 / 0.12e2 - t5 * t177 * t163 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t181 * t290)
  t297 = r1 <= f.p.dens_threshold
  t298 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t299 = 0.1e1 + t298
  t300 = t299 <= f.p.zeta_threshold
  t301 = t299 ** (0.1e1 / 0.3e1)
  t302 = t301 ** 2
  t303 = 0.1e1 / t302
  t305 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t306 = t305 ** 2
  t310 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t314 = f.my_piecewise3(t300, 0, 0.4e1 / 0.9e1 * t303 * t306 + 0.4e1 / 0.3e1 * t301 * t310)
  t316 = jnp.sqrt(s2)
  t317 = r1 ** (0.1e1 / 0.3e1)
  t319 = 0.1e1 / t317 / r1
  t320 = t316 * t319
  t322 = t49 * t320 / 0.12e2
  t323 = jnp.tanh(t322)
  t325 = jnp.asinh(t322)
  t327 = jnp.log(0.1e1 + t322)
  t344 = 0.1e1 + params.mu * t323 * t325 * (0.1e1 + params.alpha * (t67 * t48 * t316 * t319 / 0.12e2 + t62 * t320 * t327 / 0.12e2)) / (params.beta * t323 * t325 + 0.1e1)
  t350 = f.my_piecewise3(t300, 0, 0.4e1 / 0.3e1 * t301 * t305)
  t356 = f.my_piecewise3(t300, t168, t301 * t299)
  t362 = f.my_piecewise3(t297, 0, -0.3e1 / 0.8e1 * t5 * t314 * t42 * t344 - t5 * t350 * t90 * t344 / 0.4e1 + t5 * t356 * t172 * t344 / 0.12e2)
  t372 = t24 ** 2
  t376 = 0.6e1 * t33 - 0.6e1 * t16 / t372
  t377 = f.my_piecewise5(t10, 0, t14, 0, t376)
  t381 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t377)
  t404 = 0.1e1 / t89 / t24
  t430 = t97 ** 2
  t434 = 0.1e1 / t185 / t131
  t435 = t214 * t434
  t441 = t434 * t59
  t447 = 0.1e1 / t111 / t185 / r0
  t458 = 0.1e1 / t51 / t185
  t468 = 0.1e1 / t47 / t46
  t469 = s0 ** 2
  t471 = t185 ** 2
  t473 = 0.1e1 / t51 / t471
  t486 = t469 * t473
  t492 = t213 * t50 * t469
  t496 = 0.1e1 / t111 / t471 / r0
  t497 = t117 ** 2
  t499 = 0.1e1 / t118 / t497
  t504 = 0.8e1 / 0.81e2 * params.beta * t430 * t213 * t435 * t59 - 0.16e2 / 0.81e2 * params.beta * t96 * t97 * t215 * t441 + 0.28e2 / 0.27e2 * t264 * t265 * t447 * t59 + 0.32e2 / 0.9e1 * t76 * t97 * t215 * t434 * t119 - 0.70e2 / 0.81e2 * t150 * t68 * t458 * t59 - 0.112e3 / 0.9e1 * t274 * t265 * t447 * t119 + 0.128e3 / 0.9e1 * t150 * t468 * t469 * t473 * t220 - 0.280e3 / 0.27e2 * t155 * t68 * t458 * t119 + 0.1600e4 / 0.3e1 * t283 * t435 * t220 + 0.64e2 / 0.9e1 * t149 * t49 * t486 * t213 * t220 - 0.1536e4 * t76 * t492 * t496 * t499 * t110
  t507 = t146 ** 2
  t514 = t50 * t458
  t518 = s0 * t447
  t550 = t142 * t147 * t160
  t554 = t188 * t59
  t572 = t98 * t110 * s0
  t582 = -0.3e1 * t125 * t250 * t253 - 0.3e1 * t125 * t143 * t147 * t287 + 0.6e1 * t125 * t259 * t160 * t287 + 0.6e1 * t125 * t143 * t258 * t260 - t125 * t148 * t504 - 0.6e1 * t125 * t74 / t507 * t260 * t160 + t125 * params.alpha * (-0.70e2 / 0.81e2 * t62 * t514 * t64 - 0.119e3 / 0.81e2 * t130 * t518 * t135 + 0.11e2 / 0.27e2 * t239 * t435 * t242 - 0.2e1 / 0.243e3 * t239 * t469 * t473 / t241 / t63 * t49 - 0.70e2 / 0.81e2 * t67 * t68 * t458) * t79 + 0.8e1 / 0.81e2 * params.mu * t430 * t215 * t441 * t222 + 0.1600e4 / 0.3e1 * t216 * t434 * t220 * t222 + 0.8e1 * t226 * t156 * params.alpha * t550 - 0.4e1 / 0.9e1 * t184 * t554 * t144 + 0.2e1 / 0.3e1 * t203 * t151 * params.alpha * t550 + 0.4e1 / 0.9e1 * t184 * t554 * t161 - 0.7e1 / 0.9e1 * t203 * t270 * t161 + 0.7e1 / 0.9e1 * t203 * t270 * t144 - 0.16e2 / 0.3e1 * t572 * t275 * t161 + 0.16e2 / 0.3e1 * t572 * t275 * t144 - t203 * t151 * t251 / 0.3e1
  t608 = t220 * t74 * t79
  t630 = t97 * t213
  t653 = 0.28e2 / 0.27e2 * t184 * t518 * t80 - 0.8e1 * t226 * t156 * t261 - 0.2e1 / 0.3e1 * t203 * t151 * t261 + 0.4e1 * t226 * t156 * t288 + t203 * t151 * t288 / 0.3e1 - 0.28e2 / 0.3e1 * t226 * t279 * t161 + 0.28e2 / 0.3e1 * t226 * t279 * t144 + 0.64e2 / 0.9e1 * t98 * t49 * t469 * t473 * t213 * t608 - 0.1536e4 * t58 * t492 * t496 * t499 * t74 * t79 * t44 * t109 - 0.4e1 * t226 * t156 * t251 - 0.280e3 / 0.27e2 * t107 * t514 * t121 - 0.70e2 / 0.81e2 * t99 * t514 * t80 - 0.16e2 / 0.81e2 * params.mu * t96 * t630 * t435 * t80 + 0.32e2 / 0.9e1 * t58 * t630 * t435 * t121 - 0.112e3 / 0.9e1 * t198 * t518 * t121 + 0.128e3 / 0.9e1 * t98 * t45 * t468 * t486 * t608 + 0.192e3 * t216 * t221 * t161 - 0.192e3 * t216 * t221 * t144
  t659 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t381 * t42 * t82 - 0.3e1 / 0.8e1 * t5 * t41 * t90 * t82 - 0.9e1 / 0.8e1 * t5 * t43 * t163 + t5 * t88 * t172 * t82 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t91 * t163 - 0.9e1 / 0.8e1 * t5 * t95 * t290 - 0.5e1 / 0.36e2 * t5 * t170 * t404 * t82 + t5 * t173 * t163 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t177 * t290 - 0.3e1 / 0.8e1 * t5 * t181 * (t582 + t653))
  t669 = f.my_piecewise5(t14, 0, t10, 0, -t376)
  t673 = f.my_piecewise3(t300, 0, -0.8e1 / 0.27e2 / t302 / t299 * t306 * t305 + 0.4e1 / 0.3e1 * t303 * t305 * t310 + 0.4e1 / 0.3e1 * t301 * t669)
  t691 = f.my_piecewise3(t297, 0, -0.3e1 / 0.8e1 * t5 * t673 * t42 * t344 - 0.3e1 / 0.8e1 * t5 * t314 * t90 * t344 + t5 * t350 * t172 * t344 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t356 * t404 * t344)
  d111 = 0.3e1 * t295 + 0.3e1 * t362 + t6 * (t659 + t691)

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
  t57 = t56 ** 2
  t58 = jnp.pi ** 2
  t59 = t58 ** (0.1e1 / 0.3e1)
  t60 = 0.1e1 / t59
  t61 = t57 * t60
  t62 = jnp.sqrt(s0)
  t63 = r0 ** (0.1e1 / 0.3e1)
  t65 = 0.1e1 / t63 / r0
  t66 = t62 * t65
  t68 = t61 * t66 / 0.12e2
  t69 = jnp.tanh(t68)
  t70 = params.mu * t69
  t71 = jnp.asinh(t68)
  t72 = 0.1e1 - params.zeta
  t74 = t72 * t57 * t60
  t75 = 0.1e1 + t68
  t76 = jnp.log(t75)
  t79 = params.zeta * t57
  t80 = t60 * t62
  t86 = 0.1e1 + params.alpha * (t79 * t80 * t65 / 0.12e2 + t74 * t66 * t76 / 0.12e2)
  t88 = params.beta * t69
  t90 = t88 * t71 + 0.1e1
  t91 = 0.1e1 / t90
  t92 = t71 * t86 * t91
  t94 = t70 * t92 + 0.1e1
  t103 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t104 = t54 ** 2
  t105 = 0.1e1 / t104
  t106 = t103 * t105
  t110 = t103 * t54
  t111 = t69 ** 2
  t112 = 0.1e1 - t111
  t113 = params.mu * t112
  t114 = t113 * t61
  t115 = r0 ** 2
  t117 = 0.1e1 / t63 / t115
  t118 = t62 * t117
  t122 = t70 * t61
  t123 = t59 ** 2
  t124 = 0.1e1 / t123
  t125 = t56 * t124
  t126 = t63 ** 2
  t132 = 0.144e3 + 0.6e1 * t125 * s0 / t126 / t115
  t133 = jnp.sqrt(t132)
  t134 = 0.1e1 / t133
  t136 = t134 * t86 * t91
  t140 = t70 * t71
  t145 = t72 * t56 * t124
  t146 = t115 * r0
  t150 = 0.1e1 / t75
  t157 = -t74 * t118 * t76 / 0.9e1 - t145 * s0 / t126 / t146 * t150 / 0.18e2 - t79 * t80 * t117 / 0.9e1
  t158 = params.alpha * t157
  t159 = t158 * t91
  t161 = t90 ** 2
  t162 = 0.1e1 / t161
  t163 = t86 * t162
  t164 = params.beta * t112
  t165 = t164 * t57
  t166 = t117 * t71
  t170 = t88 * t57
  t171 = t117 * t134
  t175 = -t165 * t80 * t166 / 0.9e1 - 0.4e1 / 0.3e1 * t170 * t80 * t171
  t176 = t163 * t175
  t178 = -t114 * t118 * t92 / 0.9e1 - 0.4e1 / 0.3e1 * t122 * t118 * t136 + t140 * t159 - t140 * t176
  t184 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t186 = 0.1e1 / t104 / t6
  t187 = t184 * t186
  t191 = t184 * t105
  t195 = t184 * t54
  t196 = t112 * t56
  t198 = t70 * t196 * t124
  t199 = t115 ** 2
  t201 = 0.1e1 / t126 / t199
  t202 = s0 * t201
  t207 = 0.1e1 / t63 / t146
  t208 = t62 * t207
  t212 = t113 * t125
  t216 = t61 * t62
  t217 = t113 * t216
  t227 = 0.1e1 / t58
  t228 = t62 * s0
  t229 = t227 * t228
  t230 = t70 * t229
  t231 = t199 * t115
  t232 = 0.1e1 / t231
  t234 = 0.1e1 / t133 / t132
  t235 = t232 * t234
  t236 = t86 * t91
  t240 = t70 * t216
  t253 = t72 * t227
  t254 = t228 * t232
  t255 = t75 ** 2
  t256 = 0.1e1 / t255
  t263 = 0.7e1 / 0.27e2 * t74 * t208 * t76 + 0.5e1 / 0.18e2 * t145 * t202 * t150 - t253 * t254 * t256 / 0.27e2 + 0.7e1 / 0.27e2 * t79 * t80 * t207
  t264 = params.alpha * t263
  t265 = t264 * t91
  t267 = t162 * t175
  t272 = 0.1e1 / t161 / t90
  t273 = t86 * t272
  t274 = t175 ** 2
  t275 = t273 * t274
  t278 = t88 * t196
  t279 = t124 * s0
  t280 = t201 * t71
  t284 = t207 * t71
  t288 = t164 * t56
  t289 = t201 * t134
  t293 = t207 * t134
  t297 = t88 * t227
  t301 = -0.4e1 / 0.27e2 * t278 * t279 * t280 + 0.7e1 / 0.27e2 * t165 * t80 * t284 + 0.16e2 / 0.9e1 * t288 * t279 * t289 + 0.28e2 / 0.9e1 * t170 * t80 * t293 - 0.64e2 * t297 * t254 * t234
  t302 = t163 * t301
  t304 = -0.4e1 / 0.27e2 * t198 * t202 * t92 + 0.7e1 / 0.27e2 * t114 * t208 * t92 + 0.16e2 / 0.9e1 * t212 * t202 * t136 - 0.2e1 / 0.9e1 * t217 * t166 * t159 + 0.2e1 / 0.9e1 * t217 * t166 * t176 + 0.28e2 / 0.9e1 * t122 * t208 * t136 - 0.64e2 * t230 * t235 * t236 - 0.8e1 / 0.3e1 * t240 * t171 * t159 + 0.8e1 / 0.3e1 * t240 * t171 * t176 + t140 * t265 - 0.2e1 * t140 * t158 * t267 + 0.2e1 * t140 * t275 - t140 * t302
  t308 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t309 = t308 * f.p.zeta_threshold
  t311 = f.my_piecewise3(t20, t309, t21 * t19)
  t313 = 0.1e1 / t104 / t25
  t314 = t311 * t313
  t318 = t311 * t186
  t322 = t311 * t105
  t326 = t311 * t54
  t327 = t112 ** 2
  t328 = params.beta * t327
  t329 = t328 * t227
  t331 = 0.1e1 / t199 / t146
  t332 = t228 * t331
  t336 = params.beta * t111
  t337 = t336 * t112
  t338 = t331 * t71
  t342 = t199 * r0
  t344 = 0.1e1 / t126 / t342
  t349 = t88 * t112
  t350 = t331 * t134
  t355 = 0.1e1 / t63 / t199
  t356 = t355 * t71
  t360 = t344 * t134
  t365 = 0.1e1 / t59 / t58
  t366 = s0 ** 2
  t367 = t365 * t366
  t368 = t199 ** 2
  t370 = 0.1e1 / t63 / t368
  t371 = t370 * t234
  t375 = t355 * t134
  t382 = t164 * t61
  t383 = t366 * t370
  t384 = t227 * t234
  t388 = t62 * t366
  t389 = t227 * t388
  t390 = t88 * t389
  t391 = t368 * r0
  t393 = 0.1e1 / t126 / t391
  t394 = t132 ** 2
  t396 = 0.1e1 / t133 / t394
  t401 = 0.8e1 / 0.81e2 * t329 * t332 * t71 - 0.16e2 / 0.81e2 * t337 * t229 * t338 + 0.28e2 / 0.27e2 * t278 * t279 * t344 * t71 + 0.32e2 / 0.9e1 * t349 * t229 * t350 - 0.70e2 / 0.81e2 * t165 * t80 * t356 - 0.112e3 / 0.9e1 * t288 * t279 * t360 + 0.128e3 / 0.9e1 * t165 * t367 * t371 - 0.280e3 / 0.27e2 * t170 * t80 * t375 + 0.1600e4 / 0.3e1 * t297 * t332 * t234 + 0.64e2 / 0.9e1 * t382 * t383 * t384 - 0.1536e4 * t390 * t393 * t396 * t125
  t402 = t163 * t401
  t404 = t161 ** 2
  t405 = 0.1e1 / t404
  t406 = t86 * t405
  t407 = t274 * t175
  t408 = t406 * t407
  t411 = t62 * t355
  t415 = s0 * t344
  t422 = t253 * t366
  t424 = 0.1e1 / t255 / t75
  t433 = params.alpha * (-0.70e2 / 0.81e2 * t74 * t411 * t76 - 0.119e3 / 0.81e2 * t145 * t415 * t150 + 0.11e2 / 0.27e2 * t253 * t332 * t256 - 0.2e1 / 0.243e3 * t422 * t370 * t424 * t61 - 0.70e2 / 0.81e2 * t79 * t80 * t355)
  t434 = t433 * t91
  t436 = t272 * t274
  t443 = t162 * t301
  t447 = t175 * t301
  t470 = t113 * t61 * t366
  t471 = t370 * t227
  t473 = t234 * t86 * t91
  t478 = t70 * t389 * t393
  t479 = t396 * t86
  t481 = t91 * t56 * t124
  t482 = t479 * t481
  t494 = -t140 * t402 - 0.6e1 * t140 * t408 + t140 * t434 + 0.6e1 * t140 * t158 * t436 - 0.3e1 * t140 * t264 * t267 - 0.3e1 * t140 * t158 * t443 + 0.6e1 * t140 * t273 * t447 - 0.8e1 * t240 * t171 * t275 - 0.2e1 / 0.3e1 * t217 * t166 * t275 + 0.4e1 * t240 * t171 * t302 + t217 * t166 * t302 / 0.3e1 - 0.28e2 / 0.3e1 * t240 * t293 * t176 + 0.28e2 / 0.3e1 * t240 * t293 * t159 + 0.64e2 / 0.9e1 * t470 * t471 * t473 - 0.1536e4 * t478 * t482 - 0.4e1 * t240 * t171 * t265 - 0.7e1 / 0.9e1 * t217 * t284 * t176 + 0.7e1 / 0.9e1 * t217 * t284 * t159
  t495 = t125 * s0
  t496 = t113 * t495
  t509 = t202 * t71
  t513 = t166 * params.alpha
  t514 = t157 * t162
  t515 = t514 * t175
  t519 = t171 * params.alpha
  t526 = t331 * t234
  t530 = params.mu * t327
  t531 = t530 * t229
  t541 = params.mu * t111
  t542 = t112 * t227
  t543 = t541 * t542
  t547 = t70 * t542
  t554 = t57 * t365
  t555 = t113 * t554
  t565 = -0.16e2 / 0.3e1 * t496 * t289 * t176 + 0.16e2 / 0.3e1 * t496 * t289 * t159 - t217 * t166 * t265 / 0.3e1 + 0.28e2 / 0.27e2 * t198 * t415 * t92 - 0.4e1 / 0.9e1 * t198 * t509 * t159 + 0.2e1 / 0.3e1 * t217 * t513 * t515 + 0.8e1 * t240 * t519 * t515 + 0.4e1 / 0.9e1 * t198 * t509 * t176 + 0.1600e4 / 0.3e1 * t230 * t526 * t236 + 0.8e1 / 0.81e2 * t531 * t338 * t236 - 0.280e3 / 0.27e2 * t122 * t411 * t136 - 0.70e2 / 0.81e2 * t114 * t411 * t92 - 0.16e2 / 0.81e2 * t543 * t332 * t92 + 0.32e2 / 0.9e1 * t547 * t332 * t136 - 0.112e3 / 0.9e1 * t212 * t415 * t136 + 0.128e3 / 0.9e1 * t555 * t383 * t473 + 0.192e3 * t230 * t235 * t176 - 0.192e3 * t230 * t235 * t159
  t566 = t494 + t565
  t571 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t94 - 0.3e1 / 0.8e1 * t5 * t106 * t94 - 0.9e1 / 0.8e1 * t5 * t110 * t178 + t5 * t187 * t94 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t191 * t178 - 0.9e1 / 0.8e1 * t5 * t195 * t304 - 0.5e1 / 0.36e2 * t5 * t314 * t94 + t5 * t318 * t178 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t322 * t304 - 0.3e1 / 0.8e1 * t5 * t326 * t566)
  t573 = r1 <= f.p.dens_threshold
  t574 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t575 = 0.1e1 + t574
  t576 = t575 <= f.p.zeta_threshold
  t577 = t575 ** (0.1e1 / 0.3e1)
  t578 = t577 ** 2
  t580 = 0.1e1 / t578 / t575
  t582 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t583 = t582 ** 2
  t587 = 0.1e1 / t578
  t588 = t587 * t582
  t590 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t594 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t598 = f.my_piecewise3(t576, 0, -0.8e1 / 0.27e2 * t580 * t583 * t582 + 0.4e1 / 0.3e1 * t588 * t590 + 0.4e1 / 0.3e1 * t577 * t594)
  t600 = jnp.sqrt(s2)
  t601 = r1 ** (0.1e1 / 0.3e1)
  t603 = 0.1e1 / t601 / r1
  t604 = t600 * t603
  t606 = t61 * t604 / 0.12e2
  t607 = jnp.tanh(t606)
  t609 = jnp.asinh(t606)
  t611 = jnp.log(0.1e1 + t606)
  t628 = 0.1e1 + params.mu * t607 * t609 * (0.1e1 + params.alpha * (t79 * t60 * t600 * t603 / 0.12e2 + t74 * t604 * t611 / 0.12e2)) / (params.beta * t607 * t609 + 0.1e1)
  t637 = f.my_piecewise3(t576, 0, 0.4e1 / 0.9e1 * t587 * t583 + 0.4e1 / 0.3e1 * t577 * t590)
  t644 = f.my_piecewise3(t576, 0, 0.4e1 / 0.3e1 * t577 * t582)
  t650 = f.my_piecewise3(t576, t309, t577 * t575)
  t656 = f.my_piecewise3(t573, 0, -0.3e1 / 0.8e1 * t5 * t598 * t54 * t628 - 0.3e1 / 0.8e1 * t5 * t637 * t105 * t628 + t5 * t644 * t186 * t628 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t650 * t313 * t628)
  t659 = 0.1e1 / t104 / t36
  t692 = 0.1e1 / t126 / t231
  t693 = s0 * t692
  t704 = 0.1e1 / t63 / t391
  t705 = t704 * t227
  t711 = 0.1e1 / t126 / t368 / t115
  t712 = t389 * t711
  t716 = t227 * t366
  t717 = t716 * t704
  t718 = t530 * t717
  t728 = t542 * t228
  t729 = t541 * t728
  t730 = t338 * t176
  t733 = t70 * t728
  t738 = t338 * t159
  t763 = 0.1e1 / t123 / t58
  t766 = t388 * t711
  t771 = t113 * t554 * t366
  t778 = -0.64e2 / 0.81e2 * t729 * t738 + 0.128e3 / 0.9e1 * t733 * t350 * t159 + 0.1120e4 / 0.27e2 * t240 * t375 * t176 - 0.1120e4 / 0.27e2 * t240 * t375 * t159 + 0.28e2 / 0.9e1 * t217 * t284 * t275 - 0.56e2 / 0.3e1 * t240 * t293 * t302 - 0.14e2 / 0.9e1 * t217 * t284 * t302 + 0.112e3 / 0.3e1 * t240 * t293 * t275 + 0.512e3 / 0.27e2 * t70 * t196 * t763 * t766 * t473 + 0.512e3 / 0.9e1 * t771 * t371 * t159 + 0.32e2 / 0.3e1 * t496 * t289 * t265
  t795 = t366 * s0
  t797 = t227 * t62 * t795
  t800 = 0.1e1 / t63 / t368 / t342
  t805 = 0.1e1 / t133 / t394 / t132
  t827 = 0.14e2 / 0.9e1 * t217 * t284 * t265 - 0.512e3 / 0.9e1 * t771 * t371 * t176 + 0.448e3 / 0.9e1 * t496 * t360 * t176 + 0.56e2 / 0.3e1 * t240 * t293 * t265 - 0.448e3 / 0.9e1 * t496 * t360 * t159 - 0.61440e5 * t70 * t797 * t800 * t805 * t86 * t91 * t57 * t365 + 0.64e2 / 0.3e1 * t496 * t289 * t275 - 0.32e2 / 0.3e1 * t496 * t289 * t302 + 0.8e1 / 0.3e1 * t217 * t166 * t408 + 0.32e2 * t240 * t171 * t408 - 0.4e1 / 0.9e1 * t217 * t166 * t434
  t837 = t274 ** 2
  t841 = t301 ** 2
  t846 = 0.1e1 / t63 / t342
  t847 = t62 * t846
  t854 = 0.1e1 / t368
  t855 = t228 * t854
  t864 = t255 ** 2
  t877 = t58 ** 2
  t878 = 0.1e1 / t877
  t881 = 0.1e1 / t368 / t199
  t898 = t366 * t704
  t911 = t328 * t716
  t912 = t704 * t57
  t917 = t854 * t71
  t942 = t69 * t57 * t60
  t946 = t111 * t69
  t948 = t112 * t57
  t970 = 0.4096e4 * t164 * t878 * t795 * t881 * t396 - 0.38080e5 / 0.9e1 * t297 * t855 * t234 + 0.512e3 / 0.27e2 * t278 * t763 * t388 * t711 * t234 + 0.3640e4 / 0.81e2 * t170 * t80 * t846 * t134 - 0.3200e4 / 0.27e2 * t382 * t898 * t384 + 0.27648e5 * t390 * t711 * t396 * t125 - 0.61440e5 * t88 * t797 * t800 * t805 * t554 - 0.128e3 / 0.243e3 * t911 * t912 * t60 * t134 + 0.224e3 / 0.81e2 * t337 * t229 * t917 + 0.910e3 / 0.243e3 * t165 * t80 * t846 * t71 - 0.112e3 / 0.81e2 * t329 * t855 * t71 - 0.448e3 / 0.9e1 * t349 * t229 * t854 * t134 + 0.6832e4 / 0.81e2 * t288 * t279 * t692 * t134 - 0.5888e4 / 0.27e2 * t165 * t367 * t704 * t234 + 0.64e2 / 0.729e3 * t911 * t704 * t71 * t942 - 0.32e2 / 0.729e3 * params.beta * t946 * t948 * t60 * t366 * t705 * t71 + 0.256e3 / 0.243e3 * t336 * t542 * t898 * t61 * t134 - 0.1708e4 / 0.243e3 * t278 * t279 * t692 * t71 + 0.1024e4 / 0.27e2 * t88 * t542 * t766 * t234 * t56 * t124
  t987 = -0.16e2 / 0.3e1 * t240 * t171 * t434 + 0.4e1 / 0.9e1 * t217 * t166 * t402 + 0.24e2 * t140 * t86 / t404 / t90 * t837 + 0.6e1 * t140 * t273 * t841 + t140 * params.alpha * (0.910e3 / 0.243e3 * t74 * t847 * t76 + 0.721e3 / 0.81e2 * t145 * t693 * t150 - 0.931e3 / 0.243e3 * t253 * t855 * t256 + 0.116e3 / 0.729e3 * t422 * t704 * t424 * t61 - 0.4e1 / 0.243e3 * t253 * t388 * t711 / t864 * t125 + 0.910e3 / 0.243e3 * t79 * t80 * t846) * t91 - t140 * t163 * t970 + 0.3640e4 / 0.81e2 * t122 * t847 * t136 + 0.910e3 / 0.243e3 * t114 * t847 * t92 - 0.6400e4 / 0.3e1 * t230 * t526 * t176 + 0.6400e4 / 0.3e1 * t230 * t526 * t159 - 0.32e2 / 0.81e2 * t531 * t730
  t1023 = t263 * t162 * t175
  t1027 = 0.32e2 / 0.81e2 * t531 * t738 - 0.768e3 * t230 * t235 * t275 + 0.384e3 * t230 * t235 * t302 - 0.384e3 * t230 * t235 * t265 + 0.224e3 / 0.81e2 * t543 * t855 * t92 - 0.448e3 / 0.9e1 * t547 * t855 * t136 + 0.6832e4 / 0.81e2 * t212 * t693 * t136 - 0.5888e4 / 0.27e2 * t555 * t898 * t473 + 0.16e2 / 0.9e1 * t70 * t112 * t495 * t280 * params.alpha * t515 + 0.64e2 / 0.729e3 * t718 * t92 * t942 + 0.16e2 * t240 * t519 * t1023
  t1028 = t514 * t301
  t1039 = t415 * t71
  t1053 = t157 * t272
  t1054 = t1053 * t274
  t1071 = 0.16e2 * t240 * t519 * t1028 - 0.64e2 / 0.3e1 * t496 * t289 * params.alpha * t515 + 0.8e1 / 0.9e1 * t198 * t509 * t302 - 0.112e3 / 0.27e2 * t198 * t1039 * t176 - 0.16e2 / 0.9e1 * t198 * t509 * t275 + 0.112e3 / 0.27e2 * t198 * t1039 * t159 - 0.28e2 / 0.9e1 * t217 * t284 * params.alpha * t515 - 0.8e1 / 0.3e1 * t217 * t513 * t1054 - 0.112e3 / 0.3e1 * t240 * t293 * params.alpha * t515 - 0.32e2 * t240 * t519 * t1054 - 0.32e2 / 0.729e3 * params.mu * t946 * t948 * t60 * t717 * t92
  t1079 = t471 * t234
  t1101 = t272 * t175 * t301
  t1118 = 0.256e3 / 0.243e3 * t541 * t542 * t366 * t912 * t60 * t136 - 0.256e3 / 0.9e1 * t470 * t1079 * t176 + 0.1024e4 / 0.27e2 * t198 * t712 * t473 + 0.256e3 / 0.9e1 * t470 * t1079 * t159 + 0.6144e4 * t478 * t479 * t162 * t125 * t175 - 0.6144e4 * t478 * t396 * params.alpha * t157 * t481 - 0.8e1 / 0.3e1 * t217 * t166 * t86 * t1101 - 0.8e1 / 0.9e1 * t198 * t509 * t265 + 0.4e1 / 0.3e1 * t217 * t513 * t1023 + 0.4e1 / 0.3e1 * t217 * t513 * t1028 - 0.32e2 * t240 * t171 * t86 * t1101
  t1162 = -0.24e2 * t140 * t158 * t405 * t407 - 0.36e2 * t140 * t406 * t274 * t301 - 0.4e1 * t140 * t158 * t162 * t401 + 0.12e2 * t140 * t264 * t436 - 0.6e1 * t140 * t264 * t443 - 0.4e1 * t140 * t433 * t267 + 0.8e1 * t140 * t273 * t401 * t175 - 0.38080e5 / 0.9e1 * t230 * t854 * t234 * t236 - 0.112e3 / 0.81e2 * t531 * t917 * t236 + 0.4096e4 * t113 * t878 * t795 * t881 * t396 * t236 + 0.24e2 * t70 * t71 * params.alpha * t1053 * t447
  t1169 = t19 ** 2
  t1172 = t30 ** 2
  t1178 = t41 ** 2
  t1187 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t1188 = f.my_piecewise5(t10, 0, t14, 0, t1187)
  t1192 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t1169 * t1172 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t1178 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t1188)
  t1211 = 0.10e2 / 0.27e2 * t5 * t311 * t659 * t94 - t5 * t53 * t105 * t94 / 0.2e1 + t5 * t103 * t186 * t94 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t184 * t313 * t94 - 0.3e1 / 0.2e1 * t5 * t195 * t566 - 0.5e1 / 0.9e1 * t5 * t314 * t178 + t5 * t318 * t304 / 0.2e1 - t5 * t322 * t566 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t326 * (0.16e2 / 0.3e1 * t240 * t171 * t402 - 0.1708e4 / 0.243e3 * t198 * t693 * t92 + 0.280e3 / 0.81e2 * t217 * t356 * t176 - 0.280e3 / 0.81e2 * t217 * t356 * t159 - 0.3200e4 / 0.27e2 * t470 * t705 * t473 + 0.27648e5 * t70 * t712 * t482 - 0.128e3 / 0.243e3 * t718 * t61 * t136 + 0.768e3 * t70 * t229 * t232 * t234 * params.alpha * t515 + 0.64e2 / 0.81e2 * t729 * t730 - 0.128e3 / 0.9e1 * t733 * t350 * t176 + t778 + t827 + t987 + t1027 + t1071 + t1118 + t1162) - 0.3e1 / 0.8e1 * t5 * t1192 * t54 * t94 - 0.3e1 / 0.2e1 * t5 * t55 * t178 - 0.3e1 / 0.2e1 * t5 * t106 * t178 - 0.9e1 / 0.4e1 * t5 * t110 * t304 + t5 * t187 * t178 - 0.3e1 / 0.2e1 * t5 * t191 * t304
  t1212 = f.my_piecewise3(t1, 0, t1211)
  t1213 = t575 ** 2
  t1216 = t583 ** 2
  t1222 = t590 ** 2
  t1228 = f.my_piecewise5(t14, 0, t10, 0, -t1187)
  t1232 = f.my_piecewise3(t576, 0, 0.40e2 / 0.81e2 / t578 / t1213 * t1216 - 0.16e2 / 0.9e1 * t580 * t583 * t590 + 0.4e1 / 0.3e1 * t587 * t1222 + 0.16e2 / 0.9e1 * t588 * t594 + 0.4e1 / 0.3e1 * t577 * t1228)
  t1254 = f.my_piecewise3(t573, 0, -0.3e1 / 0.8e1 * t5 * t1232 * t54 * t628 - t5 * t598 * t105 * t628 / 0.2e1 + t5 * t637 * t186 * t628 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t644 * t313 * t628 + 0.10e2 / 0.27e2 * t5 * t650 * t659 * t628)
  d1111 = 0.4e1 * t571 + 0.4e1 * t656 + t6 * (t1212 + t1254)

  res = {'v4rho4': d1111}
  return res
