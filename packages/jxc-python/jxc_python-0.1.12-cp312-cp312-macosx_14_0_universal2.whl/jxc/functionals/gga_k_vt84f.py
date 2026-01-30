"""Generated from gga_k_vt84f.mpl."""

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

  vt84f_f0_orig = lambda s: 1 - params_mu * s ** 2 * jnp.exp(-params_alpha * s ** 2) / (1 + params_mu * s ** 2) + (1 - jnp.exp(-params_alpha * s ** 4)) * (s ** (-2) - 1) + 5 * s ** 2 / 3

  vt84f_f0_series = lambda s: 1 + (-params_mu + params_alpha + 5 / 3) * s ** 2 + (params_alpha * params_mu + params_mu ** 2 - params_alpha) * s ** 4 + (-1 / 2 * params_mu * params_alpha ** 2 - (params_alpha * params_mu + params_mu ** 2) * params_mu - 1 / 2 * params_alpha ** 2) * s ** 6 + (1 / 6 * params_mu * params_alpha ** 3 - (-1 / 2 * params_mu * params_alpha ** 2 - params_alpha * params_mu ** 2 - params_mu ** 3) * params_mu + 1 / 2 * params_alpha ** 2) * s ** 8

  vt84f_f0 = lambda s: f.my_piecewise3(s <= jnp.sqrt(DBL_EPSILON), vt84f_f0_series(s), vt84f_f0_orig(jnp.maximum(s, jnp.sqrt(DBL_EPSILON))))

  vt84f_f = lambda x: vt84f_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, vt84f_f, rs, z, xs0, xs1)

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

  vt84f_f0_orig = lambda s: 1 - params_mu * s ** 2 * jnp.exp(-params_alpha * s ** 2) / (1 + params_mu * s ** 2) + (1 - jnp.exp(-params_alpha * s ** 4)) * (s ** (-2) - 1) + 5 * s ** 2 / 3

  vt84f_f0_series = lambda s: 1 + (-params_mu + params_alpha + 5 / 3) * s ** 2 + (params_alpha * params_mu + params_mu ** 2 - params_alpha) * s ** 4 + (-1 / 2 * params_mu * params_alpha ** 2 - (params_alpha * params_mu + params_mu ** 2) * params_mu - 1 / 2 * params_alpha ** 2) * s ** 6 + (1 / 6 * params_mu * params_alpha ** 3 - (-1 / 2 * params_mu * params_alpha ** 2 - params_alpha * params_mu ** 2 - params_mu ** 3) * params_mu + 1 / 2 * params_alpha ** 2) * s ** 8

  vt84f_f0 = lambda s: f.my_piecewise3(s <= jnp.sqrt(DBL_EPSILON), vt84f_f0_series(s), vt84f_f0_orig(jnp.maximum(s, jnp.sqrt(DBL_EPSILON))))

  vt84f_f = lambda x: vt84f_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, vt84f_f, rs, z, xs0, xs1)

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

  vt84f_f0_orig = lambda s: 1 - params_mu * s ** 2 * jnp.exp(-params_alpha * s ** 2) / (1 + params_mu * s ** 2) + (1 - jnp.exp(-params_alpha * s ** 4)) * (s ** (-2) - 1) + 5 * s ** 2 / 3

  vt84f_f0_series = lambda s: 1 + (-params_mu + params_alpha + 5 / 3) * s ** 2 + (params_alpha * params_mu + params_mu ** 2 - params_alpha) * s ** 4 + (-1 / 2 * params_mu * params_alpha ** 2 - (params_alpha * params_mu + params_mu ** 2) * params_mu - 1 / 2 * params_alpha ** 2) * s ** 6 + (1 / 6 * params_mu * params_alpha ** 3 - (-1 / 2 * params_mu * params_alpha ** 2 - params_alpha * params_mu ** 2 - params_mu ** 3) * params_mu + 1 / 2 * params_alpha ** 2) * s ** 8

  vt84f_f0 = lambda s: f.my_piecewise3(s <= jnp.sqrt(DBL_EPSILON), vt84f_f0_series(s), vt84f_f0_orig(jnp.maximum(s, jnp.sqrt(DBL_EPSILON))))

  vt84f_f = lambda x: vt84f_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, vt84f_f, rs, z, xs0, xs1)

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
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t37 = t33 / t35
  t38 = jnp.sqrt(s0)
  t39 = r0 ** (0.1e1 / 0.3e1)
  t41 = 0.1e1 / t39 / r0
  t44 = t37 * t38 * t41 / 0.12e2
  t45 = jnp.sqrt(DBL_EPSILON)
  t46 = t44 <= t45
  t48 = (-params.mu + params.alpha + 0.5e1 / 0.3e1) * t32
  t49 = t35 ** 2
  t50 = 0.1e1 / t49
  t51 = t50 * s0
  t52 = r0 ** 2
  t53 = t39 ** 2
  t55 = 0.1e1 / t53 / t52
  t59 = params.mu * params.alpha
  t60 = params.mu ** 2
  t62 = (t59 + t60 - params.alpha) * t33
  t64 = 0.1e1 / t35 / t34
  t65 = s0 ** 2
  t66 = t64 * t65
  t67 = t52 ** 2
  t70 = 0.1e1 / t39 / t67 / r0
  t74 = params.alpha ** 2
  t76 = params.mu * t74 / 0.2e1
  t79 = t74 / 0.2e1
  t81 = t34 ** 2
  t83 = (-t76 - (t59 + t60) * params.mu - t79) / t81
  t84 = t65 * s0
  t85 = t67 ** 2
  t86 = 0.1e1 / t85
  t98 = (params.mu * t74 * params.alpha / 0.6e1 - (-params.alpha * t60 - t60 * params.mu - t76) * params.mu + t79) * t32
  t100 = 0.1e1 / t49 / t81
  t101 = t65 ** 2
  t102 = t100 * t101
  t105 = 0.1e1 / t53 / t85 / t52
  t110 = t45 < t44
  t111 = f.my_piecewise3(t110, t44, t45)
  t112 = t111 ** 2
  t113 = params.mu * t112
  t115 = jnp.exp(-params.alpha * t112)
  t116 = 0.1e1 + t113
  t118 = t115 / t116
  t120 = t112 ** 2
  t122 = jnp.exp(-params.alpha * t120)
  t123 = 0.1e1 - t122
  t125 = 0.1e1 / t112 - 0.1e1
  t129 = f.my_piecewise3(t46, 0.1e1 + t48 * t51 * t55 / 0.24e2 + t62 * t66 * t70 / 0.576e3 + t83 * t84 * t86 / 0.2304e4 + t98 * t102 * t105 / 0.55296e5, 0.1e1 - t113 * t118 + t123 * t125 + 0.5e1 / 0.3e1 * t112)
  t133 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t129)
  t134 = r1 <= f.p.dens_threshold
  t135 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t136 = 0.1e1 + t135
  t137 = t136 <= f.p.zeta_threshold
  t138 = t136 ** (0.1e1 / 0.3e1)
  t139 = t138 ** 2
  t141 = f.my_piecewise3(t137, t24, t139 * t136)
  t142 = t141 * t30
  t143 = jnp.sqrt(s2)
  t144 = r1 ** (0.1e1 / 0.3e1)
  t146 = 0.1e1 / t144 / r1
  t149 = t37 * t143 * t146 / 0.12e2
  t150 = t149 <= t45
  t151 = t50 * s2
  t152 = r1 ** 2
  t153 = t144 ** 2
  t155 = 0.1e1 / t153 / t152
  t159 = s2 ** 2
  t160 = t64 * t159
  t161 = t152 ** 2
  t164 = 0.1e1 / t144 / t161 / r1
  t168 = t159 * s2
  t169 = t161 ** 2
  t170 = 0.1e1 / t169
  t174 = t159 ** 2
  t175 = t100 * t174
  t178 = 0.1e1 / t153 / t169 / t152
  t183 = t45 < t149
  t184 = f.my_piecewise3(t183, t149, t45)
  t185 = t184 ** 2
  t186 = params.mu * t185
  t188 = jnp.exp(-params.alpha * t185)
  t189 = 0.1e1 + t186
  t191 = t188 / t189
  t193 = t185 ** 2
  t195 = jnp.exp(-params.alpha * t193)
  t196 = 0.1e1 - t195
  t198 = 0.1e1 / t185 - 0.1e1
  t202 = f.my_piecewise3(t150, 0.1e1 + t48 * t151 * t155 / 0.24e2 + t62 * t160 * t164 / 0.576e3 + t83 * t168 * t170 / 0.2304e4 + t98 * t175 * t178 / 0.55296e5, 0.1e1 - t186 * t191 + t196 * t198 + 0.5e1 / 0.3e1 * t185)
  t206 = f.my_piecewise3(t134, 0, 0.3e1 / 0.20e2 * t6 * t142 * t202)
  t207 = t7 ** 2
  t209 = t17 / t207
  t210 = t8 - t209
  t211 = f.my_piecewise5(t11, 0, t15, 0, t210)
  t214 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t211)
  t219 = 0.1e1 / t29
  t223 = t6 * t28 * t219 * t129 / 0.10e2
  t224 = t52 * r0
  t248 = params.mu * t111
  t254 = f.my_piecewise3(t110, -t37 * t38 / t39 / t52 / 0.9e1, 0)
  t255 = t118 * t254
  t258 = t112 * t111
  t260 = params.mu * t258 * params.alpha
  t263 = t60 * t258
  t264 = t116 ** 2
  t266 = t115 / t264
  t270 = params.alpha * t258
  t276 = t123 / t258
  t282 = f.my_piecewise3(t46, -t48 * t51 / t53 / t224 / 0.9e1 - t62 * t66 / t39 / t67 / t52 / 0.108e3 - t83 * t84 / t85 / r0 / 0.288e3 - t98 * t102 / t53 / t85 / t224 / 0.5184e4, -0.2e1 * t248 * t255 + 0.2e1 * t260 * t255 + 0.2e1 * t263 * t266 * t254 + 0.4e1 * t270 * t254 * t122 * t125 - 0.2e1 * t276 * t254 + 0.10e2 / 0.3e1 * t111 * t254)
  t287 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t214 * t30 * t129 + t223 + 0.3e1 / 0.20e2 * t6 * t31 * t282)
  t289 = f.my_piecewise5(t15, 0, t11, 0, -t210)
  t292 = f.my_piecewise3(t137, 0, 0.5e1 / 0.3e1 * t139 * t289)
  t300 = t6 * t141 * t219 * t202 / 0.10e2
  t302 = f.my_piecewise3(t134, 0, 0.3e1 / 0.20e2 * t6 * t292 * t30 * t202 + t300)
  vrho_0_ = t133 + t206 + t7 * (t287 + t302)
  t305 = -t8 - t209
  t306 = f.my_piecewise5(t11, 0, t15, 0, t305)
  t309 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t306)
  t315 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t309 * t30 * t129 + t223)
  t317 = f.my_piecewise5(t15, 0, t11, 0, -t305)
  t320 = f.my_piecewise3(t137, 0, 0.5e1 / 0.3e1 * t139 * t317)
  t325 = t152 * r1
  t349 = params.mu * t184
  t355 = f.my_piecewise3(t183, -t37 * t143 / t144 / t152 / 0.9e1, 0)
  t356 = t191 * t355
  t359 = t185 * t184
  t361 = params.mu * t359 * params.alpha
  t364 = t60 * t359
  t365 = t189 ** 2
  t367 = t188 / t365
  t371 = params.alpha * t359
  t377 = t196 / t359
  t383 = f.my_piecewise3(t150, -t48 * t151 / t153 / t325 / 0.9e1 - t62 * t160 / t144 / t161 / t152 / 0.108e3 - t83 * t168 / t169 / r1 / 0.288e3 - t98 * t175 / t153 / t169 / t325 / 0.5184e4, -0.2e1 * t349 * t356 + 0.2e1 * t361 * t356 + 0.2e1 * t364 * t367 * t355 + 0.4e1 * t371 * t355 * t195 * t198 - 0.2e1 * t377 * t355 + 0.10e2 / 0.3e1 * t184 * t355)
  t388 = f.my_piecewise3(t134, 0, 0.3e1 / 0.20e2 * t6 * t320 * t30 * t202 + t300 + 0.3e1 / 0.20e2 * t6 * t142 * t383)
  vrho_1_ = t133 + t206 + t7 * (t315 + t388)
  t410 = f.my_piecewise3(t110, t37 / t38 * t41 / 0.24e2, 0)
  t411 = t118 * t410
  t428 = f.my_piecewise3(t46, t48 * t50 * t55 / 0.24e2 + t62 * t64 * s0 * t70 / 0.288e3 + t83 * t65 * t86 / 0.768e3 + t98 * t100 * t84 * t105 / 0.13824e5, -0.2e1 * t248 * t411 + 0.2e1 * t260 * t411 + 0.2e1 * t263 * t266 * t410 + 0.4e1 * t270 * t410 * t122 * t125 - 0.2e1 * t276 * t410 + 0.10e2 / 0.3e1 * t111 * t410)
  t432 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t428)
  vsigma_0_ = t7 * t432
  vsigma_1_ = 0.0e0
  t452 = f.my_piecewise3(t183, t37 / t143 * t146 / 0.24e2, 0)
  t453 = t191 * t452
  t470 = f.my_piecewise3(t150, t48 * t50 * t155 / 0.24e2 + t62 * t64 * s2 * t164 / 0.288e3 + t83 * t159 * t170 / 0.768e3 + t98 * t100 * t168 * t178 / 0.13824e5, -0.2e1 * t349 * t453 + 0.2e1 * t361 * t453 + 0.2e1 * t364 * t367 * t452 + 0.4e1 * t371 * t452 * t195 * t198 - 0.2e1 * t377 * t452 + 0.10e2 / 0.3e1 * t184 * t452)
  t474 = f.my_piecewise3(t134, 0, 0.3e1 / 0.20e2 * t6 * t142 * t470)
  vsigma_2_ = t7 * t474
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

  vt84f_f0_orig = lambda s: 1 - params_mu * s ** 2 * jnp.exp(-params_alpha * s ** 2) / (1 + params_mu * s ** 2) + (1 - jnp.exp(-params_alpha * s ** 4)) * (s ** (-2) - 1) + 5 * s ** 2 / 3

  vt84f_f0_series = lambda s: 1 + (-params_mu + params_alpha + 5 / 3) * s ** 2 + (params_alpha * params_mu + params_mu ** 2 - params_alpha) * s ** 4 + (-1 / 2 * params_mu * params_alpha ** 2 - (params_alpha * params_mu + params_mu ** 2) * params_mu - 1 / 2 * params_alpha ** 2) * s ** 6 + (1 / 6 * params_mu * params_alpha ** 3 - (-1 / 2 * params_mu * params_alpha ** 2 - params_alpha * params_mu ** 2 - params_mu ** 3) * params_mu + 1 / 2 * params_alpha ** 2) * s ** 8

  vt84f_f0 = lambda s: f.my_piecewise3(s <= jnp.sqrt(DBL_EPSILON), vt84f_f0_series(s), vt84f_f0_orig(jnp.maximum(s, jnp.sqrt(DBL_EPSILON))))

  vt84f_f = lambda x: vt84f_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, vt84f_f, rs, z, xs0, xs1)

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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t29 = t25 / t27
  t30 = jnp.sqrt(s0)
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t30 * t31
  t34 = 0.1e1 / t21 / r0
  t37 = t29 * t32 * t34 / 0.12e2
  t38 = jnp.sqrt(DBL_EPSILON)
  t39 = t37 <= t38
  t41 = (-params.mu + params.alpha + 0.5e1 / 0.3e1) * t24
  t42 = t27 ** 2
  t43 = 0.1e1 / t42
  t44 = t41 * t43
  t45 = t31 ** 2
  t46 = s0 * t45
  t47 = r0 ** 2
  t49 = 0.1e1 / t22 / t47
  t53 = params.mu * params.alpha
  t54 = params.mu ** 2
  t59 = (t53 + t54 - params.alpha) * t25 / t27 / t26
  t60 = s0 ** 2
  t61 = t60 * t31
  t62 = t47 ** 2
  t65 = 0.1e1 / t21 / t62 / r0
  t69 = params.alpha ** 2
  t71 = params.mu * t69 / 0.2e1
  t74 = t69 / 0.2e1
  t76 = t26 ** 2
  t78 = (-t71 - (t53 + t54) * params.mu - t74) / t76
  t79 = t60 * s0
  t80 = t62 ** 2
  t81 = 0.1e1 / t80
  t96 = (params.mu * t69 * params.alpha / 0.6e1 - (-params.alpha * t54 - t54 * params.mu - t71) * params.mu + t74) * t24 / t42 / t76
  t97 = t60 ** 2
  t98 = t97 * t45
  t101 = 0.1e1 / t22 / t80 / t47
  t106 = t38 < t37
  t107 = f.my_piecewise3(t106, t37, t38)
  t108 = t107 ** 2
  t109 = params.mu * t108
  t111 = jnp.exp(-params.alpha * t108)
  t112 = 0.1e1 + t109
  t114 = t111 / t112
  t116 = t108 ** 2
  t118 = jnp.exp(-params.alpha * t116)
  t119 = 0.1e1 - t118
  t121 = 0.1e1 / t108 - 0.1e1
  t125 = f.my_piecewise3(t39, 0.1e1 + t44 * t46 * t49 / 0.24e2 + t59 * t61 * t65 / 0.288e3 + t78 * t79 * t81 / 0.576e3 + t96 * t98 * t101 / 0.13824e5, 0.1e1 - t109 * t114 + t119 * t121 + 0.5e1 / 0.3e1 * t108)
  t129 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t125)
  t135 = t47 * r0
  t159 = params.mu * t107
  t165 = f.my_piecewise3(t106, -t29 * t32 / t21 / t47 / 0.9e1, 0)
  t166 = t114 * t165
  t169 = t108 * t107
  t171 = params.mu * t169 * params.alpha
  t174 = t54 * t169
  t175 = t112 ** 2
  t177 = t111 / t175
  t181 = params.alpha * t169
  t187 = t119 / t169
  t193 = f.my_piecewise3(t39, -t44 * t46 / t22 / t135 / 0.9e1 - t59 * t61 / t21 / t62 / t47 / 0.54e2 - t78 * t79 / t80 / r0 / 0.72e2 - t96 * t98 / t22 / t80 / t135 / 0.1296e4, -0.2e1 * t159 * t166 + 0.2e1 * t171 * t166 + 0.2e1 * t174 * t177 * t165 + 0.4e1 * t181 * t165 * t118 * t121 - 0.2e1 * t187 * t165 + 0.10e2 / 0.3e1 * t107 * t165)
  t198 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t125 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * t193)
  vrho_0_ = 0.2e1 * r0 * t198 + 0.2e1 * t129
  t222 = f.my_piecewise3(t106, t29 / t30 * t31 * t34 / 0.24e2, 0)
  t223 = t114 * t222
  t240 = f.my_piecewise3(t39, t41 * t43 * t45 * t49 / 0.24e2 + t59 * s0 * t31 * t65 / 0.144e3 + t78 * t60 * t81 / 0.192e3 + t96 * t79 * t45 * t101 / 0.3456e4, -0.2e1 * t159 * t223 + 0.2e1 * t171 * t223 + 0.2e1 * t174 * t177 * t222 + 0.4e1 * t181 * t222 * t118 * t121 - 0.2e1 * t187 * t222 + 0.10e2 / 0.3e1 * t107 * t222)
  t244 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t240)
  vsigma_0_ = 0.2e1 * r0 * t244
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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t29 = t25 / t27
  t30 = jnp.sqrt(s0)
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t30 * t31
  t34 = 0.1e1 / t21 / r0
  t37 = t29 * t32 * t34 / 0.12e2
  t38 = jnp.sqrt(DBL_EPSILON)
  t39 = t37 <= t38
  t41 = (-params.mu + params.alpha + 0.5e1 / 0.3e1) * t24
  t42 = t27 ** 2
  t43 = 0.1e1 / t42
  t44 = t41 * t43
  t45 = t31 ** 2
  t46 = s0 * t45
  t47 = r0 ** 2
  t48 = t21 ** 2
  t50 = 0.1e1 / t48 / t47
  t54 = params.alpha * params.mu
  t55 = params.mu ** 2
  t57 = (t54 + t55 - params.alpha) * t25
  t59 = 0.1e1 / t27 / t26
  t60 = t57 * t59
  t61 = s0 ** 2
  t62 = t61 * t31
  t63 = t47 ** 2
  t66 = 0.1e1 / t21 / t63 / r0
  t70 = params.alpha ** 2
  t72 = params.mu * t70 / 0.2e1
  t75 = t70 / 0.2e1
  t77 = t26 ** 2
  t79 = (-t72 - (t54 + t55) * params.mu - t75) / t77
  t80 = t61 * s0
  t81 = t63 ** 2
  t82 = 0.1e1 / t81
  t90 = t55 * params.mu
  t97 = (params.mu * t70 * params.alpha / 0.6e1 - (-params.alpha * t55 - t72 - t90) * params.mu + t75) * t24 / t42 / t77
  t98 = t61 ** 2
  t99 = t98 * t45
  t100 = t81 * t47
  t102 = 0.1e1 / t48 / t100
  t107 = t38 < t37
  t108 = f.my_piecewise3(t107, t37, t38)
  t109 = t108 ** 2
  t110 = params.mu * t109
  t111 = params.alpha * t109
  t112 = jnp.exp(-t111)
  t113 = 0.1e1 + t110
  t114 = 0.1e1 / t113
  t115 = t112 * t114
  t117 = t109 ** 2
  t119 = jnp.exp(-params.alpha * t117)
  t120 = 0.1e1 - t119
  t122 = 0.1e1 / t109 - 0.1e1
  t126 = f.my_piecewise3(t39, 0.1e1 + t44 * t46 * t50 / 0.24e2 + t60 * t62 * t66 / 0.288e3 + t79 * t80 * t82 / 0.576e3 + t97 * t99 * t102 / 0.13824e5, 0.1e1 - t110 * t115 + t120 * t122 + 0.5e1 / 0.3e1 * t109)
  t130 = t20 * t48
  t131 = t47 * r0
  t133 = 0.1e1 / t48 / t131
  t139 = 0.1e1 / t21 / t63 / t47
  t144 = 0.1e1 / t81 / r0
  t150 = 0.1e1 / t48 / t81 / t131
  t155 = params.mu * t108
  t157 = 0.1e1 / t21 / t47
  t161 = f.my_piecewise3(t107, -t29 * t32 * t157 / 0.9e1, 0)
  t162 = t115 * t161
  t165 = t109 * t108
  t167 = params.mu * t165 * params.alpha
  t170 = t55 * t165
  t171 = t113 ** 2
  t172 = 0.1e1 / t171
  t173 = t112 * t172
  t177 = params.alpha * t165
  t178 = t161 * t119
  t179 = t178 * t122
  t183 = t120 / t165
  t189 = f.my_piecewise3(t39, -t44 * t46 * t133 / 0.9e1 - t60 * t62 * t139 / 0.54e2 - t79 * t80 * t144 / 0.72e2 - t97 * t99 * t150 / 0.1296e4, -0.2e1 * t155 * t162 + 0.2e1 * t167 * t162 + 0.2e1 * t170 * t173 * t161 + 0.4e1 * t177 * t179 - 0.2e1 * t183 * t161 + 0.10e2 / 0.3e1 * t108 * t161)
  t194 = f.my_piecewise3(t2, 0, t7 * t23 * t126 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t130 * t189)
  t225 = t161 ** 2
  t229 = t110 * params.alpha
  t231 = t225 * t112 * t114
  t234 = t55 * t109
  t235 = t173 * t225
  t243 = f.my_piecewise3(t107, 0.7e1 / 0.27e2 * t29 * t32 / t21 / t131, 0)
  t244 = t115 * t243
  t250 = params.mu * t117 * t70
  t254 = t55 * t117 * params.alpha
  t257 = t90 * t117
  t259 = 0.1e1 / t171 / t113
  t260 = t112 * t259
  t268 = t225 * t119 * t122
  t276 = t70 * t117 * t109
  t283 = t120 / t117
  t291 = -0.2e1 * params.mu * t225 * t115 + 0.10e2 * t229 * t231 + 0.10e2 * t234 * t235 - 0.2e1 * t155 * t244 + 0.2e1 * t167 * t244 - 0.4e1 * t250 * t231 - 0.8e1 * t254 * t235 - 0.8e1 * t257 * t260 * t225 + 0.2e1 * t170 * t173 * t243 + 0.12e2 * t111 * t268 + 0.4e1 * t177 * t243 * t119 * t122 - 0.16e2 * t276 * t268 - 0.16e2 * params.alpha * t225 * t119 + 0.6e1 * t283 * t225 - 0.2e1 * t183 * t243 + 0.10e2 / 0.3e1 * t225 + 0.10e2 / 0.3e1 * t108 * t243
  t292 = f.my_piecewise3(t39, 0.11e2 / 0.27e2 * t44 * t46 / t48 / t63 + 0.19e2 / 0.162e3 * t60 * t62 / t21 / t63 / t131 + t79 * t80 / t100 / 0.8e1 + 0.35e2 / 0.3888e4 * t97 * t99 / t48 / t81 / t63, t291)
  t297 = f.my_piecewise3(t2, 0, -t7 * t20 * t34 * t126 / 0.30e2 + t7 * t23 * t189 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t130 * t292)
  v2rho2_0_ = 0.2e1 * r0 * t297 + 0.4e1 * t194
  t300 = t43 * t45
  t304 = s0 * t31
  t311 = t80 * t45
  t317 = 0.1e1 / t30 * t31
  t321 = f.my_piecewise3(t107, t29 * t317 * t34 / 0.24e2, 0)
  t322 = t115 * t321
  t339 = f.my_piecewise3(t39, t41 * t300 * t50 / 0.24e2 + t60 * t304 * t66 / 0.144e3 + t79 * t61 * t82 / 0.192e3 + t97 * t311 * t102 / 0.3456e4, -0.2e1 * t155 * t322 + 0.2e1 * t167 * t322 + 0.2e1 * t170 * t173 * t321 + 0.4e1 * t177 * t321 * t119 * t122 - 0.2e1 * t183 * t321 + 0.10e2 / 0.3e1 * t108 * t321)
  t343 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t130 * t339)
  t365 = t161 * t112 * t114 * t321
  t376 = f.my_piecewise3(t107, -t29 * t317 * t157 / 0.18e2, 0)
  t377 = t115 * t376
  t410 = t161 * t321
  t418 = -0.2e1 * params.mu * t161 * t322 + 0.10e2 * t229 * t365 + 0.10e2 * t234 * t112 * t172 * t321 * t161 - 0.2e1 * t155 * t377 + 0.2e1 * t167 * t377 - 0.4e1 * t250 * t365 - 0.8e1 * t254 * t321 * t112 * t172 * t161 - 0.8e1 * t257 * t112 * t259 * t321 * t161 + 0.2e1 * t170 * t173 * t376 + 0.12e2 * t111 * t321 * t179 + 0.4e1 * t177 * t376 * t119 * t122 - 0.16e2 * t276 * t321 * t179 - 0.16e2 * params.alpha * t321 * t178 + 0.6e1 * t283 * t410 - 0.2e1 * t183 * t376 + 0.10e2 / 0.3e1 * t410 + 0.10e2 / 0.3e1 * t108 * t376
  t419 = f.my_piecewise3(t39, -t41 * t300 * t133 / 0.9e1 - t60 * t304 * t139 / 0.27e2 - t79 * t61 * t144 / 0.24e2 - t97 * t311 * t150 / 0.324e3, t418)
  t424 = f.my_piecewise3(t2, 0, t7 * t23 * t339 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t130 * t419)
  v2rhosigma_0_ = 0.2e1 * r0 * t424 + 0.2e1 * t343
  t439 = t321 ** 2
  t444 = t439 * t112 * t114
  t447 = t173 * t439
  t456 = f.my_piecewise3(t107, -t29 / t30 / s0 * t31 * t34 / 0.48e2, 0)
  t457 = t115 * t456
  t473 = t439 * t119 * t122
  t492 = -0.2e1 * params.mu * t439 * t115 + 0.10e2 * t229 * t444 + 0.10e2 * t234 * t447 - 0.2e1 * t155 * t457 + 0.2e1 * t167 * t457 - 0.4e1 * t250 * t444 - 0.8e1 * t254 * t447 - 0.8e1 * t257 * t260 * t439 + 0.2e1 * t170 * t173 * t456 + 0.12e2 * t111 * t473 + 0.4e1 * t177 * t456 * t119 * t122 - 0.16e2 * t276 * t473 - 0.16e2 * params.alpha * t439 * t119 + 0.6e1 * t283 * t439 - 0.2e1 * t183 * t456 + 0.10e2 / 0.3e1 * t439 + 0.10e2 / 0.3e1 * t108 * t456
  t493 = f.my_piecewise3(t39, t57 * t59 * t31 * t66 / 0.144e3 + t79 * s0 * t82 / 0.96e2 + t97 * t61 * t45 * t102 / 0.1152e4, t492)
  t497 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t130 * t493)
  v2sigma2_0_ = 0.2e1 * r0 * t497
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
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t30 = t26 / t28
  t31 = jnp.sqrt(s0)
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t31 * t32
  t36 = t30 * t33 * t23 / 0.12e2
  t37 = jnp.sqrt(DBL_EPSILON)
  t38 = t36 <= t37
  t41 = t28 ** 2
  t43 = (-params.mu + params.alpha + 0.5e1 / 0.3e1) * t25 / t41
  t44 = t32 ** 2
  t45 = s0 * t44
  t46 = r0 ** 2
  t47 = t21 ** 2
  t53 = params.alpha * params.mu
  t54 = params.mu ** 2
  t59 = (t53 + t54 - params.alpha) * t26 / t28 / t27
  t60 = s0 ** 2
  t61 = t60 * t32
  t62 = t46 ** 2
  t63 = t62 * r0
  t69 = params.alpha ** 2
  t71 = params.mu * t69 / 0.2e1
  t74 = t69 / 0.2e1
  t76 = t27 ** 2
  t78 = (-t71 - (t53 + t54) * params.mu - t74) / t76
  t79 = t60 * s0
  t80 = t62 ** 2
  t85 = t69 * params.alpha
  t89 = t54 * params.mu
  t96 = (params.mu * t85 / 0.6e1 - (-params.alpha * t54 - t71 - t89) * params.mu + t74) * t25 / t41 / t76
  t97 = t60 ** 2
  t98 = t97 * t44
  t99 = t80 * t46
  t106 = t37 < t36
  t107 = f.my_piecewise3(t106, t36, t37)
  t108 = t107 ** 2
  t109 = params.mu * t108
  t110 = params.alpha * t108
  t111 = jnp.exp(-t110)
  t112 = 0.1e1 + t109
  t113 = 0.1e1 / t112
  t114 = t111 * t113
  t116 = t108 ** 2
  t118 = jnp.exp(-params.alpha * t116)
  t119 = 0.1e1 - t118
  t121 = 0.1e1 / t108 - 0.1e1
  t125 = f.my_piecewise3(t38, 0.1e1 + t43 * t45 / t47 / t46 / 0.24e2 + t59 * t61 / t21 / t63 / 0.288e3 + t78 * t79 / t80 / 0.576e3 + t96 * t98 / t47 / t99 / 0.13824e5, 0.1e1 - t109 * t114 + t119 * t121 + 0.5e1 / 0.3e1 * t108)
  t130 = t20 / t21
  t131 = t46 * r0
  t148 = t80 * t131
  t155 = params.mu * t107
  t157 = 0.1e1 / t21 / t46
  t161 = f.my_piecewise3(t106, -t30 * t33 * t157 / 0.9e1, 0)
  t162 = t114 * t161
  t165 = t108 * t107
  t166 = params.mu * t165
  t167 = t166 * params.alpha
  t170 = t54 * t165
  t171 = t112 ** 2
  t172 = 0.1e1 / t171
  t173 = t111 * t172
  t177 = params.alpha * t165
  t178 = t161 * t118
  t179 = t178 * t121
  t183 = t119 / t165
  t189 = f.my_piecewise3(t38, -t43 * t45 / t47 / t131 / 0.9e1 - t59 * t61 / t21 / t62 / t46 / 0.54e2 - t78 * t79 / t80 / r0 / 0.72e2 - t96 * t98 / t47 / t148 / 0.1296e4, -0.2e1 * t155 * t162 + 0.2e1 * t167 * t162 + 0.2e1 * t170 * t173 * t161 + 0.4e1 * t177 * t179 - 0.2e1 * t183 * t161 + 0.10e2 / 0.3e1 * t107 * t161)
  t193 = t20 * t47
  t216 = t161 ** 2
  t220 = t109 * params.alpha
  t222 = t216 * t111 * t113
  t225 = t54 * t108
  t226 = t173 * t216
  t234 = f.my_piecewise3(t106, 0.7e1 / 0.27e2 * t30 * t33 / t21 / t131, 0)
  t235 = t114 * t234
  t241 = params.mu * t116 * t69
  t245 = t54 * t116 * params.alpha
  t248 = t89 * t116
  t250 = 0.1e1 / t171 / t112
  t251 = t111 * t250
  t259 = t216 * t118 * t121
  t263 = t234 * t118 * t121
  t267 = t69 * t116 * t108
  t274 = t119 / t116
  t282 = -0.2e1 * params.mu * t216 * t114 + 0.10e2 * t220 * t222 + 0.10e2 * t225 * t226 - 0.2e1 * t155 * t235 + 0.2e1 * t167 * t235 - 0.4e1 * t241 * t222 - 0.8e1 * t245 * t226 - 0.8e1 * t248 * t251 * t216 + 0.2e1 * t170 * t173 * t234 + 0.12e2 * t110 * t259 + 0.4e1 * t177 * t263 - 0.16e2 * t267 * t259 - 0.16e2 * params.alpha * t216 * t118 + 0.6e1 * t274 * t216 - 0.2e1 * t183 * t234 + 0.10e2 / 0.3e1 * t216 + 0.10e2 / 0.3e1 * t107 * t234
  t283 = f.my_piecewise3(t38, 0.11e2 / 0.27e2 * t43 * t45 / t47 / t62 + 0.19e2 / 0.162e3 * t59 * t61 / t21 / t62 / t131 + t78 * t79 / t99 / 0.8e1 + 0.35e2 / 0.3888e4 * t96 * t98 / t47 / t80 / t62, t282)
  t288 = f.my_piecewise3(t2, 0, -t7 * t24 * t125 / 0.30e2 + t7 * t130 * t189 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t193 * t283)
  t321 = t116 ** 2
  t324 = t216 * t161
  t325 = t324 * t118
  t326 = t325 * t121
  t337 = t251 * t324
  t345 = f.my_piecewise3(t106, -0.70e2 / 0.81e2 * t30 * t33 / t21 / t62, 0)
  t346 = t114 * t345
  t349 = t54 ** 2
  t350 = t116 * t107
  t352 = t171 ** 2
  t377 = t161 * t234
  t383 = 0.64e2 * t85 * t321 * t107 * t326 - 0.6e1 * params.mu * t161 * t235 + 0.24e2 * t54 * t324 * t173 * t107 - 0.72e2 * t89 * t165 * t337 - 0.2e1 * t155 * t346 + 0.48e2 * t349 * t350 * t111 / t352 * t324 + 0.2e1 * t170 * t173 * t345 - 0.144e3 * t69 * t350 * t326 + 0.4e1 * t177 * t345 * t118 * t121 + 0.24e2 * params.alpha * t107 * t326 - 0.24e2 * t119 / t350 * t324 - 0.2e1 * t183 * t345 + 0.10e2 * t377 + 0.10e2 / 0.3e1 * t107 * t345 + 0.18e2 * t274 * t377
  t400 = t324 * t111
  t401 = t400 * t113
  t405 = t400 * t172
  t409 = t172 * t161
  t437 = t161 * t111 * t113 * t234
  t446 = -0.48e2 * params.alpha * t234 * t178 + 0.96e2 * t69 * t165 * t325 - 0.48e2 * t267 * t234 * t179 + 0.24e2 * params.mu * t324 * params.alpha * t107 * t111 * t113 - 0.36e2 * t166 * t69 * t401 - 0.72e2 * t170 * params.alpha * t405 + 0.30e2 * t225 * t111 * t409 * t234 + 0.2e1 * t167 * t346 + 0.8e1 * params.mu * t350 * t85 * t401 + 0.24e2 * t54 * t350 * t69 * t405 + 0.48e2 * t89 * t350 * params.alpha * t337 - 0.24e2 * t248 * t111 * t250 * t161 * t234 + 0.36e2 * t110 * t161 * t263 + 0.30e2 * t220 * t437 - 0.12e2 * t241 * t437 - 0.24e2 * t245 * t234 * t111 * t409
  t448 = f.my_piecewise3(t38, -0.154e3 / 0.81e2 * t43 * t45 / t47 / t63 - 0.209e3 / 0.243e3 * t59 * t61 / t21 / t80 - 0.5e1 / 0.4e1 * t78 * t79 / t148 - 0.665e3 / 0.5832e4 * t96 * t98 / t47 / t80 / t63, t383 + t446)
  t453 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t157 * t125 - t7 * t24 * t189 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t130 * t283 + 0.3e1 / 0.20e2 * t7 * t193 * t448)
  v3rho3_0_ = 0.2e1 * r0 * t453 + 0.6e1 * t288

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
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t31 = t27 / t29
  t32 = jnp.sqrt(s0)
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t32 * t33
  t36 = 0.1e1 / t22 / r0
  t39 = t31 * t34 * t36 / 0.12e2
  t40 = jnp.sqrt(DBL_EPSILON)
  t41 = t39 <= t40
  t44 = t29 ** 2
  t46 = (-params.mu + params.alpha + 0.5e1 / 0.3e1) * t26 / t44
  t47 = t33 ** 2
  t48 = s0 * t47
  t49 = t22 ** 2
  t55 = params.alpha * params.mu
  t56 = params.mu ** 2
  t61 = (t55 + t56 - params.alpha) * t27 / t29 / t28
  t62 = s0 ** 2
  t63 = t62 * t33
  t64 = t21 ** 2
  t65 = t64 * r0
  t67 = 0.1e1 / t22 / t65
  t71 = params.alpha ** 2
  t73 = params.mu * t71 / 0.2e1
  t76 = t71 / 0.2e1
  t78 = t28 ** 2
  t80 = (-t73 - (t55 + t56) * params.mu - t76) / t78
  t81 = t62 * s0
  t82 = t64 ** 2
  t87 = t71 * params.alpha
  t91 = t56 * params.mu
  t98 = (params.mu * t87 / 0.6e1 - (-params.alpha * t56 - t73 - t91) * params.mu + t76) * t26 / t44 / t78
  t99 = t62 ** 2
  t100 = t99 * t47
  t101 = t82 * t21
  t108 = t40 < t39
  t109 = f.my_piecewise3(t108, t39, t40)
  t110 = t109 ** 2
  t111 = params.mu * t110
  t112 = params.alpha * t110
  t113 = jnp.exp(-t112)
  t114 = 0.1e1 + t111
  t115 = 0.1e1 / t114
  t116 = t113 * t115
  t118 = t110 ** 2
  t120 = jnp.exp(-params.alpha * t118)
  t121 = 0.1e1 - t120
  t122 = 0.1e1 / t110
  t123 = t122 - 0.1e1
  t127 = f.my_piecewise3(t41, 0.1e1 + t46 * t48 / t49 / t21 / 0.24e2 + t61 * t63 * t67 / 0.288e3 + t80 * t81 / t82 / 0.576e3 + t98 * t100 / t49 / t101 / 0.13824e5, 0.1e1 - t111 * t116 + t121 * t123 + 0.5e1 / 0.3e1 * t110)
  t131 = t20 * t36
  t132 = t21 * r0
  t138 = t64 * t21
  t144 = t82 * r0
  t149 = t82 * t132
  t156 = params.mu * t109
  t160 = f.my_piecewise3(t108, -t31 * t34 * t24 / 0.9e1, 0)
  t161 = t116 * t160
  t164 = t110 * t109
  t165 = params.mu * t164
  t166 = t165 * params.alpha
  t169 = t56 * t164
  t170 = t114 ** 2
  t171 = 0.1e1 / t170
  t172 = t113 * t171
  t176 = params.alpha * t164
  t177 = t160 * t120
  t178 = t177 * t123
  t182 = t121 / t164
  t188 = f.my_piecewise3(t41, -t46 * t48 / t49 / t132 / 0.9e1 - t61 * t63 / t22 / t138 / 0.54e2 - t80 * t81 / t144 / 0.72e2 - t98 * t100 / t49 / t149 / 0.1296e4, -0.2e1 * t156 * t161 + 0.2e1 * t166 * t161 + 0.2e1 * t169 * t172 * t160 + 0.4e1 * t176 * t178 - 0.2e1 * t182 * t160 + 0.10e2 / 0.3e1 * t109 * t160)
  t193 = t20 / t22
  t209 = t82 * t64
  t216 = t160 ** 2
  t217 = params.mu * t216
  t220 = t111 * params.alpha
  t221 = t216 * t113
  t222 = t221 * t115
  t225 = t56 * t110
  t226 = t172 * t216
  t230 = 0.1e1 / t22 / t132
  t234 = f.my_piecewise3(t108, 0.7e1 / 0.27e2 * t31 * t34 * t230, 0)
  t235 = t116 * t234
  t240 = params.mu * t118
  t241 = t240 * t71
  t244 = t56 * t118
  t245 = t244 * params.alpha
  t248 = t91 * t118
  t250 = 0.1e1 / t170 / t114
  t251 = t113 * t250
  t259 = t216 * t120 * t123
  t263 = t234 * t120 * t123
  t266 = t118 * t110
  t267 = t71 * t266
  t274 = t121 / t118
  t282 = -0.2e1 * t217 * t116 + 0.10e2 * t220 * t222 + 0.10e2 * t225 * t226 - 0.2e1 * t156 * t235 + 0.2e1 * t166 * t235 - 0.4e1 * t241 * t222 - 0.8e1 * t245 * t226 - 0.8e1 * t248 * t251 * t216 + 0.2e1 * t169 * t172 * t234 + 0.12e2 * t112 * t259 + 0.4e1 * t176 * t263 - 0.16e2 * t267 * t259 - 0.16e2 * params.alpha * t216 * t120 + 0.6e1 * t274 * t216 - 0.2e1 * t182 * t234 + 0.10e2 / 0.3e1 * t216 + 0.10e2 / 0.3e1 * t109 * t234
  t283 = f.my_piecewise3(t41, 0.11e2 / 0.27e2 * t46 * t48 / t49 / t64 + 0.19e2 / 0.162e3 * t61 * t63 / t22 / t64 / t132 + t80 * t81 / t101 / 0.8e1 + 0.35e2 / 0.3888e4 * t98 * t100 / t49 / t209, t282)
  t287 = t20 * t49
  t309 = t165 * t71
  t310 = t216 * t160
  t311 = t310 * t113
  t312 = t311 * t115
  t315 = t169 * params.alpha
  t316 = t311 * t171
  t319 = t225 * t113
  t320 = t171 * t160
  t329 = f.my_piecewise3(t108, -0.70e2 / 0.81e2 * t31 * t34 / t22 / t64, 0)
  t331 = t329 * t113 * t115
  t334 = t118 * t109
  t336 = params.mu * t334 * t87
  t340 = t56 * t334 * t71
  t344 = t91 * t334 * params.alpha
  t345 = t311 * t250
  t348 = t248 * t113
  t361 = t109 * t113
  t365 = t160 * t234
  t372 = t310 * t120
  t375 = params.mu * t160
  t378 = -0.36e2 * t309 * t312 - 0.72e2 * t315 * t316 + 0.30e2 * t319 * t320 * t234 + 0.2e1 * t166 * t331 + 0.8e1 * t336 * t312 + 0.24e2 * t340 * t316 + 0.48e2 * t344 * t345 - 0.24e2 * t348 * t250 * t160 * t234 + 0.36e2 * t112 * t160 * t263 - 0.48e2 * t267 * t234 * t178 + 0.24e2 * params.mu * t310 * params.alpha * t361 * t115 + 0.18e2 * t274 * t365 - 0.48e2 * params.alpha * t234 * t177 + 0.96e2 * t71 * t164 * t372 - 0.6e1 * t375 * t235
  t383 = t91 * t164
  t388 = t56 ** 2
  t389 = t388 * t334
  t390 = t170 ** 2
  t391 = 0.1e1 / t390
  t399 = t71 * t334
  t400 = t372 * t123
  t403 = t329 * t120
  t407 = t118 ** 2
  t409 = t87 * t407 * t109
  t412 = params.alpha * t109
  t415 = t160 * t113
  t416 = t115 * t234
  t417 = t415 * t416
  t430 = t121 / t334
  t435 = 0.24e2 * t56 * t310 * t172 * t109 - 0.72e2 * t383 * t345 - 0.2e1 * t156 * t331 + 0.48e2 * t389 * t113 * t391 * t310 + 0.2e1 * t169 * t172 * t329 - 0.144e3 * t399 * t400 + 0.4e1 * t176 * t403 * t123 + 0.64e2 * t409 * t400 + 0.24e2 * t412 * t400 + 0.30e2 * t220 * t417 - 0.12e2 * t241 * t417 - 0.24e2 * t245 * t234 * t113 * t320 + 0.10e2 * t365 + 0.10e2 / 0.3e1 * t109 * t329 - 0.24e2 * t430 * t310 - 0.2e1 * t182 * t329
  t437 = f.my_piecewise3(t41, -0.154e3 / 0.81e2 * t46 * t48 / t49 / t65 - 0.209e3 / 0.243e3 * t61 * t63 / t22 / t82 - 0.5e1 / 0.4e1 * t80 * t81 / t149 - 0.665e3 / 0.5832e4 * t98 * t100 / t49 / t82 / t65, t378 + t435)
  t442 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t127 - t7 * t131 * t188 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t193 * t283 + 0.3e1 / 0.20e2 * t7 * t287 * t437)
  t497 = t216 ** 2
  t498 = t497 * t113
  t499 = t498 * t391
  t507 = t498 * t250
  t516 = t56 * t497
  t518 = t110 * t113
  t530 = t171 * t329
  t534 = t234 ** 2
  t535 = t534 * t113
  t536 = t535 * t115
  t541 = t535 * t171
  t544 = -0.864e3 * t399 * t216 * t263 + 0.48e2 * t112 * t329 * t178 - 0.64e2 * t267 * t329 * t178 + 0.384e3 * t409 * t216 * t263 + 0.288e3 * t389 * t113 * t391 * t216 * t234 - 0.384e3 * t388 * t266 * params.alpha * t499 + 0.144e3 * t412 * t216 * t263 - 0.192e3 * t91 * t266 * t71 * t507 + 0.144e3 * t56 * t216 * t113 * t171 * t109 * t234 - 0.312e3 * t516 * params.alpha * t518 * t171 - 0.432e3 * t383 * t113 * t250 * t216 * t234 + 0.672e3 * t248 * params.alpha * t507 + 0.40e2 * t319 * t530 * t160 + 0.30e2 * t220 * t536 - 0.12e2 * t241 * t536 - 0.24e2 * t245 * t541
  t546 = t498 * t115
  t550 = t498 * t171
  t553 = params.mu * t497
  t561 = f.my_piecewise3(t108, 0.910e3 / 0.243e3 * t31 * t34 * t67, 0)
  t563 = t561 * t113 * t115
  t567 = t71 ** 2
  t587 = t497 * t120
  t598 = t160 * t329
  t607 = 0.112e3 * t240 * t87 * t546 + 0.336e3 * t244 * t71 * t550 - 0.156e3 * t553 * t71 * t518 * t115 + 0.2e1 * t166 * t563 - 0.16e2 * params.mu * t266 * t567 * t546 - 0.64e2 * t56 * t266 * t87 * t550 - 0.32e2 * t348 * t250 * t329 * t160 - 0.6e1 * params.mu * t534 * t116 + 0.24e2 * params.alpha * t497 * t120 * t123 + 0.576e3 * t71 * t110 * t587 + 0.24e2 * t516 * t172 - 0.144e3 * t430 * t216 * t234 - 0.144e3 * params.alpha * t122 * t587 + 0.24e2 * t274 * t598 - 0.64e2 * params.alpha * t160 * t403 - 0.512e3 * t87 * t266 * t587
  t617 = t587 * t123
  t623 = t534 * t120 * t123
  t666 = -0.24e2 * t248 * t251 * t534 + 0.24e2 * t553 * params.alpha * t113 * t115 - 0.816e3 * t71 * t118 * t617 + 0.30e2 * t225 * t541 - 0.48e2 * t267 * t623 - 0.312e3 * t91 * t497 * t251 * t110 + 0.672e3 * t388 * t118 * t499 + 0.36e2 * t112 * t623 - 0.384e3 * t388 * params.mu * t266 * t113 / t390 / t114 * t497 + 0.576e3 * t71 * t234 * t164 * t216 * t120 - 0.2e1 * t156 * t563 + 0.2e1 * t169 * t172 * t561 + 0.1152e4 * t87 * t407 * t617 + 0.4e1 * t176 * t561 * t120 * t123 - 0.256e3 * t567 * t407 * t118 * t617 - 0.8e1 * t375 * t331
  t669 = t221 * t171 * t234
  t672 = t598 * t116
  t675 = t221 * t416
  t709 = 0.10e2 * t534 - 0.432e3 * t315 * t669 - 0.16e2 * t241 * t672 + 0.48e2 * t336 * t675 + 0.144e3 * t340 * t669 - 0.216e3 * t309 * t675 + 0.40e2 * t220 * t672 - 0.32e2 * t245 * t415 * t530 + 0.144e3 * t217 * params.alpha * t361 * t416 + 0.288e3 * t344 * t221 * t250 * t234 + 0.40e2 / 0.3e1 * t598 + 0.10e2 / 0.3e1 * t109 * t561 - 0.2e1 * t182 * t561 + 0.120e3 * t121 / t266 * t497 + 0.18e2 * t274 * t534 - 0.48e2 * params.alpha * t534 * t120
  t712 = f.my_piecewise3(t41, 0.2618e4 / 0.243e3 * t46 * t48 / t49 / t138 + 0.5225e4 / 0.729e3 * t61 * t63 / t22 / t144 + 0.55e2 / 0.4e1 * t80 * t81 / t209 + 0.27265e5 / 0.17496e5 * t98 * t100 / t49 / t82 / t138, t544 + t607 + t666 + t709)
  t717 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t230 * t127 + 0.8e1 / 0.45e2 * t7 * t25 * t188 - t7 * t131 * t283 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t193 * t437 + 0.3e1 / 0.20e2 * t7 * t287 * t712)
  v4rho4_0_ = 0.2e1 * r0 * t717 + 0.8e1 * t442

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
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t40 = t36 / t38
  t41 = jnp.sqrt(s0)
  t42 = r0 ** (0.1e1 / 0.3e1)
  t47 = t40 * t41 / t42 / r0 / 0.12e2
  t48 = jnp.sqrt(DBL_EPSILON)
  t49 = t47 <= t48
  t51 = (-params.mu + params.alpha + 0.5e1 / 0.3e1) * t35
  t52 = t38 ** 2
  t53 = 0.1e1 / t52
  t54 = t53 * s0
  t55 = r0 ** 2
  t56 = t42 ** 2
  t62 = params.mu * params.alpha
  t63 = params.mu ** 2
  t65 = (t62 + t63 - params.alpha) * t36
  t67 = 0.1e1 / t38 / t37
  t68 = s0 ** 2
  t69 = t67 * t68
  t70 = t55 ** 2
  t77 = params.alpha ** 2
  t79 = params.mu * t77 / 0.2e1
  t82 = t77 / 0.2e1
  t84 = t37 ** 2
  t86 = (-t79 - (t62 + t63) * params.mu - t82) / t84
  t87 = t68 * s0
  t88 = t70 ** 2
  t97 = t63 * params.mu
  t101 = (params.mu * t77 * params.alpha / 0.6e1 - (-params.alpha * t63 - t79 - t97) * params.mu + t82) * t35
  t103 = 0.1e1 / t52 / t84
  t104 = t68 ** 2
  t105 = t103 * t104
  t106 = t88 * t55
  t113 = t48 < t47
  t114 = f.my_piecewise3(t113, t47, t48)
  t115 = t114 ** 2
  t116 = params.mu * t115
  t117 = params.alpha * t115
  t118 = jnp.exp(-t117)
  t119 = 0.1e1 + t116
  t120 = 0.1e1 / t119
  t121 = t118 * t120
  t123 = t115 ** 2
  t125 = jnp.exp(-params.alpha * t123)
  t126 = 0.1e1 - t125
  t128 = 0.1e1 / t115 - 0.1e1
  t132 = f.my_piecewise3(t49, 0.1e1 + t51 * t54 / t56 / t55 / 0.24e2 + t65 * t69 / t42 / t70 / r0 / 0.576e3 + t86 * t87 / t88 / 0.2304e4 + t101 * t105 / t56 / t106 / 0.55296e5, 0.1e1 - t116 * t121 + t126 * t128 + 0.5e1 / 0.3e1 * t115)
  t136 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t137 = t136 ** 2
  t138 = t137 * f.p.zeta_threshold
  t140 = f.my_piecewise3(t21, t138, t23 * t20)
  t141 = 0.1e1 / t32
  t142 = t140 * t141
  t145 = t6 * t142 * t132 / 0.10e2
  t146 = t140 * t33
  t147 = t55 * r0
  t171 = params.mu * t114
  t177 = f.my_piecewise3(t113, -t40 * t41 / t42 / t55 / 0.9e1, 0)
  t178 = t121 * t177
  t181 = t115 * t114
  t183 = params.mu * t181 * params.alpha
  t186 = t63 * t181
  t187 = t119 ** 2
  t189 = t118 / t187
  t193 = params.alpha * t181
  t199 = t126 / t181
  t205 = f.my_piecewise3(t49, -t51 * t54 / t56 / t147 / 0.9e1 - t65 * t69 / t42 / t70 / t55 / 0.108e3 - t86 * t87 / t88 / r0 / 0.288e3 - t101 * t105 / t56 / t88 / t147 / 0.5184e4, -0.2e1 * t171 * t178 + 0.2e1 * t183 * t178 + 0.2e1 * t186 * t189 * t177 + 0.4e1 * t193 * t177 * t125 * t128 - 0.2e1 * t199 * t177 + 0.10e2 / 0.3e1 * t114 * t177)
  t210 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t132 + t145 + 0.3e1 / 0.20e2 * t6 * t146 * t205)
  t212 = r1 <= f.p.dens_threshold
  t213 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t214 = 0.1e1 + t213
  t215 = t214 <= f.p.zeta_threshold
  t216 = t214 ** (0.1e1 / 0.3e1)
  t217 = t216 ** 2
  t219 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t222 = f.my_piecewise3(t215, 0, 0.5e1 / 0.3e1 * t217 * t219)
  t223 = t222 * t33
  t224 = jnp.sqrt(s2)
  t225 = r1 ** (0.1e1 / 0.3e1)
  t230 = t40 * t224 / t225 / r1 / 0.12e2
  t231 = t230 <= t48
  t232 = t53 * s2
  t233 = r1 ** 2
  t234 = t225 ** 2
  t240 = s2 ** 2
  t241 = t67 * t240
  t242 = t233 ** 2
  t249 = t240 * s2
  t250 = t242 ** 2
  t255 = t240 ** 2
  t256 = t103 * t255
  t257 = t250 * t233
  t264 = t48 < t230
  t265 = f.my_piecewise3(t264, t230, t48)
  t266 = t265 ** 2
  t267 = params.mu * t266
  t268 = params.alpha * t266
  t269 = jnp.exp(-t268)
  t270 = 0.1e1 + t267
  t271 = 0.1e1 / t270
  t272 = t269 * t271
  t274 = t266 ** 2
  t276 = jnp.exp(-params.alpha * t274)
  t277 = 0.1e1 - t276
  t279 = 0.1e1 / t266 - 0.1e1
  t283 = f.my_piecewise3(t231, 0.1e1 + t51 * t232 / t234 / t233 / 0.24e2 + t65 * t241 / t225 / t242 / r1 / 0.576e3 + t86 * t249 / t250 / 0.2304e4 + t101 * t256 / t234 / t257 / 0.55296e5, 0.1e1 - t267 * t272 + t277 * t279 + 0.5e1 / 0.3e1 * t266)
  t288 = f.my_piecewise3(t215, t138, t217 * t214)
  t289 = t288 * t141
  t292 = t6 * t289 * t283 / 0.10e2
  t294 = f.my_piecewise3(t212, 0, 0.3e1 / 0.20e2 * t6 * t223 * t283 + t292)
  t296 = 0.1e1 / t22
  t297 = t28 ** 2
  t302 = t17 / t24 / t7
  t304 = -0.2e1 * t25 + 0.2e1 * t302
  t305 = f.my_piecewise5(t11, 0, t15, 0, t304)
  t309 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t296 * t297 + 0.5e1 / 0.3e1 * t23 * t305)
  t316 = t6 * t31 * t141 * t132
  t322 = 0.1e1 / t32 / t7
  t326 = t6 * t140 * t322 * t132 / 0.30e2
  t328 = t6 * t142 * t205
  t352 = t177 ** 2
  t358 = t352 * t118 * t120
  t362 = t189 * t352
  t370 = f.my_piecewise3(t113, 0.7e1 / 0.27e2 * t40 * t41 / t42 / t147, 0)
  t371 = t121 * t370
  t395 = t352 * t125 * t128
  t418 = -0.2e1 * params.mu * t352 * t121 + 0.10e2 * t116 * params.alpha * t358 + 0.10e2 * t63 * t115 * t362 - 0.2e1 * t171 * t371 + 0.2e1 * t183 * t371 - 0.4e1 * params.mu * t123 * t77 * t358 - 0.8e1 * t63 * t123 * params.alpha * t362 - 0.8e1 * t97 * t123 * t118 / t187 / t119 * t352 + 0.2e1 * t186 * t189 * t370 + 0.12e2 * t117 * t395 + 0.4e1 * t193 * t370 * t125 * t128 - 0.16e2 * t77 * t123 * t115 * t395 - 0.16e2 * params.alpha * t352 * t125 + 0.6e1 * t126 / t123 * t352 - 0.2e1 * t199 * t370 + 0.10e2 / 0.3e1 * t352 + 0.10e2 / 0.3e1 * t114 * t370
  t419 = f.my_piecewise3(t49, 0.11e2 / 0.27e2 * t51 * t54 / t56 / t70 + 0.19e2 / 0.324e3 * t65 * t69 / t42 / t70 / t147 + t86 * t87 / t106 / 0.32e2 + 0.35e2 / 0.15552e5 * t101 * t105 / t56 / t88 / t70, t418)
  t424 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t309 * t33 * t132 + t316 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t205 - t326 + t328 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t146 * t419)
  t425 = 0.1e1 / t216
  t426 = t219 ** 2
  t430 = f.my_piecewise5(t15, 0, t11, 0, -t304)
  t434 = f.my_piecewise3(t215, 0, 0.10e2 / 0.9e1 * t425 * t426 + 0.5e1 / 0.3e1 * t217 * t430)
  t441 = t6 * t222 * t141 * t283
  t446 = t6 * t288 * t322 * t283 / 0.30e2
  t448 = f.my_piecewise3(t212, 0, 0.3e1 / 0.20e2 * t6 * t434 * t33 * t283 + t441 / 0.5e1 - t446)
  d11 = 0.2e1 * t210 + 0.2e1 * t294 + t7 * (t424 + t448)
  t451 = -t8 - t26
  t452 = f.my_piecewise5(t11, 0, t15, 0, t451)
  t455 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t452)
  t456 = t455 * t33
  t461 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t456 * t132 + t145)
  t463 = f.my_piecewise5(t15, 0, t11, 0, -t451)
  t466 = f.my_piecewise3(t215, 0, 0.5e1 / 0.3e1 * t217 * t463)
  t467 = t466 * t33
  t471 = t288 * t33
  t472 = t233 * r1
  t496 = params.mu * t265
  t502 = f.my_piecewise3(t264, -t40 * t224 / t225 / t233 / 0.9e1, 0)
  t503 = t272 * t502
  t506 = t266 * t265
  t508 = params.mu * t506 * params.alpha
  t511 = t63 * t506
  t512 = t270 ** 2
  t514 = t269 / t512
  t518 = params.alpha * t506
  t524 = t277 / t506
  t530 = f.my_piecewise3(t231, -t51 * t232 / t234 / t472 / 0.9e1 - t65 * t241 / t225 / t242 / t233 / 0.108e3 - t86 * t249 / t250 / r1 / 0.288e3 - t101 * t256 / t234 / t250 / t472 / 0.5184e4, -0.2e1 * t496 * t503 + 0.2e1 * t508 * t503 + 0.2e1 * t511 * t514 * t502 + 0.4e1 * t518 * t502 * t276 * t279 - 0.2e1 * t524 * t502 + 0.10e2 / 0.3e1 * t265 * t502)
  t535 = f.my_piecewise3(t212, 0, 0.3e1 / 0.20e2 * t6 * t467 * t283 + t292 + 0.3e1 / 0.20e2 * t6 * t471 * t530)
  t539 = 0.2e1 * t302
  t540 = f.my_piecewise5(t11, 0, t15, 0, t539)
  t544 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t296 * t452 * t28 + 0.5e1 / 0.3e1 * t23 * t540)
  t551 = t6 * t455 * t141 * t132
  t559 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t544 * t33 * t132 + t551 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t456 * t205 + t316 / 0.10e2 - t326 + t328 / 0.10e2)
  t563 = f.my_piecewise5(t15, 0, t11, 0, -t539)
  t567 = f.my_piecewise3(t215, 0, 0.10e2 / 0.9e1 * t425 * t463 * t219 + 0.5e1 / 0.3e1 * t217 * t563)
  t574 = t6 * t466 * t141 * t283
  t581 = t6 * t289 * t530
  t584 = f.my_piecewise3(t212, 0, 0.3e1 / 0.20e2 * t6 * t567 * t33 * t283 + t574 / 0.10e2 + t441 / 0.10e2 - t446 + 0.3e1 / 0.20e2 * t6 * t223 * t530 + t581 / 0.10e2)
  d12 = t210 + t294 + t461 + t535 + t7 * (t559 + t584)
  t589 = t452 ** 2
  t593 = 0.2e1 * t25 + 0.2e1 * t302
  t594 = f.my_piecewise5(t11, 0, t15, 0, t593)
  t598 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t296 * t589 + 0.5e1 / 0.3e1 * t23 * t594)
  t605 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t598 * t33 * t132 + t551 / 0.5e1 - t326)
  t606 = t463 ** 2
  t610 = f.my_piecewise5(t15, 0, t11, 0, -t593)
  t614 = f.my_piecewise3(t215, 0, 0.10e2 / 0.9e1 * t425 * t606 + 0.5e1 / 0.3e1 * t217 * t610)
  t646 = t502 ** 2
  t652 = t646 * t269 * t271
  t656 = t514 * t646
  t664 = f.my_piecewise3(t264, 0.7e1 / 0.27e2 * t40 * t224 / t225 / t472, 0)
  t665 = t272 * t664
  t689 = t646 * t276 * t279
  t712 = -0.2e1 * params.mu * t646 * t272 + 0.10e2 * t267 * params.alpha * t652 + 0.10e2 * t63 * t266 * t656 - 0.2e1 * t496 * t665 + 0.2e1 * t508 * t665 - 0.4e1 * params.mu * t274 * t77 * t652 - 0.8e1 * t63 * t274 * params.alpha * t656 - 0.8e1 * t97 * t274 * t269 / t512 / t270 * t646 + 0.2e1 * t511 * t514 * t664 + 0.12e2 * t268 * t689 + 0.4e1 * t518 * t664 * t276 * t279 - 0.16e2 * t77 * t274 * t266 * t689 - 0.16e2 * params.alpha * t646 * t276 + 0.6e1 * t277 / t274 * t646 - 0.2e1 * t524 * t664 + 0.10e2 / 0.3e1 * t646 + 0.10e2 / 0.3e1 * t265 * t664
  t713 = f.my_piecewise3(t231, 0.11e2 / 0.27e2 * t51 * t232 / t234 / t242 + 0.19e2 / 0.324e3 * t65 * t241 / t225 / t242 / t472 + t86 * t249 / t257 / 0.32e2 + 0.35e2 / 0.15552e5 * t101 * t256 / t234 / t250 / t242, t712)
  t718 = f.my_piecewise3(t212, 0, 0.3e1 / 0.20e2 * t6 * t614 * t33 * t283 + t574 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t467 * t530 - t446 + t581 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t471 * t713)
  d22 = 0.2e1 * t461 + 0.2e1 * t535 + t7 * (t605 + t718)
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
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t51 = t47 / t49
  t52 = jnp.sqrt(s0)
  t53 = r0 ** (0.1e1 / 0.3e1)
  t58 = t51 * t52 / t53 / r0 / 0.12e2
  t59 = jnp.sqrt(DBL_EPSILON)
  t60 = t58 <= t59
  t62 = (-params.mu + params.alpha + 0.5e1 / 0.3e1) * t46
  t63 = t49 ** 2
  t64 = 0.1e1 / t63
  t65 = t64 * s0
  t66 = r0 ** 2
  t67 = t53 ** 2
  t73 = params.mu * params.alpha
  t74 = params.mu ** 2
  t76 = (t73 + t74 - params.alpha) * t47
  t78 = 0.1e1 / t49 / t48
  t79 = s0 ** 2
  t80 = t78 * t79
  t81 = t66 ** 2
  t82 = t81 * r0
  t88 = params.alpha ** 2
  t90 = params.mu * t88 / 0.2e1
  t93 = t88 / 0.2e1
  t95 = t48 ** 2
  t97 = (-t90 - (t73 + t74) * params.mu - t93) / t95
  t98 = t79 * s0
  t99 = t81 ** 2
  t104 = t88 * params.alpha
  t108 = t74 * params.mu
  t112 = (params.mu * t104 / 0.6e1 - (-params.alpha * t74 - t108 - t90) * params.mu + t93) * t46
  t114 = 0.1e1 / t63 / t95
  t115 = t79 ** 2
  t116 = t114 * t115
  t117 = t99 * t66
  t124 = t59 < t58
  t125 = f.my_piecewise3(t124, t58, t59)
  t126 = t125 ** 2
  t127 = params.mu * t126
  t128 = params.alpha * t126
  t129 = jnp.exp(-t128)
  t130 = 0.1e1 + t127
  t131 = 0.1e1 / t130
  t132 = t129 * t131
  t134 = t126 ** 2
  t136 = jnp.exp(-params.alpha * t134)
  t137 = 0.1e1 - t136
  t139 = 0.1e1 / t126 - 0.1e1
  t143 = f.my_piecewise3(t60, 0.1e1 + t62 * t65 / t67 / t66 / 0.24e2 + t76 * t80 / t53 / t82 / 0.576e3 + t97 * t98 / t99 / 0.2304e4 + t112 * t116 / t67 / t117 / 0.55296e5, 0.1e1 - t127 * t132 + t137 * t139 + 0.5e1 / 0.3e1 * t126)
  t149 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t150 = 0.1e1 / t43
  t151 = t149 * t150
  t155 = t149 * t44
  t156 = t66 * r0
  t173 = t99 * t156
  t180 = params.mu * t125
  t186 = f.my_piecewise3(t124, -t51 * t52 / t53 / t66 / 0.9e1, 0)
  t187 = t132 * t186
  t190 = t126 * t125
  t191 = params.mu * t190
  t192 = t191 * params.alpha
  t195 = t74 * t190
  t196 = t130 ** 2
  t197 = 0.1e1 / t196
  t198 = t129 * t197
  t202 = params.alpha * t190
  t203 = t186 * t136
  t204 = t203 * t139
  t208 = t137 / t190
  t214 = f.my_piecewise3(t60, -t62 * t65 / t67 / t156 / 0.9e1 - t76 * t80 / t53 / t81 / t66 / 0.108e3 - t97 * t98 / t99 / r0 / 0.288e3 - t112 * t116 / t67 / t173 / 0.5184e4, -0.2e1 * t180 * t187 + 0.2e1 * t192 * t187 + 0.2e1 * t195 * t198 * t186 + 0.4e1 * t202 * t204 - 0.2e1 * t208 * t186 + 0.10e2 / 0.3e1 * t125 * t186)
  t218 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t219 = t218 ** 2
  t220 = t219 * f.p.zeta_threshold
  t222 = f.my_piecewise3(t21, t220, t32 * t20)
  t224 = 0.1e1 / t43 / t7
  t225 = t222 * t224
  t229 = t222 * t150
  t233 = t222 * t44
  t256 = t186 ** 2
  t260 = t127 * params.alpha
  t262 = t256 * t129 * t131
  t265 = t74 * t126
  t266 = t198 * t256
  t274 = f.my_piecewise3(t124, 0.7e1 / 0.27e2 * t51 * t52 / t53 / t156, 0)
  t275 = t132 * t274
  t281 = params.mu * t134 * t88
  t285 = t74 * t134 * params.alpha
  t288 = t108 * t134
  t290 = 0.1e1 / t196 / t130
  t291 = t129 * t290
  t299 = t256 * t136 * t139
  t303 = t274 * t136 * t139
  t307 = t88 * t134 * t126
  t314 = t137 / t134
  t322 = -0.2e1 * params.mu * t256 * t132 + 0.10e2 * t260 * t262 + 0.10e2 * t265 * t266 - 0.2e1 * t180 * t275 + 0.2e1 * t192 * t275 - 0.4e1 * t281 * t262 - 0.8e1 * t285 * t266 - 0.8e1 * t288 * t291 * t256 + 0.2e1 * t195 * t198 * t274 + 0.12e2 * t128 * t299 + 0.4e1 * t202 * t303 - 0.16e2 * t307 * t299 - 0.16e2 * params.alpha * t256 * t136 + 0.6e1 * t314 * t256 - 0.2e1 * t208 * t274 + 0.10e2 / 0.3e1 * t256 + 0.10e2 / 0.3e1 * t125 * t274
  t323 = f.my_piecewise3(t60, 0.11e2 / 0.27e2 * t62 * t65 / t67 / t81 + 0.19e2 / 0.324e3 * t76 * t80 / t53 / t81 / t156 + t97 * t98 / t117 / 0.32e2 + 0.35e2 / 0.15552e5 * t112 * t116 / t67 / t99 / t81, t322)
  t328 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t143 + t6 * t151 * t143 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t155 * t214 - t6 * t225 * t143 / 0.30e2 + t6 * t229 * t214 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t233 * t323)
  t330 = r1 <= f.p.dens_threshold
  t331 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t332 = 0.1e1 + t331
  t333 = t332 <= f.p.zeta_threshold
  t334 = t332 ** (0.1e1 / 0.3e1)
  t335 = 0.1e1 / t334
  t337 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t338 = t337 ** 2
  t341 = t334 ** 2
  t343 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t347 = f.my_piecewise3(t333, 0, 0.10e2 / 0.9e1 * t335 * t338 + 0.5e1 / 0.3e1 * t341 * t343)
  t349 = jnp.sqrt(s2)
  t350 = r1 ** (0.1e1 / 0.3e1)
  t355 = t51 * t349 / t350 / r1 / 0.12e2
  t358 = r1 ** 2
  t359 = t350 ** 2
  t365 = s2 ** 2
  t367 = t358 ** 2
  t375 = t367 ** 2
  t380 = t365 ** 2
  t390 = f.my_piecewise3(t59 < t355, t355, t59)
  t391 = t390 ** 2
  t392 = params.mu * t391
  t394 = jnp.exp(-params.alpha * t391)
  t399 = t391 ** 2
  t401 = jnp.exp(-params.alpha * t399)
  t408 = f.my_piecewise3(t355 <= t59, 0.1e1 + t62 * t64 * s2 / t359 / t358 / 0.24e2 + t76 * t78 * t365 / t350 / t367 / r1 / 0.576e3 + t97 * t365 * s2 / t375 / 0.2304e4 + t112 * t114 * t380 / t359 / t375 / t358 / 0.55296e5, 0.1e1 - t392 * t394 / (0.1e1 + t392) + (0.1e1 - t401) * (0.1e1 / t391 - 0.1e1) + 0.5e1 / 0.3e1 * t391)
  t414 = f.my_piecewise3(t333, 0, 0.5e1 / 0.3e1 * t341 * t337)
  t420 = f.my_piecewise3(t333, t220, t341 * t332)
  t426 = f.my_piecewise3(t330, 0, 0.3e1 / 0.20e2 * t6 * t347 * t44 * t408 + t6 * t414 * t150 * t408 / 0.5e1 - t6 * t420 * t224 * t408 / 0.30e2)
  t436 = t24 ** 2
  t440 = 0.6e1 * t34 - 0.6e1 * t17 / t436
  t441 = f.my_piecewise5(t11, 0, t15, 0, t440)
  t445 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t441)
  t468 = 0.1e1 / t43 / t24
  t500 = t186 * t274
  t507 = f.my_piecewise3(t124, -0.70e2 / 0.81e2 * t51 * t52 / t53 / t81, 0)
  t511 = t256 * t186
  t512 = t291 * t511
  t515 = t132 * t507
  t518 = t74 ** 2
  t519 = t134 * t125
  t521 = t196 ** 2
  t531 = t511 * t136
  t532 = t531 * t139
  t539 = t134 ** 2
  t563 = 0.10e2 * t500 + 0.10e2 / 0.3e1 * t125 * t507 - 0.72e2 * t108 * t190 * t512 - 0.2e1 * t180 * t515 + 0.48e2 * t518 * t519 * t129 / t521 * t511 + 0.2e1 * t195 * t198 * t507 - 0.144e3 * t88 * t519 * t532 + 0.4e1 * t202 * t507 * t136 * t139 + 0.64e2 * t104 * t539 * t125 * t532 + 0.24e2 * params.alpha * t125 * t532 - 0.6e1 * params.mu * t186 * t275 + 0.24e2 * t74 * t511 * t198 * t125 - 0.2e1 * t208 * t507 - 0.24e2 * t137 / t519 * t511 - 0.48e2 * params.alpha * t274 * t203
  t571 = t186 * t129 * t131 * t274
  t577 = t197 * t186
  t588 = t511 * t129
  t589 = t588 * t131
  t593 = t588 * t197
  t625 = 0.96e2 * t88 * t190 * t531 + 0.18e2 * t314 * t500 + 0.30e2 * t260 * t571 - 0.12e2 * t281 * t571 - 0.24e2 * t285 * t274 * t129 * t577 + 0.24e2 * params.mu * t511 * params.alpha * t125 * t129 * t131 - 0.36e2 * t191 * t88 * t589 - 0.72e2 * t195 * params.alpha * t593 + 0.30e2 * t265 * t129 * t577 * t274 + 0.2e1 * t192 * t515 + 0.8e1 * params.mu * t519 * t104 * t589 + 0.24e2 * t74 * t519 * t88 * t593 + 0.48e2 * t108 * t519 * params.alpha * t512 - 0.24e2 * t288 * t129 * t290 * t186 * t274 + 0.36e2 * t128 * t186 * t303 - 0.48e2 * t307 * t274 * t204
  t627 = f.my_piecewise3(t60, -0.154e3 / 0.81e2 * t62 * t65 / t67 / t82 - 0.209e3 / 0.486e3 * t76 * t80 / t53 / t99 - 0.5e1 / 0.16e2 * t97 * t98 / t173 - 0.665e3 / 0.23328e5 * t112 * t116 / t67 / t99 / t82, t563 + t625)
  t632 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t445 * t44 * t143 + 0.3e1 / 0.10e2 * t6 * t42 * t150 * t143 + 0.9e1 / 0.20e2 * t6 * t45 * t214 - t6 * t149 * t224 * t143 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t151 * t214 + 0.9e1 / 0.20e2 * t6 * t155 * t323 + 0.2e1 / 0.45e2 * t6 * t222 * t468 * t143 - t6 * t225 * t214 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t229 * t323 + 0.3e1 / 0.20e2 * t6 * t233 * t627)
  t642 = f.my_piecewise5(t15, 0, t11, 0, -t440)
  t646 = f.my_piecewise3(t333, 0, -0.10e2 / 0.27e2 / t334 / t332 * t338 * t337 + 0.10e2 / 0.3e1 * t335 * t337 * t343 + 0.5e1 / 0.3e1 * t341 * t642)
  t664 = f.my_piecewise3(t330, 0, 0.3e1 / 0.20e2 * t6 * t646 * t44 * t408 + 0.3e1 / 0.10e2 * t6 * t347 * t150 * t408 - t6 * t414 * t224 * t408 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t420 * t468 * t408)
  d111 = 0.3e1 * t328 + 0.3e1 * t426 + t7 * (t632 + t664)

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
  t58 = 6 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t60 = jnp.pi ** 2
  t61 = t60 ** (0.1e1 / 0.3e1)
  t63 = t59 / t61
  t64 = jnp.sqrt(s0)
  t65 = r0 ** (0.1e1 / 0.3e1)
  t70 = t63 * t64 / t65 / r0 / 0.12e2
  t71 = jnp.sqrt(DBL_EPSILON)
  t72 = t70 <= t71
  t74 = (-params.mu + params.alpha + 0.5e1 / 0.3e1) * t58
  t75 = t61 ** 2
  t76 = 0.1e1 / t75
  t77 = t76 * s0
  t78 = r0 ** 2
  t79 = t65 ** 2
  t85 = params.alpha * params.mu
  t86 = params.mu ** 2
  t88 = (t85 + t86 - params.alpha) * t59
  t90 = 0.1e1 / t61 / t60
  t91 = s0 ** 2
  t92 = t90 * t91
  t93 = t78 ** 2
  t94 = t93 * r0
  t96 = 0.1e1 / t65 / t94
  t100 = params.alpha ** 2
  t102 = params.mu * t100 / 0.2e1
  t105 = t100 / 0.2e1
  t107 = t60 ** 2
  t109 = (-t102 - (t85 + t86) * params.mu - t105) / t107
  t110 = t91 * s0
  t111 = t93 ** 2
  t116 = t100 * params.alpha
  t120 = t86 * params.mu
  t124 = (params.mu * t116 / 0.6e1 - (-params.alpha * t86 - t102 - t120) * params.mu + t105) * t58
  t126 = 0.1e1 / t75 / t107
  t127 = t91 ** 2
  t128 = t126 * t127
  t129 = t111 * t78
  t136 = t71 < t70
  t137 = f.my_piecewise3(t136, t70, t71)
  t138 = t137 ** 2
  t139 = params.mu * t138
  t140 = params.alpha * t138
  t141 = jnp.exp(-t140)
  t142 = 0.1e1 + t139
  t143 = 0.1e1 / t142
  t144 = t141 * t143
  t146 = t138 ** 2
  t148 = jnp.exp(-params.alpha * t146)
  t149 = 0.1e1 - t148
  t150 = 0.1e1 / t138
  t151 = t150 - 0.1e1
  t155 = f.my_piecewise3(t72, 0.1e1 + t74 * t77 / t79 / t78 / 0.24e2 + t88 * t92 * t96 / 0.576e3 + t109 * t110 / t111 / 0.2304e4 + t124 * t128 / t79 / t129 / 0.55296e5, 0.1e1 - t139 * t144 + t149 * t151 + 0.5e1 / 0.3e1 * t138)
  t164 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t165 = 0.1e1 / t55
  t166 = t164 * t165
  t170 = t164 * t56
  t171 = t78 * r0
  t177 = t93 * t78
  t183 = t111 * r0
  t188 = t111 * t171
  t195 = params.mu * t137
  t201 = f.my_piecewise3(t136, -t63 * t64 / t65 / t78 / 0.9e1, 0)
  t202 = t144 * t201
  t205 = t138 * t137
  t206 = params.mu * t205
  t207 = t206 * params.alpha
  t210 = t86 * t205
  t211 = t142 ** 2
  t212 = 0.1e1 / t211
  t213 = t141 * t212
  t217 = params.alpha * t205
  t218 = t201 * t148
  t219 = t218 * t151
  t223 = t149 / t205
  t229 = f.my_piecewise3(t72, -t74 * t77 / t79 / t171 / 0.9e1 - t88 * t92 / t65 / t177 / 0.108e3 - t109 * t110 / t183 / 0.288e3 - t124 * t128 / t79 / t188 / 0.5184e4, -0.2e1 * t195 * t202 + 0.2e1 * t207 * t202 + 0.2e1 * t210 * t213 * t201 + 0.4e1 * t217 * t219 - 0.2e1 * t223 * t201 + 0.10e2 / 0.3e1 * t137 * t201)
  t235 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t237 = 0.1e1 / t55 / t7
  t238 = t235 * t237
  t242 = t235 * t165
  t246 = t235 * t56
  t262 = t111 * t93
  t269 = t201 ** 2
  t270 = params.mu * t269
  t273 = t139 * params.alpha
  t274 = t269 * t141
  t275 = t274 * t143
  t278 = t86 * t138
  t279 = t213 * t269
  t287 = f.my_piecewise3(t136, 0.7e1 / 0.27e2 * t63 * t64 / t65 / t171, 0)
  t288 = t144 * t287
  t293 = params.mu * t146
  t294 = t293 * t100
  t297 = t86 * t146
  t298 = t297 * params.alpha
  t301 = t120 * t146
  t303 = 0.1e1 / t211 / t142
  t304 = t141 * t303
  t312 = t269 * t148 * t151
  t316 = t287 * t148 * t151
  t319 = t146 * t138
  t320 = t100 * t319
  t327 = t149 / t146
  t335 = -0.2e1 * t270 * t144 + 0.10e2 * t273 * t275 + 0.10e2 * t278 * t279 - 0.2e1 * t195 * t288 + 0.2e1 * t207 * t288 - 0.4e1 * t294 * t275 - 0.8e1 * t298 * t279 - 0.8e1 * t301 * t304 * t269 + 0.2e1 * t210 * t213 * t287 + 0.12e2 * t140 * t312 + 0.4e1 * t217 * t316 - 0.16e2 * t320 * t312 - 0.16e2 * params.alpha * t269 * t148 + 0.6e1 * t327 * t269 - 0.2e1 * t223 * t287 + 0.10e2 / 0.3e1 * t269 + 0.10e2 / 0.3e1 * t137 * t287
  t336 = f.my_piecewise3(t72, 0.11e2 / 0.27e2 * t74 * t77 / t79 / t93 + 0.19e2 / 0.324e3 * t88 * t92 / t65 / t93 / t171 + t109 * t110 / t129 / 0.32e2 + 0.35e2 / 0.15552e5 * t124 * t128 / t79 / t262, t335)
  t340 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t341 = t340 ** 2
  t342 = t341 * f.p.zeta_threshold
  t344 = f.my_piecewise3(t21, t342, t44 * t20)
  t346 = 0.1e1 / t55 / t25
  t347 = t344 * t346
  t351 = t344 * t237
  t355 = t344 * t165
  t359 = t344 * t56
  t381 = t120 * t205
  t382 = t269 * t201
  t383 = t304 * t382
  t391 = f.my_piecewise3(t136, -0.70e2 / 0.81e2 * t63 * t64 / t65 / t93, 0)
  t392 = t144 * t391
  t395 = t86 ** 2
  t396 = t146 * t137
  t397 = t395 * t396
  t398 = t211 ** 2
  t399 = 0.1e1 / t398
  t400 = t141 * t399
  t407 = t100 * t396
  t408 = t382 * t148
  t409 = t408 * t151
  t416 = t146 ** 2
  t418 = t116 * t416 * t137
  t421 = params.alpha * t137
  t424 = params.mu * t201
  t437 = t201 * t287
  t443 = -0.72e2 * t381 * t383 - 0.2e1 * t195 * t392 + 0.48e2 * t397 * t400 * t382 + 0.2e1 * t210 * t213 * t391 - 0.144e3 * t407 * t409 + 0.4e1 * t217 * t391 * t148 * t151 + 0.64e2 * t418 * t409 + 0.24e2 * t421 * t409 - 0.6e1 * t424 * t288 + 0.24e2 * t86 * t382 * t213 * t137 - 0.48e2 * params.alpha * t287 * t218 + 0.96e2 * t100 * t205 * t408 + 0.18e2 * t327 * t437 + 0.10e2 * t437 + 0.10e2 / 0.3e1 * t137 * t391
  t446 = t137 * t141
  t450 = t206 * t100
  t451 = t382 * t141
  t452 = t451 * t143
  t455 = t210 * params.alpha
  t456 = t451 * t212
  t459 = t278 * t141
  t460 = t212 * t201
  t467 = params.mu * t396 * t116
  t471 = t86 * t396 * t100
  t475 = t120 * t396 * params.alpha
  t478 = t301 * t141
  t492 = t149 / t396
  t495 = t201 * t141
  t496 = t143 * t287
  t497 = t495 * t496
  t502 = t287 * t141
  t506 = 0.24e2 * params.mu * t382 * params.alpha * t446 * t143 - 0.36e2 * t450 * t452 - 0.72e2 * t455 * t456 + 0.30e2 * t459 * t460 * t287 + 0.2e1 * t207 * t392 + 0.8e1 * t467 * t452 + 0.24e2 * t471 * t456 + 0.48e2 * t475 * t383 - 0.24e2 * t478 * t303 * t201 * t287 + 0.36e2 * t140 * t201 * t316 - 0.48e2 * t320 * t287 * t219 - 0.2e1 * t223 * t391 - 0.24e2 * t492 * t382 + 0.30e2 * t273 * t497 - 0.12e2 * t294 * t497 - 0.24e2 * t298 * t502 * t460
  t508 = f.my_piecewise3(t72, -0.154e3 / 0.81e2 * t74 * t77 / t79 / t94 - 0.209e3 / 0.486e3 * t88 * t92 / t65 / t111 - 0.5e1 / 0.16e2 * t109 * t110 / t188 - 0.665e3 / 0.23328e5 * t124 * t128 / t79 / t111 / t94, t443 + t506)
  t513 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t155 + 0.3e1 / 0.10e2 * t6 * t166 * t155 + 0.9e1 / 0.20e2 * t6 * t170 * t229 - t6 * t238 * t155 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t242 * t229 + 0.9e1 / 0.20e2 * t6 * t246 * t336 + 0.2e1 / 0.45e2 * t6 * t347 * t155 - t6 * t351 * t229 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t355 * t336 + 0.3e1 / 0.20e2 * t6 * t359 * t508)
  t515 = r1 <= f.p.dens_threshold
  t516 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t517 = 0.1e1 + t516
  t518 = t517 <= f.p.zeta_threshold
  t519 = t517 ** (0.1e1 / 0.3e1)
  t521 = 0.1e1 / t519 / t517
  t523 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t524 = t523 ** 2
  t528 = 0.1e1 / t519
  t529 = t528 * t523
  t531 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t534 = t519 ** 2
  t536 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t540 = f.my_piecewise3(t518, 0, -0.10e2 / 0.27e2 * t521 * t524 * t523 + 0.10e2 / 0.3e1 * t529 * t531 + 0.5e1 / 0.3e1 * t534 * t536)
  t542 = jnp.sqrt(s2)
  t543 = r1 ** (0.1e1 / 0.3e1)
  t548 = t63 * t542 / t543 / r1 / 0.12e2
  t551 = r1 ** 2
  t552 = t543 ** 2
  t558 = s2 ** 2
  t560 = t551 ** 2
  t568 = t560 ** 2
  t573 = t558 ** 2
  t583 = f.my_piecewise3(t71 < t548, t548, t71)
  t584 = t583 ** 2
  t585 = params.mu * t584
  t587 = jnp.exp(-params.alpha * t584)
  t592 = t584 ** 2
  t594 = jnp.exp(-params.alpha * t592)
  t601 = f.my_piecewise3(t548 <= t71, 0.1e1 + t74 * t76 * s2 / t552 / t551 / 0.24e2 + t88 * t90 * t558 / t543 / t560 / r1 / 0.576e3 + t109 * t558 * s2 / t568 / 0.2304e4 + t124 * t126 * t573 / t552 / t568 / t551 / 0.55296e5, 0.1e1 - t585 * t587 / (0.1e1 + t585) + (0.1e1 - t594) * (0.1e1 / t584 - 0.1e1) + 0.5e1 / 0.3e1 * t584)
  t610 = f.my_piecewise3(t518, 0, 0.10e2 / 0.9e1 * t528 * t524 + 0.5e1 / 0.3e1 * t534 * t531)
  t617 = f.my_piecewise3(t518, 0, 0.5e1 / 0.3e1 * t534 * t523)
  t623 = f.my_piecewise3(t518, t342, t534 * t517)
  t629 = f.my_piecewise3(t515, 0, 0.3e1 / 0.20e2 * t6 * t540 * t56 * t601 + 0.3e1 / 0.10e2 * t6 * t610 * t165 * t601 - t6 * t617 * t237 * t601 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t623 * t346 * t601)
  t652 = t287 ** 2
  t655 = t269 ** 2
  t656 = t655 * t148
  t657 = t656 * t151
  t669 = f.my_piecewise3(t136, 0.910e3 / 0.243e3 * t63 * t64 * t96, 0)
  t681 = t652 * t148 * t151
  t686 = params.mu * t655
  t691 = t213 * t652
  t698 = t400 * t655
  t701 = t144 * t669
  t717 = 0.10e2 * t652 - 0.816e3 * t100 * t146 * t657 - 0.8e1 * t424 * t392 - 0.312e3 * t120 * t655 * t304 * t138 + 0.2e1 * t210 * t213 * t669 + 0.4e1 * t217 * t669 * t148 * t151 - 0.24e2 * t301 * t304 * t652 + 0.36e2 * t140 * t681 - 0.48e2 * t320 * t681 + 0.24e2 * t686 * params.alpha * t141 * t143 + 0.30e2 * t278 * t691 + 0.1152e4 * t116 * t416 * t657 + 0.672e3 * t395 * t146 * t698 - 0.2e1 * t195 * t701 - 0.384e3 * t395 * params.mu * t319 * t141 / t398 / t142 * t655 + 0.576e3 * t100 * t287 * t205 * t269 * t148
  t718 = t100 ** 2
  t726 = t86 * t655
  t741 = t201 * t391
  t755 = t652 * t141 * t143
  t760 = t655 * t141
  t761 = t760 * t143
  t766 = t760 * t212
  t771 = t760 * t303
  t774 = -0.256e3 * t718 * t416 * t146 * t657 - 0.6e1 * params.mu * t652 * t144 + 0.24e2 * t726 * t213 + 0.576e3 * t100 * t138 * t656 - 0.144e3 * t492 * t269 * t287 - 0.64e2 * params.alpha * t391 * t218 - 0.512e3 * t116 * t319 * t656 + 0.24e2 * t327 * t741 - 0.144e3 * params.alpha * t150 * t656 + 0.24e2 * params.alpha * t655 * t148 * t151 + 0.40e2 / 0.3e1 * t741 + 0.10e2 / 0.3e1 * t137 * t669 - 0.12e2 * t294 * t755 - 0.16e2 * params.mu * t319 * t718 * t761 - 0.64e2 * t86 * t319 * t116 * t766 - 0.192e3 * t120 * t319 * t100 * t771
  t777 = t303 * t269
  t794 = t138 * t141
  t814 = t212 * t287
  t836 = -0.432e3 * t381 * t141 * t777 * t287 + 0.672e3 * t301 * params.alpha * t771 + 0.288e3 * t397 * t141 * t399 * t269 * t287 - 0.384e3 * t395 * t319 * params.alpha * t698 - 0.156e3 * t686 * t100 * t794 * t143 + 0.112e3 * t293 * t116 * t761 + 0.336e3 * t297 * t100 * t766 + 0.2e1 * t207 * t701 + 0.384e3 * t418 * t269 * t316 + 0.144e3 * t421 * t269 * t316 + 0.144e3 * t86 * t269 * t141 * t814 * t137 - 0.312e3 * t726 * params.alpha * t794 * t212 + 0.40e2 * t459 * t212 * t391 * t201 - 0.32e2 * t478 * t303 * t391 * t201 - 0.864e3 * t407 * t269 * t316 + 0.48e2 * t140 * t391 * t219
  t856 = t495 * t143 * t391
  t859 = t274 * t496
  t862 = t274 * t814
  t882 = -0.64e2 * t320 * t391 * t219 - 0.24e2 * t298 * t691 + 0.30e2 * t273 * t755 - 0.48e2 * params.alpha * t652 * t148 + 0.18e2 * t327 * t652 + 0.120e3 * t149 / t319 * t655 - 0.2e1 * t223 * t669 + 0.40e2 * t273 * t856 - 0.216e3 * t450 * t859 - 0.432e3 * t455 * t862 - 0.16e2 * t294 * t856 + 0.48e2 * t467 * t859 + 0.144e3 * t471 * t862 - 0.32e2 * t298 * t391 * t141 * t460 + 0.288e3 * t475 * t502 * t777 + 0.144e3 * t270 * params.alpha * t446 * t496
  t885 = f.my_piecewise3(t72, 0.2618e4 / 0.243e3 * t74 * t77 / t79 / t177 + 0.5225e4 / 0.1458e4 * t88 * t92 / t65 / t183 + 0.55e2 / 0.16e2 * t109 * t110 / t262 + 0.27265e5 / 0.69984e5 * t124 * t128 / t79 / t111 / t177, t717 + t774 + t836 + t882)
  t889 = t20 ** 2
  t892 = t30 ** 2
  t898 = t41 ** 2
  t907 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t908 = f.my_piecewise5(t11, 0, t15, 0, t907)
  t912 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t889 * t892 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t898 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t908)
  t957 = 0.1e1 / t55 / t36
  t962 = 0.3e1 / 0.20e2 * t6 * t359 * t885 + 0.3e1 / 0.20e2 * t6 * t912 * t56 * t155 + 0.3e1 / 0.5e1 * t6 * t57 * t229 + 0.6e1 / 0.5e1 * t6 * t166 * t229 + 0.9e1 / 0.10e2 * t6 * t170 * t336 - 0.2e1 / 0.5e1 * t6 * t238 * t229 + 0.6e1 / 0.5e1 * t6 * t242 * t336 + 0.3e1 / 0.5e1 * t6 * t246 * t508 + 0.8e1 / 0.45e2 * t6 * t347 * t229 - t6 * t351 * t336 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t355 * t508 + 0.2e1 / 0.5e1 * t6 * t54 * t165 * t155 - t6 * t164 * t237 * t155 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t235 * t346 * t155 - 0.14e2 / 0.135e3 * t6 * t344 * t957 * t155
  t963 = f.my_piecewise3(t1, 0, t962)
  t964 = t517 ** 2
  t967 = t524 ** 2
  t973 = t531 ** 2
  t979 = f.my_piecewise5(t15, 0, t11, 0, -t907)
  t983 = f.my_piecewise3(t518, 0, 0.40e2 / 0.81e2 / t519 / t964 * t967 - 0.20e2 / 0.9e1 * t521 * t524 * t531 + 0.10e2 / 0.3e1 * t528 * t973 + 0.40e2 / 0.9e1 * t529 * t536 + 0.5e1 / 0.3e1 * t534 * t979)
  t1005 = f.my_piecewise3(t515, 0, 0.3e1 / 0.20e2 * t6 * t983 * t56 * t601 + 0.2e1 / 0.5e1 * t6 * t540 * t165 * t601 - t6 * t610 * t237 * t601 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t617 * t346 * t601 - 0.14e2 / 0.135e3 * t6 * t623 * t957 * t601)
  d1111 = 0.4e1 * t513 + 0.4e1 * t629 + t7 * (t963 + t1005)

  res = {'v4rho4': d1111}
  return res
