"""Generated from gga_x_pbe_erf_gws.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
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
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))
  params_b_PBE_raw = params.b_PBE
  if isinstance(params_b_PBE_raw, (str, bytes, dict)):
    params_b_PBE = params_b_PBE_raw
  else:
    try:
      params_b_PBE_seq = list(params_b_PBE_raw)
    except TypeError:
      params_b_PBE = params_b_PBE_raw
    else:
      params_b_PBE_seq = np.asarray(params_b_PBE_seq, dtype=np.float64)
      params_b_PBE = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_PBE_seq))
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

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  lda_x_ax = -f.RS_FACTOR * X_FACTOR_C / 2 ** (4 / 3)

  pbe_x_erf_gws_c1_b = lambda x: 1 + 22 * x ** 2 + 144 * x ** 4

  pbe_x_erf_gws_c2_b = lambda x: 2 * x ** 2 * (-7 + 72 * x ** 2)

  pbe_x_erf_gws_c3_b = lambda x: -864 * x ** 4 * (-1 + 2 * x ** 2)

  pbe_x_erf_gws_c4_b = lambda x: x ** 2 * (-3 - 24 * x ** 2 + 32 * x ** 4 + 8 * x * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * x)))

  exp_b = lambda mu_t: jnp.exp(1 / (4 * mu_t ** 2))

  pbe_x_erf_gws_b_large_mu = lambda mu_t: 1 / (72 * mu_t ** 2) - 1 / (17280 * mu_t ** 4) - 23 / (358400 * mu_t ** 6)

  pbe_x_erf_gws_b_thresh_small = 0.05

  pbe_x_erf_gws_b_thresh_large = 10000000000.0

  pbe_x_erf_gws_b_piece0 = 7 / 81

  pbe_x_erf_gws_kappa_fx = lambda rs=None, z=None: params_kappa

  pbe_x_erf_gws_x_b_orig = params_b_PBE

  pbe_x_erf_gws_ax = params_ax

  nu_2 = lambda rs, z: f.nu(rs, z) / 2

  rs_a = lambda rs, z: simplify(f.r_ws(f.n_spin(rs, z)))

  rs_b = lambda rs, z: simplify(f.r_ws(f.n_spin(rs, -z)))

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  pbe_x_erf_gws_b_small_mu = lambda mu_t: apply_piecewise(mu_t, lambda _aval_small: _aval_small == 0.0, lambda _aval_small: pbe_x_erf_gws_b_piece0, lambda _aval_small: pbe_x_erf_gws_c2_b(_aval_small) / (54 * pbe_x_erf_gws_c4_b(_aval_small)))

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  pbe_x_erf_gws_b_mod = lambda mu_t: pbe_x_erf_gws_x_b_orig / pbe_x_erf_gws_b_piece0 * pbe_x_erf_gws_b_piece(mu_t) * jnp.exp(-pbe_x_erf_gws_ax * mu_t ** 2)

  lda_x_erf_spin = lambda rs, z: lda_x_ax * f.opz_pow_n(z, 4 / 3) / rs * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3))

  pbe_x_erf_gws_Fx = lambda rs, z, s: 1 + pbe_x_erf_gws_kappa_fx(rs, z) * (1 - pbe_x_erf_gws_kappa_fx(rs, z) / (pbe_x_erf_gws_kappa_fx(rs, z) + pbe_x_erf_gws_b_mod(nu_2(rs, z)) * s ** 2))

  f_pbe_x_erf_gws_spin = lambda rs, z, xs: lda_x_erf_spin(rs, z) * pbe_x_erf_gws_Fx(rs, z, xs * X2S)

  functional_body = lambda rs, z, xt, xs0, xs1: simplify((+f.my_piecewise3(f.screen_dens(rs, z), 0, f_pbe_x_erf_gws_spin(rs_a(rs, z), 1, xs0) * f.n_spin(rs, z)) + f.my_piecewise3(f.screen_dens(rs, -z), 0, f_pbe_x_erf_gws_spin(rs_b(rs, z), 1, xs1) * f.n_spin(rs, -z))) / f.n_total(rs))

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
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))
  params_b_PBE_raw = params.b_PBE
  if isinstance(params_b_PBE_raw, (str, bytes, dict)):
    params_b_PBE = params_b_PBE_raw
  else:
    try:
      params_b_PBE_seq = list(params_b_PBE_raw)
    except TypeError:
      params_b_PBE = params_b_PBE_raw
    else:
      params_b_PBE_seq = np.asarray(params_b_PBE_seq, dtype=np.float64)
      params_b_PBE = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_PBE_seq))
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

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  lda_x_ax = -f.RS_FACTOR * X_FACTOR_C / 2 ** (4 / 3)

  pbe_x_erf_gws_c1_b = lambda x: 1 + 22 * x ** 2 + 144 * x ** 4

  pbe_x_erf_gws_c2_b = lambda x: 2 * x ** 2 * (-7 + 72 * x ** 2)

  pbe_x_erf_gws_c3_b = lambda x: -864 * x ** 4 * (-1 + 2 * x ** 2)

  pbe_x_erf_gws_c4_b = lambda x: x ** 2 * (-3 - 24 * x ** 2 + 32 * x ** 4 + 8 * x * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * x)))

  exp_b = lambda mu_t: jnp.exp(1 / (4 * mu_t ** 2))

  pbe_x_erf_gws_b_large_mu = lambda mu_t: 1 / (72 * mu_t ** 2) - 1 / (17280 * mu_t ** 4) - 23 / (358400 * mu_t ** 6)

  pbe_x_erf_gws_b_thresh_small = 0.05

  pbe_x_erf_gws_b_thresh_large = 10000000000.0

  pbe_x_erf_gws_b_piece0 = 7 / 81

  pbe_x_erf_gws_kappa_fx = lambda rs=None, z=None: params_kappa

  pbe_x_erf_gws_x_b_orig = params_b_PBE

  pbe_x_erf_gws_ax = params_ax

  nu_2 = lambda rs, z: f.nu(rs, z) / 2

  rs_a = lambda rs, z: simplify(f.r_ws(f.n_spin(rs, z)))

  rs_b = lambda rs, z: simplify(f.r_ws(f.n_spin(rs, -z)))

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  pbe_x_erf_gws_b_small_mu = lambda mu_t: apply_piecewise(mu_t, lambda _aval_small: _aval_small == 0.0, lambda _aval_small: pbe_x_erf_gws_b_piece0, lambda _aval_small: pbe_x_erf_gws_c2_b(_aval_small) / (54 * pbe_x_erf_gws_c4_b(_aval_small)))

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  pbe_x_erf_gws_b_mod = lambda mu_t: pbe_x_erf_gws_x_b_orig / pbe_x_erf_gws_b_piece0 * pbe_x_erf_gws_b_piece(mu_t) * jnp.exp(-pbe_x_erf_gws_ax * mu_t ** 2)

  lda_x_erf_spin = lambda rs, z: lda_x_ax * f.opz_pow_n(z, 4 / 3) / rs * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3))

  pbe_x_erf_gws_Fx = lambda rs, z, s: 1 + pbe_x_erf_gws_kappa_fx(rs, z) * (1 - pbe_x_erf_gws_kappa_fx(rs, z) / (pbe_x_erf_gws_kappa_fx(rs, z) + pbe_x_erf_gws_b_mod(nu_2(rs, z)) * s ** 2))

  f_pbe_x_erf_gws_spin = lambda rs, z, xs: lda_x_erf_spin(rs, z) * pbe_x_erf_gws_Fx(rs, z, xs * X2S)

  functional_body = lambda rs, z, xt, xs0, xs1: simplify((+f.my_piecewise3(f.screen_dens(rs, z), 0, f_pbe_x_erf_gws_spin(rs_a(rs, z), 1, xs0) * f.n_spin(rs, z)) + f.my_piecewise3(f.screen_dens(rs, -z), 0, f_pbe_x_erf_gws_spin(rs_b(rs, z), 1, xs1) * f.n_spin(rs, -z))) / f.n_total(rs))

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
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))
  params_b_PBE_raw = params.b_PBE
  if isinstance(params_b_PBE_raw, (str, bytes, dict)):
    params_b_PBE = params_b_PBE_raw
  else:
    try:
      params_b_PBE_seq = list(params_b_PBE_raw)
    except TypeError:
      params_b_PBE = params_b_PBE_raw
    else:
      params_b_PBE_seq = np.asarray(params_b_PBE_seq, dtype=np.float64)
      params_b_PBE = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_PBE_seq))
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

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  lda_x_ax = -f.RS_FACTOR * X_FACTOR_C / 2 ** (4 / 3)

  pbe_x_erf_gws_c1_b = lambda x: 1 + 22 * x ** 2 + 144 * x ** 4

  pbe_x_erf_gws_c2_b = lambda x: 2 * x ** 2 * (-7 + 72 * x ** 2)

  pbe_x_erf_gws_c3_b = lambda x: -864 * x ** 4 * (-1 + 2 * x ** 2)

  pbe_x_erf_gws_c4_b = lambda x: x ** 2 * (-3 - 24 * x ** 2 + 32 * x ** 4 + 8 * x * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * x)))

  exp_b = lambda mu_t: jnp.exp(1 / (4 * mu_t ** 2))

  pbe_x_erf_gws_b_large_mu = lambda mu_t: 1 / (72 * mu_t ** 2) - 1 / (17280 * mu_t ** 4) - 23 / (358400 * mu_t ** 6)

  pbe_x_erf_gws_b_thresh_small = 0.05

  pbe_x_erf_gws_b_thresh_large = 10000000000.0

  pbe_x_erf_gws_b_piece0 = 7 / 81

  pbe_x_erf_gws_kappa_fx = lambda rs=None, z=None: params_kappa

  pbe_x_erf_gws_x_b_orig = params_b_PBE

  pbe_x_erf_gws_ax = params_ax

  nu_2 = lambda rs, z: f.nu(rs, z) / 2

  rs_a = lambda rs, z: simplify(f.r_ws(f.n_spin(rs, z)))

  rs_b = lambda rs, z: simplify(f.r_ws(f.n_spin(rs, -z)))

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  pbe_x_erf_gws_b_small_mu = lambda mu_t: apply_piecewise(mu_t, lambda _aval_small: _aval_small == 0.0, lambda _aval_small: pbe_x_erf_gws_b_piece0, lambda _aval_small: pbe_x_erf_gws_c2_b(_aval_small) / (54 * pbe_x_erf_gws_c4_b(_aval_small)))

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  pbe_x_erf_gws_b_mod = lambda mu_t: pbe_x_erf_gws_x_b_orig / pbe_x_erf_gws_b_piece0 * pbe_x_erf_gws_b_piece(mu_t) * jnp.exp(-pbe_x_erf_gws_ax * mu_t ** 2)

  lda_x_erf_spin = lambda rs, z: lda_x_ax * f.opz_pow_n(z, 4 / 3) / rs * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3))

  pbe_x_erf_gws_Fx = lambda rs, z, s: 1 + pbe_x_erf_gws_kappa_fx(rs, z) * (1 - pbe_x_erf_gws_kappa_fx(rs, z) / (pbe_x_erf_gws_kappa_fx(rs, z) + pbe_x_erf_gws_b_mod(nu_2(rs, z)) * s ** 2))

  f_pbe_x_erf_gws_spin = lambda rs, z, xs: lda_x_erf_spin(rs, z) * pbe_x_erf_gws_Fx(rs, z, xs * X2S)

  functional_body = lambda rs, z, xt, xs0, xs1: simplify((+f.my_piecewise3(f.screen_dens(rs, z), 0, f_pbe_x_erf_gws_spin(rs_a(rs, z), 1, xs0) * f.n_spin(rs, z)) + f.my_piecewise3(f.screen_dens(rs, -z), 0, f_pbe_x_erf_gws_spin(rs_b(rs, z), 1, xs1) * f.n_spin(rs, -z))) / f.n_total(rs))

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
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))
  params_b_PBE_raw = params.b_PBE
  if isinstance(params_b_PBE_raw, (str, bytes, dict)):
    params_b_PBE = params_b_PBE_raw
  else:
    try:
      params_b_PBE_seq = list(params_b_PBE_raw)
    except TypeError:
      params_b_PBE = params_b_PBE_raw
    else:
      params_b_PBE_seq = np.asarray(params_b_PBE_seq, dtype=np.float64)
      params_b_PBE = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_PBE_seq))
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

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  lda_x_ax = -f.RS_FACTOR * X_FACTOR_C / 2 ** (4 / 3)

  pbe_x_erf_gws_c1_b = lambda x: 1 + 22 * x ** 2 + 144 * x ** 4

  pbe_x_erf_gws_c2_b = lambda x: 2 * x ** 2 * (-7 + 72 * x ** 2)

  pbe_x_erf_gws_c3_b = lambda x: -864 * x ** 4 * (-1 + 2 * x ** 2)

  pbe_x_erf_gws_c4_b = lambda x: x ** 2 * (-3 - 24 * x ** 2 + 32 * x ** 4 + 8 * x * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * x)))

  exp_b = lambda mu_t: jnp.exp(1 / (4 * mu_t ** 2))

  pbe_x_erf_gws_b_large_mu = lambda mu_t: 1 / (72 * mu_t ** 2) - 1 / (17280 * mu_t ** 4) - 23 / (358400 * mu_t ** 6)

  pbe_x_erf_gws_b_thresh_small = 0.05

  pbe_x_erf_gws_b_thresh_large = 10000000000.0

  pbe_x_erf_gws_b_piece0 = 7 / 81

  pbe_x_erf_gws_kappa_fx = lambda rs=None, z=None: params_kappa

  pbe_x_erf_gws_x_b_orig = params_b_PBE

  pbe_x_erf_gws_ax = params_ax

  nu_2 = lambda rs, z: f.nu(rs, z) / 2

  rs_a = lambda rs, z: simplify(f.r_ws(f.n_spin(rs, z)))

  rs_b = lambda rs, z: simplify(f.r_ws(f.n_spin(rs, -z)))

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  pbe_x_erf_gws_b_small_mu = lambda mu_t: apply_piecewise(mu_t, lambda _aval_small: _aval_small == 0.0, lambda _aval_small: pbe_x_erf_gws_b_piece0, lambda _aval_small: pbe_x_erf_gws_c2_b(_aval_small) / (54 * pbe_x_erf_gws_c4_b(_aval_small)))

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  pbe_x_erf_gws_b_mod = lambda mu_t: pbe_x_erf_gws_x_b_orig / pbe_x_erf_gws_b_piece0 * pbe_x_erf_gws_b_piece(mu_t) * jnp.exp(-pbe_x_erf_gws_ax * mu_t ** 2)

  lda_x_erf_spin = lambda rs, z: lda_x_ax * f.opz_pow_n(z, 4 / 3) / rs * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3))

  pbe_x_erf_gws_Fx = lambda rs, z, s: 1 + pbe_x_erf_gws_kappa_fx(rs, z) * (1 - pbe_x_erf_gws_kappa_fx(rs, z) / (pbe_x_erf_gws_kappa_fx(rs, z) + pbe_x_erf_gws_b_mod(nu_2(rs, z)) * s ** 2))

  f_pbe_x_erf_gws_spin = lambda rs, z, xs: lda_x_erf_spin(rs, z) * pbe_x_erf_gws_Fx(rs, z, xs * X2S)

  functional_body = lambda rs, z, xt, xs0, xs1: simplify((+f.my_piecewise3(f.screen_dens(rs, z), 0, f_pbe_x_erf_gws_spin(rs_a(rs, z), 1, xs0) * f.n_spin(rs, z)) + f.my_piecewise3(f.screen_dens(rs, -z), 0, f_pbe_x_erf_gws_spin(rs_b(rs, z), 1, xs1) * f.n_spin(rs, -z))) / f.n_total(rs))

  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  r0 = r
  pol = pol_fxc(p, (r0/2, r0/2), (s/4 if s is not None else None, s/4 if s is not None else None, s/4 if s is not None else None), (None, None), (None, None))
  res = {}
  # Extract v2rho2 from polarized output
  v2rho2_pol = pol.get('v2rho2', None)
  if v2rho2_pol is not None:
    d11, d12, d22 = v2rho2_pol[..., 0], v2rho2_pol[..., 1], v2rho2_pol[..., 2]
    res['v2rho2'] = 0.25 * (d11 + 2*d12 + d22)
  # Extract v2rhosigma from polarized output
  v2rhosigma_pol = pol.get('v2rhosigma', None)
  if v2rhosigma_pol is not None:
    # Broadcast scalars to match array shape (Maple may emit some derivatives as scalar 0)
    d13 = jnp.asarray(v2rhosigma_pol[..., 0]) + jnp.zeros_like(r0)
    d14 = jnp.asarray(v2rhosigma_pol[..., 1]) + jnp.zeros_like(r0)
    d15 = jnp.asarray(v2rhosigma_pol[..., 2]) + jnp.zeros_like(r0)
    d23 = jnp.asarray(v2rhosigma_pol[..., 3]) + jnp.zeros_like(r0)
    d24 = jnp.asarray(v2rhosigma_pol[..., 4]) + jnp.zeros_like(r0)
    d25 = jnp.asarray(v2rhosigma_pol[..., 5]) + jnp.zeros_like(r0)
    res['v2rhosigma'] = (1/8) * (d13 + d14 + d15 + d23 + d24 + d25)
  # Extract v2sigma2 from polarized output
  v2sigma2_pol = pol.get('v2sigma2', None)
  if v2sigma2_pol is not None:
    # Broadcast scalars to match array shape
    d33 = jnp.asarray(v2sigma2_pol[..., 0]) + jnp.zeros_like(r0)
    d34 = jnp.asarray(v2sigma2_pol[..., 1]) + jnp.zeros_like(r0)
    d35 = jnp.asarray(v2sigma2_pol[..., 2]) + jnp.zeros_like(r0)
    d44 = jnp.asarray(v2sigma2_pol[..., 3]) + jnp.zeros_like(r0)
    d45 = jnp.asarray(v2sigma2_pol[..., 4]) + jnp.zeros_like(r0)
    d55 = jnp.asarray(v2sigma2_pol[..., 5]) + jnp.zeros_like(r0)
    res['v2sigma2'] = (1/16) * (d33 + 2*d34 + 2*d35 + d44 + 2*d45 + d55)
  return res
