"""Generated from lda_c_chachiyo_mod.mpl."""

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
  params_af_raw = params.af
  if isinstance(params_af_raw, (str, bytes, dict)):
    params_af = params_af_raw
  else:
    try:
      params_af_seq = list(params_af_raw)
    except TypeError:
      params_af = params_af_raw
    else:
      params_af_seq = np.asarray(params_af_seq, dtype=np.float64)
      params_af = np.concatenate((np.array([np.nan], dtype=np.float64), params_af_seq))
  params_ap_raw = params.ap
  if isinstance(params_ap_raw, (str, bytes, dict)):
    params_ap = params_ap_raw
  else:
    try:
      params_ap_seq = list(params_ap_raw)
    except TypeError:
      params_ap = params_ap_raw
    else:
      params_ap_seq = np.asarray(params_ap_seq, dtype=np.float64)
      params_ap = np.concatenate((np.array([np.nan], dtype=np.float64), params_ap_seq))
  params_bf_raw = params.bf
  if isinstance(params_bf_raw, (str, bytes, dict)):
    params_bf = params_bf_raw
  else:
    try:
      params_bf_seq = list(params_bf_raw)
    except TypeError:
      params_bf = params_bf_raw
    else:
      params_bf_seq = np.asarray(params_bf_seq, dtype=np.float64)
      params_bf = np.concatenate((np.array([np.nan], dtype=np.float64), params_bf_seq))
  params_bp_raw = params.bp
  if isinstance(params_bp_raw, (str, bytes, dict)):
    params_bp = params_bp_raw
  else:
    try:
      params_bp_seq = list(params_bp_raw)
    except TypeError:
      params_bp = params_bp_raw
    else:
      params_bp_seq = np.asarray(params_bp_seq, dtype=np.float64)
      params_bp = np.concatenate((np.array([np.nan], dtype=np.float64), params_bp_seq))
  params_cf_raw = params.cf
  if isinstance(params_cf_raw, (str, bytes, dict)):
    params_cf = params_cf_raw
  else:
    try:
      params_cf_seq = list(params_cf_raw)
    except TypeError:
      params_cf = params_cf_raw
    else:
      params_cf_seq = np.asarray(params_cf_seq, dtype=np.float64)
      params_cf = np.concatenate((np.array([np.nan], dtype=np.float64), params_cf_seq))
  params_cp_raw = params.cp
  if isinstance(params_cp_raw, (str, bytes, dict)):
    params_cp = params_cp_raw
  else:
    try:
      params_cp_seq = list(params_cp_raw)
    except TypeError:
      params_cp = params_cp_raw
    else:
      params_cp_seq = np.asarray(params_cp_seq, dtype=np.float64)
      params_cp = np.concatenate((np.array([np.nan], dtype=np.float64), params_cp_seq))

  e0 = lambda rs: params_ap * jnp.log(1 + params_bp / rs + params_cp / rs ** 2)

  e1 = lambda rs: params_af * jnp.log(1 + params_bf / rs + params_cf / rs ** 2)

  g = lambda z: (f.opz_pow_n(z, 2 / 3) + f.opz_pow_n(-z, 2 / 3)) / 2

  g_zeta = lambda zeta: 2 * (1 - g(zeta) ** 3)

  f_chachiyo = lambda rs, zeta: e0(rs) + (e1(rs) - e0(rs)) * g_zeta(zeta)

  functional_body = lambda rs, zeta: f_chachiyo(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res


def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_af_raw = params.af
  if isinstance(params_af_raw, (str, bytes, dict)):
    params_af = params_af_raw
  else:
    try:
      params_af_seq = list(params_af_raw)
    except TypeError:
      params_af = params_af_raw
    else:
      params_af_seq = np.asarray(params_af_seq, dtype=np.float64)
      params_af = np.concatenate((np.array([np.nan], dtype=np.float64), params_af_seq))
  params_ap_raw = params.ap
  if isinstance(params_ap_raw, (str, bytes, dict)):
    params_ap = params_ap_raw
  else:
    try:
      params_ap_seq = list(params_ap_raw)
    except TypeError:
      params_ap = params_ap_raw
    else:
      params_ap_seq = np.asarray(params_ap_seq, dtype=np.float64)
      params_ap = np.concatenate((np.array([np.nan], dtype=np.float64), params_ap_seq))
  params_bf_raw = params.bf
  if isinstance(params_bf_raw, (str, bytes, dict)):
    params_bf = params_bf_raw
  else:
    try:
      params_bf_seq = list(params_bf_raw)
    except TypeError:
      params_bf = params_bf_raw
    else:
      params_bf_seq = np.asarray(params_bf_seq, dtype=np.float64)
      params_bf = np.concatenate((np.array([np.nan], dtype=np.float64), params_bf_seq))
  params_bp_raw = params.bp
  if isinstance(params_bp_raw, (str, bytes, dict)):
    params_bp = params_bp_raw
  else:
    try:
      params_bp_seq = list(params_bp_raw)
    except TypeError:
      params_bp = params_bp_raw
    else:
      params_bp_seq = np.asarray(params_bp_seq, dtype=np.float64)
      params_bp = np.concatenate((np.array([np.nan], dtype=np.float64), params_bp_seq))
  params_cf_raw = params.cf
  if isinstance(params_cf_raw, (str, bytes, dict)):
    params_cf = params_cf_raw
  else:
    try:
      params_cf_seq = list(params_cf_raw)
    except TypeError:
      params_cf = params_cf_raw
    else:
      params_cf_seq = np.asarray(params_cf_seq, dtype=np.float64)
      params_cf = np.concatenate((np.array([np.nan], dtype=np.float64), params_cf_seq))
  params_cp_raw = params.cp
  if isinstance(params_cp_raw, (str, bytes, dict)):
    params_cp = params_cp_raw
  else:
    try:
      params_cp_seq = list(params_cp_raw)
    except TypeError:
      params_cp = params_cp_raw
    else:
      params_cp_seq = np.asarray(params_cp_seq, dtype=np.float64)
      params_cp = np.concatenate((np.array([np.nan], dtype=np.float64), params_cp_seq))

  e0 = lambda rs: params_ap * jnp.log(1 + params_bp / rs + params_cp / rs ** 2)

  e1 = lambda rs: params_af * jnp.log(1 + params_bf / rs + params_cf / rs ** 2)

  g = lambda z: (f.opz_pow_n(z, 2 / 3) + f.opz_pow_n(-z, 2 / 3)) / 2

  g_zeta = lambda zeta: 2 * (1 - g(zeta) ** 3)

  f_chachiyo = lambda rs, zeta: e0(rs) + (e1(rs) - e0(rs)) * g_zeta(zeta)

  functional_body = lambda rs, zeta: f_chachiyo(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t3 = params.bp * t2
  t5 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t5 * t7
  t9 = r0 + r1
  t10 = t9 ** (0.1e1 / 0.3e1)
  t11 = t8 * t10
  t14 = params.cp * t1
  t15 = t5 ** 2
  t17 = t7 ** 2
  t18 = 0.1e1 / t15 * t17
  t19 = t10 ** 2
  t20 = t18 * t19
  t23 = 0.1e1 + t3 * t11 / 0.3e1 + t14 * t20 / 0.3e1
  t24 = jnp.log(t23)
  t25 = params.ap * t24
  t26 = params.bf * t2
  t29 = params.cf * t1
  t32 = 0.1e1 + t26 * t11 / 0.3e1 + t29 * t20 / 0.3e1
  t33 = jnp.log(t32)
  t35 = params.af * t33 - t25
  t36 = r0 - r1
  t37 = 0.1e1 / t9
  t38 = t36 * t37
  t39 = 0.1e1 + t38
  t40 = t39 <= f.p.zeta_threshold
  t41 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t43 = t39 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = f.my_piecewise3(t40, t42, t44)
  t46 = 0.1e1 - t38
  t47 = t46 <= f.p.zeta_threshold
  t48 = t46 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = f.my_piecewise3(t47, t42, t49)
  t52 = t45 / 0.2e1 + t50 / 0.2e1
  t53 = t52 ** 2
  t56 = -0.2e1 * t53 * t52 + 0.2e1
  t57 = t35 * t56
  t59 = t8 / t19
  t63 = t18 / t10
  t69 = params.ap * (t3 * t59 / 0.9e1 + 0.2e1 / 0.9e1 * t14 * t63) / t23
  t79 = (params.af * (t26 * t59 / 0.9e1 + 0.2e1 / 0.9e1 * t29 * t63) / t32 - t69) * t56
  t80 = t35 * t53
  t81 = 0.1e1 / t43
  t82 = t9 ** 2
  t84 = t36 / t82
  t85 = t37 - t84
  t88 = f.my_piecewise3(t40, 0, 0.2e1 / 0.3e1 * t81 * t85)
  t89 = 0.1e1 / t48
  t93 = f.my_piecewise3(t47, 0, -0.2e1 / 0.3e1 * t89 * t85)
  vrho_0_ = t25 + t57 + t9 * (t69 + t79 - 0.6e1 * t80 * (t88 / 0.2e1 + t93 / 0.2e1))
  t100 = -t37 - t84
  t103 = f.my_piecewise3(t40, 0, 0.2e1 / 0.3e1 * t81 * t100)
  t107 = f.my_piecewise3(t47, 0, -0.2e1 / 0.3e1 * t89 * t100)
  vrho_1_ = t25 + t57 + t9 * (t69 + t79 - 0.6e1 * t80 * (t103 / 0.2e1 + t107 / 0.2e1))

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res


def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t3 = params.bp * t2
  t5 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t5 * t7
  t9 = r0 ** (0.1e1 / 0.3e1)
  t10 = t8 * t9
  t13 = params.cp * t1
  t14 = t5 ** 2
  t16 = t7 ** 2
  t17 = 0.1e1 / t14 * t16
  t18 = t9 ** 2
  t19 = t17 * t18
  t22 = 0.1e1 + t3 * t10 / 0.3e1 + t13 * t19 / 0.3e1
  t23 = jnp.log(t22)
  t24 = params.ap * t23
  t25 = params.bf * t2
  t28 = params.cf * t1
  t31 = 0.1e1 + t25 * t10 / 0.3e1 + t28 * t19 / 0.3e1
  t32 = jnp.log(t31)
  t36 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t37, 1)
  t39 = t38 ** 2
  t42 = -0.2e1 * t39 * t38 + 0.2e1
  t45 = t8 / t18
  t49 = t17 / t9
  t55 = params.ap * (t3 * t45 / 0.9e1 + 0.2e1 / 0.9e1 * t13 * t49) / t22
  vrho_0_ = t24 + (params.af * t32 - t24) * t42 + r0 * (t55 + (params.af * (t25 * t45 / 0.9e1 + 0.2e1 / 0.9e1 * t28 * t49) / t31 - t55) * t42)

  res = {'vrho': vrho_0_}
  return res
