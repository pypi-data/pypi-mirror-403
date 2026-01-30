"""Generated from mgga_x_rscan.mpl."""

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
  params_alphar_raw = params.alphar
  if isinstance(params_alphar_raw, (str, bytes, dict)):
    params_alphar = params_alphar_raw
  else:
    try:
      params_alphar_seq = list(params_alphar_raw)
    except TypeError:
      params_alphar = params_alphar_raw
    else:
      params_alphar_seq = np.asarray(params_alphar_seq, dtype=np.float64)
      params_alphar = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphar_seq))
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
  params_taur_raw = params.taur
  if isinstance(params_taur_raw, (str, bytes, dict)):
    params_taur = params_taur_raw
  else:
    try:
      params_taur_seq = list(params_taur_raw)
    except TypeError:
      params_taur = params_taur_raw
    else:
      params_taur_seq = np.asarray(params_taur_seq, dtype=np.float64)
      params_taur = np.concatenate((np.array([np.nan], dtype=np.float64), params_taur_seq))

  params_c1 = 0.667
  params_dp2 = 0.361
  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_b2 = jnp.sqrt(5913 / 405000)

  scan_b3 = 1 / 2

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  np53 = lambda rs, z: f.n_spin(rs, z) ** (5 / 3)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  scan_b1 = 511 / 13500 / (2 * scan_b2)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  rscan_alpha0 = lambda rs, z, x, t: np53(rs, z) * jnp.maximum(t - x ** 2 / 8, 0) / (np53(rs, z) * K_FACTOR_C + params_taur / 2)

  rscan_f_alpha = lambda a, ff: f.my_piecewise3(a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  scan_b4 = MU_GE ** 2 / params_k1 - 1606 / 18225 - scan_b1 ** 2

  rscan_alpha = lambda rs, z, x, t: rscan_alpha0(rs, z, x, t) ** 3 / (rscan_alpha0(rs, z, x, t) ** 2 + params_alphar)

  scan_y = lambda x, a: MU_GE * scan_p(x) + scan_b4 * scan_p(x) ** 2 * jnp.exp(-scan_b4 * scan_p(x) / MU_GE) + (scan_b1 * scan_p(x) + scan_b2 * (1 - a) * jnp.exp(-scan_b3 * (1 - a) ** 2)) ** 2

  rscan_f = lambda rs, z, x, u, t: (scan_h1x(scan_y(x, rscan_alpha(rs, z, x, t))) * (1 - rscan_f_alpha(rscan_alpha(rs, z, x, t), rscan_fx)) + scan_h0x * rscan_f_alpha(rscan_alpha(rs, z, x, t), rscan_fx)) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, rscan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_alphar_raw = params.alphar
  if isinstance(params_alphar_raw, (str, bytes, dict)):
    params_alphar = params_alphar_raw
  else:
    try:
      params_alphar_seq = list(params_alphar_raw)
    except TypeError:
      params_alphar = params_alphar_raw
    else:
      params_alphar_seq = np.asarray(params_alphar_seq, dtype=np.float64)
      params_alphar = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphar_seq))
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
  params_taur_raw = params.taur
  if isinstance(params_taur_raw, (str, bytes, dict)):
    params_taur = params_taur_raw
  else:
    try:
      params_taur_seq = list(params_taur_raw)
    except TypeError:
      params_taur = params_taur_raw
    else:
      params_taur_seq = np.asarray(params_taur_seq, dtype=np.float64)
      params_taur = np.concatenate((np.array([np.nan], dtype=np.float64), params_taur_seq))

  params_c1 = 0.667
  params_dp2 = 0.361
  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_b2 = jnp.sqrt(5913 / 405000)

  scan_b3 = 1 / 2

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  np53 = lambda rs, z: f.n_spin(rs, z) ** (5 / 3)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  scan_b1 = 511 / 13500 / (2 * scan_b2)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  rscan_alpha0 = lambda rs, z, x, t: np53(rs, z) * jnp.maximum(t - x ** 2 / 8, 0) / (np53(rs, z) * K_FACTOR_C + params_taur / 2)

  rscan_f_alpha = lambda a, ff: f.my_piecewise3(a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  scan_b4 = MU_GE ** 2 / params_k1 - 1606 / 18225 - scan_b1 ** 2

  rscan_alpha = lambda rs, z, x, t: rscan_alpha0(rs, z, x, t) ** 3 / (rscan_alpha0(rs, z, x, t) ** 2 + params_alphar)

  scan_y = lambda x, a: MU_GE * scan_p(x) + scan_b4 * scan_p(x) ** 2 * jnp.exp(-scan_b4 * scan_p(x) / MU_GE) + (scan_b1 * scan_p(x) + scan_b2 * (1 - a) * jnp.exp(-scan_b3 * (1 - a) ** 2)) ** 2

  rscan_f = lambda rs, z, x, u, t: (scan_h1x(scan_y(x, rscan_alpha(rs, z, x, t))) * (1 - rscan_f_alpha(rscan_alpha(rs, z, x, t), rscan_fx)) + scan_h0x * rscan_f_alpha(rscan_alpha(rs, z, x, t), rscan_fx)) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, rscan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_alphar_raw = params.alphar
  if isinstance(params_alphar_raw, (str, bytes, dict)):
    params_alphar = params_alphar_raw
  else:
    try:
      params_alphar_seq = list(params_alphar_raw)
    except TypeError:
      params_alphar = params_alphar_raw
    else:
      params_alphar_seq = np.asarray(params_alphar_seq, dtype=np.float64)
      params_alphar = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphar_seq))
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
  params_taur_raw = params.taur
  if isinstance(params_taur_raw, (str, bytes, dict)):
    params_taur = params_taur_raw
  else:
    try:
      params_taur_seq = list(params_taur_raw)
    except TypeError:
      params_taur = params_taur_raw
    else:
      params_taur_seq = np.asarray(params_taur_seq, dtype=np.float64)
      params_taur = np.concatenate((np.array([np.nan], dtype=np.float64), params_taur_seq))

  params_c1 = 0.667
  params_dp2 = 0.361
  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_b2 = jnp.sqrt(5913 / 405000)

  scan_b3 = 1 / 2

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  np53 = lambda rs, z: f.n_spin(rs, z) ** (5 / 3)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  scan_b1 = 511 / 13500 / (2 * scan_b2)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  rscan_alpha0 = lambda rs, z, x, t: np53(rs, z) * jnp.maximum(t - x ** 2 / 8, 0) / (np53(rs, z) * K_FACTOR_C + params_taur / 2)

  rscan_f_alpha = lambda a, ff: f.my_piecewise3(a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  scan_b4 = MU_GE ** 2 / params_k1 - 1606 / 18225 - scan_b1 ** 2

  rscan_alpha = lambda rs, z, x, t: rscan_alpha0(rs, z, x, t) ** 3 / (rscan_alpha0(rs, z, x, t) ** 2 + params_alphar)

  scan_y = lambda x, a: MU_GE * scan_p(x) + scan_b4 * scan_p(x) ** 2 * jnp.exp(-scan_b4 * scan_p(x) / MU_GE) + (scan_b1 * scan_p(x) + scan_b2 * (1 - a) * jnp.exp(-scan_b3 * (1 - a) ** 2)) ** 2

  rscan_f = lambda rs, z, x, u, t: (scan_h1x(scan_y(x, rscan_alpha(rs, z, x, t))) * (1 - rscan_f_alpha(rscan_alpha(rs, z, x, t), rscan_fx)) + scan_h0x * rscan_f_alpha(rscan_alpha(rs, z, x, t), rscan_fx)) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, rscan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t44 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t45 = t28 ** 2
  t49 = t44 * t45 / t30 / t29
  t50 = s0 ** 2
  t51 = t34 ** 2
  t54 = 0.1e1 / t35 / t51 / r0
  t56 = t44 * t28
  t57 = t32 * s0
  t58 = t57 * t38
  t61 = jnp.exp(-0.27e2 / 0.80e2 * t56 * t58)
  t65 = jnp.sqrt(0.146e3)
  t66 = t65 * t28
  t69 = t19 ** 2
  t70 = t69 ** 2
  t71 = t70 * t19
  t72 = t6 ** 2
  t73 = t72 ** 2
  t74 = t73 * t6
  t75 = t71 * t74
  t77 = 0.1e1 / t36 / r0
  t80 = tau0 * t77 - t39 / 0.8e1
  t81 = 0.0e0 < t80
  t82 = f.my_piecewise3(t81, t80, 0)
  t83 = t82 ** 2
  t84 = t83 * t82
  t85 = 2 ** (0.1e1 / 0.3e1)
  t86 = t19 * t6
  t87 = t86 ** (0.1e1 / 0.3e1)
  t88 = t87 ** 2
  t91 = t45 * t31
  t94 = params.taur / 0.2e1
  t95 = 0.3e1 / 0.40e2 * t85 * t88 * t86 * t91 + t94
  t96 = t95 ** 2
  t98 = 0.1e1 / t96 / t95
  t100 = t85 ** 2
  t102 = t72 * t6
  t104 = t87 * t69 * t19 * t102
  t105 = t100 * t104
  t106 = 0.1e1 / t96
  t107 = t83 * t106
  t110 = t105 * t107 / 0.16e2 + params.alphar
  t111 = 0.1e1 / t110
  t112 = t84 * t98 * t111
  t114 = t75 * t112 / 0.32e2
  t115 = 0.1e1 - t114
  t117 = t115 ** 2
  t119 = jnp.exp(-t117 / 0.2e1)
  t122 = 0.7e1 / 0.12960e5 * t66 * t58 + t65 * t115 * t119 / 0.100e3
  t123 = t122 ** 2
  t124 = params.k1 + 0.5e1 / 0.972e3 * t33 * t39 + t49 * t50 * t54 * t61 / 0.576e3 + t123
  t129 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t124)
  t130 = t114 <= 0.25e1
  t131 = 0.25e1 < t114
  t132 = f.my_piecewise3(t131, 0.25e1, t114)
  t134 = t132 ** 2
  t136 = t134 * t132
  t138 = t134 ** 2
  t140 = t138 * t132
  t142 = t138 * t134
  t147 = f.my_piecewise3(t131, t114, 0.25e1)
  t148 = 0.1e1 - t147
  t151 = jnp.exp(params.c2 / t148)
  t153 = f.my_piecewise3(t130, 0.1e1 - 0.667e0 * t132 - 0.4445555e0 * t134 - 0.663086601049e0 * t136 + 0.1451297044490e1 * t138 - 0.887998041597e0 * t140 + 0.234528941479e0 * t142 - 0.23185843322e-1 * t138 * t136, -params.d * t151)
  t154 = 0.1e1 - t153
  t157 = t129 * t154 + 0.1174e1 * t153
  t159 = jnp.sqrt(0.3e1)
  t160 = 0.1e1 / t30
  t161 = t45 * t160
  t162 = jnp.sqrt(s0)
  t164 = 0.1e1 / t35 / r0
  t166 = t161 * t162 * t164
  t167 = jnp.sqrt(t166)
  t171 = jnp.exp(-0.98958e1 * t159 / t167)
  t172 = 0.1e1 - t171
  t173 = t27 * t157 * t172
  t176 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t173)
  t177 = r1 <= f.p.dens_threshold
  t178 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t179 = 0.1e1 + t178
  t180 = t179 <= f.p.zeta_threshold
  t181 = t179 ** (0.1e1 / 0.3e1)
  t183 = f.my_piecewise3(t180, t22, t181 * t179)
  t184 = t5 * t183
  t185 = r1 ** 2
  t186 = r1 ** (0.1e1 / 0.3e1)
  t187 = t186 ** 2
  t189 = 0.1e1 / t187 / t185
  t190 = s2 * t189
  t193 = s2 ** 2
  t194 = t185 ** 2
  t197 = 0.1e1 / t186 / t194 / r1
  t199 = t32 * s2
  t200 = t199 * t189
  t203 = jnp.exp(-0.27e2 / 0.80e2 * t56 * t200)
  t209 = t179 ** 2
  t210 = t209 ** 2
  t211 = t210 * t179
  t212 = t211 * t74
  t214 = 0.1e1 / t187 / r1
  t217 = tau1 * t214 - t190 / 0.8e1
  t218 = 0.0e0 < t217
  t219 = f.my_piecewise3(t218, t217, 0)
  t220 = t219 ** 2
  t221 = t220 * t219
  t222 = t179 * t6
  t223 = t222 ** (0.1e1 / 0.3e1)
  t224 = t223 ** 2
  t229 = 0.3e1 / 0.40e2 * t85 * t224 * t222 * t91 + t94
  t230 = t229 ** 2
  t232 = 0.1e1 / t230 / t229
  t236 = t223 * t209 * t179 * t102
  t237 = t100 * t236
  t238 = 0.1e1 / t230
  t239 = t220 * t238
  t242 = t237 * t239 / 0.16e2 + params.alphar
  t243 = 0.1e1 / t242
  t244 = t221 * t232 * t243
  t246 = t212 * t244 / 0.32e2
  t247 = 0.1e1 - t246
  t249 = t247 ** 2
  t251 = jnp.exp(-t249 / 0.2e1)
  t254 = 0.7e1 / 0.12960e5 * t66 * t200 + t65 * t247 * t251 / 0.100e3
  t255 = t254 ** 2
  t256 = params.k1 + 0.5e1 / 0.972e3 * t33 * t190 + t49 * t193 * t197 * t203 / 0.576e3 + t255
  t261 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t256)
  t262 = t246 <= 0.25e1
  t263 = 0.25e1 < t246
  t264 = f.my_piecewise3(t263, 0.25e1, t246)
  t266 = t264 ** 2
  t268 = t266 * t264
  t270 = t266 ** 2
  t272 = t270 * t264
  t274 = t270 * t266
  t279 = f.my_piecewise3(t263, t246, 0.25e1)
  t280 = 0.1e1 - t279
  t283 = jnp.exp(params.c2 / t280)
  t285 = f.my_piecewise3(t262, 0.1e1 - 0.667e0 * t264 - 0.4445555e0 * t266 - 0.663086601049e0 * t268 + 0.1451297044490e1 * t270 - 0.887998041597e0 * t272 + 0.234528941479e0 * t274 - 0.23185843322e-1 * t270 * t268, -params.d * t283)
  t286 = 0.1e1 - t285
  t289 = t261 * t286 + 0.1174e1 * t285
  t291 = jnp.sqrt(s2)
  t293 = 0.1e1 / t186 / r1
  t295 = t161 * t291 * t293
  t296 = jnp.sqrt(t295)
  t300 = jnp.exp(-0.98958e1 * t159 / t296)
  t301 = 0.1e1 - t300
  t302 = t27 * t289 * t301
  t305 = f.my_piecewise3(t177, 0, -0.3e1 / 0.8e1 * t184 * t302)
  t307 = t16 / t72
  t308 = t7 - t307
  t309 = f.my_piecewise5(t10, 0, t14, 0, t308)
  t312 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t309)
  t316 = t27 ** 2
  t317 = 0.1e1 / t316
  t321 = t26 * t317 * t157 * t172 / 0.8e1
  t322 = params.k1 ** 2
  t323 = t124 ** 2
  t325 = t322 / t323
  t328 = 0.1e1 / t36 / t34 / r0
  t329 = s0 * t328
  t339 = t44 ** 2
  t340 = t29 ** 2
  t342 = t339 / t340
  t344 = t51 ** 2
  t355 = t70 * t74 * t84
  t356 = t98 * t111
  t362 = 0.5e1 / 0.32e2 * t71 * t73 * t112
  t363 = t75 * t83
  t368 = f.my_piecewise3(t81, -0.5e1 / 0.3e1 * tau0 * t38 + t329 / 0.3e1, 0)
  t372 = t96 ** 2
  t376 = t75 * t84 / t372 * t111
  t377 = t85 * t88
  t379 = t309 * t6 + t18 + 0.1e1
  t384 = t75 * t84
  t385 = t110 ** 2
  t386 = 0.1e1 / t385
  t387 = t98 * t386
  t390 = t100 * t87 * t69 * t72
  t399 = t70 * t73 * t83
  t400 = t98 * t45
  t409 = -0.5e1 / 0.32e2 * t355 * t356 * t309 - t362 - 0.3e1 / 0.32e2 * t363 * t356 * t368 + 0.3e1 / 0.256e3 * t376 * t377 * t91 * t379 + t384 * t387 * (0.5e1 / 0.24e2 * t390 * t107 * t379 + t105 * t82 * t106 * t368 / 0.8e1 - t399 * t400 * t31 * t379 / 0.32e2) / 0.32e2
  t413 = t65 * t117
  t423 = -t409
  t424 = f.my_piecewise3(t131, 0, t423)
  t439 = params.d * params.c2
  t440 = t148 ** 2
  t441 = 0.1e1 / t440
  t442 = f.my_piecewise3(t131, t423, 0)
  t446 = f.my_piecewise3(t130, -0.667e0 * t424 - 0.8891110e0 * t132 * t424 - 0.1989259803147e1 * t134 * t424 + 0.5805188177960e1 * t136 * t424 - 0.4439990207985e1 * t138 * t424 + 0.1407173648874e1 * t140 * t424 - 0.162300903254e0 * t142 * t424, -t439 * t441 * t442 * t151)
  t454 = 3 ** (0.1e1 / 0.6e1)
  t455 = t454 ** 2
  t456 = t455 ** 2
  t458 = t456 * t454 * t4
  t461 = t458 * t25 * t27 * t157
  t465 = 0.1e1 / t167 / t166 * t45 * t160
  t474 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t312 * t173 - t321 - 0.3e1 / 0.8e1 * t26 * t27 * (t325 * (-0.10e2 / 0.729e3 * t33 * t329 - t49 * t50 / t35 / t51 / t34 * t61 / 0.108e3 + 0.3e1 / 0.320e3 * t342 * t50 * s0 / t344 / r0 * t61 + 0.2e1 * t122 * (-0.7e1 / 0.4860e4 * t66 * t57 * t328 + t65 * t409 * t119 / 0.100e3 - t413 * t409 * t119 / 0.100e3)) * t154 - t129 * t446 + 0.1174e1 * t446) * t172 - 0.24739500000000000000000000000000000000000000000000e1 * t461 * t465 * t162 / t35 / t34 * t171)
  t476 = f.my_piecewise5(t14, 0, t10, 0, -t308)
  t479 = f.my_piecewise3(t180, 0, 0.4e1 / 0.3e1 * t181 * t476)
  t486 = t184 * t317 * t289 * t301 / 0.8e1
  t487 = t256 ** 2
  t489 = t322 / t487
  t491 = t210 * t74 * t221
  t492 = t232 * t243
  t498 = 0.5e1 / 0.32e2 * t211 * t73 * t244
  t499 = t230 ** 2
  t503 = t212 * t221 / t499 * t243
  t504 = t85 * t224
  t506 = t476 * t6 + t178 + 0.1e1
  t511 = t212 * t221
  t512 = t242 ** 2
  t513 = 0.1e1 / t512
  t514 = t232 * t513
  t517 = t100 * t223 * t209 * t72
  t522 = t210 * t73 * t220
  t523 = t232 * t45
  t532 = -0.5e1 / 0.32e2 * t491 * t492 * t476 - t498 + 0.3e1 / 0.256e3 * t503 * t504 * t91 * t506 + t511 * t514 * (0.5e1 / 0.24e2 * t517 * t239 * t506 - t522 * t523 * t31 * t506 / 0.32e2) / 0.32e2
  t535 = t65 * t249
  t544 = -t532
  t545 = f.my_piecewise3(t263, 0, t544)
  t560 = t280 ** 2
  t561 = 0.1e1 / t560
  t562 = f.my_piecewise3(t263, t544, 0)
  t566 = f.my_piecewise3(t262, -0.667e0 * t545 - 0.8891110e0 * t264 * t545 - 0.1989259803147e1 * t266 * t545 + 0.5805188177960e1 * t268 * t545 - 0.4439990207985e1 * t270 * t545 + 0.1407173648874e1 * t272 * t545 - 0.162300903254e0 * t274 * t545, -t439 * t561 * t562 * t283)
  t575 = f.my_piecewise3(t177, 0, -0.3e1 / 0.8e1 * t5 * t479 * t302 - t486 - 0.3e1 / 0.8e1 * t184 * t27 * (0.2e1 * t489 * t254 * (-t535 * t532 * t251 / 0.100e3 + t65 * t532 * t251 / 0.100e3) * t286 - t261 * t566 + 0.1174e1 * t566) * t301)
  vrho_0_ = t176 + t305 + t6 * (t474 + t575)
  t578 = -t7 - t307
  t579 = f.my_piecewise5(t10, 0, t14, 0, t578)
  t582 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t579)
  t590 = t579 * t6 + t18 + 0.1e1
  t606 = -0.5e1 / 0.32e2 * t355 * t356 * t579 - t362 + 0.3e1 / 0.256e3 * t376 * t377 * t91 * t590 + t384 * t387 * (0.5e1 / 0.24e2 * t390 * t107 * t590 - t399 * t400 * t31 * t590 / 0.32e2) / 0.32e2
  t617 = -t606
  t618 = f.my_piecewise3(t131, 0, t617)
  t633 = f.my_piecewise3(t131, t617, 0)
  t637 = f.my_piecewise3(t130, -0.667e0 * t618 - 0.8891110e0 * t132 * t618 - 0.1989259803147e1 * t134 * t618 + 0.5805188177960e1 * t136 * t618 - 0.4439990207985e1 * t138 * t618 + 0.1407173648874e1 * t140 * t618 - 0.162300903254e0 * t142 * t618, -t439 * t441 * t633 * t151)
  t646 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t582 * t173 - t321 - 0.3e1 / 0.8e1 * t26 * t27 * (0.2e1 * t325 * t122 * (-t413 * t606 * t119 / 0.100e3 + t65 * t606 * t119 / 0.100e3) * t154 - t129 * t637 + 0.1174e1 * t637) * t172)
  t648 = f.my_piecewise5(t14, 0, t10, 0, -t578)
  t651 = f.my_piecewise3(t180, 0, 0.4e1 / 0.3e1 * t181 * t648)
  t657 = 0.1e1 / t187 / t185 / r1
  t658 = s2 * t657
  t669 = t194 ** 2
  t682 = t212 * t220
  t687 = f.my_piecewise3(t218, -0.5e1 / 0.3e1 * tau1 * t189 + t658 / 0.3e1, 0)
  t692 = t648 * t6 + t178 + 0.1e1
  t712 = -0.5e1 / 0.32e2 * t491 * t492 * t648 - t498 - 0.3e1 / 0.32e2 * t682 * t492 * t687 + 0.3e1 / 0.256e3 * t503 * t504 * t91 * t692 + t511 * t514 * (0.5e1 / 0.24e2 * t517 * t239 * t692 + t237 * t219 * t238 * t687 / 0.8e1 - t522 * t523 * t31 * t692 / 0.32e2) / 0.32e2
  t725 = -t712
  t726 = f.my_piecewise3(t263, 0, t725)
  t741 = f.my_piecewise3(t263, t725, 0)
  t745 = f.my_piecewise3(t262, -0.667e0 * t726 - 0.8891110e0 * t264 * t726 - 0.1989259803147e1 * t266 * t726 + 0.5805188177960e1 * t268 * t726 - 0.4439990207985e1 * t270 * t726 + 0.1407173648874e1 * t272 * t726 - 0.162300903254e0 * t274 * t726, -t439 * t561 * t741 * t283)
  t755 = t458 * t183 * t27 * t289
  t759 = 0.1e1 / t296 / t295 * t45 * t160
  t768 = f.my_piecewise3(t177, 0, -0.3e1 / 0.8e1 * t5 * t651 * t302 - t486 - 0.3e1 / 0.8e1 * t184 * t27 * (t489 * (-0.10e2 / 0.729e3 * t33 * t658 - t49 * t193 / t186 / t194 / t185 * t203 / 0.108e3 + 0.3e1 / 0.320e3 * t342 * t193 * s2 / t669 / r1 * t203 + 0.2e1 * t254 * (-0.7e1 / 0.4860e4 * t66 * t199 * t657 + t65 * t712 * t251 / 0.100e3 - t535 * t712 * t251 / 0.100e3)) * t286 - t261 * t745 + 0.1174e1 * t745) * t301 - 0.24739500000000000000000000000000000000000000000000e1 * t755 * t759 * t291 / t186 / t185 * t300)
  vrho_1_ = t176 + t305 + t6 * (t646 + t768)
  t786 = f.my_piecewise3(t81, -t38 / 0.8e1, 0)
  t790 = t83 ** 2
  t794 = t75 * t790 / t372 / t95
  t795 = t386 * t100
  t800 = -0.3e1 / 0.32e2 * t363 * t356 * t786 + t794 * t795 * t104 * t786 / 0.256e3
  t813 = -t800
  t814 = f.my_piecewise3(t131, 0, t813)
  t829 = f.my_piecewise3(t131, t813, 0)
  t833 = f.my_piecewise3(t130, -0.667e0 * t814 - 0.8891110e0 * t132 * t814 - 0.1989259803147e1 * t134 * t814 + 0.5805188177960e1 * t136 * t814 - 0.4439990207985e1 * t138 * t814 + 0.1407173648874e1 * t140 * t814 - 0.162300903254e0 * t142 * t814, -t439 * t441 * t829 * t151)
  t848 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (t325 * (0.5e1 / 0.972e3 * t33 * t38 + t49 * s0 * t54 * t61 / 0.288e3 - 0.9e1 / 0.2560e4 * t342 * t50 / t344 * t61 + 0.2e1 * t122 * (0.7e1 / 0.12960e5 * t66 * t32 * t38 + t65 * t800 * t119 / 0.100e3 - t413 * t800 * t119 / 0.100e3)) * t154 - t129 * t833 + 0.1174e1 * t833) * t172 + 0.92773125000000000000000000000000000000000000000000e0 * t461 * t465 / t162 * t164 * t171)
  vsigma_0_ = t6 * t848
  vsigma_1_ = 0.0e0
  t864 = f.my_piecewise3(t218, -t189 / 0.8e1, 0)
  t868 = t220 ** 2
  t872 = t212 * t868 / t499 / t229
  t873 = t513 * t100
  t878 = -0.3e1 / 0.32e2 * t682 * t492 * t864 + t872 * t873 * t236 * t864 / 0.256e3
  t891 = -t878
  t892 = f.my_piecewise3(t263, 0, t891)
  t907 = f.my_piecewise3(t263, t891, 0)
  t911 = f.my_piecewise3(t262, -0.667e0 * t892 - 0.8891110e0 * t264 * t892 - 0.1989259803147e1 * t266 * t892 + 0.5805188177960e1 * t268 * t892 - 0.4439990207985e1 * t270 * t892 + 0.1407173648874e1 * t272 * t892 - 0.162300903254e0 * t274 * t892, -t439 * t561 * t907 * t283)
  t926 = f.my_piecewise3(t177, 0, -0.3e1 / 0.8e1 * t184 * t27 * (t489 * (0.5e1 / 0.972e3 * t33 * t189 + t49 * s2 * t197 * t203 / 0.288e3 - 0.9e1 / 0.2560e4 * t342 * t193 / t669 * t203 + 0.2e1 * t254 * (0.7e1 / 0.12960e5 * t66 * t32 * t189 + t65 * t878 * t251 / 0.100e3 - t535 * t878 * t251 / 0.100e3)) * t286 - t261 * t911 + 0.1174e1 * t911) * t301 + 0.92773125000000000000000000000000000000000000000000e0 * t755 * t759 / t291 * t293 * t300)
  vsigma_2_ = t6 * t926
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t927 = f.my_piecewise3(t81, t77, 0)
  t935 = -0.3e1 / 0.32e2 * t363 * t356 * t927 + t794 * t795 * t104 * t927 / 0.256e3
  t946 = -t935
  t947 = f.my_piecewise3(t131, 0, t946)
  t962 = f.my_piecewise3(t131, t946, 0)
  t966 = f.my_piecewise3(t130, -0.667e0 * t947 - 0.8891110e0 * t132 * t947 - 0.1989259803147e1 * t134 * t947 + 0.5805188177960e1 * t136 * t947 - 0.4439990207985e1 * t138 * t947 + 0.1407173648874e1 * t140 * t947 - 0.162300903254e0 * t142 * t947, -t439 * t441 * t962 * t151)
  t974 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t26 * t27 * (0.2e1 * t325 * t122 * (-t413 * t935 * t119 / 0.100e3 + t65 * t935 * t119 / 0.100e3) * t154 - t129 * t966 + 0.1174e1 * t966) * t172)
  vtau_0_ = t6 * t974
  t975 = f.my_piecewise3(t218, t214, 0)
  t983 = -0.3e1 / 0.32e2 * t682 * t492 * t975 + t872 * t873 * t236 * t975 / 0.256e3
  t994 = -t983
  t995 = f.my_piecewise3(t263, 0, t994)
  t1010 = f.my_piecewise3(t263, t994, 0)
  t1014 = f.my_piecewise3(t262, -0.667e0 * t995 - 0.8891110e0 * t264 * t995 - 0.1989259803147e1 * t266 * t995 + 0.5805188177960e1 * t268 * t995 - 0.4439990207985e1 * t270 * t995 + 0.1407173648874e1 * t272 * t995 - 0.162300903254e0 * t274 * t995, -t439 * t561 * t1010 * t283)
  t1022 = f.my_piecewise3(t177, 0, -0.3e1 / 0.8e1 * t184 * t27 * (0.2e1 * t489 * t254 * (-t535 * t983 * t251 / 0.100e3 + t65 * t983 * t251 / 0.100e3) * t286 - t261 * t1014 + 0.1174e1 * t1014) * t301)
  vtau_1_ = t6 * t1022
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
  params_alphar_raw = params.alphar
  if isinstance(params_alphar_raw, (str, bytes, dict)):
    params_alphar = params_alphar_raw
  else:
    try:
      params_alphar_seq = list(params_alphar_raw)
    except TypeError:
      params_alphar = params_alphar_raw
    else:
      params_alphar_seq = np.asarray(params_alphar_seq, dtype=np.float64)
      params_alphar = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphar_seq))
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
  params_taur_raw = params.taur
  if isinstance(params_taur_raw, (str, bytes, dict)):
    params_taur = params_taur_raw
  else:
    try:
      params_taur_seq = list(params_taur_raw)
    except TypeError:
      params_taur = params_taur_raw
    else:
      params_taur_seq = np.asarray(params_taur_seq, dtype=np.float64)
      params_taur = np.concatenate((np.array([np.nan], dtype=np.float64), params_taur_seq))

  params_c1 = 0.667
  params_dp2 = 0.361
  scan_p = lambda x: X2S ** 2 * x ** 2

  scan_h1x = lambda x: 1 + params_k1 * (1 - params_k1 / (params_k1 + x))

  scan_b2 = jnp.sqrt(5913 / 405000)

  scan_b3 = 1 / 2

  scan_a1 = 4.9479

  scan_h0x = 1.174

  rscan_fx = np.array([np.nan, -0.023185843322, 0.234528941479, -0.887998041597, 1.45129704449, -0.663086601049, -0.4445555, -0.667, 1], dtype=np.float64)

  np53 = lambda rs, z: f.n_spin(rs, z) ** (5 / 3)

  rscan_f_alpha_small = lambda a, ff: jnp.sum(jnp.array([ff[8 - i] * a ** i for i in range(0, 7 + 1)]), axis=0)

  rscan_f_alpha_large = lambda a: -params_d * jnp.exp(params_c2 / (1 - a))

  scan_b1 = 511 / 13500 / (2 * scan_b2)

  scan_gx = lambda x: 1 - jnp.exp(-scan_a1 / jnp.sqrt(X2S * x))

  rscan_alpha0 = lambda rs, z, x, t: np53(rs, z) * jnp.maximum(t - x ** 2 / 8, 0) / (np53(rs, z) * K_FACTOR_C + params_taur / 2)

  rscan_f_alpha = lambda a, ff: f.my_piecewise3(a <= 2.5, rscan_f_alpha_small(jnp.minimum(a, 2.5), ff), rscan_f_alpha_large(jnp.maximum(a, 2.5)))

  scan_b4 = MU_GE ** 2 / params_k1 - 1606 / 18225 - scan_b1 ** 2

  rscan_alpha = lambda rs, z, x, t: rscan_alpha0(rs, z, x, t) ** 3 / (rscan_alpha0(rs, z, x, t) ** 2 + params_alphar)

  scan_y = lambda x, a: MU_GE * scan_p(x) + scan_b4 * scan_p(x) ** 2 * jnp.exp(-scan_b4 * scan_p(x) / MU_GE) + (scan_b1 * scan_p(x) + scan_b2 * (1 - a) * jnp.exp(-scan_b3 * (1 - a) ** 2)) ** 2

  rscan_f = lambda rs, z, x, u, t: (scan_h1x(scan_y(x, rscan_alpha(rs, z, x, t))) * (1 - rscan_f_alpha(rscan_alpha(rs, z, x, t), rscan_fx)) + scan_h0x * rscan_f_alpha(rscan_alpha(rs, z, x, t), rscan_fx)) * scan_gx(x)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, rscan_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t20 = 6 ** (0.1e1 / 0.3e1)
  t21 = jnp.pi ** 2
  t22 = t21 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = 0.1e1 / t23
  t25 = t20 * t24
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = s0 * t27
  t29 = r0 ** 2
  t30 = t19 ** 2
  t32 = 0.1e1 / t30 / t29
  t33 = t28 * t32
  t38 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t39 = t20 ** 2
  t43 = t38 * t39 / t22 / t21
  t44 = s0 ** 2
  t45 = t44 * t26
  t46 = t29 ** 2
  t47 = t46 * r0
  t54 = jnp.exp(-0.27e2 / 0.80e2 * t38 * t20 * t24 * t33)
  t55 = 0.1e1 / t19 / t47 * t54
  t59 = jnp.sqrt(0.146e3)
  t60 = t59 * t20
  t61 = t60 * t24
  t64 = t11 ** 2
  t65 = t64 ** 2
  t66 = t65 * t11
  t67 = t66 * t47
  t68 = tau0 * t27
  t70 = 0.1e1 / t30 / r0
  t73 = t68 * t70 - t33 / 0.8e1
  t74 = 0.0e0 < t73
  t75 = f.my_piecewise3(t74, t73, 0)
  t76 = t75 ** 2
  t77 = t76 * t75
  t78 = t11 * r0
  t79 = t78 ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t87 = 0.3e1 / 0.40e2 * t26 * t80 * t78 * t39 * t23 + params.taur / 0.2e1
  t88 = t87 ** 2
  t90 = 0.1e1 / t88 / t87
  t93 = t29 * r0
  t95 = t79 * t64 * t11 * t93
  t96 = t27 * t95
  t97 = 0.1e1 / t88
  t98 = t76 * t97
  t101 = t96 * t98 / 0.16e2 + params.alphar
  t102 = 0.1e1 / t101
  t103 = t77 * t90 * t102
  t105 = t67 * t103 / 0.32e2
  t106 = 0.1e1 - t105
  t108 = t106 ** 2
  t110 = jnp.exp(-t108 / 0.2e1)
  t113 = 0.7e1 / 0.12960e5 * t61 * t33 + t59 * t106 * t110 / 0.100e3
  t114 = t113 ** 2
  t115 = params.k1 + 0.5e1 / 0.972e3 * t25 * t33 + t43 * t45 * t55 / 0.288e3 + t114
  t120 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t115)
  t121 = t105 <= 0.25e1
  t122 = 0.25e1 < t105
  t123 = f.my_piecewise3(t122, 0.25e1, t105)
  t125 = t123 ** 2
  t127 = t125 * t123
  t129 = t125 ** 2
  t131 = t129 * t123
  t133 = t129 * t125
  t138 = f.my_piecewise3(t122, t105, 0.25e1)
  t139 = 0.1e1 - t138
  t142 = jnp.exp(params.c2 / t139)
  t144 = f.my_piecewise3(t121, 0.1e1 - 0.667e0 * t123 - 0.4445555e0 * t125 - 0.663086601049e0 * t127 + 0.1451297044490e1 * t129 - 0.887998041597e0 * t131 + 0.234528941479e0 * t133 - 0.23185843322e-1 * t129 * t127, -params.d * t142)
  t145 = 0.1e1 - t144
  t148 = t120 * t145 + 0.1174e1 * t144
  t150 = jnp.sqrt(0.3e1)
  t151 = 0.1e1 / t22
  t153 = jnp.sqrt(s0)
  t154 = t153 * t26
  t158 = t39 * t151 * t154 / t19 / r0
  t159 = jnp.sqrt(t158)
  t163 = jnp.exp(-0.98958e1 * t150 / t159)
  t164 = 0.1e1 - t163
  t168 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * t148 * t164)
  t174 = params.k1 ** 2
  t175 = t115 ** 2
  t177 = t174 / t175
  t180 = t28 / t30 / t93
  t190 = t38 ** 2
  t191 = t21 ** 2
  t193 = t190 / t191
  t195 = t46 ** 2
  t204 = t66 * t46
  t207 = t67 * t76
  t208 = t90 * t102
  t213 = f.my_piecewise3(t74, -0.5e1 / 0.3e1 * t68 * t32 + t180 / 0.3e1, 0)
  t219 = t88 ** 2
  t230 = t101 ** 2
  t231 = 0.1e1 / t230
  t252 = -0.5e1 / 0.32e2 * t204 * t103 - 0.3e1 / 0.32e2 * t207 * t208 * t213 + 0.3e1 / 0.256e3 * t65 * t64 * t47 * t77 / t219 * t102 * t26 * t80 * t39 * t23 + t67 * t77 * t90 * t231 * (0.5e1 / 0.24e2 * t27 * t79 * t64 * t29 * t98 * t11 + t96 * t75 * t97 * t213 / 0.8e1 - t204 * t76 * t90 * t39 * t23 / 0.32e2) / 0.32e2
  t256 = t59 * t108
  t266 = -t252
  t267 = f.my_piecewise3(t122, 0, t266)
  t282 = params.d * params.c2
  t283 = t139 ** 2
  t284 = 0.1e1 / t283
  t285 = f.my_piecewise3(t122, t266, 0)
  t289 = f.my_piecewise3(t121, -0.667e0 * t267 - 0.8891110e0 * t123 * t267 - 0.1989259803147e1 * t125 * t267 + 0.5805188177960e1 * t127 * t267 - 0.4439990207985e1 * t129 * t267 + 0.1407173648874e1 * t131 * t267 - 0.162300903254e0 * t133 * t267, -t282 * t284 * t285 * t142)
  t297 = 3 ** (0.1e1 / 0.6e1)
  t298 = t297 ** 2
  t299 = t298 ** 2
  t301 = t299 * t297 * t5
  t309 = 0.1e1 / t159 / t158 * t39 * t151
  t315 = f.my_piecewise3(t2, 0, -t18 / t30 * t148 * t164 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * (t177 * (-0.10e2 / 0.729e3 * t25 * t180 - t43 * t45 / t19 / t46 / t29 * t54 / 0.54e2 + 0.3e1 / 0.80e2 * t193 * t44 * s0 / t195 / r0 * t54 + 0.2e1 * t113 * (-0.7e1 / 0.4860e4 * t61 * t180 + t59 * t252 * t110 / 0.100e3 - t256 * t252 * t110 / 0.100e3)) * t145 - t120 * t289 + 0.1174e1 * t289) * t164 - 0.24739500000000000000000000000000000000000000000000e1 * t301 * t17 / t29 * t148 * t309 * t154 * t163)
  vrho_0_ = 0.2e1 * r0 * t315 + 0.2e1 * t168
  t318 = t27 * t32
  t335 = f.my_piecewise3(t74, -t318 / 0.8e1, 0)
  t339 = t76 ** 2
  t343 = t67 * t339 / t219 / t87
  t344 = t231 * t27
  t349 = -0.3e1 / 0.32e2 * t207 * t208 * t335 + t343 * t344 * t95 * t335 / 0.256e3
  t362 = -t349
  t363 = f.my_piecewise3(t122, 0, t362)
  t378 = f.my_piecewise3(t122, t362, 0)
  t382 = f.my_piecewise3(t121, -0.667e0 * t363 - 0.8891110e0 * t123 * t363 - 0.1989259803147e1 * t125 * t363 + 0.5805188177960e1 * t127 * t363 - 0.4439990207985e1 * t129 * t363 + 0.1407173648874e1 * t131 * t363 - 0.162300903254e0 * t133 * t363, -t282 * t284 * t378 * t142)
  t401 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (t177 * (0.5e1 / 0.972e3 * t25 * t318 + t43 * s0 * t26 * t55 / 0.144e3 - 0.9e1 / 0.640e3 * t193 * t44 / t195 * t54 + 0.2e1 * t113 * (0.7e1 / 0.12960e5 * t60 * t24 * t27 * t32 + t59 * t349 * t110 / 0.100e3 - t256 * t349 * t110 / 0.100e3)) * t145 - t120 * t382 + 0.1174e1 * t382) * t164 + 0.92773125000000000000000000000000000000000000000000e0 * t301 * t17 / r0 * t148 * t309 / t153 * t26 * t163)
  vsigma_0_ = 0.2e1 * r0 * t401
  vlapl_0_ = 0.0e0
  t404 = f.my_piecewise3(t74, t27 * t70, 0)
  t412 = -0.3e1 / 0.32e2 * t207 * t208 * t404 + t343 * t344 * t95 * t404 / 0.256e3
  t423 = -t412
  t424 = f.my_piecewise3(t122, 0, t423)
  t439 = f.my_piecewise3(t122, t423, 0)
  t443 = f.my_piecewise3(t121, -0.667e0 * t424 - 0.8891110e0 * t123 * t424 - 0.1989259803147e1 * t125 * t424 + 0.5805188177960e1 * t127 * t424 - 0.4439990207985e1 * t129 * t424 + 0.1407173648874e1 * t131 * t424 - 0.162300903254e0 * t133 * t424, -t282 * t284 * t439 * t142)
  t451 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t18 * t19 * (0.2e1 * t177 * t113 * (-t256 * t412 * t110 / 0.100e3 + t59 * t412 * t110 / 0.100e3) * t145 - t120 * t443 + 0.1174e1 * t443) * t164)
  vtau_0_ = 0.2e1 * r0 * t451
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
  t21 = 0.1e1 / t20
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = jnp.pi ** 2
  t24 = t23 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = 0.1e1 / t25
  t27 = t22 * t26
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = s0 * t29
  t31 = r0 ** 2
  t33 = 0.1e1 / t20 / t31
  t34 = t30 * t33
  t35 = t27 * t34
  t39 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t40 = t22 ** 2
  t42 = t24 * t23
  t44 = t39 * t40 / t42
  t45 = s0 ** 2
  t46 = t45 * t28
  t47 = t31 ** 2
  t48 = t47 * r0
  t55 = jnp.exp(-0.27e2 / 0.80e2 * t39 * t22 * t26 * t34)
  t60 = jnp.sqrt(0.146e3)
  t62 = t60 * t22 * t26
  t65 = t11 ** 2
  t66 = t65 ** 2
  t67 = t66 * t11
  t68 = t67 * t48
  t69 = tau0 * t29
  t71 = 0.1e1 / t20 / r0
  t74 = t69 * t71 - t34 / 0.8e1
  t75 = 0.0e0 < t74
  t76 = f.my_piecewise3(t75, t74, 0)
  t77 = t76 ** 2
  t78 = t77 * t76
  t79 = t11 * r0
  t80 = t79 ** (0.1e1 / 0.3e1)
  t81 = t80 ** 2
  t84 = t40 * t25
  t88 = 0.3e1 / 0.40e2 * t28 * t81 * t79 * t84 + params.taur / 0.2e1
  t89 = t88 ** 2
  t91 = 0.1e1 / t89 / t88
  t93 = t65 * t11
  t94 = t31 * r0
  t97 = t29 * t80 * t93 * t94
  t98 = 0.1e1 / t89
  t99 = t77 * t98
  t102 = t97 * t99 / 0.16e2 + params.alphar
  t103 = 0.1e1 / t102
  t104 = t78 * t91 * t103
  t106 = t68 * t104 / 0.32e2
  t107 = 0.1e1 - t106
  t109 = t107 ** 2
  t111 = jnp.exp(-t109 / 0.2e1)
  t114 = 0.7e1 / 0.12960e5 * t62 * t34 + t60 * t107 * t111 / 0.100e3
  t115 = t114 ** 2
  t116 = params.k1 + 0.5e1 / 0.972e3 * t35 + t44 * t46 / t19 / t48 * t55 / 0.288e3 + t115
  t121 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t116)
  t122 = t106 <= 0.25e1
  t123 = 0.25e1 < t106
  t124 = f.my_piecewise3(t123, 0.25e1, t106)
  t126 = t124 ** 2
  t128 = t126 * t124
  t130 = t126 ** 2
  t132 = t130 * t124
  t134 = t130 * t126
  t139 = f.my_piecewise3(t123, t106, 0.25e1)
  t140 = 0.1e1 - t139
  t143 = jnp.exp(params.c2 / t140)
  t145 = f.my_piecewise3(t122, 0.1e1 - 0.667e0 * t124 - 0.4445555e0 * t126 - 0.663086601049e0 * t128 + 0.1451297044490e1 * t130 - 0.887998041597e0 * t132 + 0.234528941479e0 * t134 - 0.23185843322e-1 * t130 * t128, -params.d * t143)
  t146 = 0.1e1 - t145
  t149 = t121 * t146 + 0.1174e1 * t145
  t151 = jnp.sqrt(0.3e1)
  t152 = 0.1e1 / t24
  t154 = jnp.sqrt(s0)
  t155 = t154 * t28
  t159 = t40 * t152 * t155 / t19 / r0
  t160 = jnp.sqrt(t159)
  t164 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t151 / t160)
  t165 = 0.1e1 - t164
  t169 = params.k1 ** 2
  t170 = t116 ** 2
  t172 = t169 / t170
  t174 = 0.1e1 / t20 / t94
  t175 = t30 * t174
  t185 = t39 ** 2
  t186 = t23 ** 2
  t187 = 0.1e1 / t186
  t188 = t185 * t187
  t189 = t45 * s0
  t190 = t47 ** 2
  t199 = t67 * t47
  t202 = t68 * t77
  t203 = t91 * t103
  t208 = f.my_piecewise3(t75, -0.5e1 / 0.3e1 * t69 * t33 + t175 / 0.3e1, 0)
  t209 = t203 * t208
  t212 = t66 * t65
  t213 = t212 * t48
  t214 = t89 ** 2
  t215 = 0.1e1 / t214
  t216 = t78 * t215
  t218 = t103 * t28
  t220 = t81 * t40 * t25
  t221 = t218 * t220
  t224 = t68 * t78
  t225 = t102 ** 2
  t226 = 0.1e1 / t225
  t227 = t91 * t226
  t230 = t29 * t80 * t65 * t31
  t234 = t76 * t98
  t238 = t199 * t77
  t240 = t91 * t40 * t25
  t243 = 0.5e1 / 0.24e2 * t230 * t99 * t11 + t97 * t234 * t208 / 0.8e1 - t238 * t240 / 0.32e2
  t244 = t227 * t243
  t247 = -0.5e1 / 0.32e2 * t199 * t104 - 0.3e1 / 0.32e2 * t202 * t209 + 0.3e1 / 0.256e3 * t213 * t216 * t221 + t224 * t244 / 0.32e2
  t251 = t60 * t109
  t255 = -0.7e1 / 0.4860e4 * t62 * t175 + t60 * t247 * t111 / 0.100e3 - t251 * t247 * t111 / 0.100e3
  t258 = -0.10e2 / 0.729e3 * t27 * t175 - t44 * t46 / t19 / t47 / t31 * t55 / 0.54e2 + 0.3e1 / 0.80e2 * t188 * t189 / t190 / r0 * t55 + 0.2e1 * t114 * t255
  t261 = -t247
  t262 = f.my_piecewise3(t123, 0, t261)
  t277 = params.d * params.c2
  t278 = t140 ** 2
  t279 = 0.1e1 / t278
  t280 = f.my_piecewise3(t123, t261, 0)
  t284 = f.my_piecewise3(t122, -0.667e0 * t262 - 0.8891110e0 * t124 * t262 - 0.1989259803147e1 * t126 * t262 + 0.5805188177960e1 * t128 * t262 - 0.4439990207985e1 * t130 * t262 + 0.1407173648874e1 * t132 * t262 - 0.162300903254e0 * t134 * t262, -t277 * t279 * t280 * t143)
  t287 = t172 * t258 * t146 - t121 * t284 + 0.1174e1 * t284
  t292 = 3 ** (0.1e1 / 0.6e1)
  t293 = t292 ** 2
  t294 = t293 ** 2
  t296 = t294 * t292 * t5
  t298 = t17 / t31
  t306 = 0.1e1 / t160 / t159 * t40 * t152 * t155 * t164
  t310 = f.my_piecewise3(t2, 0, -t18 * t21 * t149 * t165 / 0.8e1 - 0.3e1 / 0.8e1 * t18 * t19 * t287 * t165 - 0.24739500000000000000000000000000000000000000000000e1 * t296 * t298 * t149 * t306)
  t329 = t258 ** 2
  t335 = t30 / t20 / t47
  t353 = t45 ** 2
  t363 = t255 ** 2
  t367 = t67 * t94
  t372 = t212 * t47
  t380 = t208 ** 2
  t384 = t77 * t215
  t399 = f.my_piecewise3(t75, 0.40e2 / 0.9e1 * t69 * t174 - 0.11e2 / 0.9e1 * t335, 0)
  t404 = t66 * t93 * t48
  t410 = t80 * t79
  t418 = t28 * t81
  t433 = t243 ** 2
  t469 = -0.5e1 / 0.8e1 * t367 * t104 - 0.15e2 / 0.16e2 * t238 * t209 + 0.15e2 / 0.128e3 * t372 * t216 * t221 + 0.5e1 / 0.16e2 * t199 * t78 * t244 - 0.3e1 / 0.16e2 * t68 * t76 * t203 * t380 + 0.9e1 / 0.128e3 * t213 * t384 * t103 * t208 * t28 * t220 + 0.3e1 / 0.16e2 * t202 * t227 * t208 * t243 - 0.3e1 / 0.32e2 * t202 * t203 * t399 - 0.9e1 / 0.256e3 * t404 * t78 / t214 / t88 * t103 * t29 * t410 * t22 * t42 - 0.3e1 / 0.128e3 * t213 * t216 * t226 * t418 * t84 * t243 + t404 * t216 * t218 / t80 * t40 * t25 / 0.128e3 - t224 * t91 / t225 / t102 * t433 / 0.16e2 + t224 * t227 * (0.35e2 / 0.72e2 * t29 * t410 * t99 * t65 + 0.5e1 / 0.6e1 * t230 * t76 * t98 * t11 * t208 - 0.11e2 / 0.48e2 * t367 * t77 * t240 + t97 * t380 * t98 / 0.8e1 - t199 * t76 * t91 * t208 * t84 / 0.8e1 + t97 * t234 * t399 / 0.8e1 + 0.9e1 / 0.128e3 * t372 * t384 * t22 * t42 * t418) / 0.32e2
  t473 = t247 ** 2
  t495 = -t469
  t496 = f.my_piecewise3(t123, 0, t495)
  t498 = t262 ** 2
  t522 = -0.667e0 * t496 - 0.8891110e0 * t498 - 0.8891110e0 * t124 * t496 - 0.3978519606294e1 * t124 * t498 - 0.1989259803147e1 * t126 * t496 + 0.17415564533880e2 * t126 * t498 + 0.5805188177960e1 * t128 * t496 - 0.17759960831940e2 * t128 * t498 - 0.4439990207985e1 * t130 * t496 + 0.7035868244370e1 * t130 * t498 + 0.1407173648874e1 * t132 * t496 - 0.973805419524e0 * t132 * t498 - 0.162300903254e0 * t134 * t496
  t525 = t280 ** 2
  t530 = f.my_piecewise3(t123, t495, 0)
  t534 = params.c2 ** 2
  t536 = t278 ** 2
  t542 = f.my_piecewise3(t122, t522, -0.2e1 * t277 / t278 / t140 * t525 * t143 - t277 * t279 * t530 * t143 - params.d * t534 / t536 * t525 * t143)
  t568 = t4 ** 2
  t583 = f.my_piecewise3(t2, 0, t18 * t71 * t149 * t165 / 0.12e2 - t18 * t21 * t287 * t165 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t296 * t17 / t94 * t149 * t306 - 0.3e1 / 0.8e1 * t18 * t19 * (-0.2e1 * t169 / t170 / t116 * t329 * t146 + t172 * (0.110e3 / 0.2187e4 * t27 * t335 + 0.19e2 / 0.162e3 * t44 * t46 / t19 / t47 / t94 * t55 - 0.43e2 / 0.80e2 * t188 * t189 / t190 / t31 * t55 + 0.27e2 / 0.800e3 * t185 * t39 * t187 * t353 / t20 / t190 / t47 * t27 * t29 * t55 + 0.2e1 * t363 + 0.2e1 * t114 * (0.77e2 / 0.14580e5 * t62 * t335 + t60 * t469 * t111 / 0.100e3 - 0.3e1 / 0.100e3 * t60 * t473 * t107 * t111 - t251 * t469 * t111 / 0.100e3 + t60 * t109 * t107 * t473 * t111 / 0.100e3)) * t146 - 0.2e1 * t172 * t258 * t284 - t121 * t542 + 0.1174e1 * t542) * t165 - 0.49479000000000000000000000000000000000000000000000e1 * t296 * t298 * t287 * t306 - 0.49479000000000000000000000000000000000000000000000e1 * t296 * t17 / t19 / t47 * t149 / t160 / t35 * t22 * t26 * t30 * t164 + 0.40802857350000000000000000000000000000000000000000e1 * t3 * t568 * jnp.pi * t17 / t19 * t149 / t154 * t22 * t26 * t29 * t164)
  v2rho2_0_ = 0.2e1 * r0 * t583 + 0.4e1 * t310

  res = {'v2rho2': v2rho2_0_}
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
  t23 = 6 ** (0.1e1 / 0.3e1)
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = t23 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t20 / t32
  t35 = t31 * t34
  t36 = t28 * t35
  t40 = 0.100e3 / 0.6561e4 / params.k1 - 0.73e2 / 0.648e3
  t41 = t23 ** 2
  t43 = t25 * t24
  t44 = 0.1e1 / t43
  t45 = t40 * t41 * t44
  t46 = s0 ** 2
  t47 = t46 * t29
  t48 = t32 ** 2
  t49 = t48 * r0
  t51 = 0.1e1 / t19 / t49
  t56 = jnp.exp(-0.27e2 / 0.80e2 * t40 * t23 * t27 * t35)
  t61 = jnp.sqrt(0.146e3)
  t63 = t61 * t23 * t27
  t66 = t11 ** 2
  t67 = t66 ** 2
  t68 = t67 * t11
  t69 = t68 * t49
  t70 = tau0 * t30
  t73 = t70 * t22 - t35 / 0.8e1
  t74 = 0.0e0 < t73
  t75 = f.my_piecewise3(t74, t73, 0)
  t76 = t75 ** 2
  t77 = t76 * t75
  t78 = t11 * r0
  t79 = t78 ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t83 = t41 * t26
  t87 = 0.3e1 / 0.40e2 * t29 * t80 * t78 * t83 + params.taur / 0.2e1
  t88 = t87 ** 2
  t90 = 0.1e1 / t88 / t87
  t92 = t66 * t11
  t93 = t32 * r0
  t96 = t30 * t79 * t92 * t93
  t97 = 0.1e1 / t88
  t98 = t76 * t97
  t101 = t96 * t98 / 0.16e2 + params.alphar
  t102 = 0.1e1 / t101
  t103 = t77 * t90 * t102
  t105 = t69 * t103 / 0.32e2
  t106 = 0.1e1 - t105
  t108 = t106 ** 2
  t110 = jnp.exp(-t108 / 0.2e1)
  t113 = 0.7e1 / 0.12960e5 * t63 * t35 + t61 * t106 * t110 / 0.100e3
  t114 = t113 ** 2
  t115 = params.k1 + 0.5e1 / 0.972e3 * t36 + t45 * t47 * t51 * t56 / 0.288e3 + t114
  t120 = 0.1e1 + params.k1 * (0.1e1 - params.k1 / t115)
  t121 = t105 <= 0.25e1
  t122 = 0.25e1 < t105
  t123 = f.my_piecewise3(t122, 0.25e1, t105)
  t125 = t123 ** 2
  t127 = t125 * t123
  t129 = t125 ** 2
  t131 = t129 * t123
  t133 = t129 * t125
  t138 = f.my_piecewise3(t122, t105, 0.25e1)
  t139 = 0.1e1 - t138
  t142 = jnp.exp(params.c2 / t139)
  t144 = f.my_piecewise3(t121, 0.1e1 - 0.667e0 * t123 - 0.4445555e0 * t125 - 0.663086601049e0 * t127 + 0.1451297044490e1 * t129 - 0.887998041597e0 * t131 + 0.234528941479e0 * t133 - 0.23185843322e-1 * t129 * t127, -params.d * t142)
  t145 = 0.1e1 - t144
  t148 = t120 * t145 + 0.1174e1 * t144
  t150 = jnp.sqrt(0.3e1)
  t151 = 0.1e1 / t25
  t153 = jnp.sqrt(s0)
  t154 = t153 * t29
  t156 = 0.1e1 / t19 / r0
  t158 = t41 * t151 * t154 * t156
  t159 = jnp.sqrt(t158)
  t163 = jnp.exp(-0.98958000000000000000000000000000000000000000000000e1 * t150 / t159)
  t164 = 0.1e1 - t163
  t168 = 0.1e1 / t20
  t169 = params.k1 ** 2
  t170 = t115 ** 2
  t172 = t169 / t170
  t174 = 0.1e1 / t20 / t93
  t175 = t31 * t174
  t178 = t48 * t32
  t185 = t40 ** 2
  t186 = t24 ** 2
  t187 = 0.1e1 / t186
  t188 = t185 * t187
  t189 = t46 * s0
  t190 = t48 ** 2
  t199 = t68 * t48
  t202 = t69 * t76
  t203 = t90 * t102
  t208 = f.my_piecewise3(t74, -0.5e1 / 0.3e1 * t70 * t34 + t175 / 0.3e1, 0)
  t209 = t203 * t208
  t212 = t67 * t66
  t213 = t212 * t49
  t214 = t88 ** 2
  t215 = 0.1e1 / t214
  t216 = t77 * t215
  t218 = t102 * t29
  t220 = t80 * t41 * t26
  t221 = t218 * t220
  t224 = t69 * t77
  t225 = t101 ** 2
  t226 = 0.1e1 / t225
  t227 = t90 * t226
  t230 = t30 * t79 * t66 * t32
  t234 = t75 * t97
  t238 = t199 * t76
  t240 = t90 * t41 * t26
  t243 = 0.5e1 / 0.24e2 * t230 * t98 * t11 + t96 * t234 * t208 / 0.8e1 - t238 * t240 / 0.32e2
  t244 = t227 * t243
  t247 = -0.5e1 / 0.32e2 * t199 * t103 - 0.3e1 / 0.32e2 * t202 * t209 + 0.3e1 / 0.256e3 * t213 * t216 * t221 + t224 * t244 / 0.32e2
  t251 = t61 * t108
  t255 = -0.7e1 / 0.4860e4 * t63 * t175 + t61 * t247 * t110 / 0.100e3 - t251 * t247 * t110 / 0.100e3
  t258 = -0.10e2 / 0.729e3 * t28 * t175 - t45 * t47 / t19 / t178 * t56 / 0.54e2 + 0.3e1 / 0.80e2 * t188 * t189 / t190 / r0 * t56 + 0.2e1 * t113 * t255
  t259 = t258 * t145
  t261 = -t247
  t262 = f.my_piecewise3(t122, 0, t261)
  t264 = t123 * t262
  t266 = t125 * t262
  t268 = t127 * t262
  t270 = t129 * t262
  t272 = t131 * t262
  t277 = params.d * params.c2
  t278 = t139 ** 2
  t279 = 0.1e1 / t278
  t280 = f.my_piecewise3(t122, t261, 0)
  t284 = f.my_piecewise3(t121, -0.667e0 * t262 - 0.8891110e0 * t264 - 0.1989259803147e1 * t266 + 0.5805188177960e1 * t268 - 0.4439990207985e1 * t270 + 0.1407173648874e1 * t272 - 0.162300903254e0 * t133 * t262, -t277 * t279 * t280 * t142)
  t287 = t172 * t259 - t120 * t284 + 0.1174e1 * t284
  t292 = 3 ** (0.1e1 / 0.6e1)
  t293 = t292 ** 2
  t294 = t293 ** 2
  t295 = t294 * t292
  t296 = t295 * t5
  t298 = t17 / t93
  t302 = 0.1e1 / t159 / t158
  t306 = t302 * t41 * t151 * t154 * t163
  t311 = t169 / t170 / t115
  t312 = t258 ** 2
  t317 = 0.1e1 / t20 / t48
  t318 = t31 * t317
  t321 = t48 * t93
  t335 = t185 * t40 * t187
  t336 = t46 ** 2
  t343 = t28 * t30 * t56
  t346 = t255 ** 2
  t350 = t68 * t93
  t355 = t212 * t48
  t359 = t199 * t77
  t362 = t69 * t75
  t363 = t208 ** 2
  t364 = t203 * t363
  t367 = t76 * t215
  t368 = t367 * t102
  t369 = t213 * t368
  t370 = t208 * t29
  t371 = t370 * t220
  t375 = t227 * t208 * t243
  t382 = f.my_piecewise3(t74, 0.40e2 / 0.9e1 * t70 * t174 - 0.11e2 / 0.9e1 * t318, 0)
  t383 = t203 * t382
  t386 = t67 * t92
  t387 = t386 * t49
  t389 = 0.1e1 / t214 / t87
  t390 = t77 * t389
  t392 = t102 * t30
  t393 = t79 * t78
  t395 = t393 * t23 * t43
  t396 = t392 * t395
  t399 = t216 * t226
  t400 = t213 * t399
  t401 = t29 * t80
  t402 = t83 * t243
  t403 = t401 * t402
  t407 = 0.1e1 / t79
  t409 = t407 * t41 * t26
  t410 = t218 * t409
  t414 = 0.1e1 / t225 / t101
  t415 = t90 * t414
  t416 = t243 ** 2
  t417 = t415 * t416
  t420 = t30 * t393
  t424 = t230 * t75
  t425 = t97 * t11
  t429 = t350 * t76
  t432 = t363 * t97
  t435 = t199 * t75
  t437 = t90 * t208 * t83
  t444 = t23 * t43
  t445 = t444 * t401
  t448 = 0.35e2 / 0.72e2 * t420 * t98 * t66 + 0.5e1 / 0.6e1 * t424 * t425 * t208 - 0.11e2 / 0.48e2 * t429 * t240 + t96 * t432 / 0.8e1 - t435 * t437 / 0.8e1 + t96 * t234 * t382 / 0.8e1 + 0.9e1 / 0.128e3 * t355 * t367 * t445
  t449 = t227 * t448
  t452 = -0.5e1 / 0.8e1 * t350 * t103 - 0.15e2 / 0.16e2 * t238 * t209 + 0.15e2 / 0.128e3 * t355 * t216 * t221 + 0.5e1 / 0.16e2 * t359 * t244 - 0.3e1 / 0.16e2 * t362 * t364 + 0.9e1 / 0.128e3 * t369 * t371 + 0.3e1 / 0.16e2 * t202 * t375 - 0.3e1 / 0.32e2 * t202 * t383 - 0.9e1 / 0.256e3 * t387 * t390 * t396 - 0.3e1 / 0.128e3 * t400 * t403 + t387 * t216 * t410 / 0.128e3 - t224 * t417 / 0.16e2 + t224 * t449 / 0.32e2
  t453 = t61 * t452
  t456 = t247 ** 2
  t465 = t61 * t108 * t106
  t469 = 0.77e2 / 0.14580e5 * t63 * t318 + t453 * t110 / 0.100e3 - 0.3e1 / 0.100e3 * t61 * t456 * t106 * t110 - t251 * t452 * t110 / 0.100e3 + t465 * t456 * t110 / 0.100e3
  t472 = 0.110e3 / 0.2187e4 * t28 * t318 + 0.19e2 / 0.162e3 * t45 * t47 / t19 / t321 * t56 - 0.43e2 / 0.80e2 * t188 * t189 / t190 / t32 * t56 + 0.27e2 / 0.800e3 * t335 * t336 / t20 / t190 / t48 * t343 + 0.2e1 * t346 + 0.2e1 * t113 * t469
  t478 = -t452
  t479 = f.my_piecewise3(t122, 0, t478)
  t481 = t262 ** 2
  t505 = -0.667e0 * t479 - 0.8891110e0 * t481 - 0.8891110e0 * t123 * t479 - 0.3978519606294e1 * t123 * t481 - 0.1989259803147e1 * t125 * t479 + 0.17415564533880e2 * t125 * t481 + 0.5805188177960e1 * t127 * t479 - 0.17759960831940e2 * t127 * t481 - 0.4439990207985e1 * t129 * t479 + 0.7035868244370e1 * t129 * t481 + 0.1407173648874e1 * t131 * t479 - 0.973805419524e0 * t131 * t481 - 0.162300903254e0 * t133 * t479
  t507 = 0.1e1 / t278 / t139
  t508 = t280 ** 2
  t513 = f.my_piecewise3(t122, t478, 0)
  t517 = params.c2 ** 2
  t518 = params.d * t517
  t519 = t278 ** 2
  t520 = 0.1e1 / t519
  t525 = f.my_piecewise3(t121, t505, -t277 * t279 * t513 * t142 - 0.2e1 * t277 * t507 * t508 * t142 - t518 * t520 * t508 * t142)
  t528 = -0.2e1 * t311 * t312 * t145 + t172 * t472 * t145 - 0.2e1 * t172 * t258 * t284 - t120 * t525 + 0.1174e1 * t525
  t534 = t17 / t32
  t541 = t17 / t19 / t48
  t550 = 0.1e1 / t159 / t36 * t23 * t27 * t31 * t163 / 0.6e1
  t553 = t4 ** 2
  t555 = t3 * t553 * jnp.pi
  t557 = t17 / t19
  t560 = 0.1e1 / t153
  t564 = t560 * t23 * t27 * t30 * t163
  t568 = f.my_piecewise3(t2, 0, t18 * t22 * t148 * t164 / 0.12e2 - t18 * t168 * t287 * t164 / 0.4e1 + 0.41232500000000000000000000000000000000000000000000e1 * t296 * t298 * t148 * t306 - 0.3e1 / 0.8e1 * t18 * t19 * t528 * t164 - 0.49479000000000000000000000000000000000000000000000e1 * t296 * t534 * t287 * t306 - 0.29687400000000000000000000000000000000000000000000e2 * t296 * t541 * t148 * t550 + 0.40802857350000000000000000000000000000000000000000e1 * t555 * t557 * t148 * t564)
  t570 = t34 * t148
  t578 = 0.1e1 / t48
  t598 = t17 * t156 * t148
  t602 = t170 ** 2
  t617 = t31 / t20 / t49
  t639 = t185 ** 2
  t642 = t190 ** 2
  t666 = t75 * t215
  t695 = t29 * t407
  t705 = t68 * t32
  t713 = t67 ** 2
  t714 = t713 * t49
  t728 = t386 * t48
  t732 = t212 * t93
  t739 = -0.9e1 / 0.256e3 * t400 * t401 * t83 * t448 + 0.135e3 / 0.128e3 * t355 * t368 * t371 - 0.45e2 / 0.128e3 * t355 * t399 * t403 + 0.27e2 / 0.128e3 * t213 * t666 * t102 * t363 * t29 * t220 + 0.27e2 / 0.256e3 * t369 * t382 * t29 * t220 - 0.81e2 / 0.256e3 * t387 * t76 * t389 * t102 * t208 * t30 * t395 + 0.9e1 / 0.128e3 * t387 * t368 * t370 * t409 + 0.9e1 / 0.128e3 * t213 * t216 * t414 * t401 * t83 * t416 - 0.3e1 / 0.128e3 * t387 * t399 * t695 * t402 + 0.27e2 / 0.256e3 * t387 * t390 * t226 * t420 * t444 * t243 - 0.15e2 / 0.8e1 * t705 * t103 - 0.3e1 / 0.16e2 * t69 * t363 * t208 * t90 * t102 - 0.9e1 / 0.128e3 * t714 * t390 * t392 * t79 * t23 * t43 - t714 * t216 * t218 / t393 * t41 * t26 / 0.384e3 + 0.15e2 / 0.128e3 * t728 * t216 * t410 + 0.45e2 / 0.64e2 * t732 * t216 * t221 - 0.135e3 / 0.256e3 * t728 * t390 * t396
  t770 = f.my_piecewise3(t74, -0.440e3 / 0.27e2 * t70 * t317 + 0.154e3 / 0.27e2 * t617, 0)
  t837 = 0.51e2 / 0.64e2 * t732 * t367 * t445 + 0.27e2 / 0.64e2 * t355 * t666 * t208 * t23 * t43 * t29 * t80 + 0.3e1 / 0.64e2 * t728 * t367 * t444 * t695 + 0.3e1 / 0.8e1 * t96 * t208 * t97 * t382 + t96 * t234 * t770 / 0.8e1 - 0.27e2 / 0.128e3 * t728 * t76 * t389 * t186 * t420 - 0.11e2 / 0.8e1 * t350 * t75 * t437 - 0.3e1 / 0.16e2 * t435 * t90 * t382 * t83 + 0.35e2 / 0.54e2 * t30 * t79 * t98 * t92 + 0.35e2 / 0.12e2 * t420 * t75 * t97 * t66 * t208 - 0.67e2 / 0.72e2 * t705 * t76 * t240 + 0.5e1 / 0.4e1 * t230 * t432 * t11 + 0.5e1 / 0.4e1 * t424 * t425 * t382 - 0.3e1 / 0.16e2 * t199 * t363 * t240
  t845 = t225 ** 2
  t867 = 0.45e2 / 0.16e2 * t238 * t375 + 0.9e1 / 0.16e2 * t362 * t227 * t363 * t243 - 0.9e1 / 0.16e2 * t362 * t203 * t208 * t382 - 0.9e1 / 0.16e2 * t202 * t415 * t208 * t416 + 0.9e1 / 0.32e2 * t202 * t227 * t382 * t243 + 0.9e1 / 0.32e2 * t202 * t227 * t208 * t448 - 0.3e1 / 0.16e2 * t224 * t415 * t243 * t448 - 0.3e1 / 0.32e2 * t202 * t203 * t770 + 0.135e3 / 0.512e3 * t713 * t66 * t321 * t77 / t214 / t88 * t102 * t186 + t224 * t227 * t837 / 0.32e2 - 0.45e2 / 0.16e2 * t435 * t364 - 0.15e2 / 0.16e2 * t359 * t417 + 0.3e1 / 0.16e2 * t224 * t90 / t845 * t416 * t243 - 0.45e2 / 0.8e1 * t429 * t209 + 0.15e2 / 0.8e1 * t350 * t77 * t244 - 0.45e2 / 0.32e2 * t238 * t383 + 0.15e2 / 0.32e2 * t359 * t449 - 0.27e2 / 0.128e3 * t213 * t367 * t226 * t370 * t80 * t402
  t868 = t739 + t867
  t876 = t456 * t247
  t877 = t61 * t876
  t890 = t108 ** 2
  t907 = -t868
  t908 = f.my_piecewise3(t122, 0, t907)
  t914 = t481 * t262
  t944 = -0.667e0 * t908 - 0.26673330e1 * t262 * t479 - 0.8891110e0 * t123 * t908 - 0.3978519606294e1 * t914 - 0.11935558818882e2 * t264 * t479 - 0.1989259803147e1 * t125 * t908 + 0.34831129067760e2 * t123 * t914 + 0.52246693601640e2 * t266 * t479 + 0.5805188177960e1 * t127 * t908 - 0.53279882495820e2 * t125 * t914 - 0.53279882495820e2 * t268 * t479 - 0.4439990207985e1 * t129 * t908 + 0.28143472977480e2 * t127 * t914 + 0.21107604733110e2 * t270 * t479 + 0.1407173648874e1 * t131 * t908 - 0.4869027097620e1 * t129 * t914 - 0.2921416258572e1 * t272 * t479 - 0.162300903254e0 * t133 * t908
  t945 = t508 * t280
  t952 = t280 * t142 * t513
  t961 = f.my_piecewise3(t122, t907, 0)
  t976 = f.my_piecewise3(t121, t944, -0.6e1 * t277 * t520 * t945 * t142 - 0.6e1 * t277 * t507 * t952 - 0.6e1 * t518 / t519 / t139 * t945 * t142 - t277 * t279 * t961 * t142 - 0.3e1 * t518 * t520 * t952 - params.d * t517 * params.c2 / t519 / t278 * t945 * t142)
  t997 = 0.1e1 / t4 / t24
  t1004 = t153 * s0
  t1027 = -0.5e1 / 0.36e2 * t18 * t570 * t164 + t18 * t22 * t287 * t164 / 0.4e1 - 0.11819983333333333333333333333333333333333333333333e2 * t296 * t17 * t578 * t148 * t306 - 0.3e1 / 0.8e1 * t18 * t168 * t528 * t164 + 0.12369750000000000000000000000000000000000000000000e2 * t296 * t298 * t287 * t306 + 0.17812440000000000000000000000000000000000000000000e3 * t296 * t17 * t51 * t148 * t550 - 0.81605714700000000000000000000000000000000000000000e1 * t555 * t598 * t564 - 0.3e1 / 0.8e1 * t18 * t19 * (0.6e1 * t169 / t602 * t312 * t258 * t145 - 0.6e1 * t311 * t259 * t472 + 0.6e1 * t311 * t312 * t284 + t172 * (-0.1540e4 / 0.6561e4 * t28 * t617 - 0.209e3 / 0.243e3 * t45 * t47 / t19 / t190 * t56 + 0.797e3 / 0.120e3 * t188 * t189 / t190 / t93 * t56 - 0.729e3 / 0.800e3 * t335 * t336 / t20 / t190 / t49 * t343 + 0.243e3 / 0.4000e4 * t639 * t187 * t336 * s0 / t19 / t642 * t41 * t44 * t29 * t56 + 0.6e1 * t255 * t469 + 0.2e1 * t113 * (-0.539e3 / 0.21870e5 * t63 * t617 + t61 * t868 * t110 / 0.100e3 - 0.9e1 / 0.100e3 * t453 * t106 * t247 * t110 - 0.3e1 / 0.100e3 * t877 * t110 + 0.3e1 / 0.50e2 * t877 * t108 * t110 - t251 * t868 * t110 / 0.100e3 + 0.3e1 / 0.100e3 * t465 * t452 * t247 * t110 - t61 * t890 * t876 * t110 / 0.100e3)) * t145 - 0.3e1 * t172 * t472 * t284 - 0.3e1 * t172 * t258 * t525 - t120 * t976 + 0.1174e1 * t976) * t164 - 0.74218500000000000000000000000000000000000000000000e1 * t296 * t534 * t528 * t306 - 0.89062200000000000000000000000000000000000000000000e2 * t296 * t541 * t287 * t550 + 0.12240857205000000000000000000000000000000000000000e2 * t555 * t557 * t287 * t564 - 0.16493000000000000000000000000000000000000000000000e2 * t295 * t997 * t17 / t20 / t178 * t148 / t159 * t24 / t578 * t163 + 0.81605714699999999999999999999999999999999999999999e1 * t3 * t997 * t598 * t444 * t560 * t30 * t163 - 0.32302153261130400000000000000000000000000000000000e3 * t296 * t17 * t570 * t302 * t163
  t1028 = f.my_piecewise3(t2, 0, t1027)
  v3rho3_0_ = 0.2e1 * r0 * t1028 + 0.6e1 * t568

  res = {'v3rho3': v3rho3_0_}
  return res
