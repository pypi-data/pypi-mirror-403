"""Generated from mgga_c_revtpss.mpl."""

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
  params_C0_c_raw = params.C0_c
  if isinstance(params_C0_c_raw, (str, bytes, dict)):
    params_C0_c = params_C0_c_raw
  else:
    try:
      params_C0_c_seq = list(params_C0_c_raw)
    except TypeError:
      params_C0_c = params_C0_c_raw
    else:
      params_C0_c_seq = np.asarray(params_C0_c_seq, dtype=np.float64)
      params_C0_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_C0_c_seq))
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  beta_a = 0.06672455060314922

  beta_b = 0.1

  beta_c = 0.1778

  tpss_xi2 = lambda z, xt, xs0, xs1: (1 - z ** 2) * (f.t_total(z, xs0 ** 2, xs1 ** 2) - xt ** 2) / (2 * (3 * jnp.pi ** 2) ** (1 / 3)) ** 2

  tpss_C00 = lambda cc, z: +jnp.sum(jnp.array([cc[i] * z ** (2 * (i - 1)) for i in range(1, 4 + 1)]), axis=0)

  tpss_aux = lambda z, xt, ts0, ts1: jnp.minimum(xt ** 2 / (8 * f.t_total(z, ts0, ts1)), 1)

  tpss_par_s0 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 + z)) ** (1 / 3), 1, xs0, xs0, 0), f_gga(rs, z, xt, xs0, xs1)) * (1 + z) / 2

  tpss_par_s1 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 - z)) ** (1 / 3), -1, xs1, 0, xs1), f_gga(rs, z, xt, xs0, xs1)) * (1 - z) / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  mgamma = params_gamma

  BB = params_BB

  mbeta = lambda rs, t=None: beta_a * (1 + beta_b * rs) / (1 + beta_c * rs)

  tpss_C0_den = lambda z, xt, xs0, xs1: 1 + tpss_xi2(z, xt, xs0, xs1) * ((1 + z) ** (-4 / 3) + (1 - z) ** (-4 / 3)) / 2

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  tpss_C0 = lambda cc, z, xt, xs0, xs1: f.my_piecewise3(1 - jnp.abs(z) <= 1e-12, jnp.sum(jnp.array([cc[i] for i in range(1, 4 + 1)]), axis=0), tpss_C00(cc, z) / tpss_C0_den(f.z_thr(z), xt, xs0, xs1) ** 4)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  tpss_par = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: -(1 + tpss_C0(params_C0_c, z, xt, xs0, xs1)) * tpss_aux(z, xt, ts0, ts1) ** 2 * (+f.my_piecewise3(f.screen_dens_zeta(rs, z), f_gga(rs, f.z_thr(z), xt, xs0, xs1) * (1 + z) / 2, tpss_par_s0(f_gga, rs, f.z_thr(z), xt, xs0, xs1)) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), f_gga(rs, f.z_thr(z), xt, xs0, xs1) * (1 - z) / 2, tpss_par_s1(f_gga, rs, f.z_thr(z), xt, xs0, xs1)))

  tpss_perp = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: (1 + tpss_C0(params_C0_c, z, xt, xs0, xs1) * tpss_aux(z, xt, ts0, ts1) ** 2) * f_gga(rs, z, xt, xs0, xs1)

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  tpss_f0 = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: +tpss_par(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) + tpss_perp(f_gga, rs, z, xt, xs0, xs1, ts0, ts1)

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  tpss_f = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: +tpss_f0(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) * (1 + params_d * tpss_f0(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) * tpss_aux(z, xt, ts0, ts1) ** 3)

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: +tpss_f(f_pbe, rs, z, xt, xs0, xs1, ts0, ts1)

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
  params_C0_c_raw = params.C0_c
  if isinstance(params_C0_c_raw, (str, bytes, dict)):
    params_C0_c = params_C0_c_raw
  else:
    try:
      params_C0_c_seq = list(params_C0_c_raw)
    except TypeError:
      params_C0_c = params_C0_c_raw
    else:
      params_C0_c_seq = np.asarray(params_C0_c_seq, dtype=np.float64)
      params_C0_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_C0_c_seq))
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  beta_a = 0.06672455060314922

  beta_b = 0.1

  beta_c = 0.1778

  tpss_xi2 = lambda z, xt, xs0, xs1: (1 - z ** 2) * (f.t_total(z, xs0 ** 2, xs1 ** 2) - xt ** 2) / (2 * (3 * jnp.pi ** 2) ** (1 / 3)) ** 2

  tpss_C00 = lambda cc, z: +jnp.sum(jnp.array([cc[i] * z ** (2 * (i - 1)) for i in range(1, 4 + 1)]), axis=0)

  tpss_aux = lambda z, xt, ts0, ts1: jnp.minimum(xt ** 2 / (8 * f.t_total(z, ts0, ts1)), 1)

  tpss_par_s0 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 + z)) ** (1 / 3), 1, xs0, xs0, 0), f_gga(rs, z, xt, xs0, xs1)) * (1 + z) / 2

  tpss_par_s1 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 - z)) ** (1 / 3), -1, xs1, 0, xs1), f_gga(rs, z, xt, xs0, xs1)) * (1 - z) / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  mgamma = params_gamma

  BB = params_BB

  mbeta = lambda rs, t=None: beta_a * (1 + beta_b * rs) / (1 + beta_c * rs)

  tpss_C0_den = lambda z, xt, xs0, xs1: 1 + tpss_xi2(z, xt, xs0, xs1) * ((1 + z) ** (-4 / 3) + (1 - z) ** (-4 / 3)) / 2

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  tpss_C0 = lambda cc, z, xt, xs0, xs1: f.my_piecewise3(1 - jnp.abs(z) <= 1e-12, jnp.sum(jnp.array([cc[i] for i in range(1, 4 + 1)]), axis=0), tpss_C00(cc, z) / tpss_C0_den(f.z_thr(z), xt, xs0, xs1) ** 4)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  tpss_par = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: -(1 + tpss_C0(params_C0_c, z, xt, xs0, xs1)) * tpss_aux(z, xt, ts0, ts1) ** 2 * (+f.my_piecewise3(f.screen_dens_zeta(rs, z), f_gga(rs, f.z_thr(z), xt, xs0, xs1) * (1 + z) / 2, tpss_par_s0(f_gga, rs, f.z_thr(z), xt, xs0, xs1)) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), f_gga(rs, f.z_thr(z), xt, xs0, xs1) * (1 - z) / 2, tpss_par_s1(f_gga, rs, f.z_thr(z), xt, xs0, xs1)))

  tpss_perp = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: (1 + tpss_C0(params_C0_c, z, xt, xs0, xs1) * tpss_aux(z, xt, ts0, ts1) ** 2) * f_gga(rs, z, xt, xs0, xs1)

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  tpss_f0 = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: +tpss_par(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) + tpss_perp(f_gga, rs, z, xt, xs0, xs1, ts0, ts1)

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  tpss_f = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: +tpss_f0(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) * (1 + params_d * tpss_f0(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) * tpss_aux(z, xt, ts0, ts1) ** 3)

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: +tpss_f(f_pbe, rs, z, xt, xs0, xs1, ts0, ts1)

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
  params_C0_c_raw = params.C0_c
  if isinstance(params_C0_c_raw, (str, bytes, dict)):
    params_C0_c = params_C0_c_raw
  else:
    try:
      params_C0_c_seq = list(params_C0_c_raw)
    except TypeError:
      params_C0_c = params_C0_c_raw
    else:
      params_C0_c_seq = np.asarray(params_C0_c_seq, dtype=np.float64)
      params_C0_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_C0_c_seq))
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  beta_a = 0.06672455060314922

  beta_b = 0.1

  beta_c = 0.1778

  tpss_xi2 = lambda z, xt, xs0, xs1: (1 - z ** 2) * (f.t_total(z, xs0 ** 2, xs1 ** 2) - xt ** 2) / (2 * (3 * jnp.pi ** 2) ** (1 / 3)) ** 2

  tpss_C00 = lambda cc, z: +jnp.sum(jnp.array([cc[i] * z ** (2 * (i - 1)) for i in range(1, 4 + 1)]), axis=0)

  tpss_aux = lambda z, xt, ts0, ts1: jnp.minimum(xt ** 2 / (8 * f.t_total(z, ts0, ts1)), 1)

  tpss_par_s0 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 + z)) ** (1 / 3), 1, xs0, xs0, 0), f_gga(rs, z, xt, xs0, xs1)) * (1 + z) / 2

  tpss_par_s1 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 - z)) ** (1 / 3), -1, xs1, 0, xs1), f_gga(rs, z, xt, xs0, xs1)) * (1 - z) / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  mgamma = params_gamma

  BB = params_BB

  mbeta = lambda rs, t=None: beta_a * (1 + beta_b * rs) / (1 + beta_c * rs)

  tpss_C0_den = lambda z, xt, xs0, xs1: 1 + tpss_xi2(z, xt, xs0, xs1) * ((1 + z) ** (-4 / 3) + (1 - z) ** (-4 / 3)) / 2

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  tpss_C0 = lambda cc, z, xt, xs0, xs1: f.my_piecewise3(1 - jnp.abs(z) <= 1e-12, jnp.sum(jnp.array([cc[i] for i in range(1, 4 + 1)]), axis=0), tpss_C00(cc, z) / tpss_C0_den(f.z_thr(z), xt, xs0, xs1) ** 4)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  tpss_par = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: -(1 + tpss_C0(params_C0_c, z, xt, xs0, xs1)) * tpss_aux(z, xt, ts0, ts1) ** 2 * (+f.my_piecewise3(f.screen_dens_zeta(rs, z), f_gga(rs, f.z_thr(z), xt, xs0, xs1) * (1 + z) / 2, tpss_par_s0(f_gga, rs, f.z_thr(z), xt, xs0, xs1)) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), f_gga(rs, f.z_thr(z), xt, xs0, xs1) * (1 - z) / 2, tpss_par_s1(f_gga, rs, f.z_thr(z), xt, xs0, xs1)))

  tpss_perp = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: (1 + tpss_C0(params_C0_c, z, xt, xs0, xs1) * tpss_aux(z, xt, ts0, ts1) ** 2) * f_gga(rs, z, xt, xs0, xs1)

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  tpss_f0 = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: +tpss_par(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) + tpss_perp(f_gga, rs, z, xt, xs0, xs1, ts0, ts1)

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  tpss_f = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: +tpss_f0(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) * (1 + params_d * tpss_f0(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) * tpss_aux(z, xt, ts0, ts1) ** 3)

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: +tpss_f(f_pbe, rs, z, xt, xs0, xs1, ts0, ts1)

  t1 = r0 - r1
  t2 = r0 + r1
  t3 = 0.1e1 / t2
  t4 = t1 * t3
  t6 = f.my_piecewise3(0.0e0 < t4, t4, -t4)
  t7 = -t6 <= -0.999999999999e0
  t8 = params.C0_c[0]
  t9 = params.C0_c[1]
  t10 = params.C0_c[2]
  t11 = params.C0_c[3]
  t13 = t1 ** 2
  t14 = t9 * t13
  t15 = t2 ** 2
  t16 = 0.1e1 / t15
  t18 = t13 ** 2
  t19 = t10 * t18
  t20 = t15 ** 2
  t21 = 0.1e1 / t20
  t24 = t11 * t18 * t13
  t26 = 0.1e1 / t20 / t15
  t28 = t14 * t16 + t19 * t21 + t24 * t26 + t8
  t29 = 0.1e1 + t4
  t30 = t29 <= f.p.zeta_threshold
  t31 = f.p.zeta_threshold - 0.1e1
  t32 = 0.1e1 - t4
  t33 = t32 <= f.p.zeta_threshold
  t35 = f.my_piecewise5(t30, t31, t33, -t31, t4)
  t36 = t35 ** 2
  t37 = 0.1e1 - t36
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t43 = s0 * t42
  t44 = 0.1e1 + t35
  t45 = t44 / 0.2e1
  t46 = t45 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = t47 * t45
  t50 = r1 ** 2
  t51 = r1 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t54 = 0.1e1 / t52 / t50
  t55 = s2 * t54
  t56 = 0.1e1 - t35
  t57 = t56 / 0.2e1
  t58 = t57 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t60 = t59 * t57
  t63 = s0 + 0.2e1 * s1 + s2
  t64 = t2 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t67 = 0.1e1 / t65 / t15
  t68 = t63 * t67
  t69 = t43 * t48 + t55 * t60 - t68
  t70 = t37 * t69
  t71 = 3 ** (0.1e1 / 0.3e1)
  t72 = jnp.pi ** 2
  t73 = t72 ** (0.1e1 / 0.3e1)
  t74 = t73 ** 2
  t75 = 0.1e1 / t74
  t76 = t71 * t75
  t77 = t44 ** (0.1e1 / 0.3e1)
  t78 = t77 * t44
  t80 = t56 ** (0.1e1 / 0.3e1)
  t81 = t80 * t56
  t83 = 0.1e1 / t78 + 0.1e1 / t81
  t84 = t76 * t83
  t87 = 0.1e1 + t70 * t84 / 0.24e2
  t88 = t87 ** 2
  t89 = t88 ** 2
  t90 = 0.1e1 / t89
  t92 = f.my_piecewise3(t7, t8 + t9 + t10 + t11, t28 * t90)
  t93 = 0.1e1 + t92
  t95 = 0.1e1 / t40 / r0
  t96 = tau0 * t95
  t97 = t29 / 0.2e1
  t98 = t97 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t100 = t99 * t97
  t103 = 0.1e1 / t52 / r1
  t104 = tau1 * t103
  t105 = t32 / 0.2e1
  t106 = t105 ** (0.1e1 / 0.3e1)
  t107 = t106 ** 2
  t108 = t107 * t105
  t111 = 0.8e1 * t96 * t100 + 0.8e1 * t104 * t108
  t112 = 0.1e1 / t111
  t113 = t68 * t112
  t114 = 0.1e1 < t113
  t115 = f.my_piecewise3(t114, 1, t113)
  t116 = t115 ** 2
  t117 = t93 * t116
  t119 = jnp.logical_or(r0 <= f.p.dens_threshold, t30)
  t121 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t122 = t71 * t121
  t123 = 4 ** (0.1e1 / 0.3e1)
  t124 = t123 ** 2
  t125 = 0.1e1 / t64
  t127 = t122 * t124 * t125
  t129 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t127
  t130 = jnp.sqrt(t127)
  t133 = t127 ** 0.15e1
  t135 = t71 ** 2
  t136 = t121 ** 2
  t137 = t135 * t136
  t138 = 0.1e1 / t65
  t140 = t137 * t123 * t138
  t142 = 0.23615562999000000000000000000000000000000000000000e0 * t130 + 0.55770497660000000000000000000000000000000000000000e-1 * t127 + 0.12733196185000000000000000000000000000000000000000e-1 * t133 + 0.76629248290000000000000000000000000000000000000000e-2 * t140
  t144 = 0.1e1 + 0.1e1 / t142
  t145 = jnp.log(t144)
  t146 = t129 * t145
  t147 = t36 ** 2
  t148 = t44 <= f.p.zeta_threshold
  t149 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t150 = t149 * f.p.zeta_threshold
  t151 = f.my_piecewise3(t148, t150, t78)
  t152 = t56 <= f.p.zeta_threshold
  t153 = f.my_piecewise3(t152, t150, t81)
  t154 = t151 + t153 - 0.2e1
  t155 = t147 * t154
  t156 = 2 ** (0.1e1 / 0.3e1)
  t159 = 0.1e1 / (0.2e1 * t156 - 0.2e1)
  t161 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t127
  t166 = 0.21948324211500000000000000000000000000000000000000e0 * t130 + 0.48172707847500000000000000000000000000000000000000e-1 * t127 + 0.13082189292500000000000000000000000000000000000000e-1 * t133 + 0.48592432297500000000000000000000000000000000000000e-2 * t140
  t168 = 0.1e1 + 0.1e1 / t166
  t169 = jnp.log(t168)
  t172 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t127
  t177 = 0.17489762330000000000000000000000000000000000000000e0 * t130 + 0.30591463695000000000000000000000000000000000000000e-1 * t127 + 0.37162156485000000000000000000000000000000000000000e-2 * t133 + 0.41939460495000000000000000000000000000000000000000e-2 * t140
  t179 = 0.1e1 + 0.1e1 / t177
  t180 = jnp.log(t179)
  t181 = t172 * t180
  t183 = -t161 * t169 + t146 - 0.58482236226346462072622386637590534819724553404281e0 * t181
  t184 = t159 * t183
  t185 = t155 * t184
  t186 = t154 * t159
  t188 = 0.58482236226346462072622386637590534819724553404281e0 * t186 * t181
  t189 = jnp.log(0.2e1)
  t190 = 0.1e1 - t189
  t191 = 0.1e1 / t72
  t192 = t190 * t191
  t193 = t149 ** 2
  t194 = t77 ** 2
  t195 = f.my_piecewise3(t148, t193, t194)
  t196 = t80 ** 2
  t197 = f.my_piecewise3(t152, t193, t196)
  t199 = t195 / 0.2e1 + t197 / 0.2e1
  t200 = t199 ** 2
  t201 = t200 * t199
  t203 = 0.66724550603149220e-1 + 0.16681137650787305000000000000000000000000000000000e-2 * t127
  t205 = 0.1e1 + 0.44450000000000000000000000000000000000000000000000e-1 * t127
  t206 = 0.1e1 / t205
  t207 = t203 * t206
  t209 = 0.1e1 / t64 / t15
  t210 = t63 * t209
  t211 = t210 * t156
  t212 = 0.1e1 / t200
  t214 = 0.1e1 / t121
  t215 = t214 * t123
  t216 = t212 * t135 * t215
  t219 = 0.1e1 / t190
  t220 = t207 * t219
  t222 = (-t146 + t185 + t188) * t219
  t223 = 0.1e1 / t201
  t224 = t72 * t223
  t226 = jnp.exp(-t222 * t224)
  t227 = t226 - 0.1e1
  t228 = 0.1e1 / t227
  t229 = t72 * t228
  t230 = t63 ** 2
  t231 = t229 * t230
  t232 = t220 * t231
  t234 = 0.1e1 / t65 / t20
  t235 = t156 ** 2
  t236 = t234 * t235
  t237 = t200 ** 2
  t238 = 0.1e1 / t237
  t240 = 0.1e1 / t136
  t241 = t71 * t240
  t242 = t241 * t124
  t243 = t236 * t238 * t242
  t246 = t211 * t216 / 0.96e2 + t232 * t243 / 0.3072e4
  t247 = t207 * t246
  t248 = t219 * t72
  t249 = t229 * t246
  t251 = t220 * t249 + 0.1e1
  t252 = 0.1e1 / t251
  t253 = t248 * t252
  t255 = t247 * t253 + 0.1e1
  t256 = jnp.log(t255)
  t259 = t192 * t201 * t256 - t146 + t185 + t188
  t262 = t122 * t124
  t263 = t125 * t156
  t264 = 0.1e1 / t44
  t265 = t264 ** (0.1e1 / 0.3e1)
  t267 = t262 * t263 * t265
  t269 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t267
  t270 = jnp.sqrt(t267)
  t273 = t267 ** 0.15e1
  t275 = t137 * t123
  t276 = t138 * t235
  t277 = t265 ** 2
  t279 = t275 * t276 * t277
  t281 = 0.23615562999000000000000000000000000000000000000000e0 * t270 + 0.55770497660000000000000000000000000000000000000000e-1 * t267 + 0.12733196185000000000000000000000000000000000000000e-1 * t273 + 0.76629248290000000000000000000000000000000000000000e-2 * t279
  t283 = 0.1e1 + 0.1e1 / t281
  t284 = jnp.log(t283)
  t285 = t269 * t284
  t286 = 0.2e1 <= f.p.zeta_threshold
  t288 = f.my_piecewise3(t286, t150, 0.2e1 * t156)
  t289 = 0.0e0 <= f.p.zeta_threshold
  t290 = f.my_piecewise3(t289, t150, 0)
  t292 = (t288 + t290 - 0.2e1) * t159
  t294 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t267
  t299 = 0.21948324211500000000000000000000000000000000000000e0 * t270 + 0.48172707847500000000000000000000000000000000000000e-1 * t267 + 0.13082189292500000000000000000000000000000000000000e-1 * t273 + 0.48592432297500000000000000000000000000000000000000e-2 * t279
  t301 = 0.1e1 + 0.1e1 / t299
  t302 = jnp.log(t301)
  t305 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t267
  t310 = 0.17489762330000000000000000000000000000000000000000e0 * t270 + 0.30591463695000000000000000000000000000000000000000e-1 * t267 + 0.37162156485000000000000000000000000000000000000000e-2 * t273 + 0.41939460495000000000000000000000000000000000000000e-2 * t279
  t312 = 0.1e1 + 0.1e1 / t310
  t313 = jnp.log(t312)
  t314 = t305 * t313
  t317 = t292 * (-t294 * t302 + t285 - 0.58482236226346462072622386637590534819724553404281e0 * t314)
  t319 = 0.58482236226346462072622386637590534819724553404281e0 * t292 * t314
  t320 = f.my_piecewise3(t286, t193, t235)
  t321 = f.my_piecewise3(t289, t193, 0)
  t323 = t320 / 0.2e1 + t321 / 0.2e1
  t324 = t323 ** 2
  t325 = t324 * t323
  t327 = 0.66724550603149220e-1 + 0.16681137650787305000000000000000000000000000000000e-2 * t267
  t329 = 0.1e1 + 0.44450000000000000000000000000000000000000000000000e-1 * t267
  t330 = 0.1e1 / t329
  t331 = t327 * t330
  t332 = 0.1e1 / t324
  t333 = t332 * t135
  t334 = t43 * t333
  t335 = 0.1e1 / t265
  t337 = t215 * t64 * t335
  t340 = t331 * t219
  t343 = 0.1e1 / t325
  t344 = t72 * t343
  t346 = jnp.exp(-(-t285 + t317 + t319) * t219 * t344)
  t347 = t346 - 0.1e1
  t348 = 0.1e1 / t347
  t349 = t72 * t348
  t350 = s0 ** 2
  t351 = t349 * t350
  t352 = t340 * t351
  t353 = t38 ** 2
  t356 = 0.1e1 / t39 / t353 / r0
  t357 = t324 ** 2
  t358 = 0.1e1 / t357
  t360 = t356 * t358 * t71
  t361 = t240 * t124
  t362 = 0.1e1 / t277
  t363 = t65 * t362
  t364 = t361 * t363
  t365 = t360 * t364
  t368 = t334 * t337 / 0.96e2 + t352 * t365 / 0.3072e4
  t369 = t331 * t368
  t370 = t349 * t368
  t372 = t340 * t370 + 0.1e1
  t373 = 0.1e1 / t372
  t374 = t248 * t373
  t376 = t369 * t374 + 0.1e1
  t377 = jnp.log(t376)
  t380 = t192 * t325 * t377 - t285 + t317 + t319
  t381 = t259 < t380
  t382 = f.my_piecewise3(t381, t380, t259)
  t385 = f.my_piecewise3(t119, t259 * t29 / 0.2e1, t382 * t44 / 0.2e1)
  t387 = jnp.logical_or(r1 <= f.p.dens_threshold, t33)
  t390 = 0.1e1 / t56
  t391 = t390 ** (0.1e1 / 0.3e1)
  t393 = t262 * t263 * t391
  t395 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t393
  t396 = jnp.sqrt(t393)
  t399 = t393 ** 0.15e1
  t401 = t391 ** 2
  t403 = t275 * t276 * t401
  t405 = 0.23615562999000000000000000000000000000000000000000e0 * t396 + 0.55770497660000000000000000000000000000000000000000e-1 * t393 + 0.12733196185000000000000000000000000000000000000000e-1 * t399 + 0.76629248290000000000000000000000000000000000000000e-2 * t403
  t407 = 0.1e1 + 0.1e1 / t405
  t408 = jnp.log(t407)
  t409 = t395 * t408
  t411 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t393
  t416 = 0.21948324211500000000000000000000000000000000000000e0 * t396 + 0.48172707847500000000000000000000000000000000000000e-1 * t393 + 0.13082189292500000000000000000000000000000000000000e-1 * t399 + 0.48592432297500000000000000000000000000000000000000e-2 * t403
  t418 = 0.1e1 + 0.1e1 / t416
  t419 = jnp.log(t418)
  t422 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t393
  t427 = 0.17489762330000000000000000000000000000000000000000e0 * t396 + 0.30591463695000000000000000000000000000000000000000e-1 * t393 + 0.37162156485000000000000000000000000000000000000000e-2 * t399 + 0.41939460495000000000000000000000000000000000000000e-2 * t403
  t429 = 0.1e1 + 0.1e1 / t427
  t430 = jnp.log(t429)
  t431 = t422 * t430
  t434 = t292 * (-t411 * t419 + t409 - 0.58482236226346462072622386637590534819724553404281e0 * t431)
  t436 = 0.58482236226346462072622386637590534819724553404281e0 * t292 * t431
  t438 = 0.66724550603149220e-1 + 0.16681137650787305000000000000000000000000000000000e-2 * t393
  t440 = 0.1e1 + 0.44450000000000000000000000000000000000000000000000e-1 * t393
  t441 = 0.1e1 / t440
  t442 = t438 * t441
  t443 = t55 * t333
  t444 = 0.1e1 / t391
  t446 = t215 * t64 * t444
  t449 = t442 * t219
  t453 = jnp.exp(-(-t409 + t434 + t436) * t219 * t344)
  t454 = t453 - 0.1e1
  t455 = 0.1e1 / t454
  t456 = t72 * t455
  t457 = s2 ** 2
  t458 = t456 * t457
  t459 = t449 * t458
  t460 = t50 ** 2
  t463 = 0.1e1 / t51 / t460 / r1
  t465 = t463 * t358 * t71
  t466 = 0.1e1 / t401
  t467 = t65 * t466
  t468 = t361 * t467
  t469 = t465 * t468
  t472 = t443 * t446 / 0.96e2 + t459 * t469 / 0.3072e4
  t473 = t442 * t472
  t474 = t456 * t472
  t476 = t449 * t474 + 0.1e1
  t477 = 0.1e1 / t476
  t478 = t248 * t477
  t480 = t473 * t478 + 0.1e1
  t481 = jnp.log(t480)
  t484 = t192 * t325 * t481 - t409 + t434 + t436
  t485 = t259 < t484
  t486 = f.my_piecewise3(t485, t484, t259)
  t489 = f.my_piecewise3(t387, t259 * t32 / 0.2e1, t486 * t56 / 0.2e1)
  t490 = t385 + t489
  t493 = t92 * t116 + 0.1e1
  t494 = t18 * t21
  t495 = t29 ** (0.1e1 / 0.3e1)
  t497 = f.my_piecewise3(t30, t150, t495 * t29)
  t498 = t32 ** (0.1e1 / 0.3e1)
  t500 = f.my_piecewise3(t33, t150, t498 * t32)
  t502 = (t497 + t500 - 0.2e1) * t159
  t503 = t502 * t183
  t504 = t494 * t503
  t506 = 0.58482236226346462072622386637590534819724553404281e0 * t502 * t181
  t507 = t495 ** 2
  t508 = f.my_piecewise3(t30, t193, t507)
  t509 = t498 ** 2
  t510 = f.my_piecewise3(t33, t193, t509)
  t512 = t508 / 0.2e1 + t510 / 0.2e1
  t513 = t512 ** 2
  t514 = t513 * t512
  t515 = 0.1e1 / t513
  t517 = t515 * t135 * t215
  t521 = (-t146 + t504 + t506) * t219
  t522 = 0.1e1 / t514
  t523 = t72 * t522
  t525 = jnp.exp(-t521 * t523)
  t526 = t525 - 0.1e1
  t527 = 0.1e1 / t526
  t528 = t72 * t527
  t529 = t528 * t230
  t530 = t220 * t529
  t531 = t513 ** 2
  t532 = 0.1e1 / t531
  t534 = t236 * t532 * t242
  t537 = t211 * t517 / 0.96e2 + t530 * t534 / 0.3072e4
  t538 = t207 * t537
  t539 = t528 * t537
  t541 = t220 * t539 + 0.1e1
  t542 = 0.1e1 / t541
  t543 = t248 * t542
  t545 = t538 * t543 + 0.1e1
  t546 = jnp.log(t545)
  t549 = t192 * t514 * t546 - t146 + t504 + t506
  t551 = -t117 * t490 + t493 * t549
  t552 = params.d * t551
  t553 = t116 * t115
  t555 = t552 * t553 + 0.1e1
  t556 = t551 * t555
  t559 = 0.2e1 * t9 * t1 * t16
  t560 = t15 * t2
  t563 = 0.2e1 * t14 / t560
  t564 = t13 * t1
  t567 = 0.4e1 * t10 * t564 * t21
  t568 = t20 * t2
  t569 = 0.1e1 / t568
  t571 = 0.4e1 * t19 * t569
  t575 = 0.6e1 * t11 * t18 * t1 * t26
  t579 = 0.6e1 * t24 / t20 / t560
  t584 = t28 / t89 / t87
  t585 = t1 * t16
  t586 = t3 - t585
  t587 = f.my_piecewise5(t30, 0, t33, 0, t586)
  t595 = s0 / t40 / t38 / r0
  t606 = t63 / t65 / t560
  t607 = 0.8e1 / 0.3e1 * t606
  t612 = t44 ** 2
  t614 = 0.1e1 / t77 / t612
  t616 = t56 ** 2
  t618 = 0.1e1 / t80 / t616
  t629 = f.my_piecewise3(t7, 0, (t559 - t563 + t567 - t571 + t575 - t579) * t90 - 0.4e1 * t584 * (-t35 * t587 * t69 * t84 / 0.12e2 + t37 * (-0.8e1 / 0.3e1 * t595 * t48 + 0.5e1 / 0.6e1 * t43 * t47 * t587 - 0.5e1 / 0.6e1 * t55 * t59 * t587 + t607) * t84 / 0.24e2 + t70 * t76 * (-0.4e1 / 0.3e1 * t614 * t587 + 0.4e1 / 0.3e1 * t618 * t587) / 0.24e2))
  t630 = t629 * t116
  t632 = t93 * t115
  t634 = 0.8e1 / 0.3e1 * t606 * t112
  t635 = t111 ** 2
  t636 = 0.1e1 / t635
  t639 = t586 / 0.2e1
  t650 = f.my_piecewise3(t114, 0, -t634 - t68 * t636 * (-0.40e2 / 0.3e1 * tau0 * t42 * t100 - 0.40e2 / 0.3e1 * t104 * t107 * t639 + 0.40e2 / 0.3e1 * t96 * t99 * t639))
  t655 = 0.1e1 / t64 / t2
  t656 = t124 * t655
  t659 = 0.11073470983333333333333333333333333333333333333333e-2 * t122 * t656 * t145
  t660 = t142 ** 2
  t665 = t121 * t124
  t666 = t665 * t655
  t667 = 0.1e1 / t130 * t71 * t666
  t669 = t122 * t656
  t671 = t127 ** 0.5e0
  t673 = t671 * t71 * t666
  t676 = 0.1e1 / t65 / t2
  t678 = t137 * t123 * t676
  t683 = t129 / t660 * (-0.39359271665000000000000000000000000000000000000000e-1 * t667 - 0.18590165886666666666666666666666666666666666666667e-1 * t669 - 0.63665980925000000000000000000000000000000000000000e-2 * t673 - 0.51086165526666666666666666666666666666666666666667e-2 * t678) / t144
  t685 = t36 * t35 * t154
  t688 = 0.4e1 * t685 * t184 * t587
  t691 = f.my_piecewise3(t148, 0, 0.4e1 / 0.3e1 * t77 * t587)
  t694 = f.my_piecewise3(t152, 0, -0.4e1 / 0.3e1 * t80 * t587)
  t695 = t691 + t694
  t697 = t147 * t695 * t184
  t701 = t166 ** 2
  t715 = t177 ** 2
  t716 = 0.1e1 / t715
  t722 = -0.29149603883333333333333333333333333333333333333333e-1 * t667 - 0.10197154565000000000000000000000000000000000000000e-1 * t669 - 0.18581078242500000000000000000000000000000000000000e-2 * t673 - 0.27959640330000000000000000000000000000000000000000e-2 * t678
  t723 = 0.1e1 / t179
  t727 = 0.53237641966666666666666666666666666666666666666667e-3 * t122 * t656 * t169 + t161 / t701 * (-0.36580540352500000000000000000000000000000000000000e-1 * t667 - 0.16057569282500000000000000000000000000000000000000e-1 * t669 - 0.65410946462500000000000000000000000000000000000000e-2 * t673 - 0.32394954865000000000000000000000000000000000000000e-2 * t678) / t168 - t659 - t683 + 0.18311447306006545054854346104378990962041954983034e-3 * t122 * t656 * t180 + 0.58482236226346462072622386637590534819724553404281e0 * t172 * t716 * t722 * t723
  t729 = t155 * t159 * t727
  t732 = 0.58482236226346462072622386637590534819724553404281e0 * t695 * t159 * t181
  t735 = t665 * t655 * t180
  t737 = 0.18311447306006545054854346104378990962041954983034e-3 * t186 * t71 * t735
  t740 = t716 * t722 * t723
  t742 = 0.58482236226346462072622386637590534819724553404281e0 * t186 * t172 * t740
  t743 = t200 * t256
  t744 = 0.1e1 / t77
  t747 = f.my_piecewise3(t148, 0, 0.2e1 / 0.3e1 * t744 * t587)
  t748 = 0.1e1 / t80
  t751 = f.my_piecewise3(t152, 0, -0.2e1 / 0.3e1 * t748 * t587)
  t753 = t747 / 0.2e1 + t751 / 0.2e1
  t760 = 0.55603792169291016666666666666666666666666666666667e-3 * t669 * t206 * t246 * t253
  t761 = t205 ** 2
  t762 = 0.1e1 / t761
  t763 = t203 * t762
  t770 = 0.14816666666666666666666666666666666666666666666667e-1 * t763 * t246 * t219 * t72 * t252 * t71 * t666
  t774 = t63 / t64 / t560 * t156
  t776 = 0.7e1 / 0.288e3 * t774 * t216
  t778 = t210 * t156 * t223
  t779 = t135 * t214
  t786 = t779 * t123 * t26 * t206
  t787 = t248 * t228
  t788 = t230 * t235
  t792 = 0.72400771053764344618055555555555555555555555555557e-6 * t786 * t787 * t788 * t238
  t793 = t763 * t219
  t795 = t26 * t235
  t797 = t779 * t123
  t800 = 0.19292534722222222222222222222222222222222222222223e-4 * t793 * t231 * t795 * t238 * t797
  t801 = t227 ** 2
  t802 = 0.1e1 / t801
  t804 = t230 * t234
  t806 = t220 * t72 * t802 * t804
  t808 = t235 * t238 * t71
  t812 = t72 * t238
  t817 = (-(t659 + t683 + t688 + t697 + t729 + t732 - t737 - t742) * t219 * t224 + 0.3e1 * t222 * t812 * t753) * t226
  t824 = 0.1e1 / t65 / t568 * t235
  t828 = 0.7e1 / 0.4608e4 * t232 * t824 * t238 * t242
  t831 = t236 / t237 / t199
  t837 = -t776 - t778 * t779 * t123 * t753 / 0.48e2 - t792 + t800 - t806 * t808 * t361 * t817 / 0.3072e4 - t828 - t232 * t831 * t241 * t124 * t753 / 0.768e3
  t840 = t251 ** 2
  t841 = 0.1e1 / t840
  t842 = t206 * t219
  t845 = 0.55603792169291016666666666666666666666666666666667e-3 * t669 * t842 * t249
  t850 = 0.14816666666666666666666666666666666666666666666667e-1 * t763 * t787 * t246 * t71 * t666
  t851 = t207 * t248
  t852 = t802 * t246
  t863 = 0.1e1 / t255
  t866 = t659 + t683 + t688 + t697 + t729 + t732 - t737 - t742 + 0.3e1 * t192 * t743 * t753 + t192 * t201 * (-t760 + t770 + t207 * t837 * t253 - t247 * t248 * t841 * (t220 * t229 * t837 - t851 * t852 * t817 - t845 + t850)) * t863
  t871 = t655 * t156
  t873 = t262 * t871 * t265
  t874 = 0.11073470983333333333333333333333333333333333333333e-2 * t873
  t875 = t156 * t362
  t876 = 0.1e1 / t612
  t877 = t876 * t587
  t879 = t127 * t875 * t877
  t882 = (-t874 - 0.11073470983333333333333333333333333333333333333333e-2 * t879) * t284
  t883 = t281 ** 2
  t885 = t269 / t883
  t886 = 0.1e1 / t270
  t888 = -t873 / 0.3e1 - t879 / 0.3e1
  t889 = t886 * t888
  t891 = 0.18590165886666666666666666666666666666666666666667e-1 * t873
  t893 = t267 ** 0.5e0
  t894 = t893 * t888
  t896 = t676 * t235
  t898 = t275 * t896 * t277
  t899 = 0.51086165526666666666666666666666666666666666666667e-2 * t898
  t900 = t235 * t335
  t902 = t140 * t900 * t877
  t905 = 0.1e1 / t283
  t907 = t885 * (0.11807781499500000000000000000000000000000000000000e0 * t889 - t891 - 0.18590165886666666666666666666666666666666666666667e-1 * t879 + 0.19099794277500000000000000000000000000000000000000e-1 * t894 - t899 - 0.51086165526666666666666666666666666666666666666667e-2 * t902) * t905
  t908 = 0.53237641966666666666666666666666666666666666666667e-3 * t873
  t912 = t299 ** 2
  t914 = t294 / t912
  t916 = 0.16057569282500000000000000000000000000000000000000e-1 * t873
  t919 = 0.32394954865000000000000000000000000000000000000000e-2 * t898
  t922 = 0.1e1 / t301
  t925 = 0.31311127083333333333333333333333333333333333333333e-3 * t873
  t928 = (-t925 - 0.31311127083333333333333333333333333333333333333333e-3 * t879) * t313
  t930 = t310 ** 2
  t931 = 0.1e1 / t930
  t932 = t305 * t931
  t934 = 0.10197154565000000000000000000000000000000000000000e-1 * t873
  t937 = 0.27959640330000000000000000000000000000000000000000e-2 * t898
  t939 = 0.87448811650000000000000000000000000000000000000000e-1 * t889 - t934 - 0.10197154565000000000000000000000000000000000000000e-1 * t879 + 0.55743234727500000000000000000000000000000000000000e-2 * t894 - t937 - 0.27959640330000000000000000000000000000000000000000e-2 * t902
  t940 = 0.1e1 / t312
  t945 = t292 * (-(-t908 - 0.53237641966666666666666666666666666666666666666667e-3 * t879) * t302 + t914 * (0.10974162105750000000000000000000000000000000000000e0 * t889 - t916 - 0.16057569282500000000000000000000000000000000000000e-1 * t879 + 0.19623283938750000000000000000000000000000000000000e-1 * t894 - t919 - 0.32394954865000000000000000000000000000000000000000e-2 * t902) * t922 + t882 - t907 - 0.58482236226346462072622386637590534819724553404281e0 * t928 + 0.58482236226346462072622386637590534819724553404281e0 * t932 * t939 * t940)
  t947 = 0.58482236226346462072622386637590534819724553404281e0 * t292 * t928
  t948 = t292 * t305
  t952 = 0.58482236226346462072622386637590534819724553404281e0 * t948 * t931 * t939 * t940
  t953 = 0.55603792169291016666666666666666666666666666666667e-3 * t873
  t956 = (-t953 - 0.55603792169291016666666666666666666666666666666667e-3 * t879) * t330
  t959 = t329 ** 2
  t960 = 0.1e1 / t959
  t961 = t327 * t960
  t962 = t961 * t368
  t963 = 0.14816666666666666666666666666666666666666666666667e-1 * t873
  t965 = -t963 - 0.14816666666666666666666666666666666666666666666667e-1 * t879
  t975 = t334 * t215 * t138 * t335 / 0.288e3
  t976 = t333 * t214
  t977 = t43 * t976
  t978 = t123 * t64
  t981 = 0.1e1 / t265 / t264 * t876
  t986 = t956 * t219
  t990 = t961 * t219
  t991 = t350 * t356
  t992 = t349 * t991
  t993 = t990 * t992
  t994 = t358 * t71
  t995 = t994 * t240
  t996 = t124 * t65
  t1002 = t190 ** 2
  t1003 = 0.1e1 / t1002
  t1005 = t72 ** 2
  t1006 = t347 ** 2
  t1007 = 0.1e1 / t1006
  t1010 = t331 * t1003 * t1005 * t1007 * t991
  t1014 = 0.1e1 / t357 / t325 * t71 * t361
  t1015 = -t882 + t907 + t945 + t947 - t952
  t1033 = t352 * t360 * t361 * t125 * t362 / 0.4608e4
  t1034 = t340 * t992
  t1035 = t994 * t361
  t1038 = t65 / t277 / t264
  t1043 = -t595 * t333 * t337 / 0.36e2 + t975 + t977 * t978 * t981 * t587 / 0.288e3 + t986 * t351 * t365 / 0.3072e4 - t993 * t995 * t996 * t362 * t965 / 0.3072e4 + t1010 * t1014 * t363 * t1015 * t346 / 0.3072e4 - t352 / t39 / t353 / t38 * t358 * t71 * t364 / 0.576e3 + t1033 + t1034 * t1035 * t1038 * t877 / 0.4608e4
  t1046 = t372 ** 2
  t1047 = 0.1e1 / t1046
  t1052 = t1003 * t1005
  t1053 = t331 * t1052
  t1054 = t1007 * t368
  t1067 = 0.1e1 / t376
  t1071 = f.my_piecewise3(t381, -t882 + t907 + t945 + t947 - t952 + t192 * t325 * (t956 * t368 * t374 - t962 * t248 * t373 * t965 + t331 * t1043 * t374 - t369 * t248 * t1047 * (t1053 * t1054 * t1015 * t343 * t346 - t990 * t349 * t368 * t965 + t340 * t349 * t1043 + t986 * t370)) * t1067, t866)
  t1076 = f.my_piecewise3(t119, t259 * t586 / 0.2e1 + t866 * t29 / 0.2e1, t1071 * t44 / 0.2e1 + t382 * t587 / 0.2e1)
  t1078 = -t586
  t1083 = t262 * t871 * t391
  t1084 = 0.11073470983333333333333333333333333333333333333333e-2 * t1083
  t1085 = t156 * t466
  t1086 = 0.1e1 / t616
  t1087 = t1086 * t587
  t1089 = t127 * t1085 * t1087
  t1092 = (-t1084 + 0.11073470983333333333333333333333333333333333333333e-2 * t1089) * t408
  t1093 = t405 ** 2
  t1095 = t395 / t1093
  t1096 = 0.1e1 / t396
  t1098 = -t1083 / 0.3e1 + t1089 / 0.3e1
  t1099 = t1096 * t1098
  t1101 = 0.18590165886666666666666666666666666666666666666667e-1 * t1083
  t1103 = t393 ** 0.5e0
  t1104 = t1103 * t1098
  t1107 = t275 * t896 * t401
  t1108 = 0.51086165526666666666666666666666666666666666666667e-2 * t1107
  t1109 = t235 * t444
  t1111 = t140 * t1109 * t1087
  t1114 = 0.1e1 / t407
  t1116 = t1095 * (0.11807781499500000000000000000000000000000000000000e0 * t1099 - t1101 + 0.18590165886666666666666666666666666666666666666667e-1 * t1089 + 0.19099794277500000000000000000000000000000000000000e-1 * t1104 - t1108 + 0.51086165526666666666666666666666666666666666666667e-2 * t1111) * t1114
  t1117 = 0.53237641966666666666666666666666666666666666666667e-3 * t1083
  t1121 = t416 ** 2
  t1123 = t411 / t1121
  t1125 = 0.16057569282500000000000000000000000000000000000000e-1 * t1083
  t1128 = 0.32394954865000000000000000000000000000000000000000e-2 * t1107
  t1131 = 0.1e1 / t418
  t1134 = 0.31311127083333333333333333333333333333333333333333e-3 * t1083
  t1137 = (-t1134 + 0.31311127083333333333333333333333333333333333333333e-3 * t1089) * t430
  t1139 = t427 ** 2
  t1140 = 0.1e1 / t1139
  t1141 = t422 * t1140
  t1143 = 0.10197154565000000000000000000000000000000000000000e-1 * t1083
  t1146 = 0.27959640330000000000000000000000000000000000000000e-2 * t1107
  t1148 = 0.87448811650000000000000000000000000000000000000000e-1 * t1099 - t1143 + 0.10197154565000000000000000000000000000000000000000e-1 * t1089 + 0.55743234727500000000000000000000000000000000000000e-2 * t1104 - t1146 + 0.27959640330000000000000000000000000000000000000000e-2 * t1111
  t1149 = 0.1e1 / t429
  t1154 = t292 * (-(-t1117 + 0.53237641966666666666666666666666666666666666666667e-3 * t1089) * t419 + t1123 * (0.10974162105750000000000000000000000000000000000000e0 * t1099 - t1125 + 0.16057569282500000000000000000000000000000000000000e-1 * t1089 + 0.19623283938750000000000000000000000000000000000000e-1 * t1104 - t1128 + 0.32394954865000000000000000000000000000000000000000e-2 * t1111) * t1131 + t1092 - t1116 - 0.58482236226346462072622386637590534819724553404281e0 * t1137 + 0.58482236226346462072622386637590534819724553404281e0 * t1141 * t1148 * t1149)
  t1156 = 0.58482236226346462072622386637590534819724553404281e0 * t292 * t1137
  t1157 = t292 * t422
  t1161 = 0.58482236226346462072622386637590534819724553404281e0 * t1157 * t1140 * t1148 * t1149
  t1162 = 0.55603792169291016666666666666666666666666666666667e-3 * t1083
  t1165 = (-t1162 + 0.55603792169291016666666666666666666666666666666667e-3 * t1089) * t441
  t1168 = t440 ** 2
  t1169 = 0.1e1 / t1168
  t1170 = t438 * t1169
  t1171 = t1170 * t472
  t1172 = 0.14816666666666666666666666666666666666666666666667e-1 * t1083
  t1174 = -t1172 + 0.14816666666666666666666666666666666666666666666667e-1 * t1089
  t1181 = t443 * t215 * t138 * t444 / 0.288e3
  t1182 = t55 * t976
  t1185 = 0.1e1 / t391 / t390 * t1086
  t1190 = t1165 * t219
  t1194 = t1170 * t219
  t1195 = t457 * t463
  t1196 = t456 * t1195
  t1197 = t1194 * t1196
  t1204 = t454 ** 2
  t1205 = 0.1e1 / t1204
  t1208 = t442 * t1003 * t1005 * t1205 * t1195
  t1209 = -t1092 + t1116 + t1154 + t1156 - t1161
  t1219 = t459 * t465 * t361 * t125 * t466 / 0.4608e4
  t1220 = t449 * t1196
  t1223 = t65 / t401 / t390
  t1228 = t1181 - t1182 * t978 * t1185 * t587 / 0.288e3 + t1190 * t458 * t469 / 0.3072e4 - t1197 * t995 * t996 * t466 * t1174 / 0.3072e4 + t1208 * t1014 * t467 * t1209 * t453 / 0.3072e4 + t1219 - t1220 * t1035 * t1223 * t1087 / 0.4608e4
  t1231 = t476 ** 2
  t1232 = 0.1e1 / t1231
  t1237 = t442 * t1052
  t1238 = t1205 * t472
  t1251 = 0.1e1 / t480
  t1255 = f.my_piecewise3(t485, -t1092 + t1116 + t1154 + t1156 - t1161 + t192 * t325 * (t1165 * t472 * t478 - t1171 * t248 * t477 * t1174 + t442 * t1228 * t478 - t473 * t248 * t1232 * (t1237 * t1238 * t1209 * t343 * t453 - t1194 * t456 * t472 * t1174 + t449 * t456 * t1228 + t1190 * t474)) * t1251, t866)
  t1260 = f.my_piecewise3(t387, t259 * t1078 / 0.2e1 + t866 * t32 / 0.2e1, t1255 * t56 / 0.2e1 - t486 * t587 / 0.2e1)
  t1263 = t92 * t115
  t1270 = 0.4e1 * t564 * t21 * t503
  t1273 = 0.4e1 * t18 * t569 * t503
  t1276 = f.my_piecewise3(t30, 0, 0.4e1 / 0.3e1 * t495 * t586)
  t1279 = f.my_piecewise3(t33, 0, 0.4e1 / 0.3e1 * t498 * t1078)
  t1281 = (t1276 + t1279) * t159
  t1283 = t494 * t1281 * t183
  t1285 = t494 * t502 * t727
  t1287 = 0.58482236226346462072622386637590534819724553404281e0 * t1281 * t181
  t1290 = 0.18311447306006545054854346104378990962041954983034e-3 * t502 * t71 * t735
  t1293 = 0.58482236226346462072622386637590534819724553404281e0 * t502 * t172 * t740
  t1294 = t513 * t546
  t1295 = 0.1e1 / t495
  t1298 = f.my_piecewise3(t30, 0, 0.2e1 / 0.3e1 * t1295 * t586)
  t1299 = 0.1e1 / t498
  t1302 = f.my_piecewise3(t33, 0, 0.2e1 / 0.3e1 * t1299 * t1078)
  t1304 = t1298 / 0.2e1 + t1302 / 0.2e1
  t1311 = 0.55603792169291016666666666666666666666666666666667e-3 * t669 * t206 * t537 * t543
  t1318 = 0.14816666666666666666666666666666666666666666666667e-1 * t763 * t537 * t219 * t72 * t542 * t71 * t666
  t1320 = 0.7e1 / 0.288e3 * t774 * t517
  t1322 = t210 * t156 * t522
  t1327 = t248 * t527
  t1331 = 0.72400771053764344618055555555555555555555555555557e-6 * t786 * t1327 * t788 * t532
  t1336 = 0.19292534722222222222222222222222222222222222222223e-4 * t793 * t529 * t795 * t532 * t797
  t1337 = t526 ** 2
  t1338 = 0.1e1 / t1337
  t1341 = t220 * t72 * t1338 * t804
  t1343 = t235 * t532 * t71
  t1347 = t72 * t532
  t1352 = (-(t659 + t683 + t1270 - t1273 + t1283 + t1285 + t1287 - t1290 - t1293) * t219 * t523 + 0.3e1 * t521 * t1347 * t1304) * t525
  t1360 = 0.7e1 / 0.4608e4 * t530 * t824 * t532 * t242
  t1363 = t236 / t531 / t512
  t1369 = -t1320 - t1322 * t779 * t123 * t1304 / 0.48e2 - t1331 + t1336 - t1341 * t1343 * t361 * t1352 / 0.3072e4 - t1360 - t530 * t1363 * t241 * t124 * t1304 / 0.768e3
  t1372 = t541 ** 2
  t1373 = 0.1e1 / t1372
  t1376 = 0.55603792169291016666666666666666666666666666666667e-3 * t669 * t842 * t539
  t1381 = 0.14816666666666666666666666666666666666666666666667e-1 * t763 * t1327 * t537 * t71 * t666
  t1382 = t1338 * t537
  t1393 = 0.1e1 / t545
  t1396 = t659 + t683 + t1270 - t1273 + t1283 + t1285 + t1287 - t1290 - t1293 + 0.3e1 * t192 * t1294 * t1304 + t192 * t514 * (-t1311 + t1318 + t207 * t1369 * t543 - t538 * t248 * t1373 * (-t851 * t1382 * t1352 + t220 * t528 * t1369 - t1376 + t1381)) * t1393
  t1398 = -t630 * t490 - 0.2e1 * t632 * t490 * t650 - t117 * (t1076 + t1260) + (0.2e1 * t1263 * t650 + t630) * t549 + t493 * t1396
  t1401 = t2 * t551
  vrho_0_ = t556 + t2 * t1398 * t555 + t1401 * (0.3e1 * t552 * t116 * t650 + params.d * t1398 * t553)
  t1411 = -t3 - t585
  t1412 = f.my_piecewise5(t30, 0, t33, 0, t1411)
  t1423 = s2 / t52 / t50 / r1
  t1444 = f.my_piecewise3(t7, 0, (-t559 - t563 - t567 - t571 - t575 - t579) * t90 - 0.4e1 * t584 * (-t35 * t1412 * t69 * t84 / 0.12e2 + t37 * (0.5e1 / 0.6e1 * t43 * t47 * t1412 - 0.8e1 / 0.3e1 * t1423 * t60 - 0.5e1 / 0.6e1 * t55 * t59 * t1412 + t607) * t84 / 0.24e2 + t70 * t76 * (-0.4e1 / 0.3e1 * t614 * t1412 + 0.4e1 / 0.3e1 * t618 * t1412) / 0.24e2))
  t1445 = t1444 * t116
  t1447 = t1411 / 0.2e1
  t1460 = f.my_piecewise3(t114, 0, -t634 - t68 * t636 * (-0.40e2 / 0.3e1 * t104 * t107 * t1447 - 0.40e2 / 0.3e1 * tau1 * t54 * t108 + 0.40e2 / 0.3e1 * t96 * t99 * t1447))
  t1466 = 0.4e1 * t685 * t184 * t1412
  t1469 = f.my_piecewise3(t148, 0, 0.4e1 / 0.3e1 * t77 * t1412)
  t1472 = f.my_piecewise3(t152, 0, -0.4e1 / 0.3e1 * t80 * t1412)
  t1473 = t1469 + t1472
  t1475 = t147 * t1473 * t184
  t1478 = 0.58482236226346462072622386637590534819724553404281e0 * t1473 * t159 * t181
  t1481 = f.my_piecewise3(t148, 0, 0.2e1 / 0.3e1 * t744 * t1412)
  t1484 = f.my_piecewise3(t152, 0, -0.2e1 / 0.3e1 * t748 * t1412)
  t1486 = t1481 / 0.2e1 + t1484 / 0.2e1
  t1501 = (-(t659 + t683 + t1466 + t1475 + t729 + t1478 - t737 - t742) * t219 * t224 + 0.3e1 * t222 * t812 * t1486) * t226
  t1511 = -t776 - t778 * t779 * t123 * t1486 / 0.48e2 - t792 + t800 - t806 * t808 * t361 * t1501 / 0.3072e4 - t828 - t232 * t831 * t241 * t124 * t1486 / 0.768e3
  t1526 = t659 + t683 + t1466 + t1475 + t729 + t1478 - t737 - t742 + 0.3e1 * t192 * t743 * t1486 + t192 * t201 * (-t760 + t770 + t207 * t1511 * t253 - t247 * t248 * t841 * (-t851 * t852 * t1501 + t220 * t229 * t1511 - t845 + t850)) * t863
  t1531 = t876 * t1412
  t1533 = t127 * t875 * t1531
  t1536 = (-t874 - 0.11073470983333333333333333333333333333333333333333e-2 * t1533) * t284
  t1538 = -t873 / 0.3e1 - t1533 / 0.3e1
  t1539 = t886 * t1538
  t1542 = t893 * t1538
  t1545 = t140 * t900 * t1531
  t1549 = t885 * (0.11807781499500000000000000000000000000000000000000e0 * t1539 - t891 - 0.18590165886666666666666666666666666666666666666667e-1 * t1533 + 0.19099794277500000000000000000000000000000000000000e-1 * t1542 - t899 - 0.51086165526666666666666666666666666666666666666667e-2 * t1545) * t905
  t1562 = (-t925 - 0.31311127083333333333333333333333333333333333333333e-3 * t1533) * t313
  t1568 = 0.87448811650000000000000000000000000000000000000000e-1 * t1539 - t934 - 0.10197154565000000000000000000000000000000000000000e-1 * t1533 + 0.55743234727500000000000000000000000000000000000000e-2 * t1542 - t937 - 0.27959640330000000000000000000000000000000000000000e-2 * t1545
  t1573 = t292 * (-(-t908 - 0.53237641966666666666666666666666666666666666666667e-3 * t1533) * t302 + t914 * (0.10974162105750000000000000000000000000000000000000e0 * t1539 - t916 - 0.16057569282500000000000000000000000000000000000000e-1 * t1533 + 0.19623283938750000000000000000000000000000000000000e-1 * t1542 - t919 - 0.32394954865000000000000000000000000000000000000000e-2 * t1545) * t922 + t1536 - t1549 - 0.58482236226346462072622386637590534819724553404281e0 * t1562 + 0.58482236226346462072622386637590534819724553404281e0 * t932 * t1568 * t940)
  t1575 = 0.58482236226346462072622386637590534819724553404281e0 * t292 * t1562
  t1579 = 0.58482236226346462072622386637590534819724553404281e0 * t948 * t931 * t1568 * t940
  t1582 = (-t953 - 0.55603792169291016666666666666666666666666666666667e-3 * t1533) * t330
  t1586 = -t963 - 0.14816666666666666666666666666666666666666666666667e-1 * t1533
  t1594 = t1582 * t219
  t1603 = -t1536 + t1549 + t1573 + t1575 - t1579
  t1613 = t975 + t977 * t978 * t981 * t1412 / 0.288e3 + t1594 * t351 * t365 / 0.3072e4 - t993 * t995 * t996 * t362 * t1586 / 0.3072e4 + t1010 * t1014 * t363 * t1603 * t346 / 0.3072e4 + t1033 + t1034 * t1035 * t1038 * t1531 / 0.4608e4
  t1635 = f.my_piecewise3(t381, -t1536 + t1549 + t1573 + t1575 - t1579 + t192 * t325 * (t1582 * t368 * t374 - t962 * t248 * t373 * t1586 + t331 * t1613 * t374 - t369 * t248 * t1047 * (t1053 * t1054 * t1603 * t343 * t346 - t990 * t349 * t368 * t1586 + t340 * t349 * t1613 + t1594 * t370)) * t1067, t1526)
  t1640 = f.my_piecewise3(t119, t259 * t1411 / 0.2e1 + t1526 * t29 / 0.2e1, t382 * t1412 / 0.2e1 + t1635 * t44 / 0.2e1)
  t1642 = -t1411
  t1646 = t1086 * t1412
  t1648 = t127 * t1085 * t1646
  t1651 = (-t1084 + 0.11073470983333333333333333333333333333333333333333e-2 * t1648) * t408
  t1653 = -t1083 / 0.3e1 + t1648 / 0.3e1
  t1654 = t1096 * t1653
  t1657 = t1103 * t1653
  t1660 = t140 * t1109 * t1646
  t1664 = t1095 * (0.11807781499500000000000000000000000000000000000000e0 * t1654 - t1101 + 0.18590165886666666666666666666666666666666666666667e-1 * t1648 + 0.19099794277500000000000000000000000000000000000000e-1 * t1657 - t1108 + 0.51086165526666666666666666666666666666666666666667e-2 * t1660) * t1114
  t1677 = (-t1134 + 0.31311127083333333333333333333333333333333333333333e-3 * t1648) * t430
  t1683 = 0.87448811650000000000000000000000000000000000000000e-1 * t1654 - t1143 + 0.10197154565000000000000000000000000000000000000000e-1 * t1648 + 0.55743234727500000000000000000000000000000000000000e-2 * t1657 - t1146 + 0.27959640330000000000000000000000000000000000000000e-2 * t1660
  t1688 = t292 * (-(-t1117 + 0.53237641966666666666666666666666666666666666666667e-3 * t1648) * t419 + t1123 * (0.10974162105750000000000000000000000000000000000000e0 * t1654 - t1125 + 0.16057569282500000000000000000000000000000000000000e-1 * t1648 + 0.19623283938750000000000000000000000000000000000000e-1 * t1657 - t1128 + 0.32394954865000000000000000000000000000000000000000e-2 * t1660) * t1131 + t1651 - t1664 - 0.58482236226346462072622386637590534819724553404281e0 * t1677 + 0.58482236226346462072622386637590534819724553404281e0 * t1141 * t1683 * t1149)
  t1690 = 0.58482236226346462072622386637590534819724553404281e0 * t292 * t1677
  t1694 = 0.58482236226346462072622386637590534819724553404281e0 * t1157 * t1140 * t1683 * t1149
  t1697 = (-t1162 + 0.55603792169291016666666666666666666666666666666667e-3 * t1648) * t441
  t1701 = -t1172 + 0.14816666666666666666666666666666666666666666666667e-1 * t1648
  t1712 = t1697 * t219
  t1721 = -t1651 + t1664 + t1688 + t1690 - t1694
  t1739 = -t1423 * t333 * t446 / 0.36e2 + t1181 - t1182 * t978 * t1185 * t1412 / 0.288e3 + t1712 * t458 * t469 / 0.3072e4 - t1197 * t995 * t996 * t466 * t1701 / 0.3072e4 + t1208 * t1014 * t467 * t1721 * t453 / 0.3072e4 - t459 / t51 / t460 / t50 * t358 * t71 * t468 / 0.576e3 + t1219 - t1220 * t1035 * t1223 * t1646 / 0.4608e4
  t1761 = f.my_piecewise3(t485, -t1651 + t1664 + t1688 + t1690 - t1694 + t192 * t325 * (t1697 * t472 * t478 - t1171 * t248 * t477 * t1701 + t442 * t1739 * t478 - t473 * t248 * t1232 * (t1237 * t1238 * t1721 * t343 * t453 - t1194 * t456 * t472 * t1701 + t449 * t456 * t1739 + t1712 * t474)) * t1251, t1526)
  t1766 = f.my_piecewise3(t387, t1526 * t32 / 0.2e1 + t259 * t1642 / 0.2e1, -t486 * t1412 / 0.2e1 + t1761 * t56 / 0.2e1)
  t1775 = f.my_piecewise3(t30, 0, 0.4e1 / 0.3e1 * t495 * t1411)
  t1778 = f.my_piecewise3(t33, 0, 0.4e1 / 0.3e1 * t498 * t1642)
  t1780 = (t1775 + t1778) * t159
  t1782 = t494 * t1780 * t183
  t1784 = 0.58482236226346462072622386637590534819724553404281e0 * t1780 * t181
  t1787 = f.my_piecewise3(t30, 0, 0.2e1 / 0.3e1 * t1295 * t1411)
  t1790 = f.my_piecewise3(t33, 0, 0.2e1 / 0.3e1 * t1299 * t1642)
  t1792 = t1787 / 0.2e1 + t1790 / 0.2e1
  t1807 = (-(t659 + t683 - t1270 - t1273 + t1782 + t1285 + t1784 - t1290 - t1293) * t219 * t523 + 0.3e1 * t521 * t1347 * t1792) * t525
  t1817 = -t1320 - t1322 * t779 * t123 * t1792 / 0.48e2 - t1331 + t1336 - t1341 * t1343 * t361 * t1807 / 0.3072e4 - t1360 - t530 * t1363 * t241 * t124 * t1792 / 0.768e3
  t1832 = t659 + t683 - t1270 - t1273 + t1782 + t1285 + t1784 - t1290 - t1293 + 0.3e1 * t192 * t1294 * t1792 + t192 * t514 * (-t1311 + t1318 + t207 * t1817 * t543 - t538 * t248 * t1373 * (-t851 * t1382 * t1807 + t220 * t528 * t1817 - t1376 + t1381)) * t1393
  t1834 = -t1445 * t490 - 0.2e1 * t632 * t490 * t1460 - t117 * (t1640 + t1766) + (0.2e1 * t1263 * t1460 + t1445) * t549 + t493 * t1832
  vrho_1_ = t556 + t2 * t1834 * t555 + t1401 * (0.3e1 * t552 * t116 * t1460 + params.d * t1834 * t553)
  t1844 = t584 * t37
  t1848 = t75 * t83
  t1852 = f.my_piecewise3(t7, 0, -t1844 * (t42 * t48 - t67) * t71 * t1848 / 0.6e1)
  t1853 = t1852 * t116
  t1855 = t67 * t112
  t1856 = f.my_piecewise3(t114, 0, t1855)
  t1859 = 0.2e1 * t632 * t490 * t1856
  t1860 = t192 * t201
  t1861 = t209 * t156
  t1863 = t1861 * t212 * t797
  t1867 = t220 * t229 * t63 * t243
  t1869 = t1863 / 0.96e2 + t1867 / 0.1536e4
  t1872 = t203 ** 2
  t1873 = t1872 * t762
  t1875 = t1873 * t246 * t1003
  t1876 = t1005 * t841
  t1880 = -t1875 * t1876 * t228 * t1869 + t207 * t1869 * t253
  t1881 = t1880 * t863
  t1884 = t1860 * t1881 * t29 / 0.2e1
  t1893 = t42 * t332 * t135 * t337 / 0.96e2 + t340 * t349 * s0 * t365 / 0.1536e4
  t1896 = t327 ** 2
  t1910 = t192 * t201 * t1880 * t863
  t1911 = f.my_piecewise3(t381, t192 * t325 * (-t1896 * t960 * t368 * t1003 * t1005 * t1047 * t348 * t1893 + t331 * t1893 * t374) * t1067, t1910)
  t1914 = f.my_piecewise3(t119, t1884, t1911 * t44 / 0.2e1)
  t1917 = t1860 * t1881 * t32 / 0.2e1
  t1918 = f.my_piecewise3(t485, 0, t1910)
  t1921 = f.my_piecewise3(t387, t1917, t1918 * t56 / 0.2e1)
  t1925 = 0.2e1 * t1263 * t1856
  t1929 = t493 * t190 * t191
  t1931 = t1861 * t515 * t797
  t1935 = t220 * t528 * t63 * t534
  t1937 = t1931 / 0.96e2 + t1935 / 0.1536e4
  t1941 = t1873 * t537 * t1003
  t1942 = t1005 * t1373
  t1949 = t1929 * t514 * (-t1941 * t1942 * t527 * t1937 + t207 * t1937 * t543) * t1393
  t1950 = -t1853 * t490 - t1859 - t117 * (t1914 + t1921) + (t1853 + t1925) * t549 + t1949
  t1957 = 0.3e1 * t552 * t116 * t1856
  vsigma_0_ = t2 * t1950 * t555 + t1401 * (params.d * t1950 * t553 + t1957)
  t1964 = f.my_piecewise3(t7, 0, t1844 * t67 * t71 * t1848 / 0.3e1)
  t1965 = t1964 * t116
  t1968 = f.my_piecewise3(t114, 0, 0.2e1 * t1855)
  t1974 = t1863 / 0.48e2 + t1867 / 0.768e3
  t1980 = -t1875 * t1876 * t228 * t1974 + t207 * t1974 * t253
  t1981 = t1980 * t863
  t1987 = t192 * t201 * t1980 * t863
  t1988 = f.my_piecewise3(t381, 0, t1987)
  t1991 = f.my_piecewise3(t119, t1860 * t1981 * t29 / 0.2e1, t1988 * t44 / 0.2e1)
  t1995 = f.my_piecewise3(t485, 0, t1987)
  t1998 = f.my_piecewise3(t387, t1860 * t1981 * t32 / 0.2e1, t1995 * t56 / 0.2e1)
  t2007 = t1931 / 0.48e2 + t1935 / 0.768e3
  t2017 = -t1965 * t490 - 0.2e1 * t632 * t490 * t1968 - t117 * (t1991 + t1998) + (0.2e1 * t1263 * t1968 + t1965) * t549 + t1929 * t514 * (-t1941 * t1942 * t527 * t2007 + t207 * t2007 * t543) * t1393
  vsigma_1_ = t2 * t2017 * t555 + t1401 * (0.3e1 * t552 * t116 * t1968 + params.d * t2017 * t553)
  t2033 = f.my_piecewise3(t7, 0, -t1844 * (t54 * t60 - t67) * t71 * t1848 / 0.6e1)
  t2034 = t2033 * t116
  t2036 = f.my_piecewise3(t381, 0, t1910)
  t2039 = f.my_piecewise3(t119, t1884, t2036 * t44 / 0.2e1)
  t2048 = t54 * t332 * t135 * t446 / 0.96e2 + t449 * t456 * s2 * t469 / 0.1536e4
  t2051 = t438 ** 2
  t2063 = f.my_piecewise3(t485, t192 * t325 * (-t2051 * t1169 * t472 * t1003 * t1005 * t1232 * t455 * t2048 + t442 * t2048 * t478) * t1251, t1910)
  t2066 = f.my_piecewise3(t387, t1917, t2063 * t56 / 0.2e1)
  t2071 = -t2034 * t490 - t1859 - t117 * (t2039 + t2066) + (t2034 + t1925) * t549 + t1949
  vsigma_2_ = t2 * t2071 * t555 + t1401 * (params.d * t2071 * t553 + t1957)
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t2082 = f.my_piecewise3(t114, 0, -0.8e1 * t68 * t636 * t95 * t100)
  t2088 = 0.2e1 * t1263 * t2082 * t549 - 0.2e1 * t632 * t490 * t2082
  vtau_0_ = t2 * t2088 * t555 + t1401 * (0.3e1 * t552 * t116 * t2082 + params.d * t2088 * t553)
  t2102 = f.my_piecewise3(t114, 0, -0.8e1 * t68 * t636 * t103 * t108)
  t2108 = 0.2e1 * t1263 * t2102 * t549 - 0.2e1 * t632 * t490 * t2102
  vtau_1_ = t2 * t2108 * t555 + t1401 * (0.3e1 * t552 * t116 * t2102 + params.d * t2108 * t553)
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
  params_C0_c_raw = params.C0_c
  if isinstance(params_C0_c_raw, (str, bytes, dict)):
    params_C0_c = params_C0_c_raw
  else:
    try:
      params_C0_c_seq = list(params_C0_c_raw)
    except TypeError:
      params_C0_c = params_C0_c_raw
    else:
      params_C0_c_seq = np.asarray(params_C0_c_seq, dtype=np.float64)
      params_C0_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_C0_c_seq))
  params_d_raw = params.d
  if isinstance(params_d_raw, (str, bytes, dict)):
    params_d = params_d_raw
  else:
    try:
      params_d_seq = list(params_d_raw)
    except TypeError:
      params_d = params_d_raw
    else:
      params_d_seq = np.asarray(params_d_seq, dtype=np.float64)
      params_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_d_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  beta_a = 0.06672455060314922

  beta_b = 0.1

  beta_c = 0.1778

  tpss_xi2 = lambda z, xt, xs0, xs1: (1 - z ** 2) * (f.t_total(z, xs0 ** 2, xs1 ** 2) - xt ** 2) / (2 * (3 * jnp.pi ** 2) ** (1 / 3)) ** 2

  tpss_C00 = lambda cc, z: +jnp.sum(jnp.array([cc[i] * z ** (2 * (i - 1)) for i in range(1, 4 + 1)]), axis=0)

  tpss_aux = lambda z, xt, ts0, ts1: jnp.minimum(xt ** 2 / (8 * f.t_total(z, ts0, ts1)), 1)

  tpss_par_s0 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 + z)) ** (1 / 3), 1, xs0, xs0, 0), f_gga(rs, z, xt, xs0, xs1)) * (1 + z) / 2

  tpss_par_s1 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 - z)) ** (1 / 3), -1, xs1, 0, xs1), f_gga(rs, z, xt, xs0, xs1)) * (1 - z) / 2

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  mgamma = params_gamma

  BB = params_BB

  mbeta = lambda rs, t=None: beta_a * (1 + beta_b * rs) / (1 + beta_c * rs)

  tpss_C0_den = lambda z, xt, xs0, xs1: 1 + tpss_xi2(z, xt, xs0, xs1) * ((1 + z) ** (-4 / 3) + (1 - z) ** (-4 / 3)) / 2

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  tpss_C0 = lambda cc, z, xt, xs0, xs1: f.my_piecewise3(1 - jnp.abs(z) <= 1e-12, jnp.sum(jnp.array([cc[i] for i in range(1, 4 + 1)]), axis=0), tpss_C00(cc, z) / tpss_C0_den(f.z_thr(z), xt, xs0, xs1) ** 4)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  tpss_par = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: -(1 + tpss_C0(params_C0_c, z, xt, xs0, xs1)) * tpss_aux(z, xt, ts0, ts1) ** 2 * (+f.my_piecewise3(f.screen_dens_zeta(rs, z), f_gga(rs, f.z_thr(z), xt, xs0, xs1) * (1 + z) / 2, tpss_par_s0(f_gga, rs, f.z_thr(z), xt, xs0, xs1)) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), f_gga(rs, f.z_thr(z), xt, xs0, xs1) * (1 - z) / 2, tpss_par_s1(f_gga, rs, f.z_thr(z), xt, xs0, xs1)))

  tpss_perp = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: (1 + tpss_C0(params_C0_c, z, xt, xs0, xs1) * tpss_aux(z, xt, ts0, ts1) ** 2) * f_gga(rs, z, xt, xs0, xs1)

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  tpss_f0 = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: +tpss_par(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) + tpss_perp(f_gga, rs, z, xt, xs0, xs1, ts0, ts1)

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  tpss_f = lambda f_gga, rs, z, xt, xs0, xs1, ts0, ts1: +tpss_f0(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) * (1 + params_d * tpss_f0(f_gga, rs, z, xt, xs0, xs1, ts0, ts1) * tpss_aux(z, xt, ts0, ts1) ** 3)

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: +tpss_f(f_pbe, rs, z, xt, xs0, xs1, ts0, ts1)

  t2 = f.my_piecewise3(0 < 0, 0, 0)
  t3 = -t2 <= -0.999999999999e0
  t4 = params.C0_c[0]
  t9 = 0.1e1 <= f.p.zeta_threshold
  t10 = f.p.zeta_threshold - 0.1e1
  t12 = f.my_piecewise5(t9, t10, t9, -t10, 0)
  t13 = t12 ** 2
  t14 = 0.1e1 - t13
  t15 = 2 ** (0.1e1 / 0.3e1)
  t16 = t15 ** 2
  t17 = s0 * t16
  t18 = r0 ** 2
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / t18
  t23 = 0.1e1 + t12
  t24 = t23 / 0.2e1
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = t26 * t24
  t30 = 0.1e1 - t12
  t31 = t30 / 0.2e1
  t32 = t31 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = t33 * t31
  t40 = 3 ** (0.1e1 / 0.3e1)
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t46 = t23 ** (0.1e1 / 0.3e1)
  t47 = t46 * t23
  t49 = t30 ** (0.1e1 / 0.3e1)
  t50 = t49 * t30
  t52 = 0.1e1 / t47 + 0.1e1 / t50
  t56 = 0.1e1 + t14 * (t17 * t22 * t27 + t17 * t22 * t34 - s0 * t22) * t40 * t44 * t52 / 0.24e2
  t57 = t56 ** 2
  t58 = t57 ** 2
  t61 = f.my_piecewise3(t3, t4 + params.C0_c[1] + params.C0_c[2] + params.C0_c[3], t4 / t58)
  t62 = 0.1e1 + t61
  t63 = 0.1e1 / r0
  t64 = s0 * t63
  t65 = 0.1e1 / tau0
  t67 = t64 * t65 / 0.8e1
  t68 = 0.1e1 < t67
  t69 = f.my_piecewise3(t68, 1, t67)
  t70 = t69 ** 2
  t71 = t62 * t70
  t74 = jnp.logical_or(r0 / 0.2e1 <= f.p.dens_threshold, t9)
  t76 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t77 = t40 * t76
  t78 = 4 ** (0.1e1 / 0.3e1)
  t79 = t78 ** 2
  t80 = 0.1e1 / t19
  t82 = t77 * t79 * t80
  t84 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t82
  t85 = jnp.sqrt(t82)
  t88 = t82 ** 0.15e1
  t90 = t40 ** 2
  t91 = t76 ** 2
  t92 = t90 * t91
  t93 = 0.1e1 / t20
  t95 = t92 * t78 * t93
  t97 = 0.23615562999000000000000000000000000000000000000000e0 * t85 + 0.55770497660000000000000000000000000000000000000000e-1 * t82 + 0.12733196185000000000000000000000000000000000000000e-1 * t88 + 0.76629248290000000000000000000000000000000000000000e-2 * t95
  t99 = 0.1e1 + 0.1e1 / t97
  t100 = jnp.log(t99)
  t101 = t84 * t100
  t103 = t13 ** 2
  t104 = t23 <= f.p.zeta_threshold
  t105 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t106 = t105 * f.p.zeta_threshold
  t107 = f.my_piecewise3(t104, t106, t47)
  t108 = t30 <= f.p.zeta_threshold
  t109 = f.my_piecewise3(t108, t106, t50)
  t110 = t107 + t109 - 0.2e1
  t111 = t103 * t110
  t114 = 0.1e1 / (0.2e1 * t15 - 0.2e1)
  t116 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t82
  t121 = 0.21948324211500000000000000000000000000000000000000e0 * t85 + 0.48172707847500000000000000000000000000000000000000e-1 * t82 + 0.13082189292500000000000000000000000000000000000000e-1 * t88 + 0.48592432297500000000000000000000000000000000000000e-2 * t95
  t123 = 0.1e1 + 0.1e1 / t121
  t124 = jnp.log(t123)
  t127 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t82
  t132 = 0.17489762330000000000000000000000000000000000000000e0 * t85 + 0.30591463695000000000000000000000000000000000000000e-1 * t82 + 0.37162156485000000000000000000000000000000000000000e-2 * t88 + 0.41939460495000000000000000000000000000000000000000e-2 * t95
  t134 = 0.1e1 + 0.1e1 / t132
  t135 = jnp.log(t134)
  t136 = t127 * t135
  t140 = t111 * t114 * (-t116 * t124 + t101 - 0.58482236226346462072622386637590534819724553404281e0 * t136)
  t142 = t110 * t114
  t143 = t142 * t136
  t145 = jnp.log(0.2e1)
  t146 = 0.1e1 - t145
  t147 = 0.1e1 / t41
  t148 = t146 * t147
  t149 = t105 ** 2
  t150 = t46 ** 2
  t151 = f.my_piecewise3(t104, t149, t150)
  t152 = t49 ** 2
  t153 = f.my_piecewise3(t108, t149, t152)
  t155 = t151 / 0.2e1 + t153 / 0.2e1
  t156 = t155 ** 2
  t157 = t156 * t155
  t159 = 0.66724550603149220e-1 + 0.16681137650787305000000000000000000000000000000000e-2 * t82
  t161 = 0.1e1 + 0.44450000000000000000000000000000000000000000000000e-1 * t82
  t162 = 0.1e1 / t161
  t163 = t159 * t162
  t165 = 0.1e1 / t19 / t18
  t166 = s0 * t165
  t167 = t166 * t15
  t168 = 0.1e1 / t156
  t170 = 0.1e1 / t76
  t171 = t170 * t78
  t172 = t168 * t90 * t171
  t175 = 0.1e1 / t146
  t176 = t163 * t175
  t177 = 0.58482236226346462072622386637590534819724553404281e0 * t143
  t180 = 0.1e1 / t157
  t183 = jnp.exp(-(-t101 + t140 + t177) * t175 * t41 * t180)
  t184 = t183 - 0.1e1
  t185 = 0.1e1 / t184
  t186 = t41 * t185
  t187 = s0 ** 2
  t188 = t186 * t187
  t189 = t176 * t188
  t190 = t18 ** 2
  t192 = 0.1e1 / t20 / t190
  t193 = t192 * t16
  t194 = t156 ** 2
  t195 = 0.1e1 / t194
  t197 = 0.1e1 / t91
  t199 = t40 * t197 * t79
  t200 = t193 * t195 * t199
  t203 = t167 * t172 / 0.96e2 + t189 * t200 / 0.3072e4
  t204 = t163 * t203
  t205 = t175 * t41
  t206 = t186 * t203
  t208 = t176 * t206 + 0.1e1
  t209 = 0.1e1 / t208
  t210 = t205 * t209
  t212 = t204 * t210 + 0.1e1
  t213 = jnp.log(t212)
  t215 = t148 * t157 * t213
  t217 = -t101 / 0.2e1 + t140 / 0.2e1 + 0.29241118113173231036311193318795267409862276702140e0 * t143 + t215 / 0.2e1
  t218 = -t101 + t140 + t177 + t215
  t219 = t77 * t79
  t220 = t80 * t15
  t222 = (0.1e1 / t23) ** (0.1e1 / 0.3e1)
  t224 = t219 * t220 * t222
  t226 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t224
  t227 = jnp.sqrt(t224)
  t230 = t224 ** 0.15e1
  t232 = t92 * t78
  t233 = t93 * t16
  t234 = t222 ** 2
  t236 = t232 * t233 * t234
  t238 = 0.23615562999000000000000000000000000000000000000000e0 * t227 + 0.55770497660000000000000000000000000000000000000000e-1 * t224 + 0.12733196185000000000000000000000000000000000000000e-1 * t230 + 0.76629248290000000000000000000000000000000000000000e-2 * t236
  t240 = 0.1e1 + 0.1e1 / t238
  t241 = jnp.log(t240)
  t242 = t226 * t241
  t243 = 0.2e1 <= f.p.zeta_threshold
  t245 = f.my_piecewise3(t243, t106, 0.2e1 * t15)
  t246 = 0.0e0 <= f.p.zeta_threshold
  t247 = f.my_piecewise3(t246, t106, 0)
  t249 = (t245 + t247 - 0.2e1) * t114
  t251 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t224
  t256 = 0.21948324211500000000000000000000000000000000000000e0 * t227 + 0.48172707847500000000000000000000000000000000000000e-1 * t224 + 0.13082189292500000000000000000000000000000000000000e-1 * t230 + 0.48592432297500000000000000000000000000000000000000e-2 * t236
  t258 = 0.1e1 + 0.1e1 / t256
  t259 = jnp.log(t258)
  t262 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t224
  t267 = 0.17489762330000000000000000000000000000000000000000e0 * t227 + 0.30591463695000000000000000000000000000000000000000e-1 * t224 + 0.37162156485000000000000000000000000000000000000000e-2 * t230 + 0.41939460495000000000000000000000000000000000000000e-2 * t236
  t269 = 0.1e1 + 0.1e1 / t267
  t270 = jnp.log(t269)
  t271 = t262 * t270
  t274 = t249 * (-t251 * t259 + t242 - 0.58482236226346462072622386637590534819724553404281e0 * t271)
  t276 = 0.58482236226346462072622386637590534819724553404281e0 * t249 * t271
  t277 = f.my_piecewise3(t243, t149, t16)
  t278 = f.my_piecewise3(t246, t149, 0)
  t280 = t277 / 0.2e1 + t278 / 0.2e1
  t281 = t280 ** 2
  t282 = t281 * t280
  t284 = 0.66724550603149220e-1 + 0.16681137650787305000000000000000000000000000000000e-2 * t224
  t286 = 0.1e1 + 0.44450000000000000000000000000000000000000000000000e-1 * t224
  t287 = 0.1e1 / t286
  t288 = t284 * t287
  t289 = 0.1e1 / t281
  t290 = t289 * t90
  t291 = t166 * t290
  t292 = 0.1e1 / t222
  t294 = t171 * t16 * t292
  t297 = t288 * t175
  t300 = 0.1e1 / t282
  t301 = t41 * t300
  t303 = jnp.exp(-(-t242 + t274 + t276) * t175 * t301)
  t304 = t303 - 0.1e1
  t305 = 0.1e1 / t304
  t306 = t41 * t305
  t307 = t306 * t187
  t308 = t297 * t307
  t309 = t281 ** 2
  t310 = 0.1e1 / t309
  t312 = t192 * t310 * t40
  t313 = t197 * t79
  t315 = t15 / t234
  t316 = t313 * t315
  t317 = t312 * t316
  t320 = t291 * t294 / 0.96e2 + t308 * t317 / 0.1536e4
  t321 = t288 * t320
  t322 = t306 * t320
  t324 = t297 * t322 + 0.1e1
  t326 = t205 / t324
  t328 = t321 * t326 + 0.1e1
  t329 = jnp.log(t328)
  t332 = t148 * t282 * t329 - t242 + t274 + t276
  t333 = t218 < t332
  t334 = f.my_piecewise3(t333, t332, t218)
  t337 = f.my_piecewise3(t74, t217, t334 * t23 / 0.2e1)
  t339 = (0.1e1 / t30) ** (0.1e1 / 0.3e1)
  t341 = t219 * t220 * t339
  t343 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t341
  t344 = jnp.sqrt(t341)
  t347 = t341 ** 0.15e1
  t349 = t339 ** 2
  t351 = t232 * t233 * t349
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
  t382 = t249 * (-t359 * t367 + t357 - 0.58482236226346462072622386637590534819724553404281e0 * t379)
  t384 = 0.58482236226346462072622386637590534819724553404281e0 * t249 * t379
  t386 = 0.66724550603149220e-1 + 0.16681137650787305000000000000000000000000000000000e-2 * t341
  t388 = 0.1e1 + 0.44450000000000000000000000000000000000000000000000e-1 * t341
  t389 = 0.1e1 / t388
  t390 = t386 * t389
  t391 = 0.1e1 / t339
  t393 = t171 * t16 * t391
  t396 = t390 * t175
  t400 = jnp.exp(-(-t357 + t382 + t384) * t175 * t301)
  t401 = t400 - 0.1e1
  t402 = 0.1e1 / t401
  t403 = t41 * t402
  t404 = t403 * t187
  t405 = t396 * t404
  t407 = t15 / t349
  t408 = t313 * t407
  t409 = t312 * t408
  t412 = t291 * t393 / 0.96e2 + t405 * t409 / 0.1536e4
  t413 = t390 * t412
  t414 = t403 * t412
  t416 = t396 * t414 + 0.1e1
  t418 = t205 / t416
  t420 = t413 * t418 + 0.1e1
  t421 = jnp.log(t420)
  t424 = t148 * t282 * t421 - t357 + t382 + t384
  t425 = t218 < t424
  t426 = f.my_piecewise3(t425, t424, t218)
  t429 = f.my_piecewise3(t74, t217, t426 * t30 / 0.2e1)
  t430 = t337 + t429
  t433 = t61 * t70 + 0.1e1
  t434 = f.my_piecewise3(t9, t106, 1)
  t437 = (0.2e1 * t434 - 0.2e1) * t114
  t439 = 0.58482236226346462072622386637590534819724553404281e0 * t437 * t136
  t440 = f.my_piecewise3(t9, t149, 1)
  t441 = t440 ** 2
  t442 = t441 * t440
  t443 = 0.1e1 / t441
  t445 = t443 * t90 * t171
  t450 = 0.1e1 / t442
  t453 = jnp.exp(-(-t101 + t439) * t175 * t41 * t450)
  t454 = t453 - 0.1e1
  t455 = 0.1e1 / t454
  t456 = t41 * t455
  t457 = t456 * t187
  t458 = t176 * t457
  t459 = t441 ** 2
  t460 = 0.1e1 / t459
  t462 = t193 * t460 * t199
  t465 = t167 * t445 / 0.96e2 + t458 * t462 / 0.3072e4
  t466 = t163 * t465
  t467 = t456 * t465
  t469 = t176 * t467 + 0.1e1
  t470 = 0.1e1 / t469
  t471 = t205 * t470
  t473 = t466 * t471 + 0.1e1
  t474 = jnp.log(t473)
  t477 = t148 * t442 * t474 - t101 + t439
  t479 = -t71 * t430 + t433 * t477
  t480 = params.d * t479
  t481 = t70 * t69
  t483 = t480 * t481 + 0.1e1
  t488 = t4 / t58 / t56 * t14
  t489 = t18 * r0
  t491 = 0.1e1 / t20 / t489
  t500 = t44 * t52
  t504 = f.my_piecewise3(t3, 0, -t488 * (-0.8e1 / 0.3e1 * t17 * t491 * t27 - 0.8e1 / 0.3e1 * t17 * t491 * t34 + 0.8e1 / 0.3e1 * s0 * t491) * t40 * t500 / 0.6e1)
  t505 = t504 * t70
  t507 = t62 * t69
  t512 = f.my_piecewise3(t68, 0, -s0 / t18 * t65 / 0.8e1)
  t517 = 0.1e1 / t19 / r0
  t518 = t79 * t517
  t520 = t77 * t518 * t100
  t522 = t97 ** 2
  t527 = t76 * t79
  t528 = t527 * t517
  t529 = 0.1e1 / t85 * t40 * t528
  t531 = t77 * t518
  t533 = t82 ** 0.5e0
  t535 = t533 * t40 * t528
  t538 = 0.1e1 / t20 / r0
  t540 = t92 * t78 * t538
  t545 = t84 / t522 * (-0.39359271665000000000000000000000000000000000000000e-1 * t529 - 0.18590165886666666666666666666666666666666666666667e-1 * t531 - 0.63665980925000000000000000000000000000000000000000e-2 * t535 - 0.51086165526666666666666666666666666666666666666667e-2 * t540) / t99
  t550 = t121 ** 2
  t561 = 0.11073470983333333333333333333333333333333333333333e-2 * t520
  t565 = t132 ** 2
  t566 = 0.1e1 / t565
  t572 = -0.29149603883333333333333333333333333333333333333333e-1 * t529 - 0.10197154565000000000000000000000000000000000000000e-1 * t531 - 0.18581078242500000000000000000000000000000000000000e-2 * t535 - 0.27959640330000000000000000000000000000000000000000e-2 * t540
  t573 = 0.1e1 / t134
  t579 = t111 * t114 * (0.53237641966666666666666666666666666666666666666667e-3 * t77 * t518 * t124 + t116 / t550 * (-0.36580540352500000000000000000000000000000000000000e-1 * t529 - 0.16057569282500000000000000000000000000000000000000e-1 * t531 - 0.65410946462500000000000000000000000000000000000000e-2 * t535 - 0.32394954865000000000000000000000000000000000000000e-2 * t540) / t123 - t561 - t545 + 0.18311447306006545054854346104378990962041954983034e-3 * t77 * t518 * t135 + 0.58482236226346462072622386637590534819724553404281e0 * t127 * t566 * t572 * t573)
  t583 = t527 * t517 * t135
  t584 = t142 * t40 * t583
  t588 = t566 * t572 * t573
  t589 = t142 * t127 * t588
  t595 = t161 ** 2
  t596 = 0.1e1 / t595
  t597 = t159 * t596
  t607 = s0 / t19 / t489
  t608 = t607 * t15
  t611 = t90 * t170
  t613 = 0.1e1 / t190 / t18
  t616 = t611 * t78 * t613 * t162
  t617 = t205 * t185
  t618 = t187 * t16
  t623 = t597 * t175
  t625 = t613 * t16
  t627 = t611 * t78
  t631 = t146 ** 2
  t632 = 0.1e1 / t631
  t633 = t163 * t632
  t634 = t41 ** 2
  t635 = t184 ** 2
  t636 = 0.1e1 / t635
  t638 = t187 * t192
  t645 = 0.18311447306006545054854346104378990962041954983034e-3 * t584
  t646 = 0.58482236226346462072622386637590534819724553404281e0 * t589
  t647 = t561 + t545 + t579 - t645 - t646
  t655 = 0.1e1 / t20 / t190 / r0
  t656 = t655 * t16
  t661 = -0.7e1 / 0.288e3 * t608 * t172 - 0.72400771053764344618055555555555555555555555555557e-6 * t616 * t617 * t618 * t195 + 0.19292534722222222222222222222222222222222222222223e-4 * t623 * t188 * t625 * t195 * t627 + t633 * t634 * t636 * t638 * t16 / t194 / t157 * t40 * t313 * t647 * t183 / 0.3072e4 - 0.7e1 / 0.4608e4 * t189 * t656 * t195 * t199
  t664 = t208 ** 2
  t665 = 0.1e1 / t664
  t666 = t162 * t175
  t675 = t632 * t634
  t676 = t163 * t675
  t690 = 0.1e1 / t212
  t692 = t148 * t157 * (-0.55603792169291016666666666666666666666666666666667e-3 * t531 * t162 * t203 * t210 + 0.14816666666666666666666666666666666666666666666667e-1 * t597 * t203 * t175 * t41 * t209 * t40 * t528 + t163 * t661 * t210 - t204 * t205 * t665 * (-0.55603792169291016666666666666666666666666666666667e-3 * t531 * t666 * t206 + 0.14816666666666666666666666666666666666666666666667e-1 * t597 * t617 * t203 * t40 * t528 + t676 * t636 * t203 * t647 * t180 * t183 + t176 * t186 * t661)) * t690
  t694 = 0.55367354916666666666666666666666666666666666666665e-3 * t520 + t545 / 0.2e1 + t579 / 0.2e1 - 0.91557236530032725274271730521894954810209774915169e-4 * t584 - 0.29241118113173231036311193318795267409862276702140e0 * t589 + t692 / 0.2e1
  t695 = t517 * t15
  t699 = 0.11073470983333333333333333333333333333333333333333e-2 * t219 * t695 * t222 * t241
  t700 = t238 ** 2
  t706 = t15 * t222
  t707 = t518 * t706
  t708 = 0.1e1 / t227 * t40 * t76 * t707
  t711 = t219 * t695 * t222
  t713 = t224 ** 0.5e0
  t716 = t713 * t40 * t76 * t707
  t718 = t538 * t16
  t720 = t232 * t718 * t234
  t725 = t226 / t700 * (-0.39359271665000000000000000000000000000000000000000e-1 * t708 - 0.18590165886666666666666666666666666666666666666667e-1 * t711 - 0.63665980925000000000000000000000000000000000000000e-2 * t716 - 0.51086165526666666666666666666666666666666666666667e-2 * t720) / t240
  t730 = t256 ** 2
  t745 = t267 ** 2
  t746 = 0.1e1 / t745
  t752 = -0.29149603883333333333333333333333333333333333333333e-1 * t708 - 0.10197154565000000000000000000000000000000000000000e-1 * t711 - 0.18581078242500000000000000000000000000000000000000e-2 * t716 - 0.27959640330000000000000000000000000000000000000000e-2 * t720
  t753 = 0.1e1 / t269
  t758 = t249 * (0.53237641966666666666666666666666666666666666666667e-3 * t219 * t695 * t222 * t259 + t251 / t730 * (-0.36580540352500000000000000000000000000000000000000e-1 * t708 - 0.16057569282500000000000000000000000000000000000000e-1 * t711 - 0.65410946462500000000000000000000000000000000000000e-2 * t716 - 0.32394954865000000000000000000000000000000000000000e-2 * t720) / t258 - t699 - t725 + 0.18311447306006545054854346104378990962041954983034e-3 * t219 * t695 * t222 * t270 + 0.58482236226346462072622386637590534819724553404281e0 * t262 * t746 * t752 * t753)
  t759 = t249 * t77
  t763 = 0.18311447306006545054854346104378990962041954983034e-3 * t759 * t518 * t706 * t270
  t768 = 0.58482236226346462072622386637590534819724553404281e0 * t249 * t262 * t746 * t752 * t753
  t770 = t77 * t518 * t15
  t771 = t222 * t287
  t776 = t286 ** 2
  t777 = 0.1e1 / t776
  t778 = t284 * t777
  t783 = t607 * t290
  t795 = t778 * t175
  t798 = t613 * t310 * t90
  t803 = t304 ** 2
  t804 = 0.1e1 / t803
  t811 = 0.1e1 / t309 / t282 * t40 * t313
  t812 = t699 + t725 + t758 - t763 - t768
  t819 = t655 * t310 * t40
  t823 = -0.7e1 / 0.288e3 * t783 * t294 - 0.14480154210752868923611111111111111111111111111111e-5 * t627 * t625 * t292 * t287 * t175 * t41 * t305 * t187 * t310 + 0.38585069444444444444444444444444444444444444444445e-4 * t795 * t307 * t798 * t294 + t288 * t632 * t634 * t804 * t638 * t811 * t315 * t812 * t303 / 0.1536e4 - 0.7e1 / 0.2304e4 * t308 * t819 * t316
  t826 = t324 ** 2
  t827 = 0.1e1 / t826
  t849 = 0.1e1 / t328
  t853 = t561 + t545 + t579 - t645 - t646 + t692
  t854 = f.my_piecewise3(t333, t699 + t725 + t758 - t763 - t768 + t148 * t282 * (-0.55603792169291016666666666666666666666666666666667e-3 * t770 * t771 * t320 * t326 + 0.14816666666666666666666666666666666666666666666667e-1 * t778 * t320 * t326 * t711 + t288 * t823 * t326 - t321 * t205 * t827 * (-0.55603792169291016666666666666666666666666666666667e-3 * t770 * t771 * t175 * t322 + 0.14816666666666666666666666666666666666666666666667e-1 * t795 * t322 * t711 + t288 * t675 * t804 * t320 * t812 * t300 * t303 + t297 * t306 * t823)) * t849, t853)
  t857 = f.my_piecewise3(t74, t694, t854 * t23 / 0.2e1)
  t861 = 0.11073470983333333333333333333333333333333333333333e-2 * t219 * t695 * t339 * t356
  t862 = t353 ** 2
  t868 = t15 * t339
  t869 = t518 * t868
  t870 = 0.1e1 / t344 * t40 * t76 * t869
  t873 = t219 * t695 * t339
  t875 = t341 ** 0.5e0
  t878 = t875 * t40 * t76 * t869
  t881 = t232 * t718 * t349
  t886 = t343 / t862 * (-0.39359271665000000000000000000000000000000000000000e-1 * t870 - 0.18590165886666666666666666666666666666666666666667e-1 * t873 - 0.63665980925000000000000000000000000000000000000000e-2 * t878 - 0.51086165526666666666666666666666666666666666666667e-2 * t881) / t355
  t891 = t364 ** 2
  t906 = t375 ** 2
  t907 = 0.1e1 / t906
  t913 = -0.29149603883333333333333333333333333333333333333333e-1 * t870 - 0.10197154565000000000000000000000000000000000000000e-1 * t873 - 0.18581078242500000000000000000000000000000000000000e-2 * t878 - 0.27959640330000000000000000000000000000000000000000e-2 * t881
  t914 = 0.1e1 / t377
  t919 = t249 * (0.53237641966666666666666666666666666666666666666667e-3 * t219 * t695 * t339 * t367 + t359 / t891 * (-0.36580540352500000000000000000000000000000000000000e-1 * t870 - 0.16057569282500000000000000000000000000000000000000e-1 * t873 - 0.65410946462500000000000000000000000000000000000000e-2 * t878 - 0.32394954865000000000000000000000000000000000000000e-2 * t881) / t366 - t861 - t886 + 0.18311447306006545054854346104378990962041954983034e-3 * t219 * t695 * t339 * t378 + 0.58482236226346462072622386637590534819724553404281e0 * t370 * t907 * t913 * t914)
  t923 = 0.18311447306006545054854346104378990962041954983034e-3 * t759 * t518 * t868 * t378
  t928 = 0.58482236226346462072622386637590534819724553404281e0 * t249 * t370 * t907 * t913 * t914
  t929 = t339 * t389
  t934 = t388 ** 2
  t935 = 0.1e1 / t934
  t936 = t386 * t935
  t952 = t936 * t175
  t958 = t401 ** 2
  t959 = 0.1e1 / t958
  t963 = t861 + t886 + t919 - t923 - t928
  t972 = -0.7e1 / 0.288e3 * t783 * t393 - 0.14480154210752868923611111111111111111111111111111e-5 * t627 * t625 * t391 * t389 * t175 * t41 * t402 * t187 * t310 + 0.38585069444444444444444444444444444444444444444445e-4 * t952 * t404 * t798 * t393 + t390 * t632 * t634 * t959 * t638 * t811 * t407 * t963 * t400 / 0.1536e4 - 0.7e1 / 0.2304e4 * t405 * t819 * t408
  t975 = t416 ** 2
  t976 = 0.1e1 / t975
  t998 = 0.1e1 / t420
  t1002 = f.my_piecewise3(t425, t861 + t886 + t919 - t923 - t928 + t148 * t282 * (-0.55603792169291016666666666666666666666666666666667e-3 * t770 * t929 * t412 * t418 + 0.14816666666666666666666666666666666666666666666667e-1 * t936 * t412 * t418 * t873 + t390 * t972 * t418 - t413 * t205 * t976 * (-0.55603792169291016666666666666666666666666666666667e-3 * t770 * t929 * t175 * t414 + 0.14816666666666666666666666666666666666666666666667e-1 * t952 * t414 * t873 + t390 * t675 * t959 * t412 * t963 * t300 * t400 + t396 * t403 * t972)) * t998, t853)
  t1005 = f.my_piecewise3(t74, t694, t1002 * t30 / 0.2e1)
  t1008 = t61 * t69
  t1015 = 0.18311447306006545054854346104378990962041954983034e-3 * t437 * t40 * t583
  t1018 = 0.58482236226346462072622386637590534819724553404281e0 * t437 * t127 * t588
  t1032 = t205 * t455
  t1042 = t454 ** 2
  t1043 = 0.1e1 / t1042
  t1051 = t561 + t545 - t1015 - t1018
  t1061 = -0.7e1 / 0.288e3 * t608 * t445 - 0.72400771053764344618055555555555555555555555555557e-6 * t616 * t1032 * t618 * t460 + 0.19292534722222222222222222222222222222222222222223e-4 * t623 * t457 * t625 * t460 * t627 + t633 * t634 * t1043 * t638 * t16 / t459 / t442 * t40 * t313 * t1051 * t453 / 0.3072e4 - 0.7e1 / 0.4608e4 * t458 * t656 * t460 * t199
  t1064 = t469 ** 2
  t1065 = 0.1e1 / t1064
  t1087 = 0.1e1 / t473
  t1092 = -t505 * t430 - 0.2e1 * t507 * t430 * t512 - t71 * (t857 + t1005) + (0.2e1 * t1008 * t512 + t505) * t477 + t433 * (t561 + t545 - t1015 - t1018 + t148 * t442 * (-0.55603792169291016666666666666666666666666666666667e-3 * t531 * t162 * t465 * t471 + 0.14816666666666666666666666666666666666666666666667e-1 * t597 * t465 * t175 * t41 * t470 * t40 * t528 + t163 * t1061 * t471 - t466 * t205 * t1065 * (-0.55603792169291016666666666666666666666666666666667e-3 * t531 * t666 * t467 + 0.14816666666666666666666666666666666666666666666667e-1 * t597 * t1032 * t465 * t40 * t528 + t676 * t1043 * t465 * t1051 * t450 * t453 + t176 * t456 * t1061)) * t1087)
  t1095 = r0 * t479
  vrho_0_ = t479 * t483 + r0 * t1092 * t483 + t1095 * (params.d * t1092 * t481 + 0.3e1 * t480 * t70 * t512)
  t1103 = t16 * t22
  t1111 = f.my_piecewise3(t3, 0, -t488 * (t1103 * t27 + t1103 * t34 - t22) * t40 * t500 / 0.6e1)
  t1112 = t1111 * t70
  t1116 = f.my_piecewise3(t68, 0, t63 * t65 / 0.8e1)
  t1120 = t165 * t15
  t1128 = t1120 * t168 * t627 / 0.96e2 + t176 * t186 * s0 * t200 / 0.1536e4
  t1131 = t159 ** 2
  t1132 = t1131 * t596
  t1142 = t148 * t157 * (-t1132 * t203 * t632 * t634 * t665 * t185 * t1128 + t163 * t1128 * t210) * t690
  t1143 = t1142 / 0.2e1
  t1145 = t165 * t289 * t90
  t1152 = t1145 * t294 / 0.96e2 + t297 * t306 * s0 * t317 / 0.768e3
  t1155 = t284 ** 2
  t1167 = f.my_piecewise3(t333, t148 * t282 * (-t1155 * t777 * t320 * t632 * t634 * t827 * t305 * t1152 + t288 * t1152 * t326) * t849, t1142)
  t1170 = f.my_piecewise3(t74, t1143, t1167 * t23 / 0.2e1)
  t1177 = t1145 * t393 / 0.96e2 + t396 * t403 * s0 * t409 / 0.768e3
  t1180 = t386 ** 2
  t1192 = f.my_piecewise3(t425, t148 * t282 * (-t1180 * t935 * t412 * t632 * t634 * t976 * t402 * t1177 + t390 * t1177 * t418) * t998, t1142)
  t1195 = f.my_piecewise3(t74, t1143, t1192 * t30 / 0.2e1)
  t1211 = t1120 * t443 * t627 / 0.96e2 + t176 * t456 * s0 * t462 / 0.1536e4
  t1224 = -t1112 * t430 - 0.2e1 * t507 * t430 * t1116 - t71 * (t1170 + t1195) + (0.2e1 * t1008 * t1116 + t1112) * t477 + t433 * t146 * t147 * t442 * (-t1132 * t465 * t632 * t634 * t1065 * t455 * t1211 + t163 * t1211 * t471) * t1087
  vsigma_0_ = r0 * t1224 * t483 + t1095 * (0.3e1 * t480 * t70 * t1116 + params.d * t1224 * t481)
  vlapl_0_ = 0.0e0
  t1234 = tau0 ** 2
  t1238 = f.my_piecewise3(t68, 0, -t64 / t1234 / 0.8e1)
  t1244 = 0.2e1 * t1008 * t1238 * t477 - 0.2e1 * t507 * t430 * t1238
  vtau_0_ = r0 * t1244 * t483 + t1095 * (0.3e1 * t480 * t70 * t1238 + params.d * t1244 * t481)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
  return res

