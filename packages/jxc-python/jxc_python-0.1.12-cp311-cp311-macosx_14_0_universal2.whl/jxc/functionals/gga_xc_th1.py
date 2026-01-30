"""Generated from gga_xc_th1.mpl."""

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

  params_n = 21

  params_a = [None, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 8 / 6, 9 / 6, 10 / 6, 11 / 6, 9 / 6, 10 / 6, 11 / 6, 12 / 6, 9 / 6, 10 / 6, 11 / 6, 12 / 6, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 1]

  params_b = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0], dtype=np.float64)

  params_c = np.array([np.nan, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float64)

  params_d = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0], dtype=np.float64)

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

  params_n = 21

  params_a = [None, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 8 / 6, 9 / 6, 10 / 6, 11 / 6, 9 / 6, 10 / 6, 11 / 6, 12 / 6, 9 / 6, 10 / 6, 11 / 6, 12 / 6, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 1]

  params_b = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0], dtype=np.float64)

  params_c = np.array([np.nan, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float64)

  params_d = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0], dtype=np.float64)

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

  params_n = 21

  params_a = [None, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 8 / 6, 9 / 6, 10 / 6, 11 / 6, 9 / 6, 10 / 6, 11 / 6, 12 / 6, 9 / 6, 10 / 6, 11 / 6, 12 / 6, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 1]

  params_b = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0], dtype=np.float64)

  params_c = np.array([np.nan, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float64)

  params_d = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0], dtype=np.float64)

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
  t17 = params.omega[20]
  t18 = params.omega[15]
  t20 = r0 ** 2
  t22 = 0.1e1 / t14 / t20
  t23 = s0 * t22
  t24 = r0 - r1
  t25 = r0 + r1
  t26 = 0.1e1 / t25
  t27 = t24 * t26
  t28 = 0.1e1 + t27
  t29 = t28 <= f.p.zeta_threshold
  t30 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t31 = t30 * f.p.zeta_threshold
  t32 = t28 ** (0.1e1 / 0.3e1)
  t34 = f.my_piecewise3(t29, t31, t32 * t28)
  t35 = t34 ** 2
  t36 = 2 ** (0.1e1 / 0.3e1)
  t37 = t35 * t36
  t38 = t23 * t37
  t40 = r1 ** 2
  t41 = r1 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t44 = 0.1e1 / t42 / t40
  t45 = s2 * t44
  t46 = 0.1e1 - t27
  t47 = t46 <= f.p.zeta_threshold
  t48 = t46 ** (0.1e1 / 0.3e1)
  t50 = f.my_piecewise3(t47, t31, t48 * t46)
  t51 = t50 ** 2
  t52 = t51 * t36
  t53 = t45 * t52
  t56 = s0 + 0.2e1 * s1 + s2
  t57 = t25 ** 2
  t58 = t25 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t61 = 0.1e1 / t59 / t57
  t63 = t38 / 0.4e1 + t53 / 0.4e1 - t56 * t61
  t66 = params.omega[4]
  t67 = t6 * r0
  t68 = t41 * r1
  t69 = t67 + t68
  t70 = t66 * t69
  t71 = jnp.sqrt(s0)
  t75 = t36 ** 2
  t76 = t34 * t75
  t79 = 0.1e1 / t67
  t80 = t71 * t79
  t81 = 0.1e1 / t57
  t82 = t24 * t81
  t83 = t26 - t82
  t86 = f.my_piecewise3(t29, 0, 0.4e1 / 0.3e1 * t32 * t83)
  t90 = jnp.sqrt(s2)
  t91 = 0.1e1 / t68
  t92 = t90 * t91
  t96 = f.my_piecewise3(t47, 0, -0.4e1 / 0.3e1 * t48 * t83)
  t100 = -t71 / t6 / t20 * t76 / 0.3e1 + t80 * t86 * t75 / 0.4e1 + t92 * t96 * t75 / 0.4e1
  t105 = t50 * t75
  t108 = t92 * t105 / 0.4e1 + t80 * t76 / 0.4e1
  t111 = params.omega[5]
  t113 = jnp.sqrt(r1)
  t115 = t10 * r0 + t113 * r1
  t116 = t111 * t115
  t122 = params.omega[6]
  t125 = t14 * r0 + t42 * r1
  t126 = t122 * t125
  t132 = params.omega[7]
  t133 = t2 ** 2
  t134 = t133 ** 2
  t135 = t134 * t2
  t137 = r1 ** (0.1e1 / 0.6e1)
  t138 = t137 ** 2
  t139 = t138 ** 2
  t140 = t139 * t137
  t142 = t135 * r0 + t140 * r1
  t143 = t132 * t142
  t149 = params.omega[8]
  t150 = t149 * t115
  t155 = s0 / t14 / t20 / r0 * t37
  t157 = t34 * t36
  t159 = t23 * t157 * t86
  t161 = t50 * t36
  t163 = t45 * t161 * t96
  t165 = -t155 / 0.3e1 + t159 / 0.4e1 + t163 / 0.4e1
  t170 = t38 / 0.8e1 + t53 / 0.8e1
  t173 = params.omega[9]
  t174 = t173 * t125
  t180 = params.omega[10]
  t181 = t180 * t142
  t187 = 0.7e1 / 0.6e1 * t1 * t2 + 0.4e1 / 0.3e1 * t5 * t6 + 0.3e1 / 0.2e1 * t9 * t10 + 0.5e1 / 0.3e1 * t13 * t14 + t17 + 0.2e1 * t18 * r0 * t63 + t70 * t100 / 0.2e1 + 0.2e1 / 0.3e1 * t66 * t6 * t108 + t116 * t100 / 0.2e1 + 0.3e1 / 0.4e1 * t111 * t10 * t108 + t126 * t100 / 0.2e1 + 0.5e1 / 0.6e1 * t122 * t14 * t108 + t143 * t100 / 0.2e1 + 0.11e2 / 0.12e2 * t132 * t135 * t108 + t150 * t165 / 0.2e1 + 0.3e1 / 0.4e1 * t149 * t10 * t170 + t174 * t165 / 0.2e1 + 0.5e1 / 0.6e1 * t173 * t14 * t170 + t181 * t165 / 0.2e1 + 0.11e2 / 0.12e2 * t180 * t135 * t170
  t188 = params.omega[11]
  t189 = t20 + t40
  t190 = t188 * t189
  t195 = params.omega[12]
  t196 = t195 * t115
  t200 = t57 * t25
  t204 = 0.8e1 / 0.3e1 * t56 / t59 / t200
  t205 = -0.2e1 / 0.3e1 * t155 + t159 / 0.2e1 + t163 / 0.2e1 + t204
  t210 = params.omega[13]
  t211 = t210 * t125
  t216 = params.omega[14]
  t217 = t216 * t142
  t222 = t18 * t189
  t224 = params.omega[16]
  t228 = t224 * (t2 * r0 + t137 * r1)
  t230 = 0.2e1 * t228 * t82
  t232 = t24 ** 2
  t234 = t232 / t200
  t236 = 0.2e1 * t228 * t234
  t237 = params.omega[17]
  t238 = t237 * t69
  t240 = 0.2e1 * t238 * t82
  t242 = 0.2e1 * t238 * t234
  t243 = params.omega[18]
  t244 = t243 * t115
  t246 = 0.2e1 * t244 * t82
  t248 = 0.2e1 * t244 * t234
  t249 = params.omega[19]
  t250 = t249 * t125
  t252 = 0.2e1 * t250 * t82
  t254 = 0.2e1 * t250 * t234
  t256 = t232 * t81
  t268 = -t236 + t240 - t242 + t246 - t248 + t252 - t254 + 0.7e1 / 0.6e1 * t224 * t2 * t256 + 0.4e1 / 0.3e1 * t237 * t6 * t256 + 0.3e1 / 0.2e1 * t243 * t10 * t256 + 0.5e1 / 0.3e1 * t249 * t14 * t256
  vrho_0_ = t187 + t190 * t165 / 0.2e1 + t188 * r0 * t170 + t196 * t205 + 0.3e1 / 0.2e1 * t195 * t10 * t63 + t211 * t205 + 0.5e1 / 0.3e1 * t210 * t14 * t63 + t217 * t205 + 0.11e2 / 0.6e1 * t216 * t135 * t63 + t222 * t205 + t230 + t268
  t278 = -t26 - t82
  t281 = f.my_piecewise3(t29, 0, 0.4e1 / 0.3e1 * t32 * t278)
  t293 = f.my_piecewise3(t47, 0, -0.4e1 / 0.3e1 * t48 * t278)
  t297 = t80 * t281 * t75 / 0.4e1 - t90 / t41 / t40 * t105 / 0.3e1 + t92 * t293 * t75 / 0.4e1
  t319 = t23 * t157 * t281
  t325 = s2 / t42 / t40 / r1 * t52
  t328 = t45 * t161 * t293
  t330 = t319 / 0.4e1 - t325 / 0.3e1 + t328 / 0.4e1
  t348 = 0.7e1 / 0.6e1 * t1 * t137 + 0.4e1 / 0.3e1 * t5 * t41 + 0.3e1 / 0.2e1 * t9 * t113 + 0.5e1 / 0.3e1 * t13 * t42 + t17 + t70 * t297 / 0.2e1 + 0.2e1 / 0.3e1 * t66 * t41 * t108 + t116 * t297 / 0.2e1 + 0.3e1 / 0.4e1 * t111 * t113 * t108 + t126 * t297 / 0.2e1 + 0.5e1 / 0.6e1 * t122 * t42 * t108 + t143 * t297 / 0.2e1 + 0.11e2 / 0.12e2 * t132 * t140 * t108 + t150 * t330 / 0.2e1 + 0.3e1 / 0.4e1 * t149 * t113 * t170 + t174 * t330 / 0.2e1 + 0.5e1 / 0.6e1 * t173 * t42 * t170 + t181 * t330 / 0.2e1 + 0.11e2 / 0.12e2 * t180 * t140 * t170 + t190 * t330 / 0.2e1
  t354 = t319 / 0.2e1 - 0.2e1 / 0.3e1 * t325 + t328 / 0.2e1 + t204
  t384 = 0.4e1 / 0.3e1 * t237 * t41 * t256 + 0.3e1 / 0.2e1 * t243 * t113 * t256 + 0.5e1 / 0.3e1 * t249 * t42 * t256 - t230 - t236 - t240 - t242 - t246 - t248 - t252 - t254
  vrho_1_ = t348 + t188 * r1 * t170 + t196 * t354 + 0.3e1 / 0.2e1 * t195 * t113 * t63 + t211 * t354 + 0.5e1 / 0.3e1 * t210 * t42 * t63 + t217 * t354 + 0.11e2 / 0.6e1 * t216 * t140 * t63 + t222 * t354 + 0.2e1 * t18 * r1 * t63 + 0.7e1 / 0.6e1 * t224 * t137 * t256 + t384
  t386 = 0.1e1 / t71
  t389 = t79 * t34 * t75
  t402 = t22 * t35 * t36
  t412 = t402 / 0.4e1 - t61
  vsigma_0_ = t70 * t386 * t389 / 0.16e2 + t116 * t386 * t389 / 0.16e2 + t126 * t386 * t389 / 0.16e2 + t143 * t386 * t389 / 0.16e2 + t150 * t402 / 0.16e2 + t174 * t402 / 0.16e2 + t181 * t402 / 0.16e2 + t190 * t402 / 0.16e2 + t196 * t412 + t211 * t412 + t217 * t412 + t222 * t412
  vsigma_1_ = -0.2e1 * t196 * t61 - 0.2e1 * t211 * t61 - 0.2e1 * t217 * t61 - 0.2e1 * t222 * t61
  t422 = 0.1e1 / t90
  t425 = t91 * t50 * t75
  t438 = t44 * t51 * t36
  t448 = t438 / 0.4e1 - t61
  vsigma_2_ = t70 * t422 * t425 / 0.16e2 + t116 * t422 * t425 / 0.16e2 + t126 * t422 * t425 / 0.16e2 + t143 * t422 * t425 / 0.16e2 + t150 * t438 / 0.16e2 + t174 * t438 / 0.16e2 + t181 * t438 / 0.16e2 + t190 * t438 / 0.16e2 + t196 * t448 + t211 * t448 + t217 * t448 + t222 * t448
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

  params_n = 21

  params_a = [None, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 8 / 6, 9 / 6, 10 / 6, 11 / 6, 9 / 6, 10 / 6, 11 / 6, 12 / 6, 9 / 6, 10 / 6, 11 / 6, 12 / 6, 7 / 6, 8 / 6, 9 / 6, 10 / 6, 1]

  params_b = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0], dtype=np.float64)

  params_c = np.array([np.nan, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float64)

  params_d = np.array([np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0], dtype=np.float64)

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
  t29 = params.omega[5] * t18
  t30 = t7 ** 2
  t31 = t30 ** 2
  t32 = t31 * t7
  t33 = 0.1e1 / t32
  t34 = jnp.sqrt(s0)
  t37 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t39 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t37 * f.p.zeta_threshold, 1)
  t44 = params.omega[6] * t11
  t45 = 0.1e1 / t25
  t51 = params.omega[7] * t2
  t58 = params.omega[8] * t18
  t59 = r0 ** 2
  t63 = t39 ** 2
  t68 = params.omega[9] * t11
  t75 = params.omega[10] * t2
  t76 = t32 * r0
  t82 = params.omega[11]
  t83 = t25 * r0
  t90 = params.omega[12] * t18
  t92 = 0.1e1 / t25 / t59
  t93 = s0 * t92
  t95 = t93 * t63 - t93
  t99 = t20 * r0
  t103 = s0 / t25 / t59 / r0
  t106 = -0.8e1 / 0.3e1 * t103 * t63 + 0.8e1 / 0.3e1 * t103
  t111 = params.omega[13] * t11
  t119 = params.omega[14] * t2
  t126 = params.omega[15]
  t129 = t126 * t59
  vrho_0_ = 0.7e1 / 0.12e2 * params.omega[0] * t4 * t2 * t7 + 0.2e1 / 0.3e1 * params.omega[1] * t12 * t14 + 0.3e1 / 0.4e1 * params.omega[2] * t18 * t20 + 0.5e1 / 0.6e1 * params.omega[3] * t11 * t25 + t29 * t33 * t34 * t39 / 0.24e2 + t44 * t45 * t34 * t39 / 0.12e2 + t51 / t20 * t34 * t39 / 0.8e1 - 0.7e1 / 0.48e2 * t58 / t7 / t59 * s0 * t63 - t68 / t59 * s0 * t63 / 0.8e1 - 0.5e1 / 0.48e2 * t75 / t76 * s0 * t63 - t82 / t83 * s0 * t63 / 0.12e2 + 0.3e1 / 0.4e1 * t90 * t20 * t95 + t90 * t99 * t106 / 0.2e1 + 0.5e1 / 0.6e1 * t111 * t25 * t95 + t111 * t83 * t106 / 0.2e1 + 0.11e2 / 0.12e2 * t119 * t32 * t95 + t119 * t76 * t106 / 0.2e1 + t126 * r0 * t95 + t129 * t106 / 0.2e1 + params.omega[20]
  t135 = 0.1e1 / t34
  t167 = t92 * t63 - t92
  vsigma_0_ = params.omega[4] * t12 * t135 * t39 / 0.8e1 + t29 * t7 * t135 * t39 / 0.8e1 + t44 * t14 * t135 * t39 / 0.8e1 + t51 * t20 * t135 * t39 / 0.8e1 + t58 / t7 / r0 * t63 / 0.8e1 + t68 / r0 * t63 / 0.8e1 + t75 * t33 * t63 / 0.8e1 + t82 * t45 * t63 / 0.8e1 + t90 * t99 * t167 / 0.2e1 + t111 * t83 * t167 / 0.2e1 + t119 * t76 * t167 / 0.2e1 + t129 * t167 / 0.2e1
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = jnp.sqrt(0.2e1)
  t3 = params.omega[5] * t2
  t4 = r0 ** (0.1e1 / 0.6e1)
  t5 = t4 ** 2
  t6 = t5 ** 2
  t7 = t6 * t4
  t8 = t7 * r0
  t9 = 0.1e1 / t8
  t10 = jnp.sqrt(s0)
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, 1)
  t20 = 2 ** (0.1e1 / 0.3e1)
  t21 = params.omega[6] * t20
  t22 = r0 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t23 * r0
  t25 = 0.1e1 / t24
  t31 = 2 ** (0.1e1 / 0.6e1)
  t32 = params.omega[7] * t31
  t33 = jnp.sqrt(r0)
  t34 = t33 * r0
  t41 = params.omega[8] * t2
  t42 = r0 ** 2
  t43 = t42 * r0
  t47 = t15 ** 2
  t52 = params.omega[9] * t20
  t59 = params.omega[10] * t31
  t67 = params.omega[12] * t2
  t68 = 0.1e1 / t33
  t70 = 0.1e1 / t23 / t42
  t71 = s0 * t70
  t73 = t71 * t47 - t71
  t78 = params.omega[13] * t20
  t79 = 0.1e1 / t22
  t84 = params.omega[14] * t31
  t89 = params.omega[11]
  t95 = 0.1e1 / t23 / t43
  t96 = s0 * t95
  t99 = -0.8e1 / 0.3e1 * t96 * t47 + 0.8e1 / 0.3e1 * t96
  t103 = -0.5e1 / 0.144e3 * t3 * t9 * t10 * t15 - t21 * t25 * t10 * t15 / 0.18e2 - t32 / t34 * t10 * t15 / 0.16e2 + 0.91e2 / 0.288e3 * t41 / t4 / t43 * s0 * t47 + t52 / t43 * s0 * t47 / 0.4e1 + 0.55e2 / 0.288e3 * t59 / t7 / t42 * s0 * t47 + 0.3e1 / 0.8e1 * t67 * t68 * t73 + 0.5e1 / 0.9e1 * t78 * t79 * t73 + 0.55e2 / 0.72e2 * t84 / t4 * t73 + 0.5e1 / 0.36e2 * t89 * t70 * s0 * t47 + 0.3e1 / 0.2e1 * t67 * t33 * t99
  t104 = t42 ** 2
  t107 = s0 / t23 / t104
  t110 = 0.88e2 / 0.9e1 * t107 * t47 - 0.88e2 / 0.9e1 * t107
  t127 = t20 ** 2
  t129 = 0.1e1 / t23
  t137 = t31 ** 2
  t138 = t137 ** 2
  t141 = 0.1e1 / t7
  t148 = params.omega[15]
  t150 = t148 * r0
  t153 = t148 * t42
  t156 = t67 * t34 * t110 / 0.2e1 + 0.5e1 / 0.3e1 * t78 * t23 * t99 + t78 * t24 * t110 / 0.2e1 + 0.11e2 / 0.6e1 * t84 * t7 * t99 + t84 * t8 * t110 / 0.2e1 + 0.2e1 / 0.9e1 * params.omega[1] * t127 * t129 + 0.3e1 / 0.8e1 * params.omega[2] * t2 * t68 + 0.7e1 / 0.72e2 * params.omega[0] * t138 * t31 * t141 + 0.5e1 / 0.9e1 * params.omega[3] * t20 * t79 + t148 * t73 + 0.2e1 * t150 * t99 + t153 * t110 / 0.2e1
  v2rho2_0_ = t103 + t156
  t157 = 0.1e1 / t10
  t186 = t70 * t47 - t70
  t192 = -0.8e1 / 0.3e1 * t95 * t47 + 0.8e1 / 0.3e1 * t95
  v2rhosigma_0_ = t3 * t141 * t157 * t15 / 0.48e2 + t21 * t129 * t157 * t15 / 0.24e2 + t32 * t68 * t157 * t15 / 0.16e2 - 0.7e1 / 0.48e2 * t41 / t4 / t42 * t47 - t52 / t42 * t47 / 0.8e1 - 0.5e1 / 0.48e2 * t59 * t9 * t47 - t89 * t25 * t47 / 0.12e2 + 0.3e1 / 0.4e1 * t67 * t33 * t186 + t67 * t34 * t192 / 0.2e1 + 0.5e1 / 0.6e1 * t78 * t23 * t186 + t78 * t24 * t192 / 0.2e1 + 0.11e2 / 0.12e2 * t84 * t7 * t186 + t84 * t8 * t192 / 0.2e1 + t150 * t186 + t153 * t192 / 0.2e1
  t214 = 0.1e1 / t10 / s0
  v2sigma2_0_ = -params.omega[4] * t127 * t214 * t15 / 0.16e2 - t21 * t22 * t214 * t15 / 0.16e2 - t3 * t4 * t214 * t15 / 0.16e2 - t32 * t33 * t214 * t15 / 0.16e2

  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = jnp.sqrt(0.2e1)
  t4 = r0 ** 2
  t5 = r0 ** (0.1e1 / 0.6e1)
  t6 = t5 ** 2
  t7 = t6 ** 2
  t8 = t7 * t5
  t11 = jnp.sqrt(s0)
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t16 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t14 * f.p.zeta_threshold, 1)
  t21 = 2 ** (0.1e1 / 0.3e1)
  t23 = r0 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t26 = 0.1e1 / t24 / t4
  t32 = 2 ** (0.1e1 / 0.6e1)
  t34 = jnp.sqrt(r0)
  t43 = t4 ** 2
  t47 = t16 ** 2
  t60 = t4 * r0
  t67 = params.omega[15]
  t69 = 0.1e1 / t24 / t60
  t70 = s0 * t69
  t73 = -0.8e1 / 0.3e1 * t70 * t47 + 0.8e1 / 0.3e1 * t70
  t77 = params.omega[12] * t2
  t78 = t34 * r0
  t79 = 0.1e1 / t78
  t80 = s0 * t26
  t82 = t80 * t47 - t80
  t87 = params.omega[13] * t21
  t89 = 0.1e1 / t23 / r0
  t94 = params.omega[14] * t32
  t112 = 0.55e2 / 0.864e3 * params.omega[5] * t2 / t8 / t4 * t11 * t16 + 0.5e1 / 0.54e2 * params.omega[6] * t21 * t26 * t11 * t16 + 0.3e1 / 0.32e2 * params.omega[7] * t32 / t34 / t4 * t11 * t16 - 0.1729e4 / 0.1728e4 * params.omega[8] * t2 / t5 / t43 * s0 * t47 - 0.3e1 / 0.4e1 * params.omega[9] * t21 / t43 * s0 * t47 - 0.935e3 / 0.1728e4 * params.omega[10] * t32 / t8 / t60 * s0 * t47 + 0.3e1 * t67 * t73 - 0.3e1 / 0.16e2 * t77 * t79 * t82 - 0.5e1 / 0.27e2 * t87 * t89 * t82 - 0.55e2 / 0.432e3 * t94 / t5 / r0 * t82 + 0.9e1 / 0.8e1 * t77 / t34 * t73 + 0.5e1 / 0.3e1 * t87 / t23 * t73 + 0.55e2 / 0.24e2 * t94 / t5 * t73
  t120 = s0 / t24 / t43
  t123 = 0.88e2 / 0.9e1 * t120 * t47 - 0.88e2 / 0.9e1 * t120
  t130 = s0 / t24 / t43 / r0
  t133 = -0.1232e4 / 0.27e2 * t130 * t47 + 0.1232e4 / 0.27e2 * t130
  t140 = t24 * r0
  t147 = t8 * r0
  t152 = t21 ** 2
  t158 = t32 ** 2
  t159 = t158 ** 2
  t179 = -0.10e2 / 0.27e2 * params.omega[11] * t69 * s0 * t47 + 0.9e1 / 0.4e1 * t77 * t34 * t123 + t77 * t78 * t133 / 0.2e1 + 0.5e1 / 0.2e1 * t87 * t24 * t123 + t87 * t140 * t133 / 0.2e1 + 0.11e2 / 0.4e1 * t94 * t8 * t123 + t94 * t147 * t133 / 0.2e1 - 0.4e1 / 0.27e2 * params.omega[1] * t152 / t140 - 0.35e2 / 0.432e3 * params.omega[0] * t159 * t32 / t147 - 0.5e1 / 0.27e2 * params.omega[3] * t21 * t89 + 0.3e1 * t67 * r0 * t123 + t67 * t4 * t133 / 0.2e1 - 0.3e1 / 0.16e2 * params.omega[2] * t2 * t79
  v3rho3_0_ = t112 + t179

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = jnp.sqrt(0.2e1)
  t4 = r0 ** 2
  t5 = t4 * r0
  t6 = r0 ** (0.1e1 / 0.6e1)
  t7 = t6 ** 2
  t8 = t7 ** 2
  t9 = t8 * t6
  t12 = jnp.sqrt(s0)
  t15 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, 1)
  t22 = 2 ** (0.1e1 / 0.3e1)
  t24 = r0 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t27 = 0.1e1 / t25 / t5
  t33 = 2 ** (0.1e1 / 0.6e1)
  t35 = jnp.sqrt(r0)
  t44 = t4 ** 2
  t45 = t44 * r0
  t49 = t17 ** 2
  t68 = params.omega[15]
  t70 = 0.1e1 / t25 / t44
  t71 = s0 * t70
  t74 = 0.88e2 / 0.9e1 * t71 * t49 - 0.88e2 / 0.9e1 * t71
  t78 = params.omega[12] * t2
  t80 = 0.1e1 / t35 / t4
  t82 = 0.1e1 / t25 / t4
  t83 = s0 * t82
  t85 = t83 * t49 - t83
  t90 = params.omega[13] * t22
  t92 = 0.1e1 / t24 / t4
  t97 = params.omega[14] * t33
  t103 = t35 * r0
  t105 = s0 * t27
  t108 = -0.8e1 / 0.3e1 * t105 * t49 + 0.8e1 / 0.3e1 * t105
  t126 = -0.935e3 / 0.5184e4 * params.omega[5] * t2 / t9 / t5 * t12 * t17 - 0.20e2 / 0.81e2 * params.omega[6] * t22 * t27 * t12 * t17 - 0.15e2 / 0.64e2 * params.omega[7] * t33 / t35 / t5 * t12 * t17 + 0.43225e5 / 0.10368e5 * params.omega[8] * t2 / t6 / t45 * s0 * t49 + 0.3e1 * params.omega[9] * t22 / t45 * s0 * t49 + 0.21505e5 / 0.10368e5 * params.omega[10] * t33 / t9 / t44 * s0 * t49 + 0.6e1 * t68 * t74 + 0.9e1 / 0.32e2 * t78 * t80 * t85 + 0.20e2 / 0.81e2 * t90 * t92 * t85 + 0.385e3 / 0.2592e4 * t97 / t6 / t4 * t85 - 0.3e1 / 0.4e1 * t78 / t103 * t108 - 0.20e2 / 0.27e2 * t90 / t24 / r0 * t108 - 0.55e2 / 0.108e3 * t97 / t6 / r0 * t108 + 0.9e1 / 0.4e1 * t78 / t35 * t74
  t142 = s0 / t25 / t45
  t145 = -0.1232e4 / 0.27e2 * t142 * t49 + 0.1232e4 / 0.27e2 * t142
  t152 = s0 / t25 / t44 / t4
  t155 = 0.20944e5 / 0.81e2 * t152 * t49 - 0.20944e5 / 0.81e2 * t152
  t174 = t33 ** 2
  t175 = t174 ** 2
  t187 = t22 ** 2
  t201 = 0.10e2 / 0.3e1 * t90 / t24 * t74 + 0.55e2 / 0.12e2 * t97 / t6 * t74 + 0.110e3 / 0.81e2 * params.omega[11] * t70 * s0 * t49 + 0.3e1 * t78 * t35 * t145 + t78 * t103 * t155 / 0.2e1 + 0.10e2 / 0.3e1 * t90 * t25 * t145 + t90 * t25 * r0 * t155 / 0.2e1 + 0.11e2 / 0.3e1 * t97 * t9 * t145 + t97 * t9 * r0 * t155 / 0.2e1 + 0.385e3 / 0.2592e4 * params.omega[0] * t175 * t33 / t9 / t4 + 0.9e1 / 0.32e2 * params.omega[2] * t2 * t80 + 0.20e2 / 0.81e2 * params.omega[1] * t187 * t82 + 0.20e2 / 0.81e2 * params.omega[3] * t22 * t92 + 0.4e1 * t68 * r0 * t145 + t68 * t4 * t155 / 0.2e1
  v4rho4_0_ = t126 + t201

  res = {'v4rho4': v4rho4_0_}
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

  t1 = params.omega[6]
  t2 = r0 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t5 = jnp.sqrt(s0)
  t6 = r0 ** 2
  t7 = t6 * r0
  t10 = t5 / t2 / t7
  t11 = r0 - r1
  t12 = r0 + r1
  t13 = 0.1e1 / t12
  t14 = t11 * t13
  t15 = 0.1e1 + t14
  t16 = t15 <= f.p.zeta_threshold
  t17 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t18 = t17 * f.p.zeta_threshold
  t19 = t15 ** (0.1e1 / 0.3e1)
  t21 = f.my_piecewise3(t16, t18, t19 * t15)
  t22 = 2 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t21 * t23
  t29 = t5 / t2 / t6
  t30 = t12 ** 2
  t31 = 0.1e1 / t30
  t32 = t11 * t31
  t33 = t13 - t32
  t36 = f.my_piecewise3(t16, 0, 0.4e1 / 0.3e1 * t19 * t33)
  t37 = t36 * t23
  t40 = t2 * r0
  t41 = 0.1e1 / t40
  t42 = t5 * t41
  t43 = t19 ** 2
  t44 = 0.1e1 / t43
  t45 = t33 ** 2
  t48 = t30 * t12
  t49 = 0.1e1 / t48
  t50 = t11 * t49
  t52 = -0.2e1 * t31 + 0.2e1 * t50
  t56 = f.my_piecewise3(t16, 0, 0.4e1 / 0.9e1 * t44 * t45 + 0.4e1 / 0.3e1 * t19 * t52)
  t57 = t56 * t23
  t60 = jnp.sqrt(s2)
  t61 = r1 ** (0.1e1 / 0.3e1)
  t62 = t61 * r1
  t64 = t60 / t62
  t65 = 0.1e1 - t14
  t66 = t65 <= f.p.zeta_threshold
  t67 = t65 ** (0.1e1 / 0.3e1)
  t68 = t67 ** 2
  t69 = 0.1e1 / t68
  t70 = -t33
  t71 = t70 ** 2
  t74 = -t52
  t78 = f.my_piecewise3(t66, 0, 0.4e1 / 0.9e1 * t69 * t71 + 0.4e1 / 0.3e1 * t67 * t74)
  t82 = 0.7e1 / 0.9e1 * t10 * t24 - 0.2e1 / 0.3e1 * t29 * t37 + t42 * t57 / 0.4e1 + t64 * t78 * t23 / 0.4e1
  t85 = params.omega[7]
  t86 = r0 ** (0.1e1 / 0.6e1)
  t87 = t86 ** 2
  t88 = t87 ** 2
  t89 = t88 * t86
  t90 = t89 * r0
  t91 = r1 ** (0.1e1 / 0.6e1)
  t92 = t91 ** 2
  t93 = t92 ** 2
  t96 = t93 * t91 * r1 + t90
  t98 = t6 ** 2
  t115 = t30 ** 2
  t116 = 0.1e1 / t115
  t117 = t11 * t116
  t119 = 0.6e1 * t49 - 0.6e1 * t117
  t123 = f.my_piecewise3(t16, 0, -0.8e1 / 0.27e2 / t43 / t15 * t45 * t33 + 0.4e1 / 0.3e1 * t44 * t33 * t52 + 0.4e1 / 0.3e1 * t19 * t119)
  t139 = f.my_piecewise3(t66, 0, -0.8e1 / 0.27e2 / t68 / t65 * t71 * t70 + 0.4e1 / 0.3e1 * t69 * t70 * t74 - 0.4e1 / 0.3e1 * t67 * t119)
  t143 = -0.70e2 / 0.27e2 * t5 / t2 / t98 * t24 + 0.7e1 / 0.3e1 * t10 * t37 - t29 * t57 + t42 * t123 * t23 / 0.4e1 + t64 * t139 * t23 / 0.4e1
  t149 = params.omega[8]
  t150 = jnp.sqrt(r0)
  t151 = t150 * r0
  t152 = jnp.sqrt(r1)
  t154 = t152 * r1 + t151
  t160 = t21 ** 2
  t161 = t160 * t22
  t162 = s0 / t3 / t98 / r0 * t161
  t166 = s0 / t3 / t98
  t167 = t21 * t22
  t168 = t167 * t36
  t169 = t166 * t168
  t173 = s0 / t3 / t7
  t174 = t36 ** 2
  t175 = t174 * t22
  t176 = t173 * t175
  t178 = t167 * t56
  t179 = t173 * t178
  t183 = s0 / t3 / t6
  t186 = t183 * t36 * t22 * t56
  t189 = t183 * t167 * t123
  t191 = r1 ** 2
  t192 = t61 ** 2
  t195 = s2 / t192 / t191
  t198 = f.my_piecewise3(t66, 0, 0.4e1 / 0.3e1 * t67 * t70)
  t201 = t195 * t198 * t22 * t78
  t204 = f.my_piecewise3(t66, t18, t67 * t65)
  t205 = t204 * t22
  t207 = t195 * t205 * t139
  t209 = -0.154e3 / 0.27e2 * t162 + 0.22e2 / 0.3e1 * t169 - 0.2e1 * t176 - 0.2e1 * t179 + 0.3e1 / 0.4e1 * t186 + t189 / 0.4e1 + 0.3e1 / 0.4e1 * t201 + t207 / 0.4e1
  t213 = t166 * t161
  t215 = t173 * t168
  t217 = t183 * t175
  t219 = t183 * t178
  t221 = t198 ** 2
  t223 = t195 * t221 * t22
  t226 = t195 * t205 * t78
  t228 = 0.11e2 / 0.9e1 * t213 - 0.4e1 / 0.3e1 * t215 + t217 / 0.4e1 + t219 / 0.4e1 + t223 / 0.4e1 + t226 / 0.4e1
  t231 = params.omega[14]
  t240 = s0 + 0.2e1 * s1 + s2
  t241 = t12 ** (0.1e1 / 0.3e1)
  t242 = t241 ** 2
  t247 = 0.22e2 / 0.9e1 * t213 - 0.8e1 / 0.3e1 * t215 + t217 / 0.2e1 + t219 / 0.2e1 + t223 / 0.2e1 + t226 / 0.2e1 - 0.88e2 / 0.9e1 * t240 / t242 / t115
  t259 = t115 * t12
  t264 = -0.308e3 / 0.27e2 * t162 + 0.44e2 / 0.3e1 * t169 - 0.4e1 * t176 - 0.4e1 * t179 + 0.3e1 / 0.2e1 * t186 + t189 / 0.2e1 + 0.3e1 / 0.2e1 * t201 + t207 / 0.2e1 + 0.1232e4 / 0.27e2 * t240 / t242 / t259
  t266 = params.omega[13]
  t270 = t3 * r0
  t272 = t192 * r1 + t270
  t275 = params.omega[12]
  t284 = t64 * t204 * t23 / 0.4e1 + t42 * t24 / 0.4e1
  t287 = params.omega[5]
  t288 = 0.1e1 / t151
  t292 = t86 * r0
  t293 = 0.1e1 / t292
  t298 = t183 * t161
  t299 = t204 ** 2
  t301 = t195 * t299 * t22
  t303 = t298 / 0.8e1 + t301 / 0.8e1
  t306 = params.omega[9]
  t310 = params.omega[10]
  t320 = t298 / 0.4e1 + t301 / 0.4e1 - t240 / t242 / t30
  t329 = params.omega[4]
  t330 = 0.1e1 / t270
  t337 = -0.5e1 / 0.27e2 * t1 * t41 * t284 - 0.3e1 / 0.16e2 * t287 * t288 * t284 - 0.55e2 / 0.432e3 * t85 * t293 * t284 - 0.3e1 / 0.16e2 * t149 * t288 * t303 - 0.5e1 / 0.27e2 * t306 * t41 * t303 - 0.55e2 / 0.432e3 * t310 * t293 * t303 - 0.3e1 / 0.8e1 * t275 * t288 * t320 - 0.10e2 / 0.27e2 * t266 * t41 * t320 - 0.55e2 / 0.216e3 * t231 * t293 * t320 - 0.4e1 / 0.27e2 * t329 * t330 * t284 + t306 * t272 * t209 / 0.2e1
  t348 = params.omega[11]
  t349 = t6 + t191
  t356 = 0.1e1 / t3
  t365 = -t29 * t24 / 0.3e1 + t42 * t37 / 0.4e1 + t64 * t198 * t23 / 0.4e1
  t368 = t40 + t62
  t372 = 0.1e1 / t86
  t374 = t173 * t161
  t376 = t183 * t168
  t379 = t195 * t205 * t198
  t385 = -0.2e1 / 0.3e1 * t374 + t376 / 0.2e1 + t379 / 0.2e1 + 0.8e1 / 0.3e1 * t240 / t242 / t48
  t388 = 0.1e1 / t2
  t392 = 0.1e1 / t150
  t396 = params.omega[16]
  t399 = t396 * (t91 * r1 + t292)
  t402 = 0.5e1 / 0.2e1 * t306 * t3 * t228 + t310 * t96 * t209 / 0.2e1 + 0.11e2 / 0.4e1 * t310 * t89 * t228 + t348 * t349 * t209 / 0.2e1 + 0.3e1 * t348 * r0 * t228 + 0.2e1 / 0.3e1 * t329 * t356 * t365 + t329 * t368 * t143 / 0.2e1 + 0.55e2 / 0.12e2 * t231 * t372 * t385 + 0.10e2 / 0.3e1 * t266 * t388 * t385 + 0.9e1 / 0.4e1 * t275 * t392 * t385 - 0.12e2 * t399 * t49
  t403 = params.omega[17]
  t404 = t403 * t368
  t407 = params.omega[18]
  t408 = t407 * t154
  t411 = params.omega[19]
  t412 = t411 * t272
  t415 = t396 * t86
  t418 = t403 * t2
  t421 = t407 * t150
  t424 = t411 * t3
  t439 = -0.12e2 * t404 * t49 - 0.12e2 * t408 * t49 - 0.12e2 * t412 * t49 + 0.7e1 * t415 * t31 + 0.8e1 * t418 * t31 + 0.9e1 * t421 * t31 + 0.10e2 * t424 * t31 + 0.2e1 * t329 * t2 * t82 + t287 * t154 * t143 / 0.2e1 + 0.9e1 / 0.4e1 * t287 * t150 * t82 + t1 * t272 * t143 / 0.2e1
  t458 = -t374 / 0.3e1 + t376 / 0.4e1 + t379 / 0.4e1
  t467 = params.omega[15]
  t488 = 0.1e1 / t90
  t493 = t11 ** 2
  t495 = t493 / t259
  t506 = -0.8e1 / 0.27e2 * params.omega[1] * t330 + 0.6e1 * t467 * t385 - 0.3e1 / 0.8e1 * params.omega[2] * t288 - 0.10e2 / 0.27e2 * params.omega[3] * t41 - 0.35e2 / 0.216e3 * params.omega[0] * t488 + 0.36e2 * t399 * t117 - 0.24e2 * t399 * t495 + 0.36e2 * t404 * t117 - 0.24e2 * t404 * t495 + 0.36e2 * t408 * t117 - 0.24e2 * t408 * t495
  t513 = t493 * t31
  t517 = t396 / t89
  t520 = t493 * t49
  t526 = t403 * t356
  t534 = t407 * t392
  t539 = 0.36e2 * t412 * t117 - 0.24e2 * t412 * t495 - 0.35e2 / 0.216e3 * t396 * t488 * t513 + 0.7e1 / 0.6e1 * t517 * t32 - 0.7e1 / 0.6e1 * t517 * t520 - 0.8e1 / 0.27e2 * t403 * t330 * t513 + 0.8e1 / 0.3e1 * t526 * t32 - 0.8e1 / 0.3e1 * t526 * t520 - 0.3e1 / 0.8e1 * t407 * t288 * t513 + 0.9e1 / 0.2e1 * t534 * t32 - 0.9e1 / 0.2e1 * t534 * t520
  t543 = t411 * t388
  t550 = t493 * t116
  t565 = -0.10e2 / 0.27e2 * t411 * t41 * t513 + 0.20e2 / 0.3e1 * t543 * t32 - 0.20e2 / 0.3e1 * t543 * t520 - 0.28e2 * t415 * t50 + 0.21e2 * t415 * t550 - 0.32e2 * t418 * t50 + 0.24e2 * t418 * t550 - 0.36e2 * t421 * t50 + 0.27e2 * t421 * t550 - 0.40e2 * t424 * t50 + 0.30e2 * t424 * t550
  d111 = t565 + t539 + t506 + t439 + t402 + 0.5e1 / 0.3e1 * t306 * t388 * t458 + 0.55e2 / 0.24e2 * t310 * t372 * t458 + 0.6e1 * t467 * r0 * t247 + t467 * t349 * t264 + 0.9e1 / 0.2e1 * t275 * t150 * t247 + 0.5e1 / 0.3e1 * t1 * t388 * t365 + 0.9e1 / 0.8e1 * t287 * t392 * t365 + 0.55e2 / 0.24e2 * t85 * t372 * t365 + 0.9e1 / 0.8e1 * t149 * t392 * t458 + t149 * t154 * t209 / 0.2e1 + 0.9e1 / 0.4e1 * t149 * t150 * t228 + 0.11e2 / 0.2e1 * t231 * t89 * t247 + t231 * t96 * t264 + 0.5e1 * t266 * t3 * t247 + t266 * t272 * t264 + t275 * t154 * t264 + 0.5e1 / 0.2e1 * t1 * t3 * t82 + t85 * t96 * t143 / 0.2e1 + 0.11e2 / 0.4e1 * t85 * t89 * t82 + t337 + 0.3e1 * t348 * t458

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
  t2 = r0 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t5 = r0 ** 2
  t6 = t5 ** 2
  t7 = t6 * r0
  t10 = s0 / t3 / t7
  t11 = r0 - r1
  t12 = r0 + r1
  t13 = 0.1e1 / t12
  t14 = t11 * t13
  t15 = 0.1e1 + t14
  t16 = t15 <= f.p.zeta_threshold
  t17 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t18 = t17 * f.p.zeta_threshold
  t19 = t15 ** (0.1e1 / 0.3e1)
  t21 = f.my_piecewise3(t16, t18, t19 * t15)
  t22 = t21 ** 2
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t22 * t23
  t25 = t10 * t24
  t29 = s0 / t3 / t6
  t30 = t21 * t23
  t31 = t12 ** 2
  t32 = 0.1e1 / t31
  t33 = t11 * t32
  t34 = t13 - t33
  t37 = f.my_piecewise3(t16, 0, 0.4e1 / 0.3e1 * t19 * t34)
  t38 = t30 * t37
  t39 = t29 * t38
  t41 = t5 * r0
  t44 = s0 / t3 / t41
  t45 = t37 ** 2
  t46 = t45 * t23
  t47 = t44 * t46
  t49 = t19 ** 2
  t50 = 0.1e1 / t49
  t51 = t34 ** 2
  t54 = t31 * t12
  t55 = 0.1e1 / t54
  t56 = t11 * t55
  t58 = -0.2e1 * t32 + 0.2e1 * t56
  t62 = f.my_piecewise3(t16, 0, 0.4e1 / 0.9e1 * t50 * t51 + 0.4e1 / 0.3e1 * t19 * t58)
  t63 = t30 * t62
  t64 = t44 * t63
  t67 = 0.1e1 / t3 / t5
  t68 = s0 * t67
  t69 = t37 * t23
  t70 = t69 * t62
  t71 = t68 * t70
  t74 = 0.1e1 / t49 / t15
  t78 = t50 * t34
  t81 = t31 ** 2
  t82 = 0.1e1 / t81
  t83 = t11 * t82
  t85 = 0.6e1 * t55 - 0.6e1 * t83
  t89 = f.my_piecewise3(t16, 0, -0.8e1 / 0.27e2 * t74 * t51 * t34 + 0.4e1 / 0.3e1 * t78 * t58 + 0.4e1 / 0.3e1 * t19 * t85)
  t90 = t30 * t89
  t91 = t68 * t90
  t93 = r1 ** 2
  t94 = r1 ** (0.1e1 / 0.3e1)
  t95 = t94 ** 2
  t98 = s2 / t95 / t93
  t99 = 0.1e1 - t14
  t100 = t99 <= f.p.zeta_threshold
  t101 = t99 ** (0.1e1 / 0.3e1)
  t102 = -t34
  t105 = f.my_piecewise3(t100, 0, 0.4e1 / 0.3e1 * t101 * t102)
  t106 = t105 * t23
  t107 = t101 ** 2
  t108 = 0.1e1 / t107
  t109 = t102 ** 2
  t112 = -t58
  t116 = f.my_piecewise3(t100, 0, 0.4e1 / 0.9e1 * t108 * t109 + 0.4e1 / 0.3e1 * t101 * t112)
  t118 = t98 * t106 * t116
  t121 = f.my_piecewise3(t100, t18, t101 * t99)
  t122 = t121 * t23
  t124 = 0.1e1 / t107 / t99
  t128 = t108 * t102
  t131 = -t85
  t135 = f.my_piecewise3(t100, 0, -0.8e1 / 0.27e2 * t124 * t109 * t102 + 0.4e1 / 0.3e1 * t128 * t112 + 0.4e1 / 0.3e1 * t101 * t131)
  t137 = t98 * t122 * t135
  t140 = s0 + 0.2e1 * s1 + s2
  t141 = t81 * t12
  t142 = t12 ** (0.1e1 / 0.3e1)
  t143 = t142 ** 2
  t148 = -0.308e3 / 0.27e2 * t25 + 0.44e2 / 0.3e1 * t39 - 0.4e1 * t47 - 0.4e1 * t64 + 0.3e1 / 0.2e1 * t71 + t91 / 0.2e1 + 0.3e1 / 0.2e1 * t118 + t137 / 0.2e1 + 0.1232e4 / 0.27e2 * t140 / t143 / t141
  t151 = params.omega[14]
  t152 = r0 ** (0.1e1 / 0.6e1)
  t153 = t152 ** 2
  t154 = t153 ** 2
  t155 = t154 * t152
  t156 = t155 * r0
  t157 = r1 ** (0.1e1 / 0.6e1)
  t158 = t157 ** 2
  t159 = t158 ** 2
  t162 = t159 * t157 * r1 + t156
  t168 = s0 / t3 / t6 / t5 * t24
  t170 = t10 * t38
  t172 = t29 * t46
  t174 = t29 * t63
  t176 = t44 * t70
  t178 = t44 * t90
  t180 = t62 ** 2
  t182 = t68 * t180 * t23
  t185 = t68 * t69 * t89
  t187 = t15 ** 2
  t190 = t51 ** 2
  t196 = t58 ** 2
  t201 = 0.1e1 / t141
  t202 = t11 * t201
  t204 = -0.24e2 * t82 + 0.24e2 * t202
  t208 = f.my_piecewise3(t16, 0, 0.40e2 / 0.81e2 / t49 / t187 * t190 - 0.16e2 / 0.9e1 * t74 * t51 * t58 + 0.4e1 / 0.3e1 * t50 * t196 + 0.16e2 / 0.9e1 * t78 * t85 + 0.4e1 / 0.3e1 * t19 * t204)
  t210 = t68 * t30 * t208
  t212 = t116 ** 2
  t214 = t98 * t212 * t23
  t217 = t98 * t106 * t135
  t219 = t99 ** 2
  t222 = t109 ** 2
  t228 = t112 ** 2
  t237 = f.my_piecewise3(t100, 0, 0.40e2 / 0.81e2 / t107 / t219 * t222 - 0.16e2 / 0.9e1 * t124 * t109 * t112 + 0.4e1 / 0.3e1 * t108 * t228 + 0.16e2 / 0.9e1 * t128 * t131 - 0.4e1 / 0.3e1 * t101 * t204)
  t239 = t98 * t122 * t237
  t241 = t81 * t31
  t246 = 0.5236e4 / 0.81e2 * t168 - 0.2464e4 / 0.27e2 * t170 + 0.88e2 / 0.3e1 * t172 + 0.88e2 / 0.3e1 * t174 - 0.16e2 * t176 - 0.16e2 / 0.3e1 * t178 + 0.3e1 / 0.2e1 * t182 + 0.2e1 * t185 + t210 / 0.2e1 + 0.3e1 / 0.2e1 * t214 + 0.2e1 * t217 + t239 / 0.2e1 - 0.20944e5 / 0.81e2 * t140 / t143 / t241
  t251 = params.omega[12]
  t252 = jnp.sqrt(r0)
  t253 = t252 * r0
  t254 = jnp.sqrt(r1)
  t256 = t254 * r1 + t253
  t262 = params.omega[7]
  t263 = 0.1e1 / t152
  t265 = jnp.sqrt(s0)
  t268 = t265 / t2 / t41
  t269 = t23 ** 2
  t270 = t21 * t269
  t274 = 0.1e1 / t2 / t5
  t275 = t265 * t274
  t276 = t37 * t269
  t279 = t2 * r0
  t280 = 0.1e1 / t279
  t281 = t265 * t280
  t282 = t62 * t269
  t285 = jnp.sqrt(s2)
  t286 = t94 * r1
  t288 = t285 / t286
  t292 = 0.7e1 / 0.9e1 * t268 * t270 - 0.2e1 / 0.3e1 * t275 * t276 + t281 * t282 / 0.4e1 + t288 * t116 * t269 / 0.4e1
  t295 = params.omega[6]
  t296 = 0.1e1 / t2
  t300 = params.omega[5]
  t301 = 0.1e1 / t252
  t313 = t265 / t2 / t6
  t318 = t89 * t269
  t327 = 0.910e3 / 0.81e2 * t265 / t2 / t7 * t270 - 0.280e3 / 0.27e2 * t313 * t276 + 0.14e2 / 0.3e1 * t268 * t282 - 0.4e1 / 0.3e1 * t275 * t318 + t281 * t208 * t269 / 0.4e1 + t288 * t237 * t269 / 0.4e1
  t341 = -0.70e2 / 0.27e2 * t313 * t270 + 0.7e1 / 0.3e1 * t268 * t276 - t275 * t282 + t281 * t318 / 0.4e1 + t288 * t135 * t269 / 0.4e1
  t344 = t3 * r0
  t346 = t95 * r1 + t344
  t356 = 0.20e2 / 0.3e1 * t1 * t3 * t148 + t151 * t162 * t246 + 0.22e2 / 0.3e1 * t151 * t155 * t148 + t251 * t256 * t246 + 0.6e1 * t251 * t252 * t148 + 0.55e2 / 0.12e2 * t262 * t263 * t292 + 0.10e2 / 0.3e1 * t295 * t296 * t292 + 0.9e1 / 0.4e1 * t300 * t301 * t292 + t300 * t256 * t327 / 0.2e1 + 0.3e1 * t300 * t252 * t341 + t295 * t346 * t327 / 0.2e1 + 0.10e2 / 0.3e1 * t295 * t3 * t341 + t262 * t162 * t327 / 0.2e1
  t360 = params.omega[15]
  t364 = t5 + t93
  t367 = params.omega[4]
  t368 = 0.1e1 / t344
  t377 = -t275 * t270 / 0.3e1 + t281 * t276 / 0.4e1 + t288 * t105 * t269 / 0.4e1
  t380 = params.omega[11]
  t390 = -0.154e3 / 0.27e2 * t25 + 0.22e2 / 0.3e1 * t39 - 0.2e1 * t47 - 0.2e1 * t64 + 0.3e1 / 0.4e1 * t71 + t91 / 0.4e1 + 0.3e1 / 0.4e1 * t118 + t137 / 0.4e1
  t404 = 0.2618e4 / 0.81e2 * t168 - 0.1232e4 / 0.27e2 * t170 + 0.44e2 / 0.3e1 * t172 + 0.44e2 / 0.3e1 * t174 - 0.8e1 * t176 - 0.8e1 / 0.3e1 * t178 + 0.3e1 / 0.4e1 * t182 + t185 + t210 / 0.4e1 + 0.3e1 / 0.4e1 * t214 + t217 + t239 / 0.4e1
  t407 = params.omega[10]
  t414 = params.omega[9]
  t421 = params.omega[8]
  t429 = t29 * t24
  t431 = t44 * t38
  t433 = t68 * t46
  t435 = t68 * t63
  t437 = t105 ** 2
  t439 = t98 * t437 * t23
  t442 = t98 * t122 * t116
  t448 = 0.22e2 / 0.9e1 * t429 - 0.8e1 / 0.3e1 * t431 + t433 / 0.2e1 + t435 / 0.2e1 + t439 / 0.2e1 + t442 / 0.2e1 - 0.88e2 / 0.9e1 * t140 / t143 / t81
  t451 = params.omega[16]
  t452 = t451 * t152
  t455 = 0.11e2 / 0.3e1 * t262 * t155 * t341 + 0.8e1 * t360 * r0 * t148 + t360 * t364 * t246 - 0.16e2 / 0.27e2 * t367 * t368 * t377 + 0.4e1 * t380 * r0 * t390 + t380 * t364 * t404 / 0.2e1 + 0.11e2 / 0.3e1 * t407 * t155 * t390 + t407 * t162 * t404 / 0.2e1 + 0.10e2 / 0.3e1 * t414 * t3 * t390 + t414 * t346 * t404 / 0.2e1 + 0.3e1 * t421 * t252 * t390 + t421 * t256 * t404 / 0.2e1 + 0.20e2 / 0.3e1 * t1 * t296 * t448 - 0.56e2 * t452 * t55
  t457 = params.omega[17]
  t458 = t457 * t2
  t461 = params.omega[18]
  t462 = t461 * t252
  t465 = params.omega[19]
  t466 = t465 * t3
  t472 = t279 + t286
  t479 = 0.1e1 / t3
  t486 = 0.1e1 / t152 / t5
  t492 = t288 * t121 * t269 / 0.4e1 + t281 * t270 / 0.4e1
  t499 = 0.1e1 / t252 / t5
  t504 = t68 * t24
  t505 = t121 ** 2
  t507 = t98 * t505 * t23
  t509 = t504 / 0.8e1 + t507 / 0.8e1
  t515 = -0.64e2 * t458 * t55 - 0.72e2 * t462 * t55 - 0.80e2 * t466 * t55 + 0.55e2 / 0.6e1 * t151 * t263 * t448 + t367 * t472 * t327 / 0.2e1 + 0.8e1 / 0.3e1 * t367 * t2 * t341 + 0.4e1 / 0.3e1 * t367 * t479 * t292 + t1 * t346 * t246 + 0.385e3 / 0.2592e4 * t262 * t486 * t492 + 0.20e2 / 0.81e2 * t295 * t274 * t492 + 0.9e1 / 0.32e2 * t300 * t499 * t492 + 0.9e1 / 0.32e2 * t421 * t499 * t509 + 0.20e2 / 0.81e2 * t414 * t274 * t509
  t525 = t504 / 0.4e1 + t507 / 0.4e1 - t140 / t143 / t31
  t538 = t451 / t155
  t544 = t152 * r0
  t545 = 0.1e1 / t544
  t552 = 0.1e1 / t253
  t557 = t44 * t24
  t559 = t68 * t38
  t562 = t98 * t122 * t105
  t564 = -t557 / 0.3e1 + t559 / 0.4e1 + t562 / 0.4e1
  t581 = -0.2e1 / 0.3e1 * t557 + t559 / 0.2e1 + t562 / 0.2e1 + 0.8e1 / 0.3e1 * t140 / t143 / t54
  t584 = 0.385e3 / 0.2592e4 * t407 * t486 * t509 + 0.9e1 / 0.16e2 * t251 * t499 * t525 + 0.40e2 / 0.81e2 * t1 * t274 * t525 + 0.385e3 / 0.1296e4 * t151 * t486 * t525 + 0.20e2 / 0.81e2 * t367 * t67 * t492 + 0.7e1 / 0.3e1 * t538 * t32 + 0.9e1 / 0.2e1 * t251 * t301 * t448 - 0.55e2 / 0.108e3 * t262 * t545 * t377 - 0.20e2 / 0.27e2 * t295 * t280 * t377 - 0.3e1 / 0.4e1 * t300 * t552 * t377 - 0.3e1 / 0.4e1 * t421 * t552 * t564 - 0.20e2 / 0.27e2 * t414 * t280 * t564 - 0.55e2 / 0.108e3 * t407 * t545 * t564 - 0.3e1 / 0.2e1 * t251 * t552 * t581
  t587 = t457 * t479
  t590 = t461 * t301
  t593 = t465 * t296
  t603 = 0.11e2 / 0.9e1 * t429 - 0.4e1 / 0.3e1 * t431 + t433 / 0.4e1 + t435 / 0.4e1 + t439 / 0.4e1 + t442 / 0.4e1
  t617 = t451 * (t157 * r1 + t544)
  t620 = t457 * t472
  t623 = t461 * t256
  t626 = t465 * t346
  t634 = 0.16e2 / 0.3e1 * t587 * t32 + 0.9e1 * t590 * t32 + 0.40e2 / 0.3e1 * t593 * t32 + 0.55e2 / 0.12e2 * t407 * t263 * t603 + 0.10e2 / 0.3e1 * t414 * t296 * t603 + 0.9e1 / 0.4e1 * t421 * t301 * t603 - 0.40e2 / 0.27e2 * t1 * t280 * t581 + 0.72e2 * t617 * t82 + 0.72e2 * t620 * t82 + 0.72e2 * t623 * t82 + 0.72e2 * t626 * t82 - 0.55e2 / 0.54e2 * t151 * t545 * t581 + 0.12e2 * t360 * t448
  t640 = 0.1e1 / t155 / t5
  t652 = t11 ** 2
  t653 = t652 * t32
  t657 = t451 / t156
  t662 = t652 * t201
  t667 = t652 * t55
  t672 = t652 * t82
  t678 = 0.40e2 / 0.81e2 * params.omega[1] * t67 + 0.385e3 / 0.1296e4 * params.omega[0] * t640 + 0.40e2 / 0.81e2 * params.omega[3] * t274 + 0.6e1 * t380 * t603 + 0.9e1 / 0.16e2 * params.omega[2] * t499 + 0.385e3 / 0.1296e4 * t451 * t640 * t653 - 0.35e2 / 0.27e2 * t657 * t33 + 0.168e3 * t452 * t83 - 0.112e3 * t452 * t662 + 0.192e3 * t458 * t83 + 0.35e2 / 0.27e2 * t657 * t667 - 0.28e2 / 0.3e1 * t538 * t56 + 0.7e1 * t538 * t672 + 0.40e2 / 0.81e2 * t457 * t67 * t653
  t680 = t457 * t368
  t692 = t461 * t552
  t704 = t465 * t280
  t711 = -0.64e2 / 0.27e2 * t680 * t33 + 0.64e2 / 0.27e2 * t680 * t667 - 0.64e2 / 0.3e1 * t587 * t56 + 0.16e2 * t587 * t672 + 0.9e1 / 0.16e2 * t461 * t499 * t653 - 0.3e1 * t692 * t33 + 0.3e1 * t692 * t667 - 0.36e2 * t590 * t56 + 0.27e2 * t590 * t672 + 0.40e2 / 0.81e2 * t465 * t274 * t653 - 0.80e2 / 0.27e2 * t704 * t33 + 0.80e2 / 0.27e2 * t704 * t667 - 0.160e3 / 0.3e1 * t593 * t56
  t717 = t652 / t241
  t742 = -0.192e3 * t617 * t202 - 0.192e3 * t620 * t202 - 0.192e3 * t623 * t202 - 0.192e3 * t626 * t202 - 0.128e3 * t458 * t662 - 0.144e3 * t462 * t662 + 0.216e3 * t462 * t83 - 0.160e3 * t466 * t662 + 0.240e3 * t466 * t83 + 0.40e2 * t593 * t672 + 0.120e3 * t617 * t717 + 0.120e3 * t620 * t717 + 0.120e3 * t623 * t717 + 0.120e3 * t626 * t717
  d1111 = t356 + t455 + t515 + t584 + t634 + t678 + t711 + t742

  res = {'v4rho4': d1111}
  return res
