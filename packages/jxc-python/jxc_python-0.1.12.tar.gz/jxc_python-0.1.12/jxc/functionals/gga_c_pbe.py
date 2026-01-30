"""Generated from gga_c_pbe.mpl."""

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
  params_BB_raw = params.BB
  if isinstance(params_BB_raw, (str, bytes, dict)):
    params_BB = params_BB_raw
  else:
    try:
      params_BB_seq = list(params_BB_raw)
    except TypeError:
      params_BB = params_BB_raw
    else:
      params_BB_seq = np.asarray(params_BB_seq, dtype=np.float64)
      params_BB = np.concatenate((np.array([np.nan], dtype=np.float64), params_BB_seq))
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mgamma = params_gamma

  mbeta = lambda rs=None, t=None: params_beta

  BB = params_BB

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  functional_body = lambda rs, z, xt, xs0, xs1: f_pbe(rs, z, xt, xs0, xs1)

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
  params_BB_raw = params.BB
  if isinstance(params_BB_raw, (str, bytes, dict)):
    params_BB = params_BB_raw
  else:
    try:
      params_BB_seq = list(params_BB_raw)
    except TypeError:
      params_BB = params_BB_raw
    else:
      params_BB_seq = np.asarray(params_BB_seq, dtype=np.float64)
      params_BB = np.concatenate((np.array([np.nan], dtype=np.float64), params_BB_seq))
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mgamma = params_gamma

  mbeta = lambda rs=None, t=None: params_beta

  BB = params_BB

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  functional_body = lambda rs, z, xt, xs0, xs1: f_pbe(rs, z, xt, xs0, xs1)

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
  params_BB_raw = params.BB
  if isinstance(params_BB_raw, (str, bytes, dict)):
    params_BB = params_BB_raw
  else:
    try:
      params_BB_seq = list(params_BB_raw)
    except TypeError:
      params_BB = params_BB_raw
    else:
      params_BB_seq = np.asarray(params_BB_seq, dtype=np.float64)
      params_BB = np.concatenate((np.array([np.nan], dtype=np.float64), params_BB_seq))
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mgamma = params_gamma

  mbeta = lambda rs=None, t=None: params_beta

  BB = params_BB

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  functional_body = lambda rs, z, xt, xs0, xs1: f_pbe(rs, z, xt, xs0, xs1)

  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t11 = t4 * t6 / t8
  t13 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t11
  t14 = jnp.sqrt(t11)
  t17 = t11 ** 0.15e1
  t19 = t1 ** 2
  t20 = t3 ** 2
  t21 = t19 * t20
  t22 = t8 ** 2
  t25 = t21 * t5 / t22
  t27 = 0.23615562999000000000000000000000000000000000000000e0 * t14 + 0.55770497660000000000000000000000000000000000000000e-1 * t11 + 0.12733196185000000000000000000000000000000000000000e-1 * t17 + 0.76629248290000000000000000000000000000000000000000e-2 * t25
  t29 = 0.1e1 + 0.1e1 / t27
  t30 = jnp.log(t29)
  t31 = t13 * t30
  t32 = r0 - r1
  t33 = t32 ** 2
  t34 = t33 ** 2
  t35 = t7 ** 2
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t34 * t37
  t39 = 0.1e1 / t7
  t40 = t32 * t39
  t41 = 0.1e1 + t40
  t42 = t41 <= f.p.zeta_threshold
  t43 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t44 = t43 * f.p.zeta_threshold
  t45 = t41 ** (0.1e1 / 0.3e1)
  t47 = f.my_piecewise3(t42, t44, t45 * t41)
  t48 = 0.1e1 - t40
  t49 = t48 <= f.p.zeta_threshold
  t50 = t48 ** (0.1e1 / 0.3e1)
  t52 = f.my_piecewise3(t49, t44, t50 * t48)
  t54 = 2 ** (0.1e1 / 0.3e1)
  t57 = 0.1e1 / (0.2e1 * t54 - 0.2e1)
  t58 = (t47 + t52 - 0.2e1) * t57
  t60 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t11
  t65 = 0.21948324211500000000000000000000000000000000000000e0 * t14 + 0.48172707847500000000000000000000000000000000000000e-1 * t11 + 0.13082189292500000000000000000000000000000000000000e-1 * t17 + 0.48592432297500000000000000000000000000000000000000e-2 * t25
  t67 = 0.1e1 + 0.1e1 / t65
  t68 = jnp.log(t67)
  t71 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t11
  t76 = 0.17489762330000000000000000000000000000000000000000e0 * t14 + 0.30591463695000000000000000000000000000000000000000e-1 * t11 + 0.37162156485000000000000000000000000000000000000000e-2 * t17 + 0.41939460495000000000000000000000000000000000000000e-2 * t25
  t78 = 0.1e1 + 0.1e1 / t76
  t79 = jnp.log(t78)
  t80 = t71 * t79
  t82 = -t60 * t68 + t31 - 0.58482236226346462072622386637590534819724553404281e0 * t80
  t83 = t58 * t82
  t84 = t38 * t83
  t86 = 0.58482236226346462072622386637590534819724553404281e0 * t58 * t80
  t87 = t43 ** 2
  t88 = t45 ** 2
  t89 = f.my_piecewise3(t42, t87, t88)
  t90 = t50 ** 2
  t91 = f.my_piecewise3(t49, t87, t90)
  t93 = t89 / 0.2e1 + t91 / 0.2e1
  t94 = t93 ** 2
  t95 = t94 * t93
  t96 = params.gamma * t95
  t98 = s0 + 0.2e1 * s1 + s2
  t100 = 0.1e1 / t8 / t35
  t101 = t98 * t100
  t103 = 0.1e1 / t94
  t105 = 0.1e1 / t3
  t107 = t103 * t19 * t105 * t5
  t110 = params.BB * params.beta
  t111 = 0.1e1 / params.gamma
  t113 = (-t31 + t84 + t86) * t111
  t114 = 0.1e1 / t95
  t116 = jnp.exp(-t113 * t114)
  t117 = t116 - 0.1e1
  t118 = 0.1e1 / t117
  t119 = t111 * t118
  t120 = t98 ** 2
  t122 = t110 * t119 * t120
  t124 = 0.1e1 / t22 / t36
  t125 = t54 ** 2
  t127 = t94 ** 2
  t128 = 0.1e1 / t127
  t130 = 0.1e1 / t20
  t132 = t1 * t130 * t6
  t133 = t124 * t125 * t128 * t132
  t136 = t101 * t54 * t107 / 0.96e2 + t122 * t133 / 0.3072e4
  t137 = params.beta * t136
  t138 = params.beta * t111
  t141 = t138 * t118 * t136 + 0.1e1
  t143 = t111 / t141
  t145 = t137 * t143 + 0.1e1
  t146 = jnp.log(t145)
  t147 = t96 * t146
  t149 = 0.1e1 / t8 / t7
  t150 = t6 * t149
  t153 = 0.11073470983333333333333333333333333333333333333333e-2 * t4 * t150 * t30
  t154 = t27 ** 2
  t159 = t3 * t6
  t160 = t159 * t149
  t161 = 0.1e1 / t14 * t1 * t160
  t163 = t4 * t150
  t165 = t11 ** 0.5e0
  t167 = t165 * t1 * t160
  t172 = t21 * t5 / t22 / t7
  t177 = t13 / t154 * (-0.39359271665000000000000000000000000000000000000000e-1 * t161 - 0.18590165886666666666666666666666666666666666666667e-1 * t163 - 0.63665980925000000000000000000000000000000000000000e-2 * t167 - 0.51086165526666666666666666666666666666666666666667e-2 * t172) / t29
  t181 = 0.4e1 * t33 * t32 * t37 * t83
  t182 = t36 * t7
  t186 = 0.4e1 * t34 / t182 * t83
  t188 = t32 / t35
  t189 = t39 - t188
  t192 = f.my_piecewise3(t42, 0, 0.4e1 / 0.3e1 * t45 * t189)
  t193 = -t189
  t196 = f.my_piecewise3(t49, 0, 0.4e1 / 0.3e1 * t50 * t193)
  t198 = (t192 + t196) * t57
  t200 = t38 * t198 * t82
  t204 = t65 ** 2
  t218 = t76 ** 2
  t219 = 0.1e1 / t218
  t225 = -0.29149603883333333333333333333333333333333333333333e-1 * t161 - 0.10197154565000000000000000000000000000000000000000e-1 * t163 - 0.18581078242500000000000000000000000000000000000000e-2 * t167 - 0.27959640330000000000000000000000000000000000000000e-2 * t172
  t226 = 0.1e1 / t78
  t232 = t38 * t58 * (0.53237641966666666666666666666666666666666666666667e-3 * t4 * t150 * t68 + t60 / t204 * (-0.36580540352500000000000000000000000000000000000000e-1 * t161 - 0.16057569282500000000000000000000000000000000000000e-1 * t163 - 0.65410946462500000000000000000000000000000000000000e-2 * t167 - 0.32394954865000000000000000000000000000000000000000e-2 * t172) / t67 - t153 - t177 + 0.18311447306006545054854346104378990962041954983034e-3 * t4 * t150 * t79 + 0.58482236226346462072622386637590534819724553404281e0 * t71 * t219 * t225 * t226)
  t234 = 0.58482236226346462072622386637590534819724553404281e0 * t198 * t80
  t239 = 0.18311447306006545054854346104378990962041954983034e-3 * t58 * t1 * t159 * t149 * t79
  t244 = 0.58482236226346462072622386637590534819724553404281e0 * t58 * t71 * t219 * t225 * t226
  t245 = params.gamma * t94
  t246 = 0.1e1 / t45
  t249 = f.my_piecewise3(t42, 0, 0.2e1 / 0.3e1 * t246 * t189)
  t250 = 0.1e1 / t50
  t253 = f.my_piecewise3(t49, 0, 0.2e1 / 0.3e1 * t250 * t193)
  t255 = t249 / 0.2e1 + t253 / 0.2e1
  t265 = 0.7e1 / 0.288e3 * t98 / t8 / t35 / t7 * t54 * t107
  t267 = t101 * t54 * t114
  t268 = t19 * t105
  t273 = t110 * t111
  t274 = t117 ** 2
  t275 = 0.1e1 / t274
  t278 = t273 * t275 * t120 * t124
  t280 = t125 * t128 * t1
  t281 = t130 * t6
  t288 = -(t153 + t177 + t181 - t186 + t200 + t232 + t234 - t239 - t244) * t111 * t114 + 0.3e1 * t113 * t128 * t255
  t300 = 0.7e1 / 0.4608e4 * t122 / t22 / t182 * t125 * t128 * t132
  t303 = t273 * t118 * t120 * t124
  t307 = t125 / t127 / t93 * t1
  t312 = -t265 - t267 * t268 * t5 * t255 / 0.48e2 - t278 * t280 * t281 * t288 * t116 / 0.3072e4 - t300 - t303 * t307 * t281 * t255 / 0.768e3
  t315 = t141 ** 2
  t316 = 0.1e1 / t315
  t317 = t111 * t316
  t318 = t138 * t275
  t328 = 0.1e1 / t145
  t331 = t153 + t177 + t181 - t186 + t200 + t232 + t234 - t239 - t244 + 0.3e1 * t245 * t146 * t255 + t96 * (params.beta * t312 * t143 - t137 * t317 * (-t318 * t136 * t288 * t116 + t138 * t118 * t312)) * t328
  vrho_0_ = t7 * t331 + t147 - t31 + t84 + t86
  t333 = -t39 - t188
  t336 = f.my_piecewise3(t42, 0, 0.4e1 / 0.3e1 * t45 * t333)
  t337 = -t333
  t340 = f.my_piecewise3(t49, 0, 0.4e1 / 0.3e1 * t50 * t337)
  t342 = (t336 + t340) * t57
  t344 = t38 * t342 * t82
  t346 = 0.58482236226346462072622386637590534819724553404281e0 * t342 * t80
  t349 = f.my_piecewise3(t42, 0, 0.2e1 / 0.3e1 * t246 * t333)
  t352 = f.my_piecewise3(t49, 0, 0.2e1 / 0.3e1 * t250 * t337)
  t354 = t349 / 0.2e1 + t352 / 0.2e1
  t368 = -(t153 + t177 - t181 - t186 + t344 + t232 + t346 - t239 - t244) * t111 * t114 + 0.3e1 * t113 * t128 * t354
  t378 = -t265 - t267 * t268 * t5 * t354 / 0.48e2 - t278 * t280 * t281 * t368 * t116 / 0.3072e4 - t300 - t303 * t307 * t281 * t354 / 0.768e3
  t392 = t153 + t177 - t181 - t186 + t344 + t232 + t346 - t239 - t244 + 0.3e1 * t245 * t146 * t354 + t96 * (params.beta * t378 * t143 - t137 * t317 * (-t318 * t136 * t368 * t116 + t138 * t118 * t378)) * t328
  vrho_1_ = t7 * t392 + t147 - t31 + t84 + t86
  t394 = t7 * params.gamma
  t398 = t100 * t54 * t103 * t268 * t5
  t402 = t110 * t119 * t98 * t133
  t404 = t398 / 0.96e2 + t402 / 0.1536e4
  t407 = params.beta ** 2
  t409 = params.gamma ** 2
  t411 = t407 * t136 / t409
  t412 = t316 * t118
  vsigma_0_ = t394 * t95 * (params.beta * t404 * t143 - t411 * t412 * t404) * t328
  t420 = t398 / 0.48e2 + t402 / 0.768e3
  vsigma_1_ = t394 * t95 * (params.beta * t420 * t143 - t411 * t412 * t420) * t328
  vsigma_2_ = vsigma_0_
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
  params_BB_raw = params.BB
  if isinstance(params_BB_raw, (str, bytes, dict)):
    params_BB = params_BB_raw
  else:
    try:
      params_BB_seq = list(params_BB_raw)
    except TypeError:
      params_BB = params_BB_raw
    else:
      params_BB_seq = np.asarray(params_BB_seq, dtype=np.float64)
      params_BB = np.concatenate((np.array([np.nan], dtype=np.float64), params_BB_seq))
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mgamma = params_gamma

  mbeta = lambda rs=None, t=None: params_beta

  BB = params_BB

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  functional_body = lambda rs, z, xt, xs0, xs1: f_pbe(rs, z, xt, xs0, xs1)

  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t10 = t4 * t6 / t7
  t12 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t10
  t13 = jnp.sqrt(t10)
  t16 = t10 ** 0.15e1
  t18 = t1 ** 2
  t19 = t3 ** 2
  t20 = t18 * t19
  t21 = t7 ** 2
  t24 = t20 * t5 / t21
  t26 = 0.23615562999000000000000000000000000000000000000000e0 * t13 + 0.55770497660000000000000000000000000000000000000000e-1 * t10 + 0.12733196185000000000000000000000000000000000000000e-1 * t16 + 0.76629248290000000000000000000000000000000000000000e-2 * t24
  t28 = 0.1e1 + 0.1e1 / t26
  t29 = jnp.log(t28)
  t30 = t12 * t29
  t31 = 0.1e1 <= f.p.zeta_threshold
  t32 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t34 = f.my_piecewise3(t31, t32 * f.p.zeta_threshold, 1)
  t37 = 2 ** (0.1e1 / 0.3e1)
  t41 = (0.2e1 * t34 - 0.2e1) / (0.2e1 * t37 - 0.2e1)
  t43 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t10
  t48 = 0.17489762330000000000000000000000000000000000000000e0 * t13 + 0.30591463695000000000000000000000000000000000000000e-1 * t10 + 0.37162156485000000000000000000000000000000000000000e-2 * t16 + 0.41939460495000000000000000000000000000000000000000e-2 * t24
  t50 = 0.1e1 + 0.1e1 / t48
  t51 = jnp.log(t50)
  t54 = 0.58482236226346462072622386637590534819724553404281e0 * t41 * t43 * t51
  t55 = t32 ** 2
  t56 = f.my_piecewise3(t31, t55, 1)
  t57 = t56 ** 2
  t58 = t57 * t56
  t59 = params.gamma * t58
  t60 = r0 ** 2
  t62 = 0.1e1 / t7 / t60
  t65 = 0.1e1 / t57
  t67 = 0.1e1 / t3
  t69 = t65 * t18 * t67 * t5
  t72 = params.BB * params.beta
  t73 = 0.1e1 / params.gamma
  t76 = 0.1e1 / t58
  t78 = jnp.exp(-(-t30 + t54) * t73 * t76)
  t79 = t78 - 0.1e1
  t80 = 0.1e1 / t79
  t81 = t73 * t80
  t82 = s0 ** 2
  t84 = t72 * t81 * t82
  t85 = t60 ** 2
  t87 = 0.1e1 / t21 / t85
  t88 = t37 ** 2
  t90 = t57 ** 2
  t91 = 0.1e1 / t90
  t93 = 0.1e1 / t19
  t95 = t1 * t93 * t6
  t96 = t87 * t88 * t91 * t95
  t99 = s0 * t62 * t37 * t69 / 0.96e2 + t84 * t96 / 0.3072e4
  t100 = params.beta * t99
  t101 = params.beta * t73
  t104 = t101 * t80 * t99 + 0.1e1
  t106 = t73 / t104
  t108 = t100 * t106 + 0.1e1
  t109 = jnp.log(t108)
  t112 = 0.1e1 / t7 / r0
  t113 = t6 * t112
  t116 = 0.11073470983333333333333333333333333333333333333333e-2 * t4 * t113 * t29
  t117 = t26 ** 2
  t122 = t3 * t6
  t123 = t122 * t112
  t124 = 0.1e1 / t13 * t1 * t123
  t126 = t4 * t113
  t128 = t10 ** 0.5e0
  t130 = t128 * t1 * t123
  t135 = t20 * t5 / t21 / r0
  t140 = t12 / t117 * (-0.39359271665000000000000000000000000000000000000000e-1 * t124 - 0.18590165886666666666666666666666666666666666666667e-1 * t126 - 0.63665980925000000000000000000000000000000000000000e-2 * t130 - 0.51086165526666666666666666666666666666666666666667e-2 * t135) / t28
  t145 = 0.18311447306006545054854346104378990962041954983034e-3 * t41 * t1 * t122 * t112 * t51
  t147 = t48 ** 2
  t158 = 0.58482236226346462072622386637590534819724553404281e0 * t41 * t43 / t147 * (-0.29149603883333333333333333333333333333333333333333e-1 * t124 - 0.10197154565000000000000000000000000000000000000000e-1 * t126 - 0.18581078242500000000000000000000000000000000000000e-2 * t130 - 0.27959640330000000000000000000000000000000000000000e-2 * t135) / t50
  t166 = params.gamma ** 2
  t167 = 0.1e1 / t166
  t169 = t79 ** 2
  t170 = 0.1e1 / t169
  t179 = t116 + t140 - t145 - t158
  t193 = -0.7e1 / 0.288e3 * s0 / t7 / t60 / r0 * t37 * t69 + t72 * t167 * t170 * t82 * t87 * t88 / t90 / t58 * t1 * t93 * t6 * t179 * t78 / 0.3072e4 - 0.7e1 / 0.4608e4 * t84 / t21 / t85 / r0 * t88 * t91 * t95
  t196 = t104 ** 2
  t197 = 0.1e1 / t196
  t211 = 0.1e1 / t108
  vrho_0_ = -t30 + t54 + t59 * t109 + r0 * (t116 + t140 - t145 - t158 + t59 * (params.beta * t193 * t106 - t100 * t73 * t197 * (params.beta * t167 * t170 * t99 * t179 * t76 * t78 + t101 * t80 * t193)) * t211)
  t227 = t62 * t37 * t65 * t18 * t67 * t5 / 0.96e2 + t72 * t81 * s0 * t96 / 0.1536e4
  t230 = params.beta ** 2
  vsigma_0_ = r0 * params.gamma * t58 * (-t230 * t99 * t167 * t197 * t80 * t227 + params.beta * t227 * t106) * t211
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  r0 = r
  pol = pol_fxc(p, (r0/2, r0/2), (s/4 if s is not None else None, s/4 if s is not None else None, s/4 if s is not None else None), (None, None), (None, None))
  res = {}
  # Extract v2rho2 from polarized output
  v2rho2_pol = pol.get('v2rho2', None)
  if v2rho2_pol is not None:
    d11, d12, d22 = v2rho2_pol[..., 0], v2rho2_pol[..., 1], v2rho2_pol[..., 2]
    res['v2rho2'] = 0.25 * (d11 + 2*d12 + d22)
  # Extract v2rhosigma from polarized output
  v2rhosigma_pol = pol.get('v2rhosigma', None)
  if v2rhosigma_pol is not None:
    # Broadcast scalars to match array shape (Maple may emit some derivatives as scalar 0)
    d13 = jnp.asarray(v2rhosigma_pol[..., 0]) + jnp.zeros_like(r0)
    d14 = jnp.asarray(v2rhosigma_pol[..., 1]) + jnp.zeros_like(r0)
    d15 = jnp.asarray(v2rhosigma_pol[..., 2]) + jnp.zeros_like(r0)
    d23 = jnp.asarray(v2rhosigma_pol[..., 3]) + jnp.zeros_like(r0)
    d24 = jnp.asarray(v2rhosigma_pol[..., 4]) + jnp.zeros_like(r0)
    d25 = jnp.asarray(v2rhosigma_pol[..., 5]) + jnp.zeros_like(r0)
    res['v2rhosigma'] = (1/8) * (d13 + d14 + d15 + d23 + d24 + d25)
  # Extract v2sigma2 from polarized output
  v2sigma2_pol = pol.get('v2sigma2', None)
  if v2sigma2_pol is not None:
    # Broadcast scalars to match array shape
    d33 = jnp.asarray(v2sigma2_pol[..., 0]) + jnp.zeros_like(r0)
    d34 = jnp.asarray(v2sigma2_pol[..., 1]) + jnp.zeros_like(r0)
    d35 = jnp.asarray(v2sigma2_pol[..., 2]) + jnp.zeros_like(r0)
    d44 = jnp.asarray(v2sigma2_pol[..., 3]) + jnp.zeros_like(r0)
    d45 = jnp.asarray(v2sigma2_pol[..., 4]) + jnp.zeros_like(r0)
    d55 = jnp.asarray(v2sigma2_pol[..., 5]) + jnp.zeros_like(r0)
    res['v2sigma2'] = (1/16) * (d33 + 2*d34 + 2*d35 + d44 + 2*d45 + d55)
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 0.1e1 <= f.p.zeta_threshold
  t2 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = f.my_piecewise3(t1, t3, 1)
  t5 = t4 ** 2
  t6 = t5 * t4
  t7 = params.gamma * t6
  t8 = r0 ** 2
  t9 = t8 * r0
  t10 = r0 ** (0.1e1 / 0.3e1)
  t12 = 0.1e1 / t10 / t9
  t14 = 2 ** (0.1e1 / 0.3e1)
  t17 = 3 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = 0.1e1 / jnp.pi
  t21 = t20 ** (0.1e1 / 0.3e1)
  t23 = 4 ** (0.1e1 / 0.3e1)
  t25 = 0.1e1 / t5 * t18 / t21 * t23
  t28 = params.BB * params.beta
  t29 = params.gamma ** 2
  t30 = 0.1e1 / t29
  t31 = t28 * t30
  t32 = t17 * t21
  t33 = t23 ** 2
  t36 = t32 * t33 / t10
  t38 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t36
  t39 = jnp.sqrt(t36)
  t42 = t36 ** 0.15e1
  t44 = t21 ** 2
  t45 = t18 * t44
  t46 = t10 ** 2
  t49 = t45 * t23 / t46
  t51 = 0.37978500000000000000000000000000000000000000000000e1 * t39 + 0.89690000000000000000000000000000000000000000000000e0 * t36 + 0.20477500000000000000000000000000000000000000000000e0 * t42 + 0.12323500000000000000000000000000000000000000000000e0 * t49
  t54 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t51
  t55 = jnp.log(t54)
  t59 = f.my_piecewise3(t1, t2 * f.p.zeta_threshold, 1)
  t65 = (0.2e1 * t59 - 0.2e1) / (0.2e1 * t14 - 0.2e1)
  t67 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t36
  t72 = 0.51785000000000000000000000000000000000000000000000e1 * t39 + 0.90577500000000000000000000000000000000000000000000e0 * t36 + 0.11003250000000000000000000000000000000000000000000e0 * t42 + 0.12417750000000000000000000000000000000000000000000e0 * t49
  t75 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t72
  t76 = jnp.log(t75)
  t81 = 0.1e1 / params.gamma
  t83 = 0.1e1 / t6
  t85 = jnp.exp(-(-0.621814e-1 * t38 * t55 + 0.19751673498613801407483339618206552048944131217655e-1 * t65 * t67 * t76) * t81 * t83)
  t86 = t85 - 0.1e1
  t87 = t86 ** 2
  t88 = 0.1e1 / t87
  t89 = s0 ** 2
  t90 = t88 * t89
  t91 = t8 ** 2
  t93 = 0.1e1 / t46 / t91
  t94 = t90 * t93
  t95 = t31 * t94
  t96 = t14 ** 2
  t97 = t5 ** 2
  t101 = t96 / t97 / t6 * t17
  t102 = 0.1e1 / t44
  t103 = t102 * t33
  t105 = 0.1e1 / t10 / r0
  t106 = t33 * t105
  t110 = t51 ** 2
  t111 = 0.1e1 / t110
  t112 = t38 * t111
  t114 = 0.1e1 / t39 * t17
  t115 = t21 * t33
  t116 = t115 * t105
  t117 = t114 * t116
  t119 = t32 * t106
  t121 = t36 ** 0.5e0
  t122 = t121 * t17
  t123 = t122 * t116
  t128 = t45 * t23 / t46 / r0
  t130 = -0.63297500000000000000000000000000000000000000000000e0 * t117 - 0.29896666666666666666666666666666666666666666666667e0 * t119 - 0.10238750000000000000000000000000000000000000000000e0 * t123 - 0.82156666666666666666666666666666666666666666666667e-1 * t128
  t131 = 0.1e1 / t54
  t132 = t130 * t131
  t135 = t65 * t17
  t140 = t65 * t67
  t141 = t72 ** 2
  t142 = 0.1e1 / t141
  t147 = -0.86308333333333333333333333333333333333333333333334e0 * t117 - 0.30192500000000000000000000000000000000000000000000e0 * t119 - 0.55016250000000000000000000000000000000000000000000e-1 * t123 - 0.82785000000000000000000000000000000000000000000000e-1 * t128
  t149 = 0.1e1 / t75
  t150 = t142 * t147 * t149
  t153 = 0.11073470983333333333333333333333333333333333333333e-2 * t32 * t106 * t55 + 0.10000000000000000000000000000000000000000000000000e1 * t112 * t132 - 0.18311447306006545054854346104378990962041954983034e-3 * t135 * t115 * t105 * t76 - 0.58482236226346462072622386637590534819724553404280e0 * t140 * t150
  t154 = t153 * t85
  t156 = t101 * t103 * t154
  t159 = 0.1e1 / t86
  t162 = t28 * t81 * t159 * t89
  t163 = t91 * r0
  t165 = 0.1e1 / t46 / t163
  t167 = 0.1e1 / t97
  t170 = t17 * t102 * t33
  t174 = -0.7e1 / 0.288e3 * s0 * t12 * t14 * t25 + t95 * t156 / 0.3072e4 - 0.7e1 / 0.4608e4 * t162 * t165 * t96 * t167 * t170
  t175 = params.beta * t174
  t176 = params.beta * t81
  t178 = 0.1e1 / t10 / t8
  t183 = t93 * t96
  t188 = s0 * t178 * t14 * t25 / 0.96e2 + t162 * t183 * t167 * t170 / 0.3072e4
  t191 = t176 * t159 * t188 + 0.1e1
  t193 = t81 / t191
  t195 = params.beta * t188
  t196 = t191 ** 2
  t198 = t81 / t196
  t200 = params.beta * t30 * t88
  t202 = t83 * t85
  t207 = t200 * t188 * t153 * t202 + t176 * t159 * t174
  t208 = t198 * t207
  t210 = t175 * t193 - t195 * t208
  t211 = t210 ** 2
  t213 = t195 * t193 + 0.1e1
  t214 = t213 ** 2
  t215 = 0.1e1 / t214
  t219 = t33 * t178
  t221 = t32 * t219 * t55
  t223 = t110 ** 2
  t224 = 0.1e1 / t223
  t225 = t38 * t224
  t226 = t130 ** 2
  t227 = t54 ** 2
  t228 = 0.1e1 / t227
  t229 = t226 * t228
  t230 = t225 * t229
  t233 = 0.1e1 / t110 / t51
  t234 = t38 * t233
  t235 = t226 * t131
  t236 = t234 * t235
  t240 = 0.1e1 / t39 / t36 * t18
  t241 = t44 * t23
  t243 = 0.1e1 / t46 / t8
  t244 = t241 * t243
  t245 = t240 * t244
  t247 = t115 * t178
  t248 = t114 * t247
  t250 = t32 * t219
  t252 = t36 ** (-0.5e0)
  t253 = t252 * t18
  t254 = t253 * t244
  t256 = t122 * t247
  t259 = t45 * t23 * t243
  t261 = -0.42198333333333333333333333333333333333333333333333e0 * t245 + 0.84396666666666666666666666666666666666666666666666e0 * t248 + 0.39862222222222222222222222222222222222222222222223e0 * t250 + 0.68258333333333333333333333333333333333333333333333e-1 * t254 + 0.13651666666666666666666666666666666666666666666667e0 * t256 + 0.13692777777777777777777777777777777777777777777778e0 * t259
  t262 = t261 * t131
  t263 = t112 * t262
  t272 = 0.1e1 / t29 / params.gamma
  t273 = t28 * t272
  t275 = 0.1e1 / t87 / t86
  t276 = t275 * t89
  t277 = t276 * t93
  t279 = t97 ** 2
  t281 = 0.1e1 / t279 / t5
  t283 = t96 * t281 * t17
  t284 = t153 ** 2
  t285 = t85 ** 2
  t288 = t283 * t103 * t284 * t285
  t291 = t90 * t165
  t292 = t31 * t291
  t296 = t32 * t33
  t297 = t105 * t111
  t299 = t296 * t297 * t132
  t306 = t135 * t115 * t178 * t76
  t308 = t65 * t32
  t310 = t308 * t106 * t150
  t313 = 0.1e1 / t141 / t72
  t314 = t147 ** 2
  t316 = t313 * t314 * t149
  t317 = t140 * t316
  t325 = -0.57538888888888888888888888888888888888888888888889e0 * t245 + 0.11507777777777777777777777777777777777777777777778e1 * t248 + 0.40256666666666666666666666666666666666666666666667e0 * t250 + 0.36677500000000000000000000000000000000000000000000e-1 * t254 + 0.73355000000000000000000000000000000000000000000000e-1 * t256 + 0.13797500000000000000000000000000000000000000000000e0 * t259
  t327 = t142 * t325 * t149
  t328 = t140 * t327
  t330 = t141 ** 2
  t331 = 0.1e1 / t330
  t333 = t75 ** 2
  t334 = 0.1e1 / t333
  t335 = t331 * t314 * t334
  t336 = t140 * t335
  t338 = -0.14764627977777777777777777777777777777777777777777e-2 * t221 - 0.35616666666666666666666666666666666666666666666666e-1 * t299 - 0.20000000000000000000000000000000000000000000000000e1 * t236 + 0.10000000000000000000000000000000000000000000000000e1 * t263 + 0.16081979498692535066756296899072713062105388428051e2 * t230 + 0.24415263074675393406472461472505321282722606644045e-3 * t306 + 0.10843581300301739842632067522386578331157260943710e-1 * t310 + 0.11696447245269292414524477327518106963944910680856e1 * t317 - 0.58482236226346462072622386637590534819724553404280e0 * t328 - 0.17315859105681463759666483083807725165579399831905e2 * t336
  t341 = t101 * t103 * t338 * t85
  t347 = t283 * t103 * t284 * t85
  t352 = 0.1e1 / t46 / t91 / t8
  t358 = 0.35e2 / 0.432e3 * s0 / t10 / t91 * t14 * t25 + t273 * t277 * t288 / 0.1536e4 - 0.7e1 / 0.2304e4 * t292 * t156 + t95 * t341 / 0.3072e4 - t273 * t94 * t347 / 0.3072e4 + 0.119e3 / 0.13824e5 * t162 * t352 * t96 * t167 * t170
  t359 = params.beta * t358
  t364 = 0.1e1 / t196 / t191
  t366 = t207 ** 2
  t367 = t81 * t364 * t366
  t370 = params.beta * t272
  t371 = t370 * t275
  t372 = t188 * t284
  t374 = 0.1e1 / t97 / t5
  t375 = t374 * t285
  t386 = t370 * t88
  t387 = t374 * t85
  t392 = 0.2e1 * t200 * t174 * t153 * t202 + t200 * t188 * t338 * t202 + t176 * t159 * t358 + 0.2e1 * t371 * t372 * t375 - t386 * t372 * t387
  t393 = t198 * t392
  t395 = -0.2e1 * t175 * t208 + t359 * t193 + 0.2e1 * t195 * t367 - t195 * t393
  t396 = 0.1e1 / t213
  t410 = 0.51947577317044391278999449251423175496738199495715e2 * t140 * t331 * t325 * t334 * t147
  t415 = 0.35089341735807877243573431982554320891834732042568e1 * t140 * t313 * t147 * t149 * t325
  t419 = 0.71233333333333333333333333333333333333333333333331e-1 * t296 * t178 * t111 * t132
  t422 = 0.53424999999999999999999999999999999999999999999999e-1 * t296 * t297 * t262
  t426 = 0.85917975471764868594145516183295969534298037676861e0 * t296 * t105 * t224 * t229
  t430 = 0.10685000000000000000000000000000000000000000000000e0 * t296 * t105 * t233 * t235
  t434 = 0.56968947174242584615102410102512416326352748836105e-3 * t135 * t115 * t12 * t76
  t435 = t226 * t130
  t438 = 0.60000000000000000000000000000000000000000000000000e1 * t225 * t435 * t131
  t451 = t29 ** 2
  t452 = 0.1e1 / t451
  t453 = t28 * t452
  t454 = t87 ** 2
  t455 = 0.1e1 / t454
  t463 = t96 / t279 / t97 / t4 * t17
  t464 = t284 * t153
  t465 = t285 * t85
  t478 = t281 * t17 * t102
  t480 = t285 * t338
  t503 = 0.48245938496077605200268890697218139186316165284153e2 * t225 * t261 * t228 * t130
  t506 = 0.60000000000000000000000000000000000000000000000000e1 * t234 * t132 * t261
  t507 = t33 * t12
  t510 = 0.34450798614814814814814814814814814814814814814813e-2 * t32 * t507 * t55
  t513 = 0.32530743900905219527896202567159734993471782831130e-1 * t308 * t106 * t316
  t516 = 0.21687162600603479685264135044773156662314521887420e-1 * t308 * t219 * t150
  t519 = 0.16265371950452609763948101283579867496735891415565e-1 * t308 * t106 * t327
  t522 = 0.48159733137676571081572406076840235616767705782485e0 * t308 * t106 * t335
  t525 = t314 * t147
  t531 = 0.10254018858216406658218194626490193680059335835414e4 * t140 / t330 / t141 * t525 / t333 / t75
  t537 = 0.10389515463408878255799889850284635099347639899143e3 * t140 / t330 / t72 * t525 * t334
  t542 = 0.1e1 / t91
  t543 = 0.1e1 / t39 / t49 * t20 * t542 / 0.4e1
  t546 = 0.1e1 / t46 / t9
  t547 = t241 * t546
  t548 = t240 * t547
  t550 = t115 * t12
  t551 = t114 * t550
  t553 = t32 * t507
  t555 = t36 ** (-0.15e1)
  t557 = t555 * t20 * t542
  t559 = t253 * t547
  t561 = t122 * t550
  t564 = t45 * t23 * t546
  t570 = 0.58482236226346462072622386637590534819724553404280e0 * t140 * t142 * (-0.34523333333333333333333333333333333333333333333333e1 * t543 + 0.23015555555555555555555555555555555555555555555556e1 * t548 - 0.26851481481481481481481481481481481481481481481482e1 * t551 - 0.93932222222222222222222222222222222222222222222223e0 * t553 + 0.73355000000000000000000000000000000000000000000000e-1 * t557 - 0.14671000000000000000000000000000000000000000000000e0 * t559 - 0.17116166666666666666666666666666666666666666666667e0 * t561 - 0.36793333333333333333333333333333333333333333333333e0 * t564) * t149
  t571 = t503 + t438 - t506 + t510 - t513 - t516 + t519 + t522 - t531 + t537 - t570
  t575 = 0.35089341735807877243573431982554320891834732042568e1 * t140 * t331 * t525 * t149
  t581 = 0.96491876992155210400537781394436278372632330568306e2 * t38 / t223 / t51 * t435 * t228
  t593 = 0.10000000000000000000000000000000000000000000000000e1 * t112 * (-0.25319000000000000000000000000000000000000000000000e1 * t543 + 0.16879333333333333333333333333333333333333333333333e1 * t548 - 0.19692555555555555555555555555555555555555555555555e1 * t551 - 0.93011851851851851851851851851851851851851851851854e0 * t553 + 0.13651666666666666666666666666666666666666666666667e0 * t557 - 0.27303333333333333333333333333333333333333333333333e0 * t559 - 0.31853888888888888888888888888888888888888888888890e0 * t561 - 0.36514074074074074074074074074074074074074074074075e0 * t564) * t131
  t601 = 0.51726012919273400298984252201052768390886626637712e3 * t38 / t223 / t110 * t435 / t227 / t54
  t602 = -t410 - t575 + t415 + t419 - t422 - t426 - t581 + t593 + t601 + t430 - t434
  t603 = t571 + t602
  t630 = -0.455e3 / 0.1296e4 * s0 / t10 / t163 * t14 * t25 + t453 * t455 * t89 * t93 * t463 * t103 * t464 * t465 / 0.512e3 - 0.7e1 / 0.768e3 * t273 * t276 * t165 * t288 + t273 * t276 * t183 * t478 * t33 * t153 * t480 / 0.512e3 - t453 * t277 * t463 * t103 * t464 * t285 / 0.512e3 + 0.119e3 / 0.4608e4 * t31 * t90 * t352 * t156 - 0.7e1 / 0.1536e4 * t292 * t341 + 0.7e1 / 0.1536e4 * t273 * t291 * t347 + t95 * t101 * t103 * t603 * t85 / 0.3072e4 - t273 * t90 * t183 * t478 * t33 * t338 * t154 / 0.1024e4 + t453 * t94 * t463 * t103 * t464 * t85 / 0.3072e4 - 0.595e3 / 0.10368e5 * t162 / t46 / t91 / t9 * t96 * t167 * t170
  t639 = t196 ** 2
  t651 = params.beta * t452
  t653 = t188 * t464
  t655 = 0.1e1 / t279 / t4
  t660 = t174 * t284
  t701 = 0.6e1 * t370 * t275 * t188 * t153 * t374 * t480 - 0.3e1 * t370 * t88 * t188 * t338 * t374 * t154 - 0.6e1 * t651 * t275 * t653 * t655 * t285 + 0.6e1 * t651 * t455 * t653 * t655 * t465 + t651 * t88 * t653 * t655 * t85 + 0.3e1 * t200 * t358 * t153 * t202 + 0.3e1 * t200 * t174 * t338 * t202 + t200 * t188 * t603 * t202 + t176 * t159 * t630 + 0.6e1 * t371 * t660 * t375 - 0.3e1 * t386 * t660 * t387
  t707 = -t410 + t415 + t419 - t422 - t426 + t430 - t434 + t438 + 0.2e1 * t7 * t211 * t210 / t214 / t213 + t7 * (params.beta * t630 * t193 - 0.3e1 * t359 * t208 + 0.6e1 * t175 * t367 - 0.3e1 * t175 * t393 - 0.6e1 * t195 * t81 / t639 * t366 * t207 + 0.6e1 * t195 * t81 * t364 * t207 * t392 - t195 * t198 * t701) * t396 - t506 + t510
  t712 = -0.3e1 * t7 * t395 * t215 * t210 + t503 - t513 - t516 + t519 + t522 - t531 + t537 - t570 - t575 - t581 + t593 + t601
  v3rho3_0_ = -0.3e1 * t7 * t211 * t215 - 0.44293883933333333333333333333333333333333333333332e-2 * t221 + 0.48245938496077605200268890697218139186316165284153e2 * t230 - 0.60000000000000000000000000000000000000000000000000e1 * t236 + 0.30000000000000000000000000000000000000000000000000e1 * t263 + 0.3e1 * t7 * t395 * t396 + 0.35089341735807877243573431982554320891834732042568e1 * t317 - 0.17544670867903938621786715991277160445917366021284e1 * t328 - 0.51947577317044391278999449251423175496738199495715e2 * t336 + 0.32530743900905219527896202567159734993471782831130e-1 * t310 - 0.10685000000000000000000000000000000000000000000000e0 * t299 + 0.73245789224026180219417384417515963848167819932136e-3 * t306 + r0 * (t707 + t712)

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 0.1e1 <= f.p.zeta_threshold
  t2 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t4 = f.my_piecewise3(t1, t2 * f.p.zeta_threshold, 1)
  t7 = 2 ** (0.1e1 / 0.3e1)
  t11 = (0.2e1 * t4 - 0.2e1) / (0.2e1 * t7 - 0.2e1)
  t12 = 3 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / jnp.pi
  t14 = t13 ** (0.1e1 / 0.3e1)
  t15 = t12 * t14
  t16 = 4 ** (0.1e1 / 0.3e1)
  t17 = t16 ** 2
  t18 = r0 ** (0.1e1 / 0.3e1)
  t21 = t15 * t17 / t18
  t23 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t21
  t24 = t11 * t23
  t25 = jnp.sqrt(t21)
  t28 = t21 ** 0.15e1
  t30 = t12 ** 2
  t31 = t14 ** 2
  t32 = t30 * t31
  t33 = t18 ** 2
  t36 = t32 * t16 / t33
  t38 = 0.51785000000000000000000000000000000000000000000000e1 * t25 + 0.90577500000000000000000000000000000000000000000000e0 * t21 + 0.11003250000000000000000000000000000000000000000000e0 * t28 + 0.12417750000000000000000000000000000000000000000000e0 * t36
  t39 = t38 ** 2
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t39
  t44 = 0.1e1 / t25 * t12
  t45 = t14 * t17
  t47 = 0.1e1 / t18 / r0
  t48 = t45 * t47
  t49 = t44 * t48
  t51 = t17 * t47
  t52 = t15 * t51
  t54 = t21 ** 0.5e0
  t55 = t54 * t12
  t56 = t55 * t48
  t61 = t32 * t16 / t33 / r0
  t63 = -0.86308333333333333333333333333333333333333333333334e0 * t49 - 0.30192500000000000000000000000000000000000000000000e0 * t52 - 0.55016250000000000000000000000000000000000000000000e-1 * t56 - 0.82785000000000000000000000000000000000000000000000e-1 * t61
  t64 = t63 ** 2
  t65 = t64 * t63
  t69 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t38
  t70 = t69 ** 2
  t72 = 0.1e1 / t70 / t69
  t73 = t42 * t65 * t72
  t74 = t24 * t73
  t77 = 0.1e1 / t40 / t38
  t79 = 0.1e1 / t70
  t80 = t77 * t65 * t79
  t81 = t24 * t80
  t83 = 0.1e1 / t39
  t87 = 0.1e1 / t25 / t36 * t13 / 0.4e1
  t88 = r0 ** 2
  t89 = t88 ** 2
  t90 = 0.1e1 / t89
  t91 = t87 * t90
  t95 = 0.1e1 / t25 / t21 * t30
  t96 = t31 * t16
  t97 = t88 * r0
  t99 = 0.1e1 / t33 / t97
  t100 = t96 * t99
  t101 = t95 * t100
  t104 = 0.1e1 / t18 / t97
  t105 = t45 * t104
  t106 = t44 * t105
  t108 = t17 * t104
  t109 = t15 * t108
  t111 = t21 ** (-0.15e1)
  t112 = t111 * t13
  t113 = t112 * t90
  t115 = t21 ** (-0.5e0)
  t116 = t115 * t30
  t117 = t116 * t100
  t119 = t55 * t105
  t122 = t32 * t16 * t99
  t124 = -0.34523333333333333333333333333333333333333333333333e1 * t91 + 0.23015555555555555555555555555555555555555555555556e1 * t101 - 0.26851481481481481481481481481481481481481481481482e1 * t106 - 0.93932222222222222222222222222222222222222222222223e0 * t109 + 0.73355000000000000000000000000000000000000000000000e-1 * t113 - 0.14671000000000000000000000000000000000000000000000e0 * t117 - 0.17116166666666666666666666666666666666666666666667e0 * t119 - 0.36793333333333333333333333333333333333333333333333e0 * t122
  t126 = 0.1e1 / t69
  t127 = t83 * t124 * t126
  t128 = t24 * t127
  t130 = t11 * t15
  t131 = t39 * t38
  t132 = 0.1e1 / t131
  t134 = t132 * t64 * t126
  t136 = t130 * t51 * t134
  t139 = 0.1e1 / t18 / t88
  t140 = t17 * t139
  t142 = t83 * t63 * t126
  t144 = t130 * t140 * t142
  t147 = 0.1e1 / t33 / t88
  t148 = t96 * t147
  t149 = t95 * t148
  t151 = t45 * t139
  t152 = t44 * t151
  t154 = t15 * t140
  t156 = t116 * t148
  t158 = t55 * t151
  t161 = t32 * t16 * t147
  t163 = -0.57538888888888888888888888888888888888888888888889e0 * t149 + 0.11507777777777777777777777777777777777777777777778e1 * t152 + 0.40256666666666666666666666666666666666666666666667e0 * t154 + 0.36677500000000000000000000000000000000000000000000e-1 * t156 + 0.73355000000000000000000000000000000000000000000000e-1 * t158 + 0.13797500000000000000000000000000000000000000000000e0 * t161
  t165 = t83 * t163 * t126
  t167 = t130 * t51 * t165
  t169 = 0.1e1 / t40
  t170 = t169 * t64
  t171 = t170 * t79
  t173 = t130 * t51 * t171
  t175 = t2 ** 2
  t176 = f.my_piecewise3(t1, t175, 1)
  t177 = t176 ** 2
  t178 = t177 * t176
  t179 = params.gamma * t178
  t180 = t89 * r0
  t182 = 0.1e1 / t18 / t180
  t189 = 0.1e1 / t177 * t30 / t14 * t16
  t192 = params.BB * params.beta
  t193 = params.gamma ** 2
  t194 = t193 ** 2
  t195 = 0.1e1 / t194
  t196 = t192 * t195
  t198 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t21
  t203 = 0.37978500000000000000000000000000000000000000000000e1 * t25 + 0.89690000000000000000000000000000000000000000000000e0 * t21 + 0.20477500000000000000000000000000000000000000000000e0 * t28 + 0.12323500000000000000000000000000000000000000000000e0 * t36
  t206 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t203
  t207 = jnp.log(t206)
  t210 = jnp.log(t69)
  t215 = 0.1e1 / params.gamma
  t217 = 0.1e1 / t178
  t219 = jnp.exp(-(-0.621814e-1 * t198 * t207 + 0.19751673498613801407483339618206552048944131217655e-1 * t11 * t23 * t210) * t215 * t217)
  t220 = t219 - 0.1e1
  t221 = t220 ** 2
  t222 = t221 ** 2
  t223 = 0.1e1 / t222
  t224 = s0 ** 2
  t225 = t223 * t224
  t227 = 0.1e1 / t33 / t89
  t228 = t225 * t227
  t230 = t7 ** 2
  t231 = t177 ** 2
  t233 = t231 ** 2
  t235 = 0.1e1 / t233 / t231 / t176
  t237 = t230 * t235 * t12
  t238 = 0.1e1 / t31
  t239 = t238 * t17
  t243 = t203 ** 2
  t244 = 0.1e1 / t243
  t245 = t198 * t244
  t250 = -0.63297500000000000000000000000000000000000000000000e0 * t49 - 0.29896666666666666666666666666666666666666666666667e0 * t52 - 0.10238750000000000000000000000000000000000000000000e0 * t56 - 0.82156666666666666666666666666666666666666666666667e-1 * t61
  t251 = 0.1e1 / t206
  t252 = t250 * t251
  t255 = t11 * t12
  t262 = 0.11073470983333333333333333333333333333333333333333e-2 * t15 * t51 * t207 + 0.10000000000000000000000000000000000000000000000000e1 * t245 * t252 - 0.18311447306006545054854346104378990962041954983034e-3 * t255 * t45 * t47 * t210 - 0.58482236226346462072622386637590534819724553404280e0 * t24 * t142
  t263 = t262 ** 2
  t264 = t263 * t262
  t265 = t219 ** 2
  t266 = t265 * t219
  t269 = t237 * t239 * t264 * t266
  t273 = 0.1e1 / t193 / params.gamma
  t274 = t192 * t273
  t276 = 0.1e1 / t221 / t220
  t277 = t276 * t224
  t279 = 0.1e1 / t33 / t180
  t280 = t277 * t279
  t283 = 0.1e1 / t233 / t177
  t285 = t230 * t283 * t12
  t288 = t285 * t239 * t263 * t265
  t291 = t227 * t230
  t292 = t277 * t291
  t293 = t274 * t292
  t295 = t283 * t12 * t238
  t296 = t17 * t262
  t300 = t15 * t17
  t301 = t47 * t244
  t305 = t243 * t203
  t306 = 0.1e1 / t305
  t307 = t198 * t306
  t308 = t250 ** 2
  t309 = t308 * t251
  t318 = -0.42198333333333333333333333333333333333333333333333e0 * t149 + 0.84396666666666666666666666666666666666666666666666e0 * t152 + 0.39862222222222222222222222222222222222222222222223e0 * t154 + 0.68258333333333333333333333333333333333333333333333e-1 * t156 + 0.13651666666666666666666666666666666666666666666667e0 * t158 + 0.13692777777777777777777777777777777777777777777778e0 * t161
  t319 = t318 * t251
  t322 = t243 ** 2
  t323 = 0.1e1 / t322
  t324 = t198 * t323
  t325 = t206 ** 2
  t326 = 0.1e1 / t325
  t327 = t308 * t326
  t343 = -0.14764627977777777777777777777777777777777777777777e-2 * t15 * t140 * t207 - 0.35616666666666666666666666666666666666666666666666e-1 * t300 * t301 * t252 - 0.20000000000000000000000000000000000000000000000000e1 * t307 * t309 + 0.10000000000000000000000000000000000000000000000000e1 * t245 * t319 + 0.16081979498692535066756296899072713062105388428051e2 * t324 * t327 + 0.24415263074675393406472461472505321282722606644045e-3 * t255 * t45 * t139 * t210 + 0.10843581300301739842632067522386578331157260943710e-1 * t130 * t51 * t142 + 0.11696447245269292414524477327518106963944910680856e1 * t24 * t134 - 0.58482236226346462072622386637590534819724553404280e0 * t24 * t165 - 0.17315859105681463759666483083807725165579399831905e2 * t24 * t171
  t344 = t265 * t343
  t346 = t295 * t296 * t344
  t349 = t277 * t227
  t353 = t237 * t239 * t264 * t265
  t356 = 0.1e1 / t193
  t357 = t192 * t356
  t358 = 0.1e1 / t221
  t359 = t358 * t224
  t360 = t89 * t88
  t362 = 0.1e1 / t33 / t360
  t363 = t359 * t362
  t364 = t357 * t363
  t368 = t230 / t231 / t178 * t12
  t369 = t262 * t219
  t371 = t368 * t239 * t369
  t374 = t359 * t279
  t375 = t357 * t374
  t378 = t368 * t239 * t343 * t219
  t382 = t263 * t219
  t384 = t285 * t239 * t382
  t387 = t359 * t227
  t388 = t357 * t387
  t391 = t324 * t318 * t326 * t250
  t393 = t308 * t250
  t394 = t393 * t251
  t395 = t324 * t394
  t398 = t307 * t252 * t318
  t404 = t15 * t108 * t207
  t410 = 0.48245938496077605200268890697218139186316165284153e2 * t391 + 0.60000000000000000000000000000000000000000000000000e1 * t395 - 0.60000000000000000000000000000000000000000000000000e1 * t398 - 0.10254018858216406658218194626490193680059335835414e4 * t74 + 0.10389515463408878255799889850284635099347639899143e3 * t81 - 0.58482236226346462072622386637590534819724553404280e0 * t128 + 0.34450798614814814814814814814814814814814814814813e-2 * t404 - 0.32530743900905219527896202567159734993471782831130e-1 * t136 - 0.21687162600603479685264135044773156662314521887420e-1 * t144 + 0.16265371950452609763948101283579867496735891415565e-1 * t167 + 0.48159733137676571081572406076840235616767705782485e0 * t173
  t412 = t79 * t63
  t414 = t24 * t169 * t163 * t412
  t417 = t169 * t65 * t126
  t418 = t24 * t417
  t421 = t126 * t163
  t423 = t24 * t132 * t63 * t421
  t425 = t139 * t244
  t427 = t300 * t425 * t252
  t430 = t300 * t301 * t319
  t432 = t47 * t323
  t434 = t300 * t432 * t327
  t437 = 0.1e1 / t322 / t203
  t438 = t198 * t437
  t439 = t393 * t326
  t440 = t438 * t439
  t450 = -0.25319000000000000000000000000000000000000000000000e1 * t91 + 0.16879333333333333333333333333333333333333333333333e1 * t101 - 0.19692555555555555555555555555555555555555555555555e1 * t106 - 0.93011851851851851851851851851851851851851851851854e0 * t109 + 0.13651666666666666666666666666666666666666666666667e0 * t113 - 0.27303333333333333333333333333333333333333333333333e0 * t117 - 0.31853888888888888888888888888888888888888888888890e0 * t119 - 0.36514074074074074074074074074074074074074074074075e0 * t122
  t451 = t450 * t251
  t452 = t245 * t451
  t455 = 0.1e1 / t322 / t243
  t456 = t198 * t455
  t458 = 0.1e1 / t325 / t206
  t459 = t393 * t458
  t460 = t456 * t459
  t464 = t300 * t47 * t306 * t309
  t468 = t255 * t45 * t104 * t210
  t470 = -0.51947577317044391278999449251423175496738199495715e2 * t414 - 0.35089341735807877243573431982554320891834732042568e1 * t418 + 0.35089341735807877243573431982554320891834732042568e1 * t423 + 0.71233333333333333333333333333333333333333333333331e-1 * t427 - 0.53424999999999999999999999999999999999999999999999e-1 * t430 - 0.85917975471764868594145516183295969534298037676861e0 * t434 - 0.96491876992155210400537781394436278372632330568306e2 * t440 + 0.10000000000000000000000000000000000000000000000000e1 * t452 + 0.51726012919273400298984252201052768390886626637712e3 * t460 + 0.10685000000000000000000000000000000000000000000000e0 * t464 - 0.56968947174242584615102410102512416326352748836105e-3 * t468
  t471 = t410 + t470
  t474 = t368 * t239 * t471 * t219
  t477 = t359 * t291
  t478 = t274 * t477
  t479 = t17 * t343
  t481 = t295 * t479 * t369
  t487 = t237 * t239 * t264 * t219
  t490 = 0.1e1 / t220
  t493 = t192 * t215 * t490 * t224
  t496 = 0.1e1 / t33 / t89 / t97
  t498 = 0.1e1 / t231
  t501 = t12 * t238 * t17
  t505 = -0.455e3 / 0.1296e4 * s0 * t182 * t7 * t189 + t196 * t228 * t269 / 0.512e3 - 0.7e1 / 0.768e3 * t274 * t280 * t288 + t293 * t346 / 0.512e3 - t196 * t349 * t353 / 0.512e3 + 0.119e3 / 0.4608e4 * t364 * t371 - 0.7e1 / 0.1536e4 * t375 * t378 + 0.7e1 / 0.1536e4 * t274 * t374 * t384 + t388 * t474 / 0.3072e4 - t478 * t481 / 0.1024e4 + t196 * t387 * t487 / 0.3072e4 - 0.595e3 / 0.10368e5 * t493 * t496 * t230 * t498 * t501
  t506 = params.beta * t505
  t507 = params.beta * t215
  t516 = s0 * t139 * t7 * t189 / 0.96e2 + t493 * t291 * t498 * t501 / 0.3072e4
  t519 = t507 * t490 * t516 + 0.1e1
  t521 = t215 / t519
  t524 = 0.1e1 / t18 / t89
  t529 = t274 * t349
  t536 = t274 * t387
  t544 = 0.35e2 / 0.432e3 * s0 * t524 * t7 * t189 + t529 * t288 / 0.1536e4 - 0.7e1 / 0.2304e4 * t375 * t371 + t388 * t378 / 0.3072e4 - t536 * t384 / 0.3072e4 + 0.119e3 / 0.13824e5 * t493 * t362 * t230 * t498 * t501
  t545 = params.beta * t544
  t546 = t519 ** 2
  t548 = t215 / t546
  t550 = params.beta * t356 * t358
  t552 = t217 * t219
  t561 = t279 * t230
  t566 = -0.7e1 / 0.288e3 * s0 * t104 * t7 * t189 + t388 * t371 / 0.3072e4 - 0.7e1 / 0.4608e4 * t493 * t561 * t498 * t501
  t569 = t550 * t516 * t262 * t552 + t507 * t490 * t566
  t570 = t548 * t569
  t573 = params.beta * t566
  t575 = 0.1e1 / t546 / t519
  t576 = t215 * t575
  t577 = t569 ** 2
  t578 = t576 * t577
  t581 = params.beta * t273
  t582 = t581 * t276
  t583 = t516 * t263
  t585 = 0.1e1 / t231 / t177
  t586 = t585 * t265
  t597 = t581 * t358
  t598 = t585 * t219
  t603 = 0.2e1 * t550 * t566 * t262 * t552 + t550 * t516 * t343 * t552 + t507 * t490 * t544 + 0.2e1 * t582 * t583 * t586 - t597 * t583 * t598
  t604 = t548 * t603
  t607 = params.beta * t516
  t608 = t546 ** 2
  t609 = 0.1e1 / t608
  t612 = t215 * t609 * t577 * t569
  t615 = t607 * t215
  t616 = t575 * t569
  t617 = t616 * t603
  t620 = params.beta * t195
  t621 = t620 * t223
  t622 = t516 * t264
  t624 = 0.1e1 / t233 / t176
  t625 = t624 * t266
  t629 = t566 * t263
  t633 = t276 * t516
  t634 = t581 * t633
  t635 = t262 * t585
  t636 = t635 * t344
  t639 = t620 * t276
  t640 = t624 * t265
  t658 = t358 * t516
  t659 = t581 * t658
  t661 = t343 * t585 * t369
  t664 = t620 * t358
  t665 = t624 * t219
  t670 = 0.3e1 * t550 * t544 * t262 * t552 + 0.3e1 * t550 * t566 * t343 * t552 + t550 * t516 * t471 * t552 + t507 * t490 * t505 + 0.6e1 * t582 * t629 * t586 - 0.3e1 * t597 * t629 * t598 + 0.6e1 * t621 * t622 * t625 - 0.6e1 * t639 * t622 * t640 + t664 * t622 * t665 + 0.6e1 * t634 * t636 - 0.3e1 * t659 * t661
  t671 = t548 * t670
  t673 = t506 * t521 - 0.3e1 * t545 * t570 + 0.6e1 * t573 * t578 - 0.3e1 * t573 * t604 - 0.6e1 * t607 * t612 - t607 * t671 + 0.6e1 * t615 * t617
  t675 = t607 * t521 + 0.1e1
  t676 = 0.1e1 / t675
  t685 = -0.41016075432865626632872778505960774720237343341655e4 * t74 + 0.41558061853635513023199559401138540397390559596572e3 * t81 - 0.23392894490538584829048954655036213927889821361712e1 * t128 - 0.13012297560362087811158481026863893997388713132452e0 * t136 - 0.86748650402413918741056540179092626649258087549680e-1 * t144 + 0.65061487801810439055792405134319469986943565662260e-1 * t167 + 0.19263893255070628432628962430736094246707082312994e1 * t173 + 0.4e1 * t179 * t673 * t676 - 0.20779030926817756511599779700569270198695279798286e3 * t414 + 0.14035736694323150897429372793021728356733892817027e2 * t423 + 0.28493333333333333333333333333333333333333333333333e0 * t427 - 0.21370000000000000000000000000000000000000000000000e0 * t430 - 0.34367190188705947437658206473318387813719215070744e1 * t434
  t697 = t573 * t521 - t607 * t570
  t698 = t697 ** 2
  t700 = t675 ** 2
  t702 = 0.1e1 / t700 / t675
  t710 = 0.31035607751564040179390551320631661034531975982628e4 * t456 * t318 * t458 * t308
  t714 = 0.64327917994770140267025187596290852248421553712204e2 * t324 * t450 * t326 * t250
  t717 = t64 ** 2
  t721 = 0.12304822629859687989861833551788232416071203002497e5 * t24 / t40 / t131 * t717 * t72
  t725 = 0.62337092780453269534799339101707810596085839394858e3 * t24 * t42 * t717 * t79
  t726 = t40 ** 2
  t729 = t70 ** 2
  t733 = 0.91082604192152556048340974007871726131433263376469e5 * t24 / t726 * t717 / t729
  t741 = 0.1e1 / t25 * r0 * t182 * t300 / 0.48e2
  t743 = 0.1e1 / t180
  t744 = t87 * t743
  t746 = t96 * t227
  t747 = t95 * t746
  t749 = t45 * t524
  t750 = t44 * t749
  t752 = t17 * t524
  t753 = t15 * t752
  t755 = t21 ** (-0.25e1)
  t758 = t755 * t13 * t182 * t300
  t760 = t112 * t743
  t762 = t116 * t746
  t764 = t55 * t749
  t767 = t32 * t16 * t227
  t773 = 0.58482236226346462072622386637590534819724553404280e0 * t24 * t83 * (-0.28769444444444444444444444444444444444444444444444e1 * t741 + 0.27618666666666666666666666666666666666666666666667e2 * t744 - 0.10229135802469135802469135802469135802469135802469e2 * t747 + 0.89504938271604938271604938271604938271604938271607e1 * t750 + 0.31310740740740740740740740740740740740740740740741e1 * t753 + 0.36677500000000000000000000000000000000000000000000e-1 * t758 - 0.58684000000000000000000000000000000000000000000000e0 * t760 + 0.65204444444444444444444444444444444444444444444445e0 * t762 + 0.57053888888888888888888888888888888888888888888890e0 * t764 + 0.13490888888888888888888888888888888888888888888889e1 * t767) * t126
  t774 = t163 ** 2
  t778 = 0.35089341735807877243573431982554320891834732042568e1 * t24 * t132 * t774 * t126
  t782 = 0.51947577317044391278999449251423175496738199495715e2 * t24 * t169 * t774 * t79
  t786 = 0.14035736694323150897429372793021728356733892817027e2 * t24 * t77 * t717 * t126
  t789 = 0.36000000000000000000000000000000000000000000000000e2 * t324 * t309 * t318
  t792 = 0.11483599538271604938271604938271604938271604938271e-1 * t15 * t752 * t207
  t795 = 0.80000000000000000000000000000000000000000000000000e1 * t307 * t252 * t450
  t796 = t710 + t714 + t721 - t725 - t733 - t773 + t778 - t782 + t786 + t789 - t792 - t795
  t799 = 0.57895126195293126240322668836661767023579398340984e3 * t438 * t327 * t318
  t806 = t545 * t521 - 0.2e1 * t573 * t570 + 0.2e1 * t607 * t578 - t607 * t604
  t807 = t806 ** 2
  t808 = 0.1e1 / t700
  t814 = t235 * t12 * t238
  t823 = 0.1e1 / t194 / params.gamma
  t824 = t192 * t823
  t826 = t233 ** 2
  t829 = t230 / t826 * t12
  t830 = t263 ** 2
  t842 = 0.1e1 / t222 / t220
  t846 = t265 ** 2
  t863 = t343 ** 2
  t883 = t196 * t477 * t814 * t479 * t382 / 0.512e3 + 0.7e1 / 0.192e3 * t196 * t280 * t353 + 0.7e1 / 0.1536e4 * t824 * t349 * t829 * t239 * t830 * t265 + 0.119e3 / 0.2304e4 * t364 * t378 - 0.119e3 / 0.2304e4 * t274 * t363 * t384 + t824 * t842 * t224 * t227 * t829 * t239 * t830 * t846 / 0.128e3 - 0.3e1 / 0.256e3 * t824 * t228 * t829 * t239 * t830 * t266 - t478 * t295 * t17 * t471 * t369 / 0.768e3 - t536 * t285 * t239 * t863 * t219 / 0.1024e4 + 0.7e1 / 0.384e3 * t274 * t359 * t561 * t481 + 0.455e3 / 0.243e3 * s0 / t18 / t360 * t7 * t189 - 0.595e3 / 0.2592e4 * t357 * t359 * t496 * t371
  t884 = t265 * t471
  t890 = t17 * t263
  t906 = t266 * t343
  t930 = t710 + t714 + t721 - t725 - t733 - t773 + t778 - t782 + t786 + t789 - t792
  t933 = 0.67471172535210825687488420139294265171645179205307e-1 * t130 * t108 * t142
  t936 = 0.86748650402413918741056540179092626649258087549680e-1 * t130 * t140 * t134
  t939 = 0.13012297560362087811158481026863893997388713132452e0 * t130 * t51 * t417
  t942 = 0.21687162600603479685264135044773156662314521887420e-1 * t130 * t51 * t127
  t946 = 0.42740000000000000000000000000000000000000000000000e0 * t52 * t306 * t250 * t319
  t951 = 0.34367190188705947437658206473318387813719215070744e1 * t52 * t323 * t318 * t326 * t250
  t954 = 0.43374325201206959370528270089546313324629043774840e-1 * t130 * t140 * t165
  t957 = 0.12842595503380418955085974953824062831138054875329e1 * t130 * t140 * t171
  t960 = 0.38025319932552508024225805073234468230220037056326e2 * t130 * t51 * t73
  t963 = 0.38527786510141256865257924861472188493414164625988e1 * t130 * t51 * t80
  t964 = -t795 - t799 + t933 + t936 + t939 + t942 + t946 - t951 - t954 - t957 + t960 - t963
  t967 = t126 * t63
  t970 = 0.46785788981077169658097909310072427855779642723424e1 * t24 * t132 * t124 * t967
  t974 = 0.69263436422725855038665932335230900662317599327620e2 * t24 * t169 * t124 * t412
  t978 = 0.22161481481481481481481481481481481481481481481481e0 * t300 * t104 * t244 * t252
  t983 = 0.61524113149298439949309167758941162080356015012483e4 * t24 * t42 * t64 * t72 * t163
  t985 = t79 * t163
  t988 = 0.62337092780453269534799339101707810596085839394858e3 * t24 * t77 * t64 * t985
  t991 = 0.42740000000000000000000000000000000000000000000000e0 * t300 * t432 * t394
  t995 = 0.18989649058080861538367470034170805442117582945368e-2 * t255 * t45 * t524 * t210
  t999 = 0.28493333333333333333333333333333333333333333333333e0 * t300 * t139 * t306 * t309
  t1003 = 0.68734380377411894875316412946636775627438430141488e1 * t300 * t47 * t437 * t439
  t1007 = 0.22911460125803964958438804315545591875812810047162e1 * t300 * t139 * t323 * t327
  t1010 = 0.71233333333333333333333333333333333333333333333332e-1 * t300 * t301 * t451
  t1011 = t970 - t974 - t978 - t983 + t988 - t991 + t995 - t999 + t1003 + t1007 - t1010
  t1015 = 0.36846163202829085479643115651216588683774907041596e2 * t300 * t47 * t455 * t459
  t1018 = 0.14246666666666666666666666666666666666666666666666e0 * t300 * t425 * t319
  t1021 = 0.21053605041484726346144059189532592535100839225540e2 * t24 * t170 * t421
  t1035 = 0.10000000000000000000000000000000000000000000000000e1 * t245 * (-0.21099166666666666666666666666666666666666666666667e1 * t741 + 0.20255200000000000000000000000000000000000000000000e2 * t744 - 0.75019259259259259259259259259259259259259259259258e1 * t747 + 0.65641851851851851851851851851851851851851851851850e1 * t750 + 0.31003950617283950617283950617283950617283950617285e1 * t753 + 0.68258333333333333333333333333333333333333333333335e-1 * t758 - 0.10921333333333333333333333333333333333333333333333e1 * t760 + 0.12134814814814814814814814814814814814814814814815e1 * t762 + 0.10617962962962962962962962962962962962962962962963e1 * t764 + 0.13388493827160493827160493827160493827160493827161e1 * t767) * t251
  t1036 = t308 ** 2
  t1039 = 0.57895126195293126240322668836661767023579398340984e3 * t456 * t1036 * t326
  t1040 = t318 ** 2
  t1043 = 0.60000000000000000000000000000000000000000000000000e1 * t307 * t1040 * t251
  t1044 = t322 ** 2
  t1047 = t325 ** 2
  t1051 = 0.24955700379505800914252936827276051226357058527653e5 * t198 / t1044 * t1036 / t1047
  t1057 = 0.62071215503128080358781102641263322069063951965254e4 * t198 / t322 / t305 * t1036 * t458
  t1058 = t11 * t300
  t1063 = 0.19263893255070628432628962430736094246707082312995e1 * t1058 * t47 * t169 * t985 * t63
  t1068 = 0.13012297560362087811158481026863893997388713132452e0 * t1058 * t47 * t132 * t967 * t163
  t1071 = 0.24000000000000000000000000000000000000000000000000e2 * t438 * t1036 * t251
  t1074 = 0.48245938496077605200268890697218139186316165284153e2 * t324 * t1040 * t326
  t1075 = -t1015 + t1018 - t1021 + t1035 + t1039 - t1043 + t1051 - t1057 + t1063 - t1068 - t1071 + t1074
  t1077 = t930 + t964 + t1011 + t1075
  t1083 = t89 ** 2
  t1091 = t293 * t295 * t296 * t884 / 0.384e3 - 0.3e1 / 0.256e3 * t196 * t292 * t814 * t890 * t344 - 0.7e1 / 0.192e3 * t274 * t277 * t561 * t346 + t529 * t285 * t239 * t863 * t265 / 0.512e3 + 0.3e1 / 0.256e3 * t196 * t225 * t291 * t814 * t890 * t906 + 0.119e3 / 0.1152e4 * t274 * t277 * t362 * t288 - 0.7e1 / 0.192e3 * t196 * t225 * t279 * t269 - t824 * t387 * t829 * t239 * t830 * t219 / 0.3072e4 - 0.7e1 / 0.1152e4 * t375 * t474 - 0.7e1 / 0.1152e4 * t196 * t374 * t487 + t388 * t368 * t239 * t1077 * t219 / 0.3072e4 + 0.13685e5 / 0.31104e5 * t493 / t33 / t1083 * t230 * t498 * t501
  t1092 = t883 + t1091
  t1111 = t577 ** 2
  t1119 = t603 ** 2
  t1126 = t566 * t264
  t1130 = params.beta * t823
  t1132 = t516 * t830
  t1134 = 0.1e1 / t233 / t231
  t1144 = t544 * t263
  t1171 = -0.24e2 * t639 * t1126 * t640 + 0.24e2 * t1130 * t842 * t1132 * t1134 * t846 - 0.36e2 * t1130 * t223 * t1132 * t1134 * t266 + 0.12e2 * t582 * t1144 * t586 + 0.24e2 * t621 * t1126 * t625 - 0.4e1 * t659 * t471 * t585 * t369 + t507 * t490 * t1092 + 0.4e1 * t664 * t1126 * t665 + 0.4e1 * t550 * t566 * t471 * t552 - 0.6e1 * t597 * t1144 * t598 + 0.6e1 * t550 * t544 * t343 * t552
  t1187 = t516 * t863
  t1198 = t263 * t624
  t1221 = -0.12e2 * t581 * t358 * t566 * t661 + t550 * t516 * t1077 * t552 + 0.24e2 * t581 * t276 * t566 * t636 - t1130 * t358 * t1132 * t1134 * t219 - 0.3e1 * t597 * t1187 * t598 + 0.6e1 * t620 * t658 * t343 * t624 * t382 + 0.36e2 * t620 * t223 * t516 * t1198 * t906 - 0.36e2 * t620 * t633 * t1198 * t344 + 0.6e1 * t582 * t1187 * t586 + 0.8e1 * t634 * t635 * t884 + 0.14e2 * t1130 * t276 * t1132 * t1134 * t265 + 0.4e1 * t550 * t505 * t262 * t552
  t1225 = params.beta * t1092 * t521 - 0.4e1 * t506 * t570 + 0.12e2 * t545 * t578 - 0.6e1 * t545 * t604 - 0.24e2 * t573 * t612 + 0.24e2 * t573 * t215 * t617 - 0.4e1 * t573 * t671 + 0.24e2 * t607 * t215 / t608 / t519 * t1111 - 0.36e2 * t615 * t609 * t577 * t603 + 0.6e1 * t607 * t576 * t1119 + 0.8e1 * t615 * t616 * t670 - t607 * t548 * (t1171 + t1221)
  t1228 = t698 ** 2
  t1229 = t700 ** 2
  t1234 = -t799 - 0.3e1 * t179 * t807 * t808 + t179 * t1225 * t676 - 0.6e1 * t179 * t1228 / t1229 + t933 + t936 + t939 + t942 + t946 - t951 - t954 - t957 + t960
  t1240 = -0.4e1 * t179 * t673 * t808 * t697 + t1003 + t1007 - t1010 - t963 + t970 - t974 - t978 - t983 + t988 - t991 + t995 - t999
  t1245 = 0.12e2 * t179 * t806 * t702 * t698 - t1015 + t1018 - t1021 + t1035 + t1039 - t1043 + t1051 - t1057 + t1063 - t1068 - t1071 + t1074
  t1253 = 0.42740000000000000000000000000000000000000000000000e0 * t464 - 0.22787578869697033846040964041004966530541099534442e-2 * t468 - 0.24000000000000000000000000000000000000000000000000e2 * t398 + 0.13780319445925925925925925925925925925925925925925e-1 * t404 + 0.19298375398431042080107556278887255674526466113661e3 * t391 - 0.14035736694323150897429372793021728356733892817027e2 * t418 - 0.38596750796862084160215112557774511349052932227323e3 * t440 + 0.40000000000000000000000000000000000000000000000000e1 * t452 + 0.20690405167709360119593700880421107356354650655085e4 * t460 + 0.8e1 * t179 * t698 * t697 * t702 + 0.24000000000000000000000000000000000000000000000000e2 * t395 + r0 * (t796 + t1234 + t1240 + t1245) - 0.12e2 * t179 * t806 * t808 * t697
  v4rho4_0_ = t685 + t1253

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t10 = 0.1e1 / t8 / t7
  t11 = t6 * t10
  t14 = t4 * t6 / t8
  t15 = jnp.sqrt(t14)
  t18 = t14 ** 0.15e1
  t20 = t1 ** 2
  t21 = t3 ** 2
  t22 = t20 * t21
  t23 = t8 ** 2
  t26 = t22 * t5 / t23
  t28 = 0.37978500000000000000000000000000000000000000000000e1 * t15 + 0.89690000000000000000000000000000000000000000000000e0 * t14 + 0.20477500000000000000000000000000000000000000000000e0 * t18 + 0.12323500000000000000000000000000000000000000000000e0 * t26
  t31 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t28
  t32 = jnp.log(t31)
  t34 = t4 * t11 * t32
  t35 = 0.22146941966666666666666666666666666666666666666666e-2 * t34
  t37 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t14
  t38 = t28 ** 2
  t39 = 0.1e1 / t38
  t40 = t37 * t39
  t42 = 0.1e1 / t15 * t1
  t43 = t3 * t6
  t44 = t43 * t10
  t45 = t42 * t44
  t47 = t4 * t11
  t49 = t14 ** 0.5e0
  t50 = t49 * t1
  t51 = t50 * t44
  t56 = t22 * t5 / t23 / t7
  t58 = -0.63297500000000000000000000000000000000000000000000e0 * t45 - 0.29896666666666666666666666666666666666666666666667e0 * t47 - 0.10238750000000000000000000000000000000000000000000e0 * t51 - 0.82156666666666666666666666666666666666666666666667e-1 * t56
  t59 = 0.1e1 / t31
  t60 = t58 * t59
  t61 = t40 * t60
  t62 = 0.20000000000000000000000000000000000000000000000000e1 * t61
  t63 = r0 - r1
  t64 = t63 ** 2
  t65 = t64 * t63
  t66 = t7 ** 2
  t67 = t66 ** 2
  t68 = 0.1e1 / t67
  t69 = t65 * t68
  t70 = 0.1e1 / t7
  t71 = t63 * t70
  t72 = 0.1e1 + t71
  t73 = t72 <= f.p.zeta_threshold
  t74 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t75 = t74 * f.p.zeta_threshold
  t76 = t72 ** (0.1e1 / 0.3e1)
  t77 = t76 * t72
  t78 = f.my_piecewise3(t73, t75, t77)
  t79 = 0.1e1 - t71
  t80 = t79 <= f.p.zeta_threshold
  t81 = t79 ** (0.1e1 / 0.3e1)
  t82 = t81 * t79
  t83 = f.my_piecewise3(t80, t75, t82)
  t85 = 2 ** (0.1e1 / 0.3e1)
  t88 = 0.1e1 / (0.2e1 * t85 - 0.2e1)
  t89 = (t78 + t83 - 0.2e1) * t88
  t91 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t14
  t96 = 0.70594500000000000000000000000000000000000000000000e1 * t15 + 0.15494250000000000000000000000000000000000000000000e1 * t14 + 0.42077500000000000000000000000000000000000000000000e0 * t18 + 0.15629250000000000000000000000000000000000000000000e0 * t26
  t99 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t96
  t100 = jnp.log(t99)
  t104 = 0.621814e-1 * t37 * t32
  t106 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t14
  t111 = 0.51785000000000000000000000000000000000000000000000e1 * t15 + 0.90577500000000000000000000000000000000000000000000e0 * t14 + 0.11003250000000000000000000000000000000000000000000e0 * t18 + 0.12417750000000000000000000000000000000000000000000e0 * t26
  t114 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t111
  t115 = jnp.log(t114)
  t116 = t106 * t115
  t118 = -0.3109070e-1 * t91 * t100 + t104 - 0.19751673498613801407483339618206552048944131217655e-1 * t116
  t119 = t89 * t118
  t120 = t69 * t119
  t121 = 0.8e1 * t120
  t122 = t64 ** 2
  t123 = t67 * t7
  t124 = 0.1e1 / t123
  t125 = t122 * t124
  t126 = t125 * t119
  t127 = 0.8e1 * t126
  t128 = t122 * t68
  t129 = 0.1e1 / t66
  t130 = t63 * t129
  t131 = t70 - t130
  t134 = f.my_piecewise3(t73, 0, 0.4e1 / 0.3e1 * t76 * t131)
  t135 = -t131
  t138 = f.my_piecewise3(t80, 0, 0.4e1 / 0.3e1 * t81 * t135)
  t140 = (t134 + t138) * t88
  t141 = t140 * t118
  t142 = t128 * t141
  t147 = t96 ** 2
  t148 = 0.1e1 / t147
  t149 = t91 * t148
  t154 = -0.11765750000000000000000000000000000000000000000000e1 * t45 - 0.51647500000000000000000000000000000000000000000000e0 * t47 - 0.21038750000000000000000000000000000000000000000000e0 * t51 - 0.10419500000000000000000000000000000000000000000000e0 * t56
  t155 = 0.1e1 / t99
  t156 = t154 * t155
  t159 = 0.11073470983333333333333333333333333333333333333333e-2 * t34
  t160 = 0.10000000000000000000000000000000000000000000000000e1 * t61
  t164 = t111 ** 2
  t165 = 0.1e1 / t164
  t166 = t106 * t165
  t171 = -0.86308333333333333333333333333333333333333333333334e0 * t45 - 0.30192500000000000000000000000000000000000000000000e0 * t47 - 0.55016250000000000000000000000000000000000000000000e-1 * t51 - 0.82785000000000000000000000000000000000000000000000e-1 * t56
  t172 = 0.1e1 / t114
  t173 = t171 * t172
  t176 = 0.53237641966666666666666666666666666666666666666666e-3 * t4 * t11 * t100 + 0.10000000000000000000000000000000000000000000000000e1 * t149 * t156 - t159 - t160 + 0.18311447306006545054854346104378990962041954983034e-3 * t4 * t11 * t115 + 0.58482236226346462072622386637590534819724553404280e0 * t166 * t173
  t177 = t89 * t176
  t178 = t128 * t177
  t179 = 0.2e1 * t178
  t180 = t140 * t116
  t182 = t89 * t1
  t184 = t43 * t10 * t115
  t185 = t182 * t184
  t186 = 0.36622894612013090109708692208757981924083909966068e-3 * t185
  t187 = t89 * t106
  t189 = t165 * t171 * t172
  t190 = t187 * t189
  t191 = 0.11696447245269292414524477327518106963944910680856e1 * t190
  t192 = t74 ** 2
  t193 = t76 ** 2
  t194 = f.my_piecewise3(t73, t192, t193)
  t195 = t81 ** 2
  t196 = f.my_piecewise3(t80, t192, t195)
  t198 = t194 / 0.2e1 + t196 / 0.2e1
  t199 = t198 ** 2
  t200 = params.gamma * t199
  t202 = s0 + 0.2e1 * s1 + s2
  t204 = 0.1e1 / t8 / t66
  t205 = t202 * t204
  t209 = 0.1e1 / t3
  t211 = 0.1e1 / t199 * t20 * t209 * t5
  t214 = params.BB * params.beta
  t215 = 0.1e1 / params.gamma
  t220 = (-t104 + t128 * t119 + 0.19751673498613801407483339618206552048944131217655e-1 * t89 * t116) * t215
  t221 = t199 * t198
  t222 = 0.1e1 / t221
  t224 = jnp.exp(-t220 * t222)
  t225 = t224 - 0.1e1
  t226 = 0.1e1 / t225
  t228 = t202 ** 2
  t230 = t214 * t215 * t226 * t228
  t232 = 0.1e1 / t23 / t67
  t233 = t85 ** 2
  t234 = t232 * t233
  t235 = t199 ** 2
  t236 = 0.1e1 / t235
  t238 = 0.1e1 / t21
  t240 = t1 * t238 * t6
  t244 = t205 * t85 * t211 / 0.96e2 + t230 * t234 * t236 * t240 / 0.3072e4
  t245 = params.beta * t244
  t246 = params.beta * t215
  t249 = t246 * t226 * t244 + 0.1e1
  t251 = t215 / t249
  t253 = t245 * t251 + 0.1e1
  t254 = jnp.log(t253)
  t255 = 0.1e1 / t76
  t258 = f.my_piecewise3(t73, 0, 0.2e1 / 0.3e1 * t255 * t131)
  t259 = 0.1e1 / t81
  t262 = f.my_piecewise3(t80, 0, 0.2e1 / 0.3e1 * t259 * t135)
  t264 = t258 / 0.2e1 + t262 / 0.2e1
  t266 = t200 * t254 * t264
  t268 = params.gamma * t221
  t269 = t66 * t7
  t272 = t202 / t8 / t269
  t275 = 0.7e1 / 0.288e3 * t272 * t85 * t211
  t276 = t85 * t222
  t277 = t205 * t276
  t278 = t20 * t209
  t280 = t278 * t5 * t264
  t283 = t214 * t215
  t284 = t225 ** 2
  t285 = 0.1e1 / t284
  t286 = t285 * t228
  t288 = t283 * t286 * t232
  t290 = t233 * t236 * t1
  t291 = t238 * t6
  t292 = 0.4e1 * t120
  t293 = 0.4e1 * t126
  t294 = 0.19751673498613801407483339618206552048944131217655e-1 * t180
  t295 = 0.18311447306006545054854346104378990962041954983034e-3 * t185
  t296 = 0.58482236226346462072622386637590534819724553404280e0 * t190
  t298 = (t159 + t160 + t292 - t293 + t142 + t178 + t294 - t295 - t296) * t215
  t300 = t236 * t264
  t303 = 0.3e1 * t220 * t300 - t298 * t222
  t304 = t303 * t224
  t306 = t290 * t291 * t304
  t310 = 0.1e1 / t23 / t123
  t315 = 0.7e1 / 0.4608e4 * t230 * t310 * t233 * t236 * t240
  t316 = t226 * t228
  t318 = t283 * t316 * t232
  t320 = 0.1e1 / t235 / t198
  t322 = t233 * t320 * t1
  t324 = t322 * t291 * t264
  t327 = -t275 - t277 * t280 / 0.48e2 - t288 * t306 / 0.3072e4 - t315 - t318 * t324 / 0.768e3
  t328 = params.beta * t327
  t330 = t249 ** 2
  t332 = t215 / t330
  t333 = t246 * t285
  t339 = -t333 * t244 * t303 * t224 + t246 * t226 * t327
  t340 = t332 * t339
  t342 = -t245 * t340 + t328 * t251
  t343 = 0.1e1 / t253
  t344 = t342 * t343
  t345 = t268 * t344
  t347 = t342 ** 2
  t348 = t253 ** 2
  t349 = 0.1e1 / t348
  t352 = params.gamma * t198
  t353 = t264 ** 2
  t357 = 0.1e1 / t77
  t358 = t131 ** 2
  t361 = 0.1e1 / t269
  t362 = t63 * t361
  t364 = -0.2e1 * t129 + 0.2e1 * t362
  t368 = f.my_piecewise3(t73, 0, -0.2e1 / 0.9e1 * t357 * t358 + 0.2e1 / 0.3e1 * t255 * t364)
  t369 = 0.1e1 / t82
  t370 = t135 ** 2
  t373 = -t364
  t377 = f.my_piecewise3(t80, 0, -0.2e1 / 0.9e1 * t369 * t370 + 0.2e1 / 0.3e1 * t259 * t373)
  t379 = t368 / 0.2e1 + t377 / 0.2e1
  t386 = 0.10843581300301739842632067522386578331157260943710e-1 * t89 * t4 * t11 * t189
  t389 = 0.12e2 * t64 * t68 * t119
  t392 = 0.32e2 * t65 * t124 * t119
  t394 = 0.8e1 * t125 * t177
  t395 = t69 * t141
  t396 = 0.8e1 * t395
  t401 = 0.8e1 * t69 * t177
  t403 = t128 * t140 * t176
  t404 = 0.2e1 * t403
  t405 = t125 * t141
  t406 = 0.8e1 * t405
  t407 = 0.1e1 / t193
  t413 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t407 * t358 + 0.4e1 / 0.3e1 * t76 * t364)
  t414 = 0.1e1 / t195
  t420 = f.my_piecewise3(t80, 0, 0.4e1 / 0.9e1 * t414 * t370 + 0.4e1 / 0.3e1 * t81 * t373)
  t422 = (t413 + t420) * t88
  t424 = t128 * t422 * t118
  t425 = t6 * t204
  t428 = 0.14764627977777777777777777777777777777777777777777e-2 * t4 * t425 * t32
  t429 = 0.3e1 * t200 * t254 * t379 + 0.6e1 * t200 * t344 * t264 + 0.6e1 * t352 * t254 * t353 - t268 * t347 * t349 + t386 + t389 - t392 - t394 + t396 + t401 + t404 - t406 + t424 - t428
  t430 = t67 * t66
  t434 = 0.20e2 * t122 / t430 * t119
  t438 = t4 * t6
  t446 = t154 ** 2
  t455 = 0.1e1 / t23 / t66
  t456 = t21 * t5 * t455
  t457 = 0.1e1 / t15 / t14 * t20 * t456
  t459 = t43 * t204
  t460 = t42 * t459
  t462 = t4 * t425
  t464 = t14 ** (-0.5e0)
  t466 = t464 * t20 * t456
  t468 = t50 * t459
  t471 = t22 * t5 * t455
  t477 = t147 ** 2
  t480 = t99 ** 2
  t488 = 0.35616666666666666666666666666666666666666666666666e-1 * t438 * t10 * t39 * t60
  t492 = t58 ** 2
  t495 = 0.20000000000000000000000000000000000000000000000000e1 * t37 / t38 / t28 * t492 * t59
  t505 = 0.10000000000000000000000000000000000000000000000000e1 * t40 * (-0.42198333333333333333333333333333333333333333333333e0 * t457 + 0.84396666666666666666666666666666666666666666666666e0 * t460 + 0.39862222222222222222222222222222222222222222222223e0 * t462 + 0.68258333333333333333333333333333333333333333333333e-1 * t466 + 0.13651666666666666666666666666666666666666666666667e0 * t468 + 0.13692777777777777777777777777777777777777777777778e0 * t471) * t59
  t506 = t38 ** 2
  t509 = t31 ** 2
  t513 = 0.16081979498692535066756296899072713062105388428051e2 * t37 / t506 * t492 / t509
  t522 = 0.1e1 / t164 / t111
  t524 = t171 ** 2
  t534 = -0.57538888888888888888888888888888888888888888888889e0 * t457 + 0.11507777777777777777777777777777777777777777777778e1 * t460 + 0.40256666666666666666666666666666666666666666666667e0 * t462 + 0.36677500000000000000000000000000000000000000000000e-1 * t466 + 0.73355000000000000000000000000000000000000000000000e-1 * t468 + 0.13797500000000000000000000000000000000000000000000e0 * t471
  t538 = t164 ** 2
  t539 = 0.1e1 / t538
  t541 = t114 ** 2
  t542 = 0.1e1 / t541
  t546 = -0.70983522622222222222222222222222222222222222222221e-3 * t4 * t425 * t100 - 0.34246666666666666666666666666666666666666666666666e-1 * t438 * t10 * t148 * t156 - 0.20000000000000000000000000000000000000000000000000e1 * t91 / t147 / t96 * t446 * t155 + 0.10000000000000000000000000000000000000000000000000e1 * t149 * (-0.78438333333333333333333333333333333333333333333333e0 * t457 + 0.15687666666666666666666666666666666666666666666667e1 * t460 + 0.68863333333333333333333333333333333333333333333333e0 * t462 + 0.14025833333333333333333333333333333333333333333333e0 * t466 + 0.28051666666666666666666666666666666666666666666667e0 * t468 + 0.17365833333333333333333333333333333333333333333333e0 * t471) * t155 + 0.32163958997385070133512593798145426124210776856102e2 * t91 / t477 * t446 / t480 + t428 + t488 + t495 - t505 - t513 - 0.24415263074675393406472461472505321282722606644045e-3 * t4 * t425 * t115 - 0.10843581300301739842632067522386578331157260943710e-1 * t438 * t10 * t165 * t173 - 0.11696447245269292414524477327518106963944910680856e1 * t106 * t522 * t524 * t172 + 0.58482236226346462072622386637590534819724553404280e0 * t166 * t534 * t172 + 0.17315859105681463759666483083807725165579399831905e2 * t106 * t539 * t524 * t542
  t548 = t128 * t89 * t546
  t550 = t140 * t1 * t184
  t551 = 0.36622894612013090109708692208757981924083909966068e-3 * t550
  t557 = 0.35e2 / 0.432e3 * t202 / t8 / t67 * t85 * t211
  t558 = t272 * t276
  t559 = t558 * t280
  t562 = t205 * t85 * t236
  t572 = 0.1e1 / t284 / t225
  t573 = t572 * t228
  t575 = t283 * t573 * t232
  t576 = t303 ** 2
  t577 = t224 ** 2
  t584 = t283 * t286 * t310
  t585 = t584 * t306
  t588 = t283 * t286 * t234
  t590 = t320 * t1 * t238
  t592 = t224 * t264
  t598 = 0.19751673498613801407483339618206552048944131217655e-1 * t422 * t116
  t602 = 0.17315859105681463759666483083807725165579399831905e2 * t187 * t539 * t524 * t542
  t606 = 0.58482236226346462072622386637590534819724553404280e0 * t187 * t165 * t534 * t172
  t608 = t140 * t106 * t189
  t609 = 0.11696447245269292414524477327518106963944910680856e1 * t608
  t610 = t598 - t602 - t606 - t609 + t434 + t548 + t424 + t404 - t406 - t394 + t396
  t614 = 0.11696447245269292414524477327518106963944910680856e1 * t187 * t522 * t524 * t172
  t618 = 0.24415263074675393406472461472505321282722606644045e-3 * t182 * t43 * t204 * t115
  t619 = t401 - t495 + t513 + t505 - t551 + t614 - t488 + t386 - t428 + t389 - t392 + t618
  t631 = -(t610 + t619) * t215 * t222 + 0.6e1 * t298 * t300 - 0.12e2 * t220 * t320 * t353 + 0.3e1 * t220 * t236 * t379
  t648 = 0.119e3 / 0.13824e5 * t230 / t23 / t430 * t233 * t236 * t240
  t650 = t283 * t316 * t310
  t651 = t650 * t324
  t656 = t233 / t235 / t199 * t1
  t665 = t557 + 0.7e1 / 0.72e2 * t559 + t562 * t278 * t5 * t353 / 0.16e2 - t277 * t278 * t5 * t379 / 0.48e2 + t575 * t290 * t291 * t576 * t577 / 0.1536e4 + 0.7e1 / 0.2304e4 * t585 + t588 * t590 * t6 * t303 * t592 / 0.384e3 - t288 * t290 * t291 * t631 * t224 / 0.3072e4 - t288 * t290 * t291 * t576 * t224 / 0.3072e4 + t648 + 0.7e1 / 0.576e3 * t651 + 0.5e1 / 0.768e3 * t318 * t656 * t291 * t353 - t318 * t322 * t291 * t379 / 0.768e3
  t671 = 0.1e1 / t330 / t249
  t672 = t215 * t671
  t673 = t339 ** 2
  t677 = t246 * t572
  t678 = t244 * t576
  t699 = t434 + t548 - t488 - t551 + t268 * (params.beta * t665 * t251 - 0.2e1 * t328 * t340 + 0.2e1 * t245 * t672 * t673 - t245 * t332 * (-t333 * t244 * t631 * t224 - 0.2e1 * t333 * t327 * t303 * t224 - t333 * t678 * t224 + t246 * t226 * t665 + 0.2e1 * t677 * t678 * t577)) * t343 + t505 + t513 - t495 + t598 - t602 - t606 - t609 + t614 + t618
  d11 = t35 + t62 + t121 - t127 + 0.2e1 * t142 + t179 + 0.39503346997227602814966679236413104097888262435310e-1 * t180 - t186 - t191 + 0.6e1 * t266 + 0.2e1 * t345 + t7 * (t429 + t699)
  t703 = -t70 - t130
  t706 = f.my_piecewise3(t73, 0, 0.4e1 / 0.3e1 * t76 * t703)
  t707 = -t703
  t710 = f.my_piecewise3(t80, 0, 0.4e1 / 0.3e1 * t81 * t707)
  t712 = (t706 + t710) * t88
  t713 = t712 * t118
  t714 = t128 * t713
  t715 = t712 * t116
  t716 = 0.19751673498613801407483339618206552048944131217655e-1 * t715
  t719 = f.my_piecewise3(t73, 0, 0.2e1 / 0.3e1 * t255 * t703)
  t722 = f.my_piecewise3(t80, 0, 0.2e1 / 0.3e1 * t259 * t707)
  t724 = t719 / 0.2e1 + t722 / 0.2e1
  t725 = t254 * t724
  t726 = t200 * t725
  t728 = t5 * t724
  t729 = t278 * t728
  t733 = (t159 + t160 - t292 - t293 + t714 + t178 + t716 - t295 - t296) * t215
  t735 = t236 * t724
  t738 = 0.3e1 * t220 * t735 - t733 * t222
  t741 = t290 * t291 * t738 * t224
  t745 = t322 * t291 * t724
  t748 = -t275 - t277 * t729 / 0.48e2 - t288 * t741 / 0.3072e4 - t315 - t318 * t745 / 0.768e3
  t749 = params.beta * t748
  t751 = t244 * t738
  t756 = -t333 * t751 * t224 + t246 * t226 * t748
  t757 = t332 * t756
  t759 = -t245 * t757 + t749 * t251
  t760 = t759 * t343
  t761 = t268 * t760
  t762 = t69 * t713
  t763 = 0.4e1 * t762
  t764 = t125 * t713
  t765 = 0.4e1 * t764
  t773 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t407 * t703 * t131 + 0.8e1 / 0.3e1 * t76 * t63 * t361)
  t781 = f.my_piecewise3(t80, 0, 0.4e1 / 0.9e1 * t414 * t707 * t135 - 0.8e1 / 0.3e1 * t81 * t63 * t361)
  t783 = (t773 + t781) * t88
  t785 = t128 * t783 * t118
  t787 = t128 * t712 * t176
  t795 = 0.19751673498613801407483339618206552048944131217655e-1 * t783 * t116
  t796 = 0.4e1 * t395
  t797 = 0.4e1 * t405
  t798 = 0.3e1 * t200 * t760 * t264 + 0.6e1 * t352 * t725 * t264 + t386 - t389 - t394 + t403 - t428 + t434 + t548 + t763 - t765 + t785 + t787 + t795 - t796 - t797
  t803 = t712 * t106 * t189
  t804 = 0.58482236226346462072622386637590534819724553404280e0 * t803
  t812 = f.my_piecewise3(t73, 0, -0.2e1 / 0.9e1 * t357 * t703 * t131 + 0.4e1 / 0.3e1 * t255 * t63 * t361)
  t820 = f.my_piecewise3(t80, 0, -0.2e1 / 0.9e1 * t369 * t707 * t135 - 0.4e1 / 0.3e1 * t259 * t63 * t361)
  t822 = t812 / 0.2e1 + t820 / 0.2e1
  t826 = 0.18311447306006545054854346104378990962041954983034e-3 * t550
  t828 = t558 * t729
  t841 = t236 * t1 * t238
  t842 = t6 * t738
  t843 = t577 * t303
  t848 = t584 * t741
  t854 = t763 - t765 + t785 + t787 + t795 + t386 - t389 - t394 - t796 + t403 - t797 - t428 + t434
  t856 = t712 * t1 * t184
  t857 = 0.18311447306006545054854346104378990962041954983034e-3 * t856
  t858 = 0.58482236226346462072622386637590534819724553404280e0 * t608
  t859 = t548 - t804 - t488 - t826 + t505 + t513 - t495 - t857 - t602 - t606 - t858 + t614 + t618
  t874 = -(t854 + t859) * t215 * t222 + 0.3e1 * t733 * t300 + 0.3e1 * t298 * t735 - 0.12e2 * t220 * t320 * t724 * t264 + 0.3e1 * t220 * t236 * t822
  t891 = t650 * t745
  t902 = t557 + 0.7e1 / 0.144e3 * t559 + 0.7e1 / 0.144e3 * t828 + t562 * t278 * t728 * t264 / 0.16e2 - t277 * t278 * t5 * t822 / 0.48e2 + t283 * t573 * t234 * t841 * t842 * t843 / 0.1536e4 + 0.7e1 / 0.4608e4 * t848 + t588 * t590 * t842 * t592 / 0.768e3 - t288 * t290 * t291 * t874 * t224 / 0.3072e4 - t588 * t841 * t842 * t304 / 0.3072e4 + 0.7e1 / 0.4608e4 * t585 + t648 + 0.7e1 / 0.1152e4 * t651 + t588 * t590 * t6 * t724 * t304 / 0.768e3 + 0.7e1 / 0.1152e4 * t891 + 0.5e1 / 0.768e3 * t318 * t656 * t291 * t724 * t264 - t318 * t322 * t291 * t822 / 0.768e3
  t937 = 0.3e1 * t200 * t344 * t724 - t804 + 0.3e1 * t200 * t254 * t822 - t488 - t826 + t505 + t513 - t495 + t268 * (params.beta * t902 * t251 - t749 * t340 - t328 * t757 + 0.2e1 * t245 * t215 * t671 * t756 * t339 - t245 * t332 * (-t333 * t244 * t874 * t224 - t333 * t748 * t303 * t224 - t333 * t327 * t738 * t224 + t246 * t226 * t902 - t333 * t751 * t304 + 0.2e1 * t677 * t751 * t843)) * t343 - t857 - t602 - t606 - t858 + t614 + t618 - t268 * t759 * t349 * t342
  d12 = t35 + t62 - t127 + t142 + t179 + t294 - t186 - t191 + 0.3e1 * t266 + t345 + t714 + t716 + 0.3e1 * t726 + t761 + t7 * (t798 + t937)
  t944 = 0.8e1 * t762
  t945 = 0.8e1 * t764
  t946 = 0.2e1 * t787
  t947 = t703 ** 2
  t951 = 0.2e1 * t129 + 0.2e1 * t362
  t955 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t407 * t947 + 0.4e1 / 0.3e1 * t76 * t951)
  t956 = t707 ** 2
  t959 = -t951
  t963 = f.my_piecewise3(t80, 0, 0.4e1 / 0.9e1 * t414 * t956 + 0.4e1 / 0.3e1 * t81 * t959)
  t965 = (t955 + t963) * t88
  t967 = t128 * t965 * t118
  t968 = 0.11696447245269292414524477327518106963944910680856e1 * t803
  t969 = t724 ** 2
  t973 = 0.6e1 * t352 * t254 * t969 + t386 + t389 + t392 - t394 - t401 - t428 + t434 + t548 - t944 - t945 + t946 + t967 - t968
  t975 = 0.19751673498613801407483339618206552048944131217655e-1 * t965 * t116
  t976 = t759 ** 2
  t984 = f.my_piecewise3(t73, 0, -0.2e1 / 0.9e1 * t357 * t947 + 0.2e1 / 0.3e1 * t255 * t951)
  t990 = f.my_piecewise3(t80, 0, -0.2e1 / 0.9e1 * t369 * t956 + 0.2e1 / 0.3e1 * t259 * t959)
  t992 = t984 / 0.2e1 + t990 / 0.2e1
  t1005 = t738 ** 2
  t1017 = 0.36622894612013090109708692208757981924083909966068e-3 * t856
  t1018 = -t602 - t606 - t968 + t513 + t505 + t548 - t1017 + t614 - t488 + t386 - t495
  t1019 = t967 + t946 + t392 - t428 + t389 - t945 - t394 - t944 - t401 + t975 + t434 + t618
  t1031 = -(t1018 + t1019) * t215 * t222 + 0.6e1 * t733 * t735 - 0.12e2 * t220 * t320 * t969 + 0.3e1 * t220 * t236 * t992
  t1051 = t557 + 0.7e1 / 0.72e2 * t828 + t562 * t278 * t5 * t969 / 0.16e2 - t277 * t278 * t5 * t992 / 0.48e2 + t575 * t290 * t291 * t1005 * t577 / 0.1536e4 + 0.7e1 / 0.2304e4 * t848 + t588 * t590 * t842 * t224 * t724 / 0.384e3 - t288 * t290 * t291 * t1031 * t224 / 0.3072e4 - t288 * t290 * t291 * t1005 * t224 / 0.3072e4 + t648 + 0.7e1 / 0.576e3 * t891 + 0.5e1 / 0.768e3 * t318 * t656 * t291 * t969 - t318 * t322 * t291 * t992 / 0.768e3
  t1056 = t756 ** 2
  t1060 = t244 * t1005
  t1084 = t975 - t488 + t505 + t513 - t268 * t976 * t349 + 0.3e1 * t200 * t254 * t992 + t268 * (params.beta * t1051 * t251 - 0.2e1 * t749 * t757 + 0.2e1 * t245 * t672 * t1056 - t245 * t332 * (-t333 * t244 * t1031 * t224 - 0.2e1 * t333 * t748 * t738 * t224 + t246 * t226 * t1051 - t333 * t1060 * t224 + 0.2e1 * t677 * t1060 * t577)) * t343 - t495 - t1017 + 0.6e1 * t200 * t760 * t724 - t602 - t606 + t614 + t618
  d22 = t35 + t62 - t121 - t127 + 0.2e1 * t714 + t179 + 0.39503346997227602814966679236413104097888262435310e-1 * t715 - t186 - t191 + 0.6e1 * t726 + 0.2e1 * t761 + t7 * (t973 + t1084)
  t1 = r0 - r1
  t2 = r0 + r1
  t3 = 0.1e1 / t2
  t4 = t1 * t3
  t5 = 0.1e1 + t4
  t6 = t5 <= f.p.zeta_threshold
  t7 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t9 = t5 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = f.my_piecewise3(t6, t8, t10)
  t12 = 0.1e1 - t4
  t13 = t12 <= f.p.zeta_threshold
  t14 = t12 ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t16 = f.my_piecewise3(t13, t8, t15)
  t18 = t11 / 0.2e1 + t16 / 0.2e1
  t19 = t18 ** 2
  t20 = t19 * t18
  t21 = params.gamma * t20
  t22 = t2 ** 2
  t23 = t2 ** (0.1e1 / 0.3e1)
  t25 = 0.1e1 / t23 / t22
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t25 * t26
  t28 = 0.1e1 / t19
  t30 = 3 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t33 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t33
  t35 = t31 * t34
  t36 = 4 ** (0.1e1 / 0.3e1)
  t37 = t35 * t36
  t38 = t27 * t28 * t37
  t40 = params.BB * params.beta
  t41 = 0.1e1 / params.gamma
  t42 = t30 * t33
  t43 = t36 ** 2
  t46 = t42 * t43 / t23
  t48 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t46
  t49 = jnp.sqrt(t46)
  t52 = t46 ** 0.15e1
  t54 = t33 ** 2
  t55 = t31 * t54
  t56 = t23 ** 2
  t59 = t55 * t36 / t56
  t61 = 0.37978500000000000000000000000000000000000000000000e1 * t49 + 0.89690000000000000000000000000000000000000000000000e0 * t46 + 0.20477500000000000000000000000000000000000000000000e0 * t52 + 0.12323500000000000000000000000000000000000000000000e0 * t59
  t64 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t61
  t65 = jnp.log(t64)
  t67 = 0.621814e-1 * t48 * t65
  t68 = t1 ** 2
  t69 = t68 ** 2
  t70 = t22 ** 2
  t71 = 0.1e1 / t70
  t72 = t69 * t71
  t73 = t7 * f.p.zeta_threshold
  t75 = f.my_piecewise3(t6, t73, t9 * t5)
  t77 = f.my_piecewise3(t13, t73, t14 * t12)
  t81 = 0.1e1 / (0.2e1 * t26 - 0.2e1)
  t82 = (t75 + t77 - 0.2e1) * t81
  t84 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t46
  t89 = 0.70594500000000000000000000000000000000000000000000e1 * t49 + 0.15494250000000000000000000000000000000000000000000e1 * t46 + 0.42077500000000000000000000000000000000000000000000e0 * t52 + 0.15629250000000000000000000000000000000000000000000e0 * t59
  t92 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t89
  t93 = jnp.log(t92)
  t97 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t46
  t102 = 0.51785000000000000000000000000000000000000000000000e1 * t49 + 0.90577500000000000000000000000000000000000000000000e0 * t46 + 0.11003250000000000000000000000000000000000000000000e0 * t52 + 0.12417750000000000000000000000000000000000000000000e0 * t59
  t105 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t102
  t106 = jnp.log(t105)
  t107 = t97 * t106
  t109 = -0.3109070e-1 * t84 * t93 + t67 - 0.19751673498613801407483339618206552048944131217655e-1 * t107
  t110 = t82 * t109
  t115 = (-t67 + t72 * t110 + 0.19751673498613801407483339618206552048944131217655e-1 * t82 * t107) * t41
  t116 = 0.1e1 / t20
  t118 = jnp.exp(-t115 * t116)
  t119 = t118 - 0.1e1
  t120 = 0.1e1 / t119
  t121 = t41 * t120
  t123 = s0 + 0.2e1 * s1 + s2
  t125 = t40 * t121 * t123
  t127 = 0.1e1 / t56 / t70
  t128 = t26 ** 2
  t130 = t19 ** 2
  t131 = 0.1e1 / t130
  t133 = 0.1e1 / t54
  t135 = t30 * t133 * t43
  t136 = t127 * t128 * t131 * t135
  t137 = t125 * t136
  t139 = t38 / 0.96e2 + t137 / 0.1536e4
  t140 = params.beta * t139
  t141 = params.beta * t41
  t142 = t123 * t25
  t146 = t28 * t31 * t34 * t36
  t149 = t123 ** 2
  t151 = t40 * t121 * t149
  t154 = t142 * t26 * t146 / 0.96e2 + t151 * t136 / 0.3072e4
  t157 = t141 * t120 * t154 + 0.1e1
  t159 = t41 / t157
  t161 = params.beta ** 2
  t162 = t161 * t154
  t163 = params.gamma ** 2
  t164 = 0.1e1 / t163
  t165 = t162 * t164
  t166 = t157 ** 2
  t167 = 0.1e1 / t166
  t168 = t167 * t120
  t169 = t168 * t139
  t171 = t140 * t159 - t165 * t169
  t172 = params.beta * t154
  t174 = t172 * t159 + 0.1e1
  t175 = 0.1e1 / t174
  t176 = t171 * t175
  t178 = t2 * params.gamma
  t179 = t178 * t19
  t183 = t3 - t1 / t22
  t186 = f.my_piecewise3(t6, 0, 0.2e1 / 0.3e1 / t9 * t183)
  t188 = -t183
  t191 = f.my_piecewise3(t13, 0, 0.2e1 / 0.3e1 / t14 * t188)
  t193 = t186 / 0.2e1 + t191 / 0.2e1
  t199 = 0.1e1 / t23 / t22 / t2
  t202 = t199 * t26 * t28 * t37
  t206 = t35 * t36 * t193
  t207 = t27 * t116 * t206
  t209 = t40 * t41
  t210 = t119 ** 2
  t211 = 0.1e1 / t210
  t217 = t133 * t43
  t219 = 0.1e1 / t23 / t2
  t220 = t43 * t219
  t223 = 0.11073470983333333333333333333333333333333333333333e-2 * t42 * t220 * t65
  t224 = t61 ** 2
  t229 = t33 * t43
  t230 = t229 * t219
  t231 = 0.1e1 / t49 * t30 * t230
  t233 = t42 * t220
  t235 = t46 ** 0.5e0
  t237 = t235 * t30 * t230
  t242 = t55 * t36 / t56 / t2
  t248 = 0.10000000000000000000000000000000000000000000000000e1 * t48 / t224 * (-0.63297500000000000000000000000000000000000000000000e0 * t231 - 0.29896666666666666666666666666666666666666666666667e0 * t233 - 0.10238750000000000000000000000000000000000000000000e0 * t237 - 0.82156666666666666666666666666666666666666666666667e-1 * t242) / t64
  t253 = t70 * t2
  t260 = f.my_piecewise3(t6, 0, 0.4e1 / 0.3e1 * t9 * t183)
  t263 = f.my_piecewise3(t13, 0, 0.4e1 / 0.3e1 * t14 * t188)
  t265 = (t260 + t263) * t81
  t271 = t89 ** 2
  t286 = t102 ** 2
  t287 = 0.1e1 / t286
  t293 = -0.86308333333333333333333333333333333333333333333334e0 * t231 - 0.30192500000000000000000000000000000000000000000000e0 * t233 - 0.55016250000000000000000000000000000000000000000000e-1 * t237 - 0.82785000000000000000000000000000000000000000000000e-1 * t242
  t294 = 0.1e1 / t105
  t319 = -(t223 + t248 + 0.4e1 * t68 * t1 * t71 * t110 - 0.4e1 * t69 / t253 * t110 + t72 * t265 * t109 + t72 * t82 * (0.53237641966666666666666666666666666666666666666666e-3 * t42 * t220 * t93 + 0.10000000000000000000000000000000000000000000000000e1 * t84 / t271 * (-0.11765750000000000000000000000000000000000000000000e1 * t231 - 0.51647500000000000000000000000000000000000000000000e0 * t233 - 0.21038750000000000000000000000000000000000000000000e0 * t237 - 0.10419500000000000000000000000000000000000000000000e0 * t242) / t92 - t223 - t248 + 0.18311447306006545054854346104378990962041954983034e-3 * t42 * t220 * t106 + 0.58482236226346462072622386637590534819724553404280e0 * t97 * t287 * t293 * t294) + 0.19751673498613801407483339618206552048944131217655e-1 * t265 * t107 - 0.18311447306006545054854346104378990962041954983034e-3 * t82 * t30 * t229 * t219 * t106 - 0.58482236226346462072622386637590534819724553404280e0 * t82 * t97 * t287 * t293 * t294) * t41 * t116 + 0.3e1 * t115 * t131 * t193
  t320 = t319 * t118
  t322 = t128 * t131 * t30 * t217 * t320
  t323 = t209 * t211 * t123 * t127 * t322
  t329 = 0.1e1 / t56 / t253 * t128 * t131 * t135
  t330 = t125 * t329
  t340 = t128 / t130 / t18 * t30 * t217 * t193
  t341 = t209 * t120 * t123 * t127 * t340
  t343 = -0.7e1 / 0.288e3 * t202 - t207 / 0.48e2 - t323 / 0.1536e4 - 0.7e1 / 0.2304e4 * t330 - t341 / 0.384e3
  t371 = -0.7e1 / 0.288e3 * t123 * t199 * t26 * t146 - t142 * t26 * t116 * t206 / 0.48e2 - t209 * t211 * t149 * t127 * t322 / 0.3072e4 - 0.7e1 / 0.4608e4 * t151 * t329 - t209 * t120 * t149 * t127 * t340 / 0.768e3
  t374 = -t141 * t211 * t154 * t319 * t118 + t141 * t120 * t371
  t375 = t41 * t167 * t374
  t378 = t161 * t371 * t164
  t382 = 0.1e1 / t166 / t157 * t120
  t388 = t162 * t164 * t167
  t398 = t178 * t20
  t399 = t174 ** 2
  t400 = 0.1e1 / t399
  t405 = params.beta * t371 * t159 - t172 * t375
  d13 = t21 * t176 + 0.3e1 * t179 * t176 * t193 + t178 * t20 * (0.2e1 * t165 * t382 * t139 * t374 + t388 * t211 * t139 * t320 + params.beta * t343 * t159 - t165 * t168 * t343 - t140 * t375 - t378 * t169) * t175 - t398 * t171 * t400 * t405
  t410 = t38 / 0.48e2 + t137 / 0.768e3
  t411 = params.beta * t410
  t413 = t168 * t410
  t415 = t411 * t159 - t165 * t413
  t416 = t415 * t175
  t426 = -0.7e1 / 0.144e3 * t202 - t207 / 0.24e2 - t323 / 0.768e3 - 0.7e1 / 0.1152e4 * t330 - t341 / 0.192e3
  d14 = t21 * t416 + 0.3e1 * t179 * t416 * t193 + t178 * t20 * (0.2e1 * t165 * t382 * t410 * t374 + t388 * t211 * t410 * t320 + params.beta * t426 * t159 - t165 * t168 * t426 - t411 * t375 - t378 * t413) * t175 - t398 * t415 * t400 * t405
  d15 = d13
  t1 = r0 - r1
  t2 = r0 + r1
  t3 = 0.1e1 / t2
  t4 = t1 * t3
  t5 = 0.1e1 + t4
  t6 = t5 <= f.p.zeta_threshold
  t7 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t9 = t5 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = f.my_piecewise3(t6, t8, t10)
  t12 = 0.1e1 - t4
  t13 = t12 <= f.p.zeta_threshold
  t14 = t12 ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t16 = f.my_piecewise3(t13, t8, t15)
  t18 = t11 / 0.2e1 + t16 / 0.2e1
  t19 = t18 ** 2
  t20 = t19 * t18
  t21 = params.gamma * t20
  t22 = t2 ** 2
  t23 = t2 ** (0.1e1 / 0.3e1)
  t25 = 0.1e1 / t23 / t22
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t25 * t26
  t28 = 0.1e1 / t19
  t30 = 3 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t33 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t33
  t35 = t31 * t34
  t36 = 4 ** (0.1e1 / 0.3e1)
  t37 = t35 * t36
  t38 = t27 * t28 * t37
  t40 = params.BB * params.beta
  t41 = 0.1e1 / params.gamma
  t42 = t30 * t33
  t43 = t36 ** 2
  t46 = t42 * t43 / t23
  t48 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t46
  t49 = jnp.sqrt(t46)
  t52 = t46 ** 0.15e1
  t54 = t33 ** 2
  t55 = t31 * t54
  t56 = t23 ** 2
  t59 = t55 * t36 / t56
  t61 = 0.37978500000000000000000000000000000000000000000000e1 * t49 + 0.89690000000000000000000000000000000000000000000000e0 * t46 + 0.20477500000000000000000000000000000000000000000000e0 * t52 + 0.12323500000000000000000000000000000000000000000000e0 * t59
  t64 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t61
  t65 = jnp.log(t64)
  t67 = 0.621814e-1 * t48 * t65
  t68 = t1 ** 2
  t69 = t68 ** 2
  t70 = t22 ** 2
  t71 = 0.1e1 / t70
  t72 = t69 * t71
  t73 = t7 * f.p.zeta_threshold
  t75 = f.my_piecewise3(t6, t73, t9 * t5)
  t77 = f.my_piecewise3(t13, t73, t14 * t12)
  t81 = 0.1e1 / (0.2e1 * t26 - 0.2e1)
  t82 = (t75 + t77 - 0.2e1) * t81
  t84 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t46
  t89 = 0.70594500000000000000000000000000000000000000000000e1 * t49 + 0.15494250000000000000000000000000000000000000000000e1 * t46 + 0.42077500000000000000000000000000000000000000000000e0 * t52 + 0.15629250000000000000000000000000000000000000000000e0 * t59
  t92 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t89
  t93 = jnp.log(t92)
  t97 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t46
  t102 = 0.51785000000000000000000000000000000000000000000000e1 * t49 + 0.90577500000000000000000000000000000000000000000000e0 * t46 + 0.11003250000000000000000000000000000000000000000000e0 * t52 + 0.12417750000000000000000000000000000000000000000000e0 * t59
  t105 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t102
  t106 = jnp.log(t105)
  t107 = t97 * t106
  t109 = -0.3109070e-1 * t84 * t93 + t67 - 0.19751673498613801407483339618206552048944131217655e-1 * t107
  t110 = t82 * t109
  t115 = (-t67 + t72 * t110 + 0.19751673498613801407483339618206552048944131217655e-1 * t82 * t107) * t41
  t116 = 0.1e1 / t20
  t118 = jnp.exp(-t115 * t116)
  t119 = t118 - 0.1e1
  t120 = 0.1e1 / t119
  t121 = t41 * t120
  t123 = s0 + 0.2e1 * s1 + s2
  t125 = t40 * t121 * t123
  t127 = 0.1e1 / t56 / t70
  t128 = t26 ** 2
  t130 = t19 ** 2
  t131 = 0.1e1 / t130
  t133 = 0.1e1 / t54
  t135 = t30 * t133 * t43
  t136 = t127 * t128 * t131 * t135
  t137 = t125 * t136
  t139 = t38 / 0.96e2 + t137 / 0.1536e4
  t140 = params.beta * t139
  t141 = params.beta * t41
  t142 = t123 * t25
  t146 = t28 * t31 * t34 * t36
  t149 = t123 ** 2
  t151 = t40 * t121 * t149
  t154 = t142 * t26 * t146 / 0.96e2 + t151 * t136 / 0.3072e4
  t157 = t141 * t120 * t154 + 0.1e1
  t159 = t41 / t157
  t161 = params.beta ** 2
  t162 = t161 * t154
  t163 = params.gamma ** 2
  t164 = 0.1e1 / t163
  t165 = t162 * t164
  t166 = t157 ** 2
  t167 = 0.1e1 / t166
  t168 = t167 * t120
  t169 = t168 * t139
  t171 = t140 * t159 - t165 * t169
  t172 = params.beta * t154
  t174 = t172 * t159 + 0.1e1
  t175 = 0.1e1 / t174
  t176 = t171 * t175
  t178 = t2 * params.gamma
  t179 = t178 * t19
  t183 = -t3 - t1 / t22
  t186 = f.my_piecewise3(t6, 0, 0.2e1 / 0.3e1 / t9 * t183)
  t188 = -t183
  t191 = f.my_piecewise3(t13, 0, 0.2e1 / 0.3e1 / t14 * t188)
  t193 = t186 / 0.2e1 + t191 / 0.2e1
  t199 = 0.1e1 / t23 / t22 / t2
  t202 = t199 * t26 * t28 * t37
  t206 = t35 * t36 * t193
  t207 = t27 * t116 * t206
  t209 = t40 * t41
  t210 = t119 ** 2
  t211 = 0.1e1 / t210
  t217 = t133 * t43
  t219 = 0.1e1 / t23 / t2
  t220 = t43 * t219
  t223 = 0.11073470983333333333333333333333333333333333333333e-2 * t42 * t220 * t65
  t224 = t61 ** 2
  t229 = t33 * t43
  t230 = t229 * t219
  t231 = 0.1e1 / t49 * t30 * t230
  t233 = t42 * t220
  t235 = t46 ** 0.5e0
  t237 = t235 * t30 * t230
  t242 = t55 * t36 / t56 / t2
  t248 = 0.10000000000000000000000000000000000000000000000000e1 * t48 / t224 * (-0.63297500000000000000000000000000000000000000000000e0 * t231 - 0.29896666666666666666666666666666666666666666666667e0 * t233 - 0.10238750000000000000000000000000000000000000000000e0 * t237 - 0.82156666666666666666666666666666666666666666666667e-1 * t242) / t64
  t253 = t70 * t2
  t260 = f.my_piecewise3(t6, 0, 0.4e1 / 0.3e1 * t9 * t183)
  t263 = f.my_piecewise3(t13, 0, 0.4e1 / 0.3e1 * t14 * t188)
  t265 = (t260 + t263) * t81
  t271 = t89 ** 2
  t286 = t102 ** 2
  t287 = 0.1e1 / t286
  t293 = -0.86308333333333333333333333333333333333333333333334e0 * t231 - 0.30192500000000000000000000000000000000000000000000e0 * t233 - 0.55016250000000000000000000000000000000000000000000e-1 * t237 - 0.82785000000000000000000000000000000000000000000000e-1 * t242
  t294 = 0.1e1 / t105
  t319 = -(t223 + t248 - 0.4e1 * t68 * t1 * t71 * t110 - 0.4e1 * t69 / t253 * t110 + t72 * t265 * t109 + t72 * t82 * (0.53237641966666666666666666666666666666666666666666e-3 * t42 * t220 * t93 + 0.10000000000000000000000000000000000000000000000000e1 * t84 / t271 * (-0.11765750000000000000000000000000000000000000000000e1 * t231 - 0.51647500000000000000000000000000000000000000000000e0 * t233 - 0.21038750000000000000000000000000000000000000000000e0 * t237 - 0.10419500000000000000000000000000000000000000000000e0 * t242) / t92 - t223 - t248 + 0.18311447306006545054854346104378990962041954983034e-3 * t42 * t220 * t106 + 0.58482236226346462072622386637590534819724553404280e0 * t97 * t287 * t293 * t294) + 0.19751673498613801407483339618206552048944131217655e-1 * t265 * t107 - 0.18311447306006545054854346104378990962041954983034e-3 * t82 * t30 * t229 * t219 * t106 - 0.58482236226346462072622386637590534819724553404280e0 * t82 * t97 * t287 * t293 * t294) * t41 * t116 + 0.3e1 * t115 * t131 * t193
  t320 = t319 * t118
  t322 = t128 * t131 * t30 * t217 * t320
  t323 = t209 * t211 * t123 * t127 * t322
  t329 = 0.1e1 / t56 / t253 * t128 * t131 * t135
  t330 = t125 * t329
  t340 = t128 / t130 / t18 * t30 * t217 * t193
  t341 = t209 * t120 * t123 * t127 * t340
  t343 = -0.7e1 / 0.288e3 * t202 - t207 / 0.48e2 - t323 / 0.1536e4 - 0.7e1 / 0.2304e4 * t330 - t341 / 0.384e3
  t371 = -0.7e1 / 0.288e3 * t123 * t199 * t26 * t146 - t142 * t26 * t116 * t206 / 0.48e2 - t209 * t211 * t149 * t127 * t322 / 0.3072e4 - 0.7e1 / 0.4608e4 * t151 * t329 - t209 * t120 * t149 * t127 * t340 / 0.768e3
  t374 = -t141 * t211 * t154 * t319 * t118 + t141 * t120 * t371
  t375 = t41 * t167 * t374
  t378 = t161 * t371 * t164
  t382 = 0.1e1 / t166 / t157 * t120
  t388 = t162 * t164 * t167
  t398 = t178 * t20
  t399 = t174 ** 2
  t400 = 0.1e1 / t399
  t405 = params.beta * t371 * t159 - t172 * t375
  d23 = t21 * t176 + 0.3e1 * t179 * t176 * t193 + t178 * t20 * (0.2e1 * t165 * t382 * t139 * t374 + t388 * t211 * t139 * t320 + params.beta * t343 * t159 - t165 * t168 * t343 - t140 * t375 - t378 * t169) * t175 - t398 * t171 * t400 * t405
  t410 = t38 / 0.48e2 + t137 / 0.768e3
  t411 = params.beta * t410
  t413 = t168 * t410
  t415 = t411 * t159 - t165 * t413
  t416 = t415 * t175
  t426 = -0.7e1 / 0.144e3 * t202 - t207 / 0.24e2 - t323 / 0.768e3 - 0.7e1 / 0.1152e4 * t330 - t341 / 0.192e3
  d24 = t21 * t416 + 0.3e1 * t179 * t416 * t193 + t178 * t20 * (0.2e1 * t165 * t382 * t410 * t374 + t388 * t211 * t410 * t320 + params.beta * t426 * t159 - t165 * t168 * t426 - t411 * t375 - t378 * t413) * t175 - t398 * t415 * t400 * t405
  d25 = d23
  t1 = r0 + r1
  t2 = t1 * params.gamma
  t3 = r0 - r1
  t5 = t3 / t1
  t6 = 0.1e1 + t5
  t7 = t6 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t10 = t6 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = f.my_piecewise3(t7, t9, t11)
  t13 = 0.1e1 - t5
  t14 = t13 <= f.p.zeta_threshold
  t15 = t13 ** (0.1e1 / 0.3e1)
  t16 = t15 ** 2
  t17 = f.my_piecewise3(t14, t9, t16)
  t19 = t12 / 0.2e1 + t17 / 0.2e1
  t20 = t19 ** 2
  t21 = t20 * t19
  t22 = params.beta ** 2
  t24 = params.gamma ** 2
  t25 = 0.1e1 / t24
  t26 = 3 ** (0.1e1 / 0.3e1)
  t28 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t30 = 4 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = t1 ** (0.1e1 / 0.3e1)
  t35 = t26 * t28 * t31 / t32
  t38 = jnp.sqrt(t35)
  t41 = t35 ** 0.15e1
  t43 = t26 ** 2
  t44 = t28 ** 2
  t46 = t32 ** 2
  t49 = t43 * t44 * t30 / t46
  t55 = jnp.log(0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / (0.37978500000000000000000000000000000000000000000000e1 * t38 + 0.89690000000000000000000000000000000000000000000000e0 * t35 + 0.20477500000000000000000000000000000000000000000000e0 * t41 + 0.12323500000000000000000000000000000000000000000000e0 * t49))
  t57 = 0.621814e-1 * (0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t35) * t55
  t58 = t3 ** 2
  t59 = t58 ** 2
  t60 = t1 ** 2
  t61 = t60 ** 2
  t64 = t8 * f.p.zeta_threshold
  t66 = f.my_piecewise3(t7, t64, t10 * t6)
  t68 = f.my_piecewise3(t14, t64, t15 * t13)
  t70 = 2 ** (0.1e1 / 0.3e1)
  t74 = (t66 + t68 - 0.2e1) / (0.2e1 * t70 - 0.2e1)
  t85 = jnp.log(0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / (0.70594500000000000000000000000000000000000000000000e1 * t38 + 0.15494250000000000000000000000000000000000000000000e1 * t35 + 0.42077500000000000000000000000000000000000000000000e0 * t41 + 0.15629250000000000000000000000000000000000000000000e0 * t49))
  t98 = jnp.log(0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / (0.51785000000000000000000000000000000000000000000000e1 * t38 + 0.90577500000000000000000000000000000000000000000000e0 * t35 + 0.11003250000000000000000000000000000000000000000000e0 * t41 + 0.12417750000000000000000000000000000000000000000000e0 * t49))
  t99 = (0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t35) * t98
  t107 = 0.1e1 / params.gamma
  t111 = jnp.exp(-(-t57 + t59 / t61 * t74 * (-0.3109070e-1 * (0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t35) * t85 + t57 - 0.19751673498613801407483339618206552048944131217655e-1 * t99) + 0.19751673498613801407483339618206552048944131217655e-1 * t74 * t99) * t107 / t21)
  t112 = t111 - 0.1e1
  t113 = 0.1e1 / t112
  t116 = 0.1e1 / t46 / t61
  t119 = t70 ** 2
  t120 = t20 ** 2
  t121 = 0.1e1 / t120
  t124 = 0.1e1 / t44
  t128 = s0 + 0.2e1 * s1 + s2
  t130 = 0.1e1 / t32 / t60
  t133 = 0.1e1 / t20
  t135 = 0.1e1 / t28
  t140 = params.BB * params.beta
  t141 = t107 * t113
  t142 = t128 ** 2
  t149 = t116 * t119 * t121 * t26 * t124 * t31
  t152 = t128 * t130 * t70 * t133 * t43 * t135 * t30 / 0.96e2 + t140 * t141 * t142 * t149 / 0.3072e4
  t155 = params.beta * t107 * t113 * t152 + 0.1e1
  t156 = 0.1e1 / t155
  t159 = t22 * params.BB * t25 * t113 * t116 * t119 * t121 * t26 * t124 * t31 * t156
  t165 = t130 * t70 * t133 * t43 * t135 * t30
  t169 = t140 * t141 * t128 * t149
  t171 = t165 / 0.96e2 + t169 / 0.1536e4
  t172 = t171 ** 2
  t174 = t155 ** 2
  t175 = 0.1e1 / t174
  t184 = t22 * params.beta * t152 / t24 / params.gamma
  t187 = t112 ** 2
  t188 = 0.1e1 / t187
  t189 = 0.1e1 / t174 / t155 * t188
  t196 = t184 * t175 * t188 * params.BB * t149
  t201 = t107 * t156
  t203 = params.beta * t152 * t201 + 0.1e1
  t204 = 0.1e1 / t203
  t210 = t22 * t152 * t25
  t211 = t175 * t113
  t212 = t211 * t171
  t214 = params.beta * t171 * t201 - t210 * t212
  t215 = t214 ** 2
  t217 = t203 ** 2
  t218 = 0.1e1 / t217
  d33 = t2 * t21 * (t159 / 0.1536e4 - 0.2e1 * t22 * t172 * t25 * t175 * t113 + 0.2e1 * t184 * t189 * t172 - t196 / 0.1536e4) * t204 - t2 * t21 * t215 * t218
  t224 = t165 / 0.48e2 + t169 / 0.768e3
  d34 = t2 * t21 * (t159 / 0.768e3 - 0.2e1 * t22 * t224 * t25 * t212 + 0.2e1 * t184 * t189 * t224 * t171 - t196 / 0.768e3) * t204 - t2 * t21 * (params.beta * t224 * t201 - t210 * t211 * t224) * t218 * t214
  d35 = d33
  t1 = r0 + r1
  t2 = t1 * params.gamma
  t3 = r0 - r1
  t5 = t3 / t1
  t6 = 0.1e1 + t5
  t7 = t6 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t10 = t6 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = f.my_piecewise3(t7, t9, t11)
  t13 = 0.1e1 - t5
  t14 = t13 <= f.p.zeta_threshold
  t15 = t13 ** (0.1e1 / 0.3e1)
  t16 = t15 ** 2
  t17 = f.my_piecewise3(t14, t9, t16)
  t19 = t12 / 0.2e1 + t17 / 0.2e1
  t20 = t19 ** 2
  t21 = t20 * t19
  t22 = params.beta ** 2
  t24 = params.gamma ** 2
  t25 = 0.1e1 / t24
  t26 = 3 ** (0.1e1 / 0.3e1)
  t28 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t30 = 4 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = t1 ** (0.1e1 / 0.3e1)
  t35 = t26 * t28 * t31 / t32
  t38 = jnp.sqrt(t35)
  t41 = t35 ** 0.15e1
  t43 = t26 ** 2
  t44 = t28 ** 2
  t46 = t32 ** 2
  t49 = t43 * t44 * t30 / t46
  t55 = jnp.log(0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / (0.37978500000000000000000000000000000000000000000000e1 * t38 + 0.89690000000000000000000000000000000000000000000000e0 * t35 + 0.20477500000000000000000000000000000000000000000000e0 * t41 + 0.12323500000000000000000000000000000000000000000000e0 * t49))
  t57 = 0.621814e-1 * (0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t35) * t55
  t58 = t3 ** 2
  t59 = t58 ** 2
  t60 = t1 ** 2
  t61 = t60 ** 2
  t64 = t8 * f.p.zeta_threshold
  t66 = f.my_piecewise3(t7, t64, t10 * t6)
  t68 = f.my_piecewise3(t14, t64, t15 * t13)
  t70 = 2 ** (0.1e1 / 0.3e1)
  t74 = (t66 + t68 - 0.2e1) / (0.2e1 * t70 - 0.2e1)
  t85 = jnp.log(0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / (0.70594500000000000000000000000000000000000000000000e1 * t38 + 0.15494250000000000000000000000000000000000000000000e1 * t35 + 0.42077500000000000000000000000000000000000000000000e0 * t41 + 0.15629250000000000000000000000000000000000000000000e0 * t49))
  t98 = jnp.log(0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / (0.51785000000000000000000000000000000000000000000000e1 * t38 + 0.90577500000000000000000000000000000000000000000000e0 * t35 + 0.11003250000000000000000000000000000000000000000000e0 * t41 + 0.12417750000000000000000000000000000000000000000000e0 * t49))
  t99 = (0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t35) * t98
  t107 = 0.1e1 / params.gamma
  t111 = jnp.exp(-(-t57 + t59 / t61 * t74 * (-0.3109070e-1 * (0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t35) * t85 + t57 - 0.19751673498613801407483339618206552048944131217655e-1 * t99) + 0.19751673498613801407483339618206552048944131217655e-1 * t74 * t99) * t107 / t21)
  t112 = t111 - 0.1e1
  t113 = 0.1e1 / t112
  t116 = 0.1e1 / t46 / t61
  t119 = t70 ** 2
  t120 = t20 ** 2
  t121 = 0.1e1 / t120
  t124 = 0.1e1 / t44
  t128 = s0 + 0.2e1 * s1 + s2
  t130 = 0.1e1 / t32 / t60
  t133 = 0.1e1 / t20
  t135 = 0.1e1 / t28
  t140 = params.BB * params.beta
  t141 = t107 * t113
  t142 = t128 ** 2
  t149 = t116 * t119 * t121 * t26 * t124 * t31
  t152 = t128 * t130 * t70 * t133 * t43 * t135 * t30 / 0.96e2 + t140 * t141 * t142 * t149 / 0.3072e4
  t155 = params.beta * t107 * t113 * t152 + 0.1e1
  t156 = 0.1e1 / t155
  t159 = t22 * params.BB * t25 * t113 * t116 * t119 * t121 * t26 * t124 * t31 * t156
  t165 = t130 * t70 * t133 * t43 * t135 * t30
  t169 = t140 * t141 * t128 * t149
  t171 = t165 / 0.48e2 + t169 / 0.768e3
  t172 = t171 ** 2
  t174 = t155 ** 2
  t175 = 0.1e1 / t174
  t177 = t25 * t175 * t113
  t184 = t22 * params.beta * t152 / t24 / params.gamma
  t187 = t112 ** 2
  t188 = 0.1e1 / t187
  t189 = 0.1e1 / t174 / t155 * t188
  t196 = t184 * t175 * t188 * params.BB * t149
  t201 = t107 * t156
  t203 = params.beta * t152 * t201 + 0.1e1
  t204 = 0.1e1 / t203
  t210 = t22 * t152 * t25
  t211 = t175 * t113
  t212 = t211 * t171
  t214 = params.beta * t171 * t201 - t210 * t212
  t215 = t214 ** 2
  t217 = t203 ** 2
  t218 = 0.1e1 / t217
  d44 = t2 * t21 * (t159 / 0.384e3 - 0.2e1 * t22 * t172 * t177 + 0.2e1 * t184 * t189 * t172 - t196 / 0.384e3) * t204 - t2 * t21 * t215 * t218
  t224 = t165 / 0.96e2 + t169 / 0.1536e4
  t243 = params.beta * t224 * t201 - t210 * t211 * t224
  d45 = t2 * t21 * (t159 / 0.768e3 - 0.2e1 * t22 * t224 * t25 * t212 + 0.2e1 * t184 * t189 * t224 * t171 - t196 / 0.768e3) * t204 - t2 * t21 * t243 * t218 * t214
  t248 = t224 ** 2
  t260 = t243 ** 2
  d55 = t2 * t21 * (t159 / 0.1536e4 - 0.2e1 * t22 * t248 * t177 + 0.2e1 * t184 * t189 * t248 - t196 / 0.1536e4) * t204 - t2 * t21 * t260 * t218
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

  t1 = r0 - r1
  t2 = r0 + r1
  t3 = 0.1e1 / t2
  t4 = t1 * t3
  t5 = 0.1e1 + t4
  t6 = t5 <= f.p.zeta_threshold
  t7 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t9 = t5 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = f.my_piecewise3(t6, t8, t10)
  t12 = 0.1e1 - t4
  t13 = t12 <= f.p.zeta_threshold
  t14 = t12 ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t16 = f.my_piecewise3(t13, t8, t15)
  t18 = t11 / 0.2e1 + t16 / 0.2e1
  t19 = t18 ** 2
  t20 = t19 * t18
  t21 = params.gamma * t20
  t23 = s0 + 0.2e1 * s1 + s2
  t24 = t2 ** 2
  t25 = t24 ** 2
  t26 = t2 ** (0.1e1 / 0.3e1)
  t29 = t23 / t26 / t25
  t30 = 2 ** (0.1e1 / 0.3e1)
  t33 = 3 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t36 = 0.1e1 / jnp.pi
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t37
  t39 = 4 ** (0.1e1 / 0.3e1)
  t41 = 0.1e1 / t19 * t34 * t38 * t39
  t44 = t24 * t2
  t46 = 0.1e1 / t26 / t44
  t47 = t23 * t46
  t48 = 0.1e1 / t20
  t49 = t30 * t48
  t50 = t47 * t49
  t51 = t34 * t38
  t52 = 0.1e1 / t9
  t53 = 0.1e1 / t24
  t55 = -t1 * t53 + t3
  t58 = f.my_piecewise3(t6, 0, 0.2e1 / 0.3e1 * t52 * t55)
  t59 = 0.1e1 / t14
  t60 = -t55
  t63 = f.my_piecewise3(t13, 0, 0.2e1 / 0.3e1 * t59 * t60)
  t65 = t58 / 0.2e1 + t63 / 0.2e1
  t66 = t39 * t65
  t67 = t51 * t66
  t71 = 0.1e1 / t26 / t24
  t72 = t23 * t71
  t73 = t19 ** 2
  t74 = 0.1e1 / t73
  t75 = t30 * t74
  t76 = t72 * t75
  t77 = t65 ** 2
  t79 = t51 * t39 * t77
  t82 = t72 * t49
  t83 = t9 * t5
  t84 = 0.1e1 / t83
  t85 = t55 ** 2
  t88 = 0.1e1 / t44
  t91 = 0.2e1 * t1 * t88 - 0.2e1 * t53
  t95 = f.my_piecewise3(t6, 0, -0.2e1 / 0.9e1 * t84 * t85 + 0.2e1 / 0.3e1 * t52 * t91)
  t96 = t14 * t12
  t97 = 0.1e1 / t96
  t98 = t60 ** 2
  t101 = -t91
  t105 = f.my_piecewise3(t13, 0, -0.2e1 / 0.9e1 * t97 * t98 + 0.2e1 / 0.3e1 * t59 * t101)
  t107 = t95 / 0.2e1 + t105 / 0.2e1
  t109 = t51 * t39 * t107
  t112 = params.BB * params.beta
  t113 = 0.1e1 / params.gamma
  t114 = t112 * t113
  t115 = t33 * t37
  t116 = t39 ** 2
  t119 = t115 * t116 / t26
  t121 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t119
  t122 = jnp.sqrt(t119)
  t125 = t119 ** 0.15e1
  t127 = t37 ** 2
  t128 = t34 * t127
  t129 = t26 ** 2
  t132 = t128 * t39 / t129
  t134 = 0.37978500000000000000000000000000000000000000000000e1 * t122 + 0.89690000000000000000000000000000000000000000000000e0 * t119 + 0.20477500000000000000000000000000000000000000000000e0 * t125 + 0.12323500000000000000000000000000000000000000000000e0 * t132
  t137 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t134
  t138 = jnp.log(t137)
  t140 = 0.621814e-1 * t121 * t138
  t141 = t1 ** 2
  t142 = t141 ** 2
  t143 = 0.1e1 / t25
  t144 = t142 * t143
  t145 = t7 * f.p.zeta_threshold
  t146 = f.my_piecewise3(t6, t145, t83)
  t147 = f.my_piecewise3(t13, t145, t96)
  t151 = 0.1e1 / (0.2e1 * t30 - 0.2e1)
  t152 = (t146 + t147 - 0.2e1) * t151
  t154 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t119
  t159 = 0.70594500000000000000000000000000000000000000000000e1 * t122 + 0.15494250000000000000000000000000000000000000000000e1 * t119 + 0.42077500000000000000000000000000000000000000000000e0 * t125 + 0.15629250000000000000000000000000000000000000000000e0 * t132
  t162 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t159
  t163 = jnp.log(t162)
  t167 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t119
  t172 = 0.51785000000000000000000000000000000000000000000000e1 * t122 + 0.90577500000000000000000000000000000000000000000000e0 * t119 + 0.11003250000000000000000000000000000000000000000000e0 * t125 + 0.12417750000000000000000000000000000000000000000000e0 * t132
  t175 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t172
  t176 = jnp.log(t175)
  t177 = t167 * t176
  t179 = -0.3109070e-1 * t154 * t163 + t140 - 0.19751673498613801407483339618206552048944131217655e-1 * t177
  t180 = t152 * t179
  t185 = (-t140 + t144 * t180 + 0.19751673498613801407483339618206552048944131217655e-1 * t152 * t177) * t113
  t187 = jnp.exp(-t185 * t48)
  t188 = t187 - 0.1e1
  t189 = t188 ** 2
  t191 = 0.1e1 / t189 / t188
  t192 = t23 ** 2
  t193 = t191 * t192
  t195 = 0.1e1 / t129 / t25
  t197 = t114 * t193 * t195
  t198 = t30 ** 2
  t200 = t198 * t74 * t33
  t201 = 0.1e1 / t127
  t202 = t201 * t116
  t204 = 0.1e1 / t26 / t2
  t205 = t116 * t204
  t208 = 0.11073470983333333333333333333333333333333333333333e-2 * t115 * t205 * t138
  t209 = t134 ** 2
  t210 = 0.1e1 / t209
  t211 = t121 * t210
  t213 = 0.1e1 / t122 * t33
  t214 = t37 * t116
  t215 = t214 * t204
  t216 = t213 * t215
  t218 = t115 * t205
  t220 = t119 ** 0.5e0
  t221 = t220 * t33
  t222 = t221 * t215
  t227 = t128 * t39 / t129 / t2
  t229 = -0.63297500000000000000000000000000000000000000000000e0 * t216 - 0.29896666666666666666666666666666666666666666666667e0 * t218 - 0.10238750000000000000000000000000000000000000000000e0 * t222 - 0.82156666666666666666666666666666666666666666666667e-1 * t227
  t230 = 0.1e1 / t137
  t231 = t229 * t230
  t233 = 0.10000000000000000000000000000000000000000000000000e1 * t211 * t231
  t234 = t141 * t1
  t235 = t234 * t143
  t238 = t25 * t2
  t239 = 0.1e1 / t238
  t240 = t142 * t239
  t245 = f.my_piecewise3(t6, 0, 0.4e1 / 0.3e1 * t9 * t55)
  t248 = f.my_piecewise3(t13, 0, 0.4e1 / 0.3e1 * t14 * t60)
  t250 = (t245 + t248) * t151
  t251 = t250 * t179
  t256 = t159 ** 2
  t257 = 0.1e1 / t256
  t258 = t154 * t257
  t263 = -0.11765750000000000000000000000000000000000000000000e1 * t216 - 0.51647500000000000000000000000000000000000000000000e0 * t218 - 0.21038750000000000000000000000000000000000000000000e0 * t222 - 0.10419500000000000000000000000000000000000000000000e0 * t227
  t264 = 0.1e1 / t162
  t265 = t263 * t264
  t271 = t172 ** 2
  t272 = 0.1e1 / t271
  t273 = t167 * t272
  t278 = -0.86308333333333333333333333333333333333333333333334e0 * t216 - 0.30192500000000000000000000000000000000000000000000e0 * t218 - 0.55016250000000000000000000000000000000000000000000e-1 * t222 - 0.82785000000000000000000000000000000000000000000000e-1 * t227
  t279 = 0.1e1 / t175
  t280 = t278 * t279
  t283 = 0.53237641966666666666666666666666666666666666666666e-3 * t115 * t205 * t163 + 0.10000000000000000000000000000000000000000000000000e1 * t258 * t265 - t208 - t233 + 0.18311447306006545054854346104378990962041954983034e-3 * t115 * t205 * t176 + 0.58482236226346462072622386637590534819724553404280e0 * t273 * t280
  t284 = t152 * t283
  t288 = t152 * t33
  t290 = t214 * t204 * t176
  t293 = t152 * t167
  t295 = t272 * t278 * t279
  t299 = (t208 + t233 + 0.4e1 * t235 * t180 - 0.4e1 * t240 * t180 + t144 * t251 + t144 * t284 + 0.19751673498613801407483339618206552048944131217655e-1 * t250 * t177 - 0.18311447306006545054854346104378990962041954983034e-3 * t288 * t290 - 0.58482236226346462072622386637590534819724553404280e0 * t293 * t295) * t113
  t301 = t74 * t65
  t304 = 0.3e1 * t185 * t301 - t299 * t48
  t305 = t304 ** 2
  t306 = t187 ** 2
  t309 = t200 * t202 * t305 * t306
  t312 = 0.1e1 / t189
  t313 = t312 * t192
  t315 = 0.1e1 / t129 / t238
  t317 = t114 * t313 * t315
  t318 = t304 * t187
  t320 = t200 * t202 * t318
  t323 = t195 * t198
  t325 = t114 * t313 * t323
  t327 = 0.1e1 / t73 / t18
  t329 = t327 * t33 * t201
  t330 = t116 * t304
  t331 = t187 * t65
  t333 = t329 * t330 * t331
  t337 = t114 * t313 * t195
  t338 = t271 ** 2
  t339 = 0.1e1 / t338
  t340 = t278 ** 2
  t342 = t175 ** 2
  t343 = 0.1e1 / t342
  t344 = t339 * t340 * t343
  t345 = t293 * t344
  t349 = 0.1e1 / t122 / t119 * t34
  t350 = t127 * t39
  t352 = 0.1e1 / t129 / t24
  t353 = t350 * t352
  t354 = t349 * t353
  t356 = t214 * t71
  t357 = t213 * t356
  t359 = t116 * t71
  t360 = t115 * t359
  t362 = t119 ** (-0.5e0)
  t363 = t362 * t34
  t364 = t363 * t353
  t366 = t221 * t356
  t369 = t128 * t39 * t352
  t371 = -0.57538888888888888888888888888888888888888888888889e0 * t354 + 0.11507777777777777777777777777777777777777777777778e1 * t357 + 0.40256666666666666666666666666666666666666666666667e0 * t360 + 0.36677500000000000000000000000000000000000000000000e-1 * t364 + 0.73355000000000000000000000000000000000000000000000e-1 * t366 + 0.13797500000000000000000000000000000000000000000000e0 * t369
  t373 = t272 * t371 * t279
  t374 = t293 * t373
  t376 = t250 * t167
  t377 = t376 * t295
  t379 = t25 * t24
  t380 = 0.1e1 / t379
  t381 = t142 * t380
  t382 = t381 * t180
  t387 = t115 * t116
  t388 = t204 * t257
  t393 = 0.1e1 / t256 / t159
  t394 = t154 * t393
  t395 = t263 ** 2
  t396 = t395 * t264
  t405 = -0.78438333333333333333333333333333333333333333333333e0 * t354 + 0.15687666666666666666666666666666666666666666666667e1 * t357 + 0.68863333333333333333333333333333333333333333333333e0 * t360 + 0.14025833333333333333333333333333333333333333333333e0 * t364 + 0.28051666666666666666666666666666666666666666666667e0 * t366 + 0.17365833333333333333333333333333333333333333333333e0 * t369
  t406 = t405 * t264
  t409 = t256 ** 2
  t410 = 0.1e1 / t409
  t411 = t154 * t410
  t412 = t162 ** 2
  t413 = 0.1e1 / t412
  t414 = t395 * t413
  t418 = t115 * t359 * t138
  t419 = 0.14764627977777777777777777777777777777777777777777e-2 * t418
  t420 = t204 * t210
  t422 = t387 * t420 * t231
  t423 = 0.35616666666666666666666666666666666666666666666666e-1 * t422
  t425 = 0.1e1 / t209 / t134
  t426 = t121 * t425
  t427 = t229 ** 2
  t428 = t427 * t230
  t429 = t426 * t428
  t430 = 0.20000000000000000000000000000000000000000000000000e1 * t429
  t437 = -0.42198333333333333333333333333333333333333333333333e0 * t354 + 0.84396666666666666666666666666666666666666666666666e0 * t357 + 0.39862222222222222222222222222222222222222222222223e0 * t360 + 0.68258333333333333333333333333333333333333333333333e-1 * t364 + 0.13651666666666666666666666666666666666666666666667e0 * t366 + 0.13692777777777777777777777777777777777777777777778e0 * t369
  t438 = t437 * t230
  t439 = t211 * t438
  t440 = 0.10000000000000000000000000000000000000000000000000e1 * t439
  t441 = t209 ** 2
  t442 = 0.1e1 / t441
  t443 = t121 * t442
  t444 = t137 ** 2
  t445 = 0.1e1 / t444
  t446 = t427 * t445
  t447 = t443 * t446
  t448 = 0.16081979498692535066756296899072713062105388428051e2 * t447
  t452 = t204 * t272
  t457 = 0.1e1 / t271 / t172
  t458 = t167 * t457
  t459 = t340 * t279
  t462 = t371 * t279
  t465 = t167 * t339
  t466 = t340 * t343
  t469 = -0.70983522622222222222222222222222222222222222222221e-3 * t115 * t359 * t163 - 0.34246666666666666666666666666666666666666666666666e-1 * t387 * t388 * t265 - 0.20000000000000000000000000000000000000000000000000e1 * t394 * t396 + 0.10000000000000000000000000000000000000000000000000e1 * t258 * t406 + 0.32163958997385070133512593798145426124210776856102e2 * t411 * t414 + t419 + t423 + t430 - t440 - t448 - 0.24415263074675393406472461472505321282722606644045e-3 * t115 * t359 * t176 - 0.10843581300301739842632067522386578331157260943710e-1 * t387 * t452 * t280 - 0.11696447245269292414524477327518106963944910680856e1 * t458 * t459 + 0.58482236226346462072622386637590534819724553404280e0 * t273 * t462 + 0.17315859105681463759666483083807725165579399831905e2 * t465 * t466
  t470 = t152 * t469
  t471 = t144 * t470
  t472 = 0.1e1 / t10
  t478 = f.my_piecewise3(t6, 0, 0.4e1 / 0.9e1 * t472 * t85 + 0.4e1 / 0.3e1 * t9 * t91)
  t479 = 0.1e1 / t15
  t485 = f.my_piecewise3(t13, 0, 0.4e1 / 0.9e1 * t479 * t98 + 0.4e1 / 0.3e1 * t14 * t101)
  t487 = (t478 + t485) * t151
  t488 = t487 * t179
  t489 = t144 * t488
  t490 = t250 * t283
  t491 = t144 * t490
  t493 = t240 * t251
  t495 = t240 * t284
  t497 = t235 * t251
  t499 = t235 * t284
  t501 = -0.17315859105681463759666483083807725165579399831905e2 * t345 - 0.58482236226346462072622386637590534819724553404280e0 * t374 - 0.11696447245269292414524477327518106963944910680856e1 * t377 + 0.20e2 * t382 + t471 + t489 + 0.2e1 * t491 - 0.8e1 * t493 - 0.8e1 * t495 + 0.8e1 * t497 + 0.8e1 * t499
  t502 = t487 * t177
  t504 = t250 * t33
  t505 = t504 * t290
  t508 = t457 * t340 * t279
  t509 = t293 * t508
  t511 = t152 * t115
  t512 = t205 * t295
  t513 = t511 * t512
  t515 = t141 * t143
  t516 = t515 * t180
  t518 = t234 * t239
  t519 = t518 * t180
  t522 = t214 * t71 * t176
  t523 = t288 * t522
  t525 = -t430 + 0.19751673498613801407483339618206552048944131217655e-1 * t502 + t448 + t440 - 0.36622894612013090109708692208757981924083909966068e-3 * t505 + 0.11696447245269292414524477327518106963944910680856e1 * t509 - t423 + 0.10843581300301739842632067522386578331157260943710e-1 * t513 - t419 + 0.12e2 * t516 - 0.32e2 * t519 + 0.24415263074675393406472461472505321282722606644045e-3 * t523
  t527 = (t501 + t525) * t113
  t531 = t327 * t77
  t534 = t74 * t107
  t537 = -0.12e2 * t185 * t531 + 0.3e1 * t185 * t534 + 0.6e1 * t299 * t301 - t527 * t48
  t540 = t200 * t202 * t537 * t187
  t545 = t200 * t202 * t305 * t187
  t548 = 0.1e1 / t188
  t551 = t112 * t113 * t548 * t192
  t553 = 0.1e1 / t129 / t379
  t557 = t33 * t201 * t116
  t561 = t548 * t192
  t563 = t114 * t561 * t315
  t565 = t198 * t327 * t33
  t567 = t565 * t202 * t65
  t571 = t114 * t561 * t195
  t573 = 0.1e1 / t73 / t19
  t575 = t198 * t573 * t33
  t577 = t575 * t202 * t77
  t581 = t565 * t202 * t107
  t584 = 0.35e2 / 0.432e3 * t29 * t30 * t41 + 0.7e1 / 0.72e2 * t50 * t67 + t76 * t79 / 0.16e2 - t82 * t109 / 0.48e2 + t197 * t309 / 0.1536e4 + 0.7e1 / 0.2304e4 * t317 * t320 + t325 * t333 / 0.384e3 - t337 * t540 / 0.3072e4 - t337 * t545 / 0.3072e4 + 0.119e3 / 0.13824e5 * t551 * t553 * t198 * t74 * t557 + 0.7e1 / 0.576e3 * t563 * t567 + 0.5e1 / 0.768e3 * t571 * t577 - t571 * t581 / 0.768e3
  t585 = params.beta * t584
  t586 = params.beta * t113
  t594 = t72 * t30 * t41 / 0.96e2 + t551 * t323 * t74 * t557 / 0.3072e4
  t597 = t586 * t548 * t594 + 0.1e1
  t599 = t113 / t597
  t608 = t315 * t198
  t615 = -0.7e1 / 0.288e3 * t47 * t30 * t41 - t82 * t67 / 0.48e2 - t337 * t320 / 0.3072e4 - 0.7e1 / 0.4608e4 * t551 * t608 * t74 * t557 - t571 * t567 / 0.768e3
  t616 = params.beta * t615
  t617 = t597 ** 2
  t619 = t113 / t617
  t620 = t586 * t312
  t621 = t594 * t304
  t626 = -t620 * t621 * t187 + t586 * t548 * t615
  t627 = t619 * t626
  t630 = params.beta * t594
  t632 = 0.1e1 / t617 / t597
  t634 = t626 ** 2
  t635 = t113 * t632 * t634
  t638 = t586 * t191
  t639 = t594 * t305
  t647 = t594 * t537
  t654 = -0.2e1 * t620 * t615 * t304 * t187 - t620 * t639 * t187 - t620 * t647 * t187 + 0.2e1 * t638 * t639 * t306 + t586 * t548 * t584
  t655 = t619 * t654
  t657 = t585 * t599 - 0.2e1 * t616 * t627 + 0.2e1 * t630 * t635 - t630 * t655
  t659 = t630 * t599 + 0.1e1
  t660 = 0.1e1 / t659
  t661 = t657 * t660
  t668 = params.gamma * t18
  t669 = jnp.log(t659)
  t673 = params.gamma * t19
  t674 = t669 * t107
  t679 = t616 * t599 - t630 * t627
  t680 = t679 ** 2
  t681 = t659 ** 2
  t682 = 0.1e1 / t681
  t683 = t680 * t682
  t687 = 0.12e2 * t240 * t470
  t689 = 0.24e2 * t240 * t490
  t693 = 0.48245938496077605200268890697218139186316165284153e2 * t443 * t437 * t445 * t229
  t696 = 0.60000000000000000000000000000000000000000000000000e1 * t426 * t438 * t229
  t699 = t85 * t55
  t705 = t1 * t143
  t707 = 0.6e1 * t88 - 0.6e1 * t705
  t711 = f.my_piecewise3(t6, 0, -0.8e1 / 0.27e2 / t10 / t5 * t699 + 0.4e1 / 0.3e1 * t472 * t55 * t91 + 0.4e1 / 0.3e1 * t9 * t707)
  t714 = t98 * t60
  t720 = -t707
  t724 = f.my_piecewise3(t13, 0, -0.8e1 / 0.27e2 / t15 / t12 * t714 + 0.4e1 / 0.3e1 * t479 * t60 * t101 + 0.4e1 / 0.3e1 * t14 * t720)
  t726 = (t711 + t724) * t151
  t728 = t144 * t726 * t179
  t730 = 0.12e2 * t235 * t470
  t736 = t77 * t65
  t743 = t5 ** 2
  t754 = f.my_piecewise3(t6, 0, 0.8e1 / 0.27e2 / t9 / t743 * t699 - 0.2e1 / 0.3e1 * t84 * t55 * t91 + 0.2e1 / 0.3e1 * t52 * t707)
  t755 = t12 ** 2
  t766 = f.my_piecewise3(t13, 0, 0.8e1 / 0.27e2 / t14 / t755 * t714 - 0.2e1 / 0.3e1 * t97 * t60 * t101 + 0.2e1 / 0.3e1 * t59 * t720)
  t768 = t754 / 0.2e1 + t766 / 0.2e1
  t782 = t74 * t33 * t201
  t783 = t116 * t537
  t789 = t114 * t193 * t323
  t790 = t306 * t537
  t808 = t340 * t278
  t812 = 0.35089341735807877243573431982554320891834732042568e1 * t293 * t339 * t808 * t279
  t814 = 0.1e1 / t338 / t172
  t818 = 0.10389515463408878255799889850284635099347639899143e3 * t293 * t814 * t808 * t343
  t821 = 0.17544670867903938621786715991277160445917366021284e1 * t487 * t167 * t295
  t823 = 0.24e2 * t235 * t490
  t825 = 0.60e2 * t381 * t284
  t827 = 0.60e2 * t381 * t251
  t828 = -t687 - t689 + t693 - t696 + t728 + t730 - t812 + t818 - t821 + t823 + t825 + t827
  t832 = t427 * t229
  t837 = 0.51726012919273400298984252201052768390886626637712e3 * t121 / t441 / t209 * t832 / t444 / t137
  t840 = 0.60000000000000000000000000000000000000000000000000e1 * t443 * t832 * t230
  t846 = 0.96491876992155210400537781394436278372632330568306e2 * t121 / t441 / t134 * t832 * t445
  t849 = 0.3e1 * t144 * t487 * t283
  t852 = 0.53424999999999999999999999999999999999999999999999e-1 * t387 * t420 * t438
  t856 = 0.71233333333333333333333333333333333333333333333331e-1 * t387 * t71 * t210 * t231
  t859 = 0.48159733137676571081572406076840235616767705782485e0 * t511 * t205 * t344
  t862 = 0.16265371950452609763948101283579867496735891415565e-1 * t511 * t205 * t373
  t865 = 0.32530743900905219527896202567159734993471782831130e-1 * t250 * t115 * t512
  t868 = 0.32530743900905219527896202567159734993471782831130e-1 * t511 * t205 * t508
  t871 = 0.21687162600603479685264135044773156662314521887420e-1 * t511 * t359 * t295
  t873 = 0.19751673498613801407483339618206552048944131217655e-1 * t726 * t177
  t878 = 0.1e1 / t122 / t132 * t36 * t143 / 0.4e1
  t881 = 0.1e1 / t129 / t44
  t882 = t350 * t881
  t883 = t349 * t882
  t885 = t214 * t46
  t886 = t213 * t885
  t888 = t116 * t46
  t889 = t115 * t888
  t891 = t119 ** (-0.15e1)
  t893 = t891 * t36 * t143
  t895 = t363 * t882
  t897 = t221 * t885
  t900 = t128 * t39 * t881
  t902 = -0.34523333333333333333333333333333333333333333333333e1 * t878 + 0.23015555555555555555555555555555555555555555555556e1 * t883 - 0.26851481481481481481481481481481481481481481481482e1 * t886 - 0.93932222222222222222222222222222222222222222222223e0 * t889 + 0.73355000000000000000000000000000000000000000000000e-1 * t893 - 0.14671000000000000000000000000000000000000000000000e0 * t895 - 0.17116166666666666666666666666666666666666666666667e0 * t897 - 0.36793333333333333333333333333333333333333333333333e0 * t900
  t906 = 0.58482236226346462072622386637590534819724553404280e0 * t293 * t272 * t902 * t279
  t907 = t837 + t840 - t846 + t849 - t852 + t856 + t859 + t862 + t865 - t868 - t871 + t873 - t906
  t910 = 0.51947577317044391278999449251423175496738199495715e2 * t376 * t344
  t912 = 0.1e1 / t338 / t271
  t915 = 0.1e1 / t342 / t175
  t918 = 0.10254018858216406658218194626490193680059335835414e4 * t293 * t912 * t808 * t915
  t920 = 0.17544670867903938621786715991277160445917366021284e1 * t376 * t373
  t922 = 0.35089341735807877243573431982554320891834732042568e1 * t376 * t508
  t926 = t395 * t263
  t969 = -t693 + t696 + 0.16562821945185185185185185185185185185185185185185e-2 * t115 * t888 * t163 - t837 - t840 + t846 + 0.60000000000000000000000000000000000000000000000000e1 * t411 * t926 * t264 - 0.19298375398431042080107556278887255674526466113661e3 * t154 / t409 / t159 * t926 * t413 + 0.10000000000000000000000000000000000000000000000000e1 * t258 * (-0.47063000000000000000000000000000000000000000000000e1 * t878 + 0.31375333333333333333333333333333333333333333333334e1 * t883 - 0.36604555555555555555555555555555555555555555555556e1 * t886 - 0.16068111111111111111111111111111111111111111111111e1 * t889 + 0.28051666666666666666666666666666666666666666666666e0 * t893 - 0.56103333333333333333333333333333333333333333333332e0 * t895 - 0.65453888888888888888888888888888888888888888888890e0 * t897 - 0.46308888888888888888888888888888888888888888888888e0 * t900) * t264 + 0.35089341735807877243573431982554320891834732042568e1 * t465 * t808 * t279 + t852 - t856 + 0.20690405167709360119593700880421107356354650655085e4 * t154 / t409 / t256 * t926 / t412 / t162 + 0.56968947174242584615102410102512416326352748836105e-3 * t115 * t888 * t176 + 0.96491876992155210400537781394436278372632330568306e2 * t411 * t405 * t413 * t263 - 0.60000000000000000000000000000000000000000000000000e1 * t394 * t265 * t405
  t973 = t371 * t343
  t988 = 0.10000000000000000000000000000000000000000000000000e1 * t211 * (-0.25319000000000000000000000000000000000000000000000e1 * t878 + 0.16879333333333333333333333333333333333333333333333e1 * t883 - 0.19692555555555555555555555555555555555555555555555e1 * t886 - 0.93011851851851851851851851851851851851851851851854e0 * t889 + 0.13651666666666666666666666666666666666666666666667e0 * t893 - 0.27303333333333333333333333333333333333333333333333e0 * t895 - 0.31853888888888888888888888888888888888888888888890e0 * t897 - 0.36514074074074074074074074074074074074074074074075e0 * t900) * t230
  t1014 = 0.85917975471764868594145516183295969534298037676861e0 * t387 * t204 * t442 * t446
  t1018 = 0.10685000000000000000000000000000000000000000000000e0 * t387 * t204 * t425 * t428
  t1040 = 0.34450798614814814814814814814814814814814814814813e-2 * t115 * t888 * t138
  t1041 = -0.35089341735807877243573431982554320891834732042568e1 * t458 * t280 * t371 + 0.51947577317044391278999449251423175496738199495715e2 * t465 * t973 * t278 - t988 + 0.21687162600603479685264135044773156662314521887420e-1 * t387 * t71 * t272 * t280 - 0.16265371950452609763948101283579867496735891415565e-1 * t387 * t452 * t462 - 0.48159733137676571081572406076840235616767705782485e0 * t387 * t204 * t339 * t466 + 0.68493333333333333333333333333333333333333333333332e-1 * t387 * t71 * t257 * t265 - 0.51369999999999999999999999999999999999999999999999e-1 * t387 * t388 * t406 - 0.16522625736956710527585419434107305400007076070979e1 * t387 * t204 * t410 * t414 + t1014 - t1018 + 0.10274000000000000000000000000000000000000000000000e0 * t387 * t204 * t393 * t396 + 0.32530743900905219527896202567159734993471782831130e-1 * t387 * t204 * t457 * t459 + 0.10254018858216406658218194626490193680059335835414e4 * t167 * t912 * t808 * t915 - 0.10389515463408878255799889850284635099347639899143e3 * t167 * t814 * t808 * t343 + 0.58482236226346462072622386637590534819724553404280e0 * t273 * t902 * t279 - t1040
  t1044 = t144 * t152 * (t969 + t1041)
  t1047 = 0.3e1 * t144 * t250 * t469
  t1049 = 0.12e2 * t235 * t488
  t1051 = 0.12e2 * t240 * t488
  t1053 = 0.96e2 * t518 * t284
  t1055 = 0.96e2 * t518 * t251
  t1058 = 0.240e3 * t234 * t380 * t180
  t1059 = t25 * t44
  t1063 = 0.120e3 * t142 / t1059 * t180
  t1064 = -t910 - t918 - t920 + t922 + t1044 + t1047 + t1049 - t1051 - t1053 - t1055 + t1058 - t1063
  t1066 = 0.24e2 * t705 * t180
  t1069 = 0.144e3 * t141 * t239 * t180
  t1071 = 0.36e2 * t515 * t284
  t1073 = 0.36e2 * t515 * t251
  t1077 = 0.51947577317044391278999449251423175496738199495715e2 * t293 * t339 * t278 * t973
  t1081 = 0.35089341735807877243573431982554320891834732042568e1 * t293 * t457 * t371 * t280
  t1083 = 0.73245789224026180219417384417515963848167819932136e-3 * t504 * t522
  t1087 = 0.56968947174242584615102410102512416326352748836105e-3 * t288 * t214 * t46 * t176
  t1090 = 0.54934341918019635164563038313136972886125864949102e-3 * t487 * t33 * t290
  t1091 = t1066 - t1069 + t1071 + t1073 - t1077 + t1081 + t1083 - t1087 - t1090 + t988 - t1014 + t1018 + t1040
  t1112 = -(t828 + t907 + t1064 + t1091) * t113 * t48 + 0.9e1 * t527 * t301 - 0.36e2 * t299 * t531 + 0.9e1 * t299 * t534 + 0.60e2 * t185 * t573 * t736 - 0.36e2 * t185 * t327 * t65 * t107 + 0.3e1 * t185 * t74 * t768
  t1120 = t305 * t304
  t1130 = -0.7e1 / 0.16e2 * t47 * t75 * t79 - t72 * t30 * t327 * t51 * t39 * t736 / 0.4e1 + 0.7e1 / 0.48e2 * t50 * t109 - t82 * t51 * t39 * t768 / 0.48e2 - 0.35e2 / 0.72e2 * t29 * t49 * t67 + t325 * t329 * t330 * t187 * t107 / 0.256e3 - t325 * t782 * t783 * t318 / 0.1024e4 + t789 * t782 * t330 * t790 / 0.512e3 - 0.7e1 / 0.192e3 * t114 * t313 * t608 * t333 + t325 * t329 * t783 * t331 / 0.256e3 + 0.5e1 / 0.256e3 * t571 * t575 * t202 * t65 * t107 - t337 * t200 * t202 * t1112 * t187 / 0.3072e4 + 0.7e1 / 0.1536e4 * t317 * t540 - t337 * t200 * t202 * t1120 * t187 / 0.3072e4 - 0.119e3 / 0.4608e4 * t114 * t313 * t553 * t320
  t1142 = t189 ** 2
  t1143 = 0.1e1 / t1142
  t1147 = t306 * t187
  t1177 = t116 * t305
  t1207 = 0.7e1 / 0.1536e4 * t317 * t545 - 0.7e1 / 0.768e3 * t114 * t193 * t315 * t309 + t197 * t200 * t202 * t1120 * t306 / 0.512e3 - t114 * t1143 * t192 * t195 * t200 * t202 * t1120 * t1147 / 0.512e3 + 0.3e1 / 0.16e2 * t76 * t51 * t66 * t107 - 0.35e2 / 0.384e3 * t563 * t577 - 0.5e1 / 0.128e3 * t571 * t198 / t73 / t20 * t33 * t202 * t736 - 0.119e3 / 0.1152e4 * t114 * t561 * t553 * t567 + 0.7e1 / 0.384e3 * t563 * t581 - t571 * t565 * t202 * t768 / 0.768e3 - t789 * t329 * t1177 * t306 * t65 / 0.128e3 - 0.5e1 / 0.256e3 * t325 * t573 * t33 * t201 * t330 * t187 * t77 + t325 * t329 * t1177 * t331 / 0.256e3 - 0.595e3 / 0.10368e5 * t551 / t129 / t1059 * t198 * t74 * t557 - 0.455e3 / 0.1296e4 * t23 / t26 / t238 * t30 * t41
  t1208 = t1130 + t1207
  t1217 = t617 ** 2
  t1230 = t594 * t1120
  t1234 = t615 * t305
  t1265 = -t620 * t594 * t1112 * t187 - 0.6e1 * t586 * t1143 * t1230 * t1147 - 0.3e1 * t620 * t584 * t304 * t187 - 0.3e1 * t620 * t615 * t537 * t187 + t586 * t548 * t1208 - t620 * t1230 * t187 + 0.6e1 * t638 * t1230 * t306 - 0.3e1 * t620 * t1234 * t187 + 0.6e1 * t638 * t1234 * t306 - 0.3e1 * t620 * t647 * t318 + 0.6e1 * t638 * t621 * t790
  t1271 = t679 * t660
  t1275 = -t687 - t689 + t693 - t696 + t728 + t730 + t21 * (params.beta * t1208 * t599 - 0.3e1 * t585 * t627 + 0.6e1 * t616 * t635 - 0.3e1 * t616 * t655 - 0.6e1 * t630 * t113 / t1217 * t634 * t626 + 0.6e1 * t630 * t113 * t632 * t626 * t654 - t630 * t619 * t1265) * t660 - t812 + t818 - t821 + t823 + t825 + t827 + 0.9e1 * t673 * t1271 * t107 + t837
  t1292 = t840 - t846 + 0.18e2 * t668 * t1271 * t77 + t849 - t852 + t856 + t859 + t862 + t865 - t868 - t871 + 0.2e1 * t21 * t680 * t679 / t681 / t659 + t873 - 0.9e1 * t673 * t683 * t65 - 0.3e1 * t21 * t657 * t682 * t679
  t1297 = 0.3e1 * t673 * t669 * t768 + t1044 + t1047 + t1049 - t1051 - t1053 - t1055 + t1058 - t1063 + t1066 - t906 - t910 - t918 - t920 + t922
  t1307 = 0.9e1 * t673 * t661 * t65 + 0.18e2 * t668 * t674 * t65 + 0.6e1 * params.gamma * t736 * t669 - t1014 + t1018 + t1040 - t1069 + t1071 + t1073 - t1077 + t1081 + t1083 - t1087 - t1090 + t988
  t1318 = 0.3e1 * t21 * t661 + 0.6e1 * t491 - 0.24e2 * t493 + 0.3e1 * t489 + 0.48245938496077605200268890697218139186316165284153e2 * t447 + 0.18e2 * t668 * t669 * t77 + 0.9e1 * t673 * t674 - 0.3e1 * t21 * t683 + t2 * (t1275 + t1292 + t1297 + t1307) + 0.18e2 * t673 * t1271 * t65 - 0.60000000000000000000000000000000000000000000000000e1 * t429 + 0.30000000000000000000000000000000000000000000000000e1 * t439 - 0.24e2 * t495 + 0.24e2 * t497
  t1334 = 0.59255020495841404222450018854619656146832393652965e-1 * t502 - 0.51947577317044391278999449251423175496738199495715e2 * t345 - 0.17544670867903938621786715991277160445917366021284e1 * t374 - 0.35089341735807877243573431982554320891834732042568e1 * t377 + 0.36e2 * t516 - 0.96e2 * t519 + 0.24e2 * t499 - 0.10685000000000000000000000000000000000000000000000e0 * t422 - 0.10986868383603927032912607662627394577225172989820e-2 * t505 + 0.73245789224026180219417384417515963848167819932136e-3 * t523 + 0.32530743900905219527896202567159734993471782831130e-1 * t513 - 0.44293883933333333333333333333333333333333333333332e-2 * t418 + 0.60e2 * t382 + 0.3e1 * t471 + 0.35089341735807877243573431982554320891834732042568e1 * t509
  d111 = t1318 + t1334

  res = {'v3rho3': d111}
  return res