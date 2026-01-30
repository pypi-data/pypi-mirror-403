"""Generated from gga_xc_th3.mpl."""

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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  params_n = 19

  params_a = [None, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 17 / 12, 9 / 6, 10 / 6, 11 / 6, 10 / 6, 11 / 6, 12 / 6, 10 / 6, 11 / 6, 12 / 6, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 13 / 12.0]

  params_b = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0], dtype=np.float64)

  params_c = np.array([np.nan, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float64)

  params_d = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0], dtype=np.float64)

  XX = lambda z, xs: xs * f.opz_pow_n(z, 4 / 3) * 2 ** (-4 / 3)

  YY = lambda z, xt, xs0, xs1: 2 * (XX(z, xs0) ** 2 + XX(-z, xs1) ** 2) - xt ** 2

  f_th = lambda rs, z, xt, xs0, xs1: jnp.sum(jnp.array([params_omega[i] * (f.n_spin(rs, z) ** params_a[i] + f.n_spin(rs, -z) ** params_a[i]) * z ** (2 * params_b[i]) * 1 / 2 * (XX(z, xs0) ** params_c[i] + XX(-z, xs1) ** params_c[i]) * YY(z, xt, xs0, xs1) ** params_d[i] for i in range(1, params_n + 1)]), axis=0) / f.n_total(rs)

  functional_body = lambda rs, z, xt, xs0, xs1: f_th(rs, z, xt, xs0, xs1)

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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  params_n = 19

  params_a = [None, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 17 / 12, 9 / 6, 10 / 6, 11 / 6, 10 / 6, 11 / 6, 12 / 6, 10 / 6, 11 / 6, 12 / 6, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 13 / 12.0]

  params_b = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0], dtype=np.float64)

  params_c = np.array([np.nan, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float64)

  params_d = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0], dtype=np.float64)

  XX = lambda z, xs: xs * f.opz_pow_n(z, 4 / 3) * 2 ** (-4 / 3)

  YY = lambda z, xt, xs0, xs1: 2 * (XX(z, xs0) ** 2 + XX(-z, xs1) ** 2) - xt ** 2

  f_th = lambda rs, z, xt, xs0, xs1: jnp.sum(jnp.array([params_omega[i] * (f.n_spin(rs, z) ** params_a[i] + f.n_spin(rs, -z) ** params_a[i]) * z ** (2 * params_b[i]) * 1 / 2 * (XX(z, xs0) ** params_c[i] + XX(-z, xs1) ** params_c[i]) * YY(z, xt, xs0, xs1) ** params_d[i] for i in range(1, params_n + 1)]), axis=0) / f.n_total(rs)

  functional_body = lambda rs, z, xt, xs0, xs1: f_th(rs, z, xt, xs0, xs1)

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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  params_n = 19

  params_a = [None, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 17 / 12, 9 / 6, 10 / 6, 11 / 6, 10 / 6, 11 / 6, 12 / 6, 10 / 6, 11 / 6, 12 / 6, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 13 / 12.0]

  params_b = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0], dtype=np.float64)

  params_c = np.array([np.nan, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float64)

  params_d = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0], dtype=np.float64)

  XX = lambda z, xs: xs * f.opz_pow_n(z, 4 / 3) * 2 ** (-4 / 3)

  YY = lambda z, xt, xs0, xs1: 2 * (XX(z, xs0) ** 2 + XX(-z, xs1) ** 2) - xt ** 2

  f_th = lambda rs, z, xt, xs0, xs1: jnp.sum(jnp.array([params_omega[i] * (f.n_spin(rs, z) ** params_a[i] + f.n_spin(rs, -z) ** params_a[i]) * z ** (2 * params_b[i]) * 1 / 2 * (XX(z, xs0) ** params_c[i] + XX(-z, xs1) ** params_c[i]) * YY(z, xt, xs0, xs1) ** params_d[i] for i in range(1, params_n + 1)]), axis=0) / f.n_total(rs)

  functional_body = lambda rs, z, xt, xs0, xs1: f_th(rs, z, xt, xs0, xs1)

  t1 = params.omega[0]
  t2 = r0 ** (0.1e1 / 0.6e1)
  t5 = params.omega[1]
  t6 = r0 ** (0.1e1 / 0.3e1)
  t9 = params.omega[2]
  t10 = jnp.sqrt(r0)
  t13 = params.omega[3]
  t14 = t6 ** 2
  t17 = params.omega[18]
  t18 = r0 ** 0.833333333333333333333333333333333333333333333333e-1
  t21 = params.omega[14]
  t23 = r1 ** (0.1e1 / 0.6e1)
  t26 = t21 * (t2 * r0 + t23 * r1)
  t27 = r0 - r1
  t28 = r0 + r1
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = t27 * t30
  t33 = 0.2e1 * t26 * t31
  t34 = t27 ** 2
  t35 = t29 * t28
  t37 = t34 / t35
  t39 = 0.2e1 * t26 * t37
  t40 = params.omega[15]
  t41 = t6 * r0
  t42 = r1 ** (0.1e1 / 0.3e1)
  t43 = t42 * r1
  t45 = t40 * (t41 + t43)
  t47 = 0.2e1 * t45 * t31
  t49 = 0.2e1 * t45 * t37
  t50 = params.omega[16]
  t52 = jnp.sqrt(r1)
  t54 = t10 * r0 + t52 * r1
  t55 = t50 * t54
  t57 = 0.2e1 * t55 * t31
  t59 = 0.2e1 * t55 * t37
  t60 = params.omega[17]
  t62 = t42 ** 2
  t64 = t14 * r0 + t62 * r1
  t65 = t60 * t64
  t67 = 0.2e1 * t65 * t31
  t69 = 0.2e1 * t65 * t37
  t71 = t34 * t30
  t83 = params.omega[4]
  t84 = r0 ** (0.1e1 / 0.12e2)
  t85 = t84 ** 2
  t86 = t85 ** 2
  t87 = t86 * t84
  t89 = r1 ** (0.1e1 / 0.12e2)
  t90 = t89 ** 2
  t91 = t90 ** 2
  t92 = t91 * t89
  t95 = t83 * (t87 * r0 + t92 * r1)
  t96 = jnp.sqrt(s0)
  t97 = r0 ** 2
  t101 = 0.1e1 / t28
  t102 = t27 * t101
  t103 = 0.1e1 + t102
  t104 = t103 <= f.p.zeta_threshold
  t105 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t106 = t105 * f.p.zeta_threshold
  t107 = t103 ** (0.1e1 / 0.3e1)
  t109 = f.my_piecewise3(t104, t106, t107 * t103)
  t110 = 2 ** (0.1e1 / 0.3e1)
  t111 = t110 ** 2
  t112 = t109 * t111
  t115 = 0.1e1 / t41
  t116 = t96 * t115
  t117 = t101 - t31
  t120 = f.my_piecewise3(t104, 0, 0.4e1 / 0.3e1 * t107 * t117)
  t124 = jnp.sqrt(s2)
  t125 = 0.1e1 / t43
  t126 = t124 * t125
  t127 = 0.1e1 - t102
  t128 = t127 <= f.p.zeta_threshold
  t129 = t127 ** (0.1e1 / 0.3e1)
  t133 = f.my_piecewise3(t128, 0, -0.4e1 / 0.3e1 * t129 * t117)
  t137 = -t96 / t6 / t97 * t112 / 0.3e1 + t116 * t120 * t111 / 0.4e1 + t126 * t133 * t111 / 0.4e1
  t140 = 0.7e1 / 0.6e1 * t1 * t2 + 0.4e1 / 0.3e1 * t5 * t6 + 0.3e1 / 0.2e1 * t9 * t10 + 0.5e1 / 0.3e1 * t13 * t14 + 0.10833333333333333333333333333333333333333333333333e1 * t17 * t18 + t33 - t39 + t47 - t49 + t57 - t59 + t67 - t69 + 0.7e1 / 0.6e1 * t21 * t2 * t71 + 0.4e1 / 0.3e1 * t40 * t6 * t71 + 0.3e1 / 0.2e1 * t50 * t10 * t71 + 0.5e1 / 0.3e1 * t60 * t14 * t71 + t95 * t137 / 0.2e1
  t144 = f.my_piecewise3(t128, t106, t129 * t127)
  t145 = t144 * t111
  t148 = t116 * t112 / 0.4e1 + t126 * t145 / 0.4e1
  t151 = params.omega[5]
  t152 = t151 * t54
  t158 = params.omega[6]
  t159 = t158 * t64
  t165 = params.omega[7]
  t166 = t2 ** 2
  t167 = t166 ** 2
  t168 = t167 * t2
  t170 = t23 ** 2
  t171 = t170 ** 2
  t172 = t171 * t23
  t174 = t168 * r0 + t172 * r1
  t175 = t165 * t174
  t181 = params.omega[8]
  t182 = t181 * t64
  t187 = t109 ** 2
  t188 = t187 * t110
  t189 = s0 / t14 / t97 / r0 * t188
  t192 = 0.1e1 / t14 / t97
  t193 = s0 * t192
  t194 = t109 * t110
  t196 = t193 * t194 * t120
  t198 = r1 ** 2
  t200 = 0.1e1 / t62 / t198
  t201 = s2 * t200
  t202 = t144 * t110
  t204 = t201 * t202 * t133
  t206 = -t189 / 0.3e1 + t196 / 0.4e1 + t204 / 0.4e1
  t210 = t193 * t188
  t211 = t144 ** 2
  t212 = t211 * t110
  t213 = t201 * t212
  t215 = t210 / 0.8e1 + t213 / 0.8e1
  t218 = params.omega[9]
  t219 = t218 * t174
  t225 = params.omega[10]
  t226 = t97 + t198
  t227 = t225 * t226
  t232 = params.omega[11]
  t233 = t232 * t64
  t238 = s0 + 0.2e1 * s1 + s2
  t239 = t28 ** (0.1e1 / 0.3e1)
  t240 = t239 ** 2
  t244 = 0.8e1 / 0.3e1 * t238 / t240 / t35
  t245 = -0.2e1 / 0.3e1 * t189 + t196 / 0.2e1 + t204 / 0.2e1 + t244
  t251 = 0.1e1 / t240 / t29
  t253 = t210 / 0.4e1 + t213 / 0.4e1 - t238 * t251
  t256 = params.omega[12]
  t257 = t256 * t174
  t262 = params.omega[13]
  t263 = t262 * t226
  t268 = 0.17e2 / 0.24e2 * t83 * t87 * t148 + t152 * t137 / 0.2e1 + 0.3e1 / 0.4e1 * t151 * t10 * t148 + t159 * t137 / 0.2e1 + 0.5e1 / 0.6e1 * t158 * t14 * t148 + t175 * t137 / 0.2e1 + 0.11e2 / 0.12e2 * t165 * t168 * t148 + t182 * t206 / 0.2e1 + 0.5e1 / 0.6e1 * t181 * t14 * t215 + t219 * t206 / 0.2e1 + 0.11e2 / 0.12e2 * t218 * t168 * t215 + t227 * t206 / 0.2e1 + t225 * r0 * t215 + t233 * t245 + 0.5e1 / 0.3e1 * t232 * t14 * t253 + t257 * t245 + 0.11e2 / 0.6e1 * t256 * t168 * t253 + t263 * t245 + 0.2e1 * t262 * r0 * t253
  vrho_0_ = t140 + t268
  t275 = r1 ** 0.833333333333333333333333333333333333333333333333e-1
  t292 = -t101 - t31
  t295 = f.my_piecewise3(t104, 0, 0.4e1 / 0.3e1 * t107 * t292)
  t307 = f.my_piecewise3(t128, 0, -0.4e1 / 0.3e1 * t129 * t292)
  t311 = t116 * t295 * t111 / 0.4e1 - t124 / t42 / t198 * t145 / 0.3e1 + t126 * t307 * t111 / 0.4e1
  t314 = 0.4e1 / 0.3e1 * t5 * t42 + 0.3e1 / 0.2e1 * t9 * t52 + 0.5e1 / 0.3e1 * t13 * t62 + 0.10833333333333333333333333333333333333333333333333e1 * t17 * t275 + 0.7e1 / 0.6e1 * t1 * t23 - t33 - t39 - t47 - t49 - t57 - t59 - t67 - t69 + 0.7e1 / 0.6e1 * t21 * t23 * t71 + 0.4e1 / 0.3e1 * t40 * t42 * t71 + 0.3e1 / 0.2e1 * t50 * t52 * t71 + 0.5e1 / 0.3e1 * t60 * t62 * t71 + t95 * t311 / 0.2e1
  t334 = t193 * t194 * t295
  t340 = s2 / t62 / t198 / r1 * t212
  t343 = t201 * t202 * t307
  t345 = t334 / 0.4e1 - t340 / 0.3e1 + t343 / 0.4e1
  t363 = t334 / 0.2e1 - 0.2e1 / 0.3e1 * t340 + t343 / 0.2e1 + t244
  t376 = 0.17e2 / 0.24e2 * t83 * t92 * t148 + t152 * t311 / 0.2e1 + 0.3e1 / 0.4e1 * t151 * t52 * t148 + t159 * t311 / 0.2e1 + 0.5e1 / 0.6e1 * t158 * t62 * t148 + t175 * t311 / 0.2e1 + 0.11e2 / 0.12e2 * t165 * t172 * t148 + t182 * t345 / 0.2e1 + 0.5e1 / 0.6e1 * t181 * t62 * t215 + t219 * t345 / 0.2e1 + 0.11e2 / 0.12e2 * t218 * t172 * t215 + t227 * t345 / 0.2e1 + t225 * r1 * t215 + t233 * t363 + 0.5e1 / 0.3e1 * t232 * t62 * t253 + t257 * t363 + 0.11e2 / 0.6e1 * t256 * t172 * t253 + t263 * t363 + 0.2e1 * t262 * r1 * t253
  vrho_1_ = t314 + t376
  t377 = 0.1e1 / t96
  t380 = t115 * t109 * t111
  t393 = t192 * t187 * t110
  t401 = t393 / 0.4e1 - t251
  vsigma_0_ = t95 * t377 * t380 / 0.16e2 + t152 * t377 * t380 / 0.16e2 + t159 * t377 * t380 / 0.16e2 + t175 * t377 * t380 / 0.16e2 + t182 * t393 / 0.16e2 + t219 * t393 / 0.16e2 + t227 * t393 / 0.16e2 + t233 * t401 + t257 * t401 + t263 * t401
  vsigma_1_ = -0.2e1 * t233 * t251 - 0.2e1 * t257 * t251 - 0.2e1 * t263 * t251
  t409 = 0.1e1 / t124
  t412 = t125 * t144 * t111
  t425 = t200 * t211 * t110
  t433 = t425 / 0.4e1 - t251
  vsigma_2_ = t95 * t409 * t412 / 0.16e2 + t152 * t409 * t412 / 0.16e2 + t159 * t409 * t412 / 0.16e2 + t175 * t409 * t412 / 0.16e2 + t182 * t425 / 0.16e2 + t219 * t425 / 0.16e2 + t227 * t425 / 0.16e2 + t233 * t433 + t257 * t433 + t263 * t433
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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  params_n = 19

  params_a = [None, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 17 / 12, 9 / 6, 10 / 6, 11 / 6, 10 / 6, 11 / 6, 12 / 6, 10 / 6, 11 / 6, 12 / 6, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 13 / 12.0]

  params_b = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0], dtype=np.float64)

  params_c = np.array([np.nan, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float64)

  params_d = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0], dtype=np.float64)

  XX = lambda z, xs: xs * f.opz_pow_n(z, 4 / 3) * 2 ** (-4 / 3)

  YY = lambda z, xt, xs0, xs1: 2 * (XX(z, xs0) ** 2 + XX(-z, xs1) ** 2) - xt ** 2

  f_th = lambda rs, z, xt, xs0, xs1: jnp.sum(jnp.array([params_omega[i] * (f.n_spin(rs, z) ** params_a[i] + f.n_spin(rs, -z) ** params_a[i]) * z ** (2 * params_b[i]) * 1 / 2 * (XX(z, xs0) ** params_c[i] + XX(-z, xs1) ** params_c[i]) * YY(z, xt, xs0, xs1) ** params_d[i] for i in range(1, params_n + 1)]), axis=0) / f.n_total(rs)

  functional_body = lambda rs, z, xt, xs0, xs1: f_th(rs, z, xt, xs0, xs1)

  t2 = 2 ** (0.1e1 / 0.6e1)
  t3 = t2 ** 2
  t4 = t3 ** 2
  t7 = r0 ** (0.1e1 / 0.6e1)
  t11 = 2 ** (0.1e1 / 0.3e1)
  t12 = t11 ** 2
  t14 = r0 ** (0.1e1 / 0.3e1)
  t18 = jnp.sqrt(0.2e1)
  t20 = jnp.sqrt(r0)
  t25 = t14 ** 2
  t29 = 2 ** (0.1e1 / 0.12e2)
  t30 = t29 ** 2
  t32 = t30 ** 2
  t34 = params.omega[4] * t32 * t30 * t29
  t35 = r0 ** (0.1e1 / 0.12e2)
  t36 = t35 ** 2
  t38 = t36 ** 2
  t39 = t38 ** 2
  t42 = jnp.sqrt(s0)
  t45 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t47 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t45 * f.p.zeta_threshold, 1)
  t52 = params.omega[5] * t18
  t53 = t7 ** 2
  t54 = t53 ** 2
  t55 = t54 * t7
  t56 = 0.1e1 / t55
  t62 = params.omega[6] * t11
  t63 = 0.1e1 / t25
  t69 = params.omega[7] * t2
  t76 = params.omega[8] * t11
  t77 = r0 ** 2
  t80 = t47 ** 2
  t85 = params.omega[9] * t2
  t86 = t55 * r0
  t92 = params.omega[10]
  t93 = t25 * r0
  t100 = params.omega[11] * t11
  t102 = 0.1e1 / t25 / t77
  t103 = s0 * t102
  t105 = t103 * t80 - t103
  t112 = s0 / t25 / t77 / r0
  t115 = -0.8e1 / 0.3e1 * t112 * t80 + 0.8e1 / 0.3e1 * t112
  t120 = params.omega[12] * t2
  t127 = params.omega[13]
  t130 = t127 * t77
  t134 = r0 ** 0.833333333333333333333333333333333333333333333333e-1
  vrho_0_ = 0.7e1 / 0.12e2 * params.omega[0] * t4 * t2 * t7 + 0.2e1 / 0.3e1 * params.omega[1] * t12 * t14 + 0.3e1 / 0.4e1 * params.omega[2] * t18 * t20 + 0.5e1 / 0.6e1 * params.omega[3] * t11 * t25 + t34 / t39 / t36 / t35 * t42 * t47 / 0.48e2 + t52 * t56 * t42 * t47 / 0.24e2 + t62 * t63 * t42 * t47 / 0.12e2 + t69 / t20 * t42 * t47 / 0.8e1 - t76 / t77 * s0 * t80 / 0.8e1 - 0.5e1 / 0.48e2 * t85 / t86 * s0 * t80 - t92 / t93 * s0 * t80 / 0.12e2 + 0.5e1 / 0.6e1 * t100 * t25 * t105 + t100 * t93 * t115 / 0.2e1 + 0.11e2 / 0.12e2 * t120 * t55 * t105 + t120 * t86 * t115 / 0.2e1 + t127 * r0 * t105 + t130 * t115 / 0.2e1 + 0.10225305054051679546954059197231622406748656619503e1 * params.omega[18] * t134
  t137 = 0.1e1 / t42
  t165 = t102 * t80 - t102
  vsigma_0_ = t34 * t35 * t137 * t47 / 0.8e1 + t52 * t7 * t137 * t47 / 0.8e1 + t62 * t14 * t137 * t47 / 0.8e1 + t69 * t20 * t137 * t47 / 0.8e1 + t76 / r0 * t80 / 0.8e1 + t85 * t56 * t80 / 0.8e1 + t92 * t63 * t80 / 0.8e1 + t100 * t93 * t165 / 0.2e1 + t120 * t86 * t165 / 0.2e1 + t130 * t165 / 0.2e1
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t2 = 2 ** (0.1e1 / 0.6e1)
  t3 = t2 ** 2
  t4 = t3 ** 2
  t7 = r0 ** (0.1e1 / 0.6e1)
  t8 = t7 ** 2
  t9 = t8 ** 2
  t10 = t9 * t7
  t11 = 0.1e1 / t10
  t15 = 2 ** (0.1e1 / 0.3e1)
  t16 = t15 ** 2
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t20 = 0.1e1 / t19
  t24 = jnp.sqrt(0.2e1)
  t26 = jnp.sqrt(r0)
  t27 = 0.1e1 / t26
  t32 = 0.1e1 / t18
  t36 = 2 ** (0.1e1 / 0.12e2)
  t37 = t36 ** 2
  t39 = t37 ** 2
  t41 = params.omega[4] * t39 * t37 * t36
  t42 = r0 ** (0.1e1 / 0.12e2)
  t43 = t42 ** 2
  t45 = t43 ** 2
  t46 = t45 ** 2
  t47 = t46 * t43 * t42
  t50 = jnp.sqrt(s0)
  t53 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t55 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t53 * f.p.zeta_threshold, 1)
  t60 = params.omega[5] * t24
  t61 = t10 * r0
  t62 = 0.1e1 / t61
  t68 = params.omega[6] * t15
  t69 = t19 * r0
  t70 = 0.1e1 / t69
  t76 = params.omega[7] * t2
  t84 = params.omega[8] * t15
  t85 = r0 ** 2
  t86 = t85 * r0
  t89 = t55 ** 2
  t94 = params.omega[9] * t2
  t102 = params.omega[10]
  t104 = 0.1e1 / t19 / t85
  t110 = params.omega[11] * t15
  t111 = s0 * t104
  t113 = t111 * t89 - t111
  t118 = 0.1e1 / t19 / t86
  t119 = s0 * t118
  t122 = -0.8e1 / 0.3e1 * t119 * t89 + 0.8e1 / 0.3e1 * t119
  t126 = t85 ** 2
  t129 = s0 / t19 / t126
  t132 = 0.88e2 / 0.9e1 * t129 * t89 - 0.88e2 / 0.9e1 * t129
  t137 = params.omega[12] * t2
  t148 = params.omega[13]
  t150 = t148 * r0
  t153 = t148 * t85
  t157 = r0 ** (-0.9166666666666666666666666666666666666666666666667e0)
  t160 = 0.5e1 / 0.36e2 * t102 * t104 * s0 * t89 + 0.5e1 / 0.9e1 * t110 * t32 * t113 + 0.5e1 / 0.3e1 * t110 * t19 * t122 + t110 * t69 * t132 / 0.2e1 + 0.55e2 / 0.72e2 * t137 / t7 * t113 + 0.11e2 / 0.6e1 * t137 * t10 * t122 + t137 * t61 * t132 / 0.2e1 + t148 * t113 + 0.2e1 * t150 * t122 + t153 * t132 / 0.2e1 + 0.85210875450430662891283826643596853389572138495824e-1 * params.omega[18] * t157
  v2rho2_0_ = 0.7e1 / 0.72e2 * params.omega[0] * t4 * t2 * t11 + 0.2e1 / 0.9e1 * params.omega[1] * t16 * t20 + 0.3e1 / 0.8e1 * params.omega[2] * t24 * t27 + 0.5e1 / 0.9e1 * params.omega[3] * t15 * t32 - 0.11e2 / 0.576e3 * t41 / t47 / r0 * t50 * t55 - 0.5e1 / 0.144e3 * t60 * t62 * t50 * t55 - t68 * t70 * t50 * t55 / 0.18e2 - t76 / t26 / r0 * t50 * t55 / 0.16e2 + t84 / t86 * s0 * t89 / 0.4e1 + 0.55e2 / 0.288e3 * t94 / t10 / t85 * s0 * t89 + t160
  t162 = 0.1e1 / t50
  t190 = t104 * t89 - t104
  t196 = -0.8e1 / 0.3e1 * t118 * t89 + 0.8e1 / 0.3e1 * t118
  v2rhosigma_0_ = t41 / t47 * t162 * t55 / 0.96e2 + t60 * t11 * t162 * t55 / 0.48e2 + t68 * t20 * t162 * t55 / 0.24e2 + t76 * t27 * t162 * t55 / 0.16e2 - t84 / t85 * t89 / 0.8e1 - 0.5e1 / 0.48e2 * t94 * t62 * t89 - t102 * t70 * t89 / 0.12e2 + 0.5e1 / 0.6e1 * t110 * t19 * t190 + t110 * t69 * t196 / 0.2e1 + 0.11e2 / 0.12e2 * t137 * t10 * t190 + t137 * t61 * t196 / 0.2e1 + t150 * t190 + t153 * t196 / 0.2e1
  t210 = 0.1e1 / t50 / s0
  v2sigma2_0_ = -t68 * t18 * t210 * t55 / 0.16e2 - t76 * t26 * t210 * t55 / 0.16e2 - t41 * t42 * t210 * t55 / 0.16e2 - t60 * t7 * t210 * t55 / 0.16e2
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 ** (-0.19166666666666666666666666666666666666666666666667e1)
  t5 = params.omega[13]
  t6 = r0 ** 2
  t7 = t6 * r0
  t8 = r0 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t11 = 0.1e1 / t9 / t7
  t12 = s0 * t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t16 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t14 * f.p.zeta_threshold, 1)
  t17 = t16 ** 2
  t20 = -0.8e1 / 0.3e1 * t12 * t17 + 0.8e1 / 0.3e1 * t12
  t24 = 2 ** (0.1e1 / 0.6e1)
  t25 = t24 ** 2
  t26 = t25 ** 2
  t29 = r0 ** (0.1e1 / 0.6e1)
  t30 = t29 ** 2
  t31 = t30 ** 2
  t32 = t31 * t29
  t33 = t32 * r0
  t38 = t6 ** 2
  t41 = s0 / t9 / t38
  t44 = 0.88e2 / 0.9e1 * t41 * t17 - 0.88e2 / 0.9e1 * t41
  t51 = s0 / t9 / t38 / r0
  t54 = -0.1232e4 / 0.27e2 * t51 * t17 + 0.1232e4 / 0.27e2 * t51
  t58 = 2 ** (0.1e1 / 0.12e2)
  t59 = t58 ** 2
  t61 = t59 ** 2
  t64 = r0 ** (0.1e1 / 0.12e2)
  t65 = t64 ** 2
  t67 = t65 ** 2
  t68 = t67 ** 2
  t72 = jnp.sqrt(s0)
  t78 = jnp.sqrt(0.2e1)
  t87 = 2 ** (0.1e1 / 0.3e1)
  t90 = 0.1e1 / t9 / t6
  t97 = jnp.sqrt(r0)
  t119 = -0.78109969162894774317010174423297115607107793621175e-1 * params.omega[18] * t2 + 0.3e1 * t5 * t20 - 0.35e2 / 0.432e3 * params.omega[0] * t26 * t24 / t33 + 0.3e1 * t5 * r0 * t44 + t5 * t6 * t54 / 0.2e1 + 0.253e3 / 0.6912e4 * params.omega[4] * t61 * t59 * t58 / t68 / t65 / t64 / t6 * t72 * t16 + 0.55e2 / 0.864e3 * params.omega[5] * t78 / t32 / t6 * t72 * t16 + 0.5e1 / 0.54e2 * params.omega[6] * t87 * t90 * t72 * t16 + 0.3e1 / 0.32e2 * params.omega[7] * t24 / t97 / t6 * t72 * t16 - 0.3e1 / 0.4e1 * params.omega[8] * t87 / t38 * s0 * t17 - 0.935e3 / 0.1728e4 * params.omega[9] * t24 / t32 / t7 * s0 * t17
  t121 = params.omega[11] * t87
  t123 = 0.1e1 / t8 / r0
  t124 = s0 * t90
  t126 = t124 * t17 - t124
  t131 = params.omega[12] * t24
  t149 = t9 * r0
  t164 = t87 ** 2
  t179 = -0.5e1 / 0.27e2 * t121 * t123 * t126 - 0.55e2 / 0.432e3 * t131 / t29 / r0 * t126 - 0.10e2 / 0.27e2 * params.omega[10] * t11 * s0 * t17 + 0.5e1 / 0.3e1 * t121 / t8 * t20 + 0.5e1 / 0.2e1 * t121 * t9 * t44 + t121 * t149 * t54 / 0.2e1 + 0.55e2 / 0.24e2 * t131 / t29 * t20 + 0.11e2 / 0.4e1 * t131 * t32 * t44 + t131 * t33 * t54 / 0.2e1 - 0.4e1 / 0.27e2 * params.omega[1] * t164 / t149 - 0.3e1 / 0.16e2 * params.omega[2] * t78 / t97 / r0 - 0.5e1 / 0.27e2 * params.omega[3] * t87 * t123
  v3rho3_0_ = t119 + t179

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = 2 ** (0.1e1 / 0.3e1)
  t4 = r0 ** 2
  t5 = t4 ** 2
  t6 = t5 * r0
  t10 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t12 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t10 * f.p.zeta_threshold, 1)
  t13 = t12 ** 2
  t18 = 2 ** (0.1e1 / 0.6e1)
  t20 = r0 ** (0.1e1 / 0.6e1)
  t21 = t20 ** 2
  t22 = t21 ** 2
  t23 = t22 * t20
  t31 = 2 ** (0.1e1 / 0.12e2)
  t32 = t31 ** 2
  t34 = t32 ** 2
  t37 = t4 * r0
  t38 = r0 ** (0.1e1 / 0.12e2)
  t39 = t38 ** 2
  t41 = t39 ** 2
  t42 = t41 ** 2
  t46 = jnp.sqrt(s0)
  t52 = jnp.sqrt(0.2e1)
  t62 = r0 ** (0.1e1 / 0.3e1)
  t63 = t62 ** 2
  t65 = 0.1e1 / t63 / t37
  t72 = jnp.sqrt(r0)
  t80 = r0 ** (-0.29166666666666666666666666666666666666666666666667e1)
  t83 = params.omega[13]
  t85 = 0.1e1 / t63 / t5
  t86 = s0 * t85
  t89 = 0.88e2 / 0.9e1 * t86 * t13 - 0.88e2 / 0.9e1 * t86
  t93 = params.omega[11] * t2
  t95 = 0.1e1 / t62 / t4
  t97 = 0.1e1 / t63 / t4
  t98 = s0 * t97
  t100 = t98 * t13 - t98
  t105 = params.omega[12] * t18
  t113 = s0 * t65
  t116 = -0.8e1 / 0.3e1 * t113 * t13 + 0.8e1 / 0.3e1 * t113
  t125 = 0.3e1 * params.omega[8] * t2 / t6 * s0 * t13 + 0.21505e5 / 0.10368e5 * params.omega[9] * t18 / t23 / t5 * s0 * t13 - 0.8855e4 / 0.82944e5 * params.omega[4] * t34 * t32 * t31 / t42 / t39 / t38 / t37 * t46 * t12 - 0.935e3 / 0.5184e4 * params.omega[5] * t52 / t23 / t37 * t46 * t12 - 0.20e2 / 0.81e2 * params.omega[6] * t2 * t65 * t46 * t12 - 0.15e2 / 0.64e2 * params.omega[7] * t18 / t72 / t37 * t46 * t12 + 0.14971077422888165077426950097798613824695660444059e0 * params.omega[18] * t80 + 0.6e1 * t83 * t89 + 0.20e2 / 0.81e2 * t93 * t95 * t100 + 0.385e3 / 0.2592e4 * t105 / t20 / t4 * t100 - 0.20e2 / 0.27e2 * t93 / t62 / r0 * t116 - 0.55e2 / 0.108e3 * t105 / t20 / r0 * t116
  t137 = s0 / t63 / t6
  t140 = -0.1232e4 / 0.27e2 * t137 * t13 + 0.1232e4 / 0.27e2 * t137
  t148 = s0 / t63 / t5 / t4
  t151 = 0.20944e5 / 0.81e2 * t148 * t13 - 0.20944e5 / 0.81e2 * t148
  t180 = t18 ** 2
  t181 = t180 ** 2
  t192 = t2 ** 2
  t196 = 0.110e3 / 0.81e2 * params.omega[10] * t85 * s0 * t13 + 0.10e2 / 0.3e1 * t93 / t62 * t89 + 0.10e2 / 0.3e1 * t93 * t63 * t140 + t93 * t63 * r0 * t151 / 0.2e1 + 0.55e2 / 0.12e2 * t105 / t20 * t89 + 0.11e2 / 0.3e1 * t105 * t23 * t140 + t105 * t23 * r0 * t151 / 0.2e1 + 0.20e2 / 0.81e2 * params.omega[3] * t2 * t95 + 0.9e1 / 0.32e2 * params.omega[2] * t52 / t72 / t4 + t83 * t4 * t151 / 0.2e1 + 0.385e3 / 0.2592e4 * params.omega[0] * t181 * t18 / t23 / t4 + 0.4e1 * t83 * r0 * t140 + 0.20e2 / 0.81e2 * params.omega[1] * t192 * t97
  v4rho4_0_ = t125 + t196

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = params.omega[10]
  t2 = t1 * r0
  t3 = r0 ** 2
  t4 = t3 * r0
  t5 = r0 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t9 = s0 / t6 / t4
  t10 = r0 - r1
  t11 = r0 + r1
  t12 = 0.1e1 / t11
  t13 = t10 * t12
  t14 = 0.1e1 + t13
  t15 = t14 <= f.p.zeta_threshold
  t16 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t17 = t16 * f.p.zeta_threshold
  t18 = t14 ** (0.1e1 / 0.3e1)
  t20 = f.my_piecewise3(t15, t17, t18 * t14)
  t21 = t20 ** 2
  t22 = 2 ** (0.1e1 / 0.3e1)
  t23 = t21 * t22
  t24 = t9 * t23
  t28 = s0 / t6 / t3
  t29 = t20 * t22
  t30 = t11 ** 2
  t31 = 0.1e1 / t30
  t32 = t10 * t31
  t33 = t12 - t32
  t36 = f.my_piecewise3(t15, 0, 0.4e1 / 0.3e1 * t18 * t33)
  t37 = t29 * t36
  t38 = t28 * t37
  t40 = r1 ** 2
  t41 = r1 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t45 = s2 / t42 / t40
  t46 = 0.1e1 - t13
  t47 = t46 <= f.p.zeta_threshold
  t48 = t46 ** (0.1e1 / 0.3e1)
  t50 = f.my_piecewise3(t47, t17, t48 * t46)
  t51 = t50 * t22
  t52 = -t33
  t55 = f.my_piecewise3(t47, 0, 0.4e1 / 0.3e1 * t48 * t52)
  t56 = t51 * t55
  t57 = t45 * t56
  t59 = -t24 / 0.3e1 + t38 / 0.4e1 + t57 / 0.4e1
  t62 = params.omega[11]
  t65 = t6 * r0 + t42 * r1
  t66 = t62 * t65
  t67 = t3 ** 2
  t71 = s0 / t6 / t67 * t23
  t73 = t9 * t37
  t75 = t36 ** 2
  t77 = t28 * t75 * t22
  t79 = t18 ** 2
  t80 = 0.1e1 / t79
  t81 = t33 ** 2
  t84 = t30 * t11
  t85 = 0.1e1 / t84
  t86 = t10 * t85
  t88 = -0.2e1 * t31 + 0.2e1 * t86
  t92 = f.my_piecewise3(t15, 0, 0.4e1 / 0.9e1 * t80 * t81 + 0.4e1 / 0.3e1 * t18 * t88)
  t94 = t28 * t29 * t92
  t96 = t55 ** 2
  t98 = t45 * t96 * t22
  t100 = t48 ** 2
  t101 = 0.1e1 / t100
  t102 = t52 ** 2
  t109 = f.my_piecewise3(t47, 0, 0.4e1 / 0.9e1 * t101 * t102 - 0.4e1 / 0.3e1 * t48 * t88)
  t111 = t45 * t51 * t109
  t114 = s0 + 0.2e1 * s1 + s2
  t115 = t30 ** 2
  t116 = t11 ** (0.1e1 / 0.3e1)
  t117 = t116 ** 2
  t121 = 0.88e2 / 0.9e1 * t114 / t117 / t115
  t122 = 0.22e2 / 0.9e1 * t71 - 0.8e1 / 0.3e1 * t73 + t77 / 0.2e1 + t94 / 0.2e1 + t98 / 0.2e1 + t111 / 0.2e1 - t121
  t124 = t62 * t6
  t131 = 0.8e1 / 0.3e1 * t114 / t117 / t84
  t132 = -0.2e1 / 0.3e1 * t24 + t38 / 0.2e1 + t57 / 0.2e1 + t131
  t135 = params.omega[12]
  t136 = r0 ** (0.1e1 / 0.6e1)
  t137 = t136 ** 2
  t138 = t137 ** 2
  t139 = t138 * t136
  t141 = r1 ** (0.1e1 / 0.6e1)
  t142 = t141 ** 2
  t143 = t142 ** 2
  t144 = t143 * t141
  t146 = t139 * r0 + t144 * r1
  t147 = t135 * t146
  t149 = t135 * t139
  t152 = params.omega[13]
  t153 = t3 + t40
  t154 = t152 * t153
  t156 = t152 * r0
  t159 = params.omega[4]
  t160 = r0 ** (0.1e1 / 0.12e2)
  t161 = t160 ** 2
  t162 = t161 ** 2
  t163 = t162 * t160
  t164 = t159 * t163
  t165 = jnp.sqrt(s0)
  t168 = t165 / t5 / t3
  t169 = t22 ** 2
  t170 = t20 * t169
  t173 = t5 * r0
  t175 = t165 / t173
  t176 = t36 * t169
  t179 = jnp.sqrt(s2)
  t180 = t41 * r1
  t182 = t179 / t180
  t183 = t55 * t169
  t186 = -t168 * t170 / 0.3e1 + t175 * t176 / 0.4e1 + t182 * t183 / 0.4e1
  t190 = r1 ** (0.1e1 / 0.12e2)
  t191 = t190 ** 2
  t192 = t191 ** 2
  t193 = t192 * t190
  t196 = t159 * (t163 * r0 + t193 * r1)
  t210 = 0.7e1 / 0.9e1 * t165 / t5 / t4 * t170 - 0.2e1 / 0.3e1 * t168 * t176 + t175 * t92 * t169 / 0.4e1 + t182 * t109 * t169 / 0.4e1
  t213 = params.omega[5]
  t214 = jnp.sqrt(r0)
  t216 = jnp.sqrt(r1)
  t218 = t214 * r0 + t216 * r1
  t219 = t213 * t218
  t222 = t213 * t214
  t225 = params.omega[6]
  t226 = 0.1e1 / t5
  t229 = t50 * t169
  t232 = t175 * t170 / 0.4e1 + t182 * t229 / 0.4e1
  t235 = params.omega[7]
  t236 = 0.1e1 / t136
  t240 = params.omega[8]
  t242 = t28 * t23
  t243 = t50 ** 2
  t244 = t243 * t22
  t245 = t45 * t244
  t247 = t242 / 0.8e1 + t245 / 0.8e1
  t250 = 0.2e1 * t2 * t59 + t66 * t122 + 0.10e2 / 0.3e1 * t124 * t132 + t147 * t122 + 0.11e2 / 0.3e1 * t149 * t132 + t154 * t122 + 0.4e1 * t156 * t132 + 0.17e2 / 0.12e2 * t164 * t186 + t196 * t210 / 0.2e1 + t219 * t210 / 0.2e1 + 0.3e1 / 0.2e1 * t222 * t186 + 0.5e1 / 0.9e1 * t225 * t226 * t232 + 0.55e2 / 0.72e2 * t235 * t236 * t232 + 0.5e1 / 0.9e1 * t240 * t226 * t247
  t251 = params.omega[9]
  t261 = t242 / 0.4e1 + t245 / 0.4e1 - t114 / t117 / t30
  t264 = params.omega[14]
  t268 = t264 * (t136 * r0 + t141 * r1)
  t270 = 0.2e1 * t268 * t31
  t271 = params.omega[15]
  t273 = t271 * (t173 + t180)
  t275 = 0.2e1 * t273 * t31
  t276 = params.omega[16]
  t277 = t276 * t218
  t279 = 0.2e1 * t277 * t31
  t280 = params.omega[17]
  t281 = t280 * t65
  t283 = 0.2e1 * t281 * t31
  t293 = 0.1e1 / t214
  t297 = t225 * t65
  t300 = t225 * t6
  t303 = t235 * t146
  t306 = t235 * t139
  t309 = t240 * t65
  t316 = 0.11e2 / 0.9e1 * t71 - 0.4e1 / 0.3e1 * t73 + t77 / 0.4e1 + t94 / 0.4e1 + t98 / 0.4e1 + t111 / 0.4e1
  t319 = t240 * t6
  t322 = 0.55e2 / 0.72e2 * t251 * t236 * t247 + 0.10e2 / 0.9e1 * t62 * t226 * t261 + t270 + t275 + t279 + t283 + 0.55e2 / 0.36e2 * t135 * t236 * t261 + 0.85e2 / 0.288e3 * t159 / t162 / t161 / t160 * t232 + 0.3e1 / 0.8e1 * t213 * t293 * t232 + t297 * t210 / 0.2e1 + 0.5e1 / 0.3e1 * t300 * t186 + t303 * t210 / 0.2e1 + 0.11e2 / 0.6e1 * t306 * t186 + t309 * t316 / 0.2e1 + 0.5e1 / 0.3e1 * t319 * t59
  t324 = t251 * t146
  t327 = t251 * t139
  t330 = t1 * t153
  t334 = 0.2e1 * t152 * t261
  t335 = t1 * t247
  t336 = params.omega[18]
  t337 = r0 ** (-0.9166666666666666666666666666666666666666666666667e0)
  t340 = params.omega[3]
  t343 = params.omega[2]
  t346 = params.omega[1]
  t347 = 0.1e1 / t6
  t350 = params.omega[0]
  t351 = 0.1e1 / t139
  t354 = t10 ** 2
  t356 = t354 / t115
  t358 = 0.6e1 * t277 * t356
  t360 = 0.8e1 * t281 * t86
  t362 = 0.6e1 * t281 * t356
  t364 = t354 * t31
  t370 = t324 * t316 / 0.2e1 + 0.11e2 / 0.6e1 * t327 * t59 + t330 * t316 / 0.2e1 + t334 + t335 + 0.90277777777777777777777777777777777777777777777739e-1 * t336 * t337 + 0.10e2 / 0.9e1 * t340 * t226 + 0.3e1 / 0.4e1 * t343 * t293 + 0.4e1 / 0.9e1 * t346 * t347 + 0.7e1 / 0.36e2 * t350 * t351 + t358 - t360 + t362 + 0.7e1 / 0.36e2 * t264 * t351 * t364 + 0.4e1 / 0.9e1 * t271 * t347 * t364
  t378 = 0.8e1 * t268 * t86
  t380 = 0.6e1 * t268 * t356
  t382 = 0.8e1 * t273 * t86
  t384 = 0.6e1 * t273 * t356
  t386 = 0.8e1 * t277 * t86
  t387 = t264 * t136
  t388 = t387 * t32
  t390 = t354 * t85
  t391 = t387 * t390
  t393 = t271 * t5
  t394 = t393 * t32
  t396 = t393 * t390
  t398 = t276 * t214
  t399 = t398 * t32
  t401 = t398 * t390
  t403 = t280 * t6
  t404 = t403 * t32
  t406 = t403 * t390
  t408 = 0.3e1 / 0.4e1 * t276 * t293 * t364 + 0.10e2 / 0.9e1 * t280 * t226 * t364 - t378 + t380 - t382 + t384 - t386 + 0.14e2 / 0.3e1 * t388 - 0.14e2 / 0.3e1 * t391 + 0.16e2 / 0.3e1 * t394 - 0.16e2 / 0.3e1 * t396 + 0.6e1 * t399 - 0.6e1 * t401 + 0.20e2 / 0.3e1 * t404 - 0.20e2 / 0.3e1 * t406
  d11 = t250 + t322 + t370 + t408
  t410 = -t12 - t32
  t413 = f.my_piecewise3(t15, 0, 0.4e1 / 0.3e1 * t18 * t410)
  t414 = t29 * t413
  t415 = t28 * t414
  t417 = t40 * r1
  t420 = s2 / t42 / t417
  t421 = t420 * t244
  t423 = -t410
  t426 = f.my_piecewise3(t47, 0, 0.4e1 / 0.3e1 * t48 * t423)
  t427 = t51 * t426
  t428 = t45 * t427
  t430 = t415 / 0.4e1 - t421 / 0.3e1 + t428 / 0.4e1
  t433 = t251 * t144
  t436 = t9 * t414
  t440 = t28 * t36 * t22 * t413
  t449 = f.my_piecewise3(t15, 0, 0.4e1 / 0.9e1 * t80 * t410 * t33 + 0.8e1 / 0.3e1 * t18 * t10 * t85)
  t451 = t28 * t29 * t449
  t453 = t420 * t56
  t457 = t45 * t55 * t22 * t426
  t466 = f.my_piecewise3(t47, 0, 0.4e1 / 0.9e1 * t101 * t423 * t52 - 0.8e1 / 0.3e1 * t48 * t10 * t85)
  t468 = t45 * t51 * t466
  t470 = -0.2e1 / 0.3e1 * t436 + t440 / 0.4e1 + t451 / 0.4e1 - 0.2e1 / 0.3e1 * t453 + t457 / 0.4e1 + t468 / 0.4e1
  t474 = t1 * r1
  t482 = -0.4e1 / 0.3e1 * t436 + t440 / 0.2e1 + t451 / 0.2e1 - 0.4e1 / 0.3e1 * t453 + t457 / 0.2e1 + t468 / 0.2e1 - t121
  t487 = t415 / 0.2e1 - 0.2e1 / 0.3e1 * t421 + t428 / 0.2e1 + t131
  t490 = t62 * t42
  t496 = t135 * t144
  t502 = 0.11e2 / 0.12e2 * t327 * t430 + 0.11e2 / 0.12e2 * t433 * t59 + t330 * t470 / 0.2e1 + t2 * t430 + t474 * t59 + t66 * t482 + 0.5e1 / 0.3e1 * t124 * t487 + 0.5e1 / 0.3e1 * t490 * t132 + t147 * t482 + 0.11e2 / 0.6e1 * t149 * t487 + 0.11e2 / 0.6e1 * t496 * t132 + t154 * t482 + 0.2e1 * t156 * t487
  t503 = t152 * r1
  t506 = t213 * t216
  t509 = t159 * t193
  t512 = t413 * t169
  t520 = t179 / t41 / t40
  t526 = -t168 * t512 / 0.3e1 + t175 * t449 * t169 / 0.4e1 - t520 * t183 / 0.3e1 + t182 * t466 * t169 / 0.4e1
  t533 = t426 * t169
  t536 = t175 * t512 / 0.4e1 - t520 * t229 / 0.3e1 + t182 * t533 / 0.4e1
  t547 = t225 * t42
  t554 = t235 * t144
  t559 = 0.2e1 * t503 * t132 + 0.3e1 / 0.4e1 * t506 * t186 + 0.17e2 / 0.24e2 * t509 * t186 + t196 * t526 / 0.2e1 + 0.17e2 / 0.24e2 * t164 * t536 + t219 * t526 / 0.2e1 + 0.3e1 / 0.4e1 * t222 * t536 + t297 * t526 / 0.2e1 + 0.5e1 / 0.6e1 * t300 * t536 + 0.5e1 / 0.6e1 * t547 * t186 + t303 * t526 / 0.2e1 + 0.11e2 / 0.12e2 * t306 * t536 + 0.11e2 / 0.12e2 * t554 * t186 + t309 * t470 / 0.2e1
  t563 = t240 * t42
  t568 = t264 * t141
  t569 = t568 * t32
  t571 = t568 * t390
  t573 = t271 * t41
  t574 = t573 * t32
  t576 = t573 * t390
  t578 = t276 * t216
  t579 = t578 * t32
  t581 = t578 * t390
  t583 = 0.5e1 / 0.6e1 * t319 * t430 + 0.5e1 / 0.6e1 * t563 * t59 + t324 * t470 / 0.2e1 - t270 - t275 - t279 - t283 + 0.7e1 / 0.3e1 * t569 - 0.7e1 / 0.3e1 * t571 + 0.8e1 / 0.3e1 * t574 - 0.8e1 / 0.3e1 * t576 + 0.3e1 * t579 - 0.3e1 * t581
  t584 = t280 * t42
  t585 = t584 * t32
  t587 = t584 * t390
  t597 = 0.10e2 / 0.3e1 * t585 - 0.10e2 / 0.3e1 * t587 + t358 + t362 + t380 + t384 - 0.7e1 / 0.3e1 * t388 - 0.7e1 / 0.3e1 * t391 - 0.8e1 / 0.3e1 * t394 - 0.8e1 / 0.3e1 * t396 - 0.3e1 * t399 - 0.3e1 * t401 - 0.10e2 / 0.3e1 * t404 - 0.10e2 / 0.3e1 * t406
  d12 = t502 + t559 + t583 + t597
  t599 = r1 ** (-0.9166666666666666666666666666666666666666666666667e0)
  t602 = 0.1e1 / t41
  t605 = 0.1e1 / t216
  t608 = 0.1e1 / t42
  t611 = 0.1e1 / t144
  t617 = 0.1e1 / t141
  t624 = t413 ** 2
  t626 = t28 * t624 * t22
  t628 = t410 ** 2
  t632 = 0.2e1 * t31 + 0.2e1 * t86
  t636 = f.my_piecewise3(t15, 0, 0.4e1 / 0.9e1 * t80 * t628 + 0.4e1 / 0.3e1 * t18 * t632)
  t638 = t28 * t29 * t636
  t640 = t40 ** 2
  t644 = s2 / t42 / t640 * t244
  t646 = t420 * t427
  t648 = t426 ** 2
  t650 = t45 * t648 * t22
  t652 = t423 ** 2
  t659 = f.my_piecewise3(t47, 0, 0.4e1 / 0.9e1 * t101 * t652 - 0.4e1 / 0.3e1 * t48 * t632)
  t661 = t45 * t51 * t659
  t663 = t626 / 0.4e1 + t638 / 0.4e1 + 0.11e2 / 0.9e1 * t644 - 0.4e1 / 0.3e1 * t646 + t650 / 0.4e1 + t661 / 0.4e1
  t685 = t175 * t636 * t169 / 0.4e1 + 0.7e1 / 0.9e1 * t179 / t41 / t417 * t229 - 0.2e1 / 0.3e1 * t520 * t533 + t182 * t659 * t169 / 0.4e1
  t690 = 0.90277777777777777777777777777777777777777777777739e-1 * t336 * t599 + 0.10e2 / 0.9e1 * t340 * t602 + 0.3e1 / 0.4e1 * t343 * t605 + 0.4e1 / 0.9e1 * t346 * t608 + 0.7e1 / 0.36e2 * t350 * t611 + 0.5e1 / 0.9e1 * t240 * t602 * t247 + 0.55e2 / 0.72e2 * t235 * t617 * t232 + 0.55e2 / 0.36e2 * t135 * t617 * t261 + t330 * t663 / 0.2e1 + t309 * t663 / 0.2e1 + 0.5e1 / 0.3e1 * t563 * t430 + t324 * t663 / 0.2e1 + t303 * t685 / 0.2e1 + 0.11e2 / 0.6e1 * t554 * t536
  t713 = t626 / 0.2e1 + t638 / 0.2e1 + 0.22e2 / 0.9e1 * t644 - 0.8e1 / 0.3e1 * t646 + t650 / 0.2e1 + t661 / 0.2e1 - t121
  t726 = t297 * t685 / 0.2e1 + 0.5e1 / 0.3e1 * t547 * t536 + t196 * t685 / 0.2e1 + 0.17e2 / 0.12e2 * t509 * t536 + t219 * t685 / 0.2e1 + 0.3e1 / 0.2e1 * t506 * t536 + 0.4e1 * t503 * t487 + 0.11e2 / 0.3e1 * t496 * t487 + t154 * t713 + 0.10e2 / 0.3e1 * t490 * t487 + t147 * t713 + 0.2e1 * t474 * t430 + t66 * t713 + 0.11e2 / 0.6e1 * t433 * t430 + 0.5e1 / 0.9e1 * t225 * t602 * t232
  t756 = 0.3e1 / 0.8e1 * t213 * t605 * t232 + 0.85e2 / 0.288e3 * t159 / t192 / t191 / t190 * t232 + 0.10e2 / 0.9e1 * t62 * t602 * t261 + 0.55e2 / 0.72e2 * t251 * t617 * t247 + t270 + t275 + t279 + t283 + t334 + t335 + 0.7e1 / 0.36e2 * t264 * t611 * t364 + 0.4e1 / 0.9e1 * t271 * t608 * t364 + 0.3e1 / 0.4e1 * t276 * t605 * t364 + 0.10e2 / 0.9e1 * t280 * t602 * t364 - 0.14e2 / 0.3e1 * t569
  t764 = -0.14e2 / 0.3e1 * t571 - 0.16e2 / 0.3e1 * t574 - 0.16e2 / 0.3e1 * t576 - 0.6e1 * t579 - 0.6e1 * t581 - 0.20e2 / 0.3e1 * t585 - 0.20e2 / 0.3e1 * t587 + t358 + t360 + t362 + t378 + t380 + t382 + t384 + t386
  d22 = t690 + t726 + t756 + t764
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

  t1 = params.omega[10]
  t2 = r0 ** 2
  t3 = t2 * r0
  t4 = r0 ** (0.1e1 / 0.3e1)
  t5 = t4 ** 2
  t8 = s0 / t5 / t3
  t9 = r0 - r1
  t10 = r0 + r1
  t11 = 0.1e1 / t10
  t12 = t9 * t11
  t13 = 0.1e1 + t12
  t14 = t13 <= f.p.zeta_threshold
  t15 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t16 = t15 * f.p.zeta_threshold
  t17 = t13 ** (0.1e1 / 0.3e1)
  t19 = f.my_piecewise3(t14, t16, t17 * t13)
  t20 = t19 ** 2
  t21 = 2 ** (0.1e1 / 0.3e1)
  t22 = t20 * t21
  t23 = t8 * t22
  t27 = s0 / t5 / t2
  t28 = t19 * t21
  t29 = t10 ** 2
  t30 = 0.1e1 / t29
  t31 = t9 * t30
  t32 = t11 - t31
  t35 = f.my_piecewise3(t14, 0, 0.4e1 / 0.3e1 * t17 * t32)
  t36 = t28 * t35
  t37 = t27 * t36
  t39 = r1 ** 2
  t40 = r1 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t44 = s2 / t41 / t39
  t45 = 0.1e1 - t12
  t46 = t45 <= f.p.zeta_threshold
  t47 = t45 ** (0.1e1 / 0.3e1)
  t49 = f.my_piecewise3(t46, t16, t47 * t45)
  t50 = t49 * t21
  t51 = -t32
  t54 = f.my_piecewise3(t46, 0, 0.4e1 / 0.3e1 * t47 * t51)
  t56 = t44 * t50 * t54
  t58 = -t23 / 0.3e1 + t37 / 0.4e1 + t56 / 0.4e1
  t61 = params.omega[13]
  t66 = s0 + 0.2e1 * s1 + s2
  t67 = t29 * t10
  t68 = t10 ** (0.1e1 / 0.3e1)
  t69 = t68 ** 2
  t74 = -0.2e1 / 0.3e1 * t23 + t37 / 0.2e1 + t56 / 0.2e1 + 0.8e1 / 0.3e1 * t66 / t69 / t67
  t78 = r0 ** (0.1e1 / 0.6e1)
  t79 = t78 ** 2
  t80 = t79 ** 2
  t81 = t80 * t78
  t82 = t81 * r0
  t83 = 0.1e1 / t82
  t87 = t5 * r0
  t88 = 0.1e1 / t87
  t92 = jnp.sqrt(r0)
  t93 = t92 * r0
  t94 = 0.1e1 / t93
  t98 = t4 * r0
  t99 = 0.1e1 / t98
  t103 = r0 ** (-0.19166666666666666666666666666666666666666666666667e1)
  t106 = params.omega[7]
  t107 = r1 ** (0.1e1 / 0.6e1)
  t108 = t107 ** 2
  t109 = t108 ** 2
  t112 = t109 * t107 * r1 + t82
  t114 = jnp.sqrt(s0)
  t115 = t2 ** 2
  t119 = t21 ** 2
  t120 = t19 * t119
  t125 = t114 / t4 / t3
  t126 = t35 * t119
  t131 = t114 / t4 / t2
  t132 = t17 ** 2
  t133 = 0.1e1 / t132
  t134 = t32 ** 2
  t137 = 0.1e1 / t67
  t138 = t9 * t137
  t140 = -0.2e1 * t30 + 0.2e1 * t138
  t144 = f.my_piecewise3(t14, 0, 0.4e1 / 0.9e1 * t133 * t134 + 0.4e1 / 0.3e1 * t17 * t140)
  t145 = t144 * t119
  t147 = t114 * t99
  t156 = t29 ** 2
  t157 = 0.1e1 / t156
  t158 = t9 * t157
  t160 = 0.6e1 * t137 - 0.6e1 * t158
  t164 = f.my_piecewise3(t14, 0, -0.8e1 / 0.27e2 / t132 / t13 * t134 * t32 + 0.4e1 / 0.3e1 * t133 * t32 * t140 + 0.4e1 / 0.3e1 * t17 * t160)
  t168 = jnp.sqrt(s2)
  t169 = t40 * r1
  t171 = t168 / t169
  t172 = t47 ** 2
  t175 = t51 ** 2
  t179 = 0.1e1 / t172
  t181 = -t140
  t188 = f.my_piecewise3(t46, 0, -0.8e1 / 0.27e2 / t172 / t45 * t175 * t51 + 0.4e1 / 0.3e1 * t179 * t51 * t181 - 0.4e1 / 0.3e1 * t47 * t160)
  t192 = -0.70e2 / 0.27e2 * t114 / t4 / t115 * t120 + 0.7e1 / 0.3e1 * t125 * t126 - t131 * t145 + t147 * t164 * t119 / 0.4e1 + t171 * t188 * t119 / 0.4e1
  t207 = f.my_piecewise3(t46, 0, 0.4e1 / 0.9e1 * t179 * t175 + 0.4e1 / 0.3e1 * t47 * t181)
  t211 = 0.7e1 / 0.9e1 * t125 * t120 - 0.2e1 / 0.3e1 * t131 * t126 + t147 * t145 / 0.4e1 + t171 * t207 * t119 / 0.4e1
  t214 = params.omega[17]
  t215 = t214 * t5
  t218 = params.omega[14]
  t219 = t78 * r0
  t222 = t218 * (t107 * r1 + t219)
  t225 = params.omega[15]
  t227 = t225 * (t98 + t169)
  t230 = params.omega[16]
  t231 = jnp.sqrt(r1)
  t233 = t231 * r1 + t93
  t234 = t230 * t233
  t238 = t41 * r1 + t87
  t239 = t214 * t238
  t242 = t218 * t78
  t245 = t225 * t4
  t248 = t230 * t92
  t251 = 0.1e1 / t219
  t257 = t171 * t49 * t119 / 0.4e1 + t147 * t120 / 0.4e1
  t260 = params.omega[6]
  t264 = 0.3e1 * t1 * t58 + 0.6e1 * t61 * t74 - 0.35e2 / 0.216e3 * params.omega[0] * t83 - 0.8e1 / 0.27e2 * params.omega[1] * t88 - 0.3e1 / 0.8e1 * params.omega[2] * t94 - 0.10e2 / 0.27e2 * params.omega[3] * t99 - 0.82754629629629629629629629629629629629629629629597e-1 * params.omega[18] * t103 + t106 * t112 * t192 / 0.2e1 + 0.11e2 / 0.4e1 * t106 * t81 * t211 + 0.10e2 * t215 * t30 - 0.12e2 * t222 * t137 - 0.12e2 * t227 * t137 - 0.12e2 * t234 * t137 - 0.12e2 * t239 * t137 + 0.7e1 * t242 * t30 + 0.8e1 * t245 * t30 + 0.9e1 * t248 * t30 - 0.55e2 / 0.432e3 * t106 * t251 * t257 - 0.5e1 / 0.27e2 * t260 * t99 * t257
  t265 = params.omega[8]
  t267 = t27 * t22
  t268 = t49 ** 2
  t270 = t44 * t268 * t21
  t272 = t267 / 0.8e1 + t270 / 0.8e1
  t275 = params.omega[9]
  t279 = params.omega[11]
  t286 = t267 / 0.4e1 + t270 / 0.4e1 - t66 / t69 / t29
  t289 = params.omega[12]
  t293 = 0.1e1 / t78
  t302 = -t131 * t120 / 0.3e1 + t147 * t126 / 0.4e1 + t171 * t54 * t119 / 0.4e1
  t305 = 0.1e1 / t4
  t315 = params.omega[4]
  t316 = r0 ** (0.1e1 / 0.12e2)
  t317 = t316 ** 2
  t319 = t317 ** 2
  t320 = t319 * t317 * t316
  t326 = params.omega[5]
  t338 = s0 / t5 / t115 / r0 * t22
  t342 = s0 / t5 / t115
  t343 = t342 * t36
  t345 = t35 ** 2
  t346 = t345 * t21
  t347 = t8 * t346
  t349 = t28 * t144
  t350 = t8 * t349
  t354 = t27 * t35 * t21 * t144
  t357 = t27 * t28 * t164
  t361 = t44 * t54 * t21 * t207
  t364 = t44 * t50 * t188
  t366 = -0.154e3 / 0.27e2 * t338 + 0.22e2 / 0.3e1 * t343 - 0.2e1 * t347 - 0.2e1 * t350 + 0.3e1 / 0.4e1 * t354 + t357 / 0.4e1 + 0.3e1 / 0.4e1 * t361 + t364 / 0.4e1
  t370 = t342 * t22
  t372 = t8 * t36
  t374 = t27 * t346
  t376 = t27 * t349
  t378 = t54 ** 2
  t380 = t44 * t378 * t21
  t383 = t44 * t50 * t207
  t385 = 0.11e2 / 0.9e1 * t370 - 0.4e1 / 0.3e1 * t372 + t374 / 0.4e1 + t376 / 0.4e1 + t380 / 0.4e1 + t383 / 0.4e1
  t394 = t2 + t39
  t410 = t156 * t10
  t415 = -0.308e3 / 0.27e2 * t338 + 0.44e2 / 0.3e1 * t343 - 0.4e1 * t347 - 0.4e1 * t350 + 0.3e1 / 0.2e1 * t354 + t357 / 0.2e1 + 0.3e1 / 0.2e1 * t361 + t364 / 0.2e1 + 0.1232e4 / 0.27e2 * t66 / t69 / t410
  t428 = 0.22e2 / 0.9e1 * t370 - 0.8e1 / 0.3e1 * t372 + t374 / 0.2e1 + t376 / 0.2e1 + t380 / 0.2e1 + t383 / 0.2e1 - 0.88e2 / 0.9e1 * t66 / t69 / t156
  t433 = -0.5e1 / 0.27e2 * t265 * t99 * t272 - 0.55e2 / 0.432e3 * t275 * t251 * t272 - 0.10e2 / 0.27e2 * t279 * t99 * t286 - 0.55e2 / 0.216e3 * t289 * t251 * t286 + 0.55e2 / 0.24e2 * t106 * t293 * t302 + 0.5e1 / 0.3e1 * t260 * t305 * t302 + 0.5e1 / 0.3e1 * t265 * t305 * t58 + 0.55e2 / 0.24e2 * t275 * t293 * t58 - 0.595e3 / 0.3456e4 * t315 / t320 / r0 * t257 - 0.3e1 / 0.16e2 * t326 * t94 * t257 + t260 * t238 * t192 / 0.2e1 + t265 * t238 * t366 / 0.2e1 + 0.5e1 / 0.2e1 * t265 * t5 * t385 + t275 * t112 * t366 / 0.2e1 + 0.11e2 / 0.4e1 * t275 * t81 * t385 + t1 * t394 * t366 / 0.2e1 + 0.3e1 * t1 * r0 * t385 + t279 * t238 * t415 + 0.5e1 * t279 * t5 * t428 + t289 * t112 * t415
  t443 = t319 * t316
  t445 = r1 ** (0.1e1 / 0.12e2)
  t446 = t445 ** 2
  t447 = t446 ** 2
  t470 = 0.1e1 / t92
  t481 = t225 / t5
  t482 = t9 ** 2
  t483 = t482 * t137
  t487 = t482 * t30
  t490 = t230 * t470
  t502 = t482 * t157
  t505 = 0.11e2 / 0.2e1 * t289 * t81 * t428 + t61 * t394 * t415 + 0.6e1 * t61 * r0 * t428 + t315 * (t447 * t445 * r1 + t443 * r0) * t192 / 0.2e1 + 0.17e2 / 0.8e1 * t315 * t443 * t211 + 0.9e1 / 0.4e1 * t326 * t92 * t211 + 0.10e2 / 0.3e1 * t279 * t305 * t74 + 0.55e2 / 0.12e2 * t289 * t293 * t74 + 0.85e2 / 0.96e2 * t315 / t320 * t302 + 0.9e1 / 0.8e1 * t326 * t470 * t302 + 0.5e1 / 0.2e1 * t260 * t5 * t211 + t326 * t233 * t192 / 0.2e1 - 0.8e1 / 0.3e1 * t481 * t483 - 0.3e1 / 0.8e1 * t230 * t94 * t487 + 0.9e1 / 0.2e1 * t490 * t31 - 0.9e1 / 0.2e1 * t490 * t483 - 0.10e2 / 0.27e2 * t214 * t99 * t487 + 0.36e2 * t222 * t158 - 0.28e2 * t242 * t138 + 0.21e2 * t242 * t502
  t515 = t482 / t410
  t526 = t214 * t305
  t543 = t218 / t81
  t553 = -0.32e2 * t245 * t138 + 0.24e2 * t245 * t502 - 0.36e2 * t248 * t138 + 0.27e2 * t248 * t502 - 0.24e2 * t222 * t515 + 0.36e2 * t227 * t158 - 0.24e2 * t227 * t515 + 0.36e2 * t234 * t158 - 0.24e2 * t234 * t515 + 0.20e2 / 0.3e1 * t526 * t31 - 0.40e2 * t215 * t138 - 0.20e2 / 0.3e1 * t526 * t483 + 0.30e2 * t215 * t502 + 0.36e2 * t239 * t158 - 0.24e2 * t239 * t515 - 0.35e2 / 0.216e3 * t218 * t83 * t487 + 0.7e1 / 0.6e1 * t543 * t31 - 0.7e1 / 0.6e1 * t543 * t483 - 0.8e1 / 0.27e2 * t225 * t88 * t487 + 0.8e1 / 0.3e1 * t481 * t31
  d111 = t264 + t433 + t505 + t553

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

  t1 = params.omega[13]
  t2 = r0 ** 2
  t3 = t2 ** 2
  t4 = r0 ** (0.1e1 / 0.3e1)
  t5 = t4 ** 2
  t8 = s0 / t5 / t3
  t9 = r0 - r1
  t10 = r0 + r1
  t11 = 0.1e1 / t10
  t12 = t9 * t11
  t13 = 0.1e1 + t12
  t14 = t13 <= f.p.zeta_threshold
  t15 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t16 = t15 * f.p.zeta_threshold
  t17 = t13 ** (0.1e1 / 0.3e1)
  t19 = f.my_piecewise3(t14, t16, t17 * t13)
  t20 = t19 ** 2
  t21 = 2 ** (0.1e1 / 0.3e1)
  t22 = t20 * t21
  t23 = t8 * t22
  t25 = t2 * r0
  t28 = s0 / t5 / t25
  t29 = t19 * t21
  t30 = t10 ** 2
  t31 = 0.1e1 / t30
  t32 = t9 * t31
  t33 = t11 - t32
  t36 = f.my_piecewise3(t14, 0, 0.4e1 / 0.3e1 * t17 * t33)
  t37 = t29 * t36
  t38 = t28 * t37
  t41 = 0.1e1 / t5 / t2
  t42 = s0 * t41
  t43 = t36 ** 2
  t44 = t43 * t21
  t45 = t42 * t44
  t47 = t17 ** 2
  t48 = 0.1e1 / t47
  t49 = t33 ** 2
  t52 = t30 * t10
  t53 = 0.1e1 / t52
  t54 = t9 * t53
  t56 = -0.2e1 * t31 + 0.2e1 * t54
  t60 = f.my_piecewise3(t14, 0, 0.4e1 / 0.9e1 * t48 * t49 + 0.4e1 / 0.3e1 * t17 * t56)
  t61 = t29 * t60
  t62 = t42 * t61
  t64 = r1 ** 2
  t65 = r1 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t69 = s2 / t66 / t64
  t70 = 0.1e1 - t12
  t71 = t70 <= f.p.zeta_threshold
  t72 = t70 ** (0.1e1 / 0.3e1)
  t73 = -t33
  t76 = f.my_piecewise3(t71, 0, 0.4e1 / 0.3e1 * t72 * t73)
  t77 = t76 ** 2
  t79 = t69 * t77 * t21
  t82 = f.my_piecewise3(t71, t16, t72 * t70)
  t83 = t82 * t21
  t84 = t72 ** 2
  t85 = 0.1e1 / t84
  t86 = t73 ** 2
  t89 = -t56
  t93 = f.my_piecewise3(t71, 0, 0.4e1 / 0.9e1 * t85 * t86 + 0.4e1 / 0.3e1 * t72 * t89)
  t95 = t69 * t83 * t93
  t98 = s0 + 0.2e1 * s1 + s2
  t99 = t30 ** 2
  t100 = t10 ** (0.1e1 / 0.3e1)
  t101 = t100 ** 2
  t106 = 0.22e2 / 0.9e1 * t23 - 0.8e1 / 0.3e1 * t38 + t45 / 0.2e1 + t62 / 0.2e1 + t79 / 0.2e1 + t95 / 0.2e1 - 0.88e2 / 0.9e1 * t98 / t101 / t99
  t110 = jnp.sqrt(r0)
  t112 = 0.1e1 / t110 / t2
  t119 = r0 ** (0.1e1 / 0.6e1)
  t120 = t119 ** 2
  t121 = t120 ** 2
  t122 = t121 * t119
  t124 = 0.1e1 / t122 / t2
  t128 = r0 ** (-0.29166666666666666666666666666666666666666666666667e1)
  t133 = 0.1e1 / t4 / t2
  t136 = params.omega[10]
  t143 = 0.11e2 / 0.9e1 * t23 - 0.4e1 / 0.3e1 * t38 + t45 / 0.4e1 + t62 / 0.4e1 + t79 / 0.4e1 + t95 / 0.4e1
  t146 = params.omega[16]
  t147 = 0.1e1 / t110
  t148 = t146 * t147
  t151 = params.omega[14]
  t152 = t119 * r0
  t153 = r1 ** (0.1e1 / 0.6e1)
  t156 = t151 * (t153 * r1 + t152)
  t157 = t99 * t10
  t158 = 0.1e1 / t157
  t159 = t9 * t158
  t162 = t9 ** 2
  t163 = t99 * t30
  t165 = t162 / t163
  t168 = params.omega[15]
  t169 = t4 * r0
  t170 = t65 * r1
  t172 = t168 * (t169 + t170)
  t175 = t151 * t119
  t176 = 0.1e1 / t99
  t177 = t9 * t176
  t180 = 0.12e2 * t1 * t106 + 0.9e1 / 0.16e2 * params.omega[2] * t112 + 0.40e2 / 0.81e2 * params.omega[1] * t41 + 0.385e3 / 0.1296e4 * params.omega[0] * t124 + 0.15861304012345679012345679012345679012345679012340e0 * params.omega[18] * t128 + 0.40e2 / 0.81e2 * params.omega[3] * t133 + 0.6e1 * t136 * t143 - 0.36e2 * t148 * t54 - 0.192e3 * t156 * t159 + 0.120e3 * t156 * t165 - 0.192e3 * t172 * t159 + 0.168e3 * t175 * t177
  t181 = t162 * t158
  t184 = t168 * t4
  t189 = t146 * t110
  t194 = t110 * r0
  t195 = jnp.sqrt(r1)
  t197 = t195 * r1 + t194
  t198 = t146 * t197
  t201 = params.omega[17]
  t202 = 0.1e1 / t169
  t203 = t201 * t202
  t206 = 0.1e1 / t4
  t207 = t201 * t206
  t210 = t201 * t5
  t213 = t162 * t53
  t216 = t162 * t176
  t221 = -0.112e3 * t175 * t181 + 0.192e3 * t184 * t177 - 0.128e3 * t184 * t181 + 0.216e3 * t189 * t177 - 0.144e3 * t189 * t181 + 0.120e3 * t198 * t165 - 0.80e2 / 0.27e2 * t203 * t32 - 0.160e3 / 0.3e1 * t207 * t54 + 0.240e3 * t210 * t177 + 0.80e2 / 0.27e2 * t203 * t213 + 0.40e2 * t207 * t216 - 0.160e3 * t210 * t181
  t223 = t5 * r0
  t225 = t66 * r1 + t223
  t226 = t201 * t225
  t232 = t162 * t31
  t235 = t122 * r0
  t237 = t151 / t235
  t243 = t151 / t122
  t252 = t168 / t223
  t258 = t168 / t5
  t263 = -0.192e3 * t226 * t159 + 0.120e3 * t226 * t165 + 0.385e3 / 0.1296e4 * t151 * t124 * t232 - 0.35e2 / 0.27e2 * t237 * t32 + 0.35e2 / 0.27e2 * t237 * t213 - 0.28e2 / 0.3e1 * t243 * t54 + 0.7e1 * t243 * t216 + 0.40e2 / 0.81e2 * t168 * t41 * t232 - 0.64e2 / 0.27e2 * t252 * t32 + 0.64e2 / 0.27e2 * t252 * t213 - 0.64e2 / 0.3e1 * t258 * t54 + 0.16e2 * t258 * t216
  t267 = 0.1e1 / t194
  t268 = t146 * t267
  t282 = params.omega[4]
  t283 = r0 ** (0.1e1 / 0.12e2)
  t284 = t283 ** 2
  t285 = t284 ** 2
  t286 = t285 * t283
  t288 = jnp.sqrt(s0)
  t291 = t288 / t4 / t3
  t292 = t21 ** 2
  t293 = t19 * t292
  t298 = t288 / t4 / t25
  t299 = t36 * t292
  t302 = t288 * t133
  t303 = t60 * t292
  t305 = t288 * t202
  t307 = 0.1e1 / t47 / t13
  t311 = t48 * t33
  t315 = 0.6e1 * t53 - 0.6e1 * t177
  t319 = f.my_piecewise3(t14, 0, -0.8e1 / 0.27e2 * t307 * t49 * t33 + 0.4e1 / 0.3e1 * t311 * t56 + 0.4e1 / 0.3e1 * t17 * t315)
  t320 = t319 * t292
  t323 = jnp.sqrt(s2)
  t325 = t323 / t170
  t327 = 0.1e1 / t84 / t70
  t331 = t85 * t73
  t334 = -t315
  t338 = f.my_piecewise3(t71, 0, -0.8e1 / 0.27e2 * t327 * t86 * t73 + 0.4e1 / 0.3e1 * t331 * t89 + 0.4e1 / 0.3e1 * t72 * t334)
  t342 = -0.70e2 / 0.27e2 * t291 * t293 + 0.7e1 / 0.3e1 * t298 * t299 - t302 * t303 + t305 * t320 / 0.4e1 + t325 * t338 * t292 / 0.4e1
  t346 = r1 ** (0.1e1 / 0.12e2)
  t347 = t346 ** 2
  t348 = t347 ** 2
  t353 = t3 * r0
  t365 = t13 ** 2
  t368 = t49 ** 2
  t374 = t56 ** 2
  t380 = -0.24e2 * t176 + 0.24e2 * t159
  t384 = f.my_piecewise3(t14, 0, 0.40e2 / 0.81e2 / t47 / t365 * t368 - 0.16e2 / 0.9e1 * t307 * t49 * t56 + 0.4e1 / 0.3e1 * t48 * t374 + 0.16e2 / 0.9e1 * t311 * t315 + 0.4e1 / 0.3e1 * t17 * t380)
  t388 = t70 ** 2
  t391 = t86 ** 2
  t397 = t89 ** 2
  t406 = f.my_piecewise3(t71, 0, 0.40e2 / 0.81e2 / t84 / t388 * t391 - 0.16e2 / 0.9e1 * t327 * t86 * t89 + 0.4e1 / 0.3e1 * t85 * t397 + 0.16e2 / 0.9e1 * t331 * t334 - 0.4e1 / 0.3e1 * t72 * t380)
  t410 = 0.910e3 / 0.81e2 * t288 / t4 / t353 * t293 - 0.280e3 / 0.27e2 * t291 * t299 + 0.14e2 / 0.3e1 * t298 * t303 - 0.4e1 / 0.3e1 * t302 * t320 + t305 * t384 * t292 / 0.4e1 + t325 * t406 * t292 / 0.4e1
  t416 = s0 / t5 / t353
  t417 = t416 * t22
  t419 = t8 * t37
  t421 = t28 * t44
  t423 = t28 * t61
  t425 = t36 * t21
  t426 = t425 * t60
  t427 = t42 * t426
  t429 = t29 * t319
  t430 = t42 * t429
  t432 = t76 * t21
  t434 = t69 * t432 * t93
  t437 = t69 * t83 * t338
  t443 = -0.308e3 / 0.27e2 * t417 + 0.44e2 / 0.3e1 * t419 - 0.4e1 * t421 - 0.4e1 * t423 + 0.3e1 / 0.2e1 * t427 + t430 / 0.2e1 + 0.3e1 / 0.2e1 * t434 + t437 / 0.2e1 + 0.1232e4 / 0.27e2 * t98 / t101 / t157
  t446 = t2 + t64
  t452 = s0 / t5 / t3 / t2 * t22
  t454 = t416 * t37
  t456 = t8 * t44
  t458 = t8 * t61
  t460 = t28 * t426
  t462 = t28 * t429
  t464 = t60 ** 2
  t466 = t42 * t464 * t21
  t469 = t42 * t425 * t319
  t472 = t42 * t29 * t384
  t474 = t93 ** 2
  t476 = t69 * t474 * t21
  t479 = t69 * t432 * t338
  t482 = t69 * t83 * t406
  t488 = 0.5236e4 / 0.81e2 * t452 - 0.2464e4 / 0.27e2 * t454 + 0.88e2 / 0.3e1 * t456 + 0.88e2 / 0.3e1 * t458 - 0.16e2 * t460 - 0.16e2 / 0.3e1 * t462 + 0.3e1 / 0.2e1 * t466 + 0.2e1 * t469 + t472 / 0.2e1 + 0.3e1 / 0.2e1 * t476 + 0.2e1 * t479 + t482 / 0.2e1 - 0.20944e5 / 0.81e2 * t98 / t101 / t163
  t490 = params.omega[12]
  t494 = t153 ** 2
  t495 = t494 ** 2
  t498 = t495 * t153 * r1 + t235
  t501 = 0.9e1 / 0.16e2 * t146 * t112 * t232 - 0.3e1 * t268 * t32 + 0.3e1 * t268 * t213 + 0.27e2 * t148 * t216 + 0.40e2 / 0.81e2 * t201 * t133 * t232 + 0.120e3 * t172 * t165 - 0.192e3 * t198 * t159 + 0.17e2 / 0.6e1 * t282 * t286 * t342 + t282 * (t348 * t346 * r1 + t286 * r0) * t410 / 0.2e1 + 0.8e1 * t1 * r0 * t443 + t1 * t446 * t488 + 0.22e2 / 0.3e1 * t490 * t122 * t443 + t490 * t498 * t488
  t504 = params.omega[11]
  t519 = -0.154e3 / 0.27e2 * t417 + 0.22e2 / 0.3e1 * t419 - 0.2e1 * t421 - 0.2e1 * t423 + 0.3e1 / 0.4e1 * t427 + t430 / 0.4e1 + 0.3e1 / 0.4e1 * t434 + t437 / 0.4e1
  t533 = 0.2618e4 / 0.81e2 * t452 - 0.1232e4 / 0.27e2 * t454 + 0.44e2 / 0.3e1 * t456 + 0.44e2 / 0.3e1 * t458 - 0.8e1 * t460 - 0.8e1 / 0.3e1 * t462 + 0.3e1 / 0.4e1 * t466 + t469 + t472 / 0.4e1 + 0.3e1 / 0.4e1 * t476 + t479 + t482 / 0.4e1
  t536 = params.omega[9]
  t543 = params.omega[8]
  t550 = params.omega[7]
  t557 = params.omega[6]
  t561 = params.omega[5]
  t572 = 0.7e1 / 0.9e1 * t298 * t293 - 0.2e1 / 0.3e1 * t302 * t299 + t305 * t303 / 0.4e1 + t325 * t93 * t292 / 0.4e1
  t575 = 0.20e2 / 0.3e1 * t504 * t5 * t443 + t504 * t225 * t488 + 0.4e1 * t136 * r0 * t519 + t136 * t446 * t533 / 0.2e1 + 0.11e2 / 0.3e1 * t536 * t122 * t519 + t536 * t498 * t533 / 0.2e1 + 0.10e2 / 0.3e1 * t543 * t5 * t519 + t543 * t225 * t533 / 0.2e1 + 0.11e2 / 0.3e1 * t550 * t122 * t342 + t550 * t498 * t410 / 0.2e1 + 0.10e2 / 0.3e1 * t557 * t5 * t342 + 0.9e1 / 0.4e1 * t561 * t147 * t572
  t580 = t285 * t284 * t283
  t592 = t42 * t22
  t594 = t82 ** 2
  t596 = t69 * t594 * t21
  t601 = t592 / 0.4e1 + t596 / 0.4e1 - t98 / t101 / t30
  t605 = 0.1e1 / t119 / t2
  t609 = 0.1e1 / t152
  t618 = -t302 * t293 / 0.3e1 + t305 * t299 / 0.4e1 + t325 * t76 * t292 / 0.4e1
  t633 = t557 * t225 * t410 / 0.2e1 + 0.85e2 / 0.48e2 * t282 / t580 * t572 + t561 * t197 * t410 / 0.2e1 + 0.3e1 * t561 * t110 * t342 + 0.40e2 / 0.81e2 * t504 * t133 * t601 + 0.385e3 / 0.1296e4 * t490 * t605 * t601 - 0.55e2 / 0.108e3 * t550 * t609 * t618 + 0.72e2 * t226 * t176 + 0.7e1 / 0.3e1 * t243 * t31 + 0.16e2 / 0.3e1 * t258 * t31 + 0.9e1 * t148 * t31 + 0.72e2 * t156 * t176 - 0.56e2 * t175 * t53
  t639 = 0.1e1 / t119
  t668 = -0.64e2 * t184 * t53 - 0.72e2 * t189 * t53 + 0.55e2 / 0.12e2 * t536 * t639 * t143 + 0.72e2 * t172 * t176 + 0.72e2 * t198 * t176 + 0.40e2 / 0.3e1 * t207 * t31 - 0.80e2 * t210 * t53 + 0.55e2 / 0.6e1 * t490 * t639 * t106 + 0.20e2 / 0.3e1 * t504 * t206 * t106 + 0.10e2 / 0.3e1 * t557 * t206 * t572 - 0.3e1 / 0.4e1 * t561 * t267 * t618 - 0.595e3 / 0.864e3 * t282 / t580 / r0 * t618
  t680 = t325 * t82 * t292 / 0.4e1 + t305 * t293 / 0.4e1
  t685 = t592 / 0.8e1 + t596 / 0.8e1
  t695 = t28 * t22
  t697 = t42 * t37
  t700 = t69 * t83 * t76
  t706 = -0.2e1 / 0.3e1 * t695 + t697 / 0.2e1 + t700 / 0.2e1 + 0.8e1 / 0.3e1 * t98 / t101 / t52
  t724 = -t695 / 0.3e1 + t697 / 0.4e1 + t700 / 0.4e1
  t733 = 0.10e2 / 0.3e1 * t543 * t206 * t143 + 0.55e2 / 0.12e2 * t550 * t639 * t572 + 0.385e3 / 0.2592e4 * t550 * t605 * t680 + 0.20e2 / 0.81e2 * t543 * t133 * t685 + 0.20e2 / 0.81e2 * t557 * t133 * t680 + 0.385e3 / 0.2592e4 * t536 * t605 * t685 - 0.55e2 / 0.54e2 * t490 * t609 * t706 + 0.11305e5 / 0.41472e5 * t282 / t580 / t2 * t680 + 0.9e1 / 0.32e2 * t561 * t112 * t680 - 0.40e2 / 0.27e2 * t504 * t202 * t706 - 0.55e2 / 0.108e3 * t536 * t609 * t724 - 0.20e2 / 0.27e2 * t543 * t202 * t724 - 0.20e2 / 0.27e2 * t557 * t202 * t618
  d1111 = t180 + t221 + t263 + t501 + t575 + t633 + t668 + t733

  res = {'v4rho4': d1111}
  return res
