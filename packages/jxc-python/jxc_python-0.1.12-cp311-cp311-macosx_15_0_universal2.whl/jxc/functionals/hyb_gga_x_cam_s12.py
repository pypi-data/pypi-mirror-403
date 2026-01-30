"""Generated from hyb_gga_x_cam_s12.mpl."""

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
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))
  params_D_raw = params.D
  if isinstance(params_D_raw, (str, bytes, dict)):
    params_D = params_D_raw
  else:
    try:
      params_D_seq = list(params_D_raw)
    except TypeError:
      params_D = params_D_raw
    else:
      params_D_seq = np.asarray(params_D_seq, dtype=np.float64)
      params_D = np.concatenate((np.array([np.nan], dtype=np.float64), params_D_seq))
  params_E_raw = params.E
  if isinstance(params_E_raw, (str, bytes, dict)):
    params_E = params_E_raw
  else:
    try:
      params_E_seq = list(params_E_raw)
    except TypeError:
      params_E = params_E_raw
    else:
      params_E_seq = np.asarray(params_E_seq, dtype=np.float64)
      params_E = np.concatenate((np.array([np.nan], dtype=np.float64), params_E_seq))
  params_bx_raw = params.bx
  if isinstance(params_bx_raw, (str, bytes, dict)):
    params_bx = params_bx_raw
  else:
    try:
      params_bx_seq = list(params_bx_raw)
    except TypeError:
      params_bx = params_bx_raw
    else:
      params_bx_seq = np.asarray(params_bx_seq, dtype=np.float64)
      params_bx = np.concatenate((np.array([np.nan], dtype=np.float64), params_bx_seq))

  s12g_f = lambda x: params_bx * (params_A + params_B * (1 - 1 / (1 + params_C * x ** 2 + params_D * x ** 4)) * (1 - 1 / (1 + params_E * x ** 2)))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  ityh_enhancement = lambda xs: s12g_f(xs) / params_bx

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_k_GGA = lambda rs, z, xs: jnp.sqrt(9 * jnp.pi / (2 * X_FACTOR_C * ityh_enhancement(xs))) * f.n_spin(rs, z) ** (1 / 3)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  ityh_aa = lambda rs, z, xs: f.p.cam_omega / (2 * ityh_k_GGA(rs, z, xs))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  ityh_attenuation = lambda a: attenuation_erf(a)

  ityh_f_aa = lambda rs, z, xs: ityh_attenuation(ityh_aa(rs, z, xs))

  cam_s12_f = lambda rs, z, xs: ityh_enhancement(xs) * (1 - f.p.cam_alpha - f.p.cam_beta * ityh_f_aa(rs, z, xs))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, cam_s12_f, rs, z, xs0, xs1)

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
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))
  params_D_raw = params.D
  if isinstance(params_D_raw, (str, bytes, dict)):
    params_D = params_D_raw
  else:
    try:
      params_D_seq = list(params_D_raw)
    except TypeError:
      params_D = params_D_raw
    else:
      params_D_seq = np.asarray(params_D_seq, dtype=np.float64)
      params_D = np.concatenate((np.array([np.nan], dtype=np.float64), params_D_seq))
  params_E_raw = params.E
  if isinstance(params_E_raw, (str, bytes, dict)):
    params_E = params_E_raw
  else:
    try:
      params_E_seq = list(params_E_raw)
    except TypeError:
      params_E = params_E_raw
    else:
      params_E_seq = np.asarray(params_E_seq, dtype=np.float64)
      params_E = np.concatenate((np.array([np.nan], dtype=np.float64), params_E_seq))
  params_bx_raw = params.bx
  if isinstance(params_bx_raw, (str, bytes, dict)):
    params_bx = params_bx_raw
  else:
    try:
      params_bx_seq = list(params_bx_raw)
    except TypeError:
      params_bx = params_bx_raw
    else:
      params_bx_seq = np.asarray(params_bx_seq, dtype=np.float64)
      params_bx = np.concatenate((np.array([np.nan], dtype=np.float64), params_bx_seq))

  s12g_f = lambda x: params_bx * (params_A + params_B * (1 - 1 / (1 + params_C * x ** 2 + params_D * x ** 4)) * (1 - 1 / (1 + params_E * x ** 2)))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  ityh_enhancement = lambda xs: s12g_f(xs) / params_bx

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_k_GGA = lambda rs, z, xs: jnp.sqrt(9 * jnp.pi / (2 * X_FACTOR_C * ityh_enhancement(xs))) * f.n_spin(rs, z) ** (1 / 3)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  ityh_aa = lambda rs, z, xs: f.p.cam_omega / (2 * ityh_k_GGA(rs, z, xs))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  ityh_attenuation = lambda a: attenuation_erf(a)

  ityh_f_aa = lambda rs, z, xs: ityh_attenuation(ityh_aa(rs, z, xs))

  cam_s12_f = lambda rs, z, xs: ityh_enhancement(xs) * (1 - f.p.cam_alpha - f.p.cam_beta * ityh_f_aa(rs, z, xs))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, cam_s12_f, rs, z, xs0, xs1)

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
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))
  params_D_raw = params.D
  if isinstance(params_D_raw, (str, bytes, dict)):
    params_D = params_D_raw
  else:
    try:
      params_D_seq = list(params_D_raw)
    except TypeError:
      params_D = params_D_raw
    else:
      params_D_seq = np.asarray(params_D_seq, dtype=np.float64)
      params_D = np.concatenate((np.array([np.nan], dtype=np.float64), params_D_seq))
  params_E_raw = params.E
  if isinstance(params_E_raw, (str, bytes, dict)):
    params_E = params_E_raw
  else:
    try:
      params_E_seq = list(params_E_raw)
    except TypeError:
      params_E = params_E_raw
    else:
      params_E_seq = np.asarray(params_E_seq, dtype=np.float64)
      params_E = np.concatenate((np.array([np.nan], dtype=np.float64), params_E_seq))
  params_bx_raw = params.bx
  if isinstance(params_bx_raw, (str, bytes, dict)):
    params_bx = params_bx_raw
  else:
    try:
      params_bx_seq = list(params_bx_raw)
    except TypeError:
      params_bx = params_bx_raw
    else:
      params_bx_seq = np.asarray(params_bx_seq, dtype=np.float64)
      params_bx = np.concatenate((np.array([np.nan], dtype=np.float64), params_bx_seq))

  s12g_f = lambda x: params_bx * (params_A + params_B * (1 - 1 / (1 + params_C * x ** 2 + params_D * x ** 4)) * (1 - 1 / (1 + params_E * x ** 2)))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  ityh_enhancement = lambda xs: s12g_f(xs) / params_bx

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_k_GGA = lambda rs, z, xs: jnp.sqrt(9 * jnp.pi / (2 * X_FACTOR_C * ityh_enhancement(xs))) * f.n_spin(rs, z) ** (1 / 3)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  ityh_aa = lambda rs, z, xs: f.p.cam_omega / (2 * ityh_k_GGA(rs, z, xs))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  ityh_attenuation = lambda a: attenuation_erf(a)

  ityh_f_aa = lambda rs, z, xs: ityh_attenuation(ityh_aa(rs, z, xs))

  cam_s12_f = lambda rs, z, xs: ityh_enhancement(xs) * (1 - f.p.cam_alpha - f.p.cam_beta * ityh_f_aa(rs, z, xs))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, cam_s12_f, rs, z, xs0, xs1)

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
  t28 = params.C * s0
  t29 = r0 ** 2
  t30 = r0 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t33 = 0.1e1 / t31 / t29
  t35 = s0 ** 2
  t36 = params.D * t35
  t37 = t29 ** 2
  t40 = 0.1e1 / t30 / t37 / r0
  t42 = t28 * t33 + t36 * t40 + 0.1e1
  t45 = params.B * (0.1e1 - 0.1e1 / t42)
  t46 = params.E * s0
  t48 = t46 * t33 + 0.1e1
  t50 = 0.1e1 - 0.1e1 / t48
  t52 = t45 * t50 + params.A
  t53 = t27 * t52
  t54 = t2 ** 2
  t55 = jnp.pi * t54
  t57 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t58 = 0.1e1 / t57
  t59 = 4 ** (0.1e1 / 0.3e1)
  t60 = t58 * t59
  t63 = t55 * t60 / t52
  t64 = jnp.sqrt(t63)
  t66 = f.p.cam_omega / t64
  t67 = 2 ** (0.1e1 / 0.3e1)
  t68 = t19 * t6
  t69 = t68 ** (0.1e1 / 0.3e1)
  t71 = t67 / t69
  t73 = t66 * t71 / 0.2e1
  t74 = 0.135e1 <= t73
  t75 = 0.135e1 < t73
  t76 = f.my_piecewise3(t75, t73, 0.135e1)
  t77 = t76 ** 2
  t80 = t77 ** 2
  t83 = t80 * t77
  t86 = t80 ** 2
  t98 = t86 ** 2
  t102 = f.my_piecewise3(t75, 0.135e1, t73)
  t103 = jnp.sqrt(jnp.pi)
  t104 = 0.1e1 / t102
  t106 = jax.lax.erf(t104 / 0.2e1)
  t108 = t102 ** 2
  t109 = 0.1e1 / t108
  t111 = jnp.exp(-t109 / 0.4e1)
  t112 = t111 - 0.1e1
  t115 = t111 - 0.3e1 / 0.2e1 - 0.2e1 * t108 * t112
  t118 = 0.2e1 * t102 * t115 + t103 * t106
  t122 = f.my_piecewise3(t74, 0.1e1 / t77 / 0.36e2 - 0.1e1 / t80 / 0.960e3 + 0.1e1 / t83 / 0.26880e5 - 0.1e1 / t86 / 0.829440e6 + 0.1e1 / t86 / t77 / 0.28385280e8 - 0.1e1 / t86 / t80 / 0.1073479680e10 + 0.1e1 / t86 / t83 / 0.44590694400e11 - 0.1e1 / t98 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t102 * t118)
  t124 = -f.p.cam_beta * t122 - f.p.cam_alpha + 0.1e1
  t125 = t53 * t124
  t128 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t125)
  t129 = r1 <= f.p.dens_threshold
  t130 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t131 = 0.1e1 + t130
  t132 = t131 <= f.p.zeta_threshold
  t133 = t131 ** (0.1e1 / 0.3e1)
  t135 = f.my_piecewise3(t132, t22, t133 * t131)
  t136 = t5 * t135
  t137 = params.C * s2
  t138 = r1 ** 2
  t139 = r1 ** (0.1e1 / 0.3e1)
  t140 = t139 ** 2
  t142 = 0.1e1 / t140 / t138
  t144 = s2 ** 2
  t145 = params.D * t144
  t146 = t138 ** 2
  t149 = 0.1e1 / t139 / t146 / r1
  t151 = t137 * t142 + t145 * t149 + 0.1e1
  t154 = params.B * (0.1e1 - 0.1e1 / t151)
  t155 = params.E * s2
  t157 = t155 * t142 + 0.1e1
  t159 = 0.1e1 - 0.1e1 / t157
  t161 = t154 * t159 + params.A
  t162 = t27 * t161
  t165 = t55 * t60 / t161
  t166 = jnp.sqrt(t165)
  t168 = f.p.cam_omega / t166
  t169 = t131 * t6
  t170 = t169 ** (0.1e1 / 0.3e1)
  t172 = t67 / t170
  t174 = t168 * t172 / 0.2e1
  t175 = 0.135e1 <= t174
  t176 = 0.135e1 < t174
  t177 = f.my_piecewise3(t176, t174, 0.135e1)
  t178 = t177 ** 2
  t181 = t178 ** 2
  t184 = t181 * t178
  t187 = t181 ** 2
  t199 = t187 ** 2
  t203 = f.my_piecewise3(t176, 0.135e1, t174)
  t204 = 0.1e1 / t203
  t206 = jax.lax.erf(t204 / 0.2e1)
  t208 = t203 ** 2
  t209 = 0.1e1 / t208
  t211 = jnp.exp(-t209 / 0.4e1)
  t212 = t211 - 0.1e1
  t215 = t211 - 0.3e1 / 0.2e1 - 0.2e1 * t208 * t212
  t218 = t103 * t206 + 0.2e1 * t203 * t215
  t222 = f.my_piecewise3(t175, 0.1e1 / t178 / 0.36e2 - 0.1e1 / t181 / 0.960e3 + 0.1e1 / t184 / 0.26880e5 - 0.1e1 / t187 / 0.829440e6 + 0.1e1 / t187 / t178 / 0.28385280e8 - 0.1e1 / t187 / t181 / 0.1073479680e10 + 0.1e1 / t187 / t184 / 0.44590694400e11 - 0.1e1 / t199 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t203 * t218)
  t224 = -f.p.cam_beta * t222 - f.p.cam_alpha + 0.1e1
  t225 = t162 * t224
  t228 = f.my_piecewise3(t129, 0, -0.3e1 / 0.8e1 * t136 * t225)
  t229 = t6 ** 2
  t231 = t16 / t229
  t232 = t7 - t231
  t233 = f.my_piecewise5(t10, 0, t14, 0, t232)
  t236 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t233)
  t240 = t27 ** 2
  t241 = 0.1e1 / t240
  t245 = t26 * t241 * t52 * t124 / 0.8e1
  t246 = t42 ** 2
  t248 = params.B / t246
  t251 = 0.1e1 / t31 / t29 / r0
  t262 = t48 ** 2
  t263 = 0.1e1 / t262
  t268 = t248 * (-0.8e1 / 0.3e1 * t28 * t251 - 0.16e2 / 0.3e1 * t36 / t30 / t37 / t29) * t50 - 0.8e1 / 0.3e1 * t45 * t263 * t46 * t251
  t273 = t77 * t76
  t274 = 0.1e1 / t273
  t279 = f.p.cam_omega / t64 / t63 * t71 * jnp.pi
  t280 = t54 * t58
  t281 = t52 ** 2
  t283 = t59 / t281
  t290 = t67 / t69 / t68
  t296 = t279 * t280 * t283 * t268 / 0.4e1 - t66 * t290 * (t233 * t6 + t18 + 0.1e1) / 0.6e1
  t297 = f.my_piecewise3(t75, t296, 0)
  t300 = t80 * t76
  t301 = 0.1e1 / t300
  t304 = t80 * t273
  t305 = 0.1e1 / t304
  t309 = 0.1e1 / t86 / t76
  t313 = 0.1e1 / t86 / t273
  t317 = 0.1e1 / t86 / t300
  t321 = 0.1e1 / t86 / t304
  t325 = 0.1e1 / t98 / t76
  t329 = f.my_piecewise3(t75, 0, t296)
  t331 = t111 * t109
  t336 = 0.1e1 / t108 / t102
  t340 = t102 * t112
  t352 = f.my_piecewise3(t74, -t274 * t297 / 0.18e2 + t301 * t297 / 0.240e3 - t305 * t297 / 0.4480e4 + t309 * t297 / 0.103680e6 - t313 * t297 / 0.2838528e7 + t317 * t297 / 0.89456640e8 - t321 * t297 / 0.3185049600e10 + t325 * t297 / 0.126340300800e12, -0.8e1 / 0.3e1 * t329 * t118 - 0.8e1 / 0.3e1 * t102 * (-t331 * t329 + 0.2e1 * t329 * t115 + 0.2e1 * t102 * (t336 * t329 * t111 / 0.2e1 - 0.4e1 * t340 * t329 - t104 * t329 * t111)))
  t358 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t236 * t125 - t245 - 0.3e1 / 0.8e1 * t26 * t27 * t268 * t124 + 0.3e1 / 0.8e1 * t26 * t53 * f.p.cam_beta * t352)
  t360 = f.my_piecewise5(t14, 0, t10, 0, -t232)
  t363 = f.my_piecewise3(t132, 0, 0.4e1 / 0.3e1 * t133 * t360)
  t370 = t136 * t241 * t161 * t224 / 0.8e1
  t371 = t178 * t177
  t372 = 0.1e1 / t371
  t375 = t67 / t170 / t169
  t380 = t168 * t375 * (t360 * t6 + t130 + 0.1e1) / 0.6e1
  t381 = f.my_piecewise3(t176, -t380, 0)
  t384 = t181 * t177
  t385 = 0.1e1 / t384
  t388 = t181 * t371
  t389 = 0.1e1 / t388
  t393 = 0.1e1 / t187 / t177
  t397 = 0.1e1 / t187 / t371
  t401 = 0.1e1 / t187 / t384
  t405 = 0.1e1 / t187 / t388
  t409 = 0.1e1 / t199 / t177
  t413 = f.my_piecewise3(t176, 0, -t380)
  t415 = t211 * t209
  t420 = 0.1e1 / t208 / t203
  t424 = t203 * t212
  t436 = f.my_piecewise3(t175, -t372 * t381 / 0.18e2 + t385 * t381 / 0.240e3 - t389 * t381 / 0.4480e4 + t393 * t381 / 0.103680e6 - t397 * t381 / 0.2838528e7 + t401 * t381 / 0.89456640e8 - t405 * t381 / 0.3185049600e10 + t409 * t381 / 0.126340300800e12, -0.8e1 / 0.3e1 * t413 * t218 - 0.8e1 / 0.3e1 * t203 * (-t415 * t413 + 0.2e1 * t413 * t215 + 0.2e1 * t203 * (t420 * t413 * t211 / 0.2e1 - 0.4e1 * t424 * t413 - t204 * t413 * t211)))
  t442 = f.my_piecewise3(t129, 0, -0.3e1 / 0.8e1 * t5 * t363 * t225 - t370 + 0.3e1 / 0.8e1 * t136 * t162 * f.p.cam_beta * t436)
  vrho_0_ = t128 + t228 + t6 * (t358 + t442)
  t445 = -t7 - t231
  t446 = f.my_piecewise5(t10, 0, t14, 0, t445)
  t449 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t446)
  t457 = t66 * t290 * (t446 * t6 + t18 + 0.1e1) / 0.6e1
  t458 = f.my_piecewise3(t75, -t457, 0)
  t476 = f.my_piecewise3(t75, 0, -t457)
  t495 = f.my_piecewise3(t74, -t274 * t458 / 0.18e2 + t301 * t458 / 0.240e3 - t305 * t458 / 0.4480e4 + t309 * t458 / 0.103680e6 - t313 * t458 / 0.2838528e7 + t317 * t458 / 0.89456640e8 - t321 * t458 / 0.3185049600e10 + t325 * t458 / 0.126340300800e12, -0.8e1 / 0.3e1 * t476 * t118 - 0.8e1 / 0.3e1 * t102 * (-t331 * t476 + 0.2e1 * t476 * t115 + 0.2e1 * t102 * (t336 * t476 * t111 / 0.2e1 - 0.4e1 * t340 * t476 - t104 * t476 * t111)))
  t501 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t449 * t125 - t245 + 0.3e1 / 0.8e1 * t26 * t53 * f.p.cam_beta * t495)
  t503 = f.my_piecewise5(t14, 0, t10, 0, -t445)
  t506 = f.my_piecewise3(t132, 0, 0.4e1 / 0.3e1 * t133 * t503)
  t510 = t151 ** 2
  t512 = params.B / t510
  t515 = 0.1e1 / t140 / t138 / r1
  t526 = t157 ** 2
  t527 = 0.1e1 / t526
  t532 = t512 * (-0.8e1 / 0.3e1 * t137 * t515 - 0.16e2 / 0.3e1 * t145 / t139 / t146 / t138) * t159 - 0.8e1 / 0.3e1 * t154 * t527 * t155 * t515
  t541 = f.p.cam_omega / t166 / t165 * t172 * jnp.pi
  t542 = t161 ** 2
  t544 = t59 / t542
  t554 = t541 * t280 * t544 * t532 / 0.4e1 - t168 * t375 * (t503 * t6 + t130 + 0.1e1) / 0.6e1
  t555 = f.my_piecewise3(t176, t554, 0)
  t573 = f.my_piecewise3(t176, 0, t554)
  t592 = f.my_piecewise3(t175, -t372 * t555 / 0.18e2 + t385 * t555 / 0.240e3 - t389 * t555 / 0.4480e4 + t393 * t555 / 0.103680e6 - t397 * t555 / 0.2838528e7 + t401 * t555 / 0.89456640e8 - t405 * t555 / 0.3185049600e10 + t409 * t555 / 0.126340300800e12, -0.8e1 / 0.3e1 * t573 * t218 - 0.8e1 / 0.3e1 * t203 * (-t415 * t573 + 0.2e1 * t573 * t215 + 0.2e1 * t203 * (t420 * t573 * t211 / 0.2e1 - 0.4e1 * t424 * t573 - t204 * t573 * t211)))
  t598 = f.my_piecewise3(t129, 0, -0.3e1 / 0.8e1 * t5 * t506 * t225 - t370 - 0.3e1 / 0.8e1 * t136 * t27 * t532 * t224 + 0.3e1 / 0.8e1 * t136 * t162 * f.p.cam_beta * t592)
  vrho_1_ = t128 + t228 + t6 * (t501 + t598)
  t611 = t248 * (0.2e1 * params.D * s0 * t40 + params.C * t33) * t50 + t45 * t263 * params.E * t33
  t618 = t279 * t280 * t283 * t611 / 0.4e1
  t619 = f.my_piecewise3(t75, t618, 0)
  t637 = f.my_piecewise3(t75, 0, t618)
  t656 = f.my_piecewise3(t74, -t274 * t619 / 0.18e2 + t301 * t619 / 0.240e3 - t305 * t619 / 0.4480e4 + t309 * t619 / 0.103680e6 - t313 * t619 / 0.2838528e7 + t317 * t619 / 0.89456640e8 - t321 * t619 / 0.3185049600e10 + t325 * t619 / 0.126340300800e12, -0.8e1 / 0.3e1 * t637 * t118 - 0.8e1 / 0.3e1 * t102 * (-t331 * t637 + 0.2e1 * t637 * t115 + 0.2e1 * t102 * (t336 * t637 * t111 / 0.2e1 - 0.4e1 * t340 * t637 - t104 * t637 * t111)))
  t662 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * t611 * t124 + 0.3e1 / 0.8e1 * t26 * t53 * f.p.cam_beta * t656)
  vsigma_0_ = t6 * t662
  vsigma_1_ = 0.0e0
  t673 = t512 * (0.2e1 * params.D * s2 * t149 + params.C * t142) * t159 + t154 * t527 * params.E * t142
  t680 = t541 * t280 * t544 * t673 / 0.4e1
  t681 = f.my_piecewise3(t176, t680, 0)
  t699 = f.my_piecewise3(t176, 0, t680)
  t718 = f.my_piecewise3(t175, -t372 * t681 / 0.18e2 + t385 * t681 / 0.240e3 - t389 * t681 / 0.4480e4 + t393 * t681 / 0.103680e6 - t397 * t681 / 0.2838528e7 + t401 * t681 / 0.89456640e8 - t405 * t681 / 0.3185049600e10 + t409 * t681 / 0.126340300800e12, -0.8e1 / 0.3e1 * t699 * t218 - 0.8e1 / 0.3e1 * t203 * (-t415 * t699 + 0.2e1 * t699 * t215 + 0.2e1 * t203 * (t420 * t699 * t211 / 0.2e1 - 0.4e1 * t424 * t699 - t204 * t699 * t211)))
  t724 = f.my_piecewise3(t129, 0, 0.3e1 / 0.8e1 * t136 * t162 * f.p.cam_beta * t718 - 0.3e1 / 0.8e1 * t136 * t27 * t673 * t224)
  vsigma_2_ = t6 * t724
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
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))
  params_D_raw = params.D
  if isinstance(params_D_raw, (str, bytes, dict)):
    params_D = params_D_raw
  else:
    try:
      params_D_seq = list(params_D_raw)
    except TypeError:
      params_D = params_D_raw
    else:
      params_D_seq = np.asarray(params_D_seq, dtype=np.float64)
      params_D = np.concatenate((np.array([np.nan], dtype=np.float64), params_D_seq))
  params_E_raw = params.E
  if isinstance(params_E_raw, (str, bytes, dict)):
    params_E = params_E_raw
  else:
    try:
      params_E_seq = list(params_E_raw)
    except TypeError:
      params_E = params_E_raw
    else:
      params_E_seq = np.asarray(params_E_seq, dtype=np.float64)
      params_E = np.concatenate((np.array([np.nan], dtype=np.float64), params_E_seq))
  params_bx_raw = params.bx
  if isinstance(params_bx_raw, (str, bytes, dict)):
    params_bx = params_bx_raw
  else:
    try:
      params_bx_seq = list(params_bx_raw)
    except TypeError:
      params_bx = params_bx_raw
    else:
      params_bx_seq = np.asarray(params_bx_seq, dtype=np.float64)
      params_bx = np.concatenate((np.array([np.nan], dtype=np.float64), params_bx_seq))

  s12g_f = lambda x: params_bx * (params_A + params_B * (1 - 1 / (1 + params_C * x ** 2 + params_D * x ** 4)) * (1 - 1 / (1 + params_E * x ** 2)))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  ityh_enhancement = lambda xs: s12g_f(xs) / params_bx

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  ityh_k_GGA = lambda rs, z, xs: jnp.sqrt(9 * jnp.pi / (2 * X_FACTOR_C * ityh_enhancement(xs))) * f.n_spin(rs, z) ** (1 / 3)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  ityh_aa = lambda rs, z, xs: f.p.cam_omega / (2 * ityh_k_GGA(rs, z, xs))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  ityh_attenuation = lambda a: attenuation_erf(a)

  ityh_f_aa = lambda rs, z, xs: ityh_attenuation(ityh_aa(rs, z, xs))

  cam_s12_f = lambda rs, z, xs: ityh_enhancement(xs) * (1 - f.p.cam_alpha - f.p.cam_beta * ityh_f_aa(rs, z, xs))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, cam_s12_f, rs, z, xs0, xs1)

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
  t20 = params.C * s0
  t21 = 2 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = r0 ** 2
  t24 = t19 ** 2
  t26 = 0.1e1 / t24 / t23
  t27 = t22 * t26
  t29 = s0 ** 2
  t30 = params.D * t29
  t31 = t23 ** 2
  t35 = t21 / t19 / t31 / r0
  t38 = t20 * t27 + 0.2e1 * t30 * t35 + 0.1e1
  t41 = params.B * (0.1e1 - 0.1e1 / t38)
  t42 = params.E * s0
  t44 = t42 * t27 + 0.1e1
  t46 = 0.1e1 - 0.1e1 / t44
  t48 = t41 * t46 + params.A
  t49 = t19 * t48
  t50 = t3 ** 2
  t53 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t54 = 0.1e1 / t53
  t55 = 4 ** (0.1e1 / 0.3e1)
  t59 = jnp.pi * t50 * t54 * t55 / t48
  t60 = jnp.sqrt(t59)
  t62 = f.p.cam_omega / t60
  t63 = t11 * r0
  t64 = t63 ** (0.1e1 / 0.3e1)
  t66 = t21 / t64
  t68 = t62 * t66 / 0.2e1
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
  t119 = -f.p.cam_beta * t117 - f.p.cam_alpha + 0.1e1
  t123 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t49 * t119)
  t129 = t38 ** 2
  t131 = params.B / t129
  t135 = t22 / t24 / t23 / r0
  t147 = t44 ** 2
  t149 = t41 / t147
  t153 = t131 * (-0.8e1 / 0.3e1 * t20 * t135 - 0.32e2 / 0.3e1 * t30 * t21 / t19 / t31 / t23) * t46 - 0.8e1 / 0.3e1 * t149 * t42 * t135
  t158 = t72 * t71
  t159 = 0.1e1 / t158
  t164 = f.p.cam_omega / t60 / t59 * t66 * jnp.pi
  t165 = t50 * t54
  t166 = t48 ** 2
  t168 = t55 / t166
  t179 = t164 * t165 * t168 * t153 / 0.4e1 - t62 * t21 / t64 / t63 * t11 / 0.6e1
  t180 = f.my_piecewise3(t70, t179, 0)
  t183 = t75 * t71
  t184 = 0.1e1 / t183
  t187 = t75 * t158
  t188 = 0.1e1 / t187
  t192 = 0.1e1 / t81 / t71
  t196 = 0.1e1 / t81 / t158
  t200 = 0.1e1 / t81 / t183
  t204 = 0.1e1 / t81 / t187
  t208 = 0.1e1 / t93 / t71
  t212 = f.my_piecewise3(t70, 0, t179)
  t214 = t106 * t104
  t219 = 0.1e1 / t103 / t97
  t223 = t97 * t107
  t235 = f.my_piecewise3(t69, -t159 * t180 / 0.18e2 + t184 * t180 / 0.240e3 - t188 * t180 / 0.4480e4 + t192 * t180 / 0.103680e6 - t196 * t180 / 0.2838528e7 + t200 * t180 / 0.89456640e8 - t204 * t180 / 0.3185049600e10 + t208 * t180 / 0.126340300800e12, -0.8e1 / 0.3e1 * t212 * t113 - 0.8e1 / 0.3e1 * t97 * (-t214 * t212 + 0.2e1 * t212 * t110 + 0.2e1 * t97 * (t219 * t212 * t106 / 0.2e1 - 0.4e1 * t223 * t212 - t99 * t212 * t106)))
  t241 = f.my_piecewise3(t2, 0, -t18 / t24 * t48 * t119 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t153 * t119 + 0.3e1 / 0.8e1 * t18 * t49 * f.p.cam_beta * t235)
  vrho_0_ = 0.2e1 * r0 * t241 + 0.2e1 * t123
  t255 = t131 * (0.4e1 * params.D * s0 * t35 + params.C * t22 * t26) * t46 + t149 * params.E * t22 * t26
  t262 = t164 * t165 * t168 * t255 / 0.4e1
  t263 = f.my_piecewise3(t70, t262, 0)
  t281 = f.my_piecewise3(t70, 0, t262)
  t300 = f.my_piecewise3(t69, -t159 * t263 / 0.18e2 + t184 * t263 / 0.240e3 - t188 * t263 / 0.4480e4 + t192 * t263 / 0.103680e6 - t196 * t263 / 0.2838528e7 + t200 * t263 / 0.89456640e8 - t204 * t263 / 0.3185049600e10 + t208 * t263 / 0.126340300800e12, -0.8e1 / 0.3e1 * t281 * t113 - 0.8e1 / 0.3e1 * t97 * (-t214 * t281 + 0.2e1 * t281 * t110 + 0.2e1 * t97 * (t219 * t281 * t106 / 0.2e1 - 0.4e1 * t223 * t281 - t99 * t281 * t106)))
  t306 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t255 * t119 + 0.3e1 / 0.8e1 * t18 * t49 * f.p.cam_beta * t300)
  vsigma_0_ = 0.2e1 * r0 * t306
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
  t22 = params.C * s0
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = r0 ** 2
  t27 = 0.1e1 / t20 / t25
  t28 = t24 * t27
  t30 = s0 ** 2
  t31 = params.D * t30
  t32 = t25 ** 2
  t35 = 0.1e1 / t19 / t32 / r0
  t36 = t23 * t35
  t39 = t22 * t28 + 0.2e1 * t31 * t36 + 0.1e1
  t42 = params.B * (0.1e1 - 0.1e1 / t39)
  t43 = params.E * s0
  t45 = t43 * t28 + 0.1e1
  t47 = 0.1e1 - 0.1e1 / t45
  t49 = t42 * t47 + params.A
  t50 = t21 * t49
  t51 = t3 ** 2
  t54 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t55 = 0.1e1 / t54
  t56 = 4 ** (0.1e1 / 0.3e1)
  t60 = jnp.pi * t51 * t55 * t56 / t49
  t61 = jnp.sqrt(t60)
  t63 = f.p.cam_omega / t61
  t64 = t11 * r0
  t65 = t64 ** (0.1e1 / 0.3e1)
  t67 = t23 / t65
  t69 = t63 * t67 / 0.2e1
  t70 = 0.135e1 <= t69
  t71 = 0.135e1 < t69
  t72 = f.my_piecewise3(t71, t69, 0.135e1)
  t73 = t72 ** 2
  t76 = t73 ** 2
  t77 = 0.1e1 / t76
  t79 = t76 * t73
  t80 = 0.1e1 / t79
  t82 = t76 ** 2
  t83 = 0.1e1 / t82
  t86 = 0.1e1 / t82 / t73
  t89 = 0.1e1 / t82 / t76
  t92 = 0.1e1 / t82 / t79
  t94 = t82 ** 2
  t95 = 0.1e1 / t94
  t98 = f.my_piecewise3(t71, 0.135e1, t69)
  t99 = jnp.sqrt(jnp.pi)
  t100 = 0.1e1 / t98
  t102 = jax.lax.erf(t100 / 0.2e1)
  t104 = t98 ** 2
  t105 = 0.1e1 / t104
  t107 = jnp.exp(-t105 / 0.4e1)
  t108 = t107 - 0.1e1
  t111 = t107 - 0.3e1 / 0.2e1 - 0.2e1 * t104 * t108
  t114 = t99 * t102 + 0.2e1 * t98 * t111
  t118 = f.my_piecewise3(t70, 0.1e1 / t73 / 0.36e2 - t77 / 0.960e3 + t80 / 0.26880e5 - t83 / 0.829440e6 + t86 / 0.28385280e8 - t89 / 0.1073479680e10 + t92 / 0.44590694400e11 - t95 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t98 * t114)
  t120 = -f.p.cam_beta * t118 - f.p.cam_alpha + 0.1e1
  t124 = t39 ** 2
  t126 = params.B / t124
  t127 = t25 * r0
  t129 = 0.1e1 / t20 / t127
  t130 = t24 * t129
  t135 = 0.1e1 / t19 / t32 / t25
  t136 = t23 * t135
  t139 = -0.8e1 / 0.3e1 * t22 * t130 - 0.32e2 / 0.3e1 * t31 * t136
  t142 = t45 ** 2
  t143 = 0.1e1 / t142
  t144 = t42 * t143
  t145 = t43 * t130
  t148 = t126 * t139 * t47 - 0.8e1 / 0.3e1 * t144 * t145
  t149 = t19 * t148
  t153 = t19 * t49
  t154 = t73 * t72
  t155 = 0.1e1 / t154
  t158 = f.p.cam_omega / t61 / t60
  t160 = t158 * t67 * jnp.pi
  t161 = t51 * t55
  t162 = t49 ** 2
  t163 = 0.1e1 / t162
  t164 = t56 * t163
  t171 = t23 / t65 / t64
  t175 = t160 * t161 * t164 * t148 / 0.4e1 - t63 * t171 * t11 / 0.6e1
  t176 = f.my_piecewise3(t71, t175, 0)
  t179 = t76 * t72
  t180 = 0.1e1 / t179
  t183 = t76 * t154
  t184 = 0.1e1 / t183
  t188 = 0.1e1 / t82 / t72
  t192 = 0.1e1 / t82 / t154
  t196 = 0.1e1 / t82 / t179
  t200 = 0.1e1 / t82 / t183
  t204 = 0.1e1 / t94 / t72
  t208 = f.my_piecewise3(t71, 0, t175)
  t210 = t107 * t105
  t215 = 0.1e1 / t104 / t98
  t219 = t98 * t108
  t224 = t215 * t208 * t107 / 0.2e1 - 0.4e1 * t219 * t208 - t100 * t208 * t107
  t227 = 0.2e1 * t208 * t111 - t210 * t208 + 0.2e1 * t98 * t224
  t231 = f.my_piecewise3(t70, -t155 * t176 / 0.18e2 + t180 * t176 / 0.240e3 - t184 * t176 / 0.4480e4 + t188 * t176 / 0.103680e6 - t192 * t176 / 0.2838528e7 + t196 * t176 / 0.89456640e8 - t200 * t176 / 0.3185049600e10 + t204 * t176 / 0.126340300800e12, -0.8e1 / 0.3e1 * t208 * t114 - 0.8e1 / 0.3e1 * t98 * t227)
  t232 = f.p.cam_beta * t231
  t237 = f.my_piecewise3(t2, 0, -t18 * t50 * t120 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t149 * t120 + 0.3e1 / 0.8e1 * t18 * t153 * t232)
  t254 = params.B / t124 / t39
  t255 = t139 ** 2
  t261 = t24 / t20 / t32
  t267 = t23 / t19 / t32 / t127
  t279 = t42 / t142 / t45
  t280 = params.E ** 2
  t288 = -0.2e1 * t254 * t255 * t47 + t126 * (0.88e2 / 0.9e1 * t22 * t261 + 0.608e3 / 0.9e1 * t31 * t267) * t47 - 0.16e2 / 0.3e1 * t126 * t139 * t143 * t145 - 0.256e3 / 0.9e1 * t279 * t280 * t30 * t267 + 0.88e2 / 0.9e1 * t144 * t43 * t261
  t296 = t176 ** 2
  t299 = jnp.pi ** 2
  t301 = t54 ** 2
  t302 = 0.1e1 / t301
  t303 = t56 ** 2
  t312 = f.p.cam_omega / t61 / t3 / t302 / t303 / t163 * t67 / 0.3e1
  t313 = t3 * t302
  t314 = t162 ** 2
  t315 = 0.1e1 / t314
  t316 = t303 * t315
  t317 = t148 ** 2
  t323 = t158 * t171 * jnp.pi
  t324 = t161 * t56
  t331 = 0.1e1 / t162 / t49
  t332 = t56 * t331
  t341 = t11 ** 2
  t349 = 0.9e1 / 0.8e1 * t312 * t313 * t316 * t317 - t323 * t324 * t163 * t148 * t11 / 0.6e1 - t160 * t161 * t332 * t317 / 0.2e1 + t160 * t161 * t164 * t288 / 0.4e1 + 0.2e1 / 0.9e1 * t63 * t23 / t65 / t25
  t350 = f.my_piecewise3(t71, t349, 0)
  t378 = 0.1e1 / t94 / t73
  t383 = t77 * t296 / 0.6e1 - t155 * t350 / 0.18e2 - t80 * t296 / 0.48e2 + t180 * t350 / 0.240e3 + t83 * t296 / 0.640e3 - t184 * t350 / 0.4480e4 - t86 * t296 / 0.11520e5 + t188 * t350 / 0.103680e6 + t89 * t296 / 0.258048e6 - t192 * t350 / 0.2838528e7 - t92 * t296 / 0.6881280e7 + t196 * t350 / 0.89456640e8 + t95 * t296 / 0.212336640e9 - t200 * t350 / 0.3185049600e10 - t378 * t296 / 0.7431782400e10 + t204 * t350 / 0.126340300800e12
  t384 = f.my_piecewise3(t71, 0, t349)
  t389 = t104 ** 2
  t391 = 0.1e1 / t389 / t98
  t392 = t208 ** 2
  t396 = t107 * t215
  t404 = 0.1e1 / t389
  t412 = 0.1e1 / t389 / t104
  t431 = f.my_piecewise3(t70, t383, -0.8e1 / 0.3e1 * t384 * t114 - 0.16e2 / 0.3e1 * t208 * t227 - 0.8e1 / 0.3e1 * t98 * (-t391 * t392 * t107 / 0.2e1 + 0.2e1 * t396 * t392 - t210 * t384 + 0.2e1 * t384 * t111 + 0.4e1 * t208 * t224 + 0.2e1 * t98 * (-0.2e1 * t404 * t392 * t107 + t215 * t384 * t107 / 0.2e1 + t412 * t392 * t107 / 0.4e1 - 0.4e1 * t392 * t108 - t105 * t392 * t107 - 0.4e1 * t219 * t384 - t100 * t384 * t107)))
  t437 = f.my_piecewise3(t2, 0, t18 / t20 / r0 * t49 * t120 / 0.12e2 - t18 * t21 * t148 * t120 / 0.4e1 + t18 * t50 * t232 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t19 * t288 * t120 + 0.3e1 / 0.4e1 * t18 * t149 * t232 + 0.3e1 / 0.8e1 * t18 * t153 * f.p.cam_beta * t431)
  v2rho2_0_ = 0.2e1 * r0 * t437 + 0.4e1 * t237
  t440 = params.C * t24
  t442 = params.D * s0
  t445 = t440 * t27 + 0.4e1 * t442 * t36
  t446 = t445 * t47
  t448 = params.E * t24
  t451 = t144 * t448 * t27 + t126 * t446
  t452 = t19 * t451
  t458 = t160 * t161 * t164 * t451 / 0.4e1
  t459 = f.my_piecewise3(t71, t458, 0)
  t477 = f.my_piecewise3(t71, 0, t458)
  t489 = t215 * t477 * t107 / 0.2e1 - 0.4e1 * t219 * t477 - t100 * t477 * t107
  t492 = 0.2e1 * t477 * t111 - t210 * t477 + 0.2e1 * t98 * t489
  t496 = f.my_piecewise3(t70, -t155 * t459 / 0.18e2 + t180 * t459 / 0.240e3 - t184 * t459 / 0.4480e4 + t188 * t459 / 0.103680e6 - t192 * t459 / 0.2838528e7 + t196 * t459 / 0.89456640e8 - t200 * t459 / 0.3185049600e10 + t204 * t459 / 0.126340300800e12, -0.8e1 / 0.3e1 * t477 * t114 - 0.8e1 / 0.3e1 * t98 * t492)
  t497 = f.p.cam_beta * t496
  t502 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t452 * t120 + 0.3e1 / 0.8e1 * t18 * t153 * t497)
  t523 = t143 * params.E * t28
  t525 = t280 * t23
  t533 = -0.2e1 * t254 * t446 * t139 + t126 * (-0.8e1 / 0.3e1 * t440 * t129 - 0.64e2 / 0.3e1 * t442 * t136) * t47 - 0.8e1 / 0.3e1 * t126 * t445 * t143 * t145 + t126 * t139 * t523 + 0.32e2 / 0.3e1 * t279 * t525 * t135 * s0 - 0.8e1 / 0.3e1 * t144 * t448 * t129
  t570 = 0.9e1 / 0.8e1 * t312 * t313 * t303 * t315 * t451 * t148 - t323 * t324 * t163 * t451 * t11 / 0.12e2 - t160 * t324 * t331 * t451 * t148 / 0.2e1 + t160 * t161 * t164 * t533 / 0.4e1
  t571 = f.my_piecewise3(t71, t570, 0)
  t609 = t77 * t459 * t176 / 0.6e1 - t155 * t571 / 0.18e2 - t80 * t459 * t176 / 0.48e2 + t180 * t571 / 0.240e3 + t83 * t459 * t176 / 0.640e3 - t184 * t571 / 0.4480e4 - t86 * t459 * t176 / 0.11520e5 + t188 * t571 / 0.103680e6 + t89 * t459 * t176 / 0.258048e6 - t192 * t571 / 0.2838528e7 - t92 * t459 * t176 / 0.6881280e7 + t196 * t571 / 0.89456640e8 + t95 * t459 * t176 / 0.212336640e9 - t200 * t571 / 0.3185049600e10 - t378 * t459 * t176 / 0.7431782400e10 + t204 * t571 / 0.126340300800e12
  t610 = f.my_piecewise3(t71, 0, t570)
  t615 = t107 * t477
  t629 = t107 * t208
  t654 = f.my_piecewise3(t70, t609, -0.8e1 / 0.3e1 * t610 * t114 - 0.8e1 / 0.3e1 * t477 * t227 - 0.8e1 / 0.3e1 * t208 * t492 - 0.8e1 / 0.3e1 * t98 * (-t391 * t208 * t615 / 0.2e1 + 0.2e1 * t396 * t477 * t208 - t210 * t610 + 0.2e1 * t610 * t111 + 0.2e1 * t477 * t224 + 0.2e1 * t208 * t489 + 0.2e1 * t98 * (-0.2e1 * t404 * t477 * t629 + t215 * t610 * t107 / 0.2e1 + t412 * t477 * t629 / 0.4e1 - 0.4e1 * t208 * t108 * t477 - t105 * t208 * t615 - 0.4e1 * t219 * t610 - t100 * t610 * t107)))
  t660 = f.my_piecewise3(t2, 0, -t18 * t21 * t451 * t120 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t533 * t120 + 0.3e1 / 0.8e1 * t18 * t452 * t232 + t18 * t50 * t497 / 0.8e1 + 0.3e1 / 0.8e1 * t18 * t149 * t497 + 0.3e1 / 0.8e1 * t18 * t153 * f.p.cam_beta * t654)
  v2rhosigma_0_ = 0.2e1 * r0 * t660 + 0.2e1 * t502
  t663 = t445 ** 2
  t677 = 0.4e1 * t126 * params.D * t36 * t47 + 0.2e1 * t126 * t445 * t523 - 0.2e1 * t254 * t663 * t47 - 0.4e1 * t279 * t525 * t35
  t685 = t459 ** 2
  t688 = t451 ** 2
  t701 = 0.9e1 / 0.8e1 * t312 * t313 * t316 * t688 - t160 * t161 * t332 * t688 / 0.2e1 + t160 * t161 * t164 * t677 / 0.4e1
  t702 = f.my_piecewise3(t71, t701, 0)
  t733 = t77 * t685 / 0.6e1 - t155 * t702 / 0.18e2 - t80 * t685 / 0.48e2 + t180 * t702 / 0.240e3 + t83 * t685 / 0.640e3 - t184 * t702 / 0.4480e4 - t86 * t685 / 0.11520e5 + t188 * t702 / 0.103680e6 + t89 * t685 / 0.258048e6 - t192 * t702 / 0.2838528e7 - t92 * t685 / 0.6881280e7 + t196 * t702 / 0.89456640e8 + t95 * t685 / 0.212336640e9 - t200 * t702 / 0.3185049600e10 - t378 * t685 / 0.7431782400e10 + t204 * t702 / 0.126340300800e12
  t734 = f.my_piecewise3(t71, 0, t701)
  t739 = t477 ** 2
  t774 = f.my_piecewise3(t70, t733, -0.8e1 / 0.3e1 * t734 * t114 - 0.16e2 / 0.3e1 * t477 * t492 - 0.8e1 / 0.3e1 * t98 * (-t391 * t739 * t107 / 0.2e1 + 0.2e1 * t396 * t739 - t210 * t734 + 0.2e1 * t734 * t111 + 0.4e1 * t477 * t489 + 0.2e1 * t98 * (-0.2e1 * t404 * t739 * t107 + t215 * t734 * t107 / 0.2e1 + t412 * t739 * t107 / 0.4e1 - 0.4e1 * t739 * t108 - t105 * t739 * t107 - 0.4e1 * t219 * t734 - t100 * t734 * t107)))
  t780 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t677 * t120 + 0.3e1 / 0.4e1 * t18 * t452 * t497 + 0.3e1 / 0.8e1 * t18 * t153 * f.p.cam_beta * t774)
  v2sigma2_0_ = 0.2e1 * r0 * t780
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
  t23 = params.C * s0
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = r0 ** 2
  t28 = 0.1e1 / t20 / t26
  t29 = t25 * t28
  t31 = s0 ** 2
  t32 = params.D * t31
  t33 = t26 ** 2
  t34 = t33 * r0
  t40 = 0.1e1 + t23 * t29 + 0.2e1 * t32 * t24 / t19 / t34
  t43 = params.B * (0.1e1 - 0.1e1 / t40)
  t44 = params.E * s0
  t46 = t44 * t29 + 0.1e1
  t48 = 0.1e1 - 0.1e1 / t46
  t50 = t43 * t48 + params.A
  t51 = t22 * t50
  t52 = t3 ** 2
  t55 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t56 = 0.1e1 / t55
  t57 = 4 ** (0.1e1 / 0.3e1)
  t61 = jnp.pi * t52 * t56 * t57 / t50
  t62 = jnp.sqrt(t61)
  t64 = f.p.cam_omega / t62
  t65 = t11 * r0
  t66 = t65 ** (0.1e1 / 0.3e1)
  t67 = 0.1e1 / t66
  t68 = t24 * t67
  t70 = t64 * t68 / 0.2e1
  t71 = 0.135e1 <= t70
  t72 = 0.135e1 < t70
  t73 = f.my_piecewise3(t72, t70, 0.135e1)
  t74 = t73 ** 2
  t77 = t74 ** 2
  t78 = 0.1e1 / t77
  t80 = t77 * t74
  t81 = 0.1e1 / t80
  t83 = t77 ** 2
  t84 = 0.1e1 / t83
  t87 = 0.1e1 / t83 / t74
  t90 = 0.1e1 / t83 / t77
  t93 = 0.1e1 / t83 / t80
  t95 = t83 ** 2
  t96 = 0.1e1 / t95
  t99 = f.my_piecewise3(t72, 0.135e1, t70)
  t100 = jnp.sqrt(jnp.pi)
  t101 = 0.1e1 / t99
  t103 = jnp.erf(t101 / 0.2e1)
  t105 = t99 ** 2
  t106 = 0.1e1 / t105
  t108 = jnp.exp(-t106 / 0.4e1)
  t109 = t108 - 0.1e1
  t112 = t108 - 0.3e1 / 0.2e1 - 0.2e1 * t105 * t109
  t115 = t100 * t103 + 0.2e1 * t99 * t112
  t119 = f.my_piecewise3(t71, 0.1e1 / t74 / 0.36e2 - t78 / 0.960e3 + t81 / 0.26880e5 - t84 / 0.829440e6 + t87 / 0.28385280e8 - t90 / 0.1073479680e10 + t93 / 0.44590694400e11 - t96 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t99 * t115)
  t121 = -f.p.cam_beta * t119 - f.p.cam_alpha + 0.1e1
  t125 = 0.1e1 / t20
  t126 = t40 ** 2
  t128 = params.B / t126
  t129 = t26 * r0
  t132 = t25 / t20 / t129
  t141 = -0.8e1 / 0.3e1 * t23 * t132 - 0.32e2 / 0.3e1 * t32 * t24 / t19 / t33 / t26
  t142 = t141 * t48
  t144 = t46 ** 2
  t145 = 0.1e1 / t144
  t146 = t43 * t145
  t147 = t44 * t132
  t150 = t128 * t142 - 0.8e1 / 0.3e1 * t146 * t147
  t151 = t125 * t150
  t155 = t125 * t50
  t156 = t74 * t73
  t157 = 0.1e1 / t156
  t160 = f.p.cam_omega / t62 / t61
  t162 = t160 * t68 * jnp.pi
  t163 = t52 * t56
  t164 = t50 ** 2
  t165 = 0.1e1 / t164
  t166 = t57 * t165
  t173 = t24 / t66 / t65
  t177 = t162 * t163 * t166 * t150 / 0.4e1 - t64 * t173 * t11 / 0.6e1
  t178 = f.my_piecewise3(t72, t177, 0)
  t181 = t77 * t73
  t182 = 0.1e1 / t181
  t185 = t77 * t156
  t186 = 0.1e1 / t185
  t190 = 0.1e1 / t83 / t73
  t194 = 0.1e1 / t83 / t156
  t198 = 0.1e1 / t83 / t181
  t202 = 0.1e1 / t83 / t185
  t206 = 0.1e1 / t95 / t73
  t210 = f.my_piecewise3(t72, 0, t177)
  t212 = t108 * t106
  t216 = t105 * t99
  t217 = 0.1e1 / t216
  t221 = t99 * t109
  t226 = t217 * t210 * t108 / 0.2e1 - 0.4e1 * t221 * t210 - t101 * t210 * t108
  t229 = 0.2e1 * t210 * t112 - t212 * t210 + 0.2e1 * t99 * t226
  t233 = f.my_piecewise3(t71, -t157 * t178 / 0.18e2 + t182 * t178 / 0.240e3 - t186 * t178 / 0.4480e4 + t190 * t178 / 0.103680e6 - t194 * t178 / 0.2838528e7 + t198 * t178 / 0.89456640e8 - t202 * t178 / 0.3185049600e10 + t206 * t178 / 0.126340300800e12, -0.8e1 / 0.3e1 * t210 * t115 - 0.8e1 / 0.3e1 * t99 * t229)
  t234 = f.p.cam_beta * t233
  t240 = params.B / t126 / t40
  t241 = t141 ** 2
  t247 = t25 / t20 / t33
  t253 = t24 / t19 / t33 / t129
  t256 = 0.88e2 / 0.9e1 * t23 * t247 + 0.608e3 / 0.9e1 * t32 * t253
  t260 = t128 * t141 * t145
  t264 = 0.1e1 / t144 / t46
  t265 = t43 * t264
  t266 = params.E ** 2
  t267 = t266 * t31
  t268 = t267 * t253
  t271 = t44 * t247
  t274 = -0.2e1 * t240 * t241 * t48 + t128 * t256 * t48 - 0.16e2 / 0.3e1 * t260 * t147 - 0.256e3 / 0.9e1 * t265 * t268 + 0.88e2 / 0.9e1 * t146 * t271
  t275 = t19 * t274
  t279 = t19 * t150
  t283 = t19 * t50
  t284 = t178 ** 2
  t287 = jnp.pi ** 2
  t289 = t55 ** 2
  t290 = 0.1e1 / t289
  t291 = t57 ** 2
  t298 = f.p.cam_omega / t62 / t287 / t3 / t290 / t291 / t165 / 0.3e1
  t300 = t298 * t68 * t287
  t301 = t3 * t290
  t302 = t164 ** 2
  t303 = 0.1e1 / t302
  t305 = t150 ** 2
  t311 = t160 * t173 * jnp.pi
  t312 = t163 * t57
  t313 = t165 * t150
  t319 = 0.1e1 / t164 / t50
  t329 = t11 ** 2
  t333 = t24 / t66 / t329 / t26
  t337 = 0.9e1 / 0.8e1 * t300 * t301 * t291 * t303 * t305 - t311 * t312 * t313 * t11 / 0.6e1 - t162 * t163 * t57 * t319 * t305 / 0.2e1 + t162 * t163 * t166 * t274 / 0.4e1 + 0.2e1 / 0.9e1 * t64 * t333 * t329
  t338 = f.my_piecewise3(t72, t337, 0)
  t366 = 0.1e1 / t95 / t74
  t371 = t78 * t284 / 0.6e1 - t157 * t338 / 0.18e2 - t81 * t284 / 0.48e2 + t182 * t338 / 0.240e3 + t84 * t284 / 0.640e3 - t186 * t338 / 0.4480e4 - t87 * t284 / 0.11520e5 + t190 * t338 / 0.103680e6 + t90 * t284 / 0.258048e6 - t194 * t338 / 0.2838528e7 - t93 * t284 / 0.6881280e7 + t198 * t338 / 0.89456640e8 + t96 * t284 / 0.212336640e9 - t202 * t338 / 0.3185049600e10 - t366 * t284 / 0.7431782400e10 + t206 * t338 / 0.126340300800e12
  t372 = f.my_piecewise3(t72, 0, t337)
  t377 = t105 ** 2
  t379 = 0.1e1 / t377 / t99
  t380 = t210 ** 2
  t384 = t108 * t217
  t392 = 0.1e1 / t377
  t400 = 0.1e1 / t377 / t105
  t412 = -0.2e1 * t392 * t380 * t108 + t217 * t372 * t108 / 0.2e1 + t400 * t380 * t108 / 0.4e1 - 0.4e1 * t380 * t109 - t106 * t380 * t108 - 0.4e1 * t221 * t372 - t101 * t372 * t108
  t415 = -t379 * t380 * t108 / 0.2e1 + 0.2e1 * t384 * t380 - t212 * t372 + 0.2e1 * t372 * t112 + 0.4e1 * t210 * t226 + 0.2e1 * t99 * t412
  t419 = f.my_piecewise3(t71, t371, -0.8e1 / 0.3e1 * t372 * t115 - 0.16e2 / 0.3e1 * t210 * t229 - 0.8e1 / 0.3e1 * t99 * t415)
  t420 = f.p.cam_beta * t419
  t425 = f.my_piecewise3(t2, 0, t18 * t51 * t121 / 0.12e2 - t18 * t151 * t121 / 0.4e1 + t18 * t155 * t234 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t275 * t121 + 0.3e1 / 0.4e1 * t18 * t279 * t234 + 0.3e1 / 0.8e1 * t18 * t283 * t420)
  t448 = t126 ** 2
  t464 = t25 / t20 / t34
  t467 = t33 ** 2
  t470 = t24 / t19 / t467
  t486 = t144 ** 2
  t503 = 0.6e1 * params.B / t448 * t241 * t141 * t48 - 0.6e1 * t240 * t142 * t256 + 0.16e2 * t240 * t241 * t145 * t147 + t128 * (-0.1232e4 / 0.27e2 * t23 * t464 - 0.13376e5 / 0.27e2 * t32 * t470) * t48 - 0.8e1 * t128 * t256 * t145 * t147 - 0.256e3 / 0.3e1 * t128 * t141 * t264 * t268 + 0.88e2 / 0.3e1 * t260 * t271 - 0.4096e4 / 0.9e1 * t43 / t486 * t266 * params.E * t31 * s0 / t467 / t129 + 0.2816e4 / 0.9e1 * t265 * t267 * t470 - 0.1232e4 / 0.27e2 * t146 * t44 * t464
  t514 = t287 ** 2
  t524 = t305 * t150
  t531 = t301 * t291
  t579 = t329 * t11
  t587 = 0.15e2 / 0.16e2 * f.p.cam_omega / t62 / t319 * t24 * t67 / t302 / t164 * t524 - 0.9e1 / 0.8e1 * t298 * t173 * t287 * t531 * t303 * t305 * t11 - 0.27e2 / 0.4e1 * t300 * t301 * t291 / t302 / t50 * t524 + 0.27e2 / 0.8e1 * t300 * t531 * t303 * t150 * t274 + t160 * t333 * jnp.pi * t312 * t313 * t329 / 0.3e1 + t311 * t312 * t319 * t305 * t11 / 0.2e1 - t311 * t312 * t165 * t274 * t11 / 0.4e1 + 0.3e1 / 0.2e1 * t162 * t163 * t57 * t303 * t524 - 0.3e1 / 0.2e1 * t162 * t312 * t319 * t150 * t274 + t162 * t163 * t166 * t503 / 0.4e1 - 0.14e2 / 0.27e2 * t64 * t24 / t66 / t129
  t588 = f.my_piecewise3(t72, t587, 0)
  t605 = t284 * t178
  t616 = t206 * t588 / 0.126340300800e12 - t157 * t588 / 0.18e2 + t182 * t588 / 0.240e3 - t186 * t588 / 0.4480e4 + t190 * t588 / 0.103680e6 - t194 * t588 / 0.2838528e7 + t198 * t588 / 0.89456640e8 - t202 * t588 / 0.3185049600e10 - 0.2e1 / 0.3e1 * t182 * t605 + t78 * t178 * t338 / 0.2e1 + t186 * t605 / 0.8e1 - t81 * t178 * t338 / 0.16e2
  t649 = -t190 * t605 / 0.80e2 + 0.3e1 / 0.640e3 * t84 * t178 * t338 + t194 * t605 / 0.1152e4 - t87 * t178 * t338 / 0.3840e4 - t198 * t605 / 0.21504e5 + t90 * t178 * t338 / 0.86016e5 + t202 * t605 / 0.491520e6 - t93 * t178 * t338 / 0.2293760e7 - t206 * t605 / 0.13271040e8 + t96 * t178 * t338 / 0.70778880e8 + 0.1e1 / t95 / t156 * t605 / 0.412876800e9 - t366 * t178 * t338 / 0.2477260800e10
  t651 = f.my_piecewise3(t72, 0, t587)
  t658 = t380 * t210
  t663 = t108 * t372
  t666 = t377 ** 2
  t724 = f.my_piecewise3(t71, t616 + t649, -0.8e1 / 0.3e1 * t651 * t115 - 0.8e1 * t372 * t229 - 0.8e1 * t210 * t415 - 0.8e1 / 0.3e1 * t99 * (0.7e1 / 0.2e1 * t400 * t658 * t108 - 0.3e1 / 0.2e1 * t379 * t210 * t663 - 0.1e1 / t666 * t658 * t108 / 0.4e1 - 0.6e1 * t108 * t392 * t658 + 0.6e1 * t384 * t210 * t372 - t212 * t651 + 0.2e1 * t651 * t112 + 0.6e1 * t372 * t226 + 0.6e1 * t210 * t412 + 0.2e1 * t99 * (0.15e2 / 0.2e1 * t379 * t658 * t108 - 0.6e1 * t392 * t210 * t663 - 0.5e1 / 0.2e1 / t377 / t216 * t658 * t108 + t217 * t651 * t108 / 0.2e1 + 0.3e1 / 0.4e1 * t400 * t372 * t210 * t108 + 0.1e1 / t666 / t99 * t658 * t108 / 0.8e1 - 0.12e2 * t210 * t109 * t372 - 0.3e1 * t106 * t210 * t663 - 0.4e1 * t221 * t651 - t101 * t651 * t108)))
  t730 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t28 * t50 * t121 + t18 * t22 * t150 * t121 / 0.4e1 - t18 * t51 * t234 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t125 * t274 * t121 + 0.3e1 / 0.4e1 * t18 * t151 * t234 + 0.3e1 / 0.8e1 * t18 * t155 * t420 - 0.3e1 / 0.8e1 * t18 * t19 * t503 * t121 + 0.9e1 / 0.8e1 * t18 * t275 * t234 + 0.9e1 / 0.8e1 * t18 * t279 * t420 + 0.3e1 / 0.8e1 * t18 * t283 * f.p.cam_beta * t724)
  v3rho3_0_ = 0.2e1 * r0 * t730 + 0.6e1 * t425

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
  t24 = params.C * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = t26 * t23
  t29 = s0 ** 2
  t30 = params.D * t29
  t31 = t19 ** 2
  t32 = t31 * r0
  t38 = 0.1e1 + t24 * t27 + 0.2e1 * t30 * t25 / t20 / t32
  t41 = params.B * (0.1e1 - 0.1e1 / t38)
  t42 = params.E * s0
  t44 = t42 * t27 + 0.1e1
  t46 = 0.1e1 - 0.1e1 / t44
  t48 = t41 * t46 + params.A
  t49 = t23 * t48
  t50 = t3 ** 2
  t52 = 0.1e1 / jnp.pi
  t53 = t52 ** (0.1e1 / 0.3e1)
  t54 = 0.1e1 / t53
  t55 = 4 ** (0.1e1 / 0.3e1)
  t56 = t54 * t55
  t59 = jnp.pi * t50 * t56 / t48
  t60 = jnp.sqrt(t59)
  t62 = f.p.cam_omega / t60
  t63 = t11 * r0
  t64 = t63 ** (0.1e1 / 0.3e1)
  t65 = 0.1e1 / t64
  t66 = t25 * t65
  t68 = t62 * t66 / 0.2e1
  t69 = 0.135e1 <= t68
  t70 = 0.135e1 < t68
  t71 = f.my_piecewise3(t70, t68, 0.135e1)
  t72 = t71 ** 2
  t75 = t72 ** 2
  t76 = 0.1e1 / t75
  t78 = t75 * t72
  t79 = 0.1e1 / t78
  t81 = t75 ** 2
  t82 = 0.1e1 / t81
  t85 = 0.1e1 / t81 / t72
  t88 = 0.1e1 / t81 / t75
  t91 = 0.1e1 / t81 / t78
  t93 = t81 ** 2
  t94 = 0.1e1 / t93
  t97 = f.my_piecewise3(t70, 0.135e1, t68)
  t98 = jnp.sqrt(jnp.pi)
  t99 = 0.1e1 / t97
  t101 = jnp.erf(t99 / 0.2e1)
  t103 = t97 ** 2
  t104 = 0.1e1 / t103
  t106 = jnp.exp(-t104 / 0.4e1)
  t107 = t106 - 0.1e1
  t110 = t106 - 0.3e1 / 0.2e1 - 0.2e1 * t103 * t107
  t113 = t98 * t101 + 0.2e1 * t97 * t110
  t117 = f.my_piecewise3(t69, 0.1e1 / t72 / 0.36e2 - t76 / 0.960e3 + t79 / 0.26880e5 - t82 / 0.829440e6 + t85 / 0.28385280e8 - t88 / 0.1073479680e10 + t91 / 0.44590694400e11 - t94 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t97 * t113)
  t119 = -f.p.cam_beta * t117 - f.p.cam_alpha + 0.1e1
  t124 = 0.1e1 / t21 / r0
  t125 = t38 ** 2
  t127 = params.B / t125
  t128 = t19 * r0
  t130 = 0.1e1 / t21 / t128
  t131 = t26 * t130
  t134 = t31 * t19
  t140 = -0.8e1 / 0.3e1 * t24 * t131 - 0.32e2 / 0.3e1 * t30 * t25 / t20 / t134
  t141 = t140 * t46
  t143 = t44 ** 2
  t144 = 0.1e1 / t143
  t145 = t41 * t144
  t146 = t42 * t131
  t149 = t127 * t141 - 0.8e1 / 0.3e1 * t145 * t146
  t150 = t124 * t149
  t154 = t124 * t48
  t155 = t72 * t71
  t156 = 0.1e1 / t155
  t159 = f.p.cam_omega / t60 / t59
  t161 = t159 * t66 * jnp.pi
  t162 = t50 * t54
  t163 = t48 ** 2
  t164 = 0.1e1 / t163
  t165 = t55 * t164
  t171 = 0.1e1 / t64 / t63
  t172 = t25 * t171
  t176 = t161 * t162 * t165 * t149 / 0.4e1 - t62 * t172 * t11 / 0.6e1
  t177 = f.my_piecewise3(t70, t176, 0)
  t180 = t75 * t71
  t181 = 0.1e1 / t180
  t184 = t75 * t155
  t185 = 0.1e1 / t184
  t189 = 0.1e1 / t81 / t71
  t193 = 0.1e1 / t81 / t155
  t197 = 0.1e1 / t81 / t180
  t201 = 0.1e1 / t81 / t184
  t205 = 0.1e1 / t93 / t71
  t209 = f.my_piecewise3(t70, 0, t176)
  t211 = t106 * t104
  t215 = t103 * t97
  t216 = 0.1e1 / t215
  t220 = t97 * t107
  t225 = t216 * t209 * t106 / 0.2e1 - 0.4e1 * t220 * t209 - t99 * t209 * t106
  t228 = 0.2e1 * t209 * t110 - t211 * t209 + 0.2e1 * t97 * t225
  t232 = f.my_piecewise3(t69, -t156 * t177 / 0.18e2 + t181 * t177 / 0.240e3 - t185 * t177 / 0.4480e4 + t189 * t177 / 0.103680e6 - t193 * t177 / 0.2838528e7 + t197 * t177 / 0.89456640e8 - t201 * t177 / 0.3185049600e10 + t205 * t177 / 0.126340300800e12, -0.8e1 / 0.3e1 * t209 * t113 - 0.8e1 / 0.3e1 * t97 * t228)
  t233 = f.p.cam_beta * t232
  t237 = 0.1e1 / t21
  t240 = params.B / t125 / t38
  t241 = t140 ** 2
  t242 = t241 * t46
  t247 = t26 / t21 / t31
  t253 = t25 / t20 / t31 / t128
  t256 = 0.88e2 / 0.9e1 * t24 * t247 + 0.608e3 / 0.9e1 * t30 * t253
  t259 = t140 * t144
  t260 = t127 * t259
  t264 = 0.1e1 / t143 / t44
  t265 = t41 * t264
  t266 = params.E ** 2
  t267 = t266 * t29
  t268 = t267 * t253
  t271 = t42 * t247
  t274 = -0.2e1 * t240 * t242 + t127 * t256 * t46 - 0.16e2 / 0.3e1 * t260 * t146 - 0.256e3 / 0.9e1 * t265 * t268 + 0.88e2 / 0.9e1 * t145 * t271
  t275 = t237 * t274
  t279 = t237 * t149
  t283 = t237 * t48
  t284 = t177 ** 2
  t287 = jnp.pi ** 2
  t289 = t53 ** 2
  t290 = 0.1e1 / t289
  t291 = t55 ** 2
  t292 = t290 * t291
  t298 = f.p.cam_omega / t60 / t287 / t3 / t292 / t164 / 0.3e1
  t300 = t298 * t66 * t287
  t301 = t3 * t290
  t302 = t163 ** 2
  t303 = 0.1e1 / t302
  t304 = t291 * t303
  t305 = t149 ** 2
  t311 = t159 * t172 * jnp.pi
  t312 = t162 * t55
  t313 = t164 * t149
  t318 = t163 * t48
  t319 = 0.1e1 / t318
  t320 = t55 * t319
  t329 = t11 ** 2
  t333 = t25 / t64 / t329 / t19
  t337 = 0.9e1 / 0.8e1 * t300 * t301 * t304 * t305 - t311 * t312 * t313 * t11 / 0.6e1 - t161 * t162 * t320 * t305 / 0.2e1 + t161 * t162 * t165 * t274 / 0.4e1 + 0.2e1 / 0.9e1 * t62 * t333 * t329
  t338 = f.my_piecewise3(t70, t337, 0)
  t366 = 0.1e1 / t93 / t72
  t371 = t76 * t284 / 0.6e1 - t156 * t338 / 0.18e2 - t79 * t284 / 0.48e2 + t181 * t338 / 0.240e3 + t82 * t284 / 0.640e3 - t185 * t338 / 0.4480e4 - t85 * t284 / 0.11520e5 + t189 * t338 / 0.103680e6 + t88 * t284 / 0.258048e6 - t193 * t338 / 0.2838528e7 - t91 * t284 / 0.6881280e7 + t197 * t338 / 0.89456640e8 + t94 * t284 / 0.212336640e9 - t201 * t338 / 0.3185049600e10 - t366 * t284 / 0.7431782400e10 + t205 * t338 / 0.126340300800e12
  t372 = f.my_piecewise3(t70, 0, t337)
  t377 = t103 ** 2
  t379 = 0.1e1 / t377 / t97
  t380 = t209 ** 2
  t381 = t379 * t380
  t384 = t106 * t216
  t392 = 0.1e1 / t377
  t400 = 0.1e1 / t377 / t103
  t401 = t400 * t380
  t412 = -0.2e1 * t392 * t380 * t106 + t216 * t372 * t106 / 0.2e1 + t401 * t106 / 0.4e1 - 0.4e1 * t380 * t107 - t104 * t380 * t106 - 0.4e1 * t220 * t372 - t99 * t372 * t106
  t415 = -t381 * t106 / 0.2e1 + 0.2e1 * t384 * t380 - t211 * t372 + 0.2e1 * t372 * t110 + 0.4e1 * t209 * t225 + 0.2e1 * t97 * t412
  t419 = f.my_piecewise3(t69, t371, -0.8e1 / 0.3e1 * t372 * t113 - 0.16e2 / 0.3e1 * t209 * t228 - 0.8e1 / 0.3e1 * t97 * t415)
  t420 = f.p.cam_beta * t419
  t424 = t125 ** 2
  t426 = params.B / t424
  t427 = t241 * t140
  t435 = t240 * t241 * t144
  t440 = t26 / t21 / t32
  t443 = t31 ** 2
  t446 = t25 / t20 / t443
  t449 = -0.1232e4 / 0.27e2 * t24 * t440 - 0.13376e5 / 0.27e2 * t30 * t446
  t453 = t127 * t256 * t144
  t457 = t127 * t140 * t264
  t462 = t143 ** 2
  t463 = 0.1e1 / t462
  t464 = t41 * t463
  t465 = t266 * params.E
  t466 = t29 * s0
  t467 = t465 * t466
  t469 = 0.1e1 / t443 / t128
  t473 = t267 * t446
  t476 = t42 * t440
  t479 = 0.6e1 * t426 * t427 * t46 - 0.6e1 * t240 * t141 * t256 + 0.16e2 * t435 * t146 + t127 * t449 * t46 - 0.8e1 * t453 * t146 - 0.256e3 / 0.3e1 * t457 * t268 + 0.88e2 / 0.3e1 * t260 * t271 - 0.4096e4 / 0.9e1 * t464 * t467 * t469 + 0.2816e4 / 0.9e1 * t265 * t473 - 0.1232e4 / 0.27e2 * t145 * t476
  t480 = t20 * t479
  t484 = t20 * t274
  t488 = t20 * t149
  t492 = t20 * t48
  t493 = t287 ** 2
  t498 = f.p.cam_omega / t60 / t493 / t319 / 0.36e2
  t499 = t498 * t25
  t500 = t65 * t493
  t502 = 0.1e1 / t302 / t163
  t503 = t305 * t149
  t509 = t298 * t172 * t287
  t510 = t301 * t291
  t511 = t303 * t305
  t517 = 0.1e1 / t302 / t48
  t523 = t303 * t149
  t529 = t159 * t333 * jnp.pi
  t534 = t319 * t305
  t539 = t164 * t274
  t549 = t319 * t149
  t558 = t329 * t11
  t562 = t25 / t64 / t558 / t128
  t566 = 0.135e3 / 0.4e1 * t499 * t500 * t502 * t503 - 0.9e1 / 0.8e1 * t509 * t510 * t511 * t11 - 0.27e2 / 0.4e1 * t300 * t301 * t291 * t517 * t503 + 0.27e2 / 0.8e1 * t300 * t510 * t523 * t274 + t529 * t312 * t313 * t329 / 0.3e1 + t311 * t312 * t534 * t11 / 0.2e1 - t311 * t312 * t539 * t11 / 0.4e1 + 0.3e1 / 0.2e1 * t161 * t162 * t55 * t303 * t503 - 0.3e1 / 0.2e1 * t161 * t312 * t549 * t274 + t161 * t162 * t165 * t479 / 0.4e1 - 0.14e2 / 0.27e2 * t62 * t562 * t558
  t567 = f.my_piecewise3(t70, t566, 0)
  t584 = t284 * t177
  t595 = -t156 * t567 / 0.18e2 + t181 * t567 / 0.240e3 - t185 * t567 / 0.4480e4 + t189 * t567 / 0.103680e6 - t193 * t567 / 0.2838528e7 + t197 * t567 / 0.89456640e8 - t201 * t567 / 0.3185049600e10 + t205 * t567 / 0.126340300800e12 - 0.2e1 / 0.3e1 * t181 * t584 + t76 * t177 * t338 / 0.2e1 + t185 * t584 / 0.8e1 - t79 * t177 * t338 / 0.16e2
  t622 = 0.1e1 / t93 / t155
  t628 = -t189 * t584 / 0.80e2 + 0.3e1 / 0.640e3 * t82 * t177 * t338 + t193 * t584 / 0.1152e4 - t85 * t177 * t338 / 0.3840e4 - t197 * t584 / 0.21504e5 + t88 * t177 * t338 / 0.86016e5 + t201 * t584 / 0.491520e6 - t91 * t177 * t338 / 0.2293760e7 - t205 * t584 / 0.13271040e8 + t94 * t177 * t338 / 0.70778880e8 + t622 * t584 / 0.412876800e9 - t366 * t177 * t338 / 0.2477260800e10
  t630 = f.my_piecewise3(t70, 0, t566)
  t637 = t380 * t209
  t641 = t379 * t209
  t642 = t106 * t372
  t645 = t377 ** 2
  t646 = 0.1e1 / t645
  t650 = t106 * t392
  t666 = t392 * t209
  t670 = 0.1e1 / t377 / t215
  t678 = t209 * t106
  t682 = 0.1e1 / t645 / t97
  t686 = t209 * t107
  t689 = t104 * t209
  t696 = 0.15e2 / 0.2e1 * t379 * t637 * t106 - 0.6e1 * t666 * t642 - 0.5e1 / 0.2e1 * t670 * t637 * t106 + t216 * t630 * t106 / 0.2e1 + 0.3e1 / 0.4e1 * t400 * t372 * t678 + t682 * t637 * t106 / 0.8e1 - 0.12e2 * t686 * t372 - 0.3e1 * t689 * t642 - 0.4e1 * t220 * t630 - t99 * t630 * t106
  t699 = 0.7e1 / 0.2e1 * t400 * t637 * t106 - 0.3e1 / 0.2e1 * t641 * t642 - t646 * t637 * t106 / 0.4e1 - 0.6e1 * t650 * t637 + 0.6e1 * t384 * t209 * t372 - t211 * t630 + 0.2e1 * t630 * t110 + 0.6e1 * t372 * t225 + 0.6e1 * t209 * t412 + 0.2e1 * t97 * t696
  t703 = f.my_piecewise3(t69, t595 + t628, -0.8e1 / 0.3e1 * t630 * t113 - 0.8e1 * t372 * t228 - 0.8e1 * t209 * t415 - 0.8e1 / 0.3e1 * t97 * t699)
  t704 = f.p.cam_beta * t703
  t709 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t49 * t119 + t18 * t150 * t119 / 0.4e1 - t18 * t154 * t233 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t275 * t119 + 0.3e1 / 0.4e1 * t18 * t279 * t233 + 0.3e1 / 0.8e1 * t18 * t283 * t420 - 0.3e1 / 0.8e1 * t18 * t480 * t119 + 0.9e1 / 0.8e1 * t18 * t484 * t233 + 0.9e1 / 0.8e1 * t18 * t488 * t420 + 0.3e1 / 0.8e1 * t18 * t492 * t704)
  t763 = t338 ** 2
  t772 = t284 ** 2
  t781 = -t205 * t284 * t338 / 0.2211840e7 - t85 * t567 * t177 / 0.2880e4 - t91 * t567 * t177 / 0.1720320e7 - t366 * t567 * t177 / 0.1857945600e10 + t88 * t567 * t177 / 0.64512e5 + t82 * t567 * t177 / 0.160e3 + t622 * t284 * t338 / 0.68812800e8 - t197 * t284 * t338 / 0.3584e4 - t79 * t567 * t177 / 0.12e2 + t193 * t284 * t338 / 0.192e3 + 0.2e1 / 0.3e1 * t76 * t567 * t177 + 0.3e1 / 0.4e1 * t185 * t284 * t338 - 0.4e1 * t181 * t284 * t338 + t94 * t567 * t177 / 0.53084160e8 + t88 * t763 / 0.86016e5 - t79 * t763 / 0.16e2 - t91 * t763 / 0.2293760e7 - 0.19e2 / 0.412876800e9 / t93 / t75 * t772 + t201 * t284 * t338 / 0.81920e5 - 0.3e1 / 0.40e2 * t189 * t284 * t338
  t792 = t305 ** 2
  t804 = t241 ** 2
  t811 = t256 ** 2
  t820 = t26 / t21 / t134
  t826 = t25 / t20 / t443 / r0
  t875 = t266 ** 2
  t876 = t29 ** 2
  t891 = -0.24e2 * params.B / t424 / t38 * t804 * t46 + 0.36e2 * t426 * t242 * t256 - 0.6e1 * t240 * t811 * t46 - 0.8e1 * t240 * t141 * t449 + t127 * (0.20944e5 / 0.81e2 * t24 * t820 + 0.334400e6 / 0.81e2 * t30 * t826) * t46 + 0.1024e4 / 0.3e1 * t240 * t241 * t264 * t268 - 0.32e2 / 0.3e1 * t127 * t449 * t144 * t146 - 0.512e3 / 0.3e1 * t127 * t256 * t264 * t268 - 0.64e2 * t426 * t427 * t144 * t146 + 0.11264e5 / 0.9e1 * t457 * t473 - 0.4928e4 / 0.27e2 * t260 * t476 + 0.64e2 * t240 * t259 * t42 * t131 * t256 - 0.352e3 / 0.3e1 * t435 * t271 + 0.176e3 / 0.3e1 * t453 * t271 - 0.16384e5 / 0.9e1 * t127 * t140 * t463 * t465 * t466 * t469 + 0.90112e5 / 0.9e1 * t464 * t467 / t443 / t31 - 0.131072e6 / 0.27e2 * t41 / t462 / t44 * t875 * t876 / t21 / t443 / t134 * t26 - 0.250624e6 / 0.81e2 * t265 * t267 * t826 + 0.20944e5 / 0.81e2 * t145 * t42 * t820
  t909 = t302 ** 2
  t915 = t329 ** 2
  t923 = t274 ** 2
  t942 = 0.2e1 / 0.3e1 * t529 * t312 * t539 * t329 - t311 * t312 * t164 * t479 * t11 / 0.3e1 - 0.6e1 * t161 * t162 * t55 * t517 * t792 + 0.9e1 * t161 * t312 * t511 * t274 + t161 * t162 * t165 * t891 / 0.4e1 + 0.105e3 / 0.32e2 * f.p.cam_omega / t60 / t50 * t53 * t52 / t55 / t303 * t66 * jnp.pi / t909 * t792 * t312 + 0.140e3 / 0.81e2 * t62 * t25 / t64 / t31 - 0.3e1 / 0.2e1 * t161 * t162 * t320 * t923 - 0.2e1 * t161 * t312 * t549 * t479 + 0.81e2 / 0.2e1 * t300 * t301 * t291 * t502 * t792 - 0.81e2 / 0.2e1 * t300 * t510 * t517 * t305 * t274
  t972 = t149 * t11 * t274
  t996 = t493 * t502
  t1012 = 0.27e2 / 0.8e1 * t300 * t301 * t304 * t923 + 0.9e1 / 0.2e1 * t300 * t510 * t523 * t479 - 0.28e2 / 0.27e2 * t159 * t562 * jnp.pi * t312 * t313 * t558 - 0.4e1 / 0.3e1 * t529 * t312 * t534 * t329 - 0.2e1 * t311 * t312 * t303 * t503 * t11 + 0.2e1 * t159 * t25 * t171 * jnp.pi * t50 * t56 * t319 * t972 + 0.3e1 * t298 * t333 * t287 * t510 * t511 * t329 + 0.9e1 * t509 * t510 * t517 * t503 * t11 - 0.9e1 / 0.2e1 * t298 * t25 * t171 * t287 * t3 * t292 * t303 * t972 - 0.45e2 * t498 * t172 * t996 * t503 * t11 - 0.405e3 * t499 * t500 / t302 / t318 * t792 + 0.405e3 / 0.2e1 * t498 * t66 * t996 * t305 * t274
  t1013 = t942 + t1012
  t1014 = f.my_piecewise3(t70, t1013, 0)
  t1055 = -t201 * t1014 / 0.3185049600e10 + 0.3e1 / 0.640e3 * t82 * t763 + t189 * t1014 / 0.103680e6 + 0.9e1 / 0.80e2 * t85 * t772 - 0.11e2 / 0.1152e4 * t88 * t772 - t156 * t1014 / 0.18e2 - t193 * t1014 / 0.2838528e7 + t94 * t763 / 0.70778880e8 - t366 * t763 / 0.2477260800e10 + t197 * t1014 / 0.89456640e8 - t85 * t763 / 0.3840e4 + t181 * t1014 / 0.240e3 + 0.10e2 / 0.3e1 * t79 * t772 - t94 * t772 / 0.32768e5 + t76 * t763 / 0.2e1 + t205 * t1014 / 0.126340300800e12 + 0.13e2 / 0.21504e5 * t91 * t772 - t185 * t1014 / 0.4480e4 - 0.7e1 / 0.8e1 * t82 * t772 + 0.17e2 / 0.13271040e8 * t366 * t772
  t1057 = f.my_piecewise3(t70, 0, t1013)
  t1066 = t380 ** 2
  t1081 = t372 ** 2
  t1085 = t106 * t630
  t1161 = -0.12e2 * t1081 * t107 - 0.16e2 * t686 * t630 - 0.4e1 * t220 * t1057 - t99 * t1057 * t106 + 0.85e2 / 0.4e1 * t646 * t1066 * t106 - 0.19e2 / 0.8e1 / t645 / t103 * t1066 * t106 + t216 * t1057 * t106 / 0.2e1 + 0.1e1 / t645 / t377 * t1066 * t106 / 0.16e2 - 0.75e2 / 0.2e1 * t400 * t1066 * t106 + 0.45e2 * t381 * t642 - 0.6e1 * t392 * t1081 * t106 - 0.8e1 * t666 * t1085 - 0.15e2 * t670 * t380 * t642 + t400 * t630 * t678 + 0.3e1 / 0.4e1 * t400 * t1081 * t106 + 0.3e1 / 0.4e1 * t682 * t372 * t380 * t106 - 0.3e1 * t104 * t1081 * t106 - 0.4e1 * t689 * t1085
  t1164 = 0.15e2 / 0.4e1 * t682 * t1066 * t106 - 0.1e1 / t645 / t215 * t1066 * t106 / 0.8e1 - t211 * t1057 - 0.24e2 * t670 * t1066 * t106 + 0.21e2 * t401 * t642 - 0.3e1 / 0.2e1 * t379 * t1081 * t106 - 0.2e1 * t641 * t1085 - 0.3e1 / 0.2e1 * t646 * t380 * t642 + 0.24e2 * t106 * t379 * t1066 - 0.36e2 * t650 * t380 * t372 + 0.6e1 * t384 * t1081 + 0.8e1 * t384 * t209 * t630 + 0.2e1 * t1057 * t110 + 0.8e1 * t630 * t225 + 0.12e2 * t372 * t412 + 0.8e1 * t209 * t696 + 0.2e1 * t97 * t1161
  t1168 = f.my_piecewise3(t69, t781 + t1055, -0.8e1 / 0.3e1 * t1057 * t113 - 0.32e2 / 0.3e1 * t630 * t228 - 0.16e2 * t372 * t415 - 0.32e2 / 0.3e1 * t209 * t699 - 0.8e1 / 0.3e1 * t97 * t1164)
  t1209 = -0.5e1 / 0.9e1 * t18 * t23 * t149 * t119 + 0.9e1 / 0.4e1 * t18 * t484 * t420 + 0.3e1 / 0.2e1 * t18 * t488 * t704 + 0.3e1 / 0.8e1 * t18 * t492 * f.p.cam_beta * t1168 + t18 * t124 * t274 * t119 / 0.2e1 - t18 * t237 * t479 * t119 / 0.2e1 - 0.3e1 / 0.8e1 * t18 * t20 * t891 * t119 + t18 * t283 * t704 / 0.2e1 + 0.3e1 / 0.2e1 * t18 * t480 * t233 + 0.10e2 / 0.27e2 * t18 * t130 * t48 * t119 + 0.5e1 / 0.9e1 * t18 * t49 * t233 - t18 * t150 * t233 - t18 * t154 * t420 / 0.2e1 + 0.3e1 / 0.2e1 * t18 * t275 * t233 + 0.3e1 / 0.2e1 * t18 * t279 * t420
  t1210 = f.my_piecewise3(t2, 0, t1209)
  v4rho4_0_ = 0.2e1 * r0 * t1210 + 0.8e1 * t709

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
  t30 = t5 * t29
  t31 = t6 ** (0.1e1 / 0.3e1)
  t32 = params.C * s0
  t33 = r0 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / t33
  t39 = s0 ** 2
  t40 = params.D * t39
  t41 = t33 ** 2
  t46 = 0.1e1 + t32 * t37 + t40 / t34 / t41 / r0
  t49 = params.B * (0.1e1 - 0.1e1 / t46)
  t50 = params.E * s0
  t52 = t50 * t37 + 0.1e1
  t54 = 0.1e1 - 0.1e1 / t52
  t56 = t49 * t54 + params.A
  t57 = t31 * t56
  t58 = t2 ** 2
  t59 = jnp.pi * t58
  t61 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t62 = 0.1e1 / t61
  t63 = 4 ** (0.1e1 / 0.3e1)
  t64 = t62 * t63
  t67 = t59 * t64 / t56
  t68 = jnp.sqrt(t67)
  t70 = f.p.cam_omega / t68
  t71 = 2 ** (0.1e1 / 0.3e1)
  t72 = t19 * t6
  t73 = t72 ** (0.1e1 / 0.3e1)
  t75 = t71 / t73
  t77 = t70 * t75 / 0.2e1
  t78 = 0.135e1 <= t77
  t79 = 0.135e1 < t77
  t80 = f.my_piecewise3(t79, t77, 0.135e1)
  t81 = t80 ** 2
  t84 = t81 ** 2
  t85 = 0.1e1 / t84
  t87 = t84 * t81
  t88 = 0.1e1 / t87
  t90 = t84 ** 2
  t91 = 0.1e1 / t90
  t94 = 0.1e1 / t90 / t81
  t97 = 0.1e1 / t90 / t84
  t100 = 0.1e1 / t90 / t87
  t102 = t90 ** 2
  t103 = 0.1e1 / t102
  t106 = f.my_piecewise3(t79, 0.135e1, t77)
  t107 = jnp.sqrt(jnp.pi)
  t108 = 0.1e1 / t106
  t110 = jax.lax.erf(t108 / 0.2e1)
  t112 = t106 ** 2
  t113 = 0.1e1 / t112
  t115 = jnp.exp(-t113 / 0.4e1)
  t116 = t115 - 0.1e1
  t119 = t115 - 0.3e1 / 0.2e1 - 0.2e1 * t112 * t116
  t122 = 0.2e1 * t106 * t119 + t107 * t110
  t126 = f.my_piecewise3(t78, 0.1e1 / t81 / 0.36e2 - t85 / 0.960e3 + t88 / 0.26880e5 - t91 / 0.829440e6 + t94 / 0.28385280e8 - t97 / 0.1073479680e10 + t100 / 0.44590694400e11 - t103 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t106 * t122)
  t128 = -f.p.cam_beta * t126 - f.p.cam_alpha + 0.1e1
  t129 = t57 * t128
  t132 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t133 = t132 * f.p.zeta_threshold
  t135 = f.my_piecewise3(t20, t133, t21 * t19)
  t136 = t5 * t135
  t137 = t31 ** 2
  t138 = 0.1e1 / t137
  t139 = t138 * t56
  t140 = t139 * t128
  t142 = t136 * t140 / 0.8e1
  t143 = t46 ** 2
  t145 = params.B / t143
  t146 = t33 * r0
  t148 = 0.1e1 / t35 / t146
  t156 = -0.8e1 / 0.3e1 * t32 * t148 - 0.16e2 / 0.3e1 * t40 / t34 / t41 / t33
  t159 = t52 ** 2
  t160 = 0.1e1 / t159
  t161 = t49 * t160
  t165 = t145 * t156 * t54 - 0.8e1 / 0.3e1 * t161 * t50 * t148
  t166 = t31 * t165
  t167 = t166 * t128
  t170 = t81 * t80
  t171 = 0.1e1 / t170
  t174 = f.p.cam_omega / t68 / t67
  t176 = t174 * t75 * jnp.pi
  t177 = t58 * t62
  t178 = t56 ** 2
  t179 = 0.1e1 / t178
  t180 = t63 * t179
  t181 = t180 * t165
  t187 = t71 / t73 / t72
  t189 = t26 * t6 + t18 + 0.1e1
  t193 = t176 * t177 * t181 / 0.4e1 - t70 * t187 * t189 / 0.6e1
  t194 = f.my_piecewise3(t79, t193, 0)
  t197 = t84 * t80
  t198 = 0.1e1 / t197
  t201 = t84 * t170
  t202 = 0.1e1 / t201
  t206 = 0.1e1 / t90 / t80
  t210 = 0.1e1 / t90 / t170
  t214 = 0.1e1 / t90 / t197
  t218 = 0.1e1 / t90 / t201
  t222 = 0.1e1 / t102 / t80
  t226 = f.my_piecewise3(t79, 0, t193)
  t228 = t115 * t113
  t233 = 0.1e1 / t112 / t106
  t237 = t106 * t116
  t242 = t233 * t226 * t115 / 0.2e1 - 0.4e1 * t237 * t226 - t108 * t226 * t115
  t245 = 0.2e1 * t106 * t242 + 0.2e1 * t226 * t119 - t228 * t226
  t249 = f.my_piecewise3(t78, -t171 * t194 / 0.18e2 + t198 * t194 / 0.240e3 - t202 * t194 / 0.4480e4 + t206 * t194 / 0.103680e6 - t210 * t194 / 0.2838528e7 + t214 * t194 / 0.89456640e8 - t218 * t194 / 0.3185049600e10 + t222 * t194 / 0.126340300800e12, -0.8e1 / 0.3e1 * t106 * t245 - 0.8e1 / 0.3e1 * t226 * t122)
  t250 = f.p.cam_beta * t249
  t251 = t57 * t250
  t255 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t129 - t142 - 0.3e1 / 0.8e1 * t136 * t167 + 0.3e1 / 0.8e1 * t136 * t251)
  t257 = r1 <= f.p.dens_threshold
  t258 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t259 = 0.1e1 + t258
  t260 = t259 <= f.p.zeta_threshold
  t261 = t259 ** (0.1e1 / 0.3e1)
  t263 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t266 = f.my_piecewise3(t260, 0, 0.4e1 / 0.3e1 * t261 * t263)
  t267 = t5 * t266
  t268 = params.C * s2
  t269 = r1 ** 2
  t270 = r1 ** (0.1e1 / 0.3e1)
  t271 = t270 ** 2
  t273 = 0.1e1 / t271 / t269
  t275 = s2 ** 2
  t276 = params.D * t275
  t277 = t269 ** 2
  t282 = 0.1e1 + t268 * t273 + t276 / t270 / t277 / r1
  t285 = params.B * (0.1e1 - 0.1e1 / t282)
  t286 = params.E * s2
  t288 = t286 * t273 + 0.1e1
  t290 = 0.1e1 - 0.1e1 / t288
  t292 = t285 * t290 + params.A
  t293 = t31 * t292
  t296 = t59 * t64 / t292
  t297 = jnp.sqrt(t296)
  t299 = f.p.cam_omega / t297
  t300 = t259 * t6
  t301 = t300 ** (0.1e1 / 0.3e1)
  t303 = t71 / t301
  t305 = t299 * t303 / 0.2e1
  t306 = 0.135e1 <= t305
  t307 = 0.135e1 < t305
  t308 = f.my_piecewise3(t307, t305, 0.135e1)
  t309 = t308 ** 2
  t312 = t309 ** 2
  t313 = 0.1e1 / t312
  t315 = t312 * t309
  t316 = 0.1e1 / t315
  t318 = t312 ** 2
  t319 = 0.1e1 / t318
  t322 = 0.1e1 / t318 / t309
  t325 = 0.1e1 / t318 / t312
  t328 = 0.1e1 / t318 / t315
  t330 = t318 ** 2
  t331 = 0.1e1 / t330
  t334 = f.my_piecewise3(t307, 0.135e1, t305)
  t335 = 0.1e1 / t334
  t337 = jax.lax.erf(t335 / 0.2e1)
  t339 = t334 ** 2
  t340 = 0.1e1 / t339
  t342 = jnp.exp(-t340 / 0.4e1)
  t343 = t342 - 0.1e1
  t346 = t342 - 0.3e1 / 0.2e1 - 0.2e1 * t339 * t343
  t349 = t107 * t337 + 0.2e1 * t334 * t346
  t353 = f.my_piecewise3(t306, 0.1e1 / t309 / 0.36e2 - t313 / 0.960e3 + t316 / 0.26880e5 - t319 / 0.829440e6 + t322 / 0.28385280e8 - t325 / 0.1073479680e10 + t328 / 0.44590694400e11 - t331 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t334 * t349)
  t355 = -f.p.cam_beta * t353 - f.p.cam_alpha + 0.1e1
  t356 = t293 * t355
  t360 = f.my_piecewise3(t260, t133, t261 * t259)
  t361 = t5 * t360
  t362 = t138 * t292
  t363 = t362 * t355
  t365 = t361 * t363 / 0.8e1
  t366 = t309 * t308
  t367 = 0.1e1 / t366
  t370 = t71 / t301 / t300
  t372 = t263 * t6 + t258 + 0.1e1
  t375 = t299 * t370 * t372 / 0.6e1
  t376 = f.my_piecewise3(t307, -t375, 0)
  t379 = t312 * t308
  t380 = 0.1e1 / t379
  t383 = t312 * t366
  t384 = 0.1e1 / t383
  t388 = 0.1e1 / t318 / t308
  t392 = 0.1e1 / t318 / t366
  t396 = 0.1e1 / t318 / t379
  t400 = 0.1e1 / t318 / t383
  t404 = 0.1e1 / t330 / t308
  t408 = f.my_piecewise3(t307, 0, -t375)
  t410 = t342 * t340
  t415 = 0.1e1 / t339 / t334
  t419 = t334 * t343
  t424 = t415 * t408 * t342 / 0.2e1 - 0.4e1 * t419 * t408 - t335 * t408 * t342
  t427 = 0.2e1 * t334 * t424 + 0.2e1 * t408 * t346 - t410 * t408
  t431 = f.my_piecewise3(t306, -t367 * t376 / 0.18e2 + t380 * t376 / 0.240e3 - t384 * t376 / 0.4480e4 + t388 * t376 / 0.103680e6 - t392 * t376 / 0.2838528e7 + t396 * t376 / 0.89456640e8 - t400 * t376 / 0.3185049600e10 + t404 * t376 / 0.126340300800e12, -0.8e1 / 0.3e1 * t334 * t427 - 0.8e1 / 0.3e1 * t408 * t349)
  t432 = f.p.cam_beta * t431
  t433 = t293 * t432
  t437 = f.my_piecewise3(t257, 0, -0.3e1 / 0.8e1 * t267 * t356 - t365 + 0.3e1 / 0.8e1 * t361 * t433)
  t439 = t21 ** 2
  t440 = 0.1e1 / t439
  t441 = t26 ** 2
  t446 = t16 / t22 / t6
  t448 = -0.2e1 * t23 + 0.2e1 * t446
  t449 = f.my_piecewise5(t10, 0, t14, 0, t448)
  t453 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t440 * t441 + 0.4e1 / 0.3e1 * t21 * t449)
  t457 = t30 * t140
  t464 = 0.1e1 / t137 / t6
  t468 = t136 * t464 * t56 * t128 / 0.12e2
  t471 = t136 * t138 * t165 * t128
  t474 = t136 * t139 * t250
  t479 = t156 ** 2
  t484 = 0.1e1 / t35 / t41
  t489 = 0.1e1 / t34 / t41 / t146
  t504 = params.E ** 2
  t512 = -0.2e1 * params.B / t143 / t46 * t479 * t54 + t145 * (0.88e2 / 0.9e1 * t32 * t484 + 0.304e3 / 0.9e1 * t40 * t489) * t54 - 0.16e2 / 0.3e1 * t145 * t156 * t160 * params.E * s0 * t148 - 0.128e3 / 0.9e1 * t49 / t159 / t52 * t504 * t39 * t489 + 0.88e2 / 0.9e1 * t161 * t50 * t484
  t520 = t194 ** 2
  t523 = jnp.pi ** 2
  t524 = t523 * t2
  t525 = t61 ** 2
  t526 = 0.1e1 / t525
  t527 = t63 ** 2
  t528 = t526 * t527
  t537 = t2 * t526
  t538 = t178 ** 2
  t541 = t165 ** 2
  t548 = t177 * t63
  t565 = t19 ** 2
  t568 = 0.1e1 / t73 / t565 / t22
  t569 = t71 * t568
  t570 = t189 ** 2
  t580 = 0.3e1 / 0.8e1 * f.p.cam_omega / t68 / t524 / t528 / t179 * t75 * t523 * t537 * t527 / t538 * t541 - t174 * t187 * jnp.pi * t548 * t179 * t165 * t189 / 0.6e1 - t176 * t177 * t63 / t178 / t56 * t541 / 0.2e1 + t176 * t177 * t180 * t512 / 0.4e1 + 0.2e1 / 0.9e1 * t70 * t569 * t570 - t70 * t187 * (t449 * t6 + 0.2e1 * t26) / 0.6e1
  t581 = f.my_piecewise3(t79, t580, 0)
  t609 = 0.1e1 / t102 / t81
  t614 = t85 * t520 / 0.6e1 - t171 * t581 / 0.18e2 - t88 * t520 / 0.48e2 + t198 * t581 / 0.240e3 + t91 * t520 / 0.640e3 - t202 * t581 / 0.4480e4 - t94 * t520 / 0.11520e5 + t206 * t581 / 0.103680e6 + t97 * t520 / 0.258048e6 - t210 * t581 / 0.2838528e7 - t100 * t520 / 0.6881280e7 + t214 * t581 / 0.89456640e8 + t103 * t520 / 0.212336640e9 - t218 * t581 / 0.3185049600e10 - t609 * t520 / 0.7431782400e10 + t222 * t581 / 0.126340300800e12
  t615 = f.my_piecewise3(t79, 0, t580)
  t620 = t112 ** 2
  t622 = 0.1e1 / t620 / t106
  t623 = t226 ** 2
  t627 = t115 * t233
  t635 = 0.1e1 / t620
  t643 = 0.1e1 / t620 / t112
  t662 = f.my_piecewise3(t78, t614, -0.8e1 / 0.3e1 * t615 * t122 - 0.16e2 / 0.3e1 * t226 * t245 - 0.8e1 / 0.3e1 * t106 * (-t622 * t623 * t115 / 0.2e1 + 0.2e1 * t627 * t623 - t228 * t615 + 0.2e1 * t615 * t119 + 0.4e1 * t226 * t242 + 0.2e1 * t106 * (-0.2e1 * t635 * t623 * t115 + t233 * t615 * t115 / 0.2e1 + t643 * t623 * t115 / 0.4e1 - 0.4e1 * t623 * t116 - t113 * t623 * t115 - 0.4e1 * t237 * t615 - t108 * t615 * t115)))
  t668 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t453 * t129 - t457 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t167 + 0.3e1 / 0.4e1 * t30 * t251 + t468 - t471 / 0.4e1 + t474 / 0.4e1 - 0.3e1 / 0.8e1 * t136 * t31 * t512 * t128 + 0.3e1 / 0.4e1 * t136 * t166 * t250 + 0.3e1 / 0.8e1 * t136 * t57 * f.p.cam_beta * t662)
  t669 = t261 ** 2
  t670 = 0.1e1 / t669
  t671 = t263 ** 2
  t675 = f.my_piecewise5(t14, 0, t10, 0, -t448)
  t679 = f.my_piecewise3(t260, 0, 0.4e1 / 0.9e1 * t670 * t671 + 0.4e1 / 0.3e1 * t261 * t675)
  t683 = t267 * t363
  t690 = t361 * t464 * t292 * t355 / 0.12e2
  t692 = t361 * t362 * t432
  t694 = t376 ** 2
  t697 = t259 ** 2
  t700 = 0.1e1 / t301 / t697 / t22
  t701 = t71 * t700
  t702 = t372 ** 2
  t712 = 0.2e1 / 0.9e1 * t299 * t701 * t702 - t299 * t370 * (t675 * t6 + 0.2e1 * t263) / 0.6e1
  t713 = f.my_piecewise3(t307, t712, 0)
  t741 = 0.1e1 / t330 / t309
  t746 = t313 * t694 / 0.6e1 - t367 * t713 / 0.18e2 - t316 * t694 / 0.48e2 + t380 * t713 / 0.240e3 + t319 * t694 / 0.640e3 - t384 * t713 / 0.4480e4 - t322 * t694 / 0.11520e5 + t388 * t713 / 0.103680e6 + t325 * t694 / 0.258048e6 - t392 * t713 / 0.2838528e7 - t328 * t694 / 0.6881280e7 + t396 * t713 / 0.89456640e8 + t331 * t694 / 0.212336640e9 - t400 * t713 / 0.3185049600e10 - t741 * t694 / 0.7431782400e10 + t404 * t713 / 0.126340300800e12
  t747 = f.my_piecewise3(t307, 0, t712)
  t752 = t339 ** 2
  t754 = 0.1e1 / t752 / t334
  t755 = t408 ** 2
  t759 = t342 * t415
  t767 = 0.1e1 / t752
  t775 = 0.1e1 / t752 / t339
  t794 = f.my_piecewise3(t306, t746, -0.8e1 / 0.3e1 * t747 * t349 - 0.16e2 / 0.3e1 * t408 * t427 - 0.8e1 / 0.3e1 * t334 * (-t754 * t755 * t342 / 0.2e1 + 0.2e1 * t759 * t755 - t410 * t747 + 0.2e1 * t747 * t346 + 0.4e1 * t408 * t424 + 0.2e1 * t334 * (-0.2e1 * t767 * t755 * t342 + t415 * t747 * t342 / 0.2e1 + t775 * t755 * t342 / 0.4e1 - 0.4e1 * t755 * t343 - t340 * t755 * t342 - 0.4e1 * t419 * t747 - t335 * t747 * t342)))
  t800 = f.my_piecewise3(t257, 0, -0.3e1 / 0.8e1 * t5 * t679 * t356 - t683 / 0.4e1 + 0.3e1 / 0.4e1 * t267 * t433 + t690 + t692 / 0.4e1 + 0.3e1 / 0.8e1 * t361 * t293 * f.p.cam_beta * t794)
  d11 = 0.2e1 * t255 + 0.2e1 * t437 + t6 * (t668 + t800)
  t803 = -t7 - t24
  t804 = f.my_piecewise5(t10, 0, t14, 0, t803)
  t807 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t804)
  t808 = t5 * t807
  t812 = t804 * t6 + t18 + 0.1e1
  t813 = t187 * t812
  t815 = t70 * t813 / 0.6e1
  t816 = f.my_piecewise3(t79, -t815, 0)
  t834 = f.my_piecewise3(t79, 0, -t815)
  t846 = t233 * t834 * t115 / 0.2e1 - 0.4e1 * t237 * t834 - t108 * t834 * t115
  t849 = 0.2e1 * t106 * t846 + 0.2e1 * t834 * t119 - t228 * t834
  t853 = f.my_piecewise3(t78, -t171 * t816 / 0.18e2 + t198 * t816 / 0.240e3 - t202 * t816 / 0.4480e4 + t206 * t816 / 0.103680e6 - t210 * t816 / 0.2838528e7 + t214 * t816 / 0.89456640e8 - t218 * t816 / 0.3185049600e10 + t222 * t816 / 0.126340300800e12, -0.8e1 / 0.3e1 * t106 * t849 - 0.8e1 / 0.3e1 * t834 * t122)
  t854 = f.p.cam_beta * t853
  t855 = t57 * t854
  t859 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t808 * t129 - t142 + 0.3e1 / 0.8e1 * t136 * t855)
  t861 = f.my_piecewise5(t14, 0, t10, 0, -t803)
  t864 = f.my_piecewise3(t260, 0, 0.4e1 / 0.3e1 * t261 * t861)
  t865 = t5 * t864
  t868 = t282 ** 2
  t870 = params.B / t868
  t871 = t269 * r1
  t873 = 0.1e1 / t271 / t871
  t881 = -0.8e1 / 0.3e1 * t268 * t873 - 0.16e2 / 0.3e1 * t276 / t270 / t277 / t269
  t884 = t288 ** 2
  t885 = 0.1e1 / t884
  t886 = t285 * t885
  t890 = t870 * t881 * t290 - 0.8e1 / 0.3e1 * t886 * t286 * t873
  t891 = t31 * t890
  t892 = t891 * t355
  t897 = f.p.cam_omega / t297 / t296
  t899 = t897 * t303 * jnp.pi
  t900 = t292 ** 2
  t901 = 0.1e1 / t900
  t902 = t63 * t901
  t908 = t861 * t6 + t258 + 0.1e1
  t912 = t899 * t177 * t902 * t890 / 0.4e1 - t299 * t370 * t908 / 0.6e1
  t913 = f.my_piecewise3(t307, t912, 0)
  t931 = f.my_piecewise3(t307, 0, t912)
  t943 = t415 * t931 * t342 / 0.2e1 - 0.4e1 * t419 * t931 - t335 * t931 * t342
  t946 = 0.2e1 * t334 * t943 + 0.2e1 * t931 * t346 - t410 * t931
  t950 = f.my_piecewise3(t306, -t367 * t913 / 0.18e2 + t380 * t913 / 0.240e3 - t384 * t913 / 0.4480e4 + t388 * t913 / 0.103680e6 - t392 * t913 / 0.2838528e7 + t396 * t913 / 0.89456640e8 - t400 * t913 / 0.3185049600e10 + t404 * t913 / 0.126340300800e12, -0.8e1 / 0.3e1 * t334 * t946 - 0.8e1 / 0.3e1 * t931 * t349)
  t951 = f.p.cam_beta * t950
  t952 = t293 * t951
  t956 = f.my_piecewise3(t257, 0, -0.3e1 / 0.8e1 * t865 * t356 - t365 - 0.3e1 / 0.8e1 * t361 * t892 + 0.3e1 / 0.8e1 * t361 * t952)
  t960 = 0.2e1 * t446
  t961 = f.my_piecewise5(t10, 0, t14, 0, t960)
  t965 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t440 * t804 * t26 + 0.4e1 / 0.3e1 * t21 * t961)
  t969 = t808 * t140
  t981 = t136 * t139 * t854
  t1004 = -t174 * t813 * t59 * t62 * t181 / 0.12e2 + 0.2e1 / 0.9e1 * t70 * t71 * t568 * t812 * t189 - t70 * t187 * (t961 * t6 + t26 + t804) / 0.6e1
  t1005 = f.my_piecewise3(t79, t1004, 0)
  t1043 = t85 * t816 * t194 / 0.6e1 - t171 * t1005 / 0.18e2 - t88 * t816 * t194 / 0.48e2 + t198 * t1005 / 0.240e3 + t91 * t816 * t194 / 0.640e3 - t202 * t1005 / 0.4480e4 - t94 * t816 * t194 / 0.11520e5 + t206 * t1005 / 0.103680e6 + t97 * t816 * t194 / 0.258048e6 - t210 * t1005 / 0.2838528e7 - t100 * t816 * t194 / 0.6881280e7 + t214 * t1005 / 0.89456640e8 + t103 * t816 * t194 / 0.212336640e9 - t218 * t1005 / 0.3185049600e10 - t609 * t816 * t194 / 0.7431782400e10 + t222 * t1005 / 0.126340300800e12
  t1044 = f.my_piecewise3(t79, 0, t1004)
  t1049 = t115 * t834
  t1063 = t115 * t226
  t1088 = f.my_piecewise3(t78, t1043, -0.8e1 / 0.3e1 * t1044 * t122 - 0.8e1 / 0.3e1 * t834 * t245 - 0.8e1 / 0.3e1 * t226 * t849 - 0.8e1 / 0.3e1 * t106 * (-t622 * t226 * t1049 / 0.2e1 + 0.2e1 * t627 * t834 * t226 - t228 * t1044 + 0.2e1 * t1044 * t119 + 0.2e1 * t834 * t242 + 0.2e1 * t226 * t846 + 0.2e1 * t106 * (-0.2e1 * t635 * t834 * t1063 + t233 * t1044 * t115 / 0.2e1 + t643 * t834 * t1063 / 0.4e1 - 0.4e1 * t226 * t116 * t834 - t113 * t226 * t1049 - 0.4e1 * t237 * t1044 - t108 * t1044 * t115)))
  t1093 = -0.3e1 / 0.8e1 * t5 * t965 * t129 - t969 / 0.8e1 - 0.3e1 / 0.8e1 * t808 * t167 + 0.3e1 / 0.8e1 * t808 * t251 - t457 / 0.8e1 + t468 - t471 / 0.8e1 + t474 / 0.8e1 + 0.3e1 / 0.8e1 * t30 * t855 + t981 / 0.8e1 + 0.3e1 / 0.8e1 * t136 * t166 * t854 + 0.3e1 / 0.8e1 * t136 * t57 * f.p.cam_beta * t1088
  t1094 = f.my_piecewise3(t1, 0, t1093)
  t1098 = f.my_piecewise5(t14, 0, t10, 0, -t960)
  t1102 = f.my_piecewise3(t260, 0, 0.4e1 / 0.9e1 * t670 * t861 * t263 + 0.4e1 / 0.3e1 * t261 * t1098)
  t1106 = t865 * t363
  t1116 = t361 * t138 * t890 * t355
  t1124 = t361 * t362 * t951
  t1130 = t897 * t370 * jnp.pi
  t1131 = t901 * t890
  t1146 = -t1130 * t548 * t1131 * t372 / 0.12e2 + 0.2e1 / 0.9e1 * t299 * t71 * t700 * t908 * t372 - t299 * t370 * (t1098 * t6 + t263 + t861) / 0.6e1
  t1147 = f.my_piecewise3(t307, t1146, 0)
  t1185 = t313 * t913 * t376 / 0.6e1 - t367 * t1147 / 0.18e2 - t316 * t913 * t376 / 0.48e2 + t380 * t1147 / 0.240e3 + t319 * t913 * t376 / 0.640e3 - t384 * t1147 / 0.4480e4 - t322 * t913 * t376 / 0.11520e5 + t388 * t1147 / 0.103680e6 + t325 * t913 * t376 / 0.258048e6 - t392 * t1147 / 0.2838528e7 - t328 * t913 * t376 / 0.6881280e7 + t396 * t1147 / 0.89456640e8 + t331 * t913 * t376 / 0.212336640e9 - t400 * t1147 / 0.3185049600e10 - t741 * t913 * t376 / 0.7431782400e10 + t404 * t1147 / 0.126340300800e12
  t1186 = f.my_piecewise3(t307, 0, t1146)
  t1191 = t342 * t931
  t1205 = t342 * t408
  t1230 = f.my_piecewise3(t306, t1185, -0.8e1 / 0.3e1 * t1186 * t349 - 0.8e1 / 0.3e1 * t931 * t427 - 0.8e1 / 0.3e1 * t408 * t946 - 0.8e1 / 0.3e1 * t334 * (-t754 * t408 * t1191 / 0.2e1 + 0.2e1 * t759 * t931 * t408 - t410 * t1186 + 0.2e1 * t1186 * t346 + 0.2e1 * t931 * t424 + 0.2e1 * t408 * t943 + 0.2e1 * t334 * (-0.2e1 * t767 * t931 * t1205 + t415 * t1186 * t342 / 0.2e1 + t775 * t931 * t1205 / 0.4e1 - 0.4e1 * t408 * t343 * t931 - t340 * t408 * t1191 - 0.4e1 * t419 * t1186 - t335 * t1186 * t342)))
  t1235 = -0.3e1 / 0.8e1 * t5 * t1102 * t356 - t1106 / 0.8e1 + 0.3e1 / 0.8e1 * t865 * t433 - t683 / 0.8e1 + t690 + t692 / 0.8e1 - 0.3e1 / 0.8e1 * t267 * t892 - t1116 / 0.8e1 + 0.3e1 / 0.8e1 * t361 * t891 * t432 + 0.3e1 / 0.8e1 * t267 * t952 + t1124 / 0.8e1 + 0.3e1 / 0.8e1 * t361 * t293 * f.p.cam_beta * t1230
  t1236 = f.my_piecewise3(t257, 0, t1235)
  d12 = t255 + t437 + t859 + t956 + t6 * (t1094 + t1236)
  t1241 = t804 ** 2
  t1245 = 0.2e1 * t23 + 0.2e1 * t446
  t1246 = f.my_piecewise5(t10, 0, t14, 0, t1245)
  t1250 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t440 * t1241 + 0.4e1 / 0.3e1 * t21 * t1246)
  t1258 = t816 ** 2
  t1261 = t812 ** 2
  t1271 = 0.2e1 / 0.9e1 * t70 * t569 * t1261 - t70 * t187 * (t1246 * t6 + 0.2e1 * t804) / 0.6e1
  t1272 = f.my_piecewise3(t79, t1271, 0)
  t1303 = t85 * t1258 / 0.6e1 - t171 * t1272 / 0.18e2 - t88 * t1258 / 0.48e2 + t198 * t1272 / 0.240e3 + t91 * t1258 / 0.640e3 - t202 * t1272 / 0.4480e4 - t94 * t1258 / 0.11520e5 + t206 * t1272 / 0.103680e6 + t97 * t1258 / 0.258048e6 - t210 * t1272 / 0.2838528e7 - t100 * t1258 / 0.6881280e7 + t214 * t1272 / 0.89456640e8 + t103 * t1258 / 0.212336640e9 - t218 * t1272 / 0.3185049600e10 - t609 * t1258 / 0.7431782400e10 + t222 * t1272 / 0.126340300800e12
  t1304 = f.my_piecewise3(t79, 0, t1271)
  t1309 = t834 ** 2
  t1344 = f.my_piecewise3(t78, t1303, -0.8e1 / 0.3e1 * t1304 * t122 - 0.16e2 / 0.3e1 * t834 * t849 - 0.8e1 / 0.3e1 * t106 * (-t622 * t1309 * t115 / 0.2e1 + 0.2e1 * t627 * t1309 - t228 * t1304 + 0.2e1 * t1304 * t119 + 0.4e1 * t834 * t846 + 0.2e1 * t106 * (-0.2e1 * t635 * t1309 * t115 + t233 * t1304 * t115 / 0.2e1 + t643 * t1309 * t115 / 0.4e1 - 0.4e1 * t1309 * t116 - t113 * t1309 * t115 - 0.4e1 * t237 * t1304 - t108 * t1304 * t115)))
  t1350 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t1250 * t129 - t969 / 0.4e1 + 0.3e1 / 0.4e1 * t808 * t855 + t468 + t981 / 0.4e1 + 0.3e1 / 0.8e1 * t136 * t57 * f.p.cam_beta * t1344)
  t1351 = t861 ** 2
  t1355 = f.my_piecewise5(t14, 0, t10, 0, -t1245)
  t1359 = f.my_piecewise3(t260, 0, 0.4e1 / 0.9e1 * t670 * t1351 + 0.4e1 / 0.3e1 * t261 * t1355)
  t1373 = t881 ** 2
  t1378 = 0.1e1 / t271 / t277
  t1383 = 0.1e1 / t270 / t277 / t871
  t1405 = -0.2e1 * params.B / t868 / t282 * t1373 * t290 + t870 * (0.88e2 / 0.9e1 * t268 * t1378 + 0.304e3 / 0.9e1 * t276 * t1383) * t290 - 0.16e2 / 0.3e1 * t870 * t881 * t885 * params.E * s2 * t873 - 0.128e3 / 0.9e1 * t285 / t884 / t288 * t504 * t275 * t1383 + 0.88e2 / 0.9e1 * t886 * t286 * t1378
  t1413 = t913 ** 2
  t1424 = t900 ** 2
  t1427 = t890 ** 2
  t1447 = t908 ** 2
  t1457 = 0.3e1 / 0.8e1 * f.p.cam_omega / t297 / t524 / t528 / t901 * t303 * t523 * t537 * t527 / t1424 * t1427 - t1130 * t548 * t1131 * t908 / 0.6e1 - t899 * t177 * t63 / t900 / t292 * t1427 / 0.2e1 + t899 * t177 * t902 * t1405 / 0.4e1 + 0.2e1 / 0.9e1 * t299 * t701 * t1447 - t299 * t370 * (t1355 * t6 + 0.2e1 * t861) / 0.6e1
  t1458 = f.my_piecewise3(t307, t1457, 0)
  t1489 = t313 * t1413 / 0.6e1 - t367 * t1458 / 0.18e2 - t316 * t1413 / 0.48e2 + t380 * t1458 / 0.240e3 + t319 * t1413 / 0.640e3 - t384 * t1458 / 0.4480e4 - t322 * t1413 / 0.11520e5 + t388 * t1458 / 0.103680e6 + t325 * t1413 / 0.258048e6 - t392 * t1458 / 0.2838528e7 - t328 * t1413 / 0.6881280e7 + t396 * t1458 / 0.89456640e8 + t331 * t1413 / 0.212336640e9 - t400 * t1458 / 0.3185049600e10 - t741 * t1413 / 0.7431782400e10 + t404 * t1458 / 0.126340300800e12
  t1490 = f.my_piecewise3(t307, 0, t1457)
  t1495 = t931 ** 2
  t1530 = f.my_piecewise3(t306, t1489, -0.8e1 / 0.3e1 * t1490 * t349 - 0.16e2 / 0.3e1 * t931 * t946 - 0.8e1 / 0.3e1 * t334 * (-t754 * t1495 * t342 / 0.2e1 + 0.2e1 * t759 * t1495 - t410 * t1490 + 0.2e1 * t1490 * t346 + 0.4e1 * t931 * t943 + 0.2e1 * t334 * (-0.2e1 * t767 * t1495 * t342 + t415 * t1490 * t342 / 0.2e1 + t775 * t1495 * t342 / 0.4e1 - 0.4e1 * t1495 * t343 - t340 * t1495 * t342 - 0.4e1 * t419 * t1490 - t335 * t1490 * t342)))
  t1536 = f.my_piecewise3(t257, 0, -0.3e1 / 0.8e1 * t5 * t1359 * t356 - t1106 / 0.4e1 - 0.3e1 / 0.4e1 * t865 * t892 + 0.3e1 / 0.4e1 * t865 * t952 + t690 - t1116 / 0.4e1 + t1124 / 0.4e1 - 0.3e1 / 0.8e1 * t361 * t31 * t1405 * t355 + 0.3e1 / 0.4e1 * t361 * t891 * t951 + 0.3e1 / 0.8e1 * t361 * t293 * f.p.cam_beta * t1530)
  d22 = 0.2e1 * t859 + 0.2e1 * t956 + t6 * (t1350 + t1536)
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
  t32 = t24 * t6
  t33 = 0.1e1 / t32
  t36 = 0.2e1 * t16 * t33 - 0.2e1 * t25
  t37 = f.my_piecewise5(t10, 0, t14, 0, t36)
  t41 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t23 * t29 + 0.4e1 / 0.3e1 * t21 * t37)
  t42 = t5 * t41
  t43 = t6 ** (0.1e1 / 0.3e1)
  t44 = params.C * s0
  t45 = r0 ** 2
  t46 = r0 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t49 = 0.1e1 / t47 / t45
  t51 = s0 ** 2
  t52 = params.D * t51
  t53 = t45 ** 2
  t54 = t53 * r0
  t58 = 0.1e1 + t44 * t49 + t52 / t46 / t54
  t61 = params.B * (0.1e1 - 0.1e1 / t58)
  t62 = params.E * s0
  t64 = t62 * t49 + 0.1e1
  t66 = 0.1e1 - 0.1e1 / t64
  t68 = t61 * t66 + params.A
  t69 = t43 * t68
  t70 = t2 ** 2
  t71 = jnp.pi * t70
  t73 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t74 = 0.1e1 / t73
  t75 = 4 ** (0.1e1 / 0.3e1)
  t76 = t74 * t75
  t79 = t71 * t76 / t68
  t80 = jnp.sqrt(t79)
  t82 = f.p.cam_omega / t80
  t83 = 2 ** (0.1e1 / 0.3e1)
  t84 = t19 * t6
  t85 = t84 ** (0.1e1 / 0.3e1)
  t86 = 0.1e1 / t85
  t87 = t83 * t86
  t89 = t82 * t87 / 0.2e1
  t90 = 0.135e1 <= t89
  t91 = 0.135e1 < t89
  t92 = f.my_piecewise3(t91, t89, 0.135e1)
  t93 = t92 ** 2
  t96 = t93 ** 2
  t97 = 0.1e1 / t96
  t99 = t96 * t93
  t100 = 0.1e1 / t99
  t102 = t96 ** 2
  t103 = 0.1e1 / t102
  t106 = 0.1e1 / t102 / t93
  t109 = 0.1e1 / t102 / t96
  t112 = 0.1e1 / t102 / t99
  t114 = t102 ** 2
  t115 = 0.1e1 / t114
  t118 = f.my_piecewise3(t91, 0.135e1, t89)
  t119 = jnp.sqrt(jnp.pi)
  t120 = 0.1e1 / t118
  t122 = jnp.erf(t120 / 0.2e1)
  t124 = t118 ** 2
  t125 = 0.1e1 / t124
  t127 = jnp.exp(-t125 / 0.4e1)
  t128 = t127 - 0.1e1
  t131 = t127 - 0.3e1 / 0.2e1 - 0.2e1 * t124 * t128
  t134 = 0.2e1 * t118 * t131 + t119 * t122
  t138 = f.my_piecewise3(t90, 0.1e1 / t93 / 0.36e2 - t97 / 0.960e3 + t100 / 0.26880e5 - t103 / 0.829440e6 + t106 / 0.28385280e8 - t109 / 0.1073479680e10 + t112 / 0.44590694400e11 - t115 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t118 * t134)
  t140 = -f.p.cam_beta * t138 - f.p.cam_alpha + 0.1e1
  t141 = t69 * t140
  t146 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t147 = t5 * t146
  t148 = t43 ** 2
  t149 = 0.1e1 / t148
  t150 = t149 * t68
  t151 = t150 * t140
  t154 = t58 ** 2
  t156 = params.B / t154
  t157 = t45 * r0
  t159 = 0.1e1 / t47 / t157
  t167 = -0.8e1 / 0.3e1 * t44 * t159 - 0.16e2 / 0.3e1 * t52 / t46 / t53 / t45
  t168 = t167 * t66
  t170 = t64 ** 2
  t171 = 0.1e1 / t170
  t172 = t61 * t171
  t176 = t156 * t168 - 0.8e1 / 0.3e1 * t172 * t62 * t159
  t177 = t43 * t176
  t178 = t177 * t140
  t181 = t93 * t92
  t182 = 0.1e1 / t181
  t185 = f.p.cam_omega / t80 / t79
  t187 = t185 * t87 * jnp.pi
  t188 = t70 * t74
  t189 = t68 ** 2
  t190 = 0.1e1 / t189
  t191 = t75 * t190
  t198 = t83 / t85 / t84
  t200 = t28 * t6 + t18 + 0.1e1
  t204 = t187 * t188 * t191 * t176 / 0.4e1 - t82 * t198 * t200 / 0.6e1
  t205 = f.my_piecewise3(t91, t204, 0)
  t208 = t96 * t92
  t209 = 0.1e1 / t208
  t212 = t96 * t181
  t213 = 0.1e1 / t212
  t217 = 0.1e1 / t102 / t92
  t221 = 0.1e1 / t102 / t181
  t225 = 0.1e1 / t102 / t208
  t229 = 0.1e1 / t102 / t212
  t233 = 0.1e1 / t114 / t92
  t237 = f.my_piecewise3(t91, 0, t204)
  t239 = t127 * t125
  t243 = t124 * t118
  t244 = 0.1e1 / t243
  t248 = t118 * t128
  t253 = t244 * t237 * t127 / 0.2e1 - 0.4e1 * t248 * t237 - t120 * t237 * t127
  t256 = 0.2e1 * t118 * t253 + 0.2e1 * t237 * t131 - t239 * t237
  t260 = f.my_piecewise3(t90, -t182 * t205 / 0.18e2 + t209 * t205 / 0.240e3 - t213 * t205 / 0.4480e4 + t217 * t205 / 0.103680e6 - t221 * t205 / 0.2838528e7 + t225 * t205 / 0.89456640e8 - t229 * t205 / 0.3185049600e10 + t233 * t205 / 0.126340300800e12, -0.8e1 / 0.3e1 * t118 * t256 - 0.8e1 / 0.3e1 * t237 * t134)
  t261 = f.p.cam_beta * t260
  t262 = t69 * t261
  t265 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t266 = t265 * f.p.zeta_threshold
  t268 = f.my_piecewise3(t20, t266, t21 * t19)
  t269 = t5 * t268
  t271 = 0.1e1 / t148 / t6
  t272 = t271 * t68
  t273 = t272 * t140
  t276 = t149 * t176
  t277 = t276 * t140
  t280 = t150 * t261
  t285 = params.B / t154 / t58
  t286 = t167 ** 2
  t291 = 0.1e1 / t47 / t53
  t296 = 0.1e1 / t46 / t53 / t157
  t299 = 0.88e2 / 0.9e1 * t44 * t291 + 0.304e3 / 0.9e1 * t52 * t296
  t302 = t156 * t167
  t303 = t171 * params.E
  t305 = t303 * s0 * t159
  t309 = 0.1e1 / t170 / t64
  t310 = t61 * t309
  t311 = params.E ** 2
  t312 = t311 * t51
  t319 = -0.2e1 * t285 * t286 * t66 + t156 * t299 * t66 - 0.16e2 / 0.3e1 * t302 * t305 - 0.128e3 / 0.9e1 * t310 * t312 * t296 + 0.88e2 / 0.9e1 * t172 * t62 * t291
  t320 = t43 * t319
  t321 = t320 * t140
  t324 = t177 * t261
  t327 = t205 ** 2
  t330 = jnp.pi ** 2
  t332 = t73 ** 2
  t333 = 0.1e1 / t332
  t334 = t75 ** 2
  t341 = f.p.cam_omega / t80 / t330 / t2 / t333 / t334 / t190 / 0.3e1
  t343 = t341 * t87 * t330
  t344 = t2 * t333
  t345 = t189 ** 2
  t346 = 0.1e1 / t345
  t348 = t176 ** 2
  t354 = t185 * t198 * jnp.pi
  t355 = t188 * t75
  t356 = t190 * t176
  t362 = 0.1e1 / t189 / t68
  t372 = t19 ** 2
  t375 = 0.1e1 / t85 / t372 / t24
  t376 = t83 * t375
  t377 = t200 ** 2
  t383 = t37 * t6 + 0.2e1 * t28
  t387 = 0.9e1 / 0.8e1 * t343 * t344 * t334 * t346 * t348 - t354 * t355 * t356 * t200 / 0.6e1 - t187 * t188 * t75 * t362 * t348 / 0.2e1 + t187 * t188 * t191 * t319 / 0.4e1 + 0.2e1 / 0.9e1 * t82 * t376 * t377 - t82 * t198 * t383 / 0.6e1
  t388 = f.my_piecewise3(t91, t387, 0)
  t416 = 0.1e1 / t114 / t93
  t421 = t97 * t327 / 0.6e1 - t182 * t388 / 0.18e2 - t100 * t327 / 0.48e2 + t209 * t388 / 0.240e3 + t103 * t327 / 0.640e3 - t213 * t388 / 0.4480e4 - t106 * t327 / 0.11520e5 + t217 * t388 / 0.103680e6 + t109 * t327 / 0.258048e6 - t221 * t388 / 0.2838528e7 - t112 * t327 / 0.6881280e7 + t225 * t388 / 0.89456640e8 + t115 * t327 / 0.212336640e9 - t229 * t388 / 0.3185049600e10 - t416 * t327 / 0.7431782400e10 + t233 * t388 / 0.126340300800e12
  t422 = f.my_piecewise3(t91, 0, t387)
  t427 = t124 ** 2
  t429 = 0.1e1 / t427 / t118
  t430 = t237 ** 2
  t434 = t127 * t244
  t442 = 0.1e1 / t427
  t450 = 0.1e1 / t427 / t124
  t462 = -0.2e1 * t442 * t430 * t127 + t244 * t422 * t127 / 0.2e1 + t450 * t430 * t127 / 0.4e1 - 0.4e1 * t430 * t128 - t125 * t430 * t127 - 0.4e1 * t248 * t422 - t120 * t422 * t127
  t465 = -t429 * t430 * t127 / 0.2e1 + 0.2e1 * t434 * t430 - t239 * t422 + 0.2e1 * t422 * t131 + 0.4e1 * t237 * t253 + 0.2e1 * t118 * t462
  t469 = f.my_piecewise3(t90, t421, -0.8e1 / 0.3e1 * t422 * t134 - 0.16e2 / 0.3e1 * t237 * t256 - 0.8e1 / 0.3e1 * t118 * t465)
  t470 = f.p.cam_beta * t469
  t471 = t69 * t470
  t475 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t42 * t141 - t147 * t151 / 0.4e1 - 0.3e1 / 0.4e1 * t147 * t178 + 0.3e1 / 0.4e1 * t147 * t262 + t269 * t273 / 0.12e2 - t269 * t277 / 0.4e1 + t269 * t280 / 0.4e1 - 0.3e1 / 0.8e1 * t269 * t321 + 0.3e1 / 0.4e1 * t269 * t324 + 0.3e1 / 0.8e1 * t269 * t471)
  t477 = r1 <= f.p.dens_threshold
  t478 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t479 = 0.1e1 + t478
  t480 = t479 <= f.p.zeta_threshold
  t481 = t479 ** (0.1e1 / 0.3e1)
  t482 = t481 ** 2
  t483 = 0.1e1 / t482
  t485 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t486 = t485 ** 2
  t490 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t494 = f.my_piecewise3(t480, 0, 0.4e1 / 0.9e1 * t483 * t486 + 0.4e1 / 0.3e1 * t481 * t490)
  t495 = t5 * t494
  t497 = r1 ** 2
  t498 = r1 ** (0.1e1 / 0.3e1)
  t499 = t498 ** 2
  t501 = 0.1e1 / t499 / t497
  t503 = s2 ** 2
  t505 = t497 ** 2
  t520 = params.A + params.B * (0.1e1 - 0.1e1 / (0.1e1 + params.C * s2 * t501 + params.D * t503 / t498 / t505 / r1)) * (0.1e1 - 0.1e1 / (params.E * s2 * t501 + 0.1e1))
  t521 = t43 * t520
  t525 = jnp.sqrt(t71 * t76 / t520)
  t527 = f.p.cam_omega / t525
  t528 = t479 * t6
  t529 = t528 ** (0.1e1 / 0.3e1)
  t533 = t527 * t83 / t529 / 0.2e1
  t534 = 0.135e1 <= t533
  t535 = 0.135e1 < t533
  t536 = f.my_piecewise3(t535, t533, 0.135e1)
  t537 = t536 ** 2
  t540 = t537 ** 2
  t541 = 0.1e1 / t540
  t543 = t540 * t537
  t544 = 0.1e1 / t543
  t546 = t540 ** 2
  t547 = 0.1e1 / t546
  t550 = 0.1e1 / t546 / t537
  t553 = 0.1e1 / t546 / t540
  t556 = 0.1e1 / t546 / t543
  t558 = t546 ** 2
  t559 = 0.1e1 / t558
  t562 = f.my_piecewise3(t535, 0.135e1, t533)
  t563 = 0.1e1 / t562
  t565 = jnp.erf(t563 / 0.2e1)
  t567 = t562 ** 2
  t568 = 0.1e1 / t567
  t570 = jnp.exp(-t568 / 0.4e1)
  t571 = t570 - 0.1e1
  t574 = t570 - 0.3e1 / 0.2e1 - 0.2e1 * t567 * t571
  t577 = t119 * t565 + 0.2e1 * t562 * t574
  t581 = f.my_piecewise3(t534, 0.1e1 / t537 / 0.36e2 - t541 / 0.960e3 + t544 / 0.26880e5 - t547 / 0.829440e6 + t550 / 0.28385280e8 - t553 / 0.1073479680e10 + t556 / 0.44590694400e11 - t559 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t562 * t577)
  t583 = -f.p.cam_beta * t581 - f.p.cam_alpha + 0.1e1
  t584 = t521 * t583
  t589 = f.my_piecewise3(t480, 0, 0.4e1 / 0.3e1 * t481 * t485)
  t590 = t5 * t589
  t591 = t149 * t520
  t592 = t591 * t583
  t595 = t537 * t536
  t596 = 0.1e1 / t595
  t599 = t83 / t529 / t528
  t601 = t485 * t6 + t478 + 0.1e1
  t604 = t527 * t599 * t601 / 0.6e1
  t605 = f.my_piecewise3(t535, -t604, 0)
  t608 = t540 * t536
  t609 = 0.1e1 / t608
  t612 = t540 * t595
  t613 = 0.1e1 / t612
  t617 = 0.1e1 / t546 / t536
  t621 = 0.1e1 / t546 / t595
  t625 = 0.1e1 / t546 / t608
  t629 = 0.1e1 / t546 / t612
  t633 = 0.1e1 / t558 / t536
  t637 = f.my_piecewise3(t535, 0, -t604)
  t639 = t570 * t568
  t643 = t567 * t562
  t644 = 0.1e1 / t643
  t648 = t562 * t571
  t653 = t644 * t637 * t570 / 0.2e1 - 0.4e1 * t648 * t637 - t563 * t637 * t570
  t656 = 0.2e1 * t562 * t653 + 0.2e1 * t637 * t574 - t639 * t637
  t660 = f.my_piecewise3(t534, -t596 * t605 / 0.18e2 + t609 * t605 / 0.240e3 - t613 * t605 / 0.4480e4 + t617 * t605 / 0.103680e6 - t621 * t605 / 0.2838528e7 + t625 * t605 / 0.89456640e8 - t629 * t605 / 0.3185049600e10 + t633 * t605 / 0.126340300800e12, -0.8e1 / 0.3e1 * t562 * t656 - 0.8e1 / 0.3e1 * t637 * t577)
  t661 = f.p.cam_beta * t660
  t662 = t521 * t661
  t666 = f.my_piecewise3(t480, t266, t481 * t479)
  t667 = t5 * t666
  t668 = t271 * t520
  t669 = t668 * t583
  t672 = t591 * t661
  t675 = t605 ** 2
  t678 = t479 ** 2
  t681 = 0.1e1 / t529 / t678 / t24
  t683 = t601 ** 2
  t689 = t490 * t6 + 0.2e1 * t485
  t693 = 0.2e1 / 0.9e1 * t527 * t83 * t681 * t683 - t527 * t599 * t689 / 0.6e1
  t694 = f.my_piecewise3(t535, t693, 0)
  t722 = 0.1e1 / t558 / t537
  t727 = t541 * t675 / 0.6e1 - t596 * t694 / 0.18e2 - t544 * t675 / 0.48e2 + t609 * t694 / 0.240e3 + t547 * t675 / 0.640e3 - t613 * t694 / 0.4480e4 - t550 * t675 / 0.11520e5 + t617 * t694 / 0.103680e6 + t553 * t675 / 0.258048e6 - t621 * t694 / 0.2838528e7 - t556 * t675 / 0.6881280e7 + t625 * t694 / 0.89456640e8 + t559 * t675 / 0.212336640e9 - t629 * t694 / 0.3185049600e10 - t722 * t675 / 0.7431782400e10 + t633 * t694 / 0.126340300800e12
  t728 = f.my_piecewise3(t535, 0, t693)
  t733 = t567 ** 2
  t735 = 0.1e1 / t733 / t562
  t736 = t637 ** 2
  t740 = t570 * t644
  t748 = 0.1e1 / t733
  t756 = 0.1e1 / t733 / t567
  t768 = -0.2e1 * t748 * t736 * t570 + t644 * t728 * t570 / 0.2e1 + t756 * t736 * t570 / 0.4e1 - 0.4e1 * t736 * t571 - t568 * t736 * t570 - 0.4e1 * t648 * t728 - t563 * t728 * t570
  t771 = -t735 * t736 * t570 / 0.2e1 + 0.2e1 * t740 * t736 - t639 * t728 + 0.2e1 * t728 * t574 + 0.4e1 * t637 * t653 + 0.2e1 * t562 * t768
  t775 = f.my_piecewise3(t534, t727, -0.8e1 / 0.3e1 * t728 * t577 - 0.16e2 / 0.3e1 * t637 * t656 - 0.8e1 / 0.3e1 * t562 * t771)
  t776 = f.p.cam_beta * t775
  t777 = t521 * t776
  t781 = f.my_piecewise3(t477, 0, -0.3e1 / 0.8e1 * t495 * t584 - t590 * t592 / 0.4e1 + 0.3e1 / 0.4e1 * t590 * t662 + t667 * t669 / 0.12e2 + t667 * t672 / 0.4e1 + 0.3e1 / 0.8e1 * t667 * t777)
  t791 = t24 ** 2
  t795 = 0.6e1 * t33 - 0.6e1 * t16 / t791
  t796 = f.my_piecewise5(t10, 0, t14, 0, t795)
  t800 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t796)
  t818 = t154 ** 2
  t832 = 0.1e1 / t47 / t54
  t835 = t53 ** 2
  t837 = 0.1e1 / t46 / t835
  t855 = t170 ** 2
  t872 = 0.6e1 * params.B / t818 * t286 * t167 * t66 - 0.6e1 * t285 * t168 * t299 + 0.16e2 * t285 * t286 * t305 + t156 * (-0.1232e4 / 0.27e2 * t44 * t832 - 0.6688e4 / 0.27e2 * t52 * t837) * t66 - 0.8e1 * t156 * t299 * t305 - 0.128e3 / 0.3e1 * t302 * t309 * t311 * t51 * t296 + 0.88e2 / 0.3e1 * t302 * t303 * s0 * t291 - 0.1024e4 / 0.9e1 * t61 / t855 * t311 * params.E * t51 * s0 / t835 / t157 + 0.1408e4 / 0.9e1 * t310 * t312 * t837 - 0.1232e4 / 0.27e2 * t172 * t62 * t832
  t883 = t330 ** 2
  t893 = t348 * t176
  t900 = t344 * t334
  t972 = 0.15e2 / 0.16e2 * f.p.cam_omega / t80 / t362 * t83 * t86 / t345 / t189 * t893 - 0.9e1 / 0.8e1 * t341 * t198 * t330 * t900 * t346 * t348 * t200 - 0.27e2 / 0.4e1 * t343 * t344 * t334 / t345 / t68 * t893 + 0.27e2 / 0.8e1 * t343 * t900 * t346 * t176 * t319 + t185 * t376 * jnp.pi * t355 * t356 * t377 / 0.3e1 + t354 * t355 * t362 * t348 * t200 / 0.2e1 - t354 * t355 * t190 * t319 * t200 / 0.4e1 - t354 * t355 * t356 * t383 / 0.4e1 + 0.3e1 / 0.2e1 * t187 * t188 * t75 * t346 * t893 - 0.3e1 / 0.2e1 * t187 * t355 * t362 * t176 * t319 + t187 * t188 * t191 * t872 / 0.4e1 - 0.14e2 / 0.27e2 * t82 * t83 / t85 / t372 / t19 / t32 * t377 * t200 + 0.2e1 / 0.3e1 * t82 * t83 * t375 * t200 * t383 - t82 * t198 * (t796 * t6 + 0.3e1 * t37) / 0.6e1
  t973 = f.my_piecewise3(t91, t972, 0)
  t990 = t327 * t205
  t1001 = -t182 * t973 / 0.18e2 + t209 * t973 / 0.240e3 - t213 * t973 / 0.4480e4 + t217 * t973 / 0.103680e6 - t221 * t973 / 0.2838528e7 + t225 * t973 / 0.89456640e8 - t229 * t973 / 0.3185049600e10 + t233 * t973 / 0.126340300800e12 - 0.2e1 / 0.3e1 * t209 * t990 + t97 * t205 * t388 / 0.2e1 + t213 * t990 / 0.8e1 - t100 * t205 * t388 / 0.16e2
  t1034 = -t217 * t990 / 0.80e2 + 0.3e1 / 0.640e3 * t103 * t205 * t388 + t221 * t990 / 0.1152e4 - t106 * t205 * t388 / 0.3840e4 - t225 * t990 / 0.21504e5 + t109 * t205 * t388 / 0.86016e5 + t229 * t990 / 0.491520e6 - t112 * t205 * t388 / 0.2293760e7 - t233 * t990 / 0.13271040e8 + t115 * t205 * t388 / 0.70778880e8 + 0.1e1 / t114 / t181 * t990 / 0.412876800e9 - t416 * t205 * t388 / 0.2477260800e10
  t1036 = f.my_piecewise3(t91, 0, t972)
  t1043 = t430 * t237
  t1048 = t127 * t422
  t1051 = t427 ** 2
  t1109 = f.my_piecewise3(t90, t1001 + t1034, -0.8e1 / 0.3e1 * t1036 * t134 - 0.8e1 * t422 * t256 - 0.8e1 * t237 * t465 - 0.8e1 / 0.3e1 * t118 * (0.7e1 / 0.2e1 * t450 * t1043 * t127 - 0.3e1 / 0.2e1 * t429 * t237 * t1048 - 0.1e1 / t1051 * t1043 * t127 / 0.4e1 - 0.6e1 * t127 * t442 * t1043 + 0.6e1 * t434 * t237 * t422 - t239 * t1036 + 0.2e1 * t1036 * t131 + 0.6e1 * t422 * t253 + 0.6e1 * t237 * t462 + 0.2e1 * t118 * (0.15e2 / 0.2e1 * t429 * t1043 * t127 - 0.6e1 * t442 * t237 * t1048 - 0.5e1 / 0.2e1 / t427 / t243 * t1043 * t127 + t244 * t1036 * t127 / 0.2e1 + 0.3e1 / 0.4e1 * t450 * t422 * t237 * t127 + 0.1e1 / t1051 / t118 * t1043 * t127 / 0.8e1 - 0.12e2 * t237 * t128 * t422 - 0.3e1 * t125 * t237 * t1048 - 0.4e1 * t248 * t1036 - t120 * t1036 * t127)))
  t1115 = 0.1e1 / t148 / t24
  t1141 = -0.3e1 / 0.8e1 * t5 * t800 * t141 - 0.9e1 / 0.8e1 * t42 * t178 - 0.3e1 / 0.4e1 * t147 * t277 - 0.9e1 / 0.8e1 * t147 * t321 + t269 * t271 * t176 * t140 / 0.4e1 - 0.3e1 / 0.8e1 * t269 * t149 * t319 * t140 - 0.3e1 / 0.8e1 * t269 * t43 * t872 * t140 + 0.9e1 / 0.8e1 * t269 * t320 * t261 + 0.9e1 / 0.8e1 * t269 * t177 * t470 + 0.3e1 / 0.8e1 * t269 * t69 * f.p.cam_beta * t1109 - 0.5e1 / 0.36e2 * t269 * t1115 * t68 * t140 - t269 * t272 * t261 / 0.4e1 + 0.3e1 / 0.4e1 * t269 * t276 * t261 + 0.3e1 / 0.8e1 * t269 * t150 * t470 - 0.3e1 / 0.8e1 * t42 * t151 + 0.9e1 / 0.8e1 * t42 * t262 + t147 * t273 / 0.4e1 + 0.3e1 / 0.4e1 * t147 * t280 + 0.9e1 / 0.4e1 * t147 * t324 + 0.9e1 / 0.8e1 * t147 * t471
  t1142 = f.my_piecewise3(t1, 0, t1141)
  t1152 = f.my_piecewise5(t14, 0, t10, 0, -t795)
  t1156 = f.my_piecewise3(t480, 0, -0.8e1 / 0.27e2 / t482 / t479 * t486 * t485 + 0.4e1 / 0.3e1 * t483 * t485 * t490 + 0.4e1 / 0.3e1 * t481 * t1152)
  t1200 = -0.14e2 / 0.27e2 * t527 * t83 / t529 / t678 / t479 / t32 * t683 * t601 + 0.2e1 / 0.3e1 * t527 * t83 * t681 * t601 * t689 - t527 * t599 * (t1152 * t6 + 0.3e1 * t490) / 0.6e1
  t1201 = f.my_piecewise3(t535, t1200, 0)
  t1218 = t675 * t605
  t1229 = t609 * t1201 / 0.240e3 - t613 * t1201 / 0.4480e4 + t617 * t1201 / 0.103680e6 - t621 * t1201 / 0.2838528e7 + t625 * t1201 / 0.89456640e8 - t629 * t1201 / 0.3185049600e10 + t633 * t1201 / 0.126340300800e12 - t596 * t1201 / 0.18e2 - 0.2e1 / 0.3e1 * t609 * t1218 + t541 * t605 * t694 / 0.2e1 + t613 * t1218 / 0.8e1 - t544 * t605 * t694 / 0.16e2
  t1262 = -t617 * t1218 / 0.80e2 + 0.3e1 / 0.640e3 * t547 * t605 * t694 + t621 * t1218 / 0.1152e4 - t550 * t605 * t694 / 0.3840e4 - t625 * t1218 / 0.21504e5 + t553 * t605 * t694 / 0.86016e5 + t629 * t1218 / 0.491520e6 - t556 * t605 * t694 / 0.2293760e7 - t633 * t1218 / 0.13271040e8 + t559 * t605 * t694 / 0.70778880e8 + 0.1e1 / t558 / t595 * t1218 / 0.412876800e9 - t722 * t605 * t694 / 0.2477260800e10
  t1264 = f.my_piecewise3(t535, 0, t1200)
  t1271 = t736 * t637
  t1276 = t570 * t728
  t1279 = t733 ** 2
  t1337 = f.my_piecewise3(t534, t1229 + t1262, -0.8e1 / 0.3e1 * t1264 * t577 - 0.8e1 * t728 * t656 - 0.8e1 * t637 * t771 - 0.8e1 / 0.3e1 * t562 * (0.7e1 / 0.2e1 * t756 * t1271 * t570 - 0.3e1 / 0.2e1 * t735 * t637 * t1276 - 0.1e1 / t1279 * t1271 * t570 / 0.4e1 - 0.6e1 * t570 * t748 * t1271 + 0.6e1 * t740 * t637 * t728 - t639 * t1264 + 0.2e1 * t1264 * t574 + 0.6e1 * t728 * t653 + 0.6e1 * t637 * t768 + 0.2e1 * t562 * (0.15e2 / 0.2e1 * t735 * t1271 * t570 - 0.6e1 * t748 * t637 * t1276 - 0.5e1 / 0.2e1 / t733 / t643 * t1271 * t570 + t644 * t1264 * t570 / 0.2e1 + 0.3e1 / 0.4e1 * t756 * t728 * t637 * t570 + 0.1e1 / t1279 / t562 * t1271 * t570 / 0.8e1 - 0.12e2 * t637 * t571 * t728 - 0.3e1 * t568 * t637 * t1276 - 0.4e1 * t648 * t1264 - t563 * t1264 * t570)))
  t1343 = f.my_piecewise3(t477, 0, -0.3e1 / 0.8e1 * t5 * t1156 * t584 - 0.3e1 / 0.8e1 * t495 * t592 + 0.9e1 / 0.8e1 * t495 * t662 + t590 * t669 / 0.4e1 + 0.3e1 / 0.4e1 * t590 * t672 + 0.9e1 / 0.8e1 * t590 * t777 - 0.5e1 / 0.36e2 * t667 * t1115 * t520 * t583 - t667 * t668 * t661 / 0.4e1 + 0.3e1 / 0.8e1 * t667 * t591 * t776 + 0.3e1 / 0.8e1 * t667 * t521 * f.p.cam_beta * t1337)
  d111 = 0.3e1 * t475 + 0.3e1 * t781 + t6 * (t1142 + t1343)

  res = {'v3rho3': d111}
  return res
