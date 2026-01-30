"""Generated from mgga_x_ktbm.mpl."""

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
  params_a2b_raw = params.a2b
  if isinstance(params_a2b_raw, (str, bytes, dict)):
    params_a2b = params_a2b_raw
  else:
    try:
      params_a2b_seq = list(params_a2b_raw)
    except TypeError:
      params_a2b = params_a2b_raw
    else:
      params_a2b_seq = np.asarray(params_a2b_seq, dtype=np.float64)
      params_a2b = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2b_seq))
  params_a2t_raw = params.a2t
  if isinstance(params_a2t_raw, (str, bytes, dict)):
    params_a2t = params_a2t_raw
  else:
    try:
      params_a2t_seq = list(params_a2t_raw)
    except TypeError:
      params_a2t = params_a2t_raw
    else:
      params_a2t_seq = np.asarray(params_a2t_seq, dtype=np.float64)
      params_a2t = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2t_seq))
  params_ab_raw = params.ab
  if isinstance(params_ab_raw, (str, bytes, dict)):
    params_ab = params_ab_raw
  else:
    try:
      params_ab_seq = list(params_ab_raw)
    except TypeError:
      params_ab = params_ab_raw
    else:
      params_ab_seq = np.asarray(params_ab_seq, dtype=np.float64)
      params_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_ab_seq))
  params_at_raw = params.at
  if isinstance(params_at_raw, (str, bytes, dict)):
    params_at = params_at_raw
  else:
    try:
      params_at_seq = list(params_at_raw)
    except TypeError:
      params_at = params_at_raw
    else:
      params_at_seq = np.asarray(params_at_seq, dtype=np.float64)
      params_at = np.concatenate((np.array([np.nan], dtype=np.float64), params_at_seq))
  params_b2b_raw = params.b2b
  if isinstance(params_b2b_raw, (str, bytes, dict)):
    params_b2b = params_b2b_raw
  else:
    try:
      params_b2b_seq = list(params_b2b_raw)
    except TypeError:
      params_b2b = params_b2b_raw
    else:
      params_b2b_seq = np.asarray(params_b2b_seq, dtype=np.float64)
      params_b2b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2b_seq))
  params_b2t_raw = params.b2t
  if isinstance(params_b2t_raw, (str, bytes, dict)):
    params_b2t = params_b2t_raw
  else:
    try:
      params_b2t_seq = list(params_b2t_raw)
    except TypeError:
      params_b2t = params_b2t_raw
    else:
      params_b2t_seq = np.asarray(params_b2t_seq, dtype=np.float64)
      params_b2t = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2t_seq))
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
  params_bt_raw = params.bt
  if isinstance(params_bt_raw, (str, bytes, dict)):
    params_bt = params_bt_raw
  else:
    try:
      params_bt_seq = list(params_bt_raw)
    except TypeError:
      params_bt = params_bt_raw
    else:
      params_bt_seq = np.asarray(params_bt_seq, dtype=np.float64)
      params_bt = np.concatenate((np.array([np.nan], dtype=np.float64), params_bt_seq))
  params_cb_raw = params.cb
  if isinstance(params_cb_raw, (str, bytes, dict)):
    params_cb = params_cb_raw
  else:
    try:
      params_cb_seq = list(params_cb_raw)
    except TypeError:
      params_cb = params_cb_raw
    else:
      params_cb_seq = np.asarray(params_cb_seq, dtype=np.float64)
      params_cb = np.concatenate((np.array([np.nan], dtype=np.float64), params_cb_seq))
  params_ct_raw = params.ct
  if isinstance(params_ct_raw, (str, bytes, dict)):
    params_ct = params_ct_raw
  else:
    try:
      params_ct_seq = list(params_ct_raw)
    except TypeError:
      params_ct = params_ct_raw
    else:
      params_ct_seq = np.asarray(params_ct_seq, dtype=np.float64)
      params_ct = np.concatenate((np.array([np.nan], dtype=np.float64), params_ct_seq))
  params_xb_raw = params.xb
  if isinstance(params_xb_raw, (str, bytes, dict)):
    params_xb = params_xb_raw
  else:
    try:
      params_xb_seq = list(params_xb_raw)
    except TypeError:
      params_xb = params_xb_raw
    else:
      params_xb_seq = np.asarray(params_xb_seq, dtype=np.float64)
      params_xb = np.concatenate((np.array([np.nan], dtype=np.float64), params_xb_seq))
  params_xt_raw = params.xt
  if isinstance(params_xt_raw, (str, bytes, dict)):
    params_xt = params_xt_raw
  else:
    try:
      params_xt_seq = list(params_xt_raw)
    except TypeError:
      params_xt = params_xt_raw
    else:
      params_xt_seq = np.asarray(params_xt_seq, dtype=np.float64)
      params_xt = np.concatenate((np.array([np.nan], dtype=np.float64), params_xt_seq))

  ktbm_p = lambda x: X2S ** 2 * x ** 2

  ktbm_t = lambda t: t / K_FACTOR_C

  ktbm_top = lambda p, t: params_ct + params_at * p + params_bt * t + params_a2t * p * p + params_b2t * t * t + params_xt * p * t

  ktbm_bot = lambda p, t: params_cb + params_ab * p + params_bb * t + params_a2b * p * p + params_b2b * t * t + params_xb * p * t

  ktbm_f = lambda x, u, t: ktbm_top(ktbm_p(x), ktbm_t(t)) / ktbm_bot(ktbm_p(x), ktbm_t(t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ktbm_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_a2b_raw = params.a2b
  if isinstance(params_a2b_raw, (str, bytes, dict)):
    params_a2b = params_a2b_raw
  else:
    try:
      params_a2b_seq = list(params_a2b_raw)
    except TypeError:
      params_a2b = params_a2b_raw
    else:
      params_a2b_seq = np.asarray(params_a2b_seq, dtype=np.float64)
      params_a2b = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2b_seq))
  params_a2t_raw = params.a2t
  if isinstance(params_a2t_raw, (str, bytes, dict)):
    params_a2t = params_a2t_raw
  else:
    try:
      params_a2t_seq = list(params_a2t_raw)
    except TypeError:
      params_a2t = params_a2t_raw
    else:
      params_a2t_seq = np.asarray(params_a2t_seq, dtype=np.float64)
      params_a2t = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2t_seq))
  params_ab_raw = params.ab
  if isinstance(params_ab_raw, (str, bytes, dict)):
    params_ab = params_ab_raw
  else:
    try:
      params_ab_seq = list(params_ab_raw)
    except TypeError:
      params_ab = params_ab_raw
    else:
      params_ab_seq = np.asarray(params_ab_seq, dtype=np.float64)
      params_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_ab_seq))
  params_at_raw = params.at
  if isinstance(params_at_raw, (str, bytes, dict)):
    params_at = params_at_raw
  else:
    try:
      params_at_seq = list(params_at_raw)
    except TypeError:
      params_at = params_at_raw
    else:
      params_at_seq = np.asarray(params_at_seq, dtype=np.float64)
      params_at = np.concatenate((np.array([np.nan], dtype=np.float64), params_at_seq))
  params_b2b_raw = params.b2b
  if isinstance(params_b2b_raw, (str, bytes, dict)):
    params_b2b = params_b2b_raw
  else:
    try:
      params_b2b_seq = list(params_b2b_raw)
    except TypeError:
      params_b2b = params_b2b_raw
    else:
      params_b2b_seq = np.asarray(params_b2b_seq, dtype=np.float64)
      params_b2b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2b_seq))
  params_b2t_raw = params.b2t
  if isinstance(params_b2t_raw, (str, bytes, dict)):
    params_b2t = params_b2t_raw
  else:
    try:
      params_b2t_seq = list(params_b2t_raw)
    except TypeError:
      params_b2t = params_b2t_raw
    else:
      params_b2t_seq = np.asarray(params_b2t_seq, dtype=np.float64)
      params_b2t = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2t_seq))
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
  params_bt_raw = params.bt
  if isinstance(params_bt_raw, (str, bytes, dict)):
    params_bt = params_bt_raw
  else:
    try:
      params_bt_seq = list(params_bt_raw)
    except TypeError:
      params_bt = params_bt_raw
    else:
      params_bt_seq = np.asarray(params_bt_seq, dtype=np.float64)
      params_bt = np.concatenate((np.array([np.nan], dtype=np.float64), params_bt_seq))
  params_cb_raw = params.cb
  if isinstance(params_cb_raw, (str, bytes, dict)):
    params_cb = params_cb_raw
  else:
    try:
      params_cb_seq = list(params_cb_raw)
    except TypeError:
      params_cb = params_cb_raw
    else:
      params_cb_seq = np.asarray(params_cb_seq, dtype=np.float64)
      params_cb = np.concatenate((np.array([np.nan], dtype=np.float64), params_cb_seq))
  params_ct_raw = params.ct
  if isinstance(params_ct_raw, (str, bytes, dict)):
    params_ct = params_ct_raw
  else:
    try:
      params_ct_seq = list(params_ct_raw)
    except TypeError:
      params_ct = params_ct_raw
    else:
      params_ct_seq = np.asarray(params_ct_seq, dtype=np.float64)
      params_ct = np.concatenate((np.array([np.nan], dtype=np.float64), params_ct_seq))
  params_xb_raw = params.xb
  if isinstance(params_xb_raw, (str, bytes, dict)):
    params_xb = params_xb_raw
  else:
    try:
      params_xb_seq = list(params_xb_raw)
    except TypeError:
      params_xb = params_xb_raw
    else:
      params_xb_seq = np.asarray(params_xb_seq, dtype=np.float64)
      params_xb = np.concatenate((np.array([np.nan], dtype=np.float64), params_xb_seq))
  params_xt_raw = params.xt
  if isinstance(params_xt_raw, (str, bytes, dict)):
    params_xt = params_xt_raw
  else:
    try:
      params_xt_seq = list(params_xt_raw)
    except TypeError:
      params_xt = params_xt_raw
    else:
      params_xt_seq = np.asarray(params_xt_seq, dtype=np.float64)
      params_xt = np.concatenate((np.array([np.nan], dtype=np.float64), params_xt_seq))

  ktbm_p = lambda x: X2S ** 2 * x ** 2

  ktbm_t = lambda t: t / K_FACTOR_C

  ktbm_top = lambda p, t: params_ct + params_at * p + params_bt * t + params_a2t * p * p + params_b2t * t * t + params_xt * p * t

  ktbm_bot = lambda p, t: params_cb + params_ab * p + params_bb * t + params_a2b * p * p + params_b2b * t * t + params_xb * p * t

  ktbm_f = lambda x, u, t: ktbm_top(ktbm_p(x), ktbm_t(t)) / ktbm_bot(ktbm_p(x), ktbm_t(t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ktbm_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_a2b_raw = params.a2b
  if isinstance(params_a2b_raw, (str, bytes, dict)):
    params_a2b = params_a2b_raw
  else:
    try:
      params_a2b_seq = list(params_a2b_raw)
    except TypeError:
      params_a2b = params_a2b_raw
    else:
      params_a2b_seq = np.asarray(params_a2b_seq, dtype=np.float64)
      params_a2b = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2b_seq))
  params_a2t_raw = params.a2t
  if isinstance(params_a2t_raw, (str, bytes, dict)):
    params_a2t = params_a2t_raw
  else:
    try:
      params_a2t_seq = list(params_a2t_raw)
    except TypeError:
      params_a2t = params_a2t_raw
    else:
      params_a2t_seq = np.asarray(params_a2t_seq, dtype=np.float64)
      params_a2t = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2t_seq))
  params_ab_raw = params.ab
  if isinstance(params_ab_raw, (str, bytes, dict)):
    params_ab = params_ab_raw
  else:
    try:
      params_ab_seq = list(params_ab_raw)
    except TypeError:
      params_ab = params_ab_raw
    else:
      params_ab_seq = np.asarray(params_ab_seq, dtype=np.float64)
      params_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_ab_seq))
  params_at_raw = params.at
  if isinstance(params_at_raw, (str, bytes, dict)):
    params_at = params_at_raw
  else:
    try:
      params_at_seq = list(params_at_raw)
    except TypeError:
      params_at = params_at_raw
    else:
      params_at_seq = np.asarray(params_at_seq, dtype=np.float64)
      params_at = np.concatenate((np.array([np.nan], dtype=np.float64), params_at_seq))
  params_b2b_raw = params.b2b
  if isinstance(params_b2b_raw, (str, bytes, dict)):
    params_b2b = params_b2b_raw
  else:
    try:
      params_b2b_seq = list(params_b2b_raw)
    except TypeError:
      params_b2b = params_b2b_raw
    else:
      params_b2b_seq = np.asarray(params_b2b_seq, dtype=np.float64)
      params_b2b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2b_seq))
  params_b2t_raw = params.b2t
  if isinstance(params_b2t_raw, (str, bytes, dict)):
    params_b2t = params_b2t_raw
  else:
    try:
      params_b2t_seq = list(params_b2t_raw)
    except TypeError:
      params_b2t = params_b2t_raw
    else:
      params_b2t_seq = np.asarray(params_b2t_seq, dtype=np.float64)
      params_b2t = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2t_seq))
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
  params_bt_raw = params.bt
  if isinstance(params_bt_raw, (str, bytes, dict)):
    params_bt = params_bt_raw
  else:
    try:
      params_bt_seq = list(params_bt_raw)
    except TypeError:
      params_bt = params_bt_raw
    else:
      params_bt_seq = np.asarray(params_bt_seq, dtype=np.float64)
      params_bt = np.concatenate((np.array([np.nan], dtype=np.float64), params_bt_seq))
  params_cb_raw = params.cb
  if isinstance(params_cb_raw, (str, bytes, dict)):
    params_cb = params_cb_raw
  else:
    try:
      params_cb_seq = list(params_cb_raw)
    except TypeError:
      params_cb = params_cb_raw
    else:
      params_cb_seq = np.asarray(params_cb_seq, dtype=np.float64)
      params_cb = np.concatenate((np.array([np.nan], dtype=np.float64), params_cb_seq))
  params_ct_raw = params.ct
  if isinstance(params_ct_raw, (str, bytes, dict)):
    params_ct = params_ct_raw
  else:
    try:
      params_ct_seq = list(params_ct_raw)
    except TypeError:
      params_ct = params_ct_raw
    else:
      params_ct_seq = np.asarray(params_ct_seq, dtype=np.float64)
      params_ct = np.concatenate((np.array([np.nan], dtype=np.float64), params_ct_seq))
  params_xb_raw = params.xb
  if isinstance(params_xb_raw, (str, bytes, dict)):
    params_xb = params_xb_raw
  else:
    try:
      params_xb_seq = list(params_xb_raw)
    except TypeError:
      params_xb = params_xb_raw
    else:
      params_xb_seq = np.asarray(params_xb_seq, dtype=np.float64)
      params_xb = np.concatenate((np.array([np.nan], dtype=np.float64), params_xb_seq))
  params_xt_raw = params.xt
  if isinstance(params_xt_raw, (str, bytes, dict)):
    params_xt = params_xt_raw
  else:
    try:
      params_xt_seq = list(params_xt_raw)
    except TypeError:
      params_xt = params_xt_raw
    else:
      params_xt_seq = np.asarray(params_xt_seq, dtype=np.float64)
      params_xt = np.concatenate((np.array([np.nan], dtype=np.float64), params_xt_seq))

  ktbm_p = lambda x: X2S ** 2 * x ** 2

  ktbm_t = lambda t: t / K_FACTOR_C

  ktbm_top = lambda p, t: params_ct + params_at * p + params_bt * t + params_a2t * p * p + params_b2t * t * t + params_xt * p * t

  ktbm_bot = lambda p, t: params_cb + params_ab * p + params_bb * t + params_a2b * p * p + params_b2b * t * t + params_xb * p * t

  ktbm_f = lambda x, u, t: ktbm_top(ktbm_p(x), ktbm_t(t)) / ktbm_bot(ktbm_p(x), ktbm_t(t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ktbm_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = t21 * f.p.zeta_threshold
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t20, t22, t23 * t19)
  t26 = t5 * t25
  t27 = t6 ** (0.1e1 / 0.3e1)
  t28 = 6 ** (0.1e1 / 0.3e1)
  t29 = params.at * t28
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = t33 * s0
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t40 = t34 * t39
  t43 = params.bt * tau0
  t45 = 0.1e1 / t37 / r0
  t47 = t45 * t28 * t33
  t50 = t28 ** 2
  t51 = params.a2t * t50
  t53 = 0.1e1 / t31 / t30
  t54 = s0 ** 2
  t55 = t53 * t54
  t56 = t35 ** 2
  t59 = 0.1e1 / t36 / t56 / r0
  t60 = t55 * t59
  t63 = tau0 ** 2
  t64 = params.b2t * t63
  t65 = t35 * r0
  t69 = 0.1e1 / t36 / t65 * t50 * t53
  t72 = params.xt * t50
  t73 = t72 * t53
  t75 = 0.1e1 / t36 / t56
  t77 = s0 * t75 * tau0
  t80 = params.ct + t29 * t40 / 0.24e2 + 0.5e1 / 0.9e1 * t43 * t47 + t51 * t60 / 0.576e3 + 0.25e2 / 0.81e2 * t64 * t69 + 0.5e1 / 0.216e3 * t73 * t77
  t81 = t27 * t80
  t82 = params.ab * t28
  t85 = params.bb * tau0
  t88 = params.a2b * t50
  t91 = params.b2b * t63
  t94 = params.xb * t50
  t95 = t94 * t53
  t98 = params.cb + t82 * t40 / 0.24e2 + 0.5e1 / 0.9e1 * t85 * t47 + t88 * t60 / 0.576e3 + 0.25e2 / 0.81e2 * t91 * t69 + 0.5e1 / 0.216e3 * t95 * t77
  t99 = 0.1e1 / t98
  t100 = t81 * t99
  t103 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t100)
  t104 = r1 <= f.p.dens_threshold
  t105 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t106 = 0.1e1 + t105
  t107 = t106 <= f.p.zeta_threshold
  t108 = t106 ** (0.1e1 / 0.3e1)
  t110 = f.my_piecewise3(t107, t22, t108 * t106)
  t111 = t5 * t110
  t112 = t33 * s2
  t113 = r1 ** 2
  t114 = r1 ** (0.1e1 / 0.3e1)
  t115 = t114 ** 2
  t117 = 0.1e1 / t115 / t113
  t118 = t112 * t117
  t121 = params.bt * tau1
  t123 = 0.1e1 / t115 / r1
  t125 = t123 * t28 * t33
  t128 = s2 ** 2
  t129 = t53 * t128
  t130 = t113 ** 2
  t133 = 0.1e1 / t114 / t130 / r1
  t134 = t129 * t133
  t137 = tau1 ** 2
  t138 = params.b2t * t137
  t139 = t113 * r1
  t143 = 0.1e1 / t114 / t139 * t50 * t53
  t147 = 0.1e1 / t114 / t130
  t149 = s2 * t147 * tau1
  t152 = params.ct + t29 * t118 / 0.24e2 + 0.5e1 / 0.9e1 * t121 * t125 + t51 * t134 / 0.576e3 + 0.25e2 / 0.81e2 * t138 * t143 + 0.5e1 / 0.216e3 * t73 * t149
  t153 = t27 * t152
  t156 = params.bb * tau1
  t161 = params.b2b * t137
  t166 = params.cb + t82 * t118 / 0.24e2 + 0.5e1 / 0.9e1 * t156 * t125 + t88 * t134 / 0.576e3 + 0.25e2 / 0.81e2 * t161 * t143 + 0.5e1 / 0.216e3 * t95 * t149
  t167 = 0.1e1 / t166
  t168 = t153 * t167
  t171 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t111 * t168)
  t172 = t6 ** 2
  t174 = t16 / t172
  t175 = t7 - t174
  t176 = f.my_piecewise5(t10, 0, t14, 0, t175)
  t179 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t176)
  t183 = t27 ** 2
  t184 = 0.1e1 / t183
  t188 = t26 * t184 * t80 * t99 / 0.8e1
  t191 = t34 / t37 / t65
  t195 = t39 * t28 * t33
  t201 = t55 / t36 / t56 / t35
  t205 = t75 * t50 * t53
  t209 = s0 * t59 * tau0
  t217 = t98 ** 2
  t218 = 0.1e1 / t217
  t235 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t179 * t100 - t188 - 0.3e1 / 0.8e1 * t26 * t27 * (-t29 * t191 / 0.9e1 - 0.25e2 / 0.27e2 * t43 * t195 - t51 * t201 / 0.108e3 - 0.250e3 / 0.243e3 * t64 * t205 - 0.65e2 / 0.648e3 * t73 * t209) * t99 + 0.3e1 / 0.8e1 * t26 * t81 * t218 * (-t82 * t191 / 0.9e1 - 0.25e2 / 0.27e2 * t85 * t195 - t88 * t201 / 0.108e3 - 0.250e3 / 0.243e3 * t91 * t205 - 0.65e2 / 0.648e3 * t95 * t209))
  t237 = f.my_piecewise5(t14, 0, t10, 0, -t175)
  t240 = f.my_piecewise3(t107, 0, 0.4e1 / 0.3e1 * t108 * t237)
  t247 = t111 * t184 * t152 * t167 / 0.8e1
  t249 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t5 * t240 * t168 - t247)
  vrho_0_ = t103 + t171 + t6 * (t235 + t249)
  t252 = -t7 - t174
  t253 = f.my_piecewise5(t10, 0, t14, 0, t252)
  t256 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t253)
  t261 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t256 * t100 - t188)
  t263 = f.my_piecewise5(t14, 0, t10, 0, -t252)
  t266 = f.my_piecewise3(t107, 0, 0.4e1 / 0.3e1 * t108 * t263)
  t272 = t112 / t115 / t139
  t276 = t117 * t28 * t33
  t282 = t129 / t114 / t130 / t113
  t286 = t147 * t50 * t53
  t290 = s2 * t133 * tau1
  t298 = t166 ** 2
  t299 = 0.1e1 / t298
  t316 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t5 * t266 * t168 - t247 - 0.3e1 / 0.8e1 * t111 * t27 * (-t29 * t272 / 0.9e1 - 0.25e2 / 0.27e2 * t121 * t276 - t51 * t282 / 0.108e3 - 0.250e3 / 0.243e3 * t138 * t286 - 0.65e2 / 0.648e3 * t73 * t290) * t167 + 0.3e1 / 0.8e1 * t111 * t153 * t299 * (-t82 * t272 / 0.9e1 - 0.25e2 / 0.27e2 * t156 * t276 - t88 * t282 / 0.108e3 - 0.250e3 / 0.243e3 * t161 * t286 - 0.65e2 / 0.648e3 * t95 * t290))
  vrho_1_ = t103 + t171 + t6 * (t261 + t316)
  t319 = t33 * t39
  t322 = t53 * s0
  t323 = t322 * t59
  t327 = t53 * t75 * tau0
  t346 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (t29 * t319 / 0.24e2 + t51 * t323 / 0.288e3 + 0.5e1 / 0.216e3 * t72 * t327) * t99 + 0.3e1 / 0.8e1 * t26 * t81 * t218 * (t82 * t319 / 0.24e2 + t88 * t323 / 0.288e3 + 0.5e1 / 0.216e3 * t94 * t327))
  vsigma_0_ = t6 * t346
  vsigma_1_ = 0.0e0
  t347 = t33 * t117
  t350 = t53 * s2
  t351 = t350 * t133
  t355 = t53 * t147 * tau1
  t374 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t111 * t27 * (t29 * t347 / 0.24e2 + t51 * t351 / 0.288e3 + 0.5e1 / 0.216e3 * t72 * t355) * t167 + 0.3e1 / 0.8e1 * t111 * t153 * t299 * (t82 * t347 / 0.24e2 + t88 * t351 / 0.288e3 + 0.5e1 / 0.216e3 * t94 * t355))
  vsigma_2_ = t6 * t374
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t376 = t28 * t33
  t382 = t322 * t75
  t403 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (0.5e1 / 0.9e1 * params.bt * t45 * t376 + 0.50e2 / 0.81e2 * params.b2t * tau0 * t69 + 0.5e1 / 0.216e3 * t72 * t382) * t99 + 0.3e1 / 0.8e1 * t26 * t81 * t218 * (0.5e1 / 0.9e1 * params.bb * t45 * t376 + 0.50e2 / 0.81e2 * params.b2b * tau0 * t69 + 0.5e1 / 0.216e3 * t94 * t382))
  vtau_0_ = t6 * t403
  t410 = t350 * t147
  t431 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t111 * t27 * (0.5e1 / 0.9e1 * params.bt * t123 * t376 + 0.50e2 / 0.81e2 * params.b2t * tau1 * t143 + 0.5e1 / 0.216e3 * t72 * t410) * t167 + 0.3e1 / 0.8e1 * t111 * t153 * t299 * (0.5e1 / 0.9e1 * params.bb * t123 * t376 + 0.50e2 / 0.81e2 * params.b2b * tau1 * t143 + 0.5e1 / 0.216e3 * t94 * t410))
  vtau_1_ = t6 * t431
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
  params_a2b_raw = params.a2b
  if isinstance(params_a2b_raw, (str, bytes, dict)):
    params_a2b = params_a2b_raw
  else:
    try:
      params_a2b_seq = list(params_a2b_raw)
    except TypeError:
      params_a2b = params_a2b_raw
    else:
      params_a2b_seq = np.asarray(params_a2b_seq, dtype=np.float64)
      params_a2b = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2b_seq))
  params_a2t_raw = params.a2t
  if isinstance(params_a2t_raw, (str, bytes, dict)):
    params_a2t = params_a2t_raw
  else:
    try:
      params_a2t_seq = list(params_a2t_raw)
    except TypeError:
      params_a2t = params_a2t_raw
    else:
      params_a2t_seq = np.asarray(params_a2t_seq, dtype=np.float64)
      params_a2t = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2t_seq))
  params_ab_raw = params.ab
  if isinstance(params_ab_raw, (str, bytes, dict)):
    params_ab = params_ab_raw
  else:
    try:
      params_ab_seq = list(params_ab_raw)
    except TypeError:
      params_ab = params_ab_raw
    else:
      params_ab_seq = np.asarray(params_ab_seq, dtype=np.float64)
      params_ab = np.concatenate((np.array([np.nan], dtype=np.float64), params_ab_seq))
  params_at_raw = params.at
  if isinstance(params_at_raw, (str, bytes, dict)):
    params_at = params_at_raw
  else:
    try:
      params_at_seq = list(params_at_raw)
    except TypeError:
      params_at = params_at_raw
    else:
      params_at_seq = np.asarray(params_at_seq, dtype=np.float64)
      params_at = np.concatenate((np.array([np.nan], dtype=np.float64), params_at_seq))
  params_b2b_raw = params.b2b
  if isinstance(params_b2b_raw, (str, bytes, dict)):
    params_b2b = params_b2b_raw
  else:
    try:
      params_b2b_seq = list(params_b2b_raw)
    except TypeError:
      params_b2b = params_b2b_raw
    else:
      params_b2b_seq = np.asarray(params_b2b_seq, dtype=np.float64)
      params_b2b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2b_seq))
  params_b2t_raw = params.b2t
  if isinstance(params_b2t_raw, (str, bytes, dict)):
    params_b2t = params_b2t_raw
  else:
    try:
      params_b2t_seq = list(params_b2t_raw)
    except TypeError:
      params_b2t = params_b2t_raw
    else:
      params_b2t_seq = np.asarray(params_b2t_seq, dtype=np.float64)
      params_b2t = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2t_seq))
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
  params_bt_raw = params.bt
  if isinstance(params_bt_raw, (str, bytes, dict)):
    params_bt = params_bt_raw
  else:
    try:
      params_bt_seq = list(params_bt_raw)
    except TypeError:
      params_bt = params_bt_raw
    else:
      params_bt_seq = np.asarray(params_bt_seq, dtype=np.float64)
      params_bt = np.concatenate((np.array([np.nan], dtype=np.float64), params_bt_seq))
  params_cb_raw = params.cb
  if isinstance(params_cb_raw, (str, bytes, dict)):
    params_cb = params_cb_raw
  else:
    try:
      params_cb_seq = list(params_cb_raw)
    except TypeError:
      params_cb = params_cb_raw
    else:
      params_cb_seq = np.asarray(params_cb_seq, dtype=np.float64)
      params_cb = np.concatenate((np.array([np.nan], dtype=np.float64), params_cb_seq))
  params_ct_raw = params.ct
  if isinstance(params_ct_raw, (str, bytes, dict)):
    params_ct = params_ct_raw
  else:
    try:
      params_ct_seq = list(params_ct_raw)
    except TypeError:
      params_ct = params_ct_raw
    else:
      params_ct_seq = np.asarray(params_ct_seq, dtype=np.float64)
      params_ct = np.concatenate((np.array([np.nan], dtype=np.float64), params_ct_seq))
  params_xb_raw = params.xb
  if isinstance(params_xb_raw, (str, bytes, dict)):
    params_xb = params_xb_raw
  else:
    try:
      params_xb_seq = list(params_xb_raw)
    except TypeError:
      params_xb = params_xb_raw
    else:
      params_xb_seq = np.asarray(params_xb_seq, dtype=np.float64)
      params_xb = np.concatenate((np.array([np.nan], dtype=np.float64), params_xb_seq))
  params_xt_raw = params.xt
  if isinstance(params_xt_raw, (str, bytes, dict)):
    params_xt = params_xt_raw
  else:
    try:
      params_xt_seq = list(params_xt_raw)
    except TypeError:
      params_xt = params_xt_raw
    else:
      params_xt_seq = np.asarray(params_xt_seq, dtype=np.float64)
      params_xt = np.concatenate((np.array([np.nan], dtype=np.float64), params_xt_seq))

  ktbm_p = lambda x: X2S ** 2 * x ** 2

  ktbm_t = lambda t: t / K_FACTOR_C

  ktbm_top = lambda p, t: params_ct + params_at * p + params_bt * t + params_a2t * p * p + params_b2t * t * t + params_xt * p * t

  ktbm_bot = lambda p, t: params_cb + params_ab * p + params_bb * t + params_a2b * p * p + params_b2b * t * t + params_xb * p * t

  ktbm_f = lambda x, u, t: ktbm_top(ktbm_p(x), ktbm_t(t)) / ktbm_bot(ktbm_p(x), ktbm_t(t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ktbm_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = 6 ** (0.1e1 / 0.3e1)
  t21 = params.at * t20
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t26 = t21 * t25
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t19 ** 2
  t33 = 0.1e1 / t31 / t30
  t34 = t29 * t33
  t38 = params.bt * tau0 * t28
  t42 = 0.1e1 / t31 / r0 * t20 * t25
  t45 = t20 ** 2
  t48 = 0.1e1 / t23 / t22
  t49 = params.a2t * t45 * t48
  t50 = s0 ** 2
  t51 = t50 * t27
  t52 = t30 ** 2
  t55 = 0.1e1 / t19 / t52 / r0
  t56 = t51 * t55
  t59 = tau0 ** 2
  t61 = params.b2t * t59 * t27
  t62 = t30 * r0
  t66 = 0.1e1 / t19 / t62 * t45 * t48
  t70 = params.xt * t45 * t48
  t71 = s0 * t27
  t73 = 0.1e1 / t19 / t52
  t75 = t71 * t73 * tau0
  t78 = params.ct + t26 * t34 / 0.24e2 + 0.5e1 / 0.9e1 * t38 * t42 + t49 * t56 / 0.288e3 + 0.50e2 / 0.81e2 * t61 * t66 + 0.5e1 / 0.108e3 * t70 * t75
  t79 = t19 * t78
  t80 = params.ab * t20
  t81 = t80 * t25
  t85 = params.bb * tau0 * t28
  t89 = params.a2b * t45 * t48
  t93 = params.b2b * t59 * t27
  t97 = params.xb * t45 * t48
  t100 = params.cb + t81 * t34 / 0.24e2 + 0.5e1 / 0.9e1 * t85 * t42 + t89 * t56 / 0.288e3 + 0.50e2 / 0.81e2 * t93 * t66 + 0.5e1 / 0.108e3 * t97 * t75
  t101 = 0.1e1 / t100
  t105 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t79 * t101)
  t113 = t29 / t31 / t62
  t117 = t33 * t20 * t25
  t123 = t51 / t19 / t52 / t30
  t127 = t73 * t45 * t48
  t131 = t71 * t55 * tau0
  t139 = t100 ** 2
  t140 = 0.1e1 / t139
  t157 = f.my_piecewise3(t2, 0, -t18 / t31 * t78 * t101 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (-t26 * t113 / 0.9e1 - 0.25e2 / 0.27e2 * t38 * t117 - t49 * t123 / 0.54e2 - 0.500e3 / 0.243e3 * t61 * t127 - 0.65e2 / 0.324e3 * t70 * t131) * t101 + 0.3e1 / 0.8e1 * t18 * t79 * t140 * (-t81 * t113 / 0.9e1 - 0.25e2 / 0.27e2 * t85 * t117 - t89 * t123 / 0.54e2 - 0.500e3 / 0.243e3 * t93 * t127 - 0.65e2 / 0.324e3 * t97 * t131))
  vrho_0_ = 0.2e1 * r0 * t157 + 0.2e1 * t105
  t161 = t25 * t28 * t33
  t164 = t71 * t55
  t168 = t27 * t73 * tau0
  t187 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (t21 * t161 / 0.24e2 + t49 * t164 / 0.144e3 + 0.5e1 / 0.108e3 * t70 * t168) * t101 + 0.3e1 / 0.8e1 * t18 * t79 * t140 * (t80 * t161 / 0.24e2 + t89 * t164 / 0.144e3 + 0.5e1 / 0.108e3 * t97 * t168))
  vsigma_0_ = 0.2e1 * r0 * t187
  vlapl_0_ = 0.0e0
  t196 = t71 * t73
  t218 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (0.5e1 / 0.9e1 * params.bt * t28 * t42 + 0.100e3 / 0.81e2 * params.b2t * tau0 * t27 * t66 + 0.5e1 / 0.108e3 * t70 * t196) * t101 + 0.3e1 / 0.8e1 * t18 * t79 * t140 * (0.5e1 / 0.9e1 * params.bb * t28 * t42 + 0.100e3 / 0.81e2 * params.b2b * tau0 * t27 * t66 + 0.5e1 / 0.108e3 * t97 * t196))
  vtau_0_ = 0.2e1 * r0 * t218
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
  
  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 / t4 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t22 = 6 ** (0.1e1 / 0.3e1)
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = params.at * t22 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t20 / t32
  t35 = t31 * t34
  t39 = params.bt * tau0 * t30
  t41 = 0.1e1 / t20 / r0
  t43 = t41 * t22 * t27
  t46 = t22 ** 2
  t49 = 0.1e1 / t25 / t24
  t50 = params.a2t * t46 * t49
  t51 = s0 ** 2
  t52 = t51 * t29
  t53 = t32 ** 2
  t56 = 0.1e1 / t19 / t53 / r0
  t57 = t52 * t56
  t60 = tau0 ** 2
  t62 = params.b2t * t60 * t29
  t63 = t32 * r0
  t67 = 0.1e1 / t19 / t63 * t46 * t49
  t71 = params.xt * t46 * t49
  t72 = s0 * t29
  t74 = 0.1e1 / t19 / t53
  t76 = t72 * t74 * tau0
  t79 = params.ct + t28 * t35 / 0.24e2 + 0.5e1 / 0.9e1 * t39 * t43 + t50 * t57 / 0.288e3 + 0.50e2 / 0.81e2 * t62 * t67 + 0.5e1 / 0.108e3 * t71 * t76
  t80 = t21 * t79
  t82 = params.ab * t22 * t27
  t86 = params.bb * tau0 * t30
  t90 = params.a2b * t46 * t49
  t94 = params.b2b * t60 * t29
  t98 = params.xb * t46 * t49
  t101 = params.cb + t82 * t35 / 0.24e2 + 0.5e1 / 0.9e1 * t86 * t43 + t90 * t57 / 0.288e3 + 0.50e2 / 0.81e2 * t94 * t67 + 0.5e1 / 0.108e3 * t98 * t76
  t102 = 0.1e1 / t101
  t107 = 0.1e1 / t20 / t63
  t108 = t31 * t107
  t112 = t34 * t22 * t27
  t117 = 0.1e1 / t19 / t53 / t32
  t118 = t52 * t117
  t122 = t74 * t46 * t49
  t126 = t72 * t56 * tau0
  t129 = -t28 * t108 / 0.9e1 - 0.25e2 / 0.27e2 * t39 * t112 - t50 * t118 / 0.54e2 - 0.500e3 / 0.243e3 * t62 * t122 - 0.65e2 / 0.324e3 * t71 * t126
  t130 = t19 * t129
  t134 = t19 * t79
  t135 = t101 ** 2
  t136 = 0.1e1 / t135
  t147 = -t82 * t108 / 0.9e1 - 0.25e2 / 0.27e2 * t86 * t112 - t90 * t118 / 0.54e2 - 0.500e3 / 0.243e3 * t94 * t122 - 0.65e2 / 0.324e3 * t98 * t126
  t148 = t136 * t147
  t153 = f.my_piecewise3(t2, 0, -t18 * t80 * t102 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t130 * t102 + 0.3e1 / 0.8e1 * t18 * t134 * t148)
  t168 = t31 / t20 / t53
  t172 = t107 * t22 * t27
  t178 = t52 / t19 / t53 / t63
  t182 = t56 * t46 * t49
  t186 = t72 * t117 * tau0
  t199 = t147 ** 2
  t220 = f.my_piecewise3(t2, 0, t18 * t41 * t79 * t102 / 0.12e2 - t18 * t21 * t129 * t102 / 0.4e1 + t18 * t80 * t148 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t19 * (0.11e2 / 0.27e2 * t28 * t168 + 0.200e3 / 0.81e2 * t39 * t172 + 0.19e2 / 0.162e3 * t50 * t178 + 0.6500e4 / 0.729e3 * t62 * t182 + 0.260e3 / 0.243e3 * t71 * t186) * t102 + 0.3e1 / 0.4e1 * t18 * t130 * t148 - 0.3e1 / 0.4e1 * t18 * t134 / t135 / t101 * t199 + 0.3e1 / 0.8e1 * t18 * t134 * t136 * (0.11e2 / 0.27e2 * t82 * t168 + 0.200e3 / 0.81e2 * t86 * t172 + 0.19e2 / 0.162e3 * t90 * t178 + 0.6500e4 / 0.729e3 * t94 * t182 + 0.260e3 / 0.243e3 * t98 * t186))
  v2rho2_0_ = 0.2e1 * r0 * t220 + 0.4e1 * t153
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t6 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / r0
  t23 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = params.at * t23 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t20 / t33
  t36 = t32 * t35
  t40 = params.bt * tau0 * t31
  t42 = t22 * t23 * t28
  t45 = t23 ** 2
  t48 = 0.1e1 / t26 / t25
  t49 = params.a2t * t45 * t48
  t50 = s0 ** 2
  t51 = t50 * t30
  t52 = t33 ** 2
  t53 = t52 * r0
  t55 = 0.1e1 / t19 / t53
  t56 = t51 * t55
  t59 = tau0 ** 2
  t61 = params.b2t * t59 * t30
  t62 = t33 * r0
  t66 = 0.1e1 / t19 / t62 * t45 * t48
  t70 = params.xt * t45 * t48
  t71 = s0 * t30
  t73 = 0.1e1 / t19 / t52
  t75 = t71 * t73 * tau0
  t78 = params.ct + t29 * t36 / 0.24e2 + 0.5e1 / 0.9e1 * t40 * t42 + t49 * t56 / 0.288e3 + 0.50e2 / 0.81e2 * t61 * t66 + 0.5e1 / 0.108e3 * t70 * t75
  t79 = t22 * t78
  t81 = params.ab * t23 * t28
  t85 = params.bb * tau0 * t31
  t89 = params.a2b * t45 * t48
  t93 = params.b2b * t59 * t30
  t97 = params.xb * t45 * t48
  t100 = params.cb + t81 * t36 / 0.24e2 + 0.5e1 / 0.9e1 * t85 * t42 + t89 * t56 / 0.288e3 + 0.50e2 / 0.81e2 * t93 * t66 + 0.5e1 / 0.108e3 * t97 * t75
  t101 = 0.1e1 / t100
  t105 = 0.1e1 / t20
  t107 = 0.1e1 / t20 / t62
  t108 = t32 * t107
  t112 = t35 * t23 * t28
  t117 = 0.1e1 / t19 / t52 / t33
  t118 = t51 * t117
  t122 = t73 * t45 * t48
  t126 = t71 * t55 * tau0
  t129 = -t29 * t108 / 0.9e1 - 0.25e2 / 0.27e2 * t40 * t112 - t49 * t118 / 0.54e2 - 0.500e3 / 0.243e3 * t61 * t122 - 0.65e2 / 0.324e3 * t70 * t126
  t130 = t105 * t129
  t134 = t105 * t78
  t135 = t100 ** 2
  t136 = 0.1e1 / t135
  t147 = -t81 * t108 / 0.9e1 - 0.25e2 / 0.27e2 * t85 * t112 - t89 * t118 / 0.54e2 - 0.500e3 / 0.243e3 * t93 * t122 - 0.65e2 / 0.324e3 * t97 * t126
  t148 = t136 * t147
  t153 = 0.1e1 / t20 / t52
  t154 = t32 * t153
  t158 = t107 * t23 * t28
  t163 = 0.1e1 / t19 / t52 / t62
  t164 = t51 * t163
  t168 = t55 * t45 * t48
  t172 = t71 * t117 * tau0
  t175 = 0.11e2 / 0.27e2 * t29 * t154 + 0.200e3 / 0.81e2 * t40 * t158 + 0.19e2 / 0.162e3 * t49 * t164 + 0.6500e4 / 0.729e3 * t61 * t168 + 0.260e3 / 0.243e3 * t70 * t172
  t176 = t19 * t175
  t180 = t19 * t129
  t184 = t19 * t78
  t186 = 0.1e1 / t135 / t100
  t187 = t147 ** 2
  t188 = t186 * t187
  t202 = 0.11e2 / 0.27e2 * t81 * t154 + 0.200e3 / 0.81e2 * t85 * t158 + 0.19e2 / 0.162e3 * t89 * t164 + 0.6500e4 / 0.729e3 * t93 * t168 + 0.260e3 / 0.243e3 * t97 * t172
  t203 = t136 * t202
  t208 = f.my_piecewise3(t2, 0, t18 * t79 * t101 / 0.12e2 - t18 * t130 * t101 / 0.4e1 + t18 * t134 * t148 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t176 * t101 + 0.3e1 / 0.4e1 * t18 * t180 * t148 - 0.3e1 / 0.4e1 * t18 * t184 * t188 + 0.3e1 / 0.8e1 * t18 * t184 * t203)
  t210 = t135 ** 2
  t240 = t32 / t20 / t53
  t244 = t153 * t23 * t28
  t247 = t52 ** 2
  t250 = t51 / t19 / t247
  t254 = t117 * t45 * t48
  t258 = t71 * t163 * tau0
  t300 = 0.9e1 / 0.4e1 * t18 * t184 / t210 * t187 * t147 - 0.9e1 / 0.4e1 * t6 * t17 * t19 * t78 * t186 * t147 * t202 - 0.3e1 / 0.4e1 * t18 * t134 * t188 - 0.9e1 / 0.4e1 * t18 * t180 * t188 + t18 * t22 * t129 * t101 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t105 * t175 * t101 - 0.3e1 / 0.8e1 * t18 * t19 * (-0.154e3 / 0.81e2 * t29 * t240 - 0.2200e4 / 0.243e3 * t40 * t244 - 0.209e3 / 0.243e3 * t49 * t250 - 0.104000e6 / 0.2187e4 * t61 * t254 - 0.4940e4 / 0.729e3 * t70 * t258) * t101 - 0.5e1 / 0.36e2 * t18 * t35 * t78 * t101 - t18 * t79 * t148 / 0.4e1 + 0.3e1 / 0.4e1 * t18 * t130 * t148 + 0.3e1 / 0.8e1 * t18 * t134 * t203 + 0.9e1 / 0.8e1 * t18 * t176 * t148 + 0.9e1 / 0.8e1 * t18 * t180 * t203 + 0.3e1 / 0.8e1 * t18 * t184 * t136 * (-0.154e3 / 0.81e2 * t81 * t240 - 0.2200e4 / 0.243e3 * t85 * t244 - 0.209e3 / 0.243e3 * t89 * t250 - 0.104000e6 / 0.2187e4 * t93 * t254 - 0.4940e4 / 0.729e3 * t97 * t258)
  t301 = f.my_piecewise3(t2, 0, t300)
  v3rho3_0_ = 0.2e1 * r0 * t301 + 0.6e1 * t208

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t6 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = 6 ** (0.1e1 / 0.3e1)
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t26 = params.at * t20 * t25
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t19 ** 2
  t33 = 0.1e1 / t31 / t30
  t34 = t29 * t33
  t38 = params.bt * tau0 * t28
  t40 = 0.1e1 / t31 / r0
  t42 = t40 * t20 * t25
  t45 = t20 ** 2
  t48 = 0.1e1 / t23 / t22
  t49 = params.a2t * t45 * t48
  t50 = s0 ** 2
  t51 = t50 * t27
  t52 = t30 ** 2
  t53 = t52 * r0
  t55 = 0.1e1 / t19 / t53
  t56 = t51 * t55
  t59 = tau0 ** 2
  t61 = params.b2t * t59 * t27
  t62 = t30 * r0
  t66 = 0.1e1 / t19 / t62 * t45 * t48
  t70 = params.xt * t45 * t48
  t71 = s0 * t27
  t73 = 0.1e1 / t19 / t52
  t75 = t71 * t73 * tau0
  t78 = params.ct + t26 * t34 / 0.24e2 + 0.5e1 / 0.9e1 * t38 * t42 + t49 * t56 / 0.288e3 + 0.50e2 / 0.81e2 * t61 * t66 + 0.5e1 / 0.108e3 * t70 * t75
  t79 = t19 * t78
  t81 = params.ab * t20 * t25
  t85 = params.bb * tau0 * t28
  t89 = params.a2b * t45 * t48
  t93 = params.b2b * t59 * t27
  t97 = params.xb * t45 * t48
  t100 = params.cb + t81 * t34 / 0.24e2 + 0.5e1 / 0.9e1 * t85 * t42 + t89 * t56 / 0.288e3 + 0.50e2 / 0.81e2 * t93 * t66 + 0.5e1 / 0.108e3 * t97 * t75
  t101 = t100 ** 2
  t102 = t101 ** 2
  t103 = 0.1e1 / t102
  t105 = 0.1e1 / t31 / t62
  t106 = t29 * t105
  t110 = t33 * t20 * t25
  t113 = t52 * t30
  t115 = 0.1e1 / t19 / t113
  t116 = t51 * t115
  t120 = t73 * t45 * t48
  t124 = t71 * t55 * tau0
  t127 = -t81 * t106 / 0.9e1 - 0.25e2 / 0.27e2 * t85 * t110 - t89 * t116 / 0.54e2 - 0.500e3 / 0.243e3 * t93 * t120 - 0.65e2 / 0.324e3 * t97 * t124
  t128 = t127 ** 2
  t130 = t103 * t128 * t127
  t135 = t6 * t17 * t19
  t137 = 0.1e1 / t101 / t100
  t138 = t78 * t137
  t140 = 0.1e1 / t31 / t52
  t141 = t29 * t140
  t145 = t105 * t20 * t25
  t150 = 0.1e1 / t19 / t52 / t62
  t151 = t51 * t150
  t155 = t55 * t45 * t48
  t159 = t71 * t115 * tau0
  t162 = 0.11e2 / 0.27e2 * t81 * t141 + 0.200e3 / 0.81e2 * t85 * t145 + 0.19e2 / 0.162e3 * t89 * t151 + 0.6500e4 / 0.729e3 * t93 * t155 + 0.260e3 / 0.243e3 * t97 * t159
  t163 = t127 * t162
  t164 = t138 * t163
  t167 = 0.1e1 / t31
  t168 = t167 * t78
  t169 = t137 * t128
  t183 = -t26 * t106 / 0.9e1 - 0.25e2 / 0.27e2 * t38 * t110 - t49 * t116 / 0.54e2 - 0.500e3 / 0.243e3 * t61 * t120 - 0.65e2 / 0.324e3 * t70 * t124
  t184 = t19 * t183
  t188 = t40 * t183
  t189 = 0.1e1 / t100
  t203 = 0.11e2 / 0.27e2 * t26 * t141 + 0.200e3 / 0.81e2 * t38 * t145 + 0.19e2 / 0.162e3 * t49 * t151 + 0.6500e4 / 0.729e3 * t61 * t155 + 0.260e3 / 0.243e3 * t70 * t159
  t204 = t167 * t203
  t209 = 0.1e1 / t31 / t53
  t210 = t29 * t209
  t214 = t140 * t20 * t25
  t217 = t52 ** 2
  t219 = 0.1e1 / t19 / t217
  t220 = t51 * t219
  t224 = t115 * t45 * t48
  t228 = t71 * t150 * tau0
  t231 = -0.154e3 / 0.81e2 * t26 * t210 - 0.2200e4 / 0.243e3 * t38 * t214 - 0.209e3 / 0.243e3 * t49 * t220 - 0.104000e6 / 0.2187e4 * t61 * t224 - 0.4940e4 / 0.729e3 * t70 * t228
  t232 = t19 * t231
  t236 = t33 * t78
  t240 = t40 * t78
  t241 = 0.1e1 / t101
  t242 = t241 * t127
  t246 = t167 * t183
  t250 = t241 * t162
  t254 = t19 * t203
  t271 = -0.154e3 / 0.81e2 * t81 * t210 - 0.2200e4 / 0.243e3 * t85 * t214 - 0.209e3 / 0.243e3 * t89 * t220 - 0.104000e6 / 0.2187e4 * t93 * t224 - 0.4940e4 / 0.729e3 * t97 * t228
  t272 = t241 * t271
  t276 = 0.9e1 / 0.4e1 * t18 * t79 * t130 - 0.9e1 / 0.4e1 * t135 * t164 - 0.3e1 / 0.4e1 * t18 * t168 * t169 - 0.9e1 / 0.4e1 * t18 * t184 * t169 + t18 * t188 * t189 / 0.4e1 - 0.3e1 / 0.8e1 * t18 * t204 * t189 - 0.3e1 / 0.8e1 * t18 * t232 * t189 - 0.5e1 / 0.36e2 * t18 * t236 * t189 - t18 * t240 * t242 / 0.4e1 + 0.3e1 / 0.4e1 * t18 * t246 * t242 + 0.3e1 / 0.8e1 * t18 * t168 * t250 + 0.9e1 / 0.8e1 * t18 * t254 * t242 + 0.9e1 / 0.8e1 * t18 * t184 * t250 + 0.3e1 / 0.8e1 * t18 * t79 * t272
  t277 = f.my_piecewise3(t2, 0, t276)
  t279 = t162 ** 2
  t292 = t29 / t31 / t113
  t296 = t209 * t20 * t25
  t302 = t51 / t19 / t217 / r0
  t306 = t150 * t45 * t48
  t310 = t71 * t219 * tau0
  t364 = -0.9e1 / 0.4e1 * t18 * t79 * t137 * t279 - 0.3e1 * t18 * t246 * t169 - 0.9e1 / 0.2e1 * t18 * t254 * t169 + 0.3e1 / 0.8e1 * t18 * t79 * t241 * (0.2618e4 / 0.243e3 * t81 * t292 + 0.30800e5 / 0.729e3 * t85 * t296 + 0.5225e4 / 0.729e3 * t89 * t302 + 0.1976000e7 / 0.6561e4 * t93 * t306 + 0.108680e6 / 0.2187e4 * t97 * t310) + 0.9e1 * t18 * t184 * t130 - t18 * t167 * t231 * t189 / 0.2e1 - 0.5e1 / 0.9e1 * t18 * t33 * t183 * t189 + 0.10e2 / 0.27e2 * t18 * t105 * t78 * t189 - 0.3e1 / 0.8e1 * t18 * t19 * (0.2618e4 / 0.243e3 * t26 * t292 + 0.30800e5 / 0.729e3 * t38 * t296 + 0.5225e4 / 0.729e3 * t49 * t302 + 0.1976000e7 / 0.6561e4 * t61 * t306 + 0.108680e6 / 0.2187e4 * t70 * t310) * t189 + t18 * t40 * t203 * t189 / 0.2e1 - 0.9e1 * t135 * t183 * t137 * t163 - 0.3e1 * t6 * t17 * t167 * t164 - 0.3e1 * t135 * t138 * t127 * t271
  t381 = t128 ** 2
  t408 = 0.27e2 / 0.2e1 * t135 * t78 * t103 * t128 * t162 + 0.9e1 / 0.4e1 * t18 * t254 * t250 + 0.3e1 / 0.2e1 * t18 * t184 * t272 + 0.3e1 * t18 * t168 * t130 - 0.9e1 * t18 * t79 / t102 / t100 * t381 + t18 * t240 * t169 + 0.3e1 / 0.2e1 * t18 * t246 * t250 + t18 * t168 * t272 / 0.2e1 + 0.5e1 / 0.9e1 * t18 * t236 * t242 - t18 * t240 * t250 / 0.2e1 + 0.3e1 / 0.2e1 * t18 * t204 * t242 + 0.3e1 / 0.2e1 * t18 * t232 * t242 - t18 * t188 * t242
  t410 = f.my_piecewise3(t2, 0, t364 + t408)
  v4rho4_0_ = 0.2e1 * r0 * t410 + 0.8e1 * t277

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t6 ** 2
  t23 = 0.1e1 / t22
  t24 = t16 * t23
  t25 = t7 - t24
  t26 = f.my_piecewise5(t10, 0, t14, 0, t25)
  t29 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t26)
  t30 = t5 * t29
  t31 = t6 ** (0.1e1 / 0.3e1)
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = params.at * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t44 = t38 * t43
  t47 = params.bt * tau0
  t51 = 0.1e1 / t41 / r0 * t32 * t37
  t54 = t32 ** 2
  t55 = params.a2t * t54
  t57 = 0.1e1 / t35 / t34
  t58 = s0 ** 2
  t59 = t57 * t58
  t60 = t39 ** 2
  t63 = 0.1e1 / t40 / t60 / r0
  t64 = t59 * t63
  t67 = tau0 ** 2
  t68 = params.b2t * t67
  t69 = t39 * r0
  t73 = 0.1e1 / t40 / t69 * t54 * t57
  t77 = params.xt * t54 * t57
  t79 = 0.1e1 / t40 / t60
  t81 = s0 * t79 * tau0
  t84 = params.ct + t33 * t44 / 0.24e2 + 0.5e1 / 0.9e1 * t47 * t51 + t55 * t64 / 0.576e3 + 0.25e2 / 0.81e2 * t68 * t73 + 0.5e1 / 0.216e3 * t77 * t81
  t85 = t31 * t84
  t86 = params.ab * t32
  t89 = params.bb * tau0
  t92 = params.a2b * t54
  t95 = params.b2b * t67
  t99 = params.xb * t54 * t57
  t102 = params.cb + t86 * t44 / 0.24e2 + 0.5e1 / 0.9e1 * t89 * t51 + t92 * t64 / 0.576e3 + 0.25e2 / 0.81e2 * t95 * t73 + 0.5e1 / 0.216e3 * t99 * t81
  t103 = 0.1e1 / t102
  t104 = t85 * t103
  t107 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t108 = t107 * f.p.zeta_threshold
  t110 = f.my_piecewise3(t20, t108, t21 * t19)
  t111 = t5 * t110
  t112 = t31 ** 2
  t113 = 0.1e1 / t112
  t114 = t113 * t84
  t115 = t114 * t103
  t117 = t111 * t115 / 0.8e1
  t119 = 0.1e1 / t41 / t69
  t120 = t38 * t119
  t124 = t43 * t32 * t37
  t129 = 0.1e1 / t40 / t60 / t39
  t130 = t59 * t129
  t134 = t79 * t54 * t57
  t138 = s0 * t63 * tau0
  t141 = -t33 * t120 / 0.9e1 - 0.25e2 / 0.27e2 * t47 * t124 - t55 * t130 / 0.108e3 - 0.250e3 / 0.243e3 * t68 * t134 - 0.65e2 / 0.648e3 * t77 * t138
  t142 = t31 * t141
  t143 = t142 * t103
  t146 = t102 ** 2
  t147 = 0.1e1 / t146
  t158 = -t86 * t120 / 0.9e1 - 0.25e2 / 0.27e2 * t89 * t124 - t92 * t130 / 0.108e3 - 0.250e3 / 0.243e3 * t95 * t134 - 0.65e2 / 0.648e3 * t99 * t138
  t159 = t147 * t158
  t160 = t85 * t159
  t164 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t104 - t117 - 0.3e1 / 0.8e1 * t111 * t143 + 0.3e1 / 0.8e1 * t111 * t160)
  t166 = r1 <= f.p.dens_threshold
  t167 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t168 = 0.1e1 + t167
  t169 = t168 <= f.p.zeta_threshold
  t170 = t168 ** (0.1e1 / 0.3e1)
  t172 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t175 = f.my_piecewise3(t169, 0, 0.4e1 / 0.3e1 * t170 * t172)
  t176 = t5 * t175
  t177 = t37 * s2
  t178 = r1 ** 2
  t179 = r1 ** (0.1e1 / 0.3e1)
  t180 = t179 ** 2
  t182 = 0.1e1 / t180 / t178
  t183 = t177 * t182
  t186 = params.bt * tau1
  t190 = 0.1e1 / t180 / r1 * t32 * t37
  t193 = s2 ** 2
  t194 = t57 * t193
  t195 = t178 ** 2
  t198 = 0.1e1 / t179 / t195 / r1
  t199 = t194 * t198
  t202 = tau1 ** 2
  t203 = params.b2t * t202
  t204 = t178 * r1
  t208 = 0.1e1 / t179 / t204 * t54 * t57
  t212 = 0.1e1 / t179 / t195
  t214 = s2 * t212 * tau1
  t217 = params.ct + t33 * t183 / 0.24e2 + 0.5e1 / 0.9e1 * t186 * t190 + t55 * t199 / 0.576e3 + 0.25e2 / 0.81e2 * t203 * t208 + 0.5e1 / 0.216e3 * t77 * t214
  t218 = t31 * t217
  t221 = params.bb * tau1
  t226 = params.b2b * t202
  t231 = params.cb + t86 * t183 / 0.24e2 + 0.5e1 / 0.9e1 * t221 * t190 + t92 * t199 / 0.576e3 + 0.25e2 / 0.81e2 * t226 * t208 + 0.5e1 / 0.216e3 * t99 * t214
  t232 = 0.1e1 / t231
  t233 = t218 * t232
  t237 = f.my_piecewise3(t169, t108, t170 * t168)
  t238 = t5 * t237
  t239 = t113 * t217
  t240 = t239 * t232
  t242 = t238 * t240 / 0.8e1
  t244 = f.my_piecewise3(t166, 0, -0.3e1 / 0.8e1 * t176 * t233 - t242)
  t246 = t21 ** 2
  t247 = 0.1e1 / t246
  t248 = t26 ** 2
  t253 = t16 / t22 / t6
  t255 = -0.2e1 * t23 + 0.2e1 * t253
  t256 = f.my_piecewise5(t10, 0, t14, 0, t255)
  t260 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t247 * t248 + 0.4e1 / 0.3e1 * t21 * t256)
  t264 = t30 * t115
  t271 = 0.1e1 / t112 / t6
  t275 = t111 * t271 * t84 * t103 / 0.12e2
  t278 = t111 * t113 * t141 * t103
  t281 = t111 * t114 * t159
  t285 = t38 / t41 / t60
  t289 = t119 * t32 * t37
  t295 = t59 / t40 / t60 / t69
  t299 = t63 * t54 * t57
  t303 = s0 * t129 * tau0
  t316 = t158 ** 2
  t336 = -0.3e1 / 0.8e1 * t5 * t260 * t104 - t264 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t143 + 0.3e1 / 0.4e1 * t30 * t160 + t275 - t278 / 0.4e1 + t281 / 0.4e1 - 0.3e1 / 0.8e1 * t111 * t31 * (0.11e2 / 0.27e2 * t33 * t285 + 0.200e3 / 0.81e2 * t47 * t289 + 0.19e2 / 0.324e3 * t55 * t295 + 0.3250e4 / 0.729e3 * t68 * t299 + 0.130e3 / 0.243e3 * t77 * t303) * t103 + 0.3e1 / 0.4e1 * t111 * t142 * t159 - 0.3e1 / 0.4e1 * t111 * t85 / t146 / t102 * t316 + 0.3e1 / 0.8e1 * t111 * t85 * t147 * (0.11e2 / 0.27e2 * t86 * t285 + 0.200e3 / 0.81e2 * t89 * t289 + 0.19e2 / 0.324e3 * t92 * t295 + 0.3250e4 / 0.729e3 * t95 * t299 + 0.130e3 / 0.243e3 * t99 * t303)
  t337 = f.my_piecewise3(t1, 0, t336)
  t338 = t170 ** 2
  t339 = 0.1e1 / t338
  t340 = t172 ** 2
  t344 = f.my_piecewise5(t14, 0, t10, 0, -t255)
  t348 = f.my_piecewise3(t169, 0, 0.4e1 / 0.9e1 * t339 * t340 + 0.4e1 / 0.3e1 * t170 * t344)
  t352 = t176 * t240
  t357 = t238 * t271 * t217 * t232 / 0.12e2
  t359 = f.my_piecewise3(t166, 0, -0.3e1 / 0.8e1 * t5 * t348 * t233 - t352 / 0.4e1 + t357)
  d11 = 0.2e1 * t164 + 0.2e1 * t244 + t6 * (t337 + t359)
  t362 = -t7 - t24
  t363 = f.my_piecewise5(t10, 0, t14, 0, t362)
  t366 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t363)
  t367 = t5 * t366
  t371 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t367 * t104 - t117)
  t373 = f.my_piecewise5(t14, 0, t10, 0, -t362)
  t376 = f.my_piecewise3(t169, 0, 0.4e1 / 0.3e1 * t170 * t373)
  t377 = t5 * t376
  t381 = 0.1e1 / t180 / t204
  t382 = t177 * t381
  t386 = t182 * t32 * t37
  t391 = 0.1e1 / t179 / t195 / t178
  t392 = t194 * t391
  t396 = t212 * t54 * t57
  t400 = s2 * t198 * tau1
  t403 = -t33 * t382 / 0.9e1 - 0.25e2 / 0.27e2 * t186 * t386 - t55 * t392 / 0.108e3 - 0.250e3 / 0.243e3 * t203 * t396 - 0.65e2 / 0.648e3 * t77 * t400
  t404 = t31 * t403
  t405 = t404 * t232
  t408 = t231 ** 2
  t409 = 0.1e1 / t408
  t420 = -t86 * t382 / 0.9e1 - 0.25e2 / 0.27e2 * t221 * t386 - t92 * t392 / 0.108e3 - 0.250e3 / 0.243e3 * t226 * t396 - 0.65e2 / 0.648e3 * t99 * t400
  t421 = t409 * t420
  t422 = t218 * t421
  t426 = f.my_piecewise3(t166, 0, -0.3e1 / 0.8e1 * t377 * t233 - t242 - 0.3e1 / 0.8e1 * t238 * t405 + 0.3e1 / 0.8e1 * t238 * t422)
  t430 = 0.2e1 * t253
  t431 = f.my_piecewise5(t10, 0, t14, 0, t430)
  t435 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t247 * t363 * t26 + 0.4e1 / 0.3e1 * t21 * t431)
  t439 = t367 * t115
  t449 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t435 * t104 - t439 / 0.8e1 - 0.3e1 / 0.8e1 * t367 * t143 + 0.3e1 / 0.8e1 * t367 * t160 - t264 / 0.8e1 + t275 - t278 / 0.8e1 + t281 / 0.8e1)
  t453 = f.my_piecewise5(t14, 0, t10, 0, -t430)
  t457 = f.my_piecewise3(t169, 0, 0.4e1 / 0.9e1 * t339 * t373 * t172 + 0.4e1 / 0.3e1 * t170 * t453)
  t461 = t377 * t240
  t468 = t238 * t113 * t403 * t232
  t473 = t238 * t239 * t421
  t476 = f.my_piecewise3(t166, 0, -0.3e1 / 0.8e1 * t5 * t457 * t233 - t461 / 0.8e1 - t352 / 0.8e1 + t357 - 0.3e1 / 0.8e1 * t176 * t405 - t468 / 0.8e1 + 0.3e1 / 0.8e1 * t176 * t422 + t473 / 0.8e1)
  d12 = t164 + t244 + t371 + t426 + t6 * (t449 + t476)
  t481 = t363 ** 2
  t485 = 0.2e1 * t23 + 0.2e1 * t253
  t486 = f.my_piecewise5(t10, 0, t14, 0, t485)
  t490 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t247 * t481 + 0.4e1 / 0.3e1 * t21 * t486)
  t496 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t490 * t104 - t439 / 0.4e1 + t275)
  t497 = t373 ** 2
  t501 = f.my_piecewise5(t14, 0, t10, 0, -t485)
  t505 = f.my_piecewise3(t169, 0, 0.4e1 / 0.9e1 * t339 * t497 + 0.4e1 / 0.3e1 * t170 * t501)
  t518 = t177 / t180 / t195
  t522 = t381 * t32 * t37
  t528 = t194 / t179 / t195 / t204
  t532 = t198 * t54 * t57
  t536 = s2 * t391 * tau1
  t549 = t420 ** 2
  t569 = -0.3e1 / 0.8e1 * t5 * t505 * t233 - t461 / 0.4e1 - 0.3e1 / 0.4e1 * t377 * t405 + 0.3e1 / 0.4e1 * t377 * t422 + t357 - t468 / 0.4e1 + t473 / 0.4e1 - 0.3e1 / 0.8e1 * t238 * t31 * (0.11e2 / 0.27e2 * t33 * t518 + 0.200e3 / 0.81e2 * t186 * t522 + 0.19e2 / 0.324e3 * t55 * t528 + 0.3250e4 / 0.729e3 * t203 * t532 + 0.130e3 / 0.243e3 * t77 * t536) * t232 + 0.3e1 / 0.4e1 * t238 * t404 * t421 - 0.3e1 / 0.4e1 * t238 * t218 / t408 / t231 * t549 + 0.3e1 / 0.8e1 * t238 * t218 * t409 * (0.11e2 / 0.27e2 * t86 * t518 + 0.200e3 / 0.81e2 * t221 * t522 + 0.19e2 / 0.324e3 * t92 * t528 + 0.3250e4 / 0.729e3 * t226 * t532 + 0.130e3 / 0.243e3 * t99 * t536)
  t570 = f.my_piecewise3(t166, 0, t569)
  d22 = 0.2e1 * t371 + 0.2e1 * t426 + t6 * (t496 + t570)
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

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = 0.1e1 / t22
  t24 = t6 ** 2
  t25 = 0.1e1 / t24
  t27 = -t16 * t25 + t7
  t28 = f.my_piecewise5(t10, 0, t14, 0, t27)
  t29 = t28 ** 2
  t33 = 0.1e1 / t24 / t6
  t36 = 0.2e1 * t16 * t33 - 0.2e1 * t25
  t37 = f.my_piecewise5(t10, 0, t14, 0, t36)
  t41 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t23 * t29 + 0.4e1 / 0.3e1 * t21 * t37)
  t42 = t5 * t41
  t43 = t6 ** (0.1e1 / 0.3e1)
  t44 = 6 ** (0.1e1 / 0.3e1)
  t45 = params.at * t44
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t50 = t49 * s0
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t55 = 0.1e1 / t53 / t51
  t56 = t50 * t55
  t59 = params.bt * tau0
  t63 = 0.1e1 / t53 / r0 * t44 * t49
  t66 = t44 ** 2
  t67 = params.a2t * t66
  t69 = 0.1e1 / t47 / t46
  t70 = s0 ** 2
  t71 = t69 * t70
  t72 = t51 ** 2
  t73 = t72 * r0
  t75 = 0.1e1 / t52 / t73
  t76 = t71 * t75
  t79 = tau0 ** 2
  t80 = params.b2t * t79
  t81 = t51 * r0
  t85 = 0.1e1 / t52 / t81 * t66 * t69
  t89 = params.xt * t66 * t69
  t91 = 0.1e1 / t52 / t72
  t93 = s0 * t91 * tau0
  t96 = params.ct + t45 * t56 / 0.24e2 + 0.5e1 / 0.9e1 * t59 * t63 + t67 * t76 / 0.576e3 + 0.25e2 / 0.81e2 * t80 * t85 + 0.5e1 / 0.216e3 * t89 * t93
  t97 = t43 * t96
  t98 = params.ab * t44
  t101 = params.bb * tau0
  t104 = params.a2b * t66
  t107 = params.b2b * t79
  t111 = params.xb * t66 * t69
  t114 = params.cb + t98 * t56 / 0.24e2 + 0.5e1 / 0.9e1 * t101 * t63 + t104 * t76 / 0.576e3 + 0.25e2 / 0.81e2 * t107 * t85 + 0.5e1 / 0.216e3 * t111 * t93
  t115 = 0.1e1 / t114
  t116 = t97 * t115
  t121 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t122 = t5 * t121
  t123 = t43 ** 2
  t124 = 0.1e1 / t123
  t125 = t124 * t96
  t126 = t125 * t115
  t130 = 0.1e1 / t53 / t81
  t131 = t50 * t130
  t135 = t55 * t44 * t49
  t140 = 0.1e1 / t52 / t72 / t51
  t141 = t71 * t140
  t145 = t91 * t66 * t69
  t149 = s0 * t75 * tau0
  t152 = -t45 * t131 / 0.9e1 - 0.25e2 / 0.27e2 * t59 * t135 - t67 * t141 / 0.108e3 - 0.250e3 / 0.243e3 * t80 * t145 - 0.65e2 / 0.648e3 * t89 * t149
  t153 = t43 * t152
  t154 = t153 * t115
  t157 = t114 ** 2
  t158 = 0.1e1 / t157
  t169 = -t98 * t131 / 0.9e1 - 0.25e2 / 0.27e2 * t101 * t135 - t104 * t141 / 0.108e3 - 0.250e3 / 0.243e3 * t107 * t145 - 0.65e2 / 0.648e3 * t111 * t149
  t170 = t158 * t169
  t171 = t97 * t170
  t174 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t175 = t174 * f.p.zeta_threshold
  t177 = f.my_piecewise3(t20, t175, t21 * t19)
  t178 = t5 * t177
  t180 = 0.1e1 / t123 / t6
  t181 = t180 * t96
  t182 = t181 * t115
  t185 = t124 * t152
  t186 = t185 * t115
  t189 = t125 * t170
  t193 = 0.1e1 / t53 / t72
  t194 = t50 * t193
  t198 = t130 * t44 * t49
  t203 = 0.1e1 / t52 / t72 / t81
  t204 = t71 * t203
  t208 = t75 * t66 * t69
  t212 = s0 * t140 * tau0
  t215 = 0.11e2 / 0.27e2 * t45 * t194 + 0.200e3 / 0.81e2 * t59 * t198 + 0.19e2 / 0.324e3 * t67 * t204 + 0.3250e4 / 0.729e3 * t80 * t208 + 0.130e3 / 0.243e3 * t89 * t212
  t216 = t43 * t215
  t217 = t216 * t115
  t220 = t153 * t170
  t224 = 0.1e1 / t157 / t114
  t225 = t169 ** 2
  t226 = t224 * t225
  t227 = t97 * t226
  t240 = 0.11e2 / 0.27e2 * t98 * t194 + 0.200e3 / 0.81e2 * t101 * t198 + 0.19e2 / 0.324e3 * t104 * t204 + 0.3250e4 / 0.729e3 * t107 * t208 + 0.130e3 / 0.243e3 * t111 * t212
  t241 = t158 * t240
  t242 = t97 * t241
  t245 = -0.3e1 / 0.8e1 * t42 * t116 - t122 * t126 / 0.4e1 - 0.3e1 / 0.4e1 * t122 * t154 + 0.3e1 / 0.4e1 * t122 * t171 + t178 * t182 / 0.12e2 - t178 * t186 / 0.4e1 + t178 * t189 / 0.4e1 - 0.3e1 / 0.8e1 * t178 * t217 + 0.3e1 / 0.4e1 * t178 * t220 - 0.3e1 / 0.4e1 * t178 * t227 + 0.3e1 / 0.8e1 * t178 * t242
  t246 = f.my_piecewise3(t1, 0, t245)
  t248 = r1 <= f.p.dens_threshold
  t249 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t250 = 0.1e1 + t249
  t251 = t250 <= f.p.zeta_threshold
  t252 = t250 ** (0.1e1 / 0.3e1)
  t253 = t252 ** 2
  t254 = 0.1e1 / t253
  t256 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t257 = t256 ** 2
  t261 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t265 = f.my_piecewise3(t251, 0, 0.4e1 / 0.9e1 * t254 * t257 + 0.4e1 / 0.3e1 * t252 * t261)
  t266 = t5 * t265
  t268 = r1 ** 2
  t269 = r1 ** (0.1e1 / 0.3e1)
  t270 = t269 ** 2
  t273 = t49 * s2 / t270 / t268
  t280 = 0.1e1 / t270 / r1 * t44 * t49
  t283 = s2 ** 2
  t285 = t268 ** 2
  t289 = t69 * t283 / t269 / t285 / r1
  t292 = tau1 ** 2
  t298 = 0.1e1 / t269 / t268 / r1 * t66 * t69
  t304 = s2 / t269 / t285 * tau1
  t307 = params.ct + t45 * t273 / 0.24e2 + 0.5e1 / 0.9e1 * params.bt * tau1 * t280 + t67 * t289 / 0.576e3 + 0.25e2 / 0.81e2 * params.b2t * t292 * t298 + 0.5e1 / 0.216e3 * t89 * t304
  t322 = 0.1e1 / (params.cb + t98 * t273 / 0.24e2 + 0.5e1 / 0.9e1 * params.bb * tau1 * t280 + t104 * t289 / 0.576e3 + 0.25e2 / 0.81e2 * params.b2b * t292 * t298 + 0.5e1 / 0.216e3 * t111 * t304)
  t323 = t43 * t307 * t322
  t328 = f.my_piecewise3(t251, 0, 0.4e1 / 0.3e1 * t252 * t256)
  t329 = t5 * t328
  t331 = t124 * t307 * t322
  t335 = f.my_piecewise3(t251, t175, t252 * t250)
  t336 = t5 * t335
  t338 = t180 * t307 * t322
  t342 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t266 * t323 - t329 * t331 / 0.4e1 + t336 * t338 / 0.12e2)
  t345 = 0.1e1 / t123 / t24
  t352 = t50 / t53 / t73
  t356 = t193 * t44 * t49
  t359 = t72 ** 2
  t362 = t71 / t52 / t359
  t366 = t140 * t66 * t69
  t370 = s0 * t203 * tau0
  t386 = t24 ** 2
  t390 = 0.6e1 * t33 - 0.6e1 * t16 / t386
  t391 = f.my_piecewise5(t10, 0, t14, 0, t390)
  t395 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t391)
  t427 = -0.5e1 / 0.36e2 * t178 * t345 * t96 * t115 - 0.3e1 / 0.8e1 * t178 * t43 * (-0.154e3 / 0.81e2 * t45 * t352 - 0.2200e4 / 0.243e3 * t59 * t356 - 0.209e3 / 0.486e3 * t67 * t362 - 0.52000e5 / 0.2187e4 * t80 * t366 - 0.2470e4 / 0.729e3 * t89 * t370) * t115 - 0.3e1 / 0.8e1 * t5 * t395 * t116 - 0.9e1 / 0.8e1 * t42 * t154 - 0.9e1 / 0.8e1 * t122 * t217 + t178 * t180 * t152 * t115 / 0.4e1 - 0.3e1 / 0.8e1 * t178 * t124 * t215 * t115 - 0.3e1 / 0.8e1 * t42 * t126 + t122 * t182 / 0.4e1 - 0.3e1 / 0.4e1 * t122 * t186 - 0.9e1 / 0.4e1 * t5 * t177 * t43 * t96 * t224 * t169 * t240 - 0.3e1 / 0.4e1 * t178 * t125 * t226
  t431 = t157 ** 2
  t478 = -0.9e1 / 0.4e1 * t178 * t153 * t226 + 0.9e1 / 0.4e1 * t178 * t97 / t431 * t225 * t169 - 0.9e1 / 0.4e1 * t122 * t227 + 0.9e1 / 0.8e1 * t178 * t153 * t241 + 0.3e1 / 0.8e1 * t178 * t97 * t158 * (-0.154e3 / 0.81e2 * t98 * t352 - 0.2200e4 / 0.243e3 * t101 * t356 - 0.209e3 / 0.486e3 * t104 * t362 - 0.52000e5 / 0.2187e4 * t107 * t366 - 0.2470e4 / 0.729e3 * t111 * t370) + 0.9e1 / 0.8e1 * t42 * t171 + 0.3e1 / 0.4e1 * t122 * t189 + 0.9e1 / 0.4e1 * t122 * t220 + 0.9e1 / 0.8e1 * t122 * t242 - t178 * t181 * t170 / 0.4e1 + 0.3e1 / 0.4e1 * t178 * t185 * t170 + 0.3e1 / 0.8e1 * t178 * t125 * t241 + 0.9e1 / 0.8e1 * t178 * t216 * t170
  t480 = f.my_piecewise3(t1, 0, t427 + t478)
  t490 = f.my_piecewise5(t14, 0, t10, 0, -t390)
  t494 = f.my_piecewise3(t251, 0, -0.8e1 / 0.27e2 / t253 / t250 * t257 * t256 + 0.4e1 / 0.3e1 * t254 * t256 * t261 + 0.4e1 / 0.3e1 * t252 * t490)
  t507 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t5 * t494 * t323 - 0.3e1 / 0.8e1 * t266 * t331 + t329 * t338 / 0.4e1 - 0.5e1 / 0.36e2 * t336 * t345 * t307 * t322)
  d111 = 0.3e1 * t246 + 0.3e1 * t342 + t6 * (t480 + t507)

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

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t6 ** 2
  t23 = 0.1e1 / t22
  t25 = -t16 * t23 + t7
  t26 = f.my_piecewise5(t10, 0, t14, 0, t25)
  t29 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t26)
  t30 = t5 * t29
  t31 = t6 ** (0.1e1 / 0.3e1)
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = params.at * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t44 = t38 * t43
  t47 = params.bt * tau0
  t51 = 0.1e1 / t41 / r0 * t32 * t37
  t54 = t32 ** 2
  t55 = params.a2t * t54
  t57 = 0.1e1 / t35 / t34
  t58 = s0 ** 2
  t59 = t57 * t58
  t60 = t39 ** 2
  t61 = t60 * r0
  t63 = 0.1e1 / t40 / t61
  t64 = t59 * t63
  t67 = tau0 ** 2
  t68 = params.b2t * t67
  t69 = t39 * r0
  t73 = 0.1e1 / t40 / t69 * t54 * t57
  t77 = params.xt * t54 * t57
  t79 = 0.1e1 / t40 / t60
  t81 = s0 * t79 * tau0
  t84 = params.ct + t33 * t44 / 0.24e2 + 0.5e1 / 0.9e1 * t47 * t51 + t55 * t64 / 0.576e3 + 0.25e2 / 0.81e2 * t68 * t73 + 0.5e1 / 0.216e3 * t77 * t81
  t85 = t31 * t84
  t86 = params.ab * t32
  t89 = params.bb * tau0
  t92 = params.a2b * t54
  t95 = params.b2b * t67
  t99 = params.xb * t54 * t57
  t102 = params.cb + t86 * t44 / 0.24e2 + 0.5e1 / 0.9e1 * t89 * t51 + t92 * t64 / 0.576e3 + 0.25e2 / 0.81e2 * t95 * t73 + 0.5e1 / 0.216e3 * t99 * t81
  t103 = t102 ** 2
  t105 = 0.1e1 / t103 / t102
  t107 = 0.1e1 / t41 / t69
  t108 = t38 * t107
  t112 = t43 * t32 * t37
  t115 = t60 * t39
  t117 = 0.1e1 / t40 / t115
  t118 = t59 * t117
  t122 = t79 * t54 * t57
  t126 = s0 * t63 * tau0
  t129 = -t86 * t108 / 0.9e1 - 0.25e2 / 0.27e2 * t89 * t112 - t92 * t118 / 0.108e3 - 0.250e3 / 0.243e3 * t95 * t122 - 0.65e2 / 0.648e3 * t99 * t126
  t130 = t129 ** 2
  t131 = t105 * t130
  t132 = t85 * t131
  t135 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t136 = t135 * f.p.zeta_threshold
  t138 = f.my_piecewise3(t20, t136, t21 * t19)
  t139 = t5 * t138
  t150 = -t33 * t108 / 0.9e1 - 0.25e2 / 0.27e2 * t47 * t112 - t55 * t118 / 0.108e3 - 0.250e3 / 0.243e3 * t68 * t122 - 0.65e2 / 0.648e3 * t77 * t126
  t151 = t31 * t150
  t152 = 0.1e1 / t103
  t154 = 0.1e1 / t41 / t60
  t155 = t38 * t154
  t159 = t107 * t32 * t37
  t164 = 0.1e1 / t40 / t60 / t69
  t165 = t59 * t164
  t169 = t63 * t54 * t57
  t173 = s0 * t117 * tau0
  t176 = 0.11e2 / 0.27e2 * t86 * t155 + 0.200e3 / 0.81e2 * t89 * t159 + 0.19e2 / 0.324e3 * t92 * t165 + 0.3250e4 / 0.729e3 * t95 * t169 + 0.130e3 / 0.243e3 * t99 * t173
  t177 = t152 * t176
  t178 = t151 * t177
  t182 = 0.1e1 / t41 / t61
  t183 = t38 * t182
  t187 = t154 * t32 * t37
  t190 = t60 ** 2
  t192 = 0.1e1 / t40 / t190
  t193 = t59 * t192
  t197 = t117 * t54 * t57
  t201 = s0 * t164 * tau0
  t204 = -0.154e3 / 0.81e2 * t86 * t183 - 0.2200e4 / 0.243e3 * t89 * t187 - 0.209e3 / 0.486e3 * t92 * t193 - 0.52000e5 / 0.2187e4 * t95 * t197 - 0.2470e4 / 0.729e3 * t99 * t201
  t205 = t152 * t204
  t206 = t85 * t205
  t209 = t21 ** 2
  t210 = 0.1e1 / t209
  t211 = t26 ** 2
  t214 = t22 * t6
  t215 = 0.1e1 / t214
  t218 = 0.2e1 * t16 * t215 - 0.2e1 * t23
  t219 = f.my_piecewise5(t10, 0, t14, 0, t218)
  t223 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t210 * t211 + 0.4e1 / 0.3e1 * t21 * t219)
  t224 = t5 * t223
  t225 = t152 * t129
  t226 = t85 * t225
  t229 = t31 ** 2
  t230 = 0.1e1 / t229
  t231 = t230 * t84
  t232 = t231 * t225
  t235 = t151 * t225
  t238 = t85 * t177
  t242 = 0.1e1 / t229 / t6
  t243 = t242 * t84
  t244 = t243 * t225
  t247 = t230 * t150
  t248 = t247 * t225
  t251 = t231 * t177
  t264 = 0.11e2 / 0.27e2 * t33 * t155 + 0.200e3 / 0.81e2 * t47 * t159 + 0.19e2 / 0.324e3 * t55 * t165 + 0.3250e4 / 0.729e3 * t68 * t169 + 0.130e3 / 0.243e3 * t77 * t173
  t265 = t31 * t264
  t266 = t265 * t225
  t269 = t231 * t131
  t272 = -0.9e1 / 0.4e1 * t30 * t132 + 0.9e1 / 0.8e1 * t139 * t178 + 0.3e1 / 0.8e1 * t139 * t206 + 0.9e1 / 0.8e1 * t224 * t226 + 0.3e1 / 0.4e1 * t30 * t232 + 0.9e1 / 0.4e1 * t30 * t235 + 0.9e1 / 0.8e1 * t30 * t238 - t139 * t244 / 0.4e1 + 0.3e1 / 0.4e1 * t139 * t248 + 0.3e1 / 0.8e1 * t139 * t251 + 0.9e1 / 0.8e1 * t139 * t266 - 0.3e1 / 0.4e1 * t139 * t269
  t273 = t151 * t131
  t276 = t103 ** 2
  t277 = 0.1e1 / t276
  t279 = t277 * t130 * t129
  t280 = t85 * t279
  t284 = 0.1e1 / t229 / t22
  t285 = t284 * t84
  t286 = 0.1e1 / t102
  t287 = t285 * t286
  t290 = t230 * t264
  t291 = t290 * t286
  t304 = -0.154e3 / 0.81e2 * t33 * t183 - 0.2200e4 / 0.243e3 * t47 * t187 - 0.209e3 / 0.486e3 * t55 * t193 - 0.52000e5 / 0.2187e4 * t68 * t197 - 0.2470e4 / 0.729e3 * t77 * t201
  t305 = t31 * t304
  t306 = t305 * t286
  t309 = t247 * t286
  t312 = t265 * t286
  t315 = t242 * t150
  t316 = t315 * t286
  t319 = t151 * t286
  t322 = t231 * t286
  t325 = t243 * t286
  t329 = 0.1e1 / t209 / t19
  t333 = t210 * t26
  t336 = t22 ** 2
  t337 = 0.1e1 / t336
  t340 = -0.6e1 * t16 * t337 + 0.6e1 * t215
  t341 = f.my_piecewise5(t10, 0, t14, 0, t340)
  t345 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t329 * t211 * t26 + 0.4e1 / 0.3e1 * t333 * t219 + 0.4e1 / 0.3e1 * t21 * t341)
  t346 = t5 * t345
  t347 = t85 * t286
  t351 = t5 * t138 * t31
  t352 = t84 * t105
  t353 = t129 * t176
  t354 = t352 * t353
  t357 = -0.9e1 / 0.4e1 * t139 * t273 + 0.9e1 / 0.4e1 * t139 * t280 - 0.5e1 / 0.36e2 * t139 * t287 - 0.3e1 / 0.8e1 * t139 * t291 - 0.3e1 / 0.8e1 * t139 * t306 - 0.3e1 / 0.4e1 * t30 * t309 - 0.9e1 / 0.8e1 * t30 * t312 + t139 * t316 / 0.4e1 - 0.9e1 / 0.8e1 * t224 * t319 - 0.3e1 / 0.8e1 * t224 * t322 + t30 * t325 / 0.4e1 - 0.3e1 / 0.8e1 * t346 * t347 - 0.9e1 / 0.4e1 * t351 * t354
  t359 = f.my_piecewise3(t1, 0, t272 + t357)
  t361 = r1 <= f.p.dens_threshold
  t362 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t363 = 0.1e1 + t362
  t364 = t363 <= f.p.zeta_threshold
  t365 = t363 ** (0.1e1 / 0.3e1)
  t366 = t365 ** 2
  t368 = 0.1e1 / t366 / t363
  t370 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t371 = t370 ** 2
  t375 = 0.1e1 / t366
  t376 = t375 * t370
  t378 = f.my_piecewise5(t14, 0, t10, 0, -t218)
  t382 = f.my_piecewise5(t14, 0, t10, 0, -t340)
  t386 = f.my_piecewise3(t364, 0, -0.8e1 / 0.27e2 * t368 * t371 * t370 + 0.4e1 / 0.3e1 * t376 * t378 + 0.4e1 / 0.3e1 * t365 * t382)
  t387 = t5 * t386
  t389 = r1 ** 2
  t390 = r1 ** (0.1e1 / 0.3e1)
  t391 = t390 ** 2
  t394 = t37 * s2 / t391 / t389
  t401 = 0.1e1 / t391 / r1 * t32 * t37
  t404 = s2 ** 2
  t406 = t389 ** 2
  t410 = t57 * t404 / t390 / t406 / r1
  t413 = tau1 ** 2
  t419 = 0.1e1 / t390 / t389 / r1 * t54 * t57
  t425 = s2 / t390 / t406 * tau1
  t428 = params.ct + t33 * t394 / 0.24e2 + 0.5e1 / 0.9e1 * params.bt * tau1 * t401 + t55 * t410 / 0.576e3 + 0.25e2 / 0.81e2 * params.b2t * t413 * t419 + 0.5e1 / 0.216e3 * t77 * t425
  t443 = 0.1e1 / (params.cb + t86 * t394 / 0.24e2 + 0.5e1 / 0.9e1 * params.bb * tau1 * t401 + t92 * t410 / 0.576e3 + 0.25e2 / 0.81e2 * params.b2b * t413 * t419 + 0.5e1 / 0.216e3 * t99 * t425)
  t444 = t31 * t428 * t443
  t452 = f.my_piecewise3(t364, 0, 0.4e1 / 0.9e1 * t375 * t371 + 0.4e1 / 0.3e1 * t365 * t378)
  t453 = t5 * t452
  t455 = t230 * t428 * t443
  t460 = f.my_piecewise3(t364, 0, 0.4e1 / 0.3e1 * t365 * t370)
  t461 = t5 * t460
  t463 = t242 * t428 * t443
  t467 = f.my_piecewise3(t364, t136, t365 * t363)
  t468 = t5 * t467
  t470 = t284 * t428 * t443
  t474 = f.my_piecewise3(t361, 0, -0.3e1 / 0.8e1 * t387 * t444 - 0.3e1 / 0.8e1 * t453 * t455 + t461 * t463 / 0.4e1 - 0.5e1 / 0.36e2 * t468 * t470)
  t502 = 0.9e1 * t30 * t280 + 0.3e1 / 0.2e1 * t139 * t305 * t225 + 0.3e1 / 0.2e1 * t346 * t226 + 0.9e1 / 0.2e1 * t224 * t235 + 0.9e1 / 0.2e1 * t30 * t266 - t139 * t315 * t225 + 0.9e1 * t139 * t151 * t279 + 0.3e1 / 0.2e1 * t224 * t232 - t30 * t244 + 0.3e1 * t30 * t248 + 0.5e1 / 0.9e1 * t139 * t285 * t225 + 0.9e1 / 0.4e1 * t224 * t238
  t528 = t38 / t41 / t115
  t532 = t182 * t32 * t37
  t538 = t59 / t40 / t190 / r0
  t542 = t164 * t54 * t57
  t546 = s0 * t192 * tau0
  t562 = t130 ** 2
  t567 = -0.3e1 * t30 * t269 - 0.3e1 * t139 * t247 * t131 - 0.9e1 * t30 * t273 - 0.9e1 / 0.2e1 * t139 * t265 * t131 + 0.3e1 * t139 * t231 * t279 + 0.9e1 / 0.2e1 * t30 * t178 + 0.9e1 / 0.4e1 * t139 * t265 * t177 + 0.3e1 / 0.2e1 * t139 * t151 * t205 + 0.3e1 / 0.2e1 * t30 * t206 + 0.3e1 / 0.8e1 * t139 * t85 * t152 * (0.2618e4 / 0.243e3 * t86 * t528 + 0.30800e5 / 0.729e3 * t89 * t532 + 0.5225e4 / 0.1458e4 * t92 * t538 + 0.988000e6 / 0.6561e4 * t95 * t542 + 0.54340e5 / 0.2187e4 * t99 * t546) - t139 * t243 * t177 / 0.2e1 + 0.3e1 / 0.2e1 * t139 * t290 * t225 - 0.9e1 * t139 * t85 / t276 / t102 * t562
  t577 = t176 ** 2
  t610 = t19 ** 2
  t613 = t211 ** 2
  t619 = t219 ** 2
  t628 = -0.24e2 * t337 + 0.24e2 * t16 / t336 / t6
  t629 = f.my_piecewise5(t10, 0, t14, 0, t628)
  t633 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t209 / t610 * t613 - 0.16e2 / 0.9e1 * t329 * t211 * t219 + 0.4e1 / 0.3e1 * t210 * t619 + 0.16e2 / 0.9e1 * t333 * t341 + 0.4e1 / 0.3e1 * t21 * t629)
  t637 = 0.3e1 / 0.2e1 * t139 * t247 * t177 + t139 * t231 * t205 / 0.2e1 + 0.3e1 / 0.2e1 * t30 * t251 - 0.9e1 / 0.4e1 * t139 * t85 * t105 * t577 - 0.9e1 / 0.2e1 * t224 * t132 + t139 * t243 * t131 - 0.3e1 / 0.2e1 * t224 * t309 - 0.3e1 / 0.2e1 * t30 * t291 - 0.9e1 / 0.4e1 * t224 * t312 + t30 * t316 - t346 * t322 / 0.2e1 - 0.3e1 / 0.8e1 * t139 * t31 * (0.2618e4 / 0.243e3 * t33 * t528 + 0.30800e5 / 0.729e3 * t47 * t532 + 0.5225e4 / 0.1458e4 * t55 * t538 + 0.988000e6 / 0.6561e4 * t68 * t542 + 0.54340e5 / 0.2187e4 * t77 * t546) * t286 - 0.3e1 / 0.8e1 * t5 * t633 * t347
  t641 = 0.1e1 / t229 / t214
  t685 = -0.3e1 / 0.2e1 * t346 * t319 + 0.10e2 / 0.27e2 * t139 * t641 * t84 * t286 + t139 * t242 * t264 * t286 / 0.2e1 - 0.3e1 / 0.2e1 * t30 * t306 - t139 * t230 * t304 * t286 / 0.2e1 + t224 * t325 / 0.2e1 - 0.5e1 / 0.9e1 * t30 * t287 - 0.5e1 / 0.9e1 * t139 * t284 * t150 * t286 - 0.9e1 * t5 * t29 * t31 * t354 - 0.9e1 * t351 * t150 * t105 * t353 - 0.3e1 * t351 * t352 * t129 * t204 - 0.3e1 * t5 * t138 * t230 * t354 + 0.27e2 / 0.2e1 * t351 * t84 * t277 * t130 * t176
  t688 = f.my_piecewise3(t1, 0, t502 + t567 + t637 + t685)
  t689 = t363 ** 2
  t692 = t371 ** 2
  t698 = t378 ** 2
  t704 = f.my_piecewise5(t14, 0, t10, 0, -t628)
  t708 = f.my_piecewise3(t364, 0, 0.40e2 / 0.81e2 / t366 / t689 * t692 - 0.16e2 / 0.9e1 * t368 * t371 * t378 + 0.4e1 / 0.3e1 * t375 * t698 + 0.16e2 / 0.9e1 * t376 * t382 + 0.4e1 / 0.3e1 * t365 * t704)
  t723 = f.my_piecewise3(t361, 0, -0.3e1 / 0.8e1 * t5 * t708 * t444 - t387 * t455 / 0.2e1 + t453 * t463 / 0.2e1 - 0.5e1 / 0.9e1 * t461 * t470 + 0.10e2 / 0.27e2 * t468 * t641 * t428 * t443)
  d1111 = 0.4e1 * t359 + 0.4e1 * t474 + t6 * (t688 + t723)

  res = {'v4rho4': d1111}
  return res
