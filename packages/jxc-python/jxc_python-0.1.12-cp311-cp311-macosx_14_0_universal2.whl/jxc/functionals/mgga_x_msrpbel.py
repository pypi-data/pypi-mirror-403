"""Generated from mgga_x_msrpbel.mpl."""

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
  params_eta_raw = params.eta
  if isinstance(params_eta_raw, (str, bytes, dict)):
    params_eta = params_eta_raw
  else:
    try:
      params_eta_seq = list(params_eta_raw)
    except TypeError:
      params_eta = params_eta_raw
    else:
      params_eta_seq = np.asarray(params_eta_seq, dtype=np.float64)
      params_eta = np.concatenate((np.array([np.nan], dtype=np.float64), params_eta_seq))
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

  msrpbel_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  msrpbel_f0 = lambda p, c: 1 + params_kappa * (1 - jnp.exp(-(MU_GE * p + c) / params_kappa))

  msrpbel_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  msrpbel_f = lambda x, u, t: msrpbel_f0(X2S ** 2 * x ** 2, 0) + msrpbel_fa(msrpbel_alpha(t, x)) * (msrpbel_f0(X2S ** 2 * x ** 2, params_c) - msrpbel_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msrpbel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_eta_raw = params.eta
  if isinstance(params_eta_raw, (str, bytes, dict)):
    params_eta = params_eta_raw
  else:
    try:
      params_eta_seq = list(params_eta_raw)
    except TypeError:
      params_eta = params_eta_raw
    else:
      params_eta_seq = np.asarray(params_eta_seq, dtype=np.float64)
      params_eta = np.concatenate((np.array([np.nan], dtype=np.float64), params_eta_seq))
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

  msrpbel_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  msrpbel_f0 = lambda p, c: 1 + params_kappa * (1 - jnp.exp(-(MU_GE * p + c) / params_kappa))

  msrpbel_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  msrpbel_f = lambda x, u, t: msrpbel_f0(X2S ** 2 * x ** 2, 0) + msrpbel_fa(msrpbel_alpha(t, x)) * (msrpbel_f0(X2S ** 2 * x ** 2, params_c) - msrpbel_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msrpbel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_eta_raw = params.eta
  if isinstance(params_eta_raw, (str, bytes, dict)):
    params_eta = params_eta_raw
  else:
    try:
      params_eta_seq = list(params_eta_raw)
    except TypeError:
      params_eta = params_eta_raw
    else:
      params_eta_seq = np.asarray(params_eta_seq, dtype=np.float64)
      params_eta = np.concatenate((np.array([np.nan], dtype=np.float64), params_eta_seq))
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

  msrpbel_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  msrpbel_f0 = lambda p, c: 1 + params_kappa * (1 - jnp.exp(-(MU_GE * p + c) / params_kappa))

  msrpbel_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  msrpbel_f = lambda x, u, t: msrpbel_f0(X2S ** 2 * x ** 2, 0) + msrpbel_fa(msrpbel_alpha(t, x)) * (msrpbel_f0(X2S ** 2 * x ** 2, params_c) - msrpbel_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msrpbel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t26 = t6 ** (0.1e1 / 0.3e1)
  t27 = t25 * t26
  t28 = 6 ** (0.1e1 / 0.3e1)
  t29 = jnp.pi ** 2
  t30 = t29 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t33 = t28 / t31
  t34 = r0 ** 2
  t35 = r0 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t38 = 0.1e1 / t36 / t34
  t39 = s0 * t38
  t40 = 0.1e1 / params.kappa
  t44 = jnp.exp(-0.5e1 / 0.972e3 * t33 * t39 * t40)
  t46 = params.kappa * (0.1e1 - t44)
  t48 = 0.1e1 / t36 / r0
  t51 = tau0 * t48 - t39 / 0.8e1
  t52 = t51 ** 2
  t53 = t28 ** 2
  t55 = 0.3e1 / 0.10e2 * t53 * t31
  t56 = params.eta * s0
  t59 = t55 + t56 * t38 / 0.8e1
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t63 = -t52 * t61 + 0.1e1
  t64 = t63 ** 2
  t65 = t64 * t63
  t66 = t52 * t51
  t67 = t60 * t59
  t68 = 0.1e1 / t67
  t70 = t52 ** 2
  t72 = params.b * t70 * t52
  t73 = t60 ** 2
  t75 = 0.1e1 / t73 / t60
  t77 = t66 * t68 + t72 * t75 + 0.1e1
  t78 = 0.1e1 / t77
  t79 = t65 * t78
  t84 = jnp.exp(-(0.5e1 / 0.972e3 * t33 * t39 + params.c) * t40)
  t87 = params.kappa * (0.1e1 - t84) - t46
  t89 = t79 * t87 + t46 + 0.1e1
  t93 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t89)
  t94 = r1 <= f.p.dens_threshold
  t95 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t96 = 0.1e1 + t95
  t97 = t96 <= f.p.zeta_threshold
  t98 = t96 ** (0.1e1 / 0.3e1)
  t100 = f.my_piecewise3(t97, t22, t98 * t96)
  t101 = t100 * t26
  t102 = r1 ** 2
  t103 = r1 ** (0.1e1 / 0.3e1)
  t104 = t103 ** 2
  t106 = 0.1e1 / t104 / t102
  t107 = s2 * t106
  t111 = jnp.exp(-0.5e1 / 0.972e3 * t33 * t107 * t40)
  t113 = params.kappa * (0.1e1 - t111)
  t115 = 0.1e1 / t104 / r1
  t118 = tau1 * t115 - t107 / 0.8e1
  t119 = t118 ** 2
  t120 = params.eta * s2
  t123 = t55 + t120 * t106 / 0.8e1
  t124 = t123 ** 2
  t125 = 0.1e1 / t124
  t127 = -t119 * t125 + 0.1e1
  t128 = t127 ** 2
  t129 = t128 * t127
  t130 = t119 * t118
  t131 = t124 * t123
  t132 = 0.1e1 / t131
  t134 = t119 ** 2
  t136 = params.b * t134 * t119
  t137 = t124 ** 2
  t139 = 0.1e1 / t137 / t124
  t141 = t130 * t132 + t136 * t139 + 0.1e1
  t142 = 0.1e1 / t141
  t143 = t129 * t142
  t148 = jnp.exp(-(0.5e1 / 0.972e3 * t33 * t107 + params.c) * t40)
  t151 = params.kappa * (0.1e1 - t148) - t113
  t153 = t143 * t151 + t113 + 0.1e1
  t157 = f.my_piecewise3(t94, 0, -0.3e1 / 0.8e1 * t5 * t101 * t153)
  t158 = t6 ** 2
  t160 = t16 / t158
  t161 = t7 - t160
  t162 = f.my_piecewise5(t10, 0, t14, 0, t161)
  t165 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t162)
  t170 = t26 ** 2
  t171 = 0.1e1 / t170
  t175 = t5 * t25 * t171 * t89 / 0.8e1
  t178 = 0.1e1 / t36 / t34 / r0
  t179 = s0 * t178
  t181 = t33 * t179 * t44
  t183 = t64 * t78
  t184 = t51 * t61
  t188 = -0.5e1 / 0.3e1 * tau0 * t38 + t179 / 0.3e1
  t191 = t52 * t68
  t192 = t56 * t178
  t199 = t77 ** 2
  t201 = t65 / t199
  t205 = t66 / t73
  t208 = params.b * t70 * t51
  t213 = 0.1e1 / t73 / t67
  t230 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t165 * t26 * t89 - t175 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.10e2 / 0.729e3 * t181 + 0.3e1 * t183 * t87 * (-0.2e1 * t184 * t188 - 0.2e1 / 0.3e1 * t191 * t192) - t201 * t87 * (0.6e1 * t208 * t75 * t188 + 0.2e1 * t72 * t213 * t192 + 0.3e1 * t191 * t188 + t205 * t192) + t79 * (-0.10e2 / 0.729e3 * t33 * t179 * t84 + 0.10e2 / 0.729e3 * t181)))
  t232 = f.my_piecewise5(t14, 0, t10, 0, -t161)
  t235 = f.my_piecewise3(t97, 0, 0.4e1 / 0.3e1 * t98 * t232)
  t243 = t5 * t100 * t171 * t153 / 0.8e1
  t245 = f.my_piecewise3(t94, 0, -0.3e1 / 0.8e1 * t5 * t235 * t26 * t153 - t243)
  vrho_0_ = t93 + t157 + t6 * (t230 + t245)
  t248 = -t7 - t160
  t249 = f.my_piecewise5(t10, 0, t14, 0, t248)
  t252 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t249)
  t258 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t252 * t26 * t89 - t175)
  t260 = f.my_piecewise5(t14, 0, t10, 0, -t248)
  t263 = f.my_piecewise3(t97, 0, 0.4e1 / 0.3e1 * t98 * t260)
  t270 = 0.1e1 / t104 / t102 / r1
  t271 = s2 * t270
  t273 = t33 * t271 * t111
  t275 = t128 * t142
  t276 = t118 * t125
  t280 = -0.5e1 / 0.3e1 * tau1 * t106 + t271 / 0.3e1
  t283 = t119 * t132
  t284 = t120 * t270
  t291 = t141 ** 2
  t293 = t129 / t291
  t297 = t130 / t137
  t300 = params.b * t134 * t118
  t305 = 0.1e1 / t137 / t131
  t322 = f.my_piecewise3(t94, 0, -0.3e1 / 0.8e1 * t5 * t263 * t26 * t153 - t243 - 0.3e1 / 0.8e1 * t5 * t101 * (-0.10e2 / 0.729e3 * t273 + 0.3e1 * t275 * t151 * (-0.2e1 * t276 * t280 - 0.2e1 / 0.3e1 * t283 * t284) - t293 * t151 * (0.2e1 * t136 * t305 * t284 + 0.6e1 * t300 * t139 * t280 + 0.3e1 * t283 * t280 + t297 * t284) + t143 * (-0.10e2 / 0.729e3 * t33 * t271 * t148 + 0.10e2 / 0.729e3 * t273)))
  vrho_1_ = t93 + t157 + t6 * (t258 + t322)
  t326 = t33 * t38 * t44
  t329 = params.eta * t38
  t359 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.5e1 / 0.972e3 * t326 + 0.3e1 * t183 * t87 * (t184 * t38 / 0.4e1 + t191 * t329 / 0.4e1) - t201 * t87 * (-0.3e1 / 0.8e1 * t191 * t38 - 0.3e1 / 0.8e1 * t205 * t329 - 0.3e1 / 0.4e1 * t208 * t75 * t38 - 0.3e1 / 0.4e1 * t72 * t213 * params.eta * t38) + t79 * (0.5e1 / 0.972e3 * t33 * t38 * t84 - 0.5e1 / 0.972e3 * t326)))
  vsigma_0_ = t6 * t359
  vsigma_1_ = 0.0e0
  t361 = t33 * t106 * t111
  t364 = params.eta * t106
  t394 = f.my_piecewise3(t94, 0, -0.3e1 / 0.8e1 * t5 * t101 * (0.5e1 / 0.972e3 * t361 + 0.3e1 * t275 * t151 * (t276 * t106 / 0.4e1 + t283 * t364 / 0.4e1) - t293 * t151 * (-0.3e1 / 0.8e1 * t283 * t106 - 0.3e1 / 0.8e1 * t297 * t364 - 0.3e1 / 0.4e1 * t300 * t139 * t106 - 0.3e1 / 0.4e1 * t136 * t305 * params.eta * t106) + t143 * (0.5e1 / 0.972e3 * t33 * t106 * t148 - 0.5e1 / 0.972e3 * t361)))
  vsigma_2_ = t6 * t394
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t411 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-0.6e1 * t183 * t87 * t184 * t48 - t201 * t87 * (0.6e1 * t208 * t75 * t48 + 0.3e1 * t191 * t48)))
  vtau_0_ = t6 * t411
  t428 = f.my_piecewise3(t94, 0, -0.3e1 / 0.8e1 * t5 * t101 * (-0.6e1 * t275 * t151 * t276 * t115 - t293 * t151 * (0.6e1 * t300 * t139 * t115 + 0.3e1 * t283 * t115)))
  vtau_1_ = t6 * t428
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
  params_eta_raw = params.eta
  if isinstance(params_eta_raw, (str, bytes, dict)):
    params_eta = params_eta_raw
  else:
    try:
      params_eta_seq = list(params_eta_raw)
    except TypeError:
      params_eta = params_eta_raw
    else:
      params_eta_seq = np.asarray(params_eta_seq, dtype=np.float64)
      params_eta = np.concatenate((np.array([np.nan], dtype=np.float64), params_eta_seq))
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

  msrpbel_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  msrpbel_f0 = lambda p, c: 1 + params_kappa * (1 - jnp.exp(-(MU_GE * p + c) / params_kappa))

  msrpbel_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  msrpbel_f = lambda x, u, t: msrpbel_f0(X2S ** 2 * x ** 2, 0) + msrpbel_fa(msrpbel_alpha(t, x)) * (msrpbel_f0(X2S ** 2 * x ** 2, params_c) - msrpbel_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msrpbel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t17 * t18
  t20 = 6 ** (0.1e1 / 0.3e1)
  t21 = jnp.pi ** 2
  t22 = t21 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t25 = t20 / t23
  t26 = t25 * s0
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = r0 ** 2
  t30 = t18 ** 2
  t32 = 0.1e1 / t30 / t29
  t33 = t28 * t32
  t34 = 0.1e1 / params.kappa
  t38 = jnp.exp(-0.5e1 / 0.972e3 * t26 * t33 * t34)
  t40 = params.kappa * (0.1e1 - t38)
  t41 = tau0 * t28
  t43 = 0.1e1 / t30 / r0
  t45 = s0 * t28
  t46 = t45 * t32
  t48 = t41 * t43 - t46 / 0.8e1
  t49 = t48 ** 2
  t50 = t20 ** 2
  t53 = params.eta * s0
  t56 = 0.3e1 / 0.10e2 * t50 * t23 + t53 * t33 / 0.8e1
  t57 = t56 ** 2
  t58 = 0.1e1 / t57
  t60 = -t49 * t58 + 0.1e1
  t61 = t60 ** 2
  t62 = t61 * t60
  t63 = t49 * t48
  t64 = t57 * t56
  t65 = 0.1e1 / t64
  t67 = t49 ** 2
  t69 = params.b * t67 * t49
  t70 = t57 ** 2
  t72 = 0.1e1 / t70 / t57
  t74 = t63 * t65 + t69 * t72 + 0.1e1
  t75 = 0.1e1 / t74
  t76 = t62 * t75
  t81 = jnp.exp(-(0.5e1 / 0.972e3 * t25 * t46 + params.c) * t34)
  t84 = params.kappa * (0.1e1 - t81) - t40
  t86 = t76 * t84 + t40 + 0.1e1
  t90 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t86)
  t98 = 0.1e1 / t30 / t29 / r0
  t99 = t28 * t98
  t101 = t26 * t99 * t38
  t103 = t61 * t75
  t104 = t48 * t58
  t107 = t45 * t98
  t109 = -0.5e1 / 0.3e1 * t41 * t32 + t107 / 0.3e1
  t112 = t49 * t65
  t120 = t74 ** 2
  t122 = t62 / t120
  t126 = t63 / t70
  t130 = params.b * t67 * t48
  t136 = t69 / t70 / t64
  t153 = f.my_piecewise3(t2, 0, -t6 * t17 / t30 * t86 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.10e2 / 0.729e3 * t101 + 0.3e1 * t103 * t84 * (-0.2e1 * t104 * t109 - 0.2e1 / 0.3e1 * t112 * params.eta * t107) - t122 * t84 * (t126 * params.eta * t107 + 0.6e1 * t130 * t72 * t109 + 0.2e1 * t136 * t53 * t99 + 0.3e1 * t112 * t109) + t76 * (-0.10e2 / 0.729e3 * t26 * t99 * t81 + 0.10e2 / 0.729e3 * t101)))
  vrho_0_ = 0.2e1 * r0 * t153 + 0.2e1 * t90
  t157 = t25 * t33 * t38
  t161 = params.eta * t28 * t32
  t172 = t72 * t28
  t190 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.5e1 / 0.972e3 * t157 + 0.3e1 * t103 * t84 * (t104 * t33 / 0.4e1 + t112 * t161 / 0.4e1) - t122 * t84 * (-0.3e1 / 0.8e1 * t112 * t33 - 0.3e1 / 0.8e1 * t126 * t161 - 0.3e1 / 0.4e1 * t130 * t172 * t32 - 0.3e1 / 0.4e1 * t136 * t161) + t76 * (0.5e1 / 0.972e3 * t25 * t33 * t81 - 0.5e1 / 0.972e3 * t157)))
  vsigma_0_ = 0.2e1 * r0 * t190
  vlapl_0_ = 0.0e0
  t193 = t28 * t43
  t209 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-0.6e1 * t103 * t84 * t104 * t193 - t122 * t84 * (0.6e1 * t130 * t172 * t43 + 0.3e1 * t112 * t193)))
  vtau_0_ = 0.2e1 * r0 * t209
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
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = t17 / t19
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = jnp.pi ** 2
  t24 = t23 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t27 = t22 / t25
  t28 = t27 * s0
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = r0 ** 2
  t33 = 0.1e1 / t19 / t31
  t34 = t30 * t33
  t35 = 0.1e1 / params.kappa
  t39 = jnp.exp(-0.5e1 / 0.972e3 * t28 * t34 * t35)
  t41 = params.kappa * (0.1e1 - t39)
  t42 = tau0 * t30
  t44 = 0.1e1 / t19 / r0
  t46 = s0 * t30
  t47 = t46 * t33
  t49 = t42 * t44 - t47 / 0.8e1
  t50 = t49 ** 2
  t51 = t22 ** 2
  t54 = params.eta * s0
  t57 = 0.3e1 / 0.10e2 * t51 * t25 + t54 * t34 / 0.8e1
  t58 = t57 ** 2
  t59 = 0.1e1 / t58
  t61 = -t50 * t59 + 0.1e1
  t62 = t61 ** 2
  t63 = t62 * t61
  t64 = t50 * t49
  t65 = t58 * t57
  t66 = 0.1e1 / t65
  t68 = t50 ** 2
  t70 = params.b * t68 * t50
  t71 = t58 ** 2
  t73 = 0.1e1 / t71 / t58
  t75 = t64 * t66 + t70 * t73 + 0.1e1
  t76 = 0.1e1 / t75
  t77 = t63 * t76
  t82 = jnp.exp(-(0.5e1 / 0.972e3 * t27 * t47 + params.c) * t35)
  t85 = params.kappa * (0.1e1 - t82) - t41
  t87 = t77 * t85 + t41 + 0.1e1
  t91 = t17 * t18
  t92 = t31 * r0
  t94 = 0.1e1 / t19 / t92
  t95 = t30 * t94
  t97 = t28 * t95 * t39
  t99 = t62 * t76
  t100 = t49 * t59
  t103 = t46 * t94
  t105 = -0.5e1 / 0.3e1 * t42 * t33 + t103 / 0.3e1
  t108 = t50 * t66
  t109 = t108 * params.eta
  t112 = -0.2e1 * t100 * t105 - 0.2e1 / 0.3e1 * t109 * t103
  t113 = t85 * t112
  t116 = t75 ** 2
  t117 = 0.1e1 / t116
  t118 = t63 * t117
  t121 = 0.1e1 / t71
  t123 = t64 * t121 * params.eta
  t126 = params.b * t68 * t49
  t131 = 0.1e1 / t71 / t65
  t132 = t70 * t131
  t133 = t54 * t95
  t136 = 0.6e1 * t126 * t73 * t105 + t123 * t103 + 0.3e1 * t108 * t105 + 0.2e1 * t132 * t133
  t142 = -0.10e2 / 0.729e3 * t28 * t95 * t82 + 0.10e2 / 0.729e3 * t97
  t144 = -0.10e2 / 0.729e3 * t97 + 0.3e1 * t99 * t113 - t118 * t85 * t136 + t77 * t142
  t149 = f.my_piecewise3(t2, 0, -t6 * t21 * t87 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t91 * t144)
  t158 = t31 ** 2
  t160 = 0.1e1 / t19 / t158
  t161 = t30 * t160
  t164 = 0.110e3 / 0.2187e4 * t28 * t161 * t39
  t168 = s0 ** 2
  t169 = t51 / t24 / t23 * t168
  t172 = 0.1e1 / t18 / t158 / t92
  t173 = t29 * t172
  t177 = 0.200e3 / 0.531441e6 * t169 * t173 * t35 * t39
  t179 = t112 ** 2
  t190 = t105 ** 2
  t193 = t49 * t66
  t199 = t46 * t160
  t201 = 0.40e2 / 0.9e1 * t42 * t94 - 0.11e2 / 0.9e1 * t199
  t204 = t50 * t121
  t205 = params.eta ** 2
  t208 = t168 * t29 * t172
  t220 = t136 ** 2
  t253 = t71 ** 2
  t280 = f.my_piecewise3(t2, 0, t6 * t17 * t44 * t87 / 0.12e2 - t6 * t21 * t144 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t91 * (t164 - t177 + 0.6e1 * t61 * t76 * t85 * t179 - 0.6e1 * t62 * t117 * t113 * t136 + 0.6e1 * t99 * t142 * t112 + 0.3e1 * t99 * t85 * (-0.2e1 * t190 * t59 - 0.8e1 / 0.3e1 * t193 * t105 * t133 - 0.2e1 * t100 * t201 - 0.4e1 / 0.3e1 * t204 * t205 * t208 + 0.22e2 / 0.9e1 * t109 * t199) + 0.2e1 * t63 / t116 / t75 * t85 * t220 - 0.2e1 * t118 * t142 * t136 - t118 * t85 * (0.6e1 * t193 * t190 + 0.6e1 * t204 * t105 * t133 + 0.3e1 * t108 * t201 + 0.8e1 / 0.3e1 * t64 / t71 / t57 * t205 * t208 - 0.11e2 / 0.3e1 * t123 * t199 + 0.30e2 * params.b * t68 * t73 * t190 + 0.24e2 * t126 * t131 * t105 * t133 + 0.6e1 * t126 * t73 * t201 + 0.28e2 / 0.3e1 * t70 / t253 * t205 * t168 * t173 - 0.22e2 / 0.3e1 * t132 * t54 * t161) + t77 * (0.110e3 / 0.2187e4 * t28 * t161 * t82 - 0.200e3 / 0.531441e6 * t169 * t173 * t35 * t82 - t164 + t177)))
  v2rho2_0_ = 0.2e1 * r0 * t280 + 0.4e1 * t149
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
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = 0.1e1 / t19 / r0
  t22 = t17 * t21
  t23 = 6 ** (0.1e1 / 0.3e1)
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = t23 / t26
  t29 = t28 * s0
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t35 = t31 * t34
  t36 = 0.1e1 / params.kappa
  t40 = jnp.exp(-0.5e1 / 0.972e3 * t29 * t35 * t36)
  t42 = params.kappa * (0.1e1 - t40)
  t43 = tau0 * t31
  t45 = s0 * t31
  t46 = t45 * t34
  t48 = t43 * t21 - t46 / 0.8e1
  t49 = t48 ** 2
  t50 = t23 ** 2
  t53 = params.eta * s0
  t56 = 0.3e1 / 0.10e2 * t50 * t26 + t53 * t35 / 0.8e1
  t57 = t56 ** 2
  t58 = 0.1e1 / t57
  t60 = -t49 * t58 + 0.1e1
  t61 = t60 ** 2
  t62 = t61 * t60
  t63 = t49 * t48
  t64 = t57 * t56
  t65 = 0.1e1 / t64
  t67 = t49 ** 2
  t69 = params.b * t67 * t49
  t70 = t57 ** 2
  t72 = 0.1e1 / t70 / t57
  t74 = t63 * t65 + t69 * t72 + 0.1e1
  t75 = 0.1e1 / t74
  t76 = t62 * t75
  t81 = jnp.exp(-(0.5e1 / 0.972e3 * t28 * t46 + params.c) * t36)
  t84 = params.kappa * (0.1e1 - t81) - t42
  t86 = t76 * t84 + t42 + 0.1e1
  t91 = t17 / t19
  t92 = t32 * r0
  t94 = 0.1e1 / t19 / t92
  t95 = t31 * t94
  t97 = t29 * t95 * t40
  t99 = t61 * t75
  t100 = t48 * t58
  t103 = t45 * t94
  t105 = -0.5e1 / 0.3e1 * t43 * t34 + t103 / 0.3e1
  t108 = t49 * t65
  t109 = t108 * params.eta
  t112 = -0.2e1 * t100 * t105 - 0.2e1 / 0.3e1 * t109 * t103
  t113 = t84 * t112
  t116 = t74 ** 2
  t117 = 0.1e1 / t116
  t118 = t62 * t117
  t121 = 0.1e1 / t70
  t123 = t63 * t121 * params.eta
  t126 = params.b * t67 * t48
  t127 = t72 * t105
  t131 = 0.1e1 / t70 / t64
  t132 = t69 * t131
  t133 = t53 * t95
  t136 = t123 * t103 + 0.3e1 * t108 * t105 + 0.6e1 * t126 * t127 + 0.2e1 * t132 * t133
  t137 = t84 * t136
  t142 = -0.10e2 / 0.729e3 * t29 * t95 * t81 + 0.10e2 / 0.729e3 * t97
  t144 = -0.10e2 / 0.729e3 * t97 + 0.3e1 * t99 * t113 - t118 * t137 + t76 * t142
  t148 = t17 * t18
  t149 = t32 ** 2
  t151 = 0.1e1 / t19 / t149
  t152 = t31 * t151
  t155 = 0.110e3 / 0.2187e4 * t29 * t152 * t40
  t159 = s0 ** 2
  t160 = t50 / t25 / t24 * t159
  t163 = 0.1e1 / t18 / t149 / t92
  t164 = t30 * t163
  t165 = t36 * t40
  t168 = 0.200e3 / 0.531441e6 * t160 * t164 * t165
  t169 = t60 * t75
  t170 = t112 ** 2
  t171 = t84 * t170
  t174 = t61 * t117
  t178 = t142 * t112
  t181 = t105 ** 2
  t184 = t48 * t65
  t185 = t184 * t105
  t190 = t45 * t151
  t192 = 0.40e2 / 0.9e1 * t43 * t94 - 0.11e2 / 0.9e1 * t190
  t195 = t49 * t121
  t196 = params.eta ** 2
  t197 = t195 * t196
  t198 = t159 * t30
  t199 = t198 * t163
  t204 = -0.2e1 * t181 * t58 - 0.8e1 / 0.3e1 * t185 * t133 - 0.2e1 * t100 * t192 - 0.4e1 / 0.3e1 * t197 * t199 + 0.22e2 / 0.9e1 * t109 * t190
  t205 = t84 * t204
  t209 = 0.1e1 / t116 / t74
  t210 = t62 * t209
  t211 = t136 ** 2
  t220 = t195 * t105
  t226 = 0.1e1 / t70 / t56
  t228 = t63 * t226 * t196
  t233 = params.b * t67
  t238 = t126 * t131 * t105
  t244 = t70 ** 2
  t245 = 0.1e1 / t244
  t246 = t69 * t245
  t247 = t196 * t159
  t248 = t247 * t164
  t251 = t53 * t152
  t254 = 0.6e1 * t184 * t181 + 0.6e1 * t220 * t133 + 0.3e1 * t108 * t192 + 0.8e1 / 0.3e1 * t228 * t199 - 0.11e2 / 0.3e1 * t123 * t190 + 0.30e2 * t233 * t72 * t181 + 0.24e2 * t238 * t133 + 0.6e1 * t126 * t72 * t192 + 0.28e2 / 0.3e1 * t246 * t248 - 0.22e2 / 0.3e1 * t132 * t251
  t260 = t36 * t81
  t264 = 0.110e3 / 0.2187e4 * t29 * t152 * t81 - 0.200e3 / 0.531441e6 * t160 * t164 * t260 - t155 + t168
  t266 = -0.6e1 * t174 * t113 * t136 - 0.2e1 * t118 * t142 * t136 - t118 * t84 * t254 + 0.2e1 * t210 * t84 * t211 + 0.6e1 * t169 * t171 + 0.6e1 * t99 * t178 + 0.3e1 * t99 * t205 + t76 * t264 + t155 - t168
  t271 = f.my_piecewise3(t2, 0, t6 * t22 * t86 / 0.12e2 - t6 * t91 * t144 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t148 * t266)
  t292 = t149 ** 2
  t294 = 0.1e1 / t18 / t292
  t295 = t30 * t294
  t301 = 0.1e1 / t19 / t149 / r0
  t302 = t31 * t301
  t311 = t45 * t301
  t313 = -0.440e3 / 0.27e2 * t43 * t151 + 0.154e3 / 0.27e2 * t311
  t317 = t181 * t105
  t322 = t198 * t294
  t327 = t48 * t121
  t334 = t49 * t226
  t340 = t159 * s0
  t343 = 0.1e1 / t292 / t92
  t344 = t196 * params.eta * t340 * t343
  t375 = -0.308e3 / 0.3e1 * t246 * t247 * t295 + 0.308e3 / 0.9e1 * t132 * t53 * t302 + 0.18e2 * t184 * t105 * t192 + 0.6e1 * t126 * t72 * t313 + 0.6e1 * t317 * t65 + 0.3e1 * t108 * t313 - 0.88e2 / 0.3e1 * t228 * t322 + 0.154e3 / 0.9e1 * t123 * t311 + 0.18e2 * t327 * t181 * t133 + 0.9e1 * t195 * t192 * t133 + 0.24e2 * t334 * t105 * t248 + 0.80e2 / 0.9e1 * t63 * t72 * t344 + 0.120e3 * params.b * t63 * t72 * t317 + 0.90e2 * t233 * t127 * t192 - 0.33e2 * t220 * t251 + 0.180e3 * t233 * t131 * t181 * t133 + 0.36e2 * t126 * t131 * t192 * t133 + 0.168e3 * t126 * t245 * t105 * t248 + 0.448e3 / 0.9e1 * t69 / t244 / t56 * t344 - 0.132e3 * t238 * t251
  t424 = t24 ** 2
  t426 = 0.1e1 / t424 * t340
  t427 = params.kappa ** 2
  t429 = t343 / t427
  t435 = 0.1540e4 / 0.6561e4 * t29 * t302 * t40
  t438 = 0.2200e4 / 0.531441e6 * t160 * t295 * t165
  t441 = 0.8000e4 / 0.129140163e9 * t426 * t429 * t40
  t448 = t116 ** 2
  t475 = -t435 + t438 - 0.9e1 * t174 * t113 * t254 - 0.6e1 * t62 / t448 * t84 * t211 * t136 + 0.6e1 * t210 * t137 * t254 - t441 - 0.18e2 * t60 * t117 * t171 * t136 + 0.18e2 * t169 * t113 * t204 - 0.18e2 * t174 * t178 * t136 - 0.9e1 * t174 * t205 * t136 + 0.18e2 * t61 * t209 * t113 * t211
  t481 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t34 * t86 + t6 * t22 * t144 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t91 * t266 - 0.3e1 / 0.8e1 * t6 * t148 * (0.6e1 * t210 * t142 * t211 - 0.3e1 * t118 * t264 * t136 - 0.3e1 * t118 * t142 * t254 - t118 * t84 * t375 + 0.6e1 * t170 * t112 * t75 * t84 + 0.18e2 * t169 * t142 * t170 + 0.9e1 * t99 * t264 * t112 + 0.9e1 * t99 * t142 * t204 + 0.3e1 * t99 * t84 * (-0.6e1 * t105 * t58 * t192 - 0.4e1 * t181 * t65 * params.eta * t103 - 0.8e1 * t327 * t105 * t248 - 0.4e1 * t184 * t192 * t133 + 0.44e2 / 0.3e1 * t185 * t251 - 0.2e1 * t100 * t313 - 0.32e2 / 0.9e1 * t334 * t344 + 0.44e2 / 0.3e1 * t197 * t322 - 0.308e3 / 0.27e2 * t109 * t311) + t76 * (-0.1540e4 / 0.6561e4 * t29 * t302 * t81 + 0.2200e4 / 0.531441e6 * t160 * t295 * t260 - 0.8000e4 / 0.129140163e9 * t426 * t429 * t81 + t435 - t438 + t441) + t475))
  v3rho3_0_ = 0.2e1 * r0 * t481 + 0.6e1 * t271

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
  t18 = r0 ** 2
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / t18
  t23 = t17 * t22
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t29 = t24 / t27
  t30 = t29 * s0
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = t32 * t22
  t34 = 0.1e1 / params.kappa
  t38 = jnp.exp(-0.5e1 / 0.972e3 * t30 * t33 * t34)
  t40 = params.kappa * (0.1e1 - t38)
  t41 = tau0 * t32
  t43 = 0.1e1 / t20 / r0
  t45 = s0 * t32
  t46 = t45 * t22
  t48 = t41 * t43 - t46 / 0.8e1
  t49 = t48 ** 2
  t50 = t24 ** 2
  t53 = params.eta * s0
  t56 = 0.3e1 / 0.10e2 * t50 * t27 + t53 * t33 / 0.8e1
  t57 = t56 ** 2
  t58 = 0.1e1 / t57
  t60 = -t49 * t58 + 0.1e1
  t61 = t60 ** 2
  t62 = t61 * t60
  t63 = t49 * t48
  t64 = t57 * t56
  t65 = 0.1e1 / t64
  t67 = t49 ** 2
  t69 = params.b * t67 * t49
  t70 = t57 ** 2
  t72 = 0.1e1 / t70 / t57
  t74 = t63 * t65 + t69 * t72 + 0.1e1
  t75 = 0.1e1 / t74
  t76 = t62 * t75
  t81 = jnp.exp(-(0.5e1 / 0.972e3 * t29 * t46 + params.c) * t34)
  t84 = params.kappa * (0.1e1 - t81) - t40
  t86 = t76 * t84 + t40 + 0.1e1
  t90 = t17 * t43
  t91 = t18 * r0
  t93 = 0.1e1 / t20 / t91
  t94 = t32 * t93
  t96 = t30 * t94 * t38
  t98 = t61 * t75
  t99 = t48 * t58
  t102 = t45 * t93
  t104 = -0.5e1 / 0.3e1 * t41 * t22 + t102 / 0.3e1
  t107 = t49 * t65
  t108 = t107 * params.eta
  t111 = -0.2e1 * t99 * t104 - 0.2e1 / 0.3e1 * t108 * t102
  t112 = t84 * t111
  t115 = t74 ** 2
  t116 = 0.1e1 / t115
  t117 = t62 * t116
  t120 = 0.1e1 / t70
  t122 = t63 * t120 * params.eta
  t125 = params.b * t67 * t48
  t126 = t72 * t104
  t130 = 0.1e1 / t70 / t64
  t131 = t69 * t130
  t132 = t53 * t94
  t135 = t122 * t102 + 0.3e1 * t107 * t104 + 0.6e1 * t125 * t126 + 0.2e1 * t131 * t132
  t136 = t84 * t135
  t141 = -0.10e2 / 0.729e3 * t30 * t94 * t81 + 0.10e2 / 0.729e3 * t96
  t143 = -0.10e2 / 0.729e3 * t96 + 0.3e1 * t98 * t112 - t117 * t136 + t76 * t141
  t148 = t17 / t20
  t149 = t18 ** 2
  t151 = 0.1e1 / t20 / t149
  t152 = t32 * t151
  t155 = 0.110e3 / 0.2187e4 * t30 * t152 * t38
  t159 = s0 ** 2
  t160 = t50 / t26 / t25 * t159
  t163 = 0.1e1 / t19 / t149 / t91
  t164 = t31 * t163
  t165 = t34 * t38
  t168 = 0.200e3 / 0.531441e6 * t160 * t164 * t165
  t169 = t60 * t75
  t170 = t111 ** 2
  t171 = t84 * t170
  t174 = t61 * t116
  t178 = t141 * t111
  t181 = t104 ** 2
  t184 = t48 * t65
  t185 = t184 * t104
  t190 = t45 * t151
  t192 = 0.40e2 / 0.9e1 * t41 * t93 - 0.11e2 / 0.9e1 * t190
  t195 = t49 * t120
  t196 = params.eta ** 2
  t197 = t195 * t196
  t198 = t159 * t31
  t199 = t198 * t163
  t204 = -0.2e1 * t181 * t58 - 0.8e1 / 0.3e1 * t185 * t132 - 0.2e1 * t99 * t192 - 0.4e1 / 0.3e1 * t197 * t199 + 0.22e2 / 0.9e1 * t108 * t190
  t205 = t84 * t204
  t209 = 0.1e1 / t115 / t74
  t210 = t62 * t209
  t211 = t135 ** 2
  t212 = t84 * t211
  t215 = t141 * t135
  t220 = t195 * t104
  t226 = 0.1e1 / t70 / t56
  t228 = t63 * t226 * t196
  t233 = params.b * t67
  t234 = t72 * t181
  t237 = t130 * t104
  t238 = t125 * t237
  t244 = t70 ** 2
  t245 = 0.1e1 / t244
  t246 = t69 * t245
  t247 = t196 * t159
  t248 = t247 * t164
  t251 = t53 * t152
  t254 = 0.6e1 * t184 * t181 + 0.6e1 * t220 * t132 + 0.3e1 * t107 * t192 + 0.8e1 / 0.3e1 * t228 * t199 - 0.11e2 / 0.3e1 * t122 * t190 + 0.30e2 * t233 * t234 + 0.24e2 * t238 * t132 + 0.6e1 * t125 * t72 * t192 + 0.28e2 / 0.3e1 * t246 * t248 - 0.22e2 / 0.3e1 * t131 * t251
  t260 = t34 * t81
  t264 = 0.110e3 / 0.2187e4 * t30 * t152 * t81 - 0.200e3 / 0.531441e6 * t160 * t164 * t260 - t155 + t168
  t266 = -0.6e1 * t174 * t112 * t135 - t117 * t84 * t254 - 0.2e1 * t117 * t215 + 0.6e1 * t169 * t171 + 0.6e1 * t98 * t178 + 0.3e1 * t98 * t205 + 0.2e1 * t210 * t212 + t76 * t264 + t155 - t168
  t270 = t17 * t19
  t271 = t141 * t211
  t274 = t264 * t135
  t277 = t141 * t254
  t280 = t149 ** 2
  t282 = 0.1e1 / t19 / t280
  t283 = t31 * t282
  t284 = t247 * t283
  t289 = 0.1e1 / t20 / t149 / r0
  t290 = t32 * t289
  t291 = t53 * t290
  t296 = t104 * t192
  t301 = t45 * t289
  t303 = -0.440e3 / 0.27e2 * t41 * t151 + 0.154e3 / 0.27e2 * t301
  t304 = t72 * t303
  t307 = t181 * t104
  t312 = t198 * t282
  t317 = t48 * t120
  t318 = t317 * t181
  t321 = t195 * t192
  t324 = t49 * t226
  t328 = t63 * t72
  t329 = t196 * params.eta
  t330 = t159 * s0
  t331 = t329 * t330
  t333 = 0.1e1 / t280 / t91
  t334 = t331 * t333
  t337 = params.b * t63
  t347 = t233 * t130 * t181
  t351 = t125 * t130 * t192
  t359 = 0.1e1 / t244 / t56
  t360 = t69 * t359
  t363 = -0.308e3 / 0.3e1 * t246 * t284 + 0.308e3 / 0.9e1 * t131 * t291 - 0.132e3 * t238 * t251 + 0.18e2 * t184 * t296 + 0.6e1 * t125 * t304 + 0.6e1 * t307 * t65 + 0.3e1 * t107 * t303 - 0.88e2 / 0.3e1 * t228 * t312 + 0.154e3 / 0.9e1 * t122 * t301 + 0.18e2 * t318 * t132 + 0.9e1 * t321 * t132 + 0.24e2 * t324 * t104 * t248 + 0.80e2 / 0.9e1 * t328 * t334 + 0.120e3 * t337 * t72 * t307 + 0.90e2 * t233 * t126 * t192 - 0.33e2 * t220 * t251 + 0.180e3 * t347 * t132 + 0.36e2 * t351 * t132 + 0.168e3 * t125 * t245 * t104 * t248 + 0.448e3 / 0.9e1 * t360 * t334
  t364 = t84 * t363
  t366 = t170 * t111
  t367 = t366 * t75
  t370 = t141 * t170
  t376 = t141 * t204
  t379 = t104 * t58
  t382 = t181 * t65
  t383 = t382 * params.eta
  t386 = t317 * t104
  t389 = t184 * t192
  t402 = -0.6e1 * t379 * t192 - 0.4e1 * t383 * t102 - 0.8e1 * t386 * t248 - 0.4e1 * t389 * t132 + 0.44e2 / 0.3e1 * t185 * t251 - 0.2e1 * t99 * t303 - 0.32e2 / 0.9e1 * t324 * t334 + 0.44e2 / 0.3e1 * t197 * t312 - 0.308e3 / 0.27e2 * t108 * t301
  t403 = t84 * t402
  t412 = t25 ** 2
  t413 = 0.1e1 / t412
  t414 = t413 * t330
  t415 = params.kappa ** 2
  t416 = 0.1e1 / t415
  t417 = t333 * t416
  t423 = 0.1540e4 / 0.6561e4 * t30 * t290 * t38
  t426 = 0.2200e4 / 0.531441e6 * t160 * t283 * t165
  t429 = 0.8000e4 / 0.129140163e9 * t414 * t417 * t38
  t430 = -0.1540e4 / 0.6561e4 * t30 * t290 * t81 + 0.2200e4 / 0.531441e6 * t160 * t283 * t260 - 0.8000e4 / 0.129140163e9 * t414 * t417 * t81 + t423 - t426 + t429
  t436 = t115 ** 2
  t437 = 0.1e1 / t436
  t438 = t62 * t437
  t439 = t211 * t135
  t440 = t84 * t439
  t446 = t60 * t116
  t459 = t61 * t209
  t463 = 0.18e2 * t169 * t112 * t204 - 0.9e1 * t174 * t112 * t254 + 0.18e2 * t459 * t112 * t211 - 0.18e2 * t446 * t171 * t135 - 0.18e2 * t174 * t178 * t135 - 0.9e1 * t174 * t205 * t135 + 0.6e1 * t210 * t136 * t254 - 0.6e1 * t438 * t440 - t423 + t426 - t429
  t464 = 0.9e1 * t98 * t264 * t111 - 0.3e1 * t117 * t274 - 0.3e1 * t117 * t277 - t117 * t364 + 0.18e2 * t169 * t370 + 0.6e1 * t210 * t271 + 0.6e1 * t367 * t84 + 0.9e1 * t98 * t376 + 0.3e1 * t98 * t403 + t76 * t430 + t463
  t469 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t86 + t6 * t90 * t143 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t148 * t266 - 0.3e1 / 0.8e1 * t6 * t270 * t464)
  t546 = -0.12e2 * t174 * t403 * t135 - 0.36e2 * t174 * t376 * t135 + 0.24e2 * t169 * t403 * t111 + 0.72e2 * t169 * t178 * t204 + 0.36e2 * t459 * t205 * t211 - 0.36e2 * t446 * t171 * t254 + 0.72e2 * t60 * t209 * t171 * t211 + 0.8e1 * t210 * t364 * t135 - 0.72e2 * t446 * t370 * t135 - 0.36e2 * t174 * t277 * t111 - 0.12e2 * t174 * t364 * t111 + 0.72e2 * t459 * t271 * t111 + 0.24e2 * t210 * t215 * t254 - 0.36e2 * t174 * t274 * t111 - 0.72e2 * t61 * t437 * t440 * t111 - 0.36e2 * t438 * t212 * t254 - 0.4e1 * t117 * t430 * t135 + 0.12e2 * t98 * t141 * t402 + 0.12e2 * t210 * t264 * t211 + 0.12e2 * t98 * t430 * t111
  t561 = t149 * t18
  t563 = 0.1e1 / t20 / t561
  t564 = t45 * t563
  t566 = 0.6160e4 / 0.81e2 * t41 * t289 - 0.2618e4 / 0.81e2 * t564
  t571 = t192 ** 2
  t575 = t181 ** 2
  t592 = 0.1e1 / t280 / t149
  t593 = t331 * t592
  t616 = t198 * t282 * t104
  t622 = t45 * t289 * t104
  t630 = 0.3e1 * t107 * t566 + 0.36e2 * t382 * t192 + 0.18e2 * t184 * t571 + 0.360e3 * params.b * t49 * t72 * t575 + 0.90e2 * t233 * t72 * t571 + 0.24e2 * t184 * t104 * t303 + 0.6e1 * t125 * t72 * t566 + 0.120e3 * t233 * t304 * t104 - 0.1760e4 / 0.9e1 * t328 * t593 + 0.720e3 * t337 * t234 * t192 - 0.1320e4 * t347 * t251 + 0.1680e4 * t233 * t245 * t181 * t248 + 0.336e3 * t125 * t245 * t192 * t248 + 0.960e3 * t337 * t130 * t307 * t132 - 0.2464e4 * t125 * t245 * t196 * t616 + 0.2464e4 / 0.3e1 * t125 * t130 * params.eta * t622 - 0.264e3 * t351 * t251 + 0.72e2 * t317 * t296 * t132
  t646 = 0.1e1 / t19 / t280 / r0
  t647 = t31 * t646
  t651 = t32 * t563
  t658 = t196 ** 2
  t659 = t159 ** 2
  t663 = 0.1e1 / t20 / t280 / t561
  t671 = t48 * t226
  t696 = t49 * t72
  t703 = t659 * t663 * t32
  t706 = t198 * t646
  t711 = 0.48e2 * t125 * t130 * t303 * t132 + 0.720e3 * t233 * t237 * t192 * params.eta * t102 - 0.132e3 * t318 * t251 - 0.66e2 * t321 * t251 + 0.27412e5 / 0.27e2 * t246 * t247 * t647 - 0.5236e4 / 0.27e2 * t131 * t53 * t651 + 0.448e3 / 0.3e1 * t69 / t244 / t57 * t658 * t659 * t663 * t32 + 0.616e3 / 0.3e1 * t195 * params.eta * t622 + 0.96e2 * t671 * t181 * t248 + 0.48e2 * t324 * t192 * t248 + 0.3584e4 / 0.3e1 * t125 * t359 * t104 * t329 * t330 * t333 + 0.12e2 * t195 * t303 * t132 - 0.352e3 * t324 * t196 * t616 - 0.9856e4 / 0.9e1 * t360 * t593 + 0.24e2 * t307 * t120 * params.eta * t102 + 0.320e3 / 0.3e1 * t696 * t104 * t334 + 0.160e3 / 0.9e1 * t63 * t130 * t658 * t703 + 0.7832e4 / 0.27e2 * t228 * t706 - 0.2618e4 / 0.27e2 * t122 * t564
  t755 = -0.16e2 * t181 * t120 * t196 * t199 - 0.256e3 / 0.9e1 * t671 * t104 * t334 + 0.704e3 / 0.9e1 * t324 * t593 - 0.160e3 / 0.27e2 * t696 * t658 * t703 + 0.352e3 / 0.3e1 * t386 * t284 + 0.88e2 / 0.3e1 * t389 * t251 - 0.2464e4 / 0.27e2 * t185 * t291 + 0.5236e4 / 0.81e2 * t108 * t564 - 0.16e2 * t104 * t65 * t192 * t132 + 0.88e2 / 0.3e1 * t383 * t190 - 0.16e2 * t317 * t192 * t248 - 0.16e2 / 0.3e1 * t184 * t303 * t132 - 0.3916e4 / 0.27e2 * t197 * t706 - 0.6e1 * t571 * t58 - 0.8e1 * t379 * t303 - 0.2e1 * t99 * t566
  t765 = t592 * t416
  t768 = 0.176000e6 / 0.129140163e9 * t414 * t765 * t38
  t773 = t413 * t659 * t663 / t415 / params.kappa
  t777 = 0.80000e5 / 0.94143178827e11 * t773 * t29 * t32 * t38
  t781 = 0.195800e6 / 0.4782969e7 * t160 * t647 * t165
  t794 = 0.26180e5 / 0.19683e5 * t30 * t651 * t38
  t815 = t211 ** 2
  t822 = t204 ** 2
  t829 = t254 ** 2
  t833 = -t781 + 0.72e2 * t459 * t84 * t111 * t254 * t135 - 0.72e2 * t446 * t84 * t111 * t135 * t204 + t794 + 0.24e2 * t367 * t141 + t76 * (0.26180e5 / 0.19683e5 * t30 * t651 * t81 - 0.195800e6 / 0.4782969e7 * t160 * t647 * t260 + 0.176000e6 / 0.129140163e9 * t414 * t765 * t81 - 0.80000e5 / 0.94143178827e11 * t773 * t29 * t32 * t81 - t794 + t781 - t768 + t777) + 0.24e2 * t62 / t436 / t74 * t84 * t815 + 0.36e2 * t170 * t75 * t205 + 0.18e2 * t169 * t84 * t822 - 0.24e2 * t438 * t141 * t439 + 0.6e1 * t210 * t84 * t829
  t840 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t93 * t86 - 0.5e1 / 0.9e1 * t6 * t23 * t143 + t6 * t90 * t266 / 0.2e1 - t6 * t148 * t464 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t270 * (t546 + 0.18e2 * t98 * t264 * t204 - 0.6e1 * t117 * t264 * t254 - 0.24e2 * t366 * t116 * t136 + 0.36e2 * t169 * t264 * t170 - t117 * t84 * (t630 + t711) + 0.3e1 * t98 * t84 * t755 - 0.4e1 * t117 * t141 * t363 - 0.18e2 * t174 * t205 * t254 + t768 - t777 + t833))
  v4rho4_0_ = 0.2e1 * r0 * t840 + 0.8e1 * t469

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
  t30 = t6 ** (0.1e1 / 0.3e1)
  t31 = t29 * t30
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = t32 / t35
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t43 = s0 * t42
  t44 = 0.1e1 / params.kappa
  t48 = jnp.exp(-0.5e1 / 0.972e3 * t37 * t43 * t44)
  t50 = params.kappa * (0.1e1 - t48)
  t55 = tau0 / t40 / r0 - t43 / 0.8e1
  t56 = t55 ** 2
  t57 = t32 ** 2
  t59 = 0.3e1 / 0.10e2 * t57 * t35
  t60 = params.eta * s0
  t63 = t59 + t60 * t42 / 0.8e1
  t64 = t63 ** 2
  t65 = 0.1e1 / t64
  t67 = -t56 * t65 + 0.1e1
  t68 = t67 ** 2
  t69 = t68 * t67
  t70 = t56 * t55
  t71 = t64 * t63
  t72 = 0.1e1 / t71
  t74 = t56 ** 2
  t76 = params.b * t74 * t56
  t77 = t64 ** 2
  t79 = 0.1e1 / t77 / t64
  t81 = t70 * t72 + t76 * t79 + 0.1e1
  t82 = 0.1e1 / t81
  t83 = t69 * t82
  t88 = jnp.exp(-(0.5e1 / 0.972e3 * t37 * t43 + params.c) * t44)
  t91 = params.kappa * (0.1e1 - t88) - t50
  t93 = t83 * t91 + t50 + 0.1e1
  t97 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t98 = t97 * f.p.zeta_threshold
  t100 = f.my_piecewise3(t20, t98, t21 * t19)
  t101 = t30 ** 2
  t102 = 0.1e1 / t101
  t103 = t100 * t102
  t106 = t5 * t103 * t93 / 0.8e1
  t107 = t100 * t30
  t108 = t38 * r0
  t110 = 0.1e1 / t40 / t108
  t111 = s0 * t110
  t113 = t37 * t111 * t48
  t115 = t68 * t82
  t116 = t55 * t65
  t120 = -0.5e1 / 0.3e1 * tau0 * t42 + t111 / 0.3e1
  t123 = t56 * t72
  t124 = t60 * t110
  t127 = -0.2e1 * t116 * t120 - 0.2e1 / 0.3e1 * t123 * t124
  t128 = t91 * t127
  t131 = t81 ** 2
  t132 = 0.1e1 / t131
  t133 = t69 * t132
  t136 = 0.1e1 / t77
  t137 = t70 * t136
  t140 = params.b * t74 * t55
  t145 = 0.1e1 / t77 / t71
  t146 = t76 * t145
  t149 = 0.6e1 * t140 * t79 * t120 + 0.3e1 * t123 * t120 + t137 * t124 + 0.2e1 * t146 * t124
  t155 = -0.10e2 / 0.729e3 * t37 * t111 * t88 + 0.10e2 / 0.729e3 * t113
  t157 = -0.10e2 / 0.729e3 * t113 + 0.3e1 * t115 * t128 - t133 * t91 * t149 + t83 * t155
  t162 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t93 - t106 - 0.3e1 / 0.8e1 * t5 * t107 * t157)
  t164 = r1 <= f.p.dens_threshold
  t165 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t166 = 0.1e1 + t165
  t167 = t166 <= f.p.zeta_threshold
  t168 = t166 ** (0.1e1 / 0.3e1)
  t170 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t173 = f.my_piecewise3(t167, 0, 0.4e1 / 0.3e1 * t168 * t170)
  t174 = t173 * t30
  t175 = r1 ** 2
  t176 = r1 ** (0.1e1 / 0.3e1)
  t177 = t176 ** 2
  t179 = 0.1e1 / t177 / t175
  t180 = s2 * t179
  t184 = jnp.exp(-0.5e1 / 0.972e3 * t37 * t180 * t44)
  t186 = params.kappa * (0.1e1 - t184)
  t191 = tau1 / t177 / r1 - t180 / 0.8e1
  t192 = t191 ** 2
  t193 = params.eta * s2
  t196 = t59 + t193 * t179 / 0.8e1
  t197 = t196 ** 2
  t198 = 0.1e1 / t197
  t200 = -t192 * t198 + 0.1e1
  t201 = t200 ** 2
  t202 = t201 * t200
  t203 = t192 * t191
  t204 = t197 * t196
  t205 = 0.1e1 / t204
  t207 = t192 ** 2
  t209 = params.b * t207 * t192
  t210 = t197 ** 2
  t212 = 0.1e1 / t210 / t197
  t214 = t203 * t205 + t209 * t212 + 0.1e1
  t215 = 0.1e1 / t214
  t216 = t202 * t215
  t221 = jnp.exp(-(0.5e1 / 0.972e3 * t37 * t180 + params.c) * t44)
  t224 = params.kappa * (0.1e1 - t221) - t186
  t226 = t216 * t224 + t186 + 0.1e1
  t231 = f.my_piecewise3(t167, t98, t168 * t166)
  t232 = t231 * t102
  t235 = t5 * t232 * t226 / 0.8e1
  t237 = f.my_piecewise3(t164, 0, -0.3e1 / 0.8e1 * t5 * t174 * t226 - t235)
  t239 = t21 ** 2
  t240 = 0.1e1 / t239
  t241 = t26 ** 2
  t246 = t16 / t22 / t6
  t248 = -0.2e1 * t23 + 0.2e1 * t246
  t249 = f.my_piecewise5(t10, 0, t14, 0, t248)
  t253 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t240 * t241 + 0.4e1 / 0.3e1 * t21 * t249)
  t260 = t5 * t29 * t102 * t93
  t266 = 0.1e1 / t101 / t6
  t270 = t5 * t100 * t266 * t93 / 0.12e2
  t272 = t5 * t103 * t157
  t274 = t38 ** 2
  t276 = 0.1e1 / t40 / t274
  t277 = s0 * t276
  t280 = 0.110e3 / 0.2187e4 * t37 * t277 * t48
  t283 = t57 / t34 / t33
  t284 = s0 ** 2
  t285 = t283 * t284
  t288 = 0.1e1 / t39 / t274 / t108
  t289 = t288 * t44
  t292 = 0.100e3 / 0.531441e6 * t285 * t289 * t48
  t294 = t127 ** 2
  t305 = t120 ** 2
  t308 = t55 * t72
  t315 = 0.40e2 / 0.9e1 * tau0 * t110 - 0.11e2 / 0.9e1 * t277
  t318 = t56 * t136
  t319 = params.eta ** 2
  t321 = t319 * t284 * t288
  t324 = t60 * t276
  t334 = t149 ** 2
  t367 = t77 ** 2
  t390 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t253 * t30 * t93 - t260 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t157 + t270 - t272 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t107 * (t280 - t292 + 0.6e1 * t67 * t82 * t91 * t294 - 0.6e1 * t68 * t132 * t128 * t149 + 0.6e1 * t115 * t155 * t127 + 0.3e1 * t115 * t91 * (-0.2e1 * t305 * t65 - 0.8e1 / 0.3e1 * t308 * t120 * t124 - 0.2e1 * t116 * t315 - 0.2e1 / 0.3e1 * t318 * t321 + 0.22e2 / 0.9e1 * t123 * t324) + 0.2e1 * t69 / t131 / t81 * t91 * t334 - 0.2e1 * t133 * t155 * t149 - t133 * t91 * (0.6e1 * t308 * t305 + 0.6e1 * t318 * t120 * t124 + 0.3e1 * t123 * t315 + 0.4e1 / 0.3e1 * t70 / t77 / t63 * t321 - 0.11e2 / 0.3e1 * t137 * t324 + 0.30e2 * params.b * t74 * t79 * t305 + 0.24e2 * t140 * t145 * t120 * params.eta * t111 + 0.6e1 * t140 * t79 * t315 + 0.14e2 / 0.3e1 * t76 / t367 * t321 - 0.22e2 / 0.3e1 * t146 * t324) + t83 * (0.110e3 / 0.2187e4 * t37 * t277 * t88 - 0.100e3 / 0.531441e6 * t285 * t289 * t88 - t280 + t292)))
  t391 = t168 ** 2
  t392 = 0.1e1 / t391
  t393 = t170 ** 2
  t397 = f.my_piecewise5(t14, 0, t10, 0, -t248)
  t401 = f.my_piecewise3(t167, 0, 0.4e1 / 0.9e1 * t392 * t393 + 0.4e1 / 0.3e1 * t168 * t397)
  t408 = t5 * t173 * t102 * t226
  t413 = t5 * t231 * t266 * t226 / 0.12e2
  t415 = f.my_piecewise3(t164, 0, -0.3e1 / 0.8e1 * t5 * t401 * t30 * t226 - t408 / 0.4e1 + t413)
  d11 = 0.2e1 * t162 + 0.2e1 * t237 + t6 * (t390 + t415)
  t418 = -t7 - t24
  t419 = f.my_piecewise5(t10, 0, t14, 0, t418)
  t422 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t419)
  t423 = t422 * t30
  t428 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t423 * t93 - t106)
  t430 = f.my_piecewise5(t14, 0, t10, 0, -t418)
  t433 = f.my_piecewise3(t167, 0, 0.4e1 / 0.3e1 * t168 * t430)
  t434 = t433 * t30
  t438 = t231 * t30
  t439 = t175 * r1
  t441 = 0.1e1 / t177 / t439
  t442 = s2 * t441
  t444 = t37 * t442 * t184
  t446 = t201 * t215
  t447 = t191 * t198
  t451 = -0.5e1 / 0.3e1 * tau1 * t179 + t442 / 0.3e1
  t454 = t192 * t205
  t455 = t193 * t441
  t458 = -0.2e1 * t447 * t451 - 0.2e1 / 0.3e1 * t454 * t455
  t459 = t224 * t458
  t462 = t214 ** 2
  t463 = 0.1e1 / t462
  t464 = t202 * t463
  t467 = 0.1e1 / t210
  t468 = t203 * t467
  t471 = params.b * t207 * t191
  t476 = 0.1e1 / t210 / t204
  t477 = t209 * t476
  t480 = 0.6e1 * t471 * t212 * t451 + 0.3e1 * t454 * t451 + t468 * t455 + 0.2e1 * t477 * t455
  t486 = -0.10e2 / 0.729e3 * t37 * t442 * t221 + 0.10e2 / 0.729e3 * t444
  t488 = -0.10e2 / 0.729e3 * t444 + 0.3e1 * t446 * t459 - t464 * t224 * t480 + t216 * t486
  t493 = f.my_piecewise3(t164, 0, -0.3e1 / 0.8e1 * t5 * t434 * t226 - t235 - 0.3e1 / 0.8e1 * t5 * t438 * t488)
  t497 = 0.2e1 * t246
  t498 = f.my_piecewise5(t10, 0, t14, 0, t497)
  t502 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t240 * t419 * t26 + 0.4e1 / 0.3e1 * t21 * t498)
  t509 = t5 * t422 * t102 * t93
  t517 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t502 * t30 * t93 - t509 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t423 * t157 - t260 / 0.8e1 + t270 - t272 / 0.8e1)
  t521 = f.my_piecewise5(t14, 0, t10, 0, -t497)
  t525 = f.my_piecewise3(t167, 0, 0.4e1 / 0.9e1 * t392 * t430 * t170 + 0.4e1 / 0.3e1 * t168 * t521)
  t532 = t5 * t433 * t102 * t226
  t539 = t5 * t232 * t488
  t542 = f.my_piecewise3(t164, 0, -0.3e1 / 0.8e1 * t5 * t525 * t30 * t226 - t532 / 0.8e1 - t408 / 0.8e1 + t413 - 0.3e1 / 0.8e1 * t5 * t174 * t488 - t539 / 0.8e1)
  d12 = t162 + t237 + t428 + t493 + t6 * (t517 + t542)
  t547 = t419 ** 2
  t551 = 0.2e1 * t23 + 0.2e1 * t246
  t552 = f.my_piecewise5(t10, 0, t14, 0, t551)
  t556 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t240 * t547 + 0.4e1 / 0.3e1 * t21 * t552)
  t563 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t556 * t30 * t93 - t509 / 0.4e1 + t270)
  t564 = t430 ** 2
  t568 = f.my_piecewise5(t14, 0, t10, 0, -t551)
  t572 = f.my_piecewise3(t167, 0, 0.4e1 / 0.9e1 * t392 * t564 + 0.4e1 / 0.3e1 * t168 * t568)
  t582 = t175 ** 2
  t584 = 0.1e1 / t177 / t582
  t585 = s2 * t584
  t588 = 0.110e3 / 0.2187e4 * t37 * t585 * t184
  t589 = s2 ** 2
  t590 = t283 * t589
  t593 = 0.1e1 / t176 / t582 / t439
  t594 = t593 * t44
  t597 = 0.100e3 / 0.531441e6 * t590 * t594 * t184
  t599 = t458 ** 2
  t610 = t451 ** 2
  t613 = t191 * t205
  t620 = 0.40e2 / 0.9e1 * tau1 * t441 - 0.11e2 / 0.9e1 * t585
  t623 = t192 * t467
  t625 = t319 * t589 * t593
  t628 = t193 * t584
  t638 = t480 ** 2
  t671 = t210 ** 2
  t694 = f.my_piecewise3(t164, 0, -0.3e1 / 0.8e1 * t5 * t572 * t30 * t226 - t532 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t434 * t488 + t413 - t539 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t438 * (t588 - t597 + 0.6e1 * t200 * t215 * t224 * t599 - 0.6e1 * t201 * t463 * t459 * t480 + 0.6e1 * t446 * t486 * t458 + 0.3e1 * t446 * t224 * (-0.2e1 * t610 * t198 - 0.8e1 / 0.3e1 * t613 * t451 * t455 - 0.2e1 * t447 * t620 - 0.2e1 / 0.3e1 * t623 * t625 + 0.22e2 / 0.9e1 * t454 * t628) + 0.2e1 * t202 / t462 / t214 * t224 * t638 - 0.2e1 * t464 * t486 * t480 - t464 * t224 * (0.6e1 * t613 * t610 + 0.6e1 * t623 * t451 * t455 + 0.3e1 * t454 * t620 + 0.4e1 / 0.3e1 * t203 / t210 / t196 * t625 - 0.11e2 / 0.3e1 * t468 * t628 + 0.30e2 * params.b * t207 * t212 * t610 + 0.24e2 * t471 * t476 * t451 * params.eta * t442 + 0.6e1 * t471 * t212 * t620 + 0.14e2 / 0.3e1 * t209 / t671 * t625 - 0.22e2 / 0.3e1 * t477 * t628) + t216 * (0.110e3 / 0.2187e4 * t37 * t585 * t221 - 0.100e3 / 0.531441e6 * t590 * t594 * t221 - t588 + t597)))
  d22 = 0.2e1 * t428 + 0.2e1 * t493 + t6 * (t563 + t694)
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
  t42 = t6 ** (0.1e1 / 0.3e1)
  t43 = t41 * t42
  t44 = 6 ** (0.1e1 / 0.3e1)
  t45 = jnp.pi ** 2
  t46 = t45 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t49 = t44 / t47
  t50 = r0 ** 2
  t51 = r0 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t54 = 0.1e1 / t52 / t50
  t55 = s0 * t54
  t56 = 0.1e1 / params.kappa
  t60 = jnp.exp(-0.5e1 / 0.972e3 * t49 * t55 * t56)
  t62 = params.kappa * (0.1e1 - t60)
  t67 = tau0 / t52 / r0 - t55 / 0.8e1
  t68 = t67 ** 2
  t69 = t44 ** 2
  t71 = 0.3e1 / 0.10e2 * t69 * t47
  t72 = params.eta * s0
  t75 = t71 + t72 * t54 / 0.8e1
  t76 = t75 ** 2
  t77 = 0.1e1 / t76
  t79 = -t68 * t77 + 0.1e1
  t80 = t79 ** 2
  t81 = t80 * t79
  t82 = t68 * t67
  t83 = t76 * t75
  t84 = 0.1e1 / t83
  t86 = t68 ** 2
  t88 = params.b * t86 * t68
  t89 = t76 ** 2
  t91 = 0.1e1 / t89 / t76
  t93 = t82 * t84 + t88 * t91 + 0.1e1
  t94 = 0.1e1 / t93
  t95 = t81 * t94
  t100 = jnp.exp(-(0.5e1 / 0.972e3 * t49 * t55 + params.c) * t56)
  t103 = params.kappa * (0.1e1 - t100) - t62
  t105 = t95 * t103 + t62 + 0.1e1
  t111 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t112 = t42 ** 2
  t113 = 0.1e1 / t112
  t114 = t111 * t113
  t118 = t111 * t42
  t119 = t50 * r0
  t121 = 0.1e1 / t52 / t119
  t122 = s0 * t121
  t124 = t49 * t122 * t60
  t126 = t80 * t94
  t127 = t67 * t77
  t131 = -0.5e1 / 0.3e1 * tau0 * t54 + t122 / 0.3e1
  t134 = t68 * t84
  t135 = t72 * t121
  t138 = -0.2e1 * t127 * t131 - 0.2e1 / 0.3e1 * t134 * t135
  t139 = t103 * t138
  t142 = t93 ** 2
  t143 = 0.1e1 / t142
  t144 = t81 * t143
  t147 = 0.1e1 / t89
  t148 = t82 * t147
  t151 = params.b * t86 * t67
  t152 = t91 * t131
  t156 = 0.1e1 / t89 / t83
  t157 = t88 * t156
  t160 = 0.3e1 * t134 * t131 + t148 * t135 + 0.2e1 * t157 * t135 + 0.6e1 * t151 * t152
  t161 = t103 * t160
  t166 = -0.10e2 / 0.729e3 * t49 * t122 * t100 + 0.10e2 / 0.729e3 * t124
  t168 = -0.10e2 / 0.729e3 * t124 + 0.3e1 * t126 * t139 - t144 * t161 + t95 * t166
  t172 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t173 = t172 * f.p.zeta_threshold
  t175 = f.my_piecewise3(t20, t173, t21 * t19)
  t177 = 0.1e1 / t112 / t6
  t178 = t175 * t177
  t182 = t175 * t113
  t186 = t175 * t42
  t187 = t50 ** 2
  t189 = 0.1e1 / t52 / t187
  t190 = s0 * t189
  t193 = 0.110e3 / 0.2187e4 * t49 * t190 * t60
  t197 = s0 ** 2
  t198 = t69 / t46 / t45 * t197
  t201 = 0.1e1 / t51 / t187 / t119
  t202 = t201 * t56
  t205 = 0.100e3 / 0.531441e6 * t198 * t202 * t60
  t206 = t79 * t94
  t207 = t138 ** 2
  t208 = t103 * t207
  t211 = t80 * t143
  t215 = t166 * t138
  t218 = t131 ** 2
  t221 = t67 * t84
  t222 = t221 * t131
  t228 = 0.40e2 / 0.9e1 * tau0 * t121 - 0.11e2 / 0.9e1 * t190
  t231 = t68 * t147
  t232 = params.eta ** 2
  t233 = t232 * t197
  t234 = t233 * t201
  t237 = t72 * t189
  t240 = -0.2e1 * t218 * t77 - 0.8e1 / 0.3e1 * t222 * t135 - 0.2e1 * t127 * t228 - 0.2e1 / 0.3e1 * t231 * t234 + 0.22e2 / 0.9e1 * t134 * t237
  t241 = t103 * t240
  t245 = 0.1e1 / t142 / t93
  t246 = t81 * t245
  t247 = t160 ** 2
  t256 = t231 * t131
  t262 = 0.1e1 / t89 / t75
  t263 = t82 * t262
  t268 = params.b * t86
  t272 = t151 * t156
  t273 = t131 * params.eta
  t280 = t89 ** 2
  t281 = 0.1e1 / t280
  t282 = t88 * t281
  t287 = 0.6e1 * t221 * t218 + 0.6e1 * t256 * t135 + 0.3e1 * t134 * t228 + 0.4e1 / 0.3e1 * t263 * t234 - 0.11e2 / 0.3e1 * t148 * t237 + 0.30e2 * t268 * t91 * t218 + 0.24e2 * t272 * t273 * t122 + 0.6e1 * t151 * t91 * t228 + 0.14e2 / 0.3e1 * t282 * t234 - 0.22e2 / 0.3e1 * t157 * t237
  t296 = 0.110e3 / 0.2187e4 * t49 * t190 * t100 - 0.100e3 / 0.531441e6 * t198 * t202 * t100 - t193 + t205
  t298 = -t144 * t103 * t287 + 0.2e1 * t246 * t103 * t247 - 0.6e1 * t211 * t139 * t160 - 0.2e1 * t144 * t166 * t160 + 0.6e1 * t126 * t215 + 0.3e1 * t126 * t241 + 0.6e1 * t206 * t208 + t95 * t296 + t193 - t205
  t303 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t105 - t5 * t114 * t105 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t118 * t168 + t5 * t178 * t105 / 0.12e2 - t5 * t182 * t168 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t186 * t298)
  t305 = r1 <= f.p.dens_threshold
  t306 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t307 = 0.1e1 + t306
  t308 = t307 <= f.p.zeta_threshold
  t309 = t307 ** (0.1e1 / 0.3e1)
  t310 = t309 ** 2
  t311 = 0.1e1 / t310
  t313 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t314 = t313 ** 2
  t318 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t322 = f.my_piecewise3(t308, 0, 0.4e1 / 0.9e1 * t311 * t314 + 0.4e1 / 0.3e1 * t309 * t318)
  t324 = r1 ** 2
  t325 = r1 ** (0.1e1 / 0.3e1)
  t326 = t325 ** 2
  t328 = 0.1e1 / t326 / t324
  t329 = s2 * t328
  t333 = jnp.exp(-0.5e1 / 0.972e3 * t49 * t329 * t56)
  t335 = params.kappa * (0.1e1 - t333)
  t340 = tau1 / t326 / r1 - t329 / 0.8e1
  t341 = t340 ** 2
  t345 = t71 + params.eta * s2 * t328 / 0.8e1
  t346 = t345 ** 2
  t349 = 0.1e1 - t341 / t346
  t350 = t349 ** 2
  t356 = t341 ** 2
  t359 = t346 ** 2
  t370 = jnp.exp(-(0.5e1 / 0.972e3 * t49 * t329 + params.c) * t56)
  t375 = 0.1e1 + t335 + t350 * t349 / (0.1e1 + t341 * t340 / t346 / t345 + params.b * t356 * t341 / t359 / t346) * (params.kappa * (0.1e1 - t370) - t335)
  t381 = f.my_piecewise3(t308, 0, 0.4e1 / 0.3e1 * t309 * t313)
  t387 = f.my_piecewise3(t308, t173, t309 * t307)
  t393 = f.my_piecewise3(t305, 0, -0.3e1 / 0.8e1 * t5 * t322 * t42 * t375 - t5 * t381 * t113 * t375 / 0.4e1 + t5 * t387 * t177 * t375 / 0.12e2)
  t403 = t24 ** 2
  t407 = 0.6e1 * t33 - 0.6e1 * t16 / t403
  t408 = f.my_piecewise5(t10, 0, t14, 0, t407)
  t412 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t408)
  t435 = 0.1e1 / t112 / t24
  t448 = 0.1e1 / t52 / t187 / r0
  t449 = s0 * t448
  t453 = t187 ** 2
  t455 = 0.1e1 / t51 / t453
  t456 = t455 * t56
  t460 = t45 ** 2
  t462 = t197 * s0
  t463 = 0.1e1 / t460 * t462
  t465 = 0.1e1 / t453 / t119
  t466 = params.kappa ** 2
  t468 = t465 / t466
  t474 = 0.1540e4 / 0.6561e4 * t49 * t449 * t60
  t477 = 0.1100e4 / 0.531441e6 * t198 * t456 * t60
  t480 = 0.2000e4 / 0.129140163e9 * t463 * t468 * t60
  t499 = t142 ** 2
  t529 = t67 * t147
  t541 = -0.440e3 / 0.27e2 * tau0 * t189 + 0.154e3 / 0.27e2 * t449
  t544 = t68 * t262
  t547 = t232 * params.eta * t462 * t465
  t550 = t233 * t455
  t553 = t72 * t448
  t569 = t218 * t131
  t632 = 0.6e1 * t569 * t84 + 0.3e1 * t134 * t541 + 0.84e2 * t151 * t281 * t131 * t232 * t197 * t201 - 0.154e3 / 0.3e1 * t282 * t550 + 0.308e3 / 0.9e1 * t157 * t553 - 0.33e2 * t256 * t237 + 0.180e3 * t268 * t156 * t218 * params.eta * t122 + 0.36e2 * t272 * t228 * params.eta * t122 + 0.20e2 / 0.9e1 * t82 * t91 * t547 + 0.120e3 * params.b * t82 * t91 * t569 + 0.90e2 * t268 * t152 * t228 - 0.132e3 * t272 * t273 * t190 + 0.18e2 * t221 * t131 * t228 + 0.6e1 * t151 * t91 * t541 + 0.18e2 * t529 * t218 * t135 + 0.9e1 * t231 * t228 * t135 + 0.12e2 * t544 * t131 * t234 - 0.44e2 / 0.3e1 * t263 * t550 + 0.154e3 / 0.9e1 * t148 * t553 + 0.112e3 / 0.9e1 * t88 / t280 / t75 * t547
  t639 = 0.18e2 * t206 * t166 * t207 + 0.9e1 * t126 * t296 * t138 + 0.9e1 * t126 * t166 * t240 + 0.3e1 * t126 * t103 * (-0.6e1 * t131 * t77 * t228 - 0.4e1 * t218 * t84 * t135 - 0.4e1 * t529 * t131 * t234 - 0.4e1 * t221 * t228 * t135 + 0.44e2 / 0.3e1 * t222 * t237 - 0.2e1 * t127 * t541 - 0.8e1 / 0.9e1 * t544 * t547 + 0.22e2 / 0.3e1 * t231 * t550 - 0.308e3 / 0.27e2 * t134 * t553) + 0.6e1 * t246 * t166 * t247 - 0.3e1 * t144 * t296 * t160 - 0.3e1 * t144 * t166 * t287 - t144 * t103 * t632 - t474 + t477 + 0.18e2 * t80 * t245 * t139 * t247
  t645 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t412 * t42 * t105 - 0.3e1 / 0.8e1 * t5 * t41 * t113 * t105 - 0.9e1 / 0.8e1 * t5 * t43 * t168 + t5 * t111 * t177 * t105 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t114 * t168 - 0.9e1 / 0.8e1 * t5 * t118 * t298 - 0.5e1 / 0.36e2 * t5 * t175 * t435 * t105 + t5 * t178 * t168 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t182 * t298 - 0.3e1 / 0.8e1 * t5 * t186 * (t95 * (-0.1540e4 / 0.6561e4 * t49 * t449 * t100 + 0.1100e4 / 0.531441e6 * t198 * t456 * t100 - 0.2000e4 / 0.129140163e9 * t463 * t468 * t100 + t474 - t477 + t480) - t480 - 0.18e2 * t79 * t143 * t208 * t160 + 0.18e2 * t206 * t139 * t240 - 0.18e2 * t211 * t215 * t160 - 0.9e1 * t211 * t241 * t160 - 0.9e1 * t211 * t139 * t287 - 0.6e1 * t81 / t499 * t103 * t247 * t160 + 0.6e1 * t246 * t161 * t287 + 0.6e1 * t207 * t138 * t94 * t103 + t639))
  t655 = f.my_piecewise5(t14, 0, t10, 0, -t407)
  t659 = f.my_piecewise3(t308, 0, -0.8e1 / 0.27e2 / t310 / t307 * t314 * t313 + 0.4e1 / 0.3e1 * t311 * t313 * t318 + 0.4e1 / 0.3e1 * t309 * t655)
  t677 = f.my_piecewise3(t305, 0, -0.3e1 / 0.8e1 * t5 * t659 * t42 * t375 - 0.3e1 / 0.8e1 * t5 * t322 * t113 * t375 + t5 * t381 * t177 * t375 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t387 * t435 * t375)
  d111 = 0.3e1 * t303 + 0.3e1 * t393 + t6 * (t645 + t677)

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
  t22 = t21 ** 2
  t24 = 0.1e1 / t22 / t19
  t25 = t6 ** 2
  t26 = 0.1e1 / t25
  t28 = -t16 * t26 + t7
  t29 = f.my_piecewise5(t10, 0, t14, 0, t28)
  t30 = t29 ** 2
  t34 = 0.1e1 / t22
  t35 = t34 * t29
  t36 = t25 * t6
  t37 = 0.1e1 / t36
  t40 = 0.2e1 * t16 * t37 - 0.2e1 * t26
  t41 = f.my_piecewise5(t10, 0, t14, 0, t40)
  t44 = t25 ** 2
  t45 = 0.1e1 / t44
  t48 = -0.6e1 * t16 * t45 + 0.6e1 * t37
  t49 = f.my_piecewise5(t10, 0, t14, 0, t48)
  t53 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t24 * t30 * t29 + 0.4e1 / 0.3e1 * t35 * t41 + 0.4e1 / 0.3e1 * t21 * t49)
  t54 = t6 ** (0.1e1 / 0.3e1)
  t55 = t53 * t54
  t56 = 6 ** (0.1e1 / 0.3e1)
  t57 = jnp.pi ** 2
  t58 = t57 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t60 = 0.1e1 / t59
  t61 = t56 * t60
  t62 = r0 ** 2
  t63 = r0 ** (0.1e1 / 0.3e1)
  t64 = t63 ** 2
  t66 = 0.1e1 / t64 / t62
  t67 = s0 * t66
  t68 = 0.1e1 / params.kappa
  t72 = jnp.exp(-0.5e1 / 0.972e3 * t61 * t67 * t68)
  t74 = params.kappa * (0.1e1 - t72)
  t79 = tau0 / t64 / r0 - t67 / 0.8e1
  t80 = t79 ** 2
  t81 = t56 ** 2
  t83 = 0.3e1 / 0.10e2 * t81 * t59
  t84 = params.eta * s0
  t87 = t83 + t84 * t66 / 0.8e1
  t88 = t87 ** 2
  t89 = 0.1e1 / t88
  t91 = -t80 * t89 + 0.1e1
  t92 = t91 ** 2
  t93 = t92 * t91
  t94 = t80 * t79
  t95 = t88 * t87
  t96 = 0.1e1 / t95
  t98 = t80 ** 2
  t100 = params.b * t98 * t80
  t101 = t88 ** 2
  t103 = 0.1e1 / t101 / t88
  t105 = t100 * t103 + t94 * t96 + 0.1e1
  t106 = 0.1e1 / t105
  t107 = t93 * t106
  t112 = jnp.exp(-(0.5e1 / 0.972e3 * t61 * t67 + params.c) * t68)
  t115 = params.kappa * (0.1e1 - t112) - t74
  t117 = t107 * t115 + t74 + 0.1e1
  t126 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t127 = t54 ** 2
  t128 = 0.1e1 / t127
  t129 = t126 * t128
  t133 = t126 * t54
  t134 = t62 * r0
  t136 = 0.1e1 / t64 / t134
  t137 = s0 * t136
  t139 = t61 * t137 * t72
  t141 = t92 * t106
  t142 = t79 * t89
  t146 = -0.5e1 / 0.3e1 * tau0 * t66 + t137 / 0.3e1
  t149 = t80 * t96
  t150 = t84 * t136
  t153 = -0.2e1 * t142 * t146 - 0.2e1 / 0.3e1 * t149 * t150
  t154 = t115 * t153
  t157 = t105 ** 2
  t158 = 0.1e1 / t157
  t159 = t93 * t158
  t162 = 0.1e1 / t101
  t163 = t94 * t162
  t166 = params.b * t98 * t79
  t167 = t103 * t146
  t171 = 0.1e1 / t101 / t95
  t172 = t100 * t171
  t175 = 0.3e1 * t149 * t146 + t163 * t150 + 0.2e1 * t172 * t150 + 0.6e1 * t166 * t167
  t176 = t115 * t175
  t181 = -0.10e2 / 0.729e3 * t61 * t137 * t112 + 0.10e2 / 0.729e3 * t139
  t183 = -0.10e2 / 0.729e3 * t139 + 0.3e1 * t141 * t154 - t159 * t176 + t107 * t181
  t189 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t191 = 0.1e1 / t127 / t6
  t192 = t189 * t191
  t196 = t189 * t128
  t200 = t189 * t54
  t201 = t62 ** 2
  t203 = 0.1e1 / t64 / t201
  t204 = s0 * t203
  t207 = 0.110e3 / 0.2187e4 * t61 * t204 * t72
  t211 = s0 ** 2
  t212 = t81 / t58 / t57 * t211
  t215 = 0.1e1 / t63 / t201 / t134
  t216 = t215 * t68
  t219 = 0.100e3 / 0.531441e6 * t212 * t216 * t72
  t220 = t91 * t106
  t221 = t153 ** 2
  t222 = t115 * t221
  t225 = t92 * t158
  t229 = t181 * t153
  t232 = t146 ** 2
  t235 = t79 * t96
  t236 = t235 * t146
  t242 = 0.40e2 / 0.9e1 * tau0 * t136 - 0.11e2 / 0.9e1 * t204
  t245 = t80 * t162
  t246 = params.eta ** 2
  t247 = t246 * t211
  t248 = t247 * t215
  t251 = t84 * t203
  t254 = -0.2e1 * t232 * t89 - 0.8e1 / 0.3e1 * t236 * t150 - 0.2e1 * t142 * t242 - 0.2e1 / 0.3e1 * t245 * t248 + 0.22e2 / 0.9e1 * t149 * t251
  t255 = t115 * t254
  t259 = 0.1e1 / t157 / t105
  t260 = t93 * t259
  t261 = t175 ** 2
  t262 = t115 * t261
  t265 = t181 * t175
  t270 = t245 * t146
  t276 = 0.1e1 / t101 / t87
  t277 = t94 * t276
  t282 = params.b * t98
  t283 = t103 * t232
  t286 = t166 * t171
  t287 = t146 * params.eta
  t294 = t101 ** 2
  t295 = 0.1e1 / t294
  t296 = t100 * t295
  t301 = 0.6e1 * t235 * t232 + 0.6e1 * t270 * t150 + 0.3e1 * t149 * t242 + 0.4e1 / 0.3e1 * t277 * t248 - 0.11e2 / 0.3e1 * t163 * t251 + 0.30e2 * t282 * t283 + 0.24e2 * t286 * t287 * t137 + 0.6e1 * t166 * t103 * t242 + 0.14e2 / 0.3e1 * t296 * t248 - 0.22e2 / 0.3e1 * t172 * t251
  t310 = 0.110e3 / 0.2187e4 * t61 * t204 * t112 - 0.100e3 / 0.531441e6 * t212 * t216 * t112 - t207 + t219
  t312 = -t159 * t115 * t301 - 0.6e1 * t225 * t154 * t175 + t107 * t310 + 0.6e1 * t141 * t229 + 0.3e1 * t141 * t255 - 0.2e1 * t159 * t265 + 0.6e1 * t220 * t222 + 0.2e1 * t260 * t262 + t207 - t219
  t316 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t317 = t316 * f.p.zeta_threshold
  t319 = f.my_piecewise3(t20, t317, t21 * t19)
  t321 = 0.1e1 / t127 / t25
  t322 = t319 * t321
  t326 = t319 * t191
  t330 = t319 * t128
  t334 = t319 * t54
  t337 = 0.1e1 / t64 / t201 / r0
  t338 = s0 * t337
  t342 = t201 ** 2
  t344 = 0.1e1 / t63 / t342
  t345 = t344 * t68
  t349 = t57 ** 2
  t350 = 0.1e1 / t349
  t351 = t211 * s0
  t352 = t350 * t351
  t354 = 0.1e1 / t342 / t134
  t355 = params.kappa ** 2
  t356 = 0.1e1 / t355
  t357 = t354 * t356
  t363 = 0.1540e4 / 0.6561e4 * t61 * t338 * t72
  t366 = 0.1100e4 / 0.531441e6 * t212 * t345 * t72
  t369 = 0.2000e4 / 0.129140163e9 * t352 * t357 * t72
  t370 = -0.1540e4 / 0.6561e4 * t61 * t338 * t112 + 0.1100e4 / 0.531441e6 * t212 * t345 * t112 - 0.2000e4 / 0.129140163e9 * t352 * t357 * t112 + t363 - t366 + t369
  t372 = t91 * t158
  t388 = t157 ** 2
  t389 = 0.1e1 / t388
  t390 = t93 * t389
  t391 = t261 * t175
  t392 = t115 * t391
  t398 = t221 * t153
  t399 = t398 * t106
  t403 = t181 * t221
  t406 = t310 * t153
  t409 = t181 * t254
  t412 = t146 * t89
  t415 = t232 * t96
  t418 = t79 * t162
  t419 = t418 * t146
  t422 = t235 * t242
  t430 = -0.440e3 / 0.27e2 * tau0 * t203 + 0.154e3 / 0.27e2 * t338
  t433 = t80 * t276
  t434 = t246 * params.eta
  t435 = t434 * t351
  t436 = t435 * t354
  t439 = t247 * t344
  t442 = t84 * t337
  t445 = -0.6e1 * t412 * t242 - 0.4e1 * t415 * t150 - 0.4e1 * t419 * t248 - 0.4e1 * t422 * t150 + 0.44e2 / 0.3e1 * t236 * t251 - 0.2e1 * t142 * t430 - 0.8e1 / 0.9e1 * t433 * t436 + 0.22e2 / 0.3e1 * t245 * t439 - 0.308e3 / 0.27e2 * t149 * t442
  t446 = t115 * t445
  t458 = t232 * t146
  t463 = t166 * t295
  t464 = t146 * t246
  t465 = t211 * t215
  t475 = t282 * t171
  t476 = t232 * params.eta
  t480 = t242 * params.eta
  t481 = t480 * t137
  t484 = t94 * t103
  t487 = params.b * t94
  t503 = t418 * t232
  t506 = t245 * t242
  t509 = t433 * t146
  t517 = 0.1e1 / t294 / t87
  t518 = t100 * t517
  t521 = 0.6e1 * t458 * t96 + 0.3e1 * t149 * t430 + 0.84e2 * t463 * t464 * t465 - 0.154e3 / 0.3e1 * t296 * t439 + 0.308e3 / 0.9e1 * t172 * t442 - 0.33e2 * t270 * t251 + 0.180e3 * t475 * t476 * t137 + 0.36e2 * t286 * t481 + 0.20e2 / 0.9e1 * t484 * t436 + 0.120e3 * t487 * t103 * t458 + 0.90e2 * t282 * t167 * t242 - 0.132e3 * t286 * t287 * t204 + 0.18e2 * t235 * t146 * t242 + 0.6e1 * t166 * t103 * t430 + 0.18e2 * t503 * t150 + 0.9e1 * t506 * t150 + 0.12e2 * t509 * t248 - 0.44e2 / 0.3e1 * t277 * t439 + 0.154e3 / 0.9e1 * t163 * t442 + 0.112e3 / 0.9e1 * t518 * t436
  t524 = t92 * t259
  t528 = -t159 * t115 * t521 + 0.18e2 * t524 * t154 * t261 - 0.3e1 * t159 * t310 * t175 - 0.3e1 * t159 * t181 * t301 + 0.6e1 * t260 * t181 * t261 + 0.9e1 * t141 * t406 + 0.9e1 * t141 * t409 + 0.3e1 * t141 * t446 + 0.18e2 * t220 * t403 - t363 + t366
  t529 = 0.18e2 * t220 * t154 * t254 - 0.9e1 * t225 * t154 * t301 - 0.18e2 * t372 * t222 * t175 - 0.18e2 * t225 * t229 * t175 - 0.9e1 * t225 * t255 * t175 + 0.6e1 * t260 * t176 * t301 + t107 * t370 + 0.6e1 * t399 * t115 - 0.6e1 * t390 * t392 - t369 + t528
  t534 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t117 - 0.3e1 / 0.8e1 * t5 * t129 * t117 - 0.9e1 / 0.8e1 * t5 * t133 * t183 + t5 * t192 * t117 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t196 * t183 - 0.9e1 / 0.8e1 * t5 * t200 * t312 - 0.5e1 / 0.36e2 * t5 * t322 * t117 + t5 * t326 * t183 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t330 * t312 - 0.3e1 / 0.8e1 * t5 * t334 * t529)
  t536 = r1 <= f.p.dens_threshold
  t537 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t538 = 0.1e1 + t537
  t539 = t538 <= f.p.zeta_threshold
  t540 = t538 ** (0.1e1 / 0.3e1)
  t541 = t540 ** 2
  t543 = 0.1e1 / t541 / t538
  t545 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t546 = t545 ** 2
  t550 = 0.1e1 / t541
  t551 = t550 * t545
  t553 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t557 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t561 = f.my_piecewise3(t539, 0, -0.8e1 / 0.27e2 * t543 * t546 * t545 + 0.4e1 / 0.3e1 * t551 * t553 + 0.4e1 / 0.3e1 * t540 * t557)
  t563 = r1 ** 2
  t564 = r1 ** (0.1e1 / 0.3e1)
  t565 = t564 ** 2
  t567 = 0.1e1 / t565 / t563
  t568 = s2 * t567
  t572 = jnp.exp(-0.5e1 / 0.972e3 * t61 * t568 * t68)
  t574 = params.kappa * (0.1e1 - t572)
  t579 = tau1 / t565 / r1 - t568 / 0.8e1
  t580 = t579 ** 2
  t584 = t83 + params.eta * s2 * t567 / 0.8e1
  t585 = t584 ** 2
  t588 = 0.1e1 - t580 / t585
  t589 = t588 ** 2
  t595 = t580 ** 2
  t598 = t585 ** 2
  t609 = jnp.exp(-(0.5e1 / 0.972e3 * t61 * t568 + params.c) * t68)
  t614 = 0.1e1 + t574 + t589 * t588 / (0.1e1 + t580 * t579 / t585 / t584 + params.b * t595 * t580 / t598 / t585) * (params.kappa * (0.1e1 - t609) - t574)
  t623 = f.my_piecewise3(t539, 0, 0.4e1 / 0.9e1 * t550 * t546 + 0.4e1 / 0.3e1 * t540 * t553)
  t630 = f.my_piecewise3(t539, 0, 0.4e1 / 0.3e1 * t540 * t545)
  t636 = f.my_piecewise3(t539, t317, t540 * t538)
  t642 = f.my_piecewise3(t536, 0, -0.3e1 / 0.8e1 * t5 * t561 * t54 * t614 - 0.3e1 / 0.8e1 * t5 * t623 * t128 * t614 + t5 * t630 * t191 * t614 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t636 * t321 * t614)
  t657 = 0.1e1 / t127 / t36
  t664 = 0.1e1 / t63 / t342 / r0
  t665 = t664 * t68
  t668 = 0.97900e5 / 0.4782969e7 * t212 * t665 * t72
  t669 = t211 ** 2
  t671 = t201 * t62
  t674 = 0.1e1 / t64 / t342 / t671
  t675 = t350 * t669 * t674
  t678 = 0.1e1 / t355 / params.kappa * t56
  t682 = 0.20000e5 / 0.94143178827e11 * t675 * t678 * t60 * t72
  t687 = 0.1e1 / t342 / t201
  t688 = t435 * t687
  t691 = t247 * t664
  t695 = 0.1e1 / t64 / t671
  t696 = t84 * t695
  t708 = t79 * t276
  t712 = t242 ** 2
  t719 = s0 * t695
  t721 = 0.6160e4 / 0.81e2 * tau0 * t337 - 0.2618e4 / 0.81e2 * t719
  t733 = t80 * t103
  t734 = t246 ** 2
  t736 = t734 * t669 * t674
  t739 = -0.16e2 / 0.3e1 * t235 * t430 * t150 + 0.176e3 / 0.9e1 * t433 * t688 - 0.1958e4 / 0.27e2 * t245 * t691 + 0.5236e4 / 0.81e2 * t149 * t696 - 0.16e2 * t146 * t96 * t242 * t150 + 0.88e2 / 0.3e1 * t415 * t251 - 0.8e1 * t418 * t242 * t248 - 0.64e2 / 0.9e1 * t708 * t146 * t436 - 0.6e1 * t712 * t89 - 0.8e1 * t412 * t430 - 0.2e1 * t142 * t721 + 0.176e3 / 0.3e1 * t419 * t439 + 0.88e2 / 0.3e1 * t422 * t251 - 0.2464e4 / 0.27e2 * t236 * t442 - 0.8e1 * t232 * t162 * t248 - 0.40e2 / 0.27e2 * t733 * t736
  t764 = t254 ** 2
  t789 = t351 * t354
  t814 = t232 ** 2
  t824 = -0.2464e4 / 0.9e1 * t518 * t688 - 0.66e2 * t506 * t251 + 0.616e3 / 0.3e1 * t270 * t442 + 0.13706e5 / 0.27e2 * t296 * t691 - 0.5236e4 / 0.27e2 * t172 * t696 - 0.132e3 * t503 * t251 - 0.176e3 * t509 * t439 + 0.80e2 / 0.3e1 * t733 * t434 * t789 * t146 + 0.48e2 * t708 * t232 * t248 + 0.24e2 * t433 * t242 * t248 + 0.112e3 / 0.3e1 * t100 / t294 / t88 * t736 + 0.12e2 * t245 * t430 * t150 + 0.36e2 * t415 * t242 + 0.3e1 * t149 * t721 + 0.18e2 * t235 * t712 + 0.360e3 * params.b * t80 * t103 * t814 + 0.90e2 * t282 * t103 * t712 + 0.24e2 * t235 * t430 * t146
  t889 = 0.6e1 * t166 * t103 * t721 + 0.720e3 * t282 * t171 * t146 * t481 + 0.24e2 * t458 * t162 * t150 + 0.40e2 / 0.9e1 * t94 * t171 * t736 + 0.720e3 * t487 * t283 * t242 + 0.120e3 * t282 * t167 * t430 - 0.440e3 / 0.9e1 * t484 * t688 + 0.3916e4 / 0.27e2 * t277 * t691 - 0.2618e4 / 0.27e2 * t163 * t696 - 0.1320e4 * t475 * t476 * t204 - 0.264e3 * t286 * t480 * t204 + 0.840e3 * t282 * t295 * t232 * t246 * t465 - 0.1232e4 * t463 * t464 * t211 * t344 + 0.960e3 * t487 * t171 * t458 * params.eta * t137 + 0.48e2 * t286 * t430 * params.eta * t137 + 0.72e2 * t419 * t481 + 0.168e3 * t463 * t242 * t246 * t465 + 0.896e3 / 0.3e1 * t166 * t517 * t146 * t434 * t789 + 0.2464e4 / 0.3e1 * t286 * t84 * t337 * t146
  t896 = t261 ** 2
  t900 = t301 ** 2
  t916 = -t668 - t682 + 0.3e1 * t141 * t115 * t739 + 0.12e2 * t260 * t310 * t261 - 0.24e2 * t390 * t181 * t391 + 0.36e2 * t220 * t310 * t221 + 0.18e2 * t141 * t310 * t254 + 0.12e2 * t141 * t181 * t445 - 0.24e2 * t398 * t158 * t176 + 0.36e2 * t221 * t106 * t255 + 0.18e2 * t220 * t115 * t764 + 0.12e2 * t141 * t370 * t153 - 0.4e1 * t159 * t370 * t175 - t159 * t115 * (t824 + t889) + 0.24e2 * t93 / t388 / t105 * t115 * t896 + 0.6e1 * t260 * t115 * t900 - 0.6e1 * t159 * t310 * t301 - 0.4e1 * t159 * t181 * t521 - 0.36e2 * t372 * t222 * t301 + 0.72e2 * t220 * t229 * t254
  t964 = 0.26180e5 / 0.19683e5 * t61 * t719 * t72
  t965 = t687 * t356
  t968 = 0.44000e5 / 0.129140163e9 * t352 * t965 * t72
  t999 = -0.12e2 * t225 * t446 * t175 - 0.18e2 * t225 * t255 * t301 - 0.12e2 * t225 * t154 * t521 - 0.72e2 * t92 * t389 * t392 * t153 + t964 + t968 - 0.36e2 * t225 * t409 * t175 + 0.24e2 * t399 * t181 + t107 * (0.26180e5 / 0.19683e5 * t61 * t719 * t112 - 0.97900e5 / 0.4782969e7 * t212 * t665 * t112 + 0.44000e5 / 0.129140163e9 * t352 * t965 * t112 - 0.20000e5 / 0.94143178827e11 * t675 * t678 * t60 * t112 - t964 + t668 - t968 + t682) - 0.72e2 * t372 * t115 * t153 * t175 * t254 + 0.72e2 * t524 * t115 * t153 * t301 * t175
  t1005 = t19 ** 2
  t1008 = t30 ** 2
  t1014 = t41 ** 2
  t1023 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t1024 = f.my_piecewise5(t10, 0, t14, 0, t1023)
  t1028 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t1005 * t1008 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t1014 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t1024)
  t1059 = -t5 * t53 * t128 * t117 / 0.2e1 + t5 * t126 * t191 * t117 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t189 * t321 * t117 + 0.10e2 / 0.27e2 * t5 * t319 * t657 * t117 - 0.3e1 / 0.8e1 * t5 * t334 * (0.72e2 * t91 * t259 * t222 * t261 + 0.24e2 * t220 * t154 * t445 - 0.36e2 * t225 * t406 * t175 - 0.72e2 * t372 * t403 * t175 + 0.8e1 * t260 * t176 * t521 - 0.36e2 * t225 * t229 * t301 + 0.72e2 * t524 * t229 * t261 + 0.36e2 * t524 * t255 * t261 + 0.24e2 * t260 * t265 * t301 - 0.36e2 * t390 * t262 * t301 + t916 + t999) - 0.3e1 / 0.8e1 * t5 * t1028 * t54 * t117 - 0.3e1 / 0.2e1 * t5 * t55 * t183 - 0.3e1 / 0.2e1 * t5 * t129 * t183 - 0.9e1 / 0.4e1 * t5 * t133 * t312 + t5 * t192 * t183 - 0.3e1 / 0.2e1 * t5 * t196 * t312 - 0.3e1 / 0.2e1 * t5 * t200 * t529 - 0.5e1 / 0.9e1 * t5 * t322 * t183 + t5 * t326 * t312 / 0.2e1 - t5 * t330 * t529 / 0.2e1
  t1060 = f.my_piecewise3(t1, 0, t1059)
  t1061 = t538 ** 2
  t1064 = t546 ** 2
  t1070 = t553 ** 2
  t1076 = f.my_piecewise5(t14, 0, t10, 0, -t1023)
  t1080 = f.my_piecewise3(t539, 0, 0.40e2 / 0.81e2 / t541 / t1061 * t1064 - 0.16e2 / 0.9e1 * t543 * t546 * t553 + 0.4e1 / 0.3e1 * t550 * t1070 + 0.16e2 / 0.9e1 * t551 * t557 + 0.4e1 / 0.3e1 * t540 * t1076)
  t1102 = f.my_piecewise3(t536, 0, -0.3e1 / 0.8e1 * t5 * t1080 * t54 * t614 - t5 * t561 * t128 * t614 / 0.2e1 + t5 * t623 * t191 * t614 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t630 * t321 * t614 + 0.10e2 / 0.27e2 * t5 * t636 * t657 * t614)
  d1111 = 0.4e1 * t534 + 0.4e1 * t642 + t6 * (t1060 + t1102)

  res = {'v4rho4': d1111}
  return res
