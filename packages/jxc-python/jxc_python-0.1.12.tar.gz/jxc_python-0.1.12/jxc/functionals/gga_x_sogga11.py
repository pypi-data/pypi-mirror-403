"""Generated from gga_x_sogga11.mpl."""

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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
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

  sogga11_alpha = params_mu * X2S * X2S / params_kappa

  sogga11_f0 = lambda x: 1 - 1 / (1 + sogga11_alpha * x ** 2)

  sogga11_f1 = lambda x: 1 - jnp.exp(-sogga11_alpha * x ** 2)

  sogga11_f = lambda x: jnp.sum(jnp.array([params_a[i] * sogga11_f0(x) ** (i - 1) for i in range(1, 6 + 1)]), axis=0) + jnp.sum(jnp.array([params_b[i] * sogga11_f1(x) ** (i - 1) for i in range(1, 6 + 1)]), axis=0)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, sogga11_f, rs, zeta, xs0, xs1)

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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
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

  sogga11_alpha = params_mu * X2S * X2S / params_kappa

  sogga11_f0 = lambda x: 1 - 1 / (1 + sogga11_alpha * x ** 2)

  sogga11_f1 = lambda x: 1 - jnp.exp(-sogga11_alpha * x ** 2)

  sogga11_f = lambda x: jnp.sum(jnp.array([params_a[i] * sogga11_f0(x) ** (i - 1) for i in range(1, 6 + 1)]), axis=0) + jnp.sum(jnp.array([params_b[i] * sogga11_f1(x) ** (i - 1) for i in range(1, 6 + 1)]), axis=0)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, sogga11_f, rs, zeta, xs0, xs1)

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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
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

  sogga11_alpha = params_mu * X2S * X2S / params_kappa

  sogga11_f0 = lambda x: 1 - 1 / (1 + sogga11_alpha * x ** 2)

  sogga11_f1 = lambda x: 1 - jnp.exp(-sogga11_alpha * x ** 2)

  sogga11_f = lambda x: jnp.sum(jnp.array([params_a[i] * sogga11_f0(x) ** (i - 1) for i in range(1, 6 + 1)]), axis=0) + jnp.sum(jnp.array([params_b[i] * sogga11_f1(x) ** (i - 1) for i in range(1, 6 + 1)]), axis=0)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, sogga11_f, rs, zeta, xs0, xs1)

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
  t28 = params.a[0]
  t29 = params.a[1]
  t30 = 6 ** (0.1e1 / 0.3e1)
  t31 = params.mu * t30
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = 0.1e1 / t34
  t36 = t31 * t35
  t37 = 0.1e1 / params.kappa
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t46 = t36 * t38 * t43 / 0.24e2
  t47 = 0.1e1 + t46
  t49 = 0.1e1 - 0.1e1 / t47
  t51 = params.a[2]
  t52 = t49 ** 2
  t54 = params.a[3]
  t55 = t52 * t49
  t57 = params.a[4]
  t58 = t52 ** 2
  t60 = params.a[5]
  t63 = params.b[0]
  t64 = params.b[1]
  t65 = jnp.exp(-t46)
  t66 = 0.1e1 - t65
  t68 = params.b[2]
  t69 = t66 ** 2
  t71 = params.b[3]
  t72 = t69 * t66
  t74 = params.b[4]
  t75 = t69 ** 2
  t77 = params.b[5]
  t80 = t60 * t58 * t49 + t77 * t75 * t66 + t29 * t49 + t51 * t52 + t54 * t55 + t57 * t58 + t64 * t66 + t68 * t69 + t71 * t72 + t74 * t75 + t28 + t63
  t84 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t80)
  t85 = r1 <= f.p.dens_threshold
  t86 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t87 = 0.1e1 + t86
  t88 = t87 <= f.p.zeta_threshold
  t89 = t87 ** (0.1e1 / 0.3e1)
  t91 = f.my_piecewise3(t88, t22, t89 * t87)
  t92 = t91 * t26
  t93 = t37 * s2
  t94 = r1 ** 2
  t95 = r1 ** (0.1e1 / 0.3e1)
  t96 = t95 ** 2
  t98 = 0.1e1 / t96 / t94
  t101 = t36 * t93 * t98 / 0.24e2
  t102 = 0.1e1 + t101
  t104 = 0.1e1 - 0.1e1 / t102
  t106 = t104 ** 2
  t108 = t106 * t104
  t110 = t106 ** 2
  t114 = jnp.exp(-t101)
  t115 = 0.1e1 - t114
  t117 = t115 ** 2
  t119 = t117 * t115
  t121 = t117 ** 2
  t125 = t60 * t110 * t104 + t77 * t121 * t115 + t29 * t104 + t51 * t106 + t54 * t108 + t57 * t110 + t64 * t115 + t68 * t117 + t71 * t119 + t74 * t121 + t28 + t63
  t129 = f.my_piecewise3(t85, 0, -0.3e1 / 0.8e1 * t5 * t92 * t125)
  t130 = t6 ** 2
  t132 = t16 / t130
  t133 = t7 - t132
  t134 = f.my_piecewise5(t10, 0, t14, 0, t133)
  t137 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t134)
  t142 = t26 ** 2
  t143 = 0.1e1 / t142
  t147 = t5 * t25 * t143 * t80 / 0.8e1
  t148 = t47 ** 2
  t149 = 0.1e1 / t148
  t150 = t29 * t149
  t152 = t35 * t37
  t155 = 0.1e1 / t41 / t39 / r0
  t156 = s0 * t155
  t161 = t149 * params.mu
  t162 = t51 * t49 * t161
  t163 = t30 * t35
  t165 = t163 * t38 * t155
  t169 = t54 * t52 * t161
  t173 = t57 * t55 * t161
  t177 = t60 * t58 * t161
  t180 = t64 * params.mu
  t181 = t180 * t163
  t187 = t68 * t66 * t31
  t189 = t152 * t156 * t65
  t193 = t71 * t69 * t31
  t197 = t74 * t72 * t31
  t201 = t77 * t75 * t31
  t209 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t137 * t26 * t80 - t147 - 0.3e1 / 0.8e1 * t5 * t27 * (-t150 * t31 * t152 * t156 / 0.9e1 - 0.2e1 / 0.9e1 * t162 * t165 - t169 * t165 / 0.3e1 - 0.4e1 / 0.9e1 * t173 * t165 - 0.5e1 / 0.9e1 * t177 * t165 - t181 * t38 * t155 * t65 / 0.9e1 - 0.2e1 / 0.9e1 * t187 * t189 - t193 * t189 / 0.3e1 - 0.4e1 / 0.9e1 * t197 * t189 - 0.5e1 / 0.9e1 * t201 * t189))
  t211 = f.my_piecewise5(t14, 0, t10, 0, -t133)
  t214 = f.my_piecewise3(t88, 0, 0.4e1 / 0.3e1 * t89 * t211)
  t222 = t5 * t91 * t143 * t125 / 0.8e1
  t224 = f.my_piecewise3(t85, 0, -0.3e1 / 0.8e1 * t5 * t214 * t26 * t125 - t222)
  vrho_0_ = t84 + t129 + t6 * (t209 + t224)
  t227 = -t7 - t132
  t228 = f.my_piecewise5(t10, 0, t14, 0, t227)
  t231 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t228)
  t237 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t231 * t26 * t80 - t147)
  t239 = f.my_piecewise5(t14, 0, t10, 0, -t227)
  t242 = f.my_piecewise3(t88, 0, 0.4e1 / 0.3e1 * t89 * t239)
  t247 = t102 ** 2
  t248 = 0.1e1 / t247
  t249 = t29 * t248
  t253 = 0.1e1 / t96 / t94 / r1
  t254 = s2 * t253
  t259 = t248 * params.mu
  t260 = t51 * t104 * t259
  t262 = t163 * t93 * t253
  t266 = t54 * t106 * t259
  t270 = t57 * t108 * t259
  t274 = t60 * t110 * t259
  t282 = t68 * t115 * t31
  t284 = t152 * t254 * t114
  t288 = t71 * t117 * t31
  t292 = t74 * t119 * t31
  t296 = t77 * t121 * t31
  t304 = f.my_piecewise3(t85, 0, -0.3e1 / 0.8e1 * t5 * t242 * t26 * t125 - t222 - 0.3e1 / 0.8e1 * t5 * t92 * (-t249 * t31 * t152 * t254 / 0.9e1 - 0.2e1 / 0.9e1 * t260 * t262 - t266 * t262 / 0.3e1 - 0.4e1 / 0.9e1 * t270 * t262 - 0.5e1 / 0.9e1 * t274 * t262 - t181 * t93 * t253 * t114 / 0.9e1 - 0.2e1 / 0.9e1 * t282 * t284 - t288 * t284 / 0.3e1 - 0.4e1 / 0.9e1 * t292 * t284 - 0.5e1 / 0.9e1 * t296 * t284))
  vrho_1_ = t84 + t129 + t6 * (t237 + t304)
  t309 = t163 * t37 * t43
  t320 = t180 * t30
  t322 = t152 * t43 * t65
  t337 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t150 * params.mu * t309 / 0.24e2 + t162 * t309 / 0.12e2 + t169 * t309 / 0.8e1 + t173 * t309 / 0.6e1 + 0.5e1 / 0.24e2 * t177 * t309 + t320 * t322 / 0.24e2 + t187 * t322 / 0.12e2 + t193 * t322 / 0.8e1 + t197 * t322 / 0.6e1 + 0.5e1 / 0.24e2 * t201 * t322))
  vsigma_0_ = t6 * t337
  vsigma_1_ = 0.0e0
  t340 = t163 * t37 * t98
  t352 = t152 * t98 * t114
  t367 = f.my_piecewise3(t85, 0, -0.3e1 / 0.8e1 * t5 * t92 * (t249 * params.mu * t340 / 0.24e2 + t260 * t340 / 0.12e2 + t266 * t340 / 0.8e1 + t270 * t340 / 0.6e1 + 0.5e1 / 0.24e2 * t274 * t340 + t320 * t352 / 0.24e2 + t282 * t352 / 0.12e2 + t288 * t352 / 0.8e1 + t292 * t352 / 0.6e1 + 0.5e1 / 0.24e2 * t296 * t352))
  vsigma_2_ = t6 * t367
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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
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

  sogga11_alpha = params_mu * X2S * X2S / params_kappa

  sogga11_f0 = lambda x: 1 - 1 / (1 + sogga11_alpha * x ** 2)

  sogga11_f1 = lambda x: 1 - jnp.exp(-sogga11_alpha * x ** 2)

  sogga11_f = lambda x: jnp.sum(jnp.array([params_a[i] * sogga11_f0(x) ** (i - 1) for i in range(1, 6 + 1)]), axis=0) + jnp.sum(jnp.array([params_b[i] * sogga11_f1(x) ** (i - 1) for i in range(1, 6 + 1)]), axis=0)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, sogga11_f, rs, zeta, xs0, xs1)

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
  t21 = params.a[1]
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = params.mu * t22
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = t23 * t27
  t29 = 0.1e1 / params.kappa
  t30 = t29 * s0
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = r0 ** 2
  t34 = t18 ** 2
  t36 = 0.1e1 / t34 / t33
  t37 = t32 * t36
  t40 = t28 * t30 * t37 / 0.24e2
  t41 = 0.1e1 + t40
  t43 = 0.1e1 - 0.1e1 / t41
  t45 = params.a[2]
  t46 = t43 ** 2
  t48 = params.a[3]
  t49 = t46 * t43
  t51 = params.a[4]
  t52 = t46 ** 2
  t54 = params.a[5]
  t58 = params.b[1]
  t59 = jnp.exp(-t40)
  t60 = 0.1e1 - t59
  t62 = params.b[2]
  t63 = t60 ** 2
  t65 = params.b[3]
  t66 = t63 * t60
  t68 = params.b[4]
  t69 = t63 ** 2
  t71 = params.b[5]
  t74 = t54 * t52 * t43 + t71 * t69 * t60 + t21 * t43 + t45 * t46 + t48 * t49 + t51 * t52 + t58 * t60 + t62 * t63 + t65 * t66 + t68 * t69 + params.a[0] + params.b[0]
  t78 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t74)
  t84 = t41 ** 2
  t85 = 0.1e1 / t84
  t87 = t21 * t85 * t23
  t88 = t27 * t29
  t92 = 0.1e1 / t34 / t33 / r0
  t94 = t88 * s0 * t32 * t92
  t97 = t45 * t43
  t98 = t85 * params.mu
  t99 = t98 * t22
  t103 = t48 * t46
  t107 = t51 * t49
  t111 = t54 * t52
  t116 = t22 * t27
  t117 = t58 * params.mu * t116
  t120 = t30 * t32 * t92 * t59
  t123 = t62 * t60
  t127 = t65 * t63
  t131 = t68 * t66
  t135 = t71 * t69
  t144 = f.my_piecewise3(t2, 0, -t6 * t17 / t34 * t74 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t87 * t94 / 0.9e1 - 0.2e1 / 0.9e1 * t97 * t99 * t94 - t103 * t99 * t94 / 0.3e1 - 0.4e1 / 0.9e1 * t107 * t99 * t94 - 0.5e1 / 0.9e1 * t111 * t99 * t94 - t117 * t120 / 0.9e1 - 0.2e1 / 0.9e1 * t123 * t28 * t120 - t127 * t28 * t120 / 0.3e1 - 0.4e1 / 0.9e1 * t131 * t28 * t120 - 0.5e1 / 0.9e1 * t135 * t28 * t120))
  vrho_0_ = 0.2e1 * r0 * t144 + 0.2e1 * t78
  t151 = t29 * t32
  t153 = t116 * t151 * t36
  t171 = t88 * t37 * t59
  t187 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t87 * t88 * t37 / 0.24e2 + t97 * t98 * t153 / 0.12e2 + t103 * t98 * t153 / 0.8e1 + t107 * t98 * t153 / 0.6e1 + 0.5e1 / 0.24e2 * t111 * t98 * t153 + t117 * t151 * t36 * t59 / 0.24e2 + t123 * t23 * t171 / 0.12e2 + t127 * t23 * t171 / 0.8e1 + t131 * t23 * t171 / 0.6e1 + 0.5e1 / 0.24e2 * t135 * t23 * t171))
  vsigma_0_ = 0.2e1 * r0 * t187
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
  t23 = params.a[1]
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = params.mu * t24
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = t25 * t29
  t31 = 0.1e1 / params.kappa
  t32 = t31 * s0
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = r0 ** 2
  t37 = 0.1e1 / t19 / t35
  t38 = t34 * t37
  t41 = t30 * t32 * t38 / 0.24e2
  t42 = 0.1e1 + t41
  t44 = 0.1e1 - 0.1e1 / t42
  t46 = params.a[2]
  t47 = t44 ** 2
  t49 = params.a[3]
  t50 = t47 * t44
  t52 = params.a[4]
  t53 = t47 ** 2
  t55 = params.a[5]
  t59 = params.b[1]
  t60 = jnp.exp(-t41)
  t61 = 0.1e1 - t60
  t63 = params.b[2]
  t64 = t61 ** 2
  t66 = params.b[3]
  t67 = t64 * t61
  t69 = params.b[4]
  t70 = t64 ** 2
  t72 = params.b[5]
  t75 = t55 * t53 * t44 + t72 * t70 * t61 + t23 * t44 + t46 * t47 + t49 * t50 + t52 * t53 + t59 * t61 + t63 * t64 + t66 * t67 + t69 * t70 + params.a[0] + params.b[0]
  t79 = t17 * t18
  t80 = t42 ** 2
  t81 = 0.1e1 / t80
  t83 = t23 * t81 * t25
  t84 = t29 * t31
  t85 = s0 * t34
  t86 = t35 * r0
  t88 = 0.1e1 / t19 / t86
  t90 = t84 * t85 * t88
  t93 = t46 * t44
  t94 = t81 * params.mu
  t95 = t94 * t24
  t96 = t93 * t95
  t99 = t49 * t47
  t100 = t99 * t95
  t103 = t52 * t50
  t104 = t103 * t95
  t107 = t55 * t53
  t108 = t107 * t95
  t112 = t24 * t29
  t113 = t59 * params.mu * t112
  t114 = t34 * t88
  t115 = t114 * t60
  t116 = t32 * t115
  t119 = t63 * t61
  t120 = t119 * t30
  t123 = t66 * t64
  t124 = t123 * t30
  t127 = t69 * t67
  t128 = t127 * t30
  t131 = t72 * t70
  t132 = t131 * t30
  t135 = -t83 * t90 / 0.9e1 - 0.2e1 / 0.9e1 * t96 * t90 - t100 * t90 / 0.3e1 - 0.4e1 / 0.9e1 * t104 * t90 - 0.5e1 / 0.9e1 * t108 * t90 - t113 * t116 / 0.9e1 - 0.2e1 / 0.9e1 * t120 * t116 - t124 * t116 / 0.3e1 - 0.4e1 / 0.9e1 * t128 * t116 - 0.5e1 / 0.9e1 * t132 * t116
  t140 = f.my_piecewise3(t2, 0, -t6 * t21 * t75 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t79 * t135)
  t151 = params.mu ** 2
  t152 = t24 ** 2
  t153 = t151 * t152
  t155 = 0.1e1 / t27 / t26
  t156 = t153 * t155
  t157 = t127 * t156
  t158 = params.kappa ** 2
  t159 = 0.1e1 / t158
  t160 = s0 ** 2
  t161 = t159 * t160
  t162 = t35 ** 2
  t165 = 0.1e1 / t18 / t162 / t86
  t166 = t33 * t165
  t168 = t161 * t166 * t60
  t171 = t49 * t44
  t172 = t80 ** 2
  t173 = 0.1e1 / t172
  t174 = t173 * t151
  t175 = t174 * t152
  t176 = t171 * t175
  t177 = t155 * t159
  t180 = t177 * t160 * t33 * t165
  t184 = 0.1e1 / t80 / t42
  t185 = t184 * t151
  t186 = t185 * t152
  t187 = t99 * t186
  t190 = t52 * t47
  t191 = t190 * t175
  t194 = t103 * t186
  t197 = t55 * t50
  t198 = t197 * t175
  t201 = t107 * t186
  t204 = t93 * t186
  t208 = 0.1e1 / t19 / t162
  t210 = t84 * t85 * t208
  t221 = t32 * t34 * t208 * t60
  t226 = -0.8e1 / 0.81e2 * t157 * t168 + 0.4e1 / 0.27e2 * t176 * t180 - 0.4e1 / 0.27e2 * t187 * t180 + 0.8e1 / 0.27e2 * t191 * t180 - 0.16e2 / 0.81e2 * t194 * t180 + 0.40e2 / 0.81e2 * t198 * t180 - 0.20e2 / 0.81e2 * t201 * t180 - 0.8e1 / 0.81e2 * t204 * t180 + 0.22e2 / 0.27e2 * t96 * t210 + 0.11e2 / 0.9e1 * t100 * t210 + 0.44e2 / 0.27e2 * t104 * t210 + 0.55e2 / 0.27e2 * t108 * t210 + 0.22e2 / 0.27e2 * t120 * t221 + 0.11e2 / 0.9e1 * t124 * t221
  t231 = t72 * t67
  t232 = t231 * t156
  t233 = t60 ** 2
  t235 = t161 * t166 * t233
  t238 = t131 * t156
  t241 = t119 * t156
  t244 = t66 * t61
  t245 = t244 * t156
  t248 = t123 * t156
  t251 = t69 * t64
  t252 = t251 * t156
  t260 = t23 * t184 * t153
  t264 = t46 * t173 * t153
  t268 = t152 * t155
  t269 = t59 * t151 * t268
  t273 = t63 * t151 * t268
  t276 = 0.44e2 / 0.27e2 * t128 * t221 + 0.55e2 / 0.27e2 * t132 * t221 + 0.40e2 / 0.81e2 * t232 * t235 - 0.10e2 / 0.81e2 * t238 * t168 - 0.4e1 / 0.81e2 * t241 * t168 + 0.4e1 / 0.27e2 * t245 * t235 - 0.2e1 / 0.27e2 * t248 * t168 + 0.8e1 / 0.27e2 * t252 * t235 + 0.11e2 / 0.27e2 * t113 * t221 + 0.11e2 / 0.27e2 * t83 * t210 - 0.4e1 / 0.81e2 * t260 * t180 + 0.4e1 / 0.81e2 * t264 * t180 - 0.2e1 / 0.81e2 * t269 * t168 + 0.4e1 / 0.81e2 * t273 * t235
  t282 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t75 / 0.12e2 - t6 * t21 * t135 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t79 * (t226 + t276))
  v2rho2_0_ = 0.2e1 * r0 * t282 + 0.4e1 * t140
  t288 = t93 * t94
  t289 = t31 * t34
  t291 = t112 * t289 * t37
  t294 = t99 * t94
  t297 = t103 * t94
  t300 = t107 * t94
  t307 = t119 * t25
  t309 = t84 * t38 * t60
  t312 = t123 * t25
  t315 = t127 * t25
  t318 = t131 * t25
  t321 = t83 * t84 * t38 / 0.24e2 + t288 * t291 / 0.12e2 + t294 * t291 / 0.8e1 + t297 * t291 / 0.6e1 + 0.5e1 / 0.24e2 * t300 * t291 + t113 * t289 * t37 * t60 / 0.24e2 + t307 * t309 / 0.12e2 + t312 * t309 / 0.8e1 + t315 * t309 / 0.6e1 + 0.5e1 / 0.24e2 * t318 * t309
  t325 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t79 * t321)
  t338 = 0.1e1 / t18 / t162 / t35
  t341 = t177 * t33 * t338 * s0
  t350 = t159 * t33
  t353 = t350 * t338 * t233 * s0
  t358 = t350 * t338 * s0 * t60
  t373 = -t113 * t289 * t88 * t60 / 0.9e1 - t83 * t84 * t114 / 0.9e1 + 0.2e1 / 0.27e2 * t194 * t341 - 0.5e1 / 0.27e2 * t198 * t341 + 0.5e1 / 0.54e2 * t201 * t341 + t204 * t341 / 0.27e2 - t252 * t353 / 0.9e1 + t157 * t358 / 0.27e2 - 0.5e1 / 0.27e2 * t232 * t353 + 0.5e1 / 0.108e3 * t238 * t358 + t241 * t358 / 0.54e2 - t245 * t353 / 0.18e2 + t248 * t358 / 0.36e2 - t176 * t341 / 0.18e2
  t378 = t84 * t115
  t388 = t112 * t289 * t88
  t405 = t187 * t341 / 0.18e2 - t191 * t341 / 0.9e1 - 0.5e1 / 0.9e1 * t318 * t378 - 0.2e1 / 0.9e1 * t307 * t378 - t312 * t378 / 0.3e1 - 0.4e1 / 0.9e1 * t315 * t378 - t294 * t388 / 0.3e1 - 0.4e1 / 0.9e1 * t297 * t388 - 0.5e1 / 0.9e1 * t300 * t388 - 0.2e1 / 0.9e1 * t288 * t388 + t260 * t341 / 0.54e2 - t264 * t341 / 0.54e2 + t269 * t358 / 0.108e3 - t273 * t353 / 0.54e2
  t411 = f.my_piecewise3(t2, 0, -t6 * t21 * t321 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t79 * (t373 + t405))
  v2rhosigma_0_ = 0.2e1 * r0 * t411 + 0.2e1 * t325
  t416 = 0.1e1 / t18 / t162 / r0
  t417 = t33 * t416
  t418 = t177 * t417
  t425 = t268 * t350 * t416
  t456 = t177 * t417 * t60
  t461 = t177 * t417 * t233
  t479 = -t260 * t418 / 0.144e3 + t264 * t418 / 0.144e3 - t93 * t185 * t425 / 0.72e2 + t171 * t174 * t425 / 0.48e2 - t99 * t185 * t425 / 0.48e2 + t190 * t174 * t425 / 0.24e2 - t103 * t185 * t425 / 0.36e2 + 0.5e1 / 0.72e2 * t197 * t174 * t425 - 0.5e1 / 0.144e3 * t107 * t185 * t425 - t269 * t350 * t416 * t60 / 0.288e3 + t273 * t350 * t416 * t233 / 0.144e3 - t119 * t153 * t456 / 0.144e3 + t244 * t153 * t461 / 0.48e2 - t123 * t153 * t456 / 0.96e2 + t251 * t153 * t461 / 0.24e2 - t127 * t153 * t456 / 0.72e2 + 0.5e1 / 0.72e2 * t231 * t153 * t461 - 0.5e1 / 0.288e3 * t131 * t153 * t456
  t483 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t79 * t479)
  v2sigma2_0_ = 0.2e1 * r0 * t483
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
  t24 = params.a[1]
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = params.mu * t25
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = t26 * t30
  t32 = 0.1e1 / params.kappa
  t33 = t32 * s0
  t34 = 2 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = r0 ** 2
  t38 = 0.1e1 / t19 / t36
  t42 = t31 * t33 * t35 * t38 / 0.24e2
  t43 = 0.1e1 + t42
  t45 = 0.1e1 - 0.1e1 / t43
  t47 = params.a[2]
  t48 = t45 ** 2
  t50 = params.a[3]
  t51 = t48 * t45
  t53 = params.a[4]
  t54 = t48 ** 2
  t56 = params.a[5]
  t60 = params.b[1]
  t61 = jnp.exp(-t42)
  t62 = 0.1e1 - t61
  t64 = params.b[2]
  t65 = t62 ** 2
  t67 = params.b[3]
  t68 = t65 * t62
  t70 = params.b[4]
  t71 = t65 ** 2
  t73 = params.b[5]
  t76 = t56 * t54 * t45 + t73 * t71 * t62 + t24 * t45 + t47 * t48 + t50 * t51 + t53 * t54 + t60 * t62 + t64 * t65 + t67 * t68 + t70 * t71 + params.a[0] + params.b[0]
  t81 = t17 / t19
  t82 = t43 ** 2
  t83 = 0.1e1 / t82
  t85 = t24 * t83 * t26
  t86 = t30 * t32
  t87 = s0 * t35
  t88 = t36 * r0
  t90 = 0.1e1 / t19 / t88
  t92 = t86 * t87 * t90
  t95 = t47 * t45
  t97 = t83 * params.mu * t25
  t98 = t95 * t97
  t101 = t50 * t48
  t102 = t101 * t97
  t105 = t53 * t51
  t106 = t105 * t97
  t109 = t56 * t54
  t110 = t109 * t97
  t115 = t60 * params.mu * t25 * t30
  t118 = t33 * t35 * t90 * t61
  t121 = t64 * t62
  t122 = t121 * t31
  t125 = t67 * t65
  t126 = t125 * t31
  t129 = t70 * t68
  t130 = t129 * t31
  t133 = t73 * t71
  t134 = t133 * t31
  t137 = -t85 * t92 / 0.9e1 - 0.2e1 / 0.9e1 * t98 * t92 - t102 * t92 / 0.3e1 - 0.4e1 / 0.9e1 * t106 * t92 - 0.5e1 / 0.9e1 * t110 * t92 - t115 * t118 / 0.9e1 - 0.2e1 / 0.9e1 * t122 * t118 - t126 * t118 / 0.3e1 - 0.4e1 / 0.9e1 * t130 * t118 - 0.5e1 / 0.9e1 * t134 * t118
  t141 = t17 * t18
  t142 = t36 ** 2
  t144 = 0.1e1 / t19 / t142
  t146 = t86 * t87 * t144
  t157 = t33 * t35 * t144 * t61
  t166 = t73 * t68
  t167 = params.mu ** 2
  t168 = t25 ** 2
  t169 = t167 * t168
  t171 = 0.1e1 / t28 / t27
  t172 = t169 * t171
  t173 = t166 * t172
  t174 = params.kappa ** 2
  t175 = 0.1e1 / t174
  t176 = s0 ** 2
  t177 = t175 * t176
  t180 = 0.1e1 / t18 / t142 / t88
  t181 = t34 * t180
  t182 = t61 ** 2
  t184 = t177 * t181 * t182
  t187 = t133 * t172
  t189 = t177 * t181 * t61
  t192 = t121 * t172
  t195 = t67 * t62
  t196 = t195 * t172
  t199 = t125 * t172
  t202 = t70 * t65
  t203 = t202 * t172
  t206 = 0.22e2 / 0.27e2 * t98 * t146 + 0.11e2 / 0.9e1 * t102 * t146 + 0.44e2 / 0.27e2 * t106 * t146 + 0.55e2 / 0.27e2 * t110 * t146 + 0.22e2 / 0.27e2 * t122 * t157 + 0.11e2 / 0.9e1 * t126 * t157 + 0.44e2 / 0.27e2 * t130 * t157 + 0.55e2 / 0.27e2 * t134 * t157 + 0.40e2 / 0.81e2 * t173 * t184 - 0.10e2 / 0.81e2 * t187 * t189 - 0.4e1 / 0.81e2 * t192 * t189 + 0.4e1 / 0.27e2 * t196 * t184 - 0.2e1 / 0.27e2 * t199 * t189 + 0.8e1 / 0.27e2 * t203 * t184
  t207 = t129 * t172
  t210 = t50 * t45
  t211 = t82 ** 2
  t212 = 0.1e1 / t211
  t214 = t212 * t167 * t168
  t215 = t210 * t214
  t216 = t171 * t175
  t217 = t176 * t34
  t219 = t216 * t217 * t180
  t223 = 0.1e1 / t82 / t43
  t225 = t223 * t167 * t168
  t226 = t101 * t225
  t229 = t53 * t48
  t230 = t229 * t214
  t233 = t105 * t225
  t236 = t56 * t51
  t237 = t236 * t214
  t240 = t109 * t225
  t243 = t95 * t225
  t251 = t24 * t223 * t169
  t255 = t47 * t212 * t169
  t259 = t168 * t171
  t260 = t60 * t167 * t259
  t264 = t64 * t167 * t259
  t267 = -0.8e1 / 0.81e2 * t207 * t189 + 0.4e1 / 0.27e2 * t215 * t219 - 0.4e1 / 0.27e2 * t226 * t219 + 0.8e1 / 0.27e2 * t230 * t219 - 0.16e2 / 0.81e2 * t233 * t219 + 0.40e2 / 0.81e2 * t237 * t219 - 0.20e2 / 0.81e2 * t240 * t219 - 0.8e1 / 0.81e2 * t243 * t219 + 0.11e2 / 0.27e2 * t115 * t157 + 0.11e2 / 0.27e2 * t85 * t146 - 0.4e1 / 0.81e2 * t251 * t219 + 0.4e1 / 0.81e2 * t255 * t219 - 0.2e1 / 0.81e2 * t260 * t189 + 0.4e1 / 0.81e2 * t264 * t184
  t268 = t206 + t267
  t273 = f.my_piecewise3(t2, 0, t6 * t22 * t76 / 0.12e2 - t6 * t81 * t137 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t141 * t268)
  t286 = 0.1e1 / t211 / t43
  t287 = t167 * params.mu
  t288 = t286 * t287
  t290 = t27 ** 2
  t291 = 0.1e1 / t290
  t293 = 0.1e1 / t174 / params.kappa
  t295 = t176 * s0
  t296 = t142 ** 2
  t298 = 0.1e1 / t296 / t88
  t300 = t291 * t293 * t295 * t298
  t303 = t212 * t287
  t311 = t287 * t291
  t313 = t293 * t295
  t316 = t313 * t298 * t182 * t61
  t321 = t313 * t298 * t182
  t326 = t313 * t298 * t61
  t351 = 0.320e3 / 0.81e2 * t236 * t288 * t300 - 0.80e2 / 0.81e2 * t109 * t303 * t300 - 0.32e2 / 0.81e2 * t95 * t303 * t300 - 0.160e3 / 0.81e2 * t73 * t65 * t311 * t316 + 0.160e3 / 0.81e2 * t166 * t311 * t321 - 0.40e2 / 0.243e3 * t133 * t311 * t326 - 0.16e2 / 0.243e3 * t121 * t311 * t326 + 0.16e2 / 0.27e2 * t195 * t311 * t321 - 0.8e1 / 0.81e2 * t125 * t311 * t326 - 0.64e2 / 0.81e2 * t70 * t62 * t311 * t316 + 0.32e2 / 0.27e2 * t202 * t311 * t321 - 0.32e2 / 0.243e3 * t129 * t311 * t326 + 0.32e2 / 0.27e2 * t210 * t288 * t300
  t357 = 0.1e1 / t211 / t82
  t358 = t357 * t287
  t373 = 0.1e1 / t18 / t296
  t375 = t216 * t217 * t373
  t390 = 0.1e1 / t19 / t142 / r0
  t392 = t86 * t87 * t390
  t397 = -0.16e2 / 0.27e2 * t101 * t303 * t300 - 0.64e2 / 0.81e2 * t53 * t45 * t358 * t300 + 0.64e2 / 0.27e2 * t229 * t288 * t300 - 0.64e2 / 0.81e2 * t105 * t303 * t300 - 0.160e3 / 0.81e2 * t56 * t48 * t358 * t300 + 0.44e2 / 0.27e2 * t226 * t375 - 0.88e2 / 0.27e2 * t230 * t375 + 0.176e3 / 0.81e2 * t233 * t375 - 0.440e3 / 0.81e2 * t237 * t375 + 0.220e3 / 0.81e2 * t240 * t375 + 0.88e2 / 0.81e2 * t243 * t375 - 0.308e3 / 0.81e2 * t98 * t392 - 0.154e3 / 0.27e2 * t102 * t392
  t405 = t33 * t35 * t390 * t61
  t414 = t34 * t373
  t416 = t177 * t414 * t182
  t420 = t177 * t414 * t61
  t433 = -0.616e3 / 0.81e2 * t106 * t392 - 0.770e3 / 0.81e2 * t110 * t392 - 0.308e3 / 0.81e2 * t122 * t405 - 0.154e3 / 0.27e2 * t126 * t405 - 0.616e3 / 0.81e2 * t130 * t405 - 0.770e3 / 0.81e2 * t134 * t405 - 0.44e2 / 0.27e2 * t196 * t416 + 0.22e2 / 0.27e2 * t199 * t420 - 0.88e2 / 0.27e2 * t203 * t416 + 0.88e2 / 0.81e2 * t207 * t420 - 0.440e3 / 0.81e2 * t173 * t416 + 0.110e3 / 0.81e2 * t187 * t420 - 0.44e2 / 0.27e2 * t215 * t375
  t472 = 0.44e2 / 0.81e2 * t192 * t420 - 0.16e2 / 0.81e2 * t67 * t287 * t291 * t316 - 0.16e2 / 0.81e2 * t50 * t357 * t287 * t300 - 0.16e2 / 0.81e2 * t24 * t212 * t287 * t300 - 0.8e1 / 0.243e3 * t60 * t287 * t291 * t326 + 0.32e2 / 0.81e2 * t47 * t286 * t287 * t300 + 0.16e2 / 0.81e2 * t64 * t287 * t291 * t321 - 0.154e3 / 0.81e2 * t85 * t392 - 0.154e3 / 0.81e2 * t115 * t405 - 0.44e2 / 0.81e2 * t255 * t375 - 0.44e2 / 0.81e2 * t264 * t416 + 0.22e2 / 0.81e2 * t260 * t420 + 0.44e2 / 0.81e2 * t251 * t375
  t479 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t38 * t76 + t6 * t22 * t137 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t81 * t268 - 0.3e1 / 0.8e1 * t6 * t141 * (t351 + t397 + t433 + t472))
  v3rho3_0_ = 0.2e1 * r0 * t479 + 0.6e1 * t273

  res = {'v3rho3': v3rho3_0_}
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
  t32 = params.a[0]
  t33 = params.a[1]
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = params.mu * t34
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t40 = t35 * t39
  t41 = 0.1e1 / params.kappa
  t42 = t41 * s0
  t43 = r0 ** 2
  t44 = r0 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t50 = t40 * t42 / t45 / t43 / 0.24e2
  t51 = 0.1e1 + t50
  t53 = 0.1e1 - 0.1e1 / t51
  t55 = params.a[2]
  t56 = t53 ** 2
  t58 = params.a[3]
  t59 = t56 * t53
  t61 = params.a[4]
  t62 = t56 ** 2
  t64 = params.a[5]
  t67 = params.b[0]
  t68 = params.b[1]
  t69 = jnp.exp(-t50)
  t70 = 0.1e1 - t69
  t72 = params.b[2]
  t73 = t70 ** 2
  t75 = params.b[3]
  t76 = t73 * t70
  t78 = params.b[4]
  t79 = t73 ** 2
  t81 = params.b[5]
  t84 = t64 * t62 * t53 + t81 * t79 * t70 + t33 * t53 + t55 * t56 + t58 * t59 + t61 * t62 + t68 * t70 + t72 * t73 + t75 * t76 + t78 * t79 + t32 + t67
  t88 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t89 = t88 * f.p.zeta_threshold
  t91 = f.my_piecewise3(t20, t89, t21 * t19)
  t92 = t30 ** 2
  t93 = 0.1e1 / t92
  t94 = t91 * t93
  t97 = t5 * t94 * t84 / 0.8e1
  t98 = t91 * t30
  t99 = t51 ** 2
  t100 = 0.1e1 / t99
  t102 = t33 * t100 * t35
  t103 = t39 * t41
  t104 = t43 * r0
  t106 = 0.1e1 / t45 / t104
  t107 = s0 * t106
  t111 = t55 * t53
  t112 = t100 * params.mu
  t113 = t111 * t112
  t114 = t34 * t39
  t116 = t114 * t42 * t106
  t119 = t58 * t56
  t120 = t119 * t112
  t123 = t61 * t59
  t124 = t123 * t112
  t127 = t64 * t62
  t128 = t127 * t112
  t132 = t68 * params.mu * t114
  t137 = t72 * t70
  t138 = t137 * t35
  t140 = t103 * t107 * t69
  t143 = t75 * t73
  t144 = t143 * t35
  t147 = t78 * t76
  t148 = t147 * t35
  t151 = t81 * t79
  t152 = t151 * t35
  t155 = -t102 * t103 * t107 / 0.9e1 - 0.2e1 / 0.9e1 * t113 * t116 - t120 * t116 / 0.3e1 - 0.4e1 / 0.9e1 * t124 * t116 - 0.5e1 / 0.9e1 * t128 * t116 - t132 * t42 * t106 * t69 / 0.9e1 - 0.2e1 / 0.9e1 * t138 * t140 - t144 * t140 / 0.3e1 - 0.4e1 / 0.9e1 * t148 * t140 - 0.5e1 / 0.9e1 * t152 * t140
  t160 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t84 - t97 - 0.3e1 / 0.8e1 * t5 * t98 * t155)
  t162 = r1 <= f.p.dens_threshold
  t163 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t164 = 0.1e1 + t163
  t165 = t164 <= f.p.zeta_threshold
  t166 = t164 ** (0.1e1 / 0.3e1)
  t168 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t171 = f.my_piecewise3(t165, 0, 0.4e1 / 0.3e1 * t166 * t168)
  t172 = t171 * t30
  t173 = t41 * s2
  t174 = r1 ** 2
  t175 = r1 ** (0.1e1 / 0.3e1)
  t176 = t175 ** 2
  t181 = t40 * t173 / t176 / t174 / 0.24e2
  t182 = 0.1e1 + t181
  t184 = 0.1e1 - 0.1e1 / t182
  t186 = t184 ** 2
  t188 = t186 * t184
  t190 = t186 ** 2
  t194 = jnp.exp(-t181)
  t195 = 0.1e1 - t194
  t197 = t195 ** 2
  t199 = t197 * t195
  t201 = t197 ** 2
  t205 = t64 * t190 * t184 + t81 * t201 * t195 + t33 * t184 + t55 * t186 + t58 * t188 + t61 * t190 + t68 * t195 + t72 * t197 + t75 * t199 + t78 * t201 + t32 + t67
  t210 = f.my_piecewise3(t165, t89, t166 * t164)
  t211 = t210 * t93
  t214 = t5 * t211 * t205 / 0.8e1
  t216 = f.my_piecewise3(t162, 0, -0.3e1 / 0.8e1 * t5 * t172 * t205 - t214)
  t218 = t21 ** 2
  t219 = 0.1e1 / t218
  t220 = t26 ** 2
  t225 = t16 / t22 / t6
  t227 = -0.2e1 * t23 + 0.2e1 * t225
  t228 = f.my_piecewise5(t10, 0, t14, 0, t227)
  t232 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t219 * t220 + 0.4e1 / 0.3e1 * t21 * t228)
  t239 = t5 * t29 * t93 * t84
  t245 = 0.1e1 / t92 / t6
  t249 = t5 * t91 * t245 * t84 / 0.12e2
  t251 = t5 * t94 * t155
  t253 = t43 ** 2
  t255 = 0.1e1 / t45 / t253
  t257 = t114 * t42 * t255
  t265 = 0.1e1 / t99 / t51
  t266 = params.mu ** 2
  t267 = t265 * t266
  t269 = t34 ** 2
  t271 = 0.1e1 / t37 / t36
  t272 = t269 * t271
  t273 = params.kappa ** 2
  t274 = 0.1e1 / t273
  t275 = s0 ** 2
  t276 = t274 * t275
  t279 = 0.1e1 / t44 / t253 / t104
  t281 = t272 * t276 * t279
  t285 = t99 ** 2
  t286 = 0.1e1 / t285
  t287 = t286 * t266
  t308 = t266 * t269
  t310 = t271 * t274
  t311 = t275 * t279
  t313 = t310 * t311 * t69
  t318 = t69 ** 2
  t320 = t310 * t311 * t318
  t330 = 0.11e2 / 0.9e1 * t120 * t257 + 0.44e2 / 0.27e2 * t124 * t257 + 0.55e2 / 0.27e2 * t128 * t257 - 0.4e1 / 0.81e2 * t111 * t267 * t281 + 0.2e1 / 0.27e2 * t58 * t53 * t287 * t281 - 0.2e1 / 0.27e2 * t119 * t267 * t281 + 0.4e1 / 0.27e2 * t61 * t56 * t287 * t281 - 0.8e1 / 0.81e2 * t123 * t267 * t281 + 0.20e2 / 0.81e2 * t64 * t59 * t287 * t281 - 0.10e2 / 0.81e2 * t127 * t267 * t281 - 0.2e1 / 0.81e2 * t137 * t308 * t313 + 0.2e1 / 0.27e2 * t75 * t70 * t308 * t320 - t143 * t308 * t313 / 0.27e2 + 0.4e1 / 0.27e2 * t78 * t73 * t308 * t320
  t341 = s0 * t255
  t343 = t103 * t341 * t69
  t355 = t72 * t266 * t272
  t369 = t310 * t311
  t377 = t68 * t266 * t272
  t382 = -0.4e1 / 0.81e2 * t147 * t308 * t313 + 0.20e2 / 0.81e2 * t81 * t76 * t308 * t320 - 0.5e1 / 0.81e2 * t151 * t308 * t313 + 0.22e2 / 0.27e2 * t138 * t343 + 0.11e2 / 0.9e1 * t144 * t343 + 0.44e2 / 0.27e2 * t148 * t343 + 0.55e2 / 0.27e2 * t152 * t343 + 0.22e2 / 0.27e2 * t113 * t257 + 0.2e1 / 0.81e2 * t355 * t276 * t279 * t318 + 0.11e2 / 0.27e2 * t102 * t103 * t341 + 0.11e2 / 0.27e2 * t132 * t42 * t255 * t69 - 0.2e1 / 0.81e2 * t33 * t265 * t308 * t369 + 0.2e1 / 0.81e2 * t55 * t286 * t308 * t369 - t377 * t276 * t279 * t69 / 0.81e2
  t388 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t232 * t30 * t84 - t239 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t155 + t249 - t251 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t98 * (t330 + t382))
  t389 = t166 ** 2
  t390 = 0.1e1 / t389
  t391 = t168 ** 2
  t395 = f.my_piecewise5(t14, 0, t10, 0, -t227)
  t399 = f.my_piecewise3(t165, 0, 0.4e1 / 0.9e1 * t390 * t391 + 0.4e1 / 0.3e1 * t166 * t395)
  t406 = t5 * t171 * t93 * t205
  t411 = t5 * t210 * t245 * t205 / 0.12e2
  t413 = f.my_piecewise3(t162, 0, -0.3e1 / 0.8e1 * t5 * t399 * t30 * t205 - t406 / 0.4e1 + t411)
  d11 = 0.2e1 * t160 + 0.2e1 * t216 + t6 * (t388 + t413)
  t416 = -t7 - t24
  t417 = f.my_piecewise5(t10, 0, t14, 0, t416)
  t420 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t417)
  t421 = t420 * t30
  t426 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t421 * t84 - t97)
  t428 = f.my_piecewise5(t14, 0, t10, 0, -t416)
  t431 = f.my_piecewise3(t165, 0, 0.4e1 / 0.3e1 * t166 * t428)
  t432 = t431 * t30
  t436 = t210 * t30
  t437 = t182 ** 2
  t438 = 0.1e1 / t437
  t440 = t33 * t438 * t35
  t441 = t174 * r1
  t443 = 0.1e1 / t176 / t441
  t444 = s2 * t443
  t448 = t55 * t184
  t449 = t438 * params.mu
  t450 = t448 * t449
  t452 = t114 * t173 * t443
  t455 = t58 * t186
  t456 = t455 * t449
  t459 = t61 * t188
  t460 = t459 * t449
  t463 = t64 * t190
  t464 = t463 * t449
  t471 = t72 * t195
  t472 = t471 * t35
  t474 = t103 * t444 * t194
  t477 = t75 * t197
  t478 = t477 * t35
  t481 = t78 * t199
  t482 = t481 * t35
  t485 = t81 * t201
  t486 = t485 * t35
  t489 = -t440 * t103 * t444 / 0.9e1 - 0.2e1 / 0.9e1 * t450 * t452 - t456 * t452 / 0.3e1 - 0.4e1 / 0.9e1 * t460 * t452 - 0.5e1 / 0.9e1 * t464 * t452 - t132 * t173 * t443 * t194 / 0.9e1 - 0.2e1 / 0.9e1 * t472 * t474 - t478 * t474 / 0.3e1 - 0.4e1 / 0.9e1 * t482 * t474 - 0.5e1 / 0.9e1 * t486 * t474
  t494 = f.my_piecewise3(t162, 0, -0.3e1 / 0.8e1 * t5 * t432 * t205 - t214 - 0.3e1 / 0.8e1 * t5 * t436 * t489)
  t498 = 0.2e1 * t225
  t499 = f.my_piecewise5(t10, 0, t14, 0, t498)
  t503 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t219 * t417 * t26 + 0.4e1 / 0.3e1 * t21 * t499)
  t510 = t5 * t420 * t93 * t84
  t518 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t503 * t30 * t84 - t510 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t421 * t155 - t239 / 0.8e1 + t249 - t251 / 0.8e1)
  t522 = f.my_piecewise5(t14, 0, t10, 0, -t498)
  t526 = f.my_piecewise3(t165, 0, 0.4e1 / 0.9e1 * t390 * t428 * t168 + 0.4e1 / 0.3e1 * t166 * t522)
  t533 = t5 * t431 * t93 * t205
  t540 = t5 * t211 * t489
  t543 = f.my_piecewise3(t162, 0, -0.3e1 / 0.8e1 * t5 * t526 * t30 * t205 - t533 / 0.8e1 - t406 / 0.8e1 + t411 - 0.3e1 / 0.8e1 * t5 * t172 * t489 - t540 / 0.8e1)
  d12 = t160 + t216 + t426 + t494 + t6 * (t518 + t543)
  t548 = t417 ** 2
  t552 = 0.2e1 * t23 + 0.2e1 * t225
  t553 = f.my_piecewise5(t10, 0, t14, 0, t552)
  t557 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t219 * t548 + 0.4e1 / 0.3e1 * t21 * t553)
  t564 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t557 * t30 * t84 - t510 / 0.4e1 + t249)
  t565 = t428 ** 2
  t569 = f.my_piecewise5(t14, 0, t10, 0, -t552)
  t573 = f.my_piecewise3(t165, 0, 0.4e1 / 0.9e1 * t390 * t565 + 0.4e1 / 0.3e1 * t166 * t569)
  t583 = t174 ** 2
  t585 = 0.1e1 / t176 / t583
  t587 = t114 * t173 * t585
  t593 = 0.1e1 / t437 / t182
  t594 = t593 * t266
  t596 = s2 ** 2
  t597 = t274 * t596
  t600 = 0.1e1 / t175 / t583 / t441
  t602 = t272 * t597 * t600
  t606 = t437 ** 2
  t607 = 0.1e1 / t606
  t608 = t607 * t266
  t630 = t596 * t600
  t632 = t310 * t630 * t194
  t637 = t194 ** 2
  t639 = t310 * t630 * t637
  t652 = 0.11e2 / 0.9e1 * t456 * t587 + 0.44e2 / 0.27e2 * t460 * t587 - 0.4e1 / 0.81e2 * t448 * t594 * t602 + 0.2e1 / 0.27e2 * t58 * t184 * t608 * t602 - 0.2e1 / 0.27e2 * t455 * t594 * t602 + 0.4e1 / 0.27e2 * t61 * t186 * t608 * t602 - 0.8e1 / 0.81e2 * t459 * t594 * t602 + 0.20e2 / 0.81e2 * t64 * t188 * t608 * t602 - 0.10e2 / 0.81e2 * t463 * t594 * t602 - 0.2e1 / 0.81e2 * t471 * t308 * t632 + 0.2e1 / 0.27e2 * t75 * t195 * t308 * t639 - t477 * t308 * t632 / 0.27e2 + 0.4e1 / 0.27e2 * t78 * t197 * t308 * t639 - 0.4e1 / 0.81e2 * t481 * t308 * t632
  t660 = s2 * t585
  t662 = t103 * t660 * t194
  t677 = t310 * t630
  t699 = 0.20e2 / 0.81e2 * t81 * t199 * t308 * t639 - 0.5e1 / 0.81e2 * t485 * t308 * t632 + 0.55e2 / 0.27e2 * t486 * t662 + 0.55e2 / 0.27e2 * t464 * t587 + 0.22e2 / 0.27e2 * t472 * t662 + 0.11e2 / 0.9e1 * t478 * t662 + 0.44e2 / 0.27e2 * t482 * t662 + 0.22e2 / 0.27e2 * t450 * t587 - 0.2e1 / 0.81e2 * t33 * t593 * t308 * t677 + 0.2e1 / 0.81e2 * t55 * t607 * t308 * t677 - t377 * t597 * t600 * t194 / 0.81e2 + 0.2e1 / 0.81e2 * t355 * t597 * t600 * t637 + 0.11e2 / 0.27e2 * t440 * t103 * t660 + 0.11e2 / 0.27e2 * t132 * t173 * t585 * t194
  t705 = f.my_piecewise3(t162, 0, -0.3e1 / 0.8e1 * t5 * t573 * t30 * t205 - t533 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t432 * t489 + t411 - t540 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t436 * (t652 + t699))
  d22 = 0.2e1 * t426 + 0.2e1 * t494 + t6 * (t564 + t705)
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
  t44 = params.a[0]
  t45 = params.a[1]
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = params.mu * t46
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t52 = t47 * t51
  t53 = 0.1e1 / params.kappa
  t54 = t53 * s0
  t55 = r0 ** 2
  t56 = r0 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t62 = t52 * t54 / t57 / t55 / 0.24e2
  t63 = 0.1e1 + t62
  t65 = 0.1e1 - 0.1e1 / t63
  t67 = params.a[2]
  t68 = t65 ** 2
  t70 = params.a[3]
  t71 = t68 * t65
  t73 = params.a[4]
  t74 = t68 ** 2
  t76 = params.a[5]
  t79 = params.b[0]
  t80 = params.b[1]
  t81 = jnp.exp(-t62)
  t82 = 0.1e1 - t81
  t84 = params.b[2]
  t85 = t82 ** 2
  t87 = params.b[3]
  t88 = t85 * t82
  t90 = params.b[4]
  t91 = t85 ** 2
  t93 = params.b[5]
  t96 = t76 * t74 * t65 + t93 * t91 * t82 + t45 * t65 + t67 * t68 + t70 * t71 + t73 * t74 + t80 * t82 + t84 * t85 + t87 * t88 + t90 * t91 + t44 + t79
  t102 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t103 = t42 ** 2
  t104 = 0.1e1 / t103
  t105 = t102 * t104
  t109 = t102 * t42
  t110 = t63 ** 2
  t111 = 0.1e1 / t110
  t113 = t45 * t111 * t47
  t114 = t51 * t53
  t115 = t55 * r0
  t117 = 0.1e1 / t57 / t115
  t118 = s0 * t117
  t122 = t67 * t65
  t123 = t111 * params.mu
  t124 = t122 * t123
  t125 = t46 * t51
  t127 = t125 * t54 * t117
  t130 = t70 * t68
  t131 = t130 * t123
  t134 = t73 * t71
  t135 = t134 * t123
  t138 = t76 * t74
  t139 = t138 * t123
  t143 = t80 * params.mu * t125
  t148 = t84 * t82
  t149 = t148 * t47
  t151 = t114 * t118 * t81
  t154 = t87 * t85
  t155 = t154 * t47
  t158 = t90 * t88
  t159 = t158 * t47
  t162 = t93 * t91
  t163 = t162 * t47
  t166 = -t113 * t114 * t118 / 0.9e1 - 0.2e1 / 0.9e1 * t124 * t127 - t131 * t127 / 0.3e1 - 0.4e1 / 0.9e1 * t135 * t127 - 0.5e1 / 0.9e1 * t139 * t127 - t143 * t54 * t117 * t81 / 0.9e1 - 0.2e1 / 0.9e1 * t149 * t151 - t155 * t151 / 0.3e1 - 0.4e1 / 0.9e1 * t159 * t151 - 0.5e1 / 0.9e1 * t163 * t151
  t170 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t171 = t170 * f.p.zeta_threshold
  t173 = f.my_piecewise3(t20, t171, t21 * t19)
  t175 = 0.1e1 / t103 / t6
  t176 = t173 * t175
  t180 = t173 * t104
  t184 = t173 * t42
  t186 = 0.1e1 / t110 / t63
  t188 = params.mu ** 2
  t189 = t46 ** 2
  t190 = t188 * t189
  t191 = t45 * t186 * t190
  t193 = 0.1e1 / t49 / t48
  t194 = params.kappa ** 2
  t195 = 0.1e1 / t194
  t196 = t193 * t195
  t197 = s0 ** 2
  t198 = t55 ** 2
  t201 = 0.1e1 / t56 / t198 / t115
  t202 = t197 * t201
  t203 = t196 * t202
  t206 = t110 ** 2
  t207 = 0.1e1 / t206
  t209 = t67 * t207 * t190
  t213 = t189 * t193
  t214 = t80 * t188 * t213
  t215 = t195 * t197
  t221 = t84 * t188 * t213
  t222 = t81 ** 2
  t228 = 0.1e1 / t57 / t198
  t229 = s0 * t228
  t237 = t158 * t190
  t239 = t196 * t202 * t81
  t242 = t93 * t88
  t243 = t242 * t190
  t245 = t196 * t202 * t222
  t248 = t162 * t190
  t252 = t114 * t229 * t81
  t262 = t125 * t54 * t228
  t265 = -0.2e1 / 0.81e2 * t191 * t203 + 0.2e1 / 0.81e2 * t209 * t203 - t214 * t215 * t201 * t81 / 0.81e2 + 0.2e1 / 0.81e2 * t221 * t215 * t201 * t222 + 0.11e2 / 0.27e2 * t113 * t114 * t229 + 0.11e2 / 0.27e2 * t143 * t54 * t228 * t81 - 0.4e1 / 0.81e2 * t237 * t239 + 0.20e2 / 0.81e2 * t243 * t245 - 0.5e1 / 0.81e2 * t248 * t239 + 0.22e2 / 0.27e2 * t149 * t252 + 0.11e2 / 0.9e1 * t155 * t252 + 0.44e2 / 0.27e2 * t159 * t252 + 0.55e2 / 0.27e2 * t163 * t252 + 0.22e2 / 0.27e2 * t124 * t262
  t272 = t186 * t188
  t273 = t122 * t272
  t275 = t213 * t215 * t201
  t278 = t70 * t65
  t279 = t207 * t188
  t280 = t278 * t279
  t283 = t130 * t272
  t286 = t73 * t68
  t287 = t286 * t279
  t290 = t134 * t272
  t293 = t76 * t71
  t294 = t293 * t279
  t297 = t138 * t272
  t300 = t148 * t190
  t303 = t87 * t82
  t304 = t303 * t190
  t307 = t154 * t190
  t310 = t90 * t85
  t311 = t310 * t190
  t314 = 0.11e2 / 0.9e1 * t131 * t262 + 0.44e2 / 0.27e2 * t135 * t262 + 0.55e2 / 0.27e2 * t139 * t262 - 0.4e1 / 0.81e2 * t273 * t275 + 0.2e1 / 0.27e2 * t280 * t275 - 0.2e1 / 0.27e2 * t283 * t275 + 0.4e1 / 0.27e2 * t287 * t275 - 0.8e1 / 0.81e2 * t290 * t275 + 0.20e2 / 0.81e2 * t294 * t275 - 0.10e2 / 0.81e2 * t297 * t275 - 0.2e1 / 0.81e2 * t300 * t239 + 0.2e1 / 0.27e2 * t304 * t245 - t307 * t239 / 0.27e2 + 0.4e1 / 0.27e2 * t311 * t245
  t315 = t265 + t314
  t320 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t96 - t5 * t105 * t96 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t109 * t166 + t5 * t176 * t96 / 0.12e2 - t5 * t180 * t166 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t184 * t315)
  t322 = r1 <= f.p.dens_threshold
  t323 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t324 = 0.1e1 + t323
  t325 = t324 <= f.p.zeta_threshold
  t326 = t324 ** (0.1e1 / 0.3e1)
  t327 = t326 ** 2
  t328 = 0.1e1 / t327
  t330 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t331 = t330 ** 2
  t335 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t339 = f.my_piecewise3(t325, 0, 0.4e1 / 0.9e1 * t328 * t331 + 0.4e1 / 0.3e1 * t326 * t335)
  t342 = r1 ** 2
  t343 = r1 ** (0.1e1 / 0.3e1)
  t344 = t343 ** 2
  t349 = t52 * t53 * s2 / t344 / t342 / 0.24e2
  t352 = 0.1e1 - 0.1e1 / (0.1e1 + t349)
  t354 = t352 ** 2
  t358 = t354 ** 2
  t362 = jnp.exp(-t349)
  t363 = 0.1e1 - t362
  t365 = t363 ** 2
  t369 = t365 ** 2
  t373 = t70 * t354 * t352 + t76 * t358 * t352 + t87 * t365 * t363 + t93 * t369 * t363 + t45 * t352 + t67 * t354 + t73 * t358 + t80 * t363 + t84 * t365 + t90 * t369 + t44 + t79
  t379 = f.my_piecewise3(t325, 0, 0.4e1 / 0.3e1 * t326 * t330)
  t385 = f.my_piecewise3(t325, t171, t326 * t324)
  t391 = f.my_piecewise3(t322, 0, -0.3e1 / 0.8e1 * t5 * t339 * t42 * t373 - t5 * t379 * t104 * t373 / 0.4e1 + t5 * t385 * t175 * t373 / 0.12e2)
  t401 = t24 ** 2
  t405 = 0.6e1 * t33 - 0.6e1 * t16 / t401
  t406 = f.my_piecewise5(t10, 0, t14, 0, t405)
  t410 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t406)
  t433 = 0.1e1 / t103 / t24
  t444 = t188 * params.mu
  t446 = t48 ** 2
  t447 = 0.1e1 / t446
  t450 = 0.1e1 / t194 / params.kappa
  t451 = t197 * s0
  t452 = t450 * t451
  t453 = t198 ** 2
  t455 = 0.1e1 / t453 / t115
  t457 = t452 * t455 * t222
  t461 = 0.1e1 / t206 / t110
  t466 = t447 * t450 * t451 * t455
  t473 = t452 * t455 * t222 * t81
  t481 = 0.1e1 / t206 / t63
  t489 = t452 * t455 * t81
  t492 = t444 * t447
  t516 = 0.4e1 / 0.81e2 * t84 * t444 * t447 * t457 - 0.4e1 / 0.81e2 * t70 * t461 * t444 * t466 - 0.4e1 / 0.81e2 * t87 * t444 * t447 * t473 - 0.4e1 / 0.81e2 * t45 * t207 * t444 * t466 + 0.8e1 / 0.81e2 * t67 * t481 * t444 * t466 - 0.2e1 / 0.243e3 * t80 * t444 * t447 * t489 - 0.2e1 / 0.81e2 * t154 * t492 * t489 - 0.16e2 / 0.81e2 * t90 * t82 * t492 * t473 + 0.8e1 / 0.27e2 * t310 * t492 * t457 - 0.8e1 / 0.243e3 * t158 * t492 * t489 - 0.40e2 / 0.81e2 * t93 * t85 * t492 * t473 + 0.40e2 / 0.81e2 * t242 * t492 * t457 - 0.10e2 / 0.243e3 * t162 * t492 * t489
  t517 = t207 * t444
  t521 = t481 * t444
  t529 = t461 * t444
  t556 = 0.1e1 / t56 / t453
  t557 = t197 * t556
  t558 = t196 * t557
  t563 = -0.8e1 / 0.81e2 * t122 * t517 * t466 + 0.8e1 / 0.27e2 * t278 * t521 * t466 - 0.4e1 / 0.27e2 * t130 * t517 * t466 - 0.16e2 / 0.81e2 * t73 * t65 * t529 * t466 + 0.16e2 / 0.27e2 * t286 * t521 * t466 - 0.16e2 / 0.81e2 * t134 * t517 * t466 - 0.40e2 / 0.81e2 * t76 * t68 * t529 * t466 + 0.80e2 / 0.81e2 * t293 * t521 * t466 - 0.20e2 / 0.81e2 * t138 * t517 * t466 - 0.4e1 / 0.243e3 * t148 * t492 * t489 + 0.4e1 / 0.27e2 * t303 * t492 * t457 + 0.22e2 / 0.81e2 * t191 * t558 - 0.22e2 / 0.81e2 * t209 * t558
  t575 = 0.1e1 / t57 / t198 / r0
  t576 = s0 * t575
  t585 = t196 * t557 * t81
  t589 = t213 * t215 * t556
  t605 = t125 * t54 * t575
  t608 = 0.11e2 / 0.81e2 * t214 * t215 * t556 * t81 - 0.22e2 / 0.81e2 * t221 * t215 * t556 * t222 - 0.154e3 / 0.81e2 * t113 * t114 * t576 - 0.154e3 / 0.81e2 * t143 * t54 * t575 * t81 + 0.55e2 / 0.81e2 * t248 * t585 + 0.44e2 / 0.81e2 * t273 * t589 - 0.22e2 / 0.27e2 * t280 * t589 + 0.22e2 / 0.27e2 * t283 * t589 - 0.44e2 / 0.27e2 * t287 * t589 + 0.88e2 / 0.81e2 * t290 * t589 - 0.220e3 / 0.81e2 * t294 * t589 + 0.110e3 / 0.81e2 * t297 * t589 - 0.770e3 / 0.81e2 * t139 * t605
  t610 = t114 * t576 * t81
  t628 = t196 * t557 * t222
  t639 = -0.770e3 / 0.81e2 * t163 * t610 - 0.308e3 / 0.81e2 * t124 * t605 - 0.154e3 / 0.27e2 * t131 * t605 - 0.616e3 / 0.81e2 * t135 * t605 - 0.308e3 / 0.81e2 * t149 * t610 - 0.154e3 / 0.27e2 * t155 * t610 - 0.616e3 / 0.81e2 * t159 * t610 + 0.22e2 / 0.81e2 * t300 * t585 - 0.22e2 / 0.27e2 * t304 * t628 + 0.11e2 / 0.27e2 * t307 * t585 - 0.44e2 / 0.27e2 * t311 * t628 + 0.44e2 / 0.81e2 * t237 * t585 - 0.220e3 / 0.81e2 * t243 * t628
  t646 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t410 * t42 * t96 - 0.3e1 / 0.8e1 * t5 * t41 * t104 * t96 - 0.9e1 / 0.8e1 * t5 * t43 * t166 + t5 * t102 * t175 * t96 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t105 * t166 - 0.9e1 / 0.8e1 * t5 * t109 * t315 - 0.5e1 / 0.36e2 * t5 * t173 * t433 * t96 + t5 * t176 * t166 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t180 * t315 - 0.3e1 / 0.8e1 * t5 * t184 * (t516 + t563 + t608 + t639))
  t656 = f.my_piecewise5(t14, 0, t10, 0, -t405)
  t660 = f.my_piecewise3(t325, 0, -0.8e1 / 0.27e2 / t327 / t324 * t331 * t330 + 0.4e1 / 0.3e1 * t328 * t330 * t335 + 0.4e1 / 0.3e1 * t326 * t656)
  t678 = f.my_piecewise3(t322, 0, -0.3e1 / 0.8e1 * t5 * t660 * t42 * t373 - 0.3e1 / 0.8e1 * t5 * t339 * t104 * t373 + t5 * t379 * t175 * t373 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t385 * t433 * t373)
  d111 = 0.3e1 * t320 + 0.3e1 * t391 + t6 * (t646 + t678)

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
  t56 = params.a[0]
  t57 = params.a[1]
  t58 = 6 ** (0.1e1 / 0.3e1)
  t59 = params.mu * t58
  t60 = jnp.pi ** 2
  t61 = t60 ** (0.1e1 / 0.3e1)
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t64 = t59 * t63
  t65 = 0.1e1 / params.kappa
  t66 = t65 * s0
  t67 = r0 ** 2
  t68 = r0 ** (0.1e1 / 0.3e1)
  t69 = t68 ** 2
  t74 = t64 * t66 / t69 / t67 / 0.24e2
  t75 = 0.1e1 + t74
  t77 = 0.1e1 - 0.1e1 / t75
  t79 = params.a[2]
  t80 = t77 ** 2
  t82 = params.a[3]
  t83 = t80 * t77
  t85 = params.a[4]
  t86 = t80 ** 2
  t88 = params.a[5]
  t91 = params.b[0]
  t92 = params.b[1]
  t93 = jnp.exp(-t74)
  t94 = 0.1e1 - t93
  t96 = params.b[2]
  t97 = t94 ** 2
  t99 = params.b[3]
  t100 = t97 * t94
  t102 = params.b[4]
  t103 = t97 ** 2
  t105 = params.b[5]
  t108 = t105 * t103 * t94 + t88 * t86 * t77 + t99 * t100 + t102 * t103 + t57 * t77 + t79 * t80 + t82 * t83 + t85 * t86 + t92 * t94 + t96 * t97 + t56 + t91
  t117 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t118 = t54 ** 2
  t119 = 0.1e1 / t118
  t120 = t117 * t119
  t124 = t117 * t54
  t125 = t75 ** 2
  t126 = 0.1e1 / t125
  t128 = t57 * t126 * t59
  t129 = t63 * t65
  t130 = t67 * r0
  t132 = 0.1e1 / t69 / t130
  t133 = s0 * t132
  t137 = t79 * t77
  t138 = t126 * params.mu
  t139 = t137 * t138
  t140 = t58 * t63
  t142 = t140 * t66 * t132
  t145 = t82 * t80
  t146 = t145 * t138
  t149 = t85 * t83
  t150 = t149 * t138
  t153 = t88 * t86
  t154 = t153 * t138
  t158 = t92 * params.mu * t140
  t163 = t96 * t94
  t164 = t163 * t59
  t166 = t129 * t133 * t93
  t169 = t99 * t97
  t170 = t169 * t59
  t173 = t102 * t100
  t174 = t173 * t59
  t177 = t105 * t103
  t178 = t177 * t59
  t181 = -t128 * t129 * t133 / 0.9e1 - 0.2e1 / 0.9e1 * t139 * t142 - t146 * t142 / 0.3e1 - 0.4e1 / 0.9e1 * t150 * t142 - 0.5e1 / 0.9e1 * t154 * t142 - t158 * t66 * t132 * t93 / 0.9e1 - 0.2e1 / 0.9e1 * t164 * t166 - t170 * t166 / 0.3e1 - 0.4e1 / 0.9e1 * t174 * t166 - 0.5e1 / 0.9e1 * t178 * t166
  t187 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t189 = 0.1e1 / t118 / t6
  t190 = t187 * t189
  t194 = t187 * t119
  t198 = t187 * t54
  t199 = t125 * t75
  t200 = 0.1e1 / t199
  t202 = params.mu ** 2
  t203 = t58 ** 2
  t204 = t202 * t203
  t205 = t57 * t200 * t204
  t207 = 0.1e1 / t61 / t60
  t208 = params.kappa ** 2
  t209 = 0.1e1 / t208
  t210 = t207 * t209
  t211 = s0 ** 2
  t212 = t67 ** 2
  t215 = 0.1e1 / t68 / t212 / t130
  t216 = t211 * t215
  t217 = t210 * t216
  t220 = t125 ** 2
  t221 = 0.1e1 / t220
  t223 = t79 * t221 * t204
  t227 = t203 * t207
  t228 = t92 * t202 * t227
  t229 = t209 * t211
  t235 = t96 * t202 * t227
  t236 = t93 ** 2
  t242 = 0.1e1 / t69 / t212
  t243 = s0 * t242
  t251 = t88 * t83
  t252 = t221 * t202
  t253 = t251 * t252
  t255 = t227 * t229 * t215
  t258 = t200 * t202
  t259 = t153 * t258
  t262 = t163 * t204
  t264 = t210 * t216 * t93
  t267 = t99 * t94
  t268 = t267 * t204
  t270 = t210 * t216 * t236
  t273 = t169 * t204
  t276 = t102 * t97
  t277 = t276 * t204
  t280 = t173 * t204
  t283 = t105 * t100
  t284 = t283 * t204
  t287 = -0.2e1 / 0.81e2 * t205 * t217 + 0.2e1 / 0.81e2 * t223 * t217 - t228 * t229 * t215 * t93 / 0.81e2 + 0.2e1 / 0.81e2 * t235 * t229 * t215 * t236 + 0.11e2 / 0.27e2 * t128 * t129 * t243 + 0.11e2 / 0.27e2 * t158 * t66 * t242 * t93 + 0.20e2 / 0.81e2 * t253 * t255 - 0.10e2 / 0.81e2 * t259 * t255 - 0.2e1 / 0.81e2 * t262 * t264 + 0.2e1 / 0.27e2 * t268 * t270 - t273 * t264 / 0.27e2 + 0.4e1 / 0.27e2 * t277 * t270 - 0.4e1 / 0.81e2 * t280 * t264 + 0.20e2 / 0.81e2 * t284 * t270
  t288 = t177 * t204
  t292 = t129 * t243 * t93
  t302 = t140 * t66 * t242
  t311 = t137 * t258
  t314 = t82 * t77
  t315 = t314 * t252
  t318 = t145 * t258
  t321 = t85 * t80
  t322 = t321 * t252
  t325 = t149 * t258
  t328 = -0.5e1 / 0.81e2 * t288 * t264 + 0.22e2 / 0.27e2 * t164 * t292 + 0.11e2 / 0.9e1 * t170 * t292 + 0.44e2 / 0.27e2 * t174 * t292 + 0.55e2 / 0.27e2 * t178 * t292 + 0.22e2 / 0.27e2 * t139 * t302 + 0.11e2 / 0.9e1 * t146 * t302 + 0.44e2 / 0.27e2 * t150 * t302 + 0.55e2 / 0.27e2 * t154 * t302 - 0.4e1 / 0.81e2 * t311 * t255 + 0.2e1 / 0.27e2 * t315 * t255 - 0.2e1 / 0.27e2 * t318 * t255 + 0.4e1 / 0.27e2 * t322 * t255 - 0.8e1 / 0.81e2 * t325 * t255
  t329 = t287 + t328
  t333 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t334 = t333 * f.p.zeta_threshold
  t336 = f.my_piecewise3(t20, t334, t21 * t19)
  t338 = 0.1e1 / t118 / t25
  t339 = t336 * t338
  t343 = t336 * t189
  t347 = t336 * t119
  t351 = t336 * t54
  t353 = 0.1e1 / t220 / t75
  t354 = t202 * params.mu
  t355 = t353 * t354
  t356 = t251 * t355
  t357 = t60 ** 2
  t358 = 0.1e1 / t357
  t360 = 0.1e1 / t208 / params.kappa
  t361 = t358 * t360
  t362 = t211 * s0
  t363 = t212 ** 2
  t365 = 0.1e1 / t363 / t130
  t367 = t361 * t362 * t365
  t370 = t221 * t354
  t371 = t153 * t370
  t374 = t354 * t358
  t375 = t163 * t374
  t376 = t360 * t362
  t378 = t376 * t365 * t93
  t381 = t267 * t374
  t383 = t376 * t365 * t236
  t386 = t169 * t374
  t389 = t102 * t94
  t390 = t389 * t374
  t391 = t236 * t93
  t393 = t376 * t365 * t391
  t397 = 0.1e1 / t68 / t363
  t398 = t211 * t397
  t399 = t210 * t398
  t414 = 0.1e1 / t69 / t212 / r0
  t415 = s0 * t414
  t423 = t276 * t374
  t426 = 0.80e2 / 0.81e2 * t356 * t367 - 0.20e2 / 0.81e2 * t371 * t367 - 0.4e1 / 0.243e3 * t375 * t378 + 0.4e1 / 0.27e2 * t381 * t383 - 0.2e1 / 0.81e2 * t386 * t378 - 0.16e2 / 0.81e2 * t390 * t393 + 0.22e2 / 0.81e2 * t205 * t399 - 0.22e2 / 0.81e2 * t223 * t399 + 0.11e2 / 0.81e2 * t228 * t229 * t397 * t93 - 0.22e2 / 0.81e2 * t235 * t229 * t397 * t236 - 0.154e3 / 0.81e2 * t128 * t129 * t415 - 0.154e3 / 0.81e2 * t158 * t66 * t414 * t93 + 0.8e1 / 0.27e2 * t423 * t383
  t427 = t173 * t374
  t430 = t105 * t97
  t431 = t430 * t374
  t434 = t283 * t374
  t437 = t177 * t374
  t440 = t137 * t370
  t443 = t314 * t355
  t446 = t145 * t370
  t449 = t85 * t77
  t451 = 0.1e1 / t220 / t125
  t452 = t451 * t354
  t453 = t449 * t452
  t456 = t321 * t355
  t459 = t149 * t370
  t462 = t88 * t80
  t463 = t462 * t452
  t467 = t210 * t398 * t236
  t471 = t210 * t398 * t93
  t474 = -0.8e1 / 0.243e3 * t427 * t378 - 0.40e2 / 0.81e2 * t431 * t393 + 0.40e2 / 0.81e2 * t434 * t383 - 0.10e2 / 0.243e3 * t437 * t378 - 0.8e1 / 0.81e2 * t440 * t367 + 0.8e1 / 0.27e2 * t443 * t367 - 0.4e1 / 0.27e2 * t446 * t367 - 0.16e2 / 0.81e2 * t453 * t367 + 0.16e2 / 0.27e2 * t456 * t367 - 0.16e2 / 0.81e2 * t459 * t367 - 0.40e2 / 0.81e2 * t463 * t367 - 0.220e3 / 0.81e2 * t284 * t467 + 0.55e2 / 0.81e2 * t288 * t471
  t477 = t227 * t229 * t397
  t493 = t140 * t66 * t414
  t497 = t129 * t415 * t93
  t508 = 0.44e2 / 0.81e2 * t311 * t477 - 0.22e2 / 0.27e2 * t315 * t477 + 0.22e2 / 0.27e2 * t318 * t477 - 0.44e2 / 0.27e2 * t322 * t477 + 0.88e2 / 0.81e2 * t325 * t477 - 0.220e3 / 0.81e2 * t253 * t477 + 0.110e3 / 0.81e2 * t259 * t477 - 0.770e3 / 0.81e2 * t154 * t493 - 0.770e3 / 0.81e2 * t178 * t497 - 0.308e3 / 0.81e2 * t139 * t493 - 0.154e3 / 0.27e2 * t146 * t493 - 0.616e3 / 0.81e2 * t150 * t493 - 0.308e3 / 0.81e2 * t164 * t497
  t524 = t96 * t354 * t358
  t528 = t82 * t451 * t354
  t532 = t99 * t354 * t358
  t536 = t57 * t221 * t354
  t540 = t79 * t353 * t354
  t544 = t92 * t354 * t358
  t547 = -0.154e3 / 0.27e2 * t170 * t497 - 0.616e3 / 0.81e2 * t174 * t497 + 0.22e2 / 0.81e2 * t262 * t471 - 0.22e2 / 0.27e2 * t268 * t467 + 0.11e2 / 0.27e2 * t273 * t471 - 0.44e2 / 0.27e2 * t277 * t467 + 0.44e2 / 0.81e2 * t280 * t471 + 0.4e1 / 0.81e2 * t524 * t383 - 0.4e1 / 0.81e2 * t528 * t367 - 0.4e1 / 0.81e2 * t532 * t393 - 0.4e1 / 0.81e2 * t536 * t367 + 0.8e1 / 0.81e2 * t540 * t367 - 0.2e1 / 0.243e3 * t544 * t378
  t549 = t426 + t474 + t508 + t547
  t554 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t108 - 0.3e1 / 0.8e1 * t5 * t120 * t108 - 0.9e1 / 0.8e1 * t5 * t124 * t181 + t5 * t190 * t108 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t194 * t181 - 0.9e1 / 0.8e1 * t5 * t198 * t329 - 0.5e1 / 0.36e2 * t5 * t339 * t108 + t5 * t343 * t181 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t347 * t329 - 0.3e1 / 0.8e1 * t5 * t351 * t549)
  t556 = r1 <= f.p.dens_threshold
  t557 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t558 = 0.1e1 + t557
  t559 = t558 <= f.p.zeta_threshold
  t560 = t558 ** (0.1e1 / 0.3e1)
  t561 = t560 ** 2
  t563 = 0.1e1 / t561 / t558
  t565 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t566 = t565 ** 2
  t570 = 0.1e1 / t561
  t571 = t570 * t565
  t573 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t577 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t581 = f.my_piecewise3(t559, 0, -0.8e1 / 0.27e2 * t563 * t566 * t565 + 0.4e1 / 0.3e1 * t571 * t573 + 0.4e1 / 0.3e1 * t560 * t577)
  t584 = r1 ** 2
  t585 = r1 ** (0.1e1 / 0.3e1)
  t586 = t585 ** 2
  t591 = t64 * t65 * s2 / t586 / t584 / 0.24e2
  t594 = 0.1e1 - 0.1e1 / (0.1e1 + t591)
  t596 = t594 ** 2
  t600 = t596 ** 2
  t604 = jnp.exp(-t591)
  t605 = 0.1e1 - t604
  t607 = t605 ** 2
  t611 = t607 ** 2
  t615 = t105 * t611 * t605 + t82 * t596 * t594 + t88 * t600 * t594 + t99 * t607 * t605 + t102 * t611 + t57 * t594 + t79 * t596 + t85 * t600 + t92 * t605 + t96 * t607 + t56 + t91
  t624 = f.my_piecewise3(t559, 0, 0.4e1 / 0.9e1 * t570 * t566 + 0.4e1 / 0.3e1 * t560 * t573)
  t631 = f.my_piecewise3(t559, 0, 0.4e1 / 0.3e1 * t560 * t565)
  t637 = f.my_piecewise3(t559, t334, t560 * t558)
  t643 = f.my_piecewise3(t556, 0, -0.3e1 / 0.8e1 * t5 * t581 * t54 * t615 - 0.3e1 / 0.8e1 * t5 * t624 * t119 * t615 + t5 * t631 * t189 * t615 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t637 * t338 * t615)
  t645 = t19 ** 2
  t648 = t30 ** 2
  t654 = t41 ** 2
  t663 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t664 = f.my_piecewise5(t10, 0, t14, 0, t663)
  t668 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t645 * t648 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t654 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t664)
  t700 = 0.1e1 / t363 / t212
  t702 = t361 * t362 * t700
  t706 = t376 * t700 * t93
  t710 = t376 * t700 * t236
  t716 = t376 * t700 * t391
  t721 = t202 ** 2
  t722 = t721 * t358
  t723 = t208 ** 2
  t724 = 0.1e1 / t723
  t725 = t722 * t724
  t727 = t211 ** 2
  t728 = t212 * t67
  t731 = 0.1e1 / t69 / t363 / t728
  t732 = t727 * t731
  t735 = t732 * t391 * t58 * t63
  t741 = t732 * t236 * t58 * t63
  t745 = t451 * t721 * t358
  t747 = t724 * t727
  t750 = t747 * t731 * t58 * t63
  t754 = t353 * t721 * t358
  t759 = 0.1e1 / t220 / t199
  t761 = t759 * t721 * t358
  t770 = t732 * t140 * t93
  t792 = t220 ** 2
  t793 = 0.1e1 / t792
  t799 = -0.176e3 / 0.81e2 * t540 * t702 + 0.44e2 / 0.243e3 * t544 * t706 - 0.88e2 / 0.81e2 * t524 * t710 + 0.88e2 / 0.81e2 * t528 * t702 + 0.88e2 / 0.81e2 * t532 * t716 + 0.88e2 / 0.81e2 * t536 * t702 - 0.32e2 / 0.243e3 * t389 * t725 * t735 + 0.56e2 / 0.729e3 * t276 * t725 * t741 + 0.160e3 / 0.243e3 * t251 * t745 * t750 - 0.80e2 / 0.729e3 * t153 * t754 * t750 - 0.64e2 / 0.243e3 * t449 * t761 * t750 + 0.32e2 / 0.81e2 * t321 * t745 * t750 - 0.4e1 / 0.2187e4 * t163 * t725 * t770 - 0.2e1 / 0.729e3 * t169 * t725 * t770 + 0.16e2 / 0.81e2 * t314 * t745 * t750 - 0.16e2 / 0.243e3 * t145 * t754 * t750 - 0.8e1 / 0.2187e4 * t173 * t725 * t770 + 0.28e2 / 0.729e3 * t267 * t725 * t741 - 0.64e2 / 0.729e3 * t149 * t754 * t750 + 0.80e2 / 0.729e3 * t88 * t77 * t793 * t721 * t358 * t750
  t814 = t236 ** 2
  t828 = 0.1e1 / t69 / t728
  t835 = 0.1e1 / t68 / t363 / r0
  t840 = s0 * t828
  t844 = t211 * t835
  t845 = t210 * t844
  t866 = -0.160e3 / 0.243e3 * t462 * t761 * t750 + 0.280e3 / 0.2187e4 * t283 * t725 * t741 - 0.10e2 / 0.2187e4 * t177 * t725 * t770 - 0.32e2 / 0.729e3 * t137 * t754 * t750 + 0.80e2 / 0.729e3 * t105 * t94 * t725 * t732 * t814 * t58 * t63 - 0.80e2 / 0.243e3 * t430 * t725 * t735 - 0.352e3 / 0.27e2 * t456 * t702 + 0.352e3 / 0.81e2 * t459 * t702 + 0.2618e4 / 0.243e3 * t158 * t66 * t828 * t93 - 0.979e3 / 0.729e3 * t228 * t229 * t835 * t93 + 0.2618e4 / 0.243e3 * t128 * t129 * t840 - 0.1958e4 / 0.729e3 * t205 * t845 + 0.880e3 / 0.81e2 * t463 * t702 - 0.1760e4 / 0.81e2 * t356 * t702 + 0.440e3 / 0.81e2 * t371 * t702 + 0.1958e4 / 0.729e3 * t223 * t845 + 0.1958e4 / 0.729e3 * t235 * t229 * t835 * t236 + 0.88e2 / 0.243e3 * t375 * t706 - 0.88e2 / 0.27e2 * t381 * t710 + 0.44e2 / 0.81e2 * t386 * t706
  t889 = t210 * t844 * t93
  t893 = t210 * t844 * t236
  t899 = t358 * t724
  t920 = t227 * t229 * t835
  t925 = 0.352e3 / 0.81e2 * t390 * t716 - 0.176e3 / 0.27e2 * t423 * t710 + 0.176e3 / 0.243e3 * t427 * t706 + 0.880e3 / 0.81e2 * t431 * t716 - 0.880e3 / 0.81e2 * t434 * t710 + 0.220e3 / 0.243e3 * t437 * t706 + 0.176e3 / 0.81e2 * t440 * t702 - 0.176e3 / 0.27e2 * t443 * t702 + 0.88e2 / 0.27e2 * t446 * t702 + 0.352e3 / 0.81e2 * t453 * t702 - 0.979e3 / 0.243e3 * t273 * t889 + 0.3916e4 / 0.243e3 * t277 * t893 - 0.3916e4 / 0.729e3 * t280 * t889 + 0.28e2 / 0.2187e4 * t96 * t721 * t899 * t741 - 0.16e2 / 0.243e3 * t82 * t759 * t722 * t750 - 0.8e1 / 0.243e3 * t99 * t721 * t899 * t735 - 0.16e2 / 0.729e3 * t57 * t353 * t722 * t750 + 0.16e2 / 0.243e3 * t79 * t451 * t722 * t750 + 0.3916e4 / 0.243e3 * t322 * t920 - 0.7832e4 / 0.729e3 * t325 * t920
  t940 = t129 * t840 * t93
  t944 = t140 * t66 * t828
  t983 = -0.1958e4 / 0.729e3 * t262 * t889 - 0.2e1 / 0.2187e4 * t92 * t721 * t899 * t770 + 0.16e2 / 0.729e3 * t102 * t721 * t140 * t747 * t731 * t814 * t358 + 0.13090e5 / 0.243e3 * t178 * t940 + 0.5236e4 / 0.243e3 * t139 * t944 + 0.2618e4 / 0.81e2 * t146 * t944 + 0.19580e5 / 0.729e3 * t253 * t920 - 0.9790e4 / 0.729e3 * t259 * t920 + 0.13090e5 / 0.243e3 * t154 * t944 - 0.1958e4 / 0.243e3 * t318 * t920 - 0.4895e4 / 0.729e3 * t288 * t889 - 0.3916e4 / 0.729e3 * t311 * t920 + 0.1958e4 / 0.243e3 * t315 * t920 + 0.19580e5 / 0.729e3 * t284 * t893 + 0.10472e5 / 0.243e3 * t150 * t944 + 0.5236e4 / 0.243e3 * t164 * t940 + 0.2618e4 / 0.81e2 * t170 * t940 + 0.10472e5 / 0.243e3 * t174 * t940 + 0.16e2 / 0.729e3 * t85 * t793 * t721 * t58 * t63 * t724 * t732 * t358 + 0.1958e4 / 0.243e3 * t268 * t893
  t1002 = 0.1e1 / t118 / t36
  t1007 = -0.3e1 / 0.8e1 * t5 * t668 * t54 * t108 - 0.3e1 / 0.2e1 * t5 * t55 * t181 - 0.3e1 / 0.2e1 * t5 * t120 * t181 - 0.9e1 / 0.4e1 * t5 * t124 * t329 + t5 * t190 * t181 - 0.3e1 / 0.2e1 * t5 * t194 * t329 - 0.3e1 / 0.2e1 * t5 * t198 * t549 - 0.5e1 / 0.9e1 * t5 * t339 * t181 + t5 * t343 * t329 / 0.2e1 - t5 * t347 * t549 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t351 * (t799 + t866 + t925 + t983) - t5 * t53 * t119 * t108 / 0.2e1 + t5 * t117 * t189 * t108 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t187 * t338 * t108 + 0.10e2 / 0.27e2 * t5 * t336 * t1002 * t108
  t1008 = f.my_piecewise3(t1, 0, t1007)
  t1009 = t558 ** 2
  t1012 = t566 ** 2
  t1018 = t573 ** 2
  t1024 = f.my_piecewise5(t14, 0, t10, 0, -t663)
  t1028 = f.my_piecewise3(t559, 0, 0.40e2 / 0.81e2 / t561 / t1009 * t1012 - 0.16e2 / 0.9e1 * t563 * t566 * t573 + 0.4e1 / 0.3e1 * t570 * t1018 + 0.16e2 / 0.9e1 * t571 * t577 + 0.4e1 / 0.3e1 * t560 * t1024)
  t1050 = f.my_piecewise3(t556, 0, -0.3e1 / 0.8e1 * t5 * t1028 * t54 * t615 - t5 * t581 * t119 * t615 / 0.2e1 + t5 * t624 * t189 * t615 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t631 * t338 * t615 + 0.10e2 / 0.27e2 * t5 * t637 * t1002 * t615)
  d1111 = 0.4e1 * t554 + 0.4e1 * t643 + t6 * (t1008 + t1050)

  res = {'v4rho4': d1111}
  return res
