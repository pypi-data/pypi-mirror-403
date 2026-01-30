"""Generated from gga_c_pbe_erf_gws.mpl."""

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
  params_a_c_raw = params.a_c
  if isinstance(params_a_c_raw, (str, bytes, dict)):
    params_a_c = params_a_c_raw
  else:
    try:
      params_a_c_seq = list(params_a_c_raw)
    except TypeError:
      params_a_c = params_a_c_raw
    else:
      params_a_c_seq = np.asarray(params_a_c_seq, dtype=np.float64)
      params_a_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_c_seq))
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
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.031091, 0.015545, 0.016887], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.709921

  lda_c_pw_erf_mu = f.p.cam_omega

  lda_c_pw_erf_b0 = lambda rs: 0.784949 * rs

  lda_c_pw_erf_alpha = (4 / (9 * jnp.pi)) ** (1 / 3)

  lda_c_pw_erf_ac = 5.84605

  lda_c_pw_erf_c = 3.91744

  lda_c_pw_erf_d = 3.44851

  lda_c_pw_erf_phin = lambda n, z: 1 / 2 * ((1 + z) ** (n / 3) + (1 - z) ** (n / 3))

  lda_c_pw_erf_g0 = lambda rs: 1 / 2 * (1 + 0.0207 * rs + 0.08193 * rs ** 2 - 0.01277 * rs ** 3 + 0.001859 * rs ** 4) * jnp.exp(-0.7524 * rs)

  lda_c_pw_erf_D2 = lambda rs: jnp.exp(-0.547 * rs) * (-0.388 * rs + 0.676 * rs ** 2) / rs ** 2

  lda_c_pw_erf_D3 = lambda rs: jnp.exp(-0.31 * rs) * (-4.95 * rs + rs ** 2) / rs ** 3

  pbe_c_erf_gws_gamma = params_gamma

  pbe_c_erf_gws_beta_orig = params_beta

  pbe_c_erf_gws_a_c = params_a_c

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  lda_c_pw_erf_g1 = lambda rs: 2 ** (5 / 3) * (1 - 0.02267 * rs) / (5 * lda_c_pw_erf_alpha ** 2 * rs ** 2 * (1 + 0.4319 * rs + 0.04 * rs ** 2))

  lda_c_pw_erf_bc = lda_c_pw_erf_d - 3 * jnp.pi * lda_c_pw_erf_alpha / (4 * jnp.log(2) - 4)

  lda_c_pw_erf_g0c = lambda rs: lda_c_pw_erf_g0(rs) - 1 / 2

  lda_c_pw_erf_C3 = lambda rs, z: -(1 - z ** 2) * lda_c_pw_erf_g0(rs) / (jnp.sqrt(2 * jnp.pi) * rs ** 3)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  lda_c_pw_erf_c4_l = lambda rs, z: ((1 + z) / 2) ** 2 * lda_c_pw_erf_g1(rs * (2 / (1 + z)) ** (1 / 3)) + ((1 - z) / 2) ** 2 * lda_c_pw_erf_g1(rs * (2 / (1 - z)) ** (1 / 3)) + (1 - z ** 2) * lda_c_pw_erf_D2(rs) - lda_c_pw_erf_phin(8, z) / (5 * lda_c_pw_erf_alpha ** 2 * rs ** 2)

  lda_c_pw_erf_c5_l = lambda rs, z: ((1 + z) / 2) ** 2 * lda_c_pw_erf_g1(rs * (2 / (1 + z)) ** (1 / 3)) + ((1 - z) / 2) ** 2 * lda_c_pw_erf_g1(rs * (2 / (1 - z)) ** (1 / 3)) + (1 - z ** 2) * lda_c_pw_erf_D3(rs)

  lda_c_pw_erf_Q = lambda x: (2 * jnp.log(2) - 2) * jnp.log((1 + lda_c_pw_erf_ac * x + lda_c_pw_erf_bc * x ** 2 + lda_c_pw_erf_c * x ** 3) / (1 + lda_c_pw_erf_ac * x + lda_c_pw_erf_d * x ** 2)) / jnp.pi ** 2

  lda_c_pw_erf_C2 = lambda rs, z: -3 * (1 - z ** 2) * lda_c_pw_erf_g0c(rs) / (8 * rs ** 3)

  lda_c_pw_erf_a3 = lambda rs, z: lda_c_pw_erf_b0(rs) ** 8 * lda_c_pw_erf_C3(rs, z)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  lda_c_pw_erf_C4 = lambda rs, z: -9 * lda_c_pw_erf_c4_l(rs, z) / (64 * rs ** 3)

  lda_c_pw_erf_C5 = lambda rs, z: -9 * lda_c_pw_erf_c5_l(rs, z) / (40 * jnp.sqrt(2 * jnp.pi) * rs ** 3)

  lda_c_pw_erf_a4 = lambda rs, z: lda_c_pw_erf_b0(rs) ** 8 * lda_c_pw_erf_C2(rs, z) + 4 * lda_c_pw_erf_b0(rs) ** 6 * f_pw(rs, z)

  lda_c_pw_erf_a5 = lambda rs, z: lda_c_pw_erf_b0(rs) ** 8 * f_pw(rs, z)

  lda_c_pw_erf_a2 = lambda rs, z: 4 * lda_c_pw_erf_b0(rs) ** 6 * lda_c_pw_erf_C2(rs, z) + lda_c_pw_erf_b0(rs) ** 8 * lda_c_pw_erf_C4(rs, z) + 6 * lda_c_pw_erf_b0(rs) ** 4 * f_pw(rs, z)

  lda_c_pw_erf_a1 = lambda rs, z: 4 * lda_c_pw_erf_b0(rs) ** 6 * lda_c_pw_erf_C3(rs, z) + lda_c_pw_erf_b0(rs) ** 8 * lda_c_pw_erf_C5(rs, z)

  lda_c_pw_erf_f = lambda rs, z: f_pw(rs, z) - (lda_c_pw_erf_phin(2, z) ** 3 * lda_c_pw_erf_Q(lda_c_pw_erf_mu * jnp.sqrt(rs) / lda_c_pw_erf_phin(2, z)) + lda_c_pw_erf_a1(rs, z) * lda_c_pw_erf_mu ** 3 + lda_c_pw_erf_a2(rs, z) * lda_c_pw_erf_mu ** 4 + lda_c_pw_erf_a3(rs, z) * lda_c_pw_erf_mu ** 5 + lda_c_pw_erf_a4(rs, z) * lda_c_pw_erf_mu ** 6 + lda_c_pw_erf_a5(rs, z) * lda_c_pw_erf_mu ** 8) / (1 + lda_c_pw_erf_b0(rs) ** 2 * lda_c_pw_erf_mu ** 2) ** 4

  pbe_c_erf_gws_beta = lambda rs, z: pbe_c_erf_gws_beta_orig * (lda_c_pw_erf_f(rs, z) / f_pw(rs, z)) ** pbe_c_erf_gws_a_c

  pbe_c_erf_gws_A = lambda rs, z: pbe_c_erf_gws_beta(rs, z) / (pbe_c_erf_gws_gamma * (jnp.exp(-lda_c_pw_erf_f(rs, z) / (f.mphi(z) ** 3 * pbe_c_erf_gws_gamma)) - 1))

  pbe_c_erf_gws_H = lambda rs, z, t: pbe_c_erf_gws_gamma * f.mphi(z) ** 3 * jnp.log(1 + pbe_c_erf_gws_beta(rs, z) * t ** 2 / pbe_c_erf_gws_gamma * ((1 + pbe_c_erf_gws_A(rs, z) * t ** 2) / (1 + pbe_c_erf_gws_A(rs, z) * t ** 2 + pbe_c_erf_gws_A(rs, z) ** 2 * t ** 4)))

  functional_body = lambda rs, z, xt, xs0=None, xs1=None: lda_c_pw_erf_f(rs, z) + pbe_c_erf_gws_H(rs, z, f.tt(rs, z, xt))

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
  params_a_c_raw = params.a_c
  if isinstance(params_a_c_raw, (str, bytes, dict)):
    params_a_c = params_a_c_raw
  else:
    try:
      params_a_c_seq = list(params_a_c_raw)
    except TypeError:
      params_a_c = params_a_c_raw
    else:
      params_a_c_seq = np.asarray(params_a_c_seq, dtype=np.float64)
      params_a_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_c_seq))
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
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.031091, 0.015545, 0.016887], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.709921

  lda_c_pw_erf_mu = f.p.cam_omega

  lda_c_pw_erf_b0 = lambda rs: 0.784949 * rs

  lda_c_pw_erf_alpha = (4 / (9 * jnp.pi)) ** (1 / 3)

  lda_c_pw_erf_ac = 5.84605

  lda_c_pw_erf_c = 3.91744

  lda_c_pw_erf_d = 3.44851

  lda_c_pw_erf_phin = lambda n, z: 1 / 2 * ((1 + z) ** (n / 3) + (1 - z) ** (n / 3))

  lda_c_pw_erf_g0 = lambda rs: 1 / 2 * (1 + 0.0207 * rs + 0.08193 * rs ** 2 - 0.01277 * rs ** 3 + 0.001859 * rs ** 4) * jnp.exp(-0.7524 * rs)

  lda_c_pw_erf_D2 = lambda rs: jnp.exp(-0.547 * rs) * (-0.388 * rs + 0.676 * rs ** 2) / rs ** 2

  lda_c_pw_erf_D3 = lambda rs: jnp.exp(-0.31 * rs) * (-4.95 * rs + rs ** 2) / rs ** 3

  pbe_c_erf_gws_gamma = params_gamma

  pbe_c_erf_gws_beta_orig = params_beta

  pbe_c_erf_gws_a_c = params_a_c

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  lda_c_pw_erf_g1 = lambda rs: 2 ** (5 / 3) * (1 - 0.02267 * rs) / (5 * lda_c_pw_erf_alpha ** 2 * rs ** 2 * (1 + 0.4319 * rs + 0.04 * rs ** 2))

  lda_c_pw_erf_bc = lda_c_pw_erf_d - 3 * jnp.pi * lda_c_pw_erf_alpha / (4 * jnp.log(2) - 4)

  lda_c_pw_erf_g0c = lambda rs: lda_c_pw_erf_g0(rs) - 1 / 2

  lda_c_pw_erf_C3 = lambda rs, z: -(1 - z ** 2) * lda_c_pw_erf_g0(rs) / (jnp.sqrt(2 * jnp.pi) * rs ** 3)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  lda_c_pw_erf_c4_l = lambda rs, z: ((1 + z) / 2) ** 2 * lda_c_pw_erf_g1(rs * (2 / (1 + z)) ** (1 / 3)) + ((1 - z) / 2) ** 2 * lda_c_pw_erf_g1(rs * (2 / (1 - z)) ** (1 / 3)) + (1 - z ** 2) * lda_c_pw_erf_D2(rs) - lda_c_pw_erf_phin(8, z) / (5 * lda_c_pw_erf_alpha ** 2 * rs ** 2)

  lda_c_pw_erf_c5_l = lambda rs, z: ((1 + z) / 2) ** 2 * lda_c_pw_erf_g1(rs * (2 / (1 + z)) ** (1 / 3)) + ((1 - z) / 2) ** 2 * lda_c_pw_erf_g1(rs * (2 / (1 - z)) ** (1 / 3)) + (1 - z ** 2) * lda_c_pw_erf_D3(rs)

  lda_c_pw_erf_Q = lambda x: (2 * jnp.log(2) - 2) * jnp.log((1 + lda_c_pw_erf_ac * x + lda_c_pw_erf_bc * x ** 2 + lda_c_pw_erf_c * x ** 3) / (1 + lda_c_pw_erf_ac * x + lda_c_pw_erf_d * x ** 2)) / jnp.pi ** 2

  lda_c_pw_erf_C2 = lambda rs, z: -3 * (1 - z ** 2) * lda_c_pw_erf_g0c(rs) / (8 * rs ** 3)

  lda_c_pw_erf_a3 = lambda rs, z: lda_c_pw_erf_b0(rs) ** 8 * lda_c_pw_erf_C3(rs, z)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  lda_c_pw_erf_C4 = lambda rs, z: -9 * lda_c_pw_erf_c4_l(rs, z) / (64 * rs ** 3)

  lda_c_pw_erf_C5 = lambda rs, z: -9 * lda_c_pw_erf_c5_l(rs, z) / (40 * jnp.sqrt(2 * jnp.pi) * rs ** 3)

  lda_c_pw_erf_a4 = lambda rs, z: lda_c_pw_erf_b0(rs) ** 8 * lda_c_pw_erf_C2(rs, z) + 4 * lda_c_pw_erf_b0(rs) ** 6 * f_pw(rs, z)

  lda_c_pw_erf_a5 = lambda rs, z: lda_c_pw_erf_b0(rs) ** 8 * f_pw(rs, z)

  lda_c_pw_erf_a2 = lambda rs, z: 4 * lda_c_pw_erf_b0(rs) ** 6 * lda_c_pw_erf_C2(rs, z) + lda_c_pw_erf_b0(rs) ** 8 * lda_c_pw_erf_C4(rs, z) + 6 * lda_c_pw_erf_b0(rs) ** 4 * f_pw(rs, z)

  lda_c_pw_erf_a1 = lambda rs, z: 4 * lda_c_pw_erf_b0(rs) ** 6 * lda_c_pw_erf_C3(rs, z) + lda_c_pw_erf_b0(rs) ** 8 * lda_c_pw_erf_C5(rs, z)

  lda_c_pw_erf_f = lambda rs, z: f_pw(rs, z) - (lda_c_pw_erf_phin(2, z) ** 3 * lda_c_pw_erf_Q(lda_c_pw_erf_mu * jnp.sqrt(rs) / lda_c_pw_erf_phin(2, z)) + lda_c_pw_erf_a1(rs, z) * lda_c_pw_erf_mu ** 3 + lda_c_pw_erf_a2(rs, z) * lda_c_pw_erf_mu ** 4 + lda_c_pw_erf_a3(rs, z) * lda_c_pw_erf_mu ** 5 + lda_c_pw_erf_a4(rs, z) * lda_c_pw_erf_mu ** 6 + lda_c_pw_erf_a5(rs, z) * lda_c_pw_erf_mu ** 8) / (1 + lda_c_pw_erf_b0(rs) ** 2 * lda_c_pw_erf_mu ** 2) ** 4

  pbe_c_erf_gws_beta = lambda rs, z: pbe_c_erf_gws_beta_orig * (lda_c_pw_erf_f(rs, z) / f_pw(rs, z)) ** pbe_c_erf_gws_a_c

  pbe_c_erf_gws_A = lambda rs, z: pbe_c_erf_gws_beta(rs, z) / (pbe_c_erf_gws_gamma * (jnp.exp(-lda_c_pw_erf_f(rs, z) / (f.mphi(z) ** 3 * pbe_c_erf_gws_gamma)) - 1))

  pbe_c_erf_gws_H = lambda rs, z, t: pbe_c_erf_gws_gamma * f.mphi(z) ** 3 * jnp.log(1 + pbe_c_erf_gws_beta(rs, z) * t ** 2 / pbe_c_erf_gws_gamma * ((1 + pbe_c_erf_gws_A(rs, z) * t ** 2) / (1 + pbe_c_erf_gws_A(rs, z) * t ** 2 + pbe_c_erf_gws_A(rs, z) ** 2 * t ** 4)))

  functional_body = lambda rs, z, xt, xs0=None, xs1=None: lda_c_pw_erf_f(rs, z) + pbe_c_erf_gws_H(rs, z, f.tt(rs, z, xt))

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

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t9 = 0.1e1 / t8
  t10 = t6 * t9
  t11 = t4 * t10
  t13 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t11
  t14 = jnp.sqrt(t11)
  t17 = t11 ** 0.15e1
  t19 = t1 ** 2
  t20 = t3 ** 2
  t21 = t19 * t20
  t22 = t8 ** 2
  t23 = 0.1e1 / t22
  t24 = t5 * t23
  t25 = t21 * t24
  t27 = 0.37978500000000000000000000000000000000000000000000e1 * t14 + 0.89690000000000000000000000000000000000000000000000e0 * t11 + 0.20477500000000000000000000000000000000000000000000e0 * t17 + 0.12323500000000000000000000000000000000000000000000e0 * t25
  t30 = 0.1e1 + 0.16081824322151104821330931780901225435013347914188e2 / t27
  t31 = jnp.log(t30)
  t33 = 0.62182e-1 * t13 * t31
  t34 = r0 - r1
  t35 = t34 ** 2
  t36 = t35 ** 2
  t37 = t7 ** 2
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t40 = t36 * t39
  t41 = 0.1e1 / t7
  t42 = t34 * t41
  t43 = 0.1e1 + t42
  t44 = t43 <= f.p.zeta_threshold
  t45 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t46 = t45 * f.p.zeta_threshold
  t47 = t43 ** (0.1e1 / 0.3e1)
  t49 = f.my_piecewise3(t44, t46, t47 * t43)
  t50 = 0.1e1 - t42
  t51 = t50 <= f.p.zeta_threshold
  t52 = t50 ** (0.1e1 / 0.3e1)
  t54 = f.my_piecewise3(t51, t46, t52 * t50)
  t56 = 2 ** (0.1e1 / 0.3e1)
  t59 = 0.1e1 / (0.2e1 * t56 - 0.2e1)
  t60 = (t49 + t54 - 0.2e1) * t59
  t62 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t11
  t67 = 0.70594500000000000000000000000000000000000000000000e1 * t14 + 0.15494250000000000000000000000000000000000000000000e1 * t11 + 0.42077500000000000000000000000000000000000000000000e0 * t17 + 0.15629250000000000000000000000000000000000000000000e0 * t25
  t70 = 0.1e1 + 0.32164683177870697973624959794146027661627532968800e2 / t67
  t71 = jnp.log(t70)
  t75 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t11
  t80 = 0.51785000000000000000000000000000000000000000000000e1 * t14 + 0.90577500000000000000000000000000000000000000000000e0 * t11 + 0.11003250000000000000000000000000000000000000000000e0 * t17 + 0.12417750000000000000000000000000000000000000000000e0 * t25
  t83 = 0.1e1 + 0.29608574643216675549239059631669331438384556167466e2 / t80
  t84 = jnp.log(t83)
  t85 = t75 * t84
  t87 = -0.31090e-1 * t62 * t71 + t33 - 0.19751789702565206228825776161588751761046270558698e-1 * t85
  t88 = t60 * t87
  t89 = t40 * t88
  t91 = 0.19751789702565206228825776161588751761046270558698e-1 * t60 * t85
  t92 = t47 ** 2
  t93 = t52 ** 2
  t95 = t92 / 0.2e1 + t93 / 0.2e1
  t96 = t95 ** 2
  t97 = t96 * t95
  t98 = jnp.log(0.2e1)
  t99 = t98 - 0.1e1
  t100 = 0.2e1 * t99
  t101 = t97 * t100
  t102 = f.p.cam_omega * t14
  t103 = 0.1e1 / t95
  t105 = 0.29230250000000000000000000000000000000000000000000e1 * t102 * t103
  t107 = 9 ** (0.1e1 / 0.3e1)
  t108 = t107 ** 2
  t116 = f.p.cam_omega ** 2
  t117 = (0.344851e1 - jnp.pi * t5 * t108 * t3 / t99 / 0.12e2) * t116
  t118 = t117 * t1
  t119 = t3 * t6
  t120 = 0.1e1 / t96
  t125 = t116 * f.p.cam_omega
  t127 = t125 * t14 * t11
  t128 = 0.1e1 / t97
  t131 = 0.1e1 + t105 + t118 * t119 * t9 * t120 / 0.4e1 + 0.48968000000000000000000000000000000000000000000000e0 * t127 * t128
  t133 = t116 * t1 * t3
  t137 = 0.1e1 + t105 + 0.86212750000000000000000000000000000000000000000000e0 * t133 * t10 * t120
  t138 = 0.1e1 / t137
  t140 = jnp.log(t131 * t138)
  t141 = jnp.pi ** 2
  t142 = 0.1e1 / t141
  t143 = t140 * t142
  t145 = jnp.sqrt(jnp.pi)
  t147 = 0.1e1 / t145 / jnp.pi
  t148 = t147 * t41
  t149 = 0.1e1 / t37
  t151 = -t35 * t149 + 0.1e1
  t152 = t148 * t151
  t155 = t2 * t41
  t157 = t3 * t2
  t158 = t1 * t157
  t160 = 0.1e1 / t8 / t7
  t161 = t6 * t160
  t164 = 0.1e1 + 0.51750000000000000000000000000000000000000000000000e-2 * t11 + 0.20482500000000000000000000000000000000000000000000e-1 * t25 - 0.95775000000000000000000000000000000000000000000000e-2 * t155 + 0.34856250000000000000000000000000000000000000000000e-3 * t158 * t161
  t166 = jnp.exp(-0.18810000000000000000000000000000000000000000000000e0 * t11)
  t167 = t164 * t166
  t168 = jnp.sqrt(0.2e1)
  t169 = t167 * t168
  t173 = t19 * t20 * t142
  t174 = t173 * t5
  t176 = 0.1e1 / t22 / t7
  t177 = t43 / 0.2e1
  t178 = t177 ** 2
  t179 = t4 * t6
  t180 = t9 * t56
  t181 = 0.1e1 / t43
  t182 = t181 ** (0.1e1 / 0.3e1)
  t184 = t179 * t180 * t182
  t186 = 0.1e1 - 0.56675000000000000000000000000000000000000000000000e-2 * t184
  t187 = t178 * t186
  t188 = 0.1e1 / t157
  t189 = t108 * t188
  t190 = t187 * t189
  t191 = t1 * t22
  t192 = t182 ** 2
  t193 = 0.1e1 / t192
  t195 = t21 * t5
  t196 = t56 ** 2
  t197 = t23 * t196
  t201 = 0.1e1 + 0.10797500000000000000000000000000000000000000000000e0 * t184 + 0.10000000000000000000000000000000000000000000000000e-1 * t195 * t197 * t192
  t202 = 0.1e1 / t201
  t203 = t193 * t202
  t204 = t191 * t203
  t206 = 0.2e1 / 0.15e2 * t190 * t204
  t207 = t50 / 0.2e1
  t208 = t207 ** 2
  t209 = 0.1e1 / t50
  t210 = t209 ** (0.1e1 / 0.3e1)
  t212 = t179 * t180 * t210
  t214 = 0.1e1 - 0.56675000000000000000000000000000000000000000000000e-2 * t212
  t215 = t208 * t214
  t216 = t215 * t189
  t217 = t210 ** 2
  t218 = 0.1e1 / t217
  t223 = 0.1e1 + 0.10797500000000000000000000000000000000000000000000e0 * t212 + 0.10000000000000000000000000000000000000000000000000e-1 * t195 * t197 * t217
  t224 = 0.1e1 / t223
  t225 = t218 * t224
  t226 = t191 * t225
  t228 = 0.2e1 / 0.15e2 * t216 * t226
  t230 = jnp.exp(-0.77500000000000000000000000000000000000000000000000e-1 * t11)
  t231 = t151 * t230
  t235 = (-0.12375000000000000000000000000000000000000000000000e1 * t11 + t25 / 0.4e1) * jnp.pi
  t236 = t235 * t7
  t239 = t206 + t228 + 0.4e1 / 0.3e1 * t231 * t236
  t241 = t168 * t145
  t248 = t167 / 0.2e1 - 0.1e1 / 0.2e1
  t249 = t151 * t248
  t253 = jnp.exp(-0.13675000000000000000000000000000000000000000000000e0 * t11)
  t254 = t151 * t253
  t257 = -0.97000000000000000000000000000000000000000000000000e-1 * t11 + 0.16900000000000000000000000000000000000000000000000e0 * t25
  t258 = t254 * t257
  t259 = 0.1e1 / t20
  t260 = t1 * t259
  t262 = t260 * t6 * t22
  t265 = t43 ** 2
  t267 = t50 ** 2
  t271 = (t92 * t265 / 0.2e1 + t93 * t267 / 0.2e1) * t108
  t272 = t188 * t1
  t273 = t272 * t22
  t276 = t206 + t228 + t258 * t262 / 0.3e1 - t271 * t273 / 0.15e2
  t281 = -t33 + t89 + t91
  t286 = t116 ** 2
  t288 = t5 * t176
  t290 = t173 * t288 * t151
  t291 = t286 * f.p.cam_omega
  t292 = t241 * t291
  t293 = t167 * t292
  t296 = t176 * t151
  t297 = t248 * jnp.pi
  t301 = t142 * t149
  t305 = t286 * t116
  t308 = 0.1e1 / t22 / t37
  t310 = t286 ** 2
  t314 = t101 * t143 + (-0.17543244109220059985638668152930835075000000000000e0 * t152 * t169 - 0.30400821447970174150861446235388365887845217506462e-2 * t174 * t176 * t239 * t241) * t125 + (-0.26314866163830089978458002229396252612500000000000e0 * t155 * t249 - 0.38001026809962717688576807794235457359806521883077e-2 * t174 * t176 * t276 * jnp.pi + 0.42708890021612718670335112500000000000000000000000e0 * t158 * t161 * t281) * t286 - 0.67557380995489275890803213856418590861878261125470e-2 * t290 * t293 + (-0.10133607149323391383620482078462788629281739168820e-1 * t174 * t296 * t297 + 0.52629732327660179956916004458792505225000000000000e0 * t301 * t281) * t305 + 0.20267214298646782767240964156925577258563478337641e-1 * t174 * t308 * t281 * t310
  t318 = 0.1e1 + 0.15403623315025000000000000000000000000000000000000e0 * t21 * t24 * t116
  t319 = t318 ** 2
  t320 = t319 ** 2
  t321 = 0.1e1 / t320
  t322 = t314 * t321
  t323 = t45 ** 2
  t324 = f.my_piecewise3(t44, t323, t92)
  t325 = f.my_piecewise3(t51, t323, t93)
  t327 = t324 / 0.2e1 + t325 / 0.2e1
  t328 = t327 ** 2
  t329 = t328 * t327
  t330 = params.gamma * t329
  t331 = -t33 + t89 + t91 - t322
  t332 = 0.1e1 / t281
  t334 = (t331 * t332) ** params.a_c
  t335 = params.beta * t334
  t337 = s0 + 0.2e1 * s1 + s2
  t338 = t335 * t337
  t340 = 0.1e1 / t8 / t37
  t341 = t340 * t56
  t342 = 0.1e1 / t328
  t343 = t341 * t342
  t344 = t338 * t343
  t345 = 0.1e1 / t3
  t346 = t19 * t345
  t347 = t346 * t5
  t348 = 0.1e1 / params.gamma
  t349 = 0.1e1 / t329
  t352 = jnp.exp(-t331 * t349 * t348)
  t353 = t352 - 0.1e1
  t354 = 0.1e1 / t353
  t355 = t348 * t354
  t357 = t335 * t355 * t337
  t360 = t357 * t343 * t347 / 0.96e2
  t361 = 0.1e1 + t360
  t362 = t348 * t361
  t363 = params.beta ** 2
  t364 = t334 ** 2
  t365 = t363 * t364
  t366 = params.gamma ** 2
  t367 = 0.1e1 / t366
  t368 = t353 ** 2
  t369 = 0.1e1 / t368
  t370 = t367 * t369
  t371 = t337 ** 2
  t373 = t365 * t370 * t371
  t375 = 0.1e1 / t22 / t38
  t376 = t375 * t196
  t377 = t328 ** 2
  t378 = 0.1e1 / t377
  t379 = t376 * t378
  t380 = t260 * t6
  t381 = t379 * t380
  t384 = 0.1e1 + t360 + t373 * t381 / 0.3072e4
  t385 = 0.1e1 / t384
  t387 = t347 * t362 * t385
  t390 = 0.1e1 + t344 * t387 / 0.96e2
  t391 = jnp.log(t390)
  t392 = t330 * t391
  t395 = 0.11073577833333333333333333333333333333333333333333e-2 * t4 * t161 * t31
  t396 = t27 ** 2
  t399 = 0.1e1 / t14
  t401 = t119 * t160
  t402 = t399 * t1 * t401
  t404 = t4 * t161
  t406 = t11 ** 0.5e0
  t408 = t406 * t1 * t401
  t410 = t21 * t288
  t416 = 0.10000000000000000000000000000000000000000000000000e1 * t13 / t396 * (-0.63297500000000000000000000000000000000000000000000e0 * t402 - 0.29896666666666666666666666666666666666666666666667e0 * t404 - 0.10238750000000000000000000000000000000000000000000e0 * t408 - 0.82156666666666666666666666666666666666666666666667e-1 * t410) / t30
  t420 = 0.4e1 * t35 * t34 * t39 * t88
  t421 = t38 * t7
  t425 = 0.4e1 * t36 / t421 * t88
  t426 = t34 * t149
  t427 = t41 - t426
  t430 = f.my_piecewise3(t44, 0, 0.4e1 / 0.3e1 * t47 * t427)
  t431 = -t427
  t434 = f.my_piecewise3(t51, 0, 0.4e1 / 0.3e1 * t52 * t431)
  t436 = (t430 + t434) * t59
  t438 = t40 * t436 * t87
  t442 = t67 ** 2
  t457 = t80 ** 2
  t458 = 0.1e1 / t457
  t464 = -0.86308333333333333333333333333333333333333333333334e0 * t402 - 0.30192500000000000000000000000000000000000000000000e0 * t404 - 0.55016250000000000000000000000000000000000000000000e-1 * t408 - 0.82785000000000000000000000000000000000000000000000e-1 * t410
  t465 = 0.1e1 / t83
  t471 = t40 * t60 * (0.53236443333333333333333333333333333333333333333332e-3 * t4 * t161 * t71 + 0.99999999999999999999999999999999999999999999999999e0 * t62 / t442 * (-0.11765750000000000000000000000000000000000000000000e1 * t402 - 0.51647500000000000000000000000000000000000000000000e0 * t404 - 0.21038750000000000000000000000000000000000000000000e0 * t408 - 0.10419500000000000000000000000000000000000000000000e0 * t410) / t70 - t395 - t416 + 0.18311555036753159941307229983139571945136646663793e-3 * t4 * t161 * t84 + 0.58482233974552040708313425006184496242808878304903e0 * t75 * t458 * t464 * t465)
  t473 = 0.19751789702565206228825776161588751761046270558698e-1 * t436 * t85
  t478 = 0.18311555036753159941307229983139571945136646663793e-3 * t60 * t1 * t119 * t160 * t84
  t483 = 0.58482233974552040708313425006184496242808878304903e0 * t60 * t75 * t458 * t464 * t465
  t484 = t96 * t100
  t485 = 0.1e1 / t47
  t486 = t485 * t427
  t487 = 0.1e1 / t52
  t488 = t487 * t431
  t490 = t486 / 0.3e1 + t488 / 0.3e1
  t497 = 0.48717083333333333333333333333333333333333333333333e0 * f.p.cam_omega * t399 * t103 * t404
  t500 = 0.29230250000000000000000000000000000000000000000000e1 * t102 * t120 * t490
  t504 = t118 * t119 * t160 * t120 / 0.12e2
  t505 = t117 * t4
  t507 = t10 * t128 * t490
  t513 = 0.24484000000000000000000000000000000000000000000000e0 * t125 * t14 * t128 * t404
  t514 = t96 ** 2
  t515 = 0.1e1 / t514
  t521 = t137 ** 2
  t523 = t131 / t521
  t526 = 0.28737583333333333333333333333333333333333333333333e0 * t133 * t161 * t120
  t535 = 0.1e1 / t131 * t137 * t142
  t540 = 0.17543244109220059985638668152930835075000000000000e0 * t147 * t149 * t151 * t169
  t541 = t37 * t7
  t542 = 0.1e1 / t541
  t543 = t35 * t542
  t545 = -0.2e1 * t426 + 0.2e1 * t543
  t551 = t2 * t149
  t553 = t6 * t340
  t557 = (-0.17250000000000000000000000000000000000000000000000e-2 * t404 - 0.13655000000000000000000000000000000000000000000000e-1 * t410 + 0.95775000000000000000000000000000000000000000000000e-2 * t551 - 0.46475000000000000000000000000000000000000000000000e-3 * t158 * t553) * t166
  t560 = 0.17543244109220059985638668152930835075000000000000e0 * t152 * t557 * t168
  t568 = 0.10999614056480977610995444931887633592025000000000e-1 * t147 * t340 * t151 * t164 * t4 * t6 * t166 * t168
  t572 = 0.50668035746616956918102410392313943146408695844103e-2 * t174 * t308 * t239 * t241
  t574 = t177 * t186 * t189
  t575 = t427 / 0.2e1
  t579 = 0.4e1 / 0.15e2 * t574 * t191 * t203 * t575
  t580 = t160 * t56
  t582 = t179 * t580 * t182
  t583 = 0.18891666666666666666666666666666666666666666666667e-2 * t582
  t584 = t56 * t193
  t585 = 0.1e1 / t265
  t586 = t585 * t427
  t588 = t11 * t584 * t586
  t594 = 0.2e1 / 0.15e2 * t178 * (t583 + 0.18891666666666666666666666666666666666666666666667e-2 * t588) * t189 * t204
  t595 = t1 * t9
  t598 = 0.4e1 / 0.45e2 * t190 * t595 * t203
  t599 = t189 * t1
  t600 = t187 * t599
  t603 = t22 / t192 / t181
  t604 = t202 * t585
  t608 = 0.4e1 / 0.45e2 * t600 * t603 * t604 * t427
  t609 = t201 ** 2
  t611 = t193 / t609
  t612 = 0.35991666666666666666666666666666666666666666666667e-1 * t582
  t614 = t176 * t196
  t617 = 0.66666666666666666666666666666666666666666666666667e-2 * t195 * t614 * t192
  t619 = t196 / t182
  t627 = 0.2e1 / 0.15e2 * t190 * t191 * t611 * (-t612 - 0.35991666666666666666666666666666666666666666666667e-1 * t588 - t617 - 0.66666666666666666666666666666666666666666666666667e-2 * t25 * t619 * t586)
  t629 = t207 * t214 * t189
  t634 = -0.4e1 / 0.15e2 * t629 * t191 * t225 * t575
  t636 = t179 * t580 * t210
  t637 = 0.18891666666666666666666666666666666666666666666667e-2 * t636
  t638 = t56 * t218
  t639 = 0.1e1 / t267
  t640 = t639 * t431
  t642 = t11 * t638 * t640
  t648 = 0.2e1 / 0.15e2 * t208 * (t637 + 0.18891666666666666666666666666666666666666666666667e-2 * t642) * t189 * t226
  t651 = 0.4e1 / 0.45e2 * t216 * t595 * t225
  t652 = t215 * t599
  t655 = t22 / t217 / t209
  t656 = t224 * t639
  t660 = 0.4e1 / 0.45e2 * t652 * t655 * t656 * t431
  t661 = t223 ** 2
  t663 = t218 / t661
  t664 = 0.35991666666666666666666666666666666666666666666667e-1 * t636
  t668 = 0.66666666666666666666666666666666666666666666666667e-2 * t195 * t614 * t217
  t670 = t196 / t210
  t678 = 0.2e1 / 0.15e2 * t216 * t191 * t663 * (-t664 - 0.35991666666666666666666666666666666666666666666667e-1 * t642 - t668 - 0.66666666666666666666666666666666666666666666666667e-2 * t25 * t670 * t640)
  t687 = 0.34444444444444444444444444444444444444444444444444e-1 * t151 * t1 * t119 * t9 * t230 * t235
  t694 = 0.4e1 / 0.3e1 * t231 * (0.41250000000000000000000000000000000000000000000000e0 * t404 - t410 / 0.6e1) * jnp.pi * t7
  t696 = 0.4e1 / 0.3e1 * t231 * t235
  t697 = t579 + t594 + t598 + t608 - t627 + t634 + t648 + t651 + t660 - t678 + 0.4e1 / 0.3e1 * t545 * t230 * t236 + t687 + t694 + t696
  t705 = 0.26314866163830089978458002229396252612500000000000e0 * t551 * t249
  t715 = t557 / 0.2e1 + 0.31350000000000000000000000000000000000000000000000e-1 * t164 * t1 * t3 * t161 * t166
  t718 = 0.26314866163830089978458002229396252612500000000000e0 * t155 * t151 * t715
  t722 = 0.63335044683271196147628012990392428933010869805128e-2 * t174 * t308 * t276 * jnp.pi
  t732 = 0.60777777777777777777777777777777777777777777777777e-1 * t151 * t19 * t345 * t24 * t253 * t257
  t738 = t254 * (0.32333333333333333333333333333333333333333333333333e-1 * t404 - 0.11266666666666666666666666666666666666666666666667e0 * t410) * t262 / 0.3e1
  t741 = 0.2e1 / 0.9e1 * t258 * t260 * t10
  t742 = t92 * t43
  t744 = t93 * t50
  t753 = 0.2e1 / 0.45e2 * t271 * t272 * t9
  t754 = t579 + t594 + t598 + t608 - t627 + t634 + t648 + t651 + t660 - t678 + t545 * t253 * t257 * t262 / 0.3e1 + t732 + t738 + t741 - (0.4e1 / 0.3e1 * t742 * t427 + 0.4e1 / 0.3e1 * t744 * t431) * t108 * t273 / 0.15e2 - t753
  t761 = 0.56945186695483624893780150000000000000000000000000e0 * t158 * t553 * t281
  t762 = t395 + t416 + t420 - t425 + t438 + t471 + t473 - t478 - t483
  t772 = 0.11259563499248212648467202309403098476979710187578e-1 * t173 * t5 * t308 * t151 * t293
  t779 = 0.67557380995489275890803213856418590861878261125470e-2 * t290 * t557 * t292
  t787 = 0.50830173461006131180240338105569347764477203670804e-2 / t145 / t141 * t542 * t151 * t167 * t168 * t291
  t791 = 0.16889345248872318972700803464104647715469565281367e-1 * t174 * t308 * t151 * t297
  t799 = 0.10133607149323391383620482078462788629281739168820e-1 * t174 * t296 * t715 * jnp.pi
  t802 = 0.10525946465532035991383200891758501045000000000000e1 * t142 * t542 * t281
  t812 = 0.54045904796391420712642571085134872689502608900376e-1 * t174 / t22 / t541 * t281 * t310
  t817 = 0.3e1 * t484 * t143 * t490 + t101 * ((-t497 - t500 - t504 - t505 * t507 / 0.2e1 - t513 - 0.14690400000000000000000000000000000000000000000000e1 * t127 * t515 * t490) * t138 - t523 * (-t497 - t500 - t526 - 0.17242550000000000000000000000000000000000000000000e1 * t133 * t507)) * t535 + (t540 - 0.17543244109220059985638668152930835075000000000000e0 * t148 * t545 * t169 - t560 - t568 + t572 - 0.30400821447970174150861446235388365887845217506462e-2 * t174 * t176 * t697 * t241) * t125 + (t705 - 0.26314866163830089978458002229396252612500000000000e0 * t155 * t545 * t248 - t718 + t722 - 0.38001026809962717688576807794235457359806521883077e-2 * t174 * t176 * t754 * jnp.pi - t761 + 0.42708890021612718670335112500000000000000000000000e0 * t158 * t161 * t762) * t286 + t772 - 0.67557380995489275890803213856418590861878261125470e-2 * t173 * t288 * t545 * t293 - t779 - t787 + (t791 - 0.10133607149323391383620482078462788629281739168820e-1 * t174 * t176 * t545 * t297 - t799 - t802 + 0.52629732327660179956916004458792505225000000000000e0 * t301 * t762) * t305 - t812 + 0.20267214298646782767240964156925577258563478337641e-1 * t174 * t308 * t762 * t310
  t818 = t817 * t321
  t827 = 0.41076328840066666666666666666666666666666666666668e0 * t314 / t320 / t318 * t19 * t20 * t5 * t176 * t116
  t828 = params.gamma * t328
  t830 = f.my_piecewise3(t44, 0, 0.2e1 / 0.3e1 * t486)
  t832 = f.my_piecewise3(t51, 0, 0.2e1 / 0.3e1 * t488)
  t834 = t830 / 0.2e1 + t832 / 0.2e1
  t838 = t395 + t416 + t420 - t425 + t438 + t471 + t473 - t478 - t483 - t818 - t827
  t840 = t281 ** 2
  t842 = t331 / t840
  t844 = t838 * t332 - t842 * t762
  t845 = params.a_c * t844
  t847 = 0.1e1 / t331
  t848 = t847 * t281
  t850 = t848 * t337 * t340
  t852 = t56 * t342
  t857 = t852 * t346 * t5 * t348 * t361 * t385
  t863 = 0.1e1 / t8 / t541 * t56 * t342
  t866 = 0.7e1 / 0.288e3 * t338 * t863 * t387
  t868 = t338 * t341 * t349
  t874 = t335 * params.a_c
  t876 = t281 * t348
  t879 = t354 * t337
  t882 = t345 * t5
  t884 = t879 * t341 * t342 * t19 * t882
  t886 = t874 * t844 * t847 * t876 * t884 / 0.96e2
  t887 = t335 * t348
  t890 = t887 * t369 * t337 * t340
  t891 = t852 * t19
  t894 = t331 * t378
  t899 = (-t348 * t349 * t838 + 0.3e1 * t348 * t834 * t894) * t352
  t903 = t890 * t891 * t882 * t899 / 0.96e2
  t906 = 0.7e1 / 0.288e3 * t357 * t863 * t347
  t908 = t887 * t879 * t340
  t910 = t56 * t349 * t19
  t914 = t908 * t910 * t882 * t834 / 0.48e2
  t921 = t384 ** 2
  t922 = 0.1e1 / t921
  t923 = t365 * t367
  t924 = t369 * t371
  t926 = t923 * t924 * t376
  t928 = t259 * t6
  t929 = t378 * t1 * t928
  t938 = t923 / t368 / t353 * t371 * t375
  t940 = t196 * t378 * t1
  t951 = 0.7e1 / 0.4608e4 * t373 / t22 / t421 * t196 * t378 * t380
  t953 = t923 * t924 * t375
  t957 = t196 / t377 / t327 * t1
  t969 = 0.1e1 / t390
  t972 = t395 + t416 + t420 - t425 + t438 + t471 + t473 - t478 - t483 - t818 - t827 + 0.3e1 * t828 * t391 * t834 + t330 * (t335 * t845 * t850 * t857 / 0.96e2 - t866 - t868 * t347 * t362 * t385 * t834 / 0.48e2 + t344 * t347 * t348 * (t886 - t903 - t906 - t914) * t385 / 0.96e2 - t344 * t347 * t362 * t922 * (t886 - t903 - t906 - t914 + t926 * t929 * t845 * t848 / 0.1536e4 - t938 * t940 * t928 * t899 / 0.1536e4 - t951 - t953 * t957 * t928 * t834 / 0.768e3) / 0.96e2) * t969
  vrho_0_ = t7 * t972 - t322 - t33 + t392 + t89 + t91
  t974 = -t41 - t426
  t977 = f.my_piecewise3(t44, 0, 0.4e1 / 0.3e1 * t47 * t974)
  t978 = -t974
  t981 = f.my_piecewise3(t51, 0, 0.4e1 / 0.3e1 * t52 * t978)
  t983 = (t977 + t981) * t59
  t985 = t40 * t983 * t87
  t987 = 0.19751789702565206228825776161588751761046270558698e-1 * t983 * t85
  t988 = t485 * t974
  t989 = t487 * t978
  t991 = t988 / 0.3e1 + t989 / 0.3e1
  t997 = 0.29230250000000000000000000000000000000000000000000e1 * t102 * t120 * t991
  t999 = t10 * t128 * t991
  t1015 = 0.2e1 * t426 + 0.2e1 * t543
  t1019 = t974 / 0.2e1
  t1023 = 0.4e1 / 0.15e2 * t574 * t191 * t203 * t1019
  t1024 = t585 * t974
  t1026 = t11 * t584 * t1024
  t1032 = 0.2e1 / 0.15e2 * t178 * (t583 + 0.18891666666666666666666666666666666666666666666667e-2 * t1026) * t189 * t204
  t1036 = 0.4e1 / 0.45e2 * t600 * t603 * t604 * t974
  t1045 = 0.2e1 / 0.15e2 * t190 * t191 * t611 * (-t612 - 0.35991666666666666666666666666666666666666666666667e-1 * t1026 - t617 - 0.66666666666666666666666666666666666666666666666667e-2 * t25 * t619 * t1024)
  t1050 = -0.4e1 / 0.15e2 * t629 * t191 * t225 * t1019
  t1051 = t639 * t978
  t1053 = t11 * t638 * t1051
  t1059 = 0.2e1 / 0.15e2 * t208 * (t637 + 0.18891666666666666666666666666666666666666666666667e-2 * t1053) * t189 * t226
  t1063 = 0.4e1 / 0.45e2 * t652 * t655 * t656 * t978
  t1072 = 0.2e1 / 0.15e2 * t216 * t191 * t663 * (-t664 - 0.35991666666666666666666666666666666666666666666667e-1 * t1053 - t668 - 0.66666666666666666666666666666666666666666666666667e-2 * t25 * t670 * t1051)
  t1076 = t1023 + t1032 + t598 + t1036 - t1045 + t1050 + t1059 + t651 + t1063 - t1072 + 0.4e1 / 0.3e1 * t1015 * t230 * t236 + t687 + t694 + t696
  t1097 = t1023 + t1032 + t598 + t1036 - t1045 + t1050 + t1059 + t651 + t1063 - t1072 + t1015 * t253 * t257 * t262 / 0.3e1 + t732 + t738 + t741 - (0.4e1 / 0.3e1 * t742 * t974 + 0.4e1 / 0.3e1 * t744 * t978) * t108 * t273 / 0.15e2 - t753
  t1102 = t395 + t416 - t420 - t425 + t985 + t471 + t987 - t478 - t483
  t1124 = 0.3e1 * t484 * t143 * t991 + t101 * ((-t497 - t997 - t504 - t505 * t999 / 0.2e1 - t513 - 0.14690400000000000000000000000000000000000000000000e1 * t127 * t515 * t991) * t138 - t523 * (-t497 - t997 - t526 - 0.17242550000000000000000000000000000000000000000000e1 * t133 * t999)) * t535 + (t540 - 0.17543244109220059985638668152930835075000000000000e0 * t148 * t1015 * t169 - t560 - t568 + t572 - 0.30400821447970174150861446235388365887845217506462e-2 * t174 * t176 * t1076 * t241) * t125 + (t705 - 0.26314866163830089978458002229396252612500000000000e0 * t155 * t1015 * t248 - t718 + t722 - 0.38001026809962717688576807794235457359806521883077e-2 * t174 * t176 * t1097 * jnp.pi - t761 + 0.42708890021612718670335112500000000000000000000000e0 * t158 * t161 * t1102) * t286 + t772 - 0.67557380995489275890803213856418590861878261125470e-2 * t173 * t288 * t1015 * t293 - t779 - t787 + (t791 - 0.10133607149323391383620482078462788629281739168820e-1 * t174 * t176 * t1015 * t297 - t799 - t802 + 0.52629732327660179956916004458792505225000000000000e0 * t301 * t1102) * t305 - t812 + 0.20267214298646782767240964156925577258563478337641e-1 * t174 * t308 * t1102 * t310
  t1125 = t1124 * t321
  t1127 = f.my_piecewise3(t44, 0, 0.2e1 / 0.3e1 * t988)
  t1129 = f.my_piecewise3(t51, 0, 0.2e1 / 0.3e1 * t989)
  t1131 = t1127 / 0.2e1 + t1129 / 0.2e1
  t1135 = t395 + t416 - t420 - t425 + t985 + t471 + t987 - t478 - t483 - t1125 - t827
  t1138 = -t842 * t1102 + t1135 * t332
  t1139 = params.a_c * t1138
  t1153 = t874 * t1138 * t847 * t876 * t884 / 0.96e2
  t1160 = (0.3e1 * t1131 * t348 * t894 - t1135 * t348 * t349) * t352
  t1164 = t890 * t891 * t882 * t1160 / 0.96e2
  t1168 = t908 * t910 * t882 * t1131 / 0.48e2
  t1196 = t395 + t416 - t420 - t425 + t985 + t471 + t987 - t478 - t483 - t1125 - t827 + 0.3e1 * t828 * t391 * t1131 + t330 * (t335 * t1139 * t850 * t857 / 0.96e2 - t866 - t868 * t347 * t362 * t385 * t1131 / 0.48e2 + t344 * t347 * t348 * (t1153 - t1164 - t906 - t1168) * t385 / 0.96e2 - t344 * t347 * t362 * t922 * (t1153 - t1164 - t906 - t1168 + t926 * t929 * t1139 * t848 / 0.1536e4 - t938 * t940 * t928 * t1160 / 0.1536e4 - t951 - t953 * t957 * t928 * t1131 / 0.768e3) / 0.96e2) * t969
  vrho_1_ = t7 * t1196 - t322 - t33 + t392 + t89 + t91
  t1198 = t7 * params.gamma
  t1200 = t335 * t343 * t387
  t1207 = t365 * t337 * t379 * t380 * t367 * t354 * t385
  t1212 = t335 * t355 * t340 * t852 * t347
  t1216 = t365 * t370 * t337 * t381
  vsigma_0_ = t1198 * t329 * (t1200 / 0.96e2 + t1207 / 0.3072e4 - t344 * t347 * t362 * t922 * (t1212 / 0.96e2 + t1216 / 0.1536e4) / 0.96e2) * t969
  vsigma_1_ = t1198 * t329 * (t1200 / 0.48e2 + t1207 / 0.1536e4 - t344 * t347 * t362 * t922 * (t1212 / 0.48e2 + t1216 / 0.768e3) / 0.96e2) * t969
  vsigma_2_ = vsigma_0_

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1), 'vsigma': jnp.stack([vsigma_0_, vsigma_1_, vsigma_2_], axis=-1)}
  return res


def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t7
  t9 = t6 * t8
  t10 = t4 * t9
  t12 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t10
  t13 = jnp.sqrt(t10)
  t16 = t10 ** 0.15e1
  t18 = t1 ** 2
  t19 = t3 ** 2
  t20 = t18 * t19
  t21 = t7 ** 2
  t22 = 0.1e1 / t21
  t23 = t5 * t22
  t24 = t20 * t23
  t26 = 0.37978500000000000000000000000000000000000000000000e1 * t13 + 0.89690000000000000000000000000000000000000000000000e0 * t10 + 0.20477500000000000000000000000000000000000000000000e0 * t16 + 0.12323500000000000000000000000000000000000000000000e0 * t24
  t29 = 0.1e1 + 0.16081824322151104821330931780901225435013347914188e2 / t26
  t30 = jnp.log(t29)
  t32 = 0.62182e-1 * t12 * t30
  t33 = 0.1e1 <= f.p.zeta_threshold
  t34 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t36 = f.my_piecewise3(t33, t34 * f.p.zeta_threshold, 1)
  t39 = 2 ** (0.1e1 / 0.3e1)
  t43 = (0.2e1 * t36 - 0.2e1) / (0.2e1 * t39 - 0.2e1)
  t45 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t10
  t50 = 0.51785000000000000000000000000000000000000000000000e1 * t13 + 0.90577500000000000000000000000000000000000000000000e0 * t10 + 0.11003250000000000000000000000000000000000000000000e0 * t16 + 0.12417750000000000000000000000000000000000000000000e0 * t24
  t53 = 0.1e1 + 0.29608574643216675549239059631669331438384556167466e2 / t50
  t54 = jnp.log(t53)
  t57 = 0.19751789702565206228825776161588751761046270558698e-1 * t43 * t45 * t54
  t58 = jnp.log(0.2e1)
  t59 = t58 - 0.1e1
  t60 = 0.2e1 * t59
  t62 = 0.29230250000000000000000000000000000000000000000000e1 * f.p.cam_omega * t13
  t64 = 9 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t73 = f.p.cam_omega ** 2
  t75 = (0.344851e1 - jnp.pi * t5 * t65 * t3 / t59 / 0.12e2) * t73 * t1
  t76 = t3 * t6
  t77 = t76 * t8
  t80 = t73 * f.p.cam_omega
  t84 = 0.1e1 + t62 + t75 * t77 / 0.4e1 + 0.48968000000000000000000000000000000000000000000000e0 * t80 * t13 * t10
  t85 = t73 * t1
  t88 = 0.1e1 + t62 + 0.86212750000000000000000000000000000000000000000000e0 * t85 * t77
  t89 = 0.1e1 / t88
  t91 = jnp.log(t84 * t89)
  t93 = jnp.pi ** 2
  t94 = 0.1e1 / t93
  t96 = jnp.sqrt(jnp.pi)
  t98 = 0.1e1 / t96 / jnp.pi
  t99 = 0.1e1 / r0
  t100 = t98 * t99
  t103 = t2 * t99
  t105 = t3 * t2
  t106 = t1 * t105
  t108 = 0.1e1 / t7 / r0
  t109 = t6 * t108
  t112 = 0.1e1 + 0.51750000000000000000000000000000000000000000000000e-2 * t10 + 0.20482500000000000000000000000000000000000000000000e-1 * t24 - 0.95775000000000000000000000000000000000000000000000e-2 * t103 + 0.34856250000000000000000000000000000000000000000000e-3 * t106 * t109
  t114 = jnp.exp(-0.18810000000000000000000000000000000000000000000000e0 * t10)
  t115 = t112 * t114
  t116 = jnp.sqrt(0.2e1)
  t117 = t115 * t116
  t121 = t18 * t19 * t94
  t122 = t121 * t5
  t124 = 0.1e1 / t21 / r0
  t126 = t4 * t9 * t39
  t130 = 0.1e1 / t105
  t131 = (0.1e1 - 0.56675000000000000000000000000000000000000000000000e-2 * t126) * t65 * t130
  t132 = t1 * t21
  t134 = t39 ** 2
  t138 = 0.1e1 + 0.10797500000000000000000000000000000000000000000000e0 * t126 + 0.10000000000000000000000000000000000000000000000000e-1 * t20 * t23 * t134
  t139 = 0.1e1 / t138
  t142 = t131 * t132 * t139 / 0.15e2
  t144 = jnp.exp(-0.77500000000000000000000000000000000000000000000000e-1 * t10)
  t147 = -0.12375000000000000000000000000000000000000000000000e1 * t10 + t24 / 0.4e1
  t148 = t144 * t147
  t149 = jnp.pi * r0
  t152 = t142 + 0.4e1 / 0.3e1 * t148 * t149
  t154 = t116 * t96
  t161 = t115 / 0.2e1 - 0.1e1 / 0.2e1
  t165 = jnp.exp(-0.13675000000000000000000000000000000000000000000000e0 * t10)
  t168 = -0.97000000000000000000000000000000000000000000000000e-1 * t10 + 0.16900000000000000000000000000000000000000000000000e0 * t24
  t170 = t165 * t168 * t1
  t171 = 0.1e1 / t19
  t172 = t171 * t6
  t173 = t172 * t21
  t176 = t65 * t130
  t179 = t142 + t170 * t173 / 0.3e1 - t176 * t132 / 0.15e2
  t184 = -t32 + t57
  t189 = t73 ** 2
  t191 = t5 * t124
  t192 = t121 * t191
  t193 = t189 * f.p.cam_omega
  t194 = t154 * t193
  t195 = t115 * t194
  t202 = r0 ** 2
  t203 = 0.1e1 / t202
  t204 = t94 * t203
  t208 = t189 * t73
  t211 = 0.1e1 / t21 / t202
  t213 = t189 ** 2
  t217 = t60 * t91 * t94 + (-0.17543244109220059985638668152930835075000000000000e0 * t100 * t117 - 0.30400821447970174150861446235388365887845217506462e-2 * t122 * t124 * t152 * t154) * t80 + (-0.26314866163830089978458002229396252612500000000000e0 * t103 * t161 - 0.38001026809962717688576807794235457359806521883077e-2 * t122 * t124 * t179 * jnp.pi + 0.42708890021612718670335112500000000000000000000000e0 * t106 * t109 * t184) * t189 - 0.67557380995489275890803213856418590861878261125470e-2 * t192 * t195 + (-0.10133607149323391383620482078462788629281739168820e-1 * t122 * t124 * t161 * jnp.pi + 0.52629732327660179956916004458792505225000000000000e0 * t204 * t184) * t208 + 0.20267214298646782767240964156925577258563478337641e-1 * t122 * t211 * t184 * t213
  t221 = 0.1e1 + 0.15403623315025000000000000000000000000000000000000e0 * t20 * t23 * t73
  t222 = t221 ** 2
  t223 = t222 ** 2
  t224 = 0.1e1 / t223
  t225 = t217 * t224
  t226 = t34 ** 2
  t227 = f.my_piecewise3(t33, t226, 1)
  t228 = t227 ** 2
  t229 = t228 * t227
  t230 = params.gamma * t229
  t231 = -t32 + t57 - t225
  t232 = 0.1e1 / t184
  t234 = (t231 * t232) ** params.a_c
  t235 = params.beta * t234
  t236 = t235 * s0
  t238 = 0.1e1 / t7 / t202
  t239 = t238 * t39
  t240 = 0.1e1 / t228
  t241 = t239 * t240
  t242 = t236 * t241
  t243 = 0.1e1 / t3
  t244 = t18 * t243
  t245 = t244 * t5
  t246 = 0.1e1 / params.gamma
  t250 = jnp.exp(-t231 / t229 * t246)
  t251 = t250 - 0.1e1
  t252 = 0.1e1 / t251
  t253 = t246 * t252
  t255 = t235 * t253 * s0
  t258 = t255 * t241 * t245 / 0.96e2
  t259 = 0.1e1 + t258
  t260 = t246 * t259
  t261 = params.beta ** 2
  t262 = t234 ** 2
  t263 = t261 * t262
  t264 = params.gamma ** 2
  t265 = 0.1e1 / t264
  t266 = t251 ** 2
  t267 = 0.1e1 / t266
  t268 = t265 * t267
  t269 = s0 ** 2
  t271 = t263 * t268 * t269
  t272 = t202 ** 2
  t274 = 0.1e1 / t21 / t272
  t275 = t274 * t134
  t276 = t228 ** 2
  t277 = 0.1e1 / t276
  t278 = t275 * t277
  t280 = t1 * t171 * t6
  t281 = t278 * t280
  t284 = 0.1e1 + t258 + t271 * t281 / 0.3072e4
  t285 = 0.1e1 / t284
  t287 = t245 * t260 * t285
  t290 = 0.1e1 + t242 * t287 / 0.96e2
  t291 = jnp.log(t290)
  t295 = 0.11073577833333333333333333333333333333333333333333e-2 * t4 * t109 * t30
  t296 = t26 ** 2
  t299 = 0.1e1 / t13
  t301 = t76 * t108
  t302 = t299 * t1 * t301
  t304 = t4 * t109
  t306 = t10 ** 0.5e0
  t308 = t306 * t1 * t301
  t310 = t20 * t191
  t316 = 0.10000000000000000000000000000000000000000000000000e1 * t12 / t296 * (-0.63297500000000000000000000000000000000000000000000e0 * t302 - 0.29896666666666666666666666666666666666666666666667e0 * t304 - 0.10238750000000000000000000000000000000000000000000e0 * t308 - 0.82156666666666666666666666666666666666666666666667e-1 * t310) / t29
  t321 = 0.18311555036753159941307229983139571945136646663793e-3 * t43 * t1 * t76 * t108 * t54
  t323 = t50 ** 2
  t334 = 0.58482233974552040708313425006184496242808878304903e0 * t43 * t45 / t323 * (-0.86308333333333333333333333333333333333333333333334e0 * t302 - 0.30192500000000000000000000000000000000000000000000e0 * t304 - 0.55016250000000000000000000000000000000000000000000e-1 * t308 - 0.82785000000000000000000000000000000000000000000000e-1 * t310) / t53
  t338 = 0.48717083333333333333333333333333333333333333333333e0 * f.p.cam_omega * t299 * t1 * t301
  t347 = t88 ** 2
  t365 = t2 * t203
  t367 = t6 * t238
  t371 = (-0.17250000000000000000000000000000000000000000000000e-2 * t304 - 0.13655000000000000000000000000000000000000000000000e-1 * t310 + 0.95775000000000000000000000000000000000000000000000e-2 * t365 - 0.46475000000000000000000000000000000000000000000000e-3 * t106 * t367) * t114
  t376 = t112 * t1
  t378 = t114 * t116
  t392 = 0.12594444444444444444444444444444444444444444444445e-3 * t18 * jnp.pi * t6 * t22 * t39 * t65 * t139
  t393 = t1 * t8
  t396 = 0.2e1 / 0.45e2 * t131 * t393 * t139
  t397 = t138 ** 2
  t409 = t131 * t132 / t397 * (-0.35991666666666666666666666666666666666666666666667e-1 * t4 * t109 * t39 - 0.66666666666666666666666666666666666666666666666667e-2 * t20 * t191 * t134) / 0.15e2
  t438 = t371 / 0.2e1 + 0.31350000000000000000000000000000000000000000000000e-1 * t376 * t3 * t109 * t114
  t469 = t295 + t316 - t321 - t334
  t484 = t202 * r0
  t485 = 0.1e1 / t484
  t517 = (t60 * ((-t338 - t75 * t301 / 0.12e2 - 0.24484000000000000000000000000000000000000000000000e0 * t80 * t13 * t1 * t301) * t89 - t84 / t347 * (-t338 - 0.28737583333333333333333333333333333333333333333333e0 * t85 * t301)) / t84 * t88 * t94 + (0.17543244109220059985638668152930835075000000000000e0 * t98 * t203 * t117 - 0.17543244109220059985638668152930835075000000000000e0 * t100 * t371 * t116 - 0.10999614056480977610995444931887633592025000000000e-1 * t98 * t238 * t376 * t76 * t378 + 0.50668035746616956918102410392313943146408695844103e-2 * t122 * t211 * t152 * t154 - 0.30400821447970174150861446235388365887845217506462e-2 * t122 * t124 * (t392 + t396 - t409 + 0.34444444444444444444444444444444444444444444444444e-1 * t4 * t6 * t8 * t144 * t147 * jnp.pi + 0.4e1 / 0.3e1 * t144 * (0.41250000000000000000000000000000000000000000000000e0 * t304 - t310 / 0.6e1) * t149 + 0.4e1 / 0.3e1 * t148 * jnp.pi) * t154) * t80 + (0.26314866163830089978458002229396252612500000000000e0 * t365 * t161 - 0.26314866163830089978458002229396252612500000000000e0 * t103 * t438 + 0.63335044683271196147628012990392428933010869805128e-2 * t122 * t211 * t179 * jnp.pi - 0.38001026809962717688576807794235457359806521883077e-2 * t122 * t124 * (t392 + t396 - t409 + 0.60777777777777777777777777777777777777777777777777e-1 * t245 * t22 * t165 * t168 + t165 * (0.32333333333333333333333333333333333333333333333333e-1 * t304 - 0.11266666666666666666666666666666666666666666666667e0 * t310) * t1 * t173 / 0.3e1 + 0.2e1 / 0.9e1 * t170 * t172 * t8 - 0.2e1 / 0.45e2 * t176 * t393) * jnp.pi - 0.56945186695483624893780150000000000000000000000000e0 * t106 * t367 * t184 + 0.42708890021612718670335112500000000000000000000000e0 * t106 * t109 * t469) * t189 + 0.11259563499248212648467202309403098476979710187578e-1 * t121 * t5 * t211 * t195 - 0.67557380995489275890803213856418590861878261125470e-2 * t192 * t371 * t194 - 0.50830173461006131180240338105569347764477203670804e-2 / t96 / t93 * t485 * t112 * t378 * t193 + (0.16889345248872318972700803464104647715469565281367e-1 * t122 * t211 * t161 * jnp.pi - 0.10133607149323391383620482078462788629281739168820e-1 * t122 * t124 * t438 * jnp.pi - 0.10525946465532035991383200891758501045000000000000e1 * t94 * t485 * t184 + 0.52629732327660179956916004458792505225000000000000e0 * t204 * t469) * t208 - 0.54045904796391420712642571085134872689502608900376e-1 * t122 / t21 / t484 * t184 * t213 + 0.20267214298646782767240964156925577258563478337641e-1 * t122 * t211 * t469 * t213) * t224
  t526 = 0.41076328840066666666666666666666666666666666666668e0 * t217 / t223 / t221 * t18 * t19 * t5 * t124 * t73
  t527 = t295 + t316 - t321 - t334 - t517 - t526
  t529 = t184 ** 2
  t533 = t527 * t232 - t231 / t529 * t469
  t534 = params.a_c * t533
  t536 = 0.1e1 / t231
  t537 = t536 * t184
  t541 = t39 * t240
  t552 = 0.1e1 / t7 / t484 * t39 * t240
  t564 = t243 * t5
  t568 = t235 * params.a_c * t533 * t536 * t184 * t246 * t252 * s0 * t239 * t240 * t18 * t564 / 0.96e2
  t577 = t527 * t250
  t581 = t235 * t265 * t267 * s0 * t238 * t39 / t276 / t227 * t18 * t564 * t577 / 0.96e2
  t584 = 0.7e1 / 0.288e3 * t255 * t552 * t245
  t591 = t284 ** 2
  t592 = 0.1e1 / t591
  t634 = 0.1e1 / t290
  vrho_0_ = -t32 + t57 - t225 + t230 * t291 + r0 * (t295 + t316 - t321 - t334 - t517 - t526 + t230 * (t235 * t534 * t537 * s0 * t238 * t541 * t244 * t5 * t246 * t259 * t285 / 0.96e2 - 0.7e1 / 0.288e3 * t236 * t552 * t287 + t242 * t245 * t246 * (t568 + t581 - t584) * t285 / 0.96e2 - t242 * t245 * t260 * t592 * (t568 + t581 - t584 + t263 * t265 * t267 * t269 * t275 * t277 * t1 * t172 * t534 * t537 / 0.1536e4 + t263 / t264 / params.gamma / t266 / t251 * t269 * t274 * t134 / t276 / t229 * t1 * t172 * t577 / 0.1536e4 - 0.7e1 / 0.4608e4 * t271 / t21 / t272 / r0 * t134 * t277 * t280) / 0.96e2) * t634)
  vsigma_0_ = r0 * params.gamma * t229 * (t235 * t241 * t287 / 0.96e2 + t263 * s0 * t278 * t280 * t265 * t252 * t285 / 0.3072e4 - t242 * t245 * t260 * t592 * (t235 * t253 * t238 * t541 * t245 / 0.96e2 + t263 * t268 * s0 * t281 / 0.1536e4) / 0.96e2) * t634

  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res
