"""Generated from mgga_c_m08.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
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
  params_m08_a_raw = params.m08_a
  if isinstance(params_m08_a_raw, (str, bytes, dict)):
    params_m08_a = params_m08_a_raw
  else:
    try:
      params_m08_a_seq = list(params_m08_a_raw)
    except TypeError:
      params_m08_a = params_m08_a_raw
    else:
      params_m08_a_seq = np.asarray(params_m08_a_seq, dtype=np.float64)
      params_m08_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_m08_a_seq))
  params_m08_b_raw = params.m08_b
  if isinstance(params_m08_b_raw, (str, bytes, dict)):
    params_m08_b = params_m08_b_raw
  else:
    try:
      params_m08_b_seq = list(params_m08_b_raw)
    except TypeError:
      params_m08_b = params_m08_b_raw
    else:
      params_m08_b_seq = np.asarray(params_m08_b_seq, dtype=np.float64)
      params_m08_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_m08_b_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  params_beta = 0.06672455060314922

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  mbeta = lambda rs=None, t=None: params_beta

  mgamma = params_gamma

  BB = params_BB

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  m08_f = lambda rs, z, xt, xs0, xs1, ts0, ts1: +mgga_series_w(params_m08_a, 12, 2 ** (2 / 3) * f.t_total(z, ts0, ts1)) * f_pw(rs, z) + mgga_series_w(params_m08_b, 12, 2 ** (2 / 3) * f.t_total(z, ts0, ts1)) * (f_pbe(rs, z, xt, xs0, xs1) - f_pw(rs, z))

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: m08_f(rs, z, xt, xs0, xs1, ts0, ts1)

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
  params_m08_a_raw = params.m08_a
  if isinstance(params_m08_a_raw, (str, bytes, dict)):
    params_m08_a = params_m08_a_raw
  else:
    try:
      params_m08_a_seq = list(params_m08_a_raw)
    except TypeError:
      params_m08_a = params_m08_a_raw
    else:
      params_m08_a_seq = np.asarray(params_m08_a_seq, dtype=np.float64)
      params_m08_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_m08_a_seq))
  params_m08_b_raw = params.m08_b
  if isinstance(params_m08_b_raw, (str, bytes, dict)):
    params_m08_b = params_m08_b_raw
  else:
    try:
      params_m08_b_seq = list(params_m08_b_raw)
    except TypeError:
      params_m08_b = params_m08_b_raw
    else:
      params_m08_b_seq = np.asarray(params_m08_b_seq, dtype=np.float64)
      params_m08_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_m08_b_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  params_beta = 0.06672455060314922

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  mbeta = lambda rs=None, t=None: params_beta

  mgamma = params_gamma

  BB = params_BB

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  m08_f = lambda rs, z, xt, xs0, xs1, ts0, ts1: +mgga_series_w(params_m08_a, 12, 2 ** (2 / 3) * f.t_total(z, ts0, ts1)) * f_pw(rs, z) + mgga_series_w(params_m08_b, 12, 2 ** (2 / 3) * f.t_total(z, ts0, ts1)) * (f_pbe(rs, z, xt, xs0, xs1) - f_pw(rs, z))

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: m08_f(rs, z, xt, xs0, xs1, ts0, ts1)

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
  params_m08_a_raw = params.m08_a
  if isinstance(params_m08_a_raw, (str, bytes, dict)):
    params_m08_a = params_m08_a_raw
  else:
    try:
      params_m08_a_seq = list(params_m08_a_raw)
    except TypeError:
      params_m08_a = params_m08_a_raw
    else:
      params_m08_a_seq = np.asarray(params_m08_a_seq, dtype=np.float64)
      params_m08_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_m08_a_seq))
  params_m08_b_raw = params.m08_b
  if isinstance(params_m08_b_raw, (str, bytes, dict)):
    params_m08_b = params_m08_b_raw
  else:
    try:
      params_m08_b_seq = list(params_m08_b_raw)
    except TypeError:
      params_m08_b = params_m08_b_raw
    else:
      params_m08_b_seq = np.asarray(params_m08_b_seq, dtype=np.float64)
      params_m08_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_m08_b_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  params_beta = 0.06672455060314922

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  mbeta = lambda rs=None, t=None: params_beta

  mgamma = params_gamma

  BB = params_BB

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  m08_f = lambda rs, z, xt, xs0, xs1, ts0, ts1: +mgga_series_w(params_m08_a, 12, 2 ** (2 / 3) * f.t_total(z, ts0, ts1)) * f_pw(rs, z) + mgga_series_w(params_m08_b, 12, 2 ** (2 / 3) * f.t_total(z, ts0, ts1)) * (f_pbe(rs, z, xt, xs0, xs1) - f_pw(rs, z))

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: m08_f(rs, z, xt, xs0, xs1, ts0, ts1)

  t2 = params.m08_a[1]
  t3 = 6 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** 2
  t6 = t5 ** (0.1e1 / 0.3e1)
  t7 = t6 ** 2
  t9 = 0.3e1 / 0.10e2 * t4 * t7
  t10 = 2 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = r0 ** (0.1e1 / 0.3e1)
  t13 = t12 ** 2
  t15 = 0.1e1 / t13 / r0
  t16 = tau0 * t15
  t17 = r0 - r1
  t18 = r0 + r1
  t19 = 0.1e1 / t18
  t20 = t17 * t19
  t21 = 0.1e1 + t20
  t22 = t21 / 0.2e1
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = t24 * t22
  t27 = r1 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t30 = 0.1e1 / t28 / r1
  t31 = tau1 * t30
  t32 = 0.1e1 - t20
  t33 = t32 / 0.2e1
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = t35 * t33
  t39 = t11 * (t16 * t25 + t31 * t36)
  t40 = t9 - t39
  t41 = t2 * t40
  t42 = t9 + t39
  t43 = 0.1e1 / t42
  t45 = params.m08_a[2]
  t46 = t40 ** 2
  t47 = t45 * t46
  t48 = t42 ** 2
  t49 = 0.1e1 / t48
  t51 = params.m08_a[3]
  t52 = t46 * t40
  t53 = t51 * t52
  t54 = t48 * t42
  t55 = 0.1e1 / t54
  t57 = params.m08_a[4]
  t58 = t46 ** 2
  t59 = t57 * t58
  t60 = t48 ** 2
  t61 = 0.1e1 / t60
  t63 = params.m08_a[5]
  t64 = t58 * t40
  t65 = t63 * t64
  t67 = 0.1e1 / t60 / t42
  t69 = params.m08_a[6]
  t70 = t58 * t46
  t71 = t69 * t70
  t73 = 0.1e1 / t60 / t48
  t75 = params.m08_a[7]
  t76 = t58 * t52
  t77 = t75 * t76
  t79 = 0.1e1 / t60 / t54
  t81 = params.m08_a[8]
  t82 = t58 ** 2
  t83 = t81 * t82
  t84 = t60 ** 2
  t85 = 0.1e1 / t84
  t87 = params.m08_a[9]
  t88 = t82 * t40
  t89 = t87 * t88
  t91 = 0.1e1 / t84 / t42
  t93 = params.m08_a[10]
  t94 = t82 * t46
  t95 = t93 * t94
  t97 = 0.1e1 / t84 / t48
  t99 = params.m08_a[11]
  t100 = t82 * t52
  t101 = t99 * t100
  t103 = 0.1e1 / t84 / t54
  t105 = t101 * t103 + t41 * t43 + t47 * t49 + t53 * t55 + t59 * t61 + t65 * t67 + t71 * t73 + t77 * t79 + t83 * t85 + t89 * t91 + t95 * t97 + params.m08_a[0]
  t106 = 3 ** (0.1e1 / 0.3e1)
  t108 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t109 = t106 * t108
  t110 = 4 ** (0.1e1 / 0.3e1)
  t111 = t110 ** 2
  t112 = t18 ** (0.1e1 / 0.3e1)
  t115 = t109 * t111 / t112
  t117 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t115
  t118 = jnp.sqrt(t115)
  t121 = t115 ** 0.15e1
  t123 = t106 ** 2
  t124 = t108 ** 2
  t125 = t123 * t124
  t126 = t112 ** 2
  t129 = t125 * t110 / t126
  t131 = 0.23615562999000000000000000000000000000000000000000e0 * t118 + 0.55770497660000000000000000000000000000000000000000e-1 * t115 + 0.12733196185000000000000000000000000000000000000000e-1 * t121 + 0.76629248290000000000000000000000000000000000000000e-2 * t129
  t133 = 0.1e1 + 0.1e1 / t131
  t134 = jnp.log(t133)
  t135 = t117 * t134
  t136 = t17 ** 2
  t137 = t136 ** 2
  t138 = t18 ** 2
  t139 = t138 ** 2
  t140 = 0.1e1 / t139
  t141 = t137 * t140
  t142 = t21 <= f.p.zeta_threshold
  t143 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t144 = t143 * f.p.zeta_threshold
  t145 = t21 ** (0.1e1 / 0.3e1)
  t147 = f.my_piecewise3(t142, t144, t145 * t21)
  t148 = t32 <= f.p.zeta_threshold
  t149 = t32 ** (0.1e1 / 0.3e1)
  t151 = f.my_piecewise3(t148, t144, t149 * t32)
  t155 = 0.1e1 / (0.2e1 * t10 - 0.2e1)
  t156 = (t147 + t151 - 0.2e1) * t155
  t158 = 0.3109070e-1 + 0.15971292590000000000000000000000000000000000000000e-2 * t115
  t163 = 0.21948324211500000000000000000000000000000000000000e0 * t118 + 0.48172707847500000000000000000000000000000000000000e-1 * t115 + 0.13082189292500000000000000000000000000000000000000e-1 * t121 + 0.48592432297500000000000000000000000000000000000000e-2 * t129
  t165 = 0.1e1 + 0.1e1 / t163
  t166 = jnp.log(t165)
  t169 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t115
  t174 = 0.17489762330000000000000000000000000000000000000000e0 * t118 + 0.30591463695000000000000000000000000000000000000000e-1 * t115 + 0.37162156485000000000000000000000000000000000000000e-2 * t121 + 0.41939460495000000000000000000000000000000000000000e-2 * t129
  t176 = 0.1e1 + 0.1e1 / t174
  t177 = jnp.log(t176)
  t178 = t169 * t177
  t180 = -t158 * t166 + t135 - 0.58482236226346462072622386637590534819724553404281e0 * t178
  t181 = t156 * t180
  t185 = -t135 + t141 * t181 + 0.58482236226346462072622386637590534819724553404281e0 * t156 * t178
  t186 = t105 * t185
  t188 = params.m08_b[1]
  t189 = t188 * t40
  t191 = params.m08_b[2]
  t192 = t191 * t46
  t194 = params.m08_b[3]
  t195 = t194 * t52
  t197 = params.m08_b[4]
  t198 = t197 * t58
  t200 = params.m08_b[5]
  t201 = t200 * t64
  t203 = params.m08_b[6]
  t204 = t203 * t70
  t206 = params.m08_b[7]
  t207 = t206 * t76
  t209 = params.m08_b[8]
  t210 = t209 * t82
  t212 = params.m08_b[9]
  t213 = t212 * t88
  t215 = params.m08_b[10]
  t216 = t215 * t94
  t218 = params.m08_b[11]
  t219 = t218 * t100
  t221 = t219 * t103 + t189 * t43 + t192 * t49 + t195 * t55 + t198 * t61 + t201 * t67 + t204 * t73 + t207 * t79 + t210 * t85 + t213 * t91 + t216 * t97 + params.m08_b[0]
  t222 = jnp.log(0.2e1)
  t223 = 0.1e1 - t222
  t224 = t221 * t223
  t225 = 0.1e1 / t5
  t226 = t143 ** 2
  t227 = t145 ** 2
  t228 = f.my_piecewise3(t142, t226, t227)
  t229 = t149 ** 2
  t230 = f.my_piecewise3(t148, t226, t229)
  t232 = t228 / 0.2e1 + t230 / 0.2e1
  t233 = t232 ** 2
  t234 = t233 * t232
  t235 = t225 * t234
  t237 = s0 + 0.2e1 * s1 + s2
  t239 = 0.1e1 / t112 / t138
  t240 = t237 * t239
  t242 = 0.1e1 / t233
  t244 = 0.1e1 / t108
  t246 = t242 * t123 * t244 * t110
  t247 = t240 * t10 * t246
  t249 = 0.1e1 / t223
  t250 = t249 * t5
  t251 = t185 * t249
  t252 = 0.1e1 / t234
  t253 = t5 * t252
  t255 = jnp.exp(-t251 * t253)
  t256 = t255 - 0.1e1
  t257 = 0.1e1 / t256
  t258 = t237 ** 2
  t259 = t257 * t258
  t261 = 0.1e1 / t126 / t139
  t263 = t250 * t259 * t261
  t264 = t233 ** 2
  t265 = 0.1e1 / t264
  t267 = 0.1e1 / t124
  t270 = t11 * t265 * t106 * t267 * t111
  t271 = t263 * t270
  t273 = 0.69504740211613770833333333333333333333333333333333e-3 * t247 + 0.14492726735651760867483664018907552083333333333334e-5 * t271
  t274 = t273 * t249
  t277 = t247 / 0.96e2 + 0.21720231316129303385416666666666666666666666666667e-4 * t271
  t281 = 0.1e1 + 0.6672455060314922e-1 * t250 * t257 * t277
  t283 = t5 / t281
  t285 = t274 * t283 + 0.1e1
  t286 = jnp.log(t285)
  t287 = t235 * t286
  t288 = t224 * t287
  t289 = t2 * t11
  t290 = r0 ** 2
  t296 = t17 / t138
  t297 = t19 - t296
  t298 = t297 / 0.2e1
  t305 = -0.5e1 / 0.3e1 * tau0 / t13 / t290 * t25 + 0.5e1 / 0.3e1 * t16 * t24 * t298 - 0.5e1 / 0.3e1 * t31 * t35 * t298
  t306 = t305 * t43
  t308 = t49 * t11
  t309 = t308 * t305
  t311 = t45 * t40
  t314 = t55 * t11
  t315 = t314 * t305
  t318 = t51 * t46
  t321 = t61 * t11
  t322 = t321 * t305
  t325 = t57 * t52
  t328 = t67 * t11
  t329 = t328 * t305
  t332 = t63 * t58
  t335 = t73 * t11
  t336 = t335 * t305
  t339 = t69 * t64
  t342 = -t289 * t306 - 0.2e1 * t311 * t309 - t41 * t309 - 0.3e1 * t318 * t315 - 0.2e1 * t47 * t315 - 0.4e1 * t325 * t322 - 0.3e1 * t53 * t322 - 0.5e1 * t332 * t329 - 0.4e1 * t59 * t329 - 0.6e1 * t339 * t336 - 0.5e1 * t65 * t336
  t343 = t79 * t11
  t344 = t343 * t305
  t347 = t75 * t70
  t350 = t85 * t11
  t351 = t350 * t305
  t354 = t81 * t76
  t357 = t91 * t11
  t358 = t357 * t305
  t361 = t87 * t82
  t364 = t97 * t11
  t365 = t364 * t305
  t368 = t93 * t88
  t371 = t103 * t11
  t372 = t371 * t305
  t375 = t99 * t94
  t379 = 0.1e1 / t84 / t60
  t380 = t379 * t11
  t381 = t380 * t305
  t384 = -0.11e2 * t101 * t381 - 0.7e1 * t347 * t344 - 0.6e1 * t71 * t344 - 0.8e1 * t354 * t351 - 0.7e1 * t77 * t351 - 0.9e1 * t361 * t358 - 0.8e1 * t83 * t358 - 0.10e2 * t368 * t365 - 0.9e1 * t89 * t365 - 0.11e2 * t375 * t372 - 0.10e2 * t95 * t372
  t388 = 0.1e1 / t112 / t18
  t389 = t111 * t388
  t392 = 0.11073470983333333333333333333333333333333333333333e-2 * t109 * t389 * t134
  t393 = t131 ** 2
  t398 = t108 * t111
  t399 = t398 * t388
  t400 = 0.1e1 / t118 * t106 * t399
  t402 = t109 * t389
  t404 = t115 ** 0.5e0
  t406 = t404 * t106 * t399
  t411 = t125 * t110 / t126 / t18
  t416 = t117 / t393 * (-0.39359271665000000000000000000000000000000000000000e-1 * t400 - 0.18590165886666666666666666666666666666666666666667e-1 * t402 - 0.63665980925000000000000000000000000000000000000000e-2 * t406 - 0.51086165526666666666666666666666666666666666666667e-2 * t411) / t133
  t420 = 0.4e1 * t136 * t17 * t140 * t181
  t421 = t139 * t18
  t425 = 0.4e1 * t137 / t421 * t181
  t428 = f.my_piecewise3(t142, 0, 0.4e1 / 0.3e1 * t145 * t297)
  t429 = -t297
  t432 = f.my_piecewise3(t148, 0, 0.4e1 / 0.3e1 * t149 * t429)
  t434 = (t428 + t432) * t155
  t440 = t163 ** 2
  t454 = t174 ** 2
  t455 = 0.1e1 / t454
  t461 = -0.29149603883333333333333333333333333333333333333333e-1 * t400 - 0.10197154565000000000000000000000000000000000000000e-1 * t402 - 0.18581078242500000000000000000000000000000000000000e-2 * t406 - 0.27959640330000000000000000000000000000000000000000e-2 * t411
  t462 = 0.1e1 / t176
  t468 = t141 * t156 * (0.53237641966666666666666666666666666666666666666667e-3 * t109 * t389 * t166 + t158 / t440 * (-0.36580540352500000000000000000000000000000000000000e-1 * t400 - 0.16057569282500000000000000000000000000000000000000e-1 * t402 - 0.65410946462500000000000000000000000000000000000000e-2 * t406 - 0.32394954865000000000000000000000000000000000000000e-2 * t411) / t165 - t392 - t416 + 0.18311447306006545054854346104378990962041954983034e-3 * t109 * t389 * t177 + 0.58482236226346462072622386637590534819724553404281e0 * t169 * t455 * t461 * t462)
  t475 = 0.18311447306006545054854346104378990962041954983034e-3 * t156 * t106 * t398 * t388 * t177
  t480 = 0.58482236226346462072622386637590534819724553404281e0 * t156 * t169 * t455 * t461 * t462
  t481 = t392 + t416 + t420 - t425 + t141 * t434 * t180 + t468 + 0.58482236226346462072622386637590534819724553404281e0 * t434 * t178 - t475 - t480
  t483 = t188 * t11
  t486 = t191 * t40
  t491 = t194 * t46
  t496 = t197 * t52
  t501 = t200 * t58
  t506 = t203 * t64
  t509 = -t189 * t309 - 0.2e1 * t192 * t315 - 0.3e1 * t195 * t322 - 0.4e1 * t198 * t329 - 0.5e1 * t201 * t336 - t483 * t306 - 0.2e1 * t486 * t309 - 0.3e1 * t491 * t315 - 0.4e1 * t496 * t322 - 0.5e1 * t501 * t329 - 0.6e1 * t506 * t336
  t512 = t206 * t70
  t517 = t209 * t76
  t522 = t212 * t82
  t527 = t215 * t88
  t532 = t218 * t94
  t537 = -0.6e1 * t204 * t344 - 0.7e1 * t207 * t351 - 0.8e1 * t210 * t358 - 0.9e1 * t213 * t365 - 0.10e2 * t216 * t372 - 0.11e2 * t219 * t381 - 0.7e1 * t512 * t344 - 0.8e1 * t517 * t351 - 0.9e1 * t522 * t358 - 0.10e2 * t527 * t365 - 0.11e2 * t532 * t372
  t541 = t224 * t225
  t542 = t233 * t286
  t543 = 0.1e1 / t145
  t546 = f.my_piecewise3(t142, 0, 0.2e1 / 0.3e1 * t543 * t297)
  t547 = 0.1e1 / t149
  t550 = f.my_piecewise3(t148, 0, 0.2e1 / 0.3e1 * t547 * t429)
  t552 = t546 / 0.2e1 + t550 / 0.2e1
  t561 = t237 / t112 / t138 / t18 * t10 * t246
  t562 = 0.16217772716043213194444444444444444444444444444444e-2 * t561
  t564 = t240 * t10 * t252
  t565 = t123 * t244
  t568 = t564 * t565 * t110 * t552
  t570 = t256 ** 2
  t572 = t250 / t570
  t575 = t572 * t258 * t261 * t11
  t577 = t265 * t106 * t267
  t580 = t5 * t265
  t584 = -t481 * t249 * t253 + 0.3e1 * t251 * t580 * t552
  t588 = t575 * t577 * t111 * t584 * t255
  t594 = t250 * t259 / t126 / t421 * t270
  t595 = 0.67632724766374884048257098754901909722222222222225e-5 * t594
  t599 = t11 / t264 / t232 * t106
  t600 = t267 * t111
  t603 = t263 * t599 * t600 * t552
  t608 = t281 ** 2
  t609 = 0.1e1 / t608
  t610 = t5 * t609
  t615 = 0.7e1 / 0.288e3 * t561
  t618 = 0.10136107947527008246527777777777777777777777777778e-3 * t594
  t629 = 0.1e1 / t285
  vrho_0_ = t186 + t288 + t18 * ((t342 + t384) * t185 + t105 * t481 + (t509 + t537) * t223 * t287 + 0.3e1 * t541 * t542 * t552 + t541 * t234 * ((-t562 - 0.13900948042322754166666666666666666666666666666667e-2 * t568 - 0.14492726735651760867483664018907552083333333333334e-5 * t588 - t595 - 0.57970906942607043469934656075630208333333333333336e-5 * t603) * t249 * t283 - t274 * t610 * (-0.6672455060314922e-1 * t572 * t277 * t584 * t255 + 0.6672455060314922e-1 * t250 * t257 * (-t615 - t568 / 0.48e2 - 0.21720231316129303385416666666666666666666666666667e-4 * t588 - t618 - 0.86880925264517213541666666666666666666666666666668e-4 * t603))) * t629)
  t634 = -t19 - t296
  t635 = t634 / 0.2e1
  t638 = r1 ** 2
  t647 = 0.5e1 / 0.3e1 * t16 * t24 * t635 - 0.5e1 / 0.3e1 * tau1 / t28 / t638 * t36 - 0.5e1 / 0.3e1 * t31 * t35 * t635
  t648 = t647 * t43
  t650 = t308 * t647
  t654 = t314 * t647
  t659 = t321 * t647
  t664 = t328 * t647
  t669 = t335 * t647
  t674 = -t289 * t648 - 0.2e1 * t311 * t650 - 0.3e1 * t318 * t654 - 0.4e1 * t325 * t659 - 0.5e1 * t332 * t664 - 0.6e1 * t339 * t669 - t41 * t650 - 0.2e1 * t47 * t654 - 0.3e1 * t53 * t659 - 0.4e1 * t59 * t664 - 0.5e1 * t65 * t669
  t675 = t343 * t647
  t680 = t350 * t647
  t685 = t357 * t647
  t690 = t364 * t647
  t695 = t371 * t647
  t700 = t380 * t647
  t703 = -0.11e2 * t101 * t700 - 0.7e1 * t347 * t675 - 0.8e1 * t354 * t680 - 0.9e1 * t361 * t685 - 0.10e2 * t368 * t690 - 0.11e2 * t375 * t695 - 0.6e1 * t71 * t675 - 0.7e1 * t77 * t680 - 0.8e1 * t83 * t685 - 0.9e1 * t89 * t690 - 0.10e2 * t95 * t695
  t708 = f.my_piecewise3(t142, 0, 0.4e1 / 0.3e1 * t145 * t634)
  t709 = -t634
  t712 = f.my_piecewise3(t148, 0, 0.4e1 / 0.3e1 * t149 * t709)
  t714 = (t708 + t712) * t155
  t719 = t392 + t416 - t420 - t425 + t141 * t714 * t180 + t468 + 0.58482236226346462072622386637590534819724553404281e0 * t714 * t178 - t475 - t480
  t741 = -t189 * t650 - 0.2e1 * t192 * t654 - 0.3e1 * t195 * t659 - 0.4e1 * t198 * t664 - 0.5e1 * t201 * t669 - t483 * t648 - 0.2e1 * t486 * t650 - 0.3e1 * t491 * t654 - 0.4e1 * t496 * t659 - 0.5e1 * t501 * t664 - 0.6e1 * t506 * t669
  t764 = -0.6e1 * t204 * t675 - 0.7e1 * t207 * t680 - 0.8e1 * t210 * t685 - 0.9e1 * t213 * t690 - 0.10e2 * t216 * t695 - 0.11e2 * t219 * t700 - 0.7e1 * t512 * t675 - 0.8e1 * t517 * t680 - 0.9e1 * t522 * t685 - 0.10e2 * t527 * t690 - 0.11e2 * t532 * t695
  t770 = f.my_piecewise3(t142, 0, 0.2e1 / 0.3e1 * t543 * t634)
  t773 = f.my_piecewise3(t148, 0, 0.2e1 / 0.3e1 * t547 * t709)
  t775 = t770 / 0.2e1 + t773 / 0.2e1
  t781 = t564 * t565 * t110 * t775
  t788 = -t719 * t249 * t253 + 0.3e1 * t251 * t580 * t775
  t792 = t575 * t577 * t111 * t788 * t255
  t796 = t263 * t599 * t600 * t775
  vrho_1_ = t186 + t288 + t18 * ((t674 + t703) * t185 + t105 * t719 + (t741 + t764) * t223 * t287 + 0.3e1 * t541 * t542 * t775 + t541 * t234 * ((-t562 - 0.13900948042322754166666666666666666666666666666667e-2 * t781 - 0.14492726735651760867483664018907552083333333333334e-5 * t792 - t595 - 0.57970906942607043469934656075630208333333333333336e-5 * t796) * t249 * t283 - t274 * t610 * (-0.6672455060314922e-1 * t572 * t277 * t788 * t255 + 0.6672455060314922e-1 * t250 * t257 * (-t615 - t781 / 0.48e2 - 0.21720231316129303385416666666666666666666666666667e-4 * t792 - t618 - 0.86880925264517213541666666666666666666666666666668e-4 * t796))) * t629)
  t822 = t18 * t221 * t223
  t826 = t239 * t10 * t242 * t565 * t110
  t831 = t250 * t257 * t237 * t261 * t270
  t836 = t223 ** 2
  t839 = t5 ** 2
  t840 = t273 / t836 * t839
  t841 = t609 * t257
  vsigma_0_ = t822 * t235 * ((0.69504740211613770833333333333333333333333333333333e-3 * t826 + 0.28985453471303521734967328037815104166666666666668e-5 * t831) * t249 * t283 - 0.6672455060314922e-1 * t840 * t841 * (t826 / 0.96e2 + 0.43440462632258606770833333333333333333333333333334e-4 * t831)) * t629
  vsigma_1_ = t822 * t235 * ((0.13900948042322754166666666666666666666666666666667e-2 * t826 + 0.57970906942607043469934656075630208333333333333336e-5 * t831) * t249 * t283 - 0.6672455060314922e-1 * t840 * t841 * (t826 / 0.48e2 + 0.86880925264517213541666666666666666666666666666668e-4 * t831)) * t629
  vsigma_2_ = vsigma_0_
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t866 = t15 * t25 * t43
  t868 = t41 * t49
  t870 = t11 * t15 * t25
  t872 = t311 * t49
  t875 = t47 * t55
  t878 = t318 * t55
  t881 = t53 * t61
  t884 = t325 * t61
  t887 = t59 * t67
  t890 = t332 * t67
  t893 = t65 * t73
  t896 = t339 * t73
  t899 = -t289 * t866 - t868 * t870 - 0.2e1 * t872 * t870 - 0.2e1 * t875 * t870 - 0.3e1 * t878 * t870 - 0.3e1 * t881 * t870 - 0.4e1 * t884 * t870 - 0.4e1 * t887 * t870 - 0.5e1 * t890 * t870 - 0.5e1 * t893 * t870 - 0.6e1 * t896 * t870
  t900 = t71 * t79
  t903 = t347 * t79
  t906 = t77 * t85
  t909 = t354 * t85
  t912 = t83 * t91
  t915 = t361 * t91
  t918 = t89 * t97
  t921 = t368 * t97
  t924 = t95 * t103
  t927 = t375 * t103
  t930 = t101 * t379
  t933 = -0.6e1 * t900 * t870 - 0.7e1 * t903 * t870 - 0.7e1 * t906 * t870 - 0.8e1 * t909 * t870 - 0.8e1 * t912 * t870 - 0.9e1 * t915 * t870 - 0.9e1 * t918 * t870 - 0.10e2 * t921 * t870 - 0.10e2 * t924 * t870 - 0.11e2 * t927 * t870 - 0.11e2 * t930 * t870
  t937 = t189 * t49
  t939 = t486 * t49
  t942 = t192 * t55
  t945 = t491 * t55
  t948 = t195 * t61
  t951 = t496 * t61
  t954 = t198 * t67
  t957 = t501 * t67
  t960 = t201 * t73
  t963 = t506 * t73
  t966 = -t483 * t866 - t937 * t870 - 0.2e1 * t939 * t870 - 0.2e1 * t942 * t870 - 0.3e1 * t945 * t870 - 0.3e1 * t948 * t870 - 0.4e1 * t951 * t870 - 0.4e1 * t954 * t870 - 0.5e1 * t957 * t870 - 0.5e1 * t960 * t870 - 0.6e1 * t963 * t870
  t967 = t204 * t79
  t970 = t512 * t79
  t973 = t207 * t85
  t976 = t517 * t85
  t979 = t210 * t91
  t982 = t522 * t91
  t985 = t213 * t97
  t988 = t527 * t97
  t991 = t216 * t103
  t994 = t532 * t103
  t997 = t219 * t379
  t1000 = -0.6e1 * t967 * t870 - 0.7e1 * t970 * t870 - 0.7e1 * t973 * t870 - 0.8e1 * t976 * t870 - 0.8e1 * t979 * t870 - 0.9e1 * t982 * t870 - 0.9e1 * t985 * t870 - 0.10e2 * t988 * t870 - 0.10e2 * t991 * t870 - 0.11e2 * t994 * t870 - 0.11e2 * t997 * t870
  vtau_0_ = t18 * ((t899 + t933) * t185 + (t966 + t1000) * t223 * t287)
  t1006 = t30 * t36 * t43
  t1009 = t11 * t30 * t36
  t1029 = -t289 * t1006 - t868 * t1009 - 0.2e1 * t872 * t1009 - 0.2e1 * t875 * t1009 - 0.3e1 * t878 * t1009 - 0.3e1 * t881 * t1009 - 0.4e1 * t884 * t1009 - 0.4e1 * t887 * t1009 - 0.5e1 * t890 * t1009 - 0.5e1 * t893 * t1009 - 0.6e1 * t896 * t1009
  t1052 = -0.6e1 * t900 * t1009 - 0.7e1 * t903 * t1009 - 0.7e1 * t906 * t1009 - 0.8e1 * t909 * t1009 - 0.8e1 * t912 * t1009 - 0.9e1 * t915 * t1009 - 0.9e1 * t918 * t1009 - 0.10e2 * t921 * t1009 - 0.10e2 * t924 * t1009 - 0.11e2 * t927 * t1009 - 0.11e2 * t930 * t1009
  t1075 = -t483 * t1006 - t937 * t1009 - 0.2e1 * t939 * t1009 - 0.2e1 * t942 * t1009 - 0.3e1 * t945 * t1009 - 0.3e1 * t948 * t1009 - 0.4e1 * t951 * t1009 - 0.4e1 * t954 * t1009 - 0.5e1 * t957 * t1009 - 0.5e1 * t960 * t1009 - 0.6e1 * t963 * t1009
  t1098 = -0.6e1 * t967 * t1009 - 0.7e1 * t970 * t1009 - 0.7e1 * t973 * t1009 - 0.8e1 * t976 * t1009 - 0.8e1 * t979 * t1009 - 0.9e1 * t982 * t1009 - 0.9e1 * t985 * t1009 - 0.10e2 * t988 * t1009 - 0.10e2 * t991 * t1009 - 0.11e2 * t994 * t1009 - 0.11e2 * t997 * t1009
  vtau_1_ = t18 * ((t1029 + t1052) * t185 + (t1075 + t1098) * t223 * t287)
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
  params_m08_a_raw = params.m08_a
  if isinstance(params_m08_a_raw, (str, bytes, dict)):
    params_m08_a = params_m08_a_raw
  else:
    try:
      params_m08_a_seq = list(params_m08_a_raw)
    except TypeError:
      params_m08_a = params_m08_a_raw
    else:
      params_m08_a_seq = np.asarray(params_m08_a_seq, dtype=np.float64)
      params_m08_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_m08_a_seq))
  params_m08_b_raw = params.m08_b
  if isinstance(params_m08_b_raw, (str, bytes, dict)):
    params_m08_b = params_m08_b_raw
  else:
    try:
      params_m08_b_seq = list(params_m08_b_raw)
    except TypeError:
      params_m08_b = params_m08_b_raw
    else:
      params_m08_b_seq = np.asarray(params_m08_b_seq, dtype=np.float64)
      params_m08_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_m08_b_seq))

  params_pp = np.array([np.nan, 1, 1, 1], dtype=np.float64)

  params_a = np.array([np.nan, 0.0310907, 0.01554535, 0.0168869], dtype=np.float64)

  params_alpha1 = np.array([np.nan, 0.2137, 0.20548, 0.11125], dtype=np.float64)

  params_beta1 = np.array([np.nan, 7.5957, 14.1189, 10.357], dtype=np.float64)

  params_beta2 = np.array([np.nan, 3.5876, 6.1977, 3.6231], dtype=np.float64)

  params_beta3 = np.array([np.nan, 1.6382, 3.3662, 0.88026], dtype=np.float64)

  params_beta4 = np.array([np.nan, 0.49294, 0.62517, 0.49671], dtype=np.float64)

  params_fz20 = 1.7099209341613657

  params_beta = 0.06672455060314922

  params_gamma = (1 - jnp.log(2)) / jnp.pi ** 2

  params_BB = 1

  tp = lambda rs, z, xt: f.tt(rs, z, xt)

  g_aux = lambda k, rs: params_beta1[k] * jnp.sqrt(rs) + params_beta2[k] * rs + params_beta3[k] * rs ** 1.5 + params_beta4[k] * rs ** (params_pp[k] + 1)

  mbeta = lambda rs=None, t=None: params_beta

  mgamma = params_gamma

  BB = params_BB

  g = lambda k, rs: -2 * params_a[k] * (1 + params_alpha1[k] * rs) * jnp.log(1 + 1 / (2 * params_a[k] * g_aux(k, rs)))

  f_pw = lambda rs, zeta: g(1, rs) + zeta ** 4 * f.f_zeta(zeta) * (g(2, rs) - g(1, rs) + g(3, rs) / params_fz20) - f.f_zeta(zeta) * g(3, rs) / params_fz20

  A = lambda rs, z, t: mbeta(rs, t) / (mgamma * (jnp.exp(-f_pw(rs, z) / (mgamma * f.mphi(z) ** 3)) - 1))

  f1 = lambda rs, z, t: t ** 2 + BB * A(rs, z, t) * t ** 4

  f2 = lambda rs, z, t: mbeta(rs, t) * f1(rs, z, t) / (mgamma * (1 + A(rs, z, t) * f1(rs, z, t)))

  fH = lambda rs, z, t: mgamma * f.mphi(z) ** 3 * jnp.log(1 + f2(rs, z, t))

  f_pbe = lambda rs, z, xt, xs0=None, xs1=None: f_pw(rs, z) + fH(rs, z, tp(rs, z, xt))

  m08_f = lambda rs, z, xt, xs0, xs1, ts0, ts1: +mgga_series_w(params_m08_a, 12, 2 ** (2 / 3) * f.t_total(z, ts0, ts1)) * f_pw(rs, z) + mgga_series_w(params_m08_b, 12, 2 ** (2 / 3) * f.t_total(z, ts0, ts1)) * (f_pbe(rs, z, xt, xs0, xs1) - f_pw(rs, z))

  functional_body = lambda rs, z, xt, xs0, xs1, us0, us1, ts0, ts1: m08_f(rs, z, xt, xs0, xs1, ts0, ts1)

  t2 = params.m08_a[1]
  t3 = 6 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** 2
  t6 = t5 ** (0.1e1 / 0.3e1)
  t7 = t6 ** 2
  t9 = 0.3e1 / 0.10e2 * t4 * t7
  t10 = 2 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = tau0 * t11
  t13 = r0 ** (0.1e1 / 0.3e1)
  t14 = t13 ** 2
  t16 = 0.1e1 / t14 / r0
  t17 = t12 * t16
  t18 = t9 - t17
  t19 = t2 * t18
  t20 = t9 + t17
  t21 = 0.1e1 / t20
  t23 = params.m08_a[2]
  t24 = t18 ** 2
  t25 = t23 * t24
  t26 = t20 ** 2
  t27 = 0.1e1 / t26
  t29 = params.m08_a[3]
  t30 = t24 * t18
  t31 = t29 * t30
  t32 = t26 * t20
  t33 = 0.1e1 / t32
  t35 = params.m08_a[4]
  t36 = t24 ** 2
  t37 = t35 * t36
  t38 = t26 ** 2
  t39 = 0.1e1 / t38
  t41 = params.m08_a[5]
  t42 = t36 * t18
  t43 = t41 * t42
  t45 = 0.1e1 / t38 / t20
  t47 = params.m08_a[6]
  t48 = t36 * t24
  t49 = t47 * t48
  t51 = 0.1e1 / t38 / t26
  t53 = params.m08_a[7]
  t54 = t36 * t30
  t55 = t53 * t54
  t57 = 0.1e1 / t38 / t32
  t59 = params.m08_a[8]
  t60 = t36 ** 2
  t61 = t59 * t60
  t62 = t38 ** 2
  t63 = 0.1e1 / t62
  t65 = params.m08_a[9]
  t66 = t60 * t18
  t67 = t65 * t66
  t69 = 0.1e1 / t62 / t20
  t71 = params.m08_a[10]
  t72 = t60 * t24
  t73 = t71 * t72
  t75 = 0.1e1 / t62 / t26
  t77 = params.m08_a[11]
  t78 = t60 * t30
  t79 = t77 * t78
  t81 = 0.1e1 / t62 / t32
  t83 = t19 * t21 + t25 * t27 + t31 * t33 + t37 * t39 + t43 * t45 + t49 * t51 + t55 * t57 + t61 * t63 + t67 * t69 + t73 * t75 + t79 * t81 + params.m08_a[0]
  t84 = 3 ** (0.1e1 / 0.3e1)
  t86 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t87 = t84 * t86
  t88 = 4 ** (0.1e1 / 0.3e1)
  t89 = t88 ** 2
  t92 = t87 * t89 / t13
  t94 = 0.621814e-1 + 0.33220412950000000000000000000000000000000000000000e-2 * t92
  t95 = jnp.sqrt(t92)
  t98 = t92 ** 0.15e1
  t100 = t84 ** 2
  t101 = t86 ** 2
  t102 = t100 * t101
  t105 = t102 * t88 / t14
  t107 = 0.23615562999000000000000000000000000000000000000000e0 * t95 + 0.55770497660000000000000000000000000000000000000000e-1 * t92 + 0.12733196185000000000000000000000000000000000000000e-1 * t98 + 0.76629248290000000000000000000000000000000000000000e-2 * t105
  t109 = 0.1e1 + 0.1e1 / t107
  t110 = jnp.log(t109)
  t112 = 0.1e1 <= f.p.zeta_threshold
  t113 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t115 = f.my_piecewise3(t112, t113 * f.p.zeta_threshold, 1)
  t121 = (0.2e1 * t115 - 0.2e1) / (0.2e1 * t10 - 0.2e1)
  t123 = 0.337738e-1 + 0.93933381250000000000000000000000000000000000000000e-3 * t92
  t128 = 0.17489762330000000000000000000000000000000000000000e0 * t95 + 0.30591463695000000000000000000000000000000000000000e-1 * t92 + 0.37162156485000000000000000000000000000000000000000e-2 * t98 + 0.41939460495000000000000000000000000000000000000000e-2 * t105
  t130 = 0.1e1 + 0.1e1 / t128
  t131 = jnp.log(t130)
  t135 = -t94 * t110 + 0.58482236226346462072622386637590534819724553404281e0 * t121 * t123 * t131
  t138 = params.m08_b[1]
  t139 = t138 * t18
  t141 = params.m08_b[2]
  t142 = t141 * t24
  t144 = params.m08_b[3]
  t145 = t144 * t30
  t147 = params.m08_b[4]
  t148 = t147 * t36
  t150 = params.m08_b[5]
  t151 = t150 * t42
  t153 = params.m08_b[6]
  t154 = t153 * t48
  t156 = params.m08_b[7]
  t157 = t156 * t54
  t159 = params.m08_b[8]
  t160 = t159 * t60
  t162 = params.m08_b[9]
  t163 = t162 * t66
  t165 = params.m08_b[10]
  t166 = t165 * t72
  t168 = params.m08_b[11]
  t169 = t168 * t78
  t171 = t139 * t21 + t142 * t27 + t145 * t33 + t148 * t39 + t151 * t45 + t154 * t51 + t157 * t57 + t160 * t63 + t163 * t69 + t166 * t75 + t169 * t81 + params.m08_b[0]
  t172 = jnp.log(0.2e1)
  t173 = 0.1e1 - t172
  t174 = t171 * t173
  t175 = 0.1e1 / t5
  t176 = t113 ** 2
  t177 = f.my_piecewise3(t112, t176, 1)
  t178 = t177 ** 2
  t179 = t178 * t177
  t180 = t175 * t179
  t181 = r0 ** 2
  t183 = 0.1e1 / t13 / t181
  t186 = 0.1e1 / t178
  t188 = 0.1e1 / t86
  t190 = t186 * t100 * t188 * t88
  t191 = s0 * t183 * t10 * t190
  t193 = 0.1e1 / t173
  t194 = t193 * t5
  t196 = 0.1e1 / t179
  t199 = jnp.exp(-t135 * t193 * t5 * t196)
  t200 = t199 - 0.1e1
  t201 = 0.1e1 / t200
  t202 = s0 ** 2
  t203 = t201 * t202
  t204 = t181 ** 2
  t206 = 0.1e1 / t14 / t204
  t209 = t178 ** 2
  t212 = 0.1e1 / t101
  t215 = t11 / t209 * t84 * t212 * t89
  t216 = t194 * t203 * t206 * t215
  t218 = 0.69504740211613770833333333333333333333333333333333e-3 * t191 + 0.14492726735651760867483664018907552083333333333334e-5 * t216
  t219 = t218 * t193
  t222 = t191 / 0.96e2 + 0.21720231316129303385416666666666666666666666666667e-4 * t216
  t226 = 0.1e1 + 0.6672455060314922e-1 * t194 * t201 * t222
  t228 = t5 / t226
  t230 = t219 * t228 + 0.1e1
  t231 = jnp.log(t230)
  t232 = t180 * t231
  t236 = 0.1e1 / t14 / t181
  t238 = t11 * t236 * t21
  t242 = t12 * t236
  t245 = t23 * t18
  t252 = t29 * t24
  t259 = t35 * t30
  t266 = t41 * t36
  t273 = t47 * t42
  t277 = 0.5e1 / 0.3e1 * t2 * tau0 * t238 + 0.5e1 / 0.3e1 * t19 * t27 * t242 + 0.10e2 / 0.3e1 * t245 * t27 * t242 + 0.10e2 / 0.3e1 * t25 * t33 * t242 + 0.5e1 * t252 * t33 * t242 + 0.5e1 * t31 * t39 * t242 + 0.20e2 / 0.3e1 * t259 * t39 * t242 + 0.20e2 / 0.3e1 * t37 * t45 * t242 + 0.25e2 / 0.3e1 * t266 * t45 * t242 + 0.25e2 / 0.3e1 * t43 * t51 * t242 + 0.10e2 * t273 * t51 * t242
  t281 = t53 * t48
  t288 = t59 * t54
  t295 = t65 * t60
  t302 = t71 * t66
  t309 = t77 * t72
  t314 = 0.1e1 / t62 / t38
  t318 = 0.10e2 * t49 * t57 * t242 + 0.35e2 / 0.3e1 * t281 * t57 * t242 + 0.35e2 / 0.3e1 * t55 * t63 * t242 + 0.40e2 / 0.3e1 * t288 * t63 * t242 + 0.40e2 / 0.3e1 * t61 * t69 * t242 + 0.15e2 * t295 * t69 * t242 + 0.15e2 * t67 * t75 * t242 + 0.50e2 / 0.3e1 * t302 * t75 * t242 + 0.50e2 / 0.3e1 * t73 * t81 * t242 + 0.55e2 / 0.3e1 * t309 * t81 * t242 + 0.55e2 / 0.3e1 * t79 * t314 * t242
  t322 = 0.1e1 / t13 / r0
  t323 = t89 * t322
  t327 = t107 ** 2
  t332 = t86 * t89
  t333 = t332 * t322
  t334 = 0.1e1 / t95 * t84 * t333
  t336 = t87 * t323
  t338 = t92 ** 0.5e0
  t340 = t338 * t84 * t333
  t343 = t102 * t88 * t16
  t355 = t128 ** 2
  t367 = 0.11073470983333333333333333333333333333333333333333e-2 * t87 * t323 * t110 + t94 / t327 * (-0.39359271665000000000000000000000000000000000000000e-1 * t334 - 0.18590165886666666666666666666666666666666666666667e-1 * t336 - 0.63665980925000000000000000000000000000000000000000e-2 * t340 - 0.51086165526666666666666666666666666666666666666667e-2 * t343) / t109 - 0.18311447306006545054854346104378990962041954983034e-3 * t121 * t84 * t332 * t322 * t131 - 0.58482236226346462072622386637590534819724553404281e0 * t121 * t123 / t355 * (-0.29149603883333333333333333333333333333333333333333e-1 * t334 - 0.10197154565000000000000000000000000000000000000000e-1 * t336 - 0.18581078242500000000000000000000000000000000000000e-2 * t340 - 0.27959640330000000000000000000000000000000000000000e-2 * t343) / t130
  t375 = t141 * t18
  t382 = t144 * t24
  t389 = t147 * t30
  t396 = t150 * t36
  t403 = t153 * t42
  t407 = 0.5e1 / 0.3e1 * t138 * tau0 * t238 + 0.5e1 / 0.3e1 * t139 * t27 * t242 + 0.10e2 / 0.3e1 * t375 * t27 * t242 + 0.10e2 / 0.3e1 * t142 * t33 * t242 + 0.5e1 * t382 * t33 * t242 + 0.5e1 * t145 * t39 * t242 + 0.20e2 / 0.3e1 * t389 * t39 * t242 + 0.20e2 / 0.3e1 * t148 * t45 * t242 + 0.25e2 / 0.3e1 * t396 * t45 * t242 + 0.25e2 / 0.3e1 * t151 * t51 * t242 + 0.10e2 * t403 * t51 * t242
  t411 = t156 * t48
  t418 = t159 * t54
  t425 = t162 * t60
  t432 = t165 * t66
  t439 = t168 * t72
  t446 = 0.10e2 * t154 * t57 * t242 + 0.35e2 / 0.3e1 * t411 * t57 * t242 + 0.35e2 / 0.3e1 * t157 * t63 * t242 + 0.40e2 / 0.3e1 * t418 * t63 * t242 + 0.40e2 / 0.3e1 * t160 * t69 * t242 + 0.15e2 * t425 * t69 * t242 + 0.15e2 * t163 * t75 * t242 + 0.50e2 / 0.3e1 * t432 * t75 * t242 + 0.50e2 / 0.3e1 * t166 * t81 * t242 + 0.55e2 / 0.3e1 * t439 * t81 * t242 + 0.55e2 / 0.3e1 * t169 * t314 * t242
  t456 = s0 / t13 / t181 / r0 * t10 * t190
  t458 = t173 ** 2
  t459 = 0.1e1 / t458
  t460 = t5 ** 2
  t462 = t200 ** 2
  t464 = t459 * t460 / t462
  t475 = t464 * t202 * t206 * t11 / t209 / t179 * t84 * t212 * t89 * t367 * t199
  t482 = t194 * t203 / t14 / t204 / r0 * t215
  t487 = t226 ** 2
  t488 = 0.1e1 / t487
  t507 = 0.1e1 / t230
  vrho_0_ = t83 * t135 + t174 * t232 + r0 * ((t277 + t318) * t135 + t83 * t367 + (t407 + t446) * t173 * t232 + t174 * t175 * t179 * ((-0.16217772716043213194444444444444444444444444444444e-2 * t456 + 0.14492726735651760867483664018907552083333333333334e-5 * t475 - 0.67632724766374884048257098754901909722222222222225e-5 * t482) * t193 * t228 - t219 * t5 * t488 * (0.6672455060314922e-1 * t464 * t222 * t367 * t196 * t199 + 0.6672455060314922e-1 * t194 * t201 * (-0.7e1 / 0.288e3 * t456 + 0.21720231316129303385416666666666666666666666666667e-4 * t475 - 0.10136107947527008246527777777777777777777777777778e-3 * t482))) * t507)
  t518 = t183 * t10 * t186 * t100 * t188 * t88
  t523 = t194 * t201 * s0 * t206 * t215
  vsigma_0_ = r0 * t171 * t173 * t180 * ((0.69504740211613770833333333333333333333333333333333e-3 * t518 + 0.28985453471303521734967328037815104166666666666668e-5 * t523) * t193 * t228 - 0.6672455060314922e-1 * t218 * t459 * t460 * t488 * t201 * (t518 / 0.96e2 + 0.43440462632258606770833333333333333333333333333334e-4 * t523)) * t507
  vlapl_0_ = 0.0e0
  t541 = t16 * t21
  t544 = t27 * t11 * t16
  t549 = t33 * t11 * t16
  t555 = t39 * t11 * t16
  t561 = t45 * t11 * t16
  t567 = t51 * t11 * t16
  t572 = -t2 * t11 * t541 - t19 * t544 - 0.2e1 * t245 * t544 - 0.2e1 * t25 * t549 - 0.3e1 * t252 * t549 - 0.4e1 * t259 * t555 - 0.5e1 * t266 * t561 - 0.6e1 * t273 * t567 - 0.3e1 * t31 * t555 - 0.4e1 * t37 * t561 - 0.5e1 * t43 * t567
  t574 = t57 * t11 * t16
  t580 = t63 * t11 * t16
  t586 = t69 * t11 * t16
  t592 = t75 * t11 * t16
  t598 = t81 * t11 * t16
  t604 = t314 * t11 * t16
  t607 = -0.7e1 * t281 * t574 - 0.8e1 * t288 * t580 - 0.9e1 * t295 * t586 - 0.10e2 * t302 * t592 - 0.11e2 * t309 * t598 - 0.6e1 * t49 * t574 - 0.7e1 * t55 * t580 - 0.8e1 * t61 * t586 - 0.9e1 * t67 * t592 - 0.10e2 * t73 * t598 - 0.11e2 * t79 * t604
  t631 = -t138 * t11 * t541 - t139 * t544 - 0.2e1 * t142 * t549 - 0.3e1 * t145 * t555 - 0.4e1 * t148 * t561 - 0.5e1 * t151 * t567 - 0.2e1 * t375 * t544 - 0.3e1 * t382 * t549 - 0.4e1 * t389 * t555 - 0.5e1 * t396 * t561 - 0.6e1 * t403 * t567
  t654 = -0.6e1 * t154 * t574 - 0.7e1 * t157 * t580 - 0.8e1 * t160 * t586 - 0.9e1 * t163 * t592 - 0.10e2 * t166 * t598 - 0.11e2 * t169 * t604 - 0.7e1 * t411 * t574 - 0.8e1 * t418 * t580 - 0.9e1 * t425 * t586 - 0.10e2 * t432 * t592 - 0.11e2 * t439 * t598
  vtau_0_ = r0 * ((t572 + t607) * t135 + (t631 + t654) * t173 * t232)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
  return res

