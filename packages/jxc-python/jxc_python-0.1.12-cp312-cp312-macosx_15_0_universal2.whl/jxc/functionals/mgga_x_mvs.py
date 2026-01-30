"""Generated from mgga_x_mvs.mpl."""

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

  mvs_f = lambda x, u, t: (1 + params_k0 * mvs_fa(mvs_alpha(t, x))) / (1 + params_b * (X2S * x) ** 4) ** (1 / 8)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mvs_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  mvs_f = lambda x, u, t: (1 + params_k0 * mvs_fa(mvs_alpha(t, x))) / (1 + params_b * (X2S * x) ** 4) ** (1 / 8)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mvs_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  mvs_f = lambda x, u, t: (1 + params_k0 * mvs_fa(mvs_alpha(t, x))) / (1 + params_b * (X2S * x) ** 4) ** (1 / 8)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mvs_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t33 = r0 ** 2
  t35 = 0.1e1 / t29 / t33
  t38 = tau0 * t31 - s0 * t35 / 0.8e1
  t39 = 6 ** (0.1e1 / 0.3e1)
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t48 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t38 * t39 * t44)
  t49 = t38 ** 2
  t51 = t39 ** 2
  t53 = 0.1e1 / t42 / t41
  t54 = t51 * t53
  t57 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t49 * t54
  t58 = t57 ** 2
  t59 = t49 ** 2
  t61 = t41 ** 2
  t64 = t39 / t43 / t61
  t67 = t58 + 0.1250e4 / 0.2187e4 * params.c1 * t59 * t64
  t68 = t67 ** (0.1e1 / 0.4e1)
  t69 = 0.1e1 / t68
  t71 = t48 * t69 + 0.1e1
  t73 = params.b * t51
  t74 = s0 ** 2
  t75 = t53 * t74
  t76 = t33 ** 2
  t79 = 0.1e1 / t28 / t76 / r0
  t83 = 0.1e1 + t73 * t75 * t79 / 0.576e3
  t84 = t83 ** (0.1e1 / 0.8e1)
  t85 = 0.1e1 / t84
  t86 = t27 * t71 * t85
  t89 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t86)
  t90 = r1 <= f.p.dens_threshold
  t91 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t92 = 0.1e1 + t91
  t93 = t92 <= f.p.zeta_threshold
  t94 = t92 ** (0.1e1 / 0.3e1)
  t96 = f.my_piecewise3(t93, t22, t94 * t92)
  t97 = t5 * t96
  t98 = r1 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t101 = 0.1e1 / t99 / r1
  t103 = r1 ** 2
  t105 = 0.1e1 / t99 / t103
  t108 = tau1 * t101 - s2 * t105 / 0.8e1
  t113 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t108 * t39 * t44)
  t114 = t108 ** 2
  t118 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t114 * t54
  t119 = t118 ** 2
  t120 = t114 ** 2
  t124 = t119 + 0.1250e4 / 0.2187e4 * params.c1 * t120 * t64
  t125 = t124 ** (0.1e1 / 0.4e1)
  t126 = 0.1e1 / t125
  t128 = t113 * t126 + 0.1e1
  t130 = s2 ** 2
  t131 = t53 * t130
  t132 = t103 ** 2
  t135 = 0.1e1 / t98 / t132 / r1
  t139 = 0.1e1 + t73 * t131 * t135 / 0.576e3
  t140 = t139 ** (0.1e1 / 0.8e1)
  t141 = 0.1e1 / t140
  t142 = t27 * t128 * t141
  t145 = f.my_piecewise3(t90, 0, -0.3e1 / 0.8e1 * t97 * t142)
  t146 = t6 ** 2
  t148 = t16 / t146
  t149 = t7 - t148
  t150 = f.my_piecewise5(t10, 0, t14, 0, t149)
  t153 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t150)
  t157 = t27 ** 2
  t158 = 0.1e1 / t157
  t162 = t26 * t158 * t71 * t85 / 0.8e1
  t170 = -0.5e1 / 0.3e1 * tau0 * t35 + s0 / t29 / t33 / r0 / 0.3e1
  t172 = t39 * t44
  t173 = t172 * t69
  t177 = 0.1e1 / t68 / t67
  t179 = t57 * params.e1 * t38
  t184 = params.c1 * t49 * t38
  t199 = t5 * t25 * t27 * t71
  t203 = 0.1e1 / t84 / t83 * params.b * t51
  t212 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t153 * t86 - t162 - 0.3e1 / 0.8e1 * t26 * t27 * (-0.5e1 / 0.9e1 * params.k0 * t170 * t173 - t48 * t177 * (0.100e3 / 0.81e2 * t179 * t54 * t170 + 0.5000e4 / 0.2187e4 * t184 * t64 * t170) / 0.4e1) * t85 - t199 * t203 * t75 / t28 / t76 / t33 / 0.2304e4)
  t214 = f.my_piecewise5(t14, 0, t10, 0, -t149)
  t217 = f.my_piecewise3(t93, 0, 0.4e1 / 0.3e1 * t94 * t214)
  t224 = t97 * t158 * t128 * t141 / 0.8e1
  t226 = f.my_piecewise3(t90, 0, -0.3e1 / 0.8e1 * t5 * t217 * t142 - t224)
  vrho_0_ = t89 + t145 + t6 * (t212 + t226)
  t229 = -t7 - t148
  t230 = f.my_piecewise5(t10, 0, t14, 0, t229)
  t233 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t230)
  t238 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t233 * t86 - t162)
  t240 = f.my_piecewise5(t14, 0, t10, 0, -t229)
  t243 = f.my_piecewise3(t93, 0, 0.4e1 / 0.3e1 * t94 * t240)
  t254 = -0.5e1 / 0.3e1 * tau1 * t105 + s2 / t99 / t103 / r1 / 0.3e1
  t256 = t172 * t126
  t260 = 0.1e1 / t125 / t124
  t262 = t118 * params.e1 * t108
  t267 = params.c1 * t114 * t108
  t282 = t5 * t96 * t27 * t128
  t286 = 0.1e1 / t140 / t139 * params.b * t51
  t295 = f.my_piecewise3(t90, 0, -0.3e1 / 0.8e1 * t5 * t243 * t142 - t224 - 0.3e1 / 0.8e1 * t97 * t27 * (-0.5e1 / 0.9e1 * params.k0 * t254 * t256 - t113 * t260 * (0.100e3 / 0.81e2 * t262 * t54 * t254 + 0.5000e4 / 0.2187e4 * t267 * t64 * t254) / 0.4e1) * t141 - t282 * t286 * t131 / t98 / t132 / t103 / 0.2304e4)
  vrho_1_ = t89 + t145 + t6 * (t238 + t295)
  t322 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (0.5e1 / 0.72e2 * params.k0 * t35 * t173 - t48 * t177 * (-0.25e2 / 0.162e3 * t179 * t54 * t35 - 0.625e3 / 0.2187e4 * t184 * t64 * t35) / 0.4e1) * t85 + t199 * t203 * t53 * s0 * t79 / 0.6144e4)
  vsigma_0_ = t6 * t322
  vsigma_1_ = 0.0e0
  t347 = f.my_piecewise3(t90, 0, -0.3e1 / 0.8e1 * t97 * t27 * (0.5e1 / 0.72e2 * params.k0 * t105 * t256 - t113 * t260 * (-0.25e2 / 0.162e3 * t262 * t54 * t105 - 0.625e3 / 0.2187e4 * t267 * t64 * t105) / 0.4e1) * t141 + t282 * t286 * t53 * s2 * t135 / 0.6144e4)
  vsigma_2_ = t6 * t347
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t366 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (-0.5e1 / 0.9e1 * params.k0 * t31 * t173 - t48 * t177 * (0.100e3 / 0.81e2 * t179 * t54 * t31 + 0.5000e4 / 0.2187e4 * t184 * t64 * t31) / 0.4e1) * t85)
  vtau_0_ = t6 * t366
  t385 = f.my_piecewise3(t90, 0, -0.3e1 / 0.8e1 * t97 * t27 * (-0.5e1 / 0.9e1 * params.k0 * t101 * t256 - t113 * t260 * (0.100e3 / 0.81e2 * t262 * t54 * t101 + 0.5000e4 / 0.2187e4 * t267 * t64 * t101) / 0.4e1) * t141)
  vtau_1_ = t6 * t385
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

  mvs_f = lambda x, u, t: (1 + params_k0 * mvs_fa(mvs_alpha(t, x))) / (1 + params_b * (X2S * x) ** 4) ** (1 / 8)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mvs_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t27 = s0 * t21
  t28 = r0 ** 2
  t30 = 0.1e1 / t23 / t28
  t33 = t22 * t25 - t27 * t30 / 0.8e1
  t34 = 6 ** (0.1e1 / 0.3e1)
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t43 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t33 * t34 * t39)
  t44 = t33 ** 2
  t46 = t34 ** 2
  t48 = 0.1e1 / t37 / t36
  t49 = t46 * t48
  t52 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t44 * t49
  t53 = t52 ** 2
  t54 = t44 ** 2
  t56 = t36 ** 2
  t58 = 0.1e1 / t38 / t56
  t59 = t34 * t58
  t62 = t53 + 0.1250e4 / 0.2187e4 * params.c1 * t54 * t59
  t63 = t62 ** (0.1e1 / 0.4e1)
  t64 = 0.1e1 / t63
  t66 = t43 * t64 + 0.1e1
  t70 = s0 ** 2
  t72 = t28 ** 2
  t73 = t72 * r0
  t79 = 0.1e1 + params.b * t46 * t48 * t70 * t20 / t19 / t73 / 0.288e3
  t80 = t79 ** (0.1e1 / 0.8e1)
  t81 = 0.1e1 / t80
  t85 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t66 * t81)
  t98 = -0.5e1 / 0.3e1 * t22 * t30 + t27 / t23 / t28 / r0 / 0.3e1
  t101 = t34 * t39 * t64
  t105 = 0.1e1 / t63 / t62
  t107 = t52 * params.e1 * t33
  t112 = params.c1 * t44 * t33
  t133 = 0.1e1 / t80 / t79 * params.b * t46
  t140 = f.my_piecewise3(t2, 0, -t18 / t23 * t66 * t81 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (-0.5e1 / 0.9e1 * params.k0 * t98 * t101 - t43 * t105 * (0.100e3 / 0.81e2 * t107 * t49 * t98 + 0.5000e4 / 0.2187e4 * t112 * t59 * t98) / 0.4e1) * t81 - t6 * t17 / t72 / t28 * t66 * t133 * t48 * t70 * t20 / 0.1152e4)
  vrho_0_ = 0.2e1 * r0 * t140 + 0.2e1 * t85
  t143 = params.k0 * t21
  t151 = t112 * t34
  t152 = t58 * t21
  t175 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (0.5e1 / 0.72e2 * t143 * t30 * t101 - t43 * t105 * (-0.25e2 / 0.162e3 * t107 * t49 * t21 * t30 - 0.625e3 / 0.2187e4 * t151 * t152 * t30) / 0.4e1) * t81 + t6 * t17 / t73 * t66 * t133 * t48 * s0 * t20 / 0.3072e4)
  vsigma_0_ = 0.2e1 * r0 * t175
  vlapl_0_ = 0.0e0
  t196 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (-0.5e1 / 0.9e1 * t143 * t25 * t101 - t43 * t105 * (0.100e3 / 0.81e2 * t107 * t49 * t21 * t25 + 0.5000e4 / 0.2187e4 * t151 * t152 * t25) / 0.4e1) * t81)
  vtau_0_ = 0.2e1 * r0 * t196
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
  t28 = s0 * t23
  t29 = r0 ** 2
  t31 = 0.1e1 / t20 / t29
  t34 = t24 * t26 - t28 * t31 / 0.8e1
  t35 = 6 ** (0.1e1 / 0.3e1)
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t44 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t34 * t35 * t40)
  t45 = t34 ** 2
  t47 = t35 ** 2
  t49 = 0.1e1 / t38 / t37
  t50 = t47 * t49
  t53 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t45 * t50
  t54 = t53 ** 2
  t55 = t45 ** 2
  t57 = t37 ** 2
  t59 = 0.1e1 / t39 / t57
  t60 = t35 * t59
  t63 = t54 + 0.1250e4 / 0.2187e4 * params.c1 * t55 * t60
  t64 = t63 ** (0.1e1 / 0.4e1)
  t65 = 0.1e1 / t64
  t67 = t44 * t65 + 0.1e1
  t71 = s0 ** 2
  t73 = t29 ** 2
  t80 = 0.1e1 + params.b * t47 * t49 * t71 * t22 / t19 / t73 / r0 / 0.288e3
  t81 = t80 ** (0.1e1 / 0.8e1)
  t82 = 0.1e1 / t81
  t88 = t29 * r0
  t90 = 0.1e1 / t20 / t88
  t93 = -0.5e1 / 0.3e1 * t24 * t31 + t28 * t90 / 0.3e1
  t94 = params.k0 * t93
  t96 = t35 * t40 * t65
  t100 = 0.1e1 / t64 / t63
  t101 = t53 * params.e1
  t102 = t101 * t34
  t107 = params.c1 * t45 * t34
  t111 = 0.100e3 / 0.81e2 * t102 * t50 * t93 + 0.5000e4 / 0.2187e4 * t107 * t60 * t93
  t115 = -0.5e1 / 0.9e1 * t94 * t96 - t44 * t100 * t111 / 0.4e1
  t122 = t17 / t73 / t29
  t131 = 0.1e1 / t81 / t80 * params.b * t47 * t49 * t71 * t22
  t135 = f.my_piecewise3(t2, 0, -t18 * t21 * t67 * t82 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t115 * t82 - t6 * t122 * t67 * t131 / 0.1152e4)
  t158 = 0.40e2 / 0.9e1 * t24 * t90 - 0.11e2 / 0.9e1 * t28 / t20 / t73
  t167 = t63 ** 2
  t170 = t111 ** 2
  t174 = params.e1 ** 2
  t176 = t93 ** 2
  t177 = t60 * t176
  t206 = t73 ** 2
  t213 = t80 ** 2
  t216 = params.b ** 2
  t219 = t71 ** 2
  t226 = f.my_piecewise3(t2, 0, t18 * t26 * t67 * t82 / 0.12e2 - t18 * t21 * t115 * t82 / 0.4e1 + 0.17e2 / 0.3456e4 * t6 * t17 / t73 / t88 * t67 * t131 - 0.3e1 / 0.8e1 * t18 * t19 * (-0.5e1 / 0.9e1 * params.k0 * t158 * t96 + 0.5e1 / 0.18e2 * t94 * t35 * t40 * t100 * t111 + 0.5e1 / 0.16e2 * t44 / t64 / t167 * t170 - t44 * t100 * (0.10000e5 / 0.2187e4 * t174 * t45 * t177 + 0.100e3 / 0.81e2 * t101 * t176 * t47 * t49 + 0.100e3 / 0.81e2 * t102 * t50 * t158 + 0.5000e4 / 0.729e3 * params.c1 * t45 * t177 + 0.5000e4 / 0.2187e4 * t107 * t60 * t158) / 0.4e1) * t82 - t6 * t122 * t115 * t131 / 0.576e3 - t6 * t17 / t19 / t206 / t73 * t67 / t81 / t213 * t216 * t35 * t59 * t219 * t23 / 0.9216e4)
  v2rho2_0_ = 0.2e1 * r0 * t226 + 0.4e1 * t135
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
  t27 = s0 * t24
  t28 = r0 ** 2
  t30 = 0.1e1 / t20 / t28
  t33 = t25 * t22 - t27 * t30 / 0.8e1
  t34 = 6 ** (0.1e1 / 0.3e1)
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t43 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t33 * t34 * t39)
  t44 = t33 ** 2
  t46 = t34 ** 2
  t48 = 0.1e1 / t37 / t36
  t49 = t46 * t48
  t52 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t44 * t49
  t53 = t52 ** 2
  t54 = t44 ** 2
  t56 = t36 ** 2
  t58 = 0.1e1 / t38 / t56
  t59 = t34 * t58
  t62 = t53 + 0.1250e4 / 0.2187e4 * params.c1 * t54 * t59
  t63 = t62 ** (0.1e1 / 0.4e1)
  t64 = 0.1e1 / t63
  t66 = t43 * t64 + 0.1e1
  t70 = s0 ** 2
  t72 = t28 ** 2
  t73 = t72 * r0
  t79 = 0.1e1 + params.b * t46 * t48 * t70 * t23 / t19 / t73 / 0.288e3
  t80 = t79 ** (0.1e1 / 0.8e1)
  t81 = 0.1e1 / t80
  t85 = 0.1e1 / t20
  t88 = t28 * r0
  t90 = 0.1e1 / t20 / t88
  t93 = -0.5e1 / 0.3e1 * t25 * t30 + t27 * t90 / 0.3e1
  t94 = params.k0 * t93
  t96 = t34 * t39 * t64
  t100 = 0.1e1 / t63 / t62
  t101 = t52 * params.e1
  t102 = t101 * t33
  t107 = params.c1 * t44 * t33
  t111 = 0.100e3 / 0.81e2 * t102 * t49 * t93 + 0.5000e4 / 0.2187e4 * t107 * t59 * t93
  t115 = -0.5e1 / 0.9e1 * t94 * t96 - t43 * t100 * t111 / 0.4e1
  t122 = t17 / t72 / t88
  t131 = 0.1e1 / t80 / t79 * params.b * t46 * t48 * t70 * t23
  t137 = 0.1e1 / t20 / t72
  t140 = 0.40e2 / 0.9e1 * t25 * t90 - 0.11e2 / 0.9e1 * t27 * t137
  t141 = params.k0 * t140
  t144 = t94 * t34
  t145 = t39 * t100
  t146 = t145 * t111
  t149 = t62 ** 2
  t151 = 0.1e1 / t63 / t149
  t152 = t111 ** 2
  t156 = params.e1 ** 2
  t157 = t156 * t44
  t158 = t93 ** 2
  t159 = t59 * t158
  t166 = t49 * t140
  t169 = params.c1 * t44
  t175 = 0.10000e5 / 0.2187e4 * t157 * t159 + 0.100e3 / 0.81e2 * t101 * t158 * t46 * t48 + 0.100e3 / 0.81e2 * t102 * t166 + 0.5000e4 / 0.729e3 * t169 * t159 + 0.5000e4 / 0.2187e4 * t107 * t59 * t140
  t179 = -0.5e1 / 0.9e1 * t141 * t96 + 0.5e1 / 0.18e2 * t144 * t146 + 0.5e1 / 0.16e2 * t43 * t151 * t152 - t43 * t100 * t175 / 0.4e1
  t186 = t17 / t72 / t28
  t191 = t72 ** 2
  t195 = t17 / t19 / t191 / t72
  t198 = t79 ** 2
  t201 = params.b ** 2
  t204 = t70 ** 2
  t207 = 0.1e1 / t80 / t198 * t201 * t34 * t58 * t204 * t24
  t211 = f.my_piecewise3(t2, 0, t18 * t22 * t66 * t81 / 0.12e2 - t18 * t85 * t115 * t81 / 0.4e1 + 0.17e2 / 0.3456e4 * t6 * t122 * t66 * t131 - 0.3e1 / 0.8e1 * t18 * t19 * t179 * t81 - t6 * t186 * t115 * t131 / 0.576e3 - t6 * t195 * t66 * t207 / 0.9216e4)
  t249 = -0.440e3 / 0.27e2 * t25 * t137 + 0.154e3 / 0.27e2 * t27 / t20 / t73
  t276 = t59 * t158 * t93
  t281 = t58 * t93 * t140
  t316 = t56 ** 2
  t320 = t191 ** 2
  t337 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t30 * t66 * t81 + t18 * t22 * t115 * t81 / 0.4e1 - 0.355e3 / 0.10368e5 * t6 * t17 / t191 * t66 * t131 - 0.3e1 / 0.8e1 * t18 * t85 * t179 * t81 + 0.17e2 / 0.1152e4 * t6 * t122 * t115 * t131 + t6 * t17 / t19 / t191 / t73 * t66 * t207 / 0.512e3 - 0.3e1 / 0.8e1 * t18 * t19 * (-0.5e1 / 0.9e1 * params.k0 * t249 * t96 + 0.5e1 / 0.12e2 * t141 * t34 * t146 - 0.25e2 / 0.48e2 * t144 * t39 * t151 * t152 + 0.5e1 / 0.12e2 * t144 * t145 * t175 - 0.45e2 / 0.64e2 * t43 / t63 / t149 / t62 * t152 * t111 + 0.15e2 / 0.16e2 * t43 * t151 * t111 * t175 - t43 * t100 * (0.10000e5 / 0.729e3 * t156 * t33 * t276 + 0.10000e5 / 0.729e3 * t157 * t34 * t281 + 0.100e3 / 0.27e2 * t101 * t93 * t166 + 0.100e3 / 0.81e2 * t102 * t49 * t249 + 0.10000e5 / 0.729e3 * params.c1 * t33 * t276 + 0.5000e4 / 0.243e3 * t169 * t34 * t281 + 0.5000e4 / 0.2187e4 * t107 * t59 * t249) / 0.4e1) * t81 - t6 * t186 * t179 * t131 / 0.384e3 - t6 * t195 * t115 * t207 / 0.3072e4 - 0.17e2 / 0.331776e6 * t3 / t4 / t316 * t17 / t20 / t320 / t28 * t66 / t80 / t198 / t79 * t201 * params.b * t204 * t70)
  v3rho3_0_ = 0.2e1 * r0 * t337 + 0.6e1 * t211

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
  t30 = s0 * t25
  t33 = t26 * t28 - t30 * t23 / 0.8e1
  t34 = 6 ** (0.1e1 / 0.3e1)
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t43 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t33 * t34 * t39)
  t44 = t33 ** 2
  t46 = t34 ** 2
  t48 = 0.1e1 / t37 / t36
  t49 = t46 * t48
  t52 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t44 * t49
  t53 = t52 ** 2
  t54 = t44 ** 2
  t56 = t36 ** 2
  t58 = 0.1e1 / t38 / t56
  t59 = t34 * t58
  t62 = t53 + 0.1250e4 / 0.2187e4 * params.c1 * t54 * t59
  t63 = t62 ** (0.1e1 / 0.4e1)
  t64 = 0.1e1 / t63
  t66 = t43 * t64 + 0.1e1
  t70 = s0 ** 2
  t72 = t19 ** 2
  t73 = t72 * r0
  t79 = 0.1e1 + params.b * t46 * t48 * t70 * t24 / t20 / t73 / 0.288e3
  t80 = t79 ** (0.1e1 / 0.8e1)
  t81 = 0.1e1 / t80
  t87 = t19 * r0
  t89 = 0.1e1 / t21 / t87
  t92 = -0.5e1 / 0.3e1 * t26 * t23 + t30 * t89 / 0.3e1
  t93 = params.k0 * t92
  t95 = t34 * t39 * t64
  t99 = 0.1e1 / t63 / t62
  t100 = t52 * params.e1
  t101 = t100 * t33
  t106 = params.c1 * t44 * t33
  t110 = 0.100e3 / 0.81e2 * t101 * t49 * t92 + 0.5000e4 / 0.2187e4 * t106 * t59 * t92
  t114 = -0.5e1 / 0.9e1 * t93 * t95 - t43 * t99 * t110 / 0.4e1
  t119 = t72 ** 2
  t121 = t17 / t119
  t130 = 0.1e1 / t80 / t79 * params.b * t46 * t48 * t70 * t24
  t133 = 0.1e1 / t21
  t137 = 0.1e1 / t21 / t72
  t140 = 0.40e2 / 0.9e1 * t26 * t89 - 0.11e2 / 0.9e1 * t30 * t137
  t141 = params.k0 * t140
  t144 = t93 * t34
  t145 = t39 * t99
  t146 = t145 * t110
  t149 = t62 ** 2
  t151 = 0.1e1 / t63 / t149
  t152 = t110 ** 2
  t156 = params.e1 ** 2
  t157 = t156 * t44
  t158 = t92 ** 2
  t159 = t59 * t158
  t166 = t49 * t140
  t169 = params.c1 * t44
  t175 = 0.10000e5 / 0.2187e4 * t157 * t159 + 0.100e3 / 0.81e2 * t100 * t158 * t46 * t48 + 0.100e3 / 0.81e2 * t101 * t166 + 0.5000e4 / 0.729e3 * t169 * t159 + 0.5000e4 / 0.2187e4 * t106 * t59 * t140
  t179 = -0.5e1 / 0.9e1 * t141 * t95 + 0.5e1 / 0.18e2 * t144 * t146 + 0.5e1 / 0.16e2 * t43 * t151 * t152 - t43 * t99 * t175 / 0.4e1
  t186 = t17 / t72 / t87
  t194 = t17 / t20 / t119 / t73
  t197 = t79 ** 2
  t200 = params.b ** 2
  t203 = t70 ** 2
  t206 = 0.1e1 / t80 / t197 * t200 * t34 * t58 * t203 * t25
  t212 = 0.1e1 / t21 / t73
  t215 = -0.440e3 / 0.27e2 * t26 * t137 + 0.154e3 / 0.27e2 * t30 * t212
  t216 = params.k0 * t215
  t219 = t141 * t34
  t222 = t39 * t151
  t223 = t222 * t152
  t226 = t145 * t175
  t231 = 0.1e1 / t63 / t149 / t62
  t232 = t152 * t110
  t236 = t151 * t110
  t240 = t156 * t33
  t242 = t59 * t158 * t92
  t245 = t157 * t34
  t246 = t58 * t92
  t247 = t246 * t140
  t250 = t100 * t92
  t253 = t49 * t215
  t256 = params.c1 * t33
  t259 = t169 * t34
  t265 = 0.10000e5 / 0.729e3 * t240 * t242 + 0.10000e5 / 0.729e3 * t245 * t247 + 0.100e3 / 0.27e2 * t250 * t166 + 0.100e3 / 0.81e2 * t101 * t253 + 0.10000e5 / 0.729e3 * t256 * t242 + 0.5000e4 / 0.243e3 * t259 * t247 + 0.5000e4 / 0.2187e4 * t106 * t59 * t215
  t269 = -0.5e1 / 0.9e1 * t216 * t95 + 0.5e1 / 0.12e2 * t219 * t146 - 0.25e2 / 0.48e2 * t144 * t223 + 0.5e1 / 0.12e2 * t144 * t226 - 0.45e2 / 0.64e2 * t43 * t231 * t232 + 0.15e2 / 0.16e2 * t43 * t236 * t175 - t43 * t99 * t265 / 0.4e1
  t274 = t72 * t19
  t276 = t17 / t274
  t284 = t17 / t20 / t119 / t72
  t289 = t56 ** 2
  t292 = t3 / t4 / t289
  t293 = t119 ** 2
  t298 = t292 * t17 / t21 / t293 / t19
  t301 = 0.1e1 / t80 / t197 / t79
  t305 = t200 * params.b * t203 * t70
  t306 = t66 * t301 * t305
  t310 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t18 * t23 * t66 * t81 + t18 * t28 * t114 * t81 / 0.4e1 - 0.355e3 / 0.10368e5 * t6 * t121 * t66 * t130 - 0.3e1 / 0.8e1 * t18 * t133 * t179 * t81 + 0.17e2 / 0.1152e4 * t6 * t186 * t114 * t130 + t6 * t194 * t66 * t206 / 0.512e3 - 0.3e1 / 0.8e1 * t18 * t20 * t269 * t81 - t6 * t276 * t179 * t130 / 0.384e3 - t6 * t284 * t114 * t206 / 0.3072e4 - 0.17e2 / 0.331776e6 * t298 * t306)
  t345 = 0.6160e4 / 0.81e2 * t26 * t212 - 0.2618e4 / 0.81e2 * t30 / t21 / t274
  t367 = t149 ** 2
  t370 = t152 ** 2
  t378 = t175 ** 2
  t385 = t158 ** 2
  t391 = t58 * t158 * t140
  t394 = t140 ** 2
  t395 = t59 * t394
  t398 = t246 * t215
  t423 = 0.10000e5 / 0.729e3 * t156 * t385 * t59 + 0.20000e5 / 0.243e3 * t240 * t34 * t391 + 0.10000e5 / 0.729e3 * t157 * t395 + 0.40000e5 / 0.2187e4 * t245 * t398 + 0.100e3 / 0.27e2 * t100 * t394 * t46 * t48 + 0.400e3 / 0.81e2 * t250 * t253 + 0.100e3 / 0.81e2 * t101 * t49 * t345 + 0.10000e5 / 0.729e3 * params.c1 * t385 * t59 + 0.20000e5 / 0.243e3 * t256 * t34 * t391 + 0.5000e4 / 0.243e3 * t169 * t395 + 0.20000e5 / 0.729e3 * t259 * t398 + 0.5000e4 / 0.2187e4 * t106 * t59 * t345
  t427 = -0.5e1 / 0.9e1 * params.k0 * t345 * t95 + 0.5e1 / 0.9e1 * t216 * t34 * t146 - 0.25e2 / 0.24e2 * t219 * t223 + 0.5e1 / 0.6e1 * t219 * t226 + 0.25e2 / 0.16e2 * t144 * t39 * t231 * t232 - 0.25e2 / 0.12e2 * t144 * t222 * t110 * t175 + 0.5e1 / 0.9e1 * t144 * t145 * t265 + 0.585e3 / 0.256e3 * t43 / t63 / t367 * t370 - 0.135e3 / 0.32e2 * t43 * t231 * t152 * t175 + 0.15e2 / 0.16e2 * t43 * t151 * t378 + 0.5e1 / 0.4e1 * t43 * t236 * t265 - t43 * t99 * t423 / 0.4e1
  t432 = t119 * r0
  t472 = t197 ** 2
  t475 = t200 ** 2
  t477 = t203 ** 2
  t483 = 0.10e2 / 0.27e2 * t18 * t89 * t66 * t81 + 0.935e3 / 0.497664e6 * t292 * t17 / t21 / t293 / t87 * t306 - 0.17e2 / 0.82944e5 * t298 * t114 * t301 * t305 - 0.5e1 / 0.9e1 * t18 * t23 * t114 * t81 + t18 * t28 * t179 * t81 / 0.2e1 - t18 * t133 * t269 * t81 / 0.2e1 - 0.3e1 / 0.8e1 * t18 * t20 * t427 * t81 + 0.4255e4 / 0.15552e5 * t6 * t17 / t432 * t66 * t130 - 0.355e3 / 0.2592e4 * t6 * t121 * t114 * t130 - 0.2515e4 / 0.82944e5 * t6 * t17 / t20 / t119 / t274 * t66 * t206 + 0.17e2 / 0.576e3 * t6 * t186 * t179 * t130 + t6 * t194 * t114 * t206 / 0.128e3 - t6 * t276 * t269 * t130 / 0.288e3 - t6 * t284 * t179 * t206 / 0.1536e4 - 0.425e3 / 0.143327232e9 * t292 * t17 / t293 / t432 * t66 / t80 / t472 * t475 * t477 * t49 * t24
  t484 = f.my_piecewise3(t2, 0, t483)
  v4rho4_0_ = 0.2e1 * r0 * t484 + 0.8e1 * t310

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
  t37 = r0 ** 2
  t39 = 0.1e1 / t33 / t37
  t42 = tau0 / t33 / r0 - s0 * t39 / 0.8e1
  t43 = 6 ** (0.1e1 / 0.3e1)
  t45 = jnp.pi ** 2
  t46 = t45 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = 0.1e1 / t47
  t52 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t42 * t43 * t48)
  t53 = t42 ** 2
  t55 = t43 ** 2
  t57 = 0.1e1 / t46 / t45
  t58 = t55 * t57
  t61 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t53 * t58
  t62 = t61 ** 2
  t63 = t53 ** 2
  t65 = t45 ** 2
  t67 = 0.1e1 / t47 / t65
  t68 = t43 * t67
  t71 = t62 + 0.1250e4 / 0.2187e4 * params.c1 * t63 * t68
  t72 = t71 ** (0.1e1 / 0.4e1)
  t73 = 0.1e1 / t72
  t75 = t52 * t73 + 0.1e1
  t77 = params.b * t55
  t78 = s0 ** 2
  t79 = t57 * t78
  t80 = t37 ** 2
  t87 = 0.1e1 + t77 * t79 / t32 / t80 / r0 / 0.576e3
  t88 = t87 ** (0.1e1 / 0.8e1)
  t89 = 0.1e1 / t88
  t90 = t31 * t75 * t89
  t93 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t94 = t93 * f.p.zeta_threshold
  t96 = f.my_piecewise3(t20, t94, t21 * t19)
  t97 = t5 * t96
  t98 = t31 ** 2
  t99 = 0.1e1 / t98
  t101 = t99 * t75 * t89
  t103 = t97 * t101 / 0.8e1
  t106 = t37 * r0
  t108 = 0.1e1 / t33 / t106
  t111 = -0.5e1 / 0.3e1 * tau0 * t39 + s0 * t108 / 0.3e1
  t112 = params.k0 * t111
  t113 = t43 * t48
  t114 = t113 * t73
  t118 = 0.1e1 / t72 / t71
  t119 = t61 * params.e1
  t120 = t119 * t42
  t125 = params.c1 * t53 * t42
  t129 = 0.100e3 / 0.81e2 * t120 * t58 * t111 + 0.5000e4 / 0.2187e4 * t125 * t68 * t111
  t133 = -0.5e1 / 0.9e1 * t112 * t114 - t52 * t118 * t129 / 0.4e1
  t135 = t31 * t133 * t89
  t138 = t96 * t31
  t140 = t5 * t138 * t75
  t144 = 0.1e1 / t88 / t87 * params.b * t55
  t149 = t144 * t79 / t32 / t80 / t37
  t153 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t90 - t103 - 0.3e1 / 0.8e1 * t97 * t135 - t140 * t149 / 0.2304e4)
  t155 = r1 <= f.p.dens_threshold
  t156 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t157 = 0.1e1 + t156
  t158 = t157 <= f.p.zeta_threshold
  t159 = t157 ** (0.1e1 / 0.3e1)
  t161 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t164 = f.my_piecewise3(t158, 0, 0.4e1 / 0.3e1 * t159 * t161)
  t165 = t5 * t164
  t166 = r1 ** (0.1e1 / 0.3e1)
  t167 = t166 ** 2
  t171 = r1 ** 2
  t173 = 0.1e1 / t167 / t171
  t176 = tau1 / t167 / r1 - s2 * t173 / 0.8e1
  t181 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t176 * t43 * t48)
  t182 = t176 ** 2
  t186 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t182 * t58
  t187 = t186 ** 2
  t188 = t182 ** 2
  t192 = t187 + 0.1250e4 / 0.2187e4 * params.c1 * t188 * t68
  t193 = t192 ** (0.1e1 / 0.4e1)
  t194 = 0.1e1 / t193
  t196 = t181 * t194 + 0.1e1
  t198 = s2 ** 2
  t199 = t57 * t198
  t200 = t171 ** 2
  t207 = 0.1e1 + t77 * t199 / t166 / t200 / r1 / 0.576e3
  t208 = t207 ** (0.1e1 / 0.8e1)
  t209 = 0.1e1 / t208
  t210 = t31 * t196 * t209
  t214 = f.my_piecewise3(t158, t94, t159 * t157)
  t215 = t5 * t214
  t217 = t99 * t196 * t209
  t219 = t215 * t217 / 0.8e1
  t221 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t165 * t210 - t219)
  t223 = t21 ** 2
  t224 = 0.1e1 / t223
  t225 = t26 ** 2
  t230 = t16 / t22 / t6
  t232 = -0.2e1 * t23 + 0.2e1 * t230
  t233 = f.my_piecewise5(t10, 0, t14, 0, t232)
  t237 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t224 * t225 + 0.4e1 / 0.3e1 * t21 * t233)
  t241 = t30 * t101
  t251 = 0.1e1 / t98 / t6
  t255 = t97 * t251 * t75 * t89 / 0.12e2
  t258 = t97 * t99 * t133 * t89
  t263 = t5 * t96 * t99 * t75 * t149
  t271 = 0.40e2 / 0.9e1 * tau0 * t108 - 0.11e2 / 0.9e1 * s0 / t33 / t80
  t280 = t71 ** 2
  t283 = t129 ** 2
  t287 = params.e1 ** 2
  t289 = t111 ** 2
  t290 = t68 * t289
  t319 = t87 ** 2
  t322 = params.b ** 2
  t325 = t78 ** 2
  t327 = t80 ** 2
  t342 = -0.3e1 / 0.8e1 * t5 * t237 * t90 - t241 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t135 - t5 * t29 * t31 * t75 * t149 / 0.1152e4 + t255 - t258 / 0.4e1 - t263 / 0.3456e4 - 0.3e1 / 0.8e1 * t97 * t31 * (-0.5e1 / 0.9e1 * params.k0 * t271 * t114 + 0.5e1 / 0.18e2 * t112 * t43 * t48 * t118 * t129 + 0.5e1 / 0.16e2 * t52 / t72 / t280 * t283 - t52 * t118 * (0.10000e5 / 0.2187e4 * t287 * t53 * t290 + 0.100e3 / 0.81e2 * t119 * t289 * t55 * t57 + 0.100e3 / 0.81e2 * t120 * t58 * t271 + 0.5000e4 / 0.729e3 * params.c1 * t53 * t290 + 0.5000e4 / 0.2187e4 * t125 * t68 * t271) / 0.4e1) * t89 - t5 * t138 * t133 * t149 / 0.1152e4 - t140 / t88 / t319 * t322 * t43 * t67 * t325 / t33 / t327 / t80 / 0.36864e5 + 0.19e2 / 0.6912e4 * t140 * t144 * t79 / t32 / t80 / t106
  t343 = f.my_piecewise3(t1, 0, t342)
  t344 = t159 ** 2
  t345 = 0.1e1 / t344
  t346 = t161 ** 2
  t350 = f.my_piecewise5(t14, 0, t10, 0, -t232)
  t354 = f.my_piecewise3(t158, 0, 0.4e1 / 0.9e1 * t345 * t346 + 0.4e1 / 0.3e1 * t159 * t350)
  t358 = t165 * t217
  t363 = t215 * t251 * t196 * t209 / 0.12e2
  t365 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t5 * t354 * t210 - t358 / 0.4e1 + t363)
  d11 = 0.2e1 * t153 + 0.2e1 * t221 + t6 * (t343 + t365)
  t368 = -t7 - t24
  t369 = f.my_piecewise5(t10, 0, t14, 0, t368)
  t372 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t369)
  t373 = t5 * t372
  t377 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t373 * t90 - t103)
  t379 = f.my_piecewise5(t14, 0, t10, 0, -t368)
  t382 = f.my_piecewise3(t158, 0, 0.4e1 / 0.3e1 * t159 * t379)
  t383 = t5 * t382
  t388 = t171 * r1
  t390 = 0.1e1 / t167 / t388
  t393 = -0.5e1 / 0.3e1 * tau1 * t173 + s2 * t390 / 0.3e1
  t394 = params.k0 * t393
  t395 = t113 * t194
  t399 = 0.1e1 / t193 / t192
  t400 = t186 * params.e1
  t401 = t400 * t176
  t406 = params.c1 * t182 * t176
  t410 = 0.100e3 / 0.81e2 * t401 * t58 * t393 + 0.5000e4 / 0.2187e4 * t406 * t68 * t393
  t414 = -0.5e1 / 0.9e1 * t394 * t395 - t181 * t399 * t410 / 0.4e1
  t416 = t31 * t414 * t209
  t419 = t214 * t31
  t421 = t5 * t419 * t196
  t425 = 0.1e1 / t208 / t207 * params.b * t55
  t430 = t425 * t199 / t166 / t200 / t171
  t434 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t383 * t210 - t219 - 0.3e1 / 0.8e1 * t215 * t416 - t421 * t430 / 0.2304e4)
  t438 = 0.2e1 * t230
  t439 = f.my_piecewise5(t10, 0, t14, 0, t438)
  t443 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t224 * t369 * t26 + 0.4e1 / 0.3e1 * t21 * t439)
  t447 = t373 * t101
  t460 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t443 * t90 - t447 / 0.8e1 - 0.3e1 / 0.8e1 * t373 * t135 - t5 * t372 * t31 * t75 * t149 / 0.2304e4 - t241 / 0.8e1 + t255 - t258 / 0.8e1 - t263 / 0.6912e4)
  t464 = f.my_piecewise5(t14, 0, t10, 0, -t438)
  t468 = f.my_piecewise3(t158, 0, 0.4e1 / 0.9e1 * t345 * t379 * t161 + 0.4e1 / 0.3e1 * t159 * t464)
  t472 = t383 * t217
  t479 = t215 * t99 * t414 * t209
  t489 = t5 * t214 * t99 * t196 * t430
  t492 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t5 * t468 * t210 - t472 / 0.8e1 - t358 / 0.8e1 + t363 - 0.3e1 / 0.8e1 * t165 * t416 - t479 / 0.8e1 - t5 * t164 * t31 * t196 * t430 / 0.2304e4 - t489 / 0.6912e4)
  d12 = t153 + t221 + t377 + t434 + t6 * (t460 + t492)
  t497 = t369 ** 2
  t501 = 0.2e1 * t23 + 0.2e1 * t230
  t502 = f.my_piecewise5(t10, 0, t14, 0, t501)
  t506 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t224 * t497 + 0.4e1 / 0.3e1 * t21 * t502)
  t512 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t506 * t90 - t447 / 0.4e1 + t255)
  t513 = t379 ** 2
  t517 = f.my_piecewise5(t14, 0, t10, 0, -t501)
  t521 = f.my_piecewise3(t158, 0, 0.4e1 / 0.9e1 * t345 * t513 + 0.4e1 / 0.3e1 * t159 * t517)
  t541 = 0.40e2 / 0.9e1 * tau1 * t390 - 0.11e2 / 0.9e1 * s2 / t167 / t200
  t550 = t192 ** 2
  t553 = t410 ** 2
  t558 = t393 ** 2
  t559 = t68 * t558
  t588 = t207 ** 2
  t593 = t198 ** 2
  t595 = t200 ** 2
  t610 = -0.3e1 / 0.8e1 * t5 * t521 * t210 - t472 / 0.4e1 - 0.3e1 / 0.4e1 * t383 * t416 - t5 * t382 * t31 * t196 * t430 / 0.1152e4 + t363 - t479 / 0.4e1 - t489 / 0.3456e4 - 0.3e1 / 0.8e1 * t215 * t31 * (-0.5e1 / 0.9e1 * params.k0 * t541 * t395 + 0.5e1 / 0.18e2 * t394 * t43 * t48 * t399 * t410 + 0.5e1 / 0.16e2 * t181 / t193 / t550 * t553 - t181 * t399 * (0.10000e5 / 0.2187e4 * t287 * t182 * t559 + 0.100e3 / 0.81e2 * t400 * t558 * t55 * t57 + 0.100e3 / 0.81e2 * t401 * t58 * t541 + 0.5000e4 / 0.729e3 * params.c1 * t182 * t559 + 0.5000e4 / 0.2187e4 * t406 * t68 * t541) / 0.4e1) * t209 - t5 * t419 * t414 * t430 / 0.1152e4 - t421 / t208 / t588 * t322 * t43 * t67 * t593 / t167 / t595 / t200 / 0.36864e5 + 0.19e2 / 0.6912e4 * t421 * t425 * t199 / t166 / t200 / t388
  t611 = f.my_piecewise3(t155, 0, t610)
  d22 = 0.2e1 * t377 + 0.2e1 * t434 + t6 * (t512 + t611)
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
  t49 = r0 ** 2
  t51 = 0.1e1 / t45 / t49
  t54 = tau0 / t45 / r0 - s0 * t51 / 0.8e1
  t55 = 6 ** (0.1e1 / 0.3e1)
  t57 = jnp.pi ** 2
  t58 = t57 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t60 = 0.1e1 / t59
  t64 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t54 * t55 * t60)
  t65 = t54 ** 2
  t67 = t55 ** 2
  t69 = 0.1e1 / t58 / t57
  t70 = t67 * t69
  t73 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t65 * t70
  t74 = t73 ** 2
  t75 = t65 ** 2
  t77 = t57 ** 2
  t79 = 0.1e1 / t59 / t77
  t80 = t55 * t79
  t83 = t74 + 0.1250e4 / 0.2187e4 * params.c1 * t75 * t80
  t84 = t83 ** (0.1e1 / 0.4e1)
  t85 = 0.1e1 / t84
  t87 = t64 * t85 + 0.1e1
  t89 = params.b * t67
  t90 = s0 ** 2
  t91 = t69 * t90
  t92 = t49 ** 2
  t93 = t92 * r0
  t99 = 0.1e1 + t89 * t91 / t44 / t93 / 0.576e3
  t100 = t99 ** (0.1e1 / 0.8e1)
  t101 = 0.1e1 / t100
  t102 = t43 * t87 * t101
  t107 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t108 = t5 * t107
  t109 = t43 ** 2
  t110 = 0.1e1 / t109
  t112 = t110 * t87 * t101
  t117 = t49 * r0
  t119 = 0.1e1 / t45 / t117
  t122 = -0.5e1 / 0.3e1 * tau0 * t51 + s0 * t119 / 0.3e1
  t123 = params.k0 * t122
  t125 = t55 * t60 * t85
  t129 = 0.1e1 / t84 / t83
  t130 = t73 * params.e1
  t131 = t130 * t54
  t136 = params.c1 * t65 * t54
  t140 = 0.100e3 / 0.81e2 * t131 * t70 * t122 + 0.5000e4 / 0.2187e4 * t136 * t80 * t122
  t144 = -0.5e1 / 0.9e1 * t123 * t125 - t64 * t129 * t140 / 0.4e1
  t146 = t43 * t144 * t101
  t149 = t107 * t43
  t151 = t5 * t149 * t87
  t155 = 0.1e1 / t100 / t99 * params.b * t67
  t160 = t155 * t91 / t44 / t92 / t49
  t163 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t164 = t163 * f.p.zeta_threshold
  t166 = f.my_piecewise3(t20, t164, t21 * t19)
  t167 = t5 * t166
  t169 = 0.1e1 / t109 / t6
  t171 = t169 * t87 * t101
  t175 = t110 * t144 * t101
  t178 = t166 * t110
  t180 = t5 * t178 * t87
  t186 = 0.1e1 / t45 / t92
  t189 = 0.40e2 / 0.9e1 * tau0 * t119 - 0.11e2 / 0.9e1 * s0 * t186
  t190 = params.k0 * t189
  t193 = t123 * t55
  t194 = t60 * t129
  t195 = t194 * t140
  t198 = t83 ** 2
  t200 = 0.1e1 / t84 / t198
  t201 = t140 ** 2
  t205 = params.e1 ** 2
  t206 = t205 * t65
  t207 = t122 ** 2
  t208 = t80 * t207
  t215 = t70 * t189
  t218 = params.c1 * t65
  t224 = 0.10000e5 / 0.2187e4 * t206 * t208 + 0.100e3 / 0.81e2 * t130 * t207 * t67 * t69 + 0.100e3 / 0.81e2 * t131 * t215 + 0.5000e4 / 0.729e3 * t218 * t208 + 0.5000e4 / 0.2187e4 * t136 * t80 * t189
  t228 = -0.5e1 / 0.9e1 * t190 * t125 + 0.5e1 / 0.18e2 * t193 * t195 + 0.5e1 / 0.16e2 * t64 * t200 * t201 - t64 * t129 * t224 / 0.4e1
  t230 = t43 * t228 * t101
  t233 = t166 * t43
  t235 = t5 * t233 * t144
  t239 = t5 * t233 * t87
  t240 = t99 ** 2
  t243 = params.b ** 2
  t245 = 0.1e1 / t100 / t240 * t243 * t55
  t246 = t90 ** 2
  t247 = t79 * t246
  t248 = t92 ** 2
  t253 = t245 * t247 / t45 / t248 / t92
  t260 = t155 * t91 / t44 / t92 / t117
  t263 = -0.3e1 / 0.8e1 * t42 * t102 - t108 * t112 / 0.4e1 - 0.3e1 / 0.4e1 * t108 * t146 - t151 * t160 / 0.1152e4 + t167 * t171 / 0.12e2 - t167 * t175 / 0.4e1 - t180 * t160 / 0.3456e4 - 0.3e1 / 0.8e1 * t167 * t230 - t235 * t160 / 0.1152e4 - t239 * t253 / 0.36864e5 + 0.19e2 / 0.6912e4 * t239 * t260
  t264 = f.my_piecewise3(t1, 0, t263)
  t266 = r1 <= f.p.dens_threshold
  t267 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t268 = 0.1e1 + t267
  t269 = t268 <= f.p.zeta_threshold
  t270 = t268 ** (0.1e1 / 0.3e1)
  t271 = t270 ** 2
  t272 = 0.1e1 / t271
  t274 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t275 = t274 ** 2
  t279 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t283 = f.my_piecewise3(t269, 0, 0.4e1 / 0.9e1 * t272 * t275 + 0.4e1 / 0.3e1 * t270 * t279)
  t284 = t5 * t283
  t285 = r1 ** (0.1e1 / 0.3e1)
  t286 = t285 ** 2
  t290 = r1 ** 2
  t295 = tau1 / t286 / r1 - s2 / t286 / t290 / 0.8e1
  t301 = t295 ** 2
  t306 = (0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t301 * t70) ** 2
  t307 = t301 ** 2
  t312 = (t306 + 0.1250e4 / 0.2187e4 * params.c1 * t307 * t80) ** (0.1e1 / 0.4e1)
  t315 = 0.1e1 + params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t295 * t55 * t60) / t312
  t317 = s2 ** 2
  t319 = t290 ** 2
  t327 = (0.1e1 + t89 * t69 * t317 / t285 / t319 / r1 / 0.576e3) ** (0.1e1 / 0.8e1)
  t328 = 0.1e1 / t327
  t329 = t43 * t315 * t328
  t334 = f.my_piecewise3(t269, 0, 0.4e1 / 0.3e1 * t270 * t274)
  t335 = t5 * t334
  t337 = t110 * t315 * t328
  t341 = f.my_piecewise3(t269, t164, t270 * t268)
  t342 = t5 * t341
  t344 = t169 * t315 * t328
  t348 = f.my_piecewise3(t266, 0, -0.3e1 / 0.8e1 * t284 * t329 - t335 * t337 / 0.4e1 + t342 * t344 / 0.12e2)
  t356 = -0.440e3 / 0.27e2 * tau0 * t186 + 0.154e3 / 0.27e2 * s0 / t45 / t93
  t383 = t80 * t207 * t122
  t388 = t79 * t122 * t189
  t451 = -0.3e1 / 0.8e1 * t167 * t43 * (-0.5e1 / 0.9e1 * params.k0 * t356 * t125 + 0.5e1 / 0.12e2 * t190 * t55 * t195 - 0.25e2 / 0.48e2 * t193 * t60 * t200 * t201 + 0.5e1 / 0.12e2 * t193 * t194 * t224 - 0.45e2 / 0.64e2 * t64 / t84 / t198 / t83 * t201 * t140 + 0.15e2 / 0.16e2 * t64 * t200 * t140 * t224 - t64 * t129 * (0.10000e5 / 0.729e3 * t205 * t54 * t383 + 0.10000e5 / 0.729e3 * t206 * t55 * t388 + 0.100e3 / 0.27e2 * t130 * t122 * t215 + 0.100e3 / 0.81e2 * t131 * t70 * t356 + 0.10000e5 / 0.729e3 * params.c1 * t54 * t383 + 0.5000e4 / 0.243e3 * t218 * t55 * t388 + 0.5000e4 / 0.2187e4 * t136 * t80 * t356) / 0.4e1) * t101 - 0.9e1 / 0.8e1 * t42 * t146 - 0.3e1 / 0.4e1 * t108 * t175 - 0.9e1 / 0.8e1 * t108 * t230 + t167 * t169 * t144 * t101 / 0.4e1 - 0.3e1 / 0.8e1 * t167 * t110 * t228 * t101 + 0.19e2 / 0.36864e5 * t239 * t245 * t247 / t45 / t248 / t93 + 0.19e2 / 0.2304e4 * t151 * t260 + 0.19e2 / 0.6912e4 * t180 * t260 - t5 * t233 * t228 * t160 / 0.768e3 - t235 * t253 / 0.12288e5 - t5 * t41 * t43 * t87 * t160 / 0.768e3
  t487 = 0.1e1 / t109 / t24
  t500 = t24 ** 2
  t504 = 0.6e1 * t33 - 0.6e1 * t16 / t500
  t505 = f.my_piecewise5(t10, 0, t14, 0, t504)
  t509 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t505)
  t513 = t77 ** 2
  t525 = t248 ** 2
  t532 = -t5 * t107 * t110 * t87 * t160 / 0.1152e4 - t5 * t149 * t144 * t160 / 0.384e3 - t151 * t253 / 0.12288e5 + t5 * t166 * t169 * t87 * t160 / 0.3456e4 - t5 * t178 * t144 * t160 / 0.1152e4 - t180 * t253 / 0.36864e5 - 0.209e3 / 0.10368e5 * t239 * t155 * t91 / t44 / t248 + 0.19e2 / 0.2304e4 * t235 * t260 - 0.3e1 / 0.8e1 * t42 * t112 + t108 * t171 / 0.4e1 - 0.5e1 / 0.36e2 * t167 * t487 * t87 * t101 - 0.3e1 / 0.8e1 * t5 * t509 * t102 - 0.17e2 / 0.5308416e7 * t2 / t3 / t513 * t233 * t87 / t100 / t240 / t99 * t243 * params.b * t246 * t90 / t525 / t117
  t534 = f.my_piecewise3(t1, 0, t451 + t532)
  t544 = f.my_piecewise5(t14, 0, t10, 0, -t504)
  t548 = f.my_piecewise3(t269, 0, -0.8e1 / 0.27e2 / t271 / t268 * t275 * t274 + 0.4e1 / 0.3e1 * t272 * t274 * t279 + 0.4e1 / 0.3e1 * t270 * t544)
  t561 = f.my_piecewise3(t266, 0, -0.3e1 / 0.8e1 * t5 * t548 * t329 - 0.3e1 / 0.8e1 * t284 * t337 + t335 * t344 / 0.4e1 - 0.5e1 / 0.36e2 * t342 * t487 * t315 * t328)
  d111 = 0.3e1 * t264 + 0.3e1 * t348 + t6 * (t534 + t561)

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
  t30 = t6 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = 0.1e1 / t31
  t33 = t29 * t32
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t39 = r0 ** 2
  t41 = 0.1e1 / t35 / t39
  t44 = tau0 / t35 / r0 - s0 * t41 / 0.8e1
  t45 = 6 ** (0.1e1 / 0.3e1)
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t54 = params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t44 * t45 * t50)
  t55 = t44 ** 2
  t57 = t45 ** 2
  t59 = 0.1e1 / t48 / t47
  t60 = t57 * t59
  t63 = 0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t55 * t60
  t64 = t63 ** 2
  t65 = t55 ** 2
  t67 = t47 ** 2
  t69 = 0.1e1 / t49 / t67
  t70 = t45 * t69
  t73 = t64 + 0.1250e4 / 0.2187e4 * params.c1 * t65 * t70
  t74 = t73 ** (0.1e1 / 0.4e1)
  t75 = 0.1e1 / t74
  t77 = t54 * t75 + 0.1e1
  t79 = t5 * t33 * t77
  t80 = params.b * t57
  t81 = s0 ** 2
  t82 = t59 * t81
  t83 = t39 ** 2
  t84 = t83 * r0
  t90 = 0.1e1 + t80 * t82 / t34 / t84 / 0.576e3
  t91 = t90 ** (0.1e1 / 0.8e1)
  t95 = 0.1e1 / t91 / t90 * params.b * t57
  t96 = t83 * t39
  t100 = t95 * t82 / t34 / t96
  t103 = t29 * t30
  t106 = t39 * r0
  t108 = 0.1e1 / t35 / t106
  t111 = -0.5e1 / 0.3e1 * tau0 * t41 + s0 * t108 / 0.3e1
  t112 = params.k0 * t111
  t114 = t45 * t50 * t75
  t118 = 0.1e1 / t74 / t73
  t119 = t63 * params.e1
  t120 = t119 * t44
  t125 = params.c1 * t55 * t44
  t129 = 0.100e3 / 0.81e2 * t120 * t60 * t111 + 0.5000e4 / 0.2187e4 * t125 * t70 * t111
  t133 = -0.5e1 / 0.9e1 * t112 * t114 - t54 * t118 * t129 / 0.4e1
  t135 = t5 * t103 * t133
  t139 = t5 * t103 * t77
  t140 = t90 ** 2
  t143 = params.b ** 2
  t145 = 0.1e1 / t91 / t140 * t143 * t45
  t146 = t81 ** 2
  t147 = t69 * t146
  t148 = t83 ** 2
  t153 = t145 * t147 / t35 / t148 / t83
  t156 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t157 = t156 * f.p.zeta_threshold
  t159 = f.my_piecewise3(t20, t157, t21 * t19)
  t161 = 0.1e1 / t31 / t6
  t162 = t159 * t161
  t164 = t5 * t162 * t77
  t167 = t159 * t32
  t169 = t5 * t167 * t133
  t173 = t5 * t167 * t77
  t176 = t159 * t30
  t177 = t176 * t77
  t178 = t5 * t177
  t182 = t95 * t82 / t34 / t148
  t186 = t5 * t176 * t133
  t191 = t95 * t82 / t34 / t83 / t106
  t198 = t145 * t147 / t35 / t148 / t84
  t208 = 0.1e1 / t35 / t83
  t211 = 0.40e2 / 0.9e1 * tau0 * t108 - 0.11e2 / 0.9e1 * s0 * t208
  t212 = params.k0 * t211
  t215 = t112 * t45
  t216 = t50 * t118
  t217 = t216 * t129
  t220 = t73 ** 2
  t222 = 0.1e1 / t74 / t220
  t223 = t129 ** 2
  t227 = params.e1 ** 2
  t228 = t227 * t55
  t229 = t111 ** 2
  t230 = t70 * t229
  t237 = t60 * t211
  t240 = params.c1 * t55
  t246 = 0.10000e5 / 0.2187e4 * t228 * t230 + 0.100e3 / 0.81e2 * t119 * t229 * t57 * t59 + 0.100e3 / 0.81e2 * t120 * t237 + 0.5000e4 / 0.729e3 * t240 * t230 + 0.5000e4 / 0.2187e4 * t125 * t70 * t211
  t250 = -0.5e1 / 0.9e1 * t212 * t114 + 0.5e1 / 0.18e2 * t215 * t217 + 0.5e1 / 0.16e2 * t54 * t222 * t223 - t54 * t118 * t246 / 0.4e1
  t252 = t5 * t176 * t250
  t255 = -t79 * t100 / 0.1152e4 - t135 * t100 / 0.384e3 - t139 * t153 / 0.12288e5 + t164 * t100 / 0.3456e4 - t169 * t100 / 0.1152e4 - t173 * t153 / 0.36864e5 - 0.209e3 / 0.10368e5 * t178 * t182 + 0.19e2 / 0.2304e4 * t186 * t191 + 0.19e2 / 0.36864e5 * t178 * t198 + 0.19e2 / 0.2304e4 * t139 * t191 + 0.19e2 / 0.6912e4 * t173 * t191 - t252 * t100 / 0.768e3
  t258 = t21 ** 2
  t259 = 0.1e1 / t258
  t260 = t26 ** 2
  t263 = t22 * t6
  t264 = 0.1e1 / t263
  t267 = 0.2e1 * t16 * t264 - 0.2e1 * t23
  t268 = f.my_piecewise5(t10, 0, t14, 0, t267)
  t272 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t259 * t260 + 0.4e1 / 0.3e1 * t21 * t268)
  t273 = t272 * t30
  t275 = t5 * t273 * t77
  t278 = t5 * t272
  t280 = 0.1e1 / t91
  t281 = t32 * t77 * t280
  t284 = t5 * t29
  t286 = t161 * t77 * t280
  t289 = t5 * t159
  t291 = 0.1e1 / t31 / t22
  t293 = t291 * t77 * t280
  t297 = 0.1e1 / t258 / t19
  t301 = t259 * t26
  t304 = t22 ** 2
  t305 = 0.1e1 / t304
  t308 = -0.6e1 * t16 * t305 + 0.6e1 * t264
  t309 = f.my_piecewise5(t10, 0, t14, 0, t308)
  t313 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t297 * t260 * t26 + 0.4e1 / 0.3e1 * t301 * t268 + 0.4e1 / 0.3e1 * t21 * t309)
  t314 = t5 * t313
  t316 = t30 * t77 * t280
  t320 = t30 * t133 * t280
  t324 = t32 * t133 * t280
  t328 = t30 * t250 * t280
  t332 = t161 * t133 * t280
  t336 = t32 * t250 * t280
  t342 = 0.1e1 / t35 / t84
  t345 = -0.440e3 / 0.27e2 * tau0 * t208 + 0.154e3 / 0.27e2 * s0 * t342
  t346 = params.k0 * t345
  t349 = t212 * t45
  t352 = t50 * t222
  t353 = t352 * t223
  t356 = t216 * t246
  t361 = 0.1e1 / t74 / t220 / t73
  t362 = t223 * t129
  t366 = t222 * t129
  t370 = t227 * t44
  t372 = t70 * t229 * t111
  t375 = t228 * t45
  t376 = t69 * t111
  t377 = t376 * t211
  t380 = t119 * t111
  t383 = t60 * t345
  t386 = params.c1 * t44
  t389 = t240 * t45
  t395 = 0.10000e5 / 0.729e3 * t370 * t372 + 0.10000e5 / 0.729e3 * t375 * t377 + 0.100e3 / 0.27e2 * t380 * t237 + 0.100e3 / 0.81e2 * t120 * t383 + 0.10000e5 / 0.729e3 * t386 * t372 + 0.5000e4 / 0.243e3 * t389 * t377 + 0.5000e4 / 0.2187e4 * t125 * t70 * t345
  t399 = -0.5e1 / 0.9e1 * t346 * t114 + 0.5e1 / 0.12e2 * t349 * t217 - 0.25e2 / 0.48e2 * t215 * t353 + 0.5e1 / 0.12e2 * t215 * t356 - 0.45e2 / 0.64e2 * t54 * t361 * t362 + 0.15e2 / 0.16e2 * t54 * t366 * t246 - t54 * t118 * t395 / 0.4e1
  t401 = t30 * t399 * t280
  t404 = t67 ** 2
  t407 = t2 / t3 / t404
  t408 = t407 * t176
  t411 = 0.1e1 / t91 / t140 / t90
  t412 = t77 * t411
  t415 = t143 * params.b * t146 * t81
  t416 = t148 ** 2
  t419 = t415 / t416 / t106
  t420 = t412 * t419
  t423 = -t186 * t153 / 0.12288e5 - t275 * t100 / 0.768e3 - 0.3e1 / 0.8e1 * t278 * t281 + t284 * t286 / 0.4e1 - 0.5e1 / 0.36e2 * t289 * t293 - 0.3e1 / 0.8e1 * t314 * t316 - 0.9e1 / 0.8e1 * t278 * t320 - 0.3e1 / 0.4e1 * t284 * t324 - 0.9e1 / 0.8e1 * t284 * t328 + t289 * t332 / 0.4e1 - 0.3e1 / 0.8e1 * t289 * t336 - 0.3e1 / 0.8e1 * t289 * t401 - 0.17e2 / 0.5308416e7 * t408 * t420
  t425 = f.my_piecewise3(t1, 0, t255 + t423)
  t427 = r1 <= f.p.dens_threshold
  t428 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t429 = 0.1e1 + t428
  t430 = t429 <= f.p.zeta_threshold
  t431 = t429 ** (0.1e1 / 0.3e1)
  t432 = t431 ** 2
  t434 = 0.1e1 / t432 / t429
  t436 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t437 = t436 ** 2
  t441 = 0.1e1 / t432
  t442 = t441 * t436
  t444 = f.my_piecewise5(t14, 0, t10, 0, -t267)
  t448 = f.my_piecewise5(t14, 0, t10, 0, -t308)
  t452 = f.my_piecewise3(t430, 0, -0.8e1 / 0.27e2 * t434 * t437 * t436 + 0.4e1 / 0.3e1 * t442 * t444 + 0.4e1 / 0.3e1 * t431 * t448)
  t453 = t5 * t452
  t454 = r1 ** (0.1e1 / 0.3e1)
  t455 = t454 ** 2
  t459 = r1 ** 2
  t464 = tau1 / t455 / r1 - s2 / t455 / t459 / 0.8e1
  t470 = t464 ** 2
  t475 = (0.1e1 + 0.25e2 / 0.81e2 * params.e1 * t470 * t60) ** 2
  t476 = t470 ** 2
  t481 = (t475 + 0.1250e4 / 0.2187e4 * params.c1 * t476 * t70) ** (0.1e1 / 0.4e1)
  t484 = 0.1e1 + params.k0 * (0.1e1 - 0.5e1 / 0.9e1 * t464 * t45 * t50) / t481
  t486 = s2 ** 2
  t488 = t459 ** 2
  t496 = (0.1e1 + t80 * t59 * t486 / t454 / t488 / r1 / 0.576e3) ** (0.1e1 / 0.8e1)
  t497 = 0.1e1 / t496
  t498 = t30 * t484 * t497
  t506 = f.my_piecewise3(t430, 0, 0.4e1 / 0.9e1 * t441 * t437 + 0.4e1 / 0.3e1 * t431 * t444)
  t507 = t5 * t506
  t509 = t32 * t484 * t497
  t514 = f.my_piecewise3(t430, 0, 0.4e1 / 0.3e1 * t431 * t436)
  t515 = t5 * t514
  t517 = t161 * t484 * t497
  t521 = f.my_piecewise3(t430, t157, t431 * t429)
  t522 = t5 * t521
  t524 = t291 * t484 * t497
  t528 = f.my_piecewise3(t427, 0, -0.3e1 / 0.8e1 * t453 * t498 - 0.3e1 / 0.8e1 * t507 * t509 + t515 * t517 / 0.4e1 - 0.5e1 / 0.36e2 * t522 * t524)
  t532 = t148 * r0
  t562 = t140 ** 2
  t565 = t143 ** 2
  t567 = t146 ** 2
  t586 = -t135 * t153 / 0.3072e4 + 0.5225e4 / 0.31104e5 * t178 * t95 * t82 / t34 / t532 - 0.5e1 / 0.7776e4 * t5 * t159 * t291 * t77 * t100 - 0.19e2 / 0.5184e4 * t164 * t191 - 0.209e3 / 0.7776e4 * t173 * t182 - t5 * t167 * t250 * t100 / 0.576e3 + 0.19e2 / 0.27648e5 * t173 * t198 - 0.2755e4 / 0.331776e6 * t178 * t145 * t147 / t35 / t148 / t96 - 0.425e3 / 0.4586471424e10 * t407 * t177 / t91 / t562 * t565 * t567 / t34 / t416 / t532 * t57 * t59 + t164 * t153 / 0.27648e5 - 0.209e3 / 0.2592e4 * t186 * t182 - t5 * t313 * t30 * t77 * t100 / 0.576e3
  t623 = -t5 * t273 * t133 * t100 / 0.192e3 - t275 * t153 / 0.6144e4 - t5 * t33 * t133 * t100 / 0.288e3 - t79 * t153 / 0.9216e4 + t5 * t162 * t133 * t100 / 0.864e3 + 0.19e2 / 0.9216e4 * t139 * t198 + 0.19e2 / 0.9216e4 * t186 * t198 + 0.19e2 / 0.1152e4 * t275 * t191 + 0.19e2 / 0.576e3 * t135 * t191 + 0.19e2 / 0.1728e4 * t169 * t191 - t5 * t103 * t250 * t100 / 0.192e3 - t5 * t176 * t399 * t100 / 0.576e3 - t252 * t153 / 0.6144e4
  t656 = 0.1e1 / t31 / t263
  t661 = t5 * t29 * t161 * t77 * t100 / 0.864e3 + 0.19e2 / 0.1152e4 * t252 * t191 - t169 * t153 / 0.9216e4 - t5 * t272 * t32 * t77 * t100 / 0.576e3 + 0.19e2 / 0.1728e4 * t79 * t191 - 0.209e3 / 0.2592e4 * t139 * t182 + t289 * t161 * t250 * t280 / 0.2e1 - t314 * t281 / 0.2e1 - 0.3e1 / 0.2e1 * t278 * t324 + t278 * t286 / 0.2e1 - 0.5e1 / 0.9e1 * t284 * t293 + 0.10e2 / 0.27e2 * t289 * t656 * t77 * t280
  t674 = 0.6160e4 / 0.81e2 * tau0 * t342 - 0.2618e4 / 0.81e2 * s0 / t35 / t96
  t696 = t220 ** 2
  t699 = t223 ** 2
  t707 = t246 ** 2
  t714 = t229 ** 2
  t720 = t69 * t229 * t211
  t723 = t211 ** 2
  t724 = t70 * t723
  t727 = t376 * t345
  t752 = 0.10000e5 / 0.729e3 * t227 * t714 * t70 + 0.20000e5 / 0.243e3 * t370 * t45 * t720 + 0.10000e5 / 0.729e3 * t228 * t724 + 0.40000e5 / 0.2187e4 * t375 * t727 + 0.100e3 / 0.27e2 * t119 * t723 * t57 * t59 + 0.400e3 / 0.81e2 * t380 * t383 + 0.100e3 / 0.81e2 * t120 * t60 * t674 + 0.10000e5 / 0.729e3 * params.c1 * t714 * t70 + 0.20000e5 / 0.243e3 * t386 * t45 * t720 + 0.5000e4 / 0.243e3 * t240 * t724 + 0.20000e5 / 0.729e3 * t389 * t727 + 0.5000e4 / 0.2187e4 * t125 * t70 * t674
  t756 = -0.5e1 / 0.9e1 * params.k0 * t674 * t114 + 0.5e1 / 0.9e1 * t346 * t45 * t217 - 0.25e2 / 0.24e2 * t349 * t353 + 0.5e1 / 0.6e1 * t349 * t356 + 0.25e2 / 0.16e2 * t215 * t50 * t361 * t362 - 0.25e2 / 0.12e2 * t215 * t352 * t129 * t246 + 0.5e1 / 0.9e1 * t215 * t216 * t395 + 0.585e3 / 0.256e3 * t54 / t74 / t696 * t699 - 0.135e3 / 0.32e2 * t54 * t361 * t223 * t246 + 0.15e2 / 0.16e2 * t54 * t222 * t707 + 0.5e1 / 0.4e1 * t54 * t366 * t395 - t54 * t118 * t752 / 0.4e1
  t766 = t19 ** 2
  t769 = t260 ** 2
  t775 = t268 ** 2
  t784 = -0.24e2 * t305 + 0.24e2 * t16 / t304 / t6
  t785 = f.my_piecewise5(t10, 0, t14, 0, t784)
  t789 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t258 / t766 * t769 - 0.16e2 / 0.9e1 * t297 * t260 * t268 + 0.4e1 / 0.3e1 * t259 * t775 + 0.16e2 / 0.9e1 * t301 * t309 + 0.4e1 / 0.3e1 * t21 * t785)
  t815 = -t289 * t32 * t399 * t280 / 0.2e1 - 0.3e1 / 0.2e1 * t284 * t401 - 0.3e1 / 0.8e1 * t289 * t30 * t756 * t280 + t284 * t332 - 0.5e1 / 0.9e1 * t289 * t291 * t133 * t280 - 0.3e1 / 0.8e1 * t5 * t789 * t316 - 0.3e1 / 0.2e1 * t314 * t320 - 0.9e1 / 0.4e1 * t278 * t328 - 0.3e1 / 0.2e1 * t284 * t336 + 0.323e3 / 0.2654208e7 * t408 * t412 * t415 / t416 / t83 - 0.17e2 / 0.1327104e7 * t408 * t133 * t411 * t419 - 0.17e2 / 0.1327104e7 * t407 * t103 * t420 - 0.17e2 / 0.3981312e7 * t407 * t167 * t420
  t818 = f.my_piecewise3(t1, 0, t586 + t623 + t661 + t815)
  t819 = t429 ** 2
  t822 = t437 ** 2
  t828 = t444 ** 2
  t834 = f.my_piecewise5(t14, 0, t10, 0, -t784)
  t838 = f.my_piecewise3(t430, 0, 0.40e2 / 0.81e2 / t432 / t819 * t822 - 0.16e2 / 0.9e1 * t434 * t437 * t444 + 0.4e1 / 0.3e1 * t441 * t828 + 0.16e2 / 0.9e1 * t442 * t448 + 0.4e1 / 0.3e1 * t431 * t834)
  t853 = f.my_piecewise3(t427, 0, -0.3e1 / 0.8e1 * t5 * t838 * t498 - t453 * t509 / 0.2e1 + t507 * t517 / 0.2e1 - 0.5e1 / 0.9e1 * t515 * t524 + 0.10e2 / 0.27e2 * t522 * t656 * t484 * t497)
  d1111 = 0.4e1 * t425 + 0.4e1 * t528 + t6 * (t818 + t853)

  res = {'v4rho4': d1111}
  return res
