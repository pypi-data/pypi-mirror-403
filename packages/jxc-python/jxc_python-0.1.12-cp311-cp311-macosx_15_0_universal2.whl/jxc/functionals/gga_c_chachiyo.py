"""Generated from gga_c_chachiyo.mpl."""

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
  params_h_raw = params.h
  if isinstance(params_h_raw, (str, bytes, dict)):
    params_h = params_h_raw
  else:
    try:
      params_h_seq = list(params_h_raw)
    except TypeError:
      params_h = params_h_raw
    else:
      params_h_seq = np.asarray(params_h_seq, dtype=np.float64)
      params_h = np.concatenate((np.array([np.nan], dtype=np.float64), params_h_seq))

  e0 = lambda rs: params_ap * jnp.log(1 + params_bp / rs + params_cp / rs ** 2)

  e1 = lambda rs: params_af * jnp.log(1 + params_bf / rs + params_cf / rs ** 2)

  g = lambda z: (f.opz_pow_n(z, 2 / 3) + f.opz_pow_n(-z, 2 / 3)) / 2

  cha_t = lambda rs, xt: (jnp.pi / 3) ** (1 / 6) / 4 * f.n_total(rs) ** (1 / 6) * xt

  g_zeta = lambda zeta: 2 * (1 - g(zeta) ** 3)

  f_chachiyo = lambda rs, zeta: e0(rs) + (e1(rs) - e0(rs)) * g_zeta(zeta)

  f_chachiyo_gga = lambda rs, z, xt, xs0=None, xs1=None: f_chachiyo(rs, z) * (1 + cha_t(rs, xt) ** 2) ** (params_h / f_chachiyo(rs, z))

  functional_body = lambda rs, z, xt, xs0, xs1: f_chachiyo_gga(rs, z, xt, xs0, xs1)

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
  params_h_raw = params.h
  if isinstance(params_h_raw, (str, bytes, dict)):
    params_h = params_h_raw
  else:
    try:
      params_h_seq = list(params_h_raw)
    except TypeError:
      params_h = params_h_raw
    else:
      params_h_seq = np.asarray(params_h_seq, dtype=np.float64)
      params_h = np.concatenate((np.array([np.nan], dtype=np.float64), params_h_seq))

  e0 = lambda rs: params_ap * jnp.log(1 + params_bp / rs + params_cp / rs ** 2)

  e1 = lambda rs: params_af * jnp.log(1 + params_bf / rs + params_cf / rs ** 2)

  g = lambda z: (f.opz_pow_n(z, 2 / 3) + f.opz_pow_n(-z, 2 / 3)) / 2

  cha_t = lambda rs, xt: (jnp.pi / 3) ** (1 / 6) / 4 * f.n_total(rs) ** (1 / 6) * xt

  g_zeta = lambda zeta: 2 * (1 - g(zeta) ** 3)

  f_chachiyo = lambda rs, zeta: e0(rs) + (e1(rs) - e0(rs)) * g_zeta(zeta)

  f_chachiyo_gga = lambda rs, z, xt, xs0=None, xs1=None: f_chachiyo(rs, z) * (1 + cha_t(rs, xt) ** 2) ** (params_h / f_chachiyo(rs, z))

  functional_body = lambda rs, z, xt, xs0, xs1: f_chachiyo_gga(rs, z, xt, xs0, xs1)

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
  params_h_raw = params.h
  if isinstance(params_h_raw, (str, bytes, dict)):
    params_h = params_h_raw
  else:
    try:
      params_h_seq = list(params_h_raw)
    except TypeError:
      params_h = params_h_raw
    else:
      params_h_seq = np.asarray(params_h_seq, dtype=np.float64)
      params_h = np.concatenate((np.array([np.nan], dtype=np.float64), params_h_seq))

  e0 = lambda rs: params_ap * jnp.log(1 + params_bp / rs + params_cp / rs ** 2)

  e1 = lambda rs: params_af * jnp.log(1 + params_bf / rs + params_cf / rs ** 2)

  g = lambda z: (f.opz_pow_n(z, 2 / 3) + f.opz_pow_n(-z, 2 / 3)) / 2

  cha_t = lambda rs, xt: (jnp.pi / 3) ** (1 / 6) / 4 * f.n_total(rs) ** (1 / 6) * xt

  g_zeta = lambda zeta: 2 * (1 - g(zeta) ** 3)

  f_chachiyo = lambda rs, zeta: e0(rs) + (e1(rs) - e0(rs)) * g_zeta(zeta)

  f_chachiyo_gga = lambda rs, z, xt, xs0=None, xs1=None: f_chachiyo(rs, z) * (1 + cha_t(rs, xt) ** 2) ** (params_h / f_chachiyo(rs, z))

  functional_body = lambda rs, z, xt, xs0, xs1: f_chachiyo_gga(rs, z, xt, xs0, xs1)

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
  t58 = t35 * t56 + t25
  t59 = jnp.pi ** (0.1e1 / 0.3e1)
  t60 = t2 * t59
  t61 = t9 ** 2
  t65 = s0 + 0.2e1 * s1 + s2
  t69 = 0.1e1 + t60 / t10 / t61 * t65 / 0.48e2
  t71 = params.h / t58
  t72 = t69 ** t71
  t73 = t58 * t72
  t75 = t8 / t19
  t79 = t18 / t10
  t85 = params.ap * (t3 * t75 / 0.9e1 + 0.2e1 / 0.9e1 * t14 * t79) / t23
  t95 = (params.af * (t26 * t75 / 0.9e1 + 0.2e1 / 0.9e1 * t29 * t79) / t32 - t85) * t56
  t96 = t35 * t53
  t97 = 0.1e1 / t43
  t99 = t36 / t61
  t100 = t37 - t99
  t103 = f.my_piecewise3(t40, 0, 0.2e1 / 0.3e1 * t97 * t100)
  t104 = 0.1e1 / t48
  t108 = f.my_piecewise3(t47, 0, -0.2e1 / 0.3e1 * t104 * t100)
  t113 = t85 + t95 - 0.6e1 * t96 * (t103 / 0.2e1 + t108 / 0.2e1)
  t116 = t9 * t58
  t117 = t58 ** 2
  t119 = params.h / t117
  t120 = jnp.log(t69)
  t128 = 0.1e1 / t69
  t132 = 0.7e1 / 0.144e3 * t71 * t2 * t59 / t10 / t61 / t9 * t65 * t128
  vrho_0_ = t73 + t9 * t113 * t72 + t116 * t72 * (-t119 * t113 * t120 - t132)
  t136 = -t37 - t99
  t139 = f.my_piecewise3(t40, 0, 0.2e1 / 0.3e1 * t97 * t136)
  t143 = f.my_piecewise3(t47, 0, -0.2e1 / 0.3e1 * t104 * t136)
  t148 = t85 + t95 - 0.6e1 * t96 * (t139 / 0.2e1 + t143 / 0.2e1)
  vrho_1_ = t73 + t9 * t148 * t72 + t116 * t72 * (-t119 * t148 * t120 - t132)
  t161 = 0.1e1 / t10 / t9 * t72 * params.h * t60 * t128
  vsigma_0_ = t161 / 0.48e2
  vsigma_1_ = t161 / 0.24e2
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
  params_h_raw = params.h
  if isinstance(params_h_raw, (str, bytes, dict)):
    params_h = params_h_raw
  else:
    try:
      params_h_seq = list(params_h_raw)
    except TypeError:
      params_h = params_h_raw
    else:
      params_h_seq = np.asarray(params_h_seq, dtype=np.float64)
      params_h = np.concatenate((np.array([np.nan], dtype=np.float64), params_h_seq))

  e0 = lambda rs: params_ap * jnp.log(1 + params_bp / rs + params_cp / rs ** 2)

  e1 = lambda rs: params_af * jnp.log(1 + params_bf / rs + params_cf / rs ** 2)

  g = lambda z: (f.opz_pow_n(z, 2 / 3) + f.opz_pow_n(-z, 2 / 3)) / 2

  cha_t = lambda rs, xt: (jnp.pi / 3) ** (1 / 6) / 4 * f.n_total(rs) ** (1 / 6) * xt

  g_zeta = lambda zeta: 2 * (1 - g(zeta) ** 3)

  f_chachiyo = lambda rs, zeta: e0(rs) + (e1(rs) - e0(rs)) * g_zeta(zeta)

  f_chachiyo_gga = lambda rs, z, xt, xs0=None, xs1=None: f_chachiyo(rs, z) * (1 + cha_t(rs, xt) ** 2) ** (params_h / f_chachiyo(rs, z))

  functional_body = lambda rs, z, xt, xs0, xs1: f_chachiyo_gga(rs, z, xt, xs0, xs1)

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
  t44 = t24 + (params.af * t32 - t24) * t42
  t45 = jnp.pi ** (0.1e1 / 0.3e1)
  t46 = t2 * t45
  t47 = r0 ** 2
  t53 = 0.1e1 + t46 / t9 / t47 * s0 / 0.48e2
  t55 = params.h / t44
  t56 = t53 ** t55
  t59 = t8 / t18
  t63 = t17 / t9
  t69 = params.ap * (t3 * t59 / 0.9e1 + 0.2e1 / 0.9e1 * t13 * t63) / t22
  t80 = t69 + (params.af * (t25 * t59 / 0.9e1 + 0.2e1 / 0.9e1 * t28 * t63) / t31 - t69) * t42
  t84 = t44 ** 2
  t87 = jnp.log(t53)
  t95 = 0.1e1 / t53
  vrho_0_ = t44 * t56 + r0 * t80 * t56 + r0 * t44 * t56 * (-params.h / t84 * t80 * t87 - 0.7e1 / 0.144e3 * t55 * t2 * t45 / t9 / t47 / r0 * s0 * t95)
  vsigma_0_ = 0.1e1 / t9 / r0 * t56 * params.h * t46 * t95 / 0.48e2
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
  t2 = t1 ** 2
  t3 = params.bp * t2
  t5 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t5 * t7
  t9 = r0 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t12 = t8 / t10
  t15 = params.cp * t1
  t16 = t5 ** 2
  t18 = t7 ** 2
  t19 = 0.1e1 / t16 * t18
  t21 = t19 / t9
  t24 = t3 * t12 / 0.9e1 + 0.2e1 / 0.9e1 * t15 * t21
  t26 = t8 * t9
  t29 = t19 * t10
  t32 = 0.1e1 + t3 * t26 / 0.3e1 + t15 * t29 / 0.3e1
  t33 = 0.1e1 / t32
  t34 = params.ap * t24 * t33
  t35 = params.bf * t2
  t38 = params.cf * t1
  t41 = t35 * t12 / 0.9e1 + 0.2e1 / 0.9e1 * t38 * t21
  t47 = 0.1e1 + t35 * t26 / 0.3e1 + t38 * t29 / 0.3e1
  t48 = 0.1e1 / t47
  t52 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t54 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t53, 1)
  t55 = t54 ** 2
  t58 = -0.2e1 * t55 * t54 + 0.2e1
  t60 = t34 + (params.af * t41 * t48 - t34) * t58
  t61 = jnp.pi ** (0.1e1 / 0.3e1)
  t62 = t2 * t61
  t63 = r0 ** 2
  t65 = 0.1e1 / t9 / t63
  t69 = 0.1e1 + t62 * t65 * s0 / 0.48e2
  t70 = jnp.log(t32)
  t71 = params.ap * t70
  t72 = jnp.log(t47)
  t76 = t71 + (params.af * t72 - t71) * t58
  t77 = 0.1e1 / t76
  t78 = params.h * t77
  t79 = t69 ** t78
  t83 = t76 ** 2
  t85 = params.h / t83
  t86 = jnp.log(t69)
  t89 = t78 * t2
  t90 = t63 * r0
  t94 = 0.1e1 / t69
  t95 = s0 * t94
  t96 = t61 / t9 / t90 * t95
  t99 = -t85 * t60 * t86 - 0.7e1 / 0.144e3 * t89 * t96
  t104 = t8 / t10 / r0
  t107 = 0.1e1 / t9 / r0
  t108 = t19 * t107
  t113 = params.ap * (-0.2e1 / 0.27e2 * t3 * t104 - 0.2e1 / 0.27e2 * t15 * t108) * t33
  t114 = t24 ** 2
  t116 = t32 ** 2
  t118 = params.ap * t114 / t116
  t125 = t41 ** 2
  t127 = t47 ** 2
  t132 = t113 - t118 + (params.af * (-0.2e1 / 0.27e2 * t35 * t104 - 0.2e1 / 0.27e2 * t38 * t108) * t48 - params.af * t125 / t127 - t113 + t118) * t58
  t139 = r0 * t76
  t140 = t99 ** 2
  t146 = t60 ** 2
  t156 = t63 ** 2
  t164 = t61 ** 2
  t169 = s0 ** 2
  t170 = t69 ** 2
  t171 = 0.1e1 / t170
  v2rho2_0_ = 0.2e1 * t60 * t79 + 0.2e1 * t76 * t79 * t99 + r0 * t132 * t79 + 0.2e1 * r0 * t60 * t79 * t99 + t139 * t79 * t140 + t139 * t79 * (0.2e1 * params.h / t83 / t76 * t146 * t86 - t85 * t132 * t86 + 0.7e1 / 0.72e2 * t85 * t60 * t2 * t96 + 0.35e2 / 0.216e3 * t89 * t61 / t9 / t156 * t95 - 0.49e2 / 0.6912e4 * t78 * t1 * t164 / t10 / t156 / t63 * t169 * t171)
  t195 = t1 * t164
  v2rhosigma_0_ = -t65 * t79 * params.h * t62 * t94 / 0.36e2 + t107 * t79 * t99 * params.h * t2 * t61 * t94 / 0.48e2 + 0.7e1 / 0.2304e4 / t10 / t156 * t79 * params.h * t195 * t171 * s0
  t202 = 0.1e1 / t10 / t90 * t79
  t203 = params.h ** 2
  v2sigma2_0_ = t202 * t203 * t77 * t1 * t164 * t171 / 0.768e3 - t202 * params.h * t195 * t171 / 0.768e3
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
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
  t10 = t9 ** 2
  t13 = t8 / t10 / r0
  t15 = params.cp * t1
  t16 = t5 ** 2
  t18 = t7 ** 2
  t19 = 0.1e1 / t16 * t18
  t22 = t19 / t9 / r0
  t26 = params.ap * (-0.2e1 / 0.27e2 * t3 * t13 - 0.2e1 / 0.27e2 * t15 * t22)
  t27 = t8 * t9
  t30 = t19 * t10
  t33 = 0.1e1 + t3 * t27 / 0.3e1 + t15 * t30 / 0.3e1
  t34 = 0.1e1 / t33
  t35 = t26 * t34
  t37 = t8 / t10
  t41 = t19 / t9
  t44 = t3 * t37 / 0.9e1 + 0.2e1 / 0.9e1 * t15 * t41
  t45 = t44 ** 2
  t47 = t33 ** 2
  t48 = 0.1e1 / t47
  t49 = params.ap * t45 * t48
  t50 = params.bf * t2
  t52 = params.cf * t1
  t56 = params.af * (-0.2e1 / 0.27e2 * t50 * t13 - 0.2e1 / 0.27e2 * t52 * t22)
  t61 = 0.1e1 + t50 * t27 / 0.3e1 + t52 * t30 / 0.3e1
  t62 = 0.1e1 / t61
  t68 = t50 * t37 / 0.9e1 + 0.2e1 / 0.9e1 * t52 * t41
  t69 = t68 ** 2
  t71 = t61 ** 2
  t72 = 0.1e1 / t71
  t76 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t77 = t76 ** 2
  t78 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t77, 1)
  t79 = t78 ** 2
  t82 = -0.2e1 * t79 * t78 + 0.2e1
  t84 = t35 - t49 + (-params.af * t69 * t72 + t56 * t62 - t35 + t49) * t82
  t85 = jnp.pi ** (0.1e1 / 0.3e1)
  t87 = r0 ** 2
  t89 = 0.1e1 / t9 / t87
  t93 = 0.1e1 + t2 * t85 * t89 * s0 / 0.48e2
  t94 = jnp.log(t33)
  t95 = params.ap * t94
  t96 = jnp.log(t61)
  t100 = t95 + (params.af * t96 - t95) * t82
  t102 = params.h / t100
  t103 = t93 ** t102
  t107 = params.ap * t44 * t34
  t112 = t107 + (params.af * t68 * t62 - t107) * t82
  t114 = t100 ** 2
  t116 = params.h / t114
  t117 = jnp.log(t93)
  t118 = t112 * t117
  t120 = t102 * t2
  t121 = t87 * r0
  t126 = s0 / t93
  t127 = t85 / t9 / t121 * t126
  t130 = -t116 * t118 - 0.7e1 / 0.144e3 * t120 * t127
  t133 = t100 * t103
  t134 = t130 ** 2
  t139 = params.h / t114 / t100
  t140 = t112 ** 2
  t147 = t116 * t112 * t2
  t150 = t87 ** 2
  t154 = t85 / t9 / t150 * t126
  t157 = t102 * t1
  t158 = t85 ** 2
  t163 = s0 ** 2
  t164 = t93 ** 2
  t166 = t163 / t164
  t167 = t158 / t10 / t150 / t87 * t166
  t170 = 0.2e1 * t139 * t140 * t117 - t116 * t84 * t117 + 0.7e1 / 0.72e2 * t147 * t127 + 0.35e2 / 0.216e3 * t120 * t154 - 0.49e2 / 0.6912e4 * t157 * t167
  t175 = t8 / t10 / t87
  t178 = t19 * t89
  t183 = params.ap * (0.10e2 / 0.81e2 * t3 * t175 + 0.8e1 / 0.81e2 * t15 * t178) * t34
  t186 = 0.3e1 * t26 * t48 * t44
  t192 = 0.2e1 * params.ap * t45 * t44 / t47 / t33
  t211 = t183 - t186 + t192 + (params.af * (0.10e2 / 0.81e2 * t50 * t175 + 0.8e1 / 0.81e2 * t52 * t178) * t62 - 0.3e1 * t56 * t72 * t68 + 0.2e1 * params.af * t69 * t68 / t71 / t61 - t183 + t186 - t192) * t82
  t215 = t103 * t130
  t218 = r0 * t112
  t225 = r0 * t100
  t232 = t114 ** 2
  t273 = t150 ** 2
  v3rho3_0_ = 0.3e1 * t84 * t103 + 0.6e1 * t112 * t103 * t130 + 0.3e1 * t133 * t134 + 0.3e1 * t133 * t170 + r0 * t211 * t103 + 0.3e1 * r0 * t84 * t215 + 0.3e1 * t218 * t103 * t134 + 0.3e1 * t218 * t103 * t170 + t225 * t103 * t134 * t130 + 0.3e1 * t225 * t215 * t170 + t225 * t103 * (-0.6e1 * params.h / t232 * t140 * t112 * t117 + 0.6e1 * t139 * t118 * t84 - 0.7e1 / 0.24e2 * t139 * t140 * t2 * t127 - t116 * t211 * t117 + 0.7e1 / 0.48e2 * t116 * t84 * t2 * t127 - 0.35e2 / 0.72e2 * t147 * t154 + 0.49e2 / 0.2304e4 * t116 * t112 * t1 * t167 - 0.455e3 / 0.648e3 * t120 * t85 / t9 / t150 / r0 * t126 + 0.245e3 / 0.3456e4 * t157 * t158 / t10 / t150 / t121 * t166 - 0.343e3 / 0.165888e6 * t102 * jnp.pi / t273 / t87 * t163 * s0 / t164 / t93)

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t3 = params.bp * t2
  t5 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t5 * t7
  t9 = r0 ** 2
  t10 = r0 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t14 = t8 / t11 / t9
  t17 = params.cp * t1
  t18 = t5 ** 2
  t20 = t7 ** 2
  t21 = 0.1e1 / t18 * t20
  t23 = 0.1e1 / t10 / t9
  t24 = t21 * t23
  t28 = params.ap * (0.10e2 / 0.81e2 * t3 * t14 + 0.8e1 / 0.81e2 * t17 * t24)
  t29 = t8 * t10
  t32 = t21 * t11
  t35 = 0.1e1 + t3 * t29 / 0.3e1 + t17 * t32 / 0.3e1
  t36 = 0.1e1 / t35
  t37 = t28 * t36
  t40 = t8 / t11 / r0
  t44 = t21 / t10 / r0
  t47 = -0.2e1 / 0.27e2 * t17 * t44 - 0.2e1 / 0.27e2 * t3 * t40
  t48 = params.ap * t47
  t49 = t35 ** 2
  t50 = 0.1e1 / t49
  t52 = t8 / t11
  t56 = t21 / t10
  t59 = t3 * t52 / 0.9e1 + 0.2e1 / 0.9e1 * t17 * t56
  t60 = t50 * t59
  t62 = 0.3e1 * t48 * t60
  t63 = t59 ** 2
  t67 = 0.1e1 / t49 / t35
  t69 = 0.2e1 * params.ap * t63 * t59 * t67
  t70 = params.bf * t2
  t73 = params.cf * t1
  t77 = params.af * (0.10e2 / 0.81e2 * t70 * t14 + 0.8e1 / 0.81e2 * t73 * t24)
  t82 = 0.1e1 + t70 * t29 / 0.3e1 + t73 * t32 / 0.3e1
  t83 = 0.1e1 / t82
  t88 = -0.2e1 / 0.27e2 * t70 * t40 - 0.2e1 / 0.27e2 * t73 * t44
  t89 = params.af * t88
  t90 = t82 ** 2
  t91 = 0.1e1 / t90
  t96 = t70 * t52 / 0.9e1 + 0.2e1 / 0.9e1 * t73 * t56
  t97 = t91 * t96
  t100 = t96 ** 2
  t104 = 0.1e1 / t90 / t82
  t109 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t110 = t109 ** 2
  t111 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t110, 1)
  t112 = t111 ** 2
  t115 = -0.2e1 * t112 * t111 + 0.2e1
  t117 = t37 - t62 + t69 + (0.2e1 * params.af * t100 * t96 * t104 + t77 * t83 - 0.3e1 * t89 * t97 - t37 + t62 - t69) * t115
  t118 = jnp.pi ** (0.1e1 / 0.3e1)
  t123 = 0.1e1 + t2 * t118 * t23 * s0 / 0.48e2
  t124 = jnp.log(t35)
  t125 = params.ap * t124
  t126 = jnp.log(t82)
  t130 = t125 + (params.af * t126 - t125) * t115
  t132 = params.h / t130
  t133 = t123 ** t132
  t136 = t48 * t36
  t138 = params.ap * t63 * t50
  t144 = t136 - t138 + (-params.af * t100 * t91 + t89 * t83 - t136 + t138) * t115
  t146 = t130 ** 2
  t148 = params.h / t146
  t150 = params.ap * t59 * t36
  t155 = t150 + (params.af * t96 * t83 - t150) * t115
  t156 = jnp.log(t123)
  t157 = t155 * t156
  t159 = t132 * t2
  t160 = t9 * r0
  t162 = 0.1e1 / t10 / t160
  t163 = t118 * t162
  t165 = s0 / t123
  t166 = t163 * t165
  t169 = -t148 * t157 - 0.7e1 / 0.144e3 * t159 * t166
  t172 = t155 * t133
  t175 = params.h / t146 / t130
  t176 = t155 ** 2
  t177 = t176 * t156
  t182 = t155 * t2
  t183 = t148 * t182
  t186 = t9 ** 2
  t190 = t118 / t10 / t186 * t165
  t193 = t132 * t1
  t194 = t118 ** 2
  t195 = t186 * t9
  t199 = s0 ** 2
  t200 = t123 ** 2
  t202 = t199 / t200
  t203 = t194 / t11 / t195 * t202
  t206 = 0.2e1 * t175 * t177 - t148 * t144 * t156 + 0.7e1 / 0.72e2 * t183 * t166 + 0.35e2 / 0.216e3 * t159 * t190 - 0.49e2 / 0.6912e4 * t193 * t203
  t209 = t130 * t133
  t210 = t146 ** 2
  t212 = params.h / t210
  t213 = t176 * t155
  t221 = t175 * t176 * t2
  t227 = t148 * t144 * t2
  t233 = t148 * t155 * t1
  t236 = t186 * r0
  t240 = t118 / t10 / t236 * t165
  t247 = t194 / t11 / t186 / t160 * t202
  t250 = t132 * jnp.pi
  t251 = t186 ** 2
  t253 = 0.1e1 / t251 / t9
  t254 = t199 * s0
  t257 = 0.1e1 / t200 / t123
  t261 = -0.6e1 * t212 * t213 * t156 + 0.6e1 * t175 * t157 * t144 - 0.7e1 / 0.24e2 * t221 * t166 - t148 * t117 * t156 + 0.7e1 / 0.48e2 * t227 * t166 - 0.35e2 / 0.72e2 * t183 * t190 + 0.49e2 / 0.2304e4 * t233 * t203 - 0.455e3 / 0.648e3 * t159 * t240 + 0.245e3 / 0.3456e4 * t193 * t247 - 0.343e3 / 0.165888e6 * t250 * t253 * t254 * t257
  t266 = t8 / t11 / t160
  t269 = t21 * t162
  t274 = params.ap * (-0.80e2 / 0.243e3 * t3 * t266 - 0.56e2 / 0.243e3 * t17 * t269) * t36
  t276 = 0.4e1 * t28 * t60
  t279 = 0.12e2 * t48 * t67 * t63
  t280 = t47 ** 2
  t283 = 0.3e1 * params.ap * t280 * t50
  t284 = t63 ** 2
  t286 = t49 ** 2
  t289 = 0.6e1 * params.ap * t284 / t286
  t302 = t88 ** 2
  t306 = t100 ** 2
  t308 = t90 ** 2
  t314 = t274 - t276 + t279 - t283 - t289 + (params.af * (-0.80e2 / 0.243e3 * t70 * t266 - 0.56e2 / 0.243e3 * t73 * t269) * t83 - 0.4e1 * t77 * t97 + 0.12e2 * t89 * t104 * t100 - 0.3e1 * params.af * t302 * t91 - 0.6e1 * params.af * t306 / t308 - t274 + t276 - t279 + t283 + t289) * t115
  t317 = r0 * t144
  t318 = t169 ** 2
  t319 = t133 * t318
  t322 = r0 * t155
  t323 = t133 * t169
  t327 = t318 * t169
  t331 = r0 * t130
  t335 = t318 ** 2
  t338 = t206 ** 2
  t370 = t176 ** 2
  t377 = t144 ** 2
  t412 = t199 ** 2
  t414 = t200 ** 2
  t446 = 0.1715e4 / 0.41472e5 * t250 / t251 / t160 * t254 * t257 + 0.24e2 * params.h / t210 / t130 * t370 * t156 - 0.36e2 * t212 * t177 * t144 + 0.6e1 * t175 * t377 * t156 + 0.8e1 * t175 * t157 * t117 + 0.35e2 / 0.18e2 * t221 * t190 - 0.35e2 / 0.36e2 * t227 * t190 + 0.455e3 / 0.162e3 * t183 * t240 - 0.7e1 / 0.6e1 * t175 * t182 * t163 * t165 * t144 + 0.343e3 / 0.41472e5 * t148 * t155 * jnp.pi * t253 * t254 * t257 - 0.10045e5 / 0.15552e5 * t193 * t194 / t11 / t251 * t202 - 0.2401e4 / 0.7962624e7 * t132 * t118 * jnp.pi / t10 / t251 / t236 * t412 / t414 * t2 - t148 * t314 * t156 + 0.7e1 / 0.6e1 * t212 * t213 * t2 * t166 - 0.49e2 / 0.576e3 * t175 * t176 * t1 * t203 + 0.7e1 / 0.36e2 * t148 * t117 * t2 * t166 + 0.49e2 / 0.1152e4 * t148 * t144 * t1 * t203 - 0.245e3 / 0.864e3 * t233 * t247 + 0.910e3 / 0.243e3 * t159 * t118 / t10 / t195 * t165
  v4rho4_0_ = 0.4e1 * r0 * t117 * t323 + r0 * t314 * t133 + 0.12e2 * t144 * t133 * t169 + 0.6e1 * t317 * t133 * t206 + 0.4e1 * t322 * t133 * t261 + 0.4e1 * t322 * t133 * t327 + t331 * t133 * t335 + 0.3e1 * t331 * t133 * t338 + t331 * t133 * t446 + 0.12e2 * t209 * t169 * t206 + 0.6e1 * t331 * t319 * t206 + 0.12e2 * t322 * t323 * t206 + 0.4e1 * t331 * t323 * t261 + 0.4e1 * t117 * t133 + 0.12e2 * t172 * t206 + 0.12e2 * t172 * t318 + 0.4e1 * t209 * t261 + 0.4e1 * t209 * t327 + 0.6e1 * t317 * t319

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
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
  t11 = t10 ** 2
  t13 = t8 / t11
  t16 = params.cp * t1
  t17 = t5 ** 2
  t19 = t7 ** 2
  t20 = 0.1e1 / t17 * t19
  t22 = t20 / t10
  t25 = t3 * t13 / 0.9e1 + 0.2e1 / 0.9e1 * t16 * t22
  t27 = t8 * t10
  t30 = t20 * t11
  t33 = 0.1e1 + t3 * t27 / 0.3e1 + t16 * t30 / 0.3e1
  t34 = 0.1e1 / t33
  t35 = params.ap * t25 * t34
  t36 = params.bf * t2
  t39 = params.cf * t1
  t42 = t36 * t13 / 0.9e1 + 0.2e1 / 0.9e1 * t39 * t22
  t48 = 0.1e1 + t36 * t27 / 0.3e1 + t39 * t30 / 0.3e1
  t49 = 0.1e1 / t48
  t51 = params.af * t42 * t49 - t35
  t52 = r0 - r1
  t53 = 0.1e1 / t9
  t54 = t52 * t53
  t55 = 0.1e1 + t54
  t56 = t55 <= f.p.zeta_threshold
  t57 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t58 = t57 ** 2
  t59 = t55 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = f.my_piecewise3(t56, t58, t60)
  t62 = 0.1e1 - t54
  t63 = t62 <= f.p.zeta_threshold
  t64 = t62 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t66 = f.my_piecewise3(t63, t58, t65)
  t68 = t61 / 0.2e1 + t66 / 0.2e1
  t69 = t68 ** 2
  t72 = -0.2e1 * t69 * t68 + 0.2e1
  t73 = t51 * t72
  t74 = jnp.log(t48)
  t76 = jnp.log(t33)
  t77 = params.ap * t76
  t78 = params.af * t74 - t77
  t79 = t78 * t69
  t80 = 0.1e1 / t59
  t81 = t9 ** 2
  t82 = 0.1e1 / t81
  t83 = t52 * t82
  t84 = t53 - t83
  t87 = f.my_piecewise3(t56, 0, 0.2e1 / 0.3e1 * t80 * t84)
  t88 = 0.1e1 / t64
  t89 = -t84
  t92 = f.my_piecewise3(t63, 0, 0.2e1 / 0.3e1 * t88 * t89)
  t94 = t87 / 0.2e1 + t92 / 0.2e1
  t97 = -0.6e1 * t79 * t94 + t35 + t73
  t98 = jnp.pi ** (0.1e1 / 0.3e1)
  t103 = s0 + 0.2e1 * s1 + s2
  t107 = 0.1e1 + t2 * t98 / t10 / t81 * t103 / 0.48e2
  t109 = t78 * t72 + t77
  t111 = params.h / t109
  t112 = t107 ** t111
  t113 = t97 * t112
  t115 = t109 * t112
  t116 = t109 ** 2
  t118 = params.h / t116
  t119 = jnp.log(t107)
  t122 = t111 * t2
  t123 = t81 * t9
  t128 = t103 / t107
  t129 = t98 / t10 / t123 * t128
  t131 = 0.7e1 / 0.144e3 * t122 * t129
  t132 = -t118 * t97 * t119 - t131
  t133 = t115 * t132
  t137 = t8 / t11 / t9
  t141 = t20 / t10 / t9
  t146 = params.ap * (-0.2e1 / 0.27e2 * t3 * t137 - 0.2e1 / 0.27e2 * t16 * t141) * t34
  t147 = t25 ** 2
  t149 = t33 ** 2
  t151 = params.ap * t147 / t149
  t158 = t42 ** 2
  t160 = t48 ** 2
  t164 = (params.af * (-0.2e1 / 0.27e2 * t36 * t137 - 0.2e1 / 0.27e2 * t39 * t141) * t49 - params.af * t158 / t160 - t146 + t151) * t72
  t165 = t51 * t69
  t166 = t165 * t94
  t168 = t78 * t68
  t169 = t94 ** 2
  t173 = 0.1e1 / t59 / t55
  t174 = t84 ** 2
  t177 = 0.1e1 / t123
  t178 = t52 * t177
  t180 = -0.2e1 * t82 + 0.2e1 * t178
  t184 = f.my_piecewise3(t56, 0, -0.2e1 / 0.9e1 * t173 * t174 + 0.2e1 / 0.3e1 * t80 * t180)
  t186 = 0.1e1 / t64 / t62
  t187 = t89 ** 2
  t194 = f.my_piecewise3(t63, 0, -0.2e1 / 0.9e1 * t186 * t187 - 0.2e1 / 0.3e1 * t88 * t180)
  t199 = t146 - t151 + t164 - 0.12e2 * t166 - 0.12e2 * t168 * t169 - 0.6e1 * t79 * (t184 / 0.2e1 + t194 / 0.2e1)
  t202 = t9 * t97
  t203 = t112 * t132
  t206 = t9 * t109
  t207 = t132 ** 2
  t212 = params.h / t116 / t109
  t213 = t97 ** 2
  t221 = t118 * t97 * t2 * t129
  t223 = t81 ** 2
  t229 = 0.35e2 / 0.216e3 * t122 * t98 / t10 / t223 * t128
  t231 = t98 ** 2
  t236 = t103 ** 2
  t237 = t107 ** 2
  t242 = 0.49e2 / 0.6912e4 * t111 * t1 * t231 / t11 / t223 / t81 * t236 / t237
  d11 = 0.2e1 * t113 + 0.2e1 * t133 + t9 * t199 * t112 + 0.2e1 * t202 * t203 + t206 * t112 * t207 + t206 * t112 * (0.2e1 * t212 * t213 * t119 - t118 * t199 * t119 + 0.7e1 / 0.72e2 * t221 + t229 - t242)
  t246 = -t53 - t83
  t249 = f.my_piecewise3(t56, 0, 0.2e1 / 0.3e1 * t80 * t246)
  t250 = -t246
  t253 = f.my_piecewise3(t63, 0, 0.2e1 / 0.3e1 * t88 * t250)
  t255 = t249 / 0.2e1 + t253 / 0.2e1
  t258 = -0.6e1 * t79 * t255 + t35 + t73
  t259 = t258 * t112
  t261 = t165 * t255
  t273 = f.my_piecewise3(t56, 0, -0.2e1 / 0.9e1 * t173 * t246 * t84 + 0.4e1 / 0.3e1 * t80 * t52 * t177)
  t281 = f.my_piecewise3(t63, 0, -0.2e1 / 0.9e1 * t186 * t250 * t89 - 0.4e1 / 0.3e1 * t88 * t52 * t177)
  t286 = t146 - t151 + t164 - 0.6e1 * t166 - 0.6e1 * t261 - 0.12e2 * t168 * t255 * t94 - 0.6e1 * t79 * (t273 / 0.2e1 + t281 / 0.2e1)
  t289 = t9 * t258
  t291 = t258 * t119
  t293 = -t118 * t291 - t131
  t294 = t115 * t293
  t295 = t112 * t293
  t306 = t118 * t258 * t2 * t129
  d12 = t113 + t133 + t259 + t9 * t286 * t112 + t289 * t203 + t294 + t202 * t295 + t206 * t203 * t293 + t206 * t112 * (0.2e1 * t212 * t291 * t97 - t118 * t286 * t119 + 0.7e1 / 0.144e3 * t306 + 0.7e1 / 0.144e3 * t221 + t229 - t242)
  t315 = t255 ** 2
  t318 = t246 ** 2
  t322 = 0.2e1 * t82 + 0.2e1 * t178
  t326 = f.my_piecewise3(t56, 0, -0.2e1 / 0.9e1 * t173 * t318 + 0.2e1 / 0.3e1 * t80 * t322)
  t327 = t250 ** 2
  t334 = f.my_piecewise3(t63, 0, -0.2e1 / 0.9e1 * t186 * t327 - 0.2e1 / 0.3e1 * t88 * t322)
  t339 = t146 - t151 + t164 - 0.12e2 * t261 - 0.12e2 * t168 * t315 - 0.6e1 * t79 * (t326 / 0.2e1 + t334 / 0.2e1)
  t344 = t293 ** 2
  t347 = t258 ** 2
  d22 = 0.2e1 * t259 + 0.2e1 * t294 + t9 * t339 * t112 + 0.2e1 * t289 * t295 + t206 * t112 * t344 + t206 * t112 * (0.2e1 * t212 * t347 * t119 - t118 * t339 * t119 + 0.7e1 / 0.72e2 * t306 + t229 - t242)
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
  t2 = t1 ** 2
  t3 = params.bp * t2
  t5 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t5 * t7
  t9 = r0 + r1
  t10 = t9 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t14 = t8 / t11 / t9
  t16 = params.cp * t1
  t17 = t5 ** 2
  t19 = t7 ** 2
  t20 = 0.1e1 / t17 * t19
  t23 = t20 / t10 / t9
  t27 = params.ap * (-0.2e1 / 0.27e2 * t3 * t14 - 0.2e1 / 0.27e2 * t16 * t23)
  t28 = t8 * t10
  t31 = t20 * t11
  t34 = 0.1e1 + t3 * t28 / 0.3e1 + t16 * t31 / 0.3e1
  t35 = 0.1e1 / t34
  t36 = t27 * t35
  t38 = t8 / t11
  t42 = t20 / t10
  t45 = t3 * t38 / 0.9e1 + 0.2e1 / 0.9e1 * t16 * t42
  t46 = t45 ** 2
  t48 = t34 ** 2
  t49 = 0.1e1 / t48
  t50 = params.ap * t46 * t49
  t51 = params.bf * t2
  t53 = params.cf * t1
  t57 = params.af * (-0.2e1 / 0.27e2 * t51 * t14 - 0.2e1 / 0.27e2 * t53 * t23)
  t62 = 0.1e1 + t51 * t28 / 0.3e1 + t53 * t31 / 0.3e1
  t63 = 0.1e1 / t62
  t69 = t51 * t38 / 0.9e1 + 0.2e1 / 0.9e1 * t53 * t42
  t70 = t69 ** 2
  t72 = t62 ** 2
  t73 = 0.1e1 / t72
  t75 = -params.af * t70 * t73 + t57 * t63 - t36 + t50
  t76 = r0 - r1
  t77 = 0.1e1 / t9
  t78 = t76 * t77
  t79 = 0.1e1 + t78
  t80 = t79 <= f.p.zeta_threshold
  t81 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t83 = t79 ** (0.1e1 / 0.3e1)
  t84 = t83 ** 2
  t85 = f.my_piecewise3(t80, t82, t84)
  t86 = 0.1e1 - t78
  t87 = t86 <= f.p.zeta_threshold
  t88 = t86 ** (0.1e1 / 0.3e1)
  t89 = t88 ** 2
  t90 = f.my_piecewise3(t87, t82, t89)
  t92 = t85 / 0.2e1 + t90 / 0.2e1
  t93 = t92 ** 2
  t96 = -0.2e1 * t93 * t92 + 0.2e1
  t101 = params.ap * t45 * t35
  t102 = params.af * t69 * t63 - t101
  t103 = t102 * t93
  t104 = 0.1e1 / t83
  t105 = t9 ** 2
  t106 = 0.1e1 / t105
  t108 = -t76 * t106 + t77
  t111 = f.my_piecewise3(t80, 0, 0.2e1 / 0.3e1 * t104 * t108)
  t112 = 0.1e1 / t88
  t113 = -t108
  t116 = f.my_piecewise3(t87, 0, 0.2e1 / 0.3e1 * t112 * t113)
  t118 = t111 / 0.2e1 + t116 / 0.2e1
  t121 = jnp.log(t62)
  t123 = jnp.log(t34)
  t124 = params.ap * t123
  t125 = params.af * t121 - t124
  t126 = t125 * t92
  t127 = t118 ** 2
  t130 = t125 * t93
  t132 = 0.1e1 / t83 / t79
  t133 = t108 ** 2
  t136 = t105 * t9
  t137 = 0.1e1 / t136
  t140 = 0.2e1 * t76 * t137 - 0.2e1 * t106
  t144 = f.my_piecewise3(t80, 0, -0.2e1 / 0.9e1 * t132 * t133 + 0.2e1 / 0.3e1 * t104 * t140)
  t146 = 0.1e1 / t88 / t86
  t147 = t113 ** 2
  t150 = -t140
  t154 = f.my_piecewise3(t87, 0, -0.2e1 / 0.9e1 * t146 * t147 + 0.2e1 / 0.3e1 * t112 * t150)
  t156 = t144 / 0.2e1 + t154 / 0.2e1
  t159 = -0.12e2 * t103 * t118 - 0.12e2 * t126 * t127 - 0.6e1 * t130 * t156 + t75 * t96 + t36 - t50
  t160 = jnp.pi ** (0.1e1 / 0.3e1)
  t163 = 0.1e1 / t10 / t105
  t165 = s0 + 0.2e1 * s1 + s2
  t169 = 0.1e1 + t2 * t160 * t163 * t165 / 0.48e2
  t171 = t125 * t96 + t124
  t173 = params.h / t171
  t174 = t169 ** t173
  t180 = t102 * t96 - 0.6e1 * t130 * t118 + t101
  t182 = t171 ** 2
  t184 = params.h / t182
  t185 = jnp.log(t169)
  t186 = t180 * t185
  t188 = t173 * t2
  t193 = t165 / t169
  t194 = t160 / t10 / t136 * t193
  t197 = -t184 * t186 - 0.7e1 / 0.144e3 * t188 * t194
  t200 = t171 * t174
  t201 = t197 ** 2
  t206 = params.h / t182 / t171
  t207 = t180 ** 2
  t214 = t184 * t180 * t2
  t217 = t105 ** 2
  t221 = t160 / t10 / t217 * t193
  t224 = t173 * t1
  t225 = t160 ** 2
  t230 = t165 ** 2
  t231 = t169 ** 2
  t233 = t230 / t231
  t234 = t225 / t11 / t217 / t105 * t233
  t237 = 0.2e1 * t206 * t207 * t185 - t184 * t159 * t185 + 0.7e1 / 0.72e2 * t214 * t194 + 0.35e2 / 0.216e3 * t188 * t221 - 0.49e2 / 0.6912e4 * t224 * t234
  t242 = t8 / t11 / t105
  t245 = t20 * t163
  t250 = params.ap * (0.10e2 / 0.81e2 * t3 * t242 + 0.8e1 / 0.81e2 * t16 * t245) * t35
  t253 = 0.3e1 * t27 * t49 * t45
  t259 = 0.2e1 * params.ap * t46 * t45 / t48 / t34
  t292 = t79 ** 2
  t304 = 0.6e1 * t137 - 0.6e1 * t76 / t217
  t308 = f.my_piecewise3(t80, 0, 0.8e1 / 0.27e2 / t83 / t292 * t133 * t108 - 0.2e1 / 0.3e1 * t132 * t108 * t140 + 0.2e1 / 0.3e1 * t104 * t304)
  t309 = t86 ** 2
  t322 = f.my_piecewise3(t87, 0, 0.8e1 / 0.27e2 / t88 / t309 * t147 * t113 - 0.2e1 / 0.3e1 * t146 * t113 * t150 - 0.2e1 / 0.3e1 * t112 * t304)
  t327 = t250 - t253 + t259 + (params.af * (0.10e2 / 0.81e2 * t51 * t242 + 0.8e1 / 0.81e2 * t53 * t245) * t63 - 0.3e1 * t57 * t73 * t69 + 0.2e1 * params.af * t70 * t69 / t72 / t62 - t250 + t253 - t259) * t96 - 0.18e2 * t75 * t93 * t118 - 0.36e2 * t102 * t92 * t127 - 0.18e2 * t103 * t156 - 0.12e2 * t125 * t127 * t118 - 0.36e2 * t126 * t118 * t156 - 0.6e1 * t130 * (t308 / 0.2e1 + t322 / 0.2e1)
  t331 = t174 * t197
  t334 = t9 * t180
  t341 = t9 * t171
  t348 = t182 ** 2
  t389 = t217 ** 2
  d111 = 0.3e1 * t159 * t174 + 0.6e1 * t180 * t174 * t197 + 0.3e1 * t200 * t201 + 0.3e1 * t200 * t237 + t9 * t327 * t174 + 0.3e1 * t9 * t159 * t331 + 0.3e1 * t334 * t174 * t201 + 0.3e1 * t334 * t174 * t237 + t341 * t174 * t201 * t197 + 0.3e1 * t341 * t331 * t237 + t341 * t174 * (-0.6e1 * params.h / t348 * t207 * t180 * t185 + 0.6e1 * t206 * t186 * t159 - 0.7e1 / 0.24e2 * t206 * t207 * t2 * t194 - t184 * t327 * t185 + 0.7e1 / 0.48e2 * t184 * t159 * t2 * t194 - 0.35e2 / 0.72e2 * t214 * t221 + 0.49e2 / 0.2304e4 * t184 * t180 * t1 * t234 - 0.455e3 / 0.648e3 * t188 * t160 / t10 / t217 / t9 * t193 + 0.245e3 / 0.3456e4 * t224 * t225 / t11 / t217 / t136 * t233 - 0.343e3 / 0.165888e6 * t173 * jnp.pi / t389 / t105 * t230 * t165 / t231 / t169)

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
  t2 = t1 ** 2
  t3 = params.bp * t2
  t5 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t5 * t7
  t9 = r0 + r1
  t10 = t9 ** 2
  t11 = t9 ** (0.1e1 / 0.3e1)
  t12 = t11 ** 2
  t15 = t8 / t12 / t10
  t18 = params.cp * t1
  t19 = t5 ** 2
  t21 = t7 ** 2
  t22 = 0.1e1 / t19 * t21
  t24 = 0.1e1 / t11 / t10
  t25 = t22 * t24
  t29 = params.ap * (0.10e2 / 0.81e2 * t3 * t15 + 0.8e1 / 0.81e2 * t18 * t25)
  t30 = t8 * t11
  t33 = t22 * t12
  t36 = 0.1e1 + t3 * t30 / 0.3e1 + t18 * t33 / 0.3e1
  t37 = 0.1e1 / t36
  t38 = t29 * t37
  t41 = t8 / t12 / t9
  t45 = t22 / t11 / t9
  t48 = -0.2e1 / 0.27e2 * t18 * t45 - 0.2e1 / 0.27e2 * t3 * t41
  t49 = params.ap * t48
  t50 = t36 ** 2
  t51 = 0.1e1 / t50
  t53 = t8 / t12
  t57 = t22 / t11
  t60 = t3 * t53 / 0.9e1 + 0.2e1 / 0.9e1 * t18 * t57
  t61 = t51 * t60
  t63 = 0.3e1 * t49 * t61
  t64 = t60 ** 2
  t68 = 0.1e1 / t50 / t36
  t70 = 0.2e1 * params.ap * t64 * t60 * t68
  t71 = params.bf * t2
  t74 = params.cf * t1
  t78 = params.af * (0.10e2 / 0.81e2 * t71 * t15 + 0.8e1 / 0.81e2 * t74 * t25)
  t83 = 0.1e1 + t71 * t30 / 0.3e1 + t74 * t33 / 0.3e1
  t84 = 0.1e1 / t83
  t89 = -0.2e1 / 0.27e2 * t71 * t41 - 0.2e1 / 0.27e2 * t74 * t45
  t90 = params.af * t89
  t91 = t83 ** 2
  t92 = 0.1e1 / t91
  t97 = t71 * t53 / 0.9e1 + 0.2e1 / 0.9e1 * t74 * t57
  t98 = t92 * t97
  t101 = t97 ** 2
  t105 = 0.1e1 / t91 / t83
  t108 = 0.2e1 * params.af * t101 * t97 * t105 + t78 * t84 - 0.3e1 * t90 * t98 - t38 + t63 - t70
  t109 = r0 - r1
  t110 = 0.1e1 / t9
  t111 = t109 * t110
  t112 = 0.1e1 + t111
  t113 = t112 <= f.p.zeta_threshold
  t114 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t115 = t114 ** 2
  t116 = t112 ** (0.1e1 / 0.3e1)
  t117 = t116 ** 2
  t118 = f.my_piecewise3(t113, t115, t117)
  t119 = 0.1e1 - t111
  t120 = t119 <= f.p.zeta_threshold
  t121 = t119 ** (0.1e1 / 0.3e1)
  t122 = t121 ** 2
  t123 = f.my_piecewise3(t120, t115, t122)
  t125 = t118 / 0.2e1 + t123 / 0.2e1
  t126 = t125 ** 2
  t129 = -0.2e1 * t126 * t125 + 0.2e1
  t134 = t49 * t37
  t136 = params.ap * t64 * t51
  t137 = -params.af * t101 * t92 + t90 * t84 - t134 + t136
  t138 = t137 * t126
  t139 = 0.1e1 / t116
  t140 = 0.1e1 / t10
  t142 = -t109 * t140 + t110
  t145 = f.my_piecewise3(t113, 0, 0.2e1 / 0.3e1 * t139 * t142)
  t146 = 0.1e1 / t121
  t147 = -t142
  t150 = f.my_piecewise3(t120, 0, 0.2e1 / 0.3e1 * t146 * t147)
  t152 = t145 / 0.2e1 + t150 / 0.2e1
  t158 = params.ap * t60 * t37
  t159 = params.af * t97 * t84 - t158
  t160 = t159 * t125
  t161 = t152 ** 2
  t164 = t159 * t126
  t166 = 0.1e1 / t116 / t112
  t167 = t142 ** 2
  t170 = t10 * t9
  t171 = 0.1e1 / t170
  t174 = 0.2e1 * t109 * t171 - 0.2e1 * t140
  t178 = f.my_piecewise3(t113, 0, -0.2e1 / 0.9e1 * t166 * t167 + 0.2e1 / 0.3e1 * t139 * t174)
  t180 = 0.1e1 / t121 / t119
  t181 = t147 ** 2
  t184 = -t174
  t188 = f.my_piecewise3(t120, 0, -0.2e1 / 0.9e1 * t180 * t181 + 0.2e1 / 0.3e1 * t146 * t184)
  t190 = t178 / 0.2e1 + t188 / 0.2e1
  t193 = jnp.log(t83)
  t195 = jnp.log(t36)
  t196 = params.ap * t195
  t197 = params.af * t193 - t196
  t198 = t161 * t152
  t201 = t197 * t125
  t202 = t152 * t190
  t205 = t197 * t126
  t206 = t112 ** 2
  t208 = 0.1e1 / t116 / t206
  t212 = t166 * t142
  t215 = t10 ** 2
  t216 = 0.1e1 / t215
  t219 = -0.6e1 * t109 * t216 + 0.6e1 * t171
  t223 = f.my_piecewise3(t113, 0, 0.8e1 / 0.27e2 * t208 * t167 * t142 - 0.2e1 / 0.3e1 * t212 * t174 + 0.2e1 / 0.3e1 * t139 * t219)
  t224 = t119 ** 2
  t226 = 0.1e1 / t121 / t224
  t230 = t180 * t147
  t233 = -t219
  t237 = f.my_piecewise3(t120, 0, 0.8e1 / 0.27e2 * t226 * t181 * t147 - 0.2e1 / 0.3e1 * t230 * t184 + 0.2e1 / 0.3e1 * t146 * t233)
  t239 = t223 / 0.2e1 + t237 / 0.2e1
  t242 = t108 * t129 - 0.18e2 * t138 * t152 - 0.36e2 * t160 * t161 - 0.18e2 * t164 * t190 - 0.12e2 * t197 * t198 - 0.36e2 * t201 * t202 - 0.6e1 * t205 * t239 + t38 - t63 + t70
  t243 = jnp.pi ** (0.1e1 / 0.3e1)
  t246 = s0 + 0.2e1 * s1 + s2
  t250 = 0.1e1 + t2 * t243 * t24 * t246 / 0.48e2
  t252 = t197 * t129 + t196
  t254 = params.h / t252
  t255 = t250 ** t254
  t265 = t137 * t129 - 0.12e2 * t164 * t152 - 0.12e2 * t201 * t161 - 0.6e1 * t205 * t190 + t134 - t136
  t267 = t252 ** 2
  t269 = params.h / t267
  t273 = t159 * t129 - 0.6e1 * t205 * t152 + t158
  t274 = jnp.log(t250)
  t275 = t273 * t274
  t277 = t254 * t2
  t279 = 0.1e1 / t11 / t170
  t280 = t243 * t279
  t282 = t246 / t250
  t283 = t280 * t282
  t286 = -t269 * t275 - 0.7e1 / 0.144e3 * t277 * t283
  t289 = t273 * t255
  t292 = params.h / t267 / t252
  t293 = t273 ** 2
  t294 = t293 * t274
  t299 = t273 * t2
  t300 = t269 * t299
  t306 = t243 / t11 / t215 * t282
  t309 = t254 * t1
  t310 = t243 ** 2
  t311 = t215 * t10
  t315 = t246 ** 2
  t316 = t250 ** 2
  t318 = t315 / t316
  t319 = t310 / t12 / t311 * t318
  t322 = 0.2e1 * t292 * t294 - t269 * t265 * t274 + 0.7e1 / 0.72e2 * t300 * t283 + 0.35e2 / 0.216e3 * t277 * t306 - 0.49e2 / 0.6912e4 * t309 * t319
  t325 = t252 * t255
  t326 = t267 ** 2
  t328 = params.h / t326
  t329 = t293 * t273
  t337 = t292 * t293 * t2
  t343 = t269 * t265 * t2
  t349 = t269 * t273 * t1
  t352 = t215 * t9
  t356 = t243 / t11 / t352 * t282
  t363 = t310 / t12 / t215 / t170 * t318
  t366 = t254 * jnp.pi
  t367 = t215 ** 2
  t369 = 0.1e1 / t367 / t10
  t370 = t315 * t246
  t373 = 0.1e1 / t316 / t250
  t377 = -0.6e1 * t328 * t329 * t274 + 0.6e1 * t292 * t275 * t265 - 0.7e1 / 0.24e2 * t337 * t283 - t269 * t242 * t274 + 0.7e1 / 0.48e2 * t343 * t283 - 0.35e2 / 0.72e2 * t300 * t306 + 0.49e2 / 0.2304e4 * t349 * t319 - 0.455e3 / 0.648e3 * t277 * t356 + 0.245e3 / 0.3456e4 * t309 * t363 - 0.343e3 / 0.165888e6 * t366 * t369 * t370 * t373
  t382 = t8 / t12 / t170
  t385 = t22 * t279
  t396 = t89 ** 2
  t400 = t101 ** 2
  t402 = t91 ** 2
  t412 = params.ap * (-0.80e2 / 0.243e3 * t3 * t382 - 0.56e2 / 0.243e3 * t18 * t385) * t37
  t414 = 0.4e1 * t29 * t61
  t417 = 0.12e2 * t49 * t68 * t64
  t418 = t48 ** 2
  t421 = 0.3e1 * params.ap * t418 * t51
  t422 = t64 ** 2
  t424 = t50 ** 2
  t427 = 0.6e1 * params.ap * t422 / t424
  t433 = t167 ** 2
  t439 = t174 ** 2
  t447 = -0.24e2 * t216 + 0.24e2 * t109 / t352
  t451 = f.my_piecewise3(t113, 0, -0.56e2 / 0.81e2 / t116 / t206 / t112 * t433 + 0.16e2 / 0.9e1 * t208 * t167 * t174 - 0.2e1 / 0.3e1 * t166 * t439 - 0.8e1 / 0.9e1 * t212 * t219 + 0.2e1 / 0.3e1 * t139 * t447)
  t455 = t181 ** 2
  t461 = t184 ** 2
  t470 = f.my_piecewise3(t120, 0, -0.56e2 / 0.81e2 / t121 / t224 / t119 * t455 + 0.16e2 / 0.9e1 * t226 * t181 * t184 - 0.2e1 / 0.3e1 * t180 * t461 - 0.8e1 / 0.9e1 * t230 * t233 - 0.2e1 / 0.3e1 * t146 * t447)
  t492 = t190 ** 2
  t498 = (params.af * (-0.80e2 / 0.243e3 * t71 * t382 - 0.56e2 / 0.243e3 * t74 * t385) * t84 - 0.4e1 * t78 * t98 + 0.12e2 * t90 * t105 * t101 - 0.3e1 * params.af * t396 * t92 - 0.6e1 * params.af * t400 / t402 - t412 + t414 - t417 + t421 + t427) * t129 - 0.6e1 * t205 * (t451 / 0.2e1 + t470 / 0.2e1) + t412 - 0.24e2 * t108 * t126 * t152 - 0.36e2 * t138 * t190 - 0.48e2 * t159 * t198 - 0.24e2 * t164 * t239 - 0.72e2 * t197 * t161 * t190 + t417 - t414 - t421 - t427 - 0.72e2 * t137 * t125 * t161 - 0.144e3 * t160 * t202 - 0.36e2 * t201 * t492 - 0.48e2 * t201 * t152 * t239
  t501 = t9 * t252
  t502 = t322 ** 2
  t506 = t255 * t286
  t510 = t9 * t265
  t511 = t286 ** 2
  t512 = t255 * t511
  t515 = t9 * t273
  t519 = t511 * t286
  t526 = t511 ** 2
  t565 = t293 ** 2
  t572 = t265 ** 2
  t596 = t315 ** 2
  t598 = t316 ** 2
  t630 = -0.7e1 / 0.6e1 * t292 * t299 * t280 * t282 * t265 + 0.35e2 / 0.18e2 * t337 * t306 - 0.35e2 / 0.36e2 * t343 * t306 + 0.455e3 / 0.162e3 * t300 * t356 + 0.1715e4 / 0.41472e5 * t366 / t367 / t170 * t370 * t373 + 0.24e2 * params.h / t326 / t252 * t565 * t274 - 0.36e2 * t328 * t294 * t265 + 0.6e1 * t292 * t572 * t274 + 0.8e1 * t292 * t275 * t242 + 0.343e3 / 0.41472e5 * t269 * t273 * jnp.pi * t369 * t370 * t373 - 0.10045e5 / 0.15552e5 * t309 * t310 / t12 / t367 * t318 - 0.2401e4 / 0.7962624e7 * t254 * t243 * jnp.pi / t11 / t367 / t352 * t596 / t598 * t2 - t269 * t498 * t274 + 0.7e1 / 0.6e1 * t328 * t329 * t2 * t283 - 0.49e2 / 0.576e3 * t292 * t293 * t1 * t319 + 0.7e1 / 0.36e2 * t269 * t242 * t2 * t283 + 0.49e2 / 0.1152e4 * t269 * t265 * t1 * t319 - 0.245e3 / 0.864e3 * t349 * t363 + 0.910e3 / 0.243e3 * t277 * t243 / t11 / t311 * t282
  d1111 = 0.4e1 * t9 * t242 * t506 + 0.12e2 * t265 * t255 * t286 + 0.6e1 * t510 * t255 * t322 + 0.4e1 * t515 * t255 * t377 + t9 * t498 * t255 + 0.3e1 * t501 * t255 * t502 + t501 * t255 * t526 + t501 * t255 * t630 + 0.4e1 * t515 * t255 * t519 + 0.12e2 * t325 * t286 * t322 + 0.6e1 * t501 * t512 * t322 + 0.12e2 * t515 * t506 * t322 + 0.4e1 * t501 * t506 * t377 + 0.4e1 * t242 * t255 + 0.12e2 * t289 * t322 + 0.12e2 * t289 * t511 + 0.4e1 * t325 * t377 + 0.4e1 * t325 * t519 + 0.6e1 * t510 * t512

  res = {'v4rho4': d1111}
  return res
