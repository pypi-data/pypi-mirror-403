"""Generated from gga_x_ityh_pbe.mpl."""

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

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  pbe_f = lambda x: pbe_f0(X2S * x)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_enhancement = lambda xs: pbe_f(xs)

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

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  pbe_f = lambda x: pbe_f0(X2S * x)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_enhancement = lambda xs: pbe_f(xs)

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

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  pbe_f = lambda x: pbe_f0(X2S * x)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_enhancement = lambda xs: pbe_f(xs)

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
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = params.mu * t35
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t41 = t40 * s0
  t42 = r0 ** 2
  t43 = r0 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t46 = 0.1e1 / t44 / t42
  t50 = params.kappa + t36 * t41 * t46 / 0.24e2
  t55 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t50)
  t58 = t29 * t34 / t55
  t59 = jnp.sqrt(t58)
  t61 = f.p.cam_omega / t59
  t62 = 2 ** (0.1e1 / 0.3e1)
  t63 = t19 * t6
  t64 = t63 ** (0.1e1 / 0.3e1)
  t65 = 0.1e1 / t64
  t66 = t62 * t65
  t68 = t61 * t66 / 0.2e1
  t69 = 0.135e1 <= t68
  t70 = 0.135e1 < t68
  t71 = f.my_piecewise3(t70, t68, 0.135e1)
  t72 = t71 ** 2
  t75 = t72 ** 2
  t78 = t75 * t72
  t81 = t75 ** 2
  t93 = t81 ** 2
  t97 = f.my_piecewise3(t70, 0.135e1, t68)
  t98 = jnp.sqrt(jnp.pi)
  t99 = 0.1e1 / t97
  t101 = jax.lax.erf(t99 / 0.2e1)
  t103 = t97 ** 2
  t104 = 0.1e1 / t103
  t106 = jnp.exp(-t104 / 0.4e1)
  t107 = t106 - 0.1e1
  t110 = t106 - 0.3e1 / 0.2e1 - 0.2e1 * t103 * t107
  t113 = t98 * t101 + 0.2e1 * t97 * t110
  t117 = f.my_piecewise3(t69, 0.1e1 / t72 / 0.36e2 - 0.1e1 / t75 / 0.960e3 + 0.1e1 / t78 / 0.26880e5 - 0.1e1 / t81 / 0.829440e6 + 0.1e1 / t81 / t72 / 0.28385280e8 - 0.1e1 / t81 / t75 / 0.1073479680e10 + 0.1e1 / t81 / t78 / 0.44590694400e11 - 0.1e1 / t93 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t97 * t113)
  t118 = t27 * t117
  t119 = t118 * t55
  t122 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t119)
  t123 = r1 <= f.p.dens_threshold
  t124 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t125 = 0.1e1 + t124
  t126 = t125 <= f.p.zeta_threshold
  t127 = t125 ** (0.1e1 / 0.3e1)
  t129 = f.my_piecewise3(t126, t22, t127 * t125)
  t130 = t5 * t129
  t131 = t40 * s2
  t132 = r1 ** 2
  t133 = r1 ** (0.1e1 / 0.3e1)
  t134 = t133 ** 2
  t136 = 0.1e1 / t134 / t132
  t140 = params.kappa + t36 * t131 * t136 / 0.24e2
  t145 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t140)
  t148 = t29 * t34 / t145
  t149 = jnp.sqrt(t148)
  t151 = f.p.cam_omega / t149
  t152 = t125 * t6
  t153 = t152 ** (0.1e1 / 0.3e1)
  t154 = 0.1e1 / t153
  t155 = t62 * t154
  t157 = t151 * t155 / 0.2e1
  t158 = 0.135e1 <= t157
  t159 = 0.135e1 < t157
  t160 = f.my_piecewise3(t159, t157, 0.135e1)
  t161 = t160 ** 2
  t164 = t161 ** 2
  t167 = t164 * t161
  t170 = t164 ** 2
  t182 = t170 ** 2
  t186 = f.my_piecewise3(t159, 0.135e1, t157)
  t187 = 0.1e1 / t186
  t189 = jax.lax.erf(t187 / 0.2e1)
  t191 = t186 ** 2
  t192 = 0.1e1 / t191
  t194 = jnp.exp(-t192 / 0.4e1)
  t195 = t194 - 0.1e1
  t198 = t194 - 0.3e1 / 0.2e1 - 0.2e1 * t191 * t195
  t201 = 0.2e1 * t186 * t198 + t98 * t189
  t205 = f.my_piecewise3(t158, 0.1e1 / t161 / 0.36e2 - 0.1e1 / t164 / 0.960e3 + 0.1e1 / t167 / 0.26880e5 - 0.1e1 / t170 / 0.829440e6 + 0.1e1 / t170 / t161 / 0.28385280e8 - 0.1e1 / t170 / t164 / 0.1073479680e10 + 0.1e1 / t170 / t167 / 0.44590694400e11 - 0.1e1 / t182 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t186 * t201)
  t206 = t27 * t205
  t207 = t206 * t145
  t210 = f.my_piecewise3(t123, 0, -0.3e1 / 0.8e1 * t130 * t207)
  t211 = t6 ** 2
  t213 = t16 / t211
  t214 = t7 - t213
  t215 = f.my_piecewise5(t10, 0, t14, 0, t214)
  t218 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t215)
  t222 = t27 ** 2
  t223 = 0.1e1 / t222
  t227 = t26 * t223 * t117 * t55 / 0.8e1
  t228 = t72 * t71
  t229 = 0.1e1 / t228
  t232 = f.p.cam_omega / t59 / t58
  t234 = t29 * t34
  t236 = t55 ** 2
  t237 = 0.1e1 / t236
  t238 = params.kappa ** 2
  t240 = t50 ** 2
  t241 = 0.1e1 / t240
  t242 = t241 * params.mu
  t244 = t35 * t40
  t247 = 0.1e1 / t44 / t42 / r0
  t255 = t62 / t64 / t63
  t261 = -t232 * t66 * t234 * t237 * t238 * t242 * t244 * s0 * t247 / 0.36e2 - t61 * t255 * (t215 * t6 + t18 + 0.1e1) / 0.6e1
  t262 = f.my_piecewise3(t70, t261, 0)
  t265 = t75 * t71
  t266 = 0.1e1 / t265
  t269 = t75 * t228
  t270 = 0.1e1 / t269
  t274 = 0.1e1 / t81 / t71
  t278 = 0.1e1 / t81 / t228
  t282 = 0.1e1 / t81 / t265
  t286 = 0.1e1 / t81 / t269
  t290 = 0.1e1 / t93 / t71
  t294 = f.my_piecewise3(t70, 0, t261)
  t296 = t106 * t104
  t301 = 0.1e1 / t103 / t97
  t305 = t97 * t107
  t317 = f.my_piecewise3(t69, -t229 * t262 / 0.18e2 + t266 * t262 / 0.240e3 - t270 * t262 / 0.4480e4 + t274 * t262 / 0.103680e6 - t278 * t262 / 0.2838528e7 + t282 * t262 / 0.89456640e8 - t286 * t262 / 0.3185049600e10 + t290 * t262 / 0.126340300800e12, -0.8e1 / 0.3e1 * t294 * t113 - 0.8e1 / 0.3e1 * t97 * (-t296 * t294 + 0.2e1 * t294 * t110 + 0.2e1 * t97 * (t301 * t294 * t106 / 0.2e1 - 0.4e1 * t305 * t294 - t99 * t294 * t106)))
  t330 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t218 * t119 - t227 - 0.3e1 / 0.8e1 * t26 * t27 * t317 * t55 + t26 * t118 * t238 * t242 * t35 * t41 * t247 / 0.24e2)
  t332 = f.my_piecewise5(t14, 0, t10, 0, -t214)
  t335 = f.my_piecewise3(t126, 0, 0.4e1 / 0.3e1 * t127 * t332)
  t342 = t130 * t223 * t205 * t145 / 0.8e1
  t343 = t161 * t160
  t344 = 0.1e1 / t343
  t347 = t62 / t153 / t152
  t352 = t151 * t347 * (t332 * t6 + t124 + 0.1e1) / 0.6e1
  t353 = f.my_piecewise3(t159, -t352, 0)
  t356 = t164 * t160
  t357 = 0.1e1 / t356
  t360 = t164 * t343
  t361 = 0.1e1 / t360
  t365 = 0.1e1 / t170 / t160
  t369 = 0.1e1 / t170 / t343
  t373 = 0.1e1 / t170 / t356
  t377 = 0.1e1 / t170 / t360
  t381 = 0.1e1 / t182 / t160
  t385 = f.my_piecewise3(t159, 0, -t352)
  t387 = t194 * t192
  t392 = 0.1e1 / t191 / t186
  t396 = t186 * t195
  t408 = f.my_piecewise3(t158, -t344 * t353 / 0.18e2 + t357 * t353 / 0.240e3 - t361 * t353 / 0.4480e4 + t365 * t353 / 0.103680e6 - t369 * t353 / 0.2838528e7 + t373 * t353 / 0.89456640e8 - t377 * t353 / 0.3185049600e10 + t381 * t353 / 0.126340300800e12, -0.8e1 / 0.3e1 * t385 * t201 - 0.8e1 / 0.3e1 * t186 * (-t387 * t385 + 0.2e1 * t385 * t198 + 0.2e1 * t186 * (t392 * t385 * t194 / 0.2e1 - 0.4e1 * t396 * t385 - t187 * t385 * t194)))
  t414 = f.my_piecewise3(t123, 0, -0.3e1 / 0.8e1 * t5 * t335 * t207 - t342 - 0.3e1 / 0.8e1 * t130 * t27 * t408 * t145)
  vrho_0_ = t122 + t210 + t6 * (t330 + t414)
  t417 = -t7 - t213
  t418 = f.my_piecewise5(t10, 0, t14, 0, t417)
  t421 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t418)
  t429 = t61 * t255 * (t418 * t6 + t18 + 0.1e1) / 0.6e1
  t430 = f.my_piecewise3(t70, -t429, 0)
  t448 = f.my_piecewise3(t70, 0, -t429)
  t467 = f.my_piecewise3(t69, -t229 * t430 / 0.18e2 + t266 * t430 / 0.240e3 - t270 * t430 / 0.4480e4 + t274 * t430 / 0.103680e6 - t278 * t430 / 0.2838528e7 + t282 * t430 / 0.89456640e8 - t286 * t430 / 0.3185049600e10 + t290 * t430 / 0.126340300800e12, -0.8e1 / 0.3e1 * t448 * t113 - 0.8e1 / 0.3e1 * t97 * (-t296 * t448 + 0.2e1 * t448 * t110 + 0.2e1 * t97 * (t301 * t448 * t106 / 0.2e1 - 0.4e1 * t305 * t448 - t99 * t448 * t106)))
  t473 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t421 * t119 - t227 - 0.3e1 / 0.8e1 * t26 * t27 * t467 * t55)
  t475 = f.my_piecewise5(t14, 0, t10, 0, -t417)
  t478 = f.my_piecewise3(t126, 0, 0.4e1 / 0.3e1 * t127 * t475)
  t484 = f.p.cam_omega / t149 / t148
  t487 = t145 ** 2
  t488 = 0.1e1 / t487
  t490 = t140 ** 2
  t491 = 0.1e1 / t490
  t492 = t491 * params.mu
  t496 = 0.1e1 / t134 / t132 / r1
  t507 = -t484 * t155 * t234 * t488 * t238 * t492 * t244 * s2 * t496 / 0.36e2 - t151 * t347 * (t475 * t6 + t124 + 0.1e1) / 0.6e1
  t508 = f.my_piecewise3(t159, t507, 0)
  t526 = f.my_piecewise3(t159, 0, t507)
  t545 = f.my_piecewise3(t158, -t344 * t508 / 0.18e2 + t357 * t508 / 0.240e3 - t361 * t508 / 0.4480e4 + t365 * t508 / 0.103680e6 - t369 * t508 / 0.2838528e7 + t373 * t508 / 0.89456640e8 - t377 * t508 / 0.3185049600e10 + t381 * t508 / 0.126340300800e12, -0.8e1 / 0.3e1 * t526 * t201 - 0.8e1 / 0.3e1 * t186 * (-t387 * t526 + 0.2e1 * t526 * t198 + 0.2e1 * t186 * (t392 * t526 * t194 / 0.2e1 - 0.4e1 * t396 * t526 - t187 * t526 * t194)))
  t558 = f.my_piecewise3(t123, 0, -0.3e1 / 0.8e1 * t5 * t478 * t207 - t342 - 0.3e1 / 0.8e1 * t130 * t27 * t545 * t145 + t130 * t206 * t238 * t492 * t35 * t131 * t496 / 0.24e2)
  vrho_1_ = t122 + t210 + t6 * (t473 + t558)
  t563 = t28 * t32
  t567 = t238 * t241
  t573 = t232 * t62 * t65 * jnp.pi * t563 * t33 * t237 * t567 * t36 * t40 * t46 / 0.96e2
  t574 = f.my_piecewise3(t70, t573, 0)
  t592 = f.my_piecewise3(t70, 0, t573)
  t611 = f.my_piecewise3(t69, -t229 * t574 / 0.18e2 + t266 * t574 / 0.240e3 - t270 * t574 / 0.4480e4 + t274 * t574 / 0.103680e6 - t278 * t574 / 0.2838528e7 + t282 * t574 / 0.89456640e8 - t286 * t574 / 0.3185049600e10 + t290 * t574 / 0.126340300800e12, -0.8e1 / 0.3e1 * t592 * t113 - 0.8e1 / 0.3e1 * t97 * (-t296 * t592 + 0.2e1 * t592 * t110 + 0.2e1 * t97 * (t301 * t592 * t106 / 0.2e1 - 0.4e1 * t305 * t592 - t99 * t592 * t106)))
  t625 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * t611 * t55 - t5 * t25 * t27 * t117 * t567 * params.mu * t244 * t46 / 0.64e2)
  vsigma_0_ = t6 * t625
  vsigma_1_ = 0.0e0
  t631 = t238 * t491
  t637 = t484 * t62 * t154 * jnp.pi * t563 * t33 * t488 * t631 * t36 * t40 * t136 / 0.96e2
  t638 = f.my_piecewise3(t159, t637, 0)
  t656 = f.my_piecewise3(t159, 0, t637)
  t675 = f.my_piecewise3(t158, -t344 * t638 / 0.18e2 + t357 * t638 / 0.240e3 - t361 * t638 / 0.4480e4 + t365 * t638 / 0.103680e6 - t369 * t638 / 0.2838528e7 + t373 * t638 / 0.89456640e8 - t377 * t638 / 0.3185049600e10 + t381 * t638 / 0.126340300800e12, -0.8e1 / 0.3e1 * t656 * t201 - 0.8e1 / 0.3e1 * t186 * (-t387 * t656 + 0.2e1 * t656 * t198 + 0.2e1 * t186 * (t392 * t656 * t194 / 0.2e1 - 0.4e1 * t396 * t656 - t187 * t656 * t194)))
  t689 = f.my_piecewise3(t123, 0, -0.3e1 / 0.8e1 * t130 * t27 * t675 * t145 - t5 * t129 * t27 * t205 * t631 * params.mu * t244 * t136 / 0.64e2)
  vsigma_2_ = t6 * t689
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

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  pbe_f = lambda x: pbe_f0(X2S * x)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_enhancement = lambda xs: pbe_f(xs)

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
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t6 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t3 ** 2
  t21 = jnp.pi * t20
  t23 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t25 = 4 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t23 * t25
  t27 = 6 ** (0.1e1 / 0.3e1)
  t28 = params.mu * t27
  t29 = jnp.pi ** 2
  t30 = t29 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = 0.1e1 / t31
  t34 = 2 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = r0 ** 2
  t38 = t19 ** 2
  t40 = 0.1e1 / t38 / t37
  t44 = params.kappa + t28 * t32 * s0 * t35 * t40 / 0.24e2
  t49 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t44)
  t52 = t21 * t26 / t49
  t53 = jnp.sqrt(t52)
  t55 = f.p.cam_omega / t53
  t56 = t11 * r0
  t57 = t56 ** (0.1e1 / 0.3e1)
  t58 = 0.1e1 / t57
  t61 = t55 * t34 * t58 / 0.2e1
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
  t115 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t110 * t49)
  t121 = t65 * t64
  t122 = 0.1e1 / t121
  t128 = f.p.cam_omega / t53 / t52 * t58 * t21 * t26
  t129 = t49 ** 2
  t131 = params.kappa ** 2
  t132 = 0.1e1 / t129 * t131
  t133 = t44 ** 2
  t134 = 0.1e1 / t133
  t135 = t134 * params.mu
  t137 = t27 * t32
  t138 = t37 * r0
  t152 = -t128 * t132 * t135 * t137 * s0 / t38 / t138 / 0.18e2 - t55 * t34 / t57 / t56 * t11 / 0.6e1
  t153 = f.my_piecewise3(t63, t152, 0)
  t156 = t68 * t64
  t157 = 0.1e1 / t156
  t160 = t68 * t121
  t161 = 0.1e1 / t160
  t165 = 0.1e1 / t74 / t64
  t169 = 0.1e1 / t74 / t121
  t173 = 0.1e1 / t74 / t156
  t177 = 0.1e1 / t74 / t160
  t181 = 0.1e1 / t86 / t64
  t185 = f.my_piecewise3(t63, 0, t152)
  t187 = t99 * t97
  t192 = 0.1e1 / t96 / t90
  t196 = t90 * t100
  t208 = f.my_piecewise3(t62, -t122 * t153 / 0.18e2 + t157 * t153 / 0.240e3 - t161 * t153 / 0.4480e4 + t165 * t153 / 0.103680e6 - t169 * t153 / 0.2838528e7 + t173 * t153 / 0.89456640e8 - t177 * t153 / 0.3185049600e10 + t181 * t153 / 0.126340300800e12, -0.8e1 / 0.3e1 * t185 * t106 - 0.8e1 / 0.3e1 * t90 * (-t187 * t185 + 0.2e1 * t185 * t103 + 0.2e1 * t90 * (t192 * t185 * t99 / 0.2e1 - 0.4e1 * t196 * t185 - t92 * t185 * t99)))
  t225 = f.my_piecewise3(t2, 0, -t18 / t38 * t110 * t49 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t208 * t49 + t18 / t19 / t138 * t110 * t131 * t135 * t27 * t32 * s0 * t35 / 0.24e2)
  vrho_0_ = 0.2e1 * r0 * t225 + 0.2e1 * t115
  t233 = t128 * t132 * t134 * t28 * t32 * t40 / 0.48e2
  t234 = f.my_piecewise3(t63, t233, 0)
  t252 = f.my_piecewise3(t63, 0, t233)
  t271 = f.my_piecewise3(t62, -t122 * t234 / 0.18e2 + t157 * t234 / 0.240e3 - t161 * t234 / 0.4480e4 + t165 * t234 / 0.103680e6 - t169 * t234 / 0.2838528e7 + t173 * t234 / 0.89456640e8 - t177 * t234 / 0.3185049600e10 + t181 * t234 / 0.126340300800e12, -0.8e1 / 0.3e1 * t252 * t106 - 0.8e1 / 0.3e1 * t90 * (-t187 * t252 + 0.2e1 * t252 * t103 + 0.2e1 * t90 * (t192 * t252 * t99 / 0.2e1 - 0.4e1 * t196 * t252 - t92 * t252 * t99)))
  t288 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t271 * t49 - t6 * t17 / t19 / t37 * t110 * t131 * t134 * params.mu * t137 * t35 / 0.64e2)
  vsigma_0_ = 0.2e1 * r0 * t288
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
  t18 = t6 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t22 = t3 ** 2
  t23 = jnp.pi * t22
  t25 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t27 = 4 ** (0.1e1 / 0.3e1)
  t28 = t26 * t27
  t29 = 6 ** (0.1e1 / 0.3e1)
  t30 = params.mu * t29
  t31 = jnp.pi ** 2
  t32 = t31 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = 0.1e1 / t33
  t36 = 2 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = s0 * t37
  t39 = r0 ** 2
  t41 = 0.1e1 / t20 / t39
  t45 = params.kappa + t30 * t34 * t38 * t41 / 0.24e2
  t50 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t45)
  t53 = t23 * t28 / t50
  t54 = jnp.sqrt(t53)
  t56 = f.p.cam_omega / t54
  t57 = t11 * r0
  t58 = t57 ** (0.1e1 / 0.3e1)
  t59 = 0.1e1 / t58
  t62 = t56 * t36 * t59 / 0.2e1
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
  t95 = jnp.erf(t93 / 0.2e1)
  t97 = t91 ** 2
  t98 = 0.1e1 / t97
  t100 = jnp.exp(-t98 / 0.4e1)
  t101 = t100 - 0.1e1
  t104 = t100 - 0.3e1 / 0.2e1 - 0.2e1 * t97 * t101
  t107 = 0.2e1 * t91 * t104 + t92 * t95
  t111 = f.my_piecewise3(t63, 0.1e1 / t66 / 0.36e2 - t70 / 0.960e3 + t73 / 0.26880e5 - t76 / 0.829440e6 + t79 / 0.28385280e8 - t82 / 0.1073479680e10 + t85 / 0.44590694400e11 - t88 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t91 * t107)
  t116 = t66 * t65
  t117 = 0.1e1 / t116
  t120 = f.p.cam_omega / t54 / t53
  t122 = t23 * t28
  t123 = t120 * t59 * t122
  t124 = t50 ** 2
  t125 = 0.1e1 / t124
  t126 = params.kappa ** 2
  t127 = t125 * t126
  t128 = t45 ** 2
  t129 = 0.1e1 / t128
  t130 = t129 * params.mu
  t131 = t127 * t130
  t132 = t29 * t34
  t133 = t39 * r0
  t135 = 0.1e1 / t20 / t133
  t142 = 0.1e1 / t58 / t57
  t147 = -t123 * t131 * t132 * s0 * t135 / 0.18e2 - t56 * t36 * t142 * t11 / 0.6e1
  t148 = f.my_piecewise3(t64, t147, 0)
  t151 = t69 * t65
  t152 = 0.1e1 / t151
  t155 = t69 * t116
  t156 = 0.1e1 / t155
  t160 = 0.1e1 / t75 / t65
  t164 = 0.1e1 / t75 / t116
  t168 = 0.1e1 / t75 / t151
  t172 = 0.1e1 / t75 / t155
  t176 = 0.1e1 / t87 / t65
  t180 = f.my_piecewise3(t64, 0, t147)
  t182 = t100 * t98
  t187 = 0.1e1 / t97 / t91
  t191 = t91 * t101
  t196 = t187 * t180 * t100 / 0.2e1 - 0.4e1 * t191 * t180 - t93 * t180 * t100
  t199 = 0.2e1 * t180 * t104 - t182 * t180 + 0.2e1 * t91 * t196
  t203 = f.my_piecewise3(t63, -t117 * t148 / 0.18e2 + t152 * t148 / 0.240e3 - t156 * t148 / 0.4480e4 + t160 * t148 / 0.103680e6 - t164 * t148 / 0.2838528e7 + t168 * t148 / 0.89456640e8 - t172 * t148 / 0.3185049600e10 + t176 * t148 / 0.126340300800e12, -0.8e1 / 0.3e1 * t180 * t107 - 0.8e1 / 0.3e1 * t91 * t199)
  t209 = 0.1e1 / t19 / t133
  t214 = t34 * s0
  t216 = t130 * t29 * t214 * t37
  t220 = f.my_piecewise3(t2, 0, -t18 * t21 * t111 * t50 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t203 * t50 + t18 * t209 * t111 * t126 * t216 / 0.24e2)
  t232 = t39 ** 2
  t240 = t148 ** 2
  t243 = t31 * t3
  t244 = t25 ** 2
  t245 = 0.1e1 / t244
  t246 = t27 ** 2
  t247 = t245 * t246
  t253 = f.p.cam_omega / t54 / t243 / t247 / t125 / 0.3e1
  t257 = t124 ** 2
  t258 = 0.1e1 / t257
  t261 = t253 * t59 * t31 * t3 * t245 * t246 * t258
  t262 = t126 ** 2
  t263 = t128 ** 2
  t264 = 0.1e1 / t263
  t266 = params.mu ** 2
  t267 = t29 ** 2
  t268 = t266 * t267
  t269 = t262 * t264 * t268
  t271 = 0.1e1 / t32 / t31
  t272 = s0 ** 2
  t273 = t271 * t272
  t274 = t232 * t133
  t278 = t273 / t19 / t274 * t37
  t279 = t269 * t278
  t284 = t22 * t26
  t286 = t284 * t27 * t125
  t288 = t126 * t129
  t296 = t120 * t59 * jnp.pi
  t298 = 0.1e1 / t124 / t50
  t301 = t296 * t284 * t27 * t298
  t304 = t296 * t286
  t306 = 0.1e1 / t128 / t45
  t307 = t126 * t306
  t308 = t307 * t268
  t319 = t11 ** 2
  t327 = t261 * t279 / 0.36e2 + t120 * t142 * jnp.pi * t286 * t288 * t30 * t214 * t135 * t11 / 0.27e2 - t301 * t279 / 0.81e2 - t304 * t308 * t278 / 0.81e2 + 0.11e2 / 0.54e2 * t123 * t131 * t132 * s0 / t20 / t232 + 0.2e1 / 0.9e1 * t56 * t36 / t58 / t39
  t328 = f.my_piecewise3(t64, t327, 0)
  t356 = 0.1e1 / t87 / t66
  t361 = t70 * t240 / 0.6e1 - t117 * t328 / 0.18e2 - t73 * t240 / 0.48e2 + t152 * t328 / 0.240e3 + t76 * t240 / 0.640e3 - t156 * t328 / 0.4480e4 - t79 * t240 / 0.11520e5 + t160 * t328 / 0.103680e6 + t82 * t240 / 0.258048e6 - t164 * t328 / 0.2838528e7 - t85 * t240 / 0.6881280e7 + t168 * t328 / 0.89456640e8 + t88 * t240 / 0.212336640e9 - t172 * t328 / 0.3185049600e10 - t356 * t240 / 0.7431782400e10 + t176 * t328 / 0.126340300800e12
  t362 = f.my_piecewise3(t64, 0, t327)
  t367 = t97 ** 2
  t369 = 0.1e1 / t367 / t91
  t370 = t180 ** 2
  t374 = t100 * t187
  t382 = 0.1e1 / t367
  t390 = 0.1e1 / t367 / t97
  t409 = f.my_piecewise3(t63, t361, -0.8e1 / 0.3e1 * t362 * t107 - 0.16e2 / 0.3e1 * t180 * t199 - 0.8e1 / 0.3e1 * t91 * (-t369 * t370 * t100 / 0.2e1 + 0.2e1 * t374 * t370 - t182 * t362 + 0.2e1 * t362 * t104 + 0.4e1 * t180 * t196 + 0.2e1 * t91 * (-0.2e1 * t382 * t370 * t100 + t187 * t362 * t100 / 0.2e1 + t390 * t370 * t100 / 0.4e1 - 0.4e1 * t370 * t101 - t98 * t370 * t100 - 0.4e1 * t191 * t362 - t93 * t362 * t100)))
  t423 = t306 * t266
  t424 = t423 * t267
  t430 = f.my_piecewise3(t2, 0, t18 / t20 / r0 * t111 * t50 / 0.12e2 - t18 * t21 * t203 * t50 / 0.4e1 - t18 / t19 / t232 * t111 * t126 * t216 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t409 * t50 + t18 * t209 * t203 * t126 * t216 / 0.12e2 + t18 / t274 * t111 * t126 * t424 * t273 * t36 / 0.54e2)
  v2rho2_0_ = 0.2e1 * r0 * t430 + 0.4e1 * t220
  t433 = t127 * t129
  t438 = t123 * t433 * t30 * t34 * t41 / 0.48e2
  t439 = f.my_piecewise3(t64, t438, 0)
  t457 = f.my_piecewise3(t64, 0, t438)
  t469 = t187 * t457 * t100 / 0.2e1 - 0.4e1 * t191 * t457 - t93 * t457 * t100
  t472 = 0.2e1 * t457 * t104 - t182 * t457 + 0.2e1 * t91 * t469
  t476 = f.my_piecewise3(t63, -t117 * t439 / 0.18e2 + t152 * t439 / 0.240e3 - t156 * t439 / 0.4480e4 + t160 * t439 / 0.103680e6 - t164 * t439 / 0.2838528e7 + t168 * t439 / 0.89456640e8 - t172 * t439 / 0.3185049600e10 + t176 * t439 / 0.126340300800e12, -0.8e1 / 0.3e1 * t457 * t107 - 0.8e1 / 0.3e1 * t91 * t472)
  t483 = t17 / t19 / t39
  t488 = t288 * params.mu * t132 * t37
  t492 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t476 * t50 - t6 * t483 * t111 * t488 / 0.64e2)
  t500 = t232 * t39
  t504 = t271 / t19 / t500 * t38
  t505 = t269 * t504
  t525 = -t261 * t505 / 0.96e2 - t120 * t142 * t122 * t131 * t132 * t41 * t11 / 0.144e3 + t301 * t505 / 0.216e3 + t304 * t308 * t504 / 0.216e3 - t123 * t433 * t30 * t34 * t135 / 0.18e2
  t526 = f.my_piecewise3(t64, t525, 0)
  t564 = t70 * t439 * t148 / 0.6e1 - t117 * t526 / 0.18e2 - t73 * t439 * t148 / 0.48e2 + t152 * t526 / 0.240e3 + t76 * t439 * t148 / 0.640e3 - t156 * t526 / 0.4480e4 - t79 * t439 * t148 / 0.11520e5 + t160 * t526 / 0.103680e6 + t82 * t439 * t148 / 0.258048e6 - t164 * t526 / 0.2838528e7 - t85 * t439 * t148 / 0.6881280e7 + t168 * t526 / 0.89456640e8 + t88 * t439 * t148 / 0.212336640e9 - t172 * t526 / 0.3185049600e10 - t356 * t439 * t148 / 0.7431782400e10 + t176 * t526 / 0.126340300800e12
  t565 = f.my_piecewise3(t64, 0, t525)
  t570 = t100 * t457
  t584 = t100 * t180
  t609 = f.my_piecewise3(t63, t564, -0.8e1 / 0.3e1 * t565 * t107 - 0.8e1 / 0.3e1 * t457 * t199 - 0.8e1 / 0.3e1 * t180 * t472 - 0.8e1 / 0.3e1 * t91 * (-t369 * t180 * t570 / 0.2e1 + 0.2e1 * t374 * t457 * t180 - t182 * t565 + 0.2e1 * t565 * t104 + 0.2e1 * t457 * t196 + 0.2e1 * t180 * t469 + 0.2e1 * t91 * (-0.2e1 * t382 * t457 * t584 + t187 * t565 * t100 / 0.2e1 + t390 * t457 * t584 / 0.4e1 - 0.4e1 * t180 * t101 * t457 - t98 * t180 * t570 - 0.4e1 * t191 * t565 - t93 * t565 * t100)))
  t638 = f.my_piecewise3(t2, 0, -t18 * t21 * t476 * t50 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t609 * t50 + t18 * t209 * t476 * t126 * t216 / 0.24e2 + 0.7e1 / 0.192e3 * t6 * t17 * t209 * t111 * t488 - t6 * t483 * t203 * t488 / 0.64e2 - t18 / t500 * t111 * t126 * t424 * t271 * t36 * s0 / 0.144e3)
  v2rhosigma_0_ = 0.2e1 * r0 * t638 + 0.2e1 * t492
  t641 = t439 ** 2
  t648 = t264 * t266
  t650 = t267 * t271
  t651 = t232 * r0
  t655 = t650 / t19 / t651 * t37
  t668 = t253 * t59 * t243 * t247 * t258 * t262 * t648 * t655 / 0.256e3 - t123 * t298 * t262 * t648 * t655 / 0.576e3 - t123 * t127 * t423 * t655 / 0.576e3
  t669 = f.my_piecewise3(t64, t668, 0)
  t700 = t70 * t641 / 0.6e1 - t117 * t669 / 0.18e2 - t73 * t641 / 0.48e2 + t152 * t669 / 0.240e3 + t76 * t641 / 0.640e3 - t156 * t669 / 0.4480e4 - t79 * t641 / 0.11520e5 + t160 * t669 / 0.103680e6 + t82 * t641 / 0.258048e6 - t164 * t669 / 0.2838528e7 - t85 * t641 / 0.6881280e7 + t168 * t669 / 0.89456640e8 + t88 * t641 / 0.212336640e9 - t172 * t669 / 0.3185049600e10 - t356 * t641 / 0.7431782400e10 + t176 * t669 / 0.126340300800e12
  t701 = f.my_piecewise3(t64, 0, t668)
  t706 = t457 ** 2
  t741 = f.my_piecewise3(t63, t700, -0.8e1 / 0.3e1 * t701 * t107 - 0.16e2 / 0.3e1 * t457 * t472 - 0.8e1 / 0.3e1 * t91 * (-t369 * t706 * t100 / 0.2e1 + 0.2e1 * t374 * t706 - t182 * t701 + 0.2e1 * t701 * t104 + 0.4e1 * t457 * t469 + 0.2e1 * t91 * (-0.2e1 * t382 * t706 * t100 + t187 * t701 * t100 / 0.2e1 + t390 * t706 * t100 / 0.4e1 - 0.4e1 * t706 * t101 - t98 * t706 * t100 - 0.4e1 * t191 * t701 - t93 * t701 * t100)))
  t760 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t741 * t50 - t6 * t483 * t476 * t488 / 0.32e2 + t6 * t17 / t651 * t111 * t307 * t266 * t650 * t36 / 0.384e3)
  v2sigma2_0_ = 0.2e1 * r0 * t760

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
  t24 = jnp.pi * t23
  t26 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t26
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = t27 * t28
  t30 = 6 ** (0.1e1 / 0.3e1)
  t31 = params.mu * t30
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = 0.1e1 / t34
  t37 = 2 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t40 = r0 ** 2
  t42 = 0.1e1 / t20 / t40
  t46 = params.kappa + t31 * t35 * s0 * t38 * t42 / 0.24e2
  t51 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t46)
  t54 = t24 * t29 / t51
  t55 = jnp.sqrt(t54)
  t57 = f.p.cam_omega / t55
  t58 = t11 * r0
  t59 = t58 ** (0.1e1 / 0.3e1)
  t60 = 0.1e1 / t59
  t63 = t57 * t37 * t60 / 0.2e1
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
  t117 = 0.1e1 / t20
  t118 = t67 * t66
  t119 = 0.1e1 / t118
  t122 = f.p.cam_omega / t55 / t54
  t123 = t122 * t60
  t125 = t123 * t24 * t29
  t126 = t51 ** 2
  t127 = 0.1e1 / t126
  t128 = params.kappa ** 2
  t129 = t127 * t128
  t130 = t46 ** 2
  t131 = 0.1e1 / t130
  t132 = t131 * params.mu
  t133 = t129 * t132
  t134 = t30 * t35
  t135 = t40 * r0
  t137 = 0.1e1 / t20 / t135
  t144 = 0.1e1 / t59 / t58
  t149 = -t125 * t133 * t134 * s0 * t137 / 0.18e2 - t57 * t37 * t144 * t11 / 0.6e1
  t150 = f.my_piecewise3(t65, t149, 0)
  t153 = t70 * t66
  t154 = 0.1e1 / t153
  t157 = t70 * t118
  t158 = 0.1e1 / t157
  t162 = 0.1e1 / t76 / t66
  t166 = 0.1e1 / t76 / t118
  t170 = 0.1e1 / t76 / t153
  t174 = 0.1e1 / t76 / t157
  t178 = 0.1e1 / t88 / t66
  t182 = f.my_piecewise3(t65, 0, t149)
  t184 = t101 * t99
  t188 = t98 * t92
  t189 = 0.1e1 / t188
  t193 = t92 * t102
  t198 = t189 * t182 * t101 / 0.2e1 - 0.4e1 * t193 * t182 - t94 * t182 * t101
  t201 = 0.2e1 * t182 * t105 - t184 * t182 + 0.2e1 * t92 * t198
  t205 = f.my_piecewise3(t64, -t119 * t150 / 0.18e2 + t154 * t150 / 0.240e3 - t158 * t150 / 0.4480e4 + t162 * t150 / 0.103680e6 - t166 * t150 / 0.2838528e7 + t170 * t150 / 0.89456640e8 - t174 * t150 / 0.3185049600e10 + t178 * t150 / 0.126340300800e12, -0.8e1 / 0.3e1 * t182 * t108 - 0.8e1 / 0.3e1 * t92 * t201)
  t210 = t40 ** 2
  t212 = 0.1e1 / t19 / t210
  t217 = t35 * s0
  t219 = t132 * t30 * t217 * t38
  t222 = t150 ** 2
  t226 = t26 ** 2
  t227 = 0.1e1 / t226
  t228 = t28 ** 2
  t229 = t227 * t228
  t235 = f.p.cam_omega / t55 / t32 / t3 / t229 / t127 / 0.3e1
  t239 = t126 ** 2
  t240 = 0.1e1 / t239
  t242 = t3 * t227 * t228 * t240
  t243 = t235 * t60 * t32 * t242
  t244 = t128 ** 2
  t245 = t130 ** 2
  t246 = 0.1e1 / t245
  t248 = params.mu ** 2
  t249 = t30 ** 2
  t250 = t248 * t249
  t251 = t244 * t246 * t250
  t254 = s0 ** 2
  t255 = 0.1e1 / t33 / t32 * t254
  t256 = t210 * t135
  t258 = 0.1e1 / t19 / t256
  t260 = t255 * t258 * t38
  t261 = t251 * t260
  t265 = t122 * t144 * jnp.pi
  t266 = t23 * t27
  t268 = t266 * t28 * t127
  t269 = t265 * t268
  t271 = t128 * t131 * t31
  t278 = t122 * t60 * jnp.pi
  t280 = 0.1e1 / t126 / t51
  t282 = t266 * t28 * t280
  t283 = t278 * t282
  t286 = t278 * t268
  t288 = 0.1e1 / t130 / t46
  t290 = t128 * t288 * t250
  t295 = 0.1e1 / t20 / t210
  t301 = t11 ** 2
  t304 = 0.1e1 / t59 / t301 / t40
  t309 = t243 * t261 / 0.36e2 + t269 * t271 * t217 * t137 * t11 / 0.27e2 - t283 * t261 / 0.81e2 - t286 * t290 * t260 / 0.81e2 + 0.11e2 / 0.54e2 * t125 * t133 * t134 * s0 * t295 + 0.2e1 / 0.9e1 * t57 * t37 * t304 * t301
  t310 = f.my_piecewise3(t65, t309, 0)
  t338 = 0.1e1 / t88 / t67
  t343 = t71 * t222 / 0.6e1 - t119 * t310 / 0.18e2 - t74 * t222 / 0.48e2 + t154 * t310 / 0.240e3 + t77 * t222 / 0.640e3 - t158 * t310 / 0.4480e4 - t80 * t222 / 0.11520e5 + t162 * t310 / 0.103680e6 + t83 * t222 / 0.258048e6 - t166 * t310 / 0.2838528e7 - t86 * t222 / 0.6881280e7 + t170 * t310 / 0.89456640e8 + t89 * t222 / 0.212336640e9 - t174 * t310 / 0.3185049600e10 - t338 * t222 / 0.7431782400e10 + t178 * t310 / 0.126340300800e12
  t344 = f.my_piecewise3(t65, 0, t309)
  t349 = t98 ** 2
  t351 = 0.1e1 / t349 / t92
  t352 = t182 ** 2
  t356 = t101 * t189
  t364 = 0.1e1 / t349
  t372 = 0.1e1 / t349 / t98
  t384 = -0.2e1 * t364 * t352 * t101 + t189 * t344 * t101 / 0.2e1 + t372 * t352 * t101 / 0.4e1 - 0.4e1 * t352 * t102 - t99 * t352 * t101 - 0.4e1 * t193 * t344 - t94 * t344 * t101
  t387 = -t351 * t352 * t101 / 0.2e1 + 0.2e1 * t356 * t352 - t184 * t344 + 0.2e1 * t344 * t105 + 0.4e1 * t182 * t198 + 0.2e1 * t92 * t384
  t391 = f.my_piecewise3(t64, t343, -0.8e1 / 0.3e1 * t344 * t108 - 0.16e2 / 0.3e1 * t182 * t201 - 0.8e1 / 0.3e1 * t92 * t387)
  t397 = 0.1e1 / t19 / t135
  t403 = 0.1e1 / t256
  t410 = t288 * t248 * t249 * t255 * t37
  t414 = f.my_piecewise3(t2, 0, t18 * t22 * t112 * t51 / 0.12e2 - t18 * t117 * t205 * t51 / 0.4e1 - t18 * t212 * t112 * t128 * t219 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t391 * t51 + t18 * t397 * t205 * t128 * t219 / 0.12e2 + t18 * t403 * t112 * t128 * t410 / 0.54e2)
  t424 = t210 * r0
  t441 = t210 ** 2
  t448 = t301 * t11
  t456 = t32 ** 2
  t465 = t244 * t128
  t469 = 0.1e1 / t245 / t130
  t470 = t248 * params.mu
  t472 = t254 * s0
  t474 = 0.1e1 / t441 / t135
  t490 = t255 / t19 / t441 * t38
  t494 = t251 * t490
  t505 = t255 * t258 * t11 * t38
  t506 = t251 * t505
  t531 = t235 * t60 / t32 * t3 * t229
  t538 = t470 * t472 * t474 * t37
  t544 = 0.1e1 / t245 / t46
  t553 = t123 / t32 / jnp.pi * t23 * t29
  t568 = -0.14e2 / 0.27e2 * t57 * t37 / t59 / t135 - 0.5e1 / 0.162e3 * f.p.cam_omega / t55 / t456 / t280 * t60 / t239 / t126 * t465 * t469 * t470 * t472 * t474 * t37 - 0.77e2 / 0.81e2 * t125 * t133 * t134 * s0 / t20 / t424 + 0.11e2 / 0.81e2 * t286 * t290 * t490 + 0.11e2 / 0.81e2 * t283 * t494 - 0.11e2 / 0.54e2 * t269 * t271 * t217 * t295 * t11 + t265 * t282 * t506 / 0.81e2 + t269 * t290 * t505 / 0.81e2 - 0.11e2 / 0.36e2 * t243 * t494 - 0.2e1 / 0.27e2 * t122 * t304 * jnp.pi * t268 * t271 * t217 * t137 * t301 - t235 * t144 * t32 * t242 * t506 / 0.36e2 + 0.2e1 / 0.9e1 * t531 / t239 / t51 * t465 * t469 * t538 + 0.2e1 / 0.9e1 * t531 * t240 * t244 * t544 * t538 - 0.4e1 / 0.81e2 * t553 * t240 * t465 * t469 * t538 - 0.8e1 / 0.81e2 * t553 * t280 * t244 * t544 * t538 - 0.4e1 / 0.81e2 * t553 * t129 * t246 * t538
  t569 = f.my_piecewise3(t65, t568, 0)
  t586 = t222 * t150
  t597 = -t174 * t569 / 0.3185049600e10 + t178 * t569 / 0.126340300800e12 - t119 * t569 / 0.18e2 + t154 * t569 / 0.240e3 - t158 * t569 / 0.4480e4 + t162 * t569 / 0.103680e6 - t166 * t569 / 0.2838528e7 + t170 * t569 / 0.89456640e8 - 0.2e1 / 0.3e1 * t154 * t586 + t71 * t150 * t310 / 0.2e1 + t158 * t586 / 0.8e1 - t74 * t150 * t310 / 0.16e2
  t630 = -t162 * t586 / 0.80e2 + 0.3e1 / 0.640e3 * t77 * t150 * t310 + t166 * t586 / 0.1152e4 - t80 * t150 * t310 / 0.3840e4 - t170 * t586 / 0.21504e5 + t83 * t150 * t310 / 0.86016e5 + t174 * t586 / 0.491520e6 - t86 * t150 * t310 / 0.2293760e7 - t178 * t586 / 0.13271040e8 + t89 * t150 * t310 / 0.70778880e8 + 0.1e1 / t88 / t118 * t586 / 0.412876800e9 - t338 * t150 * t310 / 0.2477260800e10
  t632 = f.my_piecewise3(t65, 0, t568)
  t639 = t352 * t182
  t644 = t101 * t344
  t647 = t349 ** 2
  t705 = f.my_piecewise3(t64, t597 + t630, -0.8e1 / 0.3e1 * t632 * t108 - 0.8e1 * t344 * t201 - 0.8e1 * t182 * t387 - 0.8e1 / 0.3e1 * t92 * (0.7e1 / 0.2e1 * t372 * t639 * t101 - 0.3e1 / 0.2e1 * t351 * t182 * t644 - 0.1e1 / t647 * t639 * t101 / 0.4e1 - 0.6e1 * t101 * t364 * t639 + 0.6e1 * t356 * t182 * t344 - t184 * t632 + 0.2e1 * t632 * t105 + 0.6e1 * t344 * t198 + 0.6e1 * t182 * t384 + 0.2e1 * t92 * (0.15e2 / 0.2e1 * t351 * t639 * t101 - 0.6e1 * t364 * t182 * t644 - 0.5e1 / 0.2e1 / t349 / t188 * t639 * t101 + t189 * t632 * t101 / 0.2e1 + 0.3e1 / 0.4e1 * t372 * t344 * t182 * t101 + 0.1e1 / t647 / t92 * t639 * t101 / 0.8e1 - 0.12e2 * t182 * t102 * t344 - 0.3e1 * t99 * t182 * t644 - 0.4e1 * t193 * t632 - t94 * t632 * t101)))
  t735 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t42 * t112 * t51 + t18 * t22 * t205 * t51 / 0.4e1 + 0.115e3 / 0.216e3 * t18 / t19 / t424 * t112 * t128 * t219 - 0.3e1 / 0.8e1 * t18 * t117 * t391 * t51 - 0.3e1 / 0.8e1 * t18 * t212 * t205 * t128 * t219 - 0.5e1 / 0.27e2 * t18 / t441 * t112 * t128 * t410 - 0.3e1 / 0.8e1 * t18 * t19 * t705 * t51 + t18 * t397 * t391 * t128 * t219 / 0.8e1 + t18 * t403 * t205 * t128 * t410 / 0.18e2 + 0.2e1 / 0.27e2 * t3 / t4 / t456 * t17 / t20 / t441 / t40 * t112 * t128 * t246 * t470 * t472)
  v3rho3_0_ = 0.2e1 * r0 * t735 + 0.6e1 * t414

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
  t25 = jnp.pi * t24
  t26 = 0.1e1 / jnp.pi
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = 0.1e1 / t27
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = t28 * t29
  t31 = 6 ** (0.1e1 / 0.3e1)
  t32 = params.mu * t31
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = 0.1e1 / t35
  t38 = 2 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t44 = params.kappa + t32 * t36 * s0 * t39 * t23 / 0.24e2
  t49 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t44)
  t52 = t25 * t30 / t49
  t53 = jnp.sqrt(t52)
  t55 = f.p.cam_omega / t53
  t56 = t11 * r0
  t57 = t56 ** (0.1e1 / 0.3e1)
  t58 = 0.1e1 / t57
  t61 = t55 * t38 * t58 / 0.2e1
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
  t116 = 0.1e1 / t21 / r0
  t117 = t65 * t64
  t118 = 0.1e1 / t117
  t121 = f.p.cam_omega / t53 / t52
  t122 = t121 * t58
  t123 = t25 * t30
  t124 = t122 * t123
  t125 = t49 ** 2
  t126 = 0.1e1 / t125
  t127 = params.kappa ** 2
  t128 = t126 * t127
  t129 = t44 ** 2
  t130 = 0.1e1 / t129
  t131 = t130 * params.mu
  t132 = t128 * t131
  t133 = t31 * t36
  t134 = t19 * r0
  t136 = 0.1e1 / t21 / t134
  t139 = t132 * t133 * s0 * t136
  t143 = 0.1e1 / t57 / t56
  t148 = -t124 * t139 / 0.18e2 - t55 * t38 * t143 * t11 / 0.6e1
  t149 = f.my_piecewise3(t63, t148, 0)
  t152 = t68 * t64
  t153 = 0.1e1 / t152
  t156 = t68 * t117
  t157 = 0.1e1 / t156
  t161 = 0.1e1 / t74 / t64
  t165 = 0.1e1 / t74 / t117
  t169 = 0.1e1 / t74 / t152
  t173 = 0.1e1 / t74 / t156
  t177 = 0.1e1 / t86 / t64
  t181 = f.my_piecewise3(t63, 0, t148)
  t183 = t99 * t97
  t187 = t96 * t90
  t188 = 0.1e1 / t187
  t192 = t90 * t100
  t197 = t188 * t181 * t99 / 0.2e1 - 0.4e1 * t192 * t181 - t92 * t181 * t99
  t200 = 0.2e1 * t181 * t103 - t183 * t181 + 0.2e1 * t90 * t197
  t204 = f.my_piecewise3(t62, -t118 * t149 / 0.18e2 + t153 * t149 / 0.240e3 - t157 * t149 / 0.4480e4 + t161 * t149 / 0.103680e6 - t165 * t149 / 0.2838528e7 + t169 * t149 / 0.89456640e8 - t173 * t149 / 0.3185049600e10 + t177 * t149 / 0.126340300800e12, -0.8e1 / 0.3e1 * t181 * t106 - 0.8e1 / 0.3e1 * t90 * t200)
  t209 = t19 ** 2
  t210 = t209 * r0
  t212 = 0.1e1 / t20 / t210
  t217 = t36 * s0
  t219 = t131 * t31 * t217 * t39
  t222 = 0.1e1 / t21
  t223 = t149 ** 2
  t227 = t27 ** 2
  t228 = 0.1e1 / t227
  t229 = t29 ** 2
  t230 = t228 * t229
  t236 = f.p.cam_omega / t53 / t33 / t3 / t230 / t126 / 0.3e1
  t240 = t125 ** 2
  t241 = 0.1e1 / t240
  t243 = t3 * t228 * t229 * t241
  t244 = t236 * t58 * t33 * t243
  t245 = t127 ** 2
  t246 = t129 ** 2
  t247 = 0.1e1 / t246
  t249 = params.mu ** 2
  t250 = t31 ** 2
  t251 = t249 * t250
  t252 = t245 * t247 * t251
  t255 = s0 ** 2
  t256 = 0.1e1 / t34 / t33 * t255
  t257 = t209 * t134
  t259 = 0.1e1 / t20 / t257
  t261 = t256 * t259 * t39
  t262 = t252 * t261
  t266 = t121 * t143 * jnp.pi
  t267 = t24 * t28
  t269 = t267 * t29 * t126
  t270 = t266 * t269
  t272 = t127 * t130 * t32
  t279 = t121 * t58 * jnp.pi
  t280 = t125 * t49
  t281 = 0.1e1 / t280
  t283 = t267 * t29 * t281
  t284 = t279 * t283
  t287 = t279 * t269
  t288 = t129 * t44
  t289 = 0.1e1 / t288
  t291 = t127 * t289 * t251
  t296 = 0.1e1 / t21 / t209
  t302 = t11 ** 2
  t305 = 0.1e1 / t57 / t302 / t19
  t310 = t244 * t262 / 0.36e2 + t270 * t272 * t217 * t136 * t11 / 0.27e2 - t284 * t262 / 0.81e2 - t287 * t291 * t261 / 0.81e2 + 0.11e2 / 0.54e2 * t124 * t132 * t133 * s0 * t296 + 0.2e1 / 0.9e1 * t55 * t38 * t305 * t302
  t311 = f.my_piecewise3(t63, t310, 0)
  t339 = 0.1e1 / t86 / t65
  t344 = t69 * t223 / 0.6e1 - t118 * t311 / 0.18e2 - t72 * t223 / 0.48e2 + t153 * t311 / 0.240e3 + t75 * t223 / 0.640e3 - t157 * t311 / 0.4480e4 - t78 * t223 / 0.11520e5 + t161 * t311 / 0.103680e6 + t81 * t223 / 0.258048e6 - t165 * t311 / 0.2838528e7 - t84 * t223 / 0.6881280e7 + t169 * t311 / 0.89456640e8 + t87 * t223 / 0.212336640e9 - t173 * t311 / 0.3185049600e10 - t339 * t223 / 0.7431782400e10 + t177 * t311 / 0.126340300800e12
  t345 = f.my_piecewise3(t63, 0, t310)
  t350 = t96 ** 2
  t352 = 0.1e1 / t350 / t90
  t353 = t181 ** 2
  t354 = t352 * t353
  t357 = t99 * t188
  t365 = 0.1e1 / t350
  t373 = 0.1e1 / t350 / t96
  t374 = t373 * t353
  t385 = -0.2e1 * t365 * t353 * t99 + t188 * t345 * t99 / 0.2e1 + t374 * t99 / 0.4e1 - 0.4e1 * t353 * t100 - t97 * t353 * t99 - 0.4e1 * t192 * t345 - t92 * t345 * t99
  t388 = -t354 * t99 / 0.2e1 + 0.2e1 * t357 * t353 - t183 * t345 + 0.2e1 * t345 * t103 + 0.4e1 * t181 * t197 + 0.2e1 * t90 * t385
  t392 = f.my_piecewise3(t62, t344, -0.8e1 / 0.3e1 * t345 * t106 - 0.16e2 / 0.3e1 * t181 * t200 - 0.8e1 / 0.3e1 * t90 * t388)
  t398 = 0.1e1 / t20 / t209
  t404 = t209 ** 2
  t405 = 0.1e1 / t404
  t412 = t289 * t249 * t250 * t256 * t38
  t415 = t302 * t11
  t418 = 0.1e1 / t57 / t415 / t134
  t423 = t33 ** 2
  t428 = f.p.cam_omega / t53 / t423 / t281 / 0.36e2
  t430 = 0.1e1 / t240 / t125
  t432 = t245 * t127
  t434 = t428 * t58 * t430 * t432
  t436 = 0.1e1 / t246 / t129
  t437 = t249 * params.mu
  t438 = t436 * t437
  t439 = t255 * s0
  t440 = t404 * t134
  t441 = 0.1e1 / t440
  t442 = t439 * t441
  t448 = 0.1e1 / t21 / t210
  t455 = 0.1e1 / t20 / t404
  t457 = t256 * t455 * t39
  t461 = t252 * t457
  t469 = t266 * t283
  t472 = t256 * t259 * t11 * t39
  t473 = t252 * t472
  t482 = t121 * t305 * jnp.pi
  t483 = t482 * t269
  t491 = t236 * t143 * t33 * t243
  t497 = 0.1e1 / t33 * t3 * t230
  t498 = t236 * t58 * t497
  t500 = 0.1e1 / t240 / t49
  t501 = t500 * t432
  t502 = t501 * t436
  t503 = t437 * t439
  t504 = t441 * t38
  t505 = t503 * t504
  t509 = t241 * t245
  t511 = 0.1e1 / t246 / t44
  t512 = t509 * t511
  t519 = 0.1e1 / t33 / jnp.pi * t24 * t30
  t520 = t122 * t519
  t521 = t241 * t432
  t522 = t521 * t436
  t526 = t281 * t245
  t527 = t526 * t511
  t531 = t128 * t247
  t535 = -0.14e2 / 0.27e2 * t55 * t38 * t418 * t415 - 0.10e2 / 0.9e1 * t434 * t438 * t442 * t38 - 0.77e2 / 0.81e2 * t124 * t132 * t133 * s0 * t448 + 0.11e2 / 0.81e2 * t287 * t291 * t457 + 0.11e2 / 0.81e2 * t284 * t461 - 0.11e2 / 0.54e2 * t270 * t272 * t217 * t296 * t11 + t469 * t473 / 0.81e2 + t270 * t291 * t472 / 0.81e2 - 0.11e2 / 0.36e2 * t244 * t461 - 0.2e1 / 0.27e2 * t483 * t272 * t217 * t136 * t302 - t491 * t473 / 0.36e2 + 0.2e1 / 0.9e1 * t498 * t502 * t505 + 0.2e1 / 0.9e1 * t498 * t512 * t505 - 0.4e1 / 0.81e2 * t520 * t522 * t505 - 0.8e1 / 0.81e2 * t520 * t527 * t505 - 0.4e1 / 0.81e2 * t520 * t531 * t505
  t536 = f.my_piecewise3(t63, t535, 0)
  t553 = t223 * t149
  t564 = -t118 * t536 / 0.18e2 + t153 * t536 / 0.240e3 - t157 * t536 / 0.4480e4 + t161 * t536 / 0.103680e6 - t165 * t536 / 0.2838528e7 + t169 * t536 / 0.89456640e8 - t173 * t536 / 0.3185049600e10 + t177 * t536 / 0.126340300800e12 - 0.2e1 / 0.3e1 * t153 * t553 + t69 * t149 * t311 / 0.2e1 + t157 * t553 / 0.8e1 - t72 * t149 * t311 / 0.16e2
  t591 = 0.1e1 / t86 / t117
  t597 = -t161 * t553 / 0.80e2 + 0.3e1 / 0.640e3 * t75 * t149 * t311 + t165 * t553 / 0.1152e4 - t78 * t149 * t311 / 0.3840e4 - t169 * t553 / 0.21504e5 + t81 * t149 * t311 / 0.86016e5 + t173 * t553 / 0.491520e6 - t84 * t149 * t311 / 0.2293760e7 - t177 * t553 / 0.13271040e8 + t87 * t149 * t311 / 0.70778880e8 + t591 * t553 / 0.412876800e9 - t339 * t149 * t311 / 0.2477260800e10
  t599 = f.my_piecewise3(t63, 0, t535)
  t606 = t353 * t181
  t610 = t352 * t181
  t611 = t99 * t345
  t614 = t350 ** 2
  t615 = 0.1e1 / t614
  t619 = t99 * t365
  t635 = t365 * t181
  t639 = 0.1e1 / t350 / t187
  t647 = t181 * t99
  t651 = 0.1e1 / t614 / t90
  t655 = t181 * t100
  t658 = t97 * t181
  t665 = 0.15e2 / 0.2e1 * t352 * t606 * t99 - 0.6e1 * t635 * t611 - 0.5e1 / 0.2e1 * t639 * t606 * t99 + t188 * t599 * t99 / 0.2e1 + 0.3e1 / 0.4e1 * t373 * t345 * t647 + t651 * t606 * t99 / 0.8e1 - 0.12e2 * t655 * t345 - 0.3e1 * t658 * t611 - 0.4e1 * t192 * t599 - t92 * t599 * t99
  t668 = 0.7e1 / 0.2e1 * t373 * t606 * t99 - 0.3e1 / 0.2e1 * t610 * t611 - t615 * t606 * t99 / 0.4e1 - 0.6e1 * t619 * t606 + 0.6e1 * t357 * t181 * t345 - t183 * t599 + 0.2e1 * t599 * t103 + 0.6e1 * t345 * t197 + 0.6e1 * t181 * t385 + 0.2e1 * t90 * t665
  t672 = f.my_piecewise3(t62, t564 + t597, -0.8e1 / 0.3e1 * t599 * t106 - 0.8e1 * t345 * t200 - 0.8e1 * t181 * t388 - 0.8e1 / 0.3e1 * t90 * t668)
  t678 = 0.1e1 / t20 / t134
  t684 = 0.1e1 / t257
  t692 = t3 / t4 / t423
  t697 = t692 * t17 / t21 / t404 / t19
  t699 = t247 * t437
  t700 = t699 * t439
  t701 = t110 * t127 * t700
  t705 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t23 * t110 * t49 + t18 * t116 * t204 * t49 / 0.4e1 + 0.115e3 / 0.216e3 * t18 * t212 * t110 * t127 * t219 - 0.3e1 / 0.8e1 * t18 * t222 * t392 * t49 - 0.3e1 / 0.8e1 * t18 * t398 * t204 * t127 * t219 - 0.5e1 / 0.27e2 * t18 * t405 * t110 * t127 * t412 - 0.3e1 / 0.8e1 * t18 * t20 * t672 * t49 + t18 * t678 * t392 * t127 * t219 / 0.8e1 + t18 * t684 * t204 * t127 * t412 / 0.18e2 + 0.2e1 / 0.27e2 * t697 * t701)
  t733 = t311 ** 2
  t738 = t223 ** 2
  t750 = 0.1e1 / t404 / t209
  t758 = t256 * t259 * t302 * t39
  t763 = t252 * t758
  t773 = t256 * t455 * t11 * t39
  t774 = t252 * t773
  t783 = t121 * t143 * t519
  t784 = t511 * t437
  t787 = t442 * t11 * t38
  t793 = t249 ** 2
  t794 = 0.1e1 / t246 / t288 * t793
  t796 = t255 ** 2
  t797 = t209 * t19
  t798 = t404 * t797
  t800 = 0.1e1 / t21 / t798
  t801 = t796 * t800
  t802 = t801 * t133
  t806 = t436 * t793
  t811 = t245 ** 2
  t813 = t246 ** 2
  t815 = 0.1e1 / t813 * t793
  t827 = t511 * t793
  t842 = t236 * t143 * t497
  t855 = 0.220e3 / 0.9e1 * t434 * t438 * t439 * t750 * t38 - 0.8e1 / 0.243e3 * t483 * t291 * t758 - 0.8e1 / 0.243e3 * t482 * t283 * t763 + 0.2e1 / 0.27e2 * t236 * t305 * t33 * t243 * t763 + 0.11e2 / 0.27e2 * t491 * t774 - 0.44e2 / 0.243e3 * t270 * t291 * t773 - 0.44e2 / 0.243e3 * t469 * t774 + 0.32e2 / 0.243e3 * t783 * t526 * t784 * t787 + 0.16e2 / 0.27e2 * t498 * t501 * t794 * t802 - 0.32e2 / 0.243e3 * t520 * t526 * t806 * t802 + 0.8e1 / 0.27e2 * t498 * t430 * t811 * t815 * t802 + 0.1309e4 / 0.243e3 * t124 * t132 * t133 * s0 / t21 / t797 - 0.32e2 / 0.729e3 * t520 * t128 * t827 * t802 - 0.32e2 / 0.729e3 * t520 * t500 * t811 * t815 * t802 - 0.32e2 / 0.243e3 * t520 * t521 * t794 * t802 - 0.8e1 / 0.27e2 * t842 * t509 * t784 * t787 + 0.16e2 / 0.243e3 * t783 * t128 * t699 * t787 + 0.8e1 / 0.27e2 * t498 * t509 * t806 * t802
  t867 = t240 ** 2
  t885 = t404 * r0
  t889 = t256 / t20 / t885 * t39
  t908 = t252 * t889
  t913 = t302 ** 2
  t922 = t503 * t750 * t38
  t953 = t800 * t31 * t36
  t961 = 0.35e2 / 0.1458e4 * f.p.cam_omega / t53 / t423 / t24 * t27 * t26 / t29 / t241 * t58 / t867 * t811 * t815 * t801 * t25 * t30 * t133 - 0.8e1 / 0.27e2 * t842 * t501 * t438 * t787 + 0.16e2 / 0.243e3 * t783 * t521 * t438 * t787 - 0.979e3 / 0.729e3 * t287 * t291 * t889 + 0.308e3 / 0.243e3 * t270 * t272 * t217 * t448 * t11 + 0.44e2 / 0.81e2 * t483 * t272 * t217 * t296 * t302 + 0.56e2 / 0.243e3 * t121 * t418 * t415 * t123 * t139 + 0.979e3 / 0.324e3 * t244 * t908 - 0.979e3 / 0.729e3 * t284 * t908 + 0.140e3 / 0.81e2 * t55 * t38 / t57 / t209 + 0.176e3 / 0.81e2 * t520 * t527 * t922 + 0.88e2 / 0.81e2 * t520 * t531 * t922 - 0.44e2 / 0.9e1 * t498 * t502 * t922 + 0.88e2 / 0.81e2 * t520 * t522 * t922 - 0.44e2 / 0.9e1 * t498 * t512 * t922 + 0.40e2 / 0.27e2 * t428 * t143 * t430 * t432 * t438 * t439 * t504 * t11 - 0.80e2 / 0.27e2 * t428 * t58 / t240 / t280 * t811 * t815 * t796 * t953 - 0.80e2 / 0.27e2 * t434 * t794 * t796 * t953
  t962 = t855 + t961
  t963 = f.my_piecewise3(t63, t962, 0)
  t992 = -t78 * t733 / 0.3840e4 + t81 * t733 / 0.86016e5 + 0.13e2 / 0.21504e5 * t84 * t738 + 0.10e2 / 0.3e1 * t72 * t738 + t69 * t733 / 0.2e1 - 0.19e2 / 0.412876800e9 / t86 / t68 * t738 + t161 * t963 / 0.103680e6 - 0.7e1 / 0.8e1 * t75 * t738 + 0.9e1 / 0.80e2 * t78 * t738 - t72 * t733 / 0.16e2 + t169 * t963 / 0.89456640e8 - t157 * t963 / 0.4480e4 - 0.11e2 / 0.1152e4 * t81 * t738 + t177 * t963 / 0.126340300800e12 - t118 * t963 / 0.18e2 - t165 * t963 / 0.2838528e7 + t87 * t733 / 0.70778880e8 - t87 * t738 / 0.32768e5 - t339 * t733 / 0.2477260800e10 + 0.3e1 / 0.640e3 * t75 * t733
  t1049 = -t173 * t963 / 0.3185049600e10 - t84 * t733 / 0.2293760e7 + 0.17e2 / 0.13271040e8 * t339 * t738 + t153 * t963 / 0.240e3 + 0.2e1 / 0.3e1 * t69 * t536 * t149 - t72 * t536 * t149 / 0.12e2 + t75 * t536 * t149 / 0.160e3 - t78 * t536 * t149 / 0.2880e4 + t81 * t536 * t149 / 0.64512e5 - t84 * t536 * t149 / 0.1720320e7 + t87 * t536 * t149 / 0.53084160e8 - t339 * t536 * t149 / 0.1857945600e10 - 0.4e1 * t153 * t223 * t311 + 0.3e1 / 0.4e1 * t157 * t223 * t311 - 0.3e1 / 0.40e2 * t161 * t223 * t311 + t165 * t223 * t311 / 0.192e3 - t169 * t223 * t311 / 0.3584e4 + t173 * t223 * t311 / 0.81920e5 - t177 * t223 * t311 / 0.2211840e7 + t591 * t223 * t311 / 0.68812800e8
  t1051 = f.my_piecewise3(t63, 0, t962)
  t1060 = t353 ** 2
  t1066 = t345 ** 2
  t1070 = t99 * t599
  t1155 = -0.75e2 / 0.2e1 * t373 * t1060 * t99 + 0.45e2 * t354 * t611 - 0.6e1 * t365 * t1066 * t99 - 0.8e1 * t635 * t1070 - 0.15e2 * t639 * t353 * t611 + t373 * t599 * t647 + 0.3e1 / 0.4e1 * t373 * t1066 * t99 + 0.3e1 / 0.4e1 * t651 * t345 * t353 * t99 - 0.3e1 * t97 * t1066 * t99 - 0.4e1 * t658 * t1070 + 0.85e2 / 0.4e1 * t615 * t1060 * t99 - 0.19e2 / 0.8e1 / t614 / t96 * t1060 * t99 + t188 * t1051 * t99 / 0.2e1 + 0.1e1 / t614 / t350 * t1060 * t99 / 0.16e2 - 0.12e2 * t1066 * t100 - 0.16e2 * t655 * t599 - 0.4e1 * t192 * t1051 - t92 * t1051 * t99
  t1158 = -0.24e2 * t639 * t1060 * t99 + 0.21e2 * t374 * t611 - 0.3e1 / 0.2e1 * t352 * t1066 * t99 - 0.2e1 * t610 * t1070 - 0.3e1 / 0.2e1 * t615 * t353 * t611 + 0.24e2 * t99 * t352 * t1060 - 0.36e2 * t619 * t353 * t345 + 0.6e1 * t357 * t1066 + 0.8e1 * t357 * t181 * t599 + 0.2e1 * t1051 * t103 + 0.8e1 * t599 * t197 + 0.15e2 / 0.4e1 * t651 * t1060 * t99 - 0.1e1 / t614 / t187 * t1060 * t99 / 0.8e1 - t183 * t1051 + 0.12e2 * t345 * t385 + 0.8e1 * t181 * t665 + 0.2e1 * t90 * t1155
  t1162 = f.my_piecewise3(t62, t992 + t1049, -0.8e1 / 0.3e1 * t1051 * t106 - 0.32e2 / 0.3e1 * t599 * t200 - 0.16e2 * t345 * t388 - 0.32e2 / 0.3e1 * t181 * t668 - 0.8e1 / 0.3e1 * t90 * t1158)
  t1216 = 0.10e2 / 0.27e2 * t18 * t136 * t110 * t49 - 0.5e1 / 0.9e1 * t18 * t23 * t204 * t49 + t18 * t116 * t392 * t49 / 0.2e1 - t18 * t222 * t672 * t49 / 0.2e1 - 0.124e3 / 0.81e2 * t692 * t17 / t21 / t440 * t701 + 0.8e1 / 0.27e2 * t697 * t204 * t127 * t700 - 0.3e1 / 0.8e1 * t18 * t20 * t1162 * t49 - 0.305e3 / 0.108e3 * t18 / t20 / t797 * t110 * t127 * t219 + 0.115e3 / 0.54e2 * t18 * t212 * t204 * t127 * t219 + 0.835e3 / 0.486e3 * t18 / t885 * t110 * t127 * t412 - 0.3e1 / 0.4e1 * t18 * t398 * t392 * t127 * t219 - 0.20e2 / 0.27e2 * t18 * t405 * t204 * t127 * t412 + t18 * t678 * t672 * t127 * t219 / 0.6e1 + t18 * t684 * t392 * t127 * t412 / 0.9e1 + 0.8e1 / 0.243e3 * t692 * t17 / t20 / t798 * t110 * t127 * t827 * t796 * t133 * t39
  t1217 = f.my_piecewise3(t2, 0, t1216)
  v4rho4_0_ = 0.2e1 * r0 * t1217 + 0.8e1 * t705

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
  t51 = 6 ** (0.1e1 / 0.3e1)
  t52 = params.mu * t51
  t53 = jnp.pi ** 2
  t54 = t53 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t56 = 0.1e1 / t55
  t57 = t56 * s0
  t58 = r0 ** 2
  t59 = r0 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t66 = params.kappa + t52 * t57 / t60 / t58 / 0.24e2
  t71 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t66)
  t74 = t45 * t50 / t71
  t75 = jnp.sqrt(t74)
  t77 = f.p.cam_omega / t75
  t78 = 2 ** (0.1e1 / 0.3e1)
  t79 = t19 * t6
  t80 = t79 ** (0.1e1 / 0.3e1)
  t81 = 0.1e1 / t80
  t82 = t78 * t81
  t84 = t77 * t82 / 0.2e1
  t85 = 0.135e1 <= t84
  t86 = 0.135e1 < t84
  t87 = f.my_piecewise3(t86, t84, 0.135e1)
  t88 = t87 ** 2
  t91 = t88 ** 2
  t92 = 0.1e1 / t91
  t94 = t91 * t88
  t95 = 0.1e1 / t94
  t97 = t91 ** 2
  t98 = 0.1e1 / t97
  t101 = 0.1e1 / t97 / t88
  t104 = 0.1e1 / t97 / t91
  t107 = 0.1e1 / t97 / t94
  t109 = t97 ** 2
  t110 = 0.1e1 / t109
  t113 = f.my_piecewise3(t86, 0.135e1, t84)
  t114 = jnp.sqrt(jnp.pi)
  t115 = 0.1e1 / t113
  t117 = jnp.erf(t115 / 0.2e1)
  t119 = t113 ** 2
  t120 = 0.1e1 / t119
  t122 = jnp.exp(-t120 / 0.4e1)
  t123 = t122 - 0.1e1
  t126 = t122 - 0.3e1 / 0.2e1 - 0.2e1 * t119 * t123
  t129 = 0.2e1 * t113 * t126 + t114 * t117
  t133 = f.my_piecewise3(t85, 0.1e1 / t88 / 0.36e2 - t92 / 0.960e3 + t95 / 0.26880e5 - t98 / 0.829440e6 + t101 / 0.28385280e8 - t104 / 0.1073479680e10 + t107 / 0.44590694400e11 - t110 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t113 * t129)
  t134 = t43 * t133
  t135 = t134 * t71
  t140 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t141 = t5 * t140
  t142 = t43 ** 2
  t143 = 0.1e1 / t142
  t144 = t143 * t133
  t145 = t144 * t71
  t148 = t88 * t87
  t149 = 0.1e1 / t148
  t152 = f.p.cam_omega / t75 / t74
  t154 = t45 * t50
  t155 = t152 * t82 * t154
  t156 = t71 ** 2
  t157 = 0.1e1 / t156
  t158 = params.kappa ** 2
  t159 = t157 * t158
  t160 = t66 ** 2
  t162 = 0.1e1 / t160 * params.mu
  t163 = t159 * t162
  t164 = t51 * t56
  t165 = t58 * r0
  t167 = 0.1e1 / t60 / t165
  t168 = s0 * t167
  t175 = t78 / t80 / t79
  t177 = t28 * t6 + t18 + 0.1e1
  t181 = -t155 * t163 * t164 * t168 / 0.36e2 - t77 * t175 * t177 / 0.6e1
  t182 = f.my_piecewise3(t86, t181, 0)
  t185 = t91 * t87
  t186 = 0.1e1 / t185
  t189 = t91 * t148
  t190 = 0.1e1 / t189
  t194 = 0.1e1 / t97 / t87
  t198 = 0.1e1 / t97 / t148
  t202 = 0.1e1 / t97 / t185
  t206 = 0.1e1 / t97 / t189
  t210 = 0.1e1 / t109 / t87
  t214 = f.my_piecewise3(t86, 0, t181)
  t216 = t122 * t120
  t220 = t119 * t113
  t221 = 0.1e1 / t220
  t225 = t113 * t123
  t230 = t221 * t214 * t122 / 0.2e1 - 0.4e1 * t225 * t214 - t115 * t214 * t122
  t233 = 0.2e1 * t113 * t230 + 0.2e1 * t214 * t126 - t216 * t214
  t237 = f.my_piecewise3(t85, -t149 * t182 / 0.18e2 + t186 * t182 / 0.240e3 - t190 * t182 / 0.4480e4 + t194 * t182 / 0.103680e6 - t198 * t182 / 0.2838528e7 + t202 * t182 / 0.89456640e8 - t206 * t182 / 0.3185049600e10 + t210 * t182 / 0.126340300800e12, -0.8e1 / 0.3e1 * t113 * t233 - 0.8e1 / 0.3e1 * t214 * t129)
  t238 = t43 * t237
  t239 = t238 * t71
  t242 = t134 * t158
  t243 = t141 * t242
  t244 = t162 * t51
  t246 = t244 * t57 * t167
  t249 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t250 = t249 * f.p.zeta_threshold
  t252 = f.my_piecewise3(t20, t250, t21 * t19)
  t253 = t5 * t252
  t255 = 0.1e1 / t142 / t6
  t256 = t255 * t133
  t257 = t256 * t71
  t260 = t143 * t237
  t261 = t260 * t71
  t264 = t144 * t158
  t265 = t253 * t264
  t268 = t182 ** 2
  t271 = t53 * t2
  t272 = t47 ** 2
  t273 = 0.1e1 / t272
  t274 = t49 ** 2
  t275 = t273 * t274
  t281 = f.p.cam_omega / t75 / t271 / t275 / t157 / 0.3e1
  t283 = t271 * t275
  t284 = t281 * t82 * t283
  t285 = t156 ** 2
  t286 = 0.1e1 / t285
  t287 = t158 ** 2
  t289 = t160 ** 2
  t290 = 0.1e1 / t289
  t291 = params.mu ** 2
  t292 = t290 * t291
  t293 = t286 * t287 * t292
  t294 = t51 ** 2
  t296 = 0.1e1 / t54 / t53
  t297 = t294 * t296
  t298 = s0 ** 2
  t299 = t58 ** 2
  t302 = 0.1e1 / t59 / t299 / t165
  t303 = t298 * t302
  t304 = t297 * t303
  t309 = t152 * t175 * t154
  t316 = 0.1e1 / t156 / t71
  t318 = t316 * t287 * t292
  t324 = 0.1e1 / t160 / t66 * t291
  t325 = t159 * t324
  t330 = 0.1e1 / t60 / t299
  t331 = s0 * t330
  t336 = t19 ** 2
  t339 = 0.1e1 / t80 / t336 / t24
  t340 = t78 * t339
  t341 = t177 ** 2
  t347 = t37 * t6 + 0.2e1 * t28
  t351 = t284 * t293 * t304 / 0.72e2 + t309 * t163 * t164 * t168 * t177 / 0.54e2 - t155 * t318 * t304 / 0.162e3 - t155 * t325 * t304 / 0.162e3 + 0.11e2 / 0.108e3 * t155 * t163 * t164 * t331 + 0.2e1 / 0.9e1 * t77 * t340 * t341 - t77 * t175 * t347 / 0.6e1
  t352 = f.my_piecewise3(t86, t351, 0)
  t380 = 0.1e1 / t109 / t88
  t385 = t92 * t268 / 0.6e1 - t149 * t352 / 0.18e2 - t95 * t268 / 0.48e2 + t186 * t352 / 0.240e3 + t98 * t268 / 0.640e3 - t190 * t352 / 0.4480e4 - t101 * t268 / 0.11520e5 + t194 * t352 / 0.103680e6 + t104 * t268 / 0.258048e6 - t198 * t352 / 0.2838528e7 - t107 * t268 / 0.6881280e7 + t202 * t352 / 0.89456640e8 + t110 * t268 / 0.212336640e9 - t206 * t352 / 0.3185049600e10 - t380 * t268 / 0.7431782400e10 + t210 * t352 / 0.126340300800e12
  t386 = f.my_piecewise3(t86, 0, t351)
  t391 = t119 ** 2
  t393 = 0.1e1 / t391 / t113
  t394 = t214 ** 2
  t398 = t122 * t221
  t406 = 0.1e1 / t391
  t414 = 0.1e1 / t391 / t119
  t426 = -0.2e1 * t406 * t394 * t122 + t221 * t386 * t122 / 0.2e1 + t414 * t394 * t122 / 0.4e1 - 0.4e1 * t394 * t123 - t120 * t394 * t122 - 0.4e1 * t225 * t386 - t115 * t386 * t122
  t429 = -t393 * t394 * t122 / 0.2e1 + 0.2e1 * t398 * t394 - t216 * t386 + 0.2e1 * t386 * t126 + 0.4e1 * t214 * t230 + 0.2e1 * t113 * t426
  t433 = f.my_piecewise3(t85, t385, -0.8e1 / 0.3e1 * t386 * t129 - 0.16e2 / 0.3e1 * t214 * t233 - 0.8e1 / 0.3e1 * t113 * t429)
  t434 = t43 * t433
  t435 = t434 * t71
  t438 = t238 * t158
  t439 = t253 * t438
  t442 = t253 * t242
  t443 = t324 * t294
  t444 = t296 * t298
  t446 = t443 * t444 * t302
  t450 = t244 * t57 * t330
  t453 = -0.3e1 / 0.8e1 * t42 * t135 - t141 * t145 / 0.4e1 - 0.3e1 / 0.4e1 * t141 * t239 + t243 * t246 / 0.12e2 + t253 * t257 / 0.12e2 - t253 * t261 / 0.4e1 + t265 * t246 / 0.36e2 - 0.3e1 / 0.8e1 * t253 * t435 + t439 * t246 / 0.12e2 + t442 * t446 / 0.108e3 - 0.11e2 / 0.72e2 * t442 * t450
  t454 = f.my_piecewise3(t1, 0, t453)
  t456 = r1 <= f.p.dens_threshold
  t457 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t458 = 0.1e1 + t457
  t459 = t458 <= f.p.zeta_threshold
  t460 = t458 ** (0.1e1 / 0.3e1)
  t461 = t460 ** 2
  t462 = 0.1e1 / t461
  t464 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t465 = t464 ** 2
  t469 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t473 = f.my_piecewise3(t459, 0, 0.4e1 / 0.9e1 * t462 * t465 + 0.4e1 / 0.3e1 * t460 * t469)
  t474 = t5 * t473
  t476 = r1 ** 2
  t477 = r1 ** (0.1e1 / 0.3e1)
  t478 = t477 ** 2
  t489 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + t52 * t56 * s2 / t478 / t476 / 0.24e2))
  t493 = jnp.sqrt(t45 * t50 / t489)
  t495 = f.p.cam_omega / t493
  t496 = t458 * t6
  t497 = t496 ** (0.1e1 / 0.3e1)
  t501 = t495 * t78 / t497 / 0.2e1
  t502 = 0.135e1 <= t501
  t503 = 0.135e1 < t501
  t504 = f.my_piecewise3(t503, t501, 0.135e1)
  t505 = t504 ** 2
  t508 = t505 ** 2
  t509 = 0.1e1 / t508
  t511 = t508 * t505
  t512 = 0.1e1 / t511
  t514 = t508 ** 2
  t515 = 0.1e1 / t514
  t518 = 0.1e1 / t514 / t505
  t521 = 0.1e1 / t514 / t508
  t524 = 0.1e1 / t514 / t511
  t526 = t514 ** 2
  t527 = 0.1e1 / t526
  t530 = f.my_piecewise3(t503, 0.135e1, t501)
  t531 = 0.1e1 / t530
  t533 = jnp.erf(t531 / 0.2e1)
  t535 = t530 ** 2
  t536 = 0.1e1 / t535
  t538 = jnp.exp(-t536 / 0.4e1)
  t539 = t538 - 0.1e1
  t542 = t538 - 0.3e1 / 0.2e1 - 0.2e1 * t535 * t539
  t545 = t114 * t533 + 0.2e1 * t530 * t542
  t549 = f.my_piecewise3(t502, 0.1e1 / t505 / 0.36e2 - t509 / 0.960e3 + t512 / 0.26880e5 - t515 / 0.829440e6 + t518 / 0.28385280e8 - t521 / 0.1073479680e10 + t524 / 0.44590694400e11 - t527 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t530 * t545)
  t551 = t43 * t549 * t489
  t556 = f.my_piecewise3(t459, 0, 0.4e1 / 0.3e1 * t460 * t464)
  t557 = t5 * t556
  t559 = t143 * t549 * t489
  t562 = t505 * t504
  t563 = 0.1e1 / t562
  t566 = t78 / t497 / t496
  t568 = t464 * t6 + t457 + 0.1e1
  t571 = t495 * t566 * t568 / 0.6e1
  t572 = f.my_piecewise3(t503, -t571, 0)
  t575 = t508 * t504
  t576 = 0.1e1 / t575
  t579 = t508 * t562
  t580 = 0.1e1 / t579
  t584 = 0.1e1 / t514 / t504
  t588 = 0.1e1 / t514 / t562
  t592 = 0.1e1 / t514 / t575
  t596 = 0.1e1 / t514 / t579
  t600 = 0.1e1 / t526 / t504
  t604 = f.my_piecewise3(t503, 0, -t571)
  t606 = t538 * t536
  t610 = t535 * t530
  t611 = 0.1e1 / t610
  t615 = t530 * t539
  t620 = t611 * t604 * t538 / 0.2e1 - 0.4e1 * t615 * t604 - t531 * t604 * t538
  t623 = 0.2e1 * t530 * t620 + 0.2e1 * t604 * t542 - t606 * t604
  t627 = f.my_piecewise3(t502, -t563 * t572 / 0.18e2 + t576 * t572 / 0.240e3 - t580 * t572 / 0.4480e4 + t584 * t572 / 0.103680e6 - t588 * t572 / 0.2838528e7 + t592 * t572 / 0.89456640e8 - t596 * t572 / 0.3185049600e10 + t600 * t572 / 0.126340300800e12, -0.8e1 / 0.3e1 * t530 * t623 - 0.8e1 / 0.3e1 * t604 * t545)
  t629 = t43 * t627 * t489
  t633 = f.my_piecewise3(t459, t250, t460 * t458)
  t634 = t5 * t633
  t636 = t255 * t549 * t489
  t640 = t143 * t627 * t489
  t643 = t572 ** 2
  t646 = t458 ** 2
  t649 = 0.1e1 / t497 / t646 / t24
  t651 = t568 ** 2
  t657 = t469 * t6 + 0.2e1 * t464
  t661 = 0.2e1 / 0.9e1 * t495 * t78 * t649 * t651 - t495 * t566 * t657 / 0.6e1
  t662 = f.my_piecewise3(t503, t661, 0)
  t690 = 0.1e1 / t526 / t505
  t695 = t509 * t643 / 0.6e1 - t563 * t662 / 0.18e2 - t512 * t643 / 0.48e2 + t576 * t662 / 0.240e3 + t515 * t643 / 0.640e3 - t580 * t662 / 0.4480e4 - t518 * t643 / 0.11520e5 + t584 * t662 / 0.103680e6 + t521 * t643 / 0.258048e6 - t588 * t662 / 0.2838528e7 - t524 * t643 / 0.6881280e7 + t592 * t662 / 0.89456640e8 + t527 * t643 / 0.212336640e9 - t596 * t662 / 0.3185049600e10 - t690 * t643 / 0.7431782400e10 + t600 * t662 / 0.126340300800e12
  t696 = f.my_piecewise3(t503, 0, t661)
  t701 = t535 ** 2
  t703 = 0.1e1 / t701 / t530
  t704 = t604 ** 2
  t708 = t538 * t611
  t716 = 0.1e1 / t701
  t724 = 0.1e1 / t701 / t535
  t736 = -0.2e1 * t716 * t704 * t538 + t611 * t696 * t538 / 0.2e1 + t724 * t704 * t538 / 0.4e1 - 0.4e1 * t704 * t539 - t536 * t704 * t538 - 0.4e1 * t615 * t696 - t531 * t696 * t538
  t739 = -t703 * t704 * t538 / 0.2e1 + 0.2e1 * t708 * t704 - t606 * t696 + 0.2e1 * t696 * t542 + 0.4e1 * t604 * t620 + 0.2e1 * t530 * t736
  t743 = f.my_piecewise3(t502, t695, -0.8e1 / 0.3e1 * t696 * t545 - 0.16e2 / 0.3e1 * t604 * t623 - 0.8e1 / 0.3e1 * t530 * t739)
  t745 = t43 * t743 * t489
  t749 = f.my_piecewise3(t456, 0, -0.3e1 / 0.8e1 * t474 * t551 - t557 * t559 / 0.4e1 - 0.3e1 / 0.4e1 * t557 * t629 + t634 * t636 / 0.12e2 - t634 * t640 / 0.4e1 - 0.3e1 / 0.8e1 * t634 * t745)
  t778 = t299 ** 2
  t780 = 0.1e1 / t59 / t778
  t787 = 0.1e1 / t60 / t299 / r0
  t794 = t439 * t446 / 0.36e2 + t141 * t264 * t246 / 0.12e2 + t141 * t438 * t246 / 0.4e1 + t243 * t446 / 0.36e2 - t253 * t256 * t158 * t246 / 0.36e2 + t253 * t260 * t158 * t246 / 0.12e2 + t265 * t446 / 0.108e3 + t253 * t434 * t158 * t246 / 0.8e1 + t42 * t242 * t246 / 0.8e1 - 0.11e2 / 0.108e3 * t442 * t443 * t444 * t780 + 0.77e2 / 0.108e3 * t442 * t244 * t57 * t787 - 0.11e2 / 0.72e2 * t265 * t450
  t799 = t53 ** 2
  t807 = t291 * params.mu
  t808 = t298 * s0
  t811 = 0.1e1 / t778 / t165
  t812 = t807 * t808 * t811
  t816 = t268 * t182
  t847 = -0.2e1 / 0.3e1 * t186 * t816 + t92 * t182 * t352 / 0.2e1 + t190 * t816 / 0.8e1 - t95 * t182 * t352 / 0.16e2 - t194 * t816 / 0.80e2 + 0.3e1 / 0.640e3 * t98 * t182 * t352 + t198 * t816 / 0.1152e4 - t101 * t182 * t352 / 0.3840e4 - t202 * t816 / 0.21504e5 + t104 * t182 * t352 / 0.86016e5 + t206 * t816 / 0.491520e6 - t107 * t182 * t352 / 0.2293760e7
  t866 = t297 * t298 * t780
  t882 = t297 * t303 * t177
  t894 = t24 ** 2
  t898 = 0.6e1 * t33 - 0.6e1 * t16 / t894
  t899 = f.my_piecewise5(t10, 0, t14, 0, t898)
  t941 = t287 * t158
  t943 = 0.1e1 / t289 / t160
  t953 = t281 * t78 * t81 / t53 * t2 * t273
  t959 = t808 * t811
  t960 = t943 * t807 * t959
  t969 = 0.1e1 / t289 / t66 * t807 * t959
  t979 = t152 * t78 * t81 / t53 / jnp.pi * t44 * t48
  t997 = -0.77e2 / 0.162e3 * t155 * t163 * t164 * s0 * t787 + 0.11e2 / 0.162e3 * t155 * t325 * t866 + 0.11e2 / 0.162e3 * t155 * t318 * t866 - 0.11e2 / 0.72e2 * t284 * t293 * t866 + t309 * t163 * t164 * t168 * t347 / 0.36e2 + t309 * t318 * t882 / 0.162e3 + t309 * t325 * t882 / 0.162e3 - t281 * t175 * t283 * t293 * t882 / 0.72e2 - t77 * t175 * (t899 * t6 + 0.3e1 * t37) / 0.6e1 - 0.14e2 / 0.27e2 * t77 * t78 / t80 / t336 / t19 / t32 * t341 * t177 + 0.2e1 / 0.3e1 * t77 * t78 * t339 * t177 * t347 - 0.11e2 / 0.108e3 * t309 * t163 * t164 * t331 * t177 - t152 * t340 * t154 * t163 * t164 * t168 * t341 / 0.27e2 - 0.5e1 / 0.648e3 * f.p.cam_omega / t75 / t799 / t316 * t82 / t285 / t156 * t941 * t943 * t812 + t953 * t274 / t285 / t71 * t941 * t960 / 0.18e2 + t953 * t274 * t286 * t287 * t969 / 0.18e2 - t979 * t49 * t286 * t941 * t960 / 0.81e2 - 0.2e1 / 0.81e2 * t979 * t49 * t316 * t287 * t969 - t979 * t49 * t157 * t158 * t290 * t807 * t959 / 0.81e2
  t998 = f.my_piecewise3(t86, t997, 0)
  t1015 = -t210 * t816 / 0.13271040e8 + t110 * t182 * t352 / 0.70778880e8 + 0.1e1 / t109 / t148 * t816 / 0.412876800e9 - t380 * t182 * t352 / 0.2477260800e10 - t149 * t998 / 0.18e2 + t186 * t998 / 0.240e3 - t190 * t998 / 0.4480e4 + t194 * t998 / 0.103680e6 - t198 * t998 / 0.2838528e7 + t202 * t998 / 0.89456640e8 - t206 * t998 / 0.3185049600e10 + t210 * t998 / 0.126340300800e12
  t1017 = f.my_piecewise3(t86, 0, t997)
  t1024 = t394 * t214
  t1029 = t122 * t386
  t1032 = t391 ** 2
  t1090 = f.my_piecewise3(t85, t847 + t1015, -0.8e1 / 0.3e1 * t1017 * t129 - 0.8e1 * t386 * t233 - 0.8e1 * t214 * t429 - 0.8e1 / 0.3e1 * t113 * (0.7e1 / 0.2e1 * t414 * t1024 * t122 - 0.3e1 / 0.2e1 * t393 * t214 * t1029 - 0.1e1 / t1032 * t1024 * t122 / 0.4e1 - 0.6e1 * t122 * t406 * t1024 + 0.6e1 * t398 * t214 * t386 - t216 * t1017 + 0.2e1 * t1017 * t126 + 0.6e1 * t386 * t230 + 0.6e1 * t214 * t426 + 0.2e1 * t113 * (0.15e2 / 0.2e1 * t393 * t1024 * t122 - 0.6e1 * t406 * t214 * t1029 - 0.5e1 / 0.2e1 / t391 / t220 * t1024 * t122 + t221 * t1017 * t122 / 0.2e1 + 0.3e1 / 0.4e1 * t414 * t386 * t214 * t122 + 0.1e1 / t1032 / t113 * t1024 * t122 / 0.8e1 - 0.12e2 * t214 * t123 * t386 - 0.3e1 * t120 * t214 * t1029 - 0.4e1 * t225 * t1017 - t115 * t1017 * t122)))
  t1096 = 0.1e1 / t142 / t24
  t1116 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t899)
  t1134 = -0.11e2 / 0.24e2 * t439 * t450 - 0.11e2 / 0.24e2 * t243 * t450 + t2 / t3 / t799 * t252 * t43 * t133 * t158 * t290 * t812 / 0.54e2 - 0.3e1 / 0.8e1 * t253 * t43 * t1090 * t71 - 0.5e1 / 0.36e2 * t253 * t1096 * t133 * t71 - 0.3e1 / 0.8e1 * t42 * t145 + t141 * t257 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t1116 * t135 - 0.9e1 / 0.8e1 * t42 * t239 - 0.3e1 / 0.4e1 * t141 * t261 - 0.9e1 / 0.8e1 * t141 * t435 + t253 * t255 * t237 * t71 / 0.4e1 - 0.3e1 / 0.8e1 * t253 * t143 * t433 * t71
  t1136 = f.my_piecewise3(t1, 0, t794 + t1134)
  t1146 = f.my_piecewise5(t14, 0, t10, 0, -t898)
  t1150 = f.my_piecewise3(t459, 0, -0.8e1 / 0.27e2 / t461 / t458 * t465 * t464 + 0.4e1 / 0.3e1 * t462 * t464 * t469 + 0.4e1 / 0.3e1 * t460 * t1146)
  t1196 = -0.14e2 / 0.27e2 * t495 * t78 / t497 / t646 / t458 / t32 * t651 * t568 + 0.2e1 / 0.3e1 * t495 * t78 * t649 * t568 * t657 - t495 * t566 * (t1146 * t6 + 0.3e1 * t469) / 0.6e1
  t1197 = f.my_piecewise3(t503, t1196, 0)
  t1214 = t643 * t572
  t1225 = -t563 * t1197 / 0.18e2 + t576 * t1197 / 0.240e3 - t580 * t1197 / 0.4480e4 + t584 * t1197 / 0.103680e6 - t588 * t1197 / 0.2838528e7 + t592 * t1197 / 0.89456640e8 - t596 * t1197 / 0.3185049600e10 + t600 * t1197 / 0.126340300800e12 - 0.2e1 / 0.3e1 * t576 * t1214 + t509 * t572 * t662 / 0.2e1 + t580 * t1214 / 0.8e1 - t512 * t572 * t662 / 0.16e2
  t1258 = -t584 * t1214 / 0.80e2 + 0.3e1 / 0.640e3 * t515 * t572 * t662 + t588 * t1214 / 0.1152e4 - t518 * t572 * t662 / 0.3840e4 - t592 * t1214 / 0.21504e5 + t521 * t572 * t662 / 0.86016e5 + t596 * t1214 / 0.491520e6 - t524 * t572 * t662 / 0.2293760e7 - t600 * t1214 / 0.13271040e8 + t527 * t572 * t662 / 0.70778880e8 + 0.1e1 / t526 / t562 * t1214 / 0.412876800e9 - t690 * t572 * t662 / 0.2477260800e10
  t1260 = f.my_piecewise3(t503, 0, t1196)
  t1267 = t704 * t604
  t1272 = t538 * t696
  t1275 = t701 ** 2
  t1333 = f.my_piecewise3(t502, t1225 + t1258, -0.8e1 / 0.3e1 * t1260 * t545 - 0.8e1 * t696 * t623 - 0.8e1 * t604 * t739 - 0.8e1 / 0.3e1 * t530 * (0.7e1 / 0.2e1 * t724 * t1267 * t538 - 0.3e1 / 0.2e1 * t703 * t604 * t1272 - 0.1e1 / t1275 * t1267 * t538 / 0.4e1 - 0.6e1 * t538 * t716 * t1267 + 0.6e1 * t708 * t604 * t696 - t606 * t1260 + 0.2e1 * t1260 * t542 + 0.6e1 * t696 * t620 + 0.6e1 * t604 * t736 + 0.2e1 * t530 * (0.15e2 / 0.2e1 * t703 * t1267 * t538 - 0.6e1 * t716 * t604 * t1272 - 0.5e1 / 0.2e1 / t701 / t610 * t1267 * t538 + t611 * t1260 * t538 / 0.2e1 + 0.3e1 / 0.4e1 * t724 * t696 * t604 * t538 + 0.1e1 / t1275 / t530 * t1267 * t538 / 0.8e1 - 0.12e2 * t604 * t539 * t696 - 0.3e1 * t536 * t604 * t1272 - 0.4e1 * t615 * t1260 - t531 * t1260 * t538)))
  t1339 = f.my_piecewise3(t456, 0, -0.3e1 / 0.8e1 * t5 * t1150 * t551 - 0.3e1 / 0.8e1 * t474 * t559 - 0.9e1 / 0.8e1 * t474 * t629 + t557 * t636 / 0.4e1 - 0.3e1 / 0.4e1 * t557 * t640 - 0.9e1 / 0.8e1 * t557 * t745 - 0.5e1 / 0.36e2 * t634 * t1096 * t549 * t489 + t634 * t255 * t627 * t489 / 0.4e1 - 0.3e1 / 0.8e1 * t634 * t143 * t743 * t489 - 0.3e1 / 0.8e1 * t634 * t43 * t1333 * t489)
  d111 = 0.3e1 * t454 + 0.3e1 * t749 + t6 * (t1136 + t1339)

  res = {'v3rho3': d111}
  return res
