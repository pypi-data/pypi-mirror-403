"""Generated from mgga_x_msb.mpl."""

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

  ms_f0 = lambda p, c: 1 + params_kappa * (1 - params_kappa / (params_kappa + MU_GE * p + c))

  ms_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  msb_fa = lambda b: (1 - (2 * b) ** 2) ** 3 / (1 + (2 * b) ** 3 + params_b * (2 * b) ** 6)

  msb_beta = lambda t, x: ms_alpha(t, x) * K_FACTOR_C / (t + K_FACTOR_C)

  msb_f = lambda x, u, t: ms_f0(X2S ** 2 * x ** 2, 0) + msb_fa(msb_beta(t, x)) * (ms_f0(X2S ** 2 * x ** 2, params_c) - ms_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msb_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  ms_f0 = lambda p, c: 1 + params_kappa * (1 - params_kappa / (params_kappa + MU_GE * p + c))

  ms_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  msb_fa = lambda b: (1 - (2 * b) ** 2) ** 3 / (1 + (2 * b) ** 3 + params_b * (2 * b) ** 6)

  msb_beta = lambda t, x: ms_alpha(t, x) * K_FACTOR_C / (t + K_FACTOR_C)

  msb_f = lambda x, u, t: ms_f0(X2S ** 2 * x ** 2, 0) + msb_fa(msb_beta(t, x)) * (ms_f0(X2S ** 2 * x ** 2, params_c) - ms_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msb_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  ms_f0 = lambda p, c: 1 + params_kappa * (1 - params_kappa / (params_kappa + MU_GE * p + c))

  ms_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  msb_fa = lambda b: (1 - (2 * b) ** 2) ** 3 / (1 + (2 * b) ** 3 + params_b * (2 * b) ** 6)

  msb_beta = lambda t, x: ms_alpha(t, x) * K_FACTOR_C / (t + K_FACTOR_C)

  msb_f = lambda x, u, t: ms_f0(X2S ** 2 * x ** 2, 0) + msb_fa(msb_beta(t, x)) * (ms_f0(X2S ** 2 * x ** 2, params_c) - ms_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msb_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t32 = 0.1e1 / t31
  t33 = t28 * t32
  t34 = r0 ** 2
  t35 = r0 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t38 = 0.1e1 / t36 / t34
  t39 = s0 * t38
  t41 = 0.5e1 / 0.972e3 * t33 * t39
  t42 = params.kappa + t41
  t46 = params.kappa * (0.1e1 - params.kappa / t42)
  t48 = 0.1e1 / t36 / r0
  t49 = tau0 * t48
  t51 = t49 - t39 / 0.8e1
  t52 = t51 ** 2
  t53 = t28 ** 2
  t55 = 0.3e1 / 0.10e2 * t53 * t31
  t56 = t49 + t55
  t57 = t56 ** 2
  t58 = 0.1e1 / t57
  t61 = -0.4e1 * t52 * t58 + 0.1e1
  t62 = t61 ** 2
  t63 = t62 * t61
  t64 = t52 * t51
  t65 = t57 * t56
  t66 = 0.1e1 / t65
  t69 = t52 ** 2
  t71 = params.b * t69 * t52
  t72 = t57 ** 2
  t74 = 0.1e1 / t72 / t57
  t77 = 0.8e1 * t64 * t66 + 0.64e2 * t71 * t74 + 0.1e1
  t78 = 0.1e1 / t77
  t79 = t63 * t78
  t80 = params.kappa + t41 + params.c
  t85 = params.kappa * (0.1e1 - params.kappa / t80) - t46
  t87 = t79 * t85 + t46 + 0.1e1
  t91 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t87)
  t92 = r1 <= f.p.dens_threshold
  t93 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t94 = 0.1e1 + t93
  t95 = t94 <= f.p.zeta_threshold
  t96 = t94 ** (0.1e1 / 0.3e1)
  t98 = f.my_piecewise3(t95, t22, t96 * t94)
  t99 = t98 * t26
  t100 = r1 ** 2
  t101 = r1 ** (0.1e1 / 0.3e1)
  t102 = t101 ** 2
  t104 = 0.1e1 / t102 / t100
  t105 = s2 * t104
  t107 = 0.5e1 / 0.972e3 * t33 * t105
  t108 = params.kappa + t107
  t112 = params.kappa * (0.1e1 - params.kappa / t108)
  t114 = 0.1e1 / t102 / r1
  t115 = tau1 * t114
  t117 = t115 - t105 / 0.8e1
  t118 = t117 ** 2
  t119 = t115 + t55
  t120 = t119 ** 2
  t121 = 0.1e1 / t120
  t124 = -0.4e1 * t118 * t121 + 0.1e1
  t125 = t124 ** 2
  t126 = t125 * t124
  t127 = t118 * t117
  t128 = t120 * t119
  t129 = 0.1e1 / t128
  t132 = t118 ** 2
  t134 = params.b * t132 * t118
  t135 = t120 ** 2
  t137 = 0.1e1 / t135 / t120
  t140 = 0.8e1 * t127 * t129 + 0.64e2 * t134 * t137 + 0.1e1
  t141 = 0.1e1 / t140
  t142 = t126 * t141
  t143 = params.kappa + t107 + params.c
  t148 = params.kappa * (0.1e1 - params.kappa / t143) - t112
  t150 = t142 * t148 + t112 + 0.1e1
  t154 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t99 * t150)
  t155 = t6 ** 2
  t157 = t16 / t155
  t158 = t7 - t157
  t159 = f.my_piecewise5(t10, 0, t14, 0, t158)
  t162 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t159)
  t167 = t26 ** 2
  t168 = 0.1e1 / t167
  t172 = t5 * t25 * t168 * t87 / 0.8e1
  t173 = params.kappa ** 2
  t174 = t42 ** 2
  t176 = t173 / t174
  t181 = 0.1e1 / t36 / t34 / r0
  t182 = t32 * s0 * t181
  t183 = t176 * t28 * t182
  t185 = t62 * t78
  t186 = t51 * t58
  t187 = tau0 * t38
  t191 = -0.5e1 / 0.3e1 * t187 + s0 * t181 / 0.3e1
  t194 = t52 * t66
  t201 = t77 ** 2
  t203 = t63 / t201
  t207 = t64 / t72
  t211 = params.b * t69 * t51
  t216 = 0.1e1 / t72 / t65
  t224 = t80 ** 2
  t226 = t173 / t224
  t237 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t162 * t26 * t87 - t172 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.10e2 / 0.729e3 * t183 + 0.3e1 * t185 * t85 * (-0.8e1 * t186 * t191 - 0.40e2 / 0.3e1 * t194 * t187) - t203 * t85 * (0.640e3 * t71 * t216 * tau0 * t38 + 0.384e3 * t211 * t74 * t191 + 0.40e2 * t207 * t187 + 0.24e2 * t194 * t191) + t79 * (-0.10e2 / 0.729e3 * t226 * t28 * t182 + 0.10e2 / 0.729e3 * t183)))
  t239 = f.my_piecewise5(t14, 0, t10, 0, -t158)
  t242 = f.my_piecewise3(t95, 0, 0.4e1 / 0.3e1 * t96 * t239)
  t250 = t5 * t98 * t168 * t150 / 0.8e1
  t252 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t242 * t26 * t150 - t250)
  vrho_0_ = t91 + t154 + t6 * (t237 + t252)
  t255 = -t7 - t157
  t256 = f.my_piecewise5(t10, 0, t14, 0, t255)
  t259 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t256)
  t265 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t259 * t26 * t87 - t172)
  t267 = f.my_piecewise5(t14, 0, t10, 0, -t255)
  t270 = f.my_piecewise3(t95, 0, 0.4e1 / 0.3e1 * t96 * t267)
  t275 = t108 ** 2
  t277 = t173 / t275
  t282 = 0.1e1 / t102 / t100 / r1
  t283 = t32 * s2 * t282
  t284 = t277 * t28 * t283
  t286 = t125 * t141
  t287 = t117 * t121
  t288 = tau1 * t104
  t292 = -0.5e1 / 0.3e1 * t288 + s2 * t282 / 0.3e1
  t295 = t118 * t129
  t302 = t140 ** 2
  t304 = t126 / t302
  t308 = t127 / t135
  t312 = params.b * t132 * t117
  t317 = 0.1e1 / t135 / t128
  t325 = t143 ** 2
  t327 = t173 / t325
  t338 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t270 * t26 * t150 - t250 - 0.3e1 / 0.8e1 * t5 * t99 * (-0.10e2 / 0.729e3 * t284 + 0.3e1 * t286 * t148 * (-0.8e1 * t287 * t292 - 0.40e2 / 0.3e1 * t295 * t288) - t304 * t148 * (0.640e3 * t134 * t317 * tau1 * t104 + 0.384e3 * t312 * t137 * t292 + 0.40e2 * t308 * t288 + 0.24e2 * t295 * t292) + t142 * (-0.10e2 / 0.729e3 * t327 * t28 * t283 + 0.10e2 / 0.729e3 * t284)))
  vrho_1_ = t91 + t154 + t6 * (t265 + t338)
  t341 = t33 * t38
  t342 = t176 * t341
  t364 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.5e1 / 0.972e3 * t342 + 0.3e1 * t185 * t85 * t186 * t38 - t203 * t85 * (-0.48e2 * t211 * t74 * t38 - 0.3e1 * t194 * t38) + t79 * (0.5e1 / 0.972e3 * t226 * t341 - 0.5e1 / 0.972e3 * t342)))
  vsigma_0_ = t6 * t364
  vsigma_1_ = 0.0e0
  t365 = t33 * t104
  t366 = t277 * t365
  t388 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t99 * (0.5e1 / 0.972e3 * t366 + 0.3e1 * t286 * t148 * t287 * t104 - t304 * t148 * (-0.48e2 * t312 * t137 * t104 - 0.3e1 * t295 * t104) + t142 * (0.5e1 / 0.972e3 * t327 * t365 - 0.5e1 / 0.972e3 * t366)))
  vsigma_2_ = t6 * t388
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t390 = t194 * t48
  t412 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.3e1 * t185 * t85 * (-0.8e1 * t186 * t48 + 0.8e1 * t390) - t203 * t85 * (0.384e3 * t211 * t74 * t48 - 0.384e3 * t71 * t216 * t48 - 0.24e2 * t207 * t48 + 0.24e2 * t390)))
  vtau_0_ = t6 * t412
  t414 = t295 * t114
  t436 = f.my_piecewise3(t92, 0, -0.3e1 / 0.8e1 * t5 * t99 * (0.3e1 * t286 * t148 * (-0.8e1 * t287 * t114 + 0.8e1 * t414) - t304 * t148 * (-0.384e3 * t134 * t317 * t114 + 0.384e3 * t312 * t137 * t114 - 0.24e2 * t308 * t114 + 0.24e2 * t414)))
  vtau_1_ = t6 * t436
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

  ms_f0 = lambda p, c: 1 + params_kappa * (1 - params_kappa / (params_kappa + MU_GE * p + c))

  ms_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  msb_fa = lambda b: (1 - (2 * b) ** 2) ** 3 / (1 + (2 * b) ** 3 + params_b * (2 * b) ** 6)

  msb_beta = lambda t, x: ms_alpha(t, x) * K_FACTOR_C / (t + K_FACTOR_C)

  msb_f = lambda x, u, t: ms_f0(X2S ** 2 * x ** 2, 0) + msb_fa(msb_beta(t, x)) * (ms_f0(X2S ** 2 * x ** 2, params_c) - ms_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, msb_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t24 = 0.1e1 / t23
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = s0 * t27
  t29 = r0 ** 2
  t30 = t18 ** 2
  t32 = 0.1e1 / t30 / t29
  t33 = t28 * t32
  t35 = 0.5e1 / 0.972e3 * t20 * t24 * t33
  t36 = params.kappa + t35
  t40 = params.kappa * (0.1e1 - params.kappa / t36)
  t41 = tau0 * t27
  t43 = 0.1e1 / t30 / r0
  t44 = t41 * t43
  t46 = t44 - t33 / 0.8e1
  t47 = t46 ** 2
  t48 = t20 ** 2
  t51 = t44 + 0.3e1 / 0.10e2 * t48 * t23
  t52 = t51 ** 2
  t53 = 0.1e1 / t52
  t56 = -0.4e1 * t47 * t53 + 0.1e1
  t57 = t56 ** 2
  t58 = t57 * t56
  t59 = t47 * t46
  t60 = t52 * t51
  t61 = 0.1e1 / t60
  t64 = t47 ** 2
  t66 = params.b * t64 * t47
  t67 = t52 ** 2
  t69 = 0.1e1 / t67 / t52
  t72 = 0.8e1 * t59 * t61 + 0.64e2 * t66 * t69 + 0.1e1
  t73 = 0.1e1 / t72
  t74 = t58 * t73
  t75 = params.kappa + t35 + params.c
  t80 = params.kappa * (0.1e1 - params.kappa / t75) - t40
  t82 = t74 * t80 + t40 + 0.1e1
  t86 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t82)
  t92 = params.kappa ** 2
  t93 = t36 ** 2
  t96 = t92 / t93 * t20
  t100 = 0.1e1 / t30 / t29 / r0
  t102 = t24 * s0 * t27 * t100
  t103 = t96 * t102
  t105 = t57 * t73
  t106 = t46 * t53
  t107 = t41 * t32
  t111 = -0.5e1 / 0.3e1 * t107 + t28 * t100 / 0.3e1
  t114 = t47 * t61
  t121 = t72 ** 2
  t123 = t58 / t121
  t127 = t59 / t67
  t131 = params.b * t64 * t46
  t136 = 0.1e1 / t67 / t60
  t143 = t75 ** 2
  t146 = t92 / t143 * t20
  t156 = f.my_piecewise3(t2, 0, -t6 * t17 / t30 * t82 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.10e2 / 0.729e3 * t103 + 0.3e1 * t105 * t80 * (-0.8e1 * t106 * t111 - 0.40e2 / 0.3e1 * t114 * t107) - t123 * t80 * (0.640e3 * t66 * t136 * t107 + 0.384e3 * t131 * t69 * t111 + 0.40e2 * t127 * t107 + 0.24e2 * t114 * t111) + t74 * (-0.10e2 / 0.729e3 * t146 * t102 + 0.10e2 / 0.729e3 * t103)))
  vrho_0_ = 0.2e1 * r0 * t156 + 0.2e1 * t86
  t160 = t24 * t27 * t32
  t161 = t96 * t160
  t164 = t27 * t32
  t170 = t69 * t27
  t185 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.5e1 / 0.972e3 * t161 + 0.3e1 * t105 * t80 * t106 * t164 - t123 * t80 * (-0.48e2 * t131 * t170 * t32 - 0.3e1 * t114 * t164) + t74 * (0.5e1 / 0.972e3 * t146 * t160 - 0.5e1 / 0.972e3 * t161)))
  vsigma_0_ = 0.2e1 * r0 * t185
  vlapl_0_ = 0.0e0
  t187 = t27 * t43
  t189 = t114 * t187
  t212 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.3e1 * t105 * t80 * (-0.8e1 * t106 * t187 + 0.8e1 * t189) - t123 * t80 * (-0.384e3 * t66 * t136 * t27 * t43 + 0.384e3 * t131 * t170 * t43 - 0.24e2 * t127 * t187 + 0.24e2 * t189)))
  vtau_0_ = 0.2e1 * r0 * t212
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
  t26 = 0.1e1 / t25
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = s0 * t29
  t31 = r0 ** 2
  t33 = 0.1e1 / t19 / t31
  t34 = t30 * t33
  t36 = 0.5e1 / 0.972e3 * t22 * t26 * t34
  t37 = params.kappa + t36
  t41 = params.kappa * (0.1e1 - params.kappa / t37)
  t42 = tau0 * t29
  t44 = 0.1e1 / t19 / r0
  t45 = t42 * t44
  t47 = t45 - t34 / 0.8e1
  t48 = t47 ** 2
  t49 = t22 ** 2
  t52 = 0.3e1 / 0.10e2 * t49 * t25 + t45
  t53 = t52 ** 2
  t54 = 0.1e1 / t53
  t57 = -0.4e1 * t48 * t54 + 0.1e1
  t58 = t57 ** 2
  t59 = t58 * t57
  t60 = t48 * t47
  t61 = t53 * t52
  t62 = 0.1e1 / t61
  t65 = t48 ** 2
  t67 = params.b * t65 * t48
  t68 = t53 ** 2
  t70 = 0.1e1 / t68 / t53
  t73 = 0.8e1 * t60 * t62 + 0.64e2 * t67 * t70 + 0.1e1
  t74 = 0.1e1 / t73
  t75 = t59 * t74
  t76 = params.kappa + t36 + params.c
  t81 = params.kappa * (0.1e1 - params.kappa / t76) - t41
  t83 = t75 * t81 + t41 + 0.1e1
  t87 = t17 * t18
  t88 = params.kappa ** 2
  t89 = t37 ** 2
  t92 = t88 / t89 * t22
  t93 = t26 * s0
  t94 = t31 * r0
  t96 = 0.1e1 / t19 / t94
  t98 = t93 * t29 * t96
  t99 = t92 * t98
  t101 = t58 * t74
  t102 = t47 * t54
  t103 = t42 * t33
  t107 = -0.5e1 / 0.3e1 * t103 + t30 * t96 / 0.3e1
  t110 = t48 * t62
  t113 = -0.8e1 * t102 * t107 - 0.40e2 / 0.3e1 * t110 * t103
  t114 = t81 * t113
  t117 = t73 ** 2
  t118 = 0.1e1 / t117
  t119 = t59 * t118
  t122 = 0.1e1 / t68
  t123 = t60 * t122
  t127 = params.b * t65 * t47
  t132 = 0.1e1 / t68 / t61
  t133 = t67 * t132
  t136 = 0.384e3 * t127 * t70 * t107 + 0.40e2 * t123 * t103 + 0.640e3 * t133 * t103 + 0.24e2 * t110 * t107
  t139 = t76 ** 2
  t142 = t88 / t139 * t22
  t145 = -0.10e2 / 0.729e3 * t142 * t98 + 0.10e2 / 0.729e3 * t99
  t147 = -0.10e2 / 0.729e3 * t99 + 0.3e1 * t101 * t114 - t119 * t81 * t136 + t75 * t145
  t152 = f.my_piecewise3(t2, 0, -t6 * t21 * t83 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t87 * t147)
  t167 = s0 ** 2
  t169 = t31 ** 2
  t174 = 0.1e1 / t24 / t23 * t167 * t28 / t18 / t169 / t94
  t176 = 0.400e3 / 0.531441e6 * t88 / t89 / t37 * t49 * t174
  t178 = 0.1e1 / t19 / t169
  t180 = t93 * t29 * t178
  t182 = 0.110e3 / 0.2187e4 * t92 * t180
  t184 = t113 ** 2
  t195 = t107 ** 2
  t198 = t47 * t62
  t202 = t42 * t96
  t206 = 0.40e2 / 0.9e1 * t202 - 0.11e2 / 0.9e1 * t30 * t178
  t209 = t48 * t122
  t210 = tau0 ** 2
  t215 = t210 * t28 / t18 / t169 / r0
  t227 = t136 ** 2
  t261 = t68 ** 2
  t286 = f.my_piecewise3(t2, 0, t6 * t17 * t44 * t83 / 0.12e2 - t6 * t21 * t147 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t87 * (-t176 + t182 + 0.6e1 * t57 * t74 * t81 * t184 - 0.6e1 * t58 * t118 * t114 * t136 + 0.6e1 * t101 * t145 * t113 + 0.3e1 * t101 * t81 * (-0.8e1 * t195 * t54 - 0.160e3 / 0.3e1 * t198 * t107 * t103 - 0.8e1 * t102 * t206 - 0.400e3 / 0.3e1 * t209 * t215 + 0.320e3 / 0.9e1 * t110 * t202) + 0.2e1 * t59 / t117 / t73 * t81 * t227 - 0.2e1 * t119 * t145 * t136 - t119 * t81 * (0.48e2 * t198 * t195 + 0.240e3 * t209 * t107 * t103 + 0.24e2 * t110 * t206 + 0.1600e4 / 0.3e1 * t60 / t68 / t52 * t215 - 0.320e3 / 0.3e1 * t123 * t202 + 0.1920e4 * params.b * t65 * t70 * t195 + 0.7680e4 * t127 * t132 * t107 * tau0 * t29 * t33 + 0.384e3 * t127 * t70 * t206 + 0.44800e5 / 0.3e1 * t67 / t261 * t215 - 0.5120e4 / 0.3e1 * t133 * t202) + t75 * (-0.400e3 / 0.531441e6 * t88 / t139 / t76 * t49 * t174 + 0.110e3 / 0.2187e4 * t142 * t180 + t176 - t182)))
  v2rho2_0_ = 0.2e1 * r0 * t286 + 0.4e1 * t152
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
  t27 = 0.1e1 / t26
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t35 = t31 * t34
  t37 = 0.5e1 / 0.972e3 * t23 * t27 * t35
  t38 = params.kappa + t37
  t42 = params.kappa * (0.1e1 - params.kappa / t38)
  t43 = tau0 * t30
  t44 = t43 * t21
  t46 = t44 - t35 / 0.8e1
  t47 = t46 ** 2
  t48 = t23 ** 2
  t51 = 0.3e1 / 0.10e2 * t48 * t26 + t44
  t52 = t51 ** 2
  t53 = 0.1e1 / t52
  t56 = -0.4e1 * t47 * t53 + 0.1e1
  t57 = t56 ** 2
  t58 = t57 * t56
  t59 = t47 * t46
  t60 = t52 * t51
  t61 = 0.1e1 / t60
  t64 = t47 ** 2
  t66 = params.b * t64 * t47
  t67 = t52 ** 2
  t69 = 0.1e1 / t67 / t52
  t72 = 0.8e1 * t59 * t61 + 0.64e2 * t66 * t69 + 0.1e1
  t73 = 0.1e1 / t72
  t74 = t58 * t73
  t75 = params.kappa + t37 + params.c
  t80 = params.kappa * (0.1e1 - params.kappa / t75) - t42
  t82 = t74 * t80 + t42 + 0.1e1
  t87 = t17 / t19
  t88 = params.kappa ** 2
  t89 = t38 ** 2
  t92 = t88 / t89 * t23
  t93 = t27 * s0
  t94 = t32 * r0
  t96 = 0.1e1 / t19 / t94
  t97 = t30 * t96
  t98 = t93 * t97
  t99 = t92 * t98
  t101 = t57 * t73
  t102 = t46 * t53
  t103 = t43 * t34
  t107 = -0.5e1 / 0.3e1 * t103 + t31 * t96 / 0.3e1
  t110 = t47 * t61
  t113 = -0.8e1 * t102 * t107 - 0.40e2 / 0.3e1 * t110 * t103
  t114 = t80 * t113
  t117 = t72 ** 2
  t118 = 0.1e1 / t117
  t119 = t58 * t118
  t122 = 0.1e1 / t67
  t123 = t59 * t122
  t127 = params.b * t64 * t46
  t128 = t69 * t107
  t132 = 0.1e1 / t67 / t60
  t133 = t66 * t132
  t136 = 0.40e2 * t123 * t103 + 0.640e3 * t133 * t103 + 0.24e2 * t110 * t107 + 0.384e3 * t127 * t128
  t137 = t80 * t136
  t139 = t75 ** 2
  t142 = t88 / t139 * t23
  t145 = -0.10e2 / 0.729e3 * t142 * t98 + 0.10e2 / 0.729e3 * t99
  t147 = -0.10e2 / 0.729e3 * t99 + 0.3e1 * t101 * t114 - t119 * t137 + t74 * t145
  t151 = t17 * t18
  t155 = t88 / t89 / t38 * t48
  t158 = s0 ** 2
  t159 = 0.1e1 / t25 / t24 * t158
  t160 = t32 ** 2
  t165 = t159 * t29 / t18 / t160 / t94
  t167 = 0.400e3 / 0.531441e6 * t155 * t165
  t169 = 0.1e1 / t19 / t160
  t171 = t93 * t30 * t169
  t173 = 0.110e3 / 0.2187e4 * t92 * t171
  t174 = t56 * t73
  t175 = t113 ** 2
  t176 = t80 * t175
  t179 = t57 * t118
  t183 = t145 * t113
  t186 = t107 ** 2
  t189 = t46 * t61
  t190 = t189 * t107
  t193 = t43 * t96
  t197 = 0.40e2 / 0.9e1 * t193 - 0.11e2 / 0.9e1 * t31 * t169
  t200 = t47 * t122
  t201 = tau0 ** 2
  t202 = t201 * t29
  t203 = t160 * r0
  t205 = 0.1e1 / t18 / t203
  t206 = t202 * t205
  t211 = -0.8e1 * t186 * t53 - 0.160e3 / 0.3e1 * t190 * t103 - 0.8e1 * t102 * t197 - 0.400e3 / 0.3e1 * t200 * t206 + 0.320e3 / 0.9e1 * t110 * t193
  t212 = t80 * t211
  t216 = 0.1e1 / t117 / t72
  t217 = t58 * t216
  t218 = t136 ** 2
  t227 = t200 * t107
  t233 = 0.1e1 / t67 / t51
  t234 = t59 * t233
  t239 = params.b * t64
  t243 = t127 * t132
  t244 = t107 * tau0
  t245 = t30 * t34
  t252 = t67 ** 2
  t253 = 0.1e1 / t252
  t254 = t66 * t253
  t259 = 0.48e2 * t189 * t186 + 0.240e3 * t227 * t103 + 0.24e2 * t110 * t197 + 0.1600e4 / 0.3e1 * t234 * t206 - 0.320e3 / 0.3e1 * t123 * t193 + 0.1920e4 * t239 * t69 * t186 + 0.7680e4 * t243 * t244 * t245 + 0.384e3 * t127 * t69 * t197 + 0.44800e5 / 0.3e1 * t254 * t206 - 0.5120e4 / 0.3e1 * t133 * t193
  t265 = t88 / t139 / t75 * t48
  t270 = -0.400e3 / 0.531441e6 * t265 * t165 + 0.110e3 / 0.2187e4 * t142 * t171 + t167 - t173
  t272 = -0.6e1 * t179 * t114 * t136 - 0.2e1 * t119 * t145 * t136 - t119 * t80 * t259 + 0.2e1 * t217 * t80 * t218 + 0.6e1 * t101 * t183 + 0.3e1 * t101 * t212 + 0.6e1 * t174 * t176 + t74 * t270 - t167 + t173
  t277 = f.my_piecewise3(t2, 0, t6 * t22 * t82 / 0.12e2 - t6 * t87 * t147 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t151 * t272)
  t289 = t139 ** 2
  t292 = t24 ** 2
  t296 = t160 ** 2
  t299 = 0.1e1 / t292 * t158 * s0 / t296 / t94
  t305 = t159 * t29 / t18 / t296
  t309 = 0.1e1 / t19 / t203
  t311 = t93 * t30 * t309
  t314 = t89 ** 2
  t318 = 0.16000e5 / 0.43046721e8 * t88 / t314 * t299
  t320 = 0.4400e4 / 0.531441e6 * t155 * t305
  t322 = 0.1540e4 / 0.6561e4 * t92 * t311
  t331 = t117 ** 2
  t371 = t46 * t122
  t380 = t43 * t169
  t384 = -0.440e3 / 0.27e2 * t380 + 0.154e3 / 0.27e2 * t31 * t309
  t387 = t47 * t233
  t388 = t201 * tau0
  t389 = 0.1e1 / t296
  t390 = t388 * t389
  t396 = t202 / t18 / t160 / t32
  t414 = t186 * t107
  t478 = 0.48e2 * t414 * t61 + 0.24e2 * t110 * t384 + 0.57600e5 * t239 * t132 * t186 * tau0 * t245 + 0.11520e5 * t243 * t197 * tau0 * t245 + 0.268800e6 * t127 * t253 * t107 * t201 * t29 * t205 - 0.358400e6 / 0.3e1 * t254 * t396 + 0.56320e5 / 0.9e1 * t133 * t380 - 0.960e3 * t227 * t193 + 0.7680e4 * params.b * t59 * t69 * t414 + 0.5760e4 * t239 * t128 * t197 + 0.3584000e7 / 0.9e1 * t66 / t252 / t51 * t388 * t389 - 0.30720e5 * t243 * t244 * t97 + 0.144e3 * t189 * t107 * t197 + 0.80000e5 / 0.9e1 * t59 * t69 * t390 + 0.384e3 * t127 * t69 * t384 + 0.720e3 * t371 * t186 * t103 + 0.360e3 * t200 * t197 * t103 + 0.4800e4 * t387 * t107 * t206 - 0.12800e5 / 0.3e1 * t234 * t396 + 0.3520e4 / 0.9e1 * t123 * t380
  t485 = t320 + 0.6e1 * t175 * t113 * t73 * t80 + 0.18e2 * t174 * t145 * t175 + 0.9e1 * t101 * t270 * t113 + 0.9e1 * t101 * t145 * t211 + 0.3e1 * t101 * t80 * (-0.24e2 * t107 * t53 * t197 - 0.80e2 * t186 * t61 * t103 - 0.800e3 * t371 * t107 * t206 - 0.80e2 * t189 * t197 * t103 + 0.640e3 / 0.3e1 * t190 * t193 - 0.8e1 * t102 * t384 - 0.16000e5 / 0.9e1 * t387 * t390 + 0.3200e4 / 0.3e1 * t200 * t396 - 0.3520e4 / 0.27e2 * t110 * t380) + 0.6e1 * t217 * t145 * t218 - 0.3e1 * t119 * t270 * t136 - 0.3e1 * t119 * t145 * t259 - t119 * t80 * t478 + 0.18e2 * t57 * t216 * t114 * t218
  t491 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t34 * t82 + t6 * t22 * t147 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t87 * t272 - 0.3e1 / 0.8e1 * t6 * t151 * (t74 * (-0.16000e5 / 0.43046721e8 * t88 / t289 * t299 + 0.4400e4 / 0.531441e6 * t265 * t305 - 0.1540e4 / 0.6561e4 * t142 * t311 + t318 - t320 + t322) - 0.9e1 * t179 * t212 * t136 - 0.9e1 * t179 * t114 * t259 - 0.6e1 * t58 / t331 * t80 * t218 * t136 + 0.6e1 * t217 * t137 * t259 - t318 - 0.18e2 * t56 * t118 * t176 * t136 + 0.18e2 * t174 * t114 * t211 - 0.18e2 * t179 * t183 * t136 - t322 + t485))
  v3rho3_0_ = 0.2e1 * r0 * t491 + 0.6e1 * t277

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
  t28 = 0.1e1 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = t32 * t22
  t35 = 0.5e1 / 0.972e3 * t24 * t28 * t33
  t36 = params.kappa + t35
  t40 = params.kappa * (0.1e1 - params.kappa / t36)
  t41 = tau0 * t31
  t43 = 0.1e1 / t20 / r0
  t44 = t41 * t43
  t46 = t44 - t33 / 0.8e1
  t47 = t46 ** 2
  t48 = t24 ** 2
  t51 = 0.3e1 / 0.10e2 * t48 * t27 + t44
  t52 = t51 ** 2
  t53 = 0.1e1 / t52
  t56 = -0.4e1 * t47 * t53 + 0.1e1
  t57 = t56 ** 2
  t58 = t57 * t56
  t59 = t47 * t46
  t60 = t52 * t51
  t61 = 0.1e1 / t60
  t64 = t47 ** 2
  t66 = params.b * t64 * t47
  t67 = t52 ** 2
  t69 = 0.1e1 / t67 / t52
  t72 = 0.8e1 * t59 * t61 + 0.64e2 * t66 * t69 + 0.1e1
  t73 = 0.1e1 / t72
  t74 = t58 * t73
  t75 = params.kappa + t35 + params.c
  t80 = params.kappa * (0.1e1 - params.kappa / t75) - t40
  t82 = t74 * t80 + t40 + 0.1e1
  t86 = t17 * t43
  t87 = params.kappa ** 2
  t88 = t36 ** 2
  t91 = t87 / t88 * t24
  t92 = t28 * s0
  t93 = t18 * r0
  t95 = 0.1e1 / t20 / t93
  t96 = t31 * t95
  t97 = t92 * t96
  t98 = t91 * t97
  t100 = t57 * t73
  t101 = t46 * t53
  t102 = t41 * t22
  t106 = -0.5e1 / 0.3e1 * t102 + t32 * t95 / 0.3e1
  t109 = t47 * t61
  t112 = -0.8e1 * t101 * t106 - 0.40e2 / 0.3e1 * t109 * t102
  t113 = t80 * t112
  t116 = t72 ** 2
  t117 = 0.1e1 / t116
  t118 = t58 * t117
  t121 = 0.1e1 / t67
  t122 = t59 * t121
  t126 = params.b * t64 * t46
  t127 = t69 * t106
  t131 = 0.1e1 / t67 / t60
  t132 = t66 * t131
  t135 = 0.40e2 * t122 * t102 + 0.640e3 * t132 * t102 + 0.24e2 * t109 * t106 + 0.384e3 * t126 * t127
  t136 = t80 * t135
  t138 = t75 ** 2
  t141 = t87 / t138 * t24
  t144 = -0.10e2 / 0.729e3 * t141 * t97 + 0.10e2 / 0.729e3 * t98
  t146 = -0.10e2 / 0.729e3 * t98 + 0.3e1 * t100 * t113 - t118 * t136 + t74 * t144
  t151 = t17 / t20
  t155 = t87 / t88 / t36 * t48
  t158 = s0 ** 2
  t159 = 0.1e1 / t26 / t25 * t158
  t160 = t18 ** 2
  t163 = 0.1e1 / t19 / t160 / t93
  t165 = t159 * t30 * t163
  t167 = 0.400e3 / 0.531441e6 * t155 * t165
  t169 = 0.1e1 / t20 / t160
  t171 = t92 * t31 * t169
  t173 = 0.110e3 / 0.2187e4 * t91 * t171
  t174 = t56 * t73
  t175 = t112 ** 2
  t176 = t80 * t175
  t179 = t57 * t117
  t183 = t144 * t112
  t186 = t106 ** 2
  t189 = t46 * t61
  t190 = t189 * t106
  t193 = t41 * t95
  t197 = 0.40e2 / 0.9e1 * t193 - 0.11e2 / 0.9e1 * t32 * t169
  t200 = t47 * t121
  t201 = tau0 ** 2
  t202 = t201 * t30
  t203 = t160 * r0
  t205 = 0.1e1 / t19 / t203
  t206 = t202 * t205
  t211 = -0.8e1 * t186 * t53 - 0.160e3 / 0.3e1 * t190 * t102 - 0.8e1 * t101 * t197 - 0.400e3 / 0.3e1 * t200 * t206 + 0.320e3 / 0.9e1 * t109 * t193
  t212 = t80 * t211
  t216 = 0.1e1 / t116 / t72
  t217 = t58 * t216
  t218 = t135 ** 2
  t219 = t80 * t218
  t222 = t144 * t135
  t227 = t200 * t106
  t233 = 0.1e1 / t67 / t51
  t234 = t59 * t233
  t239 = params.b * t64
  t240 = t69 * t186
  t243 = t126 * t131
  t244 = t106 * tau0
  t245 = t31 * t22
  t252 = t67 ** 2
  t253 = 0.1e1 / t252
  t254 = t66 * t253
  t259 = 0.48e2 * t189 * t186 + 0.240e3 * t227 * t102 + 0.24e2 * t109 * t197 + 0.1600e4 / 0.3e1 * t234 * t206 - 0.320e3 / 0.3e1 * t122 * t193 + 0.1920e4 * t239 * t240 + 0.7680e4 * t243 * t244 * t245 + 0.384e3 * t126 * t69 * t197 + 0.44800e5 / 0.3e1 * t254 * t206 - 0.5120e4 / 0.3e1 * t132 * t193
  t265 = t87 / t138 / t75 * t48
  t270 = -0.400e3 / 0.531441e6 * t265 * t165 + 0.110e3 / 0.2187e4 * t141 * t171 + t167 - t173
  t272 = -0.6e1 * t179 * t113 * t135 - t118 * t80 * t259 + 0.6e1 * t100 * t183 + 0.3e1 * t100 * t212 - 0.2e1 * t118 * t222 + 0.6e1 * t174 * t176 + 0.2e1 * t217 * t219 + t74 * t270 - t167 + t173
  t276 = t17 * t19
  t277 = t138 ** 2
  t279 = t87 / t277
  t280 = t25 ** 2
  t281 = 0.1e1 / t280
  t283 = t281 * t158 * s0
  t284 = t160 ** 2
  t287 = t283 / t284 / t93
  t293 = t159 * t30 / t19 / t284
  t297 = 0.1e1 / t20 / t203
  t299 = t92 * t31 * t297
  t302 = t88 ** 2
  t304 = t87 / t302
  t306 = 0.16000e5 / 0.43046721e8 * t304 * t287
  t308 = 0.4400e4 / 0.531441e6 * t155 * t293
  t310 = 0.1540e4 / 0.6561e4 * t91 * t299
  t311 = -0.16000e5 / 0.43046721e8 * t279 * t287 + 0.4400e4 / 0.531441e6 * t265 * t293 - 0.1540e4 / 0.6561e4 * t141 * t299 + t306 - t308 + t310
  t319 = t116 ** 2
  t320 = 0.1e1 / t319
  t321 = t58 * t320
  t322 = t218 * t135
  t323 = t80 * t322
  t329 = t56 * t117
  t340 = t175 * t112
  t341 = t340 * t73
  t344 = t144 * t175
  t347 = t270 * t112
  t350 = t144 * t211
  t353 = t106 * t53
  t356 = t186 * t61
  t359 = t46 * t121
  t360 = t359 * t106
  t363 = t189 * t197
  t368 = t41 * t169
  t372 = -0.440e3 / 0.27e2 * t368 + 0.154e3 / 0.27e2 * t32 * t297
  t375 = t47 * t233
  t376 = t201 * tau0
  t377 = 0.1e1 / t284
  t378 = t376 * t377
  t381 = t160 * t18
  t383 = 0.1e1 / t19 / t381
  t384 = t202 * t383
  t389 = -0.24e2 * t353 * t197 - 0.80e2 * t356 * t102 - 0.800e3 * t360 * t206 - 0.80e2 * t363 * t102 + 0.640e3 / 0.3e1 * t190 * t193 - 0.8e1 * t101 * t372 - 0.16000e5 / 0.9e1 * t375 * t378 + 0.3200e4 / 0.3e1 * t200 * t384 - 0.3520e4 / 0.27e2 * t109 * t368
  t390 = t80 * t389
  t402 = t186 * t106
  t407 = t239 * t131
  t408 = t186 * tau0
  t412 = t197 * tau0
  t413 = t412 * t245
  t416 = t126 * t253
  t417 = t106 * t201
  t418 = t30 * t205
  t428 = params.b * t59
  t436 = 0.1e1 / t252 / t51
  t437 = t436 * t376
  t447 = t59 * t69
  t453 = t359 * t186
  t456 = t200 * t197
  t459 = t375 * t106
  t466 = 0.48e2 * t402 * t61 + 0.24e2 * t109 * t372 + 0.57600e5 * t407 * t408 * t245 + 0.11520e5 * t243 * t413 + 0.268800e6 * t416 * t417 * t418 - 0.358400e6 / 0.3e1 * t254 * t384 + 0.56320e5 / 0.9e1 * t132 * t368 - 0.960e3 * t227 * t193 + 0.7680e4 * t428 * t69 * t402 + 0.5760e4 * t239 * t127 * t197 + 0.3584000e7 / 0.9e1 * t66 * t437 * t377 - 0.30720e5 * t243 * t244 * t96 + 0.144e3 * t189 * t106 * t197 + 0.80000e5 / 0.9e1 * t447 * t378 + 0.384e3 * t126 * t69 * t372 + 0.720e3 * t453 * t102 + 0.360e3 * t456 * t102 + 0.4800e4 * t459 * t206 - 0.12800e5 / 0.3e1 * t234 * t384 + 0.3520e4 / 0.9e1 * t122 * t368
  t469 = t57 * t216
  t473 = 0.18e2 * t469 * t113 * t218 - 0.3e1 * t118 * t270 * t135 - 0.3e1 * t118 * t144 * t259 - t118 * t80 * t466 + 0.6e1 * t217 * t144 * t218 + 0.9e1 * t100 * t347 + 0.9e1 * t100 * t350 + 0.3e1 * t100 * t390 + 0.18e2 * t174 * t344 + 0.6e1 * t341 * t80 + t308
  t474 = 0.18e2 * t174 * t113 * t211 - 0.9e1 * t179 * t113 * t259 - 0.18e2 * t329 * t176 * t135 - 0.18e2 * t179 * t183 * t135 - 0.9e1 * t179 * t212 * t135 + 0.6e1 * t217 * t136 * t259 + t74 * t311 - 0.6e1 * t321 * t323 - t306 - t310 + t473
  t479 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t82 + t6 * t86 * t146 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t151 * t272 - 0.3e1 / 0.8e1 * t6 * t276 * t474)
  t506 = t283 / t284 / t160
  t508 = 0.352000e6 / 0.43046721e8 * t304 * t506
  t514 = t158 ** 2
  t515 = t281 * t514
  t522 = 0.1e1 / t20 / t284 / t381 * t24 * t28 * t31
  t527 = t284 * r0
  t531 = t159 * t30 / t19 / t527
  t535 = 0.1e1 / t20 / t381
  t537 = t92 * t31 * t535
  t545 = 0.640000e6 / 0.31381059609e11 * t87 / t302 / t36 * t515 * t522
  t547 = 0.391600e6 / 0.4782969e7 * t155 * t531
  t549 = 0.26180e5 / 0.19683e5 * t91 * t537
  t599 = -0.72e2 * t329 * t80 * t211 * t135 * t112 + 0.72e2 * t469 * t80 * t112 * t259 * t135 + t508 + 0.24e2 * t341 * t144 + t74 * (-0.640000e6 / 0.31381059609e11 * t87 / t277 / t75 * t515 * t522 + 0.352000e6 / 0.43046721e8 * t279 * t506 - 0.391600e6 / 0.4782969e7 * t265 * t531 + 0.26180e5 / 0.19683e5 * t141 * t537 + t545 - t508 + t547 - t549) - 0.72e2 * t57 * t320 * t323 * t112 - 0.18e2 * t179 * t212 * t259 - 0.72e2 * t329 * t344 * t135 + 0.72e2 * t174 * t183 * t211 + 0.24e2 * t174 * t113 * t389 - 0.36e2 * t179 * t347 * t135 - 0.12e2 * t179 * t113 * t466 + 0.24e2 * t217 * t222 * t259 + 0.8e1 * t217 * t136 * t466 - 0.36e2 * t179 * t350 * t135 - 0.12e2 * t179 * t390 * t135 + 0.36e2 * t469 * t212 * t218 - 0.36e2 * t179 * t183 * t259 + 0.72e2 * t56 * t216 * t176 * t218 + 0.72e2 * t469 * t183 * t218
  t606 = t197 ** 2
  t611 = t41 * t297
  t615 = 0.6160e4 / 0.81e2 * t611 - 0.2618e4 / 0.81e2 * t32 * t535
  t629 = t106 * t376 * t377
  t639 = t201 ** 2
  t644 = t639 / t20 / t284 / t18 * t31
  t647 = t46 * t233
  t654 = t202 * t163
  t660 = 0.1e1 / t527
  t670 = 0.144e3 * t189 * t606 + 0.288e3 * t356 * t197 + 0.24e2 * t109 * t615 - 0.788480e6 / 0.27e2 * t132 * t611 - 0.3840e4 * t453 * t193 + 0.14080e5 / 0.3e1 * t227 * t368 + 0.480e3 * t200 * t372 * t102 + 0.28672000e8 / 0.3e1 * t126 * t436 * t629 - 0.1920e4 * t456 * t193 - 0.51200e5 * t459 * t384 + 0.17920000e8 / 0.3e1 * t66 / t252 / t52 * t644 + 0.19200e5 * t647 * t186 * t206 + 0.9600e4 * t375 * t197 * t206 + 0.24371200e8 / 0.27e2 * t254 * t654 + 0.960e3 * t402 * t121 * t102 - 0.57344000e8 / 0.9e1 * t66 * t437 * t660 + 0.46080e5 * t428 * t240 * t197 + 0.7680e4 * t239 * t127 * t372
  t671 = t47 * t69
  t682 = t186 ** 2
  t689 = t376 * t660
  t736 = 0.320000e6 / 0.3e1 * t671 * t629 + 0.800000e6 / 0.9e1 * t59 * t131 * t644 + 0.870400e6 / 0.27e2 * t234 * t654 - 0.49280e5 / 0.27e2 * t122 * t611 + 0.23040e5 * params.b * t47 * t69 * t682 + 0.5760e4 * t239 * t69 * t606 - 0.1280000e7 / 0.9e1 * t447 * t689 + 0.192e3 * t189 * t372 * t106 + 0.384e3 * t126 * t69 * t615 - 0.2867200e7 * t416 * t417 * t30 * t383 + 0.307200e6 * t428 * t131 * t402 * tau0 * t245 - 0.307200e6 * t407 * t408 * t96 + 0.450560e6 / 0.3e1 * t243 * t41 * t169 * t106 + 0.2880e4 * t360 * t413 + 0.2688000e7 * t239 * t253 * t186 * t201 * t418 + 0.15360e5 * t243 * t372 * tau0 * t245 + 0.537600e6 * t416 * t197 * t201 * t418 - 0.61440e5 * t243 * t412 * t96 + 0.230400e6 * t239 * t131 * t106 * t413
  t780 = -0.24e2 * t606 * t53 - 0.32e2 * t353 * t372 - 0.8e1 * t101 * t615 + 0.256000e6 / 0.9e1 * t375 * t689 - 0.400000e6 / 0.27e2 * t671 * t644 - 0.1600e4 * t186 * t121 * t206 - 0.128000e6 / 0.9e1 * t647 * t629 + 0.25600e5 / 0.3e1 * t360 * t384 + 0.1280e4 / 0.3e1 * t363 * t193 - 0.28160e5 / 0.27e2 * t190 * t368 - 0.320e3 * t106 * t61 * t197 * t102 + 0.1280e4 / 0.3e1 * t356 * t193 - 0.1600e4 * t359 * t197 * t206 - 0.320e3 / 0.3e1 * t189 * t372 * t102 - 0.217600e6 / 0.27e2 * t200 * t654 + 0.49280e5 / 0.81e2 * t109 * t611
  t806 = t211 ** 2
  t816 = t259 ** 2
  t826 = t218 ** 2
  t830 = 0.18e2 * t100 * t270 * t211 + 0.36e2 * t175 * t73 * t212 + 0.18e2 * t174 * t80 * t806 + 0.12e2 * t100 * t311 * t112 - 0.4e1 * t118 * t311 * t135 + 0.6e1 * t217 * t80 * t816 - 0.24e2 * t340 * t117 * t136 + 0.24e2 * t58 / t319 / t72 * t80 * t826 - t547 + t549 - t545
  t837 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t95 * t82 - 0.5e1 / 0.9e1 * t6 * t23 * t146 + t6 * t86 * t272 / 0.2e1 - t6 * t151 * t474 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t276 * (t599 - 0.36e2 * t329 * t176 * t259 - 0.36e2 * t321 * t219 * t259 - t118 * t80 * (t670 + t736) - 0.4e1 * t118 * t144 * t466 + 0.3e1 * t100 * t80 * t780 + 0.12e2 * t217 * t270 * t218 - 0.6e1 * t118 * t270 * t259 + 0.12e2 * t100 * t144 * t389 - 0.24e2 * t321 * t144 * t322 + 0.36e2 * t174 * t270 * t175 + t830))
  v4rho4_0_ = 0.2e1 * r0 * t837 + 0.8e1 * t479

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
  t36 = 0.1e1 / t35
  t37 = t32 * t36
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t43 = s0 * t42
  t45 = 0.5e1 / 0.972e3 * t37 * t43
  t46 = params.kappa + t45
  t50 = params.kappa * (0.1e1 - params.kappa / t46)
  t53 = tau0 / t40 / r0
  t55 = t53 - t43 / 0.8e1
  t56 = t55 ** 2
  t57 = t32 ** 2
  t59 = 0.3e1 / 0.10e2 * t57 * t35
  t60 = t59 + t53
  t61 = t60 ** 2
  t62 = 0.1e1 / t61
  t65 = -0.4e1 * t56 * t62 + 0.1e1
  t66 = t65 ** 2
  t67 = t66 * t65
  t68 = t56 * t55
  t69 = t61 * t60
  t70 = 0.1e1 / t69
  t73 = t56 ** 2
  t75 = params.b * t73 * t56
  t76 = t61 ** 2
  t78 = 0.1e1 / t76 / t61
  t81 = 0.8e1 * t68 * t70 + 0.64e2 * t75 * t78 + 0.1e1
  t82 = 0.1e1 / t81
  t83 = t67 * t82
  t84 = params.kappa + t45 + params.c
  t89 = params.kappa * (0.1e1 - params.kappa / t84) - t50
  t91 = t83 * t89 + t50 + 0.1e1
  t95 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t96 = t95 * f.p.zeta_threshold
  t98 = f.my_piecewise3(t20, t96, t21 * t19)
  t99 = t30 ** 2
  t100 = 0.1e1 / t99
  t101 = t98 * t100
  t104 = t5 * t101 * t91 / 0.8e1
  t105 = t98 * t30
  t106 = params.kappa ** 2
  t107 = t46 ** 2
  t110 = t106 / t107 * t32
  t111 = t36 * s0
  t112 = t38 * r0
  t114 = 0.1e1 / t40 / t112
  t115 = t111 * t114
  t116 = t110 * t115
  t118 = t66 * t82
  t119 = t55 * t62
  t120 = tau0 * t42
  t124 = -0.5e1 / 0.3e1 * t120 + s0 * t114 / 0.3e1
  t127 = t56 * t70
  t130 = -0.8e1 * t119 * t124 - 0.40e2 / 0.3e1 * t127 * t120
  t131 = t89 * t130
  t134 = t81 ** 2
  t135 = 0.1e1 / t134
  t136 = t67 * t135
  t139 = 0.1e1 / t76
  t140 = t68 * t139
  t144 = params.b * t73 * t55
  t149 = 0.1e1 / t76 / t69
  t150 = t149 * tau0
  t154 = 0.384e3 * t144 * t78 * t124 + 0.640e3 * t75 * t150 * t42 + 0.40e2 * t140 * t120 + 0.24e2 * t127 * t124
  t157 = t84 ** 2
  t160 = t106 / t157 * t32
  t163 = -0.10e2 / 0.729e3 * t160 * t115 + 0.10e2 / 0.729e3 * t116
  t165 = -0.10e2 / 0.729e3 * t116 + 0.3e1 * t118 * t131 - t136 * t89 * t154 + t83 * t163
  t170 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t91 - t104 - 0.3e1 / 0.8e1 * t5 * t105 * t165)
  t172 = r1 <= f.p.dens_threshold
  t173 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t174 = 0.1e1 + t173
  t175 = t174 <= f.p.zeta_threshold
  t176 = t174 ** (0.1e1 / 0.3e1)
  t178 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t181 = f.my_piecewise3(t175, 0, 0.4e1 / 0.3e1 * t176 * t178)
  t182 = t181 * t30
  t183 = r1 ** 2
  t184 = r1 ** (0.1e1 / 0.3e1)
  t185 = t184 ** 2
  t187 = 0.1e1 / t185 / t183
  t188 = s2 * t187
  t190 = 0.5e1 / 0.972e3 * t37 * t188
  t191 = params.kappa + t190
  t195 = params.kappa * (0.1e1 - params.kappa / t191)
  t198 = tau1 / t185 / r1
  t200 = t198 - t188 / 0.8e1
  t201 = t200 ** 2
  t202 = t59 + t198
  t203 = t202 ** 2
  t204 = 0.1e1 / t203
  t207 = -0.4e1 * t201 * t204 + 0.1e1
  t208 = t207 ** 2
  t209 = t208 * t207
  t210 = t201 * t200
  t211 = t203 * t202
  t212 = 0.1e1 / t211
  t215 = t201 ** 2
  t217 = params.b * t215 * t201
  t218 = t203 ** 2
  t220 = 0.1e1 / t218 / t203
  t223 = 0.8e1 * t210 * t212 + 0.64e2 * t217 * t220 + 0.1e1
  t224 = 0.1e1 / t223
  t225 = t209 * t224
  t226 = params.kappa + t190 + params.c
  t231 = params.kappa * (0.1e1 - params.kappa / t226) - t195
  t233 = t225 * t231 + t195 + 0.1e1
  t238 = f.my_piecewise3(t175, t96, t176 * t174)
  t239 = t238 * t100
  t242 = t5 * t239 * t233 / 0.8e1
  t244 = f.my_piecewise3(t172, 0, -0.3e1 / 0.8e1 * t5 * t182 * t233 - t242)
  t246 = t21 ** 2
  t247 = 0.1e1 / t246
  t248 = t26 ** 2
  t253 = t16 / t22 / t6
  t255 = -0.2e1 * t23 + 0.2e1 * t253
  t256 = f.my_piecewise5(t10, 0, t14, 0, t255)
  t260 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t247 * t248 + 0.4e1 / 0.3e1 * t21 * t256)
  t267 = t5 * t29 * t100 * t91
  t273 = 0.1e1 / t99 / t6
  t277 = t5 * t98 * t273 * t91 / 0.12e2
  t279 = t5 * t101 * t165
  t286 = 0.1e1 / t34 / t33
  t287 = s0 ** 2
  t289 = t38 ** 2
  t293 = t286 * t287 / t39 / t289 / t112
  t295 = 0.200e3 / 0.531441e6 * t106 / t107 / t46 * t57 * t293
  t297 = 0.1e1 / t40 / t289
  t298 = t111 * t297
  t300 = 0.110e3 / 0.2187e4 * t110 * t298
  t302 = t130 ** 2
  t313 = t124 ** 2
  t316 = t55 * t70
  t318 = t124 * tau0 * t42
  t321 = tau0 * t114
  t325 = 0.40e2 / 0.9e1 * t321 - 0.11e2 / 0.9e1 * s0 * t297
  t328 = t56 * t139
  t329 = tau0 ** 2
  t332 = 0.1e1 / t39 / t289 / r0
  t333 = t329 * t332
  t345 = t154 ** 2
  t375 = t76 ** 2
  t402 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t260 * t30 * t91 - t267 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t165 + t277 - t279 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t105 * (-t295 + t300 + 0.6e1 * t65 * t82 * t89 * t302 - 0.6e1 * t66 * t135 * t131 * t154 + 0.6e1 * t118 * t163 * t130 + 0.3e1 * t118 * t89 * (-0.8e1 * t313 * t62 - 0.160e3 / 0.3e1 * t316 * t318 - 0.8e1 * t119 * t325 - 0.200e3 / 0.3e1 * t328 * t333 + 0.320e3 / 0.9e1 * t127 * t321) + 0.2e1 * t67 / t134 / t81 * t89 * t345 - 0.2e1 * t136 * t163 * t154 - t136 * t89 * (0.48e2 * t316 * t313 + 0.240e3 * t328 * t318 + 0.24e2 * t127 * t325 + 0.800e3 / 0.3e1 * t68 / t76 / t60 * t333 - 0.320e3 / 0.3e1 * t140 * t321 + 0.1920e4 * params.b * t73 * t78 * t313 + 0.7680e4 * t144 * t149 * t318 + 0.384e3 * t144 * t78 * t325 + 0.22400e5 / 0.3e1 * t75 / t375 * t329 * t332 - 0.5120e4 / 0.3e1 * t75 * t150 * t114) + t83 * (-0.200e3 / 0.531441e6 * t106 / t157 / t84 * t57 * t293 + 0.110e3 / 0.2187e4 * t160 * t298 + t295 - t300)))
  t403 = t176 ** 2
  t404 = 0.1e1 / t403
  t405 = t178 ** 2
  t409 = f.my_piecewise5(t14, 0, t10, 0, -t255)
  t413 = f.my_piecewise3(t175, 0, 0.4e1 / 0.9e1 * t404 * t405 + 0.4e1 / 0.3e1 * t176 * t409)
  t420 = t5 * t181 * t100 * t233
  t425 = t5 * t238 * t273 * t233 / 0.12e2
  t427 = f.my_piecewise3(t172, 0, -0.3e1 / 0.8e1 * t5 * t413 * t30 * t233 - t420 / 0.4e1 + t425)
  d11 = 0.2e1 * t170 + 0.2e1 * t244 + t6 * (t402 + t427)
  t430 = -t7 - t24
  t431 = f.my_piecewise5(t10, 0, t14, 0, t430)
  t434 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t431)
  t435 = t434 * t30
  t440 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t435 * t91 - t104)
  t442 = f.my_piecewise5(t14, 0, t10, 0, -t430)
  t445 = f.my_piecewise3(t175, 0, 0.4e1 / 0.3e1 * t176 * t442)
  t446 = t445 * t30
  t450 = t238 * t30
  t451 = t191 ** 2
  t454 = t106 / t451 * t32
  t455 = t36 * s2
  t456 = t183 * r1
  t458 = 0.1e1 / t185 / t456
  t459 = t455 * t458
  t460 = t454 * t459
  t462 = t208 * t224
  t463 = t200 * t204
  t464 = tau1 * t187
  t468 = -0.5e1 / 0.3e1 * t464 + s2 * t458 / 0.3e1
  t471 = t201 * t212
  t474 = -0.8e1 * t463 * t468 - 0.40e2 / 0.3e1 * t471 * t464
  t475 = t231 * t474
  t478 = t223 ** 2
  t479 = 0.1e1 / t478
  t480 = t209 * t479
  t483 = 0.1e1 / t218
  t484 = t210 * t483
  t488 = params.b * t215 * t200
  t493 = 0.1e1 / t218 / t211
  t494 = t493 * tau1
  t498 = 0.640e3 * t217 * t494 * t187 + 0.384e3 * t488 * t220 * t468 + 0.40e2 * t484 * t464 + 0.24e2 * t471 * t468
  t501 = t226 ** 2
  t504 = t106 / t501 * t32
  t507 = -0.10e2 / 0.729e3 * t504 * t459 + 0.10e2 / 0.729e3 * t460
  t509 = -0.10e2 / 0.729e3 * t460 + 0.3e1 * t462 * t475 - t480 * t231 * t498 + t225 * t507
  t514 = f.my_piecewise3(t172, 0, -0.3e1 / 0.8e1 * t5 * t446 * t233 - t242 - 0.3e1 / 0.8e1 * t5 * t450 * t509)
  t518 = 0.2e1 * t253
  t519 = f.my_piecewise5(t10, 0, t14, 0, t518)
  t523 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t247 * t431 * t26 + 0.4e1 / 0.3e1 * t21 * t519)
  t530 = t5 * t434 * t100 * t91
  t538 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t523 * t30 * t91 - t530 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t435 * t165 - t267 / 0.8e1 + t277 - t279 / 0.8e1)
  t542 = f.my_piecewise5(t14, 0, t10, 0, -t518)
  t546 = f.my_piecewise3(t175, 0, 0.4e1 / 0.9e1 * t404 * t442 * t178 + 0.4e1 / 0.3e1 * t176 * t542)
  t553 = t5 * t445 * t100 * t233
  t560 = t5 * t239 * t509
  t563 = f.my_piecewise3(t172, 0, -0.3e1 / 0.8e1 * t5 * t546 * t30 * t233 - t553 / 0.8e1 - t420 / 0.8e1 + t425 - 0.3e1 / 0.8e1 * t5 * t182 * t509 - t560 / 0.8e1)
  d12 = t170 + t244 + t440 + t514 + t6 * (t538 + t563)
  t568 = t431 ** 2
  t572 = 0.2e1 * t23 + 0.2e1 * t253
  t573 = f.my_piecewise5(t10, 0, t14, 0, t572)
  t577 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t247 * t568 + 0.4e1 / 0.3e1 * t21 * t573)
  t584 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t577 * t30 * t91 - t530 / 0.4e1 + t277)
  t585 = t442 ** 2
  t589 = f.my_piecewise5(t14, 0, t10, 0, -t572)
  t593 = f.my_piecewise3(t175, 0, 0.4e1 / 0.9e1 * t404 * t585 + 0.4e1 / 0.3e1 * t176 * t589)
  t607 = s2 ** 2
  t609 = t183 ** 2
  t613 = t286 * t607 / t184 / t609 / t456
  t615 = 0.200e3 / 0.531441e6 * t106 / t451 / t191 * t57 * t613
  t617 = 0.1e1 / t185 / t609
  t618 = t455 * t617
  t620 = 0.110e3 / 0.2187e4 * t454 * t618
  t622 = t474 ** 2
  t633 = t468 ** 2
  t636 = t200 * t212
  t638 = t468 * tau1 * t187
  t641 = tau1 * t458
  t645 = 0.40e2 / 0.9e1 * t641 - 0.11e2 / 0.9e1 * s2 * t617
  t648 = t201 * t483
  t649 = tau1 ** 2
  t652 = 0.1e1 / t184 / t609 / r1
  t653 = t649 * t652
  t665 = t498 ** 2
  t695 = t218 ** 2
  t722 = f.my_piecewise3(t172, 0, -0.3e1 / 0.8e1 * t5 * t593 * t30 * t233 - t553 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t446 * t509 + t425 - t560 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t450 * (-t615 + t620 + 0.6e1 * t207 * t224 * t231 * t622 - 0.6e1 * t208 * t479 * t475 * t498 + 0.6e1 * t462 * t507 * t474 + 0.3e1 * t462 * t231 * (-0.8e1 * t633 * t204 - 0.160e3 / 0.3e1 * t636 * t638 - 0.8e1 * t463 * t645 - 0.200e3 / 0.3e1 * t648 * t653 + 0.320e3 / 0.9e1 * t471 * t641) + 0.2e1 * t209 / t478 / t223 * t231 * t665 - 0.2e1 * t480 * t507 * t498 - t480 * t231 * (0.48e2 * t636 * t633 + 0.240e3 * t648 * t638 + 0.24e2 * t471 * t645 + 0.800e3 / 0.3e1 * t210 / t218 / t202 * t653 - 0.320e3 / 0.3e1 * t484 * t641 + 0.1920e4 * params.b * t215 * t220 * t633 + 0.7680e4 * t488 * t493 * t638 + 0.384e3 * t488 * t220 * t645 + 0.22400e5 / 0.3e1 * t217 / t695 * t649 * t652 - 0.5120e4 / 0.3e1 * t217 * t494 * t458) + t225 * (-0.200e3 / 0.531441e6 * t106 / t501 / t226 * t57 * t613 + 0.110e3 / 0.2187e4 * t504 * t618 + t615 - t620)))
  d22 = 0.2e1 * t440 + 0.2e1 * t514 + t6 * (t584 + t722)
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
  t48 = 0.1e1 / t47
  t49 = t44 * t48
  t50 = r0 ** 2
  t51 = r0 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t54 = 0.1e1 / t52 / t50
  t55 = s0 * t54
  t57 = 0.5e1 / 0.972e3 * t49 * t55
  t58 = params.kappa + t57
  t62 = params.kappa * (0.1e1 - params.kappa / t58)
  t65 = tau0 / t52 / r0
  t67 = t65 - t55 / 0.8e1
  t68 = t67 ** 2
  t69 = t44 ** 2
  t71 = 0.3e1 / 0.10e2 * t69 * t47
  t72 = t71 + t65
  t73 = t72 ** 2
  t74 = 0.1e1 / t73
  t77 = -0.4e1 * t68 * t74 + 0.1e1
  t78 = t77 ** 2
  t79 = t78 * t77
  t80 = t68 * t67
  t81 = t73 * t72
  t82 = 0.1e1 / t81
  t85 = t68 ** 2
  t87 = params.b * t85 * t68
  t88 = t73 ** 2
  t90 = 0.1e1 / t88 / t73
  t93 = 0.8e1 * t80 * t82 + 0.64e2 * t87 * t90 + 0.1e1
  t94 = 0.1e1 / t93
  t95 = t79 * t94
  t96 = params.kappa + t57 + params.c
  t101 = params.kappa * (0.1e1 - params.kappa / t96) - t62
  t103 = t95 * t101 + t62 + 0.1e1
  t109 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t110 = t42 ** 2
  t111 = 0.1e1 / t110
  t112 = t109 * t111
  t116 = t109 * t42
  t117 = params.kappa ** 2
  t118 = t58 ** 2
  t121 = t117 / t118 * t44
  t122 = t48 * s0
  t123 = t50 * r0
  t125 = 0.1e1 / t52 / t123
  t126 = t122 * t125
  t127 = t121 * t126
  t129 = t78 * t94
  t130 = t67 * t74
  t131 = tau0 * t54
  t135 = -0.5e1 / 0.3e1 * t131 + s0 * t125 / 0.3e1
  t138 = t68 * t82
  t141 = -0.8e1 * t130 * t135 - 0.40e2 / 0.3e1 * t138 * t131
  t142 = t101 * t141
  t145 = t93 ** 2
  t146 = 0.1e1 / t145
  t147 = t79 * t146
  t150 = 0.1e1 / t88
  t151 = t80 * t150
  t155 = params.b * t85 * t67
  t156 = t90 * t135
  t160 = 0.1e1 / t88 / t81
  t161 = t160 * tau0
  t165 = 0.640e3 * t87 * t161 * t54 + 0.40e2 * t151 * t131 + 0.24e2 * t138 * t135 + 0.384e3 * t155 * t156
  t166 = t101 * t165
  t168 = t96 ** 2
  t171 = t117 / t168 * t44
  t174 = -0.10e2 / 0.729e3 * t171 * t126 + 0.10e2 / 0.729e3 * t127
  t176 = -0.10e2 / 0.729e3 * t127 + 0.3e1 * t129 * t142 - t147 * t166 + t95 * t174
  t180 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t181 = t180 * f.p.zeta_threshold
  t183 = f.my_piecewise3(t20, t181, t21 * t19)
  t185 = 0.1e1 / t110 / t6
  t186 = t183 * t185
  t190 = t183 * t111
  t194 = t183 * t42
  t198 = t117 / t118 / t58 * t69
  t201 = s0 ** 2
  t202 = 0.1e1 / t46 / t45 * t201
  t203 = t50 ** 2
  t207 = t202 / t51 / t203 / t123
  t209 = 0.200e3 / 0.531441e6 * t198 * t207
  t211 = 0.1e1 / t52 / t203
  t212 = t122 * t211
  t214 = 0.110e3 / 0.2187e4 * t121 * t212
  t215 = t77 * t94
  t216 = t141 ** 2
  t217 = t101 * t216
  t220 = t78 * t146
  t224 = t174 * t141
  t227 = t135 ** 2
  t230 = t67 * t82
  t231 = t135 * tau0
  t232 = t231 * t54
  t235 = tau0 * t125
  t239 = 0.40e2 / 0.9e1 * t235 - 0.11e2 / 0.9e1 * s0 * t211
  t242 = t68 * t150
  t243 = tau0 ** 2
  t244 = t203 * r0
  t246 = 0.1e1 / t51 / t244
  t247 = t243 * t246
  t252 = -0.8e1 * t227 * t74 - 0.160e3 / 0.3e1 * t230 * t232 - 0.8e1 * t130 * t239 - 0.200e3 / 0.3e1 * t242 * t247 + 0.320e3 / 0.9e1 * t138 * t235
  t253 = t101 * t252
  t257 = 0.1e1 / t145 / t93
  t258 = t79 * t257
  t259 = t165 ** 2
  t273 = 0.1e1 / t88 / t72
  t274 = t80 * t273
  t279 = params.b * t85
  t283 = t155 * t160
  t289 = t88 ** 2
  t290 = 0.1e1 / t289
  t291 = t290 * t243
  t298 = 0.48e2 * t230 * t227 + 0.240e3 * t242 * t232 + 0.24e2 * t138 * t239 + 0.800e3 / 0.3e1 * t274 * t247 - 0.320e3 / 0.3e1 * t151 * t235 + 0.1920e4 * t279 * t90 * t227 + 0.7680e4 * t283 * t232 + 0.384e3 * t155 * t90 * t239 + 0.22400e5 / 0.3e1 * t87 * t291 * t246 - 0.5120e4 / 0.3e1 * t87 * t161 * t125
  t304 = t117 / t168 / t96 * t69
  t309 = -0.200e3 / 0.531441e6 * t304 * t207 + 0.110e3 / 0.2187e4 * t171 * t212 + t209 - t214
  t311 = -t147 * t101 * t298 + 0.2e1 * t258 * t101 * t259 - 0.6e1 * t220 * t142 * t165 - 0.2e1 * t147 * t174 * t165 + 0.6e1 * t129 * t224 + 0.3e1 * t129 * t253 + 0.6e1 * t215 * t217 + t95 * t309 - t209 + t214
  t316 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t103 - t5 * t112 * t103 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t116 * t176 + t5 * t186 * t103 / 0.12e2 - t5 * t190 * t176 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t194 * t311)
  t318 = r1 <= f.p.dens_threshold
  t319 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t320 = 0.1e1 + t319
  t321 = t320 <= f.p.zeta_threshold
  t322 = t320 ** (0.1e1 / 0.3e1)
  t323 = t322 ** 2
  t324 = 0.1e1 / t323
  t326 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t327 = t326 ** 2
  t331 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t335 = f.my_piecewise3(t321, 0, 0.4e1 / 0.9e1 * t324 * t327 + 0.4e1 / 0.3e1 * t322 * t331)
  t337 = r1 ** 2
  t338 = r1 ** (0.1e1 / 0.3e1)
  t339 = t338 ** 2
  t342 = s2 / t339 / t337
  t344 = 0.5e1 / 0.972e3 * t49 * t342
  t349 = params.kappa * (0.1e1 - params.kappa / (params.kappa + t344))
  t352 = tau1 / t339 / r1
  t354 = t352 - t342 / 0.8e1
  t355 = t354 ** 2
  t356 = t71 + t352
  t357 = t356 ** 2
  t361 = 0.1e1 - 0.4e1 * t355 / t357
  t362 = t361 ** 2
  t369 = t355 ** 2
  t372 = t357 ** 2
  t387 = 0.1e1 + t349 + t362 * t361 / (0.1e1 + 0.8e1 * t355 * t354 / t357 / t356 + 0.64e2 * params.b * t369 * t355 / t372 / t357) * (params.kappa * (0.1e1 - params.kappa / (params.kappa + t344 + params.c)) - t349)
  t393 = f.my_piecewise3(t321, 0, 0.4e1 / 0.3e1 * t322 * t326)
  t399 = f.my_piecewise3(t321, t181, t322 * t320)
  t405 = f.my_piecewise3(t318, 0, -0.3e1 / 0.8e1 * t5 * t335 * t42 * t387 - t5 * t393 * t111 * t387 / 0.4e1 + t5 * t399 * t185 * t387 / 0.12e2)
  t415 = t24 ** 2
  t419 = 0.6e1 * t33 - 0.6e1 * t16 / t415
  t420 = f.my_piecewise5(t10, 0, t14, 0, t419)
  t424 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t420)
  t447 = 0.1e1 / t110 / t24
  t458 = t168 ** 2
  t461 = t45 ** 2
  t465 = t203 ** 2
  t468 = 0.1e1 / t461 * t201 * s0 / t465 / t123
  t473 = t202 / t51 / t465
  t477 = 0.1e1 / t52 / t244
  t478 = t122 * t477
  t481 = t118 ** 2
  t485 = 0.4000e4 / 0.43046721e8 * t117 / t481 * t468
  t487 = 0.2200e4 / 0.531441e6 * t198 * t473
  t489 = 0.1540e4 / 0.6561e4 * t121 * t478
  t492 = t145 ** 2
  t538 = t67 * t150
  t540 = t135 * t243 * t246
  t544 = t239 * tau0 * t54
  t547 = t231 * t125
  t550 = tau0 * t211
  t554 = -0.440e3 / 0.27e2 * t550 + 0.154e3 / 0.27e2 * s0 * t477
  t557 = t68 * t273
  t558 = t243 * tau0
  t559 = 0.1e1 / t465
  t560 = t558 * t559
  t565 = 0.1e1 / t51 / t203 / t50
  t566 = t243 * t565
  t590 = t227 * t135
  t598 = t227 * tau0 * t54
  t641 = 0.20000e5 / 0.9e1 * t80 * t90 * t560 + 0.384e3 * t155 * t90 * t554 + 0.48e2 * t590 * t82 + 0.24e2 * t138 * t554 - 0.30720e5 * t283 * t547 + 0.720e3 * t538 * t598 + 0.360e3 * t242 * t544 + 0.2400e4 * t557 * t540 - 0.6400e4 / 0.3e1 * t274 * t566 + 0.3520e4 / 0.9e1 * t151 * t550 + 0.7680e4 * params.b * t80 * t90 * t590 + 0.5760e4 * t279 * t156 * t239 + 0.896000e6 / 0.9e1 * t87 / t289 / t72 * t558 * t559 + 0.144e3 * t230 * t135 * t239 - 0.960e3 * t242 * t547 + 0.57600e5 * t279 * t160 * t598 + 0.11520e5 * t283 * t544 + 0.134400e6 * t155 * t290 * t540 - 0.179200e6 / 0.3e1 * t87 * t291 * t565 + 0.56320e5 / 0.9e1 * t87 * t161 * t211
  t648 = -0.9e1 * t220 * t142 * t298 + 0.6e1 * t216 * t141 * t94 * t101 + 0.18e2 * t215 * t174 * t216 + 0.9e1 * t129 * t309 * t141 + 0.9e1 * t129 * t174 * t252 + 0.3e1 * t129 * t101 * (-0.24e2 * t135 * t74 * t239 - 0.80e2 * t227 * t82 * t131 - 0.400e3 * t538 * t540 - 0.80e2 * t230 * t544 + 0.640e3 / 0.3e1 * t230 * t547 - 0.8e1 * t130 * t554 - 0.4000e4 / 0.9e1 * t557 * t560 + 0.1600e4 / 0.3e1 * t242 * t566 - 0.3520e4 / 0.27e2 * t138 * t550) + 0.6e1 * t258 * t174 * t259 - 0.3e1 * t147 * t309 * t165 - 0.3e1 * t147 * t174 * t298 - t147 * t101 * t641 + 0.18e2 * t78 * t257 * t142 * t259
  t654 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t424 * t42 * t103 - 0.3e1 / 0.8e1 * t5 * t41 * t111 * t103 - 0.9e1 / 0.8e1 * t5 * t43 * t176 + t5 * t109 * t185 * t103 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t112 * t176 - 0.9e1 / 0.8e1 * t5 * t116 * t311 - 0.5e1 / 0.36e2 * t5 * t183 * t447 * t103 + t5 * t186 * t176 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t190 * t311 - 0.3e1 / 0.8e1 * t5 * t194 * (t95 * (-0.4000e4 / 0.43046721e8 * t117 / t458 * t468 + 0.2200e4 / 0.531441e6 * t304 * t473 - 0.1540e4 / 0.6561e4 * t171 * t478 + t485 - t487 + t489) + t487 - t489 - 0.6e1 * t79 / t492 * t101 * t259 * t165 + 0.6e1 * t258 * t166 * t298 - t485 - 0.18e2 * t77 * t146 * t217 * t165 + 0.18e2 * t215 * t142 * t252 - 0.18e2 * t220 * t224 * t165 - 0.9e1 * t220 * t253 * t165 + t648))
  t664 = f.my_piecewise5(t14, 0, t10, 0, -t419)
  t668 = f.my_piecewise3(t321, 0, -0.8e1 / 0.27e2 / t323 / t320 * t327 * t326 + 0.4e1 / 0.3e1 * t324 * t326 * t331 + 0.4e1 / 0.3e1 * t322 * t664)
  t686 = f.my_piecewise3(t318, 0, -0.3e1 / 0.8e1 * t5 * t668 * t42 * t387 - 0.3e1 / 0.8e1 * t5 * t335 * t111 * t387 + t5 * t393 * t185 * t387 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t399 * t447 * t387)
  d111 = 0.3e1 * t316 + 0.3e1 * t405 + t6 * (t654 + t686)

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
  t69 = 0.5e1 / 0.972e3 * t61 * t67
  t70 = params.kappa + t69
  t74 = params.kappa * (0.1e1 - params.kappa / t70)
  t77 = tau0 / t64 / r0
  t79 = t77 - t67 / 0.8e1
  t80 = t79 ** 2
  t81 = t56 ** 2
  t83 = 0.3e1 / 0.10e2 * t81 * t59
  t84 = t83 + t77
  t85 = t84 ** 2
  t86 = 0.1e1 / t85
  t89 = -0.4e1 * t80 * t86 + 0.1e1
  t90 = t89 ** 2
  t91 = t90 * t89
  t92 = t80 * t79
  t93 = t85 * t84
  t94 = 0.1e1 / t93
  t97 = t80 ** 2
  t99 = params.b * t97 * t80
  t100 = t85 ** 2
  t102 = 0.1e1 / t100 / t85
  t105 = 0.64e2 * t99 * t102 + 0.8e1 * t92 * t94 + 0.1e1
  t106 = 0.1e1 / t105
  t107 = t91 * t106
  t108 = params.kappa + t69 + params.c
  t113 = params.kappa * (0.1e1 - params.kappa / t108) - t74
  t115 = t107 * t113 + t74 + 0.1e1
  t124 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t125 = t54 ** 2
  t126 = 0.1e1 / t125
  t127 = t124 * t126
  t131 = t124 * t54
  t132 = params.kappa ** 2
  t133 = t70 ** 2
  t136 = t132 / t133 * t56
  t137 = t60 * s0
  t138 = t62 * r0
  t140 = 0.1e1 / t64 / t138
  t141 = t137 * t140
  t142 = t136 * t141
  t144 = t90 * t106
  t145 = t79 * t86
  t146 = tau0 * t66
  t150 = -0.5e1 / 0.3e1 * t146 + s0 * t140 / 0.3e1
  t153 = t80 * t94
  t156 = -0.8e1 * t145 * t150 - 0.40e2 / 0.3e1 * t153 * t146
  t157 = t113 * t156
  t160 = t105 ** 2
  t161 = 0.1e1 / t160
  t162 = t91 * t161
  t165 = 0.1e1 / t100
  t166 = t92 * t165
  t170 = params.b * t97 * t79
  t171 = t102 * t150
  t175 = 0.1e1 / t100 / t93
  t176 = t175 * tau0
  t180 = 0.640e3 * t99 * t176 * t66 + 0.40e2 * t166 * t146 + 0.24e2 * t153 * t150 + 0.384e3 * t170 * t171
  t181 = t113 * t180
  t183 = t108 ** 2
  t186 = t132 / t183 * t56
  t189 = -0.10e2 / 0.729e3 * t186 * t141 + 0.10e2 / 0.729e3 * t142
  t191 = -0.10e2 / 0.729e3 * t142 + 0.3e1 * t144 * t157 - t162 * t181 + t107 * t189
  t197 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t199 = 0.1e1 / t125 / t6
  t200 = t197 * t199
  t204 = t197 * t126
  t208 = t197 * t54
  t212 = t132 / t133 / t70 * t81
  t215 = s0 ** 2
  t216 = 0.1e1 / t58 / t57 * t215
  t217 = t62 ** 2
  t220 = 0.1e1 / t63 / t217 / t138
  t221 = t216 * t220
  t223 = 0.200e3 / 0.531441e6 * t212 * t221
  t225 = 0.1e1 / t64 / t217
  t226 = t137 * t225
  t228 = 0.110e3 / 0.2187e4 * t136 * t226
  t229 = t89 * t106
  t230 = t156 ** 2
  t231 = t113 * t230
  t234 = t90 * t161
  t238 = t189 * t156
  t241 = t150 ** 2
  t244 = t79 * t94
  t245 = t150 * tau0
  t246 = t245 * t66
  t249 = tau0 * t140
  t253 = 0.40e2 / 0.9e1 * t249 - 0.11e2 / 0.9e1 * s0 * t225
  t256 = t80 * t165
  t257 = tau0 ** 2
  t258 = t217 * r0
  t260 = 0.1e1 / t63 / t258
  t261 = t257 * t260
  t266 = -0.8e1 * t241 * t86 - 0.160e3 / 0.3e1 * t244 * t246 - 0.8e1 * t145 * t253 - 0.200e3 / 0.3e1 * t256 * t261 + 0.320e3 / 0.9e1 * t153 * t249
  t267 = t113 * t266
  t271 = 0.1e1 / t160 / t105
  t272 = t91 * t271
  t273 = t180 ** 2
  t274 = t113 * t273
  t277 = t189 * t180
  t287 = 0.1e1 / t100 / t84
  t288 = t92 * t287
  t293 = params.b * t97
  t294 = t102 * t241
  t297 = t170 * t175
  t303 = t100 ** 2
  t304 = 0.1e1 / t303
  t305 = t304 * t257
  t312 = 0.48e2 * t244 * t241 + 0.240e3 * t256 * t246 + 0.24e2 * t153 * t253 + 0.800e3 / 0.3e1 * t288 * t261 - 0.320e3 / 0.3e1 * t166 * t249 + 0.1920e4 * t293 * t294 + 0.7680e4 * t297 * t246 + 0.384e3 * t170 * t102 * t253 + 0.22400e5 / 0.3e1 * t99 * t305 * t260 - 0.5120e4 / 0.3e1 * t99 * t176 * t140
  t318 = t132 / t183 / t108 * t81
  t323 = -0.200e3 / 0.531441e6 * t318 * t221 + 0.110e3 / 0.2187e4 * t186 * t226 + t223 - t228
  t325 = -t162 * t113 * t312 - 0.6e1 * t234 * t157 * t180 + t107 * t323 + 0.6e1 * t144 * t238 + 0.3e1 * t144 * t267 - 0.2e1 * t162 * t277 + 0.6e1 * t229 * t231 + 0.2e1 * t272 * t274 - t223 + t228
  t329 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t330 = t329 * f.p.zeta_threshold
  t332 = f.my_piecewise3(t20, t330, t21 * t19)
  t334 = 0.1e1 / t125 / t25
  t335 = t332 * t334
  t339 = t332 * t199
  t343 = t332 * t126
  t347 = t332 * t54
  t348 = t183 ** 2
  t350 = t132 / t348
  t351 = t57 ** 2
  t352 = 0.1e1 / t351
  t354 = t352 * t215 * s0
  t355 = t217 ** 2
  t358 = t354 / t355 / t138
  t363 = t216 / t63 / t355
  t367 = 0.1e1 / t64 / t258
  t368 = t137 * t367
  t371 = t133 ** 2
  t373 = t132 / t371
  t375 = 0.4000e4 / 0.43046721e8 * t373 * t358
  t377 = 0.2200e4 / 0.531441e6 * t212 * t363
  t379 = 0.1540e4 / 0.6561e4 * t136 * t368
  t380 = -0.4000e4 / 0.43046721e8 * t350 * t358 + 0.2200e4 / 0.531441e6 * t318 * t363 - 0.1540e4 / 0.6561e4 * t186 * t368 + t375 - t377 + t379
  t382 = t160 ** 2
  t383 = 0.1e1 / t382
  t384 = t91 * t383
  t385 = t273 * t180
  t386 = t113 * t385
  t392 = t89 * t161
  t409 = t230 * t156
  t410 = t409 * t106
  t413 = t189 * t230
  t416 = t323 * t156
  t419 = t189 * t266
  t422 = t150 * t86
  t425 = t241 * t94
  t428 = t79 * t165
  t429 = t150 * t257
  t430 = t429 * t260
  t433 = t253 * tau0
  t434 = t433 * t66
  t437 = t245 * t140
  t440 = tau0 * t225
  t444 = -0.440e3 / 0.27e2 * t440 + 0.154e3 / 0.27e2 * s0 * t367
  t447 = t80 * t287
  t448 = t257 * tau0
  t449 = 0.1e1 / t355
  t450 = t448 * t449
  t453 = t217 * t62
  t455 = 0.1e1 / t63 / t453
  t456 = t257 * t455
  t461 = -0.24e2 * t422 * t253 - 0.80e2 * t425 * t146 - 0.400e3 * t428 * t430 - 0.80e2 * t244 * t434 + 0.640e3 / 0.3e1 * t244 * t437 - 0.8e1 * t145 * t444 - 0.4000e4 / 0.9e1 * t447 * t450 + 0.1600e4 / 0.3e1 * t256 * t456 - 0.3520e4 / 0.27e2 * t153 * t440
  t462 = t113 * t461
  t474 = t92 * t102
  t477 = t102 * t444
  t480 = t241 * t150
  t487 = t241 * tau0
  t488 = t487 * t66
  t499 = params.b * t92
  t507 = 0.1e1 / t303 / t84
  t508 = t507 * t448
  t512 = t150 * t253
  t517 = t293 * t175
  t522 = t170 * t304
  t531 = 0.20000e5 / 0.9e1 * t474 * t450 + 0.384e3 * t170 * t477 + 0.48e2 * t480 * t94 + 0.24e2 * t153 * t444 - 0.30720e5 * t297 * t437 + 0.720e3 * t428 * t488 + 0.360e3 * t256 * t434 + 0.2400e4 * t447 * t430 - 0.6400e4 / 0.3e1 * t288 * t456 + 0.3520e4 / 0.9e1 * t166 * t440 + 0.7680e4 * t499 * t102 * t480 + 0.5760e4 * t293 * t171 * t253 + 0.896000e6 / 0.9e1 * t99 * t508 * t449 + 0.144e3 * t244 * t512 - 0.960e3 * t256 * t437 + 0.57600e5 * t517 * t488 + 0.11520e5 * t297 * t434 + 0.134400e6 * t522 * t430 - 0.179200e6 / 0.3e1 * t99 * t305 * t455 + 0.56320e5 / 0.9e1 * t99 * t176 * t225
  t534 = t90 * t271
  t538 = -t162 * t113 * t531 - 0.9e1 * t234 * t157 * t312 + 0.18e2 * t534 * t157 * t273 - 0.3e1 * t162 * t323 * t180 - 0.3e1 * t162 * t189 * t312 + 0.6e1 * t272 * t189 * t273 + 0.6e1 * t410 * t113 + 0.9e1 * t144 * t416 + 0.9e1 * t144 * t419 + 0.3e1 * t144 * t462 + 0.18e2 * t229 * t413
  t539 = 0.18e2 * t229 * t157 * t266 - 0.18e2 * t392 * t231 * t180 - 0.18e2 * t234 * t238 * t180 - 0.9e1 * t234 * t267 * t180 + 0.6e1 * t272 * t181 * t312 + t107 * t380 - 0.6e1 * t384 * t386 - t375 + t377 - t379 + t538
  t544 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t115 - 0.3e1 / 0.8e1 * t5 * t127 * t115 - 0.9e1 / 0.8e1 * t5 * t131 * t191 + t5 * t200 * t115 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t204 * t191 - 0.9e1 / 0.8e1 * t5 * t208 * t325 - 0.5e1 / 0.36e2 * t5 * t335 * t115 + t5 * t339 * t191 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t343 * t325 - 0.3e1 / 0.8e1 * t5 * t347 * t539)
  t546 = r1 <= f.p.dens_threshold
  t547 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t548 = 0.1e1 + t547
  t549 = t548 <= f.p.zeta_threshold
  t550 = t548 ** (0.1e1 / 0.3e1)
  t551 = t550 ** 2
  t553 = 0.1e1 / t551 / t548
  t555 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t556 = t555 ** 2
  t560 = 0.1e1 / t551
  t561 = t560 * t555
  t563 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t567 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t571 = f.my_piecewise3(t549, 0, -0.8e1 / 0.27e2 * t553 * t556 * t555 + 0.4e1 / 0.3e1 * t561 * t563 + 0.4e1 / 0.3e1 * t550 * t567)
  t573 = r1 ** 2
  t574 = r1 ** (0.1e1 / 0.3e1)
  t575 = t574 ** 2
  t578 = s2 / t575 / t573
  t580 = 0.5e1 / 0.972e3 * t61 * t578
  t585 = params.kappa * (0.1e1 - params.kappa / (params.kappa + t580))
  t588 = tau1 / t575 / r1
  t590 = t588 - t578 / 0.8e1
  t591 = t590 ** 2
  t592 = t83 + t588
  t593 = t592 ** 2
  t597 = 0.1e1 - 0.4e1 * t591 / t593
  t598 = t597 ** 2
  t605 = t591 ** 2
  t608 = t593 ** 2
  t623 = 0.1e1 + t585 + t598 * t597 / (0.1e1 + 0.8e1 * t591 * t590 / t593 / t592 + 0.64e2 * params.b * t605 * t591 / t608 / t593) * (params.kappa * (0.1e1 - params.kappa / (params.kappa + t580 + params.c)) - t585)
  t632 = f.my_piecewise3(t549, 0, 0.4e1 / 0.9e1 * t560 * t556 + 0.4e1 / 0.3e1 * t550 * t563)
  t639 = f.my_piecewise3(t549, 0, 0.4e1 / 0.3e1 * t550 * t555)
  t645 = f.my_piecewise3(t549, t330, t550 * t548)
  t651 = f.my_piecewise3(t546, 0, -0.3e1 / 0.8e1 * t5 * t571 * t54 * t623 - 0.3e1 / 0.8e1 * t5 * t632 * t126 * t623 + t5 * t639 * t199 * t623 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t645 * t334 * t623)
  t678 = t354 / t355 / t217
  t680 = 0.88000e5 / 0.43046721e8 * t373 * t678
  t719 = t355 * r0
  t722 = t216 / t63 / t719
  t724 = 0.195800e6 / 0.4782969e7 * t212 * t722
  t726 = 0.1e1 / t64 / t453
  t727 = t137 * t726
  t729 = 0.26180e5 / 0.19683e5 * t136 * t727
  t744 = t215 ** 2
  t749 = t744 / t64 / t355 / t453 * t61
  t751 = 0.160000e6 / 0.31381059609e11 * t132 / t371 / t70 * t352 * t749
  t752 = -0.18e2 * t234 * t267 * t312 - 0.12e2 * t234 * t157 * t531 + t680 + 0.72e2 * t89 * t271 * t231 * t273 + 0.72e2 * t534 * t238 * t273 - 0.36e2 * t234 * t416 * t180 - 0.36e2 * t234 * t419 * t180 - 0.36e2 * t234 * t238 * t312 - 0.12e2 * t234 * t462 * t180 - 0.36e2 * t384 * t274 * t312 - 0.72e2 * t392 * t413 * t180 - 0.36e2 * t392 * t231 * t312 + 0.72e2 * t229 * t238 * t266 + 0.24e2 * t229 * t157 * t461 - 0.72e2 * t90 * t383 * t386 * t156 - t724 + t729 + 0.72e2 * t534 * t113 * t180 * t312 * t156 - 0.72e2 * t392 * t113 * t156 * t180 * t266 - t751
  t762 = t266 ** 2
  t769 = t273 ** 2
  t773 = t312 ** 2
  t777 = t429 * t455
  t789 = t450 * t150
  t794 = t241 * t257 * t260
  t798 = t253 * t257 * t260
  t801 = t487 * t140
  t804 = t245 * t225
  t808 = t444 * tau0 * t66
  t811 = t433 * t140
  t821 = 0.1e1 / t719
  t831 = t80 * t102
  t837 = -0.1433600e7 * t522 * t777 + 0.2880e4 * t428 * t150 * t434 + 0.307200e6 * t499 * t175 * t480 * tau0 * t66 + 0.7168000e7 / 0.3e1 * t170 * t507 * t789 + 0.1344000e7 * t293 * t304 * t794 + 0.268800e6 * t522 * t798 - 0.307200e6 * t517 * t801 + 0.450560e6 / 0.3e1 * t297 * t804 + 0.15360e5 * t297 * t808 - 0.61440e5 * t297 * t811 + 0.230400e6 * t517 * t512 * t146 - 0.1920e4 * t256 * t811 - 0.25600e5 * t447 * t777 - 0.14336000e8 / 0.9e1 * t99 * t508 * t821 + 0.12185600e8 / 0.27e2 * t99 * t305 * t220 - 0.788480e6 / 0.27e2 * t99 * t176 * t367 + 0.80000e5 / 0.3e1 * t831 * t789 + 0.7680e4 * t293 * t477 * t150
  t840 = t79 * t287
  t852 = t257 ** 2
  t856 = 0.1e1 / t64 / t355 / t62
  t862 = t448 * t821
  t865 = t257 * t220
  t868 = tau0 * t367
  t872 = t241 ** 2
  t876 = t253 ** 2
  t881 = t852 * t856
  t887 = 0.6160e4 / 0.81e2 * t868 - 0.2618e4 / 0.81e2 * s0 * t726
  t903 = 0.480e3 * t256 * t808 + 0.9600e4 * t840 * t794 + 0.4800e4 * t447 * t798 + 0.14080e5 / 0.3e1 * t256 * t804 + 0.46080e5 * t499 * t294 * t253 + 0.4480000e7 / 0.3e1 * t99 / t303 / t85 * t852 * t856 - 0.3840e4 * t428 * t801 - 0.320000e6 / 0.9e1 * t474 * t862 + 0.435200e6 / 0.27e2 * t288 * t865 - 0.49280e5 / 0.27e2 * t166 * t868 + 0.23040e5 * params.b * t80 * t102 * t872 + 0.5760e4 * t293 * t102 * t876 + 0.200000e6 / 0.9e1 * t92 * t175 * t881 + 0.384e3 * t170 * t102 * t887 + 0.960e3 * t480 * t165 * t146 + 0.192e3 * t244 * t444 * t150 + 0.144e3 * t244 * t876 + 0.288e3 * t425 * t253 + 0.24e2 * t153 * t887
  t966 = -0.320e3 * t150 * t94 * t434 + 0.1280e4 / 0.3e1 * t425 * t249 - 0.800e3 * t428 * t798 - 0.32000e5 / 0.9e1 * t840 * t789 - 0.320e3 / 0.3e1 * t244 * t808 + 0.64000e5 / 0.9e1 * t447 * t862 - 0.108800e6 / 0.27e2 * t256 * t865 + 0.49280e5 / 0.81e2 * t153 * t868 - 0.800e3 * t241 * t165 * t261 - 0.100000e6 / 0.27e2 * t831 * t881 - 0.24e2 * t876 * t86 - 0.32e2 * t422 * t444 - 0.8e1 * t145 * t887 + 0.12800e5 / 0.3e1 * t428 * t777 + 0.1280e4 / 0.3e1 * t244 * t811 - 0.28160e5 / 0.27e2 * t244 * t804
  t995 = 0.36e2 * t229 * t323 * t230 - 0.24e2 * t409 * t161 * t181 + 0.36e2 * t230 * t106 * t267 + 0.18e2 * t144 * t323 * t266 + 0.12e2 * t144 * t189 * t461 + 0.3e1 * t144 * t113 * t966 + 0.12e2 * t272 * t323 * t273 - 0.6e1 * t162 * t323 * t312 - 0.4e1 * t162 * t189 * t531 + t107 * (-0.160000e6 / 0.31381059609e11 * t132 / t348 / t108 * t352 * t749 + 0.88000e5 / 0.43046721e8 * t350 * t678 - 0.195800e6 / 0.4782969e7 * t318 * t722 + 0.26180e5 / 0.19683e5 * t186 * t727 + t751 - t680 + t724 - t729) + 0.24e2 * t410 * t189
  t1001 = t19 ** 2
  t1004 = t30 ** 2
  t1010 = t41 ** 2
  t1019 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t1020 = f.my_piecewise5(t10, 0, t14, 0, t1019)
  t1024 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t1001 * t1004 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t1010 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t1020)
  t1051 = 0.1e1 / t125 / t36
  t1056 = t5 * t200 * t191 - 0.3e1 / 0.2e1 * t5 * t204 * t325 - 0.3e1 / 0.2e1 * t5 * t208 * t539 - 0.5e1 / 0.9e1 * t5 * t335 * t191 + t5 * t339 * t325 / 0.2e1 - t5 * t343 * t539 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t347 * (t752 + 0.36e2 * t534 * t267 * t273 + 0.24e2 * t272 * t277 * t312 + 0.8e1 * t272 * t181 * t531 + 0.18e2 * t229 * t113 * t762 + 0.24e2 * t91 / t382 / t105 * t113 * t769 + 0.6e1 * t272 * t113 * t773 - t162 * t113 * (t837 + t903) + 0.12e2 * t144 * t380 * t156 - 0.4e1 * t162 * t380 * t180 - 0.24e2 * t384 * t189 * t385 + t995) - 0.3e1 / 0.8e1 * t5 * t1024 * t54 * t115 - 0.3e1 / 0.2e1 * t5 * t55 * t191 - 0.3e1 / 0.2e1 * t5 * t127 * t191 - 0.9e1 / 0.4e1 * t5 * t131 * t325 - t5 * t53 * t126 * t115 / 0.2e1 + t5 * t124 * t199 * t115 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t197 * t334 * t115 + 0.10e2 / 0.27e2 * t5 * t332 * t1051 * t115
  t1057 = f.my_piecewise3(t1, 0, t1056)
  t1058 = t548 ** 2
  t1061 = t556 ** 2
  t1067 = t563 ** 2
  t1073 = f.my_piecewise5(t14, 0, t10, 0, -t1019)
  t1077 = f.my_piecewise3(t549, 0, 0.40e2 / 0.81e2 / t551 / t1058 * t1061 - 0.16e2 / 0.9e1 * t553 * t556 * t563 + 0.4e1 / 0.3e1 * t560 * t1067 + 0.16e2 / 0.9e1 * t561 * t567 + 0.4e1 / 0.3e1 * t550 * t1073)
  t1099 = f.my_piecewise3(t546, 0, -0.3e1 / 0.8e1 * t5 * t1077 * t54 * t623 - t5 * t571 * t126 * t623 / 0.2e1 + t5 * t632 * t199 * t623 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t639 * t334 * t623 + 0.10e2 / 0.27e2 * t5 * t645 * t1051 * t623)
  d1111 = 0.4e1 * t544 + 0.4e1 * t651 + t6 * (t1057 + t1099)

  res = {'v4rho4': d1111}
  return res
