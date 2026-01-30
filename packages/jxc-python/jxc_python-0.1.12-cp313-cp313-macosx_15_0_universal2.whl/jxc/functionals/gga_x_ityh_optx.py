"""Generated from gga_x_ityh_optx.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
import scipy.special as sp_special
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

  params_gamma = 6.0

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  optx_f = lambda x: params_a + params_b * (params_gamma * x ** 2 / (1 + params_gamma * x ** 2)) ** 2

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_enhancement = lambda xs: optx_f(xs)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  ityh_k_GGA = lambda rs, z, xs: jnp.sqrt(9 * jnp.pi / (2 * X_FACTOR_C * ityh_enhancement(xs))) * f.n_spin(rs, z) ** (1 / 3)

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  ityh_aa = lambda rs, z, xs: f.p.cam_omega / (2 * ityh_k_GGA(rs, z, xs))

  ityh_attenuation = lambda a: attenuation_erf(a)

  ityh_f_aa = lambda rs, z, xs: ityh_attenuation(ityh_aa(rs, z, xs))

  ityh_f = lambda rs, z, xs: ityh_f_aa(rs, z, xs) * ityh_enhancement(xs)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, ityh_f, rs, zeta, xs0, xs1)

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

  params_gamma = 6.0

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  optx_f = lambda x: params_a + params_b * (params_gamma * x ** 2 / (1 + params_gamma * x ** 2)) ** 2

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_enhancement = lambda xs: optx_f(xs)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  ityh_k_GGA = lambda rs, z, xs: jnp.sqrt(9 * jnp.pi / (2 * X_FACTOR_C * ityh_enhancement(xs))) * f.n_spin(rs, z) ** (1 / 3)

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  ityh_aa = lambda rs, z, xs: f.p.cam_omega / (2 * ityh_k_GGA(rs, z, xs))

  ityh_attenuation = lambda a: attenuation_erf(a)

  ityh_f_aa = lambda rs, z, xs: ityh_attenuation(ityh_aa(rs, z, xs))

  ityh_f = lambda rs, z, xs: ityh_f_aa(rs, z, xs) * ityh_enhancement(xs)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, ityh_f, rs, zeta, xs0, xs1)

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

  params_gamma = 6.0

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  optx_f = lambda x: params_a + params_b * (params_gamma * x ** 2 / (1 + params_gamma * x ** 2)) ** 2

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_enhancement = lambda xs: optx_f(xs)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  ityh_k_GGA = lambda rs, z, xs: jnp.sqrt(9 * jnp.pi / (2 * X_FACTOR_C * ityh_enhancement(xs))) * f.n_spin(rs, z) ** (1 / 3)

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  ityh_aa = lambda rs, z, xs: f.p.cam_omega / (2 * ityh_k_GGA(rs, z, xs))

  ityh_attenuation = lambda a: attenuation_erf(a)

  ityh_f_aa = lambda rs, z, xs: ityh_attenuation(ityh_aa(rs, z, xs))

  ityh_f = lambda rs, z, xs: ityh_f_aa(rs, z, xs) * ityh_enhancement(xs)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, ityh_f, rs, zeta, xs0, xs1)

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
  t26 = t5 * t25
  t27 = t6 ** (0.1e1 / 0.3e1)
  t28 = t2 ** 2
  t29 = jnp.pi * t28
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = t32 * t33
  t35 = s0 ** 2
  t36 = params.b * t35
  t37 = r0 ** 2
  t38 = t37 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t43 = t40 ** 2
  t48 = 0.1e1 + 0.60e1 * s0 / t43 / t37
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t51 = 0.1e1 / t40 / t38 / r0 * t50
  t54 = params.a + 0.3600e2 * t36 * t51
  t57 = t29 * t34 / t54
  t58 = jnp.sqrt(t57)
  t60 = f.p.cam_omega / t58
  t61 = 2 ** (0.1e1 / 0.3e1)
  t62 = t19 * t6
  t63 = t62 ** (0.1e1 / 0.3e1)
  t65 = t61 / t63
  t67 = t60 * t65 / 0.2e1
  t68 = 0.135e1 <= t67
  t69 = 0.135e1 < t67
  t70 = f.my_piecewise3(t69, t67, 0.135e1)
  t71 = t70 ** 2
  t74 = t71 ** 2
  t77 = t74 * t71
  t80 = t74 ** 2
  t92 = t80 ** 2
  t96 = f.my_piecewise3(t69, 0.135e1, t67)
  t97 = jnp.sqrt(jnp.pi)
  t98 = 0.1e1 / t96
  t100 = jax.lax.erf(t98 / 0.2e1)
  t102 = t96 ** 2
  t103 = 0.1e1 / t102
  t105 = jnp.exp(-t103 / 0.4e1)
  t106 = t105 - 0.1e1
  t109 = t105 - 0.3e1 / 0.2e1 - 0.2e1 * t102 * t106
  t112 = t97 * t100 + 0.2e1 * t96 * t109
  t116 = f.my_piecewise3(t68, 0.1e1 / t71 / 0.36e2 - 0.1e1 / t74 / 0.960e3 + 0.1e1 / t77 / 0.26880e5 - 0.1e1 / t80 / 0.829440e6 + 0.1e1 / t80 / t71 / 0.28385280e8 - 0.1e1 / t80 / t74 / 0.1073479680e10 + 0.1e1 / t80 / t77 / 0.44590694400e11 - 0.1e1 / t92 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t96 * t112)
  t117 = t27 * t116
  t118 = t117 * t54
  t121 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t118)
  t122 = r1 <= f.p.dens_threshold
  t123 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t124 = 0.1e1 + t123
  t125 = t124 <= f.p.zeta_threshold
  t126 = t124 ** (0.1e1 / 0.3e1)
  t128 = f.my_piecewise3(t125, t22, t126 * t124)
  t129 = t5 * t128
  t130 = s2 ** 2
  t131 = params.b * t130
  t132 = r1 ** 2
  t133 = t132 ** 2
  t135 = r1 ** (0.1e1 / 0.3e1)
  t138 = t135 ** 2
  t143 = 0.1e1 + 0.60e1 * s2 / t138 / t132
  t144 = t143 ** 2
  t145 = 0.1e1 / t144
  t146 = 0.1e1 / t135 / t133 / r1 * t145
  t149 = params.a + 0.3600e2 * t131 * t146
  t152 = t29 * t34 / t149
  t153 = jnp.sqrt(t152)
  t155 = f.p.cam_omega / t153
  t156 = t124 * t6
  t157 = t156 ** (0.1e1 / 0.3e1)
  t159 = t61 / t157
  t161 = t155 * t159 / 0.2e1
  t162 = 0.135e1 <= t161
  t163 = 0.135e1 < t161
  t164 = f.my_piecewise3(t163, t161, 0.135e1)
  t165 = t164 ** 2
  t168 = t165 ** 2
  t171 = t168 * t165
  t174 = t168 ** 2
  t186 = t174 ** 2
  t190 = f.my_piecewise3(t163, 0.135e1, t161)
  t191 = 0.1e1 / t190
  t193 = jax.lax.erf(t191 / 0.2e1)
  t195 = t190 ** 2
  t196 = 0.1e1 / t195
  t198 = jnp.exp(-t196 / 0.4e1)
  t199 = t198 - 0.1e1
  t202 = t198 - 0.3e1 / 0.2e1 - 0.2e1 * t195 * t199
  t205 = 0.2e1 * t190 * t202 + t97 * t193
  t209 = f.my_piecewise3(t162, 0.1e1 / t165 / 0.36e2 - 0.1e1 / t168 / 0.960e3 + 0.1e1 / t171 / 0.26880e5 - 0.1e1 / t174 / 0.829440e6 + 0.1e1 / t174 / t165 / 0.28385280e8 - 0.1e1 / t174 / t168 / 0.1073479680e10 + 0.1e1 / t174 / t171 / 0.44590694400e11 - 0.1e1 / t186 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t190 * t205)
  t210 = t27 * t209
  t211 = t210 * t149
  t214 = f.my_piecewise3(t122, 0, -0.3e1 / 0.8e1 * t129 * t211)
  t215 = t6 ** 2
  t217 = t16 / t215
  t218 = t7 - t217
  t219 = f.my_piecewise5(t10, 0, t14, 0, t218)
  t222 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t219)
  t226 = t27 ** 2
  t227 = 0.1e1 / t226
  t231 = t26 * t227 * t116 * t54 / 0.8e1
  t232 = t71 * t70
  t233 = 0.1e1 / t232
  t238 = f.p.cam_omega / t58 / t57 * t65 * jnp.pi
  t239 = t28 * t32
  t240 = t54 ** 2
  t242 = t33 / t240
  t251 = t38 ** 2
  t255 = 0.1e1 / t49 / t48
  t259 = -0.19200000000000000000000000000000000000000000000000e3 * t36 / t40 / t38 / t37 * t50 + 0.11520000000000000000000000000000000000000000000000e4 * params.b * t35 * s0 / t251 / r0 * t255
  t266 = t61 / t63 / t62
  t272 = t238 * t239 * t242 * t259 / 0.4e1 - t60 * t266 * (t219 * t6 + t18 + 0.1e1) / 0.6e1
  t273 = f.my_piecewise3(t69, t272, 0)
  t276 = t74 * t70
  t277 = 0.1e1 / t276
  t280 = t74 * t232
  t281 = 0.1e1 / t280
  t285 = 0.1e1 / t80 / t70
  t289 = 0.1e1 / t80 / t232
  t293 = 0.1e1 / t80 / t276
  t297 = 0.1e1 / t80 / t280
  t301 = 0.1e1 / t92 / t70
  t305 = f.my_piecewise3(t69, 0, t272)
  t307 = t105 * t103
  t312 = 0.1e1 / t102 / t96
  t316 = t96 * t106
  t328 = f.my_piecewise3(t68, -t233 * t273 / 0.18e2 + t277 * t273 / 0.240e3 - t281 * t273 / 0.4480e4 + t285 * t273 / 0.103680e6 - t289 * t273 / 0.2838528e7 + t293 * t273 / 0.89456640e8 - t297 * t273 / 0.3185049600e10 + t301 * t273 / 0.126340300800e12, -0.8e1 / 0.3e1 * t305 * t112 - 0.8e1 / 0.3e1 * t96 * (-t307 * t305 + 0.2e1 * t305 * t109 + 0.2e1 * t96 * (t312 * t305 * t105 / 0.2e1 - 0.4e1 * t316 * t305 - t98 * t305 * t105)))
  t337 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t222 * t118 - t231 - 0.3e1 / 0.8e1 * t26 * t27 * t328 * t54 - 0.3e1 / 0.8e1 * t26 * t117 * t259)
  t339 = f.my_piecewise5(t14, 0, t10, 0, -t218)
  t342 = f.my_piecewise3(t125, 0, 0.4e1 / 0.3e1 * t126 * t339)
  t349 = t129 * t227 * t209 * t149 / 0.8e1
  t350 = t165 * t164
  t351 = 0.1e1 / t350
  t354 = t61 / t157 / t156
  t359 = t155 * t354 * (t339 * t6 + t123 + 0.1e1) / 0.6e1
  t360 = f.my_piecewise3(t163, -t359, 0)
  t363 = t168 * t164
  t364 = 0.1e1 / t363
  t367 = t168 * t350
  t368 = 0.1e1 / t367
  t372 = 0.1e1 / t174 / t164
  t376 = 0.1e1 / t174 / t350
  t380 = 0.1e1 / t174 / t363
  t384 = 0.1e1 / t174 / t367
  t388 = 0.1e1 / t186 / t164
  t392 = f.my_piecewise3(t163, 0, -t359)
  t394 = t198 * t196
  t399 = 0.1e1 / t195 / t190
  t403 = t190 * t199
  t415 = f.my_piecewise3(t162, -t351 * t360 / 0.18e2 + t364 * t360 / 0.240e3 - t368 * t360 / 0.4480e4 + t372 * t360 / 0.103680e6 - t376 * t360 / 0.2838528e7 + t380 * t360 / 0.89456640e8 - t384 * t360 / 0.3185049600e10 + t388 * t360 / 0.126340300800e12, -0.8e1 / 0.3e1 * t392 * t205 - 0.8e1 / 0.3e1 * t190 * (-t394 * t392 + 0.2e1 * t392 * t202 + 0.2e1 * t190 * (t399 * t392 * t198 / 0.2e1 - 0.4e1 * t403 * t392 - t191 * t392 * t198)))
  t421 = f.my_piecewise3(t122, 0, -0.3e1 / 0.8e1 * t5 * t342 * t211 - t349 - 0.3e1 / 0.8e1 * t129 * t27 * t415 * t149)
  vrho_0_ = t121 + t214 + t6 * (t337 + t421)
  t424 = -t7 - t217
  t425 = f.my_piecewise5(t10, 0, t14, 0, t424)
  t428 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t425)
  t436 = t60 * t266 * (t425 * t6 + t18 + 0.1e1) / 0.6e1
  t437 = f.my_piecewise3(t69, -t436, 0)
  t455 = f.my_piecewise3(t69, 0, -t436)
  t474 = f.my_piecewise3(t68, -t233 * t437 / 0.18e2 + t277 * t437 / 0.240e3 - t281 * t437 / 0.4480e4 + t285 * t437 / 0.103680e6 - t289 * t437 / 0.2838528e7 + t293 * t437 / 0.89456640e8 - t297 * t437 / 0.3185049600e10 + t301 * t437 / 0.126340300800e12, -0.8e1 / 0.3e1 * t455 * t112 - 0.8e1 / 0.3e1 * t96 * (-t307 * t455 + 0.2e1 * t455 * t109 + 0.2e1 * t96 * (t312 * t455 * t105 / 0.2e1 - 0.4e1 * t316 * t455 - t98 * t455 * t105)))
  t480 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t428 * t118 - t231 - 0.3e1 / 0.8e1 * t26 * t27 * t474 * t54)
  t482 = f.my_piecewise5(t14, 0, t10, 0, -t424)
  t485 = f.my_piecewise3(t125, 0, 0.4e1 / 0.3e1 * t126 * t482)
  t493 = f.p.cam_omega / t153 / t152 * t159 * jnp.pi
  t494 = t149 ** 2
  t496 = t33 / t494
  t505 = t133 ** 2
  t509 = 0.1e1 / t144 / t143
  t513 = -0.19200000000000000000000000000000000000000000000000e3 * t131 / t135 / t133 / t132 * t145 + 0.11520000000000000000000000000000000000000000000000e4 * params.b * t130 * s2 / t505 / r1 * t509
  t523 = t493 * t239 * t496 * t513 / 0.4e1 - t155 * t354 * (t482 * t6 + t123 + 0.1e1) / 0.6e1
  t524 = f.my_piecewise3(t163, t523, 0)
  t542 = f.my_piecewise3(t163, 0, t523)
  t561 = f.my_piecewise3(t162, -t351 * t524 / 0.18e2 + t364 * t524 / 0.240e3 - t368 * t524 / 0.4480e4 + t372 * t524 / 0.103680e6 - t376 * t524 / 0.2838528e7 + t380 * t524 / 0.89456640e8 - t384 * t524 / 0.3185049600e10 + t388 * t524 / 0.126340300800e12, -0.8e1 / 0.3e1 * t542 * t205 - 0.8e1 / 0.3e1 * t190 * (-t394 * t542 + 0.2e1 * t542 * t202 + 0.2e1 * t190 * (t399 * t542 * t198 / 0.2e1 - 0.4e1 * t403 * t542 - t191 * t542 * t198)))
  t570 = f.my_piecewise3(t122, 0, -0.3e1 / 0.8e1 * t5 * t485 * t211 - t349 - 0.3e1 / 0.8e1 * t129 * t27 * t561 * t149 - 0.3e1 / 0.8e1 * t129 * t210 * t513)
  vrho_1_ = t121 + t214 + t6 * (t480 + t570)
  t580 = 0.7200e2 * params.b * s0 * t51 - 0.432000e3 * t36 / t251 * t255
  t584 = t238 * t239 * t242 * t580 / 0.4e1
  t585 = f.my_piecewise3(t69, t584, 0)
  t603 = f.my_piecewise3(t69, 0, t584)
  t622 = f.my_piecewise3(t68, -t233 * t585 / 0.18e2 + t277 * t585 / 0.240e3 - t281 * t585 / 0.4480e4 + t285 * t585 / 0.103680e6 - t289 * t585 / 0.2838528e7 + t293 * t585 / 0.89456640e8 - t297 * t585 / 0.3185049600e10 + t301 * t585 / 0.126340300800e12, -0.8e1 / 0.3e1 * t603 * t112 - 0.8e1 / 0.3e1 * t96 * (-t307 * t603 + 0.2e1 * t603 * t109 + 0.2e1 * t96 * (t312 * t603 * t105 / 0.2e1 - 0.4e1 * t316 * t603 - t98 * t603 * t105)))
  t630 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * t622 * t54 - 0.3e1 / 0.8e1 * t26 * t117 * t580)
  vsigma_0_ = t6 * t630
  vsigma_1_ = 0.0e0
  t638 = 0.7200e2 * params.b * s2 * t146 - 0.432000e3 * t131 / t505 * t509
  t642 = t493 * t239 * t496 * t638 / 0.4e1
  t643 = f.my_piecewise3(t163, t642, 0)
  t661 = f.my_piecewise3(t163, 0, t642)
  t680 = f.my_piecewise3(t162, -t351 * t643 / 0.18e2 + t364 * t643 / 0.240e3 - t368 * t643 / 0.4480e4 + t372 * t643 / 0.103680e6 - t376 * t643 / 0.2838528e7 + t380 * t643 / 0.89456640e8 - t384 * t643 / 0.3185049600e10 + t388 * t643 / 0.126340300800e12, -0.8e1 / 0.3e1 * t661 * t205 - 0.8e1 / 0.3e1 * t190 * (-t394 * t661 + 0.2e1 * t661 * t202 + 0.2e1 * t190 * (t399 * t661 * t198 / 0.2e1 - 0.4e1 * t403 * t661 - t191 * t661 * t198)))
  t688 = f.my_piecewise3(t122, 0, -0.3e1 / 0.8e1 * t129 * t27 * t680 * t149 - 0.3e1 / 0.8e1 * t129 * t210 * t638)
  vsigma_2_ = t6 * t688
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

  params_gamma = 6.0

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  optx_f = lambda x: params_a + params_b * (params_gamma * x ** 2 / (1 + params_gamma * x ** 2)) ** 2

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_enhancement = lambda xs: optx_f(xs)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  ityh_k_GGA = lambda rs, z, xs: jnp.sqrt(9 * jnp.pi / (2 * X_FACTOR_C * ityh_enhancement(xs))) * f.n_spin(rs, z) ** (1 / 3)

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  ityh_aa = lambda rs, z, xs: f.p.cam_omega / (2 * ityh_k_GGA(rs, z, xs))

  ityh_attenuation = lambda a: attenuation_erf(a)

  ityh_f_aa = lambda rs, z, xs: ityh_attenuation(ityh_aa(rs, z, xs))

  ityh_f = lambda rs, z, xs: ityh_f_aa(rs, z, xs) * ityh_enhancement(xs)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, ityh_f, rs, zeta, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t3 ** 2
  t23 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t23
  t25 = 4 ** (0.1e1 / 0.3e1)
  t27 = s0 ** 2
  t28 = params.b * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = r0 ** 2
  t31 = t30 ** 2
  t36 = t29 ** 2
  t38 = t19 ** 2
  t43 = 0.1e1 + 0.60e1 * s0 * t36 / t38 / t30
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t46 = t29 / t19 / t31 / r0 * t45
  t49 = params.a + 0.7200e2 * t28 * t46
  t52 = jnp.pi * t20 * t24 * t25 / t49
  t53 = jnp.sqrt(t52)
  t55 = f.p.cam_omega / t53
  t56 = t11 * r0
  t57 = t56 ** (0.1e1 / 0.3e1)
  t59 = t29 / t57
  t61 = t55 * t59 / 0.2e1
  t62 = 0.135e1 <= t61
  t63 = 0.135e1 < t61
  t64 = f.my_piecewise3(t63, t61, 0.135e1)
  t65 = t64 ** 2
  t68 = t65 ** 2
  t71 = t68 * t65
  t74 = t68 ** 2
  t86 = t74 ** 2
  t90 = f.my_piecewise3(t63, 0.135e1, t61)
  t91 = jnp.sqrt(jnp.pi)
  t92 = 0.1e1 / t90
  t94 = jax.lax.erf(t92 / 0.2e1)
  t96 = t90 ** 2
  t97 = 0.1e1 / t96
  t99 = jnp.exp(-t97 / 0.4e1)
  t100 = t99 - 0.1e1
  t103 = t99 - 0.3e1 / 0.2e1 - 0.2e1 * t96 * t100
  t106 = 0.2e1 * t90 * t103 + t91 * t94
  t110 = f.my_piecewise3(t62, 0.1e1 / t65 / 0.36e2 - 0.1e1 / t68 / 0.960e3 + 0.1e1 / t71 / 0.26880e5 - 0.1e1 / t74 / 0.829440e6 + 0.1e1 / t74 / t65 / 0.28385280e8 - 0.1e1 / t74 / t68 / 0.1073479680e10 + 0.1e1 / t74 / t71 / 0.44590694400e11 - 0.1e1 / t86 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t90 * t106)
  t111 = t19 * t110
  t115 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t111 * t49)
  t121 = t65 * t64
  t122 = 0.1e1 / t121
  t127 = f.p.cam_omega / t53 / t52 * t59 * jnp.pi
  t128 = t20 * t24
  t129 = t49 ** 2
  t131 = t25 / t129
  t141 = t31 ** 2
  t145 = 0.1e1 / t44 / t43
  t149 = -0.38400000000000000000000000000000000000000000000000e3 * t28 * t29 / t19 / t31 / t30 * t45 + 0.46080000000000000000000000000000000000000000000000e4 * params.b * t27 * s0 / t141 / r0 * t145
  t160 = t127 * t128 * t131 * t149 / 0.4e1 - t55 * t29 / t57 / t56 * t11 / 0.6e1
  t161 = f.my_piecewise3(t63, t160, 0)
  t164 = t68 * t64
  t165 = 0.1e1 / t164
  t168 = t68 * t121
  t169 = 0.1e1 / t168
  t173 = 0.1e1 / t74 / t64
  t177 = 0.1e1 / t74 / t121
  t181 = 0.1e1 / t74 / t164
  t185 = 0.1e1 / t74 / t168
  t189 = 0.1e1 / t86 / t64
  t193 = f.my_piecewise3(t63, 0, t160)
  t195 = t99 * t97
  t200 = 0.1e1 / t96 / t90
  t204 = t90 * t100
  t216 = f.my_piecewise3(t62, -t122 * t161 / 0.18e2 + t165 * t161 / 0.240e3 - t169 * t161 / 0.4480e4 + t173 * t161 / 0.103680e6 - t177 * t161 / 0.2838528e7 + t181 * t161 / 0.89456640e8 - t185 * t161 / 0.3185049600e10 + t189 * t161 / 0.126340300800e12, -0.8e1 / 0.3e1 * t193 * t106 - 0.8e1 / 0.3e1 * t90 * (-t195 * t193 + 0.2e1 * t193 * t103 + 0.2e1 * t90 * (t200 * t193 * t99 / 0.2e1 - 0.4e1 * t204 * t193 - t92 * t193 * t99)))
  t225 = f.my_piecewise3(t2, 0, -t18 / t38 * t110 * t49 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t216 * t49 - 0.3e1 / 0.8e1 * t18 * t111 * t149)
  vrho_0_ = 0.2e1 * r0 * t225 + 0.2e1 * t115
  t235 = 0.14400e3 * params.b * s0 * t46 - 0.1728000e4 * t28 / t141 * t145
  t239 = t127 * t128 * t131 * t235 / 0.4e1
  t240 = f.my_piecewise3(t63, t239, 0)
  t258 = f.my_piecewise3(t63, 0, t239)
  t277 = f.my_piecewise3(t62, -t122 * t240 / 0.18e2 + t165 * t240 / 0.240e3 - t169 * t240 / 0.4480e4 + t173 * t240 / 0.103680e6 - t177 * t240 / 0.2838528e7 + t181 * t240 / 0.89456640e8 - t185 * t240 / 0.3185049600e10 + t189 * t240 / 0.126340300800e12, -0.8e1 / 0.3e1 * t258 * t106 - 0.8e1 / 0.3e1 * t90 * (-t195 * t258 + 0.2e1 * t258 * t103 + 0.2e1 * t90 * (t200 * t258 * t99 / 0.2e1 - 0.4e1 * t204 * t258 - t92 * t258 * t99)))
  t285 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t277 * t49 - 0.3e1 / 0.8e1 * t18 * t111 * t235)
  vsigma_0_ = 0.2e1 * r0 * t285
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
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t22 = t3 ** 2
  t25 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t27 = 4 ** (0.1e1 / 0.3e1)
  t29 = s0 ** 2
  t30 = params.b * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = r0 ** 2
  t33 = t32 ** 2
  t36 = 0.1e1 / t19 / t33 / r0
  t38 = t31 ** 2
  t44 = 0.1e1 + 0.60e1 * s0 * t38 / t20 / t32
  t45 = t44 ** 2
  t46 = 0.1e1 / t45
  t47 = t31 * t36 * t46
  t50 = params.a + 0.7200e2 * t30 * t47
  t53 = jnp.pi * t22 * t26 * t27 / t50
  t54 = jnp.sqrt(t53)
  t56 = f.p.cam_omega / t54
  t57 = t11 * r0
  t58 = t57 ** (0.1e1 / 0.3e1)
  t60 = t31 / t58
  t62 = t56 * t60 / 0.2e1
  t63 = 0.135e1 <= t62
  t64 = 0.135e1 < t62
  t65 = f.my_piecewise3(t64, t62, 0.135e1)
  t66 = t65 ** 2
  t69 = t66 ** 2
  t70 = 0.1e1 / t69
  t72 = t69 * t66
  t73 = 0.1e1 / t72
  t75 = t69 ** 2
  t76 = 0.1e1 / t75
  t79 = 0.1e1 / t75 / t66
  t82 = 0.1e1 / t75 / t69
  t85 = 0.1e1 / t75 / t72
  t87 = t75 ** 2
  t88 = 0.1e1 / t87
  t91 = f.my_piecewise3(t64, 0.135e1, t62)
  t92 = jnp.sqrt(jnp.pi)
  t93 = 0.1e1 / t91
  t95 = jax.lax.erf(t93 / 0.2e1)
  t97 = t91 ** 2
  t98 = 0.1e1 / t97
  t100 = jnp.exp(-t98 / 0.4e1)
  t101 = t100 - 0.1e1
  t104 = t100 - 0.3e1 / 0.2e1 - 0.2e1 * t97 * t101
  t107 = 0.2e1 * t91 * t104 + t92 * t95
  t111 = f.my_piecewise3(t63, 0.1e1 / t66 / 0.36e2 - t70 / 0.960e3 + t73 / 0.26880e5 - t76 / 0.829440e6 + t79 / 0.28385280e8 - t82 / 0.1073479680e10 + t85 / 0.44590694400e11 - t88 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t91 * t107)
  t112 = t21 * t111
  t116 = t66 * t65
  t117 = 0.1e1 / t116
  t120 = f.p.cam_omega / t54 / t53
  t122 = t120 * t60 * jnp.pi
  t123 = t22 * t26
  t124 = t50 ** 2
  t125 = 0.1e1 / t124
  t126 = t27 * t125
  t131 = t31 / t19 / t33 / t32 * t46
  t135 = params.b * t29 * s0
  t136 = t33 ** 2
  t140 = 0.1e1 / t45 / t44
  t141 = 0.1e1 / t136 / r0 * t140
  t144 = -0.38400000000000000000000000000000000000000000000000e3 * t30 * t131 + 0.46080000000000000000000000000000000000000000000000e4 * t135 * t141
  t151 = t31 / t58 / t57
  t155 = t122 * t123 * t126 * t144 / 0.4e1 - t56 * t151 * t11 / 0.6e1
  t156 = f.my_piecewise3(t64, t155, 0)
  t159 = t69 * t65
  t160 = 0.1e1 / t159
  t163 = t69 * t116
  t164 = 0.1e1 / t163
  t168 = 0.1e1 / t75 / t65
  t172 = 0.1e1 / t75 / t116
  t176 = 0.1e1 / t75 / t159
  t180 = 0.1e1 / t75 / t163
  t184 = 0.1e1 / t87 / t65
  t188 = f.my_piecewise3(t64, 0, t155)
  t190 = t100 * t98
  t195 = 0.1e1 / t97 / t91
  t199 = t91 * t101
  t204 = t195 * t188 * t100 / 0.2e1 - 0.4e1 * t199 * t188 - t93 * t188 * t100
  t207 = 0.2e1 * t188 * t104 - t190 * t188 + 0.2e1 * t91 * t204
  t211 = f.my_piecewise3(t63, -t117 * t156 / 0.18e2 + t160 * t156 / 0.240e3 - t164 * t156 / 0.4480e4 + t168 * t156 / 0.103680e6 - t172 * t156 / 0.2838528e7 + t176 * t156 / 0.89456640e8 - t180 * t156 / 0.3185049600e10 + t184 * t156 / 0.126340300800e12, -0.8e1 / 0.3e1 * t188 * t107 - 0.8e1 / 0.3e1 * t91 * t207)
  t212 = t19 * t211
  t216 = t19 * t111
  t221 = f.my_piecewise3(t2, 0, -t18 * t112 * t50 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t212 * t50 - 0.3e1 / 0.8e1 * t18 * t216 * t144)
  t236 = t156 ** 2
  t239 = jnp.pi ** 2
  t241 = t25 ** 2
  t242 = 0.1e1 / t241
  t243 = t27 ** 2
  t252 = f.p.cam_omega / t54 / t3 / t242 / t243 / t125 * t60 / 0.3e1
  t253 = t3 * t242
  t254 = t124 ** 2
  t255 = 0.1e1 / t254
  t256 = t243 * t255
  t257 = t144 ** 2
  t263 = t120 * t151 * jnp.pi
  t264 = t123 * t27
  t271 = 0.1e1 / t124 / t50
  t272 = t27 * t271
  t277 = t32 * r0
  t285 = t136 * t32
  t290 = t29 ** 2
  t295 = t45 ** 2
  t296 = 0.1e1 / t295
  t301 = 0.24320000000000000000000000000000000000000000000000e4 * t30 * t31 / t19 / t33 / t277 * t46 - 0.66048000000000000000000000000000000000000000000000e5 * t135 / t285 * t140 + 0.22118400000000000000000000000000000000000000000000e6 * params.b * t290 / t20 / t136 / t33 * t296 * t38
  t306 = t11 ** 2
  t314 = 0.9e1 / 0.8e1 * t252 * t253 * t256 * t257 - t263 * t264 * t125 * t144 * t11 / 0.6e1 - t122 * t123 * t272 * t257 / 0.2e1 + t122 * t123 * t126 * t301 / 0.4e1 + 0.2e1 / 0.9e1 * t56 * t31 / t58 / t32
  t315 = f.my_piecewise3(t64, t314, 0)
  t343 = 0.1e1 / t87 / t66
  t348 = t70 * t236 / 0.6e1 - t117 * t315 / 0.18e2 - t73 * t236 / 0.48e2 + t160 * t315 / 0.240e3 + t76 * t236 / 0.640e3 - t164 * t315 / 0.4480e4 - t79 * t236 / 0.11520e5 + t168 * t315 / 0.103680e6 + t82 * t236 / 0.258048e6 - t172 * t315 / 0.2838528e7 - t85 * t236 / 0.6881280e7 + t176 * t315 / 0.89456640e8 + t88 * t236 / 0.212336640e9 - t180 * t315 / 0.3185049600e10 - t343 * t236 / 0.7431782400e10 + t184 * t315 / 0.126340300800e12
  t349 = f.my_piecewise3(t64, 0, t314)
  t354 = t97 ** 2
  t356 = 0.1e1 / t354 / t91
  t357 = t188 ** 2
  t361 = t100 * t195
  t369 = 0.1e1 / t354
  t377 = 0.1e1 / t354 / t97
  t396 = f.my_piecewise3(t63, t348, -0.8e1 / 0.3e1 * t349 * t107 - 0.16e2 / 0.3e1 * t188 * t207 - 0.8e1 / 0.3e1 * t91 * (-t356 * t357 * t100 / 0.2e1 + 0.2e1 * t361 * t357 - t190 * t349 + 0.2e1 * t349 * t104 + 0.4e1 * t188 * t204 + 0.2e1 * t91 * (-0.2e1 * t369 * t357 * t100 + t195 * t349 * t100 / 0.2e1 + t377 * t357 * t100 / 0.4e1 - 0.4e1 * t357 * t101 - t98 * t357 * t100 - 0.4e1 * t199 * t349 - t93 * t349 * t100)))
  t408 = f.my_piecewise3(t2, 0, t18 / t20 / r0 * t111 * t50 / 0.12e2 - t18 * t21 * t211 * t50 / 0.4e1 - t18 * t112 * t144 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t19 * t396 * t50 - 0.3e1 / 0.4e1 * t18 * t212 * t144 - 0.3e1 / 0.8e1 * t18 * t216 * t301)
  v2rho2_0_ = 0.2e1 * r0 * t408 + 0.4e1 * t221
  t411 = params.b * s0
  t415 = 0.1e1 / t136 * t140
  t418 = 0.14400e3 * t411 * t47 - 0.1728000e4 * t30 * t415
  t422 = t122 * t123 * t126 * t418 / 0.4e1
  t423 = f.my_piecewise3(t64, t422, 0)
  t441 = f.my_piecewise3(t64, 0, t422)
  t453 = t195 * t441 * t100 / 0.2e1 - 0.4e1 * t199 * t441 - t93 * t441 * t100
  t456 = 0.2e1 * t441 * t104 - t190 * t441 + 0.2e1 * t91 * t453
  t460 = f.my_piecewise3(t63, -t117 * t423 / 0.18e2 + t160 * t423 / 0.240e3 - t164 * t423 / 0.4480e4 + t168 * t423 / 0.103680e6 - t172 * t423 / 0.2838528e7 + t176 * t423 / 0.89456640e8 - t180 * t423 / 0.3185049600e10 + t184 * t423 / 0.126340300800e12, -0.8e1 / 0.3e1 * t441 * t107 - 0.8e1 / 0.3e1 * t91 * t456)
  t461 = t19 * t460
  t468 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t216 * t418 - 0.3e1 / 0.8e1 * t18 * t461 * t50)
  t503 = -0.76800000000000000000000000000000000000000000000000e3 * t411 * t131 + 0.23040000000000000000000000000000000000000000000000e5 * t30 * t141 - 0.82944000000000000000000000000000000000000000000000e5 * t135 / t20 / t136 / t277 * t296 * t38
  t508 = 0.9e1 / 0.8e1 * t252 * t253 * t243 * t255 * t418 * t144 - t263 * t264 * t125 * t418 * t11 / 0.12e2 - t122 * t264 * t271 * t418 * t144 / 0.2e1 + t122 * t123 * t126 * t503 / 0.4e1
  t509 = f.my_piecewise3(t64, t508, 0)
  t547 = t70 * t423 * t156 / 0.6e1 - t117 * t509 / 0.18e2 - t73 * t423 * t156 / 0.48e2 + t160 * t509 / 0.240e3 + t76 * t423 * t156 / 0.640e3 - t164 * t509 / 0.4480e4 - t79 * t423 * t156 / 0.11520e5 + t168 * t509 / 0.103680e6 + t82 * t423 * t156 / 0.258048e6 - t172 * t509 / 0.2838528e7 - t85 * t423 * t156 / 0.6881280e7 + t176 * t509 / 0.89456640e8 + t88 * t423 * t156 / 0.212336640e9 - t180 * t509 / 0.3185049600e10 - t343 * t423 * t156 / 0.7431782400e10 + t184 * t509 / 0.126340300800e12
  t548 = f.my_piecewise3(t64, 0, t508)
  t553 = t100 * t441
  t567 = t100 * t188
  t592 = f.my_piecewise3(t63, t547, -0.8e1 / 0.3e1 * t548 * t107 - 0.8e1 / 0.3e1 * t441 * t207 - 0.8e1 / 0.3e1 * t188 * t456 - 0.8e1 / 0.3e1 * t91 * (-t356 * t188 * t553 / 0.2e1 + 0.2e1 * t361 * t441 * t188 - t190 * t548 + 0.2e1 * t548 * t104 + 0.2e1 * t441 * t204 + 0.2e1 * t188 * t453 + 0.2e1 * t91 * (-0.2e1 * t369 * t441 * t567 + t195 * t548 * t100 / 0.2e1 + t377 * t441 * t567 / 0.4e1 - 0.4e1 * t188 * t101 * t441 - t98 * t188 * t553 - 0.4e1 * t199 * t548 - t93 * t548 * t100)))
  t610 = f.my_piecewise3(t2, 0, -t18 * t21 * t460 * t50 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t592 * t50 - 0.3e1 / 0.8e1 * t18 * t461 * t144 - t18 * t112 * t418 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t212 * t418 - 0.3e1 / 0.8e1 * t18 * t216 * t503)
  v2rhosigma_0_ = 0.2e1 * r0 * t610 + 0.2e1 * t468
  t613 = t423 ** 2
  t616 = t418 ** 2
  t637 = 0.14400e3 * params.b * t31 * t36 * t46 - 0.6912000e4 * t411 * t415 + 0.311040000e5 * t30 / t20 / t285 * t296 * t38
  t642 = 0.9e1 / 0.8e1 * t252 * t253 * t256 * t616 - t122 * t123 * t272 * t616 / 0.2e1 + t122 * t123 * t126 * t637 / 0.4e1
  t643 = f.my_piecewise3(t64, t642, 0)
  t674 = t70 * t613 / 0.6e1 - t117 * t643 / 0.18e2 - t73 * t613 / 0.48e2 + t160 * t643 / 0.240e3 + t76 * t613 / 0.640e3 - t164 * t643 / 0.4480e4 - t79 * t613 / 0.11520e5 + t168 * t643 / 0.103680e6 + t82 * t613 / 0.258048e6 - t172 * t643 / 0.2838528e7 - t85 * t613 / 0.6881280e7 + t176 * t643 / 0.89456640e8 + t88 * t613 / 0.212336640e9 - t180 * t643 / 0.3185049600e10 - t343 * t613 / 0.7431782400e10 + t184 * t643 / 0.126340300800e12
  t675 = f.my_piecewise3(t64, 0, t642)
  t680 = t441 ** 2
  t715 = f.my_piecewise3(t63, t674, -0.8e1 / 0.3e1 * t675 * t107 - 0.16e2 / 0.3e1 * t441 * t456 - 0.8e1 / 0.3e1 * t91 * (-t356 * t680 * t100 / 0.2e1 + 0.2e1 * t361 * t680 - t190 * t675 + 0.2e1 * t675 * t104 + 0.4e1 * t441 * t453 + 0.2e1 * t91 * (-0.2e1 * t369 * t680 * t100 + t195 * t675 * t100 / 0.2e1 + t377 * t680 * t100 / 0.4e1 - 0.4e1 * t680 * t101 - t98 * t680 * t100 - 0.4e1 * t199 * t675 - t93 * t675 * t100)))
  t727 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t715 * t50 - 0.3e1 / 0.4e1 * t18 * t461 * t418 - 0.3e1 / 0.8e1 * t18 * t216 * t637)
  v2sigma2_0_ = 0.2e1 * r0 * t727
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / r0
  t23 = t3 ** 2
  t26 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t26
  t28 = 4 ** (0.1e1 / 0.3e1)
  t30 = s0 ** 2
  t31 = params.b * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = r0 ** 2
  t34 = t33 ** 2
  t35 = t34 * r0
  t39 = t32 ** 2
  t42 = 0.1e1 / t20 / t33
  t45 = 0.1e1 + 0.60e1 * s0 * t39 * t42
  t46 = t45 ** 2
  t47 = 0.1e1 / t46
  t51 = params.a + 0.7200e2 * t31 * t32 / t19 / t35 * t47
  t54 = jnp.pi * t23 * t27 * t28 / t51
  t55 = jnp.sqrt(t54)
  t57 = f.p.cam_omega / t55
  t58 = t11 * r0
  t59 = t58 ** (0.1e1 / 0.3e1)
  t60 = 0.1e1 / t59
  t61 = t32 * t60
  t63 = t57 * t61 / 0.2e1
  t64 = 0.135e1 <= t63
  t65 = 0.135e1 < t63
  t66 = f.my_piecewise3(t65, t63, 0.135e1)
  t67 = t66 ** 2
  t70 = t67 ** 2
  t71 = 0.1e1 / t70
  t73 = t70 * t67
  t74 = 0.1e1 / t73
  t76 = t70 ** 2
  t77 = 0.1e1 / t76
  t80 = 0.1e1 / t76 / t67
  t83 = 0.1e1 / t76 / t70
  t86 = 0.1e1 / t76 / t73
  t88 = t76 ** 2
  t89 = 0.1e1 / t88
  t92 = f.my_piecewise3(t65, 0.135e1, t63)
  t93 = jnp.sqrt(jnp.pi)
  t94 = 0.1e1 / t92
  t96 = jnp.erf(t94 / 0.2e1)
  t98 = t92 ** 2
  t99 = 0.1e1 / t98
  t101 = jnp.exp(-t99 / 0.4e1)
  t102 = t101 - 0.1e1
  t105 = t101 - 0.3e1 / 0.2e1 - 0.2e1 * t98 * t102
  t108 = 0.2e1 * t92 * t105 + t93 * t96
  t112 = f.my_piecewise3(t64, 0.1e1 / t67 / 0.36e2 - t71 / 0.960e3 + t74 / 0.26880e5 - t77 / 0.829440e6 + t80 / 0.28385280e8 - t83 / 0.1073479680e10 + t86 / 0.44590694400e11 - t89 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t92 * t108)
  t113 = t22 * t112
  t117 = 0.1e1 / t20
  t118 = t67 * t66
  t119 = 0.1e1 / t118
  t122 = f.p.cam_omega / t55 / t54
  t124 = t122 * t61 * jnp.pi
  t125 = t23 * t27
  t126 = t51 ** 2
  t127 = 0.1e1 / t126
  t128 = t28 * t127
  t137 = params.b * t30 * s0
  t138 = t34 ** 2
  t142 = 0.1e1 / t46 / t45
  t146 = -0.38400000000000000000000000000000000000000000000000e3 * t31 * t32 / t19 / t34 / t33 * t47 + 0.46080000000000000000000000000000000000000000000000e4 * t137 / t138 / r0 * t142
  t153 = t32 / t59 / t58
  t157 = t124 * t125 * t128 * t146 / 0.4e1 - t57 * t153 * t11 / 0.6e1
  t158 = f.my_piecewise3(t65, t157, 0)
  t161 = t70 * t66
  t162 = 0.1e1 / t161
  t165 = t70 * t118
  t166 = 0.1e1 / t165
  t170 = 0.1e1 / t76 / t66
  t174 = 0.1e1 / t76 / t118
  t178 = 0.1e1 / t76 / t161
  t182 = 0.1e1 / t76 / t165
  t186 = 0.1e1 / t88 / t66
  t190 = f.my_piecewise3(t65, 0, t157)
  t192 = t101 * t99
  t196 = t98 * t92
  t197 = 0.1e1 / t196
  t201 = t92 * t102
  t206 = t197 * t190 * t101 / 0.2e1 - 0.4e1 * t201 * t190 - t94 * t190 * t101
  t209 = 0.2e1 * t190 * t105 - t192 * t190 + 0.2e1 * t92 * t206
  t213 = f.my_piecewise3(t64, -t119 * t158 / 0.18e2 + t162 * t158 / 0.240e3 - t166 * t158 / 0.4480e4 + t170 * t158 / 0.103680e6 - t174 * t158 / 0.2838528e7 + t178 * t158 / 0.89456640e8 - t182 * t158 / 0.3185049600e10 + t186 * t158 / 0.126340300800e12, -0.8e1 / 0.3e1 * t190 * t108 - 0.8e1 / 0.3e1 * t92 * t209)
  t214 = t117 * t213
  t218 = t117 * t112
  t222 = t158 ** 2
  t225 = jnp.pi ** 2
  t227 = t26 ** 2
  t228 = 0.1e1 / t227
  t229 = t28 ** 2
  t236 = f.p.cam_omega / t55 / t225 / t3 / t228 / t229 / t127 / 0.3e1
  t238 = t236 * t61 * t225
  t239 = t3 * t228
  t240 = t126 ** 2
  t241 = 0.1e1 / t240
  t243 = t146 ** 2
  t249 = t122 * t153 * jnp.pi
  t250 = t125 * t28
  t251 = t127 * t146
  t257 = 0.1e1 / t126 / t51
  t263 = t33 * r0
  t276 = t30 ** 2
  t277 = params.b * t276
  t281 = t46 ** 2
  t282 = 0.1e1 / t281
  t287 = 0.24320000000000000000000000000000000000000000000000e4 * t31 * t32 / t19 / t34 / t263 * t47 - 0.66048000000000000000000000000000000000000000000000e5 * t137 / t138 / t33 * t142 + 0.22118400000000000000000000000000000000000000000000e6 * t277 / t20 / t138 / t34 * t282 * t39
  t292 = t11 ** 2
  t296 = t32 / t59 / t292 / t33
  t300 = 0.9e1 / 0.8e1 * t238 * t239 * t229 * t241 * t243 - t249 * t250 * t251 * t11 / 0.6e1 - t124 * t125 * t28 * t257 * t243 / 0.2e1 + t124 * t125 * t128 * t287 / 0.4e1 + 0.2e1 / 0.9e1 * t57 * t296 * t292
  t301 = f.my_piecewise3(t65, t300, 0)
  t329 = 0.1e1 / t88 / t67
  t334 = t71 * t222 / 0.6e1 - t119 * t301 / 0.18e2 - t74 * t222 / 0.48e2 + t162 * t301 / 0.240e3 + t77 * t222 / 0.640e3 - t166 * t301 / 0.4480e4 - t80 * t222 / 0.11520e5 + t170 * t301 / 0.103680e6 + t83 * t222 / 0.258048e6 - t174 * t301 / 0.2838528e7 - t86 * t222 / 0.6881280e7 + t178 * t301 / 0.89456640e8 + t89 * t222 / 0.212336640e9 - t182 * t301 / 0.3185049600e10 - t329 * t222 / 0.7431782400e10 + t186 * t301 / 0.126340300800e12
  t335 = f.my_piecewise3(t65, 0, t300)
  t340 = t98 ** 2
  t342 = 0.1e1 / t340 / t92
  t343 = t190 ** 2
  t347 = t101 * t197
  t355 = 0.1e1 / t340
  t363 = 0.1e1 / t340 / t98
  t375 = -0.2e1 * t355 * t343 * t101 + t197 * t335 * t101 / 0.2e1 + t363 * t343 * t101 / 0.4e1 - 0.4e1 * t343 * t102 - t99 * t343 * t101 - 0.4e1 * t201 * t335 - t94 * t335 * t101
  t378 = -t342 * t343 * t101 / 0.2e1 + 0.2e1 * t347 * t343 - t192 * t335 + 0.2e1 * t335 * t105 + 0.4e1 * t190 * t206 + 0.2e1 * t92 * t375
  t382 = f.my_piecewise3(t64, t334, -0.8e1 / 0.3e1 * t335 * t108 - 0.16e2 / 0.3e1 * t190 * t209 - 0.8e1 / 0.3e1 * t92 * t378)
  t383 = t19 * t382
  t387 = t19 * t213
  t391 = t19 * t112
  t396 = f.my_piecewise3(t2, 0, t18 * t113 * t51 / 0.12e2 - t18 * t214 * t51 / 0.4e1 - t18 * t218 * t146 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t383 * t51 - 0.3e1 / 0.4e1 * t18 * t387 * t146 - 0.3e1 / 0.8e1 * t18 * t391 * t287)
  t419 = t222 * t158
  t440 = t225 ** 2
  t450 = t243 * t146
  t457 = t239 * t229
  t521 = t138 ** 2
  t530 = -0.17834666666666666666666666666666666666666666666667e5 * t31 * t32 / t19 / t138 * t47 + 0.81612800000000000000000000000000000000000000000000e6 * t137 / t138 / t263 * t142 - 0.59719680000000000000000000000000000000000000000000e7 * t277 / t20 / t138 / t35 * t282 * t39 + 0.28311552000000000000000000000000000000000000000000e8 * params.b * t276 * s0 / t19 / t521 / t281 / t45 * t32
  t535 = t292 * t11
  t543 = 0.15e2 / 0.16e2 * f.p.cam_omega / t55 / t257 * t32 * t60 / t240 / t126 * t450 - 0.9e1 / 0.8e1 * t236 * t153 * t225 * t457 * t241 * t243 * t11 - 0.27e2 / 0.4e1 * t238 * t239 * t229 / t240 / t51 * t450 + 0.27e2 / 0.8e1 * t238 * t457 * t241 * t146 * t287 + t122 * t296 * jnp.pi * t250 * t251 * t292 / 0.3e1 + t249 * t250 * t257 * t243 * t11 / 0.2e1 - t249 * t250 * t127 * t287 * t11 / 0.4e1 + 0.3e1 / 0.2e1 * t124 * t125 * t28 * t241 * t450 - 0.3e1 / 0.2e1 * t124 * t250 * t257 * t146 * t287 + t124 * t125 * t128 * t530 / 0.4e1 - 0.14e2 / 0.27e2 * t57 * t32 / t59 / t263
  t544 = f.my_piecewise3(t65, t543, 0)
  t553 = -t186 * t419 / 0.13271040e8 + t89 * t158 * t301 / 0.70778880e8 + t182 * t419 / 0.491520e6 - t86 * t158 * t301 / 0.2293760e7 - t178 * t419 / 0.21504e5 + t83 * t158 * t301 / 0.86016e5 + t174 * t419 / 0.1152e4 - t80 * t158 * t301 / 0.3840e4 + t186 * t544 / 0.126340300800e12 - t182 * t544 / 0.3185049600e10 + t178 * t544 / 0.89456640e8 - t174 * t544 / 0.2838528e7
  t584 = t170 * t544 / 0.103680e6 - t166 * t544 / 0.4480e4 + t162 * t544 / 0.240e3 - t119 * t544 / 0.18e2 + 0.1e1 / t88 / t118 * t419 / 0.412876800e9 - t329 * t158 * t301 / 0.2477260800e10 - t170 * t419 / 0.80e2 + 0.3e1 / 0.640e3 * t77 * t158 * t301 + t166 * t419 / 0.8e1 - t74 * t158 * t301 / 0.16e2 - 0.2e1 / 0.3e1 * t162 * t419 + t71 * t158 * t301 / 0.2e1
  t586 = f.my_piecewise3(t65, 0, t543)
  t593 = t343 * t190
  t598 = t101 * t335
  t601 = t340 ** 2
  t659 = f.my_piecewise3(t64, t553 + t584, -0.8e1 / 0.3e1 * t586 * t108 - 0.8e1 * t335 * t209 - 0.8e1 * t190 * t378 - 0.8e1 / 0.3e1 * t92 * (0.7e1 / 0.2e1 * t363 * t593 * t101 - 0.3e1 / 0.2e1 * t342 * t190 * t598 - 0.1e1 / t601 * t593 * t101 / 0.4e1 - 0.6e1 * t101 * t355 * t593 + 0.6e1 * t347 * t190 * t335 - t192 * t586 + 0.2e1 * t586 * t105 + 0.6e1 * t335 * t206 + 0.6e1 * t190 * t375 + 0.2e1 * t92 * (0.15e2 / 0.2e1 * t342 * t593 * t101 - 0.6e1 * t355 * t190 * t598 - 0.5e1 / 0.2e1 / t340 / t196 * t593 * t101 + t197 * t586 * t101 / 0.2e1 + 0.3e1 / 0.4e1 * t363 * t335 * t190 * t101 + 0.1e1 / t601 / t92 * t593 * t101 / 0.8e1 - 0.12e2 * t190 * t102 * t335 - 0.3e1 * t99 * t190 * t598 - 0.4e1 * t201 * t586 - t94 * t586 * t101)))
  t674 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t42 * t112 * t51 + t18 * t22 * t213 * t51 / 0.4e1 + t18 * t113 * t146 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t117 * t382 * t51 - 0.3e1 / 0.4e1 * t18 * t214 * t146 - 0.3e1 / 0.8e1 * t18 * t218 * t287 - 0.3e1 / 0.8e1 * t18 * t19 * t659 * t51 - 0.9e1 / 0.8e1 * t18 * t383 * t146 - 0.9e1 / 0.8e1 * t18 * t387 * t287 - 0.3e1 / 0.8e1 * t18 * t391 * t530)
  v3rho3_0_ = 0.2e1 * r0 * t674 + 0.6e1 * t396

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** 2
  t20 = r0 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t23 = 0.1e1 / t21 / t19
  t24 = t3 ** 2
  t26 = 0.1e1 / jnp.pi
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = 0.1e1 / t27
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = t28 * t29
  t31 = s0 ** 2
  t32 = params.b * t31
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t19 ** 2
  t35 = t34 * r0
  t39 = t33 ** 2
  t43 = 0.1e1 + 0.60e1 * s0 * t39 * t23
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t49 = params.a + 0.7200e2 * t32 * t33 / t20 / t35 * t45
  t52 = jnp.pi * t24 * t30 / t49
  t53 = jnp.sqrt(t52)
  t55 = f.p.cam_omega / t53
  t56 = t11 * r0
  t57 = t56 ** (0.1e1 / 0.3e1)
  t58 = 0.1e1 / t57
  t59 = t33 * t58
  t61 = t55 * t59 / 0.2e1
  t62 = 0.135e1 <= t61
  t63 = 0.135e1 < t61
  t64 = f.my_piecewise3(t63, t61, 0.135e1)
  t65 = t64 ** 2
  t68 = t65 ** 2
  t69 = 0.1e1 / t68
  t71 = t68 * t65
  t72 = 0.1e1 / t71
  t74 = t68 ** 2
  t75 = 0.1e1 / t74
  t78 = 0.1e1 / t74 / t65
  t81 = 0.1e1 / t74 / t68
  t84 = 0.1e1 / t74 / t71
  t86 = t74 ** 2
  t87 = 0.1e1 / t86
  t90 = f.my_piecewise3(t63, 0.135e1, t61)
  t91 = jnp.sqrt(jnp.pi)
  t92 = 0.1e1 / t90
  t94 = jnp.erf(t92 / 0.2e1)
  t96 = t90 ** 2
  t97 = 0.1e1 / t96
  t99 = jnp.exp(-t97 / 0.4e1)
  t100 = t99 - 0.1e1
  t103 = t99 - 0.3e1 / 0.2e1 - 0.2e1 * t96 * t100
  t106 = 0.2e1 * t90 * t103 + t91 * t94
  t110 = f.my_piecewise3(t62, 0.1e1 / t65 / 0.36e2 - t69 / 0.960e3 + t72 / 0.26880e5 - t75 / 0.829440e6 + t78 / 0.28385280e8 - t81 / 0.1073479680e10 + t84 / 0.44590694400e11 - t87 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t90 * t106)
  t111 = t23 * t110
  t116 = 0.1e1 / t21 / r0
  t117 = t65 * t64
  t118 = 0.1e1 / t117
  t121 = f.p.cam_omega / t53 / t52
  t123 = t121 * t59 * jnp.pi
  t124 = t24 * t28
  t125 = t49 ** 2
  t126 = 0.1e1 / t125
  t127 = t29 * t126
  t128 = t34 * t19
  t136 = params.b * t31 * s0
  t137 = t34 ** 2
  t138 = t137 * r0
  t141 = 0.1e1 / t44 / t43
  t145 = -0.38400000000000000000000000000000000000000000000000e3 * t32 * t33 / t20 / t128 * t45 + 0.46080000000000000000000000000000000000000000000000e4 * t136 / t138 * t141
  t151 = 0.1e1 / t57 / t56
  t152 = t33 * t151
  t156 = t123 * t124 * t127 * t145 / 0.4e1 - t55 * t152 * t11 / 0.6e1
  t157 = f.my_piecewise3(t63, t156, 0)
  t160 = t68 * t64
  t161 = 0.1e1 / t160
  t164 = t68 * t117
  t165 = 0.1e1 / t164
  t169 = 0.1e1 / t74 / t64
  t173 = 0.1e1 / t74 / t117
  t177 = 0.1e1 / t74 / t160
  t181 = 0.1e1 / t74 / t164
  t185 = 0.1e1 / t86 / t64
  t189 = f.my_piecewise3(t63, 0, t156)
  t191 = t99 * t97
  t195 = t96 * t90
  t196 = 0.1e1 / t195
  t200 = t90 * t100
  t205 = t196 * t189 * t99 / 0.2e1 - 0.4e1 * t200 * t189 - t92 * t189 * t99
  t208 = 0.2e1 * t189 * t103 - t191 * t189 + 0.2e1 * t90 * t205
  t212 = f.my_piecewise3(t62, -t118 * t157 / 0.18e2 + t161 * t157 / 0.240e3 - t165 * t157 / 0.4480e4 + t169 * t157 / 0.103680e6 - t173 * t157 / 0.2838528e7 + t177 * t157 / 0.89456640e8 - t181 * t157 / 0.3185049600e10 + t185 * t157 / 0.126340300800e12, -0.8e1 / 0.3e1 * t189 * t106 - 0.8e1 / 0.3e1 * t90 * t208)
  t213 = t116 * t212
  t217 = t116 * t110
  t221 = 0.1e1 / t21
  t222 = t157 ** 2
  t225 = jnp.pi ** 2
  t227 = t27 ** 2
  t228 = 0.1e1 / t227
  t229 = t29 ** 2
  t230 = t228 * t229
  t236 = f.p.cam_omega / t53 / t225 / t3 / t230 / t126 / 0.3e1
  t238 = t236 * t59 * t225
  t239 = t3 * t228
  t240 = t125 ** 2
  t241 = 0.1e1 / t240
  t242 = t229 * t241
  t243 = t145 ** 2
  t249 = t121 * t152 * jnp.pi
  t250 = t124 * t29
  t251 = t126 * t145
  t256 = t125 * t49
  t257 = 0.1e1 / t256
  t258 = t29 * t257
  t263 = t19 * r0
  t276 = t31 ** 2
  t277 = params.b * t276
  t278 = t137 * t34
  t281 = t44 ** 2
  t282 = 0.1e1 / t281
  t287 = 0.24320000000000000000000000000000000000000000000000e4 * t32 * t33 / t20 / t34 / t263 * t45 - 0.66048000000000000000000000000000000000000000000000e5 * t136 / t137 / t19 * t141 + 0.22118400000000000000000000000000000000000000000000e6 * t277 / t21 / t278 * t282 * t39
  t292 = t11 ** 2
  t296 = t33 / t57 / t292 / t19
  t300 = 0.9e1 / 0.8e1 * t238 * t239 * t242 * t243 - t249 * t250 * t251 * t11 / 0.6e1 - t123 * t124 * t258 * t243 / 0.2e1 + t123 * t124 * t127 * t287 / 0.4e1 + 0.2e1 / 0.9e1 * t55 * t296 * t292
  t301 = f.my_piecewise3(t63, t300, 0)
  t329 = 0.1e1 / t86 / t65
  t334 = t69 * t222 / 0.6e1 - t118 * t301 / 0.18e2 - t72 * t222 / 0.48e2 + t161 * t301 / 0.240e3 + t75 * t222 / 0.640e3 - t165 * t301 / 0.4480e4 - t78 * t222 / 0.11520e5 + t169 * t301 / 0.103680e6 + t81 * t222 / 0.258048e6 - t173 * t301 / 0.2838528e7 - t84 * t222 / 0.6881280e7 + t177 * t301 / 0.89456640e8 + t87 * t222 / 0.212336640e9 - t181 * t301 / 0.3185049600e10 - t329 * t222 / 0.7431782400e10 + t185 * t301 / 0.126340300800e12
  t335 = f.my_piecewise3(t63, 0, t300)
  t340 = t96 ** 2
  t342 = 0.1e1 / t340 / t90
  t343 = t189 ** 2
  t344 = t342 * t343
  t347 = t99 * t196
  t355 = 0.1e1 / t340
  t363 = 0.1e1 / t340 / t96
  t364 = t363 * t343
  t375 = -0.2e1 * t355 * t343 * t99 + t196 * t335 * t99 / 0.2e1 + t364 * t99 / 0.4e1 - 0.4e1 * t343 * t100 - t97 * t343 * t99 - 0.4e1 * t200 * t335 - t92 * t335 * t99
  t378 = -t344 * t99 / 0.2e1 + 0.2e1 * t347 * t343 - t191 * t335 + 0.2e1 * t335 * t103 + 0.4e1 * t189 * t205 + 0.2e1 * t90 * t375
  t382 = f.my_piecewise3(t62, t334, -0.8e1 / 0.3e1 * t335 * t106 - 0.16e2 / 0.3e1 * t189 * t208 - 0.8e1 / 0.3e1 * t90 * t378)
  t383 = t221 * t382
  t387 = t221 * t212
  t391 = t221 * t110
  t396 = 0.1e1 / t86 / t117
  t397 = t222 * t157
  t400 = t329 * t157
  t405 = t87 * t157
  t410 = t84 * t157
  t415 = t81 * t157
  t420 = t78 * t157
  t425 = t75 * t157
  t428 = t396 * t397 / 0.412876800e9 - t400 * t301 / 0.2477260800e10 - t185 * t397 / 0.13271040e8 + t405 * t301 / 0.70778880e8 + t181 * t397 / 0.491520e6 - t410 * t301 / 0.2293760e7 - t177 * t397 / 0.21504e5 + t415 * t301 / 0.86016e5 + t173 * t397 / 0.1152e4 - t420 * t301 / 0.3840e4 - t169 * t397 / 0.80e2 + 0.3e1 / 0.640e3 * t425 * t301
  t429 = t225 ** 2
  t434 = f.p.cam_omega / t53 / t429 / t257 / 0.36e2
  t435 = t434 * t33
  t436 = t58 * t429
  t438 = 0.1e1 / t240 / t125
  t439 = t243 * t145
  t445 = t236 * t152 * t225
  t446 = t239 * t229
  t447 = t241 * t243
  t453 = 0.1e1 / t240 / t49
  t459 = t241 * t145
  t465 = t121 * t296 * jnp.pi
  t470 = t257 * t243
  t475 = t126 * t287
  t485 = t257 * t145
  t509 = params.b * t276 * s0
  t510 = t137 ** 2
  t514 = 0.1e1 / t281 / t43
  t519 = -0.17834666666666666666666666666666666666666666666667e5 * t32 * t33 / t20 / t137 * t45 + 0.81612800000000000000000000000000000000000000000000e6 * t136 / t137 / t263 * t141 - 0.59719680000000000000000000000000000000000000000000e7 * t277 / t21 / t137 / t35 * t282 * t39 + 0.28311552000000000000000000000000000000000000000000e8 * t509 / t20 / t510 * t514 * t33
  t524 = t292 * t11
  t528 = t33 / t57 / t524 / t263
  t532 = 0.135e3 / 0.4e1 * t435 * t436 * t438 * t439 - 0.9e1 / 0.8e1 * t445 * t446 * t447 * t11 - 0.27e2 / 0.4e1 * t238 * t239 * t229 * t453 * t439 + 0.27e2 / 0.8e1 * t238 * t446 * t459 * t287 + t465 * t250 * t251 * t292 / 0.3e1 + t249 * t250 * t470 * t11 / 0.2e1 - t249 * t250 * t475 * t11 / 0.4e1 + 0.3e1 / 0.2e1 * t123 * t124 * t29 * t241 * t439 - 0.3e1 / 0.2e1 * t123 * t250 * t485 * t287 + t123 * t124 * t127 * t519 / 0.4e1 - 0.14e2 / 0.27e2 * t55 * t528 * t524
  t533 = f.my_piecewise3(t63, t532, 0)
  t560 = t161 * t533 / 0.240e3 - t118 * t533 / 0.18e2 - t181 * t533 / 0.3185049600e10 + t185 * t533 / 0.126340300800e12 + t177 * t533 / 0.89456640e8 - t173 * t533 / 0.2838528e7 + t169 * t533 / 0.103680e6 - t165 * t533 / 0.4480e4 + t165 * t397 / 0.8e1 - t72 * t157 * t301 / 0.16e2 + t69 * t157 * t301 / 0.2e1 - 0.2e1 / 0.3e1 * t161 * t397
  t562 = f.my_piecewise3(t63, 0, t532)
  t569 = t343 * t189
  t573 = t342 * t189
  t574 = t99 * t335
  t577 = t340 ** 2
  t578 = 0.1e1 / t577
  t582 = t99 * t355
  t598 = t355 * t189
  t602 = 0.1e1 / t340 / t195
  t610 = t189 * t99
  t614 = 0.1e1 / t577 / t90
  t618 = t189 * t100
  t621 = t97 * t189
  t628 = 0.15e2 / 0.2e1 * t342 * t569 * t99 - 0.6e1 * t598 * t574 - 0.5e1 / 0.2e1 * t602 * t569 * t99 + t196 * t562 * t99 / 0.2e1 + 0.3e1 / 0.4e1 * t363 * t335 * t610 + t614 * t569 * t99 / 0.8e1 - 0.12e2 * t618 * t335 - 0.3e1 * t621 * t574 - 0.4e1 * t200 * t562 - t92 * t562 * t99
  t631 = 0.7e1 / 0.2e1 * t363 * t569 * t99 - 0.3e1 / 0.2e1 * t573 * t574 - t578 * t569 * t99 / 0.4e1 - 0.6e1 * t582 * t569 + 0.6e1 * t347 * t189 * t335 - t191 * t562 + 0.2e1 * t562 * t103 + 0.6e1 * t335 * t205 + 0.6e1 * t189 * t375 + 0.2e1 * t90 * t628
  t635 = f.my_piecewise3(t62, t428 + t560, -0.8e1 / 0.3e1 * t562 * t106 - 0.8e1 * t335 * t208 - 0.8e1 * t189 * t378 - 0.8e1 / 0.3e1 * t90 * t631)
  t636 = t20 * t635
  t640 = t20 * t382
  t644 = t20 * t212
  t648 = t20 * t110
  t653 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t111 * t49 + t18 * t213 * t49 / 0.4e1 + t18 * t217 * t145 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t383 * t49 - 0.3e1 / 0.4e1 * t18 * t387 * t145 - 0.3e1 / 0.8e1 * t18 * t391 * t287 - 0.3e1 / 0.8e1 * t18 * t636 * t49 - 0.9e1 / 0.8e1 * t18 * t640 * t145 - 0.9e1 / 0.8e1 * t18 * t644 * t287 - 0.3e1 / 0.8e1 * t18 * t648 * t519)
  t716 = 0.14862222222222222222222222222222222222222222222222e6 * t32 * t33 / t20 / t138 * t45 - 0.10118826666666666666666666666666666666666666666667e8 * t136 / t278 * t141 + 0.12079104000000000000000000000000000000000000000000e9 * t277 / t21 / t137 / t128 * t282 * t39 - 0.12268339200000000000000000000000000000000000000000e10 * t509 / t20 / t510 / r0 * t514 * t33 + 0.45298483200000000000000000000000000000000000000000e10 * params.b * t276 * t31 / t510 / t34 / t281 / t44
  t771 = t243 ** 2
  t780 = t287 ** 2
  t806 = t145 * t11 * t287
  t810 = t292 ** 2
  t828 = -t249 * t250 * t126 * t519 * t11 / 0.3e1 - 0.6e1 * t123 * t124 * t29 * t453 * t771 + 0.9e1 * t123 * t250 * t447 * t287 - 0.3e1 / 0.2e1 * t123 * t124 * t258 * t780 - 0.2e1 * t123 * t250 * t485 * t519 + 0.3e1 * t236 * t296 * t225 * t446 * t447 * t292 + 0.9e1 * t445 * t446 * t453 * t439 * t11 - 0.9e1 / 0.2e1 * t236 * t33 * t151 * t225 * t3 * t230 * t241 * t806 + 0.140e3 / 0.81e2 * t55 * t33 / t57 / t34 - 0.28e2 / 0.27e2 * t121 * t528 * jnp.pi * t250 * t251 * t524 - 0.4e1 / 0.3e1 * t465 * t250 * t470 * t292
  t855 = t240 ** 2
  t866 = t429 * t438
  t904 = -0.2e1 * t249 * t250 * t241 * t439 * t11 + 0.2e1 * t121 * t33 * t151 * jnp.pi * t24 * t30 * t257 * t806 + 0.105e3 / 0.32e2 * f.p.cam_omega / t53 / t24 * t27 * t26 / t29 / t241 * t59 * jnp.pi / t855 * t771 * t250 + t123 * t124 * t127 * t716 / 0.4e1 - 0.45e2 * t434 * t152 * t866 * t439 * t11 - 0.405e3 * t435 * t436 / t240 / t256 * t771 + 0.405e3 / 0.2e1 * t434 * t59 * t866 * t243 * t287 + 0.81e2 / 0.2e1 * t238 * t239 * t229 * t438 * t771 - 0.81e2 / 0.2e1 * t238 * t446 * t453 * t243 * t287 + 0.27e2 / 0.8e1 * t238 * t239 * t242 * t780 + 0.9e1 / 0.2e1 * t238 * t446 * t459 * t519 + 0.2e1 / 0.3e1 * t465 * t250 * t475 * t292
  t905 = t828 + t904
  t906 = f.my_piecewise3(t63, t905, 0)
  t913 = t222 ** 2
  t916 = -t400 * t533 / 0.1857945600e10 + t415 * t533 / 0.64512e5 - 0.4e1 * t161 * t222 * t301 + 0.3e1 / 0.4e1 * t165 * t222 * t301 + t396 * t222 * t301 / 0.68812800e8 - 0.3e1 / 0.40e2 * t169 * t222 * t301 - t420 * t533 / 0.2880e4 + 0.2e1 / 0.3e1 * t69 * t533 * t157 + t173 * t222 * t301 / 0.192e3 + t181 * t222 * t301 / 0.81920e5 - t410 * t533 / 0.1720320e7 - t185 * t222 * t301 / 0.2211840e7 + t405 * t533 / 0.53084160e8 - t72 * t533 * t157 / 0.12e2 - t177 * t222 * t301 / 0.3584e4 + t425 * t533 / 0.160e3 + t177 * t906 / 0.89456640e8 + t169 * t906 / 0.103680e6 + t161 * t906 / 0.240e3 + 0.17e2 / 0.13271040e8 * t329 * t913
  t919 = t301 ** 2
  t960 = 0.9e1 / 0.80e2 * t78 * t913 - t72 * t919 / 0.16e2 - 0.7e1 / 0.8e1 * t75 * t913 - t173 * t906 / 0.2838528e7 + t185 * t906 / 0.126340300800e12 - t181 * t906 / 0.3185049600e10 + t87 * t919 / 0.70778880e8 - 0.19e2 / 0.412876800e9 / t86 / t68 * t913 - t165 * t906 / 0.4480e4 + 0.10e2 / 0.3e1 * t72 * t913 - t329 * t919 / 0.2477260800e10 + 0.13e2 / 0.21504e5 * t84 * t913 - t118 * t906 / 0.18e2 + t69 * t919 / 0.2e1 + t81 * t919 / 0.86016e5 - 0.11e2 / 0.1152e4 * t81 * t913 + 0.3e1 / 0.640e3 * t75 * t919 - t84 * t919 / 0.2293760e7 - t78 * t919 / 0.3840e4 - t87 * t913 / 0.32768e5
  t962 = f.my_piecewise3(t63, 0, t905)
  t973 = t343 ** 2
  t977 = t99 * t562
  t988 = t335 ** 2
  t1043 = -t92 * t962 * t99 - 0.75e2 / 0.2e1 * t363 * t973 * t99 + 0.45e2 * t344 * t574 - 0.15e2 * t602 * t343 * t574 - 0.16e2 * t618 * t562 - 0.3e1 * t97 * t988 * t99 - 0.4e1 * t621 * t977 - 0.6e1 * t355 * t988 * t99 - 0.8e1 * t598 * t977 + 0.85e2 / 0.4e1 * t578 * t973 * t99 + t363 * t562 * t610 + 0.3e1 / 0.4e1 * t363 * t988 * t99 + 0.3e1 / 0.4e1 * t614 * t335 * t343 * t99 - 0.19e2 / 0.8e1 / t577 / t96 * t973 * t99 + t196 * t962 * t99 / 0.2e1 + 0.1e1 / t577 / t340 * t973 * t99 / 0.16e2 - 0.12e2 * t988 * t100 - 0.4e1 * t200 * t962
  t1069 = -0.1e1 / t577 / t195 * t973 * t99 / 0.8e1 - 0.2e1 * t573 * t977 - 0.3e1 / 0.2e1 * t578 * t343 * t574 - 0.24e2 * t602 * t973 * t99 + 0.21e2 * t364 * t574 - 0.3e1 / 0.2e1 * t342 * t988 * t99 + 0.2e1 * t90 * t1043 + 0.8e1 * t189 * t628 + 0.15e2 / 0.4e1 * t614 * t973 * t99 + 0.24e2 * t99 * t342 * t973 - 0.36e2 * t582 * t343 * t335 + 0.6e1 * t347 * t988 + 0.8e1 * t347 * t189 * t562 - t191 * t962 + 0.12e2 * t335 * t375 + 0.8e1 * t562 * t205 + 0.2e1 * t962 * t103
  t1073 = f.my_piecewise3(t62, t916 + t960, -0.8e1 / 0.3e1 * t962 * t106 - 0.32e2 / 0.3e1 * t562 * t208 - 0.16e2 * t335 * t378 - 0.32e2 / 0.3e1 * t189 * t631 - 0.8e1 / 0.3e1 * t90 * t1069)
  t1091 = t18 * t217 * t287 / 0.2e1 - t18 * t221 * t635 * t49 / 0.2e1 + 0.10e2 / 0.27e2 * t18 / t21 / t263 * t110 * t49 + t18 * t213 * t145 - 0.5e1 / 0.9e1 * t18 * t111 * t145 + t18 * t116 * t382 * t49 / 0.2e1 - 0.9e1 / 0.4e1 * t18 * t640 * t287 - 0.3e1 / 0.2e1 * t18 * t636 * t145 - 0.3e1 / 0.8e1 * t18 * t648 * t716 - 0.3e1 / 0.2e1 * t18 * t644 * t519 - 0.3e1 / 0.8e1 * t18 * t20 * t1073 * t49 - 0.5e1 / 0.9e1 * t18 * t23 * t212 * t49 - 0.3e1 / 0.2e1 * t18 * t383 * t145 - 0.3e1 / 0.2e1 * t18 * t387 * t287 - t18 * t391 * t519 / 0.2e1
  t1092 = f.my_piecewise3(t2, 0, t1091)
  v4rho4_0_ = 0.2e1 * r0 * t1092 + 0.8e1 * t653

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
  t32 = t24 * t6
  t33 = 0.1e1 / t32
  t36 = 0.2e1 * t16 * t33 - 0.2e1 * t25
  t37 = f.my_piecewise5(t10, 0, t14, 0, t36)
  t41 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t23 * t29 + 0.4e1 / 0.3e1 * t21 * t37)
  t42 = t5 * t41
  t43 = t6 ** (0.1e1 / 0.3e1)
  t44 = t2 ** 2
  t45 = jnp.pi * t44
  t47 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t48 = 0.1e1 / t47
  t49 = 4 ** (0.1e1 / 0.3e1)
  t50 = t48 * t49
  t51 = s0 ** 2
  t52 = params.b * t51
  t53 = r0 ** 2
  t54 = t53 ** 2
  t55 = t54 * r0
  t56 = r0 ** (0.1e1 / 0.3e1)
  t59 = t56 ** 2
  t64 = 0.1e1 + 0.60e1 * s0 / t59 / t53
  t65 = t64 ** 2
  t66 = 0.1e1 / t65
  t70 = params.a + 0.3600e2 * t52 / t56 / t55 * t66
  t73 = t45 * t50 / t70
  t74 = jnp.sqrt(t73)
  t76 = f.p.cam_omega / t74
  t77 = 2 ** (0.1e1 / 0.3e1)
  t78 = t19 * t6
  t79 = t78 ** (0.1e1 / 0.3e1)
  t80 = 0.1e1 / t79
  t81 = t77 * t80
  t83 = t76 * t81 / 0.2e1
  t84 = 0.135e1 <= t83
  t85 = 0.135e1 < t83
  t86 = f.my_piecewise3(t85, t83, 0.135e1)
  t87 = t86 ** 2
  t90 = t87 ** 2
  t91 = 0.1e1 / t90
  t93 = t90 * t87
  t94 = 0.1e1 / t93
  t96 = t90 ** 2
  t97 = 0.1e1 / t96
  t100 = 0.1e1 / t96 / t87
  t103 = 0.1e1 / t96 / t90
  t106 = 0.1e1 / t96 / t93
  t108 = t96 ** 2
  t109 = 0.1e1 / t108
  t112 = f.my_piecewise3(t85, 0.135e1, t83)
  t113 = jnp.sqrt(jnp.pi)
  t114 = 0.1e1 / t112
  t116 = jnp.erf(t114 / 0.2e1)
  t118 = t112 ** 2
  t119 = 0.1e1 / t118
  t121 = jnp.exp(-t119 / 0.4e1)
  t122 = t121 - 0.1e1
  t125 = t121 - 0.3e1 / 0.2e1 - 0.2e1 * t118 * t122
  t128 = 0.2e1 * t112 * t125 + t113 * t116
  t132 = f.my_piecewise3(t84, 0.1e1 / t87 / 0.36e2 - t91 / 0.960e3 + t94 / 0.26880e5 - t97 / 0.829440e6 + t100 / 0.28385280e8 - t103 / 0.1073479680e10 + t106 / 0.44590694400e11 - t109 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t112 * t128)
  t133 = t43 * t132
  t134 = t133 * t70
  t139 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t140 = t5 * t139
  t141 = t43 ** 2
  t142 = 0.1e1 / t141
  t143 = t142 * t132
  t144 = t143 * t70
  t147 = t87 * t86
  t148 = 0.1e1 / t147
  t151 = f.p.cam_omega / t74 / t73
  t153 = t151 * t81 * jnp.pi
  t154 = t44 * t48
  t155 = t70 ** 2
  t156 = 0.1e1 / t155
  t157 = t49 * t156
  t165 = params.b * t51 * s0
  t166 = t54 ** 2
  t170 = 0.1e1 / t65 / t64
  t174 = -0.19200000000000000000000000000000000000000000000000e3 * t52 / t56 / t54 / t53 * t66 + 0.11520000000000000000000000000000000000000000000000e4 * t165 / t166 / r0 * t170
  t181 = t77 / t79 / t78
  t183 = t28 * t6 + t18 + 0.1e1
  t187 = t153 * t154 * t157 * t174 / 0.4e1 - t76 * t181 * t183 / 0.6e1
  t188 = f.my_piecewise3(t85, t187, 0)
  t191 = t90 * t86
  t192 = 0.1e1 / t191
  t195 = t90 * t147
  t196 = 0.1e1 / t195
  t200 = 0.1e1 / t96 / t86
  t204 = 0.1e1 / t96 / t147
  t208 = 0.1e1 / t96 / t191
  t212 = 0.1e1 / t96 / t195
  t216 = 0.1e1 / t108 / t86
  t220 = f.my_piecewise3(t85, 0, t187)
  t222 = t121 * t119
  t226 = t118 * t112
  t227 = 0.1e1 / t226
  t231 = t112 * t122
  t236 = t227 * t220 * t121 / 0.2e1 - 0.4e1 * t231 * t220 - t114 * t220 * t121
  t239 = 0.2e1 * t112 * t236 + 0.2e1 * t220 * t125 - t222 * t220
  t243 = f.my_piecewise3(t84, -t148 * t188 / 0.18e2 + t192 * t188 / 0.240e3 - t196 * t188 / 0.4480e4 + t200 * t188 / 0.103680e6 - t204 * t188 / 0.2838528e7 + t208 * t188 / 0.89456640e8 - t212 * t188 / 0.3185049600e10 + t216 * t188 / 0.126340300800e12, -0.8e1 / 0.3e1 * t112 * t239 - 0.8e1 / 0.3e1 * t220 * t128)
  t244 = t43 * t243
  t245 = t244 * t70
  t248 = t133 * t174
  t251 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t252 = t251 * f.p.zeta_threshold
  t254 = f.my_piecewise3(t20, t252, t21 * t19)
  t255 = t5 * t254
  t257 = 0.1e1 / t141 / t6
  t258 = t257 * t132
  t259 = t258 * t70
  t262 = t142 * t243
  t263 = t262 * t70
  t266 = t143 * t174
  t269 = t188 ** 2
  t272 = jnp.pi ** 2
  t274 = t47 ** 2
  t275 = 0.1e1 / t274
  t276 = t49 ** 2
  t283 = f.p.cam_omega / t74 / t272 / t2 / t275 / t276 / t156 / 0.3e1
  t285 = t283 * t81 * t272
  t286 = t2 * t275
  t287 = t155 ** 2
  t288 = 0.1e1 / t287
  t290 = t174 ** 2
  t296 = t151 * t181 * jnp.pi
  t297 = t154 * t49
  t298 = t156 * t174
  t304 = 0.1e1 / t155 / t70
  t310 = t53 * r0
  t322 = t51 ** 2
  t323 = params.b * t322
  t327 = t65 ** 2
  t328 = 0.1e1 / t327
  t332 = 0.12160000000000000000000000000000000000000000000000e4 * t52 / t56 / t54 / t310 * t66 - 0.16512000000000000000000000000000000000000000000000e5 * t165 / t166 / t53 * t170 + 0.55296000000000000000000000000000000000000000000000e5 * t323 / t59 / t166 / t54 * t328
  t337 = t19 ** 2
  t340 = 0.1e1 / t79 / t337 / t24
  t341 = t77 * t340
  t342 = t183 ** 2
  t348 = t37 * t6 + 0.2e1 * t28
  t352 = 0.9e1 / 0.8e1 * t285 * t286 * t276 * t288 * t290 - t296 * t297 * t298 * t183 / 0.6e1 - t153 * t154 * t49 * t304 * t290 / 0.2e1 + t153 * t154 * t157 * t332 / 0.4e1 + 0.2e1 / 0.9e1 * t76 * t341 * t342 - t76 * t181 * t348 / 0.6e1
  t353 = f.my_piecewise3(t85, t352, 0)
  t381 = 0.1e1 / t108 / t87
  t386 = t91 * t269 / 0.6e1 - t148 * t353 / 0.18e2 - t94 * t269 / 0.48e2 + t192 * t353 / 0.240e3 + t97 * t269 / 0.640e3 - t196 * t353 / 0.4480e4 - t100 * t269 / 0.11520e5 + t200 * t353 / 0.103680e6 + t103 * t269 / 0.258048e6 - t204 * t353 / 0.2838528e7 - t106 * t269 / 0.6881280e7 + t208 * t353 / 0.89456640e8 + t109 * t269 / 0.212336640e9 - t212 * t353 / 0.3185049600e10 - t381 * t269 / 0.7431782400e10 + t216 * t353 / 0.126340300800e12
  t387 = f.my_piecewise3(t85, 0, t352)
  t392 = t118 ** 2
  t394 = 0.1e1 / t392 / t112
  t395 = t220 ** 2
  t399 = t121 * t227
  t407 = 0.1e1 / t392
  t415 = 0.1e1 / t392 / t118
  t427 = -0.2e1 * t407 * t395 * t121 + t227 * t387 * t121 / 0.2e1 + t415 * t395 * t121 / 0.4e1 - 0.4e1 * t395 * t122 - t119 * t395 * t121 - 0.4e1 * t231 * t387 - t114 * t387 * t121
  t430 = -t394 * t395 * t121 / 0.2e1 + 0.2e1 * t399 * t395 - t222 * t387 + 0.2e1 * t387 * t125 + 0.4e1 * t220 * t236 + 0.2e1 * t112 * t427
  t434 = f.my_piecewise3(t84, t386, -0.8e1 / 0.3e1 * t387 * t128 - 0.16e2 / 0.3e1 * t220 * t239 - 0.8e1 / 0.3e1 * t112 * t430)
  t435 = t43 * t434
  t436 = t435 * t70
  t439 = t244 * t174
  t442 = t133 * t332
  t446 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t42 * t134 - t140 * t144 / 0.4e1 - 0.3e1 / 0.4e1 * t140 * t245 - 0.3e1 / 0.4e1 * t140 * t248 + t255 * t259 / 0.12e2 - t255 * t263 / 0.4e1 - t255 * t266 / 0.4e1 - 0.3e1 / 0.8e1 * t255 * t436 - 0.3e1 / 0.4e1 * t255 * t439 - 0.3e1 / 0.8e1 * t255 * t442)
  t448 = r1 <= f.p.dens_threshold
  t449 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t450 = 0.1e1 + t449
  t451 = t450 <= f.p.zeta_threshold
  t452 = t450 ** (0.1e1 / 0.3e1)
  t453 = t452 ** 2
  t454 = 0.1e1 / t453
  t456 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t457 = t456 ** 2
  t461 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t465 = f.my_piecewise3(t451, 0, 0.4e1 / 0.9e1 * t454 * t457 + 0.4e1 / 0.3e1 * t452 * t461)
  t466 = t5 * t465
  t467 = s2 ** 2
  t469 = r1 ** 2
  t470 = t469 ** 2
  t472 = r1 ** (0.1e1 / 0.3e1)
  t475 = t472 ** 2
  t481 = (0.1e1 + 0.60e1 * s2 / t475 / t469) ** 2
  t486 = params.a + 0.3600e2 * params.b * t467 / t472 / t470 / r1 / t481
  t490 = jnp.sqrt(t45 * t50 / t486)
  t492 = f.p.cam_omega / t490
  t493 = t450 * t6
  t494 = t493 ** (0.1e1 / 0.3e1)
  t498 = t492 * t77 / t494 / 0.2e1
  t499 = 0.135e1 <= t498
  t500 = 0.135e1 < t498
  t501 = f.my_piecewise3(t500, t498, 0.135e1)
  t502 = t501 ** 2
  t505 = t502 ** 2
  t506 = 0.1e1 / t505
  t508 = t505 * t502
  t509 = 0.1e1 / t508
  t511 = t505 ** 2
  t512 = 0.1e1 / t511
  t515 = 0.1e1 / t511 / t502
  t518 = 0.1e1 / t511 / t505
  t521 = 0.1e1 / t511 / t508
  t523 = t511 ** 2
  t524 = 0.1e1 / t523
  t527 = f.my_piecewise3(t500, 0.135e1, t498)
  t528 = 0.1e1 / t527
  t530 = jnp.erf(t528 / 0.2e1)
  t532 = t527 ** 2
  t533 = 0.1e1 / t532
  t535 = jnp.exp(-t533 / 0.4e1)
  t536 = t535 - 0.1e1
  t539 = t535 - 0.3e1 / 0.2e1 - 0.2e1 * t532 * t536
  t542 = t113 * t530 + 0.2e1 * t527 * t539
  t546 = f.my_piecewise3(t499, 0.1e1 / t502 / 0.36e2 - t506 / 0.960e3 + t509 / 0.26880e5 - t512 / 0.829440e6 + t515 / 0.28385280e8 - t518 / 0.1073479680e10 + t521 / 0.44590694400e11 - t524 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t527 * t542)
  t548 = t43 * t546 * t486
  t553 = f.my_piecewise3(t451, 0, 0.4e1 / 0.3e1 * t452 * t456)
  t554 = t5 * t553
  t556 = t142 * t546 * t486
  t559 = t502 * t501
  t560 = 0.1e1 / t559
  t563 = t77 / t494 / t493
  t565 = t456 * t6 + t449 + 0.1e1
  t568 = t492 * t563 * t565 / 0.6e1
  t569 = f.my_piecewise3(t500, -t568, 0)
  t572 = t505 * t501
  t573 = 0.1e1 / t572
  t576 = t505 * t559
  t577 = 0.1e1 / t576
  t581 = 0.1e1 / t511 / t501
  t585 = 0.1e1 / t511 / t559
  t589 = 0.1e1 / t511 / t572
  t593 = 0.1e1 / t511 / t576
  t597 = 0.1e1 / t523 / t501
  t601 = f.my_piecewise3(t500, 0, -t568)
  t603 = t535 * t533
  t607 = t532 * t527
  t608 = 0.1e1 / t607
  t612 = t527 * t536
  t617 = t608 * t601 * t535 / 0.2e1 - 0.4e1 * t612 * t601 - t528 * t601 * t535
  t620 = 0.2e1 * t527 * t617 + 0.2e1 * t601 * t539 - t603 * t601
  t624 = f.my_piecewise3(t499, -t560 * t569 / 0.18e2 + t573 * t569 / 0.240e3 - t577 * t569 / 0.4480e4 + t581 * t569 / 0.103680e6 - t585 * t569 / 0.2838528e7 + t589 * t569 / 0.89456640e8 - t593 * t569 / 0.3185049600e10 + t597 * t569 / 0.126340300800e12, -0.8e1 / 0.3e1 * t527 * t620 - 0.8e1 / 0.3e1 * t601 * t542)
  t626 = t43 * t624 * t486
  t630 = f.my_piecewise3(t451, t252, t452 * t450)
  t631 = t5 * t630
  t633 = t257 * t546 * t486
  t637 = t142 * t624 * t486
  t640 = t569 ** 2
  t643 = t450 ** 2
  t646 = 0.1e1 / t494 / t643 / t24
  t648 = t565 ** 2
  t654 = t461 * t6 + 0.2e1 * t456
  t658 = 0.2e1 / 0.9e1 * t492 * t77 * t646 * t648 - t492 * t563 * t654 / 0.6e1
  t659 = f.my_piecewise3(t500, t658, 0)
  t687 = 0.1e1 / t523 / t502
  t692 = t506 * t640 / 0.6e1 - t560 * t659 / 0.18e2 - t509 * t640 / 0.48e2 + t573 * t659 / 0.240e3 + t512 * t640 / 0.640e3 - t577 * t659 / 0.4480e4 - t515 * t640 / 0.11520e5 + t581 * t659 / 0.103680e6 + t518 * t640 / 0.258048e6 - t585 * t659 / 0.2838528e7 - t521 * t640 / 0.6881280e7 + t589 * t659 / 0.89456640e8 + t524 * t640 / 0.212336640e9 - t593 * t659 / 0.3185049600e10 - t687 * t640 / 0.7431782400e10 + t597 * t659 / 0.126340300800e12
  t693 = f.my_piecewise3(t500, 0, t658)
  t698 = t532 ** 2
  t700 = 0.1e1 / t698 / t527
  t701 = t601 ** 2
  t705 = t535 * t608
  t713 = 0.1e1 / t698
  t721 = 0.1e1 / t698 / t532
  t733 = -0.2e1 * t713 * t701 * t535 + t608 * t693 * t535 / 0.2e1 + t721 * t701 * t535 / 0.4e1 - 0.4e1 * t701 * t536 - t533 * t701 * t535 - 0.4e1 * t612 * t693 - t528 * t693 * t535
  t736 = -t700 * t701 * t535 / 0.2e1 + 0.2e1 * t705 * t701 - t603 * t693 + 0.2e1 * t693 * t539 + 0.4e1 * t601 * t617 + 0.2e1 * t527 * t733
  t740 = f.my_piecewise3(t499, t692, -0.8e1 / 0.3e1 * t693 * t542 - 0.16e2 / 0.3e1 * t601 * t620 - 0.8e1 / 0.3e1 * t527 * t736)
  t742 = t43 * t740 * t486
  t746 = f.my_piecewise3(t448, 0, -0.3e1 / 0.8e1 * t466 * t548 - t554 * t556 / 0.4e1 - 0.3e1 / 0.4e1 * t554 * t626 + t631 * t633 / 0.12e2 - t631 * t637 / 0.4e1 - 0.3e1 / 0.8e1 * t631 * t742)
  t770 = t272 ** 2
  t780 = t290 * t174
  t787 = t286 * t276
  t853 = t166 ** 2
  t861 = -0.89173333333333333333333333333333333333333333333333e4 * t52 / t56 / t166 * t66 + 0.20403200000000000000000000000000000000000000000000e6 * t165 / t166 / t310 * t170 - 0.14929920000000000000000000000000000000000000000000e7 * t323 / t59 / t166 / t55 * t328 + 0.35389440000000000000000000000000000000000000000000e7 * params.b * t322 * s0 / t56 / t853 / t327 / t64
  t880 = t24 ** 2
  t884 = 0.6e1 * t33 - 0.6e1 * t16 / t880
  t885 = f.my_piecewise5(t10, 0, t14, 0, t884)
  t892 = 0.15e2 / 0.16e2 * f.p.cam_omega / t74 / t304 * t77 * t80 / t287 / t155 * t780 - 0.9e1 / 0.8e1 * t283 * t181 * t272 * t787 * t288 * t290 * t183 - 0.27e2 / 0.4e1 * t285 * t286 * t276 / t287 / t70 * t780 + 0.27e2 / 0.8e1 * t285 * t787 * t288 * t174 * t332 + t151 * t341 * jnp.pi * t297 * t298 * t342 / 0.3e1 + t296 * t297 * t304 * t290 * t183 / 0.2e1 - t296 * t297 * t156 * t332 * t183 / 0.4e1 - t296 * t297 * t298 * t348 / 0.4e1 + 0.3e1 / 0.2e1 * t153 * t154 * t49 * t288 * t780 - 0.3e1 / 0.2e1 * t153 * t297 * t304 * t174 * t332 + t153 * t154 * t157 * t861 / 0.4e1 - 0.14e2 / 0.27e2 * t76 * t77 / t79 / t337 / t19 / t32 * t342 * t183 + 0.2e1 / 0.3e1 * t76 * t77 * t340 * t183 * t348 - t76 * t181 * (t885 * t6 + 0.3e1 * t37) / 0.6e1
  t893 = f.my_piecewise3(t85, t892, 0)
  t896 = t269 * t188
  t923 = t216 * t893 / 0.126340300800e12 + t204 * t896 / 0.1152e4 - t100 * t188 * t353 / 0.3840e4 + t208 * t893 / 0.89456640e8 - t204 * t893 / 0.2838528e7 + t200 * t893 / 0.103680e6 - t196 * t893 / 0.4480e4 + t192 * t893 / 0.240e3 - t148 * t893 / 0.18e2 + 0.1e1 / t108 / t147 * t896 / 0.412876800e9 - t381 * t188 * t353 / 0.2477260800e10 - t208 * t896 / 0.21504e5
  t954 = t103 * t188 * t353 / 0.86016e5 + t212 * t896 / 0.491520e6 - t106 * t188 * t353 / 0.2293760e7 + t196 * t896 / 0.8e1 - t94 * t188 * t353 / 0.16e2 - 0.2e1 / 0.3e1 * t192 * t896 + t91 * t188 * t353 / 0.2e1 - t212 * t893 / 0.3185049600e10 - t216 * t896 / 0.13271040e8 + t109 * t188 * t353 / 0.70778880e8 - t200 * t896 / 0.80e2 + 0.3e1 / 0.640e3 * t97 * t188 * t353
  t956 = f.my_piecewise3(t85, 0, t892)
  t963 = t395 * t220
  t968 = t121 * t387
  t971 = t392 ** 2
  t1029 = f.my_piecewise3(t84, t923 + t954, -0.8e1 / 0.3e1 * t956 * t128 - 0.8e1 * t387 * t239 - 0.8e1 * t220 * t430 - 0.8e1 / 0.3e1 * t112 * (0.7e1 / 0.2e1 * t415 * t963 * t121 - 0.3e1 / 0.2e1 * t394 * t220 * t968 - 0.1e1 / t971 * t963 * t121 / 0.4e1 - 0.6e1 * t121 * t407 * t963 + 0.6e1 * t399 * t220 * t387 - t222 * t956 + 0.2e1 * t956 * t125 + 0.6e1 * t387 * t236 + 0.6e1 * t220 * t427 + 0.2e1 * t112 * (0.15e2 / 0.2e1 * t394 * t963 * t121 - 0.6e1 * t407 * t220 * t968 - 0.5e1 / 0.2e1 / t392 / t226 * t963 * t121 + t227 * t956 * t121 / 0.2e1 + 0.3e1 / 0.4e1 * t415 * t387 * t220 * t121 + 0.1e1 / t971 / t112 * t963 * t121 / 0.8e1 - 0.12e2 * t220 * t122 * t387 - 0.3e1 * t119 * t220 * t968 - 0.4e1 * t231 * t956 - t114 * t956 * t121)))
  t1035 = 0.1e1 / t141 / t24
  t1062 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t885)
  t1077 = t140 * t259 / 0.4e1 - 0.3e1 / 0.8e1 * t42 * t144 - 0.3e1 / 0.4e1 * t255 * t262 * t174 + t255 * t257 * t243 * t70 / 0.4e1 - 0.9e1 / 0.8e1 * t140 * t442 - 0.9e1 / 0.4e1 * t140 * t439 + t255 * t258 * t174 / 0.4e1 - 0.3e1 / 0.8e1 * t255 * t142 * t434 * t70 - 0.3e1 / 0.8e1 * t255 * t43 * t1029 * t70 - 0.5e1 / 0.36e2 * t255 * t1035 * t132 * t70 - 0.3e1 / 0.8e1 * t255 * t143 * t332 - 0.3e1 / 0.4e1 * t140 * t266 - 0.9e1 / 0.8e1 * t140 * t436 - 0.3e1 / 0.4e1 * t140 * t263 - 0.9e1 / 0.8e1 * t42 * t248 - 0.3e1 / 0.8e1 * t5 * t1062 * t134 - 0.9e1 / 0.8e1 * t42 * t245 - 0.9e1 / 0.8e1 * t255 * t435 * t174 - 0.9e1 / 0.8e1 * t255 * t244 * t332 - 0.3e1 / 0.8e1 * t255 * t133 * t861
  t1078 = f.my_piecewise3(t1, 0, t1077)
  t1088 = f.my_piecewise5(t14, 0, t10, 0, -t884)
  t1092 = f.my_piecewise3(t451, 0, -0.8e1 / 0.27e2 / t453 / t450 * t457 * t456 + 0.4e1 / 0.3e1 * t454 * t456 * t461 + 0.4e1 / 0.3e1 * t452 * t1088)
  t1118 = t640 * t569
  t1151 = t593 * t1118 / 0.491520e6 - t521 * t569 * t659 / 0.2293760e7 - t597 * t1118 / 0.13271040e8 + t524 * t569 * t659 / 0.70778880e8 + 0.1e1 / t523 / t559 * t1118 / 0.412876800e9 - t687 * t569 * t659 / 0.2477260800e10 - 0.2e1 / 0.3e1 * t573 * t1118 + t506 * t569 * t659 / 0.2e1 + t577 * t1118 / 0.8e1 - t509 * t569 * t659 / 0.16e2 - t581 * t1118 / 0.80e2 + 0.3e1 / 0.640e3 * t512 * t569 * t659
  t1182 = -0.14e2 / 0.27e2 * t492 * t77 / t494 / t643 / t450 / t32 * t648 * t565 + 0.2e1 / 0.3e1 * t492 * t77 * t646 * t565 * t654 - t492 * t563 * (t1088 * t6 + 0.3e1 * t461) / 0.6e1
  t1183 = f.my_piecewise3(t500, t1182, 0)
  t1200 = t585 * t1118 / 0.1152e4 - t515 * t569 * t659 / 0.3840e4 - t589 * t1118 / 0.21504e5 + t518 * t569 * t659 / 0.86016e5 + t589 * t1183 / 0.89456640e8 - t593 * t1183 / 0.3185049600e10 + t597 * t1183 / 0.126340300800e12 - t577 * t1183 / 0.4480e4 + t581 * t1183 / 0.103680e6 - t585 * t1183 / 0.2838528e7 - t560 * t1183 / 0.18e2 + t573 * t1183 / 0.240e3
  t1202 = f.my_piecewise3(t500, 0, t1182)
  t1209 = t701 * t601
  t1214 = t535 * t693
  t1217 = t698 ** 2
  t1275 = f.my_piecewise3(t499, t1151 + t1200, -0.8e1 / 0.3e1 * t1202 * t542 - 0.8e1 * t693 * t620 - 0.8e1 * t601 * t736 - 0.8e1 / 0.3e1 * t527 * (0.7e1 / 0.2e1 * t721 * t1209 * t535 - 0.3e1 / 0.2e1 * t700 * t601 * t1214 - 0.1e1 / t1217 * t1209 * t535 / 0.4e1 - 0.6e1 * t535 * t713 * t1209 + 0.6e1 * t705 * t601 * t693 - t603 * t1202 + 0.2e1 * t1202 * t539 + 0.6e1 * t693 * t617 + 0.6e1 * t601 * t733 + 0.2e1 * t527 * (0.15e2 / 0.2e1 * t700 * t1209 * t535 - 0.6e1 * t713 * t601 * t1214 - 0.5e1 / 0.2e1 / t698 / t607 * t1209 * t535 + t608 * t1202 * t535 / 0.2e1 + 0.3e1 / 0.4e1 * t721 * t693 * t601 * t535 + 0.1e1 / t1217 / t527 * t1209 * t535 / 0.8e1 - 0.12e2 * t601 * t536 * t693 - 0.3e1 * t533 * t601 * t1214 - 0.4e1 * t612 * t1202 - t528 * t1202 * t535)))
  t1281 = f.my_piecewise3(t448, 0, -0.3e1 / 0.8e1 * t5 * t1092 * t548 - 0.3e1 / 0.8e1 * t466 * t556 - 0.9e1 / 0.8e1 * t466 * t626 + t554 * t633 / 0.4e1 - 0.3e1 / 0.4e1 * t554 * t637 - 0.9e1 / 0.8e1 * t554 * t742 - 0.5e1 / 0.36e2 * t631 * t1035 * t546 * t486 + t631 * t257 * t624 * t486 / 0.4e1 - 0.3e1 / 0.8e1 * t631 * t142 * t740 * t486 - 0.3e1 / 0.8e1 * t631 * t43 * t1275 * t486)
  d111 = 0.3e1 * t446 + 0.3e1 * t746 + t6 * (t1078 + t1281)

  res = {'v3rho3': d111}
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
  t30 = t5 * t29
  t31 = t6 ** (0.1e1 / 0.3e1)
  t32 = t2 ** 2
  t33 = jnp.pi * t32
  t35 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t36 = 0.1e1 / t35
  t37 = 4 ** (0.1e1 / 0.3e1)
  t38 = t36 * t37
  t39 = s0 ** 2
  t40 = params.b * t39
  t41 = r0 ** 2
  t42 = t41 ** 2
  t44 = r0 ** (0.1e1 / 0.3e1)
  t47 = t44 ** 2
  t52 = 0.1e1 + 0.60e1 * s0 / t47 / t41
  t53 = t52 ** 2
  t54 = 0.1e1 / t53
  t58 = params.a + 0.3600e2 * t40 / t44 / t42 / r0 * t54
  t61 = t33 * t38 / t58
  t62 = jnp.sqrt(t61)
  t64 = f.p.cam_omega / t62
  t65 = 2 ** (0.1e1 / 0.3e1)
  t66 = t19 * t6
  t67 = t66 ** (0.1e1 / 0.3e1)
  t69 = t65 / t67
  t71 = t64 * t69 / 0.2e1
  t72 = 0.135e1 <= t71
  t73 = 0.135e1 < t71
  t74 = f.my_piecewise3(t73, t71, 0.135e1)
  t75 = t74 ** 2
  t78 = t75 ** 2
  t79 = 0.1e1 / t78
  t81 = t78 * t75
  t82 = 0.1e1 / t81
  t84 = t78 ** 2
  t85 = 0.1e1 / t84
  t88 = 0.1e1 / t84 / t75
  t91 = 0.1e1 / t84 / t78
  t94 = 0.1e1 / t84 / t81
  t96 = t84 ** 2
  t97 = 0.1e1 / t96
  t100 = f.my_piecewise3(t73, 0.135e1, t71)
  t101 = jnp.sqrt(jnp.pi)
  t102 = 0.1e1 / t100
  t104 = jax.lax.erf(t102 / 0.2e1)
  t106 = t100 ** 2
  t107 = 0.1e1 / t106
  t109 = jnp.exp(-t107 / 0.4e1)
  t110 = t109 - 0.1e1
  t113 = t109 - 0.3e1 / 0.2e1 - 0.2e1 * t106 * t110
  t116 = 0.2e1 * t100 * t113 + t101 * t104
  t120 = f.my_piecewise3(t72, 0.1e1 / t75 / 0.36e2 - t79 / 0.960e3 + t82 / 0.26880e5 - t85 / 0.829440e6 + t88 / 0.28385280e8 - t91 / 0.1073479680e10 + t94 / 0.44590694400e11 - t97 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t100 * t116)
  t121 = t31 * t120
  t122 = t121 * t58
  t125 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t126 = t125 * f.p.zeta_threshold
  t128 = f.my_piecewise3(t20, t126, t21 * t19)
  t129 = t5 * t128
  t130 = t31 ** 2
  t131 = 0.1e1 / t130
  t132 = t131 * t120
  t133 = t132 * t58
  t135 = t129 * t133 / 0.8e1
  t136 = t75 * t74
  t137 = 0.1e1 / t136
  t140 = f.p.cam_omega / t62 / t61
  t142 = t140 * t69 * jnp.pi
  t143 = t32 * t36
  t144 = t58 ** 2
  t145 = 0.1e1 / t144
  t146 = t37 * t145
  t154 = params.b * t39 * s0
  t155 = t42 ** 2
  t159 = 0.1e1 / t53 / t52
  t163 = -0.19200000000000000000000000000000000000000000000000e3 * t40 / t44 / t42 / t41 * t54 + 0.11520000000000000000000000000000000000000000000000e4 * t154 / t155 / r0 * t159
  t164 = t146 * t163
  t170 = t65 / t67 / t66
  t172 = t26 * t6 + t18 + 0.1e1
  t176 = t142 * t143 * t164 / 0.4e1 - t64 * t170 * t172 / 0.6e1
  t177 = f.my_piecewise3(t73, t176, 0)
  t180 = t78 * t74
  t181 = 0.1e1 / t180
  t184 = t78 * t136
  t185 = 0.1e1 / t184
  t189 = 0.1e1 / t84 / t74
  t193 = 0.1e1 / t84 / t136
  t197 = 0.1e1 / t84 / t180
  t201 = 0.1e1 / t84 / t184
  t205 = 0.1e1 / t96 / t74
  t209 = f.my_piecewise3(t73, 0, t176)
  t211 = t109 * t107
  t216 = 0.1e1 / t106 / t100
  t220 = t100 * t110
  t225 = t216 * t209 * t109 / 0.2e1 - 0.4e1 * t220 * t209 - t102 * t209 * t109
  t228 = 0.2e1 * t100 * t225 + 0.2e1 * t209 * t113 - t211 * t209
  t232 = f.my_piecewise3(t72, -t137 * t177 / 0.18e2 + t181 * t177 / 0.240e3 - t185 * t177 / 0.4480e4 + t189 * t177 / 0.103680e6 - t193 * t177 / 0.2838528e7 + t197 * t177 / 0.89456640e8 - t201 * t177 / 0.3185049600e10 + t205 * t177 / 0.126340300800e12, -0.8e1 / 0.3e1 * t100 * t228 - 0.8e1 / 0.3e1 * t209 * t116)
  t233 = t31 * t232
  t234 = t233 * t58
  t237 = t121 * t163
  t241 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t122 - t135 - 0.3e1 / 0.8e1 * t129 * t234 - 0.3e1 / 0.8e1 * t129 * t237)
  t243 = r1 <= f.p.dens_threshold
  t244 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t245 = 0.1e1 + t244
  t246 = t245 <= f.p.zeta_threshold
  t247 = t245 ** (0.1e1 / 0.3e1)
  t249 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t252 = f.my_piecewise3(t246, 0, 0.4e1 / 0.3e1 * t247 * t249)
  t253 = t5 * t252
  t254 = s2 ** 2
  t255 = params.b * t254
  t256 = r1 ** 2
  t257 = t256 ** 2
  t259 = r1 ** (0.1e1 / 0.3e1)
  t262 = t259 ** 2
  t267 = 0.1e1 + 0.60e1 * s2 / t262 / t256
  t268 = t267 ** 2
  t269 = 0.1e1 / t268
  t273 = params.a + 0.3600e2 * t255 / t259 / t257 / r1 * t269
  t276 = t33 * t38 / t273
  t277 = jnp.sqrt(t276)
  t279 = f.p.cam_omega / t277
  t280 = t245 * t6
  t281 = t280 ** (0.1e1 / 0.3e1)
  t283 = t65 / t281
  t285 = t279 * t283 / 0.2e1
  t286 = 0.135e1 <= t285
  t287 = 0.135e1 < t285
  t288 = f.my_piecewise3(t287, t285, 0.135e1)
  t289 = t288 ** 2
  t292 = t289 ** 2
  t293 = 0.1e1 / t292
  t295 = t292 * t289
  t296 = 0.1e1 / t295
  t298 = t292 ** 2
  t299 = 0.1e1 / t298
  t302 = 0.1e1 / t298 / t289
  t305 = 0.1e1 / t298 / t292
  t308 = 0.1e1 / t298 / t295
  t310 = t298 ** 2
  t311 = 0.1e1 / t310
  t314 = f.my_piecewise3(t287, 0.135e1, t285)
  t315 = 0.1e1 / t314
  t317 = jax.lax.erf(t315 / 0.2e1)
  t319 = t314 ** 2
  t320 = 0.1e1 / t319
  t322 = jnp.exp(-t320 / 0.4e1)
  t323 = t322 - 0.1e1
  t326 = t322 - 0.3e1 / 0.2e1 - 0.2e1 * t319 * t323
  t329 = t101 * t317 + 0.2e1 * t314 * t326
  t333 = f.my_piecewise3(t286, 0.1e1 / t289 / 0.36e2 - t293 / 0.960e3 + t296 / 0.26880e5 - t299 / 0.829440e6 + t302 / 0.28385280e8 - t305 / 0.1073479680e10 + t308 / 0.44590694400e11 - t311 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t314 * t329)
  t334 = t31 * t333
  t335 = t334 * t273
  t339 = f.my_piecewise3(t246, t126, t247 * t245)
  t340 = t5 * t339
  t341 = t131 * t333
  t342 = t341 * t273
  t344 = t340 * t342 / 0.8e1
  t345 = t289 * t288
  t346 = 0.1e1 / t345
  t349 = t65 / t281 / t280
  t351 = t249 * t6 + t244 + 0.1e1
  t354 = t279 * t349 * t351 / 0.6e1
  t355 = f.my_piecewise3(t287, -t354, 0)
  t358 = t292 * t288
  t359 = 0.1e1 / t358
  t362 = t292 * t345
  t363 = 0.1e1 / t362
  t367 = 0.1e1 / t298 / t288
  t371 = 0.1e1 / t298 / t345
  t375 = 0.1e1 / t298 / t358
  t379 = 0.1e1 / t298 / t362
  t383 = 0.1e1 / t310 / t288
  t387 = f.my_piecewise3(t287, 0, -t354)
  t389 = t322 * t320
  t394 = 0.1e1 / t319 / t314
  t398 = t314 * t323
  t403 = t394 * t387 * t322 / 0.2e1 - 0.4e1 * t398 * t387 - t315 * t387 * t322
  t406 = 0.2e1 * t314 * t403 + 0.2e1 * t387 * t326 - t389 * t387
  t410 = f.my_piecewise3(t286, -t346 * t355 / 0.18e2 + t359 * t355 / 0.240e3 - t363 * t355 / 0.4480e4 + t367 * t355 / 0.103680e6 - t371 * t355 / 0.2838528e7 + t375 * t355 / 0.89456640e8 - t379 * t355 / 0.3185049600e10 + t383 * t355 / 0.126340300800e12, -0.8e1 / 0.3e1 * t314 * t406 - 0.8e1 / 0.3e1 * t387 * t329)
  t411 = t31 * t410
  t412 = t411 * t273
  t416 = f.my_piecewise3(t243, 0, -0.3e1 / 0.8e1 * t253 * t335 - t344 - 0.3e1 / 0.8e1 * t340 * t412)
  t418 = t21 ** 2
  t419 = 0.1e1 / t418
  t420 = t26 ** 2
  t425 = t16 / t22 / t6
  t427 = -0.2e1 * t23 + 0.2e1 * t425
  t428 = f.my_piecewise5(t10, 0, t14, 0, t427)
  t432 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t419 * t420 + 0.4e1 / 0.3e1 * t21 * t428)
  t436 = t30 * t133
  t443 = 0.1e1 / t130 / t6
  t447 = t129 * t443 * t120 * t58 / 0.12e2
  t450 = t129 * t131 * t232 * t58
  t453 = t129 * t132 * t163
  t455 = t177 ** 2
  t458 = jnp.pi ** 2
  t459 = t458 * t2
  t460 = t35 ** 2
  t461 = 0.1e1 / t460
  t462 = t37 ** 2
  t463 = t461 * t462
  t472 = t2 * t461
  t473 = t144 ** 2
  t476 = t163 ** 2
  t483 = t143 * t37
  t508 = t39 ** 2
  t513 = t53 ** 2
  t518 = 0.12160000000000000000000000000000000000000000000000e4 * t40 / t44 / t42 / t41 / r0 * t54 - 0.16512000000000000000000000000000000000000000000000e5 * t154 / t155 / t41 * t159 + 0.55296000000000000000000000000000000000000000000000e5 * params.b * t508 / t47 / t155 / t42 / t513
  t523 = t19 ** 2
  t526 = 0.1e1 / t67 / t523 / t22
  t527 = t65 * t526
  t528 = t172 ** 2
  t538 = 0.3e1 / 0.8e1 * f.p.cam_omega / t62 / t459 / t463 / t145 * t69 * t458 * t472 * t462 / t473 * t476 - t140 * t170 * jnp.pi * t483 * t145 * t163 * t172 / 0.6e1 - t142 * t143 * t37 / t144 / t58 * t476 / 0.2e1 + t142 * t143 * t146 * t518 / 0.4e1 + 0.2e1 / 0.9e1 * t64 * t527 * t528 - t64 * t170 * (t428 * t6 + 0.2e1 * t26) / 0.6e1
  t539 = f.my_piecewise3(t73, t538, 0)
  t567 = 0.1e1 / t96 / t75
  t572 = t79 * t455 / 0.6e1 - t137 * t539 / 0.18e2 - t82 * t455 / 0.48e2 + t181 * t539 / 0.240e3 + t85 * t455 / 0.640e3 - t185 * t539 / 0.4480e4 - t88 * t455 / 0.11520e5 + t189 * t539 / 0.103680e6 + t91 * t455 / 0.258048e6 - t193 * t539 / 0.2838528e7 - t94 * t455 / 0.6881280e7 + t197 * t539 / 0.89456640e8 + t97 * t455 / 0.212336640e9 - t201 * t539 / 0.3185049600e10 - t567 * t455 / 0.7431782400e10 + t205 * t539 / 0.126340300800e12
  t573 = f.my_piecewise3(t73, 0, t538)
  t578 = t106 ** 2
  t580 = 0.1e1 / t578 / t100
  t581 = t209 ** 2
  t585 = t109 * t216
  t593 = 0.1e1 / t578
  t601 = 0.1e1 / t578 / t106
  t620 = f.my_piecewise3(t72, t572, -0.8e1 / 0.3e1 * t573 * t116 - 0.16e2 / 0.3e1 * t209 * t228 - 0.8e1 / 0.3e1 * t100 * (-t580 * t581 * t109 / 0.2e1 + 0.2e1 * t585 * t581 - t211 * t573 + 0.2e1 * t573 * t113 + 0.4e1 * t209 * t225 + 0.2e1 * t100 * (-0.2e1 * t593 * t581 * t109 + t216 * t573 * t109 / 0.2e1 + t601 * t581 * t109 / 0.4e1 - 0.4e1 * t581 * t110 - t107 * t581 * t109 - 0.4e1 * t220 * t573 - t102 * t573 * t109)))
  t632 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t432 * t122 - t436 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t234 - 0.3e1 / 0.4e1 * t30 * t237 + t447 - t450 / 0.4e1 - t453 / 0.4e1 - 0.3e1 / 0.8e1 * t129 * t31 * t620 * t58 - 0.3e1 / 0.4e1 * t129 * t233 * t163 - 0.3e1 / 0.8e1 * t129 * t121 * t518)
  t633 = t247 ** 2
  t634 = 0.1e1 / t633
  t635 = t249 ** 2
  t639 = f.my_piecewise5(t14, 0, t10, 0, -t427)
  t643 = f.my_piecewise3(t246, 0, 0.4e1 / 0.9e1 * t634 * t635 + 0.4e1 / 0.3e1 * t247 * t639)
  t647 = t253 * t342
  t654 = t340 * t443 * t333 * t273 / 0.12e2
  t657 = t340 * t131 * t410 * t273
  t659 = t355 ** 2
  t662 = t245 ** 2
  t665 = 0.1e1 / t281 / t662 / t22
  t666 = t65 * t665
  t667 = t351 ** 2
  t677 = 0.2e1 / 0.9e1 * t279 * t666 * t667 - t279 * t349 * (t639 * t6 + 0.2e1 * t249) / 0.6e1
  t678 = f.my_piecewise3(t287, t677, 0)
  t706 = 0.1e1 / t310 / t289
  t711 = t293 * t659 / 0.6e1 - t346 * t678 / 0.18e2 - t296 * t659 / 0.48e2 + t359 * t678 / 0.240e3 + t299 * t659 / 0.640e3 - t363 * t678 / 0.4480e4 - t302 * t659 / 0.11520e5 + t367 * t678 / 0.103680e6 + t305 * t659 / 0.258048e6 - t371 * t678 / 0.2838528e7 - t308 * t659 / 0.6881280e7 + t375 * t678 / 0.89456640e8 + t311 * t659 / 0.212336640e9 - t379 * t678 / 0.3185049600e10 - t706 * t659 / 0.7431782400e10 + t383 * t678 / 0.126340300800e12
  t712 = f.my_piecewise3(t287, 0, t677)
  t717 = t319 ** 2
  t719 = 0.1e1 / t717 / t314
  t720 = t387 ** 2
  t724 = t322 * t394
  t732 = 0.1e1 / t717
  t740 = 0.1e1 / t717 / t319
  t759 = f.my_piecewise3(t286, t711, -0.8e1 / 0.3e1 * t712 * t329 - 0.16e2 / 0.3e1 * t387 * t406 - 0.8e1 / 0.3e1 * t314 * (-t719 * t720 * t322 / 0.2e1 + 0.2e1 * t724 * t720 - t389 * t712 + 0.2e1 * t712 * t326 + 0.4e1 * t387 * t403 + 0.2e1 * t314 * (-0.2e1 * t732 * t720 * t322 + t394 * t712 * t322 / 0.2e1 + t740 * t720 * t322 / 0.4e1 - 0.4e1 * t720 * t323 - t320 * t720 * t322 - 0.4e1 * t398 * t712 - t315 * t712 * t322)))
  t765 = f.my_piecewise3(t243, 0, -0.3e1 / 0.8e1 * t5 * t643 * t335 - t647 / 0.4e1 - 0.3e1 / 0.4e1 * t253 * t412 + t654 - t657 / 0.4e1 - 0.3e1 / 0.8e1 * t340 * t31 * t759 * t273)
  d11 = 0.2e1 * t241 + 0.2e1 * t416 + t6 * (t632 + t765)
  t768 = -t7 - t24
  t769 = f.my_piecewise5(t10, 0, t14, 0, t768)
  t772 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t769)
  t773 = t5 * t772
  t777 = t769 * t6 + t18 + 0.1e1
  t778 = t170 * t777
  t780 = t64 * t778 / 0.6e1
  t781 = f.my_piecewise3(t73, -t780, 0)
  t799 = f.my_piecewise3(t73, 0, -t780)
  t811 = t216 * t799 * t109 / 0.2e1 - 0.4e1 * t220 * t799 - t102 * t799 * t109
  t814 = 0.2e1 * t100 * t811 + 0.2e1 * t799 * t113 - t211 * t799
  t818 = f.my_piecewise3(t72, -t137 * t781 / 0.18e2 + t181 * t781 / 0.240e3 - t185 * t781 / 0.4480e4 + t189 * t781 / 0.103680e6 - t193 * t781 / 0.2838528e7 + t197 * t781 / 0.89456640e8 - t201 * t781 / 0.3185049600e10 + t205 * t781 / 0.126340300800e12, -0.8e1 / 0.3e1 * t100 * t814 - 0.8e1 / 0.3e1 * t799 * t116)
  t819 = t31 * t818
  t820 = t819 * t58
  t824 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t773 * t122 - t135 - 0.3e1 / 0.8e1 * t129 * t820)
  t826 = f.my_piecewise5(t14, 0, t10, 0, -t768)
  t829 = f.my_piecewise3(t246, 0, 0.4e1 / 0.3e1 * t247 * t826)
  t830 = t5 * t829
  t835 = f.p.cam_omega / t277 / t276
  t837 = t835 * t283 * jnp.pi
  t838 = t273 ** 2
  t839 = 0.1e1 / t838
  t840 = t37 * t839
  t848 = params.b * t254 * s2
  t849 = t257 ** 2
  t853 = 0.1e1 / t268 / t267
  t857 = -0.19200000000000000000000000000000000000000000000000e3 * t255 / t259 / t257 / t256 * t269 + 0.11520000000000000000000000000000000000000000000000e4 * t848 / t849 / r1 * t853
  t863 = t826 * t6 + t244 + 0.1e1
  t867 = t837 * t143 * t840 * t857 / 0.4e1 - t279 * t349 * t863 / 0.6e1
  t868 = f.my_piecewise3(t287, t867, 0)
  t886 = f.my_piecewise3(t287, 0, t867)
  t898 = t394 * t886 * t322 / 0.2e1 - 0.4e1 * t398 * t886 - t315 * t886 * t322
  t901 = 0.2e1 * t314 * t898 + 0.2e1 * t886 * t326 - t389 * t886
  t905 = f.my_piecewise3(t286, -t346 * t868 / 0.18e2 + t359 * t868 / 0.240e3 - t363 * t868 / 0.4480e4 + t367 * t868 / 0.103680e6 - t371 * t868 / 0.2838528e7 + t375 * t868 / 0.89456640e8 - t379 * t868 / 0.3185049600e10 + t383 * t868 / 0.126340300800e12, -0.8e1 / 0.3e1 * t314 * t901 - 0.8e1 / 0.3e1 * t886 * t329)
  t906 = t31 * t905
  t907 = t906 * t273
  t910 = t334 * t857
  t914 = f.my_piecewise3(t243, 0, -0.3e1 / 0.8e1 * t830 * t335 - t344 - 0.3e1 / 0.8e1 * t340 * t907 - 0.3e1 / 0.8e1 * t340 * t910)
  t918 = 0.2e1 * t425
  t919 = f.my_piecewise5(t10, 0, t14, 0, t918)
  t923 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t419 * t769 * t26 + 0.4e1 / 0.3e1 * t21 * t919)
  t927 = t773 * t133
  t940 = t129 * t131 * t818 * t58
  t960 = -t140 * t778 * t33 * t36 * t164 / 0.12e2 + 0.2e1 / 0.9e1 * t64 * t65 * t526 * t777 * t172 - t64 * t170 * (t919 * t6 + t26 + t769) / 0.6e1
  t961 = f.my_piecewise3(t73, t960, 0)
  t999 = t79 * t781 * t177 / 0.6e1 - t137 * t961 / 0.18e2 - t82 * t781 * t177 / 0.48e2 + t181 * t961 / 0.240e3 + t85 * t781 * t177 / 0.640e3 - t185 * t961 / 0.4480e4 - t88 * t781 * t177 / 0.11520e5 + t189 * t961 / 0.103680e6 + t91 * t781 * t177 / 0.258048e6 - t193 * t961 / 0.2838528e7 - t94 * t781 * t177 / 0.6881280e7 + t197 * t961 / 0.89456640e8 + t97 * t781 * t177 / 0.212336640e9 - t201 * t961 / 0.3185049600e10 - t567 * t781 * t177 / 0.7431782400e10 + t205 * t961 / 0.126340300800e12
  t1000 = f.my_piecewise3(t73, 0, t960)
  t1005 = t109 * t799
  t1019 = t109 * t209
  t1044 = f.my_piecewise3(t72, t999, -0.8e1 / 0.3e1 * t1000 * t116 - 0.8e1 / 0.3e1 * t799 * t228 - 0.8e1 / 0.3e1 * t209 * t814 - 0.8e1 / 0.3e1 * t100 * (-t580 * t209 * t1005 / 0.2e1 + 0.2e1 * t585 * t799 * t209 - t211 * t1000 + 0.2e1 * t1000 * t113 + 0.2e1 * t799 * t225 + 0.2e1 * t209 * t811 + 0.2e1 * t100 * (-0.2e1 * t593 * t799 * t1019 + t216 * t1000 * t109 / 0.2e1 + t601 * t799 * t1019 / 0.4e1 - 0.4e1 * t209 * t110 * t799 - t107 * t209 * t1005 - 0.4e1 * t220 * t1000 - t102 * t1000 * t109)))
  t1052 = -0.3e1 / 0.8e1 * t5 * t923 * t122 - t927 / 0.8e1 - 0.3e1 / 0.8e1 * t773 * t234 - 0.3e1 / 0.8e1 * t773 * t237 - t436 / 0.8e1 + t447 - t450 / 0.8e1 - t453 / 0.8e1 - 0.3e1 / 0.8e1 * t30 * t820 - t940 / 0.8e1 - 0.3e1 / 0.8e1 * t129 * t31 * t1044 * t58 - 0.3e1 / 0.8e1 * t129 * t819 * t163
  t1053 = f.my_piecewise3(t1, 0, t1052)
  t1057 = f.my_piecewise5(t14, 0, t10, 0, -t918)
  t1061 = f.my_piecewise3(t246, 0, 0.4e1 / 0.9e1 * t634 * t826 * t249 + 0.4e1 / 0.3e1 * t247 * t1057)
  t1065 = t830 * t342
  t1075 = t340 * t131 * t905 * t273
  t1081 = t835 * t349 * jnp.pi
  t1082 = t839 * t857
  t1097 = -t1081 * t483 * t1082 * t351 / 0.12e2 + 0.2e1 / 0.9e1 * t279 * t65 * t665 * t863 * t351 - t279 * t349 * (t1057 * t6 + t249 + t826) / 0.6e1
  t1098 = f.my_piecewise3(t287, t1097, 0)
  t1136 = t293 * t868 * t355 / 0.6e1 - t346 * t1098 / 0.18e2 - t296 * t868 * t355 / 0.48e2 + t359 * t1098 / 0.240e3 + t299 * t868 * t355 / 0.640e3 - t363 * t1098 / 0.4480e4 - t302 * t868 * t355 / 0.11520e5 + t367 * t1098 / 0.103680e6 + t305 * t868 * t355 / 0.258048e6 - t371 * t1098 / 0.2838528e7 - t308 * t868 * t355 / 0.6881280e7 + t375 * t1098 / 0.89456640e8 + t311 * t868 * t355 / 0.212336640e9 - t379 * t1098 / 0.3185049600e10 - t706 * t868 * t355 / 0.7431782400e10 + t383 * t1098 / 0.126340300800e12
  t1137 = f.my_piecewise3(t287, 0, t1097)
  t1142 = t322 * t886
  t1156 = t322 * t387
  t1181 = f.my_piecewise3(t286, t1136, -0.8e1 / 0.3e1 * t1137 * t329 - 0.8e1 / 0.3e1 * t886 * t406 - 0.8e1 / 0.3e1 * t387 * t901 - 0.8e1 / 0.3e1 * t314 * (-t719 * t387 * t1142 / 0.2e1 + 0.2e1 * t724 * t886 * t387 - t389 * t1137 + 0.2e1 * t1137 * t326 + 0.2e1 * t886 * t403 + 0.2e1 * t387 * t898 + 0.2e1 * t314 * (-0.2e1 * t732 * t886 * t1156 + t394 * t1137 * t322 / 0.2e1 + t740 * t886 * t1156 / 0.4e1 - 0.4e1 * t387 * t323 * t886 - t320 * t387 * t1142 - 0.4e1 * t398 * t1137 - t315 * t1137 * t322)))
  t1189 = t340 * t341 * t857
  t1194 = -0.3e1 / 0.8e1 * t5 * t1061 * t335 - t1065 / 0.8e1 - 0.3e1 / 0.8e1 * t830 * t412 - t647 / 0.8e1 + t654 - t657 / 0.8e1 - 0.3e1 / 0.8e1 * t253 * t907 - t1075 / 0.8e1 - 0.3e1 / 0.8e1 * t340 * t31 * t1181 * t273 - 0.3e1 / 0.8e1 * t253 * t910 - t1189 / 0.8e1 - 0.3e1 / 0.8e1 * t340 * t411 * t857
  t1195 = f.my_piecewise3(t243, 0, t1194)
  d12 = t241 + t416 + t824 + t914 + t6 * (t1053 + t1195)
  t1200 = t769 ** 2
  t1204 = 0.2e1 * t23 + 0.2e1 * t425
  t1205 = f.my_piecewise5(t10, 0, t14, 0, t1204)
  t1209 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t419 * t1200 + 0.4e1 / 0.3e1 * t21 * t1205)
  t1217 = t781 ** 2
  t1220 = t777 ** 2
  t1230 = 0.2e1 / 0.9e1 * t64 * t527 * t1220 - t64 * t170 * (t1205 * t6 + 0.2e1 * t769) / 0.6e1
  t1231 = f.my_piecewise3(t73, t1230, 0)
  t1262 = t79 * t1217 / 0.6e1 - t137 * t1231 / 0.18e2 - t82 * t1217 / 0.48e2 + t181 * t1231 / 0.240e3 + t85 * t1217 / 0.640e3 - t185 * t1231 / 0.4480e4 - t88 * t1217 / 0.11520e5 + t189 * t1231 / 0.103680e6 + t91 * t1217 / 0.258048e6 - t193 * t1231 / 0.2838528e7 - t94 * t1217 / 0.6881280e7 + t197 * t1231 / 0.89456640e8 + t97 * t1217 / 0.212336640e9 - t201 * t1231 / 0.3185049600e10 - t567 * t1217 / 0.7431782400e10 + t205 * t1231 / 0.126340300800e12
  t1263 = f.my_piecewise3(t73, 0, t1230)
  t1268 = t799 ** 2
  t1303 = f.my_piecewise3(t72, t1262, -0.8e1 / 0.3e1 * t1263 * t116 - 0.16e2 / 0.3e1 * t799 * t814 - 0.8e1 / 0.3e1 * t100 * (-t580 * t1268 * t109 / 0.2e1 + 0.2e1 * t585 * t1268 - t211 * t1263 + 0.2e1 * t1263 * t113 + 0.4e1 * t799 * t811 + 0.2e1 * t100 * (-0.2e1 * t593 * t1268 * t109 + t216 * t1263 * t109 / 0.2e1 + t601 * t1268 * t109 / 0.4e1 - 0.4e1 * t1268 * t110 - t107 * t1268 * t109 - 0.4e1 * t220 * t1263 - t102 * t1263 * t109)))
  t1309 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t1209 * t122 - t927 / 0.4e1 - 0.3e1 / 0.4e1 * t773 * t820 + t447 - t940 / 0.4e1 - 0.3e1 / 0.8e1 * t129 * t31 * t1303 * t58)
  t1310 = t826 ** 2
  t1314 = f.my_piecewise5(t14, 0, t10, 0, -t1204)
  t1318 = f.my_piecewise3(t246, 0, 0.4e1 / 0.9e1 * t634 * t1310 + 0.4e1 / 0.3e1 * t247 * t1314)
  t1329 = t868 ** 2
  t1340 = t838 ** 2
  t1343 = t857 ** 2
  t1371 = t254 ** 2
  t1376 = t268 ** 2
  t1381 = 0.12160000000000000000000000000000000000000000000000e4 * t255 / t259 / t257 / t256 / r1 * t269 - 0.16512000000000000000000000000000000000000000000000e5 * t848 / t849 / t256 * t853 + 0.55296000000000000000000000000000000000000000000000e5 * params.b * t1371 / t262 / t849 / t257 / t1376
  t1386 = t863 ** 2
  t1396 = 0.3e1 / 0.8e1 * f.p.cam_omega / t277 / t459 / t463 / t839 * t283 * t458 * t472 * t462 / t1340 * t1343 - t1081 * t483 * t1082 * t863 / 0.6e1 - t837 * t143 * t37 / t838 / t273 * t1343 / 0.2e1 + t837 * t143 * t840 * t1381 / 0.4e1 + 0.2e1 / 0.9e1 * t279 * t666 * t1386 - t279 * t349 * (t1314 * t6 + 0.2e1 * t826) / 0.6e1
  t1397 = f.my_piecewise3(t287, t1396, 0)
  t1428 = t293 * t1329 / 0.6e1 - t346 * t1397 / 0.18e2 - t296 * t1329 / 0.48e2 + t359 * t1397 / 0.240e3 + t299 * t1329 / 0.640e3 - t363 * t1397 / 0.4480e4 - t302 * t1329 / 0.11520e5 + t367 * t1397 / 0.103680e6 + t305 * t1329 / 0.258048e6 - t371 * t1397 / 0.2838528e7 - t308 * t1329 / 0.6881280e7 + t375 * t1397 / 0.89456640e8 + t311 * t1329 / 0.212336640e9 - t379 * t1397 / 0.3185049600e10 - t706 * t1329 / 0.7431782400e10 + t383 * t1397 / 0.126340300800e12
  t1429 = f.my_piecewise3(t287, 0, t1396)
  t1434 = t886 ** 2
  t1469 = f.my_piecewise3(t286, t1428, -0.8e1 / 0.3e1 * t1429 * t329 - 0.16e2 / 0.3e1 * t886 * t901 - 0.8e1 / 0.3e1 * t314 * (-t719 * t1434 * t322 / 0.2e1 + 0.2e1 * t724 * t1434 - t389 * t1429 + 0.2e1 * t1429 * t326 + 0.4e1 * t886 * t898 + 0.2e1 * t314 * (-0.2e1 * t732 * t1434 * t322 + t394 * t1429 * t322 / 0.2e1 + t740 * t1434 * t322 / 0.4e1 - 0.4e1 * t1434 * t323 - t320 * t1434 * t322 - 0.4e1 * t398 * t1429 - t315 * t1429 * t322)))
  t1481 = f.my_piecewise3(t243, 0, -0.3e1 / 0.8e1 * t5 * t1318 * t335 - t1065 / 0.4e1 - 0.3e1 / 0.4e1 * t830 * t907 - 0.3e1 / 0.4e1 * t830 * t910 + t654 - t1075 / 0.4e1 - t1189 / 0.4e1 - 0.3e1 / 0.8e1 * t340 * t31 * t1469 * t273 - 0.3e1 / 0.4e1 * t340 * t906 * t857 - 0.3e1 / 0.8e1 * t340 * t334 * t1381)
  d22 = 0.2e1 * t824 + 0.2e1 * t914 + t6 * (t1309 + t1481)
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

