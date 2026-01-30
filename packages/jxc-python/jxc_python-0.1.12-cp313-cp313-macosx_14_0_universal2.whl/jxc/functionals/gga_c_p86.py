"""Generated from gga_c_p86.mpl."""

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

  params_gamma = np.array([np.nan, -0.1423, -0.0843], dtype=np.float64)

  params_beta1 = np.array([np.nan, 1.0529, 1.3981], dtype=np.float64)

  params_beta2 = np.array([np.nan, 0.3334, 0.2611], dtype=np.float64)

  params_a = np.array([np.nan, 0.0311, 0.01555], dtype=np.float64)

  params_b = np.array([np.nan, -0.048, -0.0269], dtype=np.float64)

  params_c = np.array([np.nan, 0.002, 0.0007], dtype=np.float64)

  params_d = np.array([np.nan, -0.0116, -0.0048], dtype=np.float64)

  p86_DD = lambda z: jnp.sqrt(f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3)) / jnp.sqrt(2)

  p86_CC = lambda rs: +params_aa + (params_bb + params_malpha * rs + params_mbeta * rs ** 2) / (1 + params_mgamma * rs + params_mdelta * rs ** 2 + 10000.0 * params_mbeta * rs ** 3)

  p86_CCinf = params_aa + params_bb

  p86_x1 = lambda rs, xt: xt / jnp.sqrt(rs / f.RS_FACTOR)

  ec_low = lambda i, rs: params_gamma[i] / (1 + params_beta1[i] * jnp.sqrt(rs) + params_beta2[i] * rs)

  ec_high = lambda i, rs: params_a[i] * jnp.log(rs) + params_b[i] + params_c[i] * rs * jnp.log(rs) + params_d[i] * rs

  p86_mPhi = lambda rs, xt: params_ftilde * (p86_CCinf / p86_CC(rs)) * p86_x1(rs, xt)

  ec = lambda i, x: f.my_piecewise3(x >= 1, ec_low(i, x), ec_high(i, x))

  p86_H = lambda rs, z, xt: p86_x1(rs, xt) ** 2 * jnp.exp(-p86_mPhi(rs, xt)) * p86_CC(rs) / p86_DD(z)

  f_pz = lambda rs, zeta: ec(1, rs) + (ec(2, rs) - ec(1, rs)) * f.f_zeta(zeta)

  f_p86 = lambda rs, z, xt, xs0=None, xs1=None: f_pz(rs, z) + p86_H(rs, z, xt)

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

  params_gamma = np.array([np.nan, -0.1423, -0.0843], dtype=np.float64)

  params_beta1 = np.array([np.nan, 1.0529, 1.3981], dtype=np.float64)

  params_beta2 = np.array([np.nan, 0.3334, 0.2611], dtype=np.float64)

  params_a = np.array([np.nan, 0.0311, 0.01555], dtype=np.float64)

  params_b = np.array([np.nan, -0.048, -0.0269], dtype=np.float64)

  params_c = np.array([np.nan, 0.002, 0.0007], dtype=np.float64)

  params_d = np.array([np.nan, -0.0116, -0.0048], dtype=np.float64)

  p86_DD = lambda z: jnp.sqrt(f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3)) / jnp.sqrt(2)

  p86_CC = lambda rs: +params_aa + (params_bb + params_malpha * rs + params_mbeta * rs ** 2) / (1 + params_mgamma * rs + params_mdelta * rs ** 2 + 10000.0 * params_mbeta * rs ** 3)

  p86_CCinf = params_aa + params_bb

  p86_x1 = lambda rs, xt: xt / jnp.sqrt(rs / f.RS_FACTOR)

  ec_low = lambda i, rs: params_gamma[i] / (1 + params_beta1[i] * jnp.sqrt(rs) + params_beta2[i] * rs)

  ec_high = lambda i, rs: params_a[i] * jnp.log(rs) + params_b[i] + params_c[i] * rs * jnp.log(rs) + params_d[i] * rs

  p86_mPhi = lambda rs, xt: params_ftilde * (p86_CCinf / p86_CC(rs)) * p86_x1(rs, xt)

  ec = lambda i, x: f.my_piecewise3(x >= 1, ec_low(i, x), ec_high(i, x))

  p86_H = lambda rs, z, xt: p86_x1(rs, xt) ** 2 * jnp.exp(-p86_mPhi(rs, xt)) * p86_CC(rs) / p86_DD(z)

  f_pz = lambda rs, zeta: ec(1, rs) + (ec(2, rs) - ec(1, rs)) * f.f_zeta(zeta)

  f_p86 = lambda rs, z, xt, xs0=None, xs1=None: f_pz(rs, z) + p86_H(rs, z, xt)

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

  params_gamma = np.array([np.nan, -0.1423, -0.0843], dtype=np.float64)

  params_beta1 = np.array([np.nan, 1.0529, 1.3981], dtype=np.float64)

  params_beta2 = np.array([np.nan, 0.3334, 0.2611], dtype=np.float64)

  params_a = np.array([np.nan, 0.0311, 0.01555], dtype=np.float64)

  params_b = np.array([np.nan, -0.048, -0.0269], dtype=np.float64)

  params_c = np.array([np.nan, 0.002, 0.0007], dtype=np.float64)

  params_d = np.array([np.nan, -0.0116, -0.0048], dtype=np.float64)

  p86_DD = lambda z: jnp.sqrt(f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3)) / jnp.sqrt(2)

  p86_CC = lambda rs: +params_aa + (params_bb + params_malpha * rs + params_mbeta * rs ** 2) / (1 + params_mgamma * rs + params_mdelta * rs ** 2 + 10000.0 * params_mbeta * rs ** 3)

  p86_CCinf = params_aa + params_bb

  p86_x1 = lambda rs, xt: xt / jnp.sqrt(rs / f.RS_FACTOR)

  ec_low = lambda i, rs: params_gamma[i] / (1 + params_beta1[i] * jnp.sqrt(rs) + params_beta2[i] * rs)

  ec_high = lambda i, rs: params_a[i] * jnp.log(rs) + params_b[i] + params_c[i] * rs * jnp.log(rs) + params_d[i] * rs

  p86_mPhi = lambda rs, xt: params_ftilde * (p86_CCinf / p86_CC(rs)) * p86_x1(rs, xt)

  ec = lambda i, x: f.my_piecewise3(x >= 1, ec_low(i, x), ec_high(i, x))

  p86_H = lambda rs, z, xt: p86_x1(rs, xt) ** 2 * jnp.exp(-p86_mPhi(rs, xt)) * p86_CC(rs) / p86_DD(z)

  f_pz = lambda rs, zeta: ec(1, rs) + (ec(2, rs) - ec(1, rs)) * f.f_zeta(zeta)

  f_p86 = lambda rs, z, xt, xs0=None, xs1=None: f_pz(rs, z) + p86_H(rs, z, xt)

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
  t13 = 0.1e1 <= t12
  t14 = jnp.sqrt(t11)
  t17 = 0.1e1 + 0.52645000000000000000000000000000000000000000000000e0 * t14 + 0.83350000000000000000000000000000000000000000000000e-1 * t11
  t20 = jnp.log(t12)
  t23 = t4 * t10 * t20
  t27 = f.my_piecewise3(t13, -0.1423e0 / t17, 0.311e-1 * t20 - 0.48e-1 + 0.50000000000000000000000000000000000000000000000000e-3 * t23 - 0.29000000000000000000000000000000000000000000000000e-2 * t11)
  t30 = 0.1e1 + 0.69905000000000000000000000000000000000000000000000e0 * t14 + 0.65275000000000000000000000000000000000000000000000e-1 * t11
  t37 = f.my_piecewise3(t13, -0.843e-1 / t30, 0.1555e-1 * t20 - 0.269e-1 + 0.17500000000000000000000000000000000000000000000000e-3 * t23 - 0.12000000000000000000000000000000000000000000000000e-2 * t11)
  t38 = t37 - t27
  t39 = r0 - r1
  t40 = 0.1e1 / t7
  t41 = t39 * t40
  t42 = 0.1e1 + t41
  t43 = t42 <= f.p.zeta_threshold
  t44 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t45 = t44 * f.p.zeta_threshold
  t46 = t42 ** (0.1e1 / 0.3e1)
  t48 = f.my_piecewise3(t43, t45, t46 * t42)
  t49 = 0.1e1 - t41
  t50 = t49 <= f.p.zeta_threshold
  t51 = t49 ** (0.1e1 / 0.3e1)
  t53 = f.my_piecewise3(t50, t45, t51 * t49)
  t54 = t48 + t53 - 0.2e1
  t56 = 2 ** (0.1e1 / 0.3e1)
  t59 = 0.1e1 / (0.2e1 * t56 - 0.2e1)
  t60 = t38 * t54 * t59
  t62 = s0 + 0.2e1 * s1 + s2
  t63 = t7 ** 2
  t65 = 0.1e1 / t8 / t63
  t66 = t62 * t65
  t67 = params.aa + params.bb
  t68 = params.ftilde * t67
  t69 = params.malpha * t1
  t70 = t3 * t6
  t71 = t70 * t9
  t74 = t1 ** 2
  t75 = params.mbeta * t74
  t76 = t3 ** 2
  t77 = t76 * t5
  t78 = t8 ** 2
  t80 = t77 / t78
  t83 = params.bb + t69 * t71 / 0.4e1 + t75 * t80 / 0.4e1
  t84 = params.mgamma * t1
  t87 = params.mdelta * t74
  t90 = params.mbeta * t2
  t93 = 0.1e1 + t84 * t71 / 0.4e1 + t87 * t80 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t90 * t40
  t94 = 0.1e1 / t93
  t96 = t83 * t94 + params.aa
  t98 = jnp.sqrt(t62)
  t99 = 0.1e1 / t96 * t98
  t100 = t7 ** (0.1e1 / 0.6e1)
  t102 = 0.1e1 / t100 / t7
  t105 = jnp.exp(-t68 * t99 * t102)
  t106 = t66 * t105
  t107 = t44 ** 2
  t108 = t107 * f.p.zeta_threshold
  t109 = t46 ** 2
  t111 = f.my_piecewise3(t43, t108, t109 * t42)
  t112 = t51 ** 2
  t114 = f.my_piecewise3(t50, t108, t112 * t49)
  t115 = t111 + t114
  t116 = jnp.sqrt(t115)
  t117 = 0.1e1 / t116
  t119 = jnp.sqrt(0.2e1)
  t120 = t96 * t117 * t119
  t121 = t106 * t120
  t122 = t17 ** 2
  t127 = 0.1e1 / t8 / t7
  t128 = t70 * t127
  t129 = 0.1e1 / t14 * t1 * t128
  t131 = t6 * t127
  t132 = t4 * t131
  t139 = t4 * t131 * t20
  t143 = f.my_piecewise3(t13, 0.1423e0 / t122 * (-0.87741666666666666666666666666666666666666666666667e-1 * t129 - 0.27783333333333333333333333333333333333333333333333e-1 * t132), -0.10366666666666666666666666666666666666666666666667e-1 * t40 - 0.16666666666666666666666666666666666666666666666667e-3 * t139 + 0.80000000000000000000000000000000000000000000000000e-3 * t132)
  t144 = t30 ** 2
  t155 = f.my_piecewise3(t13, 0.843e-1 / t144 * (-0.11650833333333333333333333333333333333333333333333e0 * t129 - 0.21758333333333333333333333333333333333333333333333e-1 * t132), -0.51833333333333333333333333333333333333333333333333e-2 * t40 - 0.58333333333333333333333333333333333333333333333333e-4 * t139 + 0.34166666666666666666666666666666666666666666666667e-3 * t132)
  t158 = (t155 - t143) * t54 * t59
  t159 = 0.1e1 / t63
  t160 = t39 * t159
  t161 = t40 - t160
  t164 = f.my_piecewise3(t43, 0, 0.4e1 / 0.3e1 * t46 * t161)
  t165 = -t161
  t168 = f.my_piecewise3(t50, 0, 0.4e1 / 0.3e1 * t51 * t165)
  t172 = t63 * t7
  t178 = 0.7e1 / 0.3e1 * t62 / t8 / t172 * t105 * t120
  t179 = t96 ** 2
  t187 = t77 / t78 / t7
  t192 = t93 ** 2
  t203 = (-t69 * t128 / 0.12e2 - t75 * t187 / 0.6e1) * t94 - t83 / t192 * (-t84 * t128 / 0.12e2 - t87 * t187 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t90 * t159)
  t214 = t117 * t119
  t216 = t66 * (t68 / t179 * t98 * t102 * t203 + 0.7e1 / 0.6e1 * t68 * t99 / t100 / t63) * t105 * t96 * t214
  t219 = t106 * t203 * t117 * t119
  t222 = t96 / t116 / t115
  t225 = f.my_piecewise3(t43, 0, 0.5e1 / 0.3e1 * t109 * t161)
  t228 = f.my_piecewise3(t50, 0, 0.5e1 / 0.3e1 * t112 * t165)
  vrho_0_ = t27 + t60 + t121 + t7 * (t143 + t158 + t38 * (t164 + t168) * t59 - t178 + t216 + t219 - t106 * t222 * t119 * (t225 + t228) / 0.2e1)
  t236 = -t40 - t160
  t239 = f.my_piecewise3(t43, 0, 0.4e1 / 0.3e1 * t46 * t236)
  t240 = -t236
  t243 = f.my_piecewise3(t50, 0, 0.4e1 / 0.3e1 * t51 * t240)
  t249 = f.my_piecewise3(t43, 0, 0.5e1 / 0.3e1 * t109 * t236)
  t252 = f.my_piecewise3(t50, 0, 0.5e1 / 0.3e1 * t112 * t240)
  vrho_1_ = t27 + t60 + t121 + t7 * (t143 + t158 + t38 * (t239 + t243) * t59 - t178 + t216 + t219 - t106 * t222 * t119 * (t249 + t252) / 0.2e1)
  t261 = t65 * t105 * t120
  t262 = jnp.sqrt(t7)
  t269 = t98 / t262 / t172 * params.ftilde * t67 * t105 * t214
  vsigma_0_ = t7 * (t261 - t269 / 0.2e1)
  vsigma_1_ = t7 * (0.2e1 * t261 - t269)
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

  params_gamma = np.array([np.nan, -0.1423, -0.0843], dtype=np.float64)

  params_beta1 = np.array([np.nan, 1.0529, 1.3981], dtype=np.float64)

  params_beta2 = np.array([np.nan, 0.3334, 0.2611], dtype=np.float64)

  params_a = np.array([np.nan, 0.0311, 0.01555], dtype=np.float64)

  params_b = np.array([np.nan, -0.048, -0.0269], dtype=np.float64)

  params_c = np.array([np.nan, 0.002, 0.0007], dtype=np.float64)

  params_d = np.array([np.nan, -0.0116, -0.0048], dtype=np.float64)

  p86_DD = lambda z: jnp.sqrt(f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3)) / jnp.sqrt(2)

  p86_CC = lambda rs: +params_aa + (params_bb + params_malpha * rs + params_mbeta * rs ** 2) / (1 + params_mgamma * rs + params_mdelta * rs ** 2 + 10000.0 * params_mbeta * rs ** 3)

  p86_CCinf = params_aa + params_bb

  p86_x1 = lambda rs, xt: xt / jnp.sqrt(rs / f.RS_FACTOR)

  ec_low = lambda i, rs: params_gamma[i] / (1 + params_beta1[i] * jnp.sqrt(rs) + params_beta2[i] * rs)

  ec_high = lambda i, rs: params_a[i] * jnp.log(rs) + params_b[i] + params_c[i] * rs * jnp.log(rs) + params_d[i] * rs

  p86_mPhi = lambda rs, xt: params_ftilde * (p86_CCinf / p86_CC(rs)) * p86_x1(rs, xt)

  ec = lambda i, x: f.my_piecewise3(x >= 1, ec_low(i, x), ec_high(i, x))

  p86_H = lambda rs, z, xt: p86_x1(rs, xt) ** 2 * jnp.exp(-p86_mPhi(rs, xt)) * p86_CC(rs) / p86_DD(z)

  f_pz = lambda rs, zeta: ec(1, rs) + (ec(2, rs) - ec(1, rs)) * f.f_zeta(zeta)

  f_p86 = lambda rs, z, xt, xs0=None, xs1=None: f_pz(rs, z) + p86_H(rs, z, xt)

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
  t12 = 0.1e1 <= t11
  t13 = jnp.sqrt(t10)
  t16 = 0.1e1 + 0.52645000000000000000000000000000000000000000000000e0 * t13 + 0.83350000000000000000000000000000000000000000000000e-1 * t10
  t19 = jnp.log(t11)
  t22 = t4 * t9 * t19
  t26 = f.my_piecewise3(t12, -0.1423e0 / t16, 0.311e-1 * t19 - 0.48e-1 + 0.50000000000000000000000000000000000000000000000000e-3 * t22 - 0.29000000000000000000000000000000000000000000000000e-2 * t10)
  t29 = 0.1e1 + 0.69905000000000000000000000000000000000000000000000e0 * t13 + 0.65275000000000000000000000000000000000000000000000e-1 * t10
  t36 = f.my_piecewise3(t12, -0.843e-1 / t29, 0.1555e-1 * t19 - 0.269e-1 + 0.17500000000000000000000000000000000000000000000000e-3 * t22 - 0.12000000000000000000000000000000000000000000000000e-2 * t10)
  t38 = 0.1e1 <= f.p.zeta_threshold
  t39 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t41 = f.my_piecewise3(t38, t39 * f.p.zeta_threshold, 1)
  t43 = 0.2e1 * t41 - 0.2e1
  t45 = 2 ** (0.1e1 / 0.3e1)
  t48 = 0.1e1 / (0.2e1 * t45 - 0.2e1)
  t50 = r0 ** 2
  t52 = 0.1e1 / t7 / t50
  t53 = s0 * t52
  t54 = params.aa + params.bb
  t55 = params.ftilde * t54
  t56 = params.malpha * t1
  t57 = t3 * t6
  t58 = t57 * t8
  t61 = t1 ** 2
  t62 = params.mbeta * t61
  t63 = t3 ** 2
  t64 = t63 * t5
  t65 = t7 ** 2
  t67 = t64 / t65
  t70 = params.bb + t56 * t58 / 0.4e1 + t62 * t67 / 0.4e1
  t71 = params.mgamma * t1
  t74 = params.mdelta * t61
  t77 = params.mbeta * t2
  t78 = 0.1e1 / r0
  t81 = 0.1e1 + t71 * t58 / 0.4e1 + t74 * t67 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t77 * t78
  t82 = 0.1e1 / t81
  t84 = t70 * t82 + params.aa
  t86 = jnp.sqrt(s0)
  t87 = 0.1e1 / t84 * t86
  t88 = r0 ** (0.1e1 / 0.6e1)
  t90 = 0.1e1 / t88 / r0
  t93 = jnp.exp(-t55 * t87 * t90)
  t95 = t39 ** 2
  t97 = f.my_piecewise3(t38, t95 * f.p.zeta_threshold, 1)
  t98 = jnp.sqrt(t97)
  t99 = 0.1e1 / t98
  t100 = t93 * t84 * t99
  t102 = t16 ** 2
  t107 = 0.1e1 / t7 / r0
  t108 = t57 * t107
  t109 = 0.1e1 / t13 * t1 * t108
  t111 = t6 * t107
  t112 = t4 * t111
  t119 = t4 * t111 * t19
  t123 = f.my_piecewise3(t12, 0.1423e0 / t102 * (-0.87741666666666666666666666666666666666666666666667e-1 * t109 - 0.27783333333333333333333333333333333333333333333333e-1 * t112), -0.10366666666666666666666666666666666666666666666667e-1 * t78 - 0.16666666666666666666666666666666666666666666666667e-3 * t119 + 0.80000000000000000000000000000000000000000000000000e-3 * t112)
  t124 = t29 ** 2
  t135 = f.my_piecewise3(t12, 0.843e-1 / t124 * (-0.11650833333333333333333333333333333333333333333333e0 * t109 - 0.21758333333333333333333333333333333333333333333333e-1 * t112), -0.51833333333333333333333333333333333333333333333333e-2 * t78 - 0.58333333333333333333333333333333333333333333333333e-4 * t119 + 0.34166666666666666666666666666666666666666666666667e-3 * t112)
  t139 = t50 * r0
  t145 = t84 ** 2
  t153 = t64 / t65 / r0
  t158 = t81 ** 2
  t170 = (-t56 * t108 / 0.12e2 - t62 * t153 / 0.6e1) * t82 - t70 / t158 * (-t71 * t108 / 0.12e2 - t74 * t153 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t77 / t50)
  vrho_0_ = t26 + (t36 - t26) * t43 * t48 + t53 * t100 + r0 * (t123 + (t135 - t123) * t43 * t48 - 0.7e1 / 0.3e1 * s0 / t7 / t139 * t100 + t53 * (t55 / t145 * t86 * t90 * t170 + 0.7e1 / 0.6e1 * t55 * t87 / t88 / t50) * t100 + t53 * t93 * t170 * t99)
  t189 = jnp.sqrt(r0)
  vsigma_0_ = r0 * (t52 * t93 * t84 * t99 - t86 / t189 / t139 * params.ftilde * t54 * t93 * t99 / 0.2e1)
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
  t8 = 0.1e1 / t7
  t10 = t4 * t6 * t8
  t11 = t10 / 0.4e1
  t12 = 0.1e1 <= t11
  t13 = jnp.sqrt(t10)
  t16 = 0.1e1 + 0.52645000000000000000000000000000000000000000000000e0 * t13 + 0.83350000000000000000000000000000000000000000000000e-1 * t10
  t17 = t16 ** 2
  t18 = 0.1e1 / t17
  t20 = 0.1e1 / t13 * t1
  t21 = t3 * t6
  t23 = 0.1e1 / t7 / r0
  t24 = t21 * t23
  t25 = t20 * t24
  t27 = t6 * t23
  t28 = t4 * t27
  t30 = -0.87741666666666666666666666666666666666666666666667e-1 * t25 - 0.27783333333333333333333333333333333333333333333333e-1 * t28
  t33 = 0.1e1 / r0
  t35 = jnp.log(t11)
  t37 = t4 * t27 * t35
  t41 = f.my_piecewise3(t12, 0.1423e0 * t18 * t30, -0.10366666666666666666666666666666666666666666666667e-1 * t33 - 0.16666666666666666666666666666666666666666666666667e-3 * t37 + 0.80000000000000000000000000000000000000000000000000e-3 * t28)
  t45 = 0.1e1 + 0.69905000000000000000000000000000000000000000000000e0 * t13 + 0.65275000000000000000000000000000000000000000000000e-1 * t10
  t46 = t45 ** 2
  t47 = 0.1e1 / t46
  t50 = -0.11650833333333333333333333333333333333333333333333e0 * t25 - 0.21758333333333333333333333333333333333333333333333e-1 * t28
  t57 = f.my_piecewise3(t12, 0.843e-1 * t47 * t50, -0.51833333333333333333333333333333333333333333333333e-2 * t33 - 0.58333333333333333333333333333333333333333333333333e-4 * t37 + 0.34166666666666666666666666666666666666666666666667e-3 * t28)
  t59 = 0.1e1 <= f.p.zeta_threshold
  t60 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t62 = f.my_piecewise3(t59, t60 * f.p.zeta_threshold, 1)
  t64 = 0.2e1 * t62 - 0.2e1
  t66 = 2 ** (0.1e1 / 0.3e1)
  t69 = 0.1e1 / (0.2e1 * t66 - 0.2e1)
  t72 = r0 ** 2
  t73 = t72 * r0
  t75 = 0.1e1 / t7 / t73
  t76 = s0 * t75
  t77 = params.aa + params.bb
  t78 = params.ftilde * t77
  t79 = params.malpha * t1
  t80 = t21 * t8
  t83 = t1 ** 2
  t84 = params.mbeta * t83
  t85 = t3 ** 2
  t86 = t85 * t5
  t87 = t7 ** 2
  t89 = t86 / t87
  t92 = params.bb + t79 * t80 / 0.4e1 + t84 * t89 / 0.4e1
  t93 = params.mgamma * t1
  t96 = params.mdelta * t83
  t99 = params.mbeta * t2
  t102 = 0.1e1 + t93 * t80 / 0.4e1 + t96 * t89 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t99 * t33
  t103 = 0.1e1 / t102
  t105 = t92 * t103 + params.aa
  t106 = 0.1e1 / t105
  t107 = jnp.sqrt(s0)
  t108 = t106 * t107
  t109 = r0 ** (0.1e1 / 0.6e1)
  t111 = 0.1e1 / t109 / r0
  t114 = jnp.exp(-t78 * t108 * t111)
  t116 = t60 ** 2
  t118 = f.my_piecewise3(t59, t116 * f.p.zeta_threshold, 1)
  t119 = jnp.sqrt(t118)
  t120 = 0.1e1 / t119
  t121 = t114 * t105 * t120
  t125 = 0.1e1 / t7 / t72
  t126 = s0 * t125
  t127 = t105 ** 2
  t129 = t78 / t127
  t130 = t107 * t111
  t135 = t86 / t87 / r0
  t138 = -t79 * t24 / 0.12e2 - t84 * t135 / 0.6e1
  t140 = t102 ** 2
  t141 = 0.1e1 / t140
  t142 = t92 * t141
  t147 = 0.1e1 / t72
  t150 = -t93 * t24 / 0.12e2 - t96 * t135 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t99 * t147
  t152 = t138 * t103 - t142 * t150
  t156 = 0.1e1 / t109 / t72
  t160 = t129 * t130 * t152 + 0.7e1 / 0.6e1 * t78 * t108 * t156
  t161 = t126 * t160
  t165 = t114 * t152 * t120
  t170 = t30 ** 2
  t178 = t86 / t87 / t72
  t179 = 0.1e1 / t13 / t10 * t83 * t178
  t181 = t21 * t125
  t182 = t20 * t181
  t184 = t6 * t125
  t185 = t4 * t184
  t193 = t4 * t184 * t35
  t197 = f.my_piecewise3(t12, -0.2846e0 / t17 / t16 * t170 + 0.1423e0 * t18 * (-0.58494444444444444444444444444444444444444444444445e-1 * t179 + 0.11698888888888888888888888888888888888888888888889e0 * t182 + 0.37044444444444444444444444444444444444444444444444e-1 * t185), 0.10366666666666666666666666666666666666666666666667e-1 * t147 + 0.22222222222222222222222222222222222222222222222223e-3 * t193 - 0.10111111111111111111111111111111111111111111111111e-2 * t185)
  t200 = t50 ** 2
  t214 = f.my_piecewise3(t12, -0.1686e0 / t46 / t45 * t200 + 0.843e-1 * t47 * (-0.77672222222222222222222222222222222222222222222220e-1 * t179 + 0.15534444444444444444444444444444444444444444444444e0 * t182 + 0.29011111111111111111111111111111111111111111111111e-1 * t185), 0.51833333333333333333333333333333333333333333333333e-2 * t147 + 0.77777777777777777777777777777777777777777777777777e-4 * t193 - 0.43611111111111111111111111111111111111111111111112e-3 * t185)
  t218 = t72 ** 2
  t232 = t152 ** 2
  t252 = t150 ** 2
  t264 = (t79 * t181 / 0.9e1 + 0.5e1 / 0.18e2 * t84 * t178) * t103 - 0.2e1 * t138 * t141 * t150 + 0.2e1 * t92 / t140 / t102 * t252 - t142 * (t93 * t181 / 0.9e1 + 0.5e1 / 0.18e2 * t96 * t178 + 0.15000000000000000000000000000000000000000000000000e5 * t99 / t73)
  t275 = t160 ** 2
  v2rho2_0_ = 0.2e1 * t41 + 0.2e1 * (t57 - t41) * t64 * t69 - 0.14e2 / 0.3e1 * t76 * t121 + 0.2e1 * t161 * t121 + 0.2e1 * t126 * t165 + r0 * (t197 + (t214 - t197) * t64 * t69 + 0.70e2 / 0.9e1 * s0 / t7 / t218 * t121 - 0.14e2 / 0.3e1 * t76 * t160 * t121 - 0.14e2 / 0.3e1 * t76 * t165 + t126 * (-0.2e1 * t78 / t127 / t105 * t130 * t232 - 0.7e1 / 0.3e1 * t129 * t107 * t156 * t152 + t129 * t130 * t264 - 0.91e2 / 0.36e2 * t78 * t108 / t109 / t73) * t121 + t126 * t275 * t121 + 0.2e1 * t161 * t165 + t126 * t114 * t264 * t120)
  t285 = t125 * t114
  t286 = t105 * t120
  t288 = jnp.sqrt(r0)
  t290 = 0.1e1 / t288 / t73
  t292 = t107 * t290 * params.ftilde
  t294 = t77 * t114 * t120
  v2rhosigma_0_ = t285 * t286 - t292 * t294 / 0.2e1 + r0 * (-0.7e1 / 0.3e1 * t75 * t114 * t286 + t125 * t160 * t121 + t285 * t152 * t120 + 0.7e1 / 0.4e1 * t107 / t288 / t218 * params.ftilde * t294 - t292 * t77 * t160 * t114 * t120 / 0.2e1)
  t326 = params.ftilde ** 2
  t328 = t77 ** 2
  v2sigma2_0_ = r0 * (-0.3e1 / 0.4e1 * t290 * params.ftilde * t77 / t107 * t114 * t120 + 0.1e1 / t87 / t218 * t326 * t328 * t106 * t114 * t120 / 0.4e1)
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
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
  t10 = t4 * t6 * t8
  t11 = t10 / 0.4e1
  t12 = 0.1e1 <= t11
  t13 = jnp.sqrt(t10)
  t16 = 0.1e1 + 0.52645000000000000000000000000000000000000000000000e0 * t13 + 0.83350000000000000000000000000000000000000000000000e-1 * t10
  t17 = t16 ** 2
  t19 = 0.1e1 / t17 / t16
  t21 = 0.1e1 / t13 * t1
  t22 = t3 * t6
  t24 = 0.1e1 / t7 / r0
  t25 = t22 * t24
  t26 = t21 * t25
  t29 = t4 * t6 * t24
  t31 = -0.87741666666666666666666666666666666666666666666667e-1 * t26 - 0.27783333333333333333333333333333333333333333333333e-1 * t29
  t32 = t31 ** 2
  t35 = 0.1e1 / t17
  t38 = t1 ** 2
  t39 = 0.1e1 / t13 / t10 * t38
  t40 = t3 ** 2
  t41 = t40 * t5
  t42 = r0 ** 2
  t43 = t7 ** 2
  t46 = t41 / t43 / t42
  t47 = t39 * t46
  t50 = 0.1e1 / t7 / t42
  t51 = t22 * t50
  t52 = t21 * t51
  t54 = t6 * t50
  t55 = t4 * t54
  t57 = -0.58494444444444444444444444444444444444444444444445e-1 * t47 + 0.11698888888888888888888888888888888888888888888889e0 * t52 + 0.37044444444444444444444444444444444444444444444444e-1 * t55
  t61 = 0.1e1 / t42
  t63 = jnp.log(t11)
  t65 = t4 * t54 * t63
  t69 = f.my_piecewise3(t12, -0.2846e0 * t19 * t32 + 0.1423e0 * t35 * t57, 0.10366666666666666666666666666666666666666666666667e-1 * t61 + 0.22222222222222222222222222222222222222222222222223e-3 * t65 - 0.10111111111111111111111111111111111111111111111111e-2 * t55)
  t73 = 0.1e1 + 0.69905000000000000000000000000000000000000000000000e0 * t13 + 0.65275000000000000000000000000000000000000000000000e-1 * t10
  t74 = t73 ** 2
  t76 = 0.1e1 / t74 / t73
  t79 = -0.11650833333333333333333333333333333333333333333333e0 * t26 - 0.21758333333333333333333333333333333333333333333333e-1 * t29
  t80 = t79 ** 2
  t83 = 0.1e1 / t74
  t87 = -0.77672222222222222222222222222222222222222222222220e-1 * t47 + 0.15534444444444444444444444444444444444444444444444e0 * t52 + 0.29011111111111111111111111111111111111111111111111e-1 * t55
  t95 = f.my_piecewise3(t12, -0.1686e0 * t76 * t80 + 0.843e-1 * t83 * t87, 0.51833333333333333333333333333333333333333333333333e-2 * t61 + 0.77777777777777777777777777777777777777777777777777e-4 * t65 - 0.43611111111111111111111111111111111111111111111112e-3 * t55)
  t97 = 0.1e1 <= f.p.zeta_threshold
  t98 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t100 = f.my_piecewise3(t97, t98 * f.p.zeta_threshold, 1)
  t102 = 0.2e1 * t100 - 0.2e1
  t104 = 2 ** (0.1e1 / 0.3e1)
  t107 = 0.1e1 / (0.2e1 * t104 - 0.2e1)
  t110 = t42 ** 2
  t113 = s0 / t7 / t110
  t115 = params.ftilde * (params.aa + params.bb)
  t116 = params.malpha * t1
  t117 = t22 * t8
  t120 = params.mbeta * t38
  t121 = 0.1e1 / t43
  t122 = t41 * t121
  t125 = params.bb + t116 * t117 / 0.4e1 + t120 * t122 / 0.4e1
  t126 = params.mgamma * t1
  t129 = params.mdelta * t38
  t132 = params.mbeta * t2
  t136 = 0.1e1 + t126 * t117 / 0.4e1 + t129 * t122 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t132 / r0
  t137 = 0.1e1 / t136
  t139 = t125 * t137 + params.aa
  t141 = jnp.sqrt(s0)
  t142 = 0.1e1 / t139 * t141
  t143 = r0 ** (0.1e1 / 0.6e1)
  t145 = 0.1e1 / t143 / r0
  t148 = jnp.exp(-t115 * t142 * t145)
  t150 = t98 ** 2
  t152 = f.my_piecewise3(t97, t150 * f.p.zeta_threshold, 1)
  t153 = jnp.sqrt(t152)
  t154 = 0.1e1 / t153
  t155 = t148 * t139 * t154
  t158 = t42 * r0
  t160 = 0.1e1 / t7 / t158
  t161 = s0 * t160
  t162 = t139 ** 2
  t164 = t115 / t162
  t165 = t141 * t145
  t170 = t41 / t43 / r0
  t173 = -t116 * t25 / 0.12e2 - t120 * t170 / 0.6e1
  t175 = t136 ** 2
  t176 = 0.1e1 / t175
  t177 = t125 * t176
  t184 = -t126 * t25 / 0.12e2 - t129 * t170 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t132 * t61
  t186 = t173 * t137 - t177 * t184
  t190 = 0.1e1 / t143 / t42
  t194 = t164 * t165 * t186 + 0.7e1 / 0.6e1 * t115 * t142 * t190
  t195 = t161 * t194
  t199 = t148 * t186 * t154
  t202 = s0 * t50
  t205 = t115 / t162 / t139
  t206 = t186 ** 2
  t210 = t141 * t190
  t218 = t116 * t51 / 0.9e1 + 0.5e1 / 0.18e2 * t120 * t46
  t220 = t173 * t176
  t224 = 0.1e1 / t175 / t136
  t225 = t125 * t224
  t226 = t184 ** 2
  t233 = 0.1e1 / t158
  t236 = t126 * t51 / 0.9e1 + 0.5e1 / 0.18e2 * t129 * t46 + 0.15000000000000000000000000000000000000000000000000e5 * t132 * t233
  t238 = t218 * t137 - t177 * t236 - 0.2e1 * t220 * t184 + 0.2e1 * t225 * t226
  t242 = 0.1e1 / t143 / t158
  t246 = -0.2e1 * t205 * t165 * t206 - 0.7e1 / 0.3e1 * t164 * t210 * t186 + t164 * t165 * t238 - 0.91e2 / 0.36e2 * t115 * t142 * t242
  t247 = t202 * t246
  t250 = t194 ** 2
  t251 = t202 * t250
  t254 = t202 * t194
  t258 = t148 * t238 * t154
  t281 = t162 ** 2
  t302 = t22 * t160
  t307 = t41 / t43 / t158
  t320 = t175 ** 2
  t333 = 0.1e1 / t110
  t338 = (-0.7e1 / 0.27e2 * t116 * t302 - 0.20e2 / 0.27e2 * t120 * t307) * t137 - 0.3e1 * t218 * t176 * t184 + 0.6e1 * t173 * t224 * t226 - 0.3e1 * t220 * t236 - 0.6e1 * t125 / t320 * t226 * t184 + 0.6e1 * t225 * t184 * t236 - t177 * (-0.7e1 / 0.27e2 * t126 * t302 - 0.20e2 / 0.27e2 * t129 * t307 - 0.45000000000000000000000000000000000000000000000000e5 * t132 * t333)
  t356 = t17 ** 2
  t371 = 0.1e1 / t13 / t38 / t40 / t5 / t121 * t2 * t333 / 0.4e1
  t373 = t39 * t307
  t375 = t21 * t302
  t377 = t6 * t160
  t378 = t4 * t377
  t386 = t4 * t377 * t63
  t390 = f.my_piecewise3(t12, 0.8538e0 / t356 * t32 * t31 - 0.8538e0 * t19 * t31 * t57 + 0.1423e0 * t35 * (-0.35096666666666666666666666666666666666666666666667e0 * t371 + 0.23397777777777777777777777777777777777777777777778e0 * t373 - 0.27297407407407407407407407407407407407407407407408e0 * t375 - 0.86437037037037037037037037037037037037037037037036e-1 * t378), -0.20733333333333333333333333333333333333333333333334e-1 * t233 - 0.51851851851851851851851851851851851851851851851854e-3 * t386 + 0.22851851851851851851851851851851851851851851851851e-2 * t378)
  t402 = t74 ** 2
  t422 = f.my_piecewise3(t12, 0.5058e0 / t402 * t80 * t79 - 0.5058e0 * t76 * t79 * t87 + 0.843e-1 * t83 * (-0.46603333333333333333333333333333333333333333333332e0 * t371 + 0.31068888888888888888888888888888888888888888888888e0 * t373 - 0.36247037037037037037037037037037037037037037037036e0 * t375 - 0.67692592592592592592592592592592592592592592592592e-1 * t378), -0.10366666666666666666666666666666666666666666666667e-1 * t233 - 0.18148148148148148148148148148148148148148148148148e-3 * t386 + 0.99166666666666666666666666666666666666666666666667e-3 * t378)
  t426 = 0.3e1 * t254 * t258 + 0.3e1 * t247 * t199 + 0.3e1 * t251 * t199 - 0.910e3 / 0.27e2 * s0 / t7 / t110 / r0 * t155 + 0.70e2 / 0.3e1 * t113 * t194 * t155 - 0.7e1 * t161 * t246 * t155 - 0.14e2 * t195 * t199 + t202 * (0.6e1 * t115 / t281 * t165 * t206 * t186 + 0.7e1 * t205 * t210 * t206 - 0.6e1 * t205 * t165 * t186 * t238 + 0.91e2 / 0.12e2 * t164 * t141 * t242 * t186 - 0.7e1 / 0.2e1 * t164 * t210 * t238 + t164 * t165 * t338 + 0.1729e4 / 0.216e3 * t115 * t142 / t143 / t110) * t155 + t202 * t148 * t338 * t154 - 0.7e1 * t161 * t258 + 0.70e2 / 0.3e1 * t113 * t199 + t390 + 0.3e1 * t247 * t194 * t148 * t139 * t154 + t202 * t250 * t194 * t155 - 0.7e1 * t161 * t250 * t155 + (t422 - t390) * t102 * t107
  v3rho3_0_ = 0.3e1 * t69 + 0.3e1 * (t95 - t69) * t102 * t107 + 0.70e2 / 0.3e1 * t113 * t155 - 0.14e2 * t195 * t155 - 0.14e2 * t161 * t199 + 0.3e1 * t247 * t155 + 0.3e1 * t251 * t155 + 0.6e1 * t254 * t199 + 0.3e1 * t202 * t258 + r0 * t426

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
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
  t10 = t4 * t6 * t8
  t11 = t10 / 0.4e1
  t12 = 0.1e1 <= t11
  t13 = jnp.sqrt(t10)
  t16 = 0.1e1 + 0.52645000000000000000000000000000000000000000000000e0 * t13 + 0.83350000000000000000000000000000000000000000000000e-1 * t10
  t17 = t16 ** 2
  t18 = t17 ** 2
  t19 = 0.1e1 / t18
  t21 = 0.1e1 / t13 * t1
  t22 = t3 * t6
  t24 = 0.1e1 / t7 / r0
  t25 = t22 * t24
  t26 = t21 * t25
  t29 = t4 * t6 * t24
  t31 = -0.87741666666666666666666666666666666666666666666667e-1 * t26 - 0.27783333333333333333333333333333333333333333333333e-1 * t29
  t32 = t31 ** 2
  t37 = 0.1e1 / t17 / t16
  t38 = t37 * t31
  t41 = t1 ** 2
  t42 = 0.1e1 / t13 / t10 * t41
  t43 = t3 ** 2
  t44 = t43 * t5
  t45 = r0 ** 2
  t46 = t7 ** 2
  t49 = t44 / t46 / t45
  t50 = t42 * t49
  t53 = 0.1e1 / t7 / t45
  t54 = t22 * t53
  t55 = t21 * t54
  t58 = t4 * t6 * t53
  t60 = -0.58494444444444444444444444444444444444444444444445e-1 * t50 + 0.11698888888888888888888888888888888888888888888889e0 * t55 + 0.37044444444444444444444444444444444444444444444444e-1 * t58
  t63 = 0.1e1 / t17
  t65 = 0.1e1 / t46
  t71 = 0.1e1 / t13 / t41 / t43 / t5 / t65 * t2 / 0.4e1
  t72 = t45 ** 2
  t73 = 0.1e1 / t72
  t74 = t71 * t73
  t76 = t45 * r0
  t79 = t44 / t46 / t76
  t80 = t42 * t79
  t83 = 0.1e1 / t7 / t76
  t84 = t22 * t83
  t85 = t21 * t84
  t87 = t6 * t83
  t88 = t4 * t87
  t90 = -0.35096666666666666666666666666666666666666666666667e0 * t74 + 0.23397777777777777777777777777777777777777777777778e0 * t80 - 0.27297407407407407407407407407407407407407407407408e0 * t85 - 0.86437037037037037037037037037037037037037037037036e-1 * t88
  t94 = 0.1e1 / t76
  t96 = jnp.log(t11)
  t98 = t4 * t87 * t96
  t102 = f.my_piecewise3(t12, 0.8538e0 * t19 * t32 * t31 - 0.8538e0 * t38 * t60 + 0.1423e0 * t63 * t90, -0.20733333333333333333333333333333333333333333333334e-1 * t94 - 0.51851851851851851851851851851851851851851851851854e-3 * t98 + 0.22851851851851851851851851851851851851851851851851e-2 * t88)
  t106 = 0.1e1 + 0.69905000000000000000000000000000000000000000000000e0 * t13 + 0.65275000000000000000000000000000000000000000000000e-1 * t10
  t107 = t106 ** 2
  t108 = t107 ** 2
  t109 = 0.1e1 / t108
  t112 = -0.11650833333333333333333333333333333333333333333333e0 * t26 - 0.21758333333333333333333333333333333333333333333333e-1 * t29
  t113 = t112 ** 2
  t118 = 0.1e1 / t107 / t106
  t119 = t118 * t112
  t123 = -0.77672222222222222222222222222222222222222222222220e-1 * t50 + 0.15534444444444444444444444444444444444444444444444e0 * t55 + 0.29011111111111111111111111111111111111111111111111e-1 * t58
  t126 = 0.1e1 / t107
  t131 = -0.46603333333333333333333333333333333333333333333332e0 * t74 + 0.31068888888888888888888888888888888888888888888888e0 * t80 - 0.36247037037037037037037037037037037037037037037036e0 * t85 - 0.67692592592592592592592592592592592592592592592592e-1 * t88
  t139 = f.my_piecewise3(t12, 0.5058e0 * t109 * t113 * t112 - 0.5058e0 * t119 * t123 + 0.843e-1 * t126 * t131, -0.10366666666666666666666666666666666666666666666667e-1 * t94 - 0.18148148148148148148148148148148148148148148148148e-3 * t98 + 0.99166666666666666666666666666666666666666666666667e-3 * t88)
  t141 = 0.1e1 <= f.p.zeta_threshold
  t142 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t144 = f.my_piecewise3(t141, t142 * f.p.zeta_threshold, 1)
  t146 = 0.2e1 * t144 - 0.2e1
  t148 = 2 ** (0.1e1 / 0.3e1)
  t151 = 0.1e1 / (0.2e1 * t148 - 0.2e1)
  t154 = s0 * t53
  t156 = params.ftilde * (params.aa + params.bb)
  t157 = params.malpha * t1
  t158 = t22 * t8
  t161 = params.mbeta * t41
  t162 = t44 * t65
  t165 = params.bb + t157 * t158 / 0.4e1 + t161 * t162 / 0.4e1
  t166 = params.mgamma * t1
  t169 = params.mdelta * t41
  t172 = params.mbeta * t2
  t173 = 0.1e1 / r0
  t176 = 0.1e1 + t166 * t158 / 0.4e1 + t169 * t162 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t172 * t173
  t177 = 0.1e1 / t176
  t179 = t165 * t177 + params.aa
  t180 = t179 ** 2
  t182 = t156 / t180
  t183 = jnp.sqrt(s0)
  t184 = r0 ** (0.1e1 / 0.6e1)
  t186 = 0.1e1 / t184 / r0
  t187 = t183 * t186
  t192 = t44 / t46 / r0
  t195 = -t157 * t25 / 0.12e2 - t161 * t192 / 0.6e1
  t197 = t176 ** 2
  t198 = 0.1e1 / t197
  t199 = t165 * t198
  t207 = -t166 * t25 / 0.12e2 - t169 * t192 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t172 / t45
  t209 = t195 * t177 - t199 * t207
  t213 = 0.1e1 / t179 * t183
  t215 = 0.1e1 / t184 / t45
  t219 = t182 * t187 * t209 + 0.7e1 / 0.6e1 * t156 * t213 * t215
  t220 = t219 ** 2
  t221 = t220 * t219
  t222 = t154 * t221
  t225 = jnp.exp(-t156 * t213 * t186)
  t227 = t142 ** 2
  t229 = f.my_piecewise3(t141, t227 * f.p.zeta_threshold, 1)
  t230 = jnp.sqrt(t229)
  t231 = 0.1e1 / t230
  t232 = t225 * t179 * t231
  t235 = s0 * t83
  t236 = t235 * t220
  t239 = t180 ** 2
  t241 = t156 / t239
  t242 = t209 ** 2
  t243 = t242 * t209
  t249 = t156 / t180 / t179
  t250 = t183 * t215
  t258 = t157 * t54 / 0.9e1 + 0.5e1 / 0.18e2 * t161 * t49
  t260 = t195 * t198
  t264 = 0.1e1 / t197 / t176
  t265 = t165 * t264
  t266 = t207 ** 2
  t275 = t166 * t54 / 0.9e1 + 0.5e1 / 0.18e2 * t169 * t49 + 0.15000000000000000000000000000000000000000000000000e5 * t172 * t94
  t277 = t258 * t177 - t199 * t275 - 0.2e1 * t260 * t207 + 0.2e1 * t265 * t266
  t278 = t209 * t277
  t283 = 0.1e1 / t184 / t76
  t284 = t183 * t283
  t295 = -0.7e1 / 0.27e2 * t157 * t84 - 0.20e2 / 0.27e2 * t161 * t79
  t297 = t258 * t198
  t300 = t195 * t264
  t305 = t197 ** 2
  t306 = 0.1e1 / t305
  t307 = t165 * t306
  t308 = t266 * t207
  t311 = t207 * t275
  t320 = -0.7e1 / 0.27e2 * t166 * t84 - 0.20e2 / 0.27e2 * t169 * t79 - 0.45000000000000000000000000000000000000000000000000e5 * t172 * t73
  t322 = t295 * t177 - t199 * t320 - 0.3e1 * t297 * t207 - 0.3e1 * t260 * t275 + 0.6e1 * t265 * t311 + 0.6e1 * t300 * t266 - 0.6e1 * t307 * t308
  t326 = 0.1e1 / t184 / t72
  t330 = 0.6e1 * t241 * t187 * t243 + 0.7e1 * t249 * t250 * t242 - 0.6e1 * t249 * t187 * t278 + 0.91e2 / 0.12e2 * t182 * t284 * t209 - 0.7e1 / 0.2e1 * t182 * t250 * t277 + t182 * t187 * t322 + 0.1729e4 / 0.216e3 * t156 * t213 * t326
  t331 = t154 * t330
  t334 = t235 * t219
  t336 = t225 * t209 * t231
  t350 = -0.2e1 * t249 * t187 * t242 - 0.7e1 / 0.3e1 * t182 * t250 * t209 + t182 * t187 * t277 - 0.91e2 / 0.36e2 * t156 * t213 * t283
  t351 = t235 * t350
  t355 = 0.1e1 / t7 / t72
  t356 = s0 * t355
  t360 = t225 * t322 * t231
  t364 = t225 * t277 * t231
  t367 = t72 * r0
  t369 = 0.1e1 / t7 / t367
  t370 = s0 * t369
  t373 = t356 * t219
  t376 = t154 * t220
  t379 = t154 * t350
  t382 = t154 * t219
  t385 = t219 * t225
  t386 = t179 * t231
  t387 = t385 * t386
  t392 = t32 ** 2
  t398 = t60 ** 2
  t410 = 0.1e1 / t13 / t173 * t369 * t4 * t6 / 0.48e2
  t412 = 0.1e1 / t367
  t413 = t71 * t412
  t417 = t44 / t46 / t72
  t418 = t42 * t417
  t420 = t22 * t355
  t421 = t21 * t420
  t423 = t6 * t355
  t424 = t4 * t423
  t432 = t4 * t423 * t96
  t436 = f.my_piecewise3(t12, -0.34152e1 / t18 / t16 * t392 + 0.51228e1 * t19 * t32 * t60 - 0.8538e0 * t37 * t398 - 0.11384e1 * t38 * t90 + 0.1423e0 * t63 * (-0.29247222222222222222222222222222222222222222222222e0 * t410 + 0.28077333333333333333333333333333333333333333333334e1 * t413 - 0.10399012345679012345679012345679012345679012345679e1 * t418 + 0.90991358024691358024691358024691358024691358024693e0 * t421 + 0.28812345679012345679012345679012345679012345679012e0 * t424), 0.62200000000000000000000000000000000000000000000002e-1 * t73 + 0.17283950617283950617283950617283950617283950617285e-2 * t432 - 0.74444444444444444444444444444444444444444444444442e-2 * t424)
  t459 = t350 ** 2
  t466 = t220 ** 2
  t469 = t436 - 0.3640e4 / 0.27e2 * t370 * t219 * t232 + 0.4e1 * t331 * t336 + 0.4e1 * t382 * t360 + 0.6e1 * t379 * t364 + 0.140e3 / 0.3e1 * t356 * t220 * t232 + 0.4e1 * t222 * t336 - 0.28e2 * t236 * t336 - 0.28e2 * t351 * t336 + 0.6e1 * t376 * t364 - 0.28e2 * t334 * t364 + 0.3e1 * t154 * t459 * t232 - 0.28e2 / 0.3e1 * t235 * t221 * t232 + t154 * t466 * t232
  t504 = t266 ** 2
  t510 = t275 ** 2
  t524 = (0.70e2 / 0.81e2 * t157 * t420 + 0.220e3 / 0.81e2 * t161 * t417) * t177 - 0.4e1 * t295 * t198 * t207 + 0.12e2 * t258 * t264 * t266 - 0.6e1 * t297 * t275 - 0.24e2 * t195 * t306 * t308 + 0.24e2 * t300 * t311 - 0.4e1 * t260 * t320 + 0.24e2 * t165 / t305 / t176 * t504 - 0.36e2 * t307 * t266 * t275 + 0.6e1 * t265 * t510 + 0.8e1 * t265 * t207 * t320 - t199 * (0.70e2 / 0.81e2 * t166 * t420 + 0.220e3 / 0.81e2 * t169 * t417 + 0.18000000000000000000000000000000000000000000000000e6 * t172 * t412)
  t530 = t113 ** 2
  t536 = t123 ** 2
  t554 = f.my_piecewise3(t12, -0.20232e1 / t108 / t106 * t530 + 0.30348e1 * t109 * t113 * t123 - 0.5058e0 * t118 * t536 - 0.6744e0 * t119 * t131 + 0.843e-1 * t126 * (-0.38836111111111111111111111111111111111111111111110e0 * t410 + 0.37282666666666666666666666666666666666666666666666e1 * t413 - 0.13808395061728395061728395061728395061728395061728e1 * t418 + 0.12082345679012345679012345679012345679012345679012e1 * t421 + 0.22564197530864197530864197530864197530864197530864e0 * t424), 0.31100000000000000000000000000000000000000000000001e-1 * t73 + 0.60493827160493827160493827160493827160493827160493e-3 * t432 - 0.32450617283950617283950617283950617283950617283951e-2 * t424)
  t566 = t242 ** 2
  t583 = t277 ** 2
  t608 = -0.24e2 * t156 / t239 / t179 * t187 * t566 - 0.28e2 * t241 * t250 * t243 + 0.36e2 * t241 * t187 * t242 * t277 - 0.91e2 / 0.3e1 * t249 * t284 * t242 + 0.28e2 * t249 * t250 * t278 - 0.6e1 * t249 * t187 * t583 - 0.8e1 * t249 * t187 * t209 * t322 - 0.1729e4 / 0.54e2 * t182 * t183 * t326 * t209 + 0.91e2 / 0.6e1 * t182 * t284 * t277 - 0.14e2 / 0.3e1 * t182 * t250 * t322 + t182 * t187 * t524 - 0.43225e5 / 0.1296e4 * t156 * t213 / t184 / t367
  t628 = -0.28e2 / 0.3e1 * t235 * t360 - 0.3640e4 / 0.27e2 * t370 * t336 + 0.14560e5 / 0.81e2 * s0 / t7 / t72 / t45 * t232 + t154 * t225 * t524 * t231 + (t554 - t436) * t146 * t151 + 0.140e3 / 0.3e1 * t356 * t364 - 0.28e2 / 0.3e1 * t235 * t330 * t232 + t154 * t608 * t232 + 0.280e3 / 0.3e1 * t373 * t336 + 0.140e3 / 0.3e1 * t356 * t350 * t232 + 0.12e2 * t379 * t385 * t209 * t231 + 0.6e1 * t379 * t220 * t225 * t386 + 0.4e1 * t331 * t387 - 0.28e2 * t351 * t387
  v4rho4_0_ = 0.4e1 * t102 + 0.4e1 * (t139 - t102) * t146 * t151 + 0.4e1 * t222 * t232 - 0.28e2 * t236 * t232 + 0.4e1 * t331 * t232 - 0.56e2 * t334 * t336 - 0.28e2 * t351 * t232 + 0.280e3 / 0.3e1 * t356 * t336 + 0.4e1 * t154 * t360 - 0.28e2 * t235 * t364 - 0.3640e4 / 0.27e2 * t370 * t232 + 0.280e3 / 0.3e1 * t373 * t232 + 0.12e2 * t376 * t336 + 0.12e2 * t379 * t336 + 0.12e2 * t382 * t364 + 0.12e2 * t379 * t387 + r0 * (t469 + t628)

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
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
  t12 = t11 / 0.4e1
  t13 = 0.1e1 <= t12
  t14 = jnp.sqrt(t11)
  t17 = 0.1e1 + 0.52645000000000000000000000000000000000000000000000e0 * t14 + 0.83350000000000000000000000000000000000000000000000e-1 * t11
  t18 = t17 ** 2
  t19 = 0.1e1 / t18
  t21 = 0.1e1 / t14 * t1
  t22 = t3 * t6
  t24 = 0.1e1 / t8 / t7
  t25 = t22 * t24
  t26 = t21 * t25
  t28 = t6 * t24
  t29 = t4 * t28
  t31 = -0.87741666666666666666666666666666666666666666666667e-1 * t26 - 0.27783333333333333333333333333333333333333333333333e-1 * t29
  t34 = 0.1e1 / t7
  t36 = jnp.log(t12)
  t38 = t4 * t28 * t36
  t42 = f.my_piecewise3(t13, 0.1423e0 * t19 * t31, -0.10366666666666666666666666666666666666666666666667e-1 * t34 - 0.16666666666666666666666666666666666666666666666667e-3 * t38 + 0.80000000000000000000000000000000000000000000000000e-3 * t29)
  t43 = 0.2e1 * t42
  t46 = 0.1e1 + 0.69905000000000000000000000000000000000000000000000e0 * t14 + 0.65275000000000000000000000000000000000000000000000e-1 * t11
  t47 = t46 ** 2
  t48 = 0.1e1 / t47
  t51 = -0.11650833333333333333333333333333333333333333333333e0 * t26 - 0.21758333333333333333333333333333333333333333333333e-1 * t29
  t58 = f.my_piecewise3(t13, 0.843e-1 * t48 * t51, -0.51833333333333333333333333333333333333333333333333e-2 * t34 - 0.58333333333333333333333333333333333333333333333333e-4 * t38 + 0.34166666666666666666666666666666666666666666666667e-3 * t29)
  t59 = t58 - t42
  t60 = r0 - r1
  t61 = t60 * t34
  t62 = 0.1e1 + t61
  t63 = t62 <= f.p.zeta_threshold
  t64 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t65 = t64 * f.p.zeta_threshold
  t66 = t62 ** (0.1e1 / 0.3e1)
  t68 = f.my_piecewise3(t63, t65, t66 * t62)
  t69 = 0.1e1 - t61
  t70 = t69 <= f.p.zeta_threshold
  t71 = t69 ** (0.1e1 / 0.3e1)
  t73 = f.my_piecewise3(t70, t65, t71 * t69)
  t74 = t68 + t73 - 0.2e1
  t76 = 2 ** (0.1e1 / 0.3e1)
  t79 = 0.1e1 / (0.2e1 * t76 - 0.2e1)
  t81 = 0.2e1 * t59 * t74 * t79
  t86 = t4 * t10 * t36
  t90 = f.my_piecewise3(t13, -0.843e-1 / t46, 0.1555e-1 * t36 - 0.269e-1 + 0.17500000000000000000000000000000000000000000000000e-3 * t86 - 0.12000000000000000000000000000000000000000000000000e-2 * t11)
  t97 = f.my_piecewise3(t13, -0.1423e0 / t17, 0.311e-1 * t36 - 0.48e-1 + 0.50000000000000000000000000000000000000000000000000e-3 * t86 - 0.29000000000000000000000000000000000000000000000000e-2 * t11)
  t98 = t90 - t97
  t99 = t7 ** 2
  t100 = 0.1e1 / t99
  t101 = t60 * t100
  t102 = t34 - t101
  t105 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t66 * t102)
  t106 = -t102
  t109 = f.my_piecewise3(t70, 0, 0.4e1 / 0.3e1 * t71 * t106)
  t110 = t105 + t109
  t112 = t98 * t110 * t79
  t115 = s0 + 0.2e1 * s1 + s2
  t116 = t99 * t7
  t119 = t115 / t8 / t116
  t121 = params.ftilde * (params.aa + params.bb)
  t122 = params.malpha * t1
  t123 = t22 * t9
  t126 = t1 ** 2
  t127 = params.mbeta * t126
  t128 = t3 ** 2
  t129 = t128 * t5
  t130 = t8 ** 2
  t132 = t129 / t130
  t135 = params.bb + t122 * t123 / 0.4e1 + t127 * t132 / 0.4e1
  t136 = params.mgamma * t1
  t139 = params.mdelta * t126
  t142 = params.mbeta * t2
  t145 = 0.1e1 + t136 * t123 / 0.4e1 + t139 * t132 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t142 * t34
  t146 = 0.1e1 / t145
  t148 = t135 * t146 + params.aa
  t150 = jnp.sqrt(t115)
  t151 = 0.1e1 / t148 * t150
  t152 = t7 ** (0.1e1 / 0.6e1)
  t154 = 0.1e1 / t152 / t7
  t157 = jnp.exp(-t121 * t151 * t154)
  t158 = t119 * t157
  t159 = t64 ** 2
  t160 = t159 * f.p.zeta_threshold
  t161 = t66 ** 2
  t163 = f.my_piecewise3(t63, t160, t161 * t62)
  t164 = t71 ** 2
  t166 = f.my_piecewise3(t70, t160, t164 * t69)
  t167 = t163 + t166
  t168 = jnp.sqrt(t167)
  t169 = 0.1e1 / t168
  t171 = jnp.sqrt(0.2e1)
  t172 = t148 * t169 * t171
  t174 = 0.14e2 / 0.3e1 * t158 * t172
  t176 = 0.1e1 / t8 / t99
  t177 = t115 * t176
  t178 = t148 ** 2
  t180 = t121 / t178
  t181 = t150 * t154
  t186 = t129 / t130 / t7
  t189 = -t122 * t25 / 0.12e2 - t127 * t186 / 0.6e1
  t191 = t145 ** 2
  t192 = 0.1e1 / t191
  t193 = t135 * t192
  t200 = -t136 * t25 / 0.12e2 - t139 * t186 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t142 * t100
  t202 = t189 * t146 - t193 * t200
  t206 = 0.1e1 / t152 / t99
  t210 = t180 * t181 * t202 + 0.7e1 / 0.6e1 * t121 * t151 * t206
  t211 = t177 * t210
  t212 = t157 * t148
  t213 = t169 * t171
  t214 = t212 * t213
  t216 = 0.2e1 * t211 * t214
  t217 = t177 * t157
  t219 = t202 * t169 * t171
  t221 = 0.2e1 * t217 * t219
  t223 = 0.1e1 / t168 / t167
  t224 = t148 * t223
  t227 = f.my_piecewise3(t63, 0, 0.5e1 / 0.3e1 * t161 * t102)
  t230 = f.my_piecewise3(t70, 0, 0.5e1 / 0.3e1 * t164 * t106)
  t231 = t227 + t230
  t232 = t171 * t231
  t233 = t224 * t232
  t234 = t217 * t233
  t237 = t31 ** 2
  t245 = t129 / t130 / t99
  t246 = 0.1e1 / t14 / t11 * t126 * t245
  t248 = t22 * t176
  t249 = t21 * t248
  t251 = t6 * t176
  t252 = t4 * t251
  t260 = t4 * t251 * t36
  t264 = f.my_piecewise3(t13, -0.2846e0 / t18 / t17 * t237 + 0.1423e0 * t19 * (-0.58494444444444444444444444444444444444444444444445e-1 * t246 + 0.11698888888888888888888888888888888888888888888889e0 * t249 + 0.37044444444444444444444444444444444444444444444444e-1 * t252), 0.10366666666666666666666666666666666666666666666667e-1 * t100 + 0.22222222222222222222222222222222222222222222222223e-3 * t260 - 0.10111111111111111111111111111111111111111111111111e-2 * t252)
  t267 = t51 ** 2
  t281 = f.my_piecewise3(t13, -0.1686e0 / t47 / t46 * t267 + 0.843e-1 * t48 * (-0.77672222222222222222222222222222222222222222222220e-1 * t246 + 0.15534444444444444444444444444444444444444444444444e0 * t249 + 0.29011111111111111111111111111111111111111111111111e-1 * t252), 0.51833333333333333333333333333333333333333333333333e-2 * t100 + 0.77777777777777777777777777777777777777777777777777e-4 * t260 - 0.43611111111111111111111111111111111111111111111112e-3 * t252)
  t284 = (t281 - t264) * t74 * t79
  t286 = t59 * t110 * t79
  t288 = 0.1e1 / t161
  t289 = t102 ** 2
  t292 = 0.1e1 / t116
  t293 = t60 * t292
  t295 = -0.2e1 * t100 + 0.2e1 * t293
  t299 = f.my_piecewise3(t63, 0, 0.4e1 / 0.9e1 * t288 * t289 + 0.4e1 / 0.3e1 * t66 * t295)
  t300 = 0.1e1 / t164
  t301 = t106 ** 2
  t304 = -t295
  t308 = f.my_piecewise3(t70, 0, 0.4e1 / 0.9e1 * t300 * t301 + 0.4e1 / 0.3e1 * t71 * t304)
  t312 = t99 ** 2
  t318 = 0.70e2 / 0.9e1 * t115 / t8 / t312 * t157 * t172
  t321 = 0.14e2 / 0.3e1 * t119 * t210 * t214
  t323 = 0.14e2 / 0.3e1 * t158 * t219
  t324 = t158 * t233
  t329 = t202 ** 2
  t349 = t200 ** 2
  t360 = (t122 * t248 / 0.9e1 + 0.5e1 / 0.18e2 * t127 * t245) * t146 - 0.2e1 * t189 * t192 * t200 + 0.2e1 * t135 / t191 / t145 * t349 - t193 * (t136 * t248 / 0.9e1 + 0.5e1 / 0.18e2 * t139 * t245 + 0.15000000000000000000000000000000000000000000000000e5 * t142 * t292)
  t370 = t177 * (-0.2e1 * t121 / t178 / t148 * t181 * t329 - 0.7e1 / 0.3e1 * t180 * t150 * t206 * t202 + t180 * t181 * t360 - 0.91e2 / 0.36e2 * t121 * t151 / t152 / t116) * t214
  t371 = t210 ** 2
  t373 = t177 * t371 * t214
  t377 = 0.2e1 * t211 * t157 * t202 * t213
  t379 = t177 * t210 * t157
  t380 = t379 * t233
  t383 = t217 * t360 * t169 * t171
  t384 = t202 * t223
  t386 = t217 * t384 * t232
  t387 = t167 ** 2
  t389 = 0.1e1 / t168 / t387
  t390 = t148 * t389
  t391 = t231 ** 2
  t396 = 0.1e1 / t66
  t402 = f.my_piecewise3(t63, 0, 0.10e2 / 0.9e1 * t396 * t289 + 0.5e1 / 0.3e1 * t161 * t295)
  t403 = 0.1e1 / t71
  t409 = f.my_piecewise3(t70, 0, 0.10e2 / 0.9e1 * t403 * t301 + 0.5e1 / 0.3e1 * t164 * t304)
  t415 = t264 + t284 + 0.2e1 * t286 + t98 * (t299 + t308) * t79 + t318 - t321 - t323 + 0.7e1 / 0.3e1 * t324 + t370 + t373 + t377 - t380 + t383 - t386 + 0.3e1 / 0.4e1 * t217 * t390 * t171 * t391 - t217 * t224 * t171 * (t402 + t409) / 0.2e1
  d11 = t7 * t415 + 0.2e1 * t112 - t174 + t216 + t221 - t234 + t43 + t81
  t418 = -t34 - t101
  t421 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t66 * t418)
  t422 = -t418
  t425 = f.my_piecewise3(t70, 0, 0.4e1 / 0.3e1 * t71 * t422)
  t426 = t421 + t425
  t428 = t98 * t426 * t79
  t431 = f.my_piecewise3(t63, 0, 0.5e1 / 0.3e1 * t161 * t418)
  t434 = f.my_piecewise3(t70, 0, 0.5e1 / 0.3e1 * t164 * t422)
  t435 = t431 + t434
  t436 = t171 * t435
  t437 = t224 * t436
  t438 = t217 * t437
  t441 = t59 * t426 * t79
  t449 = f.my_piecewise3(t63, 0, 0.4e1 / 0.9e1 * t288 * t418 * t102 + 0.8e1 / 0.3e1 * t66 * t60 * t292)
  t457 = f.my_piecewise3(t70, 0, 0.4e1 / 0.9e1 * t300 * t422 * t106 - 0.8e1 / 0.3e1 * t71 * t60 * t292)
  t464 = t158 * t437
  t466 = t379 * t437
  t469 = t217 * t384 * t436
  t484 = f.my_piecewise3(t63, 0, 0.10e2 / 0.9e1 * t396 * t418 * t102 + 0.10e2 / 0.3e1 * t161 * t60 * t292)
  t492 = f.my_piecewise3(t70, 0, 0.10e2 / 0.9e1 * t403 * t422 * t106 - 0.10e2 / 0.3e1 * t164 * t60 * t292)
  t498 = t264 + t284 + t286 + t441 + t98 * (t449 + t457) * t79 + t318 - t321 - t323 + 0.7e1 / 0.6e1 * t324 + t370 + t373 + t377 - t380 / 0.2e1 + t383 - t386 / 0.2e1 + 0.7e1 / 0.6e1 * t464 - t466 / 0.2e1 - t469 / 0.2e1 + 0.3e1 / 0.4e1 * t177 * t212 * t389 * t171 * t435 * t231 - t217 * t224 * t171 * (t484 + t492) / 0.2e1
  d12 = t43 + t81 + t112 - t174 + t216 + t221 - t234 / 0.2e1 + t428 - t438 / 0.2e1 + t7 * t498
  t502 = t418 ** 2
  t506 = 0.2e1 * t100 + 0.2e1 * t293
  t510 = f.my_piecewise3(t63, 0, 0.4e1 / 0.9e1 * t288 * t502 + 0.4e1 / 0.3e1 * t66 * t506)
  t511 = t422 ** 2
  t514 = -t506
  t518 = f.my_piecewise3(t70, 0, 0.4e1 / 0.9e1 * t300 * t511 + 0.4e1 / 0.3e1 * t71 * t514)
  t523 = t435 ** 2
  t533 = f.my_piecewise3(t63, 0, 0.10e2 / 0.9e1 * t396 * t502 + 0.5e1 / 0.3e1 * t161 * t506)
  t539 = f.my_piecewise3(t70, 0, 0.10e2 / 0.9e1 * t403 * t511 + 0.5e1 / 0.3e1 * t164 * t514)
  t545 = t264 + t284 + 0.2e1 * t441 + t98 * (t510 + t518) * t79 + t318 - t321 - t323 + 0.7e1 / 0.3e1 * t464 + t370 + t373 + t377 - t466 + t383 - t469 + 0.3e1 / 0.4e1 * t217 * t390 * t171 * t523 - t217 * t224 * t171 * (t533 + t539) / 0.2e1
  d22 = t7 * t545 - t174 + t216 + t221 + 0.2e1 * t428 + t43 - t438 + t81
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

  t1 = r0 + r1
  t3 = s0 + 0.2e1 * s1 + s2
  t4 = t1 ** 2
  t5 = t4 * t1
  t6 = t1 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t6 / t5
  t9 = t3 * t8
  t11 = params.ftilde * (params.aa + params.bb)
  t12 = 3 ** (0.1e1 / 0.3e1)
  t13 = params.malpha * t12
  t14 = 0.1e1 / jnp.pi
  t15 = t14 ** (0.1e1 / 0.3e1)
  t16 = 4 ** (0.1e1 / 0.3e1)
  t17 = t16 ** 2
  t18 = t15 * t17
  t19 = 0.1e1 / t6
  t20 = t18 * t19
  t23 = t12 ** 2
  t24 = params.mbeta * t23
  t25 = t15 ** 2
  t26 = t25 * t16
  t27 = t6 ** 2
  t28 = 0.1e1 / t27
  t29 = t26 * t28
  t32 = params.bb + t13 * t20 / 0.4e1 + t24 * t29 / 0.4e1
  t33 = params.mgamma * t12
  t36 = params.mdelta * t23
  t39 = params.mbeta * t14
  t40 = 0.1e1 / t1
  t43 = 0.1e1 + t33 * t20 / 0.4e1 + t36 * t29 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t39 * t40
  t44 = 0.1e1 / t43
  t46 = t32 * t44 + params.aa
  t48 = jnp.sqrt(t3)
  t49 = 0.1e1 / t46 * t48
  t50 = t1 ** (0.1e1 / 0.6e1)
  t52 = 0.1e1 / t50 / t1
  t55 = jnp.exp(-t11 * t49 * t52)
  t56 = t9 * t55
  t58 = 0.1e1 / t6 / t4
  t59 = t18 * t58
  t64 = t26 / t27 / t4
  t67 = t13 * t59 / 0.9e1 + 0.5e1 / 0.18e2 * t24 * t64
  t70 = 0.1e1 / t6 / t1
  t71 = t18 * t70
  t76 = t26 / t27 / t1
  t79 = -t13 * t71 / 0.12e2 - t24 * t76 / 0.6e1
  t80 = t43 ** 2
  t81 = 0.1e1 / t80
  t82 = t79 * t81
  t87 = 0.1e1 / t4
  t90 = -t33 * t71 / 0.12e2 - t36 * t76 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t39 * t87
  t94 = 0.1e1 / t80 / t43
  t95 = t32 * t94
  t96 = t90 ** 2
  t99 = t32 * t81
  t104 = 0.1e1 / t5
  t107 = t33 * t59 / 0.9e1 + 0.5e1 / 0.18e2 * t36 * t64 + 0.15000000000000000000000000000000000000000000000000e5 * t39 * t104
  t109 = -t99 * t107 + t67 * t44 - 0.2e1 * t82 * t90 + 0.2e1 * t95 * t96
  t110 = r0 - r1
  t111 = t110 * t40
  t112 = 0.1e1 + t111
  t113 = t112 <= f.p.zeta_threshold
  t114 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t115 = t114 ** 2
  t116 = t115 * f.p.zeta_threshold
  t117 = t112 ** (0.1e1 / 0.3e1)
  t118 = t117 ** 2
  t119 = t118 * t112
  t120 = f.my_piecewise3(t113, t116, t119)
  t121 = 0.1e1 - t111
  t122 = t121 <= f.p.zeta_threshold
  t123 = t121 ** (0.1e1 / 0.3e1)
  t124 = t123 ** 2
  t125 = t124 * t121
  t126 = f.my_piecewise3(t122, t116, t125)
  t127 = t120 + t126
  t128 = jnp.sqrt(t127)
  t129 = 0.1e1 / t128
  t131 = jnp.sqrt(0.2e1)
  t132 = t109 * t129 * t131
  t135 = t3 * t58
  t136 = t135 * t55
  t137 = t18 * t8
  t142 = t26 / t27 / t5
  t155 = t80 ** 2
  t168 = t4 ** 2
  t169 = 0.1e1 / t168
  t174 = (-0.7e1 / 0.27e2 * t13 * t137 - 0.20e2 / 0.27e2 * t24 * t142) * t44 - 0.3e1 * t67 * t81 * t90 + 0.6e1 * t79 * t94 * t96 - 0.3e1 * t82 * t107 - 0.6e1 * t32 / t155 * t96 * t90 + 0.6e1 * t95 * t90 * t107 - t99 * (-0.7e1 / 0.27e2 * t33 * t137 - 0.20e2 / 0.27e2 * t36 * t142 - 0.45000000000000000000000000000000000000000000000000e5 * t39 * t169)
  t178 = t12 * t15
  t179 = t17 * t19
  t180 = t178 * t179
  t181 = t180 / 0.4e1
  t182 = 0.1e1 <= t181
  t183 = jnp.sqrt(t180)
  t186 = 0.1e1 + 0.52645000000000000000000000000000000000000000000000e0 * t183 + 0.83350000000000000000000000000000000000000000000000e-1 * t180
  t187 = t186 ** 2
  t188 = t187 ** 2
  t191 = 0.1e1 / t183 * t12
  t192 = t191 * t71
  t194 = t17 * t70
  t195 = t178 * t194
  t197 = -0.87741666666666666666666666666666666666666666666667e-1 * t192 - 0.27783333333333333333333333333333333333333333333333e-1 * t195
  t198 = t197 ** 2
  t203 = 0.1e1 / t187 / t186
  t207 = 0.1e1 / t183 / t180 * t23
  t208 = t207 * t64
  t210 = t191 * t59
  t212 = t17 * t58
  t213 = t178 * t212
  t215 = -0.58494444444444444444444444444444444444444444444445e-1 * t208 + 0.11698888888888888888888888888888888888888888888889e0 * t210 + 0.37044444444444444444444444444444444444444444444444e-1 * t213
  t218 = 0.1e1 / t187
  t226 = 0.1e1 / t183 / t23 / t25 / t16 / t28 * t14 * t169 / 0.4e1
  t228 = t207 * t142
  t230 = t191 * t137
  t232 = t17 * t8
  t233 = t178 * t232
  t240 = jnp.log(t181)
  t242 = t178 * t232 * t240
  t246 = f.my_piecewise3(t182, 0.8538e0 / t188 * t198 * t197 - 0.8538e0 * t203 * t197 * t215 + 0.1423e0 * t218 * (-0.35096666666666666666666666666666666666666666666667e0 * t226 + 0.23397777777777777777777777777777777777777777777778e0 * t228 - 0.27297407407407407407407407407407407407407407407408e0 * t230 - 0.86437037037037037037037037037037037037037037037036e-1 * t233), -0.20733333333333333333333333333333333333333333333334e-1 * t104 - 0.51851851851851851851851851851851851851851851851854e-3 * t242 + 0.22851851851851851851851851851851851851851851851851e-2 * t233)
  t249 = 0.1e1 + 0.69905000000000000000000000000000000000000000000000e0 * t183 + 0.65275000000000000000000000000000000000000000000000e-1 * t180
  t250 = t249 ** 2
  t251 = 0.1e1 / t250
  t254 = -0.11650833333333333333333333333333333333333333333333e0 * t192 - 0.21758333333333333333333333333333333333333333333333e-1 * t195
  t259 = t178 * t194 * t240
  t263 = f.my_piecewise3(t182, 0.843e-1 * t251 * t254, -0.51833333333333333333333333333333333333333333333333e-2 * t40 - 0.58333333333333333333333333333333333333333333333333e-4 * t259 + 0.34166666666666666666666666666666666666666666666667e-3 * t195)
  t270 = f.my_piecewise3(t182, 0.1423e0 * t218 * t197, -0.10366666666666666666666666666666666666666666666667e-1 * t40 - 0.16666666666666666666666666666666666666666666666667e-3 * t259 + 0.80000000000000000000000000000000000000000000000000e-3 * t195)
  t271 = t263 - t270
  t272 = 0.1e1 / t118
  t274 = -t110 * t87 + t40
  t275 = t274 ** 2
  t280 = 0.2e1 * t110 * t104 - 0.2e1 * t87
  t284 = f.my_piecewise3(t113, 0, 0.4e1 / 0.9e1 * t272 * t275 + 0.4e1 / 0.3e1 * t117 * t280)
  t285 = 0.1e1 / t124
  t286 = -t274
  t287 = t286 ** 2
  t290 = -t280
  t294 = f.my_piecewise3(t122, 0, 0.4e1 / 0.9e1 * t285 * t287 + 0.4e1 / 0.3e1 * t123 * t290)
  t295 = t284 + t294
  t297 = 2 ** (0.1e1 / 0.3e1)
  t300 = 0.1e1 / (0.2e1 * t297 - 0.2e1)
  t307 = t178 * t179 * t240
  t311 = f.my_piecewise3(t182, -0.843e-1 / t249, 0.1555e-1 * t240 - 0.269e-1 + 0.17500000000000000000000000000000000000000000000000e-3 * t307 - 0.12000000000000000000000000000000000000000000000000e-2 * t180)
  t318 = f.my_piecewise3(t182, -0.1423e0 / t186, 0.311e-1 * t240 - 0.48e-1 + 0.50000000000000000000000000000000000000000000000000e-3 * t307 - 0.29000000000000000000000000000000000000000000000000e-2 * t180)
  t319 = t311 - t318
  t321 = t275 * t274
  t329 = -0.6e1 * t110 * t169 + 0.6e1 * t104
  t333 = f.my_piecewise3(t113, 0, -0.8e1 / 0.27e2 / t119 * t321 + 0.4e1 / 0.3e1 * t272 * t274 * t280 + 0.4e1 / 0.3e1 * t117 * t329)
  t335 = t287 * t286
  t341 = -t329
  t345 = f.my_piecewise3(t122, 0, -0.8e1 / 0.27e2 / t125 * t335 + 0.4e1 / 0.3e1 * t285 * t286 * t290 + 0.4e1 / 0.3e1 * t123 * t341)
  t350 = 0.1e1 / t250 / t249
  t351 = t254 ** 2
  t357 = -0.77672222222222222222222222222222222222222222222220e-1 * t208 + 0.15534444444444444444444444444444444444444444444444e0 * t210 + 0.29011111111111111111111111111111111111111111111111e-1 * t213
  t363 = t178 * t212 * t240
  t367 = f.my_piecewise3(t182, -0.1686e0 * t350 * t351 + 0.843e-1 * t251 * t357, 0.51833333333333333333333333333333333333333333333333e-2 * t87 + 0.77777777777777777777777777777777777777777777777777e-4 * t363 - 0.43611111111111111111111111111111111111111111111112e-3 * t213)
  t377 = f.my_piecewise3(t182, -0.2846e0 * t203 * t198 + 0.1423e0 * t218 * t215, 0.10366666666666666666666666666666666666666666666667e-1 * t87 + 0.22222222222222222222222222222222222222222222222223e-3 * t363 - 0.10111111111111111111111111111111111111111111111111e-2 * t213)
  t378 = t367 - t377
  t381 = f.my_piecewise3(t113, 0, 0.4e1 / 0.3e1 * t117 * t274)
  t384 = f.my_piecewise3(t122, 0, 0.4e1 / 0.3e1 * t123 * t286)
  t385 = t381 + t384
  t389 = t250 ** 2
  t409 = f.my_piecewise3(t182, 0.5058e0 / t389 * t351 * t254 - 0.5058e0 * t350 * t254 * t357 + 0.843e-1 * t251 * (-0.46603333333333333333333333333333333333333333333332e0 * t226 + 0.31068888888888888888888888888888888888888888888888e0 * t228 - 0.36247037037037037037037037037037037037037037037036e0 * t230 - 0.67692592592592592592592592592592592592592592592592e-1 * t233), -0.10366666666666666666666666666666666666666666666667e-1 * t104 - 0.18148148148148148148148148148148148148148148148148e-3 * t242 + 0.99166666666666666666666666666666666666666666666667e-3 * t233)
  t411 = t114 * f.p.zeta_threshold
  t412 = t117 * t112
  t413 = f.my_piecewise3(t113, t411, t412)
  t414 = t123 * t121
  t415 = f.my_piecewise3(t122, t411, t414)
  t416 = t413 + t415 - 0.2e1
  t419 = t55 * t46
  t421 = t127 ** 2
  t423 = 0.1e1 / t128 / t421
  t427 = f.my_piecewise3(t113, 0, 0.5e1 / 0.3e1 * t118 * t274)
  t430 = f.my_piecewise3(t122, 0, 0.5e1 / 0.3e1 * t124 * t286)
  t431 = t427 + t430
  t432 = 0.1e1 / t117
  t438 = f.my_piecewise3(t113, 0, 0.10e2 / 0.9e1 * t432 * t275 + 0.5e1 / 0.3e1 * t118 * t280)
  t439 = 0.1e1 / t123
  t445 = f.my_piecewise3(t122, 0, 0.10e2 / 0.9e1 * t439 * t287 + 0.5e1 / 0.3e1 * t124 * t290)
  t446 = t438 + t445
  t451 = t46 ** 2
  t453 = t11 / t451
  t454 = t48 * t52
  t457 = t79 * t44 - t99 * t90
  t461 = 0.1e1 / t50 / t4
  t465 = t453 * t454 * t457 + 0.7e1 / 0.6e1 * t11 * t49 * t461
  t466 = t465 * t55
  t467 = t135 * t466
  t469 = t431 ** 2
  t470 = t131 * t469
  t471 = t46 * t423 * t470
  t476 = 0.1e1 / t128 / t127
  t477 = t46 * t476
  t478 = t131 * t431
  t479 = t477 * t478
  t484 = t11 / t451 / t46
  t485 = t457 ** 2
  t489 = t48 * t461
  t496 = 0.1e1 / t50 / t5
  t500 = -0.2e1 * t484 * t454 * t485 - 0.7e1 / 0.3e1 * t453 * t489 * t457 + t453 * t454 * t109 - 0.91e2 / 0.36e2 * t11 * t49 * t496
  t507 = t129 * t131
  t508 = t419 * t507
  t511 = t465 ** 2
  t516 = t457 * t476
  t517 = t516 * t478
  t520 = t131 * t446
  t521 = t477 * t520
  t529 = -0.7e1 * t56 * t132 + t136 * t174 * t129 * t131 + t246 + 0.3e1 * t271 * t295 * t300 + t319 * (t333 + t345) * t300 + 0.3e1 * t378 * t385 * t300 + (t409 - t246) * t416 * t300 + 0.9e1 / 0.4e1 * t135 * t419 * t423 * t131 * t431 * t446 + 0.9e1 / 0.4e1 * t467 * t471 + 0.7e1 * t9 * t466 * t479 - 0.3e1 / 0.2e1 * t135 * t500 * t55 * t479 + 0.3e1 * t135 * t500 * t465 * t508 - 0.3e1 / 0.2e1 * t135 * t511 * t55 * t479 - 0.3e1 * t467 * t517 - 0.3e1 / 0.2e1 * t467 * t521 - 0.7e1 * t9 * t511 * t508 - 0.21e2 / 0.4e1 * t56 * t471
  t548 = t3 / t6 / t168
  t549 = t548 * t55
  t567 = f.my_piecewise3(t113, 0, -0.10e2 / 0.27e2 / t412 * t321 + 0.10e2 / 0.3e1 * t432 * t274 * t280 + 0.5e1 / 0.3e1 * t118 * t329)
  t577 = f.my_piecewise3(t122, 0, -0.10e2 / 0.27e2 / t414 * t335 + 0.10e2 / 0.3e1 * t439 * t286 * t290 + 0.5e1 / 0.3e1 * t124 * t341)
  t590 = t135 * t465
  t595 = t135 * t511
  t597 = t55 * t457 * t507
  t600 = t135 * t500
  t605 = t451 ** 2
  t638 = t9 * t465
  t642 = t457 * t129 * t131
  t651 = t46 * t129 * t131
  t654 = t135 * t511 * t465 * t508 + 0.9e1 / 0.4e1 * t136 * t457 * t423 * t470 - 0.15e2 / 0.8e1 * t136 * t46 / t128 / t421 / t127 * t131 * t469 * t431 - 0.35e2 / 0.3e1 * t549 * t479 + 0.70e2 / 0.3e1 * t548 * t465 * t508 - 0.7e1 * t9 * t500 * t508 - t136 * t477 * t131 * (t567 + t577) / 0.2e1 - 0.3e1 / 0.2e1 * t136 * t516 * t520 - 0.3e1 / 0.2e1 * t136 * t109 * t476 * t478 + 0.3e1 * t590 * t55 * t109 * t507 + 0.3e1 * t595 * t597 + 0.3e1 * t600 * t597 + 0.7e1 / 0.2e1 * t56 * t521 + t135 * (0.6e1 * t11 / t605 * t454 * t485 * t457 + 0.7e1 * t484 * t489 * t485 - 0.6e1 * t484 * t454 * t457 * t109 + 0.91e2 / 0.12e2 * t453 * t48 * t496 * t457 - 0.7e1 / 0.2e1 * t453 * t489 * t109 + t453 * t454 * t174 + 0.1729e4 / 0.216e3 * t11 * t49 / t50 / t168) * t508 + 0.7e1 * t56 * t517 - 0.14e2 * t638 * t597 + 0.70e2 / 0.3e1 * t549 * t642 - 0.910e3 / 0.27e2 * t3 / t6 / t168 / t1 * t55 * t651
  d111 = t1 * (t529 + t654) + 0.3e1 * t136 * t132 - 0.14e2 * t56 * t642 + 0.3e1 * t377 + 0.3e1 * t378 * t416 * t300 + 0.6e1 * t271 * t385 * t300 + 0.3e1 * t319 * t295 * t300 + 0.70e2 / 0.3e1 * t549 * t651 - 0.3e1 * t467 * t479 - 0.14e2 * t638 * t508 + 0.7e1 * t56 * t479 + 0.3e1 * t600 * t508 + 0.3e1 * t595 * t508 + 0.6e1 * t590 * t597 - 0.3e1 * t136 * t517 + 0.9e1 / 0.4e1 * t136 * t471 - 0.3e1 / 0.2e1 * t136 * t521

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
  t9 = 0.1e1 / t8
  t10 = t6 * t9
  t11 = t4 * t10
  t12 = t11 / 0.4e1
  t13 = 0.1e1 <= t12
  t14 = jnp.sqrt(t11)
  t17 = 0.1e1 + 0.52645000000000000000000000000000000000000000000000e0 * t14 + 0.83350000000000000000000000000000000000000000000000e-1 * t11
  t18 = t17 ** 2
  t19 = t18 ** 2
  t20 = 0.1e1 / t19
  t22 = 0.1e1 / t14 * t1
  t23 = t3 * t6
  t25 = 0.1e1 / t8 / t7
  t26 = t23 * t25
  t27 = t22 * t26
  t29 = t6 * t25
  t30 = t4 * t29
  t32 = -0.87741666666666666666666666666666666666666666666667e-1 * t27 - 0.27783333333333333333333333333333333333333333333333e-1 * t30
  t33 = t32 ** 2
  t38 = 0.1e1 / t18 / t17
  t39 = t38 * t32
  t42 = t1 ** 2
  t43 = 0.1e1 / t14 / t11 * t42
  t44 = t3 ** 2
  t45 = t44 * t5
  t46 = t7 ** 2
  t47 = t8 ** 2
  t50 = t45 / t47 / t46
  t51 = t43 * t50
  t54 = 0.1e1 / t8 / t46
  t55 = t23 * t54
  t56 = t22 * t55
  t58 = t6 * t54
  t59 = t4 * t58
  t61 = -0.58494444444444444444444444444444444444444444444445e-1 * t51 + 0.11698888888888888888888888888888888888888888888889e0 * t56 + 0.37044444444444444444444444444444444444444444444444e-1 * t59
  t64 = 0.1e1 / t18
  t66 = 0.1e1 / t47
  t72 = 0.1e1 / t14 / t42 / t44 / t5 / t66 * t2 / 0.4e1
  t73 = t46 ** 2
  t74 = 0.1e1 / t73
  t75 = t72 * t74
  t77 = t46 * t7
  t80 = t45 / t47 / t77
  t81 = t43 * t80
  t84 = 0.1e1 / t8 / t77
  t85 = t23 * t84
  t86 = t22 * t85
  t88 = t6 * t84
  t89 = t4 * t88
  t91 = -0.35096666666666666666666666666666666666666666666667e0 * t75 + 0.23397777777777777777777777777777777777777777777778e0 * t81 - 0.27297407407407407407407407407407407407407407407408e0 * t86 - 0.86437037037037037037037037037037037037037037037036e-1 * t89
  t95 = 0.1e1 / t77
  t97 = jnp.log(t12)
  t99 = t4 * t88 * t97
  t103 = f.my_piecewise3(t13, 0.8538e0 * t20 * t33 * t32 - 0.8538e0 * t39 * t61 + 0.1423e0 * t64 * t91, -0.20733333333333333333333333333333333333333333333334e-1 * t95 - 0.51851851851851851851851851851851851851851851851854e-3 * t99 + 0.22851851851851851851851851851851851851851851851851e-2 * t89)
  t106 = s0 + 0.2e1 * s1 + s2
  t107 = t106 * t54
  t109 = params.ftilde * (params.aa + params.bb)
  t110 = params.malpha * t1
  t111 = t23 * t9
  t114 = params.mbeta * t42
  t115 = t45 * t66
  t118 = params.bb + t110 * t111 / 0.4e1 + t114 * t115 / 0.4e1
  t119 = params.mgamma * t1
  t122 = params.mdelta * t42
  t125 = params.mbeta * t2
  t126 = 0.1e1 / t7
  t129 = 0.1e1 + t119 * t111 / 0.4e1 + t122 * t115 / 0.4e1 + 0.75000000000000000000000000000000000000000000000000e4 * t125 * t126
  t130 = 0.1e1 / t129
  t132 = t118 * t130 + params.aa
  t133 = t132 ** 2
  t134 = t133 ** 2
  t136 = t109 / t134
  t137 = jnp.sqrt(t106)
  t138 = t7 ** (0.1e1 / 0.6e1)
  t140 = 0.1e1 / t138 / t7
  t141 = t137 * t140
  t146 = t45 / t47 / t7
  t149 = -t110 * t26 / 0.12e2 - t114 * t146 / 0.6e1
  t151 = t129 ** 2
  t152 = 0.1e1 / t151
  t153 = t118 * t152
  t158 = 0.1e1 / t46
  t161 = -t119 * t26 / 0.12e2 - t122 * t146 / 0.6e1 - 0.75000000000000000000000000000000000000000000000000e4 * t125 * t158
  t163 = t149 * t130 - t153 * t161
  t164 = t163 ** 2
  t165 = t164 * t163
  t171 = t109 / t133 / t132
  t173 = 0.1e1 / t138 / t46
  t174 = t137 * t173
  t182 = t110 * t55 / 0.9e1 + 0.5e1 / 0.18e2 * t114 * t50
  t184 = t149 * t152
  t188 = 0.1e1 / t151 / t129
  t189 = t118 * t188
  t190 = t161 ** 2
  t199 = t119 * t55 / 0.9e1 + 0.5e1 / 0.18e2 * t122 * t50 + 0.15000000000000000000000000000000000000000000000000e5 * t125 * t95
  t201 = t182 * t130 - t153 * t199 - 0.2e1 * t184 * t161 + 0.2e1 * t189 * t190
  t202 = t163 * t201
  t207 = t109 / t133
  t209 = 0.1e1 / t138 / t77
  t210 = t137 * t209
  t221 = -0.7e1 / 0.27e2 * t110 * t85 - 0.20e2 / 0.27e2 * t114 * t80
  t223 = t182 * t152
  t226 = t149 * t188
  t231 = t151 ** 2
  t232 = 0.1e1 / t231
  t233 = t118 * t232
  t234 = t190 * t161
  t237 = t161 * t199
  t246 = -0.7e1 / 0.27e2 * t119 * t85 - 0.20e2 / 0.27e2 * t122 * t80 - 0.45000000000000000000000000000000000000000000000000e5 * t125 * t74
  t248 = t221 * t130 - t153 * t246 - 0.3e1 * t223 * t161 - 0.3e1 * t184 * t199 + 0.6e1 * t189 * t237 + 0.6e1 * t226 * t190 - 0.6e1 * t233 * t234
  t252 = 0.1e1 / t132 * t137
  t254 = 0.1e1 / t138 / t73
  t258 = 0.6e1 * t136 * t141 * t165 + 0.7e1 * t171 * t174 * t164 - 0.6e1 * t171 * t141 * t202 + 0.91e2 / 0.12e2 * t207 * t210 * t163 - 0.7e1 / 0.2e1 * t207 * t174 * t201 + t207 * t141 * t248 + 0.1729e4 / 0.216e3 * t109 * t252 * t254
  t259 = t107 * t258
  t262 = jnp.exp(-t109 * t252 * t140)
  t263 = t262 * t132
  t264 = r0 - r1
  t265 = t264 * t126
  t266 = 0.1e1 + t265
  t267 = t266 <= f.p.zeta_threshold
  t268 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t269 = t268 ** 2
  t270 = t269 * f.p.zeta_threshold
  t271 = t266 ** (0.1e1 / 0.3e1)
  t272 = t271 ** 2
  t273 = t272 * t266
  t274 = f.my_piecewise3(t267, t270, t273)
  t275 = 0.1e1 - t265
  t276 = t275 <= f.p.zeta_threshold
  t277 = t275 ** (0.1e1 / 0.3e1)
  t278 = t277 ** 2
  t279 = t278 * t275
  t280 = f.my_piecewise3(t276, t270, t279)
  t281 = t274 + t280
  t282 = jnp.sqrt(t281)
  t283 = 0.1e1 / t282
  t284 = jnp.sqrt(0.2e1)
  t285 = t283 * t284
  t286 = t263 * t285
  t289 = t106 * t84
  t290 = t289 * t262
  t292 = 0.1e1 / t282 / t281
  t293 = t163 * t292
  t295 = -t264 * t158 + t126
  t298 = f.my_piecewise3(t267, 0, 0.5e1 / 0.3e1 * t272 * t295)
  t299 = -t295
  t302 = f.my_piecewise3(t276, 0, 0.5e1 / 0.3e1 * t278 * t299)
  t303 = t298 + t302
  t304 = t284 * t303
  t305 = t293 * t304
  t313 = t207 * t141 * t163 + 0.7e1 / 0.6e1 * t109 * t252 * t173
  t314 = t289 * t313
  t315 = t262 * t163
  t316 = t315 * t285
  t319 = t313 ** 2
  t320 = t289 * t319
  t323 = t281 ** 2
  t325 = 0.1e1 / t282 / t323
  t326 = t132 * t325
  t327 = t303 ** 2
  t328 = t284 * t327
  t329 = t326 * t328
  t332 = t319 * t313
  t333 = t107 * t332
  t336 = t107 * t262
  t338 = t163 * t325 * t328
  t343 = 0.1e1 / t282 / t323 / t281
  t346 = t284 * t327 * t303
  t347 = t132 * t343 * t346
  t351 = 0.1e1 / t8 / t73
  t352 = t106 * t351
  t353 = t352 * t262
  t354 = t132 * t292
  t355 = t354 * t304
  t358 = t352 * t313
  t372 = -0.2e1 * t171 * t141 * t164 - 0.7e1 / 0.3e1 * t207 * t174 * t163 + t207 * t141 * t201 - 0.91e2 / 0.36e2 * t109 * t252 * t209
  t373 = t289 * t372
  t376 = t271 * t266
  t377 = 0.1e1 / t376
  t378 = t295 ** 2
  t379 = t378 * t295
  t382 = 0.1e1 / t271
  t383 = t382 * t295
  t386 = 0.2e1 * t264 * t95 - 0.2e1 * t158
  t391 = -0.6e1 * t264 * t74 + 0.6e1 * t95
  t395 = f.my_piecewise3(t267, 0, -0.10e2 / 0.27e2 * t377 * t379 + 0.10e2 / 0.3e1 * t383 * t386 + 0.5e1 / 0.3e1 * t272 * t391)
  t396 = t277 * t275
  t397 = 0.1e1 / t396
  t398 = t299 ** 2
  t399 = t398 * t299
  t402 = 0.1e1 / t277
  t403 = t402 * t299
  t404 = -t386
  t407 = -t391
  t411 = f.my_piecewise3(t276, 0, -0.10e2 / 0.27e2 * t397 * t399 + 0.10e2 / 0.3e1 * t403 * t404 + 0.5e1 / 0.3e1 * t278 * t407)
  t412 = t395 + t411
  t413 = t284 * t412
  t414 = t354 * t413
  t422 = f.my_piecewise3(t267, 0, 0.10e2 / 0.9e1 * t382 * t378 + 0.5e1 / 0.3e1 * t272 * t386)
  t428 = f.my_piecewise3(t276, 0, 0.10e2 / 0.9e1 * t402 * t398 + 0.5e1 / 0.3e1 * t278 * t404)
  t429 = t422 + t428
  t430 = t284 * t429
  t431 = t293 * t430
  t434 = t201 * t292
  t435 = t434 * t304
  t438 = t107 * t313
  t440 = t262 * t201 * t285
  t443 = t107 * t319
  t446 = t107 * t372
  t449 = 0.4e1 * t103 + 0.4e1 * t259 * t286 + 0.28e2 * t290 * t305 - 0.56e2 * t314 * t316 - 0.28e2 * t320 * t286 - 0.21e2 * t290 * t329 + 0.4e1 * t333 * t286 + 0.9e1 * t336 * t338 - 0.15e2 / 0.2e1 * t336 * t347 - 0.140e3 / 0.3e1 * t353 * t355 + 0.280e3 / 0.3e1 * t358 * t286 - 0.28e2 * t373 * t286 - 0.2e1 * t336 * t414 - 0.6e1 * t336 * t431 - 0.6e1 * t336 * t435 + 0.12e2 * t438 * t440 + 0.12e2 * t443 * t316 + 0.12e2 * t446 * t316
  t450 = t354 * t430
  t453 = t73 * t7
  t455 = 0.1e1 / t8 / t453
  t456 = t106 * t455
  t457 = t456 * t262
  t458 = t163 * t283
  t459 = t458 * t284
  t463 = t248 * t283 * t284
  t471 = t132 * t283
  t472 = t471 * t284
  t475 = t23 * t351
  t480 = t45 / t47 / t73
  t503 = t190 ** 2
  t509 = t199 ** 2
  t519 = 0.1e1 / t453
  t524 = (0.70e2 / 0.81e2 * t110 * t475 + 0.220e3 / 0.81e2 * t114 * t480) * t130 - 0.4e1 * t221 * t152 * t161 + 0.12e2 * t182 * t188 * t190 - 0.6e1 * t223 * t199 - 0.24e2 * t149 * t232 * t234 + 0.24e2 * t226 * t237 - 0.4e1 * t184 * t246 + 0.24e2 * t118 / t231 / t129 * t503 - 0.36e2 * t233 * t190 * t199 + 0.6e1 * t189 * t509 + 0.8e1 * t189 * t161 * t246 - t153 * (0.70e2 / 0.81e2 * t119 * t475 + 0.220e3 / 0.81e2 * t122 * t480 + 0.18000000000000000000000000000000000000000000000000e6 * t125 * t519)
  t529 = t201 * t283 * t284
  t532 = t313 * t262
  t533 = t107 * t532
  t551 = t323 ** 2
  t555 = t327 ** 2
  t579 = -0.3640e4 / 0.27e2 * t457 * t459 - 0.28e2 / 0.3e1 * t290 * t463 + 0.14560e5 / 0.81e2 * t106 / t8 / t73 / t46 * t262 * t472 + t336 * t524 * t283 * t284 + 0.140e3 / 0.3e1 * t353 * t529 + 0.9e1 * t533 * t326 * t304 * t429 - 0.6e1 * t533 * t354 * t304 * t372 + 0.140e3 / 0.3e1 * t352 * t319 * t286 - 0.15e2 / 0.2e1 * t336 * t163 * t343 * t346 - 0.21e2 * t290 * t338 + 0.105e3 / 0.16e2 * t336 * t132 / t282 / t551 * t284 * t555 + 0.35e2 * t353 * t329 - 0.28e2 / 0.3e1 * t289 * t332 * t286 + 0.35e2 / 0.2e1 * t290 * t347 + 0.14e2 / 0.3e1 * t290 * t414 + 0.6e1 * t443 * t440 + 0.9e1 / 0.2e1 * t336 * t201 * t325 * t328 - 0.2e1 * t336 * t248 * t292 * t304
  t591 = t164 ** 2
  t608 = t201 ** 2
  t633 = -0.24e2 * t109 / t134 / t132 * t141 * t591 - 0.28e2 * t136 * t174 * t165 + 0.36e2 * t136 * t141 * t164 * t201 - 0.91e2 / 0.3e1 * t171 * t210 * t164 + 0.28e2 * t171 * t174 * t202 - 0.6e1 * t171 * t141 * t608 - 0.8e1 * t171 * t141 * t163 * t248 - 0.1729e4 / 0.54e2 * t207 * t137 * t254 * t163 + 0.91e2 / 0.6e1 * t207 * t210 * t201 - 0.14e2 / 0.3e1 * t207 * t174 * t248 + t207 * t141 * t524 - 0.43225e5 / 0.1296e4 * t109 * t252 / t138 / t453
  t640 = t266 ** 2
  t643 = t378 ** 2
  t649 = t386 ** 2
  t656 = 0.24e2 * t264 * t519 - 0.24e2 * t74
  t660 = f.my_piecewise3(t267, 0, 0.40e2 / 0.81e2 / t271 / t640 * t643 - 0.20e2 / 0.9e1 * t377 * t378 * t386 + 0.10e2 / 0.3e1 * t382 * t649 + 0.40e2 / 0.9e1 * t383 * t391 + 0.5e1 / 0.3e1 * t272 * t656)
  t661 = t275 ** 2
  t664 = t398 ** 2
  t670 = t404 ** 2
  t675 = -t656
  t679 = f.my_piecewise3(t276, 0, 0.40e2 / 0.81e2 / t277 / t661 * t664 - 0.20e2 / 0.9e1 * t397 * t398 * t404 + 0.10e2 / 0.3e1 * t402 * t670 + 0.40e2 / 0.9e1 * t403 * t407 + 0.5e1 / 0.3e1 * t278 * t675)
  t694 = t429 ** 2
  t699 = t372 ** 2
  t718 = 0.4e1 * t438 * t262 * t248 * t285 + 0.14e2 * t290 * t435 - 0.28e2 * t314 * t440 + t107 * t633 * t286 + 0.4e1 * t259 * t316 + 0.6e1 * t446 * t440 - t336 * t354 * t284 * (t660 + t679) / 0.2e1 - 0.3e1 * t336 * t434 * t430 - 0.2e1 * t336 * t293 * t413 - 0.28e2 / 0.3e1 * t289 * t258 * t286 + 0.9e1 / 0.4e1 * t336 * t326 * t284 * t694 + 0.3e1 * t107 * t699 * t286 + 0.14e2 * t290 * t431 - 0.70e2 / 0.3e1 * t353 * t450 + 0.140e3 / 0.3e1 * t352 * t372 * t286 + 0.4e1 * t333 * t316 - 0.28e2 * t373 * t316 - 0.140e3 / 0.3e1 * t353 * t305 + 0.280e3 / 0.3e1 * t358 * t316
  t725 = t319 ** 2
  t732 = 0.1e1 + 0.69905000000000000000000000000000000000000000000000e0 * t14 + 0.65275000000000000000000000000000000000000000000000e-1 * t11
  t733 = t732 ** 2
  t735 = 0.1e1 / t733 / t732
  t738 = -0.11650833333333333333333333333333333333333333333333e0 * t27 - 0.21758333333333333333333333333333333333333333333333e-1 * t30
  t739 = t738 ** 2
  t742 = 0.1e1 / t733
  t746 = -0.77672222222222222222222222222222222222222222222220e-1 * t51 + 0.15534444444444444444444444444444444444444444444444e0 * t56 + 0.29011111111111111111111111111111111111111111111111e-1 * t59
  t752 = t4 * t58 * t97
  t756 = f.my_piecewise3(t13, -0.1686e0 * t735 * t739 + 0.843e-1 * t742 * t746, 0.51833333333333333333333333333333333333333333333333e-2 * t158 + 0.77777777777777777777777777777777777777777777777777e-4 * t752 - 0.43611111111111111111111111111111111111111111111112e-3 * t59)
  t766 = f.my_piecewise3(t13, -0.2846e0 * t38 * t33 + 0.1423e0 * t64 * t61, 0.10366666666666666666666666666666666666666666666667e-1 * t158 + 0.22222222222222222222222222222222222222222222222223e-3 * t752 - 0.10111111111111111111111111111111111111111111111111e-2 * t59)
  t767 = t756 - t766
  t768 = 0.1e1 / t272
  t774 = f.my_piecewise3(t267, 0, 0.4e1 / 0.9e1 * t768 * t378 + 0.4e1 / 0.3e1 * t271 * t386)
  t775 = 0.1e1 / t278
  t781 = f.my_piecewise3(t276, 0, 0.4e1 / 0.9e1 * t775 * t398 + 0.4e1 / 0.3e1 * t277 * t404)
  t782 = t774 + t781
  t784 = 2 ** (0.1e1 / 0.3e1)
  t787 = 0.1e1 / (0.2e1 * t784 - 0.2e1)
  t790 = t733 ** 2
  t791 = 0.1e1 / t790
  t795 = t735 * t738
  t802 = -0.46603333333333333333333333333333333333333333333332e0 * t75 + 0.31068888888888888888888888888888888888888888888888e0 * t81 - 0.36247037037037037037037037037037037037037037037036e0 * t86 - 0.67692592592592592592592592592592592592592592592592e-1 * t89
  t810 = f.my_piecewise3(t13, 0.5058e0 * t791 * t739 * t738 - 0.5058e0 * t795 * t746 + 0.843e-1 * t742 * t802, -0.10366666666666666666666666666666666666666666666667e-1 * t95 - 0.18148148148148148148148148148148148148148148148148e-3 * t99 + 0.99166666666666666666666666666666666666666666666667e-3 * t89)
  t811 = t810 - t103
  t814 = f.my_piecewise3(t267, 0, 0.4e1 / 0.3e1 * t271 * t295)
  t817 = f.my_piecewise3(t276, 0, 0.4e1 / 0.3e1 * t277 * t299)
  t818 = t814 + t817
  t824 = t739 ** 2
  t830 = t746 ** 2
  t842 = 0.1e1 / t14 / t126 * t455 * t4 * t6 / 0.48e2
  t844 = t72 * t519
  t846 = t43 * t480
  t848 = t22 * t475
  t850 = t6 * t351
  t851 = t4 * t850
  t859 = t4 * t850 * t97
  t863 = f.my_piecewise3(t13, -0.20232e1 / t790 / t732 * t824 + 0.30348e1 * t791 * t739 * t746 - 0.5058e0 * t735 * t830 - 0.6744e0 * t795 * t802 + 0.843e-1 * t742 * (-0.38836111111111111111111111111111111111111111111110e0 * t842 + 0.37282666666666666666666666666666666666666666666666e1 * t844 - 0.13808395061728395061728395061728395061728395061728e1 * t846 + 0.12082345679012345679012345679012345679012345679012e1 * t848 + 0.22564197530864197530864197530864197530864197530864e0 * t851), 0.31100000000000000000000000000000000000000000000001e-1 * t74 + 0.60493827160493827160493827160493827160493827160493e-3 * t859 - 0.32450617283950617283950617283950617283950617283951e-2 * t851)
  t866 = t33 ** 2
  t872 = t61 ** 2
  t890 = f.my_piecewise3(t13, -0.34152e1 / t19 / t17 * t866 + 0.51228e1 * t20 * t33 * t61 - 0.8538e0 * t38 * t872 - 0.11384e1 * t39 * t91 + 0.1423e0 * t64 * (-0.29247222222222222222222222222222222222222222222222e0 * t842 + 0.28077333333333333333333333333333333333333333333334e1 * t844 - 0.10399012345679012345679012345679012345679012345679e1 * t846 + 0.90991358024691358024691358024691358024691358024693e0 * t848 + 0.28812345679012345679012345679012345679012345679012e0 * t851), 0.62200000000000000000000000000000000000000000000002e-1 * t74 + 0.17283950617283950617283950617283950617283950617285e-2 * t859 - 0.74444444444444444444444444444444444444444444444442e-2 * t851)
  t892 = t268 * f.p.zeta_threshold
  t893 = f.my_piecewise3(t267, t892, t376)
  t894 = f.my_piecewise3(t276, t892, t396)
  t895 = t893 + t894 - 0.2e1
  t902 = t4 * t29 * t97
  t906 = f.my_piecewise3(t13, 0.843e-1 * t742 * t738, -0.51833333333333333333333333333333333333333333333333e-2 * t126 - 0.58333333333333333333333333333333333333333333333333e-4 * t902 + 0.34166666666666666666666666666666666666666666666667e-3 * t30)
  t913 = f.my_piecewise3(t13, 0.1423e0 * t64 * t32, -0.10366666666666666666666666666666666666666666666667e-1 * t126 - 0.16666666666666666666666666666666666666666666666667e-3 * t902 + 0.80000000000000000000000000000000000000000000000000e-3 * t30)
  t914 = t906 - t913
  t915 = 0.1e1 / t273
  t918 = t768 * t295
  t924 = f.my_piecewise3(t267, 0, -0.8e1 / 0.27e2 * t915 * t379 + 0.4e1 / 0.3e1 * t918 * t386 + 0.4e1 / 0.3e1 * t271 * t391)
  t925 = 0.1e1 / t279
  t928 = t775 * t299
  t934 = f.my_piecewise3(t276, 0, -0.8e1 / 0.27e2 * t925 * t399 + 0.4e1 / 0.3e1 * t928 * t404 + 0.4e1 / 0.3e1 * t277 * t407)
  t935 = t924 + t934
  t943 = t4 * t10 * t97
  t947 = f.my_piecewise3(t13, -0.843e-1 / t732, 0.1555e-1 * t97 - 0.269e-1 + 0.17500000000000000000000000000000000000000000000000e-3 * t943 - 0.12000000000000000000000000000000000000000000000000e-2 * t11)
  t954 = f.my_piecewise3(t13, -0.1423e0 / t17, 0.311e-1 * t97 - 0.48e-1 + 0.50000000000000000000000000000000000000000000000000e-3 * t943 - 0.29000000000000000000000000000000000000000000000000e-2 * t11)
  t955 = t947 - t954
  t970 = f.my_piecewise3(t267, 0, 0.40e2 / 0.81e2 / t272 / t640 * t643 - 0.16e2 / 0.9e1 * t915 * t378 * t386 + 0.4e1 / 0.3e1 * t768 * t649 + 0.16e2 / 0.9e1 * t918 * t391 + 0.4e1 / 0.3e1 * t271 * t656)
  t985 = f.my_piecewise3(t276, 0, 0.40e2 / 0.81e2 / t278 / t661 * t664 - 0.16e2 / 0.9e1 * t925 * t398 * t404 + 0.4e1 / 0.3e1 * t775 * t670 + 0.16e2 / 0.9e1 * t928 * t407 + 0.4e1 / 0.3e1 * t277 * t675)
  t989 = t319 * t262
  t990 = t107 * t989
  t1003 = t372 * t262
  t1004 = t107 * t1003
  t1014 = 0.1820e4 / 0.27e2 * t457 * t355 - 0.3640e4 / 0.27e2 * t456 * t313 * t286 + t107 * t725 * t286 - 0.28e2 * t320 * t316 + 0.6e1 * t767 * t782 * t787 + 0.4e1 * t811 * t818 * t787 + (t863 - t890) * t895 * t787 + 0.4e1 * t914 * t935 * t787 + t955 * (t970 + t985) * t787 + t890 + 0.9e1 / 0.2e1 * t990 * t329 - 0.2e1 * t107 * t258 * t262 * t355 + 0.4e1 * t107 * t258 * t313 * t286 - 0.3e1 * t990 * t450 + 0.9e1 / 0.2e1 * t1004 * t329 - 0.3e1 * t1004 * t450 + 0.9e1 * t533 * t338 - 0.140e3 / 0.3e1 * t352 * t532 * t355
  t1015 = t289 * t532
  t1018 = t284 * t372
  t1019 = t471 * t1018
  t1022 = t107 * t263
  t1033 = t325 * t284
  t1035 = t1033 * t303 * t429
  t1072 = -0.21e2 * t1015 * t329 - 0.28e2 * t1015 * t1019 - 0.45e2 / 0.4e1 * t1022 * t343 * t284 * t327 * t429 + 0.6e1 * t990 * t1019 + 0.28e2 * t1015 * t305 + 0.9e1 * t107 * t315 * t1035 + 0.14e2 * t289 * t989 * t355 - 0.15e2 / 0.2e1 * t533 * t347 + 0.14e2 * t289 * t1003 * t355 - 0.2e1 * t107 * t332 * t262 * t355 - 0.21e2 * t289 * t263 * t1035 + 0.3e1 * t1022 * t1033 * t412 * t303 - 0.2e1 * t533 * t414 - 0.6e1 * t533 * t431 - 0.6e1 * t533 * t435 + 0.12e2 * t533 * t458 * t1018 - 0.6e1 * t990 * t305 - 0.6e1 * t1004 * t305 + 0.14e2 * t1015 * t450
  t1114 = 0.14e2 * t290 * t450 + t7 * (t579 + t718 + t1014 + t1072) + 0.12e2 * t767 * t818 * t787 + 0.4e1 * t811 * t895 * t787 + 0.4e1 * t955 * t935 * t787 + 0.12e2 * t914 * t782 * t787 + 0.4e1 * t336 * t463 - 0.28e2 * t290 * t529 + 0.280e3 / 0.3e1 * t353 * t459 - 0.3640e4 / 0.27e2 * t457 * t472 + 0.9e1 * t533 * t329 + 0.28e2 * t1015 * t355 - 0.6e1 * t1004 * t355 + 0.12e2 * t107 * t372 * t313 * t286 - 0.6e1 * t990 * t355 - 0.12e2 * t533 * t305 - 0.6e1 * t533 * t450 + 0.9e1 * t1022 * t1035
  d1111 = t449 + t1114

  res = {'v4rho4': d1111}
  return res
