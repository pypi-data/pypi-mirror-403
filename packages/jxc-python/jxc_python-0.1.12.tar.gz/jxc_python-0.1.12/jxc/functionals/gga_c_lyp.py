"""Generated from gga_c_lyp.mpl."""

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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))
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

  lyp_Cf = 3 / 10 * (3 * jnp.pi ** 2) ** (2 / 3)

  lyp_omega = lambda rr: params_b * jnp.exp(-params_c * rr) / (1 + params_d * rr)

  lyp_delta = lambda rr: (params_c + params_d / (1 + params_d * rr)) * rr

  lyp_aux6 = 1 / 2 ** (8 / 3)

  lyp_t1 = lambda rr, z: -(1 - z ** 2) / (1 + params_d * rr)

  lyp_t3 = lambda z: -lyp_Cf / 2 * (1 - z ** 2) * (f.opz_pow_n(z, 8 / 3) + f.opz_pow_n(-z, 8 / 3))

  lyp_t2 = lambda rr, z, xt: -xt ** 2 * ((1 - z ** 2) * (47 - 7 * lyp_delta(rr)) / (4 * 18) - 2 / 3)

  lyp_aux4 = lyp_aux6 / 4

  lyp_t6 = lambda z, xs0, xs1: -lyp_aux6 * (2 / 3 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3)) - f.opz_pow_n(z, 2) * xs1 ** 2 * f.opz_pow_n(-z, 8 / 3) / 4 - f.opz_pow_n(-z, 2) * xs0 ** 2 * f.opz_pow_n(z, 8 / 3) / 4)

  lyp_aux5 = lyp_aux4 / (9 * 2)

  lyp_t4 = lambda rr, z, xs0, xs1: lyp_aux4 * (1 - z ** 2) * (5 / 2 - lyp_delta(rr) / 18) * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))

  lyp_t5 = lambda rr, z, xs0, xs1: lyp_aux5 * (1 - z ** 2) * (lyp_delta(rr) - 11) * (xs0 ** 2 * f.opz_pow_n(z, 11 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 11 / 3))

  f_lyp_rr = lambda rr, z, xt, xs0, xs1: params_a * (lyp_t1(rr, z) + lyp_omega(rr) * (+lyp_t2(rr, z, xt) + lyp_t3(z) + lyp_t4(rr, z, xs0, xs1) + lyp_t5(rr, z, xs0, xs1) + lyp_t6(z, xs0, xs1)))

  f_lyp = lambda rs, z, xt, xs0, xs1: f_lyp_rr(rs / f.RS_FACTOR, z, xt, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_lyp(rs, z, xt, xs0, xs1)

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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))
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

  lyp_Cf = 3 / 10 * (3 * jnp.pi ** 2) ** (2 / 3)

  lyp_omega = lambda rr: params_b * jnp.exp(-params_c * rr) / (1 + params_d * rr)

  lyp_delta = lambda rr: (params_c + params_d / (1 + params_d * rr)) * rr

  lyp_aux6 = 1 / 2 ** (8 / 3)

  lyp_t1 = lambda rr, z: -(1 - z ** 2) / (1 + params_d * rr)

  lyp_t3 = lambda z: -lyp_Cf / 2 * (1 - z ** 2) * (f.opz_pow_n(z, 8 / 3) + f.opz_pow_n(-z, 8 / 3))

  lyp_t2 = lambda rr, z, xt: -xt ** 2 * ((1 - z ** 2) * (47 - 7 * lyp_delta(rr)) / (4 * 18) - 2 / 3)

  lyp_aux4 = lyp_aux6 / 4

  lyp_t6 = lambda z, xs0, xs1: -lyp_aux6 * (2 / 3 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3)) - f.opz_pow_n(z, 2) * xs1 ** 2 * f.opz_pow_n(-z, 8 / 3) / 4 - f.opz_pow_n(-z, 2) * xs0 ** 2 * f.opz_pow_n(z, 8 / 3) / 4)

  lyp_aux5 = lyp_aux4 / (9 * 2)

  lyp_t4 = lambda rr, z, xs0, xs1: lyp_aux4 * (1 - z ** 2) * (5 / 2 - lyp_delta(rr) / 18) * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))

  lyp_t5 = lambda rr, z, xs0, xs1: lyp_aux5 * (1 - z ** 2) * (lyp_delta(rr) - 11) * (xs0 ** 2 * f.opz_pow_n(z, 11 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 11 / 3))

  f_lyp_rr = lambda rr, z, xt, xs0, xs1: params_a * (lyp_t1(rr, z) + lyp_omega(rr) * (+lyp_t2(rr, z, xt) + lyp_t3(z) + lyp_t4(rr, z, xs0, xs1) + lyp_t5(rr, z, xs0, xs1) + lyp_t6(z, xs0, xs1)))

  f_lyp = lambda rs, z, xt, xs0, xs1: f_lyp_rr(rs / f.RS_FACTOR, z, xt, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_lyp(rs, z, xt, xs0, xs1)

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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))
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

  lyp_Cf = 3 / 10 * (3 * jnp.pi ** 2) ** (2 / 3)

  lyp_omega = lambda rr: params_b * jnp.exp(-params_c * rr) / (1 + params_d * rr)

  lyp_delta = lambda rr: (params_c + params_d / (1 + params_d * rr)) * rr

  lyp_aux6 = 1 / 2 ** (8 / 3)

  lyp_t1 = lambda rr, z: -(1 - z ** 2) / (1 + params_d * rr)

  lyp_t3 = lambda z: -lyp_Cf / 2 * (1 - z ** 2) * (f.opz_pow_n(z, 8 / 3) + f.opz_pow_n(-z, 8 / 3))

  lyp_t2 = lambda rr, z, xt: -xt ** 2 * ((1 - z ** 2) * (47 - 7 * lyp_delta(rr)) / (4 * 18) - 2 / 3)

  lyp_aux4 = lyp_aux6 / 4

  lyp_t6 = lambda z, xs0, xs1: -lyp_aux6 * (2 / 3 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3)) - f.opz_pow_n(z, 2) * xs1 ** 2 * f.opz_pow_n(-z, 8 / 3) / 4 - f.opz_pow_n(-z, 2) * xs0 ** 2 * f.opz_pow_n(z, 8 / 3) / 4)

  lyp_aux5 = lyp_aux4 / (9 * 2)

  lyp_t4 = lambda rr, z, xs0, xs1: lyp_aux4 * (1 - z ** 2) * (5 / 2 - lyp_delta(rr) / 18) * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))

  lyp_t5 = lambda rr, z, xs0, xs1: lyp_aux5 * (1 - z ** 2) * (lyp_delta(rr) - 11) * (xs0 ** 2 * f.opz_pow_n(z, 11 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 11 / 3))

  f_lyp_rr = lambda rr, z, xt, xs0, xs1: params_a * (lyp_t1(rr, z) + lyp_omega(rr) * (+lyp_t2(rr, z, xt) + lyp_t3(z) + lyp_t4(rr, z, xs0, xs1) + lyp_t5(rr, z, xs0, xs1) + lyp_t6(z, xs0, xs1)))

  f_lyp = lambda rs, z, xt, xs0, xs1: f_lyp_rr(rs / f.RS_FACTOR, z, xt, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_lyp(rs, z, xt, xs0, xs1)

  t1 = r0 - r1
  t2 = t1 ** 2
  t3 = r0 + r1
  t4 = t3 ** 2
  t5 = 0.1e1 / t4
  t7 = -t2 * t5 + 0.1e1
  t8 = t3 ** (0.1e1 / 0.3e1)
  t9 = 0.1e1 / t8
  t11 = params.d * t9 + 0.1e1
  t12 = 0.1e1 / t11
  t15 = jnp.exp(-params.c * t9)
  t16 = params.b * t15
  t18 = s0 + 0.2e1 * s1 + s2
  t19 = t8 ** 2
  t21 = 0.1e1 / t19 / t4
  t22 = t18 * t21
  t24 = params.d * t12 + params.c
  t25 = t24 * t9
  t27 = 0.47e2 - 0.7e1 * t25
  t30 = t7 * t27 / 0.72e2 - 0.2e1 / 0.3e1
  t32 = 3 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = t33 * t36
  t38 = 0.1e1 / t3
  t39 = t1 * t38
  t40 = 0.1e1 + t39
  t41 = t40 <= f.p.zeta_threshold
  t42 = f.p.zeta_threshold ** 2
  t43 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = t44 * t42
  t46 = t40 ** 2
  t47 = t40 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = t48 * t46
  t50 = f.my_piecewise3(t41, t45, t49)
  t51 = 0.1e1 - t39
  t52 = t51 <= f.p.zeta_threshold
  t53 = t51 ** 2
  t54 = t51 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t56 = t55 * t53
  t57 = f.my_piecewise3(t52, t45, t56)
  t58 = t50 + t57
  t62 = 2 ** (0.1e1 / 0.3e1)
  t63 = t62 * t7
  t65 = 0.5e1 / 0.2e1 - t25 / 0.18e2
  t66 = r0 ** 2
  t67 = r0 ** (0.1e1 / 0.3e1)
  t68 = t67 ** 2
  t70 = 0.1e1 / t68 / t66
  t71 = s0 * t70
  t72 = t71 * t50
  t73 = r1 ** 2
  t74 = r1 ** (0.1e1 / 0.3e1)
  t75 = t74 ** 2
  t77 = 0.1e1 / t75 / t73
  t78 = s2 * t77
  t79 = t78 * t57
  t80 = t72 + t79
  t81 = t65 * t80
  t84 = t25 - 0.11e2
  t86 = t44 * t42 * f.p.zeta_threshold
  t89 = f.my_piecewise3(t41, t86, t48 * t46 * t40)
  t93 = f.my_piecewise3(t52, t86, t55 * t53 * t51)
  t95 = t71 * t89 + t78 * t93
  t96 = t84 * t95
  t101 = f.my_piecewise3(t41, t42, t46)
  t102 = t101 * s2
  t103 = t77 * t57
  t106 = f.my_piecewise3(t52, t42, t53)
  t107 = t106 * s0
  t108 = t70 * t50
  t114 = -t22 * t30 - 0.3e1 / 0.20e2 * t37 * t7 * t58 + t63 * t81 / 0.32e2 + t63 * t96 / 0.576e3 - t62 * (0.2e1 / 0.3e1 * t72 + 0.2e1 / 0.3e1 * t79 - t102 * t103 / 0.4e1 - t107 * t108 / 0.4e1) / 0.8e1
  t118 = params.a * (t16 * t12 * t114 - t7 * t12)
  t119 = t3 * params.a
  t120 = t1 * t5
  t121 = t4 * t3
  t123 = t2 / t121
  t125 = -0.2e1 * t120 + 0.2e1 * t123
  t127 = t11 ** 2
  t128 = 0.1e1 / t127
  t131 = 0.1e1 / t8 / t3
  t134 = t7 * t128 * params.d * t131 / 0.3e1
  t137 = t15 * t12
  t140 = params.b * params.c * t131 * t137 * t114 / 0.3e1
  t145 = t16 * t128 * t114 * params.d * t131 / 0.3e1
  t150 = 0.8e1 / 0.3e1 * t18 / t19 / t121 * t30
  t152 = params.d ** 2
  t155 = 0.1e1 / t19 / t3
  t158 = -t152 * t128 * t155 + t24 * t131
  t160 = 0.7e1 / 0.3e1 * t7 * t158
  t167 = t48 * t40
  t168 = t38 - t120
  t171 = f.my_piecewise3(t41, 0, 0.8e1 / 0.3e1 * t167 * t168)
  t172 = t55 * t51
  t173 = -t168
  t176 = f.my_piecewise3(t52, 0, 0.8e1 / 0.3e1 * t172 * t173)
  t181 = t62 * t125
  t187 = t63 * t158 * t80 / 0.1728e4
  t190 = 0.1e1 / t68 / t66 / r0
  t191 = s0 * t190
  t192 = t191 * t50
  t194 = t71 * t171
  t195 = t78 * t176
  t206 = -t63 * t158 * t95 / 0.1728e4
  t211 = f.my_piecewise3(t41, 0, 0.11e2 / 0.3e1 * t49 * t168)
  t215 = f.my_piecewise3(t52, 0, 0.11e2 / 0.3e1 * t56 * t173)
  t226 = f.my_piecewise3(t41, 0, 0.2e1 * t40 * t168)
  t235 = f.my_piecewise3(t52, 0, 0.2e1 * t51 * t173)
  t248 = t150 - t22 * (t125 * t27 / 0.72e2 + t160 / 0.72e2) - 0.3e1 / 0.20e2 * t37 * t125 * t58 - 0.3e1 / 0.20e2 * t37 * t7 * (t171 + t176) + t181 * t81 / 0.32e2 + t187 + t63 * t65 * (-0.8e1 / 0.3e1 * t192 + t194 + t195) / 0.32e2 + t181 * t96 / 0.576e3 + t206 + t63 * t84 * (-0.8e1 / 0.3e1 * t191 * t89 + t71 * t211 + t78 * t215) / 0.576e3 - t62 * (-0.16e2 / 0.9e1 * t192 + 0.2e1 / 0.3e1 * t194 + 0.2e1 / 0.3e1 * t195 - t226 * s2 * t103 / 0.4e1 - t102 * t77 * t176 / 0.4e1 - t235 * s0 * t108 / 0.4e1 + 0.2e1 / 0.3e1 * t107 * t190 * t50 - t107 * t70 * t171 / 0.4e1) / 0.8e1
  vrho_0_ = t118 + t119 * (t16 * t12 * t248 - t125 * t12 - t134 + t140 + t145)
  t254 = 0.2e1 * t120 + 0.2e1 * t123
  t263 = -t38 - t120
  t266 = f.my_piecewise3(t41, 0, 0.8e1 / 0.3e1 * t167 * t263)
  t267 = -t263
  t270 = f.my_piecewise3(t52, 0, 0.8e1 / 0.3e1 * t172 * t267)
  t275 = t62 * t254
  t278 = t71 * t266
  t281 = 0.1e1 / t75 / t73 / r1
  t282 = s2 * t281
  t283 = t282 * t57
  t285 = t78 * t270
  t294 = f.my_piecewise3(t41, 0, 0.11e2 / 0.3e1 * t49 * t263)
  t300 = f.my_piecewise3(t52, 0, 0.11e2 / 0.3e1 * t56 * t267)
  t311 = f.my_piecewise3(t41, 0, 0.2e1 * t40 * t263)
  t323 = f.my_piecewise3(t52, 0, 0.2e1 * t51 * t267)
  t333 = t150 - t22 * (t254 * t27 / 0.72e2 + t160 / 0.72e2) - 0.3e1 / 0.20e2 * t37 * t254 * t58 - 0.3e1 / 0.20e2 * t37 * t7 * (t266 + t270) + t275 * t81 / 0.32e2 + t187 + t63 * t65 * (t278 - 0.8e1 / 0.3e1 * t283 + t285) / 0.32e2 + t275 * t96 / 0.576e3 + t206 + t63 * t84 * (t71 * t294 - 0.8e1 / 0.3e1 * t282 * t93 + t78 * t300) / 0.576e3 - t62 * (0.2e1 / 0.3e1 * t278 - 0.16e2 / 0.9e1 * t283 + 0.2e1 / 0.3e1 * t285 - t311 * s2 * t103 / 0.4e1 + 0.2e1 / 0.3e1 * t102 * t281 * t57 - t102 * t77 * t270 / 0.4e1 - t323 * s0 * t108 / 0.4e1 - t107 * t70 * t266 / 0.4e1) / 0.8e1
  vrho_1_ = t118 + t119 * (t16 * t12 * t333 - t254 * t12 - t134 + t140 + t145)
  t338 = t119 * params.b
  t339 = t21 * t30
  vsigma_0_ = t338 * t137 * (-t339 + t63 * t65 * t70 * t50 / 0.32e2 + t63 * t84 * t70 * t89 / 0.576e3 - t62 * (0.2e1 / 0.3e1 * t108 - t106 * t70 * t50 / 0.4e1) / 0.8e1)
  vsigma_1_ = -0.2e1 * t155 * params.a * params.b * t137 * t30
  vsigma_2_ = t338 * t137 * (-t339 + t63 * t65 * t77 * t57 / 0.32e2 + t63 * t84 * t77 * t93 / 0.576e3 - t62 * (0.2e1 / 0.3e1 * t103 - t101 * t77 * t57 / 0.4e1) / 0.8e1)
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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))
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

  lyp_Cf = 3 / 10 * (3 * jnp.pi ** 2) ** (2 / 3)

  lyp_omega = lambda rr: params_b * jnp.exp(-params_c * rr) / (1 + params_d * rr)

  lyp_delta = lambda rr: (params_c + params_d / (1 + params_d * rr)) * rr

  lyp_aux6 = 1 / 2 ** (8 / 3)

  lyp_t1 = lambda rr, z: -(1 - z ** 2) / (1 + params_d * rr)

  lyp_t3 = lambda z: -lyp_Cf / 2 * (1 - z ** 2) * (f.opz_pow_n(z, 8 / 3) + f.opz_pow_n(-z, 8 / 3))

  lyp_t2 = lambda rr, z, xt: -xt ** 2 * ((1 - z ** 2) * (47 - 7 * lyp_delta(rr)) / (4 * 18) - 2 / 3)

  lyp_aux4 = lyp_aux6 / 4

  lyp_t6 = lambda z, xs0, xs1: -lyp_aux6 * (2 / 3 * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3)) - f.opz_pow_n(z, 2) * xs1 ** 2 * f.opz_pow_n(-z, 8 / 3) / 4 - f.opz_pow_n(-z, 2) * xs0 ** 2 * f.opz_pow_n(z, 8 / 3) / 4)

  lyp_aux5 = lyp_aux4 / (9 * 2)

  lyp_t4 = lambda rr, z, xs0, xs1: lyp_aux4 * (1 - z ** 2) * (5 / 2 - lyp_delta(rr) / 18) * (xs0 ** 2 * f.opz_pow_n(z, 8 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 8 / 3))

  lyp_t5 = lambda rr, z, xs0, xs1: lyp_aux5 * (1 - z ** 2) * (lyp_delta(rr) - 11) * (xs0 ** 2 * f.opz_pow_n(z, 11 / 3) + xs1 ** 2 * f.opz_pow_n(-z, 11 / 3))

  f_lyp_rr = lambda rr, z, xt, xs0, xs1: params_a * (lyp_t1(rr, z) + lyp_omega(rr) * (+lyp_t2(rr, z, xt) + lyp_t3(z) + lyp_t4(rr, z, xs0, xs1) + lyp_t5(rr, z, xs0, xs1) + lyp_t6(z, xs0, xs1)))

  f_lyp = lambda rs, z, xt, xs0, xs1: f_lyp_rr(rs / f.RS_FACTOR, z, xt, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_lyp(rs, z, xt, xs0, xs1)

  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / t1
  t4 = params.d * t2 + 0.1e1
  t5 = 0.1e1 / t4
  t7 = jnp.exp(-params.c * t2)
  t8 = params.b * t7
  t9 = r0 ** 2
  t10 = t1 ** 2
  t12 = 0.1e1 / t10 / t9
  t13 = s0 * t12
  t15 = params.d * t5 + params.c
  t16 = t15 * t2
  t18 = -0.1e1 / 0.72e2 - 0.7e1 / 0.72e2 * t16
  t20 = 3 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t26 = 0.1e1 <= f.p.zeta_threshold
  t27 = f.p.zeta_threshold ** 2
  t28 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t31 = f.my_piecewise3(t26, t29 * t27, 1)
  t35 = 0.5e1 / 0.2e1 - t16 / 0.18e2
  t36 = t35 * s0
  t37 = t12 * t31
  t40 = t16 - 0.11e2
  t41 = t40 * s0
  t44 = f.my_piecewise3(t26, t29 * t27 * f.p.zeta_threshold, 1)
  t45 = t12 * t44
  t48 = 2 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = s0 * t49
  t53 = f.my_piecewise3(t26, t27, 1)
  t54 = t53 * s0
  t56 = t49 * t12 * t31
  t62 = -t13 * t18 - 0.3e1 / 0.10e2 * t21 * t24 * t31 + t36 * t37 / 0.8e1 + t41 * t45 / 0.144e3 - t48 * (0.4e1 / 0.3e1 * t50 * t37 - t54 * t56 / 0.2e1) / 0.8e1
  t67 = r0 * params.a
  t68 = t4 ** 2
  t69 = 0.1e1 / t68
  t72 = 0.1e1 / t1 / r0
  t77 = t7 * t5
  t88 = 0.1e1 / t10 / t9 / r0
  t92 = params.d ** 2
  t98 = -t92 * t69 / t10 / r0 + t15 * t72
  t105 = t88 * t31
  vrho_0_ = params.a * (t8 * t5 * t62 - t5) + t67 * (-t69 * params.d * t72 / 0.3e1 + params.b * params.c * t72 * t77 * t62 / 0.3e1 + t8 * t69 * t62 * params.d * t72 / 0.3e1 + t8 * t5 * (0.8e1 / 0.3e1 * s0 * t88 * t18 - 0.7e1 / 0.216e3 * t13 * t98 + t98 * s0 * t37 / 0.432e3 - t36 * t105 / 0.3e1 - t98 * s0 * t45 / 0.432e3 - t41 * t88 * t44 / 0.54e2 - t48 * (-0.32e2 / 0.9e1 * t50 * t105 + 0.4e1 / 0.3e1 * t54 * t49 * t88 * t31) / 0.8e1))
  vsigma_0_ = t67 * params.b * t77 * (-t12 * t18 + t35 * t12 * t31 / 0.8e1 + t40 * t12 * t44 / 0.144e3 - t48 * (0.4e1 / 0.3e1 * t56 - t53 * t49 * t37 / 0.2e1) / 0.8e1)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
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

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / t1
  t4 = params.d * t2 + 0.1e1
  t5 = t4 ** 2
  t7 = 0.1e1 / t5 / t4
  t8 = params.d ** 2
  t9 = t7 * t8
  t10 = r0 ** 2
  t11 = t1 ** 2
  t13 = 0.1e1 / t11 / t10
  t16 = 0.1e1 / t5
  t17 = t16 * params.d
  t19 = 0.1e1 / t1 / t10
  t22 = params.b * params.c
  t23 = t22 * t19
  t25 = jnp.exp(-params.c * t2)
  t26 = 0.1e1 / t4
  t27 = t25 * t26
  t28 = s0 * t13
  t30 = params.d * t26 + params.c
  t31 = t30 * t2
  t33 = -0.1e1 / 0.72e2 - 0.7e1 / 0.72e2 * t31
  t35 = 3 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t41 = 0.1e1 <= f.p.zeta_threshold
  t42 = f.p.zeta_threshold ** 2
  t43 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t46 = f.my_piecewise3(t41, t44 * t42, 1)
  t51 = (0.5e1 / 0.2e1 - t31 / 0.18e2) * s0
  t52 = t13 * t46
  t56 = (t31 - 0.11e2) * s0
  t59 = f.my_piecewise3(t41, t44 * t42 * f.p.zeta_threshold, 1)
  t60 = t13 * t59
  t63 = 2 ** (0.1e1 / 0.3e1)
  t64 = t63 ** 2
  t65 = s0 * t64
  t68 = f.my_piecewise3(t41, t42, 1)
  t69 = t68 * s0
  t77 = -t28 * t33 - 0.3e1 / 0.10e2 * t36 * t39 * t46 + t51 * t52 / 0.8e1 + t56 * t60 / 0.144e3 - t63 * (0.4e1 / 0.3e1 * t65 * t52 - t69 * t64 * t13 * t46 / 0.2e1) / 0.8e1
  t78 = t27 * t77
  t81 = params.c ** 2
  t82 = params.b * t81
  t83 = t82 * t13
  t86 = t22 * t13
  t87 = t25 * t16
  t88 = t77 * params.d
  t89 = t87 * t88
  t93 = 0.1e1 / t1 / r0
  t94 = t22 * t93
  t95 = t10 * r0
  t97 = 0.1e1 / t11 / t95
  t98 = s0 * t97
  t101 = t8 * t16
  t106 = -t101 / t11 / r0 + t30 * t93
  t107 = 0.7e1 / 0.216e3 * t106
  t110 = t106 * s0 / 0.54e2
  t113 = t97 * t46
  t118 = -t106 * s0 / 0.3e1
  t121 = t97 * t59
  t133 = 0.8e1 / 0.3e1 * t98 * t33 - t28 * t107 + t110 * t52 / 0.8e1 - t51 * t113 / 0.3e1 + t118 * t60 / 0.144e3 - t56 * t121 / 0.54e2 - t63 * (-0.32e2 / 0.9e1 * t65 * t113 + 0.4e1 / 0.3e1 * t69 * t64 * t97 * t46) / 0.8e1
  t134 = t27 * t133
  t137 = params.b * t25
  t138 = t137 * t7
  t139 = t77 * t8
  t143 = t137 * t16
  t144 = t133 * params.d
  t151 = t10 ** 2
  t153 = 0.1e1 / t11 / t151
  t154 = s0 * t153
  t159 = t8 * params.d
  t160 = t159 * t7
  t162 = t160 / t95
  t164 = t101 * t13
  t166 = t30 * t19
  t168 = -0.7e1 / 0.324e3 * t162 + 0.7e1 / 0.108e3 * t164 - 0.7e1 / 0.162e3 * t166
  t174 = (-t162 / 0.81e2 + t164 / 0.27e2 - 0.2e1 / 0.81e2 * t166) * s0
  t179 = t153 * t46
  t186 = (0.2e1 / 0.9e1 * t162 - 0.2e1 / 0.3e1 * t164 + 0.4e1 / 0.9e1 * t166) * s0
  t191 = t153 * t59
  t203 = -0.88e2 / 0.9e1 * t154 * t33 + 0.16e2 / 0.3e1 * t98 * t107 - t28 * t168 + t174 * t52 / 0.8e1 - 0.2e1 / 0.3e1 * t110 * t113 + 0.11e2 / 0.9e1 * t51 * t179 + t186 * t60 / 0.144e3 - t118 * t121 / 0.27e2 + 0.11e2 / 0.162e3 * t56 * t191 - t63 * (0.352e3 / 0.27e2 * t65 * t179 - 0.44e2 / 0.9e1 * t69 * t64 * t153 * t46) / 0.8e1
  t213 = 0.1e1 / t151
  t226 = 0.1e1 / t1 / t95
  t239 = t5 ** 2
  t240 = 0.1e1 / t239
  t250 = 0.1e1 / t11 / t151 / r0
  t258 = t8 ** 2
  t262 = t258 * t240 / t1 / t151
  t264 = t160 * t213
  t266 = t101 * t97
  t268 = t30 * t226
  t283 = t250 * t46
  t310 = 0.1232e4 / 0.27e2 * s0 * t250 * t33 - 0.88e2 / 0.3e1 * t154 * t107 + 0.8e1 * t98 * t168 - t28 * (-0.7e1 / 0.324e3 * t262 + 0.35e2 / 0.324e3 * t264 - 0.91e2 / 0.486e3 * t266 + 0.49e2 / 0.486e3 * t268) + (-t262 / 0.81e2 + 0.5e1 / 0.81e2 * t264 - 0.26e2 / 0.243e3 * t266 + 0.14e2 / 0.243e3 * t268) * s0 * t52 / 0.8e1 - t174 * t113 + 0.11e2 / 0.3e1 * t110 * t179 - 0.154e3 / 0.27e2 * t51 * t283 + (0.2e1 / 0.9e1 * t262 - 0.10e2 / 0.9e1 * t264 + 0.52e2 / 0.27e2 * t266 - 0.28e2 / 0.27e2 * t268) * s0 * t60 / 0.144e3 - t186 * t121 / 0.18e2 + 0.11e2 / 0.54e2 * t118 * t191 - 0.77e2 / 0.243e3 * t56 * t250 * t59 - t63 * (-0.4928e4 / 0.81e2 * t65 * t283 + 0.616e3 / 0.27e2 * t69 * t64 * t250 * t46) / 0.8e1
  t339 = 0.2e1 / 0.3e1 * t86 * t87 * t144 + 0.2e1 / 0.9e1 * t22 * t213 * t25 * t7 * t139 - 0.8e1 / 0.9e1 * t138 * t139 * t97 - 0.4e1 / 0.3e1 * t143 * t144 * t19 + 0.28e2 / 0.27e2 * t143 * t88 * t226 + 0.28e2 / 0.27e2 * t22 * t226 * t78 - 0.8e1 / 0.9e1 * t22 * t97 * t89 + t82 * t213 * t89 / 0.9e1 - 0.2e1 / 0.9e1 * t240 * t159 * t213 + 0.8e1 / 0.9e1 * t9 * t97 - 0.28e2 / 0.27e2 * t17 * t226 + t137 * t26 * t310 - 0.4e1 / 0.3e1 * t23 * t134 - 0.4e1 / 0.9e1 * t82 * t97 * t78 + t83 * t134 / 0.3e1 + params.b * t81 * params.c * t213 * t78 / 0.27e2 + t94 * t27 * t203 + 0.2e1 / 0.3e1 * t138 * t133 * t8 * t13 + 0.2e1 / 0.9e1 * t137 * t240 * t77 * t159 * t213 + t143 * t203 * params.d * t93
  v3rho3_0_ = 0.3e1 * params.a * (-0.2e1 / 0.9e1 * t9 * t13 + 0.4e1 / 0.9e1 * t17 * t19 - 0.4e1 / 0.9e1 * t23 * t78 + t83 * t78 / 0.9e1 + 0.2e1 / 0.9e1 * t86 * t89 + 0.2e1 / 0.3e1 * t94 * t134 + 0.2e1 / 0.9e1 * t138 * t139 * t13 + 0.2e1 / 0.3e1 * t143 * t144 * t93 - 0.4e1 / 0.9e1 * t143 * t88 * t19 + t137 * t26 * t203) + r0 * params.a * t339

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.b * params.c
  t2 = r0 ** 2
  t3 = r0 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t6 = 0.1e1 / t4 / t2
  t7 = t1 * t6
  t8 = 0.1e1 / t3
  t10 = jnp.exp(-params.c * t8)
  t12 = params.d * t8 + 0.1e1
  t13 = t12 ** 2
  t14 = 0.1e1 / t13
  t15 = t10 * t14
  t16 = t2 * r0
  t18 = 0.1e1 / t4 / t16
  t19 = s0 * t18
  t20 = 0.1e1 / t12
  t22 = params.d * t20 + params.c
  t23 = t22 * t8
  t25 = -0.1e1 / 0.72e2 - 0.7e1 / 0.72e2 * t23
  t28 = s0 * t6
  t29 = params.d ** 2
  t30 = t29 * t14
  t35 = 0.1e1 / t3 / r0
  t37 = -t30 / t4 / r0 + t22 * t35
  t38 = 0.7e1 / 0.216e3 * t37
  t41 = t37 * s0 / 0.54e2
  t42 = 0.1e1 <= f.p.zeta_threshold
  t43 = f.p.zeta_threshold ** 2
  t44 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t47 = f.my_piecewise3(t42, t45 * t43, 1)
  t48 = t6 * t47
  t53 = (0.5e1 / 0.2e1 - t23 / 0.18e2) * s0
  t54 = t18 * t47
  t59 = -t37 * s0 / 0.3e1
  t62 = f.my_piecewise3(t42, t45 * t43 * f.p.zeta_threshold, 1)
  t63 = t6 * t62
  t67 = (t23 - 0.11e2) * s0
  t68 = t18 * t62
  t71 = 2 ** (0.1e1 / 0.3e1)
  t72 = t71 ** 2
  t73 = s0 * t72
  t76 = f.my_piecewise3(t42, t43, 1)
  t77 = t76 * s0
  t85 = 0.8e1 / 0.3e1 * t19 * t25 - t28 * t38 + t41 * t48 / 0.8e1 - t53 * t54 / 0.3e1 + t59 * t63 / 0.144e3 - t67 * t68 / 0.54e2 - t71 * (-0.32e2 / 0.9e1 * t73 * t54 + 0.4e1 / 0.3e1 * t77 * t72 * t18 * t47) / 0.8e1
  t86 = t85 * params.d
  t87 = t15 * t86
  t90 = t2 ** 2
  t91 = 0.1e1 / t90
  t92 = t1 * t91
  t94 = 0.1e1 / t13 / t12
  t95 = t10 * t94
  t97 = 3 ** (0.1e1 / 0.3e1)
  t98 = t97 ** 2
  t99 = jnp.pi ** 2
  t100 = t99 ** (0.1e1 / 0.3e1)
  t101 = t100 ** 2
  t118 = -t28 * t25 - 0.3e1 / 0.10e2 * t98 * t101 * t47 + t53 * t48 / 0.8e1 + t67 * t63 / 0.144e3 - t71 * (0.4e1 / 0.3e1 * t73 * t48 - t77 * t72 * t6 * t47 / 0.2e1) / 0.8e1
  t119 = t118 * t29
  t120 = t95 * t119
  t123 = params.b * t10
  t124 = t123 * t94
  t128 = t123 * t14
  t130 = 0.1e1 / t3 / t2
  t134 = t118 * params.d
  t136 = 0.1e1 / t3 / t16
  t140 = t1 * t136
  t141 = t10 * t20
  t142 = t141 * t118
  t145 = t1 * t18
  t146 = t15 * t134
  t149 = params.c ** 2
  t150 = params.b * t149
  t151 = t150 * t91
  t154 = t13 ** 2
  t155 = 0.1e1 / t154
  t156 = t29 * params.d
  t157 = t155 * t156
  t160 = t94 * t29
  t163 = t14 * params.d
  t166 = t90 * r0
  t168 = 0.1e1 / t4 / t166
  t169 = s0 * t168
  t173 = 0.1e1 / t4 / t90
  t174 = s0 * t173
  t177 = t156 * t94
  t179 = t177 / t16
  t181 = t30 * t6
  t183 = t22 * t130
  t185 = -0.7e1 / 0.324e3 * t179 + 0.7e1 / 0.108e3 * t181 - 0.7e1 / 0.162e3 * t183
  t188 = t29 ** 2
  t189 = t188 * t155
  t191 = 0.1e1 / t3 / t90
  t192 = t189 * t191
  t194 = t177 * t91
  t196 = t30 * t18
  t198 = t22 * t136
  t200 = -0.7e1 / 0.324e3 * t192 + 0.35e2 / 0.324e3 * t194 - 0.91e2 / 0.486e3 * t196 + 0.49e2 / 0.486e3 * t198
  t207 = (-t192 / 0.81e2 + 0.5e1 / 0.81e2 * t194 - 0.26e2 / 0.243e3 * t196 + 0.14e2 / 0.243e3 * t198) * s0
  t214 = (-t179 / 0.81e2 + t181 / 0.27e2 - 0.2e1 / 0.81e2 * t183) * s0
  t216 = t173 * t47
  t219 = t168 * t47
  t227 = (0.2e1 / 0.9e1 * t192 - 0.10e2 / 0.9e1 * t194 + 0.52e2 / 0.27e2 * t196 - 0.28e2 / 0.27e2 * t198) * s0
  t234 = (0.2e1 / 0.9e1 * t179 - 0.2e1 / 0.3e1 * t181 + 0.4e1 / 0.9e1 * t183) * s0
  t237 = t173 * t62
  t240 = t168 * t62
  t252 = 0.1232e4 / 0.27e2 * t169 * t25 - 0.88e2 / 0.3e1 * t174 * t38 + 0.8e1 * t19 * t185 - t28 * t200 + t207 * t48 / 0.8e1 - t214 * t54 + 0.11e2 / 0.3e1 * t41 * t216 - 0.154e3 / 0.27e2 * t53 * t219 + t227 * t63 / 0.144e3 - t234 * t68 / 0.18e2 + 0.11e2 / 0.54e2 * t59 * t237 - 0.77e2 / 0.243e3 * t67 * t240 - t71 * (-0.4928e4 / 0.81e2 * t73 * t219 + 0.616e3 / 0.27e2 * t77 * t72 * t168 * t47) / 0.8e1
  t255 = t1 * t130
  t256 = t141 * t85
  t259 = t150 * t18
  t262 = t150 * t6
  t266 = params.b * t149 * params.c
  t267 = t266 * t91
  t270 = t1 * t35
  t297 = -0.88e2 / 0.9e1 * t174 * t25 + 0.16e2 / 0.3e1 * t19 * t38 - t28 * t185 + t214 * t48 / 0.8e1 - 0.2e1 / 0.3e1 * t41 * t54 + 0.11e2 / 0.9e1 * t53 * t216 + t234 * t63 / 0.144e3 - t59 * t68 / 0.27e2 + 0.11e2 / 0.162e3 * t67 * t237 - t71 * (0.352e3 / 0.27e2 * t73 * t216 - 0.44e2 / 0.9e1 * t77 * t72 * t173 * t47) / 0.8e1
  t298 = t141 * t297
  t300 = t85 * t29
  t304 = t123 * t155
  t305 = t118 * t156
  t309 = t297 * params.d
  t312 = 0.2e1 / 0.3e1 * t7 * t87 + 0.2e1 / 0.9e1 * t92 * t120 - 0.8e1 / 0.9e1 * t124 * t119 * t18 - 0.4e1 / 0.3e1 * t128 * t86 * t130 + 0.28e2 / 0.27e2 * t128 * t134 * t136 + 0.28e2 / 0.27e2 * t140 * t142 - 0.8e1 / 0.9e1 * t145 * t146 + t151 * t146 / 0.9e1 - 0.2e1 / 0.9e1 * t157 * t91 + 0.8e1 / 0.9e1 * t160 * t18 - 0.28e2 / 0.27e2 * t163 * t136 + t123 * t20 * t252 - 0.4e1 / 0.3e1 * t255 * t256 - 0.4e1 / 0.9e1 * t259 * t142 + t262 * t256 / 0.3e1 + t267 * t142 / 0.27e2 + t270 * t298 + 0.2e1 / 0.3e1 * t124 * t300 * t6 + 0.2e1 / 0.9e1 * t304 * t305 * t91 + t128 * t309 * t35
  t318 = 0.1e1 / t154 / t12
  t320 = t188 * params.d * t318 * t168
  t323 = 0.1e1 / t3 / t166
  t324 = t189 * t323
  t326 = 0.1e1 / t166
  t327 = t177 * t326
  t329 = t30 * t173
  t331 = t22 * t191
  t348 = 0.1e1 / t4 / t90 / t2
  t352 = t348 * t47
  t392 = (-0.4e1 / 0.243e3 * t320 + 0.28e2 / 0.243e3 * t324 - 0.232e3 / 0.729e3 * t327 + 0.100e3 / 0.243e3 * t329 - 0.140e3 / 0.729e3 * t331) * s0 * t48 / 0.8e1 + (0.8e1 / 0.27e2 * t320 - 0.56e2 / 0.27e2 * t324 + 0.464e3 / 0.81e2 * t327 - 0.200e3 / 0.27e2 * t329 + 0.280e3 / 0.81e2 * t331) * s0 * t63 / 0.144e3 - 0.20944e5 / 0.81e2 * s0 * t348 * t25 - t71 * (0.83776e5 / 0.243e3 * t73 * t352 - 0.10472e5 / 0.81e2 * t77 * t72 * t348 * t47) / 0.8e1 - 0.4e1 / 0.3e1 * t207 * t54 + 0.22e2 / 0.3e1 * t214 * t216 - 0.616e3 / 0.27e2 * t41 * t219 + 0.2618e4 / 0.81e2 * t53 * t352 - 0.2e1 / 0.27e2 * t227 * t68 + 0.11e2 / 0.27e2 * t234 * t237 - 0.308e3 / 0.243e3 * t59 * t240 + 0.1309e4 / 0.729e3 * t67 * t348 * t62 + 0.4928e4 / 0.27e2 * t169 * t38 - 0.176e3 / 0.3e1 * t174 * t185 + 0.32e2 / 0.3e1 * t19 * t200 - t28 * (-0.7e1 / 0.243e3 * t320 + 0.49e2 / 0.243e3 * t324 - 0.406e3 / 0.729e3 * t327 + 0.175e3 / 0.243e3 * t329 - 0.245e3 / 0.729e3 * t331)
  t440 = t123 * t20 * t392 + 0.16e2 / 0.9e1 * t157 * t326 - 0.320e3 / 0.81e2 * t160 * t173 + 0.280e3 / 0.81e2 * t163 * t191 - 0.8e1 / 0.27e2 * t318 * t188 * t323 - 0.16e2 / 0.9e1 * t1 * t326 * t120 - 0.8e1 / 0.9e1 * t150 * t326 * t146 + 0.4e1 / 0.81e2 * t266 * t323 * t146 + 0.4e1 / 0.3e1 * t7 * t15 * t309 + 0.4e1 / 0.9e1 * t151 * t87 + 0.8e1 / 0.9e1 * t92 * t95 * t300 + 0.4e1 / 0.27e2 * t150 * t323 * t120 + 0.8e1 / 0.27e2 * t1 * t323 * t10 * t155 * t305 + 0.320e3 / 0.81e2 * t1 * t173 * t146 - 0.32e2 / 0.9e1 * t145 * t87 + 0.320e3 / 0.81e2 * t124 * t119 * t173 + 0.112e3 / 0.27e2 * t128 * t86 * t136
  t479 = t149 ** 2
  t497 = -0.280e3 / 0.81e2 * t128 * t134 * t191 - 0.280e3 / 0.81e2 * t1 * t191 * t142 - 0.32e2 / 0.9e1 * t124 * t300 * t18 - 0.16e2 / 0.9e1 * t304 * t305 * t326 - 0.8e1 / 0.3e1 * t128 * t309 * t130 + 0.112e3 / 0.27e2 * t140 * t256 + 0.160e3 / 0.81e2 * t150 * t173 * t142 + 0.4e1 / 0.3e1 * t270 * t141 * t252 + 0.4e1 / 0.3e1 * t128 * t252 * params.d * t35 - 0.8e1 / 0.3e1 * t255 * t298 - 0.16e2 / 0.9e1 * t259 * t256 - 0.8e1 / 0.27e2 * t266 * t326 * t142 + 0.2e1 / 0.3e1 * t262 * t298 + 0.4e1 / 0.27e2 * t267 * t256 + params.b * t479 * t323 * t142 / 0.81e2 + 0.4e1 / 0.3e1 * t124 * t297 * t29 * t6 + 0.8e1 / 0.9e1 * t304 * t85 * t156 * t91 + 0.8e1 / 0.27e2 * t123 * t318 * t118 * t188 * t323
  v4rho4_0_ = 0.4e1 * params.a * t312 + r0 * params.a * (t440 + t497)

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 - r1
  t2 = r0 + r1
  t3 = t2 ** 2
  t4 = 0.1e1 / t3
  t5 = t1 * t4
  t6 = t1 ** 2
  t7 = t3 * t2
  t8 = 0.1e1 / t7
  t9 = t6 * t8
  t11 = -0.2e1 * t5 + 0.2e1 * t9
  t12 = t2 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / t12
  t15 = params.d * t13 + 0.1e1
  t16 = 0.1e1 / t15
  t19 = -t6 * t4 + 0.1e1
  t20 = t15 ** 2
  t21 = 0.1e1 / t20
  t22 = t19 * t21
  t24 = 0.1e1 / t12 / t2
  t25 = params.d * t24
  t27 = t22 * t25 / 0.3e1
  t28 = params.b * params.c
  t29 = t28 * t24
  t31 = jnp.exp(-params.c * t13)
  t32 = t31 * t16
  t34 = s0 + 0.2e1 * s1 + s2
  t35 = t12 ** 2
  t37 = 0.1e1 / t35 / t3
  t38 = t34 * t37
  t40 = params.d * t16 + params.c
  t41 = t40 * t13
  t43 = 0.47e2 - 0.7e1 * t41
  t46 = t19 * t43 / 0.72e2 - 0.2e1 / 0.3e1
  t48 = 3 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = jnp.pi ** 2
  t51 = t50 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t53 = t49 * t52
  t54 = 0.1e1 / t2
  t55 = t1 * t54
  t56 = 0.1e1 + t55
  t57 = t56 <= f.p.zeta_threshold
  t58 = f.p.zeta_threshold ** 2
  t59 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = t60 * t58
  t62 = t56 ** 2
  t63 = t56 ** (0.1e1 / 0.3e1)
  t64 = t63 ** 2
  t65 = t64 * t62
  t66 = f.my_piecewise3(t57, t61, t65)
  t67 = 0.1e1 - t55
  t68 = t67 <= f.p.zeta_threshold
  t69 = t67 ** 2
  t70 = t67 ** (0.1e1 / 0.3e1)
  t71 = t70 ** 2
  t72 = t71 * t69
  t73 = f.my_piecewise3(t68, t61, t72)
  t74 = t66 + t73
  t78 = 2 ** (0.1e1 / 0.3e1)
  t79 = t78 * t19
  t81 = 0.5e1 / 0.2e1 - t41 / 0.18e2
  t82 = r0 ** 2
  t83 = r0 ** (0.1e1 / 0.3e1)
  t84 = t83 ** 2
  t86 = 0.1e1 / t84 / t82
  t87 = s0 * t86
  t88 = t87 * t66
  t89 = r1 ** 2
  t90 = r1 ** (0.1e1 / 0.3e1)
  t91 = t90 ** 2
  t93 = 0.1e1 / t91 / t89
  t94 = s2 * t93
  t95 = t94 * t73
  t96 = t88 + t95
  t97 = t81 * t96
  t100 = t41 - 0.11e2
  t102 = t60 * t58 * f.p.zeta_threshold
  t105 = f.my_piecewise3(t57, t102, t64 * t62 * t56)
  t109 = f.my_piecewise3(t68, t102, t71 * t69 * t67)
  t111 = t87 * t105 + t94 * t109
  t112 = t100 * t111
  t117 = f.my_piecewise3(t57, t58, t62)
  t118 = t117 * s2
  t119 = t93 * t73
  t122 = f.my_piecewise3(t68, t58, t69)
  t123 = t122 * s0
  t124 = t86 * t66
  t130 = -t38 * t46 - 0.3e1 / 0.20e2 * t53 * t19 * t74 + t79 * t97 / 0.32e2 + t79 * t112 / 0.576e3 - t78 * (0.2e1 / 0.3e1 * t88 + 0.2e1 / 0.3e1 * t95 - t118 * t119 / 0.4e1 - t123 * t124 / 0.4e1) / 0.8e1
  t131 = t32 * t130
  t133 = t29 * t131 / 0.3e1
  t134 = params.b * t31
  t135 = t134 * t21
  t136 = t130 * params.d
  t139 = t135 * t136 * t24 / 0.3e1
  t142 = t34 / t35 / t7
  t144 = 0.8e1 / 0.3e1 * t142 * t46
  t146 = params.d ** 2
  t147 = t146 * t21
  t152 = -t147 / t35 / t2 + t40 * t24
  t153 = 0.7e1 / 0.3e1 * t152
  t154 = t19 * t153
  t156 = t11 * t43 / 0.72e2 + t154 / 0.72e2
  t161 = t64 * t56
  t162 = t54 - t5
  t165 = f.my_piecewise3(t57, 0, 0.8e1 / 0.3e1 * t161 * t162)
  t166 = t71 * t67
  t167 = -t162
  t170 = f.my_piecewise3(t68, 0, 0.8e1 / 0.3e1 * t166 * t167)
  t171 = t165 + t170
  t175 = t78 * t11
  t178 = t152 / 0.54e2
  t179 = t178 * t96
  t181 = t79 * t179 / 0.32e2
  t184 = 0.1e1 / t84 / t82 / r0
  t185 = s0 * t184
  t186 = t185 * t66
  t188 = t87 * t165
  t189 = t94 * t170
  t190 = -0.8e1 / 0.3e1 * t186 + t188 + t189
  t191 = t81 * t190
  t197 = -t152 / 0.3e1
  t198 = t197 * t111
  t200 = t79 * t198 / 0.576e3
  t205 = f.my_piecewise3(t57, 0, 0.11e2 / 0.3e1 * t65 * t162)
  t209 = f.my_piecewise3(t68, 0, 0.11e2 / 0.3e1 * t72 * t167)
  t211 = -0.8e1 / 0.3e1 * t185 * t105 + t87 * t205 + t94 * t209
  t212 = t100 * t211
  t220 = f.my_piecewise3(t57, 0, 0.2e1 * t56 * t162)
  t221 = t220 * s2
  t224 = t93 * t170
  t229 = f.my_piecewise3(t68, 0, 0.2e1 * t67 * t167)
  t230 = t229 * s0
  t233 = t184 * t66
  t236 = t86 * t165
  t242 = t144 - t38 * t156 - 0.3e1 / 0.20e2 * t53 * t11 * t74 - 0.3e1 / 0.20e2 * t53 * t19 * t171 + t175 * t97 / 0.32e2 + t181 + t79 * t191 / 0.32e2 + t175 * t112 / 0.576e3 + t200 + t79 * t212 / 0.576e3 - t78 * (-0.16e2 / 0.9e1 * t186 + 0.2e1 / 0.3e1 * t188 + 0.2e1 / 0.3e1 * t189 - t221 * t119 / 0.4e1 - t118 * t224 / 0.4e1 - t230 * t124 / 0.4e1 + 0.2e1 / 0.3e1 * t123 * t233 - t123 * t236 / 0.4e1) / 0.8e1
  t246 = params.a * (t134 * t16 * t242 - t11 * t16 + t133 + t139 - t27)
  t248 = t2 * params.a
  t249 = 0.2e1 * t4
  t250 = t1 * t8
  t251 = 0.8e1 * t250
  t252 = t3 ** 2
  t255 = 0.6e1 * t6 / t252
  t256 = -t249 + t251 - t255
  t259 = t11 * t21 * t25
  t262 = 0.1e1 / t20 / t15
  t266 = 0.2e1 / 0.9e1 * t19 * t262 * t146 * t37
  t268 = 0.1e1 / t12 / t3
  t271 = 0.4e1 / 0.9e1 * t22 * params.d * t268
  t274 = 0.4e1 / 0.9e1 * t28 * t268 * t131
  t275 = params.c ** 2
  t279 = params.b * t275 * t37 * t131 / 0.9e1
  t284 = 0.2e1 / 0.9e1 * t28 * t37 * t31 * t21 * t136
  t286 = t29 * t32 * t242
  t292 = 0.2e1 / 0.9e1 * t134 * t262 * t130 * t146 * t37
  t295 = t135 * t242 * params.d * t24
  t299 = 0.4e1 / 0.9e1 * t135 * t136 * t268
  t300 = t82 ** 2
  t302 = 0.1e1 / t84 / t300
  t303 = s0 * t302
  t304 = t303 * t66
  t306 = t185 * t165
  t308 = t162 ** 2
  t312 = -0.2e1 * t4 + 0.2e1 * t250
  t316 = f.my_piecewise3(t57, 0, 0.40e2 / 0.9e1 * t64 * t308 + 0.8e1 / 0.3e1 * t161 * t312)
  t317 = t87 * t316
  t319 = t167 ** 2
  t322 = -t312
  t326 = f.my_piecewise3(t68, 0, 0.40e2 / 0.9e1 * t71 * t319 + 0.8e1 / 0.3e1 * t166 * t322)
  t327 = t94 * t326
  t332 = f.my_piecewise3(t57, 0, 0.2e1 * t56 * t312 + 0.2e1 * t308)
  t344 = f.my_piecewise3(t68, 0, 0.2e1 * t67 * t322 + 0.2e1 * t319)
  t361 = 0.176e3 / 0.27e2 * t304 - 0.32e2 / 0.9e1 * t306 + 0.2e1 / 0.3e1 * t317 + 0.2e1 / 0.3e1 * t327 - t332 * s2 * t119 / 0.4e1 - t221 * t224 / 0.2e1 - t118 * t93 * t326 / 0.4e1 - t344 * s0 * t124 / 0.4e1 + 0.4e1 / 0.3e1 * t230 * t233 - t230 * t236 / 0.2e1 - 0.22e2 / 0.9e1 * t123 * t302 * t66 + 0.4e1 / 0.3e1 * t123 * t184 * t165 - t123 * t86 * t316 / 0.4e1
  t368 = 0.88e2 / 0.9e1 * t34 / t35 / t252 * t46
  t379 = t78 * t256
  t382 = t175 * t179
  t388 = t146 * params.d * t262 * t8
  t390 = t147 * t37
  t392 = t40 * t268
  t397 = t79 * (-t388 / 0.81e2 + t390 / 0.27e2 - 0.2e1 / 0.81e2 * t392) * t96 / 0.32e2
  t399 = t79 * t178 * t190
  t409 = t175 * t198
  t419 = t79 * (0.2e1 / 0.9e1 * t388 - 0.2e1 / 0.3e1 * t390 + 0.4e1 / 0.9e1 * t392) * t111 / 0.576e3
  t421 = t79 * t197 * t211
  t432 = f.my_piecewise3(t57, 0, 0.88e2 / 0.9e1 * t161 * t308 + 0.11e2 / 0.3e1 * t65 * t312)
  t439 = f.my_piecewise3(t68, 0, 0.88e2 / 0.9e1 * t166 * t319 + 0.11e2 / 0.3e1 * t72 * t322)
  t445 = t142 * t156
  t449 = t11 * t153
  t455 = t19 * (-0.14e2 / 0.9e1 * t388 + 0.14e2 / 0.3e1 * t390 - 0.28e2 / 0.9e1 * t392)
  t456 = t455 / 0.72e2
  t459 = -t78 * t361 / 0.8e1 - t368 - 0.3e1 / 0.20e2 * t53 * t256 * t74 - 0.3e1 / 0.10e2 * t53 * t11 * t171 - 0.3e1 / 0.20e2 * t53 * t19 * (t316 + t326) + t379 * t97 / 0.32e2 + t382 / 0.16e2 + t175 * t191 / 0.16e2 + t397 + t399 / 0.16e2 + t79 * t81 * (0.88e2 / 0.9e1 * t304 - 0.16e2 / 0.3e1 * t306 + t317 + t327) / 0.32e2 + t379 * t112 / 0.576e3 + t409 / 0.288e3 + t175 * t212 / 0.288e3 + t419 + t421 / 0.288e3 + t79 * t100 * (0.88e2 / 0.9e1 * t303 * t105 - 0.16e2 / 0.3e1 * t185 * t205 + t87 * t432 + t94 * t439) / 0.576e3 + 0.16e2 / 0.3e1 * t445 - t38 * (t256 * t43 / 0.72e2 + t449 / 0.36e2 + t456)
  t462 = -t256 * t16 - 0.2e1 / 0.3e1 * t259 - t266 + t271 - t274 + t279 + t284 + 0.2e1 / 0.3e1 * t286 + t292 + 0.2e1 / 0.3e1 * t295 - t299 + t134 * t16 * t459
  d11 = t248 * t462 + 0.2e1 * t246
  t465 = 0.2e1 * t5 + 0.2e1 * t9
  t469 = t465 * t43 / 0.72e2 + t154 / 0.72e2
  t474 = -t54 - t5
  t475 = t161 * t474
  t477 = f.my_piecewise3(t57, 0, 0.8e1 / 0.3e1 * t475)
  t478 = -t474
  t479 = t166 * t478
  t481 = f.my_piecewise3(t68, 0, 0.8e1 / 0.3e1 * t479)
  t482 = t477 + t481
  t486 = t78 * t465
  t489 = t87 * t477
  t492 = 0.1e1 / t91 / t89 / r1
  t493 = s2 * t492
  t494 = t493 * t73
  t496 = t94 * t481
  t497 = t489 - 0.8e1 / 0.3e1 * t494 + t496
  t498 = t81 * t497
  t505 = f.my_piecewise3(t57, 0, 0.11e2 / 0.3e1 * t65 * t474)
  t511 = f.my_piecewise3(t68, 0, 0.11e2 / 0.3e1 * t72 * t478)
  t513 = t87 * t505 - 0.8e1 / 0.3e1 * t493 * t109 + t94 * t511
  t514 = t100 * t513
  t522 = f.my_piecewise3(t57, 0, 0.2e1 * t56 * t474)
  t523 = t522 * s2
  t526 = t492 * t73
  t529 = t93 * t481
  t534 = f.my_piecewise3(t68, 0, 0.2e1 * t67 * t478)
  t535 = t534 * s0
  t538 = t86 * t477
  t544 = t144 - t38 * t469 - 0.3e1 / 0.20e2 * t53 * t465 * t74 - 0.3e1 / 0.20e2 * t53 * t19 * t482 + t486 * t97 / 0.32e2 + t181 + t79 * t498 / 0.32e2 + t486 * t112 / 0.576e3 + t200 + t79 * t514 / 0.576e3 - t78 * (0.2e1 / 0.3e1 * t489 - 0.16e2 / 0.9e1 * t494 + 0.2e1 / 0.3e1 * t496 - t523 * t119 / 0.4e1 + 0.2e1 / 0.3e1 * t118 * t526 - t118 * t529 / 0.4e1 - t535 * t124 / 0.4e1 - t123 * t538 / 0.4e1) / 0.8e1
  t548 = params.a * (t134 * t16 * t544 - t465 * t16 + t133 + t139 - t27)
  t549 = t249 - t255
  t552 = t465 * t21 * t25
  t558 = t29 * t32 * t544
  t562 = t135 * t544 * params.d * t24
  t564 = t185 * t477
  t573 = f.my_piecewise3(t57, 0, 0.40e2 / 0.9e1 * t64 * t474 * t162 + 0.16e2 / 0.3e1 * t161 * t1 * t8)
  t574 = t87 * t573
  t576 = t493 * t170
  t585 = f.my_piecewise3(t68, 0, 0.40e2 / 0.9e1 * t71 * t478 * t167 - 0.16e2 / 0.3e1 * t166 * t1 * t8)
  t586 = t94 * t585
  t594 = f.my_piecewise3(t57, 0, 0.4e1 * t56 * t1 * t8 + 0.2e1 * t162 * t474)
  t616 = f.my_piecewise3(t68, 0, -0.4e1 * t67 * t1 * t8 + 0.2e1 * t167 * t478)
  t632 = -0.16e2 / 0.9e1 * t564 + 0.2e1 / 0.3e1 * t574 - 0.16e2 / 0.9e1 * t576 + 0.2e1 / 0.3e1 * t586 - t594 * s2 * t119 / 0.4e1 - t523 * t224 / 0.4e1 + 0.2e1 / 0.3e1 * t221 * t526 + 0.2e1 / 0.3e1 * t118 * t492 * t170 - t221 * t529 / 0.4e1 - t118 * t93 * t585 / 0.4e1 - t616 * s0 * t124 / 0.4e1 + 0.2e1 / 0.3e1 * t535 * t233 - t535 * t236 / 0.4e1 - t230 * t538 / 0.4e1 + 0.2e1 / 0.3e1 * t123 * t184 * t477 - t123 * t86 * t573 / 0.4e1
  t635 = t142 * t469
  t638 = t465 * t153
  t651 = f.my_piecewise3(t57, 0, 0.88e2 / 0.9e1 * t475 * t162 + 0.22e2 / 0.3e1 * t65 * t1 * t8)
  t661 = f.my_piecewise3(t68, 0, 0.88e2 / 0.9e1 * t479 * t167 - 0.22e2 / 0.3e1 * t72 * t1 * t8)
  t680 = t78 * t549
  t683 = t486 * t179
  t687 = -t78 * t632 / 0.8e1 + 0.8e1 / 0.3e1 * t635 - t38 * (t549 * t43 / 0.72e2 + t449 / 0.72e2 + t455 / 0.72e2 + t638 / 0.72e2) + 0.8e1 / 0.3e1 * t445 - t368 + t79 * t100 * (-0.8e1 / 0.3e1 * t185 * t505 + t87 * t651 - 0.8e1 / 0.3e1 * t493 * t209 + t94 * t661) / 0.576e3 - 0.3e1 / 0.20e2 * t53 * t549 * t74 - 0.3e1 / 0.20e2 * t53 * t465 * t171 - 0.3e1 / 0.20e2 * t53 * t11 * t482 - 0.3e1 / 0.20e2 * t53 * t19 * (t573 + t585) + t680 * t97 / 0.32e2 + t683 / 0.32e2 + t486 * t191 / 0.32e2
  t691 = t79 * t178 * t497
  t701 = t486 * t198
  t708 = t79 * t197 * t513
  t714 = t175 * t498 / 0.32e2 + t691 / 0.32e2 + t79 * t81 * (-0.8e1 / 0.3e1 * t564 + t574 - 0.8e1 / 0.3e1 * t576 + t586) / 0.32e2 + t680 * t112 / 0.576e3 + t701 / 0.576e3 + t486 * t212 / 0.576e3 + t175 * t514 / 0.576e3 + t708 / 0.576e3 + t382 / 0.32e2 + t397 + t399 / 0.32e2 + t409 / 0.576e3 + t419 + t421 / 0.576e3
  t718 = -t549 * t16 - t552 / 0.3e1 - t259 / 0.3e1 - t266 + t271 - t274 + t279 + t284 + t286 / 0.3e1 + t292 + t295 / 0.3e1 - t299 + t558 / 0.3e1 + t562 / 0.3e1 + t134 * t16 * (t687 + t714)
  d12 = t248 * t718 + t246 + t548
  t721 = -t249 - t251 - t255
  t726 = t474 ** 2
  t730 = 0.2e1 * t4 + 0.2e1 * t250
  t734 = f.my_piecewise3(t57, 0, 0.40e2 / 0.9e1 * t64 * t726 + 0.8e1 / 0.3e1 * t161 * t730)
  t735 = t87 * t734
  t737 = t89 ** 2
  t739 = 0.1e1 / t91 / t737
  t740 = s2 * t739
  t741 = t740 * t73
  t743 = t493 * t481
  t745 = t478 ** 2
  t748 = -t730
  t752 = f.my_piecewise3(t68, 0, 0.40e2 / 0.9e1 * t71 * t745 + 0.8e1 / 0.3e1 * t166 * t748)
  t753 = t94 * t752
  t758 = f.my_piecewise3(t57, 0, 0.2e1 * t56 * t730 + 0.2e1 * t726)
  t778 = f.my_piecewise3(t68, 0, 0.2e1 * t67 * t748 + 0.2e1 * t745)
  t787 = 0.2e1 / 0.3e1 * t735 + 0.176e3 / 0.27e2 * t741 - 0.32e2 / 0.9e1 * t743 + 0.2e1 / 0.3e1 * t753 - t758 * s2 * t119 / 0.4e1 + 0.4e1 / 0.3e1 * t523 * t526 - t523 * t529 / 0.2e1 - 0.22e2 / 0.9e1 * t118 * t739 * t73 + 0.4e1 / 0.3e1 * t118 * t492 * t481 - t118 * t93 * t752 / 0.4e1 - t778 * s0 * t124 / 0.4e1 - t535 * t538 / 0.2e1 - t123 * t86 * t734 / 0.4e1
  t806 = t78 * t721
  t830 = f.my_piecewise3(t57, 0, 0.88e2 / 0.9e1 * t161 * t726 + 0.11e2 / 0.3e1 * t65 * t730)
  t841 = f.my_piecewise3(t68, 0, 0.88e2 / 0.9e1 * t166 * t745 + 0.11e2 / 0.3e1 * t72 * t748)
  t847 = -t78 * t787 / 0.8e1 + 0.16e2 / 0.3e1 * t635 - t38 * (t721 * t43 / 0.72e2 + t638 / 0.36e2 + t456) - t368 - 0.3e1 / 0.20e2 * t53 * t721 * t74 - 0.3e1 / 0.10e2 * t53 * t465 * t482 - 0.3e1 / 0.20e2 * t53 * t19 * (t734 + t752) + t806 * t97 / 0.32e2 + t683 / 0.16e2 + t486 * t498 / 0.16e2 + t397 + t691 / 0.16e2 + t79 * t81 * (t735 + 0.88e2 / 0.9e1 * t741 - 0.16e2 / 0.3e1 * t743 + t753) / 0.32e2 + t806 * t112 / 0.576e3 + t701 / 0.288e3 + t486 * t514 / 0.288e3 + t419 + t708 / 0.288e3 + t79 * t100 * (t87 * t830 + 0.88e2 / 0.9e1 * t740 * t109 - 0.16e2 / 0.3e1 * t493 * t511 + t94 * t841) / 0.576e3
  t850 = -t721 * t16 - 0.2e1 / 0.3e1 * t552 - t266 + t271 - t274 + t279 + t284 + 0.2e1 / 0.3e1 * t558 + t292 + 0.2e1 / 0.3e1 * t562 - t299 + t134 * t16 * t847
  d22 = t248 * t850 + 0.2e1 * t548
  t1 = params.a * params.b
  t2 = r0 + r1
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t6 = jnp.exp(-params.c * t4)
  t8 = params.d * t4 + 0.1e1
  t9 = 0.1e1 / t8
  t10 = t6 * t9
  t11 = t2 ** 2
  t12 = t3 ** 2
  t14 = 0.1e1 / t12 / t11
  t15 = r0 - r1
  t16 = t15 ** 2
  t17 = 0.1e1 / t11
  t19 = -t16 * t17 + 0.1e1
  t21 = params.d * t9 + params.c
  t22 = t21 * t4
  t24 = 0.47e2 - 0.7e1 * t22
  t27 = t19 * t24 / 0.72e2 - 0.2e1 / 0.3e1
  t28 = t14 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 * t19
  t32 = 0.5e1 / 0.2e1 - t22 / 0.18e2
  t33 = r0 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / t33
  t38 = t32 * t37
  t39 = 0.1e1 / t2
  t40 = t15 * t39
  t41 = 0.1e1 + t40
  t42 = t41 <= f.p.zeta_threshold
  t43 = f.p.zeta_threshold ** 2
  t44 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = t45 * t43
  t47 = t41 ** 2
  t48 = t41 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = t49 * t47
  t51 = f.my_piecewise3(t42, t46, t50)
  t52 = t38 * t51
  t55 = t22 - 0.11e2
  t56 = t55 * t37
  t58 = t45 * t43 * f.p.zeta_threshold
  t61 = f.my_piecewise3(t42, t58, t49 * t47 * t41)
  t62 = t56 * t61
  t67 = 0.1e1 - t40
  t68 = t67 <= f.p.zeta_threshold
  t69 = t67 ** 2
  t70 = f.my_piecewise3(t68, t43, t69)
  t71 = t70 * t37
  t77 = -t28 + t30 * t52 / 0.32e2 + t30 * t62 / 0.576e3 - t29 * (0.2e1 / 0.3e1 * t37 * t51 - t71 * t51 / 0.4e1) / 0.8e1
  t81 = t4 * params.a * params.b
  t82 = params.c * t6
  t87 = t8 ** 2
  t88 = 0.1e1 / t87
  t89 = t6 * t88
  t95 = t2 * params.a * params.b
  t96 = t11 * t2
  t100 = 0.8e1 / 0.3e1 / t12 / t96 * t27
  t101 = t15 * t17
  t102 = 0.1e1 / t96
  t105 = 0.2e1 * t16 * t102 - 0.2e1 * t101
  t107 = params.d ** 2
  t110 = 0.1e1 / t12 / t2
  t115 = -t107 * t88 * t110 + t21 / t3 / t2
  t119 = t105 * t24 / 0.72e2 + 0.7e1 / 0.216e3 * t19 * t115
  t120 = t14 * t119
  t121 = t29 * t105
  t124 = t115 / 0.54e2
  t131 = 0.1e1 / t35 / t33 / r0
  t137 = t39 - t101
  t140 = f.my_piecewise3(t42, 0, 0.8e1 / 0.3e1 * t49 * t41 * t137)
  t147 = -t115 / 0.3e1
  t158 = f.my_piecewise3(t42, 0, 0.11e2 / 0.3e1 * t50 * t137)
  t166 = -t137
  t169 = f.my_piecewise3(t68, 0, 0.2e1 * t67 * t166)
  t181 = t100 - t120 + t121 * t52 / 0.32e2 + t30 * t124 * t37 * t51 / 0.32e2 - t30 * t32 * t131 * t51 / 0.12e2 + t30 * t38 * t140 / 0.32e2 + t121 * t62 / 0.576e3 + t30 * t147 * t37 * t61 / 0.576e3 - t30 * t55 * t131 * t61 / 0.216e3 + t30 * t56 * t158 / 0.576e3 - t29 * (-0.16e2 / 0.9e1 * t131 * t51 + 0.2e1 / 0.3e1 * t37 * t140 - t169 * t37 * t51 / 0.4e1 + 0.2e1 / 0.3e1 * t70 * t131 * t51 - t71 * t140 / 0.4e1) / 0.8e1
  d13 = t1 * t10 * t77 + t81 * t82 * t9 * t77 / 0.3e1 + t81 * t89 * t77 * params.d / 0.3e1 + t95 * t10 * t181
  t190 = t102 * params.a * params.b
  d14 = 0.10e2 / 0.3e1 * t14 * params.a * params.b * t10 * t27 - 0.2e1 / 0.3e1 * t190 * t82 * t9 * t27 - 0.2e1 / 0.3e1 * t190 * t89 * t27 * params.d - 0.2e1 * t110 * params.a * params.b * t10 * t119
  t204 = r1 ** 2
  t205 = r1 ** (0.1e1 / 0.3e1)
  t206 = t205 ** 2
  t208 = 0.1e1 / t206 / t204
  t209 = t32 * t208
  t210 = t67 ** (0.1e1 / 0.3e1)
  t211 = t210 ** 2
  t212 = t211 * t69
  t213 = f.my_piecewise3(t68, t46, t212)
  t214 = t209 * t213
  t217 = t55 * t208
  t220 = f.my_piecewise3(t68, t58, t211 * t69 * t67)
  t221 = t217 * t220
  t226 = f.my_piecewise3(t42, t43, t47)
  t227 = t226 * t208
  t233 = -t28 + t30 * t214 / 0.32e2 + t30 * t221 / 0.576e3 - t29 * (0.2e1 / 0.3e1 * t208 * t213 - t227 * t213 / 0.4e1) / 0.8e1
  t253 = f.my_piecewise3(t68, 0, 0.8e1 / 0.3e1 * t211 * t67 * t166)
  t265 = f.my_piecewise3(t68, 0, 0.11e2 / 0.3e1 * t212 * t166)
  t273 = f.my_piecewise3(t42, 0, 0.2e1 * t41 * t137)
  d15 = t1 * t10 * t233 + t81 * t82 * t9 * t233 / 0.3e1 + t81 * t89 * t233 * params.d / 0.3e1 + t95 * t10 * (t100 - t120 + t121 * t214 / 0.32e2 + t30 * t124 * t208 * t213 / 0.32e2 + t30 * t209 * t253 / 0.32e2 + t121 * t221 / 0.576e3 + t30 * t147 * t208 * t220 / 0.576e3 + t30 * t217 * t265 / 0.576e3 - t29 * (0.2e1 / 0.3e1 * t208 * t253 - t273 * t208 * t213 / 0.4e1 - t227 * t253 / 0.4e1) / 0.8e1)
  t1 = params.a * params.b
  t2 = r0 + r1
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t6 = jnp.exp(-params.c * t4)
  t8 = params.d * t4 + 0.1e1
  t9 = 0.1e1 / t8
  t10 = t6 * t9
  t11 = t2 ** 2
  t12 = t3 ** 2
  t14 = 0.1e1 / t12 / t11
  t15 = r0 - r1
  t16 = t15 ** 2
  t17 = 0.1e1 / t11
  t19 = -t16 * t17 + 0.1e1
  t21 = params.d * t9 + params.c
  t22 = t21 * t4
  t24 = 0.47e2 - 0.7e1 * t22
  t27 = t19 * t24 / 0.72e2 - 0.2e1 / 0.3e1
  t28 = t14 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 * t19
  t32 = 0.5e1 / 0.2e1 - t22 / 0.18e2
  t33 = r0 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / t33
  t38 = t32 * t37
  t39 = 0.1e1 / t2
  t40 = t15 * t39
  t41 = 0.1e1 + t40
  t42 = t41 <= f.p.zeta_threshold
  t43 = f.p.zeta_threshold ** 2
  t44 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = t45 * t43
  t47 = t41 ** 2
  t48 = t41 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = t49 * t47
  t51 = f.my_piecewise3(t42, t46, t50)
  t52 = t38 * t51
  t55 = t22 - 0.11e2
  t56 = t55 * t37
  t58 = t45 * t43 * f.p.zeta_threshold
  t61 = f.my_piecewise3(t42, t58, t49 * t47 * t41)
  t62 = t56 * t61
  t67 = 0.1e1 - t40
  t68 = t67 <= f.p.zeta_threshold
  t69 = t67 ** 2
  t70 = f.my_piecewise3(t68, t43, t69)
  t71 = t70 * t37
  t77 = -t28 + t30 * t52 / 0.32e2 + t30 * t62 / 0.576e3 - t29 * (0.2e1 / 0.3e1 * t37 * t51 - t71 * t51 / 0.4e1) / 0.8e1
  t81 = t4 * params.a * params.b
  t82 = params.c * t6
  t87 = t8 ** 2
  t88 = 0.1e1 / t87
  t89 = t6 * t88
  t95 = t2 * params.a * params.b
  t96 = t11 * t2
  t100 = 0.8e1 / 0.3e1 / t12 / t96 * t27
  t101 = t15 * t17
  t102 = 0.1e1 / t96
  t105 = 0.2e1 * t16 * t102 + 0.2e1 * t101
  t107 = params.d ** 2
  t110 = 0.1e1 / t12 / t2
  t115 = -t107 * t88 * t110 + t21 / t3 / t2
  t119 = t105 * t24 / 0.72e2 + 0.7e1 / 0.216e3 * t19 * t115
  t120 = t14 * t119
  t121 = t29 * t105
  t124 = t115 / 0.54e2
  t130 = -t39 - t101
  t133 = f.my_piecewise3(t42, 0, 0.8e1 / 0.3e1 * t49 * t41 * t130)
  t140 = -t115 / 0.3e1
  t147 = f.my_piecewise3(t42, 0, 0.11e2 / 0.3e1 * t50 * t130)
  t153 = -t130
  t156 = f.my_piecewise3(t68, 0, 0.2e1 * t67 * t153)
  d23 = t1 * t10 * t77 + t81 * t82 * t9 * t77 / 0.3e1 + t81 * t89 * t77 * params.d / 0.3e1 + t95 * t10 * (t100 - t120 + t121 * t52 / 0.32e2 + t30 * t124 * t37 * t51 / 0.32e2 + t30 * t38 * t133 / 0.32e2 + t121 * t62 / 0.576e3 + t30 * t140 * t37 * t61 / 0.576e3 + t30 * t56 * t147 / 0.576e3 - t29 * (0.2e1 / 0.3e1 * t37 * t133 - t156 * t37 * t51 / 0.4e1 - t71 * t133 / 0.4e1) / 0.8e1)
  t174 = t102 * params.a * params.b
  d24 = 0.10e2 / 0.3e1 * t14 * params.a * params.b * t10 * t27 - 0.2e1 / 0.3e1 * t174 * t82 * t9 * t27 - 0.2e1 / 0.3e1 * t174 * t89 * t27 * params.d - 0.2e1 * t110 * params.a * params.b * t10 * t119
  t188 = r1 ** 2
  t189 = r1 ** (0.1e1 / 0.3e1)
  t190 = t189 ** 2
  t192 = 0.1e1 / t190 / t188
  t193 = t32 * t192
  t194 = t67 ** (0.1e1 / 0.3e1)
  t195 = t194 ** 2
  t196 = t195 * t69
  t197 = f.my_piecewise3(t68, t46, t196)
  t198 = t193 * t197
  t201 = t55 * t192
  t204 = f.my_piecewise3(t68, t58, t195 * t69 * t67)
  t205 = t201 * t204
  t210 = f.my_piecewise3(t42, t43, t47)
  t211 = t210 * t192
  t217 = -t28 + t30 * t198 / 0.32e2 + t30 * t205 / 0.576e3 - t29 * (0.2e1 / 0.3e1 * t192 * t197 - t211 * t197 / 0.4e1) / 0.8e1
  t236 = 0.1e1 / t190 / t188 / r1
  t244 = f.my_piecewise3(t68, 0, 0.8e1 / 0.3e1 * t195 * t67 * t153)
  t260 = f.my_piecewise3(t68, 0, 0.11e2 / 0.3e1 * t196 * t153)
  t270 = f.my_piecewise3(t42, 0, 0.2e1 * t41 * t130)
  t282 = t100 - t120 + t121 * t198 / 0.32e2 + t30 * t124 * t192 * t197 / 0.32e2 - t30 * t32 * t236 * t197 / 0.12e2 + t30 * t193 * t244 / 0.32e2 + t121 * t205 / 0.576e3 + t30 * t140 * t192 * t204 / 0.576e3 - t30 * t55 * t236 * t204 / 0.216e3 + t30 * t201 * t260 / 0.576e3 - t29 * (-0.16e2 / 0.9e1 * t236 * t197 + 0.2e1 / 0.3e1 * t192 * t244 - t270 * t192 * t197 / 0.4e1 + 0.2e1 / 0.3e1 * t210 * t236 * t197 - t211 * t244 / 0.4e1) / 0.8e1
  d25 = t1 * t10 * t217 + t81 * t82 * t9 * t217 / 0.3e1 + t81 * t89 * t217 * params.d / 0.3e1 + t95 * t10 * t282
  d33 = 0.0e0
  d34 = 0.0e0
  d35 = 0.0e0
  d44 = 0.0e0
  d45 = 0.0e0
  d55 = 0.0e0
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
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
  t2 = t1 ** 2
  t3 = 0.1e1 / t2
  t5 = r0 - r1
  t6 = t2 * t1
  t7 = 0.1e1 / t6
  t8 = t5 * t7
  t10 = t5 ** 2
  t11 = t2 ** 2
  t12 = 0.1e1 / t11
  t15 = -0.6e1 * t10 * t12 - 0.2e1 * t3 + 0.8e1 * t8
  t16 = t1 ** (0.1e1 / 0.3e1)
  t17 = 0.1e1 / t16
  t19 = params.d * t17 + 0.1e1
  t20 = 0.1e1 / t19
  t22 = t5 * t3
  t25 = 0.2e1 * t10 * t7 - 0.2e1 * t22
  t26 = t19 ** 2
  t27 = 0.1e1 / t26
  t28 = t25 * t27
  t30 = 0.1e1 / t16 / t1
  t31 = params.d * t30
  t35 = -t10 * t3 + 0.1e1
  t37 = 0.1e1 / t26 / t19
  t38 = t35 * t37
  t39 = params.d ** 2
  t40 = t16 ** 2
  t42 = 0.1e1 / t40 / t2
  t43 = t39 * t42
  t46 = t35 * t27
  t48 = 0.1e1 / t16 / t2
  t49 = params.d * t48
  t52 = params.b * params.c
  t53 = t52 * t48
  t55 = jnp.exp(-params.c * t17)
  t56 = t55 * t20
  t58 = s0 + 0.2e1 * s1 + s2
  t59 = t58 * t42
  t61 = params.d * t20 + params.c
  t62 = t61 * t17
  t64 = 0.47e2 - 0.7e1 * t62
  t67 = t35 * t64 / 0.72e2 - 0.2e1 / 0.3e1
  t69 = 3 ** (0.1e1 / 0.3e1)
  t70 = t69 ** 2
  t71 = jnp.pi ** 2
  t72 = t71 ** (0.1e1 / 0.3e1)
  t73 = t72 ** 2
  t74 = t70 * t73
  t75 = 0.1e1 / t1
  t76 = t5 * t75
  t77 = 0.1e1 + t76
  t78 = t77 <= f.p.zeta_threshold
  t79 = f.p.zeta_threshold ** 2
  t80 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t81 = t80 ** 2
  t82 = t81 * t79
  t83 = t77 ** 2
  t84 = t77 ** (0.1e1 / 0.3e1)
  t85 = t84 ** 2
  t86 = t85 * t83
  t87 = f.my_piecewise3(t78, t82, t86)
  t88 = 0.1e1 - t76
  t89 = t88 <= f.p.zeta_threshold
  t90 = t88 ** 2
  t91 = t88 ** (0.1e1 / 0.3e1)
  t92 = t91 ** 2
  t93 = t92 * t90
  t94 = f.my_piecewise3(t89, t82, t93)
  t95 = t87 + t94
  t99 = 2 ** (0.1e1 / 0.3e1)
  t100 = t99 * t35
  t102 = 0.5e1 / 0.2e1 - t62 / 0.18e2
  t103 = r0 ** 2
  t104 = r0 ** (0.1e1 / 0.3e1)
  t105 = t104 ** 2
  t107 = 0.1e1 / t105 / t103
  t108 = s0 * t107
  t109 = t108 * t87
  t110 = r1 ** 2
  t111 = r1 ** (0.1e1 / 0.3e1)
  t112 = t111 ** 2
  t114 = 0.1e1 / t112 / t110
  t115 = s2 * t114
  t116 = t115 * t94
  t117 = t109 + t116
  t118 = t102 * t117
  t121 = t62 - 0.11e2
  t123 = t81 * t79 * f.p.zeta_threshold
  t126 = f.my_piecewise3(t78, t123, t85 * t83 * t77)
  t130 = f.my_piecewise3(t89, t123, t92 * t90 * t88)
  t132 = t108 * t126 + t115 * t130
  t133 = t121 * t132
  t138 = f.my_piecewise3(t78, t79, t83)
  t139 = t138 * s2
  t140 = t114 * t94
  t143 = f.my_piecewise3(t89, t79, t90)
  t144 = t143 * s0
  t145 = t107 * t87
  t151 = -t59 * t67 - 0.3e1 / 0.20e2 * t74 * t35 * t95 + t100 * t118 / 0.32e2 + t100 * t133 / 0.576e3 - t99 * (0.2e1 / 0.3e1 * t109 + 0.2e1 / 0.3e1 * t116 - t139 * t140 / 0.4e1 - t144 * t145 / 0.4e1) / 0.8e1
  t152 = t56 * t151
  t155 = params.c ** 2
  t156 = params.b * t155
  t157 = t156 * t42
  t160 = t52 * t42
  t161 = t55 * t27
  t162 = t151 * params.d
  t163 = t161 * t162
  t166 = t52 * t30
  t168 = 0.1e1 / t40 / t6
  t169 = t58 * t168
  t173 = t39 * t27
  t178 = -t173 / t40 / t1 + t61 * t30
  t179 = 0.7e1 / 0.3e1 * t178
  t182 = t35 * t179 / 0.72e2 + t25 * t64 / 0.72e2
  t187 = t85 * t77
  t188 = t75 - t22
  t189 = t187 * t188
  t191 = f.my_piecewise3(t78, 0, 0.8e1 / 0.3e1 * t189)
  t192 = t92 * t88
  t193 = -t188
  t194 = t192 * t193
  t196 = f.my_piecewise3(t89, 0, 0.8e1 / 0.3e1 * t194)
  t197 = t191 + t196
  t201 = t99 * t25
  t204 = t178 / 0.54e2
  t205 = t204 * t117
  t210 = 0.1e1 / t105 / t103 / r0
  t211 = s0 * t210
  t212 = t211 * t87
  t214 = t108 * t191
  t215 = t115 * t196
  t216 = -0.8e1 / 0.3e1 * t212 + t214 + t215
  t217 = t102 * t216
  t223 = -t178 / 0.3e1
  t224 = t223 * t132
  t231 = f.my_piecewise3(t78, 0, 0.11e2 / 0.3e1 * t86 * t188)
  t235 = f.my_piecewise3(t89, 0, 0.11e2 / 0.3e1 * t93 * t193)
  t237 = -0.8e1 / 0.3e1 * t211 * t126 + t108 * t231 + t115 * t235
  t238 = t121 * t237
  t246 = f.my_piecewise3(t78, 0, 0.2e1 * t77 * t188)
  t247 = t246 * s2
  t250 = t114 * t196
  t255 = f.my_piecewise3(t89, 0, 0.2e1 * t88 * t193)
  t256 = t255 * s0
  t259 = t210 * t87
  t262 = t107 * t191
  t268 = 0.8e1 / 0.3e1 * t169 * t67 - t59 * t182 - 0.3e1 / 0.20e2 * t74 * t25 * t95 - 0.3e1 / 0.20e2 * t74 * t35 * t197 + t201 * t118 / 0.32e2 + t100 * t205 / 0.32e2 + t100 * t217 / 0.32e2 + t201 * t133 / 0.576e3 + t100 * t224 / 0.576e3 + t100 * t238 / 0.576e3 - t99 * (-0.16e2 / 0.9e1 * t212 + 0.2e1 / 0.3e1 * t214 + 0.2e1 / 0.3e1 * t215 - t247 * t140 / 0.4e1 - t139 * t250 / 0.4e1 - t256 * t145 / 0.4e1 + 0.2e1 / 0.3e1 * t144 * t259 - t144 * t262 / 0.4e1) / 0.8e1
  t269 = t56 * t268
  t272 = params.b * t55
  t273 = t272 * t37
  t274 = t151 * t39
  t278 = t272 * t27
  t279 = t268 * params.d
  t286 = t103 ** 2
  t288 = 0.1e1 / t105 / t286
  t289 = s0 * t288
  t290 = t289 * t87
  t292 = t211 * t191
  t294 = t188 ** 2
  t298 = -0.2e1 * t3 + 0.2e1 * t8
  t302 = f.my_piecewise3(t78, 0, 0.40e2 / 0.9e1 * t85 * t294 + 0.8e1 / 0.3e1 * t187 * t298)
  t303 = t108 * t302
  t305 = t193 ** 2
  t308 = -t298
  t312 = f.my_piecewise3(t89, 0, 0.40e2 / 0.9e1 * t92 * t305 + 0.8e1 / 0.3e1 * t192 * t308)
  t313 = t115 * t312
  t318 = f.my_piecewise3(t78, 0, 0.2e1 * t77 * t298 + 0.2e1 * t294)
  t319 = t318 * s2
  t324 = t114 * t312
  t330 = f.my_piecewise3(t89, 0, 0.2e1 * t88 * t308 + 0.2e1 * t305)
  t331 = t330 * s0
  t338 = t288 * t87
  t341 = t210 * t191
  t344 = t107 * t302
  t347 = 0.176e3 / 0.27e2 * t290 - 0.32e2 / 0.9e1 * t292 + 0.2e1 / 0.3e1 * t303 + 0.2e1 / 0.3e1 * t313 - t319 * t140 / 0.4e1 - t247 * t250 / 0.2e1 - t139 * t324 / 0.4e1 - t331 * t145 / 0.4e1 + 0.4e1 / 0.3e1 * t256 * t259 - t256 * t262 / 0.2e1 - 0.22e2 / 0.9e1 * t144 * t338 + 0.4e1 / 0.3e1 * t144 * t341 - t144 * t344 / 0.4e1
  t352 = t58 / t40 / t11
  t361 = t302 + t312
  t365 = t99 * t15
  t372 = t39 * params.d
  t373 = t372 * t37
  t374 = t373 * t7
  t376 = t173 * t42
  t378 = t61 * t48
  t380 = -t374 / 0.81e2 + t376 / 0.27e2 - 0.2e1 / 0.81e2 * t378
  t381 = t380 * t117
  t384 = t204 * t216
  t389 = 0.88e2 / 0.9e1 * t290 - 0.16e2 / 0.3e1 * t292 + t303 + t313
  t390 = t102 * t389
  t402 = 0.2e1 / 0.9e1 * t374 - 0.2e1 / 0.3e1 * t376 + 0.4e1 / 0.9e1 * t378
  t403 = t402 * t132
  t406 = t223 * t237
  t418 = f.my_piecewise3(t78, 0, 0.88e2 / 0.9e1 * t187 * t294 + 0.11e2 / 0.3e1 * t86 * t298)
  t425 = f.my_piecewise3(t89, 0, 0.88e2 / 0.9e1 * t192 * t305 + 0.11e2 / 0.3e1 * t93 * t308)
  t427 = 0.88e2 / 0.9e1 * t289 * t126 - 0.16e2 / 0.3e1 * t211 * t231 + t108 * t418 + t115 * t425
  t428 = t121 * t427
  t440 = -0.14e2 / 0.9e1 * t374 + 0.14e2 / 0.3e1 * t376 - 0.28e2 / 0.9e1 * t378
  t443 = t15 * t64 / 0.72e2 + t25 * t179 / 0.36e2 + t35 * t440 / 0.72e2
  t445 = -t99 * t347 / 0.8e1 - 0.88e2 / 0.9e1 * t352 * t67 - 0.3e1 / 0.20e2 * t74 * t15 * t95 - 0.3e1 / 0.10e2 * t74 * t25 * t197 - 0.3e1 / 0.20e2 * t74 * t35 * t361 + t365 * t118 / 0.32e2 + t201 * t205 / 0.16e2 + t201 * t217 / 0.16e2 + t100 * t381 / 0.32e2 + t100 * t384 / 0.16e2 + t100 * t390 / 0.32e2 + t365 * t133 / 0.576e3 + t201 * t224 / 0.288e3 + t201 * t238 / 0.288e3 + t100 * t403 / 0.576e3 + t100 * t406 / 0.288e3 + t100 * t428 / 0.576e3 + 0.16e2 / 0.3e1 * t169 * t182 - t59 * t443
  t448 = -t15 * t20 - 0.2e1 / 0.3e1 * t28 * t31 - 0.2e1 / 0.9e1 * t38 * t43 + 0.4e1 / 0.9e1 * t46 * t49 - 0.4e1 / 0.9e1 * t53 * t152 + t157 * t152 / 0.9e1 + 0.2e1 / 0.9e1 * t160 * t163 + 0.2e1 / 0.3e1 * t166 * t269 + 0.2e1 / 0.9e1 * t273 * t274 * t42 + 0.2e1 / 0.3e1 * t278 * t279 * t30 - 0.4e1 / 0.9e1 * t278 * t162 * t48 + t272 * t20 * t445
  t458 = 0.1e1 / t16 / t6
  t463 = t5 * t12
  t465 = t11 * t1
  t469 = 0.12e2 * t7 - 0.36e2 * t463 + 0.24e2 * t10 / t465
  t497 = 0.4e1 / 0.3e1 * t28 * t49 + 0.8e1 / 0.9e1 * t38 * t39 * t168 - 0.28e2 / 0.27e2 * t46 * params.d * t458 - t469 * t20 - 0.8e1 / 0.9e1 * t273 * t274 * t168 - 0.4e1 / 0.3e1 * t278 * t279 * t48 + 0.28e2 / 0.27e2 * t278 * t162 * t458 + 0.28e2 / 0.27e2 * t52 * t458 * t152 - 0.8e1 / 0.9e1 * t52 * t168 * t163 + t156 * t12 * t163 / 0.9e1 + 0.2e1 / 0.3e1 * t160 * t161 * t279 + 0.2e1 / 0.9e1 * t52 * t12 * t55 * t37 * t274
  t503 = t26 ** 2
  t504 = 0.1e1 / t503
  t515 = 0.1e1 / t105 / t286 / r0
  t519 = t289 * t191
  t521 = t211 * t302
  t524 = t294 * t188
  t531 = 0.6e1 * t7 - 0.6e1 * t463
  t535 = f.my_piecewise3(t78, 0, 0.80e2 / 0.27e2 / t84 * t524 + 0.40e2 / 0.3e1 * t85 * t188 * t298 + 0.8e1 / 0.3e1 * t187 * t531)
  t536 = t108 * t535
  t539 = t305 * t193
  t545 = -t531
  t549 = f.my_piecewise3(t89, 0, 0.80e2 / 0.27e2 / t91 * t539 + 0.40e2 / 0.3e1 * t92 * t193 * t308 + 0.8e1 / 0.3e1 * t192 * t545)
  t550 = t115 * t549
  t552 = s0 * t515
  t553 = t552 * t87
  t560 = f.my_piecewise3(t78, 0, 0.6e1 * t188 * t298 + 0.2e1 * t77 * t531)
  t576 = f.my_piecewise3(t89, 0, 0.6e1 * t193 * t308 + 0.2e1 * t88 * t545)
  t595 = 0.2e1 * t331 * t259 - 0.22e2 / 0.3e1 * t256 * t338 + 0.308e3 / 0.27e2 * t144 * t515 * t87 + 0.176e3 / 0.9e1 * t519 - 0.16e2 / 0.3e1 * t521 + 0.2e1 / 0.3e1 * t536 + 0.2e1 / 0.3e1 * t550 - 0.2464e4 / 0.81e2 * t553 - t560 * s2 * t140 / 0.4e1 - 0.3e1 / 0.4e1 * t319 * t250 - 0.3e1 / 0.4e1 * t247 * t324 - t139 * t114 * t549 / 0.4e1 - t576 * s0 * t145 / 0.4e1 - 0.3e1 / 0.4e1 * t331 * t262 + 0.4e1 * t256 * t341 - 0.3e1 / 0.4e1 * t256 * t344 - 0.22e2 / 0.3e1 * t144 * t288 * t191 + 0.2e1 * t144 * t210 * t302 - t144 * t107 * t535 / 0.4e1
  t611 = f.my_piecewise3(t78, 0, 0.440e3 / 0.27e2 * t85 * t524 + 0.88e2 / 0.3e1 * t189 * t298 + 0.11e2 / 0.3e1 * t86 * t531)
  t620 = f.my_piecewise3(t89, 0, 0.440e3 / 0.27e2 * t92 * t539 + 0.88e2 / 0.3e1 * t194 * t308 + 0.11e2 / 0.3e1 * t93 * t545)
  t639 = t99 * t469
  t652 = t39 ** 2
  t656 = t652 * t504 / t16 / t11
  t658 = t373 * t12
  t660 = t173 * t168
  t662 = t61 * t458
  t671 = -t99 * t595 / 0.8e1 + t100 * t121 * (-0.1232e4 / 0.27e2 * t552 * t126 + 0.88e2 / 0.3e1 * t289 * t231 - 0.8e1 * t211 * t418 + t108 * t611 + t115 * t620) / 0.576e3 - 0.3e1 / 0.20e2 * t74 * t469 * t95 - 0.9e1 / 0.20e2 * t74 * t15 * t197 - 0.9e1 / 0.20e2 * t74 * t25 * t361 - 0.3e1 / 0.20e2 * t74 * t35 * (t535 + t549) + t639 * t118 / 0.32e2 + 0.3e1 / 0.32e2 * t365 * t205 + 0.3e1 / 0.32e2 * t365 * t217 + 0.3e1 / 0.32e2 * t201 * t381 + 0.3e1 / 0.16e2 * t201 * t384 + 0.3e1 / 0.32e2 * t201 * t390 + t100 * (-t656 / 0.81e2 + 0.5e1 / 0.81e2 * t658 - 0.26e2 / 0.243e3 * t660 + 0.14e2 / 0.243e3 * t662) * t117 / 0.32e2 + 0.3e1 / 0.32e2 * t100 * t380 * t216
  t732 = 0.3e1 / 0.32e2 * t100 * t204 * t389 + t100 * t102 * (-0.1232e4 / 0.27e2 * t553 + 0.88e2 / 0.3e1 * t519 - 0.8e1 * t521 + t536 + t550) / 0.32e2 + t639 * t133 / 0.576e3 + t365 * t224 / 0.192e3 + t365 * t238 / 0.192e3 + t201 * t403 / 0.192e3 + t201 * t406 / 0.96e2 + t201 * t428 / 0.192e3 + t100 * (0.2e1 / 0.9e1 * t656 - 0.10e2 / 0.9e1 * t658 + 0.52e2 / 0.27e2 * t660 - 0.28e2 / 0.27e2 * t662) * t132 / 0.576e3 + t100 * t402 * t237 / 0.192e3 + t100 * t223 * t427 / 0.192e3 - t59 * (t469 * t64 / 0.72e2 + t15 * t179 / 0.24e2 + t25 * t440 / 0.24e2 + t35 * (-0.14e2 / 0.9e1 * t656 + 0.70e2 / 0.9e1 * t658 - 0.364e3 / 0.27e2 * t660 + 0.196e3 / 0.27e2 * t662) / 0.72e2) - 0.88e2 / 0.3e1 * t352 * t182 + 0.8e1 * t169 * t443 + 0.1232e4 / 0.27e2 * t58 / t40 / t465 * t67
  t762 = -t15 * t27 * t31 - 0.2e1 / 0.3e1 * t25 * t37 * t43 - 0.2e1 / 0.9e1 * t35 * t504 * t372 * t12 + t272 * t20 * (t671 + t732) - 0.4e1 / 0.3e1 * t53 * t269 - 0.4e1 / 0.9e1 * t156 * t168 * t152 + t157 * t269 / 0.3e1 + params.b * t155 * params.c * t12 * t152 / 0.27e2 + t166 * t56 * t445 + 0.2e1 / 0.3e1 * t273 * t268 * t39 * t42 + 0.2e1 / 0.9e1 * t272 * t504 * t151 * t372 * t12 + t278 * t445 * params.d * t30
  d111 = 0.3e1 * params.a * t448 + t1 * params.a * (t497 + t762)

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

  t1 = r0 - r1
  t2 = r0 + r1
  t3 = t2 ** 2
  t4 = 0.1e1 / t3
  t5 = t1 * t4
  t6 = t1 ** 2
  t7 = t3 * t2
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * t6 * t8 - 0.2e1 * t5
  t12 = t2 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / t12
  t15 = params.d * t13 + 0.1e1
  t16 = t15 ** 2
  t17 = 0.1e1 / t16
  t18 = t11 * t17
  t20 = 0.1e1 / t12 / t3
  t21 = params.d * t20
  t25 = -t6 * t4 + 0.1e1
  t27 = 0.1e1 / t16 / t15
  t28 = t25 * t27
  t29 = params.d ** 2
  t30 = t12 ** 2
  t32 = 0.1e1 / t30 / t7
  t33 = t29 * t32
  t36 = t25 * t17
  t38 = 0.1e1 / t12 / t7
  t39 = params.d * t38
  t43 = t3 ** 2
  t44 = 0.1e1 / t43
  t45 = t1 * t44
  t47 = t43 * t2
  t48 = 0.1e1 / t47
  t51 = 0.24e2 * t6 * t48 - 0.36e2 * t45 + 0.12e2 * t8
  t52 = 0.1e1 / t15
  t55 = jnp.exp(-params.c * t13)
  t56 = params.b * t55
  t57 = t56 * t27
  t59 = s0 + 0.2e1 * s1 + s2
  t61 = 0.1e1 / t30 / t3
  t62 = t59 * t61
  t64 = params.d * t52 + params.c
  t65 = t64 * t13
  t67 = 0.47e2 - 0.7e1 * t65
  t70 = t25 * t67 / 0.72e2 - 0.2e1 / 0.3e1
  t72 = 3 ** (0.1e1 / 0.3e1)
  t73 = t72 ** 2
  t74 = jnp.pi ** 2
  t75 = t74 ** (0.1e1 / 0.3e1)
  t76 = t75 ** 2
  t77 = t73 * t76
  t78 = 0.1e1 / t2
  t79 = t1 * t78
  t80 = 0.1e1 + t79
  t81 = t80 <= f.p.zeta_threshold
  t82 = f.p.zeta_threshold ** 2
  t83 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t84 = t83 ** 2
  t85 = t84 * t82
  t86 = t80 ** 2
  t87 = t80 ** (0.1e1 / 0.3e1)
  t88 = t87 ** 2
  t89 = t88 * t86
  t90 = f.my_piecewise3(t81, t85, t89)
  t91 = 0.1e1 - t79
  t92 = t91 <= f.p.zeta_threshold
  t93 = t91 ** 2
  t94 = t91 ** (0.1e1 / 0.3e1)
  t95 = t94 ** 2
  t96 = t95 * t93
  t97 = f.my_piecewise3(t92, t85, t96)
  t98 = t90 + t97
  t102 = 2 ** (0.1e1 / 0.3e1)
  t103 = t102 * t25
  t105 = 0.5e1 / 0.2e1 - t65 / 0.18e2
  t106 = r0 ** 2
  t107 = r0 ** (0.1e1 / 0.3e1)
  t108 = t107 ** 2
  t110 = 0.1e1 / t108 / t106
  t111 = s0 * t110
  t112 = t111 * t90
  t113 = r1 ** 2
  t114 = r1 ** (0.1e1 / 0.3e1)
  t115 = t114 ** 2
  t117 = 0.1e1 / t115 / t113
  t118 = s2 * t117
  t119 = t118 * t97
  t120 = t112 + t119
  t121 = t105 * t120
  t124 = t65 - 0.11e2
  t126 = t84 * t82 * f.p.zeta_threshold
  t129 = f.my_piecewise3(t81, t126, t88 * t86 * t80)
  t133 = f.my_piecewise3(t92, t126, t95 * t93 * t91)
  t135 = t111 * t129 + t118 * t133
  t136 = t124 * t135
  t141 = f.my_piecewise3(t81, t82, t86)
  t142 = t141 * s2
  t143 = t117 * t97
  t146 = f.my_piecewise3(t92, t82, t93)
  t147 = t146 * s0
  t148 = t110 * t90
  t154 = -t62 * t70 - 0.3e1 / 0.20e2 * t77 * t25 * t98 + t103 * t121 / 0.32e2 + t103 * t136 / 0.576e3 - t102 * (0.2e1 / 0.3e1 * t112 + 0.2e1 / 0.3e1 * t119 - t142 * t143 / 0.4e1 - t147 * t148 / 0.4e1) / 0.8e1
  t155 = t154 * t29
  t159 = t56 * t17
  t160 = t59 * t32
  t164 = t29 * t17
  t169 = 0.1e1 / t12 / t2
  t171 = -t164 / t30 / t2 + t64 * t169
  t172 = 0.7e1 / 0.3e1 * t171
  t175 = t11 * t67 / 0.72e2 + t25 * t172 / 0.72e2
  t180 = t88 * t80
  t181 = t78 - t5
  t182 = t180 * t181
  t184 = f.my_piecewise3(t81, 0, 0.8e1 / 0.3e1 * t182)
  t185 = t95 * t91
  t186 = -t181
  t187 = t185 * t186
  t189 = f.my_piecewise3(t92, 0, 0.8e1 / 0.3e1 * t187)
  t190 = t184 + t189
  t194 = t102 * t11
  t197 = t171 / 0.54e2
  t198 = t197 * t120
  t203 = 0.1e1 / t108 / t106 / r0
  t204 = s0 * t203
  t205 = t204 * t90
  t207 = t111 * t184
  t208 = t118 * t189
  t209 = -0.8e1 / 0.3e1 * t205 + t207 + t208
  t210 = t105 * t209
  t216 = -t171 / 0.3e1
  t217 = t216 * t135
  t224 = f.my_piecewise3(t81, 0, 0.11e2 / 0.3e1 * t89 * t181)
  t228 = f.my_piecewise3(t92, 0, 0.11e2 / 0.3e1 * t96 * t186)
  t230 = -0.8e1 / 0.3e1 * t204 * t129 + t111 * t224 + t118 * t228
  t231 = t124 * t230
  t239 = f.my_piecewise3(t81, 0, 0.2e1 * t80 * t181)
  t240 = t239 * s2
  t243 = t117 * t189
  t248 = f.my_piecewise3(t92, 0, 0.2e1 * t91 * t186)
  t249 = t248 * s0
  t252 = t203 * t90
  t255 = t110 * t184
  t261 = 0.8e1 / 0.3e1 * t160 * t70 - t62 * t175 - 0.3e1 / 0.20e2 * t77 * t11 * t98 - 0.3e1 / 0.20e2 * t77 * t25 * t190 + t194 * t121 / 0.32e2 + t103 * t198 / 0.32e2 + t103 * t210 / 0.32e2 + t194 * t136 / 0.576e3 + t103 * t217 / 0.576e3 + t103 * t231 / 0.576e3 - t102 * (-0.16e2 / 0.9e1 * t205 + 0.2e1 / 0.3e1 * t207 + 0.2e1 / 0.3e1 * t208 - t240 * t143 / 0.4e1 - t142 * t243 / 0.4e1 - t249 * t148 / 0.4e1 + 0.2e1 / 0.3e1 * t147 * t252 - t147 * t255 / 0.4e1) / 0.8e1
  t262 = t261 * params.d
  t266 = t154 * params.d
  t270 = params.b * params.c
  t271 = t270 * t38
  t272 = t55 * t52
  t273 = t272 * t154
  t276 = t270 * t32
  t277 = t55 * t17
  t278 = t277 * t266
  t281 = params.c ** 2
  t282 = params.b * t281
  t283 = t282 * t44
  t286 = t270 * t61
  t287 = t277 * t262
  t290 = t270 * t44
  t291 = t55 * t27
  t292 = t291 * t155
  t295 = 0.4e1 / 0.3e1 * t18 * t21 + 0.8e1 / 0.9e1 * t28 * t33 - 0.28e2 / 0.27e2 * t36 * t39 - t51 * t52 - 0.8e1 / 0.9e1 * t57 * t155 * t32 - 0.4e1 / 0.3e1 * t159 * t262 * t20 + 0.28e2 / 0.27e2 * t159 * t266 * t38 + 0.28e2 / 0.27e2 * t271 * t273 - 0.8e1 / 0.9e1 * t276 * t278 + t283 * t278 / 0.9e1 + 0.2e1 / 0.3e1 * t286 * t287 + 0.2e1 / 0.9e1 * t290 * t292
  t297 = t1 * t8
  t301 = -0.6e1 * t6 * t44 + 0.8e1 * t297 - 0.2e1 * t4
  t302 = t301 * t17
  t303 = params.d * t169
  t305 = t11 * t27
  t306 = t29 * t61
  t309 = t16 ** 2
  t310 = 0.1e1 / t309
  t311 = t25 * t310
  t312 = t29 * params.d
  t313 = t312 * t44
  t317 = 0.1e1 / t30 / t43
  t318 = t59 * t317
  t322 = 0.1e1 / t30 / t47
  t323 = t59 * t322
  t330 = t312 * t27
  t331 = t330 * t8
  t333 = t164 * t61
  t335 = t64 * t20
  t337 = -0.14e2 / 0.9e1 * t331 + 0.14e2 / 0.3e1 * t333 - 0.28e2 / 0.9e1 * t335
  t340 = t301 * t67 / 0.72e2 + t11 * t172 / 0.36e2 + t25 * t337 / 0.72e2
  t349 = t29 ** 2
  t350 = t349 * t310
  t352 = 0.1e1 / t12 / t43
  t353 = t350 * t352
  t355 = t330 * t44
  t357 = t164 * t32
  t359 = t64 * t38
  t361 = -0.14e2 / 0.9e1 * t353 + 0.70e2 / 0.9e1 * t355 - 0.364e3 / 0.27e2 * t357 + 0.196e3 / 0.27e2 * t359
  t364 = t51 * t67 / 0.72e2 + t301 * t172 / 0.24e2 + t11 * t337 / 0.24e2 + t25 * t361 / 0.72e2
  t366 = t186 ** 2
  t368 = 0.2e1 * t4 - 0.2e1 * t297
  t372 = f.my_piecewise3(t92, 0, 0.2e1 * t91 * t368 + 0.2e1 * t366)
  t373 = t372 * s0
  t376 = t106 ** 2
  t378 = 0.1e1 / t108 / t376
  t379 = t378 * t90
  t384 = 0.1e1 / t108 / t376 / r0
  t385 = t384 * t90
  t388 = s0 * t378
  t389 = t388 * t184
  t391 = t181 ** 2
  t392 = t88 * t391
  t394 = -t368
  t398 = f.my_piecewise3(t81, 0, 0.40e2 / 0.9e1 * t392 + 0.8e1 / 0.3e1 * t180 * t394)
  t399 = t204 * t398
  t401 = 0.1e1 / t87
  t402 = t391 * t181
  t405 = t88 * t181
  t409 = 0.6e1 * t8 - 0.6e1 * t45
  t413 = f.my_piecewise3(t81, 0, 0.80e2 / 0.27e2 * t401 * t402 + 0.40e2 / 0.3e1 * t405 * t394 + 0.8e1 / 0.3e1 * t180 * t409)
  t414 = t111 * t413
  t416 = 0.1e1 / t94
  t417 = t366 * t186
  t420 = t95 * t186
  t423 = -t409
  t427 = f.my_piecewise3(t92, 0, 0.80e2 / 0.27e2 * t416 * t417 + 0.40e2 / 0.3e1 * t420 * t368 + 0.8e1 / 0.3e1 * t185 * t423)
  t428 = t118 * t427
  t430 = s0 * t384
  t431 = t430 * t90
  t438 = f.my_piecewise3(t81, 0, 0.6e1 * t181 * t394 + 0.2e1 * t80 * t409)
  t439 = t438 * s2
  t445 = f.my_piecewise3(t81, 0, 0.2e1 * t80 * t394 + 0.2e1 * t391)
  t446 = t445 * s2
  t449 = t95 * t366
  t454 = f.my_piecewise3(t92, 0, 0.40e2 / 0.9e1 * t449 + 0.8e1 / 0.3e1 * t185 * t368)
  t455 = t117 * t454
  t458 = t117 * t427
  t466 = f.my_piecewise3(t92, 0, 0.6e1 * t186 * t368 + 0.2e1 * t91 * t423)
  t467 = t466 * s0
  t472 = t203 * t184
  t475 = t110 * t398
  t478 = t378 * t184
  t481 = t203 * t398
  t484 = t110 * t413
  t487 = 0.2e1 * t373 * t252 - 0.22e2 / 0.3e1 * t249 * t379 + 0.308e3 / 0.27e2 * t147 * t385 + 0.176e3 / 0.9e1 * t389 - 0.16e2 / 0.3e1 * t399 + 0.2e1 / 0.3e1 * t414 + 0.2e1 / 0.3e1 * t428 - 0.2464e4 / 0.81e2 * t431 - t439 * t143 / 0.4e1 - 0.3e1 / 0.4e1 * t446 * t243 - 0.3e1 / 0.4e1 * t240 * t455 - t142 * t458 / 0.4e1 - t467 * t148 / 0.4e1 - 0.3e1 / 0.4e1 * t373 * t255 + 0.4e1 * t249 * t472 - 0.3e1 / 0.4e1 * t249 * t475 - 0.22e2 / 0.3e1 * t147 * t478 + 0.2e1 * t147 * t481 - t147 * t484 / 0.4e1
  t490 = t398 + t454
  t494 = t413 + t427
  t498 = t102 * t51
  t501 = t102 * t301
  t509 = -t331 / 0.81e2 + t333 / 0.27e2 - 0.2e1 / 0.81e2 * t335
  t510 = t509 * t120
  t513 = t197 * t209
  t516 = t388 * t90
  t518 = t204 * t184
  t520 = t111 * t398
  t521 = t118 * t454
  t522 = 0.88e2 / 0.9e1 * t516 - 0.16e2 / 0.3e1 * t518 + t520 + t521
  t523 = t105 * t522
  t530 = -t353 / 0.81e2 + 0.5e1 / 0.81e2 * t355 - 0.26e2 / 0.243e3 * t357 + 0.14e2 / 0.243e3 * t359
  t531 = t530 * t120
  t534 = -0.88e2 / 0.3e1 * t318 * t175 + 0.1232e4 / 0.27e2 * t323 * t70 + 0.8e1 * t160 * t340 - t62 * t364 - t102 * t487 / 0.8e1 - 0.9e1 / 0.20e2 * t77 * t11 * t490 - 0.3e1 / 0.20e2 * t77 * t25 * t494 + t498 * t121 / 0.32e2 + 0.3e1 / 0.32e2 * t501 * t198 + 0.3e1 / 0.32e2 * t501 * t210 + 0.3e1 / 0.32e2 * t194 * t510 + 0.3e1 / 0.16e2 * t194 * t513 + 0.3e1 / 0.32e2 * t194 * t523 + t103 * t531 / 0.32e2
  t535 = t509 * t209
  t538 = t197 * t522
  t544 = -0.1232e4 / 0.27e2 * t431 + 0.88e2 / 0.3e1 * t389 - 0.8e1 * t399 + t414 + t428
  t545 = t105 * t544
  t557 = 0.2e1 / 0.9e1 * t331 - 0.2e1 / 0.3e1 * t333 + 0.4e1 / 0.9e1 * t335
  t558 = t557 * t135
  t561 = t216 * t230
  t573 = f.my_piecewise3(t81, 0, 0.88e2 / 0.9e1 * t180 * t391 + 0.11e2 / 0.3e1 * t89 * t394)
  t580 = f.my_piecewise3(t92, 0, 0.88e2 / 0.9e1 * t185 * t366 + 0.11e2 / 0.3e1 * t96 * t368)
  t582 = 0.88e2 / 0.9e1 * t388 * t129 - 0.16e2 / 0.3e1 * t204 * t224 + t111 * t573 + t118 * t580
  t583 = t124 * t582
  t590 = 0.2e1 / 0.9e1 * t353 - 0.10e2 / 0.9e1 * t355 + 0.52e2 / 0.27e2 * t357 - 0.28e2 / 0.27e2 * t359
  t591 = t590 * t135
  t594 = t557 * t230
  t597 = t216 * t582
  t613 = f.my_piecewise3(t81, 0, 0.440e3 / 0.27e2 * t88 * t402 + 0.88e2 / 0.3e1 * t182 * t394 + 0.11e2 / 0.3e1 * t89 * t409)
  t622 = f.my_piecewise3(t92, 0, 0.440e3 / 0.27e2 * t95 * t417 + 0.88e2 / 0.3e1 * t187 * t368 + 0.11e2 / 0.3e1 * t96 * t423)
  t624 = -0.1232e4 / 0.27e2 * t430 * t129 + 0.88e2 / 0.3e1 * t388 * t224 - 0.8e1 * t204 * t573 + t111 * t613 + t118 * t622
  t625 = t124 * t624
  t634 = 0.3e1 / 0.32e2 * t103 * t535 + 0.3e1 / 0.32e2 * t103 * t538 + t103 * t545 / 0.32e2 + t498 * t136 / 0.576e3 + t501 * t217 / 0.192e3 + t501 * t231 / 0.192e3 + t194 * t558 / 0.192e3 + t194 * t561 / 0.96e2 + t194 * t583 / 0.192e3 + t103 * t591 / 0.576e3 + t103 * t594 / 0.192e3 + t103 * t597 / 0.192e3 + t103 * t625 / 0.576e3 - 0.3e1 / 0.20e2 * t77 * t51 * t98 - 0.9e1 / 0.20e2 * t77 * t301 * t190
  t635 = t534 + t634
  t638 = t270 * t20
  t639 = t272 * t261
  t642 = t282 * t32
  t645 = t282 * t61
  t649 = params.b * t281 * params.c
  t650 = t649 * t44
  t653 = t270 * t169
  t676 = 0.176e3 / 0.27e2 * t516 - 0.32e2 / 0.9e1 * t518 + 0.2e1 / 0.3e1 * t520 + 0.2e1 / 0.3e1 * t521 - t446 * t143 / 0.4e1 - t240 * t243 / 0.2e1 - t142 * t455 / 0.4e1 - t373 * t148 / 0.4e1 + 0.4e1 / 0.3e1 * t249 * t252 - t249 * t255 / 0.2e1 - 0.22e2 / 0.9e1 * t147 * t379 + 0.4e1 / 0.3e1 * t147 * t472 - t147 * t475 / 0.4e1
  t717 = -t102 * t676 / 0.8e1 - 0.88e2 / 0.9e1 * t318 * t70 - 0.3e1 / 0.20e2 * t77 * t301 * t98 - 0.3e1 / 0.10e2 * t77 * t11 * t190 - 0.3e1 / 0.20e2 * t77 * t25 * t490 + t501 * t121 / 0.32e2 + t194 * t198 / 0.16e2 + t194 * t210 / 0.16e2 + t103 * t510 / 0.32e2 + t103 * t513 / 0.16e2 + t103 * t523 / 0.32e2 + t501 * t136 / 0.576e3 + t194 * t217 / 0.288e3 + t194 * t231 / 0.288e3 + t103 * t558 / 0.576e3 + t103 * t561 / 0.288e3 + t103 * t583 / 0.576e3 + 0.16e2 / 0.3e1 * t160 * t175 - t62 * t340
  t718 = t272 * t717
  t720 = t261 * t29
  t724 = t56 * t310
  t725 = t154 * t312
  t729 = t717 * params.d
  t732 = -t302 * t303 - 0.2e1 / 0.3e1 * t305 * t306 - 0.2e1 / 0.9e1 * t311 * t313 + t56 * t52 * t635 - 0.4e1 / 0.3e1 * t638 * t639 - 0.4e1 / 0.9e1 * t642 * t273 + t645 * t639 / 0.3e1 + t650 * t273 / 0.27e2 + t653 * t718 + 0.2e1 / 0.3e1 * t57 * t720 * t61 + 0.2e1 / 0.9e1 * t724 * t725 * t44 + t159 * t729 * t169
  t744 = 0.1e1 / t309 / t15
  t747 = 0.1e1 / t12 / t47
  t785 = t1 * t48
  t787 = t43 * t3
  t791 = -0.72e2 * t44 + 0.192e3 * t785 - 0.120e3 * t6 / t787
  t806 = t391 ** 2
  t812 = t394 ** 2
  t818 = -0.24e2 * t44 + 0.24e2 * t785
  t822 = f.my_piecewise3(t81, 0, -0.80e2 / 0.81e2 / t87 / t80 * t806 + 0.160e3 / 0.9e1 * t401 * t391 * t394 + 0.40e2 / 0.3e1 * t88 * t812 + 0.160e3 / 0.9e1 * t405 * t409 + 0.8e1 / 0.3e1 * t180 * t818)
  t825 = t366 ** 2
  t831 = t368 ** 2
  t836 = -t818
  t840 = f.my_piecewise3(t92, 0, -0.80e2 / 0.81e2 / t94 / t91 * t825 + 0.160e3 / 0.9e1 * t416 * t366 * t368 + 0.40e2 / 0.3e1 * t95 * t831 + 0.160e3 / 0.9e1 * t420 * t423 + 0.8e1 / 0.3e1 * t185 * t836)
  t845 = t102 * t791
  t864 = t498 * t217 / 0.144e3 + t498 * t231 / 0.144e3 + t501 * t558 / 0.96e2 + t501 * t561 / 0.48e2 + t103 * t590 * t230 / 0.144e3 + t103 * t557 * t582 / 0.96e2 - 0.3e1 / 0.20e2 * t77 * t791 * t98 - 0.3e1 / 0.5e1 * t77 * t51 * t190 - 0.9e1 / 0.10e2 * t77 * t301 * t490 - 0.3e1 / 0.5e1 * t77 * t11 * t494 - 0.3e1 / 0.20e2 * t77 * t25 * (t822 + t840) + t845 * t121 / 0.32e2 + t498 * t198 / 0.8e1 + t498 * t210 / 0.8e1 + 0.3e1 / 0.16e2 * t501 * t510 + 0.3e1 / 0.8e1 * t501 * t513 + 0.3e1 / 0.16e2 * t501 * t523 + t194 * t531 / 0.8e1 + 0.3e1 / 0.8e1 * t194 * t535 + 0.3e1 / 0.8e1 * t194 * t538
  t867 = t349 * params.d * t744 * t322
  t869 = t350 * t747
  t871 = t330 * t48
  t873 = t164 * t317
  t875 = t64 * t352
  t883 = 0.1e1 / t108 / t376 / t106
  t884 = s0 * t883
  t885 = t884 * t90
  t887 = t430 * t184
  t889 = t388 * t398
  t891 = t204 * t413
  t893 = t111 * t822
  t894 = t118 * t840
  t931 = f.my_piecewise3(t81, 0, 0.880e3 / 0.81e2 * t401 * t806 + 0.880e3 / 0.9e1 * t392 * t394 + 0.88e2 / 0.3e1 * t180 * t812 + 0.352e3 / 0.9e1 * t182 * t409 + 0.11e2 / 0.3e1 * t89 * t818)
  t944 = f.my_piecewise3(t92, 0, 0.880e3 / 0.81e2 * t416 * t825 + 0.880e3 / 0.9e1 * t449 * t368 + 0.88e2 / 0.3e1 * t185 * t831 + 0.352e3 / 0.9e1 * t187 * t423 + 0.11e2 / 0.3e1 * t96 * t836)
  t1005 = f.my_piecewise3(t81, 0, 0.8e1 * t181 * t409 + 0.2e1 * t80 * t818 + 0.6e1 * t812)
  t1010 = -t249 * t484 + 0.8e1 / 0.3e1 * t467 * t252 + 0.8e1 * t373 * t472 - 0.88e2 / 0.3e1 * t249 * t478 - 0.44e2 / 0.3e1 * t373 * t379 + 0.1232e4 / 0.27e2 * t249 * t385 - 0.5236e4 / 0.81e2 * t147 * t883 * t90 - 0.44e2 / 0.3e1 * t147 * t378 * t398 + 0.8e1 / 0.3e1 * t147 * t203 * t413 - t147 * t110 * t822 / 0.4e1 + 0.1232e4 / 0.27e2 * t147 * t384 * t184 - t1005 * s2 * t143 / 0.4e1 - t439 * t243
  t1023 = f.my_piecewise3(t92, 0, 0.8e1 * t186 * t423 + 0.2e1 * t91 * t836 + 0.6e1 * t831)
  t1038 = -0.3e1 / 0.2e1 * t446 * t455 - t240 * t458 - t142 * t117 * t840 / 0.4e1 - t1023 * s0 * t148 / 0.4e1 - t467 * t255 - 0.3e1 / 0.2e1 * t373 * t475 + 0.8e1 * t249 * t481 + 0.41888e5 / 0.243e3 * t885 - 0.9856e4 / 0.81e2 * t887 + 0.352e3 / 0.9e1 * t889 - 0.64e2 / 0.9e1 * t891 + 0.2e1 / 0.3e1 * t893 + 0.2e1 / 0.3e1 * t894
  t1071 = t103 * t197 * t544 / 0.8e1 + t103 * t530 * t209 / 0.8e1 + 0.3e1 / 0.16e2 * t103 * t509 * t522 + t103 * (0.8e1 / 0.27e2 * t867 - 0.56e2 / 0.27e2 * t869 + 0.464e3 / 0.81e2 * t871 - 0.200e3 / 0.27e2 * t873 + 0.280e3 / 0.81e2 * t875) * t135 / 0.576e3 + t501 * t583 / 0.96e2 - t102 * (t1010 + t1038) / 0.8e1 - 0.176e3 / 0.3e1 * t318 * t340 + 0.32e2 / 0.3e1 * t160 * t364 + 0.4928e4 / 0.27e2 * t323 * t175 - 0.20944e5 / 0.81e2 * t59 / t30 / t787 * t70 - t62 * (t791 * t67 / 0.72e2 + t51 * t172 / 0.18e2 + t301 * t337 / 0.12e2 + t11 * t361 / 0.18e2 + t25 * (-0.56e2 / 0.27e2 * t867 + 0.392e3 / 0.27e2 * t869 - 0.3248e4 / 0.81e2 * t871 + 0.1400e4 / 0.27e2 * t873 - 0.1960e4 / 0.81e2 * t875) / 0.72e2)
  t1106 = t56 * t52 * (t864 + t103 * (-0.4e1 / 0.243e3 * t867 + 0.28e2 / 0.243e3 * t869 - 0.232e3 / 0.729e3 * t871 + 0.100e3 / 0.243e3 * t873 - 0.140e3 / 0.729e3 * t875) * t120 / 0.32e2 + t103 * t105 * (0.20944e5 / 0.81e2 * t885 - 0.4928e4 / 0.27e2 * t887 + 0.176e3 / 0.3e1 * t889 - 0.32e2 / 0.3e1 * t891 + t893 + t894) / 0.32e2 + t845 * t136 / 0.576e3 + t194 * t591 / 0.144e3 + t194 * t594 / 0.48e2 + t194 * t597 / 0.48e2 + t194 * t625 / 0.144e3 + t103 * t216 * t624 / 0.144e3 + t103 * t124 * (0.20944e5 / 0.81e2 * t884 * t129 - 0.4928e4 / 0.27e2 * t430 * t224 + 0.176e3 / 0.3e1 * t388 * t573 - 0.32e2 / 0.3e1 * t204 * t613 + t111 * t931 + t118 * t944) / 0.576e3 + t194 * t545 / 0.8e1 + t1071) + 0.8e1 / 0.27e2 * t270 * t747 * t55 * t310 * t725 + 0.320e3 / 0.81e2 * t270 * t317 * t278 - 0.8e1 / 0.9e1 * t282 * t48 * t278 + 0.4e1 / 0.9e1 * t283 * t287 + 0.4e1 / 0.81e2 * t649 * t747 * t278 + 0.4e1 / 0.27e2 * t282 * t747 * t292 + 0.4e1 / 0.3e1 * t286 * t277 * t729 + 0.8e1 / 0.9e1 * t290 * t291 * t720 - 0.16e2 / 0.9e1 * t270 * t48 * t292 - 0.32e2 / 0.9e1 * t276 * t287
  t1154 = t281 ** 2
  t1172 = 0.4e1 / 0.3e1 * t653 * t272 * t635 + 0.4e1 / 0.3e1 * t159 * t635 * params.d * t169 - 0.8e1 / 0.3e1 * t638 * t718 - 0.16e2 / 0.9e1 * t642 * t639 - 0.8e1 / 0.27e2 * t649 * t48 * t273 + 0.2e1 / 0.3e1 * t645 * t718 + 0.4e1 / 0.27e2 * t650 * t639 + params.b * t1154 * t747 * t273 / 0.81e2 + 0.4e1 / 0.3e1 * t57 * t717 * t29 * t61 + 0.8e1 / 0.9e1 * t724 * t261 * t312 * t44 + 0.8e1 / 0.27e2 * t56 * t744 * t154 * t349 * t747
  d1111 = 0.4e1 * params.a * (t295 + t732) + t2 * params.a * (-0.4e1 / 0.3e1 * t301 * t27 * t306 - 0.8e1 / 0.9e1 * t11 * t310 * t313 - 0.8e1 / 0.27e2 * t25 * t744 * t349 * t747 + 0.8e1 / 0.3e1 * t302 * t21 + 0.32e2 / 0.9e1 * t305 * t33 + 0.16e2 / 0.9e1 * t311 * t312 * t48 - 0.4e1 / 0.3e1 * t51 * t17 * t303 - 0.112e3 / 0.27e2 * t18 * t39 - 0.320e3 / 0.81e2 * t28 * t29 * t317 + 0.280e3 / 0.81e2 * t36 * params.d * t352 + t1106 - t791 * t52 - 0.280e3 / 0.81e2 * t159 * t266 * t352 - 0.280e3 / 0.81e2 * t270 * t352 * t273 + 0.320e3 / 0.81e2 * t57 * t155 * t317 + 0.112e3 / 0.27e2 * t159 * t262 * t38 - 0.32e2 / 0.9e1 * t57 * t720 * t32 - 0.16e2 / 0.9e1 * t724 * t725 * t48 - 0.8e1 / 0.3e1 * t159 * t729 * t20 + 0.112e3 / 0.27e2 * t271 * t639 + 0.160e3 / 0.81e2 * t282 * t317 * t273 + t1172)

  res = {'v4rho4': d1111}
  return res