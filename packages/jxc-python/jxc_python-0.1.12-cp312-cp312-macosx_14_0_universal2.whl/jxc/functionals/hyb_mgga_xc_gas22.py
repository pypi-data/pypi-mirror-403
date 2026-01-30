"""Generated from hyb_mgga_xc_gas22.mpl."""

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
  params_c_os_raw = params.c_os
  if isinstance(params_c_os_raw, (str, bytes, dict)):
    params_c_os = params_c_os_raw
  else:
    try:
      params_c_os_seq = list(params_c_os_raw)
    except TypeError:
      params_c_os = params_c_os_raw
    else:
      params_c_os_seq = np.asarray(params_c_os_seq, dtype=np.float64)
      params_c_os = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_os_seq))
  params_c_ss_raw = params.c_ss
  if isinstance(params_c_ss_raw, (str, bytes, dict)):
    params_c_ss = params_c_ss_raw
  else:
    try:
      params_c_ss_seq = list(params_c_ss_raw)
    except TypeError:
      params_c_ss = params_c_ss_raw
    else:
      params_c_ss_seq = np.asarray(params_c_ss_seq, dtype=np.float64)
      params_c_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_ss_seq))
  params_c_x_raw = params.c_x
  if isinstance(params_c_x_raw, (str, bytes, dict)):
    params_c_x = params_c_x_raw
  else:
    try:
      params_c_x_seq = list(params_c_x_raw)
    except TypeError:
      params_c_x = params_c_x_raw
    else:
      params_c_x_seq = np.asarray(params_c_x_seq, dtype=np.float64)
      params_c_x = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_x_seq))

  b97mv_par_n = 5

  b97mv_gamma_x = 0.003840616724010807

  b97mv_par_x = [None, np.array([np.nan, params_c_x[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_x[2], 0, 1], dtype=np.float64), np.array([np.nan, params_c_x[3], 1, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_ss = 0.46914023462026644

  b97mv_par_ss = [None, np.array([np.nan, params_c_ss[1], 0, 1], dtype=np.float64), np.array([np.nan, params_c_ss[2], 1, 0], dtype=np.float64), np.array([np.nan, params_c_ss[3], 2, 0], dtype=np.float64), np.array([np.nan, params_c_ss[4], 0, 6], dtype=np.float64), np.array([np.nan, params_c_ss[5], 4, 6], dtype=np.float64)]

  b97mv_gamma_os = 0.006

  b97mv_par_os = [None, np.array([np.nan, params_c_os[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_os[2], 2, 0], dtype=np.float64), np.array([np.nan, params_c_os[3], 6, 0], dtype=np.float64), np.array([np.nan, params_c_os[4], 6, 2 / 3], dtype=np.float64), np.array([np.nan, params_c_os[5], 2, 2 / 3], dtype=np.float64)]

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  lda_x_ax = -f.RS_FACTOR * X_FACTOR_C / 2 ** (4 / 3)

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  b97mv_ux = lambda mgamma, x: mgamma * x ** 2 / (1 + mgamma * x ** 2)

  b97mv_ux_os = lambda mgamma, x: x

  b97mv_wx_ss = lambda t, dummy=None: (K_FACTOR_C - t) / (K_FACTOR_C + t)

  b97mv_wx_os = lambda ts0, ts1: (K_FACTOR_C * (ts0 + ts1) - 2 * ts0 * ts1) / (K_FACTOR_C * (ts0 + ts1) + 2 * ts0 * ts1)

  b97mv_g = lambda mgamma, wx, ux, cc, n, xs, ts0, ts1: jnp.sum(jnp.array([cc[i][1] * wx(ts0, ts1) ** cc[i][2] * ux(mgamma, xs) ** cc[i][3] for i in range(1, n + 1)]), axis=0)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  b97mv_ux_ss = lambda mgamma, x: b97mv_ux(mgamma, x)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  lda_x_erf_spin = lambda rs, z: lda_x_ax * f.opz_pow_n(z, 4 / 3) / rs * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3))

  b97mv_fpar = lambda rs, z, xs0, xs1, ts0, ts1: +lda_stoll_par(f, params, f_pw, rs, z, 1) * b97mv_g(b97mv_gamma_ss, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_ss, b97mv_par_n, xs0, ts0, 0) + lda_stoll_par(f, params, f_pw, rs, -z, -1) * b97mv_g(b97mv_gamma_ss, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_ss, b97mv_par_n, xs1, ts1, 0)

  b97mv_fos = lambda rs, z, xs0, xs1, ts0, ts1: lda_stoll_perp(f, params, f_pw, rs, z) * b97mv_g(b97mv_gamma_os, b97mv_wx_os, b97mv_ux_os, b97mv_par_os, b97mv_par_n, jnp.sqrt(xs0 ** 2 + xs1 ** 2) / jnp.sqrt(2), ts0, ts1)

  wb97mv_f = lambda rs, z, xs0, xs1, ts0, ts1: f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, (1 + z) / 2 * lda_x_erf_spin(rs * (2 / (1 + z)) ** (1 / 3), 1) * b97mv_g(b97mv_gamma_x, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_x, b97mv_par_n, xs0, ts0, 0)) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, (1 - z) / 2 * lda_x_erf_spin(rs * (2 / (1 - z)) ** (1 / 3), 1) * b97mv_g(b97mv_gamma_x, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_x, b97mv_par_n, xs1, ts1, 0))

  b97mv_f = lambda rs, z, xs0, xs1, ts0, ts1: +b97mv_fpar(rs, z, xs0, xs1, ts0, ts1) + b97mv_fos(rs, z, xs0, xs1, ts0, ts1)

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: wb97mv_f(rs, z, xs0, xs1, ts0, ts1) + b97mv_f(rs, z, xs0, xs1, ts0, ts1)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
      f.xt(r0, r1, s0, s1, s2),
      f.xs0(r0, r1, s0, s2),
      f.xs1(r0, r1, s0, s2),
      f.u0(r0, r1, l0, l1),
      f.u1(r0, r1, l0, l1),
      f.tt0(r0, r1, tau0, tau1),
      f.tt1(r0, r1, tau0, tau1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_c_os_raw = params.c_os
  if isinstance(params_c_os_raw, (str, bytes, dict)):
    params_c_os = params_c_os_raw
  else:
    try:
      params_c_os_seq = list(params_c_os_raw)
    except TypeError:
      params_c_os = params_c_os_raw
    else:
      params_c_os_seq = np.asarray(params_c_os_seq, dtype=np.float64)
      params_c_os = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_os_seq))
  params_c_ss_raw = params.c_ss
  if isinstance(params_c_ss_raw, (str, bytes, dict)):
    params_c_ss = params_c_ss_raw
  else:
    try:
      params_c_ss_seq = list(params_c_ss_raw)
    except TypeError:
      params_c_ss = params_c_ss_raw
    else:
      params_c_ss_seq = np.asarray(params_c_ss_seq, dtype=np.float64)
      params_c_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_ss_seq))
  params_c_x_raw = params.c_x
  if isinstance(params_c_x_raw, (str, bytes, dict)):
    params_c_x = params_c_x_raw
  else:
    try:
      params_c_x_seq = list(params_c_x_raw)
    except TypeError:
      params_c_x = params_c_x_raw
    else:
      params_c_x_seq = np.asarray(params_c_x_seq, dtype=np.float64)
      params_c_x = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_x_seq))

  b97mv_par_n = 5

  b97mv_gamma_x = 0.003840616724010807

  b97mv_par_x = [None, np.array([np.nan, params_c_x[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_x[2], 0, 1], dtype=np.float64), np.array([np.nan, params_c_x[3], 1, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_ss = 0.46914023462026644

  b97mv_par_ss = [None, np.array([np.nan, params_c_ss[1], 0, 1], dtype=np.float64), np.array([np.nan, params_c_ss[2], 1, 0], dtype=np.float64), np.array([np.nan, params_c_ss[3], 2, 0], dtype=np.float64), np.array([np.nan, params_c_ss[4], 0, 6], dtype=np.float64), np.array([np.nan, params_c_ss[5], 4, 6], dtype=np.float64)]

  b97mv_gamma_os = 0.006

  b97mv_par_os = [None, np.array([np.nan, params_c_os[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_os[2], 2, 0], dtype=np.float64), np.array([np.nan, params_c_os[3], 6, 0], dtype=np.float64), np.array([np.nan, params_c_os[4], 6, 2 / 3], dtype=np.float64), np.array([np.nan, params_c_os[5], 2, 2 / 3], dtype=np.float64)]

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  lda_x_ax = -f.RS_FACTOR * X_FACTOR_C / 2 ** (4 / 3)

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  b97mv_ux = lambda mgamma, x: mgamma * x ** 2 / (1 + mgamma * x ** 2)

  b97mv_ux_os = lambda mgamma, x: x

  b97mv_wx_ss = lambda t, dummy=None: (K_FACTOR_C - t) / (K_FACTOR_C + t)

  b97mv_wx_os = lambda ts0, ts1: (K_FACTOR_C * (ts0 + ts1) - 2 * ts0 * ts1) / (K_FACTOR_C * (ts0 + ts1) + 2 * ts0 * ts1)

  b97mv_g = lambda mgamma, wx, ux, cc, n, xs, ts0, ts1: jnp.sum(jnp.array([cc[i][1] * wx(ts0, ts1) ** cc[i][2] * ux(mgamma, xs) ** cc[i][3] for i in range(1, n + 1)]), axis=0)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  b97mv_ux_ss = lambda mgamma, x: b97mv_ux(mgamma, x)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  lda_x_erf_spin = lambda rs, z: lda_x_ax * f.opz_pow_n(z, 4 / 3) / rs * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3))

  b97mv_fpar = lambda rs, z, xs0, xs1, ts0, ts1: +lda_stoll_par(f, params, f_pw, rs, z, 1) * b97mv_g(b97mv_gamma_ss, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_ss, b97mv_par_n, xs0, ts0, 0) + lda_stoll_par(f, params, f_pw, rs, -z, -1) * b97mv_g(b97mv_gamma_ss, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_ss, b97mv_par_n, xs1, ts1, 0)

  b97mv_fos = lambda rs, z, xs0, xs1, ts0, ts1: lda_stoll_perp(f, params, f_pw, rs, z) * b97mv_g(b97mv_gamma_os, b97mv_wx_os, b97mv_ux_os, b97mv_par_os, b97mv_par_n, jnp.sqrt(xs0 ** 2 + xs1 ** 2) / jnp.sqrt(2), ts0, ts1)

  wb97mv_f = lambda rs, z, xs0, xs1, ts0, ts1: f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, (1 + z) / 2 * lda_x_erf_spin(rs * (2 / (1 + z)) ** (1 / 3), 1) * b97mv_g(b97mv_gamma_x, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_x, b97mv_par_n, xs0, ts0, 0)) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, (1 - z) / 2 * lda_x_erf_spin(rs * (2 / (1 - z)) ** (1 / 3), 1) * b97mv_g(b97mv_gamma_x, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_x, b97mv_par_n, xs1, ts1, 0))

  b97mv_f = lambda rs, z, xs0, xs1, ts0, ts1: +b97mv_fpar(rs, z, xs0, xs1, ts0, ts1) + b97mv_fos(rs, z, xs0, xs1, ts0, ts1)

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: wb97mv_f(rs, z, xs0, xs1, ts0, ts1) + b97mv_f(rs, z, xs0, xs1, ts0, ts1)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
      f.xt(r0 / 2, r0 / 2, s0 / 4, s0 / 4, s0 / 4),
      f.xs0(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.xs1(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.u0(r0 / 2, r0 / 2, l0 / 2, l0 / 2),
      f.u1(r0 / 2, r0 / 2, l0 / 2, l0 / 2),
      f.tt0(r0 / 2, r0 / 2, tau0 / 2, tau0 / 2),
      f.tt1(r0 / 2, r0 / 2, tau0 / 2, tau0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_c_os_raw = params.c_os
  if isinstance(params_c_os_raw, (str, bytes, dict)):
    params_c_os = params_c_os_raw
  else:
    try:
      params_c_os_seq = list(params_c_os_raw)
    except TypeError:
      params_c_os = params_c_os_raw
    else:
      params_c_os_seq = np.asarray(params_c_os_seq, dtype=np.float64)
      params_c_os = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_os_seq))
  params_c_ss_raw = params.c_ss
  if isinstance(params_c_ss_raw, (str, bytes, dict)):
    params_c_ss = params_c_ss_raw
  else:
    try:
      params_c_ss_seq = list(params_c_ss_raw)
    except TypeError:
      params_c_ss = params_c_ss_raw
    else:
      params_c_ss_seq = np.asarray(params_c_ss_seq, dtype=np.float64)
      params_c_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_ss_seq))
  params_c_x_raw = params.c_x
  if isinstance(params_c_x_raw, (str, bytes, dict)):
    params_c_x = params_c_x_raw
  else:
    try:
      params_c_x_seq = list(params_c_x_raw)
    except TypeError:
      params_c_x = params_c_x_raw
    else:
      params_c_x_seq = np.asarray(params_c_x_seq, dtype=np.float64)
      params_c_x = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_x_seq))

  b97mv_par_n = 5

  b97mv_gamma_x = 0.003840616724010807

  b97mv_par_x = [None, np.array([np.nan, params_c_x[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_x[2], 0, 1], dtype=np.float64), np.array([np.nan, params_c_x[3], 1, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_ss = 0.46914023462026644

  b97mv_par_ss = [None, np.array([np.nan, params_c_ss[1], 0, 1], dtype=np.float64), np.array([np.nan, params_c_ss[2], 1, 0], dtype=np.float64), np.array([np.nan, params_c_ss[3], 2, 0], dtype=np.float64), np.array([np.nan, params_c_ss[4], 0, 6], dtype=np.float64), np.array([np.nan, params_c_ss[5], 4, 6], dtype=np.float64)]

  b97mv_gamma_os = 0.006

  b97mv_par_os = [None, np.array([np.nan, params_c_os[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_os[2], 2, 0], dtype=np.float64), np.array([np.nan, params_c_os[3], 6, 0], dtype=np.float64), np.array([np.nan, params_c_os[4], 6, 2 / 3], dtype=np.float64), np.array([np.nan, params_c_os[5], 2, 2 / 3], dtype=np.float64)]

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  lda_x_ax = -f.RS_FACTOR * X_FACTOR_C / 2 ** (4 / 3)

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  b97mv_ux = lambda mgamma, x: mgamma * x ** 2 / (1 + mgamma * x ** 2)

  b97mv_ux_os = lambda mgamma, x: x

  b97mv_wx_ss = lambda t, dummy=None: (K_FACTOR_C - t) / (K_FACTOR_C + t)

  b97mv_wx_os = lambda ts0, ts1: (K_FACTOR_C * (ts0 + ts1) - 2 * ts0 * ts1) / (K_FACTOR_C * (ts0 + ts1) + 2 * ts0 * ts1)

  b97mv_g = lambda mgamma, wx, ux, cc, n, xs, ts0, ts1: jnp.sum(jnp.array([cc[i][1] * wx(ts0, ts1) ** cc[i][2] * ux(mgamma, xs) ** cc[i][3] for i in range(1, n + 1)]), axis=0)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  b97mv_ux_ss = lambda mgamma, x: b97mv_ux(mgamma, x)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  lda_x_erf_spin = lambda rs, z: lda_x_ax * f.opz_pow_n(z, 4 / 3) / rs * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3))

  b97mv_fpar = lambda rs, z, xs0, xs1, ts0, ts1: +lda_stoll_par(f, params, f_pw, rs, z, 1) * b97mv_g(b97mv_gamma_ss, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_ss, b97mv_par_n, xs0, ts0, 0) + lda_stoll_par(f, params, f_pw, rs, -z, -1) * b97mv_g(b97mv_gamma_ss, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_ss, b97mv_par_n, xs1, ts1, 0)

  b97mv_fos = lambda rs, z, xs0, xs1, ts0, ts1: lda_stoll_perp(f, params, f_pw, rs, z) * b97mv_g(b97mv_gamma_os, b97mv_wx_os, b97mv_ux_os, b97mv_par_os, b97mv_par_n, jnp.sqrt(xs0 ** 2 + xs1 ** 2) / jnp.sqrt(2), ts0, ts1)

  wb97mv_f = lambda rs, z, xs0, xs1, ts0, ts1: f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, (1 + z) / 2 * lda_x_erf_spin(rs * (2 / (1 + z)) ** (1 / 3), 1) * b97mv_g(b97mv_gamma_x, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_x, b97mv_par_n, xs0, ts0, 0)) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, (1 - z) / 2 * lda_x_erf_spin(rs * (2 / (1 - z)) ** (1 / 3), 1) * b97mv_g(b97mv_gamma_x, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_x, b97mv_par_n, xs1, ts1, 0))

  b97mv_f = lambda rs, z, xs0, xs1, ts0, ts1: +b97mv_fpar(rs, z, xs0, xs1, ts0, ts1) + b97mv_fos(rs, z, xs0, xs1, ts0, ts1)

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: wb97mv_f(rs, z, xs0, xs1, ts0, ts1) + b97mv_f(rs, z, xs0, xs1, ts0, ts1)

  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t6 = 0.1e1 + t5
  t7 = t6 <= f.p.zeta_threshold
  t8 = r0 <= f.p.dens_threshold or t7
  t10 = 3 ** (0.1e1 / 0.3e1)
  t11 = t6 * t10 / 0.2e1
  t13 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t14 = 4 ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t16 = t13 * t15
  t17 = 2 ** (0.1e1 / 0.3e1)
  t18 = t16 * t17
  t19 = t11 * t18
  t20 = 0.2e1 <= f.p.zeta_threshold
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = t21 * f.p.zeta_threshold
  t24 = f.my_piecewise3(t20, t22, 0.2e1 * t17)
  t25 = t3 ** (0.1e1 / 0.3e1)
  t26 = t24 * t25
  t27 = 0.1e1 / t6
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t28
  t30 = 9 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = t13 ** 2
  t33 = t31 * t32
  t34 = f.p.cam_omega * t10
  t35 = t33 * t34
  t36 = 0.1e1 / t25
  t37 = t36 * t17
  t38 = f.my_piecewise3(t20, t21, t17)
  t39 = 0.1e1 / t38
  t40 = t28 * t39
  t43 = t35 * t37 * t40 / 0.18e2
  t44 = 0.135e1 <= t43
  t45 = 0.135e1 < t43
  t46 = f.my_piecewise3(t45, t43, 0.135e1)
  t47 = t46 ** 2
  t50 = t47 ** 2
  t53 = t50 * t47
  t56 = t50 ** 2
  t68 = t56 ** 2
  t72 = f.my_piecewise3(t45, 0.135e1, t43)
  t73 = jnp.sqrt(jnp.pi)
  t74 = 0.1e1 / t72
  t76 = jax.lax.erf(t74 / 0.2e1)
  t78 = t72 ** 2
  t79 = 0.1e1 / t78
  t81 = jnp.exp(-t79 / 0.4e1)
  t82 = t81 - 0.1e1
  t85 = t81 - 0.3e1 / 0.2e1 - 0.2e1 * t78 * t82
  t88 = 0.2e1 * t72 * t85 + t73 * t76
  t92 = f.my_piecewise3(t44, 0.1e1 / t47 / 0.36e2 - 0.1e1 / t50 / 0.960e3 + 0.1e1 / t53 / 0.26880e5 - 0.1e1 / t56 / 0.829440e6 + 0.1e1 / t56 / t47 / 0.28385280e8 - 0.1e1 / t56 / t50 / 0.1073479680e10 + 0.1e1 / t56 / t53 / 0.44590694400e11 - 0.1e1 / t68 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t72 * t88)
  t93 = t29 * t92
  t94 = params.c_x[0]
  t95 = params.c_x[1]
  t96 = t95 * s0
  t97 = r0 ** 2
  t98 = r0 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t101 = 0.1e1 / t99 / t97
  t102 = s0 * t101
  t104 = 0.1e1 + 0.3840616724010807e-2 * t102
  t105 = 0.1e1 / t104
  t109 = params.c_x[2]
  t110 = 6 ** (0.1e1 / 0.3e1)
  t111 = t110 ** 2
  t112 = jnp.pi ** 2
  t113 = t112 ** (0.1e1 / 0.3e1)
  t114 = t113 ** 2
  t115 = t111 * t114
  t116 = 0.3e1 / 0.10e2 * t115
  t118 = 0.1e1 / t99 / r0
  t119 = tau0 * t118
  t120 = t116 - t119
  t121 = t109 * t120
  t122 = t116 + t119
  t123 = 0.1e1 / t122
  t125 = t94 + 0.3840616724010807e-2 * t96 * t101 * t105 + t121 * t123
  t126 = t93 * t125
  t127 = t26 * t126
  t130 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t19 * t127)
  t132 = 0.1e1 - t5
  t133 = t132 <= f.p.zeta_threshold
  t134 = r1 <= f.p.dens_threshold or t133
  t136 = t132 * t10 / 0.2e1
  t137 = t136 * t18
  t138 = 0.1e1 / t132
  t139 = t138 ** (0.1e1 / 0.3e1)
  t140 = 0.1e1 / t139
  t141 = t139 * t39
  t144 = t35 * t37 * t141 / 0.18e2
  t145 = 0.135e1 <= t144
  t146 = 0.135e1 < t144
  t147 = f.my_piecewise3(t146, t144, 0.135e1)
  t148 = t147 ** 2
  t151 = t148 ** 2
  t154 = t151 * t148
  t157 = t151 ** 2
  t169 = t157 ** 2
  t173 = f.my_piecewise3(t146, 0.135e1, t144)
  t174 = 0.1e1 / t173
  t176 = jax.lax.erf(t174 / 0.2e1)
  t178 = t173 ** 2
  t179 = 0.1e1 / t178
  t181 = jnp.exp(-t179 / 0.4e1)
  t182 = t181 - 0.1e1
  t185 = t181 - 0.3e1 / 0.2e1 - 0.2e1 * t178 * t182
  t188 = 0.2e1 * t173 * t185 + t73 * t176
  t192 = f.my_piecewise3(t145, 0.1e1 / t148 / 0.36e2 - 0.1e1 / t151 / 0.960e3 + 0.1e1 / t154 / 0.26880e5 - 0.1e1 / t157 / 0.829440e6 + 0.1e1 / t157 / t148 / 0.28385280e8 - 0.1e1 / t157 / t151 / 0.1073479680e10 + 0.1e1 / t157 / t154 / 0.44590694400e11 - 0.1e1 / t169 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t173 * t188)
  t193 = t140 * t192
  t194 = t95 * s2
  t195 = r1 ** 2
  t196 = r1 ** (0.1e1 / 0.3e1)
  t197 = t196 ** 2
  t199 = 0.1e1 / t197 / t195
  t200 = s2 * t199
  t202 = 0.1e1 + 0.3840616724010807e-2 * t200
  t203 = 0.1e1 / t202
  t208 = 0.1e1 / t197 / r1
  t209 = tau1 * t208
  t210 = t116 - t209
  t211 = t109 * t210
  t212 = t116 + t209
  t213 = 0.1e1 / t212
  t215 = t94 + 0.3840616724010807e-2 * t194 * t199 * t203 + t211 * t213
  t216 = t193 * t215
  t217 = t26 * t216
  t220 = f.my_piecewise3(t134, 0, -0.3e1 / 0.32e2 * t137 * t217)
  t221 = f.my_piecewise3(t7, f.p.zeta_threshold, t6)
  t222 = t10 * t13
  t223 = t222 * t15
  t224 = 0.1e1 / t21
  t225 = t6 ** (0.1e1 / 0.3e1)
  t227 = f.my_piecewise3(t7, t224, 0.1e1 / t225)
  t229 = t223 * t37 * t227
  t231 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t229
  t232 = jnp.sqrt(t229)
  t235 = t229 ** 0.15e1
  t237 = t10 ** 2
  t238 = t237 * t32
  t239 = t238 * t14
  t240 = t25 ** 2
  t241 = 0.1e1 / t240
  t242 = t17 ** 2
  t243 = t241 * t242
  t244 = t227 ** 2
  t246 = t239 * t243 * t244
  t248 = 0.23615562999000000000000000000000000000000000000000e0 * t232 + 0.55770497660000000000000000000000000000000000000000e-1 * t229 + 0.12733196185000000000000000000000000000000000000000e-1 * t235 + 0.76629248290000000000000000000000000000000000000000e-2 * t246
  t250 = 0.1e1 + 0.1e1 / t248
  t251 = jnp.log(t250)
  t252 = t231 * t251
  t254 = f.my_piecewise3(0.0e0 <= f.p.zeta_threshold, t22, 0)
  t258 = 0.1e1 / (0.2e1 * t17 - 0.2e1)
  t259 = (t24 + t254 - 0.2e1) * t258
  t261 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t229
  t266 = 0.21948324211500000000000000000000000000000000000000e0 * t232 + 0.48172707847500000000000000000000000000000000000000e-1 * t229 + 0.13082189292500000000000000000000000000000000000000e-1 * t235 + 0.48592432297500000000000000000000000000000000000000e-2 * t246
  t268 = 0.1e1 + 0.1e1 / t266
  t269 = jnp.log(t268)
  t272 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t229
  t277 = 0.17489762330000000000000000000000000000000000000000e0 * t232 + 0.30591463695000000000000000000000000000000000000000e-1 * t229 + 0.37162156485000000000000000000000000000000000000000e-2 * t235 + 0.41939460495000000000000000000000000000000000000000e-2 * t246
  t279 = 0.1e1 + 0.1e1 / t277
  t280 = jnp.log(t279)
  t281 = t272 * t280
  t287 = -t252 + t259 * (-t261 * t269 + t252 - 0.58482236226346462072622386637590534819724553404281e0 * t281) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t281
  t290 = f.my_piecewise3(t8, 0, t221 * t287 / 0.2e1)
  t291 = params.c_ss[0]
  t292 = t291 * s0
  t294 = 0.1e1 + 0.46914023462026644e0 * t102
  t295 = 0.1e1 / t294
  t299 = params.c_ss[1]
  t300 = t299 * t120
  t302 = params.c_ss[2]
  t303 = t120 ** 2
  t304 = t302 * t303
  t305 = t122 ** 2
  t306 = 0.1e1 / t305
  t308 = params.c_ss[3]
  t309 = s0 ** 2
  t310 = t309 ** 2
  t311 = t310 * t309
  t312 = t308 * t311
  t313 = t97 ** 2
  t314 = t313 ** 2
  t315 = t314 ** 2
  t316 = 0.1e1 / t315
  t317 = t294 ** 2
  t318 = t317 ** 2
  t320 = 0.1e1 / t318 / t317
  t321 = t316 * t320
  t324 = params.c_ss[4]
  t325 = t303 ** 2
  t326 = t324 * t325
  t327 = t305 ** 2
  t328 = 0.1e1 / t327
  t329 = t326 * t328
  t334 = 0.46914023462026644e0 * t292 * t101 * t295 + t300 * t123 + t304 * t306 + 0.10661445329398457900683623960781177903004063098542e-1 * t312 * t321 + 0.10661445329398457900683623960781177903004063098542e-1 * t329 * t311 * t316 * t320
  t335 = t290 * t334
  t336 = f.my_piecewise3(t133, f.p.zeta_threshold, t132)
  t337 = t132 ** (0.1e1 / 0.3e1)
  t339 = f.my_piecewise3(t133, t224, 0.1e1 / t337)
  t341 = t223 * t37 * t339
  t343 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t341
  t344 = jnp.sqrt(t341)
  t347 = t341 ** 0.15e1
  t349 = t339 ** 2
  t351 = t239 * t243 * t349
  t353 = 0.23615562999000000000000000000000000000000000000000e0 * t344 + 0.55770497660000000000000000000000000000000000000000e-1 * t341 + 0.12733196185000000000000000000000000000000000000000e-1 * t347 + 0.76629248290000000000000000000000000000000000000000e-2 * t351
  t355 = 0.1e1 + 0.1e1 / t353
  t356 = jnp.log(t355)
  t357 = t343 * t356
  t359 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t341
  t364 = 0.21948324211500000000000000000000000000000000000000e0 * t344 + 0.48172707847500000000000000000000000000000000000000e-1 * t341 + 0.13082189292500000000000000000000000000000000000000e-1 * t347 + 0.48592432297500000000000000000000000000000000000000e-2 * t351
  t366 = 0.1e1 + 0.1e1 / t364
  t367 = jnp.log(t366)
  t370 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t341
  t375 = 0.17489762330000000000000000000000000000000000000000e0 * t344 + 0.30591463695000000000000000000000000000000000000000e-1 * t341 + 0.37162156485000000000000000000000000000000000000000e-2 * t347 + 0.41939460495000000000000000000000000000000000000000e-2 * t351
  t377 = 0.1e1 + 0.1e1 / t375
  t378 = jnp.log(t377)
  t379 = t370 * t378
  t385 = -t357 + t259 * (-t359 * t367 + t357 - 0.58482236226346462072622386637590534819724553404281e0 * t379) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t379
  t388 = f.my_piecewise3(t134, 0, t336 * t385 / 0.2e1)
  t389 = t291 * s2
  t391 = 0.1e1 + 0.46914023462026644e0 * t200
  t392 = 0.1e1 / t391
  t396 = t299 * t210
  t398 = t210 ** 2
  t399 = t302 * t398
  t400 = t212 ** 2
  t401 = 0.1e1 / t400
  t403 = s2 ** 2
  t404 = t403 ** 2
  t405 = t404 * t403
  t406 = t308 * t405
  t407 = t195 ** 2
  t408 = t407 ** 2
  t409 = t408 ** 2
  t410 = 0.1e1 / t409
  t411 = t391 ** 2
  t412 = t411 ** 2
  t414 = 0.1e1 / t412 / t411
  t415 = t410 * t414
  t418 = t398 ** 2
  t419 = t324 * t418
  t420 = t400 ** 2
  t421 = 0.1e1 / t420
  t422 = t419 * t421
  t427 = 0.46914023462026644e0 * t389 * t199 * t392 + t396 * t213 + t399 * t401 + 0.10661445329398457900683623960781177903004063098542e-1 * t406 * t415 + 0.10661445329398457900683623960781177903004063098542e-1 * t422 * t405 * t410 * t414
  t428 = t388 * t427
  t430 = t222 * t15 * t36
  t432 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t430
  t433 = jnp.sqrt(t430)
  t436 = t430 ** 0.15e1
  t439 = t238 * t14 * t241
  t441 = 0.23615562999000000000000000000000000000000000000000e0 * t433 + 0.55770497660000000000000000000000000000000000000000e-1 * t430 + 0.12733196185000000000000000000000000000000000000000e-1 * t436 + 0.76629248290000000000000000000000000000000000000000e-2 * t439
  t443 = 0.1e1 + 0.1e1 / t441
  t444 = jnp.log(t443)
  t445 = t432 * t444
  t446 = t2 ** 2
  t447 = t446 ** 2
  t448 = t3 ** 2
  t449 = t448 ** 2
  t450 = 0.1e1 / t449
  t451 = t447 * t450
  t452 = t225 * t6
  t453 = f.my_piecewise3(t7, t22, t452)
  t454 = t337 * t132
  t455 = f.my_piecewise3(t133, t22, t454)
  t457 = (t453 + t455 - 0.2e1) * t258
  t459 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t430
  t464 = 0.21948324211500000000000000000000000000000000000000e0 * t433 + 0.48172707847500000000000000000000000000000000000000e-1 * t430 + 0.13082189292500000000000000000000000000000000000000e-1 * t436 + 0.48592432297500000000000000000000000000000000000000e-2 * t439
  t466 = 0.1e1 + 0.1e1 / t464
  t467 = jnp.log(t466)
  t470 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t430
  t475 = 0.17489762330000000000000000000000000000000000000000e0 * t433 + 0.30591463695000000000000000000000000000000000000000e-1 * t430 + 0.37162156485000000000000000000000000000000000000000e-2 * t436 + 0.41939460495000000000000000000000000000000000000000e-2 * t439
  t477 = 0.1e1 + 0.1e1 / t475
  t478 = jnp.log(t477)
  t479 = t470 * t478
  t481 = -t459 * t467 + t445 - 0.58482236226346462072622386637590534819724553404281e0 * t479
  t482 = t457 * t481
  t486 = -t445 + t451 * t482 + 0.58482236226346462072622386637590534819724553404281e0 * t457 * t479 - t290 - t388
  t488 = params.c_os[1]
  t491 = 0.3e1 / 0.10e2 * t115 * (t119 + t209)
  t493 = 0.2e1 * t119 * t209
  t494 = t491 - t493
  t495 = t494 ** 2
  t496 = t488 * t495
  t497 = t491 + t493
  t498 = t497 ** 2
  t499 = 0.1e1 / t498
  t501 = params.c_os[2]
  t502 = t495 ** 2
  t503 = t502 * t495
  t504 = t501 * t503
  t505 = t498 ** 2
  t507 = 0.1e1 / t505 / t498
  t509 = params.c_os[3]
  t510 = t509 * t503
  t513 = jnp.sqrt(t102 + t200)
  t514 = jnp.sqrt(0.2e1)
  t516 = (t513 * t514) ** (0.1e1 / 0.3e1)
  t517 = t516 ** 2
  t521 = params.c_os[4]
  t522 = t521 * t495
  t527 = params.c_os[0] + t496 * t499 + t504 * t507 + t510 * t507 * t17 * t517 / 0.2e1 + t522 * t499 * t17 * t517 / 0.2e1
  t528 = t486 * t527
  t530 = t2 / t448
  t531 = t4 - t530
  t532 = t531 / 0.2e1
  t537 = t24 * t241
  t540 = t19 * t537 * t126 / 0.32e2
  t543 = t15 * t17 * t24
  t544 = t11 * t13 * t543
  t548 = t25 / t28 / t27 * t92
  t549 = t6 ** 2
  t550 = 0.1e1 / t549
  t551 = t125 * t550
  t556 = t47 * t46
  t557 = 0.1e1 / t556
  t559 = 0.1e1 / t25 / t3
  t560 = t559 * t17
  t562 = t35 * t560 * t40
  t564 = t33 * t34 * t36
  t565 = t28 ** 2
  t567 = t17 / t565
  t568 = t39 * t550
  t573 = -t564 * t567 * t568 * t531 / 0.54e2 - t562 / 0.54e2
  t574 = f.my_piecewise3(t45, t573, 0)
  t577 = t50 * t46
  t578 = 0.1e1 / t577
  t581 = t50 * t556
  t582 = 0.1e1 / t581
  t586 = 0.1e1 / t56 / t46
  t590 = 0.1e1 / t56 / t556
  t594 = 0.1e1 / t56 / t577
  t598 = 0.1e1 / t56 / t581
  t602 = 0.1e1 / t68 / t46
  t606 = f.my_piecewise3(t45, 0, t573)
  t608 = t81 * t79
  t613 = 0.1e1 / t78 / t72
  t617 = t72 * t82
  t629 = f.my_piecewise3(t44, -t557 * t574 / 0.18e2 + t578 * t574 / 0.240e3 - t582 * t574 / 0.4480e4 + t586 * t574 / 0.103680e6 - t590 * t574 / 0.2838528e7 + t594 * t574 / 0.89456640e8 - t598 * t574 / 0.3185049600e10 + t602 * t574 / 0.126340300800e12, -0.8e1 / 0.3e1 * t606 * t88 - 0.8e1 / 0.3e1 * t72 * (-t608 * t606 + 0.2e1 * t606 * t85 + 0.2e1 * t72 * (t613 * t606 * t81 / 0.2e1 - 0.4e1 * t617 * t606 - t74 * t606 * t81)))
  t635 = t97 * r0
  t637 = 0.1e1 / t99 / t635
  t644 = 0.1e1 / t98 / t313 / t97
  t645 = t104 ** 2
  t646 = 0.1e1 / t645
  t651 = t101 * t123
  t655 = t306 * tau0 * t101
  t664 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t532 * t10 * t18 * t127 - t540 - t544 * t548 * t551 * t531 / 0.32e2 - 0.3e1 / 0.32e2 * t19 * t26 * t29 * t629 * t125 - 0.3e1 / 0.32e2 * t19 * t26 * t93 * (-0.10241644597362152000000000000000000000000000000000e-1 * t96 * t637 * t105 + 0.39334231522004008708993740776664000000000000000000e-4 * t95 * t309 * t644 * t646 + 0.5e1 / 0.3e1 * t109 * tau0 * t651 + 0.5e1 / 0.3e1 * t121 * t655))
  t672 = t137 * t537 * t216 / 0.32e2
  t674 = t136 * t13 * t543
  t678 = t25 / t139 / t138 * t192
  t679 = t132 ** 2
  t680 = 0.1e1 / t679
  t681 = t215 * t680
  t682 = -t531
  t687 = t148 * t147
  t688 = 0.1e1 / t687
  t690 = t35 * t560 * t141
  t691 = t139 ** 2
  t693 = t17 / t691
  t694 = t39 * t680
  t699 = -t564 * t693 * t694 * t682 / 0.54e2 - t690 / 0.54e2
  t700 = f.my_piecewise3(t146, t699, 0)
  t703 = t151 * t147
  t704 = 0.1e1 / t703
  t707 = t151 * t687
  t708 = 0.1e1 / t707
  t712 = 0.1e1 / t157 / t147
  t716 = 0.1e1 / t157 / t687
  t720 = 0.1e1 / t157 / t703
  t724 = 0.1e1 / t157 / t707
  t728 = 0.1e1 / t169 / t147
  t732 = f.my_piecewise3(t146, 0, t699)
  t734 = t181 * t179
  t739 = 0.1e1 / t178 / t173
  t743 = t173 * t182
  t755 = f.my_piecewise3(t145, -t688 * t700 / 0.18e2 + t704 * t700 / 0.240e3 - t708 * t700 / 0.4480e4 + t712 * t700 / 0.103680e6 - t716 * t700 / 0.2838528e7 + t720 * t700 / 0.89456640e8 - t724 * t700 / 0.3185049600e10 + t728 * t700 / 0.126340300800e12, -0.8e1 / 0.3e1 * t732 * t188 - 0.8e1 / 0.3e1 * t173 * (-t734 * t732 + 0.2e1 * t732 * t185 + 0.2e1 * t173 * (t739 * t732 * t181 / 0.2e1 - 0.4e1 * t743 * t732 - t174 * t732 * t181)))
  t762 = f.my_piecewise3(t134, 0, 0.3e1 / 0.32e2 * t532 * t10 * t18 * t217 - t672 - t674 * t678 * t681 * t682 / 0.32e2 - 0.3e1 / 0.32e2 * t137 * t26 * t140 * t755 * t215)
  t763 = f.my_piecewise3(t7, 0, t531)
  t766 = t223 * t560 * t227
  t767 = 0.11073470983333333333333333333333333333333333333333e-2 * t766
  t768 = 0.1e1 / t452
  t771 = f.my_piecewise3(t7, 0, -t768 * t531 / 0.3e1)
  t773 = t223 * t37 * t771
  t776 = (-t767 + 0.33220412950000000000000000000000000000000000000000e-2 * t773) * t251
  t777 = t248 ** 2
  t779 = t231 / t777
  t780 = 0.1e1 / t232
  t781 = t766 / 0.3e1
  t782 = -t781 + t773
  t783 = t780 * t782
  t785 = 0.18590165886666666666666666666666666666666666666667e-1 * t766
  t787 = t229 ** 0.5e0
  t788 = t787 * t782
  t791 = 0.1e1 / t240 / t3
  t792 = t791 * t242
  t794 = t239 * t792 * t244
  t795 = 0.51086165526666666666666666666666666666666666666667e-2 * t794
  t798 = t239 * t243 * t227 * t771
  t801 = 0.1e1 / t250
  t803 = t779 * (0.11807781499500000000000000000000000000000000000000e0 * t783 - t785 + 0.55770497660000000000000000000000000000000000000000e-1 * t773 + 0.19099794277500000000000000000000000000000000000000e-1 * t788 - t795 + 0.15325849658000000000000000000000000000000000000000e-1 * t798) * t801
  t804 = 0.53237641966666666666666666666666666666666666666667e-3 * t766
  t808 = t266 ** 2
  t810 = t261 / t808
  t812 = 0.16057569282500000000000000000000000000000000000000e-1 * t766
  t815 = 0.32394954865000000000000000000000000000000000000000e-2 * t794
  t818 = 0.1e1 / t268
  t821 = 0.31311127083333333333333333333333333333333333333333e-3 * t766
  t824 = (-t821 + 0.93933381250000000000000000000000000000000000000000e-3 * t773) * t280
  t826 = t277 ** 2
  t827 = 0.1e1 / t826
  t828 = t272 * t827
  t830 = 0.10197154565000000000000000000000000000000000000000e-1 * t766
  t833 = 0.27959640330000000000000000000000000000000000000000e-2 * t794
  t835 = 0.87448811650000000000000000000000000000000000000000e-1 * t783 - t830 + 0.30591463695000000000000000000000000000000000000000e-1 * t773 + 0.55743234727500000000000000000000000000000000000000e-2 * t788 - t833 + 0.83878920990000000000000000000000000000000000000000e-2 * t798
  t836 = 0.1e1 / t279
  t844 = t259 * t272
  t853 = f.my_piecewise3(t8, 0, t763 * t287 / 0.2e1 + t221 * (-t776 + t803 + t259 * (-(-t804 + 0.15971292590000000000000000000000000000000000000000e-2 * t773) * t269 + t810 * (0.10974162105750000000000000000000000000000000000000e0 * t783 - t812 + 0.48172707847500000000000000000000000000000000000000e-1 * t773 + 0.19623283938750000000000000000000000000000000000000e-1 * t788 - t815 + 0.97184864595000000000000000000000000000000000000000e-2 * t798) * t818 + t776 - t803 - 0.58482236226346462072622386637590534819724553404281e0 * t824 + 0.58482236226346462072622386637590534819724553404281e0 * t828 * t835 * t836) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t824 - 0.58482236226346462072622386637590534819724553404281e0 * t844 * t827 * t835 * t836) / 0.2e1)
  t859 = 0.1e1 / t317
  t868 = t302 * t120
  t872 = 0.1e1 / t305 / t122
  t877 = t315 * r0
  t878 = 0.1e1 / t877
  t883 = t310 * t309 * s0
  t887 = 0.1e1 / t99 / t315 / t635
  t890 = 0.1e1 / t318 / t317 / t294
  t896 = t324 * t303 * t120 * t328
  t899 = 0.1e1 / t99 / t315 / t97
  t900 = t311 * t899
  t902 = t900 * t320 * tau0
  t907 = t326 / t327 / t122
  t918 = -0.12510406256540438400000000000000000000000000000000e1 * t292 * t637 * t295 + 0.58691349263882304531366500424072960000000000000000e0 * t291 * t309 * t644 * t859 + 0.5e1 / 0.3e1 * t299 * tau0 * t651 + 0.5e1 / 0.3e1 * t300 * t655 + 0.10e2 / 0.3e1 * t868 * t655 + 0.10e2 / 0.3e1 * t304 * t872 * tau0 * t101 - 0.17058312527037532641093798337249884644806500957667e0 * t312 * t878 * t320 + 0.80027407411602181735783566855612697994614340830460e-1 * t308 * t883 * t887 * t890 + 0.71076302195989719337890826405207852686693753990280e-1 * t896 * t902 + 0.71076302195989719337890826405207852686693753990280e-1 * t907 * t902 - 0.17058312527037532641093798337249884644806500957667e0 * t329 * t311 * t878 * t320 + 0.80027407411602181735783566855612697994614340830460e-1 * t329 * t883 * t887 * t890
  t920 = f.my_piecewise3(t133, 0, t682)
  t923 = t223 * t560 * t339
  t924 = 0.11073470983333333333333333333333333333333333333333e-2 * t923
  t925 = 0.1e1 / t454
  t928 = f.my_piecewise3(t133, 0, -t925 * t682 / 0.3e1)
  t930 = t223 * t37 * t928
  t933 = (-t924 + 0.33220412950000000000000000000000000000000000000000e-2 * t930) * t356
  t934 = t353 ** 2
  t936 = t343 / t934
  t937 = 0.1e1 / t344
  t938 = t923 / 0.3e1
  t939 = -t938 + t930
  t940 = t937 * t939
  t942 = 0.18590165886666666666666666666666666666666666666667e-1 * t923
  t944 = t341 ** 0.5e0
  t945 = t944 * t939
  t948 = t239 * t792 * t349
  t949 = 0.51086165526666666666666666666666666666666666666667e-2 * t948
  t952 = t239 * t243 * t339 * t928
  t955 = 0.1e1 / t355
  t957 = t936 * (0.11807781499500000000000000000000000000000000000000e0 * t940 - t942 + 0.55770497660000000000000000000000000000000000000000e-1 * t930 + 0.19099794277500000000000000000000000000000000000000e-1 * t945 - t949 + 0.15325849658000000000000000000000000000000000000000e-1 * t952) * t955
  t958 = 0.53237641966666666666666666666666666666666666666667e-3 * t923
  t962 = t364 ** 2
  t964 = t359 / t962
  t966 = 0.16057569282500000000000000000000000000000000000000e-1 * t923
  t969 = 0.32394954865000000000000000000000000000000000000000e-2 * t948
  t972 = 0.1e1 / t366
  t975 = 0.31311127083333333333333333333333333333333333333333e-3 * t923
  t978 = (-t975 + 0.93933381250000000000000000000000000000000000000000e-3 * t930) * t378
  t980 = t375 ** 2
  t981 = 0.1e1 / t980
  t982 = t370 * t981
  t984 = 0.10197154565000000000000000000000000000000000000000e-1 * t923
  t987 = 0.27959640330000000000000000000000000000000000000000e-2 * t948
  t989 = 0.87448811650000000000000000000000000000000000000000e-1 * t940 - t984 + 0.30591463695000000000000000000000000000000000000000e-1 * t930 + 0.55743234727500000000000000000000000000000000000000e-2 * t945 - t987 + 0.83878920990000000000000000000000000000000000000000e-2 * t952
  t990 = 0.1e1 / t377
  t998 = t259 * t370
  t1007 = f.my_piecewise3(t134, 0, t920 * t385 / 0.2e1 + t336 * (-t933 + t957 + t259 * (-(-t958 + 0.15971292590000000000000000000000000000000000000000e-2 * t930) * t367 + t964 * (0.10974162105750000000000000000000000000000000000000e0 * t940 - t966 + 0.48172707847500000000000000000000000000000000000000e-1 * t930 + 0.19623283938750000000000000000000000000000000000000e-1 * t945 - t969 + 0.97184864595000000000000000000000000000000000000000e-2 * t952) * t972 + t933 - t957 - 0.58482236226346462072622386637590534819724553404281e0 * t978 + 0.58482236226346462072622386637590534819724553404281e0 * t982 * t989 * t990) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t978 - 0.58482236226346462072622386637590534819724553404281e0 * t998 * t981 * t989 * t990) / 0.2e1)
  t1009 = t15 * t559
  t1012 = 0.11073470983333333333333333333333333333333333333333e-2 * t222 * t1009 * t444
  t1013 = t441 ** 2
  t1018 = t16 * t559
  t1019 = 0.1e1 / t433 * t10 * t1018
  t1021 = t222 * t1009
  t1023 = t430 ** 0.5e0
  t1025 = t1023 * t10 * t1018
  t1028 = t238 * t14 * t791
  t1033 = t432 / t1013 * (-0.39359271665000000000000000000000000000000000000000e-1 * t1019 - 0.18590165886666666666666666666666666666666666666667e-1 * t1021 - 0.63665980925000000000000000000000000000000000000000e-2 * t1025 - 0.51086165526666666666666666666666666666666666666667e-2 * t1028) / t443
  t1037 = 0.4e1 * t446 * t2 * t450 * t482
  t1042 = 0.4e1 * t447 / t449 / t3 * t482
  t1045 = f.my_piecewise3(t7, 0, 0.4e1 / 0.3e1 * t225 * t531)
  t1048 = f.my_piecewise3(t133, 0, 0.4e1 / 0.3e1 * t337 * t682)
  t1050 = (t1045 + t1048) * t258
  t1056 = t464 ** 2
  t1070 = t475 ** 2
  t1071 = 0.1e1 / t1070
  t1077 = -0.29149603883333333333333333333333333333333333333333e-1 * t1019 - 0.10197154565000000000000000000000000000000000000000e-1 * t1021 - 0.18581078242500000000000000000000000000000000000000e-2 * t1025 - 0.27959640330000000000000000000000000000000000000000e-2 * t1028
  t1078 = 0.1e1 / t477
  t1084 = t451 * t457 * (0.53237641966666666666666666666666666666666666666667e-3 * t222 * t1009 * t467 + t459 / t1056 * (-0.36580540352500000000000000000000000000000000000000e-1 * t1019 - 0.16057569282500000000000000000000000000000000000000e-1 * t1021 - 0.65410946462500000000000000000000000000000000000000e-2 * t1025 - 0.32394954865000000000000000000000000000000000000000e-2 * t1028) / t466 - t1012 - t1033 + 0.18311447306006545054854346104378990962041954983034e-3 * t222 * t1009 * t478 + 0.58482236226346462072622386637590534819724553404281e0 * t470 * t1071 * t1077 * t1078)
  t1091 = 0.18311447306006545054854346104378990962041954983034e-3 * t457 * t10 * t16 * t559 * t478
  t1096 = 0.58482236226346462072622386637590534819724553404281e0 * t457 * t470 * t1071 * t1077 * t1078
  t1097 = t1012 + t1033 + t1037 - t1042 + t451 * t1050 * t481 + t1084 + 0.58482236226346462072622386637590534819724553404281e0 * t1050 * t479 - t1091 - t1096 - t853 - t1007
  t1099 = t488 * t494
  t1100 = tau0 * t101
  t1102 = t115 * t1100 / 0.2e1
  t1104 = 0.10e2 / 0.3e1 * t1100 * t209
  t1105 = -t1102 + t1104
  t1109 = t498 * t497
  t1110 = 0.1e1 / t1109
  t1111 = -t1102 - t1104
  t1115 = t502 * t494
  t1116 = t501 * t1115
  t1121 = 0.1e1 / t505 / t1109
  t1126 = t509 * t1115 * t507
  t1127 = t17 * t517
  t1128 = t1127 * t1105
  t1131 = t510 * t1121
  t1132 = t1127 * t1111
  t1135 = 2 ** (0.1e1 / 0.6e1)
  t1136 = t1135 ** 2
  t1137 = t1136 ** 2
  t1138 = t1137 * t1135
  t1140 = t510 * t507 * t1138
  t1141 = 0.1e1 / t516
  t1142 = 0.1e1 / t513
  t1143 = t1141 * t1142
  t1145 = t1143 * s0 * t637
  t1149 = t521 * t494 * t499
  t1151 = t522 * t1110
  t1154 = t522 * t499 * t1138
  vrho_0_ = t130 + t220 + t335 + t428 + t528 + t3 * (t664 + t762 + t853 * t334 + t290 * t918 + t1007 * t427 + t1097 * t527 + t486 * (0.2e1 * t1099 * t499 * t1105 - 0.2e1 * t496 * t1110 * t1111 + 0.6e1 * t1116 * t507 * t1105 - 0.6e1 * t504 * t1121 * t1111 + 0.3e1 * t1126 * t1128 - 0.3e1 * t1131 * t1132 - 0.4e1 / 0.9e1 * t1140 * t1145 + t1149 * t1128 - t1151 * t1132 - 0.4e1 / 0.9e1 * t1154 * t1145))
  t1161 = -t4 - t530
  t1162 = t1161 / 0.2e1
  t1175 = -t564 * t567 * t568 * t1161 / 0.54e2 - t562 / 0.54e2
  t1176 = f.my_piecewise3(t45, t1175, 0)
  t1194 = f.my_piecewise3(t45, 0, t1175)
  t1213 = f.my_piecewise3(t44, -t557 * t1176 / 0.18e2 + t578 * t1176 / 0.240e3 - t582 * t1176 / 0.4480e4 + t586 * t1176 / 0.103680e6 - t590 * t1176 / 0.2838528e7 + t594 * t1176 / 0.89456640e8 - t598 * t1176 / 0.3185049600e10 + t602 * t1176 / 0.126340300800e12, -0.8e1 / 0.3e1 * t1194 * t88 - 0.8e1 / 0.3e1 * t72 * (-t608 * t1194 + 0.2e1 * t1194 * t85 + 0.2e1 * t72 * (t613 * t1194 * t81 / 0.2e1 - 0.4e1 * t617 * t1194 - t74 * t1194 * t81)))
  t1220 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t1162 * t10 * t18 * t127 - t540 - t544 * t548 * t551 * t1161 / 0.32e2 - 0.3e1 / 0.32e2 * t19 * t26 * t29 * t1213 * t125)
  t1226 = -t1161
  t1235 = -t564 * t693 * t694 * t1226 / 0.54e2 - t690 / 0.54e2
  t1236 = f.my_piecewise3(t146, t1235, 0)
  t1254 = f.my_piecewise3(t146, 0, t1235)
  t1273 = f.my_piecewise3(t145, -t688 * t1236 / 0.18e2 + t704 * t1236 / 0.240e3 - t708 * t1236 / 0.4480e4 + t712 * t1236 / 0.103680e6 - t716 * t1236 / 0.2838528e7 + t720 * t1236 / 0.89456640e8 - t724 * t1236 / 0.3185049600e10 + t728 * t1236 / 0.126340300800e12, -0.8e1 / 0.3e1 * t1254 * t188 - 0.8e1 / 0.3e1 * t173 * (-t734 * t1254 + 0.2e1 * t1254 * t185 + 0.2e1 * t173 * (t739 * t1254 * t181 / 0.2e1 - 0.4e1 * t743 * t1254 - t174 * t1254 * t181)))
  t1279 = t195 * r1
  t1281 = 0.1e1 / t197 / t1279
  t1288 = 0.1e1 / t196 / t407 / t195
  t1289 = t202 ** 2
  t1290 = 0.1e1 / t1289
  t1295 = t199 * t213
  t1299 = t401 * tau1 * t199
  t1308 = f.my_piecewise3(t134, 0, 0.3e1 / 0.32e2 * t1162 * t10 * t18 * t217 - t672 - t674 * t678 * t681 * t1226 / 0.32e2 - 0.3e1 / 0.32e2 * t137 * t26 * t140 * t1273 * t215 - 0.3e1 / 0.32e2 * t137 * t26 * t193 * (-0.10241644597362152000000000000000000000000000000000e-1 * t194 * t1281 * t203 + 0.39334231522004008708993740776664000000000000000000e-4 * t95 * t403 * t1288 * t1290 + 0.5e1 / 0.3e1 * t109 * tau1 * t1295 + 0.5e1 / 0.3e1 * t211 * t1299))
  t1309 = f.my_piecewise3(t7, 0, t1161)
  t1313 = f.my_piecewise3(t7, 0, -t768 * t1161 / 0.3e1)
  t1315 = t223 * t37 * t1313
  t1318 = (-t767 + 0.33220412950000000000000000000000000000000000000000e-2 * t1315) * t251
  t1319 = -t781 + t1315
  t1320 = t780 * t1319
  t1323 = t787 * t1319
  t1327 = t239 * t243 * t227 * t1313
  t1331 = t779 * (0.11807781499500000000000000000000000000000000000000e0 * t1320 - t785 + 0.55770497660000000000000000000000000000000000000000e-1 * t1315 + 0.19099794277500000000000000000000000000000000000000e-1 * t1323 - t795 + 0.15325849658000000000000000000000000000000000000000e-1 * t1327) * t801
  t1344 = (-t821 + 0.93933381250000000000000000000000000000000000000000e-3 * t1315) * t280
  t1350 = 0.87448811650000000000000000000000000000000000000000e-1 * t1320 - t830 + 0.30591463695000000000000000000000000000000000000000e-1 * t1315 + 0.55743234727500000000000000000000000000000000000000e-2 * t1323 - t833 + 0.83878920990000000000000000000000000000000000000000e-2 * t1327
  t1366 = f.my_piecewise3(t8, 0, t1309 * t287 / 0.2e1 + t221 * (-t1318 + t1331 + t259 * (-(-t804 + 0.15971292590000000000000000000000000000000000000000e-2 * t1315) * t269 + t810 * (0.10974162105750000000000000000000000000000000000000e0 * t1320 - t812 + 0.48172707847500000000000000000000000000000000000000e-1 * t1315 + 0.19623283938750000000000000000000000000000000000000e-1 * t1323 - t815 + 0.97184864595000000000000000000000000000000000000000e-2 * t1327) * t818 + t1318 - t1331 - 0.58482236226346462072622386637590534819724553404281e0 * t1344 + 0.58482236226346462072622386637590534819724553404281e0 * t828 * t1350 * t836) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t1344 - 0.58482236226346462072622386637590534819724553404281e0 * t844 * t827 * t1350 * t836) / 0.2e1)
  t1368 = f.my_piecewise3(t133, 0, t1226)
  t1372 = f.my_piecewise3(t133, 0, -t925 * t1226 / 0.3e1)
  t1374 = t223 * t37 * t1372
  t1377 = (-t924 + 0.33220412950000000000000000000000000000000000000000e-2 * t1374) * t356
  t1378 = -t938 + t1374
  t1379 = t937 * t1378
  t1382 = t944 * t1378
  t1386 = t239 * t243 * t339 * t1372
  t1390 = t936 * (0.11807781499500000000000000000000000000000000000000e0 * t1379 - t942 + 0.55770497660000000000000000000000000000000000000000e-1 * t1374 + 0.19099794277500000000000000000000000000000000000000e-1 * t1382 - t949 + 0.15325849658000000000000000000000000000000000000000e-1 * t1386) * t955
  t1403 = (-t975 + 0.93933381250000000000000000000000000000000000000000e-3 * t1374) * t378
  t1409 = 0.87448811650000000000000000000000000000000000000000e-1 * t1379 - t984 + 0.30591463695000000000000000000000000000000000000000e-1 * t1374 + 0.55743234727500000000000000000000000000000000000000e-2 * t1382 - t987 + 0.83878920990000000000000000000000000000000000000000e-2 * t1386
  t1425 = f.my_piecewise3(t134, 0, t1368 * t385 / 0.2e1 + t336 * (-t1377 + t1390 + t259 * (-(-t958 + 0.15971292590000000000000000000000000000000000000000e-2 * t1374) * t367 + t964 * (0.10974162105750000000000000000000000000000000000000e0 * t1379 - t966 + 0.48172707847500000000000000000000000000000000000000e-1 * t1374 + 0.19623283938750000000000000000000000000000000000000e-1 * t1382 - t969 + 0.97184864595000000000000000000000000000000000000000e-2 * t1386) * t972 + t1377 - t1390 - 0.58482236226346462072622386637590534819724553404281e0 * t1403 + 0.58482236226346462072622386637590534819724553404281e0 * t982 * t1409 * t990) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t1403 - 0.58482236226346462072622386637590534819724553404281e0 * t998 * t981 * t1409 * t990) / 0.2e1)
  t1431 = 0.1e1 / t411
  t1440 = t302 * t210
  t1444 = 0.1e1 / t400 / t212
  t1449 = t409 * r1
  t1450 = 0.1e1 / t1449
  t1455 = t404 * t403 * s2
  t1459 = 0.1e1 / t197 / t409 / t1279
  t1462 = 0.1e1 / t412 / t411 / t391
  t1468 = t324 * t398 * t210 * t421
  t1471 = 0.1e1 / t197 / t409 / t195
  t1472 = t405 * t1471
  t1474 = t1472 * t414 * tau1
  t1479 = t419 / t420 / t212
  t1490 = -0.12510406256540438400000000000000000000000000000000e1 * t389 * t1281 * t392 + 0.58691349263882304531366500424072960000000000000000e0 * t291 * t403 * t1288 * t1431 + 0.5e1 / 0.3e1 * t299 * tau1 * t1295 + 0.5e1 / 0.3e1 * t396 * t1299 + 0.10e2 / 0.3e1 * t1440 * t1299 + 0.10e2 / 0.3e1 * t399 * t1444 * tau1 * t199 - 0.17058312527037532641093798337249884644806500957667e0 * t406 * t1450 * t414 + 0.80027407411602181735783566855612697994614340830460e-1 * t308 * t1455 * t1459 * t1462 + 0.71076302195989719337890826405207852686693753990280e-1 * t1468 * t1474 + 0.71076302195989719337890826405207852686693753990280e-1 * t1479 * t1474 - 0.17058312527037532641093798337249884644806500957667e0 * t422 * t405 * t1450 * t414 + 0.80027407411602181735783566855612697994614340830460e-1 * t422 * t1455 * t1459 * t1462
  t1494 = f.my_piecewise3(t7, 0, 0.4e1 / 0.3e1 * t225 * t1161)
  t1497 = f.my_piecewise3(t133, 0, 0.4e1 / 0.3e1 * t337 * t1226)
  t1499 = (t1494 + t1497) * t258
  t1504 = t1012 + t1033 - t1037 - t1042 + t451 * t1499 * t481 + t1084 + 0.58482236226346462072622386637590534819724553404281e0 * t1499 * t479 - t1091 - t1096 - t1366 - t1425
  t1506 = tau1 * t199
  t1508 = t115 * t1506 / 0.2e1
  t1510 = 0.10e2 / 0.3e1 * t119 * t1506
  t1511 = -t1508 + t1510
  t1515 = -t1508 - t1510
  t1525 = t1127 * t1511
  t1528 = t1127 * t1515
  t1532 = t1143 * s2 * t1281
  vrho_1_ = t130 + t220 + t335 + t428 + t528 + t3 * (t1220 + t1308 + t1366 * t334 + t1425 * t427 + t388 * t1490 + t1504 * t527 + t486 * (0.2e1 * t1099 * t499 * t1511 - 0.2e1 * t496 * t1110 * t1515 + 0.6e1 * t1116 * t507 * t1511 - 0.6e1 * t504 * t1121 * t1515 + 0.3e1 * t1126 * t1525 - 0.3e1 * t1131 * t1528 - 0.4e1 / 0.9e1 * t1140 * t1532 + t1149 * t1525 - t1151 * t1528 - 0.4e1 / 0.9e1 * t1154 * t1532))
  t1548 = 0.1e1 / t98 / t313 / r0
  t1557 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t19 * t26 * t93 * (0.3840616724010807e-2 * t95 * t101 * t105 - 0.14750336820751503265872652791249e-4 * t96 * t1548 * t646))
  t1564 = t310 * s0
  t1580 = t510 * t507
  t1581 = t1138 * t1141
  t1583 = t1581 * t1142 * t101
  t1585 = t522 * t499
  vsigma_0_ = t3 * (t1557 + t290 * (0.46914023462026644e0 * t291 * t101 * t295 - 0.2200925597395586419926243765902736e0 * t292 * t1548 * t859 + 0.63968671976390747404101743764687067418024378591252e-1 * t308 * t1564 * t321 - 0.30010277779350818150918837570854761747980377811423e-1 * t312 * t899 * t890 + 0.63968671976390747404101743764687067418024378591252e-1 * t329 * t1564 * t316 * t320 - 0.30010277779350818150918837570854761747980377811423e-1 * t329 * t900 * t890) + t486 * (t1580 * t1583 / 0.6e1 + t1585 * t1583 / 0.6e1))
  vsigma_1_ = 0.0e0
  t1596 = 0.1e1 / t196 / t407 / r1
  t1605 = f.my_piecewise3(t134, 0, -0.3e1 / 0.32e2 * t137 * t26 * t193 * (0.3840616724010807e-2 * t95 * t199 * t203 - 0.14750336820751503265872652791249e-4 * t194 * t1596 * t1290))
  t1612 = t404 * s2
  t1629 = t1581 * t1142 * t199
  vsigma_2_ = t3 * (t1605 + t388 * (0.46914023462026644e0 * t291 * t199 * t392 - 0.2200925597395586419926243765902736e0 * t389 * t1596 * t1431 + 0.63968671976390747404101743764687067418024378591252e-1 * t308 * t1612 * t415 - 0.30010277779350818150918837570854761747980377811423e-1 * t406 * t1471 * t1462 + 0.63968671976390747404101743764687067418024378591252e-1 * t422 * t1612 * t410 * t414 - 0.30010277779350818150918837570854761747980377811423e-1 * t422 * t1472 * t1462) + t486 * (t1580 * t1629 / 0.6e1 + t1585 * t1629 / 0.6e1))
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t1638 = t306 * t118
  t1645 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t19 * t26 * t93 * (-t109 * t118 * t123 - t121 * t1638))
  t1657 = t311 / t99 / t877 * t320
  t1665 = 0.3e1 / 0.10e2 * t115 * t118
  t1668 = 0.2e1 * t118 * tau1 * t208
  t1669 = t1665 - t1668
  t1673 = t1665 + t1668
  t1683 = t1127 * t1669
  t1686 = t1127 * t1673
  vtau_0_ = t3 * (t1645 + t290 * (-t299 * t118 * t123 - t300 * t1638 - 0.2e1 * t868 * t1638 - 0.2e1 * t304 * t872 * t118 - 0.42645781317593831602734495843124711612016252394168e-1 * t896 * t1657 - 0.42645781317593831602734495843124711612016252394168e-1 * t907 * t1657) + t486 * (0.2e1 * t1099 * t499 * t1669 - 0.2e1 * t496 * t1110 * t1673 + 0.6e1 * t1116 * t507 * t1669 - 0.6e1 * t504 * t1121 * t1673 + 0.3e1 * t1126 * t1683 - 0.3e1 * t1131 * t1686 + t1149 * t1683 - t1151 * t1686))
  t1696 = t401 * t208
  t1703 = f.my_piecewise3(t134, 0, -0.3e1 / 0.32e2 * t137 * t26 * t193 * (-t109 * t208 * t213 - t211 * t1696))
  t1715 = t405 / t197 / t1449 * t414
  t1723 = 0.3e1 / 0.10e2 * t115 * t208
  t1725 = 0.2e1 * t119 * t208
  t1726 = t1723 - t1725
  t1730 = t1723 + t1725
  t1740 = t1127 * t1726
  t1743 = t1127 * t1730
  vtau_1_ = t3 * (t1703 + t388 * (-t299 * t208 * t213 - t396 * t1696 - 0.2e1 * t1440 * t1696 - 0.2e1 * t399 * t1444 * t208 - 0.42645781317593831602734495843124711612016252394168e-1 * t1468 * t1715 - 0.42645781317593831602734495843124711612016252394168e-1 * t1479 * t1715) + t486 * (0.2e1 * t1099 * t499 * t1726 - 0.2e1 * t496 * t1110 * t1730 + 0.6e1 * t1116 * t507 * t1726 - 0.6e1 * t504 * t1121 * t1730 + 0.3e1 * t1126 * t1740 - 0.3e1 * t1131 * t1743 + t1149 * t1740 - t1151 * t1743))
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  vsigma_0_ = _b(vsigma_0_)
  vsigma_1_ = _b(vsigma_1_)
  vsigma_2_ = _b(vsigma_2_)
  vlapl_0_ = _b(vlapl_0_)
  vlapl_1_ = _b(vlapl_1_)
  vtau_0_ = _b(vtau_0_)
  vtau_1_ = _b(vtau_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1), 'vsigma': jnp.stack([vsigma_0_, vsigma_1_, vsigma_2_], axis=-1), 'vlapl': jnp.stack([vlapl_0_, vlapl_1_], axis=-1), 'vtau':  jnp.stack([vtau_0_, vtau_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_c_os_raw = params.c_os
  if isinstance(params_c_os_raw, (str, bytes, dict)):
    params_c_os = params_c_os_raw
  else:
    try:
      params_c_os_seq = list(params_c_os_raw)
    except TypeError:
      params_c_os = params_c_os_raw
    else:
      params_c_os_seq = np.asarray(params_c_os_seq, dtype=np.float64)
      params_c_os = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_os_seq))
  params_c_ss_raw = params.c_ss
  if isinstance(params_c_ss_raw, (str, bytes, dict)):
    params_c_ss = params_c_ss_raw
  else:
    try:
      params_c_ss_seq = list(params_c_ss_raw)
    except TypeError:
      params_c_ss = params_c_ss_raw
    else:
      params_c_ss_seq = np.asarray(params_c_ss_seq, dtype=np.float64)
      params_c_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_ss_seq))
  params_c_x_raw = params.c_x
  if isinstance(params_c_x_raw, (str, bytes, dict)):
    params_c_x = params_c_x_raw
  else:
    try:
      params_c_x_seq = list(params_c_x_raw)
    except TypeError:
      params_c_x = params_c_x_raw
    else:
      params_c_x_seq = np.asarray(params_c_x_seq, dtype=np.float64)
      params_c_x = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_x_seq))

  b97mv_par_n = 5

  b97mv_gamma_x = 0.003840616724010807

  b97mv_par_x = [None, np.array([np.nan, params_c_x[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_x[2], 0, 1], dtype=np.float64), np.array([np.nan, params_c_x[3], 1, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_ss = 0.46914023462026644

  b97mv_par_ss = [None, np.array([np.nan, params_c_ss[1], 0, 1], dtype=np.float64), np.array([np.nan, params_c_ss[2], 1, 0], dtype=np.float64), np.array([np.nan, params_c_ss[3], 2, 0], dtype=np.float64), np.array([np.nan, params_c_ss[4], 0, 6], dtype=np.float64), np.array([np.nan, params_c_ss[5], 4, 6], dtype=np.float64)]

  b97mv_gamma_os = 0.006

  b97mv_par_os = [None, np.array([np.nan, params_c_os[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_os[2], 2, 0], dtype=np.float64), np.array([np.nan, params_c_os[3], 6, 0], dtype=np.float64), np.array([np.nan, params_c_os[4], 6, 2 / 3], dtype=np.float64), np.array([np.nan, params_c_os[5], 2, 2 / 3], dtype=np.float64)]

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  lda_x_ax = -f.RS_FACTOR * X_FACTOR_C / 2 ** (4 / 3)

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  b97mv_ux = lambda mgamma, x: mgamma * x ** 2 / (1 + mgamma * x ** 2)

  b97mv_ux_os = lambda mgamma, x: x

  b97mv_wx_ss = lambda t, dummy=None: (K_FACTOR_C - t) / (K_FACTOR_C + t)

  b97mv_wx_os = lambda ts0, ts1: (K_FACTOR_C * (ts0 + ts1) - 2 * ts0 * ts1) / (K_FACTOR_C * (ts0 + ts1) + 2 * ts0 * ts1)

  b97mv_g = lambda mgamma, wx, ux, cc, n, xs, ts0, ts1: jnp.sum(jnp.array([cc[i][1] * wx(ts0, ts1) ** cc[i][2] * ux(mgamma, xs) ** cc[i][3] for i in range(1, n + 1)]), axis=0)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  b97mv_ux_ss = lambda mgamma, x: b97mv_ux(mgamma, x)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  lda_x_erf_spin = lambda rs, z: lda_x_ax * f.opz_pow_n(z, 4 / 3) / rs * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3))

  b97mv_fpar = lambda rs, z, xs0, xs1, ts0, ts1: +lda_stoll_par(f, params, f_pw, rs, z, 1) * b97mv_g(b97mv_gamma_ss, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_ss, b97mv_par_n, xs0, ts0, 0) + lda_stoll_par(f, params, f_pw, rs, -z, -1) * b97mv_g(b97mv_gamma_ss, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_ss, b97mv_par_n, xs1, ts1, 0)

  b97mv_fos = lambda rs, z, xs0, xs1, ts0, ts1: lda_stoll_perp(f, params, f_pw, rs, z) * b97mv_g(b97mv_gamma_os, b97mv_wx_os, b97mv_ux_os, b97mv_par_os, b97mv_par_n, jnp.sqrt(xs0 ** 2 + xs1 ** 2) / jnp.sqrt(2), ts0, ts1)

  wb97mv_f = lambda rs, z, xs0, xs1, ts0, ts1: f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, (1 + z) / 2 * lda_x_erf_spin(rs * (2 / (1 + z)) ** (1 / 3), 1) * b97mv_g(b97mv_gamma_x, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_x, b97mv_par_n, xs0, ts0, 0)) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, (1 - z) / 2 * lda_x_erf_spin(rs * (2 / (1 - z)) ** (1 / 3), 1) * b97mv_g(b97mv_gamma_x, b97mv_wx_ss, b97mv_ux_ss, b97mv_par_x, b97mv_par_n, xs1, ts1, 0))

  b97mv_f = lambda rs, z, xs0, xs1, ts0, ts1: +b97mv_fpar(rs, z, xs0, xs1, ts0, ts1) + b97mv_fos(rs, z, xs0, xs1, ts0, ts1)

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: wb97mv_f(rs, z, xs0, xs1, ts0, ts1) + b97mv_f(rs, z, xs0, xs1, ts0, ts1)

  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = r0 / 0.2e1 <= f.p.dens_threshold or t3
  t5 = 3 ** (0.1e1 / 0.3e1)
  t7 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t8 = t5 * t7
  t9 = 4 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = 2 ** (0.1e1 / 0.3e1)
  t13 = t8 * t10 * t11
  t14 = 0.2e1 <= f.p.zeta_threshold
  t15 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t16 = t15 * f.p.zeta_threshold
  t18 = f.my_piecewise3(t14, t16, 0.2e1 * t11)
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t18 * t19
  t21 = 9 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = t7 ** 2
  t25 = t22 * t23 * f.p.cam_omega
  t26 = 0.1e1 / t19
  t28 = f.my_piecewise3(t14, t15, t11)
  t30 = t11 / t28
  t33 = t25 * t5 * t26 * t30 / 0.18e2
  t34 = 0.135e1 <= t33
  t35 = 0.135e1 < t33
  t36 = f.my_piecewise3(t35, t33, 0.135e1)
  t37 = t36 ** 2
  t40 = t37 ** 2
  t43 = t40 * t37
  t46 = t40 ** 2
  t58 = t46 ** 2
  t62 = f.my_piecewise3(t35, 0.135e1, t33)
  t63 = jnp.sqrt(jnp.pi)
  t64 = 0.1e1 / t62
  t66 = jax.lax.erf(t64 / 0.2e1)
  t68 = t62 ** 2
  t69 = 0.1e1 / t68
  t71 = jnp.exp(-t69 / 0.4e1)
  t72 = t71 - 0.1e1
  t75 = t71 - 0.3e1 / 0.2e1 - 0.2e1 * t68 * t72
  t78 = 0.2e1 * t62 * t75 + t63 * t66
  t82 = f.my_piecewise3(t34, 0.1e1 / t37 / 0.36e2 - 0.1e1 / t40 / 0.960e3 + 0.1e1 / t43 / 0.26880e5 - 0.1e1 / t46 / 0.829440e6 + 0.1e1 / t46 / t37 / 0.28385280e8 - 0.1e1 / t46 / t40 / 0.1073479680e10 + 0.1e1 / t46 / t43 / 0.44590694400e11 - 0.1e1 / t58 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t62 * t78)
  t84 = params.c_x[1]
  t85 = t84 * s0
  t86 = t11 ** 2
  t87 = r0 ** 2
  t88 = t19 ** 2
  t90 = 0.1e1 / t88 / t87
  t91 = t86 * t90
  t93 = s0 * t86 * t90
  t95 = 0.1e1 + 0.3840616724010807e-2 * t93
  t96 = 0.1e1 / t95
  t100 = params.c_x[2]
  t101 = 6 ** (0.1e1 / 0.3e1)
  t102 = t101 ** 2
  t103 = jnp.pi ** 2
  t104 = t103 ** (0.1e1 / 0.3e1)
  t105 = t104 ** 2
  t106 = t102 * t105
  t107 = 0.3e1 / 0.10e2 * t106
  t108 = tau0 * t86
  t110 = 0.1e1 / t88 / r0
  t111 = t108 * t110
  t112 = t107 - t111
  t113 = t100 * t112
  t114 = t107 + t111
  t115 = 0.1e1 / t114
  t117 = params.c_x[0] + 0.3840616724010807e-2 * t85 * t91 * t96 + t113 * t115
  t118 = t82 * t117
  t122 = f.my_piecewise3(t4, 0, -0.3e1 / 0.64e2 * t13 * t20 * t118)
  t124 = f.my_piecewise3(t3, f.p.zeta_threshold, 1)
  t125 = t8 * t10
  t128 = f.my_piecewise3(t3, 0.1e1 / t15, 1)
  t130 = t125 * t26 * t11 * t128
  t132 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t130
  t133 = jnp.sqrt(t130)
  t136 = t130 ** 0.15e1
  t138 = t5 ** 2
  t139 = t138 * t23
  t140 = t139 * t9
  t141 = 0.1e1 / t88
  t143 = t128 ** 2
  t145 = t140 * t141 * t86 * t143
  t147 = 0.23615562999000000000000000000000000000000000000000e0 * t133 + 0.55770497660000000000000000000000000000000000000000e-1 * t130 + 0.12733196185000000000000000000000000000000000000000e-1 * t136 + 0.76629248290000000000000000000000000000000000000000e-2 * t145
  t149 = 0.1e1 + 0.1e1 / t147
  t150 = jnp.log(t149)
  t151 = t132 * t150
  t153 = f.my_piecewise3(0.0e0 <= f.p.zeta_threshold, t16, 0)
  t157 = 0.1e1 / (0.2e1 * t11 - 0.2e1)
  t158 = (t18 + t153 - 0.2e1) * t157
  t160 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t130
  t165 = 0.21948324211500000000000000000000000000000000000000e0 * t133 + 0.48172707847500000000000000000000000000000000000000e-1 * t130 + 0.13082189292500000000000000000000000000000000000000e-1 * t136 + 0.48592432297500000000000000000000000000000000000000e-2 * t145
  t167 = 0.1e1 + 0.1e1 / t165
  t168 = jnp.log(t167)
  t171 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t130
  t176 = 0.17489762330000000000000000000000000000000000000000e0 * t133 + 0.30591463695000000000000000000000000000000000000000e-1 * t130 + 0.37162156485000000000000000000000000000000000000000e-2 * t136 + 0.41939460495000000000000000000000000000000000000000e-2 * t145
  t178 = 0.1e1 + 0.1e1 / t176
  t179 = jnp.log(t178)
  t180 = t171 * t179
  t189 = f.my_piecewise3(t4, 0, t124 * (-t151 + t158 * (-t160 * t168 + t151 - 0.58482236226346462072622386637590534819724553404281e0 * t180) + 0.58482236226346462072622386637590534819724553404281e0 * t158 * t180) / 0.2e1)
  t190 = params.c_ss[0]
  t191 = t190 * s0
  t193 = 0.1e1 + 0.46914023462026644e0 * t93
  t194 = 0.1e1 / t193
  t198 = params.c_ss[1]
  t199 = t198 * t112
  t201 = params.c_ss[2]
  t202 = t112 ** 2
  t203 = t201 * t202
  t204 = t114 ** 2
  t205 = 0.1e1 / t204
  t207 = params.c_ss[3]
  t208 = s0 ** 2
  t209 = t208 ** 2
  t210 = t209 * t208
  t211 = t207 * t210
  t212 = t87 ** 2
  t213 = t212 ** 2
  t214 = t213 ** 2
  t215 = 0.1e1 / t214
  t216 = t193 ** 2
  t217 = t216 ** 2
  t219 = 0.1e1 / t217 / t216
  t220 = t215 * t219
  t223 = params.c_ss[4]
  t224 = t202 ** 2
  t225 = t223 * t224
  t226 = t204 ** 2
  t227 = 0.1e1 / t226
  t228 = t225 * t227
  t233 = 0.46914023462026644e0 * t191 * t91 * t194 + t199 * t115 + t203 * t205 + 0.17058312527037532641093798337249884644806500957667e0 * t211 * t220 + 0.17058312527037532641093798337249884644806500957667e0 * t228 * t210 * t215 * t219
  t237 = t8 * t10 * t26
  t239 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t237
  t240 = jnp.sqrt(t237)
  t243 = t237 ** 0.15e1
  t246 = t139 * t9 * t141
  t248 = 0.23615562999000000000000000000000000000000000000000e0 * t240 + 0.55770497660000000000000000000000000000000000000000e-1 * t237 + 0.12733196185000000000000000000000000000000000000000e-1 * t243 + 0.76629248290000000000000000000000000000000000000000e-2 * t246
  t250 = 0.1e1 + 0.1e1 / t248
  t251 = jnp.log(t250)
  t253 = f.my_piecewise3(t3, t16, 1)
  t256 = (0.2e1 * t253 - 0.2e1) * t157
  t258 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t237
  t263 = 0.17489762330000000000000000000000000000000000000000e0 * t240 + 0.30591463695000000000000000000000000000000000000000e-1 * t237 + 0.37162156485000000000000000000000000000000000000000e-2 * t243 + 0.41939460495000000000000000000000000000000000000000e-2 * t246
  t265 = 0.1e1 + 0.1e1 / t263
  t266 = jnp.log(t265)
  t271 = -t239 * t251 + 0.58482236226346462072622386637590534819724553404281e0 * t256 * t258 * t266 - 0.2e1 * t189
  t273 = params.c_os[1]
  t275 = 0.3e1 / 0.5e1 * t106 * t111
  t276 = tau0 ** 2
  t277 = t276 * t11
  t278 = t87 * r0
  t280 = 0.1e1 / t19 / t278
  t282 = 0.4e1 * t277 * t280
  t283 = t275 - t282
  t284 = t283 ** 2
  t285 = t273 * t284
  t286 = t275 + t282
  t287 = t286 ** 2
  t288 = 0.1e1 / t287
  t290 = params.c_os[2]
  t291 = t284 ** 2
  t292 = t291 * t284
  t293 = t290 * t292
  t294 = t287 ** 2
  t296 = 0.1e1 / t294 / t287
  t298 = params.c_os[3]
  t299 = t298 * t292
  t300 = t93 ** (0.1e1 / 0.3e1)
  t301 = t296 * t300
  t303 = params.c_os[4]
  t304 = t303 * t284
  t305 = t288 * t300
  t307 = t285 * t288 + t293 * t296 + t299 * t301 + t304 * t305 + params.c_os[0]
  t313 = t37 * t36
  t316 = 0.1e1 / t19 / r0
  t320 = t25 * t5 * t316 * t30 / 0.54e2
  t321 = f.my_piecewise3(t35, -t320, 0)
  t324 = t40 * t36
  t328 = t40 * t313
  t353 = f.my_piecewise3(t35, 0, -t320)
  t376 = f.my_piecewise3(t34, -0.1e1 / t313 * t321 / 0.18e2 + 0.1e1 / t324 * t321 / 0.240e3 - 0.1e1 / t328 * t321 / 0.4480e4 + 0.1e1 / t46 / t36 * t321 / 0.103680e6 - 0.1e1 / t46 / t313 * t321 / 0.2838528e7 + 0.1e1 / t46 / t324 * t321 / 0.89456640e8 - 0.1e1 / t46 / t328 * t321 / 0.3185049600e10 + 0.1e1 / t58 / t36 * t321 / 0.126340300800e12, -0.8e1 / 0.3e1 * t353 * t78 - 0.8e1 / 0.3e1 * t62 * (-t71 * t69 * t353 + 0.2e1 * t353 * t75 + 0.2e1 * t62 * (0.1e1 / t68 / t62 * t353 * t71 / 0.2e1 - 0.4e1 * t62 * t72 * t353 - t64 * t353 * t71)))
  t383 = t86 / t88 / t278
  t391 = t11 / t19 / t212 / t87
  t392 = t95 ** 2
  t393 = 0.1e1 / t392
  t398 = t91 * t115
  t402 = t108 * t90
  t411 = f.my_piecewise3(t4, 0, -t13 * t18 * t141 * t118 / 0.64e2 - 0.3e1 / 0.64e2 * t13 * t20 * t376 * t117 - 0.3e1 / 0.64e2 * t13 * t20 * t82 * (-0.10241644597362152000000000000000000000000000000000e-1 * t85 * t383 * t96 + 0.78668463044008017417987481553328000000000000000000e-4 * t84 * t208 * t391 * t393 + 0.5e1 / 0.3e1 * t100 * tau0 * t398 + 0.5e1 / 0.3e1 * t113 * t205 * t402))
  t413 = t316 * t11
  t417 = 0.11073470983333333333333333333333333333333333333333e-2 * t125 * t413 * t128 * t150
  t418 = t147 ** 2
  t424 = t10 * t316
  t425 = t11 * t128
  t426 = t424 * t425
  t427 = 0.1e1 / t133 * t5 * t7 * t426
  t430 = t125 * t413 * t128
  t432 = t130 ** 0.5e0
  t435 = t432 * t5 * t7 * t426
  t437 = t110 * t86
  t439 = t140 * t437 * t143
  t444 = t132 / t418 * (-0.39359271665000000000000000000000000000000000000000e-1 * t427 - 0.18590165886666666666666666666666666666666666666667e-1 * t430 - 0.63665980925000000000000000000000000000000000000000e-2 * t435 - 0.51086165526666666666666666666666666666666666666667e-2 * t439) / t149
  t449 = t165 ** 2
  t464 = t176 ** 2
  t465 = 0.1e1 / t464
  t471 = -0.29149603883333333333333333333333333333333333333333e-1 * t427 - 0.10197154565000000000000000000000000000000000000000e-1 * t430 - 0.18581078242500000000000000000000000000000000000000e-2 * t435 - 0.27959640330000000000000000000000000000000000000000e-2 * t439
  t472 = 0.1e1 / t178
  t491 = f.my_piecewise3(t4, 0, t124 * (t417 + t444 + t158 * (0.53237641966666666666666666666666666666666666666667e-3 * t125 * t413 * t128 * t168 + t160 / t449 * (-0.36580540352500000000000000000000000000000000000000e-1 * t427 - 0.16057569282500000000000000000000000000000000000000e-1 * t430 - 0.65410946462500000000000000000000000000000000000000e-2 * t435 - 0.32394954865000000000000000000000000000000000000000e-2 * t439) / t167 - t417 - t444 + 0.18311447306006545054854346104378990962041954983034e-3 * t125 * t413 * t128 * t179 + 0.58482236226346462072622386637590534819724553404281e0 * t171 * t465 * t471 * t472) - 0.18311447306006545054854346104378990962041954983034e-3 * t158 * t8 * t424 * t425 * t179 - 0.58482236226346462072622386637590534819724553404281e0 * t158 * t171 * t465 * t471 * t472) / 0.2e1)
  t498 = 0.1e1 / t216
  t508 = t201 * t112
  t513 = 0.1e1 / t204 / t114
  t517 = t214 * r0
  t518 = 0.1e1 / t517
  t523 = t209 * t208 * s0
  t527 = 0.1e1 / t88 / t214 / t278
  t530 = 0.1e1 / t217 / t216 / t193
  t536 = t223 * t202 * t112
  t541 = 0.1e1 / t88 / t214 / t87
  t543 = t541 * t219 * t108
  t547 = 0.1e1 / t226 / t114
  t557 = t530 * t86
  t561 = -0.12510406256540438400000000000000000000000000000000e1 * t191 * t383 * t194 + 0.11738269852776460906273300084814592000000000000000e1 * t190 * t208 * t391 * t498 + 0.5e1 / 0.3e1 * t198 * tau0 * t398 + 0.5e1 / 0.3e1 * t199 * t205 * t402 + 0.10e2 / 0.3e1 * t508 * t205 * t402 + 0.10e2 / 0.3e1 * t203 * t513 * t402 - 0.27293300043260052225750077339599815431690401532267e1 * t211 * t518 * t219 + 0.12804385185856349077725370696898031679138294532873e1 * t207 * t523 * t527 * t530 * t86 + 0.11372208351358355094062532224833256429871000638445e1 * t536 * t227 * t210 * t543 + 0.11372208351358355094062532224833256429871000638445e1 * t225 * t547 * t210 * t543 - 0.27293300043260052225750077339599815431690401532267e1 * t228 * t210 * t518 * t219 + 0.12804385185856349077725370696898031679138294532873e1 * t228 * t523 * t527 * t557
  t567 = t248 ** 2
  t572 = t7 * t10
  t573 = t572 * t316
  t574 = 0.1e1 / t240 * t5 * t573
  t576 = t8 * t424
  t578 = t237 ** 0.5e0
  t580 = t578 * t5 * t573
  t583 = t139 * t9 * t110
  t595 = t263 ** 2
  t610 = t273 * t283
  t611 = t106 * t402
  t615 = 0.40e2 / 0.3e1 * t277 / t19 / t212
  t616 = -t611 + t615
  t620 = t287 * t286
  t621 = 0.1e1 / t620
  t622 = -t611 - t615
  t626 = t291 * t283
  t627 = t290 * t626
  t632 = 0.1e1 / t294 / t620
  t636 = t298 * t626
  t640 = t632 * t300
  t644 = t299 * t296
  t645 = t300 ** 2
  t646 = 0.1e1 / t645
  t648 = t646 * s0 * t383
  t651 = t303 * t283
  t655 = t621 * t300
  t659 = t304 * t288
  vrho_0_ = 0.2e1 * t122 + 0.2e1 * t189 * t233 + t271 * t307 + r0 * (0.2e1 * t411 + 0.2e1 * t491 * t233 + 0.2e1 * t189 * t561 + (0.11073470983333333333333333333333333333333333333333e-2 * t8 * t424 * t251 + t239 / t567 * (-0.39359271665000000000000000000000000000000000000000e-1 * t574 - 0.18590165886666666666666666666666666666666666666667e-1 * t576 - 0.63665980925000000000000000000000000000000000000000e-2 * t580 - 0.51086165526666666666666666666666666666666666666667e-2 * t583) / t250 - 0.18311447306006545054854346104378990962041954983034e-3 * t256 * t5 * t572 * t316 * t266 - 0.58482236226346462072622386637590534819724553404281e0 * t256 * t258 / t595 * (-0.29149603883333333333333333333333333333333333333333e-1 * t574 - 0.10197154565000000000000000000000000000000000000000e-1 * t576 - 0.18581078242500000000000000000000000000000000000000e-2 * t580 - 0.27959640330000000000000000000000000000000000000000e-2 * t583) / t265 - 0.2e1 * t491) * t307 + t271 * (0.2e1 * t610 * t288 * t616 - 0.2e1 * t285 * t621 * t622 + 0.6e1 * t627 * t296 * t616 - 0.6e1 * t293 * t632 * t622 + 0.6e1 * t636 * t301 * t616 - 0.6e1 * t299 * t640 * t622 - 0.8e1 / 0.9e1 * t644 * t648 + 0.2e1 * t651 * t305 * t616 - 0.2e1 * t304 * t655 * t622 - 0.8e1 / 0.9e1 * t659 * t648))
  t673 = t11 / t19 / t212 / r0
  t682 = f.my_piecewise3(t4, 0, -0.3e1 / 0.64e2 * t13 * t20 * t82 * (0.3840616724010807e-2 * t84 * t86 * t90 * t96 - 0.29500673641503006531745305582498e-4 * t85 * t673 * t393))
  t691 = t209 * s0
  t711 = t646 * t86 * t90
  vsigma_0_ = r0 * (0.2e1 * t682 + 0.2e1 * t189 * (0.46914023462026644e0 * t190 * t86 * t90 * t194 - 0.4401851194791172839852487531805472e0 * t191 * t673 * t498 + 0.10234987516222519584656279002349930786883900574600e1 * t207 * t691 * t220 - 0.48016444446961309041470140113367618796768604498275e0 * t211 * t541 * t530 * t86 + 0.10234987516222519584656279002349930786883900574600e1 * t228 * t691 * t215 * t219 - 0.48016444446961309041470140113367618796768604498275e0 * t228 * t210 * t541 * t557) + t271 * (t644 * t711 / 0.3e1 + t659 * t711 / 0.3e1))
  vlapl_0_ = 0.0e0
  t719 = t110 * t115
  t722 = t205 * t86 * t110
  t729 = f.my_piecewise3(t4, 0, -0.3e1 / 0.64e2 * t13 * t20 * t82 * (-t100 * t86 * t719 - t113 * t722))
  t745 = t210 / t88 / t517 * t219 * t86
  t755 = 0.3e1 / 0.5e1 * t106 * t437
  t758 = 0.8e1 * tau0 * t11 * t280
  t759 = t755 - t758
  t763 = t755 + t758
  vtau_0_ = r0 * (0.2e1 * t729 + 0.2e1 * t189 * (-t198 * t86 * t719 - t199 * t722 - 0.2e1 * t508 * t722 - 0.2e1 * t203 * t513 * t86 * t110 - 0.68233250108150130564375193348999538579226003830668e0 * t536 * t227 * t745 - 0.68233250108150130564375193348999538579226003830668e0 * t225 * t547 * t745) + t271 * (-0.2e1 * t285 * t621 * t763 + 0.2e1 * t610 * t288 * t759 - 0.6e1 * t293 * t632 * t763 + 0.6e1 * t627 * t296 * t759 - 0.6e1 * t299 * t640 * t763 + 0.6e1 * t636 * t301 * t759 - 0.2e1 * t304 * t655 * t763 + 0.2e1 * t651 * t305 * t759))
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = r0 / 0.2e1 <= f.p.dens_threshold or t3
  t5 = 3 ** (0.1e1 / 0.3e1)
  t7 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t8 = t5 * t7
  t9 = 4 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = 2 ** (0.1e1 / 0.3e1)
  t13 = t8 * t10 * t11
  t14 = 0.2e1 <= f.p.zeta_threshold
  t15 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t16 = t15 * f.p.zeta_threshold
  t18 = f.my_piecewise3(t14, t16, 0.2e1 * t11)
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t22 = t18 * t21
  t23 = 9 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = t7 ** 2
  t27 = t24 * t25 * f.p.cam_omega
  t28 = 0.1e1 / t19
  t30 = f.my_piecewise3(t14, t15, t11)
  t32 = t11 / t30
  t35 = t27 * t5 * t28 * t32 / 0.18e2
  t36 = 0.135e1 <= t35
  t37 = 0.135e1 < t35
  t38 = f.my_piecewise3(t37, t35, 0.135e1)
  t39 = t38 ** 2
  t42 = t39 ** 2
  t43 = 0.1e1 / t42
  t45 = t42 * t39
  t46 = 0.1e1 / t45
  t48 = t42 ** 2
  t49 = 0.1e1 / t48
  t52 = 0.1e1 / t48 / t39
  t55 = 0.1e1 / t48 / t42
  t58 = 0.1e1 / t48 / t45
  t60 = t48 ** 2
  t61 = 0.1e1 / t60
  t64 = f.my_piecewise3(t37, 0.135e1, t35)
  t65 = jnp.sqrt(jnp.pi)
  t66 = 0.1e1 / t64
  t68 = jnp.erf(t66 / 0.2e1)
  t70 = t64 ** 2
  t71 = 0.1e1 / t70
  t73 = jnp.exp(-t71 / 0.4e1)
  t74 = t73 - 0.1e1
  t77 = t73 - 0.3e1 / 0.2e1 - 0.2e1 * t70 * t74
  t80 = 0.2e1 * t64 * t77 + t65 * t68
  t84 = f.my_piecewise3(t36, 0.1e1 / t39 / 0.36e2 - t43 / 0.960e3 + t46 / 0.26880e5 - t49 / 0.829440e6 + t52 / 0.28385280e8 - t55 / 0.1073479680e10 + t58 / 0.44590694400e11 - t61 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t64 * t80)
  t86 = params.c_x[1]
  t87 = t86 * s0
  t88 = t11 ** 2
  t89 = r0 ** 2
  t91 = 0.1e1 / t20 / t89
  t92 = t88 * t91
  t94 = s0 * t88 * t91
  t96 = 0.1e1 + 0.3840616724010807e-2 * t94
  t97 = 0.1e1 / t96
  t101 = params.c_x[2]
  t102 = 6 ** (0.1e1 / 0.3e1)
  t103 = t102 ** 2
  t104 = jnp.pi ** 2
  t105 = t104 ** (0.1e1 / 0.3e1)
  t106 = t105 ** 2
  t107 = t103 * t106
  t108 = 0.3e1 / 0.10e2 * t107
  t109 = tau0 * t88
  t111 = 0.1e1 / t20 / r0
  t112 = t109 * t111
  t113 = t108 - t112
  t114 = t101 * t113
  t115 = t108 + t112
  t116 = 0.1e1 / t115
  t118 = params.c_x[0] + 0.3840616724010807e-2 * t87 * t92 * t97 + t114 * t116
  t119 = t84 * t118
  t123 = t18 * t19
  t124 = t39 * t38
  t125 = 0.1e1 / t124
  t127 = 0.1e1 / t19 / r0
  t131 = t27 * t5 * t127 * t32 / 0.54e2
  t132 = f.my_piecewise3(t37, -t131, 0)
  t135 = t42 * t38
  t136 = 0.1e1 / t135
  t139 = t42 * t124
  t140 = 0.1e1 / t139
  t144 = 0.1e1 / t48 / t38
  t148 = 0.1e1 / t48 / t124
  t152 = 0.1e1 / t48 / t135
  t156 = 0.1e1 / t48 / t139
  t160 = 0.1e1 / t60 / t38
  t164 = f.my_piecewise3(t37, 0, -t131)
  t166 = t73 * t71
  t171 = 0.1e1 / t70 / t64
  t175 = t64 * t74
  t180 = t171 * t164 * t73 / 0.2e1 - 0.4e1 * t175 * t164 - t66 * t164 * t73
  t183 = -t166 * t164 + 0.2e1 * t164 * t77 + 0.2e1 * t64 * t180
  t187 = f.my_piecewise3(t36, -t125 * t132 / 0.18e2 + t136 * t132 / 0.240e3 - t140 * t132 / 0.4480e4 + t144 * t132 / 0.103680e6 - t148 * t132 / 0.2838528e7 + t152 * t132 / 0.89456640e8 - t156 * t132 / 0.3185049600e10 + t160 * t132 / 0.126340300800e12, -0.8e1 / 0.3e1 * t164 * t80 - 0.8e1 / 0.3e1 * t64 * t183)
  t188 = t187 * t118
  t192 = t89 * r0
  t194 = 0.1e1 / t20 / t192
  t195 = t88 * t194
  t199 = s0 ** 2
  t200 = t86 * t199
  t201 = t89 ** 2
  t202 = t201 * t89
  t205 = t11 / t19 / t202
  t206 = t96 ** 2
  t207 = 0.1e1 / t206
  t211 = t101 * tau0
  t212 = t92 * t116
  t215 = t115 ** 2
  t216 = 0.1e1 / t215
  t217 = t114 * t216
  t218 = t109 * t91
  t221 = -0.10241644597362152000000000000000000000000000000000e-1 * t87 * t195 * t97 + 0.78668463044008017417987481553328000000000000000000e-4 * t200 * t205 * t207 + 0.5e1 / 0.3e1 * t211 * t212 + 0.5e1 / 0.3e1 * t217 * t218
  t222 = t84 * t221
  t227 = f.my_piecewise3(t4, 0, -t13 * t22 * t119 / 0.64e2 - 0.3e1 / 0.64e2 * t13 * t123 * t188 - 0.3e1 / 0.64e2 * t13 * t123 * t222)
  t229 = f.my_piecewise3(t3, f.p.zeta_threshold, 1)
  t230 = t8 * t10
  t231 = t127 * t11
  t233 = f.my_piecewise3(t3, 0.1e1 / t15, 1)
  t236 = t230 * t28 * t11 * t233
  t237 = jnp.sqrt(t236)
  t240 = t236 ** 0.15e1
  t242 = t5 ** 2
  t243 = t242 * t25
  t244 = t243 * t9
  t246 = t233 ** 2
  t248 = t244 * t21 * t88 * t246
  t250 = 0.37978500000000000000000000000000000000000000000000e1 * t237 + 0.89690000000000000000000000000000000000000000000000e0 * t236 + 0.20477500000000000000000000000000000000000000000000e0 * t240 + 0.12323500000000000000000000000000000000000000000000e0 * t248
  t253 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t250
  t254 = jnp.log(t253)
  t255 = t233 * t254
  t258 = 0.11073470983333333333333333333333333333333333333333e-2 * t230 * t231 * t255
  t260 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t236
  t261 = t250 ** 2
  t262 = 0.1e1 / t261
  t263 = t260 * t262
  t266 = 0.1e1 / t237 * t5 * t7
  t267 = t10 * t127
  t268 = t11 * t233
  t269 = t267 * t268
  t270 = t266 * t269
  t272 = t231 * t233
  t273 = t230 * t272
  t275 = t236 ** 0.5e0
  t277 = t275 * t5 * t7
  t278 = t277 * t269
  t282 = t244 * t111 * t88 * t246
  t284 = -0.63297500000000000000000000000000000000000000000000e0 * t270 - 0.29896666666666666666666666666666666666666666666667e0 * t273 - 0.10238750000000000000000000000000000000000000000000e0 * t278 - 0.82156666666666666666666666666666666666666666666667e-1 * t282
  t285 = 0.1e1 / t253
  t288 = 0.10000000000000000000000000000000000000000000000000e1 * t263 * t284 * t285
  t290 = f.my_piecewise3(0.0e0 <= f.p.zeta_threshold, t16, 0)
  t294 = 0.1e1 / (0.2e1 * t11 - 0.2e1)
  t295 = (t18 + t290 - 0.2e1) * t294
  t300 = 0.70594500000000000000000000000000000000000000000000e1 * t237 + 0.15494250000000000000000000000000000000000000000000e1 * t236 + 0.42077500000000000000000000000000000000000000000000e0 * t240 + 0.15629250000000000000000000000000000000000000000000e0 * t248
  t303 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t300
  t304 = jnp.log(t303)
  t305 = t233 * t304
  t310 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t236
  t311 = t300 ** 2
  t312 = 0.1e1 / t311
  t313 = t310 * t312
  t318 = -0.11765750000000000000000000000000000000000000000000e1 * t270 - 0.51647500000000000000000000000000000000000000000000e0 * t273 - 0.21038750000000000000000000000000000000000000000000e0 * t278 - 0.10419500000000000000000000000000000000000000000000e0 * t282
  t319 = 0.1e1 / t303
  t327 = 0.51785000000000000000000000000000000000000000000000e1 * t237 + 0.90577500000000000000000000000000000000000000000000e0 * t236 + 0.11003250000000000000000000000000000000000000000000e0 * t240 + 0.12417750000000000000000000000000000000000000000000e0 * t248
  t330 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t327
  t331 = jnp.log(t330)
  t332 = t233 * t331
  t337 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t236
  t338 = t327 ** 2
  t339 = 0.1e1 / t338
  t340 = t337 * t339
  t345 = -0.86308333333333333333333333333333333333333333333334e0 * t270 - 0.30192500000000000000000000000000000000000000000000e0 * t273 - 0.55016250000000000000000000000000000000000000000000e-1 * t278 - 0.82785000000000000000000000000000000000000000000000e-1 * t282
  t346 = 0.1e1 / t330
  t352 = t295 * t8
  t353 = t268 * t331
  t357 = t295 * t337
  t359 = t339 * t345 * t346
  t365 = f.my_piecewise3(t4, 0, t229 * (t258 + t288 + t295 * (0.53237641966666666666666666666666666666666666666666e-3 * t230 * t231 * t305 + 0.10000000000000000000000000000000000000000000000000e1 * t313 * t318 * t319 - t258 - t288 + 0.18311447306006545054854346104378990962041954983034e-3 * t230 * t231 * t332 + 0.58482236226346462072622386637590534819724553404280e0 * t340 * t345 * t346) - 0.18311447306006545054854346104378990962041954983034e-3 * t352 * t267 * t353 - 0.58482236226346462072622386637590534819724553404280e0 * t357 * t359) / 0.2e1)
  t366 = params.c_ss[0]
  t367 = t366 * s0
  t369 = 0.1e1 + 0.46914023462026644e0 * t94
  t370 = 0.1e1 / t369
  t374 = params.c_ss[1]
  t375 = t374 * t113
  t377 = params.c_ss[2]
  t378 = t113 ** 2
  t379 = t377 * t378
  t381 = params.c_ss[3]
  t382 = t199 ** 2
  t383 = t382 * t199
  t384 = t381 * t383
  t385 = t201 ** 2
  t386 = t385 ** 2
  t387 = 0.1e1 / t386
  t388 = t369 ** 2
  t389 = t388 ** 2
  t391 = 0.1e1 / t389 / t388
  t395 = params.c_ss[4]
  t396 = t378 ** 2
  t397 = t395 * t396
  t398 = t215 ** 2
  t399 = 0.1e1 / t398
  t400 = t397 * t399
  t405 = 0.46914023462026644e0 * t367 * t92 * t370 + t375 * t116 + t379 * t216 + 0.17058312527037532641093798337249884644806500957667e0 * t384 * t387 * t391 + 0.17058312527037532641093798337249884644806500957667e0 * t400 * t383 * t387 * t391
  t409 = 0.621814e-1 * t260 * t254
  t412 = t337 * t331
  t421 = f.my_piecewise3(t4, 0, t229 * (-t409 + t295 * (-0.3109070e-1 * t310 * t304 + t409 - 0.19751673498613801407483339618206552048944131217655e-1 * t412) + 0.19751673498613801407483339618206552048944131217655e-1 * t295 * t412) / 0.2e1)
  t425 = t366 * t199
  t426 = 0.1e1 / t388
  t430 = t374 * tau0
  t433 = t375 * t216
  t436 = t377 * t113
  t437 = t436 * t216
  t441 = 0.1e1 / t215 / t115
  t442 = t379 * t441
  t446 = 0.1e1 / t386 / r0
  t450 = t199 * s0
  t451 = t382 * t450
  t452 = t381 * t451
  t455 = 0.1e1 / t20 / t386 / t192
  t456 = t388 * t369
  t458 = 0.1e1 / t389 / t456
  t464 = t395 * t378 * t113
  t465 = t399 * t383
  t466 = t464 * t465
  t467 = t386 * t89
  t471 = 0.1e1 / t20 / t467 * t391 * t109
  t475 = 0.1e1 / t398 / t115
  t476 = t475 * t383
  t477 = t397 * t476
  t485 = t458 * t88
  t489 = -0.12510406256540438400000000000000000000000000000000e1 * t367 * t195 * t370 + 0.11738269852776460906273300084814592000000000000000e1 * t425 * t205 * t426 + 0.5e1 / 0.3e1 * t430 * t212 + 0.5e1 / 0.3e1 * t433 * t218 + 0.10e2 / 0.3e1 * t437 * t218 + 0.10e2 / 0.3e1 * t442 * t218 - 0.27293300043260052225750077339599815431690401532267e1 * t384 * t446 * t391 + 0.12804385185856349077725370696898031679138294532873e1 * t452 * t455 * t458 * t88 + 0.11372208351358355094062532224833256429871000638445e1 * t466 * t471 + 0.11372208351358355094062532224833256429871000638445e1 * t477 * t471 - 0.27293300043260052225750077339599815431690401532267e1 * t400 * t383 * t446 * t391 + 0.12804385185856349077725370696898031679138294532873e1 * t400 * t451 * t455 * t485
  t493 = t8 * t10 * t28
  t494 = jnp.sqrt(t493)
  t497 = t493 ** 0.15e1
  t500 = t243 * t9 * t21
  t502 = 0.37978500000000000000000000000000000000000000000000e1 * t494 + 0.89690000000000000000000000000000000000000000000000e0 * t493 + 0.20477500000000000000000000000000000000000000000000e0 * t497 + 0.12323500000000000000000000000000000000000000000000e0 * t500
  t505 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t502
  t506 = jnp.log(t505)
  t511 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t493
  t512 = t502 ** 2
  t513 = 0.1e1 / t512
  t514 = t511 * t513
  t516 = 0.1e1 / t494 * t5
  t517 = t7 * t10
  t518 = t517 * t127
  t519 = t516 * t518
  t521 = t8 * t267
  t523 = t493 ** 0.5e0
  t524 = t523 * t5
  t525 = t524 * t518
  t528 = t243 * t9 * t111
  t530 = -0.63297500000000000000000000000000000000000000000000e0 * t519 - 0.29896666666666666666666666666666666666666666666667e0 * t521 - 0.10238750000000000000000000000000000000000000000000e0 * t525 - 0.82156666666666666666666666666666666666666666666667e-1 * t528
  t531 = 0.1e1 / t505
  t532 = t530 * t531
  t535 = f.my_piecewise3(t3, t16, 1)
  t538 = (0.2e1 * t535 - 0.2e1) * t294
  t539 = t538 * t5
  t544 = 0.51785000000000000000000000000000000000000000000000e1 * t494 + 0.90577500000000000000000000000000000000000000000000e0 * t493 + 0.11003250000000000000000000000000000000000000000000e0 * t497 + 0.12417750000000000000000000000000000000000000000000e0 * t500
  t547 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t544
  t548 = jnp.log(t547)
  t554 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t493
  t555 = t538 * t554
  t556 = t544 ** 2
  t557 = 0.1e1 / t556
  t562 = -0.86308333333333333333333333333333333333333333333334e0 * t519 - 0.30192500000000000000000000000000000000000000000000e0 * t521 - 0.55016250000000000000000000000000000000000000000000e-1 * t525 - 0.82785000000000000000000000000000000000000000000000e-1 * t528
  t564 = 0.1e1 / t547
  t565 = t557 * t562 * t564
  t569 = 0.11073470983333333333333333333333333333333333333333e-2 * t8 * t267 * t506 + 0.10000000000000000000000000000000000000000000000000e1 * t514 * t532 - 0.18311447306006545054854346104378990962041954983034e-3 * t539 * t517 * t127 * t548 - 0.58482236226346462072622386637590534819724553404280e0 * t555 * t565 - 0.2e1 * t365
  t571 = params.c_os[1]
  t573 = 0.3e1 / 0.5e1 * t107 * t112
  t574 = tau0 ** 2
  t575 = t574 * t11
  t579 = 0.4e1 * t575 / t19 / t192
  t580 = t573 - t579
  t581 = t580 ** 2
  t582 = t571 * t581
  t583 = t573 + t579
  t584 = t583 ** 2
  t585 = 0.1e1 / t584
  t587 = params.c_os[2]
  t588 = t581 ** 2
  t589 = t588 * t581
  t590 = t587 * t589
  t591 = t584 ** 2
  t593 = 0.1e1 / t591 / t584
  t595 = params.c_os[3]
  t596 = t595 * t589
  t597 = t94 ** (0.1e1 / 0.3e1)
  t598 = t593 * t597
  t600 = params.c_os[4]
  t601 = t600 * t581
  t602 = t585 * t597
  t604 = t582 * t585 + t590 * t593 + t596 * t598 + t601 * t602 + params.c_os[0]
  t613 = -0.621814e-1 * t511 * t506 + 0.19751673498613801407483339618206552048944131217655e-1 * t538 * t554 * t548 - 0.2e1 * t421
  t614 = t571 * t580
  t615 = t107 * t218
  t619 = 0.40e2 / 0.3e1 * t575 / t19 / t201
  t620 = -t615 + t619
  t624 = t584 * t583
  t625 = 0.1e1 / t624
  t626 = -t615 - t619
  t630 = t588 * t580
  t631 = t587 * t630
  t636 = 0.1e1 / t591 / t624
  t640 = t595 * t630
  t644 = t636 * t597
  t648 = t596 * t593
  t649 = t597 ** 2
  t650 = 0.1e1 / t649
  t651 = t650 * s0
  t652 = t651 * t195
  t655 = t600 * t580
  t659 = t625 * t597
  t663 = t601 * t585
  t666 = 0.2e1 * t614 * t585 * t620 - 0.2e1 * t582 * t625 * t626 + 0.6e1 * t631 * t593 * t620 - 0.6e1 * t590 * t636 * t626 + 0.6e1 * t640 * t598 * t620 - 0.6e1 * t596 * t644 * t626 - 0.8e1 / 0.9e1 * t648 * t652 + 0.2e1 * t655 * t602 * t620 - 0.2e1 * t601 * t659 * t626 - 0.8e1 / 0.9e1 * t663 * t652
  t679 = t132 ** 2
  t683 = 0.1e1 / t19 / t89
  t687 = 0.2e1 / 0.81e2 * t27 * t5 * t683 * t32
  t688 = f.my_piecewise3(t37, t687, 0)
  t721 = t43 * t679 / 0.6e1 - t125 * t688 / 0.18e2 - t46 * t679 / 0.48e2 + t136 * t688 / 0.240e3 + t49 * t679 / 0.640e3 - t140 * t688 / 0.4480e4 - t52 * t679 / 0.11520e5 + t144 * t688 / 0.103680e6 + t55 * t679 / 0.258048e6 - t148 * t688 / 0.2838528e7 - t58 * t679 / 0.6881280e7 + t152 * t688 / 0.89456640e8 + t61 * t679 / 0.212336640e9 - t156 * t688 / 0.3185049600e10 - 0.1e1 / t60 / t39 * t679 / 0.7431782400e10 + t160 * t688 / 0.126340300800e12
  t722 = f.my_piecewise3(t37, 0, t687)
  t727 = t70 ** 2
  t730 = t164 ** 2
  t769 = f.my_piecewise3(t36, t721, -0.8e1 / 0.3e1 * t722 * t80 - 0.16e2 / 0.3e1 * t164 * t183 - 0.8e1 / 0.3e1 * t64 * (-0.1e1 / t727 / t64 * t730 * t73 / 0.2e1 + 0.2e1 * t73 * t171 * t730 - t166 * t722 + 0.2e1 * t722 * t77 + 0.4e1 * t164 * t180 + 0.2e1 * t64 * (-0.2e1 / t727 * t730 * t73 + t171 * t722 * t73 / 0.2e1 + 0.1e1 / t727 / t70 * t730 * t73 / 0.4e1 - 0.4e1 * t730 * t74 - t71 * t730 * t73 - 0.4e1 * t175 * t722 - t66 * t722 * t73)))
  t780 = t88 / t20 / t201
  t784 = t201 * t192
  t787 = t11 / t19 / t784
  t793 = 0.1e1 / t385 / t89
  t799 = t195 * t116
  t803 = t201 * r0
  t805 = 0.1e1 / t19 / t803
  t807 = t11 * t805 * t216
  t811 = t575 * t805
  t814 = t109 * t194
  t823 = f.my_piecewise3(t4, 0, t13 * t18 * t111 * t119 / 0.96e2 - t13 * t22 * t188 / 0.32e2 - t13 * t22 * t222 / 0.32e2 - 0.3e1 / 0.64e2 * t13 * t123 * t769 * t118 - 0.3e1 / 0.32e2 * t13 * t123 * t187 * t221 - 0.3e1 / 0.64e2 * t13 * t123 * t84 * (0.37552696856994557333333333333333333333333333333333e-1 * t87 * t780 * t97 - 0.70801616739607215676188733397995200000000000000000e-3 * t200 * t787 * t207 + 0.32227777580697953041677078903529515239532673674240e-5 * t86 * t450 * t793 / t206 / t96 - 0.40e2 / 0.9e1 * t211 * t799 + 0.100e3 / 0.9e1 * t101 * t574 * t807 + 0.100e3 / 0.9e1 * t114 * t441 * t811 - 0.40e2 / 0.9e1 * t217 * t814))
  t825 = t683 * t11
  t828 = 0.14764627977777777777777777777777777777777777777777e-2 * t230 * t825 * t255
  t833 = 0.35616666666666666666666666666666666666666666666666e-1 * t521 * t268 * t262 * t284 * t285
  t837 = t284 ** 2
  t840 = 0.20000000000000000000000000000000000000000000000000e1 * t260 / t261 / t250 * t837 * t285
  t845 = t9 * t91
  t847 = t845 * t88 * t246
  t848 = 0.1e1 / t237 / t236 * t242 * t25 * t847
  t850 = t10 * t683
  t851 = t850 * t268
  t852 = t266 * t851
  t855 = t230 * t825 * t233
  t857 = t236 ** (-0.5e0)
  t860 = t857 * t242 * t25 * t847
  t862 = t277 * t851
  t865 = t244 * t92 * t246
  t870 = 0.10000000000000000000000000000000000000000000000000e1 * t263 * (-0.42198333333333333333333333333333333333333333333333e0 * t848 + 0.84396666666666666666666666666666666666666666666666e0 * t852 + 0.39862222222222222222222222222222222222222222222223e0 * t855 + 0.68258333333333333333333333333333333333333333333333e-1 * t860 + 0.13651666666666666666666666666666666666666666666667e0 * t862 + 0.13692777777777777777777777777777777777777777777778e0 * t865) * t285
  t871 = t261 ** 2
  t874 = t253 ** 2
  t878 = 0.16081979498692535066756296899072713062105388428051e2 * t260 / t871 * t837 / t874
  t890 = t318 ** 2
  t904 = t311 ** 2
  t907 = t303 ** 2
  t919 = 0.1e1 / t338 / t327
  t921 = t345 ** 2
  t931 = -0.57538888888888888888888888888888888888888888888889e0 * t848 + 0.11507777777777777777777777777777777777777777777778e1 * t852 + 0.40256666666666666666666666666666666666666666666667e0 * t855 + 0.36677500000000000000000000000000000000000000000000e-1 * t860 + 0.73355000000000000000000000000000000000000000000000e-1 * t862 + 0.13797500000000000000000000000000000000000000000000e0 * t865
  t935 = t338 ** 2
  t936 = 0.1e1 / t935
  t938 = t330 ** 2
  t939 = 0.1e1 / t938
  t943 = -0.70983522622222222222222222222222222222222222222221e-3 * t230 * t825 * t305 - 0.34246666666666666666666666666666666666666666666666e-1 * t521 * t268 * t312 * t318 * t319 - 0.20000000000000000000000000000000000000000000000000e1 * t310 / t311 / t300 * t890 * t319 + 0.10000000000000000000000000000000000000000000000000e1 * t313 * (-0.78438333333333333333333333333333333333333333333333e0 * t848 + 0.15687666666666666666666666666666666666666666666667e1 * t852 + 0.68863333333333333333333333333333333333333333333333e0 * t855 + 0.14025833333333333333333333333333333333333333333333e0 * t860 + 0.28051666666666666666666666666666666666666666666667e0 * t862 + 0.17365833333333333333333333333333333333333333333333e0 * t865) * t319 + 0.32163958997385070133512593798145426124210776856102e2 * t310 / t904 * t890 / t907 + t828 + t833 + t840 - t870 - t878 - 0.24415263074675393406472461472505321282722606644045e-3 * t230 * t825 * t332 - 0.10843581300301739842632067522386578331157260943710e-1 * t521 * t268 * t359 - 0.11696447245269292414524477327518106963944910680856e1 * t337 * t919 * t921 * t346 + 0.58482236226346462072622386637590534819724553404280e0 * t340 * t931 * t346 + 0.17315859105681463759666483083807725165579399831905e2 * t337 * t936 * t921 * t939
  t964 = -t828 - t833 - t840 + t870 + t878 + t295 * t943 + 0.24415263074675393406472461472505321282722606644045e-3 * t352 * t850 * t353 + 0.10843581300301739842632067522386578331157260943710e-1 * t295 * t230 * t272 * t359 + 0.11696447245269292414524477327518106963944910680856e1 * t357 * t919 * t921 * t346 - 0.58482236226346462072622386637590534819724553404280e0 * t357 * t339 * t931 * t346 - 0.17315859105681463759666483083807725165579399831905e2 * t357 * t936 * t921 * t939
  t967 = f.my_piecewise3(t4, 0, t229 * t964 / 0.2e1)
  t974 = 0.1e1 / t20 / t386 / t201
  t979 = t382 ** 2
  t982 = 0.1e1 / t19 / t386 / t784
  t984 = t389 ** 2
  t985 = 0.1e1 / t984
  t990 = 0.1e1 / t467
  t1021 = -0.45668973829554311710553822152269646322259917167247e2 * t400 * t451 * t974 * t485 + 0.22426328475640736312697250203851942640826290654387e2 * t400 * t979 * t982 * t985 * t11 + 0.46398610073542088783775131477319686233873682604854e2 * t384 * t990 * t391 + 0.58740209842853858907753467646671477846977845758853e1 * t366 * t450 * t793 / t456 + 0.100e3 / 0.9e1 * t375 * t441 * t811 + 0.400e3 / 0.9e1 * t436 * t441 * t811 + 0.100e3 / 0.3e1 * t379 * t399 * t811 - 0.80e2 / 0.9e1 * t437 * t814 - 0.80e2 / 0.9e1 * t442 * t814 + 0.46398610073542088783775131477319686233873682604854e2 * t400 * t383 * t990 * t391 - 0.40e2 / 0.9e1 * t433 * t814 + 0.45871489607314940800000000000000000000000000000000e1 * t367 * t780 * t370
  t1050 = 0.1e1 / t19 / t386 / t803 * t391 * t575
  t1060 = 0.1e1 / t19 / t386 / t202 * t458 * tau0 * t11
  t1075 = t455 * t391 * t109
  t1080 = -0.40e2 / 0.9e1 * t430 * t799 - 0.10564442867498814815645970076333132800000000000000e2 * t425 * t787 * t426 + 0.100e3 / 0.9e1 * t374 * t574 * t807 + 0.100e3 / 0.9e1 * t377 * t574 * t807 - 0.45668973829554311710553822152269646322259917167247e2 * t452 * t974 * t458 * t88 + 0.22426328475640736312697250203851942640826290654387e2 * t381 * t979 * t982 * t985 * t11 + 0.18953680585597258490104220374722094049785001064075e2 * t397 / t398 / t215 * t383 * t1050 + 0.34145027162283597540600988525061417811035452087663e2 * t397 * t475 * t451 * t1060 + 0.11372208351358355094062532224833256429871000638445e2 * t395 * t378 * t465 * t1050 + 0.30325888936955613584166752599555350479656001702520e2 * t464 * t476 * t1050 + 0.34145027162283597540600988525061417811035452087663e2 * t464 * t399 * t451 * t1060 - 0.39423655618042297659416778379421955623552802213275e2 * t466 * t1075 - 0.39423655618042297659416778379421955623552802213275e2 * t477 * t1075
  t1094 = t530 ** 2
  t1102 = t25 * t9 * t91
  t1103 = 0.1e1 / t494 / t493 * t242 * t1102
  t1105 = t517 * t683
  t1106 = t516 * t1105
  t1108 = t8 * t850
  t1110 = t493 ** (-0.5e0)
  t1112 = t1110 * t242 * t1102
  t1114 = t524 * t1105
  t1116 = t243 * t845
  t1122 = t512 ** 2
  t1125 = t505 ** 2
  t1140 = t562 ** 2
  t1156 = t556 ** 2
  t1159 = t547 ** 2
  t1165 = -0.14764627977777777777777777777777777777777777777777e-2 * t8 * t850 * t506 - 0.35616666666666666666666666666666666666666666666666e-1 * t230 * t127 * t513 * t532 - 0.20000000000000000000000000000000000000000000000000e1 * t511 / t512 / t502 * t1094 * t531 + 0.10000000000000000000000000000000000000000000000000e1 * t514 * (-0.42198333333333333333333333333333333333333333333333e0 * t1103 + 0.84396666666666666666666666666666666666666666666666e0 * t1106 + 0.39862222222222222222222222222222222222222222222223e0 * t1108 + 0.68258333333333333333333333333333333333333333333333e-1 * t1112 + 0.13651666666666666666666666666666666666666666666667e0 * t1114 + 0.13692777777777777777777777777777777777777777777778e0 * t1116) * t531 + 0.16081979498692535066756296899072713062105388428051e2 * t511 / t1122 * t1094 / t1125 + 0.24415263074675393406472461472505321282722606644045e-3 * t539 * t517 * t683 * t548 + 0.10843581300301739842632067522386578331157260943710e-1 * t538 * t8 * t267 * t565 + 0.11696447245269292414524477327518106963944910680856e1 * t555 / t556 / t544 * t1140 * t564 - 0.58482236226346462072622386637590534819724553404280e0 * t555 * t557 * (-0.57538888888888888888888888888888888888888888888889e0 * t1103 + 0.11507777777777777777777777777777777777777777777778e1 * t1106 + 0.40256666666666666666666666666666666666666666666667e0 * t1108 + 0.36677500000000000000000000000000000000000000000000e-1 * t1112 + 0.73355000000000000000000000000000000000000000000000e-1 * t1114 + 0.13797500000000000000000000000000000000000000000000e0 * t1116) * t564 - 0.17315859105681463759666483083807725165579399831905e2 * t555 / t1156 * t1140 / t1159 - 0.2e1 * t967
  t1169 = t651 * t780
  t1177 = 0.1e1 / t649 / t94 * t199 * t787
  t1183 = 0.8e1 / 0.3e1 * t107 * t814
  t1184 = 0.520e3 / 0.9e1 * t811
  t1185 = t1183 - t1184
  t1189 = t1183 + t1184
  t1204 = t620 ** 2
  t1208 = t591 ** 2
  t1209 = 0.1e1 / t1208
  t1211 = t626 ** 2
  t1215 = 0.1e1 / t591
  t1228 = 0.88e2 / 0.27e2 * t648 * t1169 + 0.88e2 / 0.27e2 * t663 * t1169 - 0.256e3 / 0.81e2 * t663 * t1177 - 0.256e3 / 0.81e2 * t648 * t1177 + 0.6e1 * t640 * t598 * t1185 - 0.6e1 * t596 * t644 * t1189 + 0.2e1 * t655 * t602 * t1185 - 0.2e1 * t601 * t659 * t1189 - 0.8e1 * t614 * t625 * t620 * t626 + 0.30e2 * t595 * t588 * t598 * t1204 + 0.42e2 * t596 * t1209 * t597 * t1211 + 0.6e1 * t601 * t1215 * t597 * t1211 - 0.72e2 * t631 * t636 * t620 * t626 + 0.30e2 * t587 * t588 * t593 * t1204
  t1252 = t597 * t620 * t626
  t1261 = t620 * s0 * t195
  t1267 = t626 * s0 * t195
  t1281 = 0.42e2 * t590 * t1209 * t1211 + 0.2e1 * t600 * t1204 * t602 + 0.6e1 * t582 * t1215 * t1211 + 0.2e1 * t614 * t585 * t1185 - 0.2e1 * t582 * t625 * t1189 + 0.6e1 * t631 * t593 * t1185 - 0.6e1 * t590 * t636 * t1189 - 0.8e1 * t655 * t625 * t1252 - 0.72e2 * t640 * t636 * t1252 - 0.32e2 / 0.3e1 * t640 * t593 * t650 * t1261 + 0.32e2 / 0.3e1 * t596 * t636 * t650 * t1267 - 0.32e2 / 0.9e1 * t655 * t585 * t650 * t1261 + 0.32e2 / 0.9e1 * t601 * t625 * t650 * t1267 + 0.2e1 * t571 * t1204 * t585
  v2rho2_0_ = 0.4e1 * t227 + 0.4e1 * t365 * t405 + 0.4e1 * t421 * t489 + 0.2e1 * t569 * t604 + 0.2e1 * t613 * t666 + r0 * (0.2e1 * t823 + 0.2e1 * t967 * t405 + 0.4e1 * t365 * t489 + 0.2e1 * t421 * (t1021 + t1080) + t1165 * t604 + 0.2e1 * t569 * t666 + t613 * (t1228 + t1281))

  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = r0 / 0.2e1 <= f.p.dens_threshold or t3
  t5 = 3 ** (0.1e1 / 0.3e1)
  t6 = 0.1e1 / jnp.pi
  t7 = t6 ** (0.1e1 / 0.3e1)
  t8 = t5 * t7
  t9 = 4 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = 2 ** (0.1e1 / 0.3e1)
  t13 = t8 * t10 * t11
  t14 = 0.2e1 <= f.p.zeta_threshold
  t15 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t16 = t15 * f.p.zeta_threshold
  t18 = f.my_piecewise3(t14, t16, 0.2e1 * t11)
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / r0
  t23 = t18 * t22
  t24 = 9 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = t7 ** 2
  t28 = t25 * t26 * f.p.cam_omega
  t29 = 0.1e1 / t19
  t31 = f.my_piecewise3(t14, t15, t11)
  t33 = t11 / t31
  t36 = t28 * t5 * t29 * t33 / 0.18e2
  t37 = 0.135e1 <= t36
  t38 = 0.135e1 < t36
  t39 = f.my_piecewise3(t38, t36, 0.135e1)
  t40 = t39 ** 2
  t43 = t40 ** 2
  t44 = 0.1e1 / t43
  t46 = t43 * t40
  t47 = 0.1e1 / t46
  t49 = t43 ** 2
  t50 = 0.1e1 / t49
  t53 = 0.1e1 / t49 / t40
  t56 = 0.1e1 / t49 / t43
  t59 = 0.1e1 / t49 / t46
  t61 = t49 ** 2
  t62 = 0.1e1 / t61
  t65 = f.my_piecewise3(t38, 0.135e1, t36)
  t66 = jnp.sqrt(jnp.pi)
  t67 = 0.1e1 / t65
  t69 = jnp.erf(t67 / 0.2e1)
  t71 = t65 ** 2
  t72 = 0.1e1 / t71
  t74 = jnp.exp(-t72 / 0.4e1)
  t75 = t74 - 0.1e1
  t78 = t74 - 0.3e1 / 0.2e1 - 0.2e1 * t71 * t75
  t81 = 0.2e1 * t65 * t78 + t66 * t69
  t85 = f.my_piecewise3(t37, 0.1e1 / t40 / 0.36e2 - t44 / 0.960e3 + t47 / 0.26880e5 - t50 / 0.829440e6 + t53 / 0.28385280e8 - t56 / 0.1073479680e10 + t59 / 0.44590694400e11 - t62 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t65 * t81)
  t87 = params.c_x[1]
  t88 = t87 * s0
  t89 = t11 ** 2
  t90 = r0 ** 2
  t92 = 0.1e1 / t20 / t90
  t93 = t89 * t92
  t95 = s0 * t89 * t92
  t97 = 0.1e1 + 0.3840616724010807e-2 * t95
  t98 = 0.1e1 / t97
  t102 = params.c_x[2]
  t103 = 6 ** (0.1e1 / 0.3e1)
  t104 = t103 ** 2
  t105 = jnp.pi ** 2
  t106 = t105 ** (0.1e1 / 0.3e1)
  t107 = t106 ** 2
  t108 = t104 * t107
  t109 = 0.3e1 / 0.10e2 * t108
  t110 = tau0 * t89
  t111 = t110 * t22
  t112 = t109 - t111
  t113 = t102 * t112
  t114 = t109 + t111
  t115 = 0.1e1 / t114
  t117 = params.c_x[0] + 0.3840616724010807e-2 * t88 * t93 * t98 + t113 * t115
  t118 = t85 * t117
  t122 = 0.1e1 / t20
  t123 = t18 * t122
  t124 = t40 * t39
  t125 = 0.1e1 / t124
  t127 = 0.1e1 / t19 / r0
  t131 = t28 * t5 * t127 * t33 / 0.54e2
  t132 = f.my_piecewise3(t38, -t131, 0)
  t135 = t43 * t39
  t136 = 0.1e1 / t135
  t139 = t43 * t124
  t140 = 0.1e1 / t139
  t144 = 0.1e1 / t49 / t39
  t148 = 0.1e1 / t49 / t124
  t152 = 0.1e1 / t49 / t135
  t156 = 0.1e1 / t49 / t139
  t160 = 0.1e1 / t61 / t39
  t164 = f.my_piecewise3(t38, 0, -t131)
  t166 = t74 * t72
  t170 = t71 * t65
  t171 = 0.1e1 / t170
  t175 = t65 * t75
  t180 = t171 * t164 * t74 / 0.2e1 - 0.4e1 * t175 * t164 - t67 * t164 * t74
  t183 = -t166 * t164 + 0.2e1 * t164 * t78 + 0.2e1 * t65 * t180
  t187 = f.my_piecewise3(t37, -t125 * t132 / 0.18e2 + t136 * t132 / 0.240e3 - t140 * t132 / 0.4480e4 + t144 * t132 / 0.103680e6 - t148 * t132 / 0.2838528e7 + t152 * t132 / 0.89456640e8 - t156 * t132 / 0.3185049600e10 + t160 * t132 / 0.126340300800e12, -0.8e1 / 0.3e1 * t164 * t81 - 0.8e1 / 0.3e1 * t65 * t183)
  t188 = t187 * t117
  t192 = t90 * r0
  t194 = 0.1e1 / t20 / t192
  t195 = t89 * t194
  t199 = s0 ** 2
  t200 = t87 * t199
  t201 = t90 ** 2
  t202 = t201 * t90
  t204 = 0.1e1 / t19 / t202
  t205 = t11 * t204
  t206 = t97 ** 2
  t207 = 0.1e1 / t206
  t211 = t102 * tau0
  t212 = t93 * t115
  t215 = t114 ** 2
  t216 = 0.1e1 / t215
  t217 = t113 * t216
  t218 = t110 * t92
  t221 = -0.10241644597362152000000000000000000000000000000000e-1 * t88 * t195 * t98 + 0.78668463044008017417987481553328000000000000000000e-4 * t200 * t205 * t207 + 0.5e1 / 0.3e1 * t211 * t212 + 0.5e1 / 0.3e1 * t217 * t218
  t222 = t85 * t221
  t226 = t18 * t19
  t227 = t132 ** 2
  t231 = 0.1e1 / t19 / t90
  t235 = 0.2e1 / 0.81e2 * t28 * t5 * t231 * t33
  t236 = f.my_piecewise3(t38, t235, 0)
  t264 = 0.1e1 / t61 / t40
  t269 = t44 * t227 / 0.6e1 - t125 * t236 / 0.18e2 - t47 * t227 / 0.48e2 + t136 * t236 / 0.240e3 + t50 * t227 / 0.640e3 - t140 * t236 / 0.4480e4 - t53 * t227 / 0.11520e5 + t144 * t236 / 0.103680e6 + t56 * t227 / 0.258048e6 - t148 * t236 / 0.2838528e7 - t59 * t227 / 0.6881280e7 + t152 * t236 / 0.89456640e8 + t62 * t227 / 0.212336640e9 - t156 * t236 / 0.3185049600e10 - t264 * t227 / 0.7431782400e10 + t160 * t236 / 0.126340300800e12
  t270 = f.my_piecewise3(t38, 0, t235)
  t275 = t71 ** 2
  t277 = 0.1e1 / t275 / t65
  t278 = t164 ** 2
  t282 = t74 * t171
  t290 = 0.1e1 / t275
  t298 = 0.1e1 / t275 / t71
  t310 = -0.2e1 * t290 * t278 * t74 + t171 * t270 * t74 / 0.2e1 + t298 * t278 * t74 / 0.4e1 - 0.4e1 * t278 * t75 - t72 * t278 * t74 - 0.4e1 * t175 * t270 - t67 * t270 * t74
  t313 = -t277 * t278 * t74 / 0.2e1 + 0.2e1 * t282 * t278 - t166 * t270 + 0.2e1 * t270 * t78 + 0.4e1 * t164 * t180 + 0.2e1 * t65 * t310
  t317 = f.my_piecewise3(t37, t269, -0.8e1 / 0.3e1 * t270 * t81 - 0.16e2 / 0.3e1 * t164 * t183 - 0.8e1 / 0.3e1 * t65 * t313)
  t318 = t317 * t117
  t322 = t187 * t221
  t327 = 0.1e1 / t20 / t201
  t328 = t89 * t327
  t332 = t201 * t192
  t335 = t11 / t19 / t332
  t339 = t199 * s0
  t340 = t87 * t339
  t341 = t201 ** 2
  t342 = t341 * t90
  t343 = 0.1e1 / t342
  t345 = 0.1e1 / t206 / t97
  t349 = t195 * t115
  t352 = tau0 ** 2
  t353 = t102 * t352
  t354 = t201 * r0
  t356 = 0.1e1 / t19 / t354
  t358 = t11 * t356 * t216
  t361 = t215 * t114
  t362 = 0.1e1 / t361
  t363 = t113 * t362
  t364 = t352 * t11
  t365 = t364 * t356
  t368 = t110 * t194
  t371 = 0.37552696856994557333333333333333333333333333333333e-1 * t88 * t328 * t98 - 0.70801616739607215676188733397995200000000000000000e-3 * t200 * t335 * t207 + 0.32227777580697953041677078903529515239532673674240e-5 * t340 * t343 * t345 - 0.40e2 / 0.9e1 * t211 * t349 + 0.100e3 / 0.9e1 * t353 * t358 + 0.100e3 / 0.9e1 * t363 * t365 - 0.40e2 / 0.9e1 * t217 * t368
  t372 = t85 * t371
  t377 = f.my_piecewise3(t4, 0, t13 * t23 * t118 / 0.96e2 - t13 * t123 * t188 / 0.32e2 - t13 * t123 * t222 / 0.32e2 - 0.3e1 / 0.64e2 * t13 * t226 * t318 - 0.3e1 / 0.32e2 * t13 * t226 * t322 - 0.3e1 / 0.64e2 * t13 * t226 * t372)
  t379 = f.my_piecewise3(t3, f.p.zeta_threshold, 1)
  t380 = t8 * t10
  t381 = t231 * t11
  t383 = f.my_piecewise3(t3, 0.1e1 / t15, 1)
  t386 = t380 * t29 * t11 * t383
  t387 = jnp.sqrt(t386)
  t390 = t386 ** 0.15e1
  t392 = t5 ** 2
  t393 = t392 * t26
  t394 = t393 * t9
  t396 = t383 ** 2
  t398 = t394 * t122 * t89 * t396
  t400 = 0.37978500000000000000000000000000000000000000000000e1 * t387 + 0.89690000000000000000000000000000000000000000000000e0 * t386 + 0.20477500000000000000000000000000000000000000000000e0 * t390 + 0.12323500000000000000000000000000000000000000000000e0 * t398
  t403 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t400
  t404 = jnp.log(t403)
  t405 = t383 * t404
  t408 = 0.14764627977777777777777777777777777777777777777777e-2 * t380 * t381 * t405
  t409 = t10 * t127
  t410 = t8 * t409
  t411 = t11 * t383
  t412 = t400 ** 2
  t413 = 0.1e1 / t412
  t416 = 0.1e1 / t387 * t5 * t7
  t417 = t409 * t411
  t418 = t416 * t417
  t420 = t127 * t11
  t421 = t420 * t383
  t422 = t380 * t421
  t424 = t386 ** 0.5e0
  t426 = t424 * t5 * t7
  t427 = t426 * t417
  t431 = t394 * t22 * t89 * t396
  t433 = -0.63297500000000000000000000000000000000000000000000e0 * t418 - 0.29896666666666666666666666666666666666666666666667e0 * t422 - 0.10238750000000000000000000000000000000000000000000e0 * t427 - 0.82156666666666666666666666666666666666666666666667e-1 * t431
  t435 = 0.1e1 / t403
  t437 = t411 * t413 * t433 * t435
  t439 = 0.35616666666666666666666666666666666666666666666666e-1 * t410 * t437
  t441 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t386
  t443 = 0.1e1 / t412 / t400
  t444 = t441 * t443
  t445 = t433 ** 2
  t448 = 0.20000000000000000000000000000000000000000000000000e1 * t444 * t445 * t435
  t449 = t441 * t413
  t453 = 0.1e1 / t387 / t386 * t392 * t26
  t454 = t9 * t92
  t455 = t89 * t396
  t456 = t454 * t455
  t457 = t453 * t456
  t459 = t10 * t231
  t460 = t459 * t411
  t461 = t416 * t460
  t463 = t381 * t383
  t464 = t380 * t463
  t466 = t386 ** (-0.5e0)
  t468 = t466 * t392 * t26
  t469 = t468 * t456
  t471 = t426 * t460
  t474 = t394 * t93 * t396
  t476 = -0.42198333333333333333333333333333333333333333333333e0 * t457 + 0.84396666666666666666666666666666666666666666666666e0 * t461 + 0.39862222222222222222222222222222222222222222222223e0 * t464 + 0.68258333333333333333333333333333333333333333333333e-1 * t469 + 0.13651666666666666666666666666666666666666666666667e0 * t471 + 0.13692777777777777777777777777777777777777777777778e0 * t474
  t479 = 0.10000000000000000000000000000000000000000000000000e1 * t449 * t476 * t435
  t480 = t412 ** 2
  t481 = 0.1e1 / t480
  t482 = t441 * t481
  t483 = t403 ** 2
  t484 = 0.1e1 / t483
  t487 = 0.16081979498692535066756296899072713062105388428051e2 * t482 * t445 * t484
  t489 = f.my_piecewise3(0.0e0 <= f.p.zeta_threshold, t16, 0)
  t493 = 0.1e1 / (0.2e1 * t11 - 0.2e1)
  t494 = (t18 + t489 - 0.2e1) * t493
  t499 = 0.70594500000000000000000000000000000000000000000000e1 * t387 + 0.15494250000000000000000000000000000000000000000000e1 * t386 + 0.42077500000000000000000000000000000000000000000000e0 * t390 + 0.15629250000000000000000000000000000000000000000000e0 * t398
  t502 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t499
  t503 = jnp.log(t502)
  t504 = t383 * t503
  t508 = t499 ** 2
  t509 = 0.1e1 / t508
  t514 = -0.11765750000000000000000000000000000000000000000000e1 * t418 - 0.51647500000000000000000000000000000000000000000000e0 * t422 - 0.21038750000000000000000000000000000000000000000000e0 * t427 - 0.10419500000000000000000000000000000000000000000000e0 * t431
  t516 = 0.1e1 / t502
  t518 = t411 * t509 * t514 * t516
  t522 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t386
  t524 = 0.1e1 / t508 / t499
  t525 = t522 * t524
  t526 = t514 ** 2
  t530 = t522 * t509
  t537 = -0.78438333333333333333333333333333333333333333333333e0 * t457 + 0.15687666666666666666666666666666666666666666666667e1 * t461 + 0.68863333333333333333333333333333333333333333333333e0 * t464 + 0.14025833333333333333333333333333333333333333333333e0 * t469 + 0.28051666666666666666666666666666666666666666666667e0 * t471 + 0.17365833333333333333333333333333333333333333333333e0 * t474
  t541 = t508 ** 2
  t542 = 0.1e1 / t541
  t543 = t522 * t542
  t544 = t502 ** 2
  t545 = 0.1e1 / t544
  t553 = 0.51785000000000000000000000000000000000000000000000e1 * t387 + 0.90577500000000000000000000000000000000000000000000e0 * t386 + 0.11003250000000000000000000000000000000000000000000e0 * t390 + 0.12417750000000000000000000000000000000000000000000e0 * t398
  t556 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t553
  t557 = jnp.log(t556)
  t558 = t383 * t557
  t562 = t553 ** 2
  t563 = 0.1e1 / t562
  t568 = -0.86308333333333333333333333333333333333333333333334e0 * t418 - 0.30192500000000000000000000000000000000000000000000e0 * t422 - 0.55016250000000000000000000000000000000000000000000e-1 * t427 - 0.82785000000000000000000000000000000000000000000000e-1 * t431
  t570 = 0.1e1 / t556
  t571 = t563 * t568 * t570
  t572 = t411 * t571
  t576 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t386
  t578 = 0.1e1 / t562 / t553
  t579 = t576 * t578
  t580 = t568 ** 2
  t584 = t576 * t563
  t591 = -0.57538888888888888888888888888888888888888888888889e0 * t457 + 0.11507777777777777777777777777777777777777777777778e1 * t461 + 0.40256666666666666666666666666666666666666666666667e0 * t464 + 0.36677500000000000000000000000000000000000000000000e-1 * t469 + 0.73355000000000000000000000000000000000000000000000e-1 * t471 + 0.13797500000000000000000000000000000000000000000000e0 * t474
  t592 = t591 * t570
  t595 = t562 ** 2
  t596 = 0.1e1 / t595
  t597 = t576 * t596
  t598 = t556 ** 2
  t599 = 0.1e1 / t598
  t603 = -0.70983522622222222222222222222222222222222222222221e-3 * t380 * t381 * t504 - 0.34246666666666666666666666666666666666666666666666e-1 * t410 * t518 - 0.20000000000000000000000000000000000000000000000000e1 * t525 * t526 * t516 + 0.10000000000000000000000000000000000000000000000000e1 * t530 * t537 * t516 + 0.32163958997385070133512593798145426124210776856102e2 * t543 * t526 * t545 + t408 + t439 + t448 - t479 - t487 - 0.24415263074675393406472461472505321282722606644045e-3 * t380 * t381 * t558 - 0.10843581300301739842632067522386578331157260943710e-1 * t410 * t572 - 0.11696447245269292414524477327518106963944910680856e1 * t579 * t580 * t570 + 0.58482236226346462072622386637590534819724553404280e0 * t584 * t592 + 0.17315859105681463759666483083807725165579399831905e2 * t597 * t580 * t599
  t605 = t494 * t8
  t606 = t411 * t557
  t610 = t494 * t380
  t614 = t494 * t576
  t616 = t578 * t580 * t570
  t620 = t563 * t591 * t570
  t624 = t596 * t580 * t599
  t627 = -t408 - t439 - t448 + t479 + t487 + t494 * t603 + 0.24415263074675393406472461472505321282722606644045e-3 * t605 * t459 * t606 + 0.10843581300301739842632067522386578331157260943710e-1 * t610 * t421 * t571 + 0.11696447245269292414524477327518106963944910680856e1 * t614 * t616 - 0.58482236226346462072622386637590534819724553404280e0 * t614 * t620 - 0.17315859105681463759666483083807725165579399831905e2 * t614 * t624
  t630 = f.my_piecewise3(t4, 0, t379 * t627 / 0.2e1)
  t631 = params.c_ss[0]
  t632 = t631 * s0
  t634 = 0.1e1 + 0.46914023462026644e0 * t95
  t635 = 0.1e1 / t634
  t639 = params.c_ss[1]
  t640 = t639 * t112
  t642 = params.c_ss[2]
  t643 = t112 ** 2
  t644 = t642 * t643
  t646 = params.c_ss[3]
  t647 = t199 ** 2
  t648 = t647 * t199
  t649 = t646 * t648
  t650 = t341 ** 2
  t651 = 0.1e1 / t650
  t652 = t634 ** 2
  t653 = t652 ** 2
  t655 = 0.1e1 / t653 / t652
  t659 = params.c_ss[4]
  t660 = t643 ** 2
  t661 = t659 * t660
  t662 = t215 ** 2
  t663 = 0.1e1 / t662
  t664 = t661 * t663
  t669 = 0.46914023462026644e0 * t632 * t93 * t635 + t640 * t115 + t644 * t216 + 0.17058312527037532641093798337249884644806500957667e0 * t649 * t651 * t655 + 0.17058312527037532641093798337249884644806500957667e0 * t664 * t648 * t651 * t655
  t674 = 0.11073470983333333333333333333333333333333333333333e-2 * t380 * t420 * t405
  t675 = t433 * t435
  t677 = 0.10000000000000000000000000000000000000000000000000e1 * t449 * t675
  t681 = t514 * t516
  t687 = t568 * t570
  t700 = f.my_piecewise3(t4, 0, t379 * (t674 + t677 + t494 * (0.53237641966666666666666666666666666666666666666666e-3 * t380 * t420 * t504 + 0.10000000000000000000000000000000000000000000000000e1 * t530 * t681 - t674 - t677 + 0.18311447306006545054854346104378990962041954983034e-3 * t380 * t420 * t558 + 0.58482236226346462072622386637590534819724553404280e0 * t584 * t687) - 0.18311447306006545054854346104378990962041954983034e-3 * t605 * t409 * t606 - 0.58482236226346462072622386637590534819724553404280e0 * t614 * t571) / 0.2e1)
  t704 = t631 * t199
  t705 = 0.1e1 / t652
  t709 = t639 * tau0
  t712 = t640 * t216
  t715 = t642 * t112
  t716 = t715 * t216
  t719 = t644 * t362
  t723 = 0.1e1 / t650 / r0
  t727 = t647 * t339
  t728 = t646 * t727
  t729 = t650 * t192
  t731 = 0.1e1 / t20 / t729
  t732 = t652 * t634
  t734 = 0.1e1 / t653 / t732
  t740 = t659 * t643 * t112
  t741 = t663 * t648
  t742 = t740 * t741
  t743 = t650 * t90
  t747 = 0.1e1 / t20 / t743 * t655 * t110
  t751 = 0.1e1 / t662 / t114
  t752 = t751 * t648
  t753 = t661 * t752
  t761 = t734 * t89
  t765 = -0.12510406256540438400000000000000000000000000000000e1 * t632 * t195 * t635 + 0.11738269852776460906273300084814592000000000000000e1 * t704 * t205 * t705 + 0.5e1 / 0.3e1 * t709 * t212 + 0.5e1 / 0.3e1 * t712 * t218 + 0.10e2 / 0.3e1 * t716 * t218 + 0.10e2 / 0.3e1 * t719 * t218 - 0.27293300043260052225750077339599815431690401532267e1 * t649 * t723 * t655 + 0.12804385185856349077725370696898031679138294532873e1 * t728 * t731 * t734 * t89 + 0.11372208351358355094062532224833256429871000638445e1 * t742 * t747 + 0.11372208351358355094062532224833256429871000638445e1 * t753 * t747 - 0.27293300043260052225750077339599815431690401532267e1 * t664 * t648 * t723 * t655 + 0.12804385185856349077725370696898031679138294532873e1 * t664 * t727 * t731 * t761
  t769 = 0.621814e-1 * t441 * t404
  t772 = t576 * t557
  t781 = f.my_piecewise3(t4, 0, t379 * (-t769 + t494 * (-0.3109070e-1 * t522 * t503 + t769 - 0.19751673498613801407483339618206552048944131217655e-1 * t772) + 0.19751673498613801407483339618206552048944131217655e-1 * t494 * t772) / 0.2e1)
  t783 = t731 * t655 * t110
  t788 = t659 * t643
  t789 = t788 * t741
  t790 = t650 * t354
  t794 = 0.1e1 / t19 / t790 * t655 * t364
  t797 = t740 * t752
  t801 = t740 * t663 * t727
  t804 = 0.1e1 / t19 / t650 / t202
  t806 = tau0 * t11
  t807 = t804 * t734 * t806
  t811 = 0.1e1 / t662 / t215
  t813 = t661 * t811 * t648
  t817 = t661 * t751 * t727
  t822 = 0.1e1 / t20 / t650 / t201
  t827 = t647 ** 2
  t830 = 0.1e1 / t19 / t650 / t332
  t832 = t653 ** 2
  t833 = 0.1e1 / t832
  t834 = t833 * t11
  t842 = 0.1e1 / t743
  t847 = -0.39423655618042297659416778379421955623552802213275e2 * t742 * t783 - 0.39423655618042297659416778379421955623552802213275e2 * t753 * t783 + 0.11372208351358355094062532224833256429871000638445e2 * t789 * t794 + 0.30325888936955613584166752599555350479656001702520e2 * t797 * t794 + 0.34145027162283597540600988525061417811035452087663e2 * t801 * t807 + 0.18953680585597258490104220374722094049785001064075e2 * t813 * t794 + 0.34145027162283597540600988525061417811035452087663e2 * t817 * t807 - 0.45668973829554311710553822152269646322259917167247e2 * t664 * t727 * t822 * t761 + 0.22426328475640736312697250203851942640826290654387e2 * t664 * t827 * t830 * t834 - 0.80e2 / 0.9e1 * t716 * t368 - 0.80e2 / 0.9e1 * t719 * t368 + 0.46398610073542088783775131477319686233873682604854e2 * t664 * t648 * t842 * t655
  t850 = t640 * t362
  t853 = t715 * t362
  t856 = t644 * t663
  t867 = t639 * t352
  t870 = t642 * t352
  t877 = t646 * t827
  t885 = t631 * t339
  t886 = 0.1e1 / t732
  t890 = -0.40e2 / 0.9e1 * t712 * t368 + 0.100e3 / 0.9e1 * t850 * t365 + 0.400e3 / 0.9e1 * t853 * t365 + 0.100e3 / 0.3e1 * t856 * t365 - 0.40e2 / 0.9e1 * t709 * t349 + 0.45871489607314940800000000000000000000000000000000e1 * t632 * t328 * t635 - 0.10564442867498814815645970076333132800000000000000e2 * t704 * t335 * t705 + 0.100e3 / 0.9e1 * t867 * t358 + 0.100e3 / 0.9e1 * t870 * t358 - 0.45668973829554311710553822152269646322259917167247e2 * t728 * t822 * t734 * t89 + 0.22426328475640736312697250203851942640826290654387e2 * t877 * t830 * t833 * t11 + 0.46398610073542088783775131477319686233873682604854e2 * t649 * t842 * t655 + 0.58740209842853858907753467646671477846977845758853e1 * t885 * t343 * t886
  t891 = t847 + t890
  t895 = t8 * t10 * t29
  t896 = jnp.sqrt(t895)
  t899 = t895 ** 0.15e1
  t902 = t393 * t9 * t122
  t904 = 0.37978500000000000000000000000000000000000000000000e1 * t896 + 0.89690000000000000000000000000000000000000000000000e0 * t895 + 0.20477500000000000000000000000000000000000000000000e0 * t899 + 0.12323500000000000000000000000000000000000000000000e0 * t902
  t907 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t904
  t908 = jnp.log(t907)
  t912 = t904 ** 2
  t913 = 0.1e1 / t912
  t914 = t127 * t913
  t916 = 0.1e1 / t896 * t5
  t917 = t7 * t10
  t918 = t917 * t127
  t919 = t916 * t918
  t922 = t895 ** 0.5e0
  t923 = t922 * t5
  t924 = t923 * t918
  t927 = t393 * t9 * t22
  t929 = -0.63297500000000000000000000000000000000000000000000e0 * t919 - 0.29896666666666666666666666666666666666666666666667e0 * t410 - 0.10238750000000000000000000000000000000000000000000e0 * t924 - 0.82156666666666666666666666666666666666666666666667e-1 * t927
  t930 = 0.1e1 / t907
  t931 = t929 * t930
  t936 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t895
  t938 = 0.1e1 / t912 / t904
  t939 = t936 * t938
  t940 = t929 ** 2
  t941 = t940 * t930
  t944 = t936 * t913
  t947 = 0.1e1 / t896 / t895 * t392
  t948 = t26 * t9
  t949 = t948 * t92
  t950 = t947 * t949
  t952 = t917 * t231
  t953 = t916 * t952
  t955 = t8 * t459
  t957 = t895 ** (-0.5e0)
  t958 = t957 * t392
  t959 = t958 * t949
  t961 = t923 * t952
  t963 = t393 * t454
  t965 = -0.42198333333333333333333333333333333333333333333333e0 * t950 + 0.84396666666666666666666666666666666666666666666666e0 * t953 + 0.39862222222222222222222222222222222222222222222223e0 * t955 + 0.68258333333333333333333333333333333333333333333333e-1 * t959 + 0.13651666666666666666666666666666666666666666666667e0 * t961 + 0.13692777777777777777777777777777777777777777777778e0 * t963
  t966 = t965 * t930
  t969 = t912 ** 2
  t970 = 0.1e1 / t969
  t971 = t936 * t970
  t972 = t907 ** 2
  t973 = 0.1e1 / t972
  t974 = t940 * t973
  t977 = f.my_piecewise3(t3, t16, 1)
  t980 = (0.2e1 * t977 - 0.2e1) * t493
  t981 = t980 * t5
  t986 = 0.51785000000000000000000000000000000000000000000000e1 * t896 + 0.90577500000000000000000000000000000000000000000000e0 * t895 + 0.11003250000000000000000000000000000000000000000000e0 * t899 + 0.12417750000000000000000000000000000000000000000000e0 * t902
  t989 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t986
  t990 = jnp.log(t989)
  t995 = t980 * t8
  t996 = t986 ** 2
  t997 = 0.1e1 / t996
  t1002 = -0.86308333333333333333333333333333333333333333333334e0 * t919 - 0.30192500000000000000000000000000000000000000000000e0 * t410 - 0.55016250000000000000000000000000000000000000000000e-1 * t924 - 0.82785000000000000000000000000000000000000000000000e-1 * t927
  t1004 = 0.1e1 / t989
  t1005 = t997 * t1002 * t1004
  t1010 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t895
  t1011 = t980 * t1010
  t1013 = 0.1e1 / t996 / t986
  t1014 = t1002 ** 2
  t1016 = t1013 * t1014 * t1004
  t1025 = -0.57538888888888888888888888888888888888888888888889e0 * t950 + 0.11507777777777777777777777777777777777777777777778e1 * t953 + 0.40256666666666666666666666666666666666666666666667e0 * t955 + 0.36677500000000000000000000000000000000000000000000e-1 * t959 + 0.73355000000000000000000000000000000000000000000000e-1 * t961 + 0.13797500000000000000000000000000000000000000000000e0 * t963
  t1027 = t997 * t1025 * t1004
  t1030 = t996 ** 2
  t1031 = 0.1e1 / t1030
  t1033 = t989 ** 2
  t1034 = 0.1e1 / t1033
  t1035 = t1031 * t1014 * t1034
  t1039 = -0.14764627977777777777777777777777777777777777777777e-2 * t8 * t459 * t908 - 0.35616666666666666666666666666666666666666666666666e-1 * t380 * t914 * t931 - 0.20000000000000000000000000000000000000000000000000e1 * t939 * t941 + 0.10000000000000000000000000000000000000000000000000e1 * t944 * t966 + 0.16081979498692535066756296899072713062105388428051e2 * t971 * t974 + 0.24415263074675393406472461472505321282722606644045e-3 * t981 * t917 * t231 * t990 + 0.10843581300301739842632067522386578331157260943710e-1 * t995 * t409 * t1005 + 0.11696447245269292414524477327518106963944910680856e1 * t1011 * t1016 - 0.58482236226346462072622386637590534819724553404280e0 * t1011 * t1027 - 0.17315859105681463759666483083807725165579399831905e2 * t1011 * t1035 - 0.2e1 * t630
  t1041 = params.c_os[1]
  t1043 = 0.3e1 / 0.5e1 * t108 * t111
  t1045 = 0.1e1 / t19 / t192
  t1047 = 0.4e1 * t364 * t1045
  t1048 = t1043 - t1047
  t1049 = t1048 ** 2
  t1050 = t1041 * t1049
  t1051 = t1043 + t1047
  t1052 = t1051 ** 2
  t1053 = 0.1e1 / t1052
  t1055 = params.c_os[2]
  t1056 = t1049 ** 2
  t1057 = t1056 * t1049
  t1058 = t1055 * t1057
  t1059 = t1052 ** 2
  t1061 = 0.1e1 / t1059 / t1052
  t1063 = params.c_os[3]
  t1064 = t1063 * t1057
  t1065 = t95 ** (0.1e1 / 0.3e1)
  t1066 = t1061 * t1065
  t1068 = params.c_os[4]
  t1069 = t1068 * t1049
  t1070 = t1053 * t1065
  t1072 = t1050 * t1053 + t1058 * t1061 + t1064 * t1066 + t1069 * t1070 + params.c_os[0]
  t1087 = 0.11073470983333333333333333333333333333333333333333e-2 * t8 * t409 * t908 + 0.10000000000000000000000000000000000000000000000000e1 * t944 * t931 - 0.18311447306006545054854346104378990962041954983034e-3 * t981 * t917 * t127 * t990 - 0.58482236226346462072622386637590534819724553404280e0 * t1011 * t1005 - 0.2e1 * t700
  t1088 = t1041 * t1048
  t1089 = t108 * t218
  t1093 = 0.40e2 / 0.3e1 * t364 / t19 / t201
  t1094 = -t1089 + t1093
  t1098 = t1052 * t1051
  t1099 = 0.1e1 / t1098
  t1100 = -t1089 - t1093
  t1101 = t1099 * t1100
  t1104 = t1056 * t1048
  t1105 = t1055 * t1104
  t1106 = t1061 * t1094
  t1110 = 0.1e1 / t1059 / t1098
  t1114 = t1063 * t1104
  t1118 = t1110 * t1065
  t1122 = t1064 * t1061
  t1123 = t1065 ** 2
  t1124 = 0.1e1 / t1123
  t1125 = t1124 * s0
  t1126 = t1125 * t195
  t1129 = t1068 * t1048
  t1133 = t1099 * t1065
  t1134 = t1133 * t1100
  t1137 = t1069 * t1053
  t1140 = 0.2e1 * t1088 * t1053 * t1094 - 0.2e1 * t1050 * t1101 + 0.6e1 * t1105 * t1106 - 0.6e1 * t1058 * t1110 * t1100 + 0.6e1 * t1114 * t1066 * t1094 - 0.6e1 * t1064 * t1118 * t1100 - 0.8e1 / 0.9e1 * t1122 * t1126 + 0.2e1 * t1129 * t1070 * t1094 - 0.2e1 * t1069 * t1134 - 0.8e1 / 0.9e1 * t1137 * t1126
  t1149 = -0.621814e-1 * t936 * t908 + 0.19751673498613801407483339618206552048944131217655e-1 * t980 * t1010 * t990 - 0.2e1 * t781
  t1150 = t1061 * t1124
  t1151 = t1114 * t1150
  t1152 = t1094 * s0
  t1153 = t1152 * t195
  t1156 = t1110 * t1124
  t1157 = t1064 * t1156
  t1158 = t1100 * s0
  t1159 = t1158 * t195
  t1163 = t1129 * t1053 * t1124
  t1166 = t1099 * t1124
  t1167 = t1069 * t1166
  t1170 = t1114 * t1110
  t1171 = t1065 * t1094
  t1172 = t1171 * t1100
  t1175 = t1129 * t1099
  t1178 = t1125 * t328
  t1184 = 0.1e1 / t1123 / t95
  t1185 = t1184 * t199
  t1186 = t1185 * t335
  t1192 = 0.8e1 / 0.3e1 * t108 * t368
  t1193 = 0.520e3 / 0.9e1 * t365
  t1194 = t1192 + t1193
  t1195 = t1110 * t1194
  t1198 = t1055 * t1056
  t1199 = t1094 ** 2
  t1203 = t1041 * t1199
  t1206 = t1059 ** 2
  t1207 = 0.1e1 / t1206
  t1208 = t1100 ** 2
  t1209 = t1207 * t1208
  t1212 = -0.32e2 / 0.3e1 * t1151 * t1153 + 0.32e2 / 0.3e1 * t1157 * t1159 - 0.32e2 / 0.9e1 * t1163 * t1153 + 0.32e2 / 0.9e1 * t1167 * t1159 - 0.72e2 * t1170 * t1172 - 0.8e1 * t1175 * t1172 + 0.88e2 / 0.27e2 * t1122 * t1178 + 0.88e2 / 0.27e2 * t1137 * t1178 - 0.256e3 / 0.81e2 * t1137 * t1186 - 0.256e3 / 0.81e2 * t1122 * t1186 - 0.6e1 * t1058 * t1195 + 0.30e2 * t1198 * t1061 * t1199 + 0.2e1 * t1203 * t1053 + 0.42e2 * t1058 * t1209
  t1213 = t1068 * t1199
  t1216 = 0.1e1 / t1059
  t1220 = t1192 - t1193
  t1221 = t1053 * t1220
  t1248 = t1070 * t1220
  t1254 = t1099 * t1094
  t1258 = t1063 * t1056
  t1262 = 0.42e2 * t1064 * t1207 * t1065 * t1208 + 0.6e1 * t1069 * t1216 * t1065 * t1208 - 0.72e2 * t1105 * t1110 * t1094 * t1100 - 0.2e1 * t1050 * t1099 * t1194 + 0.6e1 * t1050 * t1216 * t1208 + 0.6e1 * t1105 * t1061 * t1220 - 0.6e1 * t1064 * t1118 * t1194 + 0.6e1 * t1114 * t1066 * t1220 + 0.30e2 * t1258 * t1066 * t1199 - 0.2e1 * t1069 * t1133 * t1194 - 0.8e1 * t1088 * t1254 * t1100 + 0.2e1 * t1213 * t1070 + 0.2e1 * t1088 * t1221 + 0.2e1 * t1129 * t1248
  t1263 = t1212 + t1262
  t1288 = 0.14e2 / 0.243e3 * t28 * t5 * t1045 * t33
  t1289 = f.my_piecewise3(t38, -t1288, 0)
  t1306 = t227 * t132
  t1317 = -t125 * t1289 / 0.18e2 + t136 * t1289 / 0.240e3 - t140 * t1289 / 0.4480e4 + t144 * t1289 / 0.103680e6 - t148 * t1289 / 0.2838528e7 + t152 * t1289 / 0.89456640e8 - t156 * t1289 / 0.3185049600e10 + t160 * t1289 / 0.126340300800e12 - 0.2e1 / 0.3e1 * t136 * t1306 + t44 * t132 * t236 / 0.2e1 + t140 * t1306 / 0.8e1 - t47 * t132 * t236 / 0.16e2
  t1350 = -t144 * t1306 / 0.80e2 + 0.3e1 / 0.640e3 * t50 * t132 * t236 + t148 * t1306 / 0.1152e4 - t53 * t132 * t236 / 0.3840e4 - t152 * t1306 / 0.21504e5 + t56 * t132 * t236 / 0.86016e5 + t156 * t1306 / 0.491520e6 - t59 * t132 * t236 / 0.2293760e7 - t160 * t1306 / 0.13271040e8 + t62 * t132 * t236 / 0.70778880e8 + 0.1e1 / t61 / t124 * t1306 / 0.412876800e9 - t264 * t132 * t236 / 0.2477260800e10
  t1352 = f.my_piecewise3(t38, 0, -t1288)
  t1359 = t278 * t164
  t1364 = t74 * t270
  t1367 = t275 ** 2
  t1425 = f.my_piecewise3(t37, t1317 + t1350, -0.8e1 / 0.3e1 * t1352 * t81 - 0.8e1 * t270 * t183 - 0.8e1 * t164 * t313 - 0.8e1 / 0.3e1 * t65 * (0.7e1 / 0.2e1 * t298 * t1359 * t74 - 0.3e1 / 0.2e1 * t277 * t164 * t1364 - 0.1e1 / t1367 * t1359 * t74 / 0.4e1 - 0.6e1 * t74 * t290 * t1359 + 0.6e1 * t282 * t164 * t270 - t166 * t1352 + 0.2e1 * t1352 * t78 + 0.6e1 * t270 * t180 + 0.6e1 * t164 * t310 + 0.2e1 * t65 * (0.15e2 / 0.2e1 * t277 * t1359 * t74 - 0.6e1 * t290 * t164 * t1364 - 0.5e1 / 0.2e1 / t275 / t170 * t1359 * t74 + t171 * t1352 * t74 / 0.2e1 + 0.3e1 / 0.4e1 * t298 * t270 * t164 * t74 + 0.1e1 / t1367 / t65 * t1359 * t74 / 0.8e1 - 0.12e2 * t164 * t75 * t270 - 0.3e1 * t72 * t164 * t1364 - 0.4e1 * t175 * t1352 - t67 * t1352 * t74)))
  t1440 = t89 / t20 / t354
  t1446 = t11 / t19 / t341
  t1450 = t341 * t192
  t1451 = 0.1e1 / t1450
  t1458 = 0.1e1 / t20 / t341 / t354
  t1459 = t206 ** 2
  t1465 = t328 * t115
  t1468 = t205 * t216
  t1471 = t352 * tau0
  t1473 = 0.1e1 / t341
  t1474 = t1473 * t362
  t1478 = t663 * t1471 * t1473
  t1481 = t364 * t204
  t1484 = t110 * t327
  t1493 = f.my_piecewise3(t4, 0, -0.5e1 / 0.288e3 * t13 * t18 * t92 * t118 + t13 * t23 * t188 / 0.32e2 + t13 * t23 * t222 / 0.32e2 - 0.3e1 / 0.64e2 * t13 * t123 * t318 - 0.3e1 / 0.32e2 * t13 * t123 * t322 - 0.3e1 / 0.64e2 * t13 * t123 * t372 - 0.3e1 / 0.64e2 * t13 * t226 * t1425 * t117 - 0.9e1 / 0.64e2 * t13 * t226 * t317 * t221 - 0.9e1 / 0.64e2 * t13 * t226 * t187 * t371 - 0.3e1 / 0.64e2 * t13 * t226 * t85 * (-0.17524591866597460088888888888888888888888888888889e0 * t88 * t1440 * t98 + 0.59613213106681630976741624910410773333333333333333e-2 * t200 * t1446 * t207 - 0.61232777403326110779186449916706078955112079981056e-4 * t340 * t1451 * t345 + 0.99019633243303282909397008818307554438617996743131e-7 * t87 * t647 * t1458 / t1459 * t89 + 0.440e3 / 0.27e2 * t211 * t1465 - 0.800e3 / 0.9e1 * t353 * t1468 + 0.1000e4 / 0.9e1 * t102 * t1471 * t1474 + 0.1000e4 / 0.9e1 * t113 * t1478 - 0.800e3 / 0.9e1 * t363 * t1481 + 0.440e3 / 0.27e2 * t217 * t1484))
  t1498 = t445 * t433
  t1503 = 0.51726012919273400298984252201052768390886626637712e3 * t441 / t480 / t412 * t1498 / t483 / t403
  t1509 = 0.96491876992155210400537781394436278372632330568306e2 * t441 / t480 / t400 * t1498 * t484
  t1514 = 0.1e1 / t201
  t1516 = t1514 * t396 * t383
  t1517 = 0.1e1 / t387 / t398 * t6 * t1516 / 0.4e1
  t1519 = t9 * t194
  t1520 = t1519 * t455
  t1521 = t453 * t1520
  t1523 = t10 * t1045
  t1524 = t1523 * t411
  t1525 = t416 * t1524
  t1527 = t1045 * t11
  t1529 = t380 * t1527 * t383
  t1531 = t386 ** (-0.15e1)
  t1533 = t1531 * t6 * t1516
  t1535 = t468 * t1520
  t1537 = t426 * t1524
  t1540 = t394 * t195 * t396
  t1545 = 0.10000000000000000000000000000000000000000000000000e1 * t449 * (-0.50638000000000000000000000000000000000000000000000e1 * t1517 + 0.16879333333333333333333333333333333333333333333333e1 * t1521 - 0.19692555555555555555555555555555555555555555555555e1 * t1525 - 0.93011851851851851851851851851851851851851851851854e0 * t1529 + 0.27303333333333333333333333333333333333333333333333e0 * t1533 - 0.27303333333333333333333333333333333333333333333333e0 * t1535 - 0.31853888888888888888888888888888888888888888888890e0 * t1537 - 0.36514074074074074074074074074074074074074074074075e0 * t1540) * t435
  t1556 = 0.10685000000000000000000000000000000000000000000000e0 * t410 * t411 * t443 * t445 * t435
  t1571 = t580 * t568
  t1576 = t1503 - t1509 + t1545 - 0.32530743900905219527896202567159734993471782831130e-1 * t610 * t421 * t616 - 0.56968947174242584615102410102512416326352748836105e-3 * t605 * t1523 * t606 + t1556 - 0.21687162600603479685264135044773156662314521887420e-1 * t610 * t463 * t571 + 0.16265371950452609763948101283579867496735891415565e-1 * t610 * t421 * t620 + 0.48159733137676571081572406076840235616767705782485e0 * t610 * t421 * t624 - 0.51947577317044391278999449251423175496738199495715e2 * t614 * t596 * t591 * t599 * t568 - 0.35089341735807877243573431982554320891834732042568e1 * t614 * t596 * t1571 * t570
  t1582 = 0.1e1 / t595 / t562
  t1585 = 0.1e1 / t598 / t556
  t1593 = 0.85917975471764868594145516183295969534298037676861e0 * t410 * t411 * t481 * t445 * t484
  t1596 = 0.34450798614814814814814814814814814814814814814813e-2 * t380 * t1527 * t405
  t1598 = 0.71233333333333333333333333333333333333333333333331e-1 * t955 * t437
  t1603 = 0.53424999999999999999999999999999999999999999999999e-1 * t410 * t411 * t413 * t476 * t435
  t1605 = 0.1e1 / t595 / t553
  t1618 = -0.69046666666666666666666666666666666666666666666667e1 * t1517 + 0.23015555555555555555555555555555555555555555555556e1 * t1521 - 0.26851481481481481481481481481481481481481481481482e1 * t1525 - 0.93932222222222222222222222222222222222222222222223e0 * t1529 + 0.14671000000000000000000000000000000000000000000000e0 * t1533 - 0.14671000000000000000000000000000000000000000000000e0 * t1535 - 0.17116166666666666666666666666666666666666666666667e0 * t1537 - 0.36793333333333333333333333333333333333333333333333e0 * t1540
  t1658 = t526 * t514
  t1692 = 0.56968947174242584615102410102512416326352748836105e-3 * t380 * t1527 * t558 + 0.16562821945185185185185185185185185185185185185185e-2 * t380 * t1527 * t504 + 0.35089341735807877243573431982554320891834732042568e1 * t597 * t1571 * t570 - 0.10389515463408878255799889850284635099347639899143e3 * t576 * t1605 * t1571 * t599 + 0.58482236226346462072622386637590534819724553404280e0 * t584 * t1618 * t570 + 0.10254018858216406658218194626490193680059335835414e4 * t576 * t1582 * t1571 * t1585 + 0.10000000000000000000000000000000000000000000000000e1 * t530 * (-0.94126000000000000000000000000000000000000000000000e1 * t1517 + 0.31375333333333333333333333333333333333333333333334e1 * t1521 - 0.36604555555555555555555555555555555555555555555556e1 * t1525 - 0.16068111111111111111111111111111111111111111111111e1 * t1529 + 0.56103333333333333333333333333333333333333333333332e0 * t1533 - 0.56103333333333333333333333333333333333333333333332e0 * t1535 - 0.65453888888888888888888888888888888888888888888890e0 * t1537 - 0.46308888888888888888888888888888888888888888888888e0 * t1540) * t516 + 0.20690405167709360119593700880421107356354650655085e4 * t522 / t541 / t508 * t1658 / t544 / t502 + 0.32530743900905219527896202567159734993471782831130e-1 * t410 * t411 * t616 + 0.10274000000000000000000000000000000000000000000000e0 * t410 * t411 * t524 * t526 * t516 + 0.21687162600603479685264135044773156662314521887420e-1 * t955 * t572 - 0.16265371950452609763948101283579867496735891415565e-1 * t410 * t411 * t620 - 0.48159733137676571081572406076840235616767705782485e0 * t410 * t411 * t624 - 0.51369999999999999999999999999999999999999999999999e-1 * t410 * t411 * t509 * t537 * t516 - 0.16522625736956710527585419434107305400007076070979e1 * t410 * t411 * t542 * t526 * t545 + 0.68493333333333333333333333333333333333333333333332e-1 * t955 * t518
  t1695 = 0.60000000000000000000000000000000000000000000000000e1 * t482 * t1498 * t435
  t1707 = 0.60000000000000000000000000000000000000000000000000e1 * t444 * t675 * t476
  t1711 = 0.48245938496077605200268890697218139186316165284153e2 * t482 * t476 * t484 * t433
  t1726 = -t1556 + t1593 - t1598 + t1603 - t1503 + t1509 - t1545 - t1695 + 0.60000000000000000000000000000000000000000000000000e1 * t543 * t1658 * t516 - 0.19298375398431042080107556278887255674526466113661e3 * t522 / t541 / t499 * t1658 * t545 - t1596 + t1707 - t1711 - 0.60000000000000000000000000000000000000000000000000e1 * t525 * t681 * t537 + 0.96491876992155210400537781394436278372632330568306e2 * t543 * t537 * t545 * t514 - 0.35089341735807877243573431982554320891834732042568e1 * t579 * t687 * t591 + 0.51947577317044391278999449251423175496738199495715e2 * t597 * t591 * t599 * t568
  t1729 = 0.35089341735807877243573431982554320891834732042568e1 * t614 * t578 * t568 * t592 - 0.10254018858216406658218194626490193680059335835414e4 * t614 * t1582 * t1571 * t1585 - t1593 + t1596 + t1598 - t1603 + 0.10389515463408878255799889850284635099347639899143e3 * t614 * t1605 * t1571 * t599 - 0.58482236226346462072622386637590534819724553404280e0 * t614 * t563 * t1618 * t570 + t494 * (t1692 + t1726) + t1695 - t1707 + t1711
  t1733 = f.my_piecewise3(t4, 0, t379 * (t1576 + t1729) / 0.2e1)
  t1744 = 0.1e1 / t20 / t790
  t1770 = t650 * t341
  t1772 = 0.1e1 / t19 / t1770
  t1793 = t648 / t1770 * t655 * t1471
  t1805 = t727 / t650 / t341 / r0 * t734 * t352
  t1819 = t827 / t650 / t342 * t833 * tau0
  t1830 = 0.440e3 / 0.27e2 * t709 * t1465 - 0.13231533800628034424491377620272646158087511486088e4 * t664 * t827 * t1772 * t834 + 0.12921047361994151369322424074358658189992665660839e4 * t664 * t727 * t1744 * t761 + 0.75814722342389033960416881498888376199140004256300e2 * t659 * t112 * t663 * t1793 + 0.45488833405433420376250128899333025719484002553780e3 * t788 * t751 * t1793 + 0.51217540743425396310901482787592126716553178131495e3 * t788 * t663 * t1805 + 0.75814722342389033960416881498888376199140004256300e3 * t740 * t811 * t1793 + 0.13658010864913439016240395410024567124414180835065e4 * t740 * t751 * t1805 + 0.89705313902562945250789000815407770563305162617550e3 * t740 * t663 * t1819 + 0.37907361171194516980208440749444188099570002128150e3 * t661 / t662 / t361 * t1793 + 0.85362567905708993851502471312653544527588630219158e3 * t661 * t811 * t1805
  t1843 = 0.1e1 / t729
  t1852 = t827 * s0
  t1854 = 0.1e1 / t650 / t1450
  t1857 = 0.1e1 / t832 / t634
  t1879 = t822 * t655 * t110
  t1883 = t830 * t734 * t806
  t1887 = t804 * t655 * t364
  t1898 = -0.11160639870142233192473158852867580790925790694182e3 * t885 * t1451 * t886 + 0.1000e4 / 0.9e1 * t639 * t1471 * t1474 + 0.2000e4 / 0.9e1 * t642 * t1471 * t1474 + 0.44889996811661897640650203150707619215378528852739e3 * t646 * t1852 * t1854 * t1857 + 0.10846559609784457791936975179774297021556963275601e4 * t753 * t1879 - 0.19633390618313068585845568401910315241345384950406e4 * t801 * t1883 - 0.10614061127934464754458363409844372667879600595882e4 * t813 * t1887 - 0.19633390618313068585845568401910315241345384950406e4 * t817 * t1883 + 0.10846559609784457791936975179774297021556963275601e4 * t742 * t1879 - 0.63684366767606788526750180459066236007277603575291e3 * t789 * t1887 - 0.16982497804695143607133381455750996268607360953411e4 * t797 * t1887
  t1919 = t940 * t929
  t1938 = 0.1e1 / t896 / t902 * t6 * t1514 / 0.4e1
  t1940 = t948 * t194
  t1941 = t947 * t1940
  t1943 = t917 * t1045
  t1944 = t916 * t1943
  t1946 = t8 * t1523
  t1948 = t895 ** (-0.15e1)
  t1950 = t1948 * t6 * t1514
  t1952 = t958 * t1940
  t1954 = t923 * t1943
  t1956 = t393 * t1519
  t1968 = -0.21687162600603479685264135044773156662314521887420e-1 * t995 * t459 * t1005 + 0.16265371950452609763948101283579867496735891415565e-1 * t995 * t409 * t1027 + 0.48159733137676571081572406076840235616767705782485e0 * t995 * t409 * t1035 - 0.32530743900905219527896202567159734993471782831130e-1 * t995 * t409 * t1016 + 0.48245938496077605200268890697218139186316165284153e2 * t971 * t965 * t973 * t929 + 0.60000000000000000000000000000000000000000000000000e1 * t971 * t1919 * t930 - 0.60000000000000000000000000000000000000000000000000e1 * t939 * t931 * t965 - 0.56968947174242584615102410102512416326352748836105e-3 * t981 * t917 * t1045 * t990 + 0.10685000000000000000000000000000000000000000000000e0 * t380 * t127 * t938 * t941 + 0.10000000000000000000000000000000000000000000000000e1 * t944 * (-0.25319000000000000000000000000000000000000000000000e1 * t1938 + 0.16879333333333333333333333333333333333333333333333e1 * t1941 - 0.19692555555555555555555555555555555555555555555555e1 * t1944 - 0.93011851851851851851851851851851851851851851851854e0 * t1946 + 0.13651666666666666666666666666666666666666666666667e0 * t1950 - 0.27303333333333333333333333333333333333333333333333e0 * t1952 - 0.31853888888888888888888888888888888888888888888890e0 * t1954 - 0.36514074074074074074074074074074074074074074074075e0 * t1956) * t930 - 0.96491876992155210400537781394436278372632330568306e2 * t936 / t969 / t904 * t1919 * t973
  t1974 = t1014 * t1002
  t2034 = -0.51947577317044391278999449251423175496738199495715e2 * t1011 * t1031 * t1025 * t1034 * t1002 - 0.35089341735807877243573431982554320891834732042568e1 * t1011 * t1031 * t1974 * t1004 + 0.35089341735807877243573431982554320891834732042568e1 * t1011 * t1013 * t1002 * t1004 * t1025 + 0.71233333333333333333333333333333333333333333333331e-1 * t380 * t231 * t913 * t931 - 0.53424999999999999999999999999999999999999999999999e-1 * t380 * t914 * t966 - 0.85917975471764868594145516183295969534298037676861e0 * t380 * t127 * t970 * t974 - 0.2e1 * t1733 + 0.34450798614814814814814814814814814814814814814813e-2 * t8 * t1523 * t908 + 0.51726012919273400298984252201052768390886626637712e3 * t936 / t969 / t912 * t1919 / t972 / t907 - 0.10254018858216406658218194626490193680059335835414e4 * t1011 / t1030 / t996 * t1974 / t1033 / t989 - 0.58482236226346462072622386637590534819724553404280e0 * t1011 * t997 * (-0.34523333333333333333333333333333333333333333333333e1 * t1938 + 0.23015555555555555555555555555555555555555555555556e1 * t1941 - 0.26851481481481481481481481481481481481481481481482e1 * t1944 - 0.93932222222222222222222222222222222222222222222223e0 * t1946 + 0.73355000000000000000000000000000000000000000000000e-1 * t1950 - 0.14671000000000000000000000000000000000000000000000e0 * t1952 - 0.17116166666666666666666666666666666666666666666667e0 * t1954 - 0.36793333333333333333333333333333333333333333333333e0 * t1956) * t1004 + 0.10389515463408878255799889850284635099347639899143e3 * t1011 / t1030 / t986 * t1974 * t1034
  t2041 = t1049 * t1048
  t2043 = t1199 * t1094
  t2048 = 0.1e1 / t1206 / t1051
  t2050 = t1208 * t1100
  t2055 = 0.1e1 / t1059 / t1051
  t2081 = t1065 * t1194 * t1100
  t2094 = t1065 * t1220 * t1100
  t2097 = t1171 * t1194
  t2102 = 0.120e3 * t1063 * t2041 * t1066 * t2043 - 0.336e3 * t1064 * t2048 * t1065 * t2050 - 0.24e2 * t1069 * t2055 * t1065 * t2050 - 0.12e2 * t1213 * t1134 + 0.36e2 * t1088 * t1216 * t1094 * t1208 + 0.90e2 * t1198 * t1106 * t1220 + 0.756e3 * t1105 * t1209 * t1094 + 0.126e3 * t1058 * t1207 * t1100 * t1194 + 0.6e1 * t1068 * t1094 * t1248 + 0.18e2 * t1069 * t1216 * t2081 - 0.540e3 * t1258 * t1110 * t1065 * t1199 * t1100 + 0.90e2 * t1258 * t1061 * t1171 * t1220 - 0.108e3 * t1170 * t2094 - 0.108e3 * t1170 * t2097 - 0.12e2 * t1175 * t2094
  t2107 = t1171 * t1208
  t2119 = 0.1e1 / t1123 / t199 / t11 / t356 * t339 * t1451 / 0.2e1
  t2128 = t1152 * t195 * t1100
  t2134 = t1185 * t1446
  t2139 = t1125 * t1440
  t2158 = 0.126e3 * t1064 * t1207 * t2081 + 0.756e3 * t1114 * t1207 * t2107 + 0.36e2 * t1129 * t1216 * t2107 - 0.20480e5 / 0.729e3 * t1137 * t2119 - 0.20480e5 / 0.729e3 * t1122 * t2119 - 0.12e2 * t1175 * t2097 + 0.64e2 / 0.3e1 * t1129 * t1166 * t2128 + 0.192e3 * t1114 * t1156 * t2128 + 0.2816e4 / 0.81e2 * t1122 * t2134 + 0.2816e4 / 0.81e2 * t1137 * t2134 - 0.1232e4 / 0.81e2 * t1137 * t2139 - 0.16e2 / 0.3e1 * t1213 * t1053 * t1126 - 0.1232e4 / 0.81e2 * t1122 * t2139 - 0.540e3 * t1198 * t1110 * t1199 * t1100 + 0.120e3 * t1055 * t2041 * t1061 * t2043 - 0.336e3 * t1058 * t2048 * t2050
  t2169 = 0.88e2 / 0.9e1 * t108 * t1484
  t2170 = 0.8320e4 / 0.27e2 * t1481
  t2171 = -t2169 + t2170
  t2175 = -t2169 - t2170
  t2211 = -0.24e2 * t1050 * t2055 * t2050 - 0.12e2 * t1203 * t1101 + 0.6e1 * t1041 * t1094 * t1221 + 0.2e1 * t1088 * t1053 * t2171 - 0.2e1 * t1050 * t1099 * t2175 + 0.6e1 * t1105 * t1061 * t2171 - 0.6e1 * t1058 * t1110 * t2175 - 0.108e3 * t1105 * t1195 * t1094 - 0.2e1 * t1069 * t1133 * t2175 - 0.12e2 * t1088 * t1099 * t1220 * t1100 - 0.12e2 * t1088 * t1254 * t1194 + 0.6e1 * t1114 * t1066 * t2171 - 0.6e1 * t1064 * t1118 * t2175 + 0.2e1 * t1129 * t1070 * t2171 + 0.18e2 * t1050 * t1216 * t1100 * t1194
  t2219 = t1100 * t199 * t335
  t2223 = t1220 * s0 * t195
  t2229 = t1094 * t199 * t335
  t2233 = t1194 * s0 * t195
  t2248 = t1158 * t328
  t2256 = t1152 * t328
  t2262 = t1208 * s0 * t195
  t2273 = -0.108e3 * t1105 * t1110 * t1220 * t1100 + 0.512e3 / 0.9e1 * t1064 * t1110 * t1184 * t2219 - 0.16e2 / 0.3e1 * t1163 * t2223 - 0.512e3 / 0.27e2 * t1129 * t1053 * t1184 * t2229 + 0.16e2 / 0.3e1 * t1167 * t2233 + 0.512e3 / 0.27e2 * t1069 * t1099 * t1184 * t2219 - 0.16e2 * t1151 * t2223 - 0.512e3 / 0.9e1 * t1114 * t1061 * t1184 * t2229 + 0.16e2 * t1157 * t2233 - 0.176e3 / 0.9e1 * t1167 * t2248 - 0.80e2 * t1258 * t1150 * t1199 * s0 * t195 + 0.176e3 / 0.3e1 * t1151 * t2256 - 0.112e3 * t1064 * t1207 * t1124 * t2262 - 0.176e3 / 0.3e1 * t1157 * t2248 + 0.176e3 / 0.9e1 * t1163 * t2256 - 0.16e2 * t1069 * t1216 * t1124 * t2262
  v3rho3_0_ = 0.6e1 * t377 + 0.6e1 * t630 * t669 + 0.12e2 * t700 * t765 + 0.6e1 * t781 * t891 + 0.3e1 * t1039 * t1072 + 0.6e1 * t1087 * t1140 + 0.3e1 * t1149 * t1263 + r0 * (0.2e1 * t1493 + 0.2e1 * t1733 * t669 + 0.6e1 * t630 * t765 + 0.6e1 * t700 * t891 + 0.2e1 * t781 * (-0.21406695150080305706666666666666666666666666666667e2 * t632 * t1440 * t635 + 0.12921047361994151369322424074358658189992665660839e4 * t728 * t1744 * t734 * t89 + 0.22045916661856114751893094984836334570490478532646e2 * t631 * t647 * t1458 / t653 * t89 + 0.1000e4 / 0.9e1 * t640 * t1478 + 0.2000e4 / 0.3e1 * t715 * t1478 + 0.4000e4 / 0.9e1 * t644 * t751 * t1471 * t1473 - 0.800e3 / 0.9e1 * t870 * t1468 - 0.800e3 / 0.9e1 * t867 * t1468 + 0.88950000439928292645315451753817241600000000000000e2 * t704 * t1446 * t705 - 0.13231533800628034424491377620272646158087511486088e4 * t877 * t1772 * t833 * t11 + t1830 + 0.89705313902562945250789000815407770563305162617550e3 * t661 * t751 * t1819 - 0.3200e4 / 0.9e1 * t853 * t1481 - 0.800e3 / 0.3e1 * t856 * t1481 + 0.880e3 / 0.27e2 * t716 * t1484 + 0.880e3 / 0.27e2 * t719 * t1484 - 0.83517498132375759810795236659175435220972628688737e3 * t664 * t648 * t1843 * t655 + 0.440e3 / 0.27e2 * t712 * t1484 - 0.800e3 / 0.9e1 * t850 * t1481 + 0.44889996811661897640650203150707619215378528852739e3 * t664 * t1852 * t1854 * t1857 - 0.83517498132375759810795236659175435220972628688737e3 * t649 * t1843 * t655 + t1898) + (t1968 + t2034) * t1072 + 0.3e1 * t1039 * t1140 + 0.3e1 * t1087 * t1263 + t1149 * (t2102 + t2158 + t2211 + t2273))

  res = {'v3rho3': v3rho3_0_}
  return res
