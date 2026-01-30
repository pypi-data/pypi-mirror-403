"""Generated from hyb_mgga_xc_wb97mv.mpl."""

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

  b97mv_par_n = 6

  b97mv_gamma_x = 0.004

  b97mv_par_x = [None, np.array([np.nan, params_c_x[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_x[2], 0, 1], dtype=np.float64), np.array([np.nan, params_c_x[3], 1, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_ss = 0.2

  b97mv_par_ss = [None, np.array([np.nan, params_c_ss[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_ss[2], 0, 4], dtype=np.float64), np.array([np.nan, params_c_ss[3], 1, 0], dtype=np.float64), np.array([np.nan, params_c_ss[4], 2, 0], dtype=np.float64), np.array([np.nan, params_c_ss[5], 4, 3], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_os = 0.006

  b97mv_par_os = [None, np.array([np.nan, params_c_os[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_os[2], 1, 0], dtype=np.float64), np.array([np.nan, params_c_os[3], 2, 0], dtype=np.float64), np.array([np.nan, params_c_os[4], 2, 1], dtype=np.float64), np.array([np.nan, params_c_os[5], 6, 0], dtype=np.float64), np.array([np.nan, params_c_os[6], 6, 1], dtype=np.float64)]

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

  b97mv_wx_ss = lambda t, dummy=None: (K_FACTOR_C - t) / (K_FACTOR_C + t)

  b97mv_wx_os = lambda ts0, ts1: (K_FACTOR_C * (ts0 + ts1) - 2 * ts0 * ts1) / (K_FACTOR_C * (ts0 + ts1) + 2 * ts0 * ts1)

  b97mv_g = lambda mgamma, wx, ux, cc, n, xs, ts0, ts1: jnp.sum(jnp.array([cc[i][1] * wx(ts0, ts1) ** cc[i][2] * ux(mgamma, xs) ** cc[i][3] for i in range(1, n + 1)]), axis=0)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  b97mv_ux_ss = lambda mgamma, x: b97mv_ux(mgamma, x)

  b97mv_ux_os = lambda mgamma, x: b97mv_ux(mgamma, x)

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

  b97mv_par_n = 6

  b97mv_gamma_x = 0.004

  b97mv_par_x = [None, np.array([np.nan, params_c_x[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_x[2], 0, 1], dtype=np.float64), np.array([np.nan, params_c_x[3], 1, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_ss = 0.2

  b97mv_par_ss = [None, np.array([np.nan, params_c_ss[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_ss[2], 0, 4], dtype=np.float64), np.array([np.nan, params_c_ss[3], 1, 0], dtype=np.float64), np.array([np.nan, params_c_ss[4], 2, 0], dtype=np.float64), np.array([np.nan, params_c_ss[5], 4, 3], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_os = 0.006

  b97mv_par_os = [None, np.array([np.nan, params_c_os[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_os[2], 1, 0], dtype=np.float64), np.array([np.nan, params_c_os[3], 2, 0], dtype=np.float64), np.array([np.nan, params_c_os[4], 2, 1], dtype=np.float64), np.array([np.nan, params_c_os[5], 6, 0], dtype=np.float64), np.array([np.nan, params_c_os[6], 6, 1], dtype=np.float64)]

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

  b97mv_wx_ss = lambda t, dummy=None: (K_FACTOR_C - t) / (K_FACTOR_C + t)

  b97mv_wx_os = lambda ts0, ts1: (K_FACTOR_C * (ts0 + ts1) - 2 * ts0 * ts1) / (K_FACTOR_C * (ts0 + ts1) + 2 * ts0 * ts1)

  b97mv_g = lambda mgamma, wx, ux, cc, n, xs, ts0, ts1: jnp.sum(jnp.array([cc[i][1] * wx(ts0, ts1) ** cc[i][2] * ux(mgamma, xs) ** cc[i][3] for i in range(1, n + 1)]), axis=0)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  b97mv_ux_ss = lambda mgamma, x: b97mv_ux(mgamma, x)

  b97mv_ux_os = lambda mgamma, x: b97mv_ux(mgamma, x)

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

  b97mv_par_n = 6

  b97mv_gamma_x = 0.004

  b97mv_par_x = [None, np.array([np.nan, params_c_x[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_x[2], 0, 1], dtype=np.float64), np.array([np.nan, params_c_x[3], 1, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_ss = 0.2

  b97mv_par_ss = [None, np.array([np.nan, params_c_ss[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_ss[2], 0, 4], dtype=np.float64), np.array([np.nan, params_c_ss[3], 1, 0], dtype=np.float64), np.array([np.nan, params_c_ss[4], 2, 0], dtype=np.float64), np.array([np.nan, params_c_ss[5], 4, 3], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_os = 0.006

  b97mv_par_os = [None, np.array([np.nan, params_c_os[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_os[2], 1, 0], dtype=np.float64), np.array([np.nan, params_c_os[3], 2, 0], dtype=np.float64), np.array([np.nan, params_c_os[4], 2, 1], dtype=np.float64), np.array([np.nan, params_c_os[5], 6, 0], dtype=np.float64), np.array([np.nan, params_c_os[6], 6, 1], dtype=np.float64)]

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

  b97mv_wx_ss = lambda t, dummy=None: (K_FACTOR_C - t) / (K_FACTOR_C + t)

  b97mv_wx_os = lambda ts0, ts1: (K_FACTOR_C * (ts0 + ts1) - 2 * ts0 * ts1) / (K_FACTOR_C * (ts0 + ts1) + 2 * ts0 * ts1)

  b97mv_g = lambda mgamma, wx, ux, cc, n, xs, ts0, ts1: jnp.sum(jnp.array([cc[i][1] * wx(ts0, ts1) ** cc[i][2] * ux(mgamma, xs) ** cc[i][3] for i in range(1, n + 1)]), axis=0)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  b97mv_ux_ss = lambda mgamma, x: b97mv_ux(mgamma, x)

  b97mv_ux_os = lambda mgamma, x: b97mv_ux(mgamma, x)

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
  t8 = jnp.logical_or(r0 <= f.p.dens_threshold, t7)
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
  t104 = 0.1e1 + 0.4e-2 * t102
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
  t125 = t94 + 0.4e-2 * t96 * t101 * t105 + t121 * t123
  t126 = t93 * t125
  t127 = t26 * t126
  t130 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t19 * t127)
  t132 = 0.1e1 - t5
  t133 = t132 <= f.p.zeta_threshold
  t134 = jnp.logical_or(r1 <= f.p.dens_threshold, t133)
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
  t202 = 0.1e1 + 0.4e-2 * t200
  t203 = 0.1e1 / t202
  t208 = 0.1e1 / t197 / r1
  t209 = tau1 * t208
  t210 = t116 - t209
  t211 = t109 * t210
  t212 = t116 + t209
  t213 = 0.1e1 / t212
  t215 = t94 + 0.4e-2 * t194 * t199 * t203 + t211 * t213
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
  t292 = params.c_ss[1]
  t293 = s0 ** 2
  t294 = t293 ** 2
  t295 = t292 * t294
  t296 = t97 ** 2
  t297 = t296 ** 2
  t300 = 0.1e1 / t99 / t297 / t97
  t302 = 0.1e1 + 0.2e0 * t102
  t303 = t302 ** 2
  t304 = t303 ** 2
  t305 = 0.1e1 / t304
  t306 = t300 * t305
  t309 = params.c_ss[2]
  t310 = t309 * t120
  t312 = params.c_ss[3]
  t313 = t120 ** 2
  t314 = t312 * t313
  t315 = t122 ** 2
  t316 = 0.1e1 / t315
  t318 = params.c_ss[4]
  t319 = t313 ** 2
  t320 = t318 * t319
  t321 = t315 ** 2
  t322 = 0.1e1 / t321
  t323 = t320 * t322
  t324 = t293 * s0
  t325 = 0.1e1 / t297
  t328 = 0.1e1 / t303 / t302
  t332 = t291 + 0.16e-2 * t295 * t306 + t310 * t123 + t314 * t316 + 0.8e-2 * t323 * t324 * t325 * t328
  t333 = t290 * t332
  t334 = f.my_piecewise3(t133, f.p.zeta_threshold, t132)
  t335 = t132 ** (0.1e1 / 0.3e1)
  t337 = f.my_piecewise3(t133, t224, 0.1e1 / t335)
  t339 = t223 * t37 * t337
  t341 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t339
  t342 = jnp.sqrt(t339)
  t345 = t339 ** 0.15e1
  t347 = t337 ** 2
  t349 = t239 * t243 * t347
  t351 = 0.23615562999000000000000000000000000000000000000000e0 * t342 + 0.55770497660000000000000000000000000000000000000000e-1 * t339 + 0.12733196185000000000000000000000000000000000000000e-1 * t345 + 0.76629248290000000000000000000000000000000000000000e-2 * t349
  t353 = 0.1e1 + 0.1e1 / t351
  t354 = jnp.log(t353)
  t355 = t341 * t354
  t357 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t339
  t362 = 0.21948324211500000000000000000000000000000000000000e0 * t342 + 0.48172707847500000000000000000000000000000000000000e-1 * t339 + 0.13082189292500000000000000000000000000000000000000e-1 * t345 + 0.48592432297500000000000000000000000000000000000000e-2 * t349
  t364 = 0.1e1 + 0.1e1 / t362
  t365 = jnp.log(t364)
  t368 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t339
  t373 = 0.17489762330000000000000000000000000000000000000000e0 * t342 + 0.30591463695000000000000000000000000000000000000000e-1 * t339 + 0.37162156485000000000000000000000000000000000000000e-2 * t345 + 0.41939460495000000000000000000000000000000000000000e-2 * t349
  t375 = 0.1e1 + 0.1e1 / t373
  t376 = jnp.log(t375)
  t377 = t368 * t376
  t383 = -t355 + t259 * (-t357 * t365 + t355 - 0.58482236226346462072622386637590534819724553404281e0 * t377) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t377
  t386 = f.my_piecewise3(t134, 0, t334 * t383 / 0.2e1)
  t387 = s2 ** 2
  t388 = t387 ** 2
  t389 = t292 * t388
  t390 = t195 ** 2
  t391 = t390 ** 2
  t394 = 0.1e1 / t197 / t391 / t195
  t396 = 0.1e1 + 0.2e0 * t200
  t397 = t396 ** 2
  t398 = t397 ** 2
  t399 = 0.1e1 / t398
  t400 = t394 * t399
  t403 = t309 * t210
  t405 = t210 ** 2
  t406 = t312 * t405
  t407 = t212 ** 2
  t408 = 0.1e1 / t407
  t410 = t405 ** 2
  t411 = t318 * t410
  t412 = t407 ** 2
  t413 = 0.1e1 / t412
  t414 = t411 * t413
  t415 = t387 * s2
  t416 = 0.1e1 / t391
  t419 = 0.1e1 / t397 / t396
  t423 = t291 + 0.16e-2 * t389 * t400 + t403 * t213 + t406 * t408 + 0.8e-2 * t414 * t415 * t416 * t419
  t424 = t386 * t423
  t426 = t222 * t15 * t36
  t428 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t426
  t429 = jnp.sqrt(t426)
  t432 = t426 ** 0.15e1
  t435 = t238 * t14 * t241
  t437 = 0.23615562999000000000000000000000000000000000000000e0 * t429 + 0.55770497660000000000000000000000000000000000000000e-1 * t426 + 0.12733196185000000000000000000000000000000000000000e-1 * t432 + 0.76629248290000000000000000000000000000000000000000e-2 * t435
  t439 = 0.1e1 + 0.1e1 / t437
  t440 = jnp.log(t439)
  t441 = t428 * t440
  t442 = t2 ** 2
  t443 = t442 ** 2
  t444 = t3 ** 2
  t445 = t444 ** 2
  t446 = 0.1e1 / t445
  t447 = t443 * t446
  t448 = t225 * t6
  t449 = f.my_piecewise3(t7, t22, t448)
  t450 = t335 * t132
  t451 = f.my_piecewise3(t133, t22, t450)
  t453 = (t449 + t451 - 0.2e1) * t258
  t455 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t426
  t460 = 0.21948324211500000000000000000000000000000000000000e0 * t429 + 0.48172707847500000000000000000000000000000000000000e-1 * t426 + 0.13082189292500000000000000000000000000000000000000e-1 * t432 + 0.48592432297500000000000000000000000000000000000000e-2 * t435
  t462 = 0.1e1 + 0.1e1 / t460
  t463 = jnp.log(t462)
  t466 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t426
  t471 = 0.17489762330000000000000000000000000000000000000000e0 * t429 + 0.30591463695000000000000000000000000000000000000000e-1 * t426 + 0.37162156485000000000000000000000000000000000000000e-2 * t432 + 0.41939460495000000000000000000000000000000000000000e-2 * t435
  t473 = 0.1e1 + 0.1e1 / t471
  t474 = jnp.log(t473)
  t475 = t466 * t474
  t477 = -t455 * t463 + t441 - 0.58482236226346462072622386637590534819724553404281e0 * t475
  t478 = t453 * t477
  t482 = -t441 + t447 * t478 + 0.58482236226346462072622386637590534819724553404281e0 * t453 * t475 - t290 - t386
  t484 = params.c_os[1]
  t487 = 0.3e1 / 0.10e2 * t115 * (t119 + t209)
  t489 = 0.2e1 * t119 * t209
  t490 = t487 - t489
  t491 = t484 * t490
  t492 = t487 + t489
  t493 = 0.1e1 / t492
  t495 = params.c_os[2]
  t496 = t490 ** 2
  t497 = t495 * t496
  t498 = t492 ** 2
  t499 = 0.1e1 / t498
  t501 = params.c_os[3]
  t502 = t501 * t496
  t503 = 0.30000000000000000000000000000000000000000000000000e-2 * t102
  t504 = 0.30000000000000000000000000000000000000000000000000e-2 * t200
  t505 = t503 + t504
  t507 = 0.1e1 + t503 + t504
  t508 = 0.1e1 / t507
  t511 = params.c_os[4]
  t512 = t496 ** 2
  t513 = t512 * t496
  t514 = t511 * t513
  t515 = t498 ** 2
  t517 = 0.1e1 / t515 / t498
  t519 = params.c_os[5]
  t520 = t519 * t513
  t524 = t502 * t499 * t505 * t508 + t520 * t517 * t505 * t508 + t491 * t493 + t497 * t499 + t514 * t517 + params.c_os[0]
  t525 = t482 * t524
  t527 = t2 / t444
  t528 = t4 - t527
  t529 = t528 / 0.2e1
  t534 = t24 * t241
  t537 = t19 * t534 * t126 / 0.32e2
  t540 = t15 * t17 * t24
  t541 = t11 * t13 * t540
  t545 = t25 / t28 / t27 * t92
  t546 = t6 ** 2
  t547 = 0.1e1 / t546
  t548 = t125 * t547
  t553 = t47 * t46
  t554 = 0.1e1 / t553
  t556 = 0.1e1 / t25 / t3
  t557 = t556 * t17
  t559 = t35 * t557 * t40
  t561 = t33 * t34 * t36
  t562 = t28 ** 2
  t564 = t17 / t562
  t565 = t39 * t547
  t570 = -t561 * t564 * t565 * t528 / 0.54e2 - t559 / 0.54e2
  t571 = f.my_piecewise3(t45, t570, 0)
  t574 = t50 * t46
  t575 = 0.1e1 / t574
  t578 = t50 * t553
  t579 = 0.1e1 / t578
  t583 = 0.1e1 / t56 / t46
  t587 = 0.1e1 / t56 / t553
  t591 = 0.1e1 / t56 / t574
  t595 = 0.1e1 / t56 / t578
  t599 = 0.1e1 / t68 / t46
  t603 = f.my_piecewise3(t45, 0, t570)
  t605 = t81 * t79
  t610 = 0.1e1 / t78 / t72
  t614 = t72 * t82
  t626 = f.my_piecewise3(t44, -t554 * t571 / 0.18e2 + t575 * t571 / 0.240e3 - t579 * t571 / 0.4480e4 + t583 * t571 / 0.103680e6 - t587 * t571 / 0.2838528e7 + t591 * t571 / 0.89456640e8 - t595 * t571 / 0.3185049600e10 + t599 * t571 / 0.126340300800e12, -0.8e1 / 0.3e1 * t603 * t88 - 0.8e1 / 0.3e1 * t72 * (-t605 * t603 + 0.2e1 * t603 * t85 + 0.2e1 * t72 * (t610 * t603 * t81 / 0.2e1 - 0.4e1 * t614 * t603 - t74 * t603 * t81)))
  t632 = t97 * r0
  t634 = 0.1e1 / t99 / t632
  t639 = t296 * t97
  t642 = t104 ** 2
  t643 = 0.1e1 / t642
  t648 = t101 * t123
  t652 = t316 * tau0 * t101
  t661 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t529 * t10 * t18 * t127 - t537 - t541 * t545 * t548 * t528 / 0.32e2 - 0.3e1 / 0.32e2 * t19 * t26 * t29 * t626 * t125 - 0.3e1 / 0.32e2 * t19 * t26 * t93 * (-0.10666666666666666666666666666666666666666666666667e-1 * t96 * t634 * t105 + 0.42666666666666666666666666666666666666666666666668e-4 * t95 * t293 / t98 / t639 * t643 + 0.5e1 / 0.3e1 * t109 * tau0 * t648 + 0.5e1 / 0.3e1 * t121 * t652))
  t669 = t137 * t534 * t216 / 0.32e2
  t671 = t136 * t13 * t540
  t675 = t25 / t139 / t138 * t192
  t676 = t132 ** 2
  t677 = 0.1e1 / t676
  t678 = t215 * t677
  t679 = -t528
  t684 = t148 * t147
  t685 = 0.1e1 / t684
  t687 = t35 * t557 * t141
  t688 = t139 ** 2
  t690 = t17 / t688
  t691 = t39 * t677
  t696 = -t561 * t690 * t691 * t679 / 0.54e2 - t687 / 0.54e2
  t697 = f.my_piecewise3(t146, t696, 0)
  t700 = t151 * t147
  t701 = 0.1e1 / t700
  t704 = t151 * t684
  t705 = 0.1e1 / t704
  t709 = 0.1e1 / t157 / t147
  t713 = 0.1e1 / t157 / t684
  t717 = 0.1e1 / t157 / t700
  t721 = 0.1e1 / t157 / t704
  t725 = 0.1e1 / t169 / t147
  t729 = f.my_piecewise3(t146, 0, t696)
  t731 = t181 * t179
  t736 = 0.1e1 / t178 / t173
  t740 = t173 * t182
  t752 = f.my_piecewise3(t145, -t685 * t697 / 0.18e2 + t701 * t697 / 0.240e3 - t705 * t697 / 0.4480e4 + t709 * t697 / 0.103680e6 - t713 * t697 / 0.2838528e7 + t717 * t697 / 0.89456640e8 - t721 * t697 / 0.3185049600e10 + t725 * t697 / 0.126340300800e12, -0.8e1 / 0.3e1 * t729 * t188 - 0.8e1 / 0.3e1 * t173 * (-t731 * t729 + 0.2e1 * t729 * t185 + 0.2e1 * t173 * (t736 * t729 * t181 / 0.2e1 - 0.4e1 * t740 * t729 - t174 * t729 * t181)))
  t759 = f.my_piecewise3(t134, 0, 0.3e1 / 0.32e2 * t529 * t10 * t18 * t217 - t669 - t671 * t675 * t678 * t679 / 0.32e2 - 0.3e1 / 0.32e2 * t137 * t26 * t140 * t752 * t215)
  t760 = f.my_piecewise3(t7, 0, t528)
  t763 = t223 * t557 * t227
  t764 = 0.11073470983333333333333333333333333333333333333333e-2 * t763
  t765 = 0.1e1 / t448
  t768 = f.my_piecewise3(t7, 0, -t765 * t528 / 0.3e1)
  t770 = t223 * t37 * t768
  t773 = (-t764 + 0.33220412950000000000000000000000000000000000000000e-2 * t770) * t251
  t774 = t248 ** 2
  t776 = t231 / t774
  t777 = 0.1e1 / t232
  t778 = t763 / 0.3e1
  t779 = -t778 + t770
  t780 = t777 * t779
  t782 = 0.18590165886666666666666666666666666666666666666667e-1 * t763
  t784 = t229 ** 0.5e0
  t785 = t784 * t779
  t788 = 0.1e1 / t240 / t3
  t789 = t788 * t242
  t791 = t239 * t789 * t244
  t792 = 0.51086165526666666666666666666666666666666666666667e-2 * t791
  t795 = t239 * t243 * t227 * t768
  t798 = 0.1e1 / t250
  t800 = t776 * (0.11807781499500000000000000000000000000000000000000e0 * t780 - t782 + 0.55770497660000000000000000000000000000000000000000e-1 * t770 + 0.19099794277500000000000000000000000000000000000000e-1 * t785 - t792 + 0.15325849658000000000000000000000000000000000000000e-1 * t795) * t798
  t801 = 0.53237641966666666666666666666666666666666666666667e-3 * t763
  t805 = t266 ** 2
  t807 = t261 / t805
  t809 = 0.16057569282500000000000000000000000000000000000000e-1 * t763
  t812 = 0.32394954865000000000000000000000000000000000000000e-2 * t791
  t815 = 0.1e1 / t268
  t818 = 0.31311127083333333333333333333333333333333333333333e-3 * t763
  t821 = (-t818 + 0.93933381250000000000000000000000000000000000000000e-3 * t770) * t280
  t823 = t277 ** 2
  t824 = 0.1e1 / t823
  t825 = t272 * t824
  t827 = 0.10197154565000000000000000000000000000000000000000e-1 * t763
  t830 = 0.27959640330000000000000000000000000000000000000000e-2 * t791
  t832 = 0.87448811650000000000000000000000000000000000000000e-1 * t780 - t827 + 0.30591463695000000000000000000000000000000000000000e-1 * t770 + 0.55743234727500000000000000000000000000000000000000e-2 * t785 - t830 + 0.83878920990000000000000000000000000000000000000000e-2 * t795
  t833 = 0.1e1 / t279
  t841 = t259 * t272
  t850 = f.my_piecewise3(t8, 0, t760 * t287 / 0.2e1 + t221 * (-t773 + t800 + t259 * (-(-t801 + 0.15971292590000000000000000000000000000000000000000e-2 * t770) * t269 + t807 * (0.10974162105750000000000000000000000000000000000000e0 * t780 - t809 + 0.48172707847500000000000000000000000000000000000000e-1 * t770 + 0.19623283938750000000000000000000000000000000000000e-1 * t785 - t812 + 0.97184864595000000000000000000000000000000000000000e-2 * t795) * t815 + t773 - t800 - 0.58482236226346462072622386637590534819724553404281e0 * t821 + 0.58482236226346462072622386637590534819724553404281e0 * t825 * t832 * t833) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t821 - 0.58482236226346462072622386637590534819724553404281e0 * t841 * t824 * t832 * t833) / 0.2e1)
  t854 = 0.1e1 / t99 / t297 / t632
  t864 = 0.1e1 / t304 / t302
  t873 = t312 * t120
  t877 = 0.1e1 / t315 / t122
  t884 = t318 * t313 * t120 * t322
  t885 = t324 * t300
  t887 = t885 * t328 * tau0
  t892 = t320 / t321 / t122
  t895 = t297 * r0
  t907 = f.my_piecewise3(t133, 0, t679)
  t910 = t223 * t557 * t337
  t911 = 0.11073470983333333333333333333333333333333333333333e-2 * t910
  t912 = 0.1e1 / t450
  t915 = f.my_piecewise3(t133, 0, -t912 * t679 / 0.3e1)
  t917 = t223 * t37 * t915
  t920 = (-t911 + 0.33220412950000000000000000000000000000000000000000e-2 * t917) * t354
  t921 = t351 ** 2
  t923 = t341 / t921
  t924 = 0.1e1 / t342
  t925 = t910 / 0.3e1
  t926 = -t925 + t917
  t927 = t924 * t926
  t929 = 0.18590165886666666666666666666666666666666666666667e-1 * t910
  t931 = t339 ** 0.5e0
  t932 = t931 * t926
  t935 = t239 * t789 * t347
  t936 = 0.51086165526666666666666666666666666666666666666667e-2 * t935
  t939 = t239 * t243 * t337 * t915
  t942 = 0.1e1 / t353
  t944 = t923 * (0.11807781499500000000000000000000000000000000000000e0 * t927 - t929 + 0.55770497660000000000000000000000000000000000000000e-1 * t917 + 0.19099794277500000000000000000000000000000000000000e-1 * t932 - t936 + 0.15325849658000000000000000000000000000000000000000e-1 * t939) * t942
  t945 = 0.53237641966666666666666666666666666666666666666667e-3 * t910
  t949 = t362 ** 2
  t951 = t357 / t949
  t953 = 0.16057569282500000000000000000000000000000000000000e-1 * t910
  t956 = 0.32394954865000000000000000000000000000000000000000e-2 * t935
  t959 = 0.1e1 / t364
  t962 = 0.31311127083333333333333333333333333333333333333333e-3 * t910
  t965 = (-t962 + 0.93933381250000000000000000000000000000000000000000e-3 * t917) * t376
  t967 = t373 ** 2
  t968 = 0.1e1 / t967
  t969 = t368 * t968
  t971 = 0.10197154565000000000000000000000000000000000000000e-1 * t910
  t974 = 0.27959640330000000000000000000000000000000000000000e-2 * t935
  t976 = 0.87448811650000000000000000000000000000000000000000e-1 * t927 - t971 + 0.30591463695000000000000000000000000000000000000000e-1 * t917 + 0.55743234727500000000000000000000000000000000000000e-2 * t932 - t974 + 0.83878920990000000000000000000000000000000000000000e-2 * t939
  t977 = 0.1e1 / t375
  t985 = t259 * t368
  t994 = f.my_piecewise3(t134, 0, t907 * t383 / 0.2e1 + t334 * (-t920 + t944 + t259 * (-(-t945 + 0.15971292590000000000000000000000000000000000000000e-2 * t917) * t365 + t951 * (0.10974162105750000000000000000000000000000000000000e0 * t927 - t953 + 0.48172707847500000000000000000000000000000000000000e-1 * t917 + 0.19623283938750000000000000000000000000000000000000e-1 * t932 - t956 + 0.97184864595000000000000000000000000000000000000000e-2 * t939) * t959 + t920 - t944 - 0.58482236226346462072622386637590534819724553404281e0 * t965 + 0.58482236226346462072622386637590534819724553404281e0 * t969 * t976 * t977) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t965 - 0.58482236226346462072622386637590534819724553404281e0 * t985 * t968 * t976 * t977) / 0.2e1)
  t996 = t15 * t556
  t999 = 0.11073470983333333333333333333333333333333333333333e-2 * t222 * t996 * t440
  t1000 = t437 ** 2
  t1005 = t16 * t556
  t1006 = 0.1e1 / t429 * t10 * t1005
  t1008 = t222 * t996
  t1010 = t426 ** 0.5e0
  t1012 = t1010 * t10 * t1005
  t1015 = t238 * t14 * t788
  t1020 = t428 / t1000 * (-0.39359271665000000000000000000000000000000000000000e-1 * t1006 - 0.18590165886666666666666666666666666666666666666667e-1 * t1008 - 0.63665980925000000000000000000000000000000000000000e-2 * t1012 - 0.51086165526666666666666666666666666666666666666667e-2 * t1015) / t439
  t1024 = 0.4e1 * t442 * t2 * t446 * t478
  t1029 = 0.4e1 * t443 / t445 / t3 * t478
  t1032 = f.my_piecewise3(t7, 0, 0.4e1 / 0.3e1 * t225 * t528)
  t1035 = f.my_piecewise3(t133, 0, 0.4e1 / 0.3e1 * t335 * t679)
  t1037 = (t1032 + t1035) * t258
  t1043 = t460 ** 2
  t1057 = t471 ** 2
  t1058 = 0.1e1 / t1057
  t1064 = -0.29149603883333333333333333333333333333333333333333e-1 * t1006 - 0.10197154565000000000000000000000000000000000000000e-1 * t1008 - 0.18581078242500000000000000000000000000000000000000e-2 * t1012 - 0.27959640330000000000000000000000000000000000000000e-2 * t1015
  t1065 = 0.1e1 / t473
  t1071 = t447 * t453 * (0.53237641966666666666666666666666666666666666666667e-3 * t222 * t996 * t463 + t455 / t1043 * (-0.36580540352500000000000000000000000000000000000000e-1 * t1006 - 0.16057569282500000000000000000000000000000000000000e-1 * t1008 - 0.65410946462500000000000000000000000000000000000000e-2 * t1012 - 0.32394954865000000000000000000000000000000000000000e-2 * t1015) / t462 - t999 - t1020 + 0.18311447306006545054854346104378990962041954983034e-3 * t222 * t996 * t474 + 0.58482236226346462072622386637590534819724553404281e0 * t466 * t1058 * t1064 * t1065)
  t1078 = 0.18311447306006545054854346104378990962041954983034e-3 * t453 * t10 * t16 * t556 * t474
  t1083 = 0.58482236226346462072622386637590534819724553404281e0 * t453 * t466 * t1058 * t1064 * t1065
  t1084 = t999 + t1020 + t1024 - t1029 + t447 * t1037 * t477 + t1071 + 0.58482236226346462072622386637590534819724553404281e0 * t1037 * t475 - t1078 - t1083 - t850 - t994
  t1086 = tau0 * t101
  t1088 = t115 * t1086 / 0.2e1
  t1090 = 0.10e2 / 0.3e1 * t1086 * t209
  t1091 = -t1088 + t1090
  t1094 = -t1088 - t1090
  t1097 = t495 * t490
  t1101 = t498 * t492
  t1102 = 0.1e1 / t1101
  t1107 = t501 * t490 * t499
  t1108 = t505 * t508
  t1109 = t1108 * t1091
  t1112 = t502 * t1102
  t1113 = t1108 * t1094
  t1116 = t502 * t499
  t1117 = s0 * t634
  t1118 = t1117 * t508
  t1121 = t507 ** 2
  t1123 = t505 / t1121
  t1124 = t1123 * t1117
  t1127 = t512 * t490
  t1128 = t511 * t1127
  t1133 = 0.1e1 / t515 / t1101
  t1138 = t519 * t1127 * t517
  t1141 = t520 * t1133
  t1144 = t520 * t517
  t1149 = t484 * t1091 * t493 - t491 * t499 * t1094 + 0.2e1 * t1097 * t499 * t1091 - 0.2e1 * t497 * t1102 * t1094 + 0.2e1 * t1107 * t1109 - 0.2e1 * t1112 * t1113 - 0.80000000000000000000000000000000000000000000000000e-2 * t1116 * t1118 + 0.80000000000000000000000000000000000000000000000000e-2 * t1116 * t1124 + 0.6e1 * t1128 * t517 * t1091 - 0.6e1 * t514 * t1133 * t1094 + 0.6e1 * t1138 * t1109 - 0.6e1 * t1141 * t1113 - 0.80000000000000000000000000000000000000000000000000e-2 * t1144 * t1118 + 0.80000000000000000000000000000000000000000000000000e-2 * t1144 * t1124
  vrho_0_ = t130 + t220 + t333 + t424 + t525 + t3 * (t661 + t759 + t850 * t332 + t290 * (-0.17066666666666666666666666666666666666666666666667e-1 * t295 * t854 * t305 + 0.34133333333333333333333333333333333333333333333333e-2 * t292 * t294 * s0 / t98 / t297 / t639 * t864 + 0.5e1 / 0.3e1 * t309 * tau0 * t648 + 0.5e1 / 0.3e1 * t310 * t652 + 0.10e2 / 0.3e1 * t873 * t652 + 0.10e2 / 0.3e1 * t314 * t877 * tau0 * t101 + 0.53333333333333333333333333333333333333333333333333e-1 * t884 * t887 + 0.53333333333333333333333333333333333333333333333333e-1 * t892 * t887 - 0.64e-1 * t323 * t324 / t895 * t328 + 0.12800000000000000000000000000000000000000000000000e-1 * t323 * t294 * t854 * t305) + t994 * t423 + t1084 * t524 + t482 * t1149)
  t1153 = -t4 - t527
  t1154 = t1153 / 0.2e1
  t1167 = -t561 * t564 * t565 * t1153 / 0.54e2 - t559 / 0.54e2
  t1168 = f.my_piecewise3(t45, t1167, 0)
  t1186 = f.my_piecewise3(t45, 0, t1167)
  t1205 = f.my_piecewise3(t44, -t554 * t1168 / 0.18e2 + t575 * t1168 / 0.240e3 - t579 * t1168 / 0.4480e4 + t583 * t1168 / 0.103680e6 - t587 * t1168 / 0.2838528e7 + t591 * t1168 / 0.89456640e8 - t595 * t1168 / 0.3185049600e10 + t599 * t1168 / 0.126340300800e12, -0.8e1 / 0.3e1 * t1186 * t88 - 0.8e1 / 0.3e1 * t72 * (-t605 * t1186 + 0.2e1 * t1186 * t85 + 0.2e1 * t72 * (t610 * t1186 * t81 / 0.2e1 - 0.4e1 * t614 * t1186 - t74 * t1186 * t81)))
  t1212 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t1154 * t10 * t18 * t127 - t537 - t541 * t545 * t548 * t1153 / 0.32e2 - 0.3e1 / 0.32e2 * t19 * t26 * t29 * t1205 * t125)
  t1218 = -t1153
  t1227 = -t561 * t690 * t691 * t1218 / 0.54e2 - t687 / 0.54e2
  t1228 = f.my_piecewise3(t146, t1227, 0)
  t1246 = f.my_piecewise3(t146, 0, t1227)
  t1265 = f.my_piecewise3(t145, -t685 * t1228 / 0.18e2 + t701 * t1228 / 0.240e3 - t705 * t1228 / 0.4480e4 + t709 * t1228 / 0.103680e6 - t713 * t1228 / 0.2838528e7 + t717 * t1228 / 0.89456640e8 - t721 * t1228 / 0.3185049600e10 + t725 * t1228 / 0.126340300800e12, -0.8e1 / 0.3e1 * t1246 * t188 - 0.8e1 / 0.3e1 * t173 * (-t731 * t1246 + 0.2e1 * t1246 * t185 + 0.2e1 * t173 * (t736 * t1246 * t181 / 0.2e1 - 0.4e1 * t740 * t1246 - t174 * t1246 * t181)))
  t1271 = t195 * r1
  t1273 = 0.1e1 / t197 / t1271
  t1278 = t390 * t195
  t1281 = t202 ** 2
  t1282 = 0.1e1 / t1281
  t1287 = t199 * t213
  t1291 = t408 * tau1 * t199
  t1300 = f.my_piecewise3(t134, 0, 0.3e1 / 0.32e2 * t1154 * t10 * t18 * t217 - t669 - t671 * t675 * t678 * t1218 / 0.32e2 - 0.3e1 / 0.32e2 * t137 * t26 * t140 * t1265 * t215 - 0.3e1 / 0.32e2 * t137 * t26 * t193 * (-0.10666666666666666666666666666666666666666666666667e-1 * t194 * t1273 * t203 + 0.42666666666666666666666666666666666666666666666668e-4 * t95 * t387 / t196 / t1278 * t1282 + 0.5e1 / 0.3e1 * t109 * tau1 * t1287 + 0.5e1 / 0.3e1 * t211 * t1291))
  t1301 = f.my_piecewise3(t7, 0, t1153)
  t1305 = f.my_piecewise3(t7, 0, -t765 * t1153 / 0.3e1)
  t1307 = t223 * t37 * t1305
  t1310 = (-t764 + 0.33220412950000000000000000000000000000000000000000e-2 * t1307) * t251
  t1311 = -t778 + t1307
  t1312 = t777 * t1311
  t1315 = t784 * t1311
  t1319 = t239 * t243 * t227 * t1305
  t1323 = t776 * (0.11807781499500000000000000000000000000000000000000e0 * t1312 - t782 + 0.55770497660000000000000000000000000000000000000000e-1 * t1307 + 0.19099794277500000000000000000000000000000000000000e-1 * t1315 - t792 + 0.15325849658000000000000000000000000000000000000000e-1 * t1319) * t798
  t1336 = (-t818 + 0.93933381250000000000000000000000000000000000000000e-3 * t1307) * t280
  t1342 = 0.87448811650000000000000000000000000000000000000000e-1 * t1312 - t827 + 0.30591463695000000000000000000000000000000000000000e-1 * t1307 + 0.55743234727500000000000000000000000000000000000000e-2 * t1315 - t830 + 0.83878920990000000000000000000000000000000000000000e-2 * t1319
  t1358 = f.my_piecewise3(t8, 0, t1301 * t287 / 0.2e1 + t221 * (-t1310 + t1323 + t259 * (-(-t801 + 0.15971292590000000000000000000000000000000000000000e-2 * t1307) * t269 + t807 * (0.10974162105750000000000000000000000000000000000000e0 * t1312 - t809 + 0.48172707847500000000000000000000000000000000000000e-1 * t1307 + 0.19623283938750000000000000000000000000000000000000e-1 * t1315 - t812 + 0.97184864595000000000000000000000000000000000000000e-2 * t1319) * t815 + t1310 - t1323 - 0.58482236226346462072622386637590534819724553404281e0 * t1336 + 0.58482236226346462072622386637590534819724553404281e0 * t825 * t1342 * t833) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t1336 - 0.58482236226346462072622386637590534819724553404281e0 * t841 * t824 * t1342 * t833) / 0.2e1)
  t1360 = f.my_piecewise3(t133, 0, t1218)
  t1364 = f.my_piecewise3(t133, 0, -t912 * t1218 / 0.3e1)
  t1366 = t223 * t37 * t1364
  t1369 = (-t911 + 0.33220412950000000000000000000000000000000000000000e-2 * t1366) * t354
  t1370 = -t925 + t1366
  t1371 = t924 * t1370
  t1374 = t931 * t1370
  t1378 = t239 * t243 * t337 * t1364
  t1382 = t923 * (0.11807781499500000000000000000000000000000000000000e0 * t1371 - t929 + 0.55770497660000000000000000000000000000000000000000e-1 * t1366 + 0.19099794277500000000000000000000000000000000000000e-1 * t1374 - t936 + 0.15325849658000000000000000000000000000000000000000e-1 * t1378) * t942
  t1395 = (-t962 + 0.93933381250000000000000000000000000000000000000000e-3 * t1366) * t376
  t1401 = 0.87448811650000000000000000000000000000000000000000e-1 * t1371 - t971 + 0.30591463695000000000000000000000000000000000000000e-1 * t1366 + 0.55743234727500000000000000000000000000000000000000e-2 * t1374 - t974 + 0.83878920990000000000000000000000000000000000000000e-2 * t1378
  t1417 = f.my_piecewise3(t134, 0, t1360 * t383 / 0.2e1 + t334 * (-t1369 + t1382 + t259 * (-(-t945 + 0.15971292590000000000000000000000000000000000000000e-2 * t1366) * t365 + t951 * (0.10974162105750000000000000000000000000000000000000e0 * t1371 - t953 + 0.48172707847500000000000000000000000000000000000000e-1 * t1366 + 0.19623283938750000000000000000000000000000000000000e-1 * t1374 - t956 + 0.97184864595000000000000000000000000000000000000000e-2 * t1378) * t959 + t1369 - t1382 - 0.58482236226346462072622386637590534819724553404281e0 * t1395 + 0.58482236226346462072622386637590534819724553404281e0 * t969 * t1401 * t977) + 0.58482236226346462072622386637590534819724553404281e0 * t259 * t1395 - 0.58482236226346462072622386637590534819724553404281e0 * t985 * t968 * t1401 * t977) / 0.2e1)
  t1421 = 0.1e1 / t197 / t391 / t1271
  t1431 = 0.1e1 / t398 / t396
  t1440 = t312 * t210
  t1444 = 0.1e1 / t407 / t212
  t1451 = t318 * t405 * t210 * t413
  t1452 = t415 * t394
  t1454 = t1452 * t419 * tau1
  t1459 = t411 / t412 / t212
  t1462 = t391 * r1
  t1476 = f.my_piecewise3(t7, 0, 0.4e1 / 0.3e1 * t225 * t1153)
  t1479 = f.my_piecewise3(t133, 0, 0.4e1 / 0.3e1 * t335 * t1218)
  t1481 = (t1476 + t1479) * t258
  t1486 = t999 + t1020 - t1024 - t1029 + t447 * t1481 * t477 + t1071 + 0.58482236226346462072622386637590534819724553404281e0 * t1481 * t475 - t1078 - t1083 - t1358 - t1417
  t1488 = tau1 * t199
  t1490 = t115 * t1488 / 0.2e1
  t1492 = 0.10e2 / 0.3e1 * t119 * t1488
  t1493 = -t1490 + t1492
  t1496 = -t1490 - t1492
  t1505 = t1108 * t1493
  t1508 = t1108 * t1496
  t1511 = s2 * t1273
  t1512 = t1511 * t508
  t1515 = t1123 * t1511
  t1532 = t484 * t1493 * t493 - t491 * t499 * t1496 + 0.2e1 * t1097 * t499 * t1493 - 0.2e1 * t497 * t1102 * t1496 + 0.2e1 * t1107 * t1505 - 0.2e1 * t1112 * t1508 - 0.80000000000000000000000000000000000000000000000000e-2 * t1116 * t1512 + 0.80000000000000000000000000000000000000000000000000e-2 * t1116 * t1515 + 0.6e1 * t1128 * t517 * t1493 - 0.6e1 * t514 * t1133 * t1496 + 0.6e1 * t1138 * t1505 - 0.6e1 * t1141 * t1508 - 0.80000000000000000000000000000000000000000000000000e-2 * t1144 * t1512 + 0.80000000000000000000000000000000000000000000000000e-2 * t1144 * t1515
  vrho_1_ = t130 + t220 + t333 + t424 + t525 + t3 * (t1212 + t1300 + t1358 * t332 + t1417 * t423 + t386 * (-0.17066666666666666666666666666666666666666666666667e-1 * t389 * t1421 * t399 + 0.34133333333333333333333333333333333333333333333333e-2 * t292 * t388 * s2 / t196 / t391 / t1278 * t1431 + 0.5e1 / 0.3e1 * t309 * tau1 * t1287 + 0.5e1 / 0.3e1 * t403 * t1291 + 0.10e2 / 0.3e1 * t1440 * t1291 + 0.10e2 / 0.3e1 * t406 * t1444 * tau1 * t199 + 0.53333333333333333333333333333333333333333333333333e-1 * t1451 * t1454 + 0.53333333333333333333333333333333333333333333333333e-1 * t1459 * t1454 - 0.64e-1 * t414 * t415 / t1462 * t419 + 0.12800000000000000000000000000000000000000000000000e-1 * t414 * t388 * t1421 * t399) + t1486 * t524 + t482 * t1532)
  t1539 = t296 * r0
  t1550 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t19 * t26 * t93 * (0.4e-2 * t95 * t101 * t105 - 0.16e-4 * t96 / t98 / t1539 * t643))
  t1573 = t1123 * t101
  vsigma_0_ = t3 * (t1550 + t290 * (0.64e-2 * t292 * t324 * t306 - 0.128e-2 * t295 / t98 / t297 / t1539 * t864 + 0.24e-1 * t323 * t293 * t325 * t328 - 0.48e-2 * t323 * t885 * t305) + t482 * (0.30000000000000000000000000000000000000000000000000e-2 * t502 * t499 * t101 * t508 - 0.30000000000000000000000000000000000000000000000000e-2 * t1116 * t1573 + 0.30000000000000000000000000000000000000000000000000e-2 * t520 * t517 * t101 * t508 - 0.30000000000000000000000000000000000000000000000000e-2 * t1144 * t1573))
  vsigma_1_ = 0.0e0
  t1588 = t390 * r1
  t1599 = f.my_piecewise3(t134, 0, -0.3e1 / 0.32e2 * t137 * t26 * t193 * (0.4e-2 * t95 * t199 * t203 - 0.16e-4 * t194 / t196 / t1588 * t1282))
  t1622 = t1123 * t199
  vsigma_2_ = t3 * (t1599 + t386 * (0.64e-2 * t292 * t415 * t400 - 0.128e-2 * t389 / t196 / t391 / t1588 * t1431 + 0.24e-1 * t414 * t387 * t416 * t419 - 0.48e-2 * t414 * t1452 * t399) + t482 * (0.30000000000000000000000000000000000000000000000000e-2 * t502 * t499 * t199 * t508 - 0.30000000000000000000000000000000000000000000000000e-2 * t1116 * t1622 + 0.30000000000000000000000000000000000000000000000000e-2 * t520 * t517 * t199 * t508 - 0.30000000000000000000000000000000000000000000000000e-2 * t1144 * t1622))
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t1636 = t316 * t118
  t1643 = f.my_piecewise3(t8, 0, -0.3e1 / 0.32e2 * t19 * t26 * t93 * (-t109 * t118 * t123 - t121 * t1636))
  t1655 = t324 / t99 / t895 * t328
  t1663 = 0.3e1 / 0.10e2 * t115 * t118
  t1666 = 0.2e1 * t118 * tau1 * t208
  t1667 = t1663 - t1666
  t1670 = t1663 + t1666
  t1679 = t1108 * t1667
  t1682 = t1108 * t1670
  vtau_0_ = t3 * (t1643 + t290 * (-t309 * t118 * t123 - t310 * t1636 - 0.2e1 * t873 * t1636 - 0.2e1 * t314 * t877 * t118 - 0.32e-1 * t884 * t1655 - 0.32e-1 * t892 * t1655) + t482 * (0.2e1 * t1097 * t499 * t1667 - 0.2e1 * t497 * t1102 * t1670 + 0.6e1 * t1128 * t517 * t1667 - 0.6e1 * t514 * t1133 * t1670 + t484 * t1667 * t493 - t491 * t499 * t1670 + 0.2e1 * t1107 * t1679 - 0.2e1 * t1112 * t1682 + 0.6e1 * t1138 * t1679 - 0.6e1 * t1141 * t1682))
  t1700 = t408 * t208
  t1707 = f.my_piecewise3(t134, 0, -0.3e1 / 0.32e2 * t137 * t26 * t193 * (-t109 * t208 * t213 - t211 * t1700))
  t1719 = t415 / t197 / t1462 * t419
  t1727 = 0.3e1 / 0.10e2 * t115 * t208
  t1729 = 0.2e1 * t119 * t208
  t1730 = t1727 - t1729
  t1733 = t1727 + t1729
  t1742 = t1108 * t1730
  t1745 = t1108 * t1733
  vtau_1_ = t3 * (t1707 + t386 * (-t309 * t208 * t213 - t403 * t1700 - 0.2e1 * t1440 * t1700 - 0.2e1 * t406 * t1444 * t208 - 0.32e-1 * t1451 * t1719 - 0.32e-1 * t1459 * t1719) + t482 * (0.2e1 * t1097 * t499 * t1730 - 0.2e1 * t497 * t1102 * t1733 + 0.6e1 * t1128 * t517 * t1730 - 0.6e1 * t514 * t1133 * t1733 + t484 * t1730 * t493 - t491 * t499 * t1733 + 0.2e1 * t1107 * t1742 - 0.2e1 * t1112 * t1745 + 0.6e1 * t1138 * t1742 - 0.6e1 * t1141 * t1745))
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

  b97mv_par_n = 6

  b97mv_gamma_x = 0.004

  b97mv_par_x = [None, np.array([np.nan, params_c_x[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_x[2], 0, 1], dtype=np.float64), np.array([np.nan, params_c_x[3], 1, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_ss = 0.2

  b97mv_par_ss = [None, np.array([np.nan, params_c_ss[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_ss[2], 0, 4], dtype=np.float64), np.array([np.nan, params_c_ss[3], 1, 0], dtype=np.float64), np.array([np.nan, params_c_ss[4], 2, 0], dtype=np.float64), np.array([np.nan, params_c_ss[5], 4, 3], dtype=np.float64), np.array([np.nan, 0, 0, 0], dtype=np.float64)]

  b97mv_gamma_os = 0.006

  b97mv_par_os = [None, np.array([np.nan, params_c_os[1], 0, 0], dtype=np.float64), np.array([np.nan, params_c_os[2], 1, 0], dtype=np.float64), np.array([np.nan, params_c_os[3], 2, 0], dtype=np.float64), np.array([np.nan, params_c_os[4], 2, 1], dtype=np.float64), np.array([np.nan, params_c_os[5], 6, 0], dtype=np.float64), np.array([np.nan, params_c_os[6], 6, 1], dtype=np.float64)]

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

  b97mv_wx_ss = lambda t, dummy=None: (K_FACTOR_C - t) / (K_FACTOR_C + t)

  b97mv_wx_os = lambda ts0, ts1: (K_FACTOR_C * (ts0 + ts1) - 2 * ts0 * ts1) / (K_FACTOR_C * (ts0 + ts1) + 2 * ts0 * ts1)

  b97mv_g = lambda mgamma, wx, ux, cc, n, xs, ts0, ts1: jnp.sum(jnp.array([cc[i][1] * wx(ts0, ts1) ** cc[i][2] * ux(mgamma, xs) ** cc[i][3] for i in range(1, n + 1)]), axis=0)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  b97mv_ux_ss = lambda mgamma, x: b97mv_ux(mgamma, x)

  b97mv_ux_os = lambda mgamma, x: b97mv_ux(mgamma, x)

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
  t4 = jnp.logical_or(r0 / 0.2e1 <= f.p.dens_threshold, t3)
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
  t92 = s0 * t86
  t93 = t92 * t90
  t95 = 0.1e1 + 0.4e-2 * t93
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
  t117 = params.c_x[0] + 0.4e-2 * t85 * t91 * t96 + t113 * t115
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
  t191 = params.c_ss[1]
  t192 = s0 ** 2
  t193 = t192 ** 2
  t194 = t191 * t193
  t195 = t87 ** 2
  t196 = t195 ** 2
  t199 = 0.1e1 / t88 / t196 / t87
  t202 = 0.1e1 + 0.2e0 * t93
  t203 = t202 ** 2
  t204 = t203 ** 2
  t205 = 0.1e1 / t204
  t206 = t86 * t199 * t205
  t209 = params.c_ss[2]
  t210 = t209 * t112
  t212 = params.c_ss[3]
  t213 = t112 ** 2
  t214 = t212 * t213
  t215 = t114 ** 2
  t216 = 0.1e1 / t215
  t218 = params.c_ss[4]
  t219 = t213 ** 2
  t220 = t218 * t219
  t221 = t215 ** 2
  t222 = 0.1e1 / t221
  t223 = t220 * t222
  t224 = t192 * s0
  t225 = 0.1e1 / t196
  t228 = 0.1e1 / t203 / t202
  t232 = params.c_ss[0] + 0.64e-2 * t194 * t206 + t210 * t115 + t214 * t216 + 0.32e-1 * t223 * t224 * t225 * t228
  t236 = t8 * t10 * t26
  t238 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t236
  t239 = jnp.sqrt(t236)
  t242 = t236 ** 0.15e1
  t245 = t139 * t9 * t141
  t247 = 0.23615562999000000000000000000000000000000000000000e0 * t239 + 0.55770497660000000000000000000000000000000000000000e-1 * t236 + 0.12733196185000000000000000000000000000000000000000e-1 * t242 + 0.76629248290000000000000000000000000000000000000000e-2 * t245
  t249 = 0.1e1 + 0.1e1 / t247
  t250 = jnp.log(t249)
  t252 = f.my_piecewise3(t3, t16, 1)
  t255 = (0.2e1 * t252 - 0.2e1) * t157
  t257 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t236
  t262 = 0.17489762330000000000000000000000000000000000000000e0 * t239 + 0.30591463695000000000000000000000000000000000000000e-1 * t236 + 0.37162156485000000000000000000000000000000000000000e-2 * t242 + 0.41939460495000000000000000000000000000000000000000e-2 * t245
  t264 = 0.1e1 + 0.1e1 / t262
  t265 = jnp.log(t264)
  t270 = -t238 * t250 + 0.58482236226346462072622386637590534819724553404281e0 * t255 * t257 * t265 - 0.2e1 * t189
  t272 = params.c_os[1]
  t274 = 0.3e1 / 0.5e1 * t106 * t111
  t275 = tau0 ** 2
  t276 = t275 * t11
  t277 = t87 * r0
  t279 = 0.1e1 / t19 / t277
  t281 = 0.4e1 * t276 * t279
  t282 = t274 - t281
  t283 = t272 * t282
  t284 = t274 + t281
  t285 = 0.1e1 / t284
  t287 = params.c_os[2]
  t288 = t282 ** 2
  t289 = t287 * t288
  t290 = t284 ** 2
  t291 = 0.1e1 / t290
  t293 = params.c_os[3]
  t294 = t293 * t288
  t295 = t294 * t291
  t297 = 0.1e1 + 0.6e-2 * t93
  t298 = 0.1e1 / t297
  t300 = t92 * t90 * t298
  t303 = params.c_os[4]
  t304 = t288 ** 2
  t305 = t304 * t288
  t306 = t303 * t305
  t307 = t290 ** 2
  t309 = 0.1e1 / t307 / t290
  t311 = params.c_os[5]
  t312 = t311 * t305
  t313 = t312 * t309
  t316 = params.c_os[0] + t283 * t285 + t289 * t291 + 0.6e-2 * t295 * t300 + t306 * t309 + 0.6e-2 * t313 * t300
  t322 = t37 * t36
  t325 = 0.1e1 / t19 / r0
  t329 = t25 * t5 * t325 * t30 / 0.54e2
  t330 = f.my_piecewise3(t35, -t329, 0)
  t333 = t40 * t36
  t337 = t40 * t322
  t362 = f.my_piecewise3(t35, 0, -t329)
  t385 = f.my_piecewise3(t34, -0.1e1 / t322 * t330 / 0.18e2 + 0.1e1 / t333 * t330 / 0.240e3 - 0.1e1 / t337 * t330 / 0.4480e4 + 0.1e1 / t46 / t36 * t330 / 0.103680e6 - 0.1e1 / t46 / t322 * t330 / 0.2838528e7 + 0.1e1 / t46 / t333 * t330 / 0.89456640e8 - 0.1e1 / t46 / t337 * t330 / 0.3185049600e10 + 0.1e1 / t58 / t36 * t330 / 0.126340300800e12, -0.8e1 / 0.3e1 * t362 * t78 - 0.8e1 / 0.3e1 * t62 * (-t71 * t69 * t362 + 0.2e1 * t362 * t75 + 0.2e1 * t62 * (0.1e1 / t68 / t62 * t362 * t71 / 0.2e1 - 0.4e1 * t62 * t72 * t362 - t64 * t362 * t71)))
  t391 = 0.1e1 / t88 / t277
  t397 = t195 * t87
  t399 = 0.1e1 / t19 / t397
  t401 = t95 ** 2
  t402 = 0.1e1 / t401
  t407 = t91 * t115
  t411 = t108 * t90
  t420 = f.my_piecewise3(t4, 0, -t13 * t18 * t141 * t118 / 0.64e2 - 0.3e1 / 0.64e2 * t13 * t20 * t385 * t117 - 0.3e1 / 0.64e2 * t13 * t20 * t82 * (-0.10666666666666666666666666666666666666666666666667e-1 * t85 * t86 * t391 * t96 + 0.85333333333333333333333333333333333333333333333336e-4 * t84 * t192 * t11 * t399 * t402 + 0.5e1 / 0.3e1 * t100 * tau0 * t407 + 0.5e1 / 0.3e1 * t113 * t216 * t411))
  t422 = t325 * t11
  t426 = 0.11073470983333333333333333333333333333333333333333e-2 * t125 * t422 * t128 * t150
  t427 = t147 ** 2
  t433 = t10 * t325
  t434 = t11 * t128
  t435 = t433 * t434
  t436 = 0.1e1 / t133 * t5 * t7 * t435
  t439 = t125 * t422 * t128
  t441 = t130 ** 0.5e0
  t444 = t441 * t5 * t7 * t435
  t446 = t110 * t86
  t448 = t140 * t446 * t143
  t453 = t132 / t427 * (-0.39359271665000000000000000000000000000000000000000e-1 * t436 - 0.18590165886666666666666666666666666666666666666667e-1 * t439 - 0.63665980925000000000000000000000000000000000000000e-2 * t444 - 0.51086165526666666666666666666666666666666666666667e-2 * t448) / t149
  t458 = t165 ** 2
  t473 = t176 ** 2
  t474 = 0.1e1 / t473
  t480 = -0.29149603883333333333333333333333333333333333333333e-1 * t436 - 0.10197154565000000000000000000000000000000000000000e-1 * t439 - 0.18581078242500000000000000000000000000000000000000e-2 * t444 - 0.27959640330000000000000000000000000000000000000000e-2 * t448
  t481 = 0.1e1 / t178
  t500 = f.my_piecewise3(t4, 0, t124 * (t426 + t453 + t158 * (0.53237641966666666666666666666666666666666666666667e-3 * t125 * t422 * t128 * t168 + t160 / t458 * (-0.36580540352500000000000000000000000000000000000000e-1 * t436 - 0.16057569282500000000000000000000000000000000000000e-1 * t439 - 0.65410946462500000000000000000000000000000000000000e-2 * t444 - 0.32394954865000000000000000000000000000000000000000e-2 * t448) / t167 - t426 - t453 + 0.18311447306006545054854346104378990962041954983034e-3 * t125 * t422 * t128 * t179 + 0.58482236226346462072622386637590534819724553404281e0 * t171 * t474 * t480 * t481) - 0.18311447306006545054854346104378990962041954983034e-3 * t158 * t8 * t433 * t434 * t179 - 0.58482236226346462072622386637590534819724553404281e0 * t158 * t171 * t474 * t480 * t481) / 0.2e1)
  t505 = 0.1e1 / t88 / t196 / t277
  t517 = 0.1e1 / t204 / t202
  t527 = t212 * t112
  t532 = 0.1e1 / t215 / t114
  t537 = t218 * t213 * t112
  t541 = t199 * t228 * t108
  t545 = 0.1e1 / t221 / t114
  t550 = t196 * r0
  t557 = t205 * t86
  t567 = t247 ** 2
  t572 = t7 * t10
  t573 = t572 * t325
  t574 = 0.1e1 / t239 * t5 * t573
  t576 = t8 * t433
  t578 = t236 ** 0.5e0
  t580 = t578 * t5 * t573
  t583 = t139 * t9 * t110
  t595 = t262 ** 2
  t610 = t106 * t411
  t614 = 0.40e2 / 0.3e1 * t276 / t19 / t195
  t615 = -t610 + t614
  t618 = -t610 - t614
  t621 = t287 * t282
  t625 = t290 * t284
  t626 = 0.1e1 / t625
  t632 = t293 * t282 * t291 * s0
  t634 = t91 * t298 * t615
  t638 = t294 * t626 * s0
  t640 = t91 * t298 * t618
  t644 = t92 * t391 * t298
  t648 = t297 ** 2
  t649 = 0.1e1 / t648
  t651 = t192 * t11 * t399 * t649
  t654 = t304 * t282
  t655 = t303 * t654
  t660 = 0.1e1 / t307 / t625
  t666 = t311 * t654 * t309 * s0
  t670 = t312 * t660 * s0
  t677 = t272 * t615 * t285 - t283 * t291 * t618 + 0.2e1 * t621 * t291 * t615 - 0.2e1 * t289 * t626 * t618 + 0.12e-1 * t632 * t634 - 0.12e-1 * t638 * t640 - 0.16000000000000000000000000000000000000000000000000e-1 * t295 * t644 + 0.19200000000000000000000000000000000000000000000000e-3 * t295 * t651 + 0.6e1 * t655 * t309 * t615 - 0.6e1 * t306 * t660 * t618 + 0.36e-1 * t666 * t634 - 0.36e-1 * t670 * t640 - 0.16000000000000000000000000000000000000000000000000e-1 * t313 * t644 + 0.19200000000000000000000000000000000000000000000000e-3 * t313 * t651
  vrho_0_ = 0.2e1 * t122 + 0.2e1 * t189 * t232 + t270 * t316 + r0 * (0.2e1 * t420 + 0.2e1 * t500 * t232 + 0.2e1 * t189 * (-0.68266666666666666666666666666666666666666666666667e-1 * t194 * t86 * t505 * t205 + 0.27306666666666666666666666666666666666666666666668e-1 * t191 * t193 * s0 * t11 / t19 / t196 / t397 * t517 + 0.5e1 / 0.3e1 * t209 * tau0 * t407 + 0.5e1 / 0.3e1 * t210 * t216 * t411 + 0.10e2 / 0.3e1 * t527 * t216 * t411 + 0.10e2 / 0.3e1 * t214 * t532 * t411 + 0.21333333333333333333333333333333333333333333333333e0 * t537 * t222 * t224 * t541 + 0.21333333333333333333333333333333333333333333333333e0 * t220 * t545 * t224 * t541 - 0.256e0 * t223 * t224 / t550 * t228 + 0.51200000000000000000000000000000000000000000000000e-1 * t223 * t193 * t505 * t557) + (0.11073470983333333333333333333333333333333333333333e-2 * t8 * t433 * t250 + t238 / t567 * (-0.39359271665000000000000000000000000000000000000000e-1 * t574 - 0.18590165886666666666666666666666666666666666666667e-1 * t576 - 0.63665980925000000000000000000000000000000000000000e-2 * t580 - 0.51086165526666666666666666666666666666666666666667e-2 * t583) / t249 - 0.18311447306006545054854346104378990962041954983034e-3 * t255 * t5 * t572 * t325 * t265 - 0.58482236226346462072622386637590534819724553404281e0 * t255 * t257 / t595 * (-0.29149603883333333333333333333333333333333333333333e-1 * t574 - 0.10197154565000000000000000000000000000000000000000e-1 * t576 - 0.18581078242500000000000000000000000000000000000000e-2 * t580 - 0.27959640330000000000000000000000000000000000000000e-2 * t583) / t264 - 0.2e1 * t500) * t316 + t270 * t677)
  t685 = t195 * r0
  t687 = 0.1e1 / t19 / t685
  t697 = f.my_piecewise3(t4, 0, -0.3e1 / 0.64e2 * t13 * t20 * t82 * (0.4e-2 * t84 * t86 * t90 * t96 - 0.32e-4 * t85 * t11 * t687 * t402))
  t720 = t91 * t298
  t725 = s0 * t11 * t687 * t649
  vsigma_0_ = r0 * (0.2e1 * t697 + 0.2e1 * t189 * (0.256e-1 * t191 * t224 * t206 - 0.1024e-1 * t194 * t11 / t19 / t196 / t685 * t517 + 0.96e-1 * t223 * t192 * t225 * t228 - 0.192e-1 * t223 * t224 * t199 * t557) + t270 * (0.6e-2 * t295 * t720 - 0.72e-4 * t295 * t725 + 0.6e-2 * t313 * t720 - 0.72e-4 * t313 * t725))
  vlapl_0_ = 0.0e0
  t736 = t110 * t115
  t739 = t216 * t86 * t110
  t746 = f.my_piecewise3(t4, 0, -0.3e1 / 0.64e2 * t13 * t20 * t82 * (-t100 * t86 * t736 - t113 * t739))
  t762 = t224 / t88 / t550 * t228 * t86
  t772 = 0.3e1 / 0.5e1 * t106 * t446
  t775 = 0.8e1 * tau0 * t11 * t279
  t776 = t772 - t775
  t779 = t772 + t775
  t789 = t91 * t298 * t776
  t793 = t91 * t298 * t779
  vtau_0_ = r0 * (0.2e1 * t746 + 0.2e1 * t189 * (-t209 * t86 * t736 - t210 * t739 - 0.2e1 * t527 * t739 - 0.2e1 * t214 * t532 * t86 * t110 - 0.128e0 * t537 * t222 * t762 - 0.128e0 * t220 * t545 * t762) + t270 * (t272 * t776 * t285 - t283 * t291 * t779 + 0.2e1 * t621 * t291 * t776 - 0.2e1 * t289 * t626 * t779 + 0.12e-1 * t632 * t789 - 0.12e-1 * t638 * t793 + 0.6e1 * t655 * t309 * t776 - 0.6e1 * t306 * t660 * t779 + 0.36e-1 * t666 * t789 - 0.36e-1 * t670 * t793))
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
  t4 = jnp.logical_or(r0 / 0.2e1 <= f.p.dens_threshold, t3)
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
  t93 = s0 * t88
  t94 = t93 * t91
  t96 = 0.1e1 + 0.4e-2 * t94
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
  t118 = params.c_x[0] + 0.4e-2 * t87 * t92 * t97 + t114 * t116
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
  t204 = 0.1e1 / t19 / t202
  t205 = t11 * t204
  t206 = t96 ** 2
  t207 = 0.1e1 / t206
  t211 = t101 * tau0
  t212 = t92 * t116
  t215 = t115 ** 2
  t216 = 0.1e1 / t215
  t217 = t114 * t216
  t218 = t109 * t91
  t221 = -0.10666666666666666666666666666666666666666666666667e-1 * t87 * t195 * t97 + 0.85333333333333333333333333333333333333333333333336e-4 * t200 * t205 * t207 + 0.5e1 / 0.3e1 * t211 * t212 + 0.5e1 / 0.3e1 * t217 * t218
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
  t367 = params.c_ss[1]
  t368 = t199 ** 2
  t369 = t367 * t368
  t370 = t201 ** 2
  t371 = t370 * t89
  t373 = 0.1e1 / t20 / t371
  t376 = 0.1e1 + 0.2e0 * t94
  t377 = t376 ** 2
  t378 = t377 ** 2
  t379 = 0.1e1 / t378
  t383 = params.c_ss[2]
  t384 = t383 * t113
  t386 = params.c_ss[3]
  t387 = t113 ** 2
  t388 = t386 * t387
  t390 = params.c_ss[4]
  t391 = t387 ** 2
  t392 = t390 * t391
  t393 = t215 ** 2
  t394 = 0.1e1 / t393
  t395 = t392 * t394
  t396 = t199 * s0
  t400 = 0.1e1 / t377 / t376
  t404 = params.c_ss[0] + 0.64e-2 * t369 * t88 * t373 * t379 + t384 * t116 + t388 * t216 + 0.32e-1 * t395 * t396 / t370 * t400
  t408 = 0.621814e-1 * t260 * t254
  t411 = t337 * t331
  t420 = f.my_piecewise3(t4, 0, t229 * (-t408 + t295 * (-0.3109070e-1 * t310 * t304 + t408 - 0.19751673498613801407483339618206552048944131217655e-1 * t411) + 0.19751673498613801407483339618206552048944131217655e-1 * t295 * t411) / 0.2e1)
  t423 = 0.1e1 / t20 / t370 / t192
  t428 = t368 * s0
  t429 = t367 * t428
  t432 = 0.1e1 / t19 / t370 / t202
  t435 = 0.1e1 / t378 / t376
  t439 = t383 * tau0
  t442 = t384 * t216
  t445 = t386 * t113
  t446 = t445 * t216
  t450 = 0.1e1 / t215 / t115
  t451 = t388 * t450
  t455 = t390 * t387 * t113
  t456 = t394 * t396
  t457 = t455 * t456
  t459 = t373 * t400 * t109
  t463 = 0.1e1 / t393 / t115
  t464 = t463 * t396
  t465 = t392 * t464
  t475 = t379 * t88
  t479 = -0.68266666666666666666666666666666666666666666666667e-1 * t369 * t88 * t423 * t379 + 0.27306666666666666666666666666666666666666666666668e-1 * t429 * t11 * t432 * t435 + 0.5e1 / 0.3e1 * t439 * t212 + 0.5e1 / 0.3e1 * t442 * t218 + 0.10e2 / 0.3e1 * t446 * t218 + 0.10e2 / 0.3e1 * t451 * t218 + 0.21333333333333333333333333333333333333333333333333e0 * t457 * t459 + 0.21333333333333333333333333333333333333333333333333e0 * t465 * t459 - 0.256e0 * t395 * t396 / t370 / r0 * t400 + 0.51200000000000000000000000000000000000000000000000e-1 * t395 * t368 * t423 * t475
  t483 = t8 * t10 * t28
  t484 = jnp.sqrt(t483)
  t487 = t483 ** 0.15e1
  t490 = t243 * t9 * t21
  t492 = 0.37978500000000000000000000000000000000000000000000e1 * t484 + 0.89690000000000000000000000000000000000000000000000e0 * t483 + 0.20477500000000000000000000000000000000000000000000e0 * t487 + 0.12323500000000000000000000000000000000000000000000e0 * t490
  t495 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t492
  t496 = jnp.log(t495)
  t501 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t483
  t502 = t492 ** 2
  t503 = 0.1e1 / t502
  t504 = t501 * t503
  t506 = 0.1e1 / t484 * t5
  t507 = t7 * t10
  t508 = t507 * t127
  t509 = t506 * t508
  t511 = t8 * t267
  t513 = t483 ** 0.5e0
  t514 = t513 * t5
  t515 = t514 * t508
  t518 = t243 * t9 * t111
  t520 = -0.63297500000000000000000000000000000000000000000000e0 * t509 - 0.29896666666666666666666666666666666666666666666667e0 * t511 - 0.10238750000000000000000000000000000000000000000000e0 * t515 - 0.82156666666666666666666666666666666666666666666667e-1 * t518
  t521 = 0.1e1 / t495
  t522 = t520 * t521
  t525 = f.my_piecewise3(t3, t16, 1)
  t528 = (0.2e1 * t525 - 0.2e1) * t294
  t529 = t528 * t5
  t534 = 0.51785000000000000000000000000000000000000000000000e1 * t484 + 0.90577500000000000000000000000000000000000000000000e0 * t483 + 0.11003250000000000000000000000000000000000000000000e0 * t487 + 0.12417750000000000000000000000000000000000000000000e0 * t490
  t537 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t534
  t538 = jnp.log(t537)
  t544 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t483
  t545 = t528 * t544
  t546 = t534 ** 2
  t547 = 0.1e1 / t546
  t552 = -0.86308333333333333333333333333333333333333333333334e0 * t509 - 0.30192500000000000000000000000000000000000000000000e0 * t511 - 0.55016250000000000000000000000000000000000000000000e-1 * t515 - 0.82785000000000000000000000000000000000000000000000e-1 * t518
  t554 = 0.1e1 / t537
  t555 = t547 * t552 * t554
  t559 = 0.11073470983333333333333333333333333333333333333333e-2 * t8 * t267 * t496 + 0.10000000000000000000000000000000000000000000000000e1 * t504 * t522 - 0.18311447306006545054854346104378990962041954983034e-3 * t529 * t507 * t127 * t538 - 0.58482236226346462072622386637590534819724553404280e0 * t545 * t555 - 0.2e1 * t365
  t561 = params.c_os[1]
  t563 = 0.3e1 / 0.5e1 * t107 * t112
  t564 = tau0 ** 2
  t565 = t564 * t11
  t569 = 0.4e1 * t565 / t19 / t192
  t570 = t563 - t569
  t571 = t561 * t570
  t572 = t563 + t569
  t573 = 0.1e1 / t572
  t575 = params.c_os[2]
  t576 = t570 ** 2
  t577 = t575 * t576
  t578 = t572 ** 2
  t579 = 0.1e1 / t578
  t581 = params.c_os[3]
  t582 = t581 * t576
  t583 = t582 * t579
  t585 = 0.1e1 + 0.6e-2 * t94
  t586 = 0.1e1 / t585
  t588 = t93 * t91 * t586
  t591 = params.c_os[4]
  t592 = t576 ** 2
  t593 = t592 * t576
  t594 = t591 * t593
  t595 = t578 ** 2
  t597 = 0.1e1 / t595 / t578
  t599 = params.c_os[5]
  t600 = t599 * t593
  t601 = t600 * t597
  t604 = params.c_os[0] + t571 * t573 + t577 * t579 + 0.6e-2 * t583 * t588 + t594 * t597 + 0.6e-2 * t601 * t588
  t613 = -0.621814e-1 * t501 * t496 + 0.19751673498613801407483339618206552048944131217655e-1 * t528 * t544 * t538 - 0.2e1 * t420
  t614 = t107 * t218
  t618 = 0.40e2 / 0.3e1 * t565 / t19 / t201
  t619 = -t614 + t618
  t620 = t561 * t619
  t622 = -t614 - t618
  t623 = t579 * t622
  t625 = t575 * t570
  t629 = t578 * t572
  t630 = 0.1e1 / t629
  t634 = t581 * t570
  t636 = t634 * t579 * s0
  t637 = t586 * t619
  t638 = t92 * t637
  t641 = t630 * s0
  t642 = t582 * t641
  t643 = t586 * t622
  t644 = t92 * t643
  t648 = t93 * t194 * t586
  t651 = t199 * t11
  t652 = t585 ** 2
  t653 = 0.1e1 / t652
  t655 = t651 * t204 * t653
  t658 = t592 * t570
  t659 = t591 * t658
  t664 = 0.1e1 / t595 / t629
  t668 = t599 * t658
  t669 = t597 * s0
  t670 = t668 * t669
  t673 = t664 * s0
  t674 = t600 * t673
  t681 = t620 * t573 - t571 * t623 + 0.2e1 * t625 * t579 * t619 - 0.2e1 * t577 * t630 * t622 + 0.12e-1 * t636 * t638 - 0.12e-1 * t642 * t644 - 0.16000000000000000000000000000000000000000000000000e-1 * t583 * t648 + 0.19200000000000000000000000000000000000000000000000e-3 * t583 * t655 + 0.6e1 * t659 * t597 * t619 - 0.6e1 * t594 * t664 * t622 + 0.36e-1 * t670 * t638 - 0.36e-1 * t674 * t644 - 0.16000000000000000000000000000000000000000000000000e-1 * t601 * t648 + 0.19200000000000000000000000000000000000000000000000e-3 * t601 * t655
  t694 = t132 ** 2
  t698 = 0.1e1 / t19 / t89
  t702 = 0.2e1 / 0.81e2 * t27 * t5 * t698 * t32
  t703 = f.my_piecewise3(t37, t702, 0)
  t736 = t43 * t694 / 0.6e1 - t125 * t703 / 0.18e2 - t46 * t694 / 0.48e2 + t136 * t703 / 0.240e3 + t49 * t694 / 0.640e3 - t140 * t703 / 0.4480e4 - t52 * t694 / 0.11520e5 + t144 * t703 / 0.103680e6 + t55 * t694 / 0.258048e6 - t148 * t703 / 0.2838528e7 - t58 * t694 / 0.6881280e7 + t152 * t703 / 0.89456640e8 + t61 * t694 / 0.212336640e9 - t156 * t703 / 0.3185049600e10 - 0.1e1 / t60 / t39 * t694 / 0.7431782400e10 + t160 * t703 / 0.126340300800e12
  t737 = f.my_piecewise3(t37, 0, t702)
  t742 = t70 ** 2
  t745 = t164 ** 2
  t784 = f.my_piecewise3(t36, t736, -0.8e1 / 0.3e1 * t737 * t80 - 0.16e2 / 0.3e1 * t164 * t183 - 0.8e1 / 0.3e1 * t64 * (-0.1e1 / t742 / t64 * t745 * t73 / 0.2e1 + 0.2e1 * t73 * t171 * t745 - t166 * t737 + 0.2e1 * t737 * t77 + 0.4e1 * t164 * t180 + 0.2e1 * t64 * (-0.2e1 / t742 * t745 * t73 + t171 * t737 * t73 / 0.2e1 + 0.1e1 / t742 / t70 * t745 * t73 / 0.4e1 - 0.4e1 * t745 * t74 - t71 * t745 * t73 - 0.4e1 * t175 * t737 - t66 * t737 * t73)))
  t794 = 0.1e1 / t20 / t201
  t799 = t201 * t192
  t801 = 0.1e1 / t19 / t799
  t807 = 0.1e1 / t371
  t813 = t195 * t116
  t817 = t201 * r0
  t819 = 0.1e1 / t19 / t817
  t821 = t11 * t819 * t216
  t825 = t565 * t819
  t828 = t109 * t194
  t837 = f.my_piecewise3(t4, 0, t13 * t18 * t111 * t119 / 0.96e2 - t13 * t22 * t188 / 0.32e2 - t13 * t22 * t222 / 0.32e2 - 0.3e1 / 0.64e2 * t13 * t123 * t784 * t118 - 0.3e1 / 0.32e2 * t13 * t123 * t187 * t221 - 0.3e1 / 0.64e2 * t13 * t123 * t84 * (0.39111111111111111111111111111111111111111111111112e-1 * t87 * t88 * t794 * t97 - 0.76800000000000000000000000000000000000000000000003e-3 * t200 * t11 * t801 * t207 + 0.36408888888888888888888888888888888888888888888891e-5 * t86 * t396 * t807 / t206 / t96 - 0.40e2 / 0.9e1 * t211 * t813 + 0.100e3 / 0.9e1 * t101 * t564 * t821 + 0.100e3 / 0.9e1 * t114 * t450 * t825 - 0.40e2 / 0.9e1 * t217 * t828))
  t839 = t698 * t11
  t842 = 0.14764627977777777777777777777777777777777777777777e-2 * t230 * t839 * t255
  t847 = 0.35616666666666666666666666666666666666666666666666e-1 * t511 * t268 * t262 * t284 * t285
  t851 = t284 ** 2
  t854 = 0.20000000000000000000000000000000000000000000000000e1 * t260 / t261 / t250 * t851 * t285
  t859 = t9 * t91
  t861 = t859 * t88 * t246
  t862 = 0.1e1 / t237 / t236 * t242 * t25 * t861
  t864 = t10 * t698
  t865 = t864 * t268
  t866 = t266 * t865
  t869 = t230 * t839 * t233
  t871 = t236 ** (-0.5e0)
  t874 = t871 * t242 * t25 * t861
  t876 = t277 * t865
  t879 = t244 * t92 * t246
  t884 = 0.10000000000000000000000000000000000000000000000000e1 * t263 * (-0.42198333333333333333333333333333333333333333333333e0 * t862 + 0.84396666666666666666666666666666666666666666666666e0 * t866 + 0.39862222222222222222222222222222222222222222222223e0 * t869 + 0.68258333333333333333333333333333333333333333333333e-1 * t874 + 0.13651666666666666666666666666666666666666666666667e0 * t876 + 0.13692777777777777777777777777777777777777777777778e0 * t879) * t285
  t885 = t261 ** 2
  t888 = t253 ** 2
  t892 = 0.16081979498692535066756296899072713062105388428051e2 * t260 / t885 * t851 / t888
  t904 = t318 ** 2
  t918 = t311 ** 2
  t921 = t303 ** 2
  t933 = 0.1e1 / t338 / t327
  t935 = t345 ** 2
  t945 = -0.57538888888888888888888888888888888888888888888889e0 * t862 + 0.11507777777777777777777777777777777777777777777778e1 * t866 + 0.40256666666666666666666666666666666666666666666667e0 * t869 + 0.36677500000000000000000000000000000000000000000000e-1 * t874 + 0.73355000000000000000000000000000000000000000000000e-1 * t876 + 0.13797500000000000000000000000000000000000000000000e0 * t879
  t949 = t338 ** 2
  t950 = 0.1e1 / t949
  t952 = t330 ** 2
  t953 = 0.1e1 / t952
  t957 = -0.70983522622222222222222222222222222222222222222221e-3 * t230 * t839 * t305 - 0.34246666666666666666666666666666666666666666666666e-1 * t511 * t268 * t312 * t318 * t319 - 0.20000000000000000000000000000000000000000000000000e1 * t310 / t311 / t300 * t904 * t319 + 0.10000000000000000000000000000000000000000000000000e1 * t313 * (-0.78438333333333333333333333333333333333333333333333e0 * t862 + 0.15687666666666666666666666666666666666666666666667e1 * t866 + 0.68863333333333333333333333333333333333333333333333e0 * t869 + 0.14025833333333333333333333333333333333333333333333e0 * t874 + 0.28051666666666666666666666666666666666666666666667e0 * t876 + 0.17365833333333333333333333333333333333333333333333e0 * t879) * t319 + 0.32163958997385070133512593798145426124210776856102e2 * t310 / t918 * t904 / t921 + t842 + t847 + t854 - t884 - t892 - 0.24415263074675393406472461472505321282722606644045e-3 * t230 * t839 * t332 - 0.10843581300301739842632067522386578331157260943710e-1 * t511 * t268 * t359 - 0.11696447245269292414524477327518106963944910680856e1 * t337 * t933 * t935 * t346 + 0.58482236226346462072622386637590534819724553404280e0 * t340 * t945 * t346 + 0.17315859105681463759666483083807725165579399831905e2 * t337 * t950 * t935 * t953
  t978 = -t842 - t847 - t854 + t884 + t892 + t295 * t957 + 0.24415263074675393406472461472505321282722606644045e-3 * t352 * t864 * t353 + 0.10843581300301739842632067522386578331157260943710e-1 * t295 * t230 * t272 * t359 + 0.11696447245269292414524477327518106963944910680856e1 * t357 * t933 * t935 * t346 - 0.58482236226346462072622386637590534819724553404280e0 * t357 * t339 * t945 * t346 - 0.17315859105681463759666483083807725165579399831905e2 * t357 * t950 * t935 * t953
  t981 = f.my_piecewise3(t4, 0, t229 * t978 / 0.2e1)
  t992 = 0.1e1 / t19 / t370 / t817 * t400 * t565
  t1002 = t432 * t379 * tau0 * t11
  t1017 = 0.1e1 / t20 / t370 / t201
  t1035 = 0.21333333333333333333333333333333333333333333333333e1 * t390 * t387 * t456 * t992 + 0.56888888888888888888888888888888888888888888888888e1 * t455 * t464 * t992 + 0.13653333333333333333333333333333333333333333333333e1 * t455 * t394 * t368 * t1002 + 0.35555555555555555555555555555555555555555555555555e1 * t392 / t393 / t215 * t396 * t992 + 0.13653333333333333333333333333333333333333333333333e1 * t392 * t463 * t368 * t1002 + 0.79644444444444444444444444444444444444444444444445e0 * t369 * t88 * t1017 * t379 - 0.40e2 / 0.9e1 * t439 * t813 + 0.100e3 / 0.9e1 * t384 * t450 * t825 + 0.400e3 / 0.9e1 * t445 * t450 * t825 + 0.100e3 / 0.3e1 * t388 * t394 * t825 - 0.40e2 / 0.9e1 * t442 * t828
  t1040 = t396 * t807
  t1050 = 0.1e1 / t19 / t370 / t799
  t1068 = t370 ** 2
  t1077 = t423 * t400 * t109
  t1082 = -0.80e2 / 0.9e1 * t446 * t828 - 0.80e2 / 0.9e1 * t451 * t828 + 0.2304e1 * t395 * t1040 * t400 - 0.10069333333333333333333333333333333333333333333333e1 * t395 * t368 * t1017 * t475 + 0.21845333333333333333333333333333333333333333333334e0 * t395 * t428 * t1050 * t435 * t11 + 0.100e3 / 0.9e1 * t383 * t564 * t821 + 0.100e3 / 0.9e1 * t386 * t564 * t821 - 0.68266666666666666666666666666666666666666666666669e0 * t429 * t11 * t1050 * t435 + 0.14563555555555555555555555555555555555555555555557e0 * t367 * t368 * t199 / t1068 / t89 / t378 / t377 - 0.39822222222222222222222222222222222222222222222222e1 * t465 * t1077 - 0.39822222222222222222222222222222222222222222222222e1 * t457 * t1077
  t1096 = t520 ** 2
  t1104 = t25 * t9 * t91
  t1105 = 0.1e1 / t484 / t483 * t242 * t1104
  t1107 = t507 * t698
  t1108 = t506 * t1107
  t1110 = t8 * t864
  t1112 = t483 ** (-0.5e0)
  t1114 = t1112 * t242 * t1104
  t1116 = t514 * t1107
  t1118 = t243 * t859
  t1124 = t502 ** 2
  t1127 = t495 ** 2
  t1142 = t552 ** 2
  t1158 = t546 ** 2
  t1161 = t537 ** 2
  t1167 = -0.14764627977777777777777777777777777777777777777777e-2 * t8 * t864 * t496 - 0.35616666666666666666666666666666666666666666666666e-1 * t230 * t127 * t503 * t522 - 0.20000000000000000000000000000000000000000000000000e1 * t501 / t502 / t492 * t1096 * t521 + 0.10000000000000000000000000000000000000000000000000e1 * t504 * (-0.42198333333333333333333333333333333333333333333333e0 * t1105 + 0.84396666666666666666666666666666666666666666666666e0 * t1108 + 0.39862222222222222222222222222222222222222222222223e0 * t1110 + 0.68258333333333333333333333333333333333333333333333e-1 * t1114 + 0.13651666666666666666666666666666666666666666666667e0 * t1116 + 0.13692777777777777777777777777777777777777777777778e0 * t1118) * t521 + 0.16081979498692535066756296899072713062105388428051e2 * t501 / t1124 * t1096 / t1127 + 0.24415263074675393406472461472505321282722606644045e-3 * t529 * t507 * t698 * t538 + 0.10843581300301739842632067522386578331157260943710e-1 * t528 * t8 * t267 * t555 + 0.11696447245269292414524477327518106963944910680856e1 * t545 / t546 / t534 * t1142 * t554 - 0.58482236226346462072622386637590534819724553404280e0 * t545 * t547 * (-0.57538888888888888888888888888888888888888888888889e0 * t1105 + 0.11507777777777777777777777777777777777777777777778e1 * t1108 + 0.40256666666666666666666666666666666666666666666667e0 * t1110 + 0.36677500000000000000000000000000000000000000000000e-1 * t1114 + 0.73355000000000000000000000000000000000000000000000e-1 * t1116 + 0.13797500000000000000000000000000000000000000000000e0 * t1118) * t554 - 0.17315859105681463759666483083807725165579399831905e2 * t545 / t1158 * t1142 / t1161 - 0.2e1 * t981
  t1180 = 0.8e1 / 0.3e1 * t107 * t828
  t1181 = 0.520e3 / 0.9e1 * t825
  t1182 = t1180 + t1181
  t1186 = t595 ** 2
  t1187 = 0.1e1 / t1186
  t1188 = t622 ** 2
  t1195 = 0.1e1 / t595
  t1200 = t619 ** 2
  t1208 = t1180 - t1181
  t1220 = t1040 / t652 / t585
  t1227 = t92 * t637 * t622
  t1233 = t195 * t643
  t1236 = t195 * t637
  t1242 = t92 * t586 * t1188
  t1245 = -0.72e2 * t659 * t664 * t619 * t622 - 0.8e1 * t625 * t630 * t619 * t622 - 0.6e1 * t594 * t664 * t1182 + 0.42e2 * t594 * t1187 * t1188 + 0.2e1 * t571 * t630 * t1188 + 0.6e1 * t577 * t1195 * t1188 + 0.30e2 * t591 * t592 * t597 * t1200 - 0.2e1 * t620 * t623 - t571 * t579 * t1182 + 0.2e1 * t625 * t579 * t1208 - 0.2e1 * t577 * t630 * t1182 + 0.6e1 * t659 * t597 * t1208 + 0.12288000000000000000000000000000000000000000000000e-4 * t583 * t1220 + 0.12288000000000000000000000000000000000000000000000e-4 * t601 * t1220 - 0.432e0 * t668 * t673 * t1227 - 0.48e-1 * t634 * t641 * t1227 + 0.19200000000000000000000000000000000000000000000000e0 * t674 * t1233 - 0.64000000000000000000000000000000000000000000000000e-1 * t636 * t1236 + 0.36e-1 * t582 * t1195 * s0 * t1242
  t1247 = t92 * t586 * t1208
  t1253 = t205 * t653 * t619
  t1257 = t92 * t586 * t1182
  t1263 = t205 * t653 * t622
  t1298 = t93 * t794 * t586
  t1308 = t651 * t801 * t653
  t1313 = 0.36e-1 * t670 * t1247 + 0.23040000000000000000000000000000000000000000000000e-2 * t668 * t597 * t199 * t1253 - 0.36e-1 * t674 * t1257 - 0.23040000000000000000000000000000000000000000000000e-2 * t600 * t664 * t199 * t1263 + 0.12e-1 * t636 * t1247 + 0.76800000000000000000000000000000000000000000000000e-3 * t634 * t579 * t199 * t1253 - 0.12e-1 * t642 * t1257 - 0.76800000000000000000000000000000000000000000000000e-3 * t582 * t630 * t199 * t1263 + 0.64000000000000000000000000000000000000000000000000e-1 * t642 * t1233 + 0.180e0 * t599 * t592 * t669 * t92 * t586 * t1200 - 0.19200000000000000000000000000000000000000000000000e0 * t670 * t1236 + 0.252e0 * t600 * t1187 * s0 * t1242 + t561 * t1208 * t573 + 0.2e1 * t575 * t1200 * t579 + 0.58666666666666666666666666666666666666666666666667e-1 * t601 * t1298 + 0.12e-1 * t581 * t1200 * t579 * t588 + 0.58666666666666666666666666666666666666666666666667e-1 * t583 * t1298 - 0.17280000000000000000000000000000000000000000000000e-2 * t601 * t1308 - 0.17280000000000000000000000000000000000000000000000e-2 * t583 * t1308
  v2rho2_0_ = 0.4e1 * t227 + 0.4e1 * t365 * t404 + 0.4e1 * t420 * t479 + 0.2e1 * t559 * t604 + 0.2e1 * t613 * t681 + r0 * (0.2e1 * t837 + 0.2e1 * t981 * t404 + 0.4e1 * t365 * t479 + 0.2e1 * t420 * (t1035 + t1082) + t1167 * t604 + 0.2e1 * t559 * t681 + t613 * (t1245 + t1313))

  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = jnp.logical_or(r0 / 0.2e1 <= f.p.dens_threshold, t3)
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
  t94 = s0 * t89
  t95 = t94 * t92
  t97 = 0.1e1 + 0.4e-2 * t95
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
  t117 = params.c_x[0] + 0.4e-2 * t88 * t93 * t98 + t113 * t115
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
  t221 = -0.10666666666666666666666666666666666666666666666667e-1 * t88 * t195 * t98 + 0.85333333333333333333333333333333333333333333333336e-4 * t200 * t205 * t207 + 0.5e1 / 0.3e1 * t211 * t212 + 0.5e1 / 0.3e1 * t217 * t218
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
  t334 = 0.1e1 / t19 / t332
  t335 = t11 * t334
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
  t371 = 0.39111111111111111111111111111111111111111111111112e-1 * t88 * t328 * t98 - 0.76800000000000000000000000000000000000000000000003e-3 * t200 * t335 * t207 + 0.36408888888888888888888888888888888888888888888891e-5 * t340 * t343 * t345 - 0.40e2 / 0.9e1 * t211 * t349 + 0.100e3 / 0.9e1 * t353 * t358 + 0.100e3 / 0.9e1 * t363 * t365 - 0.40e2 / 0.9e1 * t217 * t368
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
  t632 = params.c_ss[1]
  t633 = t199 ** 2
  t634 = t632 * t633
  t636 = 0.1e1 / t20 / t342
  t639 = 0.1e1 + 0.2e0 * t95
  t640 = t639 ** 2
  t641 = t640 ** 2
  t642 = 0.1e1 / t641
  t646 = params.c_ss[2]
  t647 = t646 * t112
  t649 = params.c_ss[3]
  t650 = t112 ** 2
  t651 = t649 * t650
  t653 = params.c_ss[4]
  t654 = t650 ** 2
  t655 = t653 * t654
  t656 = t215 ** 2
  t657 = 0.1e1 / t656
  t658 = t655 * t657
  t659 = 0.1e1 / t341
  t661 = t640 * t639
  t662 = 0.1e1 / t661
  t666 = params.c_ss[0] + 0.64e-2 * t634 * t89 * t636 * t642 + t647 * t115 + t651 * t216 + 0.32e-1 * t658 * t339 * t659 * t662
  t671 = 0.11073470983333333333333333333333333333333333333333e-2 * t380 * t420 * t405
  t672 = t433 * t435
  t674 = 0.10000000000000000000000000000000000000000000000000e1 * t449 * t672
  t678 = t514 * t516
  t684 = t568 * t570
  t697 = f.my_piecewise3(t4, 0, t379 * (t671 + t674 + t494 * (0.53237641966666666666666666666666666666666666666666e-3 * t380 * t420 * t504 + 0.10000000000000000000000000000000000000000000000000e1 * t530 * t678 - t671 - t674 + 0.18311447306006545054854346104378990962041954983034e-3 * t380 * t420 * t558 + 0.58482236226346462072622386637590534819724553404280e0 * t584 * t684) - 0.18311447306006545054854346104378990962041954983034e-3 * t605 * t409 * t606 - 0.58482236226346462072622386637590534819724553404280e0 * t614 * t571) / 0.2e1)
  t698 = t341 * t192
  t700 = 0.1e1 / t20 / t698
  t705 = t633 * s0
  t706 = t632 * t705
  t709 = 0.1e1 / t19 / t341 / t202
  t712 = 0.1e1 / t641 / t639
  t716 = t646 * tau0
  t719 = t647 * t216
  t722 = t649 * t112
  t723 = t722 * t216
  t726 = t651 * t362
  t730 = t653 * t650 * t112
  t731 = t657 * t339
  t732 = t730 * t731
  t734 = t636 * t662 * t110
  t738 = 0.1e1 / t656 / t114
  t739 = t738 * t339
  t740 = t655 * t739
  t750 = t642 * t89
  t754 = -0.68266666666666666666666666666666666666666666666667e-1 * t634 * t89 * t700 * t642 + 0.27306666666666666666666666666666666666666666666668e-1 * t706 * t11 * t709 * t712 + 0.5e1 / 0.3e1 * t716 * t212 + 0.5e1 / 0.3e1 * t719 * t218 + 0.10e2 / 0.3e1 * t723 * t218 + 0.10e2 / 0.3e1 * t726 * t218 + 0.21333333333333333333333333333333333333333333333333e0 * t732 * t734 + 0.21333333333333333333333333333333333333333333333333e0 * t740 * t734 - 0.256e0 * t658 * t339 / t341 / r0 * t662 + 0.51200000000000000000000000000000000000000000000000e-1 * t658 * t633 * t700 * t750
  t758 = 0.621814e-1 * t441 * t404
  t761 = t576 * t557
  t770 = f.my_piecewise3(t4, 0, t379 * (-t758 + t494 * (-0.3109070e-1 * t522 * t503 + t758 - 0.19751673498613801407483339618206552048944131217655e-1 * t761) + 0.19751673498613801407483339618206552048944131217655e-1 * t494 * t761) / 0.2e1)
  t772 = 0.1e1 / t656 / t215
  t774 = t655 * t772 * t339
  t775 = t341 * t354
  t779 = 0.1e1 / t19 / t775 * t662 * t364
  t783 = t655 * t738 * t633
  t785 = tau0 * t11
  t786 = t709 * t642 * t785
  t789 = t653 * t650
  t790 = t789 * t731
  t793 = t730 * t739
  t797 = t730 * t657 * t633
  t802 = 0.1e1 / t20 / t341 / t201
  t809 = t647 * t362
  t812 = t722 * t362
  t815 = t651 * t657
  t820 = 0.35555555555555555555555555555555555555555555555555e1 * t774 * t779 + 0.13653333333333333333333333333333333333333333333333e1 * t783 * t786 + 0.21333333333333333333333333333333333333333333333333e1 * t790 * t779 + 0.56888888888888888888888888888888888888888888888888e1 * t793 * t779 + 0.13653333333333333333333333333333333333333333333333e1 * t797 * t786 + 0.79644444444444444444444444444444444444444444444445e0 * t634 * t89 * t802 * t642 - 0.40e2 / 0.9e1 * t716 * t349 + 0.100e3 / 0.9e1 * t809 * t365 + 0.400e3 / 0.9e1 * t812 * t365 + 0.100e3 / 0.3e1 * t815 * t365 - 0.40e2 / 0.9e1 * t719 * t368
  t825 = t339 * t343
  t835 = 0.1e1 / t19 / t341 / t332
  t837 = t712 * t11
  t841 = t646 * t352
  t844 = t649 * t352
  t851 = t633 * t199
  t852 = t632 * t851
  t853 = t341 ** 2
  t855 = 0.1e1 / t853 / t90
  t857 = 0.1e1 / t641 / t640
  t862 = t700 * t662 * t110
  t867 = -0.80e2 / 0.9e1 * t723 * t368 - 0.80e2 / 0.9e1 * t726 * t368 + 0.2304e1 * t658 * t825 * t662 - 0.10069333333333333333333333333333333333333333333333e1 * t658 * t633 * t802 * t750 + 0.21845333333333333333333333333333333333333333333334e0 * t658 * t705 * t835 * t837 + 0.100e3 / 0.9e1 * t841 * t358 + 0.100e3 / 0.9e1 * t844 * t358 - 0.68266666666666666666666666666666666666666666666669e0 * t706 * t11 * t835 * t712 + 0.14563555555555555555555555555555555555555555555557e0 * t852 * t855 * t857 - 0.39822222222222222222222222222222222222222222222222e1 * t740 * t862 - 0.39822222222222222222222222222222222222222222222222e1 * t732 * t862
  t868 = t820 + t867
  t872 = t8 * t10 * t29
  t873 = jnp.sqrt(t872)
  t876 = t872 ** 0.15e1
  t879 = t393 * t9 * t122
  t881 = 0.37978500000000000000000000000000000000000000000000e1 * t873 + 0.89690000000000000000000000000000000000000000000000e0 * t872 + 0.20477500000000000000000000000000000000000000000000e0 * t876 + 0.12323500000000000000000000000000000000000000000000e0 * t879
  t884 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t881
  t885 = jnp.log(t884)
  t889 = t881 ** 2
  t890 = 0.1e1 / t889
  t891 = t127 * t890
  t893 = 0.1e1 / t873 * t5
  t894 = t7 * t10
  t895 = t894 * t127
  t896 = t893 * t895
  t899 = t872 ** 0.5e0
  t900 = t899 * t5
  t901 = t900 * t895
  t904 = t393 * t9 * t22
  t906 = -0.63297500000000000000000000000000000000000000000000e0 * t896 - 0.29896666666666666666666666666666666666666666666667e0 * t410 - 0.10238750000000000000000000000000000000000000000000e0 * t901 - 0.82156666666666666666666666666666666666666666666667e-1 * t904
  t907 = 0.1e1 / t884
  t908 = t906 * t907
  t913 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t872
  t915 = 0.1e1 / t889 / t881
  t916 = t913 * t915
  t917 = t906 ** 2
  t918 = t917 * t907
  t921 = t913 * t890
  t924 = 0.1e1 / t873 / t872 * t392
  t925 = t26 * t9
  t926 = t925 * t92
  t927 = t924 * t926
  t929 = t894 * t231
  t930 = t893 * t929
  t932 = t8 * t459
  t934 = t872 ** (-0.5e0)
  t935 = t934 * t392
  t936 = t935 * t926
  t938 = t900 * t929
  t940 = t393 * t454
  t942 = -0.42198333333333333333333333333333333333333333333333e0 * t927 + 0.84396666666666666666666666666666666666666666666666e0 * t930 + 0.39862222222222222222222222222222222222222222222223e0 * t932 + 0.68258333333333333333333333333333333333333333333333e-1 * t936 + 0.13651666666666666666666666666666666666666666666667e0 * t938 + 0.13692777777777777777777777777777777777777777777778e0 * t940
  t943 = t942 * t907
  t946 = t889 ** 2
  t947 = 0.1e1 / t946
  t948 = t913 * t947
  t949 = t884 ** 2
  t950 = 0.1e1 / t949
  t951 = t917 * t950
  t954 = f.my_piecewise3(t3, t16, 1)
  t957 = (0.2e1 * t954 - 0.2e1) * t493
  t958 = t957 * t5
  t963 = 0.51785000000000000000000000000000000000000000000000e1 * t873 + 0.90577500000000000000000000000000000000000000000000e0 * t872 + 0.11003250000000000000000000000000000000000000000000e0 * t876 + 0.12417750000000000000000000000000000000000000000000e0 * t879
  t966 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t963
  t967 = jnp.log(t966)
  t972 = t957 * t8
  t973 = t963 ** 2
  t974 = 0.1e1 / t973
  t979 = -0.86308333333333333333333333333333333333333333333334e0 * t896 - 0.30192500000000000000000000000000000000000000000000e0 * t410 - 0.55016250000000000000000000000000000000000000000000e-1 * t901 - 0.82785000000000000000000000000000000000000000000000e-1 * t904
  t981 = 0.1e1 / t966
  t982 = t974 * t979 * t981
  t987 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t872
  t988 = t957 * t987
  t990 = 0.1e1 / t973 / t963
  t991 = t979 ** 2
  t993 = t990 * t991 * t981
  t1002 = -0.57538888888888888888888888888888888888888888888889e0 * t927 + 0.11507777777777777777777777777777777777777777777778e1 * t930 + 0.40256666666666666666666666666666666666666666666667e0 * t932 + 0.36677500000000000000000000000000000000000000000000e-1 * t936 + 0.73355000000000000000000000000000000000000000000000e-1 * t938 + 0.13797500000000000000000000000000000000000000000000e0 * t940
  t1004 = t974 * t1002 * t981
  t1007 = t973 ** 2
  t1008 = 0.1e1 / t1007
  t1010 = t966 ** 2
  t1011 = 0.1e1 / t1010
  t1012 = t1008 * t991 * t1011
  t1016 = -0.14764627977777777777777777777777777777777777777777e-2 * t8 * t459 * t885 - 0.35616666666666666666666666666666666666666666666666e-1 * t380 * t891 * t908 - 0.20000000000000000000000000000000000000000000000000e1 * t916 * t918 + 0.10000000000000000000000000000000000000000000000000e1 * t921 * t943 + 0.16081979498692535066756296899072713062105388428051e2 * t948 * t951 + 0.24415263074675393406472461472505321282722606644045e-3 * t958 * t894 * t231 * t967 + 0.10843581300301739842632067522386578331157260943710e-1 * t972 * t409 * t982 + 0.11696447245269292414524477327518106963944910680856e1 * t988 * t993 - 0.58482236226346462072622386637590534819724553404280e0 * t988 * t1004 - 0.17315859105681463759666483083807725165579399831905e2 * t988 * t1012 - 0.2e1 * t630
  t1018 = params.c_os[1]
  t1020 = 0.3e1 / 0.5e1 * t108 * t111
  t1022 = 0.1e1 / t19 / t192
  t1024 = 0.4e1 * t364 * t1022
  t1025 = t1020 - t1024
  t1026 = t1018 * t1025
  t1027 = t1020 + t1024
  t1028 = 0.1e1 / t1027
  t1030 = params.c_os[2]
  t1031 = t1025 ** 2
  t1032 = t1030 * t1031
  t1033 = t1027 ** 2
  t1034 = 0.1e1 / t1033
  t1036 = params.c_os[3]
  t1037 = t1036 * t1031
  t1038 = t1037 * t1034
  t1040 = 0.1e1 + 0.6e-2 * t95
  t1041 = 0.1e1 / t1040
  t1043 = t94 * t92 * t1041
  t1046 = params.c_os[4]
  t1047 = t1031 ** 2
  t1048 = t1047 * t1031
  t1049 = t1046 * t1048
  t1050 = t1033 ** 2
  t1052 = 0.1e1 / t1050 / t1033
  t1054 = params.c_os[5]
  t1055 = t1054 * t1048
  t1056 = t1055 * t1052
  t1059 = params.c_os[0] + t1026 * t1028 + t1032 * t1034 + 0.6e-2 * t1038 * t1043 + t1049 * t1052 + 0.6e-2 * t1056 * t1043
  t1074 = 0.11073470983333333333333333333333333333333333333333e-2 * t8 * t409 * t885 + 0.10000000000000000000000000000000000000000000000000e1 * t921 * t908 - 0.18311447306006545054854346104378990962041954983034e-3 * t958 * t894 * t127 * t967 - 0.58482236226346462072622386637590534819724553404280e0 * t988 * t982 - 0.2e1 * t697
  t1075 = t108 * t218
  t1079 = 0.40e2 / 0.3e1 * t364 / t19 / t201
  t1080 = -t1075 + t1079
  t1081 = t1018 * t1080
  t1083 = -t1075 - t1079
  t1084 = t1034 * t1083
  t1086 = t1030 * t1025
  t1090 = t1033 * t1027
  t1091 = 0.1e1 / t1090
  t1092 = t1091 * t1083
  t1095 = t1036 * t1025
  t1096 = t1034 * s0
  t1097 = t1095 * t1096
  t1098 = t1041 * t1080
  t1099 = t93 * t1098
  t1102 = t1091 * s0
  t1103 = t1037 * t1102
  t1104 = t1041 * t1083
  t1105 = t93 * t1104
  t1109 = t94 * t194 * t1041
  t1112 = t199 * t11
  t1113 = t1040 ** 2
  t1114 = 0.1e1 / t1113
  t1116 = t1112 * t204 * t1114
  t1119 = t1047 * t1025
  t1120 = t1046 * t1119
  t1121 = t1052 * t1080
  t1125 = 0.1e1 / t1050 / t1090
  t1129 = t1054 * t1119
  t1130 = t1052 * s0
  t1131 = t1129 * t1130
  t1134 = t1125 * s0
  t1135 = t1055 * t1134
  t1142 = t1081 * t1028 - t1026 * t1084 + 0.2e1 * t1086 * t1034 * t1080 - 0.2e1 * t1032 * t1092 + 0.12e-1 * t1097 * t1099 - 0.12e-1 * t1103 * t1105 - 0.16000000000000000000000000000000000000000000000000e-1 * t1038 * t1109 + 0.19200000000000000000000000000000000000000000000000e-3 * t1038 * t1116 + 0.6e1 * t1120 * t1121 - 0.6e1 * t1049 * t1125 * t1083 + 0.36e-1 * t1131 * t1099 - 0.36e-1 * t1135 * t1105 - 0.16000000000000000000000000000000000000000000000000e-1 * t1056 * t1109 + 0.19200000000000000000000000000000000000000000000000e-3 * t1056 * t1116
  t1151 = -0.621814e-1 * t913 * t885 + 0.19751673498613801407483339618206552048944131217655e-1 * t957 * t987 * t967 - 0.2e1 * t770
  t1161 = 0.1e1 / t1113 / t1040
  t1162 = t825 * t1161
  t1168 = 0.8e1 / 0.3e1 * t108 * t368
  t1169 = 0.520e3 / 0.9e1 * t365
  t1170 = t1168 - t1169
  t1171 = t1041 * t1170
  t1172 = t93 * t1171
  t1175 = t1052 * t199
  t1176 = t1129 * t1175
  t1177 = t1114 * t1080
  t1178 = t205 * t1177
  t1181 = t1168 + t1169
  t1182 = t1041 * t1181
  t1183 = t93 * t1182
  t1186 = t1125 * t199
  t1187 = t1055 * t1186
  t1188 = t1114 * t1083
  t1189 = t205 * t1188
  t1195 = t1095 * t1034 * t199
  t1200 = t1091 * t199
  t1201 = t1037 * t1200
  t1204 = t195 * t1104
  t1207 = t1054 * t1047
  t1208 = t1207 * t1130
  t1209 = t1080 ** 2
  t1210 = t1041 * t1209
  t1214 = t195 * t1098
  t1217 = t1050 ** 2
  t1218 = 0.1e1 / t1217
  t1219 = t1218 * s0
  t1220 = t1055 * t1219
  t1221 = t1083 ** 2
  t1222 = t1041 * t1221
  t1223 = t93 * t1222
  t1230 = 0.1e1 / t1050
  t1231 = t1230 * s0
  t1232 = t1037 * t1231
  t1235 = -0.72e2 * t1120 * t1125 * t1080 * t1083 - 0.8e1 * t1086 * t1091 * t1080 * t1083 + 0.12288000000000000000000000000000000000000000000000e-4 * t1038 * t1162 + 0.12288000000000000000000000000000000000000000000000e-4 * t1056 * t1162 + 0.36e-1 * t1131 * t1172 + 0.23040000000000000000000000000000000000000000000000e-2 * t1176 * t1178 - 0.36e-1 * t1135 * t1183 - 0.23040000000000000000000000000000000000000000000000e-2 * t1187 * t1189 + 0.12e-1 * t1097 * t1172 + 0.76800000000000000000000000000000000000000000000000e-3 * t1195 * t1178 - 0.12e-1 * t1103 * t1183 - 0.76800000000000000000000000000000000000000000000000e-3 * t1201 * t1189 + 0.64000000000000000000000000000000000000000000000000e-1 * t1103 * t1204 + 0.180e0 * t1208 * t93 * t1210 - 0.19200000000000000000000000000000000000000000000000e0 * t1131 * t1214 + 0.252e0 * t1220 * t1223 + 0.19200000000000000000000000000000000000000000000000e0 * t1135 * t1204 - 0.64000000000000000000000000000000000000000000000000e-1 * t1097 * t1214 + 0.36e-1 * t1232 * t1223
  t1236 = t1129 * t1134
  t1237 = t1098 * t1083
  t1238 = t93 * t1237
  t1241 = t1095 * t1102
  t1245 = t94 * t327 * t1041
  t1250 = t1036 * t1209
  t1251 = t1250 * t1034
  t1255 = t1112 * t334 * t1114
  t1260 = t1034 * t1181
  t1262 = t1034 * t1170
  t1265 = t1091 * t1181
  t1271 = t1125 * t1181
  t1274 = t1218 * t1221
  t1277 = t1091 * t1221
  t1280 = t1230 * t1221
  t1283 = t1046 * t1047
  t1289 = t1018 * t1170
  t1291 = t1030 * t1209
  t1294 = -0.432e0 * t1236 * t1238 - 0.48e-1 * t1241 * t1238 + 0.58666666666666666666666666666666666666666666666667e-1 * t1038 * t1245 + 0.58666666666666666666666666666666666666666666666667e-1 * t1056 * t1245 + 0.12e-1 * t1251 * t1043 - 0.17280000000000000000000000000000000000000000000000e-2 * t1056 * t1255 - 0.17280000000000000000000000000000000000000000000000e-2 * t1038 * t1255 - t1026 * t1260 + 0.2e1 * t1086 * t1262 - 0.2e1 * t1032 * t1265 + 0.6e1 * t1120 * t1052 * t1170 - 0.6e1 * t1049 * t1271 + 0.42e2 * t1049 * t1274 + 0.2e1 * t1026 * t1277 + 0.6e1 * t1032 * t1280 + 0.30e2 * t1283 * t1052 * t1209 - 0.2e1 * t1081 * t1084 + t1289 * t1028 + 0.2e1 * t1291 * t1034
  t1295 = t1235 + t1294
  t1320 = 0.14e2 / 0.243e3 * t28 * t5 * t1022 * t33
  t1321 = f.my_piecewise3(t38, -t1320, 0)
  t1338 = t227 * t132
  t1349 = -t125 * t1321 / 0.18e2 + t136 * t1321 / 0.240e3 - t140 * t1321 / 0.4480e4 + t144 * t1321 / 0.103680e6 - t148 * t1321 / 0.2838528e7 + t152 * t1321 / 0.89456640e8 - t156 * t1321 / 0.3185049600e10 + t160 * t1321 / 0.126340300800e12 - 0.2e1 / 0.3e1 * t136 * t1338 + t44 * t132 * t236 / 0.2e1 + t140 * t1338 / 0.8e1 - t47 * t132 * t236 / 0.16e2
  t1382 = -t144 * t1338 / 0.80e2 + 0.3e1 / 0.640e3 * t50 * t132 * t236 + t148 * t1338 / 0.1152e4 - t53 * t132 * t236 / 0.3840e4 - t152 * t1338 / 0.21504e5 + t56 * t132 * t236 / 0.86016e5 + t156 * t1338 / 0.491520e6 - t59 * t132 * t236 / 0.2293760e7 - t160 * t1338 / 0.13271040e8 + t62 * t132 * t236 / 0.70778880e8 + 0.1e1 / t61 / t124 * t1338 / 0.412876800e9 - t264 * t132 * t236 / 0.2477260800e10
  t1384 = f.my_piecewise3(t38, 0, -t1320)
  t1391 = t278 * t164
  t1396 = t74 * t270
  t1399 = t275 ** 2
  t1457 = f.my_piecewise3(t37, t1349 + t1382, -0.8e1 / 0.3e1 * t1384 * t81 - 0.8e1 * t270 * t183 - 0.8e1 * t164 * t313 - 0.8e1 / 0.3e1 * t65 * (0.7e1 / 0.2e1 * t298 * t1391 * t74 - 0.3e1 / 0.2e1 * t277 * t164 * t1396 - 0.1e1 / t1399 * t1391 * t74 / 0.4e1 - 0.6e1 * t74 * t290 * t1391 + 0.6e1 * t282 * t164 * t270 - t166 * t1384 + 0.2e1 * t1384 * t78 + 0.6e1 * t270 * t180 + 0.6e1 * t164 * t310 + 0.2e1 * t65 * (0.15e2 / 0.2e1 * t277 * t1391 * t74 - 0.6e1 * t290 * t164 * t1396 - 0.5e1 / 0.2e1 / t275 / t170 * t1391 * t74 + t171 * t1384 * t74 / 0.2e1 + 0.3e1 / 0.4e1 * t298 * t270 * t164 * t74 + 0.1e1 / t1399 / t65 * t1391 * t74 / 0.8e1 - 0.12e2 * t164 * t75 * t270 - 0.3e1 * t72 * t164 * t1396 - 0.4e1 * t175 * t1384 - t67 * t1384 * t74)))
  t1471 = 0.1e1 / t20 / t354
  t1477 = 0.1e1 / t19 / t341
  t1482 = 0.1e1 / t698
  t1488 = 0.1e1 / t20 / t775
  t1489 = t206 ** 2
  t1495 = t328 * t115
  t1498 = t205 * t216
  t1501 = t352 * tau0
  t1503 = t659 * t362
  t1507 = t657 * t1501 * t659
  t1510 = t364 * t204
  t1513 = t110 * t327
  t1522 = f.my_piecewise3(t4, 0, -0.5e1 / 0.288e3 * t13 * t18 * t92 * t118 + t13 * t23 * t188 / 0.32e2 + t13 * t23 * t222 / 0.32e2 - 0.3e1 / 0.64e2 * t13 * t123 * t318 - 0.3e1 / 0.32e2 * t13 * t123 * t322 - 0.3e1 / 0.64e2 * t13 * t123 * t372 - 0.3e1 / 0.64e2 * t13 * t226 * t1457 * t117 - 0.9e1 / 0.64e2 * t13 * t226 * t317 * t221 - 0.9e1 / 0.64e2 * t13 * t226 * t187 * t371 - 0.3e1 / 0.64e2 * t13 * t226 * t85 * (-0.18251851851851851851851851851851851851851851851852e0 * t88 * t89 * t1471 * t98 + 0.64663703703703703703703703703703703703703703703706e-2 * t200 * t11 * t1477 * t207 - 0.69176888888888888888888888888888888888888888888893e-4 * t340 * t1482 * t345 + 0.11650844444444444444444444444444444444444444444445e-6 * t87 * t633 * t1488 / t1489 * t89 + 0.440e3 / 0.27e2 * t211 * t1495 - 0.800e3 / 0.9e1 * t353 * t1498 + 0.1000e4 / 0.9e1 * t102 * t1501 * t1503 + 0.1000e4 / 0.9e1 * t113 * t1507 - 0.800e3 / 0.9e1 * t363 * t1510 + 0.440e3 / 0.27e2 * t217 * t1513))
  t1536 = t10 * t1022
  t1544 = 0.10685000000000000000000000000000000000000000000000e0 * t410 * t411 * t443 * t445 * t435
  t1546 = 0.71233333333333333333333333333333333333333333333331e-1 * t932 * t437
  t1551 = 0.53424999999999999999999999999999999999999999999999e-1 * t410 * t411 * t413 * t476 * t435
  t1556 = 0.85917975471764868594145516183295969534298037676861e0 * t410 * t411 * t481 * t445 * t484
  t1557 = t1022 * t11
  t1560 = 0.34450798614814814814814814814814814814814814814813e-2 * t380 * t1557 * t405
  t1566 = -0.21687162600603479685264135044773156662314521887420e-1 * t610 * t463 * t571 + 0.16265371950452609763948101283579867496735891415565e-1 * t610 * t421 * t620 + 0.48159733137676571081572406076840235616767705782485e0 * t610 * t421 * t624 - 0.32530743900905219527896202567159734993471782831130e-1 * t610 * t421 * t616 - 0.56968947174242584615102410102512416326352748836105e-3 * t605 * t1536 * t606 + t1544 + t1546 - t1551 - t1556 + t1560 - 0.51947577317044391278999449251423175496738199495715e2 * t614 * t596 * t591 * t599 * t568
  t1567 = t580 * t568
  t1577 = 0.1e1 / t595 / t562
  t1580 = 0.1e1 / t598 / t556
  t1585 = 0.1e1 / t595 / t553
  t1594 = 0.1e1 / t201
  t1596 = t1594 * t396 * t383
  t1597 = 0.1e1 / t387 / t398 * t6 * t1596 / 0.4e1
  t1599 = t9 * t194
  t1600 = t1599 * t455
  t1601 = t453 * t1600
  t1603 = t1536 * t411
  t1604 = t416 * t1603
  t1607 = t380 * t1557 * t383
  t1609 = t386 ** (-0.15e1)
  t1611 = t1609 * t6 * t1596
  t1613 = t468 * t1600
  t1615 = t426 * t1603
  t1618 = t394 * t195 * t396
  t1620 = -0.69046666666666666666666666666666666666666666666667e1 * t1597 + 0.23015555555555555555555555555555555555555555555556e1 * t1601 - 0.26851481481481481481481481481481481481481481481482e1 * t1604 - 0.93932222222222222222222222222222222222222222222223e0 * t1607 + 0.14671000000000000000000000000000000000000000000000e0 * t1611 - 0.14671000000000000000000000000000000000000000000000e0 * t1613 - 0.17116166666666666666666666666666666666666666666667e0 * t1615 - 0.36793333333333333333333333333333333333333333333333e0 * t1618
  t1628 = t445 * t433
  t1633 = 0.51726012919273400298984252201052768390886626637712e3 * t441 / t480 / t412 * t1628 / t483 / t403
  t1639 = 0.96491876992155210400537781394436278372632330568306e2 * t441 / t480 / t400 * t1628 * t484
  t1651 = 0.10000000000000000000000000000000000000000000000000e1 * t449 * (-0.50638000000000000000000000000000000000000000000000e1 * t1597 + 0.16879333333333333333333333333333333333333333333333e1 * t1601 - 0.19692555555555555555555555555555555555555555555555e1 * t1604 - 0.93011851851851851851851851851851851851851851851854e0 * t1607 + 0.27303333333333333333333333333333333333333333333333e0 * t1611 - 0.27303333333333333333333333333333333333333333333333e0 * t1613 - 0.31853888888888888888888888888888888888888888888890e0 * t1615 - 0.36514074074074074074074074074074074074074074074075e0 * t1618) * t435
  t1654 = 0.60000000000000000000000000000000000000000000000000e1 * t482 * t1628 * t435
  t1657 = 0.60000000000000000000000000000000000000000000000000e1 * t444 * t672 * t476
  t1661 = 0.48245938496077605200268890697218139186316165284153e2 * t482 * t476 * t484 * t433
  t1679 = t526 * t514
  t1713 = t1657 - t1661 - 0.60000000000000000000000000000000000000000000000000e1 * t525 * t678 * t537 + 0.96491876992155210400537781394436278372632330568306e2 * t543 * t537 * t545 * t514 - 0.35089341735807877243573431982554320891834732042568e1 * t579 * t684 * t591 + 0.51947577317044391278999449251423175496738199495715e2 * t597 * t591 * t599 * t568 - 0.19298375398431042080107556278887255674526466113661e3 * t522 / t541 / t499 * t1679 * t545 + 0.10000000000000000000000000000000000000000000000000e1 * t530 * (-0.94126000000000000000000000000000000000000000000000e1 * t1597 + 0.31375333333333333333333333333333333333333333333334e1 * t1601 - 0.36604555555555555555555555555555555555555555555556e1 * t1604 - 0.16068111111111111111111111111111111111111111111111e1 * t1607 + 0.56103333333333333333333333333333333333333333333332e0 * t1611 - 0.56103333333333333333333333333333333333333333333332e0 * t1613 - 0.65453888888888888888888888888888888888888888888890e0 * t1615 - 0.46308888888888888888888888888888888888888888888888e0 * t1618) * t516 + 0.20690405167709360119593700880421107356354650655085e4 * t522 / t541 / t508 * t1679 / t544 / t502 - t1633 + t1639 - t1651 - t1654 + 0.60000000000000000000000000000000000000000000000000e1 * t543 * t1679 * t516 + 0.35089341735807877243573431982554320891834732042568e1 * t597 * t1567 * t570 + 0.10254018858216406658218194626490193680059335835414e4 * t576 * t1577 * t1567 * t1580
  t1755 = -0.10389515463408878255799889850284635099347639899143e3 * t576 * t1585 * t1567 * t599 + 0.58482236226346462072622386637590534819724553404280e0 * t584 * t1620 * t570 + 0.68493333333333333333333333333333333333333333333332e-1 * t932 * t518 - 0.51369999999999999999999999999999999999999999999999e-1 * t410 * t411 * t509 * t537 * t516 + 0.32530743900905219527896202567159734993471782831130e-1 * t410 * t411 * t616 + 0.10274000000000000000000000000000000000000000000000e0 * t410 * t411 * t524 * t526 * t516 + 0.21687162600603479685264135044773156662314521887420e-1 * t932 * t572 - 0.16265371950452609763948101283579867496735891415565e-1 * t410 * t411 * t620 - t1544 - t1546 + t1551 + t1556 - 0.48159733137676571081572406076840235616767705782485e0 * t410 * t411 * t624 - 0.16522625736956710527585419434107305400007076070979e1 * t410 * t411 * t542 * t526 * t545 - t1560 + 0.16562821945185185185185185185185185185185185185185e-2 * t380 * t1557 * t504 + 0.56968947174242584615102410102512416326352748836105e-3 * t380 * t1557 * t558
  t1758 = -0.35089341735807877243573431982554320891834732042568e1 * t614 * t596 * t1567 * t570 + 0.35089341735807877243573431982554320891834732042568e1 * t614 * t578 * t568 * t592 - 0.10254018858216406658218194626490193680059335835414e4 * t614 * t1577 * t1567 * t1580 + 0.10389515463408878255799889850284635099347639899143e3 * t614 * t1585 * t1567 * t599 - 0.58482236226346462072622386637590534819724553404280e0 * t614 * t563 * t1620 * t570 + t1633 - t1639 + t1651 + t1654 - t1657 + t1661 + t494 * (t1713 + t1755)
  t1762 = f.my_piecewise3(t4, 0, t379 * (t1566 + t1758) / 0.2e1)
  t1770 = 0.1e1 / t19 / t853
  t1811 = 0.1e1 / t853 / t192
  t1815 = t633 * t1488
  t1827 = t339 / t853 * t662 * t1501
  t1840 = t633 / t853 / r0 * t642 * t352
  t1849 = t705 * t855 * t712 * tau0
  t1852 = 0.13865718518518518518518518518518518518518518518519e2 * t706 * t11 * t1770 * t712 - 0.800e3 / 0.9e1 * t841 * t1498 + 0.1000e4 / 0.9e1 * t647 * t1507 + 0.2000e4 / 0.3e1 * t722 * t1507 + 0.4000e4 / 0.9e1 * t651 * t738 * t1501 * t659 - 0.800e3 / 0.9e1 * t844 * t1498 - 0.10088296296296296296296296296296296296296296296296e2 * t634 * t89 * t1488 * t642 + 0.440e3 / 0.27e2 * t716 * t1495 + 0.46603377777777777777777777777777777777777777777782e0 * t632 * t633 * t339 / t20 / t853 / t354 / t641 / t661 * t89 + 0.1000e4 / 0.9e1 * t646 * t1501 * t1503 + 0.2000e4 / 0.9e1 * t649 * t1501 * t1503 - 0.62623288888888888888888888888888888888888888888894e1 * t852 * t1811 * t857 + 0.16440888888888888888888888888888888888888888888889e2 * t658 * t1815 * t750 - 0.76458666666666666666666666666666666666666666666668e1 * t658 * t705 * t1770 * t837 + 0.14222222222222222222222222222222222222222222222222e3 * t730 * t772 * t1827 + 0.71111111111111111111111111111111111111111111111110e2 * t655 / t656 / t361 * t1827 + 0.34133333333333333333333333333333333333333333333333e2 * t655 * t772 * t1840 + 0.54613333333333333333333333333333333333333333333333e2 * t730 * t738 * t1840 + 0.87381333333333333333333333333333333333333333333335e1 * t655 * t738 * t1849
  t1867 = t709 * t662 * t364
  t1871 = t835 * t642 * t785
  t1875 = t802 * t662 * t110
  t1898 = t339 * t1482
  t1906 = 0.14222222222222222222222222222222222222222222222222e2 * t653 * t112 * t657 * t1827 + 0.85333333333333333333333333333333333333333333333332e2 * t789 * t738 * t1827 + 0.20480000000000000000000000000000000000000000000000e2 * t789 * t657 * t1840 + 0.87381333333333333333333333333333333333333333333335e1 * t730 * t657 * t1849 - 0.18204444444444444444444444444444444444444444444445e3 * t793 * t1867 - 0.45738666666666666666666666666666666666666666666665e2 * t797 * t1871 + 0.61819259259259259259259259259259259259259259259259e2 * t732 * t1875 + 0.61819259259259259259259259259259259259259259259259e2 * t740 * t1875 - 0.11377777777777777777777777777777777777777777777778e3 * t774 * t1867 - 0.45738666666666666666666666666666666666666666666665e2 * t783 * t1871 - 0.68266666666666666666666666666666666666666666666666e2 * t790 * t1867 + 0.11650844444444444444444444444444444444444444444445e1 * t658 * t851 * t1811 * t857 - 0.800e3 / 0.3e1 * t815 * t1510 + 0.440e3 / 0.27e2 * t719 * t1513 + 0.880e3 / 0.27e2 * t723 * t1513 + 0.880e3 / 0.27e2 * t726 * t1513 - 0.23040e2 * t658 * t1898 * t662 - 0.800e3 / 0.9e1 * t809 * t1510 - 0.3200e4 / 0.9e1 * t812 * t1510
  t1926 = t917 * t906
  t1944 = t991 * t979
  t1951 = -0.21687162600603479685264135044773156662314521887420e-1 * t972 * t459 * t982 + 0.16265371950452609763948101283579867496735891415565e-1 * t972 * t409 * t1004 + 0.48159733137676571081572406076840235616767705782485e0 * t972 * t409 * t1012 - 0.32530743900905219527896202567159734993471782831130e-1 * t972 * t409 * t993 + 0.48245938496077605200268890697218139186316165284153e2 * t948 * t942 * t950 * t906 + 0.60000000000000000000000000000000000000000000000000e1 * t948 * t1926 * t907 - 0.60000000000000000000000000000000000000000000000000e1 * t916 * t908 * t942 + 0.10685000000000000000000000000000000000000000000000e0 * t380 * t127 * t915 * t918 - 0.56968947174242584615102410102512416326352748836105e-3 * t958 * t894 * t1022 * t967 - 0.2e1 * t1762 - 0.10254018858216406658218194626490193680059335835414e4 * t988 / t1007 / t973 * t1944 / t1010 / t966
  t1962 = 0.1e1 / t873 / t879 * t6 * t1594 / 0.4e1
  t1964 = t925 * t194
  t1965 = t924 * t1964
  t1967 = t894 * t1022
  t1968 = t893 * t1967
  t1970 = t8 * t1536
  t1972 = t872 ** (-0.15e1)
  t1974 = t1972 * t6 * t1594
  t1976 = t935 * t1964
  t1978 = t900 * t1967
  t1980 = t393 * t1599
  t2041 = 0.10389515463408878255799889850284635099347639899143e3 * t988 / t1007 / t963 * t1944 * t1011 - 0.58482236226346462072622386637590534819724553404280e0 * t988 * t974 * (-0.34523333333333333333333333333333333333333333333333e1 * t1962 + 0.23015555555555555555555555555555555555555555555556e1 * t1965 - 0.26851481481481481481481481481481481481481481481482e1 * t1968 - 0.93932222222222222222222222222222222222222222222223e0 * t1970 + 0.73355000000000000000000000000000000000000000000000e-1 * t1974 - 0.14671000000000000000000000000000000000000000000000e0 * t1976 - 0.17116166666666666666666666666666666666666666666667e0 * t1978 - 0.36793333333333333333333333333333333333333333333333e0 * t1980) * t981 + 0.51726012919273400298984252201052768390886626637712e3 * t913 / t946 / t889 * t1926 / t949 / t884 - 0.96491876992155210400537781394436278372632330568306e2 * t913 / t946 / t881 * t1926 * t950 + 0.10000000000000000000000000000000000000000000000000e1 * t921 * (-0.25319000000000000000000000000000000000000000000000e1 * t1962 + 0.16879333333333333333333333333333333333333333333333e1 * t1965 - 0.19692555555555555555555555555555555555555555555555e1 * t1968 - 0.93011851851851851851851851851851851851851851851854e0 * t1970 + 0.13651666666666666666666666666666666666666666666667e0 * t1974 - 0.27303333333333333333333333333333333333333333333333e0 * t1976 - 0.31853888888888888888888888888888888888888888888890e0 * t1978 - 0.36514074074074074074074074074074074074074074074075e0 * t1980) * t907 + 0.34450798614814814814814814814814814814814814814813e-2 * t8 * t1536 * t885 - 0.51947577317044391278999449251423175496738199495715e2 * t988 * t1008 * t1002 * t1011 * t979 - 0.35089341735807877243573431982554320891834732042568e1 * t988 * t1008 * t1944 * t981 + 0.35089341735807877243573431982554320891834732042568e1 * t988 * t990 * t979 * t981 * t1002 + 0.71233333333333333333333333333333333333333333333331e-1 * t380 * t231 * t890 * t908 - 0.53424999999999999999999999999999999999999999999999e-1 * t380 * t891 * t943 - 0.85917975471764868594145516183295969534298037676861e0 * t380 * t127 * t947 * t951
  t2049 = t94 * t1471 * t1041
  t2060 = t825 * t1161 * t1080
  t2065 = t825 * t1161 * t1083
  t2074 = t1113 ** 2
  t2077 = t1815 / t2074 * t89
  t2084 = t1112 * t1477 * t1114
  t2089 = t1898 * t1161
  t2095 = t93 * t1171 * t1083
  t2100 = t93 * t1222 * t1080
  t2107 = t93 * t1182 * t1080
  t2111 = t93 * t1182 * t1083
  t2114 = t195 * t1237
  t2122 = 0.14549333333333333333333333333333333333333333333333e-1 * t1038 * t2084 + 0.14549333333333333333333333333333333333333333333333e-1 * t1056 * t2084 - 0.23347200000000000000000000000000000000000000000000e-3 * t1038 * t2089 - 0.23347200000000000000000000000000000000000000000000e-3 * t1056 * t2089 - 0.648e0 * t1236 * t2095 + 0.4536e1 * t1129 * t1219 * t2100 + 0.216e0 * t1095 * t1231 * t2100 - 0.72e-1 * t1241 * t2107 + 0.108e0 * t1232 * t2111 + 0.38400000000000000000000000000000000000000000000000e0 * t1241 * t2114 - 0.3240e1 * t1207 * t1134 * t93 * t1210 * t1083
  t2128 = t205 * t1177 * t1083
  t2147 = 0.88e2 / 0.9e1 * t108 * t1513
  t2148 = 0.8320e4 / 0.27e2 * t1510
  t2149 = -t2147 - t2148
  t2157 = 0.1e1 / t1217 / t1027
  t2158 = t1221 * t1083
  t2166 = 0.1e1 / t1050 / t1027
  t2170 = t1031 * t1025
  t2172 = t1209 * t1080
  t2185 = -t2147 + t2148
  t2195 = 0.120e3 * t1046 * t2170 * t1052 * t2172 - t1026 * t1034 * t2149 - 0.6e1 * t1026 * t1230 * t2158 + 0.6e1 * t1030 * t1080 * t1262 - 0.2e1 * t1032 * t1091 * t2149 - 0.24e2 * t1032 * t2166 * t2158 + 0.2e1 * t1086 * t1034 * t2185 - 0.336e3 * t1049 * t2157 * t2158 + 0.6e1 * t1120 * t1052 * t2185 - 0.3e1 * t1081 * t1260 - 0.3e1 * t1289 * t1084
  t2237 = t335 * t1188
  t2240 = t195 * t1171
  t2243 = t335 * t1177
  t2249 = t93 * t1041 * t2185
  t2253 = t205 * t1114 * t1170
  t2257 = t93 * t1041 * t2149
  t2261 = t205 * t1114 * t1181
  t2267 = t328 * t1098
  t2270 = 0.6e1 * t1026 * t1092 * t1181 + 0.31104000000000000000000000000000000000000000000000e-1 * t1187 * t2237 - 0.96000000000000000000000000000000000000000000000000e-1 * t1097 * t2240 - 0.10368000000000000000000000000000000000000000000000e-1 * t1195 * t2243 - 0.28800000000000000000000000000000000000000000000000e0 * t1131 * t2240 + 0.36e-1 * t1131 * t2249 + 0.34560000000000000000000000000000000000000000000000e-2 * t1176 * t2253 - 0.36e-1 * t1135 * t2257 - 0.34560000000000000000000000000000000000000000000000e-2 * t1187 * t2261 - 0.72e-1 * t1250 * t1102 * t1105 + 0.10560000000000000000000000000000000000000000000000e1 * t1131 * t2267
  t2275 = t93 * t1041 * t2158
  t2278 = t195 * t1222
  t2281 = t328 * t1104
  t2290 = t195 * t1182
  t2296 = t205 * t1114 * t1221
  t2311 = -0.2016e1 * t1055 * t2157 * s0 * t2275 - 0.20160000000000000000000000000000000000000000000000e1 * t1220 * t2278 - 0.10560000000000000000000000000000000000000000000000e1 * t1135 * t2281 + 0.35200000000000000000000000000000000000000000000000e0 * t1097 * t2267 - 0.144e0 * t1037 * t2166 * s0 * t2275 + 0.96000000000000000000000000000000000000000000000000e-1 * t1103 * t2290 + 0.34560000000000000000000000000000000000000000000000e-2 * t1037 * t1230 * t199 * t2296 + 0.10368000000000000000000000000000000000000000000000e-1 * t1201 * t2237 - 0.28800000000000000000000000000000000000000000000000e0 * t1232 * t2278 - 0.35200000000000000000000000000000000000000000000000e0 * t1103 * t2281 + 0.720e0 * t1054 * t2170 * t1130 * t93 * t1041 * t2172
  t2342 = -0.14400000000000000000000000000000000000000000000000e1 * t1208 * t195 * t1210 + 0.36e-1 * t1036 * t1080 * t1096 * t1172 + 0.12e-1 * t1097 * t2249 + 0.11520000000000000000000000000000000000000000000000e-2 * t1195 * t2253 - 0.12e-1 * t1103 * t2257 - 0.11520000000000000000000000000000000000000000000000e-2 * t1201 * t2261 + 0.17280000000000000000000000000000000000000000000000e-1 * t1207 * t1175 * t205 * t1114 * t1209 - 0.31104000000000000000000000000000000000000000000000e-1 * t1176 * t2243 + 0.28800000000000000000000000000000000000000000000000e0 * t1135 * t2290 + 0.24192000000000000000000000000000000000000000000000e-1 * t1055 * t1218 * t199 * t2296 + t1018 * t2185 * t1028
  v3rho3_0_ = 0.6e1 * t377 + 0.6e1 * t630 * t666 + 0.12e2 * t697 * t754 + 0.6e1 * t770 * t868 + 0.3e1 * t1016 * t1059 + 0.6e1 * t1074 * t1142 + 0.3e1 * t1151 * t1295 + r0 * (0.2e1 * t1522 + 0.2e1 * t1762 * t666 + 0.6e1 * t630 * t754 + 0.6e1 * t697 * t868 + 0.2e1 * t770 * (t1852 + t1906) + (t1951 + t2041) * t1059 + 0.3e1 * t1016 * t1142 + 0.3e1 * t1074 * t1295 + t1151 * (t2195 - 0.46080000000000000000000000000000000000000000000000e-2 * t1095 * t1200 * t2128 - 0.6e1 * t1049 * t1125 * t2149 + 0.36e2 * t1086 * t1280 * t1080 + 0.90e2 * t1283 * t1121 * t1170 - 0.12e2 * t1086 * t1265 * t1080 - 0.108e3 * t1120 * t1271 * t1080 + 0.756e3 * t1120 * t1274 * t1080 + 0.22118400000000000000000000000000000000000000000000e-3 * t1129 * t1052 * t2060 - 0.22118400000000000000000000000000000000000000000000e-3 * t1055 * t1125 * t2065 + 0.73728000000000000000000000000000000000000000000000e-4 * t1095 * t1034 * t2060 - 0.73728000000000000000000000000000000000000000000000e-4 * t1037 * t1091 * t2065 - 0.41472000000000000000000000000000000000000000000000e-1 * t1129 * t1186 * t2128 - 0.12e2 * t1291 * t1092 + 0.6e1 * t1081 * t1277 + 0.34560000000000000000000000000000000000000000000000e1 * t1236 * t2114 - 0.648e0 * t1236 * t2107 + 0.756e0 * t1220 * t2111 - 0.72e-1 * t1241 * t2095 + 0.58982400000000000000000000000000000000000000000000e-6 * t1038 * t2077 + 0.58982400000000000000000000000000000000000000000000e-6 * t1056 * t2077 - 0.27377777777777777777777777777777777777777777777778e0 * t1056 * t2049 - 0.96000000000000000000000000000000000000000000000000e-1 * t1251 * t1109 - 0.27377777777777777777777777777777777777777777777778e0 * t1038 * t2049 + 0.11520000000000000000000000000000000000000000000000e-2 * t1251 * t1116 + t2122 + t2342 + t2311 + t2270 + 0.540e0 * t1208 * t93 * t1171 * t1080 + 0.18e2 * t1032 * t1230 * t1083 * t1181 - 0.540e3 * t1283 * t1125 * t1209 * t1083 - 0.12e2 * t1086 * t1091 * t1170 * t1083 - 0.108e3 * t1120 * t1125 * t1170 * t1083 + 0.126e3 * t1049 * t1218 * t1181 * t1083))

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = jnp.logical_or(r0 / 0.2e1 <= f.p.dens_threshold, t3)
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
  t19 = r0 ** 2
  t20 = r0 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t23 = 0.1e1 / t21 / t19
  t24 = t18 * t23
  t25 = 9 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = t7 ** 2
  t29 = t26 * t27 * f.p.cam_omega
  t30 = 0.1e1 / t20
  t32 = f.my_piecewise3(t14, t15, t11)
  t34 = t11 / t32
  t37 = t29 * t5 * t30 * t34 / 0.18e2
  t38 = 0.135e1 <= t37
  t39 = 0.135e1 < t37
  t40 = f.my_piecewise3(t39, t37, 0.135e1)
  t41 = t40 ** 2
  t44 = t41 ** 2
  t45 = 0.1e1 / t44
  t47 = t44 * t41
  t48 = 0.1e1 / t47
  t50 = t44 ** 2
  t51 = 0.1e1 / t50
  t54 = 0.1e1 / t50 / t41
  t57 = 0.1e1 / t50 / t44
  t60 = 0.1e1 / t50 / t47
  t62 = t50 ** 2
  t63 = 0.1e1 / t62
  t66 = f.my_piecewise3(t39, 0.135e1, t37)
  t67 = jnp.sqrt(jnp.pi)
  t68 = 0.1e1 / t66
  t70 = jnp.erf(t68 / 0.2e1)
  t72 = t66 ** 2
  t73 = 0.1e1 / t72
  t75 = jnp.exp(-t73 / 0.4e1)
  t76 = t75 - 0.1e1
  t79 = t75 - 0.3e1 / 0.2e1 - 0.2e1 * t72 * t76
  t82 = 0.2e1 * t66 * t79 + t67 * t70
  t86 = f.my_piecewise3(t38, 0.1e1 / t41 / 0.36e2 - t45 / 0.960e3 + t48 / 0.26880e5 - t51 / 0.829440e6 + t54 / 0.28385280e8 - t57 / 0.1073479680e10 + t60 / 0.44590694400e11 - t63 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t66 * t82)
  t88 = params.c_x[1]
  t89 = t88 * s0
  t90 = t11 ** 2
  t91 = t90 * t23
  t92 = s0 * t90
  t93 = t92 * t23
  t95 = 0.1e1 + 0.4e-2 * t93
  t96 = 0.1e1 / t95
  t100 = params.c_x[2]
  t101 = 6 ** (0.1e1 / 0.3e1)
  t102 = t101 ** 2
  t103 = jnp.pi ** 2
  t104 = t103 ** (0.1e1 / 0.3e1)
  t105 = t104 ** 2
  t106 = t102 * t105
  t107 = 0.3e1 / 0.10e2 * t106
  t108 = tau0 * t90
  t110 = 0.1e1 / t21 / r0
  t111 = t108 * t110
  t112 = t107 - t111
  t113 = t100 * t112
  t114 = t107 + t111
  t115 = 0.1e1 / t114
  t117 = params.c_x[0] + 0.4e-2 * t89 * t91 * t96 + t113 * t115
  t118 = t86 * t117
  t122 = t18 * t110
  t123 = t41 * t40
  t124 = 0.1e1 / t123
  t126 = 0.1e1 / t20 / r0
  t130 = t29 * t5 * t126 * t34 / 0.54e2
  t131 = f.my_piecewise3(t39, -t130, 0)
  t134 = t44 * t40
  t135 = 0.1e1 / t134
  t138 = t44 * t123
  t139 = 0.1e1 / t138
  t143 = 0.1e1 / t50 / t40
  t147 = 0.1e1 / t50 / t123
  t151 = 0.1e1 / t50 / t134
  t155 = 0.1e1 / t50 / t138
  t159 = 0.1e1 / t62 / t40
  t163 = f.my_piecewise3(t39, 0, -t130)
  t165 = t75 * t73
  t169 = t72 * t66
  t170 = 0.1e1 / t169
  t174 = t66 * t76
  t179 = t170 * t163 * t75 / 0.2e1 - 0.4e1 * t174 * t163 - t68 * t163 * t75
  t182 = -t165 * t163 + 0.2e1 * t163 * t79 + 0.2e1 * t66 * t179
  t186 = f.my_piecewise3(t38, -t124 * t131 / 0.18e2 + t135 * t131 / 0.240e3 - t139 * t131 / 0.4480e4 + t143 * t131 / 0.103680e6 - t147 * t131 / 0.2838528e7 + t151 * t131 / 0.89456640e8 - t155 * t131 / 0.3185049600e10 + t159 * t131 / 0.126340300800e12, -0.8e1 / 0.3e1 * t163 * t82 - 0.8e1 / 0.3e1 * t66 * t182)
  t187 = t186 * t117
  t191 = t19 * r0
  t193 = 0.1e1 / t21 / t191
  t194 = t90 * t193
  t198 = s0 ** 2
  t199 = t88 * t198
  t200 = t19 ** 2
  t201 = t200 * t19
  t203 = 0.1e1 / t20 / t201
  t204 = t11 * t203
  t205 = t95 ** 2
  t206 = 0.1e1 / t205
  t210 = t100 * tau0
  t211 = t91 * t115
  t214 = t114 ** 2
  t215 = 0.1e1 / t214
  t216 = t113 * t215
  t217 = t108 * t23
  t220 = -0.10666666666666666666666666666666666666666666666667e-1 * t89 * t194 * t96 + 0.85333333333333333333333333333333333333333333333336e-4 * t199 * t204 * t206 + 0.5e1 / 0.3e1 * t210 * t211 + 0.5e1 / 0.3e1 * t216 * t217
  t221 = t86 * t220
  t225 = 0.1e1 / t21
  t226 = t18 * t225
  t227 = t131 ** 2
  t231 = 0.1e1 / t20 / t19
  t235 = 0.2e1 / 0.81e2 * t29 * t5 * t231 * t34
  t236 = f.my_piecewise3(t39, t235, 0)
  t264 = 0.1e1 / t62 / t41
  t269 = t45 * t227 / 0.6e1 - t124 * t236 / 0.18e2 - t48 * t227 / 0.48e2 + t135 * t236 / 0.240e3 + t51 * t227 / 0.640e3 - t139 * t236 / 0.4480e4 - t54 * t227 / 0.11520e5 + t143 * t236 / 0.103680e6 + t57 * t227 / 0.258048e6 - t147 * t236 / 0.2838528e7 - t60 * t227 / 0.6881280e7 + t151 * t236 / 0.89456640e8 + t63 * t227 / 0.212336640e9 - t155 * t236 / 0.3185049600e10 - t264 * t227 / 0.7431782400e10 + t159 * t236 / 0.126340300800e12
  t270 = f.my_piecewise3(t39, 0, t235)
  t275 = t72 ** 2
  t277 = 0.1e1 / t275 / t66
  t278 = t163 ** 2
  t279 = t277 * t278
  t282 = t75 * t170
  t290 = 0.1e1 / t275
  t298 = 0.1e1 / t275 / t72
  t299 = t298 * t278
  t310 = -0.2e1 * t290 * t278 * t75 + t170 * t270 * t75 / 0.2e1 + t299 * t75 / 0.4e1 - 0.4e1 * t278 * t76 - t73 * t278 * t75 - 0.4e1 * t174 * t270 - t68 * t270 * t75
  t313 = -t279 * t75 / 0.2e1 + 0.2e1 * t282 * t278 - t165 * t270 + 0.2e1 * t270 * t79 + 0.4e1 * t163 * t179 + 0.2e1 * t66 * t310
  t317 = f.my_piecewise3(t38, t269, -0.8e1 / 0.3e1 * t270 * t82 - 0.16e2 / 0.3e1 * t163 * t182 - 0.8e1 / 0.3e1 * t66 * t313)
  t318 = t317 * t117
  t322 = t186 * t220
  t327 = 0.1e1 / t21 / t200
  t328 = t90 * t327
  t332 = t200 * t191
  t334 = 0.1e1 / t20 / t332
  t335 = t11 * t334
  t339 = t198 * s0
  t340 = t88 * t339
  t341 = t200 ** 2
  t342 = t341 * t19
  t343 = 0.1e1 / t342
  t345 = 0.1e1 / t205 / t95
  t349 = t194 * t115
  t352 = tau0 ** 2
  t353 = t100 * t352
  t354 = t200 * r0
  t356 = 0.1e1 / t20 / t354
  t358 = t11 * t356 * t215
  t361 = t214 * t114
  t362 = 0.1e1 / t361
  t363 = t113 * t362
  t364 = t352 * t11
  t365 = t364 * t356
  t368 = t108 * t193
  t371 = 0.39111111111111111111111111111111111111111111111112e-1 * t89 * t328 * t96 - 0.76800000000000000000000000000000000000000000000003e-3 * t199 * t335 * t206 + 0.36408888888888888888888888888888888888888888888891e-5 * t340 * t343 * t345 - 0.40e2 / 0.9e1 * t210 * t349 + 0.100e3 / 0.9e1 * t353 * t358 + 0.100e3 / 0.9e1 * t363 * t365 - 0.40e2 / 0.9e1 * t216 * t368
  t372 = t86 * t371
  t376 = t18 * t20
  t378 = 0.1e1 / t20 / t191
  t382 = 0.14e2 / 0.243e3 * t29 * t5 * t378 * t34
  t383 = f.my_piecewise3(t39, -t382, 0)
  t400 = t227 * t131
  t411 = -t139 * t383 / 0.4480e4 + t143 * t383 / 0.103680e6 - t147 * t383 / 0.2838528e7 + t151 * t383 / 0.89456640e8 - t155 * t383 / 0.3185049600e10 + t159 * t383 / 0.126340300800e12 - t124 * t383 / 0.18e2 + t135 * t383 / 0.240e3 - 0.2e1 / 0.3e1 * t135 * t400 + t45 * t131 * t236 / 0.2e1 + t139 * t400 / 0.8e1 - t48 * t131 * t236 / 0.16e2
  t438 = 0.1e1 / t62 / t123
  t444 = -t143 * t400 / 0.80e2 + 0.3e1 / 0.640e3 * t51 * t131 * t236 + t147 * t400 / 0.1152e4 - t54 * t131 * t236 / 0.3840e4 - t151 * t400 / 0.21504e5 + t57 * t131 * t236 / 0.86016e5 + t155 * t400 / 0.491520e6 - t60 * t131 * t236 / 0.2293760e7 - t159 * t400 / 0.13271040e8 + t63 * t131 * t236 / 0.70778880e8 + t438 * t400 / 0.412876800e9 - t264 * t131 * t236 / 0.2477260800e10
  t446 = f.my_piecewise3(t39, 0, -t382)
  t453 = t278 * t163
  t457 = t277 * t163
  t458 = t75 * t270
  t461 = t275 ** 2
  t462 = 0.1e1 / t461
  t466 = t75 * t290
  t482 = t290 * t163
  t486 = 0.1e1 / t275 / t169
  t494 = t163 * t75
  t498 = 0.1e1 / t461 / t66
  t502 = t163 * t76
  t505 = t73 * t163
  t512 = 0.15e2 / 0.2e1 * t277 * t453 * t75 - 0.6e1 * t482 * t458 - 0.5e1 / 0.2e1 * t486 * t453 * t75 + t170 * t446 * t75 / 0.2e1 + 0.3e1 / 0.4e1 * t298 * t270 * t494 + t498 * t453 * t75 / 0.8e1 - 0.12e2 * t502 * t270 - 0.3e1 * t505 * t458 - 0.4e1 * t174 * t446 - t68 * t446 * t75
  t515 = 0.7e1 / 0.2e1 * t298 * t453 * t75 - 0.3e1 / 0.2e1 * t457 * t458 - t462 * t453 * t75 / 0.4e1 - 0.6e1 * t466 * t453 + 0.6e1 * t282 * t163 * t270 - t165 * t446 + 0.2e1 * t446 * t79 + 0.6e1 * t270 * t179 + 0.6e1 * t163 * t310 + 0.2e1 * t66 * t512
  t519 = f.my_piecewise3(t38, t411 + t444, -0.8e1 / 0.3e1 * t446 * t82 - 0.8e1 * t270 * t182 - 0.8e1 * t163 * t313 - 0.8e1 / 0.3e1 * t66 * t515)
  t520 = t519 * t117
  t524 = t317 * t220
  t528 = t186 * t371
  t533 = 0.1e1 / t21 / t354
  t534 = t90 * t533
  t539 = 0.1e1 / t20 / t341
  t540 = t11 * t539
  t544 = t341 * t191
  t545 = 0.1e1 / t544
  t549 = t198 ** 2
  t550 = t88 * t549
  t551 = t341 * t354
  t553 = 0.1e1 / t21 / t551
  t554 = t205 ** 2
  t555 = 0.1e1 / t554
  t560 = t328 * t115
  t563 = t204 * t215
  t566 = t352 * tau0
  t567 = t100 * t566
  t568 = 0.1e1 / t341
  t569 = t568 * t362
  t572 = t214 ** 2
  t573 = 0.1e1 / t572
  t574 = t573 * t566
  t575 = t574 * t568
  t578 = t364 * t203
  t581 = t108 * t327
  t584 = -0.18251851851851851851851851851851851851851851851852e0 * t89 * t534 * t96 + 0.64663703703703703703703703703703703703703703703706e-2 * t199 * t540 * t206 - 0.69176888888888888888888888888888888888888888888893e-4 * t340 * t545 * t345 + 0.11650844444444444444444444444444444444444444444445e-6 * t550 * t553 * t555 * t90 + 0.440e3 / 0.27e2 * t210 * t560 - 0.800e3 / 0.9e1 * t353 * t563 + 0.1000e4 / 0.9e1 * t567 * t569 + 0.1000e4 / 0.9e1 * t113 * t575 - 0.800e3 / 0.9e1 * t363 * t578 + 0.440e3 / 0.27e2 * t216 * t581
  t585 = t86 * t584
  t590 = f.my_piecewise3(t4, 0, -0.5e1 / 0.288e3 * t13 * t24 * t118 + t13 * t122 * t187 / 0.32e2 + t13 * t122 * t221 / 0.32e2 - 0.3e1 / 0.64e2 * t13 * t226 * t318 - 0.3e1 / 0.32e2 * t13 * t226 * t322 - 0.3e1 / 0.64e2 * t13 * t226 * t372 - 0.3e1 / 0.64e2 * t13 * t376 * t520 - 0.9e1 / 0.64e2 * t13 * t376 * t524 - 0.9e1 / 0.64e2 * t13 * t376 * t528 - 0.3e1 / 0.64e2 * t13 * t376 * t585)
  t592 = f.my_piecewise3(t3, f.p.zeta_threshold, 1)
  t594 = f.my_piecewise3(0.0e0 <= f.p.zeta_threshold, t16, 0)
  t598 = 0.1e1 / (0.2e1 * t11 - 0.2e1)
  t599 = (t18 + t594 - 0.2e1) * t598
  t600 = t8 * t10
  t601 = t599 * t600
  t602 = t231 * t11
  t604 = f.my_piecewise3(t3, 0.1e1 / t15, 1)
  t605 = t602 * t604
  t608 = t600 * t30 * t11 * t604
  t609 = jnp.sqrt(t608)
  t612 = t608 ** 0.15e1
  t614 = t5 ** 2
  t615 = t614 * t27
  t616 = t615 * t9
  t618 = t604 ** 2
  t620 = t616 * t225 * t90 * t618
  t622 = 0.51785000000000000000000000000000000000000000000000e1 * t609 + 0.90577500000000000000000000000000000000000000000000e0 * t608 + 0.11003250000000000000000000000000000000000000000000e0 * t612 + 0.12417750000000000000000000000000000000000000000000e0 * t620
  t623 = t622 ** 2
  t624 = 0.1e1 / t623
  t627 = 0.1e1 / t609 * t5 * t7
  t628 = t10 * t126
  t629 = t11 * t604
  t630 = t628 * t629
  t631 = t627 * t630
  t633 = t126 * t11
  t634 = t633 * t604
  t635 = t600 * t634
  t637 = t608 ** 0.5e0
  t639 = t637 * t5 * t7
  t640 = t639 * t630
  t644 = t616 * t110 * t90 * t618
  t646 = -0.86308333333333333333333333333333333333333333333334e0 * t631 - 0.30192500000000000000000000000000000000000000000000e0 * t635 - 0.55016250000000000000000000000000000000000000000000e-1 * t640 - 0.82785000000000000000000000000000000000000000000000e-1 * t644
  t650 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t622
  t651 = 0.1e1 / t650
  t652 = t624 * t646 * t651
  t659 = 0.1e1 / t609 / t608 * t614 * t27
  t660 = t9 * t23
  t661 = t90 * t618
  t662 = t660 * t661
  t663 = t659 * t662
  t665 = t10 * t231
  t666 = t665 * t629
  t667 = t627 * t666
  t669 = t600 * t605
  t671 = t608 ** (-0.5e0)
  t673 = t671 * t614 * t27
  t674 = t673 * t662
  t676 = t639 * t666
  t679 = t616 * t91 * t618
  t681 = -0.57538888888888888888888888888888888888888888888889e0 * t663 + 0.11507777777777777777777777777777777777777777777778e1 * t667 + 0.40256666666666666666666666666666666666666666666667e0 * t669 + 0.36677500000000000000000000000000000000000000000000e-1 * t674 + 0.73355000000000000000000000000000000000000000000000e-1 * t676 + 0.13797500000000000000000000000000000000000000000000e0 * t679
  t683 = t624 * t681 * t651
  t687 = t623 ** 2
  t688 = 0.1e1 / t687
  t689 = t646 ** 2
  t690 = t688 * t689
  t691 = t650 ** 2
  t692 = 0.1e1 / t691
  t693 = t690 * t692
  t697 = t623 * t622
  t698 = 0.1e1 / t697
  t700 = t698 * t689 * t651
  t704 = t599 * t8
  t705 = t10 * t378
  t706 = jnp.log(t650)
  t707 = t629 * t706
  t711 = t8 * t628
  t716 = 0.37978500000000000000000000000000000000000000000000e1 * t609 + 0.89690000000000000000000000000000000000000000000000e0 * t608 + 0.20477500000000000000000000000000000000000000000000e0 * t612 + 0.12323500000000000000000000000000000000000000000000e0 * t620
  t717 = t716 ** 2
  t718 = t717 * t716
  t719 = 0.1e1 / t718
  t724 = -0.63297500000000000000000000000000000000000000000000e0 * t631 - 0.29896666666666666666666666666666666666666666666667e0 * t635 - 0.10238750000000000000000000000000000000000000000000e0 * t640 - 0.82156666666666666666666666666666666666666666666667e-1 * t644
  t725 = t724 ** 2
  t729 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t716
  t730 = 0.1e1 / t729
  t732 = t629 * t719 * t725 * t730
  t734 = 0.10685000000000000000000000000000000000000000000000e0 * t711 * t732
  t736 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t608
  t737 = t599 * t736
  t739 = 0.1e1 / t687 / t623
  t740 = t689 * t646
  t743 = 0.1e1 / t691 / t650
  t744 = t739 * t740 * t743
  t748 = 0.1e1 / t687 / t622
  t750 = t748 * t740 * t692
  t756 = 0.1e1 / t609 / t620 * t6 / 0.4e1
  t757 = 0.1e1 / t200
  t758 = t618 * t604
  t759 = t757 * t758
  t760 = t756 * t759
  t762 = t9 * t193
  t763 = t762 * t661
  t764 = t659 * t763
  t766 = t705 * t629
  t767 = t627 * t766
  t769 = t378 * t11
  t770 = t769 * t604
  t771 = t600 * t770
  t773 = t608 ** (-0.15e1)
  t774 = t773 * t6
  t775 = t774 * t759
  t777 = t673 * t763
  t779 = t639 * t766
  t782 = t616 * t194 * t618
  t784 = -0.69046666666666666666666666666666666666666666666667e1 * t760 + 0.23015555555555555555555555555555555555555555555556e1 * t764 - 0.26851481481481481481481481481481481481481481481482e1 * t767 - 0.93932222222222222222222222222222222222222222222223e0 * t771 + 0.14671000000000000000000000000000000000000000000000e0 * t775 - 0.14671000000000000000000000000000000000000000000000e0 * t777 - 0.17116166666666666666666666666666666666666666666667e0 * t779 - 0.36793333333333333333333333333333333333333333333333e0 * t782
  t786 = t624 * t784 * t651
  t790 = t692 * t646
  t795 = t688 * t740 * t651
  t798 = -0.21687162600603479685264135044773156662314521887420e-1 * t601 * t605 * t652 + 0.16265371950452609763948101283579867496735891415565e-1 * t601 * t634 * t683 + 0.48159733137676571081572406076840235616767705782485e0 * t601 * t634 * t693 - 0.32530743900905219527896202567159734993471782831130e-1 * t601 * t634 * t700 - 0.56968947174242584615102410102512416326352748836105e-3 * t704 * t705 * t707 + t734 - 0.10254018858216406658218194626490193680059335835414e4 * t737 * t744 + 0.10389515463408878255799889850284635099347639899143e3 * t737 * t750 - 0.58482236226346462072622386637590534819724553404280e0 * t737 * t786 - 0.51947577317044391278999449251423175496738199495715e2 * t737 * t688 * t681 * t790 - 0.35089341735807877243573431982554320891834732042568e1 * t737 * t795
  t800 = t651 * t681
  t804 = jnp.log(t729)
  t805 = t604 * t804
  t808 = 0.34450798614814814814814814814814814814814814814813e-2 * t600 * t769 * t805
  t809 = t8 * t665
  t810 = 0.1e1 / t717
  t813 = t629 * t810 * t724 * t730
  t815 = 0.71233333333333333333333333333333333333333333333331e-1 * t809 * t813
  t822 = -0.42198333333333333333333333333333333333333333333333e0 * t663 + 0.84396666666666666666666666666666666666666666666666e0 * t667 + 0.39862222222222222222222222222222222222222222222223e0 * t669 + 0.68258333333333333333333333333333333333333333333333e-1 * t674 + 0.13651666666666666666666666666666666666666666666667e0 * t676 + 0.13692777777777777777777777777777777777777777777778e0 * t679
  t825 = t629 * t810 * t822 * t730
  t827 = 0.53424999999999999999999999999999999999999999999999e-1 * t711 * t825
  t828 = t717 ** 2
  t829 = 0.1e1 / t828
  t831 = t729 ** 2
  t832 = 0.1e1 / t831
  t834 = t629 * t829 * t725 * t832
  t836 = 0.85917975471764868594145516183295969534298037676861e0 * t711 * t834
  t838 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t608
  t840 = 0.1e1 / t828 / t717
  t841 = t838 * t840
  t842 = t725 * t724
  t844 = 0.1e1 / t831 / t729
  t847 = 0.51726012919273400298984252201052768390886626637712e3 * t841 * t842 * t844
  t849 = 0.1e1 / t828 / t716
  t850 = t838 * t849
  t853 = 0.96491876992155210400537781394436278372632330568306e2 * t850 * t842 * t832
  t854 = t838 * t810
  t863 = -0.50638000000000000000000000000000000000000000000000e1 * t760 + 0.16879333333333333333333333333333333333333333333333e1 * t764 - 0.19692555555555555555555555555555555555555555555555e1 * t767 - 0.93011851851851851851851851851851851851851851851854e0 * t771 + 0.27303333333333333333333333333333333333333333333333e0 * t775 - 0.27303333333333333333333333333333333333333333333333e0 * t777 - 0.31853888888888888888888888888888888888888888888890e0 * t779 - 0.36514074074074074074074074074074074074074074074075e0 * t782
  t864 = t863 * t730
  t866 = 0.10000000000000000000000000000000000000000000000000e1 * t854 * t864
  t867 = t604 * t706
  t875 = 0.70594500000000000000000000000000000000000000000000e1 * t609 + 0.15494250000000000000000000000000000000000000000000e1 * t608 + 0.42077500000000000000000000000000000000000000000000e0 * t612 + 0.15629250000000000000000000000000000000000000000000e0 * t620
  t878 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t875
  t879 = jnp.log(t878)
  t880 = t604 * t879
  t885 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t608
  t886 = t875 ** 2
  t887 = t886 ** 2
  t889 = 0.1e1 / t887 / t886
  t890 = t885 * t889
  t895 = -0.11765750000000000000000000000000000000000000000000e1 * t631 - 0.51647500000000000000000000000000000000000000000000e0 * t635 - 0.21038750000000000000000000000000000000000000000000e0 * t640 - 0.10419500000000000000000000000000000000000000000000e0 * t644
  t896 = t895 ** 2
  t897 = t896 * t895
  t898 = t878 ** 2
  t900 = 0.1e1 / t898 / t878
  t904 = t838 * t829
  t907 = 0.60000000000000000000000000000000000000000000000000e1 * t904 * t842 * t730
  t908 = 0.1e1 / t887
  t909 = t885 * t908
  t910 = 0.1e1 / t878
  t914 = t736 * t688
  t918 = t736 * t739
  t922 = t736 * t748
  t926 = t736 * t624
  t931 = 0.1e1 / t887 / t875
  t932 = t885 * t931
  t933 = 0.1e1 / t898
  t937 = 0.1e1 / t886
  t938 = t885 * t937
  t947 = -0.94126000000000000000000000000000000000000000000000e1 * t760 + 0.31375333333333333333333333333333333333333333333334e1 * t764 - 0.36604555555555555555555555555555555555555555555556e1 * t767 - 0.16068111111111111111111111111111111111111111111111e1 * t771 + 0.56103333333333333333333333333333333333333333333332e0 * t775 - 0.56103333333333333333333333333333333333333333333332e0 * t777 - 0.65453888888888888888888888888888888888888888888890e0 * t779 - 0.46308888888888888888888888888888888888888888888888e0 * t782
  t951 = 0.56968947174242584615102410102512416326352748836105e-3 * t600 * t769 * t867 + 0.16562821945185185185185185185185185185185185185185e-2 * t600 * t769 * t880 + 0.20690405167709360119593700880421107356354650655085e4 * t890 * t897 * t900 - t907 + 0.60000000000000000000000000000000000000000000000000e1 * t909 * t897 * t910 + 0.35089341735807877243573431982554320891834732042568e1 * t914 * t740 * t651 + 0.10254018858216406658218194626490193680059335835414e4 * t918 * t740 * t743 - 0.10389515463408878255799889850284635099347639899143e3 * t922 * t740 * t692 + 0.58482236226346462072622386637590534819724553404280e0 * t926 * t784 * t651 - 0.19298375398431042080107556278887255674526466113661e3 * t932 * t897 * t933 - t847 + t853 - t866 + 0.10000000000000000000000000000000000000000000000000e1 * t938 * t947 * t910 - t734 - t815
  t954 = t629 * t908 * t896 * t933
  t959 = t629 * t937 * t895 * t910
  t968 = -0.78438333333333333333333333333333333333333333333333e0 * t663 + 0.15687666666666666666666666666666666666666666666667e1 * t667 + 0.68863333333333333333333333333333333333333333333333e0 * t669 + 0.14025833333333333333333333333333333333333333333333e0 * t674 + 0.28051666666666666666666666666666666666666666666667e0 * t676 + 0.17365833333333333333333333333333333333333333333333e0 * t679
  t971 = t629 * t937 * t968 * t910
  t974 = t838 * t719
  t975 = t724 * t730
  t976 = t975 * t822
  t978 = 0.60000000000000000000000000000000000000000000000000e1 * t974 * t976
  t980 = t822 * t832 * t724
  t982 = 0.48245938496077605200268890697218139186316165284153e2 * t904 * t980
  t983 = t886 * t875
  t984 = 0.1e1 / t983
  t985 = t885 * t984
  t986 = t895 * t910
  t987 = t986 * t968
  t991 = t968 * t933 * t895
  t994 = t736 * t698
  t995 = t646 * t651
  t996 = t995 * t681
  t999 = t681 * t692
  t1000 = t999 * t646
  t1003 = t629 * t700
  t1008 = t629 * t984 * t896 * t910
  t1011 = t629 * t652
  t1014 = t629 * t683
  t1017 = t629 * t693
  t1020 = t827 + t836 - 0.16522625736956710527585419434107305400007076070979e1 * t711 * t954 + 0.68493333333333333333333333333333333333333333333332e-1 * t809 * t959 - 0.51369999999999999999999999999999999999999999999999e-1 * t711 * t971 + t978 - t982 - 0.60000000000000000000000000000000000000000000000000e1 * t985 * t987 + 0.96491876992155210400537781394436278372632330568306e2 * t909 * t991 - 0.35089341735807877243573431982554320891834732042568e1 * t994 * t996 + 0.51947577317044391278999449251423175496738199495715e2 * t914 * t1000 - t808 + 0.32530743900905219527896202567159734993471782831130e-1 * t711 * t1003 + 0.10274000000000000000000000000000000000000000000000e0 * t711 * t1008 + 0.21687162600603479685264135044773156662314521887420e-1 * t809 * t1011 - 0.16265371950452609763948101283579867496735891415565e-1 * t711 * t1014 - 0.48159733137676571081572406076840235616767705782485e0 * t711 * t1017
  t1023 = 0.35089341735807877243573431982554320891834732042568e1 * t737 * t698 * t646 * t800 + t808 + t815 - t827 - t836 + t847 - t853 + t866 + t599 * (t951 + t1020) + t907 - t978 + t982
  t1027 = f.my_piecewise3(t4, 0, t592 * (t798 + t1023) / 0.2e1)
  t1029 = params.c_ss[1]
  t1030 = t1029 * t549
  t1032 = 0.1e1 / t21 / t342
  t1035 = 0.1e1 + 0.2e0 * t93
  t1036 = t1035 ** 2
  t1037 = t1036 ** 2
  t1038 = 0.1e1 / t1037
  t1042 = params.c_ss[2]
  t1043 = t1042 * t112
  t1045 = params.c_ss[3]
  t1046 = t112 ** 2
  t1047 = t1045 * t1046
  t1049 = params.c_ss[4]
  t1050 = t1046 ** 2
  t1051 = t1049 * t1050
  t1052 = t1051 * t573
  t1054 = t1036 * t1035
  t1055 = 0.1e1 / t1054
  t1059 = params.c_ss[0] + 0.64e-2 * t1030 * t90 * t1032 * t1038 + t1043 * t115 + t1047 * t215 + 0.32e-1 * t1052 * t339 * t568 * t1055
  t1064 = 0.14764627977777777777777777777777777777777777777777e-2 * t600 * t602 * t805
  t1066 = 0.35616666666666666666666666666666666666666666666666e-1 * t711 * t813
  t1067 = t725 * t730
  t1069 = 0.20000000000000000000000000000000000000000000000000e1 * t974 * t1067
  t1072 = 0.10000000000000000000000000000000000000000000000000e1 * t854 * t822 * t730
  t1073 = t725 * t832
  t1075 = 0.16081979498692535066756296899072713062105388428051e2 * t904 * t1073
  t1081 = t896 * t910
  t1087 = t896 * t933
  t1095 = t689 * t651
  t1103 = -0.70983522622222222222222222222222222222222222222221e-3 * t600 * t602 * t880 - 0.34246666666666666666666666666666666666666666666666e-1 * t711 * t959 - 0.20000000000000000000000000000000000000000000000000e1 * t985 * t1081 + 0.10000000000000000000000000000000000000000000000000e1 * t938 * t968 * t910 + 0.32163958997385070133512593798145426124210776856102e2 * t909 * t1087 + t1064 + t1066 + t1069 - t1072 - t1075 - 0.24415263074675393406472461472505321282722606644045e-3 * t600 * t602 * t867 - 0.10843581300301739842632067522386578331157260943710e-1 * t711 * t1011 - 0.11696447245269292414524477327518106963944910680856e1 * t994 * t1095 + 0.58482236226346462072622386637590534819724553404280e0 * t926 * t800 + 0.17315859105681463759666483083807725165579399831905e2 * t914 * t689 * t692
  t1117 = -t1064 - t1066 - t1069 + t1072 + t1075 + t599 * t1103 + 0.24415263074675393406472461472505321282722606644045e-3 * t704 * t665 * t707 + 0.10843581300301739842632067522386578331157260943710e-1 * t601 * t634 * t652 + 0.11696447245269292414524477327518106963944910680856e1 * t737 * t700 - 0.58482236226346462072622386637590534819724553404280e0 * t737 * t683 - 0.17315859105681463759666483083807725165579399831905e2 * t737 * t693
  t1120 = f.my_piecewise3(t4, 0, t592 * t1117 / 0.2e1)
  t1122 = 0.1e1 / t21 / t544
  t1127 = t549 * s0
  t1128 = t1029 * t1127
  t1129 = t341 * t201
  t1131 = 0.1e1 / t20 / t1129
  t1134 = 0.1e1 / t1037 / t1035
  t1138 = t1042 * tau0
  t1141 = t1043 * t215
  t1144 = t1045 * t112
  t1145 = t1144 * t215
  t1148 = t1047 * t362
  t1152 = t1049 * t1046 * t112
  t1153 = t573 * t339
  t1154 = t1152 * t1153
  t1156 = t1032 * t1055 * t108
  t1160 = 0.1e1 / t572 / t114
  t1161 = t1160 * t339
  t1162 = t1051 * t1161
  t1165 = t341 * r0
  t1166 = 0.1e1 / t1165
  t1172 = t1038 * t90
  t1176 = -0.68266666666666666666666666666666666666666666666667e-1 * t1030 * t90 * t1122 * t1038 + 0.27306666666666666666666666666666666666666666666668e-1 * t1128 * t11 * t1131 * t1134 + 0.5e1 / 0.3e1 * t1138 * t211 + 0.5e1 / 0.3e1 * t1141 * t217 + 0.10e2 / 0.3e1 * t1145 * t217 + 0.10e2 / 0.3e1 * t1148 * t217 + 0.21333333333333333333333333333333333333333333333333e0 * t1154 * t1156 + 0.21333333333333333333333333333333333333333333333333e0 * t1162 * t1156 - 0.256e0 * t1052 * t339 * t1166 * t1055 + 0.51200000000000000000000000000000000000000000000000e-1 * t1052 * t549 * t1122 * t1172
  t1181 = 0.11073470983333333333333333333333333333333333333333e-2 * t600 * t633 * t805
  t1183 = 0.10000000000000000000000000000000000000000000000000e1 * t854 * t975
  t1204 = f.my_piecewise3(t4, 0, t592 * (t1181 + t1183 + t599 * (0.53237641966666666666666666666666666666666666666666e-3 * t600 * t633 * t880 + 0.10000000000000000000000000000000000000000000000000e1 * t938 * t986 - t1181 - t1183 + 0.18311447306006545054854346104378990962041954983034e-3 * t600 * t633 * t867 + 0.58482236226346462072622386637590534819724553404280e0 * t926 * t995) - 0.18311447306006545054854346104378990962041954983034e-3 * t704 * t628 * t707 - 0.58482236226346462072622386637590534819724553404280e0 * t737 * t652) / 0.2e1)
  t1206 = 0.1e1 / t572 / t214
  t1207 = t1206 * t339
  t1208 = t1051 * t1207
  t1212 = 0.1e1 / t20 / t551 * t1055 * t364
  t1215 = t1160 * t549
  t1216 = t1051 * t1215
  t1218 = tau0 * t11
  t1219 = t1131 * t1038 * t1218
  t1222 = t1049 * t1046
  t1223 = t1222 * t1153
  t1226 = t1152 * t1161
  t1229 = t573 * t549
  t1230 = t1152 * t1229
  t1233 = t341 * t200
  t1235 = 0.1e1 / t21 / t1233
  t1242 = t1043 * t362
  t1245 = t1144 * t362
  t1248 = t1047 * t573
  t1253 = 0.35555555555555555555555555555555555555555555555555e1 * t1208 * t1212 + 0.13653333333333333333333333333333333333333333333333e1 * t1216 * t1219 + 0.21333333333333333333333333333333333333333333333333e1 * t1223 * t1212 + 0.56888888888888888888888888888888888888888888888888e1 * t1226 * t1212 + 0.13653333333333333333333333333333333333333333333333e1 * t1230 * t1219 + 0.79644444444444444444444444444444444444444444444445e0 * t1030 * t90 * t1235 * t1038 - 0.40e2 / 0.9e1 * t1138 * t349 + 0.100e3 / 0.9e1 * t1242 * t365 + 0.400e3 / 0.9e1 * t1245 * t365 + 0.100e3 / 0.3e1 * t1248 * t365 - 0.40e2 / 0.9e1 * t1141 * t368
  t1258 = t339 * t343
  t1268 = 0.1e1 / t20 / t341 / t332
  t1270 = t1134 * t11
  t1274 = t1042 * t352
  t1277 = t1045 * t352
  t1284 = t549 * t198
  t1285 = t1029 * t1284
  t1286 = t341 ** 2
  t1287 = t1286 * t19
  t1288 = 0.1e1 / t1287
  t1290 = 0.1e1 / t1037 / t1036
  t1295 = t1122 * t1055 * t108
  t1300 = -0.80e2 / 0.9e1 * t1145 * t368 - 0.80e2 / 0.9e1 * t1148 * t368 + 0.2304e1 * t1052 * t1258 * t1055 - 0.10069333333333333333333333333333333333333333333333e1 * t1052 * t549 * t1235 * t1172 + 0.21845333333333333333333333333333333333333333333334e0 * t1052 * t1127 * t1268 * t1270 + 0.100e3 / 0.9e1 * t1274 * t358 + 0.100e3 / 0.9e1 * t1277 * t358 - 0.68266666666666666666666666666666666666666666666669e0 * t1128 * t11 * t1268 * t1134 + 0.14563555555555555555555555555555555555555555555557e0 * t1285 * t1288 * t1290 - 0.39822222222222222222222222222222222222222222222222e1 * t1162 * t1295 - 0.39822222222222222222222222222222222222222222222222e1 * t1154 * t1295
  t1301 = t1253 + t1300
  t1305 = 0.621814e-1 * t838 * t804
  t1308 = t736 * t706
  t1317 = f.my_piecewise3(t4, 0, t592 * (-t1305 + t599 * (-0.3109070e-1 * t885 * t879 + t1305 - 0.19751673498613801407483339618206552048944131217655e-1 * t1308) + 0.19751673498613801407483339618206552048944131217655e-1 * t599 * t1308) / 0.2e1)
  t1318 = t549 * t553
  t1323 = 0.1e1 / t20 / t1286
  t1328 = t1152 * t1206
  t1331 = t1055 * t566
  t1332 = t339 / t1286 * t1331
  t1336 = 0.1e1 / t572 / t361
  t1337 = t1051 * t1336
  t1340 = t1051 * t1206
  t1341 = t1286 * r0
  t1342 = 0.1e1 / t1341
  t1344 = t1038 * t352
  t1345 = t549 * t1342 * t1344
  t1348 = t1152 * t1160
  t1351 = t1051 * t1160
  t1353 = t1134 * tau0
  t1354 = t1127 * t1288 * t1353
  t1357 = t1049 * t112
  t1358 = t1357 * t573
  t1361 = t1222 * t1160
  t1364 = t1222 * t573
  t1367 = t1152 * t573
  t1370 = t1042 * t566
  t1373 = t1045 * t566
  t1376 = t1286 * t191
  t1377 = 0.1e1 / t1376
  t1381 = t549 * t339
  t1382 = t1029 * t1381
  t1385 = 0.1e1 / t21 / t1286 / t354
  t1387 = 0.1e1 / t1037 / t1054
  t1402 = 0.16440888888888888888888888888888888888888888888889e2 * t1052 * t1318 * t1172 - 0.76458666666666666666666666666666666666666666666668e1 * t1052 * t1127 * t1323 * t1270 + 0.14222222222222222222222222222222222222222222222222e3 * t1328 * t1332 + 0.71111111111111111111111111111111111111111111111110e2 * t1337 * t1332 + 0.34133333333333333333333333333333333333333333333333e2 * t1340 * t1345 + 0.54613333333333333333333333333333333333333333333333e2 * t1348 * t1345 + 0.87381333333333333333333333333333333333333333333335e1 * t1351 * t1354 + 0.14222222222222222222222222222222222222222222222222e2 * t1358 * t1332 + 0.85333333333333333333333333333333333333333333333332e2 * t1361 * t1332 + 0.20480000000000000000000000000000000000000000000000e2 * t1364 * t1345 + 0.87381333333333333333333333333333333333333333333335e1 * t1367 * t1354 + 0.1000e4 / 0.9e1 * t1370 * t569 + 0.2000e4 / 0.9e1 * t1373 * t569 - 0.62623288888888888888888888888888888888888888888894e1 * t1285 * t1377 * t1290 + 0.46603377777777777777777777777777777777777777777782e0 * t1382 * t1385 * t1387 * t90 + 0.13865718518518518518518518518518518518518518518519e2 * t1128 * t11 * t1323 * t1134 - 0.800e3 / 0.9e1 * t1274 * t563 + 0.1000e4 / 0.9e1 * t1043 * t575 + 0.2000e4 / 0.3e1 * t1144 * t575
  t1403 = t1160 * t566
  t1427 = t339 * t545
  t1436 = t1131 * t1055 * t364
  t1440 = t1268 * t1038 * t1218
  t1450 = t1235 * t1055 * t108
  t1455 = 0.4000e4 / 0.9e1 * t1047 * t1403 * t568 - 0.800e3 / 0.9e1 * t1277 * t563 - 0.10088296296296296296296296296296296296296296296296e2 * t1030 * t90 * t553 * t1038 + 0.440e3 / 0.27e2 * t1138 * t560 + 0.11650844444444444444444444444444444444444444444445e1 * t1052 * t1284 * t1377 * t1290 - 0.800e3 / 0.3e1 * t1248 * t578 + 0.440e3 / 0.27e2 * t1141 * t581 + 0.880e3 / 0.27e2 * t1145 * t581 + 0.880e3 / 0.27e2 * t1148 * t581 - 0.23040e2 * t1052 * t1427 * t1055 - 0.800e3 / 0.9e1 * t1242 * t578 - 0.3200e4 / 0.9e1 * t1245 * t578 - 0.11377777777777777777777777777777777777777777777778e3 * t1208 * t1436 - 0.45738666666666666666666666666666666666666666666665e2 * t1216 * t1440 - 0.68266666666666666666666666666666666666666666666666e2 * t1223 * t1436 - 0.18204444444444444444444444444444444444444444444445e3 * t1226 * t1436 - 0.45738666666666666666666666666666666666666666666665e2 * t1230 * t1440 + 0.61819259259259259259259259259259259259259259259259e2 * t1154 * t1450 + 0.61819259259259259259259259259259259259259259259259e2 * t1162 * t1450
  t1456 = t1402 + t1455
  t1459 = f.my_piecewise3(t3, t16, 1)
  t1462 = (0.2e1 * t1459 - 0.2e1) * t598
  t1463 = t1462 * t8
  t1465 = t8 * t10 * t30
  t1466 = jnp.sqrt(t1465)
  t1469 = t1465 ** 0.15e1
  t1472 = t615 * t9 * t225
  t1474 = 0.51785000000000000000000000000000000000000000000000e1 * t1466 + 0.90577500000000000000000000000000000000000000000000e0 * t1465 + 0.11003250000000000000000000000000000000000000000000e0 * t1469 + 0.12417750000000000000000000000000000000000000000000e0 * t1472
  t1475 = t1474 ** 2
  t1476 = t1475 * t1474
  t1477 = 0.1e1 / t1476
  t1479 = 0.1e1 / t1466 * t5
  t1480 = t7 * t10
  t1481 = t1480 * t126
  t1482 = t1479 * t1481
  t1485 = t1465 ** 0.5e0
  t1486 = t1485 * t5
  t1487 = t1486 * t1481
  t1490 = t615 * t9 * t110
  t1492 = -0.86308333333333333333333333333333333333333333333334e0 * t1482 - 0.30192500000000000000000000000000000000000000000000e0 * t711 - 0.55016250000000000000000000000000000000000000000000e-1 * t1487 - 0.82785000000000000000000000000000000000000000000000e-1 * t1490
  t1493 = t1492 ** 2
  t1497 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t1474
  t1498 = 0.1e1 / t1497
  t1499 = t1477 * t1493 * t1498
  t1504 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t1465
  t1509 = 0.37978500000000000000000000000000000000000000000000e1 * t1466 + 0.89690000000000000000000000000000000000000000000000e0 * t1465 + 0.20477500000000000000000000000000000000000000000000e0 * t1469 + 0.12323500000000000000000000000000000000000000000000e0 * t1472
  t1510 = t1509 ** 2
  t1511 = t1510 ** 2
  t1512 = 0.1e1 / t1511
  t1513 = t1504 * t1512
  t1516 = 0.1e1 / t1466 / t1465 * t614
  t1517 = t27 * t9
  t1518 = t1517 * t23
  t1519 = t1516 * t1518
  t1521 = t1480 * t231
  t1522 = t1479 * t1521
  t1525 = t1465 ** (-0.5e0)
  t1526 = t1525 * t614
  t1527 = t1526 * t1518
  t1529 = t1486 * t1521
  t1531 = t615 * t660
  t1533 = -0.42198333333333333333333333333333333333333333333333e0 * t1519 + 0.84396666666666666666666666666666666666666666666666e0 * t1522 + 0.39862222222222222222222222222222222222222222222223e0 * t809 + 0.68258333333333333333333333333333333333333333333333e-1 * t1527 + 0.13651666666666666666666666666666666666666666666667e0 * t1529 + 0.13692777777777777777777777777777777777777777777778e0 * t1531
  t1536 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t1509
  t1537 = t1536 ** 2
  t1538 = 0.1e1 / t1537
  t1539 = t1533 * t1538
  t1544 = -0.63297500000000000000000000000000000000000000000000e0 * t1482 - 0.29896666666666666666666666666666666666666666666667e0 * t711 - 0.10238750000000000000000000000000000000000000000000e0 * t1487 - 0.82156666666666666666666666666666666666666666666667e-1 * t1490
  t1548 = t1544 ** 2
  t1549 = t1548 * t1544
  t1550 = 0.1e1 / t1536
  t1551 = t1549 * t1550
  t1554 = t1510 * t1509
  t1555 = 0.1e1 / t1554
  t1556 = t1504 * t1555
  t1557 = t1544 * t1550
  t1561 = jnp.log(t1536)
  t1566 = 0.1e1 / t1511 / t1510
  t1567 = t1504 * t1566
  t1569 = 0.1e1 / t1537 / t1536
  t1570 = t1549 * t1569
  t1574 = 0.1e1 / t1511 / t1509
  t1575 = t1504 * t1574
  t1576 = t1549 * t1538
  t1579 = 0.1e1 / t1510
  t1580 = t1504 * t1579
  t1584 = 0.1e1 / t1466 / t1472 * t6 / 0.4e1
  t1585 = t1584 * t757
  t1587 = t1517 * t193
  t1588 = t1516 * t1587
  t1590 = t1480 * t378
  t1591 = t1479 * t1590
  t1593 = t8 * t705
  t1595 = t1465 ** (-0.15e1)
  t1596 = t1595 * t6
  t1597 = t1596 * t757
  t1599 = t1526 * t1587
  t1601 = t1486 * t1590
  t1603 = t615 * t762
  t1605 = -0.25319000000000000000000000000000000000000000000000e1 * t1585 + 0.16879333333333333333333333333333333333333333333333e1 * t1588 - 0.19692555555555555555555555555555555555555555555555e1 * t1591 - 0.93011851851851851851851851851851851851851851851854e0 * t1593 + 0.13651666666666666666666666666666666666666666666667e0 * t1597 - 0.27303333333333333333333333333333333333333333333333e0 * t1599 - 0.31853888888888888888888888888888888888888888888890e0 * t1601 - 0.36514074074074074074074074074074074074074074074075e0 * t1603
  t1606 = t1605 * t1550
  t1611 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t1465
  t1612 = t1462 * t1611
  t1613 = t1475 ** 2
  t1615 = 0.1e1 / t1613 / t1475
  t1616 = t1493 * t1492
  t1618 = t1497 ** 2
  t1620 = 0.1e1 / t1618 / t1497
  t1621 = t1615 * t1616 * t1620
  t1625 = 0.1e1 / t1613 / t1474
  t1627 = 0.1e1 / t1618
  t1628 = t1625 * t1616 * t1627
  t1631 = -0.32530743900905219527896202567159734993471782831130e-1 * t1463 * t628 * t1499 + 0.48245938496077605200268890697218139186316165284153e2 * t1513 * t1539 * t1544 + 0.60000000000000000000000000000000000000000000000000e1 * t1513 * t1551 - 0.60000000000000000000000000000000000000000000000000e1 * t1556 * t1557 * t1533 + 0.34450798614814814814814814814814814814814814814813e-2 * t8 * t705 * t1561 + 0.51726012919273400298984252201052768390886626637712e3 * t1567 * t1570 - 0.96491876992155210400537781394436278372632330568306e2 * t1575 * t1576 + 0.10000000000000000000000000000000000000000000000000e1 * t1580 * t1606 - 0.2e1 * t1027 - 0.10254018858216406658218194626490193680059335835414e4 * t1612 * t1621 + 0.10389515463408878255799889850284635099347639899143e3 * t1612 * t1628
  t1632 = 0.1e1 / t1475
  t1641 = -0.34523333333333333333333333333333333333333333333333e1 * t1585 + 0.23015555555555555555555555555555555555555555555556e1 * t1588 - 0.26851481481481481481481481481481481481481481481482e1 * t1591 - 0.93932222222222222222222222222222222222222222222223e0 * t1593 + 0.73355000000000000000000000000000000000000000000000e-1 * t1597 - 0.14671000000000000000000000000000000000000000000000e0 * t1599 - 0.17116166666666666666666666666666666666666666666667e0 * t1601 - 0.36793333333333333333333333333333333333333333333333e0 * t1603
  t1643 = t1632 * t1641 * t1498
  t1646 = 0.1e1 / t1613
  t1653 = -0.57538888888888888888888888888888888888888888888889e0 * t1519 + 0.11507777777777777777777777777777777777777777777778e1 * t1522 + 0.40256666666666666666666666666666666666666666666667e0 * t809 + 0.36677500000000000000000000000000000000000000000000e-1 * t1527 + 0.73355000000000000000000000000000000000000000000000e-1 * t1529 + 0.13797500000000000000000000000000000000000000000000e0 * t1531
  t1655 = t1627 * t1492
  t1660 = t1646 * t1616 * t1498
  t1664 = t1498 * t1653
  t1668 = t231 * t1579
  t1672 = t126 * t1579
  t1673 = t1533 * t1550
  t1677 = t126 * t1512
  t1678 = t1548 * t1538
  t1683 = t1632 * t1492 * t1498
  t1688 = t1632 * t1653 * t1498
  t1692 = t1646 * t1493
  t1693 = t1692 * t1627
  t1698 = t1548 * t1550
  t1702 = t1462 * t5
  t1703 = jnp.log(t1497)
  t1708 = -0.58482236226346462072622386637590534819724553404280e0 * t1612 * t1643 - 0.51947577317044391278999449251423175496738199495715e2 * t1612 * t1646 * t1653 * t1655 - 0.35089341735807877243573431982554320891834732042568e1 * t1612 * t1660 + 0.35089341735807877243573431982554320891834732042568e1 * t1612 * t1477 * t1492 * t1664 + 0.71233333333333333333333333333333333333333333333331e-1 * t600 * t1668 * t1557 - 0.53424999999999999999999999999999999999999999999999e-1 * t600 * t1672 * t1673 - 0.85917975471764868594145516183295969534298037676861e0 * t600 * t1677 * t1678 - 0.21687162600603479685264135044773156662314521887420e-1 * t1463 * t665 * t1683 + 0.16265371950452609763948101283579867496735891415565e-1 * t1463 * t628 * t1688 + 0.48159733137676571081572406076840235616767705782485e0 * t1463 * t628 * t1693 + 0.10685000000000000000000000000000000000000000000000e0 * t600 * t126 * t1555 * t1698 - 0.56968947174242584615102410102512416326352748836105e-3 * t1702 * t1480 * t378 * t1703
  t1709 = t1631 + t1708
  t1711 = params.c_os[1]
  t1713 = 0.3e1 / 0.5e1 * t106 * t111
  t1715 = 0.4e1 * t364 * t378
  t1716 = t1713 - t1715
  t1717 = t1711 * t1716
  t1718 = t1713 + t1715
  t1719 = 0.1e1 / t1718
  t1721 = params.c_os[2]
  t1722 = t1716 ** 2
  t1723 = t1721 * t1722
  t1724 = t1718 ** 2
  t1725 = 0.1e1 / t1724
  t1727 = params.c_os[3]
  t1728 = t1727 * t1722
  t1729 = t1728 * t1725
  t1731 = 0.1e1 + 0.6e-2 * t93
  t1732 = 0.1e1 / t1731
  t1733 = t23 * t1732
  t1734 = t92 * t1733
  t1737 = params.c_os[4]
  t1738 = t1722 ** 2
  t1739 = t1738 * t1722
  t1740 = t1737 * t1739
  t1741 = t1724 ** 2
  t1743 = 0.1e1 / t1741 / t1724
  t1745 = params.c_os[5]
  t1746 = t1745 * t1739
  t1747 = t1746 * t1743
  t1750 = params.c_os[0] + t1717 * t1719 + t1723 * t1725 + 0.6e-2 * t1729 * t1734 + t1740 * t1743 + 0.6e-2 * t1747 * t1734
  t1779 = -0.14764627977777777777777777777777777777777777777777e-2 * t8 * t665 * t1561 - 0.35616666666666666666666666666666666666666666666666e-1 * t600 * t1672 * t1557 - 0.20000000000000000000000000000000000000000000000000e1 * t1556 * t1698 + 0.10000000000000000000000000000000000000000000000000e1 * t1580 * t1673 + 0.16081979498692535066756296899072713062105388428051e2 * t1513 * t1678 + 0.24415263074675393406472461472505321282722606644045e-3 * t1702 * t1480 * t231 * t1703 + 0.10843581300301739842632067522386578331157260943710e-1 * t1463 * t628 * t1683 + 0.11696447245269292414524477327518106963944910680856e1 * t1612 * t1499 - 0.58482236226346462072622386637590534819724553404280e0 * t1612 * t1688 - 0.17315859105681463759666483083807725165579399831905e2 * t1612 * t1693 - 0.2e1 * t1120
  t1780 = t106 * t217
  t1782 = 0.1e1 / t20 / t200
  t1784 = 0.40e2 / 0.3e1 * t364 * t1782
  t1785 = -t1780 + t1784
  t1786 = t1711 * t1785
  t1788 = -t1780 - t1784
  t1789 = t1725 * t1788
  t1791 = t1721 * t1716
  t1795 = t1724 * t1718
  t1796 = 0.1e1 / t1795
  t1797 = t1796 * t1788
  t1800 = t1727 * t1716
  t1801 = t1725 * s0
  t1802 = t1800 * t1801
  t1803 = t1732 * t1785
  t1804 = t91 * t1803
  t1807 = t1796 * s0
  t1808 = t1728 * t1807
  t1809 = t1732 * t1788
  t1810 = t91 * t1809
  t1814 = t92 * t193 * t1732
  t1817 = t198 * t11
  t1818 = t1731 ** 2
  t1819 = 0.1e1 / t1818
  t1821 = t1817 * t203 * t1819
  t1824 = t1738 * t1716
  t1825 = t1737 * t1824
  t1826 = t1743 * t1785
  t1830 = 0.1e1 / t1741 / t1795
  t1834 = t1745 * t1824
  t1835 = t1743 * s0
  t1836 = t1834 * t1835
  t1839 = t1830 * s0
  t1840 = t1746 * t1839
  t1847 = t1786 * t1719 - t1717 * t1789 + 0.2e1 * t1791 * t1725 * t1785 - 0.2e1 * t1723 * t1797 + 0.12e-1 * t1802 * t1804 - 0.12e-1 * t1808 * t1810 - 0.16000000000000000000000000000000000000000000000000e-1 * t1729 * t1814 + 0.19200000000000000000000000000000000000000000000000e-3 * t1729 * t1821 + 0.6e1 * t1825 * t1826 - 0.6e1 * t1740 * t1830 * t1788 + 0.36e-1 * t1836 * t1804 - 0.36e-1 * t1840 * t1810 - 0.16000000000000000000000000000000000000000000000000e-1 * t1747 * t1814 + 0.19200000000000000000000000000000000000000000000000e-3 * t1747 * t1821
  t1862 = 0.11073470983333333333333333333333333333333333333333e-2 * t8 * t628 * t1561 + 0.10000000000000000000000000000000000000000000000000e1 * t1580 * t1557 - 0.18311447306006545054854346104378990962041954983034e-3 * t1702 * t1480 * t126 * t1703 - 0.58482236226346462072622386637590534819724553404280e0 * t1612 * t1683 - 0.2e1 * t1204
  t1863 = t1741 ** 2
  t1864 = 0.1e1 / t1863
  t1865 = t1788 ** 2
  t1866 = t1864 * t1865
  t1869 = t1796 * t1865
  t1872 = 0.1e1 / t1741
  t1873 = t1872 * t1865
  t1876 = t1737 * t1738
  t1877 = t1785 ** 2
  t1878 = t1743 * t1877
  t1882 = 0.1e1 / t1818 / t1731
  t1883 = t1258 * t1882
  t1889 = 0.8e1 / 0.3e1 * t106 * t368
  t1890 = 0.520e3 / 0.9e1 * t365
  t1891 = t1889 - t1890
  t1892 = t1711 * t1891
  t1894 = t1721 * t1877
  t1898 = t1817 * t334 * t1819
  t1904 = t92 * t327 * t1732
  t1909 = t1727 * t1877
  t1910 = t1909 * t1725
  t1921 = t1864 * s0
  t1922 = t1746 * t1921
  t1923 = t1732 * t1865
  t1924 = t91 * t1923
  t1927 = t194 * t1809
  t1930 = t194 * t1803
  t1933 = t1872 * s0
  t1934 = t1728 * t1933
  t1937 = 0.42e2 * t1740 * t1866 + 0.2e1 * t1717 * t1869 + 0.6e1 * t1723 * t1873 + 0.30e2 * t1876 * t1878 + 0.12288000000000000000000000000000000000000000000000e-4 * t1729 * t1883 + 0.12288000000000000000000000000000000000000000000000e-4 * t1747 * t1883 + t1892 * t1719 + 0.2e1 * t1894 * t1725 - 0.17280000000000000000000000000000000000000000000000e-2 * t1747 * t1898 - 0.17280000000000000000000000000000000000000000000000e-2 * t1729 * t1898 + 0.58666666666666666666666666666666666666666666666667e-1 * t1729 * t1904 + 0.58666666666666666666666666666666666666666666666667e-1 * t1747 * t1904 + 0.12e-1 * t1910 * t1734 - 0.72e2 * t1825 * t1830 * t1785 * t1788 - 0.8e1 * t1791 * t1796 * t1785 * t1788 + 0.252e0 * t1922 * t1924 + 0.19200000000000000000000000000000000000000000000000e0 * t1840 * t1927 - 0.64000000000000000000000000000000000000000000000000e-1 * t1802 * t1930 + 0.36e-1 * t1934 * t1924
  t1938 = t1732 * t1891
  t1939 = t91 * t1938
  t1942 = t1743 * t198
  t1943 = t1834 * t1942
  t1944 = t1819 * t1785
  t1945 = t204 * t1944
  t1948 = t1889 + t1890
  t1949 = t1732 * t1948
  t1950 = t91 * t1949
  t1953 = t1830 * t198
  t1954 = t1746 * t1953
  t1955 = t1819 * t1788
  t1956 = t204 * t1955
  t1961 = t1725 * t198
  t1962 = t1800 * t1961
  t1967 = t1796 * t198
  t1968 = t1728 * t1967
  t1973 = t1745 * t1738
  t1974 = t1973 * t1835
  t1975 = t1732 * t1877
  t1981 = t1834 * t1839
  t1982 = t1803 * t1788
  t1983 = t91 * t1982
  t1986 = t1800 * t1807
  t1991 = t1725 * t1948
  t1993 = t1725 * t1891
  t1996 = t1796 * t1948
  t2002 = t1830 * t1948
  t2005 = 0.36e-1 * t1836 * t1939 + 0.23040000000000000000000000000000000000000000000000e-2 * t1943 * t1945 - 0.36e-1 * t1840 * t1950 - 0.23040000000000000000000000000000000000000000000000e-2 * t1954 * t1956 + 0.12e-1 * t1802 * t1939 + 0.76800000000000000000000000000000000000000000000000e-3 * t1962 * t1945 - 0.12e-1 * t1808 * t1950 - 0.76800000000000000000000000000000000000000000000000e-3 * t1968 * t1956 + 0.64000000000000000000000000000000000000000000000000e-1 * t1808 * t1927 + 0.180e0 * t1974 * t91 * t1975 - 0.19200000000000000000000000000000000000000000000000e0 * t1836 * t1930 - 0.432e0 * t1981 * t1983 - 0.48e-1 * t1986 * t1983 - 0.2e1 * t1786 * t1789 - t1717 * t1991 + 0.2e1 * t1791 * t1993 - 0.2e1 * t1723 * t1996 + 0.6e1 * t1825 * t1743 * t1891 - 0.6e1 * t1740 * t2002
  t2006 = t1937 + t2005
  t2015 = -0.621814e-1 * t1504 * t1561 + 0.19751673498613801407483339618206552048944131217655e-1 * t1462 * t1611 * t1703 - 0.2e1 * t1317
  t2019 = t92 * t533 * t1732
  t2026 = t1834 * t1743
  t2027 = t1882 * t1785
  t2028 = t1258 * t2027
  t2031 = t1746 * t1830
  t2032 = t1882 * t1788
  t2033 = t1258 * t2032
  t2036 = t1800 * t1725
  t2039 = t1728 * t1796
  t2042 = t1818 ** 2
  t2043 = 0.1e1 / t2042
  t2044 = t2043 * t90
  t2045 = t1318 * t2044
  t2052 = t1817 * t539 * t1819
  t2057 = t194 * t1949
  t2060 = t1872 * t198
  t2061 = t1728 * t2060
  t2062 = t1819 * t1865
  t2063 = t204 * t2062
  t2066 = t335 * t1955
  t2069 = t194 * t1923
  t2072 = t328 * t1809
  t2075 = t1722 * t1716
  t2076 = t1745 * t2075
  t2077 = t2076 * t1835
  t2078 = t1877 * t1785
  t2079 = t1732 * t2078
  t2086 = t1727 * t1785
  t2087 = t2086 * t1801
  t2091 = 0.88e2 / 0.9e1 * t106 * t581
  t2092 = 0.8320e4 / 0.27e2 * t578
  t2093 = -t2091 + t2092
  t2094 = t1732 * t2093
  t2095 = t91 * t2094
  t2098 = 0.14549333333333333333333333333333333333333333333333e-1 * t1729 * t2052 + 0.14549333333333333333333333333333333333333333333333e-1 * t1747 * t2052 + 0.96000000000000000000000000000000000000000000000000e-1 * t1808 * t2057 + 0.34560000000000000000000000000000000000000000000000e-2 * t2061 * t2063 + 0.10368000000000000000000000000000000000000000000000e-1 * t1968 * t2066 - 0.28800000000000000000000000000000000000000000000000e0 * t1934 * t2069 - 0.35200000000000000000000000000000000000000000000000e0 * t1808 * t2072 + 0.720e0 * t2077 * t91 * t2079 - 0.14400000000000000000000000000000000000000000000000e1 * t1974 * t194 * t1975 + 0.36e-1 * t2087 * t1939 + 0.12e-1 * t1802 * t2095
  t2100 = t1819 * t1891
  t2101 = t204 * t2100
  t2104 = -t2091 - t2092
  t2105 = t1732 * t2104
  t2106 = t91 * t2105
  t2109 = t1819 * t1948
  t2110 = t204 * t2109
  t2121 = t1973 * t1942
  t2122 = t1819 * t1877
  t2126 = t335 * t1944
  t2132 = t1864 * t198
  t2133 = t1746 * t2132
  t2138 = t194 * t1938
  t2145 = t1909 * t1807
  t2148 = t328 * t1803
  t2152 = 0.1e1 / t1863 / t1718
  t2153 = t2152 * s0
  t2154 = t1746 * t2153
  t2155 = t1865 * t1788
  t2156 = t1732 * t2155
  t2157 = t91 * t2156
  t2166 = 0.24192000000000000000000000000000000000000000000000e-1 * t2133 * t2063 + 0.31104000000000000000000000000000000000000000000000e-1 * t1954 * t2066 - 0.96000000000000000000000000000000000000000000000000e-1 * t1802 * t2138 - 0.10368000000000000000000000000000000000000000000000e-1 * t1962 * t2126 - 0.28800000000000000000000000000000000000000000000000e0 * t1836 * t2138 - 0.72e-1 * t2145 * t1810 + 0.10560000000000000000000000000000000000000000000000e1 * t1836 * t2148 - 0.2016e1 * t2154 * t2157 - 0.20160000000000000000000000000000000000000000000000e1 * t1922 * t2069 - 0.10560000000000000000000000000000000000000000000000e1 * t1840 * t2072 + 0.35200000000000000000000000000000000000000000000000e0 * t1802 * t2148
  t2170 = 0.1e1 / t1741 / t1718
  t2171 = t2170 * s0
  t2172 = t1728 * t2171
  t2175 = t1949 * t1785
  t2176 = t91 * t2175
  t2179 = t1949 * t1788
  t2180 = t91 * t2179
  t2183 = t194 * t1982
  t2186 = t1973 * t1839
  t2187 = t1975 * t1788
  t2193 = t1834 * t1953
  t2194 = t1944 * t1788
  t2195 = t204 * t2194
  t2202 = t1938 * t1788
  t2203 = t91 * t2202
  t2207 = t1800 * t1967
  t2210 = t1938 * t1785
  t2216 = t1834 * t1921
  t2217 = t1923 * t1785
  t2218 = t91 * t2217
  t2221 = t1800 * t1933
  t2224 = t1711 * t2093
  t2226 = t1427 * t1882
  t2233 = t1725 * t2104
  t2235 = t1721 * t1785
  t2238 = -0.46080000000000000000000000000000000000000000000000e-2 * t2207 * t2195 + 0.540e0 * t1974 * t91 * t2210 - 0.648e0 * t1981 * t2203 + 0.4536e1 * t2216 * t2218 + 0.216e0 * t2221 * t2218 + t2224 * t1719 - 0.23347200000000000000000000000000000000000000000000e-3 * t1729 * t2226 - 0.23347200000000000000000000000000000000000000000000e-3 * t1747 * t2226 - 0.3e1 * t1786 * t1991 - t1717 * t2233 + 0.6e1 * t2235 * t1993
  t2240 = t1725 * t2093
  t2243 = t1796 * t2104
  t2251 = t1830 * t2104
  t2256 = t2152 * t2155
  t2259 = t1872 * t2155
  t2262 = t2170 * t2155
  t2265 = t1737 * t2075
  t2271 = 0.6e1 * t1825 * t1743 * t2093 + 0.120e3 * t2265 * t1743 * t2078 - 0.6e1 * t1717 * t2259 - 0.2e1 * t1723 * t2243 - 0.24e2 * t1723 * t2262 - 0.6e1 * t1740 * t2251 - 0.336e3 * t1740 * t2256 + 0.6e1 * t1786 * t1869 - 0.3e1 * t1892 * t1789 + 0.2e1 * t1791 * t2240 - 0.12e2 * t1894 * t1797
  t2279 = t1797 * t1948
  t2285 = t1872 * t1788
  t2289 = t1830 * t1877
  t2296 = t1796 * t1891
  t2297 = t2296 * t1788
  t2303 = t1830 * t1891
  t2310 = 0.126e3 * t1740 * t1864 * t1948 * t1788 + 0.18e2 * t1723 * t2285 * t1948 + 0.36e2 * t1791 * t1873 * t1785 - 0.12e2 * t1791 * t1996 * t1785 + 0.756e3 * t1825 * t1866 * t1785 - 0.108e3 * t1825 * t2002 * t1785 - 0.108e3 * t1825 * t2303 * t1788 - 0.540e3 * t1876 * t2289 * t1788 + 0.90e2 * t1876 * t1826 * t1891 + 0.6e1 * t1717 * t2279 - 0.12e2 * t1791 * t2297
  t2313 = t2166 + t2098 + t2238 + t2271 + t2310 + 0.17280000000000000000000000000000000000000000000000e-1 * t2121 * t204 * t2122 - 0.3240e1 * t2186 * t91 * t2187 + 0.11520000000000000000000000000000000000000000000000e-2 * t1962 * t2101 - 0.12e-1 * t1808 * t2106 - 0.11520000000000000000000000000000000000000000000000e-2 * t1968 * t2110 + 0.36e-1 * t1836 * t2095 + 0.34560000000000000000000000000000000000000000000000e-2 * t1943 * t2101 - 0.36e-1 * t1840 * t2106 - 0.34560000000000000000000000000000000000000000000000e-2 * t1954 * t2110 - 0.31104000000000000000000000000000000000000000000000e-1 * t1943 * t2126 + 0.28800000000000000000000000000000000000000000000000e0 * t1840 * t2057 + 0.58982400000000000000000000000000000000000000000000e-6 * t1729 * t2045 + 0.58982400000000000000000000000000000000000000000000e-6 * t1747 * t2045 - 0.27377777777777777777777777777777777777777777777778e0 * t1729 * t2019 + 0.11520000000000000000000000000000000000000000000000e-2 * t1910 * t1821 - 0.27377777777777777777777777777777777777777777777778e0 * t1747 * t2019 + 0.22118400000000000000000000000000000000000000000000e-3 * t2026 * t2028 - 0.22118400000000000000000000000000000000000000000000e-3 * t2031 * t2033 + 0.73728000000000000000000000000000000000000000000000e-4 * t2036 * t2028 - 0.73728000000000000000000000000000000000000000000000e-4 * t2039 * t2033 - 0.96000000000000000000000000000000000000000000000000e-1 * t1910 * t1814 - 0.144e0 * t2172 * t2157 - 0.72e-1 * t1986 * t2176 + 0.108e0 * t1934 * t2180 + 0.38400000000000000000000000000000000000000000000000e0 * t1986 * t2183 + 0.34560000000000000000000000000000000000000000000000e1 * t1981 * t2183 - 0.41472000000000000000000000000000000000000000000000e-1 * t2193 * t2195 - 0.648e0 * t1981 * t2176 + 0.756e0 * t1922 * t2180 - 0.72e-1 * t1986 * t2203
  t2317 = 0.1e1 / t21 / t201
  t2323 = 0.1e1 / t20 / t1165
  t2328 = 0.1e1 / t1233
  t2333 = 0.1e1 / t21 / t1129
  t2340 = 0.1e1 / t20 / t1341
  t2347 = t534 * t115
  t2350 = t335 * t215
  t2353 = t1166 * t362
  t2356 = t352 ** 2
  t2359 = t1032 * t573 * t90
  t2364 = t2356 * t1032 * t90
  t2367 = t574 * t1166
  t2370 = t364 * t334
  t2373 = t108 * t533
  t2376 = 0.10342716049382716049382716049382716049382716049383e1 * t89 * t90 * t2317 * t96 - 0.57780148148148148148148148148148148148148148148150e-1 * t199 * t11 * t2323 * t206 + 0.10368442469135802469135802469135802469135802469136e-2 * t340 * t2328 * t345 - 0.38059425185185185185185185185185185185185185185188e-5 * t550 * t2333 * t555 * t90 + 0.99420539259259259259259259259259259259259259259267e-8 * t88 * t1127 * t2340 / t554 / t95 * t11 - 0.6160e4 / 0.81e2 * t210 * t2347 + 0.54400e5 / 0.81e2 * t353 * t2350 - 0.16000e5 / 0.9e1 * t567 * t2353 + 0.20000e5 / 0.27e2 * t100 * t2356 * t2359 + 0.20000e5 / 0.27e2 * t113 * t1160 * t2364 - 0.16000e5 / 0.9e1 * t113 * t2367 + 0.54400e5 / 0.81e2 * t363 * t2370 - 0.6160e4 / 0.81e2 * t216 * t2373
  t2384 = t227 ** 2
  t2387 = t236 ** 2
  t2423 = 0.140e3 / 0.729e3 * t29 * t5 * t1782 * t34
  t2424 = f.my_piecewise3(t39, t2423, 0)
  t2433 = 0.10e2 / 0.3e1 * t48 * t2384 + t45 * t2387 / 0.2e1 - 0.7e1 / 0.8e1 * t51 * t2384 - t48 * t2387 / 0.16e2 + 0.9e1 / 0.80e2 * t54 * t2384 + 0.3e1 / 0.640e3 * t51 * t2387 - 0.11e2 / 0.1152e4 * t57 * t2384 - t54 * t2387 / 0.3840e4 + 0.13e2 / 0.21504e5 * t60 * t2384 + t57 * t2387 / 0.86016e5 - t63 * t2384 / 0.32768e5 - t60 * t2387 / 0.2293760e7 + 0.17e2 / 0.13271040e8 * t264 * t2384 + t63 * t2387 / 0.70778880e8 - 0.19e2 / 0.412876800e9 / t62 / t44 * t2384 - t264 * t2387 / 0.2477260800e10 - t139 * t2424 / 0.4480e4 + t143 * t2424 / 0.103680e6 - t147 * t2424 / 0.2838528e7 + t151 * t2424 / 0.89456640e8
  t2490 = -t155 * t2424 / 0.3185049600e10 + t159 * t2424 / 0.126340300800e12 - t124 * t2424 / 0.18e2 + t135 * t2424 / 0.240e3 + t51 * t383 * t131 / 0.160e3 - t54 * t383 * t131 / 0.2880e4 + t57 * t383 * t131 / 0.64512e5 - t60 * t383 * t131 / 0.1720320e7 + t63 * t383 * t131 / 0.53084160e8 - t264 * t383 * t131 / 0.1857945600e10 + 0.2e1 / 0.3e1 * t45 * t383 * t131 - t48 * t383 * t131 / 0.12e2 - 0.4e1 * t135 * t227 * t236 + 0.3e1 / 0.4e1 * t139 * t227 * t236 - 0.3e1 / 0.40e2 * t143 * t227 * t236 + t147 * t227 * t236 / 0.192e3 - t151 * t227 * t236 / 0.3584e4 + t155 * t227 * t236 / 0.81920e5 - t159 * t227 * t236 / 0.2211840e7 + t438 * t227 * t236 / 0.68812800e8
  t2492 = f.my_piecewise3(t39, 0, t2423)
  t2509 = t278 ** 2
  t2515 = t270 ** 2
  t2529 = t75 * t446
  t2596 = -0.75e2 / 0.2e1 * t298 * t2509 * t75 + 0.45e2 * t279 * t458 + 0.1e1 / t461 / t275 * t2509 * t75 / 0.16e2 - 0.12e2 * t2515 * t76 - 0.16e2 * t502 * t446 - 0.4e1 * t174 * t2492 - t68 * t2492 * t75 - 0.6e1 * t290 * t2515 * t75 - 0.8e1 * t482 * t2529 - 0.15e2 * t486 * t278 * t458 + t298 * t446 * t494 + 0.3e1 / 0.4e1 * t298 * t2515 * t75 + 0.3e1 / 0.4e1 * t498 * t270 * t278 * t75 - 0.3e1 * t73 * t2515 * t75 - 0.4e1 * t505 * t2529 + 0.85e2 / 0.4e1 * t462 * t2509 * t75 - 0.19e2 / 0.8e1 / t461 / t72 * t2509 * t75 + t170 * t2492 * t75 / 0.2e1
  t2599 = 0.2e1 * t2492 * t79 + 0.8e1 * t446 * t179 - 0.3e1 / 0.2e1 * t462 * t278 * t458 + 0.24e2 * t75 * t277 * t2509 - 0.36e2 * t466 * t278 * t270 + 0.6e1 * t282 * t2515 + 0.8e1 * t282 * t163 * t446 - 0.24e2 * t486 * t2509 * t75 + 0.21e2 * t299 * t458 - 0.3e1 / 0.2e1 * t277 * t2515 * t75 - 0.2e1 * t457 * t2529 + 0.15e2 / 0.4e1 * t498 * t2509 * t75 - 0.1e1 / t461 / t169 * t2509 * t75 / 0.8e1 - t165 * t2492 + 0.12e2 * t270 * t310 + 0.8e1 * t163 * t512 + 0.2e1 * t66 * t2596
  t2603 = f.my_piecewise3(t38, t2433 + t2490, -0.8e1 / 0.3e1 * t2492 * t82 - 0.32e2 / 0.3e1 * t446 * t182 - 0.16e2 * t270 * t313 - 0.32e2 / 0.3e1 * t163 * t515 - 0.8e1 / 0.3e1 * t66 * t2599)
  t2648 = -0.3e1 / 0.64e2 * t13 * t376 * t86 * t2376 - t13 * t226 * t585 / 0.16e2 - 0.3e1 / 0.64e2 * t13 * t376 * t2603 * t117 - 0.3e1 / 0.16e2 * t13 * t376 * t519 * t220 - 0.9e1 / 0.32e2 * t13 * t376 * t317 * t371 - 0.3e1 / 0.16e2 * t13 * t376 * t186 * t584 + 0.5e1 / 0.108e3 * t13 * t18 * t193 * t118 - 0.5e1 / 0.72e2 * t13 * t24 * t187 - 0.5e1 / 0.72e2 * t13 * t24 * t221 + t13 * t122 * t318 / 0.16e2 + t13 * t122 * t322 / 0.8e1 + t13 * t122 * t372 / 0.16e2 - t13 * t226 * t520 / 0.16e2 - 0.3e1 / 0.16e2 * t13 * t226 * t524 - 0.3e1 / 0.16e2 * t13 * t226 * t528
  t2649 = f.my_piecewise3(t4, 0, t2648)
  t2652 = t599 * t5 * t1481
  t2661 = t681 ** 2
  t2666 = t689 ** 2
  t2671 = t822 ** 2
  t2674 = 0.60000000000000000000000000000000000000000000000000e1 * t974 * t2671 * t730
  t2677 = 0.48245938496077605200268890697218139186316165284153e2 * t904 * t2671 * t832
  t2693 = -0.13012297560362087811158481026863893997388713132452e0 * t2652 * t629 * t698 * t996 + 0.19263893255070628432628962430736094246707082312995e1 * t2652 * t629 * t688 * t1000 + 0.35089341735807877243573431982554320891834732042568e1 * t737 * t698 * t2661 * t651 - 0.62337092780453269534799339101707810596085839394858e3 * t737 * t739 * t2666 * t692 - t2674 + t2677 - 0.43374325201206959370528270089546313324629043774840e-1 * t601 * t605 * t683 - 0.12842595503380418955085974953824062831138054875329e1 * t601 * t605 * t693 + 0.21687162600603479685264135044773156662314521887420e-1 * t601 * t634 * t786 + 0.38025319932552508024225805073234468230220037056326e2 * t601 * t634 * t744 - 0.38527786510141256865257924861472188493414164625988e1 * t601 * t634 * t750
  t2703 = t687 ** 2
  t2704 = 0.1e1 / t2703
  t2706 = t691 ** 2
  t2707 = 0.1e1 / t2706
  t2715 = t1782 * t11
  t2722 = t887 ** 2
  t2725 = t896 ** 2
  t2726 = t898 ** 2
  t2733 = 0.11483599538271604938271604938271604938271604938271e-1 * t600 * t2715 * t805
  t2737 = t968 ** 2
  t2748 = t6 / r0
  t2754 = t618 ** 2
  t2755 = t356 * t2754
  t2757 = 0.1e1 / t609 / t2748 / t758 * t6 * t2755 * t13 / 0.96e2
  t2759 = 0.1e1 / t354
  t2760 = t2759 * t758
  t2761 = t756 * t2760
  t2763 = t9 * t327
  t2764 = t2763 * t661
  t2765 = t659 * t2764
  t2767 = t10 * t1782
  t2768 = t2767 * t629
  t2769 = t627 * t2768
  t2772 = t600 * t2715 * t604
  t2774 = t608 ** (-0.25e1)
  t2777 = t2774 * t6 * t2755 * t13
  t2779 = t774 * t2760
  t2781 = t673 * t2764
  t2783 = t639 * t2768
  t2786 = t616 * t328 * t618
  t2793 = 0.1e1 / t687 / t697
  t2808 = -0.57538888888888888888888888888888888888888888888889e1 * t2757 + 0.55237333333333333333333333333333333333333333333334e2 * t2761 - 0.10229135802469135802469135802469135802469135802469e2 * t2765 + 0.89504938271604938271604938271604938271604938271607e1 * t2769 + 0.31310740740740740740740740740740740740740740740741e1 * t2772 + 0.73355000000000000000000000000000000000000000000000e-1 * t2777 - 0.11736800000000000000000000000000000000000000000000e1 * t2779 + 0.65204444444444444444444444444444444444444444444445e0 * t2781 + 0.57053888888888888888888888888888888888888888888890e0 * t2783 + 0.13490888888888888888888888888888888888888888888889e1 * t2786
  t2815 = t725 ** 2
  t2818 = 0.62071215503128080358781102641263322069063951965254e4 * t838 / t828 / t718 * t2815 * t844
  t2832 = t2674 - t2677 - 0.55209406483950617283950617283950617283950617283950e-2 * t600 * t2715 * t880 - 0.18989649058080861538367470034170805442117582945368e-2 * t600 * t2715 * t867 + 0.19964560303604640731402349461820840981085646822122e6 * t885 / t2722 * t2725 / t2726 + t2733 + 0.51947577317044391278999449251423175496738199495715e2 * t914 * t2661 * t692 - 0.60000000000000000000000000000000000000000000000000e1 * t985 * t2737 * t910 - 0.24828486201251232143512441056505328827625580786102e5 * t885 / t887 / t983 * t2725 * t900 + 0.10000000000000000000000000000000000000000000000000e1 * t938 * (-0.78438333333333333333333333333333333333333333333333e1 * t2757 + 0.75300800000000000000000000000000000000000000000001e2 * t2761 - 0.13944592592592592592592592592592592592592592592593e2 * t2765 + 0.12201518518518518518518518518518518518518518518519e2 * t2769 + 0.53560370370370370370370370370370370370370370370370e1 * t2772 + 0.28051666666666666666666666666666666666666666666666e0 * t2777 - 0.44882666666666666666666666666666666666666666666666e1 * t2779 + 0.24934814814814814814814814814814814814814814814815e1 * t2781 + 0.21817962962962962962962962962962962962962962962963e1 * t2783 + 0.16979925925925925925925925925925925925925925925926e1 * t2786) * t910 - 0.12304822629859687989861833551788232416071203002497e5 * t736 * t2793 * t2666 * t743 + 0.58482236226346462072622386637590534819724553404280e0 * t926 * t2808 * t651 + t2818 + 0.96491876992155210400537781394436278372632330568306e2 * t909 * t2737 * t933 - 0.35089341735807877243573431982554320891834732042568e1 * t994 * t2661 * t651 + 0.62337092780453269534799339101707810596085839394858e3 * t918 * t2666 * t692 + 0.91082604192152556048340974007871726131433263376469e5 * t736 * t2704 * t2666 * t2707
  t2836 = 0.64327917994770140267025187596290852248421553712204e2 * t904 * t863 * t832 * t724
  t2841 = t681 * t743
  t2874 = 0.31035607751564040179390551320631661034531975982628e4 * t841 * t725 * t844 * t822
  t2877 = 0.57895126195293126240322668836661767023579398340984e3 * t850 * t1073 * t822
  t2880 = 0.80000000000000000000000000000000000000000000000000e1 * t974 * t864 * t724
  t2883 = 0.36000000000000000000000000000000000000000000000000e2 * t904 * t1067 * t822
  t2890 = -t2836 + 0.69263436422725855038665932335230900662317599327620e2 * t914 * t784 * t692 * t646 + 0.61524113149298439949309167758941162080356015012483e4 * t918 * t2841 * t689 - 0.80000000000000000000000000000000000000000000000000e1 * t985 * t986 * t947 - 0.11579025239058625248064533767332353404715879668197e4 * t932 * t1087 * t968 + 0.12865583598954028053405037519258170449684310742441e3 * t909 * t947 * t933 * t895 + 0.12414243100625616071756220528252664413812790393051e5 * t890 * t968 * t900 * t896 - 0.46785788981077169658097909310072427855779642723424e1 * t994 * t995 * t784 + 0.21053605041484726346144059189532592535100839225540e2 * t914 * t1095 * t681 + 0.36000000000000000000000000000000000000000000000000e2 * t909 * t1081 * t968 - 0.62337092780453269534799339101707810596085839394858e3 * t922 * t999 * t689 - t2874 + t2877 + t2880 - t2883 + 0.11579025239058625248064533767332353404715879668197e4 * t890 * t2725 * t933 - 0.24000000000000000000000000000000000000000000000000e2 * t932 * t2725 * t910
  t2903 = 0.68734380377411894875316412946636775627438430141488e1 * t711 * t629 * t849 * t842 * t832
  t2935 = 0.36846163202829085479643115651216588683774907041596e2 * t711 * t629 * t840 * t842 * t844
  t2946 = -0.14035736694323150897429372793021728356733892817027e2 * t922 * t2666 * t651 - 0.67471172535210825687488420139294265171645179205307e-1 * t1593 * t1011 - 0.21309037037037037037037037037037037037037037037036e0 * t1593 * t959 - t2903 - 0.21687162600603479685264135044773156662314521887420e-1 * t711 * t629 * t786 - 0.86748650402413918741056540179092626649258087549680e-1 * t809 * t1003 - 0.13012297560362087811158481026863893997388713132452e0 * t711 * t629 * t795 - 0.41096000000000000000000000000000000000000000000000e0 * t711 * t629 * t908 * t897 * t910 + 0.12842595503380418955085974953824062831138054875329e1 * t809 * t1017 + 0.38527786510141256865257924861472188493414164625988e1 * t711 * t629 * t750 + 0.44060335298551228073561118490952814400018869522611e1 * t809 * t954 + 0.13218100589565368422068335547285844320005660856783e2 * t711 * t629 * t931 * t897 * t933 - 0.27397333333333333333333333333333333333333333333333e0 * t809 * t1008 + t2935 - 0.38025319932552508024225805073234468230220037056326e2 * t711 * t629 * t744 - 0.14171548179536397724580378856363097131945845388689e3 * t711 * t629 * t889 * t897 * t900 + 0.13698666666666666666666666666666666666666666666666e0 * t809 * t971
  t2958 = 0.42740000000000000000000000000000000000000000000000e0 * t711 * t629 * t829 * t842 * t730
  t2960 = 0.28493333333333333333333333333333333333333333333333e0 * t809 * t732
  t2962 = 0.22161481481481481481481481481481481481481481481481e0 * t1593 * t813
  t2964 = 0.14246666666666666666666666666666666666666666666666e0 * t809 * t825
  t2966 = 0.22911460125803964958438804315545591875812810047162e1 * t809 * t834
  t2971 = 0.71233333333333333333333333333333333333333333333332e-1 * t711 * t629 * t810 * t863 * t730
  t2973 = t8 * t628 * t11
  t2977 = 0.42740000000000000000000000000000000000000000000000e0 * t2973 * t604 * t719 * t976
  t2981 = 0.34367190188705947437658206473318387813719215070744e1 * t2973 * t604 * t829 * t980
  t3000 = 0.57895126195293126240322668836661767023579398340984e3 * t841 * t2815 * t832
  t3001 = t828 ** 2
  t3004 = t831 ** 2
  t3008 = 0.24955700379505800914252936827276051226357058527653e5 * t838 / t3001 * t2815 / t3004
  t3022 = 0.10000000000000000000000000000000000000000000000000e1 * t854 * (-0.42198333333333333333333333333333333333333333333333e1 * t2757 + 0.40510400000000000000000000000000000000000000000000e2 * t2761 - 0.75019259259259259259259259259259259259259259259258e1 * t2765 + 0.65641851851851851851851851851851851851851851851850e1 * t2769 + 0.31003950617283950617283950617283950617283950617285e1 * t2772 + 0.13651666666666666666666666666666666666666666666666e0 * t2777 - 0.21842666666666666666666666666666666666666666666666e1 * t2779 + 0.12134814814814814814814814814814814814814814814815e1 * t2781 + 0.10617962962962962962962962962962962962962962962963e1 * t2783 + 0.13388493827160493827160493827160493827160493827161e1 * t2786) * t730
  t3025 = 0.24000000000000000000000000000000000000000000000000e2 * t850 * t2815 * t730
  t3026 = -0.68493333333333333333333333333333333333333333333332e-1 * t711 * t629 * t937 * t947 * t910 + 0.43374325201206959370528270089546313324629043774840e-1 * t809 * t1014 + t2958 + t2960 + t2962 - t2964 - t2966 + t2971 - t2977 + t2981 + 0.13012297560362087811158481026863893997388713132452e0 * t2973 * t604 * t698 * t996 - 0.19263893255070628432628962430736094246707082312994e1 * t2973 * t604 * t688 * t1000 + 0.41096000000000000000000000000000000000000000000000e0 * t2973 * t604 * t984 * t987 - 0.66090502947826842110341677736429221600028304283916e1 * t2973 * t604 * t908 * t991 - t3000 - t3008 - t3022 + t3025
  t3045 = 0.13012297560362087811158481026863893997388713132452e0 * t601 * t634 * t795 + 0.67471172535210825687488420139294265171645179205307e-1 * t601 * t770 * t652 + 0.86748650402413918741056540179092626649258087549680e-1 * t601 * t605 * t700 - 0.91082604192152556048340974007871726131433263376469e5 * t737 * t2704 * t2666 * t2707 - 0.51947577317044391278999449251423175496738199495715e2 * t737 * t688 * t2661 * t692 + t599 * (t2832 + t2890 + t2946 + t3026) + 0.12304822629859687989861833551788232416071203002497e5 * t737 * t2793 * t2666 * t743 - 0.69263436422725855038665932335230900662317599327620e2 * t737 * t688 * t784 * t790 + 0.46785788981077169658097909310072427855779642723424e1 * t737 * t698 * t784 * t995 - 0.21053605041484726346144059189532592535100839225540e2 * t737 * t690 * t800 - t2733 - t2818
  t3054 = 0.14035736694323150897429372793021728356733892817027e2 * t737 * t748 * t2666 * t651 + t2836 + t2874 - t2877 - t2880 + t2883 + t2903 + 0.18989649058080861538367470034170805442117582945368e-2 * t704 * t2767 * t707 - t2935 - t2958 - t2960 - t2962
  t3067 = t2964 + t2966 - t2971 + 0.62337092780453269534799339101707810596085839394858e3 * t737 * t748 * t689 * t999 - 0.61524113149298439949309167758941162080356015012483e4 * t737 * t739 * t689 * t2841 - 0.58482236226346462072622386637590534819724553404280e0 * t737 * t624 * t2808 * t651 + t2977 - t2981 + t3000 + t3008 + t3022 - t3025
  t3072 = f.my_piecewise3(t4, 0, t592 * (t2693 + t3045 + t3054 + t3067) / 0.2e1)
  t3081 = t549 ** 2
  t3086 = t1037 ** 2
  t3094 = 0.1e1 / t21 / t1286 / t201
  t3100 = t1127 * t2340
  t3107 = 0.1e1 / t21 / t1287
  t3113 = t549 * t2333
  t3118 = t339 * t1342 * t1331
  t3124 = t549 * t1288 * t1344
  t3130 = t1127 * t1377 * t1353
  t3141 = 0.34797188740740740740740740740740740740740740740745e1 * t1029 * t3081 / t20 / t1286 / t1165 / t3086 * t11 + 0.37282702222222222222222222222222222222222222222224e1 * t1052 * t1381 * t3094 * t1387 * t90 + 0.19503028148148148148148148148148148148148148148148e3 * t1052 * t3100 * t1270 + 0.23703703703703703703703703703703703703703703703703e2 * t1049 * t2356 * t90 * t3107 * t573 * t339 * t1055 - 0.26155614814814814814814814814814814814814814814815e3 * t1052 * t3113 * t1172 - 0.68266666666666666666666666666666666666666666666668e4 * t1328 * t3118 - 0.34133333333333333333333333333333333333333333333334e4 * t1337 * t3118 - 0.17066666666666666666666666666666666666666666666667e4 * t1340 * t3124 - 0.27306666666666666666666666666666666666666666666667e4 * t1348 * t3124 - 0.45438293333333333333333333333333333333333333333333e3 * t1351 * t3130 - 0.68266666666666666666666666666666666666666666666666e3 * t1358 * t3118 - 0.40960000000000000000000000000000000000000000000000e4 * t1361 * t3118 - 0.10240000000000000000000000000000000000000000000000e4 * t1364 * t3124 - 0.45438293333333333333333333333333333333333333333333e3 * t1367 * t3130
  t3150 = t339 * t2328
  t3154 = t1286 * t200
  t3155 = 0.1e1 / t3154
  t3182 = 0.54400e5 / 0.27e2 * t1248 * t2370 - 0.6160e4 / 0.81e2 * t1141 * t2373 - 0.12320e5 / 0.81e2 * t1145 * t2373 - 0.12320e5 / 0.81e2 * t1148 * t2373 + 0.253440e3 * t1052 * t3150 * t1055 - 0.62914560000000000000000000000000000000000000000004e2 * t1052 * t1284 * t3155 * t1290 + 0.54400e5 / 0.81e2 * t1242 * t2370 + 0.217600e6 / 0.81e2 * t1245 * t2370 + 0.20000e5 / 0.27e2 * t1043 * t1160 * t2364 + 0.160000e6 / 0.27e2 * t1144 * t1160 * t2364 + 0.100000e6 / 0.27e2 * t1047 * t1206 * t2364 - 0.16000e5 / 0.9e1 * t1370 * t2353 - 0.32000e5 / 0.9e1 * t1373 * t2353 + 0.19293474765432098765432098765432098765432098765434e3 * t1285 * t3155 * t1290 + 0.54400e5 / 0.81e2 * t1277 * t2350
  t3219 = 0.1e1 / t21 / t3154 * t1134 * t352 * t90
  t3225 = t1385 * t1290 * t108
  t3237 = 0.1e1 / t21 / t1376 * t1038 * t566 * t90
  t3244 = 0.13787338271604938271604938271604938271604938271605e3 * t1030 * t90 * t2333 * t1038 - 0.6160e4 / 0.81e2 * t1138 * t2347 - 0.26951680000000000000000000000000000000000000000000e3 * t1128 * t11 * t2340 * t1134 + 0.54400e5 / 0.81e2 * t1274 * t2350 - 0.16000e5 / 0.9e1 * t1043 * t2367 - 0.32000e5 / 0.3e1 * t1144 * t2367 - 0.64000e5 / 0.9e1 * t1047 * t1403 * t1166 + 0.20000e5 / 0.27e2 * t1042 * t2356 * t2359 + 0.20000e5 / 0.9e1 * t1045 * t2356 * t2359 - 0.30136850962962962962962962962962962962962962962965e2 * t1382 * t3094 * t1387 * t90 + 0.87381333333333333333333333333333333333333333333334e2 * t1222 * t573 * t1127 * t3219 + 0.31068918518518518518518518518518518518518518518519e2 * t1152 * t573 * t1284 * t3225 + 0.14563555555555555555555555555555555555555555555556e3 * t1051 * t1206 * t1127 * t3219 + 0.54613333333333333333333333333333333333333333333332e3 * t1222 * t1215 * t3237 + 0.23301688888888888888888888888888888888888888888888e3 * t1152 * t1160 * t1127 * t3219
  t3252 = t3107 * t1055 * t2356 * t90
  t3269 = t572 ** 2
  t3280 = t553 * t1055 * t108
  t3284 = t1268 * t1055 * t364
  t3290 = t1323 * t1038 * t1218
  t3299 = 0.31068918518518518518518518518518518518518518518519e2 * t1051 * t1160 * t1284 * t3225 + 0.37925925925925925925925925925925925925925925925925e3 * t1357 * t1161 * t3252 + 0.91022222222222222222222222222222222222222222222222e2 * t1357 * t1229 * t3237 + 0.14222222222222222222222222222222222222222222222222e4 * t1222 * t1207 * t3252 + 0.18962962962962962962962962962962962962962962962963e4 * t1152 * t1336 * t339 * t3252 + 0.91022222222222222222222222222222222222222222222221e3 * t1152 * t1206 * t549 * t3237 + 0.82962962962962962962962962962962962962962962962962e3 * t1051 / t3269 * t339 * t3252 + 0.45511111111111111111111111111111111111111111111111e3 * t1051 * t1336 * t549 * t3237 - 0.93664395061728395061728395061728395061728395061728e3 * t1162 * t3280 + 0.15966814814814814814814814814814814814814814814815e4 * t1223 * t3284 + 0.42578172839506172839506172839506172839506172839506e4 * t1226 * t3284 + 0.11183597037037037037037037037037037037037037037037e4 * t1230 * t3290 - 0.93664395061728395061728395061728395061728395061728e3 * t1154 * t3280 + 0.26611358024691358024691358024691358024691358024691e4 * t1208 * t3284 + 0.11183597037037037037037037037037037037037037037037e4 * t1216 * t3290
  t3304 = t1462 * t600
  t3306 = t1653 * t1627
  t3312 = t1492 * t1498
  t3347 = 0.19263893255070628432628962430736094246707082312994e1 * t3304 * t126 * t1646 * t3306 * t1492 - 0.13012297560362087811158481026863893997388713132452e0 * t3304 * t126 * t1477 * t3312 * t1653 + 0.31035607751564040179390551320631661034531975982628e4 * t1567 * t1533 * t1569 * t1548 + 0.36000000000000000000000000000000000000000000000000e2 * t1513 * t1698 * t1533 + 0.64327917994770140267025187596290852248421553712204e2 * t1513 * t1605 * t1538 * t1544 - 0.11483599538271604938271604938271604938271604938271e-1 * t8 * t2767 * t1561 - 0.2e1 * t3072 - 0.71233333333333333333333333333333333333333333333332e-1 * t600 * t1672 * t1606 - 0.22161481481481481481481481481481481481481481481481e0 * t600 * t378 * t1579 * t1557 - 0.36846163202829085479643115651216588683774907041596e2 * t600 * t126 * t1566 * t1570 + 0.68734380377411894875316412946636775627438430141488e1 * t600 * t126 * t1574 * t1576
  t3386 = t1548 ** 2
  t3393 = -0.42740000000000000000000000000000000000000000000000e0 * t600 * t1677 * t1551 - 0.21053605041484726346144059189532592535100839225540e2 * t1612 * t1692 * t1664 - 0.69263436422725855038665932335230900662317599327620e2 * t1612 * t1646 * t1641 * t1655 + 0.14246666666666666666666666666666666666666666666666e0 * t600 * t1668 * t1673 + 0.22911460125803964958438804315545591875812810047162e1 * t600 * t231 * t1512 * t1678 + 0.18989649058080861538367470034170805442117582945368e-2 * t1702 * t1480 * t1782 * t1703 - 0.28493333333333333333333333333333333333333333333333e0 * t600 * t231 * t1555 * t1698 - 0.61524113149298439949309167758941162080356015012483e4 * t1612 * t1615 * t1493 * t1620 * t1653 + 0.62337092780453269534799339101707810596085839394858e3 * t1612 * t1625 * t1493 * t3306 + 0.46785788981077169658097909310072427855779642723424e1 * t1612 * t1477 * t1641 * t3312 - 0.24000000000000000000000000000000000000000000000000e2 * t1575 * t3386 * t1550 + 0.86748650402413918741056540179092626649258087549680e-1 * t1463 * t665 * t1499
  t3421 = 0.1e1 / t1466 / t2748 * t6 * t356 * t600 / 0.48e2
  t3423 = t1584 * t2759
  t3425 = t1517 * t327
  t3426 = t1516 * t3425
  t3428 = t1480 * t1782
  t3429 = t1479 * t3428
  t3431 = t8 * t2767
  t3433 = t1465 ** (-0.25e1)
  t3436 = t3433 * t6 * t356 * t600
  t3438 = t1596 * t2759
  t3440 = t1526 * t3425
  t3442 = t1486 * t3428
  t3444 = t615 * t2763
  t3451 = t1653 ** 2
  t3460 = t1613 ** 2
  t3462 = t1493 ** 2
  t3464 = t1618 ** 2
  t3475 = 0.13012297560362087811158481026863893997388713132452e0 * t1463 * t628 * t1660 + 0.38025319932552508024225805073234468230220037056326e2 * t1463 * t628 * t1621 + 0.21687162600603479685264135044773156662314521887420e-1 * t1463 * t628 * t1643 - 0.43374325201206959370528270089546313324629043774840e-1 * t1463 * t665 * t1688 - 0.12842595503380418955085974953824062831138054875329e1 * t1463 * t665 * t1693 + 0.67471172535210825687488420139294265171645179205307e-1 * t1463 * t705 * t1683 - 0.38527786510141256865257924861472188493414164625988e1 * t1463 * t628 * t1628 - 0.58482236226346462072622386637590534819724553404280e0 * t1612 * t1632 * (-0.28769444444444444444444444444444444444444444444444e1 * t3421 + 0.27618666666666666666666666666666666666666666666667e2 * t3423 - 0.10229135802469135802469135802469135802469135802469e2 * t3426 + 0.89504938271604938271604938271604938271604938271607e1 * t3429 + 0.31310740740740740740740740740740740740740740740741e1 * t3431 + 0.36677500000000000000000000000000000000000000000000e-1 * t3436 - 0.58684000000000000000000000000000000000000000000000e0 * t3438 + 0.65204444444444444444444444444444444444444444444445e0 * t3440 + 0.57053888888888888888888888888888888888888888888890e0 * t3442 + 0.13490888888888888888888888888888888888888888888889e1 * t3444) * t1498 + 0.35089341735807877243573431982554320891834732042568e1 * t1612 * t1477 * t3451 * t1498 - 0.51947577317044391278999449251423175496738199495715e2 * t1612 * t1646 * t3451 * t1627 - 0.91082604192152556048340974007871726131433263376469e5 * t1612 / t3460 * t3462 / t3464 + 0.12304822629859687989861833551788232416071203002497e5 * t1612 / t1613 / t1476 * t3462 * t1620
  t3513 = t1511 ** 2
  t3516 = t1537 ** 2
  t3524 = t1533 ** 2
  t3537 = -0.62337092780453269534799339101707810596085839394858e3 * t1612 * t1615 * t3462 * t1627 + 0.14035736694323150897429372793021728356733892817027e2 * t1612 * t1625 * t3462 * t1498 - 0.34367190188705947437658206473318387813719215070744e1 * t711 * t1512 * t1533 * t1538 * t1544 + 0.42740000000000000000000000000000000000000000000000e0 * t711 * t1555 * t1544 * t1673 + 0.10000000000000000000000000000000000000000000000000e1 * t1580 * (-0.21099166666666666666666666666666666666666666666667e1 * t3421 + 0.20255200000000000000000000000000000000000000000000e2 * t3423 - 0.75019259259259259259259259259259259259259259259258e1 * t3426 + 0.65641851851851851851851851851851851851851851851850e1 * t3429 + 0.31003950617283950617283950617283950617283950617285e1 * t3431 + 0.68258333333333333333333333333333333333333333333335e-1 * t3436 - 0.10921333333333333333333333333333333333333333333333e1 * t3438 + 0.12134814814814814814814814814814814814814814814815e1 * t3440 + 0.10617962962962962962962962962962962962962962962963e1 * t3442 + 0.13388493827160493827160493827160493827160493827161e1 * t3444) * t1550 - 0.62071215503128080358781102641263322069063951965254e4 * t1504 / t1511 / t1554 * t3386 * t1569 + 0.24955700379505800914252936827276051226357058527653e5 * t1504 / t3513 * t3386 / t3516 + 0.57895126195293126240322668836661767023579398340984e3 * t1567 * t3386 * t1538 - 0.60000000000000000000000000000000000000000000000000e1 * t1556 * t3524 * t1550 + 0.48245938496077605200268890697218139186316165284153e2 * t1513 * t3524 * t1538 - 0.80000000000000000000000000000000000000000000000000e1 * t1556 * t1557 * t1605 - 0.57895126195293126240322668836661767023579398340984e3 * t1575 * t1539 * t1548
  t3548 = t1865 ** 2
  t3550 = t91 * t1732 * t3548
  t3553 = t328 * t1938
  t3564 = t328 * t1949
  t3570 = t204 * t1819 * t2155
  t3573 = t335 * t2062
  t3579 = t335 * t2109
  t3585 = 0.720e0 * t1728 * t1835 * t3550 + 0.70400000000000000000000000000000000000000000000000e0 * t1802 * t3553 + 0.21120000000000000000000000000000000000000000000000e1 * t1836 * t3553 + 0.432e0 * t1909 * t1933 * t1924 + 0.10560000000000000000000000000000000000000000000000e2 * t1974 * t328 * t1975 - 0.21120000000000000000000000000000000000000000000000e1 * t1840 * t3564 - 0.25804800000000000000000000000000000000000000000000e0 * t1746 * t2152 * t198 * t3570 - 0.43545600000000000000000000000000000000000000000000e0 * t2133 * t3573 - 0.76800000000000000000000000000000000000000000000000e1 * t2077 * t194 * t2079 + 0.62208000000000000000000000000000000000000000000000e-1 * t1954 * t3579 - 0.31104000000000000000000000000000000000000000000000e0 * t2121 * t335 * t2122
  t3592 = 0.1232e4 / 0.27e2 * t106 * t2373
  t3593 = 0.158080e6 / 0.81e2 * t2370
  t3594 = t3592 - t3593
  t3596 = t91 * t1732 * t3594
  t3600 = t204 * t1819 * t2093
  t3603 = t3592 + t3593
  t3605 = t91 * t1732 * t3603
  t3610 = t553 * t2043
  t3612 = t3610 * t1788 * t90
  t3618 = t1785 * t1788
  t3619 = t343 * t1882 * t3618
  t3625 = t3610 * t1785 * t90
  t3632 = t540 * t1944
  t3636 = t204 * t1819 * t2104
  t3639 = -0.92160000000000000000000000000000000000000000000000e-2 * t1909 * t1967 * t1956 + 0.48e-1 * t2087 * t2095 + 0.12e-1 * t1802 * t3596 + 0.15360000000000000000000000000000000000000000000000e-2 * t1962 * t3600 - 0.12e-1 * t1808 * t3605 - 0.14155776000000000000000000000000000000000000000000e-4 * t1746 * t1830 * t549 * t3612 - 0.58982400000000000000000000000000000000000000000000e-3 * t1800 * t1796 * t339 * t3619 + 0.47185920000000000000000000000000000000000000000000e-5 * t1800 * t1725 * t549 * t3625 - 0.47185920000000000000000000000000000000000000000000e-5 * t1728 * t1796 * t549 * t3612 + 0.11639466666666666666666666666666666666666666666667e0 * t1962 * t3632 - 0.15360000000000000000000000000000000000000000000000e-2 * t1968 * t3636
  t3645 = t1891 ** 2
  t3652 = t328 * t1923
  t3655 = t194 * t2156
  t3661 = 0.1e1 / t1863 / t1724
  t3673 = 0.36e-1 * t1836 * t3596 + 0.46080000000000000000000000000000000000000000000000e-2 * t1943 * t3600 + 0.540e0 * t1974 * t91 * t1732 * t3645 - 0.62208000000000000000000000000000000000000000000000e-1 * t2061 * t3573 + 0.21120000000000000000000000000000000000000000000000e1 * t1934 * t3652 + 0.15360000000000000000000000000000000000000000000000e1 * t2172 * t3655 - 0.70400000000000000000000000000000000000000000000000e0 * t1808 * t3564 + 0.18144e2 * t1746 * t3661 * s0 * t3550 + 0.21504000000000000000000000000000000000000000000000e2 * t2154 * t3655 + 0.14784000000000000000000000000000000000000000000000e2 * t1922 * t3652 + 0.90e2 * t1876 * t1743 * t3645
  t3677 = t1817 * t2323 * t1819
  t3681 = t1258 * t1882 * t1891
  t3685 = t1258 * t1882 * t1948
  t3695 = t3100 / t2042 / t1731 * t11
  t3703 = t92 * t2317 * t1732
  t3711 = t1427 * t2027
  t3714 = -0.24e2 * t1894 * t1996 - 0.13000533333333333333333333333333333333333333333333e0 * t1747 * t3677 + 0.44236800000000000000000000000000000000000000000000e-3 * t2026 * t3681 - 0.44236800000000000000000000000000000000000000000000e-3 * t2031 * t3685 + 0.14745600000000000000000000000000000000000000000000e-3 * t2036 * t3681 - 0.14745600000000000000000000000000000000000000000000e-3 * t2039 * t3685 + 0.75497472000000000000000000000000000000000000000000e-7 * t1729 * t3695 + 0.75497472000000000000000000000000000000000000000000e-7 * t1747 * t3695 - 0.20736000000000000000000000000000000000000000000000e-1 * t1910 * t1898 + 0.15514074074074074074074074074074074074074074074074e1 * t1747 * t3703 + 0.22118400000000000000000000000000000000000000000000e-2 * t1973 * t1743 * t1258 * t1882 * t1877 - 0.56033280000000000000000000000000000000000000000000e-2 * t2026 * t3711
  t3719 = t1258 * t1882 * t1865
  t3722 = t1427 * t2032
  t3732 = t3113 * t2044
  t3747 = 0.30965760000000000000000000000000000000000000000000e-2 * t1746 * t1864 * t3719 + 0.56033280000000000000000000000000000000000000000000e-2 * t2031 * t3722 - 0.18677760000000000000000000000000000000000000000000e-2 * t2036 * t3711 + 0.44236800000000000000000000000000000000000000000000e-3 * t1728 * t1872 * t3719 + 0.18677760000000000000000000000000000000000000000000e-2 * t2039 * t3722 - 0.19267584000000000000000000000000000000000000000000e-4 * t1729 * t3732 - 0.19267584000000000000000000000000000000000000000000e-4 * t1747 * t3732 - 0.13000533333333333333333333333333333333333333333333e0 * t1729 * t3677 + 0.70400000000000000000000000000000000000000000000000e0 * t1910 * t1904 + 0.15514074074074074074074074074074074074074074074074e1 * t1729 * t3703 + 0.36e-1 * t1727 * t3645 * t1725 * t1734
  t3750 = t1877 ** 2
  t3755 = t1948 ** 2
  t3757 = t91 * t1732 * t3755
  t3766 = t335 * t2100
  t3769 = t194 * t2105
  t3772 = t194 * t2094
  t3779 = t534 * t1803
  t3782 = t534 * t1809
  t3785 = 0.2160e1 * t1745 * t1722 * t1835 * t91 * t1732 * t3750 + 0.108e0 * t1934 * t3757 - 0.18432000000000000000000000000000000000000000000000e-1 * t1728 * t2170 * t198 * t3570 - 0.46080000000000000000000000000000000000000000000000e-2 * t1954 * t3636 - 0.62208000000000000000000000000000000000000000000000e-1 * t1943 * t3766 + 0.38400000000000000000000000000000000000000000000000e0 * t1840 * t3769 - 0.12800000000000000000000000000000000000000000000000e0 * t1802 * t3772 - 0.20736000000000000000000000000000000000000000000000e-1 * t1962 * t3766 + 0.756e0 * t1922 * t3757 - 0.65706666666666666666666666666666666666666666666667e1 * t1836 * t3779 + 0.65706666666666666666666666666666666666666666666667e1 * t1840 * t3782
  t3815 = t328 * t1982
  t3822 = -0.53084160000000000000000000000000000000000000000000e-2 * t1834 * t1830 * t339 * t3619 + 0.14155776000000000000000000000000000000000000000000e-4 * t1834 * t1743 * t549 * t3625 + 0.1512e4 * t1825 * t1866 * t1891 + 0.24e2 * t1786 * t2279 + 0.8e1 * t1717 * t1797 * t2104 + 0.120e3 * t1876 * t1826 * t2093 - 0.48e2 * t2235 * t2297 - 0.16e2 * t1791 * t1796 * t2093 * t1788 - 0.24e2 * t1791 * t2296 * t1948 - 0.25344000000000000000000000000000000000000000000000e2 * t1981 * t3815 + 0.69120000000000000000000000000000000000000000000000e-1 * t2121 * t204 * t1944 * t1891
  t3823 = t335 * t2194
  t3826 = t194 * t2175
  t3829 = t194 * t2179
  t3834 = t204 * t2062 * t1785
  t3847 = t204 * t1955 * t1948
  t3850 = t194 * t2217
  t3854 = t204 * t2109 * t1785
  t3869 = 0.74649600000000000000000000000000000000000000000000e0 * t2193 * t3823 + 0.69120000000000000000000000000000000000000000000000e1 * t1981 * t3826 - 0.80640000000000000000000000000000000000000000000000e1 * t1922 * t3829 + 0.58060800000000000000000000000000000000000000000000e0 * t1834 * t2132 * t3834 + 0.4320e1 * t2077 * t91 * t1975 * t1891 + 0.45360e2 * t1973 * t1921 * t91 * t1975 * t1865 + 0.13824000000000000000000000000000000000000000000000e-1 * t2061 * t3847 - 0.23040000000000000000000000000000000000000000000000e1 * t2221 * t3850 - 0.82944000000000000000000000000000000000000000000000e-1 * t2193 * t3854 + 0.96768000000000000000000000000000000000000000000000e-1 * t2133 * t3847 - 0.41472000000000000000000000000000000000000000000000e0 * t1973 * t1953 * t204 * t2122 * t1788 - 0.17280e2 * t2076 * t1839 * t91 * t2079 * t1788
  t3878 = t91 * t2094 * t1788
  t3882 = t204 * t2100 * t1788
  t3886 = t91 * t2105 * t1785
  t3890 = t91 * t2105 * t1788
  t3894 = t91 * t1938 * t1865
  t3900 = t91 * t1923 * t1948
  t3910 = 0.720e0 * t1974 * t91 * t2094 * t1785 - 0.864e0 * t1981 * t3878 - 0.82944000000000000000000000000000000000000000000000e-1 * t2193 * t3882 - 0.864e0 * t1981 * t3886 + 0.1008e1 * t1922 * t3890 + 0.432e0 * t2221 * t3894 - 0.96e-1 * t1986 * t3878 - 0.864e0 * t2172 * t3900 + 0.76800000000000000000000000000000000000000000000000e0 * t1986 * t3826 - 0.11520000000000000000000000000000000000000000000000e1 * t1934 * t3829 + 0.27648000000000000000000000000000000000000000000000e-1 * t1800 * t2060 * t3834
  t3913 = t91 * t2156 * t1785
  t3925 = t194 * t2202
  t3940 = -0.48384e2 * t1834 * t2153 * t3913 - 0.12096e2 * t2154 * t3900 - 0.48384000000000000000000000000000000000000000000000e2 * t2216 * t3850 - 0.28160000000000000000000000000000000000000000000000e1 * t1986 * t3815 - 0.1152e1 * t1800 * t2171 * t3913 + 0.76800000000000000000000000000000000000000000000000e0 * t1986 * t3925 + 0.82944000000000000000000000000000000000000000000000e-1 * t2207 * t3823 - 0.57600000000000000000000000000000000000000000000000e1 * t1974 * t194 * t2210 + 0.69120000000000000000000000000000000000000000000000e1 * t1981 * t3925 - 0.288e0 * t2086 * t1807 * t2203 + 0.9072e1 * t2216 * t3894
  t3973 = 0.34560000000000000000000000000000000000000000000000e2 * t2186 * t194 * t2187 - 0.192e3 * t1791 * t2262 * t1785 - 0.6e1 * t1892 * t1991 - 0.4e1 * t1786 * t2233 - t1717 * t1725 * t3603 + 0.120e3 * t1723 * t1743 * t3548 + 0.360e3 * t1737 * t1722 * t1743 * t3750 - 0.24e2 * t1786 * t2259 + 0.3024e4 * t1740 * t3661 * t3548 + 0.24e2 * t1717 * t2170 * t3548 - 0.2016e4 * t1740 * t2152 * t1948 * t1865
  t4008 = 0.7560e4 * t1876 * t1866 * t1877 - 0.8064e4 * t1825 * t2256 * t1785 - 0.36e2 * t1717 * t1873 * t1948 - 0.16e2 * t1791 * t2243 * t1785 - 0.144e3 * t1825 * t1830 * t2093 * t1788 - 0.216e3 * t1825 * t2303 * t1948 - 0.144e3 * t1825 * t2251 * t1785 + 0.168e3 * t1740 * t1864 * t2104 * t1788 - 0.92160000000000000000000000000000000000000000000000e-2 * t2207 * t3882 - 0.96e-1 * t1986 * t3886 + 0.144e0 * t1934 * t3890 - 0.92160000000000000000000000000000000000000000000000e-2 * t2207 * t3854
  t4012 = t91 * t1949 * t1891
  t4036 = t540 * t1955
  t4041 = -0.1296e1 * t1981 * t4012 - 0.144e0 * t1986 * t4012 - 0.6480e1 * t2186 * t91 * t1975 * t1948 + 0.12800000000000000000000000000000000000000000000000e0 * t1808 * t3769 + 0.20736000000000000000000000000000000000000000000000e-1 * t1968 * t3579 - 0.38400000000000000000000000000000000000000000000000e0 * t1836 * t3772 - 0.144e0 * t2145 * t1950 + 0.92160000000000000000000000000000000000000000000000e-1 * t2076 * t1942 * t204 * t1819 * t2078 - 0.36e-1 * t1840 * t3605 - 0.11639466666666666666666666666666666666666666666667e0 * t1968 * t4036 + 0.34918400000000000000000000000000000000000000000000e0 * t1943 * t3632
  t4055 = t3150 * t1882
  t4062 = t1948 * t1788 * t1785
  t4070 = -0.34918400000000000000000000000000000000000000000000e0 * t1954 * t4036 - 0.38400000000000000000000000000000000000000000000000e0 * t2087 * t2138 + 0.76800000000000000000000000000000000000000000000000e0 * t2145 * t1927 - 0.21902222222222222222222222222222222222222222222223e1 * t1802 * t3779 + 0.21902222222222222222222222222222222222222222222223e1 * t1808 * t3782 + 0.46080000000000000000000000000000000000000000000000e-2 * t2086 * t1961 * t2101 + 0.34993493333333333333333333333333333333333333333333e-2 * t1729 * t4055 + 0.34993493333333333333333333333333333333333333333333e-2 * t1747 * t4055 + 0.3024e4 * t1825 * t1864 * t4062 + 0.14745600000000000000000000000000000000000000000000e-3 * t1910 * t1883 + 0.144e3 * t1791 * t1872 * t4062
  t4073 = t3618 * t1891
  t4103 = 0.6e1 * t1717 * t1796 * t3755 - 0.2e1 * t1723 * t1796 * t3603 + 0.18e2 * t1723 * t1872 * t3755 + 0.2e1 * t1791 * t1725 * t3594 - 0.6e1 * t1740 * t1830 * t3603 + 0.126e3 * t1740 * t1864 * t3755 + 0.6e1 * t1825 * t1743 * t3594 - 0.2160e4 * t1876 * t1830 * t4073 + 0.12e2 * t1892 * t1869 + 0.72e2 * t1894 * t1873 + 0.8e1 * t2235 * t2240
  t4138 = t1733 * t4062
  t4145 = -0.4e1 * t2224 * t1789 + 0.6e1 * t1721 * t3645 * t1725 + t1711 * t3594 * t1719 - 0.144e3 * t1723 * t2170 * t1865 * t1948 - 0.2880e4 * t2265 * t1830 * t2078 * t1788 + 0.720e3 * t2265 * t1878 * t1891 + 0.72e2 * t1791 * t1873 * t1891 + 0.24e2 * t1723 * t2285 * t2104 - 0.1080e4 * t1876 * t2289 * t1948 - 0.12960e2 * t1973 * t1839 * t90 * t1733 * t4073 + 0.18144e2 * t1834 * t1921 * t90 * t4138 + 0.864e0 * t1800 * t1933 * t90 * t4138
  t4151 = 0.2e1 * t2649 + 0.2e1 * t3072 * t1059 + 0.8e1 * t1027 * t1176 + 0.12e2 * t1120 * t1301 + 0.8e1 * t1204 * t1456 + 0.2e1 * t1317 * (t3141 + t3182 + t3244 + t3299) + (t3347 + t3393 + t3475 + t3537) * t1750 + 0.4e1 * t1709 * t1847 + 0.6e1 * t1779 * t2006 + 0.4e1 * t1862 * t2313 + t2015 * (t3585 + t3639 + t3673 + t3714 + t3747 + t3785 + t3822 + t3869 + t3910 + t3940 + t3973 + t4008 + t4041 + t4070 + t4103 + t4145)
  v4rho4_0_ = r0 * t4151 + 0.8e1 * t1027 * t1059 + 0.24e2 * t1120 * t1176 + 0.24e2 * t1204 * t1301 + 0.8e1 * t1317 * t1456 + 0.4e1 * t1709 * t1750 + 0.12e2 * t1779 * t1847 + 0.12e2 * t1862 * t2006 + 0.4e1 * t2015 * t2313 + 0.8e1 * t590

  res = {'v4rho4': v4rho4_0_}
  return res
