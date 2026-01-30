"""Generated from gga_x_hjs_b88_v2.mpl."""

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

  hjs_AA = 0.757211

  hjs_BB = -0.106364

  hjs_CC = -0.118649

  hjs_DD = 0.60965

  hjs_fH = lambda s: jnp.sum(jnp.array([params_a[i] * s ** (1 + i) for i in range(1, 6 + 1)]), axis=0) / (1 + jnp.sum(jnp.array([params_b[i] * s ** i for i in range(1, 9 + 1)]), axis=0))

  hjs2_xi = 1 / (jnp.exp(20) - 1)

  hjs_zeta = lambda s: jnp.maximum(s ** 2 * hjs_fH(s), 1e-10)

  hjs2_fs = lambda s: -jnp.log((jnp.exp(-s) + hjs2_xi) / (1 + hjs2_xi))

  hjs_eta = lambda s: jnp.maximum(hjs_AA + hjs_zeta(s), 1e-10)

  hjs_lambda = lambda s: hjs_DD + hjs_zeta(s)

  hjs_fF = lambda rs, z, s: 1 - s ** 2 / (27 * hjs_CC * (1 + s ** 2 / 4)) - hjs_zeta(s) / (2 * hjs_CC)

  hjs_chi = lambda rs, z, s: f.nu(rs, z) / jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)

  hjs_fG = lambda rs, z, s: -2 / 5 * hjs_CC * hjs_fF(rs, z, s) * hjs_lambda(s) - 4 / 15 * hjs_BB * hjs_lambda(s) ** 2 - 6 / 5 * hjs_AA * hjs_lambda(s) ** 3 - hjs_lambda(s) ** (7 / 2) * (4 / 5 * jnp.sqrt(jnp.pi) + 12 / 5 * (jnp.sqrt(hjs_zeta(s)) - jnp.sqrt(hjs_eta(s))))

  hjs_f1 = lambda rs, z, s: +hjs_AA - 4 / 9 * hjs_BB * (1 - hjs_chi(rs, z, s)) / hjs_lambda(s) - 2 / 9 * hjs_CC * hjs_fF(rs, z, s) * (2 - 3 * hjs_chi(rs, z, s) + hjs_chi(rs, z, s) ** 3) / hjs_lambda(s) ** 2 - 1 / 9 * hjs_fG(rs, z, s) * (8 - 15 * hjs_chi(rs, z, s) + 10 * hjs_chi(rs, z, s) ** 3 - 3 * hjs_chi(rs, z, s) ** 5) / hjs_lambda(s) ** 3 + 2 * f.nu(rs, z) * (jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2) - jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) + 2 * hjs_zeta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2))) - 2 * hjs_eta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)))

  hjs_fx = lambda rs, z, x: hjs_f1(rs, z, hjs2_fs(X2S * x))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, hjs_fx, rs, z, xs0, xs1)

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

  hjs_AA = 0.757211

  hjs_BB = -0.106364

  hjs_CC = -0.118649

  hjs_DD = 0.60965

  hjs_fH = lambda s: jnp.sum(jnp.array([params_a[i] * s ** (1 + i) for i in range(1, 6 + 1)]), axis=0) / (1 + jnp.sum(jnp.array([params_b[i] * s ** i for i in range(1, 9 + 1)]), axis=0))

  hjs2_xi = 1 / (jnp.exp(20) - 1)

  hjs_zeta = lambda s: jnp.maximum(s ** 2 * hjs_fH(s), 1e-10)

  hjs2_fs = lambda s: -jnp.log((jnp.exp(-s) + hjs2_xi) / (1 + hjs2_xi))

  hjs_eta = lambda s: jnp.maximum(hjs_AA + hjs_zeta(s), 1e-10)

  hjs_lambda = lambda s: hjs_DD + hjs_zeta(s)

  hjs_fF = lambda rs, z, s: 1 - s ** 2 / (27 * hjs_CC * (1 + s ** 2 / 4)) - hjs_zeta(s) / (2 * hjs_CC)

  hjs_chi = lambda rs, z, s: f.nu(rs, z) / jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)

  hjs_fG = lambda rs, z, s: -2 / 5 * hjs_CC * hjs_fF(rs, z, s) * hjs_lambda(s) - 4 / 15 * hjs_BB * hjs_lambda(s) ** 2 - 6 / 5 * hjs_AA * hjs_lambda(s) ** 3 - hjs_lambda(s) ** (7 / 2) * (4 / 5 * jnp.sqrt(jnp.pi) + 12 / 5 * (jnp.sqrt(hjs_zeta(s)) - jnp.sqrt(hjs_eta(s))))

  hjs_f1 = lambda rs, z, s: +hjs_AA - 4 / 9 * hjs_BB * (1 - hjs_chi(rs, z, s)) / hjs_lambda(s) - 2 / 9 * hjs_CC * hjs_fF(rs, z, s) * (2 - 3 * hjs_chi(rs, z, s) + hjs_chi(rs, z, s) ** 3) / hjs_lambda(s) ** 2 - 1 / 9 * hjs_fG(rs, z, s) * (8 - 15 * hjs_chi(rs, z, s) + 10 * hjs_chi(rs, z, s) ** 3 - 3 * hjs_chi(rs, z, s) ** 5) / hjs_lambda(s) ** 3 + 2 * f.nu(rs, z) * (jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2) - jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) + 2 * hjs_zeta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2))) - 2 * hjs_eta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)))

  hjs_fx = lambda rs, z, x: hjs_f1(rs, z, hjs2_fs(X2S * x))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, hjs_fx, rs, z, xs0, xs1)

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

  hjs_AA = 0.757211

  hjs_BB = -0.106364

  hjs_CC = -0.118649

  hjs_DD = 0.60965

  hjs_fH = lambda s: jnp.sum(jnp.array([params_a[i] * s ** (1 + i) for i in range(1, 6 + 1)]), axis=0) / (1 + jnp.sum(jnp.array([params_b[i] * s ** i for i in range(1, 9 + 1)]), axis=0))

  hjs2_xi = 1 / (jnp.exp(20) - 1)

  hjs_zeta = lambda s: jnp.maximum(s ** 2 * hjs_fH(s), 1e-10)

  hjs2_fs = lambda s: -jnp.log((jnp.exp(-s) + hjs2_xi) / (1 + hjs2_xi))

  hjs_eta = lambda s: jnp.maximum(hjs_AA + hjs_zeta(s), 1e-10)

  hjs_lambda = lambda s: hjs_DD + hjs_zeta(s)

  hjs_fF = lambda rs, z, s: 1 - s ** 2 / (27 * hjs_CC * (1 + s ** 2 / 4)) - hjs_zeta(s) / (2 * hjs_CC)

  hjs_chi = lambda rs, z, s: f.nu(rs, z) / jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)

  hjs_fG = lambda rs, z, s: -2 / 5 * hjs_CC * hjs_fF(rs, z, s) * hjs_lambda(s) - 4 / 15 * hjs_BB * hjs_lambda(s) ** 2 - 6 / 5 * hjs_AA * hjs_lambda(s) ** 3 - hjs_lambda(s) ** (7 / 2) * (4 / 5 * jnp.sqrt(jnp.pi) + 12 / 5 * (jnp.sqrt(hjs_zeta(s)) - jnp.sqrt(hjs_eta(s))))

  hjs_f1 = lambda rs, z, s: +hjs_AA - 4 / 9 * hjs_BB * (1 - hjs_chi(rs, z, s)) / hjs_lambda(s) - 2 / 9 * hjs_CC * hjs_fF(rs, z, s) * (2 - 3 * hjs_chi(rs, z, s) + hjs_chi(rs, z, s) ** 3) / hjs_lambda(s) ** 2 - 1 / 9 * hjs_fG(rs, z, s) * (8 - 15 * hjs_chi(rs, z, s) + 10 * hjs_chi(rs, z, s) ** 3 - 3 * hjs_chi(rs, z, s) ** 5) / hjs_lambda(s) ** 3 + 2 * f.nu(rs, z) * (jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2) - jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) + 2 * hjs_zeta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2))) - 2 * hjs_eta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)))

  hjs_fx = lambda rs, z, x: hjs_f1(rs, z, hjs2_fs(X2S * x))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, hjs_fx, rs, z, xs0, xs1)

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
  t28 = t2 ** 2
  t29 = f.p.cam_omega * t28
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = t29 * t32
  t35 = 0.1e1 + t17 <= f.p.zeta_threshold
  t37 = 0.1e1 - t17 <= f.p.zeta_threshold
  t38 = f.my_piecewise5(t35, t11, t37, t15, t17)
  t39 = 0.1e1 + t38
  t40 = t39 <= f.p.zeta_threshold
  t41 = t39 ** (0.1e1 / 0.3e1)
  t42 = f.my_piecewise3(t40, t21, t41)
  t43 = 0.1e1 / t42
  t44 = 0.1e1 / t26
  t45 = t43 * t44
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = t47 * t32
  t49 = jnp.sqrt(s0)
  t50 = r0 ** (0.1e1 / 0.3e1)
  t52 = 0.1e1 / t50 / r0
  t56 = jnp.exp(-t48 * t49 * t52 / 0.12e2)
  t57 = jnp.exp(20)
  t59 = 0.1e1 / (t57 - 0.1e1)
  t60 = t56 + t59
  t62 = 0.1e1 / (0.1e1 + t59)
  t64 = jnp.log(t60 * t62)
  t65 = t64 ** 2
  t66 = params.a[0]
  t68 = params.a[1]
  t69 = t65 * t64
  t71 = params.a[2]
  t72 = t65 ** 2
  t74 = params.a[3]
  t75 = t72 * t64
  t77 = params.a[4]
  t78 = t72 * t65
  t80 = params.a[5]
  t81 = t72 * t69
  t83 = t66 * t65 - t68 * t69 + t71 * t72 - t74 * t75 + t77 * t78 - t80 * t81
  t84 = t65 * t83
  t85 = params.b[0]
  t87 = params.b[1]
  t89 = params.b[2]
  t91 = params.b[3]
  t93 = params.b[4]
  t95 = params.b[5]
  t97 = params.b[6]
  t99 = params.b[7]
  t100 = t72 ** 2
  t102 = params.b[8]
  t105 = -t102 * t100 * t64 + t99 * t100 - t85 * t64 + t87 * t65 - t89 * t69 + t91 * t72 - t93 * t75 + t95 * t78 - t97 * t81 + 0.1e1
  t106 = 0.1e1 / t105
  t107 = t84 * t106
  t108 = 0.1e-9 < t107
  t109 = f.my_piecewise3(t108, t107, 0.1e-9)
  t110 = f.p.cam_omega ** 2
  t111 = t110 * t2
  t112 = t31 ** 2
  t113 = 0.1e1 / t112
  t114 = t42 ** 2
  t115 = 0.1e1 / t114
  t116 = t113 * t115
  t117 = t26 ** 2
  t118 = 0.1e1 / t117
  t120 = t111 * t116 * t118
  t122 = 0.609650e0 + t109 + t120 / 0.3e1
  t123 = jnp.sqrt(t122)
  t124 = 0.1e1 / t123
  t126 = t33 * t45 * t124
  t128 = -0.47272888888888888888888888888888888888888888888889e-1 + 0.15757629629629629629629629629629629629629629629630e-1 * t126
  t129 = 0.609650e0 + t109
  t130 = 0.1e1 / t129
  t133 = -0.3203523e1 - 0.80088075000000000000000000000000000000000000000000e0 * t65
  t134 = 0.1e1 / t133
  t135 = t65 * t134
  t138 = -0.26366444444444444444444444444444444444444444444444e-1 + 0.26366444444444444444444444444444444444444444444444e-1 * t135 - 0.11111111111111111111111111111111111111111111111111e0 * t109
  t141 = t110 * f.p.cam_omega / t30
  t143 = 0.1e1 / t114 / t42
  t146 = 0.1e1 / t123 / t122
  t148 = t141 * t143 * t7 * t146
  t150 = 0.2e1 - t126 + t148 / 0.3e1
  t151 = t138 * t150
  t152 = t129 ** 2
  t153 = 0.1e1 / t152
  t157 = -0.47459600000000000000000000000000000000000000000000e-1 + 0.47459600000000000000000000000000000000000000000000e-1 * t135 - 0.20000000000000000000000000000000000000000000000000e0 * t109
  t161 = t152 * t129
  t163 = jnp.sqrt(t129)
  t164 = t163 * t161
  t165 = jnp.sqrt(jnp.pi)
  t166 = 0.4e1 / 0.5e1 * t165
  t167 = jnp.sqrt(t109)
  t170 = 0.0e0 < 0.7572109999e0 + t109
  t172 = f.my_piecewise3(t170, 0.757211e0 + t109, 0.1e-9)
  t173 = jnp.sqrt(t172)
  t175 = t166 + 0.12e2 / 0.5e1 * t167 - 0.12e2 / 0.5e1 * t173
  t178 = -t157 * t129 / 0.9e1 + 0.31515259259259259259259259259259259259259259259259e-2 * t152 - 0.10096146666666666666666666666666666666666666666667e0 * t161 - t164 * t175 / 0.9e1
  t181 = t110 ** 2
  t186 = t181 * f.p.cam_omega * t2 / t112 / t30
  t187 = t114 ** 2
  t189 = 0.1e1 / t187 / t42
  t191 = 0.1e1 / t117 / t6
  t192 = t189 * t191
  t193 = t122 ** 2
  t195 = 0.1e1 / t123 / t193
  t199 = 0.8e1 - 0.5e1 * t126 + 0.10e2 / 0.3e1 * t148 - t186 * t192 * t195 / 0.3e1
  t200 = t178 * t199
  t201 = 0.1e1 / t161
  t204 = 0.3e1 * t120
  t206 = jnp.sqrt(0.9e1 * t109 + t204)
  t209 = jnp.sqrt(0.9e1 * t172 + t204)
  t211 = t206 / 0.3e1 - t209 / 0.3e1
  t215 = t32 * t43
  t217 = t29 * t215 * t44
  t219 = t217 / 0.3e1 + t206 / 0.3e1
  t221 = t217 / 0.3e1 + t123
  t222 = 0.1e1 / t221
  t224 = jnp.log(t219 * t222)
  t228 = t217 / 0.3e1 + t209 / 0.3e1
  t230 = jnp.log(t228 * t222)
  t233 = 0.757211e0 - t128 * t130 - t151 * t153 - t200 * t201 + 0.2e1 / 0.3e1 * t33 * t45 * t211 + 0.2e1 * t109 * t224 - 0.2e1 * t172 * t230
  t237 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t233)
  t238 = r1 <= f.p.dens_threshold
  t239 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t240 = 0.1e1 + t239
  t241 = t240 <= f.p.zeta_threshold
  t242 = t240 ** (0.1e1 / 0.3e1)
  t244 = f.my_piecewise3(t241, t22, t242 * t240)
  t245 = t244 * t26
  t246 = f.my_piecewise5(t37, t11, t35, t15, -t17)
  t247 = 0.1e1 + t246
  t248 = t247 <= f.p.zeta_threshold
  t249 = t247 ** (0.1e1 / 0.3e1)
  t250 = f.my_piecewise3(t248, t21, t249)
  t251 = 0.1e1 / t250
  t252 = t251 * t44
  t253 = jnp.sqrt(s2)
  t254 = r1 ** (0.1e1 / 0.3e1)
  t256 = 0.1e1 / t254 / r1
  t260 = jnp.exp(-t48 * t253 * t256 / 0.12e2)
  t261 = t260 + t59
  t263 = jnp.log(t261 * t62)
  t264 = t263 ** 2
  t266 = t264 * t263
  t268 = t264 ** 2
  t270 = t268 * t263
  t272 = t268 * t264
  t274 = t268 * t266
  t276 = t66 * t264 - t68 * t266 + t71 * t268 - t74 * t270 + t77 * t272 - t80 * t274
  t277 = t264 * t276
  t285 = t268 ** 2
  t289 = -t102 * t285 * t263 - t85 * t263 + t87 * t264 - t89 * t266 + t91 * t268 - t93 * t270 + t95 * t272 - t97 * t274 + t99 * t285 + 0.1e1
  t290 = 0.1e1 / t289
  t291 = t277 * t290
  t292 = 0.1e-9 < t291
  t293 = f.my_piecewise3(t292, t291, 0.1e-9)
  t294 = t250 ** 2
  t295 = 0.1e1 / t294
  t296 = t113 * t295
  t298 = t111 * t296 * t118
  t300 = 0.609650e0 + t293 + t298 / 0.3e1
  t301 = jnp.sqrt(t300)
  t302 = 0.1e1 / t301
  t304 = t33 * t252 * t302
  t306 = -0.47272888888888888888888888888888888888888888888889e-1 + 0.15757629629629629629629629629629629629629629629630e-1 * t304
  t307 = 0.609650e0 + t293
  t308 = 0.1e1 / t307
  t311 = -0.3203523e1 - 0.80088075000000000000000000000000000000000000000000e0 * t264
  t312 = 0.1e1 / t311
  t313 = t264 * t312
  t316 = -0.26366444444444444444444444444444444444444444444444e-1 + 0.26366444444444444444444444444444444444444444444444e-1 * t313 - 0.11111111111111111111111111111111111111111111111111e0 * t293
  t318 = 0.1e1 / t294 / t250
  t321 = 0.1e1 / t301 / t300
  t323 = t141 * t318 * t7 * t321
  t325 = 0.2e1 - t304 + t323 / 0.3e1
  t326 = t316 * t325
  t327 = t307 ** 2
  t328 = 0.1e1 / t327
  t332 = -0.47459600000000000000000000000000000000000000000000e-1 + 0.47459600000000000000000000000000000000000000000000e-1 * t313 - 0.20000000000000000000000000000000000000000000000000e0 * t293
  t336 = t327 * t307
  t338 = jnp.sqrt(t307)
  t339 = t338 * t336
  t340 = jnp.sqrt(t293)
  t343 = 0.0e0 < 0.7572109999e0 + t293
  t345 = f.my_piecewise3(t343, 0.757211e0 + t293, 0.1e-9)
  t346 = jnp.sqrt(t345)
  t348 = t166 + 0.12e2 / 0.5e1 * t340 - 0.12e2 / 0.5e1 * t346
  t351 = -t332 * t307 / 0.9e1 + 0.31515259259259259259259259259259259259259259259259e-2 * t327 - 0.10096146666666666666666666666666666666666666666667e0 * t336 - t339 * t348 / 0.9e1
  t354 = t294 ** 2
  t356 = 0.1e1 / t354 / t250
  t357 = t356 * t191
  t358 = t300 ** 2
  t360 = 0.1e1 / t301 / t358
  t364 = 0.8e1 - 0.5e1 * t304 + 0.10e2 / 0.3e1 * t323 - t186 * t357 * t360 / 0.3e1
  t365 = t351 * t364
  t366 = 0.1e1 / t336
  t369 = 0.3e1 * t298
  t371 = jnp.sqrt(0.9e1 * t293 + t369)
  t374 = jnp.sqrt(0.9e1 * t345 + t369)
  t376 = t371 / 0.3e1 - t374 / 0.3e1
  t380 = t32 * t251
  t382 = t29 * t380 * t44
  t384 = t382 / 0.3e1 + t371 / 0.3e1
  t386 = t382 / 0.3e1 + t301
  t387 = 0.1e1 / t386
  t389 = jnp.log(t384 * t387)
  t393 = t382 / 0.3e1 + t374 / 0.3e1
  t395 = jnp.log(t393 * t387)
  t398 = 0.757211e0 - t306 * t308 - t326 * t328 - t365 * t366 + 0.2e1 / 0.3e1 * t33 * t252 * t376 + 0.2e1 * t293 * t389 - 0.2e1 * t345 * t395
  t402 = f.my_piecewise3(t238, 0, -0.3e1 / 0.8e1 * t5 * t245 * t398)
  t403 = t6 ** 2
  t404 = 0.1e1 / t403
  t405 = t16 * t404
  t406 = t7 - t405
  t407 = f.my_piecewise5(t10, 0, t14, 0, t406)
  t410 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t407)
  t418 = t5 * t25 * t118 * t233 / 0.8e1
  t419 = t115 * t44
  t420 = t41 ** 2
  t421 = 0.1e1 / t420
  t422 = f.my_piecewise5(t35, 0, t37, 0, t406)
  t425 = f.my_piecewise3(t40, 0, t421 * t422 / 0.3e1)
  t428 = t33 * t419 * t124 * t425
  t431 = 0.1e1 / t26 / t6
  t432 = t43 * t431
  t434 = t33 * t432 * t124
  t435 = 0.52525432098765432098765432098765432098765432098767e-2 * t434
  t438 = t64 * t83 * t106 * t47
  t440 = r0 ** 2
  t442 = 0.1e1 / t50 / t440
  t444 = 0.1e1 / t60
  t450 = t66 * t64 * t48
  t452 = t56 * t444
  t453 = t49 * t442 * t452
  t457 = t68 * t65 * t48
  t461 = t71 * t69 * t48
  t465 = t74 * t72 * t48
  t469 = t77 * t75 * t48
  t473 = t80 * t78 * t48
  t479 = t105 ** 2
  t480 = 0.1e1 / t479
  t482 = t85 * t47 * t32
  t486 = t87 * t64 * t48
  t490 = t89 * t65 * t48
  t494 = t91 * t69 * t48
  t498 = t93 * t72 * t48
  t502 = t95 * t75 * t48
  t506 = t97 * t78 * t48
  t510 = t99 * t81 * t48
  t514 = t102 * t100 * t48
  t520 = f.my_piecewise3(t108, 0.2e1 / 0.9e1 * t438 * t32 * t49 * t442 * t56 * t444 + t65 * (0.2e1 / 0.9e1 * t450 * t453 - t457 * t453 / 0.3e1 + 0.4e1 / 0.9e1 * t461 * t453 - 0.5e1 / 0.9e1 * t465 * t453 + 0.2e1 / 0.3e1 * t469 * t453 - 0.7e1 / 0.9e1 * t473 * t453) * t106 - t84 * t480 * (-t482 * t453 / 0.9e1 + 0.2e1 / 0.9e1 * t486 * t453 - t490 * t453 / 0.3e1 + 0.4e1 / 0.9e1 * t494 * t453 - 0.5e1 / 0.9e1 * t498 * t453 + 0.2e1 / 0.3e1 * t502 * t453 - 0.7e1 / 0.9e1 * t506 * t453 + 0.8e1 / 0.9e1 * t510 * t453 - t514 * t453), 0)
  t521 = t111 * t113
  t522 = t143 * t118
  t524 = t521 * t522 * t425
  t527 = t111 * t116 * t191
  t528 = 0.2e1 / 0.9e1 * t527
  t529 = t520 - 0.2e1 / 0.3e1 * t524 - t528
  t532 = t33 * t45 * t146 * t529
  t536 = t128 * t153
  t539 = t64 * t134 * t48
  t540 = t539 * t453
  t542 = t133 ** 2
  t545 = t69 / t542 * t48
  t546 = t545 * t453
  t552 = t434 / 0.3e1
  t555 = t141 / t187
  t556 = t7 * t146
  t558 = t555 * t556 * t425
  t561 = t141 * t143 * t404 * t146
  t562 = t561 / 0.3e1
  t563 = t141 * t143
  t564 = t7 * t195
  t566 = t563 * t564 * t529
  t587 = t163 * t152 * t175
  t590 = 0.1e1 / t167
  t592 = 0.1e1 / t173
  t593 = f.my_piecewise3(t170, t520, 0)
  t603 = 0.5e1 / 0.3e1 * t434
  t606 = 0.10e2 / 0.3e1 * t561
  t610 = 0.1e1 / t187 / t114 * t191
  t616 = 0.1e1 / t117 / t403
  t620 = 0.5e1 / 0.9e1 * t186 * t189 * t616 * t195
  t623 = 0.1e1 / t123 / t193 / t122
  t631 = t152 ** 2
  t632 = 0.1e1 / t631
  t642 = 0.2e1 / 0.9e1 * t33 * t432 * t211
  t643 = 0.1e1 / t206
  t645 = 0.6e1 * t524
  t646 = 0.2e1 * t527
  t648 = t643 * (0.9e1 * t520 - t645 - t646)
  t649 = 0.1e1 / t209
  t652 = t649 * (0.9e1 * t593 - t645 - t646)
  t662 = t33 * t419 * t425 / 0.3e1
  t665 = t29 * t215 * t431 / 0.9e1
  t669 = t221 ** 2
  t670 = 0.1e1 / t669
  t671 = t219 * t670
  t674 = -t662 - t665 + t124 * t529 / 0.2e1
  t679 = 0.1e1 / t219 * t221
  t687 = t228 * t670
  t692 = 0.1e1 / t228 * t221
  t695 = -(-0.15757629629629629629629629629629629629629629629630e-1 * t428 - t435 - 0.78788148148148148148148148148148148148148148148150e-2 * t532) * t130 + t536 * t520 - (0.58592098765432098765432098765432098765432098765431e-2 * t540 + 0.46925284003333333333333333333333333333333333333333e-2 * t546 - 0.11111111111111111111111111111111111111111111111111e0 * t520) * t150 * t153 - t138 * (t428 + t552 + t532 / 0.2e1 - t558 - t562 - t566 / 0.2e1) * t153 + 0.2e1 * t151 * t201 * t520 - (-(0.10546577777777777777777777777777777777777777777778e-1 * t540 + 0.84465511206000000000000000000000000000000000000000e-2 * t546 - 0.20000000000000000000000000000000000000000000000000e0 * t520) * t129 / 0.9e1 - t157 * t520 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t129 * t520 - 0.30288440000000000000000000000000000000000000000001e0 * t152 * t520 - 0.7e1 / 0.18e2 * t587 * t520 - t164 * (0.6e1 / 0.5e1 * t590 * t520 - 0.6e1 / 0.5e1 * t592 * t593) / 0.9e1) * t199 * t201 - t178 * (0.5e1 * t428 + t603 + 0.5e1 / 0.2e1 * t532 - 0.10e2 * t558 - t606 - 0.5e1 * t566 + 0.5e1 / 0.3e1 * t186 * t610 * t195 * t425 + t620 + 0.5e1 / 0.6e1 * t186 * t192 * t623 * t529) * t201 + 0.3e1 * t200 * t632 * t520 - 0.2e1 / 0.3e1 * t33 * t419 * t211 * t425 - t642 + 0.2e1 / 0.3e1 * t33 * t45 * (t648 / 0.6e1 - t652 / 0.6e1) + 0.2e1 * t520 * t224 + 0.2e1 * t109 * ((-t662 - t665 + t648 / 0.6e1) * t222 - t671 * t674) * t679 - 0.2e1 * t593 * t230 - 0.2e1 * t172 * ((-t662 - t665 + t652 / 0.6e1) * t222 - t687 * t674) * t692
  t700 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t410 * t26 * t233 - t418 - 0.3e1 / 0.8e1 * t5 * t27 * t695)
  t701 = -t406
  t702 = f.my_piecewise5(t14, 0, t10, 0, t701)
  t705 = f.my_piecewise3(t241, 0, 0.4e1 / 0.3e1 * t242 * t702)
  t713 = t5 * t244 * t118 * t398 / 0.8e1
  t714 = t295 * t44
  t715 = t249 ** 2
  t716 = 0.1e1 / t715
  t717 = f.my_piecewise5(t37, 0, t35, 0, t701)
  t720 = f.my_piecewise3(t248, 0, t716 * t717 / 0.3e1)
  t723 = t33 * t714 * t302 * t720
  t725 = t251 * t431
  t727 = t33 * t725 * t302
  t728 = 0.52525432098765432098765432098765432098765432098767e-2 * t727
  t729 = t318 * t118
  t731 = t521 * t729 * t720
  t734 = t111 * t296 * t191
  t735 = 0.2e1 / 0.9e1 * t734
  t736 = -0.2e1 / 0.3e1 * t731 - t735
  t739 = t33 * t252 * t321 * t736
  t743 = t727 / 0.3e1
  t746 = t141 / t354
  t747 = t7 * t321
  t749 = t746 * t747 * t720
  t752 = t141 * t318 * t404 * t321
  t753 = t752 / 0.3e1
  t754 = t141 * t318
  t755 = t7 * t360
  t757 = t754 * t755 * t736
  t763 = 0.5e1 / 0.3e1 * t727
  t766 = 0.10e2 / 0.3e1 * t752
  t770 = 0.1e1 / t354 / t294 * t191
  t778 = 0.5e1 / 0.9e1 * t186 * t356 * t616 * t360
  t781 = 0.1e1 / t301 / t358 / t300
  t795 = 0.2e1 / 0.9e1 * t33 * t725 * t376
  t796 = 0.1e1 / t371
  t798 = 0.2e1 * t734
  t799 = -0.6e1 * t731 - t798
  t800 = t796 * t799
  t801 = 0.1e1 / t374
  t802 = t801 * t799
  t810 = t33 * t714 * t720 / 0.3e1
  t813 = t29 * t380 * t431 / 0.9e1
  t817 = t386 ** 2
  t818 = 0.1e1 / t817
  t819 = t384 * t818
  t822 = -t810 - t813 + t302 * t736 / 0.2e1
  t827 = 0.1e1 / t384 * t386
  t833 = t393 * t818
  t838 = 0.1e1 / t393 * t386
  t846 = f.my_piecewise3(t238, 0, -0.3e1 / 0.8e1 * t5 * t705 * t26 * t398 - t713 - 0.3e1 / 0.8e1 * t5 * t245 * (-(-0.15757629629629629629629629629629629629629629629630e-1 * t723 - t728 - 0.78788148148148148148148148148148148148148148148150e-2 * t739) * t308 - t316 * (t723 + t743 + t739 / 0.2e1 - t749 - t753 - t757 / 0.2e1) * t328 - t351 * (0.5e1 * t723 + t763 + 0.5e1 / 0.2e1 * t739 - 0.10e2 * t749 - t766 - 0.5e1 * t757 + 0.5e1 / 0.3e1 * t186 * t770 * t360 * t720 + t778 + 0.5e1 / 0.6e1 * t186 * t357 * t781 * t736) * t366 - 0.2e1 / 0.3e1 * t33 * t714 * t376 * t720 - t795 + 0.2e1 / 0.3e1 * t33 * t252 * (t800 / 0.6e1 - t802 / 0.6e1) + 0.2e1 * t293 * ((-t810 - t813 + t800 / 0.6e1) * t387 - t819 * t822) * t827 - 0.2e1 * t345 * ((-t810 - t813 + t802 / 0.6e1) * t387 - t833 * t822) * t838))
  vrho_0_ = t237 + t402 + t6 * (t700 + t846)
  t849 = -t7 - t405
  t850 = f.my_piecewise5(t10, 0, t14, 0, t849)
  t853 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t850)
  t858 = f.my_piecewise5(t35, 0, t37, 0, t849)
  t861 = f.my_piecewise3(t40, 0, t421 * t858 / 0.3e1)
  t864 = t33 * t419 * t124 * t861
  t867 = t521 * t522 * t861
  t869 = -0.2e1 / 0.3e1 * t867 - t528
  t872 = t33 * t45 * t146 * t869
  t878 = t555 * t556 * t861
  t880 = t563 * t564 * t869
  t905 = -0.6e1 * t867 - t646
  t906 = t643 * t905
  t907 = t649 * t905
  t915 = t33 * t419 * t861 / 0.3e1
  t921 = -t915 - t665 + t124 * t869 / 0.2e1
  t940 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t853 * t26 * t233 - t418 - 0.3e1 / 0.8e1 * t5 * t27 * (-(-0.15757629629629629629629629629629629629629629629630e-1 * t864 - t435 - 0.78788148148148148148148148148148148148148148148150e-2 * t872) * t130 - t138 * (t864 + t552 + t872 / 0.2e1 - t878 - t562 - t880 / 0.2e1) * t153 - t178 * (0.5e1 * t864 + t603 + 0.5e1 / 0.2e1 * t872 - 0.10e2 * t878 - t606 - 0.5e1 * t880 + 0.5e1 / 0.3e1 * t186 * t610 * t195 * t861 + t620 + 0.5e1 / 0.6e1 * t186 * t192 * t623 * t869) * t201 - 0.2e1 / 0.3e1 * t33 * t419 * t211 * t861 - t642 + 0.2e1 / 0.3e1 * t33 * t45 * (t906 / 0.6e1 - t907 / 0.6e1) + 0.2e1 * t109 * ((-t915 - t665 + t906 / 0.6e1) * t222 - t671 * t921) * t679 - 0.2e1 * t172 * ((-t915 - t665 + t907 / 0.6e1) * t222 - t687 * t921) * t692))
  t941 = -t849
  t942 = f.my_piecewise5(t14, 0, t10, 0, t941)
  t945 = f.my_piecewise3(t241, 0, 0.4e1 / 0.3e1 * t242 * t942)
  t950 = f.my_piecewise5(t37, 0, t35, 0, t941)
  t953 = f.my_piecewise3(t248, 0, t716 * t950 / 0.3e1)
  t956 = t33 * t714 * t302 * t953
  t960 = t263 * t276 * t290 * t47
  t962 = r1 ** 2
  t964 = 0.1e1 / t254 / t962
  t966 = 0.1e1 / t261
  t972 = t66 * t263 * t48
  t974 = t260 * t966
  t975 = t253 * t964 * t974
  t979 = t68 * t264 * t48
  t983 = t71 * t266 * t48
  t987 = t74 * t268 * t48
  t991 = t77 * t270 * t48
  t995 = t80 * t272 * t48
  t1001 = t289 ** 2
  t1002 = 0.1e1 / t1001
  t1006 = t87 * t263 * t48
  t1010 = t89 * t264 * t48
  t1014 = t91 * t266 * t48
  t1018 = t93 * t268 * t48
  t1022 = t95 * t270 * t48
  t1026 = t97 * t272 * t48
  t1030 = t99 * t274 * t48
  t1034 = t102 * t285 * t48
  t1040 = f.my_piecewise3(t292, 0.2e1 / 0.9e1 * t960 * t32 * t253 * t964 * t260 * t966 + t264 * (0.2e1 / 0.9e1 * t972 * t975 - t979 * t975 / 0.3e1 + 0.4e1 / 0.9e1 * t983 * t975 - 0.5e1 / 0.9e1 * t987 * t975 + 0.2e1 / 0.3e1 * t991 * t975 - 0.7e1 / 0.9e1 * t995 * t975) * t290 - t277 * t1002 * (-t482 * t975 / 0.9e1 + 0.2e1 / 0.9e1 * t1006 * t975 - t1010 * t975 / 0.3e1 + 0.4e1 / 0.9e1 * t1014 * t975 - 0.5e1 / 0.9e1 * t1018 * t975 + 0.2e1 / 0.3e1 * t1022 * t975 - 0.7e1 / 0.9e1 * t1026 * t975 + 0.8e1 / 0.9e1 * t1030 * t975 - t1034 * t975), 0)
  t1042 = t521 * t729 * t953
  t1044 = t1040 - 0.2e1 / 0.3e1 * t1042 - t735
  t1047 = t33 * t252 * t321 * t1044
  t1051 = t306 * t328
  t1054 = t263 * t312 * t48
  t1055 = t1054 * t975
  t1057 = t311 ** 2
  t1060 = t266 / t1057 * t48
  t1061 = t1060 * t975
  t1069 = t746 * t747 * t953
  t1071 = t754 * t755 * t1044
  t1092 = t338 * t327 * t348
  t1095 = 0.1e1 / t340
  t1097 = 0.1e1 / t346
  t1098 = f.my_piecewise3(t343, t1040, 0)
  t1122 = t327 ** 2
  t1123 = 0.1e1 / t1122
  t1132 = 0.6e1 * t1042
  t1134 = t796 * (0.9e1 * t1040 - t1132 - t798)
  t1137 = t801 * (0.9e1 * t1098 - t1132 - t798)
  t1147 = t33 * t714 * t953 / 0.3e1
  t1153 = -t1147 - t813 + t302 * t1044 / 0.2e1
  t1169 = -(-0.15757629629629629629629629629629629629629629629630e-1 * t956 - t728 - 0.78788148148148148148148148148148148148148148148150e-2 * t1047) * t308 + t1051 * t1040 - (0.58592098765432098765432098765432098765432098765431e-2 * t1055 + 0.46925284003333333333333333333333333333333333333333e-2 * t1061 - 0.11111111111111111111111111111111111111111111111111e0 * t1040) * t325 * t328 - t316 * (t956 + t743 + t1047 / 0.2e1 - t1069 - t753 - t1071 / 0.2e1) * t328 + 0.2e1 * t326 * t366 * t1040 - (-(0.10546577777777777777777777777777777777777777777778e-1 * t1055 + 0.84465511206000000000000000000000000000000000000000e-2 * t1061 - 0.20000000000000000000000000000000000000000000000000e0 * t1040) * t307 / 0.9e1 - t332 * t1040 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t307 * t1040 - 0.30288440000000000000000000000000000000000000000001e0 * t327 * t1040 - 0.7e1 / 0.18e2 * t1092 * t1040 - t339 * (0.6e1 / 0.5e1 * t1095 * t1040 - 0.6e1 / 0.5e1 * t1097 * t1098) / 0.9e1) * t364 * t366 - t351 * (0.5e1 * t956 + t763 + 0.5e1 / 0.2e1 * t1047 - 0.10e2 * t1069 - t766 - 0.5e1 * t1071 + 0.5e1 / 0.3e1 * t186 * t770 * t360 * t953 + t778 + 0.5e1 / 0.6e1 * t186 * t357 * t781 * t1044) * t366 + 0.3e1 * t365 * t1123 * t1040 - 0.2e1 / 0.3e1 * t33 * t714 * t376 * t953 - t795 + 0.2e1 / 0.3e1 * t33 * t252 * (t1134 / 0.6e1 - t1137 / 0.6e1) + 0.2e1 * t1040 * t389 + 0.2e1 * t293 * ((-t1147 - t813 + t1134 / 0.6e1) * t387 - t819 * t1153) * t827 - 0.2e1 * t1098 * t395 - 0.2e1 * t345 * ((-t1147 - t813 + t1137 / 0.6e1) * t387 - t833 * t1153) * t838
  t1174 = f.my_piecewise3(t238, 0, -0.3e1 / 0.8e1 * t5 * t945 * t26 * t398 - t713 - 0.3e1 / 0.8e1 * t5 * t245 * t1169)
  vrho_1_ = t237 + t402 + t6 * (t940 + t1174)
  t1179 = 0.1e1 / t49
  t1187 = t1179 * t52 * t452
  t1225 = f.my_piecewise3(t108, -t438 * t32 * t1179 * t52 * t56 * t444 / 0.12e2 + t65 * (-t450 * t1187 / 0.12e2 + t457 * t1187 / 0.8e1 - t461 * t1187 / 0.6e1 + 0.5e1 / 0.24e2 * t465 * t1187 - t469 * t1187 / 0.4e1 + 0.7e1 / 0.24e2 * t473 * t1187) * t106 - t84 * t480 * (t482 * t1187 / 0.24e2 - t486 * t1187 / 0.12e2 + t490 * t1187 / 0.8e1 - t494 * t1187 / 0.6e1 + 0.5e1 / 0.24e2 * t498 * t1187 - t502 * t1187 / 0.4e1 + 0.7e1 / 0.24e2 * t506 * t1187 - t510 * t1187 / 0.3e1 + 0.3e1 / 0.8e1 * t514 * t1187), 0)
  t1231 = t539 * t1187
  t1233 = t545 * t1187
  t1241 = t33 * t45 * t146 * t1225
  t1243 = t563 * t564 * t1225
  t1266 = f.my_piecewise3(t170, t1225, 0)
  t1287 = t643 * t1225
  t1288 = t649 * t1266
  t1298 = t124 * t1225
  t1315 = 0.78788148148148148148148148148148148148148148148150e-2 * t29 * t215 * t44 * t146 * t1225 * t130 + t536 * t1225 - (-0.21972037037037037037037037037037037037037037037037e-2 * t1231 - 0.17596981501250000000000000000000000000000000000000e-2 * t1233 - 0.11111111111111111111111111111111111111111111111111e0 * t1225) * t150 * t153 - t138 * (t1241 / 0.2e1 - t1243 / 0.2e1) * t153 + 0.2e1 * t151 * t201 * t1225 - (-(-0.39549666666666666666666666666666666666666666666667e-2 * t1231 - 0.31674566702250000000000000000000000000000000000000e-2 * t1233 - 0.20000000000000000000000000000000000000000000000000e0 * t1225) * t129 / 0.9e1 - t157 * t1225 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t129 * t1225 - 0.30288440000000000000000000000000000000000000000001e0 * t152 * t1225 - 0.7e1 / 0.18e2 * t587 * t1225 - t164 * (0.6e1 / 0.5e1 * t590 * t1225 - 0.6e1 / 0.5e1 * t592 * t1266) / 0.9e1) * t199 * t201 - t178 * (0.5e1 / 0.2e1 * t1241 - 0.5e1 * t1243 + 0.5e1 / 0.6e1 * t186 * t192 * t623 * t1225) * t201 + 0.3e1 * t200 * t632 * t1225 + 0.2e1 / 0.3e1 * t33 * t45 * (0.3e1 / 0.2e1 * t1287 - 0.3e1 / 0.2e1 * t1288) + 0.2e1 * t1225 * t224 + 0.2e1 * t109 * (0.3e1 / 0.2e1 * t1287 * t222 - t671 * t1298 / 0.2e1) * t679 - 0.2e1 * t1266 * t230 - 0.2e1 * t172 * (0.3e1 / 0.2e1 * t1288 * t222 - t687 * t1298 / 0.2e1) * t692
  t1319 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t1315)
  vsigma_0_ = t6 * t1319
  vsigma_1_ = 0.0e0
  t1322 = 0.1e1 / t253
  t1330 = t1322 * t256 * t974
  t1368 = f.my_piecewise3(t292, -t960 * t32 * t1322 * t256 * t260 * t966 / 0.12e2 + t264 * (-t972 * t1330 / 0.12e2 + t979 * t1330 / 0.8e1 - t983 * t1330 / 0.6e1 + 0.5e1 / 0.24e2 * t987 * t1330 - t991 * t1330 / 0.4e1 + 0.7e1 / 0.24e2 * t995 * t1330) * t290 - t277 * t1002 * (t482 * t1330 / 0.24e2 - t1006 * t1330 / 0.12e2 + t1010 * t1330 / 0.8e1 - t1014 * t1330 / 0.6e1 + 0.5e1 / 0.24e2 * t1018 * t1330 - t1022 * t1330 / 0.4e1 + 0.7e1 / 0.24e2 * t1026 * t1330 - t1030 * t1330 / 0.3e1 + 0.3e1 / 0.8e1 * t1034 * t1330), 0)
  t1374 = t1054 * t1330
  t1376 = t1060 * t1330
  t1384 = t33 * t252 * t321 * t1368
  t1386 = t754 * t755 * t1368
  t1409 = f.my_piecewise3(t343, t1368, 0)
  t1430 = t796 * t1368
  t1431 = t801 * t1409
  t1441 = t302 * t1368
  t1458 = 0.78788148148148148148148148148148148148148148148150e-2 * t29 * t380 * t44 * t321 * t1368 * t308 + t1051 * t1368 - (-0.21972037037037037037037037037037037037037037037037e-2 * t1374 - 0.17596981501250000000000000000000000000000000000000e-2 * t1376 - 0.11111111111111111111111111111111111111111111111111e0 * t1368) * t325 * t328 - t316 * (t1384 / 0.2e1 - t1386 / 0.2e1) * t328 + 0.2e1 * t326 * t366 * t1368 - (-(-0.39549666666666666666666666666666666666666666666667e-2 * t1374 - 0.31674566702250000000000000000000000000000000000000e-2 * t1376 - 0.20000000000000000000000000000000000000000000000000e0 * t1368) * t307 / 0.9e1 - t332 * t1368 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t307 * t1368 - 0.30288440000000000000000000000000000000000000000001e0 * t327 * t1368 - 0.7e1 / 0.18e2 * t1092 * t1368 - t339 * (0.6e1 / 0.5e1 * t1095 * t1368 - 0.6e1 / 0.5e1 * t1097 * t1409) / 0.9e1) * t364 * t366 - t351 * (0.5e1 / 0.2e1 * t1384 - 0.5e1 * t1386 + 0.5e1 / 0.6e1 * t186 * t357 * t781 * t1368) * t366 + 0.3e1 * t365 * t1123 * t1368 + 0.2e1 / 0.3e1 * t33 * t252 * (0.3e1 / 0.2e1 * t1430 - 0.3e1 / 0.2e1 * t1431) + 0.2e1 * t1368 * t389 + 0.2e1 * t293 * (0.3e1 / 0.2e1 * t1430 * t387 - t819 * t1441 / 0.2e1) * t827 - 0.2e1 * t1409 * t395 - 0.2e1 * t345 * (0.3e1 / 0.2e1 * t1431 * t387 - t833 * t1441 / 0.2e1) * t838
  t1462 = f.my_piecewise3(t238, 0, -0.3e1 / 0.8e1 * t5 * t245 * t1458)
  vsigma_2_ = t6 * t1462
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

  hjs_AA = 0.757211

  hjs_BB = -0.106364

  hjs_CC = -0.118649

  hjs_DD = 0.60965

  hjs_fH = lambda s: jnp.sum(jnp.array([params_a[i] * s ** (1 + i) for i in range(1, 6 + 1)]), axis=0) / (1 + jnp.sum(jnp.array([params_b[i] * s ** i for i in range(1, 9 + 1)]), axis=0))

  hjs2_xi = 1 / (jnp.exp(20) - 1)

  hjs_zeta = lambda s: jnp.maximum(s ** 2 * hjs_fH(s), 1e-10)

  hjs2_fs = lambda s: -jnp.log((jnp.exp(-s) + hjs2_xi) / (1 + hjs2_xi))

  hjs_eta = lambda s: jnp.maximum(hjs_AA + hjs_zeta(s), 1e-10)

  hjs_lambda = lambda s: hjs_DD + hjs_zeta(s)

  hjs_fF = lambda rs, z, s: 1 - s ** 2 / (27 * hjs_CC * (1 + s ** 2 / 4)) - hjs_zeta(s) / (2 * hjs_CC)

  hjs_chi = lambda rs, z, s: f.nu(rs, z) / jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)

  hjs_fG = lambda rs, z, s: -2 / 5 * hjs_CC * hjs_fF(rs, z, s) * hjs_lambda(s) - 4 / 15 * hjs_BB * hjs_lambda(s) ** 2 - 6 / 5 * hjs_AA * hjs_lambda(s) ** 3 - hjs_lambda(s) ** (7 / 2) * (4 / 5 * jnp.sqrt(jnp.pi) + 12 / 5 * (jnp.sqrt(hjs_zeta(s)) - jnp.sqrt(hjs_eta(s))))

  hjs_f1 = lambda rs, z, s: +hjs_AA - 4 / 9 * hjs_BB * (1 - hjs_chi(rs, z, s)) / hjs_lambda(s) - 2 / 9 * hjs_CC * hjs_fF(rs, z, s) * (2 - 3 * hjs_chi(rs, z, s) + hjs_chi(rs, z, s) ** 3) / hjs_lambda(s) ** 2 - 1 / 9 * hjs_fG(rs, z, s) * (8 - 15 * hjs_chi(rs, z, s) + 10 * hjs_chi(rs, z, s) ** 3 - 3 * hjs_chi(rs, z, s) ** 5) / hjs_lambda(s) ** 3 + 2 * f.nu(rs, z) * (jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2) - jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) + 2 * hjs_zeta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2))) - 2 * hjs_eta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)))

  hjs_fx = lambda rs, z, x: hjs_f1(rs, z, hjs2_fs(X2S * x))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, hjs_fx, rs, z, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t12 = t11 <= f.p.zeta_threshold
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t12, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t17 * t18
  t20 = t3 ** 2
  t21 = f.p.cam_omega * t20
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t23
  t25 = t21 * t24
  t26 = f.my_piecewise3(t12, t13, t15)
  t27 = 0.1e1 / t26
  t28 = 0.1e1 / t18
  t29 = t27 * t28
  t30 = 6 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = t31 * t24
  t33 = jnp.sqrt(s0)
  t34 = 2 ** (0.1e1 / 0.3e1)
  t35 = t33 * t34
  t37 = 0.1e1 / t18 / r0
  t41 = jnp.exp(-t32 * t35 * t37 / 0.12e2)
  t42 = jnp.exp(20)
  t44 = 0.1e1 / (t42 - 0.1e1)
  t45 = t41 + t44
  t49 = jnp.log(t45 / (0.1e1 + t44))
  t50 = t49 ** 2
  t51 = params.a[0]
  t53 = params.a[1]
  t54 = t50 * t49
  t56 = params.a[2]
  t57 = t50 ** 2
  t59 = params.a[3]
  t60 = t57 * t49
  t62 = params.a[4]
  t63 = t57 * t50
  t65 = params.a[5]
  t66 = t57 * t54
  t68 = t51 * t50 - t53 * t54 + t56 * t57 - t59 * t60 + t62 * t63 - t65 * t66
  t69 = t50 * t68
  t70 = params.b[0]
  t72 = params.b[1]
  t74 = params.b[2]
  t76 = params.b[3]
  t78 = params.b[4]
  t80 = params.b[5]
  t82 = params.b[6]
  t84 = params.b[7]
  t85 = t57 ** 2
  t87 = params.b[8]
  t90 = -t87 * t85 * t49 - t70 * t49 + t72 * t50 - t74 * t54 + t76 * t57 - t78 * t60 + t80 * t63 - t82 * t66 + t84 * t85 + 0.1e1
  t91 = 0.1e1 / t90
  t92 = t69 * t91
  t93 = 0.1e-9 < t92
  t94 = f.my_piecewise3(t93, t92, 0.1e-9)
  t95 = f.p.cam_omega ** 2
  t96 = t95 * t3
  t97 = t23 ** 2
  t99 = t26 ** 2
  t101 = 0.1e1 / t97 / t99
  t102 = t18 ** 2
  t103 = 0.1e1 / t102
  t105 = t96 * t101 * t103
  t107 = 0.609650e0 + t94 + t105 / 0.3e1
  t108 = jnp.sqrt(t107)
  t109 = 0.1e1 / t108
  t111 = t25 * t29 * t109
  t113 = -0.47272888888888888888888888888888888888888888888889e-1 + 0.15757629629629629629629629629629629629629629629630e-1 * t111
  t114 = 0.609650e0 + t94
  t115 = 0.1e1 / t114
  t118 = -0.3203523e1 - 0.80088075000000000000000000000000000000000000000000e0 * t50
  t119 = 0.1e1 / t118
  t120 = t50 * t119
  t123 = -0.26366444444444444444444444444444444444444444444444e-1 + 0.26366444444444444444444444444444444444444444444444e-1 * t120 - 0.11111111111111111111111111111111111111111111111111e0 * t94
  t126 = t95 * f.p.cam_omega / t22
  t128 = 0.1e1 / t99 / t26
  t129 = 0.1e1 / r0
  t132 = 0.1e1 / t108 / t107
  t134 = t126 * t128 * t129 * t132
  t136 = 0.2e1 - t111 + t134 / 0.3e1
  t137 = t123 * t136
  t138 = t114 ** 2
  t139 = 0.1e1 / t138
  t143 = -0.47459600000000000000000000000000000000000000000000e-1 + 0.47459600000000000000000000000000000000000000000000e-1 * t120 - 0.20000000000000000000000000000000000000000000000000e0 * t94
  t147 = t138 * t114
  t149 = jnp.sqrt(t114)
  t150 = t149 * t147
  t151 = jnp.sqrt(jnp.pi)
  t153 = jnp.sqrt(t94)
  t156 = 0.0e0 < 0.7572109999e0 + t94
  t158 = f.my_piecewise3(t156, 0.757211e0 + t94, 0.1e-9)
  t159 = jnp.sqrt(t158)
  t161 = 0.4e1 / 0.5e1 * t151 + 0.12e2 / 0.5e1 * t153 - 0.12e2 / 0.5e1 * t159
  t164 = -t143 * t114 / 0.9e1 + 0.31515259259259259259259259259259259259259259259259e-2 * t138 - 0.10096146666666666666666666666666666666666666666667e0 * t147 - t150 * t161 / 0.9e1
  t167 = t95 ** 2
  t172 = t167 * f.p.cam_omega * t3 / t97 / t22
  t173 = t99 ** 2
  t175 = 0.1e1 / t173 / t26
  t177 = 0.1e1 / t102 / r0
  t178 = t175 * t177
  t179 = t107 ** 2
  t181 = 0.1e1 / t108 / t179
  t185 = 0.8e1 - 0.5e1 * t111 + 0.10e2 / 0.3e1 * t134 - t172 * t178 * t181 / 0.3e1
  t186 = t164 * t185
  t187 = 0.1e1 / t147
  t190 = 0.3e1 * t105
  t192 = jnp.sqrt(0.9e1 * t94 + t190)
  t195 = jnp.sqrt(0.9e1 * t158 + t190)
  t197 = t192 / 0.3e1 - t195 / 0.3e1
  t201 = t24 * t27
  t203 = t21 * t201 * t28
  t205 = t203 / 0.3e1 + t192 / 0.3e1
  t207 = t203 / 0.3e1 + t108
  t208 = 0.1e1 / t207
  t210 = jnp.log(t205 * t208)
  t214 = t203 / 0.3e1 + t195 / 0.3e1
  t216 = jnp.log(t214 * t208)
  t219 = 0.757211e0 - t113 * t115 - t137 * t139 - t186 * t187 + 0.2e1 / 0.3e1 * t25 * t29 * t197 + 0.2e1 * t94 * t210 - 0.2e1 * t158 * t216
  t223 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t219)
  t228 = t27 * t37
  t230 = t25 * t228 * t109
  t235 = t49 * t68 * t91 * t31 * t24
  t236 = r0 ** 2
  t238 = 0.1e1 / t18 / t236
  t240 = 0.1e1 / t45
  t242 = t35 * t238 * t41 * t240
  t246 = t51 * t49 * t32
  t250 = t53 * t50 * t32
  t254 = t56 * t54 * t32
  t258 = t59 * t57 * t32
  t262 = t62 * t60 * t32
  t266 = t65 * t63 * t32
  t272 = t90 ** 2
  t273 = 0.1e1 / t272
  t274 = t70 * t31
  t278 = t41 * t240
  t283 = t72 * t49 * t32
  t287 = t74 * t50 * t32
  t291 = t76 * t54 * t32
  t295 = t78 * t57 * t32
  t299 = t80 * t60 * t32
  t303 = t82 * t63 * t32
  t307 = t84 * t66 * t32
  t311 = t87 * t85 * t32
  t317 = f.my_piecewise3(t93, 0.2e1 / 0.9e1 * t235 * t242 + t50 * (0.2e1 / 0.9e1 * t246 * t242 - t250 * t242 / 0.3e1 + 0.4e1 / 0.9e1 * t254 * t242 - 0.5e1 / 0.9e1 * t258 * t242 + 0.2e1 / 0.3e1 * t262 * t242 - 0.7e1 / 0.9e1 * t266 * t242) * t91 - t69 * t273 * (-t274 * t24 * t33 * t34 * t238 * t278 / 0.9e1 + 0.2e1 / 0.9e1 * t283 * t242 - t287 * t242 / 0.3e1 + 0.4e1 / 0.9e1 * t291 * t242 - 0.5e1 / 0.9e1 * t295 * t242 + 0.2e1 / 0.3e1 * t299 * t242 - 0.7e1 / 0.9e1 * t303 * t242 + 0.8e1 / 0.9e1 * t307 * t242 - t311 * t242), 0)
  t319 = t96 * t101 * t177
  t321 = t317 - 0.2e1 / 0.9e1 * t319
  t324 = t25 * t29 * t132 * t321
  t328 = t113 * t139
  t331 = t49 * t119 * t32
  t332 = t331 * t242
  t334 = t118 ** 2
  t337 = t54 / t334 * t32
  t338 = t337 * t242
  t349 = t126 * t128 / t236 * t132
  t351 = t126 * t128
  t352 = t129 * t181
  t354 = t351 * t352 * t321
  t375 = t149 * t138 * t161
  t378 = 0.1e1 / t153
  t380 = 0.1e1 / t159
  t381 = f.my_piecewise3(t156, t317, 0)
  t402 = 0.1e1 / t108 / t179 / t107
  t410 = t138 ** 2
  t411 = 0.1e1 / t410
  t418 = 0.1e1 / t192
  t420 = 0.2e1 * t319
  t422 = t418 * (0.9e1 * t317 - t420)
  t423 = 0.1e1 / t195
  t426 = t423 * (0.9e1 * t381 - t420)
  t436 = t21 * t201 * t37 / 0.9e1
  t440 = t207 ** 2
  t441 = 0.1e1 / t440
  t442 = t205 * t441
  t445 = -t436 + t109 * t321 / 0.2e1
  t450 = 0.1e1 / t205 * t207
  t458 = t214 * t441
  t463 = 0.1e1 / t214 * t207
  t466 = -(-0.52525432098765432098765432098765432098765432098767e-2 * t230 - 0.78788148148148148148148148148148148148148148148150e-2 * t324) * t115 + t328 * t317 - (0.58592098765432098765432098765432098765432098765431e-2 * t332 + 0.46925284003333333333333333333333333333333333333333e-2 * t338 - 0.11111111111111111111111111111111111111111111111111e0 * t317) * t136 * t139 - t123 * (t230 / 0.3e1 + t324 / 0.2e1 - t349 / 0.3e1 - t354 / 0.2e1) * t139 + 0.2e1 * t137 * t187 * t317 - (-(0.10546577777777777777777777777777777777777777777778e-1 * t332 + 0.84465511206000000000000000000000000000000000000000e-2 * t338 - 0.20000000000000000000000000000000000000000000000000e0 * t317) * t114 / 0.9e1 - t143 * t317 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t114 * t317 - 0.30288440000000000000000000000000000000000000000001e0 * t138 * t317 - 0.7e1 / 0.18e2 * t375 * t317 - t150 * (0.6e1 / 0.5e1 * t378 * t317 - 0.6e1 / 0.5e1 * t380 * t381) / 0.9e1) * t185 * t187 - t164 * (0.5e1 / 0.3e1 * t230 + 0.5e1 / 0.2e1 * t324 - 0.10e2 / 0.3e1 * t349 - 0.5e1 * t354 + 0.5e1 / 0.9e1 * t172 * t175 / t102 / t236 * t181 + 0.5e1 / 0.6e1 * t172 * t178 * t402 * t321) * t187 + 0.3e1 * t186 * t411 * t317 - 0.2e1 / 0.9e1 * t25 * t228 * t197 + 0.2e1 / 0.3e1 * t25 * t29 * (t422 / 0.6e1 - t426 / 0.6e1) + 0.2e1 * t317 * t210 + 0.2e1 * t94 * ((-t436 + t422 / 0.6e1) * t208 - t442 * t445) * t450 - 0.2e1 * t381 * t216 - 0.2e1 * t158 * ((-t436 + t426 / 0.6e1) * t208 - t458 * t445) * t463
  t471 = f.my_piecewise3(t2, 0, -t6 * t17 * t103 * t219 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * t466)
  vrho_0_ = 0.2e1 * r0 * t471 + 0.2e1 * t223
  t476 = 0.1e1 / t33
  t480 = t476 * t34 * t37 * t41 * t240
  t524 = f.my_piecewise3(t93, -t235 * t480 / 0.12e2 + t50 * (-t246 * t480 / 0.12e2 + t250 * t480 / 0.8e1 - t254 * t480 / 0.6e1 + 0.5e1 / 0.24e2 * t258 * t480 - t262 * t480 / 0.4e1 + 0.7e1 / 0.24e2 * t266 * t480) * t91 - t69 * t273 * (t274 * t24 * t476 * t34 * t37 * t278 / 0.24e2 - t283 * t480 / 0.12e2 + t287 * t480 / 0.8e1 - t291 * t480 / 0.6e1 + 0.5e1 / 0.24e2 * t295 * t480 - t299 * t480 / 0.4e1 + 0.7e1 / 0.24e2 * t303 * t480 - t307 * t480 / 0.3e1 + 0.3e1 / 0.8e1 * t311 * t480), 0)
  t530 = t331 * t480
  t532 = t337 * t480
  t540 = t25 * t29 * t132 * t524
  t542 = t351 * t352 * t524
  t565 = f.my_piecewise3(t156, t524, 0)
  t586 = t418 * t524
  t587 = t423 * t565
  t597 = t109 * t524
  t614 = 0.78788148148148148148148148148148148148148148148150e-2 * t21 * t201 * t28 * t132 * t524 * t115 + t328 * t524 - (-0.21972037037037037037037037037037037037037037037037e-2 * t530 - 0.17596981501250000000000000000000000000000000000000e-2 * t532 - 0.11111111111111111111111111111111111111111111111111e0 * t524) * t136 * t139 - t123 * (t540 / 0.2e1 - t542 / 0.2e1) * t139 + 0.2e1 * t137 * t187 * t524 - (-(-0.39549666666666666666666666666666666666666666666667e-2 * t530 - 0.31674566702250000000000000000000000000000000000000e-2 * t532 - 0.20000000000000000000000000000000000000000000000000e0 * t524) * t114 / 0.9e1 - t143 * t524 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t114 * t524 - 0.30288440000000000000000000000000000000000000000001e0 * t138 * t524 - 0.7e1 / 0.18e2 * t375 * t524 - t150 * (0.6e1 / 0.5e1 * t378 * t524 - 0.6e1 / 0.5e1 * t380 * t565) / 0.9e1) * t185 * t187 - t164 * (0.5e1 / 0.2e1 * t540 - 0.5e1 * t542 + 0.5e1 / 0.6e1 * t172 * t178 * t402 * t524) * t187 + 0.3e1 * t186 * t411 * t524 + 0.2e1 / 0.3e1 * t25 * t29 * (0.3e1 / 0.2e1 * t586 - 0.3e1 / 0.2e1 * t587) + 0.2e1 * t524 * t210 + 0.2e1 * t94 * (0.3e1 / 0.2e1 * t586 * t208 - t442 * t597 / 0.2e1) * t450 - 0.2e1 * t565 * t216 - 0.2e1 * t158 * (0.3e1 / 0.2e1 * t587 * t208 - t458 * t597 / 0.2e1) * t463
  t618 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t614)
  vsigma_0_ = 0.2e1 * r0 * t618
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  vsigma_0_ = _b(vsigma_0_)
  vsigma_1_ = _b(vsigma_1_)
  vsigma_2_ = _b(vsigma_2_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res
