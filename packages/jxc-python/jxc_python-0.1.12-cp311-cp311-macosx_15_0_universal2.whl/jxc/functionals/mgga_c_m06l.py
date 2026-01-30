"""Generated from mgga_c_m06l.mpl."""

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
  params_alpha_ab_raw = params.alpha_ab
  if isinstance(params_alpha_ab_raw, (str, bytes, dict)):
    params_alpha_ab = params_alpha_ab_raw
  else:
    try:
      params_alpha_ab_seq = list(params_alpha_ab_raw)
    except TypeError:
      params_alpha_ab = params_alpha_ab_raw
    else:
      params_alpha_ab_seq = np.asarray(params_alpha_ab_seq, dtype=np.float64)
      params_alpha_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_ab_seq))
  params_alpha_ss_raw = params.alpha_ss
  if isinstance(params_alpha_ss_raw, (str, bytes, dict)):
    params_alpha_ss = params_alpha_ss_raw
  else:
    try:
      params_alpha_ss_seq = list(params_alpha_ss_raw)
    except TypeError:
      params_alpha_ss = params_alpha_ss_raw
    else:
      params_alpha_ss_seq = np.asarray(params_alpha_ss_seq, dtype=np.float64)
      params_alpha_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_ss_seq))
  params_cab_raw = params.cab
  if isinstance(params_cab_raw, (str, bytes, dict)):
    params_cab = params_cab_raw
  else:
    try:
      params_cab_seq = list(params_cab_raw)
    except TypeError:
      params_cab = params_cab_raw
    else:
      params_cab_seq = np.asarray(params_cab_seq, dtype=np.float64)
      params_cab = np.concatenate((np.array([np.nan], dtype=np.float64), params_cab_seq))
  params_css_raw = params.css
  if isinstance(params_css_raw, (str, bytes, dict)):
    params_css = params_css_raw
  else:
    try:
      params_css_seq = list(params_css_raw)
    except TypeError:
      params_css = params_css_raw
    else:
      params_css_seq = np.asarray(params_css_seq, dtype=np.float64)
      params_css = np.concatenate((np.array([np.nan], dtype=np.float64), params_css_seq))
  params_dab_raw = params.dab
  if isinstance(params_dab_raw, (str, bytes, dict)):
    params_dab = params_dab_raw
  else:
    try:
      params_dab_seq = list(params_dab_raw)
    except TypeError:
      params_dab = params_dab_raw
    else:
      params_dab_seq = np.asarray(params_dab_seq, dtype=np.float64)
      params_dab = np.concatenate((np.array([np.nan], dtype=np.float64), params_dab_seq))
  params_dss_raw = params.dss
  if isinstance(params_dss_raw, (str, bytes, dict)):
    params_dss = params_dss_raw
  else:
    try:
      params_dss_seq = list(params_dss_raw)
    except TypeError:
      params_dss = params_dss_raw
    else:
      params_dss_seq = np.asarray(params_dss_seq, dtype=np.float64)
      params_dss = np.concatenate((np.array([np.nan], dtype=np.float64), params_dss_seq))
  params_gamma_ab_raw = params.gamma_ab
  if isinstance(params_gamma_ab_raw, (str, bytes, dict)):
    params_gamma_ab = params_gamma_ab_raw
  else:
    try:
      params_gamma_ab_seq = list(params_gamma_ab_raw)
    except TypeError:
      params_gamma_ab = params_gamma_ab_raw
    else:
      params_gamma_ab_seq = np.asarray(params_gamma_ab_seq, dtype=np.float64)
      params_gamma_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_ab_seq))
  params_gamma_ss_raw = params.gamma_ss
  if isinstance(params_gamma_ss_raw, (str, bytes, dict)):
    params_gamma_ss = params_gamma_ss_raw
  else:
    try:
      params_gamma_ss_seq = list(params_gamma_ss_raw)
    except TypeError:
      params_gamma_ss = params_gamma_ss_raw
    else:
      params_gamma_ss_seq = np.asarray(params_gamma_ss_seq, dtype=np.float64)
      params_gamma_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_ss_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  gvt4_gamm = lambda alpha, x, z: 1 + alpha * (x ** 2 + z)

  b97_g = lambda gamma, cc, x: jnp.sum(jnp.array([cc[i] * (gamma * x ** 2 / (1 + gamma * x ** 2)) ** (i - 1) for i in range(1, 5 + 1)]), axis=0)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  gtv4 = lambda alpha, dd, x, z: dd[1] / gvt4_gamm(alpha, x, z) + (dd[2] * x ** 2 + dd[3] * z) / gvt4_gamm(alpha, x, z) ** 2 + (dd[4] * x ** 4 + dd[5] * x ** 2 * z + dd[6] * z ** 2) / gvt4_gamm(alpha, x, z) ** 3

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  vsxc_comp = lambda rs, z, spin, xs, ts: +lda_stoll_par(f, params, f_pw, rs, z, 1) * gtv4(params_alpha_ss, params_dss, xs, 2 * (ts - K_FACTOR_C)) * f.Fermi_D(xs, ts)

  vsxc_fperp = lambda rs, z, xs0, xs1, ts0, ts1: +lda_stoll_perp(f, params, f_pw, rs, z) * gtv4(params_alpha_ab, params_dab, jnp.sqrt(xs0 ** 2 + xs1 ** 2), 2 * (ts0 + ts1 - 2 * K_FACTOR_C))

  m05_comp = lambda rs, z, spin, xs, t: +lda_stoll_par(f, params, f_pw, rs, z, 1) * b97_g(params_gamma_ss, params_css, xs) * f.Fermi_D_corrected(xs, t)

  m05_fperp = lambda rs, z, xs0, xs1, t0=None, t1=None: +lda_stoll_perp(f, params, f_pw, rs, z) * b97_g(params_gamma_ab, params_cab, jnp.sqrt(xs0 ** 2 + xs1 ** 2))

  vsxc_fpar = lambda rs, z, xs0, xs1, ts0, ts1: +vsxc_comp(rs, z, 1, xs0, ts0) + vsxc_comp(rs, -z, -1, xs1, ts1)

  m05_fpar = lambda rs, z, xs0, xs1, t0, t1: +m05_comp(rs, z, 1, xs0, t0) + m05_comp(rs, -z, -1, xs1, t1)

  vsxc_f = lambda rs, z, xs0, xs1, ts0, ts1: +vsxc_fpar(rs, z, xs0, xs1, ts0, ts1) + vsxc_fperp(rs, z, xs0, xs1, ts0, ts1)

  m05_f = lambda rs, z, xs0, xs1, t0, t1: +m05_fpar(rs, z, xs0, xs1, t0, t1) + m05_fperp(rs, z, xs0, xs1, t0, t1)

  m06l_f = lambda rs, z, xs0, xs1, ts0, ts1: +m05_f(rs, z, xs0, xs1, ts0, ts1) + vsxc_f(rs, z, xs0, xs1, ts0, ts1)

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: m06l_f(rs, z, xs0, xs1, ts0, ts1)

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
  params_alpha_ab_raw = params.alpha_ab
  if isinstance(params_alpha_ab_raw, (str, bytes, dict)):
    params_alpha_ab = params_alpha_ab_raw
  else:
    try:
      params_alpha_ab_seq = list(params_alpha_ab_raw)
    except TypeError:
      params_alpha_ab = params_alpha_ab_raw
    else:
      params_alpha_ab_seq = np.asarray(params_alpha_ab_seq, dtype=np.float64)
      params_alpha_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_ab_seq))
  params_alpha_ss_raw = params.alpha_ss
  if isinstance(params_alpha_ss_raw, (str, bytes, dict)):
    params_alpha_ss = params_alpha_ss_raw
  else:
    try:
      params_alpha_ss_seq = list(params_alpha_ss_raw)
    except TypeError:
      params_alpha_ss = params_alpha_ss_raw
    else:
      params_alpha_ss_seq = np.asarray(params_alpha_ss_seq, dtype=np.float64)
      params_alpha_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_ss_seq))
  params_cab_raw = params.cab
  if isinstance(params_cab_raw, (str, bytes, dict)):
    params_cab = params_cab_raw
  else:
    try:
      params_cab_seq = list(params_cab_raw)
    except TypeError:
      params_cab = params_cab_raw
    else:
      params_cab_seq = np.asarray(params_cab_seq, dtype=np.float64)
      params_cab = np.concatenate((np.array([np.nan], dtype=np.float64), params_cab_seq))
  params_css_raw = params.css
  if isinstance(params_css_raw, (str, bytes, dict)):
    params_css = params_css_raw
  else:
    try:
      params_css_seq = list(params_css_raw)
    except TypeError:
      params_css = params_css_raw
    else:
      params_css_seq = np.asarray(params_css_seq, dtype=np.float64)
      params_css = np.concatenate((np.array([np.nan], dtype=np.float64), params_css_seq))
  params_dab_raw = params.dab
  if isinstance(params_dab_raw, (str, bytes, dict)):
    params_dab = params_dab_raw
  else:
    try:
      params_dab_seq = list(params_dab_raw)
    except TypeError:
      params_dab = params_dab_raw
    else:
      params_dab_seq = np.asarray(params_dab_seq, dtype=np.float64)
      params_dab = np.concatenate((np.array([np.nan], dtype=np.float64), params_dab_seq))
  params_dss_raw = params.dss
  if isinstance(params_dss_raw, (str, bytes, dict)):
    params_dss = params_dss_raw
  else:
    try:
      params_dss_seq = list(params_dss_raw)
    except TypeError:
      params_dss = params_dss_raw
    else:
      params_dss_seq = np.asarray(params_dss_seq, dtype=np.float64)
      params_dss = np.concatenate((np.array([np.nan], dtype=np.float64), params_dss_seq))
  params_gamma_ab_raw = params.gamma_ab
  if isinstance(params_gamma_ab_raw, (str, bytes, dict)):
    params_gamma_ab = params_gamma_ab_raw
  else:
    try:
      params_gamma_ab_seq = list(params_gamma_ab_raw)
    except TypeError:
      params_gamma_ab = params_gamma_ab_raw
    else:
      params_gamma_ab_seq = np.asarray(params_gamma_ab_seq, dtype=np.float64)
      params_gamma_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_ab_seq))
  params_gamma_ss_raw = params.gamma_ss
  if isinstance(params_gamma_ss_raw, (str, bytes, dict)):
    params_gamma_ss = params_gamma_ss_raw
  else:
    try:
      params_gamma_ss_seq = list(params_gamma_ss_raw)
    except TypeError:
      params_gamma_ss = params_gamma_ss_raw
    else:
      params_gamma_ss_seq = np.asarray(params_gamma_ss_seq, dtype=np.float64)
      params_gamma_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_ss_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  gvt4_gamm = lambda alpha, x, z: 1 + alpha * (x ** 2 + z)

  b97_g = lambda gamma, cc, x: jnp.sum(jnp.array([cc[i] * (gamma * x ** 2 / (1 + gamma * x ** 2)) ** (i - 1) for i in range(1, 5 + 1)]), axis=0)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  gtv4 = lambda alpha, dd, x, z: dd[1] / gvt4_gamm(alpha, x, z) + (dd[2] * x ** 2 + dd[3] * z) / gvt4_gamm(alpha, x, z) ** 2 + (dd[4] * x ** 4 + dd[5] * x ** 2 * z + dd[6] * z ** 2) / gvt4_gamm(alpha, x, z) ** 3

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  vsxc_comp = lambda rs, z, spin, xs, ts: +lda_stoll_par(f, params, f_pw, rs, z, 1) * gtv4(params_alpha_ss, params_dss, xs, 2 * (ts - K_FACTOR_C)) * f.Fermi_D(xs, ts)

  vsxc_fperp = lambda rs, z, xs0, xs1, ts0, ts1: +lda_stoll_perp(f, params, f_pw, rs, z) * gtv4(params_alpha_ab, params_dab, jnp.sqrt(xs0 ** 2 + xs1 ** 2), 2 * (ts0 + ts1 - 2 * K_FACTOR_C))

  m05_comp = lambda rs, z, spin, xs, t: +lda_stoll_par(f, params, f_pw, rs, z, 1) * b97_g(params_gamma_ss, params_css, xs) * f.Fermi_D_corrected(xs, t)

  m05_fperp = lambda rs, z, xs0, xs1, t0=None, t1=None: +lda_stoll_perp(f, params, f_pw, rs, z) * b97_g(params_gamma_ab, params_cab, jnp.sqrt(xs0 ** 2 + xs1 ** 2))

  vsxc_fpar = lambda rs, z, xs0, xs1, ts0, ts1: +vsxc_comp(rs, z, 1, xs0, ts0) + vsxc_comp(rs, -z, -1, xs1, ts1)

  m05_fpar = lambda rs, z, xs0, xs1, t0, t1: +m05_comp(rs, z, 1, xs0, t0) + m05_comp(rs, -z, -1, xs1, t1)

  vsxc_f = lambda rs, z, xs0, xs1, ts0, ts1: +vsxc_fpar(rs, z, xs0, xs1, ts0, ts1) + vsxc_fperp(rs, z, xs0, xs1, ts0, ts1)

  m05_f = lambda rs, z, xs0, xs1, t0, t1: +m05_fpar(rs, z, xs0, xs1, t0, t1) + m05_fperp(rs, z, xs0, xs1, t0, t1)

  m06l_f = lambda rs, z, xs0, xs1, ts0, ts1: +m05_f(rs, z, xs0, xs1, ts0, ts1) + vsxc_f(rs, z, xs0, xs1, ts0, ts1)

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: m06l_f(rs, z, xs0, xs1, ts0, ts1)

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
  params_alpha_ab_raw = params.alpha_ab
  if isinstance(params_alpha_ab_raw, (str, bytes, dict)):
    params_alpha_ab = params_alpha_ab_raw
  else:
    try:
      params_alpha_ab_seq = list(params_alpha_ab_raw)
    except TypeError:
      params_alpha_ab = params_alpha_ab_raw
    else:
      params_alpha_ab_seq = np.asarray(params_alpha_ab_seq, dtype=np.float64)
      params_alpha_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_ab_seq))
  params_alpha_ss_raw = params.alpha_ss
  if isinstance(params_alpha_ss_raw, (str, bytes, dict)):
    params_alpha_ss = params_alpha_ss_raw
  else:
    try:
      params_alpha_ss_seq = list(params_alpha_ss_raw)
    except TypeError:
      params_alpha_ss = params_alpha_ss_raw
    else:
      params_alpha_ss_seq = np.asarray(params_alpha_ss_seq, dtype=np.float64)
      params_alpha_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_ss_seq))
  params_cab_raw = params.cab
  if isinstance(params_cab_raw, (str, bytes, dict)):
    params_cab = params_cab_raw
  else:
    try:
      params_cab_seq = list(params_cab_raw)
    except TypeError:
      params_cab = params_cab_raw
    else:
      params_cab_seq = np.asarray(params_cab_seq, dtype=np.float64)
      params_cab = np.concatenate((np.array([np.nan], dtype=np.float64), params_cab_seq))
  params_css_raw = params.css
  if isinstance(params_css_raw, (str, bytes, dict)):
    params_css = params_css_raw
  else:
    try:
      params_css_seq = list(params_css_raw)
    except TypeError:
      params_css = params_css_raw
    else:
      params_css_seq = np.asarray(params_css_seq, dtype=np.float64)
      params_css = np.concatenate((np.array([np.nan], dtype=np.float64), params_css_seq))
  params_dab_raw = params.dab
  if isinstance(params_dab_raw, (str, bytes, dict)):
    params_dab = params_dab_raw
  else:
    try:
      params_dab_seq = list(params_dab_raw)
    except TypeError:
      params_dab = params_dab_raw
    else:
      params_dab_seq = np.asarray(params_dab_seq, dtype=np.float64)
      params_dab = np.concatenate((np.array([np.nan], dtype=np.float64), params_dab_seq))
  params_dss_raw = params.dss
  if isinstance(params_dss_raw, (str, bytes, dict)):
    params_dss = params_dss_raw
  else:
    try:
      params_dss_seq = list(params_dss_raw)
    except TypeError:
      params_dss = params_dss_raw
    else:
      params_dss_seq = np.asarray(params_dss_seq, dtype=np.float64)
      params_dss = np.concatenate((np.array([np.nan], dtype=np.float64), params_dss_seq))
  params_gamma_ab_raw = params.gamma_ab
  if isinstance(params_gamma_ab_raw, (str, bytes, dict)):
    params_gamma_ab = params_gamma_ab_raw
  else:
    try:
      params_gamma_ab_seq = list(params_gamma_ab_raw)
    except TypeError:
      params_gamma_ab = params_gamma_ab_raw
    else:
      params_gamma_ab_seq = np.asarray(params_gamma_ab_seq, dtype=np.float64)
      params_gamma_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_ab_seq))
  params_gamma_ss_raw = params.gamma_ss
  if isinstance(params_gamma_ss_raw, (str, bytes, dict)):
    params_gamma_ss = params_gamma_ss_raw
  else:
    try:
      params_gamma_ss_seq = list(params_gamma_ss_raw)
    except TypeError:
      params_gamma_ss = params_gamma_ss_raw
    else:
      params_gamma_ss_seq = np.asarray(params_gamma_ss_seq, dtype=np.float64)
      params_gamma_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_ss_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  gvt4_gamm = lambda alpha, x, z: 1 + alpha * (x ** 2 + z)

  b97_g = lambda gamma, cc, x: jnp.sum(jnp.array([cc[i] * (gamma * x ** 2 / (1 + gamma * x ** 2)) ** (i - 1) for i in range(1, 5 + 1)]), axis=0)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  gtv4 = lambda alpha, dd, x, z: dd[1] / gvt4_gamm(alpha, x, z) + (dd[2] * x ** 2 + dd[3] * z) / gvt4_gamm(alpha, x, z) ** 2 + (dd[4] * x ** 4 + dd[5] * x ** 2 * z + dd[6] * z ** 2) / gvt4_gamm(alpha, x, z) ** 3

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  vsxc_comp = lambda rs, z, spin, xs, ts: +lda_stoll_par(f, params, f_pw, rs, z, 1) * gtv4(params_alpha_ss, params_dss, xs, 2 * (ts - K_FACTOR_C)) * f.Fermi_D(xs, ts)

  vsxc_fperp = lambda rs, z, xs0, xs1, ts0, ts1: +lda_stoll_perp(f, params, f_pw, rs, z) * gtv4(params_alpha_ab, params_dab, jnp.sqrt(xs0 ** 2 + xs1 ** 2), 2 * (ts0 + ts1 - 2 * K_FACTOR_C))

  m05_comp = lambda rs, z, spin, xs, t: +lda_stoll_par(f, params, f_pw, rs, z, 1) * b97_g(params_gamma_ss, params_css, xs) * f.Fermi_D_corrected(xs, t)

  m05_fperp = lambda rs, z, xs0, xs1, t0=None, t1=None: +lda_stoll_perp(f, params, f_pw, rs, z) * b97_g(params_gamma_ab, params_cab, jnp.sqrt(xs0 ** 2 + xs1 ** 2))

  vsxc_fpar = lambda rs, z, xs0, xs1, ts0, ts1: +vsxc_comp(rs, z, 1, xs0, ts0) + vsxc_comp(rs, -z, -1, xs1, ts1)

  m05_fpar = lambda rs, z, xs0, xs1, t0, t1: +m05_comp(rs, z, 1, xs0, t0) + m05_comp(rs, -z, -1, xs1, t1)

  vsxc_f = lambda rs, z, xs0, xs1, ts0, ts1: +vsxc_fpar(rs, z, xs0, xs1, ts0, ts1) + vsxc_fperp(rs, z, xs0, xs1, ts0, ts1)

  m05_f = lambda rs, z, xs0, xs1, t0, t1: +m05_fpar(rs, z, xs0, xs1, t0, t1) + m05_fperp(rs, z, xs0, xs1, t0, t1)

  m06l_f = lambda rs, z, xs0, xs1, ts0, ts1: +m05_f(rs, z, xs0, xs1, ts0, ts1) + vsxc_f(rs, z, xs0, xs1, ts0, ts1)

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: m06l_f(rs, z, xs0, xs1, ts0, ts1)

  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t6 = 0.1e1 + t5
  t7 = t6 <= f.p.zeta_threshold
  t8 = r0 <= f.p.dens_threshold or t7
  t9 = f.my_piecewise3(t7, f.p.zeta_threshold, t6)
  t10 = 3 ** (0.1e1 / 0.3e1)
  t12 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t13 = t10 * t12
  t14 = 4 ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t16 = t13 * t15
  t17 = t3 ** (0.1e1 / 0.3e1)
  t18 = 0.1e1 / t17
  t19 = 2 ** (0.1e1 / 0.3e1)
  t20 = t18 * t19
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = 0.1e1 / t21
  t23 = t6 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t7, t22, 0.1e1 / t23)
  t27 = t16 * t20 * t25
  t29 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t27
  t30 = jnp.sqrt(t27)
  t33 = t27 ** 0.15e1
  t35 = t10 ** 2
  t36 = t12 ** 2
  t37 = t35 * t36
  t38 = t37 * t14
  t39 = t17 ** 2
  t40 = 0.1e1 / t39
  t41 = t19 ** 2
  t42 = t40 * t41
  t43 = t25 ** 2
  t45 = t38 * t42 * t43
  t47 = 0.23615562999000000000000000000000000000000000000000e0 * t30 + 0.55770497660000000000000000000000000000000000000000e-1 * t27 + 0.12733196185000000000000000000000000000000000000000e-1 * t33 + 0.76629248290000000000000000000000000000000000000000e-2 * t45
  t49 = 0.1e1 + 0.1e1 / t47
  t50 = jnp.log(t49)
  t51 = t29 * t50
  t53 = t21 * f.p.zeta_threshold
  t55 = f.my_piecewise3(0.2e1 <= f.p.zeta_threshold, t53, 0.2e1 * t19)
  t57 = f.my_piecewise3(0.0e0 <= f.p.zeta_threshold, t53, 0)
  t61 = 0.1e1 / (0.2e1 * t19 - 0.2e1)
  t62 = (t55 + t57 - 0.2e1) * t61
  t64 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t27
  t69 = 0.21948324211500000000000000000000000000000000000000e0 * t30 + 0.48172707847500000000000000000000000000000000000000e-1 * t27 + 0.13082189292500000000000000000000000000000000000000e-1 * t33 + 0.48592432297500000000000000000000000000000000000000e-2 * t45
  t71 = 0.1e1 + 0.1e1 / t69
  t72 = jnp.log(t71)
  t75 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t27
  t80 = 0.17489762330000000000000000000000000000000000000000e0 * t30 + 0.30591463695000000000000000000000000000000000000000e-1 * t27 + 0.37162156485000000000000000000000000000000000000000e-2 * t33 + 0.41939460495000000000000000000000000000000000000000e-2 * t45
  t82 = 0.1e1 + 0.1e1 / t80
  t83 = jnp.log(t82)
  t84 = t75 * t83
  t90 = -t51 + t62 * (-t64 * t72 + t51 - 0.58482236226346462072622386637590534819724553404281e0 * t84) + 0.58482236226346462072622386637590534819724553404281e0 * t62 * t84
  t93 = f.my_piecewise3(t8, 0, t9 * t90 / 0.2e1)
  t94 = params.css[0]
  t95 = params.css[1]
  t96 = t95 * params.gamma_ss
  t97 = r0 ** 2
  t98 = r0 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t101 = 0.1e1 / t99 / t97
  t102 = s0 * t101
  t105 = params.gamma_ss * s0 * t101 + 0.1e1
  t106 = 0.1e1 / t105
  t109 = params.css[2]
  t110 = params.gamma_ss ** 2
  t111 = t109 * t110
  t112 = s0 ** 2
  t113 = t97 ** 2
  t114 = t113 * r0
  t116 = 0.1e1 / t98 / t114
  t118 = t105 ** 2
  t119 = 0.1e1 / t118
  t122 = params.css[3]
  t123 = t110 * params.gamma_ss
  t124 = t122 * t123
  t125 = t112 * s0
  t126 = t113 ** 2
  t127 = 0.1e1 / t126
  t130 = 0.1e1 / t118 / t105
  t133 = params.css[4]
  t134 = t110 ** 2
  t135 = t133 * t134
  t136 = t112 ** 2
  t139 = 0.1e1 / t99 / t126 / t97
  t141 = t118 ** 2
  t142 = 0.1e1 / t141
  t145 = t111 * t112 * t116 * t119 + t124 * t125 * t127 * t130 + t135 * t136 * t139 * t142 + t96 * t102 * t106 + t94
  t146 = t93 * t145
  t147 = 0.1e1 / r0
  t148 = s0 * t147
  t149 = 0.1e1 / tau0
  t152 = 0.1e1 - t148 * t149 / 0.8e1
  t153 = tau0 ** 2
  t154 = t97 * r0
  t156 = 0.1e1 / t98 / t154
  t158 = params.Fermi_D_cnst ** 2
  t159 = 0.1e1 / t158
  t162 = jnp.exp(-0.4e1 * t153 * t156 * t159)
  t163 = 0.1e1 - t162
  t164 = t152 * t163
  t165 = t146 * t164
  t167 = 0.1e1 - t5
  t168 = t167 <= f.p.zeta_threshold
  t169 = r1 <= f.p.dens_threshold or t168
  t170 = f.my_piecewise3(t168, f.p.zeta_threshold, t167)
  t171 = t167 ** (0.1e1 / 0.3e1)
  t173 = f.my_piecewise3(t168, t22, 0.1e1 / t171)
  t175 = t16 * t20 * t173
  t177 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t175
  t178 = jnp.sqrt(t175)
  t181 = t175 ** 0.15e1
  t183 = t173 ** 2
  t185 = t38 * t42 * t183
  t187 = 0.23615562999000000000000000000000000000000000000000e0 * t178 + 0.55770497660000000000000000000000000000000000000000e-1 * t175 + 0.12733196185000000000000000000000000000000000000000e-1 * t181 + 0.76629248290000000000000000000000000000000000000000e-2 * t185
  t189 = 0.1e1 + 0.1e1 / t187
  t190 = jnp.log(t189)
  t191 = t177 * t190
  t193 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t175
  t198 = 0.21948324211500000000000000000000000000000000000000e0 * t178 + 0.48172707847500000000000000000000000000000000000000e-1 * t175 + 0.13082189292500000000000000000000000000000000000000e-1 * t181 + 0.48592432297500000000000000000000000000000000000000e-2 * t185
  t200 = 0.1e1 + 0.1e1 / t198
  t201 = jnp.log(t200)
  t204 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t175
  t209 = 0.17489762330000000000000000000000000000000000000000e0 * t178 + 0.30591463695000000000000000000000000000000000000000e-1 * t175 + 0.37162156485000000000000000000000000000000000000000e-2 * t181 + 0.41939460495000000000000000000000000000000000000000e-2 * t185
  t211 = 0.1e1 + 0.1e1 / t209
  t212 = jnp.log(t211)
  t213 = t204 * t212
  t219 = -t191 + t62 * (-t193 * t201 + t191 - 0.58482236226346462072622386637590534819724553404281e0 * t213) + 0.58482236226346462072622386637590534819724553404281e0 * t62 * t213
  t222 = f.my_piecewise3(t169, 0, t170 * t219 / 0.2e1)
  t223 = r1 ** 2
  t224 = r1 ** (0.1e1 / 0.3e1)
  t225 = t224 ** 2
  t227 = 0.1e1 / t225 / t223
  t228 = s2 * t227
  t231 = params.gamma_ss * s2 * t227 + 0.1e1
  t232 = 0.1e1 / t231
  t235 = s2 ** 2
  t236 = t223 ** 2
  t237 = t236 * r1
  t239 = 0.1e1 / t224 / t237
  t241 = t231 ** 2
  t242 = 0.1e1 / t241
  t245 = t235 * s2
  t246 = t236 ** 2
  t247 = 0.1e1 / t246
  t250 = 0.1e1 / t241 / t231
  t253 = t235 ** 2
  t256 = 0.1e1 / t225 / t246 / t223
  t258 = t241 ** 2
  t259 = 0.1e1 / t258
  t262 = t111 * t235 * t239 * t242 + t124 * t245 * t247 * t250 + t135 * t253 * t256 * t259 + t96 * t228 * t232 + t94
  t263 = t222 * t262
  t264 = 0.1e1 / r1
  t265 = s2 * t264
  t266 = 0.1e1 / tau1
  t269 = 0.1e1 - t265 * t266 / 0.8e1
  t270 = tau1 ** 2
  t271 = t223 * r1
  t273 = 0.1e1 / t224 / t271
  t277 = jnp.exp(-0.4e1 * t270 * t273 * t159)
  t278 = 0.1e1 - t277
  t279 = t269 * t278
  t280 = t263 * t279
  t282 = t13 * t15 * t18
  t284 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t282
  t285 = jnp.sqrt(t282)
  t288 = t282 ** 0.15e1
  t291 = t37 * t14 * t40
  t293 = 0.23615562999000000000000000000000000000000000000000e0 * t285 + 0.55770497660000000000000000000000000000000000000000e-1 * t282 + 0.12733196185000000000000000000000000000000000000000e-1 * t288 + 0.76629248290000000000000000000000000000000000000000e-2 * t291
  t295 = 0.1e1 + 0.1e1 / t293
  t296 = jnp.log(t295)
  t297 = t284 * t296
  t298 = t2 ** 2
  t299 = t298 ** 2
  t300 = t3 ** 2
  t301 = t300 ** 2
  t302 = 0.1e1 / t301
  t303 = t299 * t302
  t304 = t23 * t6
  t305 = f.my_piecewise3(t7, t53, t304)
  t306 = t171 * t167
  t307 = f.my_piecewise3(t168, t53, t306)
  t309 = (t305 + t307 - 0.2e1) * t61
  t311 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t282
  t316 = 0.21948324211500000000000000000000000000000000000000e0 * t285 + 0.48172707847500000000000000000000000000000000000000e-1 * t282 + 0.13082189292500000000000000000000000000000000000000e-1 * t288 + 0.48592432297500000000000000000000000000000000000000e-2 * t291
  t318 = 0.1e1 + 0.1e1 / t316
  t319 = jnp.log(t318)
  t322 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t282
  t327 = 0.17489762330000000000000000000000000000000000000000e0 * t285 + 0.30591463695000000000000000000000000000000000000000e-1 * t282 + 0.37162156485000000000000000000000000000000000000000e-2 * t288 + 0.41939460495000000000000000000000000000000000000000e-2 * t291
  t329 = 0.1e1 + 0.1e1 / t327
  t330 = jnp.log(t329)
  t331 = t322 * t330
  t333 = -t311 * t319 + t297 - 0.58482236226346462072622386637590534819724553404281e0 * t331
  t334 = t309 * t333
  t338 = -t297 + t303 * t334 + 0.58482236226346462072622386637590534819724553404281e0 * t309 * t331 - t93 - t222
  t340 = params.cab[1]
  t341 = t340 * params.gamma_ab
  t342 = t102 + t228
  t344 = params.gamma_ab * t342 + 0.1e1
  t345 = 0.1e1 / t344
  t348 = params.cab[2]
  t349 = params.gamma_ab ** 2
  t350 = t348 * t349
  t351 = t342 ** 2
  t352 = t344 ** 2
  t353 = 0.1e1 / t352
  t356 = params.cab[3]
  t357 = t349 * params.gamma_ab
  t358 = t356 * t357
  t359 = t351 * t342
  t361 = 0.1e1 / t352 / t344
  t364 = params.cab[4]
  t365 = t349 ** 2
  t366 = t364 * t365
  t367 = t351 ** 2
  t368 = t352 ** 2
  t369 = 0.1e1 / t368
  t372 = t341 * t342 * t345 + t350 * t351 * t353 + t358 * t359 * t361 + t366 * t367 * t369 + params.cab[0]
  t373 = t338 * t372
  t374 = params.dss[0]
  t376 = 0.1e1 / t99 / r0
  t378 = 0.2e1 * tau0 * t376
  t379 = 6 ** (0.1e1 / 0.3e1)
  t380 = t379 ** 2
  t381 = jnp.pi ** 2
  t382 = t381 ** (0.1e1 / 0.3e1)
  t383 = t382 ** 2
  t384 = t380 * t383
  t385 = 0.3e1 / 0.5e1 * t384
  t388 = 0.1e1 + params.alpha_ss * (t102 + t378 - t385)
  t391 = params.dss[1]
  t392 = t391 * s0
  t394 = params.dss[2]
  t395 = t378 - t385
  t397 = t392 * t101 + t394 * t395
  t398 = t388 ** 2
  t399 = 0.1e1 / t398
  t401 = params.dss[3]
  t402 = t401 * t112
  t404 = params.dss[4]
  t405 = t404 * s0
  t408 = params.dss[5]
  t409 = t395 ** 2
  t411 = t405 * t101 * t395 + t402 * t116 + t408 * t409
  t413 = 0.1e1 / t398 / t388
  t415 = t374 / t388 + t397 * t399 + t411 * t413
  t416 = t93 * t415
  t417 = t416 * t152
  t419 = 0.1e1 / t225 / r1
  t421 = 0.2e1 * tau1 * t419
  t424 = 0.1e1 + params.alpha_ss * (t228 + t421 - t385)
  t427 = t391 * s2
  t429 = t421 - t385
  t431 = t427 * t227 + t394 * t429
  t432 = t424 ** 2
  t433 = 0.1e1 / t432
  t435 = t401 * t235
  t437 = t404 * s2
  t440 = t429 ** 2
  t442 = t437 * t227 * t429 + t435 * t239 + t408 * t440
  t444 = 0.1e1 / t432 / t424
  t446 = t374 / t424 + t431 * t433 + t442 * t444
  t447 = t222 * t446
  t448 = t447 * t269
  t449 = params.dab[0]
  t450 = 0.6e1 / 0.5e1 * t384
  t453 = 0.1e1 + params.alpha_ab * (t102 + t228 + t378 + t421 - t450)
  t456 = params.dab[1]
  t458 = params.dab[2]
  t459 = t378 + t421 - t450
  t461 = t456 * t342 + t458 * t459
  t462 = t453 ** 2
  t463 = 0.1e1 / t462
  t465 = params.dab[3]
  t467 = params.dab[4]
  t468 = t467 * t342
  t470 = params.dab[5]
  t471 = t459 ** 2
  t473 = t465 * t351 + t468 * t459 + t470 * t471
  t475 = 0.1e1 / t462 / t453
  t477 = t449 / t453 + t461 * t463 + t473 * t475
  t478 = t338 * t477
  t480 = t2 / t300
  t481 = t4 - t480
  t482 = f.my_piecewise3(t7, 0, t481)
  t485 = 0.1e1 / t17 / t3
  t486 = t485 * t19
  t488 = t16 * t486 * t25
  t489 = 0.11073470983333333333333333333333333333333333333333e-2 * t488
  t490 = 0.1e1 / t304
  t493 = f.my_piecewise3(t7, 0, -t490 * t481 / 0.3e1)
  t495 = t16 * t20 * t493
  t498 = (-t489 + 0.33220412950000000000000000000000000000000000000000e-2 * t495) * t50
  t499 = t47 ** 2
  t501 = t29 / t499
  t502 = 0.1e1 / t30
  t503 = t488 / 0.3e1
  t504 = -t503 + t495
  t505 = t502 * t504
  t507 = 0.18590165886666666666666666666666666666666666666667e-1 * t488
  t509 = t27 ** 0.5e0
  t510 = t509 * t504
  t513 = 0.1e1 / t39 / t3
  t514 = t513 * t41
  t516 = t38 * t514 * t43
  t517 = 0.51086165526666666666666666666666666666666666666667e-2 * t516
  t520 = t38 * t42 * t25 * t493
  t523 = 0.1e1 / t49
  t525 = t501 * (0.11807781499500000000000000000000000000000000000000e0 * t505 - t507 + 0.55770497660000000000000000000000000000000000000000e-1 * t495 + 0.19099794277500000000000000000000000000000000000000e-1 * t510 - t517 + 0.15325849658000000000000000000000000000000000000000e-1 * t520) * t523
  t526 = 0.53237641966666666666666666666666666666666666666667e-3 * t488
  t530 = t69 ** 2
  t532 = t64 / t530
  t534 = 0.16057569282500000000000000000000000000000000000000e-1 * t488
  t537 = 0.32394954865000000000000000000000000000000000000000e-2 * t516
  t540 = 0.1e1 / t71
  t543 = 0.31311127083333333333333333333333333333333333333333e-3 * t488
  t546 = (-t543 + 0.93933381250000000000000000000000000000000000000000e-3 * t495) * t83
  t548 = t80 ** 2
  t549 = 0.1e1 / t548
  t550 = t75 * t549
  t552 = 0.10197154565000000000000000000000000000000000000000e-1 * t488
  t555 = 0.27959640330000000000000000000000000000000000000000e-2 * t516
  t557 = 0.87448811650000000000000000000000000000000000000000e-1 * t505 - t552 + 0.30591463695000000000000000000000000000000000000000e-1 * t495 + 0.55743234727500000000000000000000000000000000000000e-2 * t510 - t555 + 0.83878920990000000000000000000000000000000000000000e-2 * t520
  t558 = 0.1e1 / t82
  t566 = t62 * t75
  t575 = f.my_piecewise3(t8, 0, t482 * t90 / 0.2e1 + t9 * (-t498 + t525 + t62 * (-(-t526 + 0.15971292590000000000000000000000000000000000000000e-2 * t495) * t72 + t532 * (0.10974162105750000000000000000000000000000000000000e0 * t505 - t534 + 0.48172707847500000000000000000000000000000000000000e-1 * t495 + 0.19623283938750000000000000000000000000000000000000e-1 * t510 - t537 + 0.97184864595000000000000000000000000000000000000000e-2 * t520) * t540 + t498 - t525 - 0.58482236226346462072622386637590534819724553404281e0 * t546 + 0.58482236226346462072622386637590534819724553404281e0 * t550 * t557 * t558) + 0.58482236226346462072622386637590534819724553404281e0 * t62 * t546 - 0.58482236226346462072622386637590534819724553404281e0 * t566 * t549 * t557 * t558) / 0.2e1)
  t579 = 0.1e1 / t99 / t154
  t580 = s0 * t579
  t584 = t95 * t110
  t585 = t113 * t97
  t587 = 0.1e1 / t98 / t585
  t589 = t112 * t587 * t119
  t594 = t109 * t123
  t598 = t125 / t126 / r0 * t130
  t603 = t122 * t134
  t608 = t136 / t99 / t126 / t154 * t142
  t614 = t133 * t134 * params.gamma_ss
  t621 = 0.1e1 / t141 / t105
  t628 = t146 * s0
  t629 = 0.1e1 / t97
  t634 = t146 * t152
  t636 = 0.1e1 / t98 / t113
  t638 = t159 * t162
  t642 = -t481
  t643 = f.my_piecewise3(t168, 0, t642)
  t646 = t16 * t486 * t173
  t647 = 0.11073470983333333333333333333333333333333333333333e-2 * t646
  t648 = 0.1e1 / t306
  t651 = f.my_piecewise3(t168, 0, -t648 * t642 / 0.3e1)
  t653 = t16 * t20 * t651
  t656 = (-t647 + 0.33220412950000000000000000000000000000000000000000e-2 * t653) * t190
  t657 = t187 ** 2
  t659 = t177 / t657
  t660 = 0.1e1 / t178
  t661 = t646 / 0.3e1
  t662 = -t661 + t653
  t663 = t660 * t662
  t665 = 0.18590165886666666666666666666666666666666666666667e-1 * t646
  t667 = t175 ** 0.5e0
  t668 = t667 * t662
  t671 = t38 * t514 * t183
  t672 = 0.51086165526666666666666666666666666666666666666667e-2 * t671
  t675 = t38 * t42 * t173 * t651
  t678 = 0.1e1 / t189
  t680 = t659 * (0.11807781499500000000000000000000000000000000000000e0 * t663 - t665 + 0.55770497660000000000000000000000000000000000000000e-1 * t653 + 0.19099794277500000000000000000000000000000000000000e-1 * t668 - t672 + 0.15325849658000000000000000000000000000000000000000e-1 * t675) * t678
  t681 = 0.53237641966666666666666666666666666666666666666667e-3 * t646
  t685 = t198 ** 2
  t687 = t193 / t685
  t689 = 0.16057569282500000000000000000000000000000000000000e-1 * t646
  t692 = 0.32394954865000000000000000000000000000000000000000e-2 * t671
  t695 = 0.1e1 / t200
  t698 = 0.31311127083333333333333333333333333333333333333333e-3 * t646
  t701 = (-t698 + 0.93933381250000000000000000000000000000000000000000e-3 * t653) * t212
  t703 = t209 ** 2
  t704 = 0.1e1 / t703
  t705 = t204 * t704
  t707 = 0.10197154565000000000000000000000000000000000000000e-1 * t646
  t710 = 0.27959640330000000000000000000000000000000000000000e-2 * t671
  t712 = 0.87448811650000000000000000000000000000000000000000e-1 * t663 - t707 + 0.30591463695000000000000000000000000000000000000000e-1 * t653 + 0.55743234727500000000000000000000000000000000000000e-2 * t668 - t710 + 0.83878920990000000000000000000000000000000000000000e-2 * t675
  t713 = 0.1e1 / t211
  t721 = t62 * t204
  t730 = f.my_piecewise3(t169, 0, t643 * t219 / 0.2e1 + t170 * (-t656 + t680 + t62 * (-(-t681 + 0.15971292590000000000000000000000000000000000000000e-2 * t653) * t201 + t687 * (0.10974162105750000000000000000000000000000000000000e0 * t663 - t689 + 0.48172707847500000000000000000000000000000000000000e-1 * t653 + 0.19623283938750000000000000000000000000000000000000e-1 * t668 - t692 + 0.97184864595000000000000000000000000000000000000000e-2 * t675) * t695 + t656 - t680 - 0.58482236226346462072622386637590534819724553404281e0 * t701 + 0.58482236226346462072622386637590534819724553404281e0 * t705 * t712 * t713) + 0.58482236226346462072622386637590534819724553404281e0 * t62 * t701 - 0.58482236226346462072622386637590534819724553404281e0 * t721 * t704 * t712 * t713) / 0.2e1)
  t733 = t15 * t485
  t736 = 0.11073470983333333333333333333333333333333333333333e-2 * t13 * t733 * t296
  t737 = t293 ** 2
  t742 = t12 * t15
  t743 = t742 * t485
  t744 = 0.1e1 / t285 * t10 * t743
  t746 = t13 * t733
  t748 = t282 ** 0.5e0
  t750 = t748 * t10 * t743
  t753 = t37 * t14 * t513
  t758 = t284 / t737 * (-0.39359271665000000000000000000000000000000000000000e-1 * t744 - 0.18590165886666666666666666666666666666666666666667e-1 * t746 - 0.63665980925000000000000000000000000000000000000000e-2 * t750 - 0.51086165526666666666666666666666666666666666666667e-2 * t753) / t295
  t762 = 0.4e1 * t298 * t2 * t302 * t334
  t767 = 0.4e1 * t299 / t301 / t3 * t334
  t770 = f.my_piecewise3(t7, 0, 0.4e1 / 0.3e1 * t23 * t481)
  t773 = f.my_piecewise3(t168, 0, 0.4e1 / 0.3e1 * t171 * t642)
  t775 = (t770 + t773) * t61
  t781 = t316 ** 2
  t795 = t327 ** 2
  t796 = 0.1e1 / t795
  t802 = -0.29149603883333333333333333333333333333333333333333e-1 * t744 - 0.10197154565000000000000000000000000000000000000000e-1 * t746 - 0.18581078242500000000000000000000000000000000000000e-2 * t750 - 0.27959640330000000000000000000000000000000000000000e-2 * t753
  t803 = 0.1e1 / t329
  t809 = t303 * t309 * (0.53237641966666666666666666666666666666666666666667e-3 * t13 * t733 * t319 + t311 / t781 * (-0.36580540352500000000000000000000000000000000000000e-1 * t744 - 0.16057569282500000000000000000000000000000000000000e-1 * t746 - 0.65410946462500000000000000000000000000000000000000e-2 * t750 - 0.32394954865000000000000000000000000000000000000000e-2 * t753) / t318 - t736 - t758 + 0.18311447306006545054854346104378990962041954983034e-3 * t13 * t733 * t330 + 0.58482236226346462072622386637590534819724553404281e0 * t322 * t796 * t802 * t803)
  t816 = 0.18311447306006545054854346104378990962041954983034e-3 * t309 * t10 * t742 * t485 * t330
  t821 = 0.58482236226346462072622386637590534819724553404281e0 * t309 * t322 * t796 * t802 * t803
  t822 = t736 + t758 + t762 - t767 + t303 * t775 * t333 + t809 + 0.58482236226346462072622386637590534819724553404281e0 * t775 * t331 - t816 - t821 - t575 - t730
  t827 = t340 * t349
  t828 = t827 * t342
  t830 = t353 * s0 * t579
  t833 = t350 * t342
  t836 = t348 * t357
  t837 = t836 * t351
  t839 = t361 * s0 * t579
  t842 = t358 * t351
  t845 = t356 * t365
  t846 = t845 * t359
  t848 = t369 * s0 * t579
  t851 = t366 * t359
  t855 = t364 * t365 * params.gamma_ab
  t856 = t855 * t367
  t858 = 0.1e1 / t368 / t344
  t867 = t374 * t399
  t869 = tau0 * t101
  t871 = -0.8e1 / 0.3e1 * t580 - 0.10e2 / 0.3e1 * t869
  t872 = params.alpha_ss * t871
  t881 = t397 * t413
  t892 = t408 * t395
  t897 = t398 ** 2
  t899 = t411 / t897
  t912 = t449 * t463
  t913 = params.alpha_ab * t871
  t923 = t461 * t475
  t926 = t465 * t342
  t935 = t470 * t459
  t940 = t462 ** 2
  t942 = t473 / t940
  t947 = t575 * t145 * t164 + t93 * (-0.8e1 / 0.3e1 * t96 * t580 * t106 + 0.8e1 / 0.3e1 * t584 * t589 - 0.16e2 / 0.3e1 * t111 * t589 + 0.16e2 / 0.3e1 * t594 * t598 - 0.8e1 * t124 * t598 + 0.8e1 * t603 * t608 - 0.32e2 / 0.3e1 * t135 * t608 + 0.32e2 / 0.3e1 * t614 * t136 * s0 / t98 / t126 / t585 * t621) * t164 + t628 * t629 * t149 * t163 / 0.8e1 - 0.40e2 / 0.3e1 * t634 * t153 * t636 * t638 + t730 * t262 * t279 + t822 * t372 + t338 * (-0.8e1 / 0.3e1 * t341 * t580 * t345 + 0.8e1 / 0.3e1 * t828 * t830 - 0.16e2 / 0.3e1 * t833 * t830 + 0.16e2 / 0.3e1 * t837 * t839 - 0.8e1 * t842 * t839 + 0.8e1 * t846 * t848 - 0.32e2 / 0.3e1 * t851 * t848 + 0.32e2 / 0.3e1 * t856 * t858 * s0 * t579) + t575 * t415 * t152 + t93 * (-t867 * t872 + (-0.8e1 / 0.3e1 * t392 * t579 - 0.10e2 / 0.3e1 * t394 * tau0 * t101) * t399 - 0.2e1 * t881 * t872 + (-0.16e2 / 0.3e1 * t402 * t587 - 0.8e1 / 0.3e1 * t405 * t579 * t395 - 0.10e2 / 0.3e1 * t405 * t116 * tau0 - 0.20e2 / 0.3e1 * t892 * t869) * t413 - 0.3e1 * t899 * t872) * t152 + t416 * s0 * t629 * t149 / 0.8e1 + t730 * t446 * t269 + t822 * t477 + t338 * (-t912 * t913 + (-0.8e1 / 0.3e1 * t456 * s0 * t579 - 0.10e2 / 0.3e1 * t458 * tau0 * t101) * t463 - 0.2e1 * t923 * t913 + (-0.16e2 / 0.3e1 * t926 * t580 - 0.8e1 / 0.3e1 * t467 * s0 * t579 * t459 - 0.10e2 / 0.3e1 * t468 * t869 - 0.20e2 / 0.3e1 * t935 * t869) * t475 - 0.3e1 * t942 * t913)
  vrho_0_ = t3 * t947 + t165 + t280 + t373 + t417 + t448 + t478
  t949 = -t4 - t480
  t950 = f.my_piecewise3(t7, 0, t949)
  t954 = f.my_piecewise3(t7, 0, -t490 * t949 / 0.3e1)
  t956 = t16 * t20 * t954
  t959 = (-t489 + 0.33220412950000000000000000000000000000000000000000e-2 * t956) * t50
  t960 = -t503 + t956
  t961 = t502 * t960
  t964 = t509 * t960
  t968 = t38 * t42 * t25 * t954
  t972 = t501 * (0.11807781499500000000000000000000000000000000000000e0 * t961 - t507 + 0.55770497660000000000000000000000000000000000000000e-1 * t956 + 0.19099794277500000000000000000000000000000000000000e-1 * t964 - t517 + 0.15325849658000000000000000000000000000000000000000e-1 * t968) * t523
  t985 = (-t543 + 0.93933381250000000000000000000000000000000000000000e-3 * t956) * t83
  t991 = 0.87448811650000000000000000000000000000000000000000e-1 * t961 - t552 + 0.30591463695000000000000000000000000000000000000000e-1 * t956 + 0.55743234727500000000000000000000000000000000000000e-2 * t964 - t555 + 0.83878920990000000000000000000000000000000000000000e-2 * t968
  t1007 = f.my_piecewise3(t8, 0, t950 * t90 / 0.2e1 + t9 * (-t959 + t972 + t62 * (-(-t526 + 0.15971292590000000000000000000000000000000000000000e-2 * t956) * t72 + t532 * (0.10974162105750000000000000000000000000000000000000e0 * t961 - t534 + 0.48172707847500000000000000000000000000000000000000e-1 * t956 + 0.19623283938750000000000000000000000000000000000000e-1 * t964 - t537 + 0.97184864595000000000000000000000000000000000000000e-2 * t968) * t540 + t959 - t972 - 0.58482236226346462072622386637590534819724553404281e0 * t985 + 0.58482236226346462072622386637590534819724553404281e0 * t550 * t991 * t558) + 0.58482236226346462072622386637590534819724553404281e0 * t62 * t985 - 0.58482236226346462072622386637590534819724553404281e0 * t566 * t549 * t991 * t558) / 0.2e1)
  t1010 = -t949
  t1011 = f.my_piecewise3(t168, 0, t1010)
  t1015 = f.my_piecewise3(t168, 0, -t648 * t1010 / 0.3e1)
  t1017 = t16 * t20 * t1015
  t1020 = (-t647 + 0.33220412950000000000000000000000000000000000000000e-2 * t1017) * t190
  t1021 = -t661 + t1017
  t1022 = t660 * t1021
  t1025 = t667 * t1021
  t1029 = t38 * t42 * t173 * t1015
  t1033 = t659 * (0.11807781499500000000000000000000000000000000000000e0 * t1022 - t665 + 0.55770497660000000000000000000000000000000000000000e-1 * t1017 + 0.19099794277500000000000000000000000000000000000000e-1 * t1025 - t672 + 0.15325849658000000000000000000000000000000000000000e-1 * t1029) * t678
  t1046 = (-t698 + 0.93933381250000000000000000000000000000000000000000e-3 * t1017) * t212
  t1052 = 0.87448811650000000000000000000000000000000000000000e-1 * t1022 - t707 + 0.30591463695000000000000000000000000000000000000000e-1 * t1017 + 0.55743234727500000000000000000000000000000000000000e-2 * t1025 - t710 + 0.83878920990000000000000000000000000000000000000000e-2 * t1029
  t1068 = f.my_piecewise3(t169, 0, t1011 * t219 / 0.2e1 + t170 * (-t1020 + t1033 + t62 * (-(-t681 + 0.15971292590000000000000000000000000000000000000000e-2 * t1017) * t201 + t687 * (0.10974162105750000000000000000000000000000000000000e0 * t1022 - t689 + 0.48172707847500000000000000000000000000000000000000e-1 * t1017 + 0.19623283938750000000000000000000000000000000000000e-1 * t1025 - t692 + 0.97184864595000000000000000000000000000000000000000e-2 * t1029) * t695 + t1020 - t1033 - 0.58482236226346462072622386637590534819724553404281e0 * t1046 + 0.58482236226346462072622386637590534819724553404281e0 * t705 * t1052 * t713) + 0.58482236226346462072622386637590534819724553404281e0 * t62 * t1046 - 0.58482236226346462072622386637590534819724553404281e0 * t721 * t704 * t1052 * t713) / 0.2e1)
  t1072 = 0.1e1 / t225 / t271
  t1073 = s2 * t1072
  t1077 = t236 * t223
  t1079 = 0.1e1 / t224 / t1077
  t1081 = t235 * t1079 * t242
  t1089 = t245 / t246 / r1 * t250
  t1098 = t253 / t225 / t246 / t271 * t259
  t1109 = 0.1e1 / t258 / t231
  t1116 = t263 * s2
  t1117 = 0.1e1 / t223
  t1122 = t263 * t269
  t1124 = 0.1e1 / t224 / t236
  t1126 = t159 * t277
  t1132 = f.my_piecewise3(t7, 0, 0.4e1 / 0.3e1 * t23 * t949)
  t1135 = f.my_piecewise3(t168, 0, 0.4e1 / 0.3e1 * t171 * t1010)
  t1137 = (t1132 + t1135) * t61
  t1142 = t736 + t758 - t762 - t767 + t303 * t1137 * t333 + t809 + 0.58482236226346462072622386637590534819724553404281e0 * t1137 * t331 - t816 - t821 - t1007 - t1068
  t1148 = t353 * s2 * t1072
  t1154 = t361 * s2 * t1072
  t1160 = t369 * s2 * t1072
  t1175 = t374 * t433
  t1177 = tau1 * t227
  t1179 = -0.8e1 / 0.3e1 * t1073 - 0.10e2 / 0.3e1 * t1177
  t1180 = params.alpha_ss * t1179
  t1189 = t431 * t444
  t1200 = t408 * t429
  t1205 = t432 ** 2
  t1207 = t442 / t1205
  t1218 = params.alpha_ab * t1179
  t1246 = t1007 * t145 * t164 + t1068 * t262 * t279 + t222 * (-0.8e1 / 0.3e1 * t96 * t1073 * t232 + 0.8e1 / 0.3e1 * t584 * t1081 - 0.16e2 / 0.3e1 * t111 * t1081 + 0.16e2 / 0.3e1 * t594 * t1089 - 0.8e1 * t124 * t1089 + 0.8e1 * t603 * t1098 - 0.32e2 / 0.3e1 * t135 * t1098 + 0.32e2 / 0.3e1 * t614 * t253 * s2 / t224 / t246 / t1077 * t1109) * t279 + t1116 * t1117 * t266 * t278 / 0.8e1 - 0.40e2 / 0.3e1 * t1122 * t270 * t1124 * t1126 + t1142 * t372 + t338 * (-0.8e1 / 0.3e1 * t341 * t1073 * t345 + 0.8e1 / 0.3e1 * t828 * t1148 - 0.16e2 / 0.3e1 * t833 * t1148 + 0.16e2 / 0.3e1 * t837 * t1154 - 0.8e1 * t842 * t1154 + 0.8e1 * t846 * t1160 - 0.32e2 / 0.3e1 * t851 * t1160 + 0.32e2 / 0.3e1 * t856 * t858 * s2 * t1072) + t1007 * t415 * t152 + t1068 * t446 * t269 + t222 * (-t1175 * t1180 + (-0.8e1 / 0.3e1 * t427 * t1072 - 0.10e2 / 0.3e1 * t394 * tau1 * t227) * t433 - 0.2e1 * t1189 * t1180 + (-0.16e2 / 0.3e1 * t435 * t1079 - 0.8e1 / 0.3e1 * t437 * t1072 * t429 - 0.10e2 / 0.3e1 * t437 * t239 * tau1 - 0.20e2 / 0.3e1 * t1200 * t1177) * t444 - 0.3e1 * t1207 * t1180) * t269 + t447 * s2 * t1117 * t266 / 0.8e1 + t1142 * t477 + t338 * (-t912 * t1218 + (-0.8e1 / 0.3e1 * t456 * s2 * t1072 - 0.10e2 / 0.3e1 * t458 * tau1 * t227) * t463 - 0.2e1 * t923 * t1218 + (-0.16e2 / 0.3e1 * t926 * t1073 - 0.8e1 / 0.3e1 * t467 * s2 * t1072 * t459 - 0.10e2 / 0.3e1 * t468 * t1177 - 0.20e2 / 0.3e1 * t935 * t1177) * t475 - 0.3e1 * t942 * t1218)
  vrho_1_ = t3 * t1246 + t165 + t280 + t373 + t417 + t448 + t478
  t1251 = s0 * t116 * t119
  t1256 = t112 * t127 * t130
  t1262 = t125 * t139 * t142
  t1277 = t147 * t149
  t1283 = t342 * t353
  t1284 = t1283 * t101
  t1288 = t351 * t361
  t1289 = t1288 * t101
  t1294 = t359 * t369
  t1295 = t1294 * t101
  t1300 = t367 * t858
  t1306 = params.alpha_ss * t101
  t1326 = params.alpha_ab * t101
  vsigma_0_ = t3 * (t93 * (t96 * t101 * t106 - t584 * t1251 + 0.2e1 * t111 * t1251 - 0.2e1 * t594 * t1256 + 0.3e1 * t124 * t1256 - 0.3e1 * t603 * t1262 + 0.4e1 * t135 * t1262 - 0.4e1 * t614 * t136 / t98 / t126 / t114 * t621) * t164 - t146 * t1277 * t163 / 0.8e1 + t338 * (-0.4e1 * t855 * t1300 * t101 + t341 * t101 * t345 + 0.2e1 * t350 * t1284 - t827 * t1284 + 0.3e1 * t358 * t1289 - 0.2e1 * t836 * t1289 + 0.4e1 * t366 * t1295 - 0.3e1 * t845 * t1295) + t93 * (-t867 * t1306 + t391 * t101 * t399 - 0.2e1 * t881 * t1306 + (0.2e1 * t401 * s0 * t116 + t404 * t101 * t395) * t413 - 0.3e1 * t899 * t1306) * t152 - t416 * t1277 / 0.8e1 + t338 * (-t912 * t1326 + t456 * t101 * t463 - 0.2e1 * t923 * t1326 + (t467 * t101 * t459 + 0.2e1 * t926 * t101) * t475 - 0.3e1 * t942 * t1326))
  vsigma_1_ = 0.0e0
  t1346 = s2 * t239 * t242
  t1351 = t235 * t247 * t250
  t1357 = t245 * t256 * t259
  t1372 = t264 * t266
  t1378 = t1283 * t227
  t1382 = t1288 * t227
  t1387 = t1294 * t227
  t1397 = params.alpha_ss * t227
  t1417 = params.alpha_ab * t227
  vsigma_2_ = t3 * (t222 * (t96 * t227 * t232 - t584 * t1346 + 0.2e1 * t111 * t1346 - 0.2e1 * t594 * t1351 + 0.3e1 * t124 * t1351 - 0.3e1 * t603 * t1357 + 0.4e1 * t135 * t1357 - 0.4e1 * t614 * t253 / t224 / t246 / t237 * t1109) * t279 - t263 * t1372 * t278 / 0.8e1 + t338 * (-0.4e1 * t855 * t1300 * t227 + t341 * t227 * t345 + 0.2e1 * t350 * t1378 - t827 * t1378 + 0.3e1 * t358 * t1382 - 0.2e1 * t836 * t1382 + 0.4e1 * t366 * t1387 - 0.3e1 * t845 * t1387) + t222 * (-t1175 * t1397 + t391 * t227 * t433 - 0.2e1 * t1189 * t1397 + (0.2e1 * t401 * s2 * t239 + t404 * t227 * t429) * t444 - 0.3e1 * t1207 * t1397) * t269 - t447 * t1372 / 0.8e1 + t338 * (-t912 * t1417 + t456 * t227 * t463 - 0.2e1 * t923 * t1417 + (t467 * t227 * t459 + 0.2e1 * t926 * t227) * t475 - 0.3e1 * t942 * t1417))
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t1434 = 0.1e1 / t153
  t1443 = params.alpha_ss * t376
  t1465 = params.alpha_ab * t376
  vtau_0_ = t3 * (t628 * t147 * t1434 * t163 / 0.8e1 + 0.8e1 * t634 * tau0 * t156 * t638 + t93 * (-0.2e1 * t867 * t1443 + 0.2e1 * t394 * t376 * t399 - 0.4e1 * t881 * t1443 + (0.4e1 * t892 * t376 + 0.2e1 * t405 * t636) * t413 - 0.6e1 * t899 * t1443) * t152 + t416 * t148 * t1434 / 0.8e1 + t338 * (-0.2e1 * t912 * t1465 + 0.2e1 * t458 * t376 * t463 - 0.4e1 * t923 * t1465 + (0.2e1 * t468 * t376 + 0.4e1 * t935 * t376) * t475 - 0.6e1 * t942 * t1465))
  t1484 = 0.1e1 / t270
  t1493 = params.alpha_ss * t419
  t1515 = params.alpha_ab * t419
  vtau_1_ = t3 * (t1116 * t264 * t1484 * t278 / 0.8e1 + 0.8e1 * t1122 * tau1 * t273 * t1126 + t222 * (-0.2e1 * t1175 * t1493 + 0.2e1 * t394 * t419 * t433 - 0.4e1 * t1189 * t1493 + (0.2e1 * t437 * t1124 + 0.4e1 * t1200 * t419) * t444 - 0.6e1 * t1207 * t1493) * t269 + t447 * t265 * t1484 / 0.8e1 + t338 * (-0.2e1 * t912 * t1515 + 0.2e1 * t458 * t419 * t463 - 0.4e1 * t923 * t1515 + (0.2e1 * t468 * t419 + 0.4e1 * t935 * t419) * t475 - 0.6e1 * t942 * t1515))
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
  params_alpha_ab_raw = params.alpha_ab
  if isinstance(params_alpha_ab_raw, (str, bytes, dict)):
    params_alpha_ab = params_alpha_ab_raw
  else:
    try:
      params_alpha_ab_seq = list(params_alpha_ab_raw)
    except TypeError:
      params_alpha_ab = params_alpha_ab_raw
    else:
      params_alpha_ab_seq = np.asarray(params_alpha_ab_seq, dtype=np.float64)
      params_alpha_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_ab_seq))
  params_alpha_ss_raw = params.alpha_ss
  if isinstance(params_alpha_ss_raw, (str, bytes, dict)):
    params_alpha_ss = params_alpha_ss_raw
  else:
    try:
      params_alpha_ss_seq = list(params_alpha_ss_raw)
    except TypeError:
      params_alpha_ss = params_alpha_ss_raw
    else:
      params_alpha_ss_seq = np.asarray(params_alpha_ss_seq, dtype=np.float64)
      params_alpha_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_ss_seq))
  params_cab_raw = params.cab
  if isinstance(params_cab_raw, (str, bytes, dict)):
    params_cab = params_cab_raw
  else:
    try:
      params_cab_seq = list(params_cab_raw)
    except TypeError:
      params_cab = params_cab_raw
    else:
      params_cab_seq = np.asarray(params_cab_seq, dtype=np.float64)
      params_cab = np.concatenate((np.array([np.nan], dtype=np.float64), params_cab_seq))
  params_css_raw = params.css
  if isinstance(params_css_raw, (str, bytes, dict)):
    params_css = params_css_raw
  else:
    try:
      params_css_seq = list(params_css_raw)
    except TypeError:
      params_css = params_css_raw
    else:
      params_css_seq = np.asarray(params_css_seq, dtype=np.float64)
      params_css = np.concatenate((np.array([np.nan], dtype=np.float64), params_css_seq))
  params_dab_raw = params.dab
  if isinstance(params_dab_raw, (str, bytes, dict)):
    params_dab = params_dab_raw
  else:
    try:
      params_dab_seq = list(params_dab_raw)
    except TypeError:
      params_dab = params_dab_raw
    else:
      params_dab_seq = np.asarray(params_dab_seq, dtype=np.float64)
      params_dab = np.concatenate((np.array([np.nan], dtype=np.float64), params_dab_seq))
  params_dss_raw = params.dss
  if isinstance(params_dss_raw, (str, bytes, dict)):
    params_dss = params_dss_raw
  else:
    try:
      params_dss_seq = list(params_dss_raw)
    except TypeError:
      params_dss = params_dss_raw
    else:
      params_dss_seq = np.asarray(params_dss_seq, dtype=np.float64)
      params_dss = np.concatenate((np.array([np.nan], dtype=np.float64), params_dss_seq))
  params_gamma_ab_raw = params.gamma_ab
  if isinstance(params_gamma_ab_raw, (str, bytes, dict)):
    params_gamma_ab = params_gamma_ab_raw
  else:
    try:
      params_gamma_ab_seq = list(params_gamma_ab_raw)
    except TypeError:
      params_gamma_ab = params_gamma_ab_raw
    else:
      params_gamma_ab_seq = np.asarray(params_gamma_ab_seq, dtype=np.float64)
      params_gamma_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_ab_seq))
  params_gamma_ss_raw = params.gamma_ss
  if isinstance(params_gamma_ss_raw, (str, bytes, dict)):
    params_gamma_ss = params_gamma_ss_raw
  else:
    try:
      params_gamma_ss_seq = list(params_gamma_ss_raw)
    except TypeError:
      params_gamma_ss = params_gamma_ss_raw
    else:
      params_gamma_ss_seq = np.asarray(params_gamma_ss_seq, dtype=np.float64)
      params_gamma_ss = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_ss_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  gvt4_gamm = lambda alpha, x, z: 1 + alpha * (x ** 2 + z)

  b97_g = lambda gamma, cc, x: jnp.sum(jnp.array([cc[i] * (gamma * x ** 2 / (1 + gamma * x ** 2)) ** (i - 1) for i in range(1, 5 + 1)]), axis=0)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  gtv4 = lambda alpha, dd, x, z: dd[1] / gvt4_gamm(alpha, x, z) + (dd[2] * x ** 2 + dd[3] * z) / gvt4_gamm(alpha, x, z) ** 2 + (dd[4] * x ** 4 + dd[5] * x ** 2 * z + dd[6] * z ** 2) / gvt4_gamm(alpha, x, z) ** 3

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  vsxc_comp = lambda rs, z, spin, xs, ts: +lda_stoll_par(f, params, f_pw, rs, z, 1) * gtv4(params_alpha_ss, params_dss, xs, 2 * (ts - K_FACTOR_C)) * f.Fermi_D(xs, ts)

  vsxc_fperp = lambda rs, z, xs0, xs1, ts0, ts1: +lda_stoll_perp(f, params, f_pw, rs, z) * gtv4(params_alpha_ab, params_dab, jnp.sqrt(xs0 ** 2 + xs1 ** 2), 2 * (ts0 + ts1 - 2 * K_FACTOR_C))

  m05_comp = lambda rs, z, spin, xs, t: +lda_stoll_par(f, params, f_pw, rs, z, 1) * b97_g(params_gamma_ss, params_css, xs) * f.Fermi_D_corrected(xs, t)

  m05_fperp = lambda rs, z, xs0, xs1, t0=None, t1=None: +lda_stoll_perp(f, params, f_pw, rs, z) * b97_g(params_gamma_ab, params_cab, jnp.sqrt(xs0 ** 2 + xs1 ** 2))

  vsxc_fpar = lambda rs, z, xs0, xs1, ts0, ts1: +vsxc_comp(rs, z, 1, xs0, ts0) + vsxc_comp(rs, -z, -1, xs1, ts1)

  m05_fpar = lambda rs, z, xs0, xs1, t0, t1: +m05_comp(rs, z, 1, xs0, t0) + m05_comp(rs, -z, -1, xs1, t1)

  vsxc_f = lambda rs, z, xs0, xs1, ts0, ts1: +vsxc_fpar(rs, z, xs0, xs1, ts0, ts1) + vsxc_fperp(rs, z, xs0, xs1, ts0, ts1)

  m05_f = lambda rs, z, xs0, xs1, t0, t1: +m05_fpar(rs, z, xs0, xs1, t0, t1) + m05_fperp(rs, z, xs0, xs1, t0, t1)

  m06l_f = lambda rs, z, xs0, xs1, ts0, ts1: +m05_f(rs, z, xs0, xs1, ts0, ts1) + vsxc_f(rs, z, xs0, xs1, ts0, ts1)

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: m06l_f(rs, z, xs0, xs1, ts0, ts1)

  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = r0 / 0.2e1 <= f.p.dens_threshold or t3
  t5 = f.my_piecewise3(t3, f.p.zeta_threshold, 1)
  t6 = 3 ** (0.1e1 / 0.3e1)
  t8 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t9 = t6 * t8
  t10 = 4 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = t9 * t11
  t13 = r0 ** (0.1e1 / 0.3e1)
  t14 = 0.1e1 / t13
  t15 = 2 ** (0.1e1 / 0.3e1)
  t17 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t19 = f.my_piecewise3(t3, 0.1e1 / t17, 1)
  t21 = t12 * t14 * t15 * t19
  t23 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t21
  t24 = jnp.sqrt(t21)
  t27 = t21 ** 0.15e1
  t29 = t6 ** 2
  t30 = t8 ** 2
  t31 = t29 * t30
  t32 = t31 * t10
  t33 = t13 ** 2
  t34 = 0.1e1 / t33
  t35 = t15 ** 2
  t37 = t19 ** 2
  t39 = t32 * t34 * t35 * t37
  t41 = 0.23615562999000000000000000000000000000000000000000e0 * t24 + 0.55770497660000000000000000000000000000000000000000e-1 * t21 + 0.12733196185000000000000000000000000000000000000000e-1 * t27 + 0.76629248290000000000000000000000000000000000000000e-2 * t39
  t43 = 0.1e1 + 0.1e1 / t41
  t44 = jnp.log(t43)
  t45 = t23 * t44
  t47 = t17 * f.p.zeta_threshold
  t49 = f.my_piecewise3(0.2e1 <= f.p.zeta_threshold, t47, 0.2e1 * t15)
  t51 = f.my_piecewise3(0.0e0 <= f.p.zeta_threshold, t47, 0)
  t55 = 0.1e1 / (0.2e1 * t15 - 0.2e1)
  t56 = (t49 + t51 - 0.2e1) * t55
  t58 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t21
  t63 = 0.21948324211500000000000000000000000000000000000000e0 * t24 + 0.48172707847500000000000000000000000000000000000000e-1 * t21 + 0.13082189292500000000000000000000000000000000000000e-1 * t27 + 0.48592432297500000000000000000000000000000000000000e-2 * t39
  t65 = 0.1e1 + 0.1e1 / t63
  t66 = jnp.log(t65)
  t69 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t21
  t74 = 0.17489762330000000000000000000000000000000000000000e0 * t24 + 0.30591463695000000000000000000000000000000000000000e-1 * t21 + 0.37162156485000000000000000000000000000000000000000e-2 * t27 + 0.41939460495000000000000000000000000000000000000000e-2 * t39
  t76 = 0.1e1 + 0.1e1 / t74
  t77 = jnp.log(t76)
  t78 = t69 * t77
  t87 = f.my_piecewise3(t4, 0, t5 * (-t45 + t56 * (-t58 * t66 + t45 - 0.58482236226346462072622386637590534819724553404281e0 * t78) + 0.58482236226346462072622386637590534819724553404281e0 * t56 * t78) / 0.2e1)
  t89 = params.css[1]
  t90 = t89 * params.gamma_ss
  t91 = t90 * s0
  t92 = r0 ** 2
  t94 = 0.1e1 / t33 / t92
  t95 = t35 * t94
  t98 = params.gamma_ss * s0 * t95 + 0.1e1
  t99 = 0.1e1 / t98
  t100 = t95 * t99
  t102 = params.css[2]
  t103 = params.gamma_ss ** 2
  t104 = t102 * t103
  t105 = s0 ** 2
  t106 = t104 * t105
  t107 = t92 ** 2
  t108 = t107 * r0
  t111 = t15 / t13 / t108
  t112 = t98 ** 2
  t113 = 0.1e1 / t112
  t114 = t111 * t113
  t117 = params.css[3]
  t118 = t103 * params.gamma_ss
  t119 = t117 * t118
  t120 = t105 * s0
  t121 = t107 ** 2
  t122 = 0.1e1 / t121
  t123 = t120 * t122
  t125 = 0.1e1 / t112 / t98
  t129 = params.css[4]
  t130 = t103 ** 2
  t131 = t129 * t130
  t132 = t105 ** 2
  t133 = t131 * t132
  t137 = t35 / t33 / t121 / t92
  t138 = t112 ** 2
  t139 = 0.1e1 / t138
  t140 = t137 * t139
  t143 = 0.4e1 * t119 * t123 * t125 + t91 * t100 + 0.2e1 * t106 * t114 + 0.4e1 * t133 * t140 + params.css[0]
  t144 = t87 * t143
  t145 = 0.1e1 / r0
  t146 = s0 * t145
  t147 = 0.1e1 / tau0
  t150 = 0.1e1 - t146 * t147 / 0.8e1
  t151 = tau0 ** 2
  t153 = t92 * r0
  t155 = 0.1e1 / t13 / t153
  t156 = params.Fermi_D_cnst ** 2
  t157 = 0.1e1 / t156
  t161 = jnp.exp(-0.8e1 * t151 * t15 * t155 * t157)
  t162 = 0.1e1 - t161
  t163 = t150 * t162
  t167 = t9 * t11 * t14
  t169 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t167
  t170 = jnp.sqrt(t167)
  t173 = t167 ** 0.15e1
  t176 = t31 * t10 * t34
  t178 = 0.23615562999000000000000000000000000000000000000000e0 * t170 + 0.55770497660000000000000000000000000000000000000000e-1 * t167 + 0.12733196185000000000000000000000000000000000000000e-1 * t173 + 0.76629248290000000000000000000000000000000000000000e-2 * t176
  t180 = 0.1e1 + 0.1e1 / t178
  t181 = jnp.log(t180)
  t183 = f.my_piecewise3(t3, t47, 1)
  t186 = (0.2e1 * t183 - 0.2e1) * t55
  t188 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t167
  t193 = 0.17489762330000000000000000000000000000000000000000e0 * t170 + 0.30591463695000000000000000000000000000000000000000e-1 * t167 + 0.37162156485000000000000000000000000000000000000000e-2 * t173 + 0.41939460495000000000000000000000000000000000000000e-2 * t176
  t195 = 0.1e1 + 0.1e1 / t193
  t196 = jnp.log(t195)
  t201 = -t169 * t181 + 0.58482236226346462072622386637590534819724553404281e0 * t186 * t188 * t196 - 0.2e1 * t87
  t203 = params.cab[1]
  t204 = t203 * params.gamma_ab
  t205 = t204 * s0
  t209 = 0.2e1 * params.gamma_ab * s0 * t95 + 0.1e1
  t210 = 0.1e1 / t209
  t211 = t95 * t210
  t214 = params.cab[2]
  t215 = params.gamma_ab ** 2
  t216 = t214 * t215
  t217 = t216 * t105
  t218 = t209 ** 2
  t219 = 0.1e1 / t218
  t220 = t111 * t219
  t223 = params.cab[3]
  t224 = t215 * params.gamma_ab
  t225 = t223 * t224
  t227 = 0.1e1 / t218 / t209
  t231 = params.cab[4]
  t232 = t215 ** 2
  t233 = t231 * t232
  t234 = t233 * t132
  t235 = t218 ** 2
  t236 = 0.1e1 / t235
  t237 = t137 * t236
  t240 = 0.32e2 * t225 * t123 * t227 + 0.2e1 * t205 * t211 + 0.8e1 * t217 * t220 + 0.64e2 * t234 * t237 + params.cab[0]
  t242 = params.dss[0]
  t243 = s0 * t35
  t244 = t243 * t94
  t245 = tau0 * t35
  t247 = 0.1e1 / t33 / r0
  t248 = t245 * t247
  t249 = 0.2e1 * t248
  t250 = 6 ** (0.1e1 / 0.3e1)
  t251 = t250 ** 2
  t252 = jnp.pi ** 2
  t253 = t252 ** (0.1e1 / 0.3e1)
  t254 = t253 ** 2
  t255 = t251 * t254
  t256 = 0.3e1 / 0.5e1 * t255
  t259 = 0.1e1 + params.alpha_ss * (t244 + t249 - t256)
  t262 = params.dss[1]
  t263 = t262 * s0
  t265 = params.dss[2]
  t266 = t249 - t256
  t268 = t263 * t95 + t265 * t266
  t269 = t259 ** 2
  t270 = 0.1e1 / t269
  t272 = params.dss[3]
  t273 = t272 * t105
  t276 = params.dss[4]
  t277 = t276 * s0
  t280 = params.dss[5]
  t281 = t266 ** 2
  t283 = t277 * t95 * t266 + 0.2e1 * t273 * t111 + t280 * t281
  t285 = 0.1e1 / t269 / t259
  t287 = t242 / t259 + t268 * t270 + t283 * t285
  t288 = t87 * t287
  t291 = params.dab[0]
  t293 = 0.4e1 * t248
  t294 = 0.6e1 / 0.5e1 * t255
  t297 = 0.1e1 + params.alpha_ab * (0.2e1 * t244 + t293 - t294)
  t300 = params.dab[1]
  t301 = t300 * s0
  t304 = params.dab[2]
  t305 = t293 - t294
  t307 = 0.2e1 * t301 * t95 + t304 * t305
  t308 = t297 ** 2
  t309 = 0.1e1 / t308
  t311 = params.dab[3]
  t312 = t311 * t105
  t315 = params.dab[4]
  t316 = t315 * s0
  t320 = params.dab[5]
  t321 = t305 ** 2
  t323 = 0.2e1 * t316 * t95 * t305 + 0.8e1 * t312 * t111 + t320 * t321
  t325 = 0.1e1 / t308 / t297
  t327 = t291 / t297 + t307 * t309 + t323 * t325
  t330 = 0.1e1 / t13 / r0
  t331 = t330 * t15
  t335 = 0.11073470983333333333333333333333333333333333333333e-2 * t12 * t331 * t19 * t44
  t336 = t41 ** 2
  t342 = t11 * t330
  t343 = t15 * t19
  t344 = t342 * t343
  t345 = 0.1e1 / t24 * t6 * t8 * t344
  t348 = t12 * t331 * t19
  t350 = t21 ** 0.5e0
  t353 = t350 * t6 * t8 * t344
  t355 = t247 * t35
  t357 = t32 * t355 * t37
  t362 = t23 / t336 * (-0.39359271665000000000000000000000000000000000000000e-1 * t345 - 0.18590165886666666666666666666666666666666666666667e-1 * t348 - 0.63665980925000000000000000000000000000000000000000e-2 * t353 - 0.51086165526666666666666666666666666666666666666667e-2 * t357) / t43
  t367 = t63 ** 2
  t382 = t74 ** 2
  t383 = 0.1e1 / t382
  t389 = -0.29149603883333333333333333333333333333333333333333e-1 * t345 - 0.10197154565000000000000000000000000000000000000000e-1 * t348 - 0.18581078242500000000000000000000000000000000000000e-2 * t353 - 0.27959640330000000000000000000000000000000000000000e-2 * t357
  t390 = 0.1e1 / t76
  t409 = f.my_piecewise3(t4, 0, t5 * (t335 + t362 + t56 * (0.53237641966666666666666666666666666666666666666667e-3 * t12 * t331 * t19 * t66 + t58 / t367 * (-0.36580540352500000000000000000000000000000000000000e-1 * t345 - 0.16057569282500000000000000000000000000000000000000e-1 * t348 - 0.65410946462500000000000000000000000000000000000000e-2 * t353 - 0.32394954865000000000000000000000000000000000000000e-2 * t357) / t65 - t335 - t362 + 0.18311447306006545054854346104378990962041954983034e-3 * t12 * t331 * t19 * t77 + 0.58482236226346462072622386637590534819724553404281e0 * t69 * t383 * t389 * t390) - 0.18311447306006545054854346104378990962041954983034e-3 * t56 * t9 * t342 * t343 * t77 - 0.58482236226346462072622386637590534819724553404281e0 * t56 * t69 * t383 * t389 * t390) / 0.2e1)
  t414 = 0.1e1 / t33 / t153
  t415 = t35 * t414
  t419 = t89 * t103
  t421 = t107 * t92
  t424 = t15 / t13 / t421
  t425 = t424 * t113
  t430 = t102 * t118
  t433 = t120 / t121 / r0
  t434 = t433 * t125
  t439 = t117 * t130
  t443 = 0.1e1 / t33 / t121 / t153
  t445 = t443 * t139 * t35
  t451 = t129 * t130 * params.gamma_ss
  t452 = t132 * s0
  t457 = t15 / t13 / t121 / t421
  t459 = 0.1e1 / t138 / t98
  t467 = t144 * s0
  t468 = 0.1e1 / t92
  t477 = t15 / t13 / t107
  t478 = t157 * t161
  t485 = t178 ** 2
  t490 = t8 * t11
  t491 = t490 * t330
  t492 = 0.1e1 / t170 * t6 * t491
  t494 = t9 * t342
  t496 = t167 ** 0.5e0
  t498 = t496 * t6 * t491
  t501 = t31 * t10 * t247
  t513 = t193 ** 2
  t526 = 0.11073470983333333333333333333333333333333333333333e-2 * t9 * t342 * t181 + t169 / t485 * (-0.39359271665000000000000000000000000000000000000000e-1 * t492 - 0.18590165886666666666666666666666666666666666666667e-1 * t494 - 0.63665980925000000000000000000000000000000000000000e-2 * t498 - 0.51086165526666666666666666666666666666666666666667e-2 * t501) / t180 - 0.18311447306006545054854346104378990962041954983034e-3 * t186 * t6 * t490 * t330 * t196 - 0.58482236226346462072622386637590534819724553404281e0 * t186 * t188 / t513 * (-0.29149603883333333333333333333333333333333333333333e-1 * t492 - 0.10197154565000000000000000000000000000000000000000e-1 * t494 - 0.18581078242500000000000000000000000000000000000000e-2 * t498 - 0.27959640330000000000000000000000000000000000000000e-2 * t501) / t195 - 0.2e1 * t409
  t531 = t203 * t215
  t533 = t424 * t219
  t538 = t214 * t224
  t539 = t433 * t227
  t544 = t223 * t232
  t547 = t443 * t236 * t35
  t553 = t231 * t232 * params.gamma_ab
  t556 = 0.1e1 / t235 / t209
  t565 = t242 * t270
  t566 = t243 * t414
  t568 = t245 * t94
  t571 = params.alpha_ss * (-0.8e1 / 0.3e1 * t566 - 0.10e2 / 0.3e1 * t568)
  t580 = t268 * t285
  t588 = t111 * tau0
  t591 = t280 * t266
  t596 = t269 ** 2
  t598 = t283 / t596
  t610 = t291 * t309
  t614 = params.alpha_ab * (-0.16e2 / 0.3e1 * t566 - 0.20e2 / 0.3e1 * t568)
  t623 = t307 * t325
  t633 = t320 * t305
  t638 = t308 ** 2
  t640 = t323 / t638
  t645 = 0.2e1 * t409 * t143 * t163 + 0.2e1 * t87 * (-0.8e1 / 0.3e1 * t91 * t415 * t99 + 0.16e2 / 0.3e1 * t419 * t105 * t425 - 0.32e2 / 0.3e1 * t106 * t425 + 0.64e2 / 0.3e1 * t430 * t434 - 0.32e2 * t119 * t434 + 0.32e2 * t439 * t132 * t445 - 0.128e3 / 0.3e1 * t133 * t445 + 0.256e3 / 0.3e1 * t451 * t452 * t457 * t459) * t163 + t467 * t468 * t147 * t162 / 0.4e1 - 0.160e3 / 0.3e1 * t144 * t150 * t151 * t477 * t478 + t526 * t240 + t201 * (-0.16e2 / 0.3e1 * t205 * t415 * t210 + 0.64e2 / 0.3e1 * t531 * t105 * t533 - 0.128e3 / 0.3e1 * t217 * t533 + 0.512e3 / 0.3e1 * t538 * t539 - 0.256e3 * t225 * t539 + 0.512e3 * t544 * t132 * t547 - 0.2048e4 / 0.3e1 * t234 * t547 + 0.8192e4 / 0.3e1 * t553 * t452 * t457 * t556) + 0.2e1 * t409 * t287 * t150 + 0.2e1 * t87 * (-t565 * t571 + (-0.8e1 / 0.3e1 * t263 * t415 - 0.10e2 / 0.3e1 * t265 * tau0 * t95) * t270 - 0.2e1 * t580 * t571 + (-0.32e2 / 0.3e1 * t273 * t424 - 0.8e1 / 0.3e1 * t277 * t415 * t266 - 0.20e2 / 0.3e1 * t277 * t588 - 0.20e2 / 0.3e1 * t591 * t568) * t285 - 0.3e1 * t598 * t571) * t150 + t288 * s0 * t468 * t147 / 0.4e1 + t526 * t327 + t201 * (-t610 * t614 + (-0.16e2 / 0.3e1 * t301 * t415 - 0.20e2 / 0.3e1 * t304 * tau0 * t95) * t309 - 0.2e1 * t623 * t614 + (-0.128e3 / 0.3e1 * t312 * t424 - 0.16e2 / 0.3e1 * t316 * t415 * t305 - 0.80e2 / 0.3e1 * t316 * t588 - 0.40e2 / 0.3e1 * t633 * t568) * t325 - 0.3e1 * t640 * t614)
  vrho_0_ = r0 * t645 + 0.2e1 * t144 * t163 + 0.2e1 * t288 * t150 + t201 * t240 + t201 * t327
  t654 = t105 * t122
  t655 = t654 * t125
  t670 = t15 / t13 / t121 / t108
  t678 = t145 * t147
  t690 = t654 * t227
  t707 = params.alpha_ss * t35
  t708 = t707 * t94
  t731 = params.alpha_ab * t35
  t732 = t731 * t94
  vsigma_0_ = r0 * (0.2e1 * t87 * (-0.32e2 * t451 * t132 * t670 * t459 + 0.4e1 * t104 * s0 * t114 - 0.2e1 * t419 * s0 * t114 + 0.16e2 * t131 * t120 * t140 - 0.12e2 * t439 * t120 * t140 + t90 * t100 + 0.12e2 * t119 * t655 - 0.8e1 * t430 * t655) * t163 - t144 * t678 * t162 / 0.4e1 + t201 * (-0.1024e4 * t553 * t132 * t670 * t556 + 0.16e2 * t216 * s0 * t220 - 0.8e1 * t531 * s0 * t220 + 0.256e3 * t233 * t120 * t237 - 0.192e3 * t544 * t120 * t237 + 0.2e1 * t204 * t211 + 0.96e2 * t225 * t690 - 0.64e2 * t538 * t690) + 0.2e1 * t87 * (-t565 * t708 + t262 * t35 * t94 * t270 - 0.2e1 * t580 * t708 + (t276 * t35 * t94 * t266 + 0.4e1 * t272 * s0 * t111) * t285 - 0.3e1 * t598 * t708) * t150 - t288 * t678 / 0.4e1 + t201 * (-0.2e1 * t610 * t732 + 0.2e1 * t300 * t35 * t94 * t309 - 0.4e1 * t623 * t732 + (0.2e1 * t315 * t35 * t94 * t305 + 0.16e2 * t311 * s0 * t111) * t325 - 0.6e1 * t640 * t732))
  vlapl_0_ = 0.0e0
  t755 = 0.1e1 / t151
  t766 = t707 * t247
  t789 = t731 * t247
  vtau_0_ = r0 * (t467 * t145 * t755 * t162 / 0.4e1 + 0.32e2 * t144 * t150 * tau0 * t15 * t155 * t478 + 0.2e1 * t87 * (-0.2e1 * t565 * t766 + 0.2e1 * t265 * t35 * t247 * t270 - 0.4e1 * t580 * t766 + (0.4e1 * t277 * t477 + 0.4e1 * t591 * t355) * t285 - 0.6e1 * t598 * t766) * t150 + t288 * t146 * t755 / 0.4e1 + t201 * (-0.4e1 * t610 * t789 + 0.4e1 * t304 * t35 * t247 * t309 - 0.8e1 * t623 * t789 + (0.16e2 * t316 * t477 + 0.8e1 * t633 * t355) * t325 - 0.12e2 * t640 * t789))
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
  return res

def _energy_unpol_sum(p, r, s=None, l=None, tau=None):
  val = unpol(p, r, s, l, tau)
  import jax.numpy as jnp
  return jnp.sum(val)

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = r0 / 0.2e1 <= f.p.dens_threshold or t3
  t5 = f.my_piecewise3(t3, f.p.zeta_threshold, 1)
  t6 = 3 ** (0.1e1 / 0.3e1)
  t8 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t9 = t6 * t8
  t10 = 4 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = t9 * t11
  t13 = r0 ** (0.1e1 / 0.3e1)
  t15 = 0.1e1 / t13 / r0
  t16 = 2 ** (0.1e1 / 0.3e1)
  t17 = t15 * t16
  t18 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t20 = f.my_piecewise3(t3, 0.1e1 / t18, 1)
  t21 = 0.1e1 / t13
  t24 = t12 * t21 * t16 * t20
  t25 = jnp.sqrt(t24)
  t28 = t24 ** 0.15e1
  t30 = t6 ** 2
  t31 = t8 ** 2
  t32 = t30 * t31
  t33 = t32 * t10
  t34 = t13 ** 2
  t35 = 0.1e1 / t34
  t36 = t16 ** 2
  t38 = t20 ** 2
  t40 = t33 * t35 * t36 * t38
  t42 = 0.37978500000000000000000000000000000000000000000000e1 * t25 + 0.89690000000000000000000000000000000000000000000000e0 * t24 + 0.20477500000000000000000000000000000000000000000000e0 * t28 + 0.12323500000000000000000000000000000000000000000000e0 * t40
  t45 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t42
  t46 = jnp.log(t45)
  t47 = t20 * t46
  t50 = 0.11073470983333333333333333333333333333333333333333e-2 * t12 * t17 * t47
  t52 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t24
  t53 = t42 ** 2
  t54 = 0.1e1 / t53
  t55 = t52 * t54
  t58 = 0.1e1 / t25 * t6 * t8
  t59 = t11 * t15
  t60 = t16 * t20
  t61 = t59 * t60
  t62 = t58 * t61
  t64 = t17 * t20
  t65 = t12 * t64
  t67 = t24 ** 0.5e0
  t69 = t67 * t6 * t8
  t70 = t69 * t61
  t73 = 0.1e1 / t34 / r0
  t76 = t33 * t73 * t36 * t38
  t78 = -0.63297500000000000000000000000000000000000000000000e0 * t62 - 0.29896666666666666666666666666666666666666666666667e0 * t65 - 0.10238750000000000000000000000000000000000000000000e0 * t70 - 0.82156666666666666666666666666666666666666666666667e-1 * t76
  t79 = 0.1e1 / t45
  t82 = 0.10000000000000000000000000000000000000000000000000e1 * t55 * t78 * t79
  t84 = t18 * f.p.zeta_threshold
  t86 = f.my_piecewise3(0.2e1 <= f.p.zeta_threshold, t84, 0.2e1 * t16)
  t88 = f.my_piecewise3(0.0e0 <= f.p.zeta_threshold, t84, 0)
  t92 = 0.1e1 / (0.2e1 * t16 - 0.2e1)
  t93 = (t86 + t88 - 0.2e1) * t92
  t98 = 0.70594500000000000000000000000000000000000000000000e1 * t25 + 0.15494250000000000000000000000000000000000000000000e1 * t24 + 0.42077500000000000000000000000000000000000000000000e0 * t28 + 0.15629250000000000000000000000000000000000000000000e0 * t40
  t101 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t98
  t102 = jnp.log(t101)
  t103 = t20 * t102
  t108 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t24
  t109 = t98 ** 2
  t110 = 0.1e1 / t109
  t111 = t108 * t110
  t116 = -0.11765750000000000000000000000000000000000000000000e1 * t62 - 0.51647500000000000000000000000000000000000000000000e0 * t65 - 0.21038750000000000000000000000000000000000000000000e0 * t70 - 0.10419500000000000000000000000000000000000000000000e0 * t76
  t117 = 0.1e1 / t101
  t125 = 0.51785000000000000000000000000000000000000000000000e1 * t25 + 0.90577500000000000000000000000000000000000000000000e0 * t24 + 0.11003250000000000000000000000000000000000000000000e0 * t28 + 0.12417750000000000000000000000000000000000000000000e0 * t40
  t128 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t125
  t129 = jnp.log(t128)
  t130 = t20 * t129
  t135 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t24
  t136 = t125 ** 2
  t137 = 0.1e1 / t136
  t138 = t135 * t137
  t143 = -0.86308333333333333333333333333333333333333333333334e0 * t62 - 0.30192500000000000000000000000000000000000000000000e0 * t65 - 0.55016250000000000000000000000000000000000000000000e-1 * t70 - 0.82785000000000000000000000000000000000000000000000e-1 * t76
  t144 = 0.1e1 / t128
  t150 = t93 * t9
  t151 = t60 * t129
  t155 = t93 * t135
  t157 = t137 * t143 * t144
  t163 = f.my_piecewise3(t4, 0, t5 * (t50 + t82 + t93 * (0.53237641966666666666666666666666666666666666666666e-3 * t12 * t17 * t103 + 0.10000000000000000000000000000000000000000000000000e1 * t111 * t116 * t117 - t50 - t82 + 0.18311447306006545054854346104378990962041954983034e-3 * t12 * t17 * t130 + 0.58482236226346462072622386637590534819724553404280e0 * t138 * t143 * t144) - 0.18311447306006545054854346104378990962041954983034e-3 * t150 * t59 * t151 - 0.58482236226346462072622386637590534819724553404280e0 * t155 * t157) / 0.2e1)
  t165 = params.css[1]
  t167 = t165 * params.gamma_ss * s0
  t168 = r0 ** 2
  t170 = 0.1e1 / t34 / t168
  t171 = t36 * t170
  t174 = params.gamma_ss * s0 * t171 + 0.1e1
  t175 = 0.1e1 / t174
  t178 = params.css[2]
  t179 = params.gamma_ss ** 2
  t181 = s0 ** 2
  t182 = t178 * t179 * t181
  t183 = t168 ** 2
  t187 = t16 / t13 / t183 / r0
  t188 = t174 ** 2
  t189 = 0.1e1 / t188
  t193 = params.css[3]
  t194 = t179 * params.gamma_ss
  t195 = t193 * t194
  t196 = t181 * s0
  t197 = t183 ** 2
  t199 = t196 / t197
  t201 = 0.1e1 / t188 / t174
  t205 = params.css[4]
  t206 = t179 ** 2
  t208 = t181 ** 2
  t209 = t205 * t206 * t208
  t210 = t197 * t168
  t213 = t36 / t34 / t210
  t214 = t188 ** 2
  t215 = 0.1e1 / t214
  t219 = t167 * t171 * t175 + 0.2e1 * t182 * t187 * t189 + 0.4e1 * t195 * t199 * t201 + 0.4e1 * t209 * t213 * t215 + params.css[0]
  t220 = t163 * t219
  t223 = 0.1e1 / tau0
  t226 = 0.1e1 - s0 / r0 * t223 / 0.8e1
  t227 = tau0 ** 2
  t229 = t168 * r0
  t232 = params.Fermi_D_cnst ** 2
  t233 = 0.1e1 / t232
  t237 = jnp.exp(-0.8e1 * t227 * t16 / t13 / t229 * t233)
  t238 = 0.1e1 - t237
  t239 = t226 * t238
  t243 = 0.621814e-1 * t52 * t46
  t246 = t135 * t129
  t255 = f.my_piecewise3(t4, 0, t5 * (-t243 + t93 * (-0.3109070e-1 * t108 * t102 + t243 - 0.19751673498613801407483339618206552048944131217655e-1 * t246) + 0.19751673498613801407483339618206552048944131217655e-1 * t93 * t246) / 0.2e1)
  t257 = 0.1e1 / t34 / t229
  t258 = t36 * t257
  t263 = t165 * t179 * t181
  t264 = t183 * t168
  t266 = 0.1e1 / t13 / t264
  t267 = t16 * t266
  t268 = t267 * t189
  t273 = t178 * t194
  t276 = t196 / t197 / r0
  t277 = t276 * t201
  t283 = t193 * t206 * t208
  t286 = 0.1e1 / t34 / t197 / t229
  t288 = t286 * t215 * t36
  t293 = t206 * params.gamma_ss
  t295 = t208 * s0
  t296 = t205 * t293 * t295
  t300 = t16 / t13 / t197 / t264
  t302 = 0.1e1 / t214 / t174
  t306 = -0.8e1 / 0.3e1 * t167 * t258 * t175 + 0.16e2 / 0.3e1 * t263 * t268 - 0.32e2 / 0.3e1 * t182 * t268 + 0.64e2 / 0.3e1 * t273 * t277 - 0.32e2 * t195 * t277 + 0.32e2 * t283 * t288 - 0.128e3 / 0.3e1 * t209 * t288 + 0.256e3 / 0.3e1 * t296 * t300 * t302
  t307 = t255 * t306
  t310 = t255 * t219
  t311 = t310 * s0
  t312 = 0.1e1 / t168
  t314 = t312 * t223 * t238
  t317 = t226 * t227
  t318 = t310 * t317
  t322 = t233 * t237
  t323 = t16 / t13 / t183 * t322
  t327 = t9 * t11 * t21
  t328 = jnp.sqrt(t327)
  t331 = t327 ** 0.15e1
  t334 = t32 * t10 * t35
  t336 = 0.37978500000000000000000000000000000000000000000000e1 * t328 + 0.89690000000000000000000000000000000000000000000000e0 * t327 + 0.20477500000000000000000000000000000000000000000000e0 * t331 + 0.12323500000000000000000000000000000000000000000000e0 * t334
  t339 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t336
  t340 = jnp.log(t339)
  t345 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t327
  t346 = t336 ** 2
  t347 = 0.1e1 / t346
  t348 = t345 * t347
  t350 = 0.1e1 / t328 * t6
  t351 = t8 * t11
  t352 = t351 * t15
  t353 = t350 * t352
  t355 = t9 * t59
  t357 = t327 ** 0.5e0
  t358 = t357 * t6
  t359 = t358 * t352
  t362 = t32 * t10 * t73
  t364 = -0.63297500000000000000000000000000000000000000000000e0 * t353 - 0.29896666666666666666666666666666666666666666666667e0 * t355 - 0.10238750000000000000000000000000000000000000000000e0 * t359 - 0.82156666666666666666666666666666666666666666666667e-1 * t362
  t365 = 0.1e1 / t339
  t366 = t364 * t365
  t369 = f.my_piecewise3(t3, t84, 1)
  t372 = (0.2e1 * t369 - 0.2e1) * t92
  t373 = t372 * t6
  t378 = 0.51785000000000000000000000000000000000000000000000e1 * t328 + 0.90577500000000000000000000000000000000000000000000e0 * t327 + 0.11003250000000000000000000000000000000000000000000e0 * t331 + 0.12417750000000000000000000000000000000000000000000e0 * t334
  t381 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t378
  t382 = jnp.log(t381)
  t388 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t327
  t389 = t372 * t388
  t390 = t378 ** 2
  t391 = 0.1e1 / t390
  t396 = -0.86308333333333333333333333333333333333333333333334e0 * t353 - 0.30192500000000000000000000000000000000000000000000e0 * t355 - 0.55016250000000000000000000000000000000000000000000e-1 * t359 - 0.82785000000000000000000000000000000000000000000000e-1 * t362
  t398 = 0.1e1 / t381
  t399 = t391 * t396 * t398
  t403 = 0.11073470983333333333333333333333333333333333333333e-2 * t9 * t59 * t340 + 0.10000000000000000000000000000000000000000000000000e1 * t348 * t366 - 0.18311447306006545054854346104378990962041954983034e-3 * t373 * t351 * t15 * t382 - 0.58482236226346462072622386637590534819724553404280e0 * t389 * t399 - 0.2e1 * t163
  t405 = params.cab[1]
  t407 = t405 * params.gamma_ab * s0
  t411 = 0.2e1 * params.gamma_ab * s0 * t171 + 0.1e1
  t412 = 0.1e1 / t411
  t416 = params.cab[2]
  t417 = params.gamma_ab ** 2
  t419 = t416 * t417 * t181
  t420 = t411 ** 2
  t421 = 0.1e1 / t420
  t425 = params.cab[3]
  t426 = t417 * params.gamma_ab
  t427 = t425 * t426
  t429 = 0.1e1 / t420 / t411
  t433 = params.cab[4]
  t434 = t417 ** 2
  t436 = t433 * t434 * t208
  t437 = t420 ** 2
  t438 = 0.1e1 / t437
  t442 = 0.2e1 * t407 * t171 * t412 + 0.8e1 * t419 * t187 * t421 + 0.32e2 * t427 * t199 * t429 + 0.64e2 * t436 * t213 * t438 + params.cab[0]
  t451 = -0.621814e-1 * t345 * t340 + 0.19751673498613801407483339618206552048944131217655e-1 * t372 * t388 * t382 - 0.2e1 * t255
  t456 = t405 * t417 * t181
  t457 = t267 * t421
  t462 = t416 * t426
  t463 = t276 * t429
  t469 = t425 * t434 * t208
  t471 = t286 * t438 * t36
  t476 = t434 * params.gamma_ab
  t478 = t433 * t476 * t295
  t480 = 0.1e1 / t437 / t411
  t484 = -0.16e2 / 0.3e1 * t407 * t258 * t412 + 0.64e2 / 0.3e1 * t456 * t457 - 0.128e3 / 0.3e1 * t419 * t457 + 0.512e3 / 0.3e1 * t462 * t463 - 0.256e3 * t427 * t463 + 0.512e3 * t469 * t471 - 0.2048e4 / 0.3e1 * t436 * t471 + 0.8192e4 / 0.3e1 * t478 * t300 * t480
  t487 = params.dss[0]
  t488 = s0 * t36
  t489 = t488 * t170
  t490 = tau0 * t36
  t491 = t490 * t73
  t492 = 0.2e1 * t491
  t493 = 6 ** (0.1e1 / 0.3e1)
  t494 = t493 ** 2
  t495 = jnp.pi ** 2
  t496 = t495 ** (0.1e1 / 0.3e1)
  t497 = t496 ** 2
  t498 = t494 * t497
  t499 = 0.3e1 / 0.5e1 * t498
  t502 = 0.1e1 + params.alpha_ss * (t489 + t492 - t499)
  t506 = params.dss[1] * s0
  t508 = params.dss[2]
  t509 = t492 - t499
  t511 = t506 * t171 + t508 * t509
  t512 = t502 ** 2
  t513 = 0.1e1 / t512
  t516 = params.dss[3] * t181
  t520 = params.dss[4] * s0
  t523 = params.dss[5]
  t524 = t509 ** 2
  t526 = t520 * t171 * t509 + 0.2e1 * t516 * t187 + t523 * t524
  t528 = 0.1e1 / t512 / t502
  t530 = t487 / t502 + t511 * t513 + t526 * t528
  t531 = t163 * t530
  t534 = t487 * t513
  t535 = t488 * t257
  t537 = t490 * t170
  t539 = -0.8e1 / 0.3e1 * t535 - 0.10e2 / 0.3e1 * t537
  t540 = params.alpha_ss * t539
  t544 = t508 * tau0
  t547 = -0.8e1 / 0.3e1 * t506 * t258 - 0.10e2 / 0.3e1 * t544 * t171
  t549 = t511 * t528
  t557 = t187 * tau0
  t560 = t523 * t509
  t563 = -0.32e2 / 0.3e1 * t516 * t267 - 0.8e1 / 0.3e1 * t520 * t258 * t509 - 0.20e2 / 0.3e1 * t520 * t557 - 0.20e2 / 0.3e1 * t560 * t537
  t565 = t512 ** 2
  t566 = 0.1e1 / t565
  t567 = t526 * t566
  t570 = t547 * t513 + t563 * t528 - t534 * t540 - 0.2e1 * t549 * t540 - 0.3e1 * t567 * t540
  t571 = t255 * t570
  t574 = t255 * t530
  t576 = s0 * t312 * t223
  t579 = params.dab[0]
  t581 = 0.4e1 * t491
  t582 = 0.6e1 / 0.5e1 * t498
  t585 = 0.1e1 + params.alpha_ab * (0.2e1 * t489 + t581 - t582)
  t589 = params.dab[1] * s0
  t592 = params.dab[2]
  t593 = t581 - t582
  t595 = 0.2e1 * t589 * t171 + t592 * t593
  t596 = t585 ** 2
  t597 = 0.1e1 / t596
  t600 = params.dab[3] * t181
  t604 = params.dab[4] * s0
  t608 = params.dab[5]
  t609 = t593 ** 2
  t611 = 0.2e1 * t604 * t171 * t593 + 0.8e1 * t600 * t187 + t608 * t609
  t613 = 0.1e1 / t596 / t585
  t615 = t579 / t585 + t595 * t597 + t611 * t613
  t618 = t579 * t597
  t621 = -0.16e2 / 0.3e1 * t535 - 0.20e2 / 0.3e1 * t537
  t622 = params.alpha_ab * t621
  t626 = t592 * tau0
  t629 = -0.16e2 / 0.3e1 * t589 * t258 - 0.20e2 / 0.3e1 * t626 * t171
  t631 = t595 * t613
  t641 = t608 * t593
  t644 = -0.128e3 / 0.3e1 * t600 * t267 - 0.16e2 / 0.3e1 * t604 * t258 * t593 - 0.80e2 / 0.3e1 * t604 * t557 - 0.40e2 / 0.3e1 * t641 * t537
  t646 = t596 ** 2
  t647 = 0.1e1 / t646
  t648 = t611 * t647
  t651 = t629 * t597 + t644 * t613 - t618 * t622 - 0.2e1 * t631 * t622 - 0.3e1 * t648 * t622
  t654 = 0.1e1 / t229
  t659 = t227 ** 2
  t665 = t232 ** 2
  t679 = params.alpha_ab ** 2
  t680 = t621 ** 2
  t681 = t679 * t680
  t685 = 0.1e1 / t34 / t183
  t686 = t488 * t685
  t688 = t490 * t257
  t691 = params.alpha_ab * (0.176e3 / 0.9e1 * t686 + 0.160e3 / 0.9e1 * t688)
  t693 = t36 * t685
  t708 = t183 * t229
  t711 = t16 / t13 / t708
  t717 = t267 * tau0
  t742 = 0.1e1 / t13 / t168
  t743 = t11 * t742
  t754 = t364 ** 2
  t762 = t31 * t10 * t170
  t763 = 0.1e1 / t328 / t327 * t30 * t762
  t765 = t351 * t742
  t766 = t350 * t765
  t768 = t9 * t743
  t770 = t327 ** (-0.5e0)
  t772 = t770 * t30 * t762
  t774 = t358 * t765
  t776 = t10 * t170
  t777 = t32 * t776
  t783 = t346 ** 2
  t786 = t339 ** 2
  t801 = t396 ** 2
  t817 = t390 ** 2
  t820 = t381 ** 2
  t825 = t742 * t16
  t828 = 0.14764627977777777777777777777777777777777777777777e-2 * t12 * t825 * t47
  t833 = 0.35616666666666666666666666666666666666666666666666e-1 * t355 * t60 * t54 * t78 * t79
  t837 = t78 ** 2
  t840 = 0.20000000000000000000000000000000000000000000000000e1 * t52 / t53 / t42 * t837 * t79
  t846 = t776 * t36 * t38
  t847 = 0.1e1 / t25 / t24 * t30 * t31 * t846
  t849 = t743 * t60
  t850 = t58 * t849
  t853 = t12 * t825 * t20
  t855 = t24 ** (-0.5e0)
  t858 = t855 * t30 * t31 * t846
  t860 = t69 * t849
  t863 = t33 * t171 * t38
  t868 = 0.10000000000000000000000000000000000000000000000000e1 * t55 * (-0.42198333333333333333333333333333333333333333333333e0 * t847 + 0.84396666666666666666666666666666666666666666666666e0 * t850 + 0.39862222222222222222222222222222222222222222222223e0 * t853 + 0.68258333333333333333333333333333333333333333333333e-1 * t858 + 0.13651666666666666666666666666666666666666666666667e0 * t860 + 0.13692777777777777777777777777777777777777777777778e0 * t863) * t79
  t869 = t53 ** 2
  t872 = t45 ** 2
  t876 = 0.16081979498692535066756296899072713062105388428051e2 * t52 / t869 * t837 / t872
  t888 = t116 ** 2
  t902 = t109 ** 2
  t905 = t101 ** 2
  t917 = 0.1e1 / t136 / t125
  t919 = t143 ** 2
  t929 = -0.57538888888888888888888888888888888888888888888889e0 * t847 + 0.11507777777777777777777777777777777777777777777778e1 * t850 + 0.40256666666666666666666666666666666666666666666667e0 * t853 + 0.36677500000000000000000000000000000000000000000000e-1 * t858 + 0.73355000000000000000000000000000000000000000000000e-1 * t860 + 0.13797500000000000000000000000000000000000000000000e0 * t863
  t933 = t136 ** 2
  t934 = 0.1e1 / t933
  t936 = t128 ** 2
  t937 = 0.1e1 / t936
  t941 = -0.70983522622222222222222222222222222222222222222221e-3 * t12 * t825 * t103 - 0.34246666666666666666666666666666666666666666666666e-1 * t355 * t60 * t110 * t116 * t117 - 0.20000000000000000000000000000000000000000000000000e1 * t108 / t109 / t98 * t888 * t117 + 0.10000000000000000000000000000000000000000000000000e1 * t111 * (-0.78438333333333333333333333333333333333333333333333e0 * t847 + 0.15687666666666666666666666666666666666666666666667e1 * t850 + 0.68863333333333333333333333333333333333333333333333e0 * t853 + 0.14025833333333333333333333333333333333333333333333e0 * t858 + 0.28051666666666666666666666666666666666666666666667e0 * t860 + 0.17365833333333333333333333333333333333333333333333e0 * t863) * t117 + 0.32163958997385070133512593798145426124210776856102e2 * t108 / t902 * t888 / t905 + t828 + t833 + t840 - t868 - t876 - 0.24415263074675393406472461472505321282722606644045e-3 * t12 * t825 * t130 - 0.10843581300301739842632067522386578331157260943710e-1 * t355 * t60 * t157 - 0.11696447245269292414524477327518106963944910680856e1 * t135 * t917 * t919 * t144 + 0.58482236226346462072622386637590534819724553404280e0 * t138 * t929 * t144 + 0.17315859105681463759666483083807725165579399831905e2 * t135 * t934 * t919 * t937
  t962 = -t828 - t833 - t840 + t868 + t876 + t93 * t941 + 0.24415263074675393406472461472505321282722606644045e-3 * t150 * t743 * t151 + 0.10843581300301739842632067522386578331157260943710e-1 * t93 * t12 * t64 * t157 + 0.11696447245269292414524477327518106963944910680856e1 * t155 * t917 * t919 * t144 - 0.58482236226346462072622386637590534819724553404280e0 * t155 * t137 * t929 * t144 - 0.17315859105681463759666483083807725165579399831905e2 * t155 * t934 * t919 * t937
  t965 = f.my_piecewise3(t4, 0, t5 * t962 / 0.2e1)
  t967 = -0.14764627977777777777777777777777777777777777777777e-2 * t9 * t743 * t340 - 0.35616666666666666666666666666666666666666666666666e-1 * t12 * t15 * t347 * t366 - 0.20000000000000000000000000000000000000000000000000e1 * t345 / t346 / t336 * t754 * t365 + 0.10000000000000000000000000000000000000000000000000e1 * t348 * (-0.42198333333333333333333333333333333333333333333333e0 * t763 + 0.84396666666666666666666666666666666666666666666666e0 * t766 + 0.39862222222222222222222222222222222222222222222223e0 * t768 + 0.68258333333333333333333333333333333333333333333333e-1 * t772 + 0.13651666666666666666666666666666666666666666666667e0 * t774 + 0.13692777777777777777777777777777777777777777777778e0 * t777) * t365 + 0.16081979498692535066756296899072713062105388428051e2 * t345 / t783 * t754 / t786 + 0.24415263074675393406472461472505321282722606644045e-3 * t373 * t351 * t742 * t382 + 0.10843581300301739842632067522386578331157260943710e-1 * t372 * t9 * t59 * t399 + 0.11696447245269292414524477327518106963944910680856e1 * t389 / t390 / t378 * t801 * t398 - 0.58482236226346462072622386637590534819724553404280e0 * t389 * t391 * (-0.57538888888888888888888888888888888888888888888889e0 * t763 + 0.11507777777777777777777777777777777777777777777778e1 * t766 + 0.40256666666666666666666666666666666666666666666667e0 * t768 + 0.36677500000000000000000000000000000000000000000000e-1 * t772 + 0.73355000000000000000000000000000000000000000000000e-1 * t774 + 0.13797500000000000000000000000000000000000000000000e0 * t777) * t398 - 0.17315859105681463759666483083807725165579399831905e2 * t389 / t817 * t801 / t820 - 0.2e1 * t965
  t974 = t711 * t421
  t979 = t196 / t210
  t980 = t979 * t429
  t991 = 0.1e1 / t34 / t197 / t183
  t993 = t991 * t438 * t36
  t1004 = 0.1e1 / t13 / t197 / t708
  t1006 = t1004 * t480 * t16
  t1016 = t197 ** 2
  t1019 = t208 * t181 / t1016 / t168
  t1025 = 0.176e3 / 0.9e1 * t407 * t693 * t412 - 0.192e3 * t456 * t974 + 0.4096e4 / 0.9e1 * t405 * t426 * t980 + 0.2432e4 / 0.9e1 * t419 * t974 - 0.22016e5 / 0.9e1 * t462 * t980 + 0.8192e4 / 0.3e1 * t416 * t434 * t208 * t993 + 0.2304e4 * t427 * t980 - 0.30208e5 / 0.3e1 * t469 * t993 + 0.65536e5 / 0.3e1 * t425 * t476 * t295 * t1006 + 0.71680e5 / 0.9e1 * t436 * t993 - 0.204800e6 / 0.3e1 * t478 * t1006 + 0.1310720e7 / 0.9e1 * t433 * t434 * t417 * t1019 / t437 / t420
  t1031 = -t574 * s0 * t654 * t223 / 0.2e1 - 0.12800e5 / 0.9e1 * t310 * t226 * t659 * t36 / t34 / t197 / t665 * t237 + 0.2080e4 / 0.9e1 * t318 * t187 * t322 - t311 * t654 * t223 * t238 / 0.2e1 + t451 * (0.2e1 * t579 * t613 * t681 - t618 * t691 + (0.176e3 / 0.9e1 * t589 * t693 + 0.160e3 / 0.9e1 * t626 * t258) * t597 - 0.4e1 * t629 * t613 * t622 + 0.6e1 * t595 * t647 * t681 - 0.2e1 * t631 * t691 + (0.2432e4 / 0.9e1 * t600 * t711 + 0.176e3 / 0.9e1 * t604 * t693 * t593 + 0.640e3 / 0.3e1 * t604 * t717 + 0.1600e4 / 0.9e1 * t608 * t227 * t187 + 0.320e3 / 0.9e1 * t641 * t688) * t613 - 0.6e1 * t644 * t647 * t622 + 0.12e2 * t611 / t646 / t585 * t681 - 0.3e1 * t648 * t691) + 0.2e1 * t403 * t651 + t967 * t615 + 0.2e1 * t403 * t484 + t451 * t1025 + t967 * t442 + t307 * s0 * t314 / 0.2e1
  t1050 = t711 * t189
  t1054 = t979 * t201
  t1064 = t991 * t215 * t36
  t1074 = t1004 * t302 * t16
  t1088 = 0.88e2 / 0.9e1 * t167 * t693 * t175 - 0.48e2 * t263 * t1050 + 0.512e3 / 0.9e1 * t165 * t194 * t1054 + 0.608e3 / 0.9e1 * t182 * t1050 - 0.2752e4 / 0.9e1 * t273 * t1054 + 0.512e3 / 0.3e1 * t178 * t206 * t208 * t1064 + 0.288e3 * t195 * t1054 - 0.1888e4 / 0.3e1 * t283 * t1064 + 0.2048e4 / 0.3e1 * t193 * t293 * t295 * t1074 + 0.4480e4 / 0.9e1 * t209 * t1064 - 0.6400e4 / 0.3e1 * t296 * t1074 + 0.20480e5 / 0.9e1 * t205 * t206 * t179 * t1019 / t214 / t188
  t1099 = params.alpha_ss ** 2
  t1100 = t539 ** 2
  t1101 = t1099 * t1100
  t1107 = params.alpha_ss * (0.88e2 / 0.9e1 * t686 + 0.80e2 / 0.9e1 * t688)
  t1161 = t220 * s0 * t314 / 0.2e1 - 0.320e3 / 0.3e1 * t220 * t317 * t323 - 0.320e3 / 0.3e1 * t307 * t317 * t323 + 0.2e1 * t965 * t219 * t239 + 0.4e1 * t163 * t306 * t239 + 0.2e1 * t255 * t1088 * t239 + 0.2e1 * t965 * t530 * t226 + 0.4e1 * t163 * t570 * t226 + 0.2e1 * t255 * (0.2e1 * t487 * t528 * t1101 - t534 * t1107 + (0.88e2 / 0.9e1 * t506 * t693 + 0.80e2 / 0.9e1 * t544 * t258) * t513 - 0.4e1 * t547 * t528 * t540 + 0.6e1 * t511 * t566 * t1101 - 0.2e1 * t549 * t1107 + (0.608e3 / 0.9e1 * t516 * t711 + 0.88e2 / 0.9e1 * t520 * t693 * t509 + 0.160e3 / 0.3e1 * t520 * t717 + 0.400e3 / 0.9e1 * t523 * t227 * t187 + 0.160e3 / 0.9e1 * t560 * t688) * t528 - 0.6e1 * t563 * t566 * t540 + 0.12e2 * t526 / t565 / t502 * t1101 - 0.3e1 * t567 * t1107) * t226 - 0.40e2 / 0.3e1 * t310 * s0 * t266 * tau0 * t16 * t322 + t531 * t576 / 0.2e1 + t571 * t576 / 0.2e1
  v2rho2_0_ = 0.4e1 * t220 * t239 + 0.4e1 * t307 * t239 + t311 * t314 / 0.2e1 - 0.320e3 / 0.3e1 * t318 * t323 + 0.2e1 * t403 * t442 + 0.2e1 * t451 * t484 + 0.4e1 * t531 * t226 + 0.4e1 * t571 * t226 + t574 * t576 / 0.2e1 + 0.2e1 * t403 * t615 + 0.2e1 * t451 * t651 + r0 * (t1031 + t1161)
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  import jax
  d1 = jax.grad(_energy_unpol_sum, argnums=1)
  d2 = jax.jacfwd(d1, argnums=1)
  d3 = jax.jacfwd(lambda pp, rr, ss, ll=None, tt=None: d2(pp, rr, ss, ll, tt), argnums=1)
  v3rho3 = d3(p, r, s, l, tau)
  return {'v3rho3': v3rho3}

def unpol_lxc(p, r, s=None, l=None, tau=None):
  import jax
  d1 = jax.grad(_energy_unpol_sum, argnums=1)
  d2 = jax.jacfwd(d1, argnums=1)
  d3 = jax.jacfwd(lambda pp, rr, ss=None, ll=None, tt=None: d2(pp, rr, ss, ll, tt), argnums=1)
  d4 = jax.jacfwd(lambda pp, rr, ss=None, ll=None, tt=None: d3(pp, rr, ss, ll, tt), argnums=1)
  v4rho4 = d4(p, r, s, l, tau)
  return {'v4rho4': v4rho4}

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t10 = 0.1e1 / t8 / t7
  t11 = t6 * t10
  t12 = 0.1e1 / t8
  t14 = t4 * t6 * t12
  t15 = jnp.sqrt(t14)
  t18 = t14 ** 0.15e1
  t20 = t1 ** 2
  t21 = t3 ** 2
  t22 = t20 * t21
  t23 = t8 ** 2
  t24 = 0.1e1 / t23
  t26 = t22 * t5 * t24
  t28 = 0.37978500000000000000000000000000000000000000000000e1 * t15 + 0.89690000000000000000000000000000000000000000000000e0 * t14 + 0.20477500000000000000000000000000000000000000000000e0 * t18 + 0.12323500000000000000000000000000000000000000000000e0 * t26
  t31 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t28
  t32 = jnp.log(t31)
  t35 = 0.11073470983333333333333333333333333333333333333333e-2 * t4 * t11 * t32
  t37 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t14
  t38 = t28 ** 2
  t39 = 0.1e1 / t38
  t40 = t37 * t39
  t42 = 0.1e1 / t15 * t1
  t43 = t3 * t6
  t44 = t43 * t10
  t45 = t42 * t44
  t47 = t4 * t11
  t49 = t14 ** 0.5e0
  t50 = t49 * t1
  t51 = t50 * t44
  t54 = 0.1e1 / t23 / t7
  t56 = t22 * t5 * t54
  t58 = -0.63297500000000000000000000000000000000000000000000e0 * t45 - 0.29896666666666666666666666666666666666666666666667e0 * t47 - 0.10238750000000000000000000000000000000000000000000e0 * t51 - 0.82156666666666666666666666666666666666666666666667e-1 * t56
  t59 = 0.1e1 / t31
  t60 = t58 * t59
  t62 = 0.10000000000000000000000000000000000000000000000000e1 * t40 * t60
  t63 = r0 - r1
  t64 = t63 ** 2
  t65 = t64 * t63
  t66 = t7 ** 2
  t67 = t66 ** 2
  t68 = 0.1e1 / t67
  t69 = t65 * t68
  t70 = 0.1e1 / t7
  t71 = t63 * t70
  t72 = 0.1e1 + t71
  t73 = t72 <= f.p.zeta_threshold
  t74 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t75 = t74 * f.p.zeta_threshold
  t76 = t72 ** (0.1e1 / 0.3e1)
  t77 = t76 * t72
  t78 = f.my_piecewise3(t73, t75, t77)
  t79 = 0.1e1 - t71
  t80 = t79 <= f.p.zeta_threshold
  t81 = t79 ** (0.1e1 / 0.3e1)
  t82 = t81 * t79
  t83 = f.my_piecewise3(t80, t75, t82)
  t85 = 2 ** (0.1e1 / 0.3e1)
  t88 = 0.1e1 / (0.2e1 * t85 - 0.2e1)
  t89 = (t78 + t83 - 0.2e1) * t88
  t91 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t14
  t96 = 0.70594500000000000000000000000000000000000000000000e1 * t15 + 0.15494250000000000000000000000000000000000000000000e1 * t14 + 0.42077500000000000000000000000000000000000000000000e0 * t18 + 0.15629250000000000000000000000000000000000000000000e0 * t26
  t99 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t96
  t100 = jnp.log(t99)
  t104 = 0.621814e-1 * t37 * t32
  t106 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t14
  t111 = 0.51785000000000000000000000000000000000000000000000e1 * t15 + 0.90577500000000000000000000000000000000000000000000e0 * t14 + 0.11003250000000000000000000000000000000000000000000e0 * t18 + 0.12417750000000000000000000000000000000000000000000e0 * t26
  t114 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t111
  t115 = jnp.log(t114)
  t116 = t106 * t115
  t118 = -0.3109070e-1 * t91 * t100 + t104 - 0.19751673498613801407483339618206552048944131217655e-1 * t116
  t119 = t89 * t118
  t121 = 0.4e1 * t69 * t119
  t122 = t64 ** 2
  t124 = 0.1e1 / t67 / t7
  t125 = t122 * t124
  t127 = 0.4e1 * t125 * t119
  t128 = t122 * t68
  t129 = 0.1e1 / t66
  t130 = t63 * t129
  t131 = t70 - t130
  t134 = f.my_piecewise3(t73, 0, 0.4e1 / 0.3e1 * t76 * t131)
  t135 = -t131
  t138 = f.my_piecewise3(t80, 0, 0.4e1 / 0.3e1 * t81 * t135)
  t140 = (t134 + t138) * t88
  t141 = t140 * t118
  t146 = t96 ** 2
  t147 = 0.1e1 / t146
  t148 = t91 * t147
  t153 = -0.11765750000000000000000000000000000000000000000000e1 * t45 - 0.51647500000000000000000000000000000000000000000000e0 * t47 - 0.21038750000000000000000000000000000000000000000000e0 * t51 - 0.10419500000000000000000000000000000000000000000000e0 * t56
  t154 = 0.1e1 / t99
  t155 = t153 * t154
  t161 = t111 ** 2
  t162 = 0.1e1 / t161
  t163 = t106 * t162
  t168 = -0.86308333333333333333333333333333333333333333333334e0 * t45 - 0.30192500000000000000000000000000000000000000000000e0 * t47 - 0.55016250000000000000000000000000000000000000000000e-1 * t51 - 0.82785000000000000000000000000000000000000000000000e-1 * t56
  t169 = 0.1e1 / t114
  t170 = t168 * t169
  t173 = 0.53237641966666666666666666666666666666666666666666e-3 * t4 * t11 * t100 + 0.10000000000000000000000000000000000000000000000000e1 * t148 * t155 - t35 - t62 + 0.18311447306006545054854346104378990962041954983034e-3 * t4 * t11 * t115 + 0.58482236226346462072622386637590534819724553404280e0 * t163 * t170
  t174 = t89 * t173
  t175 = t128 * t174
  t178 = t89 * t1
  t180 = t43 * t10 * t115
  t182 = 0.18311447306006545054854346104378990962041954983034e-3 * t178 * t180
  t183 = t89 * t106
  t185 = t162 * t168 * t169
  t187 = 0.58482236226346462072622386637590534819724553404280e0 * t183 * t185
  t189 = r0 <= f.p.dens_threshold or t73
  t190 = f.my_piecewise3(t73, 0, t131)
  t191 = t4 * t6
  t192 = t12 * t85
  t193 = 0.1e1 / t74
  t195 = f.my_piecewise3(t73, t193, 0.1e1 / t76)
  t197 = t191 * t192 * t195
  t199 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t197
  t200 = jnp.sqrt(t197)
  t203 = t197 ** 0.15e1
  t205 = t22 * t5
  t206 = t85 ** 2
  t207 = t24 * t206
  t208 = t195 ** 2
  t210 = t205 * t207 * t208
  t212 = 0.37978500000000000000000000000000000000000000000000e1 * t200 + 0.89690000000000000000000000000000000000000000000000e0 * t197 + 0.20477500000000000000000000000000000000000000000000e0 * t203 + 0.12323500000000000000000000000000000000000000000000e0 * t210
  t215 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t212
  t216 = jnp.log(t215)
  t218 = 0.621814e-1 * t199 * t216
  t221 = f.my_piecewise3(0.2e1 <= f.p.zeta_threshold, t75, 0.2e1 * t85)
  t223 = f.my_piecewise3(0.0e0 <= f.p.zeta_threshold, t75, 0)
  t225 = (t221 + t223 - 0.2e1) * t88
  t227 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t197
  t232 = 0.70594500000000000000000000000000000000000000000000e1 * t200 + 0.15494250000000000000000000000000000000000000000000e1 * t197 + 0.42077500000000000000000000000000000000000000000000e0 * t203 + 0.15629250000000000000000000000000000000000000000000e0 * t210
  t235 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t232
  t236 = jnp.log(t235)
  t240 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t197
  t245 = 0.51785000000000000000000000000000000000000000000000e1 * t200 + 0.90577500000000000000000000000000000000000000000000e0 * t197 + 0.11003250000000000000000000000000000000000000000000e0 * t203 + 0.12417750000000000000000000000000000000000000000000e0 * t210
  t248 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t245
  t249 = jnp.log(t248)
  t250 = t240 * t249
  t256 = -t218 + t225 * (-0.3109070e-1 * t227 * t236 + t218 - 0.19751673498613801407483339618206552048944131217655e-1 * t250) + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t250
  t258 = f.my_piecewise3(t73, f.p.zeta_threshold, t72)
  t259 = t10 * t85
  t261 = t191 * t259 * t195
  t262 = 0.17808333333333333333333333333333333333333333333333e-1 * t261
  t263 = 0.1e1 / t77
  t266 = f.my_piecewise3(t73, 0, -t263 * t131 / 0.3e1)
  t268 = t191 * t192 * t266
  t270 = -t262 + 0.53425000000000000000000000000000000000000000000000e-1 * t268
  t272 = 0.621814e-1 * t270 * t216
  t273 = t212 ** 2
  t274 = 0.1e1 / t273
  t275 = t199 * t274
  t276 = 0.1e1 / t200
  t277 = t261 / 0.3e1
  t278 = -t277 + t268
  t279 = t276 * t278
  t281 = 0.29896666666666666666666666666666666666666666666667e0 * t261
  t283 = t197 ** 0.5e0
  t284 = t283 * t278
  t286 = t54 * t206
  t288 = t205 * t286 * t208
  t289 = 0.82156666666666666666666666666666666666666666666667e-1 * t288
  t290 = t195 * t266
  t292 = t205 * t207 * t290
  t294 = 0.18989250000000000000000000000000000000000000000000e1 * t279 - t281 + 0.89690000000000000000000000000000000000000000000000e0 * t268 + 0.30716250000000000000000000000000000000000000000000e0 * t284 - t289 + 0.24647000000000000000000000000000000000000000000000e0 * t292
  t295 = 0.1e1 / t215
  t296 = t294 * t295
  t298 = 0.10000000000000000000000000000000000000000000000000e1 * t275 * t296
  t299 = 0.17123333333333333333333333333333333333333333333333e-1 * t261
  t301 = -t299 + 0.51370000000000000000000000000000000000000000000000e-1 * t268
  t304 = t232 ** 2
  t305 = 0.1e1 / t304
  t306 = t227 * t305
  t308 = 0.51647500000000000000000000000000000000000000000000e0 * t261
  t311 = 0.10419500000000000000000000000000000000000000000000e0 * t288
  t313 = 0.35297250000000000000000000000000000000000000000000e1 * t279 - t308 + 0.15494250000000000000000000000000000000000000000000e1 * t268 + 0.63116250000000000000000000000000000000000000000000e0 * t284 - t311 + 0.31258500000000000000000000000000000000000000000000e0 * t292
  t314 = 0.1e1 / t235
  t315 = t313 * t314
  t318 = 0.92708333333333333333333333333333333333333333333333e-2 * t261
  t320 = -t318 + 0.27812500000000000000000000000000000000000000000000e-1 * t268
  t321 = t320 * t249
  t323 = t245 ** 2
  t324 = 0.1e1 / t323
  t325 = t240 * t324
  t327 = 0.30192500000000000000000000000000000000000000000000e0 * t261
  t330 = 0.82785000000000000000000000000000000000000000000000e-1 * t288
  t332 = 0.25892500000000000000000000000000000000000000000000e1 * t279 - t327 + 0.90577500000000000000000000000000000000000000000000e0 * t268 + 0.16504875000000000000000000000000000000000000000000e0 * t284 - t330 + 0.24835500000000000000000000000000000000000000000000e0 * t292
  t333 = 0.1e1 / t248
  t334 = t332 * t333
  t341 = t225 * t240
  t343 = t324 * t332 * t333
  t346 = -t272 + t298 + t225 * (-0.3109070e-1 * t301 * t236 + 0.10000000000000000000000000000000000000000000000000e1 * t306 * t315 + t272 - t298 - 0.19751673498613801407483339618206552048944131217655e-1 * t321 + 0.58482236226346462072622386637590534819724553404280e0 * t325 * t334) + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t321 - 0.58482236226346462072622386637590534819724553404280e0 * t341 * t343
  t350 = f.my_piecewise3(t189, 0, t190 * t256 / 0.2e1 + t258 * t346 / 0.2e1)
  t352 = r1 <= f.p.dens_threshold or t80
  t353 = f.my_piecewise3(t80, 0, t135)
  t355 = f.my_piecewise3(t80, t193, 0.1e1 / t81)
  t357 = t191 * t192 * t355
  t359 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t357
  t360 = jnp.sqrt(t357)
  t363 = t357 ** 0.15e1
  t365 = t355 ** 2
  t367 = t205 * t207 * t365
  t369 = 0.37978500000000000000000000000000000000000000000000e1 * t360 + 0.89690000000000000000000000000000000000000000000000e0 * t357 + 0.20477500000000000000000000000000000000000000000000e0 * t363 + 0.12323500000000000000000000000000000000000000000000e0 * t367
  t372 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t369
  t373 = jnp.log(t372)
  t375 = 0.621814e-1 * t359 * t373
  t377 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t357
  t382 = 0.70594500000000000000000000000000000000000000000000e1 * t360 + 0.15494250000000000000000000000000000000000000000000e1 * t357 + 0.42077500000000000000000000000000000000000000000000e0 * t363 + 0.15629250000000000000000000000000000000000000000000e0 * t367
  t385 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t382
  t386 = jnp.log(t385)
  t390 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t357
  t395 = 0.51785000000000000000000000000000000000000000000000e1 * t360 + 0.90577500000000000000000000000000000000000000000000e0 * t357 + 0.11003250000000000000000000000000000000000000000000e0 * t363 + 0.12417750000000000000000000000000000000000000000000e0 * t367
  t398 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t395
  t399 = jnp.log(t398)
  t400 = t390 * t399
  t406 = -t375 + t225 * (-0.3109070e-1 * t377 * t386 + t375 - 0.19751673498613801407483339618206552048944131217655e-1 * t400) + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t400
  t408 = f.my_piecewise3(t80, f.p.zeta_threshold, t79)
  t410 = t191 * t259 * t355
  t411 = 0.17808333333333333333333333333333333333333333333333e-1 * t410
  t412 = 0.1e1 / t82
  t415 = f.my_piecewise3(t80, 0, -t412 * t135 / 0.3e1)
  t417 = t191 * t192 * t415
  t419 = -t411 + 0.53425000000000000000000000000000000000000000000000e-1 * t417
  t421 = 0.621814e-1 * t419 * t373
  t422 = t369 ** 2
  t423 = 0.1e1 / t422
  t424 = t359 * t423
  t425 = 0.1e1 / t360
  t426 = t410 / 0.3e1
  t427 = -t426 + t417
  t428 = t425 * t427
  t430 = 0.29896666666666666666666666666666666666666666666667e0 * t410
  t432 = t357 ** 0.5e0
  t433 = t432 * t427
  t436 = t205 * t286 * t365
  t437 = 0.82156666666666666666666666666666666666666666666667e-1 * t436
  t438 = t355 * t415
  t440 = t205 * t207 * t438
  t442 = 0.18989250000000000000000000000000000000000000000000e1 * t428 - t430 + 0.89690000000000000000000000000000000000000000000000e0 * t417 + 0.30716250000000000000000000000000000000000000000000e0 * t433 - t437 + 0.24647000000000000000000000000000000000000000000000e0 * t440
  t443 = 0.1e1 / t372
  t444 = t442 * t443
  t446 = 0.10000000000000000000000000000000000000000000000000e1 * t424 * t444
  t447 = 0.17123333333333333333333333333333333333333333333333e-1 * t410
  t449 = -t447 + 0.51370000000000000000000000000000000000000000000000e-1 * t417
  t452 = t382 ** 2
  t453 = 0.1e1 / t452
  t454 = t377 * t453
  t456 = 0.51647500000000000000000000000000000000000000000000e0 * t410
  t459 = 0.10419500000000000000000000000000000000000000000000e0 * t436
  t461 = 0.35297250000000000000000000000000000000000000000000e1 * t428 - t456 + 0.15494250000000000000000000000000000000000000000000e1 * t417 + 0.63116250000000000000000000000000000000000000000000e0 * t433 - t459 + 0.31258500000000000000000000000000000000000000000000e0 * t440
  t462 = 0.1e1 / t385
  t463 = t461 * t462
  t466 = 0.92708333333333333333333333333333333333333333333333e-2 * t410
  t468 = -t466 + 0.27812500000000000000000000000000000000000000000000e-1 * t417
  t469 = t468 * t399
  t471 = t395 ** 2
  t472 = 0.1e1 / t471
  t473 = t390 * t472
  t475 = 0.30192500000000000000000000000000000000000000000000e0 * t410
  t478 = 0.82785000000000000000000000000000000000000000000000e-1 * t436
  t480 = 0.25892500000000000000000000000000000000000000000000e1 * t428 - t475 + 0.90577500000000000000000000000000000000000000000000e0 * t417 + 0.16504875000000000000000000000000000000000000000000e0 * t433 - t478 + 0.24835500000000000000000000000000000000000000000000e0 * t440
  t481 = 0.1e1 / t398
  t482 = t480 * t481
  t489 = t225 * t390
  t491 = t472 * t480 * t481
  t494 = -t421 + t446 + t225 * (-0.3109070e-1 * t449 * t386 + 0.10000000000000000000000000000000000000000000000000e1 * t454 * t463 + t421 - t446 - 0.19751673498613801407483339618206552048944131217655e-1 * t469 + 0.58482236226346462072622386637590534819724553404280e0 * t473 * t482) + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t469 - 0.58482236226346462072622386637590534819724553404280e0 * t489 * t491
  t498 = f.my_piecewise3(t352, 0, t353 * t406 / 0.2e1 + t408 * t494 / 0.2e1)
  t499 = t35 + t62 + t121 - t127 + t128 * t141 + t175 + 0.19751673498613801407483339618206552048944131217655e-1 * t140 * t116 - t182 - t187 - t350 - t498
  t501 = params.cab[1]
  t502 = t501 * params.gamma_ab
  t503 = r0 ** 2
  t504 = r0 ** (0.1e1 / 0.3e1)
  t505 = t504 ** 2
  t507 = 0.1e1 / t505 / t503
  t508 = s0 * t507
  t509 = r1 ** 2
  t510 = r1 ** (0.1e1 / 0.3e1)
  t511 = t510 ** 2
  t513 = 0.1e1 / t511 / t509
  t514 = s2 * t513
  t515 = t508 + t514
  t517 = params.gamma_ab * t515 + 0.1e1
  t518 = 0.1e1 / t517
  t521 = params.cab[2]
  t522 = params.gamma_ab ** 2
  t523 = t521 * t522
  t524 = t515 ** 2
  t525 = t517 ** 2
  t526 = 0.1e1 / t525
  t529 = params.cab[3]
  t530 = t522 * params.gamma_ab
  t531 = t529 * t530
  t532 = t524 * t515
  t534 = 0.1e1 / t525 / t517
  t537 = params.cab[4]
  t538 = t522 ** 2
  t539 = t537 * t538
  t540 = t524 ** 2
  t541 = t525 ** 2
  t542 = 0.1e1 / t541
  t545 = t502 * t515 * t518 + t523 * t524 * t526 + t531 * t532 * t534 + t539 * t540 * t542 + params.cab[0]
  t546 = t499 * t545
  t553 = f.my_piecewise3(t189, 0, t258 * t256 / 0.2e1)
  t556 = f.my_piecewise3(t352, 0, t408 * t406 / 0.2e1)
  t557 = -t104 + t128 * t119 + 0.19751673498613801407483339618206552048944131217655e-1 * t89 * t116 - t553 - t556
  t558 = t503 * r0
  t560 = 0.1e1 / t505 / t558
  t561 = s0 * t560
  t565 = t501 * t522
  t566 = t565 * t515
  t567 = t526 * s0
  t568 = t567 * t560
  t571 = t523 * t515
  t574 = t521 * t530
  t575 = t574 * t524
  t576 = t534 * s0
  t577 = t576 * t560
  t580 = t531 * t524
  t583 = t529 * t538
  t584 = t583 * t532
  t585 = t542 * s0
  t586 = t585 * t560
  t589 = t539 * t532
  t592 = t538 * params.gamma_ab
  t593 = t537 * t592
  t594 = t593 * t540
  t596 = 0.1e1 / t541 / t517
  t597 = t596 * s0
  t601 = -0.8e1 / 0.3e1 * t502 * t561 * t518 + 0.8e1 / 0.3e1 * t566 * t568 - 0.16e2 / 0.3e1 * t571 * t568 + 0.16e2 / 0.3e1 * t575 * t577 - 0.8e1 * t580 * t577 + 0.8e1 * t584 * t586 - 0.32e2 / 0.3e1 * t589 * t586 + 0.32e2 / 0.3e1 * t594 * t597 * t560
  t602 = t557 * t601
  t604 = params.dab[0]
  t608 = 0.2e1 * tau0 / t505 / r0
  t612 = 0.2e1 * tau1 / t511 / r1
  t613 = 6 ** (0.1e1 / 0.3e1)
  t614 = t613 ** 2
  t615 = jnp.pi ** 2
  t616 = t615 ** (0.1e1 / 0.3e1)
  t617 = t616 ** 2
  t618 = t614 * t617
  t619 = 0.6e1 / 0.5e1 * t618
  t622 = 0.1e1 + params.alpha_ab * (t508 + t514 + t608 + t612 - t619)
  t623 = t622 ** 2
  t624 = 0.1e1 / t623
  t625 = t604 * t624
  t627 = tau0 * t507
  t629 = -0.8e1 / 0.3e1 * t561 - 0.10e2 / 0.3e1 * t627
  t630 = params.alpha_ab * t629
  t632 = params.dab[1]
  t633 = t632 * s0
  t636 = params.dab[2]
  t637 = t636 * tau0
  t640 = -0.8e1 / 0.3e1 * t633 * t560 - 0.10e2 / 0.3e1 * t637 * t507
  t643 = t608 + t612 - t619
  t645 = t632 * t515 + t636 * t643
  t647 = 0.1e1 / t623 / t622
  t648 = t645 * t647
  t651 = params.dab[3]
  t652 = t651 * t515
  t655 = params.dab[4]
  t656 = t655 * s0
  t660 = t655 * t515
  t663 = params.dab[5]
  t664 = t663 * t643
  t667 = -0.16e2 / 0.3e1 * t652 * t561 - 0.8e1 / 0.3e1 * t656 * t560 * t643 - 0.10e2 / 0.3e1 * t660 * t627 - 0.20e2 / 0.3e1 * t664 * t627
  t671 = t643 ** 2
  t673 = t651 * t524 + t660 * t643 + t663 * t671
  t674 = t623 ** 2
  t675 = 0.1e1 / t674
  t676 = t673 * t675
  t679 = t640 * t624 - t625 * t630 - 0.2e1 * t648 * t630 - 0.3e1 * t676 * t630 + t667 * t647
  t680 = t557 * t679
  t682 = params.dss[0]
  t683 = 0.3e1 / 0.5e1 * t618
  t686 = 0.1e1 + params.alpha_ss * (t514 + t612 - t683)
  t689 = params.dss[1]
  t690 = t689 * s2
  t692 = params.dss[2]
  t693 = t612 - t683
  t695 = t690 * t513 + t692 * t693
  t696 = t686 ** 2
  t697 = 0.1e1 / t696
  t699 = params.dss[3]
  t700 = s2 ** 2
  t701 = t699 * t700
  t702 = t509 ** 2
  t705 = 0.1e1 / t510 / t702 / r1
  t707 = params.dss[4]
  t708 = t707 * s2
  t711 = params.dss[5]
  t712 = t693 ** 2
  t714 = t708 * t513 * t693 + t701 * t705 + t711 * t712
  t716 = 0.1e1 / t696 / t686
  t718 = t682 / t686 + t695 * t697 + t714 * t716
  t719 = t498 * t718
  t722 = 0.1e1 / tau1
  t725 = 0.1e1 - s2 / r1 * t722 / 0.8e1
  t726 = t719 * t725
  t732 = t604 / t622 + t645 * t624 + t673 * t647
  t733 = t499 * t732
  t735 = params.css[0]
  t736 = params.css[1]
  t737 = t736 * params.gamma_ss
  t740 = params.gamma_ss * s2 * t513 + 0.1e1
  t741 = 0.1e1 / t740
  t744 = params.css[2]
  t745 = params.gamma_ss ** 2
  t746 = t744 * t745
  t748 = t740 ** 2
  t749 = 0.1e1 / t748
  t752 = params.css[3]
  t753 = t745 * params.gamma_ss
  t754 = t752 * t753
  t755 = t700 * s2
  t756 = t702 ** 2
  t760 = 0.1e1 / t748 / t740
  t763 = params.css[4]
  t764 = t745 ** 2
  t765 = t763 * t764
  t766 = t700 ** 2
  t767 = t756 * t509
  t771 = t748 ** 2
  t772 = 0.1e1 / t771
  t775 = t735 + t737 * t514 * t741 + t746 * t700 * t705 * t749 + t754 * t755 / t756 * t760 + t765 * t766 / t511 / t767 * t772
  t776 = t498 * t775
  t777 = tau1 ** 2
  t778 = t509 * r1
  t782 = params.Fermi_D_cnst ** 2
  t783 = 0.1e1 / t782
  t786 = jnp.exp(-0.4e1 * t777 / t510 / t778 * t783)
  t787 = 0.1e1 - t786
  t788 = t725 * t787
  t789 = t776 * t788
  t793 = params.gamma_ss * s0 * t507 + 0.1e1
  t794 = 0.1e1 / t793
  t798 = t736 * t745
  t799 = s0 ** 2
  t800 = t503 ** 2
  t801 = t800 * t503
  t803 = 0.1e1 / t504 / t801
  t805 = t793 ** 2
  t806 = 0.1e1 / t805
  t807 = t799 * t803 * t806
  t812 = t744 * t753
  t813 = t799 * s0
  t814 = t800 ** 2
  t819 = 0.1e1 / t805 / t793
  t820 = t813 / t814 / r0 * t819
  t825 = t752 * t764
  t826 = t799 ** 2
  t831 = t805 ** 2
  t832 = 0.1e1 / t831
  t833 = t826 / t505 / t814 / t558 * t832
  t838 = t764 * params.gamma_ss
  t839 = t763 * t838
  t840 = t826 * s0
  t846 = 0.1e1 / t831 / t793
  t850 = -0.8e1 / 0.3e1 * t737 * t561 * t794 + 0.8e1 / 0.3e1 * t798 * t807 - 0.16e2 / 0.3e1 * t746 * t807 + 0.16e2 / 0.3e1 * t812 * t820 - 0.8e1 * t754 * t820 + 0.8e1 * t825 * t833 - 0.32e2 / 0.3e1 * t765 * t833 + 0.32e2 / 0.3e1 * t839 * t840 / t504 / t814 / t801 * t846
  t851 = t553 * t850
  t854 = 0.1e1 / tau0
  t857 = 0.1e1 - s0 / r0 * t854 / 0.8e1
  t858 = tau0 ** 2
  t864 = jnp.exp(-0.4e1 * t858 / t504 / t558 * t783)
  t865 = 0.1e1 - t864
  t866 = t857 * t865
  t867 = t851 * t866
  t873 = 0.1e1 / t504 / t800 / r0
  t881 = t814 * t503
  t887 = t735 + t737 * t508 * t794 + t746 * t799 * t873 * t806 + t754 * t813 / t814 * t819 + t765 * t826 / t505 / t881 * t832
  t888 = t350 * t887
  t889 = t888 * t866
  t895 = t783 * t864
  t896 = t858 / t504 / t800 * t895
  t899 = t553 * t887
  t900 = t899 * t857
  t905 = t899 * s0
  t906 = t803 * tau0
  t913 = t858 ** 2
  t917 = t782 ** 2
  t918 = 0.1e1 / t917
  t924 = 0.1e1 / t503
  t926 = t924 * t854 * t865
  t929 = 0.1e1 / t558
  t938 = 0.1e1 / t66 / t7
  t939 = t63 * t938
  t941 = -0.2e1 * t129 + 0.2e1 * t939
  t942 = f.my_piecewise3(t73, 0, t941)
  t947 = 0.1e1 / t8 / t66
  t948 = t947 * t85
  t950 = t191 * t948 * t195
  t951 = 0.23744444444444444444444444444444444444444444444444e-1 * t950
  t953 = t191 * t259 * t266
  t955 = t72 ** 2
  t957 = 0.1e1 / t76 / t955
  t958 = t131 ** 2
  t964 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t957 * t958 - t263 * t941 / 0.3e1)
  t966 = t191 * t192 * t964
  t970 = 0.621814e-1 * (t951 - 0.35616666666666666666666666666666666666666666666666e-1 * t953 + 0.53425000000000000000000000000000000000000000000000e-1 * t966) * t216
  t971 = t270 * t274
  t973 = 0.20000000000000000000000000000000000000000000000000e1 * t971 * t296
  t976 = t199 / t273 / t212
  t977 = t294 ** 2
  t980 = 0.20000000000000000000000000000000000000000000000000e1 * t976 * t977 * t295
  t982 = 0.1e1 / t200 / t197
  t983 = t278 ** 2
  t984 = t982 * t983
  t986 = 0.4e1 / 0.9e1 * t950
  t988 = t986 - 0.2e1 / 0.3e1 * t953 + t966
  t989 = t276 * t988
  t991 = 0.39862222222222222222222222222222222222222222222223e0 * t950
  t994 = t197 ** (-0.5e0)
  t995 = t994 * t983
  t997 = t283 * t988
  t1000 = 0.1e1 / t23 / t66
  t1001 = t1000 * t206
  t1003 = t205 * t1001 * t208
  t1004 = 0.13692777777777777777777777777777777777777777777778e0 * t1003
  t1006 = t205 * t286 * t290
  t1008 = t266 ** 2
  t1010 = t205 * t207 * t1008
  t1014 = t205 * t207 * t195 * t964
  t1016 = -0.94946250000000000000000000000000000000000000000000e0 * t984 + 0.18989250000000000000000000000000000000000000000000e1 * t989 + t991 - 0.59793333333333333333333333333333333333333333333334e0 * t953 + 0.89690000000000000000000000000000000000000000000000e0 * t966 + 0.15358125000000000000000000000000000000000000000000e0 * t995 + 0.30716250000000000000000000000000000000000000000000e0 * t997 + t1004 - 0.32862666666666666666666666666666666666666666666666e0 * t1006 + 0.24647000000000000000000000000000000000000000000000e0 * t1010 + 0.24647000000000000000000000000000000000000000000000e0 * t1014
  t1019 = 0.10000000000000000000000000000000000000000000000000e1 * t275 * t1016 * t295
  t1020 = t273 ** 2
  t1022 = t199 / t1020
  t1023 = t215 ** 2
  t1024 = 0.1e1 / t1023
  t1027 = 0.16081979498692535066756296899072713062105388428051e2 * t1022 * t977 * t1024
  t1028 = 0.22831111111111111111111111111111111111111111111111e-1 * t950
  t1034 = t301 * t305
  t1039 = t227 / t304 / t232
  t1040 = t313 ** 2
  t1046 = 0.68863333333333333333333333333333333333333333333333e0 * t950
  t1051 = 0.17365833333333333333333333333333333333333333333333e0 * t1003
  t1055 = -0.17648625000000000000000000000000000000000000000000e1 * t984 + 0.35297250000000000000000000000000000000000000000000e1 * t989 + t1046 - 0.10329500000000000000000000000000000000000000000000e1 * t953 + 0.15494250000000000000000000000000000000000000000000e1 * t966 + 0.31558125000000000000000000000000000000000000000000e0 * t995 + 0.63116250000000000000000000000000000000000000000000e0 * t997 + t1051 - 0.41678000000000000000000000000000000000000000000000e0 * t1006 + 0.31258500000000000000000000000000000000000000000000e0 * t1010 + 0.31258500000000000000000000000000000000000000000000e0 * t1014
  t1059 = t304 ** 2
  t1061 = t227 / t1059
  t1062 = t235 ** 2
  t1063 = 0.1e1 / t1062
  t1067 = 0.12361111111111111111111111111111111111111111111111e-1 * t950
  t1071 = (t1067 - 0.18541666666666666666666666666666666666666666666667e-1 * t953 + 0.27812500000000000000000000000000000000000000000000e-1 * t966) * t249
  t1073 = t320 * t324
  t1077 = 0.1e1 / t323 / t245
  t1078 = t240 * t1077
  t1079 = t332 ** 2
  t1085 = 0.40256666666666666666666666666666666666666666666667e0 * t950
  t1090 = 0.13797500000000000000000000000000000000000000000000e0 * t1003
  t1094 = -0.12946250000000000000000000000000000000000000000000e1 * t984 + 0.25892500000000000000000000000000000000000000000000e1 * t989 + t1085 - 0.60385000000000000000000000000000000000000000000000e0 * t953 + 0.90577500000000000000000000000000000000000000000000e0 * t966 + 0.82524375000000000000000000000000000000000000000000e-1 * t995 + 0.16504875000000000000000000000000000000000000000000e0 * t997 + t1090 - 0.33114000000000000000000000000000000000000000000000e0 * t1006 + 0.24835500000000000000000000000000000000000000000000e0 * t1010 + 0.24835500000000000000000000000000000000000000000000e0 * t1014
  t1098 = t323 ** 2
  t1099 = 0.1e1 / t1098
  t1100 = t240 * t1099
  t1101 = t248 ** 2
  t1102 = 0.1e1 / t1101
  t1106 = -0.3109070e-1 * (t1028 - 0.34246666666666666666666666666666666666666666666666e-1 * t953 + 0.51370000000000000000000000000000000000000000000000e-1 * t966) * t236 + 0.20000000000000000000000000000000000000000000000000e1 * t1034 * t315 - 0.20000000000000000000000000000000000000000000000000e1 * t1039 * t1040 * t314 + 0.10000000000000000000000000000000000000000000000000e1 * t306 * t1055 * t314 + 0.32163958997385070133512593798145426124210776856102e2 * t1061 * t1040 * t1063 + t970 - t973 + t980 - t1019 - t1027 - 0.19751673498613801407483339618206552048944131217655e-1 * t1071 + 0.11696447245269292414524477327518106963944910680856e1 * t1073 * t334 - 0.11696447245269292414524477327518106963944910680856e1 * t1078 * t1079 * t333 + 0.58482236226346462072622386637590534819724553404280e0 * t325 * t1094 * t333 + 0.17315859105681463759666483083807725165579399831905e2 * t1100 * t1079 * t1102
  t1110 = t225 * t320
  t1125 = -t970 + t973 - t980 + t1019 + t1027 + t225 * t1106 + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t1071 - 0.11696447245269292414524477327518106963944910680856e1 * t1110 * t343 + 0.11696447245269292414524477327518106963944910680856e1 * t341 * t1077 * t1079 * t333 - 0.58482236226346462072622386637590534819724553404280e0 * t341 * t324 * t1094 * t333 - 0.17315859105681463759666483083807725165579399831905e2 * t341 * t1099 * t1079 * t1102
  t1129 = f.my_piecewise3(t189, 0, t942 * t256 / 0.2e1 + t190 * t346 + t258 * t1125 / 0.2e1)
  t1135 = 0.35616666666666666666666666666666666666666666666666e-1 * t191 * t10 * t39 * t60
  t1139 = 0.24415263074675393406472461472505321282722606644045e-3 * t178 * t43 * t947 * t115
  t1141 = t140 * t1 * t180
  t1143 = t161 ** 2
  t1144 = 0.1e1 / t1143
  t1145 = t168 ** 2
  t1147 = t114 ** 2
  t1148 = 0.1e1 / t1147
  t1151 = 0.17315859105681463759666483083807725165579399831905e2 * t183 * t1144 * t1145 * t1148
  t1153 = t140 * t106 * t185
  t1156 = 0.1e1 / t161 / t111
  t1160 = 0.11696447245269292414524477327518106963944910680856e1 * t183 * t1156 * t1145 * t169
  t1165 = t21 * t5 * t1000
  t1166 = 0.1e1 / t15 / t14 * t20 * t1165
  t1168 = t43 * t947
  t1169 = t42 * t1168
  t1171 = t6 * t947
  t1172 = t4 * t1171
  t1174 = t14 ** (-0.5e0)
  t1176 = t1174 * t20 * t1165
  t1178 = t50 * t1168
  t1181 = t22 * t5 * t1000
  t1183 = -0.57538888888888888888888888888888888888888888888889e0 * t1166 + 0.11507777777777777777777777777777777777777777777778e1 * t1169 + 0.40256666666666666666666666666666666666666666666667e0 * t1172 + 0.36677500000000000000000000000000000000000000000000e-1 * t1176 + 0.73355000000000000000000000000000000000000000000000e-1 * t1178 + 0.13797500000000000000000000000000000000000000000000e0 * t1181
  t1187 = 0.58482236226346462072622386637590534819724553404280e0 * t183 * t162 * t1183 * t169
  t1191 = t58 ** 2
  t1194 = 0.20000000000000000000000000000000000000000000000000e1 * t37 / t38 / t28 * t1191 * t59
  t1204 = 0.10000000000000000000000000000000000000000000000000e1 * t40 * (-0.42198333333333333333333333333333333333333333333333e0 * t1166 + 0.84396666666666666666666666666666666666666666666666e0 * t1169 + 0.39862222222222222222222222222222222222222222222223e0 * t1172 + 0.68258333333333333333333333333333333333333333333333e-1 * t1176 + 0.13651666666666666666666666666666666666666666666667e0 * t1178 + 0.13692777777777777777777777777777777777777777777778e0 * t1181) * t59
  t1205 = -t941
  t1206 = f.my_piecewise3(t80, 0, t1205)
  t1211 = t191 * t948 * t355
  t1212 = 0.23744444444444444444444444444444444444444444444444e-1 * t1211
  t1214 = t191 * t259 * t415
  t1216 = t79 ** 2
  t1218 = 0.1e1 / t81 / t1216
  t1219 = t135 ** 2
  t1225 = f.my_piecewise3(t80, 0, 0.4e1 / 0.9e1 * t1218 * t1219 - t412 * t1205 / 0.3e1)
  t1227 = t191 * t192 * t1225
  t1231 = 0.621814e-1 * (t1212 - 0.35616666666666666666666666666666666666666666666666e-1 * t1214 + 0.53425000000000000000000000000000000000000000000000e-1 * t1227) * t373
  t1232 = t419 * t423
  t1234 = 0.20000000000000000000000000000000000000000000000000e1 * t1232 * t444
  t1237 = t359 / t422 / t369
  t1238 = t442 ** 2
  t1241 = 0.20000000000000000000000000000000000000000000000000e1 * t1237 * t1238 * t443
  t1243 = 0.1e1 / t360 / t357
  t1244 = t427 ** 2
  t1245 = t1243 * t1244
  t1247 = 0.4e1 / 0.9e1 * t1211
  t1249 = t1247 - 0.2e1 / 0.3e1 * t1214 + t1227
  t1250 = t425 * t1249
  t1252 = 0.39862222222222222222222222222222222222222222222223e0 * t1211
  t1255 = t357 ** (-0.5e0)
  t1256 = t1255 * t1244
  t1258 = t432 * t1249
  t1261 = t205 * t1001 * t365
  t1262 = 0.13692777777777777777777777777777777777777777777778e0 * t1261
  t1264 = t205 * t286 * t438
  t1266 = t415 ** 2
  t1268 = t205 * t207 * t1266
  t1272 = t205 * t207 * t355 * t1225
  t1274 = -0.94946250000000000000000000000000000000000000000000e0 * t1245 + 0.18989250000000000000000000000000000000000000000000e1 * t1250 + t1252 - 0.59793333333333333333333333333333333333333333333334e0 * t1214 + 0.89690000000000000000000000000000000000000000000000e0 * t1227 + 0.15358125000000000000000000000000000000000000000000e0 * t1256 + 0.30716250000000000000000000000000000000000000000000e0 * t1258 + t1262 - 0.32862666666666666666666666666666666666666666666666e0 * t1264 + 0.24647000000000000000000000000000000000000000000000e0 * t1268 + 0.24647000000000000000000000000000000000000000000000e0 * t1272
  t1277 = 0.10000000000000000000000000000000000000000000000000e1 * t424 * t1274 * t443
  t1278 = t422 ** 2
  t1280 = t359 / t1278
  t1281 = t372 ** 2
  t1282 = 0.1e1 / t1281
  t1285 = 0.16081979498692535066756296899072713062105388428051e2 * t1280 * t1238 * t1282
  t1286 = 0.22831111111111111111111111111111111111111111111111e-1 * t1211
  t1292 = t449 * t453
  t1297 = t377 / t452 / t382
  t1298 = t461 ** 2
  t1304 = 0.68863333333333333333333333333333333333333333333333e0 * t1211
  t1309 = 0.17365833333333333333333333333333333333333333333333e0 * t1261
  t1313 = -0.17648625000000000000000000000000000000000000000000e1 * t1245 + 0.35297250000000000000000000000000000000000000000000e1 * t1250 + t1304 - 0.10329500000000000000000000000000000000000000000000e1 * t1214 + 0.15494250000000000000000000000000000000000000000000e1 * t1227 + 0.31558125000000000000000000000000000000000000000000e0 * t1256 + 0.63116250000000000000000000000000000000000000000000e0 * t1258 + t1309 - 0.41678000000000000000000000000000000000000000000000e0 * t1264 + 0.31258500000000000000000000000000000000000000000000e0 * t1268 + 0.31258500000000000000000000000000000000000000000000e0 * t1272
  t1317 = t452 ** 2
  t1319 = t377 / t1317
  t1320 = t385 ** 2
  t1321 = 0.1e1 / t1320
  t1325 = 0.12361111111111111111111111111111111111111111111111e-1 * t1211
  t1329 = (t1325 - 0.18541666666666666666666666666666666666666666666667e-1 * t1214 + 0.27812500000000000000000000000000000000000000000000e-1 * t1227) * t399
  t1331 = t468 * t472
  t1335 = 0.1e1 / t471 / t395
  t1336 = t390 * t1335
  t1337 = t480 ** 2
  t1343 = 0.40256666666666666666666666666666666666666666666667e0 * t1211
  t1348 = 0.13797500000000000000000000000000000000000000000000e0 * t1261
  t1352 = -0.12946250000000000000000000000000000000000000000000e1 * t1245 + 0.25892500000000000000000000000000000000000000000000e1 * t1250 + t1343 - 0.60385000000000000000000000000000000000000000000000e0 * t1214 + 0.90577500000000000000000000000000000000000000000000e0 * t1227 + 0.82524375000000000000000000000000000000000000000000e-1 * t1256 + 0.16504875000000000000000000000000000000000000000000e0 * t1258 + t1348 - 0.33114000000000000000000000000000000000000000000000e0 * t1264 + 0.24835500000000000000000000000000000000000000000000e0 * t1268 + 0.24835500000000000000000000000000000000000000000000e0 * t1272
  t1356 = t471 ** 2
  t1357 = 0.1e1 / t1356
  t1358 = t390 * t1357
  t1359 = t398 ** 2
  t1360 = 0.1e1 / t1359
  t1364 = -0.3109070e-1 * (t1286 - 0.34246666666666666666666666666666666666666666666666e-1 * t1214 + 0.51370000000000000000000000000000000000000000000000e-1 * t1227) * t386 + 0.20000000000000000000000000000000000000000000000000e1 * t1292 * t463 - 0.20000000000000000000000000000000000000000000000000e1 * t1297 * t1298 * t462 + 0.10000000000000000000000000000000000000000000000000e1 * t454 * t1313 * t462 + 0.32163958997385070133512593798145426124210776856102e2 * t1319 * t1298 * t1321 + t1231 - t1234 + t1241 - t1277 - t1285 - 0.19751673498613801407483339618206552048944131217655e-1 * t1329 + 0.11696447245269292414524477327518106963944910680856e1 * t1331 * t482 - 0.11696447245269292414524477327518106963944910680856e1 * t1336 * t1337 * t481 + 0.58482236226346462072622386637590534819724553404280e0 * t473 * t1352 * t481 + 0.17315859105681463759666483083807725165579399831905e2 * t1358 * t1337 * t1360
  t1368 = t225 * t468
  t1383 = -t1231 + t1234 - t1241 + t1277 + t1285 + t225 * t1364 + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t1329 - 0.11696447245269292414524477327518106963944910680856e1 * t1368 * t491 + 0.11696447245269292414524477327518106963944910680856e1 * t489 * t1335 * t1337 * t481 - 0.58482236226346462072622386637590534819724553404280e0 * t489 * t472 * t1352 * t481 - 0.17315859105681463759666483083807725165579399831905e2 * t489 * t1357 * t1337 * t1360
  t1387 = f.my_piecewise3(t352, 0, t1206 * t406 / 0.2e1 + t353 * t494 + t408 * t1383 / 0.2e1)
  t1388 = t76 ** 2
  t1389 = 0.1e1 / t1388
  t1395 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t1389 * t958 + 0.4e1 / 0.3e1 * t76 * t941)
  t1396 = t81 ** 2
  t1397 = 0.1e1 / t1396
  t1403 = f.my_piecewise3(t80, 0, 0.4e1 / 0.9e1 * t1397 * t1219 + 0.4e1 / 0.3e1 * t81 * t1205)
  t1405 = (t1395 + t1403) * t88
  t1408 = -t1129 - t1135 + t1139 - 0.36622894612013090109708692208757981924083909966068e-3 * t1141 - t1151 - 0.11696447245269292414524477327518106963944910680856e1 * t1153 + t1160 - t1187 - t1194 + t1204 - t1387 + 0.19751673498613801407483339618206552048944131217655e-1 * t1405 * t116
  t1410 = t128 * t140 * t173
  t1412 = t125 * t141
  t1414 = t38 ** 2
  t1417 = t31 ** 2
  t1421 = 0.16081979498692535066756296899072713062105388428051e2 * t37 / t1414 * t1191 / t1417
  t1423 = 0.8e1 * t125 * t174
  t1434 = t153 ** 2
  t1448 = t146 ** 2
  t1451 = t99 ** 2
  t1458 = 0.14764627977777777777777777777777777777777777777777e-2 * t4 * t1171 * t32
  t1477 = -0.70983522622222222222222222222222222222222222222221e-3 * t4 * t1171 * t100 - 0.34246666666666666666666666666666666666666666666666e-1 * t191 * t10 * t147 * t155 - 0.20000000000000000000000000000000000000000000000000e1 * t91 / t146 / t96 * t1434 * t154 + 0.10000000000000000000000000000000000000000000000000e1 * t148 * (-0.78438333333333333333333333333333333333333333333333e0 * t1166 + 0.15687666666666666666666666666666666666666666666667e1 * t1169 + 0.68863333333333333333333333333333333333333333333333e0 * t1172 + 0.14025833333333333333333333333333333333333333333333e0 * t1176 + 0.28051666666666666666666666666666666666666666666667e0 * t1178 + 0.17365833333333333333333333333333333333333333333333e0 * t1181) * t154 + 0.32163958997385070133512593798145426124210776856102e2 * t91 / t1448 * t1434 / t1451 + t1458 + t1135 + t1194 - t1204 - t1421 - 0.24415263074675393406472461472505321282722606644045e-3 * t4 * t1171 * t115 - 0.10843581300301739842632067522386578331157260943710e-1 * t191 * t10 * t162 * t170 - 0.11696447245269292414524477327518106963944910680856e1 * t106 * t1156 * t1145 * t169 + 0.58482236226346462072622386637590534819724553404280e0 * t163 * t1183 * t169 + 0.17315859105681463759666483083807725165579399831905e2 * t106 * t1144 * t1145 * t1148
  t1479 = t128 * t89 * t1477
  t1483 = 0.10843581300301739842632067522386578331157260943710e-1 * t89 * t4 * t11 * t185
  t1488 = 0.20e2 * t122 / t67 / t66 * t119
  t1489 = t69 * t141
  t1492 = 0.8e1 * t69 * t174
  t1495 = 0.12e2 * t64 * t68 * t119
  t1498 = 0.32e2 * t65 * t124 * t119
  t1501 = t128 * t1405 * t118 + 0.2e1 * t1410 - 0.8e1 * t1412 + t1421 - t1423 - t1458 + t1479 + t1483 + t1488 + 0.8e1 * t1489 + t1492 + t1495 - t1498
  t1502 = t1408 + t1501
  t1506 = t604 * t647
  t1507 = params.alpha_ab ** 2
  t1508 = t629 ** 2
  t1509 = t1507 * t1508
  t1513 = 0.1e1 / t505 / t800
  t1514 = s0 * t1513
  t1516 = tau0 * t560
  t1518 = 0.88e2 / 0.9e1 * t1514 + 0.80e2 / 0.9e1 * t1516
  t1519 = params.alpha_ab * t1518
  t1527 = t640 * t647
  t1530 = t645 * t675
  t1536 = t800 * t558
  t1538 = 0.1e1 / t504 / t1536
  t1557 = t667 * t675
  t1562 = t673 / t674 / t622
  t1569 = -0.80e2 / 0.3e1 * t888 * t857 * t896 + 0.520e3 / 0.9e1 * t900 * t858 * t873 * t895 - 0.10e2 / 0.3e1 * t905 * t906 * t895 - 0.80e2 / 0.3e1 * t851 * t857 * t896 - 0.1600e4 / 0.9e1 * t900 * t913 / t505 / t814 * t918 * t864 + t888 * s0 * t926 / 0.4e1 - t905 * t929 * t854 * t865 / 0.4e1 + t851 * s0 * t926 / 0.4e1 + t1129 * t887 * t866 + t1502 * t732 + 0.2e1 * t499 * t679 + t557 * (0.2e1 * t1506 * t1509 - t625 * t1519 + (0.88e2 / 0.9e1 * t633 * t1513 + 0.80e2 / 0.9e1 * t637 * t560) * t624 - 0.4e1 * t1527 * t630 + 0.6e1 * t1530 * t1509 - 0.2e1 * t648 * t1519 + (0.128e3 / 0.9e1 * t651 * t799 * t1538 + 0.176e3 / 0.9e1 * t652 * t1514 + 0.88e2 / 0.9e1 * t656 * t1513 * t643 + 0.160e3 / 0.9e1 * t656 * t906 + 0.80e2 / 0.9e1 * t660 * t1516 + 0.200e3 / 0.9e1 * t663 * t858 * t873 + 0.160e3 / 0.9e1 * t664 * t1516) * t647 - 0.6e1 * t1557 * t630 + 0.12e2 * t1562 * t1509 - 0.3e1 * t676 * t1519)
  t1572 = 0.1e1 + params.alpha_ss * (t508 + t608 - t683)
  t1575 = t689 * s0
  t1577 = t608 - t683
  t1579 = t1575 * t507 + t692 * t1577
  t1580 = t1572 ** 2
  t1581 = 0.1e1 / t1580
  t1583 = t699 * t799
  t1585 = t707 * s0
  t1588 = t1577 ** 2
  t1590 = t1585 * t507 * t1577 + t1583 * t873 + t711 * t1588
  t1592 = 0.1e1 / t1580 / t1572
  t1594 = t682 / t1572 + t1579 * t1581 + t1590 * t1592
  t1595 = t350 * t1594
  t1597 = s0 * t924 * t854
  t1600 = t682 * t1581
  t1601 = params.alpha_ss * t629
  t1605 = t692 * tau0
  t1608 = -0.8e1 / 0.3e1 * t1575 * t560 - 0.10e2 / 0.3e1 * t1605 * t507
  t1610 = t1579 * t1592
  t1621 = t711 * t1577
  t1624 = -0.16e2 / 0.3e1 * t1583 * t803 - 0.8e1 / 0.3e1 * t1585 * t560 * t1577 - 0.10e2 / 0.3e1 * t1585 * t873 * tau0 - 0.20e2 / 0.3e1 * t1621 * t627
  t1626 = t1580 ** 2
  t1627 = 0.1e1 / t1626
  t1628 = t1590 * t1627
  t1631 = t1608 * t1581 + t1624 * t1592 - t1600 * t1601 - 0.2e1 * t1610 * t1601 - 0.3e1 * t1628 * t1601
  t1632 = t553 * t1631
  t1635 = t553 * t1594
  t1646 = t799 * t1538
  t1647 = t1646 * t806
  t1650 = t736 * t753
  t1653 = t813 / t881 * t819
  t1660 = t744 * t764
  t1665 = t826 / t505 / t814 / t800 * t832
  t1672 = t752 * t838
  t1677 = t840 / t504 / t814 / t1536 * t846
  t1685 = t763 * t764 * t745
  t1687 = t814 ** 2
  t1696 = 0.88e2 / 0.9e1 * t737 * t1514 * t794 - 0.24e2 * t798 * t1647 + 0.128e3 / 0.9e1 * t1650 * t1653 + 0.304e3 / 0.9e1 * t746 * t1647 - 0.688e3 / 0.9e1 * t812 * t1653 + 0.128e3 / 0.3e1 * t1660 * t1665 + 0.72e2 * t754 * t1653 - 0.472e3 / 0.3e1 * t825 * t1665 + 0.256e3 / 0.3e1 * t1672 * t1677 + 0.1120e4 / 0.9e1 * t765 * t1665 - 0.800e3 / 0.3e1 * t839 * t1677 + 0.1280e4 / 0.9e1 * t1685 * t826 * t799 / t1687 / t503 / t831 / t805
  t1706 = t1646 * t526
  t1709 = t501 * t530
  t1710 = t1709 * t515
  t1712 = t534 * t799 * t1538
  t1715 = t567 * t1513
  t1720 = t574 * t515
  t1725 = t521 * t538
  t1726 = t1725 * t524
  t1728 = t542 * t799 * t1538
  t1731 = t576 * t1513
  t1734 = t531 * t515
  t1737 = t583 * t524
  t1742 = t529 * t592
  t1743 = t1742 * t532
  t1745 = t596 * t799 * t1538
  t1748 = t585 * t1513
  t1751 = t539 * t524
  t1754 = t593 * t532
  t1760 = t537 * t538 * t522
  t1761 = t1760 * t540
  t1763 = 0.1e1 / t541 / t525
  t1771 = 0.88e2 / 0.9e1 * t502 * t1514 * t518 - 0.128e3 / 0.9e1 * t565 * t1706 + 0.128e3 / 0.9e1 * t1710 * t1712 - 0.88e2 / 0.9e1 * t566 * t1715 + 0.128e3 / 0.9e1 * t523 * t1706 - 0.512e3 / 0.9e1 * t1720 * t1712 + 0.176e3 / 0.9e1 * t571 * t1715 + 0.128e3 / 0.3e1 * t1726 * t1728 - 0.176e3 / 0.9e1 * t575 * t1731 + 0.128e3 / 0.3e1 * t1734 * t1712 - 0.128e3 * t1737 * t1728 + 0.88e2 / 0.3e1 * t580 * t1731 + 0.256e3 / 0.3e1 * t1743 * t1745 - 0.88e2 / 0.3e1 * t584 * t1748 + 0.256e3 / 0.3e1 * t1751 * t1728 - 0.2048e4 / 0.9e1 * t1754 * t1745 + 0.352e3 / 0.9e1 * t589 * t1748 + 0.1280e4 / 0.9e1 * t1761 * t1763 * t799 * t1538 - 0.352e3 / 0.9e1 * t594 * t597 * t1513
  t1780 = params.alpha_ss ** 2
  t1781 = t1780 * t1508
  t1784 = params.alpha_ss * t1518
  t1829 = t1595 * t1597 / 0.4e1 + t1632 * t1597 / 0.4e1 - t1635 * s0 * t929 * t854 / 0.4e1 + 0.2e1 * t350 * t850 * t866 + t553 * t1696 * t866 + t1387 * t775 * t788 + 0.2e1 * t499 * t601 + t557 * t1771 + t1502 * t545 + t1129 * t1594 * t857 + 0.2e1 * t350 * t1631 * t857 + t553 * (0.2e1 * t682 * t1592 * t1781 - t1600 * t1784 + (0.88e2 / 0.9e1 * t1575 * t1513 + 0.80e2 / 0.9e1 * t1605 * t560) * t1581 - 0.4e1 * t1608 * t1592 * t1601 + 0.6e1 * t1579 * t1627 * t1781 - 0.2e1 * t1610 * t1784 + (0.304e3 / 0.9e1 * t1583 * t1538 + 0.88e2 / 0.9e1 * t1585 * t1513 * t1577 + 0.80e2 / 0.3e1 * t1585 * t906 + 0.200e3 / 0.9e1 * t711 * t858 * t873 + 0.160e3 / 0.9e1 * t1621 * t1516) * t1592 - 0.6e1 * t1624 * t1627 * t1601 + 0.12e2 * t1590 / t1626 / t1572 * t1781 - 0.3e1 * t1628 * t1784) * t857 + t1387 * t718 * t725
  t1832 = t905 * t926
  t1834 = t1635 * t1597
  t1836 = t1595 * t857
  t1838 = t1632 * t857
  t1840 = t900 * t896
  d11 = 0.2e1 * t546 + 0.2e1 * t602 + 0.2e1 * t680 + 0.2e1 * t726 + 0.2e1 * t733 + 0.2e1 * t789 + 0.2e1 * t867 + 0.2e1 * t889 + t7 * (t1569 + t1829) + t1832 / 0.4e1 + t1834 / 0.4e1 + 0.2e1 * t1836 + 0.2e1 * t1838 - 0.80e2 / 0.3e1 * t1840
  t1843 = -t70 - t130
  t1844 = f.my_piecewise3(t73, 0, t1843)
  t1848 = f.my_piecewise3(t73, 0, -t263 * t1843 / 0.3e1)
  t1850 = t191 * t192 * t1848
  t1852 = -t262 + 0.53425000000000000000000000000000000000000000000000e-1 * t1850
  t1854 = 0.621814e-1 * t1852 * t216
  t1855 = -t277 + t1850
  t1856 = t276 * t1855
  t1859 = t283 * t1855
  t1861 = t195 * t1848
  t1863 = t205 * t207 * t1861
  t1865 = 0.18989250000000000000000000000000000000000000000000e1 * t1856 - t281 + 0.89690000000000000000000000000000000000000000000000e0 * t1850 + 0.30716250000000000000000000000000000000000000000000e0 * t1859 - t289 + 0.24647000000000000000000000000000000000000000000000e0 * t1863
  t1866 = t1865 * t295
  t1868 = 0.10000000000000000000000000000000000000000000000000e1 * t275 * t1866
  t1870 = -t299 + 0.51370000000000000000000000000000000000000000000000e-1 * t1850
  t1877 = 0.35297250000000000000000000000000000000000000000000e1 * t1856 - t308 + 0.15494250000000000000000000000000000000000000000000e1 * t1850 + 0.63116250000000000000000000000000000000000000000000e0 * t1859 - t311 + 0.31258500000000000000000000000000000000000000000000e0 * t1863
  t1878 = t1877 * t314
  t1882 = -t318 + 0.27812500000000000000000000000000000000000000000000e-1 * t1850
  t1883 = t1882 * t249
  t1889 = 0.25892500000000000000000000000000000000000000000000e1 * t1856 - t327 + 0.90577500000000000000000000000000000000000000000000e0 * t1850 + 0.16504875000000000000000000000000000000000000000000e0 * t1859 - t330 + 0.24835500000000000000000000000000000000000000000000e0 * t1863
  t1890 = t1889 * t333
  t1898 = t324 * t1889 * t333
  t1901 = -t1854 + t1868 + t225 * (-0.3109070e-1 * t1870 * t236 + 0.10000000000000000000000000000000000000000000000000e1 * t306 * t1878 + t1854 - t1868 - 0.19751673498613801407483339618206552048944131217655e-1 * t1883 + 0.58482236226346462072622386637590534819724553404280e0 * t325 * t1890) + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t1883 - 0.58482236226346462072622386637590534819724553404280e0 * t341 * t1898
  t1905 = f.my_piecewise3(t189, 0, t1844 * t256 / 0.2e1 + t258 * t1901 / 0.2e1)
  t1906 = t1905 * t887
  t1907 = t1906 * t866
  t1908 = t682 * t697
  t1910 = 0.1e1 / t511 / t778
  t1911 = s2 * t1910
  t1913 = tau1 * t513
  t1915 = -0.8e1 / 0.3e1 * t1911 - 0.10e2 / 0.3e1 * t1913
  t1916 = params.alpha_ss * t1915
  t1920 = t692 * tau1
  t1923 = -0.8e1 / 0.3e1 * t690 * t1910 - 0.10e2 / 0.3e1 * t1920 * t513
  t1925 = t695 * t716
  t1928 = t702 * t509
  t1930 = 0.1e1 / t510 / t1928
  t1939 = t711 * t693
  t1942 = -0.16e2 / 0.3e1 * t701 * t1930 - 0.8e1 / 0.3e1 * t708 * t1910 * t693 - 0.10e2 / 0.3e1 * t708 * t705 * tau1 - 0.20e2 / 0.3e1 * t1939 * t1913
  t1944 = t696 ** 2
  t1945 = 0.1e1 / t1944
  t1946 = t714 * t1945
  t1949 = -t1908 * t1916 - 0.2e1 * t1925 * t1916 - 0.3e1 * t1946 * t1916 + t1923 * t697 + t1942 * t716
  t1950 = t556 * t1949
  t1951 = t1950 * t725
  t1952 = -t1843
  t1953 = f.my_piecewise3(t80, 0, t1952)
  t1957 = f.my_piecewise3(t80, 0, -t412 * t1952 / 0.3e1)
  t1959 = t191 * t192 * t1957
  t1961 = -t411 + 0.53425000000000000000000000000000000000000000000000e-1 * t1959
  t1963 = 0.621814e-1 * t1961 * t373
  t1964 = -t426 + t1959
  t1965 = t425 * t1964
  t1968 = t432 * t1964
  t1970 = t355 * t1957
  t1972 = t205 * t207 * t1970
  t1974 = 0.18989250000000000000000000000000000000000000000000e1 * t1965 - t430 + 0.89690000000000000000000000000000000000000000000000e0 * t1959 + 0.30716250000000000000000000000000000000000000000000e0 * t1968 - t437 + 0.24647000000000000000000000000000000000000000000000e0 * t1972
  t1975 = t1974 * t443
  t1977 = 0.10000000000000000000000000000000000000000000000000e1 * t424 * t1975
  t1979 = -t447 + 0.51370000000000000000000000000000000000000000000000e-1 * t1959
  t1986 = 0.35297250000000000000000000000000000000000000000000e1 * t1965 - t456 + 0.15494250000000000000000000000000000000000000000000e1 * t1959 + 0.63116250000000000000000000000000000000000000000000e0 * t1968 - t459 + 0.31258500000000000000000000000000000000000000000000e0 * t1972
  t1987 = t1986 * t462
  t1991 = -t466 + 0.27812500000000000000000000000000000000000000000000e-1 * t1959
  t1992 = t1991 * t399
  t1998 = 0.25892500000000000000000000000000000000000000000000e1 * t1965 - t475 + 0.90577500000000000000000000000000000000000000000000e0 * t1959 + 0.16504875000000000000000000000000000000000000000000e0 * t1968 - t478 + 0.24835500000000000000000000000000000000000000000000e0 * t1972
  t1999 = t1998 * t481
  t2007 = t472 * t1998 * t481
  t2010 = -t1963 + t1977 + t225 * (-0.3109070e-1 * t1979 * t386 + 0.10000000000000000000000000000000000000000000000000e1 * t454 * t1987 + t1963 - t1977 - 0.19751673498613801407483339618206552048944131217655e-1 * t1992 + 0.58482236226346462072622386637590534819724553404280e0 * t473 * t1999) + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t1992 - 0.58482236226346462072622386637590534819724553404280e0 * t489 * t2007
  t2014 = f.my_piecewise3(t352, 0, t1953 * t406 / 0.2e1 + t408 * t2010 / 0.2e1)
  t2015 = t2014 * t775
  t2016 = t2015 * t788
  t2021 = t700 * t1930 * t749
  t2029 = t755 / t756 / r1 * t760
  t2038 = t766 / t511 / t756 / t778 * t772
  t2043 = t766 * s2
  t2049 = 0.1e1 / t771 / t740
  t2053 = -0.8e1 / 0.3e1 * t737 * t1911 * t741 + 0.8e1 / 0.3e1 * t798 * t2021 - 0.16e2 / 0.3e1 * t746 * t2021 + 0.16e2 / 0.3e1 * t812 * t2029 - 0.8e1 * t754 * t2029 + 0.8e1 * t825 * t2038 - 0.32e2 / 0.3e1 * t765 * t2038 + 0.32e2 / 0.3e1 * t839 * t2043 / t510 / t756 / t1928 * t2049
  t2054 = t556 * t2053
  t2055 = t2054 * t788
  t2056 = t1905 * t1594
  t2057 = t2056 * t857
  t2058 = t2014 * t718
  t2059 = t2058 * t725
  t2060 = t556 * t718
  t2061 = 0.1e1 / t509
  t2063 = s2 * t2061 * t722
  t2064 = t2060 * t2063
  t2066 = t556 * t775
  t2067 = t2066 * s2
  t2069 = t2061 * t722 * t787
  t2070 = t2067 * t2069
  t2072 = -0.40e2 / 0.3e1 * t1840 + t1907 + t1951 + t789 + t2016 + t2055 + t2057 + t2059 + t2064 / 0.8e1 + t2070 / 0.8e1 + t867 + t889 + t602
  t2073 = t2066 * t725
  t2077 = t783 * t786
  t2078 = t777 / t510 / t702 * t2077
  t2079 = t2073 * t2078
  t2084 = f.my_piecewise3(t73, 0, 0.4e1 / 0.3e1 * t76 * t1843)
  t2087 = f.my_piecewise3(t80, 0, 0.4e1 / 0.3e1 * t81 * t1952)
  t2089 = (t2084 + t2087) * t88
  t2090 = t2089 * t118
  t2094 = t35 + t62 - t121 - t127 + t128 * t2090 + t175 + 0.19751673498613801407483339618206552048944131217655e-1 * t2089 * t116 - t182 - t187 - t1905 - t2014
  t2095 = t2094 * t545
  t2096 = t2094 * t732
  t2101 = t526 * s2
  t2102 = t2101 * t1910
  t2107 = t534 * s2
  t2108 = t2107 * t1910
  t2113 = t542 * s2
  t2114 = t2113 * t1910
  t2119 = t596 * s2
  t2123 = -0.8e1 / 0.3e1 * t502 * t1911 * t518 + 0.8e1 / 0.3e1 * t566 * t2102 - 0.16e2 / 0.3e1 * t571 * t2102 + 0.16e2 / 0.3e1 * t575 * t2108 - 0.8e1 * t580 * t2108 + 0.8e1 * t584 * t2114 - 0.32e2 / 0.3e1 * t589 * t2114 + 0.32e2 / 0.3e1 * t594 * t2119 * t1910
  t2124 = t557 * t2123
  t2125 = params.alpha_ab * t1915
  t2127 = t632 * s2
  t2130 = t636 * tau1
  t2133 = -0.8e1 / 0.3e1 * t2127 * t1910 - 0.10e2 / 0.3e1 * t2130 * t513
  t2139 = t655 * s2
  t2147 = -0.16e2 / 0.3e1 * t652 * t1911 - 0.8e1 / 0.3e1 * t2139 * t1910 * t643 - 0.10e2 / 0.3e1 * t660 * t1913 - 0.20e2 / 0.3e1 * t664 * t1913
  t2151 = -t625 * t2125 - 0.2e1 * t648 * t2125 - 0.3e1 * t676 * t2125 + t2133 * t624 + t2147 * t647
  t2152 = t557 * t2151
  t2153 = 0.2e1 * t939
  t2154 = f.my_piecewise3(t73, 0, t2153)
  t2160 = t191 * t259 * t1848
  t2169 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t957 * t1843 * t131 - 0.2e1 / 0.3e1 * t263 * t63 * t938)
  t2171 = t191 * t192 * t2169
  t2175 = 0.621814e-1 * (t951 - 0.17808333333333333333333333333333333333333333333333e-1 * t953 - 0.17808333333333333333333333333333333333333333333333e-1 * t2160 + 0.53425000000000000000000000000000000000000000000000e-1 * t2171) * t216
  t2176 = t1852 * t274
  t2178 = 0.10000000000000000000000000000000000000000000000000e1 * t2176 * t296
  t2180 = 0.10000000000000000000000000000000000000000000000000e1 * t971 * t1866
  t2183 = 0.20000000000000000000000000000000000000000000000000e1 * t976 * t1866 * t294
  t2185 = t982 * t1855 * t278
  t2189 = t986 - t953 / 0.3e1 - t2160 / 0.3e1 + t2171
  t2190 = t276 * t2189
  t2196 = t994 * t1855 * t278
  t2198 = t283 * t2189
  t2202 = t205 * t286 * t1861
  t2206 = t205 * t207 * t266 * t1848
  t2210 = t205 * t207 * t195 * t2169
  t2212 = -0.94946250000000000000000000000000000000000000000000e0 * t2185 + 0.18989250000000000000000000000000000000000000000000e1 * t2190 + t991 - 0.29896666666666666666666666666666666666666666666667e0 * t953 - 0.29896666666666666666666666666666666666666666666667e0 * t2160 + 0.89690000000000000000000000000000000000000000000000e0 * t2171 + 0.15358125000000000000000000000000000000000000000000e0 * t2196 + 0.30716250000000000000000000000000000000000000000000e0 * t2198 + t1004 - 0.16431333333333333333333333333333333333333333333333e0 * t1006 - 0.16431333333333333333333333333333333333333333333333e0 * t2202 + 0.24647000000000000000000000000000000000000000000000e0 * t2206 + 0.24647000000000000000000000000000000000000000000000e0 * t2210
  t2215 = 0.10000000000000000000000000000000000000000000000000e1 * t275 * t2212 * t295
  t2219 = 0.16081979498692535066756296899072713062105388428051e2 * t1022 * t1865 * t1024 * t294
  t2226 = t1870 * t305
  t2245 = -0.17648625000000000000000000000000000000000000000000e1 * t2185 + 0.35297250000000000000000000000000000000000000000000e1 * t2190 + t1046 - 0.51647500000000000000000000000000000000000000000000e0 * t953 - 0.51647500000000000000000000000000000000000000000000e0 * t2160 + 0.15494250000000000000000000000000000000000000000000e1 * t2171 + 0.31558125000000000000000000000000000000000000000000e0 * t2196 + 0.63116250000000000000000000000000000000000000000000e0 * t2198 + t1051 - 0.20839000000000000000000000000000000000000000000000e0 * t1006 - 0.20839000000000000000000000000000000000000000000000e0 * t2202 + 0.31258500000000000000000000000000000000000000000000e0 * t2206 + 0.31258500000000000000000000000000000000000000000000e0 * t2210
  t2257 = (t1067 - 0.92708333333333333333333333333333333333333333333333e-2 * t953 - 0.92708333333333333333333333333333333333333333333333e-2 * t2160 + 0.27812500000000000000000000000000000000000000000000e-1 * t2171) * t249
  t2259 = t1882 * t324
  t2278 = -0.12946250000000000000000000000000000000000000000000e1 * t2185 + 0.25892500000000000000000000000000000000000000000000e1 * t2190 + t1085 - 0.30192500000000000000000000000000000000000000000000e0 * t953 - 0.30192500000000000000000000000000000000000000000000e0 * t2160 + 0.90577500000000000000000000000000000000000000000000e0 * t2171 + 0.82524375000000000000000000000000000000000000000000e-1 * t2196 + 0.16504875000000000000000000000000000000000000000000e0 * t2198 + t1090 - 0.16557000000000000000000000000000000000000000000000e0 * t1006 - 0.16557000000000000000000000000000000000000000000000e0 * t2202 + 0.24835500000000000000000000000000000000000000000000e0 * t2206 + 0.24835500000000000000000000000000000000000000000000e0 * t2210
  t2286 = -0.3109070e-1 * (t1028 - 0.17123333333333333333333333333333333333333333333333e-1 * t953 - 0.17123333333333333333333333333333333333333333333333e-1 * t2160 + 0.51370000000000000000000000000000000000000000000000e-1 * t2171) * t236 + 0.10000000000000000000000000000000000000000000000000e1 * t2226 * t315 + 0.10000000000000000000000000000000000000000000000000e1 * t1034 * t1878 - 0.20000000000000000000000000000000000000000000000000e1 * t1039 * t1878 * t313 + 0.10000000000000000000000000000000000000000000000000e1 * t306 * t2245 * t314 + 0.32163958997385070133512593798145426124210776856102e2 * t1061 * t1877 * t1063 * t313 + t2175 - t2178 - t2180 + t2183 - t2215 - t2219 - 0.19751673498613801407483339618206552048944131217655e-1 * t2257 + 0.58482236226346462072622386637590534819724553404280e0 * t2259 * t334 + 0.58482236226346462072622386637590534819724553404280e0 * t1073 * t1890 - 0.11696447245269292414524477327518106963944910680856e1 * t1078 * t1890 * t332 + 0.58482236226346462072622386637590534819724553404280e0 * t325 * t2278 * t333 + 0.17315859105681463759666483083807725165579399831905e2 * t1100 * t1889 * t1102 * t332
  t2290 = t225 * t1882
  t2308 = -t2175 + t2178 + t2180 - t2183 + t2215 + t2219 + t225 * t2286 + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t2257 - 0.58482236226346462072622386637590534819724553404280e0 * t2290 * t343 - 0.58482236226346462072622386637590534819724553404280e0 * t1110 * t1898 + 0.11696447245269292414524477327518106963944910680856e1 * t341 * t1077 * t1889 * t334 - 0.58482236226346462072622386637590534819724553404280e0 * t341 * t324 * t2278 * t333 - 0.17315859105681463759666483083807725165579399831905e2 * t341 * t1099 * t1889 * t1102 * t332
  t2312 = f.my_piecewise3(t189, 0, t1844 * t346 / 0.2e1 + t190 * t1901 / 0.2e1 + t2154 * t256 / 0.2e1 + t258 * t2308 / 0.2e1)
  t2323 = f.my_piecewise3(t80, 0, -t2153)
  t2329 = t191 * t259 * t1957
  t2338 = f.my_piecewise3(t80, 0, 0.4e1 / 0.9e1 * t1218 * t1952 * t135 + 0.2e1 / 0.3e1 * t412 * t63 * t938)
  t2340 = t191 * t192 * t2338
  t2344 = 0.621814e-1 * (t1212 - 0.17808333333333333333333333333333333333333333333333e-1 * t1214 - 0.17808333333333333333333333333333333333333333333333e-1 * t2329 + 0.53425000000000000000000000000000000000000000000000e-1 * t2340) * t373
  t2345 = t1961 * t423
  t2347 = 0.10000000000000000000000000000000000000000000000000e1 * t2345 * t444
  t2349 = 0.10000000000000000000000000000000000000000000000000e1 * t1232 * t1975
  t2352 = 0.20000000000000000000000000000000000000000000000000e1 * t1237 * t1975 * t442
  t2354 = t1243 * t1964 * t427
  t2358 = t1247 - t1214 / 0.3e1 - t2329 / 0.3e1 + t2340
  t2359 = t425 * t2358
  t2365 = t1255 * t1964 * t427
  t2367 = t432 * t2358
  t2371 = t205 * t286 * t1970
  t2375 = t205 * t207 * t415 * t1957
  t2379 = t205 * t207 * t355 * t2338
  t2381 = -0.94946250000000000000000000000000000000000000000000e0 * t2354 + 0.18989250000000000000000000000000000000000000000000e1 * t2359 + t1252 - 0.29896666666666666666666666666666666666666666666667e0 * t1214 - 0.29896666666666666666666666666666666666666666666667e0 * t2329 + 0.89690000000000000000000000000000000000000000000000e0 * t2340 + 0.15358125000000000000000000000000000000000000000000e0 * t2365 + 0.30716250000000000000000000000000000000000000000000e0 * t2367 + t1262 - 0.16431333333333333333333333333333333333333333333333e0 * t1264 - 0.16431333333333333333333333333333333333333333333333e0 * t2371 + 0.24647000000000000000000000000000000000000000000000e0 * t2375 + 0.24647000000000000000000000000000000000000000000000e0 * t2379
  t2384 = 0.10000000000000000000000000000000000000000000000000e1 * t424 * t2381 * t443
  t2388 = 0.16081979498692535066756296899072713062105388428051e2 * t1280 * t1974 * t1282 * t442
  t2395 = t1979 * t453
  t2414 = -0.17648625000000000000000000000000000000000000000000e1 * t2354 + 0.35297250000000000000000000000000000000000000000000e1 * t2359 + t1304 - 0.51647500000000000000000000000000000000000000000000e0 * t1214 - 0.51647500000000000000000000000000000000000000000000e0 * t2329 + 0.15494250000000000000000000000000000000000000000000e1 * t2340 + 0.31558125000000000000000000000000000000000000000000e0 * t2365 + 0.63116250000000000000000000000000000000000000000000e0 * t2367 + t1309 - 0.20839000000000000000000000000000000000000000000000e0 * t1264 - 0.20839000000000000000000000000000000000000000000000e0 * t2371 + 0.31258500000000000000000000000000000000000000000000e0 * t2375 + 0.31258500000000000000000000000000000000000000000000e0 * t2379
  t2426 = (t1325 - 0.92708333333333333333333333333333333333333333333333e-2 * t1214 - 0.92708333333333333333333333333333333333333333333333e-2 * t2329 + 0.27812500000000000000000000000000000000000000000000e-1 * t2340) * t399
  t2428 = t1991 * t472
  t2447 = -0.12946250000000000000000000000000000000000000000000e1 * t2354 + 0.25892500000000000000000000000000000000000000000000e1 * t2359 + t1343 - 0.30192500000000000000000000000000000000000000000000e0 * t1214 - 0.30192500000000000000000000000000000000000000000000e0 * t2329 + 0.90577500000000000000000000000000000000000000000000e0 * t2340 + 0.82524375000000000000000000000000000000000000000000e-1 * t2365 + 0.16504875000000000000000000000000000000000000000000e0 * t2367 + t1348 - 0.16557000000000000000000000000000000000000000000000e0 * t1264 - 0.16557000000000000000000000000000000000000000000000e0 * t2371 + 0.24835500000000000000000000000000000000000000000000e0 * t2375 + 0.24835500000000000000000000000000000000000000000000e0 * t2379
  t2455 = -0.3109070e-1 * (t1286 - 0.17123333333333333333333333333333333333333333333333e-1 * t1214 - 0.17123333333333333333333333333333333333333333333333e-1 * t2329 + 0.51370000000000000000000000000000000000000000000000e-1 * t2340) * t386 + 0.10000000000000000000000000000000000000000000000000e1 * t2395 * t463 + 0.10000000000000000000000000000000000000000000000000e1 * t1292 * t1987 - 0.20000000000000000000000000000000000000000000000000e1 * t1297 * t1987 * t461 + 0.10000000000000000000000000000000000000000000000000e1 * t454 * t2414 * t462 + 0.32163958997385070133512593798145426124210776856102e2 * t1319 * t1986 * t1321 * t461 + t2344 - t2347 - t2349 + t2352 - t2384 - t2388 - 0.19751673498613801407483339618206552048944131217655e-1 * t2426 + 0.58482236226346462072622386637590534819724553404280e0 * t2428 * t482 + 0.58482236226346462072622386637590534819724553404280e0 * t1331 * t1999 - 0.11696447245269292414524477327518106963944910680856e1 * t1336 * t1999 * t480 + 0.58482236226346462072622386637590534819724553404280e0 * t473 * t2447 * t481 + 0.17315859105681463759666483083807725165579399831905e2 * t1358 * t1998 * t1360 * t480
  t2459 = t225 * t1991
  t2477 = -t2344 + t2347 + t2349 - t2352 + t2384 + t2388 + t225 * t2455 + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t2426 - 0.58482236226346462072622386637590534819724553404280e0 * t2459 * t491 - 0.58482236226346462072622386637590534819724553404280e0 * t1368 * t2007 + 0.11696447245269292414524477327518106963944910680856e1 * t489 * t1335 * t1998 * t482 - 0.58482236226346462072622386637590534819724553404280e0 * t489 * t472 * t2447 * t481 - 0.17315859105681463759666483083807725165579399831905e2 * t489 * t1357 * t1998 * t1360 * t480
  t2481 = f.my_piecewise3(t352, 0, t1953 * t494 / 0.2e1 + t353 * t2010 / 0.2e1 + t2323 * t406 / 0.2e1 + t408 * t2477 / 0.2e1)
  t2494 = t2089 * t1 * t180
  t2497 = t125 * t2090
  t2506 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t1389 * t1843 * t131 + 0.8e1 / 0.3e1 * t76 * t63 * t938)
  t2514 = f.my_piecewise3(t80, 0, 0.4e1 / 0.9e1 * t1397 * t1952 * t135 - 0.8e1 / 0.3e1 * t81 * t63 * t938)
  t2516 = (t2506 + t2514) * t88
  t2520 = t128 * t2089 * t173
  t2523 = -t1135 + t1139 - 0.18311447306006545054854346104378990962041954983034e-3 * t1141 - 0.18311447306006545054854346104378990962041954983034e-3 * t2494 - t2312 - t1151 - 0.58482236226346462072622386637590534819724553404280e0 * t1153 - 0.4e1 * t2497 + t128 * t2516 * t118 + t2520 + 0.19751673498613801407483339618206552048944131217655e-1 * t2516 * t116 + t1160 - t1187 - t2481
  t2524 = t69 * t2090
  t2528 = t2089 * t106 * t185
  t2531 = -t1194 + t1204 + 0.4e1 * t2524 + t1410 - 0.4e1 * t1412 - 0.58482236226346462072622386637590534819724553404280e0 * t2528 + t1421 - t1423 + t1479 - t1458 + t1483 + t1488 - 0.4e1 * t1489 - t1495
  t2532 = t2523 + t2531
  t2536 = t2312 * t887 * t866 + t1905 * t850 * t866 + t1906 * s0 * t926 / 0.8e1 - 0.40e2 / 0.3e1 * t1906 * t857 * t896 + t2481 * t775 * t788 + t498 * t2053 * t788 + t776 * s2 * t2069 / 0.8e1 - 0.40e2 / 0.3e1 * t776 * t725 * t2078 + t2532 * t545 + t2094 * t601 + t499 * t2123
  t2542 = t515 * t534
  t2544 = t1911 * t561
  t2555 = t524 * t542
  t2565 = t532 * t596
  t2579 = -0.128e3 / 0.9e1 * t565 * s2 * t1910 * t526 * t561 + 0.128e3 / 0.9e1 * t1709 * t2542 * t2544 + 0.128e3 / 0.9e1 * t523 * s0 * t560 * t526 * t1911 - 0.512e3 / 0.9e1 * t574 * t2542 * t2544 + 0.128e3 / 0.3e1 * t1725 * t2555 * t2544 + 0.128e3 / 0.3e1 * t531 * t2542 * t2544 - 0.128e3 * t583 * t2555 * t2544 + 0.256e3 / 0.3e1 * t1742 * t2565 * t2544 + 0.256e3 / 0.3e1 * t539 * t2555 * t2544 - 0.2048e4 / 0.9e1 * t593 * t2565 * t2544 + 0.1280e4 / 0.9e1 * t1760 * t540 * t1763 * t2544
  t2597 = t1507 * t1915 * t629
  t2600 = t2133 * t647
  t2627 = t2147 * t675
  t2636 = t557 * t2579 + t2312 * t1594 * t857 + t1905 * t1631 * t857 + t2056 * t1597 / 0.8e1 + t2481 * t718 * t725 + t498 * t1949 * t725 + t719 * t2063 / 0.8e1 + t2532 * t732 + t2094 * t679 + t499 * t2151 + t557 * (0.2e1 * t1506 * t2597 - 0.2e1 * t2600 * t630 - 0.2e1 * t1527 * t2125 + 0.6e1 * t1530 * t2597 + (0.128e3 / 0.9e1 * t651 * s0 * t560 * s2 * t1910 + 0.80e2 / 0.9e1 * t2139 * t1910 * tau0 * t507 + 0.80e2 / 0.9e1 * t656 * t560 * tau1 * t513 + 0.200e3 / 0.9e1 * t663 * tau0 * t507 * tau1 * t513) * t647 - 0.3e1 * t2627 * t630 - 0.3e1 * t1557 * t2125 + 0.12e2 * t1562 * t2597)
  t2639 = -0.40e2 / 0.3e1 * t2079 + t546 + t733 + t1834 / 0.8e1 + t680 + t2095 + t726 + t1836 + t1838 + t2096 + t1832 / 0.8e1 + t2124 + t2152 + t7 * (t2536 + t2636)
  d12 = t2072 + t2639
  t2647 = t1915 ** 2
  t2648 = t1780 * t2647
  t2652 = 0.1e1 / t511 / t702
  t2653 = s2 * t2652
  t2655 = tau1 * t1910
  t2657 = 0.88e2 / 0.9e1 * t2653 + 0.80e2 / 0.9e1 * t2655
  t2658 = params.alpha_ss * t2657
  t2674 = t702 * t778
  t2676 = 0.1e1 / t510 / t2674
  t2682 = t1930 * tau1
  t2707 = t1507 * t2647
  t2710 = params.alpha_ab * t2657
  t2751 = 0.1e1 / t778
  t2759 = t700 * t2676
  t2760 = t2759 * t526
  t2764 = t534 * t700 * t2676
  t2767 = t2101 * t2652
  t2777 = t542 * t700 * t2676
  t2780 = t2107 * t2652
  t2790 = t596 * t700 * t2676
  t2793 = t2113 * t2652
  t2809 = 0.88e2 / 0.9e1 * t502 * t2653 * t518 - 0.128e3 / 0.9e1 * t565 * t2760 + 0.128e3 / 0.9e1 * t1710 * t2764 - 0.88e2 / 0.9e1 * t566 * t2767 + 0.128e3 / 0.9e1 * t523 * t2760 - 0.512e3 / 0.9e1 * t1720 * t2764 + 0.176e3 / 0.9e1 * t571 * t2767 + 0.128e3 / 0.3e1 * t1726 * t2777 - 0.176e3 / 0.9e1 * t575 * t2780 + 0.128e3 / 0.3e1 * t1734 * t2764 - 0.128e3 * t1737 * t2777 + 0.88e2 / 0.3e1 * t580 * t2780 + 0.256e3 / 0.3e1 * t1743 * t2790 - 0.88e2 / 0.3e1 * t584 * t2793 + 0.256e3 / 0.3e1 * t1751 * t2777 - 0.2048e4 / 0.9e1 * t1754 * t2790 + 0.352e3 / 0.9e1 * t589 * t2793 + 0.1280e4 / 0.9e1 * t1761 * t1763 * t700 * t2676 - 0.352e3 / 0.9e1 * t594 * t2119 * t2652
  t2812 = 0.2e1 * t129 + 0.2e1 * t939
  t2813 = f.my_piecewise3(t73, 0, t2812)
  t2818 = t1843 ** 2
  t2824 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t957 * t2818 - t263 * t2812 / 0.3e1)
  t2826 = t191 * t192 * t2824
  t2830 = 0.621814e-1 * (t951 - 0.35616666666666666666666666666666666666666666666666e-1 * t2160 + 0.53425000000000000000000000000000000000000000000000e-1 * t2826) * t216
  t2832 = 0.20000000000000000000000000000000000000000000000000e1 * t2176 * t1866
  t2833 = t1865 ** 2
  t2836 = 0.20000000000000000000000000000000000000000000000000e1 * t976 * t2833 * t295
  t2837 = t1855 ** 2
  t2838 = t982 * t2837
  t2841 = t986 - 0.2e1 / 0.3e1 * t2160 + t2826
  t2842 = t276 * t2841
  t2846 = t994 * t2837
  t2848 = t283 * t2841
  t2851 = t1848 ** 2
  t2853 = t205 * t207 * t2851
  t2857 = t205 * t207 * t195 * t2824
  t2859 = -0.94946250000000000000000000000000000000000000000000e0 * t2838 + 0.18989250000000000000000000000000000000000000000000e1 * t2842 + t991 - 0.59793333333333333333333333333333333333333333333334e0 * t2160 + 0.89690000000000000000000000000000000000000000000000e0 * t2826 + 0.15358125000000000000000000000000000000000000000000e0 * t2846 + 0.30716250000000000000000000000000000000000000000000e0 * t2848 + t1004 - 0.32862666666666666666666666666666666666666666666666e0 * t2202 + 0.24647000000000000000000000000000000000000000000000e0 * t2853 + 0.24647000000000000000000000000000000000000000000000e0 * t2857
  t2862 = 0.10000000000000000000000000000000000000000000000000e1 * t275 * t2859 * t295
  t2865 = 0.16081979498692535066756296899072713062105388428051e2 * t1022 * t2833 * t1024
  t2873 = t1877 ** 2
  t2886 = -0.17648625000000000000000000000000000000000000000000e1 * t2838 + 0.35297250000000000000000000000000000000000000000000e1 * t2842 + t1046 - 0.10329500000000000000000000000000000000000000000000e1 * t2160 + 0.15494250000000000000000000000000000000000000000000e1 * t2826 + 0.31558125000000000000000000000000000000000000000000e0 * t2846 + 0.63116250000000000000000000000000000000000000000000e0 * t2848 + t1051 - 0.41678000000000000000000000000000000000000000000000e0 * t2202 + 0.31258500000000000000000000000000000000000000000000e0 * t2853 + 0.31258500000000000000000000000000000000000000000000e0 * t2857
  t2896 = (t1067 - 0.18541666666666666666666666666666666666666666666667e-1 * t2160 + 0.27812500000000000000000000000000000000000000000000e-1 * t2826) * t249
  t2900 = t1889 ** 2
  t2913 = -0.12946250000000000000000000000000000000000000000000e1 * t2838 + 0.25892500000000000000000000000000000000000000000000e1 * t2842 + t1085 - 0.60385000000000000000000000000000000000000000000000e0 * t2160 + 0.90577500000000000000000000000000000000000000000000e0 * t2826 + 0.82524375000000000000000000000000000000000000000000e-1 * t2846 + 0.16504875000000000000000000000000000000000000000000e0 * t2848 + t1090 - 0.33114000000000000000000000000000000000000000000000e0 * t2202 + 0.24835500000000000000000000000000000000000000000000e0 * t2853 + 0.24835500000000000000000000000000000000000000000000e0 * t2857
  t2920 = -0.3109070e-1 * (t1028 - 0.34246666666666666666666666666666666666666666666666e-1 * t2160 + 0.51370000000000000000000000000000000000000000000000e-1 * t2826) * t236 + 0.20000000000000000000000000000000000000000000000000e1 * t2226 * t1878 - 0.20000000000000000000000000000000000000000000000000e1 * t1039 * t2873 * t314 + 0.10000000000000000000000000000000000000000000000000e1 * t306 * t2886 * t314 + 0.32163958997385070133512593798145426124210776856102e2 * t1061 * t2873 * t1063 + t2830 - t2832 + t2836 - t2862 - t2865 - 0.19751673498613801407483339618206552048944131217655e-1 * t2896 + 0.11696447245269292414524477327518106963944910680856e1 * t2259 * t1890 - 0.11696447245269292414524477327518106963944910680856e1 * t1078 * t2900 * t333 + 0.58482236226346462072622386637590534819724553404280e0 * t325 * t2913 * t333 + 0.17315859105681463759666483083807725165579399831905e2 * t1100 * t2900 * t1102
  t2938 = -t2830 + t2832 - t2836 + t2862 + t2865 + t225 * t2920 + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t2896 - 0.11696447245269292414524477327518106963944910680856e1 * t2290 * t1898 + 0.11696447245269292414524477327518106963944910680856e1 * t341 * t1077 * t2900 * t333 - 0.58482236226346462072622386637590534819724553404280e0 * t341 * t324 * t2913 * t333 - 0.17315859105681463759666483083807725165579399831905e2 * t341 * t1099 * t2900 * t1102
  t2942 = f.my_piecewise3(t189, 0, t2813 * t256 / 0.2e1 + t1844 * t1901 + t258 * t2938 / 0.2e1)
  t2956 = -0.80e2 / 0.3e1 * t2054 * t725 * t2078 + t2054 * s2 * t2069 / 0.4e1 + t556 * (0.2e1 * t682 * t716 * t2648 - t1908 * t2658 + (0.88e2 / 0.9e1 * t690 * t2652 + 0.80e2 / 0.9e1 * t1920 * t1910) * t697 - 0.4e1 * t1923 * t716 * t1916 + 0.6e1 * t695 * t1945 * t2648 - 0.2e1 * t1925 * t2658 + (0.304e3 / 0.9e1 * t701 * t2676 + 0.88e2 / 0.9e1 * t708 * t2652 * t693 + 0.80e2 / 0.3e1 * t708 * t2682 + 0.200e3 / 0.9e1 * t711 * t777 * t705 + 0.160e3 / 0.9e1 * t1939 * t2655) * t716 - 0.6e1 * t1942 * t1945 * t1916 + 0.12e2 * t714 / t1944 / t686 * t2648 - 0.3e1 * t1946 * t2658) * t725 + 0.2e1 * t2094 * t2123 + t557 * (0.2e1 * t1506 * t2707 - t625 * t2710 + (0.88e2 / 0.9e1 * t2127 * t2652 + 0.80e2 / 0.9e1 * t2130 * t1910) * t624 - 0.4e1 * t2600 * t2125 + 0.6e1 * t1530 * t2707 - 0.2e1 * t648 * t2710 + (0.128e3 / 0.9e1 * t651 * t700 * t2676 + 0.176e3 / 0.9e1 * t652 * t2653 + 0.88e2 / 0.9e1 * t2139 * t2652 * t643 + 0.160e3 / 0.9e1 * t2139 * t2682 + 0.80e2 / 0.9e1 * t660 * t2655 + 0.200e3 / 0.9e1 * t663 * t777 * t705 + 0.160e3 / 0.9e1 * t664 * t2655) * t647 - 0.6e1 * t2627 * t2125 + 0.12e2 * t1562 * t2707 - 0.3e1 * t676 * t2710) - t2060 * s2 * t2751 * t722 / 0.4e1 + t557 * t2809 + t2942 * t1594 * t857 + 0.2e1 * t2014 * t1949 * t725 + t2942 * t887 * t866 + 0.2e1 * t2094 * t2151 - t2067 * t2751 * t722 * t787 / 0.4e1
  t2960 = -t2812
  t2961 = f.my_piecewise3(t80, 0, t2960)
  t2966 = t1952 ** 2
  t2972 = f.my_piecewise3(t80, 0, 0.4e1 / 0.9e1 * t1218 * t2966 - t412 * t2960 / 0.3e1)
  t2974 = t191 * t192 * t2972
  t2978 = 0.621814e-1 * (t1212 - 0.35616666666666666666666666666666666666666666666666e-1 * t2329 + 0.53425000000000000000000000000000000000000000000000e-1 * t2974) * t373
  t2980 = 0.20000000000000000000000000000000000000000000000000e1 * t2345 * t1975
  t2981 = t1974 ** 2
  t2984 = 0.20000000000000000000000000000000000000000000000000e1 * t1237 * t2981 * t443
  t2985 = t1964 ** 2
  t2986 = t1243 * t2985
  t2989 = t1247 - 0.2e1 / 0.3e1 * t2329 + t2974
  t2990 = t425 * t2989
  t2994 = t1255 * t2985
  t2996 = t432 * t2989
  t2999 = t1957 ** 2
  t3001 = t205 * t207 * t2999
  t3005 = t205 * t207 * t355 * t2972
  t3007 = -0.94946250000000000000000000000000000000000000000000e0 * t2986 + 0.18989250000000000000000000000000000000000000000000e1 * t2990 + t1252 - 0.59793333333333333333333333333333333333333333333334e0 * t2329 + 0.89690000000000000000000000000000000000000000000000e0 * t2974 + 0.15358125000000000000000000000000000000000000000000e0 * t2994 + 0.30716250000000000000000000000000000000000000000000e0 * t2996 + t1262 - 0.32862666666666666666666666666666666666666666666666e0 * t2371 + 0.24647000000000000000000000000000000000000000000000e0 * t3001 + 0.24647000000000000000000000000000000000000000000000e0 * t3005
  t3010 = 0.10000000000000000000000000000000000000000000000000e1 * t424 * t3007 * t443
  t3013 = 0.16081979498692535066756296899072713062105388428051e2 * t1280 * t2981 * t1282
  t3021 = t1986 ** 2
  t3034 = -0.17648625000000000000000000000000000000000000000000e1 * t2986 + 0.35297250000000000000000000000000000000000000000000e1 * t2990 + t1304 - 0.10329500000000000000000000000000000000000000000000e1 * t2329 + 0.15494250000000000000000000000000000000000000000000e1 * t2974 + 0.31558125000000000000000000000000000000000000000000e0 * t2994 + 0.63116250000000000000000000000000000000000000000000e0 * t2996 + t1309 - 0.41678000000000000000000000000000000000000000000000e0 * t2371 + 0.31258500000000000000000000000000000000000000000000e0 * t3001 + 0.31258500000000000000000000000000000000000000000000e0 * t3005
  t3044 = (t1325 - 0.18541666666666666666666666666666666666666666666667e-1 * t2329 + 0.27812500000000000000000000000000000000000000000000e-1 * t2974) * t399
  t3048 = t1998 ** 2
  t3061 = -0.12946250000000000000000000000000000000000000000000e1 * t2986 + 0.25892500000000000000000000000000000000000000000000e1 * t2990 + t1343 - 0.60385000000000000000000000000000000000000000000000e0 * t2329 + 0.90577500000000000000000000000000000000000000000000e0 * t2974 + 0.82524375000000000000000000000000000000000000000000e-1 * t2994 + 0.16504875000000000000000000000000000000000000000000e0 * t2996 + t1348 - 0.33114000000000000000000000000000000000000000000000e0 * t2371 + 0.24835500000000000000000000000000000000000000000000e0 * t3001 + 0.24835500000000000000000000000000000000000000000000e0 * t3005
  t3068 = -0.3109070e-1 * (t1286 - 0.34246666666666666666666666666666666666666666666666e-1 * t2329 + 0.51370000000000000000000000000000000000000000000000e-1 * t2974) * t386 + 0.20000000000000000000000000000000000000000000000000e1 * t2395 * t1987 - 0.20000000000000000000000000000000000000000000000000e1 * t1297 * t3021 * t462 + 0.10000000000000000000000000000000000000000000000000e1 * t454 * t3034 * t462 + 0.32163958997385070133512593798145426124210776856102e2 * t1319 * t3021 * t1321 + t2978 - t2980 + t2984 - t3010 - t3013 - 0.19751673498613801407483339618206552048944131217655e-1 * t3044 + 0.11696447245269292414524477327518106963944910680856e1 * t2428 * t1999 - 0.11696447245269292414524477327518106963944910680856e1 * t1336 * t3048 * t481 + 0.58482236226346462072622386637590534819724553404280e0 * t473 * t3061 * t481 + 0.17315859105681463759666483083807725165579399831905e2 * t1358 * t3048 * t1360
  t3086 = -t2978 + t2980 - t2984 + t3010 + t3013 + t225 * t3068 + 0.19751673498613801407483339618206552048944131217655e-1 * t225 * t3044 - 0.11696447245269292414524477327518106963944910680856e1 * t2459 * t2007 + 0.11696447245269292414524477327518106963944910680856e1 * t489 * t1335 * t3048 * t481 - 0.58482236226346462072622386637590534819724553404280e0 * t489 * t472 * t3061 * t481 - 0.17315859105681463759666483083807725165579399831905e2 * t489 * t1357 * t3048 * t1360
  t3090 = f.my_piecewise3(t352, 0, t2961 * t406 / 0.2e1 + t1953 * t2010 + t408 * t3086 / 0.2e1)
  t3099 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t1389 * t2818 + 0.4e1 / 0.3e1 * t76 * t2812)
  t3105 = f.my_piecewise3(t80, 0, 0.4e1 / 0.9e1 * t1397 * t2966 + 0.4e1 / 0.3e1 * t81 * t2960)
  t3107 = (t3099 + t3105) * t88
  t3112 = -t1135 + t1139 - 0.36622894612013090109708692208757981924083909966068e-3 * t2494 - t1151 + 0.19751673498613801407483339618206552048944131217655e-1 * t3107 * t116 - t2942 - 0.8e1 * t2497 + 0.2e1 * t2520 + t1160 - t1187 - t1194 + t1204
  t3117 = -0.8e1 * t2524 + t128 * t3107 * t118 - t3090 - 0.11696447245269292414524477327518106963944910680856e1 * t2528 + t1421 - t1423 + t1479 - t1458 + t1483 + t1488 - t1492 + t1495 + t1498
  t3118 = t3112 + t3117
  t3130 = t777 ** 2
  t3148 = t2759 * t749
  t3153 = t755 / t767 * t760
  t3164 = t766 / t511 / t756 / t702 * t772
  t3175 = t2043 / t510 / t756 / t2674 * t2049
  t3183 = t756 ** 2
  t3192 = 0.88e2 / 0.9e1 * t737 * t2653 * t741 - 0.24e2 * t798 * t3148 + 0.128e3 / 0.9e1 * t1650 * t3153 + 0.304e3 / 0.9e1 * t746 * t3148 - 0.688e3 / 0.9e1 * t812 * t3153 + 0.128e3 / 0.3e1 * t1660 * t3164 + 0.72e2 * t754 * t3153 - 0.472e3 / 0.3e1 * t825 * t3164 + 0.256e3 / 0.3e1 * t1672 * t3175 + 0.1120e4 / 0.9e1 * t765 * t3164 - 0.800e3 / 0.3e1 * t839 * t3175 + 0.1280e4 / 0.9e1 * t1685 * t766 * t700 / t3183 / t509 / t771 / t748
  t3198 = t2015 * s2 * t2069 / 0.4e1 + t3090 * t718 * t725 + t3118 * t545 + t2058 * t2063 / 0.4e1 + t1950 * t2063 / 0.4e1 - 0.10e2 / 0.3e1 * t2067 * t2682 * t2077 - 0.80e2 / 0.3e1 * t2015 * t725 * t2078 - 0.1600e4 / 0.9e1 * t2073 * t3130 / t511 / t756 * t918 * t786 + 0.520e3 / 0.9e1 * t2073 * t777 * t705 * t2077 + t3118 * t732 + t3090 * t775 * t788 + t556 * t3192 * t788 + 0.2e1 * t2014 * t2053 * t788
  d22 = t7 * (t2956 + t3198) + 0.2e1 * t2059 + t2064 / 0.4e1 + 0.2e1 * t2095 + 0.2e1 * t2152 + 0.2e1 * t2096 - 0.80e2 / 0.3e1 * t2079 + 0.2e1 * t1951 + 0.2e1 * t1907 + 0.2e1 * t2016 + 0.2e1 * t2055 + 0.2e1 * t2124 + 0.2e1 * t2057 + t2070 / 0.4e1
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

