"""Generated from lda_c_chachiyo.mpl."""

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

  f_chachiyo = lambda rs, zeta: e0(rs) + (e1(rs) - e0(rs)) * f.f_zeta(zeta)

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

  f_chachiyo = lambda rs, zeta: e0(rs) + (e1(rs) - e0(rs)) * f.f_zeta(zeta)

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
  t42 = t41 * f.p.zeta_threshold
  t43 = t39 ** (0.1e1 / 0.3e1)
  t45 = f.my_piecewise3(t40, t42, t43 * t39)
  t46 = 0.1e1 - t38
  t47 = t46 <= f.p.zeta_threshold
  t48 = t46 ** (0.1e1 / 0.3e1)
  t50 = f.my_piecewise3(t47, t42, t48 * t46)
  t51 = t45 + t50 - 0.2e1
  t53 = 2 ** (0.1e1 / 0.3e1)
  t56 = 0.1e1 / (0.2e1 * t53 - 0.2e1)
  t57 = t35 * t51 * t56
  t59 = t8 / t19
  t63 = t18 / t10
  t69 = params.ap * (t3 * t59 / 0.9e1 + 0.2e1 / 0.9e1 * t14 * t63) / t23
  t80 = (params.af * (t26 * t59 / 0.9e1 + 0.2e1 / 0.9e1 * t29 * t63) / t32 - t69) * t51 * t56
  t81 = t9 ** 2
  t83 = t36 / t81
  t84 = t37 - t83
  t87 = f.my_piecewise3(t40, 0, 0.4e1 / 0.3e1 * t43 * t84)
  t91 = f.my_piecewise3(t47, 0, -0.4e1 / 0.3e1 * t48 * t84)
  vrho_0_ = t25 + t57 + t9 * (t69 + t80 + t35 * (t87 + t91) * t56)
  t97 = -t37 - t83
  t100 = f.my_piecewise3(t40, 0, 0.4e1 / 0.3e1 * t43 * t97)
  t104 = f.my_piecewise3(t47, 0, -0.4e1 / 0.3e1 * t48 * t97)
  vrho_1_ = t25 + t57 + t9 * (t69 + t80 + t35 * (t100 + t104) * t56)

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
  t38 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t36 * f.p.zeta_threshold, 1)
  t40 = 0.2e1 * t38 - 0.2e1
  t42 = 2 ** (0.1e1 / 0.3e1)
  t45 = 0.1e1 / (0.2e1 * t42 - 0.2e1)
  t48 = t8 / t18
  t52 = t17 / t9
  t58 = params.ap * (t3 * t48 / 0.9e1 + 0.2e1 / 0.9e1 * t13 * t52) / t22
  vrho_0_ = t24 + (params.af * t32 - t24) * t40 * t45 + r0 * (t58 + (params.af * (t25 * t48 / 0.9e1 + 0.2e1 / 0.9e1 * t28 * t52) / t31 - t58) * t40 * t45)

  res = {'vrho': vrho_0_}
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
  t36 = 0.2e1 * t35
  t37 = params.bf * t2
  t40 = params.cf * t1
  t43 = t37 * t13 / 0.9e1 + 0.2e1 / 0.9e1 * t40 * t22
  t49 = 0.1e1 + t37 * t27 / 0.3e1 + t40 * t30 / 0.3e1
  t50 = 0.1e1 / t49
  t52 = params.af * t43 * t50 - t35
  t53 = r0 - r1
  t54 = 0.1e1 / t9
  t55 = t53 * t54
  t56 = 0.1e1 + t55
  t57 = t56 <= f.p.zeta_threshold
  t58 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t59 = t58 * f.p.zeta_threshold
  t60 = t56 ** (0.1e1 / 0.3e1)
  t62 = f.my_piecewise3(t57, t59, t60 * t56)
  t63 = 0.1e1 - t55
  t64 = t63 <= f.p.zeta_threshold
  t65 = t63 ** (0.1e1 / 0.3e1)
  t67 = f.my_piecewise3(t64, t59, t65 * t63)
  t68 = t62 + t67 - 0.2e1
  t70 = 2 ** (0.1e1 / 0.3e1)
  t73 = 0.1e1 / (0.2e1 * t70 - 0.2e1)
  t75 = 0.2e1 * t52 * t68 * t73
  t76 = jnp.log(t49)
  t78 = jnp.log(t33)
  t80 = params.af * t76 - params.ap * t78
  t81 = t9 ** 2
  t82 = 0.1e1 / t81
  t83 = t53 * t82
  t84 = t54 - t83
  t87 = f.my_piecewise3(t57, 0, 0.4e1 / 0.3e1 * t60 * t84)
  t88 = -t84
  t91 = f.my_piecewise3(t64, 0, 0.4e1 / 0.3e1 * t65 * t88)
  t92 = t87 + t91
  t94 = t80 * t92 * t73
  t98 = t8 / t11 / t9
  t102 = t20 / t10 / t9
  t107 = params.ap * (-0.2e1 / 0.27e2 * t16 * t102 - 0.2e1 / 0.27e2 * t3 * t98) * t34
  t108 = t25 ** 2
  t110 = t33 ** 2
  t112 = params.ap * t108 / t110
  t119 = t43 ** 2
  t121 = t49 ** 2
  t126 = (params.af * (-0.2e1 / 0.27e2 * t40 * t102 - 0.2e1 / 0.27e2 * t37 * t98) * t50 - params.af * t119 / t121 - t107 + t112) * t68 * t73
  t128 = t52 * t92 * t73
  t130 = t60 ** 2
  t131 = 0.1e1 / t130
  t132 = t84 ** 2
  t136 = 0.1e1 / t81 / t9
  t137 = t53 * t136
  t139 = -0.2e1 * t82 + 0.2e1 * t137
  t143 = f.my_piecewise3(t57, 0, 0.4e1 / 0.9e1 * t131 * t132 + 0.4e1 / 0.3e1 * t60 * t139)
  t144 = t65 ** 2
  t145 = 0.1e1 / t144
  t146 = t88 ** 2
  t153 = f.my_piecewise3(t64, 0, 0.4e1 / 0.9e1 * t145 * t146 - 0.4e1 / 0.3e1 * t65 * t139)
  d11 = t36 + t75 + 0.2e1 * t94 + t9 * (t107 - t112 + t126 + 0.2e1 * t128 + t80 * (t143 + t153) * t73)
  t159 = -t54 - t83
  t162 = f.my_piecewise3(t57, 0, 0.4e1 / 0.3e1 * t60 * t159)
  t163 = -t159
  t166 = f.my_piecewise3(t64, 0, 0.4e1 / 0.3e1 * t65 * t163)
  t167 = t162 + t166
  t169 = t80 * t167 * t73
  t171 = t52 * t167 * t73
  t179 = f.my_piecewise3(t57, 0, 0.4e1 / 0.9e1 * t131 * t159 * t84 + 0.8e1 / 0.3e1 * t60 * t53 * t136)
  t187 = f.my_piecewise3(t64, 0, 0.4e1 / 0.9e1 * t145 * t163 * t88 - 0.8e1 / 0.3e1 * t65 * t53 * t136)
  d12 = t36 + t75 + t94 + t169 + t9 * (t107 - t112 + t126 + t128 + t171 + t80 * (t179 + t187) * t73)
  t195 = t159 ** 2
  t199 = 0.2e1 * t82 + 0.2e1 * t137
  t203 = f.my_piecewise3(t57, 0, 0.4e1 / 0.9e1 * t131 * t195 + 0.4e1 / 0.3e1 * t60 * t199)
  t204 = t163 ** 2
  t211 = f.my_piecewise3(t64, 0, 0.4e1 / 0.9e1 * t145 * t204 - 0.4e1 / 0.3e1 * t65 * t199)
  d22 = t36 + t75 + 0.2e1 * t169 + t9 * (t107 - t112 + t126 + 0.2e1 * t171 + t80 * (t203 + t211) * t73)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
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
  t36 = params.bf * t2
  t39 = params.cf * t1
  t42 = t36 * t12 / 0.9e1 + 0.2e1 / 0.9e1 * t39 * t21
  t48 = 0.1e1 + t36 * t26 / 0.3e1 + t39 * t29 / 0.3e1
  t49 = 0.1e1 / t48
  t53 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t55 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t53 * f.p.zeta_threshold, 1)
  t57 = 0.2e1 * t55 - 0.2e1
  t59 = 2 ** (0.1e1 / 0.3e1)
  t62 = 0.1e1 / (0.2e1 * t59 - 0.2e1)
  t67 = t8 / t10 / r0
  t71 = t19 / t9 / r0
  t76 = params.ap * (-0.2e1 / 0.27e2 * t15 * t71 - 0.2e1 / 0.27e2 * t3 * t67) * t33
  t77 = t24 ** 2
  t79 = t32 ** 2
  t81 = params.ap * t77 / t79
  t88 = t42 ** 2
  t90 = t48 ** 2
  v2rho2_0_ = 0.2e1 * t34 + 0.2e1 * (params.af * t42 * t49 - t34) * t57 * t62 + r0 * (t76 - t81 + (params.af * (-0.2e1 / 0.27e2 * t36 * t67 - 0.2e1 / 0.27e2 * t39 * t71) * t49 - params.af * t88 / t90 - t76 + t81) * t57 * t62)
  res = {'v2rho2': v2rho2_0_}
  return res
