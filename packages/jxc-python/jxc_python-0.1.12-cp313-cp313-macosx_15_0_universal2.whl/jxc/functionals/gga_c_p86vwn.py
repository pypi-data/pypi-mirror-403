"""Generated from gga_c_p86vwn.mpl."""

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
  params_aa_raw = params.aa
  if isinstance(params_aa_raw, (str, bytes, dict)):
    params_aa = params_aa_raw
  else:
    try:
      params_aa_seq = list(params_aa_raw)
    except TypeError:
      params_aa = params_aa_raw
    else:
      params_aa_seq = np.asarray(params_aa_seq, dtype=np.float64)
      params_aa = np.concatenate((np.array([np.nan], dtype=np.float64), params_aa_seq))
  params_bb_raw = params.bb
  if isinstance(params_bb_raw, (str, bytes, dict)):
    params_bb = params_bb_raw
  else:
    try:
      params_bb_seq = list(params_bb_raw)
    except TypeError:
      params_bb = params_bb_raw
    else:
      params_bb_seq = np.asarray(params_bb_seq, dtype=np.float64)
      params_bb = np.concatenate((np.array([np.nan], dtype=np.float64), params_bb_seq))
  params_ftilde_raw = params.ftilde
  if isinstance(params_ftilde_raw, (str, bytes, dict)):
    params_ftilde = params_ftilde_raw
  else:
    try:
      params_ftilde_seq = list(params_ftilde_raw)
    except TypeError:
      params_ftilde = params_ftilde_raw
    else:
      params_ftilde_seq = np.asarray(params_ftilde_seq, dtype=np.float64)
      params_ftilde = np.concatenate((np.array([np.nan], dtype=np.float64), params_ftilde_seq))
  params_malpha_raw = params.malpha
  if isinstance(params_malpha_raw, (str, bytes, dict)):
    params_malpha = params_malpha_raw
  else:
    try:
      params_malpha_seq = list(params_malpha_raw)
    except TypeError:
      params_malpha = params_malpha_raw
    else:
      params_malpha_seq = np.asarray(params_malpha_seq, dtype=np.float64)
      params_malpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_malpha_seq))
  params_mbeta_raw = params.mbeta
  if isinstance(params_mbeta_raw, (str, bytes, dict)):
    params_mbeta = params_mbeta_raw
  else:
    try:
      params_mbeta_seq = list(params_mbeta_raw)
    except TypeError:
      params_mbeta = params_mbeta_raw
    else:
      params_mbeta_seq = np.asarray(params_mbeta_seq, dtype=np.float64)
      params_mbeta = np.concatenate((np.array([np.nan], dtype=np.float64), params_mbeta_seq))
  params_mdelta_raw = params.mdelta
  if isinstance(params_mdelta_raw, (str, bytes, dict)):
    params_mdelta = params_mdelta_raw
  else:
    try:
      params_mdelta_seq = list(params_mdelta_raw)
    except TypeError:
      params_mdelta = params_mdelta_raw
    else:
      params_mdelta_seq = np.asarray(params_mdelta_seq, dtype=np.float64)
      params_mdelta = np.concatenate((np.array([np.nan], dtype=np.float64), params_mdelta_seq))
  params_mgamma_raw = params.mgamma
  if isinstance(params_mgamma_raw, (str, bytes, dict)):
    params_mgamma = params_mgamma_raw
  else:
    try:
      params_mgamma_seq = list(params_mgamma_raw)
    except TypeError:
      params_mgamma = params_mgamma_raw
    else:
      params_mgamma_seq = np.asarray(params_mgamma_seq, dtype=np.float64)
      params_mgamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_mgamma_seq))

  p86_DD = lambda z: jnp.sqrt(f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3)) / jnp.sqrt(2)

  p86_CC = lambda rs: +params_aa + (params_bb + params_malpha * rs + params_mbeta * rs ** 2) / (1 + params_mgamma * rs + params_mdelta * rs ** 2 + 10000.0 * params_mbeta * rs ** 3)

  p86_CCinf = params_aa + params_bb

  p86_x1 = lambda rs, xt: xt / jnp.sqrt(rs / f.RS_FACTOR)

  A_vwn = [None, 0.0310907, 0.01554535, -1 / (6 * jnp.pi ** 2)]

  b_vwn = np.array([np.nan, 3.72744, 7.06042, 1.13107], dtype=np.float64)

  c_vwn = np.array([np.nan, 12.9352, 18.0578, 13.0045], dtype=np.float64)

  x0_vwn = np.array([np.nan, -0.10498, -0.325, -0.0047584], dtype=np.float64)

  Q_vwn = lambda b, c: jnp.sqrt(4 * c - b ** 2)

  f2_vwn = lambda b, c, x0: b * x0 / (x0 ** 2 + b * x0 + c)

  fpp_vwn = 4 / (9 * (2 ** (1 / 3) - 1))

  fx_vwn = lambda b, c, rs: rs + b * jnp.sqrt(rs) + c

  p86_mPhi = lambda rs, xt: params_ftilde * (p86_CCinf / p86_CC(rs)) * p86_x1(rs, xt)

  f1_vwn = lambda b, c: 2 * b / Q_vwn(b, c)

  f3_vwn = lambda b, c, x0: 2 * (2 * x0 + b) / Q_vwn(b, c)

  p86_H = lambda rs, z, xt: p86_x1(rs, xt) ** 2 * jnp.exp(-p86_mPhi(rs, xt)) * p86_CC(rs) / p86_DD(z)

  f_aux = lambda A, b, c, x0, rs: A * (+jnp.log(rs / fx_vwn(b, c, rs)) + (f1_vwn(b, c) - f2_vwn(b, c, x0) * f3_vwn(b, c, x0)) * jnp.arctan(Q_vwn(b, c) / (2 * jnp.sqrt(rs) + b)) - f2_vwn(b, c, x0) * jnp.log((jnp.sqrt(rs) - x0) ** 2 / fx_vwn(b, c, rs)))

  DMC = lambda rs, z=None: +f_aux(A_vwn[2], b_vwn[2], c_vwn[2], x0_vwn[2], rs) - f_aux(A_vwn[1], b_vwn[1], c_vwn[1], x0_vwn[1], rs)

  f_vwn = lambda rs, z: +f_aux(A_vwn[1], b_vwn[1], c_vwn[1], x0_vwn[1], rs) + f_aux(A_vwn[3], b_vwn[3], c_vwn[3], x0_vwn[3], rs) * f.f_zeta(z) * (1 - z ** 4) / fpp_vwn + DMC(rs, z) * f.f_zeta(z) * z ** 4

  f_p86 = lambda rs, z, xt, xs0=None, xs1=None: f_vwn(rs, z) + p86_H(rs, z, xt)

  functional_body = lambda rs, z, xt, xs0, xs1: f_p86(rs, z, xt, xs0, xs1)

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
  params_aa_raw = params.aa
  if isinstance(params_aa_raw, (str, bytes, dict)):
    params_aa = params_aa_raw
  else:
    try:
      params_aa_seq = list(params_aa_raw)
    except TypeError:
      params_aa = params_aa_raw
    else:
      params_aa_seq = np.asarray(params_aa_seq, dtype=np.float64)
      params_aa = np.concatenate((np.array([np.nan], dtype=np.float64), params_aa_seq))
  params_bb_raw = params.bb
  if isinstance(params_bb_raw, (str, bytes, dict)):
    params_bb = params_bb_raw
  else:
    try:
      params_bb_seq = list(params_bb_raw)
    except TypeError:
      params_bb = params_bb_raw
    else:
      params_bb_seq = np.asarray(params_bb_seq, dtype=np.float64)
      params_bb = np.concatenate((np.array([np.nan], dtype=np.float64), params_bb_seq))
  params_ftilde_raw = params.ftilde
  if isinstance(params_ftilde_raw, (str, bytes, dict)):
    params_ftilde = params_ftilde_raw
  else:
    try:
      params_ftilde_seq = list(params_ftilde_raw)
    except TypeError:
      params_ftilde = params_ftilde_raw
    else:
      params_ftilde_seq = np.asarray(params_ftilde_seq, dtype=np.float64)
      params_ftilde = np.concatenate((np.array([np.nan], dtype=np.float64), params_ftilde_seq))
  params_malpha_raw = params.malpha
  if isinstance(params_malpha_raw, (str, bytes, dict)):
    params_malpha = params_malpha_raw
  else:
    try:
      params_malpha_seq = list(params_malpha_raw)
    except TypeError:
      params_malpha = params_malpha_raw
    else:
      params_malpha_seq = np.asarray(params_malpha_seq, dtype=np.float64)
      params_malpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_malpha_seq))
  params_mbeta_raw = params.mbeta
  if isinstance(params_mbeta_raw, (str, bytes, dict)):
    params_mbeta = params_mbeta_raw
  else:
    try:
      params_mbeta_seq = list(params_mbeta_raw)
    except TypeError:
      params_mbeta = params_mbeta_raw
    else:
      params_mbeta_seq = np.asarray(params_mbeta_seq, dtype=np.float64)
      params_mbeta = np.concatenate((np.array([np.nan], dtype=np.float64), params_mbeta_seq))
  params_mdelta_raw = params.mdelta
  if isinstance(params_mdelta_raw, (str, bytes, dict)):
    params_mdelta = params_mdelta_raw
  else:
    try:
      params_mdelta_seq = list(params_mdelta_raw)
    except TypeError:
      params_mdelta = params_mdelta_raw
    else:
      params_mdelta_seq = np.asarray(params_mdelta_seq, dtype=np.float64)
      params_mdelta = np.concatenate((np.array([np.nan], dtype=np.float64), params_mdelta_seq))
  params_mgamma_raw = params.mgamma
  if isinstance(params_mgamma_raw, (str, bytes, dict)):
    params_mgamma = params_mgamma_raw
  else:
    try:
      params_mgamma_seq = list(params_mgamma_raw)
    except TypeError:
      params_mgamma = params_mgamma_raw
    else:
      params_mgamma_seq = np.asarray(params_mgamma_seq, dtype=np.float64)
      params_mgamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_mgamma_seq))

  p86_DD = lambda z: jnp.sqrt(f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3)) / jnp.sqrt(2)

  p86_CC = lambda rs: +params_aa + (params_bb + params_malpha * rs + params_mbeta * rs ** 2) / (1 + params_mgamma * rs + params_mdelta * rs ** 2 + 10000.0 * params_mbeta * rs ** 3)

  p86_CCinf = params_aa + params_bb

  p86_x1 = lambda rs, xt: xt / jnp.sqrt(rs / f.RS_FACTOR)

  A_vwn = [None, 0.0310907, 0.01554535, -1 / (6 * jnp.pi ** 2)]

  b_vwn = np.array([np.nan, 3.72744, 7.06042, 1.13107], dtype=np.float64)

  c_vwn = np.array([np.nan, 12.9352, 18.0578, 13.0045], dtype=np.float64)

  x0_vwn = np.array([np.nan, -0.10498, -0.325, -0.0047584], dtype=np.float64)

  Q_vwn = lambda b, c: jnp.sqrt(4 * c - b ** 2)

  f2_vwn = lambda b, c, x0: b * x0 / (x0 ** 2 + b * x0 + c)

  fpp_vwn = 4 / (9 * (2 ** (1 / 3) - 1))

  fx_vwn = lambda b, c, rs: rs + b * jnp.sqrt(rs) + c

  p86_mPhi = lambda rs, xt: params_ftilde * (p86_CCinf / p86_CC(rs)) * p86_x1(rs, xt)

  f1_vwn = lambda b, c: 2 * b / Q_vwn(b, c)

  f3_vwn = lambda b, c, x0: 2 * (2 * x0 + b) / Q_vwn(b, c)

  p86_H = lambda rs, z, xt: p86_x1(rs, xt) ** 2 * jnp.exp(-p86_mPhi(rs, xt)) * p86_CC(rs) / p86_DD(z)

  f_aux = lambda A, b, c, x0, rs: A * (+jnp.log(rs / fx_vwn(b, c, rs)) + (f1_vwn(b, c) - f2_vwn(b, c, x0) * f3_vwn(b, c, x0)) * jnp.arctan(Q_vwn(b, c) / (2 * jnp.sqrt(rs) + b)) - f2_vwn(b, c, x0) * jnp.log((jnp.sqrt(rs) - x0) ** 2 / fx_vwn(b, c, rs)))

  DMC = lambda rs, z=None: +f_aux(A_vwn[2], b_vwn[2], c_vwn[2], x0_vwn[2], rs) - f_aux(A_vwn[1], b_vwn[1], c_vwn[1], x0_vwn[1], rs)

  f_vwn = lambda rs, z: +f_aux(A_vwn[1], b_vwn[1], c_vwn[1], x0_vwn[1], rs) + f_aux(A_vwn[3], b_vwn[3], c_vwn[3], x0_vwn[3], rs) * f.f_zeta(z) * (1 - z ** 4) / fpp_vwn + DMC(rs, z) * f.f_zeta(z) * z ** 4

  f_p86 = lambda rs, z, xt, xs0=None, xs1=None: f_vwn(rs, z) + p86_H(rs, z, xt)

  functional_body = lambda rs, z, xt, xs0, xs1: f_p86(rs, z, xt, xs0, xs1)

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
  params_aa_raw = params.aa
  if isinstance(params_aa_raw, (str, bytes, dict)):
    params_aa = params_aa_raw
  else:
    try:
      params_aa_seq = list(params_aa_raw)
    except TypeError:
      params_aa = params_aa_raw
    else:
      params_aa_seq = np.asarray(params_aa_seq, dtype=np.float64)
      params_aa = np.concatenate((np.array([np.nan], dtype=np.float64), params_aa_seq))
  params_bb_raw = params.bb
  if isinstance(params_bb_raw, (str, bytes, dict)):
    params_bb = params_bb_raw
  else:
    try:
      params_bb_seq = list(params_bb_raw)
    except TypeError:
      params_bb = params_bb_raw
    else:
      params_bb_seq = np.asarray(params_bb_seq, dtype=np.float64)
      params_bb = np.concatenate((np.array([np.nan], dtype=np.float64), params_bb_seq))
  params_ftilde_raw = params.ftilde
  if isinstance(params_ftilde_raw, (str, bytes, dict)):
    params_ftilde = params_ftilde_raw
  else:
    try:
      params_ftilde_seq = list(params_ftilde_raw)
    except TypeError:
      params_ftilde = params_ftilde_raw
    else:
      params_ftilde_seq = np.asarray(params_ftilde_seq, dtype=np.float64)
      params_ftilde = np.concatenate((np.array([np.nan], dtype=np.float64), params_ftilde_seq))
  params_malpha_raw = params.malpha
  if isinstance(params_malpha_raw, (str, bytes, dict)):
    params_malpha = params_malpha_raw
  else:
    try:
      params_malpha_seq = list(params_malpha_raw)
    except TypeError:
      params_malpha = params_malpha_raw
    else:
      params_malpha_seq = np.asarray(params_malpha_seq, dtype=np.float64)
      params_malpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_malpha_seq))
  params_mbeta_raw = params.mbeta
  if isinstance(params_mbeta_raw, (str, bytes, dict)):
    params_mbeta = params_mbeta_raw
  else:
    try:
      params_mbeta_seq = list(params_mbeta_raw)
    except TypeError:
      params_mbeta = params_mbeta_raw
    else:
      params_mbeta_seq = np.asarray(params_mbeta_seq, dtype=np.float64)
      params_mbeta = np.concatenate((np.array([np.nan], dtype=np.float64), params_mbeta_seq))
  params_mdelta_raw = params.mdelta
  if isinstance(params_mdelta_raw, (str, bytes, dict)):
    params_mdelta = params_mdelta_raw
  else:
    try:
      params_mdelta_seq = list(params_mdelta_raw)
    except TypeError:
      params_mdelta = params_mdelta_raw
    else:
      params_mdelta_seq = np.asarray(params_mdelta_seq, dtype=np.float64)
      params_mdelta = np.concatenate((np.array([np.nan], dtype=np.float64), params_mdelta_seq))
  params_mgamma_raw = params.mgamma
  if isinstance(params_mgamma_raw, (str, bytes, dict)):
    params_mgamma = params_mgamma_raw
  else:
    try:
      params_mgamma_seq = list(params_mgamma_raw)
    except TypeError:
      params_mgamma = params_mgamma_raw
    else:
      params_mgamma_seq = np.asarray(params_mgamma_seq, dtype=np.float64)
      params_mgamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_mgamma_seq))

  p86_DD = lambda z: jnp.sqrt(f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3)) / jnp.sqrt(2)

  p86_CC = lambda rs: +params_aa + (params_bb + params_malpha * rs + params_mbeta * rs ** 2) / (1 + params_mgamma * rs + params_mdelta * rs ** 2 + 10000.0 * params_mbeta * rs ** 3)

  p86_CCinf = params_aa + params_bb

  p86_x1 = lambda rs, xt: xt / jnp.sqrt(rs / f.RS_FACTOR)

  A_vwn = [None, 0.0310907, 0.01554535, -1 / (6 * jnp.pi ** 2)]

  b_vwn = np.array([np.nan, 3.72744, 7.06042, 1.13107], dtype=np.float64)

  c_vwn = np.array([np.nan, 12.9352, 18.0578, 13.0045], dtype=np.float64)

  x0_vwn = np.array([np.nan, -0.10498, -0.325, -0.0047584], dtype=np.float64)

  Q_vwn = lambda b, c: jnp.sqrt(4 * c - b ** 2)

  f2_vwn = lambda b, c, x0: b * x0 / (x0 ** 2 + b * x0 + c)

  fpp_vwn = 4 / (9 * (2 ** (1 / 3) - 1))

  fx_vwn = lambda b, c, rs: rs + b * jnp.sqrt(rs) + c

  p86_mPhi = lambda rs, xt: params_ftilde * (p86_CCinf / p86_CC(rs)) * p86_x1(rs, xt)

  f1_vwn = lambda b, c: 2 * b / Q_vwn(b, c)

  f3_vwn = lambda b, c, x0: 2 * (2 * x0 + b) / Q_vwn(b, c)

  p86_H = lambda rs, z, xt: p86_x1(rs, xt) ** 2 * jnp.exp(-p86_mPhi(rs, xt)) * p86_CC(rs) / p86_DD(z)

  f_aux = lambda A, b, c, x0, rs: A * (+jnp.log(rs / fx_vwn(b, c, rs)) + (f1_vwn(b, c) - f2_vwn(b, c, x0) * f3_vwn(b, c, x0)) * jnp.arctan(Q_vwn(b, c) / (2 * jnp.sqrt(rs) + b)) - f2_vwn(b, c, x0) * jnp.log((jnp.sqrt(rs) - x0) ** 2 / fx_vwn(b, c, rs)))

  DMC = lambda rs, z=None: +f_aux(A_vwn[2], b_vwn[2], c_vwn[2], x0_vwn[2], rs) - f_aux(A_vwn[1], b_vwn[1], c_vwn[1], x0_vwn[1], rs)

  f_vwn = lambda rs, z: +f_aux(A_vwn[1], b_vwn[1], c_vwn[1], x0_vwn[1], rs) + f_aux(A_vwn[3], b_vwn[3], c_vwn[3], x0_vwn[3], rs) * f.f_zeta(z) * (1 - z ** 4) / fpp_vwn + DMC(rs, z) * f.f_zeta(z) * z ** 4

  f_p86 = lambda rs, z, xt, xs0=None, xs1=None: f_vwn(rs, z) + p86_H(rs, z, xt)

  functional_body = lambda rs, z, xt, xs0, xs1: f_p86(rs, z, xt, xs0, xs1)

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
  t12 = t11 / 0.4e1
  t13 = jnp.sqrt(t11)
  t15 = t12 + 0.18637200000000000000000000000000000000000000000000e1 * t13 + 0.129352e2
  t16 = 0.1e1 / t15
  t20 = jnp.log(t4 * t10 * t16 / 0.4e1)
  t21 = 0.310907e-1 * t20
  t22 = t13 + 0.372744e1
  t25 = jnp.arctan(0.61519908197590802321728722658814145360143502774884e1 / t22)
  t26 = 0.38783294878113014394824731224995739188004877421366e-1 * t25
  t27 = t13 / 0.2e1
  t28 = t27 + 0.10498e0
  t29 = t28 ** 2
  t31 = jnp.log(t29 * t16)
  t32 = 0.96902277115443742137603943210562149050493484994510e-3 * t31
  t33 = jnp.pi ** 2
  t34 = 0.1e1 / t33
  t36 = t12 + 0.56553500000000000000000000000000000000000000000000e0 * t13 + 0.130045e2
  t37 = 0.1e1 / t36
  t41 = jnp.log(t4 * t10 * t37 / 0.4e1)
  t42 = t13 + 0.113107e1
  t45 = jnp.arctan(0.71231089178181179907634622339714221951452652573438e1 / t42)
  t47 = t27 + 0.47584e-2
  t48 = t47 ** 2
  t50 = jnp.log(t48 * t37)
  t53 = t34 * (t41 + 0.31770800474394146398819696256107927053514547209957e0 * t45 + 0.41403379428206274608377249480129098139321562919141e-3 * t50)
  t54 = r0 - r1
  t55 = 0.1e1 / t7
  t56 = t54 * t55
  t57 = 0.1e1 + t56
  t58 = t57 <= f.p.zeta_threshold
  t59 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t60 = t59 * f.p.zeta_threshold
  t61 = t57 ** (0.1e1 / 0.3e1)
  t63 = f.my_piecewise3(t58, t60, t61 * t57)
  t64 = 0.1e1 - t56
  t65 = t64 <= f.p.zeta_threshold
  t66 = t64 ** (0.1e1 / 0.3e1)
  t68 = f.my_piecewise3(t65, t60, t66 * t64)
  t69 = t63 + t68 - 0.2e1
  t70 = t53 * t69
  t71 = 2 ** (0.1e1 / 0.3e1)
  t72 = t71 - 0.1e1
  t74 = 0.1e1 / t72 / 0.2e1
  t75 = t54 ** 2
  t76 = t75 ** 2
  t77 = t7 ** 2
  t78 = t77 ** 2
  t79 = 0.1e1 / t78
  t83 = 0.9e1 / 0.4e1 * t72
  t84 = t74 * (-t76 * t79 + 0.1e1) * t83
  t86 = t70 * t84 / 0.6e1
  t88 = t12 + 0.35302100000000000000000000000000000000000000000000e1 * t13 + 0.180578e2
  t89 = 0.1e1 / t88
  t93 = jnp.log(t4 * t10 * t89 / 0.4e1)
  t95 = t13 + 0.706042e1
  t98 = jnp.arctan(0.47309269095601128299619512910246923284397083311420e1 / t95)
  t100 = t27 + 0.32500e0
  t101 = t100 ** 2
  t103 = jnp.log(t101 * t89)
  t105 = 0.1554535e-1 * t93 + 0.52491393169780936217021346072241076933841385384498e-1 * t98 + 0.22478670955426118383265363956423012380560746650571e-2 * t103 - t21 - t26 - t32
  t106 = t105 * t69
  t107 = t74 * t76
  t108 = t107 * t79
  t109 = t106 * t108
  t111 = s0 + 0.2e1 * s1 + s2
  t113 = 0.1e1 / t8 / t77
  t114 = t111 * t113
  t115 = params.aa + params.bb
  t116 = params.ftilde * t115
  t117 = params.malpha * t1
  t118 = t3 * t6
  t119 = t118 * t9
  t122 = t1 ** 2
  t123 = params.mbeta * t122
  t124 = t3 ** 2
  t125 = t124 * t5
  t126 = t8 ** 2
  t128 = t125 / t126
  t131 = params.bb + t117 * t119 / 0.4e1 + t123 * t128 / 0.4e1
  t132 = params.mgamma * t1
  t135 = params.mdelta * t122
  t138 = params.mbeta * t2
  t141 = 0.1e1 + t132 * t119 / 0.4e1 + t135 * t128 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t138 * t55
  t142 = 0.1e1 / t141
  t144 = t131 * t142 + params.aa
  t146 = jnp.sqrt(t111)
  t147 = 0.1e1 / t144 * t146
  t148 = t7 ** (0.1e1 / 0.6e1)
  t150 = 0.1e1 / t148 / t7
  t153 = jnp.exp(-t116 * t147 * t150)
  t154 = t114 * t153
  t155 = t59 ** 2
  t156 = t155 * f.p.zeta_threshold
  t157 = t61 ** 2
  t159 = f.my_piecewise3(t58, t156, t157 * t57)
  t160 = t66 ** 2
  t162 = f.my_piecewise3(t65, t156, t160 * t64)
  t163 = t159 + t162
  t164 = jnp.sqrt(t163)
  t165 = 0.1e1 / t164
  t167 = jnp.sqrt(0.2e1)
  t168 = t144 * t165 * t167
  t169 = t154 * t168
  t171 = 0.1e1 / t8 / t7
  t172 = t6 * t171
  t176 = t4 * t6
  t177 = t15 ** 2
  t178 = 0.1e1 / t177
  t180 = t4 * t172
  t181 = t180 / 0.12e2
  t182 = 0.1e1 / t13
  t184 = t118 * t171
  t185 = t182 * t1 * t184
  t187 = -t181 - 0.31062000000000000000000000000000000000000000000000e0 * t185
  t193 = 0.1e1 / t3
  t195 = t5 * t8
  t198 = 0.10363566666666666666666666666666666666666666666667e-1 * (-t4 * t172 * t16 / 0.12e2 - t176 * t9 * t178 * t187 / 0.4e1) * t122 * t193 * t195 * t15
  t199 = t22 ** 2
  t200 = 0.1e1 / t199
  t209 = 0.39765745675026770180313930393880960493473766078662e-1 * t200 * t182 * t1 * t118 * t171 / (0.1e1 + 0.37846991046400000000000000000000000000000000000000e2 * t200)
  t220 = 0.96902277115443742137603943210562149050493484994510e-3 * (-t28 * t16 * t182 * t180 / 0.6e1 - t29 * t178 * t187) / t29 * t15
  t224 = t36 ** 2
  t225 = 0.1e1 / t224
  t228 = -t181 - 0.94255833333333333333333333333333333333333333333334e-1 * t185
  t238 = t42 ** 2
  t239 = 0.1e1 / t238
  t264 = t34 * ((-t4 * t172 * t37 / 0.12e2 - t176 * t9 * t225 * t228 / 0.4e1) * t122 * t193 * t195 * t36 / 0.3e1 + 0.37717812030896172972515701416987212375477090048242e0 * t239 * t182 * t1 * t118 * t171 / (0.1e1 + 0.50738680655100000000000000000000000000000000000000e2 * t239) + 0.41403379428206274608377249480129098139321562919141e-3 * (-t47 * t37 * t182 * t180 / 0.6e1 - t48 * t225 * t228) / t48 * t36) * t69 * t84 / 0.6e1
  t265 = 0.1e1 / t77
  t266 = t54 * t265
  t267 = t55 - t266
  t270 = f.my_piecewise3(t58, 0, 0.4e1 / 0.3e1 * t61 * t267)
  t271 = -t267
  t274 = f.my_piecewise3(t65, 0, 0.4e1 / 0.3e1 * t66 * t271)
  t275 = t270 + t274
  t279 = t75 * t54
  t280 = t279 * t79
  t282 = 0.1e1 / t78 / t7
  t283 = t76 * t282
  t293 = t88 ** 2
  t294 = 0.1e1 / t293
  t297 = -t181 - 0.58836833333333333333333333333333333333333333333333e0 * t185
  t307 = t95 ** 2
  t308 = 0.1e1 / t307
  t331 = (0.51817833333333333333333333333333333333333333333333e-2 * (-t4 * t172 * t89 / 0.12e2 - t176 * t9 * t294 * t297 / 0.4e1) * t122 * t193 * t195 * t88 + 0.41388824077869423260215065147117773567486474051459e-1 * t308 * t182 * t1 * t118 * t171 / (0.1e1 + 0.22381669423600000000000000000000000000000000000000e2 * t308) + 0.22478670955426118383265363956423012380560746650571e-2 * (-t100 * t89 * t182 * t180 / 0.6e1 - t101 * t294 * t297) / t101 * t88 - t198 - t209 - t220) * t69 * t108
  t337 = 0.4e1 * t106 * t74 * t279 * t79
  t340 = 0.4e1 * t106 * t107 * t282
  t341 = t77 * t7
  t347 = 0.7e1 / 0.3e1 * t111 / t8 / t341 * t153 * t168
  t348 = t144 ** 2
  t356 = t125 / t126 / t7
  t361 = t141 ** 2
  t372 = (-t117 * t184 / 0.12e2 - t123 * t356 / 0.6e1) * t142 - t131 / t361 * (-t132 * t184 / 0.12e2 - t135 * t356 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t138 * t265)
  t383 = t165 * t167
  t385 = t114 * (t116 / t348 * t146 * t150 * t372 + 0.7e1 / 0.6e1 * t116 * t147 / t148 / t77) * t153 * t144 * t383
  t388 = t154 * t372 * t165 * t167
  t391 = t144 / t164 / t163
  t394 = f.my_piecewise3(t58, 0, 0.5e1 / 0.3e1 * t157 * t267)
  t397 = f.my_piecewise3(t65, 0, 0.5e1 / 0.3e1 * t160 * t271)
  t403 = t198 + t209 + t220 - t264 - t53 * t275 * t84 / 0.6e1 - t70 * t74 * (-0.4e1 * t280 + 0.4e1 * t283) * t83 / 0.6e1 + t331 + t105 * t275 * t108 + t337 - t340 - t347 + t385 + t388 - t154 * t391 * t167 * (t394 + t397) / 0.2e1
  vrho_0_ = t7 * t403 + t109 + t169 + t21 + t26 + t32 - t86
  t405 = -t55 - t266
  t408 = f.my_piecewise3(t58, 0, 0.4e1 / 0.3e1 * t61 * t405)
  t409 = -t405
  t412 = f.my_piecewise3(t65, 0, 0.4e1 / 0.3e1 * t66 * t409)
  t413 = t408 + t412
  t427 = f.my_piecewise3(t58, 0, 0.5e1 / 0.3e1 * t157 * t405)
  t430 = f.my_piecewise3(t65, 0, 0.5e1 / 0.3e1 * t160 * t409)
  t436 = t198 + t209 + t220 - t264 - t53 * t413 * t84 / 0.6e1 - t70 * t74 * (0.4e1 * t280 + 0.4e1 * t283) * t83 / 0.6e1 + t331 + t105 * t413 * t108 - t337 - t340 - t347 + t385 + t388 - t154 * t391 * t167 * (t427 + t430) / 0.2e1
  vrho_1_ = t7 * t436 + t109 + t169 + t21 + t26 + t32 - t86
  t439 = t113 * t153 * t168
  t440 = jnp.sqrt(t7)
  t447 = t146 / t440 / t341 * params.ftilde * t115 * t153 * t383
  vsigma_0_ = t7 * (t439 - t447 / 0.2e1)
  vsigma_1_ = t7 * (0.2e1 * t439 - t447)
  vsigma_2_ = vsigma_0_
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
  params_aa_raw = params.aa
  if isinstance(params_aa_raw, (str, bytes, dict)):
    params_aa = params_aa_raw
  else:
    try:
      params_aa_seq = list(params_aa_raw)
    except TypeError:
      params_aa = params_aa_raw
    else:
      params_aa_seq = np.asarray(params_aa_seq, dtype=np.float64)
      params_aa = np.concatenate((np.array([np.nan], dtype=np.float64), params_aa_seq))
  params_bb_raw = params.bb
  if isinstance(params_bb_raw, (str, bytes, dict)):
    params_bb = params_bb_raw
  else:
    try:
      params_bb_seq = list(params_bb_raw)
    except TypeError:
      params_bb = params_bb_raw
    else:
      params_bb_seq = np.asarray(params_bb_seq, dtype=np.float64)
      params_bb = np.concatenate((np.array([np.nan], dtype=np.float64), params_bb_seq))
  params_ftilde_raw = params.ftilde
  if isinstance(params_ftilde_raw, (str, bytes, dict)):
    params_ftilde = params_ftilde_raw
  else:
    try:
      params_ftilde_seq = list(params_ftilde_raw)
    except TypeError:
      params_ftilde = params_ftilde_raw
    else:
      params_ftilde_seq = np.asarray(params_ftilde_seq, dtype=np.float64)
      params_ftilde = np.concatenate((np.array([np.nan], dtype=np.float64), params_ftilde_seq))
  params_malpha_raw = params.malpha
  if isinstance(params_malpha_raw, (str, bytes, dict)):
    params_malpha = params_malpha_raw
  else:
    try:
      params_malpha_seq = list(params_malpha_raw)
    except TypeError:
      params_malpha = params_malpha_raw
    else:
      params_malpha_seq = np.asarray(params_malpha_seq, dtype=np.float64)
      params_malpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_malpha_seq))
  params_mbeta_raw = params.mbeta
  if isinstance(params_mbeta_raw, (str, bytes, dict)):
    params_mbeta = params_mbeta_raw
  else:
    try:
      params_mbeta_seq = list(params_mbeta_raw)
    except TypeError:
      params_mbeta = params_mbeta_raw
    else:
      params_mbeta_seq = np.asarray(params_mbeta_seq, dtype=np.float64)
      params_mbeta = np.concatenate((np.array([np.nan], dtype=np.float64), params_mbeta_seq))
  params_mdelta_raw = params.mdelta
  if isinstance(params_mdelta_raw, (str, bytes, dict)):
    params_mdelta = params_mdelta_raw
  else:
    try:
      params_mdelta_seq = list(params_mdelta_raw)
    except TypeError:
      params_mdelta = params_mdelta_raw
    else:
      params_mdelta_seq = np.asarray(params_mdelta_seq, dtype=np.float64)
      params_mdelta = np.concatenate((np.array([np.nan], dtype=np.float64), params_mdelta_seq))
  params_mgamma_raw = params.mgamma
  if isinstance(params_mgamma_raw, (str, bytes, dict)):
    params_mgamma = params_mgamma_raw
  else:
    try:
      params_mgamma_seq = list(params_mgamma_raw)
    except TypeError:
      params_mgamma = params_mgamma_raw
    else:
      params_mgamma_seq = np.asarray(params_mgamma_seq, dtype=np.float64)
      params_mgamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_mgamma_seq))

  p86_DD = lambda z: jnp.sqrt(f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3)) / jnp.sqrt(2)

  p86_CC = lambda rs: +params_aa + (params_bb + params_malpha * rs + params_mbeta * rs ** 2) / (1 + params_mgamma * rs + params_mdelta * rs ** 2 + 10000.0 * params_mbeta * rs ** 3)

  p86_CCinf = params_aa + params_bb

  p86_x1 = lambda rs, xt: xt / jnp.sqrt(rs / f.RS_FACTOR)

  A_vwn = [None, 0.0310907, 0.01554535, -1 / (6 * jnp.pi ** 2)]

  b_vwn = np.array([np.nan, 3.72744, 7.06042, 1.13107], dtype=np.float64)

  c_vwn = np.array([np.nan, 12.9352, 18.0578, 13.0045], dtype=np.float64)

  x0_vwn = np.array([np.nan, -0.10498, -0.325, -0.0047584], dtype=np.float64)

  Q_vwn = lambda b, c: jnp.sqrt(4 * c - b ** 2)

  f2_vwn = lambda b, c, x0: b * x0 / (x0 ** 2 + b * x0 + c)

  fpp_vwn = 4 / (9 * (2 ** (1 / 3) - 1))

  fx_vwn = lambda b, c, rs: rs + b * jnp.sqrt(rs) + c

  p86_mPhi = lambda rs, xt: params_ftilde * (p86_CCinf / p86_CC(rs)) * p86_x1(rs, xt)

  f1_vwn = lambda b, c: 2 * b / Q_vwn(b, c)

  f3_vwn = lambda b, c, x0: 2 * (2 * x0 + b) / Q_vwn(b, c)

  p86_H = lambda rs, z, xt: p86_x1(rs, xt) ** 2 * jnp.exp(-p86_mPhi(rs, xt)) * p86_CC(rs) / p86_DD(z)

  f_aux = lambda A, b, c, x0, rs: A * (+jnp.log(rs / fx_vwn(b, c, rs)) + (f1_vwn(b, c) - f2_vwn(b, c, x0) * f3_vwn(b, c, x0)) * jnp.arctan(Q_vwn(b, c) / (2 * jnp.sqrt(rs) + b)) - f2_vwn(b, c, x0) * jnp.log((jnp.sqrt(rs) - x0) ** 2 / fx_vwn(b, c, rs)))

  DMC = lambda rs, z=None: +f_aux(A_vwn[2], b_vwn[2], c_vwn[2], x0_vwn[2], rs) - f_aux(A_vwn[1], b_vwn[1], c_vwn[1], x0_vwn[1], rs)

  f_vwn = lambda rs, z: +f_aux(A_vwn[1], b_vwn[1], c_vwn[1], x0_vwn[1], rs) + f_aux(A_vwn[3], b_vwn[3], c_vwn[3], x0_vwn[3], rs) * f.f_zeta(z) * (1 - z ** 4) / fpp_vwn + DMC(rs, z) * f.f_zeta(z) * z ** 4

  f_p86 = lambda rs, z, xt, xs0=None, xs1=None: f_vwn(rs, z) + p86_H(rs, z, xt)

  functional_body = lambda rs, z, xt, xs0, xs1: f_p86(rs, z, xt, xs0, xs1)

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
  t11 = t10 / 0.4e1
  t12 = jnp.sqrt(t10)
  t14 = t11 + 0.18637200000000000000000000000000000000000000000000e1 * t12 + 0.129352e2
  t15 = 0.1e1 / t14
  t19 = jnp.log(t4 * t9 * t15 / 0.4e1)
  t21 = t12 + 0.372744e1
  t24 = jnp.arctan(0.61519908197590802321728722658814145360143502774884e1 / t21)
  t26 = t12 / 0.2e1
  t27 = t26 + 0.10498e0
  t28 = t27 ** 2
  t30 = jnp.log(t28 * t15)
  t32 = jnp.pi ** 2
  t33 = 0.1e1 / t32
  t35 = t11 + 0.56553500000000000000000000000000000000000000000000e0 * t12 + 0.130045e2
  t36 = 0.1e1 / t35
  t40 = jnp.log(t4 * t9 * t36 / 0.4e1)
  t41 = t12 + 0.113107e1
  t44 = jnp.arctan(0.71231089178181179907634622339714221951452652573438e1 / t41)
  t46 = t26 + 0.47584e-2
  t47 = t46 ** 2
  t49 = jnp.log(t47 * t36)
  t53 = 0.1e1 <= f.p.zeta_threshold
  t54 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t56 = f.my_piecewise3(t53, t54 * f.p.zeta_threshold, 1)
  t59 = 2 ** (0.1e1 / 0.3e1)
  t60 = t59 - 0.1e1
  t65 = 0.9e1 / 0.4e1 * t56 - 0.9e1 / 0.4e1
  t68 = r0 ** 2
  t70 = 0.1e1 / t7 / t68
  t71 = s0 * t70
  t72 = params.aa + params.bb
  t73 = params.ftilde * t72
  t74 = params.malpha * t1
  t75 = t3 * t6
  t76 = t75 * t8
  t79 = t1 ** 2
  t80 = params.mbeta * t79
  t81 = t3 ** 2
  t82 = t81 * t5
  t83 = t7 ** 2
  t85 = t82 / t83
  t88 = params.bb + t74 * t76 / 0.4e1 + t80 * t85 / 0.4e1
  t89 = params.mgamma * t1
  t92 = params.mdelta * t79
  t95 = params.mbeta * t2
  t99 = 0.1e1 + t89 * t76 / 0.4e1 + t92 * t85 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t95 / r0
  t100 = 0.1e1 / t99
  t102 = t88 * t100 + params.aa
  t104 = jnp.sqrt(s0)
  t105 = 0.1e1 / t102 * t104
  t106 = r0 ** (0.1e1 / 0.6e1)
  t108 = 0.1e1 / t106 / r0
  t111 = jnp.exp(-t73 * t105 * t108)
  t113 = t54 ** 2
  t115 = f.my_piecewise3(t53, t113 * f.p.zeta_threshold, 1)
  t116 = jnp.sqrt(t115)
  t117 = 0.1e1 / t116
  t118 = t111 * t102 * t117
  t121 = 0.1e1 / t7 / r0
  t122 = t6 * t121
  t126 = t4 * t6
  t127 = t14 ** 2
  t128 = 0.1e1 / t127
  t130 = t4 * t122
  t131 = t130 / 0.12e2
  t132 = 0.1e1 / t12
  t134 = t75 * t121
  t135 = t132 * t1 * t134
  t137 = -t131 - 0.31062000000000000000000000000000000000000000000000e0 * t135
  t143 = 0.1e1 / t3
  t145 = t5 * t7
  t149 = t21 ** 2
  t150 = 0.1e1 / t149
  t174 = t35 ** 2
  t175 = 0.1e1 / t174
  t178 = -t131 - 0.94255833333333333333333333333333333333333333333334e-1 * t135
  t188 = t41 ** 2
  t189 = 0.1e1 / t188
  t214 = t68 * r0
  t220 = t102 ** 2
  t228 = t82 / t83 / r0
  t233 = t99 ** 2
  t245 = (-t74 * t134 / 0.12e2 - t80 * t228 / 0.6e1) * t100 - t88 / t233 * (-t89 * t134 / 0.12e2 - t92 * t228 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t95 / t68)
  vrho_0_ = 0.310907e-1 * t19 + 0.38783294878113014394824731224995739188004877421366e-1 * t24 + 0.96902277115443742137603943210562149050493484994510e-3 * t30 - t33 * (t40 + 0.31770800474394146398819696256107927053514547209957e0 * t44 + 0.41403379428206274608377249480129098139321562919141e-3 * t49) * t65 / 0.6e1 + t71 * t118 + r0 * (0.10363566666666666666666666666666666666666666666667e-1 * (-t4 * t122 * t15 / 0.12e2 - t126 * t8 * t128 * t137 / 0.4e1) * t79 * t143 * t145 * t14 + 0.39765745675026770180313930393880960493473766078662e-1 * t150 * t132 * t1 * t75 * t121 / (0.1e1 + 0.37846991046400000000000000000000000000000000000000e2 * t150) + 0.96902277115443742137603943210562149050493484994510e-3 * (-t27 * t15 * t132 * t130 / 0.6e1 - t28 * t128 * t137) / t28 * t14 - t33 * ((-t4 * t122 * t36 / 0.12e2 - t126 * t8 * t175 * t178 / 0.4e1) * t79 * t143 * t145 * t35 / 0.3e1 + 0.37717812030896172972515701416987212375477090048242e0 * t189 * t132 * t1 * t75 * t121 / (0.1e1 + 0.50738680655100000000000000000000000000000000000000e2 * t189) + 0.41403379428206274608377249480129098139321562919141e-3 * (-t46 * t36 * t132 * t130 / 0.6e1 - t47 * t175 * t178) / t47 * t35) * t65 / 0.6e1 - 0.7e1 / 0.3e1 * s0 / t7 / t214 * t118 + t71 * (t73 / t220 * t104 * t108 * t245 + 0.7e1 / 0.6e1 * t73 * t105 / t106 / t68) * t118 + t71 * t111 * t245 * t117)
  t264 = jnp.sqrt(r0)
  vsigma_0_ = r0 * (t70 * t111 * t102 * t117 - t104 / t264 / t214 * params.ftilde * t72 * t111 * t117 / 0.2e1)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
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
  t9 = 0.1e1 / t7 / r0
  t10 = t6 * t9
  t11 = 0.1e1 / t7
  t13 = t4 * t6 * t11
  t14 = t13 / 0.4e1
  t15 = jnp.sqrt(t13)
  t17 = t14 + 0.18637200000000000000000000000000000000000000000000e1 * t15 + 0.129352e2
  t18 = 0.1e1 / t17
  t22 = t4 * t6
  t23 = t17 ** 2
  t24 = 0.1e1 / t23
  t25 = t11 * t24
  t26 = t4 * t10
  t27 = t26 / 0.12e2
  t28 = 0.1e1 / t15
  t29 = t28 * t1
  t30 = t3 * t6
  t31 = t30 * t9
  t32 = t29 * t31
  t34 = -t27 - 0.31062000000000000000000000000000000000000000000000e0 * t32
  t39 = t1 ** 2
  t41 = 0.1e1 / t3
  t42 = (-t4 * t10 * t18 / 0.12e2 - t22 * t25 * t34 / 0.4e1) * t39 * t41
  t43 = t5 * t7
  t44 = t43 * t17
  t47 = t15 + 0.372744e1
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t51 = t49 * t28 * t1
  t53 = 0.1e1 + 0.37846991046400000000000000000000000000000000000000e2 * t49
  t54 = 0.1e1 / t53
  t59 = t15 / 0.2e1
  t60 = t59 + 0.10498e0
  t61 = t60 * t18
  t62 = t61 * t28
  t65 = t60 ** 2
  t66 = t65 * t24
  t68 = -t62 * t26 / 0.6e1 - t66 * t34
  t69 = 0.1e1 / t65
  t70 = t68 * t69
  t73 = jnp.pi ** 2
  t74 = 0.1e1 / t73
  t76 = t14 + 0.56553500000000000000000000000000000000000000000000e0 * t15 + 0.130045e2
  t77 = 0.1e1 / t76
  t81 = t76 ** 2
  t82 = 0.1e1 / t81
  t83 = t11 * t82
  t85 = -t27 - 0.94255833333333333333333333333333333333333333333334e-1 * t32
  t91 = (-t4 * t10 * t77 / 0.12e2 - t22 * t83 * t85 / 0.4e1) * t39 * t41
  t92 = t43 * t76
  t95 = t15 + 0.113107e1
  t96 = t95 ** 2
  t97 = 0.1e1 / t96
  t99 = t97 * t28 * t1
  t101 = 0.1e1 + 0.50738680655100000000000000000000000000000000000000e2 * t97
  t102 = 0.1e1 / t101
  t107 = t59 + 0.47584e-2
  t108 = t107 * t77
  t109 = t108 * t28
  t112 = t107 ** 2
  t113 = t112 * t82
  t115 = -t109 * t26 / 0.6e1 - t113 * t85
  t116 = 0.1e1 / t112
  t117 = t115 * t116
  t122 = 0.1e1 <= f.p.zeta_threshold
  t123 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t125 = f.my_piecewise3(t122, t123 * f.p.zeta_threshold, 1)
  t128 = 2 ** (0.1e1 / 0.3e1)
  t129 = t128 - 0.1e1
  t134 = 0.9e1 * t125 - 0.9e1
  t137 = r0 ** 2
  t138 = t137 * r0
  t140 = 0.1e1 / t7 / t138
  t141 = s0 * t140
  t142 = params.aa + params.bb
  t143 = params.ftilde * t142
  t144 = params.malpha * t1
  t145 = t30 * t11
  t148 = params.mbeta * t39
  t149 = t3 ** 2
  t150 = t149 * t5
  t151 = t7 ** 2
  t152 = 0.1e1 / t151
  t153 = t150 * t152
  t156 = params.bb + t144 * t145 / 0.4e1 + t148 * t153 / 0.4e1
  t157 = params.mgamma * t1
  t160 = params.mdelta * t39
  t163 = params.mbeta * t2
  t167 = 0.1e1 + t157 * t145 / 0.4e1 + t160 * t153 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t163 / r0
  t168 = 0.1e1 / t167
  t170 = t156 * t168 + params.aa
  t171 = 0.1e1 / t170
  t172 = jnp.sqrt(s0)
  t173 = t171 * t172
  t174 = r0 ** (0.1e1 / 0.6e1)
  t176 = 0.1e1 / t174 / r0
  t179 = jnp.exp(-t143 * t173 * t176)
  t181 = t123 ** 2
  t183 = f.my_piecewise3(t122, t181 * f.p.zeta_threshold, 1)
  t184 = jnp.sqrt(t183)
  t185 = 0.1e1 / t184
  t186 = t179 * t170 * t185
  t190 = 0.1e1 / t7 / t137
  t191 = s0 * t190
  t192 = t170 ** 2
  t194 = t143 / t192
  t195 = t172 * t176
  t200 = t150 / t151 / r0
  t203 = -t144 * t31 / 0.12e2 - t148 * t200 / 0.6e1
  t205 = t167 ** 2
  t206 = 0.1e1 / t205
  t207 = t156 * t206
  t215 = -t157 * t31 / 0.12e2 - t160 * t200 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t163 / t137
  t217 = t203 * t168 - t207 * t215
  t221 = 0.1e1 / t174 / t137
  t225 = t194 * t195 * t217 + 0.7e1 / 0.6e1 * t143 * t173 * t221
  t226 = t191 * t225
  t230 = t179 * t217 * t185
  t233 = t6 * t190
  t235 = t4 * t233 * t18
  t242 = 0.1e1 / t23 / t17
  t244 = t34 ** 2
  t248 = t4 * t233
  t249 = t248 / 0.9e1
  t251 = 0.1e1 / t15 / t13
  t254 = 0.1e1 / t151 / t137
  t255 = t150 * t254
  t256 = t251 * t39 * t255
  t258 = t30 * t190
  t259 = t29 * t258
  t261 = t249 - 0.20708000000000000000000000000000000000000000000000e0 * t256 + 0.41416000000000000000000000000000000000000000000000e0 * t259
  t270 = t5 * t152
  t294 = t48 ** 2
  t299 = t53 ** 2
  t314 = t39 * t149 * t5 * t254
  t337 = t4 * t233 * t77
  t344 = 0.1e1 / t81 / t76
  t346 = t85 ** 2
  t352 = t249 - 0.62837222222222222222222222222222222222222222222223e-1 * t256 + 0.12567444444444444444444444444444444444444444444445e0 * t259
  t384 = t96 ** 2
  t389 = t101 ** 2
  t427 = t137 ** 2
  t441 = t217 ** 2
  t461 = t215 ** 2
  t473 = (t144 * t258 / 0.9e1 + 0.5e1 / 0.18e2 * t148 * t255) * t168 - 0.2e1 * t203 * t206 * t215 + 0.2e1 * t156 / t205 / t167 * t461 - t207 * (t157 * t258 / 0.9e1 + 0.5e1 / 0.18e2 * t160 * t255 + 0.15000000000000000000000000000000000000000000000000e5 * t163 / t138)
  t484 = t225 ** 2
  t492 = 0.10363566666666666666666666666666666666666666666667e-1 * (t235 / 0.9e1 + t22 * t9 * t24 * t34 / 0.6e1 + t22 * t11 * t242 * t244 / 0.2e1 - t22 * t25 * t261 / 0.4e1) * t39 * t41 * t44 + 0.34545222222222222222222222222222222222222222222223e-2 * t42 * t270 * t17 + 0.10363566666666666666666666666666666666666666666667e-1 * t42 * t43 * t34 + 0.13255248558342256726771310131293653497824588692887e-1 / t48 / t47 * t1 * t3 * t233 * t54 + 0.26510497116684513453542620262587306995649177385775e-1 * t49 * t251 * t39 * t150 * t254 * t54 - 0.53020994233369026907085240525174613991298354771549e-1 * t51 * t30 * t190 * t54 - 0.50167127350538589836488394571946851238131125013746e0 / t294 / t47 * t1 * t3 * t233 / t299 + 0.96902277115443742137603943210562149050493484994510e-3 * (t235 / 0.72e2 + t60 * t24 * t29 * t30 * t9 * t34 / 0.3e1 - t61 * t251 * t314 / 0.9e1 + 0.2e1 / 0.9e1 * t62 * t248 + 0.2e1 * t65 * t242 * t244 - t66 * t261) * t69 * t17 + 0.16150379519240623689600657201760358175082247499085e-3 * t68 / t65 / t60 * t17 * t28 * t26 + 0.96902277115443742137603943210562149050493484994510e-3 * t70 * t34 - t74 * ((t337 / 0.9e1 + t22 * t9 * t82 * t85 / 0.6e1 + t22 * t11 * t344 * t346 / 0.2e1 - t22 * t83 * t352 / 0.4e1) * t39 * t41 * t92 / 0.3e1 + t91 * t270 * t76 / 0.9e1 + t91 * t43 * t85 / 0.3e1 + 0.12572604010298724324171900472329070791825696682747e0 / t96 / t95 * t1 * t3 * t233 * t102 + 0.25145208020597448648343800944658141583651393365495e0 * t97 * t251 * t39 * t150 * t254 * t102 - 0.50290416041194897296687601889316283167302786730989e0 * t99 * t30 * t190 * t102 - 0.63791733988157656503906862782236557702656491548799e1 / t384 / t95 * t1 * t3 * t233 / t389 + 0.41403379428206274608377249480129098139321562919141e-3 * (t337 / 0.72e2 + t107 * t82 * t29 * t30 * t9 * t85 / 0.3e1 - t108 * t251 * t314 / 0.9e1 + 0.2e1 / 0.9e1 * t109 * t248 + 0.2e1 * t112 * t344 * t346 - t113 * t352) * t116 * t76 + 0.69005632380343791013962082466881830232202604865235e-4 * t115 / t112 / t107 * t76 * t28 * t26 + 0.41403379428206274608377249480129098139321562919141e-3 * t117 * t85) * t134 / 0.24e2 + 0.70e2 / 0.9e1 * s0 / t7 / t427 * t186 - 0.14e2 / 0.3e1 * t141 * t225 * t186 - 0.14e2 / 0.3e1 * t141 * t230 + t191 * (-0.2e1 * t143 / t192 / t170 * t195 * t441 - 0.7e1 / 0.3e1 * t194 * t172 * t221 * t217 + t194 * t195 * t473 - 0.91e2 / 0.36e2 * t143 * t173 / t174 / t138) * t186 + t191 * t484 * t186 + 0.2e1 * t226 * t230 + t191 * t179 * t473 * t185
  v2rho2_0_ = 0.20727133333333333333333333333333333333333333333334e-1 * t42 * t44 + 0.79531491350053540360627860787761920986947532157324e-1 * t51 * t30 * t9 * t54 + 0.19380455423088748427520788642112429810098696998902e-2 * t70 * t17 - t74 * (t91 * t92 / 0.3e1 + 0.37717812030896172972515701416987212375477090048242e0 * t99 * t30 * t9 * t102 + 0.41403379428206274608377249480129098139321562919141e-3 * t117 * t76) * t134 / 0.12e2 - 0.14e2 / 0.3e1 * t141 * t186 + 0.2e1 * t226 * t186 + 0.2e1 * t191 * t230 + r0 * t492
  t494 = t190 * t179
  t495 = t170 * t185
  t497 = jnp.sqrt(r0)
  t499 = 0.1e1 / t497 / t138
  t501 = t172 * t499 * params.ftilde
  t503 = t142 * t179 * t185
  v2rhosigma_0_ = t494 * t495 - t501 * t503 / 0.2e1 + r0 * (-0.7e1 / 0.3e1 * t140 * t179 * t495 + t190 * t225 * t186 + t494 * t217 * t185 + 0.7e1 / 0.4e1 * t172 / t497 / t427 * params.ftilde * t503 - t501 * t142 * t225 * t179 * t185 / 0.2e1)
  t535 = params.ftilde ** 2
  t537 = t142 ** 2
  v2sigma2_0_ = r0 * (-0.3e1 / 0.4e1 * t499 * params.ftilde * t142 / t172 * t179 * t185 + 0.1e1 / t151 / t427 * t535 * t537 * t171 * t179 * t185 / 0.4e1)
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** 2
  t2 = t1 * r0
  t3 = r0 ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t3 / t2
  t6 = s0 * t5
  t8 = params.ftilde * (params.aa + params.bb)
  t9 = 3 ** (0.1e1 / 0.3e1)
  t10 = params.malpha * t9
  t11 = 0.1e1 / jnp.pi
  t12 = t11 ** (0.1e1 / 0.3e1)
  t13 = 4 ** (0.1e1 / 0.3e1)
  t14 = t13 ** 2
  t15 = t12 * t14
  t16 = 0.1e1 / t3
  t17 = t15 * t16
  t20 = t9 ** 2
  t21 = params.mbeta * t20
  t22 = t12 ** 2
  t23 = t22 * t13
  t24 = t3 ** 2
  t25 = 0.1e1 / t24
  t26 = t23 * t25
  t29 = params.bb + t10 * t17 / 0.4e1 + t21 * t26 / 0.4e1
  t30 = params.mgamma * t9
  t33 = params.mdelta * t20
  t36 = params.mbeta * t11
  t40 = 0.1e1 + t30 * t17 / 0.4e1 + t33 * t26 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t36 / r0
  t41 = 0.1e1 / t40
  t43 = t29 * t41 + params.aa
  t44 = t43 ** 2
  t47 = t8 / t44 / t43
  t48 = jnp.sqrt(s0)
  t49 = r0 ** (0.1e1 / 0.6e1)
  t51 = 0.1e1 / t49 / r0
  t52 = t48 * t51
  t54 = 0.1e1 / t3 / r0
  t55 = t15 * t54
  t59 = 0.1e1 / t24 / r0
  t60 = t23 * t59
  t63 = -t10 * t55 / 0.12e2 - t21 * t60 / 0.6e1
  t65 = t40 ** 2
  t66 = 0.1e1 / t65
  t67 = t29 * t66
  t75 = -t30 * t55 / 0.12e2 - t33 * t60 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t36 / t1
  t77 = t63 * t41 - t67 * t75
  t78 = t77 ** 2
  t83 = t8 / t44
  t85 = 0.1e1 / t49 / t1
  t86 = t48 * t85
  t91 = 0.1e1 / t3 / t1
  t92 = t15 * t91
  t96 = 0.1e1 / t24 / t1
  t97 = t23 * t96
  t100 = t10 * t92 / 0.9e1 + 0.5e1 / 0.18e2 * t21 * t97
  t102 = t63 * t66
  t106 = 0.1e1 / t65 / t40
  t107 = t29 * t106
  t108 = t75 ** 2
  t118 = t30 * t92 / 0.9e1 + 0.5e1 / 0.18e2 * t33 * t97 + 0.15000000000000000000000000000000000000000000000000e5 * t36 / t2
  t120 = t100 * t41 - 0.2e1 * t102 * t75 + 0.2e1 * t107 * t108 - t67 * t118
  t124 = 0.1e1 / t43 * t48
  t126 = 0.1e1 / t49 / t2
  t130 = -0.2e1 * t47 * t52 * t78 - 0.7e1 / 0.3e1 * t83 * t86 * t77 + t83 * t52 * t120 - 0.91e2 / 0.36e2 * t8 * t124 * t126
  t134 = jnp.exp(-t8 * t124 * t51)
  t136 = 0.1e1 <= f.p.zeta_threshold
  t137 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t138 = t137 ** 2
  t140 = f.my_piecewise3(t136, t138 * f.p.zeta_threshold, 1)
  t141 = jnp.sqrt(t140)
  t142 = 0.1e1 / t141
  t143 = t134 * t43 * t142
  t146 = t1 ** 2
  t149 = s0 / t3 / t146
  t155 = t83 * t52 * t77 + 0.7e1 / 0.6e1 * t8 * t124 * t85
  t159 = s0 * t91
  t160 = t155 ** 2
  t161 = t159 * t160
  t163 = t134 * t77 * t142
  t166 = t159 * t130
  t169 = t159 * t155
  t171 = t134 * t120 * t142
  t174 = t9 * t12
  t175 = t14 * t54
  t177 = t174 * t14 * t16
  t178 = t177 / 0.4e1
  t179 = jnp.sqrt(t177)
  t181 = t178 + 0.18637200000000000000000000000000000000000000000000e1 * t179 + 0.129352e2
  t182 = 0.1e1 / t181
  t186 = t174 * t14
  t187 = t181 ** 2
  t188 = 0.1e1 / t187
  t189 = t16 * t188
  t190 = t174 * t175
  t191 = t190 / 0.12e2
  t192 = 0.1e1 / t179
  t193 = t192 * t9
  t194 = t193 * t55
  t196 = -t191 - 0.31062000000000000000000000000000000000000000000000e0 * t194
  t202 = 0.1e1 / t12
  t203 = (-t174 * t175 * t182 / 0.12e2 - t186 * t189 * t196 / 0.4e1) * t20 * t202
  t204 = t13 * t25
  t208 = t13 * t3
  t209 = t14 * t91
  t210 = t174 * t209
  t211 = t210 / 0.9e1
  t213 = 0.1e1 / t179 / t177
  t214 = t213 * t20
  t215 = t214 * t97
  t217 = t193 * t92
  t219 = t211 - 0.20708000000000000000000000000000000000000000000000e0 * t215 + 0.41416000000000000000000000000000000000000000000000e0 * t217
  t224 = t174 * t209 * t182
  t226 = t54 * t188
  t231 = 0.1e1 / t187 / t181
  t232 = t16 * t231
  t233 = t196 ** 2
  t242 = (t224 / 0.9e1 + t186 * t226 * t196 / 0.6e1 + t186 * t232 * t233 / 0.2e1 - t186 * t189 * t219 / 0.4e1) * t20 * t202
  t243 = t208 * t196
  t246 = t14 * t5
  t248 = t174 * t246 * t182
  t252 = t186 * t91 * t188 * t196
  t261 = t187 ** 2
  t262 = 0.1e1 / t261
  t264 = t233 * t196
  t268 = t196 * t219
  t272 = t174 * t246
  t273 = 0.7e1 / 0.27e2 * t272
  t274 = t20 * t22
  t278 = 0.1e1 / t179 / t274 / t204 / 0.4e1
  t280 = 0.1e1 / t146
  t281 = t278 * t11 * t280
  t284 = 0.1e1 / t24 / t2
  t285 = t23 * t284
  t286 = t214 * t285
  t288 = t15 * t5
  t289 = t193 * t288
  t291 = -t273 - 0.12424800000000000000000000000000000000000000000000e1 * t281 + 0.82832000000000000000000000000000000000000000000000e0 * t286 - 0.96637333333333333333333333333333333333333333333333e0 * t289
  t298 = t208 * t181
  t307 = t179 + 0.372744e1
  t308 = t307 ** 2
  t309 = t308 ** 2
  t312 = 0.1e1 / t309 / t307 * t9
  t313 = t312 * t12
  t314 = 0.1e1 / t308
  t316 = 0.1e1 + 0.37846991046400000000000000000000000000000000000000e2 * t314
  t317 = t316 ** 2
  t318 = 0.1e1 / t317
  t322 = t204 * t181
  t325 = t13 * t59
  t331 = 0.1e1 / t308 / t307 * t9
  t332 = t331 * t12
  t333 = 0.1e1 / t316
  t337 = t6 * t155
  t340 = t44 ** 2
  t375 = t65 ** 2
  t392 = (-0.7e1 / 0.27e2 * t10 * t288 - 0.20e2 / 0.27e2 * t21 * t285) * t41 - 0.3e1 * t100 * t66 * t75 + 0.6e1 * t63 * t106 * t108 - 0.3e1 * t102 * t118 - 0.6e1 * t29 / t375 * t108 * t75 + 0.6e1 * t107 * t75 * t118 - t67 * (-0.7e1 / 0.27e2 * t30 * t288 - 0.20e2 / 0.27e2 * t33 * t285 - 0.45000000000000000000000000000000000000000000000000e5 * t36 * t280)
  t406 = t11 * t280
  t410 = -0.7e1 * t6 * t130 * t143 + 0.70e2 / 0.3e1 * t149 * t155 * t143 + 0.3e1 * t161 * t163 + 0.3e1 * t166 * t163 + 0.3e1 * t169 * t171 + 0.69090444444444444444444444444444444444444444444446e-2 * t203 * t204 * t196 + 0.10363566666666666666666666666666666666666666666667e-1 * t203 * t208 * t219 + 0.20727133333333333333333333333333333333333333333334e-1 * t242 * t243 + 0.10363566666666666666666666666666666666666666666667e-1 * (-0.7e1 / 0.27e2 * t248 - t252 / 0.3e1 - t186 * t54 * t231 * t233 / 0.2e1 + t186 * t226 * t219 / 0.4e1 - 0.3e1 / 0.2e1 * t186 * t16 * t262 * t264 + 0.3e1 / 0.2e1 * t186 * t232 * t268 - t186 * t189 * t291 / 0.4e1) * t20 * t202 * t298 - 0.7e1 * t6 * t160 * t143 + t159 * t160 * t155 * t143 + 0.18394613361864149606712411343047178787314745838373e1 * t313 * t246 * t318 + 0.69090444444444444444444444444444444444444444444446e-2 * t242 * t322 - 0.23030148148148148148148148148148148148148148148149e-2 * t203 * t325 * t181 - 0.48602578047254941331494803814743396158690158540586e-1 * t332 * t246 * t333 - 0.14e2 * t337 * t163 + t159 * (0.6e1 * t8 / t340 * t52 * t78 * t77 + 0.7e1 * t47 * t86 * t78 - 0.6e1 * t47 * t52 * t77 * t120 + 0.91e2 / 0.12e2 * t83 * t48 * t126 * t77 - 0.7e1 / 0.2e1 * t83 * t86 * t120 + t83 * t52 * t392 + 0.1729e4 / 0.216e3 * t8 * t124 / t49 / t146) * t143 - 0.7e1 * t6 * t171 + 0.15906298270010708072125572157552384197389506431465e0 * t314 * t278 * t406 * t333
  t411 = jnp.pi ** 2
  t412 = 0.1e1 / t411
  t413 = t179 + 0.113107e1
  t414 = t413 ** 2
  t415 = t414 ** 2
  t418 = 0.1e1 / t415 / t413 * t9
  t419 = t418 * t12
  t420 = 0.1e1 / t414
  t422 = 0.1e1 + 0.50738680655100000000000000000000000000000000000000e2 * t420
  t423 = t422 ** 2
  t424 = 0.1e1 / t423
  t429 = 0.1e1 / t422
  t434 = t178 + 0.56553500000000000000000000000000000000000000000000e0 * t179 + 0.130045e2
  t435 = 0.1e1 / t434
  t439 = t434 ** 2
  t440 = 0.1e1 / t439
  t441 = t16 * t440
  t443 = -t191 - 0.94255833333333333333333333333333333333333333333334e-1 * t194
  t449 = (-t174 * t175 * t435 / 0.12e2 - t186 * t441 * t443 / 0.4e1) * t20 * t202
  t452 = t211 - 0.62837222222222222222222222222222222222222222222223e-1 * t215 + 0.12567444444444444444444444444444444444444444444445e0 * t217
  t457 = t174 * t209 * t435
  t459 = t54 * t440
  t464 = 0.1e1 / t439 / t434
  t465 = t16 * t464
  t466 = t443 ** 2
  t475 = (t457 / 0.9e1 + t186 * t459 * t443 / 0.6e1 + t186 * t465 * t466 / 0.2e1 - t186 * t441 * t452 / 0.4e1) * t20 * t202
  t476 = t208 * t443
  t483 = t174 * t246 * t435
  t487 = t186 * t91 * t440 * t443
  t496 = t439 ** 2
  t497 = 0.1e1 / t496
  t499 = t466 * t443
  t503 = t443 * t452
  t510 = -t273 - 0.37702333333333333333333333333333333333333333333334e0 * t281 + 0.25134888888888888888888888888888888888888888888890e0 * t286 - 0.29324037037037037037037037037037037037037037037038e0 * t289
  t517 = t208 * t434
  t520 = t179 / 0.2e1
  t521 = t520 + 0.47584e-2
  t522 = t521 * t435
  t523 = t522 * t192
  t526 = t521 ** 2
  t527 = t526 * t440
  t529 = -t523 * t190 / 0.6e1 - t527 * t443
  t531 = 0.1e1 / t526 / t521
  t532 = t529 * t531
  t533 = t434 * t192
  t534 = t532 * t533
  t538 = t420 * t192 * t9
  t544 = t521 * t440
  t545 = t544 * t193
  t550 = t522 * t213
  t552 = t274 * t13 * t96
  t557 = t526 * t464
  t561 = t457 / 0.72e2 + t545 * t15 * t54 * t443 / 0.3e1 - t550 * t552 / 0.9e1 + 0.2e1 / 0.9e1 * t523 * t210 + 0.2e1 * t557 * t466 - t527 * t452
  t586 = 0.1e1 / t22
  t588 = t9 * t586 * t14
  t589 = t5 * t11
  t595 = t13 * t284
  t596 = t274 * t595
  t607 = -0.11e2 / 0.216e3 * t483 - t487 / 0.24e2 - t521 * t464 * t193 * t15 * t54 * t466 + t544 * t214 * t23 * t96 * t443 / 0.3e1 - 0.2e1 / 0.3e1 * t545 * t15 * t91 * t443 + t545 * t15 * t54 * t452 / 0.2e1 + t588 * t589 * t435 / 0.432e3 - 0.2e1 / 0.3e1 * t522 * t281 + 0.4e1 / 0.9e1 * t550 * t596 - 0.14e2 / 0.27e2 * t523 * t272 - 0.6e1 * t526 * t497 * t499 + 0.6e1 * t557 * t503 - t527 * t510
  t608 = 0.1e1 / t526
  t612 = t561 * t608
  t615 = t529 * t608
  t618 = 0.23390302462324474051432516353486737824307380234560e2 * t419 * t246 * t424 + 0.15087124812358469189006280566794884950190836019297e1 * t420 * t278 * t406 * t429 + t449 * t208 * t452 / 0.3e1 + 0.2e1 / 0.3e1 * t475 * t476 + 0.2e1 / 0.9e1 * t449 * t204 * t443 + (-0.7e1 / 0.27e2 * t483 - t487 / 0.3e1 - t186 * t54 * t464 * t466 / 0.2e1 + t186 * t459 * t452 / 0.4e1 - 0.3e1 / 0.2e1 * t186 * t16 * t497 * t499 + 0.3e1 / 0.2e1 * t186 * t465 * t503 - t186 * t441 * t510 / 0.4e1) * t20 * t202 * t517 / 0.3e1 - 0.92007509840458388018616109955842440309603473153646e-4 * t534 * t210 + 0.11734430409612142702560440440840466072370650237231e1 * t538 * t15 * t5 * t429 + 0.13801126476068758202792416493376366046440520973047e-3 * t561 * t531 * t533 * t190 + 0.41403379428206274608377249480129098139321562919141e-3 * t607 * t608 * t434 + 0.82806758856412549216754498960258196278643125838282e-3 * t612 * t443 + 0.41403379428206274608377249480129098139321562919141e-3 * t615 * t452
  t628 = t420 * t213 * t20
  t633 = t204 * t434
  t641 = 0.1e1 / t414 / t413 * t9
  t642 = t641 * t12
  t671 = t415 ** 2
  t681 = t526 ** 2
  t687 = 0.13801126476068758202792416493376366046440520973047e-3 * t532 * t443 * t192 * t190 + 0.46003754920229194009308054977921220154801736576823e-4 * t532 * t434 * t213 * t552 - 0.10058083208238979459337520377863256633460557346198e1 * t628 * t23 * t284 * t429 + 0.2e1 / 0.9e1 * t475 * t633 - 0.2e1 / 0.27e2 * t449 * t325 * t434 - 0.46099548037761989188630301731873259570027554503406e0 * t642 * t246 * t429 + 0.25145208020597448648343800944658141583651393365494e0 / t415 * t20 * t22 * t595 * t429 * t192 - 0.29769475861140239701823202631710393594573029389440e2 / t415 / t414 * t20 * t22 * t595 * t424 * t192 + 0.20954340017164540540286500787215117986376161137912e-1 * t641 * t586 * t246 * t11 * t429 - 0.10631955664692942750651143797039426283776081924800e1 * t418 * t586 * t246 * t11 * t424 + 0.86312224513605868227832795632565231845861115350066e3 / t671 * t20 * t22 * t595 / t423 / t422 * t192 + 0.17251408095085947753490520616720457558050651216309e-4 * t529 / t681 * t434 * t210
  t691 = f.my_piecewise3(t136, t137 * f.p.zeta_threshold, 1)
  t694 = 2 ** (0.1e1 / 0.3e1)
  t695 = t694 - 0.1e1
  t700 = 0.9e1 * t691 - 0.9e1
  t715 = t520 + 0.10498e0
  t716 = t715 * t188
  t717 = t716 * t193
  t722 = t715 * t182
  t723 = t722 * t213
  t726 = t722 * t192
  t729 = t715 ** 2
  t730 = t729 * t231
  t733 = t729 * t188
  t735 = t224 / 0.72e2 + t717 * t15 * t54 * t196 / 0.3e1 - t723 * t552 / 0.9e1 + 0.2e1 / 0.9e1 * t726 * t210 + 0.2e1 * t730 * t233 - t733 * t219
  t736 = 0.1e1 / t729
  t737 = t735 * t736
  t743 = -t726 * t190 / 0.6e1 - t733 * t196
  t744 = t743 * t736
  t782 = -0.11e2 / 0.216e3 * t248 - t252 / 0.24e2 - t715 * t231 * t193 * t15 * t54 * t233 + t716 * t214 * t23 * t96 * t196 / 0.3e1 - 0.2e1 / 0.3e1 * t717 * t15 * t91 * t196 + t717 * t15 * t54 * t219 / 0.2e1 + t588 * t589 * t182 / 0.432e3 - 0.2e1 / 0.3e1 * t722 * t281 + 0.4e1 / 0.9e1 * t723 * t596 - 0.14e2 / 0.27e2 * t726 * t272 - 0.6e1 * t729 * t262 * t264 + 0.6e1 * t730 * t268 - t733 * t291
  t792 = t314 * t213 * t20
  t798 = t314 * t192 * t9
  t828 = t309 ** 2
  t838 = t729 ** 2
  t845 = 0.1e1 / t729 / t715
  t847 = t181 * t192
  t851 = t743 * t845
  t860 = t851 * t847
  t863 = -t412 * (t618 + t687) * t700 / 0.24e2 - 0.910e3 / 0.27e2 * s0 / t3 / t146 / r0 * t143 + 0.70e2 / 0.3e1 * t149 * t163 + t159 * t134 * t392 * t142 + 0.19380455423088748427520788642112429810098696998902e-2 * t737 * t196 + 0.96902277115443742137603943210562149050493484994510e-3 * t744 * t219 + 0.96902277115443742137603943210562149050493484994510e-3 * t782 * t736 * t181 + 0.3e1 * t166 * t155 * t134 * t43 * t142 - 0.10604198846673805381417048105034922798259670954310e0 * t792 * t23 * t284 * t333 + 0.12371565321119439611653222789207409931302949446695e0 * t798 * t15 * t5 * t333 + 0.26510497116684513453542620262587306995649177385774e-1 / t309 * t20 * t22 * t595 * t333 * t192 - 0.23411326096918008590361250800241863911127858339748e1 / t309 / t308 * t20 * t22 * t595 * t318 * t192 + 0.22092080930570427877952183552156089163040981154812e-2 * t331 * t586 * t246 * t11 * t333 - 0.83611878917564316394147324286578085396885208356242e-1 * t312 * t586 * t246 * t11 * t318 + 0.50631328524251801700246888250186209051365905137714e2 / t828 * t20 * t22 * t595 / t317 / t316 * t192 + 0.40375948798101559224001643004400895437705618747712e-4 * t743 / t838 * t181 * t210 + 0.32300759038481247379201314403520716350164494998170e-3 * t735 * t845 * t847 * t190 + 0.32300759038481247379201314403520716350164494998170e-3 * t851 * t196 * t192 * t190 + 0.10766919679493749126400438134506905450054831666057e-3 * t851 * t181 * t213 * t552 - 0.21533839358987498252800876269013810900109663332113e-3 * t860 * t210
  v3rho3_0_ = r0 * (t410 + t863) + 0.6e1 * t169 * t163 + 0.3e1 * t159 * t171 - 0.14e2 * t6 * t163 + 0.70e2 / 0.3e1 * t149 * t143 + 0.29070683134633122641281182963168644715148045498353e-2 * t737 * t181 + 0.29070683134633122641281182963168644715148045498353e-2 * t744 * t196 + 0.3e1 * t166 * t143 + 0.3e1 * t161 * t143 + 0.31090700000000000000000000000000000000000000000001e-1 * t242 * t298 + 0.10363566666666666666666666666666666666666666666667e-1 * t203 * t322 + 0.31090700000000000000000000000000000000000000000001e-1 * t203 * t243 + 0.39765745675026770180313930393880960493473766078662e-1 * t332 * t209 * t333 - 0.15050138205161576950946518371584055371439337504124e1 * t313 * t209 * t318 - 0.14e2 * t337 * t143 + 0.48451138557721871068801971605281074525246742497255e-3 * t860 * t190 + 0.79531491350053540360627860787761920986947532157324e-1 * t792 * t23 * t96 * t333 - 0.15906298270010708072125572157552384197389506431465e0 * t798 * t15 * t91 * t333 - t412 * (t475 * t517 / 0.3e1 + t449 * t633 / 0.9e1 + t449 * t476 / 0.3e1 + 0.12572604010298724324171900472329070791825696682747e0 * t642 * t209 * t429 + 0.25145208020597448648343800944658141583651393365495e0 * t628 * t23 * t96 * t429 - 0.50290416041194897296687601889316283167302786730989e0 * t538 * t15 * t91 * t429 - 0.63791733988157656503906862782236557702656491548799e1 * t419 * t209 * t424 + 0.41403379428206274608377249480129098139321562919141e-3 * t612 * t434 + 0.69005632380343791013962082466881830232202604865235e-4 * t534 * t190 + 0.41403379428206274608377249480129098139321562919141e-3 * t615 * t443) * t700 / 0.8e1

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** 2
  t2 = r0 ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t2 / t1
  t5 = s0 * t4
  t7 = params.ftilde * (params.aa + params.bb)
  t8 = 3 ** (0.1e1 / 0.3e1)
  t9 = params.malpha * t8
  t10 = 0.1e1 / jnp.pi
  t11 = t10 ** (0.1e1 / 0.3e1)
  t12 = 4 ** (0.1e1 / 0.3e1)
  t13 = t12 ** 2
  t14 = t11 * t13
  t15 = 0.1e1 / t2
  t16 = t14 * t15
  t19 = t8 ** 2
  t20 = params.mbeta * t19
  t21 = t11 ** 2
  t22 = t21 * t12
  t23 = t2 ** 2
  t24 = 0.1e1 / t23
  t25 = t22 * t24
  t28 = params.bb + t9 * t16 / 0.4e1 + t20 * t25 / 0.4e1
  t29 = params.mgamma * t8
  t32 = params.mdelta * t19
  t35 = params.mbeta * t10
  t36 = 0.1e1 / r0
  t39 = 0.1e1 + t29 * t16 / 0.4e1 + t32 * t25 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t35 * t36
  t40 = 0.1e1 / t39
  t42 = t28 * t40 + params.aa
  t44 = jnp.sqrt(s0)
  t45 = 0.1e1 / t42 * t44
  t46 = r0 ** (0.1e1 / 0.6e1)
  t48 = 0.1e1 / t46 / r0
  t51 = jnp.exp(-t7 * t45 * t48)
  t52 = t1 * r0
  t54 = 0.1e1 / t2 / t52
  t55 = t14 * t54
  t59 = 0.1e1 / t23 / t52
  t60 = t22 * t59
  t63 = -0.7e1 / 0.27e2 * t9 * t55 - 0.20e2 / 0.27e2 * t20 * t60
  t65 = t14 * t4
  t69 = 0.1e1 / t23 / t1
  t70 = t22 * t69
  t73 = t9 * t65 / 0.9e1 + 0.5e1 / 0.18e2 * t20 * t70
  t74 = t39 ** 2
  t75 = 0.1e1 / t74
  t76 = t73 * t75
  t78 = 0.1e1 / t2 / r0
  t79 = t14 * t78
  t83 = 0.1e1 / t23 / r0
  t84 = t22 * t83
  t90 = -t29 * t79 / 0.12e2 - t32 * t84 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t35 / t1
  t97 = -t9 * t79 / 0.12e2 - t20 * t84 / 0.6e1
  t99 = 0.1e1 / t74 / t39
  t100 = t97 * t99
  t101 = t90 ** 2
  t104 = t97 * t75
  t112 = t29 * t65 / 0.9e1 + 0.5e1 / 0.18e2 * t32 * t70 + 0.15000000000000000000000000000000000000000000000000e5 * t35 / t52
  t115 = t74 ** 2
  t116 = 0.1e1 / t115
  t117 = t28 * t116
  t118 = t101 * t90
  t121 = t28 * t99
  t122 = t90 * t112
  t125 = t28 * t75
  t130 = t1 ** 2
  t131 = 0.1e1 / t130
  t134 = -0.7e1 / 0.27e2 * t29 * t55 - 0.20e2 / 0.27e2 * t32 * t60 - 0.45000000000000000000000000000000000000000000000000e5 * t35 * t131
  t136 = 0.6e1 * t100 * t101 - 0.3e1 * t104 * t112 - 0.6e1 * t117 * t118 + 0.6e1 * t121 * t122 - t125 * t134 + t63 * t40 - 0.3e1 * t76 * t90
  t138 = 0.1e1 <= f.p.zeta_threshold
  t139 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t140 = t139 ** 2
  t142 = f.my_piecewise3(t138, t140 * f.p.zeta_threshold, 1)
  t143 = jnp.sqrt(t142)
  t144 = 0.1e1 / t143
  t145 = t51 * t136 * t144
  t148 = s0 * t54
  t155 = 0.2e1 * t121 * t101 - 0.2e1 * t104 * t90 - t125 * t112 + t73 * t40
  t157 = t51 * t155 * t144
  t160 = t130 * r0
  t162 = 0.1e1 / t2 / t160
  t163 = s0 * t162
  t164 = t51 * t42
  t165 = t164 * t144
  t169 = 0.1e1 / t2 / t130
  t170 = s0 * t169
  t173 = -t125 * t90 + t97 * t40
  t175 = t51 * t173 * t144
  t178 = jnp.pi ** 2
  t179 = 0.1e1 / t178
  t180 = t8 * t11
  t182 = t180 * t13 * t15
  t183 = jnp.sqrt(t182)
  t184 = t183 + 0.113107e1
  t185 = t184 ** 2
  t186 = t185 ** 2
  t188 = 0.1e1 / t186 / t184
  t189 = t188 * t8
  t190 = t189 * t11
  t191 = t13 * t54
  t192 = 0.1e1 / t185
  t194 = 0.1e1 + 0.50738680655100000000000000000000000000000000000000e2 * t192
  t195 = t194 ** 2
  t196 = 0.1e1 / t195
  t200 = t19 * t21
  t201 = t12 * t24
  t205 = 0.1e1 / t183 / t200 / t201 / 0.4e1
  t206 = t192 * t205
  t207 = t10 * t131
  t208 = 0.1e1 / t194
  t212 = t13 * t78
  t213 = t182 / 0.4e1
  t215 = t213 + 0.56553500000000000000000000000000000000000000000000e0 * t183 + 0.130045e2
  t216 = 0.1e1 / t215
  t220 = t180 * t13
  t221 = t215 ** 2
  t222 = 0.1e1 / t221
  t223 = t15 * t222
  t224 = t180 * t212
  t225 = t224 / 0.12e2
  t226 = 0.1e1 / t183
  t227 = t226 * t8
  t228 = t227 * t79
  t230 = -t225 - 0.94255833333333333333333333333333333333333333333334e-1 * t228
  t236 = 0.1e1 / t11
  t237 = (-t180 * t212 * t216 / 0.12e2 - t220 * t223 * t230 / 0.4e1) * t19 * t236
  t238 = t12 * t2
  t239 = t13 * t4
  t240 = t180 * t239
  t241 = t240 / 0.9e1
  t243 = 0.1e1 / t183 / t182
  t244 = t243 * t19
  t245 = t244 * t70
  t247 = t227 * t65
  t249 = t241 - 0.62837222222222222222222222222222222222222222222223e-1 * t245 + 0.12567444444444444444444444444444444444444444444445e0 * t247
  t250 = t238 * t249
  t254 = t180 * t239 * t216
  t256 = t78 * t222
  t261 = 0.1e1 / t221 / t215
  t262 = t15 * t261
  t263 = t230 ** 2
  t272 = (t254 / 0.9e1 + t220 * t256 * t230 / 0.6e1 + t220 * t262 * t263 / 0.2e1 - t220 * t223 * t249 / 0.4e1) * t19 * t236
  t273 = t238 * t230
  t276 = t201 * t230
  t280 = t180 * t191 * t216
  t282 = t4 * t222
  t284 = t220 * t282 * t230
  t286 = t78 * t261
  t293 = t221 ** 2
  t294 = 0.1e1 / t293
  t295 = t15 * t294
  t296 = t263 * t230
  t300 = t230 * t249
  t304 = t180 * t191
  t305 = 0.7e1 / 0.27e2 * t304
  t306 = t205 * t10
  t307 = t306 * t131
  t309 = t244 * t60
  t311 = t227 * t55
  t313 = -t305 - 0.37702333333333333333333333333333333333333333333334e0 * t307 + 0.25134888888888888888888888888888888888888888888890e0 * t309 - 0.29324037037037037037037037037037037037037037037038e0 * t311
  t319 = (-0.7e1 / 0.27e2 * t280 - t284 / 0.3e1 - t220 * t286 * t263 / 0.2e1 + t220 * t256 * t249 / 0.4e1 - 0.3e1 / 0.2e1 * t220 * t295 * t296 + 0.3e1 / 0.2e1 * t220 * t262 * t300 - t220 * t223 * t313 / 0.4e1) * t19 * t236
  t320 = t238 * t215
  t323 = t183 / 0.2e1
  t324 = t323 + 0.47584e-2
  t325 = t324 * t216
  t326 = t325 * t226
  t329 = t324 ** 2
  t330 = t329 * t222
  t332 = -t326 * t224 / 0.6e1 - t330 * t230
  t334 = 0.1e1 / t329 / t324
  t335 = t332 * t334
  t336 = t215 * t226
  t337 = t335 * t336
  t341 = t192 * t243 * t19
  t347 = t192 * t226 * t8
  t353 = t324 * t222
  t354 = t353 * t227
  t355 = t78 * t230
  t359 = t325 * t243
  t360 = t12 * t69
  t361 = t200 * t360
  t366 = t329 * t261
  t370 = t254 / 0.72e2 + t354 * t14 * t355 / 0.3e1 - t359 * t361 / 0.9e1 + 0.2e1 / 0.9e1 * t326 * t240 + 0.2e1 * t366 * t263 - t330 * t249
  t371 = t370 * t334
  t372 = t371 * t336
  t377 = t324 * t261
  t378 = t377 * t227
  t382 = t353 * t244
  t395 = 0.1e1 / t21
  t397 = t8 * t395 * t13
  t398 = t54 * t10
  t404 = t12 * t59
  t405 = t200 * t404
  t410 = t329 * t294
  t416 = -0.11e2 / 0.216e3 * t280 - t284 / 0.24e2 - t378 * t14 * t78 * t263 + t382 * t22 * t69 * t230 / 0.3e1 - 0.2e1 / 0.3e1 * t354 * t14 * t4 * t230 + t354 * t14 * t78 * t249 / 0.2e1 + t397 * t398 * t216 / 0.432e3 - 0.2e1 / 0.3e1 * t325 * t307 + 0.4e1 / 0.9e1 * t359 * t405 - 0.14e2 / 0.27e2 * t326 * t304 - 0.6e1 * t410 * t296 + 0.6e1 * t366 * t300 - t330 * t313
  t417 = 0.1e1 / t329
  t418 = t416 * t417
  t421 = t370 * t417
  t424 = 0.23390302462324474051432516353486737824307380234560e2 * t190 * t191 * t196 + 0.15087124812358469189006280566794884950190836019297e1 * t206 * t207 * t208 + t237 * t250 / 0.3e1 + 0.2e1 / 0.3e1 * t272 * t273 + 0.2e1 / 0.9e1 * t237 * t276 + t319 * t320 / 0.3e1 - 0.92007509840458388018616109955842440309603473153646e-4 * t337 * t240 - 0.10058083208238979459337520377863256633460557346198e1 * t341 * t22 * t59 * t208 + 0.11734430409612142702560440440840466072370650237231e1 * t347 * t14 * t54 * t208 + 0.13801126476068758202792416493376366046440520973047e-3 * t372 * t224 + 0.41403379428206274608377249480129098139321562919141e-3 * t418 * t215 + 0.82806758856412549216754498960258196278643125838282e-3 * t421 * t230
  t425 = t332 * t417
  t428 = t230 * t226
  t429 = t335 * t428
  t432 = t215 * t243
  t433 = t335 * t432
  t436 = t201 * t215
  t439 = t12 * t83
  t440 = t439 * t215
  t443 = t185 * t184
  t444 = 0.1e1 / t443
  t445 = t444 * t8
  t450 = 0.1e1 / t186
  t451 = t450 * t19
  t452 = t451 * t21
  t453 = t208 * t226
  t458 = 0.1e1 / t186 / t185
  t459 = t458 * t19
  t460 = t459 * t21
  t461 = t196 * t226
  t465 = t445 * t395
  t466 = t10 * t208
  t470 = t189 * t395
  t471 = t10 * t196
  t475 = t186 ** 2
  t476 = 0.1e1 / t475
  t477 = t476 * t19
  t478 = t477 * t21
  t480 = 0.1e1 / t195 / t194
  t481 = t480 * t226
  t485 = t329 ** 2
  t486 = 0.1e1 / t485
  t487 = t332 * t486
  t488 = t487 * t215
  t491 = 0.41403379428206274608377249480129098139321562919141e-3 * t425 * t249 + 0.13801126476068758202792416493376366046440520973047e-3 * t429 * t224 + 0.46003754920229194009308054977921220154801736576823e-4 * t433 * t361 + 0.2e1 / 0.9e1 * t272 * t436 - 0.2e1 / 0.27e2 * t237 * t440 - 0.46099548037761989188630301731873259570027554503406e0 * t445 * t11 * t191 * t208 + 0.25145208020597448648343800944658141583651393365494e0 * t452 * t404 * t453 - 0.29769475861140239701823202631710393594573029389440e2 * t460 * t404 * t461 + 0.20954340017164540540286500787215117986376161137912e-1 * t465 * t191 * t466 - 0.10631955664692942750651143797039426283776081924800e1 * t470 * t191 * t471 + 0.86312224513605868227832795632565231845861115350066e3 * t478 * t404 * t481 + 0.17251408095085947753490520616720457558050651216309e-4 * t488 * t240
  t495 = f.my_piecewise3(t138, t139 * f.p.zeta_threshold, 1)
  t498 = 2 ** (0.1e1 / 0.3e1)
  t499 = t498 - 0.1e1
  t504 = 0.9e1 * t495 - 0.9e1
  t507 = t183 + 0.372744e1
  t508 = t507 ** 2
  t509 = 0.1e1 / t508
  t510 = t509 * t205
  t512 = 0.1e1 + 0.37846991046400000000000000000000000000000000000000e2 * t509
  t513 = 0.1e1 / t512
  t517 = t42 ** 2
  t519 = t7 / t517
  t520 = t44 * t48
  t524 = 0.1e1 / t46 / t1
  t528 = t519 * t520 * t173 + 0.7e1 / 0.6e1 * t7 * t45 * t524
  t529 = t528 ** 2
  t534 = t213 + 0.18637200000000000000000000000000000000000000000000e1 * t183 + 0.129352e2
  t535 = 0.1e1 / t534
  t537 = t180 * t239 * t535
  t539 = t323 + 0.10498e0
  t540 = t534 ** 2
  t541 = 0.1e1 / t540
  t542 = t539 * t541
  t543 = t542 * t227
  t545 = -t225 - 0.31062000000000000000000000000000000000000000000000e0 * t228
  t546 = t78 * t545
  t550 = t539 * t535
  t551 = t550 * t243
  t554 = t550 * t226
  t557 = t539 ** 2
  t559 = 0.1e1 / t540 / t534
  t560 = t557 * t559
  t561 = t545 ** 2
  t564 = t557 * t541
  t567 = t241 - 0.20708000000000000000000000000000000000000000000000e0 * t245 + 0.41416000000000000000000000000000000000000000000000e0 * t247
  t569 = t537 / 0.72e2 + t543 * t14 * t546 / 0.3e1 - t551 * t361 / 0.9e1 + 0.2e1 / 0.9e1 * t554 * t240 + 0.2e1 * t560 * t561 - t564 * t567
  t570 = 0.1e1 / t557
  t571 = t569 * t570
  t577 = -t554 * t224 / 0.6e1 - t564 * t545
  t578 = t577 * t570
  t582 = -t305 - 0.12424800000000000000000000000000000000000000000000e1 * t307 + 0.82832000000000000000000000000000000000000000000000e0 * t309 - 0.96637333333333333333333333333333333333333333333333e0 * t311
  t589 = t169 * t10
  t595 = t220 * t54 * t541 * t545
  t597 = t4 * t541
  t599 = t220 * t597 * t567
  t603 = t220 * t4 * t559 * t561
  t605 = 0.1e1 / t160
  t606 = t306 * t605
  t609 = t13 * t169
  t611 = t180 * t609 * t535
  t613 = t567 ** 2
  t616 = t540 ** 2
  t618 = 0.1e1 / t616 / t534
  t620 = t561 ** 2
  t623 = t180 * t609
  t624 = 0.70e2 / 0.81e2 * t623
  t628 = 0.1e1 / t183 / t10 / t36 / 0.48e2
  t629 = t628 * t10
  t631 = t629 * t162 * t220
  t635 = 0.1e1 / t23 / t130
  t636 = t22 * t635
  t637 = t244 * t636
  t639 = t14 * t169
  t640 = t227 * t639
  t642 = t624 - 0.10354000000000000000000000000000000000000000000000e1 * t631 + 0.99398400000000000000000000000000000000000000000000e1 * t606 - 0.36814222222222222222222222222222222222222222222222e1 * t637 + 0.32212444444444444444444444444444444444444444444444e1 * t640
  t644 = t12 * t635
  t645 = t200 * t644
  t650 = 0.8e1 / 0.3e1 * t542 * t205 * t207 * t545 - 0.11e2 / 0.648e3 * t397 * t589 * t535 + 0.11e2 / 0.54e2 * t595 - t599 / 0.12e2 + t603 / 0.6e1 + 0.16e2 / 0.3e1 * t550 * t606 + 0.185e3 / 0.864e3 * t611 + 0.6e1 * t560 * t613 + 0.24e2 * t557 * t618 * t620 - t564 * t642 - 0.160e3 / 0.81e2 * t551 * t645 + 0.140e3 / 0.81e2 * t554 * t623
  t659 = 0.1e1 / t616
  t662 = t561 * t545
  t667 = t539 * t559
  t668 = t667 * t227
  t673 = t542 * t244
  t697 = t162 * t8 * t14
  t704 = t557 * t659
  t705 = t561 * t567
  t708 = t545 * t582
  t711 = -t397 * t398 * t541 * t545 / 0.108e3 + 0.56e2 / 0.27e2 * t543 * t14 * t54 * t545 + 0.4e1 * t539 * t659 * t227 * t14 * t78 * t662 + 0.8e1 / 0.3e1 * t668 * t14 * t4 * t561 - 0.16e2 / 0.9e1 * t673 * t22 * t59 * t545 - 0.4e1 / 0.3e1 * t667 * t244 * t22 * t69 * t561 + 0.2e1 / 0.3e1 * t673 * t22 * t69 * t567 - 0.4e1 / 0.3e1 * t543 * t14 * t4 * t567 + 0.2e1 / 0.3e1 * t543 * t14 * t78 * t582 - 0.5e1 / 0.9e1 * t550 * t629 * t697 - 0.4e1 * t668 * t14 * t546 * t567 - 0.36e2 * t704 * t705 + 0.8e1 * t560 * t708
  t717 = t180 * t191 * t535
  t720 = t220 * t597 * t545
  t748 = t545 * t567
  t752 = -0.11e2 / 0.216e3 * t717 - t720 / 0.24e2 - t668 * t14 * t78 * t561 + t673 * t22 * t69 * t545 / 0.3e1 - 0.2e1 / 0.3e1 * t543 * t14 * t4 * t545 + t543 * t14 * t78 * t567 / 0.2e1 + t397 * t398 * t535 / 0.432e3 - 0.2e1 / 0.3e1 * t550 * t307 + 0.4e1 / 0.9e1 * t551 * t405 - 0.14e2 / 0.27e2 * t554 * t304 - 0.6e1 * t704 * t662 + 0.6e1 * t560 * t748 - t564 * t582
  t753 = t752 * t570
  t758 = t7 / t517 / t42
  t759 = t173 ** 2
  t763 = t44 * t524
  t770 = 0.1e1 / t46 / t52
  t774 = -0.2e1 * t758 * t520 * t759 - 0.7e1 / 0.3e1 * t519 * t763 * t173 + t519 * t520 * t155 - 0.91e2 / 0.36e2 * t7 * t45 * t770
  t775 = t5 * t774
  t776 = t528 * t51
  t781 = t508 ** 2
  t783 = 0.1e1 / t781 / t507
  t784 = t783 * t8
  t785 = t784 * t395
  t786 = t512 ** 2
  t787 = 0.1e1 / t786
  t788 = t10 * t787
  t792 = t557 ** 2
  t793 = 0.1e1 / t792
  t794 = t577 * t793
  t795 = t794 * t534
  t798 = t148 * t774
  t800 = t776 * t42 * t144
  t803 = t517 ** 2
  t805 = t7 / t803
  t806 = t759 * t173
  t813 = t173 * t155
  t817 = t44 * t770
  t827 = 0.1e1 / t46 / t130
  t831 = 0.6e1 * t805 * t520 * t806 + 0.7e1 * t758 * t763 * t759 - 0.6e1 * t758 * t520 * t813 + 0.91e2 / 0.12e2 * t519 * t817 * t173 - 0.7e1 / 0.2e1 * t519 * t763 * t155 + t519 * t520 * t136 + 0.1729e4 / 0.216e3 * t7 * t45 * t827
  t832 = t5 * t831
  t836 = t509 * t243 * t19
  t842 = t509 * t226 * t8
  t850 = t236 * t12
  t854 = t508 * t507
  t863 = t781 ** 2
  t869 = 0.1e1 / t786 / t512
  t878 = t786 ** 2
  t892 = 0.1e1 / t854 * t8
  t893 = t892 * t395
  t894 = t10 * t513
  t898 = 0.140e3 / 0.3e1 * t170 * t529 * t165 + 0.29070683134633122641281182963168644715148045498353e-2 * t571 * t567 + 0.96902277115443742137603943210562149050493484994510e-3 * t578 * t582 + 0.96902277115443742137603943210562149050493484994510e-3 * (t650 + t711) * t570 * t534 + 0.29070683134633122641281182963168644715148045498353e-2 * t753 * t545 + 0.12e2 * t775 * t776 * t173 * t144 + 0.61315377872880498689041371143490595957715819461244e0 * t785 * t609 * t788 - 0.14804514559303905048800602434946994993825393540828e-3 * t795 * t304 - 0.28e2 * t798 * t800 + 0.4e1 * t832 * t800 + 0.47129772651883579472964658244599656881154093130267e0 * t836 * t22 * t635 * t513 - 0.41238551070398132038844075964024699771009831488983e0 * t842 * t14 * t169 * t513 + 0.17673664744456342302361746841724871330432784923849e-1 * t783 * t10 * t635 * t513 * t19 * t850 - 0.26755801253620581246127143771704987327003266673998e1 / t781 / t854 * t10 * t635 * t787 * t19 * t850 + 0.12657832131062950425061722062546552262841476284429e3 / t863 / t507 * t10 * t635 * t869 * t19 * t850 - 0.19162434373246948642083122762742588170998040494372e4 / t863 / t854 * t10 * t635 / t878 * t19 * t850 + 0.12112784639430467767200492901320268631311685624314e-3 * t569 * t793 * t534 * t240 + 0.12112784639430467767200492901320268631311685624314e-3 * t794 * t545 * t240 - 0.16200859349084980443831601271581132052896719513529e-1 * t893 * t609 * t894
  t899 = 0.1e1 / t781
  t900 = t899 * t19
  t901 = t900 * t21
  t902 = t513 * t226
  t907 = 0.1e1 / t781 / t508
  t908 = t907 * t19
  t909 = t908 * t21
  t910 = t787 * t226
  t914 = 0.1e1 / t863
  t915 = t914 * t19
  t916 = t915 * t21
  t917 = t869 * t226
  t921 = t5 * t529
  t951 = t10 * t605
  t955 = t5 * t528
  t960 = t78 * t559
  t964 = t78 * t541
  t968 = t15 * t659
  t972 = t15 * t559
  t976 = t15 * t541
  t982 = (-0.7e1 / 0.27e2 * t717 - t720 / 0.3e1 - t220 * t960 * t561 / 0.2e1 + t220 * t964 * t567 / 0.4e1 - 0.3e1 / 0.2e1 * t220 * t968 * t662 + 0.3e1 / 0.2e1 * t220 * t972 * t748 - t220 * t976 * t582 / 0.4e1) * t19 * t236
  t983 = t238 * t545
  t987 = t180 * t609 * t216
  t991 = t220 * t54 * t222 * t230
  t995 = t220 * t4 * t261 * t263
  t998 = t220 * t282 * t249
  t1011 = 0.1e1 / t293 / t215
  t1013 = t263 ** 2
  t1017 = t263 * t249
  t1021 = t249 ** 2
  t1025 = t230 * t313
  t1033 = t624 - 0.31418611111111111111111111111111111111111111111112e0 * t631 + 0.30161866666666666666666666666666666666666666666668e1 * t606 - 0.11171061728395061728395061728395061728395061728396e1 * t637 + 0.97746790123456790123456790123456790123456790123460e0 * t640
  t1037 = 0.70e2 / 0.81e2 * t987 + 0.28e2 / 0.27e2 * t991 + 0.4e1 / 0.3e1 * t995 - 0.2e1 / 0.3e1 * t998 + 0.2e1 * t220 * t78 * t294 * t296 - 0.2e1 * t220 * t286 * t300 + t220 * t256 * t313 / 0.3e1 + 0.6e1 * t220 * t15 * t1011 * t1013 - 0.9e1 * t220 * t295 * t1017 + 0.3e1 / 0.2e1 * t220 * t262 * t1021 + 0.2e1 * t220 * t262 * t1025 - t220 * t223 * t1033 / 0.4e1
  t1070 = t1037 * t19 * t236 * t320 / 0.3e1 + 0.2e1 / 0.3e1 * t272 * t276 - 0.2e1 / 0.9e1 * t237 * t439 * t230 + t237 * t201 * t249 / 0.3e1 - 0.98345589898409720443523080122614693124928757804400e2 * t190 * t609 * t196 - 0.2e1 / 0.9e1 * t272 * t440 + 0.10e2 / 0.81e2 * t237 * t360 * t215 + 0.27602252952137516405584832986752732092881041946094e-3 * t335 * t215 * t307 + 0.19382764515877199999765013228173984137397949052568e1 * t444 * t169 * t208 * t220 + t272 * t250 + t237 * t238 * t313 / 0.3e1 + t319 * t273
  t1098 = -0.11e2 / 0.648e3 * t397 * t589 * t216 + 0.11e2 / 0.54e2 * t991 - t998 / 0.12e2 + t995 / 0.6e1 + 0.8e1 / 0.3e1 * t353 * t205 * t207 * t230 + 0.185e3 / 0.864e3 * t987 + 0.16e2 / 0.3e1 * t325 * t606 + 0.24e2 * t329 * t1011 * t1013 + 0.6e1 * t366 * t1021 - t330 * t1033 - t397 * t398 * t222 * t230 / 0.108e3 - 0.160e3 / 0.81e2 * t359 * t645
  t1147 = 0.140e3 / 0.81e2 * t326 * t623 - 0.4e1 / 0.3e1 * t377 * t244 * t22 * t69 * t263 + 0.2e1 / 0.3e1 * t382 * t22 * t69 * t249 - 0.4e1 / 0.3e1 * t354 * t14 * t4 * t249 + 0.4e1 * t324 * t294 * t227 * t14 * t78 * t296 + 0.8e1 / 0.3e1 * t378 * t14 * t4 * t263 - 0.16e2 / 0.9e1 * t382 * t22 * t59 * t230 + 0.56e2 / 0.27e2 * t354 * t14 * t54 * t230 + 0.2e1 / 0.3e1 * t354 * t14 * t78 * t313 - 0.5e1 / 0.9e1 * t325 * t629 * t697 - 0.4e1 * t378 * t14 * t355 * t249 - 0.36e2 * t410 * t1017 + 0.8e1 * t366 * t1025
  t1170 = t195 ** 2
  t1202 = t319 * t436 / 0.3e1 + 0.41403379428206274608377249480129098139321562919141e-3 * (t1098 + t1147) * t417 * t215 + 0.12421013828461882382513174844038729441796468875742e-2 * t418 * t230 + 0.12421013828461882382513174844038729441796468875742e-2 * t421 * t249 + 0.41403379428206274608377249480129098139321562919141e-3 * t425 * t313 + 0.21578056128401467056958198908141307961465278837517e4 / t475 / t184 * t10 * t635 * t480 * t19 * t850 - 0.43793683962271420729973795871593892966464398384137e5 / t475 / t443 * t10 * t635 / t1170 * t19 * t850 - 0.18439819215104795675452120692749303828011021801362e1 * t452 * t644 * t453 + 0.16763472013731632432229200629772094389100928910329e0 * t188 * t10 * t635 * t208 * t19 * t850 - 0.34022258127017416802083660150526164108083462159360e2 / t186 / t443 * t10 * t635 * t196 * t19 * t850 + 0.51754224285257843260471561850161372674151953648927e-4 * t487 * t230 * t240 + 0.21830948964836175781337015263254288636020221552256e3 * t460 * t644 * t461 - 0.63295631309977636700410716797214503353631484590049e4 * t478 * t644 * t481
  t1231 = t395 * t13 * t398
  t1242 = t635 * t10
  t1252 = t22 * t59 * t226
  t1255 = 0.51754224285257843260471561850161372674151953648927e-4 * t370 * t486 * t215 * t240 - 0.63255163015315141762798575594641677712852387793133e-4 * t488 * t304 - 0.15366516012587329729543433910624419856675851501136e0 * t465 * t609 * t466 + 0.77967674874414913504775054511622459414357934115200e1 * t470 * t609 * t471 + 0.44702592036617686485944535012725585037602477094213e1 * t341 * t22 * t635 * t208 - 0.39114768032040475675201468136134886907902167457437e1 * t347 * t14 * t169 * t208 + 0.13801126476068758202792416493376366046440520973047e-3 * t335 * t230 * t243 * t361 + 0.28752346825143246255817534361200762596751085360514e-5 * t487 * t215 * t8 * t1231 + 0.20701689714103137304188624740064549069660781459570e-3 * t335 * t249 * t226 * t224 + 0.41403379428206274608377249480129098139321562919141e-3 * t371 * t428 * t224 + 0.14385370752267644704638799272094205307643519225011e3 * t477 * t850 * t1242 * t481 + 0.23001877460114597004654027488960610077400868288412e-4 * t332 / t485 / t324 * t215 * t19 * t1252
  t1263 = t10 * t162
  t1304 = 0.41908680034329081080573001574430235972752322275824e-1 * t451 * t850 * t1242 * t453 + 0.21468418962773623871010425656363236072240810402517e-3 * t337 * t304 + 0.12572604010298724324171900472329070791825696682747e1 * t192 * t628 * t1263 * t208 * t8 * t14 - 0.27602252952137516405584832986752732092881041946094e-3 * t372 * t240 + 0.20701689714103137304188624740064549069660781459570e-3 * t416 * t334 * t336 * t224 + 0.13801126476068758202792416493376366046440520973047e-3 * t371 * t432 * t361 - 0.27602252952137516405584832986752732092881041946094e-3 * t429 * t240 - 0.18401501968091677603723221991168488061920694630729e-3 * t433 * t405 - 0.49615793101900399503038671052850655990955048982400e1 * t459 * t850 * t1242 * t461 + 0.17262444902721173645566559126513046369172223070013e4 * t476 * t10 * t605 * t480 * t243 - 0.59538951722280479403646405263420787189146058778880e2 * t458 * t10 * t605 * t196 * t243 + 0.50290416041194897296687601889316283167302786730988e0 * t450 * t10 * t605 * t208 * t243 - 0.12069699849886775351205024453435907960152668815438e2 * t206 * t951 * t208
  t1336 = t101 ** 2
  t1342 = t112 ** 2
  t1356 = (0.70e2 / 0.81e2 * t9 * t639 + 0.220e3 / 0.81e2 * t20 * t636) * t40 - 0.4e1 * t63 * t75 * t90 + 0.12e2 * t73 * t99 * t101 - 0.6e1 * t76 * t112 - 0.24e2 * t97 * t116 * t118 + 0.24e2 * t100 * t122 - 0.4e1 * t104 * t134 + 0.24e2 * t28 / t115 / t39 * t1336 - 0.36e2 * t117 * t101 * t112 + 0.6e1 * t121 * t1342 + 0.8e1 * t121 * t90 * t134 - t125 * (0.70e2 / 0.81e2 * t29 * t639 + 0.220e3 / 0.81e2 * t32 * t636 + 0.18000000000000000000000000000000000000000000000000e6 * t35 * t605)
  t1361 = 0.1e1 / t557 / t539
  t1363 = t534 * t226
  t1367 = t569 * t1361
  t1368 = t545 * t226
  t1372 = t534 * t243
  t1376 = -0.19441031218901976532597921525897358463476063416234e0 * t901 * t644 * t902 + 0.17168305804406539632931583920177366868160429449148e2 * t909 * t644 * t910 - 0.37129640917784654580181051383469886637668330434323e3 * t916 * t644 * t917 + 0.6e1 * t921 * t164 * t144 * t774 - 0.28e2 / 0.3e1 * t148 * t145 + 0.14560e5 / 0.81e2 * s0 / t2 / t130 / t1 * t165 + 0.140e3 / 0.3e1 * t170 * t157 + 0.10126265704850360340049377650037241810273181027543e3 * t914 * t10 * t605 * t869 * t243 + 0.53020994233369026907085240525174613991298354771548e-1 * t899 * t10 * t605 * t513 * t243 - 0.46822652193836017180722501600483727822255716679496e1 * t907 * t10 * t605 * t787 * t243 - 0.12725038616008566457700457726041907357911605145172e1 * t510 * t951 * t513 + 0.4e1 * t955 * t145 + 0.31090700000000000000000000000000000000000000000001e-1 * t982 * t983 - t179 * (t1070 + t1202 + t1255 + t1304) * t504 / 0.24e2 - 0.3640e4 / 0.27e2 * t163 * t175 + t5 * t51 * t1356 * t144 + 0.48451138557721871068801971605281074525246742497255e-3 * t752 * t1361 * t1363 * t224 + 0.96902277115443742137603943210562149050493484994510e-3 * t1367 * t1368 * t224 + 0.32300759038481247379201314403520716350164494998170e-3 * t1367 * t1372 * t361
  t1378 = t577 * t1361
  t1409 = t1378 * t1363
  t1412 = t1367 * t1363
  t1415 = t1378 * t1368
  t1418 = t1378 * t1372
  t1433 = t759 ** 2
  t1450 = t155 ** 2
  t1475 = -0.24e2 * t7 / t803 / t42 * t520 * t1433 - 0.28e2 * t805 * t763 * t806 + 0.36e2 * t805 * t520 * t759 * t155 - 0.91e2 / 0.3e1 * t758 * t817 * t759 + 0.28e2 * t758 * t763 * t813 - 0.6e1 * t758 * t520 * t1450 - 0.8e1 * t758 * t520 * t173 * t136 - 0.1729e4 / 0.54e2 * t519 * t44 * t827 * t173 + 0.91e2 / 0.6e1 * t519 * t817 * t155 - 0.14e2 / 0.3e1 * t519 * t763 * t136 + t519 * t520 * t1356 - 0.43225e5 / 0.1296e4 * t7 * t45 / t46 / t160
  t1480 = t148 * t528
  t1495 = (-t180 * t212 * t535 / 0.12e2 - t220 * t976 * t545 / 0.4e1) * t19 * t236
  t1499 = 0.48451138557721871068801971605281074525246742497255e-3 * t1378 * t567 * t226 * t224 + 0.32300759038481247379201314403520716350164494998170e-3 * t1378 * t545 * t243 * t361 + 0.67293247996835932040002738340668159062842697912856e-5 * t794 * t534 * t8 * t1231 + 0.44184161861140855755904367104312178326081962309624e-2 * t900 * t850 * t1242 * t902 - 0.39018876828196680983935418000403106518546430566246e0 * t908 * t850 * t1242 * t910 + 0.84385547540419669500411480416977015085609841896189e1 * t915 * t850 * t1242 * t917 + 0.13255248558342256726771310131293653497824588692887e0 * t509 * t628 * t1263 * t513 * t8 * t14 + 0.50245625170970829256535377961032225433589214441597e-3 * t1409 * t304 - 0.64601518076962494758402628807041432700328989996340e-3 * t1412 * t240 - 0.64601518076962494758402628807041432700328989996340e-3 * t1415 * t240 - 0.43067678717974996505601752538027621800219326664227e-3 * t1418 * t405 + 0.53834598397468745632002190672534527250274158330283e-4 * t577 / t792 / t539 * t534 * t19 * t1252 - 0.28e2 * t798 * t175 + t5 * t1475 * t165 + 0.4e1 * t832 * t175 - 0.28e2 * t1480 * t157 + 0.6e1 * t921 * t157 + 0.6e1 * t775 * t157 - 0.69090444444444444444444444444444444444444444444446e-2 * t1495 * t439 * t545
  t1509 = t892 * t11
  t1525 = (t537 / 0.9e1 + t220 * t964 * t545 / 0.6e1 + t220 * t972 * t561 / 0.2e1 - t220 * t976 * t567 / 0.4e1) * t19 * t236
  t1526 = t439 * t534
  t1529 = t784 * t11
  t1533 = t170 * t528
  t1536 = t774 ** 2
  t1570 = 0.70e2 / 0.81e2 * t611 + 0.28e2 / 0.27e2 * t595 + 0.4e1 / 0.3e1 * t603 - 0.2e1 / 0.3e1 * t599 + 0.2e1 * t220 * t78 * t659 * t662 - 0.2e1 * t220 * t960 * t748 + t220 * t964 * t582 / 0.3e1 + 0.6e1 * t220 * t15 * t618 * t620 - 0.9e1 * t220 * t968 * t705 + 0.3e1 / 0.2e1 * t220 * t972 * t613 + 0.2e1 * t220 * t972 * t708 - t220 * t976 * t642 / 0.4e1
  t1573 = t238 * t534
  t1576 = t201 * t534
  t1579 = t529 * t528
  t1583 = t529 ** 2
  t1595 = t148 * t529
  t1601 = t5 * t1579
  t1604 = t238 * t567
  t1607 = t201 * t545
  t1610 = 0.10363566666666666666666666666666666666666666666667e-1 * t1495 * t238 * t582 - 0.28e2 / 0.3e1 * t148 * t831 * t165 + 0.38383580246913580246913580246913580246913580246915e-2 * t1495 * t360 * t534 + 0.20435174860777645787105769785744382475812907568201e0 * t1509 * t609 * t513 - 0.69090444444444444444444444444444444444444444444446e-2 * t1525 * t1526 - 0.77340987998746992664586274965084728992118817729523e1 * t1529 * t609 * t787 + 0.280e3 / 0.3e1 * t1533 * t175 + 0.3e1 * t5 * t1536 * t165 + 0.10363566666666666666666666666666666666666666666667e-1 * t1570 * t19 * t236 * t1573 + 0.10363566666666666666666666666666666666666666666667e-1 * t982 * t1576 - 0.28e2 / 0.3e1 * t148 * t1579 * t165 + t5 * t1583 * t165 + 0.64601518076962494758402628807041432700328989996342e-3 * t1378 * t534 * t307 - 0.3640e4 / 0.27e2 * t163 * t528 * t165 + 0.140e3 / 0.3e1 * t170 * t774 * t165 - 0.28e2 * t1595 * t175 + 0.10363566666666666666666666666666666666666666666667e-1 * t1495 * t201 * t567 + 0.4e1 * t1601 * t175 + 0.31090700000000000000000000000000000000000000000001e-1 * t1525 * t1604 + 0.20727133333333333333333333333333333333333333333334e-1 * t1525 * t1607
  t1642 = 0.4e1 * t5 * t145 - 0.28e2 * t148 * t157 - 0.3640e4 / 0.27e2 * t163 * t165 + 0.280e3 / 0.3e1 * t170 * t175 - t179 * (t424 + t491) * t504 / 0.6e1 + 0.63625193080042832288502288630209536789558025725859e0 * t510 * t207 * t513 + r0 * (t898 + t1376 + t1499 + t1610) + 0.38760910846177496855041577284224859620197393997804e-2 * t753 * t534 + 0.77521821692354993710083154568449719240394787995608e-2 * t571 * t545 + 0.38760910846177496855041577284224859620197393997804e-2 * t578 * t567 - 0.56e2 * t1480 * t175 - 0.28e2 * t798 * t165 + 0.280e3 / 0.3e1 * t1533 * t165 + 0.12e2 * t921 * t175 + 0.41454266666666666666666666666666666666666666666668e-1 * t982 * t1573 + 0.73578453447456598426849645372188715149258983353495e1 * t1529 * t191 * t787 + 0.27636177777777777777777777777777777777777777777779e-1 * t1495 * t1607 + 0.27636177777777777777777777777777777777777777777779e-1 * t1525 * t1576 - 0.92120592592592592592592592592592592592592592592596e-2 * t1495 * t1526 - 0.19441031218901976532597921525897358463476063416235e0 * t1509 * t191 * t513
  t1692 = 0.41454266666666666666666666666666666666666666666668e-1 * t1495 * t1604 + 0.82908533333333333333333333333333333333333333333336e-1 * t1525 * t983 + 0.20252531409700720680098755300074483620546362055085e3 * t916 * t404 * t917 + 0.16150379519240623689600657201760358175082247499085e-3 * t795 * t240 + 0.12e2 * t775 * t800 - 0.42416795386695221525668192420139691193038683817240e0 * t836 * t22 * t59 * t513 + 0.49486261284477758446612891156829639725211797786780e0 * t842 * t14 * t54 * t513 + 0.10604198846673805381417048105034922798259670954310e0 * t901 * t404 * t902 - 0.93645304387672034361445003200967455644511433358993e1 * t909 * t404 * t910 + 0.88368323722281711511808734208624356652163924619249e-2 * t893 * t191 * t894 - 0.33444751567025726557658929714631234158754083342496e0 * t785 * t191 * t788 + 0.12920303615392498951680525761408286540065797999268e-2 * t1412 * t224 + 0.12920303615392498951680525761408286540065797999268e-2 * t1415 * t224 + 0.43067678717974996505601752538027621800219326664227e-3 * t1418 * t361 - 0.86135357435949993011203505076055243600438653328453e-3 * t1409 * t240 + 0.12e2 * t775 * t175 + 0.12e2 * t955 * t157 + 0.4e1 * t1601 * t165 - 0.28e2 * t1595 * t165 + 0.4e1 * t832 * t165
  v4rho4_0_ = t1642 + t1692

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 + r1
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = 0.1e1 / jnp.pi
  t4 = t3 ** (0.1e1 / 0.3e1)
  t5 = t2 * t4
  t6 = 4 ** (0.1e1 / 0.3e1)
  t7 = t6 ** 2
  t8 = t1 ** (0.1e1 / 0.3e1)
  t10 = 0.1e1 / t8 / t1
  t11 = t7 * t10
  t12 = 0.1e1 / t8
  t13 = t7 * t12
  t14 = t5 * t13
  t15 = t14 / 0.4e1
  t16 = jnp.sqrt(t14)
  t18 = t15 + 0.35302100000000000000000000000000000000000000000000e1 * t16 + 0.180578e2
  t19 = 0.1e1 / t18
  t23 = t5 * t7
  t24 = t18 ** 2
  t25 = 0.1e1 / t24
  t26 = t12 * t25
  t27 = t5 * t11
  t28 = t27 / 0.12e2
  t29 = 0.1e1 / t16
  t30 = t29 * t2
  t31 = t4 * t7
  t32 = t31 * t10
  t33 = t30 * t32
  t35 = -t28 - 0.58836833333333333333333333333333333333333333333333e0 * t33
  t40 = t2 ** 2
  t42 = 0.1e1 / t4
  t43 = (-t5 * t11 * t19 / 0.12e2 - t23 * t26 * t35 / 0.4e1) * t40 * t42
  t44 = t6 * t8
  t45 = t44 * t18
  t48 = t16 + 0.706042e1
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t52 = t50 * t29 * t2
  t54 = 0.1e1 + 0.22381669423600000000000000000000000000000000000000e2 * t50
  t55 = 0.1e1 / t54
  t60 = t16 / 0.2e1
  t61 = t60 + 0.32500e0
  t62 = t61 * t19
  t63 = t62 * t29
  t66 = t61 ** 2
  t67 = t66 * t25
  t69 = -t63 * t27 / 0.6e1 - t67 * t35
  t70 = 0.1e1 / t66
  t71 = t69 * t70
  t75 = t15 + 0.18637200000000000000000000000000000000000000000000e1 * t16 + 0.129352e2
  t76 = 0.1e1 / t75
  t80 = t75 ** 2
  t81 = 0.1e1 / t80
  t82 = t12 * t81
  t84 = -t28 - 0.31062000000000000000000000000000000000000000000000e0 * t33
  t90 = (-t5 * t11 * t76 / 0.12e2 - t23 * t82 * t84 / 0.4e1) * t40 * t42
  t91 = t44 * t75
  t92 = t90 * t91
  t94 = t16 + 0.372744e1
  t95 = t94 ** 2
  t96 = 0.1e1 / t95
  t98 = t96 * t29 * t2
  t100 = 0.1e1 + 0.37846991046400000000000000000000000000000000000000e2 * t96
  t101 = 0.1e1 / t100
  t104 = t98 * t31 * t10 * t101
  t106 = t60 + 0.10498e0
  t107 = t106 * t76
  t108 = t107 * t29
  t111 = t106 ** 2
  t112 = t111 * t81
  t114 = -t108 * t27 / 0.6e1 - t112 * t84
  t115 = 0.1e1 / t111
  t116 = t114 * t115
  t117 = t116 * t75
  t119 = 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t45 + 0.41388824077869423260215065147117773567486474051458e-1 * t52 * t31 * t10 * t55 + 0.22478670955426118383265363956423012380560746650571e-2 * t71 * t18 - 0.10363566666666666666666666666666666666666666666667e-1 * t92 - 0.39765745675026770180313930393880960493473766078662e-1 * t104 - 0.96902277115443742137603943210562149050493484994510e-3 * t117
  t120 = r0 - r1
  t121 = 0.1e1 / t1
  t122 = t120 * t121
  t123 = 0.1e1 + t122
  t124 = t123 <= f.p.zeta_threshold
  t125 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t126 = t125 * f.p.zeta_threshold
  t127 = t123 ** (0.1e1 / 0.3e1)
  t129 = f.my_piecewise3(t124, t126, t127 * t123)
  t130 = 0.1e1 - t122
  t131 = t130 <= f.p.zeta_threshold
  t132 = t130 ** (0.1e1 / 0.3e1)
  t134 = f.my_piecewise3(t131, t126, t132 * t130)
  t135 = t129 + t134 - 0.2e1
  t136 = t119 * t135
  t137 = 2 ** (0.1e1 / 0.3e1)
  t138 = t137 - 0.1e1
  t140 = 0.1e1 / t138 / 0.2e1
  t141 = t120 ** 2
  t142 = t141 ** 2
  t143 = t140 * t142
  t144 = t1 ** 2
  t145 = t144 ** 2
  t147 = 0.1e1 / t145 / t1
  t148 = t143 * t147
  t150 = 0.8e1 * t136 * t148
  t154 = jnp.log(t5 * t13 * t19 / 0.4e1)
  t158 = jnp.arctan(0.47309269095601128299619512910246923284397083311420e1 / t48)
  t161 = jnp.log(t66 * t19)
  t166 = jnp.log(t5 * t13 * t76 / 0.4e1)
  t170 = jnp.arctan(0.61519908197590802321728722658814145360143502774884e1 / t94)
  t173 = jnp.log(t111 * t76)
  t175 = 0.1554535e-1 * t154 + 0.52491393169780936217021346072241076933841385384497e-1 * t158 + 0.22478670955426118383265363956423012380560746650571e-2 * t161 - 0.310907e-1 * t166 - 0.38783294878113014394824731224995739188004877421366e-1 * t170 - 0.96902277115443742137603943210562149050493484994510e-3 * t173
  t176 = t127 ** 2
  t177 = 0.1e1 / t176
  t178 = 0.1e1 / t144
  t179 = t120 * t178
  t180 = t121 - t179
  t181 = t180 ** 2
  t184 = t144 * t1
  t185 = 0.1e1 / t184
  t186 = t120 * t185
  t188 = -0.2e1 * t178 + 0.2e1 * t186
  t192 = f.my_piecewise3(t124, 0, 0.4e1 / 0.9e1 * t177 * t181 + 0.4e1 / 0.3e1 * t127 * t188)
  t193 = t132 ** 2
  t194 = 0.1e1 / t193
  t195 = -t180
  t196 = t195 ** 2
  t199 = -t188
  t203 = f.my_piecewise3(t131, 0, 0.4e1 / 0.9e1 * t194 * t196 + 0.4e1 / 0.3e1 * t132 * t199)
  t204 = t192 + t203
  t206 = 0.1e1 / t145
  t207 = t143 * t206
  t211 = f.my_piecewise3(t124, 0, 0.4e1 / 0.3e1 * t127 * t180)
  t214 = f.my_piecewise3(t131, 0, 0.4e1 / 0.3e1 * t132 * t195)
  t215 = t211 + t214
  t217 = t119 * t215 * t207
  t220 = 0.1e1 / t8 / t144
  t221 = t7 * t220
  t223 = t5 * t221 * t19
  t230 = 0.1e1 / t24 / t18
  t232 = t35 ** 2
  t236 = t5 * t221
  t237 = t236 / 0.9e1
  t239 = 0.1e1 / t16 / t14
  t241 = t4 ** 2
  t242 = t241 * t6
  t243 = t8 ** 2
  t245 = 0.1e1 / t243 / t144
  t246 = t242 * t245
  t247 = t239 * t40 * t246
  t249 = t31 * t220
  t250 = t30 * t249
  t252 = t237 - 0.39224555555555555555555555555555555555555555555555e0 * t247 + 0.78449111111111111111111111111111111111111111111110e0 * t250
  t261 = 0.1e1 / t243
  t262 = t6 * t261
  t286 = t49 ** 2
  t291 = t54 ** 2
  t306 = t40 * t241 * t6 * t245
  t329 = t5 * t221 * t76
  t336 = 0.1e1 / t80 / t75
  t338 = t84 ** 2
  t344 = t237 - 0.20708000000000000000000000000000000000000000000000e0 * t247 + 0.41416000000000000000000000000000000000000000000000e0 * t250
  t352 = 0.10363566666666666666666666666666666666666666666667e-1 * (t329 / 0.9e1 + t23 * t10 * t81 * t84 / 0.6e1 + t23 * t12 * t336 * t338 / 0.2e1 - t23 * t82 * t344 / 0.4e1) * t40 * t42 * t91
  t355 = 0.34545222222222222222222222222222222222222222222223e-2 * t90 * t262 * t75
  t358 = 0.10363566666666666666666666666666666666666666666667e-1 * t90 * t44 * t84
  t365 = 0.13255248558342256726771310131293653497824588692887e-1 / t95 / t94 * t2 * t4 * t221 * t101
  t371 = 0.26510497116684513453542620262587306995649177385775e-1 * t96 * t239 * t40 * t242 * t245 * t101
  t375 = 0.53020994233369026907085240525174613991298354771549e-1 * t98 * t31 * t220 * t101
  t376 = t95 ** 2
  t381 = t100 ** 2
  t385 = 0.50167127350538589836488394571946851238131125013746e0 / t376 / t94 * t2 * t4 * t221 / t381
  t405 = 0.96902277115443742137603943210562149050493484994510e-3 * (t329 / 0.72e2 + t106 * t81 * t30 * t31 * t10 * t84 / 0.3e1 - t107 * t239 * t306 / 0.9e1 + 0.2e1 / 0.9e1 * t108 * t236 + 0.2e1 * t111 * t336 * t338 - t112 * t344) * t115 * t75
  t412 = 0.16150379519240623689600657201760358175082247499085e-3 * t114 / t111 / t106 * t75 * t29 * t27
  t414 = 0.96902277115443742137603943210562149050493484994510e-3 * t116 * t84
  t415 = 0.51817833333333333333333333333333333333333333333333e-2 * (t223 / 0.9e1 + t23 * t10 * t25 * t35 / 0.6e1 + t23 * t12 * t230 * t232 / 0.2e1 - t23 * t26 * t252 / 0.4e1) * t40 * t42 * t45 + 0.17272611111111111111111111111111111111111111111111e-2 * t43 * t262 * t18 + 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t44 * t35 + 0.13796274692623141086738355049039257855828824683819e-1 / t49 / t48 * t2 * t4 * t221 * t55 + 0.27592549385246282173476710098078515711657649367639e-1 * t50 * t239 * t40 * t242 * t245 * t55 - 0.55185098770492564346953420196157031423315298735277e-1 * t52 * t31 * t220 * t55 - 0.30878365944746984533884071665444263610784010246137e0 / t286 / t48 * t2 * t4 * t221 / t291 + 0.22478670955426118383265363956423012380560746650571e-2 * (t223 / 0.72e2 + t61 * t25 * t30 * t31 * t10 * t35 / 0.3e1 - t62 * t239 * t306 / 0.9e1 + 0.2e1 / 0.9e1 * t63 * t236 + 0.2e1 * t66 * t230 * t232 - t67 * t252) * t70 * t18 + 0.37464451592376863972108939927371687300934577750952e-3 * t69 / t66 / t61 * t18 * t29 * t27 + 0.22478670955426118383265363956423012380560746650571e-2 * t71 * t35 - t352 - t355 - t358 - t365 - t371 + t375 + t385 - t405 - t412 - t414
  t417 = t415 * t135 * t207
  t419 = s0 + 0.2e1 * s1 + s2
  t420 = t419 * t220
  t422 = params.ftilde * (params.aa + params.bb)
  t423 = params.malpha * t2
  t424 = t31 * t12
  t427 = params.mbeta * t40
  t428 = t242 * t261
  t431 = params.bb + t423 * t424 / 0.4e1 + t427 * t428 / 0.4e1
  t432 = params.mgamma * t2
  t435 = params.mdelta * t40
  t438 = params.mbeta * t3
  t441 = 0.1e1 + t432 * t424 / 0.4e1 + t435 * t428 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t438 * t121
  t442 = 0.1e1 / t441
  t444 = t431 * t442 + params.aa
  t445 = t444 ** 2
  t447 = t422 / t445
  t448 = jnp.sqrt(t419)
  t449 = t1 ** (0.1e1 / 0.6e1)
  t451 = 0.1e1 / t449 / t1
  t452 = t448 * t451
  t457 = t242 / t243 / t1
  t460 = -t423 * t32 / 0.12e2 - t427 * t457 / 0.6e1
  t462 = t441 ** 2
  t463 = 0.1e1 / t462
  t464 = t431 * t463
  t471 = -t432 * t32 / 0.12e2 - t435 * t457 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t438 * t178
  t473 = t460 * t442 - t464 * t471
  t477 = 0.1e1 / t444 * t448
  t479 = 0.1e1 / t449 / t144
  t483 = t447 * t452 * t473 + 0.7e1 / 0.6e1 * t422 * t477 * t479
  t484 = t483 ** 2
  t488 = jnp.exp(-t422 * t477 * t451)
  t489 = t488 * t444
  t490 = t125 ** 2
  t491 = t490 * f.p.zeta_threshold
  t493 = f.my_piecewise3(t124, t491, t176 * t123)
  t495 = f.my_piecewise3(t131, t491, t193 * t130)
  t496 = t493 + t495
  t497 = jnp.sqrt(t496)
  t498 = 0.1e1 / t497
  t499 = jnp.sqrt(0.2e1)
  t500 = t498 * t499
  t501 = t489 * t500
  t502 = t420 * t484 * t501
  t503 = t420 * t488
  t504 = t496 ** 2
  t506 = 0.1e1 / t497 / t504
  t507 = t444 * t506
  t510 = f.my_piecewise3(t124, 0, 0.5e1 / 0.3e1 * t176 * t180)
  t513 = f.my_piecewise3(t131, 0, 0.5e1 / 0.3e1 * t193 * t195)
  t514 = t510 + t513
  t515 = t514 ** 2
  t521 = 0.1e1 / t497 / t496
  t522 = t473 * t521
  t523 = t499 * t514
  t525 = t503 * t522 * t523
  t526 = t444 * t521
  t527 = 0.1e1 / t127
  t533 = f.my_piecewise3(t124, 0, 0.10e2 / 0.9e1 * t527 * t181 + 0.5e1 / 0.3e1 * t176 * t188)
  t534 = 0.1e1 / t132
  t540 = f.my_piecewise3(t131, 0, 0.10e2 / 0.9e1 * t534 * t196 + 0.5e1 / 0.3e1 * t193 * t199)
  t546 = t420 * t483
  t550 = 0.2e1 * t546 * t488 * t473 * t500
  t553 = t419 / t8 / t184
  t554 = t553 * t488
  t555 = t526 * t523
  t556 = t554 * t555
  t560 = 0.14e2 / 0.3e1 * t553 * t483 * t501
  t564 = t473 ** 2
  t584 = t471 ** 2
  t595 = (t423 * t249 / 0.9e1 + 0.5e1 / 0.18e2 * t427 * t246) * t442 - 0.2e1 * t460 * t463 * t471 + 0.2e1 * t431 / t462 / t441 * t584 - t464 * (t432 * t249 / 0.9e1 + 0.5e1 / 0.18e2 * t435 * t246 + 0.15000000000000000000000000000000000000000000000000e5 * t438 * t185)
  t605 = t420 * (-0.2e1 * t422 / t445 / t444 * t452 * t564 - 0.7e1 / 0.3e1 * t447 * t448 * t479 * t473 + t447 * t452 * t595 - 0.91e2 / 0.36e2 * t422 * t477 / t449 / t184) * t501
  t606 = jnp.pi ** 2
  t607 = 0.1e1 / t606
  t609 = t15 + 0.56553500000000000000000000000000000000000000000000e0 * t16 + 0.130045e2
  t610 = 0.1e1 / t609
  t614 = t609 ** 2
  t615 = 0.1e1 / t614
  t616 = t12 * t615
  t618 = -t28 - 0.94255833333333333333333333333333333333333333333334e-1 * t33
  t624 = (-t5 * t11 * t610 / 0.12e2 - t23 * t616 * t618 / 0.4e1) * t40 * t42
  t625 = t44 * t609
  t628 = t16 + 0.113107e1
  t629 = t628 ** 2
  t630 = 0.1e1 / t629
  t632 = t630 * t29 * t2
  t634 = 0.1e1 + 0.50738680655100000000000000000000000000000000000000e2 * t630
  t635 = 0.1e1 / t634
  t640 = t60 + 0.47584e-2
  t641 = t640 * t610
  t642 = t641 * t29
  t645 = t640 ** 2
  t646 = t645 * t615
  t648 = -t642 * t27 / 0.6e1 - t646 * t618
  t649 = 0.1e1 / t645
  t650 = t648 * t649
  t654 = t607 * (t624 * t625 / 0.3e1 + 0.37717812030896172972515701416987212375477090048242e0 * t632 * t31 * t10 * t635 + 0.41403379428206274608377249480129098139321562919141e-3 * t650 * t609)
  t655 = t654 * t135
  t656 = t141 * t120
  t657 = t656 * t206
  t658 = t142 * t147
  t662 = 0.9e1 * t138
  t663 = t140 * (-0.4e1 * t657 + 0.4e1 * t658) * t662
  t664 = t655 * t663
  t671 = t444 * t498 * t499
  t673 = 0.70e2 / 0.9e1 * t419 / t8 / t145 * t488 * t671
  t677 = jnp.log(t5 * t13 * t610 / 0.4e1)
  t680 = jnp.arctan(0.71231089178181179907634622339714221951452652573438e1 / t628)
  t683 = jnp.log(t645 * t610)
  t686 = t607 * (t677 + 0.31770800474394146398819696256107927053514547209957e0 * t680 + 0.41403379428206274608377249480129098139321562919141e-3 * t683)
  t691 = t140 * (-t142 * t206 + 0.1e1) * t662
  t694 = t686 * t215
  t698 = t5 * t221 * t610
  t705 = 0.1e1 / t614 / t609
  t707 = t618 ** 2
  t713 = t237 - 0.62837222222222222222222222222222222222222222222223e-1 * t247 + 0.12567444444444444444444444444444444444444444444445e0 * t250
  t745 = t629 ** 2
  t750 = t634 ** 2
  t788 = t607 * ((t698 / 0.9e1 + t23 * t10 * t615 * t618 / 0.6e1 + t23 * t12 * t705 * t707 / 0.2e1 - t23 * t616 * t713 / 0.4e1) * t40 * t42 * t625 / 0.3e1 + t624 * t262 * t609 / 0.9e1 + t624 * t44 * t618 / 0.3e1 + 0.12572604010298724324171900472329070791825696682747e0 / t629 / t628 * t2 * t4 * t221 * t635 + 0.25145208020597448648343800944658141583651393365495e0 * t630 * t239 * t40 * t242 * t245 * t635 - 0.50290416041194897296687601889316283167302786730989e0 * t632 * t31 * t220 * t635 - 0.63791733988157656503906862782236557702656491548799e1 / t745 / t628 * t2 * t4 * t221 / t750 + 0.41403379428206274608377249480129098139321562919141e-3 * (t698 / 0.72e2 + t640 * t615 * t30 * t31 * t10 * t618 / 0.3e1 - t641 * t239 * t306 / 0.9e1 + 0.2e1 / 0.9e1 * t642 * t236 + 0.2e1 * t645 * t705 * t707 - t646 * t713) * t649 * t609 + 0.69005632380343791013962082466881830232202604865235e-4 * t648 / t645 / t640 * t609 * t29 * t27 + 0.41403379428206274608377249480129098139321562919141e-3 * t650 * t618) * t135 * t691 / 0.24e2
  t789 = -t150 + t175 * t204 * t207 + 0.2e1 * t217 + t417 + t502 + 0.3e1 / 0.4e1 * t503 * t507 * t499 * t515 - t525 - t503 * t526 * t499 * (t533 + t540) / 0.2e1 + t550 + 0.7e1 / 0.3e1 * t556 - t560 + t605 + t371 - t375 - t664 / 0.12e2 + t673 - t686 * t204 * t691 / 0.24e2 - t694 * t663 / 0.12e2 - t788
  t791 = t654 * t215 * t691
  t794 = t473 * t498 * t499
  t796 = 0.14e2 / 0.3e1 * t554 * t794
  t797 = t686 * t135
  t799 = 0.12e2 * t141 * t206
  t801 = 0.32e2 * t656 * t147
  t803 = 0.1e1 / t145 / t144
  t805 = 0.20e2 * t142 * t803
  t813 = t503 * t595 * t498 * t499
  t814 = t175 * t135
  t817 = 0.20e2 * t814 * t143 * t803
  t821 = 0.12e2 * t814 * t140 * t141 * t206
  t822 = t140 * t656
  t825 = 0.32e2 * t814 * t822 * t147
  t826 = t175 * t215
  t827 = t822 * t206
  t828 = t826 * t827
  t830 = t826 * t148
  t833 = 0.8e1 * t136 * t827
  t835 = t420 * t483 * t488
  t836 = t835 * t555
  t837 = -t791 / 0.12e2 - t796 - t797 * t140 * (-t799 + t801 - t805) * t662 / 0.24e2 + t813 + t817 + t821 - t825 + 0.8e1 * t828 - 0.8e1 * t830 + t833 + t405 + t414 + t352 + t355 + t358 + t365 - t385 + t412 - t836
  t841 = 0.2e1 * t136 * t207
  t842 = t826 * t207
  t845 = 0.8e1 * t814 * t827
  t847 = 0.8e1 * t814 * t148
  t849 = 0.2e1 * t546 * t501
  t850 = t503 * t555
  t851 = 0.79531491350053540360627860787761920986947532157324e-1 * t104
  t852 = 0.20727133333333333333333333333333333333333333333334e-1 * t92
  t854 = t655 * t691 / 0.12e2
  t855 = t694 * t691
  t857 = t797 * t663
  t860 = 0.14e2 / 0.3e1 * t554 * t671
  t862 = 0.2e1 * t503 * t794
  t863 = 0.19380455423088748427520788642112429810098696998902e-2 * t117
  d11 = t1 * (t789 + t837) + t841 + 0.2e1 * t842 + t845 - t847 + t849 - t850 + t851 + t852 - t854 - t855 / 0.12e2 - t857 / 0.12e2 - t860 + t862 + t863
  t867 = t140 * (0.4e1 * t657 + 0.4e1 * t658) * t662
  t875 = -t121 - t179
  t878 = f.my_piecewise3(t124, 0, 0.4e1 / 0.3e1 * t127 * t875)
  t879 = -t875
  t882 = f.my_piecewise3(t131, 0, 0.4e1 / 0.3e1 * t132 * t879)
  t883 = t878 + t882
  t885 = t654 * t883 * t691
  t894 = f.my_piecewise3(t124, 0, 0.4e1 / 0.9e1 * t177 * t875 * t180 + 0.8e1 / 0.3e1 * t127 * t120 * t185)
  t902 = f.my_piecewise3(t131, 0, 0.4e1 / 0.9e1 * t194 * t879 * t195 - 0.8e1 / 0.3e1 * t132 * t120 * t185)
  t903 = t894 + t902
  t907 = t686 * t883
  t910 = t655 * t867
  t914 = f.my_piecewise3(t124, 0, 0.5e1 / 0.3e1 * t176 * t875)
  t917 = f.my_piecewise3(t131, 0, 0.5e1 / 0.3e1 * t193 * t879)
  t918 = t914 + t917
  t919 = t499 * t918
  t921 = t503 * t522 * t919
  t930 = f.my_piecewise3(t124, 0, 0.10e2 / 0.9e1 * t527 * t875 * t180 + 0.10e2 / 0.3e1 * t176 * t120 * t185)
  t938 = f.my_piecewise3(t131, 0, 0.10e2 / 0.9e1 * t534 * t879 * t195 - 0.10e2 / 0.3e1 * t193 * t120 * t185)
  t944 = -t694 * t867 / 0.24e2 - t797 * t140 * (t799 - t805) * t662 / 0.24e2 - t885 / 0.24e2 - t686 * t903 * t691 / 0.24e2 - t907 * t663 / 0.24e2 - t910 / 0.24e2 - t150 + t217 + t417 - t921 / 0.2e1 - t503 * t526 * t499 * (t930 + t938) / 0.2e1
  t945 = t526 * t919
  t946 = t554 * t945
  t951 = 0.7e1 / 0.6e1 * t946 + t502 - t525 / 0.2e1 + t550 + 0.7e1 / 0.6e1 * t556 - t560 + t605 + t371 - t375 - t664 / 0.24e2 + t673
  t957 = t119 * t883 * t207
  t958 = t175 * t883
  t959 = t958 * t827
  t961 = t958 * t148
  t964 = -t788 - t791 / 0.24e2 - t796 + t813 + t175 * t903 * t207 + t957 + 0.4e1 * t959 - 0.4e1 * t961 + t817 - t821 - 0.4e1 * t828
  t973 = t835 * t945
  t975 = -0.4e1 * t830 + t405 + t414 + t352 + t355 + t358 + t365 - t385 + t412 - t836 / 0.2e1 + 0.3e1 / 0.4e1 * t420 * t489 * t506 * t499 * t918 * t514 - t973 / 0.2e1
  t979 = t958 * t207
  t981 = t503 * t945
  t985 = t907 * t691
  t987 = t797 * t867
  d12 = t1 * (t944 + t951 + t964 + t975) + t863 + t842 - t847 + t841 + t979 - t850 / 0.2e1 + t849 - t981 / 0.2e1 + t851 - t855 / 0.24e2 - t857 / 0.24e2 + t862 - t860 + t852 - t854 - t985 / 0.24e2 - t987 / 0.24e2
  t994 = t875 ** 2
  t998 = 0.2e1 * t178 + 0.2e1 * t186
  t1002 = f.my_piecewise3(t124, 0, 0.4e1 / 0.9e1 * t177 * t994 + 0.4e1 / 0.3e1 * t127 * t998)
  t1003 = t879 ** 2
  t1006 = -t998
  t1010 = f.my_piecewise3(t131, 0, 0.4e1 / 0.9e1 * t194 * t1003 + 0.4e1 / 0.3e1 * t132 * t1006)
  t1011 = t1002 + t1010
  t1015 = t918 ** 2
  t1025 = f.my_piecewise3(t124, 0, 0.10e2 / 0.9e1 * t527 * t994 + 0.5e1 / 0.3e1 * t176 * t998)
  t1031 = f.my_piecewise3(t131, 0, 0.10e2 / 0.9e1 * t534 * t1003 + 0.5e1 / 0.3e1 * t193 * t1006)
  t1037 = -t885 / 0.12e2 - t910 / 0.12e2 - t150 + t417 + t175 * t1011 * t207 - t921 + 0.7e1 / 0.3e1 * t946 + 0.3e1 / 0.4e1 * t503 * t507 * t499 * t1015 - t503 * t526 * t499 * (t1025 + t1031) / 0.2e1 + t502 + t550 - t560 + t605 + t371 - t375 + t673 - t788 - t796 + t813
  t1051 = 0.2e1 * t957 - 0.8e1 * t959 - 0.8e1 * t961 + t817 + t821 + t825 - t833 - t797 * t140 * (-t799 - t801 - t805) * t662 / 0.24e2 - t686 * t1011 * t691 / 0.24e2 - t907 * t867 / 0.12e2 + t405 + t414 + t352 + t355 + t358 + t365 - t385 + t412 - t973
  d22 = t862 - t860 + t863 + t841 + 0.2e1 * t979 - t845 - t847 + t849 - t981 + t851 - t854 - t985 / 0.12e2 - t987 / 0.12e2 + t852 + t1 * (t1037 + t1051)
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

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t10 = 0.1e1 / t8 / t7
  t11 = t6 * t10
  t12 = 0.1e1 / t8
  t13 = t6 * t12
  t14 = t4 * t13
  t15 = t14 / 0.4e1
  t16 = jnp.sqrt(t14)
  t18 = t15 + 0.35302100000000000000000000000000000000000000000000e1 * t16 + 0.180578e2
  t19 = 0.1e1 / t18
  t23 = t4 * t6
  t24 = t18 ** 2
  t25 = 0.1e1 / t24
  t26 = t12 * t25
  t27 = t4 * t11
  t28 = t27 / 0.12e2
  t29 = 0.1e1 / t16
  t30 = t29 * t1
  t31 = t3 * t6
  t32 = t31 * t10
  t33 = t30 * t32
  t35 = -t28 - 0.58836833333333333333333333333333333333333333333333e0 * t33
  t40 = t1 ** 2
  t42 = 0.1e1 / t3
  t43 = (-t4 * t11 * t19 / 0.12e2 - t23 * t26 * t35 / 0.4e1) * t40 * t42
  t44 = t5 * t8
  t45 = t44 * t18
  t48 = t16 + 0.706042e1
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t52 = t50 * t29 * t1
  t54 = 0.1e1 + 0.22381669423600000000000000000000000000000000000000e2 * t50
  t55 = 0.1e1 / t54
  t60 = t16 / 0.2e1
  t61 = t60 + 0.32500e0
  t62 = t61 * t19
  t63 = t62 * t29
  t66 = t61 ** 2
  t67 = t66 * t25
  t69 = -t63 * t27 / 0.6e1 - t67 * t35
  t70 = 0.1e1 / t66
  t71 = t69 * t70
  t75 = t15 + 0.18637200000000000000000000000000000000000000000000e1 * t16 + 0.129352e2
  t76 = 0.1e1 / t75
  t80 = t75 ** 2
  t81 = 0.1e1 / t80
  t82 = t12 * t81
  t84 = -t28 - 0.31062000000000000000000000000000000000000000000000e0 * t33
  t90 = (-t4 * t11 * t76 / 0.12e2 - t23 * t82 * t84 / 0.4e1) * t40 * t42
  t91 = t44 * t75
  t94 = t16 + 0.372744e1
  t95 = t94 ** 2
  t96 = 0.1e1 / t95
  t98 = t96 * t29 * t1
  t100 = 0.1e1 + 0.37846991046400000000000000000000000000000000000000e2 * t96
  t101 = 0.1e1 / t100
  t106 = t60 + 0.10498e0
  t107 = t106 * t76
  t108 = t107 * t29
  t111 = t106 ** 2
  t112 = t111 * t81
  t114 = -t108 * t27 / 0.6e1 - t112 * t84
  t115 = 0.1e1 / t111
  t116 = t114 * t115
  t119 = 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t45 + 0.41388824077869423260215065147117773567486474051458e-1 * t52 * t31 * t10 * t55 + 0.22478670955426118383265363956423012380560746650571e-2 * t71 * t18 - 0.10363566666666666666666666666666666666666666666667e-1 * t90 * t91 - 0.39765745675026770180313930393880960493473766078662e-1 * t98 * t31 * t10 * t101 - 0.96902277115443742137603943210562149050493484994510e-3 * t116 * t75
  t120 = r0 - r1
  t121 = 0.1e1 / t7
  t122 = t120 * t121
  t123 = 0.1e1 + t122
  t124 = t123 <= f.p.zeta_threshold
  t125 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t126 = t125 * f.p.zeta_threshold
  t127 = t123 ** (0.1e1 / 0.3e1)
  t128 = t127 * t123
  t129 = f.my_piecewise3(t124, t126, t128)
  t130 = 0.1e1 - t122
  t131 = t130 <= f.p.zeta_threshold
  t132 = t130 ** (0.1e1 / 0.3e1)
  t133 = t132 * t130
  t134 = f.my_piecewise3(t131, t126, t133)
  t135 = t129 + t134 - 0.2e1
  t136 = t119 * t135
  t137 = 2 ** (0.1e1 / 0.3e1)
  t138 = t137 - 0.1e1
  t140 = 0.1e1 / t138 / 0.2e1
  t141 = t120 ** 2
  t142 = t141 ** 2
  t143 = t140 * t142
  t144 = t7 ** 2
  t145 = t144 ** 2
  t146 = t145 * t7
  t147 = 0.1e1 / t146
  t148 = t143 * t147
  t154 = jnp.log(t4 * t13 * t19 / 0.4e1)
  t158 = jnp.atan(0.47309269095601128299619512910246923284397083311420e1 / t48)
  t161 = jnp.log(t66 * t19)
  t166 = jnp.log(t4 * t13 * t76 / 0.4e1)
  t170 = jnp.atan(0.61519908197590802321728722658814145360143502774884e1 / t94)
  t173 = jnp.log(t111 * t76)
  t175 = 0.1554535e-1 * t154 + 0.52491393169780936217021346072241076933841385384497e-1 * t158 + 0.22478670955426118383265363956423012380560746650571e-2 * t161 - 0.310907e-1 * t166 - 0.38783294878113014394824731224995739188004877421366e-1 * t170 - 0.96902277115443742137603943210562149050493484994510e-3 * t173
  t176 = t127 ** 2
  t177 = 0.1e1 / t176
  t178 = 0.1e1 / t144
  t180 = -t120 * t178 + t121
  t181 = t180 ** 2
  t184 = t144 * t7
  t185 = 0.1e1 / t184
  t188 = 0.2e1 * t120 * t185 - 0.2e1 * t178
  t192 = f.my_piecewise3(t124, 0, 0.4e1 / 0.9e1 * t177 * t181 + 0.4e1 / 0.3e1 * t127 * t188)
  t193 = t132 ** 2
  t194 = 0.1e1 / t193
  t195 = -t180
  t196 = t195 ** 2
  t199 = -t188
  t203 = f.my_piecewise3(t131, 0, 0.4e1 / 0.9e1 * t194 * t196 + 0.4e1 / 0.3e1 * t132 * t199)
  t204 = t192 + t203
  t205 = t175 * t204
  t206 = 0.1e1 / t145
  t207 = t143 * t206
  t210 = t175 * t135
  t211 = t140 * t141
  t212 = t211 * t206
  t215 = t141 * t120
  t216 = t140 * t215
  t217 = t216 * t147
  t222 = f.my_piecewise3(t124, 0, 0.4e1 / 0.3e1 * t127 * t180)
  t225 = f.my_piecewise3(t131, 0, 0.4e1 / 0.3e1 * t132 * t195)
  t226 = t222 + t225
  t227 = t175 * t226
  t228 = t216 * t206
  t234 = 0.1e1 / t8 / t144
  t235 = t6 * t234
  t237 = t4 * t235 * t19
  t239 = t10 * t25
  t244 = 0.1e1 / t24 / t18
  t245 = t12 * t244
  t246 = t35 ** 2
  t250 = t4 * t235
  t251 = t250 / 0.9e1
  t253 = 0.1e1 / t16 / t14
  t254 = t253 * t40
  t255 = t3 ** 2
  t256 = t255 * t5
  t257 = t8 ** 2
  t259 = 0.1e1 / t257 / t144
  t260 = t256 * t259
  t261 = t254 * t260
  t263 = t31 * t234
  t264 = t30 * t263
  t266 = t251 - 0.39224555555555555555555555555555555555555555555555e0 * t261 + 0.78449111111111111111111111111111111111111111111110e0 * t264
  t272 = (t237 / 0.9e1 + t23 * t239 * t35 / 0.6e1 + t23 * t245 * t246 / 0.2e1 - t23 * t26 * t266 / 0.4e1) * t40 * t42
  t275 = 0.1e1 / t257
  t276 = t5 * t275
  t277 = t276 * t18
  t280 = t44 * t35
  t285 = 0.1e1 / t49 / t48 * t1
  t286 = t285 * t3
  t291 = t50 * t253 * t40
  t300 = t49 ** 2
  t303 = 0.1e1 / t300 / t48 * t1
  t304 = t303 * t3
  t305 = t54 ** 2
  t306 = 0.1e1 / t305
  t311 = t61 * t25
  t312 = t311 * t30
  t317 = t62 * t253
  t318 = t40 * t255
  t320 = t318 * t5 * t259
  t325 = t66 * t244
  t329 = t237 / 0.72e2 + t312 * t31 * t10 * t35 / 0.3e1 - t317 * t320 / 0.9e1 + 0.2e1 / 0.9e1 * t63 * t250 + 0.2e1 * t325 * t246 - t67 * t266
  t330 = t329 * t70
  t334 = 0.1e1 / t66 / t61
  t335 = t69 * t334
  t336 = t18 * t29
  t337 = t335 * t336
  t343 = t4 * t235 * t76
  t345 = t10 * t81
  t350 = 0.1e1 / t80 / t75
  t351 = t12 * t350
  t352 = t84 ** 2
  t358 = t251 - 0.20708000000000000000000000000000000000000000000000e0 * t261 + 0.41416000000000000000000000000000000000000000000000e0 * t264
  t364 = (t343 / 0.9e1 + t23 * t345 * t84 / 0.6e1 + t23 * t351 * t352 / 0.2e1 - t23 * t82 * t358 / 0.4e1) * t40 * t42
  t365 = t364 * t91
  t367 = t276 * t75
  t368 = t90 * t367
  t370 = t44 * t84
  t371 = t90 * t370
  t375 = 0.1e1 / t95 / t94 * t1
  t376 = t375 * t3
  t378 = t376 * t235 * t101
  t381 = t96 * t253 * t40
  t384 = t381 * t256 * t259 * t101
  t388 = t98 * t31 * t234 * t101
  t390 = t95 ** 2
  t393 = 0.1e1 / t390 / t94 * t1
  t394 = t393 * t3
  t395 = t100 ** 2
  t396 = 0.1e1 / t395
  t398 = t394 * t235 * t396
  t401 = t106 * t81
  t402 = t401 * t30
  t407 = t107 * t253
  t412 = t111 * t350
  t416 = t343 / 0.72e2 + t402 * t31 * t10 * t84 / 0.3e1 - t407 * t320 / 0.9e1 + 0.2e1 / 0.9e1 * t108 * t250 + 0.2e1 * t412 * t352 - t112 * t358
  t417 = t416 * t115
  t418 = t417 * t75
  t421 = 0.1e1 / t111 / t106
  t422 = t114 * t421
  t423 = t75 * t29
  t424 = t422 * t423
  t425 = t424 * t27
  t427 = t116 * t84
  t429 = 0.51817833333333333333333333333333333333333333333333e-2 * t272 * t45 + 0.17272611111111111111111111111111111111111111111111e-2 * t43 * t277 + 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t280 + 0.13796274692623141086738355049039257855828824683819e-1 * t286 * t235 * t55 + 0.27592549385246282173476710098078515711657649367639e-1 * t291 * t256 * t259 * t55 - 0.55185098770492564346953420196157031423315298735277e-1 * t52 * t31 * t234 * t55 - 0.30878365944746984533884071665444263610784010246137e0 * t304 * t235 * t306 + 0.22478670955426118383265363956423012380560746650571e-2 * t330 * t18 + 0.37464451592376863972108939927371687300934577750952e-3 * t337 * t27 + 0.22478670955426118383265363956423012380560746650571e-2 * t71 * t35 - 0.10363566666666666666666666666666666666666666666667e-1 * t365 - 0.34545222222222222222222222222222222222222222222223e-2 * t368 - 0.10363566666666666666666666666666666666666666666667e-1 * t371 - 0.13255248558342256726771310131293653497824588692887e-1 * t378 - 0.26510497116684513453542620262587306995649177385775e-1 * t384 + 0.53020994233369026907085240525174613991298354771549e-1 * t388 + 0.50167127350538589836488394571946851238131125013746e0 * t398 - 0.96902277115443742137603943210562149050493484994510e-3 * t418 - 0.16150379519240623689600657201760358175082247499085e-3 * t425 - 0.96902277115443742137603943210562149050493484994510e-3 * t427
  t430 = t429 * t135
  t434 = 0.1e1 / t145 / t144
  t435 = t143 * t434
  t438 = t119 * t226
  t447 = s0 + 0.2e1 * s1 + s2
  t448 = t447 * t234
  t450 = params.ftilde * (params.aa + params.bb)
  t451 = params.malpha * t1
  t452 = t31 * t12
  t455 = params.mbeta * t40
  t456 = t256 * t275
  t459 = params.bb + t451 * t452 / 0.4e1 + t455 * t456 / 0.4e1
  t460 = params.mgamma * t1
  t463 = params.mdelta * t40
  t466 = params.mbeta * t2
  t469 = 0.1e1 + t460 * t452 / 0.4e1 + t463 * t456 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t466 * t121
  t470 = 0.1e1 / t469
  t472 = t459 * t470 + params.aa
  t473 = t472 ** 2
  t475 = t450 / t473
  t476 = jnp.sqrt(t447)
  t477 = t7 ** (0.1e1 / 0.6e1)
  t479 = 0.1e1 / t477 / t7
  t480 = t476 * t479
  t484 = 0.1e1 / t257 / t7
  t485 = t256 * t484
  t488 = -t451 * t32 / 0.12e2 - t455 * t485 / 0.6e1
  t490 = t469 ** 2
  t491 = 0.1e1 / t490
  t492 = t459 * t491
  t499 = -t460 * t32 / 0.12e2 - t463 * t485 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t466 * t178
  t501 = t488 * t470 - t492 * t499
  t505 = 0.1e1 / t472 * t476
  t507 = 0.1e1 / t477 / t144
  t511 = t475 * t480 * t501 + 0.7e1 / 0.6e1 * t450 * t505 * t507
  t514 = jnp.exp(-t450 * t505 * t479)
  t515 = t511 * t514
  t516 = t448 * t515
  t517 = t125 ** 2
  t518 = t517 * f.p.zeta_threshold
  t519 = t176 * t123
  t520 = f.my_piecewise3(t124, t518, t519)
  t521 = t193 * t130
  t522 = f.my_piecewise3(t131, t518, t521)
  t523 = t520 + t522
  t524 = jnp.sqrt(t523)
  t526 = 0.1e1 / t524 / t523
  t527 = t472 * t526
  t528 = jnp.sqrt(0.2e1)
  t531 = f.my_piecewise3(t124, 0, 0.5e1 / 0.3e1 * t176 * t180)
  t534 = f.my_piecewise3(t131, 0, 0.5e1 / 0.3e1 * t193 * t195)
  t535 = t531 + t534
  t536 = t528 * t535
  t537 = t527 * t536
  t540 = t448 * t514
  t545 = t451 * t263 / 0.9e1 + 0.5e1 / 0.18e2 * t455 * t260
  t547 = t488 * t491
  t551 = 0.1e1 / t490 / t469
  t552 = t459 * t551
  t553 = t499 ** 2
  t562 = t460 * t263 / 0.9e1 + 0.5e1 / 0.18e2 * t463 * t260 + 0.15000000000000000000000000000000000000000000000000e5 * t466 * t185
  t564 = t545 * t470 - t492 * t562 - 0.2e1 * t547 * t499 + 0.2e1 * t552 * t553
  t565 = 0.1e1 / t524
  t567 = t564 * t565 * t528
  t571 = 0.1e1 / t8 / t184
  t572 = t447 * t571
  t573 = t572 * t514
  t575 = t501 * t565 * t528
  t578 = jnp.pi ** 2
  t579 = 0.1e1 / t578
  t581 = t15 + 0.56553500000000000000000000000000000000000000000000e0 * t16 + 0.130045e2
  t582 = 0.1e1 / t581
  t584 = t4 * t235 * t582
  t586 = t581 ** 2
  t587 = 0.1e1 / t586
  t588 = t10 * t587
  t590 = -t28 - 0.94255833333333333333333333333333333333333333333334e-1 * t33
  t595 = 0.1e1 / t586 / t581
  t596 = t12 * t595
  t597 = t590 ** 2
  t601 = t12 * t587
  t604 = t251 - 0.62837222222222222222222222222222222222222222222223e-1 * t261 + 0.12567444444444444444444444444444444444444444444445e0 * t264
  t610 = (t584 / 0.9e1 + t23 * t588 * t590 / 0.6e1 + t23 * t596 * t597 / 0.2e1 - t23 * t601 * t604 / 0.4e1) * t40 * t42
  t611 = t44 * t581
  t622 = (-t4 * t11 * t582 / 0.12e2 - t23 * t601 * t590 / 0.4e1) * t40 * t42
  t623 = t276 * t581
  t626 = t44 * t590
  t629 = t16 + 0.113107e1
  t630 = t629 ** 2
  t633 = 0.1e1 / t630 / t629 * t1
  t634 = t633 * t3
  t635 = 0.1e1 / t630
  t637 = 0.1e1 + 0.50738680655100000000000000000000000000000000000000e2 * t635
  t638 = 0.1e1 / t637
  t643 = t635 * t253 * t40
  t649 = t635 * t29 * t1
  t654 = t630 ** 2
  t657 = 0.1e1 / t654 / t629 * t1
  t658 = t657 * t3
  t659 = t637 ** 2
  t660 = 0.1e1 / t659
  t665 = t60 + 0.47584e-2
  t666 = t665 * t587
  t667 = t666 * t30
  t672 = t665 * t582
  t673 = t672 * t253
  t676 = t672 * t29
  t679 = t665 ** 2
  t680 = t679 * t595
  t683 = t679 * t587
  t685 = t584 / 0.72e2 + t667 * t31 * t10 * t590 / 0.3e1 - t673 * t320 / 0.9e1 + 0.2e1 / 0.9e1 * t676 * t250 + 0.2e1 * t680 * t597 - t683 * t604
  t686 = 0.1e1 / t679
  t687 = t685 * t686
  t693 = -t676 * t27 / 0.6e1 - t683 * t590
  t695 = 0.1e1 / t679 / t665
  t696 = t693 * t695
  t697 = t581 * t29
  t698 = t696 * t697
  t701 = t693 * t686
  t705 = t579 * (t610 * t611 / 0.3e1 + t622 * t623 / 0.9e1 + t622 * t626 / 0.3e1 + 0.12572604010298724324171900472329070791825696682747e0 * t634 * t235 * t638 + 0.25145208020597448648343800944658141583651393365495e0 * t643 * t256 * t259 * t638 - 0.50290416041194897296687601889316283167302786730989e0 * t649 * t31 * t234 * t638 - 0.63791733988157656503906862782236557702656491548799e1 * t658 * t235 * t660 + 0.41403379428206274608377249480129098139321562919141e-3 * t687 * t581 + 0.69005632380343791013962082466881830232202604865235e-4 * t698 * t27 + 0.41403379428206274608377249480129098139321562919141e-3 * t701 * t590)
  t706 = t705 * t135
  t710 = 0.9e1 * t138
  t711 = t140 * (-t142 * t206 + 0.1e1) * t710
  t723 = t579 * (t622 * t611 / 0.3e1 + 0.37717812030896172972515701416987212375477090048242e0 * t649 * t31 * t10 * t638 + 0.41403379428206274608377249480129098139321562919141e-3 * t701 * t581)
  t724 = t723 * t226
  t727 = t723 * t135
  t733 = t140 * (0.4e1 * t142 * t147 - 0.4e1 * t215 * t206) * t710
  t736 = -0.24e2 * t136 * t148 + 0.3e1 * t205 * t207 + 0.36e2 * t210 * t212 - 0.96e2 * t210 * t217 + 0.24e2 * t227 * t228 - 0.24e2 * t227 * t148 + 0.3e1 * t430 * t207 + 0.60e2 * t210 * t435 + 0.6e1 * t438 * t207 + 0.24e2 * t136 * t228 + 0.29070683134633122641281182963168644715148045498353e-2 * t418 + 0.29070683134633122641281182963168644715148045498353e-2 * t427 + 0.48451138557721871068801971605281074525246742497255e-3 * t425 - 0.3e1 * t516 * t537 + 0.3e1 * t540 * t567 - 0.14e2 * t573 * t575 - t706 * t711 / 0.8e1 - t724 * t711 / 0.4e1 - t727 * t733 / 0.4e1
  t740 = jnp.log(t4 * t13 * t582 / 0.4e1)
  t743 = jnp.atan(0.71231089178181179907634622339714221951452652573438e1 / t629)
  t746 = jnp.log(t679 * t582)
  t749 = t579 * (t740 + 0.31770800474394146398819696256107927053514547209957e0 * t743 + 0.41403379428206274608377249480129098139321562919141e-3 * t746)
  t750 = t749 * t135
  t759 = t140 * (-0.12e2 * t141 * t206 - 0.20e2 * t142 * t434 + 0.32e2 * t215 * t147) * t710
  t762 = t749 * t204
  t765 = t749 * t226
  t770 = t447 / t8 / t145
  t771 = t770 * t514
  t773 = t472 * t565 * t528
  t781 = t511 ** 2
  t782 = t448 * t781
  t783 = t514 * t472
  t784 = t565 * t528
  t785 = t783 * t784
  t788 = t523 ** 2
  t790 = 0.1e1 / t524 / t788
  t792 = t535 ** 2
  t793 = t528 * t792
  t794 = t472 * t790 * t793
  t797 = t501 * t526
  t798 = t797 * t536
  t801 = 0.1e1 / t127
  t807 = f.my_piecewise3(t124, 0, 0.10e2 / 0.9e1 * t801 * t181 + 0.5e1 / 0.3e1 * t176 * t188)
  t808 = 0.1e1 / t132
  t814 = f.my_piecewise3(t131, 0, 0.10e2 / 0.9e1 * t808 * t196 + 0.5e1 / 0.3e1 * t193 * t199)
  t815 = t807 + t814
  t816 = t528 * t815
  t817 = t527 * t816
  t820 = t448 * t511
  t822 = t514 * t501 * t784
  t827 = t572 * t511
  t832 = t450 / t473 / t472
  t833 = t501 ** 2
  t837 = t476 * t507
  t844 = 0.1e1 / t477 / t184
  t848 = -0.2e1 * t832 * t480 * t833 - 0.7e1 / 0.3e1 * t475 * t837 * t501 + t475 * t480 * t564 - 0.91e2 / 0.36e2 * t450 * t505 * t844
  t849 = t448 * t848
  t863 = 0.32300759038481247379201314403520716350164494998170e-3 * t416 * t421 * t423 * t27
  t867 = 0.10766919679493749126400438134506905450054831666057e-3 * t422 * t75 * t253 * t320
  t871 = 0.32300759038481247379201314403520716350164494998170e-3 * t422 * t84 * t29 * t27
  t873 = 0.21533839358987498252800876269013810900109663332113e-3 * t424 * t250
  t902 = t120 * t206
  t909 = 0.1e1 / t145 / t184
  t928 = t31 * t571
  t932 = 0.1e1 / t257 / t184
  t933 = t256 * t932
  t946 = t490 ** 2
  t963 = (-0.7e1 / 0.27e2 * t451 * t928 - 0.20e2 / 0.27e2 * t455 * t933) * t470 - 0.3e1 * t545 * t491 * t499 + 0.6e1 * t488 * t551 * t553 - 0.3e1 * t547 * t562 - 0.6e1 * t459 / t946 * t553 * t499 + 0.6e1 * t552 * t499 * t562 - t492 * (-0.7e1 / 0.27e2 * t460 * t928 - 0.20e2 / 0.27e2 * t463 * t933 - 0.45000000000000000000000000000000000000000000000000e5 * t466 * t206)
  t971 = t6 * t571
  t973 = t4 * t971 * t582
  t977 = t23 * t234 * t587 * t590
  t997 = 0.1e1 / t255
  t999 = t1 * t997 * t6
  t1000 = t571 * t2
  t1007 = 0.1e1 / t16 / t318 / t276 / 0.4e1
  t1009 = t1007 * t2 * t206
  t1012 = t5 * t932
  t1013 = t318 * t1012
  t1016 = t4 * t971
  t1019 = t586 ** 2
  t1020 = 0.1e1 / t1019
  t1022 = t597 * t590
  t1025 = t590 * t604
  t1028 = 0.7e1 / 0.27e2 * t1016
  t1030 = t254 * t933
  t1032 = t30 * t928
  t1034 = -t1028 - 0.37702333333333333333333333333333333333333333333334e0 * t1009 + 0.25134888888888888888888888888888888888888888888890e0 * t1030 - 0.29324037037037037037037037037037037037037037037038e0 * t1032
  t1036 = -0.11e2 / 0.216e3 * t973 - t977 / 0.24e2 - t665 * t595 * t30 * t31 * t10 * t597 + t666 * t254 * t256 * t259 * t590 / 0.3e1 - 0.2e1 / 0.3e1 * t667 * t31 * t234 * t590 + t667 * t31 * t10 * t604 / 0.2e1 + t999 * t1000 * t582 / 0.432e3 - 0.2e1 / 0.3e1 * t672 * t1009 + 0.4e1 / 0.9e1 * t673 * t1013 - 0.14e2 / 0.27e2 * t676 * t1016 - 0.6e1 * t679 * t1020 * t1022 + 0.6e1 * t680 * t1025 - t683 * t1034
  t1040 = t679 ** 2
  t1046 = t654 ** 2
  t1086 = t5 * t484
  t1090 = 0.82806758856412549216754498960258196278643125838282e-3 * t687 * t590 + 0.41403379428206274608377249480129098139321562919141e-3 * t701 * t604 + 0.41403379428206274608377249480129098139321562919141e-3 * t1036 * t686 * t581 + 0.17251408095085947753490520616720457558050651216309e-4 * t693 / t1040 * t581 * t250 + 0.86312224513605868227832795632565231845861115350066e3 / t1046 * t40 * t255 * t1012 / t659 / t637 * t29 - 0.46099548037761989188630301731873259570027554503406e0 * t634 * t971 * t638 + 0.25145208020597448648343800944658141583651393365494e0 / t654 * t40 * t255 * t1012 * t638 * t29 - 0.29769475861140239701823202631710393594573029389440e2 / t654 / t630 * t40 * t255 * t1012 * t660 * t29 + 0.20954340017164540540286500787215117986376161137912e-1 * t633 * t997 * t971 * t2 * t638 - 0.10631955664692942750651143797039426283776081924800e1 * t657 * t997 * t971 * t2 * t660 + 0.2e1 / 0.9e1 * t610 * t623 - 0.2e1 / 0.27e2 * t622 * t1086 * t581
  t1127 = t2 * t206
  t1153 = 0.23390302462324474051432516353486737824307380234560e2 * t658 * t971 * t660 + t622 * t44 * t604 / 0.3e1 + 0.2e1 / 0.9e1 * t622 * t276 * t590 + 0.2e1 / 0.3e1 * t610 * t626 + (-0.7e1 / 0.27e2 * t973 - t977 / 0.3e1 - t23 * t10 * t595 * t597 / 0.2e1 + t23 * t588 * t604 / 0.4e1 - 0.3e1 / 0.2e1 * t23 * t12 * t1020 * t1022 + 0.3e1 / 0.2e1 * t23 * t596 * t1025 - t23 * t601 * t1034 / 0.4e1) * t40 * t42 * t611 / 0.3e1 + 0.15087124812358469189006280566794884950190836019297e1 * t635 * t1007 * t1127 * t638 + 0.13801126476068758202792416493376366046440520973047e-3 * t685 * t695 * t697 * t27 + 0.13801126476068758202792416493376366046440520973047e-3 * t696 * t590 * t29 * t27 + 0.46003754920229194009308054977921220154801736576823e-4 * t696 * t581 * t253 * t320 - 0.10058083208238979459337520377863256633460557346198e1 * t643 * t256 * t932 * t638 + 0.11734430409612142702560440440840466072370650237231e1 * t649 * t31 * t571 * t638 - 0.92007509840458388018616109955842440309603473153646e-4 * t698 * t250
  t1159 = -0.3e1 / 0.2e1 * t516 * t817 + 0.7e1 * t572 * t515 * t537 - 0.7e1 * t573 * t567 + 0.70e2 / 0.3e1 * t771 * t575 - t765 * t759 / 0.8e1 - t750 * t140 * (0.144e3 * t141 * t147 + 0.120e3 * t142 * t909 - 0.240e3 * t215 * t434 - 0.24e2 * t902) * t710 / 0.24e2 - t727 * t759 / 0.8e1 - 0.910e3 / 0.27e2 * t447 / t8 / t146 * t514 * t773 - t723 * t204 * t711 / 0.8e1 + t540 * t963 * t565 * t528 - t579 * (t1090 + t1153) * t135 * t711 / 0.24e2
  t1162 = t181 * t180
  t1169 = 0.6e1 * t185 - 0.6e1 * t902
  t1173 = f.my_piecewise3(t124, 0, -0.8e1 / 0.27e2 / t519 * t1162 + 0.4e1 / 0.3e1 * t177 * t180 * t188 + 0.4e1 / 0.3e1 * t127 * t1169)
  t1175 = t196 * t195
  t1181 = -t1169
  t1185 = f.my_piecewise3(t131, 0, -0.8e1 / 0.27e2 / t521 * t1175 + 0.4e1 / 0.3e1 * t194 * t195 * t199 + 0.4e1 / 0.3e1 * t132 * t1181)
  t1186 = t1173 + t1185
  t1195 = 0.19380455423088748427520788642112429810098696998902e-2 * t417 * t84
  t1197 = 0.96902277115443742137603943210562149050493484994510e-3 * t116 * t358
  t1199 = t4 * t971 * t76
  t1203 = t23 * t234 * t81 * t84
  t1232 = t80 ** 2
  t1233 = 0.1e1 / t1232
  t1235 = t352 * t84
  t1238 = t84 * t358
  t1244 = -t1028 - 0.12424800000000000000000000000000000000000000000000e1 * t1009 + 0.82832000000000000000000000000000000000000000000000e0 * t1030 - 0.96637333333333333333333333333333333333333333333333e0 * t1032
  t1246 = -0.11e2 / 0.216e3 * t1199 - t1203 / 0.24e2 - t106 * t350 * t30 * t31 * t10 * t352 + t401 * t254 * t256 * t259 * t84 / 0.3e1 - 0.2e1 / 0.3e1 * t402 * t31 * t234 * t84 + t402 * t31 * t10 * t358 / 0.2e1 + t999 * t1000 * t76 / 0.432e3 - 0.2e1 / 0.3e1 * t107 * t1009 + 0.4e1 / 0.9e1 * t407 * t1013 - 0.14e2 / 0.27e2 * t108 * t1016 - 0.6e1 * t111 * t1233 * t1235 + 0.6e1 * t412 * t1238 - t112 * t1244
  t1249 = 0.96902277115443742137603943210562149050493484994510e-3 * t1246 * t115 * t75
  t1286 = 0.24e2 * t210 * t140 * t120 * t206 + t175 * t1186 * t207 - 0.120e3 * t210 * t143 * t909 - 0.144e3 * t210 * t211 * t147 - 0.12e2 * t205 * t148 - 0.12e2 * t430 * t148 - 0.24e2 * t438 * t148 + 0.12e2 * t205 * t228 + 0.36e2 * t227 * t212 - 0.96e2 * t227 * t217 + 0.60e2 * t227 * t435
  t1297 = 0.15906298270010708072125572157552384197389506431465e0 * t96 * t1007 * t1127 * t101
  t1313 = t4 * t971 * t19
  t1317 = t23 * t234 * t25 * t35
  t1346 = t24 ** 2
  t1347 = 0.1e1 / t1346
  t1349 = t246 * t35
  t1352 = t35 * t266
  t1358 = -t1028 - 0.23534733333333333333333333333333333333333333333333e1 * t1009 + 0.15689822222222222222222222222222222222222222222222e1 * t1030 - 0.18304792592592592592592592592592592592592592592592e1 * t1032
  t1360 = -0.11e2 / 0.216e3 * t1313 - t1317 / 0.24e2 - t61 * t244 * t30 * t31 * t10 * t246 + t311 * t254 * t256 * t259 * t35 / 0.3e1 - 0.2e1 / 0.3e1 * t312 * t31 * t234 * t35 + t312 * t31 * t10 * t266 / 0.2e1 + t999 * t1000 * t19 / 0.432e3 - 0.2e1 / 0.3e1 * t62 * t1009 + 0.4e1 / 0.9e1 * t317 * t1013 - 0.14e2 / 0.27e2 * t63 * t1016 - 0.6e1 * t66 * t1347 * t1349 + 0.6e1 * t325 * t1352 - t67 * t1358
  t1368 = -t863 - t867 + 0.74928903184753727944217879854743374601869155501904e-3 * t335 * t35 * t29 * t27 + 0.24976301061584575981405959951581124867289718500635e-3 * t335 * t18 * t253 * t320 + 0.74928903184753727944217879854743374601869155501904e-3 * t329 * t334 * t336 * t27 - t871 + t873 - 0.49952602123169151962811919903162249734579437001269e-3 * t337 * t250 + 0.22478670955426118383265363956423012380560746650571e-2 * t1360 * t70 * t18 + 0.44957341910852236766530727912846024761121493301142e-2 * t330 * t35 + 0.22478670955426118383265363956423012380560746650571e-2 * t71 * t266 - t1195
  t1380 = 0.48602578047254941331494803814743396158690158540586e-1 * t376 * t971 * t101
  t1383 = 0.18394613361864149606712411343047178787314745838373e1 * t394 * t971 * t396
  t1386 = 0.10363566666666666666666666666666666666666666666667e-1 * t90 * t44 * t358
  t1388 = 0.20727133333333333333333333333333333333333333333334e-1 * t364 * t370
  t1391 = 0.69090444444444444444444444444444444444444444444446e-2 * t90 * t276 * t84
  t1416 = -t1197 - t1249 + 0.16555529631147769304086026058847109426994589620583e0 * t50 * t1007 * t1127 * t55 - t1297 + 0.34545222222222222222222222222222222222222222222222e-2 * t272 * t277 - 0.11515074074074074074074074074074074074074074074074e-2 * t43 * t1086 * t18 + t1380 - t1383 - t1386 - t1388 - t1391 + 0.51817833333333333333333333333333333333333333333333e-2 * (-0.7e1 / 0.27e2 * t1313 - t1317 / 0.3e1 - t23 * t10 * t244 * t246 / 0.2e1 + t23 * t239 * t266 / 0.4e1 - 0.3e1 / 0.2e1 * t23 * t12 * t1347 * t1349 + 0.3e1 / 0.2e1 * t23 * t245 * t1352 - t23 * t26 * t1358 / 0.4e1) * t40 * t42 * t45
  t1419 = 0.69090444444444444444444444444444444444444444444446e-2 * t364 * t367
  t1422 = 0.23030148148148148148148148148148148148148148148149e-2 * t90 * t1086 * t75
  t1449 = 0.10363566666666666666666666666666666666666666666667e-1 * (-0.7e1 / 0.27e2 * t1199 - t1203 / 0.3e1 - t23 * t10 * t350 * t352 / 0.2e1 + t23 * t345 * t358 / 0.4e1 - 0.3e1 / 0.2e1 * t23 * t12 * t1233 * t1235 + 0.3e1 / 0.2e1 * t23 * t351 * t1238 - t23 * t82 * t1244 / 0.4e1) * t40 * t42 * t91
  t1461 = t66 ** 2
  t1487 = -t1419 + t1422 - 0.50586340539618183984707301846477278804705690507337e-1 * t286 * t971 * t55 - t1449 + 0.11322067513073894329090826277329563323954137090250e1 * t304 * t971 * t306 + 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t44 * t266 + 0.34545222222222222222222222222222222222222222222222e-2 * t43 * t276 * t35 + 0.10363566666666666666666666666666666666666666666667e-1 * t272 * t280 + 0.93661128980942159930272349818429218252336444377380e-4 * t69 / t1461 * t18 * t250 + 0.27592549385246282173476710098078515711657649367638e-1 / t300 * t40 * t255 * t1012 * t55 * t29 - 0.14409904107548592782479233443873989685032538114864e1 / t300 / t49 * t40 * t255 * t1012 * t306 * t29 + 0.22993791154371901811230591748398763093048041139699e-2 * t285 * t997 * t971 * t2 * t55
  t1504 = 0.10604198846673805381417048105034922798259670954310e0 * t381 * t256 * t932 * t101
  t1508 = 0.12371565321119439611653222789207409931302949446695e0 * t98 * t31 * t571 * t101
  t1513 = 0.22092080930570427877952183552156089163040981154812e-2 * t375 * t997 * t971 * t2 * t101
  t1518 = 0.83611878917564316394147324286578085396885208356242e-1 * t393 * t997 * t971 * t2 * t396
  t1519 = t111 ** 2
  t1524 = 0.40375948798101559224001643004400895437705618747712e-4 * t114 / t1519 * t75 * t250
  t1525 = t390 ** 2
  t1534 = 0.50631328524251801700246888250186209051365905137714e2 / t1525 * t40 * t255 * t1012 / t395 / t100 * t29
  t1541 = 0.26510497116684513453542620262587306995649177385774e-1 / t390 * t40 * t255 * t1012 * t101 * t29
  t1549 = 0.23411326096918008590361250800241863911127858339748e1 / t390 / t95 * t40 * t255 * t1012 * t396 * t29
  t1550 = t300 ** 2
  t1560 = -0.51463943241244974223140119442407106017973350410227e-1 * t303 * t997 * t971 * t2 * t306 - 0.11037019754098512869390684039231406284663059747056e0 * t291 * t256 * t932 * t55 + 0.12876523046448265014289131379103307332106903038231e0 * t52 * t31 * t571 * t55 + t1504 - t1508 - t1513 + t1518 - t1524 - t1534 - t1541 + t1549 + 0.18429583437767336287475605998441200095133403022660e2 / t1550 * t40 * t255 * t1012 / t305 / t54 * t29
  t1584 = f.my_piecewise3(t124, 0, -0.10e2 / 0.27e2 / t128 * t1162 + 0.10e2 / 0.3e1 * t801 * t180 * t188 + 0.5e1 / 0.3e1 * t176 * t1169)
  t1594 = f.my_piecewise3(t131, 0, -0.10e2 / 0.27e2 / t133 * t1175 + 0.10e2 / 0.3e1 * t808 * t195 * t199 + 0.5e1 / 0.3e1 * t193 * t1181)
  t1615 = -t1422 + t1449 - t706 * t733 / 0.8e1 - 0.7e1 * t572 * t848 * t785 + 0.3e1 * t820 * t514 * t564 * t784 - t540 * t527 * t528 * (t1584 + t1594) / 0.2e1 - 0.3e1 / 0.2e1 * t540 * t797 * t816 + 0.9e1 / 0.4e1 * t540 * t501 * t790 * t793 - 0.3e1 / 0.2e1 * t540 * t564 * t526 * t536 + 0.3e1 * t782 * t822 + 0.3e1 * t849 * t822
  t1645 = t473 ** 2
  t1685 = -t1504 + t1508 + t1513 - t1518 + t1524 + t1534 + t1541 - t1549 + 0.3e1 * t429 * t226 * t207 + 0.12e2 * t430 * t228 - t705 * t226 * t711 / 0.8e1
  t1690 = -t750 * t759 / 0.8e1 - t762 * t711 / 0.8e1 - t765 * t733 / 0.4e1 + 0.70e2 / 0.3e1 * t771 * t773 + 0.31090700000000000000000000000000000000000000000001e-1 * t365 + 0.10363566666666666666666666666666666666666666666667e-1 * t368 + 0.31090700000000000000000000000000000000000000000001e-1 * t371 + 0.39765745675026770180313930393880960493473766078662e-1 * t378 - 0.15050138205161576950946518371584055371439337504124e1 * t398 + 0.3e1 * t782 * t785 + 0.9e1 / 0.4e1 * t540 * t794 - 0.3e1 * t540 * t798 - 0.3e1 / 0.2e1 * t540 * t817 + 0.6e1 * t820 * t822 + 0.7e1 * t573 * t537 - 0.14e2 * t827 * t785 + 0.3e1 * t849 * t785 + 0.79531491350053540360627860787761920986947532157324e-1 * t384 - 0.15906298270010708072125572157552384197389506431465e0 * t388 + t7 * (t1685 + t1615 - 0.3e1 * t516 * t798 + 0.9e1 / 0.4e1 * t516 * t794 + 0.7e1 / 0.2e1 * t573 * t817 + 0.7e1 * t573 * t798 - 0.21e2 / 0.4e1 * t573 * t794 - 0.35e2 / 0.3e1 * t771 * t537 - 0.14e2 * t827 * t822 + 0.24e2 * t438 * t228 + 0.60e2 * t136 * t435 + 0.36e2 * t136 * t212 - 0.96e2 * t136 * t217 - t762 * t733 / 0.8e1 - t724 * t733 / 0.4e1 + 0.9e1 / 0.4e1 * t448 * t783 * t790 * t528 * t535 * t815 + t1419 + t1391 + t1386 + t1388 + t1383 - t1380 + t1297 + t1286 + t1249 + t1197 + t1195 + t1159 + t448 * t781 * t511 * t785 + 0.3e1 * t448 * t848 * t511 * t785 - 0.3e1 / 0.2e1 * t448 * t848 * t514 * t537 - 0.3e1 / 0.2e1 * t448 * t781 * t514 * t537 + t871 - t873 + t867 + t863 - 0.15e2 / 0.8e1 * t540 * t472 / t524 / t788 / t523 * t528 * t792 * t535 - t749 * t1186 * t711 / 0.24e2 + 0.3e1 * t119 * t204 * t207 + 0.240e3 * t210 * t216 * t434 + (t1368 + t1416 + t1487 + t1560) * t135 * t207 + 0.70e2 / 0.3e1 * t770 * t511 * t785 - 0.7e1 * t572 * t781 * t785 + t448 * (0.6e1 * t450 / t1645 * t480 * t833 * t501 + 0.7e1 * t832 * t837 * t833 - 0.6e1 * t832 * t480 * t501 * t564 + 0.91e2 / 0.12e2 * t475 * t476 * t844 * t501 - 0.7e1 / 0.2e1 * t475 * t837 * t564 + t475 * t480 * t963 + 0.1729e4 / 0.216e3 * t450 * t505 / t477 / t145) * t785)
  d111 = t736 + t1690

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
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

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t10 = 0.1e1 / t8 / t7
  t11 = t6 * t10
  t12 = 0.1e1 / t8
  t13 = t6 * t12
  t14 = t4 * t13
  t15 = t14 / 0.4e1
  t16 = jnp.sqrt(t14)
  t18 = t15 + 0.35302100000000000000000000000000000000000000000000e1 * t16 + 0.180578e2
  t19 = 0.1e1 / t18
  t23 = t4 * t6
  t24 = t18 ** 2
  t25 = 0.1e1 / t24
  t26 = t12 * t25
  t27 = t4 * t11
  t28 = t27 / 0.12e2
  t29 = 0.1e1 / t16
  t30 = t29 * t1
  t31 = t3 * t6
  t32 = t31 * t10
  t33 = t30 * t32
  t35 = -t28 - 0.58836833333333333333333333333333333333333333333333e0 * t33
  t40 = t1 ** 2
  t42 = 0.1e1 / t3
  t43 = (-t4 * t11 * t19 / 0.12e2 - t23 * t26 * t35 / 0.4e1) * t40 * t42
  t44 = t5 * t8
  t45 = t44 * t18
  t48 = t16 + 0.706042e1
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t52 = t50 * t29 * t1
  t54 = 0.1e1 + 0.22381669423600000000000000000000000000000000000000e2 * t50
  t55 = 0.1e1 / t54
  t60 = t16 / 0.2e1
  t61 = t60 + 0.32500e0
  t62 = t61 * t19
  t63 = t62 * t29
  t66 = t61 ** 2
  t67 = t66 * t25
  t69 = -t63 * t27 / 0.6e1 - t67 * t35
  t70 = 0.1e1 / t66
  t71 = t69 * t70
  t75 = t15 + 0.18637200000000000000000000000000000000000000000000e1 * t16 + 0.129352e2
  t76 = 0.1e1 / t75
  t80 = t75 ** 2
  t81 = 0.1e1 / t80
  t82 = t12 * t81
  t84 = -t28 - 0.31062000000000000000000000000000000000000000000000e0 * t33
  t90 = (-t4 * t11 * t76 / 0.12e2 - t23 * t82 * t84 / 0.4e1) * t40 * t42
  t91 = t44 * t75
  t94 = t16 + 0.372744e1
  t95 = t94 ** 2
  t96 = 0.1e1 / t95
  t98 = t96 * t29 * t1
  t100 = 0.1e1 + 0.37846991046400000000000000000000000000000000000000e2 * t96
  t101 = 0.1e1 / t100
  t106 = t60 + 0.10498e0
  t107 = t106 * t76
  t108 = t107 * t29
  t111 = t106 ** 2
  t112 = t111 * t81
  t114 = -t108 * t27 / 0.6e1 - t112 * t84
  t115 = 0.1e1 / t111
  t116 = t114 * t115
  t119 = 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t45 + 0.41388824077869423260215065147117773567486474051458e-1 * t52 * t31 * t10 * t55 + 0.22478670955426118383265363956423012380560746650571e-2 * t71 * t18 - 0.10363566666666666666666666666666666666666666666667e-1 * t90 * t91 - 0.39765745675026770180313930393880960493473766078662e-1 * t98 * t31 * t10 * t101 - 0.96902277115443742137603943210562149050493484994510e-3 * t116 * t75
  t120 = r0 - r1
  t121 = 0.1e1 / t7
  t122 = t120 * t121
  t123 = 0.1e1 + t122
  t124 = t123 <= f.p.zeta_threshold
  t125 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t126 = t125 * f.p.zeta_threshold
  t127 = t123 ** (0.1e1 / 0.3e1)
  t128 = t127 * t123
  t129 = f.my_piecewise3(t124, t126, t128)
  t130 = 0.1e1 - t122
  t131 = t130 <= f.p.zeta_threshold
  t132 = t130 ** (0.1e1 / 0.3e1)
  t133 = t132 * t130
  t134 = f.my_piecewise3(t131, t126, t133)
  t135 = t129 + t134 - 0.2e1
  t136 = t119 * t135
  t137 = 2 ** (0.1e1 / 0.3e1)
  t138 = t137 - 0.1e1
  t140 = 0.1e1 / t138 / 0.2e1
  t141 = t120 ** 2
  t142 = t141 * t120
  t143 = t140 * t142
  t144 = t7 ** 2
  t145 = t144 ** 2
  t146 = t145 * t7
  t147 = 0.1e1 / t146
  t148 = t143 * t147
  t151 = t127 ** 2
  t152 = 0.1e1 / t151
  t153 = 0.1e1 / t144
  t155 = -t120 * t153 + t121
  t156 = t155 ** 2
  t159 = t144 * t7
  t160 = 0.1e1 / t159
  t163 = 0.2e1 * t120 * t160 - 0.2e1 * t153
  t167 = f.my_piecewise3(t124, 0, 0.4e1 / 0.9e1 * t152 * t156 + 0.4e1 / 0.3e1 * t127 * t163)
  t168 = t132 ** 2
  t169 = 0.1e1 / t168
  t170 = -t155
  t171 = t170 ** 2
  t174 = -t163
  t178 = f.my_piecewise3(t131, 0, 0.4e1 / 0.9e1 * t169 * t171 + 0.4e1 / 0.3e1 * t132 * t174)
  t179 = t167 + t178
  t180 = t119 * t179
  t181 = t141 ** 2
  t182 = t140 * t181
  t183 = 0.1e1 / t145
  t184 = t182 * t183
  t190 = jnp.log(t4 * t13 * t19 / 0.4e1)
  t194 = jnp.atan(0.47309269095601128299619512910246923284397083311420e1 / t48)
  t197 = jnp.log(t66 * t19)
  t202 = jnp.log(t4 * t13 * t76 / 0.4e1)
  t206 = jnp.atan(0.61519908197590802321728722658814145360143502774884e1 / t94)
  t209 = jnp.log(t111 * t76)
  t211 = 0.1554535e-1 * t190 + 0.52491393169780936217021346072241076933841385384497e-1 * t194 + 0.22478670955426118383265363956423012380560746650571e-2 * t197 - 0.310907e-1 * t202 - 0.38783294878113014394824731224995739188004877421366e-1 * t206 - 0.96902277115443742137603943210562149050493484994510e-3 * t209
  t214 = f.my_piecewise3(t124, 0, 0.4e1 / 0.3e1 * t127 * t155)
  t217 = f.my_piecewise3(t131, 0, 0.4e1 / 0.3e1 * t132 * t170)
  t218 = t214 + t217
  t219 = t211 * t218
  t220 = t140 * t141
  t221 = t220 * t183
  t224 = jnp.pi ** 2
  t225 = 0.1e1 / t224
  t226 = t60 + 0.47584e-2
  t228 = t15 + 0.56553500000000000000000000000000000000000000000000e0 * t16 + 0.130045e2
  t229 = 0.1e1 / t228
  t230 = t226 * t229
  t231 = t230 * t29
  t234 = t226 ** 2
  t235 = t228 ** 2
  t236 = 0.1e1 / t235
  t237 = t234 * t236
  t239 = -t28 - 0.94255833333333333333333333333333333333333333333334e-1 * t33
  t241 = -t231 * t27 / 0.6e1 - t237 * t239
  t242 = 0.1e1 / t234
  t243 = t241 * t242
  t245 = 0.1e1 / t8 / t144
  t246 = t6 * t245
  t247 = t4 * t246
  t248 = t247 / 0.9e1
  t250 = 0.1e1 / t16 / t14
  t251 = t250 * t40
  t252 = t3 ** 2
  t253 = t252 * t5
  t254 = t8 ** 2
  t256 = 0.1e1 / t254 / t144
  t257 = t253 * t256
  t258 = t251 * t257
  t260 = t31 * t245
  t261 = t30 * t260
  t263 = t248 - 0.62837222222222222222222222222222222222222222222223e-1 * t258 + 0.12567444444444444444444444444444444444444444444445e0 * t261
  t267 = t4 * t246 * t229
  t269 = t226 * t236
  t270 = t269 * t30
  t271 = t10 * t239
  t275 = t230 * t250
  t276 = t40 * t252
  t277 = t5 * t256
  t278 = t276 * t277
  t284 = 0.1e1 / t235 / t228
  t285 = t234 * t284
  t286 = t239 ** 2
  t290 = t267 / 0.72e2 + t270 * t31 * t271 / 0.3e1 - t275 * t278 / 0.9e1 + 0.2e1 / 0.9e1 * t231 * t247 + 0.2e1 * t285 * t286 - t237 * t263
  t291 = t290 * t242
  t295 = 0.1e1 / t8 / t159
  t296 = t6 * t295
  t298 = t4 * t296 * t229
  t300 = t245 * t236
  t302 = t23 * t300 * t239
  t304 = t226 * t284
  t305 = t304 * t30
  t309 = t269 * t251
  t322 = 0.1e1 / t252
  t324 = t1 * t322 * t6
  t325 = t295 * t2
  t329 = 0.1e1 / t254
  t330 = t5 * t329
  t334 = 0.1e1 / t16 / t276 / t330 / 0.4e1
  t335 = t334 * t2
  t336 = t335 * t183
  t340 = 0.1e1 / t254 / t159
  t341 = t5 * t340
  t342 = t276 * t341
  t345 = t4 * t296
  t348 = t235 ** 2
  t349 = 0.1e1 / t348
  t350 = t234 * t349
  t351 = t286 * t239
  t354 = t239 * t263
  t357 = 0.7e1 / 0.27e2 * t345
  t359 = t253 * t340
  t360 = t251 * t359
  t362 = t31 * t295
  t363 = t30 * t362
  t365 = -t357 - 0.37702333333333333333333333333333333333333333333334e0 * t336 + 0.25134888888888888888888888888888888888888888888890e0 * t360 - 0.29324037037037037037037037037037037037037037037038e0 * t363
  t367 = -0.11e2 / 0.216e3 * t298 - t302 / 0.24e2 - t305 * t31 * t10 * t286 + t309 * t253 * t256 * t239 / 0.3e1 - 0.2e1 / 0.3e1 * t270 * t31 * t245 * t239 + t270 * t31 * t10 * t263 / 0.2e1 + t324 * t325 * t229 / 0.432e3 - 0.2e1 / 0.3e1 * t230 * t336 + 0.4e1 / 0.9e1 * t275 * t342 - 0.14e2 / 0.27e2 * t231 * t345 - 0.6e1 * t350 * t351 + 0.6e1 * t285 * t354 - t237 * t365
  t368 = t367 * t242
  t371 = t234 ** 2
  t372 = 0.1e1 / t371
  t373 = t241 * t372
  t374 = t373 * t228
  t377 = t16 + 0.113107e1
  t378 = t377 ** 2
  t379 = t378 ** 2
  t380 = 0.1e1 / t379
  t381 = t380 * t40
  t382 = t381 * t252
  t383 = 0.1e1 / t378
  t385 = 0.1e1 + 0.50738680655100000000000000000000000000000000000000e2 * t383
  t386 = 0.1e1 / t385
  t387 = t386 * t29
  t392 = 0.1e1 / t379 / t378
  t393 = t392 * t40
  t394 = t393 * t252
  t395 = t385 ** 2
  t396 = 0.1e1 / t395
  t397 = t396 * t29
  t401 = t378 * t377
  t403 = 0.1e1 / t401 * t1
  t404 = t403 * t322
  t405 = t2 * t386
  t410 = 0.1e1 / t379 / t377
  t411 = t410 * t1
  t412 = t411 * t322
  t413 = t2 * t396
  t417 = t379 ** 2
  t418 = 0.1e1 / t417
  t419 = t418 * t40
  t420 = t419 * t252
  t422 = 0.1e1 / t395 / t385
  t423 = t422 * t29
  t430 = t12 * t236
  t436 = (-t4 * t11 * t229 / 0.12e2 - t23 * t430 * t239 / 0.4e1) * t40 * t42
  t438 = 0.1e1 / t254 / t7
  t439 = t5 * t438
  t440 = t439 * t228
  t443 = t403 * t3
  t448 = t10 * t236
  t452 = t12 * t284
  t461 = (t267 / 0.9e1 + t23 * t448 * t239 / 0.6e1 + t23 * t452 * t286 / 0.2e1 - t23 * t430 * t263 / 0.4e1) * t40 * t42
  t462 = t330 * t228
  t465 = 0.41403379428206274608377249480129098139321562919141e-3 * t243 * t263 + 0.82806758856412549216754498960258196278643125838282e-3 * t291 * t239 + 0.41403379428206274608377249480129098139321562919141e-3 * t368 * t228 + 0.17251408095085947753490520616720457558050651216309e-4 * t374 * t247 + 0.25145208020597448648343800944658141583651393365494e0 * t382 * t341 * t387 - 0.29769475861140239701823202631710393594573029389440e2 * t394 * t341 * t397 + 0.20954340017164540540286500787215117986376161137912e-1 * t404 * t296 * t405 - 0.10631955664692942750651143797039426283776081924800e1 * t412 * t296 * t413 + 0.86312224513605868227832795632565231845861115350066e3 * t420 * t341 * t423 - 0.2e1 / 0.27e2 * t436 * t440 - 0.46099548037761989188630301731873259570027554503406e0 * t443 * t296 * t386 + 0.2e1 / 0.9e1 * t461 * t462
  t466 = t411 * t3
  t470 = t44 * t263
  t473 = t44 * t239
  t476 = t330 * t239
  t481 = t10 * t284
  t488 = t12 * t349
  t500 = (-0.7e1 / 0.27e2 * t298 - t302 / 0.3e1 - t23 * t481 * t286 / 0.2e1 + t23 * t448 * t263 / 0.4e1 - 0.3e1 / 0.2e1 * t23 * t488 * t351 + 0.3e1 / 0.2e1 * t23 * t452 * t354 - t23 * t430 * t365 / 0.4e1) * t40 * t42
  t501 = t44 * t228
  t504 = t383 * t334
  t505 = t2 * t183
  t510 = 0.1e1 / t234 / t226
  t511 = t290 * t510
  t512 = t228 * t29
  t513 = t511 * t512
  t516 = t241 * t510
  t517 = t239 * t29
  t518 = t516 * t517
  t522 = t383 * t250 * t40
  t528 = t383 * t29 * t1
  t533 = t516 * t512
  t536 = t228 * t250
  t537 = t516 * t536
  t540 = 0.23390302462324474051432516353486737824307380234560e2 * t466 * t296 * t396 + t436 * t470 / 0.3e1 + 0.2e1 / 0.3e1 * t461 * t473 + 0.2e1 / 0.9e1 * t436 * t476 + t500 * t501 / 0.3e1 + 0.15087124812358469189006280566794884950190836019297e1 * t504 * t505 * t386 + 0.13801126476068758202792416493376366046440520973047e-3 * t513 * t27 + 0.13801126476068758202792416493376366046440520973047e-3 * t518 * t27 - 0.10058083208238979459337520377863256633460557346198e1 * t522 * t253 * t340 * t386 + 0.11734430409612142702560440440840466072370650237231e1 * t528 * t31 * t295 * t386 - 0.92007509840458388018616109955842440309603473153646e-4 * t533 * t247 + 0.46003754920229194009308054977921220154801736576823e-4 * t537 * t278
  t542 = t225 * (t465 + t540)
  t543 = t542 * t135
  t547 = 0.9e1 * t138
  t548 = t140 * (-t181 * t183 + 0.1e1) * t547
  t554 = jnp.log(t4 * t13 * t229 / 0.4e1)
  t557 = jnp.atan(0.71231089178181179907634622339714221951452652573438e1 / t377)
  t560 = jnp.log(t234 * t229)
  t563 = t225 * (t554 + 0.31770800474394146398819696256107927053514547209957e0 * t557 + 0.41403379428206274608377249480129098139321562919141e-3 * t560)
  t564 = t151 * t123
  t565 = 0.1e1 / t564
  t566 = t156 * t155
  t569 = t152 * t155
  t572 = t120 * t183
  t574 = 0.6e1 * t160 - 0.6e1 * t572
  t578 = f.my_piecewise3(t124, 0, -0.8e1 / 0.27e2 * t565 * t566 + 0.4e1 / 0.3e1 * t569 * t163 + 0.4e1 / 0.3e1 * t127 * t574)
  t579 = t168 * t130
  t580 = 0.1e1 / t579
  t581 = t171 * t170
  t584 = t169 * t170
  t587 = -t574
  t591 = f.my_piecewise3(t131, 0, -0.8e1 / 0.27e2 * t580 * t581 + 0.4e1 / 0.3e1 * t584 * t174 + 0.4e1 / 0.3e1 * t132 * t587)
  t592 = t578 + t591
  t593 = t563 * t592
  t596 = t563 * t135
  t600 = t145 * t144
  t601 = 0.1e1 / t600
  t605 = 0.1e1 / t145 / t159
  t610 = t140 * (0.144e3 * t141 * t147 - 0.240e3 * t142 * t601 + 0.120e3 * t181 * t605 - 0.24e2 * t572) * t547
  t622 = t225 * (t436 * t501 / 0.3e1 + 0.37717812030896172972515701416987212375477090048242e0 * t528 * t31 * t10 * t386 + 0.41403379428206274608377249480129098139321562919141e-3 * t243 * t228)
  t623 = t622 * t179
  t626 = t563 * t179
  t632 = t140 * (-0.4e1 * t142 * t183 + 0.4e1 * t181 * t147) * t547
  t636 = t4 * t296 * t19
  t638 = t245 * t25
  t640 = t23 * t638 * t35
  t643 = 0.1e1 / t24 / t18
  t644 = t10 * t643
  t645 = t35 ** 2
  t649 = t10 * t25
  t652 = t248 - 0.39224555555555555555555555555555555555555555555555e0 * t258 + 0.78449111111111111111111111111111111111111111111110e0 * t261
  t656 = t24 ** 2
  t657 = 0.1e1 / t656
  t658 = t12 * t657
  t659 = t645 * t35
  t663 = t12 * t643
  t664 = t35 * t652
  t671 = -t357 - 0.23534733333333333333333333333333333333333333333333e1 * t336 + 0.15689822222222222222222222222222222222222222222222e1 * t360 - 0.18304792592592592592592592592592592592592592592592e1 * t363
  t677 = (-0.7e1 / 0.27e2 * t636 - t640 / 0.3e1 - t23 * t644 * t645 / 0.2e1 + t23 * t649 * t652 / 0.4e1 - 0.3e1 / 0.2e1 * t23 * t658 * t659 + 0.3e1 / 0.2e1 * t23 * t663 * t664 - t23 * t26 * t671 / 0.4e1) * t40 * t42
  t681 = t4 * t246 * t76
  t683 = t10 * t81
  t688 = 0.1e1 / t80 / t75
  t689 = t12 * t688
  t690 = t84 ** 2
  t696 = t248 - 0.20708000000000000000000000000000000000000000000000e0 * t258 + 0.41416000000000000000000000000000000000000000000000e0 * t261
  t702 = (t681 / 0.9e1 + t23 * t683 * t84 / 0.6e1 + t23 * t689 * t690 / 0.2e1 - t23 * t82 * t696 / 0.4e1) * t40 * t42
  t703 = t330 * t75
  t704 = t702 * t703
  t706 = t330 * t84
  t707 = t90 * t706
  t709 = t44 * t84
  t710 = t702 * t709
  t712 = t50 * t334
  t717 = 0.1e1 / t66 / t61
  t718 = t69 * t717
  t719 = t35 * t29
  t720 = t718 * t719
  t723 = t18 * t250
  t724 = t718 * t723
  t728 = t4 * t246 * t19
  t730 = t61 * t25
  t731 = t730 * t30
  t732 = t10 * t35
  t736 = t62 * t250
  t741 = t66 * t643
  t745 = t728 / 0.72e2 + t731 * t31 * t732 / 0.3e1 - t736 * t278 / 0.9e1 + 0.2e1 / 0.9e1 * t63 * t247 + 0.2e1 * t741 * t645 - t67 * t652
  t746 = t745 * t717
  t747 = t18 * t29
  t748 = t746 * t747
  t752 = 0.1e1 / t111 / t106
  t753 = t114 * t752
  t754 = t84 * t29
  t755 = t753 * t754
  t756 = t755 * t27
  t759 = t106 * t81
  t760 = t759 * t30
  t761 = t10 * t84
  t765 = t107 * t250
  t770 = t111 * t688
  t774 = t681 / 0.72e2 + t760 * t31 * t761 / 0.3e1 - t765 * t278 / 0.9e1 + 0.2e1 / 0.9e1 * t108 * t247 + 0.2e1 * t770 * t690 - t112 * t696
  t775 = t774 * t752
  t776 = t75 * t29
  t777 = t775 * t776
  t778 = t777 * t27
  t780 = t75 * t250
  t781 = t753 * t780
  t782 = t781 * t278
  t784 = t718 * t747
  t787 = 0.51817833333333333333333333333333333333333333333333e-2 * t677 * t45 - 0.69090444444444444444444444444444444444444444444446e-2 * t704 - 0.69090444444444444444444444444444444444444444444446e-2 * t707 - 0.20727133333333333333333333333333333333333333333334e-1 * t710 + 0.16555529631147769304086026058847109426994589620583e0 * t712 * t505 * t55 + 0.74928903184753727944217879854743374601869155501904e-3 * t720 * t27 + 0.24976301061584575981405959951581124867289718500635e-3 * t724 * t278 + 0.74928903184753727944217879854743374601869155501904e-3 * t748 * t27 - 0.32300759038481247379201314403520716350164494998170e-3 * t756 - 0.32300759038481247379201314403520716350164494998170e-3 * t778 - 0.10766919679493749126400438134506905450054831666057e-3 * t782 - 0.49952602123169151962811919903162249734579437001269e-3 * t784 * t247
  t788 = t753 * t776
  t789 = t788 * t247
  t791 = t95 ** 2
  t793 = 0.1e1 / t791 / t94
  t794 = t793 * t1
  t795 = t794 * t322
  t796 = t100 ** 2
  t797 = 0.1e1 / t796
  t798 = t2 * t797
  t800 = t795 * t296 * t798
  t807 = t50 * t250 * t40
  t813 = t96 * t250 * t40
  t816 = t813 * t253 * t340 * t101
  t818 = t791 ** 2
  t819 = 0.1e1 / t818
  t820 = t819 * t40
  t821 = t820 * t252
  t823 = 0.1e1 / t796 / t100
  t824 = t823 * t29
  t826 = t821 * t341 * t824
  t828 = 0.1e1 / t791
  t829 = t828 * t40
  t830 = t829 * t252
  t831 = t101 * t29
  t833 = t830 * t341 * t831
  t836 = 0.1e1 / t791 / t95
  t837 = t836 * t40
  t838 = t837 * t252
  t839 = t797 * t29
  t841 = t838 * t341 * t839
  t843 = t66 ** 2
  t844 = 0.1e1 / t843
  t845 = t69 * t844
  t846 = t845 * t18
  t849 = t49 ** 2
  t850 = 0.1e1 / t849
  t851 = t850 * t40
  t852 = t851 * t252
  t853 = t55 * t29
  t858 = 0.1e1 / t849 / t49
  t859 = t858 * t40
  t860 = t859 * t252
  t861 = t54 ** 2
  t862 = 0.1e1 / t861
  t863 = t862 * t29
  t867 = t49 * t48
  t868 = 0.1e1 / t867
  t869 = t868 * t1
  t870 = t869 * t322
  t871 = t2 * t55
  t875 = 0.21533839358987498252800876269013810900109663332113e-3 * t789 + 0.83611878917564316394147324286578085396885208356242e-1 * t800 + 0.12876523046448265014289131379103307332106903038231e0 * t52 * t31 * t295 * t55 - 0.11037019754098512869390684039231406284663059747056e0 * t807 * t253 * t340 * t55 + 0.10604198846673805381417048105034922798259670954310e0 * t816 - 0.50631328524251801700246888250186209051365905137714e2 * t826 - 0.26510497116684513453542620262587306995649177385774e-1 * t833 + 0.23411326096918008590361250800241863911127858339748e1 * t841 + 0.93661128980942159930272349818429218252336444377380e-4 * t846 * t247 + 0.27592549385246282173476710098078515711657649367638e-1 * t852 * t341 * t853 - 0.14409904107548592782479233443873989685032538114864e1 * t860 * t341 * t863 + 0.22993791154371901811230591748398763093048041139699e-2 * t870 * t296 * t871
  t878 = 0.1e1 / t849 / t48
  t879 = t878 * t1
  t880 = t879 * t322
  t881 = t2 * t862
  t885 = t849 ** 2
  t886 = 0.1e1 / t885
  t887 = t886 * t40
  t888 = t887 * t252
  t890 = 0.1e1 / t861 / t54
  t891 = t890 * t29
  t895 = t111 ** 2
  t896 = 0.1e1 / t895
  t897 = t114 * t896
  t898 = t897 * t75
  t899 = t898 * t247
  t903 = t98 * t31 * t295 * t101
  t905 = t95 * t94
  t906 = 0.1e1 / t905
  t907 = t906 * t1
  t908 = t907 * t322
  t909 = t2 * t101
  t911 = t908 * t296 * t909
  t914 = t4 * t296 * t76
  t916 = t245 * t81
  t918 = t23 * t916 * t84
  t920 = t10 * t688
  t927 = t80 ** 2
  t928 = 0.1e1 / t927
  t929 = t12 * t928
  t930 = t690 * t84
  t934 = t84 * t696
  t941 = -t357 - 0.12424800000000000000000000000000000000000000000000e1 * t336 + 0.82832000000000000000000000000000000000000000000000e0 * t360 - 0.96637333333333333333333333333333333333333333333333e0 * t363
  t947 = (-0.7e1 / 0.27e2 * t914 - t918 / 0.3e1 - t23 * t920 * t690 / 0.2e1 + t23 * t683 * t696 / 0.4e1 - 0.3e1 / 0.2e1 * t23 * t929 * t930 + 0.3e1 / 0.2e1 * t23 * t689 * t934 - t23 * t82 * t941 / 0.4e1) * t40 * t42
  t948 = t947 * t91
  t950 = t879 * t3
  t954 = t44 * t652
  t959 = t61 * t643
  t960 = t959 * t30
  t964 = t730 * t251
  t986 = t66 * t657
  t992 = -0.11e2 / 0.216e3 * t636 - t640 / 0.24e2 - t960 * t31 * t10 * t645 + t964 * t253 * t256 * t35 / 0.3e1 - 0.2e1 / 0.3e1 * t731 * t31 * t245 * t35 + t731 * t31 * t10 * t652 / 0.2e1 + t324 * t325 * t19 / 0.432e3 - 0.2e1 / 0.3e1 * t62 * t336 + 0.4e1 / 0.9e1 * t736 * t342 - 0.14e2 / 0.27e2 * t63 * t345 - 0.6e1 * t986 * t659 + 0.6e1 * t741 * t664 - t67 * t671
  t993 = t992 * t70
  t996 = t745 * t70
  t1001 = t774 * t115
  t1002 = t1001 * t84
  t1004 = -0.51463943241244974223140119442407106017973350410227e-1 * t880 * t296 * t881 + 0.18429583437767336287475605998441200095133403022660e2 * t888 * t341 * t891 - 0.40375948798101559224001643004400895437705618747712e-4 * t899 - 0.12371565321119439611653222789207409931302949446695e0 * t903 - 0.22092080930570427877952183552156089163040981154812e-2 * t911 - 0.10363566666666666666666666666666666666666666666667e-1 * t948 + 0.11322067513073894329090826277329563323954137090250e1 * t950 * t296 * t862 + 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t954 + 0.22478670955426118383265363956423012380560746650571e-2 * t993 * t18 + 0.44957341910852236766530727912846024761121493301142e-2 * t996 * t35 + 0.22478670955426118383265363956423012380560746650571e-2 * t71 * t652 - 0.19380455423088748427520788642112429810098696998902e-2 * t1002
  t1005 = t116 * t696
  t1009 = t106 * t688
  t1010 = t1009 * t30
  t1014 = t759 * t251
  t1036 = t111 * t928
  t1042 = -0.11e2 / 0.216e3 * t914 - t918 / 0.24e2 - t1010 * t31 * t10 * t690 + t1014 * t253 * t256 * t84 / 0.3e1 - 0.2e1 / 0.3e1 * t760 * t31 * t245 * t84 + t760 * t31 * t10 * t696 / 0.2e1 + t324 * t325 * t76 / 0.432e3 - 0.2e1 / 0.3e1 * t107 * t336 + 0.4e1 / 0.9e1 * t765 * t342 - 0.14e2 / 0.27e2 * t108 * t345 - 0.6e1 * t1036 * t930 + 0.6e1 * t770 * t934 - t112 * t941
  t1043 = t1042 * t115
  t1044 = t1043 * t75
  t1046 = t439 * t75
  t1047 = t90 * t1046
  t1049 = t869 * t3
  t1065 = (t728 / 0.9e1 + t23 * t649 * t35 / 0.6e1 + t23 * t663 * t645 / 0.2e1 - t23 * t26 * t652 / 0.4e1) * t40 * t42
  t1066 = t330 * t18
  t1069 = t439 * t18
  t1072 = t44 * t696
  t1073 = t90 * t1072
  t1075 = t907 * t3
  t1077 = t1075 * t296 * t101
  t1079 = t794 * t3
  t1081 = t1079 * t296 * t797
  t1083 = t330 * t35
  t1086 = t44 * t35
  t1089 = t96 * t334
  t1091 = t1089 * t505 * t101
  t1093 = -0.96902277115443742137603943210562149050493484994510e-3 * t1005 - 0.96902277115443742137603943210562149050493484994510e-3 * t1044 + 0.23030148148148148148148148148148148148148148148149e-2 * t1047 - 0.50586340539618183984707301846477278804705690507337e-1 * t1049 * t296 * t55 + 0.34545222222222222222222222222222222222222222222222e-2 * t1065 * t1066 - 0.11515074074074074074074074074074074074074074074074e-2 * t43 * t1069 - 0.10363566666666666666666666666666666666666666666667e-1 * t1073 + 0.48602578047254941331494803814743396158690158540586e-1 * t1077 - 0.18394613361864149606712411343047178787314745838373e1 * t1081 + 0.34545222222222222222222222222222222222222222222222e-2 * t43 * t1083 + 0.10363566666666666666666666666666666666666666666667e-1 * t1065 * t1086 - 0.15906298270010708072125572157552384197389506431465e0 * t1091
  t1095 = t787 + t875 + t1004 + t1093
  t1096 = t1095 * t135
  t1099 = t182 * t601
  t1105 = t211 * t592
  t1108 = t211 * t179
  t1109 = t143 * t183
  t1112 = t182 * t147
  t1142 = t225 * (t461 * t501 / 0.3e1 + t436 * t462 / 0.9e1 + t436 * t473 / 0.3e1 + 0.12572604010298724324171900472329070791825696682747e0 * t443 * t246 * t386 + 0.25145208020597448648343800944658141583651393365495e0 * t522 * t253 * t256 * t386 - 0.50290416041194897296687601889316283167302786730989e0 * t528 * t31 * t245 * t386 - 0.63791733988157656503906862782236557702656491548799e1 * t466 * t246 * t396 + 0.41403379428206274608377249480129098139321562919141e-3 * t291 * t228 + 0.69005632380343791013962082466881830232202604865235e-4 * t533 * t27 + 0.41403379428206274608377249480129098139321562919141e-3 * t243 * t239)
  t1143 = t1142 * t218
  t1147 = s0 + 0.2e1 * s1 + s2
  t1148 = t1147 * t245
  t1150 = params.ftilde * (params.aa + params.bb)
  t1151 = params.malpha * t1
  t1152 = t31 * t12
  t1155 = params.mbeta * t40
  t1156 = t253 * t329
  t1159 = params.bb + t1151 * t1152 / 0.4e1 + t1155 * t1156 / 0.4e1
  t1160 = params.mgamma * t1
  t1163 = params.mdelta * t40
  t1166 = params.mbeta * t2
  t1169 = 0.1e1 + t1160 * t1152 / 0.4e1 + t1163 * t1156 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t1166 * t121
  t1170 = 0.1e1 / t1169
  t1172 = t1159 * t1170 + params.aa
  t1174 = jnp.sqrt(t1147)
  t1175 = 0.1e1 / t1172 * t1174
  t1176 = t7 ** (0.1e1 / 0.6e1)
  t1178 = 0.1e1 / t1176 / t7
  t1181 = jnp.exp(-t1150 * t1175 * t1178)
  t1182 = t1148 * t1181
  t1187 = -0.7e1 / 0.27e2 * t1151 * t362 - 0.20e2 / 0.27e2 * t1155 * t359
  t1193 = t1151 * t260 / 0.9e1 + 0.5e1 / 0.18e2 * t1155 * t257
  t1194 = t1169 ** 2
  t1195 = 0.1e1 / t1194
  t1196 = t1193 * t1195
  t1199 = t253 * t438
  t1204 = -t1160 * t32 / 0.12e2 - t1163 * t1199 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t1166 * t153
  t1211 = -t1151 * t32 / 0.12e2 - t1155 * t1199 / 0.6e1
  t1213 = 0.1e1 / t1194 / t1169
  t1214 = t1211 * t1213
  t1215 = t1204 ** 2
  t1218 = t1211 * t1195
  t1225 = t1160 * t260 / 0.9e1 + 0.5e1 / 0.18e2 * t1163 * t257 + 0.15000000000000000000000000000000000000000000000000e5 * t1166 * t160
  t1228 = t1194 ** 2
  t1229 = 0.1e1 / t1228
  t1230 = t1159 * t1229
  t1231 = t1215 * t1204
  t1234 = t1159 * t1213
  t1235 = t1204 * t1225
  t1238 = t1159 * t1195
  t1245 = -0.7e1 / 0.27e2 * t1160 * t362 - 0.20e2 / 0.27e2 * t1163 * t359 - 0.45000000000000000000000000000000000000000000000000e5 * t1166 * t183
  t1247 = t1187 * t1170 - 0.3e1 * t1196 * t1204 + 0.6e1 * t1214 * t1215 - 0.3e1 * t1218 * t1225 - 0.6e1 * t1230 * t1231 + 0.6e1 * t1234 * t1235 - t1238 * t1245
  t1248 = t125 ** 2
  t1249 = t1248 * f.p.zeta_threshold
  t1250 = f.my_piecewise3(t124, t1249, t564)
  t1251 = f.my_piecewise3(t131, t1249, t579)
  t1252 = t1250 + t1251
  t1253 = jnp.sqrt(t1252)
  t1254 = 0.1e1 / t1253
  t1256 = jnp.sqrt(0.2e1)
  t1257 = t1247 * t1254 * t1256
  t1260 = t1147 * t295
  t1261 = t1260 * t1181
  t1268 = t1193 * t1170 - 0.2e1 * t1218 * t1204 + 0.2e1 * t1234 * t1215 - t1238 * t1225
  t1270 = t1268 * t1254 * t1256
  t1273 = t1142 * t135
  t1276 = t622 * t135
  t1285 = t140 * (-0.12e2 * t141 * t183 + 0.32e2 * t142 * t147 - 0.20e2 * t181 * t601) * t547
  t1289 = 0.1e1 / t8 / t146
  t1290 = t1147 * t1289
  t1291 = t1290 * t1181
  t1293 = t1172 * t1254 * t1256
  t1297 = 0.1e1 / t8 / t145
  t1298 = t1147 * t1297
  t1299 = t1298 * t1181
  t1302 = t1211 * t1170 - t1238 * t1204
  t1304 = t1302 * t1254 * t1256
  t1307 = -0.384e3 * t219 * t148 + 0.4e1 * t1105 * t184 + 0.48e2 * t1108 * t1109 - 0.48e2 * t1108 * t1112 - t1143 * t548 / 0.2e1 + 0.4e1 * t1182 * t1257 - 0.28e2 * t1261 * t1270 - t1273 * t632 / 0.2e1 - t1276 * t1285 / 0.2e1 - 0.3640e4 / 0.27e2 * t1291 * t1293 + 0.280e3 / 0.3e1 * t1299 * t1304
  t1363 = 0.51817833333333333333333333333333333333333333333333e-2 * t1065 * t45 + 0.17272611111111111111111111111111111111111111111111e-2 * t43 * t1066 + 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t1086 + 0.13796274692623141086738355049039257855828824683819e-1 * t1049 * t246 * t55 + 0.27592549385246282173476710098078515711657649367639e-1 * t807 * t253 * t256 * t55 - 0.55185098770492564346953420196157031423315298735277e-1 * t52 * t31 * t245 * t55 - 0.30878365944746984533884071665444263610784010246137e0 * t950 * t246 * t862 + 0.22478670955426118383265363956423012380560746650571e-2 * t996 * t18 + 0.37464451592376863972108939927371687300934577750952e-3 * t784 * t27 + 0.22478670955426118383265363956423012380560746650571e-2 * t71 * t35 - 0.10363566666666666666666666666666666666666666666667e-1 * t702 * t91 - 0.34545222222222222222222222222222222222222222222223e-2 * t90 * t703 - 0.10363566666666666666666666666666666666666666666667e-1 * t90 * t709 - 0.13255248558342256726771310131293653497824588692887e-1 * t1075 * t246 * t101 - 0.26510497116684513453542620262587306995649177385775e-1 * t813 * t253 * t256 * t101 + 0.53020994233369026907085240525174613991298354771549e-1 * t98 * t31 * t245 * t101 + 0.50167127350538589836488394571946851238131125013746e0 * t1079 * t246 * t797 - 0.96902277115443742137603943210562149050493484994510e-3 * t1001 * t75 - 0.16150379519240623689600657201760358175082247499085e-3 * t788 * t27 - 0.96902277115443742137603943210562149050493484994510e-3 * t116 * t84
  t1364 = t1363 * t135
  t1369 = t211 * t135
  t1370 = t140 * t120
  t1371 = t1370 * t183
  t1374 = t182 * t605
  t1380 = t622 * t218
  t1382 = t563 * t218
  t1386 = t1252 ** 2
  t1388 = 0.1e1 / t1253 / t1386
  t1392 = f.my_piecewise3(t124, 0, 0.5e1 / 0.3e1 * t151 * t155)
  t1395 = f.my_piecewise3(t131, 0, 0.5e1 / 0.3e1 * t168 * t170)
  t1396 = t1392 + t1395
  t1397 = t1396 ** 2
  t1398 = t1256 * t1397
  t1399 = t1302 * t1388 * t1398
  t1403 = 0.1e1 / t1253 / t1252
  t1404 = t1268 * t1403
  t1405 = t1256 * t1396
  t1406 = t1404 * t1405
  t1409 = t1172 ** 2
  t1411 = t1150 / t1409
  t1412 = t1174 * t1178
  t1416 = 0.1e1 / t1176 / t144
  t1420 = t1411 * t1412 * t1302 + 0.7e1 / 0.6e1 * t1150 * t1175 * t1416
  t1421 = t1420 ** 2
  t1422 = t1148 * t1421
  t1423 = t1181 * t1302
  t1424 = t1254 * t1256
  t1425 = t1423 * t1424
  t1430 = t1150 / t1409 / t1172
  t1431 = t1302 ** 2
  t1435 = t1174 * t1416
  t1442 = 0.1e1 / t1176 / t159
  t1446 = -0.2e1 * t1430 * t1412 * t1431 - 0.7e1 / 0.3e1 * t1411 * t1435 * t1302 + t1411 * t1412 * t1268 - 0.91e2 / 0.36e2 * t1150 * t1175 * t1442
  t1447 = t1148 * t1446
  t1450 = t1421 * t1420
  t1451 = t1148 * t1450
  t1452 = t1181 * t1172
  t1453 = t1452 * t1424
  t1456 = t1298 * t1420
  t1461 = 0.1e1 / t1253 / t1386 / t1252
  t1464 = t1256 * t1397 * t1396
  t1465 = t1172 * t1461 * t1464
  t1468 = t1302 * t1403
  t1469 = t1468 * t1405
  t1472 = t1172 * t1388
  t1473 = t1472 * t1398
  t1476 = t1172 * t1403
  t1477 = 0.1e1 / t127
  t1483 = f.my_piecewise3(t124, 0, 0.10e2 / 0.9e1 * t1477 * t156 + 0.5e1 / 0.3e1 * t151 * t163)
  t1484 = 0.1e1 / t132
  t1490 = f.my_piecewise3(t131, 0, 0.10e2 / 0.9e1 * t1484 * t171 + 0.5e1 / 0.3e1 * t168 * t174)
  t1491 = t1483 + t1490
  t1492 = t1256 * t1491
  t1493 = t1476 * t1492
  t1496 = t1260 * t1421
  t1499 = 0.9e1 * t1182 * t1399 - 0.6e1 * t1182 * t1406 + 0.12e2 * t1422 * t1425 + 0.12e2 * t1447 * t1425 + 0.4e1 * t1451 * t1453 + 0.280e3 / 0.3e1 * t1456 * t1453 - 0.15e2 / 0.2e1 * t1182 * t1465 + 0.28e2 * t1261 * t1469 - 0.21e2 * t1261 * t1473 + 0.14e2 * t1261 * t1493 - 0.28e2 * t1496 * t1453
  t1502 = t1476 * t1405
  t1505 = t1260 * t1420
  t1508 = t1409 ** 2
  t1510 = t1150 / t1508
  t1511 = t1431 * t1302
  t1518 = t1302 * t1268
  t1522 = t1174 * t1442
  t1532 = 0.1e1 / t1176 / t145
  t1536 = 0.6e1 * t1510 * t1412 * t1511 + 0.7e1 * t1430 * t1435 * t1431 - 0.6e1 * t1430 * t1412 * t1518 + 0.91e2 / 0.12e2 * t1411 * t1522 * t1302 - 0.7e1 / 0.2e1 * t1411 * t1435 * t1268 + t1411 * t1412 * t1247 + 0.1729e4 / 0.216e3 * t1150 * t1175 * t1532
  t1537 = t1148 * t1536
  t1547 = t143 * t601
  t1558 = t1363 * t218
  t1563 = t1386 ** 2
  t1567 = t1397 ** 2
  t1579 = 0.29070683134633122641281182963168644715148045498353e-2 * t1001 * t696
  t1581 = 0.96902277115443742137603943210562149050493484994510e-3 * t116 * t941
  t1586 = 0.46822652193836017180722501600483727822255716679496e1 * t836 * t2 * t147 * t797 * t250
  t1587 = t2 * t147
  t1590 = 0.12725038616008566457700457726041907357911605145172e1 * t1089 * t1587 * t101
  t1595 = 0.10126265704850360340049377650037241810273181027543e3 * t819 * t2 * t147 * t823 * t250
  t1600 = 0.53020994233369026907085240525174613991298354771548e-1 * t828 * t2 * t147 * t101 * t250
  t1615 = t6 * t1297
  t1617 = t4 * t1615 * t19
  t1621 = t23 * t295 * t25 * t35
  t1625 = t23 * t245 * t643 * t645
  t1628 = t23 * t638 * t652
  t1641 = 0.1e1 / t656 / t18
  t1643 = t645 ** 2
  t1647 = t645 * t652
  t1651 = t652 ** 2
  t1655 = t35 * t671
  t1659 = t4 * t1615
  t1660 = 0.70e2 / 0.81e2 * t1659
  t1664 = 0.1e1 / t16 / t2 / t121 / 0.48e2
  t1665 = t1664 * t2
  t1667 = t1665 * t1289 * t23
  t1669 = t335 * t147
  t1672 = 0.1e1 / t254 / t145
  t1673 = t253 * t1672
  t1674 = t251 * t1673
  t1676 = t31 * t1297
  t1677 = t30 * t1676
  t1679 = t1660 - 0.19612277777777777777777777777777777777777777777777e1 * t1667 + 0.18827786666666666666666666666666666666666666666666e2 * t1669 - 0.69732543209876543209876543209876543209876543209875e1 * t1674 + 0.61015975308641975308641975308641975308641975308640e1 * t1677
  t1683 = 0.70e2 / 0.81e2 * t1617 + 0.28e2 / 0.27e2 * t1621 + 0.4e1 / 0.3e1 * t1625 - 0.2e1 / 0.3e1 * t1628 + 0.2e1 * t23 * t10 * t657 * t659 - 0.2e1 * t23 * t644 * t664 + t23 * t649 * t671 / 0.3e1 + 0.6e1 * t23 * t12 * t1641 * t1643 - 0.9e1 * t23 * t658 * t1647 + 0.3e1 / 0.2e1 * t23 * t663 * t1651 + 0.2e1 * t23 * t663 * t1655 - t23 * t26 * t1679 / 0.4e1
  t1688 = 0.15545350000000000000000000000000000000000000000000e-1 * t1065 * t954 - t1579 - t1581 + t1586 + t1590 - t1595 - t1600 + 0.15545350000000000000000000000000000000000000000000e-1 * t677 * t1086 + 0.21269256817794009175388297367268855861069438054221e0 * t868 * t1297 * t55 * t23 - 0.47604147498151601156404610484226573066625349129460e1 * t878 * t1297 * t862 * t23 + 0.10363566666666666666666666666666666666666666666667e-1 * t1065 * t1083 + 0.51817833333333333333333333333333333333333333333333e-2 * t1683 * t40 * t42 * t45
  t1700 = 0.12112784639430467767200492901320268631311685624314e-3 * t897 * t84 * t247
  t1701 = t5 * t1672
  t1704 = 0.37129640917784654580181051383469886637668330434323e3 * t821 * t1701 * t824
  t1707 = 0.16200859349084980443831601271581132052896719513529e-1 * t908 * t1615 * t909
  t1710 = 0.61315377872880498689041371143490595957715819461244e0 * t795 * t1615 * t798
  t1716 = t42 * t5
  t1719 = 0.12657832131062950425061722062546552262841476284429e3 / t818 / t94 * t2 * t1672 * t823 * t40 * t1716
  t1724 = t796 ** 2
  t1729 = 0.19162434373246948642083122762742588170998040494372e4 / t818 / t905 * t2 * t1672 / t1724 * t40 * t1716
  t1735 = 0.17673664744456342302361746841724871330432784923849e-1 * t793 * t2 * t1672 * t101 * t40 * t1716
  t1743 = 0.26755801253620581246127143771704987327003266673998e1 / t791 / t905 * t2 * t1672 * t797 * t40 * t1716
  t1746 = 0.19441031218901976532597921525897358463476063416234e0 * t830 * t1701 * t831
  t1749 = 0.17168305804406539632931583920177366868160429449148e2 * t838 * t1701 * t839
  t1750 = -0.34545222222222222222222222222222222222222222222222e-2 * t43 * t439 * t35 + 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t44 * t671 + 0.51817833333333333333333333333333333333333333333333e-2 * t43 * t330 * t652 - t1700 + t1704 + t1707 - t1710 - t1719 + t1729 - t1735 + t1743 + t1746 - t1749
  t1755 = 0.47129772651883579472964658244599656881154093130267e0 * t813 * t253 * t1672 * t101
  t1759 = 0.41238551070398132038844075964024699771009831488983e0 * t98 * t31 * t1297 * t101
  t1763 = 0.12112784639430467767200492901320268631311685624314e-3 * t774 * t896 * t75 * t247
  t1765 = 0.14804514559303905048800602434946994993825393540828e-3 * t898 * t345
  t1770 = t1672 * t2
  t1773 = 0.84385547540419669500411480416977015085609841896189e1 * t820 * t1716 * t1770 * t824
  t1780 = t253 * t340 * t29
  t1782 = 0.53834598397468745632002190672534527250274158330283e-4 * t114 / t895 / t106 * t75 * t40 * t1780
  t1786 = 0.44184161861140855755904367104312178326081962309624e-2 * t829 * t1716 * t1770 * t831
  t1788 = t2 * t1289
  t1793 = 0.13255248558342256726771310131293653497824588692887e0 * t96 * t1664 * t1788 * t101 * t1 * t31
  t1797 = t322 * t6 * t325
  t1799 = 0.67293247996835932040002738340668159062842697912856e-5 * t897 * t75 * t1 * t1797
  t1802 = 0.32300759038481247379201314403520716350164494998170e-3 * t775 * t780 * t278
  t1805 = 0.96902277115443742137603943210562149050493484994510e-3 * t775 * t754 * t27
  t1806 = -t1755 + t1759 - t1763 + t1765 + 0.14985780636950745588843575970948674920373831100381e-2 * t718 * t18 * t336 - t1773 - t1782 - t1786 - t1793 - t1799 - t1802 - t1805
  t1810 = 0.48451138557721871068801971605281074525246742497255e-3 * t753 * t696 * t29 * t27
  t1814 = 0.32300759038481247379201314403520716350164494998170e-3 * t753 * t84 * t250 * t278
  t1818 = 0.48451138557721871068801971605281074525246742497255e-3 * t1042 * t752 * t776 * t27
  t1822 = 0.39018876828196680983935418000403106518546430566246e0 * t837 * t1716 * t1770 * t839
  t1824 = 0.43067678717974996505601752538027621800219326664227e-3 * t781 * t342
  t1826 = 0.50245625170970829256535377961032225433589214441597e-3 * t788 * t345
  t1828 = 0.64601518076962494758402628807041432700328989996340e-3 * t755 * t247
  t1830 = 0.64601518076962494758402628807041432700328989996340e-3 * t777 * t247
  t1846 = -t1810 - t1814 - t1818 + t1822 + t1824 - t1826 + t1828 + t1830 - 0.34342413959678791974433194933424046692523362938372e-3 * t846 * t345 + 0.28098338694282647979081704945528765475700933313214e-3 * t845 * t35 * t247 + 0.10567263012202301373818104525507592435690527950900e2 * t860 * t1701 * t863 - 0.13515027854362713277482111065523546736431162216617e3 * t888 * t1701 * t891 + 0.28098338694282647979081704945528765475700933313214e-3 * t745 * t844 * t18 * t247
  t1856 = t861 ** 2
  t1899 = t4 * t1615 * t76
  t1903 = t23 * t295 * t81 * t84
  t1907 = t23 * t245 * t688 * t690
  t1910 = t23 * t916 * t696
  t1923 = 0.1e1 / t927 / t75
  t1925 = t690 ** 2
  t1929 = t690 * t696
  t1933 = t696 ** 2
  t1937 = t84 * t941
  t1945 = t1660 - 0.10354000000000000000000000000000000000000000000000e1 * t1667 + 0.99398400000000000000000000000000000000000000000000e1 * t1669 - 0.36814222222222222222222222222222222222222222222222e1 * t1674 + 0.32212444444444444444444444444444444444444444444444e1 * t1677
  t1949 = 0.70e2 / 0.81e2 * t1899 + 0.28e2 / 0.27e2 * t1903 + 0.4e1 / 0.3e1 * t1907 - 0.2e1 / 0.3e1 * t1910 + 0.2e1 * t23 * t10 * t928 * t930 - 0.2e1 * t23 * t920 * t934 + t23 * t683 * t941 / 0.3e1 + 0.6e1 * t23 * t12 * t1923 * t1925 - 0.9e1 * t23 * t929 * t1929 + 0.3e1 / 0.2e1 * t23 * t689 * t1933 + 0.2e1 * t23 * t689 * t1937 - t23 * t82 * t1945 / 0.4e1
  t1953 = 0.10363566666666666666666666666666666666666666666667e-1 * t1949 * t40 * t42 * t91
  t1955 = 0.31090700000000000000000000000000000000000000000001e-1 * t947 * t709
  t1957 = 0.20727133333333333333333333333333333333333333333334e-1 * t702 * t706
  t1958 = -0.20234536215847273593882920738590911521882276202934e0 * t852 * t1701 * t853 - 0.41248484411876216403621151040619215743173669759529e3 / t885 / t867 * t2 * t1672 / t1856 * t40 * t1716 + 0.18395032923497521448984473398719010474438432911759e-1 * t878 * t2 * t1672 * t55 * t40 * t1716 - 0.16468461837198391751404838221570273925751472131273e1 / t849 / t867 * t2 * t1672 * t862 * t40 * t1716 + 0.46073958594418340718689014996103000237833507556650e2 / t885 / t48 * t2 * t1672 * t890 * t40 * t1716 + 0.49053421129326723863958595729917361265169154431359e0 * t807 * t253 * t1672 * t55 - 0.16862113513206061328235767282159092934901896835780e-1 * t870 * t1615 * t871 + 0.37740225043579647763636087591098544413180456967501e0 * t880 * t1615 * t881 - 0.42921743488160883380963771263677691107023010127437e0 * t52 * t31 * t1297 * t55 - t1953 - t1955 - t1957
  t1961 = 0.38383580246913580246913580246913580246913580246915e-2 * t90 * t277 * t75
  t1963 = 0.69090444444444444444444444444444444444444444444446e-2 * t702 * t1046
  t1966 = 0.69090444444444444444444444444444444444444444444446e-2 * t90 * t439 * t84
  t1968 = 0.10363566666666666666666666666666666666666666666667e-1 * t947 * t703
  t1971 = 0.10363566666666666666666666666666666666666666666667e-1 * t90 * t44 * t941
  t1973 = 0.31090700000000000000000000000000000000000000000001e-1 * t702 * t1072
  t1976 = 0.10363566666666666666666666666666666666666666666667e-1 * t90 * t330 * t696
  t1979 = 0.64601518076962494758402628807041432700328989996342e-3 * t753 * t75 * t336
  t1983 = 0.20435174860777645787105769785744382475812907568201e0 * t906 * t1297 * t101 * t23
  t1987 = 0.77340987998746992664586274965084728992118817729523e1 * t793 * t1297 * t797 * t23
  t1995 = -t1961 + t1963 + t1966 - t1968 - t1971 - t1973 - t1976 - t1979 - t1983 + t1987 + 0.51817833333333333333333333333333333333333333333333e-2 * t677 * t1066 - 0.34545222222222222222222222222222222222222222222222e-2 * t1065 * t1069 + 0.19191790123456790123456790123456790123456790123457e-2 * t43 * t277 * t18
  t2029 = t1289 * t1 * t31
  t2061 = 0.8e1 * t770 * t1937 + 0.16e2 / 0.3e1 * t107 * t1669 - 0.4e1 / 0.3e1 * t760 * t31 * t245 * t696 + 0.2e1 / 0.3e1 * t760 * t31 * t10 * t941 - 0.5e1 / 0.9e1 * t107 * t1665 * t2029 - 0.4e1 / 0.3e1 * t1009 * t251 * t253 * t256 * t690 + 0.2e1 / 0.3e1 * t1014 * t253 * t256 * t696 - 0.16e2 / 0.9e1 * t1014 * t253 * t340 * t84 + 0.56e2 / 0.27e2 * t760 * t31 * t295 * t84 + 0.4e1 * t106 * t928 * t30 * t31 * t10 * t930 + 0.8e1 / 0.3e1 * t1010 * t31 * t245 * t690 - 0.36e2 * t1036 * t1929
  t2067 = t276 * t1701
  t2077 = t1297 * t2
  t2093 = 0.185e3 / 0.864e3 * t1899 - 0.4e1 * t1010 * t31 * t761 * t696 - 0.160e3 / 0.81e2 * t765 * t2067 + 0.140e3 / 0.81e2 * t108 * t1659 - t324 * t325 * t81 * t84 / 0.108e3 - t1910 / 0.12e2 - 0.11e2 / 0.648e3 * t324 * t2077 * t76 + 0.8e1 / 0.3e1 * t759 * t334 * t505 * t84 + 0.11e2 / 0.54e2 * t1903 + t1907 / 0.6e1 - t112 * t1945 + 0.24e2 * t111 * t1923 * t1925 + 0.6e1 * t770 * t1933
  t2097 = 0.96902277115443742137603943210562149050493484994510e-3 * (t2061 + t2093) * t115 * t75
  t2125 = 0.36859166875534672574951211996882400190266806045320e2 * t886 * t2 * t147 * t890 * t250 + 0.55185098770492564346953420196157031423315298735276e-1 * t850 * t2 * t147 * t55 * t250 - 0.28819808215097185564958466887747979370065076229728e1 * t858 * t2 * t147 * t862 * t250 - 0.13244423704918215443268820847077687541595671696467e1 * t712 * t1587 * t55 - t2097 + 0.13796274692623141086738355049039257855828824683819e0 * t50 * t1664 * t1788 * t55 * t1 * t31 - 0.14985780636950745588843575970948674920373831100381e-2 * t720 * t247 - 0.99905204246338303925623839806324499469158874002539e-3 * t724 * t342 + 0.11239335477713059191632681978211506190280373325286e-2 * t718 * t652 * t29 * t27 + 0.74928903184753727944217879854743374601869155501904e-3 * t718 * t35 * t250 * t278 + 0.11655607162072802124656114644071191604735201966963e-2 * t784 * t345 + 0.12488150530792287990702979975790562433644859250317e-3 * t69 / t843 / t61 * t18 * t40 * t1780
  t2155 = 0.29070683134633122641281182963168644715148045498353e-2 * t1043 * t84
  t2194 = -0.36e2 * t986 * t1647 + 0.8e1 * t741 * t1655 + t1625 / 0.6e1 + 0.11e2 / 0.54e2 * t1621 + 0.8e1 / 0.3e1 * t730 * t334 * t505 * t35 - t1628 / 0.12e2 - 0.4e1 / 0.3e1 * t959 * t251 * t253 * t256 * t645 + 0.2e1 / 0.3e1 * t964 * t253 * t256 * t652 - 0.4e1 / 0.3e1 * t731 * t31 * t245 * t652 + 0.2e1 / 0.3e1 * t731 * t31 * t10 * t671 + 0.4e1 * t61 * t657 * t30 * t31 * t10 * t659 + 0.8e1 / 0.3e1 * t960 * t31 * t245 * t645
  t2230 = -0.16e2 / 0.9e1 * t964 * t253 * t340 * t35 + 0.56e2 / 0.27e2 * t731 * t31 * t295 * t35 - 0.5e1 / 0.9e1 * t62 * t1665 * t2029 - 0.11e2 / 0.648e3 * t324 * t2077 * t19 + 0.185e3 / 0.864e3 * t1617 + 0.16e2 / 0.3e1 * t62 * t1669 - t324 * t325 * t25 * t35 / 0.108e3 - 0.160e3 / 0.81e2 * t736 * t2067 + 0.140e3 / 0.81e2 * t63 * t1659 - 0.4e1 * t960 * t31 * t732 * t652 - t67 * t1679 + 0.6e1 * t741 * t1651 + 0.24e2 * t66 * t1641 * t1643
  t2241 = 0.22478670955426118383265363956423012380560746650571e-2 * t746 * t719 * t27 + 0.74928903184753727944217879854743374601869155501904e-3 * t746 * t723 * t278 + 0.45987582308743803622461183496797526186096082279398e-2 * t851 * t1716 * t1770 * t853 - 0.24016506845914321304132055739789982808387563524773e0 * t859 * t1716 * t1770 * t863 + 0.30715972396278893812459343330735333491889005037766e1 * t887 * t1716 * t1770 * t891 - 0.14985780636950745588843575970948674920373831100381e-2 * t748 * t247 + 0.11239335477713059191632681978211506190280373325286e-2 * t992 * t717 * t747 * t27 + 0.15610188163490359988378724969738203042056074062897e-4 * t845 * t18 * t1 * t1797 - t2155 + 0.22478670955426118383265363956423012380560746650571e-2 * (t2194 + t2230) * t70 * t18 + 0.22478670955426118383265363956423012380560746650571e-2 * t71 * t671 + 0.67436012866278355149796091869269037141682239951713e-2 * t996 * t652 + 0.67436012866278355149796091869269037141682239951713e-2 * t993 * t35
  t2253 = t1579 + t1581 - t1586 - t1590 + t1595 + t1600 + (t1688 + t1750 + t1806 + t1846 + t1958 + t1995 + t2125 + t2241) * t135 * t184 - t1276 * t610 / 0.6e1 - t593 * t632 / 0.6e1 - t626 * t1285 / 0.4e1 + t1700
  t2269 = t220 * t147
  t2274 = -t1759 - 0.140e3 / 0.3e1 * t1299 * t1469 + 0.280e3 / 0.3e1 * t1456 * t1425 + 0.1820e4 / 0.27e2 * t1291 * t1502 - 0.3640e4 / 0.27e2 * t1290 * t1420 * t1453 + t1763 - t1765 - 0.192e3 * t1364 * t148 - 0.48e2 * t180 * t1112 - 0.576e3 * t219 * t2269 + 0.960e3 * t219 * t1547
  t2280 = t145 ** 2
  t2281 = 0.1e1 / t2280
  t2292 = t1388 * t1256
  t2294 = t2292 * t1396 * t1491
  t2297 = t1148 * t1452
  t2298 = 0.1e1 / t128
  t2301 = t1477 * t155
  t2307 = f.my_piecewise3(t124, 0, -0.10e2 / 0.27e2 * t2298 * t566 + 0.10e2 / 0.3e1 * t2301 * t163 + 0.5e1 / 0.3e1 * t151 * t574)
  t2308 = 0.1e1 / t133
  t2311 = t1484 * t170
  t2317 = f.my_piecewise3(t131, 0, -0.10e2 / 0.27e2 * t2308 * t581 + 0.10e2 / 0.3e1 * t2311 * t174 + 0.5e1 / 0.3e1 * t168 * t587)
  t2318 = t2307 + t2317
  t2327 = t1446 * t1181
  t2328 = t1148 * t2327
  t2331 = t1420 * t1181
  t2332 = t1148 * t2331
  t2343 = t1446 * t1420
  t2344 = t1148 * t2343
  t2347 = t1260 * t2331
  t2354 = t1468 * t1492
  t2357 = t1256 * t2318
  t2358 = t1476 * t2357
  t2370 = 0.14e2 * t1260 * t2327 * t1502 + 0.4e1 * t1148 * t1536 * t1420 * t1453 + 0.12e2 * t2344 * t1425 + 0.28e2 * t2347 * t1469 + 0.14e2 * t2347 * t1493 - 0.3e1 * t2328 * t1493 - 0.6e1 * t2332 * t2354 - 0.2e1 * t2332 * t2358 - 0.16e2 * t1096 * t1112 + 0.120e3 * t1108 * t1099 - 0.45e2 / 0.4e1 * t2297 * t1461 * t1256 * t1397 * t1491
  t2376 = t1421 * t1181
  t2377 = t1148 * t2376
  t2409 = -0.21e2 * t1260 * t1452 * t2294 + 0.14e2 * t1260 * t2376 * t1502 - 0.3e1 * t2377 * t1493 + t1773 + t1782 + t1786 + t1793 + t1799 + t1802 + t1805 + t1810
  t2420 = t1953 + t1955 + t1957 + t1961 - t1963 - t1966 + t1968 + t1971 + t1973 + t1976 + t1979
  t2435 = t1431 ** 2
  t2452 = t1268 ** 2
  t2494 = t1215 ** 2
  t2500 = t1225 ** 2
  t2514 = (0.70e2 / 0.81e2 * t1151 * t1676 + 0.220e3 / 0.81e2 * t1155 * t1673) * t1170 - 0.4e1 * t1187 * t1195 * t1204 + 0.12e2 * t1193 * t1213 * t1215 - 0.6e1 * t1196 * t1225 - 0.24e2 * t1211 * t1229 * t1231 + 0.24e2 * t1214 * t1235 - 0.4e1 * t1218 * t1245 + 0.24e2 * t1159 / t1228 / t1169 * t2494 - 0.36e2 * t1230 * t1215 * t1225 + 0.6e1 * t1234 * t2500 + 0.8e1 * t1234 * t1204 * t1245 - t1238 * (0.70e2 / 0.81e2 * t1160 * t1676 + 0.220e3 / 0.81e2 * t1163 * t1673 + 0.18000000000000000000000000000000000000000000000000e6 * t1166 * t147)
  t2522 = -0.24e2 * t1150 / t1508 / t1172 * t1412 * t2435 - 0.28e2 * t1510 * t1435 * t1511 + 0.36e2 * t1510 * t1412 * t1431 * t1268 - 0.91e2 / 0.3e1 * t1430 * t1522 * t1431 + 0.28e2 * t1430 * t1435 * t1518 - 0.6e1 * t1430 * t1412 * t2452 - 0.8e1 * t1430 * t1412 * t1302 * t1247 - 0.1729e4 / 0.54e2 * t1411 * t1174 * t1532 * t1302 + 0.91e2 / 0.6e1 * t1411 * t1522 * t1268 - 0.14e2 / 0.3e1 * t1411 * t1435 * t1247 + t1411 * t1412 * t2514 - 0.43225e5 / 0.1296e4 * t1150 * t1175 / t1176 / t146
  t2525 = t123 ** 2
  t2528 = t156 ** 2
  t2534 = t163 ** 2
  t2539 = t120 * t147
  t2541 = -0.24e2 * t183 + 0.24e2 * t2539
  t2545 = f.my_piecewise3(t124, 0, 0.40e2 / 0.81e2 / t127 / t2525 * t2528 - 0.20e2 / 0.9e1 * t2298 * t156 * t163 + 0.10e2 / 0.3e1 * t1477 * t2534 + 0.40e2 / 0.9e1 * t2301 * t574 + 0.5e1 / 0.3e1 * t151 * t2541)
  t2546 = t130 ** 2
  t2549 = t171 ** 2
  t2555 = t174 ** 2
  t2560 = -t2541
  t2564 = f.my_piecewise3(t131, 0, 0.40e2 / 0.81e2 / t132 / t2546 * t2549 - 0.20e2 / 0.9e1 * t2308 * t171 * t174 + 0.10e2 / 0.3e1 * t1484 * t2555 + 0.40e2 / 0.9e1 * t2311 * t587 + 0.5e1 / 0.3e1 * t168 * t2560)
  t2581 = t1421 ** 2
  t2610 = -0.28e2 / 0.3e1 * t1260 * t1450 * t1453 + t1148 * t2581 * t1453 + 0.140e3 / 0.3e1 * t1298 * t1421 * t1453 + 0.9e1 * t2332 * t1472 * t1492 * t1396 - 0.6e1 * t2344 * t1452 * t1403 * t1256 * t1396 + 0.120e3 * t1364 * t1099 - 0.192e3 * t1108 * t148 + 0.140e3 / 0.3e1 * t1299 * t1270 + t1182 * t2514 * t1254 * t1256 - t543 * t632 / 0.6e1 + 0.140e3 / 0.3e1 * t1298 * t1446 * t1453
  t2614 = t1181 * t1268 * t1424
  t2667 = f.my_piecewise3(t124, 0, 0.40e2 / 0.81e2 / t151 / t2525 * t2528 - 0.16e2 / 0.9e1 * t565 * t156 * t163 + 0.4e1 / 0.3e1 * t152 * t2534 + 0.16e2 / 0.9e1 * t569 * t574 + 0.4e1 / 0.3e1 * t127 * t2541)
  t2682 = f.my_piecewise3(t131, 0, 0.40e2 / 0.81e2 / t168 / t2546 * t2549 - 0.16e2 / 0.9e1 * t580 * t171 * t174 + 0.4e1 / 0.3e1 * t169 * t2555 + 0.16e2 / 0.9e1 * t584 * t587 + 0.4e1 / 0.3e1 * t132 * t2560)
  t2683 = t2667 + t2682
  t2691 = t119 * t218
  t2696 = -0.576e3 * t136 * t2269 - 0.48e2 * t1558 * t1112 + 0.6e1 * t1363 * t179 * t184 - t623 * t632 / 0.2e1 - t1142 * t179 * t548 / 0.4e1 + 0.48e2 * t180 * t1109 + t211 * t2683 * t184 + 0.4e1 * t1095 * t218 * t184 + 0.96e2 * t219 * t1371 + 0.144e3 * t2691 * t221 - 0.480e3 * t219 * t1374
  t2735 = t436 * t44 * t365 / 0.3e1 + 0.27602252952137516405584832986752732092881041946094e-3 * t516 * t228 * t336 + 0.10e2 / 0.81e2 * t436 * t277 * t228 + 0.19382764515877199999765013228173984137397949052569e1 * t443 * t1615 * t386 - 0.98345589898409720443523080122614693124928757804400e2 * t466 * t1615 * t396 + t436 * t330 * t263 / 0.3e1 + t500 * t473 + t461 * t470 + 0.14385370752267644704638799272094205307643519225011e3 * t419 * t1716 * t1770 * t423 - 0.27602252952137516405584832986752732092881041946094e-3 * t513 * t247 + 0.21468418962773623871010425656363236072240810402517e-3 * t533 * t345 - 0.27602252952137516405584832986752732092881041946094e-3 * t518 * t247
  t2782 = t4 * t1615 * t229
  t2786 = t23 * t295 * t236 * t239
  t2790 = t23 * t245 * t284 * t286
  t2793 = t23 * t300 * t263
  t2806 = 0.1e1 / t348 / t228
  t2808 = t286 ** 2
  t2812 = t286 * t263
  t2816 = t263 ** 2
  t2820 = t239 * t365
  t2828 = t1660 - 0.31418611111111111111111111111111111111111111111112e0 * t1667 + 0.30161866666666666666666666666666666666666666666668e1 * t1669 - 0.11171061728395061728395061728395061728395061728396e1 * t1674 + 0.97746790123456790123456790123456790123456790123460e0 * t1677
  t2832 = 0.70e2 / 0.81e2 * t2782 + 0.28e2 / 0.27e2 * t2786 + 0.4e1 / 0.3e1 * t2790 - 0.2e1 / 0.3e1 * t2793 + 0.2e1 * t23 * t10 * t349 * t351 - 0.2e1 * t23 * t481 * t354 + t23 * t448 * t365 / 0.3e1 + 0.6e1 * t23 * t12 * t2806 * t2808 - 0.9e1 * t23 * t488 * t2812 + 0.3e1 / 0.2e1 * t23 * t452 * t2816 + 0.2e1 * t23 * t452 * t2820 - t23 * t430 * t2828 / 0.4e1
  t2840 = 0.20701689714103137304188624740064549069660781459570e-3 * t367 * t510 * t512 * t27 + 0.23001877460114597004654027488960610077400868288412e-4 * t241 / t371 / t226 * t228 * t40 * t1780 + 0.41403379428206274608377249480129098139321562919141e-3 * t511 * t517 * t27 + 0.20701689714103137304188624740064549069660781459570e-3 * t516 * t263 * t29 * t27 + 0.28752346825143246255817534361200762596751085360514e-5 * t373 * t228 * t1 * t1797 + 0.13801126476068758202792416493376366046440520973047e-3 * t516 * t239 * t250 * t278 - 0.18401501968091677603723221991168488061920694630729e-3 * t537 * t342 + 0.13801126476068758202792416493376366046440520973047e-3 * t511 * t536 * t278 + 0.12572604010298724324171900472329070791825696682747e1 * t383 * t1664 * t1788 * t386 * t1 * t31 + 0.41908680034329081080573001574430235972752322275824e-1 * t381 * t1716 * t1770 * t387 - 0.49615793101900399503038671052850655990955048982400e1 * t393 * t1716 * t1770 * t397 + t2832 * t40 * t42 * t501 / 0.3e1 - 0.2e1 / 0.9e1 * t436 * t439 * t239
  t2878 = t395 ** 2
  t2891 = -0.2e1 / 0.9e1 * t461 * t440 + 0.2e1 / 0.3e1 * t461 * t476 + t500 * t462 / 0.3e1 + 0.50290416041194897296687601889316283167302786730988e0 * t380 * t2 * t147 * t386 * t250 - 0.12069699849886775351205024453435907960152668815438e2 * t504 * t1587 * t386 + 0.17262444902721173645566559126513046369172223070013e4 * t418 * t2 * t147 * t422 * t250 - 0.59538951722280479403646405263420787189146058778880e2 * t392 * t2 * t147 * t396 * t250 + 0.44702592036617686485944535012725585037602477094213e1 * t522 * t253 * t1672 * t386 - 0.39114768032040475675201468136134886907902167457437e1 * t528 * t31 * t1297 * t386 - 0.43793683962271420729973795871593892966464398384137e5 / t417 / t401 * t2 * t1672 / t2878 * t40 * t1716 + 0.51754224285257843260471561850161372674151953648927e-4 * t290 * t372 * t228 * t247 + 0.51754224285257843260471561850161372674151953648927e-4 * t373 * t239 * t247
  t2979 = 0.8e1 / 0.3e1 * t269 * t334 * t505 * t239 - 0.11e2 / 0.648e3 * t324 * t2077 * t229 + 0.4e1 * t226 * t349 * t30 * t31 * t10 * t351 + 0.8e1 / 0.3e1 * t305 * t31 * t245 * t286 - 0.16e2 / 0.9e1 * t309 * t253 * t340 * t239 + 0.56e2 / 0.27e2 * t270 * t31 * t295 * t239 + 0.2e1 / 0.3e1 * t270 * t31 * t10 * t365 - 0.5e1 / 0.9e1 * t230 * t1665 * t2029 - 0.4e1 / 0.3e1 * t304 * t251 * t253 * t256 * t286 + 0.2e1 / 0.3e1 * t309 * t253 * t256 * t263 - 0.4e1 / 0.3e1 * t270 * t31 * t245 * t263 + 0.11e2 / 0.54e2 * t2786
  t3007 = t2790 / 0.6e1 - t2793 / 0.12e2 - 0.160e3 / 0.81e2 * t275 * t2067 + 0.140e3 / 0.81e2 * t231 * t1659 - t324 * t325 * t236 * t239 / 0.108e3 + 0.16e2 / 0.3e1 * t230 * t1669 + 0.8e1 * t285 * t2820 - 0.36e2 * t350 * t2812 + 0.6e1 * t285 * t2816 + 0.24e2 * t234 * t2806 * t2808 - t237 * t2828 - 0.4e1 * t305 * t31 * t271 * t263 + 0.185e3 / 0.864e3 * t2782
  t3016 = 0.16763472013731632432229200629772094389100928910329e0 * t410 * t2 * t1672 * t386 * t40 * t1716 - 0.34022258127017416802083660150526164108083462159360e2 / t379 / t401 * t2 * t1672 * t396 * t40 * t1716 + 0.21578056128401467056958198908141307961465278837517e4 / t417 / t377 * t2 * t1672 * t422 * t40 * t1716 + 0.21830948964836175781337015263254288636020221552256e3 * t394 * t1701 * t397 - 0.15366516012587329729543433910624419856675851501136e0 * t404 * t1615 * t405 + 0.77967674874414913504775054511622459414357934115200e1 * t412 * t1615 * t413 - 0.63295631309977636700410716797214503353631484590049e4 * t420 * t1701 * t423 - 0.63255163015315141762798575594641677712852387793133e-4 * t374 * t345 - 0.18439819215104795675452120692749303828011021801362e1 * t382 * t1701 * t387 + 0.12421013828461882382513174844038729441796468875742e-2 * t368 * t239 + 0.41403379428206274608377249480129098139321562919141e-3 * (t2979 + t3007) * t242 * t228 + 0.12421013828461882382513174844038729441796468875742e-2 * t291 * t263 + 0.41403379428206274608377249480129098139321562919141e-3 * t243 * t365
  t3058 = t1148 * t1420
  t3063 = t1260 * t1446
  t3068 = t1446 ** 2
  t3074 = t1491 ** 2
  t3081 = -0.3640e4 / 0.27e2 * t1291 * t1304 - 0.2e1 * t1182 * t1468 * t2357 + 0.4e1 * t3058 * t1181 * t1247 * t1424 - 0.28e2 * t3063 * t1425 + 0.6e1 * t1447 * t2614 + 0.3e1 * t1148 * t3068 * t1453 + 0.4e1 * t1537 * t1425 + 0.9e1 / 0.4e1 * t1182 * t1472 * t1256 * t3074 + t2097 + t2155 + 0.96e2 * t136 * t1371
  t3106 = -0.33444751567025726557658929714631234158754083342496e0 * t800 - 0.42416795386695221525668192420139691193038683817240e0 * t816 + 0.20252531409700720680098755300074483620546362055085e3 * t826 + 0.10604198846673805381417048105034922798259670954310e0 * t833 - 0.93645304387672034361445003200967455644511433358993e1 * t841 + 0.16150379519240623689600657201760358175082247499085e-3 * t899 + 0.49486261284477758446612891156829639725211797786780e0 * t903 + 0.88368323722281711511808734208624356652163924619249e-2 * t911 - 0.28e2 * t3063 * t1453 + 0.12e2 * t3058 * t2614 - 0.2e1 * t1182 * t2358
  t3122 = -0.6e1 * t1182 * t2354 + 0.41454266666666666666666666666666666666666666666668e-1 * t948 + 0.77521821692354993710083154568449719240394787995608e-2 * t1002 + 0.38760910846177496855041577284224859620197393997804e-2 * t1005 + 0.38760910846177496855041577284224859620197393997804e-2 * t1044 - 0.92120592592592592592592592592592592592592592592596e-2 * t1047 + 0.41454266666666666666666666666666666666666666666668e-1 * t1073 - 0.19441031218901976532597921525897358463476063416235e0 * t1077 + 0.73578453447456598426849645372188715149258983353495e1 * t1081 + 0.28e2 * t2347 * t1502 - 0.6e1 * t2332 * t1493
  t3144 = 0.9e1 * t2297 * t2294 - 0.6e1 * t2328 * t1502 - 0.12e2 * t2332 * t1469 - 0.6e1 * t2377 * t1502 + 0.12e2 * t2344 * t1453 + 0.9e1 * t2332 * t1473 - 0.576e3 * t1369 * t2269 + 0.960e3 * t1369 * t1547 + 0.96e2 * t2691 * t1109 - 0.96e2 * t2691 * t1112 + 0.63625193080042832288502288630209536789558025725859e0 * t1091
  d1111 = -0.86135357435949993011203505076055243600438653328453e-3 * t789 + t3144 + t3122 + 0.12920303615392498951680525761408286540065797999268e-2 * t778 + t3106 + 0.27636177777777777777777777777777777777777777777779e-1 * t704 + t1307 + 0.12920303615392498951680525761408286540065797999268e-2 * t756 + 0.27636177777777777777777777777777777777777777777779e-1 * t707 + 0.82908533333333333333333333333333333333333333333336e-1 * t710 + t1499 - t593 * t548 / 0.6e1 - t596 * t610 / 0.6e1 - t623 * t548 / 0.2e1 + 0.12e2 * t1558 * t184 - 0.48e2 * t1364 * t1112 - 0.384e3 * t136 * t148 - t626 * t632 / 0.2e1 + 0.12e2 * t180 * t184 + 0.144e3 * t219 * t221 + 0.4e1 * t1096 * t184 + 0.240e3 * t136 * t1099 + 0.144e3 * t136 * t221 + 0.48e2 * t1364 * t1109 + 0.240e3 * t219 * t1099 + 0.96e2 * t1369 * t1371 - 0.480e3 * t1369 * t1374 - t1380 * t632 - t1382 * t1285 / 0.2e1 - 0.140e3 / 0.3e1 * t1299 * t1502 - 0.56e2 * t1505 * t1425 + 0.4e1 * t1537 * t1453 + t7 * (t2253 - t1828 - t1830 - t1824 + t1826 + t1818 - t1822 + t1814 - t1987 + t1983 + t1755 + t1749 - t1743 - t1746 + 0.14560e5 / 0.81e2 * t1147 / t8 / t600 * t1181 * t1293 + t2696 + t1735 - t1729 + 0.105e3 / 0.16e2 * t1182 * t1172 / t1253 / t1563 * t1256 * t1567 - t1182 * t1476 * t1256 * (t2545 + t2564) / 0.2e1 - 0.15e2 / 0.2e1 * t1182 * t1302 * t1461 * t1464 - t225 * (t2735 + t2840 + t2891 + t3016) * t135 * t548 / 0.24e2 - t596 * t140 * (-0.1440e4 * t141 * t601 + 0.1920e4 * t142 * t605 - 0.840e3 * t181 * t2281 - 0.24e2 * t183 + 0.384e3 * t2539) * t547 / 0.24e2 + 0.3e1 * t2297 * t2292 * t1396 * t2318 - 0.2e1 * t1148 * t1536 * t1181 * t1502 - 0.2e1 * t1148 * t1450 * t1181 * t1502 + 0.6e1 * t1148 * t1446 * t1421 * t1453 - 0.2e1 * t1182 * t1247 * t1403 * t1405 + 0.9e1 / 0.2e1 * t1182 * t1268 * t1388 * t1398 + t2409 + t2274 + t2370 + t1719 + t2610 + t3081 + t2420 - 0.6e1 * t2328 * t1469 - 0.6e1 * t2332 * t1406 + 0.72e2 * t1108 * t221 + 0.16e2 * t1105 * t1109 - 0.16e2 * t1105 * t1112 + 0.14e2 / 0.3e1 * t1261 * t2358 + 0.14e2 * t1261 * t2354 - 0.21e2 * t1261 * t1399 + 0.14e2 * t1261 * t1406 - 0.28e2 * t1505 * t2614 - t1380 * t1285 / 0.2e1 - t1143 * t632 / 0.2e1 + 0.6e1 * t1422 * t2614 - 0.28e2 * t1496 * t1425 + 0.4e1 * t1451 * t1425 - t1273 * t1285 / 0.4e1 - 0.70e2 / 0.3e1 * t1299 * t1493 - 0.15e2 / 0.2e1 * t2332 * t1465 - 0.21e2 * t2347 * t1473 + 0.72e2 * t1364 * t221 + 0.16e2 * t1096 * t1109 - t1382 * t610 / 0.6e1 - 0.28e2 / 0.3e1 * t1261 * t1257 + 0.9e1 / 0.2e1 * t2328 * t1473 + 0.9e1 * t2332 * t1399 - 0.6e1 * t2377 * t1469 + 0.9e1 / 0.2e1 * t2377 * t1473 + 0.960e3 * t136 * t1547 - 0.480e3 * t136 * t1374 + 0.48e2 * t1558 * t1109 + 0.35e2 / 0.2e1 * t1261 * t1465 + 0.35e2 * t1299 * t1473 + t1710 - t1707 - t1704 + 0.24e2 * t1369 * t140 * t183 - 0.1920e4 * t1369 * t143 * t605 - 0.384e3 * t1369 * t1370 * t147 - 0.28e2 / 0.3e1 * t1260 * t1536 * t1453 + 0.1440e4 * t1369 * t220 * t601 + 0.840e3 * t1369 * t182 * t2281 + 0.9e1 * t1148 * t1423 * t2294 - 0.28e2 * t1260 * t2343 * t1453 - 0.140e3 / 0.3e1 * t1298 * t2331 * t1502 + t1148 * t2522 * t1453 - 0.3e1 * t1182 * t1404 * t1492 - t622 * t592 * t548 / 0.6e1 + 0.4e1 * t119 * t592 * t184 - t563 * t2683 * t548 / 0.24e2 - t542 * t218 * t548 / 0.6e1 + 0.240e3 * t2691 * t1099 - 0.384e3 * t2691 * t148) - t543 * t548 / 0.6e1 + 0.43067678717974996505601752538027621800219326664227e-3 * t782

  res = {'v4rho4': d1111}
  return res
