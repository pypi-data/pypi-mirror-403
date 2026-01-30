"""Generated from mgga_x_eel.mpl."""

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
  params_a0_raw = params.a0
  if isinstance(params_a0_raw, (str, bytes, dict)):
    params_a0 = params_a0_raw
  else:
    try:
      params_a0_seq = list(params_a0_raw)
    except TypeError:
      params_a0 = params_a0_raw
    else:
      params_a0_seq = np.asarray(params_a0_seq, dtype=np.float64)
      params_a0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a0_seq))
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
  params_x0_raw = params.x0
  if isinstance(params_x0_raw, (str, bytes, dict)):
    params_x0 = params_x0_raw
  else:
    try:
      params_x0_seq = list(params_x0_raw)
    except TypeError:
      params_x0 = params_x0_raw
    else:
      params_x0_seq = np.asarray(params_x0_seq, dtype=np.float64)
      params_x0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_x0_seq))

  scan_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  scan_h0x = 1.174

  eel_atilde = lambda a: params_a0 * jnp.tanh(a / params_a0)

  eel_G = lambda x: scan_h0x * (1 - f.my_piecewise3(x > params_x0, jnp.exp(-params_c * jnp.maximum(x - params_x0, 0) ** (-1 / 4)), 0))

  eel_k = lambda a0: (1 - scan_h0x) / (eel_G(3 * a0 * jnp.tanh(1 / a0) / 5) - scan_h0x)

  eel_Fx = lambda s, a: eel_k(params_a0) * (eel_G(s ** 2 + 3 * eel_atilde(a) / 5) - eel_G(s ** 2)) + eel_G(s ** 2)

  eel_f = lambda x, u, t: eel_Fx(X2S * x, scan_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, eel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_a0_raw = params.a0
  if isinstance(params_a0_raw, (str, bytes, dict)):
    params_a0 = params_a0_raw
  else:
    try:
      params_a0_seq = list(params_a0_raw)
    except TypeError:
      params_a0 = params_a0_raw
    else:
      params_a0_seq = np.asarray(params_a0_seq, dtype=np.float64)
      params_a0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a0_seq))
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
  params_x0_raw = params.x0
  if isinstance(params_x0_raw, (str, bytes, dict)):
    params_x0 = params_x0_raw
  else:
    try:
      params_x0_seq = list(params_x0_raw)
    except TypeError:
      params_x0 = params_x0_raw
    else:
      params_x0_seq = np.asarray(params_x0_seq, dtype=np.float64)
      params_x0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_x0_seq))

  scan_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  scan_h0x = 1.174

  eel_atilde = lambda a: params_a0 * jnp.tanh(a / params_a0)

  eel_G = lambda x: scan_h0x * (1 - f.my_piecewise3(x > params_x0, jnp.exp(-params_c * jnp.maximum(x - params_x0, 0) ** (-1 / 4)), 0))

  eel_k = lambda a0: (1 - scan_h0x) / (eel_G(3 * a0 * jnp.tanh(1 / a0) / 5) - scan_h0x)

  eel_Fx = lambda s, a: eel_k(params_a0) * (eel_G(s ** 2 + 3 * eel_atilde(a) / 5) - eel_G(s ** 2)) + eel_G(s ** 2)

  eel_f = lambda x, u, t: eel_Fx(X2S * x, scan_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, eel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_a0_raw = params.a0
  if isinstance(params_a0_raw, (str, bytes, dict)):
    params_a0 = params_a0_raw
  else:
    try:
      params_a0_seq = list(params_a0_raw)
    except TypeError:
      params_a0 = params_a0_raw
    else:
      params_a0_seq = np.asarray(params_a0_seq, dtype=np.float64)
      params_a0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a0_seq))
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
  params_x0_raw = params.x0
  if isinstance(params_x0_raw, (str, bytes, dict)):
    params_x0 = params_x0_raw
  else:
    try:
      params_x0_seq = list(params_x0_raw)
    except TypeError:
      params_x0 = params_x0_raw
    else:
      params_x0_seq = np.asarray(params_x0_seq, dtype=np.float64)
      params_x0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_x0_seq))

  scan_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  scan_h0x = 1.174

  eel_atilde = lambda a: params_a0 * jnp.tanh(a / params_a0)

  eel_G = lambda x: scan_h0x * (1 - f.my_piecewise3(x > params_x0, jnp.exp(-params_c * jnp.maximum(x - params_x0, 0) ** (-1 / 4)), 0))

  eel_k = lambda a0: (1 - scan_h0x) / (eel_G(3 * a0 * jnp.tanh(1 / a0) / 5) - scan_h0x)

  eel_Fx = lambda s, a: eel_k(params_a0) * (eel_G(s ** 2 + 3 * eel_atilde(a) / 5) - eel_G(s ** 2)) + eel_G(s ** 2)

  eel_f = lambda x, u, t: eel_Fx(X2S * x, scan_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, eel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t28 = 0.1e1 / params.a0
  t29 = jnp.tanh(t28)
  t31 = 0.3e1 / 0.5e1 * params.a0 * t29
  t33 = t31 - params.x0
  t35 = f.my_piecewise3(0.0e0 < t33, t33, 0)
  t36 = t35 ** (0.1e1 / 0.4e1)
  t39 = jnp.exp(-params.c / t36)
  t40 = f.my_piecewise3(params.x0 < t31, t39, 0)
  t41 = 0.1e1 / t40
  t42 = 6 ** (0.1e1 / 0.3e1)
  t43 = jnp.pi ** 2
  t44 = t43 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = 0.1e1 / t45
  t47 = t42 * t46
  t48 = r0 ** 2
  t49 = r0 ** (0.1e1 / 0.3e1)
  t50 = t49 ** 2
  t52 = 0.1e1 / t50 / t48
  t53 = s0 * t52
  t55 = t47 * t53 / 0.24e2
  t57 = 0.1e1 / t50 / r0
  t62 = t46 * t28
  t65 = jnp.tanh(0.5e1 / 0.9e1 * (tau0 * t57 - t53 / 0.8e1) * t42 * t62)
  t67 = 0.3e1 / 0.5e1 * params.a0 * t65
  t69 = params.x0 < t55 + t67
  t70 = t55 + t67 - params.x0
  t71 = 0.0e0 < t70
  t72 = f.my_piecewise3(t71, t70, 0)
  t73 = t72 ** (0.1e1 / 0.4e1)
  t76 = jnp.exp(-params.c / t73)
  t77 = f.my_piecewise3(t69, t76, 0)
  t79 = params.x0 < t55
  t80 = t55 - params.x0
  t81 = 0.0e0 < t80
  t82 = f.my_piecewise3(t81, t80, 0)
  t83 = t82 ** (0.1e1 / 0.4e1)
  t86 = jnp.exp(-params.c / t83)
  t87 = f.my_piecewise3(t79, t86, 0)
  t88 = 0.1174e1 * t87
  t92 = 0.14821124361158432708688245315161839863713798977853e0 * t41 * (-0.1174e1 * t77 + t88) + 0.1174e1 - t88
  t96 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t92)
  t97 = r1 <= f.p.dens_threshold
  t98 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t99 = 0.1e1 + t98
  t100 = t99 <= f.p.zeta_threshold
  t101 = t99 ** (0.1e1 / 0.3e1)
  t103 = f.my_piecewise3(t100, t22, t101 * t99)
  t104 = t103 * t26
  t105 = r1 ** 2
  t106 = r1 ** (0.1e1 / 0.3e1)
  t107 = t106 ** 2
  t109 = 0.1e1 / t107 / t105
  t110 = s2 * t109
  t112 = t47 * t110 / 0.24e2
  t114 = 0.1e1 / t107 / r1
  t121 = jnp.tanh(0.5e1 / 0.9e1 * (tau1 * t114 - t110 / 0.8e1) * t42 * t62)
  t123 = 0.3e1 / 0.5e1 * params.a0 * t121
  t125 = params.x0 < t112 + t123
  t126 = t112 + t123 - params.x0
  t127 = 0.0e0 < t126
  t128 = f.my_piecewise3(t127, t126, 0)
  t129 = t128 ** (0.1e1 / 0.4e1)
  t132 = jnp.exp(-params.c / t129)
  t133 = f.my_piecewise3(t125, t132, 0)
  t135 = params.x0 < t112
  t136 = t112 - params.x0
  t137 = 0.0e0 < t136
  t138 = f.my_piecewise3(t137, t136, 0)
  t139 = t138 ** (0.1e1 / 0.4e1)
  t142 = jnp.exp(-params.c / t139)
  t143 = f.my_piecewise3(t135, t142, 0)
  t144 = 0.1174e1 * t143
  t148 = 0.14821124361158432708688245315161839863713798977853e0 * t41 * (-0.1174e1 * t133 + t144) + 0.1174e1 - t144
  t152 = f.my_piecewise3(t97, 0, -0.3e1 / 0.8e1 * t5 * t104 * t148)
  t153 = t6 ** 2
  t155 = t16 / t153
  t156 = t7 - t155
  t157 = f.my_piecewise5(t10, 0, t14, 0, t156)
  t160 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t157)
  t165 = t26 ** 2
  t166 = 0.1e1 / t165
  t170 = t5 * t25 * t166 * t92 / 0.8e1
  t173 = params.c / t73 / t72
  t177 = s0 / t50 / t48 / r0
  t179 = t47 * t177 / 0.9e1
  t180 = t65 ** 2
  t181 = 0.1e1 - t180
  t190 = f.my_piecewise3(t71, -t179 + t181 * (-0.5e1 / 0.3e1 * tau0 * t52 + t177 / 0.3e1) * t47 / 0.3e1, 0)
  t194 = f.my_piecewise3(t69, t173 * t190 * t76 / 0.4e1, 0)
  t198 = params.c / t83 / t82
  t199 = f.my_piecewise3(t81, -t179, 0)
  t203 = f.my_piecewise3(t79, t198 * t199 * t86 / 0.4e1, 0)
  t204 = 0.1174e1 * t203
  t213 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t160 * t26 * t92 - t170 - 0.3e1 / 0.8e1 * t5 * t27 * (0.14821124361158432708688245315161839863713798977853e0 * t41 * (-0.1174e1 * t194 + t204) - t204))
  t215 = f.my_piecewise5(t14, 0, t10, 0, -t156)
  t218 = f.my_piecewise3(t100, 0, 0.4e1 / 0.3e1 * t101 * t215)
  t226 = t5 * t103 * t166 * t148 / 0.8e1
  t228 = f.my_piecewise3(t97, 0, -0.3e1 / 0.8e1 * t5 * t218 * t26 * t148 - t226)
  vrho_0_ = t96 + t152 + t6 * (t213 + t228)
  t231 = -t7 - t155
  t232 = f.my_piecewise5(t10, 0, t14, 0, t231)
  t235 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t232)
  t241 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t235 * t26 * t92 - t170)
  t243 = f.my_piecewise5(t14, 0, t10, 0, -t231)
  t246 = f.my_piecewise3(t100, 0, 0.4e1 / 0.3e1 * t101 * t243)
  t253 = params.c / t129 / t128
  t257 = s2 / t107 / t105 / r1
  t259 = t47 * t257 / 0.9e1
  t260 = t121 ** 2
  t261 = 0.1e1 - t260
  t270 = f.my_piecewise3(t127, -t259 + t261 * (-0.5e1 / 0.3e1 * tau1 * t109 + t257 / 0.3e1) * t47 / 0.3e1, 0)
  t274 = f.my_piecewise3(t125, t253 * t270 * t132 / 0.4e1, 0)
  t278 = params.c / t139 / t138
  t279 = f.my_piecewise3(t137, -t259, 0)
  t283 = f.my_piecewise3(t135, t278 * t279 * t142 / 0.4e1, 0)
  t284 = 0.1174e1 * t283
  t293 = f.my_piecewise3(t97, 0, -0.3e1 / 0.8e1 * t5 * t246 * t26 * t148 - t226 - 0.3e1 / 0.8e1 * t5 * t104 * (0.14821124361158432708688245315161839863713798977853e0 * t41 * (-0.1174e1 * t274 + t284) - t284))
  vrho_1_ = t96 + t152 + t6 * (t241 + t293)
  t296 = t47 * t52
  t301 = f.my_piecewise3(t71, -t181 * t52 * t47 / 0.24e2 + t296 / 0.24e2, 0)
  t305 = f.my_piecewise3(t69, t173 * t301 * t76 / 0.4e1, 0)
  t308 = f.my_piecewise3(t81, t296 / 0.24e2, 0)
  t312 = f.my_piecewise3(t79, t198 * t308 * t86 / 0.4e1, 0)
  t313 = 0.1174e1 * t312
  t321 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.14821124361158432708688245315161839863713798977853e0 * t41 * (-0.1174e1 * t305 + t313) - t313))
  vsigma_0_ = t6 * t321
  vsigma_1_ = 0.0e0
  t322 = t47 * t109
  t327 = f.my_piecewise3(t127, -t261 * t109 * t47 / 0.24e2 + t322 / 0.24e2, 0)
  t331 = f.my_piecewise3(t125, t253 * t327 * t132 / 0.4e1, 0)
  t334 = f.my_piecewise3(t137, t322 / 0.24e2, 0)
  t338 = f.my_piecewise3(t135, t278 * t334 * t142 / 0.4e1, 0)
  t339 = 0.1174e1 * t338
  t347 = f.my_piecewise3(t97, 0, -0.3e1 / 0.8e1 * t5 * t104 * (0.14821124361158432708688245315161839863713798977853e0 * t41 * (-0.1174e1 * t331 + t339) - t339))
  vsigma_2_ = t6 * t347
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t349 = t26 * t41
  t353 = f.my_piecewise3(t71, t181 * t57 * t47 / 0.3e1, 0)
  t357 = f.my_piecewise3(t69, t173 * t353 * t76 / 0.4e1, 0)
  t361 = f.my_piecewise3(t1, 0, 0.65249999999999999999999999999999999999999999999996e-1 * t5 * t25 * t349 * t357)
  vtau_0_ = t6 * t361
  t366 = f.my_piecewise3(t127, t261 * t114 * t47 / 0.3e1, 0)
  t370 = f.my_piecewise3(t125, t253 * t366 * t132 / 0.4e1, 0)
  t374 = f.my_piecewise3(t97, 0, 0.65249999999999999999999999999999999999999999999996e-1 * t5 * t103 * t349 * t370)
  vtau_1_ = t6 * t374
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
  params_a0_raw = params.a0
  if isinstance(params_a0_raw, (str, bytes, dict)):
    params_a0 = params_a0_raw
  else:
    try:
      params_a0_seq = list(params_a0_raw)
    except TypeError:
      params_a0 = params_a0_raw
    else:
      params_a0_seq = np.asarray(params_a0_seq, dtype=np.float64)
      params_a0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a0_seq))
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
  params_x0_raw = params.x0
  if isinstance(params_x0_raw, (str, bytes, dict)):
    params_x0 = params_x0_raw
  else:
    try:
      params_x0_seq = list(params_x0_raw)
    except TypeError:
      params_x0 = params_x0_raw
    else:
      params_x0_seq = np.asarray(params_x0_seq, dtype=np.float64)
      params_x0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_x0_seq))

  scan_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  scan_h0x = 1.174

  eel_atilde = lambda a: params_a0 * jnp.tanh(a / params_a0)

  eel_G = lambda x: scan_h0x * (1 - f.my_piecewise3(x > params_x0, jnp.exp(-params_c * jnp.maximum(x - params_x0, 0) ** (-1 / 4)), 0))

  eel_k = lambda a0: (1 - scan_h0x) / (eel_G(3 * a0 * jnp.tanh(1 / a0) / 5) - scan_h0x)

  eel_Fx = lambda s, a: eel_k(params_a0) * (eel_G(s ** 2 + 3 * eel_atilde(a) / 5) - eel_G(s ** 2)) + eel_G(s ** 2)

  eel_f = lambda x, u, t: eel_Fx(X2S * x, scan_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, eel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t20 = 0.1e1 / params.a0
  t21 = jnp.tanh(t20)
  t23 = 0.3e1 / 0.5e1 * params.a0 * t21
  t25 = t23 - params.x0
  t27 = f.my_piecewise3(0.0e0 < t25, t25, 0)
  t28 = t27 ** (0.1e1 / 0.4e1)
  t31 = jnp.exp(-params.c / t28)
  t32 = f.my_piecewise3(params.x0 < t23, t31, 0)
  t33 = 0.1e1 / t32
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = jnp.pi ** 2
  t36 = t35 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = 0.1e1 / t37
  t39 = t34 * t38
  t40 = 2 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t42 = s0 * t41
  t43 = r0 ** 2
  t44 = t18 ** 2
  t46 = 0.1e1 / t44 / t43
  t47 = t42 * t46
  t49 = t39 * t47 / 0.24e2
  t50 = tau0 * t41
  t52 = 0.1e1 / t44 / r0
  t60 = jnp.tanh(0.5e1 / 0.9e1 * (t50 * t52 - t47 / 0.8e1) * t34 * t38 * t20)
  t62 = 0.3e1 / 0.5e1 * params.a0 * t60
  t64 = params.x0 < t49 + t62
  t65 = t49 + t62 - params.x0
  t66 = 0.0e0 < t65
  t67 = f.my_piecewise3(t66, t65, 0)
  t68 = t67 ** (0.1e1 / 0.4e1)
  t71 = jnp.exp(-params.c / t68)
  t72 = f.my_piecewise3(t64, t71, 0)
  t74 = params.x0 < t49
  t75 = t49 - params.x0
  t76 = 0.0e0 < t75
  t77 = f.my_piecewise3(t76, t75, 0)
  t78 = t77 ** (0.1e1 / 0.4e1)
  t81 = jnp.exp(-params.c / t78)
  t82 = f.my_piecewise3(t74, t81, 0)
  t83 = 0.1174e1 * t82
  t87 = 0.14821124361158432708688245315161839863713798977853e0 * t33 * (-0.1174e1 * t72 + t83) + 0.1174e1 - t83
  t91 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t87)
  t99 = params.c / t68 / t67
  t103 = t42 / t44 / t43 / r0
  t105 = t39 * t103 / 0.9e1
  t106 = t60 ** 2
  t107 = 0.1e1 - t106
  t116 = f.my_piecewise3(t66, -t105 + t107 * (-0.5e1 / 0.3e1 * t50 * t46 + t103 / 0.3e1) * t39 / 0.3e1, 0)
  t120 = f.my_piecewise3(t64, t99 * t116 * t71 / 0.4e1, 0)
  t124 = params.c / t78 / t77
  t125 = f.my_piecewise3(t76, -t105, 0)
  t129 = f.my_piecewise3(t74, t124 * t125 * t81 / 0.4e1, 0)
  t130 = 0.1174e1 * t129
  t139 = f.my_piecewise3(t2, 0, -t6 * t17 / t44 * t87 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (0.14821124361158432708688245315161839863713798977853e0 * t33 * (-0.1174e1 * t120 + t130) - t130))
  vrho_0_ = 0.2e1 * r0 * t139 + 0.2e1 * t91
  t143 = t39 * t41 * t46
  t144 = t107 * t41
  t150 = f.my_piecewise3(t66, -t144 * t46 * t34 * t38 / 0.24e2 + t143 / 0.24e2, 0)
  t154 = f.my_piecewise3(t64, t99 * t150 * t71 / 0.4e1, 0)
  t157 = f.my_piecewise3(t76, t143 / 0.24e2, 0)
  t161 = f.my_piecewise3(t74, t124 * t157 * t81 / 0.4e1, 0)
  t162 = 0.1174e1 * t161
  t170 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.14821124361158432708688245315161839863713798977853e0 * t33 * (-0.1174e1 * t154 + t162) - t162))
  vsigma_0_ = 0.2e1 * r0 * t170
  vlapl_0_ = 0.0e0
  t178 = f.my_piecewise3(t66, t144 * t52 * t34 * t38 / 0.3e1, 0)
  t182 = f.my_piecewise3(t64, t99 * t178 * t71 / 0.4e1, 0)
  t186 = f.my_piecewise3(t2, 0, 0.65249999999999999999999999999999999999999999999996e-1 * t6 * t17 * t18 * t33 * t182)
  vtau_0_ = 0.2e1 * r0 * t186
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
  t22 = 0.1e1 / params.a0
  t23 = jnp.tanh(t22)
  t25 = 0.3e1 / 0.5e1 * params.a0 * t23
  t27 = t25 - params.x0
  t29 = f.my_piecewise3(0.0e0 < t27, t27, 0)
  t30 = t29 ** (0.1e1 / 0.4e1)
  t33 = jnp.exp(-params.c / t30)
  t34 = f.my_piecewise3(params.x0 < t25, t33, 0)
  t35 = 0.1e1 / t34
  t36 = 6 ** (0.1e1 / 0.3e1)
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t41 = t36 * t40
  t42 = 2 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = s0 * t43
  t45 = r0 ** 2
  t47 = 0.1e1 / t19 / t45
  t48 = t44 * t47
  t50 = t41 * t48 / 0.24e2
  t51 = tau0 * t43
  t53 = 0.1e1 / t19 / r0
  t61 = jnp.tanh(0.5e1 / 0.9e1 * (t51 * t53 - t48 / 0.8e1) * t36 * t40 * t22)
  t63 = 0.3e1 / 0.5e1 * params.a0 * t61
  t65 = params.x0 < t50 + t63
  t66 = t50 + t63 - params.x0
  t67 = 0.0e0 < t66
  t68 = f.my_piecewise3(t67, t66, 0)
  t69 = t68 ** (0.1e1 / 0.4e1)
  t72 = jnp.exp(-params.c / t69)
  t73 = f.my_piecewise3(t65, t72, 0)
  t75 = params.x0 < t50
  t76 = t50 - params.x0
  t77 = 0.0e0 < t76
  t78 = f.my_piecewise3(t77, t76, 0)
  t79 = t78 ** (0.1e1 / 0.4e1)
  t82 = jnp.exp(-params.c / t79)
  t83 = f.my_piecewise3(t75, t82, 0)
  t84 = 0.1174e1 * t83
  t88 = 0.14821124361158432708688245315161839863713798977853e0 * t35 * (-0.1174e1 * t73 + t84) + 0.1174e1 - t84
  t92 = t17 * t18
  t95 = params.c / t69 / t68
  t98 = 0.1e1 / t19 / t45 / r0
  t99 = t44 * t98
  t101 = t41 * t99 / 0.9e1
  t102 = t61 ** 2
  t103 = 0.1e1 - t102
  t107 = -0.5e1 / 0.3e1 * t51 * t47 + t99 / 0.3e1
  t112 = f.my_piecewise3(t67, -t101 + t103 * t107 * t41 / 0.3e1, 0)
  t116 = f.my_piecewise3(t65, t95 * t112 * t72 / 0.4e1, 0)
  t120 = params.c / t79 / t78
  t121 = f.my_piecewise3(t77, -t101, 0)
  t125 = f.my_piecewise3(t75, t120 * t121 * t82 / 0.4e1, 0)
  t126 = 0.1174e1 * t125
  t130 = 0.14821124361158432708688245315161839863713798977853e0 * t35 * (-0.1174e1 * t116 + t126) - t126
  t135 = f.my_piecewise3(t2, 0, -t6 * t21 * t88 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t92 * t130)
  t144 = t68 ** 2
  t148 = t112 ** 2
  t149 = t148 * t72
  t152 = t45 ** 2
  t155 = t44 / t19 / t152
  t157 = 0.11e2 / 0.27e2 * t41 * t155
  t159 = t107 ** 2
  t161 = t36 ** 2
  t176 = f.my_piecewise3(t67, t157 - 0.10e2 / 0.27e2 * t61 * t103 * t159 * t161 / t38 / t37 * t22 + t103 * (0.40e2 / 0.9e1 * t51 * t98 - 0.11e2 / 0.9e1 * t155) * t41 / 0.3e1, 0)
  t180 = params.c ** 2
  t181 = jnp.sqrt(t68)
  t188 = f.my_piecewise3(t65, -0.5e1 / 0.16e2 * params.c / t69 / t144 * t149 + t95 * t176 * t72 / 0.4e1 + t180 / t181 / t144 * t149 / 0.16e2, 0)
  t190 = t78 ** 2
  t194 = t121 ** 2
  t195 = t194 * t82
  t198 = f.my_piecewise3(t77, t157, 0)
  t202 = jnp.sqrt(t78)
  t209 = f.my_piecewise3(t75, -0.5e1 / 0.16e2 * params.c / t79 / t190 * t195 + t120 * t198 * t82 / 0.4e1 + t180 / t202 / t190 * t195 / 0.16e2, 0)
  t210 = 0.1174e1 * t209
  t219 = f.my_piecewise3(t2, 0, t6 * t17 * t53 * t88 / 0.12e2 - t6 * t21 * t130 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t92 * (0.14821124361158432708688245315161839863713798977853e0 * t35 * (-0.1174e1 * t188 + t210) - t210))
  v2rho2_0_ = 0.2e1 * r0 * t219 + 0.4e1 * t135
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
  t23 = 0.1e1 / params.a0
  t24 = jnp.tanh(t23)
  t26 = 0.3e1 / 0.5e1 * params.a0 * t24
  t28 = t26 - params.x0
  t30 = f.my_piecewise3(0.0e0 < t28, t28, 0)
  t31 = t30 ** (0.1e1 / 0.4e1)
  t34 = jnp.exp(-params.c / t31)
  t35 = f.my_piecewise3(params.x0 < t26, t34, 0)
  t36 = 0.1e1 / t35
  t37 = 6 ** (0.1e1 / 0.3e1)
  t38 = jnp.pi ** 2
  t39 = t38 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t41 = 0.1e1 / t40
  t42 = t37 * t41
  t43 = 2 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = s0 * t44
  t46 = r0 ** 2
  t48 = 0.1e1 / t19 / t46
  t49 = t45 * t48
  t51 = t42 * t49 / 0.24e2
  t52 = tau0 * t44
  t60 = jnp.tanh(0.5e1 / 0.9e1 * (t52 * t21 - t49 / 0.8e1) * t37 * t41 * t23)
  t62 = 0.3e1 / 0.5e1 * params.a0 * t60
  t64 = params.x0 < t51 + t62
  t65 = t51 + t62 - params.x0
  t66 = 0.0e0 < t65
  t67 = f.my_piecewise3(t66, t65, 0)
  t68 = t67 ** (0.1e1 / 0.4e1)
  t71 = jnp.exp(-params.c / t68)
  t72 = f.my_piecewise3(t64, t71, 0)
  t74 = params.x0 < t51
  t75 = t51 - params.x0
  t76 = 0.0e0 < t75
  t77 = f.my_piecewise3(t76, t75, 0)
  t78 = t77 ** (0.1e1 / 0.4e1)
  t81 = jnp.exp(-params.c / t78)
  t82 = f.my_piecewise3(t74, t81, 0)
  t83 = 0.1174e1 * t82
  t87 = 0.14821124361158432708688245315161839863713798977853e0 * t36 * (-0.1174e1 * t72 + t83) + 0.1174e1 - t83
  t92 = t17 / t19
  t95 = params.c / t68 / t67
  t98 = 0.1e1 / t19 / t46 / r0
  t99 = t45 * t98
  t101 = t42 * t99 / 0.9e1
  t102 = t60 ** 2
  t103 = 0.1e1 - t102
  t107 = -0.5e1 / 0.3e1 * t52 * t48 + t99 / 0.3e1
  t112 = f.my_piecewise3(t66, -t101 + t103 * t107 * t42 / 0.3e1, 0)
  t113 = t112 * t71
  t116 = f.my_piecewise3(t64, t95 * t113 / 0.4e1, 0)
  t120 = params.c / t78 / t77
  t121 = f.my_piecewise3(t76, -t101, 0)
  t122 = t121 * t81
  t125 = f.my_piecewise3(t74, t120 * t122 / 0.4e1, 0)
  t126 = 0.1174e1 * t125
  t130 = 0.14821124361158432708688245315161839863713798977853e0 * t36 * (-0.1174e1 * t116 + t126) - t126
  t134 = t17 * t18
  t135 = t67 ** 2
  t138 = params.c / t68 / t135
  t139 = t112 ** 2
  t140 = t139 * t71
  t143 = t46 ** 2
  t145 = 0.1e1 / t19 / t143
  t146 = t45 * t145
  t148 = 0.11e2 / 0.27e2 * t42 * t146
  t149 = t60 * t103
  t150 = t107 ** 2
  t152 = t37 ** 2
  t155 = t152 / t39 / t38
  t162 = 0.40e2 / 0.9e1 * t52 * t98 - 0.11e2 / 0.9e1 * t146
  t167 = f.my_piecewise3(t66, t148 - 0.10e2 / 0.27e2 * t149 * t150 * t155 * t23 + t103 * t162 * t42 / 0.3e1, 0)
  t171 = params.c ** 2
  t172 = jnp.sqrt(t67)
  t175 = t171 / t172 / t135
  t179 = f.my_piecewise3(t64, -0.5e1 / 0.16e2 * t138 * t140 + t95 * t167 * t71 / 0.4e1 + t175 * t140 / 0.16e2, 0)
  t181 = t77 ** 2
  t184 = params.c / t78 / t181
  t185 = t121 ** 2
  t186 = t185 * t81
  t189 = f.my_piecewise3(t76, t148, 0)
  t193 = jnp.sqrt(t77)
  t196 = t171 / t193 / t181
  t200 = f.my_piecewise3(t74, -0.5e1 / 0.16e2 * t184 * t186 + t120 * t189 * t81 / 0.4e1 + t196 * t186 / 0.16e2, 0)
  t201 = 0.1174e1 * t200
  t205 = 0.14821124361158432708688245315161839863713798977853e0 * t36 * (-0.1174e1 * t179 + t201) - t201
  t210 = f.my_piecewise3(t2, 0, t6 * t22 * t87 / 0.12e2 - t6 * t92 * t130 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t134 * t205)
  t222 = t135 * t67
  t227 = t139 * t112 * t71
  t230 = t113 * t167
  t241 = t45 / t19 / t143 / r0
  t243 = 0.154e3 / 0.81e2 * t42 * t241
  t244 = t103 ** 2
  t245 = t150 * t107
  t247 = t38 ** 2
  t248 = 0.1e1 / t247
  t249 = params.a0 ** 2
  t250 = 0.1e1 / t249
  t272 = f.my_piecewise3(t66, -t243 - 0.100e3 / 0.81e2 * t244 * t245 * t248 * t250 + 0.200e3 / 0.81e2 * t102 * t103 * t245 * t248 * t250 - 0.10e2 / 0.9e1 * t149 * t107 * t155 * t23 * t162 + t103 * (-0.440e3 / 0.27e2 * t52 * t145 + 0.154e3 / 0.27e2 * t241) * t42 / 0.3e1, 0)
  t278 = t171 * params.c
  t279 = t68 ** 2
  t287 = f.my_piecewise3(t64, 0.45e2 / 0.64e2 * params.c / t68 / t222 * t227 - 0.15e2 / 0.16e2 * t138 * t230 - 0.15e2 / 0.64e2 * t171 / t172 / t222 * t227 + t95 * t272 * t71 / 0.4e1 + 0.3e1 / 0.16e2 * t175 * t230 + t278 / t279 / t68 / t222 * t227 / 0.64e2, 0)
  t289 = t181 * t77
  t294 = t185 * t121 * t81
  t297 = t122 * t189
  t305 = f.my_piecewise3(t76, -t243, 0)
  t311 = t78 ** 2
  t319 = f.my_piecewise3(t74, 0.45e2 / 0.64e2 * params.c / t78 / t289 * t294 - 0.15e2 / 0.16e2 * t184 * t297 - 0.15e2 / 0.64e2 * t171 / t193 / t289 * t294 + t120 * t305 * t81 / 0.4e1 + 0.3e1 / 0.16e2 * t196 * t297 + t278 / t311 / t78 / t289 * t294 / 0.64e2, 0)
  t320 = 0.1174e1 * t319
  t329 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t48 * t87 + t6 * t22 * t130 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t92 * t205 - 0.3e1 / 0.8e1 * t6 * t134 * (0.14821124361158432708688245315161839863713798977853e0 * t36 * (-0.1174e1 * t287 + t320) - t320))
  v3rho3_0_ = 0.2e1 * r0 * t329 + 0.6e1 * t210

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
  t24 = 0.1e1 / params.a0
  t25 = jnp.tanh(t24)
  t27 = 0.3e1 / 0.5e1 * params.a0 * t25
  t29 = t27 - params.x0
  t31 = f.my_piecewise3(0.0e0 < t29, t29, 0)
  t32 = t31 ** (0.1e1 / 0.4e1)
  t35 = jnp.exp(-params.c / t32)
  t36 = f.my_piecewise3(params.x0 < t27, t35, 0)
  t37 = 0.1e1 / t36
  t38 = 6 ** (0.1e1 / 0.3e1)
  t39 = jnp.pi ** 2
  t40 = t39 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t43 = t38 * t42
  t44 = 2 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = s0 * t45
  t47 = t46 * t22
  t49 = t43 * t47 / 0.24e2
  t50 = tau0 * t45
  t52 = 0.1e1 / t20 / r0
  t60 = jnp.tanh(0.5e1 / 0.9e1 * (t50 * t52 - t47 / 0.8e1) * t38 * t42 * t24)
  t62 = 0.3e1 / 0.5e1 * params.a0 * t60
  t64 = params.x0 < t49 + t62
  t65 = t49 + t62 - params.x0
  t66 = 0.0e0 < t65
  t67 = f.my_piecewise3(t66, t65, 0)
  t68 = t67 ** (0.1e1 / 0.4e1)
  t71 = jnp.exp(-params.c / t68)
  t72 = f.my_piecewise3(t64, t71, 0)
  t74 = params.x0 < t49
  t75 = t49 - params.x0
  t76 = 0.0e0 < t75
  t77 = f.my_piecewise3(t76, t75, 0)
  t78 = t77 ** (0.1e1 / 0.4e1)
  t81 = jnp.exp(-params.c / t78)
  t82 = f.my_piecewise3(t74, t81, 0)
  t83 = 0.1174e1 * t82
  t87 = 0.14821124361158432708688245315161839863713798977853e0 * t37 * (-0.1174e1 * t72 + t83) + 0.1174e1 - t83
  t91 = t17 * t52
  t94 = params.c / t68 / t67
  t97 = 0.1e1 / t20 / t18 / r0
  t98 = t46 * t97
  t100 = t43 * t98 / 0.9e1
  t101 = t60 ** 2
  t102 = 0.1e1 - t101
  t106 = -0.5e1 / 0.3e1 * t50 * t22 + t98 / 0.3e1
  t111 = f.my_piecewise3(t66, -t100 + t102 * t106 * t43 / 0.3e1, 0)
  t112 = t111 * t71
  t115 = f.my_piecewise3(t64, t94 * t112 / 0.4e1, 0)
  t119 = params.c / t78 / t77
  t120 = f.my_piecewise3(t76, -t100, 0)
  t121 = t120 * t81
  t124 = f.my_piecewise3(t74, t119 * t121 / 0.4e1, 0)
  t125 = 0.1174e1 * t124
  t129 = 0.14821124361158432708688245315161839863713798977853e0 * t37 * (-0.1174e1 * t115 + t125) - t125
  t134 = t17 / t20
  t135 = t67 ** 2
  t138 = params.c / t68 / t135
  t139 = t111 ** 2
  t140 = t139 * t71
  t143 = t18 ** 2
  t145 = 0.1e1 / t20 / t143
  t146 = t46 * t145
  t148 = 0.11e2 / 0.27e2 * t43 * t146
  t149 = t60 * t102
  t150 = t106 ** 2
  t152 = t38 ** 2
  t155 = t152 / t40 / t39
  t156 = t155 * t24
  t162 = 0.40e2 / 0.9e1 * t50 * t97 - 0.11e2 / 0.9e1 * t146
  t167 = f.my_piecewise3(t66, t148 - 0.10e2 / 0.27e2 * t149 * t150 * t156 + t102 * t162 * t43 / 0.3e1, 0)
  t171 = params.c ** 2
  t172 = jnp.sqrt(t67)
  t175 = t171 / t172 / t135
  t179 = f.my_piecewise3(t64, -0.5e1 / 0.16e2 * t138 * t140 + t94 * t167 * t71 / 0.4e1 + t175 * t140 / 0.16e2, 0)
  t181 = t77 ** 2
  t184 = params.c / t78 / t181
  t185 = t120 ** 2
  t186 = t185 * t81
  t189 = f.my_piecewise3(t76, t148, 0)
  t193 = jnp.sqrt(t77)
  t196 = t171 / t193 / t181
  t200 = f.my_piecewise3(t74, -0.5e1 / 0.16e2 * t184 * t186 + t119 * t189 * t81 / 0.4e1 + t196 * t186 / 0.16e2, 0)
  t201 = 0.1174e1 * t200
  t205 = 0.14821124361158432708688245315161839863713798977853e0 * t37 * (-0.1174e1 * t179 + t201) - t201
  t209 = t17 * t19
  t210 = t135 * t67
  t213 = params.c / t68 / t210
  t215 = t139 * t111 * t71
  t218 = t112 * t167
  t223 = t171 / t172 / t210
  t228 = 0.1e1 / t20 / t143 / r0
  t229 = t46 * t228
  t231 = 0.154e3 / 0.81e2 * t43 * t229
  t232 = t102 ** 2
  t233 = t150 * t106
  t235 = t39 ** 2
  t236 = 0.1e1 / t235
  t237 = params.a0 ** 2
  t238 = 0.1e1 / t237
  t239 = t236 * t238
  t242 = t101 * t102
  t247 = t149 * t106
  t255 = -0.440e3 / 0.27e2 * t50 * t145 + 0.154e3 / 0.27e2 * t229
  t260 = f.my_piecewise3(t66, -t231 - 0.100e3 / 0.81e2 * t232 * t233 * t239 + 0.200e3 / 0.81e2 * t242 * t233 * t236 * t238 - 0.10e2 / 0.9e1 * t247 * t155 * t24 * t162 + t102 * t255 * t43 / 0.3e1, 0)
  t266 = t171 * params.c
  t267 = t68 ** 2
  t268 = t267 * t68
  t271 = t266 / t268 / t210
  t275 = f.my_piecewise3(t64, 0.45e2 / 0.64e2 * t213 * t215 - 0.15e2 / 0.16e2 * t138 * t218 - 0.15e2 / 0.64e2 * t223 * t215 + t94 * t260 * t71 / 0.4e1 + 0.3e1 / 0.16e2 * t175 * t218 + t271 * t215 / 0.64e2, 0)
  t277 = t181 * t77
  t280 = params.c / t78 / t277
  t282 = t185 * t120 * t81
  t285 = t121 * t189
  t290 = t171 / t193 / t277
  t293 = f.my_piecewise3(t76, -t231, 0)
  t299 = t78 ** 2
  t300 = t299 * t78
  t303 = t266 / t300 / t277
  t307 = f.my_piecewise3(t74, 0.45e2 / 0.64e2 * t280 * t282 - 0.15e2 / 0.16e2 * t184 * t285 - 0.15e2 / 0.64e2 * t290 * t282 + t119 * t293 * t81 / 0.4e1 + 0.3e1 / 0.16e2 * t196 * t285 + t303 * t282 / 0.64e2, 0)
  t308 = 0.1174e1 * t307
  t312 = 0.14821124361158432708688245315161839863713798977853e0 * t37 * (-0.1174e1 * t275 + t308) - t308
  t317 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t87 + t6 * t91 * t129 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t134 * t205 - 0.3e1 / 0.8e1 * t6 * t209 * t312)
  t332 = t135 ** 2
  t336 = t139 ** 2
  t337 = t336 * t71
  t340 = t140 * t167
  t348 = t167 ** 2
  t349 = t348 * t71
  t354 = t112 * t260
  t365 = t46 / t20 / t143 / t18
  t367 = 0.2618e4 / 0.243e3 * t43 * t365
  t368 = t150 ** 2
  t372 = 0.1e1 / t237 / params.a0
  t378 = t239 * t162
  t391 = t162 ** 2
  t407 = f.my_piecewise3(t66, t367 + 0.4000e4 / 0.729e3 * t232 * t368 * t236 * t372 * t60 * t43 - 0.200e3 / 0.27e2 * t232 * t150 * t378 - 0.2000e4 / 0.729e3 * t101 * t60 * t102 * t368 * t43 * t372 * t236 + 0.400e3 / 0.27e2 * t242 * t150 * t378 - 0.10e2 / 0.9e1 * t149 * t391 * t156 - 0.40e2 / 0.27e2 * t247 * t155 * t24 * t255 + t102 * (0.6160e4 / 0.81e2 * t50 * t228 - 0.2618e4 / 0.81e2 * t365) * t43 / 0.3e1, 0)
  t417 = t171 ** 2
  t423 = -0.585e3 / 0.256e3 * params.c / t68 / t332 * t337 + 0.135e3 / 0.32e2 * t213 * t340 + 0.255e3 / 0.256e3 * t171 / t172 / t332 * t337 - 0.15e2 / 0.16e2 * t138 * t349 - 0.45e2 / 0.32e2 * t223 * t340 - 0.5e1 / 0.4e1 * t138 * t354 - 0.15e2 / 0.128e3 * t266 / t268 / t332 * t337 + t94 * t407 * t71 / 0.4e1 + t175 * t354 / 0.4e1 + 0.3e1 / 0.16e2 * t175 * t349 + 0.3e1 / 0.32e2 * t271 * t340 + t417 / t332 / t67 * t337 / 0.256e3
  t424 = f.my_piecewise3(t64, t423, 0)
  t426 = t181 ** 2
  t430 = t185 ** 2
  t431 = t430 * t81
  t434 = t186 * t189
  t442 = t189 ** 2
  t443 = t442 * t81
  t448 = t121 * t293
  t456 = f.my_piecewise3(t76, t367, 0)
  t471 = -0.585e3 / 0.256e3 * params.c / t78 / t426 * t431 + 0.135e3 / 0.32e2 * t280 * t434 + 0.255e3 / 0.256e3 * t171 / t193 / t426 * t431 - 0.15e2 / 0.16e2 * t184 * t443 - 0.45e2 / 0.32e2 * t290 * t434 - 0.5e1 / 0.4e1 * t184 * t448 - 0.15e2 / 0.128e3 * t266 / t300 / t426 * t431 + t119 * t456 * t81 / 0.4e1 + t196 * t448 / 0.4e1 + 0.3e1 / 0.16e2 * t196 * t443 + 0.3e1 / 0.32e2 * t303 * t434 + t417 / t426 / t77 * t431 / 0.256e3
  t472 = f.my_piecewise3(t74, t471, 0)
  t473 = 0.1174e1 * t472
  t482 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t97 * t87 - 0.5e1 / 0.9e1 * t6 * t23 * t129 + t6 * t91 * t205 / 0.2e1 - t6 * t134 * t312 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t209 * (0.14821124361158432708688245315161839863713798977853e0 * t37 * (-0.1174e1 * t424 + t473) - t473))
  v4rho4_0_ = 0.2e1 * r0 * t482 + 0.8e1 * t317

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
  t32 = 0.1e1 / params.a0
  t33 = jnp.tanh(t32)
  t35 = 0.3e1 / 0.5e1 * params.a0 * t33
  t37 = t35 - params.x0
  t39 = f.my_piecewise3(0.0e0 < t37, t37, 0)
  t40 = t39 ** (0.1e1 / 0.4e1)
  t43 = jnp.exp(-params.c / t40)
  t44 = f.my_piecewise3(params.x0 < t35, t43, 0)
  t45 = 0.1e1 / t44
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t51 = t46 * t50
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / t52
  t57 = s0 * t56
  t59 = t51 * t57 / 0.24e2
  t66 = t50 * t32
  t69 = jnp.tanh(0.5e1 / 0.9e1 * (tau0 / t54 / r0 - t57 / 0.8e1) * t46 * t66)
  t71 = 0.3e1 / 0.5e1 * params.a0 * t69
  t73 = params.x0 < t59 + t71
  t74 = t59 + t71 - params.x0
  t75 = 0.0e0 < t74
  t76 = f.my_piecewise3(t75, t74, 0)
  t77 = t76 ** (0.1e1 / 0.4e1)
  t80 = jnp.exp(-params.c / t77)
  t81 = f.my_piecewise3(t73, t80, 0)
  t83 = params.x0 < t59
  t84 = t59 - params.x0
  t85 = 0.0e0 < t84
  t86 = f.my_piecewise3(t85, t84, 0)
  t87 = t86 ** (0.1e1 / 0.4e1)
  t90 = jnp.exp(-params.c / t87)
  t91 = f.my_piecewise3(t83, t90, 0)
  t92 = 0.1174e1 * t91
  t96 = 0.14821124361158432708688245315161839863713798977853e0 * t45 * (-0.1174e1 * t81 + t92) + 0.1174e1 - t92
  t100 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t101 = t100 * f.p.zeta_threshold
  t103 = f.my_piecewise3(t20, t101, t21 * t19)
  t104 = t30 ** 2
  t105 = 0.1e1 / t104
  t106 = t103 * t105
  t109 = t5 * t106 * t96 / 0.8e1
  t110 = t103 * t30
  t113 = params.c / t77 / t76
  t116 = 0.1e1 / t54 / t52 / r0
  t117 = s0 * t116
  t119 = t51 * t117 / 0.9e1
  t120 = t69 ** 2
  t121 = 0.1e1 - t120
  t125 = -0.5e1 / 0.3e1 * tau0 * t56 + t117 / 0.3e1
  t130 = f.my_piecewise3(t75, -t119 + t121 * t125 * t51 / 0.3e1, 0)
  t134 = f.my_piecewise3(t73, t113 * t130 * t80 / 0.4e1, 0)
  t138 = params.c / t87 / t86
  t139 = f.my_piecewise3(t85, -t119, 0)
  t143 = f.my_piecewise3(t83, t138 * t139 * t90 / 0.4e1, 0)
  t144 = 0.1174e1 * t143
  t148 = 0.14821124361158432708688245315161839863713798977853e0 * t45 * (-0.1174e1 * t134 + t144) - t144
  t153 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t96 - t109 - 0.3e1 / 0.8e1 * t5 * t110 * t148)
  t155 = r1 <= f.p.dens_threshold
  t156 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t157 = 0.1e1 + t156
  t158 = t157 <= f.p.zeta_threshold
  t159 = t157 ** (0.1e1 / 0.3e1)
  t161 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t164 = f.my_piecewise3(t158, 0, 0.4e1 / 0.3e1 * t159 * t161)
  t165 = t164 * t30
  t166 = r1 ** 2
  t167 = r1 ** (0.1e1 / 0.3e1)
  t168 = t167 ** 2
  t170 = 0.1e1 / t168 / t166
  t171 = s2 * t170
  t173 = t51 * t171 / 0.24e2
  t182 = jnp.tanh(0.5e1 / 0.9e1 * (tau1 / t168 / r1 - t171 / 0.8e1) * t46 * t66)
  t184 = 0.3e1 / 0.5e1 * params.a0 * t182
  t186 = params.x0 < t173 + t184
  t187 = t173 + t184 - params.x0
  t188 = 0.0e0 < t187
  t189 = f.my_piecewise3(t188, t187, 0)
  t190 = t189 ** (0.1e1 / 0.4e1)
  t193 = jnp.exp(-params.c / t190)
  t194 = f.my_piecewise3(t186, t193, 0)
  t196 = params.x0 < t173
  t197 = t173 - params.x0
  t198 = 0.0e0 < t197
  t199 = f.my_piecewise3(t198, t197, 0)
  t200 = t199 ** (0.1e1 / 0.4e1)
  t203 = jnp.exp(-params.c / t200)
  t204 = f.my_piecewise3(t196, t203, 0)
  t205 = 0.1174e1 * t204
  t209 = 0.14821124361158432708688245315161839863713798977853e0 * t45 * (-0.1174e1 * t194 + t205) + 0.1174e1 - t205
  t214 = f.my_piecewise3(t158, t101, t159 * t157)
  t215 = t214 * t105
  t218 = t5 * t215 * t209 / 0.8e1
  t220 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t5 * t165 * t209 - t218)
  t222 = t21 ** 2
  t223 = 0.1e1 / t222
  t224 = t26 ** 2
  t229 = t16 / t22 / t6
  t231 = -0.2e1 * t23 + 0.2e1 * t229
  t232 = f.my_piecewise5(t10, 0, t14, 0, t231)
  t236 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t223 * t224 + 0.4e1 / 0.3e1 * t21 * t232)
  t243 = t5 * t29 * t105 * t96
  t249 = 0.1e1 / t104 / t6
  t253 = t5 * t103 * t249 * t96 / 0.12e2
  t255 = t5 * t106 * t148
  t257 = t76 ** 2
  t261 = t130 ** 2
  t262 = t261 * t80
  t265 = t52 ** 2
  t268 = s0 / t54 / t265
  t270 = 0.11e2 / 0.27e2 * t51 * t268
  t272 = t125 ** 2
  t274 = t46 ** 2
  t278 = t274 / t48 / t47 * t32
  t289 = f.my_piecewise3(t75, t270 - 0.10e2 / 0.27e2 * t69 * t121 * t272 * t278 + t121 * (0.40e2 / 0.9e1 * tau0 * t116 - 0.11e2 / 0.9e1 * t268) * t51 / 0.3e1, 0)
  t293 = params.c ** 2
  t294 = jnp.sqrt(t76)
  t301 = f.my_piecewise3(t73, -0.5e1 / 0.16e2 * params.c / t77 / t257 * t262 + t113 * t289 * t80 / 0.4e1 + t293 / t294 / t257 * t262 / 0.16e2, 0)
  t303 = t86 ** 2
  t307 = t139 ** 2
  t308 = t307 * t90
  t311 = f.my_piecewise3(t85, t270, 0)
  t315 = jnp.sqrt(t86)
  t322 = f.my_piecewise3(t83, -0.5e1 / 0.16e2 * params.c / t87 / t303 * t308 + t138 * t311 * t90 / 0.4e1 + t293 / t315 / t303 * t308 / 0.16e2, 0)
  t323 = 0.1174e1 * t322
  t332 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t236 * t30 * t96 - t243 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t148 + t253 - t255 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t110 * (0.14821124361158432708688245315161839863713798977853e0 * t45 * (-0.1174e1 * t301 + t323) - t323))
  t333 = t159 ** 2
  t334 = 0.1e1 / t333
  t335 = t161 ** 2
  t339 = f.my_piecewise5(t14, 0, t10, 0, -t231)
  t343 = f.my_piecewise3(t158, 0, 0.4e1 / 0.9e1 * t334 * t335 + 0.4e1 / 0.3e1 * t159 * t339)
  t350 = t5 * t164 * t105 * t209
  t355 = t5 * t214 * t249 * t209 / 0.12e2
  t357 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t5 * t343 * t30 * t209 - t350 / 0.4e1 + t355)
  d11 = 0.2e1 * t153 + 0.2e1 * t220 + t6 * (t332 + t357)
  t360 = -t7 - t24
  t361 = f.my_piecewise5(t10, 0, t14, 0, t360)
  t364 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t361)
  t365 = t364 * t30
  t370 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t365 * t96 - t109)
  t372 = f.my_piecewise5(t14, 0, t10, 0, -t360)
  t375 = f.my_piecewise3(t158, 0, 0.4e1 / 0.3e1 * t159 * t372)
  t376 = t375 * t30
  t380 = t214 * t30
  t383 = params.c / t190 / t189
  t386 = 0.1e1 / t168 / t166 / r1
  t387 = s2 * t386
  t389 = t51 * t387 / 0.9e1
  t390 = t182 ** 2
  t391 = 0.1e1 - t390
  t395 = -0.5e1 / 0.3e1 * tau1 * t170 + t387 / 0.3e1
  t400 = f.my_piecewise3(t188, -t389 + t391 * t395 * t51 / 0.3e1, 0)
  t404 = f.my_piecewise3(t186, t383 * t400 * t193 / 0.4e1, 0)
  t408 = params.c / t200 / t199
  t409 = f.my_piecewise3(t198, -t389, 0)
  t413 = f.my_piecewise3(t196, t408 * t409 * t203 / 0.4e1, 0)
  t414 = 0.1174e1 * t413
  t418 = 0.14821124361158432708688245315161839863713798977853e0 * t45 * (-0.1174e1 * t404 + t414) - t414
  t423 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t5 * t376 * t209 - t218 - 0.3e1 / 0.8e1 * t5 * t380 * t418)
  t427 = 0.2e1 * t229
  t428 = f.my_piecewise5(t10, 0, t14, 0, t427)
  t432 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t223 * t361 * t26 + 0.4e1 / 0.3e1 * t21 * t428)
  t439 = t5 * t364 * t105 * t96
  t447 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t432 * t30 * t96 - t439 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t365 * t148 - t243 / 0.8e1 + t253 - t255 / 0.8e1)
  t451 = f.my_piecewise5(t14, 0, t10, 0, -t427)
  t455 = f.my_piecewise3(t158, 0, 0.4e1 / 0.9e1 * t334 * t372 * t161 + 0.4e1 / 0.3e1 * t159 * t451)
  t462 = t5 * t375 * t105 * t209
  t469 = t5 * t215 * t418
  t472 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t5 * t455 * t30 * t209 - t462 / 0.8e1 - t350 / 0.8e1 + t355 - 0.3e1 / 0.8e1 * t5 * t165 * t418 - t469 / 0.8e1)
  d12 = t153 + t220 + t370 + t423 + t6 * (t447 + t472)
  t477 = t361 ** 2
  t481 = 0.2e1 * t23 + 0.2e1 * t229
  t482 = f.my_piecewise5(t10, 0, t14, 0, t481)
  t486 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t223 * t477 + 0.4e1 / 0.3e1 * t21 * t482)
  t493 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t486 * t30 * t96 - t439 / 0.4e1 + t253)
  t494 = t372 ** 2
  t498 = f.my_piecewise5(t14, 0, t10, 0, -t481)
  t502 = f.my_piecewise3(t158, 0, 0.4e1 / 0.9e1 * t334 * t494 + 0.4e1 / 0.3e1 * t159 * t498)
  t512 = t189 ** 2
  t516 = t400 ** 2
  t517 = t516 * t193
  t520 = t166 ** 2
  t523 = s2 / t168 / t520
  t525 = 0.11e2 / 0.27e2 * t51 * t523
  t527 = t395 ** 2
  t539 = f.my_piecewise3(t188, t525 - 0.10e2 / 0.27e2 * t182 * t391 * t527 * t278 + t391 * (0.40e2 / 0.9e1 * tau1 * t386 - 0.11e2 / 0.9e1 * t523) * t51 / 0.3e1, 0)
  t543 = jnp.sqrt(t189)
  t550 = f.my_piecewise3(t186, -0.5e1 / 0.16e2 * params.c / t190 / t512 * t517 + t383 * t539 * t193 / 0.4e1 + t293 / t543 / t512 * t517 / 0.16e2, 0)
  t552 = t199 ** 2
  t556 = t409 ** 2
  t557 = t556 * t203
  t560 = f.my_piecewise3(t198, t525, 0)
  t564 = jnp.sqrt(t199)
  t571 = f.my_piecewise3(t196, -0.5e1 / 0.16e2 * params.c / t200 / t552 * t557 + t408 * t560 * t203 / 0.4e1 + t293 / t564 / t552 * t557 / 0.16e2, 0)
  t572 = 0.1174e1 * t571
  t581 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t5 * t502 * t30 * t209 - t462 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t376 * t418 + t355 - t469 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t380 * (0.14821124361158432708688245315161839863713798977853e0 * t45 * (-0.1174e1 * t550 + t572) - t572))
  d22 = 0.2e1 * t370 + 0.2e1 * t423 + t6 * (t493 + t581)
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
  t44 = 0.1e1 / params.a0
  t45 = jnp.tanh(t44)
  t47 = 0.3e1 / 0.5e1 * params.a0 * t45
  t49 = t47 - params.x0
  t51 = f.my_piecewise3(0.0e0 < t49, t49, 0)
  t52 = t51 ** (0.1e1 / 0.4e1)
  t55 = jnp.exp(-params.c / t52)
  t56 = f.my_piecewise3(params.x0 < t47, t55, 0)
  t57 = 0.1e1 / t56
  t58 = 6 ** (0.1e1 / 0.3e1)
  t59 = jnp.pi ** 2
  t60 = t59 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t62 = 0.1e1 / t61
  t63 = t58 * t62
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t69 = s0 * t68
  t71 = t63 * t69 / 0.24e2
  t78 = t62 * t44
  t81 = jnp.tanh(0.5e1 / 0.9e1 * (tau0 / t66 / r0 - t69 / 0.8e1) * t58 * t78)
  t83 = 0.3e1 / 0.5e1 * params.a0 * t81
  t85 = params.x0 < t71 + t83
  t86 = t71 + t83 - params.x0
  t87 = 0.0e0 < t86
  t88 = f.my_piecewise3(t87, t86, 0)
  t89 = t88 ** (0.1e1 / 0.4e1)
  t92 = jnp.exp(-params.c / t89)
  t93 = f.my_piecewise3(t85, t92, 0)
  t95 = params.x0 < t71
  t96 = t71 - params.x0
  t97 = 0.0e0 < t96
  t98 = f.my_piecewise3(t97, t96, 0)
  t99 = t98 ** (0.1e1 / 0.4e1)
  t102 = jnp.exp(-params.c / t99)
  t103 = f.my_piecewise3(t95, t102, 0)
  t104 = 0.1174e1 * t103
  t108 = 0.14821124361158432708688245315161839863713798977853e0 * t57 * (-0.1174e1 * t93 + t104) + 0.1174e1 - t104
  t114 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t115 = t42 ** 2
  t116 = 0.1e1 / t115
  t117 = t114 * t116
  t121 = t114 * t42
  t124 = params.c / t89 / t88
  t127 = 0.1e1 / t66 / t64 / r0
  t128 = s0 * t127
  t130 = t63 * t128 / 0.9e1
  t131 = t81 ** 2
  t132 = 0.1e1 - t131
  t136 = -0.5e1 / 0.3e1 * tau0 * t68 + t128 / 0.3e1
  t141 = f.my_piecewise3(t87, -t130 + t132 * t136 * t63 / 0.3e1, 0)
  t142 = t141 * t92
  t145 = f.my_piecewise3(t85, t124 * t142 / 0.4e1, 0)
  t149 = params.c / t99 / t98
  t150 = f.my_piecewise3(t97, -t130, 0)
  t151 = t150 * t102
  t154 = f.my_piecewise3(t95, t149 * t151 / 0.4e1, 0)
  t155 = 0.1174e1 * t154
  t159 = 0.14821124361158432708688245315161839863713798977853e0 * t57 * (-0.1174e1 * t145 + t155) - t155
  t163 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t164 = t163 * f.p.zeta_threshold
  t166 = f.my_piecewise3(t20, t164, t21 * t19)
  t168 = 0.1e1 / t115 / t6
  t169 = t166 * t168
  t173 = t166 * t116
  t177 = t166 * t42
  t178 = t88 ** 2
  t181 = params.c / t89 / t178
  t182 = t141 ** 2
  t183 = t182 * t92
  t186 = t64 ** 2
  t188 = 0.1e1 / t66 / t186
  t189 = s0 * t188
  t191 = 0.11e2 / 0.27e2 * t63 * t189
  t192 = t81 * t132
  t193 = t136 ** 2
  t195 = t58 ** 2
  t198 = t195 / t60 / t59
  t205 = 0.40e2 / 0.9e1 * tau0 * t127 - 0.11e2 / 0.9e1 * t189
  t210 = f.my_piecewise3(t87, t191 - 0.10e2 / 0.27e2 * t192 * t193 * t198 * t44 + t132 * t205 * t63 / 0.3e1, 0)
  t214 = params.c ** 2
  t215 = jnp.sqrt(t88)
  t218 = t214 / t215 / t178
  t222 = f.my_piecewise3(t85, -0.5e1 / 0.16e2 * t181 * t183 + t124 * t210 * t92 / 0.4e1 + t218 * t183 / 0.16e2, 0)
  t224 = t98 ** 2
  t227 = params.c / t99 / t224
  t228 = t150 ** 2
  t229 = t228 * t102
  t232 = f.my_piecewise3(t97, t191, 0)
  t236 = jnp.sqrt(t98)
  t239 = t214 / t236 / t224
  t243 = f.my_piecewise3(t95, -0.5e1 / 0.16e2 * t227 * t229 + t149 * t232 * t102 / 0.4e1 + t239 * t229 / 0.16e2, 0)
  t244 = 0.1174e1 * t243
  t248 = 0.14821124361158432708688245315161839863713798977853e0 * t57 * (-0.1174e1 * t222 + t244) - t244
  t253 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t108 - t5 * t117 * t108 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t121 * t159 + t5 * t169 * t108 / 0.12e2 - t5 * t173 * t159 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t177 * t248)
  t255 = r1 <= f.p.dens_threshold
  t256 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t257 = 0.1e1 + t256
  t258 = t257 <= f.p.zeta_threshold
  t259 = t257 ** (0.1e1 / 0.3e1)
  t260 = t259 ** 2
  t261 = 0.1e1 / t260
  t263 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t264 = t263 ** 2
  t268 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t272 = f.my_piecewise3(t258, 0, 0.4e1 / 0.9e1 * t261 * t264 + 0.4e1 / 0.3e1 * t259 * t268)
  t274 = r1 ** 2
  t275 = r1 ** (0.1e1 / 0.3e1)
  t276 = t275 ** 2
  t279 = s2 / t276 / t274
  t281 = t63 * t279 / 0.24e2
  t290 = jnp.tanh(0.5e1 / 0.9e1 * (tau1 / t276 / r1 - t279 / 0.8e1) * t58 * t78)
  t292 = 0.3e1 / 0.5e1 * params.a0 * t290
  t295 = t281 + t292 - params.x0
  t297 = f.my_piecewise3(0.0e0 < t295, t295, 0)
  t298 = t297 ** (0.1e1 / 0.4e1)
  t301 = jnp.exp(-params.c / t298)
  t302 = f.my_piecewise3(params.x0 < t281 + t292, t301, 0)
  t305 = t281 - params.x0
  t307 = f.my_piecewise3(0.0e0 < t305, t305, 0)
  t308 = t307 ** (0.1e1 / 0.4e1)
  t311 = jnp.exp(-params.c / t308)
  t312 = f.my_piecewise3(params.x0 < t281, t311, 0)
  t313 = 0.1174e1 * t312
  t317 = 0.14821124361158432708688245315161839863713798977853e0 * t57 * (-0.1174e1 * t302 + t313) + 0.1174e1 - t313
  t323 = f.my_piecewise3(t258, 0, 0.4e1 / 0.3e1 * t259 * t263)
  t329 = f.my_piecewise3(t258, t164, t259 * t257)
  t335 = f.my_piecewise3(t255, 0, -0.3e1 / 0.8e1 * t5 * t272 * t42 * t317 - t5 * t323 * t116 * t317 / 0.4e1 + t5 * t329 * t168 * t317 / 0.12e2)
  t345 = t24 ** 2
  t349 = 0.6e1 * t33 - 0.6e1 * t16 / t345
  t350 = f.my_piecewise5(t10, 0, t14, 0, t349)
  t354 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t350)
  t377 = 0.1e1 / t115 / t24
  t388 = t178 * t88
  t393 = t182 * t141 * t92
  t396 = t142 * t210
  t407 = s0 / t66 / t186 / r0
  t409 = 0.154e3 / 0.81e2 * t63 * t407
  t410 = t132 ** 2
  t411 = t193 * t136
  t413 = t59 ** 2
  t414 = 0.1e1 / t413
  t415 = params.a0 ** 2
  t416 = 0.1e1 / t415
  t438 = f.my_piecewise3(t87, -t409 - 0.100e3 / 0.81e2 * t410 * t411 * t414 * t416 + 0.200e3 / 0.81e2 * t131 * t132 * t411 * t414 * t416 - 0.10e2 / 0.9e1 * t192 * t136 * t198 * t44 * t205 + t132 * (-0.440e3 / 0.27e2 * tau0 * t188 + 0.154e3 / 0.27e2 * t407) * t63 / 0.3e1, 0)
  t444 = t214 * params.c
  t445 = t89 ** 2
  t453 = f.my_piecewise3(t85, 0.45e2 / 0.64e2 * params.c / t89 / t388 * t393 - 0.15e2 / 0.16e2 * t181 * t396 - 0.15e2 / 0.64e2 * t214 / t215 / t388 * t393 + t124 * t438 * t92 / 0.4e1 + 0.3e1 / 0.16e2 * t218 * t396 + t444 / t445 / t89 / t388 * t393 / 0.64e2, 0)
  t455 = t224 * t98
  t460 = t228 * t150 * t102
  t463 = t151 * t232
  t471 = f.my_piecewise3(t97, -t409, 0)
  t477 = t99 ** 2
  t485 = f.my_piecewise3(t95, 0.45e2 / 0.64e2 * params.c / t99 / t455 * t460 - 0.15e2 / 0.16e2 * t227 * t463 - 0.15e2 / 0.64e2 * t214 / t236 / t455 * t460 + t149 * t471 * t102 / 0.4e1 + 0.3e1 / 0.16e2 * t239 * t463 + t444 / t477 / t99 / t455 * t460 / 0.64e2, 0)
  t486 = 0.1174e1 * t485
  t495 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t354 * t42 * t108 - 0.3e1 / 0.8e1 * t5 * t41 * t116 * t108 - 0.9e1 / 0.8e1 * t5 * t43 * t159 + t5 * t114 * t168 * t108 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t117 * t159 - 0.9e1 / 0.8e1 * t5 * t121 * t248 - 0.5e1 / 0.36e2 * t5 * t166 * t377 * t108 + t5 * t169 * t159 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t173 * t248 - 0.3e1 / 0.8e1 * t5 * t177 * (0.14821124361158432708688245315161839863713798977853e0 * t57 * (-0.1174e1 * t453 + t486) - t486))
  t505 = f.my_piecewise5(t14, 0, t10, 0, -t349)
  t509 = f.my_piecewise3(t258, 0, -0.8e1 / 0.27e2 / t260 / t257 * t264 * t263 + 0.4e1 / 0.3e1 * t261 * t263 * t268 + 0.4e1 / 0.3e1 * t259 * t505)
  t527 = f.my_piecewise3(t255, 0, -0.3e1 / 0.8e1 * t5 * t509 * t42 * t317 - 0.3e1 / 0.8e1 * t5 * t272 * t116 * t317 + t5 * t323 * t168 * t317 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t329 * t377 * t317)
  d111 = 0.3e1 * t253 + 0.3e1 * t335 + t6 * (t495 + t527)

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
  t56 = 0.1e1 / params.a0
  t57 = jnp.tanh(t56)
  t59 = 0.3e1 / 0.5e1 * params.a0 * t57
  t61 = t59 - params.x0
  t63 = f.my_piecewise3(0.0e0 < t61, t61, 0)
  t64 = t63 ** (0.1e1 / 0.4e1)
  t67 = jnp.exp(-params.c / t64)
  t68 = f.my_piecewise3(params.x0 < t59, t67, 0)
  t69 = 0.1e1 / t68
  t70 = 6 ** (0.1e1 / 0.3e1)
  t71 = jnp.pi ** 2
  t72 = t71 ** (0.1e1 / 0.3e1)
  t73 = t72 ** 2
  t74 = 0.1e1 / t73
  t75 = t70 * t74
  t76 = r0 ** 2
  t77 = r0 ** (0.1e1 / 0.3e1)
  t78 = t77 ** 2
  t80 = 0.1e1 / t78 / t76
  t81 = s0 * t80
  t83 = t75 * t81 / 0.24e2
  t90 = t74 * t56
  t93 = jnp.tanh(0.5e1 / 0.9e1 * (tau0 / t78 / r0 - t81 / 0.8e1) * t70 * t90)
  t95 = 0.3e1 / 0.5e1 * params.a0 * t93
  t97 = params.x0 < t83 + t95
  t98 = t83 + t95 - params.x0
  t99 = 0.0e0 < t98
  t100 = f.my_piecewise3(t99, t98, 0)
  t101 = t100 ** (0.1e1 / 0.4e1)
  t104 = jnp.exp(-params.c / t101)
  t105 = f.my_piecewise3(t97, t104, 0)
  t107 = params.x0 < t83
  t108 = t83 - params.x0
  t109 = 0.0e0 < t108
  t110 = f.my_piecewise3(t109, t108, 0)
  t111 = t110 ** (0.1e1 / 0.4e1)
  t114 = jnp.exp(-params.c / t111)
  t115 = f.my_piecewise3(t107, t114, 0)
  t116 = 0.1174e1 * t115
  t120 = 0.14821124361158432708688245315161839863713798977853e0 * t69 * (-0.1174e1 * t105 + t116) + 0.1174e1 - t116
  t129 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t130 = t54 ** 2
  t131 = 0.1e1 / t130
  t132 = t129 * t131
  t136 = t129 * t54
  t139 = params.c / t101 / t100
  t142 = 0.1e1 / t78 / t76 / r0
  t143 = s0 * t142
  t145 = t75 * t143 / 0.9e1
  t146 = t93 ** 2
  t147 = 0.1e1 - t146
  t151 = -0.5e1 / 0.3e1 * tau0 * t80 + t143 / 0.3e1
  t156 = f.my_piecewise3(t99, -t145 + t147 * t151 * t75 / 0.3e1, 0)
  t157 = t156 * t104
  t160 = f.my_piecewise3(t97, t139 * t157 / 0.4e1, 0)
  t164 = params.c / t111 / t110
  t165 = f.my_piecewise3(t109, -t145, 0)
  t166 = t165 * t114
  t169 = f.my_piecewise3(t107, t164 * t166 / 0.4e1, 0)
  t170 = 0.1174e1 * t169
  t174 = 0.14821124361158432708688245315161839863713798977853e0 * t69 * (-0.1174e1 * t160 + t170) - t170
  t180 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t182 = 0.1e1 / t130 / t6
  t183 = t180 * t182
  t187 = t180 * t131
  t191 = t180 * t54
  t192 = t100 ** 2
  t195 = params.c / t101 / t192
  t196 = t156 ** 2
  t197 = t196 * t104
  t200 = t76 ** 2
  t202 = 0.1e1 / t78 / t200
  t203 = s0 * t202
  t205 = 0.11e2 / 0.27e2 * t75 * t203
  t206 = t93 * t147
  t207 = t151 ** 2
  t209 = t70 ** 2
  t212 = t209 / t72 / t71
  t213 = t212 * t56
  t219 = 0.40e2 / 0.9e1 * tau0 * t142 - 0.11e2 / 0.9e1 * t203
  t224 = f.my_piecewise3(t99, t205 - 0.10e2 / 0.27e2 * t206 * t207 * t213 + t147 * t219 * t75 / 0.3e1, 0)
  t228 = params.c ** 2
  t229 = jnp.sqrt(t100)
  t232 = t228 / t229 / t192
  t236 = f.my_piecewise3(t97, -0.5e1 / 0.16e2 * t195 * t197 + t139 * t224 * t104 / 0.4e1 + t232 * t197 / 0.16e2, 0)
  t238 = t110 ** 2
  t241 = params.c / t111 / t238
  t242 = t165 ** 2
  t243 = t242 * t114
  t246 = f.my_piecewise3(t109, t205, 0)
  t250 = jnp.sqrt(t110)
  t253 = t228 / t250 / t238
  t257 = f.my_piecewise3(t107, -0.5e1 / 0.16e2 * t241 * t243 + t164 * t246 * t114 / 0.4e1 + t253 * t243 / 0.16e2, 0)
  t258 = 0.1174e1 * t257
  t262 = 0.14821124361158432708688245315161839863713798977853e0 * t69 * (-0.1174e1 * t236 + t258) - t258
  t266 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t267 = t266 * f.p.zeta_threshold
  t269 = f.my_piecewise3(t20, t267, t21 * t19)
  t271 = 0.1e1 / t130 / t25
  t272 = t269 * t271
  t276 = t269 * t182
  t280 = t269 * t131
  t284 = t269 * t54
  t285 = t192 * t100
  t288 = params.c / t101 / t285
  t290 = t196 * t156 * t104
  t293 = t157 * t224
  t298 = t228 / t229 / t285
  t303 = 0.1e1 / t78 / t200 / r0
  t304 = s0 * t303
  t306 = 0.154e3 / 0.81e2 * t75 * t304
  t307 = t147 ** 2
  t308 = t207 * t151
  t310 = t71 ** 2
  t311 = 0.1e1 / t310
  t312 = params.a0 ** 2
  t313 = 0.1e1 / t312
  t314 = t311 * t313
  t317 = t146 * t147
  t322 = t206 * t151
  t330 = -0.440e3 / 0.27e2 * tau0 * t202 + 0.154e3 / 0.27e2 * t304
  t335 = f.my_piecewise3(t99, -t306 - 0.100e3 / 0.81e2 * t307 * t308 * t314 + 0.200e3 / 0.81e2 * t317 * t308 * t311 * t313 - 0.10e2 / 0.9e1 * t322 * t212 * t56 * t219 + t147 * t330 * t75 / 0.3e1, 0)
  t341 = t228 * params.c
  t342 = t101 ** 2
  t343 = t342 * t101
  t346 = t341 / t343 / t285
  t350 = f.my_piecewise3(t97, 0.45e2 / 0.64e2 * t288 * t290 - 0.15e2 / 0.16e2 * t195 * t293 - 0.15e2 / 0.64e2 * t298 * t290 + t139 * t335 * t104 / 0.4e1 + 0.3e1 / 0.16e2 * t232 * t293 + t346 * t290 / 0.64e2, 0)
  t352 = t238 * t110
  t355 = params.c / t111 / t352
  t357 = t242 * t165 * t114
  t360 = t166 * t246
  t365 = t228 / t250 / t352
  t368 = f.my_piecewise3(t109, -t306, 0)
  t374 = t111 ** 2
  t375 = t374 * t111
  t378 = t341 / t375 / t352
  t382 = f.my_piecewise3(t107, 0.45e2 / 0.64e2 * t355 * t357 - 0.15e2 / 0.16e2 * t241 * t360 - 0.15e2 / 0.64e2 * t365 * t357 + t164 * t368 * t114 / 0.4e1 + 0.3e1 / 0.16e2 * t253 * t360 + t378 * t357 / 0.64e2, 0)
  t383 = 0.1174e1 * t382
  t387 = 0.14821124361158432708688245315161839863713798977853e0 * t69 * (-0.1174e1 * t350 + t383) - t383
  t392 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t120 - 0.3e1 / 0.8e1 * t5 * t132 * t120 - 0.9e1 / 0.8e1 * t5 * t136 * t174 + t5 * t183 * t120 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t187 * t174 - 0.9e1 / 0.8e1 * t5 * t191 * t262 - 0.5e1 / 0.36e2 * t5 * t272 * t120 + t5 * t276 * t174 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t280 * t262 - 0.3e1 / 0.8e1 * t5 * t284 * t387)
  t394 = r1 <= f.p.dens_threshold
  t395 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t396 = 0.1e1 + t395
  t397 = t396 <= f.p.zeta_threshold
  t398 = t396 ** (0.1e1 / 0.3e1)
  t399 = t398 ** 2
  t401 = 0.1e1 / t399 / t396
  t403 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t404 = t403 ** 2
  t408 = 0.1e1 / t399
  t409 = t408 * t403
  t411 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t415 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t419 = f.my_piecewise3(t397, 0, -0.8e1 / 0.27e2 * t401 * t404 * t403 + 0.4e1 / 0.3e1 * t409 * t411 + 0.4e1 / 0.3e1 * t398 * t415)
  t421 = r1 ** 2
  t422 = r1 ** (0.1e1 / 0.3e1)
  t423 = t422 ** 2
  t426 = s2 / t423 / t421
  t428 = t75 * t426 / 0.24e2
  t437 = jnp.tanh(0.5e1 / 0.9e1 * (tau1 / t423 / r1 - t426 / 0.8e1) * t70 * t90)
  t439 = 0.3e1 / 0.5e1 * params.a0 * t437
  t442 = t428 + t439 - params.x0
  t444 = f.my_piecewise3(0.0e0 < t442, t442, 0)
  t445 = t444 ** (0.1e1 / 0.4e1)
  t448 = jnp.exp(-params.c / t445)
  t449 = f.my_piecewise3(params.x0 < t428 + t439, t448, 0)
  t452 = t428 - params.x0
  t454 = f.my_piecewise3(0.0e0 < t452, t452, 0)
  t455 = t454 ** (0.1e1 / 0.4e1)
  t458 = jnp.exp(-params.c / t455)
  t459 = f.my_piecewise3(params.x0 < t428, t458, 0)
  t460 = 0.1174e1 * t459
  t464 = 0.14821124361158432708688245315161839863713798977853e0 * t69 * (-0.1174e1 * t449 + t460) + 0.1174e1 - t460
  t473 = f.my_piecewise3(t397, 0, 0.4e1 / 0.9e1 * t408 * t404 + 0.4e1 / 0.3e1 * t398 * t411)
  t480 = f.my_piecewise3(t397, 0, 0.4e1 / 0.3e1 * t398 * t403)
  t486 = f.my_piecewise3(t397, t267, t398 * t396)
  t492 = f.my_piecewise3(t394, 0, -0.3e1 / 0.8e1 * t5 * t419 * t54 * t464 - 0.3e1 / 0.8e1 * t5 * t473 * t131 * t464 + t5 * t480 * t182 * t464 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t486 * t271 * t464)
  t494 = t19 ** 2
  t497 = t30 ** 2
  t503 = t41 ** 2
  t512 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t513 = f.my_piecewise5(t10, 0, t14, 0, t512)
  t517 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t494 * t497 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t503 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t513)
  t548 = t192 ** 2
  t552 = t196 ** 2
  t553 = t552 * t104
  t556 = t197 * t224
  t564 = t224 ** 2
  t565 = t564 * t104
  t570 = t157 * t335
  t581 = s0 / t78 / t200 / t76
  t583 = 0.2618e4 / 0.243e3 * t75 * t581
  t584 = t207 ** 2
  t588 = 0.1e1 / t312 / params.a0
  t594 = t314 * t219
  t607 = t219 ** 2
  t623 = f.my_piecewise3(t99, t583 + 0.4000e4 / 0.729e3 * t307 * t584 * t311 * t588 * t93 * t75 - 0.200e3 / 0.27e2 * t307 * t207 * t594 - 0.2000e4 / 0.729e3 * t146 * t93 * t147 * t584 * t75 * t588 * t311 + 0.400e3 / 0.27e2 * t317 * t207 * t594 - 0.10e2 / 0.9e1 * t206 * t607 * t213 - 0.40e2 / 0.27e2 * t322 * t212 * t56 * t330 + t147 * (0.6160e4 / 0.81e2 * tau0 * t303 - 0.2618e4 / 0.81e2 * t581) * t75 / 0.3e1, 0)
  t633 = t228 ** 2
  t639 = -0.585e3 / 0.256e3 * params.c / t101 / t548 * t553 + 0.135e3 / 0.32e2 * t288 * t556 + 0.255e3 / 0.256e3 * t228 / t229 / t548 * t553 - 0.15e2 / 0.16e2 * t195 * t565 - 0.45e2 / 0.32e2 * t298 * t556 - 0.5e1 / 0.4e1 * t195 * t570 - 0.15e2 / 0.128e3 * t341 / t343 / t548 * t553 + t139 * t623 * t104 / 0.4e1 + t232 * t570 / 0.4e1 + 0.3e1 / 0.16e2 * t232 * t565 + 0.3e1 / 0.32e2 * t346 * t556 + t633 / t548 / t100 * t553 / 0.256e3
  t640 = f.my_piecewise3(t97, t639, 0)
  t642 = t238 ** 2
  t646 = t242 ** 2
  t647 = t646 * t114
  t650 = t243 * t246
  t658 = t246 ** 2
  t659 = t658 * t114
  t664 = t166 * t368
  t672 = f.my_piecewise3(t109, t583, 0)
  t687 = -0.585e3 / 0.256e3 * params.c / t111 / t642 * t647 + 0.135e3 / 0.32e2 * t355 * t650 + 0.255e3 / 0.256e3 * t228 / t250 / t642 * t647 - 0.15e2 / 0.16e2 * t241 * t659 - 0.45e2 / 0.32e2 * t365 * t650 - 0.5e1 / 0.4e1 * t241 * t664 - 0.15e2 / 0.128e3 * t341 / t375 / t642 * t647 + t164 * t672 * t114 / 0.4e1 + t253 * t664 / 0.4e1 + 0.3e1 / 0.16e2 * t253 * t659 + 0.3e1 / 0.32e2 * t378 * t650 + t633 / t642 / t110 * t647 / 0.256e3
  t688 = f.my_piecewise3(t107, t687, 0)
  t689 = 0.1174e1 * t688
  t698 = 0.1e1 / t130 / t36
  t715 = -0.3e1 / 0.8e1 * t5 * t517 * t54 * t120 - 0.3e1 / 0.2e1 * t5 * t55 * t174 - 0.3e1 / 0.2e1 * t5 * t132 * t174 - 0.9e1 / 0.4e1 * t5 * t136 * t262 + t5 * t183 * t174 - 0.3e1 / 0.2e1 * t5 * t187 * t262 - 0.3e1 / 0.2e1 * t5 * t191 * t387 - 0.5e1 / 0.9e1 * t5 * t272 * t174 + t5 * t276 * t262 / 0.2e1 - t5 * t280 * t387 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t284 * (0.14821124361158432708688245315161839863713798977853e0 * t69 * (-0.1174e1 * t640 + t689) - t689) + 0.10e2 / 0.27e2 * t5 * t269 * t698 * t120 - t5 * t53 * t131 * t120 / 0.2e1 + t5 * t129 * t182 * t120 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t180 * t271 * t120
  t716 = f.my_piecewise3(t1, 0, t715)
  t717 = t396 ** 2
  t720 = t404 ** 2
  t726 = t411 ** 2
  t732 = f.my_piecewise5(t14, 0, t10, 0, -t512)
  t736 = f.my_piecewise3(t397, 0, 0.40e2 / 0.81e2 / t399 / t717 * t720 - 0.16e2 / 0.9e1 * t401 * t404 * t411 + 0.4e1 / 0.3e1 * t408 * t726 + 0.16e2 / 0.9e1 * t409 * t415 + 0.4e1 / 0.3e1 * t398 * t732)
  t758 = f.my_piecewise3(t394, 0, -0.3e1 / 0.8e1 * t5 * t736 * t54 * t464 - t5 * t419 * t131 * t464 / 0.2e1 + t5 * t473 * t182 * t464 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t480 * t271 * t464 + 0.10e2 / 0.27e2 * t5 * t486 * t698 * t464)
  d1111 = 0.4e1 * t392 + 0.4e1 * t492 + t6 * (t716 + t758)

  res = {'v4rho4': d1111}
  return res
