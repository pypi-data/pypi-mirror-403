"""Generated from mgga_x_r2scan.mpl."""

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
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
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
  params_dp2_raw = params.dp2
  if isinstance(params_dp2_raw, (str, bytes, dict)):
    params_dp2 = params_dp2_raw
  else:
    try:
      params_dp2_seq = list(params_dp2_raw)
    except TypeError:
      params_dp2 = params_dp2_raw
    else:
      params_dp2_seq = np.asarray(params_dp2_seq, dtype=np.float64)
      params_dp2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp2_seq))
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
  params_k1_raw = params.k1
  if isinstance(params_k1_raw, (str, bytes, dict)):
    params_k1 = params_k1_raw
  else:
    try:
      params_k1_seq = list(params_k1_raw)
    except TypeError:
      params_k1 = params_k1_raw
    else:
      params_k1_seq = np.asarray(params_k1_seq, dtype=np.float64)
      params_k1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k1_seq))

  params_c1 = 0.667
  params_dp2 = 0.361
  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  r2scan_alpha = lambda x, t: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  r2scan_f_alpha_neg = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  Cn = 20 / 27 + params_eta * 5 / 3

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  r2scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx)))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r2scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
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
  params_dp2_raw = params.dp2
  if isinstance(params_dp2_raw, (str, bytes, dict)):
    params_dp2 = params_dp2_raw
  else:
    try:
      params_dp2_seq = list(params_dp2_raw)
    except TypeError:
      params_dp2 = params_dp2_raw
    else:
      params_dp2_seq = np.asarray(params_dp2_seq, dtype=np.float64)
      params_dp2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp2_seq))
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
  params_k1_raw = params.k1
  if isinstance(params_k1_raw, (str, bytes, dict)):
    params_k1 = params_k1_raw
  else:
    try:
      params_k1_seq = list(params_k1_raw)
    except TypeError:
      params_k1 = params_k1_raw
    else:
      params_k1_seq = np.asarray(params_k1_seq, dtype=np.float64)
      params_k1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k1_seq))

  params_c1 = 0.667
  params_dp2 = 0.361
  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  r2scan_alpha = lambda x, t: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  r2scan_f_alpha_neg = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  Cn = 20 / 27 + params_eta * 5 / 3

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  r2scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx)))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r2scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
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
  params_dp2_raw = params.dp2
  if isinstance(params_dp2_raw, (str, bytes, dict)):
    params_dp2 = params_dp2_raw
  else:
    try:
      params_dp2_seq = list(params_dp2_raw)
    except TypeError:
      params_dp2 = params_dp2_raw
    else:
      params_dp2_seq = np.asarray(params_dp2_seq, dtype=np.float64)
      params_dp2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp2_seq))
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
  params_k1_raw = params.k1
  if isinstance(params_k1_raw, (str, bytes, dict)):
    params_k1 = params_k1_raw
  else:
    try:
      params_k1_seq = list(params_k1_raw)
    except TypeError:
      params_k1 = params_k1_raw
    else:
      params_k1_seq = np.asarray(params_k1_seq, dtype=np.float64)
      params_k1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k1_seq))

  params_c1 = 0.667
  params_dp2 = 0.361
  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  r2scan_alpha = lambda x, t: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  r2scan_f_alpha_neg = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  Cn = 20 / 27 + params_eta * 5 / 3

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  r2scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx)))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r2scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
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
  t29 = -0.12054978906212888888888888888888888888888888888889e0 - 0.27123702538979000000000000000000000000000000000000e0 * params.eta
  t30 = 6 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t36 = t31 / t33 / t32
  t37 = s0 ** 2
  t38 = r0 ** 2
  t39 = t38 ** 2
  t41 = r0 ** (0.1e1 / 0.3e1)
  t45 = params.dp2 ** 2
  t46 = t45 ** 2
  t47 = 0.1e1 / t46
  t51 = jnp.exp(-t36 * t37 / t41 / t39 / r0 * t47 / 0.576e3)
  t54 = (t29 * t51 + 0.10e2 / 0.81e2) * t30
  t55 = t33 ** 2
  t56 = 0.1e1 / t55
  t57 = t56 * s0
  t58 = t41 ** 2
  t60 = 0.1e1 / t58 / t38
  t64 = params.k1 + t54 * t57 * t60 / 0.24e2
  t68 = params.k1 * (0.1e1 - params.k1 / t64)
  t70 = 0.1e1 / t58 / r0
  t74 = tau0 * t70 - s0 * t60 / 0.8e1
  t76 = 0.3e1 / 0.10e2 * t31 * t55
  t77 = params.eta * s0
  t80 = t76 + t77 * t60 / 0.8e1
  t81 = 0.1e1 / t80
  t82 = t74 * t81
  t83 = t82 <= 0.0e0
  t84 = 0.0e0 < t82
  t85 = f.my_piecewise3(t84, 0, t82)
  t86 = params.c1 * t85
  t87 = 0.1e1 - t85
  t88 = 0.1e1 / t87
  t90 = jnp.exp(-t86 * t88)
  t91 = t82 <= 0.25e1
  t92 = 0.25e1 < t82
  t93 = f.my_piecewise3(t92, 0.25e1, t82)
  t95 = t93 ** 2
  t97 = t95 * t93
  t99 = t95 ** 2
  t101 = t99 * t93
  t103 = t99 * t95
  t108 = f.my_piecewise3(t92, t82, 0.25e1)
  t109 = 0.1e1 - t108
  t112 = jnp.exp(params.c2 / t109)
  t114 = f.my_piecewise5(t83, t90, t91, 0.1e1 - 0.667e0 * t93 - 0.4445555e0 * t95 - 0.663086601049e0 * t97 + 0.1451297044490e1 * t99 - 0.887998041597e0 * t101 + 0.234528941479e0 * t103 - 0.23185843322e-1 * t99 * t97, -params.d * t112)
  t115 = 0.174e0 - t68
  t117 = t114 * t115 + t68 + 0.1e1
  t119 = jnp.sqrt(0.3e1)
  t120 = 0.1e1 / t33
  t121 = t31 * t120
  t122 = jnp.sqrt(s0)
  t124 = 0.1e1 / t41 / r0
  t126 = t121 * t122 * t124
  t127 = jnp.sqrt(t126)
  t131 = jnp.exp(-0.98958e1 * t119 / t127)
  t132 = 0.1e1 - t131
  t133 = t27 * t117 * t132
  t136 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t133)
  t137 = r1 <= f.p.dens_threshold
  t138 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t139 = 0.1e1 + t138
  t140 = t139 <= f.p.zeta_threshold
  t141 = t139 ** (0.1e1 / 0.3e1)
  t143 = f.my_piecewise3(t140, t22, t141 * t139)
  t144 = t5 * t143
  t145 = s2 ** 2
  t146 = r1 ** 2
  t147 = t146 ** 2
  t149 = r1 ** (0.1e1 / 0.3e1)
  t156 = jnp.exp(-t36 * t145 / t149 / t147 / r1 * t47 / 0.576e3)
  t159 = (t29 * t156 + 0.10e2 / 0.81e2) * t30
  t160 = t56 * s2
  t161 = t149 ** 2
  t163 = 0.1e1 / t161 / t146
  t167 = params.k1 + t159 * t160 * t163 / 0.24e2
  t171 = params.k1 * (0.1e1 - params.k1 / t167)
  t173 = 0.1e1 / t161 / r1
  t177 = tau1 * t173 - s2 * t163 / 0.8e1
  t178 = params.eta * s2
  t181 = t76 + t178 * t163 / 0.8e1
  t182 = 0.1e1 / t181
  t183 = t177 * t182
  t184 = t183 <= 0.0e0
  t185 = 0.0e0 < t183
  t186 = f.my_piecewise3(t185, 0, t183)
  t187 = params.c1 * t186
  t188 = 0.1e1 - t186
  t189 = 0.1e1 / t188
  t191 = jnp.exp(-t187 * t189)
  t192 = t183 <= 0.25e1
  t193 = 0.25e1 < t183
  t194 = f.my_piecewise3(t193, 0.25e1, t183)
  t196 = t194 ** 2
  t198 = t196 * t194
  t200 = t196 ** 2
  t202 = t200 * t194
  t204 = t200 * t196
  t209 = f.my_piecewise3(t193, t183, 0.25e1)
  t210 = 0.1e1 - t209
  t213 = jnp.exp(params.c2 / t210)
  t215 = f.my_piecewise5(t184, t191, t192, 0.1e1 - 0.667e0 * t194 - 0.4445555e0 * t196 - 0.663086601049e0 * t198 + 0.1451297044490e1 * t200 - 0.887998041597e0 * t202 + 0.234528941479e0 * t204 - 0.23185843322e-1 * t200 * t198, -params.d * t213)
  t216 = 0.174e0 - t171
  t218 = t215 * t216 + t171 + 0.1e1
  t220 = jnp.sqrt(s2)
  t222 = 0.1e1 / t149 / r1
  t224 = t121 * t220 * t222
  t225 = jnp.sqrt(t224)
  t229 = jnp.exp(-0.98958e1 * t119 / t225)
  t230 = 0.1e1 - t229
  t231 = t27 * t218 * t230
  t234 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t144 * t231)
  t235 = t6 ** 2
  t237 = t16 / t235
  t238 = t7 - t237
  t239 = f.my_piecewise5(t10, 0, t14, 0, t238)
  t242 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t239)
  t246 = t27 ** 2
  t247 = 0.1e1 / t246
  t251 = t26 * t247 * t117 * t132 / 0.8e1
  t252 = params.k1 ** 2
  t253 = t64 ** 2
  t254 = 0.1e1 / t253
  t255 = t252 * t254
  t256 = t32 ** 2
  t258 = t29 / t256
  t261 = t39 ** 2
  t270 = 0.1e1 / t58 / t38 / r0
  t274 = t258 * t37 * s0 / t261 / r0 * t47 * t51 / 0.432e3 - t54 * t57 * t270 / 0.9e1
  t282 = t80 ** 2
  t284 = t74 / t282
  t288 = (-0.5e1 / 0.3e1 * tau0 * t60 + s0 * t270 / 0.3e1) * t81 + t284 * t77 * t270 / 0.3e1
  t289 = f.my_piecewise3(t84, 0, t288)
  t292 = t87 ** 2
  t293 = 0.1e1 / t292
  t298 = f.my_piecewise3(t92, 0, t288)
  t313 = params.d * params.c2
  t314 = t109 ** 2
  t315 = 0.1e1 / t314
  t316 = f.my_piecewise3(t92, t288, 0)
  t320 = f.my_piecewise5(t83, (-t86 * t293 * t289 - params.c1 * t289 * t88) * t90, t91, -0.667e0 * t298 - 0.8891110e0 * t93 * t298 - 0.1989259803147e1 * t95 * t298 + 0.5805188177960e1 * t97 * t298 - 0.4439990207985e1 * t99 * t298 + 0.1407173648874e1 * t101 * t298 - 0.162300903254e0 * t103 * t298, -t313 * t315 * t316 * t112)
  t322 = t114 * t252
  t330 = 3 ** (0.1e1 / 0.6e1)
  t331 = t330 ** 2
  t332 = t331 ** 2
  t334 = t332 * t330 * t4
  t337 = t334 * t25 * t27 * t117
  t341 = 0.1e1 / t127 / t126 * t31 * t120
  t350 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t242 * t133 - t251 - 0.3e1 / 0.8e1 * t26 * t27 * (-t322 * t254 * t274 + t320 * t115 + t255 * t274) * t132 - 0.24739500000000000000000000000000000000000000000000e1 * t337 * t341 * t122 / t41 / t38 * t131)
  t352 = f.my_piecewise5(t14, 0, t10, 0, -t238)
  t355 = f.my_piecewise3(t140, 0, 0.4e1 / 0.3e1 * t141 * t352)
  t362 = t144 * t247 * t218 * t230 / 0.8e1
  t364 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t5 * t355 * t231 - t362)
  vrho_0_ = t136 + t234 + t6 * (t350 + t364)
  t367 = -t7 - t237
  t368 = f.my_piecewise5(t10, 0, t14, 0, t367)
  t371 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t368)
  t376 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t371 * t133 - t251)
  t378 = f.my_piecewise5(t14, 0, t10, 0, -t367)
  t381 = f.my_piecewise3(t140, 0, 0.4e1 / 0.3e1 * t141 * t378)
  t385 = t167 ** 2
  t386 = 0.1e1 / t385
  t387 = t252 * t386
  t390 = t147 ** 2
  t399 = 0.1e1 / t161 / t146 / r1
  t403 = t258 * t145 * s2 / t390 / r1 * t47 * t156 / 0.432e3 - t159 * t160 * t399 / 0.9e1
  t411 = t181 ** 2
  t413 = t177 / t411
  t417 = (-0.5e1 / 0.3e1 * tau1 * t163 + s2 * t399 / 0.3e1) * t182 + t413 * t178 * t399 / 0.3e1
  t418 = f.my_piecewise3(t185, 0, t417)
  t421 = t188 ** 2
  t422 = 0.1e1 / t421
  t427 = f.my_piecewise3(t193, 0, t417)
  t442 = t210 ** 2
  t443 = 0.1e1 / t442
  t444 = f.my_piecewise3(t193, t417, 0)
  t448 = f.my_piecewise5(t184, (-t187 * t422 * t418 - params.c1 * t418 * t189) * t191, t192, -0.667e0 * t427 - 0.8891110e0 * t194 * t427 - 0.1989259803147e1 * t196 * t427 + 0.5805188177960e1 * t198 * t427 - 0.4439990207985e1 * t200 * t427 + 0.1407173648874e1 * t202 * t427 - 0.162300903254e0 * t204 * t427, -t313 * t443 * t444 * t213)
  t450 = t215 * t252
  t460 = t334 * t143 * t27 * t218
  t464 = 0.1e1 / t225 / t224 * t31 * t120
  t473 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t5 * t381 * t231 - t362 - 0.3e1 / 0.8e1 * t144 * t27 * (-t450 * t386 * t403 + t448 * t216 + t387 * t403) * t230 - 0.24739500000000000000000000000000000000000000000000e1 * t460 * t464 * t220 / t149 / t146 * t229)
  vrho_1_ = t136 + t234 + t6 * (t376 + t473)
  t485 = -t258 * t37 / t261 * t47 * t51 / 0.1152e4 + t54 * t56 * t60 / 0.24e2
  t491 = -t284 * params.eta * t60 / 0.8e1 - t60 * t81 / 0.8e1
  t492 = f.my_piecewise3(t84, 0, t491)
  t499 = f.my_piecewise3(t92, 0, t491)
  t514 = f.my_piecewise3(t92, t491, 0)
  t518 = f.my_piecewise5(t83, (-t86 * t293 * t492 - params.c1 * t492 * t88) * t90, t91, -0.667e0 * t499 - 0.8891110e0 * t93 * t499 - 0.1989259803147e1 * t95 * t499 + 0.5805188177960e1 * t97 * t499 - 0.4439990207985e1 * t99 * t499 + 0.1407173648874e1 * t101 * t499 - 0.162300903254e0 * t103 * t499, -t313 * t315 * t514 * t112)
  t534 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (-t322 * t254 * t485 + t518 * t115 + t255 * t485) * t132 + 0.92773125000000000000000000000000000000000000000000e0 * t337 * t341 / t122 * t124 * t131)
  vsigma_0_ = t6 * t534
  vsigma_1_ = 0.0e0
  t544 = -t258 * t145 / t390 * t47 * t156 / 0.1152e4 + t159 * t56 * t163 / 0.24e2
  t550 = -t413 * params.eta * t163 / 0.8e1 - t163 * t182 / 0.8e1
  t551 = f.my_piecewise3(t185, 0, t550)
  t558 = f.my_piecewise3(t193, 0, t550)
  t573 = f.my_piecewise3(t193, t550, 0)
  t577 = f.my_piecewise5(t184, (-t187 * t422 * t551 - params.c1 * t551 * t189) * t191, t192, -0.667e0 * t558 - 0.8891110e0 * t194 * t558 - 0.1989259803147e1 * t196 * t558 + 0.5805188177960e1 * t198 * t558 - 0.4439990207985e1 * t200 * t558 + 0.1407173648874e1 * t202 * t558 - 0.162300903254e0 * t204 * t558, -t313 * t443 * t573 * t213)
  t593 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t144 * t27 * (-t450 * t386 * t544 + t577 * t216 + t387 * t544) * t230 + 0.92773125000000000000000000000000000000000000000000e0 * t460 * t464 / t220 * t222 * t229)
  vsigma_2_ = t6 * t593
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t594 = t70 * t81
  t595 = f.my_piecewise3(t84, 0, t594)
  t602 = f.my_piecewise3(t92, 0, t594)
  t617 = f.my_piecewise3(t92, t594, 0)
  t621 = f.my_piecewise5(t83, (-t86 * t293 * t595 - params.c1 * t595 * t88) * t90, t91, -0.667e0 * t602 - 0.8891110e0 * t93 * t602 - 0.1989259803147e1 * t95 * t602 + 0.5805188177960e1 * t97 * t602 - 0.4439990207985e1 * t99 * t602 + 0.1407173648874e1 * t101 * t602 - 0.162300903254e0 * t103 * t602, -t313 * t315 * t617 * t112)
  t627 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * t621 * t115 * t132)
  vtau_0_ = t6 * t627
  t628 = t173 * t182
  t629 = f.my_piecewise3(t185, 0, t628)
  t636 = f.my_piecewise3(t193, 0, t628)
  t651 = f.my_piecewise3(t193, t628, 0)
  t655 = f.my_piecewise5(t184, (-t187 * t422 * t629 - params.c1 * t629 * t189) * t191, t192, -0.667e0 * t636 - 0.8891110e0 * t194 * t636 - 0.1989259803147e1 * t196 * t636 + 0.5805188177960e1 * t198 * t636 - 0.4439990207985e1 * t200 * t636 + 0.1407173648874e1 * t202 * t636 - 0.162300903254e0 * t204 * t636, -t313 * t443 * t651 * t213)
  t661 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t144 * t27 * t655 * t216 * t230)
  vtau_1_ = t6 * t661
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
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
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
  params_dp2_raw = params.dp2
  if isinstance(params_dp2_raw, (str, bytes, dict)):
    params_dp2 = params_dp2_raw
  else:
    try:
      params_dp2_seq = list(params_dp2_raw)
    except TypeError:
      params_dp2 = params_dp2_raw
    else:
      params_dp2_seq = np.asarray(params_dp2_seq, dtype=np.float64)
      params_dp2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_dp2_seq))
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
  params_k1_raw = params.k1
  if isinstance(params_k1_raw, (str, bytes, dict)):
    params_k1 = params_k1_raw
  else:
    try:
      params_k1_seq = list(params_k1_raw)
    except TypeError:
      params_k1 = params_k1_raw
    else:
      params_k1_seq = np.asarray(params_k1_seq, dtype=np.float64)
      params_k1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_k1_seq))

  params_c1 = 0.667
  params_dp2 = 0.361
  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  r2scan_alpha = lambda x, t: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  r2scan_f_alpha_neg = lambda a: jnp.exp(-params_c1 * a / (1 - a))

  Cn = 20 / 27 + params_eta * 5 / 3

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  C2 = lambda ff: -jnp.sum(jnp.array([i * ff[9 - i] for i in range(1, 8 + 1)]), axis=0) * (1 - scan_h0x)

  r2scan_f_alpha = lambda a, ff: f.my_piecewise5(a <= 0, r2scan_f_alpha_neg(jnp.minimum(a, 0)), a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  r2scan_x = lambda p, ff: (Cn * C2(ff) * jnp.exp(-p ** 2 / params_dp2 ** 4) + MU_GE) * p

  r2scan_f = lambda x, u, t: (scan_h1x(r2scan_x(scan_p(x), rscan_fx)) + r2scan_f_alpha(r2scan_alpha(x, t), rscan_fx) * (scan_h0x - scan_h1x(r2scan_x(scan_p(x), rscan_fx)))) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, r2scan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 * t5 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t21 = -0.12054978906212888888888888888888888888888888888889e0 - 0.27123702538979000000000000000000000000000000000000e0 * params.eta
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t29 = s0 ** 2
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = r0 ** 2
  t33 = t32 ** 2
  t38 = params.dp2 ** 2
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t44 = jnp.exp(-t23 / t25 / t24 * t29 * t31 / t19 / t33 / r0 * t40 / 0.288e3)
  t47 = (t21 * t44 + 0.10e2 / 0.81e2) * t22
  t48 = t25 ** 2
  t49 = 0.1e1 / t48
  t50 = t47 * t49
  t51 = t31 ** 2
  t52 = s0 * t51
  t53 = t19 ** 2
  t55 = 0.1e1 / t53 / t32
  t56 = t52 * t55
  t59 = params.k1 + t50 * t56 / 0.24e2
  t63 = params.k1 * (0.1e1 - params.k1 / t59)
  t64 = tau0 * t51
  t66 = 0.1e1 / t53 / r0
  t69 = t64 * t66 - t56 / 0.8e1
  t73 = t51 * t55
  t76 = 0.3e1 / 0.10e2 * t23 * t48 + params.eta * s0 * t73 / 0.8e1
  t77 = 0.1e1 / t76
  t78 = t69 * t77
  t79 = t78 <= 0.0e0
  t80 = 0.0e0 < t78
  t81 = f.my_piecewise3(t80, 0, t78)
  t82 = params.c1 * t81
  t83 = 0.1e1 - t81
  t84 = 0.1e1 / t83
  t86 = jnp.exp(-t82 * t84)
  t87 = t78 <= 0.25e1
  t88 = 0.25e1 < t78
  t89 = f.my_piecewise3(t88, 0.25e1, t78)
  t91 = t89 ** 2
  t93 = t91 * t89
  t95 = t91 ** 2
  t97 = t95 * t89
  t99 = t95 * t91
  t104 = f.my_piecewise3(t88, t78, 0.25e1)
  t105 = 0.1e1 - t104
  t108 = jnp.exp(params.c2 / t105)
  t110 = f.my_piecewise5(t79, t86, t87, 0.1e1 - 0.667e0 * t89 - 0.4445555e0 * t91 - 0.663086601049e0 * t93 + 0.1451297044490e1 * t95 - 0.887998041597e0 * t97 + 0.234528941479e0 * t99 - 0.23185843322e-1 * t95 * t93, -params.d * t108)
  t111 = 0.174e0 - t63
  t113 = t110 * t111 + t63 + 0.1e1
  t115 = jnp.sqrt(0.3e1)
  t116 = 0.1e1 / t25
  t118 = jnp.sqrt(s0)
  t119 = t118 * t31
  t123 = t23 * t116 * t119 / t19 / r0
  t124 = jnp.sqrt(t123)
  t128 = jnp.exp(-0.98958e1 * t115 / t124)
  t129 = 0.1e1 - t128
  t133 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t113 * t129)
  t139 = params.k1 ** 2
  t140 = t59 ** 2
  t141 = 0.1e1 / t140
  t142 = t139 * t141
  t143 = t24 ** 2
  t145 = t21 / t143
  t148 = t33 ** 2
  t158 = t52 / t53 / t32 / r0
  t161 = t145 * t29 * s0 / t148 / r0 * t40 * t44 / 0.108e3 - t50 * t158 / 0.9e1
  t168 = t76 ** 2
  t170 = t69 / t168
  t174 = (-0.5e1 / 0.3e1 * t64 * t55 + t158 / 0.3e1) * t77 + t170 * params.eta * t158 / 0.3e1
  t175 = f.my_piecewise3(t80, 0, t174)
  t178 = t83 ** 2
  t179 = 0.1e1 / t178
  t184 = f.my_piecewise3(t88, 0, t174)
  t199 = params.d * params.c2
  t200 = t105 ** 2
  t201 = 0.1e1 / t200
  t202 = f.my_piecewise3(t88, t174, 0)
  t206 = f.my_piecewise5(t79, (-t82 * t179 * t175 - params.c1 * t175 * t84) * t86, t87, -0.667e0 * t184 - 0.8891110e0 * t89 * t184 - 0.1989259803147e1 * t91 * t184 + 0.5805188177960e1 * t93 * t184 - 0.4439990207985e1 * t95 * t184 + 0.1407173648874e1 * t97 * t184 - 0.162300903254e0 * t99 * t184, -t199 * t201 * t202 * t108)
  t208 = t110 * t139
  t216 = 3 ** (0.1e1 / 0.6e1)
  t217 = t216 ** 2
  t218 = t217 ** 2
  t220 = t218 * t216 * t5
  t228 = 0.1e1 / t124 / t123 * t23 * t116
  t234 = f.my_piecewise3(t2, 0, -t18 / t53 * t113 * t129 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (-t208 * t141 * t161 + t206 * t111 + t142 * t161) * t129 - 0.24739500000000000000000000000000000000000000000000e1 * t220 * t17 / t32 * t113 * t228 * t119 * t128)
  vrho_0_ = 0.2e1 * r0 * t234 + 0.2e1 * t133
  t247 = -t145 * t29 / t148 * t40 * t44 / 0.288e3 + t47 * t49 * t51 * t55 / 0.24e2
  t254 = -t170 * params.eta * t51 * t55 / 0.8e1 - t73 * t77 / 0.8e1
  t255 = f.my_piecewise3(t80, 0, t254)
  t262 = f.my_piecewise3(t88, 0, t254)
  t277 = f.my_piecewise3(t88, t254, 0)
  t281 = f.my_piecewise5(t79, (-t82 * t179 * t255 - params.c1 * t255 * t84) * t86, t87, -0.667e0 * t262 - 0.8891110e0 * t89 * t262 - 0.1989259803147e1 * t91 * t262 + 0.5805188177960e1 * t93 * t262 - 0.4439990207985e1 * t95 * t262 + 0.1407173648874e1 * t97 * t262 - 0.162300903254e0 * t99 * t262, -t199 * t201 * t277 * t108)
  t301 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (-t208 * t141 * t247 + t281 * t111 + t142 * t247) * t129 + 0.92773125000000000000000000000000000000000000000000e0 * t220 * t17 / r0 * t113 * t228 / t118 * t31 * t128)
  vsigma_0_ = 0.2e1 * r0 * t301
  vlapl_0_ = 0.0e0
  t304 = t51 * t66 * t77
  t305 = f.my_piecewise3(t80, 0, t304)
  t312 = f.my_piecewise3(t88, 0, t304)
  t327 = f.my_piecewise3(t88, t304, 0)
  t331 = f.my_piecewise5(t79, (-t82 * t179 * t305 - params.c1 * t305 * t84) * t86, t87, -0.667e0 * t312 - 0.8891110e0 * t89 * t312 - 0.1989259803147e1 * t91 * t312 + 0.5805188177960e1 * t93 * t312 - 0.4439990207985e1 * t95 * t312 + 0.1407173648874e1 * t97 * t312 - 0.162300903254e0 * t99 * t312, -t199 * t201 * t327 * t108)
  t337 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t331 * t111 * t129)
  vtau_0_ = 0.2e1 * r0 * t337
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
  t5 = 0.1e1 / t4
  t6 = t3 * t5
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
  t23 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t27 / t26
  t31 = s0 ** 2
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = r0 ** 2
  t35 = t34 ** 2
  t36 = t35 * r0
  t38 = 0.1e1 / t19 / t36
  t39 = t33 * t38
  t40 = params.dp2 ** 2
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t46 = jnp.exp(-t25 * t29 * t31 * t39 * t42 / 0.288e3)
  t50 = (-0.162742215233874e0 * t23 * t46 + 0.10e2 / 0.81e2) * t24
  t51 = t27 ** 2
  t52 = 0.1e1 / t51
  t53 = t50 * t52
  t54 = t33 ** 2
  t55 = s0 * t54
  t57 = 0.1e1 / t20 / t34
  t58 = t55 * t57
  t61 = params.k1 + t53 * t58 / 0.24e2
  t65 = params.k1 * (0.1e1 - params.k1 / t61)
  t66 = tau0 * t54
  t67 = t20 * r0
  t68 = 0.1e1 / t67
  t71 = t66 * t68 - t58 / 0.8e1
  t75 = t54 * t57
  t78 = 0.3e1 / 0.10e2 * t25 * t51 + params.eta * s0 * t75 / 0.8e1
  t79 = 0.1e1 / t78
  t80 = t71 * t79
  t81 = t80 <= 0.0e0
  t82 = 0.0e0 < t80
  t83 = f.my_piecewise3(t82, 0, t80)
  t84 = params.c1 * t83
  t85 = 0.1e1 - t83
  t86 = 0.1e1 / t85
  t88 = jnp.exp(-t84 * t86)
  t89 = t80 <= 0.25e1
  t90 = 0.25e1 < t80
  t91 = f.my_piecewise3(t90, 0.25e1, t80)
  t93 = t91 ** 2
  t95 = t93 * t91
  t97 = t93 ** 2
  t99 = t97 * t91
  t101 = t97 * t93
  t106 = f.my_piecewise3(t90, t80, 0.25e1)
  t107 = 0.1e1 - t106
  t110 = jnp.exp(params.c2 / t107)
  t112 = f.my_piecewise5(t81, t88, t89, 0.1e1 - 0.667e0 * t91 - 0.4445555e0 * t93 - 0.663086601049e0 * t95 + 0.1451297044490e1 * t97 - 0.887998041597e0 * t99 + 0.234528941479e0 * t101 - 0.23185843322e-1 * t97 * t95, -params.d * t110)
  t113 = 0.174e0 - t65
  t115 = t112 * t113 + t65 + 0.1e1
  t117 = jnp.sqrt(0.3e1)
  t118 = 0.1e1 / t27
  t120 = jnp.sqrt(s0)
  t121 = t120 * t33
  t125 = t25 * t118 * t121 / t19 / r0
  t126 = jnp.sqrt(t125)
  t130 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t117 / t126)
  t131 = 0.1e1 - t130
  t135 = params.k1 ** 2
  t136 = t61 ** 2
  t137 = 0.1e1 / t136
  t138 = t135 * t137
  t139 = t26 ** 2
  t141 = t23 / t139
  t142 = t31 * s0
  t143 = t141 * t142
  t144 = t35 ** 2
  t148 = 0.1e1 / t144 / r0 * t42 * t46
  t151 = t34 * r0
  t153 = 0.1e1 / t20 / t151
  t154 = t55 * t153
  t157 = -0.15068723632766111111111111111111111111111111111111e-2 * t143 * t148 - t53 * t154 / 0.9e1
  t162 = -0.5e1 / 0.3e1 * t66 * t57 + t154 / 0.3e1
  t164 = t78 ** 2
  t165 = 0.1e1 / t164
  t166 = t71 * t165
  t167 = t166 * params.eta
  t170 = t162 * t79 + t167 * t154 / 0.3e1
  t171 = f.my_piecewise3(t82, 0, t170)
  t174 = t85 ** 2
  t175 = 0.1e1 / t174
  t176 = t175 * t171
  t178 = -params.c1 * t171 * t86 - t84 * t176
  t180 = f.my_piecewise3(t90, 0, t170)
  t195 = params.d * params.c2
  t196 = t107 ** 2
  t197 = 0.1e1 / t196
  t198 = f.my_piecewise3(t90, t170, 0)
  t202 = f.my_piecewise5(t81, t178 * t88, t89, -0.667e0 * t180 - 0.8891110e0 * t91 * t180 - 0.1989259803147e1 * t93 * t180 + 0.5805188177960e1 * t95 * t180 - 0.4439990207985e1 * t97 * t180 + 0.1407173648874e1 * t99 * t180 - 0.162300903254e0 * t101 * t180, -t195 * t197 * t198 * t110)
  t204 = t112 * t135
  t205 = t137 * t157
  t207 = t202 * t113 + t138 * t157 - t204 * t205
  t212 = 3 ** (0.1e1 / 0.6e1)
  t213 = t212 ** 2
  t214 = t213 ** 2
  t216 = t214 * t212 * t5
  t217 = 0.1e1 / t34
  t218 = t17 * t217
  t220 = t216 * t218 * t115
  t224 = 0.1e1 / t126 / t125 * t25 * t118
  t226 = t224 * t121 * t130
  t230 = f.my_piecewise3(t2, 0, -t18 * t21 * t115 * t131 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t207 * t131 - 0.24739500000000000000000000000000000000000000000000e1 * t220 * t226)
  t247 = 0.1e1 / t136 / t61
  t248 = t135 * t247
  t249 = t157 ** 2
  t258 = t31 ** 2
  t260 = t35 * t151
  t266 = t41 ** 2
  t271 = 0.1e1 / t266 * t25 * t29 * t33 * t46
  t276 = t55 / t20 / t35
  t279 = 0.17580177571560462962962962962962962962962962962963e-1 * t143 / t144 / t34 * t42 * t46 - 0.27905043764381687242798353909465020576131687242798e-4 * t141 * t258 * s0 / t19 / t144 / t260 * t271 + 0.11e2 / 0.27e2 * t53 * t276
  t286 = t162 * t165
  t292 = t71 / t164 / t78
  t293 = params.eta ** 2
  t294 = t292 * t293
  t303 = (0.40e2 / 0.9e1 * t66 * t153 - 0.11e2 / 0.9e1 * t276) * t79 + 0.2e1 / 0.3e1 * t286 * params.eta * t154 + 0.4e1 / 0.9e1 * t294 * t31 * t33 / t19 / t260 - 0.11e2 / 0.9e1 * t167 * t276
  t304 = f.my_piecewise3(t82, 0, t303)
  t307 = t171 ** 2
  t312 = 0.1e1 / t174 / t85
  t320 = t178 ** 2
  t323 = f.my_piecewise3(t90, 0, t303)
  t325 = t180 ** 2
  t349 = -0.667e0 * t323 - 0.8891110e0 * t325 - 0.8891110e0 * t91 * t323 - 0.3978519606294e1 * t91 * t325 - 0.1989259803147e1 * t93 * t323 + 0.17415564533880e2 * t93 * t325 + 0.5805188177960e1 * t95 * t323 - 0.17759960831940e2 * t95 * t325 - 0.4439990207985e1 * t97 * t323 + 0.7035868244370e1 * t97 * t325 + 0.1407173648874e1 * t99 * t323 - 0.973805419524e0 * t99 * t325 - 0.162300903254e0 * t101 * t323
  t351 = 0.1e1 / t196 / t107
  t352 = t198 ** 2
  t357 = f.my_piecewise3(t90, t303, 0)
  t361 = params.c2 ** 2
  t362 = params.d * t361
  t363 = t196 ** 2
  t364 = 0.1e1 / t363
  t369 = f.my_piecewise5(t81, (-t84 * t175 * t304 - 0.2e1 * params.c1 * t307 * t175 - params.c1 * t304 * t86 - 0.2e1 * t84 * t312 * t307) * t88 + t320 * t88, t89, t349, -t195 * t197 * t357 * t110 - 0.2e1 * t195 * t351 * t352 * t110 - t362 * t364 * t352 * t110)
  t371 = t202 * t135
  t389 = 0.1e1 / t19 / t35
  t398 = 0.1e1 / t126 / t52 / t58 / 0.6e1
  t399 = t398 * t52
  t404 = t4 ** 2
  t406 = t3 * t404 * jnp.pi
  t411 = 0.1e1 / t120
  t413 = t52 * t54
  t414 = t413 * t130
  t419 = f.my_piecewise3(t2, 0, t18 * t68 * t115 * t131 / 0.12e2 - t18 * t21 * t207 * t131 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t216 * t17 / t151 * t115 * t226 - 0.3e1 / 0.8e1 * t18 * t19 * (-t204 * t137 * t279 + 0.2e1 * t204 * t247 * t249 + t369 * t113 + t138 * t279 - 0.2e1 * t371 * t205 - 0.2e1 * t248 * t249) * t131 - 0.49479000000000000000000000000000000000000000000000e1 * t216 * t218 * t207 * t226 - 0.29687400000000000000000000000000000000000000000000e2 * t216 * t17 * t389 * t115 * t399 * t55 * t130 + 0.40802857350000000000000000000000000000000000000000e1 * t406 * t17 / t19 * t115 * t411 * t24 * t414)
  v2rho2_0_ = 0.2e1 * r0 * t419 + 0.4e1 * t230
  t422 = t141 * t31
  t425 = 0.1e1 / t144 * t42 * t46
  t431 = 0.56507713622872916666666666666666666666666666666667e-3 * t422 * t425 + t50 * t413 * t57 / 0.24e2
  t433 = t75 * t79
  t434 = params.eta * t54
  t435 = t434 * t57
  t438 = -t166 * t435 / 0.8e1 - t433 / 0.8e1
  t439 = f.my_piecewise3(t82, 0, t438)
  t440 = params.c1 * t439
  t442 = t175 * t439
  t444 = -t440 * t86 - t84 * t442
  t446 = f.my_piecewise3(t90, 0, t438)
  t448 = t91 * t446
  t450 = t93 * t446
  t452 = t95 * t446
  t454 = t97 * t446
  t456 = t99 * t446
  t461 = f.my_piecewise3(t90, t438, 0)
  t465 = f.my_piecewise5(t81, t444 * t88, t89, -0.667e0 * t446 - 0.8891110e0 * t448 - 0.1989259803147e1 * t450 + 0.5805188177960e1 * t452 - 0.4439990207985e1 * t454 + 0.1407173648874e1 * t456 - 0.162300903254e0 * t101 * t446, -t195 * t197 * t461 * t110)
  t467 = t137 * t431
  t469 = t465 * t113 + t138 * t431 - t204 * t467
  t474 = 0.1e1 / r0
  t475 = t17 * t474
  t477 = t216 * t475 * t115
  t480 = t224 * t411 * t33 * t130
  t484 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t469 * t131 + 0.92773125000000000000000000000000000000000000000000e0 * t477 * t480)
  t494 = t35 * t34
  t505 = -0.60274894531064444444444444444444444444444444444445e-2 * t422 * t148 + 0.10464391411643132716049382716049382716049382716049e-4 * t141 * t258 / t19 / t144 / t494 * t271 - t50 * t413 * t153 / 0.9e1
  t512 = t33 / t19 / t494
  t513 = t165 * params.eta
  t514 = t513 * s0
  t525 = t54 * t153 * t79 / 0.3e1 - t512 * t514 / 0.12e2 - t286 * t435 / 0.8e1 - t294 * t512 * s0 / 0.6e1 + t166 * t434 * t153 / 0.3e1
  t526 = f.my_piecewise3(t82, 0, t525)
  t542 = f.my_piecewise3(t90, 0, t525)
  t568 = -0.667e0 * t542 - 0.8891110e0 * t180 * t446 - 0.8891110e0 * t91 * t542 - 0.3978519606294e1 * t448 * t180 - 0.1989259803147e1 * t93 * t542 + 0.17415564533880e2 * t450 * t180 + 0.5805188177960e1 * t95 * t542 - 0.17759960831940e2 * t452 * t180 - 0.4439990207985e1 * t97 * t542 + 0.7035868244370e1 * t454 * t180 + 0.1407173648874e1 * t99 * t542 - 0.973805419524e0 * t456 * t180 - 0.162300903254e0 * t101 * t542
  t569 = t195 * t351
  t571 = t461 * t110 * t198
  t574 = f.my_piecewise3(t90, t525, 0)
  t578 = t362 * t364
  t581 = f.my_piecewise5(t81, (-0.2e1 * t84 * t312 * t439 * t171 - t84 * t175 * t526 - params.c1 * t526 * t86 - 0.2e1 * t440 * t176) * t88 + t444 * t178 * t88, t89, t568, -t195 * t197 * t574 * t110 - 0.2e1 * t569 * t571 - t578 * t571)
  t583 = t465 * t135
  t619 = 0.1e1 / t120 / s0
  t625 = f.my_piecewise3(t2, 0, -t18 * t21 * t469 * t131 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (0.2e1 * t204 * t247 * t431 * t157 - t204 * t137 * t505 - 0.2e1 * t248 * t431 * t157 + t581 * t113 + t138 * t505 - t583 * t205 - t371 * t467) * t131 - 0.24739500000000000000000000000000000000000000000000e1 * t216 * t218 * t469 * t226 - 0.92773125000000000000000000000000000000000000000000e0 * t220 * t480 + 0.92773125000000000000000000000000000000000000000000e0 * t216 * t475 * t207 * t480 + 0.11132775000000000000000000000000000000000000000000e2 * t216 * t17 / t19 / t151 * t115 * t398 * t414 - 0.15301071506250000000000000000000000000000000000000e1 * t406 * t17 * t20 * t115 * t619 * t24 * t414)
  v2rhosigma_0_ = 0.2e1 * r0 * t625 + 0.2e1 * t484
  t628 = t431 ** 2
  t641 = 0.16952314086861875000000000000000000000000000000000e-2 * t141 * s0 * t425 - 0.39241467793661747685185185185185185185185185185185e-5 * t141 * t142 / t19 / t144 / t36 * t271
  t648 = t292 * t293 * t33 * t38 / 0.16e2 + t39 * t513 / 0.16e2
  t649 = f.my_piecewise3(t82, 0, t648)
  t652 = t439 ** 2
  t663 = t444 ** 2
  t666 = f.my_piecewise3(t90, 0, t648)
  t668 = t446 ** 2
  t692 = -0.667e0 * t666 - 0.8891110e0 * t668 - 0.8891110e0 * t91 * t666 - 0.3978519606294e1 * t91 * t668 - 0.1989259803147e1 * t93 * t666 + 0.17415564533880e2 * t93 * t668 + 0.5805188177960e1 * t95 * t666 - 0.17759960831940e2 * t95 * t668 - 0.4439990207985e1 * t97 * t666 + 0.7035868244370e1 * t97 * t668 + 0.1407173648874e1 * t99 * t666 - 0.973805419524e0 * t99 * t668 - 0.162300903254e0 * t101 * t666
  t693 = t461 ** 2
  t698 = f.my_piecewise3(t90, t648, 0)
  t706 = f.my_piecewise5(t81, (-t84 * t175 * t649 - 0.2e1 * params.c1 * t652 * t175 - 0.2e1 * t84 * t312 * t652 - params.c1 * t649 * t86) * t88 + t663 * t88, t89, t692, -t195 * t197 * t698 * t110 - 0.2e1 * t195 * t351 * t693 * t110 - t362 * t364 * t693 * t110)
  t750 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (-t204 * t137 * t641 + 0.2e1 * t204 * t247 * t628 + t706 * t113 + t138 * t641 - 0.2e1 * t248 * t628 - 0.2e1 * t583 * t467) * t131 + 0.18554625000000000000000000000000000000000000000000e1 * t216 * t475 * t469 * t480 - 0.41747906250000000000000000000000000000000000000000e1 * t216 * t17 / t19 / t34 * t115 * t399 / s0 * t54 * t130 - 0.46386562500000000000000000000000000000000000000000e0 * t477 * t224 * t619 * t33 * t130 + 0.57379018148437500000000000000000000000000000000000e0 * t406 * t17 * t67 * t115 / t120 / t31 * t24 * t414)
  v2sigma2_0_ = 0.2e1 * r0 * t750
  v2rholapl_0_ = 0.0e0
  v2sigmalapl_0_ = 0.0e0
  v2lapl2_0_ = 0.0e0
  t753 = t54 * t68 * t79
  t754 = f.my_piecewise3(t82, 0, t753)
  t755 = params.c1 * t754
  t759 = -t84 * t175 * t754 - t755 * t86
  t761 = f.my_piecewise3(t90, 0, t753)
  t763 = t91 * t761
  t765 = t93 * t761
  t767 = t95 * t761
  t769 = t97 * t761
  t771 = t99 * t761
  t776 = f.my_piecewise3(t90, t753, 0)
  t780 = f.my_piecewise5(t81, t759 * t88, t89, -0.667e0 * t761 - 0.8891110e0 * t763 - 0.1989259803147e1 * t765 + 0.5805188177960e1 * t767 - 0.4439990207985e1 * t769 + 0.1407173648874e1 * t771 - 0.162300903254e0 * t101 * t761, -t195 * t197 * t776 * t110)
  t782 = t113 * t131
  t786 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t780 * t782)
  t794 = -0.5e1 / 0.3e1 * t433 + 0.2e1 / 0.3e1 * t39 * t514
  t795 = f.my_piecewise3(t82, 0, t794)
  t800 = t312 * t754
  t811 = f.my_piecewise3(t90, 0, t794)
  t837 = -0.667e0 * t811 - 0.8891110e0 * t180 * t761 - 0.8891110e0 * t91 * t811 - 0.3978519606294e1 * t763 * t180 - 0.1989259803147e1 * t93 * t811 + 0.17415564533880e2 * t765 * t180 + 0.5805188177960e1 * t95 * t811 - 0.17759960831940e2 * t767 * t180 - 0.4439990207985e1 * t97 * t811 + 0.7035868244370e1 * t769 * t180 + 0.1407173648874e1 * t99 * t811 - 0.973805419524e0 * t771 * t180 - 0.162300903254e0 * t101 * t811
  t838 = t776 * t110
  t839 = t838 * t198
  t842 = f.my_piecewise3(t90, t794, 0)
  t848 = f.my_piecewise5(t81, (-0.2e1 * t84 * t800 * t171 - t84 * t175 * t795 - params.c1 * t795 * t86 - 0.2e1 * t755 * t176) * t88 + t759 * t178 * t88, t89, t837, -t195 * t197 * t842 * t110 - 0.2e1 * t569 * t839 - t578 * t839)
  t854 = t6 * t17 * t19
  t855 = t780 * t135
  t860 = t216 * t17
  t867 = f.my_piecewise3(t2, 0, -t18 * t21 * t780 * t782 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t848 * t782 + 0.3e1 / 0.8e1 * t854 * t855 * t205 * t131 - 0.24739500000000000000000000000000000000000000000000e1 * t860 * t217 * t780 * t113 * t226)
  v2rhotau_0_ = 0.2e1 * r0 * t867 + 0.2e1 * t786
  t872 = t33 * t389 * t513 / 0.4e1
  t873 = f.my_piecewise3(t82, 0, -t872)
  t888 = f.my_piecewise3(t90, 0, -t872)
  t914 = -0.667e0 * t888 - 0.8891110e0 * t446 * t761 - 0.8891110e0 * t91 * t888 - 0.3978519606294e1 * t763 * t446 - 0.1989259803147e1 * t93 * t888 + 0.17415564533880e2 * t765 * t446 + 0.5805188177960e1 * t95 * t888 - 0.17759960831940e2 * t767 * t446 - 0.4439990207985e1 * t97 * t888 + 0.7035868244370e1 * t769 * t446 + 0.1407173648874e1 * t99 * t888 - 0.973805419524e0 * t771 * t446 - 0.162300903254e0 * t101 * t888
  t915 = t838 * t461
  t918 = f.my_piecewise3(t90, -t872, 0)
  t924 = f.my_piecewise5(t81, (-t84 * t175 * t873 - 0.2e1 * t84 * t800 * t439 - params.c1 * t873 * t86 - 0.2e1 * t755 * t442) * t88 + t759 * t444 * t88, t89, t914, -t195 * t197 * t918 * t110 - 0.2e1 * t569 * t915 - t578 * t915)
  t939 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t924 * t782 + 0.3e1 / 0.8e1 * t854 * t855 * t467 * t131 + 0.92773125000000000000000000000000000000000000000000e0 * t860 * t474 * t780 * t113 * t480)
  v2sigmatau_0_ = 0.2e1 * r0 * t939
  v2lapltau_0_ = 0.0e0
  t941 = f.my_piecewise3(t82, 0, 0)
  t944 = t754 ** 2
  t955 = t759 ** 2
  t958 = f.my_piecewise3(t90, 0, 0)
  t960 = t761 ** 2
  t984 = -0.667e0 * t958 - 0.8891110e0 * t960 - 0.8891110e0 * t91 * t958 - 0.3978519606294e1 * t91 * t960 - 0.1989259803147e1 * t93 * t958 + 0.17415564533880e2 * t93 * t960 + 0.5805188177960e1 * t95 * t958 - 0.17759960831940e2 * t95 * t960 - 0.4439990207985e1 * t97 * t958 + 0.7035868244370e1 * t97 * t960 + 0.1407173648874e1 * t99 * t958 - 0.973805419524e0 * t99 * t960 - 0.162300903254e0 * t101 * t958
  t985 = t776 ** 2
  t997 = f.my_piecewise5(t81, (-t84 * t175 * t941 - 0.2e1 * params.c1 * t944 * t175 - 0.2e1 * t84 * t312 * t944 - params.c1 * t941 * t86) * t88 + t955 * t88, t89, t984, -t195 * t197 * t958 * t110 - 0.2e1 * t195 * t351 * t985 * t110 - t362 * t364 * t985 * t110)
  t1002 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t997 * t782)
  v2tau2_0_ = 0.2e1 * r0 * t1002
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_, 'v2rholapl': v2rholapl_0_, 'v2sigmalapl': v2sigmalapl_0_, 'v2lapl2': v2lapl2_0_, 'v2rhotau': v2rhotau_0_, 'v2sigmatau': v2sigmatau_0_, 'v2lapltau': v2lapltau_0_, 'v2tau2': v2tau2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 * t5 * t17
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / r0
  t24 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 * t27
  t30 = 0.1e1 / t29
  t32 = s0 ** 2
  t34 = 2 ** (0.1e1 / 0.3e1)
  t35 = r0 ** 2
  t36 = t35 ** 2
  t37 = t36 * r0
  t39 = 0.1e1 / t19 / t37
  t41 = params.dp2 ** 2
  t42 = t41 ** 2
  t43 = 0.1e1 / t42
  t47 = jnp.exp(-t26 * t30 * t32 * t34 * t39 * t43 / 0.288e3)
  t52 = t28 ** 2
  t53 = 0.1e1 / t52
  t54 = (-0.162742215233874e0 * t24 * t47 + 0.10e2 / 0.81e2) * t25 * t53
  t55 = t34 ** 2
  t56 = s0 * t55
  t58 = 0.1e1 / t20 / t35
  t59 = t56 * t58
  t62 = params.k1 + t54 * t59 / 0.24e2
  t66 = params.k1 * (0.1e1 - params.k1 / t62)
  t67 = tau0 * t55
  t70 = t67 * t22 - t59 / 0.8e1
  t77 = 0.3e1 / 0.10e2 * t26 * t52 + params.eta * s0 * t55 * t58 / 0.8e1
  t78 = 0.1e1 / t77
  t79 = t70 * t78
  t80 = t79 <= 0.0e0
  t81 = 0.0e0 < t79
  t82 = f.my_piecewise3(t81, 0, t79)
  t83 = params.c1 * t82
  t84 = 0.1e1 - t82
  t85 = 0.1e1 / t84
  t87 = jnp.exp(-t83 * t85)
  t88 = t79 <= 0.25e1
  t89 = 0.25e1 < t79
  t90 = f.my_piecewise3(t89, 0.25e1, t79)
  t92 = t90 ** 2
  t94 = t92 * t90
  t96 = t92 ** 2
  t98 = t96 * t90
  t100 = t96 * t92
  t105 = f.my_piecewise3(t89, t79, 0.25e1)
  t106 = 0.1e1 - t105
  t109 = jnp.exp(params.c2 / t106)
  t111 = f.my_piecewise5(t80, t87, t88, 0.1e1 - 0.667e0 * t90 - 0.4445555e0 * t92 - 0.663086601049e0 * t94 + 0.1451297044490e1 * t96 - 0.887998041597e0 * t98 + 0.234528941479e0 * t100 - 0.23185843322e-1 * t96 * t94, -params.d * t109)
  t112 = 0.174e0 - t66
  t114 = t111 * t112 + t66 + 0.1e1
  t116 = jnp.sqrt(0.3e1)
  t117 = 0.1e1 / t28
  t119 = jnp.sqrt(s0)
  t120 = t119 * t34
  t122 = 0.1e1 / t19 / r0
  t124 = t26 * t117 * t120 * t122
  t125 = jnp.sqrt(t124)
  t129 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t116 / t125)
  t130 = 0.1e1 - t129
  t134 = 0.1e1 / t20
  t135 = params.k1 ** 2
  t136 = t62 ** 2
  t137 = 0.1e1 / t136
  t138 = t135 * t137
  t139 = t27 ** 2
  t141 = t24 / t139
  t142 = t32 * s0
  t143 = t141 * t142
  t144 = t36 ** 2
  t151 = t35 * r0
  t153 = 0.1e1 / t20 / t151
  t154 = t56 * t153
  t157 = -0.15068723632766111111111111111111111111111111111111e-2 * t143 / t144 / r0 * t43 * t47 - t54 * t154 / 0.9e1
  t162 = -0.5e1 / 0.3e1 * t67 * t58 + t154 / 0.3e1
  t164 = t77 ** 2
  t165 = 0.1e1 / t164
  t167 = t70 * t165 * params.eta
  t170 = t162 * t78 + t167 * t154 / 0.3e1
  t171 = f.my_piecewise3(t81, 0, t170)
  t174 = t84 ** 2
  t175 = 0.1e1 / t174
  t176 = t175 * t171
  t178 = -params.c1 * t171 * t85 - t83 * t176
  t180 = f.my_piecewise3(t89, 0, t170)
  t182 = t90 * t180
  t184 = t92 * t180
  t186 = t94 * t180
  t188 = t96 * t180
  t190 = t98 * t180
  t195 = params.d * params.c2
  t196 = t106 ** 2
  t197 = 0.1e1 / t196
  t198 = f.my_piecewise3(t89, t170, 0)
  t202 = f.my_piecewise5(t80, t178 * t87, t88, -0.667e0 * t180 - 0.8891110e0 * t182 - 0.1989259803147e1 * t184 + 0.5805188177960e1 * t186 - 0.4439990207985e1 * t188 + 0.1407173648874e1 * t190 - 0.162300903254e0 * t100 * t180, -t195 * t197 * t198 * t109)
  t204 = t111 * t135
  t205 = t137 * t157
  t207 = t202 * t112 + t138 * t157 - t204 * t205
  t212 = 3 ** (0.1e1 / 0.6e1)
  t213 = t212 ** 2
  t214 = t213 ** 2
  t215 = t214 * t212
  t216 = t215 * t5
  t218 = t17 / t151
  t222 = 0.1e1 / t125 / t124
  t226 = t222 * t26 * t117 * t120 * t129
  t230 = 0.1e1 / t136 / t62
  t231 = t135 * t230
  t232 = t157 ** 2
  t241 = t32 ** 2
  t242 = t241 * s0
  t243 = t36 * t151
  t249 = t42 ** 2
  t254 = 0.1e1 / t249 * t26 * t30 * t34 * t47
  t258 = 0.1e1 / t20 / t36
  t259 = t56 * t258
  t262 = 0.17580177571560462962962962962962962962962962962963e-1 * t143 / t144 / t35 * t43 * t47 - 0.27905043764381687242798353909465020576131687242798e-4 * t141 * t242 / t19 / t144 / t243 * t254 + 0.11e2 / 0.27e2 * t54 * t259
  t267 = 0.40e2 / 0.9e1 * t67 * t153 - 0.11e2 / 0.9e1 * t259
  t270 = t162 * t165 * params.eta
  t274 = 0.1e1 / t164 / t77
  t276 = params.eta ** 2
  t277 = t70 * t274 * t276
  t278 = t32 * t34
  t281 = t278 / t19 / t243
  t286 = t267 * t78 + 0.2e1 / 0.3e1 * t270 * t154 + 0.4e1 / 0.9e1 * t277 * t281 - 0.11e2 / 0.9e1 * t167 * t259
  t287 = f.my_piecewise3(t81, 0, t286)
  t288 = params.c1 * t287
  t290 = t171 ** 2
  t295 = 0.1e1 / t174 / t84
  t301 = -t83 * t175 * t287 - 0.2e1 * params.c1 * t290 * t175 - 0.2e1 * t83 * t295 * t290 - t288 * t85
  t303 = t178 ** 2
  t306 = f.my_piecewise3(t89, 0, t286)
  t308 = t180 ** 2
  t332 = -0.667e0 * t306 - 0.8891110e0 * t308 - 0.8891110e0 * t90 * t306 - 0.3978519606294e1 * t90 * t308 - 0.1989259803147e1 * t92 * t306 + 0.17415564533880e2 * t92 * t308 + 0.5805188177960e1 * t94 * t306 - 0.17759960831940e2 * t94 * t308 - 0.4439990207985e1 * t96 * t306 + 0.7035868244370e1 * t96 * t308 + 0.1407173648874e1 * t98 * t306 - 0.973805419524e0 * t98 * t308 - 0.162300903254e0 * t100 * t306
  t334 = 0.1e1 / t196 / t106
  t335 = t198 ** 2
  t340 = f.my_piecewise3(t89, t286, 0)
  t344 = params.c2 ** 2
  t345 = params.d * t344
  t346 = t196 ** 2
  t347 = 0.1e1 / t346
  t352 = f.my_piecewise5(t80, t301 * t87 + t303 * t87, t88, t332, -t195 * t197 * t340 * t109 - 0.2e1 * t195 * t334 * t335 * t109 - t345 * t347 * t335 * t109)
  t354 = t202 * t135
  t357 = t230 * t232
  t360 = t137 * t262
  t362 = t352 * t112 + t138 * t262 + 0.2e1 * t204 * t357 - t204 * t360 - 0.2e1 * t354 * t205 - 0.2e1 * t231 * t232
  t368 = t17 / t35
  t375 = t17 / t19 / t36
  t386 = 0.1e1 / t125 / t59 * t56 * t129 / 0.6e1
  t389 = t4 ** 2
  t391 = t3 * t389 * jnp.pi
  t393 = t17 / t19
  t396 = 0.1e1 / t119
  t400 = t396 * t25 * t53 * t55 * t129
  t404 = f.my_piecewise3(t2, 0, t18 * t22 * t114 * t130 / 0.12e2 - t18 * t134 * t207 * t130 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t216 * t218 * t114 * t226 - 0.3e1 / 0.8e1 * t18 * t19 * t362 * t130 - 0.49479000000000000000000000000000000000000000000000e1 * t216 * t368 * t207 * t226 - 0.29687400000000000000000000000000000000000000000000e2 * t216 * t375 * t114 * t386 + 0.40802857350000000000000000000000000000000000000000e1 * t391 * t393 * t114 * t400)
  t406 = t58 * t114
  t414 = 0.1e1 / t36
  t434 = t17 * t122 * t114
  t438 = t136 ** 2
  t439 = 0.1e1 / t438
  t441 = t232 * t157
  t448 = 0.1e1 / t144 / t151
  t453 = t144 ** 2
  t478 = t56 / t20 / t37
  t481 = -0.19053563882319816049382716049382716049382716049383e0 * t143 * t448 * t43 * t47 + 0.75343618163830555555555555555555555555555555555555e-3 * t141 * t242 / t19 / t453 * t254 - 0.31005604182646319158664837677183356195701874714220e-5 * t141 * t241 * t142 / t20 / t453 / t37 / t249 / t42 * t25 / t52 / t139 * t55 * t47 - 0.154e3 / 0.81e2 * t54 * t478
  t497 = t164 ** 2
  t512 = (-0.440e3 / 0.27e2 * t67 * t258 + 0.154e3 / 0.27e2 * t478) * t78 + t267 * t165 * params.eta * t154 + 0.4e1 / 0.3e1 * t162 * t274 * t276 * t281 - 0.11e2 / 0.3e1 * t270 * t259 + 0.8e1 / 0.9e1 * t70 / t497 * t276 * params.eta * t142 * t448 - 0.44e2 / 0.9e1 * t277 * t278 / t19 / t144 + 0.154e3 / 0.27e2 * t167 * t478
  t513 = f.my_piecewise3(t81, 0, t512)
  t518 = t290 * t171
  t522 = t174 ** 2
  t541 = f.my_piecewise3(t89, 0, t512)
  t547 = t308 * t180
  t577 = -0.667e0 * t541 - 0.26673330e1 * t180 * t306 - 0.8891110e0 * t90 * t541 - 0.3978519606294e1 * t547 - 0.11935558818882e2 * t182 * t306 - 0.1989259803147e1 * t92 * t541 + 0.34831129067760e2 * t90 * t547 + 0.52246693601640e2 * t184 * t306 + 0.5805188177960e1 * t94 * t541 - 0.53279882495820e2 * t92 * t547 - 0.53279882495820e2 * t186 * t306 - 0.4439990207985e1 * t96 * t541 + 0.28143472977480e2 * t94 * t547 + 0.21107604733110e2 * t188 * t306 + 0.1407173648874e1 * t98 * t541 - 0.4869027097620e1 * t96 * t547 - 0.2921416258572e1 * t190 * t306 - 0.162300903254e0 * t100 * t541
  t578 = t335 * t198
  t585 = t198 * t109 * t340
  t594 = f.my_piecewise3(t89, t512, 0)
  t609 = f.my_piecewise5(t80, (-params.c1 * t513 * t85 - 0.6e1 * t288 * t176 - 0.6e1 * params.c1 * t518 * t295 - 0.6e1 * t83 / t522 * t518 - 0.6e1 * t83 * t295 * t171 * t287 - t83 * t175 * t513) * t87 + 0.3e1 * t301 * t178 * t87 + t303 * t178 * t87, t88, t577, -0.6e1 * t195 * t347 * t578 * t109 - 0.6e1 * t195 * t334 * t585 - 0.6e1 * t345 / t346 / t106 * t578 * t109 - t195 * t197 * t594 * t109 - 0.3e1 * t345 * t347 * t585 - params.d * t344 * params.c2 / t346 / t196 * t578 * t109)
  t645 = 0.1e1 / t4 / t27
  t653 = t119 * s0
  t677 = -0.5e1 / 0.36e2 * t18 * t406 * t130 + t18 * t22 * t207 * t130 / 0.4e1 - 0.11819983333333333333333333333333333333333333333333e2 * t216 * t17 * t414 * t114 * t226 - 0.3e1 / 0.8e1 * t18 * t134 * t362 * t130 + 0.12369750000000000000000000000000000000000000000000e2 * t216 * t218 * t207 * t226 + 0.17812440000000000000000000000000000000000000000000e3 * t216 * t17 * t39 * t114 * t386 - 0.81605714700000000000000000000000000000000000000000e1 * t391 * t434 * t400 - 0.3e1 / 0.8e1 * t18 * t19 * (0.6e1 * t204 * t230 * t157 * t262 - 0.3e1 * t352 * t135 * t205 + 0.6e1 * t135 * t439 * t441 - t204 * t137 * t481 - 0.6e1 * t231 * t157 * t262 - 0.6e1 * t204 * t439 * t441 + t609 * t112 + t138 * t481 + 0.6e1 * t354 * t357 - 0.3e1 * t354 * t360) * t130 - 0.74218500000000000000000000000000000000000000000000e1 * t216 * t368 * t362 * t226 - 0.89062200000000000000000000000000000000000000000000e2 * t216 * t375 * t207 * t386 + 0.12240857205000000000000000000000000000000000000000e2 * t391 * t393 * t207 * t400 - 0.16493000000000000000000000000000000000000000000000e2 * t215 * t645 * t17 / t20 / t36 / t35 * t114 / t125 * t27 / t414 * t129 + 0.81605714699999999999999999999999999999999999999999e1 * t3 * t645 * t434 * t25 * t29 * t396 * t55 * t129 - 0.32302153261130400000000000000000000000000000000000e3 * t216 * t17 * t406 * t222 * t129
  t678 = f.my_piecewise3(t2, 0, t677)
  v3rho3_0_ = 0.2e1 * r0 * t678 + 0.6e1 * t404

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = t3 * t5 * t17
  t19 = r0 ** 2
  t20 = r0 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t23 = 0.1e1 / t21 / t19
  t25 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 * t28
  t31 = 0.1e1 / t30
  t32 = t27 * t31
  t33 = s0 ** 2
  t35 = 2 ** (0.1e1 / 0.3e1)
  t36 = t19 ** 2
  t37 = t36 * r0
  t39 = 0.1e1 / t20 / t37
  t41 = params.dp2 ** 2
  t42 = t41 ** 2
  t43 = 0.1e1 / t42
  t47 = jnp.exp(-t32 * t33 * t35 * t39 * t43 / 0.288e3)
  t52 = t29 ** 2
  t53 = 0.1e1 / t52
  t54 = (-0.162742215233874e0 * t25 * t47 + 0.10e2 / 0.81e2) * t26 * t53
  t55 = t35 ** 2
  t56 = s0 * t55
  t57 = t56 * t23
  t60 = params.k1 + t54 * t57 / 0.24e2
  t64 = params.k1 * (0.1e1 - params.k1 / t60)
  t65 = tau0 * t55
  t67 = 0.1e1 / t21 / r0
  t70 = t65 * t67 - t57 / 0.8e1
  t77 = 0.3e1 / 0.10e2 * t27 * t52 + params.eta * s0 * t55 * t23 / 0.8e1
  t78 = 0.1e1 / t77
  t79 = t70 * t78
  t80 = t79 <= 0.0e0
  t81 = 0.0e0 < t79
  t82 = f.my_piecewise3(t81, 0, t79)
  t83 = params.c1 * t82
  t84 = 0.1e1 - t82
  t85 = 0.1e1 / t84
  t87 = jnp.exp(-t83 * t85)
  t88 = t79 <= 0.25e1
  t89 = 0.25e1 < t79
  t90 = f.my_piecewise3(t89, 0.25e1, t79)
  t92 = t90 ** 2
  t94 = t92 * t90
  t96 = t92 ** 2
  t98 = t96 * t90
  t100 = t96 * t92
  t105 = f.my_piecewise3(t89, t79, 0.25e1)
  t106 = 0.1e1 - t105
  t109 = jnp.exp(params.c2 / t106)
  t111 = f.my_piecewise5(t80, t87, t88, 0.1e1 - 0.667e0 * t90 - 0.4445555e0 * t92 - 0.663086601049e0 * t94 + 0.1451297044490e1 * t96 - 0.887998041597e0 * t98 + 0.234528941479e0 * t100 - 0.23185843322e-1 * t96 * t94, -params.d * t109)
  t112 = 0.174e0 - t64
  t114 = t111 * t112 + t64 + 0.1e1
  t115 = t23 * t114
  t116 = jnp.sqrt(0.3e1)
  t117 = 0.1e1 / t29
  t118 = t27 * t117
  t119 = jnp.sqrt(s0)
  t120 = t119 * t35
  t122 = 0.1e1 / t20 / r0
  t124 = t118 * t120 * t122
  t125 = jnp.sqrt(t124)
  t129 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t116 / t125)
  t130 = 0.1e1 - t129
  t134 = params.k1 ** 2
  t135 = t60 ** 2
  t136 = 0.1e1 / t135
  t137 = t134 * t136
  t138 = t28 ** 2
  t140 = t25 / t138
  t141 = t33 * s0
  t142 = t140 * t141
  t143 = t36 ** 2
  t144 = t143 * r0
  t145 = 0.1e1 / t144
  t150 = t19 * r0
  t152 = 0.1e1 / t21 / t150
  t153 = t56 * t152
  t156 = -0.15068723632766111111111111111111111111111111111111e-2 * t142 * t145 * t43 * t47 - t54 * t153 / 0.9e1
  t161 = -0.5e1 / 0.3e1 * t65 * t23 + t153 / 0.3e1
  t163 = t77 ** 2
  t164 = 0.1e1 / t163
  t166 = t70 * t164 * params.eta
  t169 = t161 * t78 + t166 * t153 / 0.3e1
  t170 = f.my_piecewise3(t81, 0, t169)
  t173 = t84 ** 2
  t174 = 0.1e1 / t173
  t175 = t174 * t170
  t177 = -params.c1 * t170 * t85 - t83 * t175
  t179 = f.my_piecewise3(t89, 0, t169)
  t181 = t90 * t179
  t183 = t92 * t179
  t185 = t94 * t179
  t187 = t96 * t179
  t189 = t98 * t179
  t194 = params.d * params.c2
  t195 = t106 ** 2
  t196 = 0.1e1 / t195
  t197 = f.my_piecewise3(t89, t169, 0)
  t201 = f.my_piecewise5(t80, t177 * t87, t88, -0.667e0 * t179 - 0.8891110e0 * t181 - 0.1989259803147e1 * t183 + 0.5805188177960e1 * t185 - 0.4439990207985e1 * t187 + 0.1407173648874e1 * t189 - 0.162300903254e0 * t100 * t179, -t194 * t196 * t197 * t109)
  t203 = t111 * t134
  t204 = t136 * t156
  t206 = t201 * t112 + t137 * t156 - t203 * t204
  t211 = 3 ** (0.1e1 / 0.6e1)
  t212 = t211 ** 2
  t213 = t212 ** 2
  t214 = t213 * t211
  t215 = t214 * t5
  t216 = 0.1e1 / t36
  t217 = t17 * t216
  t221 = 0.1e1 / t125 / t124
  t225 = t221 * t27 * t117 * t120 * t129
  t228 = 0.1e1 / t21
  t230 = 0.1e1 / t135 / t60
  t231 = t134 * t230
  t232 = t156 ** 2
  t241 = t33 ** 2
  t242 = t241 * s0
  t243 = t36 * t150
  t249 = t42 ** 2
  t254 = 0.1e1 / t249 * t27 * t31 * t35 * t47
  t258 = 0.1e1 / t21 / t36
  t259 = t56 * t258
  t262 = 0.17580177571560462962962962962962962962962962962963e-1 * t142 / t143 / t19 * t43 * t47 - 0.27905043764381687242798353909465020576131687242798e-4 * t140 * t242 / t20 / t143 / t243 * t254 + 0.11e2 / 0.27e2 * t54 * t259
  t267 = 0.40e2 / 0.9e1 * t65 * t152 - 0.11e2 / 0.9e1 * t259
  t270 = t161 * t164 * params.eta
  t274 = 0.1e1 / t163 / t77
  t276 = params.eta ** 2
  t277 = t70 * t274 * t276
  t278 = t33 * t35
  t281 = t278 / t20 / t243
  t286 = t267 * t78 + 0.2e1 / 0.3e1 * t270 * t153 + 0.4e1 / 0.9e1 * t277 * t281 - 0.11e2 / 0.9e1 * t166 * t259
  t287 = f.my_piecewise3(t81, 0, t286)
  t288 = params.c1 * t287
  t290 = t170 ** 2
  t295 = 0.1e1 / t173 / t84
  t296 = t295 * t290
  t301 = -t83 * t174 * t287 - 0.2e1 * params.c1 * t290 * t174 - t288 * t85 - 0.2e1 * t83 * t296
  t303 = t177 ** 2
  t306 = f.my_piecewise3(t89, 0, t286)
  t308 = t179 ** 2
  t312 = t90 * t308
  t316 = t92 * t308
  t320 = t94 * t308
  t324 = t96 * t308
  t332 = -0.667e0 * t306 - 0.8891110e0 * t308 - 0.8891110e0 * t90 * t306 - 0.3978519606294e1 * t312 - 0.1989259803147e1 * t92 * t306 + 0.17415564533880e2 * t316 + 0.5805188177960e1 * t94 * t306 - 0.17759960831940e2 * t320 - 0.4439990207985e1 * t96 * t306 + 0.7035868244370e1 * t324 + 0.1407173648874e1 * t98 * t306 - 0.973805419524e0 * t98 * t308 - 0.162300903254e0 * t100 * t306
  t333 = t195 * t106
  t334 = 0.1e1 / t333
  t335 = t197 ** 2
  t340 = f.my_piecewise3(t89, t286, 0)
  t344 = params.c2 ** 2
  t345 = params.d * t344
  t346 = t195 ** 2
  t347 = 0.1e1 / t346
  t352 = f.my_piecewise5(t80, t301 * t87 + t303 * t87, t88, t332, -t194 * t196 * t340 * t109 - 0.2e1 * t194 * t334 * t335 * t109 - t345 * t347 * t335 * t109)
  t354 = t201 * t134
  t357 = t230 * t232
  t360 = t136 * t262
  t362 = t352 * t112 + t137 * t262 + 0.2e1 * t203 * t357 - t203 * t360 - 0.2e1 * t354 * t204 - 0.2e1 * t231 * t232
  t368 = t17 / t150
  t373 = t17 * t39
  t380 = 0.1e1 / t125 / t26 / t53 / t57 / 0.6e1
  t384 = t380 * t26 * t53 * t56 * t129
  t387 = t4 ** 2
  t389 = t3 * t387 * jnp.pi
  t390 = t17 * t122
  t391 = t390 * t114
  t393 = 0.1e1 / t119
  t397 = t393 * t26 * t53 * t55 * t129
  t400 = t135 ** 2
  t401 = 0.1e1 / t400
  t402 = t134 * t401
  t403 = t232 * t156
  t410 = 0.1e1 / t143 / t150
  t415 = t143 ** 2
  t422 = t241 * t141
  t435 = 0.1e1 / t249 / t42 * t26 / t52 / t138 * t55 * t47
  t439 = 0.1e1 / t21 / t37
  t440 = t56 * t439
  t443 = -0.19053563882319816049382716049382716049382716049383e0 * t142 * t410 * t43 * t47 + 0.75343618163830555555555555555555555555555555555555e-3 * t140 * t242 / t20 / t415 * t254 - 0.31005604182646319158664837677183356195701874714220e-5 * t140 * t422 / t21 / t415 / t37 * t435 - 0.154e3 / 0.81e2 * t54 * t440
  t448 = -0.440e3 / 0.27e2 * t65 * t258 + 0.154e3 / 0.27e2 * t440
  t451 = t267 * t164 * params.eta
  t454 = t161 * t274 * t276
  t459 = t163 ** 2
  t460 = 0.1e1 / t459
  t461 = t70 * t460
  t463 = t276 * params.eta * t141
  t464 = t463 * t410
  t469 = t278 / t20 / t143
  t474 = t448 * t78 + t451 * t153 + 0.4e1 / 0.3e1 * t454 * t281 - 0.11e2 / 0.3e1 * t270 * t259 + 0.8e1 / 0.9e1 * t461 * t464 - 0.44e2 / 0.9e1 * t277 * t469 + 0.154e3 / 0.27e2 * t166 * t440
  t475 = f.my_piecewise3(t81, 0, t474)
  t476 = params.c1 * t475
  t480 = t290 * t170
  t484 = t173 ** 2
  t485 = 0.1e1 / t484
  t489 = t295 * t170
  t495 = -t83 * t174 * t475 - 0.6e1 * t83 * t489 * t287 - 0.6e1 * params.c1 * t480 * t295 - 0.6e1 * t83 * t485 * t480 - 0.6e1 * t288 * t175 - t476 * t85
  t503 = f.my_piecewise3(t89, 0, t474)
  t509 = t308 * t179
  t539 = -0.667e0 * t503 - 0.26673330e1 * t179 * t306 - 0.8891110e0 * t90 * t503 - 0.3978519606294e1 * t509 - 0.11935558818882e2 * t181 * t306 - 0.1989259803147e1 * t92 * t503 + 0.34831129067760e2 * t90 * t509 + 0.52246693601640e2 * t183 * t306 + 0.5805188177960e1 * t94 * t503 - 0.53279882495820e2 * t92 * t509 - 0.53279882495820e2 * t185 * t306 - 0.4439990207985e1 * t96 * t503 + 0.28143472977480e2 * t94 * t509 + 0.21107604733110e2 * t187 * t306 + 0.1407173648874e1 * t98 * t503 - 0.4869027097620e1 * t96 * t509 - 0.2921416258572e1 * t189 * t306 - 0.162300903254e0 * t100 * t503
  t540 = t335 * t197
  t545 = t194 * t334
  t546 = t197 * t109
  t547 = t546 * t340
  t551 = 0.1e1 / t346 / t106
  t556 = f.my_piecewise3(t89, t474, 0)
  t560 = t345 * t347
  t564 = params.d * t344 * params.c2
  t566 = 0.1e1 / t346 / t195
  t571 = f.my_piecewise5(t80, 0.3e1 * t301 * t177 * t87 + t303 * t177 * t87 + t495 * t87, t88, t539, -t194 * t196 * t556 * t109 - 0.6e1 * t194 * t347 * t540 * t109 - 0.6e1 * t345 * t551 * t540 * t109 - t564 * t566 * t540 * t109 - 0.6e1 * t545 * t547 - 0.3e1 * t560 * t547)
  t573 = t352 * t134
  t580 = t401 * t403
  t583 = t230 * t156
  t584 = t583 * t262
  t587 = t136 * t443
  t589 = -0.6e1 * t231 * t156 * t262 + t571 * t112 + t137 * t443 - 0.6e1 * t203 * t580 + 0.6e1 * t203 * t584 - t203 * t587 - 0.3e1 * t573 * t204 + 0.6e1 * t354 * t357 - 0.3e1 * t354 * t360 + 0.6e1 * t402 * t403
  t595 = t17 / t19
  t602 = t17 / t20 / t36
  t608 = t17 / t20
  t614 = 0.1e1 / t4 / t28
  t615 = t214 * t614
  t616 = t36 * t19
  t618 = 0.1e1 / t21 / t616
  t620 = t615 * t17 * t618
  t622 = t119 * s0
  t627 = 0.1e1 / t125 * t28 / t622 / t216 / 0.72e2
  t629 = t622 * t129
  t630 = t114 * t627 * t629
  t633 = t3 * t614
  t638 = t26 * t30 * t393 * t55 * t129
  t641 = t215 * t17
  t642 = t221 * t129
  t646 = -0.5e1 / 0.36e2 * t18 * t115 * t130 + t18 * t67 * t206 * t130 / 0.4e1 - 0.11819983333333333333333333333333333333333333333333e2 * t215 * t217 * t114 * t225 - 0.3e1 / 0.8e1 * t18 * t228 * t362 * t130 + 0.12369750000000000000000000000000000000000000000000e2 * t215 * t368 * t206 * t225 + 0.17812440000000000000000000000000000000000000000000e3 * t215 * t373 * t114 * t384 - 0.81605714700000000000000000000000000000000000000000e1 * t389 * t391 * t397 - 0.3e1 / 0.8e1 * t18 * t20 * t589 * t130 - 0.74218500000000000000000000000000000000000000000000e1 * t215 * t595 * t362 * t225 - 0.89062200000000000000000000000000000000000000000000e2 * t215 * t602 * t206 * t384 + 0.12240857205000000000000000000000000000000000000000e2 * t389 * t608 * t206 * t397 - 0.11874960000000000000000000000000000000000000000000e4 * t620 * t630 + 0.81605714699999999999999999999999999999999999999999e1 * t633 * t391 * t638 - 0.32302153261130400000000000000000000000000000000000e3 * t641 * t115 * t642
  t647 = f.my_piecewise3(t2, 0, t646)
  t655 = t23 * t206
  t659 = t152 * t114
  t695 = t215 * t17 / t37 * t114
  t715 = 0.15041616000000000000000000000000000000000000000000e5 * t615 * t17 / t21 / t243 * t630 - 0.12920861304452160000000000000000000000000000000000e4 * t641 * t655 * t642 + 0.86139075363014400000000000000000000000000000000001e3 * t641 * t659 * t642 - t18 * t228 * t589 * t130 / 0.2e1 - 0.5e1 / 0.9e1 * t18 * t655 * t130 + t18 * t67 * t362 * t130 / 0.2e1 - 0.47499840000000000000000000000000000000000000000000e4 * t620 * t206 * t627 * t629 - 0.76967333333333333333333333333333333333333333333333e2 * t615 * t17 * t145 * t114 / t125 / t32 / t278 / t39 * t33 * t129 * t118 * t35 - 0.64604306522260800000000000000000000000000000000000e3 * t695 * t380 * t129 * t27 * t117 * t119 * t35 - 0.98958000000000000000000000000000000000000000000000e1 * t215 * t595 * t589 * t225 - 0.17812440000000000000000000000000000000000000000000e3 * t215 * t602 * t362 * t384 + 0.24739500000000000000000000000000000000000000000000e2 * t215 * t368 * t362 * t225
  t748 = t390 * t206
  t758 = t17 / t20 / t19 * t114
  t772 = t143 * t36
  t773 = 0.1e1 / t772
  t792 = t138 ** 2
  t796 = t241 ** 2
  t801 = t249 ** 2
  t807 = t56 * t618
  t810 = 0.21646500548906162427983539094650205761316872427984e1 * t142 * t773 * t43 * t47 - 0.15834562056077475194330132601737540009144947416552e-1 * t140 * t242 / t20 / t415 / r0 * t254 + 0.15089394035554541990550221002895900015241579027587e-3 * t140 * t422 / t21 / t415 / t616 * t435 - 0.68901342628102931463699639282629680434893054920489e-6 * t25 / t792 / t138 * t796 * s0 / t415 / t772 / t801 * t47 + 0.2618e4 / 0.243e3 * t54 * t807
  t814 = 0.1e1 / t400 / t60
  t816 = t232 ** 2
  t822 = t262 ** 2
  t853 = t276 ** 2
  t872 = (0.6160e4 / 0.81e2 * t65 * t439 - 0.2618e4 / 0.81e2 * t807) * t78 + 0.4e1 / 0.3e1 * t448 * t164 * params.eta * t153 + 0.8e1 / 0.3e1 * t267 * t274 * t276 * t281 - 0.22e2 / 0.3e1 * t451 * t259 + 0.32e2 / 0.9e1 * t161 * t460 * t464 - 0.176e3 / 0.9e1 * t454 * t469 + 0.616e3 / 0.27e2 * t270 * t440 + 0.32e2 / 0.27e2 * t70 / t459 / t77 * t853 * t241 / t21 / t143 / t616 * t55 - 0.176e3 / 0.9e1 * t461 * t463 * t773 + 0.3916e4 / 0.81e2 * t277 * t278 / t20 / t144 - 0.2618e4 / 0.81e2 * t166 * t807
  t873 = f.my_piecewise3(t81, 0, t872)
  t880 = t287 ** 2
  t884 = t290 ** 2
  t910 = t301 ** 2
  t916 = t303 ** 2
  t919 = t308 ** 2
  t921 = t306 ** 2
  t923 = f.my_piecewise3(t89, 0, t872)
  t947 = 0.34831129067760e2 * t919 - 0.26673330e1 * t921 - 0.667e0 * t923 + 0.208986774406560e3 * t312 * t306 + 0.69662258135520e2 * t183 * t503 - 0.15914078425176e2 * t181 * t503 + 0.28143472977480e2 * t187 * t503 - 0.319679294974920e3 * t316 * t306 - 0.71039843327760e2 * t185 * t503 - 0.29214162585720e2 * t324 * t306 - 0.3895221678096e1 * t189 * t503 + 0.168860837864880e3 * t320 * t306 - 0.23871117637764e2 * t308 * t306 - 0.162300903254e0 * t100 * t923
  t976 = -0.35564440e1 * t179 * t503 - 0.8891110e0 * t90 * t923 - 0.1989259803147e1 * t92 * t923 + 0.5805188177960e1 * t94 * t923 - 0.4439990207985e1 * t96 * t923 + 0.84430418932440e2 * t92 * t919 + 0.52246693601640e2 * t92 * t921 - 0.106559764991640e3 * t90 * t919 + 0.1407173648874e1 * t98 * t923 - 0.11935558818882e2 * t90 * t921 + 0.21107604733110e2 * t96 * t921 - 0.19476108390480e2 * t94 * t919 - 0.53279882495820e2 * t94 * t921 - 0.2921416258572e1 * t98 * t921
  t978 = t335 ** 2
  t985 = t335 * t109 * t340
  t992 = t340 ** 2
  t1000 = t546 * t556
  t1009 = f.my_piecewise3(t89, t872, 0)
  t1022 = t344 ** 2
  t1024 = t346 ** 2
  t1029 = -0.24e2 * t194 * t551 * t978 * t109 - 0.36e2 * t194 * t347 * t985 - 0.36e2 * t345 * t566 * t978 * t109 - 0.6e1 * t194 * t334 * t992 * t109 - 0.36e2 * t345 * t551 * t985 - 0.8e1 * t545 * t1000 - 0.12e2 * t564 / t346 / t333 * t978 * t109 - t194 * t196 * t1009 * t109 - 0.4e1 * t560 * t1000 - 0.3e1 * t345 * t347 * t992 * t109 - 0.6e1 * t564 * t566 * t985 - params.d * t1022 / t1024 * t978 * t109
  t1030 = f.my_piecewise5(t80, (-params.c1 * t873 * t85 - 0.8e1 * t476 * t175 - 0.36e2 * t288 * t296 - 0.6e1 * params.c1 * t880 * t174 - 0.24e2 * params.c1 * t884 * t485 - 0.24e2 * t83 / t484 / t84 * t884 - 0.36e2 * t83 * t485 * t290 * t287 - 0.6e1 * t83 * t295 * t880 - 0.8e1 * t83 * t489 * t475 - t83 * t174 * t873) * t87 + 0.4e1 * t495 * t177 * t87 + 0.3e1 * t910 * t87 + 0.6e1 * t301 * t303 * t87 + t916 * t87, t88, t947 + t976, t1029)
  t1052 = -0.36e2 * t203 * t401 * t232 * t262 - 0.4e1 * t571 * t134 * t204 - 0.24e2 * t134 * t814 * t816 - t203 * t136 * t810 - 0.8e1 * t231 * t156 * t443 + 0.6e1 * t203 * t230 * t822 + 0.8e1 * t203 * t583 * t443 + 0.24e2 * t203 * t814 * t816 + 0.36e2 * t402 * t232 * t262 + t1030 * t112 + t137 * t810 - 0.6e1 * t231 * t822 - 0.24e2 * t354 * t580 + 0.24e2 * t354 * t584 - 0.4e1 * t354 * t587 + 0.12e2 * t573 * t357 - 0.6e1 * t573 * t360
  t1060 = 0.71249760000000000000000000000000000000000000000000e3 * t215 * t373 * t206 * t384 + 0.46363655555555555555555555555555555555555555555554e2 * t695 * t225 - 0.47279933333333333333333333333333333333333333333333e2 * t215 * t217 * t206 * t225 - 0.10918366000000000000000000000000000000000000000000e4 * t215 * t17 / t20 / t616 * t114 * t384 + 0.88793235622637281199999999999999999999999999999999e2 * t389 * t17 / r0 * t114 / s0 * t27 * t117 * t35 * t129 + 0.24481714410000000000000000000000000000000000000000e2 * t389 * t608 * t362 * t397 + 0.32642285880000000000000000000000000000000000000000e2 * t633 * t748 * t638 - 0.32642285880000000000000000000000000000000000000000e2 * t389 * t748 * t397 - 0.32642285879999999999999999999999999999999999999998e2 * t633 * t758 * t638 + 0.30375460471666666666666666666666666666666666666666e2 * t389 * t758 * t397 - 0.3e1 / 0.8e1 * t18 * t20 * t1052 * t130 + 0.10e2 / 0.27e2 * t18 * t659 * t130
  t1062 = f.my_piecewise3(t2, 0, t715 + t1060)
  v4rho4_0_ = 0.2e1 * r0 * t1062 + 0.8e1 * t647

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
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
  t33 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t39 = 0.1e1 / t37 / t36
  t40 = t35 * t39
  t41 = s0 ** 2
  t42 = r0 ** 2
  t43 = t42 ** 2
  t44 = t43 * r0
  t45 = r0 ** (0.1e1 / 0.3e1)
  t47 = 0.1e1 / t45 / t44
  t49 = params.dp2 ** 2
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t55 = jnp.exp(-t40 * t41 * t47 * t51 / 0.576e3)
  t59 = (-0.162742215233874e0 * t33 * t55 + 0.10e2 / 0.81e2) * t34
  t60 = t37 ** 2
  t61 = 0.1e1 / t60
  t62 = t61 * s0
  t63 = t45 ** 2
  t65 = 0.1e1 / t63 / t42
  t69 = params.k1 + t59 * t62 * t65 / 0.24e2
  t73 = params.k1 * (0.1e1 - params.k1 / t69)
  t75 = 0.1e1 / t63 / r0
  t77 = s0 * t65
  t79 = tau0 * t75 - t77 / 0.8e1
  t81 = 0.3e1 / 0.10e2 * t35 * t60
  t82 = params.eta * s0
  t85 = t81 + t82 * t65 / 0.8e1
  t86 = 0.1e1 / t85
  t87 = t79 * t86
  t88 = t87 <= 0.0e0
  t89 = 0.0e0 < t87
  t90 = f.my_piecewise3(t89, 0, t87)
  t91 = params.c1 * t90
  t92 = 0.1e1 - t90
  t93 = 0.1e1 / t92
  t95 = jnp.exp(-t91 * t93)
  t96 = t87 <= 0.25e1
  t97 = 0.25e1 < t87
  t98 = f.my_piecewise3(t97, 0.25e1, t87)
  t100 = t98 ** 2
  t102 = t100 * t98
  t104 = t100 ** 2
  t106 = t104 * t98
  t108 = t104 * t100
  t113 = f.my_piecewise3(t97, t87, 0.25e1)
  t114 = 0.1e1 - t113
  t117 = jnp.exp(params.c2 / t114)
  t119 = f.my_piecewise5(t88, t95, t96, 0.1e1 - 0.667e0 * t98 - 0.4445555e0 * t100 - 0.663086601049e0 * t102 + 0.1451297044490e1 * t104 - 0.887998041597e0 * t106 + 0.234528941479e0 * t108 - 0.23185843322e-1 * t104 * t102, -params.d * t117)
  t120 = 0.174e0 - t73
  t122 = t119 * t120 + t73 + 0.1e1
  t124 = jnp.sqrt(0.3e1)
  t125 = 0.1e1 / t37
  t126 = t35 * t125
  t127 = jnp.sqrt(s0)
  t128 = t45 * r0
  t129 = 0.1e1 / t128
  t131 = t126 * t127 * t129
  t132 = jnp.sqrt(t131)
  t136 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t124 / t132)
  t137 = 0.1e1 - t136
  t138 = t31 * t122 * t137
  t141 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t142 = t141 * f.p.zeta_threshold
  t144 = f.my_piecewise3(t20, t142, t21 * t19)
  t145 = t5 * t144
  t146 = t31 ** 2
  t147 = 0.1e1 / t146
  t149 = t147 * t122 * t137
  t151 = t145 * t149 / 0.8e1
  t152 = params.k1 ** 2
  t153 = t69 ** 2
  t154 = 0.1e1 / t153
  t155 = t152 * t154
  t156 = t36 ** 2
  t158 = t33 / t156
  t159 = t41 * s0
  t160 = t158 * t159
  t161 = t43 ** 2
  t165 = 0.1e1 / t161 / r0 * t51 * t55
  t168 = t42 * r0
  t170 = 0.1e1 / t63 / t168
  t174 = -0.37671809081915277777777777777777777777777777777778e-3 * t160 * t165 - t59 * t62 * t170 / 0.9e1
  t180 = -0.5e1 / 0.3e1 * tau0 * t65 + s0 * t170 / 0.3e1
  t182 = t85 ** 2
  t183 = 0.1e1 / t182
  t184 = t79 * t183
  t185 = t82 * t170
  t188 = t180 * t86 + t184 * t185 / 0.3e1
  t189 = f.my_piecewise3(t89, 0, t188)
  t190 = params.c1 * t189
  t192 = t92 ** 2
  t193 = 0.1e1 / t192
  t196 = -t91 * t193 * t189 - t190 * t93
  t198 = f.my_piecewise3(t97, 0, t188)
  t200 = t98 * t198
  t202 = t100 * t198
  t204 = t102 * t198
  t206 = t104 * t198
  t208 = t106 * t198
  t213 = params.d * params.c2
  t214 = t114 ** 2
  t215 = 0.1e1 / t214
  t216 = f.my_piecewise3(t97, t188, 0)
  t220 = f.my_piecewise5(t88, t196 * t95, t96, -0.667e0 * t198 - 0.8891110e0 * t200 - 0.1989259803147e1 * t202 + 0.5805188177960e1 * t204 - 0.4439990207985e1 * t206 + 0.1407173648874e1 * t208 - 0.162300903254e0 * t108 * t198, -t213 * t215 * t216 * t117)
  t222 = t119 * t152
  t223 = t154 * t174
  t225 = t220 * t120 + t155 * t174 - t222 * t223
  t227 = t31 * t225 * t137
  t230 = 3 ** (0.1e1 / 0.6e1)
  t231 = t230 ** 2
  t232 = t231 ** 2
  t234 = t232 * t230 * t4
  t235 = t144 * t31
  t236 = t235 * t122
  t237 = t234 * t236
  t241 = 0.1e1 / t132 / t131 * t35 * t125
  t243 = 0.1e1 / t45 / t42
  t246 = t241 * t127 * t243 * t136
  t250 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t138 - t151 - 0.3e1 / 0.8e1 * t145 * t227 - 0.24739500000000000000000000000000000000000000000000e1 * t237 * t246)
  t252 = r1 <= f.p.dens_threshold
  t253 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t254 = 0.1e1 + t253
  t255 = t254 <= f.p.zeta_threshold
  t256 = t254 ** (0.1e1 / 0.3e1)
  t258 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t261 = f.my_piecewise3(t255, 0, 0.4e1 / 0.3e1 * t256 * t258)
  t262 = t5 * t261
  t263 = s2 ** 2
  t264 = r1 ** 2
  t265 = t264 ** 2
  t266 = t265 * r1
  t267 = r1 ** (0.1e1 / 0.3e1)
  t269 = 0.1e1 / t267 / t266
  t274 = jnp.exp(-t40 * t263 * t269 * t51 / 0.576e3)
  t278 = (-0.162742215233874e0 * t33 * t274 + 0.10e2 / 0.81e2) * t34
  t279 = t61 * s2
  t280 = t267 ** 2
  t282 = 0.1e1 / t280 / t264
  t286 = params.k1 + t278 * t279 * t282 / 0.24e2
  t290 = params.k1 * (0.1e1 - params.k1 / t286)
  t292 = 0.1e1 / t280 / r1
  t294 = s2 * t282
  t296 = tau1 * t292 - t294 / 0.8e1
  t297 = params.eta * s2
  t300 = t81 + t297 * t282 / 0.8e1
  t301 = 0.1e1 / t300
  t302 = t296 * t301
  t303 = t302 <= 0.0e0
  t304 = 0.0e0 < t302
  t305 = f.my_piecewise3(t304, 0, t302)
  t306 = params.c1 * t305
  t307 = 0.1e1 - t305
  t308 = 0.1e1 / t307
  t310 = jnp.exp(-t306 * t308)
  t311 = t302 <= 0.25e1
  t312 = 0.25e1 < t302
  t313 = f.my_piecewise3(t312, 0.25e1, t302)
  t315 = t313 ** 2
  t317 = t315 * t313
  t319 = t315 ** 2
  t321 = t319 * t313
  t323 = t319 * t315
  t328 = f.my_piecewise3(t312, t302, 0.25e1)
  t329 = 0.1e1 - t328
  t332 = jnp.exp(params.c2 / t329)
  t334 = f.my_piecewise5(t303, t310, t311, 0.1e1 - 0.667e0 * t313 - 0.4445555e0 * t315 - 0.663086601049e0 * t317 + 0.1451297044490e1 * t319 - 0.887998041597e0 * t321 + 0.234528941479e0 * t323 - 0.23185843322e-1 * t319 * t317, -params.d * t332)
  t335 = 0.174e0 - t290
  t337 = t334 * t335 + t290 + 0.1e1
  t339 = jnp.sqrt(s2)
  t340 = t267 * r1
  t341 = 0.1e1 / t340
  t343 = t126 * t339 * t341
  t344 = jnp.sqrt(t343)
  t348 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t124 / t344)
  t349 = 0.1e1 - t348
  t350 = t31 * t337 * t349
  t354 = f.my_piecewise3(t255, t142, t256 * t254)
  t355 = t5 * t354
  t357 = t147 * t337 * t349
  t359 = t355 * t357 / 0.8e1
  t361 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t262 * t350 - t359)
  t363 = t21 ** 2
  t364 = 0.1e1 / t363
  t365 = t26 ** 2
  t370 = t16 / t22 / t6
  t372 = -0.2e1 * t23 + 0.2e1 * t370
  t373 = f.my_piecewise5(t10, 0, t14, 0, t372)
  t377 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t364 * t365 + 0.4e1 / 0.3e1 * t21 * t373)
  t381 = t30 * t149
  t387 = t234 * t29 * t31 * t122
  t391 = 0.1e1 / t146 / t6
  t395 = t145 * t391 * t122 * t137 / 0.12e2
  t398 = t145 * t147 * t225 * t137
  t402 = t234 * t144 * t147 * t122
  t403 = t402 * t246
  t406 = 0.1e1 / t153 / t69
  t407 = t152 * t406
  t408 = t174 ** 2
  t417 = t41 ** 2
  t419 = t43 * t168
  t425 = t50 ** 2
  t427 = 0.1e1 / t425 * t35
  t429 = t427 * t39 * t55
  t433 = 0.1e1 / t63 / t43
  t437 = 0.43950443928901157407407407407407407407407407407407e-2 * t160 / t161 / t42 * t51 * t55 - 0.34881304705477109053497942386831275720164609053498e-5 * t158 * t417 * s0 / t45 / t161 / t419 * t429 + 0.11e2 / 0.27e2 * t59 * t62 * t433
  t441 = s0 * t433
  t445 = t180 * t183
  t450 = t79 / t182 / t85
  t451 = params.eta ** 2
  t461 = (0.40e2 / 0.9e1 * tau0 * t170 - 0.11e2 / 0.9e1 * t441) * t86 + 0.2e1 / 0.3e1 * t445 * t185 + 0.2e1 / 0.9e1 * t450 * t451 * t41 / t45 / t419 - 0.11e2 / 0.9e1 * t184 * t82 * t433
  t462 = f.my_piecewise3(t89, 0, t461)
  t465 = t189 ** 2
  t470 = 0.1e1 / t192 / t92
  t478 = t196 ** 2
  t481 = f.my_piecewise3(t97, 0, t461)
  t483 = t198 ** 2
  t507 = -0.667e0 * t481 - 0.8891110e0 * t483 - 0.8891110e0 * t98 * t481 - 0.3978519606294e1 * t98 * t483 - 0.1989259803147e1 * t100 * t481 + 0.17415564533880e2 * t100 * t483 + 0.5805188177960e1 * t102 * t481 - 0.17759960831940e2 * t102 * t483 - 0.4439990207985e1 * t104 * t481 + 0.7035868244370e1 * t104 * t483 + 0.1407173648874e1 * t106 * t481 - 0.973805419524e0 * t106 * t483 - 0.162300903254e0 * t108 * t481
  t509 = 0.1e1 / t214 / t114
  t510 = t216 ** 2
  t515 = f.my_piecewise3(t97, t461, 0)
  t519 = params.c2 ** 2
  t520 = params.d * t519
  t521 = t214 ** 2
  t522 = 0.1e1 / t521
  t527 = f.my_piecewise5(t88, (-t91 * t193 * t462 - 0.2e1 * params.c1 * t465 * t193 - params.c1 * t462 * t93 - 0.2e1 * t91 * t470 * t465) * t95 + t478 * t95, t96, t507, -t213 * t215 * t515 * t117 - 0.2e1 * t213 * t509 * t510 * t117 - t520 * t522 * t510 * t117)
  t529 = t220 * t152
  t543 = t234 * t235 * t225
  t546 = t34 * t61
  t551 = 0.1e1 / t132 / t546 / t77 * t34 / 0.6e1
  t552 = t551 * t61
  t564 = t3 ** 2
  t566 = t2 * t564 * jnp.pi
  t567 = t566 * t236
  t568 = 0.1e1 / t127
  t571 = t546 * t136
  t575 = -0.3e1 / 0.8e1 * t5 * t377 * t138 - t381 / 0.4e1 - 0.3e1 / 0.4e1 * t30 * t227 - 0.49479000000000000000000000000000000000000000000000e1 * t387 * t246 + t395 - t398 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t403 - 0.3e1 / 0.8e1 * t145 * t31 * (-t222 * t154 * t437 + 0.2e1 * t222 * t406 * t408 + t527 * t120 + t155 * t437 - 0.2e1 * t529 * t223 - 0.2e1 * t407 * t408) * t137 - 0.49479000000000000000000000000000000000000000000000e1 * t543 * t246 - 0.29687400000000000000000000000000000000000000000000e2 * t237 * t552 * t441 * t136 + 0.57725500000000000000000000000000000000000000000000e1 * t237 * t241 * t127 / t45 / t168 * t136 + 0.81605714700000000000000000000000000000000000000000e1 * t567 * t568 / t63 * t571
  t576 = f.my_piecewise3(t1, 0, t575)
  t577 = t256 ** 2
  t578 = 0.1e1 / t577
  t579 = t258 ** 2
  t583 = f.my_piecewise5(t14, 0, t10, 0, -t372)
  t587 = f.my_piecewise3(t255, 0, 0.4e1 / 0.9e1 * t578 * t579 + 0.4e1 / 0.3e1 * t256 * t583)
  t591 = t262 * t357
  t596 = t355 * t391 * t337 * t349 / 0.12e2
  t598 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t5 * t587 * t350 - t591 / 0.4e1 + t596)
  d11 = 0.2e1 * t250 + 0.2e1 * t361 + t6 * (t576 + t598)
  t601 = -t7 - t24
  t602 = f.my_piecewise5(t10, 0, t14, 0, t601)
  t605 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t602)
  t606 = t5 * t605
  t610 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t606 * t138 - t151)
  t612 = f.my_piecewise5(t14, 0, t10, 0, -t601)
  t615 = f.my_piecewise3(t255, 0, 0.4e1 / 0.3e1 * t256 * t612)
  t616 = t5 * t615
  t619 = t286 ** 2
  t620 = 0.1e1 / t619
  t621 = t152 * t620
  t622 = t263 * s2
  t623 = t158 * t622
  t624 = t265 ** 2
  t628 = 0.1e1 / t624 / r1 * t51 * t274
  t631 = t264 * r1
  t633 = 0.1e1 / t280 / t631
  t637 = -0.37671809081915277777777777777777777777777777777778e-3 * t623 * t628 - t278 * t279 * t633 / 0.9e1
  t643 = -0.5e1 / 0.3e1 * tau1 * t282 + s2 * t633 / 0.3e1
  t645 = t300 ** 2
  t646 = 0.1e1 / t645
  t647 = t296 * t646
  t648 = t297 * t633
  t651 = t643 * t301 + t647 * t648 / 0.3e1
  t652 = f.my_piecewise3(t304, 0, t651)
  t653 = params.c1 * t652
  t655 = t307 ** 2
  t656 = 0.1e1 / t655
  t659 = -t306 * t656 * t652 - t653 * t308
  t661 = f.my_piecewise3(t312, 0, t651)
  t663 = t313 * t661
  t665 = t315 * t661
  t667 = t317 * t661
  t669 = t319 * t661
  t671 = t321 * t661
  t676 = t329 ** 2
  t677 = 0.1e1 / t676
  t678 = f.my_piecewise3(t312, t651, 0)
  t682 = f.my_piecewise5(t303, t659 * t310, t311, -0.667e0 * t661 - 0.8891110e0 * t663 - 0.1989259803147e1 * t665 + 0.5805188177960e1 * t667 - 0.4439990207985e1 * t669 + 0.1407173648874e1 * t671 - 0.162300903254e0 * t323 * t661, -t213 * t677 * t678 * t332)
  t684 = t334 * t152
  t685 = t620 * t637
  t687 = t682 * t335 + t621 * t637 - t684 * t685
  t689 = t31 * t687 * t349
  t692 = t354 * t31
  t693 = t692 * t337
  t694 = t234 * t693
  t698 = 0.1e1 / t344 / t343 * t35 * t125
  t700 = 0.1e1 / t267 / t264
  t703 = t698 * t339 * t700 * t348
  t707 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t616 * t350 - t359 - 0.3e1 / 0.8e1 * t355 * t689 - 0.24739500000000000000000000000000000000000000000000e1 * t694 * t703)
  t711 = 0.2e1 * t370
  t712 = f.my_piecewise5(t10, 0, t14, 0, t711)
  t716 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t364 * t26 * t602 + 0.4e1 / 0.3e1 * t21 * t712)
  t721 = t606 * t149
  t728 = t234 * t605 * t31 * t122
  t733 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t716 * t138 - t381 / 0.8e1 - t721 / 0.8e1 + t395 - 0.3e1 / 0.8e1 * t606 * t227 - t398 / 0.8e1 - 0.24739500000000000000000000000000000000000000000000e1 * t728 * t246 - 0.82465000000000000000000000000000000000000000000000e0 * t403)
  t737 = f.my_piecewise5(t14, 0, t10, 0, -t711)
  t741 = f.my_piecewise3(t255, 0, 0.4e1 / 0.9e1 * t578 * t258 * t612 + 0.4e1 / 0.3e1 * t256 * t737)
  t750 = t234 * t261 * t31 * t337
  t753 = t616 * t357
  t757 = t355 * t147 * t687 * t349
  t761 = t234 * t354 * t147 * t337
  t762 = t761 * t703
  t765 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t5 * t741 * t350 - t591 / 0.8e1 - 0.3e1 / 0.8e1 * t262 * t689 - 0.24739500000000000000000000000000000000000000000000e1 * t750 * t703 - t753 / 0.8e1 + t596 - t757 / 0.8e1 - 0.82465000000000000000000000000000000000000000000000e0 * t762)
  d12 = t610 + t707 + t250 + t361 + t6 * (t733 + t765)
  t770 = t602 ** 2
  t774 = 0.2e1 * t23 + 0.2e1 * t370
  t775 = f.my_piecewise5(t10, 0, t14, 0, t774)
  t779 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t364 * t770 + 0.4e1 / 0.3e1 * t21 * t775)
  t785 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t779 * t138 - t721 / 0.4e1 + t395)
  t786 = t612 ** 2
  t790 = f.my_piecewise5(t14, 0, t10, 0, -t774)
  t794 = f.my_piecewise3(t255, 0, 0.4e1 / 0.9e1 * t578 * t786 + 0.4e1 / 0.3e1 * t256 * t790)
  t803 = t234 * t615 * t31 * t337
  t809 = 0.1e1 / t619 / t286
  t810 = t152 * t809
  t811 = t637 ** 2
  t820 = t263 ** 2
  t822 = t265 * t631
  t829 = t427 * t39 * t274
  t833 = 0.1e1 / t280 / t265
  t837 = 0.43950443928901157407407407407407407407407407407407e-2 * t623 / t624 / t264 * t51 * t274 - 0.34881304705477109053497942386831275720164609053498e-5 * t158 * t820 * s2 / t267 / t624 / t822 * t829 + 0.11e2 / 0.27e2 * t278 * t279 * t833
  t841 = s2 * t833
  t845 = t643 * t646
  t850 = t296 / t645 / t300
  t860 = (0.40e2 / 0.9e1 * tau1 * t633 - 0.11e2 / 0.9e1 * t841) * t301 + 0.2e1 / 0.3e1 * t845 * t648 + 0.2e1 / 0.9e1 * t850 * t451 * t263 / t267 / t822 - 0.11e2 / 0.9e1 * t647 * t297 * t833
  t861 = f.my_piecewise3(t304, 0, t860)
  t864 = t652 ** 2
  t869 = 0.1e1 / t655 / t307
  t877 = t659 ** 2
  t880 = f.my_piecewise3(t312, 0, t860)
  t882 = t661 ** 2
  t906 = -0.667e0 * t880 - 0.8891110e0 * t882 - 0.8891110e0 * t313 * t880 - 0.3978519606294e1 * t313 * t882 - 0.1989259803147e1 * t315 * t880 + 0.17415564533880e2 * t315 * t882 + 0.5805188177960e1 * t317 * t880 - 0.17759960831940e2 * t317 * t882 - 0.4439990207985e1 * t319 * t880 + 0.7035868244370e1 * t319 * t882 + 0.1407173648874e1 * t321 * t880 - 0.973805419524e0 * t321 * t882 - 0.162300903254e0 * t323 * t880
  t908 = 0.1e1 / t676 / t329
  t909 = t678 ** 2
  t914 = f.my_piecewise3(t312, t860, 0)
  t918 = t676 ** 2
  t919 = 0.1e1 / t918
  t924 = f.my_piecewise5(t303, (-t306 * t656 * t861 - 0.2e1 * t306 * t869 * t864 - params.c1 * t861 * t308 - 0.2e1 * params.c1 * t864 * t656) * t310 + t877 * t310, t311, t906, -t213 * t677 * t914 * t332 - 0.2e1 * t213 * t908 * t909 * t332 - t520 * t919 * t909 * t332)
  t926 = t682 * t152
  t940 = t234 * t692 * t687
  t947 = 0.1e1 / t344 / t546 / t294 * t34 / 0.6e1
  t948 = t947 * t61
  t960 = t566 * t693
  t961 = 0.1e1 / t339
  t964 = t546 * t348
  t968 = -0.3e1 / 0.8e1 * t5 * t794 * t350 - t753 / 0.4e1 - 0.3e1 / 0.4e1 * t616 * t689 - 0.49479000000000000000000000000000000000000000000000e1 * t803 * t703 + t596 - t757 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t762 - 0.3e1 / 0.8e1 * t355 * t31 * (-t684 * t620 * t837 + 0.2e1 * t684 * t809 * t811 + t924 * t335 + t621 * t837 - 0.2e1 * t926 * t685 - 0.2e1 * t810 * t811) * t349 - 0.49479000000000000000000000000000000000000000000000e1 * t940 * t703 - 0.29687400000000000000000000000000000000000000000000e2 * t694 * t948 * t841 * t348 + 0.57725500000000000000000000000000000000000000000000e1 * t694 * t698 * t339 / t267 / t631 * t348 + 0.81605714700000000000000000000000000000000000000000e1 * t960 * t961 / t280 * t964
  t969 = f.my_piecewise3(t252, 0, t968)
  d22 = 0.2e1 * t610 + 0.2e1 * t707 + t6 * (t785 + t969)
  t972 = t158 * t41
  t975 = 0.1e1 / t161 * t51 * t55
  t981 = 0.14126928405718229166666666666666666666666666666667e-3 * t972 * t975 + t59 * t61 * t65 / 0.24e2
  t983 = t65 * t86
  t984 = params.eta * t65
  t987 = -t184 * t984 / 0.8e1 - t983 / 0.8e1
  t988 = f.my_piecewise3(t89, 0, t987)
  t989 = params.c1 * t988
  t991 = t193 * t988
  t993 = -t91 * t991 - t989 * t93
  t995 = f.my_piecewise3(t97, 0, t987)
  t997 = t98 * t995
  t999 = t100 * t995
  t1001 = t102 * t995
  t1003 = t104 * t995
  t1005 = t106 * t995
  t1010 = f.my_piecewise3(t97, t987, 0)
  t1014 = f.my_piecewise5(t88, t993 * t95, t96, -0.667e0 * t995 - 0.8891110e0 * t997 - 0.1989259803147e1 * t999 + 0.5805188177960e1 * t1001 - 0.4439990207985e1 * t1003 + 0.1407173648874e1 * t1005 - 0.162300903254e0 * t108 * t995, -t213 * t215 * t1010 * t117)
  t1016 = t154 * t981
  t1018 = t1014 * t120 - t222 * t1016 + t155 * t981
  t1020 = t31 * t1018 * t137
  t1025 = t241 * t568 * t129 * t136
  t1029 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t145 * t1020 + 0.92773125000000000000000000000000000000000000000000e0 * t237 * t1025)
  t1037 = t145 * t147 * t1018 * t137 / 0.8e1
  t1039 = 0.30924375000000000000000000000000000000000000000000e0 * t402 * t1025
  t1045 = t43 * t42
  t1053 = t61 * t170
  t1056 = -0.15068723632766111111111111111111111111111111111111e-2 * t972 * t165 + 0.13080489264553915895061728395061728395061728395062e-5 * t158 * t417 / t45 / t161 / t1045 * t429 - t59 * t1053 / 0.9e1
  t1063 = 0.1e1 / t45 / t1045
  t1074 = t170 * t86 / 0.3e1 - t445 * t984 / 0.8e1 - t1063 * t183 * t82 / 0.24e2 - t450 * t451 * s0 * t1063 / 0.12e2 + t184 * params.eta * t170 / 0.3e1
  t1075 = f.my_piecewise3(t89, 0, t1074)
  t1080 = t470 * t189
  t1091 = f.my_piecewise3(t97, 0, t1074)
  t1117 = -0.667e0 * t1091 - 0.8891110e0 * t995 * t198 - 0.8891110e0 * t98 * t1091 - 0.3978519606294e1 * t200 * t995 - 0.1989259803147e1 * t100 * t1091 + 0.17415564533880e2 * t202 * t995 + 0.5805188177960e1 * t102 * t1091 - 0.17759960831940e2 * t204 * t995 - 0.4439990207985e1 * t104 * t1091 + 0.7035868244370e1 * t206 * t995 + 0.1407173648874e1 * t106 * t1091 - 0.973805419524e0 * t208 * t995 - 0.162300903254e0 * t108 * t1091
  t1118 = t213 * t509
  t1119 = t216 * t117
  t1120 = t1119 * t1010
  t1123 = f.my_piecewise3(t97, t1074, 0)
  t1127 = t520 * t522
  t1130 = f.my_piecewise5(t88, (-t91 * t193 * t1075 - params.c1 * t1075 * t93 - 0.2e1 * t91 * t1080 * t988 - 0.2e1 * t190 * t991) * t95 + t196 * t993 * t95, t96, t1117, -t213 * t215 * t1123 * t117 - 0.2e1 * t1118 * t1120 - t1127 * t1120)
  t1133 = t1014 * t152
  t1149 = t234 * t235 * t1018
  t1162 = 0.1e1 / t127 / s0
  t1168 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t1020 + 0.92773125000000000000000000000000000000000000000000e0 * t387 * t1025 - t1037 + t1039 - 0.3e1 / 0.8e1 * t145 * t31 * (0.2e1 * t222 * t406 * t174 * t981 - t222 * t154 * t1056 - 0.2e1 * t407 * t174 * t981 - t529 * t1016 + t155 * t1056 + t1130 * t120 - t1133 * t223) * t137 + 0.92773125000000000000000000000000000000000000000000e0 * t543 * t1025 - 0.24739500000000000000000000000000000000000000000000e1 * t1149 * t246 + 0.11132775000000000000000000000000000000000000000000e2 * t237 * t551 * t1053 * t136 - 0.12369750000000000000000000000000000000000000000000e1 * t237 * t241 * t568 * t243 * t136 - 0.30602143012500000000000000000000000000000000000000e1 * t567 * t1162 * t45 * t571)
  d13 = t6 * t1168 + t1029
  d14 = 0.0e0
  t1170 = t158 * t263
  t1173 = 0.1e1 / t624 * t51 * t274
  t1179 = 0.14126928405718229166666666666666666666666666666667e-3 * t1170 * t1173 + t278 * t61 * t282 / 0.24e2
  t1181 = t282 * t301
  t1182 = params.eta * t282
  t1185 = -t647 * t1182 / 0.8e1 - t1181 / 0.8e1
  t1186 = f.my_piecewise3(t304, 0, t1185)
  t1187 = params.c1 * t1186
  t1189 = t656 * t1186
  t1191 = -t1187 * t308 - t306 * t1189
  t1193 = f.my_piecewise3(t312, 0, t1185)
  t1195 = t313 * t1193
  t1197 = t315 * t1193
  t1199 = t317 * t1193
  t1201 = t319 * t1193
  t1203 = t321 * t1193
  t1208 = f.my_piecewise3(t312, t1185, 0)
  t1212 = f.my_piecewise5(t303, t1191 * t310, t311, -0.667e0 * t1193 - 0.8891110e0 * t1195 - 0.1989259803147e1 * t1197 + 0.5805188177960e1 * t1199 - 0.4439990207985e1 * t1201 + 0.1407173648874e1 * t1203 - 0.162300903254e0 * t323 * t1193, -t213 * t677 * t1208 * t332)
  t1214 = t620 * t1179
  t1216 = t621 * t1179 + t1212 * t335 - t684 * t1214
  t1218 = t31 * t1216 * t349
  t1223 = t698 * t961 * t341 * t348
  t1227 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t355 * t1218 + 0.92773125000000000000000000000000000000000000000000e0 * t694 * t1223)
  t1235 = t355 * t147 * t1216 * t349 / 0.8e1
  t1237 = 0.30924375000000000000000000000000000000000000000000e0 * t761 * t1223
  t1239 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t262 * t1218 + 0.92773125000000000000000000000000000000000000000000e0 * t750 * t1223 - t1235 + t1237)
  d15 = t6 * t1239 + t1227
  t1246 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t606 * t1020 + 0.92773125000000000000000000000000000000000000000000e0 * t728 * t1025 - t1037 + t1039)
  d23 = t6 * t1246 + t1029
  d24 = 0.0e0
  t1257 = t265 * t264
  t1265 = t61 * t633
  t1268 = -0.15068723632766111111111111111111111111111111111111e-2 * t1170 * t628 + 0.13080489264553915895061728395061728395061728395062e-5 * t158 * t820 / t267 / t624 / t1257 * t829 - t278 * t1265 / 0.9e1
  t1275 = 0.1e1 / t267 / t1257
  t1286 = t633 * t301 / 0.3e1 - t845 * t1182 / 0.8e1 - t1275 * t646 * t297 / 0.24e2 - t850 * t451 * s2 * t1275 / 0.12e2 + t647 * params.eta * t633 / 0.3e1
  t1287 = f.my_piecewise3(t304, 0, t1286)
  t1292 = t869 * t652
  t1303 = f.my_piecewise3(t312, 0, t1286)
  t1329 = -0.667e0 * t1303 - 0.8891110e0 * t1193 * t661 - 0.8891110e0 * t313 * t1303 - 0.3978519606294e1 * t663 * t1193 - 0.1989259803147e1 * t315 * t1303 + 0.17415564533880e2 * t665 * t1193 + 0.5805188177960e1 * t317 * t1303 - 0.17759960831940e2 * t667 * t1193 - 0.4439990207985e1 * t319 * t1303 + 0.7035868244370e1 * t669 * t1193 + 0.1407173648874e1 * t321 * t1303 - 0.973805419524e0 * t671 * t1193 - 0.162300903254e0 * t323 * t1303
  t1330 = t213 * t908
  t1331 = t678 * t332
  t1332 = t1331 * t1208
  t1335 = f.my_piecewise3(t312, t1286, 0)
  t1339 = t520 * t919
  t1342 = f.my_piecewise5(t303, (-0.2e1 * t306 * t1292 * t1186 - t306 * t656 * t1287 - params.c1 * t1287 * t308 - 0.2e1 * t653 * t1189) * t310 + t659 * t1191 * t310, t311, t1329, -t213 * t677 * t1335 * t332 - 0.2e1 * t1330 * t1332 - t1339 * t1332)
  t1345 = t1212 * t152
  t1361 = t234 * t692 * t1216
  t1374 = 0.1e1 / t339 / s2
  t1380 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t616 * t1218 + 0.92773125000000000000000000000000000000000000000000e0 * t803 * t1223 - t1235 + t1237 - 0.3e1 / 0.8e1 * t355 * t31 * (0.2e1 * t684 * t809 * t637 * t1179 - 0.2e1 * t810 * t637 * t1179 - t684 * t620 * t1268 - t926 * t1214 + t621 * t1268 + t1342 * t335 - t1345 * t685) * t349 + 0.92773125000000000000000000000000000000000000000000e0 * t940 * t1223 - 0.24739500000000000000000000000000000000000000000000e1 * t1361 * t703 + 0.11132775000000000000000000000000000000000000000000e2 * t694 * t947 * t1265 * t348 - 0.12369750000000000000000000000000000000000000000000e1 * t694 * t698 * t961 * t700 * t348 - 0.30602143012500000000000000000000000000000000000000e1 * t960 * t1374 * t267 * t964)
  d25 = t6 * t1380 + t1227
  t1382 = t981 ** 2
  t1395 = 0.42380785217154687500000000000000000000000000000001e-3 * t158 * s0 * t975 - 0.49051834742077184606481481481481481481481481481483e-6 * t158 * t159 / t45 / t161 / t44 * t429
  t1397 = t47 * t183
  t1402 = t450 * t451 * t47 / 0.32e2 + t1397 * params.eta / 0.32e2
  t1403 = f.my_piecewise3(t89, 0, t1402)
  t1406 = t988 ** 2
  t1417 = t993 ** 2
  t1420 = f.my_piecewise3(t97, 0, t1402)
  t1422 = t995 ** 2
  t1446 = -0.667e0 * t1420 - 0.8891110e0 * t1422 - 0.8891110e0 * t98 * t1420 - 0.3978519606294e1 * t98 * t1422 - 0.1989259803147e1 * t100 * t1420 + 0.17415564533880e2 * t100 * t1422 + 0.5805188177960e1 * t102 * t1420 - 0.17759960831940e2 * t102 * t1422 - 0.4439990207985e1 * t104 * t1420 + 0.7035868244370e1 * t104 * t1422 + 0.1407173648874e1 * t106 * t1420 - 0.973805419524e0 * t106 * t1422 - 0.162300903254e0 * t108 * t1420
  t1447 = t1010 ** 2
  t1452 = f.my_piecewise3(t97, t1402, 0)
  t1460 = f.my_piecewise5(t88, (-t91 * t193 * t1403 - params.c1 * t1403 * t93 - 0.2e1 * params.c1 * t1406 * t193 - 0.2e1 * t91 * t470 * t1406) * t95 + t1417 * t95, t96, t1446, -0.2e1 * t213 * t509 * t1447 * t117 - t520 * t522 * t1447 * t117 - t213 * t215 * t1452 * t117)
  t1494 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t145 * t31 * (0.2e1 * t222 * t406 * t1382 - t222 * t154 * t1395 - 0.2e1 * t1133 * t1016 + t1460 * t120 - 0.2e1 * t407 * t1382 + t155 * t1395) * t137 + 0.18554625000000000000000000000000000000000000000000e1 * t1149 * t1025 - 0.41747906250000000000000000000000000000000000000000e1 * t237 * t552 / s0 * t65 * t136 - 0.46386562500000000000000000000000000000000000000000e0 * t237 * t241 * t1162 * t129 * t136 + 0.11475803629687500000000000000000000000000000000000e1 * t567 / t127 / t41 * t128 * t571)
  d33 = t6 * t1494
  d34 = 0.0e0
  d35 = 0.0e0
  d44 = 0.0e0
  d45 = 0.0e0
  t1495 = t1179 ** 2
  t1508 = 0.42380785217154687500000000000000000000000000000001e-3 * t158 * s2 * t1173 - 0.49051834742077184606481481481481481481481481481483e-6 * t158 * t622 / t267 / t624 / t266 * t829
  t1510 = t269 * t646
  t1515 = t850 * t451 * t269 / 0.32e2 + t1510 * params.eta / 0.32e2
  t1516 = f.my_piecewise3(t304, 0, t1515)
  t1519 = t1186 ** 2
  t1530 = t1191 ** 2
  t1533 = f.my_piecewise3(t312, 0, t1515)
  t1535 = t1193 ** 2
  t1559 = -0.667e0 * t1533 - 0.8891110e0 * t1535 - 0.8891110e0 * t313 * t1533 - 0.3978519606294e1 * t313 * t1535 - 0.1989259803147e1 * t315 * t1533 + 0.17415564533880e2 * t315 * t1535 + 0.5805188177960e1 * t317 * t1533 - 0.17759960831940e2 * t317 * t1535 - 0.4439990207985e1 * t319 * t1533 + 0.7035868244370e1 * t319 * t1535 + 0.1407173648874e1 * t321 * t1533 - 0.973805419524e0 * t321 * t1535 - 0.162300903254e0 * t323 * t1533
  t1560 = t1208 ** 2
  t1565 = f.my_piecewise3(t312, t1515, 0)
  t1573 = f.my_piecewise5(t303, (-t306 * t656 * t1516 - params.c1 * t1516 * t308 - 0.2e1 * t306 * t869 * t1519 - 0.2e1 * params.c1 * t1519 * t656) * t310 + t1530 * t310, t311, t1559, -0.2e1 * t213 * t908 * t1560 * t332 - t520 * t919 * t1560 * t332 - t213 * t677 * t1565 * t332)
  t1607 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t355 * t31 * (0.2e1 * t684 * t809 * t1495 - t684 * t620 * t1508 - 0.2e1 * t1345 * t1214 - 0.2e1 * t810 * t1495 + t621 * t1508 + t1573 * t335) * t349 + 0.18554625000000000000000000000000000000000000000000e1 * t1361 * t1223 - 0.41747906250000000000000000000000000000000000000000e1 * t694 * t948 / s2 * t282 * t348 - 0.46386562500000000000000000000000000000000000000000e0 * t694 * t698 * t1374 * t341 * t348 + 0.11475803629687500000000000000000000000000000000000e1 * t960 / t339 / t263 * t340 * t964)
  d55 = t6 * t1607
  d16 = 0.0e0
  d17 = 0.0e0
  d26 = 0.0e0
  d27 = 0.0e0
  t1608 = t75 * t86
  t1609 = f.my_piecewise3(t89, 0, t1608)
  t1612 = t193 * t1609
  t1614 = -params.c1 * t1609 * t93 - t91 * t1612
  t1616 = f.my_piecewise3(t97, 0, t1608)
  t1631 = f.my_piecewise3(t97, t1608, 0)
  t1635 = f.my_piecewise5(t88, t1614 * t95, t96, -0.667e0 * t1616 - 0.8891110e0 * t98 * t1616 - 0.1989259803147e1 * t100 * t1616 + 0.5805188177960e1 * t102 * t1616 - 0.4439990207985e1 * t104 * t1616 + 0.1407173648874e1 * t106 * t1616 - 0.162300903254e0 * t108 * t1616, -t213 * t215 * t1631 * t117)
  t1636 = t31 * t1635
  t1637 = t120 * t137
  t1638 = t1636 * t1637
  t1641 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t145 * t1638)
  t1647 = t145 * t147 * t1635 * t1637 / 0.8e1
  t1651 = -0.5e1 / 0.3e1 * t983 + t1397 * t82 / 0.3e1
  t1652 = f.my_piecewise3(t89, 0, t1651)
  t1667 = f.my_piecewise3(t97, 0, t1651)
  t1693 = -0.667e0 * t1667 - 0.8891110e0 * t1616 * t198 - 0.8891110e0 * t98 * t1667 - 0.3978519606294e1 * t200 * t1616 - 0.1989259803147e1 * t100 * t1667 + 0.17415564533880e2 * t202 * t1616 + 0.5805188177960e1 * t102 * t1667 - 0.17759960831940e2 * t204 * t1616 - 0.4439990207985e1 * t104 * t1667 + 0.7035868244370e1 * t206 * t1616 + 0.1407173648874e1 * t106 * t1667 - 0.973805419524e0 * t208 * t1616 - 0.162300903254e0 * t108 * t1667
  t1694 = t1119 * t1631
  t1697 = f.my_piecewise3(t97, t1651, 0)
  t1703 = f.my_piecewise5(t88, (-0.2e1 * t91 * t1080 * t1609 - t91 * t193 * t1652 - params.c1 * t1652 * t93 - 0.2e1 * t190 * t1612) * t95 + t196 * t1614 * t95, t96, t1693, -t213 * t215 * t1697 * t117 - 0.2e1 * t1118 * t1694 - t1127 * t1694)
  t1705 = t1635 * t152
  t1714 = t234 * t144 * t1636 * t120
  t1718 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t30 * t1638 - t1647 - 0.3e1 / 0.8e1 * t145 * t31 * (t1703 * t120 - t1705 * t223) * t137 - 0.24739500000000000000000000000000000000000000000000e1 * t1714 * t246)
  d18 = t6 * t1718 + t1641
  t1720 = t292 * t301
  t1721 = f.my_piecewise3(t304, 0, t1720)
  t1724 = t656 * t1721
  t1726 = -params.c1 * t1721 * t308 - t306 * t1724
  t1728 = f.my_piecewise3(t312, 0, t1720)
  t1743 = f.my_piecewise3(t312, t1720, 0)
  t1747 = f.my_piecewise5(t303, t1726 * t310, t311, -0.667e0 * t1728 - 0.8891110e0 * t313 * t1728 - 0.1989259803147e1 * t315 * t1728 + 0.5805188177960e1 * t317 * t1728 - 0.4439990207985e1 * t319 * t1728 + 0.1407173648874e1 * t321 * t1728 - 0.162300903254e0 * t323 * t1728, -t213 * t677 * t1743 * t332)
  t1748 = t31 * t1747
  t1749 = t335 * t349
  t1750 = t1748 * t1749
  t1753 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t355 * t1750)
  t1759 = t355 * t147 * t1747 * t1749 / 0.8e1
  t1761 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t262 * t1750 - t1759)
  d19 = t6 * t1761 + t1753
  t1766 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t606 * t1638 - t1647)
  d28 = t6 * t1766 + t1641
  t1773 = -0.5e1 / 0.3e1 * t1181 + t1510 * t297 / 0.3e1
  t1774 = f.my_piecewise3(t304, 0, t1773)
  t1789 = f.my_piecewise3(t312, 0, t1773)
  t1815 = -0.667e0 * t1789 - 0.8891110e0 * t1728 * t661 - 0.8891110e0 * t313 * t1789 - 0.3978519606294e1 * t663 * t1728 - 0.1989259803147e1 * t315 * t1789 + 0.17415564533880e2 * t665 * t1728 + 0.5805188177960e1 * t317 * t1789 - 0.17759960831940e2 * t667 * t1728 - 0.4439990207985e1 * t319 * t1789 + 0.7035868244370e1 * t669 * t1728 + 0.1407173648874e1 * t321 * t1789 - 0.973805419524e0 * t671 * t1728 - 0.162300903254e0 * t323 * t1789
  t1816 = t1331 * t1743
  t1819 = f.my_piecewise3(t312, t1773, 0)
  t1825 = f.my_piecewise5(t303, (-0.2e1 * t306 * t1292 * t1721 - t306 * t656 * t1774 - params.c1 * t1774 * t308 - 0.2e1 * t653 * t1724) * t310 + t659 * t1726 * t310, t311, t1815, -t213 * t677 * t1819 * t332 - 0.2e1 * t1330 * t1816 - t1339 * t1816)
  t1827 = t1747 * t152
  t1836 = t234 * t354 * t1748 * t335
  t1840 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t616 * t1750 - t1759 - 0.3e1 / 0.8e1 * t355 * t31 * (t1825 * t335 - t1827 * t685) * t349 - 0.24739500000000000000000000000000000000000000000000e1 * t1836 * t703)
  d29 = t6 * t1840 + t1753
  d36 = 0.0e0
  d37 = 0.0e0
  d46 = 0.0e0
  d47 = 0.0e0
  d56 = 0.0e0
  d57 = 0.0e0
  t1846 = 0.1e1 / t45 / t43 * t183 * params.eta / 0.8e1
  t1847 = f.my_piecewise3(t89, 0, -t1846)
  t1863 = f.my_piecewise3(t97, 0, -t1846)
  t1889 = -0.667e0 * t1863 - 0.8891110e0 * t1616 * t995 - 0.8891110e0 * t98 * t1863 - 0.3978519606294e1 * t997 * t1616 - 0.1989259803147e1 * t100 * t1863 + 0.17415564533880e2 * t999 * t1616 + 0.5805188177960e1 * t102 * t1863 - 0.17759960831940e2 * t1001 * t1616 - 0.4439990207985e1 * t104 * t1863 + 0.7035868244370e1 * t1003 * t1616 + 0.1407173648874e1 * t106 * t1863 - 0.973805419524e0 * t1005 * t1616 - 0.162300903254e0 * t108 * t1863
  t1891 = t1010 * t117 * t1631
  t1894 = f.my_piecewise3(t97, -t1846, 0)
  t1900 = f.my_piecewise5(t88, (-0.2e1 * t91 * t470 * t988 * t1609 - t91 * t193 * t1847 - params.c1 * t1847 * t93 - 0.2e1 * t989 * t1612) * t95 + t993 * t1614 * t95, t96, t1889, -t213 * t215 * t1894 * t117 - 0.2e1 * t1118 * t1891 - t1127 * t1891)
  t1911 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t145 * t31 * (-t1705 * t1016 + t1900 * t120) * t137 + 0.92773125000000000000000000000000000000000000000000e0 * t1714 * t1025)
  d38 = t6 * t1911
  d39 = 0.0e0
  d48 = 0.0e0
  d49 = 0.0e0
  d58 = 0.0e0
  t1916 = 0.1e1 / t267 / t265 * t646 * params.eta / 0.8e1
  t1917 = f.my_piecewise3(t304, 0, -t1916)
  t1933 = f.my_piecewise3(t312, 0, -t1916)
  t1959 = -0.667e0 * t1933 - 0.8891110e0 * t1728 * t1193 - 0.8891110e0 * t313 * t1933 - 0.3978519606294e1 * t1195 * t1728 - 0.1989259803147e1 * t315 * t1933 + 0.17415564533880e2 * t1197 * t1728 + 0.5805188177960e1 * t317 * t1933 - 0.17759960831940e2 * t1199 * t1728 - 0.4439990207985e1 * t319 * t1933 + 0.7035868244370e1 * t1201 * t1728 + 0.1407173648874e1 * t321 * t1933 - 0.973805419524e0 * t1203 * t1728 - 0.162300903254e0 * t323 * t1933
  t1961 = t1208 * t332 * t1743
  t1964 = f.my_piecewise3(t312, -t1916, 0)
  t1970 = f.my_piecewise5(t303, (-0.2e1 * t306 * t869 * t1186 * t1721 - t306 * t656 * t1917 - params.c1 * t1917 * t308 - 0.2e1 * t1187 * t1724) * t310 + t1191 * t1726 * t310, t311, t1959, -t213 * t677 * t1964 * t332 - 0.2e1 * t1330 * t1961 - t1339 * t1961)
  t1981 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t355 * t31 * (-t1827 * t1214 + t1970 * t335) * t349 + 0.92773125000000000000000000000000000000000000000000e0 * t1836 * t1223)
  d59 = t6 * t1981
  d66 = 0.0e0
  d67 = 0.0e0
  d77 = 0.0e0
  d68 = 0.0e0
  d69 = 0.0e0
  d78 = 0.0e0
  d79 = 0.0e0
  t1982 = f.my_piecewise3(t89, 0, 0)
  t1985 = t1609 ** 2
  t1996 = t1614 ** 2
  t1999 = f.my_piecewise3(t97, 0, 0)
  t2001 = t1616 ** 2
  t2025 = -0.667e0 * t1999 - 0.8891110e0 * t2001 - 0.8891110e0 * t98 * t1999 - 0.3978519606294e1 * t98 * t2001 - 0.1989259803147e1 * t100 * t1999 + 0.17415564533880e2 * t100 * t2001 + 0.5805188177960e1 * t102 * t1999 - 0.17759960831940e2 * t102 * t2001 - 0.4439990207985e1 * t104 * t1999 + 0.7035868244370e1 * t104 * t2001 + 0.1407173648874e1 * t106 * t1999 - 0.973805419524e0 * t106 * t2001 - 0.162300903254e0 * t108 * t1999
  t2026 = t1631 ** 2
  t2038 = f.my_piecewise5(t88, (-t91 * t193 * t1982 - 0.2e1 * params.c1 * t1985 * t193 - params.c1 * t1982 * t93 - 0.2e1 * t91 * t470 * t1985) * t95 + t1996 * t95, t96, t2025, -t213 * t215 * t1999 * t117 - 0.2e1 * t213 * t509 * t2026 * t117 - t520 * t522 * t2026 * t117)
  t2043 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t145 * t31 * t2038 * t1637)
  d88 = t6 * t2043
  d89 = 0.0e0
  t2044 = f.my_piecewise3(t304, 0, 0)
  t2047 = t1721 ** 2
  t2058 = t1726 ** 2
  t2061 = f.my_piecewise3(t312, 0, 0)
  t2063 = t1728 ** 2
  t2087 = -0.667e0 * t2061 - 0.8891110e0 * t2063 - 0.8891110e0 * t313 * t2061 - 0.3978519606294e1 * t313 * t2063 - 0.1989259803147e1 * t315 * t2061 + 0.17415564533880e2 * t315 * t2063 + 0.5805188177960e1 * t317 * t2061 - 0.17759960831940e2 * t317 * t2063 - 0.4439990207985e1 * t319 * t2061 + 0.7035868244370e1 * t319 * t2063 + 0.1407173648874e1 * t321 * t2061 - 0.973805419524e0 * t321 * t2063 - 0.162300903254e0 * t323 * t2061
  t2088 = t1743 ** 2
  t2100 = f.my_piecewise5(t303, (-t306 * t656 * t2044 - params.c1 * t2044 * t308 - 0.2e1 * t306 * t869 * t2047 - 0.2e1 * params.c1 * t2047 * t656) * t310 + t2058 * t310, t311, t2087, -t213 * t677 * t2061 * t332 - 0.2e1 * t213 * t908 * t2088 * t332 - t520 * t919 * t2088 * t332)
  t2105 = f.my_piecewise3(t252, 0, -0.3e1 / 0.8e1 * t355 * t31 * t2100 * t1749)
  d99 = t6 * t2105
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

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
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
  t45 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t50 = t49 * t48
  t51 = 0.1e1 / t50
  t52 = t47 * t51
  t53 = s0 ** 2
  t54 = r0 ** 2
  t55 = t54 ** 2
  t56 = t55 * r0
  t57 = r0 ** (0.1e1 / 0.3e1)
  t61 = params.dp2 ** 2
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t67 = jnp.exp(-t52 * t53 / t57 / t56 * t63 / 0.576e3)
  t71 = (-0.162742215233874e0 * t45 * t67 + 0.10e2 / 0.81e2) * t46
  t72 = t49 ** 2
  t73 = 0.1e1 / t72
  t74 = t73 * s0
  t75 = t57 ** 2
  t77 = 0.1e1 / t75 / t54
  t81 = params.k1 + t71 * t74 * t77 / 0.24e2
  t85 = params.k1 * (0.1e1 - params.k1 / t81)
  t87 = 0.1e1 / t75 / r0
  t89 = s0 * t77
  t91 = tau0 * t87 - t89 / 0.8e1
  t93 = 0.3e1 / 0.10e2 * t47 * t72
  t94 = params.eta * s0
  t97 = t93 + t94 * t77 / 0.8e1
  t98 = 0.1e1 / t97
  t99 = t91 * t98
  t100 = t99 <= 0.0e0
  t101 = 0.0e0 < t99
  t102 = f.my_piecewise3(t101, 0, t99)
  t103 = params.c1 * t102
  t104 = 0.1e1 - t102
  t105 = 0.1e1 / t104
  t107 = jnp.exp(-t103 * t105)
  t108 = t99 <= 0.25e1
  t109 = 0.25e1 < t99
  t110 = f.my_piecewise3(t109, 0.25e1, t99)
  t112 = t110 ** 2
  t114 = t112 * t110
  t116 = t112 ** 2
  t118 = t116 * t110
  t120 = t116 * t112
  t125 = f.my_piecewise3(t109, t99, 0.25e1)
  t126 = 0.1e1 - t125
  t129 = jnp.exp(params.c2 / t126)
  t131 = f.my_piecewise5(t100, t107, t108, 0.1e1 - 0.667e0 * t110 - 0.4445555e0 * t112 - 0.663086601049e0 * t114 + 0.1451297044490e1 * t116 - 0.887998041597e0 * t118 + 0.234528941479e0 * t120 - 0.23185843322e-1 * t116 * t114, -params.d * t129)
  t132 = 0.174e0 - t85
  t134 = t131 * t132 + t85 + 0.1e1
  t136 = jnp.sqrt(0.3e1)
  t137 = 0.1e1 / t49
  t138 = t47 * t137
  t139 = jnp.sqrt(s0)
  t143 = t138 * t139 / t57 / r0
  t144 = jnp.sqrt(t143)
  t148 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t136 / t144)
  t149 = 0.1e1 - t148
  t150 = t43 * t134 * t149
  t155 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t156 = t5 * t155
  t157 = t43 ** 2
  t158 = 0.1e1 / t157
  t160 = t158 * t134 * t149
  t163 = params.k1 ** 2
  t164 = t81 ** 2
  t165 = 0.1e1 / t164
  t166 = t163 * t165
  t167 = t48 ** 2
  t169 = t45 / t167
  t170 = t53 * s0
  t171 = t169 * t170
  t172 = t55 ** 2
  t179 = t54 * r0
  t181 = 0.1e1 / t75 / t179
  t185 = -0.37671809081915277777777777777777777777777777777778e-3 * t171 / t172 / r0 * t63 * t67 - t71 * t74 * t181 / 0.9e1
  t191 = -0.5e1 / 0.3e1 * tau0 * t77 + s0 * t181 / 0.3e1
  t193 = t97 ** 2
  t194 = 0.1e1 / t193
  t195 = t91 * t194
  t196 = t94 * t181
  t199 = t191 * t98 + t195 * t196 / 0.3e1
  t200 = f.my_piecewise3(t101, 0, t199)
  t203 = t104 ** 2
  t204 = 0.1e1 / t203
  t205 = t204 * t200
  t207 = -params.c1 * t200 * t105 - t103 * t205
  t209 = f.my_piecewise3(t109, 0, t199)
  t211 = t110 * t209
  t213 = t112 * t209
  t215 = t114 * t209
  t217 = t116 * t209
  t219 = t118 * t209
  t224 = params.d * params.c2
  t225 = t126 ** 2
  t226 = 0.1e1 / t225
  t227 = f.my_piecewise3(t109, t199, 0)
  t231 = f.my_piecewise5(t100, t207 * t107, t108, -0.667e0 * t209 - 0.8891110e0 * t211 - 0.1989259803147e1 * t213 + 0.5805188177960e1 * t215 - 0.4439990207985e1 * t217 + 0.1407173648874e1 * t219 - 0.162300903254e0 * t120 * t209, -t224 * t226 * t227 * t129)
  t233 = t131 * t163
  t234 = t165 * t185
  t236 = t231 * t132 + t166 * t185 - t233 * t234
  t238 = t43 * t236 * t149
  t241 = 3 ** (0.1e1 / 0.6e1)
  t242 = t241 ** 2
  t243 = t242 ** 2
  t244 = t243 * t241
  t245 = t244 * t4
  t246 = t155 * t43
  t247 = t246 * t134
  t248 = t245 * t247
  t250 = 0.1e1 / t144 / t143
  t252 = t250 * t47 * t137
  t257 = t252 * t139 / t57 / t54 * t148
  t260 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t261 = t260 * f.p.zeta_threshold
  t263 = f.my_piecewise3(t20, t261, t21 * t19)
  t264 = t5 * t263
  t266 = 0.1e1 / t157 / t6
  t268 = t266 * t134 * t149
  t272 = t158 * t236 * t149
  t275 = t263 * t158
  t276 = t275 * t134
  t277 = t245 * t276
  t281 = 0.1e1 / t164 / t81
  t282 = t163 * t281
  t283 = t185 ** 2
  t292 = t53 ** 2
  t293 = t292 * s0
  t294 = t55 * t179
  t300 = t62 ** 2
  t304 = 0.1e1 / t300 * t47 * t51 * t67
  t308 = 0.1e1 / t75 / t55
  t312 = 0.43950443928901157407407407407407407407407407407407e-2 * t171 / t172 / t54 * t63 * t67 - 0.34881304705477109053497942386831275720164609053498e-5 * t169 * t293 / t57 / t172 / t294 * t304 + 0.11e2 / 0.27e2 * t71 * t74 * t308
  t316 = s0 * t308
  t318 = 0.40e2 / 0.9e1 * tau0 * t181 - 0.11e2 / 0.9e1 * t316
  t320 = t191 * t194
  t324 = 0.1e1 / t193 / t97
  t325 = t91 * t324
  t326 = params.eta ** 2
  t327 = t326 * t53
  t330 = t327 / t57 / t294
  t333 = t94 * t308
  t336 = t318 * t98 + 0.2e1 / 0.3e1 * t320 * t196 + 0.2e1 / 0.9e1 * t325 * t330 - 0.11e2 / 0.9e1 * t195 * t333
  t337 = f.my_piecewise3(t101, 0, t336)
  t338 = params.c1 * t337
  t340 = t200 ** 2
  t345 = 0.1e1 / t203 / t104
  t351 = -t103 * t204 * t337 - 0.2e1 * t103 * t345 * t340 - 0.2e1 * params.c1 * t340 * t204 - t338 * t105
  t353 = t207 ** 2
  t356 = f.my_piecewise3(t109, 0, t336)
  t358 = t209 ** 2
  t382 = -0.667e0 * t356 - 0.8891110e0 * t358 - 0.8891110e0 * t110 * t356 - 0.3978519606294e1 * t110 * t358 - 0.1989259803147e1 * t112 * t356 + 0.17415564533880e2 * t112 * t358 + 0.5805188177960e1 * t114 * t356 - 0.17759960831940e2 * t114 * t358 - 0.4439990207985e1 * t116 * t356 + 0.7035868244370e1 * t116 * t358 + 0.1407173648874e1 * t118 * t356 - 0.973805419524e0 * t118 * t358 - 0.162300903254e0 * t120 * t356
  t384 = 0.1e1 / t225 / t126
  t385 = t227 ** 2
  t390 = f.my_piecewise3(t109, t336, 0)
  t394 = params.c2 ** 2
  t395 = params.d * t394
  t396 = t225 ** 2
  t397 = 0.1e1 / t396
  t402 = f.my_piecewise5(t100, t351 * t107 + t353 * t107, t108, t382, -t224 * t226 * t390 * t129 - 0.2e1 * t224 * t384 * t385 * t129 - t395 * t397 * t385 * t129)
  t404 = t231 * t163
  t407 = t281 * t283
  t410 = t165 * t312
  t412 = t402 * t132 + t166 * t312 + 0.2e1 * t233 * t407 - t233 * t410 - 0.2e1 * t404 * t234 - 0.2e1 * t282 * t283
  t414 = t43 * t412 * t149
  t417 = t263 * t43
  t418 = t417 * t236
  t419 = t245 * t418
  t422 = t417 * t134
  t423 = t245 * t422
  t424 = t46 * t73
  t430 = 0.1e1 / t144 / t424 / t89 * t46 * t73 / 0.6e1
  t432 = t430 * t316 * t148
  t439 = t252 * t139 / t57 / t179 * t148
  t442 = t3 ** 2
  t444 = t2 * t442 * jnp.pi
  t445 = t444 * t422
  t446 = 0.1e1 / t139
  t449 = t424 * t148
  t450 = t446 / t75 * t449
  t453 = -0.3e1 / 0.8e1 * t42 * t150 - t156 * t160 / 0.4e1 - 0.3e1 / 0.4e1 * t156 * t238 - 0.49479000000000000000000000000000000000000000000000e1 * t248 * t257 + t264 * t268 / 0.12e2 - t264 * t272 / 0.4e1 - 0.16493000000000000000000000000000000000000000000000e1 * t277 * t257 - 0.3e1 / 0.8e1 * t264 * t414 - 0.49479000000000000000000000000000000000000000000000e1 * t419 * t257 - 0.29687400000000000000000000000000000000000000000000e2 * t423 * t432 + 0.57725500000000000000000000000000000000000000000000e1 * t423 * t439 + 0.81605714700000000000000000000000000000000000000000e1 * t445 * t450
  t454 = f.my_piecewise3(t1, 0, t453)
  t456 = r1 <= f.p.dens_threshold
  t457 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t458 = 0.1e1 + t457
  t459 = t458 <= f.p.zeta_threshold
  t460 = t458 ** (0.1e1 / 0.3e1)
  t461 = t460 ** 2
  t462 = 0.1e1 / t461
  t464 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t465 = t464 ** 2
  t469 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t473 = f.my_piecewise3(t459, 0, 0.4e1 / 0.9e1 * t462 * t465 + 0.4e1 / 0.3e1 * t460 * t469)
  t474 = t5 * t473
  t475 = s2 ** 2
  t476 = r1 ** 2
  t477 = t476 ** 2
  t479 = r1 ** (0.1e1 / 0.3e1)
  t486 = jnp.exp(-t52 * t475 / t479 / t477 / r1 * t63 / 0.576e3)
  t492 = t479 ** 2
  t494 = 0.1e1 / t492 / t476
  t502 = params.k1 * (0.1e1 - params.k1 / (params.k1 + (-0.162742215233874e0 * t45 * t486 + 0.10e2 / 0.81e2) * t46 * t73 * s2 * t494 / 0.24e2))
  t514 = (tau1 / t492 / r1 - s2 * t494 / 0.8e1) / (t93 + params.eta * s2 * t494 / 0.8e1)
  t517 = f.my_piecewise3(0.0e0 < t514, 0, t514)
  t522 = jnp.exp(-params.c1 * t517 / (0.1e1 - t517))
  t524 = 0.25e1 < t514
  t525 = f.my_piecewise3(t524, 0.25e1, t514)
  t527 = t525 ** 2
  t529 = t527 * t525
  t531 = t527 ** 2
  t540 = f.my_piecewise3(t524, t514, 0.25e1)
  t544 = jnp.exp(params.c2 / (0.1e1 - t540))
  t546 = f.my_piecewise5(t514 <= 0.0e0, t522, t514 <= 0.25e1, 0.1e1 - 0.667e0 * t525 - 0.4445555e0 * t527 - 0.663086601049e0 * t529 + 0.1451297044490e1 * t531 - 0.887998041597e0 * t531 * t525 + 0.234528941479e0 * t531 * t527 - 0.23185843322e-1 * t531 * t529, -params.d * t544)
  t549 = 0.1e1 + t502 + t546 * (0.174e0 - t502)
  t551 = jnp.sqrt(s2)
  t556 = jnp.sqrt(t138 * t551 / t479 / r1)
  t560 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t136 / t556)
  t561 = 0.1e1 - t560
  t562 = t43 * t549 * t561
  t567 = f.my_piecewise3(t459, 0, 0.4e1 / 0.3e1 * t460 * t464)
  t568 = t5 * t567
  t570 = t158 * t549 * t561
  t574 = f.my_piecewise3(t459, t261, t460 * t458)
  t575 = t5 * t574
  t577 = t266 * t549 * t561
  t581 = f.my_piecewise3(t456, 0, -0.3e1 / 0.8e1 * t474 * t562 - t568 * t570 / 0.4e1 + t575 * t577 / 0.12e2)
  t583 = t164 ** 2
  t584 = 0.1e1 / t583
  t586 = t283 * t185
  t593 = 0.1e1 / t172 / t179
  t598 = t172 ** 2
  t621 = 0.1e1 / t75 / t56
  t625 = -0.47633909705799540123456790123456790123456790123456e-1 * t171 * t593 * t63 * t67 + 0.94179522704788194444444444444444444444444444444444e-4 * t169 * t293 / t57 / t598 * t304 - 0.19378502614153949474165523548239597622313671696388e-6 * t169 * t292 * t170 / t75 / t598 / t56 / t300 / t62 * t46 / t72 / t167 * t67 - 0.154e3 / 0.81e2 * t71 * t74 * t621
  t629 = s0 * t621
  t640 = t193 ** 2
  t656 = (-0.440e3 / 0.27e2 * tau0 * t308 + 0.154e3 / 0.27e2 * t629) * t98 + t318 * t194 * t196 + 0.2e1 / 0.3e1 * t191 * t324 * t330 - 0.11e2 / 0.3e1 * t320 * t333 + 0.2e1 / 0.9e1 * t91 / t640 * t326 * params.eta * t170 * t593 - 0.22e2 / 0.9e1 * t325 * t327 / t57 / t172 + 0.154e3 / 0.27e2 * t195 * t94 * t621
  t657 = f.my_piecewise3(t101, 0, t656)
  t662 = t340 * t200
  t666 = t203 ** 2
  t685 = f.my_piecewise3(t109, 0, t656)
  t691 = t358 * t209
  t721 = -0.667e0 * t685 - 0.26673330e1 * t209 * t356 - 0.8891110e0 * t110 * t685 - 0.3978519606294e1 * t691 - 0.11935558818882e2 * t211 * t356 - 0.1989259803147e1 * t112 * t685 + 0.34831129067760e2 * t110 * t691 + 0.52246693601640e2 * t213 * t356 + 0.5805188177960e1 * t114 * t685 - 0.53279882495820e2 * t112 * t691 - 0.53279882495820e2 * t215 * t356 - 0.4439990207985e1 * t116 * t685 + 0.28143472977480e2 * t114 * t691 + 0.21107604733110e2 * t217 * t356 + 0.1407173648874e1 * t118 * t685 - 0.4869027097620e1 * t116 * t691 - 0.2921416258572e1 * t219 * t356 - 0.162300903254e0 * t120 * t685
  t722 = t385 * t227
  t729 = t227 * t129 * t390
  t738 = f.my_piecewise3(t109, t656, 0)
  t753 = f.my_piecewise5(t100, (-params.c1 * t657 * t105 - 0.6e1 * t338 * t205 - 0.6e1 * params.c1 * t662 * t345 - 0.6e1 * t103 / t666 * t662 - 0.6e1 * t103 * t345 * t200 * t337 - t103 * t204 * t657) * t107 + 0.3e1 * t351 * t207 * t107 + t353 * t207 * t107, t108, t721, -0.6e1 * t224 * t397 * t722 * t129 - 0.6e1 * t224 * t384 * t729 - 0.6e1 * t395 / t396 / t126 * t722 * t129 - t224 * t226 * t738 * t129 - 0.3e1 * t395 * t397 * t729 - params.d * t394 * params.c2 / t396 / t225 * t722 * t129)
  t783 = 0.1e1 / t157 / t24
  t798 = t24 ** 2
  t802 = 0.6e1 * t33 - 0.6e1 * t16 / t798
  t803 = f.my_piecewise5(t10, 0, t14, 0, t802)
  t807 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t803)
  t835 = 0.1e1 / t3 / t48
  t839 = t446 * t87
  t847 = -0.3e1 / 0.8e1 * t264 * t43 * (0.6e1 * t233 * t281 * t185 * t312 - 0.3e1 * t402 * t163 * t234 + 0.6e1 * t163 * t584 * t586 - t233 * t165 * t625 - 0.6e1 * t282 * t185 * t312 - 0.6e1 * t233 * t584 * t586 + t753 * t132 + t166 * t625 + 0.6e1 * t404 * t407 - 0.3e1 * t404 * t410) * t149 + t264 * t266 * t236 * t149 / 0.4e1 - 0.9e1 / 0.8e1 * t156 * t414 - 0.5e1 / 0.36e2 * t264 * t783 * t134 * t149 + t156 * t268 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t807 * t150 - 0.9e1 / 0.8e1 * t42 * t238 - 0.3e1 / 0.4e1 * t156 * t272 - 0.3e1 / 0.8e1 * t264 * t158 * t412 * t149 - 0.3e1 / 0.8e1 * t42 * t160 - 0.32302153261130400000000000000000000000000000000000e3 * t245 * t417 * t134 / t179 * t250 * t148 + 0.81605714700000000000000000000000000000000000000000e1 * t444 * t276 * t450 + 0.24481714410000000000000000000000000000000000000000e2 * t444 * t418 * t450 + 0.16321142940000000000000000000000000000000000000000e2 * t2 * t835 * t422 * t46 * t50 * t839 * t148 - 0.24481714410000000000000000000000000000000000000000e2 * t445 * t839 * t449
  t904 = t139 * s0
  t918 = 0.24481714410000000000000000000000000000000000000000e2 * t444 * t247 * t450 + 0.57725500000000000000000000000000000000000000000000e1 * t277 * t439 + 0.17317650000000000000000000000000000000000000000000e2 * t248 * t439 - 0.74218500000000000000000000000000000000000000000000e1 * t245 * t417 * t412 * t257 - 0.89062200000000000000000000000000000000000000000000e2 * t419 * t432 - 0.74218500000000000000000000000000000000000000000000e1 * t245 * t41 * t43 * t134 * t257 - 0.49479000000000000000000000000000000000000000000000e1 * t245 * t155 * t158 * t134 * t257 - 0.14843700000000000000000000000000000000000000000000e2 * t245 * t246 * t236 * t257 - 0.89062200000000000000000000000000000000000000000000e2 * t248 * t432 + 0.16493000000000000000000000000000000000000000000000e1 * t245 * t263 * t266 * t134 * t257 - 0.49479000000000000000000000000000000000000000000000e1 * t245 * t275 * t236 * t257 - 0.29687400000000000000000000000000000000000000000000e2 * t277 * t432 + 0.20781180000000000000000000000000000000000000000000e3 * t423 * t430 * t629 * t148 - 0.19241833333333333333333333333333333333333333333333e2 * t423 * t252 * t139 / t57 / t55 * t148 + 0.17317650000000000000000000000000000000000000000000e2 * t419 * t439 - 0.16493000000000000000000000000000000000000000000000e2 * t244 * t835 * t417 * t134 / t144 * t48 * t55 / t294 * t148
  t920 = f.my_piecewise3(t1, 0, t847 + t918)
  t930 = f.my_piecewise5(t14, 0, t10, 0, -t802)
  t934 = f.my_piecewise3(t459, 0, -0.8e1 / 0.27e2 / t461 / t458 * t465 * t464 + 0.4e1 / 0.3e1 * t462 * t464 * t469 + 0.4e1 / 0.3e1 * t460 * t930)
  t947 = f.my_piecewise3(t456, 0, -0.3e1 / 0.8e1 * t5 * t934 * t562 - 0.3e1 / 0.8e1 * t474 * t570 + t568 * t577 / 0.4e1 - 0.5e1 / 0.36e2 * t575 * t783 * t549 * t561)
  d111 = 0.3e1 * t454 + 0.3e1 * t581 + t6 * (t920 + t947)

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
  t4 = 0.1e1 / t3
  t5 = t2 * t4
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
  t32 = params.k1 ** 2
  t34 = 0.20e2 / 0.27e2 + 0.5e1 / 0.3e1 * params.eta
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 * t37
  t40 = 0.1e1 / t39
  t41 = t36 * t40
  t42 = s0 ** 2
  t43 = r0 ** 2
  t44 = t43 ** 2
  t45 = t44 * r0
  t46 = r0 ** (0.1e1 / 0.3e1)
  t48 = 0.1e1 / t46 / t45
  t49 = t42 * t48
  t50 = params.dp2 ** 2
  t51 = t50 ** 2
  t52 = 0.1e1 / t51
  t56 = jnp.exp(-t41 * t49 * t52 / 0.576e3)
  t60 = (-0.162742215233874e0 * t34 * t56 + 0.10e2 / 0.81e2) * t35
  t61 = t38 ** 2
  t62 = 0.1e1 / t61
  t63 = t62 * s0
  t64 = t46 ** 2
  t66 = 0.1e1 / t64 / t43
  t70 = params.k1 + t60 * t63 * t66 / 0.24e2
  t71 = t70 ** 2
  t73 = 0.1e1 / t71 / t70
  t74 = t32 * t73
  t75 = t37 ** 2
  t77 = t34 / t75
  t78 = t42 * s0
  t79 = t77 * t78
  t80 = t44 ** 2
  t81 = t80 * r0
  t87 = t43 * r0
  t89 = 0.1e1 / t64 / t87
  t93 = -0.37671809081915277777777777777777777777777777777778e-3 * t79 / t81 * t52 * t56 - t60 * t63 * t89 / 0.9e1
  t94 = t93 ** 2
  t97 = 0.1e1 / t71
  t98 = t32 * t97
  t105 = t42 ** 2
  t106 = t105 * s0
  t107 = t44 * t87
  t113 = t51 ** 2
  t117 = 0.1e1 / t113 * t36 * t40 * t56
  t121 = 0.1e1 / t64 / t44
  t125 = 0.43950443928901157407407407407407407407407407407407e-2 * t79 / t80 / t43 * t52 * t56 - 0.34881304705477109053497942386831275720164609053498e-5 * t77 * t106 / t46 / t80 / t107 * t117 + 0.11e2 / 0.27e2 * t60 * t63 * t121
  t128 = 0.1e1 / t64 / r0
  t130 = s0 * t66
  t132 = tau0 * t128 - t130 / 0.8e1
  t134 = 0.3e1 / 0.10e2 * t36 * t61
  t135 = params.eta * s0
  t138 = t134 + t135 * t66 / 0.8e1
  t139 = 0.1e1 / t138
  t140 = t132 * t139
  t141 = t140 <= 0.0e0
  t142 = 0.0e0 < t140
  t145 = s0 * t121
  t147 = 0.40e2 / 0.9e1 * tau0 * t89 - 0.11e2 / 0.9e1 * t145
  t153 = -0.5e1 / 0.3e1 * tau0 * t66 + s0 * t89 / 0.3e1
  t154 = t138 ** 2
  t155 = 0.1e1 / t154
  t156 = t153 * t155
  t157 = t135 * t89
  t161 = 0.1e1 / t154 / t138
  t162 = t132 * t161
  t163 = params.eta ** 2
  t164 = t163 * t42
  t167 = t164 / t46 / t107
  t170 = t132 * t155
  t171 = t135 * t121
  t174 = t147 * t139 + 0.2e1 / 0.3e1 * t156 * t157 + 0.2e1 / 0.9e1 * t162 * t167 - 0.11e2 / 0.9e1 * t170 * t171
  t175 = f.my_piecewise3(t142, 0, t174)
  t176 = params.c1 * t175
  t177 = f.my_piecewise3(t142, 0, t140)
  t178 = 0.1e1 - t177
  t179 = 0.1e1 / t178
  t184 = t153 * t139 + t170 * t157 / 0.3e1
  t185 = f.my_piecewise3(t142, 0, t184)
  t186 = t185 ** 2
  t188 = t178 ** 2
  t189 = 0.1e1 / t188
  t192 = params.c1 * t177
  t194 = 0.1e1 / t188 / t178
  t195 = t194 * t186
  t200 = -t175 * t189 * t192 - 0.2e1 * t186 * t189 * params.c1 - t176 * t179 - 0.2e1 * t192 * t195
  t202 = jnp.exp(-t192 * t179)
  t206 = t189 * t185
  t208 = -t179 * t185 * params.c1 - t192 * t206
  t209 = t208 ** 2
  t212 = t140 <= 0.25e1
  t213 = 0.25e1 < t140
  t214 = f.my_piecewise3(t213, 0, t174)
  t216 = f.my_piecewise3(t213, 0, t184)
  t217 = t216 ** 2
  t219 = f.my_piecewise3(t213, 0.25e1, t140)
  t222 = t219 * t217
  t224 = t219 ** 2
  t227 = t224 * t217
  t229 = t224 * t219
  t232 = t229 * t217
  t234 = t224 ** 2
  t237 = t234 * t217
  t239 = t234 * t219
  t244 = t234 * t224
  t247 = -0.667e0 * t214 - 0.8891110e0 * t217 - 0.8891110e0 * t219 * t214 - 0.3978519606294e1 * t222 - 0.1989259803147e1 * t224 * t214 + 0.17415564533880e2 * t227 + 0.5805188177960e1 * t229 * t214 - 0.17759960831940e2 * t232 - 0.4439990207985e1 * t234 * t214 + 0.7035868244370e1 * t237 + 0.1407173648874e1 * t239 * t214 - 0.973805419524e0 * t239 * t217 - 0.162300903254e0 * t244 * t214
  t248 = params.d * params.c2
  t249 = f.my_piecewise3(t213, t140, 0.25e1)
  t250 = 0.1e1 - t249
  t251 = t250 ** 2
  t252 = t251 * t250
  t253 = 0.1e1 / t252
  t254 = f.my_piecewise3(t213, t184, 0)
  t255 = t254 ** 2
  t259 = jnp.exp(params.c2 / t250)
  t263 = 0.1e1 / t251
  t264 = f.my_piecewise3(t213, t174, 0)
  t268 = params.c2 ** 2
  t269 = params.d * t268
  t270 = t251 ** 2
  t271 = 0.1e1 / t270
  t276 = f.my_piecewise5(t141, t200 * t202 + t202 * t209, t212, t247, -0.2e1 * t248 * t253 * t255 * t259 - t248 * t259 * t263 * t264 - t255 * t259 * t269 * t271)
  t280 = params.k1 * (0.1e1 - params.k1 / t70)
  t281 = 0.174e0 - t280
  t285 = t219 * t216
  t287 = t224 * t216
  t289 = t229 * t216
  t291 = t234 * t216
  t293 = t239 * t216
  t301 = f.my_piecewise5(t141, t208 * t202, t212, -0.667e0 * t216 - 0.8891110e0 * t285 - 0.1989259803147e1 * t287 + 0.5805188177960e1 * t289 - 0.4439990207985e1 * t291 + 0.1407173648874e1 * t293 - 0.162300903254e0 * t244 * t216, -t248 * t263 * t254 * t259)
  t302 = t301 * t32
  t303 = t97 * t93
  t316 = f.my_piecewise5(t141, t202, t212, 0.1e1 - 0.667e0 * t219 - 0.4445555e0 * t224 - 0.663086601049e0 * t229 + 0.1451297044490e1 * t234 - 0.887998041597e0 * t239 + 0.234528941479e0 * t244 - 0.23185843322e-1 * t234 * t229, -params.d * t259)
  t317 = t316 * t32
  t318 = t73 * t94
  t321 = t97 * t125
  t323 = t125 * t98 + t276 * t281 - 0.2e1 * t302 * t303 + 0.2e1 * t317 * t318 - t317 * t321 - 0.2e1 * t74 * t94
  t325 = jnp.sqrt(0.3e1)
  t326 = 0.1e1 / t38
  t327 = t36 * t326
  t328 = jnp.sqrt(s0)
  t330 = 0.1e1 / t46 / r0
  t332 = t327 * t328 * t330
  t333 = jnp.sqrt(t332)
  t337 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t325 / t333)
  t338 = 0.1e1 - t337
  t339 = t31 * t323 * t338
  t342 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t343 = t342 * f.p.zeta_threshold
  t345 = f.my_piecewise3(t20, t343, t21 * t19)
  t346 = t5 * t345
  t347 = t31 ** 2
  t349 = 0.1e1 / t347 / t6
  t353 = t281 * t301 - t303 * t317 + t93 * t98
  t355 = t349 * t353 * t338
  t358 = t71 ** 2
  t359 = 0.1e1 / t358
  t360 = t32 * t359
  t361 = t94 * t93
  t368 = 0.1e1 / t80 / t87
  t373 = t80 ** 2
  t380 = t105 * t78
  t392 = 0.1e1 / t113 / t51 * t35 / t61 / t75 * t56
  t396 = 0.1e1 / t64 / t45
  t400 = -0.47633909705799540123456790123456790123456790123456e-1 * t79 * t368 * t52 * t56 + 0.94179522704788194444444444444444444444444444444444e-4 * t77 * t106 / t46 / t373 * t117 - 0.19378502614153949474165523548239597622313671696388e-6 * t77 * t380 / t64 / t373 / t45 * t392 - 0.154e3 / 0.81e2 * t60 * t63 * t396
  t404 = s0 * t396
  t406 = -0.440e3 / 0.27e2 * tau0 * t121 + 0.154e3 / 0.27e2 * t404
  t408 = t147 * t155
  t410 = t153 * t161
  t415 = t154 ** 2
  t416 = 0.1e1 / t415
  t417 = t132 * t416
  t419 = t163 * params.eta * t78
  t420 = t419 * t368
  t425 = t164 / t46 / t80
  t428 = t135 * t396
  t431 = t406 * t139 + t408 * t157 + 0.2e1 / 0.3e1 * t410 * t167 - 0.11e2 / 0.3e1 * t156 * t171 + 0.2e1 / 0.9e1 * t417 * t420 - 0.22e2 / 0.9e1 * t162 * t425 + 0.154e3 / 0.27e2 * t170 * t428
  t432 = f.my_piecewise3(t142, 0, t431)
  t433 = params.c1 * t432
  t437 = t186 * t185
  t441 = t188 ** 2
  t442 = 0.1e1 / t441
  t446 = t194 * t185
  t452 = -0.6e1 * t175 * t192 * t446 - t189 * t192 * t432 - 0.6e1 * t192 * t437 * t442 - 0.6e1 * t194 * t437 * params.c1 - 0.6e1 * t176 * t206 - t179 * t433
  t460 = f.my_piecewise3(t213, 0, t431)
  t466 = t217 * t216
  t496 = -0.667e0 * t460 - 0.26673330e1 * t216 * t214 - 0.8891110e0 * t219 * t460 - 0.3978519606294e1 * t466 - 0.11935558818882e2 * t285 * t214 - 0.1989259803147e1 * t224 * t460 + 0.34831129067760e2 * t219 * t466 + 0.52246693601640e2 * t287 * t214 + 0.5805188177960e1 * t229 * t460 - 0.53279882495820e2 * t224 * t466 - 0.53279882495820e2 * t289 * t214 - 0.4439990207985e1 * t234 * t460 + 0.28143472977480e2 * t229 * t466 + 0.21107604733110e2 * t291 * t214 + 0.1407173648874e1 * t239 * t460 - 0.4869027097620e1 * t234 * t466 - 0.2921416258572e1 * t293 * t214 - 0.162300903254e0 * t244 * t460
  t497 = t255 * t254
  t502 = t248 * t253
  t503 = t254 * t259
  t504 = t503 * t264
  t508 = 0.1e1 / t270 / t250
  t513 = f.my_piecewise3(t213, t431, 0)
  t517 = t269 * t271
  t521 = params.d * t268 * params.c2
  t523 = 0.1e1 / t270 / t251
  t528 = f.my_piecewise5(t141, 0.3e1 * t200 * t202 * t208 + t202 * t208 * t209 + t202 * t452, t212, t496, -t248 * t259 * t263 * t513 - 0.6e1 * t248 * t259 * t271 * t497 - 0.6e1 * t259 * t269 * t497 * t508 - t259 * t497 * t521 * t523 - 0.6e1 * t502 * t504 - 0.3e1 * t504 * t517)
  t530 = t276 * t32
  t537 = t359 * t361
  t540 = t73 * t93
  t541 = t540 * t125
  t544 = t97 * t400
  t546 = -0.6e1 * t125 * t74 * t93 + t281 * t528 + 0.6e1 * t302 * t318 - 0.3e1 * t302 * t321 - 0.3e1 * t303 * t530 - 0.6e1 * t317 * t537 + 0.6e1 * t317 * t541 - t317 * t544 + 0.6e1 * t360 * t361 + t400 * t98
  t548 = t31 * t546 * t338
  t552 = t281 * t316 + t280 + 0.1e1
  t554 = t349 * t552 * t338
  t557 = t21 ** 2
  t559 = 0.1e1 / t557 / t19
  t560 = t26 ** 2
  t564 = 0.1e1 / t557
  t565 = t564 * t26
  t566 = t22 * t6
  t567 = 0.1e1 / t566
  t570 = 0.2e1 * t16 * t567 - 0.2e1 * t23
  t571 = f.my_piecewise5(t10, 0, t14, 0, t570)
  t574 = t22 ** 2
  t575 = 0.1e1 / t574
  t578 = -0.6e1 * t16 * t575 + 0.6e1 * t567
  t579 = f.my_piecewise5(t10, 0, t14, 0, t578)
  t583 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t559 * t560 * t26 + 0.4e1 / 0.3e1 * t565 * t571 + 0.4e1 / 0.3e1 * t21 * t579)
  t584 = t5 * t583
  t586 = t31 * t552 * t338
  t594 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t564 * t560 + 0.4e1 / 0.3e1 * t21 * t571)
  t595 = t5 * t594
  t597 = t31 * t353 * t338
  t600 = 0.1e1 / t347
  t602 = t600 * t323 * t338
  t606 = t600 * t552 * t338
  t610 = 0.1e1 / t347 / t22
  t612 = t610 * t552 * t338
  t616 = t600 * t353 * t338
  t619 = 3 ** (0.1e1 / 0.6e1)
  t620 = t619 ** 2
  t621 = t620 ** 2
  t622 = t621 * t619
  t623 = t622 * t4
  t624 = t345 * t31
  t625 = t623 * t624
  t626 = 0.1e1 / t87
  t629 = 0.1e1 / t333 / t332
  t630 = t629 * t337
  t631 = t552 * t626 * t630
  t634 = t3 ** 2
  t636 = t2 * t634 * jnp.pi
  t637 = t345 * t600
  t638 = t637 * t552
  t639 = t636 * t638
  t640 = 0.1e1 / t328
  t643 = t35 * t62
  t644 = t643 * t337
  t645 = t640 / t64 * t644
  t648 = t624 * t353
  t649 = t636 * t648
  t653 = 0.1e1 / t3 / t37
  t654 = t2 * t653
  t655 = t624 * t552
  t656 = t654 * t655
  t657 = t35 * t39
  t658 = t640 * t128
  t660 = t657 * t658 * t337
  t663 = t636 * t655
  t664 = t658 * t644
  t667 = -0.9e1 / 0.8e1 * t30 * t339 + t346 * t355 / 0.4e1 - 0.3e1 / 0.8e1 * t346 * t548 + t30 * t554 / 0.4e1 - 0.3e1 / 0.8e1 * t584 * t586 - 0.9e1 / 0.8e1 * t595 * t597 - 0.3e1 / 0.8e1 * t346 * t602 - 0.3e1 / 0.8e1 * t595 * t606 - 0.5e1 / 0.36e2 * t346 * t612 - 0.3e1 / 0.4e1 * t30 * t616 - 0.32302153261130400000000000000000000000000000000000e3 * t625 * t631 + 0.81605714700000000000000000000000000000000000000000e1 * t639 * t645 + 0.24481714410000000000000000000000000000000000000000e2 * t649 * t645 + 0.16321142940000000000000000000000000000000000000000e2 * t656 * t660 - 0.24481714410000000000000000000000000000000000000000e2 * t663 * t664
  t668 = t29 * t31
  t669 = t668 * t552
  t670 = t636 * t669
  t673 = t623 * t669
  t677 = 0.1e1 / t333 / t643 / t130 / 0.6e1
  t679 = t677 * t35 * t62
  t681 = t679 * t145 * t337
  t684 = t345 * t349
  t685 = t684 * t552
  t686 = t623 * t685
  t688 = t629 * t36 * t326
  t693 = t688 * t328 / t46 / t43 * t337
  t696 = t637 * t353
  t697 = t623 * t696
  t700 = t623 * t638
  t703 = t623 * t655
  t705 = t679 * t404 * t337
  t712 = t688 * t328 / t46 / t44 * t337
  t715 = t623 * t648
  t720 = t688 * t328 / t46 / t87 * t337
  t727 = t624 * t323
  t728 = t623 * t727
  t733 = t594 * t31
  t734 = t733 * t552
  t735 = t623 * t734
  t738 = t29 * t600
  t739 = t738 * t552
  t740 = t623 * t739
  t743 = t668 * t353
  t744 = t623 * t743
  t747 = t622 * t653
  t748 = t747 * t624
  t750 = t328 * s0
  t752 = 0.1e1 / t44
  t756 = 0.1e1 / t333 * t37 / t750 / t752 / 0.36e2
  t757 = t552 * t756
  t760 = t750 / t107 * t337
  t761 = t757 * t760
  t764 = 0.24481714410000000000000000000000000000000000000000e2 * t670 * t645 - 0.89062200000000000000000000000000000000000000000000e2 * t673 * t681 + 0.16493000000000000000000000000000000000000000000000e1 * t686 * t693 - 0.49479000000000000000000000000000000000000000000000e1 * t697 * t693 - 0.29687400000000000000000000000000000000000000000000e2 * t700 * t681 + 0.20781180000000000000000000000000000000000000000000e3 * t703 * t705 - 0.19241833333333333333333333333333333333333333333333e2 * t703 * t712 + 0.17317650000000000000000000000000000000000000000000e2 * t715 * t720 + 0.57725500000000000000000000000000000000000000000000e1 * t700 * t720 + 0.17317650000000000000000000000000000000000000000000e2 * t673 * t720 - 0.74218500000000000000000000000000000000000000000000e1 * t728 * t693 - 0.89062200000000000000000000000000000000000000000000e2 * t715 * t681 - 0.74218500000000000000000000000000000000000000000000e1 * t735 * t693 - 0.49479000000000000000000000000000000000000000000000e1 * t740 * t693 - 0.14843700000000000000000000000000000000000000000000e2 * t744 * t693 - 0.59374800000000000000000000000000000000000000000000e3 * t748 * t761
  t766 = f.my_piecewise3(t1, 0, t667 + t764)
  t768 = r1 <= f.p.dens_threshold
  t769 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t770 = 0.1e1 + t769
  t771 = t770 <= f.p.zeta_threshold
  t772 = t770 ** (0.1e1 / 0.3e1)
  t773 = t772 ** 2
  t775 = 0.1e1 / t773 / t770
  t777 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t778 = t777 ** 2
  t782 = 0.1e1 / t773
  t783 = t782 * t777
  t785 = f.my_piecewise5(t14, 0, t10, 0, -t570)
  t789 = f.my_piecewise5(t14, 0, t10, 0, -t578)
  t793 = f.my_piecewise3(t771, 0, -0.8e1 / 0.27e2 * t775 * t778 * t777 + 0.4e1 / 0.3e1 * t783 * t785 + 0.4e1 / 0.3e1 * t772 * t789)
  t794 = t5 * t793
  t795 = s2 ** 2
  t796 = r1 ** 2
  t797 = t796 ** 2
  t799 = r1 ** (0.1e1 / 0.3e1)
  t806 = jnp.exp(-t41 * t795 / t799 / t797 / r1 * t52 / 0.576e3)
  t812 = t799 ** 2
  t814 = 0.1e1 / t812 / t796
  t822 = params.k1 * (0.1e1 - params.k1 / (params.k1 + (-0.162742215233874e0 * t34 * t806 + 0.10e2 / 0.81e2) * t35 * t62 * s2 * t814 / 0.24e2))
  t834 = (tau1 / t812 / r1 - s2 * t814 / 0.8e1) / (t134 + params.eta * s2 * t814 / 0.8e1)
  t837 = f.my_piecewise3(0.0e0 < t834, 0, t834)
  t842 = jnp.exp(-params.c1 * t837 / (0.1e1 - t837))
  t844 = 0.25e1 < t834
  t845 = f.my_piecewise3(t844, 0.25e1, t834)
  t847 = t845 ** 2
  t849 = t847 * t845
  t851 = t847 ** 2
  t860 = f.my_piecewise3(t844, t834, 0.25e1)
  t864 = jnp.exp(params.c2 / (0.1e1 - t860))
  t866 = f.my_piecewise5(t834 <= 0.0e0, t842, t834 <= 0.25e1, 0.1e1 - 0.667e0 * t845 - 0.4445555e0 * t847 - 0.663086601049e0 * t849 + 0.1451297044490e1 * t851 - 0.887998041597e0 * t851 * t845 + 0.234528941479e0 * t851 * t847 - 0.23185843322e-1 * t851 * t849, -params.d * t864)
  t869 = 0.1e1 + t822 + t866 * (0.174e0 - t822)
  t871 = jnp.sqrt(s2)
  t876 = jnp.sqrt(t327 * t871 / t799 / r1)
  t880 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t325 / t876)
  t881 = 0.1e1 - t880
  t882 = t31 * t869 * t881
  t890 = f.my_piecewise3(t771, 0, 0.4e1 / 0.9e1 * t782 * t778 + 0.4e1 / 0.3e1 * t772 * t785)
  t891 = t5 * t890
  t893 = t600 * t869 * t881
  t898 = f.my_piecewise3(t771, 0, 0.4e1 / 0.3e1 * t772 * t777)
  t899 = t5 * t898
  t901 = t349 * t869 * t881
  t905 = f.my_piecewise3(t771, t343, t772 * t770)
  t906 = t5 * t905
  t908 = t610 * t869 * t881
  t912 = f.my_piecewise3(t768, 0, -0.3e1 / 0.8e1 * t794 * t882 - 0.3e1 / 0.8e1 * t891 * t893 + t899 * t901 / 0.4e1 - 0.5e1 / 0.36e2 * t906 * t908)
  t930 = t19 ** 2
  t933 = t560 ** 2
  t939 = t571 ** 2
  t948 = -0.24e2 * t575 + 0.24e2 * t16 / t574 / t6
  t949 = f.my_piecewise5(t10, 0, t14, 0, t948)
  t953 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t557 / t930 * t933 - 0.16e2 / 0.9e1 * t559 * t560 * t571 + 0.4e1 / 0.3e1 * t564 * t939 + 0.16e2 / 0.9e1 * t565 * t579 + 0.4e1 / 0.3e1 * t21 * t949)
  t986 = -0.3e1 / 0.2e1 * t30 * t602 - 0.3e1 / 0.2e1 * t595 * t616 - 0.5e1 / 0.9e1 * t30 * t612 - 0.5e1 / 0.9e1 * t346 * t610 * t353 * t338 - 0.3e1 / 0.2e1 * t30 * t548 - t584 * t606 / 0.2e1 + t595 * t554 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t953 * t586 - 0.3e1 / 0.2e1 * t584 * t597 - t346 * t600 * t546 * t338 / 0.2e1 + t346 * t349 * t323 * t338 / 0.2e1 - 0.9e1 / 0.4e1 * t595 * t339 - 0.43069537681507200000000000000000000000000000000000e3 * t623 * t637 * t631 + 0.12920861304452160000000000000000000000000000000000e4 * t625 * t552 * t752 * t630 - 0.12920861304452160000000000000000000000000000000000e4 * t623 * t668 * t631 - 0.12920861304452160000000000000000000000000000000000e4 * t625 * t353 * t626 * t630 + 0.65284571760000000000000000000000000000000000000000e2 * t654 * t648 * t660
  t994 = t327 * t337
  t1001 = t640 * t66
  t1047 = -0.97926857640000000000000000000000000000000000000000e2 * t670 * t664 + 0.48963428820000000000000000000000000000000000000000e2 * t636 * t734 * t645 + 0.17758647124527456240000000000000000000000000000000e3 * t663 * t330 / s0 * t994 + 0.21761523920000000000000000000000000000000000000000e2 * t654 * t638 * t660 - 0.87046095680000000000000000000000000000000000000001e2 * t656 * t657 * t1001 * t337 + 0.10427396878333333333333333333333333333333333333333e3 * t663 * t1001 * t644 - 0.10880761960000000000000000000000000000000000000000e2 * t636 * t685 * t645 - 0.32642285880000000000000000000000000000000000000000e2 * t639 * t664 - 0.97926857640000000000000000000000000000000000000000e2 * t649 * t664 + 0.32642285880000000000000000000000000000000000000000e2 * t636 * t739 * t645 + 0.32642285880000000000000000000000000000000000000000e2 * t636 * t696 * t645 + 0.97926857640000000000000000000000000000000000000000e2 * t636 * t743 * t645 + 0.48963428820000000000000000000000000000000000000000e2 * t636 * t727 * t645 + 0.65284571760000000000000000000000000000000000000000e2 * t654 * t669 * t660 - 0.98958000000000000000000000000000000000000000000000e1 * t623 * t594 * t600 * t552 * t693 - 0.36651111111111111111111111111111111111111111111111e1 * t623 * t345 * t610 * t552 * t693 - 0.19791600000000000000000000000000000000000000000000e2 * t623 * t738 * t353 * t693 + 0.23090200000000000000000000000000000000000000000000e2 * t697 * t720
  t1074 = 0.1e1 / t46 / t81
  t1103 = 0.27708240000000000000000000000000000000000000000000e3 * t700 * t705 - 0.76967333333333333333333333333333333333333333333334e1 * t686 * t720 + 0.69270600000000000000000000000000000000000000000000e2 * t744 * t720 + 0.83124720000000000000000000000000000000000000000000e3 * t673 * t705 + 0.65972000000000000000000000000000000000000000000000e1 * t623 * t29 * t349 * t552 * t693 - 0.98958000000000000000000000000000000000000000000000e1 * t623 * t583 * t31 * t552 * t693 - 0.76967333333333333333333333333333333333333333333333e2 * t747 * t655 / t333 / t41 / t49 * t42 * t1074 * t994 + 0.34635300000000000000000000000000000000000000000000e2 * t728 * t720 + 0.34635300000000000000000000000000000000000000000000e2 * t735 * t720 - 0.98958000000000000000000000000000000000000000000000e1 * t623 * t624 * t546 * t693 - 0.17812440000000000000000000000000000000000000000000e3 * t728 * t681 + 0.65972000000000000000000000000000000000000000000000e1 * t623 * t684 * t353 * t693 + 0.39583200000000000000000000000000000000000000000000e2 * t686 * t681 - 0.11874960000000000000000000000000000000000000000000e3 * t697 * t681 + 0.83124720000000000000000000000000000000000000000000e3 * t715 * t705 - 0.76967333333333333333333333333333333333333333333333e2 * t673 * t712 - 0.76967333333333333333333333333333333333333333333333e2 * t715 * t712
  t1112 = t44 * t43
  t1114 = 0.1e1 / t64 / t1112
  t1115 = s0 * t1114
  t1184 = t163 ** 2
  t1192 = t80 * t44
  t1193 = 0.1e1 / t1192
  t1203 = (0.6160e4 / 0.81e2 * tau0 * t396 - 0.2618e4 / 0.81e2 * t1115) * t139 + 0.4e1 / 0.3e1 * t406 * t155 * t157 + 0.4e1 / 0.3e1 * t147 * t161 * t167 - 0.22e2 / 0.3e1 * t408 * t171 + 0.8e1 / 0.9e1 * t153 * t416 * t420 - 0.88e2 / 0.9e1 * t410 * t425 + 0.616e3 / 0.27e2 * t156 * t428 + 0.8e1 / 0.27e2 * t132 / t415 / t138 * t1184 * t105 / t64 / t80 / t1112 - 0.44e2 / 0.9e1 * t417 * t419 * t1193 + 0.1958e4 / 0.81e2 * t162 * t164 * t1074 - 0.2618e4 / 0.81e2 * t170 * t135 * t1114
  t1204 = f.my_piecewise3(t142, 0, t1203)
  t1211 = t175 ** 2
  t1215 = t186 ** 2
  t1241 = t200 ** 2
  t1247 = t209 ** 2
  t1250 = t214 ** 2
  t1252 = t217 ** 2
  t1254 = f.my_piecewise3(t213, 0, t1203)
  t1279 = -0.26673330e1 * t1250 + 0.34831129067760e2 * t1252 + 0.1407173648874e1 * t239 * t1254 - 0.162300903254e0 * t244 * t1254 - 0.23871117637764e2 * t217 * t214 - 0.35564440e1 * t216 * t460 - 0.11935558818882e2 * t219 * t1250 + 0.52246693601640e2 * t224 * t1250 - 0.106559764991640e3 * t219 * t1252 - 0.53279882495820e2 * t229 * t1250 - 0.1989259803147e1 * t224 * t1254 - 0.2921416258572e1 * t239 * t1250 - 0.19476108390480e2 * t229 * t1252 + 0.21107604733110e2 * t234 * t1250
  t1307 = 0.84430418932440e2 * t224 * t1252 + 0.5805188177960e1 * t229 * t1254 - 0.4439990207985e1 * t234 * t1254 - 0.8891110e0 * t219 * t1254 - 0.71039843327760e2 * t289 * t460 - 0.15914078425176e2 * t285 * t460 - 0.29214162585720e2 * t237 * t214 - 0.3895221678096e1 * t293 * t460 + 0.208986774406560e3 * t222 * t214 + 0.69662258135520e2 * t287 * t460 - 0.319679294974920e3 * t227 * t214 + 0.168860837864880e3 * t232 * t214 + 0.28143472977480e2 * t291 * t460 - 0.667e0 * t1254
  t1309 = t255 ** 2
  t1316 = t255 * t259 * t264
  t1323 = t264 ** 2
  t1331 = t503 * t513
  t1340 = f.my_piecewise3(t213, t1203, 0)
  t1353 = t268 ** 2
  t1355 = t270 ** 2
  t1360 = -0.24e2 * t248 * t508 * t1309 * t259 - 0.36e2 * t248 * t271 * t1316 - 0.36e2 * t269 * t523 * t1309 * t259 - 0.6e1 * t248 * t253 * t1323 * t259 - 0.36e2 * t269 * t508 * t1316 - 0.8e1 * t502 * t1331 - 0.12e2 * t521 / t270 / t252 * t1309 * t259 - t248 * t263 * t1340 * t259 - 0.4e1 * t517 * t1331 - 0.3e1 * t269 * t271 * t1323 * t259 - 0.6e1 * t521 * t523 * t1316 - params.d * t1353 / t1355 * t1309 * t259
  t1361 = f.my_piecewise5(t141, (-params.c1 * t1204 * t179 - 0.8e1 * t433 * t206 - 0.36e2 * t176 * t195 - 0.6e1 * params.c1 * t1211 * t189 - 0.24e2 * params.c1 * t1215 * t442 - 0.24e2 * t192 / t441 / t178 * t1215 - 0.36e2 * t192 * t442 * t186 * t175 - 0.6e1 * t192 * t194 * t1211 - 0.8e1 * t192 * t446 * t432 - t192 * t189 * t1204) * t202 + 0.4e1 * t452 * t208 * t202 + 0.3e1 * t1241 * t202 + 0.6e1 * t200 * t209 * t202 + t1247 * t202, t212, t1279 + t1307, t1360)
  t1364 = 0.1e1 / t358 / t70
  t1365 = t94 ** 2
  t1373 = t125 ** 2
  t1404 = t75 ** 2
  t1408 = t105 ** 2
  t1413 = t113 ** 2
  t1422 = 0.54116251372265406069958847736625514403292181069958e0 * t79 * t1193 * t52 * t56 - 0.19793202570096843992912665752171925011431184270690e-2 * t77 * t106 / t46 / t373 / r0 * t117 + 0.94308712722215887440938881268099375095259868922421e-5 * t77 * t380 / t64 / t373 / t1112 * t392 - 0.10765834785641083041203068637910887567952039831327e-7 * t34 / t1404 / t75 * t1408 * s0 / t373 / t1192 / t1413 * t56 + 0.2618e4 / 0.243e3 * t60 * t63 * t1114
  t1444 = -0.36e2 * t125 * t317 * t359 * t94 + 0.36e2 * t125 * t360 * t94 + 0.24e2 * t1364 * t1365 * t317 - 0.24e2 * t1364 * t1365 * t32 + 0.6e1 * t1373 * t317 * t73 - t1422 * t317 * t97 - 0.4e1 * t303 * t32 * t528 + 0.8e1 * t317 * t400 * t540 - 0.8e1 * t400 * t74 * t93 + t1361 * t281 - 0.6e1 * t1373 * t74 + t1422 * t98 - 0.24e2 * t302 * t537 + 0.24e2 * t302 * t541 - 0.4e1 * t302 * t544 + 0.12e2 * t318 * t530 - 0.6e1 * t321 * t530
  t1450 = 0.1e1 / t347 / t566
  t1456 = -0.11874960000000000000000000000000000000000000000000e3 * t740 * t681 - 0.29687400000000000000000000000000000000000000000000e2 * t623 * t733 * t353 * t693 - 0.35624880000000000000000000000000000000000000000000e3 * t744 * t681 - 0.14085022000000000000000000000000000000000000000000e4 * t703 * t679 * t1115 * t337 - 0.25655777777777777777777777777777777777777777777777e2 * t700 * t712 + 0.83381277777777777777777777777777777777777777777776e2 * t703 * t688 * t328 * t48 * t337 - 0.17812440000000000000000000000000000000000000000000e3 * t735 * t681 - 0.64604306522260800000000000000000000000000000000000e3 * t703 * t48 * t677 * t337 * t327 * t328 - 0.29687400000000000000000000000000000000000000000000e2 * t623 * t668 * t323 * t693 - 0.98958000000000000000000000000000000000000000000000e1 * t623 * t637 * t323 * t693 + 0.23090200000000000000000000000000000000000000000000e2 * t740 * t720 - 0.23749920000000000000000000000000000000000000000000e4 * t747 * t668 * t761 - 0.79166400000000000000000000000000000000000000000000e3 * t747 * t637 * t761 + 0.83124720000000000000000000000000000000000000000000e4 * t748 * t757 * t750 / t80 * t337 - 0.23749920000000000000000000000000000000000000000000e4 * t748 * t353 * t756 * t760 - 0.3e1 / 0.8e1 * t346 * t31 * t1444 * t338 + 0.10e2 / 0.27e2 * t346 * t1450 * t552 * t338 + t30 * t355
  t1459 = f.my_piecewise3(t1, 0, t986 + t1047 + t1103 + t1456)
  t1460 = t770 ** 2
  t1463 = t778 ** 2
  t1469 = t785 ** 2
  t1475 = f.my_piecewise5(t14, 0, t10, 0, -t948)
  t1479 = f.my_piecewise3(t771, 0, 0.40e2 / 0.81e2 / t773 / t1460 * t1463 - 0.16e2 / 0.9e1 * t775 * t778 * t785 + 0.4e1 / 0.3e1 * t782 * t1469 + 0.16e2 / 0.9e1 * t783 * t789 + 0.4e1 / 0.3e1 * t772 * t1475)
  t1494 = f.my_piecewise3(t768, 0, -0.3e1 / 0.8e1 * t5 * t1479 * t882 - t794 * t893 / 0.2e1 + t891 * t901 / 0.2e1 - 0.5e1 / 0.9e1 * t899 * t908 + 0.10e2 / 0.27e2 * t906 * t1450 * t869 * t881)
  d1111 = 0.4e1 * t766 + 0.4e1 * t912 + t6 * (t1459 + t1494)

  res = {'v4rho4': d1111}
  return res
