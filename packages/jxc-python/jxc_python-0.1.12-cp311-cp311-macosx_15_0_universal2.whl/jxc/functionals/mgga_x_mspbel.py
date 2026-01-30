"""Generated from mgga_x_mspbel.mpl."""

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

  mspbel_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  mspbel_f0 = lambda p, c: 1 + (MU_GE * p + c) / (1 + (MU_GE * p + c) / params_kappa)

  mspbel_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  mspbel_f = lambda x, u, t: mspbel_f0(X2S ** 2 * x ** 2, 0) + mspbel_fa(mspbel_alpha(t, x)) * (mspbel_f0(X2S ** 2 * x ** 2, params_c) - mspbel_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mspbel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  mspbel_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  mspbel_f0 = lambda p, c: 1 + (MU_GE * p + c) / (1 + (MU_GE * p + c) / params_kappa)

  mspbel_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  mspbel_f = lambda x, u, t: mspbel_f0(X2S ** 2 * x ** 2, 0) + mspbel_fa(mspbel_alpha(t, x)) * (mspbel_f0(X2S ** 2 * x ** 2, params_c) - mspbel_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mspbel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  mspbel_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  mspbel_f0 = lambda p, c: 1 + (MU_GE * p + c) / (1 + (MU_GE * p + c) / params_kappa)

  mspbel_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  mspbel_f = lambda x, u, t: mspbel_f0(X2S ** 2 * x ** 2, 0) + mspbel_fa(mspbel_alpha(t, x)) * (mspbel_f0(X2S ** 2 * x ** 2, params_c) - mspbel_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mspbel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t40 = 0.1e1 / params.kappa
  t44 = 0.1e1 + 0.5e1 / 0.972e3 * t33 * t39 * t40
  t45 = 0.1e1 / t44
  t48 = 0.5e1 / 0.972e3 * t33 * t39 * t45
  t50 = 0.1e1 / t36 / r0
  t53 = tau0 * t50 - t39 / 0.8e1
  t54 = t53 ** 2
  t55 = t28 ** 2
  t57 = 0.3e1 / 0.10e2 * t55 * t31
  t58 = params.eta * s0
  t61 = t57 + t58 * t38 / 0.8e1
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t65 = -t54 * t63 + 0.1e1
  t66 = t65 ** 2
  t67 = t66 * t65
  t68 = t54 * t53
  t69 = t62 * t61
  t70 = 0.1e1 / t69
  t72 = t54 ** 2
  t74 = params.b * t72 * t54
  t75 = t62 ** 2
  t77 = 0.1e1 / t75 / t62
  t79 = t68 * t70 + t74 * t77 + 0.1e1
  t80 = 0.1e1 / t79
  t81 = t67 * t80
  t84 = 0.5e1 / 0.972e3 * t33 * t39 + params.c
  t86 = t84 * t40 + 0.1e1
  t87 = 0.1e1 / t86
  t89 = t84 * t87 - t48
  t91 = t81 * t89 + t48 + 0.1e1
  t95 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t91)
  t96 = r1 <= f.p.dens_threshold
  t97 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t98 = 0.1e1 + t97
  t99 = t98 <= f.p.zeta_threshold
  t100 = t98 ** (0.1e1 / 0.3e1)
  t102 = f.my_piecewise3(t99, t22, t100 * t98)
  t103 = t102 * t26
  t104 = r1 ** 2
  t105 = r1 ** (0.1e1 / 0.3e1)
  t106 = t105 ** 2
  t108 = 0.1e1 / t106 / t104
  t109 = s2 * t108
  t113 = 0.1e1 + 0.5e1 / 0.972e3 * t33 * t109 * t40
  t114 = 0.1e1 / t113
  t117 = 0.5e1 / 0.972e3 * t33 * t109 * t114
  t119 = 0.1e1 / t106 / r1
  t122 = tau1 * t119 - t109 / 0.8e1
  t123 = t122 ** 2
  t124 = params.eta * s2
  t127 = t57 + t124 * t108 / 0.8e1
  t128 = t127 ** 2
  t129 = 0.1e1 / t128
  t131 = -t123 * t129 + 0.1e1
  t132 = t131 ** 2
  t133 = t132 * t131
  t134 = t123 * t122
  t135 = t128 * t127
  t136 = 0.1e1 / t135
  t138 = t123 ** 2
  t140 = params.b * t138 * t123
  t141 = t128 ** 2
  t143 = 0.1e1 / t141 / t128
  t145 = t134 * t136 + t140 * t143 + 0.1e1
  t146 = 0.1e1 / t145
  t147 = t133 * t146
  t150 = 0.5e1 / 0.972e3 * t33 * t109 + params.c
  t152 = t150 * t40 + 0.1e1
  t153 = 0.1e1 / t152
  t155 = t150 * t153 - t117
  t157 = t147 * t155 + t117 + 0.1e1
  t161 = f.my_piecewise3(t96, 0, -0.3e1 / 0.8e1 * t5 * t103 * t157)
  t162 = t6 ** 2
  t164 = t16 / t162
  t165 = t7 - t164
  t166 = f.my_piecewise5(t10, 0, t14, 0, t165)
  t169 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t166)
  t174 = t26 ** 2
  t175 = 0.1e1 / t174
  t179 = t5 * t25 * t175 * t91 / 0.8e1
  t182 = 0.1e1 / t36 / t34 / r0
  t183 = s0 * t182
  t186 = 0.10e2 / 0.729e3 * t33 * t183 * t45
  t189 = t55 / t30 / t29
  t190 = s0 ** 2
  t192 = t34 ** 2
  t196 = t44 ** 2
  t197 = 0.1e1 / t196
  t201 = 0.25e2 / 0.354294e6 * t189 * t190 / t35 / t192 / t34 * t197 * t40
  t202 = t66 * t80
  t203 = t53 * t63
  t207 = -0.5e1 / 0.3e1 * tau0 * t38 + t183 / 0.3e1
  t210 = t54 * t70
  t211 = t58 * t182
  t218 = t79 ** 2
  t220 = t67 / t218
  t224 = t68 / t75
  t227 = params.b * t72 * t53
  t232 = 0.1e1 / t75 / t69
  t242 = t86 ** 2
  t245 = t84 / t242 * t28
  t258 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t169 * t26 * t91 - t179 - 0.3e1 / 0.8e1 * t5 * t27 * (-t186 + t201 + 0.3e1 * t202 * t89 * (-0.2e1 * t203 * t207 - 0.2e1 / 0.3e1 * t210 * t211) - t220 * t89 * (0.6e1 * t227 * t77 * t207 + 0.2e1 * t74 * t232 * t211 + 0.3e1 * t210 * t207 + t224 * t211) + t81 * (-0.10e2 / 0.729e3 * t33 * t183 * t87 + 0.10e2 / 0.729e3 * t245 * t32 * s0 * t182 * t40 + t186 - t201)))
  t260 = f.my_piecewise5(t14, 0, t10, 0, -t165)
  t263 = f.my_piecewise3(t99, 0, 0.4e1 / 0.3e1 * t100 * t260)
  t271 = t5 * t102 * t175 * t157 / 0.8e1
  t273 = f.my_piecewise3(t96, 0, -0.3e1 / 0.8e1 * t5 * t263 * t26 * t157 - t271)
  vrho_0_ = t95 + t161 + t6 * (t258 + t273)
  t276 = -t7 - t164
  t277 = f.my_piecewise5(t10, 0, t14, 0, t276)
  t280 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t277)
  t286 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t280 * t26 * t91 - t179)
  t288 = f.my_piecewise5(t14, 0, t10, 0, -t276)
  t291 = f.my_piecewise3(t99, 0, 0.4e1 / 0.3e1 * t100 * t288)
  t298 = 0.1e1 / t106 / t104 / r1
  t299 = s2 * t298
  t302 = 0.10e2 / 0.729e3 * t33 * t299 * t114
  t303 = s2 ** 2
  t305 = t104 ** 2
  t309 = t113 ** 2
  t310 = 0.1e1 / t309
  t314 = 0.25e2 / 0.354294e6 * t189 * t303 / t105 / t305 / t104 * t310 * t40
  t315 = t132 * t146
  t316 = t122 * t129
  t320 = -0.5e1 / 0.3e1 * tau1 * t108 + t299 / 0.3e1
  t323 = t123 * t136
  t324 = t124 * t298
  t331 = t145 ** 2
  t333 = t133 / t331
  t337 = t134 / t141
  t340 = params.b * t138 * t122
  t345 = 0.1e1 / t141 / t135
  t355 = t152 ** 2
  t358 = t150 / t355 * t28
  t371 = f.my_piecewise3(t96, 0, -0.3e1 / 0.8e1 * t5 * t291 * t26 * t157 - t271 - 0.3e1 / 0.8e1 * t5 * t103 * (-t302 + t314 + 0.3e1 * t315 * t155 * (-0.2e1 * t316 * t320 - 0.2e1 / 0.3e1 * t323 * t324) - t333 * t155 * (0.2e1 * t140 * t345 * t324 + 0.6e1 * t340 * t143 * t320 + 0.3e1 * t323 * t320 + t337 * t324) + t147 * (-0.10e2 / 0.729e3 * t33 * t299 * t153 + 0.10e2 / 0.729e3 * t358 * t32 * s2 * t298 * t40 + t302 - t314)))
  vrho_1_ = t95 + t161 + t6 * (t286 + t371)
  t376 = 0.5e1 / 0.972e3 * t33 * t38 * t45
  t384 = 0.25e2 / 0.944784e6 * t189 * s0 / t35 / t192 / r0 * t197 * t40
  t386 = params.eta * t38
  t420 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t376 - t384 + 0.3e1 * t202 * t89 * (t203 * t38 / 0.4e1 + t210 * t386 / 0.4e1) - t220 * t89 * (-0.3e1 / 0.8e1 * t210 * t38 - 0.3e1 / 0.8e1 * t224 * t386 - 0.3e1 / 0.4e1 * t227 * t77 * t38 - 0.3e1 / 0.4e1 * t74 * t232 * params.eta * t38) + t81 * (0.5e1 / 0.972e3 * t33 * t38 * t87 - 0.5e1 / 0.972e3 * t245 * t32 * t38 * t40 - t376 + t384)))
  vsigma_0_ = t6 * t420
  vsigma_1_ = 0.0e0
  t423 = 0.5e1 / 0.972e3 * t33 * t108 * t114
  t431 = 0.25e2 / 0.944784e6 * t189 * s2 / t105 / t305 / r1 * t310 * t40
  t433 = params.eta * t108
  t467 = f.my_piecewise3(t96, 0, -0.3e1 / 0.8e1 * t5 * t103 * (t423 - t431 + 0.3e1 * t315 * t155 * (t316 * t108 / 0.4e1 + t323 * t433 / 0.4e1) - t333 * t155 * (-0.3e1 / 0.8e1 * t323 * t108 - 0.3e1 / 0.8e1 * t337 * t433 - 0.3e1 / 0.4e1 * t340 * t143 * t108 - 0.3e1 / 0.4e1 * t140 * t345 * params.eta * t108) + t147 * (0.5e1 / 0.972e3 * t33 * t108 * t153 - 0.5e1 / 0.972e3 * t358 * t32 * t108 * t40 - t423 + t431)))
  vsigma_2_ = t6 * t467
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t484 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-0.6e1 * t202 * t89 * t203 * t50 - t220 * t89 * (0.6e1 * t227 * t77 * t50 + 0.3e1 * t210 * t50)))
  vtau_0_ = t6 * t484
  t501 = f.my_piecewise3(t96, 0, -0.3e1 / 0.8e1 * t5 * t103 * (-0.6e1 * t315 * t155 * t316 * t119 - t333 * t155 * (0.6e1 * t340 * t143 * t119 + 0.3e1 * t323 * t119)))
  vtau_1_ = t6 * t501
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

  mspbel_fa = lambda a: (1 - a ** 2) ** 3 / (1 + a ** 3 + params_b * a ** 6)

  mspbel_f0 = lambda p, c: 1 + (MU_GE * p + c) / (1 + (MU_GE * p + c) / params_kappa)

  mspbel_alpha = lambda t, x: (t - x ** 2 / 8) / (K_FACTOR_C + params_eta * x ** 2 / 8)

  mspbel_f = lambda x, u, t: mspbel_f0(X2S ** 2 * x ** 2, 0) + mspbel_fa(mspbel_alpha(t, x)) * (mspbel_f0(X2S ** 2 * x ** 2, params_c) - mspbel_f0(X2S ** 2 * x ** 2, 0))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, mspbel_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t25 = t20 * t24
  t26 = t25 * s0
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = r0 ** 2
  t30 = t18 ** 2
  t32 = 0.1e1 / t30 / t29
  t33 = t28 * t32
  t34 = 0.1e1 / params.kappa
  t38 = 0.1e1 + 0.5e1 / 0.972e3 * t26 * t33 * t34
  t39 = 0.1e1 / t38
  t40 = t33 * t39
  t42 = 0.5e1 / 0.972e3 * t26 * t40
  t43 = tau0 * t28
  t45 = 0.1e1 / t30 / r0
  t47 = s0 * t28
  t48 = t47 * t32
  t50 = t43 * t45 - t48 / 0.8e1
  t51 = t50 ** 2
  t52 = t20 ** 2
  t55 = params.eta * s0
  t58 = 0.3e1 / 0.10e2 * t52 * t23 + t55 * t33 / 0.8e1
  t59 = t58 ** 2
  t60 = 0.1e1 / t59
  t62 = -t51 * t60 + 0.1e1
  t63 = t62 ** 2
  t64 = t63 * t62
  t65 = t51 * t50
  t66 = t59 * t58
  t67 = 0.1e1 / t66
  t69 = t51 ** 2
  t71 = params.b * t69 * t51
  t72 = t59 ** 2
  t74 = 0.1e1 / t72 / t59
  t76 = t65 * t67 + t71 * t74 + 0.1e1
  t77 = 0.1e1 / t76
  t78 = t64 * t77
  t81 = 0.5e1 / 0.972e3 * t25 * t48 + params.c
  t83 = t81 * t34 + 0.1e1
  t84 = 0.1e1 / t83
  t86 = t81 * t84 - t42
  t88 = t78 * t86 + t42 + 0.1e1
  t92 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t88)
  t100 = 0.1e1 / t30 / t29 / r0
  t101 = t28 * t100
  t104 = 0.10e2 / 0.729e3 * t26 * t101 * t39
  t107 = t52 / t22 / t21
  t108 = s0 ** 2
  t110 = t29 ** 2
  t115 = t38 ** 2
  t117 = 0.1e1 / t115 * t34
  t120 = 0.25e2 / 0.177147e6 * t107 * t108 * t27 / t18 / t110 / t29 * t117
  t121 = t63 * t77
  t122 = t50 * t60
  t125 = t47 * t100
  t127 = -0.5e1 / 0.3e1 * t43 * t32 + t125 / 0.3e1
  t130 = t51 * t67
  t138 = t76 ** 2
  t140 = t64 / t138
  t144 = t65 / t72
  t148 = params.b * t69 * t50
  t154 = t71 / t72 / t66
  t164 = t83 ** 2
  t166 = t81 / t164
  t179 = f.my_piecewise3(t2, 0, -t6 * t17 / t30 * t88 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t104 + t120 + 0.3e1 * t121 * t86 * (-0.2e1 * t122 * t127 - 0.2e1 / 0.3e1 * t130 * params.eta * t125) - t140 * t86 * (0.2e1 * t154 * t55 * t101 + t144 * params.eta * t125 + 0.6e1 * t148 * t74 * t127 + 0.3e1 * t130 * t127) + t78 * (-0.10e2 / 0.729e3 * t26 * t101 * t84 + 0.10e2 / 0.729e3 * t166 * t25 * t47 * t100 * t34 + t104 - t120)))
  vrho_0_ = 0.2e1 * r0 * t179 + 0.2e1 * t92
  t183 = 0.5e1 / 0.972e3 * t25 * t40
  t191 = 0.25e2 / 0.472392e6 * t107 * s0 * t27 / t18 / t110 / r0 * t117
  t194 = params.eta * t28 * t32
  t205 = t74 * t28
  t229 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t183 - t191 + 0.3e1 * t121 * t86 * (t122 * t33 / 0.4e1 + t130 * t194 / 0.4e1) - t140 * t86 * (-0.3e1 / 0.8e1 * t130 * t33 - 0.3e1 / 0.8e1 * t144 * t194 - 0.3e1 / 0.4e1 * t148 * t205 * t32 - 0.3e1 / 0.4e1 * t154 * t194) + t78 * (0.5e1 / 0.972e3 * t25 * t33 * t84 - 0.5e1 / 0.972e3 * t166 * t20 * t24 * t28 * t32 * t34 - t183 + t191)))
  vsigma_0_ = 0.2e1 * r0 * t229
  vlapl_0_ = 0.0e0
  t232 = t28 * t45
  t248 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-0.6e1 * t121 * t86 * t122 * t232 - t140 * t86 * (0.6e1 * t148 * t205 * t45 + 0.3e1 * t130 * t232)))
  vtau_0_ = 0.2e1 * r0 * t248
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
  t27 = t22 / t25
  t28 = t27 * s0
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = r0 ** 2
  t33 = 0.1e1 / t19 / t31
  t34 = t30 * t33
  t35 = 0.1e1 / params.kappa
  t39 = 0.1e1 + 0.5e1 / 0.972e3 * t28 * t34 * t35
  t40 = 0.1e1 / t39
  t43 = 0.5e1 / 0.972e3 * t28 * t34 * t40
  t44 = tau0 * t30
  t46 = 0.1e1 / t19 / r0
  t48 = s0 * t30
  t49 = t48 * t33
  t51 = t44 * t46 - t49 / 0.8e1
  t52 = t51 ** 2
  t53 = t22 ** 2
  t56 = params.eta * s0
  t59 = 0.3e1 / 0.10e2 * t53 * t25 + t56 * t34 / 0.8e1
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t63 = -t52 * t61 + 0.1e1
  t64 = t63 ** 2
  t65 = t64 * t63
  t66 = t52 * t51
  t67 = t60 * t59
  t68 = 0.1e1 / t67
  t70 = t52 ** 2
  t72 = params.b * t70 * t52
  t73 = t60 ** 2
  t75 = 0.1e1 / t73 / t60
  t77 = t66 * t68 + t72 * t75 + 0.1e1
  t78 = 0.1e1 / t77
  t79 = t65 * t78
  t82 = 0.5e1 / 0.972e3 * t27 * t49 + params.c
  t84 = t82 * t35 + 0.1e1
  t85 = 0.1e1 / t84
  t87 = t82 * t85 - t43
  t89 = t79 * t87 + t43 + 0.1e1
  t93 = t17 * t18
  t94 = t31 * r0
  t96 = 0.1e1 / t19 / t94
  t97 = t30 * t96
  t100 = 0.10e2 / 0.729e3 * t28 * t97 * t40
  t103 = t53 / t24 / t23
  t104 = s0 ** 2
  t105 = t103 * t104
  t106 = t31 ** 2
  t111 = t39 ** 2
  t113 = 0.1e1 / t111 * t35
  t116 = 0.25e2 / 0.177147e6 * t105 * t29 / t18 / t106 / t31 * t113
  t117 = t64 * t78
  t118 = t51 * t61
  t121 = t48 * t96
  t123 = -0.5e1 / 0.3e1 * t44 * t33 + t121 / 0.3e1
  t126 = t52 * t68
  t127 = t126 * params.eta
  t130 = -0.2e1 * t118 * t123 - 0.2e1 / 0.3e1 * t127 * t121
  t131 = t87 * t130
  t134 = t77 ** 2
  t135 = 0.1e1 / t134
  t136 = t65 * t135
  t139 = 0.1e1 / t73
  t141 = t66 * t139 * params.eta
  t144 = params.b * t70 * t51
  t149 = 0.1e1 / t73 / t67
  t150 = t72 * t149
  t151 = t56 * t97
  t154 = 0.6e1 * t144 * t75 * t123 + t141 * t121 + 0.3e1 * t126 * t123 + 0.2e1 * t150 * t151
  t160 = t84 ** 2
  t161 = 0.1e1 / t160
  t163 = t82 * t161 * t27
  t168 = -0.10e2 / 0.729e3 * t28 * t97 * t85 + 0.10e2 / 0.729e3 * t163 * t48 * t96 * t35 + t100 - t116
  t170 = -t136 * t87 * t154 + 0.3e1 * t117 * t131 + t79 * t168 - t100 + t116
  t175 = f.my_piecewise3(t2, 0, -t6 * t21 * t89 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t93 * t170)
  t185 = 0.1e1 / t19 / t106
  t186 = t30 * t185
  t189 = 0.110e3 / 0.2187e4 * t28 * t186 * t40
  t192 = 0.1e1 / t18 / t106 / t94
  t193 = t29 * t192
  t196 = 0.25e2 / 0.19683e5 * t105 * t193 * t113
  t197 = t23 ** 2
  t201 = t106 ** 2
  t207 = params.kappa ** 2
  t208 = 0.1e1 / t207
  t211 = 0.2000e4 / 0.43046721e8 / t197 * t104 * s0 / t201 / t31 / t111 / t39 * t208
  t213 = t130 ** 2
  t224 = t123 ** 2
  t227 = t51 * t68
  t233 = t48 * t185
  t235 = 0.40e2 / 0.9e1 * t44 * t96 - 0.11e2 / 0.9e1 * t233
  t238 = t52 * t139
  t239 = params.eta ** 2
  t241 = t104 * t29
  t242 = t241 * t192
  t254 = t154 ** 2
  t287 = t73 ** 2
  t321 = t189 - t196 + t211 + 0.6e1 * t63 * t78 * t87 * t213 - 0.6e1 * t64 * t135 * t131 * t154 + 0.6e1 * t117 * t168 * t130 + 0.3e1 * t117 * t87 * (-0.2e1 * t224 * t61 - 0.8e1 / 0.3e1 * t227 * t123 * t151 - 0.2e1 * t118 * t235 - 0.4e1 / 0.3e1 * t238 * t239 * t242 + 0.22e2 / 0.9e1 * t127 * t233) + 0.2e1 * t65 / t134 / t77 * t87 * t254 - 0.2e1 * t136 * t168 * t154 - t136 * t87 * (0.6e1 * t227 * t224 + 0.6e1 * t238 * t123 * t151 + 0.3e1 * t126 * t235 + 0.8e1 / 0.3e1 * t66 / t73 / t59 * t239 * t242 - 0.11e2 / 0.3e1 * t141 * t233 + 0.30e2 * params.b * t70 * t75 * t224 + 0.24e2 * t144 * t149 * t123 * t151 + 0.6e1 * t144 * t75 * t235 + 0.28e2 / 0.3e1 * t72 / t287 * t239 * t104 * t193 - 0.22e2 / 0.3e1 * t150 * t56 * t186) + t79 * (0.110e3 / 0.2187e4 * t28 * t186 * t85 - 0.400e3 / 0.531441e6 * t105 * t193 * t161 * t35 + 0.400e3 / 0.531441e6 * t82 / t160 / t84 * t103 * t241 * t192 * t208 - 0.110e3 / 0.2187e4 * t163 * t48 * t185 * t35 - t189 + t196 - t211)
  t326 = f.my_piecewise3(t2, 0, t6 * t17 * t46 * t89 / 0.12e2 - t6 * t21 * t170 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t93 * t321)
  v2rho2_0_ = 0.2e1 * r0 * t326 + 0.4e1 * t175
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
  t28 = t23 * t27
  t29 = t28 * s0
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t35 = t31 * t34
  t36 = 0.1e1 / params.kappa
  t40 = 0.1e1 + 0.5e1 / 0.972e3 * t29 * t35 * t36
  t41 = 0.1e1 / t40
  t44 = 0.5e1 / 0.972e3 * t29 * t35 * t41
  t45 = tau0 * t31
  t47 = s0 * t31
  t48 = t47 * t34
  t50 = t45 * t21 - t48 / 0.8e1
  t51 = t50 ** 2
  t52 = t23 ** 2
  t55 = params.eta * s0
  t58 = 0.3e1 / 0.10e2 * t52 * t26 + t55 * t35 / 0.8e1
  t59 = t58 ** 2
  t60 = 0.1e1 / t59
  t62 = -t51 * t60 + 0.1e1
  t63 = t62 ** 2
  t64 = t63 * t62
  t65 = t51 * t50
  t66 = t59 * t58
  t67 = 0.1e1 / t66
  t69 = t51 ** 2
  t71 = params.b * t69 * t51
  t72 = t59 ** 2
  t74 = 0.1e1 / t72 / t59
  t76 = t65 * t67 + t71 * t74 + 0.1e1
  t77 = 0.1e1 / t76
  t78 = t64 * t77
  t81 = 0.5e1 / 0.972e3 * t28 * t48 + params.c
  t83 = t81 * t36 + 0.1e1
  t84 = 0.1e1 / t83
  t86 = t81 * t84 - t44
  t88 = t78 * t86 + t44 + 0.1e1
  t93 = t17 / t19
  t94 = t32 * r0
  t96 = 0.1e1 / t19 / t94
  t97 = t31 * t96
  t100 = 0.10e2 / 0.729e3 * t29 * t97 * t41
  t103 = t52 / t25 / t24
  t104 = s0 ** 2
  t105 = t103 * t104
  t106 = t32 ** 2
  t111 = t40 ** 2
  t113 = 0.1e1 / t111 * t36
  t116 = 0.25e2 / 0.177147e6 * t105 * t30 / t18 / t106 / t32 * t113
  t117 = t63 * t77
  t118 = t50 * t60
  t121 = t47 * t96
  t123 = -0.5e1 / 0.3e1 * t45 * t34 + t121 / 0.3e1
  t126 = t51 * t67
  t127 = t126 * params.eta
  t130 = -0.2e1 * t118 * t123 - 0.2e1 / 0.3e1 * t127 * t121
  t131 = t86 * t130
  t134 = t76 ** 2
  t135 = 0.1e1 / t134
  t136 = t64 * t135
  t139 = 0.1e1 / t72
  t141 = t65 * t139 * params.eta
  t144 = params.b * t69 * t50
  t145 = t74 * t123
  t149 = 0.1e1 / t72 / t66
  t150 = t71 * t149
  t151 = t55 * t97
  t154 = t141 * t121 + 0.3e1 * t126 * t123 + 0.6e1 * t144 * t145 + 0.2e1 * t150 * t151
  t155 = t86 * t154
  t160 = t83 ** 2
  t161 = 0.1e1 / t160
  t163 = t81 * t161 * t28
  t168 = -0.10e2 / 0.729e3 * t29 * t97 * t84 + 0.10e2 / 0.729e3 * t163 * t47 * t96 * t36 + t100 - t116
  t170 = 0.3e1 * t117 * t131 - t136 * t155 + t78 * t168 - t100 + t116
  t174 = t17 * t18
  t176 = 0.1e1 / t19 / t106
  t177 = t31 * t176
  t180 = 0.110e3 / 0.2187e4 * t29 * t177 * t41
  t183 = 0.1e1 / t18 / t106 / t94
  t184 = t30 * t183
  t187 = 0.25e2 / 0.19683e5 * t105 * t184 * t113
  t188 = t24 ** 2
  t189 = 0.1e1 / t188
  t190 = t104 * s0
  t191 = t189 * t190
  t192 = t106 ** 2
  t196 = 0.1e1 / t111 / t40
  t198 = params.kappa ** 2
  t199 = 0.1e1 / t198
  t202 = 0.2000e4 / 0.43046721e8 * t191 / t192 / t32 * t196 * t199
  t203 = t62 * t77
  t204 = t130 ** 2
  t205 = t86 * t204
  t208 = t63 * t135
  t212 = t168 * t130
  t215 = t123 ** 2
  t218 = t50 * t67
  t219 = t218 * t123
  t224 = t47 * t176
  t226 = 0.40e2 / 0.9e1 * t45 * t96 - 0.11e2 / 0.9e1 * t224
  t229 = t51 * t139
  t230 = params.eta ** 2
  t231 = t229 * t230
  t232 = t104 * t30
  t233 = t232 * t183
  t238 = -0.2e1 * t215 * t60 - 0.8e1 / 0.3e1 * t219 * t151 - 0.2e1 * t118 * t226 - 0.4e1 / 0.3e1 * t231 * t233 + 0.22e2 / 0.9e1 * t127 * t224
  t239 = t86 * t238
  t243 = 0.1e1 / t134 / t76
  t244 = t64 * t243
  t245 = t154 ** 2
  t254 = t229 * t123
  t260 = 0.1e1 / t72 / t58
  t262 = t65 * t260 * t230
  t267 = params.b * t69
  t272 = t144 * t149 * t123
  t278 = t72 ** 2
  t279 = 0.1e1 / t278
  t280 = t71 * t279
  t281 = t230 * t104
  t282 = t281 * t184
  t285 = t55 * t177
  t288 = 0.6e1 * t218 * t215 + 0.6e1 * t254 * t151 + 0.3e1 * t126 * t226 + 0.8e1 / 0.3e1 * t262 * t233 - 0.11e2 / 0.3e1 * t141 * t224 + 0.30e2 * t267 * t74 * t215 + 0.24e2 * t272 * t151 + 0.6e1 * t144 * t74 * t226 + 0.28e2 / 0.3e1 * t280 * t282 - 0.22e2 / 0.3e1 * t150 * t285
  t294 = t161 * t36
  t299 = 0.1e1 / t160 / t83
  t301 = t81 * t299 * t103
  t310 = 0.110e3 / 0.2187e4 * t29 * t177 * t84 - 0.400e3 / 0.531441e6 * t105 * t184 * t294 + 0.400e3 / 0.531441e6 * t301 * t232 * t183 * t199 - 0.110e3 / 0.2187e4 * t163 * t47 * t176 * t36 - t180 + t187 - t202
  t312 = -0.6e1 * t208 * t131 * t154 - 0.2e1 * t136 * t168 * t154 - t136 * t86 * t288 + 0.2e1 * t244 * t86 * t245 + 0.6e1 * t117 * t212 + 0.3e1 * t117 * t239 + 0.6e1 * t203 * t205 + t78 * t310 + t180 - t187 + t202
  t317 = f.my_piecewise3(t2, 0, t6 * t22 * t88 / 0.12e2 - t6 * t93 * t170 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t174 * t312)
  t349 = t50 * t139
  t360 = t106 * r0
  t362 = 0.1e1 / t19 / t360
  t363 = t47 * t362
  t365 = -0.440e3 / 0.27e2 * t45 * t176 + 0.154e3 / 0.27e2 * t363
  t368 = t51 * t260
  t372 = 0.1e1 / t192 / t94
  t373 = t230 * params.eta * t190 * t372
  t377 = 0.1e1 / t18 / t192
  t378 = t232 * t377
  t402 = t215 * t123
  t440 = t30 * t377
  t444 = t31 * t362
  t459 = 0.6e1 * t144 * t74 * t365 + 0.18e2 * t218 * t123 * t226 + 0.6e1 * t402 * t67 + 0.3e1 * t126 * t365 - 0.132e3 * t272 * t285 + 0.80e2 / 0.9e1 * t65 * t74 * t373 + 0.120e3 * params.b * t65 * t74 * t402 + 0.90e2 * t267 * t145 * t226 + 0.18e2 * t349 * t215 * t151 + 0.9e1 * t229 * t226 * t151 + 0.24e2 * t368 * t123 * t282 - 0.88e2 / 0.3e1 * t262 * t378 + 0.154e3 / 0.9e1 * t141 * t363 + 0.36e2 * t144 * t149 * t226 * t151 + 0.168e3 * t144 * t279 * t123 * t282 - 0.308e3 / 0.3e1 * t280 * t281 * t440 + 0.308e3 / 0.9e1 * t150 * t55 * t444 - 0.33e2 * t254 * t285 + 0.180e3 * t267 * t149 * t215 * t151 + 0.448e3 / 0.9e1 * t71 / t278 / t58 * t373
  t472 = t160 ** 2
  t478 = 0.1e1 / t198 / params.kappa
  t492 = 0.1540e4 / 0.6561e4 * t29 * t444 * t41
  t495 = 0.17050e5 / 0.1594323e7 * t105 * t440 * t113
  t499 = 0.38000e5 / 0.43046721e8 * t191 * t372 * t196 * t199
  t500 = t104 ** 2
  t505 = t111 ** 2
  t513 = 0.20000e5 / 0.10460353203e11 * t189 * t500 / t19 / t192 / t360 / t505 * t478 * t23 * t27 * t31
  t516 = 0.6e1 * t204 * t130 * t77 * t86 + 0.18e2 * t203 * t168 * t204 + 0.9e1 * t117 * t310 * t130 + 0.9e1 * t117 * t168 * t238 + 0.3e1 * t117 * t86 * (-0.6e1 * t123 * t60 * t226 - 0.4e1 * t215 * t67 * params.eta * t121 - 0.8e1 * t349 * t123 * t282 - 0.4e1 * t218 * t226 * t151 + 0.44e2 / 0.3e1 * t219 * t285 - 0.2e1 * t118 * t365 - 0.32e2 / 0.9e1 * t368 * t373 + 0.44e2 / 0.3e1 * t231 * t378 - 0.308e3 / 0.27e2 * t127 * t363) + 0.6e1 * t244 * t168 * t245 - 0.3e1 * t136 * t310 * t154 - 0.3e1 * t136 * t168 * t288 - t136 * t86 * t459 + t78 * (-0.1540e4 / 0.6561e4 * t29 * t444 * t84 + 0.4400e4 / 0.531441e6 * t105 * t440 * t294 - 0.16000e5 / 0.43046721e8 * t191 * t372 * t299 * t199 + 0.16000e5 / 0.43046721e8 * t81 / t472 * t189 * t190 * t372 * t478 - 0.4400e4 / 0.531441e6 * t301 * t232 * t377 * t199 + 0.1540e4 / 0.6561e4 * t163 * t47 * t362 * t36 + t492 - t495 + t499 - t513) - t499
  t533 = t134 ** 2
  t547 = -0.18e2 * t62 * t135 * t205 * t154 + 0.18e2 * t203 * t131 * t238 - 0.18e2 * t208 * t212 * t154 - 0.9e1 * t208 * t239 * t154 - 0.9e1 * t208 * t131 * t288 - 0.6e1 * t64 / t533 * t86 * t245 * t154 + 0.6e1 * t244 * t155 * t288 - t492 + t495 + t513 + 0.18e2 * t63 * t243 * t131 * t245
  t553 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t34 * t88 + t6 * t22 * t170 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t93 * t312 - 0.3e1 / 0.8e1 * t6 * t174 * (t516 + t547))
  v3rho3_0_ = 0.2e1 * r0 * t553 + 0.6e1 * t317

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
  t29 = t24 * t28
  t30 = t29 * s0
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = t32 * t22
  t34 = 0.1e1 / params.kappa
  t38 = 0.1e1 + 0.5e1 / 0.972e3 * t30 * t33 * t34
  t39 = 0.1e1 / t38
  t42 = 0.5e1 / 0.972e3 * t30 * t33 * t39
  t43 = tau0 * t32
  t45 = 0.1e1 / t20 / r0
  t47 = s0 * t32
  t48 = t47 * t22
  t50 = t43 * t45 - t48 / 0.8e1
  t51 = t50 ** 2
  t52 = t24 ** 2
  t55 = params.eta * s0
  t58 = 0.3e1 / 0.10e2 * t52 * t27 + t55 * t33 / 0.8e1
  t59 = t58 ** 2
  t60 = 0.1e1 / t59
  t62 = -t51 * t60 + 0.1e1
  t63 = t62 ** 2
  t64 = t63 * t62
  t65 = t51 * t50
  t66 = t59 * t58
  t67 = 0.1e1 / t66
  t69 = t51 ** 2
  t71 = params.b * t69 * t51
  t72 = t59 ** 2
  t74 = 0.1e1 / t72 / t59
  t76 = t65 * t67 + t71 * t74 + 0.1e1
  t77 = 0.1e1 / t76
  t78 = t64 * t77
  t81 = 0.5e1 / 0.972e3 * t29 * t48 + params.c
  t83 = t81 * t34 + 0.1e1
  t84 = 0.1e1 / t83
  t86 = t81 * t84 - t42
  t88 = t78 * t86 + t42 + 0.1e1
  t92 = t17 * t45
  t93 = t18 * r0
  t95 = 0.1e1 / t20 / t93
  t96 = t32 * t95
  t99 = 0.10e2 / 0.729e3 * t30 * t96 * t39
  t101 = 0.1e1 / t26 / t25
  t102 = t52 * t101
  t103 = s0 ** 2
  t104 = t102 * t103
  t105 = t18 ** 2
  t106 = t105 * t18
  t110 = t38 ** 2
  t112 = 0.1e1 / t110 * t34
  t115 = 0.25e2 / 0.177147e6 * t104 * t31 / t19 / t106 * t112
  t116 = t63 * t77
  t117 = t50 * t60
  t120 = t47 * t95
  t122 = -0.5e1 / 0.3e1 * t43 * t22 + t120 / 0.3e1
  t125 = t51 * t67
  t126 = t125 * params.eta
  t129 = -0.2e1 * t117 * t122 - 0.2e1 / 0.3e1 * t126 * t120
  t130 = t86 * t129
  t133 = t76 ** 2
  t134 = 0.1e1 / t133
  t135 = t64 * t134
  t138 = 0.1e1 / t72
  t140 = t65 * t138 * params.eta
  t143 = params.b * t69 * t50
  t144 = t74 * t122
  t148 = 0.1e1 / t72 / t66
  t149 = t71 * t148
  t150 = t55 * t96
  t153 = t140 * t120 + 0.3e1 * t125 * t122 + 0.6e1 * t143 * t144 + 0.2e1 * t149 * t150
  t154 = t86 * t153
  t159 = t83 ** 2
  t160 = 0.1e1 / t159
  t162 = t81 * t160 * t29
  t167 = -0.10e2 / 0.729e3 * t30 * t96 * t84 + 0.10e2 / 0.729e3 * t162 * t47 * t95 * t34 + t99 - t115
  t169 = 0.3e1 * t116 * t130 - t135 * t154 + t78 * t167 + t115 - t99
  t174 = t17 / t20
  t176 = 0.1e1 / t20 / t105
  t177 = t32 * t176
  t180 = 0.110e3 / 0.2187e4 * t30 * t177 * t39
  t183 = 0.1e1 / t19 / t105 / t93
  t184 = t31 * t183
  t187 = 0.25e2 / 0.19683e5 * t104 * t184 * t112
  t188 = t25 ** 2
  t189 = 0.1e1 / t188
  t190 = t103 * s0
  t191 = t189 * t190
  t192 = t105 ** 2
  t196 = 0.1e1 / t110 / t38
  t198 = params.kappa ** 2
  t199 = 0.1e1 / t198
  t202 = 0.2000e4 / 0.43046721e8 * t191 / t192 / t18 * t196 * t199
  t203 = t62 * t77
  t204 = t129 ** 2
  t205 = t86 * t204
  t208 = t63 * t134
  t212 = t167 * t129
  t215 = t122 ** 2
  t218 = t50 * t67
  t219 = t218 * t122
  t224 = t47 * t176
  t226 = 0.40e2 / 0.9e1 * t43 * t95 - 0.11e2 / 0.9e1 * t224
  t229 = t51 * t138
  t230 = params.eta ** 2
  t231 = t229 * t230
  t232 = t103 * t31
  t233 = t232 * t183
  t238 = -0.2e1 * t215 * t60 - 0.8e1 / 0.3e1 * t219 * t150 - 0.2e1 * t117 * t226 - 0.4e1 / 0.3e1 * t231 * t233 + 0.22e2 / 0.9e1 * t126 * t224
  t239 = t86 * t238
  t243 = 0.1e1 / t133 / t76
  t244 = t64 * t243
  t245 = t153 ** 2
  t246 = t86 * t245
  t249 = t167 * t153
  t254 = t229 * t122
  t260 = 0.1e1 / t72 / t58
  t262 = t65 * t260 * t230
  t267 = params.b * t69
  t268 = t74 * t215
  t271 = t148 * t122
  t272 = t143 * t271
  t278 = t72 ** 2
  t279 = 0.1e1 / t278
  t280 = t71 * t279
  t281 = t230 * t103
  t282 = t281 * t184
  t285 = t55 * t177
  t288 = 0.6e1 * t218 * t215 + 0.6e1 * t254 * t150 + 0.3e1 * t125 * t226 + 0.8e1 / 0.3e1 * t262 * t233 - 0.11e2 / 0.3e1 * t140 * t224 + 0.30e2 * t267 * t268 + 0.24e2 * t272 * t150 + 0.6e1 * t143 * t74 * t226 + 0.28e2 / 0.3e1 * t280 * t282 - 0.22e2 / 0.3e1 * t149 * t285
  t294 = t160 * t34
  t299 = 0.1e1 / t159 / t83
  t301 = t81 * t299 * t102
  t310 = 0.110e3 / 0.2187e4 * t30 * t177 * t84 - 0.400e3 / 0.531441e6 * t104 * t184 * t294 + 0.400e3 / 0.531441e6 * t301 * t232 * t183 * t199 - 0.110e3 / 0.2187e4 * t162 * t47 * t176 * t34 - t180 + t187 - t202
  t312 = -0.6e1 * t208 * t130 * t153 - t135 * t86 * t288 + 0.6e1 * t116 * t212 + 0.3e1 * t116 * t239 - 0.2e1 * t135 * t249 + 0.6e1 * t203 * t205 + 0.2e1 * t244 * t246 + t78 * t310 + t180 - t187 + t202
  t316 = t17 * t19
  t317 = t204 * t129
  t318 = t317 * t77
  t321 = t167 * t204
  t324 = t310 * t129
  t327 = t167 * t238
  t330 = t122 * t60
  t333 = t215 * t67
  t334 = t333 * params.eta
  t337 = t50 * t138
  t338 = t337 * t122
  t341 = t218 * t226
  t348 = t105 * r0
  t350 = 0.1e1 / t20 / t348
  t351 = t47 * t350
  t353 = -0.440e3 / 0.27e2 * t43 * t176 + 0.154e3 / 0.27e2 * t351
  t356 = t51 * t260
  t357 = t230 * params.eta
  t358 = t357 * t190
  t360 = 0.1e1 / t192 / t93
  t361 = t358 * t360
  t365 = 0.1e1 / t19 / t192
  t366 = t232 * t365
  t371 = -0.6e1 * t330 * t226 - 0.4e1 * t334 * t120 - 0.8e1 * t338 * t282 - 0.4e1 * t341 * t150 + 0.44e2 / 0.3e1 * t219 * t285 - 0.2e1 * t117 * t353 - 0.32e2 / 0.9e1 * t356 * t361 + 0.44e2 / 0.3e1 * t231 * t366 - 0.308e3 / 0.27e2 * t126 * t351
  t372 = t86 * t371
  t375 = t167 * t245
  t381 = t167 * t288
  t384 = t74 * t353
  t387 = t122 * t226
  t390 = t215 * t122
  t397 = t65 * t74
  t400 = params.b * t65
  t407 = t337 * t215
  t410 = t229 * t226
  t413 = t356 * t122
  t420 = t31 * t365
  t421 = t281 * t420
  t424 = t32 * t350
  t425 = t55 * t424
  t431 = t267 * t148 * t215
  t435 = t143 * t148 * t226
  t439 = t143 * t279 * t122
  t443 = 0.1e1 / t278 / t58
  t444 = t71 * t443
  t447 = 0.6e1 * t143 * t384 + 0.18e2 * t218 * t387 + 0.6e1 * t390 * t67 + 0.3e1 * t125 * t353 - 0.132e3 * t272 * t285 + 0.80e2 / 0.9e1 * t397 * t361 + 0.120e3 * t400 * t74 * t390 + 0.90e2 * t267 * t144 * t226 + 0.18e2 * t407 * t150 + 0.9e1 * t410 * t150 + 0.24e2 * t413 * t282 - 0.88e2 / 0.3e1 * t262 * t366 + 0.154e3 / 0.9e1 * t140 * t351 - 0.308e3 / 0.3e1 * t280 * t421 + 0.308e3 / 0.9e1 * t149 * t425 - 0.33e2 * t254 * t285 + 0.180e3 * t431 * t150 + 0.36e2 * t435 * t150 + 0.168e3 * t439 * t282 + 0.448e3 / 0.9e1 * t444 * t361
  t448 = t86 * t447
  t460 = t159 ** 2
  t461 = 0.1e1 / t460
  t463 = t81 * t461 * t189
  t464 = t190 * t360
  t466 = 0.1e1 / t198 / params.kappa
  t480 = 0.1540e4 / 0.6561e4 * t30 * t424 * t39
  t483 = 0.17050e5 / 0.1594323e7 * t104 * t420 * t112
  t487 = 0.38000e5 / 0.43046721e8 * t191 * t360 * t196 * t199
  t488 = t103 ** 2
  t489 = t189 * t488
  t493 = t110 ** 2
  t494 = 0.1e1 / t493
  t499 = t466 * t24 * t28 * t32
  t501 = 0.20000e5 / 0.10460353203e11 * t489 / t20 / t192 / t348 * t494 * t499
  t502 = -0.1540e4 / 0.6561e4 * t30 * t424 * t84 + 0.4400e4 / 0.531441e6 * t104 * t420 * t294 - 0.16000e5 / 0.43046721e8 * t191 * t360 * t299 * t199 + 0.16000e5 / 0.43046721e8 * t463 * t464 * t466 - 0.4400e4 / 0.531441e6 * t301 * t232 * t365 * t199 + 0.1540e4 / 0.6561e4 * t162 * t47 * t350 * t34 + t480 - t483 + t487 - t501
  t504 = -0.3e1 * t135 * t310 * t153 + 0.9e1 * t116 * t324 + 0.9e1 * t116 * t327 + 0.3e1 * t116 * t372 - 0.3e1 * t135 * t381 - t135 * t448 + 0.18e2 * t203 * t321 + 0.6e1 * t244 * t375 + 0.6e1 * t318 * t86 + t78 * t502 - t487
  t505 = t62 * t134
  t521 = t133 ** 2
  t522 = 0.1e1 / t521
  t523 = t64 * t522
  t524 = t245 * t153
  t525 = t86 * t524
  t531 = t63 * t243
  t535 = 0.18e2 * t203 * t130 * t238 - 0.9e1 * t208 * t130 * t288 + 0.18e2 * t531 * t130 * t245 - 0.18e2 * t505 * t205 * t153 - 0.18e2 * t208 * t212 * t153 - 0.9e1 * t208 * t239 * t153 + 0.6e1 * t244 * t154 * t288 - 0.6e1 * t523 * t525 - t480 + t483 + t501
  t536 = t504 + t535
  t541 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t88 + t6 * t92 * t169 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t174 * t312 - 0.3e1 / 0.8e1 * t6 * t316 * t536)
  t562 = t288 ** 2
  t569 = t245 ** 2
  t573 = t238 ** 2
  t581 = t215 ** 2
  t585 = t226 ** 2
  t592 = 0.1e1 / t20 / t106
  t593 = t47 * t592
  t595 = 0.6160e4 / 0.81e2 * t43 * t350 - 0.2618e4 / 0.81e2 * t593
  t638 = 0.24e2 * t218 * t122 * t353 + 0.360e3 * params.b * t51 * t74 * t581 + 0.90e2 * t267 * t74 * t585 + 0.6e1 * t143 * t74 * t595 + 0.36e2 * t333 * t226 + 0.18e2 * t218 * t585 + 0.3e1 * t125 * t595 + 0.1680e4 * t267 * t279 * t215 * t282 + 0.336e3 * t143 * t279 * t226 * t282 + 0.48e2 * t143 * t148 * t353 * t150 + 0.72e2 * t337 * t387 * t150 - 0.264e3 * t435 * t285 - 0.2464e4 * t439 * t421 + 0.960e3 * t400 * t148 * t390 * t150 - 0.1320e4 * t431 * t285 + 0.2464e4 / 0.3e1 * t272 * t425 + 0.120e3 * t267 * t384 * t122 + 0.720e3 * t400 * t268 * t226
  t640 = 0.1e1 / t192 / t105
  t641 = t358 * t640
  t654 = t230 ** 2
  t658 = 0.1e1 / t20 / t192 / t106
  t666 = t50 * t260
  t684 = 0.1e1 / t19 / t192 / r0
  t685 = t31 * t684
  t689 = t32 * t592
  t695 = t232 * t684
  t702 = t51 * t74
  t710 = t488 * t658 * t32
  t720 = -0.1760e4 / 0.9e1 * t397 * t641 - 0.132e3 * t407 * t285 + 0.3584e4 / 0.3e1 * t143 * t443 * t122 * t357 * t464 + 0.448e3 / 0.3e1 * t71 / t278 / t59 * t654 * t488 * t658 * t32 + 0.12e2 * t229 * t353 * t150 + 0.96e2 * t666 * t215 * t282 + 0.48e2 * t356 * t226 * t282 + 0.616e3 / 0.3e1 * t229 * params.eta * t47 * t350 * t122 - 0.66e2 * t410 * t285 - 0.352e3 * t413 * t421 + 0.27412e5 / 0.27e2 * t280 * t281 * t685 - 0.5236e4 / 0.27e2 * t149 * t55 * t689 - 0.2618e4 / 0.27e2 * t140 * t593 + 0.7832e4 / 0.27e2 * t262 * t695 + 0.24e2 * t390 * t138 * params.eta * t120 + 0.320e3 / 0.3e1 * t702 * t357 * t464 * t122 + 0.160e3 / 0.9e1 * t65 * t148 * t654 * t710 - 0.9856e4 / 0.9e1 * t444 * t641 + 0.720e3 * t267 * t271 * t226 * params.eta * t120
  t767 = -0.3916e4 / 0.27e2 * t231 * t695 + 0.5236e4 / 0.81e2 * t126 * t593 - 0.16e2 * t122 * t67 * t226 * t150 + 0.88e2 / 0.3e1 * t334 * t224 - 0.16e2 * t337 * t226 * t282 - 0.16e2 / 0.3e1 * t218 * t353 * t150 + 0.88e2 / 0.3e1 * t341 * t285 - 0.2464e4 / 0.27e2 * t219 * t425 + 0.352e3 / 0.3e1 * t338 * t421 - 0.16e2 * t215 * t138 * t230 * t233 - 0.256e3 / 0.9e1 * t666 * t122 * t361 + 0.704e3 / 0.9e1 * t356 * t641 - 0.160e3 / 0.27e2 * t702 * t654 * t710 - 0.6e1 * t585 * t60 - 0.8e1 * t330 * t353 - 0.2e1 * t117 * t595
  t813 = t198 ** 2
  t814 = 0.1e1 / t813
  t834 = 0.26180e5 / 0.19683e5 * t30 * t689 * t39
  t837 = 0.152350e6 / 0.1594323e7 * t104 * t685 * t112
  t841 = 0.5126000e7 / 0.387420489e9 * t191 * t640 * t196 * t199
  t845 = 0.1960000e7 / 0.31381059609e11 * t489 * t658 * t494 * t499
  t848 = t192 ** 2
  t860 = 0.1600000e7 / 0.7625597484987e13 * t189 * t488 * s0 / t19 / t848 / r0 / t493 / t38 * t814 * t52 * t101 * t31
  t861 = 0.26180e5 / 0.19683e5 * t30 * t689 * t84 - 0.391600e6 / 0.4782969e7 * t104 * t685 * t294 + 0.352000e6 / 0.43046721e8 * t191 * t640 * t299 * t199 - 0.640000e6 / 0.31381059609e11 * t489 * t658 * t461 * t499 + 0.640000e6 / 0.31381059609e11 * t81 / t460 / t83 * t489 * t658 * t814 * t29 * t32 - 0.352000e6 / 0.43046721e8 * t463 * t190 * t640 * t466 + 0.391600e6 / 0.4782969e7 * t301 * t232 * t684 * t199 - 0.26180e5 / 0.19683e5 * t162 * t47 * t592 * t34 - t834 + t837 - t841 + t845 - t860
  t866 = 0.12e2 * t116 * t502 * t129 + 0.18e2 * t116 * t310 * t238 - 0.24e2 * t317 * t134 * t154 + 0.36e2 * t203 * t310 * t204 + 0.36e2 * t204 * t77 * t239 - 0.18e2 * t208 * t239 * t288 + 0.24e2 * t318 * t167 + t78 * t861 + t841 - t845 + t860
  t932 = -0.72e2 * t63 * t522 * t525 * t129 + 0.24e2 * t203 * t372 * t129 - 0.36e2 * t208 * t381 * t129 - 0.12e2 * t208 * t448 * t129 - 0.36e2 * t208 * t324 * t153 - 0.36e2 * t208 * t327 * t153 - 0.12e2 * t208 * t372 * t153 + 0.8e1 * t244 * t448 * t153 - 0.72e2 * t505 * t321 * t153 + 0.72e2 * t203 * t212 * t238 - 0.36e2 * t523 * t246 * t288
  t939 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t95 * t88 - 0.5e1 / 0.9e1 * t6 * t23 * t169 + t6 * t92 * t312 / 0.2e1 - t6 * t174 * t536 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t316 * (-0.24e2 * t523 * t167 * t524 - 0.4e1 * t135 * t167 * t447 + 0.6e1 * t244 * t86 * t562 + 0.24e2 * t64 / t521 / t76 * t86 * t569 + 0.18e2 * t203 * t86 * t573 - t135 * t86 * (t638 + t720) - 0.4e1 * t135 * t502 * t153 + 0.3e1 * t116 * t86 * t767 + 0.12e2 * t244 * t310 * t245 + 0.12e2 * t116 * t167 * t371 + t866 - 0.72e2 * t505 * t86 * t129 * t153 * t238 + 0.72e2 * t531 * t86 * t129 * t288 * t153 + 0.72e2 * t62 * t243 * t205 * t245 + 0.72e2 * t531 * t375 * t129 - 0.6e1 * t135 * t310 * t288 - 0.36e2 * t505 * t205 * t288 + 0.36e2 * t531 * t239 * t245 + 0.24e2 * t244 * t249 * t288 + t834 - t837 + t932))
  v4rho4_0_ = 0.2e1 * r0 * t939 + 0.8e1 * t541

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
  t44 = 0.1e1 / params.kappa
  t48 = 0.1e1 + 0.5e1 / 0.972e3 * t37 * t43 * t44
  t49 = 0.1e1 / t48
  t52 = 0.5e1 / 0.972e3 * t37 * t43 * t49
  t57 = tau0 / t40 / r0 - t43 / 0.8e1
  t58 = t57 ** 2
  t59 = t32 ** 2
  t61 = 0.3e1 / 0.10e2 * t59 * t35
  t62 = params.eta * s0
  t65 = t61 + t62 * t42 / 0.8e1
  t66 = t65 ** 2
  t67 = 0.1e1 / t66
  t69 = -t58 * t67 + 0.1e1
  t70 = t69 ** 2
  t71 = t70 * t69
  t72 = t58 * t57
  t73 = t66 * t65
  t74 = 0.1e1 / t73
  t76 = t58 ** 2
  t78 = params.b * t76 * t58
  t79 = t66 ** 2
  t81 = 0.1e1 / t79 / t66
  t83 = t72 * t74 + t78 * t81 + 0.1e1
  t84 = 0.1e1 / t83
  t85 = t71 * t84
  t88 = 0.5e1 / 0.972e3 * t37 * t43 + params.c
  t90 = t88 * t44 + 0.1e1
  t91 = 0.1e1 / t90
  t93 = t88 * t91 - t52
  t95 = t85 * t93 + t52 + 0.1e1
  t99 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t100 = t99 * f.p.zeta_threshold
  t102 = f.my_piecewise3(t20, t100, t21 * t19)
  t103 = t30 ** 2
  t104 = 0.1e1 / t103
  t105 = t102 * t104
  t108 = t5 * t105 * t95 / 0.8e1
  t109 = t102 * t30
  t110 = t38 * r0
  t112 = 0.1e1 / t40 / t110
  t113 = s0 * t112
  t116 = 0.10e2 / 0.729e3 * t37 * t113 * t49
  t118 = 0.1e1 / t34 / t33
  t119 = t59 * t118
  t120 = s0 ** 2
  t121 = t119 * t120
  t122 = t38 ** 2
  t126 = t48 ** 2
  t127 = 0.1e1 / t126
  t131 = 0.25e2 / 0.354294e6 * t121 / t39 / t122 / t38 * t127 * t44
  t132 = t70 * t84
  t133 = t57 * t67
  t137 = -0.5e1 / 0.3e1 * tau0 * t42 + t113 / 0.3e1
  t140 = t58 * t74
  t141 = t62 * t112
  t144 = -0.2e1 * t133 * t137 - 0.2e1 / 0.3e1 * t140 * t141
  t145 = t93 * t144
  t148 = t83 ** 2
  t149 = 0.1e1 / t148
  t150 = t71 * t149
  t153 = 0.1e1 / t79
  t154 = t72 * t153
  t157 = params.b * t76 * t57
  t162 = 0.1e1 / t79 / t73
  t163 = t78 * t162
  t166 = 0.6e1 * t157 * t81 * t137 + 0.3e1 * t140 * t137 + t154 * t141 + 0.2e1 * t163 * t141
  t172 = t90 ** 2
  t173 = 0.1e1 / t172
  t175 = t88 * t173 * t32
  t176 = t36 * s0
  t181 = -0.10e2 / 0.729e3 * t37 * t113 * t91 + 0.10e2 / 0.729e3 * t175 * t176 * t112 * t44 + t116 - t131
  t183 = -t150 * t93 * t166 + 0.3e1 * t132 * t145 + t85 * t181 - t116 + t131
  t188 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t95 - t108 - 0.3e1 / 0.8e1 * t5 * t109 * t183)
  t190 = r1 <= f.p.dens_threshold
  t191 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t192 = 0.1e1 + t191
  t193 = t192 <= f.p.zeta_threshold
  t194 = t192 ** (0.1e1 / 0.3e1)
  t196 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t199 = f.my_piecewise3(t193, 0, 0.4e1 / 0.3e1 * t194 * t196)
  t200 = t199 * t30
  t201 = r1 ** 2
  t202 = r1 ** (0.1e1 / 0.3e1)
  t203 = t202 ** 2
  t205 = 0.1e1 / t203 / t201
  t206 = s2 * t205
  t210 = 0.1e1 + 0.5e1 / 0.972e3 * t37 * t206 * t44
  t211 = 0.1e1 / t210
  t214 = 0.5e1 / 0.972e3 * t37 * t206 * t211
  t219 = tau1 / t203 / r1 - t206 / 0.8e1
  t220 = t219 ** 2
  t221 = params.eta * s2
  t224 = t61 + t221 * t205 / 0.8e1
  t225 = t224 ** 2
  t226 = 0.1e1 / t225
  t228 = -t220 * t226 + 0.1e1
  t229 = t228 ** 2
  t230 = t229 * t228
  t231 = t220 * t219
  t232 = t225 * t224
  t233 = 0.1e1 / t232
  t235 = t220 ** 2
  t237 = params.b * t235 * t220
  t238 = t225 ** 2
  t240 = 0.1e1 / t238 / t225
  t242 = t231 * t233 + t237 * t240 + 0.1e1
  t243 = 0.1e1 / t242
  t244 = t230 * t243
  t247 = 0.5e1 / 0.972e3 * t37 * t206 + params.c
  t249 = t247 * t44 + 0.1e1
  t250 = 0.1e1 / t249
  t252 = t247 * t250 - t214
  t254 = t244 * t252 + t214 + 0.1e1
  t259 = f.my_piecewise3(t193, t100, t194 * t192)
  t260 = t259 * t104
  t263 = t5 * t260 * t254 / 0.8e1
  t265 = f.my_piecewise3(t190, 0, -0.3e1 / 0.8e1 * t5 * t200 * t254 - t263)
  t267 = t21 ** 2
  t268 = 0.1e1 / t267
  t269 = t26 ** 2
  t274 = t16 / t22 / t6
  t276 = -0.2e1 * t23 + 0.2e1 * t274
  t277 = f.my_piecewise5(t10, 0, t14, 0, t276)
  t281 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t268 * t269 + 0.4e1 / 0.3e1 * t21 * t277)
  t288 = t5 * t29 * t104 * t95
  t294 = 0.1e1 / t103 / t6
  t298 = t5 * t102 * t294 * t95 / 0.12e2
  t300 = t5 * t105 * t183
  t303 = 0.1e1 / t40 / t122
  t304 = s0 * t303
  t307 = 0.110e3 / 0.2187e4 * t37 * t304 * t49
  t310 = 0.1e1 / t39 / t122 / t110
  t314 = 0.25e2 / 0.39366e5 * t121 * t310 * t127 * t44
  t315 = t33 ** 2
  t316 = 0.1e1 / t315
  t319 = t122 ** 2
  t325 = params.kappa ** 2
  t326 = 0.1e1 / t325
  t329 = 0.500e3 / 0.43046721e8 * t316 * t120 * s0 / t319 / t38 / t126 / t48 * t326
  t331 = t144 ** 2
  t342 = t137 ** 2
  t345 = t57 * t74
  t352 = 0.40e2 / 0.9e1 * tau0 * t112 - 0.11e2 / 0.9e1 * t304
  t355 = t58 * t153
  t356 = params.eta ** 2
  t358 = t356 * t120 * t310
  t361 = t62 * t303
  t371 = t166 ** 2
  t404 = t79 ** 2
  t436 = t307 - t314 + t329 + 0.6e1 * t69 * t84 * t93 * t331 - 0.6e1 * t70 * t149 * t145 * t166 + 0.6e1 * t132 * t181 * t144 + 0.3e1 * t132 * t93 * (-0.2e1 * t342 * t67 - 0.8e1 / 0.3e1 * t345 * t137 * t141 - 0.2e1 * t133 * t352 - 0.2e1 / 0.3e1 * t355 * t358 + 0.22e2 / 0.9e1 * t140 * t361) + 0.2e1 * t71 / t148 / t83 * t93 * t371 - 0.2e1 * t150 * t181 * t166 - t150 * t93 * (0.6e1 * t345 * t342 + 0.6e1 * t355 * t137 * t141 + 0.3e1 * t140 * t352 + 0.4e1 / 0.3e1 * t72 / t79 / t65 * t358 - 0.11e2 / 0.3e1 * t154 * t361 + 0.30e2 * params.b * t76 * t81 * t342 + 0.24e2 * t157 * t162 * t137 * params.eta * t113 + 0.6e1 * t157 * t81 * t352 + 0.14e2 / 0.3e1 * t78 / t404 * t358 - 0.22e2 / 0.3e1 * t163 * t361) + t85 * (0.110e3 / 0.2187e4 * t37 * t304 * t91 - 0.200e3 / 0.531441e6 * t121 * t310 * t173 * t44 + 0.200e3 / 0.531441e6 * t88 / t172 / t90 * t59 * t118 * t120 * t310 * t326 - 0.110e3 / 0.2187e4 * t175 * t176 * t303 * t44 - t307 + t314 - t329)
  t441 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t281 * t30 * t95 - t288 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t183 + t298 - t300 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t109 * t436)
  t442 = t194 ** 2
  t443 = 0.1e1 / t442
  t444 = t196 ** 2
  t448 = f.my_piecewise5(t14, 0, t10, 0, -t276)
  t452 = f.my_piecewise3(t193, 0, 0.4e1 / 0.9e1 * t443 * t444 + 0.4e1 / 0.3e1 * t194 * t448)
  t459 = t5 * t199 * t104 * t254
  t464 = t5 * t259 * t294 * t254 / 0.12e2
  t466 = f.my_piecewise3(t190, 0, -0.3e1 / 0.8e1 * t5 * t452 * t30 * t254 - t459 / 0.4e1 + t464)
  d11 = 0.2e1 * t188 + 0.2e1 * t265 + t6 * (t441 + t466)
  t469 = -t7 - t24
  t470 = f.my_piecewise5(t10, 0, t14, 0, t469)
  t473 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t470)
  t474 = t473 * t30
  t479 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t474 * t95 - t108)
  t481 = f.my_piecewise5(t14, 0, t10, 0, -t469)
  t484 = f.my_piecewise3(t193, 0, 0.4e1 / 0.3e1 * t194 * t481)
  t485 = t484 * t30
  t489 = t259 * t30
  t490 = t201 * r1
  t492 = 0.1e1 / t203 / t490
  t493 = s2 * t492
  t496 = 0.10e2 / 0.729e3 * t37 * t493 * t211
  t497 = s2 ** 2
  t498 = t119 * t497
  t499 = t201 ** 2
  t503 = t210 ** 2
  t504 = 0.1e1 / t503
  t508 = 0.25e2 / 0.354294e6 * t498 / t202 / t499 / t201 * t504 * t44
  t509 = t229 * t243
  t510 = t219 * t226
  t514 = -0.5e1 / 0.3e1 * tau1 * t205 + t493 / 0.3e1
  t517 = t220 * t233
  t518 = t221 * t492
  t521 = -0.2e1 * t510 * t514 - 0.2e1 / 0.3e1 * t517 * t518
  t522 = t252 * t521
  t525 = t242 ** 2
  t526 = 0.1e1 / t525
  t527 = t230 * t526
  t530 = 0.1e1 / t238
  t531 = t231 * t530
  t534 = params.b * t235 * t219
  t539 = 0.1e1 / t238 / t232
  t540 = t237 * t539
  t543 = 0.6e1 * t534 * t240 * t514 + 0.3e1 * t517 * t514 + t531 * t518 + 0.2e1 * t540 * t518
  t549 = t249 ** 2
  t550 = 0.1e1 / t549
  t552 = t247 * t550 * t32
  t553 = t36 * s2
  t558 = -0.10e2 / 0.729e3 * t37 * t493 * t250 + 0.10e2 / 0.729e3 * t552 * t553 * t492 * t44 + t496 - t508
  t560 = -t527 * t252 * t543 + t244 * t558 + 0.3e1 * t509 * t522 - t496 + t508
  t565 = f.my_piecewise3(t190, 0, -0.3e1 / 0.8e1 * t5 * t485 * t254 - t263 - 0.3e1 / 0.8e1 * t5 * t489 * t560)
  t569 = 0.2e1 * t274
  t570 = f.my_piecewise5(t10, 0, t14, 0, t569)
  t574 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t268 * t470 * t26 + 0.4e1 / 0.3e1 * t21 * t570)
  t581 = t5 * t473 * t104 * t95
  t589 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t574 * t30 * t95 - t581 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t474 * t183 - t288 / 0.8e1 + t298 - t300 / 0.8e1)
  t593 = f.my_piecewise5(t14, 0, t10, 0, -t569)
  t597 = f.my_piecewise3(t193, 0, 0.4e1 / 0.9e1 * t443 * t481 * t196 + 0.4e1 / 0.3e1 * t194 * t593)
  t604 = t5 * t484 * t104 * t254
  t611 = t5 * t260 * t560
  t614 = f.my_piecewise3(t190, 0, -0.3e1 / 0.8e1 * t5 * t597 * t30 * t254 - t604 / 0.8e1 - t459 / 0.8e1 + t464 - 0.3e1 / 0.8e1 * t5 * t200 * t560 - t611 / 0.8e1)
  d12 = t188 + t265 + t479 + t565 + t6 * (t589 + t614)
  t619 = t470 ** 2
  t623 = 0.2e1 * t23 + 0.2e1 * t274
  t624 = f.my_piecewise5(t10, 0, t14, 0, t623)
  t628 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t268 * t619 + 0.4e1 / 0.3e1 * t21 * t624)
  t635 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t628 * t30 * t95 - t581 / 0.4e1 + t298)
  t636 = t481 ** 2
  t640 = f.my_piecewise5(t14, 0, t10, 0, -t623)
  t644 = f.my_piecewise3(t193, 0, 0.4e1 / 0.9e1 * t443 * t636 + 0.4e1 / 0.3e1 * t194 * t640)
  t655 = 0.1e1 / t203 / t499
  t656 = s2 * t655
  t659 = 0.110e3 / 0.2187e4 * t37 * t656 * t211
  t662 = 0.1e1 / t202 / t499 / t490
  t666 = 0.25e2 / 0.39366e5 * t498 * t662 * t504 * t44
  t669 = t499 ** 2
  t677 = 0.500e3 / 0.43046721e8 * t316 * t497 * s2 / t669 / t201 / t503 / t210 * t326
  t679 = t521 ** 2
  t690 = t514 ** 2
  t693 = t219 * t233
  t700 = 0.40e2 / 0.9e1 * tau1 * t492 - 0.11e2 / 0.9e1 * t656
  t703 = t220 * t530
  t705 = t356 * t497 * t662
  t708 = t221 * t655
  t718 = t543 ** 2
  t751 = t238 ** 2
  t783 = t659 - t666 + t677 + 0.6e1 * t228 * t243 * t252 * t679 - 0.6e1 * t229 * t526 * t522 * t543 + 0.6e1 * t509 * t558 * t521 + 0.3e1 * t509 * t252 * (-0.2e1 * t690 * t226 - 0.8e1 / 0.3e1 * t693 * t514 * t518 - 0.2e1 * t510 * t700 - 0.2e1 / 0.3e1 * t703 * t705 + 0.22e2 / 0.9e1 * t517 * t708) + 0.2e1 * t230 / t525 / t242 * t252 * t718 - 0.2e1 * t527 * t558 * t543 - t527 * t252 * (0.6e1 * t693 * t690 + 0.6e1 * t703 * t514 * t518 + 0.3e1 * t517 * t700 + 0.4e1 / 0.3e1 * t231 / t238 / t224 * t705 - 0.11e2 / 0.3e1 * t531 * t708 + 0.30e2 * params.b * t235 * t240 * t690 + 0.24e2 * t534 * t539 * t514 * params.eta * t493 + 0.6e1 * t534 * t240 * t700 + 0.14e2 / 0.3e1 * t237 / t751 * t705 - 0.22e2 / 0.3e1 * t540 * t708) + t244 * (0.110e3 / 0.2187e4 * t37 * t656 * t250 - 0.200e3 / 0.531441e6 * t498 * t662 * t550 * t44 + 0.200e3 / 0.531441e6 * t247 / t549 / t249 * t59 * t118 * t497 * t662 * t326 - 0.110e3 / 0.2187e4 * t552 * t553 * t655 * t44 - t659 + t666 - t677)
  t788 = f.my_piecewise3(t190, 0, -0.3e1 / 0.8e1 * t5 * t644 * t30 * t254 - t604 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t485 * t560 + t464 - t611 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t489 * t783)
  d22 = 0.2e1 * t479 + 0.2e1 * t565 + t6 * (t635 + t788)
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
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
  t68 = 0.1e1 / params.kappa
  t72 = 0.1e1 + 0.5e1 / 0.972e3 * t61 * t67 * t68
  t73 = 0.1e1 / t72
  t76 = 0.5e1 / 0.972e3 * t61 * t67 * t73
  t81 = tau0 / t64 / r0 - t67 / 0.8e1
  t82 = t81 ** 2
  t83 = t56 ** 2
  t85 = 0.3e1 / 0.10e2 * t83 * t59
  t86 = params.eta * s0
  t89 = t85 + t86 * t66 / 0.8e1
  t90 = t89 ** 2
  t91 = 0.1e1 / t90
  t93 = -t82 * t91 + 0.1e1
  t94 = t93 ** 2
  t95 = t94 * t93
  t96 = t82 * t81
  t97 = t90 * t89
  t98 = 0.1e1 / t97
  t100 = t82 ** 2
  t102 = params.b * t100 * t82
  t103 = t90 ** 2
  t105 = 0.1e1 / t103 / t90
  t107 = t102 * t105 + t96 * t98 + 0.1e1
  t108 = 0.1e1 / t107
  t109 = t95 * t108
  t112 = 0.5e1 / 0.972e3 * t61 * t67 + params.c
  t114 = t112 * t68 + 0.1e1
  t115 = 0.1e1 / t114
  t117 = t112 * t115 - t76
  t119 = t109 * t117 + t76 + 0.1e1
  t128 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t129 = t54 ** 2
  t130 = 0.1e1 / t129
  t131 = t128 * t130
  t135 = t128 * t54
  t136 = t62 * r0
  t138 = 0.1e1 / t64 / t136
  t139 = s0 * t138
  t142 = 0.10e2 / 0.729e3 * t61 * t139 * t73
  t144 = 0.1e1 / t58 / t57
  t145 = t83 * t144
  t146 = s0 ** 2
  t147 = t145 * t146
  t148 = t62 ** 2
  t149 = t148 * t62
  t152 = t72 ** 2
  t153 = 0.1e1 / t152
  t157 = 0.25e2 / 0.354294e6 * t147 / t63 / t149 * t153 * t68
  t158 = t94 * t108
  t159 = t81 * t91
  t163 = -0.5e1 / 0.3e1 * tau0 * t66 + t139 / 0.3e1
  t166 = t82 * t98
  t167 = t86 * t138
  t170 = -0.2e1 * t159 * t163 - 0.2e1 / 0.3e1 * t166 * t167
  t171 = t117 * t170
  t174 = t107 ** 2
  t175 = 0.1e1 / t174
  t176 = t95 * t175
  t179 = 0.1e1 / t103
  t180 = t96 * t179
  t183 = params.b * t100 * t81
  t184 = t105 * t163
  t188 = 0.1e1 / t103 / t97
  t189 = t102 * t188
  t192 = 0.3e1 * t166 * t163 + t180 * t167 + 0.2e1 * t189 * t167 + 0.6e1 * t183 * t184
  t193 = t117 * t192
  t198 = t114 ** 2
  t199 = 0.1e1 / t198
  t201 = t112 * t199 * t56
  t202 = t60 * s0
  t207 = -0.10e2 / 0.729e3 * t61 * t139 * t115 + 0.10e2 / 0.729e3 * t201 * t202 * t138 * t68 + t142 - t157
  t209 = t109 * t207 + 0.3e1 * t158 * t171 - t176 * t193 - t142 + t157
  t215 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t217 = 0.1e1 / t129 / t6
  t218 = t215 * t217
  t222 = t215 * t130
  t226 = t215 * t54
  t228 = 0.1e1 / t64 / t148
  t229 = s0 * t228
  t232 = 0.110e3 / 0.2187e4 * t61 * t229 * t73
  t235 = 0.1e1 / t63 / t148 / t136
  t239 = 0.25e2 / 0.39366e5 * t147 * t235 * t153 * t68
  t240 = t57 ** 2
  t241 = 0.1e1 / t240
  t242 = t146 * s0
  t243 = t241 * t242
  t244 = t148 ** 2
  t248 = 0.1e1 / t152 / t72
  t250 = params.kappa ** 2
  t251 = 0.1e1 / t250
  t254 = 0.500e3 / 0.43046721e8 * t243 / t244 / t62 * t248 * t251
  t255 = t93 * t108
  t256 = t170 ** 2
  t257 = t117 * t256
  t260 = t94 * t175
  t264 = t207 * t170
  t267 = t163 ** 2
  t270 = t81 * t98
  t271 = t270 * t163
  t277 = 0.40e2 / 0.9e1 * tau0 * t138 - 0.11e2 / 0.9e1 * t229
  t280 = t82 * t179
  t281 = params.eta ** 2
  t282 = t281 * t146
  t283 = t282 * t235
  t286 = t86 * t228
  t289 = -0.2e1 * t267 * t91 - 0.8e1 / 0.3e1 * t271 * t167 - 0.2e1 * t159 * t277 - 0.2e1 / 0.3e1 * t280 * t283 + 0.22e2 / 0.9e1 * t166 * t286
  t290 = t117 * t289
  t294 = 0.1e1 / t174 / t107
  t295 = t95 * t294
  t296 = t192 ** 2
  t297 = t117 * t296
  t305 = t280 * t163
  t311 = 0.1e1 / t103 / t89
  t312 = t96 * t311
  t317 = params.b * t100
  t318 = t105 * t267
  t321 = t183 * t188
  t322 = t163 * params.eta
  t329 = t103 ** 2
  t330 = 0.1e1 / t329
  t331 = t102 * t330
  t336 = 0.6e1 * t270 * t267 + 0.6e1 * t305 * t167 + 0.3e1 * t166 * t277 + 0.4e1 / 0.3e1 * t312 * t283 - 0.11e2 / 0.3e1 * t180 * t286 + 0.30e2 * t317 * t318 + 0.24e2 * t321 * t322 * t139 + 0.6e1 * t183 * t105 * t277 + 0.14e2 / 0.3e1 * t331 * t283 - 0.22e2 / 0.3e1 * t189 * t286
  t347 = 0.1e1 / t198 / t114
  t349 = t112 * t347 * t83
  t350 = t144 * t146
  t359 = 0.110e3 / 0.2187e4 * t61 * t229 * t115 - 0.200e3 / 0.531441e6 * t147 * t235 * t199 * t68 + 0.200e3 / 0.531441e6 * t349 * t350 * t235 * t251 - 0.110e3 / 0.2187e4 * t201 * t202 * t228 * t68 - t232 + t239 - t254
  t361 = -t176 * t117 * t336 - 0.6e1 * t260 * t171 * t192 - 0.2e1 * t176 * t207 * t192 + t109 * t359 + 0.6e1 * t158 * t264 + 0.3e1 * t158 * t290 + 0.6e1 * t255 * t257 + 0.2e1 * t295 * t297 + t232 - t239 + t254
  t365 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t366 = t365 * f.p.zeta_threshold
  t368 = f.my_piecewise3(t20, t366, t21 * t19)
  t370 = 0.1e1 / t129 / t25
  t371 = t368 * t370
  t375 = t368 * t217
  t379 = t368 * t130
  t383 = t368 * t54
  t384 = t359 * t192
  t387 = t207 * t336
  t395 = t148 * r0
  t397 = 0.1e1 / t64 / t395
  t398 = s0 * t397
  t400 = -0.440e3 / 0.27e2 * tau0 * t228 + 0.154e3 / 0.27e2 * t398
  t401 = t105 * t400
  t404 = t96 * t105
  t405 = t281 * params.eta
  t406 = t405 * t242
  t408 = 0.1e1 / t244 / t136
  t409 = t406 * t408
  t412 = params.b * t96
  t413 = t267 * t163
  t426 = t317 * t188
  t427 = t267 * params.eta
  t431 = t277 * params.eta
  t432 = t431 * t139
  t435 = t183 * t330
  t436 = t163 * t281
  t437 = t146 * t235
  t442 = 0.1e1 / t63 / t244
  t443 = t282 * t442
  t446 = t86 * t397
  t452 = t81 * t179
  t453 = t452 * t267
  t456 = t280 * t277
  t459 = t82 * t311
  t460 = t459 * t163
  t468 = 0.1e1 / t329 / t89
  t469 = t102 * t468
  t472 = 0.18e2 * t270 * t163 * t277 + 0.6e1 * t183 * t401 + 0.20e2 / 0.9e1 * t404 * t409 + 0.120e3 * t412 * t105 * t413 + 0.90e2 * t317 * t184 * t277 + 0.6e1 * t413 * t98 + 0.3e1 * t166 * t400 - 0.33e2 * t305 * t286 + 0.180e3 * t426 * t427 * t139 + 0.36e2 * t321 * t432 + 0.84e2 * t435 * t436 * t437 - 0.154e3 / 0.3e1 * t331 * t443 + 0.308e3 / 0.9e1 * t189 * t446 - 0.132e3 * t321 * t322 * t229 + 0.18e2 * t453 * t167 + 0.9e1 * t456 * t167 + 0.12e2 * t460 * t283 - 0.44e2 / 0.3e1 * t312 * t443 + 0.154e3 / 0.9e1 * t180 * t446 + 0.112e3 / 0.9e1 * t469 * t409
  t473 = t117 * t472
  t478 = 0.9500e4 / 0.43046721e8 * t243 * t408 * t248 * t251
  t479 = t93 * t175
  t495 = t174 ** 2
  t496 = 0.1e1 / t495
  t497 = t95 * t496
  t498 = t296 * t192
  t499 = t117 * t498
  t505 = 0.18e2 * t255 * t171 * t289 - 0.9e1 * t260 * t171 * t336 - 0.18e2 * t479 * t257 * t192 - 0.18e2 * t260 * t264 * t192 - 0.9e1 * t260 * t290 * t192 + 0.6e1 * t295 * t193 * t336 - 0.3e1 * t176 * t384 - 0.3e1 * t176 * t387 - t176 * t473 - 0.6e1 * t497 * t499 - t478
  t517 = t198 ** 2
  t518 = 0.1e1 / t517
  t520 = t112 * t518 * t241
  t521 = t242 * t408
  t523 = 0.1e1 / t250 / params.kappa
  t537 = 0.1540e4 / 0.6561e4 * t61 * t398 * t73
  t541 = 0.8525e4 / 0.1594323e7 * t147 * t442 * t153 * t68
  t542 = t146 ** 2
  t543 = t241 * t542
  t548 = t152 ** 2
  t551 = 0.1e1 / t548 * t523 * t61
  t553 = 0.5000e4 / 0.10460353203e11 * t543 / t64 / t244 / t395 * t551
  t554 = -0.1540e4 / 0.6561e4 * t61 * t398 * t115 + 0.2200e4 / 0.531441e6 * t147 * t442 * t199 * t68 - 0.4000e4 / 0.43046721e8 * t243 * t408 * t347 * t251 + 0.4000e4 / 0.43046721e8 * t520 * t521 * t523 - 0.2200e4 / 0.531441e6 * t349 * t350 * t442 * t251 + 0.1540e4 / 0.6561e4 * t201 * t202 * t397 * t68 + t537 - t541 + t478 - t553
  t556 = t256 * t170
  t557 = t556 * t108
  t560 = t207 * t256
  t566 = t207 * t289
  t569 = t163 * t91
  t572 = t267 * t98
  t575 = t452 * t163
  t578 = t270 * t277
  t591 = -0.6e1 * t569 * t277 - 0.4e1 * t572 * t167 - 0.4e1 * t575 * t283 - 0.4e1 * t578 * t167 + 0.44e2 / 0.3e1 * t271 * t286 - 0.2e1 * t159 * t400 - 0.8e1 / 0.9e1 * t459 * t409 + 0.22e2 / 0.3e1 * t280 * t443 - 0.308e3 / 0.27e2 * t166 * t446
  t592 = t117 * t591
  t598 = t94 * t294
  t602 = 0.9e1 * t158 * t359 * t170 + 0.18e2 * t598 * t171 * t296 + 0.6e1 * t295 * t207 * t296 + t109 * t554 + 0.6e1 * t557 * t117 + 0.9e1 * t158 * t566 + 0.3e1 * t158 * t592 + 0.18e2 * t255 * t560 - t537 + t541 + t553
  t603 = t505 + t602
  t608 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t119 - 0.3e1 / 0.8e1 * t5 * t131 * t119 - 0.9e1 / 0.8e1 * t5 * t135 * t209 + t5 * t218 * t119 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t222 * t209 - 0.9e1 / 0.8e1 * t5 * t226 * t361 - 0.5e1 / 0.36e2 * t5 * t371 * t119 + t5 * t375 * t209 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t379 * t361 - 0.3e1 / 0.8e1 * t5 * t383 * t603)
  t610 = r1 <= f.p.dens_threshold
  t611 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t612 = 0.1e1 + t611
  t613 = t612 <= f.p.zeta_threshold
  t614 = t612 ** (0.1e1 / 0.3e1)
  t615 = t614 ** 2
  t617 = 0.1e1 / t615 / t612
  t619 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t620 = t619 ** 2
  t624 = 0.1e1 / t615
  t625 = t624 * t619
  t627 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t631 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t635 = f.my_piecewise3(t613, 0, -0.8e1 / 0.27e2 * t617 * t620 * t619 + 0.4e1 / 0.3e1 * t625 * t627 + 0.4e1 / 0.3e1 * t614 * t631)
  t637 = r1 ** 2
  t638 = r1 ** (0.1e1 / 0.3e1)
  t639 = t638 ** 2
  t641 = 0.1e1 / t639 / t637
  t642 = s2 * t641
  t650 = 0.5e1 / 0.972e3 * t61 * t642 / (0.1e1 + 0.5e1 / 0.972e3 * t61 * t642 * t68)
  t655 = tau1 / t639 / r1 - t642 / 0.8e1
  t656 = t655 ** 2
  t660 = t85 + params.eta * s2 * t641 / 0.8e1
  t661 = t660 ** 2
  t664 = 0.1e1 - t656 / t661
  t665 = t664 ** 2
  t671 = t656 ** 2
  t674 = t661 ** 2
  t683 = 0.5e1 / 0.972e3 * t61 * t642 + params.c
  t690 = 0.1e1 + t650 + t665 * t664 / (0.1e1 + t656 * t655 / t661 / t660 + params.b * t671 * t656 / t674 / t661) * (t683 / (t683 * t68 + 0.1e1) - t650)
  t699 = f.my_piecewise3(t613, 0, 0.4e1 / 0.9e1 * t624 * t620 + 0.4e1 / 0.3e1 * t614 * t627)
  t706 = f.my_piecewise3(t613, 0, 0.4e1 / 0.3e1 * t614 * t619)
  t712 = f.my_piecewise3(t613, t366, t614 * t612)
  t718 = f.my_piecewise3(t610, 0, -0.3e1 / 0.8e1 * t5 * t635 * t54 * t690 - 0.3e1 / 0.8e1 * t5 * t699 * t130 * t690 + t5 * t706 * t217 * t690 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t712 * t370 * t690)
  t737 = 0.1e1 / t63 / t244 / r0
  t741 = 0.76175e5 / 0.1594323e7 * t147 * t737 * t153 * t68
  t747 = 0.1e1 / t64 / t149
  t748 = s0 * t747
  t751 = 0.26180e5 / 0.19683e5 * t61 * t748 * t73
  t753 = 0.1e1 / t244 / t148
  t757 = 0.1281500e7 / 0.387420489e9 * t243 * t753 * t248 * t251
  t810 = 0.1e1 / t64 / t244 / t149
  t811 = t543 * t810
  t813 = 0.490000e6 / 0.31381059609e11 * t811 * t551
  t814 = -0.36e2 * t260 * t384 * t170 - 0.36e2 * t260 * t387 * t170 - 0.36e2 * t260 * t566 * t192 - 0.12e2 * t260 * t592 * t192 + 0.24e2 * t295 * t387 * t192 - 0.72e2 * t479 * t560 * t192 - 0.36e2 * t479 * t257 * t336 - 0.18e2 * t260 * t290 * t336 + 0.72e2 * t598 * t264 * t296 - 0.36e2 * t497 * t297 * t336 - t813
  t818 = t244 ** 2
  t825 = t250 ** 2
  t826 = 0.1e1 / t825
  t830 = 0.200000e6 / 0.7625597484987e13 * t241 * t542 * s0 / t63 / t818 / r0 / t548 / t72 * t826 * t145
  t866 = 0.26180e5 / 0.19683e5 * t61 * t748 * t115 - 0.195800e6 / 0.4782969e7 * t147 * t737 * t199 * t68 + 0.88000e5 / 0.43046721e8 * t243 * t753 * t347 * t251 - 0.160000e6 / 0.31381059609e11 * t811 * t518 * t523 * t61 + 0.160000e6 / 0.31381059609e11 * t112 / t517 / t114 * t543 * t810 * t826 * t61 - 0.88000e5 / 0.43046721e8 * t520 * t242 * t753 * t523 + 0.195800e6 / 0.4782969e7 * t349 * t350 * t737 * t251 - 0.26180e5 / 0.19683e5 * t201 * t202 * t747 * t68 - t751 + t741 - t757 + t813 - t830
  t874 = t281 ** 2
  t876 = t874 * t542 * t810
  t885 = t406 * t753
  t888 = t282 * t737
  t891 = t86 * t747
  t936 = 0.6160e4 / 0.81e2 * tau0 * t397 - 0.2618e4 / 0.81e2 * t748
  t939 = 0.120e3 * t317 * t401 * t163 + 0.40e2 / 0.9e1 * t96 * t188 * t876 + 0.720e3 * t412 * t318 * t277 + 0.24e2 * t413 * t179 * t167 - 0.440e3 / 0.9e1 * t404 * t885 + 0.3916e4 / 0.27e2 * t312 * t888 - 0.2618e4 / 0.27e2 * t180 * t891 + 0.840e3 * t317 * t330 * t267 * t281 * t437 + 0.168e3 * t435 * t277 * t281 * t437 + 0.896e3 / 0.3e1 * t183 * t468 * t163 * t405 * t521 + 0.2464e4 / 0.3e1 * t321 * t86 * t397 * t163 + 0.72e2 * t575 * t432 + 0.48e2 * t321 * t400 * params.eta * t139 + 0.960e3 * t412 * t188 * t413 * params.eta * t139 - 0.1320e4 * t426 * t427 * t229 - 0.264e3 * t321 * t431 * t229 - 0.1232e4 * t435 * t436 * t146 * t442 + 0.3e1 * t166 * t936
  t942 = t277 ** 2
  t946 = t267 ** 2
  t967 = t82 * t105
  t981 = t81 * t311
  t997 = 0.36e2 * t572 * t277 + 0.18e2 * t270 * t942 + 0.360e3 * params.b * t82 * t105 * t946 + 0.90e2 * t317 * t105 * t942 + 0.24e2 * t270 * t163 * t400 + 0.6e1 * t183 * t105 * t936 + 0.13706e5 / 0.27e2 * t331 * t888 - 0.5236e4 / 0.27e2 * t189 * t891 - 0.132e3 * t453 * t286 + 0.616e3 / 0.3e1 * t305 * t446 + 0.80e2 / 0.3e1 * t967 * t405 * t521 * t163 + 0.12e2 * t280 * t400 * t167 - 0.66e2 * t456 * t286 - 0.176e3 * t460 * t443 - 0.2464e4 / 0.9e1 * t469 * t885 + 0.48e2 * t981 * t267 * t283 + 0.24e2 * t459 * t277 * t283 + 0.112e3 / 0.3e1 * t102 / t329 / t90 * t876 + 0.720e3 * t317 * t188 * t163 * t432
  t1019 = t296 ** 2
  t1024 = t336 ** 2
  t1040 = t289 ** 2
  t1082 = -0.8e1 * t267 * t179 * t283 - 0.40e2 / 0.27e2 * t967 * t876 - 0.6e1 * t942 * t91 - 0.8e1 * t569 * t400 - 0.2e1 * t159 * t936 + 0.88e2 / 0.3e1 * t578 * t286 - 0.2464e4 / 0.27e2 * t271 * t446 + 0.176e3 / 0.3e1 * t575 * t443 - 0.16e2 * t163 * t98 * t277 * t167 + 0.88e2 / 0.3e1 * t572 * t286 - 0.8e1 * t452 * t277 * t283 - 0.64e2 / 0.9e1 * t981 * t163 * t409 - 0.16e2 / 0.3e1 * t270 * t400 * t167 + 0.176e3 / 0.9e1 * t459 * t885 - 0.1958e4 / 0.27e2 * t280 * t888 + 0.5236e4 / 0.81e2 * t166 * t891
  t1102 = -0.72e2 * t479 * t117 * t170 * t192 * t289 + 0.72e2 * t598 * t117 * t170 * t336 * t192 + 0.6e1 * t295 * t117 * t1024 + 0.18e2 * t255 * t117 * t1040 + 0.36e2 * t256 * t108 * t290 + 0.3e1 * t158 * t117 * t1082 + 0.12e2 * t158 * t554 * t170 + 0.18e2 * t158 * t359 * t289 - 0.24e2 * t556 * t175 * t193 + 0.36e2 * t255 * t359 * t256 + 0.12e2 * t295 * t359 * t296
  t1108 = t19 ** 2
  t1111 = t30 ** 2
  t1117 = t41 ** 2
  t1126 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t1127 = f.my_piecewise5(t10, 0, t14, 0, t1126)
  t1131 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t1108 * t1111 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t1117 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t1127)
  t1160 = 0.1e1 / t129 / t36
  t1165 = -0.3e1 / 0.2e1 * t5 * t222 * t361 - 0.3e1 / 0.2e1 * t5 * t226 * t603 - 0.5e1 / 0.9e1 * t5 * t371 * t209 + t5 * t375 * t361 / 0.2e1 - t5 * t379 * t603 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t383 * (-0.72e2 * t94 * t496 * t499 * t170 + 0.72e2 * t93 * t294 * t257 * t296 - 0.12e2 * t260 * t473 * t170 + 0.24e2 * t255 * t171 * t591 + 0.8e1 * t295 * t473 * t192 + 0.72e2 * t255 * t264 * t289 + 0.36e2 * t598 * t290 * t296 - t741 + t751 + t757 + t814 + t830 + t109 * t866 + 0.24e2 * t557 * t207 - t176 * t117 * (t939 + t997) - 0.24e2 * t497 * t207 * t498 - 0.4e1 * t176 * t207 * t472 + 0.12e2 * t158 * t207 * t591 - 0.4e1 * t176 * t554 * t192 - 0.6e1 * t176 * t359 * t336 + 0.24e2 * t95 / t495 / t107 * t117 * t1019 + t1102) - 0.3e1 / 0.8e1 * t5 * t1131 * t54 * t119 - 0.3e1 / 0.2e1 * t5 * t55 * t209 - 0.3e1 / 0.2e1 * t5 * t131 * t209 - 0.9e1 / 0.4e1 * t5 * t135 * t361 + t5 * t218 * t209 - t5 * t53 * t130 * t119 / 0.2e1 + t5 * t128 * t217 * t119 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t215 * t370 * t119 + 0.10e2 / 0.27e2 * t5 * t368 * t1160 * t119
  t1166 = f.my_piecewise3(t1, 0, t1165)
  t1167 = t612 ** 2
  t1170 = t620 ** 2
  t1176 = t627 ** 2
  t1182 = f.my_piecewise5(t14, 0, t10, 0, -t1126)
  t1186 = f.my_piecewise3(t613, 0, 0.40e2 / 0.81e2 / t615 / t1167 * t1170 - 0.16e2 / 0.9e1 * t617 * t620 * t627 + 0.4e1 / 0.3e1 * t624 * t1176 + 0.16e2 / 0.9e1 * t625 * t631 + 0.4e1 / 0.3e1 * t614 * t1182)
  t1208 = f.my_piecewise3(t610, 0, -0.3e1 / 0.8e1 * t5 * t1186 * t54 * t690 - t5 * t635 * t130 * t690 / 0.2e1 + t5 * t699 * t217 * t690 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t706 * t370 * t690 + 0.10e2 / 0.27e2 * t5 * t712 * t1160 * t690)
  d1111 = 0.4e1 * t608 + 0.4e1 * t718 + t6 * (t1166 + t1208)

  res = {'v4rho4': d1111}
  return res
