"""Generated from hyb_gga_xc_case21.mpl."""

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
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))
  params_gammac_raw = params.gammac
  if isinstance(params_gammac_raw, (str, bytes, dict)):
    params_gammac = params_gammac_raw
  else:
    try:
      params_gammac_seq = list(params_gammac_raw)
    except TypeError:
      params_gammac = params_gammac_raw
    else:
      params_gammac_seq = np.asarray(params_gammac_seq, dtype=np.float64)
      params_gammac = np.concatenate((np.array([np.nan], dtype=np.float64), params_gammac_seq))
  params_gammax_raw = params.gammax
  if isinstance(params_gammax_raw, (str, bytes, dict)):
    params_gammax = params_gammax_raw
  else:
    try:
      params_gammax_seq = list(params_gammax_raw)
    except TypeError:
      params_gammax = params_gammax_raw
    else:
      params_gammax_seq = np.asarray(params_gammax_seq, dtype=np.float64)
      params_gammax = np.concatenate((np.array([np.nan], dtype=np.float64), params_gammax_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  case21_ux0 = lambda s: params_gammax * s ** 2 / (1 + params_gammax * s ** 2)

  case21_t = lambda rs, z, xs0, xs1: (jnp.pi / 3) ** (1 / 6) * (xs0 * f.n_spin(rs, z) ** (4 / 3) + xs1 * f.n_spin(rs, -z) ** (4 / 3)) / (4 * f.n_total(rs) ** (7 / 6) * f.mphi(z))

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  case21_fx = lambda x: xbspline(case21_ux0(X2S * x), 0, params)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  case21_Ex = lambda rs, z, xs0, xs1: gga_exchange(f, params, case21_fx, rs, z, xs0, xs1)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  case21_uc = lambda rs, z, xs0, xs1: -f.mphi(z) ** 3 * case21_t(rs, z, xs0, xs1) ** 2 / (-f.mphi(z) ** 3 * case21_t(rs, z, xs0, xs1) ** 2 + params_gammac * f_pw(rs, z))

  case21_Ec = lambda rs, z, xs0, xs1: cbspline(case21_uc(rs, z, xs0, xs1), 0, params) * f_pw(rs, z)

  f_case21 = lambda rs, z, xt, xs0, xs1: (1 - params_ax) * case21_Ex(rs, z, xs0, xs1) + case21_Ec(rs, z, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_case21(rs, z, xt, xs0, xs1)

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
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))
  params_gammac_raw = params.gammac
  if isinstance(params_gammac_raw, (str, bytes, dict)):
    params_gammac = params_gammac_raw
  else:
    try:
      params_gammac_seq = list(params_gammac_raw)
    except TypeError:
      params_gammac = params_gammac_raw
    else:
      params_gammac_seq = np.asarray(params_gammac_seq, dtype=np.float64)
      params_gammac = np.concatenate((np.array([np.nan], dtype=np.float64), params_gammac_seq))
  params_gammax_raw = params.gammax
  if isinstance(params_gammax_raw, (str, bytes, dict)):
    params_gammax = params_gammax_raw
  else:
    try:
      params_gammax_seq = list(params_gammax_raw)
    except TypeError:
      params_gammax = params_gammax_raw
    else:
      params_gammax_seq = np.asarray(params_gammax_seq, dtype=np.float64)
      params_gammax = np.concatenate((np.array([np.nan], dtype=np.float64), params_gammax_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  case21_ux0 = lambda s: params_gammax * s ** 2 / (1 + params_gammax * s ** 2)

  case21_t = lambda rs, z, xs0, xs1: (jnp.pi / 3) ** (1 / 6) * (xs0 * f.n_spin(rs, z) ** (4 / 3) + xs1 * f.n_spin(rs, -z) ** (4 / 3)) / (4 * f.n_total(rs) ** (7 / 6) * f.mphi(z))

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  case21_fx = lambda x: xbspline(case21_ux0(X2S * x), 0, params)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  case21_Ex = lambda rs, z, xs0, xs1: gga_exchange(f, params, case21_fx, rs, z, xs0, xs1)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  case21_uc = lambda rs, z, xs0, xs1: -f.mphi(z) ** 3 * case21_t(rs, z, xs0, xs1) ** 2 / (-f.mphi(z) ** 3 * case21_t(rs, z, xs0, xs1) ** 2 + params_gammac * f_pw(rs, z))

  case21_Ec = lambda rs, z, xs0, xs1: cbspline(case21_uc(rs, z, xs0, xs1), 0, params) * f_pw(rs, z)

  f_case21 = lambda rs, z, xt, xs0, xs1: (1 - params_ax) * case21_Ex(rs, z, xs0, xs1) + case21_Ec(rs, z, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_case21(rs, z, xt, xs0, xs1)

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
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))
  params_gammac_raw = params.gammac
  if isinstance(params_gammac_raw, (str, bytes, dict)):
    params_gammac = params_gammac_raw
  else:
    try:
      params_gammac_seq = list(params_gammac_raw)
    except TypeError:
      params_gammac = params_gammac_raw
    else:
      params_gammac_seq = np.asarray(params_gammac_seq, dtype=np.float64)
      params_gammac = np.concatenate((np.array([np.nan], dtype=np.float64), params_gammac_seq))
  params_gammax_raw = params.gammax
  if isinstance(params_gammax_raw, (str, bytes, dict)):
    params_gammax = params_gammax_raw
  else:
    try:
      params_gammax_seq = list(params_gammax_raw)
    except TypeError:
      params_gammax = params_gammax_raw
    else:
      params_gammax_seq = np.asarray(params_gammax_seq, dtype=np.float64)
      params_gammax = np.concatenate((np.array([np.nan], dtype=np.float64), params_gammax_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  case21_ux0 = lambda s: params_gammax * s ** 2 / (1 + params_gammax * s ** 2)

  case21_t = lambda rs, z, xs0, xs1: (jnp.pi / 3) ** (1 / 6) * (xs0 * f.n_spin(rs, z) ** (4 / 3) + xs1 * f.n_spin(rs, -z) ** (4 / 3)) / (4 * f.n_total(rs) ** (7 / 6) * f.mphi(z))

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  case21_fx = lambda x: xbspline(case21_ux0(X2S * x), 0, params)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  case21_Ex = lambda rs, z, xs0, xs1: gga_exchange(f, params, case21_fx, rs, z, xs0, xs1)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  case21_uc = lambda rs, z, xs0, xs1: -f.mphi(z) ** 3 * case21_t(rs, z, xs0, xs1) ** 2 / (-f.mphi(z) ** 3 * case21_t(rs, z, xs0, xs1) ** 2 + params_gammac * f_pw(rs, z))

  case21_Ec = lambda rs, z, xs0, xs1: cbspline(case21_uc(rs, z, xs0, xs1), 0, params) * f_pw(rs, z)

  f_case21 = lambda rs, z, xt, xs0, xs1: (1 - params_ax) * case21_Ex(rs, z, xs0, xs1) + case21_Ec(rs, z, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_case21(rs, z, xt, xs0, xs1)

  t1 = 0.1e1 - params.ax
  t2 = r0 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t23 = t22 * f.p.zeta_threshold
  t24 = t20 ** (0.1e1 / 0.3e1)
  t26 = f.my_piecewise3(t21, t23, t24 * t20)
  t27 = t7 ** (0.1e1 / 0.3e1)
  t29 = 6 ** (0.1e1 / 0.3e1)
  t30 = params.gammax * t29
  t31 = jnp.pi ** 2
  t32 = t31 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = 0.1e1 / t33
  t35 = t30 * t34
  t36 = r0 ** 2
  t37 = r0 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t40 = 0.1e1 / t38 / t36
  t46 = 0.1e1 + t30 * t34 * s0 * t40 / 0.24e2
  t47 = 0.1e1 / t46
  t50 = t35 * s0 * t40 * t47 / 0.24e2
  t51 = xbspline(t50, 0, params)
  t55 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t26 * t27 * t51)
  t56 = r1 <= f.p.dens_threshold
  t57 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t58 = 0.1e1 + t57
  t59 = t58 <= f.p.zeta_threshold
  t60 = t58 ** (0.1e1 / 0.3e1)
  t62 = f.my_piecewise3(t59, t23, t60 * t58)
  t64 = r1 ** 2
  t65 = r1 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t74 = 0.1e1 + t30 * t34 * s2 * t68 / 0.24e2
  t75 = 0.1e1 / t74
  t78 = t35 * s2 * t68 * t75 / 0.24e2
  t79 = xbspline(t78, 0, params)
  t83 = f.my_piecewise3(t56, 0, -0.3e1 / 0.8e1 * t6 * t62 * t27 * t79)
  t85 = t1 * (t55 + t83)
  t86 = 0.1e1 + t18
  t87 = t86 <= f.p.zeta_threshold
  t88 = t22 ** 2
  t89 = t86 ** (0.1e1 / 0.3e1)
  t90 = t89 ** 2
  t91 = f.my_piecewise3(t87, t88, t90)
  t92 = 0.1e1 - t18
  t93 = t92 <= f.p.zeta_threshold
  t94 = t92 ** (0.1e1 / 0.3e1)
  t95 = t94 ** 2
  t96 = f.my_piecewise3(t93, t88, t95)
  t98 = t91 / 0.2e1 + t96 / 0.2e1
  t99 = t3 ** 2
  t100 = t98 * t99
  t101 = t100 * t4
  t102 = jnp.sqrt(s0)
  t103 = jnp.sqrt(s2)
  t104 = t102 + t103
  t105 = t104 ** 2
  t106 = t7 ** 2
  t108 = 0.1e1 / t27 / t106
  t109 = t105 * t108
  t110 = t4 * t105
  t111 = t110 * t108
  t115 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t116 = t3 * t115
  t117 = 4 ** (0.1e1 / 0.3e1)
  t118 = t117 ** 2
  t121 = t116 * t118 / t27
  t123 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t121
  t124 = jnp.sqrt(t121)
  t127 = t121 ** 0.15e1
  t129 = t115 ** 2
  t130 = t99 * t129
  t131 = t27 ** 2
  t132 = 0.1e1 / t131
  t134 = t130 * t117 * t132
  t136 = 0.23615562999000000000000000000000000000000000000000e0 * t124 + 0.55770497660000000000000000000000000000000000000000e-1 * t121 + 0.12733196185000000000000000000000000000000000000000e-1 * t127 + 0.76629248290000000000000000000000000000000000000000e-2 * t134
  t138 = 0.1e1 + 0.1e1 / t136
  t139 = jnp.log(t138)
  t140 = t123 * t139
  t141 = t17 ** 2
  t142 = t141 ** 2
  t143 = t106 ** 2
  t144 = 0.1e1 / t143
  t145 = t142 * t144
  t147 = f.my_piecewise3(t87, t23, t89 * t86)
  t149 = f.my_piecewise3(t93, t23, t94 * t92)
  t151 = 2 ** (0.1e1 / 0.3e1)
  t154 = 0.1e1 / (0.2e1 * t151 - 0.2e1)
  t155 = (t147 + t149 - 0.2e1) * t154
  t157 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t121
  t162 = 0.21948324211500000000000000000000000000000000000000e0 * t124 + 0.48172707847500000000000000000000000000000000000000e-1 * t121 + 0.13082189292500000000000000000000000000000000000000e-1 * t127 + 0.48592432297500000000000000000000000000000000000000e-2 * t134
  t164 = 0.1e1 + 0.1e1 / t162
  t165 = jnp.log(t164)
  t168 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t121
  t173 = 0.17489762330000000000000000000000000000000000000000e0 * t124 + 0.30591463695000000000000000000000000000000000000000e-1 * t121 + 0.37162156485000000000000000000000000000000000000000e-2 * t127 + 0.41939460495000000000000000000000000000000000000000e-2 * t134
  t175 = 0.1e1 + 0.1e1 / t173
  t176 = jnp.log(t175)
  t177 = t168 * t176
  t179 = -t157 * t165 + t140 - 0.58482236226346462072622386637590534819724553404281e0 * t177
  t180 = t155 * t179
  t184 = -t140 + t145 * t180 + 0.58482236226346462072622386637590534819724553404281e0 * t155 * t177
  t186 = -t100 * t111 / 0.48e2 + params.gammac * t184
  t187 = 0.1e1 / t186
  t188 = t109 * t187
  t190 = t101 * t188 / 0.48e2
  t191 = cbspline(-t190, 0, params)
  t192 = t191 * t184
  t194 = t17 / t106
  t195 = t8 - t194
  t196 = f.my_piecewise5(t11, 0, t15, 0, t195)
  t199 = f.my_piecewise3(t21, 0, 0.4e1 / 0.3e1 * t24 * t196)
  t207 = t6 * t26 * t132 * t51 / 0.8e1
  t208 = t6 * t26
  t209 = xbspline(t50, 1, params)
  t210 = t27 * t209
  t218 = params.gammax ** 2
  t219 = t29 ** 2
  t223 = t218 * t219 / t32 / t31
  t224 = s0 ** 2
  t225 = t36 ** 2
  t230 = t46 ** 2
  t231 = 0.1e1 / t230
  t240 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t199 * t27 * t51 - t207 - 0.3e1 / 0.8e1 * t208 * t210 * (-t35 * s0 / t38 / t36 / r0 * t47 / 0.9e1 + t223 * t224 / t37 / t225 / t36 * t231 / 0.216e3))
  t241 = -t195
  t242 = f.my_piecewise5(t15, 0, t11, 0, t241)
  t245 = f.my_piecewise3(t59, 0, 0.4e1 / 0.3e1 * t60 * t242)
  t253 = t6 * t62 * t132 * t79 / 0.8e1
  t255 = f.my_piecewise3(t56, 0, -0.3e1 / 0.8e1 * t6 * t245 * t27 * t79 - t253)
  t258 = cbspline(-t190, 1, params)
  t259 = 0.1e1 / t89
  t262 = f.my_piecewise3(t87, 0, 0.2e1 / 0.3e1 * t259 * t195)
  t263 = 0.1e1 / t94
  t266 = f.my_piecewise3(t93, 0, 0.2e1 / 0.3e1 * t263 * t241)
  t269 = (t262 / 0.2e1 + t266 / 0.2e1) * t99
  t275 = 0.1e1 / t27 / t106 / t7
  t279 = 0.7e1 / 0.144e3 * t101 * t105 * t275 * t187
  t280 = t186 ** 2
  t281 = 0.1e1 / t280
  t286 = 0.7e1 / 0.144e3 * t100 * t110 * t275
  t288 = 0.1e1 / t27 / t7
  t289 = t118 * t288
  t292 = 0.11073470983333333333333333333333333333333333333333e-2 * t116 * t289 * t139
  t293 = t136 ** 2
  t298 = t115 * t118
  t299 = t298 * t288
  t300 = 0.1e1 / t124 * t3 * t299
  t302 = t116 * t289
  t304 = t121 ** 0.5e0
  t306 = t304 * t3 * t299
  t311 = t130 * t117 / t131 / t7
  t316 = t123 / t293 * (-0.39359271665000000000000000000000000000000000000000e-1 * t300 - 0.18590165886666666666666666666666666666666666666667e-1 * t302 - 0.63665980925000000000000000000000000000000000000000e-2 * t306 - 0.51086165526666666666666666666666666666666666666667e-2 * t311) / t138
  t320 = 0.4e1 * t141 * t17 * t144 * t180
  t325 = 0.4e1 * t142 / t143 / t7 * t180
  t328 = f.my_piecewise3(t87, 0, 0.4e1 / 0.3e1 * t89 * t195)
  t331 = f.my_piecewise3(t93, 0, 0.4e1 / 0.3e1 * t94 * t241)
  t333 = (t328 + t331) * t154
  t339 = t162 ** 2
  t353 = t173 ** 2
  t354 = 0.1e1 / t353
  t360 = -0.29149603883333333333333333333333333333333333333333e-1 * t300 - 0.10197154565000000000000000000000000000000000000000e-1 * t302 - 0.18581078242500000000000000000000000000000000000000e-2 * t306 - 0.27959640330000000000000000000000000000000000000000e-2 * t311
  t361 = 0.1e1 / t175
  t367 = t145 * t155 * (0.53237641966666666666666666666666666666666666666667e-3 * t116 * t289 * t165 + t157 / t339 * (-0.36580540352500000000000000000000000000000000000000e-1 * t300 - 0.16057569282500000000000000000000000000000000000000e-1 * t302 - 0.65410946462500000000000000000000000000000000000000e-2 * t306 - 0.32394954865000000000000000000000000000000000000000e-2 * t311) / t164 - t292 - t316 + 0.18311447306006545054854346104378990962041954983034e-3 * t116 * t289 * t176 + 0.58482236226346462072622386637590534819724553404281e0 * t168 * t354 * t360 * t361)
  t374 = 0.18311447306006545054854346104378990962041954983034e-3 * t155 * t3 * t298 * t288 * t176
  t379 = 0.58482236226346462072622386637590534819724553404281e0 * t155 * t168 * t354 * t360 * t361
  t380 = t292 + t316 + t320 - t325 + t145 * t333 * t179 + t367 + 0.58482236226346462072622386637590534819724553404281e0 * t333 * t177 - t374 - t379
  vrho_0_ = t85 + t192 + t7 * (t1 * (t240 + t255) + t258 * (-t269 * t4 * t188 / 0.48e2 + t279 + t101 * t109 * t281 * (-t269 * t111 / 0.48e2 + t286 + params.gammac * t380) / 0.48e2) * t184 + t191 * t380)
  t393 = -t8 - t194
  t394 = f.my_piecewise5(t11, 0, t15, 0, t393)
  t397 = f.my_piecewise3(t21, 0, 0.4e1 / 0.3e1 * t24 * t394)
  t403 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t397 * t27 * t51 - t207)
  t404 = -t393
  t405 = f.my_piecewise5(t15, 0, t11, 0, t404)
  t408 = f.my_piecewise3(t59, 0, 0.4e1 / 0.3e1 * t60 * t405)
  t413 = t6 * t62
  t414 = xbspline(t78, 1, params)
  t415 = t27 * t414
  t423 = s2 ** 2
  t424 = t64 ** 2
  t429 = t74 ** 2
  t430 = 0.1e1 / t429
  t439 = f.my_piecewise3(t56, 0, -0.3e1 / 0.8e1 * t6 * t408 * t27 * t79 - t253 - 0.3e1 / 0.8e1 * t413 * t415 * (-t35 * s2 / t66 / t64 / r1 * t75 / 0.9e1 + t223 * t423 / t65 / t424 / t64 * t430 / 0.216e3))
  t444 = f.my_piecewise3(t87, 0, 0.2e1 / 0.3e1 * t259 * t393)
  t447 = f.my_piecewise3(t93, 0, 0.2e1 / 0.3e1 * t263 * t404)
  t450 = (t444 / 0.2e1 + t447 / 0.2e1) * t99
  t458 = f.my_piecewise3(t87, 0, 0.4e1 / 0.3e1 * t89 * t393)
  t461 = f.my_piecewise3(t93, 0, 0.4e1 / 0.3e1 * t94 * t404)
  t463 = (t458 + t461) * t154
  t468 = t292 + t316 - t320 - t325 + t145 * t463 * t179 + t367 + 0.58482236226346462072622386637590534819724553404281e0 * t463 * t177 - t374 - t379
  vrho_1_ = t85 + t192 + t7 * (t1 * (t403 + t439) + t258 * (-t450 * t4 * t188 / 0.48e2 + t279 + t101 * t109 * t281 * (-t450 * t111 / 0.48e2 + t286 + params.gammac * t468) / 0.48e2) * t184 + t191 * t468)
  t496 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t208 * t210 * (t30 * t34 * t40 * t47 / 0.24e2 - t223 * s0 / t37 / t225 / r0 * t231 / 0.576e3))
  t498 = t104 * t108
  t499 = 0.1e1 / t102
  t504 = t98 ** 2
  t506 = t4 ** 2
  t507 = t504 * t3 * t506
  t511 = t105 * t104 / t131 / t143
  vsigma_0_ = t7 * (t1 * t496 + t258 * (-t101 * t498 * t187 * t499 / 0.48e2 - t507 * t511 * t281 * t499 / 0.768e3) * t184)
  vsigma_1_ = 0.0e0
  t535 = f.my_piecewise3(t56, 0, -0.3e1 / 0.8e1 * t413 * t415 * (t30 * t34 * t68 * t75 / 0.24e2 - t223 * s2 / t65 / t424 / r1 * t430 / 0.576e3))
  t537 = 0.1e1 / t103
  vsigma_2_ = t7 * (t1 * t535 + t258 * (-t101 * t498 * t187 * t537 / 0.48e2 - t507 * t511 * t281 * t537 / 0.768e3) * t184)
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
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))
  params_gammac_raw = params.gammac
  if isinstance(params_gammac_raw, (str, bytes, dict)):
    params_gammac = params_gammac_raw
  else:
    try:
      params_gammac_seq = list(params_gammac_raw)
    except TypeError:
      params_gammac = params_gammac_raw
    else:
      params_gammac_seq = np.asarray(params_gammac_seq, dtype=np.float64)
      params_gammac = np.concatenate((np.array([np.nan], dtype=np.float64), params_gammac_seq))
  params_gammax_raw = params.gammax
  if isinstance(params_gammax_raw, (str, bytes, dict)):
    params_gammax = params_gammax_raw
  else:
    try:
      params_gammax_seq = list(params_gammax_raw)
    except TypeError:
      params_gammax = params_gammax_raw
    else:
      params_gammax_seq = np.asarray(params_gammax_seq, dtype=np.float64)
      params_gammax = np.concatenate((np.array([np.nan], dtype=np.float64), params_gammax_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  case21_ux0 = lambda s: params_gammax * s ** 2 / (1 + params_gammax * s ** 2)

  case21_t = lambda rs, z, xs0, xs1: (jnp.pi / 3) ** (1 / 6) * (xs0 * f.n_spin(rs, z) ** (4 / 3) + xs1 * f.n_spin(rs, -z) ** (4 / 3)) / (4 * f.n_total(rs) ** (7 / 6) * f.mphi(z))

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  case21_fx = lambda x: xbspline(case21_ux0(X2S * x), 0, params)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  case21_Ex = lambda rs, z, xs0, xs1: gga_exchange(f, params, case21_fx, rs, z, xs0, xs1)

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  case21_uc = lambda rs, z, xs0, xs1: -f.mphi(z) ** 3 * case21_t(rs, z, xs0, xs1) ** 2 / (-f.mphi(z) ** 3 * case21_t(rs, z, xs0, xs1) ** 2 + params_gammac * f_pw(rs, z))

  case21_Ec = lambda rs, z, xs0, xs1: cbspline(case21_uc(rs, z, xs0, xs1), 0, params) * f_pw(rs, z)

  f_case21 = lambda rs, z, xt, xs0, xs1: (1 - params_ax) * case21_Ex(rs, z, xs0, xs1) + case21_Ec(rs, z, xs0, xs1)

  functional_body = lambda rs, z, xt, xs0, xs1: f_case21(rs, z, xt, xs0, xs1)

  t1 = 0.1e1 - params.ax
  t3 = r0 / 0.2e1 <= f.p.dens_threshold
  t4 = 3 ** (0.1e1 / 0.3e1)
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 / t5
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 * f.p.zeta_threshold
  t16 = t12 ** (0.1e1 / 0.3e1)
  t18 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15, t16 * t12)
  t19 = r0 ** (0.1e1 / 0.3e1)
  t21 = 6 ** (0.1e1 / 0.3e1)
  t23 = jnp.pi ** 2
  t24 = t23 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t27 = params.gammax * t21 / t25
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = s0 * t29
  t31 = r0 ** 2
  t32 = t19 ** 2
  t34 = 0.1e1 / t32 / t31
  t38 = 0.1e1 + t27 * t30 * t34 / 0.24e2
  t39 = 0.1e1 / t38
  t43 = t27 * t30 * t34 * t39 / 0.24e2
  t44 = xbspline(t43, 0, params)
  t48 = f.my_piecewise3(t3, 0, -0.3e1 / 0.8e1 * t7 * t18 * t19 * t44)
  t51 = t14 ** 2
  t52 = f.my_piecewise3(t8, t51, 1)
  t53 = t4 ** 2
  t54 = t52 * t53
  t55 = t54 * t5
  t57 = 0.1e1 / t19 / t31
  t58 = s0 * t57
  t59 = t5 * s0
  t64 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t65 = t4 * t64
  t66 = 4 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t70 = t65 * t67 / t19
  t72 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t70
  t73 = jnp.sqrt(t70)
  t76 = t70 ** 0.15e1
  t78 = t64 ** 2
  t79 = t53 * t78
  t80 = 0.1e1 / t32
  t82 = t79 * t66 * t80
  t84 = 0.23615562999000000000000000000000000000000000000000e0 * t73 + 0.55770497660000000000000000000000000000000000000000e-1 * t70 + 0.12733196185000000000000000000000000000000000000000e-1 * t76 + 0.76629248290000000000000000000000000000000000000000e-2 * t82
  t86 = 0.1e1 + 0.1e1 / t84
  t87 = jnp.log(t86)
  t89 = f.my_piecewise3(t8, t15, 1)
  t95 = (0.2e1 * t89 - 0.2e1) / (0.2e1 * t28 - 0.2e1)
  t97 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t70
  t102 = 0.17489762330000000000000000000000000000000000000000e0 * t73 + 0.30591463695000000000000000000000000000000000000000e-1 * t70 + 0.37162156485000000000000000000000000000000000000000e-2 * t76 + 0.41939460495000000000000000000000000000000000000000e-2 * t82
  t104 = 0.1e1 + 0.1e1 / t102
  t105 = jnp.log(t104)
  t109 = -t72 * t87 + 0.58482236226346462072622386637590534819724553404281e0 * t95 * t97 * t105
  t111 = -t54 * t59 * t57 / 0.48e2 + params.gammac * t109
  t112 = 0.1e1 / t111
  t115 = t55 * t58 * t112 / 0.48e2
  t116 = cbspline(-t115, 0, params)
  t122 = t7 * t18
  t123 = xbspline(t43, 1, params)
  t124 = t19 * t123
  t125 = t31 * r0
  t132 = params.gammax ** 2
  t133 = t21 ** 2
  t137 = t132 * t133 / t24 / t23
  t138 = s0 ** 2
  t140 = t31 ** 2
  t144 = t38 ** 2
  t145 = 0.1e1 / t144
  t155 = f.my_piecewise3(t3, 0, -t7 * t18 * t80 * t44 / 0.8e1 - 0.3e1 / 0.8e1 * t122 * t124 * (-t27 * t30 / t32 / t125 * t39 / 0.9e1 + t137 * t138 * t28 / t19 / t140 / t31 * t145 / 0.108e3))
  t158 = cbspline(-t115, 1, params)
  t160 = 0.1e1 / t19 / t125
  t165 = t111 ** 2
  t166 = 0.1e1 / t165
  t171 = 0.1e1 / t19 / r0
  t172 = t67 * t171
  t176 = t84 ** 2
  t181 = t64 * t67
  t182 = t181 * t171
  t183 = 0.1e1 / t73 * t4 * t182
  t185 = t65 * t172
  t187 = t70 ** 0.5e0
  t189 = t187 * t4 * t182
  t194 = t79 * t66 / t32 / r0
  t206 = t102 ** 2
  t218 = 0.11073470983333333333333333333333333333333333333333e-2 * t65 * t172 * t87 + t72 / t176 * (-0.39359271665000000000000000000000000000000000000000e-1 * t183 - 0.18590165886666666666666666666666666666666666666667e-1 * t185 - 0.63665980925000000000000000000000000000000000000000e-2 * t189 - 0.51086165526666666666666666666666666666666666666667e-2 * t194) / t86 - 0.18311447306006545054854346104378990962041954983034e-3 * t95 * t4 * t181 * t171 * t105 - 0.58482236226346462072622386637590534819724553404281e0 * t95 * t97 / t206 * (-0.29149603883333333333333333333333333333333333333333e-1 * t183 - 0.10197154565000000000000000000000000000000000000000e-1 * t185 - 0.18581078242500000000000000000000000000000000000000e-2 * t189 - 0.27959640330000000000000000000000000000000000000000e-2 * t194) / t104
  vrho_0_ = 0.2e1 * t1 * t48 + t116 * t109 + r0 * (0.2e1 * t1 * t155 + t158 * (0.7e1 / 0.144e3 * t55 * s0 * t160 * t112 + t55 * t58 * t166 * (0.7e1 / 0.144e3 * t54 * t59 * t160 + params.gammac * t218) / 0.48e2) * t109 + t116 * t218)
  t247 = f.my_piecewise3(t3, 0, -0.3e1 / 0.8e1 * t122 * t124 * (t27 * t29 * t34 * t39 / 0.24e2 - t137 * s0 * t28 / t19 / t140 / r0 * t145 / 0.288e3))
  t254 = t52 ** 2
  t256 = t5 ** 2
  vsigma_0_ = r0 * (0.2e1 * t1 * t247 + t158 * (-t54 * t5 * t57 * t112 / 0.48e2 - t254 * t4 * t256 * s0 / t32 / t140 * t166 / 0.768e3) * t109)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = 0.1e1 - params.ax
  t3 = r0 / 0.2e1 <= f.p.dens_threshold
  t4 = 3 ** (0.1e1 / 0.3e1)
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 / t5
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 * f.p.zeta_threshold
  t16 = t12 ** (0.1e1 / 0.3e1)
  t18 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15, t16 * t12)
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t23 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t29 = params.gammax * t23 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t20 / t33
  t39 = 0.1e1 + t29 * t32 * t35 / 0.24e2
  t40 = 0.1e1 / t39
  t44 = t29 * t32 * t35 * t40 / 0.24e2
  t45 = xbspline(t44, 0, params)
  t49 = t7 * t18
  t50 = xbspline(t44, 1, params)
  t51 = t19 * t50
  t52 = t33 * r0
  t54 = 0.1e1 / t20 / t52
  t59 = params.gammax ** 2
  t60 = t23 ** 2
  t64 = t59 * t60 / t26 / t25
  t65 = s0 ** 2
  t66 = t65 * t30
  t67 = t33 ** 2
  t70 = 0.1e1 / t19 / t67 / t33
  t71 = t39 ** 2
  t72 = 0.1e1 / t71
  t77 = -t29 * t32 * t54 * t40 / 0.9e1 + t64 * t66 * t70 * t72 / 0.108e3
  t82 = f.my_piecewise3(t3, 0, -t7 * t18 * t21 * t45 / 0.8e1 - 0.3e1 / 0.8e1 * t49 * t51 * t77)
  t85 = t14 ** 2
  t86 = f.my_piecewise3(t8, t85, 1)
  t87 = t4 ** 2
  t88 = t86 * t87
  t89 = t88 * t5
  t91 = 0.1e1 / t19 / t33
  t92 = s0 * t91
  t93 = t5 * s0
  t98 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t99 = t4 * t98
  t100 = 4 ** (0.1e1 / 0.3e1)
  t101 = t100 ** 2
  t104 = t99 * t101 / t19
  t106 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t104
  t107 = jnp.sqrt(t104)
  t110 = t104 ** 0.15e1
  t112 = t98 ** 2
  t113 = t87 * t112
  t115 = t113 * t100 * t21
  t117 = 0.37978500000000000000000000000000000000000000000000e1 * t107 + 0.89690000000000000000000000000000000000000000000000e0 * t104 + 0.20477500000000000000000000000000000000000000000000e0 * t110 + 0.12323500000000000000000000000000000000000000000000e0 * t115
  t120 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t117
  t121 = jnp.log(t120)
  t124 = f.my_piecewise3(t8, t15, 1)
  t130 = (0.2e1 * t124 - 0.2e1) / (0.2e1 * t30 - 0.2e1)
  t132 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t104
  t137 = 0.51785000000000000000000000000000000000000000000000e1 * t107 + 0.90577500000000000000000000000000000000000000000000e0 * t104 + 0.11003250000000000000000000000000000000000000000000e0 * t110 + 0.12417750000000000000000000000000000000000000000000e0 * t115
  t140 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t137
  t141 = jnp.log(t140)
  t145 = -0.621814e-1 * t106 * t121 + 0.19751673498613801407483339618206552048944131217655e-1 * t130 * t132 * t141
  t147 = -t88 * t93 * t91 / 0.48e2 + params.gammac * t145
  t148 = 0.1e1 / t147
  t151 = t89 * t92 * t148 / 0.48e2
  t152 = cbspline(-t151, 1, params)
  t154 = 0.1e1 / t19 / t52
  t155 = s0 * t154
  t159 = t147 ** 2
  t160 = 0.1e1 / t159
  t165 = 0.1e1 / t19 / r0
  t166 = t101 * t165
  t170 = t117 ** 2
  t171 = 0.1e1 / t170
  t172 = t106 * t171
  t174 = 0.1e1 / t107 * t4
  t175 = t98 * t101
  t176 = t175 * t165
  t177 = t174 * t176
  t179 = t99 * t166
  t181 = t104 ** 0.5e0
  t182 = t181 * t4
  t183 = t182 * t176
  t186 = 0.1e1 / t20 / r0
  t188 = t113 * t100 * t186
  t190 = -0.63297500000000000000000000000000000000000000000000e0 * t177 - 0.29896666666666666666666666666666666666666666666667e0 * t179 - 0.10238750000000000000000000000000000000000000000000e0 * t183 - 0.82156666666666666666666666666666666666666666666667e-1 * t188
  t191 = 0.1e1 / t120
  t192 = t190 * t191
  t195 = t130 * t4
  t200 = t130 * t132
  t201 = t137 ** 2
  t202 = 0.1e1 / t201
  t207 = -0.86308333333333333333333333333333333333333333333334e0 * t177 - 0.30192500000000000000000000000000000000000000000000e0 * t179 - 0.55016250000000000000000000000000000000000000000000e-1 * t183 - 0.82785000000000000000000000000000000000000000000000e-1 * t188
  t209 = 0.1e1 / t140
  t210 = t202 * t207 * t209
  t213 = 0.11073470983333333333333333333333333333333333333333e-2 * t99 * t166 * t121 + 0.10000000000000000000000000000000000000000000000000e1 * t172 * t192 - 0.18311447306006545054854346104378990962041954983034e-3 * t195 * t175 * t165 * t141 - 0.58482236226346462072622386637590534819724553404280e0 * t200 * t210
  t215 = 0.7e1 / 0.144e3 * t88 * t93 * t154 + params.gammac * t213
  t216 = t160 * t215
  t220 = 0.7e1 / 0.144e3 * t89 * t155 * t148 + t89 * t92 * t216 / 0.48e2
  t221 = t152 * t220
  t224 = cbspline(-t151, 0, params)
  t231 = t21 * t50
  t235 = xbspline(t44, 2, params)
  t236 = t19 * t235
  t237 = t77 ** 2
  t242 = 0.1e1 / t20 / t67
  t247 = t67 * t52
  t255 = t25 ** 2
  t257 = t59 * params.gammax / t255
  t259 = t67 ** 2
  t264 = 0.1e1 / t71 / t39
  t273 = f.my_piecewise3(t3, 0, t7 * t18 * t186 * t45 / 0.12e2 - t49 * t231 * t77 / 0.4e1 - 0.3e1 / 0.8e1 * t49 * t236 * t237 - 0.3e1 / 0.8e1 * t49 * t51 * (0.11e2 / 0.27e2 * t29 * t32 * t242 * t40 - t64 * t66 / t19 / t247 * t72 / 0.12e2 + 0.2e1 / 0.81e2 * t257 * t65 * s0 / t259 / t33 * t264))
  t276 = cbspline(-t151, 2, params)
  t277 = t220 ** 2
  t281 = 0.1e1 / t19 / t67
  t290 = 0.1e1 / t159 / t147
  t291 = t215 ** 2
  t299 = t101 * t91
  t311 = t190 ** 2
  t319 = t112 * t100 * t35
  t320 = 0.1e1 / t107 / t104 * t87 * t319
  t322 = t175 * t91
  t323 = t174 * t322
  t325 = t99 * t299
  t327 = t104 ** (-0.5e0)
  t329 = t327 * t87 * t319
  t331 = t182 * t322
  t334 = t113 * t100 * t35
  t340 = t170 ** 2
  t343 = t120 ** 2
  t358 = t207 ** 2
  t374 = t201 ** 2
  t377 = t140 ** 2
  t382 = -0.14764627977777777777777777777777777777777777777777e-2 * t99 * t299 * t121 - 0.35616666666666666666666666666666666666666666666666e-1 * t99 * t101 * t165 * t171 * t192 - 0.20000000000000000000000000000000000000000000000000e1 * t106 / t170 / t117 * t311 * t191 + 0.10000000000000000000000000000000000000000000000000e1 * t172 * (-0.42198333333333333333333333333333333333333333333333e0 * t320 + 0.84396666666666666666666666666666666666666666666666e0 * t323 + 0.39862222222222222222222222222222222222222222222223e0 * t325 + 0.68258333333333333333333333333333333333333333333333e-1 * t329 + 0.13651666666666666666666666666666666666666666666667e0 * t331 + 0.13692777777777777777777777777777777777777777777778e0 * t334) * t191 + 0.16081979498692535066756296899072713062105388428051e2 * t106 / t340 * t311 / t343 + 0.24415263074675393406472461472505321282722606644045e-3 * t195 * t175 * t91 * t141 + 0.10843581300301739842632067522386578331157260943710e-1 * t130 * t99 * t166 * t210 + 0.11696447245269292414524477327518106963944910680856e1 * t200 / t201 / t137 * t358 * t209 - 0.58482236226346462072622386637590534819724553404280e0 * t200 * t202 * (-0.57538888888888888888888888888888888888888888888889e0 * t320 + 0.11507777777777777777777777777777777777777777777778e1 * t323 + 0.40256666666666666666666666666666666666666666666667e0 * t325 + 0.36677500000000000000000000000000000000000000000000e-1 * t329 + 0.73355000000000000000000000000000000000000000000000e-1 * t331 + 0.13797500000000000000000000000000000000000000000000e0 * t334) * t209 - 0.17315859105681463759666483083807725165579399831905e2 * t200 / t374 * t358 / t377
  v2rho2_0_ = 0.4e1 * t1 * t82 + 0.2e1 * t221 * t145 + 0.2e1 * t224 * t213 + r0 * (0.2e1 * t1 * t273 + t276 * t277 * t145 + t152 * (-0.35e2 / 0.216e3 * t89 * s0 * t281 * t148 - 0.7e1 / 0.72e2 * t89 * t155 * t216 - t89 * t92 * t290 * t291 / 0.24e2 + t89 * t92 * t160 * (-0.35e2 / 0.216e3 * t88 * t93 * t281 + params.gammac * t382) / 0.48e2) * t145 + 0.2e1 * t221 * t213 + t224 * t382)
  t402 = t67 * r0
  t404 = 0.1e1 / t19 / t402
  t409 = t29 * t31 * t35 * t40 / 0.24e2 - t64 * s0 * t30 * t404 * t72 / 0.288e3
  t413 = f.my_piecewise3(t3, 0, -0.3e1 / 0.8e1 * t49 * t51 * t409)
  t420 = t86 ** 2
  t421 = t420 * t4
  t422 = t5 ** 2
  t423 = t421 * t422
  t424 = s0 * t242
  t428 = -t88 * t5 * t91 * t148 / 0.48e2 - t423 * t424 * t160 / 0.768e3
  t429 = t152 * t428
  t458 = f.my_piecewise3(t3, 0, -t49 * t231 * t409 / 0.8e1 - 0.3e1 / 0.8e1 * t49 * t236 * t77 * t409 - 0.3e1 / 0.8e1 * t49 * t51 * (-t29 * t31 * t54 * t40 / 0.9e1 + t64 * t30 * t70 * t72 * s0 / 0.36e2 - t257 * t65 / t259 / r0 * t264 / 0.108e3))
  v2rhosigma_0_ = 0.2e1 * t1 * t413 + t429 * t145 + r0 * (0.2e1 * t1 * t458 + t276 * t220 * t428 * t145 + t152 * (0.7e1 / 0.144e3 * t88 * t5 * t154 * t148 + t89 * t91 * t160 * t215 / 0.48e2 + 0.7e1 / 0.1152e4 * t423 * s0 / t20 / t402 * t160 + t423 * t424 * t290 * t215 / 0.384e3) * t145 + t429 * t213)
  t488 = t409 ** 2
  t505 = f.my_piecewise3(t3, 0, -0.3e1 / 0.8e1 * t49 * t236 * t488 - 0.3e1 / 0.8e1 * t49 * t51 * (-t64 * t30 * t404 * t72 / 0.144e3 + t257 * s0 / t259 * t264 / 0.288e3))
  t508 = t428 ** 2
  v2sigma2_0_ = r0 * (0.2e1 * t1 * t505 + t276 * t508 * t145 + t152 * (-t421 * t422 * t242 * t160 / 0.384e3 - t420 * t86 * jnp.pi * s0 / t247 * t290 / 0.6144e4) * t145)
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 0.1e1 - params.ax
  t3 = r0 / 0.2e1 <= f.p.dens_threshold
  t4 = 3 ** (0.1e1 / 0.3e1)
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 / t5
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 * f.p.zeta_threshold
  t16 = t12 ** (0.1e1 / 0.3e1)
  t18 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15, t16 * t12)
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / r0
  t24 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = params.gammax * t24 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t36 = 0.1e1 / t20 / t34
  t40 = 0.1e1 + t30 * t33 * t36 / 0.24e2
  t41 = 0.1e1 / t40
  t45 = t30 * t33 * t36 * t41 / 0.24e2
  t46 = xbspline(t45, 0, params)
  t50 = t7 * t18
  t51 = 0.1e1 / t20
  t52 = xbspline(t45, 1, params)
  t53 = t51 * t52
  t54 = t34 * r0
  t56 = 0.1e1 / t20 / t54
  t61 = params.gammax ** 2
  t62 = t24 ** 2
  t66 = t61 * t62 / t27 / t26
  t67 = s0 ** 2
  t68 = t67 * t31
  t69 = t34 ** 2
  t73 = t40 ** 2
  t74 = 0.1e1 / t73
  t79 = -t30 * t33 * t56 * t41 / 0.9e1 + t66 * t68 / t19 / t69 / t34 * t74 / 0.108e3
  t83 = xbspline(t45, 2, params)
  t84 = t19 * t83
  t85 = t79 ** 2
  t89 = t19 * t52
  t104 = t26 ** 2
  t105 = 0.1e1 / t104
  t106 = t61 * params.gammax * t105
  t107 = t67 * s0
  t108 = t69 ** 2
  t113 = 0.1e1 / t73 / t40
  t117 = 0.11e2 / 0.27e2 * t30 * t33 / t20 / t69 * t41 - t66 * t68 / t19 / t69 / t54 * t74 / 0.12e2 + 0.2e1 / 0.81e2 * t106 * t107 / t108 / t34 * t113
  t122 = f.my_piecewise3(t3, 0, t7 * t18 * t22 * t46 / 0.12e2 - t50 * t53 * t79 / 0.4e1 - 0.3e1 / 0.8e1 * t50 * t84 * t85 - 0.3e1 / 0.8e1 * t50 * t89 * t117)
  t125 = t14 ** 2
  t126 = f.my_piecewise3(t8, t125, 1)
  t127 = t4 ** 2
  t128 = t126 * t127
  t129 = t128 * t5
  t131 = 0.1e1 / t19 / t34
  t132 = s0 * t131
  t133 = t5 * s0
  t137 = 0.1e1 / jnp.pi
  t138 = t137 ** (0.1e1 / 0.3e1)
  t139 = t4 * t138
  t140 = 4 ** (0.1e1 / 0.3e1)
  t141 = t140 ** 2
  t144 = t139 * t141 / t19
  t146 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t144
  t147 = jnp.sqrt(t144)
  t150 = t144 ** 0.15e1
  t152 = t138 ** 2
  t153 = t127 * t152
  t155 = t153 * t140 * t51
  t157 = 0.37978500000000000000000000000000000000000000000000e1 * t147 + 0.89690000000000000000000000000000000000000000000000e0 * t144 + 0.20477500000000000000000000000000000000000000000000e0 * t150 + 0.12323500000000000000000000000000000000000000000000e0 * t155
  t160 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t157
  t161 = jnp.log(t160)
  t164 = f.my_piecewise3(t8, t15, 1)
  t170 = (0.2e1 * t164 - 0.2e1) / (0.2e1 * t31 - 0.2e1)
  t172 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t144
  t177 = 0.51785000000000000000000000000000000000000000000000e1 * t147 + 0.90577500000000000000000000000000000000000000000000e0 * t144 + 0.11003250000000000000000000000000000000000000000000e0 * t150 + 0.12417750000000000000000000000000000000000000000000e0 * t155
  t180 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t177
  t181 = jnp.log(t180)
  t185 = -0.621814e-1 * t146 * t161 + 0.19751673498613801407483339618206552048944131217655e-1 * t170 * t172 * t181
  t187 = -t128 * t133 * t131 / 0.48e2 + params.gammac * t185
  t188 = 0.1e1 / t187
  t191 = t129 * t132 * t188 / 0.48e2
  t192 = cbspline(-t191, 2, params)
  t194 = 0.1e1 / t19 / t54
  t195 = s0 * t194
  t199 = t187 ** 2
  t200 = 0.1e1 / t199
  t205 = 0.1e1 / t19 / r0
  t206 = t141 * t205
  t210 = t157 ** 2
  t211 = 0.1e1 / t210
  t212 = t146 * t211
  t214 = 0.1e1 / t147 * t4
  t215 = t138 * t141
  t216 = t215 * t205
  t217 = t214 * t216
  t219 = t139 * t206
  t221 = t144 ** 0.5e0
  t222 = t221 * t4
  t223 = t222 * t216
  t226 = t153 * t140 * t22
  t228 = -0.63297500000000000000000000000000000000000000000000e0 * t217 - 0.29896666666666666666666666666666666666666666666667e0 * t219 - 0.10238750000000000000000000000000000000000000000000e0 * t223 - 0.82156666666666666666666666666666666666666666666667e-1 * t226
  t229 = 0.1e1 / t160
  t230 = t228 * t229
  t233 = t170 * t4
  t238 = t170 * t172
  t239 = t177 ** 2
  t240 = 0.1e1 / t239
  t245 = -0.86308333333333333333333333333333333333333333333334e0 * t217 - 0.30192500000000000000000000000000000000000000000000e0 * t219 - 0.55016250000000000000000000000000000000000000000000e-1 * t223 - 0.82785000000000000000000000000000000000000000000000e-1 * t226
  t247 = 0.1e1 / t180
  t248 = t240 * t245 * t247
  t251 = 0.11073470983333333333333333333333333333333333333333e-2 * t139 * t206 * t161 + 0.10000000000000000000000000000000000000000000000000e1 * t212 * t230 - 0.18311447306006545054854346104378990962041954983034e-3 * t233 * t215 * t205 * t181 - 0.58482236226346462072622386637590534819724553404280e0 * t238 * t248
  t253 = 0.7e1 / 0.144e3 * t128 * t133 * t194 + params.gammac * t251
  t254 = t200 * t253
  t258 = 0.7e1 / 0.144e3 * t129 * t195 * t188 + t129 * t132 * t254 / 0.48e2
  t259 = t258 ** 2
  t260 = t192 * t259
  t263 = cbspline(-t191, 1, params)
  t265 = 0.1e1 / t19 / t69
  t266 = s0 * t265
  t274 = 0.1e1 / t199 / t187
  t275 = t253 ** 2
  t276 = t274 * t275
  t283 = t141 * t131
  t287 = t139 * t141
  t288 = t205 * t211
  t293 = 0.1e1 / t210 / t157
  t294 = t146 * t293
  t295 = t228 ** 2
  t296 = t295 * t229
  t301 = 0.1e1 / t147 / t144 * t127
  t302 = t152 * t140
  t303 = t302 * t36
  t304 = t301 * t303
  t306 = t215 * t131
  t307 = t214 * t306
  t309 = t139 * t283
  t311 = t144 ** (-0.5e0)
  t312 = t311 * t127
  t313 = t312 * t303
  t315 = t222 * t306
  t318 = t153 * t140 * t36
  t320 = -0.42198333333333333333333333333333333333333333333333e0 * t304 + 0.84396666666666666666666666666666666666666666666666e0 * t307 + 0.39862222222222222222222222222222222222222222222223e0 * t309 + 0.68258333333333333333333333333333333333333333333333e-1 * t313 + 0.13651666666666666666666666666666666666666666666667e0 * t315 + 0.13692777777777777777777777777777777777777777777778e0 * t318
  t321 = t320 * t229
  t324 = t210 ** 2
  t325 = 0.1e1 / t324
  t326 = t146 * t325
  t327 = t160 ** 2
  t328 = 0.1e1 / t327
  t329 = t295 * t328
  t336 = t170 * t139
  t341 = 0.1e1 / t239 / t177
  t342 = t245 ** 2
  t344 = t341 * t342 * t247
  t353 = -0.57538888888888888888888888888888888888888888888889e0 * t304 + 0.11507777777777777777777777777777777777777777777778e1 * t307 + 0.40256666666666666666666666666666666666666666666667e0 * t309 + 0.36677500000000000000000000000000000000000000000000e-1 * t313 + 0.73355000000000000000000000000000000000000000000000e-1 * t315 + 0.13797500000000000000000000000000000000000000000000e0 * t318
  t355 = t240 * t353 * t247
  t358 = t239 ** 2
  t359 = 0.1e1 / t358
  t361 = t180 ** 2
  t362 = 0.1e1 / t361
  t363 = t359 * t342 * t362
  t366 = -0.14764627977777777777777777777777777777777777777777e-2 * t139 * t283 * t161 - 0.35616666666666666666666666666666666666666666666666e-1 * t287 * t288 * t230 - 0.20000000000000000000000000000000000000000000000000e1 * t294 * t296 + 0.10000000000000000000000000000000000000000000000000e1 * t212 * t321 + 0.16081979498692535066756296899072713062105388428051e2 * t326 * t329 + 0.24415263074675393406472461472505321282722606644045e-3 * t233 * t215 * t131 * t181 + 0.10843581300301739842632067522386578331157260943710e-1 * t336 * t206 * t248 + 0.11696447245269292414524477327518106963944910680856e1 * t238 * t344 - 0.58482236226346462072622386637590534819724553404280e0 * t238 * t355 - 0.17315859105681463759666483083807725165579399831905e2 * t238 * t363
  t368 = -0.35e2 / 0.216e3 * t128 * t133 * t265 + params.gammac * t366
  t369 = t200 * t368
  t373 = -0.35e2 / 0.216e3 * t129 * t266 * t188 - 0.7e1 / 0.72e2 * t129 * t195 * t254 - t129 * t132 * t276 / 0.24e2 + t129 * t132 * t369 / 0.48e2
  t374 = t263 * t373
  t377 = t263 * t258
  t380 = cbspline(-t191, 0, params)
  t398 = xbspline(t45, 3, params)
  t408 = t69 * r0
  t427 = t61 ** 2
  t429 = t67 ** 2
  t435 = t73 ** 2
  t447 = f.my_piecewise3(t3, 0, -0.5e1 / 0.36e2 * t7 * t18 * t36 * t46 + t50 * t22 * t52 * t79 / 0.4e1 - 0.3e1 / 0.8e1 * t50 * t51 * t83 * t85 - 0.3e1 / 0.8e1 * t50 * t53 * t117 - 0.3e1 / 0.8e1 * t50 * t19 * t398 * t85 * t79 - 0.9e1 / 0.8e1 * t50 * t84 * t79 * t117 - 0.3e1 / 0.8e1 * t50 * t89 * (-0.154e3 / 0.81e2 * t30 * t33 / t20 / t408 * t41 + 0.341e3 / 0.486e3 * t66 * t68 / t19 / t108 * t74 - 0.38e2 / 0.81e2 * t106 * t107 / t108 / t54 * t113 + 0.2e1 / 0.243e3 * t427 * t105 * t429 / t20 / t108 / t408 / t435 * t24 * t29 * t32))
  t450 = cbspline(-t191, 3, params)
  t461 = 0.1e1 / t19 / t408
  t475 = t199 ** 2
  t496 = t342 * t245
  t524 = 0.1e1 / t69
  t525 = 0.1e1 / t147 / t155 * t137 * t524 / 0.4e1
  t527 = t302 * t56
  t528 = t301 * t527
  t530 = t215 * t194
  t531 = t214 * t530
  t533 = t141 * t194
  t534 = t139 * t533
  t536 = t144 ** (-0.15e1)
  t538 = t536 * t137 * t524
  t540 = t312 * t527
  t542 = t222 * t530
  t545 = t153 * t140 * t56
  t559 = t295 * t228
  t571 = -0.51947577317044391278999449251423175496738199495715e2 * t238 * t359 * t353 * t362 * t245 - 0.35089341735807877243573431982554320891834732042568e1 * t238 * t359 * t496 * t247 + 0.35089341735807877243573431982554320891834732042568e1 * t238 * t341 * t245 * t247 * t353 - 0.10254018858216406658218194626490193680059335835414e4 * t238 / t358 / t239 * t496 / t361 / t180 + 0.10389515463408878255799889850284635099347639899143e3 * t238 / t358 / t177 * t496 * t362 - 0.58482236226346462072622386637590534819724553404280e0 * t238 * t240 * (-0.34523333333333333333333333333333333333333333333333e1 * t525 + 0.23015555555555555555555555555555555555555555555556e1 * t528 - 0.26851481481481481481481481481481481481481481481482e1 * t531 - 0.93932222222222222222222222222222222222222222222223e0 * t534 + 0.73355000000000000000000000000000000000000000000000e-1 * t538 - 0.14671000000000000000000000000000000000000000000000e0 * t540 - 0.17116166666666666666666666666666666666666666666667e0 * t542 - 0.36793333333333333333333333333333333333333333333333e0 * t545) * t247 + 0.48245938496077605200268890697218139186316165284153e2 * t326 * t320 * t328 * t228 - 0.60000000000000000000000000000000000000000000000000e1 * t294 * t230 * t320 + 0.60000000000000000000000000000000000000000000000000e1 * t326 * t559 * t229 + 0.10685000000000000000000000000000000000000000000000e0 * t287 * t205 * t293 * t296 - 0.56968947174242584615102410102512416326352748836105e-3 * t233 * t215 * t194 * t181
  t624 = 0.51726012919273400298984252201052768390886626637712e3 * t146 / t324 / t210 * t559 / t327 / t160 + 0.10000000000000000000000000000000000000000000000000e1 * t212 * (-0.25319000000000000000000000000000000000000000000000e1 * t525 + 0.16879333333333333333333333333333333333333333333333e1 * t528 - 0.19692555555555555555555555555555555555555555555555e1 * t531 - 0.93011851851851851851851851851851851851851851851854e0 * t534 + 0.13651666666666666666666666666666666666666666666667e0 * t538 - 0.27303333333333333333333333333333333333333333333333e0 * t540 - 0.31853888888888888888888888888888888888888888888890e0 * t542 - 0.36514074074074074074074074074074074074074074074075e0 * t545) * t229 - 0.96491876992155210400537781394436278372632330568306e2 * t146 / t324 / t157 * t559 * t328 - 0.32530743900905219527896202567159734993471782831130e-1 * t336 * t206 * t344 + 0.34450798614814814814814814814814814814814814814813e-2 * t139 * t533 * t161 - 0.21687162600603479685264135044773156662314521887420e-1 * t336 * t283 * t248 + 0.16265371950452609763948101283579867496735891415565e-1 * t336 * t206 * t355 + 0.48159733137676571081572406076840235616767705782485e0 * t336 * t206 * t363 - 0.85917975471764868594145516183295969534298037676861e0 * t287 * t205 * t325 * t329 + 0.71233333333333333333333333333333333333333333333331e-1 * t287 * t131 * t211 * t230 - 0.53424999999999999999999999999999999999999999999999e-1 * t287 * t288 * t321
  t625 = t571 + t624
  v3rho3_0_ = 0.6e1 * t1 * t122 + 0.3e1 * t260 * t185 + 0.3e1 * t374 * t185 + 0.6e1 * t377 * t251 + 0.3e1 * t380 * t366 + r0 * (0.2e1 * t1 * t447 + t450 * t259 * t258 * t185 + 0.3e1 * t192 * t258 * t185 * t373 + 0.3e1 * t260 * t251 + t263 * (0.455e3 / 0.648e3 * t129 * s0 * t461 * t188 + 0.35e2 / 0.72e2 * t129 * t266 * t254 + 0.7e1 / 0.24e2 * t129 * t195 * t276 - 0.7e1 / 0.48e2 * t129 * t195 * t369 + t129 * t132 / t475 * t275 * t253 / 0.8e1 - t128 * t133 * t131 * t274 * t253 * t368 / 0.8e1 + t129 * t132 * t200 * (0.455e3 / 0.648e3 * t128 * t133 * t461 + params.gammac * t625) / 0.48e2) * t185 + 0.3e1 * t374 * t251 + 0.3e1 * t377 * t366 + t380 * t625)

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 0.1e1 - params.ax
  t3 = r0 / 0.2e1 <= f.p.dens_threshold
  t4 = 3 ** (0.1e1 / 0.3e1)
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 / t5
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 * f.p.zeta_threshold
  t16 = t12 ** (0.1e1 / 0.3e1)
  t18 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15, t16 * t12)
  t19 = r0 ** 2
  t20 = r0 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t23 = 0.1e1 / t21 / t19
  t25 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = params.gammax * t25 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t38 = 0.1e1 + t31 * t34 * t23 / 0.24e2
  t39 = 0.1e1 / t38
  t43 = t31 * t34 * t23 * t39 / 0.24e2
  t44 = xbspline(t43, 0, params)
  t48 = t7 * t18
  t50 = 0.1e1 / t21 / r0
  t51 = xbspline(t43, 1, params)
  t52 = t50 * t51
  t53 = t19 * r0
  t55 = 0.1e1 / t21 / t53
  t60 = params.gammax ** 2
  t61 = t25 ** 2
  t64 = 0.1e1 / t28 / t27
  t65 = t60 * t61 * t64
  t66 = s0 ** 2
  t67 = t66 * t32
  t68 = t19 ** 2
  t69 = t68 * t19
  t71 = 0.1e1 / t20 / t69
  t72 = t38 ** 2
  t73 = 0.1e1 / t72
  t78 = -t31 * t34 * t55 * t39 / 0.9e1 + t65 * t67 * t71 * t73 / 0.108e3
  t82 = 0.1e1 / t21
  t83 = xbspline(t43, 2, params)
  t84 = t82 * t83
  t85 = t78 ** 2
  t89 = t82 * t51
  t91 = 0.1e1 / t21 / t68
  t104 = t27 ** 2
  t105 = 0.1e1 / t104
  t106 = t60 * params.gammax * t105
  t107 = t66 * s0
  t108 = t68 ** 2
  t113 = 0.1e1 / t72 / t38
  t117 = 0.11e2 / 0.27e2 * t31 * t34 * t91 * t39 - t65 * t67 / t20 / t68 / t53 * t73 / 0.12e2 + 0.2e1 / 0.81e2 * t106 * t107 / t108 / t19 * t113
  t121 = xbspline(t43, 3, params)
  t122 = t20 * t121
  t123 = t85 * t78
  t127 = t20 * t83
  t128 = t78 * t117
  t132 = t20 * t51
  t133 = t68 * r0
  t152 = t60 ** 2
  t153 = t152 * t105
  t154 = t66 ** 2
  t160 = t72 ** 2
  t164 = 0.1e1 / t160 * t25 * t30 * t33
  t167 = -0.154e3 / 0.81e2 * t31 * t34 / t21 / t133 * t39 + 0.341e3 / 0.486e3 * t65 * t67 / t20 / t108 * t73 - 0.38e2 / 0.81e2 * t106 * t107 / t108 / t53 * t113 + 0.2e1 / 0.243e3 * t153 * t154 / t21 / t108 / t133 * t164
  t172 = f.my_piecewise3(t3, 0, -0.5e1 / 0.36e2 * t7 * t18 * t23 * t44 + t48 * t52 * t78 / 0.4e1 - 0.3e1 / 0.8e1 * t48 * t84 * t85 - 0.3e1 / 0.8e1 * t48 * t89 * t117 - 0.3e1 / 0.8e1 * t48 * t122 * t123 - 0.9e1 / 0.8e1 * t48 * t127 * t128 - 0.3e1 / 0.8e1 * t48 * t132 * t167)
  t175 = t14 ** 2
  t176 = f.my_piecewise3(t8, t175, 1)
  t177 = t4 ** 2
  t178 = t176 * t177
  t179 = t178 * t5
  t181 = 0.1e1 / t20 / t19
  t182 = s0 * t181
  t183 = t5 * s0
  t187 = 0.1e1 / jnp.pi
  t188 = t187 ** (0.1e1 / 0.3e1)
  t189 = t4 * t188
  t190 = 4 ** (0.1e1 / 0.3e1)
  t191 = t190 ** 2
  t194 = t189 * t191 / t20
  t196 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t194
  t197 = jnp.sqrt(t194)
  t200 = t194 ** 0.15e1
  t202 = t188 ** 2
  t203 = t177 * t202
  t205 = t203 * t190 * t82
  t207 = 0.37978500000000000000000000000000000000000000000000e1 * t197 + 0.89690000000000000000000000000000000000000000000000e0 * t194 + 0.20477500000000000000000000000000000000000000000000e0 * t200 + 0.12323500000000000000000000000000000000000000000000e0 * t205
  t210 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t207
  t211 = jnp.log(t210)
  t214 = f.my_piecewise3(t8, t15, 1)
  t220 = (0.2e1 * t214 - 0.2e1) / (0.2e1 * t32 - 0.2e1)
  t222 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t194
  t227 = 0.51785000000000000000000000000000000000000000000000e1 * t197 + 0.90577500000000000000000000000000000000000000000000e0 * t194 + 0.11003250000000000000000000000000000000000000000000e0 * t200 + 0.12417750000000000000000000000000000000000000000000e0 * t205
  t230 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t227
  t231 = jnp.log(t230)
  t235 = -0.621814e-1 * t196 * t211 + 0.19751673498613801407483339618206552048944131217655e-1 * t220 * t222 * t231
  t237 = -t178 * t183 * t181 / 0.48e2 + params.gammac * t235
  t238 = 0.1e1 / t237
  t241 = t179 * t182 * t238 / 0.48e2
  t242 = cbspline(-t241, 3, params)
  t244 = 0.1e1 / t20 / t53
  t245 = s0 * t244
  t249 = t237 ** 2
  t250 = 0.1e1 / t249
  t255 = 0.1e1 / t20 / r0
  t256 = t191 * t255
  t260 = t207 ** 2
  t261 = 0.1e1 / t260
  t262 = t196 * t261
  t264 = 0.1e1 / t197 * t4
  t265 = t188 * t191
  t266 = t265 * t255
  t267 = t264 * t266
  t269 = t189 * t256
  t271 = t194 ** 0.5e0
  t272 = t271 * t4
  t273 = t272 * t266
  t276 = t203 * t190 * t50
  t278 = -0.63297500000000000000000000000000000000000000000000e0 * t267 - 0.29896666666666666666666666666666666666666666666667e0 * t269 - 0.10238750000000000000000000000000000000000000000000e0 * t273 - 0.82156666666666666666666666666666666666666666666667e-1 * t276
  t279 = 0.1e1 / t210
  t280 = t278 * t279
  t283 = t220 * t4
  t288 = t220 * t222
  t289 = t227 ** 2
  t290 = 0.1e1 / t289
  t295 = -0.86308333333333333333333333333333333333333333333334e0 * t267 - 0.30192500000000000000000000000000000000000000000000e0 * t269 - 0.55016250000000000000000000000000000000000000000000e-1 * t273 - 0.82785000000000000000000000000000000000000000000000e-1 * t276
  t297 = 0.1e1 / t230
  t298 = t290 * t295 * t297
  t301 = 0.11073470983333333333333333333333333333333333333333e-2 * t189 * t256 * t211 + 0.10000000000000000000000000000000000000000000000000e1 * t262 * t280 - 0.18311447306006545054854346104378990962041954983034e-3 * t283 * t265 * t255 * t231 - 0.58482236226346462072622386637590534819724553404280e0 * t288 * t298
  t303 = 0.7e1 / 0.144e3 * t178 * t183 * t244 + params.gammac * t301
  t304 = t250 * t303
  t308 = 0.7e1 / 0.144e3 * t179 * t245 * t238 + t179 * t182 * t304 / 0.48e2
  t309 = t308 ** 2
  t311 = t242 * t309 * t308
  t314 = cbspline(-t241, 2, params)
  t315 = t314 * t308
  t317 = 0.1e1 / t20 / t68
  t318 = s0 * t317
  t326 = 0.1e1 / t249 / t237
  t327 = t303 ** 2
  t328 = t326 * t327
  t335 = t191 * t181
  t339 = t189 * t191
  t340 = t255 * t261
  t344 = t260 * t207
  t345 = 0.1e1 / t344
  t346 = t196 * t345
  t347 = t278 ** 2
  t348 = t347 * t279
  t353 = 0.1e1 / t197 / t194 * t177
  t354 = t202 * t190
  t355 = t354 * t23
  t356 = t353 * t355
  t358 = t265 * t181
  t359 = t264 * t358
  t361 = t189 * t335
  t363 = t194 ** (-0.5e0)
  t364 = t363 * t177
  t365 = t364 * t355
  t367 = t272 * t358
  t370 = t203 * t190 * t23
  t372 = -0.42198333333333333333333333333333333333333333333333e0 * t356 + 0.84396666666666666666666666666666666666666666666666e0 * t359 + 0.39862222222222222222222222222222222222222222222223e0 * t361 + 0.68258333333333333333333333333333333333333333333333e-1 * t365 + 0.13651666666666666666666666666666666666666666666667e0 * t367 + 0.13692777777777777777777777777777777777777777777778e0 * t370
  t373 = t372 * t279
  t376 = t260 ** 2
  t377 = 0.1e1 / t376
  t378 = t196 * t377
  t379 = t210 ** 2
  t380 = 0.1e1 / t379
  t381 = t347 * t380
  t388 = t220 * t189
  t392 = t289 * t227
  t393 = 0.1e1 / t392
  t394 = t295 ** 2
  t396 = t393 * t394 * t297
  t405 = -0.57538888888888888888888888888888888888888888888889e0 * t356 + 0.11507777777777777777777777777777777777777777777778e1 * t359 + 0.40256666666666666666666666666666666666666666666667e0 * t361 + 0.36677500000000000000000000000000000000000000000000e-1 * t365 + 0.73355000000000000000000000000000000000000000000000e-1 * t367 + 0.13797500000000000000000000000000000000000000000000e0 * t370
  t407 = t290 * t405 * t297
  t410 = t289 ** 2
  t411 = 0.1e1 / t410
  t412 = t411 * t394
  t413 = t230 ** 2
  t414 = 0.1e1 / t413
  t415 = t412 * t414
  t418 = -0.14764627977777777777777777777777777777777777777777e-2 * t189 * t335 * t211 - 0.35616666666666666666666666666666666666666666666666e-1 * t339 * t340 * t280 - 0.20000000000000000000000000000000000000000000000000e1 * t346 * t348 + 0.10000000000000000000000000000000000000000000000000e1 * t262 * t373 + 0.16081979498692535066756296899072713062105388428051e2 * t378 * t381 + 0.24415263074675393406472461472505321282722606644045e-3 * t283 * t265 * t181 * t231 + 0.10843581300301739842632067522386578331157260943710e-1 * t388 * t256 * t298 + 0.11696447245269292414524477327518106963944910680856e1 * t288 * t396 - 0.58482236226346462072622386637590534819724553404280e0 * t288 * t407 - 0.17315859105681463759666483083807725165579399831905e2 * t288 * t415
  t420 = -0.35e2 / 0.216e3 * t178 * t183 * t317 + params.gammac * t418
  t421 = t250 * t420
  t425 = -0.35e2 / 0.216e3 * t179 * t318 * t238 - 0.7e1 / 0.72e2 * t179 * t245 * t304 - t179 * t182 * t328 / 0.24e2 + t179 * t182 * t421 / 0.48e2
  t426 = t235 * t425
  t429 = t314 * t309
  t432 = cbspline(-t241, 1, params)
  t434 = 0.1e1 / t20 / t133
  t435 = s0 * t434
  t448 = t249 ** 2
  t449 = 0.1e1 / t448
  t451 = t449 * t327 * t303
  t455 = t178 * t183
  t456 = t181 * t326
  t457 = t303 * t420
  t465 = t414 * t295
  t469 = t394 * t295
  t471 = t411 * t469 * t297
  t474 = t393 * t295
  t475 = t297 * t405
  t480 = 0.1e1 / t410 / t289
  t483 = 0.1e1 / t413 / t230
  t484 = t480 * t469 * t483
  t488 = 0.1e1 / t410 / t227
  t490 = t488 * t469 * t414
  t496 = 0.1e1 / t197 / t205 * t187 / 0.4e1
  t497 = 0.1e1 / t68
  t498 = t496 * t497
  t500 = t354 * t55
  t501 = t353 * t500
  t503 = t265 * t244
  t504 = t264 * t503
  t506 = t191 * t244
  t507 = t189 * t506
  t509 = t194 ** (-0.15e1)
  t510 = t509 * t187
  t511 = t510 * t497
  t513 = t364 * t500
  t515 = t272 * t503
  t518 = t203 * t190 * t55
  t520 = -0.34523333333333333333333333333333333333333333333333e1 * t498 + 0.23015555555555555555555555555555555555555555555556e1 * t501 - 0.26851481481481481481481481481481481481481481481482e1 * t504 - 0.93932222222222222222222222222222222222222222222223e0 * t507 + 0.73355000000000000000000000000000000000000000000000e-1 * t511 - 0.14671000000000000000000000000000000000000000000000e0 * t513 - 0.17116166666666666666666666666666666666666666666667e0 * t515 - 0.36793333333333333333333333333333333333333333333333e0 * t518
  t522 = t290 * t520 * t297
  t525 = t372 * t380
  t532 = t347 * t278
  t533 = t532 * t279
  t544 = -0.51947577317044391278999449251423175496738199495715e2 * t288 * t411 * t405 * t465 - 0.35089341735807877243573431982554320891834732042568e1 * t288 * t471 + 0.35089341735807877243573431982554320891834732042568e1 * t288 * t474 * t475 - 0.10254018858216406658218194626490193680059335835414e4 * t288 * t484 + 0.10389515463408878255799889850284635099347639899143e3 * t288 * t490 - 0.58482236226346462072622386637590534819724553404280e0 * t288 * t522 + 0.48245938496077605200268890697218139186316165284153e2 * t378 * t525 * t278 - 0.60000000000000000000000000000000000000000000000000e1 * t346 * t280 * t372 + 0.60000000000000000000000000000000000000000000000000e1 * t378 * t533 + 0.10685000000000000000000000000000000000000000000000e0 * t339 * t255 * t345 * t348 - 0.56968947174242584615102410102512416326352748836105e-3 * t283 * t265 * t244 * t231
  t546 = 0.1e1 / t376 / t260
  t547 = t196 * t546
  t549 = 0.1e1 / t379 / t210
  t550 = t532 * t549
  t561 = -0.25319000000000000000000000000000000000000000000000e1 * t498 + 0.16879333333333333333333333333333333333333333333333e1 * t501 - 0.19692555555555555555555555555555555555555555555555e1 * t504 - 0.93011851851851851851851851851851851851851851851854e0 * t507 + 0.13651666666666666666666666666666666666666666666667e0 * t511 - 0.27303333333333333333333333333333333333333333333333e0 * t513 - 0.31853888888888888888888888888888888888888888888890e0 * t515 - 0.36514074074074074074074074074074074074074074074075e0 * t518
  t562 = t561 * t279
  t566 = 0.1e1 / t376 / t207
  t567 = t196 * t566
  t568 = t532 * t380
  t586 = t255 * t377
  t590 = t181 * t261
  t597 = 0.51726012919273400298984252201052768390886626637712e3 * t547 * t550 + 0.10000000000000000000000000000000000000000000000000e1 * t262 * t562 - 0.96491876992155210400537781394436278372632330568306e2 * t567 * t568 - 0.32530743900905219527896202567159734993471782831130e-1 * t388 * t256 * t396 + 0.34450798614814814814814814814814814814814814814813e-2 * t189 * t506 * t211 - 0.21687162600603479685264135044773156662314521887420e-1 * t388 * t335 * t298 + 0.16265371950452609763948101283579867496735891415565e-1 * t388 * t256 * t407 + 0.48159733137676571081572406076840235616767705782485e0 * t388 * t256 * t415 - 0.85917975471764868594145516183295969534298037676861e0 * t339 * t586 * t381 + 0.71233333333333333333333333333333333333333333333331e-1 * t339 * t590 * t280 - 0.53424999999999999999999999999999999999999999999999e-1 * t339 * t340 * t373
  t598 = t544 + t597
  t600 = 0.455e3 / 0.648e3 * t178 * t183 * t434 + params.gammac * t598
  t601 = t250 * t600
  t605 = 0.455e3 / 0.648e3 * t179 * t435 * t238 + 0.35e2 / 0.72e2 * t179 * t318 * t304 + 0.7e1 / 0.24e2 * t179 * t245 * t328 - 0.7e1 / 0.48e2 * t179 * t245 * t421 + t179 * t182 * t451 / 0.8e1 - t455 * t456 * t457 / 0.8e1 + t179 * t182 * t601 / 0.48e2
  t606 = t432 * t605
  t609 = t432 * t425
  t612 = t432 * t308
  t615 = cbspline(-t241, 0, params)
  t643 = xbspline(t43, 4, params)
  t645 = t85 ** 2
  t653 = t117 ** 2
  t690 = t108 ** 2
  t707 = 0.10e2 / 0.27e2 * t7 * t18 * t55 * t44 - 0.5e1 / 0.9e1 * t48 * t23 * t51 * t78 + t48 * t50 * t83 * t85 / 0.2e1 + t48 * t52 * t117 / 0.2e1 - t48 * t82 * t121 * t123 / 0.2e1 - 0.3e1 / 0.2e1 * t48 * t84 * t128 - t48 * t89 * t167 / 0.2e1 - 0.3e1 / 0.8e1 * t48 * t20 * t643 * t645 - 0.9e1 / 0.4e1 * t48 * t122 * t85 * t117 - 0.9e1 / 0.8e1 * t48 * t127 * t653 - 0.3e1 / 0.2e1 * t48 * t127 * t78 * t167 - 0.3e1 / 0.8e1 * t48 * t132 * (0.2618e4 / 0.243e3 * t31 * t34 / t21 / t69 * t39 - 0.3047e4 / 0.486e3 * t65 * t67 / t20 / t108 / r0 * t73 + 0.5126e4 / 0.729e3 * t106 * t107 / t108 / t68 * t113 - 0.196e3 / 0.729e3 * t153 * t154 / t21 / t108 / t69 * t164 + 0.16e2 / 0.2187e4 * t152 * params.gammax * t105 * t154 * s0 / t20 / t690 / r0 / t160 / t38 * t61 * t64 * t32)
  t708 = f.my_piecewise3(t3, 0, t707)
  t711 = cbspline(-t241, 4, params)
  t712 = t309 ** 2
  t720 = t425 ** 2
  t757 = t327 ** 2
  t767 = t420 ** 2
  t793 = t191 * t317
  t800 = t347 ** 2
  t804 = t372 ** 2
  t817 = t376 ** 2
  t820 = t379 ** 2
  t825 = 0.31035607751564040179390551320631661034531975982628e4 * t547 * t372 * t549 * t347 - 0.80000000000000000000000000000000000000000000000000e1 * t346 * t280 * t561 - 0.57895126195293126240322668836661767023579398340984e3 * t567 * t525 * t347 + 0.64327917994770140267025187596290852248421553712204e2 * t378 * t561 * t380 * t278 - 0.11483599538271604938271604938271604938271604938271e-1 * t189 * t793 * t211 + 0.36000000000000000000000000000000000000000000000000e2 * t378 * t348 * t372 + 0.57895126195293126240322668836661767023579398340984e3 * t547 * t800 * t380 + 0.48245938496077605200268890697218139186316165284153e2 * t378 * t804 * t380 - 0.62071215503128080358781102641263322069063951965254e4 * t196 / t376 / t344 * t800 * t549 - 0.24000000000000000000000000000000000000000000000000e2 * t567 * t800 * t279 + 0.24955700379505800914252936827276051226357058527653e5 * t196 / t817 * t800 / t820
  t836 = 0.1e1 / t197 * r0 * t434 * t339 / 0.48e2
  t838 = 0.1e1 / t133
  t839 = t496 * t838
  t841 = t354 * t91
  t842 = t353 * t841
  t844 = t265 * t317
  t845 = t264 * t844
  t847 = t189 * t793
  t849 = t194 ** (-0.25e1)
  t852 = t849 * t187 * t434 * t339
  t854 = t510 * t838
  t856 = t364 * t841
  t858 = t272 * t844
  t861 = t203 * t190 * t91
  t907 = -0.60000000000000000000000000000000000000000000000000e1 * t346 * t804 * t279 + 0.10000000000000000000000000000000000000000000000000e1 * t262 * (-0.21099166666666666666666666666666666666666666666667e1 * t836 + 0.20255200000000000000000000000000000000000000000000e2 * t839 - 0.75019259259259259259259259259259259259259259259258e1 * t842 + 0.65641851851851851851851851851851851851851851851850e1 * t845 + 0.31003950617283950617283950617283950617283950617285e1 * t847 + 0.68258333333333333333333333333333333333333333333335e-1 * t852 - 0.10921333333333333333333333333333333333333333333333e1 * t854 + 0.12134814814814814814814814814814814814814814814815e1 * t856 + 0.10617962962962962962962962962962962962962962962963e1 * t858 + 0.13388493827160493827160493827160493827160493827161e1 * t861) * t279 + 0.68734380377411894875316412946636775627438430141488e1 * t339 * t255 * t566 * t568 + 0.22911460125803964958438804315545591875812810047162e1 * t339 * t181 * t377 * t381 - 0.28493333333333333333333333333333333333333333333333e0 * t339 * t181 * t345 * t348 + 0.18989649058080861538367470034170805442117582945368e-2 * t283 * t265 * t317 * t231 + 0.62337092780453269534799339101707810596085839394858e3 * t288 * t488 * t405 * t414 * t394 + 0.46785788981077169658097909310072427855779642723424e1 * t288 * t474 * t297 * t520 - 0.61524113149298439949309167758941162080356015012483e4 * t288 * t480 * t405 * t483 * t394 - 0.21053605041484726346144059189532592535100839225540e2 * t288 * t412 * t475 - 0.69263436422725855038665932335230900662317599327620e2 * t288 * t411 * t520 * t465 + 0.14246666666666666666666666666666666666666666666666e0 * t339 * t590 * t373
  t923 = t220 * t339
  t951 = t410 ** 2
  t953 = t394 ** 2
  t955 = t413 ** 2
  t970 = t405 ** 2
  t975 = -0.22161481481481481481481481481481481481481481481481e0 * t339 * t244 * t261 * t280 - 0.36846163202829085479643115651216588683774907041596e2 * t339 * t255 * t546 * t550 - 0.71233333333333333333333333333333333333333333333332e-1 * t339 * t340 * t562 - 0.42740000000000000000000000000000000000000000000000e0 * t339 * t586 * t533 - 0.13012297560362087811158481026863893997388713132452e0 * t923 * t255 * t393 * t295 * t297 * t405 + 0.19263893255070628432628962430736094246707082312994e1 * t923 * t255 * t411 * t405 * t414 * t295 - 0.58482236226346462072622386637590534819724553404280e0 * t288 * t290 * (-0.28769444444444444444444444444444444444444444444444e1 * t836 + 0.27618666666666666666666666666666666666666666666667e2 * t839 - 0.10229135802469135802469135802469135802469135802469e2 * t842 + 0.89504938271604938271604938271604938271604938271607e1 * t845 + 0.31310740740740740740740740740740740740740740740741e1 * t847 + 0.36677500000000000000000000000000000000000000000000e-1 * t852 - 0.58684000000000000000000000000000000000000000000000e0 * t854 + 0.65204444444444444444444444444444444444444444444445e0 * t856 + 0.57053888888888888888888888888888888888888888888890e0 * t858 + 0.13490888888888888888888888888888888888888888888889e1 * t861) * t297 - 0.91082604192152556048340974007871726131433263376469e5 * t288 / t951 * t953 / t955 - 0.62337092780453269534799339101707810596085839394858e3 * t288 * t480 * t953 * t414 + 0.12304822629859687989861833551788232416071203002497e5 * t288 / t410 / t392 * t953 * t483 - 0.51947577317044391278999449251423175496738199495715e2 * t288 * t411 * t970 * t414
  t1017 = 0.14035736694323150897429372793021728356733892817027e2 * t288 * t488 * t953 * t297 + 0.35089341735807877243573431982554320891834732042568e1 * t288 * t393 * t970 * t297 + 0.86748650402413918741056540179092626649258087549680e-1 * t388 * t335 * t396 + 0.67471172535210825687488420139294265171645179205307e-1 * t388 * t506 * t298 - 0.43374325201206959370528270089546313324629043774840e-1 * t388 * t335 * t407 - 0.12842595503380418955085974953824062831138054875329e1 * t388 * t335 * t415 + 0.13012297560362087811158481026863893997388713132452e0 * t388 * t256 * t471 + 0.38025319932552508024225805073234468230220037056326e2 * t388 * t256 * t484 - 0.38527786510141256865257924861472188493414164625988e1 * t388 * t256 * t490 + 0.21687162600603479685264135044773156662314521887420e-1 * t388 * t256 * t522 - 0.34367190188705947437658206473318387813719215070744e1 * t269 * t377 * t372 * t380 * t278 + 0.42740000000000000000000000000000000000000000000000e0 * t269 * t345 * t278 * t373
  t1019 = t825 + t907 + t975 + t1017
  t1026 = -0.910e3 / 0.243e3 * t179 * s0 * t71 * t238 - 0.455e3 / 0.162e3 * t179 * t435 * t304 - 0.35e2 / 0.18e2 * t179 * t318 * t328 + 0.35e2 / 0.36e2 * t179 * t318 * t421 - 0.7e1 / 0.6e1 * t179 * t245 * t451 + 0.7e1 / 0.6e1 * t455 * t244 * t326 * t457 - 0.7e1 / 0.36e2 * t179 * t245 * t601 - t179 * t182 / t448 / t237 * t757 / 0.2e1 + 0.3e1 / 0.4e1 * t455 * t181 * t449 * t327 * t420 - t179 * t182 * t326 * t767 / 0.8e1 - t455 * t456 * t303 * t600 / 0.6e1 + t179 * t182 * t250 * (-0.910e3 / 0.243e3 * t178 * t183 * t71 + params.gammac * t1019) / 0.48e2
  t1036 = t432 * t1026 * t235 + 0.3e1 * t314 * t720 * t235 + 0.4e1 * t315 * t235 * t605 + t711 * t712 * t235 + 0.6e1 * t242 * t309 * t426 + 0.12e2 * t315 * t301 * t425 + 0.2e1 * t1 * t708 + t615 * t1019 + 0.4e1 * t311 * t301 + 0.4e1 * t606 * t301 + 0.6e1 * t429 * t418 + 0.6e1 * t609 * t418 + 0.4e1 * t612 * t598
  v4rho4_0_ = r0 * t1036 + 0.8e1 * t1 * t172 + 0.4e1 * t311 * t235 + 0.4e1 * t606 * t235 + 0.12e2 * t429 * t301 + 0.12e2 * t609 * t301 + 0.12e2 * t315 * t426 + 0.12e2 * t612 * t418 + 0.4e1 * t615 * t598

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = 0.1e1 - params.ax
  t2 = r0 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = t7 ** 2
  t24 = 0.1e1 / t23
  t25 = t17 * t24
  t26 = t8 - t25
  t27 = f.my_piecewise5(t11, 0, t15, 0, t26)
  t30 = f.my_piecewise3(t21, 0, 0.4e1 / 0.3e1 * t22 * t27)
  t31 = t7 ** (0.1e1 / 0.3e1)
  t33 = 6 ** (0.1e1 / 0.3e1)
  t34 = params.gammax * t33
  t35 = jnp.pi ** 2
  t36 = t35 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = 0.1e1 / t37
  t39 = t34 * t38
  t40 = r0 ** 2
  t41 = r0 ** (0.1e1 / 0.3e1)
  t42 = t41 ** 2
  t44 = 0.1e1 / t42 / t40
  t50 = 0.1e1 + t34 * t38 * s0 * t44 / 0.24e2
  t51 = 0.1e1 / t50
  t54 = t39 * s0 * t44 * t51 / 0.24e2
  t55 = xbspline(t54, 0, params)
  t59 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t60 = t59 * f.p.zeta_threshold
  t62 = f.my_piecewise3(t21, t60, t22 * t20)
  t63 = t31 ** 2
  t64 = 0.1e1 / t63
  t68 = t6 * t62 * t64 * t55 / 0.8e1
  t69 = t6 * t62
  t70 = xbspline(t54, 1, params)
  t71 = t31 * t70
  t72 = t40 * r0
  t79 = params.gammax ** 2
  t80 = t33 ** 2
  t84 = t79 * t80 / t36 / t35
  t85 = s0 ** 2
  t86 = t40 ** 2
  t91 = t50 ** 2
  t92 = 0.1e1 / t91
  t96 = -t39 * s0 / t42 / t72 * t51 / 0.9e1 + t84 * t85 / t41 / t86 / t40 * t92 / 0.216e3
  t97 = t71 * t96
  t101 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t30 * t31 * t55 - t68 - 0.3e1 / 0.8e1 * t69 * t97)
  t102 = r1 <= f.p.dens_threshold
  t103 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t104 = 0.1e1 + t103
  t105 = t104 <= f.p.zeta_threshold
  t106 = t104 ** (0.1e1 / 0.3e1)
  t107 = -t26
  t108 = f.my_piecewise5(t15, 0, t11, 0, t107)
  t111 = f.my_piecewise3(t105, 0, 0.4e1 / 0.3e1 * t106 * t108)
  t113 = r1 ** 2
  t114 = r1 ** (0.1e1 / 0.3e1)
  t115 = t114 ** 2
  t117 = 0.1e1 / t115 / t113
  t123 = 0.1e1 + t34 * t38 * s2 * t117 / 0.24e2
  t124 = 0.1e1 / t123
  t127 = t39 * s2 * t117 * t124 / 0.24e2
  t128 = xbspline(t127, 0, params)
  t133 = f.my_piecewise3(t105, t60, t106 * t104)
  t137 = t6 * t133 * t64 * t128 / 0.8e1
  t139 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t6 * t111 * t31 * t128 - t137)
  t141 = t1 * (t101 + t139)
  t143 = 0.1e1 + t18
  t144 = t143 <= f.p.zeta_threshold
  t145 = t59 ** 2
  t146 = t143 ** (0.1e1 / 0.3e1)
  t147 = t146 ** 2
  t148 = f.my_piecewise3(t144, t145, t147)
  t149 = 0.1e1 - t18
  t150 = t149 <= f.p.zeta_threshold
  t151 = t149 ** (0.1e1 / 0.3e1)
  t152 = t151 ** 2
  t153 = f.my_piecewise3(t150, t145, t152)
  t156 = t3 ** 2
  t157 = (t148 / 0.2e1 + t153 / 0.2e1) * t156
  t158 = t157 * t4
  t159 = jnp.sqrt(s0)
  t160 = jnp.sqrt(s2)
  t162 = (t159 + t160) ** 2
  t164 = 0.1e1 / t31 / t23
  t165 = t162 * t164
  t166 = t4 * t162
  t167 = t166 * t164
  t171 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t172 = t3 * t171
  t173 = 4 ** (0.1e1 / 0.3e1)
  t174 = t173 ** 2
  t177 = t172 * t174 / t31
  t179 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t177
  t180 = jnp.sqrt(t177)
  t183 = t177 ** 0.15e1
  t185 = t171 ** 2
  t186 = t156 * t185
  t188 = t186 * t173 * t64
  t190 = 0.37978500000000000000000000000000000000000000000000e1 * t180 + 0.89690000000000000000000000000000000000000000000000e0 * t177 + 0.20477500000000000000000000000000000000000000000000e0 * t183 + 0.12323500000000000000000000000000000000000000000000e0 * t188
  t193 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t190
  t194 = jnp.log(t193)
  t196 = 0.621814e-1 * t179 * t194
  t197 = t17 ** 2
  t198 = t197 ** 2
  t199 = t23 ** 2
  t200 = 0.1e1 / t199
  t201 = t198 * t200
  t202 = t146 * t143
  t203 = f.my_piecewise3(t144, t60, t202)
  t204 = t151 * t149
  t205 = f.my_piecewise3(t150, t60, t204)
  t207 = 2 ** (0.1e1 / 0.3e1)
  t210 = 0.1e1 / (0.2e1 * t207 - 0.2e1)
  t211 = (t203 + t205 - 0.2e1) * t210
  t213 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t177
  t218 = 0.70594500000000000000000000000000000000000000000000e1 * t180 + 0.15494250000000000000000000000000000000000000000000e1 * t177 + 0.42077500000000000000000000000000000000000000000000e0 * t183 + 0.15629250000000000000000000000000000000000000000000e0 * t188
  t221 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t218
  t222 = jnp.log(t221)
  t226 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t177
  t231 = 0.51785000000000000000000000000000000000000000000000e1 * t180 + 0.90577500000000000000000000000000000000000000000000e0 * t177 + 0.11003250000000000000000000000000000000000000000000e0 * t183 + 0.12417750000000000000000000000000000000000000000000e0 * t188
  t234 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t231
  t235 = jnp.log(t234)
  t236 = t226 * t235
  t238 = -0.3109070e-1 * t213 * t222 + t196 - 0.19751673498613801407483339618206552048944131217655e-1 * t236
  t239 = t211 * t238
  t243 = -t196 + t201 * t239 + 0.19751673498613801407483339618206552048944131217655e-1 * t211 * t236
  t245 = -t157 * t167 / 0.48e2 + params.gammac * t243
  t246 = 0.1e1 / t245
  t247 = t165 * t246
  t249 = t158 * t247 / 0.48e2
  t250 = cbspline(-t249, 1, params)
  t251 = 0.1e1 / t146
  t254 = f.my_piecewise3(t144, 0, 0.2e1 / 0.3e1 * t251 * t26)
  t255 = 0.1e1 / t151
  t258 = f.my_piecewise3(t150, 0, 0.2e1 / 0.3e1 * t255 * t107)
  t261 = (t254 / 0.2e1 + t258 / 0.2e1) * t156
  t262 = t261 * t4
  t265 = t23 * t7
  t267 = 0.1e1 / t31 / t265
  t268 = t162 * t267
  t269 = t268 * t246
  t271 = 0.7e1 / 0.144e3 * t158 * t269
  t272 = t245 ** 2
  t273 = 0.1e1 / t272
  t276 = t166 * t267
  t278 = 0.7e1 / 0.144e3 * t157 * t276
  t280 = 0.1e1 / t31 / t7
  t281 = t174 * t280
  t284 = 0.11073470983333333333333333333333333333333333333333e-2 * t172 * t281 * t194
  t285 = t190 ** 2
  t286 = 0.1e1 / t285
  t287 = t179 * t286
  t289 = 0.1e1 / t180 * t3
  t290 = t171 * t174
  t291 = t290 * t280
  t292 = t289 * t291
  t294 = t172 * t281
  t296 = t177 ** 0.5e0
  t297 = t296 * t3
  t298 = t297 * t291
  t301 = 0.1e1 / t63 / t7
  t303 = t186 * t173 * t301
  t305 = -0.63297500000000000000000000000000000000000000000000e0 * t292 - 0.29896666666666666666666666666666666666666666666667e0 * t294 - 0.10238750000000000000000000000000000000000000000000e0 * t298 - 0.82156666666666666666666666666666666666666666666667e-1 * t303
  t306 = 0.1e1 / t193
  t307 = t305 * t306
  t309 = 0.10000000000000000000000000000000000000000000000000e1 * t287 * t307
  t310 = t197 * t17
  t311 = t310 * t200
  t313 = 0.4e1 * t311 * t239
  t315 = 0.1e1 / t199 / t7
  t316 = t198 * t315
  t318 = 0.4e1 * t316 * t239
  t321 = f.my_piecewise3(t144, 0, 0.4e1 / 0.3e1 * t146 * t26)
  t324 = f.my_piecewise3(t150, 0, 0.4e1 / 0.3e1 * t151 * t107)
  t326 = (t321 + t324) * t210
  t327 = t326 * t238
  t332 = t218 ** 2
  t333 = 0.1e1 / t332
  t334 = t213 * t333
  t339 = -0.11765750000000000000000000000000000000000000000000e1 * t292 - 0.51647500000000000000000000000000000000000000000000e0 * t294 - 0.21038750000000000000000000000000000000000000000000e0 * t298 - 0.10419500000000000000000000000000000000000000000000e0 * t303
  t340 = 0.1e1 / t221
  t341 = t339 * t340
  t347 = t231 ** 2
  t348 = 0.1e1 / t347
  t349 = t226 * t348
  t354 = -0.86308333333333333333333333333333333333333333333334e0 * t292 - 0.30192500000000000000000000000000000000000000000000e0 * t294 - 0.55016250000000000000000000000000000000000000000000e-1 * t298 - 0.82785000000000000000000000000000000000000000000000e-1 * t303
  t355 = 0.1e1 / t234
  t356 = t354 * t355
  t359 = 0.53237641966666666666666666666666666666666666666666e-3 * t172 * t281 * t222 + 0.10000000000000000000000000000000000000000000000000e1 * t334 * t341 - t284 - t309 + 0.18311447306006545054854346104378990962041954983034e-3 * t172 * t281 * t235 + 0.58482236226346462072622386637590534819724553404280e0 * t349 * t356
  t360 = t211 * t359
  t361 = t201 * t360
  t364 = t211 * t3
  t366 = t290 * t280 * t235
  t368 = 0.18311447306006545054854346104378990962041954983034e-3 * t364 * t366
  t369 = t211 * t226
  t371 = t348 * t354 * t355
  t373 = 0.58482236226346462072622386637590534819724553404280e0 * t369 * t371
  t374 = t284 + t309 + t313 - t318 + t201 * t327 + t361 + 0.19751673498613801407483339618206552048944131217655e-1 * t326 * t236 - t368 - t373
  t376 = -t261 * t167 / 0.48e2 + t278 + params.gammac * t374
  t377 = t273 * t376
  t378 = t165 * t377
  t381 = -t262 * t247 / 0.48e2 + t271 + t158 * t378 / 0.48e2
  t382 = t250 * t381
  t383 = t382 * t243
  t385 = cbspline(-t249, 0, params)
  t386 = t385 * t374
  t388 = t22 ** 2
  t389 = 0.1e1 / t388
  t390 = t27 ** 2
  t393 = 0.1e1 / t265
  t394 = t17 * t393
  t396 = -0.2e1 * t24 + 0.2e1 * t394
  t397 = f.my_piecewise5(t11, 0, t15, 0, t396)
  t401 = f.my_piecewise3(t21, 0, 0.4e1 / 0.9e1 * t389 * t390 + 0.4e1 / 0.3e1 * t22 * t397)
  t408 = t6 * t30 * t64 * t55
  t416 = t6 * t62 * t301 * t55 / 0.12e2
  t419 = t69 * t64 * t70 * t96
  t421 = xbspline(t54, 2, params)
  t423 = t96 ** 2
  t441 = t35 ** 2
  t443 = t79 * params.gammax / t441
  t445 = t86 ** 2
  t459 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t401 * t31 * t55 - t408 / 0.4e1 - 0.3e1 / 0.4e1 * t6 * t30 * t97 + t416 - t419 / 0.4e1 - 0.3e1 / 0.8e1 * t69 * t31 * t421 * t423 - 0.3e1 / 0.8e1 * t69 * t71 * (0.11e2 / 0.27e2 * t39 * s0 / t42 / t86 * t51 - t84 * t85 / t41 / t86 / t72 * t92 / 0.24e2 + t443 * t85 * s0 / t445 / t40 / t91 / t50 / 0.162e3))
  t460 = t106 ** 2
  t461 = 0.1e1 / t460
  t462 = t108 ** 2
  t465 = -t396
  t466 = f.my_piecewise5(t15, 0, t11, 0, t465)
  t470 = f.my_piecewise3(t105, 0, 0.4e1 / 0.9e1 * t461 * t462 + 0.4e1 / 0.3e1 * t106 * t466)
  t477 = t6 * t111 * t64 * t128
  t482 = t6 * t133 * t301 * t128 / 0.12e2
  t484 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t6 * t470 * t31 * t128 - t477 / 0.4e1 + t482)
  t487 = cbspline(-t249, 2, params)
  t488 = t381 ** 2
  t491 = 0.1e1 / t202
  t492 = t26 ** 2
  t498 = f.my_piecewise3(t144, 0, -0.2e1 / 0.9e1 * t491 * t492 + 0.2e1 / 0.3e1 * t251 * t396)
  t499 = 0.1e1 / t204
  t500 = t107 ** 2
  t506 = f.my_piecewise3(t150, 0, -0.2e1 / 0.9e1 * t499 * t500 + 0.2e1 / 0.3e1 * t255 * t465)
  t509 = (t498 / 0.2e1 + t506 / 0.2e1) * t156
  t513 = t262 * t269
  t518 = 0.1e1 / t31 / t199
  t522 = 0.35e2 / 0.216e3 * t158 * t162 * t518 * t246
  t524 = t158 * t268 * t377
  t527 = 0.1e1 / t272 / t245
  t528 = t376 ** 2
  t535 = t261 * t276
  t539 = 0.35e2 / 0.216e3 * t157 * t166 * t518
  t540 = t347 ** 2
  t541 = 0.1e1 / t540
  t542 = t354 ** 2
  t544 = t234 ** 2
  t545 = 0.1e1 / t544
  t548 = 0.17315859105681463759666483083807725165579399831905e2 * t369 * t541 * t542 * t545
  t550 = t326 * t226 * t371
  t557 = 0.1e1 / t63 / t23
  t558 = t185 * t173 * t557
  t559 = 0.1e1 / t180 / t177 * t156 * t558
  t561 = t290 * t164
  t562 = t289 * t561
  t564 = t174 * t164
  t565 = t172 * t564
  t567 = t177 ** (-0.5e0)
  t569 = t567 * t156 * t558
  t571 = t297 * t561
  t574 = t186 * t173 * t557
  t576 = -0.57538888888888888888888888888888888888888888888889e0 * t559 + 0.11507777777777777777777777777777777777777777777778e1 * t562 + 0.40256666666666666666666666666666666666666666666667e0 * t565 + 0.36677500000000000000000000000000000000000000000000e-1 * t569 + 0.73355000000000000000000000000000000000000000000000e-1 * t571 + 0.13797500000000000000000000000000000000000000000000e0 * t574
  t580 = 0.58482236226346462072622386637590534819724553404280e0 * t369 * t348 * t576 * t355
  t585 = 0.20e2 * t198 / t199 / t23 * t239
  t588 = 0.12e2 * t197 * t200 * t239
  t591 = 0.32e2 * t310 * t315 * t239
  t594 = 0.14764627977777777777777777777777777777777777777777e-2 * t172 * t564 * t194
  t598 = t172 * t174
  t606 = t339 ** 2
  t620 = t332 ** 2
  t623 = t221 ** 2
  t631 = 0.35616666666666666666666666666666666666666666666666e-1 * t598 * t280 * t286 * t307
  t635 = t305 ** 2
  t638 = 0.20000000000000000000000000000000000000000000000000e1 * t179 / t285 / t190 * t635 * t306
  t648 = 0.10000000000000000000000000000000000000000000000000e1 * t287 * (-0.42198333333333333333333333333333333333333333333333e0 * t559 + 0.84396666666666666666666666666666666666666666666666e0 * t562 + 0.39862222222222222222222222222222222222222222222223e0 * t565 + 0.68258333333333333333333333333333333333333333333333e-1 * t569 + 0.13651666666666666666666666666666666666666666666667e0 * t571 + 0.13692777777777777777777777777777777777777777777778e0 * t574) * t306
  t649 = t285 ** 2
  t652 = t193 ** 2
  t656 = 0.16081979498692535066756296899072713062105388428051e2 * t179 / t649 * t635 / t652
  t665 = 0.1e1 / t347 / t231
  t677 = -0.70983522622222222222222222222222222222222222222221e-3 * t172 * t564 * t222 - 0.34246666666666666666666666666666666666666666666666e-1 * t598 * t280 * t333 * t341 - 0.20000000000000000000000000000000000000000000000000e1 * t213 / t332 / t218 * t606 * t340 + 0.10000000000000000000000000000000000000000000000000e1 * t334 * (-0.78438333333333333333333333333333333333333333333333e0 * t559 + 0.15687666666666666666666666666666666666666666666667e1 * t562 + 0.68863333333333333333333333333333333333333333333333e0 * t565 + 0.14025833333333333333333333333333333333333333333333e0 * t569 + 0.28051666666666666666666666666666666666666666666667e0 * t571 + 0.17365833333333333333333333333333333333333333333333e0 * t574) * t340 + 0.32163958997385070133512593798145426124210776856102e2 * t213 / t620 * t606 / t623 + t594 + t631 + t638 - t648 - t656 - 0.24415263074675393406472461472505321282722606644045e-3 * t172 * t564 * t235 - 0.10843581300301739842632067522386578331157260943710e-1 * t598 * t280 * t348 * t356 - 0.11696447245269292414524477327518106963944910680856e1 * t226 * t665 * t542 * t355 + 0.58482236226346462072622386637590534819724553404280e0 * t349 * t576 * t355 + 0.17315859105681463759666483083807725165579399831905e2 * t226 * t541 * t542 * t545
  t679 = t201 * t211 * t677
  t680 = 0.1e1 / t147
  t686 = f.my_piecewise3(t144, 0, 0.4e1 / 0.9e1 * t680 * t492 + 0.4e1 / 0.3e1 * t146 * t396)
  t687 = 0.1e1 / t152
  t693 = f.my_piecewise3(t150, 0, 0.4e1 / 0.9e1 * t687 * t500 + 0.4e1 / 0.3e1 * t151 * t465)
  t695 = (t686 + t693) * t210
  t699 = t201 * t326 * t359
  t701 = t316 * t327
  t703 = -t548 - 0.11696447245269292414524477327518106963944910680856e1 * t550 - t580 + t585 + t588 - t591 - t594 + t679 + t201 * t695 * t238 + 0.2e1 * t699 - 0.8e1 * t701
  t705 = 0.8e1 * t316 * t360
  t706 = t311 * t327
  t709 = 0.8e1 * t311 * t360
  t715 = 0.11696447245269292414524477327518106963944910680856e1 * t369 * t665 * t542 * t355
  t717 = t326 * t3 * t366
  t722 = 0.24415263074675393406472461472505321282722606644045e-3 * t364 * t290 * t164 * t235
  t726 = 0.10843581300301739842632067522386578331157260943710e-1 * t211 * t172 * t281 * t371
  t727 = -t705 + 0.8e1 * t706 + t709 - t638 + 0.19751673498613801407483339618206552048944131217655e-1 * t695 * t236 + t656 + t648 + t715 - 0.36622894612013090109708692208757981924083909966068e-3 * t717 - t631 + t722 + t726
  t728 = t703 + t727
  d11 = 0.2e1 * t141 + 0.2e1 * t383 + 0.2e1 * t386 + t7 * (t1 * (t459 + t484) + t487 * t488 * t243 + t250 * (-t509 * t4 * t247 / 0.48e2 + 0.7e1 / 0.72e2 * t513 + t262 * t378 / 0.24e2 - t522 - 0.7e1 / 0.72e2 * t524 - t158 * t165 * t527 * t528 / 0.24e2 + t158 * t165 * t273 * (-t509 * t167 / 0.48e2 + 0.7e1 / 0.72e2 * t535 - t539 + params.gammac * t728) / 0.48e2) * t243 + 0.2e1 * t382 * t374 + t385 * t728)
  t743 = -t8 - t25
  t744 = f.my_piecewise5(t11, 0, t15, 0, t743)
  t747 = f.my_piecewise3(t21, 0, 0.4e1 / 0.3e1 * t22 * t744)
  t753 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t747 * t31 * t55 - t68)
  t754 = -t743
  t755 = f.my_piecewise5(t15, 0, t11, 0, t754)
  t758 = f.my_piecewise3(t105, 0, 0.4e1 / 0.3e1 * t106 * t755)
  t763 = t6 * t133
  t764 = xbspline(t127, 1, params)
  t765 = t31 * t764
  t766 = t113 * r1
  t773 = s2 ** 2
  t774 = t113 ** 2
  t779 = t123 ** 2
  t780 = 0.1e1 / t779
  t784 = -t39 * s2 / t115 / t766 * t124 / 0.9e1 + t84 * t773 / t114 / t774 / t113 * t780 / 0.216e3
  t785 = t765 * t784
  t789 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t6 * t758 * t31 * t128 - t137 - 0.3e1 / 0.8e1 * t763 * t785)
  t791 = t1 * (t753 + t789)
  t794 = f.my_piecewise3(t144, 0, 0.2e1 / 0.3e1 * t251 * t743)
  t797 = f.my_piecewise3(t150, 0, 0.2e1 / 0.3e1 * t255 * t754)
  t800 = (t794 / 0.2e1 + t797 / 0.2e1) * t156
  t801 = t800 * t4
  t808 = f.my_piecewise3(t144, 0, 0.4e1 / 0.3e1 * t146 * t743)
  t811 = f.my_piecewise3(t150, 0, 0.4e1 / 0.3e1 * t151 * t754)
  t813 = (t808 + t811) * t210
  t814 = t813 * t238
  t818 = t284 + t309 - t313 - t318 + t201 * t814 + t361 + 0.19751673498613801407483339618206552048944131217655e-1 * t813 * t236 - t368 - t373
  t820 = -t800 * t167 / 0.48e2 + t278 + params.gammac * t818
  t821 = t273 * t820
  t822 = t165 * t821
  t825 = -t801 * t247 / 0.48e2 + t271 + t158 * t822 / 0.48e2
  t826 = t250 * t825
  t827 = t826 * t243
  t828 = t385 * t818
  t832 = 0.2e1 * t394
  t833 = f.my_piecewise5(t11, 0, t15, 0, t832)
  t837 = f.my_piecewise3(t21, 0, 0.4e1 / 0.9e1 * t389 * t744 * t27 + 0.4e1 / 0.3e1 * t22 * t833)
  t844 = t6 * t747 * t64 * t55
  t852 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t837 * t31 * t55 - t844 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t747 * t97 - t408 / 0.8e1 + t416 - t419 / 0.8e1)
  t856 = f.my_piecewise5(t15, 0, t11, 0, -t832)
  t860 = f.my_piecewise3(t105, 0, 0.4e1 / 0.9e1 * t461 * t755 * t108 + 0.4e1 / 0.3e1 * t106 * t856)
  t867 = t6 * t758 * t64 * t128
  t875 = t763 * t64 * t764 * t784
  t878 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t6 * t860 * t31 * t128 - t867 / 0.8e1 - t477 / 0.8e1 + t482 - 0.3e1 / 0.8e1 * t6 * t111 * t785 - t875 / 0.8e1)
  t891 = f.my_piecewise3(t144, 0, -0.2e1 / 0.9e1 * t491 * t743 * t26 + 0.4e1 / 0.3e1 * t251 * t17 * t393)
  t899 = f.my_piecewise3(t150, 0, -0.2e1 / 0.9e1 * t499 * t754 * t107 - 0.4e1 / 0.3e1 * t255 * t17 * t393)
  t902 = (t891 / 0.2e1 + t899 / 0.2e1) * t156
  t906 = t801 * t269
  t915 = t158 * t268 * t821
  t925 = t800 * t276
  t928 = t316 * t814
  t930 = t311 * t814
  t939 = f.my_piecewise3(t144, 0, 0.4e1 / 0.9e1 * t680 * t743 * t26 + 0.8e1 / 0.3e1 * t146 * t17 * t393)
  t947 = f.my_piecewise3(t150, 0, 0.4e1 / 0.9e1 * t687 * t754 * t107 - 0.8e1 / 0.3e1 * t151 * t17 * t393)
  t949 = (t939 + t947) * t210
  t953 = t201 * t813 * t359
  t955 = t813 * t226 * t371
  t958 = t813 * t3 * t366
  t961 = -0.4e1 * t928 + 0.4e1 * t930 + t201 * t949 * t238 + t953 - 0.58482236226346462072622386637590534819724553404280e0 * t955 - 0.18311447306006545054854346104378990962041954983034e-3 * t958 - t631 - 0.18311447306006545054854346104378990962041954983034e-3 * t717 + t722 + t585 - t588 - t594 + t679
  t967 = t715 - t548 - 0.58482236226346462072622386637590534819724553404280e0 * t550 - t580 - 0.4e1 * t706 + t699 - 0.4e1 * t701 - t705 + t656 - t638 + t648 + 0.19751673498613801407483339618206552048944131217655e-1 * t949 * t236 + t726
  t968 = t961 + t967
  d12 = t141 + t383 + t386 + t791 + t827 + t828 + t7 * (t1 * (t852 + t878) + t487 * t381 * t825 * t243 + t250 * (-t902 * t4 * t247 / 0.48e2 + 0.7e1 / 0.144e3 * t906 + t801 * t378 / 0.48e2 + 0.7e1 / 0.144e3 * t513 - t522 - 0.7e1 / 0.144e3 * t524 + t262 * t822 / 0.48e2 - 0.7e1 / 0.144e3 * t915 - t157 * t166 * t164 * t527 * t820 * t376 / 0.24e2 + t158 * t165 * t273 * (-t902 * t167 / 0.48e2 + 0.7e1 / 0.144e3 * t925 + 0.7e1 / 0.144e3 * t535 - t539 + params.gammac * t968) / 0.48e2) * t243 + t826 * t374 + t382 * t818 + t385 * t968)
  t986 = t744 ** 2
  t990 = 0.2e1 * t24 + 0.2e1 * t394
  t991 = f.my_piecewise5(t11, 0, t15, 0, t990)
  t995 = f.my_piecewise3(t21, 0, 0.4e1 / 0.9e1 * t389 * t986 + 0.4e1 / 0.3e1 * t22 * t991)
  t1002 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t995 * t31 * t55 - t844 / 0.4e1 + t416)
  t1003 = t755 ** 2
  t1006 = -t990
  t1007 = f.my_piecewise5(t15, 0, t11, 0, t1006)
  t1011 = f.my_piecewise3(t105, 0, 0.4e1 / 0.9e1 * t461 * t1003 + 0.4e1 / 0.3e1 * t106 * t1007)
  t1021 = xbspline(t127, 2, params)
  t1023 = t784 ** 2
  t1041 = t774 ** 2
  t1055 = f.my_piecewise3(t102, 0, -0.3e1 / 0.8e1 * t6 * t1011 * t31 * t128 - t867 / 0.4e1 - 0.3e1 / 0.4e1 * t6 * t758 * t785 + t482 - t875 / 0.4e1 - 0.3e1 / 0.8e1 * t763 * t31 * t1021 * t1023 - 0.3e1 / 0.8e1 * t763 * t765 * (0.11e2 / 0.27e2 * t39 * s2 / t115 / t774 * t124 - t84 * t773 / t114 / t774 / t766 * t780 / 0.24e2 + t443 * t773 * s2 / t1041 / t113 / t779 / t123 / 0.162e3))
  t1058 = t825 ** 2
  t1061 = t743 ** 2
  t1067 = f.my_piecewise3(t144, 0, -0.2e1 / 0.9e1 * t491 * t1061 + 0.2e1 / 0.3e1 * t251 * t990)
  t1068 = t754 ** 2
  t1074 = f.my_piecewise3(t150, 0, -0.2e1 / 0.9e1 * t499 * t1068 + 0.2e1 / 0.3e1 * t255 * t1006)
  t1077 = (t1067 / 0.2e1 + t1074 / 0.2e1) * t156
  t1085 = t820 ** 2
  t1098 = f.my_piecewise3(t144, 0, 0.4e1 / 0.9e1 * t680 * t1061 + 0.4e1 / 0.3e1 * t146 * t990)
  t1104 = f.my_piecewise3(t150, 0, 0.4e1 / 0.9e1 * t687 * t1068 + 0.4e1 / 0.3e1 * t151 * t1006)
  t1106 = (t1098 + t1104) * t210
  t1110 = -t548 + t722 - t638 + 0.19751673498613801407483339618206552048944131217655e-1 * t1106 * t236 + t585 + t648 + t656 + t591 - 0.36622894612013090109708692208757981924083909966068e-3 * t958 + t715 - t631
  t1117 = t679 + t201 * t1106 * t238 + 0.2e1 * t953 + t588 - 0.8e1 * t928 - t705 - 0.8e1 * t930 - t709 - 0.11696447245269292414524477327518106963944910680856e1 * t955 - t580 - t594 + t726
  t1118 = t1110 + t1117
  d22 = 0.2e1 * t791 + 0.2e1 * t827 + 0.2e1 * t828 + t7 * (t1 * (t1002 + t1055) + t487 * t1058 * t243 + t250 * (-t1077 * t4 * t247 / 0.48e2 + 0.7e1 / 0.72e2 * t906 + t801 * t822 / 0.24e2 - t522 - 0.7e1 / 0.72e2 * t915 - t158 * t165 * t527 * t1085 / 0.24e2 + t158 * t165 * t273 * (-t1077 * t167 / 0.48e2 + 0.7e1 / 0.72e2 * t925 - t539 + params.gammac * t1118) / 0.48e2) * t243 + 0.2e1 * t826 * t818 + t385 * t1118)
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

  t1 = 0.1e1 - params.ax
  t2 = r0 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = 0.1e1 / t23
  t25 = t7 ** 2
  t26 = 0.1e1 / t25
  t28 = -t17 * t26 + t8
  t29 = f.my_piecewise5(t11, 0, t15, 0, t28)
  t30 = t29 ** 2
  t33 = t25 * t7
  t34 = 0.1e1 / t33
  t37 = 0.2e1 * t17 * t34 - 0.2e1 * t26
  t38 = f.my_piecewise5(t11, 0, t15, 0, t37)
  t42 = f.my_piecewise3(t21, 0, 0.4e1 / 0.9e1 * t24 * t30 + 0.4e1 / 0.3e1 * t22 * t38)
  t43 = t7 ** (0.1e1 / 0.3e1)
  t45 = 6 ** (0.1e1 / 0.3e1)
  t46 = params.gammax * t45
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t51 = t46 * t50
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / t52
  t62 = 0.1e1 + t46 * t50 * s0 * t56 / 0.24e2
  t63 = 0.1e1 / t62
  t66 = t51 * s0 * t56 * t63 / 0.24e2
  t67 = xbspline(t66, 0, params)
  t73 = f.my_piecewise3(t21, 0, 0.4e1 / 0.3e1 * t22 * t29)
  t74 = t43 ** 2
  t75 = 0.1e1 / t74
  t80 = t6 * t73
  t81 = xbspline(t66, 1, params)
  t82 = t43 * t81
  t83 = t52 * r0
  t90 = params.gammax ** 2
  t91 = t45 ** 2
  t95 = t90 * t91 / t48 / t47
  t96 = s0 ** 2
  t97 = t52 ** 2
  t102 = t62 ** 2
  t103 = 0.1e1 / t102
  t107 = -t51 * s0 / t54 / t83 * t63 / 0.9e1 + t95 * t96 / t53 / t97 / t52 * t103 / 0.216e3
  t108 = t82 * t107
  t111 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t112 = t111 * f.p.zeta_threshold
  t114 = f.my_piecewise3(t21, t112, t22 * t20)
  t116 = 0.1e1 / t74 / t7
  t121 = t6 * t114
  t122 = t75 * t81
  t123 = t122 * t107
  t126 = xbspline(t66, 2, params)
  t127 = t43 * t126
  t128 = t107 ** 2
  t129 = t127 * t128
  t146 = t47 ** 2
  t147 = 0.1e1 / t146
  t148 = t90 * params.gammax * t147
  t149 = t96 * s0
  t150 = t97 ** 2
  t155 = 0.1e1 / t102 / t62
  t159 = 0.11e2 / 0.27e2 * t51 * s0 / t54 / t97 * t63 - t95 * t96 / t53 / t97 / t83 * t103 / 0.24e2 + t148 * t149 / t150 / t52 * t155 / 0.162e3
  t160 = t82 * t159
  t164 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t42 * t43 * t67 - t6 * t73 * t75 * t67 / 0.4e1 - 0.3e1 / 0.4e1 * t80 * t108 + t6 * t114 * t116 * t67 / 0.12e2 - t121 * t123 / 0.4e1 - 0.3e1 / 0.8e1 * t121 * t129 - 0.3e1 / 0.8e1 * t121 * t160)
  t165 = r1 <= f.p.dens_threshold
  t166 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t167 = 0.1e1 + t166
  t168 = t167 <= f.p.zeta_threshold
  t169 = t167 ** (0.1e1 / 0.3e1)
  t170 = t169 ** 2
  t171 = 0.1e1 / t170
  t172 = -t28
  t173 = f.my_piecewise5(t15, 0, t11, 0, t172)
  t174 = t173 ** 2
  t177 = -t37
  t178 = f.my_piecewise5(t15, 0, t11, 0, t177)
  t182 = f.my_piecewise3(t168, 0, 0.4e1 / 0.9e1 * t171 * t174 + 0.4e1 / 0.3e1 * t169 * t178)
  t184 = r1 ** 2
  t185 = r1 ** (0.1e1 / 0.3e1)
  t186 = t185 ** 2
  t188 = 0.1e1 / t186 / t184
  t199 = xbspline(t51 * s2 * t188 / (0.1e1 + t46 * t50 * s2 * t188 / 0.24e2) / 0.24e2, 0, params)
  t205 = f.my_piecewise3(t168, 0, 0.4e1 / 0.3e1 * t169 * t173)
  t211 = f.my_piecewise3(t168, t112, t169 * t167)
  t217 = f.my_piecewise3(t165, 0, -0.3e1 / 0.8e1 * t6 * t182 * t43 * t199 - t6 * t205 * t75 * t199 / 0.4e1 + t6 * t211 * t116 * t199 / 0.12e2)
  t221 = 0.1e1 + t18
  t222 = t221 <= f.p.zeta_threshold
  t223 = t111 ** 2
  t224 = t221 ** (0.1e1 / 0.3e1)
  t225 = t224 ** 2
  t226 = f.my_piecewise3(t222, t223, t225)
  t227 = 0.1e1 - t18
  t228 = t227 <= f.p.zeta_threshold
  t229 = t227 ** (0.1e1 / 0.3e1)
  t230 = t229 ** 2
  t231 = f.my_piecewise3(t228, t223, t230)
  t234 = t3 ** 2
  t235 = (t226 / 0.2e1 + t231 / 0.2e1) * t234
  t236 = t235 * t4
  t237 = jnp.sqrt(s0)
  t238 = jnp.sqrt(s2)
  t240 = (t237 + t238) ** 2
  t242 = 0.1e1 / t43 / t25
  t243 = t240 * t242
  t244 = t4 * t240
  t245 = t244 * t242
  t248 = 0.1e1 / jnp.pi
  t249 = t248 ** (0.1e1 / 0.3e1)
  t250 = t3 * t249
  t251 = 4 ** (0.1e1 / 0.3e1)
  t252 = t251 ** 2
  t255 = t250 * t252 / t43
  t257 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t255
  t258 = jnp.sqrt(t255)
  t261 = t255 ** 0.15e1
  t263 = t249 ** 2
  t264 = t234 * t263
  t266 = t264 * t251 * t75
  t268 = 0.37978500000000000000000000000000000000000000000000e1 * t258 + 0.89690000000000000000000000000000000000000000000000e0 * t255 + 0.20477500000000000000000000000000000000000000000000e0 * t261 + 0.12323500000000000000000000000000000000000000000000e0 * t266
  t271 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t268
  t272 = jnp.log(t271)
  t274 = 0.621814e-1 * t257 * t272
  t275 = t17 ** 2
  t276 = t275 ** 2
  t277 = t25 ** 2
  t278 = 0.1e1 / t277
  t279 = t276 * t278
  t280 = t224 * t221
  t281 = f.my_piecewise3(t222, t112, t280)
  t282 = t229 * t227
  t283 = f.my_piecewise3(t228, t112, t282)
  t285 = 2 ** (0.1e1 / 0.3e1)
  t288 = 0.1e1 / (0.2e1 * t285 - 0.2e1)
  t289 = (t281 + t283 - 0.2e1) * t288
  t291 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t255
  t296 = 0.70594500000000000000000000000000000000000000000000e1 * t258 + 0.15494250000000000000000000000000000000000000000000e1 * t255 + 0.42077500000000000000000000000000000000000000000000e0 * t261 + 0.15629250000000000000000000000000000000000000000000e0 * t266
  t299 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t296
  t300 = jnp.log(t299)
  t304 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t255
  t309 = 0.51785000000000000000000000000000000000000000000000e1 * t258 + 0.90577500000000000000000000000000000000000000000000e0 * t255 + 0.11003250000000000000000000000000000000000000000000e0 * t261 + 0.12417750000000000000000000000000000000000000000000e0 * t266
  t312 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t309
  t313 = jnp.log(t312)
  t314 = t304 * t313
  t316 = -0.3109070e-1 * t291 * t300 + t274 - 0.19751673498613801407483339618206552048944131217655e-1 * t314
  t317 = t289 * t316
  t321 = -t274 + t279 * t317 + 0.19751673498613801407483339618206552048944131217655e-1 * t289 * t314
  t323 = -t235 * t245 / 0.48e2 + params.gammac * t321
  t324 = 0.1e1 / t323
  t325 = t243 * t324
  t327 = t236 * t325 / 0.48e2
  t328 = cbspline(-t327, 2, params)
  t329 = 0.1e1 / t224
  t332 = f.my_piecewise3(t222, 0, 0.2e1 / 0.3e1 * t329 * t28)
  t333 = 0.1e1 / t229
  t336 = f.my_piecewise3(t228, 0, 0.2e1 / 0.3e1 * t333 * t172)
  t339 = (t332 / 0.2e1 + t336 / 0.2e1) * t234
  t340 = t339 * t4
  t344 = 0.1e1 / t43 / t33
  t345 = t240 * t344
  t346 = t345 * t324
  t349 = t323 ** 2
  t350 = 0.1e1 / t349
  t353 = t244 * t344
  t357 = 0.1e1 / t43 / t7
  t358 = t252 * t357
  t361 = 0.11073470983333333333333333333333333333333333333333e-2 * t250 * t358 * t272
  t362 = t268 ** 2
  t363 = 0.1e1 / t362
  t364 = t257 * t363
  t366 = 0.1e1 / t258 * t3
  t367 = t249 * t252
  t368 = t367 * t357
  t369 = t366 * t368
  t371 = t250 * t358
  t373 = t255 ** 0.5e0
  t374 = t373 * t3
  t375 = t374 * t368
  t378 = t264 * t251 * t116
  t380 = -0.63297500000000000000000000000000000000000000000000e0 * t369 - 0.29896666666666666666666666666666666666666666666667e0 * t371 - 0.10238750000000000000000000000000000000000000000000e0 * t375 - 0.82156666666666666666666666666666666666666666666667e-1 * t378
  t381 = 0.1e1 / t271
  t382 = t380 * t381
  t384 = 0.10000000000000000000000000000000000000000000000000e1 * t364 * t382
  t385 = t275 * t17
  t386 = t385 * t278
  t389 = t277 * t7
  t390 = 0.1e1 / t389
  t391 = t276 * t390
  t396 = f.my_piecewise3(t222, 0, 0.4e1 / 0.3e1 * t224 * t28)
  t399 = f.my_piecewise3(t228, 0, 0.4e1 / 0.3e1 * t229 * t172)
  t401 = (t396 + t399) * t288
  t402 = t401 * t316
  t407 = t296 ** 2
  t408 = 0.1e1 / t407
  t409 = t291 * t408
  t414 = -0.11765750000000000000000000000000000000000000000000e1 * t369 - 0.51647500000000000000000000000000000000000000000000e0 * t371 - 0.21038750000000000000000000000000000000000000000000e0 * t375 - 0.10419500000000000000000000000000000000000000000000e0 * t378
  t415 = 0.1e1 / t299
  t416 = t414 * t415
  t422 = t309 ** 2
  t423 = 0.1e1 / t422
  t424 = t304 * t423
  t429 = -0.86308333333333333333333333333333333333333333333334e0 * t369 - 0.30192500000000000000000000000000000000000000000000e0 * t371 - 0.55016250000000000000000000000000000000000000000000e-1 * t375 - 0.82785000000000000000000000000000000000000000000000e-1 * t378
  t430 = 0.1e1 / t312
  t431 = t429 * t430
  t434 = 0.53237641966666666666666666666666666666666666666666e-3 * t250 * t358 * t300 + 0.10000000000000000000000000000000000000000000000000e1 * t409 * t416 - t361 - t384 + 0.18311447306006545054854346104378990962041954983034e-3 * t250 * t358 * t313 + 0.58482236226346462072622386637590534819724553404280e0 * t424 * t431
  t435 = t289 * t434
  t439 = t289 * t3
  t441 = t367 * t357 * t313
  t444 = t289 * t304
  t446 = t423 * t429 * t430
  t449 = t361 + t384 + 0.4e1 * t386 * t317 - 0.4e1 * t391 * t317 + t279 * t402 + t279 * t435 + 0.19751673498613801407483339618206552048944131217655e-1 * t401 * t314 - 0.18311447306006545054854346104378990962041954983034e-3 * t439 * t441 - 0.58482236226346462072622386637590534819724553404280e0 * t444 * t446
  t451 = -t339 * t245 / 0.48e2 + 0.7e1 / 0.144e3 * t235 * t353 + params.gammac * t449
  t452 = t350 * t451
  t453 = t243 * t452
  t456 = -t340 * t325 / 0.48e2 + 0.7e1 / 0.144e3 * t236 * t346 + t236 * t453 / 0.48e2
  t457 = t456 ** 2
  t458 = t328 * t457
  t461 = cbspline(-t327, 1, params)
  t462 = 0.1e1 / t280
  t463 = t28 ** 2
  t469 = f.my_piecewise3(t222, 0, -0.2e1 / 0.9e1 * t462 * t463 + 0.2e1 / 0.3e1 * t329 * t37)
  t470 = 0.1e1 / t282
  t471 = t172 ** 2
  t477 = f.my_piecewise3(t228, 0, -0.2e1 / 0.9e1 * t470 * t471 + 0.2e1 / 0.3e1 * t333 * t177)
  t480 = (t469 / 0.2e1 + t477 / 0.2e1) * t234
  t481 = t480 * t4
  t489 = 0.1e1 / t43 / t277
  t490 = t240 * t489
  t491 = t490 * t324
  t494 = t345 * t452
  t498 = 0.1e1 / t349 / t323
  t499 = t451 ** 2
  t500 = t498 * t499
  t501 = t243 * t500
  t508 = t244 * t489
  t511 = 0.1e1 / t225
  t517 = f.my_piecewise3(t222, 0, 0.4e1 / 0.9e1 * t511 * t463 + 0.4e1 / 0.3e1 * t224 * t37)
  t518 = 0.1e1 / t230
  t524 = f.my_piecewise3(t228, 0, 0.4e1 / 0.9e1 * t518 * t471 + 0.4e1 / 0.3e1 * t229 * t177)
  t526 = (t517 + t524) * t288
  t529 = t422 ** 2
  t530 = 0.1e1 / t529
  t531 = t429 ** 2
  t533 = t312 ** 2
  t534 = 0.1e1 / t533
  t535 = t530 * t531 * t534
  t538 = t401 * t304
  t543 = 0.1e1 / t258 / t255 * t234
  t544 = t263 * t251
  t546 = 0.1e1 / t74 / t25
  t547 = t544 * t546
  t548 = t543 * t547
  t550 = t367 * t242
  t551 = t366 * t550
  t553 = t252 * t242
  t554 = t250 * t553
  t556 = t255 ** (-0.5e0)
  t557 = t556 * t234
  t558 = t557 * t547
  t560 = t374 * t550
  t563 = t264 * t251 * t546
  t565 = -0.57538888888888888888888888888888888888888888888889e0 * t548 + 0.11507777777777777777777777777777777777777777777778e1 * t551 + 0.40256666666666666666666666666666666666666666666667e0 * t554 + 0.36677500000000000000000000000000000000000000000000e-1 * t558 + 0.73355000000000000000000000000000000000000000000000e-1 * t560 + 0.13797500000000000000000000000000000000000000000000e0 * t563
  t567 = t423 * t565 * t430
  t571 = 0.1e1 / t277 / t25
  t572 = t276 * t571
  t575 = t275 * t278
  t578 = t385 * t390
  t583 = 0.14764627977777777777777777777777777777777777777777e-2 * t250 * t553 * t272
  t587 = t250 * t252
  t588 = t357 * t408
  t593 = 0.1e1 / t407 / t296
  t594 = t291 * t593
  t595 = t414 ** 2
  t596 = t595 * t415
  t605 = -0.78438333333333333333333333333333333333333333333333e0 * t548 + 0.15687666666666666666666666666666666666666666666667e1 * t551 + 0.68863333333333333333333333333333333333333333333333e0 * t554 + 0.14025833333333333333333333333333333333333333333333e0 * t558 + 0.28051666666666666666666666666666666666666666666667e0 * t560 + 0.17365833333333333333333333333333333333333333333333e0 * t563
  t606 = t605 * t415
  t609 = t407 ** 2
  t610 = 0.1e1 / t609
  t611 = t291 * t610
  t612 = t299 ** 2
  t613 = 0.1e1 / t612
  t614 = t595 * t613
  t617 = t357 * t363
  t620 = 0.35616666666666666666666666666666666666666666666666e-1 * t587 * t617 * t382
  t622 = 0.1e1 / t362 / t268
  t623 = t257 * t622
  t624 = t380 ** 2
  t625 = t624 * t381
  t627 = 0.20000000000000000000000000000000000000000000000000e1 * t623 * t625
  t634 = -0.42198333333333333333333333333333333333333333333333e0 * t548 + 0.84396666666666666666666666666666666666666666666666e0 * t551 + 0.39862222222222222222222222222222222222222222222223e0 * t554 + 0.68258333333333333333333333333333333333333333333333e-1 * t558 + 0.13651666666666666666666666666666666666666666666667e0 * t560 + 0.13692777777777777777777777777777777777777777777778e0 * t563
  t635 = t634 * t381
  t637 = 0.10000000000000000000000000000000000000000000000000e1 * t364 * t635
  t638 = t362 ** 2
  t639 = 0.1e1 / t638
  t640 = t257 * t639
  t641 = t271 ** 2
  t642 = 0.1e1 / t641
  t643 = t624 * t642
  t645 = 0.16081979498692535066756296899072713062105388428051e2 * t640 * t643
  t649 = t357 * t423
  t654 = 0.1e1 / t422 / t309
  t655 = t304 * t654
  t656 = t531 * t430
  t659 = t565 * t430
  t662 = t304 * t530
  t663 = t531 * t534
  t666 = -0.70983522622222222222222222222222222222222222222221e-3 * t250 * t553 * t300 - 0.34246666666666666666666666666666666666666666666666e-1 * t587 * t588 * t416 - 0.20000000000000000000000000000000000000000000000000e1 * t594 * t596 + 0.10000000000000000000000000000000000000000000000000e1 * t409 * t606 + 0.32163958997385070133512593798145426124210776856102e2 * t611 * t614 + t583 + t620 + t627 - t637 - t645 - 0.24415263074675393406472461472505321282722606644045e-3 * t250 * t553 * t313 - 0.10843581300301739842632067522386578331157260943710e-1 * t587 * t649 * t431 - 0.11696447245269292414524477327518106963944910680856e1 * t655 * t656 + 0.58482236226346462072622386637590534819724553404280e0 * t424 * t659 + 0.17315859105681463759666483083807725165579399831905e2 * t662 * t663
  t667 = t289 * t666
  t669 = t526 * t316
  t671 = t401 * t434
  t674 = 0.19751673498613801407483339618206552048944131217655e-1 * t526 * t314 - 0.17315859105681463759666483083807725165579399831905e2 * t444 * t535 - 0.11696447245269292414524477327518106963944910680856e1 * t538 * t446 - 0.58482236226346462072622386637590534819724553404280e0 * t444 * t567 + 0.20e2 * t572 * t317 + 0.12e2 * t575 * t317 - 0.32e2 * t578 * t317 - t583 + t279 * t667 + t279 * t669 + 0.2e1 * t279 * t671
  t684 = t654 * t531 * t430
  t687 = t401 * t3
  t691 = t367 * t242 * t313
  t694 = t289 * t250
  t695 = t358 * t446
  t698 = -0.8e1 * t391 * t402 - 0.8e1 * t391 * t435 + 0.8e1 * t386 * t402 + 0.8e1 * t386 * t435 - t627 + t645 + t637 + 0.11696447245269292414524477327518106963944910680856e1 * t444 * t684 - 0.36622894612013090109708692208757981924083909966068e-3 * t687 * t441 - t620 + 0.24415263074675393406472461472505321282722606644045e-3 * t439 * t691 + 0.10843581300301739842632067522386578331157260943710e-1 * t694 * t695
  t699 = t674 + t698
  t701 = -t480 * t245 / 0.48e2 + 0.7e1 / 0.72e2 * t339 * t353 - 0.35e2 / 0.216e3 * t235 * t508 + params.gammac * t699
  t702 = t350 * t701
  t703 = t243 * t702
  t706 = -t481 * t325 / 0.48e2 + 0.7e1 / 0.72e2 * t340 * t346 + t340 * t453 / 0.24e2 - 0.35e2 / 0.216e3 * t236 * t491 - 0.7e1 / 0.72e2 * t236 * t494 - t236 * t501 / 0.24e2 + t236 * t703 / 0.48e2
  t707 = t461 * t706
  t710 = t461 * t456
  t713 = cbspline(-t327, 0, params)
  t724 = t17 * t278
  t726 = 0.6e1 * t34 - 0.6e1 * t724
  t727 = f.my_piecewise5(t11, 0, t15, 0, t726)
  t731 = f.my_piecewise3(t21, 0, -0.8e1 / 0.27e2 / t23 / t20 * t30 * t29 + 0.4e1 / 0.3e1 * t24 * t29 * t38 + 0.4e1 / 0.3e1 * t22 * t727)
  t736 = t97 * r0
  t755 = t90 ** 2
  t757 = t96 ** 2
  t762 = t102 ** 2
  t803 = xbspline(t66, 3, params)
  t815 = -0.3e1 / 0.8e1 * t6 * t731 * t43 * t67 - 0.3e1 / 0.8e1 * t121 * t82 * (-0.154e3 / 0.81e2 * t51 * s0 / t54 / t736 * t63 + 0.341e3 / 0.972e3 * t95 * t96 / t53 / t150 * t103 - 0.19e2 / 0.162e3 * t148 * t149 / t150 / t83 * t155 + t755 * t147 * t757 / t54 / t150 / t736 / t762 * t45 * t50 / 0.486e3) - 0.3e1 / 0.8e1 * t6 * t42 * t75 * t67 - 0.9e1 / 0.8e1 * t6 * t42 * t108 + t6 * t73 * t116 * t67 / 0.4e1 - 0.3e1 / 0.4e1 * t80 * t123 - 0.9e1 / 0.8e1 * t80 * t160 - 0.5e1 / 0.36e2 * t6 * t114 * t546 * t67 + t121 * t116 * t81 * t107 / 0.4e1 - 0.3e1 / 0.8e1 * t121 * t122 * t159 - 0.9e1 / 0.8e1 * t121 * t127 * t107 * t159 - 0.3e1 / 0.8e1 * t121 * t43 * t803 * t128 * t107 - 0.9e1 / 0.8e1 * t80 * t129 - 0.3e1 / 0.8e1 * t121 * t75 * t126 * t128
  t816 = f.my_piecewise3(t2, 0, t815)
  t825 = -t726
  t826 = f.my_piecewise5(t15, 0, t11, 0, t825)
  t830 = f.my_piecewise3(t168, 0, -0.8e1 / 0.27e2 / t170 / t167 * t174 * t173 + 0.4e1 / 0.3e1 * t171 * t173 * t178 + 0.4e1 / 0.3e1 * t169 * t826)
  t848 = f.my_piecewise3(t165, 0, -0.3e1 / 0.8e1 * t6 * t830 * t43 * t199 - 0.3e1 / 0.8e1 * t6 * t182 * t75 * t199 + t6 * t205 * t116 * t199 / 0.4e1 - 0.5e1 / 0.36e2 * t6 * t211 * t546 * t199)
  t851 = cbspline(-t327, 3, params)
  t861 = t221 ** 2
  t864 = t463 * t28
  t873 = f.my_piecewise3(t222, 0, 0.8e1 / 0.27e2 / t224 / t861 * t864 - 0.2e1 / 0.3e1 * t462 * t28 * t37 + 0.2e1 / 0.3e1 * t329 * t726)
  t874 = t227 ** 2
  t877 = t471 * t172
  t886 = f.my_piecewise3(t228, 0, 0.8e1 / 0.27e2 / t229 / t874 * t877 - 0.2e1 / 0.3e1 * t470 * t172 * t177 + 0.2e1 / 0.3e1 * t333 * t825)
  t889 = (t873 / 0.2e1 + t886 / 0.2e1) * t234
  t897 = 0.1e1 / t43 / t389
  t908 = t624 * t380
  t911 = 0.96491876992155210400537781394436278372632330568306e2 * t257 / t638 / t268 * t908 * t642
  t916 = 0.1e1 / t258 / t266 * t248 * t278 / 0.4e1
  t919 = 0.1e1 / t74 / t33
  t920 = t544 * t919
  t921 = t543 * t920
  t923 = t367 * t344
  t924 = t366 * t923
  t926 = t252 * t344
  t927 = t250 * t926
  t929 = t255 ** (-0.15e1)
  t931 = t929 * t248 * t278
  t933 = t557 * t920
  t935 = t374 * t923
  t938 = t264 * t251 * t919
  t943 = 0.10000000000000000000000000000000000000000000000000e1 * t364 * (-0.25319000000000000000000000000000000000000000000000e1 * t916 + 0.16879333333333333333333333333333333333333333333333e1 * t921 - 0.19692555555555555555555555555555555555555555555555e1 * t924 - 0.93011851851851851851851851851851851851851851851854e0 * t927 + 0.13651666666666666666666666666666666666666666666667e0 * t931 - 0.27303333333333333333333333333333333333333333333333e0 * t933 - 0.31853888888888888888888888888888888888888888888890e0 * t935 - 0.36514074074074074074074074074074074074074074074075e0 * t938) * t381
  t946 = 0.60000000000000000000000000000000000000000000000000e1 * t640 * t908 * t381
  t949 = 0.60000000000000000000000000000000000000000000000000e1 * t623 * t382 * t634
  t953 = 0.48245938496077605200268890697218139186316165284153e2 * t640 * t634 * t642 * t380
  t956 = 0.34450798614814814814814814814814814814814814814813e-2 * t250 * t926 * t272
  t957 = t565 * t534
  t984 = 0.51726012919273400298984252201052768390886626637712e3 * t257 / t638 / t362 * t908 / t641 / t271
  t985 = t531 * t429
  t989 = t595 * t414
  t1005 = t911 - t943 - t946 + t949 + 0.51947577317044391278999449251423175496738199495715e2 * t662 * t957 * t429 - 0.35089341735807877243573431982554320891834732042568e1 * t655 * t431 * t565 - t953 - t956 + 0.56968947174242584615102410102512416326352748836105e-3 * t250 * t926 * t313 + 0.16562821945185185185185185185185185185185185185185e-2 * t250 * t926 * t300 + 0.96491876992155210400537781394436278372632330568306e2 * t611 * t605 * t613 * t414 - 0.60000000000000000000000000000000000000000000000000e1 * t594 * t416 * t605 - t984 + 0.35089341735807877243573431982554320891834732042568e1 * t662 * t985 * t430 + 0.60000000000000000000000000000000000000000000000000e1 * t611 * t989 * t415 + 0.10000000000000000000000000000000000000000000000000e1 * t409 * (-0.47063000000000000000000000000000000000000000000000e1 * t916 + 0.31375333333333333333333333333333333333333333333334e1 * t921 - 0.36604555555555555555555555555555555555555555555556e1 * t924 - 0.16068111111111111111111111111111111111111111111111e1 * t927 + 0.28051666666666666666666666666666666666666666666666e0 * t931 - 0.56103333333333333333333333333333333333333333333332e0 * t933 - 0.65453888888888888888888888888888888888888888888890e0 * t935 - 0.46308888888888888888888888888888888888888888888888e0 * t938) * t415
  t1007 = 0.1e1 / t529 / t309
  t1034 = -0.34523333333333333333333333333333333333333333333333e1 * t916 + 0.23015555555555555555555555555555555555555555555556e1 * t921 - 0.26851481481481481481481481481481481481481481481482e1 * t924 - 0.93932222222222222222222222222222222222222222222223e0 * t927 + 0.73355000000000000000000000000000000000000000000000e-1 * t931 - 0.14671000000000000000000000000000000000000000000000e0 * t933 - 0.17116166666666666666666666666666666666666666666667e0 * t935 - 0.36793333333333333333333333333333333333333333333333e0 * t938
  t1039 = 0.1e1 / t529 / t422
  t1042 = 0.1e1 / t533 / t312
  t1060 = 0.53424999999999999999999999999999999999999999999999e-1 * t587 * t617 * t635
  t1064 = 0.85917975471764868594145516183295969534298037676861e0 * t587 * t357 * t639 * t643
  t1068 = 0.71233333333333333333333333333333333333333333333331e-1 * t587 * t242 * t363 * t382
  t1072 = 0.10685000000000000000000000000000000000000000000000e0 * t587 * t357 * t622 * t625
  t1091 = -0.10389515463408878255799889850284635099347639899143e3 * t304 * t1007 * t985 * t534 - 0.19298375398431042080107556278887255674526466113661e3 * t291 / t609 / t296 * t989 * t613 + 0.20690405167709360119593700880421107356354650655085e4 * t291 / t609 / t407 * t989 / t612 / t299 + 0.58482236226346462072622386637590534819724553404280e0 * t424 * t1034 * t430 + 0.10254018858216406658218194626490193680059335835414e4 * t304 * t1039 * t985 * t1042 - 0.16522625736956710527585419434107305400007076070979e1 * t587 * t357 * t610 * t614 + 0.32530743900905219527896202567159734993471782831130e-1 * t587 * t357 * t654 * t656 + 0.10274000000000000000000000000000000000000000000000e0 * t587 * t357 * t593 * t596 + t1060 + t1064 - t1068 - t1072 + 0.21687162600603479685264135044773156662314521887420e-1 * t587 * t242 * t423 * t431 - 0.16265371950452609763948101283579867496735891415565e-1 * t587 * t649 * t659 - 0.48159733137676571081572406076840235616767705782485e0 * t587 * t357 * t530 * t663 + 0.68493333333333333333333333333333333333333333333332e-1 * t587 * t242 * t408 * t416 - 0.51369999999999999999999999999999999999999999999999e-1 * t587 * t588 * t606
  t1100 = 0.60e2 * t572 * t435 + 0.60e2 * t572 * t402 - t911 + t943 + t946 - t949 + t953 + t956 + t279 * t289 * (t1005 + t1091) - 0.12e2 * t391 * t667 + t984 - 0.17544670867903938621786715991277160445917366021284e1 * t526 * t304 * t446
  t1126 = -0.51947577317044391278999449251423175496738199495715e2 * t538 * t535 + 0.12e2 * t386 * t667 - 0.56968947174242584615102410102512416326352748836105e-3 * t439 * t367 * t344 * t313 - 0.54934341918019635164563038313136972886125864949102e-3 * t526 * t3 * t441 - 0.51947577317044391278999449251423175496738199495715e2 * t444 * t530 * t429 * t957 + 0.35089341735807877243573431982554320891834732042568e1 * t444 * t654 * t565 * t431 + 0.73245789224026180219417384417515963848167819932136e-3 * t687 * t691 - t1060 - t1064 + t1068 + t1072 - 0.24e2 * t391 * t671 + 0.24e2 * t386 * t671
  t1163 = 0.36e2 * t575 * t435 - 0.35089341735807877243573431982554320891834732042568e1 * t444 * t530 * t985 * t430 + 0.10389515463408878255799889850284635099347639899143e3 * t444 * t1007 * t985 * t534 + 0.35089341735807877243573431982554320891834732042568e1 * t538 * t684 - 0.58482236226346462072622386637590534819724553404280e0 * t444 * t423 * t1034 * t430 - 0.10254018858216406658218194626490193680059335835414e4 * t444 * t1039 * t985 * t1042 + 0.3e1 * t279 * t401 * t666 + 0.12e2 * t386 * t669 - 0.12e2 * t391 * t669 + 0.24e2 * t724 * t317 - 0.144e3 * t275 * t390 * t317 + 0.240e3 * t385 * t571 * t317
  t1179 = f.my_piecewise3(t222, 0, -0.8e1 / 0.27e2 / t225 / t221 * t864 + 0.4e1 / 0.3e1 * t511 * t28 * t37 + 0.4e1 / 0.3e1 * t224 * t726)
  t1190 = f.my_piecewise3(t228, 0, -0.8e1 / 0.27e2 / t230 / t227 * t877 + 0.4e1 / 0.3e1 * t518 * t172 * t177 + 0.4e1 / 0.3e1 * t229 * t825)
  t1192 = (t1179 + t1190) * t288
  t1223 = -0.120e3 * t276 / t277 / t33 * t317 + t279 * t1192 * t316 + 0.3e1 * t279 * t526 * t434 - 0.96e2 * t578 * t402 - 0.96e2 * t578 * t435 + 0.36e2 * t575 * t402 + 0.19751673498613801407483339618206552048944131217655e-1 * t1192 * t314 - 0.17544670867903938621786715991277160445917366021284e1 * t538 * t567 + 0.48159733137676571081572406076840235616767705782485e0 * t694 * t358 * t535 + 0.32530743900905219527896202567159734993471782831130e-1 * t401 * t250 * t695 + 0.16265371950452609763948101283579867496735891415565e-1 * t694 * t358 * t567 - 0.32530743900905219527896202567159734993471782831130e-1 * t694 * t358 * t684 - 0.21687162600603479685264135044773156662314521887420e-1 * t694 * t553 * t446
  t1225 = t1100 + t1126 + t1163 + t1223
  t1242 = t349 ** 2
  t1273 = t236 * t243 * t350 * (-t889 * t245 / 0.48e2 + 0.7e1 / 0.48e2 * t480 * t353 - 0.35e2 / 0.72e2 * t339 * t508 + 0.455e3 / 0.648e3 * t235 * t244 * t897 + params.gammac * t1225) / 0.48e2 + 0.455e3 / 0.648e3 * t236 * t240 * t897 * t324 + 0.35e2 / 0.72e2 * t236 * t490 * t452 - 0.7e1 / 0.48e2 * t236 * t345 * t702 + t236 * t243 / t1242 * t499 * t451 / 0.8e1 - t235 * t244 * t242 * t498 * t451 * t701 / 0.8e1 - t340 * t501 / 0.8e1 + 0.7e1 / 0.24e2 * t236 * t345 * t500 + 0.7e1 / 0.48e2 * t481 * t346 + t481 * t453 / 0.16e2 - 0.35e2 / 0.72e2 * t340 * t491 - 0.7e1 / 0.24e2 * t340 * t494 + t340 * t703 / 0.16e2 - t889 * t4 * t325 / 0.48e2
  d111 = 0.3e1 * t1 * (t164 + t217) + 0.3e1 * t458 * t321 + 0.3e1 * t707 * t321 + 0.6e1 * t710 * t449 + 0.3e1 * t713 * t699 + t7 * (t1 * (t816 + t848) + t851 * t457 * t456 * t321 + 0.3e1 * t328 * t456 * t321 * t706 + 0.3e1 * t458 * t449 + t461 * t1273 * t321 + 0.3e1 * t707 * t449 + 0.3e1 * t710 * t699 + t713 * t1225)

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

  t1 = 0.1e1 - params.ax
  t2 = r0 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t25 = 0.1e1 / t23 / t20
  t26 = t7 ** 2
  t27 = 0.1e1 / t26
  t29 = -t17 * t27 + t8
  t30 = f.my_piecewise5(t11, 0, t15, 0, t29)
  t31 = t30 ** 2
  t35 = 0.1e1 / t23
  t36 = t35 * t30
  t37 = t26 * t7
  t38 = 0.1e1 / t37
  t41 = 0.2e1 * t17 * t38 - 0.2e1 * t27
  t42 = f.my_piecewise5(t11, 0, t15, 0, t41)
  t45 = t26 ** 2
  t46 = 0.1e1 / t45
  t47 = t17 * t46
  t49 = 0.6e1 * t38 - 0.6e1 * t47
  t50 = f.my_piecewise5(t11, 0, t15, 0, t49)
  t54 = f.my_piecewise3(t21, 0, -0.8e1 / 0.27e2 * t25 * t31 * t30 + 0.4e1 / 0.3e1 * t36 * t42 + 0.4e1 / 0.3e1 * t22 * t50)
  t55 = t7 ** (0.1e1 / 0.3e1)
  t57 = 6 ** (0.1e1 / 0.3e1)
  t58 = params.gammax * t57
  t59 = jnp.pi ** 2
  t60 = t59 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t62 = 0.1e1 / t61
  t63 = t58 * t62
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t74 = 0.1e1 + t58 * t62 * s0 * t68 / 0.24e2
  t75 = 0.1e1 / t74
  t78 = t63 * s0 * t68 * t75 / 0.24e2
  t79 = xbspline(t78, 0, params)
  t83 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t84 = t83 * f.p.zeta_threshold
  t86 = f.my_piecewise3(t21, t84, t22 * t20)
  t87 = t6 * t86
  t88 = t55 ** 2
  t89 = 0.1e1 / t88
  t90 = xbspline(t78, 1, params)
  t91 = t89 * t90
  t92 = t64 ** 2
  t99 = params.gammax ** 2
  t100 = t57 ** 2
  t103 = 0.1e1 / t60 / t59
  t104 = t99 * t100 * t103
  t105 = s0 ** 2
  t106 = t64 * r0
  t111 = t74 ** 2
  t112 = 0.1e1 / t111
  t117 = t59 ** 2
  t118 = 0.1e1 / t117
  t119 = t99 * params.gammax * t118
  t120 = t105 * s0
  t121 = t92 ** 2
  t126 = 0.1e1 / t111 / t74
  t130 = 0.11e2 / 0.27e2 * t63 * s0 / t66 / t92 * t75 - t104 * t105 / t65 / t92 / t106 * t112 / 0.24e2 + t119 * t120 / t121 / t64 * t126 / 0.162e3
  t131 = t91 * t130
  t134 = t55 * t90
  t135 = t92 * r0
  t154 = t99 ** 2
  t156 = t105 ** 2
  t157 = t154 * t118 * t156
  t161 = t111 ** 2
  t162 = 0.1e1 / t161
  t164 = t57 * t62
  t168 = -0.154e3 / 0.81e2 * t63 * s0 / t66 / t135 * t75 + 0.341e3 / 0.972e3 * t104 * t105 / t65 / t121 * t112 - 0.19e2 / 0.162e3 * t119 * t120 / t121 / t106 * t126 + t157 / t66 / t121 / t135 * t162 * t164 / 0.486e3
  t169 = t134 * t168
  t177 = f.my_piecewise3(t21, 0, 0.4e1 / 0.9e1 * t35 * t31 + 0.4e1 / 0.3e1 * t22 * t42)
  t182 = t6 * t177
  t189 = t92 * t64
  t196 = -t63 * s0 / t66 / t106 * t75 / 0.9e1 + t104 * t105 / t65 / t189 * t112 / 0.216e3
  t197 = t134 * t196
  t202 = f.my_piecewise3(t21, 0, 0.4e1 / 0.3e1 * t22 * t30)
  t204 = 0.1e1 / t88 / t7
  t209 = t6 * t202
  t210 = t91 * t196
  t213 = t134 * t130
  t217 = 0.1e1 / t88 / t26
  t222 = t204 * t90
  t223 = t222 * t196
  t226 = xbspline(t78, 2, params)
  t227 = t55 * t226
  t228 = t196 * t130
  t229 = t227 * t228
  t232 = xbspline(t78, 3, params)
  t233 = t55 * t232
  t234 = t196 ** 2
  t235 = t234 * t196
  t236 = t233 * t235
  t239 = t227 * t234
  t242 = t89 * t226
  t243 = t242 * t234
  t246 = -0.3e1 / 0.8e1 * t6 * t54 * t55 * t79 - 0.3e1 / 0.8e1 * t87 * t131 - 0.3e1 / 0.8e1 * t87 * t169 - 0.3e1 / 0.8e1 * t6 * t177 * t89 * t79 - 0.9e1 / 0.8e1 * t182 * t197 + t6 * t202 * t204 * t79 / 0.4e1 - 0.3e1 / 0.4e1 * t209 * t210 - 0.9e1 / 0.8e1 * t209 * t213 - 0.5e1 / 0.36e2 * t6 * t86 * t217 * t79 + t87 * t223 / 0.4e1 - 0.9e1 / 0.8e1 * t87 * t229 - 0.3e1 / 0.8e1 * t87 * t236 - 0.9e1 / 0.8e1 * t209 * t239 - 0.3e1 / 0.8e1 * t87 * t243
  t247 = f.my_piecewise3(t2, 0, t246)
  t248 = r1 <= f.p.dens_threshold
  t249 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t250 = 0.1e1 + t249
  t251 = t250 <= f.p.zeta_threshold
  t252 = t250 ** (0.1e1 / 0.3e1)
  t253 = t252 ** 2
  t255 = 0.1e1 / t253 / t250
  t256 = -t29
  t257 = f.my_piecewise5(t15, 0, t11, 0, t256)
  t258 = t257 ** 2
  t262 = 0.1e1 / t253
  t263 = t262 * t257
  t264 = -t41
  t265 = f.my_piecewise5(t15, 0, t11, 0, t264)
  t268 = -t49
  t269 = f.my_piecewise5(t15, 0, t11, 0, t268)
  t273 = f.my_piecewise3(t251, 0, -0.8e1 / 0.27e2 * t255 * t258 * t257 + 0.4e1 / 0.3e1 * t263 * t265 + 0.4e1 / 0.3e1 * t252 * t269)
  t275 = r1 ** 2
  t276 = r1 ** (0.1e1 / 0.3e1)
  t277 = t276 ** 2
  t279 = 0.1e1 / t277 / t275
  t290 = xbspline(t63 * s2 * t279 / (0.1e1 + t58 * t62 * s2 * t279 / 0.24e2) / 0.24e2, 0, params)
  t299 = f.my_piecewise3(t251, 0, 0.4e1 / 0.9e1 * t262 * t258 + 0.4e1 / 0.3e1 * t252 * t265)
  t306 = f.my_piecewise3(t251, 0, 0.4e1 / 0.3e1 * t252 * t257)
  t312 = f.my_piecewise3(t251, t84, t252 * t250)
  t318 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t6 * t273 * t55 * t290 - 0.3e1 / 0.8e1 * t6 * t299 * t89 * t290 + t6 * t306 * t204 * t290 / 0.4e1 - 0.5e1 / 0.36e2 * t6 * t312 * t217 * t290)
  t322 = 0.1e1 + t18
  t323 = t322 <= f.p.zeta_threshold
  t324 = t83 ** 2
  t325 = t322 ** (0.1e1 / 0.3e1)
  t326 = t325 ** 2
  t327 = f.my_piecewise3(t323, t324, t326)
  t328 = 0.1e1 - t18
  t329 = t328 <= f.p.zeta_threshold
  t330 = t328 ** (0.1e1 / 0.3e1)
  t331 = t330 ** 2
  t332 = f.my_piecewise3(t329, t324, t331)
  t335 = t3 ** 2
  t336 = (t327 / 0.2e1 + t332 / 0.2e1) * t335
  t337 = t336 * t4
  t338 = jnp.sqrt(s0)
  t339 = jnp.sqrt(s2)
  t341 = (t338 + t339) ** 2
  t343 = 0.1e1 / t55 / t26
  t344 = t341 * t343
  t345 = t4 * t341
  t346 = t345 * t343
  t349 = 0.1e1 / jnp.pi
  t350 = t349 ** (0.1e1 / 0.3e1)
  t351 = t3 * t350
  t352 = 4 ** (0.1e1 / 0.3e1)
  t353 = t352 ** 2
  t356 = t351 * t353 / t55
  t358 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t356
  t359 = jnp.sqrt(t356)
  t362 = t356 ** 0.15e1
  t364 = t350 ** 2
  t365 = t335 * t364
  t367 = t365 * t352 * t89
  t369 = 0.37978500000000000000000000000000000000000000000000e1 * t359 + 0.89690000000000000000000000000000000000000000000000e0 * t356 + 0.20477500000000000000000000000000000000000000000000e0 * t362 + 0.12323500000000000000000000000000000000000000000000e0 * t367
  t372 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t369
  t373 = jnp.log(t372)
  t375 = 0.621814e-1 * t358 * t373
  t376 = t17 ** 2
  t377 = t376 ** 2
  t378 = t377 * t46
  t379 = t325 * t322
  t380 = f.my_piecewise3(t323, t84, t379)
  t381 = t330 * t328
  t382 = f.my_piecewise3(t329, t84, t381)
  t383 = t380 + t382 - 0.2e1
  t384 = 2 ** (0.1e1 / 0.3e1)
  t387 = 0.1e1 / (0.2e1 * t384 - 0.2e1)
  t388 = t383 * t387
  t390 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t356
  t395 = 0.70594500000000000000000000000000000000000000000000e1 * t359 + 0.15494250000000000000000000000000000000000000000000e1 * t356 + 0.42077500000000000000000000000000000000000000000000e0 * t362 + 0.15629250000000000000000000000000000000000000000000e0 * t367
  t398 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t395
  t399 = jnp.log(t398)
  t403 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t356
  t408 = 0.51785000000000000000000000000000000000000000000000e1 * t359 + 0.90577500000000000000000000000000000000000000000000e0 * t356 + 0.11003250000000000000000000000000000000000000000000e0 * t362 + 0.12417750000000000000000000000000000000000000000000e0 * t367
  t411 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t408
  t412 = jnp.log(t411)
  t413 = t403 * t412
  t415 = -0.3109070e-1 * t390 * t399 + t375 - 0.19751673498613801407483339618206552048944131217655e-1 * t413
  t416 = t388 * t415
  t420 = -t375 + t378 * t416 + 0.19751673498613801407483339618206552048944131217655e-1 * t388 * t413
  t422 = -t336 * t346 / 0.48e2 + params.gammac * t420
  t423 = 0.1e1 / t422
  t424 = t344 * t423
  t426 = t337 * t424 / 0.48e2
  t427 = cbspline(-t426, 3, params)
  t428 = 0.1e1 / t325
  t431 = f.my_piecewise3(t323, 0, 0.2e1 / 0.3e1 * t428 * t29)
  t432 = 0.1e1 / t330
  t435 = f.my_piecewise3(t329, 0, 0.2e1 / 0.3e1 * t432 * t256)
  t438 = (t431 / 0.2e1 + t435 / 0.2e1) * t335
  t439 = t438 * t4
  t443 = 0.1e1 / t55 / t37
  t444 = t341 * t443
  t445 = t444 * t423
  t448 = t422 ** 2
  t449 = 0.1e1 / t448
  t452 = t345 * t443
  t456 = 0.1e1 / t55 / t7
  t457 = t353 * t456
  t460 = 0.11073470983333333333333333333333333333333333333333e-2 * t351 * t457 * t373
  t461 = t369 ** 2
  t462 = 0.1e1 / t461
  t463 = t358 * t462
  t465 = 0.1e1 / t359 * t3
  t466 = t350 * t353
  t467 = t466 * t456
  t468 = t465 * t467
  t470 = t351 * t457
  t472 = t356 ** 0.5e0
  t473 = t472 * t3
  t474 = t473 * t467
  t477 = t365 * t352 * t204
  t479 = -0.63297500000000000000000000000000000000000000000000e0 * t468 - 0.29896666666666666666666666666666666666666666666667e0 * t470 - 0.10238750000000000000000000000000000000000000000000e0 * t474 - 0.82156666666666666666666666666666666666666666666667e-1 * t477
  t480 = 0.1e1 / t372
  t481 = t479 * t480
  t483 = 0.10000000000000000000000000000000000000000000000000e1 * t463 * t481
  t484 = t376 * t17
  t485 = t484 * t46
  t488 = t45 * t7
  t489 = 0.1e1 / t488
  t490 = t377 * t489
  t495 = f.my_piecewise3(t323, 0, 0.4e1 / 0.3e1 * t325 * t29)
  t498 = f.my_piecewise3(t329, 0, 0.4e1 / 0.3e1 * t330 * t256)
  t500 = (t495 + t498) * t387
  t501 = t500 * t415
  t506 = t395 ** 2
  t507 = 0.1e1 / t506
  t508 = t390 * t507
  t513 = -0.11765750000000000000000000000000000000000000000000e1 * t468 - 0.51647500000000000000000000000000000000000000000000e0 * t470 - 0.21038750000000000000000000000000000000000000000000e0 * t474 - 0.10419500000000000000000000000000000000000000000000e0 * t477
  t514 = 0.1e1 / t398
  t515 = t513 * t514
  t521 = t408 ** 2
  t522 = 0.1e1 / t521
  t523 = t403 * t522
  t528 = -0.86308333333333333333333333333333333333333333333334e0 * t468 - 0.30192500000000000000000000000000000000000000000000e0 * t470 - 0.55016250000000000000000000000000000000000000000000e-1 * t474 - 0.82785000000000000000000000000000000000000000000000e-1 * t477
  t529 = 0.1e1 / t411
  t530 = t528 * t529
  t533 = 0.53237641966666666666666666666666666666666666666666e-3 * t351 * t457 * t399 + 0.10000000000000000000000000000000000000000000000000e1 * t508 * t515 - t460 - t483 + 0.18311447306006545054854346104378990962041954983034e-3 * t351 * t457 * t412 + 0.58482236226346462072622386637590534819724553404280e0 * t523 * t530
  t534 = t388 * t533
  t538 = t388 * t3
  t540 = t466 * t456 * t412
  t543 = t388 * t403
  t545 = t522 * t528 * t529
  t548 = t460 + t483 + 0.4e1 * t485 * t416 - 0.4e1 * t490 * t416 + t378 * t501 + t378 * t534 + 0.19751673498613801407483339618206552048944131217655e-1 * t500 * t413 - 0.18311447306006545054854346104378990962041954983034e-3 * t538 * t540 - 0.58482236226346462072622386637590534819724553404280e0 * t543 * t545
  t550 = -t438 * t346 / 0.48e2 + 0.7e1 / 0.144e3 * t336 * t452 + params.gammac * t548
  t551 = t449 * t550
  t552 = t344 * t551
  t555 = -t439 * t424 / 0.48e2 + 0.7e1 / 0.144e3 * t337 * t445 + t337 * t552 / 0.48e2
  t556 = t555 ** 2
  t558 = t427 * t556 * t555
  t561 = cbspline(-t426, 2, params)
  t562 = t561 * t555
  t563 = 0.1e1 / t379
  t564 = t29 ** 2
  t570 = f.my_piecewise3(t323, 0, -0.2e1 / 0.9e1 * t563 * t564 + 0.2e1 / 0.3e1 * t428 * t41)
  t571 = 0.1e1 / t381
  t572 = t256 ** 2
  t578 = f.my_piecewise3(t329, 0, -0.2e1 / 0.9e1 * t571 * t572 + 0.2e1 / 0.3e1 * t432 * t264)
  t581 = (t570 / 0.2e1 + t578 / 0.2e1) * t335
  t582 = t581 * t4
  t590 = 0.1e1 / t55 / t45
  t591 = t341 * t590
  t592 = t591 * t423
  t595 = t444 * t551
  t599 = 0.1e1 / t448 / t422
  t600 = t550 ** 2
  t601 = t599 * t600
  t602 = t344 * t601
  t609 = t345 * t590
  t612 = 0.1e1 / t326
  t618 = f.my_piecewise3(t323, 0, 0.4e1 / 0.9e1 * t612 * t564 + 0.4e1 / 0.3e1 * t325 * t41)
  t619 = 0.1e1 / t331
  t625 = f.my_piecewise3(t329, 0, 0.4e1 / 0.9e1 * t619 * t572 + 0.4e1 / 0.3e1 * t330 * t264)
  t627 = (t618 + t625) * t387
  t630 = t521 ** 2
  t631 = 0.1e1 / t630
  t632 = t528 ** 2
  t634 = t411 ** 2
  t635 = 0.1e1 / t634
  t636 = t631 * t632 * t635
  t639 = t500 * t403
  t644 = 0.1e1 / t359 / t356 * t335
  t645 = t364 * t352
  t646 = t645 * t217
  t647 = t644 * t646
  t649 = t466 * t343
  t650 = t465 * t649
  t652 = t353 * t343
  t653 = t351 * t652
  t655 = t356 ** (-0.5e0)
  t656 = t655 * t335
  t657 = t656 * t646
  t659 = t473 * t649
  t662 = t365 * t352 * t217
  t664 = -0.57538888888888888888888888888888888888888888888889e0 * t647 + 0.11507777777777777777777777777777777777777777777778e1 * t650 + 0.40256666666666666666666666666666666666666666666667e0 * t653 + 0.36677500000000000000000000000000000000000000000000e-1 * t657 + 0.73355000000000000000000000000000000000000000000000e-1 * t659 + 0.13797500000000000000000000000000000000000000000000e0 * t662
  t666 = t522 * t664 * t529
  t669 = t45 * t26
  t670 = 0.1e1 / t669
  t671 = t377 * t670
  t674 = t484 * t489
  t677 = t376 * t46
  t682 = 0.14764627977777777777777777777777777777777777777777e-2 * t351 * t652 * t373
  t686 = t351 * t353
  t687 = t456 * t507
  t691 = t506 * t395
  t692 = 0.1e1 / t691
  t693 = t390 * t692
  t694 = t513 ** 2
  t695 = t694 * t514
  t704 = -0.78438333333333333333333333333333333333333333333333e0 * t647 + 0.15687666666666666666666666666666666666666666666667e1 * t650 + 0.68863333333333333333333333333333333333333333333333e0 * t653 + 0.14025833333333333333333333333333333333333333333333e0 * t657 + 0.28051666666666666666666666666666666666666666666667e0 * t659 + 0.17365833333333333333333333333333333333333333333333e0 * t662
  t705 = t704 * t514
  t708 = t506 ** 2
  t709 = 0.1e1 / t708
  t710 = t390 * t709
  t711 = t398 ** 2
  t712 = 0.1e1 / t711
  t713 = t694 * t712
  t716 = t456 * t462
  t719 = 0.35616666666666666666666666666666666666666666666666e-1 * t686 * t716 * t481
  t720 = t461 * t369
  t721 = 0.1e1 / t720
  t722 = t358 * t721
  t723 = t479 ** 2
  t724 = t723 * t480
  t726 = 0.20000000000000000000000000000000000000000000000000e1 * t722 * t724
  t733 = -0.42198333333333333333333333333333333333333333333333e0 * t647 + 0.84396666666666666666666666666666666666666666666666e0 * t650 + 0.39862222222222222222222222222222222222222222222223e0 * t653 + 0.68258333333333333333333333333333333333333333333333e-1 * t657 + 0.13651666666666666666666666666666666666666666666667e0 * t659 + 0.13692777777777777777777777777777777777777777777778e0 * t662
  t734 = t733 * t480
  t736 = 0.10000000000000000000000000000000000000000000000000e1 * t463 * t734
  t737 = t461 ** 2
  t738 = 0.1e1 / t737
  t739 = t358 * t738
  t740 = t372 ** 2
  t741 = 0.1e1 / t740
  t742 = t723 * t741
  t744 = 0.16081979498692535066756296899072713062105388428051e2 * t739 * t742
  t748 = t456 * t522
  t752 = t521 * t408
  t753 = 0.1e1 / t752
  t754 = t403 * t753
  t755 = t632 * t529
  t758 = t664 * t529
  t761 = t403 * t631
  t762 = t632 * t635
  t765 = -0.70983522622222222222222222222222222222222222222221e-3 * t351 * t652 * t399 - 0.34246666666666666666666666666666666666666666666666e-1 * t686 * t687 * t515 - 0.20000000000000000000000000000000000000000000000000e1 * t693 * t695 + 0.10000000000000000000000000000000000000000000000000e1 * t508 * t705 + 0.32163958997385070133512593798145426124210776856102e2 * t710 * t713 + t682 + t719 + t726 - t736 - t744 - 0.24415263074675393406472461472505321282722606644045e-3 * t351 * t652 * t412 - 0.10843581300301739842632067522386578331157260943710e-1 * t686 * t748 * t530 - 0.11696447245269292414524477327518106963944910680856e1 * t754 * t755 + 0.58482236226346462072622386637590534819724553404280e0 * t523 * t758 + 0.17315859105681463759666483083807725165579399831905e2 * t761 * t762
  t766 = t388 * t765
  t768 = t627 * t415
  t770 = t500 * t533
  t773 = 0.19751673498613801407483339618206552048944131217655e-1 * t627 * t413 - 0.17315859105681463759666483083807725165579399831905e2 * t543 * t636 - 0.11696447245269292414524477327518106963944910680856e1 * t639 * t545 - 0.58482236226346462072622386637590534819724553404280e0 * t543 * t666 + 0.20e2 * t671 * t416 - 0.32e2 * t674 * t416 + 0.12e2 * t677 * t416 - t682 + t378 * t766 + t378 * t768 + 0.2e1 * t378 * t770
  t783 = t753 * t632 * t529
  t786 = t500 * t3
  t790 = t466 * t343 * t412
  t793 = t388 * t351
  t794 = t457 * t545
  t797 = -0.8e1 * t490 * t501 - 0.8e1 * t490 * t534 + 0.8e1 * t485 * t501 + 0.8e1 * t485 * t534 - t726 + t744 + t736 + 0.11696447245269292414524477327518106963944910680856e1 * t543 * t783 - 0.36622894612013090109708692208757981924083909966068e-3 * t786 * t540 - t719 + 0.24415263074675393406472461472505321282722606644045e-3 * t538 * t790 + 0.10843581300301739842632067522386578331157260943710e-1 * t793 * t794
  t798 = t773 + t797
  t800 = -t581 * t346 / 0.48e2 + 0.7e1 / 0.72e2 * t438 * t452 - 0.35e2 / 0.216e3 * t336 * t609 + params.gammac * t798
  t801 = t449 * t800
  t802 = t344 * t801
  t805 = -t582 * t424 / 0.48e2 + 0.7e1 / 0.72e2 * t439 * t445 + t439 * t552 / 0.24e2 - 0.35e2 / 0.216e3 * t337 * t592 - 0.7e1 / 0.72e2 * t337 * t595 - t337 * t602 / 0.24e2 + t337 * t802 / 0.48e2
  t806 = t420 * t805
  t809 = t561 * t556
  t812 = cbspline(-t426, 1, params)
  t813 = t448 ** 2
  t814 = 0.1e1 / t813
  t816 = t814 * t600 * t550
  t817 = t344 * t816
  t820 = t336 * t345
  t821 = t343 * t599
  t822 = t550 * t800
  t823 = t821 * t822
  t828 = t444 * t601
  t831 = t322 ** 2
  t833 = 0.1e1 / t325 / t831
  t834 = t564 * t29
  t837 = t563 * t29
  t843 = f.my_piecewise3(t323, 0, 0.8e1 / 0.27e2 * t833 * t834 - 0.2e1 / 0.3e1 * t837 * t41 + 0.2e1 / 0.3e1 * t428 * t49)
  t844 = t328 ** 2
  t846 = 0.1e1 / t330 / t844
  t847 = t572 * t256
  t850 = t571 * t256
  t856 = f.my_piecewise3(t329, 0, 0.8e1 / 0.27e2 * t846 * t847 - 0.2e1 / 0.3e1 * t850 * t264 + 0.2e1 / 0.3e1 * t432 * t268)
  t859 = (t843 / 0.2e1 + t856 / 0.2e1) * t335
  t860 = t859 * t4
  t870 = 0.1e1 / t55 / t488
  t871 = t345 * t870
  t877 = 0.1e1 / t630 / t408
  t878 = t632 * t528
  t880 = t877 * t878 * t635
  t886 = 0.1e1 / t737 / t461
  t887 = t358 * t886
  t888 = t723 * t479
  t890 = 0.1e1 / t740 / t372
  t891 = t888 * t890
  t893 = 0.51726012919273400298984252201052768390886626637712e3 * t887 * t891
  t895 = 0.1e1 / t737 / t369
  t896 = t358 * t895
  t897 = t888 * t741
  t899 = 0.96491876992155210400537781394436278372632330568306e2 * t896 * t897
  t902 = t888 * t480
  t904 = 0.60000000000000000000000000000000000000000000000000e1 * t739 * t902
  t910 = 0.1e1 / t45 / t37
  t911 = t377 * t910
  t919 = 0.48245938496077605200268890697218139186316165284153e2 * t739 * t733 * t741 * t479
  t920 = -0.51947577317044391278999449251423175496738199495715e2 * t639 * t636 + 0.10389515463408878255799889850284635099347639899143e3 * t543 * t880 + 0.35089341735807877243573431982554320891834732042568e1 * t639 * t783 + t893 - t899 + 0.60e2 * t671 * t534 + t904 + 0.36e2 * t677 * t534 - 0.96e2 * t674 * t501 - 0.120e3 * t911 * t416 + 0.36e2 * t677 * t501 + t919
  t923 = 0.60000000000000000000000000000000000000000000000000e1 * t722 * t481 * t733
  t924 = t353 * t443
  t927 = 0.34450798614814814814814814814814814814814814814813e-2 * t351 * t924 * t373
  t930 = t627 * t533
  t936 = 0.1e1 / t326 / t322
  t939 = t612 * t29
  t945 = f.my_piecewise3(t323, 0, -0.8e1 / 0.27e2 * t936 * t834 + 0.4e1 / 0.3e1 * t939 * t41 + 0.4e1 / 0.3e1 * t325 * t49)
  t947 = 0.1e1 / t331 / t328
  t950 = t619 * t256
  t956 = f.my_piecewise3(t329, 0, -0.8e1 / 0.27e2 * t947 * t847 + 0.4e1 / 0.3e1 * t950 * t264 + 0.4e1 / 0.3e1 * t330 * t268)
  t958 = (t945 + t956) * t387
  t959 = t958 * t415
  t962 = t631 * t878 * t529
  t968 = 0.1e1 / t359 / t367 * t349 / 0.4e1
  t969 = t968 * t46
  t972 = 0.1e1 / t88 / t37
  t973 = t645 * t972
  t974 = t644 * t973
  t976 = t466 * t443
  t977 = t465 * t976
  t979 = t351 * t924
  t981 = t356 ** (-0.15e1)
  t982 = t981 * t349
  t983 = t982 * t46
  t985 = t656 * t973
  t987 = t473 * t976
  t990 = t365 * t352 * t972
  t992 = -0.34523333333333333333333333333333333333333333333333e1 * t969 + 0.23015555555555555555555555555555555555555555555556e1 * t974 - 0.26851481481481481481481481481481481481481481481482e1 * t977 - 0.93932222222222222222222222222222222222222222222223e0 * t979 + 0.73355000000000000000000000000000000000000000000000e-1 * t983 - 0.14671000000000000000000000000000000000000000000000e0 * t985 - 0.17116166666666666666666666666666666666666666666667e0 * t987 - 0.36793333333333333333333333333333333333333333333333e0 * t990
  t994 = t522 * t992 * t529
  t998 = 0.1e1 / t630 / t521
  t1001 = 0.1e1 / t634 / t411
  t1002 = t998 * t878 * t1001
  t1007 = t627 * t403
  t1014 = -t923 + t927 + 0.24e2 * t47 * t416 + 0.3e1 * t378 * t930 + 0.60e2 * t671 * t501 + t378 * t959 - 0.35089341735807877243573431982554320891834732042568e1 * t543 * t962 - 0.58482236226346462072622386637590534819724553404280e0 * t543 * t994 - 0.10254018858216406658218194626490193680059335835414e4 * t543 * t1002 - 0.17544670867903938621786715991277160445917366021284e1 * t639 * t666 - 0.17544670867903938621786715991277160445917366021284e1 * t1007 * t545 - 0.12e2 * t490 * t766 - 0.24e2 * t490 * t770
  t1022 = t878 * t529
  t1025 = t992 * t529
  t1028 = t694 * t513
  t1029 = t1028 * t514
  t1033 = 0.1e1 / t708 / t395
  t1034 = t390 * t1033
  t1035 = t1028 * t712
  t1041 = t704 * t712
  t1048 = t530 * t664
  t1051 = t403 * t877
  t1052 = t878 * t635
  t1056 = 0.1e1 / t708 / t506
  t1057 = t390 * t1056
  t1059 = 0.1e1 / t711 / t398
  t1060 = t1028 * t1059
  t1063 = -t893 + t899 + 0.35089341735807877243573431982554320891834732042568e1 * t761 * t1022 + 0.58482236226346462072622386637590534819724553404280e0 * t523 * t1025 + 0.60000000000000000000000000000000000000000000000000e1 * t710 * t1029 - 0.19298375398431042080107556278887255674526466113661e3 * t1034 * t1035 - t904 - t919 + t923 - t927 + 0.16562821945185185185185185185185185185185185185185e-2 * t351 * t924 * t399 + 0.96491876992155210400537781394436278372632330568306e2 * t710 * t1041 * t513 - 0.60000000000000000000000000000000000000000000000000e1 * t693 * t515 * t704 - 0.35089341735807877243573431982554320891834732042568e1 * t754 * t1048 - 0.10389515463408878255799889850284635099347639899143e3 * t1051 * t1052 + 0.20690405167709360119593700880421107356354650655085e4 * t1057 * t1060
  t1072 = -0.47063000000000000000000000000000000000000000000000e1 * t969 + 0.31375333333333333333333333333333333333333333333334e1 * t974 - 0.36604555555555555555555555555555555555555555555556e1 * t977 - 0.16068111111111111111111111111111111111111111111111e1 * t979 + 0.28051666666666666666666666666666666666666666666666e0 * t983 - 0.56103333333333333333333333333333333333333333333332e0 * t985 - 0.65453888888888888888888888888888888888888888888890e0 * t987 - 0.46308888888888888888888888888888888888888888888888e0 * t990
  t1073 = t1072 * t514
  t1079 = t664 * t635
  t1080 = t1079 * t528
  t1083 = t403 * t998
  t1084 = t878 * t1001
  t1095 = -0.25319000000000000000000000000000000000000000000000e1 * t969 + 0.16879333333333333333333333333333333333333333333333e1 * t974 - 0.19692555555555555555555555555555555555555555555555e1 * t977 - 0.93011851851851851851851851851851851851851851851854e0 * t979 + 0.13651666666666666666666666666666666666666666666667e0 * t983 - 0.27303333333333333333333333333333333333333333333333e0 * t985 - 0.31853888888888888888888888888888888888888888888890e0 * t987 - 0.36514074074074074074074074074074074074074074074075e0 * t990
  t1096 = t1095 * t480
  t1098 = 0.10000000000000000000000000000000000000000000000000e1 * t463 * t1096
  t1102 = 0.10685000000000000000000000000000000000000000000000e0 * t686 * t456 * t721 * t724
  t1105 = 0.53424999999999999999999999999999999999999999999999e-1 * t686 * t716 * t734
  t1106 = t456 * t738
  t1109 = 0.85917975471764868594145516183295969534298037676861e0 * t686 * t1106 * t742
  t1110 = t343 * t462
  t1113 = 0.71233333333333333333333333333333333333333333333331e-1 * t686 * t1110 * t481
  t1114 = t456 * t753
  t1122 = t343 * t522
  t1129 = t456 * t631
  t1133 = t343 * t507
  t1140 = t456 * t709
  t1144 = 0.10000000000000000000000000000000000000000000000000e1 * t508 * t1073 + 0.56968947174242584615102410102512416326352748836105e-3 * t351 * t924 * t412 + 0.51947577317044391278999449251423175496738199495715e2 * t761 * t1080 + 0.10254018858216406658218194626490193680059335835414e4 * t1083 * t1084 - t1098 - t1102 + t1105 + t1109 - t1113 + 0.32530743900905219527896202567159734993471782831130e-1 * t686 * t1114 * t755 + 0.10274000000000000000000000000000000000000000000000e0 * t686 * t456 * t692 * t695 + 0.21687162600603479685264135044773156662314521887420e-1 * t686 * t1122 * t530 - 0.16265371950452609763948101283579867496735891415565e-1 * t686 * t748 * t758 - 0.48159733137676571081572406076840235616767705782485e0 * t686 * t1129 * t762 + 0.68493333333333333333333333333333333333333333333332e-1 * t686 * t1133 * t515 - 0.51369999999999999999999999999999999999999999999999e-1 * t686 * t687 * t705 - 0.16522625736956710527585419434107305400007076070979e1 * t686 * t1140 * t713
  t1145 = t1063 + t1144
  t1146 = t388 * t1145
  t1152 = t500 * t765
  t1155 = 0.12e2 * t485 * t768 - 0.12e2 * t490 * t768 - 0.96e2 * t674 * t534 + t378 * t1146 + 0.24e2 * t485 * t770 + 0.19751673498613801407483339618206552048944131217655e-1 * t958 * t413 + t1098 + 0.3e1 * t378 * t1152 + t1102 - t1105 - t1109 + t1113
  t1156 = t631 * t528
  t1157 = t1156 * t1079
  t1161 = t753 * t664 * t530
  t1167 = t466 * t443 * t412
  t1170 = t627 * t3
  t1175 = t376 * t489
  t1178 = t484 * t670
  t1181 = t457 * t636
  t1184 = t500 * t351
  t1187 = t457 * t666
  t1190 = t457 * t783
  t1193 = t652 * t545
  t1196 = -0.51947577317044391278999449251423175496738199495715e2 * t543 * t1157 + 0.35089341735807877243573431982554320891834732042568e1 * t543 * t1161 + 0.73245789224026180219417384417515963848167819932136e-3 * t786 * t790 - 0.56968947174242584615102410102512416326352748836105e-3 * t538 * t1167 - 0.54934341918019635164563038313136972886125864949102e-3 * t1170 * t540 + 0.12e2 * t485 * t766 - 0.144e3 * t1175 * t416 + 0.240e3 * t1178 * t416 + 0.48159733137676571081572406076840235616767705782485e0 * t793 * t1181 + 0.32530743900905219527896202567159734993471782831130e-1 * t1184 * t794 + 0.16265371950452609763948101283579867496735891415565e-1 * t793 * t1187 - 0.32530743900905219527896202567159734993471782831130e-1 * t793 * t1190 - 0.21687162600603479685264135044773156662314521887420e-1 * t793 * t1193
  t1198 = t920 + t1014 + t1155 + t1196
  t1200 = -t859 * t346 / 0.48e2 + 0.7e1 / 0.48e2 * t581 * t452 - 0.35e2 / 0.72e2 * t438 * t609 + 0.455e3 / 0.648e3 * t336 * t871 + params.gammac * t1198
  t1201 = t449 * t1200
  t1202 = t344 * t1201
  t1205 = t341 * t870
  t1206 = t1205 * t423
  t1209 = t591 * t551
  t1212 = t444 * t801
  t1225 = t337 * t817 / 0.8e1 - t820 * t823 / 0.8e1 - t439 * t602 / 0.8e1 + 0.7e1 / 0.24e2 * t337 * t828 - t860 * t424 / 0.48e2 + t337 * t1202 / 0.48e2 + 0.455e3 / 0.648e3 * t337 * t1206 + 0.35e2 / 0.72e2 * t337 * t1209 - 0.7e1 / 0.48e2 * t337 * t1212 + 0.7e1 / 0.48e2 * t582 * t445 + t582 * t552 / 0.16e2 - 0.35e2 / 0.72e2 * t439 * t592 - 0.7e1 / 0.24e2 * t439 * t595 + t439 * t802 / 0.16e2
  t1226 = t812 * t1225
  t1229 = t812 * t805
  t1232 = t812 * t555
  t1235 = cbspline(-t426, 0, params)
  t1284 = t121 ** 2
  t1311 = t130 ** 2
  t1319 = xbspline(t78, 4, params)
  t1321 = t234 ** 2
  t1325 = -t6 * t54 * t89 * t79 / 0.2e1 + t6 * t177 * t204 * t79 / 0.2e1 - 0.5e1 / 0.9e1 * t6 * t202 * t217 * t79 + 0.10e2 / 0.27e2 * t6 * t86 * t972 * t79 - 0.3e1 / 0.8e1 * t87 * t134 * (0.2618e4 / 0.243e3 * t63 * s0 / t66 / t189 * t75 - 0.3047e4 / 0.972e3 * t104 * t105 / t65 / t121 / r0 * t112 + 0.2563e4 / 0.1458e4 * t119 * t120 / t121 / t92 * t126 - 0.49e2 / 0.729e3 * t157 / t66 / t121 / t189 * t162 * t164 + 0.2e1 / 0.2187e4 * t154 * params.gammax * t118 * t156 * s0 / t65 / t1284 / r0 / t161 / t74 * t100 * t103) - 0.3e1 / 0.2e1 * t182 * t210 - 0.9e1 / 0.4e1 * t182 * t213 + t87 * t222 * t130 / 0.2e1 - 0.9e1 / 0.4e1 * t182 * t239 - 0.3e1 / 0.2e1 * t6 * t54 * t197 - 0.9e1 / 0.8e1 * t87 * t227 * t1311 - t87 * t89 * t232 * t235 / 0.2e1 - 0.3e1 / 0.8e1 * t87 * t55 * t1319 * t1321
  t1335 = t20 ** 2
  t1338 = t31 ** 2
  t1344 = t42 ** 2
  t1349 = t17 * t489
  t1351 = -0.24e2 * t46 + 0.24e2 * t1349
  t1352 = f.my_piecewise5(t11, 0, t15, 0, t1351)
  t1356 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t23 / t1335 * t1338 - 0.16e2 / 0.9e1 * t25 * t31 * t42 + 0.4e1 / 0.3e1 * t35 * t1344 + 0.16e2 / 0.9e1 * t36 * t50 + 0.4e1 / 0.3e1 * t22 * t1352)
  t1385 = -0.3e1 / 0.2e1 * t209 * t131 - t87 * t91 * t168 / 0.2e1 - 0.3e1 / 0.2e1 * t209 * t169 - 0.9e1 / 0.2e1 * t209 * t229 - 0.3e1 / 0.8e1 * t6 * t1356 * t55 * t79 - 0.3e1 / 0.2e1 * t209 * t243 + t87 * t204 * t226 * t234 / 0.2e1 + t209 * t223 - 0.5e1 / 0.9e1 * t87 * t217 * t90 * t196 - 0.3e1 / 0.2e1 * t209 * t236 - 0.3e1 / 0.2e1 * t87 * t242 * t228 - 0.3e1 / 0.2e1 * t87 * t227 * t196 * t168 - 0.9e1 / 0.4e1 * t87 * t233 * t234 * t130
  t1387 = f.my_piecewise3(t2, 0, t1325 + t1385)
  t1388 = t250 ** 2
  t1391 = t258 ** 2
  t1397 = t265 ** 2
  t1402 = -t1351
  t1403 = f.my_piecewise5(t15, 0, t11, 0, t1402)
  t1407 = f.my_piecewise3(t251, 0, 0.40e2 / 0.81e2 / t253 / t1388 * t1391 - 0.16e2 / 0.9e1 * t255 * t258 * t265 + 0.4e1 / 0.3e1 * t262 * t1397 + 0.16e2 / 0.9e1 * t263 * t269 + 0.4e1 / 0.3e1 * t252 * t1403)
  t1429 = f.my_piecewise3(t248, 0, -0.3e1 / 0.8e1 * t6 * t1407 * t55 * t290 - t6 * t273 * t89 * t290 / 0.2e1 + t6 * t299 * t204 * t290 / 0.2e1 - 0.5e1 / 0.9e1 * t6 * t306 * t217 * t290 + 0.10e2 / 0.27e2 * t6 * t312 * t972 * t290)
  t1432 = cbspline(-t426, 4, params)
  t1433 = t556 ** 2
  t1441 = t805 ** 2
  t1456 = t564 ** 2
  t1462 = t41 ** 2
  t1470 = f.my_piecewise3(t323, 0, -0.56e2 / 0.81e2 / t325 / t831 / t322 * t1456 + 0.16e2 / 0.9e1 * t833 * t564 * t41 - 0.2e1 / 0.3e1 * t563 * t1462 - 0.8e1 / 0.9e1 * t837 * t49 + 0.2e1 / 0.3e1 * t428 * t1351)
  t1474 = t572 ** 2
  t1480 = t264 ** 2
  t1488 = f.my_piecewise3(t329, 0, -0.56e2 / 0.81e2 / t330 / t844 / t328 * t1474 + 0.16e2 / 0.9e1 * t846 * t572 * t264 - 0.2e1 / 0.3e1 * t571 * t1480 - 0.8e1 / 0.9e1 * t850 * t268 + 0.2e1 / 0.3e1 * t432 * t1402)
  t1491 = (t1470 / 0.2e1 + t1488 / 0.2e1) * t335
  t1498 = 0.1e1 / t55 / t669
  t1523 = t600 ** 2
  t1530 = -t1491 * t4 * t424 / 0.48e2 + 0.455e3 / 0.162e3 * t439 * t1206 - 0.910e3 / 0.243e3 * t337 * t341 * t1498 * t423 - 0.35e2 / 0.36e2 * t582 * t592 - 0.35e2 / 0.18e2 * t337 * t591 * t601 + t860 * t552 / 0.12e2 + 0.7e1 / 0.36e2 * t860 * t445 + t439 * t1202 / 0.12e2 - t582 * t602 / 0.4e1 - 0.7e1 / 0.12e2 * t439 * t1212 - 0.7e1 / 0.6e1 * t337 * t444 * t816 - t337 * t344 / t813 / t422 * t1523 / 0.2e1 + t439 * t817 / 0.2e1
  t1540 = t800 ** 2
  t1567 = t723 ** 2
  t1570 = 0.24000000000000000000000000000000000000000000000000e2 * t896 * t1567 * t480
  t1576 = 0.68734380377411894875316412946636775627438430141488e1 * t686 * t456 * t895 * t897
  t1579 = 0.14246666666666666666666666666666666666666666666666e0 * t686 * t1110 * t734
  t1583 = 0.22911460125803964958438804315545591875812810047162e1 * t686 * t343 * t738 * t742
  t1587 = 0.28493333333333333333333333333333333333333333333333e0 * t686 * t343 * t721 * t724
  t1591 = 0.22161481481481481481481481481481481481481481481481e0 * t686 * t443 * t462 * t481
  t1594 = 0.71233333333333333333333333333333333333333333333332e-1 * t686 * t716 * t1096
  t1597 = 0.42740000000000000000000000000000000000000000000000e0 * t686 * t1106 * t902
  t1604 = 0.67471172535210825687488420139294265171645179205307e-1 * t793 * t924 * t545 - t1570 - 0.16e2 * t490 * t1146 + t1576 + t1579 + t1583 - t1587 - t1591 - t1594 - t1597 - 0.21053605041484726346144059189532592535100839225540e2 * t543 * t631 * t664 * t755 - 0.22787578869697033846040964041004966530541099534442e-2 * t786 * t1167
  t1609 = t635 * t992
  t1614 = t1001 * t664
  t1636 = t45 ** 2
  t1647 = 0.18989649058080861538367470034170805442117582945368e-2 * t538 * t466 * t590 * t412 - 0.69263436422725855038665932335230900662317599327620e2 * t543 * t1156 * t1609 - 0.61524113149298439949309167758941162080356015012483e4 * t543 * t998 * t632 * t1614 + 0.14035736694323150897429372793021728356733892817027e2 * t639 * t1161 + 0.46785788981077169658097909310072427855779642723424e1 * t543 * t753 * t992 * t530 - 0.20779030926817756511599779700569270198695279798286e3 * t639 * t1157 + 0.14649157844805236043883476883503192769633563986427e-2 * t1170 * t790 - 0.73245789224026180219417384417515963848167819932136e-3 * t958 * t3 * t540 + 0.4e1 * t378 * t500 * t1145 + 0.16e2 * t485 * t1146 + 0.840e3 * t377 / t1636 * t416 + 0.1440e4 * t376 * t670 * t416 - 0.1920e4 * t484 * t910 * t416
  t1650 = 0.1e1 / t630 / t752
  t1651 = t632 ** 2
  t1656 = t664 ** 2
  t1664 = 0.31035607751564040179390551320631661034531975982628e4 * t887 * t733 * t890 * t723
  t1667 = 0.80000000000000000000000000000000000000000000000000e1 * t722 * t481 * t1095
  t1682 = f.my_piecewise3(t323, 0, 0.40e2 / 0.81e2 / t326 / t831 * t1456 - 0.16e2 / 0.9e1 * t936 * t564 * t41 + 0.4e1 / 0.3e1 * t612 * t1462 + 0.16e2 / 0.9e1 * t939 * t49 + 0.4e1 / 0.3e1 * t325 * t1351)
  t1697 = f.my_piecewise3(t329, 0, 0.40e2 / 0.81e2 / t331 / t844 * t1474 - 0.16e2 / 0.9e1 * t947 * t572 * t264 + 0.4e1 / 0.3e1 * t619 * t1480 + 0.16e2 / 0.9e1 * t950 * t268 + 0.4e1 / 0.3e1 * t330 * t1402)
  t1699 = (t1682 + t1697) * t387
  t1718 = 0.12304822629859687989861833551788232416071203002497e5 * t543 * t1650 * t1651 * t1001 + 0.35089341735807877243573431982554320891834732042568e1 * t543 * t753 * t1656 * t529 + t1664 - t1667 + 0.19751673498613801407483339618206552048944131217655e-1 * t1699 * t413 + 0.72e2 * t677 * t766 + 0.96e2 * t47 * t501 + 0.4e1 * t378 * t958 * t533 - 0.384e3 * t1349 * t416 + 0.16e2 * t485 * t959 - 0.16e2 * t490 * t959 + 0.65061487801810439055792405134319469986943565662260e-1 * t627 * t351 * t794
  t1751 = 0.13012297560362087811158481026863893997388713132452e0 * t793 * t457 * t962 + 0.21687162600603479685264135044773156662314521887420e-1 * t793 * t457 * t994 - 0.13012297560362087811158481026863893997388713132452e0 * t1184 * t1190 - 0.12842595503380418955085974953824062831138054875329e1 * t793 * t652 * t636 - 0.43374325201206959370528270089546313324629043774840e-1 * t793 * t652 * t666 + 0.86748650402413918741056540179092626649258087549680e-1 * t793 * t652 * t783 - 0.86748650402413918741056540179092626649258087549680e-1 * t1184 * t1193 - 0.384e3 * t674 * t770 + 0.6e1 * t378 * t627 * t765 + 0.120e3 * t671 * t766 - 0.480e3 * t911 * t534 + 0.144e3 * t677 * t770 + t378 * t1699 * t415
  t1766 = t630 ** 2
  t1767 = 0.1e1 / t1766
  t1769 = t634 ** 2
  t1770 = 0.1e1 / t1769
  t1787 = 0.120e3 * t671 * t768 - 0.14035736694323150897429372793021728356733892817027e2 * t639 * t962 - 0.192e3 * t674 * t766 + 0.70178683471615754487146863965108641783669464085136e1 * t1007 * t783 + 0.41558061853635513023199559401138540397390559596572e3 * t639 * t880 - 0.41016075432865626632872778505960774720237343341655e4 * t639 * t1002 - 0.91082604192152556048340974007871726131433263376469e5 * t543 * t1767 * t1651 * t1770 - 0.35089341735807877243573431982554320891834732042568e1 * t1007 * t666 - 0.23392894490538584829048954655036213927889821361712e1 * t958 * t403 * t545 - 0.10389515463408878255799889850284635099347639899143e3 * t1007 * t636 - 0.62337092780453269534799339101707810596085839394858e3 * t543 * t998 * t1651 * t635 - 0.23392894490538584829048954655036213927889821361712e1 * t639 * t994
  t1794 = 0.1e1 / t359 / t8 * t870 * t686 / 0.48e2
  t1796 = t968 * t489
  t1799 = 0.1e1 / t88 / t45
  t1800 = t645 * t1799
  t1801 = t644 * t1800
  t1803 = t466 * t590
  t1804 = t465 * t1803
  t1806 = t353 * t590
  t1807 = t351 * t1806
  t1809 = t356 ** (-0.25e1)
  t1812 = t1809 * t349 * t870 * t686
  t1814 = t982 * t489
  t1816 = t656 * t1800
  t1818 = t473 * t1803
  t1821 = t365 * t352 * t1799
  t1823 = -0.28769444444444444444444444444444444444444444444444e1 * t1794 + 0.27618666666666666666666666666666666666666666666667e2 * t1796 - 0.10229135802469135802469135802469135802469135802469e2 * t1801 + 0.89504938271604938271604938271604938271604938271607e1 * t1804 + 0.31310740740740740740740740740740740740740740740741e1 * t1807 + 0.36677500000000000000000000000000000000000000000000e-1 * t1812 - 0.58684000000000000000000000000000000000000000000000e0 * t1814 + 0.65204444444444444444444444444444444444444444444445e0 * t1816 + 0.57053888888888888888888888888888888888888888888890e0 * t1818 + 0.13490888888888888888888888888888888888888888888889e1 * t1821
  t1841 = 0.64327917994770140267025187596290852248421553712204e2 * t739 * t1095 * t741 * t479
  t1844 = 0.11483599538271604938271604938271604938271604938271e-1 * t351 * t1806 * t373
  t1847 = 0.36000000000000000000000000000000000000000000000000e2 * t739 * t724 * t733
  t1850 = 0.57895126195293126240322668836661767023579398340984e3 * t896 * t742 * t733
  t1861 = -0.58482236226346462072622386637590534819724553404280e0 * t543 * t522 * t1823 * t529 - 0.48e2 * t490 * t930 - 0.51947577317044391278999449251423175496738199495715e2 * t543 * t631 * t1656 * t635 + 0.14035736694323150897429372793021728356733892817027e2 * t543 * t877 * t1651 * t529 + t1841 - t1844 + t1847 - t1850 + 0.960e3 * t1178 * t501 + 0.48e2 * t485 * t930 - 0.48e2 * t490 * t1152 + 0.72e2 * t677 * t768 - 0.576e3 * t1175 * t501
  t1876 = 0.36846163202829085479643115651216588683774907041596e2 * t686 * t456 * t886 * t891
  t1877 = t388 * t686
  t1888 = t704 ** 2
  t1931 = -0.60000000000000000000000000000000000000000000000000e1 * t693 * t1888 * t514 - 0.35089341735807877243573431982554320891834732042568e1 * t754 * t1656 * t529 - 0.14035736694323150897429372793021728356733892817027e2 * t1051 * t1651 * t529 + 0.91082604192152556048340974007871726131433263376469e5 * t403 * t1767 * t1651 * t1770 + t1570 - t1576 - 0.14171548179536397724580378856363097131945845388689e3 * t686 * t456 * t1056 * t1060 + 0.13698666666666666666666666666666666666666666666666e0 * t686 * t1133 * t705 + 0.44060335298551228073561118490952814400018869522611e1 * t686 * t343 * t709 * t713 - 0.68493333333333333333333333333333333333333333333332e-1 * t686 * t687 * t1073 - 0.21687162600603479685264135044773156662314521887420e-1 * t686 * t748 * t1025 - 0.38025319932552508024225805073234468230220037056326e2 * t686 * t456 * t998 * t1084 + 0.38527786510141256865257924861472188493414164625988e1 * t686 * t456 * t877 * t1052 - t1579 - t1583 + t1587 - 0.27397333333333333333333333333333333333333333333333e0 * t686 * t343 * t692 * t695
  t1967 = t694 ** 2
  t1974 = 0.13218100589565368422068335547285844320005660856783e2 * t686 * t456 * t1033 * t1035 + 0.43374325201206959370528270089546313324629043774840e-1 * t686 * t1122 * t758 + 0.12842595503380418955085974953824062831138054875329e1 * t686 * t343 * t631 * t762 - 0.13012297560362087811158481026863893997388713132452e0 * t686 * t1129 * t1022 - 0.86748650402413918741056540179092626649258087549680e-1 * t686 * t343 * t753 * t755 - 0.21309037037037037037037037037037037037037037037036e0 * t686 * t443 * t507 * t515 - 0.41096000000000000000000000000000000000000000000000e0 * t686 * t1140 * t1029 - 0.67471172535210825687488420139294265171645179205307e-1 * t686 * t443 * t522 * t530 + t1591 + t1594 + t1597 + 0.51947577317044391278999449251423175496738199495715e2 * t761 * t1656 * t635 + 0.96491876992155210400537781394436278372632330568306e2 * t710 * t1888 * t712 - 0.24000000000000000000000000000000000000000000000000e2 * t1034 * t1967 * t514 - t1664 + t1667 + 0.36000000000000000000000000000000000000000000000000e2 * t710 * t695 * t704
  t2003 = t708 ** 2
  t2006 = t711 ** 2
  t2037 = 0.12414243100625616071756220528252664413812790393051e5 * t1057 * t704 * t1059 * t694 + 0.62337092780453269534799339101707810596085839394858e3 * t1083 * t1651 * t635 - 0.24828486201251232143512441056505328827625580786102e5 * t390 / t708 / t691 * t1967 * t1059 - 0.12304822629859687989861833551788232416071203002497e5 * t403 * t1650 * t1651 * t1001 + 0.61524113149298439949309167758941162080356015012483e4 * t1083 * t1614 * t632 + 0.12865583598954028053405037519258170449684310742441e3 * t710 * t1072 * t712 * t513 - t1841 + t1844 - t1847 + t1850 + 0.11579025239058625248064533767332353404715879668197e4 * t1057 * t1967 * t712 + 0.19964560303604640731402349461820840981085646822122e6 * t390 / t2003 * t1967 / t2006 + 0.10000000000000000000000000000000000000000000000000e1 * t508 * (-0.39219166666666666666666666666666666666666666666667e1 * t1794 + 0.37650400000000000000000000000000000000000000000000e2 * t1796 - 0.13944592592592592592592592592592592592592592592593e2 * t1801 + 0.12201518518518518518518518518518518518518518518519e2 * t1804 + 0.53560370370370370370370370370370370370370370370370e1 * t1807 + 0.14025833333333333333333333333333333333333333333333e0 * t1812 - 0.22441333333333333333333333333333333333333333333332e1 * t1814 + 0.24934814814814814814814814814814814814814814814815e1 * t1816 + 0.21817962962962962962962962962962962962962962962963e1 * t1818 + 0.16979925925925925925925925925925925925925925925926e1 * t1821) * t514 + 0.58482236226346462072622386637590534819724553404280e0 * t523 * t1823 * t529 + 0.21053605041484726346144059189532592535100839225540e2 * t761 * t755 * t664 + 0.69263436422725855038665932335230900662317599327620e2 * t761 * t1609 * t528 - 0.55209406483950617283950617283950617283950617283950e-2 * t351 * t1806 * t399
  t2053 = t737 ** 2
  t2056 = t740 ** 2
  t2060 = 0.24955700379505800914252936827276051226357058527653e5 * t358 / t2053 * t1567 / t2056
  t2061 = t733 ** 2
  t2064 = 0.60000000000000000000000000000000000000000000000000e1 * t722 * t2061 * t480
  t2068 = 0.42740000000000000000000000000000000000000000000000e0 * t470 * t721 * t479 * t734
  t2073 = 0.34367190188705947437658206473318387813719215070744e1 * t470 * t738 * t733 * t741 * t479
  t2079 = 0.62071215503128080358781102641263322069063951965254e4 * t358 / t737 / t720 * t1567 * t890
  t2082 = 0.48245938496077605200268890697218139186316165284153e2 * t739 * t2061 * t741
  t2096 = 0.10000000000000000000000000000000000000000000000000e1 * t463 * (-0.21099166666666666666666666666666666666666666666667e1 * t1794 + 0.20255200000000000000000000000000000000000000000000e2 * t1796 - 0.75019259259259259259259259259259259259259259259258e1 * t1801 + 0.65641851851851851851851851851851851851851851851850e1 * t1804 + 0.31003950617283950617283950617283950617283950617285e1 * t1807 + 0.68258333333333333333333333333333333333333333333335e-1 * t1812 - 0.10921333333333333333333333333333333333333333333333e1 * t1814 + 0.12134814814814814814814814814814814814814814814815e1 * t1816 + 0.10617962962962962962962962962962962962962962962963e1 * t1818 + 0.13388493827160493827160493827160493827160493827161e1 * t1821) * t480
  t2099 = 0.57895126195293126240322668836661767023579398340984e3 * t887 * t1567 * t741
  t2113 = -0.11579025239058625248064533767332353404715879668197e4 * t1034 * t1041 * t694 - 0.62337092780453269534799339101707810596085839394858e3 * t1051 * t762 * t664 - 0.18989649058080861538367470034170805442117582945368e-2 * t351 * t1806 * t412 - 0.80000000000000000000000000000000000000000000000000e1 * t693 * t515 * t1072 + t1876 - 0.46785788981077169658097909310072427855779642723424e1 * t754 * t530 * t992 - t2060 + t2064 - t2068 + t2073 + t2079 - t2082 - t2096 - t2099 - 0.66090502947826842110341677736429221600028304283916e1 * t470 * t709 * t704 * t712 * t513 + 0.13012297560362087811158481026863893997388713132452e0 * t470 * t1161 - 0.19263893255070628432628962430736094246707082312994e1 * t470 * t1157 + 0.41096000000000000000000000000000000000000000000000e0 * t470 * t692 * t513 * t705
  t2118 = 0.96e2 * t47 * t534 - 0.192e3 * t674 * t768 - 0.576e3 * t1175 * t534 + 0.240e3 * t671 * t770 + 0.960e3 * t1178 * t534 - t1876 + 0.19263893255070628432628962430736094246707082312994e1 * t1877 * t1129 * t1080 - 0.13012297560362087811158481026863893997388713132452e0 * t1877 * t1114 * t1048 + 0.48e2 * t485 * t1152 - 0.480e3 * t911 * t501 + t378 * t388 * (t1931 + t1974 + t2037 + t2113) + t2060
  t2137 = -t2064 + 0.62337092780453269534799339101707810596085839394858e3 * t543 * t877 * t632 * t1079 + t2068 - t2073 + 0.24e2 * t46 * t383 * t387 * t415 - t2079 + t2082 + t2096 + t2099 + 0.38025319932552508024225805073234468230220037056326e2 * t793 * t457 * t1002 + 0.65061487801810439055792405134319469986943565662260e-1 * t1184 * t1187 + 0.19263893255070628432628962430736094246707082312994e1 * t1184 * t1181 - 0.38527786510141256865257924861472188493414164625988e1 * t793 * t457 * t880
  t2140 = t1604 + t1647 + t1718 + t1751 + t1787 + t1861 + t2118 + t2137
  t2163 = -0.7e1 / 0.12e2 * t582 * t595 + t582 * t802 / 0.8e1 + 0.35e2 / 0.18e2 * t439 * t1209 + 0.35e2 / 0.36e2 * t337 * t591 * t801 - t337 * t344 * t599 * t1540 / 0.8e1 + 0.7e1 / 0.6e1 * t439 * t828 - 0.455e3 / 0.162e3 * t337 * t1205 * t551 - 0.7e1 / 0.36e2 * t337 * t444 * t1201 + t337 * t344 * t449 * (-t1491 * t346 / 0.48e2 + 0.7e1 / 0.36e2 * t859 * t452 - 0.35e2 / 0.36e2 * t581 * t609 + 0.455e3 / 0.162e3 * t438 * t871 - 0.910e3 / 0.243e3 * t336 * t345 * t1498 + params.gammac * t2140) / 0.48e2 + 0.7e1 / 0.6e1 * t820 * t443 * t599 * t822 + 0.3e1 / 0.4e1 * t820 * t343 * t814 * t600 * t800 - t438 * t345 * t823 / 0.2e1 - t820 * t821 * t550 * t1200 / 0.6e1
  t2174 = t1 * (t1387 + t1429) + t1432 * t1433 * t420 + 0.6e1 * t427 * t556 * t806 + 0.4e1 * t558 * t548 + 0.3e1 * t561 * t1441 * t420 + 0.12e2 * t562 * t548 * t805 + 0.4e1 * t562 * t420 * t1225 + 0.6e1 * t809 * t798 + t812 * (t1530 + t2163) * t420 + 0.4e1 * t1226 * t548 + 0.6e1 * t1229 * t798 + 0.4e1 * t1232 * t1198 + t1235 * t2140
  d1111 = 0.4e1 * t1 * (t247 + t318) + 0.4e1 * t558 * t420 + 0.12e2 * t562 * t806 + 0.12e2 * t809 * t548 + 0.4e1 * t1226 * t420 + 0.12e2 * t1229 * t548 + 0.12e2 * t1232 * t798 + 0.4e1 * t1235 * t1198 + t7 * t2174

  res = {'v4rho4': d1111}
  return res
