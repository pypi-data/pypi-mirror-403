"""Generated from gga_c_zvpbeint.mpl."""

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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mbeta = lambda rs=None, t=None: params_beta

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  zvpbeint_nu = lambda rs, z, t: t * f.mphi(z) * (3 / rs) ** (1 / 6)

  mgamma = params_gamma

  BB = params_BB

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  zvpbeint_ff = lambda rs, z, t: jnp.exp(-params_alpha * zvpbeint_nu(rs, z, t) ** 3 * jnp.maximum(z ** 2, 1e-20) ** (params_omega / 2))

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  functional_body = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + zvpbeint_ff(rs, z, tp(rs, z, xt)) * fH(rs, z, tp(rs, z, xt))

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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mbeta = lambda rs=None, t=None: params_beta

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  zvpbeint_nu = lambda rs, z, t: t * f.mphi(z) * (3 / rs) ** (1 / 6)

  mgamma = params_gamma

  BB = params_BB

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  zvpbeint_ff = lambda rs, z, t: jnp.exp(-params_alpha * zvpbeint_nu(rs, z, t) ** 3 * jnp.maximum(z ** 2, 1e-20) ** (params_omega / 2))

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  functional_body = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + zvpbeint_ff(rs, z, tp(rs, z, xt)) * fH(rs, z, tp(rs, z, xt))

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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mbeta = lambda rs=None, t=None: params_beta

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  zvpbeint_nu = lambda rs, z, t: t * f.mphi(z) * (3 / rs) ** (1 / 6)

  mgamma = params_gamma

  BB = params_BB

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  zvpbeint_ff = lambda rs, z, t: jnp.exp(-params_alpha * zvpbeint_nu(rs, z, t) ** 3 * jnp.maximum(z ** 2, 1e-20) ** (params_omega / 2))

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  functional_body = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + zvpbeint_ff(rs, z, tp(rs, z, xt)) * fH(rs, z, tp(rs, z, xt))

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
  t88 = s0 + 0.2e1 * s1 + s2
  t89 = jnp.sqrt(t88)
  t91 = params.alpha * t89 * t88
  t94 = 0.1e1 / t14 / t11
  t95 = 0.1e1 / t3
  t96 = t19 * t95
  t99 = jnp.sqrt(t96 * t5 * t8)
  t101 = 0.1e1 / t35
  t102 = t33 * t101
  t103 = 0.1e-19 < t102
  t104 = f.my_piecewise3(t103, t102, 0.1e-19)
  t106 = t104 ** (params.omega / 0.2e1)
  t107 = t94 * t99 * t106
  t110 = jnp.exp(-t91 * t37 * t107 / 0.16e2)
  t111 = jnp.log(0.2e1)
  t112 = 0.1e1 - t111
  t113 = t110 * t112
  t114 = jnp.pi ** 2
  t115 = 0.1e1 / t114
  t116 = t43 ** 2
  t117 = t45 ** 2
  t118 = f.my_piecewise3(t42, t116, t117)
  t119 = t50 ** 2
  t120 = f.my_piecewise3(t49, t116, t119)
  t122 = t118 / 0.2e1 + t120 / 0.2e1
  t123 = t122 ** 2
  t124 = t123 * t122
  t127 = 0.1e1 / t8 / t35
  t128 = t88 * t127
  t130 = 0.1e1 / t123
  t133 = t130 * t19 * t95 * t5
  t136 = 0.1e1 / t112
  t137 = params.beta * t136
  t139 = (-t31 + t84 + t86) * t136
  t140 = 0.1e1 / t124
  t141 = t114 * t140
  t143 = jnp.exp(-t139 * t141)
  t144 = t143 - 0.1e1
  t145 = 0.1e1 / t144
  t146 = t114 * t145
  t147 = t88 ** 2
  t149 = t137 * t146 * t147
  t151 = 0.1e1 / t22 / t36
  t152 = t54 ** 2
  t154 = t123 ** 2
  t155 = 0.1e1 / t154
  t157 = 0.1e1 / t20
  t159 = t1 * t157 * t6
  t160 = t151 * t152 * t155 * t159
  t163 = t128 * t54 * t133 / 0.96e2 + t149 * t160 / 0.3072e4
  t164 = params.beta * t163
  t168 = t137 * t146 * t163 + 0.1e1
  t170 = t136 * t114 / t168
  t172 = t164 * t170 + 0.1e1
  t173 = jnp.log(t172)
  t174 = t115 * t124 * t173
  t175 = t113 * t174
  t177 = 0.1e1 / t8 / t7
  t178 = t6 * t177
  t181 = 0.11073470983333333333333333333333333333333333333333e-2 * t4 * t178 * t30
  t182 = t27 ** 2
  t187 = t3 * t6
  t188 = t187 * t177
  t189 = 0.1e1 / t14 * t1 * t188
  t191 = t4 * t178
  t193 = t11 ** 0.5e0
  t195 = t193 * t1 * t188
  t200 = t21 * t5 / t22 / t7
  t205 = t13 / t182 * (-0.39359271665000000000000000000000000000000000000000e-1 * t189 - 0.18590165886666666666666666666666666666666666666667e-1 * t191 - 0.63665980925000000000000000000000000000000000000000e-2 * t195 - 0.51086165526666666666666666666666666666666666666667e-2 * t200) / t29
  t209 = 0.4e1 * t33 * t32 * t37 * t83
  t210 = t36 * t7
  t211 = 0.1e1 / t210
  t214 = 0.4e1 * t34 * t211 * t83
  t215 = t32 * t101
  t216 = t39 - t215
  t219 = f.my_piecewise3(t42, 0, 0.4e1 / 0.3e1 * t45 * t216)
  t220 = -t216
  t223 = f.my_piecewise3(t49, 0, 0.4e1 / 0.3e1 * t50 * t220)
  t225 = (t219 + t223) * t57
  t227 = t38 * t225 * t82
  t231 = t65 ** 2
  t245 = t76 ** 2
  t246 = 0.1e1 / t245
  t252 = -0.29149603883333333333333333333333333333333333333333e-1 * t189 - 0.10197154565000000000000000000000000000000000000000e-1 * t191 - 0.18581078242500000000000000000000000000000000000000e-2 * t195 - 0.27959640330000000000000000000000000000000000000000e-2 * t200
  t253 = 0.1e1 / t78
  t259 = t38 * t58 * (0.53237641966666666666666666666666666666666666666667e-3 * t4 * t178 * t68 + t60 / t231 * (-0.36580540352500000000000000000000000000000000000000e-1 * t189 - 0.16057569282500000000000000000000000000000000000000e-1 * t191 - 0.65410946462500000000000000000000000000000000000000e-2 * t195 - 0.32394954865000000000000000000000000000000000000000e-2 * t200) / t67 - t181 - t205 + 0.18311447306006545054854346104378990962041954983034e-3 * t4 * t178 * t79 + 0.58482236226346462072622386637590534819724553404281e0 * t71 * t246 * t252 * t253)
  t261 = 0.58482236226346462072622386637590534819724553404281e0 * t225 * t80
  t266 = 0.18311447306006545054854346104378990962041954983034e-3 * t58 * t1 * t187 * t177 * t79
  t271 = 0.58482236226346462072622386637590534819724553404281e0 * t58 * t71 * t246 * t252 * t253
  t274 = t91 * t211 * t107 / 0.4e1
  t282 = t99 * t106
  t286 = t91 / t8 / t210 / t14 / t25 * t282 * t4 * t6 / 0.128e3
  t291 = t96 * t5
  t294 = t91 * t151 * t94 / t99 * t106 * t291 / 0.96e2
  t295 = t37 * t94
  t296 = t91 * t295
  t297 = t35 * t7
  t299 = t33 / t297
  t302 = f.my_piecewise3(t103, 0.2e1 * t215 - 0.2e1 * t299, 0)
  t304 = 0.1e1 / t104
  t313 = t113 * t115
  t314 = t123 * t173
  t315 = 0.1e1 / t45
  t318 = f.my_piecewise3(t42, 0, 0.2e1 / 0.3e1 * t315 * t216)
  t319 = 0.1e1 / t50
  t322 = f.my_piecewise3(t49, 0, 0.2e1 / 0.3e1 * t319 * t220)
  t324 = t318 / 0.2e1 + t322 / 0.2e1
  t333 = 0.7e1 / 0.288e3 * t88 / t8 / t297 * t54 * t133
  t335 = t128 * t54 * t140
  t340 = t137 * t114
  t341 = t144 ** 2
  t342 = 0.1e1 / t341
  t345 = t340 * t342 * t147 * t151
  t347 = t152 * t155 * t1
  t348 = t157 * t6
  t352 = t114 * t155
  t357 = (-(t181 + t205 + t209 - t214 + t227 + t259 + t261 - t266 - t271) * t136 * t141 + 0.3e1 * t139 * t352 * t324) * t143
  t368 = 0.7e1 / 0.4608e4 * t149 / t22 / t210 * t152 * t155 * t159
  t371 = t340 * t145 * t147 * t151
  t375 = t152 / t154 / t122 * t1
  t380 = -t333 - t335 * t96 * t5 * t324 / 0.48e2 - t345 * t347 * t348 * t357 / 0.3072e4 - t368 - t371 * t375 * t348 * t324 / 0.768e3
  t383 = t164 * t136
  t384 = t168 ** 2
  t385 = 0.1e1 / t384
  t386 = t114 * t385
  t387 = t342 * t163
  t397 = 0.1e1 / t172
  t400 = t181 + t205 + t209 - t214 + t227 + t259 + t261 - t266 - t271 + (t274 - t286 - t294 - t296 * t282 * params.omega * t302 * t304 / 0.32e2) * t110 * t112 * t174 + 0.3e1 * t313 * t314 * t324 + t313 * t124 * (params.beta * t380 * t170 - t383 * t386 * (t137 * t146 * t380 - t340 * t387 * t357)) * t397
  vrho_0_ = t7 * t400 + t175 - t31 + t84 + t86
  t402 = -t39 - t215
  t405 = f.my_piecewise3(t42, 0, 0.4e1 / 0.3e1 * t45 * t402)
  t406 = -t402
  t409 = f.my_piecewise3(t49, 0, 0.4e1 / 0.3e1 * t50 * t406)
  t411 = (t405 + t409) * t57
  t413 = t38 * t411 * t82
  t415 = 0.58482236226346462072622386637590534819724553404281e0 * t411 * t80
  t418 = f.my_piecewise3(t103, -0.2e1 * t215 - 0.2e1 * t299, 0)
  t430 = f.my_piecewise3(t42, 0, 0.2e1 / 0.3e1 * t315 * t402)
  t433 = f.my_piecewise3(t49, 0, 0.2e1 / 0.3e1 * t319 * t406)
  t435 = t430 / 0.2e1 + t433 / 0.2e1
  t450 = (-(t181 + t205 - t209 - t214 + t413 + t259 + t415 - t266 - t271) * t136 * t141 + 0.3e1 * t139 * t352 * t435) * t143
  t459 = -t333 - t335 * t96 * t5 * t435 / 0.48e2 - t345 * t347 * t348 * t450 / 0.3072e4 - t368 - t371 * t375 * t348 * t435 / 0.768e3
  t473 = t181 + t205 - t209 - t214 + t413 + t259 + t415 - t266 - t271 + (t274 - t286 - t294 - t296 * t282 * params.omega * t418 * t304 / 0.32e2) * t110 * t112 * t174 + 0.3e1 * t313 * t314 * t435 + t313 * t124 * (params.beta * t459 * t170 - t383 * t386 * (t137 * t146 * t459 - t340 * t387 * t450)) * t397
  vrho_1_ = t7 * t473 + t175 - t31 + t84 + t86
  t481 = params.alpha * t89 * t295 * t99 * t106 * t110 * t112 * t174
  t485 = t127 * t54 * t130 * t291
  t489 = t137 * t146 * t88 * t160
  t491 = t485 / 0.96e2 + t489 / 0.1536e4
  t494 = params.beta ** 2
  t496 = t112 ** 2
  t498 = t494 * t163 / t496
  t499 = t114 ** 2
  t500 = t499 * t385
  vsigma_0_ = t7 * (-0.3e1 / 0.32e2 * t481 + t313 * t124 * (-t498 * t500 * t145 * t491 + params.beta * t491 * t170) * t397)
  t512 = t485 / 0.48e2 + t489 / 0.768e3
  vsigma_1_ = t7 * (-0.3e1 / 0.16e2 * t481 + t313 * t124 * (-t498 * t500 * t145 * t512 + params.beta * t512 * t170) * t397)
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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
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
  params_omega_raw = params.omega
  if isinstance(params_omega_raw, (str, bytes, dict)):
    params_omega = params_omega_raw
  else:
    try:
      params_omega_seq = list(params_omega_raw)
    except TypeError:
      params_omega = params_omega_raw
    else:
      params_omega_seq = np.asarray(params_omega_seq, dtype=np.float64)
      params_omega = np.concatenate((np.array([np.nan], dtype=np.float64), params_omega_seq))

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  mbeta = lambda rs=None, t=None: params_beta

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  zvpbeint_nu = lambda rs, z, t: t * f.mphi(z) * (3 / rs) ** (1 / 6)

  mgamma = params_gamma

  BB = params_BB

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  zvpbeint_ff = lambda rs, z, t: jnp.exp(-params_alpha * zvpbeint_nu(rs, z, t) ** 3 * jnp.maximum(z ** 2, 1e-20) ** (params_omega / 2))

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  functional_body = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + zvpbeint_ff(rs, z, tp(rs, z, xt)) * fH(rs, z, tp(rs, z, xt))

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
  t55 = jnp.sqrt(s0)
  t57 = params.alpha * t55 * s0
  t58 = r0 ** 2
  t59 = t58 ** 2
  t60 = 0.1e1 / t59
  t63 = 0.1e1 / t13 / t10
  t64 = 0.1e1 / t3
  t65 = t18 * t64
  t68 = jnp.sqrt(t65 * t5 * t7)
  t71 = f.my_piecewise3(0.1e-19 < 0.0e0, 0, 0.1e-19)
  t73 = t71 ** (params.omega / 0.2e1)
  t74 = t63 * t68 * t73
  t77 = jnp.exp(-t57 * t60 * t74 / 0.16e2)
  t78 = jnp.log(0.2e1)
  t79 = 0.1e1 - t78
  t80 = t77 * t79
  t81 = jnp.pi ** 2
  t82 = 0.1e1 / t81
  t83 = t32 ** 2
  t84 = f.my_piecewise3(t31, t83, 1)
  t85 = t84 ** 2
  t86 = t85 * t84
  t89 = 0.1e1 / t7 / t58
  t92 = 0.1e1 / t85
  t95 = t92 * t18 * t64 * t5
  t98 = 0.1e1 / t79
  t99 = params.beta * t98
  t102 = 0.1e1 / t86
  t105 = jnp.exp(-(-t30 + t54) * t98 * t81 * t102)
  t106 = t105 - 0.1e1
  t107 = 0.1e1 / t106
  t108 = t81 * t107
  t109 = s0 ** 2
  t111 = t99 * t108 * t109
  t113 = 0.1e1 / t21 / t59
  t114 = t37 ** 2
  t116 = t85 ** 2
  t117 = 0.1e1 / t116
  t119 = 0.1e1 / t19
  t121 = t1 * t119 * t6
  t122 = t113 * t114 * t117 * t121
  t125 = s0 * t89 * t37 * t95 / 0.96e2 + t111 * t122 / 0.3072e4
  t126 = params.beta * t125
  t130 = t99 * t108 * t125 + 0.1e1
  t132 = t98 * t81 / t130
  t134 = t126 * t132 + 0.1e1
  t135 = jnp.log(t134)
  t136 = t82 * t86 * t135
  t139 = 0.1e1 / t7 / r0
  t140 = t6 * t139
  t143 = 0.11073470983333333333333333333333333333333333333333e-2 * t4 * t140 * t29
  t144 = t26 ** 2
  t149 = t3 * t6
  t150 = t149 * t139
  t151 = 0.1e1 / t13 * t1 * t150
  t153 = t4 * t140
  t155 = t10 ** 0.5e0
  t157 = t155 * t1 * t150
  t162 = t20 * t5 / t21 / r0
  t167 = t12 / t144 * (-0.39359271665000000000000000000000000000000000000000e-1 * t151 - 0.18590165886666666666666666666666666666666666666667e-1 * t153 - 0.63665980925000000000000000000000000000000000000000e-2 * t157 - 0.51086165526666666666666666666666666666666666666667e-2 * t162) / t28
  t172 = 0.18311447306006545054854346104378990962041954983034e-3 * t41 * t1 * t149 * t139 * t51
  t174 = t48 ** 2
  t185 = 0.58482236226346462072622386637590534819724553404281e0 * t41 * t43 / t174 * (-0.29149603883333333333333333333333333333333333333333e-1 * t151 - 0.10197154565000000000000000000000000000000000000000e-1 * t153 - 0.18581078242500000000000000000000000000000000000000e-2 * t157 - 0.27959640330000000000000000000000000000000000000000e-2 * t162) / t50
  t186 = t59 * r0
  t207 = t65 * t5
  t215 = t80 * t82
  t223 = t79 ** 2
  t224 = 0.1e1 / t223
  t225 = params.beta * t224
  t226 = t81 ** 2
  t228 = t106 ** 2
  t229 = 0.1e1 / t228
  t238 = t143 + t167 - t172 - t185
  t251 = -0.7e1 / 0.288e3 * s0 / t7 / t58 / r0 * t37 * t95 + t225 * t226 * t229 * t109 * t113 * t114 / t116 / t86 * t1 * t119 * t6 * t238 * t105 / 0.3072e4 - 0.7e1 / 0.4608e4 * t111 / t21 / t186 * t114 * t117 * t121
  t255 = t130 ** 2
  t256 = 0.1e1 / t255
  t271 = 0.1e1 / t134
  vrho_0_ = -t30 + t54 + t80 * t136 + r0 * (t143 + t167 - t172 - t185 + (t57 / t186 * t74 / 0.4e1 - t57 / t7 / t186 / t13 / t24 * t68 * t73 * t4 * t6 / 0.128e3 - t57 * t113 * t63 / t68 * t73 * t207 / 0.96e2) * t77 * t79 * t136 + t215 * t86 * (params.beta * t251 * t132 - t126 * t98 * t81 * t256 * (t225 * t226 * t229 * t125 * t238 * t102 * t105 + t99 * t108 * t251)) * t271)
  t293 = t89 * t37 * t92 * t207 / 0.96e2 + t99 * t108 * s0 * t122 / 0.1536e4
  t296 = params.beta ** 2
  vsigma_0_ = r0 * (-0.3e1 / 0.32e2 * params.alpha * t55 * t60 * t63 * t68 * t73 * t77 * t79 * t136 + t215 * t86 * (-t296 * t125 * t224 * t226 * t256 * t107 * t293 + params.beta * t293 * t132) * t271)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t9 = 0.1e1 / t7 / r0
  t10 = t6 * t9
  t13 = t4 * t6 / t7
  t14 = jnp.sqrt(t13)
  t17 = t13 ** 0.15e1
  t19 = t1 ** 2
  t20 = t3 ** 2
  t21 = t19 * t20
  t22 = t7 ** 2
  t25 = t21 * t5 / t22
  t27 = 0.37978500000000000000000000000000000000000000000000e1 * t14 + 0.89690000000000000000000000000000000000000000000000e0 * t13 + 0.20477500000000000000000000000000000000000000000000e0 * t17 + 0.12323500000000000000000000000000000000000000000000e0 * t25
  t30 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t27
  t31 = jnp.log(t30)
  t33 = t4 * t10 * t31
  t36 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t13
  t37 = t27 ** 2
  t38 = 0.1e1 / t37
  t39 = t36 * t38
  t41 = 0.1e1 / t14 * t1
  t42 = t3 * t6
  t43 = t42 * t9
  t44 = t41 * t43
  t46 = t4 * t10
  t48 = t13 ** 0.5e0
  t49 = t48 * t1
  t50 = t49 * t43
  t55 = t21 * t5 / t22 / r0
  t57 = -0.63297500000000000000000000000000000000000000000000e0 * t44 - 0.29896666666666666666666666666666666666666666666667e0 * t46 - 0.10238750000000000000000000000000000000000000000000e0 * t50 - 0.82156666666666666666666666666666666666666666666667e-1 * t55
  t58 = 0.1e1 / t30
  t59 = t57 * t58
  t60 = t39 * t59
  t62 = 0.1e1 <= f.p.zeta_threshold
  t63 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t65 = f.my_piecewise3(t62, t63 * f.p.zeta_threshold, 1)
  t68 = 2 ** (0.1e1 / 0.3e1)
  t72 = (0.2e1 * t65 - 0.2e1) / (0.2e1 * t68 - 0.2e1)
  t73 = t72 * t1
  t78 = 0.51785000000000000000000000000000000000000000000000e1 * t14 + 0.90577500000000000000000000000000000000000000000000e0 * t13 + 0.11003250000000000000000000000000000000000000000000e0 * t17 + 0.12417750000000000000000000000000000000000000000000e0 * t25
  t81 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t78
  t82 = jnp.log(t81)
  t85 = t73 * t42 * t9 * t82
  t88 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t13
  t89 = t72 * t88
  t90 = t78 ** 2
  t91 = 0.1e1 / t90
  t96 = -0.86308333333333333333333333333333333333333333333334e0 * t44 - 0.30192500000000000000000000000000000000000000000000e0 * t46 - 0.55016250000000000000000000000000000000000000000000e-1 * t50 - 0.82785000000000000000000000000000000000000000000000e-1 * t55
  t98 = 0.1e1 / t81
  t99 = t91 * t96 * t98
  t100 = t89 * t99
  t102 = jnp.sqrt(s0)
  t104 = params.alpha * t102 * s0
  t105 = r0 ** 2
  t106 = t105 ** 2
  t107 = t106 * r0
  t108 = 0.1e1 / t107
  t111 = 0.1e1 / t14 / t13
  t112 = 0.1e1 / t3
  t113 = t19 * t112
  t115 = t113 * t5 * t7
  t116 = jnp.sqrt(t115)
  t119 = f.my_piecewise3(0.1e-19 < 0.0e0, 0, 0.1e-19)
  t121 = t119 ** (params.omega / 0.2e1)
  t122 = t111 * t116 * t121
  t126 = 0.1e1 / t7 / t107
  t129 = 0.1e1 / t14 / t25 / 0.4e1
  t132 = t116 * t121
  t133 = t4 * t6
  t134 = t132 * t133
  t138 = 0.1e1 / t22 / t106
  t141 = 0.1e1 / t116
  t143 = t113 * t5
  t144 = t141 * t121 * t143
  t147 = t104 * t108 * t122 / 0.4e1 - t104 * t126 * t129 * t134 / 0.32e2 - t104 * t138 * t111 * t144 / 0.96e2
  t148 = 0.1e1 / t106
  t152 = jnp.exp(-t104 * t148 * t122 / 0.16e2)
  t154 = jnp.log(0.2e1)
  t155 = 0.1e1 - t154
  t156 = t147 * t152 * t155
  t157 = jnp.pi ** 2
  t158 = 0.1e1 / t157
  t159 = t63 ** 2
  t160 = f.my_piecewise3(t62, t159, 1)
  t161 = t160 ** 2
  t162 = t161 * t160
  t163 = t158 * t162
  t165 = 0.1e1 / t7 / t105
  t168 = 0.1e1 / t161
  t170 = t112 * t5
  t171 = t168 * t19 * t170
  t174 = 0.1e1 / t155
  t175 = params.beta * t174
  t183 = 0.1e1 / t162
  t186 = jnp.exp(-(-0.621814e-1 * t36 * t31 + 0.19751673498613801407483339618206552048944131217655e-1 * t72 * t88 * t82) * t174 * t157 * t183)
  t187 = t186 - 0.1e1
  t188 = 0.1e1 / t187
  t189 = t157 * t188
  t190 = s0 ** 2
  t192 = t175 * t189 * t190
  t193 = t68 ** 2
  t195 = t161 ** 2
  t196 = 0.1e1 / t195
  t198 = 0.1e1 / t20
  t200 = t1 * t198 * t6
  t201 = t138 * t193 * t196 * t200
  t204 = s0 * t165 * t68 * t171 / 0.96e2 + t192 * t201 / 0.3072e4
  t205 = params.beta * t204
  t209 = t175 * t189 * t204 + 0.1e1
  t210 = 0.1e1 / t209
  t211 = t174 * t157 * t210
  t213 = t205 * t211 + 0.1e1
  t214 = jnp.log(t213)
  t215 = t163 * t214
  t216 = t156 * t215
  t219 = t152 * t155 * t158
  t222 = 0.1e1 / t7 / t105 / r0
  t227 = t155 ** 2
  t228 = 0.1e1 / t227
  t229 = params.beta * t228
  t230 = t157 ** 2
  t231 = t229 * t230
  t232 = t187 ** 2
  t233 = 0.1e1 / t232
  t234 = t233 * t190
  t235 = t234 * t138
  t236 = t231 * t235
  t240 = t193 / t195 / t162 * t1
  t241 = t198 * t6
  t246 = 0.11073470983333333333333333333333333333333333333333e-2 * t33 + 0.10000000000000000000000000000000000000000000000000e1 * t60 - 0.18311447306006545054854346104378990962041954983034e-3 * t85 - 0.58482236226346462072622386637590534819724553404280e0 * t100
  t249 = t240 * t241 * t246 * t186
  t253 = 0.1e1 / t22 / t107
  t256 = t253 * t193 * t196 * t200
  t259 = -0.7e1 / 0.288e3 * s0 * t222 * t68 * t171 + t236 * t249 / 0.3072e4 - 0.7e1 / 0.4608e4 * t192 * t256
  t260 = params.beta * t259
  t262 = t205 * t174
  t263 = t209 ** 2
  t264 = 0.1e1 / t263
  t265 = t157 * t264
  t267 = t229 * t230 * t233
  t269 = t183 * t186
  t274 = t267 * t204 * t246 * t269 + t175 * t189 * t259
  t275 = t265 * t274
  t277 = t260 * t211 - t262 * t275
  t279 = 0.1e1 / t213
  t281 = t219 * t162 * t277 * t279
  t283 = t6 * t165
  t286 = 0.14764627977777777777777777777777777777777777777777e-2 * t4 * t283 * t31
  t290 = 0.35616666666666666666666666666666666666666666666666e-1 * t133 * t9 * t38 * t59
  t294 = t57 ** 2
  t297 = 0.20000000000000000000000000000000000000000000000000e1 * t36 / t37 / t27 * t294 * t58
  t301 = 0.1e1 / t22 / t105
  t302 = t20 * t5 * t301
  t303 = t111 * t19 * t302
  t305 = t42 * t165
  t306 = t41 * t305
  t308 = t4 * t283
  t310 = t13 ** (-0.5e0)
  t312 = t310 * t19 * t302
  t314 = t49 * t305
  t317 = t21 * t5 * t301
  t322 = 0.10000000000000000000000000000000000000000000000000e1 * t39 * (-0.42198333333333333333333333333333333333333333333333e0 * t303 + 0.84396666666666666666666666666666666666666666666666e0 * t306 + 0.39862222222222222222222222222222222222222222222223e0 * t308 + 0.68258333333333333333333333333333333333333333333333e-1 * t312 + 0.13651666666666666666666666666666666666666666666667e0 * t314 + 0.13692777777777777777777777777777777777777777777778e0 * t317) * t58
  t323 = t37 ** 2
  t326 = t30 ** 2
  t330 = 0.16081979498692535066756296899072713062105388428051e2 * t36 / t323 * t294 / t326
  t334 = 0.24415263074675393406472461472505321282722606644045e-3 * t73 * t42 * t165 * t82
  t338 = 0.10843581300301739842632067522386578331157260943710e-1 * t72 * t4 * t10 * t99
  t341 = t96 ** 2
  t345 = 0.11696447245269292414524477327518106963944910680856e1 * t89 / t90 / t78 * t341 * t98
  t356 = 0.58482236226346462072622386637590534819724553404280e0 * t89 * t91 * (-0.57538888888888888888888888888888888888888888888889e0 * t303 + 0.11507777777777777777777777777777777777777777777778e1 * t306 + 0.40256666666666666666666666666666666666666666666667e0 * t308 + 0.36677500000000000000000000000000000000000000000000e-1 * t312 + 0.73355000000000000000000000000000000000000000000000e-1 * t314 + 0.13797500000000000000000000000000000000000000000000e0 * t317) * t98
  t357 = t90 ** 2
  t360 = t81 ** 2
  t364 = 0.17315859105681463759666483083807725165579399831905e2 * t89 / t357 * t341 / t360
  t365 = t106 * t105
  t367 = t104 / t365
  t381 = 0.1e1 / t22 / t365
  t409 = t147 ** 2
  t424 = 0.1e1 / t227 / t155
  t425 = params.beta * t424
  t426 = t230 * t157
  t427 = t425 * t426
  t429 = 0.1e1 / t232 / t187
  t433 = t195 ** 2
  t437 = t193 / t433 / t161 * t1
  t438 = t246 ** 2
  t439 = t186 ** 2
  t449 = -t286 - t290 - t297 + t322 + t330 + t334 + t338 + t345 - t356 - t364
  t466 = 0.35e2 / 0.432e3 * s0 / t7 / t106 * t68 * t171 + t427 * t429 * t190 * t138 * t437 * t241 * t438 * t439 / 0.1536e4 - 0.7e1 / 0.2304e4 * t231 * t234 * t253 * t249 + t236 * t240 * t241 * t449 * t186 / 0.3072e4 - t427 * t235 * t437 * t241 * t438 * t186 / 0.3072e4 + 0.119e3 / 0.13824e5 * t192 * t381 * t193 * t196 * t200
  t473 = 0.1e1 / t263 / t209
  t475 = t274 ** 2
  t481 = t204 * t438
  t483 = 0.1e1 / t195 / t161
  t509 = t277 ** 2
  t511 = t213 ** 2
  t512 = 0.1e1 / t511
  t515 = -t286 - t290 - t297 + t322 + t330 + t334 + t338 + t345 - t356 - t364 + (-0.5e1 / 0.4e1 * t367 * t122 + 0.7e1 / 0.24e2 * t104 / t7 / t365 * t129 * t134 + 0.13e2 / 0.144e3 * t104 * t253 * t111 * t144 - 0.5e1 / 0.2304e4 * t104 * t381 / t14 / t2 * r0 * t132 * t21 * t5 - t367 * t129 * t141 * t121 / 0.8e1 + t104 * t126 * t111 / t116 / t115 * t121 * t200 / 0.192e3) * t152 * t155 * t215 + t409 * t152 * t155 * t215 + 0.2e1 * t156 * t163 * t277 * t279 + t219 * t162 * (params.beta * t466 * t211 - 0.2e1 * t260 * t174 * t275 + 0.2e1 * t262 * t157 * t473 * t475 - t262 * t265 * (-t425 * t426 * t233 * t481 * t483 * t186 + 0.2e1 * t425 * t426 * t429 * t481 * t483 * t439 + t267 * t204 * t449 * t269 + 0.2e1 * t267 * t259 * t246 * t269 + t175 * t189 * t466)) * t279 - t219 * t162 * t509 * t512
  v2rho2_0_ = 0.22146941966666666666666666666666666666666666666666e-2 * t33 + 0.20000000000000000000000000000000000000000000000000e1 * t60 - 0.36622894612013090109708692208757981924083909966068e-3 * t85 - 0.11696447245269292414524477327518106963944910680856e1 * t100 + 0.2e1 * t216 + 0.2e1 * t281 + r0 * t515
  t517 = params.alpha * t102
  t519 = t148 * t111 * t116
  t521 = t121 * t152
  t523 = t521 * t155 * t215
  t531 = t175 * t189 * s0
  t534 = t165 * t68 * t168 * t143 / 0.96e2 + t531 * t201 / 0.1536e4
  t535 = params.beta * t534
  t537 = params.beta ** 2
  t538 = t537 * t204
  t539 = t538 * t228
  t540 = t230 * t264
  t542 = t540 * t188 * t534
  t544 = t535 * t211 - t539 * t542
  t545 = t162 * t544
  t547 = t219 * t545 * t279
  t558 = t155 * t158 * t162
  t574 = t517 * t148 * t122
  t593 = -0.7e1 / 0.288e3 * t222 * t68 * t168 * t143 + t231 * t233 * s0 * t138 * t249 / 0.1536e4 - 0.7e1 / 0.2304e4 * t531 * t256
  v2rhosigma_0_ = -0.3e1 / 0.32e2 * t517 * t519 * t523 + t547 + r0 * (0.3e1 / 0.8e1 * t517 * t108 * t111 * t116 * t523 - 0.3e1 / 0.64e2 * t517 * t126 * t129 * t116 * t521 * t558 * t214 * t1 * t42 - t517 * t138 * t111 * t141 * t521 * t558 * t214 * t19 * t170 / 0.64e2 - 0.3e1 / 0.32e2 * t574 * t216 - 0.3e1 / 0.32e2 * t574 * t281 + t156 * t163 * t544 * t279 + t219 * t162 * (-t538 * t424 * t426 * t264 * t233 * t534 * t246 * t183 * t186 + 0.2e1 * t538 * t228 * t230 * t473 * t188 * t534 * t274 - t539 * t540 * t188 * t593 - t537 * t259 * t228 * t542 - t535 * t174 * t275 + params.beta * t593 * t211) * t279 - t219 * t545 * t512 * t277)
  t633 = params.alpha ** 2
  t639 = t121 ** 2
  t659 = t534 ** 2
  t667 = t537 * params.beta * t204 * t424
  t682 = t544 ** 2
  v2sigma2_0_ = r0 * (-0.3e1 / 0.64e2 * params.alpha / t102 * t519 * t523 + 0.3e1 / 0.16384e5 * t633 * s0 * t381 * t2 * t19 * t112 * t5 * t639 * t152 * t155 * t162 * t214 - 0.3e1 / 0.16e2 * t574 * t547 + t219 * t162 * (t537 * t228 * t230 * t188 * t138 * t193 * t196 * t1 * t241 * t210 / 0.1536e4 - 0.2e1 * t537 * t659 * t228 * t540 * t188 + 0.2e1 * t667 * t426 * t473 * t233 * t659 - t667 * t426 * t264 * t233 * t201 / 0.1536e4) * t279 - t219 * t162 * t682 * t512)
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t10 = t4 * t6 / t7
  t12 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t10
  t13 = jnp.sqrt(t10)
  t16 = t10 ** 0.15e1
  t18 = t1 ** 2
  t19 = t3 ** 2
  t20 = t18 * t19
  t21 = t7 ** 2
  t24 = t20 * t5 / t21
  t26 = 0.37978500000000000000000000000000000000000000000000e1 * t13 + 0.89690000000000000000000000000000000000000000000000e0 * t10 + 0.20477500000000000000000000000000000000000000000000e0 * t16 + 0.12323500000000000000000000000000000000000000000000e0 * t24
  t27 = t26 ** 2
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = t12 * t29
  t32 = 0.1e1 / t13 * t1
  t33 = t3 * t6
  t35 = 0.1e1 / t7 / r0
  t36 = t33 * t35
  t37 = t32 * t36
  t39 = t6 * t35
  t40 = t4 * t39
  t42 = t10 ** 0.5e0
  t43 = t42 * t1
  t44 = t43 * t36
  t49 = t20 * t5 / t21 / r0
  t51 = -0.63297500000000000000000000000000000000000000000000e0 * t37 - 0.29896666666666666666666666666666666666666666666667e0 * t40 - 0.10238750000000000000000000000000000000000000000000e0 * t44 - 0.82156666666666666666666666666666666666666666666667e-1 * t49
  t52 = t51 ** 2
  t55 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t26
  t56 = t55 ** 2
  t57 = 0.1e1 / t56
  t58 = t52 * t57
  t59 = t30 * t58
  t62 = 0.1e1 / t27 / t26
  t63 = t12 * t62
  t64 = 0.1e1 / t55
  t65 = t52 * t64
  t66 = t63 * t65
  t68 = 0.1e1 / t27
  t69 = t12 * t68
  t71 = 0.1e1 / t13 / t10
  t72 = t71 * t18
  t73 = t19 * t5
  t74 = r0 ** 2
  t76 = 0.1e1 / t21 / t74
  t77 = t73 * t76
  t78 = t72 * t77
  t81 = 0.1e1 / t7 / t74
  t82 = t33 * t81
  t83 = t32 * t82
  t85 = t6 * t81
  t86 = t4 * t85
  t88 = t10 ** (-0.5e0)
  t89 = t88 * t18
  t90 = t89 * t77
  t92 = t43 * t82
  t95 = t20 * t5 * t76
  t97 = -0.42198333333333333333333333333333333333333333333333e0 * t78 + 0.84396666666666666666666666666666666666666666666666e0 * t83 + 0.39862222222222222222222222222222222222222222222223e0 * t86 + 0.68258333333333333333333333333333333333333333333333e-1 * t90 + 0.13651666666666666666666666666666666666666666666667e0 * t92 + 0.13692777777777777777777777777777777777777777777778e0 * t95
  t98 = t97 * t64
  t99 = t69 * t98
  t101 = jnp.log(t55)
  t103 = t4 * t85 * t101
  t105 = 0.1e1 <= f.p.zeta_threshold
  t106 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t108 = f.my_piecewise3(t105, t106 * f.p.zeta_threshold, 1)
  t111 = 2 ** (0.1e1 / 0.3e1)
  t115 = (0.2e1 * t108 - 0.2e1) / (0.2e1 * t111 - 0.2e1)
  t117 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t10
  t118 = t115 * t117
  t123 = 0.51785000000000000000000000000000000000000000000000e1 * t13 + 0.90577500000000000000000000000000000000000000000000e0 * t10 + 0.11003250000000000000000000000000000000000000000000e0 * t16 + 0.12417750000000000000000000000000000000000000000000e0 * t24
  t124 = t123 ** 2
  t126 = 0.1e1 / t124 / t123
  t131 = -0.86308333333333333333333333333333333333333333333334e0 * t37 - 0.30192500000000000000000000000000000000000000000000e0 * t40 - 0.55016250000000000000000000000000000000000000000000e-1 * t44 - 0.82785000000000000000000000000000000000000000000000e-1 * t49
  t132 = t131 ** 2
  t136 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t123
  t137 = 0.1e1 / t136
  t138 = t126 * t132 * t137
  t139 = t118 * t138
  t141 = 0.1e1 / t124
  t148 = -0.57538888888888888888888888888888888888888888888889e0 * t78 + 0.11507777777777777777777777777777777777777777777778e1 * t83 + 0.40256666666666666666666666666666666666666666666667e0 * t86 + 0.36677500000000000000000000000000000000000000000000e-1 * t90 + 0.73355000000000000000000000000000000000000000000000e-1 * t92 + 0.13797500000000000000000000000000000000000000000000e0 * t95
  t150 = t141 * t148 * t137
  t151 = t118 * t150
  t153 = t124 ** 2
  t154 = 0.1e1 / t153
  t156 = t136 ** 2
  t157 = 0.1e1 / t156
  t158 = t154 * t132 * t157
  t159 = t118 * t158
  t161 = jnp.sqrt(s0)
  t163 = params.alpha * t161 * s0
  t164 = t74 ** 2
  t165 = t164 * t74
  t167 = t163 / t165
  t168 = 0.1e1 / t3
  t169 = t18 * t168
  t171 = t169 * t5 * t7
  t172 = jnp.sqrt(t171)
  t175 = f.my_piecewise3(0.1e-19 < 0.0e0, 0, 0.1e-19)
  t177 = t175 ** (params.omega / 0.2e1)
  t178 = t71 * t172 * t177
  t182 = 0.1e1 / t7 / t165
  t185 = 0.1e1 / t13 / t24 / 0.4e1
  t188 = t172 * t177
  t189 = t4 * t6
  t190 = t188 * t189
  t193 = t164 * r0
  t195 = 0.1e1 / t21 / t193
  t198 = 0.1e1 / t172
  t199 = t198 * t177
  t200 = t169 * t5
  t201 = t199 * t200
  t205 = 0.1e1 / t21 / t165
  t210 = 0.1e1 / t13 / t2 * r0 / 0.48e2
  t214 = t188 * t20 * t5
  t218 = t185 * t198 * t177
  t222 = 0.1e1 / t7 / t193
  t227 = 0.1e1 / t172 / t171 * t177
  t228 = 0.1e1 / t19
  t229 = t1 * t228
  t230 = t229 * t6
  t231 = t227 * t230
  t234 = -0.5e1 / 0.4e1 * t167 * t178 + 0.7e1 / 0.24e2 * t163 * t182 * t185 * t190 + 0.13e2 / 0.144e3 * t163 * t195 * t71 * t201 - 0.5e1 / 0.48e2 * t163 * t205 * t210 * t214 - t167 * t218 / 0.8e1 + t163 * t222 * t71 * t231 / 0.192e3
  t235 = 0.1e1 / t164
  t239 = jnp.exp(-t163 * t235 * t178 / 0.16e2)
  t241 = jnp.log(0.2e1)
  t242 = 0.1e1 - t241
  t243 = t234 * t239 * t242
  t244 = jnp.pi ** 2
  t245 = 0.1e1 / t244
  t246 = t106 ** 2
  t247 = f.my_piecewise3(t105, t246, 1)
  t248 = t247 ** 2
  t249 = t248 * t247
  t250 = t245 * t249
  t256 = 0.1e1 / t248 * t18 * t168 * t5
  t259 = 0.1e1 / t242
  t260 = params.beta * t259
  t263 = jnp.log(t136)
  t269 = 0.1e1 / t249
  t272 = jnp.exp(-(-0.621814e-1 * t12 * t101 + 0.19751673498613801407483339618206552048944131217655e-1 * t115 * t117 * t263) * t259 * t244 * t269)
  t273 = t272 - 0.1e1
  t275 = t244 / t273
  t276 = s0 ** 2
  t278 = t260 * t275 * t276
  t280 = 0.1e1 / t21 / t164
  t281 = t111 ** 2
  t282 = t280 * t281
  t283 = t248 ** 2
  t284 = 0.1e1 / t283
  t289 = s0 * t81 * t111 * t256 / 0.96e2 + t278 * t282 * t284 * t230 / 0.3072e4
  t290 = params.beta * t289
  t294 = t260 * t275 * t289 + 0.1e1
  t296 = t259 * t244 / t294
  t298 = t290 * t296 + 0.1e1
  t299 = jnp.log(t298)
  t300 = t250 * t299
  t315 = t163 / t193 * t178 / 0.4e1 - t163 * t222 * t185 * t190 / 0.32e2 - t163 * t280 * t71 * t201 / 0.96e2
  t316 = t315 ** 2
  t318 = t316 * t239 * t242
  t322 = t239 * t242 * t245
  t323 = t74 * r0
  t325 = 0.1e1 / t7 / t323
  t330 = t242 ** 2
  t332 = params.beta / t330
  t333 = t244 ** 2
  t334 = t332 * t333
  t335 = t273 ** 2
  t336 = 0.1e1 / t335
  t337 = t336 * t276
  t338 = t337 * t280
  t339 = t334 * t338
  t343 = t281 / t283 / t249 * t1
  t344 = t228 * t6
  t348 = t51 * t64
  t351 = t115 * t1
  t357 = t141 * t131 * t137
  t360 = 0.11073470983333333333333333333333333333333333333333e-2 * t4 * t39 * t101 + 0.10000000000000000000000000000000000000000000000000e1 * t69 * t348 - 0.18311447306006545054854346104378990962041954983034e-3 * t351 * t33 * t35 * t263 - 0.58482236226346462072622386637590534819724553404280e0 * t118 * t357
  t361 = t360 * t272
  t363 = t343 * t344 * t361
  t371 = -0.7e1 / 0.288e3 * s0 * t325 * t111 * t256 + t339 * t363 / 0.3072e4 - 0.7e1 / 0.4608e4 * t278 * t195 * t281 * t284 * t230
  t372 = params.beta * t371
  t374 = t290 * t259
  t375 = t294 ** 2
  t377 = t244 / t375
  t379 = t332 * t333 * t336
  t380 = t289 * t360
  t381 = t269 * t272
  t386 = t260 * t275 * t371 + t379 * t380 * t381
  t387 = t377 * t386
  t389 = t372 * t296 - t374 * t387
  t390 = t389 ** 2
  t392 = t298 ** 2
  t393 = 0.1e1 / t392
  t405 = params.beta / t330 / t242
  t406 = t333 * t244
  t407 = t405 * t406
  t409 = 0.1e1 / t335 / t273
  t410 = t409 * t276
  t411 = t410 * t280
  t413 = t283 ** 2
  t415 = 0.1e1 / t413 / t248
  t417 = t281 * t415 * t1
  t418 = t360 ** 2
  t419 = t272 ** 2
  t422 = t417 * t344 * t418 * t419
  t425 = t337 * t195
  t426 = t334 * t425
  t430 = t35 * t68
  t432 = t189 * t430 * t348
  t439 = t351 * t33 * t81 * t263
  t441 = t115 * t4
  t443 = t441 * t39 * t357
  t448 = -0.14764627977777777777777777777777777777777777777777e-2 * t103 - 0.35616666666666666666666666666666666666666666666666e-1 * t432 - 0.20000000000000000000000000000000000000000000000000e1 * t66 + 0.10000000000000000000000000000000000000000000000000e1 * t99 + 0.16081979498692535066756296899072713062105388428051e2 * t59 + 0.24415263074675393406472461472505321282722606644045e-3 * t439 + 0.10843581300301739842632067522386578331157260943710e-1 * t443 + 0.11696447245269292414524477327518106963944910680856e1 * t139 - 0.58482236226346462072622386637590534819724553404280e0 * t151 - 0.17315859105681463759666483083807725165579399831905e2 * t159
  t451 = t343 * t344 * t448 * t272
  t457 = t417 * t344 * t418 * t272
  t465 = 0.35e2 / 0.432e3 * s0 / t7 / t164 * t111 * t256 + t407 * t411 * t422 / 0.1536e4 - 0.7e1 / 0.2304e4 * t426 * t363 + t339 * t451 / 0.3072e4 - t407 * t338 * t457 / 0.3072e4 + 0.119e3 / 0.13824e5 * t278 * t205 * t281 * t284 * t230
  t466 = params.beta * t465
  t468 = t372 * t259
  t473 = t244 / t375 / t294
  t474 = t386 ** 2
  t475 = t473 * t474
  t479 = t405 * t406 * t409
  t480 = t289 * t418
  t482 = 0.1e1 / t283 / t248
  t483 = t482 * t419
  t491 = t289 * t448
  t495 = t405 * t406 * t336
  t496 = t482 * t272
  t501 = 0.2e1 * t379 * t371 * t360 * t381 + t260 * t275 * t465 + t379 * t491 * t381 + 0.2e1 * t479 * t480 * t483 - t495 * t480 * t496
  t502 = t377 * t501
  t504 = t466 * t296 + 0.2e1 * t374 * t475 - t374 * t502 - 0.2e1 * t468 * t387
  t505 = t249 * t504
  t506 = 0.1e1 / t298
  t514 = t52 * t51
  t517 = 0.96491876992155210400537781394436278372632330568306e2 * t12 / t28 / t26 * t514 * t57
  t519 = t185 * t2 * t235
  t522 = 0.1e1 / t21 / t323
  t523 = t73 * t522
  t524 = t72 * t523
  t526 = t33 * t325
  t527 = t32 * t526
  t529 = t6 * t325
  t530 = t4 * t529
  t532 = t10 ** (-0.15e1)
  t534 = t532 * t2 * t235
  t536 = t89 * t523
  t538 = t43 * t526
  t541 = t20 * t5 * t522
  t546 = 0.10000000000000000000000000000000000000000000000000e1 * t69 * (-0.25319000000000000000000000000000000000000000000000e1 * t519 + 0.16879333333333333333333333333333333333333333333333e1 * t524 - 0.19692555555555555555555555555555555555555555555555e1 * t527 - 0.93011851851851851851851851851851851851851851851854e0 * t530 + 0.13651666666666666666666666666666666666666666666667e0 * t534 - 0.27303333333333333333333333333333333333333333333333e0 * t536 - 0.31853888888888888888888888888888888888888888888890e0 * t538 - 0.36514074074074074074074074074074074074074074074075e0 * t541) * t64
  t554 = 0.51726012919273400298984252201052768390886626637712e3 * t12 / t28 / t27 * t514 / t56 / t55
  t560 = t315 * t239 * t242
  t566 = t250 * t389 * t506
  t577 = 0.35089341735807877243573431982554320891834732042568e1 * t118 * t126 * t131 * t137 * t148
  t581 = 0.71233333333333333333333333333333333333333333333331e-1 * t189 * t81 * t68 * t348
  t584 = 0.53424999999999999999999999999999999999999999999999e-1 * t189 * t430 * t98
  t588 = 0.85917975471764868594145516183295969534298037676861e0 * t189 * t35 * t29 * t58
  t592 = 0.10685000000000000000000000000000000000000000000000e0 * t189 * t35 * t62 * t65
  t596 = 0.56968947174242584615102410102512416326352748836105e-3 * t351 * t33 * t325 * t263
  t601 = 0.51947577317044391278999449251423175496738199495715e2 * t118 * t154 * t148 * t157 * t131
  t611 = 0.60000000000000000000000000000000000000000000000000e1 * t63 * t348 * t97
  t612 = 0.3e1 * t234 * t315 * t239 * t242 * t245 * t249 * t299 - 0.3e1 * t560 * t250 * t390 * t393 + 0.3e1 * t560 * t250 * t504 * t506 - 0.3e1 * t322 * t505 * t393 * t389 + 0.3e1 * t243 * t566 - t517 + t546 + t554 + t577 + t581 - t584 - t588 + t592 - t596 - t601 - t611
  t615 = 0.34450798614814814814814814814814814814814814814813e-2 * t4 * t529 * t101
  t619 = 0.48245938496077605200268890697218139186316165284153e2 * t30 * t97 * t57 * t51
  t620 = t164 * t323
  t622 = t163 / t620
  t626 = 0.1e1 / t7 / t620
  t636 = 0.1e1 / t21 / t620
  t647 = t164 ** 2
  t693 = t330 ** 2
  t695 = params.beta / t693
  t696 = t333 ** 2
  t697 = t695 * t696
  t698 = t335 ** 2
  t699 = 0.1e1 / t698
  t707 = t281 / t413 / t283 / t247 * t1
  t708 = t418 * t360
  t709 = t419 * t272
  t722 = t415 * t1 * t228
  t746 = t132 * t131
  t752 = 0.10254018858216406658218194626490193680059335835414e4 * t118 / t153 / t124 * t746 / t156 / t136
  t758 = 0.10389515463408878255799889850284635099347639899143e3 * t118 / t153 / t123 * t746 * t157
  t771 = 0.58482236226346462072622386637590534819724553404280e0 * t118 * t141 * (-0.34523333333333333333333333333333333333333333333333e1 * t519 + 0.23015555555555555555555555555555555555555555555556e1 * t524 - 0.26851481481481481481481481481481481481481481481482e1 * t527 - 0.93932222222222222222222222222222222222222222222223e0 * t530 + 0.73355000000000000000000000000000000000000000000000e-1 * t534 - 0.14671000000000000000000000000000000000000000000000e0 * t536 - 0.17116166666666666666666666666666666666666666666667e0 * t538 - 0.36793333333333333333333333333333333333333333333333e0 * t541) * t137
  t774 = 0.32530743900905219527896202567159734993471782831130e-1 * t441 * t39 * t138
  t777 = 0.16265371950452609763948101283579867496735891415565e-1 * t441 * t39 * t150
  t780 = 0.48159733137676571081572406076840235616767705782485e0 * t441 * t39 * t158
  t783 = 0.21687162600603479685264135044773156662314521887420e-1 * t441 * t85 * t357
  t787 = 0.35089341735807877243573431982554320891834732042568e1 * t118 * t154 * t746 * t137
  t788 = -t752 + t758 - t771 - t774 + t777 + t780 - t783 - t601 - t787 + t577 + t581
  t791 = 0.60000000000000000000000000000000000000000000000000e1 * t30 * t514 * t64
  t792 = -t584 - t588 + t554 - t517 + t546 + t619 + t791 - t611 + t615 + t592 - t596
  t793 = t788 + t792
  t817 = -0.455e3 / 0.1296e4 * s0 * t222 * t111 * t256 + t697 * t699 * t276 * t280 * t707 * t344 * t708 * t709 / 0.512e3 - 0.7e1 / 0.768e3 * t407 * t410 * t195 * t422 + t407 * t410 * t282 * t722 * t6 * t360 * t419 * t448 / 0.512e3 - t697 * t411 * t707 * t344 * t708 * t419 / 0.512e3 + 0.119e3 / 0.4608e4 * t334 * t337 * t205 * t363 - 0.7e1 / 0.1536e4 * t426 * t451 + 0.7e1 / 0.1536e4 * t407 * t425 * t457 + t339 * t343 * t344 * t793 * t272 / 0.3072e4 - t407 * t337 * t282 * t722 * t6 * t448 * t361 / 0.1024e4 + t697 * t338 * t707 * t344 * t708 * t272 / 0.3072e4 - 0.595e3 / 0.10368e5 * t278 * t636 * t281 * t284 * t230
  t827 = t375 ** 2
  t840 = t289 * t708
  t842 = 0.1e1 / t413 / t247
  t847 = t371 * t418
  t887 = t695 * t696 * t336 * t840 * t842 * t272 - 0.6e1 * t695 * t696 * t409 * t840 * t842 * t419 + 0.6e1 * t695 * t696 * t699 * t840 * t842 * t709 - 0.3e1 * t495 * t491 * t482 * t360 * t272 + t379 * t289 * t793 * t381 + 0.3e1 * t379 * t465 * t360 * t381 + 0.3e1 * t379 * t371 * t448 * t381 + 0.6e1 * t479 * t380 * t483 * t448 + t260 * t275 * t817 + 0.6e1 * t479 * t847 * t483 - 0.3e1 * t495 * t847 * t496
  t903 = t615 + t619 + (0.15e2 / 0.2e1 * t622 * t178 - 0.89e2 / 0.36e2 * t163 * t626 * t185 * t190 - 0.311e3 / 0.432e3 * t163 * t205 * t71 * t201 + 0.5e1 / 0.3e1 * t163 * t636 * t210 * t214 + 0.15e2 / 0.8e1 * t622 * t218 - 0.7e1 / 0.96e2 * t163 * t182 * t71 * t231 - 0.35e2 / 0.1152e4 * t163 / t647 / t13 / t1 / t3 / t39 * t172 * t177 - 0.5e1 / 0.32e2 * t163 * t626 * t210 * t199 * t189 + t163 * t205 * t185 * t227 * t200 / 0.32e2 - t167 * t71 / t172 / t229 / t6 / t21 * t177 * jnp.pi / 0.96e2) * t239 * t242 * t300 + t316 * t315 * t239 * t242 * t300 + t322 * t249 * (params.beta * t817 * t296 - 0.3e1 * t466 * t259 * t387 + 0.6e1 * t468 * t475 - 0.3e1 * t468 * t502 - 0.6e1 * t374 * t244 / t827 * t474 * t386 + 0.6e1 * t374 * t473 * t386 * t501 - t374 * t377 * t887) * t506 - t771 - t787 + 0.2e1 * t322 * t249 * t390 * t389 / t392 / t298 - t752 + t758 - t774 + t777 + t780 - t783 + t791 + 0.3e1 * t318 * t566
  v3rho3_0_ = 0.48245938496077605200268890697218139186316165284153e2 * t59 - 0.60000000000000000000000000000000000000000000000000e1 * t66 + 0.30000000000000000000000000000000000000000000000000e1 * t99 - 0.44293883933333333333333333333333333333333333333332e-2 * t103 + 0.35089341735807877243573431982554320891834732042568e1 * t139 - 0.17544670867903938621786715991277160445917366021284e1 * t151 - 0.51947577317044391278999449251423175496738199495715e2 * t159 + 0.3e1 * t243 * t300 + 0.3e1 * t318 * t300 - 0.3e1 * t322 * t249 * t390 * t393 + 0.3e1 * t322 * t505 * t506 + 0.32530743900905219527896202567159734993471782831130e-1 * t443 + r0 * (t612 + t903) + 0.6e1 * t560 * t566 - 0.10685000000000000000000000000000000000000000000000e0 * t432 + 0.73245789224026180219417384417515963848167819932136e-3 * t439

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
  t16 = t11 * t15
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t19 = r0 ** (0.1e1 / 0.3e1)
  t21 = 0.1e1 / t19 / r0
  t22 = t18 * t21
  t25 = t15 * t18 / t19
  t26 = jnp.sqrt(t25)
  t29 = t25 ** 0.15e1
  t31 = t12 ** 2
  t32 = t14 ** 2
  t33 = t31 * t32
  t34 = t19 ** 2
  t37 = t33 * t17 / t34
  t39 = 0.51785000000000000000000000000000000000000000000000e1 * t26 + 0.90577500000000000000000000000000000000000000000000e0 * t25 + 0.11003250000000000000000000000000000000000000000000e0 * t29 + 0.12417750000000000000000000000000000000000000000000e0 * t37
  t40 = t39 ** 2
  t41 = t40 * t39
  t42 = 0.1e1 / t41
  t44 = 0.1e1 / t26 * t12
  t45 = t14 * t18
  t46 = t45 * t21
  t47 = t44 * t46
  t49 = t15 * t22
  t51 = t25 ** 0.5e0
  t52 = t51 * t12
  t53 = t52 * t46
  t57 = t17 / t34 / r0
  t58 = t33 * t57
  t60 = -0.86308333333333333333333333333333333333333333333334e0 * t47 - 0.30192500000000000000000000000000000000000000000000e0 * t49 - 0.55016250000000000000000000000000000000000000000000e-1 * t53 - 0.82785000000000000000000000000000000000000000000000e-1 * t58
  t61 = t60 ** 2
  t65 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t39
  t66 = 0.1e1 / t65
  t67 = t42 * t61 * t66
  t69 = t16 * t22 * t67
  t71 = 0.1e1 / t40
  t73 = 0.1e1 / t26 / t25
  t74 = t73 * t31
  t75 = t32 * t17
  t76 = r0 ** 2
  t78 = 0.1e1 / t34 / t76
  t79 = t75 * t78
  t80 = t74 * t79
  t83 = 0.1e1 / t19 / t76
  t84 = t45 * t83
  t85 = t44 * t84
  t87 = t18 * t83
  t88 = t15 * t87
  t90 = t25 ** (-0.5e0)
  t91 = t90 * t31
  t92 = t91 * t79
  t94 = t52 * t84
  t97 = t33 * t17 * t78
  t99 = -0.57538888888888888888888888888888888888888888888889e0 * t80 + 0.11507777777777777777777777777777777777777777777778e1 * t85 + 0.40256666666666666666666666666666666666666666666667e0 * t88 + 0.36677500000000000000000000000000000000000000000000e-1 * t92 + 0.73355000000000000000000000000000000000000000000000e-1 * t94 + 0.13797500000000000000000000000000000000000000000000e0 * t97
  t101 = t71 * t99 * t66
  t103 = t16 * t22 * t101
  t105 = t40 ** 2
  t106 = 0.1e1 / t105
  t107 = t106 * t61
  t108 = t65 ** 2
  t109 = 0.1e1 / t108
  t110 = t107 * t109
  t112 = t16 * t22 * t110
  t115 = t71 * t60 * t66
  t117 = t16 * t87 * t115
  t120 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t25
  t121 = t11 * t120
  t123 = t109 * t60
  t125 = t121 * t106 * t99 * t123
  t127 = t42 * t60
  t128 = t66 * t99
  t130 = t121 * t127 * t128
  t132 = t15 * t18
  t137 = 0.37978500000000000000000000000000000000000000000000e1 * t26 + 0.89690000000000000000000000000000000000000000000000e0 * t25 + 0.20477500000000000000000000000000000000000000000000e0 * t29 + 0.12323500000000000000000000000000000000000000000000e0 * t37
  t138 = t137 ** 2
  t139 = 0.1e1 / t138
  t140 = t83 * t139
  t145 = -0.63297500000000000000000000000000000000000000000000e0 * t47 - 0.29896666666666666666666666666666666666666666666667e0 * t49 - 0.10238750000000000000000000000000000000000000000000e0 * t53 - 0.82156666666666666666666666666666666666666666666667e-1 * t58
  t148 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t137
  t149 = 0.1e1 / t148
  t150 = t145 * t149
  t152 = t132 * t140 * t150
  t154 = t21 * t139
  t161 = -0.42198333333333333333333333333333333333333333333333e0 * t80 + 0.84396666666666666666666666666666666666666666666666e0 * t85 + 0.39862222222222222222222222222222222222222222222223e0 * t88 + 0.68258333333333333333333333333333333333333333333333e-1 * t92 + 0.13651666666666666666666666666666666666666666666667e0 * t94 + 0.13692777777777777777777777777777777777777777777778e0 * t97
  t162 = t161 * t149
  t164 = t132 * t154 * t162
  t166 = t138 ** 2
  t167 = 0.1e1 / t166
  t168 = t21 * t167
  t169 = t145 ** 2
  t170 = t148 ** 2
  t171 = 0.1e1 / t170
  t172 = t169 * t171
  t174 = t132 * t168 * t172
  t176 = t138 * t137
  t177 = 0.1e1 / t176
  t179 = t169 * t149
  t181 = t132 * t21 * t177 * t179
  t183 = t11 * t12
  t184 = t76 * r0
  t186 = 0.1e1 / t19 / t184
  t187 = jnp.log(t65)
  t190 = t183 * t45 * t186 * t187
  t192 = jnp.sqrt(s0)
  t194 = params.alpha * t192 * s0
  t195 = t76 ** 2
  t196 = t195 * r0
  t197 = 0.1e1 / t196
  t199 = 0.1e1 / t14
  t200 = t31 * t199
  t202 = t200 * t17 * t19
  t203 = jnp.sqrt(t202)
  t206 = f.my_piecewise3(0.1e-19 < 0.0e0, 0, 0.1e-19)
  t208 = t206 ** (params.omega / 0.2e1)
  t209 = t73 * t203 * t208
  t213 = 0.1e1 / t19 / t196
  t216 = 0.1e1 / t26 / t37 / 0.4e1
  t219 = t203 * t208
  t220 = t219 * t132
  t224 = 0.1e1 / t34 / t195
  t227 = 0.1e1 / t203
  t228 = t227 * t208
  t229 = t200 * t17
  t230 = t228 * t229
  t233 = t194 * t197 * t209 / 0.4e1 - t194 * t213 * t216 * t220 / 0.32e2 - t194 * t224 * t73 * t230 / 0.96e2
  t234 = 0.1e1 / t195
  t238 = jnp.exp(-t194 * t234 * t209 / 0.16e2)
  t239 = t233 * t238
  t240 = jnp.log(0.2e1)
  t241 = 0.1e1 - t240
  t242 = t239 * t241
  t243 = jnp.pi ** 2
  t244 = 0.1e1 / t243
  t245 = t2 ** 2
  t246 = f.my_piecewise3(t1, t245, 1)
  t247 = t246 ** 2
  t248 = t247 * t246
  t249 = t244 * t248
  t251 = 0.1e1 / t19 / t195
  t257 = 0.1e1 / t247 * t31 * t199 * t17
  t260 = t241 ** 2
  t263 = params.beta / t260 / t241
  t264 = t243 ** 2
  t265 = t264 * t243
  t266 = t263 * t265
  t268 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t25
  t269 = jnp.log(t148)
  t276 = 0.1e1 / t241
  t278 = 0.1e1 / t248
  t281 = jnp.exp(-(-0.621814e-1 * t268 * t269 + 0.19751673498613801407483339618206552048944131217655e-1 * t11 * t120 * t187) * t276 * t243 * t278)
  t282 = t281 - 0.1e1
  t283 = t282 ** 2
  t285 = 0.1e1 / t283 / t282
  t286 = s0 ** 2
  t287 = t285 * t286
  t288 = t287 * t224
  t289 = t266 * t288
  t290 = t7 ** 2
  t291 = t247 ** 2
  t292 = t291 ** 2
  t294 = 0.1e1 / t292 / t247
  t296 = t290 * t294 * t12
  t297 = 0.1e1 / t32
  t298 = t297 * t18
  t302 = t268 * t139
  t311 = 0.11073470983333333333333333333333333333333333333333e-2 * t15 * t22 * t269 + 0.10000000000000000000000000000000000000000000000000e1 * t302 * t150 - 0.18311447306006545054854346104378990962041954983034e-3 * t183 * t45 * t21 * t187 - 0.58482236226346462072622386637590534819724553404280e0 * t121 * t115
  t312 = t311 ** 2
  t313 = t281 ** 2
  t316 = t296 * t298 * t312 * t313
  t320 = params.beta / t260
  t321 = t320 * t264
  t322 = 0.1e1 / t283
  t323 = t322 * t286
  t325 = 0.1e1 / t34 / t196
  t326 = t323 * t325
  t327 = t321 * t326
  t331 = t290 / t291 / t248 * t12
  t332 = t311 * t281
  t334 = t331 * t298 * t332
  t337 = t323 * t224
  t338 = t321 * t337
  t345 = t268 * t177
  t350 = t268 * t167
  t366 = -0.14764627977777777777777777777777777777777777777777e-2 * t15 * t87 * t269 - 0.35616666666666666666666666666666666666666666666666e-1 * t132 * t154 * t150 - 0.20000000000000000000000000000000000000000000000000e1 * t345 * t179 + 0.10000000000000000000000000000000000000000000000000e1 * t302 * t162 + 0.16081979498692535066756296899072713062105388428051e2 * t350 * t172 + 0.24415263074675393406472461472505321282722606644045e-3 * t183 * t45 * t83 * t187 + 0.10843581300301739842632067522386578331157260943710e-1 * t16 * t22 * t115 + 0.11696447245269292414524477327518106963944910680856e1 * t121 * t67 - 0.58482236226346462072622386637590534819724553404280e0 * t121 * t101 - 0.17315859105681463759666483083807725165579399831905e2 * t121 * t110
  t369 = t331 * t298 * t366 * t281
  t372 = t266 * t337
  t373 = t312 * t281
  t375 = t296 * t298 * t373
  t378 = params.beta * t276
  t380 = t243 / t282
  t382 = t378 * t380 * t286
  t383 = t195 * t76
  t385 = 0.1e1 / t34 / t383
  t387 = 0.1e1 / t291
  t389 = t12 * t297
  t390 = t389 * t18
  t394 = 0.35e2 / 0.432e3 * s0 * t251 * t7 * t257 + t289 * t316 / 0.1536e4 - 0.7e1 / 0.2304e4 * t327 * t334 + t338 * t369 / 0.3072e4 - t372 * t375 / 0.3072e4 + 0.119e3 / 0.13824e5 * t382 * t385 * t290 * t387 * t390
  t395 = params.beta * t394
  t401 = t224 * t290
  t406 = s0 * t83 * t7 * t257 / 0.96e2 + t382 * t401 * t387 * t390 / 0.3072e4
  t409 = t378 * t380 * t406 + 0.1e1
  t411 = t276 * t243 / t409
  t419 = t325 * t290
  t424 = -0.7e1 / 0.288e3 * s0 * t186 * t7 * t257 + t338 * t334 / 0.3072e4 - 0.7e1 / 0.4608e4 * t382 * t419 * t387 * t390
  t425 = params.beta * t424
  t426 = t425 * t276
  t427 = t409 ** 2
  t429 = t243 / t427
  t431 = t320 * t264 * t322
  t432 = t406 * t311
  t433 = t278 * t281
  t438 = t378 * t380 * t424 + t431 * t432 * t433
  t439 = t429 * t438
  t442 = params.beta * t406
  t443 = t442 * t276
  t446 = t243 / t427 / t409
  t447 = t438 ** 2
  t448 = t446 * t447
  t452 = t263 * t265 * t285
  t453 = t406 * t312
  t455 = 0.1e1 / t291 / t247
  t456 = t455 * t313
  t460 = t424 * t311
  t464 = t406 * t366
  t468 = t263 * t265 * t322
  t469 = t455 * t281
  t474 = t378 * t380 * t394 + 0.2e1 * t431 * t460 * t433 + t431 * t464 * t433 + 0.2e1 * t452 * t453 * t456 - t468 * t453 * t469
  t475 = t429 * t474
  t477 = t395 * t411 - 0.2e1 * t426 * t439 + 0.2e1 * t443 * t448 - t443 * t475
  t479 = t442 * t411 + 0.1e1
  t480 = 0.1e1 / t479
  t482 = t249 * t477 * t480
  t485 = t238 * t241
  t486 = t485 * t244
  t489 = t425 * t411 - t443 * t439
  t490 = t489 ** 2
  t491 = t490 * t489
  t493 = t479 ** 2
  t495 = 0.1e1 / t493 / t479
  t499 = t195 * t184
  t501 = t194 / t499
  t505 = 0.1e1 / t19 / t499
  t506 = t505 * t216
  t507 = t194 * t506
  t510 = t385 * t73
  t515 = 0.1e1 / t34 / t499
  t520 = 0.1e1 / t26 / t13 * r0 / 0.48e2
  t523 = t33 * t17
  t524 = t219 * t523
  t528 = t216 * t227 * t208
  t532 = 0.1e1 / t19 / t383
  t536 = 0.1e1 / t203 / t202
  t537 = t536 * t208
  t538 = t537 * t390
  t541 = t195 ** 2
  t543 = t194 / t541
  t549 = 0.1e1 / t26 / t12 / t14 / t13 / t22 / 0.48e2
  t551 = t208 * t13
  t552 = t549 * t203 * t551
  t557 = t228 * t132
  t562 = t537 * t229
  t566 = t194 / t383
  t571 = 0.1e1 / t203 / t389 / t18 / t34 / 0.3e1
  t573 = t208 * jnp.pi
  t574 = t73 * t571 * t573
  t577 = 0.15e2 / 0.2e1 * t501 * t209 - 0.89e2 / 0.36e2 * t507 * t220 - 0.311e3 / 0.432e3 * t194 * t510 * t230 + 0.5e1 / 0.3e1 * t194 * t515 * t520 * t524 + 0.15e2 / 0.8e1 * t501 * t528 - 0.7e1 / 0.96e2 * t194 * t532 * t73 * t538 - 0.35e2 / 0.24e2 * t543 * t552 - 0.5e1 / 0.32e2 * t194 * t505 * t520 * t557 + t194 * t385 * t216 * t562 / 0.32e2 - t566 * t574 / 0.32e2
  t579 = t577 * t238 * t241
  t580 = jnp.log(t479)
  t581 = t249 * t580
  t584 = t233 ** 2
  t587 = t584 * t233 * t238 * t241
  t592 = t350 * t161 * t171 * t145
  t594 = -0.13012297560362087811158481026863893997388713132452e0 * t69 + 0.65061487801810439055792405134319469986943565662260e-1 * t103 + 0.19263893255070628432628962430736094246707082312994e1 * t112 - 0.86748650402413918741056540179092626649258087549680e-1 * t117 - 0.20779030926817756511599779700569270198695279798286e3 * t125 + 0.14035736694323150897429372793021728356733892817027e2 * t130 + 0.28493333333333333333333333333333333333333333333333e0 * t152 - 0.21370000000000000000000000000000000000000000000000e0 * t164 - 0.34367190188705947437658206473318387813719215070744e1 * t174 + 0.42740000000000000000000000000000000000000000000000e0 * t181 - 0.22787578869697033846040964041004966530541099534442e-2 * t190 + 0.12e2 * t242 * t482 + 0.8e1 * t486 * t248 * t491 * t495 + 0.4e1 * t579 * t581 + 0.4e1 * t587 * t581 + 0.19298375398431042080107556278887255674526466113661e3 * t592
  t595 = t169 * t145
  t596 = t595 * t149
  t597 = t350 * t596
  t600 = t584 * t238 * t241
  t602 = t249 * t489 * t480
  t606 = t345 * t150 * t161
  t608 = t18 * t186
  t610 = t15 * t608 * t269
  t613 = 0.1e1 / t105 / t40
  t614 = t61 * t60
  t617 = 0.1e1 / t108 / t65
  t618 = t613 * t614 * t617
  t619 = t121 * t618
  t622 = 0.1e1 / t105 / t39
  t624 = t622 * t614 * t109
  t625 = t121 * t624
  t627 = t216 * t13
  t628 = t627 * t234
  t631 = 0.1e1 / t34 / t184
  t632 = t75 * t631
  t633 = t74 * t632
  t635 = t45 * t186
  t636 = t44 * t635
  t638 = t15 * t608
  t640 = t25 ** (-0.15e1)
  t641 = t640 * t13
  t642 = t641 * t234
  t644 = t91 * t632
  t646 = t52 * t635
  t649 = t33 * t17 * t631
  t651 = -0.34523333333333333333333333333333333333333333333333e1 * t628 + 0.23015555555555555555555555555555555555555555555556e1 * t633 - 0.26851481481481481481481481481481481481481481481482e1 * t636 - 0.93932222222222222222222222222222222222222222222223e0 * t638 + 0.73355000000000000000000000000000000000000000000000e-1 * t642 - 0.14671000000000000000000000000000000000000000000000e0 * t644 - 0.17116166666666666666666666666666666666666666666667e0 * t646 - 0.36793333333333333333333333333333333333333333333333e0 * t649
  t653 = t71 * t651 * t66
  t654 = t121 * t653
  t657 = t106 * t614 * t66
  t658 = t121 * t657
  t664 = t260 ** 2
  t666 = params.beta / t664
  t667 = t264 ** 2
  t668 = t666 * t667
  t669 = t283 ** 2
  t670 = 0.1e1 / t669
  t671 = t670 * t286
  t672 = t671 * t224
  t676 = 0.1e1 / t292 / t291 / t246
  t678 = t290 * t676 * t12
  t679 = t312 * t311
  t680 = t313 * t281
  t683 = t678 * t298 * t679 * t680
  t686 = t287 * t325
  t690 = t287 * t401
  t691 = t266 * t690
  t693 = t294 * t12 * t297
  t694 = t18 * t311
  t695 = t313 * t366
  t697 = t693 * t694 * t695
  t703 = t678 * t298 * t679 * t313
  t706 = t323 * t385
  t707 = t321 * t706
  t726 = -0.10254018858216406658218194626490193680059335835414e4 * t619 + 0.10389515463408878255799889850284635099347639899143e3 * t625 - 0.58482236226346462072622386637590534819724553404280e0 * t654 - 0.32530743900905219527896202567159734993471782831130e-1 * t69 + 0.16265371950452609763948101283579867496735891415565e-1 * t103 + 0.48159733137676571081572406076840235616767705782485e0 * t112 - 0.21687162600603479685264135044773156662314521887420e-1 * t117 - 0.51947577317044391278999449251423175496738199495715e2 * t125 - 0.35089341735807877243573431982554320891834732042568e1 * t658 + 0.35089341735807877243573431982554320891834732042568e1 * t130 + 0.71233333333333333333333333333333333333333333333331e-1 * t152
  t730 = 0.1e1 / t166 / t138
  t731 = t268 * t730
  t733 = 0.1e1 / t170 / t148
  t734 = t595 * t733
  t735 = t731 * t734
  t738 = 0.1e1 / t166 / t137
  t739 = t268 * t738
  t740 = t595 * t171
  t741 = t739 * t740
  t751 = -0.25319000000000000000000000000000000000000000000000e1 * t628 + 0.16879333333333333333333333333333333333333333333333e1 * t633 - 0.19692555555555555555555555555555555555555555555555e1 * t636 - 0.93011851851851851851851851851851851851851851851854e0 * t638 + 0.13651666666666666666666666666666666666666666666667e0 * t642 - 0.27303333333333333333333333333333333333333333333333e0 * t644 - 0.31853888888888888888888888888888888888888888888890e0 * t646 - 0.36514074074074074074074074074074074074074074074075e0 * t649
  t752 = t751 * t149
  t753 = t302 * t752
  t761 = -0.53424999999999999999999999999999999999999999999999e-1 * t164 - 0.85917975471764868594145516183295969534298037676861e0 * t174 + 0.51726012919273400298984252201052768390886626637712e3 * t735 - 0.96491876992155210400537781394436278372632330568306e2 * t741 + 0.10000000000000000000000000000000000000000000000000e1 * t753 + 0.48245938496077605200268890697218139186316165284153e2 * t592 + 0.60000000000000000000000000000000000000000000000000e1 * t597 - 0.60000000000000000000000000000000000000000000000000e1 * t606 + 0.34450798614814814814814814814814814814814814814813e-2 * t610 + 0.10685000000000000000000000000000000000000000000000e0 * t181 - 0.56968947174242584615102410102512416326352748836105e-3 * t190
  t762 = t726 + t761
  t765 = t331 * t298 * t762 * t281
  t768 = t323 * t401
  t769 = t266 * t768
  t770 = t18 * t366
  t772 = t693 * t770 * t332
  t778 = t678 * t298 * t679 * t281
  t786 = -0.455e3 / 0.1296e4 * s0 * t213 * t7 * t257 + t668 * t672 * t683 / 0.512e3 - 0.7e1 / 0.768e3 * t266 * t686 * t316 + t691 * t697 / 0.512e3 - t668 * t288 * t703 / 0.512e3 + 0.119e3 / 0.4608e4 * t707 * t334 - 0.7e1 / 0.1536e4 * t327 * t369 + 0.7e1 / 0.1536e4 * t266 * t326 * t375 + t338 * t765 / 0.3072e4 - t769 * t772 / 0.1024e4 + t668 * t337 * t778 / 0.3072e4 - 0.595e3 / 0.10368e5 * t382 * t515 * t290 * t387 * t390
  t787 = params.beta * t786
  t789 = t395 * t276
  t796 = t427 ** 2
  t798 = t243 / t796
  t800 = t798 * t447 * t438
  t804 = t446 * t438 * t474
  t808 = t666 * t667 * t670
  t809 = t406 * t679
  t811 = 0.1e1 / t292 / t246
  t812 = t811 * t680
  t816 = t424 * t312
  t820 = t456 * t366
  t825 = t666 * t667 * t285
  t826 = t811 * t313
  t834 = t424 * t366
  t841 = t406 * t762
  t845 = t455 * t311 * t281
  t850 = t666 * t667 * t322
  t851 = t811 * t281
  t856 = 0.3e1 * t431 * t394 * t311 * t433 + t378 * t380 * t786 + 0.3e1 * t431 * t834 * t433 + t431 * t841 * t433 + 0.6e1 * t452 * t432 * t820 + 0.6e1 * t452 * t816 * t456 - 0.3e1 * t468 * t464 * t845 - 0.3e1 * t468 * t816 * t469 + 0.6e1 * t808 * t809 * t812 - 0.6e1 * t825 * t809 * t826 + t850 * t809 * t851
  t857 = t429 * t856
  t859 = t787 * t411 + 0.6e1 * t426 * t448 - 0.3e1 * t426 * t475 - 0.3e1 * t789 * t439 - 0.6e1 * t443 * t800 + 0.6e1 * t443 * t804 - t443 * t857
  t860 = t248 * t859
  t884 = -0.5e1 / 0.4e1 * t566 * t209 + 0.7e1 / 0.24e2 * t194 * t532 * t216 * t220 + 0.13e2 / 0.144e3 * t194 * t325 * t73 * t230 - 0.5e1 / 0.48e2 * t194 * t385 * t520 * t524 - t566 * t528 / 0.8e1 + t194 * t213 * t73 * t538 / 0.192e3
  t885 = t884 * t233
  t893 = 0.1e1 / t493
  t895 = t249 * t490 * t893
  t902 = t241 * t244
  t904 = t902 * t248 * t580
  t909 = 0.12842595503380418955085974953824062831138054875329e1 * t16 * t87 * t110
  t912 = 0.38527786510141256865257924861472188493414164625988e1 * t16 * t22 * t624
  t915 = 0.21687162600603479685264135044773156662314521887420e-1 * t16 * t22 * t653
  t918 = 0.38025319932552508024225805073234468230220037056326e2 * t16 * t22 * t618
  t921 = 0.67471172535210825687488420139294265171645179205307e-1 * t16 * t608 * t115
  t924 = 0.86748650402413918741056540179092626649258087549680e-1 * t16 * t87 * t67
  t927 = 0.13012297560362087811158481026863893997388713132452e0 * t16 * t22 * t657
  t930 = 0.43374325201206959370528270089546313324629043774840e-1 * t16 * t87 * t101
  t936 = t884 * t238 * t241
  t939 = t477 ** 2
  t944 = 0.4e1 * t577 * t233 * t238 * t904 + 0.4e1 * t242 * t249 * t859 * t480 + 0.8e1 * t242 * t249 * t491 * t495 - 0.3e1 * t486 * t248 * t939 * t893 + 0.12e2 * t885 * t485 * t602 + 0.6e1 * t936 * t482 + 0.4e1 * t587 * t602 - 0.6e1 * t600 * t895 - t909 - t912 + t915 + t918 + t921 + t924 + t927 - t930
  t945 = t490 ** 2
  t947 = t493 ** 2
  t952 = t584 ** 2
  t958 = t520 * t13 * t213 * t132
  t960 = t627 * t197
  t962 = t75 * t224
  t963 = t74 * t962
  t965 = t45 * t251
  t966 = t44 * t965
  t968 = t18 * t251
  t969 = t15 * t968
  t971 = t25 ** (-0.25e1)
  t974 = t971 * t13 * t213 * t132
  t976 = t641 * t197
  t978 = t91 * t962
  t980 = t52 * t965
  t983 = t33 * t17 * t224
  t988 = 0.10000000000000000000000000000000000000000000000000e1 * t302 * (-0.21099166666666666666666666666666666666666666666667e1 * t958 + 0.20255200000000000000000000000000000000000000000000e2 * t960 - 0.75019259259259259259259259259259259259259259259258e1 * t963 + 0.65641851851851851851851851851851851851851851851850e1 * t966 + 0.31003950617283950617283950617283950617283950617285e1 * t969 + 0.68258333333333333333333333333333333333333333333335e-1 * t974 - 0.10921333333333333333333333333333333333333333333333e1 * t976 + 0.12134814814814814814814814814814814814814814814815e1 * t978 + 0.10617962962962962962962962962962962962962962962963e1 * t980 + 0.13388493827160493827160493827160493827160493827161e1 * t983) * t149
  t989 = t166 ** 2
  t992 = t169 ** 2
  t993 = t170 ** 2
  t997 = 0.24955700379505800914252936827276051226357058527653e5 * t268 / t989 * t992 / t993
  t1000 = t248 * t477
  t1010 = t893 * t489
  t1011 = t1000 * t1010
  t1016 = params.beta / t664 / t241
  t1017 = t667 * t243
  t1018 = t1016 * t1017
  t1020 = t292 ** 2
  t1023 = t290 / t1020 * t12
  t1024 = t312 ** 2
  t1038 = 0.1e1 / t669 / t282
  t1042 = t313 ** 2
  t1069 = t366 ** 2
  t1080 = 0.7e1 / 0.1536e4 * t1018 * t288 * t1023 * t298 * t1024 * t313 + 0.119e3 / 0.2304e4 * t707 * t369 - 0.119e3 / 0.2304e4 * t266 * t706 * t375 - 0.7e1 / 0.1152e4 * t327 * t765 + t1018 * t1038 * t286 * t224 * t1023 * t298 * t1024 * t1042 / 0.128e3 - 0.3e1 / 0.256e3 * t1018 * t672 * t1023 * t298 * t1024 * t680 + 0.7e1 / 0.192e3 * t668 * t686 * t703 + 0.455e3 / 0.243e3 * s0 * t532 * t7 * t257 + 0.7e1 / 0.384e3 * t266 * t323 * t419 * t772 - 0.595e3 / 0.2592e4 * t321 * t323 * t515 * t334 + t289 * t296 * t298 * t1069 * t313 / 0.512e3 + t691 * t693 * t694 * t313 * t762 / 0.384e3
  t1083 = t676 * t12 * t297
  t1084 = t18 * t312
  t1113 = 0.57895126195293126240322668836661767023579398340984e3 * t739 * t172 * t161
  t1114 = -t909 - t912 + t915 + t918 + t921 + t924 + t927 - t930 + t988 + t997 - t1113
  t1117 = 0.57895126195293126240322668836661767023579398340984e3 * t731 * t992 * t171
  t1118 = t161 ** 2
  t1121 = 0.60000000000000000000000000000000000000000000000000e1 * t345 * t1118 * t149
  t1124 = 0.48245938496077605200268890697218139186316165284153e2 * t350 * t1118 * t171
  t1128 = 0.64327917994770140267025187596290852248421553712204e2 * t350 * t751 * t171 * t145
  t1132 = 0.31035607751564040179390551320631661034531975982628e4 * t731 * t169 * t733 * t161
  t1135 = 0.36000000000000000000000000000000000000000000000000e2 * t350 * t179 * t161
  t1138 = 0.11483599538271604938271604938271604938271604938271e-1 * t15 * t968 * t269
  t1141 = 0.80000000000000000000000000000000000000000000000000e1 * t345 * t752 * t145
  t1144 = t61 ** 2
  t1148 = 0.12304822629859687989861833551788232416071203002497e5 * t121 / t105 / t41 * t1144 * t617
  t1152 = 0.62337092780453269534799339101707810596085839394858e3 * t121 * t613 * t1144 * t109
  t1153 = t99 ** 2
  t1157 = 0.51947577317044391278999449251423175496738199495715e2 * t121 * t106 * t1153 * t109
  t1161 = 0.35089341735807877243573431982554320891834732042568e1 * t121 * t42 * t1153 * t66
  t1162 = t1117 - t1121 + t1124 + t1128 + t1132 + t1135 - t1138 - t1141 + t1148 - t1152 - t1157 + t1161
  t1167 = 0.14035736694323150897429372793021728356733892817027e2 * t121 * t622 * t1144 * t66
  t1182 = 0.58482236226346462072622386637590534819724553404280e0 * t121 * t71 * (-0.28769444444444444444444444444444444444444444444444e1 * t958 + 0.27618666666666666666666666666666666666666666666667e2 * t960 - 0.10229135802469135802469135802469135802469135802469e2 * t963 + 0.89504938271604938271604938271604938271604938271607e1 * t966 + 0.31310740740740740740740740740740740740740740740741e1 * t969 + 0.36677500000000000000000000000000000000000000000000e-1 * t974 - 0.58684000000000000000000000000000000000000000000000e0 * t976 + 0.65204444444444444444444444444444444444444444444445e0 * t978 + 0.57053888888888888888888888888888888888888888888890e0 * t980 + 0.13490888888888888888888888888888888888888888888889e1 * t983) * t66
  t1183 = t105 ** 2
  t1186 = t108 ** 2
  t1190 = 0.91082604192152556048340974007871726131433263376469e5 * t121 / t1183 * t1144 / t1186
  t1195 = 0.62337092780453269534799339101707810596085839394858e3 * t121 * t622 * t99 * t109 * t61
  t1198 = 0.21053605041484726346144059189532592535100839225540e2 * t121 * t107 * t128
  t1202 = 0.18989649058080861538367470034170805442117582945368e-2 * t183 * t45 * t251 * t187
  t1206 = 0.22161481481481481481481481481481481481481481481481e0 * t132 * t186 * t139 * t150
  t1210 = 0.28493333333333333333333333333333333333333333333333e0 * t132 * t83 * t177 * t179
  t1214 = 0.68734380377411894875316412946636775627438430141488e1 * t132 * t21 * t738 * t740
  t1217 = 0.42740000000000000000000000000000000000000000000000e0 * t132 * t168 * t596
  t1222 = 0.61524113149298439949309167758941162080356015012483e4 * t121 * t613 * t99 * t617 * t61
  t1223 = t1167 - t1182 - t1190 + t1195 - t1198 + t1202 - t1206 - t1210 + t1214 - t1217 - t1222
  t1227 = 0.46785788981077169658097909310072427855779642723424e1 * t121 * t127 * t66 * t651
  t1231 = 0.36846163202829085479643115651216588683774907041596e2 * t132 * t21 * t730 * t734
  t1235 = 0.69263436422725855038665932335230900662317599327620e2 * t121 * t106 * t651 * t123
  t1238 = 0.14246666666666666666666666666666666666666666666666e0 * t132 * t140 * t162
  t1242 = 0.22911460125803964958438804315545591875812810047162e1 * t132 * t83 * t167 * t172
  t1245 = 0.71233333333333333333333333333333333333333333333332e-1 * t132 * t154 * t752
  t1246 = t11 * t132
  t1252 = 0.13012297560362087811158481026863893997388713132452e0 * t1246 * t21 * t42 * t60 * t66 * t99
  t1257 = t1246 * t21 * t106 * t99 * t109 * t60
  t1261 = 0.24000000000000000000000000000000000000000000000000e2 * t739 * t992 * t149
  t1265 = 0.42740000000000000000000000000000000000000000000000e0 * t49 * t177 * t161 * t150
  t1270 = 0.34367190188705947437658206473318387813719215070744e1 * t49 * t167 * t161 * t171 * t145
  t1276 = 0.62071215503128080358781102641263322069063951965254e4 * t268 / t166 / t176 * t992 * t733
  t1277 = t1227 - t1231 - t1235 + t1238 + t1242 - t1245 - t1252 + 0.19263893255070628432628962430736094246707082312995e1 * t1257 - t1261 + t1265 - t1270 - t1276
  t1279 = t1114 + t1162 + t1223 + t1277
  t1292 = 0.1e1 / t34 / t541
  t1313 = -0.3e1 / 0.256e3 * t668 * t690 * t1083 * t1084 * t695 + 0.3e1 / 0.256e3 * t668 * t671 * t401 * t1083 * t1084 * t680 * t366 + 0.119e3 / 0.1152e4 * t266 * t287 * t385 * t316 - 0.7e1 / 0.192e3 * t266 * t287 * t419 * t697 - 0.7e1 / 0.192e3 * t668 * t671 * t325 * t683 - 0.7e1 / 0.1152e4 * t668 * t326 * t778 + t338 * t331 * t298 * t1279 * t281 / 0.3072e4 - t1018 * t337 * t1023 * t298 * t1024 * t281 / 0.3072e4 + 0.13685e5 / 0.31104e5 * t382 * t1292 * t290 * t387 * t390 - t372 * t296 * t298 * t1069 * t281 / 0.1024e4 + t668 * t768 * t1083 * t770 * t373 / 0.512e3 - t769 * t693 * t18 * t762 * t332 / 0.768e3
  t1314 = t1080 + t1313
  t1333 = t447 ** 2
  t1341 = t474 ** 2
  t1355 = t406 * t1024
  t1357 = 0.1e1 / t292 / t291
  t1373 = t406 * t1069
  t1383 = t424 * t679
  t1396 = 0.24e2 * t1016 * t1017 * t1038 * t1355 * t1357 * t1042 + 0.14e2 * t1016 * t1017 * t285 * t1355 * t1357 * t313 + 0.4e1 * t431 * t786 * t311 * t433 + 0.36e2 * t808 * t453 * t812 * t366 - 0.36e2 * t825 * t453 * t826 * t366 + 0.8e1 * t452 * t432 * t456 * t762 + t378 * t380 * t1314 + 0.6e1 * t452 * t1373 * t456 + 0.24e2 * t808 * t1383 * t812 - 0.24e2 * t825 * t1383 * t826 + 0.24e2 * t452 * t460 * t820
  t1403 = t394 * t312
  t1443 = -0.36e2 * t1016 * t1017 * t670 * t1355 * t1357 * t680 + 0.12e2 * t452 * t1403 * t456 + 0.6e1 * t431 * t394 * t366 * t433 - 0.6e1 * t468 * t1403 * t469 + 0.4e1 * t850 * t1383 * t851 + t431 * t406 * t1279 * t433 + 0.4e1 * t431 * t424 * t762 * t433 + 0.6e1 * t850 * t464 * t811 * t312 * t281 - 0.3e1 * t468 * t1373 * t469 - 0.4e1 * t468 * t841 * t845 - 0.12e2 * t468 * t834 * t845 - t1016 * t1017 * t322 * t1355 * t1357 * t281
  t1447 = params.beta * t1314 * t411 - 0.4e1 * t787 * t276 * t439 + 0.12e2 * t789 * t448 - 0.6e1 * t789 * t475 - 0.24e2 * t426 * t800 + 0.24e2 * t426 * t804 - 0.4e1 * t426 * t857 + 0.24e2 * t443 * t243 / t796 / t409 * t1333 - 0.36e2 * t443 * t798 * t447 * t474 + 0.6e1 * t443 * t446 * t1341 + 0.8e1 * t443 * t446 * t438 * t856 - t443 * t429 * (t1396 + t1443)
  t1467 = t1292 * t549
  t1475 = 0.1e1 / t19 / t541
  t1494 = t541 * r0
  t1534 = 0.5e1 / 0.8e1 * t543 * t520 * t536 * t208 + 0.490e3 / 0.81e2 * t194 * t515 * t73 * t230 - 0.1135e4 / 0.54e2 * t194 * t1292 * t520 * t524 - 0.2e1 / 0.3e1 * t194 * t515 * t216 * t562 - 0.35e2 / 0.48e2 * t194 * t1467 * t228 * t523 - 0.403e3 / 0.18e2 * t543 * t528 + 0.2363e4 / 0.108e3 * t194 * t1475 * t216 * t220 - t194 * t506 * t571 * t573 * t132 / 0.64e2 + 0.5e1 / 0.6912e4 * t194 * t510 / t203 / jnp.pi / r0 * t573 * t229 - 0.35e2 / 0.3072e4 * t194 / t19 / t1494 / t26 / t31 / t32 / t13 / t57 * t203 * t551 * t132 - 0.35e2 / 0.144e3 * t194 * t1467 * t227 * t551 * t229 - 0.3e1 / 0.64e2 * t507 * t571 * t208 * t390 + 0.355e3 / 0.432e3 * t194 * t505 * t73 * t538 + 0.85e2 / 0.24e2 * t194 * t1475 * t520 * t557 - 0.105e3 / 0.2e1 * t543 * t209 + 0.35e2 * t194 / t1494 * t552 + 0.5e1 / 0.8e1 * t501 * t574
  t1538 = t884 ** 2
  t1543 = -0.6e1 * t486 * t248 * t945 / t947 + t952 * t238 * t241 * t581 + t988 + t997 + 0.4e1 * t579 * t602 + 0.12e2 * t486 * t1000 * t495 * t490 + 0.6e1 * t884 * t584 * t238 * t904 - 0.12e2 * t239 * t902 * t1011 + t486 * t248 * t1447 * t480 - t1113 + t1534 * t238 * t241 * t581 + 0.3e1 * t1538 * t238 * t241 * t581 + t1117 - t1121 + t1124 + t1128 + t1132
  t1545 = t1135 - t1138 - t1141 + t1148 - t1152 - t1157 + t1161 + t1167 - t1182 - t1190 + t1195 - t1198 + t1202 - t1206 - t1210 + t1214
  t1554 = -t1217 - t1222 + t1227 - t1231 - t1235 + t1238 + t1242 - t1245 - 0.6e1 * t936 * t895 - t1252 + 0.19263893255070628432628962430736094246707082312994e1 * t1257 - 0.4e1 * t486 * t860 * t1010 - t1261 + 0.6e1 * t600 * t482 + t1265 - t1270 - t1276
  t1570 = 0.24000000000000000000000000000000000000000000000000e2 * t597 + 0.12e2 * t600 * t602 - 0.24000000000000000000000000000000000000000000000000e2 * t606 + 0.13780319445925925925925925925925925925925925925925e-1 * t610 - 0.41016075432865626632872778505960774720237343341655e4 * t619 + 0.41558061853635513023199559401138540397390559596572e3 * t625 - 0.23392894490538584829048954655036213927889821361712e1 * t654 - 0.14035736694323150897429372793021728356733892817027e2 * t658 + 0.4e1 * t486 * t860 * t480 + r0 * (t944 + t1543 + t1545 + t1554) + 0.20690405167709360119593700880421107356354650655085e4 * t735 - 0.38596750796862084160215112557774511349052932227323e3 * t741 + 0.40000000000000000000000000000000000000000000000000e1 * t753 - 0.12e2 * t242 * t895 + 0.12e2 * t885 * t238 * t904 + 0.12e2 * t936 * t602 - 0.12e2 * t486 * t1011
  v4rho4_0_ = t594 + t1570

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 + r1
  t3 = s0 + 0.2e1 * s1 + s2
  t4 = jnp.sqrt(t3)
  t6 = params.alpha * t4 * t3
  t7 = t1 ** 2
  t8 = t7 ** 2
  t9 = t8 * t1
  t10 = 0.1e1 / t9
  t12 = 3 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / jnp.pi
  t14 = t13 ** (0.1e1 / 0.3e1)
  t15 = t12 * t14
  t16 = 4 ** (0.1e1 / 0.3e1)
  t17 = t16 ** 2
  t18 = t1 ** (0.1e1 / 0.3e1)
  t21 = t15 * t17 / t18
  t22 = jnp.sqrt(t21)
  t24 = 0.1e1 / t22 / t21
  t25 = t12 ** 2
  t26 = 0.1e1 / t14
  t27 = t25 * t26
  t29 = t27 * t16 * t18
  t30 = jnp.sqrt(t29)
  t32 = r0 - r1
  t33 = t32 ** 2
  t34 = 0.1e1 / t7
  t35 = t33 * t34
  t36 = 0.1e-19 < t35
  t37 = f.my_piecewise3(t36, t35, 0.1e-19)
  t39 = t37 ** (params.omega / 0.2e1)
  t40 = t24 * t30 * t39
  t42 = t6 * t10 * t40 / 0.4e1
  t44 = 0.1e1 / t18 / t9
  t45 = t14 ** 2
  t46 = t25 * t45
  t47 = t18 ** 2
  t50 = t46 * t16 / t47
  t53 = 0.1e1 / t22 / t50 / 0.4e1
  t56 = t30 * t39
  t57 = t15 * t17
  t58 = t56 * t57
  t60 = t6 * t44 * t53 * t58 / 0.32e2
  t62 = 0.1e1 / t47 / t8
  t65 = 0.1e1 / t30
  t67 = t27 * t16
  t68 = t65 * t39 * t67
  t70 = t6 * t62 * t24 * t68 / 0.96e2
  t71 = 0.1e1 / t8
  t72 = t71 * t24
  t73 = t6 * t72
  t74 = t32 * t34
  t75 = t7 * t1
  t76 = 0.1e1 / t75
  t77 = t33 * t76
  t80 = f.my_piecewise3(t36, 0.2e1 * t74 - 0.2e1 * t77, 0)
  t82 = 0.1e1 / t37
  t83 = params.omega * t80 * t82
  t84 = t56 * t83
  t87 = t42 - t60 - t70 - t73 * t84 / 0.32e2
  t91 = jnp.exp(-t6 * t71 * t40 / 0.16e2)
  t93 = jnp.log(0.2e1)
  t94 = 0.1e1 - t93
  t95 = t87 * t91 * t94
  t96 = jnp.pi ** 2
  t97 = 0.1e1 / t96
  t98 = 0.1e1 / t1
  t99 = t32 * t98
  t100 = 0.1e1 + t99
  t101 = t100 <= f.p.zeta_threshold
  t102 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t103 = t102 ** 2
  t104 = t100 ** (0.1e1 / 0.3e1)
  t105 = t104 ** 2
  t106 = f.my_piecewise3(t101, t103, t105)
  t107 = 0.1e1 - t99
  t108 = t107 <= f.p.zeta_threshold
  t109 = t107 ** (0.1e1 / 0.3e1)
  t110 = t109 ** 2
  t111 = f.my_piecewise3(t108, t103, t110)
  t113 = t106 / 0.2e1 + t111 / 0.2e1
  t114 = t113 ** 2
  t115 = t114 * t113
  t116 = t97 * t115
  t119 = t3 / t18 / t75
  t120 = 2 ** (0.1e1 / 0.3e1)
  t125 = 0.1e1 / t114 * t25 * t26 * t16
  t127 = 0.7e1 / 0.288e3 * t119 * t120 * t125
  t129 = 0.1e1 / t18 / t7
  t130 = t3 * t129
  t131 = 0.1e1 / t115
  t132 = t120 * t131
  t133 = t130 * t132
  t134 = 0.1e1 / t104
  t135 = t98 - t74
  t138 = f.my_piecewise3(t101, 0, 0.2e1 / 0.3e1 * t134 * t135)
  t139 = 0.1e1 / t109
  t140 = -t135
  t143 = f.my_piecewise3(t108, 0, 0.2e1 / 0.3e1 * t139 * t140)
  t145 = t138 / 0.2e1 + t143 / 0.2e1
  t147 = t27 * t16 * t145
  t150 = 0.1e1 / t94
  t151 = params.beta * t150
  t152 = t151 * t96
  t154 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t21
  t157 = t21 ** 0.15e1
  t160 = 0.37978500000000000000000000000000000000000000000000e1 * t22 + 0.89690000000000000000000000000000000000000000000000e0 * t21 + 0.20477500000000000000000000000000000000000000000000e0 * t157 + 0.12323500000000000000000000000000000000000000000000e0 * t50
  t163 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t160
  t164 = jnp.log(t163)
  t166 = 0.621814e-1 * t154 * t164
  t167 = t33 ** 2
  t168 = t167 * t71
  t169 = t102 * f.p.zeta_threshold
  t170 = t104 * t100
  t171 = f.my_piecewise3(t101, t169, t170)
  t172 = t109 * t107
  t173 = f.my_piecewise3(t108, t169, t172)
  t177 = 0.1e1 / (0.2e1 * t120 - 0.2e1)
  t178 = (t171 + t173 - 0.2e1) * t177
  t180 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t21
  t185 = 0.70594500000000000000000000000000000000000000000000e1 * t22 + 0.15494250000000000000000000000000000000000000000000e1 * t21 + 0.42077500000000000000000000000000000000000000000000e0 * t157 + 0.15629250000000000000000000000000000000000000000000e0 * t50
  t188 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t185
  t189 = jnp.log(t188)
  t193 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t21
  t198 = 0.51785000000000000000000000000000000000000000000000e1 * t22 + 0.90577500000000000000000000000000000000000000000000e0 * t21 + 0.11003250000000000000000000000000000000000000000000e0 * t157 + 0.12417750000000000000000000000000000000000000000000e0 * t50
  t201 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t198
  t202 = jnp.log(t201)
  t203 = t193 * t202
  t205 = -0.3109070e-1 * t180 * t189 + t166 - 0.19751673498613801407483339618206552048944131217655e-1 * t203
  t206 = t178 * t205
  t211 = (-t166 + t168 * t206 + 0.19751673498613801407483339618206552048944131217655e-1 * t178 * t203) * t150
  t212 = t96 * t131
  t214 = jnp.exp(-t211 * t212)
  t215 = t214 - 0.1e1
  t216 = t215 ** 2
  t217 = 0.1e1 / t216
  t218 = t3 ** 2
  t219 = t217 * t218
  t221 = t152 * t219 * t62
  t222 = t120 ** 2
  t223 = t114 ** 2
  t224 = 0.1e1 / t223
  t226 = t222 * t224 * t12
  t227 = 0.1e1 / t45
  t228 = t227 * t17
  t230 = 0.1e1 / t18 / t1
  t231 = t17 * t230
  t233 = t15 * t231 * t164
  t234 = 0.11073470983333333333333333333333333333333333333333e-2 * t233
  t235 = t160 ** 2
  t236 = 0.1e1 / t235
  t237 = t154 * t236
  t239 = 0.1e1 / t22 * t12
  t240 = t14 * t17
  t241 = t240 * t230
  t242 = t239 * t241
  t244 = t15 * t231
  t246 = t21 ** 0.5e0
  t247 = t246 * t12
  t248 = t247 * t241
  t253 = t46 * t16 / t47 / t1
  t255 = -0.63297500000000000000000000000000000000000000000000e0 * t242 - 0.29896666666666666666666666666666666666666666666667e0 * t244 - 0.10238750000000000000000000000000000000000000000000e0 * t248 - 0.82156666666666666666666666666666666666666666666667e-1 * t253
  t256 = 0.1e1 / t163
  t257 = t255 * t256
  t258 = t237 * t257
  t259 = 0.10000000000000000000000000000000000000000000000000e1 * t258
  t260 = t33 * t32
  t261 = t260 * t71
  t262 = t261 * t206
  t263 = 0.4e1 * t262
  t264 = t167 * t10
  t265 = t264 * t206
  t266 = 0.4e1 * t265
  t269 = f.my_piecewise3(t101, 0, 0.4e1 / 0.3e1 * t104 * t135)
  t272 = f.my_piecewise3(t108, 0, 0.4e1 / 0.3e1 * t109 * t140)
  t274 = (t269 + t272) * t177
  t275 = t274 * t205
  t276 = t168 * t275
  t280 = t185 ** 2
  t281 = 0.1e1 / t280
  t282 = t180 * t281
  t287 = -0.11765750000000000000000000000000000000000000000000e1 * t242 - 0.51647500000000000000000000000000000000000000000000e0 * t244 - 0.21038750000000000000000000000000000000000000000000e0 * t248 - 0.10419500000000000000000000000000000000000000000000e0 * t253
  t288 = 0.1e1 / t188
  t289 = t287 * t288
  t295 = t198 ** 2
  t296 = 0.1e1 / t295
  t297 = t193 * t296
  t302 = -0.86308333333333333333333333333333333333333333333334e0 * t242 - 0.30192500000000000000000000000000000000000000000000e0 * t244 - 0.55016250000000000000000000000000000000000000000000e-1 * t248 - 0.82785000000000000000000000000000000000000000000000e-1 * t253
  t303 = 0.1e1 / t201
  t304 = t302 * t303
  t307 = 0.53237641966666666666666666666666666666666666666666e-3 * t15 * t231 * t189 + 0.10000000000000000000000000000000000000000000000000e1 * t282 * t289 - t234 - t259 + 0.18311447306006545054854346104378990962041954983034e-3 * t15 * t231 * t202 + 0.58482236226346462072622386637590534819724553404280e0 * t297 * t304
  t308 = t178 * t307
  t309 = t168 * t308
  t310 = t274 * t203
  t311 = 0.19751673498613801407483339618206552048944131217655e-1 * t310
  t312 = t178 * t12
  t314 = t240 * t230 * t202
  t315 = t312 * t314
  t316 = 0.18311447306006545054854346104378990962041954983034e-3 * t315
  t317 = t178 * t193
  t319 = t296 * t302 * t303
  t320 = t317 * t319
  t321 = 0.58482236226346462072622386637590534819724553404280e0 * t320
  t323 = (t234 + t259 + t263 - t266 + t276 + t309 + t311 - t316 - t321) * t150
  t325 = t96 * t224
  t326 = t325 * t145
  t329 = 0.3e1 * t211 * t326 - t323 * t212
  t330 = t329 * t214
  t332 = t226 * t228 * t330
  t335 = 0.1e1 / t215
  t336 = t96 * t335
  t338 = t151 * t336 * t218
  t340 = 0.1e1 / t47 / t9
  t344 = t12 * t227 * t17
  t347 = 0.7e1 / 0.4608e4 * t338 * t340 * t222 * t224 * t344
  t348 = t335 * t218
  t350 = t152 * t348 * t62
  t352 = 0.1e1 / t223 / t113
  t354 = t222 * t352 * t12
  t356 = t354 * t228 * t145
  t359 = -t127 - t133 * t147 / 0.48e2 - t221 * t332 / 0.3072e4 - t347 - t350 * t356 / 0.768e3
  t360 = params.beta * t359
  t365 = t62 * t222
  t370 = t130 * t120 * t125 / 0.96e2 + t338 * t365 * t224 * t344 / 0.3072e4
  t373 = t151 * t336 * t370 + 0.1e1
  t375 = t150 * t96 / t373
  t377 = params.beta * t370
  t378 = t377 * t150
  t379 = t373 ** 2
  t381 = t96 / t379
  t382 = t217 * t370
  t387 = t151 * t336 * t359 - t152 * t382 * t330
  t388 = t381 * t387
  t390 = t360 * t375 - t378 * t388
  t392 = t377 * t375 + 0.1e1
  t393 = 0.1e1 / t392
  t395 = t116 * t390 * t393
  t399 = t91 * t94 * t97
  t400 = t114 * t390
  t401 = t393 * t145
  t408 = 0.35616666666666666666666666666666666666666666666666e-1 * t57 * t230 * t236 * t257
  t410 = t274 * t12 * t314
  t411 = 0.36622894612013090109708692208757981924083909966068e-3 * t410
  t415 = 0.24415263074675393406472461472505321282722606644045e-3 * t312 * t240 * t129 * t202
  t418 = 0.32e2 * t260 * t10 * t206
  t419 = t8 * t7
  t420 = 0.1e1 / t419
  t423 = 0.20e2 * t167 * t420 * t206
  t424 = t33 * t71
  t426 = 0.12e2 * t424 * t206
  t427 = t17 * t129
  t430 = 0.14764627977777777777777777777777777777777777777777e-2 * t15 * t427 * t164
  t432 = t168 * t274 * t307
  t433 = 0.2e1 * t432
  t444 = t287 ** 2
  t451 = 0.1e1 / t47 / t7
  t452 = t45 * t16 * t451
  t453 = t24 * t25 * t452
  t455 = t240 * t129
  t456 = t239 * t455
  t458 = t15 * t427
  t460 = t21 ** (-0.5e0)
  t462 = t460 * t25 * t452
  t464 = t247 * t455
  t467 = t46 * t16 * t451
  t473 = t280 ** 2
  t476 = t188 ** 2
  t484 = t255 ** 2
  t487 = 0.20000000000000000000000000000000000000000000000000e1 * t154 / t235 / t160 * t484 * t256
  t497 = 0.10000000000000000000000000000000000000000000000000e1 * t237 * (-0.42198333333333333333333333333333333333333333333333e0 * t453 + 0.84396666666666666666666666666666666666666666666666e0 * t456 + 0.39862222222222222222222222222222222222222222222223e0 * t458 + 0.68258333333333333333333333333333333333333333333333e-1 * t462 + 0.13651666666666666666666666666666666666666666666667e0 * t464 + 0.13692777777777777777777777777777777777777777777778e0 * t467) * t256
  t498 = t235 ** 2
  t501 = t163 ** 2
  t505 = 0.16081979498692535066756296899072713062105388428051e2 * t154 / t498 * t484 / t501
  t514 = 0.1e1 / t295 / t198
  t516 = t302 ** 2
  t526 = -0.57538888888888888888888888888888888888888888888889e0 * t453 + 0.11507777777777777777777777777777777777777777777778e1 * t456 + 0.40256666666666666666666666666666666666666666666667e0 * t458 + 0.36677500000000000000000000000000000000000000000000e-1 * t462 + 0.73355000000000000000000000000000000000000000000000e-1 * t464 + 0.13797500000000000000000000000000000000000000000000e0 * t467
  t530 = t295 ** 2
  t531 = 0.1e1 / t530
  t533 = t201 ** 2
  t534 = 0.1e1 / t533
  t538 = -0.70983522622222222222222222222222222222222222222221e-3 * t15 * t427 * t189 - 0.34246666666666666666666666666666666666666666666666e-1 * t57 * t230 * t281 * t289 - 0.20000000000000000000000000000000000000000000000000e1 * t180 / t280 / t185 * t444 * t288 + 0.10000000000000000000000000000000000000000000000000e1 * t282 * (-0.78438333333333333333333333333333333333333333333333e0 * t453 + 0.15687666666666666666666666666666666666666666666667e1 * t456 + 0.68863333333333333333333333333333333333333333333333e0 * t458 + 0.14025833333333333333333333333333333333333333333333e0 * t462 + 0.28051666666666666666666666666666666666666666666667e0 * t464 + 0.17365833333333333333333333333333333333333333333333e0 * t467) * t288 + 0.32163958997385070133512593798145426124210776856102e2 * t180 / t473 * t444 / t476 + t430 + t408 + t487 - t497 - t505 - 0.24415263074675393406472461472505321282722606644045e-3 * t15 * t427 * t202 - 0.10843581300301739842632067522386578331157260943710e-1 * t57 * t230 * t296 * t304 - 0.11696447245269292414524477327518106963944910680856e1 * t193 * t514 * t516 * t303 + 0.58482236226346462072622386637590534819724553404280e0 * t297 * t526 * t303 + 0.17315859105681463759666483083807725165579399831905e2 * t193 * t531 * t516 * t534
  t540 = t168 * t178 * t538
  t542 = 0.8e1 * t264 * t308
  t543 = 0.1e1 / t105
  t544 = t135 ** 2
  t547 = t32 * t76
  t549 = -0.2e1 * t34 + 0.2e1 * t547
  t553 = f.my_piecewise3(t101, 0, 0.4e1 / 0.9e1 * t543 * t544 + 0.4e1 / 0.3e1 * t104 * t549)
  t554 = 0.1e1 / t110
  t555 = t140 ** 2
  t558 = -t549
  t562 = f.my_piecewise3(t108, 0, 0.4e1 / 0.9e1 * t554 * t555 + 0.4e1 / 0.3e1 * t109 * t558)
  t564 = (t553 + t562) * t177
  t566 = t168 * t564 * t205
  t567 = t261 * t275
  t568 = 0.8e1 * t567
  t570 = 0.8e1 * t261 * t308
  t571 = 0.6e1 * t399 * t400 * t401 + 0.2e1 * t95 * t395 - t408 - t411 + t415 - t418 + t423 + t426 - t430 + t433 - t487 + t540 - t542 + t566 + t568 + t570
  t572 = t264 * t275
  t573 = 0.8e1 * t572
  t575 = 0.19751673498613801407483339618206552048944131217655e-1 * t564 * t203
  t576 = t390 ** 2
  t578 = t392 ** 2
  t579 = 0.1e1 / t578
  t582 = t87 ** 2
  t585 = jnp.log(t392)
  t586 = t116 * t585
  t588 = t113 * t585
  t589 = t145 ** 2
  t593 = t6 * t420
  t595 = 0.5e1 / 0.4e1 * t593 * t40
  t601 = 0.7e1 / 0.24e2 * t6 / t18 / t419 * t53 * t58
  t605 = 0.13e2 / 0.144e3 * t6 * t340 * t24 * t68
  t607 = t6 * t10 * t24
  t608 = t607 * t84
  t611 = 0.1e1 / t47 / t419
  t621 = 0.5e1 / 0.2304e4 * t6 * t611 / t22 / t13 / t98 * t56 * t46 * t16
  t625 = t593 * t53 * t65 * t39 / 0.8e1
  t629 = t6 * t44 * t53 * t30 * t39
  t631 = t629 * t83 * t57
  t640 = t6 * t44 * t24 / t30 / t29 * t39 * t344 / 0.192e3
  t644 = t6 * t62 * t24 * t65 * t39
  t646 = t644 * t83 * t67
  t648 = params.omega ** 2
  t649 = t80 ** 2
  t651 = t37 ** 2
  t652 = 0.1e1 / t651
  t657 = 0.2e1 * t34
  t658 = 0.8e1 * t547
  t659 = 0.6e1 * t424
  t661 = f.my_piecewise3(t36, t657 - t658 + t659, 0)
  t672 = -t595 + t601 + t605 + t608 / 0.4e1 - t621 - t625 - t631 / 0.32e2 + t640 - t646 / 0.96e2 - t73 * t56 * t648 * t649 * t652 / 0.64e2 - t73 * t56 * params.omega * t661 * t82 / 0.32e2 + t73 * t56 * params.omega * t649 * t652 / 0.32e2
  t676 = t114 * t585
  t677 = 0.1e1 / t170
  t683 = f.my_piecewise3(t101, 0, -0.2e1 / 0.9e1 * t677 * t544 + 0.2e1 / 0.3e1 * t134 * t549)
  t684 = 0.1e1 / t172
  t690 = f.my_piecewise3(t108, 0, -0.2e1 / 0.9e1 * t684 * t555 + 0.2e1 / 0.3e1 * t139 * t558)
  t692 = t683 / 0.2e1 + t690 / 0.2e1
  t701 = 0.35e2 / 0.432e3 * t3 / t18 / t8 * t120 * t125
  t702 = t119 * t132
  t703 = t702 * t147
  t706 = t130 * t120 * t224
  t716 = 0.1e1 / t216 / t215
  t717 = t716 * t218
  t719 = t152 * t717 * t62
  t720 = t329 ** 2
  t721 = t214 ** 2
  t722 = t720 * t721
  t728 = t152 * t219 * t340
  t729 = t728 * t332
  t732 = t152 * t219 * t365
  t734 = t352 * t12 * t227
  t736 = t214 * t145
  t744 = 0.10843581300301739842632067522386578331157260943710e-1 * t178 * t15 * t231 * t319
  t748 = 0.11696447245269292414524477327518106963944910680856e1 * t317 * t514 * t516 * t303
  t749 = t744 + t748 - t411 - t408 + t497 + t505 + t415 + t575 - t487 + t568 + t570
  t751 = t274 * t193 * t319
  t752 = 0.11696447245269292414524477327518106963944910680856e1 * t751
  t756 = 0.58482236226346462072622386637590534819724553404280e0 * t317 * t296 * t526 * t303
  t760 = 0.17315859105681463759666483083807725165579399831905e2 * t317 * t531 * t516 * t534
  t761 = -t573 - t542 + t566 + t433 + t540 - t752 - t756 - t760 - t430 + t426 - t418 + t423
  t767 = t96 * t352
  t775 = (-(t749 + t761) * t150 * t212 + 0.6e1 * t323 * t326 - 0.12e2 * t211 * t767 * t589 + 0.3e1 * t211 * t325 * t692) * t214
  t780 = t720 * t214
  t789 = 0.119e3 / 0.13824e5 * t338 * t611 * t222 * t224 * t344
  t791 = t152 * t348 * t340
  t792 = t791 * t356
  t797 = t222 / t223 / t114 * t12
  t806 = t701 + 0.7e1 / 0.72e2 * t703 + t706 * t27 * t16 * t589 / 0.16e2 - t133 * t27 * t16 * t692 / 0.48e2 + t719 * t226 * t228 * t722 / 0.1536e4 + 0.7e1 / 0.2304e4 * t729 + t732 * t734 * t17 * t329 * t736 / 0.384e3 - t221 * t226 * t228 * t775 / 0.3072e4 - t221 * t226 * t228 * t780 / 0.3072e4 + t789 + 0.7e1 / 0.576e3 * t792 + 0.5e1 / 0.768e3 * t350 * t797 * t228 * t589 - t350 * t354 * t228 * t692 / 0.768e3
  t809 = t360 * t150
  t814 = t96 / t379 / t373
  t815 = t387 ** 2
  t819 = t716 * t370
  t823 = t217 * t359
  t840 = t97 * t114
  t842 = t840 * t585 * t145
  t845 = -t573 + t575 - t399 * t115 * t576 * t579 + t582 * t91 * t94 * t586 + 0.6e1 * t399 * t588 * t589 + t672 * t91 * t94 * t586 + 0.3e1 * t399 * t676 * t692 + t399 * t115 * (params.beta * t806 * t375 - 0.2e1 * t809 * t388 + 0.2e1 * t378 * t814 * t815 - t378 * t381 * (t151 * t336 * t806 - 0.2e1 * t152 * t823 * t330 - t152 * t382 * t775 - t152 * t382 * t780 + 0.2e1 * t152 * t819 * t722)) * t393 + t497 + t505 + t744 + t748 + 0.6e1 * t95 * t842 - t752 - t756 - t760
  t849 = 0.2e1 * t309
  t850 = 0.20000000000000000000000000000000000000000000000000e1 * t258
  t851 = 0.36622894612013090109708692208757981924083909966068e-3 * t315
  t852 = 0.8e1 * t262
  t853 = 0.8e1 * t265
  t855 = 0.22146941966666666666666666666666666666666666666666e-2 * t233
  t856 = 0.11696447245269292414524477327518106963944910680856e1 * t320
  t857 = t95 * t586
  t860 = t399 * t676 * t145
  t864 = t399 * t115 * t390 * t393
  d11 = t1 * (t571 + t845) + 0.39503346997227602814966679236413104097888262435310e-1 * t310 + t849 + t850 - t851 + t852 - t853 + 0.2e1 * t276 + t855 - t856 + 0.2e1 * t857 + 0.6e1 * t860 + 0.2e1 * t864
  t866 = -t98 - t74
  t869 = f.my_piecewise3(t101, 0, 0.4e1 / 0.3e1 * t104 * t866)
  t870 = -t866
  t873 = f.my_piecewise3(t108, 0, 0.4e1 / 0.3e1 * t109 * t870)
  t875 = (t869 + t873) * t177
  t876 = t875 * t203
  t877 = 0.19751673498613801407483339618206552048944131217655e-1 * t876
  t878 = t875 * t205
  t879 = t168 * t878
  t887 = f.my_piecewise3(t101, 0, 0.4e1 / 0.9e1 * t543 * t866 * t135 + 0.8e1 / 0.3e1 * t104 * t32 * t76)
  t895 = f.my_piecewise3(t108, 0, 0.4e1 / 0.9e1 * t554 * t870 * t140 - 0.8e1 / 0.3e1 * t109 * t32 * t76)
  t897 = (t887 + t895) * t177
  t899 = 0.19751673498613801407483339618206552048944131217655e-1 * t897 * t203
  t900 = 0.18311447306006545054854346104378990962041954983034e-3 * t410
  t901 = 0.4e1 * t567
  t902 = 0.4e1 * t572
  t903 = t261 * t878
  t904 = 0.4e1 * t903
  t905 = t264 * t878
  t906 = 0.4e1 * t905
  t908 = t168 * t897 * t205
  t910 = t168 * t875 * t307
  t913 = f.my_piecewise3(t101, 0, 0.2e1 / 0.3e1 * t134 * t866)
  t916 = f.my_piecewise3(t108, 0, 0.2e1 / 0.3e1 * t139 * t870)
  t918 = t913 / 0.2e1 + t916 / 0.2e1
  t919 = t393 * t918
  t923 = t16 * t918
  t924 = t27 * t923
  t928 = (t234 + t259 - t263 - t266 + t879 + t309 + t877 - t316 - t321) * t150
  t930 = t325 * t918
  t933 = 0.3e1 * t211 * t930 - t928 * t212
  t934 = t933 * t214
  t936 = t226 * t228 * t934
  t940 = t354 * t228 * t918
  t943 = -t127 - t133 * t924 / 0.48e2 - t221 * t936 / 0.3072e4 - t347 - t350 * t940 / 0.768e3
  t944 = params.beta * t943
  t950 = t151 * t336 * t943 - t152 * t382 * t934
  t951 = t381 * t950
  t953 = t944 * t375 - t378 * t951
  t955 = t116 * t953 * t393
  t957 = 0.3e1 * t399 * t400 * t919 + t95 * t955 - t408 + t415 + t423 - t426 - t430 + t432 - t487 + t540 - t542 + t899 - t900 - t901 - t902 + t904 - t906 + t908 + t910
  t959 = t875 * t193 * t319
  t960 = 0.58482236226346462072622386637590534819724553404280e0 * t959
  t963 = f.my_piecewise3(t36, -0.2e1 * t74 - 0.2e1 * t77, 0)
  t965 = params.omega * t963 * t82
  t966 = t56 * t965
  t969 = t42 - t60 - t70 - t73 * t966 / 0.32e2
  t971 = t969 * t91 * t94
  t988 = f.my_piecewise3(t101, 0, -0.2e1 / 0.9e1 * t677 * t866 * t135 + 0.4e1 / 0.3e1 * t134 * t32 * t76)
  t996 = f.my_piecewise3(t108, 0, -0.2e1 / 0.9e1 * t684 * t870 * t140 - 0.4e1 / 0.3e1 * t139 * t32 * t76)
  t998 = t988 / 0.2e1 + t996 / 0.2e1
  t1003 = t702 * t924
  t1016 = t224 * t12 * t227
  t1017 = t17 * t933
  t1018 = t721 * t329
  t1023 = t728 * t936
  t1029 = t899 - t408 - t900 + t415 + t423 - t426 - t430 + t432 + t540 - t487 - t542 - t901 - t902
  t1031 = t875 * t12 * t314
  t1032 = 0.18311447306006545054854346104378990962041954983034e-3 * t1031
  t1033 = 0.58482236226346462072622386637590534819724553404280e0 * t751
  t1034 = t904 - t906 + t908 + t910 - t960 + t497 + t505 + t744 + t748 - t1032 - t1033 - t756 - t760
  t1051 = (-(t1029 + t1034) * t150 * t212 + 0.3e1 * t928 * t326 + 0.3e1 * t323 * t930 - 0.12e2 * t211 * t96 * t352 * t918 * t145 + 0.3e1 * t211 * t325 * t998) * t214
  t1067 = t791 * t940
  t1069 = t918 * t145
  t1078 = t701 + 0.7e1 / 0.144e3 * t703 + 0.7e1 / 0.144e3 * t1003 + t706 * t27 * t923 * t145 / 0.16e2 - t133 * t27 * t16 * t998 / 0.48e2 + t152 * t717 * t365 * t1016 * t1017 * t1018 / 0.1536e4 + 0.7e1 / 0.4608e4 * t1023 + t732 * t734 * t1017 * t736 / 0.768e3 - t221 * t226 * t228 * t1051 / 0.3072e4 - t732 * t1016 * t1017 * t330 / 0.3072e4 + 0.7e1 / 0.4608e4 * t729 + t789 + 0.7e1 / 0.1152e4 * t792 + t732 * t734 * t17 * t918 * t330 / 0.768e3 + 0.7e1 / 0.1152e4 * t1067 + 0.5e1 / 0.768e3 * t350 * t797 * t228 * t1069 - t350 * t354 * t228 * t998 / 0.768e3
  t1081 = t944 * t150
  t1090 = t370 * t933
  t1102 = t217 * t943
  t1117 = t607 * t966
  t1120 = t629 * t965 * t57
  t1123 = t644 * t965 * t67
  t1126 = t6 * t72 * t30
  t1129 = t80 * t652 * t963
  t1134 = f.my_piecewise3(t36, -t657 + t659, 0)
  t1144 = -t595 + t601 + t605 + t608 / 0.8e1 - t621 - t625 - t631 / 0.64e2 + t640 - t646 / 0.192e3 + t1117 / 0.8e1 - t1120 / 0.64e2 - t1123 / 0.192e3 - t1126 * t39 * t648 * t1129 / 0.64e2 - t73 * t56 * params.omega * t1134 * t82 / 0.32e2 + t1126 * t39 * params.omega * t1129 / 0.32e2
  t1148 = t115 * t953
  t1156 = t840 * t585 * t918
  t1159 = t114 * t953
  t1163 = -t960 + 0.3e1 * t971 * t842 + t969 * t87 * t91 * t94 * t97 * t115 * t585 + t971 * t395 + t497 + t505 + 0.3e1 * t399 * t676 * t998 + t399 * t115 * (params.beta * t1078 * t375 - t1081 * t388 - t809 * t951 + 0.2e1 * t378 * t814 * t950 * t387 - t378 * t381 * (0.2e1 * t151 * t96 * t716 * t1090 * t1018 - t151 * t96 * t217 * t1090 * t330 - t152 * t382 * t1051 + t151 * t336 * t1078 - t152 * t1102 * t330 - t152 * t823 * t934)) * t393 + t1144 * t91 * t94 * t586 + t744 + t748 - t399 * t1148 * t579 * t390 + 0.6e1 * t399 * t588 * t1069 + 0.3e1 * t95 * t1156 - t1032 + 0.3e1 * t399 * t1159 * t401 - t1033 - t756 - t760
  t1166 = t971 * t586
  t1168 = t399 * t676 * t918
  t1171 = t399 * t1148 * t393
  d12 = t311 - t851 + t877 + t850 + t276 + t849 + t879 - t853 + t855 + t1 * (t957 + t1163) + t857 + t864 - t856 + t1166 + 0.3e1 * t1168 + t1171 + 0.3e1 * t860
  t1177 = t866 ** 2
  t1181 = 0.2e1 * t34 + 0.2e1 * t547
  t1185 = f.my_piecewise3(t101, 0, 0.4e1 / 0.9e1 * t543 * t1177 + 0.4e1 / 0.3e1 * t104 * t1181)
  t1186 = t870 ** 2
  t1189 = -t1181
  t1193 = f.my_piecewise3(t108, 0, 0.4e1 / 0.9e1 * t554 * t1186 + 0.4e1 / 0.3e1 * t109 * t1189)
  t1195 = (t1185 + t1193) * t177
  t1197 = 0.19751673498613801407483339618206552048944131217655e-1 * t1195 * t203
  t1198 = 0.8e1 * t903
  t1199 = 0.8e1 * t905
  t1200 = 0.2e1 * t910
  t1201 = 0.11696447245269292414524477327518106963944910680856e1 * t959
  t1202 = 0.6e1 * t399 * t1159 * t919 + t1197 - t1198 - t1199 + t1200 - t1201 - t408 + t415 + t418 + t423 + t426 - t430 - t487 + t540 - t542 - t570
  t1208 = f.my_piecewise3(t101, 0, -0.2e1 / 0.9e1 * t677 * t1177 + 0.2e1 / 0.3e1 * t134 * t1181)
  t1214 = f.my_piecewise3(t108, 0, -0.2e1 / 0.9e1 * t684 * t1186 + 0.2e1 / 0.3e1 * t139 * t1189)
  t1216 = t1208 / 0.2e1 + t1214 / 0.2e1
  t1220 = t969 ** 2
  t1224 = t918 ** 2
  t1231 = t963 ** 2
  t1238 = f.my_piecewise3(t36, t657 + t658 + t659, 0)
  t1249 = -t595 + t601 + t605 + t1117 / 0.4e1 - t621 - t625 - t1120 / 0.32e2 + t640 - t1123 / 0.96e2 - t73 * t56 * t648 * t1231 * t652 / 0.64e2 - t73 * t56 * params.omega * t1238 * t82 / 0.32e2 + t73 * t56 * params.omega * t1231 * t652 / 0.32e2
  t1262 = t933 ** 2
  t1263 = t1262 * t721
  t1274 = 0.36622894612013090109708692208757981924083909966068e-3 * t1031
  t1275 = -t1198 - t570 - t760 - t487 + t426 - t1199 - t542 + t1197 + t748 - t1274 - t408
  t1277 = t168 * t1195 * t205
  t1278 = -t430 + t744 + t497 + t505 - t1201 - t756 + t1277 + t1200 + t540 + t418 + t423 + t415
  t1291 = (-(t1275 + t1278) * t150 * t212 + 0.6e1 * t928 * t930 - 0.12e2 * t211 * t767 * t1224 + 0.3e1 * t211 * t325 * t1216) * t214
  t1296 = t1262 * t214
  t1310 = t701 + 0.7e1 / 0.72e2 * t1003 + t706 * t27 * t16 * t1224 / 0.16e2 - t133 * t27 * t16 * t1216 / 0.48e2 + t719 * t226 * t228 * t1263 / 0.1536e4 + 0.7e1 / 0.2304e4 * t1023 + t732 * t734 * t1017 * t214 * t918 / 0.384e3 - t221 * t226 * t228 * t1291 / 0.3072e4 - t221 * t226 * t228 * t1296 / 0.3072e4 + t789 + 0.7e1 / 0.576e3 * t1067 + 0.5e1 / 0.768e3 * t350 * t797 * t228 * t1224 - t350 * t354 * t228 * t1216 / 0.768e3
  t1315 = t950 ** 2
  t1342 = t953 ** 2
  t1346 = t497 + t505 + 0.3e1 * t399 * t676 * t1216 + t1220 * t91 * t94 * t586 + 0.6e1 * t399 * t588 * t1224 + t1249 * t91 * t94 * t586 + t399 * t115 * (params.beta * t1310 * t375 - 0.2e1 * t1081 * t951 + 0.2e1 * t378 * t814 * t1315 - t378 * t381 * (-0.2e1 * t152 * t1102 * t934 + 0.2e1 * t152 * t819 * t1263 - t152 * t382 * t1291 - t152 * t382 * t1296 + t151 * t336 * t1310)) * t393 + t744 + t748 - t1274 + 0.2e1 * t971 * t955 + 0.6e1 * t971 * t1156 - t756 - t760 + t1277 - t399 * t115 * t1342 * t579
  d22 = 0.39503346997227602814966679236413104097888262435310e-1 * t876 + t850 - t851 + t1 * (t1202 + t1346) + t849 - t856 + 0.2e1 * t1166 + 0.6e1 * t1168 + 0.2e1 * t1171 + 0.2e1 * t879 + t855 - t852 - t853
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 + r1
  t3 = s0 + 0.2e1 * s1 + s2
  t4 = jnp.sqrt(t3)
  t6 = params.alpha * t4 * t3
  t7 = t1 ** 2
  t8 = t7 ** 2
  t9 = t8 * t1
  t10 = 0.1e1 / t9
  t12 = 3 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / jnp.pi
  t14 = t13 ** (0.1e1 / 0.3e1)
  t15 = t12 * t14
  t16 = 4 ** (0.1e1 / 0.3e1)
  t17 = t16 ** 2
  t18 = t1 ** (0.1e1 / 0.3e1)
  t21 = t15 * t17 / t18
  t22 = jnp.sqrt(t21)
  t24 = 0.1e1 / t22 / t21
  t25 = t12 ** 2
  t26 = 0.1e1 / t14
  t27 = t25 * t26
  t29 = t27 * t16 * t18
  t30 = jnp.sqrt(t29)
  t32 = r0 - r1
  t33 = t32 ** 2
  t34 = 0.1e1 / t7
  t35 = t33 * t34
  t36 = 0.1e-19 < t35
  t37 = f.my_piecewise3(t36, t35, 0.1e-19)
  t39 = t37 ** (params.omega / 0.2e1)
  t40 = t24 * t30 * t39
  t42 = t6 * t10 * t40 / 0.4e1
  t44 = 0.1e1 / t18 / t9
  t45 = t14 ** 2
  t46 = t25 * t45
  t47 = t18 ** 2
  t50 = t46 * t16 / t47
  t53 = 0.1e1 / t22 / t50 / 0.4e1
  t56 = t30 * t39
  t57 = t15 * t17
  t58 = t56 * t57
  t60 = t6 * t44 * t53 * t58 / 0.32e2
  t62 = 0.1e1 / t47 / t8
  t65 = 0.1e1 / t30
  t67 = t27 * t16
  t68 = t65 * t39 * t67
  t70 = t6 * t62 * t24 * t68 / 0.96e2
  t71 = 0.1e1 / t8
  t72 = t71 * t24
  t73 = t6 * t72
  t74 = t32 * t34
  t75 = t7 * t1
  t76 = 0.1e1 / t75
  t77 = t33 * t76
  t80 = f.my_piecewise3(t36, 0.2e1 * t74 - 0.2e1 * t77, 0)
  t82 = 0.1e1 / t37
  t83 = params.omega * t80 * t82
  t84 = t56 * t83
  t87 = t42 - t60 - t70 - t73 * t84 / 0.32e2
  t91 = jnp.exp(-t6 * t71 * t40 / 0.16e2)
  t93 = jnp.log(0.2e1)
  t94 = 0.1e1 - t93
  t95 = t87 * t91 * t94
  t96 = jnp.pi ** 2
  t97 = 0.1e1 / t96
  t98 = 0.1e1 / t1
  t99 = t32 * t98
  t100 = 0.1e1 + t99
  t101 = t100 <= f.p.zeta_threshold
  t102 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t103 = t102 ** 2
  t104 = t100 ** (0.1e1 / 0.3e1)
  t105 = t104 ** 2
  t106 = f.my_piecewise3(t101, t103, t105)
  t107 = 0.1e1 - t99
  t108 = t107 <= f.p.zeta_threshold
  t109 = t107 ** (0.1e1 / 0.3e1)
  t110 = t109 ** 2
  t111 = f.my_piecewise3(t108, t103, t110)
  t113 = t106 / 0.2e1 + t111 / 0.2e1
  t114 = t113 ** 2
  t115 = t114 * t113
  t116 = t97 * t115
  t119 = t3 / t18 / t75
  t120 = 2 ** (0.1e1 / 0.3e1)
  t125 = 0.1e1 / t114 * t25 * t26 * t16
  t127 = 0.7e1 / 0.288e3 * t119 * t120 * t125
  t129 = 0.1e1 / t18 / t7
  t130 = t3 * t129
  t131 = 0.1e1 / t115
  t132 = t120 * t131
  t133 = t130 * t132
  t134 = 0.1e1 / t104
  t135 = t98 - t74
  t138 = f.my_piecewise3(t101, 0, 0.2e1 / 0.3e1 * t134 * t135)
  t139 = 0.1e1 / t109
  t140 = -t135
  t143 = f.my_piecewise3(t108, 0, 0.2e1 / 0.3e1 * t139 * t140)
  t145 = t138 / 0.2e1 + t143 / 0.2e1
  t147 = t27 * t16 * t145
  t150 = 0.1e1 / t94
  t151 = params.beta * t150
  t152 = t151 * t96
  t154 = 0.1e1 + 0.53425000000000000000000000000000000000000000000000e-1 * t21
  t157 = t21 ** 0.15e1
  t160 = 0.37978500000000000000000000000000000000000000000000e1 * t22 + 0.89690000000000000000000000000000000000000000000000e0 * t21 + 0.20477500000000000000000000000000000000000000000000e0 * t157 + 0.12323500000000000000000000000000000000000000000000e0 * t50
  t163 = 0.1e1 + 0.16081979498692535066756296899072713062105388428051e2 / t160
  t164 = jnp.log(t163)
  t166 = 0.621814e-1 * t154 * t164
  t167 = t33 ** 2
  t168 = t167 * t71
  t169 = t102 * f.p.zeta_threshold
  t170 = t104 * t100
  t171 = f.my_piecewise3(t101, t169, t170)
  t172 = t109 * t107
  t173 = f.my_piecewise3(t108, t169, t172)
  t177 = 0.1e1 / (0.2e1 * t120 - 0.2e1)
  t178 = (t171 + t173 - 0.2e1) * t177
  t180 = 0.1e1 + 0.51370000000000000000000000000000000000000000000000e-1 * t21
  t185 = 0.70594500000000000000000000000000000000000000000000e1 * t22 + 0.15494250000000000000000000000000000000000000000000e1 * t21 + 0.42077500000000000000000000000000000000000000000000e0 * t157 + 0.15629250000000000000000000000000000000000000000000e0 * t50
  t188 = 0.1e1 + 0.32163958997385070133512593798145426124210776856102e2 / t185
  t189 = jnp.log(t188)
  t193 = 0.1e1 + 0.27812500000000000000000000000000000000000000000000e-1 * t21
  t198 = 0.51785000000000000000000000000000000000000000000000e1 * t22 + 0.90577500000000000000000000000000000000000000000000e0 * t21 + 0.11003250000000000000000000000000000000000000000000e0 * t157 + 0.12417750000000000000000000000000000000000000000000e0 * t50
  t201 = 0.1e1 + 0.29608749977793437516654921862508808603118393547661e2 / t198
  t202 = jnp.log(t201)
  t203 = t193 * t202
  t205 = -0.3109070e-1 * t180 * t189 + t166 - 0.19751673498613801407483339618206552048944131217655e-1 * t203
  t206 = t178 * t205
  t211 = (-t166 + t168 * t206 + 0.19751673498613801407483339618206552048944131217655e-1 * t178 * t203) * t150
  t212 = t96 * t131
  t214 = jnp.exp(-t211 * t212)
  t215 = t214 - 0.1e1
  t216 = t215 ** 2
  t217 = 0.1e1 / t216
  t218 = t3 ** 2
  t219 = t217 * t218
  t221 = t152 * t219 * t62
  t222 = t120 ** 2
  t223 = t114 ** 2
  t224 = 0.1e1 / t223
  t226 = t222 * t224 * t12
  t227 = 0.1e1 / t45
  t228 = t227 * t17
  t230 = 0.1e1 / t18 / t1
  t231 = t17 * t230
  t233 = t15 * t231 * t164
  t234 = 0.11073470983333333333333333333333333333333333333333e-2 * t233
  t235 = t160 ** 2
  t236 = 0.1e1 / t235
  t237 = t154 * t236
  t239 = 0.1e1 / t22 * t12
  t240 = t14 * t17
  t241 = t240 * t230
  t242 = t239 * t241
  t244 = t15 * t231
  t246 = t21 ** 0.5e0
  t247 = t246 * t12
  t248 = t247 * t241
  t253 = t46 * t16 / t47 / t1
  t255 = -0.63297500000000000000000000000000000000000000000000e0 * t242 - 0.29896666666666666666666666666666666666666666666667e0 * t244 - 0.10238750000000000000000000000000000000000000000000e0 * t248 - 0.82156666666666666666666666666666666666666666666667e-1 * t253
  t256 = 0.1e1 / t163
  t257 = t255 * t256
  t258 = t237 * t257
  t259 = 0.10000000000000000000000000000000000000000000000000e1 * t258
  t260 = t33 * t32
  t261 = t260 * t71
  t262 = t261 * t206
  t263 = 0.4e1 * t262
  t264 = t167 * t10
  t265 = t264 * t206
  t266 = 0.4e1 * t265
  t269 = f.my_piecewise3(t101, 0, 0.4e1 / 0.3e1 * t104 * t135)
  t272 = f.my_piecewise3(t108, 0, 0.4e1 / 0.3e1 * t109 * t140)
  t274 = (t269 + t272) * t177
  t275 = t274 * t205
  t276 = t168 * t275
  t280 = t185 ** 2
  t281 = 0.1e1 / t280
  t282 = t180 * t281
  t287 = -0.11765750000000000000000000000000000000000000000000e1 * t242 - 0.51647500000000000000000000000000000000000000000000e0 * t244 - 0.21038750000000000000000000000000000000000000000000e0 * t248 - 0.10419500000000000000000000000000000000000000000000e0 * t253
  t288 = 0.1e1 / t188
  t289 = t287 * t288
  t295 = t198 ** 2
  t296 = 0.1e1 / t295
  t297 = t193 * t296
  t302 = -0.86308333333333333333333333333333333333333333333334e0 * t242 - 0.30192500000000000000000000000000000000000000000000e0 * t244 - 0.55016250000000000000000000000000000000000000000000e-1 * t248 - 0.82785000000000000000000000000000000000000000000000e-1 * t253
  t303 = 0.1e1 / t201
  t304 = t302 * t303
  t307 = 0.53237641966666666666666666666666666666666666666666e-3 * t15 * t231 * t189 + 0.10000000000000000000000000000000000000000000000000e1 * t282 * t289 - t234 - t259 + 0.18311447306006545054854346104378990962041954983034e-3 * t15 * t231 * t202 + 0.58482236226346462072622386637590534819724553404280e0 * t297 * t304
  t308 = t178 * t307
  t309 = t168 * t308
  t310 = t274 * t203
  t311 = 0.19751673498613801407483339618206552048944131217655e-1 * t310
  t312 = t178 * t12
  t314 = t240 * t230 * t202
  t315 = t312 * t314
  t316 = 0.18311447306006545054854346104378990962041954983034e-3 * t315
  t317 = t178 * t193
  t319 = t296 * t302 * t303
  t320 = t317 * t319
  t321 = 0.58482236226346462072622386637590534819724553404280e0 * t320
  t323 = (t234 + t259 + t263 - t266 + t276 + t309 + t311 - t316 - t321) * t150
  t325 = t96 * t224
  t326 = t325 * t145
  t329 = 0.3e1 * t211 * t326 - t323 * t212
  t330 = t329 * t214
  t332 = t226 * t228 * t330
  t335 = 0.1e1 / t215
  t336 = t96 * t335
  t338 = t151 * t336 * t218
  t340 = 0.1e1 / t47 / t9
  t344 = t12 * t227 * t17
  t347 = 0.7e1 / 0.4608e4 * t338 * t340 * t222 * t224 * t344
  t348 = t335 * t218
  t350 = t152 * t348 * t62
  t352 = 0.1e1 / t223 / t113
  t354 = t222 * t352 * t12
  t356 = t354 * t228 * t145
  t359 = -t127 - t133 * t147 / 0.48e2 - t221 * t332 / 0.3072e4 - t347 - t350 * t356 / 0.768e3
  t360 = params.beta * t359
  t365 = t62 * t222
  t370 = t130 * t120 * t125 / 0.96e2 + t338 * t365 * t224 * t344 / 0.3072e4
  t373 = t151 * t336 * t370 + 0.1e1
  t375 = t150 * t96 / t373
  t377 = params.beta * t370
  t378 = t377 * t150
  t379 = t373 ** 2
  t381 = t96 / t379
  t382 = t217 * t370
  t387 = t151 * t336 * t359 - t152 * t382 * t330
  t388 = t381 * t387
  t390 = t360 * t375 - t378 * t388
  t392 = t377 * t375 + 0.1e1
  t393 = 0.1e1 / t392
  t395 = t116 * t390 * t393
  t399 = t91 * t94 * t97
  t400 = t114 * t390
  t401 = t393 * t145
  t408 = 0.35616666666666666666666666666666666666666666666666e-1 * t57 * t230 * t236 * t257
  t410 = t274 * t12 * t314
  t411 = 0.36622894612013090109708692208757981924083909966068e-3 * t410
  t415 = 0.24415263074675393406472461472505321282722606644045e-3 * t312 * t240 * t129 * t202
  t417 = t274 * t193 * t319
  t418 = 0.11696447245269292414524477327518106963944910680856e1 * t417
  t422 = 0.1e1 / t47 / t7
  t423 = t45 * t16 * t422
  t424 = t24 * t25 * t423
  t426 = t240 * t129
  t427 = t239 * t426
  t429 = t17 * t129
  t430 = t15 * t429
  t432 = t21 ** (-0.5e0)
  t434 = t432 * t25 * t423
  t436 = t247 * t426
  t439 = t46 * t16 * t422
  t441 = -0.57538888888888888888888888888888888888888888888889e0 * t424 + 0.11507777777777777777777777777777777777777777777778e1 * t427 + 0.40256666666666666666666666666666666666666666666667e0 * t430 + 0.36677500000000000000000000000000000000000000000000e-1 * t434 + 0.73355000000000000000000000000000000000000000000000e-1 * t436 + 0.13797500000000000000000000000000000000000000000000e0 * t439
  t445 = 0.58482236226346462072622386637590534819724553404280e0 * t317 * t296 * t441 * t303
  t446 = t295 ** 2
  t447 = 0.1e1 / t446
  t448 = t302 ** 2
  t450 = t201 ** 2
  t451 = 0.1e1 / t450
  t454 = 0.17315859105681463759666483083807725165579399831905e2 * t317 * t447 * t448 * t451
  t458 = t255 ** 2
  t461 = 0.20000000000000000000000000000000000000000000000000e1 * t154 / t235 / t160 * t458 * t256
  t471 = 0.10000000000000000000000000000000000000000000000000e1 * t237 * (-0.42198333333333333333333333333333333333333333333333e0 * t424 + 0.84396666666666666666666666666666666666666666666666e0 * t427 + 0.39862222222222222222222222222222222222222222222223e0 * t430 + 0.68258333333333333333333333333333333333333333333333e-1 * t434 + 0.13651666666666666666666666666666666666666666666667e0 * t436 + 0.13692777777777777777777777777777777777777777777778e0 * t439) * t256
  t472 = t235 ** 2
  t475 = t163 ** 2
  t479 = 0.16081979498692535066756296899072713062105388428051e2 * t154 / t472 * t458 / t475
  t481 = 0.1e1 / t295 / t198
  t485 = 0.11696447245269292414524477327518106963944910680856e1 * t317 * t481 * t448 * t303
  t486 = t390 ** 2
  t488 = t392 ** 2
  t489 = 0.1e1 / t488
  t492 = t87 ** 2
  t495 = jnp.log(t392)
  t496 = t116 * t495
  t498 = t113 * t495
  t499 = t145 ** 2
  t503 = t8 * t7
  t504 = 0.1e1 / t503
  t505 = t6 * t504
  t507 = 0.5e1 / 0.4e1 * t505 * t40
  t513 = 0.7e1 / 0.24e2 * t6 / t18 / t503 * t53 * t58
  t517 = 0.13e2 / 0.144e3 * t6 * t340 * t24 * t68
  t519 = t6 * t10 * t24
  t520 = t519 * t84
  t523 = 0.1e1 / t47 / t503
  t533 = 0.5e1 / 0.2304e4 * t6 * t523 / t22 / t13 / t98 * t56 * t46 * t16
  t537 = t505 * t53 * t65 * t39 / 0.8e1
  t541 = t6 * t44 * t53 * t30 * t39
  t543 = t541 * t83 * t57
  t552 = t6 * t44 * t24 / t30 / t29 * t39 * t344 / 0.192e3
  t556 = t6 * t62 * t24 * t65 * t39
  t558 = t556 * t83 * t67
  t560 = params.omega ** 2
  t561 = t80 ** 2
  t563 = t37 ** 2
  t564 = 0.1e1 / t563
  t569 = 0.2e1 * t34
  t570 = t32 * t76
  t571 = 0.8e1 * t570
  t572 = t33 * t71
  t573 = 0.6e1 * t572
  t575 = f.my_piecewise3(t36, t569 - t571 + t573, 0)
  t586 = -t507 + t513 + t517 + t520 / 0.4e1 - t533 - t537 - t543 / 0.32e2 + t552 - t558 / 0.96e2 - t73 * t56 * t560 * t561 * t564 / 0.64e2 - t73 * t56 * params.omega * t575 * t82 / 0.32e2 + t73 * t56 * params.omega * t561 * t564 / 0.32e2
  t590 = -t399 * t115 * t486 * t489 + t492 * t91 * t94 * t496 + t586 * t91 * t94 * t496 + 0.6e1 * t399 * t400 * t401 + 0.6e1 * t399 * t498 * t499 + 0.2e1 * t95 * t395 - t408 - t411 + t415 - t418 - t445 - t454 - t461 + t471 + t479 + t485
  t591 = t114 * t495
  t592 = 0.1e1 / t170
  t593 = t135 ** 2
  t597 = -0.2e1 * t34 + 0.2e1 * t570
  t601 = f.my_piecewise3(t101, 0, -0.2e1 / 0.9e1 * t592 * t593 + 0.2e1 / 0.3e1 * t134 * t597)
  t602 = 0.1e1 / t172
  t603 = t140 ** 2
  t606 = -t597
  t610 = f.my_piecewise3(t108, 0, -0.2e1 / 0.9e1 * t602 * t603 + 0.2e1 / 0.3e1 * t139 * t606)
  t612 = t601 / 0.2e1 + t610 / 0.2e1
  t621 = 0.35e2 / 0.432e3 * t3 / t18 / t8 * t120 * t125
  t622 = t119 * t132
  t623 = t622 * t147
  t626 = t130 * t120 * t224
  t636 = 0.1e1 / t216 / t215
  t637 = t636 * t218
  t639 = t152 * t637 * t62
  t640 = t329 ** 2
  t641 = t214 ** 2
  t642 = t640 * t641
  t648 = t152 * t219 * t340
  t649 = t648 * t332
  t652 = t152 * t219 * t365
  t654 = t352 * t12 * t227
  t656 = t214 * t145
  t664 = 0.10843581300301739842632067522386578331157260943710e-1 * t178 * t15 * t231 * t319
  t665 = 0.1e1 / t105
  t671 = f.my_piecewise3(t101, 0, 0.4e1 / 0.9e1 * t665 * t593 + 0.4e1 / 0.3e1 * t104 * t597)
  t672 = 0.1e1 / t110
  t678 = f.my_piecewise3(t108, 0, 0.4e1 / 0.9e1 * t672 * t603 + 0.4e1 / 0.3e1 * t109 * t606)
  t680 = (t671 + t678) * t177
  t682 = 0.19751673498613801407483339618206552048944131217655e-1 * t680 * t203
  t683 = t261 * t275
  t684 = 0.8e1 * t683
  t686 = 0.8e1 * t261 * t308
  t687 = t664 + t485 - t411 - t408 + t471 + t479 + t415 + t682 - t461 + t684 + t686
  t688 = t264 * t275
  t689 = 0.8e1 * t688
  t691 = 0.8e1 * t264 * t308
  t693 = t168 * t680 * t205
  t695 = t168 * t274 * t307
  t696 = 0.2e1 * t695
  t707 = t287 ** 2
  t721 = t280 ** 2
  t724 = t188 ** 2
  t731 = 0.14764627977777777777777777777777777777777777777777e-2 * t15 * t429 * t164
  t750 = -0.70983522622222222222222222222222222222222222222221e-3 * t15 * t429 * t189 - 0.34246666666666666666666666666666666666666666666666e-1 * t57 * t230 * t281 * t289 - 0.20000000000000000000000000000000000000000000000000e1 * t180 / t280 / t185 * t707 * t288 + 0.10000000000000000000000000000000000000000000000000e1 * t282 * (-0.78438333333333333333333333333333333333333333333333e0 * t424 + 0.15687666666666666666666666666666666666666666666667e1 * t427 + 0.68863333333333333333333333333333333333333333333333e0 * t430 + 0.14025833333333333333333333333333333333333333333333e0 * t434 + 0.28051666666666666666666666666666666666666666666667e0 * t436 + 0.17365833333333333333333333333333333333333333333333e0 * t439) * t288 + 0.32163958997385070133512593798145426124210776856102e2 * t180 / t721 * t707 / t724 + t731 + t408 + t461 - t471 - t479 - 0.24415263074675393406472461472505321282722606644045e-3 * t15 * t429 * t202 - 0.10843581300301739842632067522386578331157260943710e-1 * t57 * t230 * t296 * t304 - 0.11696447245269292414524477327518106963944910680856e1 * t193 * t481 * t448 * t303 + 0.58482236226346462072622386637590534819724553404280e0 * t297 * t441 * t303 + 0.17315859105681463759666483083807725165579399831905e2 * t193 * t447 * t448 * t451
  t752 = t168 * t178 * t750
  t754 = 0.12e2 * t572 * t206
  t757 = 0.32e2 * t260 * t10 * t206
  t760 = 0.20e2 * t167 * t504 * t206
  t761 = -t689 - t691 + t693 + t696 + t752 - t418 - t445 - t454 - t731 + t754 - t757 + t760
  t767 = t96 * t352
  t775 = (-(t687 + t761) * t150 * t212 + 0.6e1 * t323 * t326 - 0.12e2 * t211 * t767 * t499 + 0.3e1 * t211 * t325 * t612) * t214
  t780 = t640 * t214
  t789 = 0.119e3 / 0.13824e5 * t338 * t523 * t222 * t224 * t344
  t791 = t152 * t348 * t340
  t792 = t791 * t356
  t797 = t222 / t223 / t114 * t12
  t806 = t621 + 0.7e1 / 0.72e2 * t623 + t626 * t27 * t16 * t499 / 0.16e2 - t133 * t27 * t16 * t612 / 0.48e2 + t639 * t226 * t228 * t642 / 0.1536e4 + 0.7e1 / 0.2304e4 * t649 + t652 * t654 * t17 * t329 * t656 / 0.384e3 - t221 * t226 * t228 * t775 / 0.3072e4 - t221 * t226 * t228 * t780 / 0.3072e4 + t789 + 0.7e1 / 0.576e3 * t792 + 0.5e1 / 0.768e3 * t350 * t797 * t228 * t499 - t350 * t354 * t228 * t612 / 0.768e3
  t809 = t360 * t150
  t814 = t96 / t379 / t373
  t815 = t387 ** 2
  t819 = t636 * t370
  t823 = t217 * t359
  t840 = t97 * t114
  t842 = t840 * t495 * t145
  t845 = 0.3e1 * t399 * t591 * t612 + t399 * t115 * (params.beta * t806 * t375 - 0.2e1 * t809 * t388 + 0.2e1 * t378 * t814 * t815 - t378 * t381 * (t151 * t336 * t806 - 0.2e1 * t152 * t823 * t330 - t152 * t382 * t775 - t152 * t382 * t780 + 0.2e1 * t152 * t819 * t642)) * t393 + t664 + t754 - t757 + t760 - t731 + t696 + t752 - t691 + t693 + t686 - t689 + t684 + t682 + 0.6e1 * t95 * t842
  t849 = 0.2e1 * t309
  t850 = 0.20000000000000000000000000000000000000000000000000e1 * t258
  t851 = 0.36622894612013090109708692208757981924083909966068e-3 * t315
  t852 = 0.8e1 * t262
  t853 = 0.8e1 * t265
  t855 = 0.22146941966666666666666666666666666666666666666666e-2 * t233
  t856 = 0.11696447245269292414524477327518106963944910680856e1 * t320
  t857 = t95 * t496
  t860 = t399 * t591 * t145
  t864 = t399 * t115 * t390 * t393
  d11 = t1 * (t590 + t845) + 0.39503346997227602814966679236413104097888262435310e-1 * t310 + t849 + t850 - t851 + t852 - t853 + 0.2e1 * t276 + t855 - t856 + 0.2e1 * t857 + 0.6e1 * t860 + 0.2e1 * t864
  t866 = 0.18311447306006545054854346104378990962041954983034e-3 * t410
  t867 = -t98 - t74
  t870 = f.my_piecewise3(t101, 0, 0.2e1 / 0.3e1 * t134 * t867)
  t871 = -t867
  t874 = f.my_piecewise3(t108, 0, 0.2e1 / 0.3e1 * t139 * t871)
  t876 = t870 / 0.2e1 + t874 / 0.2e1
  t877 = t16 * t876
  t878 = t27 * t877
  t883 = f.my_piecewise3(t101, 0, 0.4e1 / 0.3e1 * t104 * t867)
  t886 = f.my_piecewise3(t108, 0, 0.4e1 / 0.3e1 * t109 * t871)
  t888 = (t883 + t886) * t177
  t889 = t888 * t205
  t890 = t168 * t889
  t891 = t888 * t203
  t892 = 0.19751673498613801407483339618206552048944131217655e-1 * t891
  t894 = (t234 + t259 - t263 - t266 + t890 + t309 + t892 - t316 - t321) * t150
  t896 = t325 * t876
  t899 = 0.3e1 * t211 * t896 - t894 * t212
  t900 = t899 * t214
  t902 = t226 * t228 * t900
  t906 = t354 * t228 * t876
  t909 = -t127 - t133 * t878 / 0.48e2 - t221 * t902 / 0.3072e4 - t347 - t350 * t906 / 0.768e3
  t910 = params.beta * t909
  t916 = t151 * t336 * t909 - t152 * t382 * t900
  t917 = t381 * t916
  t919 = t910 * t375 - t378 * t917
  t920 = t115 * t919
  t924 = t393 * t876
  t929 = t116 * t919 * t393
  t932 = t888 * t12 * t314
  t933 = 0.18311447306006545054854346104378990962041954983034e-3 * t932
  t934 = t114 * t919
  t940 = f.my_piecewise3(t36, -0.2e1 * t74 - 0.2e1 * t77, 0)
  t942 = params.omega * t940 * t82
  t943 = t56 * t942
  t946 = t42 - t60 - t70 - t73 * t943 / 0.32e2
  t948 = t946 * t91 * t94
  t958 = 0.58482236226346462072622386637590534819724553404280e0 * t417
  t959 = t876 * t145
  t964 = t840 * t495 * t876
  t967 = -t408 - t866 + t415 - t399 * t920 * t489 * t390 + 0.3e1 * t399 * t400 * t924 + t95 * t929 - t933 + 0.3e1 * t399 * t934 * t401 + 0.3e1 * t948 * t842 + t946 * t87 * t91 * t94 * t97 * t115 * t495 + t948 * t395 - t958 - t445 - t454 - t461 + t471 + t479 + 0.6e1 * t399 * t498 * t959 + 0.3e1 * t95 * t964
  t969 = t888 * t193 * t319
  t970 = 0.58482236226346462072622386637590534819724553404280e0 * t969
  t978 = f.my_piecewise3(t101, 0, -0.2e1 / 0.9e1 * t592 * t867 * t135 + 0.4e1 / 0.3e1 * t134 * t32 * t76)
  t986 = f.my_piecewise3(t108, 0, -0.2e1 / 0.9e1 * t602 * t871 * t140 - 0.4e1 / 0.3e1 * t139 * t32 * t76)
  t988 = t978 / 0.2e1 + t986 / 0.2e1
  t993 = t622 * t878
  t1006 = t224 * t12 * t227
  t1007 = t17 * t899
  t1008 = t641 * t329
  t1013 = t648 * t902
  t1019 = -t408 - t866 + t415 - t933 - t958 - t445 - t454 - t461 + t471 + t479 + t485 - t970 + t664
  t1020 = 0.4e1 * t688
  t1021 = 0.4e1 * t683
  t1029 = f.my_piecewise3(t101, 0, 0.4e1 / 0.9e1 * t665 * t867 * t135 + 0.8e1 / 0.3e1 * t104 * t32 * t76)
  t1037 = f.my_piecewise3(t108, 0, 0.4e1 / 0.9e1 * t672 * t871 * t140 - 0.8e1 / 0.3e1 * t109 * t32 * t76)
  t1039 = (t1029 + t1037) * t177
  t1041 = 0.19751673498613801407483339618206552048944131217655e-1 * t1039 * t203
  t1042 = t264 * t889
  t1043 = 0.4e1 * t1042
  t1045 = t168 * t1039 * t205
  t1047 = t168 * t888 * t307
  t1048 = t261 * t889
  t1049 = 0.4e1 * t1048
  t1050 = -t754 + t760 - t731 + t695 + t752 - t691 - t1020 - t1021 + t1041 - t1043 + t1045 + t1047 + t1049
  t1067 = (-(t1019 + t1050) * t150 * t212 + 0.3e1 * t894 * t326 + 0.3e1 * t323 * t896 - 0.12e2 * t211 * t96 * t352 * t876 * t145 + 0.3e1 * t211 * t325 * t988) * t214
  t1083 = t791 * t906
  t1093 = t621 + 0.7e1 / 0.144e3 * t623 + 0.7e1 / 0.144e3 * t993 + t626 * t27 * t877 * t145 / 0.16e2 - t133 * t27 * t16 * t988 / 0.48e2 + t152 * t637 * t365 * t1006 * t1007 * t1008 / 0.1536e4 + 0.7e1 / 0.4608e4 * t1013 + t652 * t654 * t1007 * t656 / 0.768e3 - t221 * t226 * t228 * t1067 / 0.3072e4 - t652 * t1006 * t1007 * t330 / 0.3072e4 + 0.7e1 / 0.4608e4 * t649 + t789 + 0.7e1 / 0.1152e4 * t792 + t652 * t654 * t17 * t876 * t330 / 0.768e3 + 0.7e1 / 0.1152e4 * t1083 + 0.5e1 / 0.768e3 * t350 * t797 * t228 * t959 - t350 * t354 * t228 * t988 / 0.768e3
  t1096 = t910 * t150
  t1105 = t370 * t899
  t1117 = t217 * t909
  t1132 = t519 * t943
  t1135 = t541 * t942 * t57
  t1138 = t556 * t942 * t67
  t1141 = t6 * t72 * t30
  t1144 = t80 * t564 * t940
  t1149 = f.my_piecewise3(t36, -t569 + t573, 0)
  t1159 = -t507 + t513 + t517 + t520 / 0.8e1 - t533 - t537 - t543 / 0.64e2 + t552 - t558 / 0.192e3 + t1132 / 0.8e1 - t1135 / 0.64e2 - t1138 / 0.192e3 - t1141 * t39 * t560 * t1144 / 0.64e2 - t73 * t56 * params.omega * t1149 * t82 / 0.32e2 + t1141 * t39 * params.omega * t1144 / 0.32e2
  t1163 = t485 - t970 + 0.3e1 * t399 * t591 * t988 + t399 * t115 * (params.beta * t1093 * t375 - t1096 * t388 - t809 * t917 + 0.2e1 * t378 * t814 * t916 * t387 - t378 * t381 * (0.2e1 * t151 * t96 * t636 * t1105 * t1008 - t151 * t96 * t217 * t1105 * t330 - t152 * t382 * t1067 + t151 * t336 * t1093 - t152 * t1117 * t330 - t152 * t823 * t900)) * t393 + t664 - t754 + t760 - t731 + t695 + t752 - t691 - t1020 - t1021 + t1041 + t1159 * t91 * t94 * t496 - t1043 + t1045 + t1047 + t1049
  t1166 = t948 * t496
  t1168 = t399 * t591 * t876
  t1171 = t399 * t920 * t393
  d12 = -t851 + t1 * (t967 + t1163) + t311 + t276 + t849 + t890 - t853 + t855 + t857 + t864 + t892 - t856 + t1166 + 0.3e1 * t1168 + t850 + t1171 + 0.3e1 * t860
  t1177 = t867 ** 2
  t1181 = 0.2e1 * t34 + 0.2e1 * t570
  t1185 = f.my_piecewise3(t101, 0, 0.4e1 / 0.9e1 * t665 * t1177 + 0.4e1 / 0.3e1 * t104 * t1181)
  t1186 = t871 ** 2
  t1189 = -t1181
  t1193 = f.my_piecewise3(t108, 0, 0.4e1 / 0.9e1 * t672 * t1186 + 0.4e1 / 0.3e1 * t109 * t1189)
  t1195 = (t1185 + t1193) * t177
  t1197 = t168 * t1195 * t205
  t1201 = t940 ** 2
  t1208 = f.my_piecewise3(t36, t569 + t571 + t573, 0)
  t1219 = -t507 + t513 + t517 + t1132 / 0.4e1 - t533 - t537 - t1135 / 0.32e2 + t552 - t1138 / 0.96e2 - t73 * t56 * t560 * t1201 * t564 / 0.64e2 - t73 * t56 * params.omega * t1208 * t82 / 0.32e2 + t73 * t56 * params.omega * t1201 * t564 / 0.32e2
  t1228 = f.my_piecewise3(t101, 0, -0.2e1 / 0.9e1 * t592 * t1177 + 0.2e1 / 0.3e1 * t134 * t1181)
  t1234 = f.my_piecewise3(t108, 0, -0.2e1 / 0.9e1 * t602 * t1186 + 0.2e1 / 0.3e1 * t139 * t1189)
  t1236 = t1228 / 0.2e1 + t1234 / 0.2e1
  t1241 = t876 ** 2
  t1250 = t899 ** 2
  t1251 = t1250 * t641
  t1262 = 0.2e1 * t1047
  t1263 = 0.8e1 * t1042
  t1265 = 0.19751673498613801407483339618206552048944131217655e-1 * t1195 * t203
  t1266 = 0.36622894612013090109708692208757981924083909966068e-3 * t932
  t1267 = t664 + t485 + t1197 + t1262 + t754 - t1263 - t691 - t461 + t1265 - t1266 - t408
  t1268 = 0.11696447245269292414524477327518106963944910680856e1 * t969
  t1269 = 0.8e1 * t1048
  t1270 = -t1268 - t445 - t731 - t686 + t752 - t1269 + t471 + t479 + t757 + t760 - t454 + t415
  t1283 = (-(t1267 + t1270) * t150 * t212 + 0.6e1 * t894 * t896 - 0.12e2 * t211 * t767 * t1241 + 0.3e1 * t211 * t325 * t1236) * t214
  t1288 = t1250 * t214
  t1302 = t621 + 0.7e1 / 0.72e2 * t993 + t626 * t27 * t16 * t1241 / 0.16e2 - t133 * t27 * t16 * t1236 / 0.48e2 + t639 * t226 * t228 * t1251 / 0.1536e4 + 0.7e1 / 0.2304e4 * t1013 + t652 * t654 * t1007 * t214 * t876 / 0.384e3 - t221 * t226 * t228 * t1283 / 0.3072e4 - t221 * t226 * t228 * t1288 / 0.3072e4 + t789 + 0.7e1 / 0.576e3 * t1083 + 0.5e1 / 0.768e3 * t350 * t797 * t228 * t1241 - t350 * t354 * t228 * t1236 / 0.768e3
  t1307 = t916 ** 2
  t1330 = t946 ** 2
  t1344 = t919 ** 2
  t1348 = t1197 - t408 + t415 + t1219 * t91 * t94 * t496 + 0.3e1 * t399 * t591 * t1236 + t399 * t115 * (params.beta * t1302 * t375 - 0.2e1 * t1096 * t917 + 0.2e1 * t378 * t814 * t1307 - t378 * t381 * (-0.2e1 * t152 * t1117 * t900 + 0.2e1 * t152 * t819 * t1251 - t152 * t382 * t1283 - t152 * t382 * t1288 + t151 * t336 * t1302)) * t393 + t1330 * t91 * t94 * t496 + 0.6e1 * t399 * t498 * t1241 + 0.2e1 * t948 * t929 + 0.6e1 * t399 * t934 * t924 + 0.6e1 * t948 * t964 - t1266 - t445 - t454 - t399 * t115 * t1344 * t489 - t461
  t1349 = t471 + t479 + t485 - t1268 + t664 + t754 + t757 + t760 - t731 + t752 - t691 - t686 + t1265 - t1263 + t1262 - t1269
  d22 = 0.39503346997227602814966679236413104097888262435310e-1 * t891 + t850 + t849 + 0.2e1 * t890 - t856 + 0.2e1 * t1166 + 0.6e1 * t1168 + t855 - t852 - t853 - t851 + t1 * (t1348 + t1349) + 0.2e1 * t1171
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

