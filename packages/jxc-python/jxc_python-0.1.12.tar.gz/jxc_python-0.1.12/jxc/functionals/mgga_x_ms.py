"""Generated from mgga_x_ms.mpl."""

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

  ms_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  ms_f0 = lambda p, c: 1 + params_kappa * (1 - params_kappa / (params_kappa + MU_GE * p + c))

  ms_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  ms_f = lambda x, u, t: ms_f0(X2S ** 2 * x ** 2, 0) + ms_fa(ms_alpha(t, x)) * (ms_f0(X2S ** 2 * x ** 2, params_c) - ms_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ms_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  ms_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  ms_f0 = lambda p, c: 1 + params_kappa * (1 - params_kappa / (params_kappa + MU_GE * p + c))

  ms_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  ms_f = lambda x, u, t: ms_f0(X2S ** 2 * x ** 2, 0) + ms_fa(ms_alpha(t, x)) * (ms_f0(X2S ** 2 * x ** 2, params_c) - ms_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ms_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  ms_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  ms_f0 = lambda p, c: 1 + params_kappa * (1 - params_kappa / (params_kappa + MU_GE * p + c))

  ms_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  ms_f = lambda x, u, t: ms_f0(X2S ** 2 * x ** 2, 0) + ms_fa(ms_alpha(t, x)) * (ms_f0(X2S ** 2 * x ** 2, params_c) - ms_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ms_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t51 = tau0 * t48 - t39 / 0.8e1
  t52 = t51 ** 2
  t53 = t28 ** 2
  t56 = 0.1e1 / t30 / t29
  t59 = 0.1e1 - 0.25e2 / 0.81e2 * t52 * t53 * t56
  t60 = t59 ** 2
  t61 = t60 * t59
  t63 = t29 ** 2
  t64 = 0.1e1 / t63
  t67 = t52 ** 2
  t70 = t63 ** 2
  t71 = 0.1e1 / t70
  t74 = 0.1e1 + 0.250e3 / 0.243e3 * t52 * t51 * t64 + 0.62500e5 / 0.59049e5 * params.b * t67 * t52 * t71
  t75 = 0.1e1 / t74
  t76 = t61 * t75
  t77 = params.kappa + t41 + params.c
  t82 = params.kappa * (0.1e1 - params.kappa / t77) - t46
  t84 = t76 * t82 + t46 + 0.1e1
  t88 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t84)
  t89 = r1 <= f.p.dens_threshold
  t90 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t91 = 0.1e1 + t90
  t92 = t91 <= f.p.zeta_threshold
  t93 = t91 ** (0.1e1 / 0.3e1)
  t95 = f.my_piecewise3(t92, t22, t93 * t91)
  t96 = t95 * t26
  t97 = r1 ** 2
  t98 = r1 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t101 = 0.1e1 / t99 / t97
  t102 = s2 * t101
  t104 = 0.5e1 / 0.972e3 * t33 * t102
  t105 = params.kappa + t104
  t109 = params.kappa * (0.1e1 - params.kappa / t105)
  t111 = 0.1e1 / t99 / r1
  t114 = tau1 * t111 - t102 / 0.8e1
  t115 = t114 ** 2
  t119 = 0.1e1 - 0.25e2 / 0.81e2 * t115 * t53 * t56
  t120 = t119 ** 2
  t121 = t120 * t119
  t125 = t115 ** 2
  t130 = 0.1e1 + 0.250e3 / 0.243e3 * t115 * t114 * t64 + 0.62500e5 / 0.59049e5 * params.b * t125 * t115 * t71
  t131 = 0.1e1 / t130
  t132 = t121 * t131
  t133 = params.kappa + t104 + params.c
  t138 = params.kappa * (0.1e1 - params.kappa / t133) - t109
  t140 = t132 * t138 + t109 + 0.1e1
  t144 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t96 * t140)
  t145 = t6 ** 2
  t147 = t16 / t145
  t148 = t7 - t147
  t149 = f.my_piecewise5(t10, 0, t14, 0, t148)
  t152 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t149)
  t157 = t26 ** 2
  t158 = 0.1e1 / t157
  t162 = t5 * t25 * t158 * t84 / 0.8e1
  t163 = params.kappa ** 2
  t164 = t42 ** 2
  t166 = t163 / t164
  t171 = 0.1e1 / t36 / t34 / r0
  t172 = t32 * s0 * t171
  t173 = t166 * t28 * t172
  t176 = t60 * t75 * t82
  t177 = t51 * t53
  t182 = -0.5e1 / 0.3e1 * tau0 * t38 + s0 * t171 / 0.3e1
  t187 = t74 ** 2
  t189 = t61 / t187
  t190 = t52 * t64
  t194 = params.b * t67 * t51
  t201 = t77 ** 2
  t203 = t163 / t201
  t214 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t152 * t26 * t84 - t162 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.10e2 / 0.729e3 * t173 - 0.50e2 / 0.27e2 * t176 * t177 * t56 * t182 - t189 * t82 * (0.250e3 / 0.81e2 * t190 * t182 + 0.125000e6 / 0.19683e5 * t194 * t71 * t182) + t76 * (-0.10e2 / 0.729e3 * t203 * t28 * t172 + 0.10e2 / 0.729e3 * t173)))
  t216 = f.my_piecewise5(t14, 0, t10, 0, -t148)
  t219 = f.my_piecewise3(t92, 0, 0.4e1 / 0.3e1 * t93 * t216)
  t227 = t5 * t95 * t158 * t140 / 0.8e1
  t229 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t219 * t26 * t140 - t227)
  vrho_0_ = t88 + t144 + t6 * (t214 + t229)
  t232 = -t7 - t147
  t233 = f.my_piecewise5(t10, 0, t14, 0, t232)
  t236 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t233)
  t242 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t236 * t26 * t84 - t162)
  t244 = f.my_piecewise5(t14, 0, t10, 0, -t232)
  t247 = f.my_piecewise3(t92, 0, 0.4e1 / 0.3e1 * t93 * t244)
  t252 = t105 ** 2
  t254 = t163 / t252
  t259 = 0.1e1 / t99 / t97 / r1
  t260 = t32 * s2 * t259
  t261 = t254 * t28 * t260
  t264 = t120 * t131 * t138
  t265 = t114 * t53
  t270 = -0.5e1 / 0.3e1 * tau1 * t101 + s2 * t259 / 0.3e1
  t275 = t130 ** 2
  t277 = t121 / t275
  t278 = t115 * t64
  t282 = params.b * t125 * t114
  t289 = t133 ** 2
  t291 = t163 / t289
  t302 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t247 * t26 * t140 - t227 - 0.3e1 / 0.8e1 * t5 * t96 * (-0.10e2 / 0.729e3 * t261 - 0.50e2 / 0.27e2 * t264 * t265 * t56 * t270 - t277 * t138 * (0.250e3 / 0.81e2 * t278 * t270 + 0.125000e6 / 0.19683e5 * t282 * t71 * t270) + t132 * (-0.10e2 / 0.729e3 * t291 * t28 * t260 + 0.10e2 / 0.729e3 * t261)))
  vrho_1_ = t88 + t144 + t6 * (t242 + t302)
  t305 = t33 * t38
  t306 = t166 * t305
  t328 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.5e1 / 0.972e3 * t306 + 0.25e2 / 0.108e3 * t176 * t177 * t56 * t38 - t189 * t82 * (-0.125e3 / 0.324e3 * t190 * t38 - 0.15625e5 / 0.19683e5 * t194 * t71 * t38) + t76 * (0.5e1 / 0.972e3 * t203 * t305 - 0.5e1 / 0.972e3 * t306)))
  vsigma_0_ = t6 * t328
  vsigma_1_ = 0.0e0
  t329 = t33 * t101
  t330 = t254 * t329
  t352 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t96 * (0.5e1 / 0.972e3 * t330 + 0.25e2 / 0.108e3 * t264 * t265 * t56 * t101 - t277 * t138 * (-0.125e3 / 0.324e3 * t278 * t101 - 0.15625e5 / 0.19683e5 * t282 * t71 * t101) + t132 * (0.5e1 / 0.972e3 * t291 * t329 - 0.5e1 / 0.972e3 * t330)))
  vsigma_2_ = t6 * t352
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t369 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-0.50e2 / 0.27e2 * t176 * t177 * t56 * t48 - t189 * t82 * (0.250e3 / 0.81e2 * t190 * t48 + 0.125000e6 / 0.19683e5 * t194 * t71 * t48)))
  vtau_0_ = t6 * t369
  t386 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t96 * (-0.50e2 / 0.27e2 * t264 * t265 * t56 * t111 - t277 * t138 * (0.250e3 / 0.81e2 * t278 * t111 + 0.125000e6 / 0.19683e5 * t282 * t71 * t111)))
  vtau_1_ = t6 * t386
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

  ms_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  ms_f0 = lambda p, c: 1 + params_kappa * (1 - params_kappa / (params_kappa + MU_GE * p + c))

  ms_alpha = lambda t, x: (t - x ** 2 / 8) / K_FACTOR_C

  ms_f = lambda x, u, t: ms_f0(X2S ** 2 * x ** 2, 0) + ms_fa(ms_alpha(t, x)) * (ms_f0(X2S ** 2 * x ** 2, params_c) - ms_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ms_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t46 = t41 * t43 - t33 / 0.8e1
  t47 = t46 ** 2
  t48 = t20 ** 2
  t51 = 0.1e1 / t22 / t21
  t54 = 0.1e1 - 0.25e2 / 0.81e2 * t47 * t48 * t51
  t55 = t54 ** 2
  t56 = t55 * t54
  t58 = t21 ** 2
  t59 = 0.1e1 / t58
  t62 = t47 ** 2
  t65 = t58 ** 2
  t66 = 0.1e1 / t65
  t69 = 0.1e1 + 0.250e3 / 0.243e3 * t47 * t46 * t59 + 0.62500e5 / 0.59049e5 * params.b * t62 * t47 * t66
  t70 = 0.1e1 / t69
  t71 = t56 * t70
  t72 = params.kappa + t35 + params.c
  t77 = params.kappa * (0.1e1 - params.kappa / t72) - t40
  t79 = t71 * t77 + t40 + 0.1e1
  t83 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t79)
  t89 = params.kappa ** 2
  t90 = t36 ** 2
  t93 = t89 / t90 * t20
  t97 = 0.1e1 / t30 / t29 / r0
  t99 = t24 * s0 * t27 * t97
  t100 = t93 * t99
  t102 = t55 * t70
  t109 = -0.5e1 / 0.3e1 * t41 * t32 + t28 * t97 / 0.3e1
  t114 = t69 ** 2
  t116 = t56 / t114
  t117 = t47 * t59
  t121 = params.b * t62 * t46
  t128 = t72 ** 2
  t131 = t89 / t128 * t20
  t141 = f.my_piecewise3(t2, 0, -t6 * t17 / t30 * t79 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.10e2 / 0.729e3 * t100 - 0.50e2 / 0.27e2 * t102 * t77 * t46 * t48 * t51 * t109 - t116 * t77 * (0.250e3 / 0.81e2 * t117 * t109 + 0.125000e6 / 0.19683e5 * t121 * t66 * t109) + t71 * (-0.10e2 / 0.729e3 * t131 * t99 + 0.10e2 / 0.729e3 * t100)))
  vrho_0_ = 0.2e1 * r0 * t141 + 0.2e1 * t83
  t145 = t24 * t27 * t32
  t146 = t93 * t145
  t149 = t102 * t77 * t46
  t150 = t48 * t51
  t151 = t27 * t32
  t157 = t66 * t27
  t172 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.5e1 / 0.972e3 * t146 + 0.25e2 / 0.108e3 * t149 * t150 * t151 - t116 * t77 * (-0.125e3 / 0.324e3 * t117 * t151 - 0.15625e5 / 0.19683e5 * t121 * t157 * t32) + t71 * (0.5e1 / 0.972e3 * t131 * t145 - 0.5e1 / 0.972e3 * t146)))
  vsigma_0_ = 0.2e1 * r0 * t172
  vlapl_0_ = 0.0e0
  t174 = t27 * t43
  t190 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-0.50e2 / 0.27e2 * t149 * t150 * t174 - t116 * t77 * (0.250e3 / 0.81e2 * t117 * t174 + 0.125000e6 / 0.19683e5 * t121 * t157 * t43)))
  vtau_0_ = 0.2e1 * r0 * t190
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
  t47 = t42 * t44 - t34 / 0.8e1
  t48 = t47 ** 2
  t49 = t22 ** 2
  t52 = 0.1e1 / t24 / t23
  t55 = 0.1e1 - 0.25e2 / 0.81e2 * t48 * t49 * t52
  t56 = t55 ** 2
  t57 = t56 * t55
  t59 = t23 ** 2
  t60 = 0.1e1 / t59
  t63 = t48 ** 2
  t66 = t59 ** 2
  t67 = 0.1e1 / t66
  t70 = 0.1e1 + 0.250e3 / 0.243e3 * t48 * t47 * t60 + 0.62500e5 / 0.59049e5 * params.b * t63 * t48 * t67
  t71 = 0.1e1 / t70
  t72 = t57 * t71
  t73 = params.kappa + t36 + params.c
  t78 = params.kappa * (0.1e1 - params.kappa / t73) - t41
  t80 = t72 * t78 + t41 + 0.1e1
  t84 = t17 * t18
  t85 = params.kappa ** 2
  t86 = t37 ** 2
  t89 = t85 / t86 * t22
  t90 = t26 * s0
  t91 = t31 * r0
  t93 = 0.1e1 / t19 / t91
  t95 = t90 * t29 * t93
  t96 = t89 * t95
  t98 = t56 * t71
  t99 = t98 * t78
  t100 = t47 * t49
  t105 = -0.5e1 / 0.3e1 * t42 * t33 + t30 * t93 / 0.3e1
  t107 = t100 * t52 * t105
  t110 = t70 ** 2
  t111 = 0.1e1 / t110
  t112 = t57 * t111
  t113 = t48 * t60
  t117 = params.b * t63 * t47
  t121 = 0.250e3 / 0.81e2 * t113 * t105 + 0.125000e6 / 0.19683e5 * t117 * t67 * t105
  t124 = t73 ** 2
  t127 = t85 / t124 * t22
  t130 = -0.10e2 / 0.729e3 * t127 * t95 + 0.10e2 / 0.729e3 * t96
  t132 = -0.10e2 / 0.729e3 * t96 - 0.50e2 / 0.27e2 * t99 * t107 - t112 * t78 * t121 + t72 * t130
  t137 = f.my_piecewise3(t2, 0, -t6 * t21 * t80 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t84 * t132)
  t150 = s0 ** 2
  t152 = t31 ** 2
  t157 = t52 * t150 * t28 / t18 / t152 / t91
  t159 = 0.400e3 / 0.531441e6 * t85 / t86 / t37 * t49 * t157
  t161 = 0.1e1 / t19 / t152
  t163 = t90 * t29 * t161
  t165 = 0.110e3 / 0.2187e4 * t89 * t163
  t171 = t105 ** 2
  t195 = 0.40e2 / 0.9e1 * t42 * t93 - 0.11e2 / 0.9e1 * t30 * t161
  t203 = t121 ** 2
  t235 = -t159 + t165 + 0.10000e5 / 0.729e3 * t55 * t71 * t78 * t48 * t22 / t25 / t59 * t171 + 0.100e3 / 0.27e2 * t56 * t111 * t78 * t47 * t49 * t52 * t105 * t121 - 0.100e3 / 0.27e2 * t98 * t130 * t107 - 0.50e2 / 0.27e2 * t99 * t171 * t49 * t52 - 0.50e2 / 0.27e2 * t99 * t100 * t52 * t195 + 0.2e1 * t57 / t110 / t70 * t78 * t203 - 0.2e1 * t112 * t130 * t121 - t112 * t78 * (0.500e3 / 0.81e2 * t47 * t60 * t171 + 0.250e3 / 0.81e2 * t113 * t195 + 0.625000e6 / 0.19683e5 * params.b * t63 * t67 * t171 + 0.125000e6 / 0.19683e5 * t117 * t67 * t195) + t72 * (-0.400e3 / 0.531441e6 * t85 / t124 / t73 * t49 * t157 + 0.110e3 / 0.2187e4 * t127 * t163 + t159 - t165)
  t240 = f.my_piecewise3(t2, 0, t6 * t17 * t44 * t80 / 0.12e2 - t6 * t21 * t132 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t84 * t235)
  v2rho2_0_ = 0.2e1 * r0 * t240 + 0.4e1 * t137
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
  t46 = t43 * t21 - t35 / 0.8e1
  t47 = t46 ** 2
  t48 = t23 ** 2
  t51 = 0.1e1 / t25 / t24
  t54 = 0.1e1 - 0.25e2 / 0.81e2 * t47 * t48 * t51
  t55 = t54 ** 2
  t56 = t55 * t54
  t57 = t47 * t46
  t58 = t24 ** 2
  t59 = 0.1e1 / t58
  t62 = t47 ** 2
  t65 = t58 ** 2
  t66 = 0.1e1 / t65
  t69 = 0.1e1 + 0.250e3 / 0.243e3 * t57 * t59 + 0.62500e5 / 0.59049e5 * params.b * t62 * t47 * t66
  t70 = 0.1e1 / t69
  t71 = t56 * t70
  t72 = params.kappa + t37 + params.c
  t77 = params.kappa * (0.1e1 - params.kappa / t72) - t42
  t79 = t71 * t77 + t42 + 0.1e1
  t84 = t17 / t19
  t85 = params.kappa ** 2
  t86 = t38 ** 2
  t89 = t85 / t86 * t23
  t90 = t27 * s0
  t91 = t32 * r0
  t93 = 0.1e1 / t19 / t91
  t95 = t90 * t30 * t93
  t96 = t89 * t95
  t98 = t55 * t70
  t99 = t98 * t77
  t100 = t46 * t48
  t105 = -0.5e1 / 0.3e1 * t43 * t34 + t31 * t93 / 0.3e1
  t107 = t100 * t51 * t105
  t110 = t69 ** 2
  t111 = 0.1e1 / t110
  t112 = t56 * t111
  t113 = t47 * t59
  t117 = params.b * t62 * t46
  t118 = t66 * t105
  t121 = 0.250e3 / 0.81e2 * t113 * t105 + 0.125000e6 / 0.19683e5 * t117 * t118
  t122 = t77 * t121
  t124 = t72 ** 2
  t127 = t85 / t124 * t23
  t130 = -0.10e2 / 0.729e3 * t127 * t95 + 0.10e2 / 0.729e3 * t96
  t132 = -0.10e2 / 0.729e3 * t96 - 0.50e2 / 0.27e2 * t99 * t107 - t112 * t122 + t71 * t130
  t136 = t17 * t18
  t140 = t85 / t86 / t38 * t48
  t141 = s0 ** 2
  t142 = t51 * t141
  t143 = t32 ** 2
  t148 = t142 * t29 / t18 / t143 / t91
  t150 = 0.400e3 / 0.531441e6 * t140 * t148
  t152 = 0.1e1 / t19 / t143
  t154 = t90 * t30 * t152
  t156 = 0.110e3 / 0.2187e4 * t89 * t154
  t157 = t54 * t70
  t158 = t157 * t77
  t161 = 0.1e1 / t26 / t58
  t162 = t105 ** 2
  t164 = t47 * t23 * t161 * t162
  t167 = t55 * t111
  t168 = t77 * t46
  t169 = t167 * t168
  t170 = t48 * t51
  t172 = t170 * t105 * t121
  t175 = t98 * t130
  t178 = t162 * t48
  t179 = t178 * t51
  t186 = 0.40e2 / 0.9e1 * t43 * t93 - 0.11e2 / 0.9e1 * t31 * t152
  t187 = t51 * t186
  t188 = t100 * t187
  t192 = 0.1e1 / t110 / t69
  t193 = t56 * t192
  t194 = t121 ** 2
  t201 = t46 * t59
  t206 = params.b * t62
  t213 = 0.500e3 / 0.81e2 * t201 * t162 + 0.250e3 / 0.81e2 * t113 * t186 + 0.625000e6 / 0.19683e5 * t206 * t66 * t162 + 0.125000e6 / 0.19683e5 * t117 * t66 * t186
  t219 = t85 / t124 / t72 * t48
  t224 = -0.400e3 / 0.531441e6 * t219 * t148 + 0.110e3 / 0.2187e4 * t127 * t154 + t150 - t156
  t226 = -t150 + t156 + 0.10000e5 / 0.729e3 * t158 * t164 + 0.100e3 / 0.27e2 * t169 * t172 - 0.100e3 / 0.27e2 * t175 * t107 - 0.50e2 / 0.27e2 * t99 * t179 - 0.50e2 / 0.27e2 * t99 * t188 + 0.2e1 * t193 * t77 * t194 - 0.2e1 * t112 * t130 * t121 - t112 * t77 * t213 + t71 * t224
  t231 = f.my_piecewise3(t2, 0, t6 * t22 * t79 / 0.12e2 - t6 * t84 * t132 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t136 * t226)
  t243 = t124 ** 2
  t248 = t143 ** 2
  t251 = t59 * t141 * s0 / t248 / t91
  t257 = t142 * t29 / t18 / t248
  t262 = 0.1e1 / t19 / t143 / r0
  t264 = t90 * t30 * t262
  t267 = t86 ** 2
  t271 = 0.16000e5 / 0.43046721e8 * t85 / t267 * t251
  t273 = 0.4400e4 / 0.531441e6 * t140 * t257
  t275 = 0.1540e4 / 0.6561e4 * t89 * t264
  t279 = t162 * t105
  t298 = t77 * t47
  t300 = t23 * t161
  t306 = t105 * t186
  t318 = t110 ** 2
  t328 = t71 * (-0.16000e5 / 0.43046721e8 * t85 / t243 * t251 + 0.4400e4 / 0.531441e6 * t219 * t257 - 0.1540e4 / 0.6561e4 * t127 * t264 + t271 - t273 + t275) - 0.1000000e7 / 0.19683e5 * t57 * t66 * t279 * t70 * t77 + 0.6e1 * t193 * t122 * t213 - t271 + 0.50e2 / 0.9e1 * t169 * t170 * t105 * t213 - 0.100e3 / 0.9e1 * t55 * t192 * t168 * t170 * t105 * t194 - 0.10000e5 / 0.243e3 * t54 * t111 * t298 * t300 * t162 * t121 + 0.10000e5 / 0.243e3 * t157 * t298 * t300 * t306 + 0.100e3 / 0.9e1 * t167 * t130 * t46 * t172 + 0.50e2 / 0.9e1 * t169 * t170 * t186 * t121 - 0.6e1 * t56 / t318 * t77 * t194 * t121 + 0.6e1 * t193 * t130 * t194
  t340 = -0.440e3 / 0.27e2 * t43 * t152 + 0.154e3 / 0.27e2 * t31 * t262
  t387 = -0.3e1 * t112 * t224 * t121 - t112 * t77 * (0.500e3 / 0.81e2 * t279 * t59 + 0.500e3 / 0.27e2 * t201 * t306 + 0.250e3 / 0.81e2 * t113 * t340 + 0.2500000e7 / 0.19683e5 * params.b * t57 * t66 * t279 + 0.625000e6 / 0.6561e4 * t206 * t118 * t186 + 0.125000e6 / 0.19683e5 * t117 * t66 * t340) - 0.3e1 * t112 * t130 * t213 - 0.50e2 / 0.9e1 * t98 * t224 * t107 - 0.50e2 / 0.9e1 * t175 * t188 - 0.50e2 / 0.9e1 * t99 * t105 * t48 * t187 - 0.50e2 / 0.27e2 * t99 * t100 * t51 * t340 + 0.10000e5 / 0.243e3 * t158 * t46 * t23 * t161 * t279 + t273 - t275 + 0.50e2 / 0.9e1 * t167 * t77 * t178 * t51 * t121 + 0.10000e5 / 0.243e3 * t157 * t130 * t164 - 0.50e2 / 0.9e1 * t175 * t179
  t393 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t34 * t79 + t6 * t22 * t132 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t84 * t226 - 0.3e1 / 0.8e1 * t6 * t136 * (t328 + t387))
  v3rho3_0_ = 0.2e1 * r0 * t393 + 0.6e1 * t231

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
  t46 = t41 * t43 - t33 / 0.8e1
  t47 = t46 ** 2
  t48 = t24 ** 2
  t51 = 0.1e1 / t26 / t25
  t54 = 0.1e1 - 0.25e2 / 0.81e2 * t47 * t48 * t51
  t55 = t54 ** 2
  t56 = t55 * t54
  t57 = t47 * t46
  t58 = t25 ** 2
  t59 = 0.1e1 / t58
  t62 = t47 ** 2
  t65 = t58 ** 2
  t66 = 0.1e1 / t65
  t69 = 0.1e1 + 0.250e3 / 0.243e3 * t57 * t59 + 0.62500e5 / 0.59049e5 * params.b * t62 * t47 * t66
  t70 = 0.1e1 / t69
  t71 = t56 * t70
  t72 = params.kappa + t35 + params.c
  t77 = params.kappa * (0.1e1 - params.kappa / t72) - t40
  t79 = t71 * t77 + t40 + 0.1e1
  t83 = t17 * t43
  t84 = params.kappa ** 2
  t85 = t36 ** 2
  t88 = t84 / t85 * t24
  t89 = t28 * s0
  t90 = t18 * r0
  t92 = 0.1e1 / t20 / t90
  t94 = t89 * t31 * t92
  t95 = t88 * t94
  t97 = t55 * t70
  t98 = t97 * t77
  t99 = t46 * t48
  t104 = -0.5e1 / 0.3e1 * t41 * t22 + t32 * t92 / 0.3e1
  t106 = t99 * t51 * t104
  t109 = t69 ** 2
  t110 = 0.1e1 / t109
  t111 = t56 * t110
  t112 = t47 * t59
  t116 = params.b * t62 * t46
  t117 = t66 * t104
  t120 = 0.250e3 / 0.81e2 * t112 * t104 + 0.125000e6 / 0.19683e5 * t116 * t117
  t121 = t77 * t120
  t123 = t72 ** 2
  t126 = t84 / t123 * t24
  t129 = -0.10e2 / 0.729e3 * t126 * t94 + 0.10e2 / 0.729e3 * t95
  t131 = -0.10e2 / 0.729e3 * t95 - 0.50e2 / 0.27e2 * t98 * t106 - t111 * t121 + t71 * t129
  t136 = t17 / t20
  t140 = t84 / t85 / t36 * t48
  t141 = s0 ** 2
  t142 = t51 * t141
  t143 = t18 ** 2
  t148 = t142 * t30 / t19 / t143 / t90
  t150 = 0.400e3 / 0.531441e6 * t140 * t148
  t152 = 0.1e1 / t20 / t143
  t154 = t89 * t31 * t152
  t156 = 0.110e3 / 0.2187e4 * t88 * t154
  t157 = t54 * t70
  t158 = t157 * t77
  t159 = t47 * t24
  t161 = 0.1e1 / t27 / t58
  t162 = t104 ** 2
  t164 = t159 * t161 * t162
  t167 = t55 * t110
  t168 = t77 * t46
  t169 = t167 * t168
  t170 = t48 * t51
  t172 = t170 * t104 * t120
  t175 = t97 * t129
  t178 = t162 * t48
  t179 = t178 * t51
  t186 = 0.40e2 / 0.9e1 * t41 * t92 - 0.11e2 / 0.9e1 * t32 * t152
  t187 = t51 * t186
  t188 = t99 * t187
  t192 = 0.1e1 / t109 / t69
  t193 = t56 * t192
  t194 = t120 ** 2
  t195 = t77 * t194
  t201 = t46 * t59
  t206 = params.b * t62
  t207 = t66 * t162
  t213 = 0.500e3 / 0.81e2 * t201 * t162 + 0.250e3 / 0.81e2 * t112 * t186 + 0.625000e6 / 0.19683e5 * t206 * t207 + 0.125000e6 / 0.19683e5 * t116 * t66 * t186
  t219 = t84 / t123 / t72 * t48
  t224 = -0.400e3 / 0.531441e6 * t219 * t148 + 0.110e3 / 0.2187e4 * t126 * t154 + t150 - t156
  t226 = -t150 + t156 + 0.10000e5 / 0.729e3 * t158 * t164 + 0.100e3 / 0.27e2 * t169 * t172 - 0.100e3 / 0.27e2 * t175 * t106 - 0.50e2 / 0.27e2 * t98 * t179 - 0.50e2 / 0.27e2 * t98 * t188 + 0.2e1 * t193 * t195 - 0.2e1 * t111 * t129 * t120 - t111 * t77 * t213 + t71 * t224
  t230 = t17 * t19
  t231 = t85 ** 2
  t233 = t84 / t231
  t235 = t59 * t141 * s0
  t236 = t143 ** 2
  t239 = t235 / t236 / t90
  t241 = 0.16000e5 / 0.43046721e8 * t233 * t239
  t242 = t57 * t66
  t243 = t162 * t104
  t244 = t243 * t70
  t251 = t123 ** 2
  t253 = t84 / t251
  t259 = t142 * t30 / t19 / t236
  t264 = 0.1e1 / t20 / t143 / r0
  t266 = t89 * t31 * t264
  t270 = 0.4400e4 / 0.531441e6 * t140 * t259
  t272 = 0.1540e4 / 0.6561e4 * t88 * t266
  t273 = -0.16000e5 / 0.43046721e8 * t253 * t239 + 0.4400e4 / 0.531441e6 * t219 * t259 - 0.1540e4 / 0.6561e4 * t126 * t266 + t241 - t270 + t272
  t275 = t55 * t192
  t276 = t275 * t168
  t278 = t170 * t104 * t194
  t281 = t186 * t120
  t282 = t170 * t281
  t285 = t104 * t213
  t286 = t170 * t285
  t289 = t54 * t110
  t290 = t77 * t47
  t291 = t289 * t290
  t292 = t24 * t161
  t294 = t292 * t162 * t120
  t297 = t157 * t290
  t298 = t104 * t186
  t299 = t292 * t298
  t302 = t129 * t46
  t303 = t167 * t302
  t306 = t97 * t224
  t309 = -t241 - 0.1000000e7 / 0.19683e5 * t242 * t244 * t77 + 0.6e1 * t193 * t121 * t213 + t71 * t273 - 0.100e3 / 0.9e1 * t276 * t278 + 0.50e2 / 0.9e1 * t169 * t282 + 0.50e2 / 0.9e1 * t169 * t286 - 0.10000e5 / 0.243e3 * t291 * t294 + 0.10000e5 / 0.243e3 * t297 * t299 + 0.100e3 / 0.9e1 * t303 * t172 - 0.50e2 / 0.9e1 * t306 * t106 + t270
  t312 = t104 * t48
  t313 = t312 * t187
  t320 = -0.440e3 / 0.27e2 * t41 * t152 + 0.154e3 / 0.27e2 * t32 * t264
  t321 = t51 * t320
  t322 = t99 * t321
  t325 = t167 * t77
  t327 = t178 * t51 * t120
  t332 = t46 * t24 * t161 * t243
  t335 = t157 * t129
  t338 = t129 * t213
  t347 = params.b * t57
  t357 = 0.500e3 / 0.81e2 * t243 * t59 + 0.500e3 / 0.27e2 * t201 * t298 + 0.250e3 / 0.81e2 * t112 * t320 + 0.2500000e7 / 0.19683e5 * t347 * t66 * t243 + 0.625000e6 / 0.6561e4 * t206 * t117 * t186 + 0.125000e6 / 0.19683e5 * t116 * t66 * t320
  t358 = t77 * t357
  t360 = t109 ** 2
  t361 = 0.1e1 / t360
  t362 = t56 * t361
  t363 = t194 * t120
  t364 = t77 * t363
  t375 = -t272 - 0.50e2 / 0.9e1 * t175 * t188 - 0.50e2 / 0.9e1 * t98 * t313 - 0.50e2 / 0.27e2 * t98 * t322 + 0.50e2 / 0.9e1 * t325 * t327 + 0.10000e5 / 0.243e3 * t158 * t332 + 0.10000e5 / 0.243e3 * t335 * t164 - 0.3e1 * t111 * t338 - t111 * t358 - 0.6e1 * t362 * t364 + 0.6e1 * t193 * t129 * t194 - 0.3e1 * t111 * t224 * t120 - 0.50e2 / 0.9e1 * t175 * t179
  t376 = t309 + t375
  t381 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t79 + t6 * t83 * t131 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t136 * t226 - 0.3e1 / 0.8e1 * t6 * t230 * t376)
  t399 = t162 ** 2
  t406 = t186 ** 2
  t436 = t194 ** 2
  t440 = t213 ** 2
  t449 = t104 * t320
  t454 = t143 * t18
  t456 = 0.1e1 / t20 / t454
  t459 = 0.6160e4 / 0.81e2 * t41 * t264 - 0.2618e4 / 0.81e2 * t32 * t456
  t481 = 0.8e1 * t193 * t358 * t120 + 0.10000e5 / 0.243e3 * t158 * t399 * t24 * t161 - 0.100e3 / 0.9e1 * t306 * t179 - 0.50e2 / 0.9e1 * t98 * t406 * t48 * t51 + 0.4000000e7 / 0.19683e5 * t242 * t243 * t110 * t77 * t120 - 0.2000000e7 / 0.6561e4 * t242 * t162 * t70 * t77 * t186 - 0.6e1 * t111 * t224 * t213 - 0.4e1 * t111 * t129 * t357 + 0.12e2 * t193 * t224 * t194 - 0.4e1 * t111 * t273 * t120 + 0.24e2 * t56 / t360 / t69 * t77 * t436 + 0.6e1 * t193 * t77 * t440 - t111 * t77 * (0.1000e4 / 0.27e2 * t162 * t59 * t186 + 0.500e3 / 0.27e2 * t201 * t406 + 0.2000e4 / 0.81e2 * t201 * t449 + 0.250e3 / 0.81e2 * t112 * t459 + 0.2500000e7 / 0.6561e4 * params.b * t47 * t66 * t399 + 0.5000000e7 / 0.6561e4 * t347 * t207 * t186 + 0.625000e6 / 0.6561e4 * t206 * t66 * t406 + 0.2500000e7 / 0.19683e5 * t206 * t117 * t320 + 0.125000e6 / 0.19683e5 * t116 * t66 * t459)
  t488 = t141 ** 2
  t489 = t59 * t488
  t496 = 0.1e1 / t20 / t236 / t454 * t24 * t28 * t31
  t501 = t235 / t236 / t143
  t508 = t142 * t30 / t19 / t236 / r0
  t512 = t89 * t31 * t456
  t520 = 0.640000e6 / 0.31381059609e11 * t84 / t231 / t36 * t489 * t496
  t522 = 0.352000e6 / 0.43046721e8 * t233 * t501
  t524 = 0.391600e6 / 0.4782969e7 * t140 * t508
  t526 = 0.26180e5 / 0.19683e5 * t88 * t512
  t543 = t129 * t47
  t568 = -0.24e2 * t362 * t129 * t363 + t71 * (-0.640000e6 / 0.31381059609e11 * t84 / t251 / t72 * t489 * t496 + 0.352000e6 / 0.43046721e8 * t253 * t501 - 0.391600e6 / 0.4782969e7 * t219 * t508 + 0.26180e5 / 0.19683e5 * t126 * t512 + t520 - t522 + t524 - t526) - 0.36e2 * t362 * t195 * t213 - 0.2000000e7 / 0.6561e4 * t47 * t66 * t399 * t70 * t77 - 0.4000000e7 / 0.19683e5 * t242 * t244 * t129 + 0.24e2 * t193 * t338 * t120 + t522 + 0.40000e5 / 0.243e3 * t157 * t543 * t299 + 0.40000e5 / 0.729e3 * t297 * t292 * t449 + 0.200e3 / 0.9e1 * t167 * t224 * t46 * t172 + 0.200e3 / 0.9e1 * t303 * t282 + 0.200e3 / 0.9e1 * t167 * t77 * t104 * t282 + 0.200e3 / 0.27e2 * t169 * t170 * t320 * t120 + 0.100e3 / 0.9e1 * t169 * t170 * t186 * t213
  t613 = 0.200e3 / 0.9e1 * t303 * t286 + 0.200e3 / 0.27e2 * t169 * t170 * t104 * t357 - 0.400e3 / 0.9e1 * t275 * t302 * t278 - 0.200e3 / 0.9e1 * t276 * t170 * t186 * t194 + 0.40000e5 / 0.243e3 * t54 * t192 * t290 * t292 * t162 * t194 - 0.40000e5 / 0.243e3 * t289 * t168 * t292 * t243 * t120 + 0.20000e5 / 0.81e2 * t157 * t168 * t292 * t162 * t186 + 0.400e3 / 0.9e1 * t55 * t361 * t364 * t106 - 0.20000e5 / 0.243e3 * t291 * t292 * t162 * t213 - 0.40000e5 / 0.243e3 * t289 * t543 * t294 - t520 - 0.200e3 / 0.27e2 * t97 * t273 * t106 - t524
  t656 = t526 - 0.100e3 / 0.9e1 * t306 * t188 - 0.200e3 / 0.9e1 * t175 * t313 - 0.200e3 / 0.27e2 * t175 * t322 - 0.200e3 / 0.27e2 * t98 * t312 * t321 + 0.200e3 / 0.9e1 * t167 * t129 * t327 + 0.100e3 / 0.9e1 * t325 * t178 * t51 * t213 - 0.50e2 / 0.27e2 * t98 * t99 * t51 * t459 + 0.40000e5 / 0.243e3 * t335 * t332 + 0.20000e5 / 0.243e3 * t157 * t224 * t164 - 0.200e3 / 0.9e1 * t275 * t77 * t178 * t51 * t194 + 0.10000e5 / 0.243e3 * t158 * t159 * t161 * t406 - 0.40000e5 / 0.243e3 * t291 * t292 * t281 * t104 - 0.400e3 / 0.9e1 * t276 * t170 * t285 * t120
  t663 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t92 * t79 - 0.5e1 / 0.9e1 * t6 * t23 * t131 + t6 * t83 * t226 / 0.2e1 - t6 * t136 * t376 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t230 * (t481 + t568 + t613 + t656))
  v4rho4_0_ = 0.2e1 * r0 * t663 + 0.8e1 * t381

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
  t55 = tau0 / t40 / r0 - t43 / 0.8e1
  t56 = t55 ** 2
  t57 = t32 ** 2
  t60 = 0.1e1 / t34 / t33
  t63 = 0.1e1 - 0.25e2 / 0.81e2 * t56 * t57 * t60
  t64 = t63 ** 2
  t65 = t64 * t63
  t67 = t33 ** 2
  t68 = 0.1e1 / t67
  t71 = t56 ** 2
  t74 = t67 ** 2
  t75 = 0.1e1 / t74
  t78 = 0.1e1 + 0.250e3 / 0.243e3 * t56 * t55 * t68 + 0.62500e5 / 0.59049e5 * params.b * t71 * t56 * t75
  t79 = 0.1e1 / t78
  t80 = t65 * t79
  t81 = params.kappa + t45 + params.c
  t86 = params.kappa * (0.1e1 - params.kappa / t81) - t50
  t88 = t80 * t86 + t50 + 0.1e1
  t92 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t93 = t92 * f.p.zeta_threshold
  t95 = f.my_piecewise3(t20, t93, t21 * t19)
  t96 = t30 ** 2
  t97 = 0.1e1 / t96
  t98 = t95 * t97
  t101 = t5 * t98 * t88 / 0.8e1
  t102 = t95 * t30
  t103 = params.kappa ** 2
  t104 = t46 ** 2
  t107 = t103 / t104 * t32
  t108 = t36 * s0
  t109 = t38 * r0
  t111 = 0.1e1 / t40 / t109
  t112 = t108 * t111
  t113 = t107 * t112
  t115 = t64 * t79
  t116 = t115 * t86
  t117 = t55 * t57
  t122 = -0.5e1 / 0.3e1 * tau0 * t42 + s0 * t111 / 0.3e1
  t124 = t117 * t60 * t122
  t127 = t78 ** 2
  t128 = 0.1e1 / t127
  t129 = t65 * t128
  t130 = t56 * t68
  t134 = params.b * t71 * t55
  t138 = 0.250e3 / 0.81e2 * t130 * t122 + 0.125000e6 / 0.19683e5 * t134 * t75 * t122
  t141 = t81 ** 2
  t144 = t103 / t141 * t32
  t147 = -0.10e2 / 0.729e3 * t144 * t112 + 0.10e2 / 0.729e3 * t113
  t149 = -0.10e2 / 0.729e3 * t113 - 0.50e2 / 0.27e2 * t116 * t124 - t129 * t86 * t138 + t80 * t147
  t154 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t88 - t101 - 0.3e1 / 0.8e1 * t5 * t102 * t149)
  t156 = r1 <= f.p.dens_threshold
  t157 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t158 = 0.1e1 + t157
  t159 = t158 <= f.p.zeta_threshold
  t160 = t158 ** (0.1e1 / 0.3e1)
  t162 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t165 = f.my_piecewise3(t159, 0, 0.4e1 / 0.3e1 * t160 * t162)
  t166 = t165 * t30
  t167 = r1 ** 2
  t168 = r1 ** (0.1e1 / 0.3e1)
  t169 = t168 ** 2
  t171 = 0.1e1 / t169 / t167
  t172 = s2 * t171
  t174 = 0.5e1 / 0.972e3 * t37 * t172
  t175 = params.kappa + t174
  t179 = params.kappa * (0.1e1 - params.kappa / t175)
  t184 = tau1 / t169 / r1 - t172 / 0.8e1
  t185 = t184 ** 2
  t189 = 0.1e1 - 0.25e2 / 0.81e2 * t185 * t57 * t60
  t190 = t189 ** 2
  t191 = t190 * t189
  t195 = t185 ** 2
  t200 = 0.1e1 + 0.250e3 / 0.243e3 * t185 * t184 * t68 + 0.62500e5 / 0.59049e5 * params.b * t195 * t185 * t75
  t201 = 0.1e1 / t200
  t202 = t191 * t201
  t203 = params.kappa + t174 + params.c
  t208 = params.kappa * (0.1e1 - params.kappa / t203) - t179
  t210 = t202 * t208 + t179 + 0.1e1
  t215 = f.my_piecewise3(t159, t93, t160 * t158)
  t216 = t215 * t97
  t219 = t5 * t216 * t210 / 0.8e1
  t221 = f.my_piecewise3(t156, 0, -0.3e1 / 0.8e1 * t5 * t166 * t210 - t219)
  t223 = t21 ** 2
  t224 = 0.1e1 / t223
  t225 = t26 ** 2
  t230 = t16 / t22 / t6
  t232 = -0.2e1 * t23 + 0.2e1 * t230
  t233 = f.my_piecewise5(t10, 0, t14, 0, t232)
  t237 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t224 * t225 + 0.4e1 / 0.3e1 * t21 * t233)
  t244 = t5 * t29 * t97 * t88
  t250 = 0.1e1 / t96 / t6
  t254 = t5 * t95 * t250 * t88 / 0.12e2
  t256 = t5 * t98 * t149
  t262 = s0 ** 2
  t264 = t38 ** 2
  t268 = t60 * t262 / t39 / t264 / t109
  t270 = 0.200e3 / 0.531441e6 * t103 / t104 / t46 * t57 * t268
  t272 = 0.1e1 / t40 / t264
  t273 = t108 * t272
  t275 = 0.110e3 / 0.2187e4 * t107 * t273
  t280 = 0.1e1 / t35 / t67
  t281 = t122 ** 2
  t289 = t57 * t60
  t305 = 0.40e2 / 0.9e1 * tau0 * t111 - 0.11e2 / 0.9e1 * s0 * t272
  t313 = t138 ** 2
  t345 = -t270 + t275 + 0.10000e5 / 0.729e3 * t63 * t79 * t86 * t56 * t32 * t280 * t281 + 0.100e3 / 0.27e2 * t64 * t128 * t86 * t55 * t289 * t122 * t138 - 0.100e3 / 0.27e2 * t115 * t147 * t124 - 0.50e2 / 0.27e2 * t116 * t281 * t57 * t60 - 0.50e2 / 0.27e2 * t116 * t117 * t60 * t305 + 0.2e1 * t65 / t127 / t78 * t86 * t313 - 0.2e1 * t129 * t147 * t138 - t129 * t86 * (0.500e3 / 0.81e2 * t55 * t68 * t281 + 0.250e3 / 0.81e2 * t130 * t305 + 0.625000e6 / 0.19683e5 * params.b * t71 * t75 * t281 + 0.125000e6 / 0.19683e5 * t134 * t75 * t305) + t80 * (-0.200e3 / 0.531441e6 * t103 / t141 / t81 * t57 * t268 + 0.110e3 / 0.2187e4 * t144 * t273 + t270 - t275)
  t350 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t237 * t30 * t88 - t244 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t149 + t254 - t256 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t102 * t345)
  t351 = t160 ** 2
  t352 = 0.1e1 / t351
  t353 = t162 ** 2
  t357 = f.my_piecewise5(t14, 0, t10, 0, -t232)
  t361 = f.my_piecewise3(t159, 0, 0.4e1 / 0.9e1 * t352 * t353 + 0.4e1 / 0.3e1 * t160 * t357)
  t368 = t5 * t165 * t97 * t210
  t373 = t5 * t215 * t250 * t210 / 0.12e2
  t375 = f.my_piecewise3(t156, 0, -0.3e1 / 0.8e1 * t5 * t361 * t30 * t210 - t368 / 0.4e1 + t373)
  d11 = 0.2e1 * t154 + 0.2e1 * t221 + t6 * (t350 + t375)
  t378 = -t7 - t24
  t379 = f.my_piecewise5(t10, 0, t14, 0, t378)
  t382 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t379)
  t383 = t382 * t30
  t388 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t383 * t88 - t101)
  t390 = f.my_piecewise5(t14, 0, t10, 0, -t378)
  t393 = f.my_piecewise3(t159, 0, 0.4e1 / 0.3e1 * t160 * t390)
  t394 = t393 * t30
  t398 = t215 * t30
  t399 = t175 ** 2
  t402 = t103 / t399 * t32
  t403 = t36 * s2
  t404 = t167 * r1
  t406 = 0.1e1 / t169 / t404
  t407 = t403 * t406
  t408 = t402 * t407
  t410 = t190 * t201
  t411 = t410 * t208
  t412 = t184 * t57
  t417 = -0.5e1 / 0.3e1 * tau1 * t171 + s2 * t406 / 0.3e1
  t419 = t412 * t60 * t417
  t422 = t200 ** 2
  t423 = 0.1e1 / t422
  t424 = t191 * t423
  t425 = t185 * t68
  t429 = params.b * t195 * t184
  t433 = 0.250e3 / 0.81e2 * t425 * t417 + 0.125000e6 / 0.19683e5 * t429 * t75 * t417
  t436 = t203 ** 2
  t439 = t103 / t436 * t32
  t442 = -0.10e2 / 0.729e3 * t439 * t407 + 0.10e2 / 0.729e3 * t408
  t444 = -0.10e2 / 0.729e3 * t408 - 0.50e2 / 0.27e2 * t411 * t419 - t424 * t208 * t433 + t202 * t442
  t449 = f.my_piecewise3(t156, 0, -0.3e1 / 0.8e1 * t5 * t394 * t210 - t219 - 0.3e1 / 0.8e1 * t5 * t398 * t444)
  t453 = 0.2e1 * t230
  t454 = f.my_piecewise5(t10, 0, t14, 0, t453)
  t458 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t224 * t379 * t26 + 0.4e1 / 0.3e1 * t21 * t454)
  t465 = t5 * t382 * t97 * t88
  t473 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t458 * t30 * t88 - t465 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t383 * t149 - t244 / 0.8e1 + t254 - t256 / 0.8e1)
  t477 = f.my_piecewise5(t14, 0, t10, 0, -t453)
  t481 = f.my_piecewise3(t159, 0, 0.4e1 / 0.9e1 * t352 * t390 * t162 + 0.4e1 / 0.3e1 * t160 * t477)
  t488 = t5 * t393 * t97 * t210
  t495 = t5 * t216 * t444
  t498 = f.my_piecewise3(t156, 0, -0.3e1 / 0.8e1 * t5 * t481 * t30 * t210 - t488 / 0.8e1 - t368 / 0.8e1 + t373 - 0.3e1 / 0.8e1 * t5 * t166 * t444 - t495 / 0.8e1)
  d12 = t154 + t221 + t388 + t449 + t6 * (t473 + t498)
  t503 = t379 ** 2
  t507 = 0.2e1 * t23 + 0.2e1 * t230
  t508 = f.my_piecewise5(t10, 0, t14, 0, t507)
  t512 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t224 * t503 + 0.4e1 / 0.3e1 * t21 * t508)
  t519 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t512 * t30 * t88 - t465 / 0.4e1 + t254)
  t520 = t390 ** 2
  t524 = f.my_piecewise5(t14, 0, t10, 0, -t507)
  t528 = f.my_piecewise3(t159, 0, 0.4e1 / 0.9e1 * t352 * t520 + 0.4e1 / 0.3e1 * t160 * t524)
  t542 = s2 ** 2
  t544 = t167 ** 2
  t548 = t60 * t542 / t168 / t544 / t404
  t550 = 0.200e3 / 0.531441e6 * t103 / t399 / t175 * t57 * t548
  t552 = 0.1e1 / t169 / t544
  t553 = t403 * t552
  t555 = 0.110e3 / 0.2187e4 * t402 * t553
  t559 = t417 ** 2
  t582 = 0.40e2 / 0.9e1 * tau1 * t406 - 0.11e2 / 0.9e1 * s2 * t552
  t590 = t433 ** 2
  t622 = -t550 + t555 + 0.10000e5 / 0.729e3 * t189 * t201 * t208 * t185 * t32 * t280 * t559 + 0.100e3 / 0.27e2 * t190 * t423 * t208 * t184 * t289 * t417 * t433 - 0.100e3 / 0.27e2 * t410 * t442 * t419 - 0.50e2 / 0.27e2 * t411 * t559 * t57 * t60 - 0.50e2 / 0.27e2 * t411 * t412 * t60 * t582 + 0.2e1 * t191 / t422 / t200 * t208 * t590 - 0.2e1 * t424 * t442 * t433 - t424 * t208 * (0.500e3 / 0.81e2 * t184 * t68 * t559 + 0.250e3 / 0.81e2 * t425 * t582 + 0.625000e6 / 0.19683e5 * params.b * t195 * t75 * t559 + 0.125000e6 / 0.19683e5 * t429 * t75 * t582) + t202 * (-0.200e3 / 0.531441e6 * t103 / t436 / t203 * t57 * t548 + 0.110e3 / 0.2187e4 * t439 * t553 + t550 - t555)
  t627 = f.my_piecewise3(t156, 0, -0.3e1 / 0.8e1 * t5 * t528 * t30 * t210 - t488 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t394 * t444 + t373 - t495 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t398 * t622)
  d22 = 0.2e1 * t388 + 0.2e1 * t449 + t6 * (t519 + t627)
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
  t67 = tau0 / t52 / r0 - t55 / 0.8e1
  t68 = t67 ** 2
  t69 = t44 ** 2
  t72 = 0.1e1 / t46 / t45
  t75 = 0.1e1 - 0.25e2 / 0.81e2 * t68 * t69 * t72
  t76 = t75 ** 2
  t77 = t76 * t75
  t78 = t68 * t67
  t79 = t45 ** 2
  t80 = 0.1e1 / t79
  t83 = t68 ** 2
  t86 = t79 ** 2
  t87 = 0.1e1 / t86
  t90 = 0.1e1 + 0.250e3 / 0.243e3 * t78 * t80 + 0.62500e5 / 0.59049e5 * params.b * t83 * t68 * t87
  t91 = 0.1e1 / t90
  t92 = t77 * t91
  t93 = params.kappa + t57 + params.c
  t98 = params.kappa * (0.1e1 - params.kappa / t93) - t62
  t100 = t92 * t98 + t62 + 0.1e1
  t106 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t107 = t42 ** 2
  t108 = 0.1e1 / t107
  t109 = t106 * t108
  t113 = t106 * t42
  t114 = params.kappa ** 2
  t115 = t58 ** 2
  t118 = t114 / t115 * t44
  t119 = t48 * s0
  t120 = t50 * r0
  t122 = 0.1e1 / t52 / t120
  t123 = t119 * t122
  t124 = t118 * t123
  t126 = t76 * t91
  t127 = t126 * t98
  t128 = t67 * t69
  t133 = -0.5e1 / 0.3e1 * tau0 * t54 + s0 * t122 / 0.3e1
  t135 = t128 * t72 * t133
  t138 = t90 ** 2
  t139 = 0.1e1 / t138
  t140 = t77 * t139
  t141 = t68 * t80
  t145 = params.b * t83 * t67
  t146 = t87 * t133
  t149 = 0.250e3 / 0.81e2 * t141 * t133 + 0.125000e6 / 0.19683e5 * t145 * t146
  t150 = t98 * t149
  t152 = t93 ** 2
  t155 = t114 / t152 * t44
  t158 = -0.10e2 / 0.729e3 * t155 * t123 + 0.10e2 / 0.729e3 * t124
  t160 = -0.10e2 / 0.729e3 * t124 - 0.50e2 / 0.27e2 * t127 * t135 - t140 * t150 + t92 * t158
  t164 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t165 = t164 * f.p.zeta_threshold
  t167 = f.my_piecewise3(t20, t165, t21 * t19)
  t169 = 0.1e1 / t107 / t6
  t170 = t167 * t169
  t174 = t167 * t108
  t178 = t167 * t42
  t182 = t114 / t115 / t58 * t69
  t183 = s0 ** 2
  t184 = t72 * t183
  t185 = t50 ** 2
  t189 = t184 / t51 / t185 / t120
  t191 = 0.200e3 / 0.531441e6 * t182 * t189
  t193 = 0.1e1 / t52 / t185
  t194 = t119 * t193
  t196 = 0.110e3 / 0.2187e4 * t118 * t194
  t197 = t75 * t91
  t198 = t197 * t98
  t201 = 0.1e1 / t47 / t79
  t202 = t133 ** 2
  t204 = t68 * t44 * t201 * t202
  t207 = t76 * t139
  t208 = t98 * t67
  t209 = t207 * t208
  t210 = t69 * t72
  t212 = t210 * t133 * t149
  t215 = t126 * t158
  t218 = t202 * t69
  t219 = t218 * t72
  t226 = 0.40e2 / 0.9e1 * tau0 * t122 - 0.11e2 / 0.9e1 * s0 * t193
  t227 = t72 * t226
  t228 = t128 * t227
  t232 = 0.1e1 / t138 / t90
  t233 = t77 * t232
  t234 = t149 ** 2
  t241 = t67 * t80
  t246 = params.b * t83
  t253 = 0.500e3 / 0.81e2 * t241 * t202 + 0.250e3 / 0.81e2 * t141 * t226 + 0.625000e6 / 0.19683e5 * t246 * t87 * t202 + 0.125000e6 / 0.19683e5 * t145 * t87 * t226
  t259 = t114 / t152 / t93 * t69
  t264 = -0.200e3 / 0.531441e6 * t259 * t189 + 0.110e3 / 0.2187e4 * t155 * t194 + t191 - t196
  t266 = -t191 + t196 + 0.10000e5 / 0.729e3 * t198 * t204 + 0.100e3 / 0.27e2 * t209 * t212 - 0.100e3 / 0.27e2 * t215 * t135 - 0.50e2 / 0.27e2 * t127 * t219 - 0.50e2 / 0.27e2 * t127 * t228 + 0.2e1 * t233 * t98 * t234 - 0.2e1 * t140 * t158 * t149 - t140 * t98 * t253 + t92 * t264
  t271 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t100 - t5 * t109 * t100 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t113 * t160 + t5 * t170 * t100 / 0.12e2 - t5 * t174 * t160 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t178 * t266)
  t273 = r1 <= f.p.dens_threshold
  t274 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t275 = 0.1e1 + t274
  t276 = t275 <= f.p.zeta_threshold
  t277 = t275 ** (0.1e1 / 0.3e1)
  t278 = t277 ** 2
  t279 = 0.1e1 / t278
  t281 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t282 = t281 ** 2
  t286 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t290 = f.my_piecewise3(t276, 0, 0.4e1 / 0.9e1 * t279 * t282 + 0.4e1 / 0.3e1 * t277 * t286)
  t292 = r1 ** 2
  t293 = r1 ** (0.1e1 / 0.3e1)
  t294 = t293 ** 2
  t297 = s2 / t294 / t292
  t299 = 0.5e1 / 0.972e3 * t49 * t297
  t304 = params.kappa * (0.1e1 - params.kappa / (params.kappa + t299))
  t309 = tau1 / t294 / r1 - t297 / 0.8e1
  t310 = t309 ** 2
  t314 = 0.1e1 - 0.25e2 / 0.81e2 * t310 * t69 * t72
  t315 = t314 ** 2
  t320 = t310 ** 2
  t335 = 0.1e1 + t304 + t315 * t314 / (0.1e1 + 0.250e3 / 0.243e3 * t310 * t309 * t80 + 0.62500e5 / 0.59049e5 * params.b * t320 * t310 * t87) * (params.kappa * (0.1e1 - params.kappa / (params.kappa + t299 + params.c)) - t304)
  t341 = f.my_piecewise3(t276, 0, 0.4e1 / 0.3e1 * t277 * t281)
  t347 = f.my_piecewise3(t276, t165, t277 * t275)
  t353 = f.my_piecewise3(t273, 0, -0.3e1 / 0.8e1 * t5 * t290 * t42 * t335 - t5 * t341 * t108 * t335 / 0.4e1 + t5 * t347 * t169 * t335 / 0.12e2)
  t363 = t24 ** 2
  t367 = 0.6e1 * t33 - 0.6e1 * t16 / t363
  t368 = f.my_piecewise5(t10, 0, t14, 0, t367)
  t372 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t368)
  t395 = 0.1e1 / t107 / t24
  t406 = t202 * t133
  t409 = t133 * t226
  t416 = 0.1e1 / t52 / t185 / r0
  t419 = -0.440e3 / 0.27e2 * tau0 * t193 + 0.154e3 / 0.27e2 * s0 * t416
  t435 = t138 ** 2
  t451 = t152 ** 2
  t456 = t185 ** 2
  t459 = t80 * t183 * s0 / t456 / t120
  t464 = t184 / t51 / t456
  t467 = t119 * t416
  t470 = t115 ** 2
  t474 = 0.4000e4 / 0.43046721e8 * t114 / t470 * t459
  t476 = 0.2200e4 / 0.531441e6 * t182 * t464
  t478 = 0.1540e4 / 0.6561e4 * t118 * t467
  t490 = t98 * t68
  t492 = t44 * t201
  t505 = -t140 * t98 * (0.500e3 / 0.81e2 * t406 * t80 + 0.500e3 / 0.27e2 * t241 * t409 + 0.250e3 / 0.81e2 * t141 * t419 + 0.2500000e7 / 0.19683e5 * params.b * t78 * t87 * t406 + 0.625000e6 / 0.6561e4 * t246 * t146 * t226 + 0.125000e6 / 0.19683e5 * t145 * t87 * t419) - 0.6e1 * t77 / t435 * t98 * t234 * t149 + 0.6e1 * t233 * t158 * t234 - 0.3e1 * t140 * t264 * t149 - 0.3e1 * t140 * t158 * t253 + t92 * (-0.4000e4 / 0.43046721e8 * t114 / t451 * t459 + 0.2200e4 / 0.531441e6 * t259 * t464 - 0.1540e4 / 0.6561e4 * t155 * t467 + t474 - t476 + t478) - 0.1000000e7 / 0.19683e5 * t78 * t87 * t406 * t91 * t98 + 0.6e1 * t233 * t150 * t253 - t474 - 0.10000e5 / 0.243e3 * t75 * t139 * t490 * t492 * t202 * t149 + 0.10000e5 / 0.243e3 * t197 * t490 * t492 * t409 + 0.100e3 / 0.9e1 * t207 * t158 * t67 * t212
  t548 = 0.50e2 / 0.9e1 * t209 * t210 * t226 * t149 + 0.50e2 / 0.9e1 * t209 * t210 * t133 * t253 - 0.100e3 / 0.9e1 * t76 * t232 * t208 * t210 * t133 * t234 + 0.10000e5 / 0.243e3 * t197 * t158 * t204 - 0.50e2 / 0.9e1 * t126 * t264 * t135 - 0.50e2 / 0.9e1 * t215 * t228 - 0.50e2 / 0.9e1 * t127 * t133 * t69 * t227 - 0.50e2 / 0.27e2 * t127 * t128 * t72 * t419 + 0.10000e5 / 0.243e3 * t198 * t67 * t44 * t201 * t406 + 0.50e2 / 0.9e1 * t207 * t98 * t218 * t72 * t149 + t476 - t478 - 0.50e2 / 0.9e1 * t215 * t219
  t554 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t372 * t42 * t100 - 0.3e1 / 0.8e1 * t5 * t41 * t108 * t100 - 0.9e1 / 0.8e1 * t5 * t43 * t160 + t5 * t106 * t169 * t100 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t109 * t160 - 0.9e1 / 0.8e1 * t5 * t113 * t266 - 0.5e1 / 0.36e2 * t5 * t167 * t395 * t100 + t5 * t170 * t160 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t174 * t266 - 0.3e1 / 0.8e1 * t5 * t178 * (t505 + t548))
  t564 = f.my_piecewise5(t14, 0, t10, 0, -t367)
  t568 = f.my_piecewise3(t276, 0, -0.8e1 / 0.27e2 / t278 / t275 * t282 * t281 + 0.4e1 / 0.3e1 * t279 * t281 * t286 + 0.4e1 / 0.3e1 * t277 * t564)
  t586 = f.my_piecewise3(t273, 0, -0.3e1 / 0.8e1 * t5 * t568 * t42 * t335 - 0.3e1 / 0.8e1 * t5 * t290 * t108 * t335 + t5 * t341 * t169 * t335 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t347 * t395 * t335)
  d111 = 0.3e1 * t271 + 0.3e1 * t353 + t6 * (t554 + t586)

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
  t79 = tau0 / t64 / r0 - t67 / 0.8e1
  t80 = t79 ** 2
  t81 = t56 ** 2
  t84 = 0.1e1 / t58 / t57
  t87 = 0.1e1 - 0.25e2 / 0.81e2 * t80 * t81 * t84
  t88 = t87 ** 2
  t89 = t88 * t87
  t90 = t80 * t79
  t91 = t57 ** 2
  t92 = 0.1e1 / t91
  t95 = t80 ** 2
  t98 = t91 ** 2
  t99 = 0.1e1 / t98
  t102 = 0.1e1 + 0.250e3 / 0.243e3 * t90 * t92 + 0.62500e5 / 0.59049e5 * params.b * t95 * t80 * t99
  t103 = 0.1e1 / t102
  t104 = t89 * t103
  t105 = params.kappa + t69 + params.c
  t110 = params.kappa * (0.1e1 - params.kappa / t105) - t74
  t112 = t104 * t110 + t74 + 0.1e1
  t121 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t122 = t54 ** 2
  t123 = 0.1e1 / t122
  t124 = t121 * t123
  t128 = t121 * t54
  t129 = params.kappa ** 2
  t130 = t70 ** 2
  t133 = t129 / t130 * t56
  t134 = t60 * s0
  t135 = t62 * r0
  t137 = 0.1e1 / t64 / t135
  t138 = t134 * t137
  t139 = t133 * t138
  t141 = t88 * t103
  t142 = t141 * t110
  t143 = t79 * t81
  t148 = -0.5e1 / 0.3e1 * tau0 * t66 + s0 * t137 / 0.3e1
  t150 = t143 * t84 * t148
  t153 = t102 ** 2
  t154 = 0.1e1 / t153
  t155 = t89 * t154
  t156 = t80 * t92
  t160 = params.b * t95 * t79
  t161 = t99 * t148
  t164 = 0.250e3 / 0.81e2 * t156 * t148 + 0.125000e6 / 0.19683e5 * t160 * t161
  t165 = t110 * t164
  t167 = t105 ** 2
  t170 = t129 / t167 * t56
  t173 = -0.10e2 / 0.729e3 * t170 * t138 + 0.10e2 / 0.729e3 * t139
  t175 = -0.10e2 / 0.729e3 * t139 - 0.50e2 / 0.27e2 * t142 * t150 - t155 * t165 + t104 * t173
  t181 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t183 = 0.1e1 / t122 / t6
  t184 = t181 * t183
  t188 = t181 * t123
  t192 = t181 * t54
  t196 = t129 / t130 / t70 * t81
  t197 = s0 ** 2
  t198 = t84 * t197
  t199 = t62 ** 2
  t203 = t198 / t63 / t199 / t135
  t205 = 0.200e3 / 0.531441e6 * t196 * t203
  t207 = 0.1e1 / t64 / t199
  t208 = t134 * t207
  t210 = 0.110e3 / 0.2187e4 * t133 * t208
  t211 = t87 * t103
  t212 = t211 * t110
  t213 = t80 * t56
  t215 = 0.1e1 / t59 / t91
  t216 = t148 ** 2
  t218 = t213 * t215 * t216
  t221 = t88 * t154
  t222 = t110 * t79
  t223 = t221 * t222
  t224 = t81 * t84
  t226 = t224 * t148 * t164
  t229 = t141 * t173
  t232 = t216 * t81
  t233 = t232 * t84
  t240 = 0.40e2 / 0.9e1 * tau0 * t137 - 0.11e2 / 0.9e1 * s0 * t207
  t241 = t84 * t240
  t242 = t143 * t241
  t246 = 0.1e1 / t153 / t102
  t247 = t89 * t246
  t248 = t164 ** 2
  t249 = t110 * t248
  t255 = t79 * t92
  t260 = params.b * t95
  t261 = t99 * t216
  t267 = 0.500e3 / 0.81e2 * t255 * t216 + 0.250e3 / 0.81e2 * t156 * t240 + 0.625000e6 / 0.19683e5 * t260 * t261 + 0.125000e6 / 0.19683e5 * t160 * t99 * t240
  t273 = t129 / t167 / t105 * t81
  t278 = -0.200e3 / 0.531441e6 * t273 * t203 + 0.110e3 / 0.2187e4 * t170 * t208 + t205 - t210
  t280 = -t205 + t210 + 0.10000e5 / 0.729e3 * t212 * t218 + 0.100e3 / 0.27e2 * t223 * t226 - 0.100e3 / 0.27e2 * t229 * t150 - 0.50e2 / 0.27e2 * t142 * t233 - 0.50e2 / 0.27e2 * t142 * t242 + 0.2e1 * t247 * t249 - 0.2e1 * t155 * t173 * t164 - t155 * t110 * t267 + t104 * t278
  t284 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t285 = t284 * f.p.zeta_threshold
  t287 = f.my_piecewise3(t20, t285, t21 * t19)
  t289 = 0.1e1 / t122 / t25
  t290 = t287 * t289
  t294 = t287 * t183
  t298 = t287 * t123
  t302 = t287 * t54
  t303 = t211 * t173
  t306 = t141 * t278
  t311 = t148 * t81
  t312 = t311 * t241
  t319 = 0.1e1 / t64 / t199 / r0
  t322 = -0.440e3 / 0.27e2 * tau0 * t207 + 0.154e3 / 0.27e2 * s0 * t319
  t323 = t84 * t322
  t324 = t143 * t323
  t328 = t216 * t148
  t330 = t79 * t56 * t215 * t328
  t333 = t221 * t110
  t335 = t232 * t84 * t164
  t338 = t167 ** 2
  t340 = t129 / t338
  t342 = t92 * t197 * s0
  t343 = t199 ** 2
  t346 = t342 / t343 / t135
  t351 = t198 / t63 / t343
  t354 = t134 * t319
  t357 = t130 ** 2
  t359 = t129 / t357
  t361 = 0.4000e4 / 0.43046721e8 * t359 * t346
  t363 = 0.2200e4 / 0.531441e6 * t196 * t351
  t365 = 0.1540e4 / 0.6561e4 * t133 * t354
  t366 = -0.4000e4 / 0.43046721e8 * t340 * t346 + 0.2200e4 / 0.531441e6 * t273 * t351 - 0.1540e4 / 0.6561e4 * t170 * t354 + t361 - t363 + t365
  t370 = t148 * t240
  t375 = params.b * t90
  t385 = 0.500e3 / 0.81e2 * t328 * t92 + 0.500e3 / 0.27e2 * t255 * t370 + 0.250e3 / 0.81e2 * t156 * t322 + 0.2500000e7 / 0.19683e5 * t375 * t99 * t328 + 0.625000e6 / 0.6561e4 * t260 * t161 * t240 + 0.125000e6 / 0.19683e5 * t160 * t99 * t322
  t386 = t110 * t385
  t388 = t153 ** 2
  t389 = 0.1e1 / t388
  t390 = t89 * t389
  t391 = t248 * t164
  t392 = t110 * t391
  t395 = t173 * t248
  t398 = t278 * t164
  t401 = 0.10000e5 / 0.243e3 * t303 * t218 - 0.50e2 / 0.9e1 * t306 * t150 - 0.50e2 / 0.9e1 * t229 * t242 - 0.50e2 / 0.9e1 * t142 * t312 - 0.50e2 / 0.27e2 * t142 * t324 + 0.10000e5 / 0.243e3 * t212 * t330 + 0.50e2 / 0.9e1 * t333 * t335 + t104 * t366 - t155 * t386 - 0.6e1 * t390 * t392 + 0.6e1 * t247 * t395 - 0.3e1 * t155 * t398
  t402 = t173 * t267
  t405 = t90 * t99
  t406 = t328 * t103
  t415 = t87 * t154
  t416 = t110 * t80
  t417 = t415 * t416
  t418 = t56 * t215
  t420 = t418 * t216 * t164
  t423 = t211 * t416
  t424 = t418 * t370
  t428 = t221 * t173 * t79
  t431 = t240 * t164
  t432 = t224 * t431
  t435 = t148 * t267
  t439 = t88 * t246
  t440 = t439 * t222
  t445 = -0.3e1 * t155 * t402 - 0.1000000e7 / 0.19683e5 * t405 * t406 * t110 + 0.6e1 * t247 * t165 * t267 - t361 - 0.50e2 / 0.9e1 * t229 * t233 + t363 - t365 - 0.10000e5 / 0.243e3 * t417 * t420 + 0.10000e5 / 0.243e3 * t423 * t424 + 0.100e3 / 0.9e1 * t428 * t226 + 0.50e2 / 0.9e1 * t223 * t432 + 0.50e2 / 0.9e1 * t223 * t224 * t435 - 0.100e3 / 0.9e1 * t440 * t224 * t148 * t248
  t446 = t401 + t445
  t451 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t112 - 0.3e1 / 0.8e1 * t5 * t124 * t112 - 0.9e1 / 0.8e1 * t5 * t128 * t175 + t5 * t184 * t112 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t188 * t175 - 0.9e1 / 0.8e1 * t5 * t192 * t280 - 0.5e1 / 0.36e2 * t5 * t290 * t112 + t5 * t294 * t175 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t298 * t280 - 0.3e1 / 0.8e1 * t5 * t302 * t446)
  t453 = r1 <= f.p.dens_threshold
  t454 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t455 = 0.1e1 + t454
  t456 = t455 <= f.p.zeta_threshold
  t457 = t455 ** (0.1e1 / 0.3e1)
  t458 = t457 ** 2
  t460 = 0.1e1 / t458 / t455
  t462 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t463 = t462 ** 2
  t467 = 0.1e1 / t458
  t468 = t467 * t462
  t470 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t474 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t478 = f.my_piecewise3(t456, 0, -0.8e1 / 0.27e2 * t460 * t463 * t462 + 0.4e1 / 0.3e1 * t468 * t470 + 0.4e1 / 0.3e1 * t457 * t474)
  t480 = r1 ** 2
  t481 = r1 ** (0.1e1 / 0.3e1)
  t482 = t481 ** 2
  t485 = s2 / t482 / t480
  t487 = 0.5e1 / 0.972e3 * t61 * t485
  t492 = params.kappa * (0.1e1 - params.kappa / (params.kappa + t487))
  t497 = tau1 / t482 / r1 - t485 / 0.8e1
  t498 = t497 ** 2
  t502 = 0.1e1 - 0.25e2 / 0.81e2 * t498 * t81 * t84
  t503 = t502 ** 2
  t508 = t498 ** 2
  t523 = 0.1e1 + t492 + t503 * t502 / (0.1e1 + 0.250e3 / 0.243e3 * t498 * t497 * t92 + 0.62500e5 / 0.59049e5 * params.b * t508 * t498 * t99) * (params.kappa * (0.1e1 - params.kappa / (params.kappa + t487 + params.c)) - t492)
  t532 = f.my_piecewise3(t456, 0, 0.4e1 / 0.9e1 * t467 * t463 + 0.4e1 / 0.3e1 * t457 * t470)
  t539 = f.my_piecewise3(t456, 0, 0.4e1 / 0.3e1 * t457 * t462)
  t545 = f.my_piecewise3(t456, t285, t457 * t455)
  t551 = f.my_piecewise3(t453, 0, -0.3e1 / 0.8e1 * t5 * t478 * t54 * t523 - 0.3e1 / 0.8e1 * t5 * t532 * t123 * t523 + t5 * t539 * t183 * t523 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t545 * t289 * t523)
  t555 = t240 ** 2
  t579 = t199 * t62
  t581 = 0.1e1 / t64 / t579
  t584 = 0.6160e4 / 0.81e2 * tau0 * t319 - 0.2618e4 / 0.81e2 * s0 * t581
  t603 = t197 ** 2
  t608 = t603 / t64 / t343 / t579 * t61
  t610 = 0.160000e6 / 0.31381059609e11 * t129 / t357 / t70 * t92 * t608
  t611 = -0.200e3 / 0.27e2 * t229 * t324 + 0.10000e5 / 0.243e3 * t212 * t213 * t215 * t555 + 0.40000e5 / 0.243e3 * t303 * t330 + 0.200e3 / 0.9e1 * t221 * t173 * t335 + 0.100e3 / 0.9e1 * t333 * t232 * t84 * t267 - 0.200e3 / 0.9e1 * t439 * t110 * t232 * t84 * t248 - 0.200e3 / 0.27e2 * t142 * t311 * t323 - 0.50e2 / 0.27e2 * t142 * t143 * t84 * t584 - 0.200e3 / 0.27e2 * t141 * t366 * t150 + 0.20000e5 / 0.243e3 * t211 * t278 * t218 - 0.100e3 / 0.9e1 * t306 * t242 - 0.200e3 / 0.9e1 * t229 * t312 - t610
  t618 = t267 ** 2
  t625 = t248 ** 2
  t643 = t148 * t322
  t649 = t216 ** 2
  t687 = t342 / t343 / t199
  t689 = 0.88000e5 / 0.43046721e8 * t359 * t687
  t690 = -0.24e2 * t390 * t173 * t391 + 0.12e2 * t247 * t278 * t248 + 0.6e1 * t247 * t110 * t618 + 0.24e2 * t89 / t388 / t102 * t110 * t625 - 0.4e1 * t155 * t366 * t164 - 0.6e1 * t155 * t278 * t267 - 0.4e1 * t155 * t173 * t385 - t155 * t110 * (0.1000e4 / 0.27e2 * t216 * t92 * t240 + 0.500e3 / 0.27e2 * t255 * t555 + 0.2000e4 / 0.81e2 * t255 * t643 + 0.250e3 / 0.81e2 * t156 * t584 + 0.2500000e7 / 0.6561e4 * params.b * t80 * t99 * t649 + 0.5000000e7 / 0.6561e4 * t375 * t261 * t240 + 0.625000e6 / 0.6561e4 * t260 * t99 * t555 + 0.2500000e7 / 0.19683e5 * t260 * t161 * t322 + 0.125000e6 / 0.19683e5 * t160 * t99 * t584) - 0.36e2 * t390 * t249 * t267 - 0.4000000e7 / 0.19683e5 * t405 * t406 * t173 - 0.2000000e7 / 0.6561e4 * t80 * t99 * t649 * t103 * t110 + 0.24e2 * t247 * t402 * t164 + 0.8e1 * t247 * t386 * t164 + t689
  t715 = t198 / t63 / t343 / r0
  t717 = 0.195800e6 / 0.4782969e7 * t196 * t715
  t718 = t134 * t581
  t720 = 0.26180e5 / 0.19683e5 * t133 * t718
  t756 = -0.2000000e7 / 0.6561e4 * t405 * t216 * t103 * t110 * t240 - 0.50e2 / 0.9e1 * t142 * t555 * t81 * t84 + 0.10000e5 / 0.243e3 * t212 * t649 * t56 * t215 - 0.100e3 / 0.9e1 * t306 * t233 + 0.4000000e7 / 0.19683e5 * t405 * t328 * t154 * t110 * t164 - t717 + t720 + t104 * (-0.160000e6 / 0.31381059609e11 * t129 / t338 / t105 * t92 * t608 + 0.88000e5 / 0.43046721e8 * t340 * t687 - 0.195800e6 / 0.4782969e7 * t273 * t715 + 0.26180e5 / 0.19683e5 * t170 * t718 + t610 - t689 + t717 - t720) + 0.40000e5 / 0.243e3 * t87 * t246 * t416 * t418 * t216 * t248 - 0.40000e5 / 0.243e3 * t415 * t222 * t418 * t328 * t164 + 0.20000e5 / 0.81e2 * t211 * t222 * t418 * t216 * t240 + 0.40000e5 / 0.729e3 * t423 * t418 * t643 + 0.200e3 / 0.9e1 * t428 * t432
  t757 = t173 * t80
  t808 = -0.40000e5 / 0.243e3 * t415 * t757 * t420 + 0.200e3 / 0.9e1 * t221 * t110 * t148 * t432 + 0.200e3 / 0.27e2 * t223 * t224 * t322 * t164 + 0.100e3 / 0.9e1 * t223 * t224 * t240 * t267 - 0.20000e5 / 0.243e3 * t417 * t418 * t216 * t267 + 0.40000e5 / 0.243e3 * t211 * t757 * t424 + 0.200e3 / 0.9e1 * t221 * t402 * t150 + 0.200e3 / 0.27e2 * t221 * t386 * t150 + 0.400e3 / 0.9e1 * t88 * t389 * t392 * t150 - 0.400e3 / 0.9e1 * t439 * t395 * t150 + 0.200e3 / 0.9e1 * t221 * t398 * t150 - 0.200e3 / 0.9e1 * t440 * t224 * t240 * t248 - 0.40000e5 / 0.243e3 * t417 * t418 * t431 * t148 - 0.400e3 / 0.9e1 * t440 * t224 * t435 * t164
  t814 = t19 ** 2
  t817 = t30 ** 2
  t823 = t41 ** 2
  t832 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t833 = f.my_piecewise5(t10, 0, t14, 0, t832)
  t837 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t814 * t817 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t823 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t833)
  t881 = 0.1e1 / t122 / t36
  t886 = -0.3e1 / 0.8e1 * t5 * t302 * (t611 + t690 + t756 + t808) - 0.3e1 / 0.8e1 * t5 * t837 * t54 * t112 - 0.3e1 / 0.2e1 * t5 * t55 * t175 - 0.3e1 / 0.2e1 * t5 * t124 * t175 - 0.9e1 / 0.4e1 * t5 * t128 * t280 + t5 * t184 * t175 - 0.3e1 / 0.2e1 * t5 * t188 * t280 - 0.3e1 / 0.2e1 * t5 * t192 * t446 - 0.5e1 / 0.9e1 * t5 * t290 * t175 + t5 * t294 * t280 / 0.2e1 - t5 * t298 * t446 / 0.2e1 - t5 * t53 * t123 * t112 / 0.2e1 + t5 * t121 * t183 * t112 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t181 * t289 * t112 + 0.10e2 / 0.27e2 * t5 * t287 * t881 * t112
  t887 = f.my_piecewise3(t1, 0, t886)
  t888 = t455 ** 2
  t891 = t463 ** 2
  t897 = t470 ** 2
  t903 = f.my_piecewise5(t14, 0, t10, 0, -t832)
  t907 = f.my_piecewise3(t456, 0, 0.40e2 / 0.81e2 / t458 / t888 * t891 - 0.16e2 / 0.9e1 * t460 * t463 * t470 + 0.4e1 / 0.3e1 * t467 * t897 + 0.16e2 / 0.9e1 * t468 * t474 + 0.4e1 / 0.3e1 * t457 * t903)
  t929 = f.my_piecewise3(t453, 0, -0.3e1 / 0.8e1 * t5 * t907 * t54 * t523 - t5 * t478 * t123 * t523 / 0.2e1 + t5 * t532 * t183 * t523 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t539 * t289 * t523 + 0.10e2 / 0.27e2 * t5 * t545 * t881 * t523)
  d1111 = 0.4e1 * t451 + 0.4e1 * t551 + t6 * (t887 + t929)

  res = {'v4rho4': d1111}
  return res
