"""Generated from mgga_c_tpss.mpl."""

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
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

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mbeta = lambda rs=None, t=None: params_beta

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  tpss_xi2 = lambda z, xt, xs0, xs1: (1 - z ** 2) * (f.t_total(z, xs0 ** 2, xs1 ** 2) - xt ** 2) / (2 * (3 * jnp.pi ** 2) ** (1 / 3)) ** 2

  tpss_C00 = lambda cc, z: +jnp.sum(jnp.array([cc[i] * z ** (2 * (i - 1)) for i in range(1, 4 + 1)]), axis=0)

  tpss_aux = lambda z, xt, ts0, ts1: jnp.minimum(xt ** 2 / (8 * f.t_total(z, ts0, ts1)), 1)

  tpss_par_s0 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 + z)) ** (1 / 3), 1, xs0, xs0, 0), f_gga(rs, z, xt, xs0, xs1)) * (1 + z) / 2

  tpss_par_s1 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 - z)) ** (1 / 3), -1, xs1, 0, xs1), f_gga(rs, z, xt, xs0, xs1)) * (1 - z) / 2

  mgamma = params_gamma

  BB = params_BB

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
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

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mbeta = lambda rs=None, t=None: params_beta

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  tpss_xi2 = lambda z, xt, xs0, xs1: (1 - z ** 2) * (f.t_total(z, xs0 ** 2, xs1 ** 2) - xt ** 2) / (2 * (3 * jnp.pi ** 2) ** (1 / 3)) ** 2

  tpss_C00 = lambda cc, z: +jnp.sum(jnp.array([cc[i] * z ** (2 * (i - 1)) for i in range(1, 4 + 1)]), axis=0)

  tpss_aux = lambda z, xt, ts0, ts1: jnp.minimum(xt ** 2 / (8 * f.t_total(z, ts0, ts1)), 1)

  tpss_par_s0 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 + z)) ** (1 / 3), 1, xs0, xs0, 0), f_gga(rs, z, xt, xs0, xs1)) * (1 + z) / 2

  tpss_par_s1 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 - z)) ** (1 / 3), -1, xs1, 0, xs1), f_gga(rs, z, xt, xs0, xs1)) * (1 - z) / 2

  mgamma = params_gamma

  BB = params_BB

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
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

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mbeta = lambda rs=None, t=None: params_beta

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  tpss_xi2 = lambda z, xt, xs0, xs1: (1 - z ** 2) * (f.t_total(z, xs0 ** 2, xs1 ** 2) - xt ** 2) / (2 * (3 * jnp.pi ** 2) ** (1 / 3)) ** 2

  tpss_C00 = lambda cc, z: +jnp.sum(jnp.array([cc[i] * z ** (2 * (i - 1)) for i in range(1, 4 + 1)]), axis=0)

  tpss_aux = lambda z, xt, ts0, ts1: jnp.minimum(xt ** 2 / (8 * f.t_total(z, ts0, ts1)), 1)

  tpss_par_s0 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 + z)) ** (1 / 3), 1, xs0, xs0, 0), f_gga(rs, z, xt, xs0, xs1)) * (1 + z) / 2

  tpss_par_s1 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 - z)) ** (1 / 3), -1, xs1, 0, xs1), f_gga(rs, z, xt, xs0, xs1)) * (1 - z) / 2

  mgamma = params_gamma

  BB = params_BB

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

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
  t126 = t124 * t125
  t127 = t122 * t126
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
  t203 = 0.1e1 / t64 / t15
  t204 = t63 * t203
  t205 = t204 * t156
  t206 = 0.1e1 / t200
  t208 = 0.1e1 / t121
  t209 = t208 * t123
  t210 = t206 * t135 * t209
  t213 = 0.1e1 / t190
  t214 = params.beta * t213
  t216 = (-t146 + t185 + t188) * t213
  t217 = 0.1e1 / t201
  t218 = t72 * t217
  t220 = jnp.exp(-t216 * t218)
  t221 = t220 - 0.1e1
  t222 = 0.1e1 / t221
  t223 = t72 * t222
  t224 = t63 ** 2
  t226 = t214 * t223 * t224
  t228 = 0.1e1 / t65 / t20
  t229 = t156 ** 2
  t230 = t228 * t229
  t231 = t200 ** 2
  t232 = 0.1e1 / t231
  t234 = 0.1e1 / t136
  t236 = t71 * t234 * t124
  t237 = t230 * t232 * t236
  t240 = t205 * t210 / 0.96e2 + t226 * t237 / 0.3072e4
  t241 = params.beta * t240
  t242 = t213 * t72
  t245 = t214 * t223 * t240 + 0.1e1
  t247 = t242 / t245
  t249 = t241 * t247 + 0.1e1
  t250 = jnp.log(t249)
  t253 = t192 * t201 * t250 - t146 + t185 + t188
  t256 = t122 * t124
  t257 = t125 * t156
  t258 = 0.1e1 / t44
  t259 = t258 ** (0.1e1 / 0.3e1)
  t261 = t256 * t257 * t259
  t263 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t261
  t264 = jnp.sqrt(t261)
  t267 = t261 ** 0.15e1
  t269 = t137 * t123
  t270 = t138 * t229
  t271 = t259 ** 2
  t273 = t269 * t270 * t271
  t275 = 0.23615562999000000000000000000000000000000000000000e0 * t264 + 0.55770497660000000000000000000000000000000000000000e-1 * t261 + 0.12733196185000000000000000000000000000000000000000e-1 * t267 + 0.76629248290000000000000000000000000000000000000000e-2 * t273
  t277 = 0.1e1 + 0.1e1 / t275
  t278 = jnp.log(t277)
  t279 = t263 * t278
  t280 = 0.2e1 <= f.p.zeta_threshold
  t282 = f.my_piecewise3(t280, t150, 0.2e1 * t156)
  t283 = 0.0e0 <= f.p.zeta_threshold
  t284 = f.my_piecewise3(t283, t150, 0)
  t286 = (t282 + t284 - 0.2e1) * t159
  t288 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t261
  t293 = 0.21948324211500000000000000000000000000000000000000e0 * t264 + 0.48172707847500000000000000000000000000000000000000e-1 * t261 + 0.13082189292500000000000000000000000000000000000000e-1 * t267 + 0.48592432297500000000000000000000000000000000000000e-2 * t273
  t295 = 0.1e1 + 0.1e1 / t293
  t296 = jnp.log(t295)
  t299 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t261
  t304 = 0.17489762330000000000000000000000000000000000000000e0 * t264 + 0.30591463695000000000000000000000000000000000000000e-1 * t261 + 0.37162156485000000000000000000000000000000000000000e-2 * t267 + 0.41939460495000000000000000000000000000000000000000e-2 * t273
  t306 = 0.1e1 + 0.1e1 / t304
  t307 = jnp.log(t306)
  t308 = t299 * t307
  t311 = t286 * (-t288 * t296 + t279 - 0.58482236226346462072622386637590534819724553404281e0 * t308)
  t313 = 0.58482236226346462072622386637590534819724553404281e0 * t286 * t308
  t314 = f.my_piecewise3(t280, t193, t229)
  t315 = f.my_piecewise3(t283, t193, 0)
  t317 = t314 / 0.2e1 + t315 / 0.2e1
  t318 = t317 ** 2
  t319 = t318 * t317
  t320 = 0.1e1 / t318
  t321 = t320 * t135
  t322 = t43 * t321
  t323 = 0.1e1 / t259
  t325 = t209 * t64 * t323
  t328 = t214 * t72
  t331 = 0.1e1 / t319
  t332 = t72 * t331
  t334 = jnp.exp(-(-t279 + t311 + t313) * t213 * t332)
  t335 = t334 - 0.1e1
  t336 = 0.1e1 / t335
  t337 = s0 ** 2
  t338 = t336 * t337
  t339 = t38 ** 2
  t342 = 0.1e1 / t39 / t339 / r0
  t344 = t328 * t338 * t342
  t345 = t318 ** 2
  t346 = 0.1e1 / t345
  t348 = t346 * t71 * t234
  t349 = t124 * t65
  t350 = 0.1e1 / t271
  t352 = t348 * t349 * t350
  t355 = t322 * t325 / 0.96e2 + t344 * t352 / 0.3072e4
  t356 = params.beta * t355
  t357 = t72 * t336
  t360 = t214 * t357 * t355 + 0.1e1
  t362 = t242 / t360
  t364 = t356 * t362 + 0.1e1
  t365 = jnp.log(t364)
  t368 = t192 * t319 * t365 - t279 + t311 + t313
  t369 = t253 < t368
  t370 = f.my_piecewise3(t369, t368, t253)
  t373 = f.my_piecewise3(t119, t253 * t29 / 0.2e1, t370 * t44 / 0.2e1)
  t375 = jnp.logical_or(r1 <= f.p.dens_threshold, t33)
  t378 = 0.1e1 / t56
  t379 = t378 ** (0.1e1 / 0.3e1)
  t381 = t256 * t257 * t379
  t383 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t381
  t384 = jnp.sqrt(t381)
  t387 = t381 ** 0.15e1
  t389 = t379 ** 2
  t391 = t269 * t270 * t389
  t393 = 0.23615562999000000000000000000000000000000000000000e0 * t384 + 0.55770497660000000000000000000000000000000000000000e-1 * t381 + 0.12733196185000000000000000000000000000000000000000e-1 * t387 + 0.76629248290000000000000000000000000000000000000000e-2 * t391
  t395 = 0.1e1 + 0.1e1 / t393
  t396 = jnp.log(t395)
  t397 = t383 * t396
  t399 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t381
  t404 = 0.21948324211500000000000000000000000000000000000000e0 * t384 + 0.48172707847500000000000000000000000000000000000000e-1 * t381 + 0.13082189292500000000000000000000000000000000000000e-1 * t387 + 0.48592432297500000000000000000000000000000000000000e-2 * t391
  t406 = 0.1e1 + 0.1e1 / t404
  t407 = jnp.log(t406)
  t410 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t381
  t415 = 0.17489762330000000000000000000000000000000000000000e0 * t384 + 0.30591463695000000000000000000000000000000000000000e-1 * t381 + 0.37162156485000000000000000000000000000000000000000e-2 * t387 + 0.41939460495000000000000000000000000000000000000000e-2 * t391
  t417 = 0.1e1 + 0.1e1 / t415
  t418 = jnp.log(t417)
  t419 = t410 * t418
  t422 = t286 * (-t399 * t407 + t397 - 0.58482236226346462072622386637590534819724553404281e0 * t419)
  t424 = 0.58482236226346462072622386637590534819724553404281e0 * t286 * t419
  t425 = t55 * t321
  t426 = 0.1e1 / t379
  t428 = t209 * t64 * t426
  t434 = jnp.exp(-(-t397 + t422 + t424) * t213 * t332)
  t435 = t434 - 0.1e1
  t436 = 0.1e1 / t435
  t437 = s2 ** 2
  t438 = t436 * t437
  t439 = t50 ** 2
  t442 = 0.1e1 / t51 / t439 / r1
  t444 = t328 * t438 * t442
  t445 = 0.1e1 / t389
  t447 = t348 * t349 * t445
  t450 = t425 * t428 / 0.96e2 + t444 * t447 / 0.3072e4
  t451 = params.beta * t450
  t452 = t72 * t436
  t455 = t214 * t452 * t450 + 0.1e1
  t457 = t242 / t455
  t459 = t451 * t457 + 0.1e1
  t460 = jnp.log(t459)
  t463 = t192 * t319 * t460 - t397 + t422 + t424
  t464 = t253 < t463
  t465 = f.my_piecewise3(t464, t463, t253)
  t468 = f.my_piecewise3(t375, t253 * t32 / 0.2e1, t465 * t56 / 0.2e1)
  t469 = t373 + t468
  t472 = t92 * t116 + 0.1e1
  t473 = t18 * t21
  t474 = t29 ** (0.1e1 / 0.3e1)
  t476 = f.my_piecewise3(t30, t150, t474 * t29)
  t477 = t32 ** (0.1e1 / 0.3e1)
  t479 = f.my_piecewise3(t33, t150, t477 * t32)
  t481 = (t476 + t479 - 0.2e1) * t159
  t482 = t481 * t183
  t483 = t473 * t482
  t485 = 0.58482236226346462072622386637590534819724553404281e0 * t481 * t181
  t486 = t474 ** 2
  t487 = f.my_piecewise3(t30, t193, t486)
  t488 = t477 ** 2
  t489 = f.my_piecewise3(t33, t193, t488)
  t491 = t487 / 0.2e1 + t489 / 0.2e1
  t492 = t491 ** 2
  t493 = t492 * t491
  t494 = 0.1e1 / t492
  t496 = t494 * t135 * t209
  t500 = (-t146 + t483 + t485) * t213
  t501 = 0.1e1 / t493
  t502 = t72 * t501
  t504 = jnp.exp(-t500 * t502)
  t505 = t504 - 0.1e1
  t506 = 0.1e1 / t505
  t507 = t72 * t506
  t509 = t214 * t507 * t224
  t510 = t492 ** 2
  t511 = 0.1e1 / t510
  t513 = t230 * t511 * t236
  t516 = t205 * t496 / 0.96e2 + t509 * t513 / 0.3072e4
  t517 = params.beta * t516
  t520 = t214 * t507 * t516 + 0.1e1
  t522 = t242 / t520
  t524 = t517 * t522 + 0.1e1
  t525 = jnp.log(t524)
  t528 = t192 * t493 * t525 - t146 + t483 + t485
  t530 = -t117 * t469 + t472 * t528
  t531 = params.d * t530
  t532 = t116 * t115
  t534 = t531 * t532 + 0.1e1
  t535 = t530 * t534
  t538 = 0.2e1 * t9 * t1 * t16
  t539 = t15 * t2
  t542 = 0.2e1 * t14 / t539
  t543 = t13 * t1
  t546 = 0.4e1 * t10 * t543 * t21
  t547 = t20 * t2
  t548 = 0.1e1 / t547
  t550 = 0.4e1 * t19 * t548
  t554 = 0.6e1 * t11 * t18 * t1 * t26
  t558 = 0.6e1 * t24 / t20 / t539
  t563 = t28 / t89 / t87
  t564 = t1 * t16
  t565 = t3 - t564
  t566 = f.my_piecewise5(t30, 0, t33, 0, t565)
  t574 = s0 / t40 / t38 / r0
  t585 = t63 / t65 / t539
  t586 = 0.8e1 / 0.3e1 * t585
  t591 = t44 ** 2
  t593 = 0.1e1 / t77 / t591
  t595 = t56 ** 2
  t597 = 0.1e1 / t80 / t595
  t608 = f.my_piecewise3(t7, 0, (t538 - t542 + t546 - t550 + t554 - t558) * t90 - 0.4e1 * t563 * (-t35 * t566 * t69 * t84 / 0.12e2 + t37 * (-0.8e1 / 0.3e1 * t574 * t48 + 0.5e1 / 0.6e1 * t43 * t47 * t566 - 0.5e1 / 0.6e1 * t55 * t59 * t566 + t586) * t84 / 0.24e2 + t70 * t76 * (-0.4e1 / 0.3e1 * t593 * t566 + 0.4e1 / 0.3e1 * t597 * t566) / 0.24e2))
  t609 = t608 * t116
  t611 = t93 * t115
  t613 = 0.8e1 / 0.3e1 * t585 * t112
  t614 = t111 ** 2
  t615 = 0.1e1 / t614
  t618 = t565 / 0.2e1
  t629 = f.my_piecewise3(t114, 0, -t613 - t68 * t615 * (-0.40e2 / 0.3e1 * tau0 * t42 * t100 - 0.40e2 / 0.3e1 * t104 * t107 * t618 + 0.40e2 / 0.3e1 * t96 * t99 * t618))
  t634 = 0.1e1 / t64 / t2
  t635 = t124 * t634
  t638 = 0.11073470983333333333333333333333333333333333333333e-2 * t122 * t635 * t145
  t639 = t142 ** 2
  t644 = t121 * t124
  t645 = t644 * t634
  t646 = 0.1e1 / t130 * t71 * t645
  t648 = t122 * t635
  t650 = t127 ** 0.5e0
  t652 = t650 * t71 * t645
  t655 = 0.1e1 / t65 / t2
  t657 = t137 * t123 * t655
  t662 = t129 / t639 * (-0.39359271665000000000000000000000000000000000000000e-1 * t646 - 0.18590165886666666666666666666666666666666666666667e-1 * t648 - 0.63665980925000000000000000000000000000000000000000e-2 * t652 - 0.51086165526666666666666666666666666666666666666667e-2 * t657) / t144
  t664 = t36 * t35 * t154
  t667 = 0.4e1 * t664 * t184 * t566
  t670 = f.my_piecewise3(t148, 0, 0.4e1 / 0.3e1 * t77 * t566)
  t673 = f.my_piecewise3(t152, 0, -0.4e1 / 0.3e1 * t80 * t566)
  t674 = t670 + t673
  t676 = t147 * t674 * t184
  t680 = t166 ** 2
  t694 = t177 ** 2
  t695 = 0.1e1 / t694
  t701 = -0.29149603883333333333333333333333333333333333333333e-1 * t646 - 0.10197154565000000000000000000000000000000000000000e-1 * t648 - 0.18581078242500000000000000000000000000000000000000e-2 * t652 - 0.27959640330000000000000000000000000000000000000000e-2 * t657
  t702 = 0.1e1 / t179
  t706 = 0.53237641966666666666666666666666666666666666666667e-3 * t122 * t635 * t169 + t161 / t680 * (-0.36580540352500000000000000000000000000000000000000e-1 * t646 - 0.16057569282500000000000000000000000000000000000000e-1 * t648 - 0.65410946462500000000000000000000000000000000000000e-2 * t652 - 0.32394954865000000000000000000000000000000000000000e-2 * t657) / t168 - t638 - t662 + 0.18311447306006545054854346104378990962041954983034e-3 * t122 * t635 * t180 + 0.58482236226346462072622386637590534819724553404281e0 * t172 * t695 * t701 * t702
  t708 = t155 * t159 * t706
  t711 = 0.58482236226346462072622386637590534819724553404281e0 * t674 * t159 * t181
  t714 = t644 * t634 * t180
  t716 = 0.18311447306006545054854346104378990962041954983034e-3 * t186 * t71 * t714
  t719 = t695 * t701 * t702
  t721 = 0.58482236226346462072622386637590534819724553404281e0 * t186 * t172 * t719
  t722 = t200 * t250
  t723 = 0.1e1 / t77
  t726 = f.my_piecewise3(t148, 0, 0.2e1 / 0.3e1 * t723 * t566)
  t727 = 0.1e1 / t80
  t730 = f.my_piecewise3(t152, 0, -0.2e1 / 0.3e1 * t727 * t566)
  t732 = t726 / 0.2e1 + t730 / 0.2e1
  t739 = t63 / t64 / t539 * t156
  t741 = 0.7e1 / 0.288e3 * t739 * t210
  t743 = t204 * t156 * t217
  t744 = t135 * t208
  t749 = t221 ** 2
  t750 = 0.1e1 / t749
  t753 = t328 * t750 * t224 * t228
  t755 = t229 * t232 * t71
  t756 = t234 * t124
  t760 = t72 * t232
  t765 = (-(t638 + t662 + t667 + t676 + t708 + t711 - t716 - t721) * t213 * t218 + 0.3e1 * t216 * t760 * t732) * t220
  t772 = 0.1e1 / t65 / t547 * t229
  t776 = 0.7e1 / 0.4608e4 * t226 * t772 * t232 * t236
  t779 = t328 * t222 * t224 * t228
  t783 = t229 / t231 / t199 * t71
  t788 = -t741 - t743 * t744 * t123 * t732 / 0.48e2 - t753 * t755 * t756 * t765 / 0.3072e4 - t776 - t779 * t783 * t756 * t732 / 0.768e3
  t791 = t241 * t213
  t792 = t245 ** 2
  t793 = 0.1e1 / t792
  t794 = t72 * t793
  t795 = t750 * t240
  t805 = 0.1e1 / t249
  t808 = t638 + t662 + t667 + t676 + t708 + t711 - t716 - t721 + 0.3e1 * t192 * t722 * t732 + t192 * t201 * (params.beta * t788 * t247 - t791 * t794 * (t214 * t223 * t788 - t328 * t795 * t765)) * t805
  t813 = t634 * t156
  t815 = t256 * t813 * t259
  t816 = 0.11073470983333333333333333333333333333333333333333e-2 * t815
  t817 = t156 * t350
  t818 = 0.1e1 / t591
  t819 = t818 * t566
  t821 = t127 * t817 * t819
  t824 = (-t816 - 0.11073470983333333333333333333333333333333333333333e-2 * t821) * t278
  t825 = t275 ** 2
  t827 = t263 / t825
  t828 = 0.1e1 / t264
  t830 = -t815 / 0.3e1 - t821 / 0.3e1
  t831 = t828 * t830
  t833 = 0.18590165886666666666666666666666666666666666666667e-1 * t815
  t835 = t261 ** 0.5e0
  t836 = t835 * t830
  t838 = t655 * t229
  t840 = t269 * t838 * t271
  t841 = 0.51086165526666666666666666666666666666666666666667e-2 * t840
  t842 = t229 * t323
  t844 = t140 * t842 * t819
  t847 = 0.1e1 / t277
  t849 = t827 * (0.11807781499500000000000000000000000000000000000000e0 * t831 - t833 - 0.18590165886666666666666666666666666666666666666667e-1 * t821 + 0.19099794277500000000000000000000000000000000000000e-1 * t836 - t841 - 0.51086165526666666666666666666666666666666666666667e-2 * t844) * t847
  t850 = 0.53237641966666666666666666666666666666666666666667e-3 * t815
  t854 = t293 ** 2
  t856 = t288 / t854
  t858 = 0.16057569282500000000000000000000000000000000000000e-1 * t815
  t861 = 0.32394954865000000000000000000000000000000000000000e-2 * t840
  t864 = 0.1e1 / t295
  t867 = 0.31311127083333333333333333333333333333333333333333e-3 * t815
  t870 = (-t867 - 0.31311127083333333333333333333333333333333333333333e-3 * t821) * t307
  t872 = t304 ** 2
  t873 = 0.1e1 / t872
  t874 = t299 * t873
  t876 = 0.10197154565000000000000000000000000000000000000000e-1 * t815
  t879 = 0.27959640330000000000000000000000000000000000000000e-2 * t840
  t881 = 0.87448811650000000000000000000000000000000000000000e-1 * t831 - t876 - 0.10197154565000000000000000000000000000000000000000e-1 * t821 + 0.55743234727500000000000000000000000000000000000000e-2 * t836 - t879 - 0.27959640330000000000000000000000000000000000000000e-2 * t844
  t882 = 0.1e1 / t306
  t887 = t286 * (-(-t850 - 0.53237641966666666666666666666666666666666666666667e-3 * t821) * t296 + t856 * (0.10974162105750000000000000000000000000000000000000e0 * t831 - t858 - 0.16057569282500000000000000000000000000000000000000e-1 * t821 + 0.19623283938750000000000000000000000000000000000000e-1 * t836 - t861 - 0.32394954865000000000000000000000000000000000000000e-2 * t844) * t864 + t824 - t849 - 0.58482236226346462072622386637590534819724553404281e0 * t870 + 0.58482236226346462072622386637590534819724553404281e0 * t874 * t881 * t882)
  t889 = 0.58482236226346462072622386637590534819724553404281e0 * t286 * t870
  t890 = t286 * t299
  t894 = 0.58482236226346462072622386637590534819724553404281e0 * t890 * t873 * t881 * t882
  t901 = t322 * t209 * t138 * t323 / 0.288e3
  t902 = t321 * t208
  t903 = t43 * t902
  t904 = t123 * t64
  t907 = 0.1e1 / t259 / t258 * t818
  t912 = t190 ** 2
  t913 = 0.1e1 / t912
  t914 = params.beta * t913
  t915 = t72 ** 2
  t916 = t914 * t915
  t917 = t335 ** 2
  t918 = 0.1e1 / t917
  t921 = 0.1e1 / t345 / t319
  t924 = t916 * t918 * t337 * t342 * t921
  t925 = t65 * t350
  t926 = -t824 + t849 + t887 + t889 - t894
  t942 = t344 * t348 * t126 * t350 / 0.4608e4
  t945 = t328 * t338 * t342 * t346
  t948 = t65 / t271 / t258
  t953 = -t574 * t321 * t325 / 0.36e2 + t901 + t903 * t904 * t907 * t566 / 0.288e3 + t924 * t236 * t925 * t926 * t334 / 0.3072e4 - t328 * t338 / t39 / t339 / t38 * t352 / 0.576e3 + t942 + t945 * t236 * t948 * t819 / 0.4608e4
  t956 = t356 * t213
  t957 = t360 ** 2
  t958 = 0.1e1 / t957
  t959 = t72 * t958
  t961 = t914 * t915 * t918
  t963 = t331 * t334
  t973 = 0.1e1 / t364
  t977 = f.my_piecewise3(t369, -t824 + t849 + t887 + t889 - t894 + t192 * t319 * (params.beta * t953 * t362 - t956 * t959 * (t961 * t355 * t926 * t963 + t214 * t357 * t953)) * t973, t808)
  t982 = f.my_piecewise3(t119, t253 * t565 / 0.2e1 + t808 * t29 / 0.2e1, t370 * t566 / 0.2e1 + t977 * t44 / 0.2e1)
  t984 = -t565
  t989 = t256 * t813 * t379
  t990 = 0.11073470983333333333333333333333333333333333333333e-2 * t989
  t991 = t156 * t445
  t992 = 0.1e1 / t595
  t993 = t992 * t566
  t995 = t127 * t991 * t993
  t998 = (-t990 + 0.11073470983333333333333333333333333333333333333333e-2 * t995) * t396
  t999 = t393 ** 2
  t1001 = t383 / t999
  t1002 = 0.1e1 / t384
  t1004 = -t989 / 0.3e1 + t995 / 0.3e1
  t1005 = t1002 * t1004
  t1007 = 0.18590165886666666666666666666666666666666666666667e-1 * t989
  t1009 = t381 ** 0.5e0
  t1010 = t1009 * t1004
  t1013 = t269 * t838 * t389
  t1014 = 0.51086165526666666666666666666666666666666666666667e-2 * t1013
  t1015 = t229 * t426
  t1017 = t140 * t1015 * t993
  t1020 = 0.1e1 / t395
  t1022 = t1001 * (0.11807781499500000000000000000000000000000000000000e0 * t1005 - t1007 + 0.18590165886666666666666666666666666666666666666667e-1 * t995 + 0.19099794277500000000000000000000000000000000000000e-1 * t1010 - t1014 + 0.51086165526666666666666666666666666666666666666667e-2 * t1017) * t1020
  t1023 = 0.53237641966666666666666666666666666666666666666667e-3 * t989
  t1027 = t404 ** 2
  t1029 = t399 / t1027
  t1031 = 0.16057569282500000000000000000000000000000000000000e-1 * t989
  t1034 = 0.32394954865000000000000000000000000000000000000000e-2 * t1013
  t1037 = 0.1e1 / t406
  t1040 = 0.31311127083333333333333333333333333333333333333333e-3 * t989
  t1043 = (-t1040 + 0.31311127083333333333333333333333333333333333333333e-3 * t995) * t418
  t1045 = t415 ** 2
  t1046 = 0.1e1 / t1045
  t1047 = t410 * t1046
  t1049 = 0.10197154565000000000000000000000000000000000000000e-1 * t989
  t1052 = 0.27959640330000000000000000000000000000000000000000e-2 * t1013
  t1054 = 0.87448811650000000000000000000000000000000000000000e-1 * t1005 - t1049 + 0.10197154565000000000000000000000000000000000000000e-1 * t995 + 0.55743234727500000000000000000000000000000000000000e-2 * t1010 - t1052 + 0.27959640330000000000000000000000000000000000000000e-2 * t1017
  t1055 = 0.1e1 / t417
  t1060 = t286 * (-(-t1023 + 0.53237641966666666666666666666666666666666666666667e-3 * t995) * t407 + t1029 * (0.10974162105750000000000000000000000000000000000000e0 * t1005 - t1031 + 0.16057569282500000000000000000000000000000000000000e-1 * t995 + 0.19623283938750000000000000000000000000000000000000e-1 * t1010 - t1034 + 0.32394954865000000000000000000000000000000000000000e-2 * t1017) * t1037 + t998 - t1022 - 0.58482236226346462072622386637590534819724553404281e0 * t1043 + 0.58482236226346462072622386637590534819724553404281e0 * t1047 * t1054 * t1055)
  t1062 = 0.58482236226346462072622386637590534819724553404281e0 * t286 * t1043
  t1063 = t286 * t410
  t1067 = 0.58482236226346462072622386637590534819724553404281e0 * t1063 * t1046 * t1054 * t1055
  t1071 = t425 * t209 * t138 * t426 / 0.288e3
  t1072 = t55 * t902
  t1075 = 0.1e1 / t379 / t378 * t992
  t1080 = t435 ** 2
  t1081 = 0.1e1 / t1080
  t1085 = t916 * t1081 * t437 * t442 * t921
  t1086 = t65 * t445
  t1087 = -t998 + t1022 + t1060 + t1062 - t1067
  t1096 = t444 * t348 * t126 * t445 / 0.4608e4
  t1099 = t328 * t438 * t442 * t346
  t1102 = t65 / t389 / t378
  t1107 = t1071 - t1072 * t904 * t1075 * t566 / 0.288e3 + t1085 * t236 * t1086 * t1087 * t434 / 0.3072e4 + t1096 - t1099 * t236 * t1102 * t993 / 0.4608e4
  t1110 = t451 * t213
  t1111 = t455 ** 2
  t1112 = 0.1e1 / t1111
  t1113 = t72 * t1112
  t1115 = t914 * t915 * t1081
  t1117 = t331 * t434
  t1127 = 0.1e1 / t459
  t1131 = f.my_piecewise3(t464, -t998 + t1022 + t1060 + t1062 - t1067 + t192 * t319 * (params.beta * t1107 * t457 - t1110 * t1113 * (t1115 * t450 * t1087 * t1117 + t214 * t452 * t1107)) * t1127, t808)
  t1136 = f.my_piecewise3(t375, t253 * t984 / 0.2e1 + t808 * t32 / 0.2e1, t1131 * t56 / 0.2e1 - t465 * t566 / 0.2e1)
  t1139 = t92 * t115
  t1146 = 0.4e1 * t543 * t21 * t482
  t1149 = 0.4e1 * t18 * t548 * t482
  t1152 = f.my_piecewise3(t30, 0, 0.4e1 / 0.3e1 * t474 * t565)
  t1155 = f.my_piecewise3(t33, 0, 0.4e1 / 0.3e1 * t477 * t984)
  t1157 = (t1152 + t1155) * t159
  t1159 = t473 * t1157 * t183
  t1161 = t473 * t481 * t706
  t1163 = 0.58482236226346462072622386637590534819724553404281e0 * t1157 * t181
  t1166 = 0.18311447306006545054854346104378990962041954983034e-3 * t481 * t71 * t714
  t1169 = 0.58482236226346462072622386637590534819724553404281e0 * t481 * t172 * t719
  t1170 = t492 * t525
  t1171 = 0.1e1 / t474
  t1174 = f.my_piecewise3(t30, 0, 0.2e1 / 0.3e1 * t1171 * t565)
  t1175 = 0.1e1 / t477
  t1178 = f.my_piecewise3(t33, 0, 0.2e1 / 0.3e1 * t1175 * t984)
  t1180 = t1174 / 0.2e1 + t1178 / 0.2e1
  t1185 = 0.7e1 / 0.288e3 * t739 * t496
  t1187 = t204 * t156 * t501
  t1192 = t505 ** 2
  t1193 = 0.1e1 / t1192
  t1196 = t328 * t1193 * t224 * t228
  t1198 = t229 * t511 * t71
  t1202 = t72 * t511
  t1207 = (-(t638 + t662 + t1146 - t1149 + t1159 + t1161 + t1163 - t1166 - t1169) * t213 * t502 + 0.3e1 * t500 * t1202 * t1180) * t504
  t1215 = 0.7e1 / 0.4608e4 * t509 * t772 * t511 * t236
  t1218 = t328 * t506 * t224 * t228
  t1222 = t229 / t510 / t491 * t71
  t1227 = -t1185 - t1187 * t744 * t123 * t1180 / 0.48e2 - t1196 * t1198 * t756 * t1207 / 0.3072e4 - t1215 - t1218 * t1222 * t756 * t1180 / 0.768e3
  t1230 = t517 * t213
  t1231 = t520 ** 2
  t1232 = 0.1e1 / t1231
  t1233 = t72 * t1232
  t1234 = t1193 * t516
  t1244 = 0.1e1 / t524
  t1247 = t638 + t662 + t1146 - t1149 + t1159 + t1161 + t1163 - t1166 - t1169 + 0.3e1 * t192 * t1170 * t1180 + t192 * t493 * (params.beta * t1227 * t522 - t1230 * t1233 * (-t328 * t1234 * t1207 + t214 * t507 * t1227)) * t1244
  t1249 = -t609 * t469 - 0.2e1 * t611 * t469 * t629 - t117 * (t982 + t1136) + (0.2e1 * t1139 * t629 + t609) * t528 + t472 * t1247
  t1252 = t2 * t530
  vrho_0_ = t535 + t2 * t1249 * t534 + t1252 * (0.3e1 * t531 * t116 * t629 + params.d * t1249 * t532)
  t1262 = -t3 - t564
  t1263 = f.my_piecewise5(t30, 0, t33, 0, t1262)
  t1274 = s2 / t52 / t50 / r1
  t1295 = f.my_piecewise3(t7, 0, (-t538 - t542 - t546 - t550 - t554 - t558) * t90 - 0.4e1 * t563 * (-t35 * t1263 * t69 * t84 / 0.12e2 + t37 * (0.5e1 / 0.6e1 * t43 * t47 * t1263 - 0.8e1 / 0.3e1 * t1274 * t60 - 0.5e1 / 0.6e1 * t55 * t59 * t1263 + t586) * t84 / 0.24e2 + t70 * t76 * (-0.4e1 / 0.3e1 * t593 * t1263 + 0.4e1 / 0.3e1 * t597 * t1263) / 0.24e2))
  t1296 = t1295 * t116
  t1298 = t1262 / 0.2e1
  t1311 = f.my_piecewise3(t114, 0, -t613 - t68 * t615 * (-0.40e2 / 0.3e1 * t104 * t107 * t1298 - 0.40e2 / 0.3e1 * tau1 * t54 * t108 + 0.40e2 / 0.3e1 * t96 * t99 * t1298))
  t1317 = 0.4e1 * t664 * t184 * t1263
  t1320 = f.my_piecewise3(t148, 0, 0.4e1 / 0.3e1 * t77 * t1263)
  t1323 = f.my_piecewise3(t152, 0, -0.4e1 / 0.3e1 * t80 * t1263)
  t1324 = t1320 + t1323
  t1326 = t147 * t1324 * t184
  t1329 = 0.58482236226346462072622386637590534819724553404281e0 * t1324 * t159 * t181
  t1332 = f.my_piecewise3(t148, 0, 0.2e1 / 0.3e1 * t723 * t1263)
  t1335 = f.my_piecewise3(t152, 0, -0.2e1 / 0.3e1 * t727 * t1263)
  t1337 = t1332 / 0.2e1 + t1335 / 0.2e1
  t1352 = (-(t638 + t662 + t1317 + t1326 + t708 + t1329 - t716 - t721) * t213 * t218 + 0.3e1 * t216 * t760 * t1337) * t220
  t1361 = -t741 - t743 * t744 * t123 * t1337 / 0.48e2 - t753 * t755 * t756 * t1352 / 0.3072e4 - t776 - t779 * t783 * t756 * t1337 / 0.768e3
  t1375 = t638 + t662 + t1317 + t1326 + t708 + t1329 - t716 - t721 + 0.3e1 * t192 * t722 * t1337 + t192 * t201 * (params.beta * t1361 * t247 - t791 * t794 * (-t328 * t795 * t1352 + t214 * t223 * t1361)) * t805
  t1380 = t818 * t1263
  t1382 = t127 * t817 * t1380
  t1385 = (-t816 - 0.11073470983333333333333333333333333333333333333333e-2 * t1382) * t278
  t1387 = -t815 / 0.3e1 - t1382 / 0.3e1
  t1388 = t828 * t1387
  t1391 = t835 * t1387
  t1394 = t140 * t842 * t1380
  t1398 = t827 * (0.11807781499500000000000000000000000000000000000000e0 * t1388 - t833 - 0.18590165886666666666666666666666666666666666666667e-1 * t1382 + 0.19099794277500000000000000000000000000000000000000e-1 * t1391 - t841 - 0.51086165526666666666666666666666666666666666666667e-2 * t1394) * t847
  t1411 = (-t867 - 0.31311127083333333333333333333333333333333333333333e-3 * t1382) * t307
  t1417 = 0.87448811650000000000000000000000000000000000000000e-1 * t1388 - t876 - 0.10197154565000000000000000000000000000000000000000e-1 * t1382 + 0.55743234727500000000000000000000000000000000000000e-2 * t1391 - t879 - 0.27959640330000000000000000000000000000000000000000e-2 * t1394
  t1422 = t286 * (-(-t850 - 0.53237641966666666666666666666666666666666666666667e-3 * t1382) * t296 + t856 * (0.10974162105750000000000000000000000000000000000000e0 * t1388 - t858 - 0.16057569282500000000000000000000000000000000000000e-1 * t1382 + 0.19623283938750000000000000000000000000000000000000e-1 * t1391 - t861 - 0.32394954865000000000000000000000000000000000000000e-2 * t1394) * t864 + t1385 - t1398 - 0.58482236226346462072622386637590534819724553404281e0 * t1411 + 0.58482236226346462072622386637590534819724553404281e0 * t874 * t1417 * t882)
  t1424 = 0.58482236226346462072622386637590534819724553404281e0 * t286 * t1411
  t1428 = 0.58482236226346462072622386637590534819724553404281e0 * t890 * t873 * t1417 * t882
  t1433 = -t1385 + t1398 + t1422 + t1424 - t1428
  t1443 = t901 + t903 * t904 * t907 * t1263 / 0.288e3 + t924 * t236 * t925 * t1433 * t334 / 0.3072e4 + t942 + t945 * t236 * t948 * t1380 / 0.4608e4
  t1459 = f.my_piecewise3(t369, -t1385 + t1398 + t1422 + t1424 - t1428 + t192 * t319 * (params.beta * t1443 * t362 - t956 * t959 * (t961 * t355 * t1433 * t963 + t214 * t357 * t1443)) * t973, t1375)
  t1464 = f.my_piecewise3(t119, t253 * t1262 / 0.2e1 + t1375 * t29 / 0.2e1, t370 * t1263 / 0.2e1 + t1459 * t44 / 0.2e1)
  t1466 = -t1262
  t1470 = t992 * t1263
  t1472 = t127 * t991 * t1470
  t1475 = (-t990 + 0.11073470983333333333333333333333333333333333333333e-2 * t1472) * t396
  t1477 = -t989 / 0.3e1 + t1472 / 0.3e1
  t1478 = t1002 * t1477
  t1481 = t1009 * t1477
  t1484 = t140 * t1015 * t1470
  t1488 = t1001 * (0.11807781499500000000000000000000000000000000000000e0 * t1478 - t1007 + 0.18590165886666666666666666666666666666666666666667e-1 * t1472 + 0.19099794277500000000000000000000000000000000000000e-1 * t1481 - t1014 + 0.51086165526666666666666666666666666666666666666667e-2 * t1484) * t1020
  t1501 = (-t1040 + 0.31311127083333333333333333333333333333333333333333e-3 * t1472) * t418
  t1507 = 0.87448811650000000000000000000000000000000000000000e-1 * t1478 - t1049 + 0.10197154565000000000000000000000000000000000000000e-1 * t1472 + 0.55743234727500000000000000000000000000000000000000e-2 * t1481 - t1052 + 0.27959640330000000000000000000000000000000000000000e-2 * t1484
  t1512 = t286 * (-(-t1023 + 0.53237641966666666666666666666666666666666666666667e-3 * t1472) * t407 + t1029 * (0.10974162105750000000000000000000000000000000000000e0 * t1478 - t1031 + 0.16057569282500000000000000000000000000000000000000e-1 * t1472 + 0.19623283938750000000000000000000000000000000000000e-1 * t1481 - t1034 + 0.32394954865000000000000000000000000000000000000000e-2 * t1484) * t1037 + t1475 - t1488 - 0.58482236226346462072622386637590534819724553404281e0 * t1501 + 0.58482236226346462072622386637590534819724553404281e0 * t1047 * t1507 * t1055)
  t1514 = 0.58482236226346462072622386637590534819724553404281e0 * t286 * t1501
  t1518 = 0.58482236226346462072622386637590534819724553404281e0 * t1063 * t1046 * t1507 * t1055
  t1526 = -t1475 + t1488 + t1512 + t1514 - t1518
  t1543 = -t1274 * t321 * t428 / 0.36e2 + t1071 - t1072 * t904 * t1075 * t1263 / 0.288e3 + t1085 * t236 * t1086 * t1526 * t434 / 0.3072e4 - t328 * t438 / t51 / t439 / t50 * t447 / 0.576e3 + t1096 - t1099 * t236 * t1102 * t1470 / 0.4608e4
  t1559 = f.my_piecewise3(t464, -t1475 + t1488 + t1512 + t1514 - t1518 + t192 * t319 * (params.beta * t1543 * t457 - t1110 * t1113 * (t1115 * t450 * t1526 * t1117 + t214 * t452 * t1543)) * t1127, t1375)
  t1564 = f.my_piecewise3(t375, t1375 * t32 / 0.2e1 + t253 * t1466 / 0.2e1, -t465 * t1263 / 0.2e1 + t1559 * t56 / 0.2e1)
  t1573 = f.my_piecewise3(t30, 0, 0.4e1 / 0.3e1 * t474 * t1262)
  t1576 = f.my_piecewise3(t33, 0, 0.4e1 / 0.3e1 * t477 * t1466)
  t1578 = (t1573 + t1576) * t159
  t1580 = t473 * t1578 * t183
  t1582 = 0.58482236226346462072622386637590534819724553404281e0 * t1578 * t181
  t1585 = f.my_piecewise3(t30, 0, 0.2e1 / 0.3e1 * t1171 * t1262)
  t1588 = f.my_piecewise3(t33, 0, 0.2e1 / 0.3e1 * t1175 * t1466)
  t1590 = t1585 / 0.2e1 + t1588 / 0.2e1
  t1605 = (-(t638 + t662 - t1146 - t1149 + t1580 + t1161 + t1582 - t1166 - t1169) * t213 * t502 + 0.3e1 * t500 * t1202 * t1590) * t504
  t1614 = -t1185 - t1187 * t744 * t123 * t1590 / 0.48e2 - t1196 * t1198 * t756 * t1605 / 0.3072e4 - t1215 - t1218 * t1222 * t756 * t1590 / 0.768e3
  t1628 = t638 + t662 - t1146 - t1149 + t1580 + t1161 + t1582 - t1166 - t1169 + 0.3e1 * t192 * t1170 * t1590 + t192 * t493 * (params.beta * t1614 * t522 - t1230 * t1233 * (-t328 * t1234 * t1605 + t214 * t507 * t1614)) * t1244
  t1630 = -t1296 * t469 - 0.2e1 * t611 * t469 * t1311 - t117 * (t1464 + t1564) + (0.2e1 * t1139 * t1311 + t1296) * t528 + t472 * t1628
  vrho_1_ = t535 + t2 * t1630 * t534 + t1252 * (0.3e1 * t531 * t116 * t1311 + params.d * t1630 * t532)
  t1640 = t563 * t37
  t1644 = t75 * t83
  t1648 = f.my_piecewise3(t7, 0, -t1640 * (t42 * t48 - t67) * t71 * t1644 / 0.6e1)
  t1649 = t1648 * t116
  t1651 = t67 * t112
  t1652 = f.my_piecewise3(t114, 0, t1651)
  t1655 = 0.2e1 * t611 * t469 * t1652
  t1656 = t192 * t201
  t1657 = t203 * t156
  t1659 = t744 * t123
  t1660 = t1657 * t206 * t1659
  t1664 = t214 * t223 * t63 * t237
  t1666 = t1660 / 0.96e2 + t1664 / 0.1536e4
  t1669 = params.beta ** 2
  t1671 = t1669 * t240 * t913
  t1672 = t915 * t793
  t1676 = -t1671 * t1672 * t222 * t1666 + params.beta * t1666 * t247
  t1677 = t1676 * t805
  t1680 = t1656 * t1677 * t29 / 0.2e1
  t1690 = t42 * t320 * t135 * t325 / 0.96e2 + t328 * t336 * s0 * t342 * t352 / 0.1536e4
  t1705 = t192 * t201 * t1676 * t805
  t1706 = f.my_piecewise3(t369, t192 * t319 * (-t1669 * t355 * t913 * t915 * t958 * t336 * t1690 + params.beta * t1690 * t362) * t973, t1705)
  t1709 = f.my_piecewise3(t119, t1680, t1706 * t44 / 0.2e1)
  t1712 = t1656 * t1677 * t32 / 0.2e1
  t1713 = f.my_piecewise3(t464, 0, t1705)
  t1716 = f.my_piecewise3(t375, t1712, t1713 * t56 / 0.2e1)
  t1720 = 0.2e1 * t1139 * t1652
  t1724 = t472 * t190 * t191
  t1726 = t1657 * t494 * t1659
  t1730 = t214 * t507 * t63 * t513
  t1732 = t1726 / 0.96e2 + t1730 / 0.1536e4
  t1736 = t1669 * t516 * t913
  t1737 = t915 * t1232
  t1744 = t1724 * t493 * (-t1736 * t1737 * t506 * t1732 + params.beta * t1732 * t522) * t1244
  t1745 = -t1649 * t469 - t1655 - t117 * (t1709 + t1716) + (t1649 + t1720) * t528 + t1744
  t1752 = 0.3e1 * t531 * t116 * t1652
  vsigma_0_ = t2 * t1745 * t534 + t1252 * (params.d * t1745 * t532 + t1752)
  t1759 = f.my_piecewise3(t7, 0, t1640 * t67 * t71 * t1644 / 0.3e1)
  t1760 = t1759 * t116
  t1763 = f.my_piecewise3(t114, 0, 0.2e1 * t1651)
  t1769 = t1660 / 0.48e2 + t1664 / 0.768e3
  t1775 = -t1671 * t1672 * t222 * t1769 + params.beta * t1769 * t247
  t1776 = t1775 * t805
  t1782 = t192 * t201 * t1775 * t805
  t1783 = f.my_piecewise3(t369, 0, t1782)
  t1786 = f.my_piecewise3(t119, t1656 * t1776 * t29 / 0.2e1, t1783 * t44 / 0.2e1)
  t1790 = f.my_piecewise3(t464, 0, t1782)
  t1793 = f.my_piecewise3(t375, t1656 * t1776 * t32 / 0.2e1, t1790 * t56 / 0.2e1)
  t1802 = t1726 / 0.48e2 + t1730 / 0.768e3
  t1812 = -t1760 * t469 - 0.2e1 * t611 * t469 * t1763 - t117 * (t1786 + t1793) + (0.2e1 * t1139 * t1763 + t1760) * t528 + t1724 * t493 * (-t1736 * t1737 * t506 * t1802 + params.beta * t1802 * t522) * t1244
  vsigma_1_ = t2 * t1812 * t534 + t1252 * (0.3e1 * t531 * t116 * t1763 + params.d * t1812 * t532)
  t1828 = f.my_piecewise3(t7, 0, -t1640 * (t54 * t60 - t67) * t71 * t1644 / 0.6e1)
  t1829 = t1828 * t116
  t1831 = f.my_piecewise3(t369, 0, t1705)
  t1834 = f.my_piecewise3(t119, t1680, t1831 * t44 / 0.2e1)
  t1844 = t54 * t320 * t135 * t428 / 0.96e2 + t328 * t436 * s2 * t442 * t447 / 0.1536e4
  t1857 = f.my_piecewise3(t464, t192 * t319 * (-t1669 * t450 * t913 * t915 * t1112 * t436 * t1844 + params.beta * t1844 * t457) * t1127, t1705)
  t1860 = f.my_piecewise3(t375, t1712, t1857 * t56 / 0.2e1)
  t1865 = -t1829 * t469 - t1655 - t117 * (t1834 + t1860) + (t1829 + t1720) * t528 + t1744
  vsigma_2_ = t2 * t1865 * t534 + t1252 * (params.d * t1865 * t532 + t1752)
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t1876 = f.my_piecewise3(t114, 0, -0.8e1 * t68 * t615 * t95 * t100)
  t1882 = 0.2e1 * t1139 * t1876 * t528 - 0.2e1 * t611 * t469 * t1876
  vtau_0_ = t2 * t1882 * t534 + t1252 * (0.3e1 * t531 * t116 * t1876 + params.d * t1882 * t532)
  t1896 = f.my_piecewise3(t114, 0, -0.8e1 * t68 * t615 * t103 * t108)
  t1902 = 0.2e1 * t1139 * t1896 * t528 - 0.2e1 * t611 * t469 * t1896
  vtau_1_ = t2 * t1902 * t534 + t1252 * (0.3e1 * t531 * t116 * t1896 + params.d * t1902 * t532)
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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
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

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mbeta = lambda rs=None, t=None: params_beta

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  tpss_xi2 = lambda z, xt, xs0, xs1: (1 - z ** 2) * (f.t_total(z, xs0 ** 2, xs1 ** 2) - xt ** 2) / (2 * (3 * jnp.pi ** 2) ** (1 / 3)) ** 2

  tpss_C00 = lambda cc, z: +jnp.sum(jnp.array([cc[i] * z ** (2 * (i - 1)) for i in range(1, 4 + 1)]), axis=0)

  tpss_aux = lambda z, xt, ts0, ts1: jnp.minimum(xt ** 2 / (8 * f.t_total(z, ts0, ts1)), 1)

  tpss_par_s0 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 + z)) ** (1 / 3), 1, xs0, xs0, 0), f_gga(rs, z, xt, xs0, xs1)) * (1 + z) / 2

  tpss_par_s1 = lambda f_gga, rs, z, xt, xs0, xs1: jnp.maximum(f_gga(rs * (2 / (1 - z)) ** (1 / 3), -1, xs1, 0, xs1), f_gga(rs, z, xt, xs0, xs1)) * (1 - z) / 2

  mgamma = params_gamma

  BB = params_BB

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

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
  t159 = 0.1e1 / t19 / t18
  t160 = s0 * t159
  t161 = t160 * t15
  t162 = 0.1e1 / t156
  t164 = 0.1e1 / t76
  t165 = t164 * t78
  t166 = t162 * t90 * t165
  t169 = 0.1e1 / t146
  t170 = params.beta * t169
  t171 = 0.58482236226346462072622386637590534819724553404281e0 * t143
  t174 = 0.1e1 / t157
  t177 = jnp.exp(-(-t101 + t140 + t171) * t169 * t41 * t174)
  t178 = t177 - 0.1e1
  t179 = 0.1e1 / t178
  t180 = t41 * t179
  t181 = s0 ** 2
  t183 = t170 * t180 * t181
  t184 = t18 ** 2
  t186 = 0.1e1 / t20 / t184
  t187 = t186 * t16
  t188 = t156 ** 2
  t189 = 0.1e1 / t188
  t191 = 0.1e1 / t91
  t193 = t40 * t191 * t79
  t194 = t187 * t189 * t193
  t197 = t161 * t166 / 0.96e2 + t183 * t194 / 0.3072e4
  t198 = params.beta * t197
  t199 = t169 * t41
  t202 = t170 * t180 * t197 + 0.1e1
  t204 = t199 / t202
  t206 = t198 * t204 + 0.1e1
  t207 = jnp.log(t206)
  t209 = t148 * t157 * t207
  t211 = -t101 / 0.2e1 + t140 / 0.2e1 + 0.29241118113173231036311193318795267409862276702140e0 * t143 + t209 / 0.2e1
  t212 = -t101 + t140 + t171 + t209
  t213 = t77 * t79
  t214 = t80 * t15
  t216 = (0.1e1 / t23) ** (0.1e1 / 0.3e1)
  t218 = t213 * t214 * t216
  t220 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t218
  t221 = jnp.sqrt(t218)
  t224 = t218 ** 0.15e1
  t226 = t92 * t78
  t227 = t93 * t16
  t228 = t216 ** 2
  t230 = t226 * t227 * t228
  t232 = 0.23615562999000000000000000000000000000000000000000e0 * t221 + 0.55770497660000000000000000000000000000000000000000e-1 * t218 + 0.12733196185000000000000000000000000000000000000000e-1 * t224 + 0.76629248290000000000000000000000000000000000000000e-2 * t230
  t234 = 0.1e1 + 0.1e1 / t232
  t235 = jnp.log(t234)
  t236 = t220 * t235
  t237 = 0.2e1 <= f.p.zeta_threshold
  t239 = f.my_piecewise3(t237, t106, 0.2e1 * t15)
  t240 = 0.0e0 <= f.p.zeta_threshold
  t241 = f.my_piecewise3(t240, t106, 0)
  t243 = (t239 + t241 - 0.2e1) * t114
  t245 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t218
  t250 = 0.21948324211500000000000000000000000000000000000000e0 * t221 + 0.48172707847500000000000000000000000000000000000000e-1 * t218 + 0.13082189292500000000000000000000000000000000000000e-1 * t224 + 0.48592432297500000000000000000000000000000000000000e-2 * t230
  t252 = 0.1e1 + 0.1e1 / t250
  t253 = jnp.log(t252)
  t256 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t218
  t261 = 0.17489762330000000000000000000000000000000000000000e0 * t221 + 0.30591463695000000000000000000000000000000000000000e-1 * t218 + 0.37162156485000000000000000000000000000000000000000e-2 * t224 + 0.41939460495000000000000000000000000000000000000000e-2 * t230
  t263 = 0.1e1 + 0.1e1 / t261
  t264 = jnp.log(t263)
  t265 = t256 * t264
  t268 = t243 * (-t245 * t253 + t236 - 0.58482236226346462072622386637590534819724553404281e0 * t265)
  t270 = 0.58482236226346462072622386637590534819724553404281e0 * t243 * t265
  t271 = f.my_piecewise3(t237, t149, t16)
  t272 = f.my_piecewise3(t240, t149, 0)
  t274 = t271 / 0.2e1 + t272 / 0.2e1
  t275 = t274 ** 2
  t276 = t275 * t274
  t277 = 0.1e1 / t275
  t278 = t277 * t90
  t279 = t160 * t278
  t282 = t165 * t16 / t216
  t285 = t170 * t41
  t288 = 0.1e1 / t276
  t289 = t41 * t288
  t291 = jnp.exp(-(-t236 + t268 + t270) * t169 * t289)
  t292 = t291 - 0.1e1
  t293 = 0.1e1 / t292
  t294 = t293 * t181
  t297 = t275 ** 2
  t300 = 0.1e1 / t297 * t40 * t191
  t301 = t79 * t15
  t302 = 0.1e1 / t228
  t304 = t300 * t301 * t302
  t307 = t279 * t282 / 0.96e2 + t285 * t294 * t186 * t304 / 0.1536e4
  t308 = params.beta * t307
  t309 = t41 * t293
  t312 = t170 * t309 * t307 + 0.1e1
  t314 = t199 / t312
  t316 = t308 * t314 + 0.1e1
  t317 = jnp.log(t316)
  t320 = t148 * t276 * t317 - t236 + t268 + t270
  t321 = t212 < t320
  t322 = f.my_piecewise3(t321, t320, t212)
  t325 = f.my_piecewise3(t74, t211, t322 * t23 / 0.2e1)
  t327 = (0.1e1 / t30) ** (0.1e1 / 0.3e1)
  t329 = t213 * t214 * t327
  t331 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t329
  t332 = jnp.sqrt(t329)
  t335 = t329 ** 0.15e1
  t337 = t327 ** 2
  t339 = t226 * t227 * t337
  t341 = 0.23615562999000000000000000000000000000000000000000e0 * t332 + 0.55770497660000000000000000000000000000000000000000e-1 * t329 + 0.12733196185000000000000000000000000000000000000000e-1 * t335 + 0.76629248290000000000000000000000000000000000000000e-2 * t339
  t343 = 0.1e1 + 0.1e1 / t341
  t344 = jnp.log(t343)
  t345 = t331 * t344
  t347 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t329
  t352 = 0.21948324211500000000000000000000000000000000000000e0 * t332 + 0.48172707847500000000000000000000000000000000000000e-1 * t329 + 0.13082189292500000000000000000000000000000000000000e-1 * t335 + 0.48592432297500000000000000000000000000000000000000e-2 * t339
  t354 = 0.1e1 + 0.1e1 / t352
  t355 = jnp.log(t354)
  t358 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t329
  t363 = 0.17489762330000000000000000000000000000000000000000e0 * t332 + 0.30591463695000000000000000000000000000000000000000e-1 * t329 + 0.37162156485000000000000000000000000000000000000000e-2 * t335 + 0.41939460495000000000000000000000000000000000000000e-2 * t339
  t365 = 0.1e1 + 0.1e1 / t363
  t366 = jnp.log(t365)
  t367 = t358 * t366
  t370 = t243 * (-t347 * t355 + t345 - 0.58482236226346462072622386637590534819724553404281e0 * t367)
  t372 = 0.58482236226346462072622386637590534819724553404281e0 * t243 * t367
  t375 = t165 * t16 / t327
  t381 = jnp.exp(-(-t345 + t370 + t372) * t169 * t289)
  t382 = t381 - 0.1e1
  t383 = 0.1e1 / t382
  t384 = t383 * t181
  t387 = 0.1e1 / t337
  t389 = t300 * t301 * t387
  t392 = t279 * t375 / 0.96e2 + t285 * t384 * t186 * t389 / 0.1536e4
  t393 = params.beta * t392
  t394 = t41 * t383
  t397 = t170 * t394 * t392 + 0.1e1
  t399 = t199 / t397
  t401 = t393 * t399 + 0.1e1
  t402 = jnp.log(t401)
  t405 = t148 * t276 * t402 - t345 + t370 + t372
  t406 = t212 < t405
  t407 = f.my_piecewise3(t406, t405, t212)
  t410 = f.my_piecewise3(t74, t211, t407 * t30 / 0.2e1)
  t411 = t325 + t410
  t414 = t61 * t70 + 0.1e1
  t415 = f.my_piecewise3(t9, t106, 1)
  t418 = (0.2e1 * t415 - 0.2e1) * t114
  t420 = 0.58482236226346462072622386637590534819724553404281e0 * t418 * t136
  t421 = f.my_piecewise3(t9, t149, 1)
  t422 = t421 ** 2
  t423 = t422 * t421
  t424 = 0.1e1 / t422
  t426 = t424 * t90 * t165
  t431 = 0.1e1 / t423
  t434 = jnp.exp(-(-t101 + t420) * t169 * t41 * t431)
  t435 = t434 - 0.1e1
  t436 = 0.1e1 / t435
  t437 = t41 * t436
  t439 = t170 * t437 * t181
  t440 = t422 ** 2
  t441 = 0.1e1 / t440
  t443 = t187 * t441 * t193
  t446 = t161 * t426 / 0.96e2 + t439 * t443 / 0.3072e4
  t447 = params.beta * t446
  t450 = t170 * t437 * t446 + 0.1e1
  t452 = t199 / t450
  t454 = t447 * t452 + 0.1e1
  t455 = jnp.log(t454)
  t458 = t148 * t423 * t455 - t101 + t420
  t460 = -t71 * t411 + t414 * t458
  t461 = params.d * t460
  t462 = t70 * t69
  t464 = t461 * t462 + 0.1e1
  t469 = t4 / t58 / t56 * t14
  t470 = t18 * r0
  t472 = 0.1e1 / t20 / t470
  t481 = t44 * t52
  t485 = f.my_piecewise3(t3, 0, -t469 * (-0.8e1 / 0.3e1 * t17 * t472 * t27 - 0.8e1 / 0.3e1 * t17 * t472 * t34 + 0.8e1 / 0.3e1 * s0 * t472) * t40 * t481 / 0.6e1)
  t486 = t485 * t70
  t488 = t62 * t69
  t493 = f.my_piecewise3(t68, 0, -s0 / t18 * t65 / 0.8e1)
  t498 = 0.1e1 / t19 / r0
  t499 = t79 * t498
  t501 = t77 * t499 * t100
  t503 = t97 ** 2
  t508 = t76 * t79
  t509 = t508 * t498
  t510 = 0.1e1 / t85 * t40 * t509
  t512 = t77 * t499
  t514 = t82 ** 0.5e0
  t516 = t514 * t40 * t509
  t519 = 0.1e1 / t20 / r0
  t521 = t92 * t78 * t519
  t526 = t84 / t503 * (-0.39359271665000000000000000000000000000000000000000e-1 * t510 - 0.18590165886666666666666666666666666666666666666667e-1 * t512 - 0.63665980925000000000000000000000000000000000000000e-2 * t516 - 0.51086165526666666666666666666666666666666666666667e-2 * t521) / t99
  t531 = t121 ** 2
  t542 = 0.11073470983333333333333333333333333333333333333333e-2 * t501
  t546 = t132 ** 2
  t547 = 0.1e1 / t546
  t553 = -0.29149603883333333333333333333333333333333333333333e-1 * t510 - 0.10197154565000000000000000000000000000000000000000e-1 * t512 - 0.18581078242500000000000000000000000000000000000000e-2 * t516 - 0.27959640330000000000000000000000000000000000000000e-2 * t521
  t554 = 0.1e1 / t134
  t560 = t111 * t114 * (0.53237641966666666666666666666666666666666666666667e-3 * t77 * t499 * t124 + t116 / t531 * (-0.36580540352500000000000000000000000000000000000000e-1 * t510 - 0.16057569282500000000000000000000000000000000000000e-1 * t512 - 0.65410946462500000000000000000000000000000000000000e-2 * t516 - 0.32394954865000000000000000000000000000000000000000e-2 * t521) / t123 - t542 - t526 + 0.18311447306006545054854346104378990962041954983034e-3 * t77 * t499 * t135 + 0.58482236226346462072622386637590534819724553404281e0 * t127 * t547 * t553 * t554)
  t564 = t508 * t498 * t135
  t565 = t142 * t40 * t564
  t569 = t547 * t553 * t554
  t570 = t142 * t127 * t569
  t574 = s0 / t19 / t470
  t575 = t574 * t15
  t578 = t146 ** 2
  t579 = 0.1e1 / t578
  t580 = params.beta * t579
  t581 = t41 ** 2
  t582 = t580 * t581
  t583 = t178 ** 2
  t584 = 0.1e1 / t583
  t592 = t191 * t79
  t593 = 0.18311447306006545054854346104378990962041954983034e-3 * t565
  t594 = 0.58482236226346462072622386637590534819724553404281e0 * t570
  t595 = t542 + t526 + t560 - t593 - t594
  t603 = 0.1e1 / t20 / t184 / r0
  t604 = t603 * t16
  t609 = -0.7e1 / 0.288e3 * t575 * t166 + t582 * t584 * t181 * t186 * t16 / t188 / t157 * t40 * t592 * t595 * t177 / 0.3072e4 - 0.7e1 / 0.4608e4 * t183 * t604 * t189 * t193
  t613 = t202 ** 2
  t614 = 0.1e1 / t613
  t629 = 0.1e1 / t206
  t631 = t148 * t157 * (params.beta * t609 * t204 - t198 * t169 * t41 * t614 * (t580 * t581 * t584 * t197 * t595 * t174 * t177 + t170 * t180 * t609)) * t629
  t633 = 0.55367354916666666666666666666666666666666666666665e-3 * t501 + t526 / 0.2e1 + t560 / 0.2e1 - 0.91557236530032725274271730521894954810209774915169e-4 * t565 - 0.29241118113173231036311193318795267409862276702140e0 * t570 + t631 / 0.2e1
  t634 = t498 * t15
  t638 = 0.11073470983333333333333333333333333333333333333333e-2 * t213 * t634 * t216 * t235
  t639 = t232 ** 2
  t645 = t15 * t216
  t646 = t499 * t645
  t647 = 0.1e1 / t221 * t40 * t76 * t646
  t650 = t213 * t634 * t216
  t652 = t218 ** 0.5e0
  t655 = t652 * t40 * t76 * t646
  t657 = t519 * t16
  t659 = t226 * t657 * t228
  t664 = t220 / t639 * (-0.39359271665000000000000000000000000000000000000000e-1 * t647 - 0.18590165886666666666666666666666666666666666666667e-1 * t650 - 0.63665980925000000000000000000000000000000000000000e-2 * t655 - 0.51086165526666666666666666666666666666666666666667e-2 * t659) / t234
  t669 = t250 ** 2
  t684 = t261 ** 2
  t685 = 0.1e1 / t684
  t691 = -0.29149603883333333333333333333333333333333333333333e-1 * t647 - 0.10197154565000000000000000000000000000000000000000e-1 * t650 - 0.18581078242500000000000000000000000000000000000000e-2 * t655 - 0.27959640330000000000000000000000000000000000000000e-2 * t659
  t692 = 0.1e1 / t263
  t697 = t243 * (0.53237641966666666666666666666666666666666666666667e-3 * t213 * t634 * t216 * t253 + t245 / t669 * (-0.36580540352500000000000000000000000000000000000000e-1 * t647 - 0.16057569282500000000000000000000000000000000000000e-1 * t650 - 0.65410946462500000000000000000000000000000000000000e-2 * t655 - 0.32394954865000000000000000000000000000000000000000e-2 * t659) / t252 - t638 - t664 + 0.18311447306006545054854346104378990962041954983034e-3 * t213 * t634 * t216 * t264 + 0.58482236226346462072622386637590534819724553404281e0 * t256 * t685 * t691 * t692)
  t698 = t243 * t77
  t702 = 0.18311447306006545054854346104378990962041954983034e-3 * t698 * t499 * t645 * t264
  t707 = 0.58482236226346462072622386637590534819724553404281e0 * t243 * t256 * t685 * t691 * t692
  t708 = t574 * t278
  t711 = t292 ** 2
  t712 = 0.1e1 / t711
  t716 = t186 / t297 / t276
  t720 = t638 + t664 + t697 - t702 - t707
  t730 = -0.7e1 / 0.288e3 * t708 * t282 + t582 * t712 * t181 * t716 * t193 * t15 * t302 * t720 * t291 / 0.1536e4 - 0.7e1 / 0.2304e4 * t285 * t294 * t603 * t304
  t734 = t312 ** 2
  t735 = 0.1e1 / t734
  t750 = 0.1e1 / t316
  t754 = t542 + t526 + t560 - t593 - t594 + t631
  t755 = f.my_piecewise3(t321, t638 + t664 + t697 - t702 - t707 + t148 * t276 * (params.beta * t730 * t314 - t308 * t169 * t41 * t735 * (t580 * t581 * t712 * t307 * t720 * t288 * t291 + t170 * t309 * t730)) * t750, t754)
  t758 = f.my_piecewise3(t74, t633, t755 * t23 / 0.2e1)
  t762 = 0.11073470983333333333333333333333333333333333333333e-2 * t213 * t634 * t327 * t344
  t763 = t341 ** 2
  t769 = t15 * t327
  t770 = t499 * t769
  t771 = 0.1e1 / t332 * t40 * t76 * t770
  t774 = t213 * t634 * t327
  t776 = t329 ** 0.5e0
  t779 = t776 * t40 * t76 * t770
  t782 = t226 * t657 * t337
  t787 = t331 / t763 * (-0.39359271665000000000000000000000000000000000000000e-1 * t771 - 0.18590165886666666666666666666666666666666666666667e-1 * t774 - 0.63665980925000000000000000000000000000000000000000e-2 * t779 - 0.51086165526666666666666666666666666666666666666667e-2 * t782) / t343
  t792 = t352 ** 2
  t807 = t363 ** 2
  t808 = 0.1e1 / t807
  t814 = -0.29149603883333333333333333333333333333333333333333e-1 * t771 - 0.10197154565000000000000000000000000000000000000000e-1 * t774 - 0.18581078242500000000000000000000000000000000000000e-2 * t779 - 0.27959640330000000000000000000000000000000000000000e-2 * t782
  t815 = 0.1e1 / t365
  t820 = t243 * (0.53237641966666666666666666666666666666666666666667e-3 * t213 * t634 * t327 * t355 + t347 / t792 * (-0.36580540352500000000000000000000000000000000000000e-1 * t771 - 0.16057569282500000000000000000000000000000000000000e-1 * t774 - 0.65410946462500000000000000000000000000000000000000e-2 * t779 - 0.32394954865000000000000000000000000000000000000000e-2 * t782) / t354 - t762 - t787 + 0.18311447306006545054854346104378990962041954983034e-3 * t213 * t634 * t327 * t366 + 0.58482236226346462072622386637590534819724553404281e0 * t358 * t808 * t814 * t815)
  t824 = 0.18311447306006545054854346104378990962041954983034e-3 * t698 * t499 * t769 * t366
  t829 = 0.58482236226346462072622386637590534819724553404281e0 * t243 * t358 * t808 * t814 * t815
  t832 = t382 ** 2
  t833 = 0.1e1 / t832
  t838 = t762 + t787 + t820 - t824 - t829
  t848 = -0.7e1 / 0.288e3 * t708 * t375 + t582 * t833 * t181 * t716 * t193 * t15 * t387 * t838 * t381 / 0.1536e4 - 0.7e1 / 0.2304e4 * t285 * t384 * t603 * t389
  t852 = t397 ** 2
  t853 = 0.1e1 / t852
  t868 = 0.1e1 / t401
  t872 = f.my_piecewise3(t406, t762 + t787 + t820 - t824 - t829 + t148 * t276 * (params.beta * t848 * t399 - t393 * t169 * t41 * t853 * (t580 * t581 * t833 * t392 * t838 * t288 * t381 + t170 * t394 * t848)) * t868, t754)
  t875 = f.my_piecewise3(t74, t633, t872 * t30 / 0.2e1)
  t878 = t61 * t69
  t885 = 0.18311447306006545054854346104378990962041954983034e-3 * t418 * t40 * t564
  t888 = 0.58482236226346462072622386637590534819724553404281e0 * t418 * t127 * t569
  t891 = t435 ** 2
  t892 = 0.1e1 / t891
  t900 = t542 + t526 - t885 - t888
  t910 = -0.7e1 / 0.288e3 * t575 * t426 + t582 * t892 * t181 * t186 * t16 / t440 / t423 * t40 * t592 * t900 * t434 / 0.3072e4 - 0.7e1 / 0.4608e4 * t439 * t604 * t441 * t193
  t914 = t450 ** 2
  t915 = 0.1e1 / t914
  t930 = 0.1e1 / t454
  t935 = -t486 * t411 - 0.2e1 * t488 * t411 * t493 - t71 * (t758 + t875) + (0.2e1 * t878 * t493 + t486) * t458 + t414 * (t542 + t526 - t885 - t888 + t148 * t423 * (params.beta * t910 * t452 - t447 * t169 * t41 * t915 * (t580 * t581 * t892 * t446 * t900 * t431 * t434 + t170 * t437 * t910)) * t930)
  t938 = r0 * t460
  vrho_0_ = t460 * t464 + r0 * t935 * t464 + t938 * (0.3e1 * t461 * t70 * t493 + params.d * t935 * t462)
  t946 = t16 * t22
  t954 = f.my_piecewise3(t3, 0, -t469 * (t946 * t27 + t946 * t34 - t22) * t40 * t481 / 0.6e1)
  t955 = t954 * t70
  t959 = f.my_piecewise3(t68, 0, t63 * t65 / 0.8e1)
  t963 = t159 * t15
  t966 = t90 * t164 * t78
  t973 = t963 * t162 * t966 / 0.96e2 + t170 * t180 * s0 * t194 / 0.1536e4
  t976 = params.beta ** 2
  t986 = t148 * t157 * (-t976 * t197 * t579 * t581 * t614 * t179 * t973 + params.beta * t973 * t204) * t629
  t987 = t986 / 0.2e1
  t989 = t159 * t277 * t90
  t997 = t989 * t282 / 0.96e2 + t285 * t293 * s0 * t186 * t304 / 0.768e3
  t1010 = f.my_piecewise3(t321, t148 * t276 * (-t976 * t307 * t579 * t581 * t735 * t293 * t997 + params.beta * t997 * t314) * t750, t986)
  t1013 = f.my_piecewise3(t74, t987, t1010 * t23 / 0.2e1)
  t1021 = t989 * t375 / 0.96e2 + t285 * t383 * s0 * t186 * t389 / 0.768e3
  t1034 = f.my_piecewise3(t406, t148 * t276 * (-t976 * t392 * t579 * t581 * t853 * t383 * t1021 + params.beta * t1021 * t399) * t868, t986)
  t1037 = f.my_piecewise3(t74, t987, t1034 * t30 / 0.2e1)
  t1053 = t963 * t424 * t966 / 0.96e2 + t170 * t437 * s0 * t443 / 0.1536e4
  t1066 = -t955 * t411 - 0.2e1 * t488 * t411 * t959 - t71 * (t1013 + t1037) + (0.2e1 * t878 * t959 + t955) * t458 + t414 * t146 * t147 * t423 * (-t976 * t446 * t579 * t581 * t915 * t436 * t1053 + params.beta * t1053 * t452) * t930
  vsigma_0_ = r0 * t1066 * t464 + t938 * (params.d * t1066 * t462 + 0.3e1 * t461 * t70 * t959)
  vlapl_0_ = 0.0e0
  t1076 = tau0 ** 2
  t1080 = f.my_piecewise3(t68, 0, -t64 / t1076 / 0.8e1)
  t1086 = -0.2e1 * t488 * t411 * t1080 + 0.2e1 * t878 * t1080 * t458
  vtau_0_ = r0 * t1086 * t464 + t938 * (0.3e1 * t461 * t70 * t1080 + params.d * t1086 * t462)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
  return res

