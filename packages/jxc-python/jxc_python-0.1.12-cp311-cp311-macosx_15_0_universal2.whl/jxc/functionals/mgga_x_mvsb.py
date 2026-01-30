"""Generated from mgga_x_mvsb.mpl."""

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_e1_raw = params.e1
  if isinstance(params_e1_raw, (str, bytes, dict)):
    params_e1 = params_e1_raw
  else:
    try:
      params_e1_seq = list(params_e1_raw)
    except TypeError:
      params_e1 = params_e1_raw
    else:
      params_e1_seq = np.asarray(params_e1_seq, dtype=np.float64)
      params_e1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_e1_seq))
  params_k0_raw = params.k0
  if isinstance(params_k0_raw, (str, bytes, dict)):
    params_k0 = params_k0_raw
  else:
    try:
      params_k0_seq = list(params_k0_raw)
    except TypeError:
      params_k0 = params_k0_raw
    else:
      params_k0_seq = np.asarray(params_k0_seq, dtype=np.float64)
      params_k0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k0_seq))

  mvs_fa = lambda a: (1 - a) / ((1 + params_e1 * a ** 2) ** 2 + params_c1 * a ** 4) ** (1 / 4)

  mvs_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  mvsb_beta = lambda t, x: mvs_alpha(t, x) * K_FACTOR_C / (t - K_FACTOR_C)

  mvsb_f = lambda x, u, t: (1 + params_k0 * mvs_fa(mvsb_beta(t, x))) / (1 + params_b * (X2S * x) ** 4) ** (1 / 8)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mvsb_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_e1_raw = params.e1
  if isinstance(params_e1_raw, (str, bytes, dict)):
    params_e1 = params_e1_raw
  else:
    try:
      params_e1_seq = list(params_e1_raw)
    except TypeError:
      params_e1 = params_e1_raw
    else:
      params_e1_seq = np.asarray(params_e1_seq, dtype=np.float64)
      params_e1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_e1_seq))
  params_k0_raw = params.k0
  if isinstance(params_k0_raw, (str, bytes, dict)):
    params_k0 = params_k0_raw
  else:
    try:
      params_k0_seq = list(params_k0_raw)
    except TypeError:
      params_k0 = params_k0_raw
    else:
      params_k0_seq = np.asarray(params_k0_seq, dtype=np.float64)
      params_k0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k0_seq))

  mvs_fa = lambda a: (1 - a) / ((1 + params_e1 * a ** 2) ** 2 + params_c1 * a ** 4) ** (1 / 4)

  mvs_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  mvsb_beta = lambda t, x: mvs_alpha(t, x) * K_FACTOR_C / (t - K_FACTOR_C)

  mvsb_f = lambda x, u, t: (1 + params_k0 * mvs_fa(mvsb_beta(t, x))) / (1 + params_b * (X2S * x) ** 4) ** (1 / 8)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mvsb_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_e1_raw = params.e1
  if isinstance(params_e1_raw, (str, bytes, dict)):
    params_e1 = params_e1_raw
  else:
    try:
      params_e1_seq = list(params_e1_raw)
    except TypeError:
      params_e1 = params_e1_raw
    else:
      params_e1_seq = np.asarray(params_e1_seq, dtype=np.float64)
      params_e1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_e1_seq))
  params_k0_raw = params.k0
  if isinstance(params_k0_raw, (str, bytes, dict)):
    params_k0 = params_k0_raw
  else:
    try:
      params_k0_seq = list(params_k0_raw)
    except TypeError:
      params_k0 = params_k0_raw
    else:
      params_k0_seq = np.asarray(params_k0_seq, dtype=np.float64)
      params_k0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k0_seq))

  mvs_fa = lambda a: (1 - a) / ((1 + params_e1 * a ** 2) ** 2 + params_c1 * a ** 4) ** (1 / 4)

  mvs_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  mvsb_beta = lambda t, x: mvs_alpha(t, x) * K_FACTOR_C / (t - K_FACTOR_C)

  mvsb_f = lambda x, u, t: (1 + params_k0 * mvs_fa(mvsb_beta(t, x))) / (1 + params_b * (X2S * x) ** 4) ** (1 / 8)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mvsb_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t28 = r0 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t31 = 0.1e1 / t29 / r0
  t32 = tau0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t29 / t33
  t38 = t32 - s0 * t35 / 0.8e1
  t39 = 6 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.3e1 / 0.10e2 * t40 * t43
  t46 = t32 - t45
  t47 = 0.1e1 / t46
  t50 = params.k0 * (-t38 * t47 + 0.1e1)
  t51 = t38 ** 2
  t52 = params.e1 * t51
  t53 = t46 ** 2
  t54 = 0.1e1 / t53
  t56 = t52 * t54 + 0.1e1
  t57 = t56 ** 2
  t58 = t51 ** 2
  t59 = params.c1 * t58
  t60 = t53 ** 2
  t61 = 0.1e1 / t60
  t63 = t59 * t61 + t57
  t64 = t63 ** (0.1e1 / 0.4e1)
  t65 = 0.1e1 / t64
  t67 = t50 * t65 + 0.1e1
  t69 = params.b * t40
  t71 = 0.1e1 / t42 / t41
  t72 = s0 ** 2
  t73 = t71 * t72
  t74 = t33 ** 2
  t77 = 0.1e1 / t28 / t74 / r0
  t81 = 0.1e1 + t69 * t73 * t77 / 0.576e3
  t82 = t81 ** (0.1e1 / 0.8e1)
  t83 = 0.1e1 / t82
  t84 = t27 * t67 * t83
  t87 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t84)
  t88 = r1 <= f.p.dens_threshold
  t89 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t90 = 0.1e1 + t89
  t91 = t90 <= f.p.zeta_threshold
  t92 = t90 ** (0.1e1 / 0.3e1)
  t94 = f.my_piecewise3(t91, t22, t92 * t90)
  t95 = t5 * t94
  t96 = r1 ** (0.1e1 / 0.3e1)
  t97 = t96 ** 2
  t99 = 0.1e1 / t97 / r1
  t100 = tau1 * t99
  t101 = r1 ** 2
  t103 = 0.1e1 / t97 / t101
  t106 = t100 - s2 * t103 / 0.8e1
  t107 = t100 - t45
  t108 = 0.1e1 / t107
  t111 = params.k0 * (-t106 * t108 + 0.1e1)
  t112 = t106 ** 2
  t113 = params.e1 * t112
  t114 = t107 ** 2
  t115 = 0.1e1 / t114
  t117 = t113 * t115 + 0.1e1
  t118 = t117 ** 2
  t119 = t112 ** 2
  t120 = params.c1 * t119
  t121 = t114 ** 2
  t122 = 0.1e1 / t121
  t124 = t120 * t122 + t118
  t125 = t124 ** (0.1e1 / 0.4e1)
  t126 = 0.1e1 / t125
  t128 = t111 * t126 + 0.1e1
  t130 = s2 ** 2
  t131 = t71 * t130
  t132 = t101 ** 2
  t135 = 0.1e1 / t96 / t132 / r1
  t139 = 0.1e1 + t69 * t131 * t135 / 0.576e3
  t140 = t139 ** (0.1e1 / 0.8e1)
  t141 = 0.1e1 / t140
  t142 = t27 * t128 * t141
  t145 = f.my_piecewise3(t88, 0, -0.3e1 / 0.8e1 * t95 * t142)
  t146 = t6 ** 2
  t148 = t16 / t146
  t149 = t7 - t148
  t150 = f.my_piecewise5(t10, 0, t14, 0, t149)
  t153 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t150)
  t157 = t27 ** 2
  t158 = 0.1e1 / t157
  t162 = t26 * t158 * t67 * t83 / 0.8e1
  t163 = tau0 * t35
  t170 = -0.5e1 / 0.3e1 * t163 + s0 / t29 / t33 / r0 / 0.3e1
  t172 = t38 * t54
  t179 = 0.1e1 / t64 / t63
  t180 = params.e1 * t38
  t185 = 0.1e1 / t53 / t46
  t194 = params.c1 * t51 * t38
  t199 = 0.1e1 / t60 / t46
  t215 = t5 * t25 * t27 * t67
  t219 = 0.1e1 / t82 / t81 * params.b * t40
  t228 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t153 * t84 - t162 - 0.3e1 / 0.8e1 * t26 * t27 * (params.k0 * (-t170 * t47 - 0.5e1 / 0.3e1 * t172 * t163) * t65 - t50 * t179 * (0.2e1 * t56 * (0.2e1 * t180 * t54 * t170 + 0.10e2 / 0.3e1 * t52 * t185 * tau0 * t35) + 0.4e1 * t194 * t61 * t170 + 0.20e2 / 0.3e1 * t59 * t199 * tau0 * t35) / 0.4e1) * t83 - t215 * t219 * t73 / t28 / t74 / t33 / 0.2304e4)
  t230 = f.my_piecewise5(t14, 0, t10, 0, -t149)
  t233 = f.my_piecewise3(t91, 0, 0.4e1 / 0.3e1 * t92 * t230)
  t240 = t95 * t158 * t128 * t141 / 0.8e1
  t242 = f.my_piecewise3(t88, 0, -0.3e1 / 0.8e1 * t5 * t233 * t142 - t240)
  vrho_0_ = t87 + t145 + t6 * (t228 + t242)
  t245 = -t7 - t148
  t246 = f.my_piecewise5(t10, 0, t14, 0, t245)
  t249 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t246)
  t254 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t249 * t84 - t162)
  t256 = f.my_piecewise5(t14, 0, t10, 0, -t245)
  t259 = f.my_piecewise3(t91, 0, 0.4e1 / 0.3e1 * t92 * t256)
  t263 = tau1 * t103
  t270 = -0.5e1 / 0.3e1 * t263 + s2 / t97 / t101 / r1 / 0.3e1
  t272 = t106 * t115
  t279 = 0.1e1 / t125 / t124
  t280 = params.e1 * t106
  t285 = 0.1e1 / t114 / t107
  t294 = params.c1 * t112 * t106
  t299 = 0.1e1 / t121 / t107
  t315 = t5 * t94 * t27 * t128
  t319 = 0.1e1 / t140 / t139 * params.b * t40
  t328 = f.my_piecewise3(t88, 0, -0.3e1 / 0.8e1 * t5 * t259 * t142 - t240 - 0.3e1 / 0.8e1 * t95 * t27 * (params.k0 * (-t270 * t108 - 0.5e1 / 0.3e1 * t272 * t263) * t126 - t111 * t279 * (0.2e1 * t117 * (0.2e1 * t280 * t115 * t270 + 0.10e2 / 0.3e1 * t113 * t285 * tau1 * t103) + 0.4e1 * t294 * t122 * t270 + 0.20e2 / 0.3e1 * t120 * t299 * tau1 * t103) / 0.4e1) * t141 - t315 * t319 * t131 / t96 / t132 / t101 / 0.2304e4)
  vrho_1_ = t87 + t145 + t6 * (t254 + t328)
  t356 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (params.k0 * t35 * t47 * t65 / 0.8e1 - t50 * t179 * (-t56 * params.e1 * t172 * t35 / 0.2e1 - t194 * t61 * t35 / 0.2e1) / 0.4e1) * t83 + t215 * t219 * t71 * s0 * t77 / 0.6144e4)
  vsigma_0_ = t6 * t356
  vsigma_1_ = 0.0e0
  t382 = f.my_piecewise3(t88, 0, -0.3e1 / 0.8e1 * t95 * t27 * (params.k0 * t103 * t108 * t126 / 0.8e1 - t111 * t279 * (-t117 * params.e1 * t272 * t103 / 0.2e1 - t294 * t122 * t103 / 0.2e1) / 0.4e1) * t141 + t315 * t319 * t71 * s2 * t135 / 0.6144e4)
  vsigma_2_ = t6 * t382
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t411 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (params.k0 * (t172 * t31 - t31 * t47) * t65 - t50 * t179 * (0.2e1 * t56 * (0.2e1 * t180 * t54 * t31 - 0.2e1 * t52 * t185 * t31) + 0.4e1 * t194 * t61 * t31 - 0.4e1 * t59 * t199 * t31) / 0.4e1) * t83)
  vtau_0_ = t6 * t411
  t440 = f.my_piecewise3(t88, 0, -0.3e1 / 0.8e1 * t95 * t27 * (params.k0 * (-t99 * t108 + t272 * t99) * t126 - t111 * t279 * (0.2e1 * t117 * (-0.2e1 * t113 * t285 * t99 + 0.2e1 * t280 * t115 * t99) + 0.4e1 * t294 * t122 * t99 - 0.4e1 * t120 * t299 * t99) / 0.4e1) * t141)
  vtau_1_ = t6 * t440
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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_e1_raw = params.e1
  if isinstance(params_e1_raw, (str, bytes, dict)):
    params_e1 = params_e1_raw
  else:
    try:
      params_e1_seq = list(params_e1_raw)
    except TypeError:
      params_e1 = params_e1_raw
    else:
      params_e1_seq = np.asarray(params_e1_seq, dtype=np.float64)
      params_e1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_e1_seq))
  params_k0_raw = params.k0
  if isinstance(params_k0_raw, (str, bytes, dict)):
    params_k0 = params_k0_raw
  else:
    try:
      params_k0_seq = list(params_k0_raw)
    except TypeError:
      params_k0 = params_k0_raw
    else:
      params_k0_seq = np.asarray(params_k0_seq, dtype=np.float64)
      params_k0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k0_seq))

  mvs_fa = lambda a: (1 - a) / ((1 + params_e1 * a ** 2) ** 2 + params_c1 * a ** 4) ** (1 / 4)

  mvs_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  mvsb_beta = lambda t, x: mvs_alpha(t, x) * K_FACTOR_C / (t - K_FACTOR_C)

  mvsb_f = lambda x, u, t: (1 + params_k0 * mvs_fa(mvsb_beta(t, x))) / (1 + params_b * (X2S * x) ** 4) ** (1 / 8)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mvsb_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t20 = 2 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t22 = tau0 * t21
  t23 = t19 ** 2
  t25 = 0.1e1 / t23 / r0
  t26 = t22 * t25
  t27 = s0 * t21
  t28 = r0 ** 2
  t30 = 0.1e1 / t23 / t28
  t33 = t26 - t27 * t30 / 0.8e1
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t41 = t26 - 0.3e1 / 0.10e2 * t35 * t38
  t42 = 0.1e1 / t41
  t45 = params.k0 * (-t33 * t42 + 0.1e1)
  t46 = t33 ** 2
  t47 = params.e1 * t46
  t48 = t41 ** 2
  t49 = 0.1e1 / t48
  t51 = t47 * t49 + 0.1e1
  t52 = t51 ** 2
  t53 = t46 ** 2
  t54 = params.c1 * t53
  t55 = t48 ** 2
  t56 = 0.1e1 / t55
  t58 = t54 * t56 + t52
  t59 = t58 ** (0.1e1 / 0.4e1)
  t60 = 0.1e1 / t59
  t62 = t45 * t60 + 0.1e1
  t66 = 0.1e1 / t37 / t36
  t68 = s0 ** 2
  t70 = t28 ** 2
  t71 = t70 * r0
  t77 = 0.1e1 + params.b * t35 * t66 * t68 * t20 / t19 / t71 / 0.288e3
  t78 = t77 ** (0.1e1 / 0.8e1)
  t79 = 0.1e1 / t78
  t83 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t62 * t79)
  t89 = t22 * t30
  t96 = -0.5e1 / 0.3e1 * t89 + t27 / t23 / t28 / r0 / 0.3e1
  t98 = t33 * t49
  t105 = 0.1e1 / t59 / t58
  t106 = params.e1 * t33
  t111 = 0.1e1 / t48 / t41
  t119 = params.c1 * t46 * t33
  t124 = 0.1e1 / t55 / t41
  t145 = 0.1e1 / t78 / t77 * params.b * t35
  t152 = f.my_piecewise3(t2, 0, -t18 / t23 * t62 * t79 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (params.k0 * (-t96 * t42 - 0.5e1 / 0.3e1 * t98 * t89) * t60 - t45 * t105 * (0.2e1 * t51 * (0.2e1 * t106 * t49 * t96 + 0.10e2 / 0.3e1 * t47 * t111 * t89) + 0.4e1 * t119 * t56 * t96 + 0.20e2 / 0.3e1 * t54 * t124 * t89) / 0.4e1) * t79 - t6 * t17 / t70 / t28 * t62 * t145 * t66 * t68 * t20 / 0.1152e4)
  vrho_0_ = 0.2e1 * r0 * t152 + 0.2e1 * t83
  t162 = t49 * t21
  t165 = t56 * t21
  t188 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (params.k0 * t21 * t30 * t42 * t60 / 0.8e1 - t45 * t105 * (-t51 * params.e1 * t33 * t162 * t30 / 0.2e1 - t119 * t165 * t30 / 0.2e1) / 0.4e1) * t79 + t6 * t17 / t71 * t62 * t145 * t66 * s0 * t20 / 0.3072e4)
  vsigma_0_ = 0.2e1 * r0 * t188
  vlapl_0_ = 0.0e0
  t190 = t21 * t25
  t221 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (params.k0 * (-t190 * t42 + t98 * t190) * t60 - t45 * t105 * (0.2e1 * t51 * (-0.2e1 * t47 * t111 * t21 * t25 + 0.2e1 * t106 * t162 * t25) + 0.4e1 * t119 * t165 * t25 - 0.4e1 * t54 * t124 * t21 * t25) / 0.4e1) * t79)
  vtau_0_ = 0.2e1 * r0 * t221
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
  t18 = t6 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t22 = 2 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = tau0 * t23
  t26 = 0.1e1 / t20 / r0
  t27 = t24 * t26
  t28 = s0 * t23
  t29 = r0 ** 2
  t31 = 0.1e1 / t20 / t29
  t34 = t27 - t28 * t31 / 0.8e1
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t42 = t27 - 0.3e1 / 0.10e2 * t36 * t39
  t43 = 0.1e1 / t42
  t46 = params.k0 * (-t34 * t43 + 0.1e1)
  t47 = t34 ** 2
  t48 = params.e1 * t47
  t49 = t42 ** 2
  t50 = 0.1e1 / t49
  t52 = t48 * t50 + 0.1e1
  t53 = t52 ** 2
  t54 = t47 ** 2
  t55 = params.c1 * t54
  t56 = t49 ** 2
  t57 = 0.1e1 / t56
  t59 = t55 * t57 + t53
  t60 = t59 ** (0.1e1 / 0.4e1)
  t61 = 0.1e1 / t60
  t63 = t46 * t61 + 0.1e1
  t67 = 0.1e1 / t38 / t37
  t69 = s0 ** 2
  t71 = t29 ** 2
  t74 = 0.1e1 / t19 / t71 / r0
  t78 = 0.1e1 + params.b * t36 * t67 * t69 * t22 * t74 / 0.288e3
  t79 = t78 ** (0.1e1 / 0.8e1)
  t80 = 0.1e1 / t79
  t84 = t24 * t31
  t86 = t29 * r0
  t88 = 0.1e1 / t20 / t86
  t91 = -0.5e1 / 0.3e1 * t84 + t28 * t88 / 0.3e1
  t93 = t34 * t50
  t97 = params.k0 * (-t91 * t43 - 0.5e1 / 0.3e1 * t93 * t84)
  t100 = 0.1e1 / t60 / t59
  t101 = params.e1 * t34
  t102 = t50 * t91
  t106 = 0.1e1 / t49 / t42
  t107 = t48 * t106
  t110 = 0.2e1 * t101 * t102 + 0.10e2 / 0.3e1 * t107 * t84
  t114 = params.c1 * t47 * t34
  t119 = 0.1e1 / t56 / t42
  t120 = t55 * t119
  t123 = 0.2e1 * t52 * t110 + 0.4e1 * t114 * t57 * t91 + 0.20e2 / 0.3e1 * t120 * t84
  t124 = t100 * t123
  t127 = t97 * t61 - t46 * t124 / 0.4e1
  t134 = t17 / t71 / t29
  t143 = 0.1e1 / t79 / t78 * params.b * t36 * t67 * t69 * t22
  t147 = f.my_piecewise3(t2, 0, -t18 * t21 * t63 * t80 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t127 * t80 - t6 * t134 * t63 * t143 / 0.1152e4)
  t164 = t24 * t88
  t170 = 0.40e2 / 0.9e1 * t164 - 0.11e2 / 0.9e1 * t28 / t20 / t71
  t175 = tau0 ** 2
  t177 = t175 * t22 * t74
  t187 = t59 ** 2
  t190 = t123 ** 2
  t194 = t110 ** 2
  t196 = t91 ** 2
  t203 = t91 * tau0 * t23 * t31
  t247 = t71 ** 2
  t254 = t78 ** 2
  t257 = params.b ** 2
  t260 = t37 ** 2
  t263 = t69 ** 2
  t270 = f.my_piecewise3(t2, 0, t18 * t26 * t63 * t80 / 0.12e2 - t18 * t21 * t127 * t80 / 0.4e1 + 0.17e2 / 0.3456e4 * t6 * t17 / t71 / t86 * t63 * t143 - 0.3e1 / 0.8e1 * t18 * t19 * (params.k0 * (-t170 * t43 - 0.10e2 / 0.3e1 * t102 * t84 - 0.100e3 / 0.9e1 * t34 * t106 * t177 + 0.40e2 / 0.9e1 * t93 * t164) * t61 - t97 * t124 / 0.2e1 + 0.5e1 / 0.16e2 * t46 / t60 / t187 * t190 - t46 * t100 * (0.2e1 * t194 + 0.2e1 * t52 * (0.2e1 * params.e1 * t196 * t50 + 0.40e2 / 0.3e1 * t101 * t106 * t203 + 0.2e1 * t101 * t50 * t170 + 0.100e3 / 0.3e1 * t48 * t57 * t177 - 0.80e2 / 0.9e1 * t107 * t164) + 0.12e2 * params.c1 * t47 * t57 * t196 + 0.160e3 / 0.3e1 * t114 * t119 * t203 + 0.4e1 * t114 * t57 * t170 + 0.1000e4 / 0.9e1 * t55 / t56 / t49 * t177 - 0.160e3 / 0.9e1 * t120 * t164) / 0.4e1) * t80 - t6 * t134 * t127 * t143 / 0.576e3 - t6 * t17 / t19 / t247 / t71 * t63 / t79 / t254 * t257 * t35 / t39 / t260 * t263 * t23 / 0.9216e4)
  v2rho2_0_ = 0.2e1 * r0 * t270 + 0.4e1 * t147
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
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = tau0 * t24
  t26 = t25 * t22
  t27 = s0 * t24
  t28 = r0 ** 2
  t30 = 0.1e1 / t20 / t28
  t33 = t26 - t27 * t30 / 0.8e1
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t41 = t26 - 0.3e1 / 0.10e2 * t35 * t38
  t42 = 0.1e1 / t41
  t45 = params.k0 * (-t33 * t42 + 0.1e1)
  t46 = t33 ** 2
  t47 = params.e1 * t46
  t48 = t41 ** 2
  t49 = 0.1e1 / t48
  t51 = t47 * t49 + 0.1e1
  t52 = t51 ** 2
  t53 = t46 ** 2
  t54 = params.c1 * t53
  t55 = t48 ** 2
  t56 = 0.1e1 / t55
  t58 = t54 * t56 + t52
  t59 = t58 ** (0.1e1 / 0.4e1)
  t60 = 0.1e1 / t59
  t62 = t45 * t60 + 0.1e1
  t66 = 0.1e1 / t37 / t36
  t68 = s0 ** 2
  t70 = t28 ** 2
  t71 = t70 * r0
  t73 = 0.1e1 / t19 / t71
  t77 = 0.1e1 + params.b * t35 * t66 * t68 * t23 * t73 / 0.288e3
  t78 = t77 ** (0.1e1 / 0.8e1)
  t79 = 0.1e1 / t78
  t83 = 0.1e1 / t20
  t84 = t25 * t30
  t86 = t28 * r0
  t88 = 0.1e1 / t20 / t86
  t91 = -0.5e1 / 0.3e1 * t84 + t27 * t88 / 0.3e1
  t93 = t33 * t49
  t97 = params.k0 * (-t91 * t42 - 0.5e1 / 0.3e1 * t93 * t84)
  t100 = 0.1e1 / t59 / t58
  t101 = params.e1 * t33
  t102 = t49 * t91
  t105 = t48 * t41
  t106 = 0.1e1 / t105
  t107 = t47 * t106
  t110 = 0.2e1 * t101 * t102 + 0.10e2 / 0.3e1 * t107 * t84
  t114 = params.c1 * t46 * t33
  t115 = t56 * t91
  t119 = 0.1e1 / t55 / t41
  t120 = t54 * t119
  t123 = 0.2e1 * t51 * t110 + 0.4e1 * t114 * t115 + 0.20e2 / 0.3e1 * t120 * t84
  t124 = t100 * t123
  t127 = t97 * t60 - t45 * t124 / 0.4e1
  t134 = t17 / t70 / t86
  t143 = 0.1e1 / t78 / t77 * params.b * t35 * t66 * t68 * t23
  t146 = t25 * t88
  t149 = 0.1e1 / t20 / t70
  t152 = 0.40e2 / 0.9e1 * t146 - 0.11e2 / 0.9e1 * t27 * t149
  t156 = t33 * t106
  t157 = tau0 ** 2
  t158 = t157 * t23
  t159 = t158 * t73
  t165 = params.k0 * (-t152 * t42 - 0.10e2 / 0.3e1 * t102 * t84 - 0.100e3 / 0.9e1 * t156 * t159 + 0.40e2 / 0.9e1 * t93 * t146)
  t169 = t58 ** 2
  t171 = 0.1e1 / t59 / t169
  t172 = t123 ** 2
  t173 = t171 * t172
  t176 = t110 ** 2
  t178 = t91 ** 2
  t179 = params.e1 * t178
  t182 = t101 * t106
  t183 = t91 * tau0
  t184 = t24 * t30
  t185 = t183 * t184
  t188 = t49 * t152
  t191 = t47 * t56
  t196 = 0.2e1 * t179 * t49 + 0.40e2 / 0.3e1 * t182 * t185 + 0.2e1 * t101 * t188 + 0.100e3 / 0.3e1 * t191 * t159 - 0.80e2 / 0.9e1 * t107 * t146
  t199 = params.c1 * t46
  t203 = t114 * t119
  t210 = 0.1e1 / t55 / t48
  t211 = t54 * t210
  t216 = 0.2e1 * t176 + 0.2e1 * t51 * t196 + 0.12e2 * t199 * t56 * t178 + 0.160e3 / 0.3e1 * t203 * t185 + 0.4e1 * t114 * t56 * t152 + 0.1000e4 / 0.9e1 * t211 * t159 - 0.160e3 / 0.9e1 * t120 * t146
  t217 = t100 * t216
  t220 = t165 * t60 - t97 * t124 / 0.2e1 + 0.5e1 / 0.16e2 * t45 * t173 - t45 * t217 / 0.4e1
  t225 = t70 * t28
  t227 = t17 / t225
  t232 = t70 ** 2
  t236 = t17 / t19 / t232 / t70
  t239 = t77 ** 2
  t242 = params.b ** 2
  t245 = t36 ** 2
  t248 = t68 ** 2
  t251 = 0.1e1 / t78 / t239 * t242 * t34 / t38 / t245 * t248 * t24
  t255 = f.my_piecewise3(t2, 0, t18 * t22 * t62 * t79 / 0.12e2 - t18 * t83 * t127 * t79 / 0.4e1 + 0.17e2 / 0.3456e4 * t6 * t134 * t62 * t143 - 0.3e1 / 0.8e1 * t18 * t19 * t220 * t79 - t6 * t227 * t127 * t143 / 0.576e3 - t6 * t236 * t62 * t251 / 0.9216e4)
  t265 = 0.1e1 / t232
  t287 = t25 * t149
  t293 = -0.440e3 / 0.27e2 * t287 + 0.154e3 / 0.27e2 * t27 / t20 / t71
  t303 = t157 * tau0
  t309 = t158 / t19 / t225
  t345 = t91 * t157 * t23 * t73
  t349 = t152 * tau0 * t184
  t353 = t183 * t24 * t88
  t403 = 0.6e1 * t110 * t196 + 0.2e1 * t51 * (0.6e1 * params.e1 * t91 * t188 + 0.20e2 * t179 * t106 * t84 + 0.200e3 * t101 * t56 * t345 + 0.20e2 * t182 * t349 - 0.160e3 / 0.3e1 * t182 * t353 + 0.2e1 * t101 * t49 * t293 + 0.4000e4 / 0.9e1 * t47 * t119 * t303 * t265 - 0.800e3 / 0.3e1 * t191 * t309 + 0.880e3 / 0.27e2 * t107 * t287) + 0.24e2 * params.c1 * t33 * t56 * t178 * t91 + 0.240e3 * t199 * t119 * t178 * tau0 * t184 + 0.36e2 * t199 * t115 * t152 + 0.4000e4 / 0.3e1 * t114 * t210 * t345 + 0.80e2 * t203 * t349 - 0.640e3 / 0.3e1 * t203 * t353 + 0.4e1 * t114 * t56 * t293 + 0.20000e5 / 0.9e1 * t54 / t55 / t105 * t303 * t265 - 0.8000e4 / 0.9e1 * t211 * t309 + 0.1760e4 / 0.27e2 * t120 * t287
  t420 = t245 ** 2
  t424 = t232 ** 2
  t441 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t30 * t62 * t79 + t18 * t22 * t127 * t79 / 0.4e1 - 0.355e3 / 0.10368e5 * t6 * t17 * t265 * t62 * t143 - 0.3e1 / 0.8e1 * t18 * t83 * t220 * t79 + 0.17e2 / 0.1152e4 * t6 * t134 * t127 * t143 + t6 * t17 / t19 / t232 / t71 * t62 * t251 / 0.512e3 - 0.3e1 / 0.8e1 * t18 * t19 * (params.k0 * (-t293 * t42 - 0.5e1 * t188 * t84 - 0.100e3 / 0.3e1 * t91 * t106 * t159 + 0.40e2 / 0.3e1 * t102 * t146 - 0.1000e4 / 0.9e1 * t33 * t56 * t303 * t265 + 0.800e3 / 0.9e1 * t156 * t309 - 0.440e3 / 0.27e2 * t93 * t287) * t60 - 0.3e1 / 0.4e1 * t165 * t124 + 0.15e2 / 0.16e2 * t97 * t173 - 0.3e1 / 0.4e1 * t97 * t217 - 0.45e2 / 0.64e2 * t45 / t59 / t169 / t58 * t172 * t123 + 0.15e2 / 0.16e2 * t45 * t171 * t123 * t216 - t45 * t100 * t403 / 0.4e1) * t79 - t6 * t227 * t220 * t143 / 0.384e3 - t6 * t236 * t127 * t251 / 0.3072e4 - 0.17e2 / 0.331776e6 * t3 / t4 / t420 * t17 / t20 / t424 / t28 * t62 / t78 / t239 / t77 * t242 * params.b * t248 * t68)
  v3rho3_0_ = 0.2e1 * r0 * t441 + 0.6e1 * t255

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
  t19 = r0 ** 2
  t20 = r0 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t23 = 0.1e1 / t21 / t19
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = tau0 * t25
  t28 = 0.1e1 / t21 / r0
  t29 = t26 * t28
  t30 = s0 * t25
  t33 = t29 - t30 * t23 / 0.8e1
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t41 = t29 - 0.3e1 / 0.10e2 * t35 * t38
  t42 = 0.1e1 / t41
  t45 = params.k0 * (-t33 * t42 + 0.1e1)
  t46 = t33 ** 2
  t47 = params.e1 * t46
  t48 = t41 ** 2
  t49 = 0.1e1 / t48
  t51 = t47 * t49 + 0.1e1
  t52 = t51 ** 2
  t53 = t46 ** 2
  t54 = params.c1 * t53
  t55 = t48 ** 2
  t56 = 0.1e1 / t55
  t58 = t54 * t56 + t52
  t59 = t58 ** (0.1e1 / 0.4e1)
  t60 = 0.1e1 / t59
  t62 = t45 * t60 + 0.1e1
  t66 = 0.1e1 / t37 / t36
  t68 = s0 ** 2
  t70 = t19 ** 2
  t71 = t70 * r0
  t73 = 0.1e1 / t20 / t71
  t77 = 0.1e1 + params.b * t35 * t66 * t68 * t24 * t73 / 0.288e3
  t78 = t77 ** (0.1e1 / 0.8e1)
  t79 = 0.1e1 / t78
  t83 = t26 * t23
  t85 = t19 * r0
  t87 = 0.1e1 / t21 / t85
  t90 = -0.5e1 / 0.3e1 * t83 + t30 * t87 / 0.3e1
  t92 = t33 * t49
  t96 = params.k0 * (-t90 * t42 - 0.5e1 / 0.3e1 * t92 * t83)
  t99 = 0.1e1 / t59 / t58
  t100 = params.e1 * t33
  t101 = t49 * t90
  t104 = t48 * t41
  t105 = 0.1e1 / t104
  t106 = t47 * t105
  t109 = 0.2e1 * t100 * t101 + 0.10e2 / 0.3e1 * t106 * t83
  t113 = params.c1 * t46 * t33
  t114 = t56 * t90
  t118 = 0.1e1 / t55 / t41
  t119 = t54 * t118
  t122 = 0.2e1 * t51 * t109 + 0.4e1 * t113 * t114 + 0.20e2 / 0.3e1 * t119 * t83
  t123 = t99 * t122
  t126 = t96 * t60 - t45 * t123 / 0.4e1
  t131 = t70 ** 2
  t132 = 0.1e1 / t131
  t133 = t17 * t132
  t142 = 0.1e1 / t78 / t77 * params.b * t35 * t66 * t68 * t24
  t145 = 0.1e1 / t21
  t146 = t26 * t87
  t149 = 0.1e1 / t21 / t70
  t152 = 0.40e2 / 0.9e1 * t146 - 0.11e2 / 0.9e1 * t30 * t149
  t156 = t33 * t105
  t157 = tau0 ** 2
  t158 = t157 * t24
  t159 = t158 * t73
  t165 = params.k0 * (-t152 * t42 - 0.10e2 / 0.3e1 * t101 * t83 - 0.100e3 / 0.9e1 * t156 * t159 + 0.40e2 / 0.9e1 * t92 * t146)
  t169 = t58 ** 2
  t171 = 0.1e1 / t59 / t169
  t172 = t122 ** 2
  t173 = t171 * t172
  t176 = t109 ** 2
  t178 = t90 ** 2
  t179 = params.e1 * t178
  t182 = t100 * t105
  t183 = t90 * tau0
  t184 = t25 * t23
  t185 = t183 * t184
  t188 = t49 * t152
  t191 = t47 * t56
  t196 = 0.2e1 * t179 * t49 + 0.40e2 / 0.3e1 * t182 * t185 + 0.2e1 * t100 * t188 + 0.100e3 / 0.3e1 * t191 * t159 - 0.80e2 / 0.9e1 * t106 * t146
  t199 = params.c1 * t46
  t200 = t56 * t178
  t203 = t113 * t118
  t210 = 0.1e1 / t55 / t48
  t211 = t54 * t210
  t216 = 0.2e1 * t176 + 0.2e1 * t51 * t196 + 0.12e2 * t199 * t200 + 0.160e3 / 0.3e1 * t203 * t185 + 0.4e1 * t113 * t56 * t152 + 0.1000e4 / 0.9e1 * t211 * t159 - 0.160e3 / 0.9e1 * t119 * t146
  t217 = t99 * t216
  t220 = t165 * t60 - t96 * t123 / 0.2e1 + 0.5e1 / 0.16e2 * t45 * t173 - t45 * t217 / 0.4e1
  t225 = t70 * t85
  t227 = t17 / t225
  t235 = t17 / t20 / t131 / t71
  t238 = t77 ** 2
  t241 = params.b ** 2
  t244 = t36 ** 2
  t247 = t68 ** 2
  t250 = 0.1e1 / t78 / t238 * t241 * t34 / t38 / t244 * t247 * t25
  t253 = t26 * t149
  t256 = 0.1e1 / t21 / t71
  t259 = -0.440e3 / 0.27e2 * t253 + 0.154e3 / 0.27e2 * t30 * t256
  t263 = t90 * t105
  t268 = t33 * t56
  t269 = t157 * tau0
  t270 = t269 * t132
  t273 = t70 * t19
  t275 = 0.1e1 / t20 / t273
  t276 = t158 * t275
  t282 = params.k0 * (-t259 * t42 - 0.5e1 * t188 * t83 - 0.100e3 / 0.3e1 * t263 * t159 + 0.40e2 / 0.3e1 * t101 * t146 - 0.1000e4 / 0.9e1 * t268 * t270 + 0.800e3 / 0.9e1 * t156 * t276 - 0.440e3 / 0.27e2 * t92 * t253)
  t292 = 0.1e1 / t59 / t169 / t58
  t294 = t292 * t172 * t122
  t297 = t171 * t122
  t298 = t297 * t216
  t303 = params.e1 * t90
  t306 = t179 * t105
  t309 = t100 * t56
  t310 = t90 * t157
  t311 = t24 * t73
  t312 = t310 * t311
  t315 = t152 * tau0
  t316 = t315 * t184
  t319 = t25 * t87
  t320 = t183 * t319
  t323 = t49 * t259
  t326 = t118 * t269
  t334 = 0.6e1 * t303 * t188 + 0.20e2 * t306 * t83 + 0.200e3 * t309 * t312 + 0.20e2 * t182 * t316 - 0.160e3 / 0.3e1 * t182 * t320 + 0.2e1 * t100 * t323 + 0.4000e4 / 0.9e1 * t47 * t326 * t132 - 0.800e3 / 0.3e1 * t191 * t276 + 0.880e3 / 0.27e2 * t106 * t253
  t337 = params.c1 * t33
  t338 = t178 * t90
  t342 = t199 * t118
  t343 = t178 * tau0
  t350 = t113 * t210
  t361 = 0.1e1 / t55 / t104
  t362 = t361 * t269
  t370 = 0.6e1 * t109 * t196 + 0.2e1 * t51 * t334 + 0.24e2 * t337 * t56 * t338 + 0.240e3 * t342 * t343 * t184 + 0.36e2 * t199 * t114 * t152 + 0.4000e4 / 0.3e1 * t350 * t312 + 0.80e2 * t203 * t316 - 0.640e3 / 0.3e1 * t203 * t320 + 0.4e1 * t113 * t56 * t259 + 0.20000e5 / 0.9e1 * t54 * t362 * t132 - 0.8000e4 / 0.9e1 * t211 * t276 + 0.1760e4 / 0.27e2 * t119 * t253
  t371 = t99 * t370
  t374 = t282 * t60 - 0.3e1 / 0.4e1 * t165 * t123 + 0.15e2 / 0.16e2 * t96 * t173 - 0.3e1 / 0.4e1 * t96 * t217 - 0.45e2 / 0.64e2 * t45 * t294 + 0.15e2 / 0.16e2 * t45 * t298 - t45 * t371 / 0.4e1
  t380 = t17 / t273
  t388 = t17 / t20 / t131 / t70
  t393 = t244 ** 2
  t396 = t3 / t4 / t393
  t397 = t131 ** 2
  t402 = t396 * t17 / t21 / t397 / t19
  t405 = 0.1e1 / t78 / t238 / t77
  t409 = t241 * params.b * t247 * t68
  t410 = t62 * t405 * t409
  t414 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t23 * t62 * t79 + t18 * t28 * t126 * t79 / 0.4e1 - 0.355e3 / 0.10368e5 * t6 * t133 * t62 * t142 - 0.3e1 / 0.8e1 * t18 * t145 * t220 * t79 + 0.17e2 / 0.1152e4 * t6 * t227 * t126 * t142 + t6 * t235 * t62 * t250 / 0.512e3 - 0.3e1 / 0.8e1 * t18 * t20 * t374 * t79 - t6 * t380 * t220 * t142 / 0.384e3 - t6 * t388 * t126 * t250 / 0.3072e4 - 0.17e2 / 0.331776e6 * t402 * t410)
  t443 = t26 * t256
  t449 = 0.6160e4 / 0.81e2 * t443 - 0.2618e4 / 0.81e2 * t30 / t21 / t273
  t465 = t157 ** 2
  t470 = t465 / t21 / t131 / t19 * t25
  t473 = t131 * r0
  t474 = 0.1e1 / t473
  t480 = t158 / t20 / t225
  t485 = -t449 * t42 - 0.20e2 / 0.3e1 * t323 * t83 - 0.200e3 / 0.3e1 * t152 * t105 * t159 + 0.80e2 / 0.3e1 * t188 * t146 - 0.4000e4 / 0.9e1 * t114 * t270 + 0.3200e4 / 0.9e1 * t263 * t276 - 0.1760e4 / 0.27e2 * t101 * t253 - 0.20000e5 / 0.27e2 * t33 * t118 * t470 + 0.16000e5 / 0.9e1 * t268 * t269 * t474 - 0.54400e5 / 0.81e2 * t156 * t480 + 0.6160e4 / 0.81e2 * t92 * t443
  t498 = t169 ** 2
  t501 = t172 ** 2
  t509 = t216 ** 2
  t519 = t55 ** 2
  t525 = t310 * t24 * t275
  t528 = t315 * t319
  t532 = t183 * t25 * t149
  t542 = t196 ** 2
  t552 = t152 ** 2
  t571 = t152 * t157 * t311
  t575 = t259 * tau0 * t184
  t583 = t90 * t269 * t132
  t592 = -0.6400e4 / 0.3e1 * t309 * t525 - 0.320e3 / 0.3e1 * t182 * t528 + 0.7040e4 / 0.27e2 * t182 * t532 + 0.6e1 * params.e1 * t552 * t49 + 0.8e1 * t303 * t323 + 0.2e1 * t100 * t49 * t449 + 0.54400e5 / 0.27e2 * t191 * t480 - 0.12320e5 / 0.81e2 * t106 * t443 + 0.80e2 * t303 * t105 * t316 - 0.320e3 / 0.3e1 * t306 * t146 + 0.400e3 * t309 * t571 + 0.80e2 / 0.3e1 * t182 * t575 + 0.400e3 * t179 * t56 * t159 + 0.32000e5 / 0.9e1 * t100 * t118 * t583 - 0.64000e5 / 0.9e1 * t47 * t326 * t474 + 0.100000e6 / 0.27e2 * t47 * t210 * t470
  t595 = t178 ** 2
  t599 = -0.320000e6 / 0.9e1 * t54 * t362 * t474 + 0.700000e6 / 0.27e2 * t54 / t519 * t470 - 0.128000e6 / 0.9e1 * t350 * t525 - 0.1280e4 / 0.3e1 * t203 * t528 + 0.28160e5 / 0.27e2 * t203 * t532 + 0.960e3 * t199 * t118 * t90 * t316 - 0.1280e4 * t342 * t343 * t319 + 0.6e1 * t542 + 0.8e1 * t109 * t334 + 0.2e1 * t51 * t592 + 0.24e2 * params.c1 * t595 * t56
  t633 = 0.4e1 * t113 * t56 * t449 + 0.144e3 * t337 * t200 * t152 + 0.36e2 * t199 * t56 * t552 + 0.48e2 * t199 * t114 * t259 - 0.24640e5 / 0.81e2 * t119 * t443 + 0.640e3 * t337 * t118 * t338 * tau0 * t184 + 0.8000e4 * t199 * t210 * t178 * t157 * t311 + 0.8000e4 / 0.3e1 * t350 * t571 + 0.320e3 / 0.3e1 * t203 * t575 + 0.544000e6 / 0.81e2 * t211 * t480 + 0.320000e6 / 0.9e1 * t113 * t361 * t583
  t638 = params.k0 * t485 * t60 - t282 * t123 + 0.15e2 / 0.8e1 * t165 * t173 - 0.3e1 / 0.2e1 * t165 * t217 - 0.45e2 / 0.16e2 * t96 * t294 + 0.15e2 / 0.4e1 * t96 * t298 - t96 * t371 + 0.585e3 / 0.256e3 * t45 / t59 / t498 * t501 - 0.135e3 / 0.32e2 * t45 * t292 * t172 * t216 + 0.15e2 / 0.16e2 * t45 * t171 * t509 + 0.5e1 / 0.4e1 * t45 * t297 * t370 - t45 * t99 * (t599 + t633) / 0.4e1
  t681 = t238 ** 2
  t684 = t241 ** 2
  t686 = t247 ** 2
  t693 = -0.17e2 / 0.82944e5 * t402 * t126 * t405 * t409 + 0.935e3 / 0.497664e6 * t396 * t17 / t21 / t397 / t85 * t410 + 0.10e2 / 0.27e2 * t18 * t87 * t62 * t79 - 0.5e1 / 0.9e1 * t18 * t23 * t126 * t79 + t18 * t28 * t220 * t79 / 0.2e1 - t18 * t145 * t374 * t79 / 0.2e1 - 0.3e1 / 0.8e1 * t18 * t20 * t638 * t79 + 0.4255e4 / 0.15552e5 * t6 * t17 * t474 * t62 * t142 - 0.355e3 / 0.2592e4 * t6 * t133 * t126 * t142 - 0.2515e4 / 0.82944e5 * t6 * t17 / t20 / t131 / t273 * t62 * t250 + 0.17e2 / 0.576e3 * t6 * t227 * t220 * t142 + t6 * t235 * t126 * t250 / 0.128e3 - t6 * t380 * t374 * t142 / 0.288e3 - t6 * t388 * t220 * t250 / 0.1536e4 - 0.425e3 / 0.143327232e9 * t396 * t17 / t397 / t473 * t62 / t78 / t681 * t684 * t686 * t35 * t66 * t24
  t694 = f.my_piecewise3(t2, 0, t693)
  v4rho4_0_ = 0.2e1 * r0 * t694 + 0.8e1 * t414

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
  t32 = r0 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t36 = tau0 / t33 / r0
  t37 = r0 ** 2
  t39 = 0.1e1 / t33 / t37
  t42 = t36 - s0 * t39 / 0.8e1
  t43 = 6 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = jnp.pi ** 2
  t46 = t45 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t49 = 0.3e1 / 0.10e2 * t44 * t47
  t50 = t36 - t49
  t51 = 0.1e1 / t50
  t54 = params.k0 * (-t42 * t51 + 0.1e1)
  t55 = t42 ** 2
  t56 = params.e1 * t55
  t57 = t50 ** 2
  t58 = 0.1e1 / t57
  t60 = t56 * t58 + 0.1e1
  t61 = t60 ** 2
  t62 = t55 ** 2
  t63 = params.c1 * t62
  t64 = t57 ** 2
  t65 = 0.1e1 / t64
  t67 = t63 * t65 + t61
  t68 = t67 ** (0.1e1 / 0.4e1)
  t69 = 0.1e1 / t68
  t71 = t54 * t69 + 0.1e1
  t73 = params.b * t44
  t75 = 0.1e1 / t46 / t45
  t76 = s0 ** 2
  t77 = t75 * t76
  t78 = t37 ** 2
  t81 = 0.1e1 / t32 / t78 / r0
  t85 = 0.1e1 + t73 * t77 * t81 / 0.576e3
  t86 = t85 ** (0.1e1 / 0.8e1)
  t87 = 0.1e1 / t86
  t88 = t31 * t71 * t87
  t91 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t92 = t91 * f.p.zeta_threshold
  t94 = f.my_piecewise3(t20, t92, t21 * t19)
  t95 = t5 * t94
  t96 = t31 ** 2
  t97 = 0.1e1 / t96
  t99 = t97 * t71 * t87
  t101 = t95 * t99 / 0.8e1
  t102 = tau0 * t39
  t104 = t37 * r0
  t106 = 0.1e1 / t33 / t104
  t109 = -0.5e1 / 0.3e1 * t102 + s0 * t106 / 0.3e1
  t111 = t42 * t58
  t115 = params.k0 * (-t109 * t51 - 0.5e1 / 0.3e1 * t111 * t102)
  t118 = 0.1e1 / t68 / t67
  t119 = params.e1 * t42
  t120 = t58 * t109
  t124 = 0.1e1 / t57 / t50
  t125 = t124 * tau0
  t129 = 0.2e1 * t119 * t120 + 0.10e2 / 0.3e1 * t56 * t125 * t39
  t133 = params.c1 * t55 * t42
  t138 = 0.1e1 / t64 / t50
  t139 = t138 * tau0
  t143 = 0.2e1 * t60 * t129 + 0.4e1 * t133 * t65 * t109 + 0.20e2 / 0.3e1 * t63 * t139 * t39
  t144 = t118 * t143
  t147 = t115 * t69 - t54 * t144 / 0.4e1
  t149 = t31 * t147 * t87
  t152 = t94 * t31
  t154 = t5 * t152 * t71
  t158 = 0.1e1 / t86 / t85 * params.b * t44
  t163 = t158 * t77 / t32 / t78 / t37
  t167 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t88 - t101 - 0.3e1 / 0.8e1 * t95 * t149 - t154 * t163 / 0.2304e4)
  t169 = r1 <= f.p.dens_threshold
  t170 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t171 = 0.1e1 + t170
  t172 = t171 <= f.p.zeta_threshold
  t173 = t171 ** (0.1e1 / 0.3e1)
  t175 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t178 = f.my_piecewise3(t172, 0, 0.4e1 / 0.3e1 * t173 * t175)
  t179 = t5 * t178
  t180 = r1 ** (0.1e1 / 0.3e1)
  t181 = t180 ** 2
  t184 = tau1 / t181 / r1
  t185 = r1 ** 2
  t187 = 0.1e1 / t181 / t185
  t190 = t184 - s2 * t187 / 0.8e1
  t191 = t184 - t49
  t192 = 0.1e1 / t191
  t195 = params.k0 * (-t190 * t192 + 0.1e1)
  t196 = t190 ** 2
  t197 = params.e1 * t196
  t198 = t191 ** 2
  t199 = 0.1e1 / t198
  t201 = t197 * t199 + 0.1e1
  t202 = t201 ** 2
  t203 = t196 ** 2
  t204 = params.c1 * t203
  t205 = t198 ** 2
  t206 = 0.1e1 / t205
  t208 = t204 * t206 + t202
  t209 = t208 ** (0.1e1 / 0.4e1)
  t210 = 0.1e1 / t209
  t212 = t195 * t210 + 0.1e1
  t214 = s2 ** 2
  t215 = t75 * t214
  t216 = t185 ** 2
  t219 = 0.1e1 / t180 / t216 / r1
  t223 = 0.1e1 + t73 * t215 * t219 / 0.576e3
  t224 = t223 ** (0.1e1 / 0.8e1)
  t225 = 0.1e1 / t224
  t226 = t31 * t212 * t225
  t230 = f.my_piecewise3(t172, t92, t173 * t171)
  t231 = t5 * t230
  t233 = t97 * t212 * t225
  t235 = t231 * t233 / 0.8e1
  t237 = f.my_piecewise3(t169, 0, -0.3e1 / 0.8e1 * t179 * t226 - t235)
  t239 = t21 ** 2
  t240 = 0.1e1 / t239
  t241 = t26 ** 2
  t246 = t16 / t22 / t6
  t248 = -0.2e1 * t23 + 0.2e1 * t246
  t249 = f.my_piecewise5(t10, 0, t14, 0, t248)
  t253 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t240 * t241 + 0.4e1 / 0.3e1 * t21 * t249)
  t257 = t30 * t99
  t267 = 0.1e1 / t96 / t6
  t271 = t95 * t267 * t71 * t87 / 0.12e2
  t274 = t95 * t97 * t147 * t87
  t279 = t5 * t94 * t97 * t71 * t163
  t281 = tau0 * t106
  t287 = 0.40e2 / 0.9e1 * t281 - 0.11e2 / 0.9e1 * s0 / t33 / t78
  t292 = tau0 ** 2
  t303 = t67 ** 2
  t306 = t143 ** 2
  t310 = t129 ** 2
  t312 = t109 ** 2
  t318 = t109 * tau0 * t39
  t366 = t85 ** 2
  t369 = params.b ** 2
  t372 = t45 ** 2
  t374 = 0.1e1 / t47 / t372
  t375 = t76 ** 2
  t377 = t78 ** 2
  t392 = -0.3e1 / 0.8e1 * t5 * t253 * t88 - t257 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t149 - t5 * t29 * t31 * t71 * t163 / 0.1152e4 + t271 - t274 / 0.4e1 - t279 / 0.3456e4 - 0.3e1 / 0.8e1 * t95 * t31 * (params.k0 * (-t287 * t51 - 0.10e2 / 0.3e1 * t120 * t102 - 0.50e2 / 0.9e1 * t42 * t124 * t292 * t81 + 0.40e2 / 0.9e1 * t111 * t281) * t69 - t115 * t144 / 0.2e1 + 0.5e1 / 0.16e2 * t54 / t68 / t303 * t306 - t54 * t118 * (0.2e1 * t310 + 0.2e1 * t60 * (0.2e1 * params.e1 * t312 * t58 + 0.40e2 / 0.3e1 * t119 * t124 * t318 + 0.2e1 * t119 * t58 * t287 + 0.50e2 / 0.3e1 * t56 * t65 * t292 * t81 - 0.80e2 / 0.9e1 * t56 * t125 * t106) + 0.12e2 * params.c1 * t55 * t65 * t312 + 0.160e3 / 0.3e1 * t133 * t138 * t318 + 0.4e1 * t133 * t65 * t287 + 0.500e3 / 0.9e1 * t63 / t64 / t57 * t292 * t81 - 0.160e3 / 0.9e1 * t63 * t139 * t106) / 0.4e1) * t87 - t5 * t152 * t147 * t163 / 0.1152e4 - t154 / t86 / t366 * t369 * t43 * t374 * t375 / t33 / t377 / t78 / 0.36864e5 + 0.19e2 / 0.6912e4 * t154 * t158 * t77 / t32 / t78 / t104
  t393 = f.my_piecewise3(t1, 0, t392)
  t394 = t173 ** 2
  t395 = 0.1e1 / t394
  t396 = t175 ** 2
  t400 = f.my_piecewise5(t14, 0, t10, 0, -t248)
  t404 = f.my_piecewise3(t172, 0, 0.4e1 / 0.9e1 * t395 * t396 + 0.4e1 / 0.3e1 * t173 * t400)
  t408 = t179 * t233
  t413 = t231 * t267 * t212 * t225 / 0.12e2
  t415 = f.my_piecewise3(t169, 0, -0.3e1 / 0.8e1 * t5 * t404 * t226 - t408 / 0.4e1 + t413)
  d11 = 0.2e1 * t167 + 0.2e1 * t237 + t6 * (t393 + t415)
  t418 = -t7 - t24
  t419 = f.my_piecewise5(t10, 0, t14, 0, t418)
  t422 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t419)
  t423 = t5 * t422
  t427 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t423 * t88 - t101)
  t429 = f.my_piecewise5(t14, 0, t10, 0, -t418)
  t432 = f.my_piecewise3(t172, 0, 0.4e1 / 0.3e1 * t173 * t429)
  t433 = t5 * t432
  t436 = tau1 * t187
  t438 = t185 * r1
  t440 = 0.1e1 / t181 / t438
  t443 = -0.5e1 / 0.3e1 * t436 + s2 * t440 / 0.3e1
  t445 = t190 * t199
  t449 = params.k0 * (-t443 * t192 - 0.5e1 / 0.3e1 * t445 * t436)
  t452 = 0.1e1 / t209 / t208
  t453 = params.e1 * t190
  t454 = t199 * t443
  t458 = 0.1e1 / t198 / t191
  t459 = t458 * tau1
  t463 = 0.2e1 * t453 * t454 + 0.10e2 / 0.3e1 * t197 * t459 * t187
  t467 = params.c1 * t196 * t190
  t472 = 0.1e1 / t205 / t191
  t473 = t472 * tau1
  t477 = 0.2e1 * t201 * t463 + 0.4e1 * t467 * t206 * t443 + 0.20e2 / 0.3e1 * t204 * t473 * t187
  t478 = t452 * t477
  t481 = t449 * t210 - t195 * t478 / 0.4e1
  t483 = t31 * t481 * t225
  t486 = t230 * t31
  t488 = t5 * t486 * t212
  t492 = 0.1e1 / t224 / t223 * params.b * t44
  t497 = t492 * t215 / t180 / t216 / t185
  t501 = f.my_piecewise3(t169, 0, -0.3e1 / 0.8e1 * t433 * t226 - t235 - 0.3e1 / 0.8e1 * t231 * t483 - t488 * t497 / 0.2304e4)
  t505 = 0.2e1 * t246
  t506 = f.my_piecewise5(t10, 0, t14, 0, t505)
  t510 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t240 * t419 * t26 + 0.4e1 / 0.3e1 * t21 * t506)
  t514 = t423 * t99
  t527 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t510 * t88 - t514 / 0.8e1 - 0.3e1 / 0.8e1 * t423 * t149 - t5 * t422 * t31 * t71 * t163 / 0.2304e4 - t257 / 0.8e1 + t271 - t274 / 0.8e1 - t279 / 0.6912e4)
  t531 = f.my_piecewise5(t14, 0, t10, 0, -t505)
  t535 = f.my_piecewise3(t172, 0, 0.4e1 / 0.9e1 * t395 * t429 * t175 + 0.4e1 / 0.3e1 * t173 * t531)
  t539 = t433 * t233
  t546 = t231 * t97 * t481 * t225
  t556 = t5 * t230 * t97 * t212 * t497
  t559 = f.my_piecewise3(t169, 0, -0.3e1 / 0.8e1 * t5 * t535 * t226 - t539 / 0.8e1 - t408 / 0.8e1 + t413 - 0.3e1 / 0.8e1 * t179 * t483 - t546 / 0.8e1 - t5 * t178 * t31 * t212 * t497 / 0.2304e4 - t556 / 0.6912e4)
  d12 = t167 + t237 + t427 + t501 + t6 * (t527 + t559)
  t564 = t419 ** 2
  t568 = 0.2e1 * t23 + 0.2e1 * t246
  t569 = f.my_piecewise5(t10, 0, t14, 0, t568)
  t573 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t240 * t564 + 0.4e1 / 0.3e1 * t21 * t569)
  t579 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t573 * t88 - t514 / 0.4e1 + t271)
  t580 = t429 ** 2
  t584 = f.my_piecewise5(t14, 0, t10, 0, -t568)
  t588 = f.my_piecewise3(t172, 0, 0.4e1 / 0.9e1 * t395 * t580 + 0.4e1 / 0.3e1 * t173 * t584)
  t602 = tau1 * t440
  t608 = 0.40e2 / 0.9e1 * t602 - 0.11e2 / 0.9e1 * s2 / t181 / t216
  t613 = tau1 ** 2
  t624 = t208 ** 2
  t627 = t477 ** 2
  t631 = t463 ** 2
  t633 = t443 ** 2
  t639 = t443 * tau1 * t187
  t687 = t223 ** 2
  t692 = t214 ** 2
  t694 = t216 ** 2
  t709 = -0.3e1 / 0.8e1 * t5 * t588 * t226 - t539 / 0.4e1 - 0.3e1 / 0.4e1 * t433 * t483 - t5 * t432 * t31 * t212 * t497 / 0.1152e4 + t413 - t546 / 0.4e1 - t556 / 0.3456e4 - 0.3e1 / 0.8e1 * t231 * t31 * (params.k0 * (-t608 * t192 - 0.10e2 / 0.3e1 * t454 * t436 - 0.50e2 / 0.9e1 * t190 * t458 * t613 * t219 + 0.40e2 / 0.9e1 * t445 * t602) * t210 - t449 * t478 / 0.2e1 + 0.5e1 / 0.16e2 * t195 / t209 / t624 * t627 - t195 * t452 * (0.2e1 * t631 + 0.2e1 * t201 * (0.2e1 * params.e1 * t633 * t199 + 0.40e2 / 0.3e1 * t453 * t458 * t639 + 0.2e1 * t453 * t199 * t608 + 0.50e2 / 0.3e1 * t197 * t206 * t613 * t219 - 0.80e2 / 0.9e1 * t197 * t459 * t440) + 0.12e2 * params.c1 * t196 * t206 * t633 + 0.160e3 / 0.3e1 * t467 * t472 * t639 + 0.4e1 * t467 * t206 * t608 + 0.500e3 / 0.9e1 * t204 / t205 / t198 * t613 * t219 - 0.160e3 / 0.9e1 * t204 * t473 * t440) / 0.4e1) * t225 - t5 * t486 * t481 * t497 / 0.1152e4 - t488 / t224 / t687 * t369 * t43 * t374 * t692 / t181 / t694 / t216 / 0.36864e5 + 0.19e2 / 0.6912e4 * t488 * t492 * t215 / t180 / t216 / t438
  t710 = f.my_piecewise3(t169, 0, t709)
  d22 = 0.2e1 * t427 + 0.2e1 * t501 + t6 * (t579 + t710)
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
  t44 = r0 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t48 = tau0 / t45 / r0
  t49 = r0 ** 2
  t51 = 0.1e1 / t45 / t49
  t54 = t48 - s0 * t51 / 0.8e1
  t55 = 6 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = jnp.pi ** 2
  t58 = t57 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t61 = 0.3e1 / 0.10e2 * t56 * t59
  t62 = t48 - t61
  t63 = 0.1e1 / t62
  t66 = params.k0 * (-t54 * t63 + 0.1e1)
  t67 = t54 ** 2
  t68 = params.e1 * t67
  t69 = t62 ** 2
  t70 = 0.1e1 / t69
  t72 = t68 * t70 + 0.1e1
  t73 = t72 ** 2
  t74 = t67 ** 2
  t75 = params.c1 * t74
  t76 = t69 ** 2
  t77 = 0.1e1 / t76
  t79 = t75 * t77 + t73
  t80 = t79 ** (0.1e1 / 0.4e1)
  t81 = 0.1e1 / t80
  t83 = t66 * t81 + 0.1e1
  t85 = params.b * t56
  t87 = 0.1e1 / t58 / t57
  t88 = s0 ** 2
  t89 = t87 * t88
  t90 = t49 ** 2
  t91 = t90 * r0
  t93 = 0.1e1 / t44 / t91
  t97 = 0.1e1 + t85 * t89 * t93 / 0.576e3
  t98 = t97 ** (0.1e1 / 0.8e1)
  t99 = 0.1e1 / t98
  t100 = t43 * t83 * t99
  t105 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t106 = t5 * t105
  t107 = t43 ** 2
  t108 = 0.1e1 / t107
  t110 = t108 * t83 * t99
  t113 = tau0 * t51
  t115 = t49 * r0
  t117 = 0.1e1 / t45 / t115
  t120 = -0.5e1 / 0.3e1 * t113 + s0 * t117 / 0.3e1
  t122 = t54 * t70
  t126 = params.k0 * (-t120 * t63 - 0.5e1 / 0.3e1 * t122 * t113)
  t129 = 0.1e1 / t80 / t79
  t130 = params.e1 * t54
  t131 = t70 * t120
  t134 = t69 * t62
  t135 = 0.1e1 / t134
  t136 = t135 * tau0
  t137 = t136 * t51
  t140 = 0.2e1 * t130 * t131 + 0.10e2 / 0.3e1 * t68 * t137
  t144 = params.c1 * t67 * t54
  t145 = t77 * t120
  t149 = 0.1e1 / t76 / t62
  t150 = t149 * tau0
  t154 = 0.2e1 * t72 * t140 + 0.4e1 * t144 * t145 + 0.20e2 / 0.3e1 * t75 * t150 * t51
  t155 = t129 * t154
  t158 = t126 * t81 - t66 * t155 / 0.4e1
  t160 = t43 * t158 * t99
  t163 = t105 * t43
  t165 = t5 * t163 * t83
  t169 = 0.1e1 / t98 / t97 * params.b * t56
  t172 = 0.1e1 / t44 / t90 / t49
  t174 = t169 * t89 * t172
  t177 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t178 = t177 * f.p.zeta_threshold
  t180 = f.my_piecewise3(t20, t178, t21 * t19)
  t181 = t5 * t180
  t183 = 0.1e1 / t107 / t6
  t185 = t183 * t83 * t99
  t189 = t108 * t158 * t99
  t192 = t180 * t108
  t194 = t5 * t192 * t83
  t197 = tau0 * t117
  t200 = 0.1e1 / t45 / t90
  t203 = 0.40e2 / 0.9e1 * t197 - 0.11e2 / 0.9e1 * s0 * t200
  t207 = t54 * t135
  t208 = tau0 ** 2
  t209 = t208 * t93
  t215 = params.k0 * (-t203 * t63 - 0.10e2 / 0.3e1 * t131 * t113 - 0.50e2 / 0.9e1 * t207 * t209 + 0.40e2 / 0.9e1 * t122 * t197)
  t219 = t79 ** 2
  t221 = 0.1e1 / t80 / t219
  t222 = t154 ** 2
  t223 = t221 * t222
  t226 = t140 ** 2
  t228 = t120 ** 2
  t229 = params.e1 * t228
  t232 = t130 * t135
  t233 = t120 * tau0
  t234 = t233 * t51
  t237 = t70 * t203
  t240 = t77 * t208
  t247 = 0.2e1 * t229 * t70 + 0.40e2 / 0.3e1 * t232 * t234 + 0.2e1 * t130 * t237 + 0.50e2 / 0.3e1 * t68 * t240 * t93 - 0.80e2 / 0.9e1 * t68 * t136 * t117
  t250 = params.c1 * t67
  t254 = t144 * t149
  t261 = 0.1e1 / t76 / t69
  t262 = t261 * t208
  t269 = 0.2e1 * t226 + 0.2e1 * t72 * t247 + 0.12e2 * t250 * t77 * t228 + 0.160e3 / 0.3e1 * t254 * t234 + 0.4e1 * t144 * t77 * t203 + 0.500e3 / 0.9e1 * t75 * t262 * t93 - 0.160e3 / 0.9e1 * t75 * t150 * t117
  t270 = t129 * t269
  t273 = t215 * t81 - t126 * t155 / 0.2e1 + 0.5e1 / 0.16e2 * t66 * t223 - t66 * t270 / 0.4e1
  t275 = t43 * t273 * t99
  t278 = t180 * t43
  t280 = t5 * t278 * t158
  t284 = t5 * t278 * t83
  t285 = t97 ** 2
  t288 = params.b ** 2
  t290 = 0.1e1 / t98 / t285 * t288 * t55
  t291 = t57 ** 2
  t294 = t88 ** 2
  t295 = 0.1e1 / t59 / t291 * t294
  t296 = t90 ** 2
  t301 = t290 * t295 / t45 / t296 / t90
  t308 = t169 * t89 / t44 / t90 / t115
  t311 = -0.3e1 / 0.8e1 * t42 * t100 - t106 * t110 / 0.4e1 - 0.3e1 / 0.4e1 * t106 * t160 - t165 * t174 / 0.1152e4 + t181 * t185 / 0.12e2 - t181 * t189 / 0.4e1 - t194 * t174 / 0.3456e4 - 0.3e1 / 0.8e1 * t181 * t275 - t280 * t174 / 0.1152e4 - t284 * t301 / 0.36864e5 + 0.19e2 / 0.6912e4 * t284 * t308
  t312 = f.my_piecewise3(t1, 0, t311)
  t314 = r1 <= f.p.dens_threshold
  t315 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t316 = 0.1e1 + t315
  t317 = t316 <= f.p.zeta_threshold
  t318 = t316 ** (0.1e1 / 0.3e1)
  t319 = t318 ** 2
  t320 = 0.1e1 / t319
  t322 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t323 = t322 ** 2
  t327 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t331 = f.my_piecewise3(t317, 0, 0.4e1 / 0.9e1 * t320 * t323 + 0.4e1 / 0.3e1 * t318 * t327)
  t332 = t5 * t331
  t333 = r1 ** (0.1e1 / 0.3e1)
  t334 = t333 ** 2
  t337 = tau1 / t334 / r1
  t338 = r1 ** 2
  t343 = t337 - s2 / t334 / t338 / 0.8e1
  t344 = t337 - t61
  t349 = t343 ** 2
  t351 = t344 ** 2
  t355 = (0.1e1 + params.e1 * t349 / t351) ** 2
  t356 = t349 ** 2
  t358 = t351 ** 2
  t362 = (t355 + params.c1 * t356 / t358) ** (0.1e1 / 0.4e1)
  t365 = 0.1e1 + params.k0 * (0.1e1 - t343 / t344) / t362
  t367 = s2 ** 2
  t369 = t338 ** 2
  t377 = (0.1e1 + t85 * t87 * t367 / t333 / t369 / r1 / 0.576e3) ** (0.1e1 / 0.8e1)
  t378 = 0.1e1 / t377
  t379 = t43 * t365 * t378
  t384 = f.my_piecewise3(t317, 0, 0.4e1 / 0.3e1 * t318 * t322)
  t385 = t5 * t384
  t387 = t108 * t365 * t378
  t391 = f.my_piecewise3(t317, t178, t318 * t316)
  t392 = t5 * t391
  t394 = t183 * t365 * t378
  t398 = f.my_piecewise3(t314, 0, -0.3e1 / 0.8e1 * t332 * t379 - t385 * t387 / 0.4e1 + t392 * t394 / 0.12e2)
  t400 = tau0 * t200
  t406 = -0.440e3 / 0.27e2 * t400 + 0.154e3 / 0.27e2 * s0 / t45 / t91
  t416 = t208 * tau0
  t417 = 0.1e1 / t296
  t455 = t120 * t208 * t93
  t459 = t203 * tau0 * t51
  t462 = t233 * t117
  t516 = 0.6e1 * t140 * t247 + 0.2e1 * t72 * (0.6e1 * params.e1 * t120 * t237 + 0.20e2 * t229 * t137 + 0.100e3 * t130 * t77 * t455 + 0.20e2 * t232 * t459 - 0.160e3 / 0.3e1 * t232 * t462 + 0.2e1 * t130 * t70 * t406 + 0.1000e4 / 0.9e1 * t68 * t149 * t416 * t417 - 0.400e3 / 0.3e1 * t68 * t240 * t172 + 0.880e3 / 0.27e2 * t68 * t136 * t200) + 0.24e2 * params.c1 * t54 * t77 * t228 * t120 + 0.240e3 * t250 * t149 * t228 * tau0 * t51 + 0.36e2 * t250 * t145 * t203 + 0.2000e4 / 0.3e1 * t144 * t261 * t455 + 0.80e2 * t254 * t459 - 0.640e3 / 0.3e1 * t254 * t462 + 0.4e1 * t144 * t77 * t406 + 0.5000e4 / 0.9e1 * t75 / t76 / t134 * t416 * t417 - 0.4000e4 / 0.9e1 * t75 * t262 * t172 + 0.1760e4 / 0.27e2 * t75 * t150 * t200
  t566 = -0.3e1 / 0.8e1 * t181 * t43 * (params.k0 * (-t406 * t63 - 0.5e1 * t237 * t113 - 0.50e2 / 0.3e1 * t120 * t135 * t209 + 0.40e2 / 0.3e1 * t131 * t197 - 0.250e3 / 0.9e1 * t54 * t77 * t416 * t417 + 0.400e3 / 0.9e1 * t207 * t208 * t172 - 0.440e3 / 0.27e2 * t122 * t400) * t81 - 0.3e1 / 0.4e1 * t215 * t155 + 0.15e2 / 0.16e2 * t126 * t223 - 0.3e1 / 0.4e1 * t126 * t270 - 0.45e2 / 0.64e2 * t66 / t80 / t219 / t79 * t222 * t154 + 0.15e2 / 0.16e2 * t66 * t221 * t154 * t269 - t66 * t129 * t516 / 0.4e1) * t99 + 0.19e2 / 0.6912e4 * t194 * t308 - t5 * t278 * t273 * t174 / 0.768e3 - t280 * t301 / 0.12288e5 - t5 * t41 * t43 * t83 * t174 / 0.768e3 - t5 * t105 * t108 * t83 * t174 / 0.1152e4 - t5 * t163 * t158 * t174 / 0.384e3 - t165 * t301 / 0.12288e5 + t5 * t180 * t183 * t83 * t174 / 0.3456e4 - t5 * t192 * t158 * t174 / 0.1152e4 - t194 * t301 / 0.36864e5 - 0.209e3 / 0.10368e5 * t284 * t169 * t89 / t44 / t296
  t587 = 0.1e1 / t107 / t24
  t600 = t24 ** 2
  t604 = 0.6e1 * t33 - 0.6e1 * t16 / t600
  t605 = f.my_piecewise5(t10, 0, t14, 0, t604)
  t609 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t605)
  t623 = t291 ** 2
  t635 = t296 ** 2
  t642 = 0.19e2 / 0.2304e4 * t280 * t308 + 0.19e2 / 0.36864e5 * t284 * t290 * t295 / t45 / t296 / t91 + 0.19e2 / 0.2304e4 * t165 * t308 - 0.3e1 / 0.8e1 * t181 * t108 * t273 * t99 - 0.3e1 / 0.8e1 * t42 * t110 + t106 * t185 / 0.4e1 - 0.5e1 / 0.36e2 * t181 * t587 * t83 * t99 - 0.3e1 / 0.8e1 * t5 * t609 * t100 - 0.9e1 / 0.8e1 * t42 * t160 - 0.3e1 / 0.4e1 * t106 * t189 - 0.9e1 / 0.8e1 * t106 * t275 + t181 * t183 * t158 * t99 / 0.4e1 - 0.17e2 / 0.5308416e7 * t2 / t3 / t623 * t278 * t83 / t98 / t285 / t97 * t288 * params.b * t294 * t88 / t635 / t115
  t644 = f.my_piecewise3(t1, 0, t566 + t642)
  t654 = f.my_piecewise5(t14, 0, t10, 0, -t604)
  t658 = f.my_piecewise3(t317, 0, -0.8e1 / 0.27e2 / t319 / t316 * t323 * t322 + 0.4e1 / 0.3e1 * t320 * t322 * t327 + 0.4e1 / 0.3e1 * t318 * t654)
  t671 = f.my_piecewise3(t314, 0, -0.3e1 / 0.8e1 * t5 * t658 * t379 - 0.3e1 / 0.8e1 * t332 * t387 + t385 * t394 / 0.4e1 - 0.5e1 / 0.36e2 * t392 * t587 * t365 * t378)
  d111 = 0.3e1 * t312 + 0.3e1 * t398 + t6 * (t644 + t671)

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
  t32 = r0 ** 2
  t33 = t32 * r0
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / t33
  t38 = tau0 * t37
  t40 = t32 ** 2
  t42 = 0.1e1 / t35 / t40
  t45 = 0.40e2 / 0.9e1 * t38 - 0.11e2 / 0.9e1 * s0 * t42
  t48 = tau0 / t35 / r0
  t49 = 6 ** (0.1e1 / 0.3e1)
  t50 = t49 ** 2
  t51 = jnp.pi ** 2
  t52 = t51 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t55 = 0.3e1 / 0.10e2 * t50 * t53
  t56 = t48 - t55
  t57 = 0.1e1 / t56
  t60 = 0.1e1 / t35 / t32
  t61 = tau0 * t60
  t65 = -0.5e1 / 0.3e1 * t61 + s0 * t37 / 0.3e1
  t66 = t56 ** 2
  t67 = 0.1e1 / t66
  t68 = t65 * t67
  t73 = t48 - s0 * t60 / 0.8e1
  t74 = t66 * t56
  t75 = 0.1e1 / t74
  t76 = t73 * t75
  t77 = tau0 ** 2
  t78 = t40 * r0
  t80 = 0.1e1 / t34 / t78
  t81 = t77 * t80
  t84 = t73 * t67
  t88 = params.k0 * (-t45 * t57 - 0.10e2 / 0.3e1 * t68 * t61 - 0.50e2 / 0.9e1 * t76 * t81 + 0.40e2 / 0.9e1 * t84 * t38)
  t89 = t73 ** 2
  t90 = params.e1 * t89
  t92 = t90 * t67 + 0.1e1
  t93 = t92 ** 2
  t94 = t89 ** 2
  t95 = params.c1 * t94
  t96 = t66 ** 2
  t97 = 0.1e1 / t96
  t99 = t95 * t97 + t93
  t100 = t99 ** (0.1e1 / 0.4e1)
  t101 = 0.1e1 / t100
  t107 = params.k0 * (-t65 * t57 - 0.5e1 / 0.3e1 * t84 * t61)
  t109 = 0.1e1 / t100 / t99
  t110 = params.e1 * t73
  t113 = t75 * tau0
  t114 = t113 * t60
  t117 = 0.2e1 * t110 * t68 + 0.10e2 / 0.3e1 * t90 * t114
  t121 = params.c1 * t89 * t73
  t122 = t97 * t65
  t126 = 0.1e1 / t96 / t56
  t127 = t126 * tau0
  t131 = 0.2e1 * t92 * t117 + 0.4e1 * t121 * t122 + 0.20e2 / 0.3e1 * t95 * t127 * t60
  t132 = t109 * t131
  t137 = params.k0 * (-t73 * t57 + 0.1e1)
  t138 = t99 ** 2
  t140 = 0.1e1 / t100 / t138
  t141 = t131 ** 2
  t142 = t140 * t141
  t145 = t117 ** 2
  t147 = t65 ** 2
  t148 = params.e1 * t147
  t151 = t110 * t75
  t152 = t65 * tau0
  t153 = t152 * t60
  t156 = t67 * t45
  t159 = t97 * t77
  t160 = t159 * t80
  t163 = t113 * t37
  t166 = 0.2e1 * t148 * t67 + 0.40e2 / 0.3e1 * t151 * t153 + 0.2e1 * t110 * t156 + 0.50e2 / 0.3e1 * t90 * t160 - 0.80e2 / 0.9e1 * t90 * t163
  t169 = params.c1 * t89
  t170 = t97 * t147
  t173 = t121 * t126
  t180 = 0.1e1 / t96 / t66
  t181 = t180 * t77
  t188 = 0.2e1 * t145 + 0.2e1 * t92 * t166 + 0.12e2 * t169 * t170 + 0.160e3 / 0.3e1 * t173 * t153 + 0.4e1 * t121 * t97 * t45 + 0.500e3 / 0.9e1 * t95 * t181 * t80 - 0.160e3 / 0.9e1 * t95 * t127 * t37
  t189 = t109 * t188
  t192 = t88 * t101 - t107 * t132 / 0.2e1 + 0.5e1 / 0.16e2 * t137 * t142 - t137 * t189 / 0.4e1
  t194 = params.b * t50
  t196 = 0.1e1 / t52 / t51
  t197 = s0 ** 2
  t198 = t196 * t197
  t202 = 0.1e1 + t194 * t198 * t80 / 0.576e3
  t203 = t202 ** (0.1e1 / 0.8e1)
  t204 = 0.1e1 / t203
  t205 = t31 * t192 * t204
  t208 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t209 = t208 * f.p.zeta_threshold
  t211 = f.my_piecewise3(t20, t209, t21 * t19)
  t212 = t5 * t211
  t213 = tau0 * t42
  t216 = 0.1e1 / t35 / t78
  t219 = -0.440e3 / 0.27e2 * t213 + 0.154e3 / 0.27e2 * s0 * t216
  t223 = t65 * t75
  t228 = t73 * t97
  t229 = t77 * tau0
  t230 = t40 ** 2
  t231 = 0.1e1 / t230
  t232 = t229 * t231
  t235 = t40 * t32
  t237 = 0.1e1 / t34 / t235
  t238 = t77 * t237
  t244 = params.k0 * (-t219 * t57 - 0.5e1 * t156 * t61 - 0.50e2 / 0.3e1 * t223 * t81 + 0.40e2 / 0.3e1 * t68 * t38 - 0.250e3 / 0.9e1 * t228 * t232 + 0.400e3 / 0.9e1 * t76 * t238 - 0.440e3 / 0.27e2 * t84 * t213)
  t254 = 0.1e1 / t100 / t138 / t99
  t256 = t254 * t141 * t131
  t259 = t140 * t131
  t260 = t259 * t188
  t265 = params.e1 * t65
  t270 = t110 * t97
  t271 = t65 * t77
  t272 = t271 * t80
  t275 = t45 * tau0
  t276 = t275 * t60
  t279 = t152 * t37
  t282 = t67 * t219
  t285 = t126 * t229
  t295 = 0.6e1 * t265 * t156 + 0.20e2 * t148 * t114 + 0.100e3 * t270 * t272 + 0.20e2 * t151 * t276 - 0.160e3 / 0.3e1 * t151 * t279 + 0.2e1 * t110 * t282 + 0.1000e4 / 0.9e1 * t90 * t285 * t231 - 0.400e3 / 0.3e1 * t90 * t159 * t237 + 0.880e3 / 0.27e2 * t90 * t113 * t42
  t298 = params.c1 * t73
  t299 = t147 * t65
  t303 = t169 * t126
  t304 = t147 * tau0
  t311 = t121 * t180
  t322 = 0.1e1 / t96 / t74
  t323 = t322 * t229
  t333 = 0.6e1 * t117 * t166 + 0.2e1 * t92 * t295 + 0.24e2 * t298 * t97 * t299 + 0.240e3 * t303 * t304 * t60 + 0.36e2 * t169 * t122 * t45 + 0.2000e4 / 0.3e1 * t311 * t272 + 0.80e2 * t173 * t276 - 0.640e3 / 0.3e1 * t173 * t279 + 0.4e1 * t121 * t97 * t219 + 0.5000e4 / 0.9e1 * t95 * t323 * t231 - 0.4000e4 / 0.9e1 * t95 * t181 * t237 + 0.1760e4 / 0.27e2 * t95 * t127 * t42
  t334 = t109 * t333
  t337 = t244 * t101 - 0.3e1 / 0.4e1 * t88 * t132 + 0.15e2 / 0.16e2 * t107 * t142 - 0.3e1 / 0.4e1 * t107 * t189 - 0.45e2 / 0.64e2 * t137 * t256 + 0.15e2 / 0.16e2 * t137 * t260 - t137 * t334 / 0.4e1
  t339 = t31 * t337 * t204
  t342 = t21 ** 2
  t343 = 0.1e1 / t342
  t344 = t26 ** 2
  t347 = t22 * t6
  t348 = 0.1e1 / t347
  t351 = 0.2e1 * t16 * t348 - 0.2e1 * t23
  t352 = f.my_piecewise5(t10, 0, t14, 0, t351)
  t356 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t343 * t344 + 0.4e1 / 0.3e1 * t21 * t352)
  t357 = t5 * t356
  t358 = t31 ** 2
  t359 = 0.1e1 / t358
  t361 = t137 * t101 + 0.1e1
  t363 = t359 * t361 * t204
  t367 = 0.1e1 / t358 / t6
  t369 = t367 * t361 * t204
  t373 = 0.1e1 / t358 / t22
  t375 = t373 * t361 * t204
  t379 = 0.1e1 / t342 / t19
  t383 = t343 * t26
  t386 = t22 ** 2
  t387 = 0.1e1 / t386
  t390 = -0.6e1 * t16 * t387 + 0.6e1 * t348
  t391 = f.my_piecewise5(t10, 0, t14, 0, t390)
  t395 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t379 * t344 * t26 + 0.4e1 / 0.3e1 * t383 * t352 + 0.4e1 / 0.3e1 * t21 * t391)
  t396 = t5 * t395
  t398 = t31 * t361 * t204
  t404 = t107 * t101 - t137 * t132 / 0.4e1
  t406 = t31 * t404 * t204
  t410 = t359 * t404 * t204
  t414 = t359 * t192 * t204
  t418 = t367 * t404 * t204
  t421 = t211 * t31
  t422 = t421 * t361
  t423 = t5 * t422
  t427 = 0.1e1 / t203 / t202 * params.b * t50
  t431 = t427 * t198 / t34 / t230
  t435 = t5 * t421 * t404
  t438 = 0.1e1 / t34 / t40 / t33
  t440 = t427 * t198 * t438
  t443 = -0.9e1 / 0.8e1 * t30 * t205 - 0.3e1 / 0.8e1 * t212 * t339 - 0.3e1 / 0.8e1 * t357 * t363 + t30 * t369 / 0.4e1 - 0.5e1 / 0.36e2 * t212 * t375 - 0.3e1 / 0.8e1 * t396 * t398 - 0.9e1 / 0.8e1 * t357 * t406 - 0.3e1 / 0.4e1 * t30 * t410 - 0.3e1 / 0.8e1 * t212 * t414 + t212 * t418 / 0.4e1 - 0.209e3 / 0.10368e5 * t423 * t431 + 0.19e2 / 0.2304e4 * t435 * t440
  t444 = t202 ** 2
  t447 = params.b ** 2
  t449 = 0.1e1 / t203 / t444 * t447 * t49
  t450 = t51 ** 2
  t453 = t197 ** 2
  t454 = 0.1e1 / t53 / t450 * t453
  t459 = t449 * t454 / t35 / t230 / t78
  t462 = t29 * t31
  t464 = t5 * t462 * t361
  t467 = t211 * t359
  t469 = t5 * t467 * t361
  t473 = t5 * t421 * t192
  t475 = t427 * t198 * t237
  t482 = t449 * t454 / t35 / t230 / t40
  t485 = t356 * t31
  t487 = t5 * t485 * t361
  t490 = t29 * t359
  t492 = t5 * t490 * t361
  t496 = t5 * t462 * t404
  t501 = t211 * t367
  t503 = t5 * t501 * t361
  t507 = t5 * t467 * t404
  t512 = t450 ** 2
  t515 = t2 / t3 / t512
  t516 = t515 * t421
  t519 = 0.1e1 / t203 / t444 / t202
  t520 = t361 * t519
  t523 = t447 * params.b * t453 * t197
  t524 = t230 ** 2
  t527 = t523 / t524 / t33
  t528 = t520 * t527
  t531 = 0.19e2 / 0.36864e5 * t423 * t459 + 0.19e2 / 0.2304e4 * t464 * t440 + 0.19e2 / 0.6912e4 * t469 * t440 - t473 * t475 / 0.768e3 - t435 * t482 / 0.12288e5 - t487 * t475 / 0.768e3 - t492 * t475 / 0.1152e4 - t496 * t475 / 0.384e3 - t464 * t482 / 0.12288e5 + t503 * t475 / 0.3456e4 - t507 * t475 / 0.1152e4 - t469 * t482 / 0.36864e5 - 0.17e2 / 0.5308416e7 * t516 * t528
  t533 = f.my_piecewise3(t1, 0, t443 + t531)
  t535 = r1 <= f.p.dens_threshold
  t536 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t537 = 0.1e1 + t536
  t538 = t537 <= f.p.zeta_threshold
  t539 = t537 ** (0.1e1 / 0.3e1)
  t540 = t539 ** 2
  t542 = 0.1e1 / t540 / t537
  t544 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t545 = t544 ** 2
  t549 = 0.1e1 / t540
  t550 = t549 * t544
  t552 = f.my_piecewise5(t14, 0, t10, 0, -t351)
  t556 = f.my_piecewise5(t14, 0, t10, 0, -t390)
  t560 = f.my_piecewise3(t538, 0, -0.8e1 / 0.27e2 * t542 * t545 * t544 + 0.4e1 / 0.3e1 * t550 * t552 + 0.4e1 / 0.3e1 * t539 * t556)
  t561 = t5 * t560
  t562 = r1 ** (0.1e1 / 0.3e1)
  t563 = t562 ** 2
  t566 = tau1 / t563 / r1
  t567 = r1 ** 2
  t572 = t566 - s2 / t563 / t567 / 0.8e1
  t573 = t566 - t55
  t578 = t572 ** 2
  t580 = t573 ** 2
  t584 = (0.1e1 + params.e1 * t578 / t580) ** 2
  t585 = t578 ** 2
  t587 = t580 ** 2
  t591 = (t584 + params.c1 * t585 / t587) ** (0.1e1 / 0.4e1)
  t594 = 0.1e1 + params.k0 * (0.1e1 - t572 / t573) / t591
  t596 = s2 ** 2
  t598 = t567 ** 2
  t606 = (0.1e1 + t194 * t196 * t596 / t562 / t598 / r1 / 0.576e3) ** (0.1e1 / 0.8e1)
  t607 = 0.1e1 / t606
  t608 = t31 * t594 * t607
  t616 = f.my_piecewise3(t538, 0, 0.4e1 / 0.9e1 * t549 * t545 + 0.4e1 / 0.3e1 * t539 * t552)
  t617 = t5 * t616
  t619 = t359 * t594 * t607
  t624 = f.my_piecewise3(t538, 0, 0.4e1 / 0.3e1 * t539 * t544)
  t625 = t5 * t624
  t627 = t367 * t594 * t607
  t631 = f.my_piecewise3(t538, t209, t539 * t537)
  t632 = t5 * t631
  t634 = t373 * t594 * t607
  t638 = f.my_piecewise3(t535, 0, -0.3e1 / 0.8e1 * t561 * t608 - 0.3e1 / 0.8e1 * t617 * t619 + t625 * t627 / 0.4e1 - 0.5e1 / 0.36e2 * t632 * t634)
  t640 = tau0 * t216
  t646 = 0.6160e4 / 0.81e2 * t640 - 0.2618e4 / 0.81e2 * s0 / t35 / t235
  t662 = t77 ** 2
  t665 = 0.1e1 / t35 / t230 / t32
  t669 = t230 * r0
  t670 = 0.1e1 / t669
  t679 = -t646 * t57 - 0.20e2 / 0.3e1 * t282 * t61 - 0.100e3 / 0.3e1 * t45 * t75 * t81 + 0.80e2 / 0.3e1 * t156 * t38 - 0.1000e4 / 0.9e1 * t122 * t232 + 0.1600e4 / 0.9e1 * t223 * t238 - 0.1760e4 / 0.27e2 * t68 * t213 - 0.5000e4 / 0.27e2 * t73 * t126 * t662 * t665 + 0.4000e4 / 0.9e1 * t228 * t229 * t670 - 0.27200e5 / 0.81e2 * t76 * t77 * t438 + 0.6160e4 / 0.81e2 * t84 * t640
  t692 = t138 ** 2
  t695 = t141 ** 2
  t703 = t188 ** 2
  t710 = t166 ** 2
  t720 = t271 * t237
  t723 = t275 * t37
  t726 = t152 * t42
  t729 = t45 ** 2
  t744 = t45 * t77 * t80
  t749 = t65 * t229 * t231
  t753 = t219 * tau0 * t60
  t765 = 0.200e3 * t148 * t160 + 0.25000e5 / 0.27e2 * t90 * t180 * t662 * t665 - 0.3200e4 / 0.3e1 * t270 * t720 - 0.320e3 / 0.3e1 * t151 * t723 + 0.7040e4 / 0.27e2 * t151 * t726 + 0.6e1 * params.e1 * t729 * t67 + 0.8e1 * t265 * t282 + 0.2e1 * t110 * t67 * t646 + 0.80e2 * t265 * t75 * t276 - 0.320e3 / 0.3e1 * t148 * t163 + 0.200e3 * t270 * t744 + 0.8000e4 / 0.9e1 * t110 * t126 * t749 + 0.80e2 / 0.3e1 * t151 * t753 - 0.16000e5 / 0.9e1 * t90 * t285 * t670 + 0.27200e5 / 0.27e2 * t90 * t159 * t438 - 0.12320e5 / 0.81e2 * t90 * t113 * t216
  t777 = t96 ** 2
  t793 = 0.6e1 * t710 + 0.8e1 * t117 * t295 + 0.2e1 * t92 * t765 + 0.144e3 * t298 * t170 * t45 + 0.36e2 * t169 * t97 * t729 + 0.48e2 * t169 * t122 * t219 + 0.175000e6 / 0.27e2 * t95 / t777 * t662 * t665 - 0.64000e5 / 0.9e1 * t311 * t720 - 0.1280e4 / 0.3e1 * t173 * t723 + 0.28160e5 / 0.27e2 * t173 * t726 + 0.960e3 * t303 * t152 * t60 * t45
  t797 = t147 ** 2
  t830 = -0.1280e4 * t303 * t304 * t37 + 0.24e2 * params.c1 * t797 * t97 + 0.4e1 * t121 * t97 * t646 + 0.640e3 * t298 * t126 * t299 * tau0 * t60 + 0.4000e4 * t169 * t180 * t147 * t77 * t80 + 0.4000e4 / 0.3e1 * t311 * t744 + 0.80000e5 / 0.9e1 * t121 * t322 * t749 + 0.320e3 / 0.3e1 * t173 * t753 - 0.80000e5 / 0.9e1 * t95 * t323 * t670 + 0.272000e6 / 0.81e2 * t95 * t181 * t438 - 0.24640e5 / 0.81e2 * t95 * t127 * t216
  t835 = params.k0 * t679 * t101 - t244 * t132 + 0.15e2 / 0.8e1 * t88 * t142 - 0.3e1 / 0.2e1 * t88 * t189 - 0.45e2 / 0.16e2 * t107 * t256 + 0.15e2 / 0.4e1 * t107 * t260 - t107 * t334 + 0.585e3 / 0.256e3 * t137 / t100 / t692 * t695 - 0.135e3 / 0.32e2 * t137 * t254 * t141 * t188 + 0.15e2 / 0.16e2 * t137 * t140 * t703 + 0.5e1 / 0.4e1 * t137 * t259 * t333 - t137 * t109 * (t793 + t830) / 0.4e1
  t848 = t19 ** 2
  t851 = t344 ** 2
  t857 = t352 ** 2
  t866 = -0.24e2 * t387 + 0.24e2 * t16 / t386 / t6
  t867 = f.my_piecewise5(t10, 0, t14, 0, t866)
  t871 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t342 / t848 * t851 - 0.16e2 / 0.9e1 * t379 * t344 * t352 + 0.4e1 / 0.3e1 * t343 * t857 + 0.16e2 / 0.9e1 * t383 * t391 + 0.4e1 / 0.3e1 * t21 * t867)
  t892 = -0.3e1 / 0.8e1 * t212 * t31 * t835 * t204 + t212 * t367 * t192 * t204 / 0.2e1 - 0.5e1 / 0.9e1 * t212 * t373 * t404 * t204 - 0.3e1 / 0.8e1 * t5 * t871 * t398 - 0.3e1 / 0.2e1 * t396 * t406 - 0.9e1 / 0.4e1 * t357 * t205 - 0.3e1 / 0.2e1 * t30 * t414 - 0.3e1 / 0.2e1 * t30 * t339 - t396 * t363 / 0.2e1 - 0.3e1 / 0.2e1 * t357 * t410 + t30 * t418 - t212 * t359 * t337 * t204 / 0.2e1
  t898 = 0.1e1 / t358 / t347
  t930 = t357 * t369 / 0.2e1 - 0.5e1 / 0.9e1 * t30 * t375 + 0.10e2 / 0.27e2 * t212 * t898 * t361 * t204 + 0.19e2 / 0.9216e4 * t435 * t459 + t503 * t482 / 0.27648e5 + 0.19e2 / 0.1728e4 * t492 * t440 + 0.19e2 / 0.1728e4 * t507 * t440 + 0.19e2 / 0.27648e5 * t469 * t459 - t5 * t462 * t192 * t475 / 0.192e3 - t5 * t421 * t337 * t475 / 0.576e3 - t473 * t482 / 0.6144e4 - t496 * t482 / 0.3072e4 - t5 * t395 * t31 * t361 * t475 / 0.576e3
  t972 = -t5 * t485 * t404 * t475 / 0.192e3 - t487 * t482 / 0.6144e4 - t5 * t490 * t404 * t475 / 0.288e3 - t492 * t482 / 0.9216e4 + 0.5225e4 / 0.31104e5 * t423 * t427 * t198 / t34 / t669 + 0.19e2 / 0.576e3 * t496 * t440 + 0.19e2 / 0.9216e4 * t464 * t459 - 0.5e1 / 0.7776e4 * t5 * t211 * t373 * t361 * t475 + 0.19e2 / 0.1152e4 * t487 * t440 + t5 * t29 * t367 * t361 * t475 / 0.864e3 - t5 * t467 * t192 * t475 / 0.576e3 + 0.19e2 / 0.1152e4 * t473 * t440
  t985 = t444 ** 2
  t988 = t447 ** 2
  t990 = t453 ** 2
  t1031 = -t507 * t482 / 0.9216e4 - t5 * t356 * t359 * t361 * t475 / 0.576e3 - 0.19e2 / 0.5184e4 * t503 * t440 - 0.209e3 / 0.7776e4 * t469 * t431 - 0.425e3 / 0.4586471424e10 * t515 * t422 / t203 / t985 * t988 * t990 / t34 / t524 / t669 * t50 * t196 - 0.209e3 / 0.2592e4 * t464 * t431 - 0.209e3 / 0.2592e4 * t435 * t431 - 0.2755e4 / 0.331776e6 * t423 * t449 * t454 / t35 / t230 / t235 + t5 * t501 * t404 * t475 / 0.864e3 - 0.17e2 / 0.1327104e7 * t516 * t404 * t519 * t527 - 0.17e2 / 0.1327104e7 * t515 * t462 * t528 - 0.17e2 / 0.3981312e7 * t515 * t467 * t528 + 0.323e3 / 0.2654208e7 * t516 * t520 * t523 / t524 / t40
  t1034 = f.my_piecewise3(t1, 0, t892 + t930 + t972 + t1031)
  t1035 = t537 ** 2
  t1038 = t545 ** 2
  t1044 = t552 ** 2
  t1050 = f.my_piecewise5(t14, 0, t10, 0, -t866)
  t1054 = f.my_piecewise3(t538, 0, 0.40e2 / 0.81e2 / t540 / t1035 * t1038 - 0.16e2 / 0.9e1 * t542 * t545 * t552 + 0.4e1 / 0.3e1 * t549 * t1044 + 0.16e2 / 0.9e1 * t550 * t556 + 0.4e1 / 0.3e1 * t539 * t1050)
  t1069 = f.my_piecewise3(t535, 0, -0.3e1 / 0.8e1 * t5 * t1054 * t608 - t561 * t619 / 0.2e1 + t617 * t627 / 0.2e1 - 0.5e1 / 0.9e1 * t625 * t634 + 0.10e2 / 0.27e2 * t632 * t898 * t594 * t607)
  d1111 = 0.4e1 * t533 + 0.4e1 * t638 + t6 * (t1034 + t1069)

  res = {'v4rho4': d1111}
  return res
