"""Generated from mgga_x_ft98.mpl."""

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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))
  params_b2_raw = params.b2
  if isinstance(params_b2_raw, (str, bytes, dict)):
    params_b2 = params_b2_raw
  else:
    try:
      params_b2_seq = list(params_b2_raw)
    except TypeError:
      params_b2 = params_b2_raw
    else:
      params_b2_seq = np.asarray(params_b2_seq, dtype=np.float64)
      params_b2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2_seq))

  ft98_f1 = lambda xi: (1 + params_a1 * xi) ** (1 / 2) / (1 + params_b1 * xi) ** (3 / 4)

  ft98_q1 = lambda xi, chi: (xi - chi) ** 2 / (1 + xi) ** 2

  ft98_q2_orig = lambda q3: 1 / (q3 + (1 + q3 ** 2) ** (1 / 2))

  ft98_q2term_smallq = lambda q3: 1 - q3 + 1 / 2 * q3 ** 2 - 1 / 8 * q3 ** 4 + 1 / 16 * q3 ** 6 - 5 / 128 * q3 ** 8

  ft98_q2_cutoff_smallq = DBL_EPSILON ** (1 / 4)

  ft98_q2term_minfty = lambda q3: -2 * q3 - 1 / 2 / q3 + 1 / 8 / q3 ** 3 - 1 / 16 / q3 ** 5

  ft98_q2_cutoff_minfty = -DBL_EPSILON ** (-1 / 4)

  ft98_q3 = lambda xi, chi: xi ** 2 - chi ** 2 - params_b2

  ft98_q20 = lambda q3: f.my_piecewise5(q3 < ft98_q2_cutoff_minfty, ft98_q2term_minfty(q3), jnp.abs(q3) < ft98_q2_cutoff_smallq, ft98_q2term_smallq(q3), ft98_q2_orig(jnp.maximum(q3, ft98_q2_cutoff_minfty)))

  ft98_q2 = lambda xi, chi: ((params_b2 ** 2 + 1) ** (1 / 2) - params_b2) * ft98_q20(ft98_q3(xi, chi))

  ft98_f2 = lambda xi, chi: (1 + params_a2 * ft98_q1(xi, chi)) * (1 + ft98_q2(xi, chi)) / (1 + (2 ** (1 / 3) - 1) * ft98_q2(xi, chi)) ** 3

  ft98_f0 = lambda xi, chi: jnp.sqrt((1 + params_a * ft98_f1(xi) * xi + params_b * ft98_f2(xi, chi) * (xi - chi) ** 2) / (1 + 36 * f.LDA_X_FACTOR ** 2 * params_b * xi))

  ft98_f = lambda x, u, t=None: ft98_f0(x ** 2, u)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ft98_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))
  params_b2_raw = params.b2
  if isinstance(params_b2_raw, (str, bytes, dict)):
    params_b2 = params_b2_raw
  else:
    try:
      params_b2_seq = list(params_b2_raw)
    except TypeError:
      params_b2 = params_b2_raw
    else:
      params_b2_seq = np.asarray(params_b2_seq, dtype=np.float64)
      params_b2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2_seq))

  ft98_f1 = lambda xi: (1 + params_a1 * xi) ** (1 / 2) / (1 + params_b1 * xi) ** (3 / 4)

  ft98_q1 = lambda xi, chi: (xi - chi) ** 2 / (1 + xi) ** 2

  ft98_q2_orig = lambda q3: 1 / (q3 + (1 + q3 ** 2) ** (1 / 2))

  ft98_q2term_smallq = lambda q3: 1 - q3 + 1 / 2 * q3 ** 2 - 1 / 8 * q3 ** 4 + 1 / 16 * q3 ** 6 - 5 / 128 * q3 ** 8

  ft98_q2_cutoff_smallq = DBL_EPSILON ** (1 / 4)

  ft98_q2term_minfty = lambda q3: -2 * q3 - 1 / 2 / q3 + 1 / 8 / q3 ** 3 - 1 / 16 / q3 ** 5

  ft98_q2_cutoff_minfty = -DBL_EPSILON ** (-1 / 4)

  ft98_q3 = lambda xi, chi: xi ** 2 - chi ** 2 - params_b2

  ft98_q20 = lambda q3: f.my_piecewise5(q3 < ft98_q2_cutoff_minfty, ft98_q2term_minfty(q3), jnp.abs(q3) < ft98_q2_cutoff_smallq, ft98_q2term_smallq(q3), ft98_q2_orig(jnp.maximum(q3, ft98_q2_cutoff_minfty)))

  ft98_q2 = lambda xi, chi: ((params_b2 ** 2 + 1) ** (1 / 2) - params_b2) * ft98_q20(ft98_q3(xi, chi))

  ft98_f2 = lambda xi, chi: (1 + params_a2 * ft98_q1(xi, chi)) * (1 + ft98_q2(xi, chi)) / (1 + (2 ** (1 / 3) - 1) * ft98_q2(xi, chi)) ** 3

  ft98_f0 = lambda xi, chi: jnp.sqrt((1 + params_a * ft98_f1(xi) * xi + params_b * ft98_f2(xi, chi) * (xi - chi) ** 2) / (1 + 36 * f.LDA_X_FACTOR ** 2 * params_b * xi))

  ft98_f = lambda x, u, t=None: ft98_f0(x ** 2, u)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ft98_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))
  params_b2_raw = params.b2
  if isinstance(params_b2_raw, (str, bytes, dict)):
    params_b2 = params_b2_raw
  else:
    try:
      params_b2_seq = list(params_b2_raw)
    except TypeError:
      params_b2 = params_b2_raw
    else:
      params_b2_seq = np.asarray(params_b2_seq, dtype=np.float64)
      params_b2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2_seq))

  ft98_f1 = lambda xi: (1 + params_a1 * xi) ** (1 / 2) / (1 + params_b1 * xi) ** (3 / 4)

  ft98_q1 = lambda xi, chi: (xi - chi) ** 2 / (1 + xi) ** 2

  ft98_q2_orig = lambda q3: 1 / (q3 + (1 + q3 ** 2) ** (1 / 2))

  ft98_q2term_smallq = lambda q3: 1 - q3 + 1 / 2 * q3 ** 2 - 1 / 8 * q3 ** 4 + 1 / 16 * q3 ** 6 - 5 / 128 * q3 ** 8

  ft98_q2_cutoff_smallq = DBL_EPSILON ** (1 / 4)

  ft98_q2term_minfty = lambda q3: -2 * q3 - 1 / 2 / q3 + 1 / 8 / q3 ** 3 - 1 / 16 / q3 ** 5

  ft98_q2_cutoff_minfty = -DBL_EPSILON ** (-1 / 4)

  ft98_q3 = lambda xi, chi: xi ** 2 - chi ** 2 - params_b2

  ft98_q20 = lambda q3: f.my_piecewise5(q3 < ft98_q2_cutoff_minfty, ft98_q2term_minfty(q3), jnp.abs(q3) < ft98_q2_cutoff_smallq, ft98_q2term_smallq(q3), ft98_q2_orig(jnp.maximum(q3, ft98_q2_cutoff_minfty)))

  ft98_q2 = lambda xi, chi: ((params_b2 ** 2 + 1) ** (1 / 2) - params_b2) * ft98_q20(ft98_q3(xi, chi))

  ft98_f2 = lambda xi, chi: (1 + params_a2 * ft98_q1(xi, chi)) * (1 + ft98_q2(xi, chi)) / (1 + (2 ** (1 / 3) - 1) * ft98_q2(xi, chi)) ** 3

  ft98_f0 = lambda xi, chi: jnp.sqrt((1 + params_a * ft98_f1(xi) * xi + params_b * ft98_f2(xi, chi) * (xi - chi) ** 2) / (1 + 36 * f.LDA_X_FACTOR ** 2 * params_b * xi))

  ft98_f = lambda x, u, t=None: ft98_f0(x ** 2, u)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ft98_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t29 = r0 ** 2
  t30 = r0 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t33 = 0.1e1 / t31 / t29
  t36 = jnp.sqrt(params.a1 * s0 * t33 + 0.1e1)
  t37 = params.a * t36
  t40 = params.b1 * s0 * t33 + 0.1e1
  t41 = t40 ** (0.1e1 / 0.4e1)
  t42 = t41 ** 2
  t43 = t42 * t41
  t44 = 0.1e1 / t43
  t45 = t44 * s0
  t48 = s0 * t33
  t50 = 0.1e1 / t31 / r0
  t52 = -l0 * t50 + t48
  t53 = t52 ** 2
  t54 = params.a2 * t53
  t55 = 0.1e1 + t48
  t56 = t55 ** 2
  t57 = 0.1e1 / t56
  t60 = params.b * (t54 * t57 + 0.1e1)
  t61 = params.b2 ** 2
  t63 = jnp.sqrt(t61 + 0.1e1)
  t64 = t63 - params.b2
  t65 = s0 ** 2
  t66 = t29 ** 2
  t69 = 0.1e1 / t30 / t66 / r0
  t70 = t65 * t69
  t71 = l0 ** 2
  t72 = t29 * r0
  t74 = 0.1e1 / t30 / t72
  t75 = t71 * t74
  t76 = t70 - t75 - params.b2
  t77 = DBL_EPSILON ** (0.1e1 / 0.4e1)
  t78 = 0.1e1 / t77
  t79 = t76 < -t78
  t82 = 0.2e1 * params.b2
  t85 = t76 ** 2
  t86 = t85 * t76
  t89 = t85 ** 2
  t90 = t89 * t76
  t96 = f.my_piecewise3(0.0e0 < t76, t76, -t76)
  t97 = t96 < t77
  t100 = t89 * t85
  t102 = t89 ** 2
  t105 = -t78 < t76
  t106 = f.my_piecewise3(t105, t76, -t78)
  t107 = t106 ** 2
  t109 = jnp.sqrt(0.1e1 + t107)
  t110 = t106 + t109
  t112 = f.my_piecewise5(t79, -0.2e1 * t70 + 0.2e1 * t75 + t82 - 0.1e1 / t76 / 0.2e1 + 0.1e1 / t86 / 0.8e1 - 0.1e1 / t90 / 0.16e2, t97, 0.1e1 - t70 + t75 + params.b2 + t85 / 0.2e1 - t89 / 0.8e1 + t100 / 0.16e2 - 0.5e1 / 0.128e3 * t102, 0.1e1 / t110)
  t114 = t64 * t112 + 0.1e1
  t115 = 2 ** (0.1e1 / 0.3e1)
  t116 = t115 - 0.1e1
  t117 = t116 * t64
  t119 = t117 * t112 + 0.1e1
  t120 = t119 ** 2
  t122 = 0.1e1 / t120 / t119
  t123 = t114 * t122
  t124 = t123 * t53
  t126 = t37 * t45 * t33 + t60 * t124 + 0.1e1
  t127 = t2 ** 2
  t129 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t130 = t129 ** 2
  t131 = t127 * t130
  t132 = 4 ** (0.1e1 / 0.3e1)
  t133 = t131 * t132
  t138 = 0.1e1 + 0.81e2 / 0.4e1 * t133 * params.b * s0 * t33
  t139 = 0.1e1 / t138
  t141 = jnp.sqrt(t126 * t139)
  t145 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t141)
  t146 = r1 <= f.p.dens_threshold
  t147 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t148 = 0.1e1 + t147
  t149 = t148 <= f.p.zeta_threshold
  t150 = t148 ** (0.1e1 / 0.3e1)
  t152 = f.my_piecewise3(t149, t22, t150 * t148)
  t155 = r1 ** 2
  t156 = r1 ** (0.1e1 / 0.3e1)
  t157 = t156 ** 2
  t159 = 0.1e1 / t157 / t155
  t162 = jnp.sqrt(params.a1 * s2 * t159 + 0.1e1)
  t163 = params.a * t162
  t166 = params.b1 * s2 * t159 + 0.1e1
  t167 = t166 ** (0.1e1 / 0.4e1)
  t168 = t167 ** 2
  t169 = t168 * t167
  t170 = 0.1e1 / t169
  t171 = t170 * s2
  t174 = s2 * t159
  t176 = 0.1e1 / t157 / r1
  t178 = -l1 * t176 + t174
  t179 = t178 ** 2
  t180 = params.a2 * t179
  t181 = 0.1e1 + t174
  t182 = t181 ** 2
  t183 = 0.1e1 / t182
  t186 = params.b * (t180 * t183 + 0.1e1)
  t187 = s2 ** 2
  t188 = t155 ** 2
  t191 = 0.1e1 / t156 / t188 / r1
  t192 = t187 * t191
  t193 = l1 ** 2
  t194 = t155 * r1
  t196 = 0.1e1 / t156 / t194
  t197 = t193 * t196
  t198 = t192 - t197 - params.b2
  t199 = t198 < -t78
  t204 = t198 ** 2
  t205 = t204 * t198
  t208 = t204 ** 2
  t209 = t208 * t198
  t215 = f.my_piecewise3(0.0e0 < t198, t198, -t198)
  t216 = t215 < t77
  t219 = t208 * t204
  t221 = t208 ** 2
  t224 = -t78 < t198
  t225 = f.my_piecewise3(t224, t198, -t78)
  t226 = t225 ** 2
  t228 = jnp.sqrt(0.1e1 + t226)
  t229 = t225 + t228
  t231 = f.my_piecewise5(t199, -0.2e1 * t192 + 0.2e1 * t197 + t82 - 0.1e1 / t198 / 0.2e1 + 0.1e1 / t205 / 0.8e1 - 0.1e1 / t209 / 0.16e2, t216, 0.1e1 - t192 + t197 + params.b2 + t204 / 0.2e1 - t208 / 0.8e1 + t219 / 0.16e2 - 0.5e1 / 0.128e3 * t221, 0.1e1 / t229)
  t233 = t64 * t231 + 0.1e1
  t235 = t117 * t231 + 0.1e1
  t236 = t235 ** 2
  t238 = 0.1e1 / t236 / t235
  t239 = t233 * t238
  t240 = t239 * t179
  t242 = t163 * t171 * t159 + t186 * t240 + 0.1e1
  t247 = 0.1e1 + 0.81e2 / 0.4e1 * t133 * params.b * s2 * t159
  t248 = 0.1e1 / t247
  t250 = jnp.sqrt(t242 * t248)
  t254 = f.my_piecewise3(t146, 0, -0.3e1 / 0.8e1 * t5 * t152 * t26 * t250)
  t255 = t6 ** 2
  t257 = t16 / t255
  t258 = t7 - t257
  t259 = f.my_piecewise5(t10, 0, t14, 0, t258)
  t262 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t259)
  t267 = t26 ** 2
  t268 = 0.1e1 / t267
  t272 = t5 * t25 * t268 * t141 / 0.8e1
  t273 = t5 * t25
  t275 = t26 / t141
  t278 = params.a / t36 * t44
  t282 = t65 / t30 / t66 / t29
  t288 = t37 / t43 / t40
  t293 = 0.1e1 / t31 / t72
  t297 = params.a2 * t52
  t298 = s0 * t293
  t302 = -0.8e1 / 0.3e1 * t298 + 0.5e1 / 0.3e1 * l0 * t33
  t307 = 0.1e1 / t56 / t55
  t315 = t60 * t64
  t319 = t71 / t30 / t66
  t321 = 0.1e1 / t85
  t322 = 0.16e2 / 0.3e1 * t282
  t323 = 0.10e2 / 0.3e1 * t319
  t324 = -t322 + t323
  t327 = 0.1e1 / t89
  t330 = 0.1e1 / t100
  t339 = t89 * t86
  t343 = t110 ** 2
  t344 = 0.1e1 / t343
  t345 = f.my_piecewise3(t105, t324, 0)
  t347 = 0.1e1 / t109 * t106
  t351 = f.my_piecewise5(t79, 0.32e2 / 0.3e1 * t282 - 0.20e2 / 0.3e1 * t319 + t321 * t324 / 0.2e1 - 0.3e1 / 0.8e1 * t327 * t324 + 0.5e1 / 0.16e2 * t330 * t324, t97, t322 - t323 + t76 * t324 - t86 * t324 / 0.2e1 + 0.3e1 / 0.8e1 * t90 * t324 - 0.5e1 / 0.16e2 * t339 * t324, -t344 * (t347 * t345 + t345))
  t355 = t120 ** 2
  t358 = t60 * t114 / t355
  t359 = t53 * t116
  t364 = t60 * t114
  t365 = t122 * t52
  t371 = t138 ** 2
  t373 = t126 / t371
  t375 = t132 * params.b
  t384 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t262 * t26 * t141 - t272 - 0.3e1 / 0.16e2 * t273 * t275 * ((-0.4e1 / 0.3e1 * t278 * t282 * params.a1 + 0.2e1 * t288 * t282 * params.b1 - 0.8e1 / 0.3e1 * t37 * t45 * t293 + params.b * (0.2e1 * t297 * t57 * t302 + 0.16e2 / 0.3e1 * t54 * t307 * s0 * t293) * t124 + t315 * t351 * t122 * t53 - 0.3e1 * t358 * t359 * t64 * t351 + 0.2e1 * t364 * t365 * t302) * t139 + 0.54e2 * t373 * t131 * t375 * t298))
  t386 = f.my_piecewise5(t14, 0, t10, 0, -t258)
  t389 = f.my_piecewise3(t149, 0, 0.4e1 / 0.3e1 * t150 * t386)
  t397 = t5 * t152 * t268 * t250 / 0.8e1
  t399 = f.my_piecewise3(t146, 0, -0.3e1 / 0.8e1 * t5 * t389 * t26 * t250 - t397)
  vrho_0_ = t145 + t254 + t6 * (t384 + t399)
  t402 = -t7 - t257
  t403 = f.my_piecewise5(t10, 0, t14, 0, t402)
  t406 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t403)
  t412 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t406 * t26 * t141 - t272)
  t414 = f.my_piecewise5(t14, 0, t10, 0, -t402)
  t417 = f.my_piecewise3(t149, 0, 0.4e1 / 0.3e1 * t150 * t414)
  t422 = t5 * t152
  t424 = t26 / t250
  t427 = params.a / t162 * t170
  t431 = t187 / t156 / t188 / t155
  t437 = t163 / t169 / t166
  t442 = 0.1e1 / t157 / t194
  t446 = params.a2 * t178
  t447 = s2 * t442
  t451 = -0.8e1 / 0.3e1 * t447 + 0.5e1 / 0.3e1 * l1 * t159
  t456 = 0.1e1 / t182 / t181
  t464 = t186 * t64
  t468 = t193 / t156 / t188
  t470 = 0.1e1 / t204
  t471 = 0.16e2 / 0.3e1 * t431
  t472 = 0.10e2 / 0.3e1 * t468
  t473 = -t471 + t472
  t476 = 0.1e1 / t208
  t479 = 0.1e1 / t219
  t488 = t208 * t205
  t492 = t229 ** 2
  t493 = 0.1e1 / t492
  t494 = f.my_piecewise3(t224, t473, 0)
  t496 = 0.1e1 / t228 * t225
  t500 = f.my_piecewise5(t199, 0.32e2 / 0.3e1 * t431 - 0.20e2 / 0.3e1 * t468 + t470 * t473 / 0.2e1 - 0.3e1 / 0.8e1 * t476 * t473 + 0.5e1 / 0.16e2 * t479 * t473, t216, t471 - t472 + t198 * t473 - t205 * t473 / 0.2e1 + 0.3e1 / 0.8e1 * t209 * t473 - 0.5e1 / 0.16e2 * t488 * t473, -t493 * (t496 * t494 + t494))
  t504 = t236 ** 2
  t507 = t186 * t233 / t504
  t508 = t179 * t116
  t513 = t186 * t233
  t514 = t238 * t178
  t520 = t247 ** 2
  t522 = t242 / t520
  t532 = f.my_piecewise3(t146, 0, -0.3e1 / 0.8e1 * t5 * t417 * t26 * t250 - t397 - 0.3e1 / 0.16e2 * t422 * t424 * ((-0.4e1 / 0.3e1 * t427 * t431 * params.a1 + 0.2e1 * t437 * t431 * params.b1 - 0.8e1 / 0.3e1 * t163 * t171 * t442 + params.b * (0.2e1 * t446 * t183 * t451 + 0.16e2 / 0.3e1 * t180 * t456 * s2 * t442) * t240 + t464 * t500 * t238 * t179 - 0.3e1 * t507 * t508 * t64 * t500 + 0.2e1 * t513 * t514 * t451) * t248 + 0.54e2 * t522 * t131 * t375 * t447))
  vrho_1_ = t145 + t254 + t6 * (t412 + t532)
  t535 = s0 * t69
  t562 = 0.2e1 * t535
  t575 = f.my_piecewise3(t105, t562, 0)
  t579 = f.my_piecewise5(t79, -0.4e1 * t535 + t321 * s0 * t69 - 0.3e1 / 0.4e1 * t327 * s0 * t69 + 0.5e1 / 0.8e1 * t330 * s0 * t69, t97, -t562 + 0.2e1 * t76 * s0 * t69 - t86 * s0 * t69 + 0.3e1 / 0.4e1 * t90 * s0 * t69 - 0.5e1 / 0.8e1 * t339 * s0 * t69, -t344 * (t347 * t575 + t575))
  t593 = t130 * t132
  t602 = f.my_piecewise3(t1, 0, -0.3e1 / 0.16e2 * t273 * t275 * ((t278 * t535 * params.a1 / 0.2e1 - 0.3e1 / 0.4e1 * t288 * t535 * params.b1 + t37 * t44 * t33 + params.b * (0.2e1 * t297 * t57 * t33 - 0.2e1 * t54 * t307 * t33) * t124 + t315 * t579 * t122 * t53 - 0.3e1 * t358 * t359 * t64 * t579 + 0.2e1 * t364 * t365 * t33) * t139 - 0.81e2 / 0.4e1 * t373 * t127 * t593 * params.b * t33))
  vsigma_0_ = t6 * t602
  vsigma_1_ = 0.0e0
  t603 = s2 * t191
  t630 = 0.2e1 * t603
  t643 = f.my_piecewise3(t224, t630, 0)
  t647 = f.my_piecewise5(t199, -0.4e1 * t603 + t470 * s2 * t191 - 0.3e1 / 0.4e1 * t476 * s2 * t191 + 0.5e1 / 0.8e1 * t479 * s2 * t191, t216, -t630 + 0.2e1 * t198 * s2 * t191 - t205 * s2 * t191 + 0.3e1 / 0.4e1 * t209 * s2 * t191 - 0.5e1 / 0.8e1 * t488 * s2 * t191, -t493 * (t496 * t643 + t643))
  t669 = f.my_piecewise3(t146, 0, -0.3e1 / 0.16e2 * t422 * t424 * ((t427 * t603 * params.a1 / 0.2e1 - 0.3e1 / 0.4e1 * t437 * t603 * params.b1 + t163 * t170 * t159 + params.b * (-0.2e1 * t180 * t456 * t159 + 0.2e1 * t446 * t183 * t159) * t240 + t464 * t647 * t238 * t179 - 0.3e1 * t507 * t508 * t64 * t647 + 0.2e1 * t513 * t514 * t159) * t248 - 0.81e2 / 0.4e1 * t522 * t127 * t593 * params.b * t159))
  vsigma_2_ = t6 * t669
  t670 = params.b * params.a2
  t677 = l0 * t74
  t688 = 0.2e1 * t677
  t701 = f.my_piecewise3(t105, -t688, 0)
  t705 = f.my_piecewise5(t79, 0.4e1 * t677 - t321 * l0 * t74 + 0.3e1 / 0.4e1 * t327 * l0 * t74 - 0.5e1 / 0.8e1 * t330 * l0 * t74, t97, t688 - 0.2e1 * t76 * l0 * t74 + t86 * l0 * t74 - 0.3e1 / 0.4e1 * t90 * l0 * t74 + 0.5e1 / 0.8e1 * t339 * l0 * t74, -t344 * (t347 * t701 + t701))
  t721 = f.my_piecewise3(t1, 0, -0.3e1 / 0.16e2 * t273 * t275 * (-0.2e1 * t670 * t53 * t52 * t57 * t50 * t123 + t315 * t705 * t122 * t53 - 0.3e1 * t358 * t359 * t64 * t705 - 0.2e1 * t364 * t365 * t50) * t139)
  vlapl_0_ = t6 * t721
  t728 = l1 * t196
  t739 = 0.2e1 * t728
  t752 = f.my_piecewise3(t224, -t739, 0)
  t756 = f.my_piecewise5(t199, 0.4e1 * t728 - t470 * l1 * t196 + 0.3e1 / 0.4e1 * t476 * l1 * t196 - 0.5e1 / 0.8e1 * t479 * l1 * t196, t216, t739 - 0.2e1 * t198 * l1 * t196 + t205 * l1 * t196 - 0.3e1 / 0.4e1 * t209 * l1 * t196 + 0.5e1 / 0.8e1 * t488 * l1 * t196, -t493 * (t496 * t752 + t752))
  t772 = f.my_piecewise3(t146, 0, -0.3e1 / 0.16e2 * t422 * t424 * (-0.2e1 * t670 * t179 * t178 * t183 * t176 * t239 + t464 * t756 * t238 * t179 - 0.3e1 * t507 * t508 * t64 * t756 - 0.2e1 * t513 * t514 * t176) * t248)
  vlapl_1_ = t6 * t772
  vtau_0_ = 0.0e0
  vtau_1_ = 0.0e0
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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
  params_a2_raw = params.a2
  if isinstance(params_a2_raw, (str, bytes, dict)):
    params_a2 = params_a2_raw
  else:
    try:
      params_a2_seq = list(params_a2_raw)
    except TypeError:
      params_a2 = params_a2_raw
    else:
      params_a2_seq = np.asarray(params_a2_seq, dtype=np.float64)
      params_a2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a2_seq))
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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))
  params_b2_raw = params.b2
  if isinstance(params_b2_raw, (str, bytes, dict)):
    params_b2 = params_b2_raw
  else:
    try:
      params_b2_seq = list(params_b2_raw)
    except TypeError:
      params_b2 = params_b2_raw
    else:
      params_b2_seq = np.asarray(params_b2_seq, dtype=np.float64)
      params_b2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b2_seq))

  ft98_f1 = lambda xi: (1 + params_a1 * xi) ** (1 / 2) / (1 + params_b1 * xi) ** (3 / 4)

  ft98_q1 = lambda xi, chi: (xi - chi) ** 2 / (1 + xi) ** 2

  ft98_q2_orig = lambda q3: 1 / (q3 + (1 + q3 ** 2) ** (1 / 2))

  ft98_q2term_smallq = lambda q3: 1 - q3 + 1 / 2 * q3 ** 2 - 1 / 8 * q3 ** 4 + 1 / 16 * q3 ** 6 - 5 / 128 * q3 ** 8

  ft98_q2_cutoff_smallq = DBL_EPSILON ** (1 / 4)

  ft98_q2term_minfty = lambda q3: -2 * q3 - 1 / 2 / q3 + 1 / 8 / q3 ** 3 - 1 / 16 / q3 ** 5

  ft98_q2_cutoff_minfty = -DBL_EPSILON ** (-1 / 4)

  ft98_q3 = lambda xi, chi: xi ** 2 - chi ** 2 - params_b2

  ft98_q20 = lambda q3: f.my_piecewise5(q3 < ft98_q2_cutoff_minfty, ft98_q2term_minfty(q3), jnp.abs(q3) < ft98_q2_cutoff_smallq, ft98_q2term_smallq(q3), ft98_q2_orig(jnp.maximum(q3, ft98_q2_cutoff_minfty)))

  ft98_q2 = lambda xi, chi: ((params_b2 ** 2 + 1) ** (1 / 2) - params_b2) * ft98_q20(ft98_q3(xi, chi))

  ft98_f2 = lambda xi, chi: (1 + params_a2 * ft98_q1(xi, chi)) * (1 + ft98_q2(xi, chi)) / (1 + (2 ** (1 / 3) - 1) * ft98_q2(xi, chi)) ** 3

  ft98_f0 = lambda xi, chi: jnp.sqrt((1 + params_a * ft98_f1(xi) * xi + params_b * ft98_f2(xi, chi) * (xi - chi) ** 2) / (1 + 36 * f.LDA_X_FACTOR ** 2 * params_b * xi))

  ft98_f = lambda x, u, t=None: ft98_f0(x ** 2, u)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, ft98_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t21 = 2 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = r0 ** 2
  t24 = t18 ** 2
  t26 = 0.1e1 / t24 / t23
  t27 = t22 * t26
  t30 = jnp.sqrt(params.a1 * s0 * t27 + 0.1e1)
  t31 = params.a * t30
  t34 = params.b1 * s0 * t27 + 0.1e1
  t35 = t34 ** (0.1e1 / 0.4e1)
  t36 = t35 ** 2
  t37 = t36 * t35
  t38 = 0.1e1 / t37
  t39 = t31 * t38
  t40 = s0 * t22
  t41 = t40 * t26
  t43 = l0 * t22
  t45 = 0.1e1 / t24 / r0
  t47 = -t43 * t45 + t41
  t48 = t47 ** 2
  t49 = params.a2 * t48
  t50 = 0.1e1 + t41
  t51 = t50 ** 2
  t52 = 0.1e1 / t51
  t55 = params.b * (t49 * t52 + 0.1e1)
  t56 = params.b2 ** 2
  t58 = jnp.sqrt(t56 + 0.1e1)
  t59 = t58 - params.b2
  t60 = s0 ** 2
  t61 = t60 * t21
  t62 = t23 ** 2
  t65 = 0.1e1 / t18 / t62 / r0
  t66 = t61 * t65
  t67 = 0.2e1 * t66
  t68 = l0 ** 2
  t69 = t68 * t21
  t70 = t23 * r0
  t72 = 0.1e1 / t18 / t70
  t73 = t69 * t72
  t74 = 0.2e1 * t73
  t75 = t67 - t74 - params.b2
  t76 = DBL_EPSILON ** (0.1e1 / 0.4e1)
  t77 = 0.1e1 / t76
  t78 = t75 < -t77
  t84 = t75 ** 2
  t85 = t84 * t75
  t88 = t84 ** 2
  t89 = t88 * t75
  t95 = f.my_piecewise3(0.0e0 < t75, t75, -t75)
  t96 = t95 < t76
  t99 = t88 * t84
  t101 = t88 ** 2
  t104 = -t77 < t75
  t105 = f.my_piecewise3(t104, t75, -t77)
  t106 = t105 ** 2
  t108 = jnp.sqrt(0.1e1 + t106)
  t109 = t105 + t108
  t111 = f.my_piecewise5(t78, -0.4e1 * t66 + 0.4e1 * t73 + 0.2e1 * params.b2 - 0.1e1 / t75 / 0.2e1 + 0.1e1 / t85 / 0.8e1 - 0.1e1 / t89 / 0.16e2, t96, 0.1e1 - t67 + t74 + params.b2 + t84 / 0.2e1 - t88 / 0.8e1 + t99 / 0.16e2 - 0.5e1 / 0.128e3 * t101, 0.1e1 / t109)
  t113 = t59 * t111 + 0.1e1
  t114 = t21 - 0.1e1
  t117 = t114 * t59 * t111 + 0.1e1
  t118 = t117 ** 2
  t120 = 0.1e1 / t118 / t117
  t121 = t113 * t120
  t122 = t121 * t48
  t124 = t55 * t122 + t39 * t41 + 0.1e1
  t125 = t3 ** 2
  t127 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t128 = t127 ** 2
  t129 = t125 * t128
  t130 = 4 ** (0.1e1 / 0.3e1)
  t136 = 0.1e1 + 0.81e2 / 0.4e1 * t129 * t130 * params.b * s0 * t27
  t137 = 0.1e1 / t136
  t139 = jnp.sqrt(t124 * t137)
  t143 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t139)
  t149 = t6 * t17
  t151 = t18 / t139
  t154 = params.a / t30 * t38
  t157 = 0.1e1 / t18 / t62 / t23
  t164 = t31 / t37 / t34
  t171 = t40 / t24 / t70
  t174 = params.a2 * t47
  t178 = -0.8e1 / 0.3e1 * t171 + 0.5e1 / 0.3e1 * t43 * t26
  t183 = 0.1e1 / t51 / t50
  t190 = t55 * t59
  t191 = t61 * t157
  t195 = t69 / t18 / t62
  t197 = 0.1e1 / t84
  t198 = 0.32e2 / 0.3e1 * t191
  t199 = 0.20e2 / 0.3e1 * t195
  t200 = -t198 + t199
  t203 = 0.1e1 / t88
  t206 = 0.1e1 / t99
  t215 = t88 * t85
  t219 = t109 ** 2
  t220 = 0.1e1 / t219
  t221 = f.my_piecewise3(t104, t200, 0)
  t223 = 0.1e1 / t108 * t105
  t227 = f.my_piecewise5(t78, 0.64e2 / 0.3e1 * t191 - 0.40e2 / 0.3e1 * t195 + t197 * t200 / 0.2e1 - 0.3e1 / 0.8e1 * t203 * t200 + 0.5e1 / 0.16e2 * t206 * t200, t96, t198 - t199 + t75 * t200 - t85 * t200 / 0.2e1 + 0.3e1 / 0.8e1 * t89 * t200 - 0.5e1 / 0.16e2 * t215 * t200, -t220 * (t223 * t221 + t221))
  t231 = t118 ** 2
  t234 = t55 * t113 / t231
  t235 = t48 * t114
  t240 = t55 * t113
  t241 = t120 * t47
  t247 = t136 ** 2
  t250 = t124 / t247 * t129
  t251 = t130 * params.b
  t260 = f.my_piecewise3(t2, 0, -t6 * t17 / t24 * t139 / 0.8e1 - 0.3e1 / 0.16e2 * t149 * t151 * ((-0.8e1 / 0.3e1 * t154 * t61 * t157 * params.a1 + 0.4e1 * t164 * t61 * t157 * params.b1 - 0.8e1 / 0.3e1 * t39 * t171 + params.b * (0.2e1 * t174 * t52 * t178 + 0.16e2 / 0.3e1 * t49 * t183 * t171) * t122 + t190 * t227 * t120 * t48 - 0.3e1 * t234 * t235 * t59 * t227 + 0.2e1 * t240 * t241 * t178) * t137 + 0.54e2 * t250 * t251 * t171))
  vrho_0_ = 0.2e1 * r0 * t260 + 0.2e1 * t143
  t263 = s0 * t21
  t284 = t263 * t65
  t287 = t21 * t65
  t297 = 0.4e1 * t284
  t311 = f.my_piecewise3(t104, t297, 0)
  t315 = f.my_piecewise5(t78, -0.8e1 * t284 + 0.2e1 * t197 * s0 * t287 - 0.3e1 / 0.2e1 * t203 * s0 * t287 + 0.5e1 / 0.4e1 * t206 * s0 * t287, t96, -t297 + 0.4e1 * t75 * s0 * t287 - 0.2e1 * t85 * s0 * t287 + 0.3e1 / 0.2e1 * t89 * s0 * t287 - 0.5e1 / 0.4e1 * t215 * s0 * t287, -t220 * (t223 * t311 + t311))
  t335 = f.my_piecewise3(t2, 0, -0.3e1 / 0.16e2 * t149 * t151 * ((t154 * t263 * t65 * params.a1 - 0.3e1 / 0.2e1 * t164 * t263 * t65 * params.b1 + t31 * t38 * t22 * t26 + params.b * (0.2e1 * t174 * t52 * t22 * t26 - 0.2e1 * t49 * t183 * t22 * t26) * t122 + t190 * t315 * t120 * t48 - 0.3e1 * t234 * t235 * t59 * t315 + 0.2e1 * t240 * t241 * t27) * t137 - 0.81e2 / 0.4e1 * t250 * t251 * t27))
  vsigma_0_ = 0.2e1 * r0 * t335
  t341 = t22 * t45
  t346 = l0 * t21 * t72
  t349 = t21 * t72
  t359 = 0.4e1 * t346
  t373 = f.my_piecewise3(t104, -t359, 0)
  t377 = f.my_piecewise5(t78, 0.8e1 * t346 - 0.2e1 * t197 * l0 * t349 + 0.3e1 / 0.2e1 * t203 * l0 * t349 - 0.5e1 / 0.4e1 * t206 * l0 * t349, t96, t359 - 0.4e1 * t75 * l0 * t349 + 0.2e1 * t85 * l0 * t349 - 0.3e1 / 0.2e1 * t89 * l0 * t349 + 0.5e1 / 0.4e1 * t215 * l0 * t349, -t220 * (t223 * t373 + t373))
  t393 = f.my_piecewise3(t2, 0, -0.3e1 / 0.16e2 * t149 * t151 * (-0.2e1 * params.b * params.a2 * t48 * t47 * t52 * t341 * t121 + t190 * t377 * t120 * t48 - 0.3e1 * t234 * t235 * t59 * t377 - 0.2e1 * t240 * t241 * t341) * t137)
  vlapl_0_ = 0.2e1 * r0 * t393
  vtau_0_ = 0.0e0
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
  t20 = 0.1e1 / t19
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = r0 ** 2
  t27 = 0.1e1 / t19 / t25
  t28 = t24 * t27
  t30 = params.a1 * s0 * t28 + 0.1e1
  t31 = jnp.sqrt(t30)
  t32 = params.a * t31
  t35 = params.b1 * s0 * t28 + 0.1e1
  t36 = t35 ** (0.1e1 / 0.4e1)
  t37 = t36 ** 2
  t38 = t37 * t36
  t39 = 0.1e1 / t38
  t40 = t32 * t39
  t41 = s0 * t24
  t42 = t41 * t27
  t44 = l0 * t24
  t46 = 0.1e1 / t19 / r0
  t48 = -t44 * t46 + t42
  t49 = t48 ** 2
  t50 = params.a2 * t49
  t51 = 0.1e1 + t42
  t52 = t51 ** 2
  t53 = 0.1e1 / t52
  t56 = params.b * (t50 * t53 + 0.1e1)
  t57 = params.b2 ** 2
  t59 = jnp.sqrt(t57 + 0.1e1)
  t60 = t59 - params.b2
  t61 = s0 ** 2
  t62 = t61 * t23
  t63 = t25 ** 2
  t66 = 0.1e1 / t18 / t63 / r0
  t67 = t62 * t66
  t68 = 0.2e1 * t67
  t69 = l0 ** 2
  t70 = t69 * t23
  t71 = t25 * r0
  t74 = t70 / t18 / t71
  t75 = 0.2e1 * t74
  t76 = t68 - t75 - params.b2
  t77 = DBL_EPSILON ** (0.1e1 / 0.4e1)
  t78 = 0.1e1 / t77
  t79 = t76 < -t78
  t85 = t76 ** 2
  t86 = t85 * t76
  t87 = 0.1e1 / t86
  t89 = t85 ** 2
  t90 = t89 * t76
  t91 = 0.1e1 / t90
  t96 = f.my_piecewise3(0.0e0 < t76, t76, -t76)
  t97 = t96 < t77
  t100 = t89 * t85
  t102 = t89 ** 2
  t105 = -t78 < t76
  t106 = f.my_piecewise3(t105, t76, -t78)
  t107 = t106 ** 2
  t108 = 0.1e1 + t107
  t109 = jnp.sqrt(t108)
  t110 = t106 + t109
  t112 = f.my_piecewise5(t79, -0.4e1 * t67 + 0.4e1 * t74 + 0.2e1 * params.b2 - 0.1e1 / t76 / 0.2e1 + t87 / 0.8e1 - t91 / 0.16e2, t97, 0.1e1 - t68 + t75 + params.b2 + t85 / 0.2e1 - t89 / 0.8e1 + t100 / 0.16e2 - 0.5e1 / 0.128e3 * t102, 0.1e1 / t110)
  t114 = t60 * t112 + 0.1e1
  t115 = t23 - 0.1e1
  t118 = t115 * t60 * t112 + 0.1e1
  t119 = t118 ** 2
  t121 = 0.1e1 / t119 / t118
  t122 = t114 * t121
  t123 = t122 * t49
  t125 = t56 * t123 + t40 * t42 + 0.1e1
  t126 = t3 ** 2
  t127 = 0.1e1 / jnp.pi
  t128 = t127 ** (0.1e1 / 0.3e1)
  t129 = t128 ** 2
  t130 = t126 * t129
  t131 = 4 ** (0.1e1 / 0.3e1)
  t137 = 0.1e1 + 0.81e2 / 0.4e1 * t130 * t131 * params.b * s0 * t28
  t138 = 0.1e1 / t137
  t139 = t125 * t138
  t140 = jnp.sqrt(t139)
  t144 = t6 * t17
  t145 = 0.1e1 / t140
  t146 = t18 * t145
  t148 = params.a / t31
  t149 = t148 * t39
  t152 = 0.1e1 / t18 / t63 / t25
  t158 = 0.1e1 / t38 / t35
  t159 = t32 * t158
  t165 = 0.1e1 / t19 / t71
  t166 = t41 * t165
  t169 = params.a2 * t48
  t173 = -0.8e1 / 0.3e1 * t166 + 0.5e1 / 0.3e1 * t44 * t27
  t178 = 0.1e1 / t52 / t51
  t179 = t50 * t178
  t183 = params.b * (0.2e1 * t169 * t53 * t173 + 0.16e2 / 0.3e1 * t179 * t166)
  t185 = t56 * t60
  t186 = t62 * t152
  t190 = t70 / t18 / t63
  t192 = 0.1e1 / t85
  t193 = 0.32e2 / 0.3e1 * t186
  t194 = 0.20e2 / 0.3e1 * t190
  t195 = -t193 + t194
  t198 = 0.1e1 / t89
  t201 = 0.1e1 / t100
  t210 = t89 * t86
  t214 = t110 ** 2
  t215 = 0.1e1 / t214
  t216 = f.my_piecewise3(t105, t195, 0)
  t217 = 0.1e1 / t109
  t218 = t217 * t106
  t220 = t218 * t216 + t216
  t222 = f.my_piecewise5(t79, 0.64e2 / 0.3e1 * t186 - 0.40e2 / 0.3e1 * t190 + t192 * t195 / 0.2e1 - 0.3e1 / 0.8e1 * t198 * t195 + 0.5e1 / 0.16e2 * t201 * t195, t97, t193 - t194 + t76 * t195 - t86 * t195 / 0.2e1 + 0.3e1 / 0.8e1 * t90 * t195 - 0.5e1 / 0.16e2 * t210 * t195, -t215 * t220)
  t223 = t222 * t121
  t224 = t223 * t49
  t226 = t119 ** 2
  t227 = 0.1e1 / t226
  t228 = t114 * t227
  t229 = t56 * t228
  t230 = t49 * t115
  t231 = t60 * t222
  t232 = t230 * t231
  t235 = t56 * t114
  t236 = t121 * t48
  t237 = t236 * t173
  t240 = -0.8e1 / 0.3e1 * t149 * t62 * t152 * params.a1 + 0.4e1 * t159 * t62 * t152 * params.b1 - 0.8e1 / 0.3e1 * t40 * t166 + t183 * t123 + t185 * t224 - 0.3e1 * t229 * t232 + 0.2e1 * t235 * t237
  t242 = t137 ** 2
  t243 = 0.1e1 / t242
  t245 = t125 * t243 * t130
  t246 = t131 * params.b
  t247 = t246 * t166
  t250 = t240 * t138 + 0.54e2 * t245 * t247
  t255 = f.my_piecewise3(t2, 0, -t6 * t17 * t20 * t140 / 0.8e1 - 0.3e1 / 0.16e2 * t144 * t146 * t250)
  t268 = t250 ** 2
  t274 = 0.1e1 / t18 / t63 / t71
  t286 = t62 * t274
  t288 = t70 * t66
  t290 = t195 ** 2
  t292 = 0.608e3 / 0.9e1 * t286
  t293 = 0.260e3 / 0.9e1 * t288
  t294 = t292 - t293
  t323 = t220 ** 2
  t326 = f.my_piecewise3(t105, t294, 0)
  t330 = t216 ** 2
  t337 = f.my_piecewise5(t79, -0.1216e4 / 0.9e1 * t286 + 0.520e3 / 0.9e1 * t288 - t87 * t290 + t192 * t294 / 0.2e1 + 0.3e1 / 0.2e1 * t91 * t290 - 0.3e1 / 0.8e1 * t198 * t294 - 0.15e2 / 0.8e1 / t210 * t290 + 0.5e1 / 0.16e2 * t201 * t294, t97, -t292 + t293 + t290 + t76 * t294 - 0.3e1 / 0.2e1 * t85 * t290 - t86 * t294 / 0.2e1 + 0.15e2 / 0.8e1 * t89 * t290 + 0.3e1 / 0.8e1 * t90 * t294 - 0.35e2 / 0.16e2 * t100 * t290 - 0.5e1 / 0.16e2 * t210 * t294, 0.2e1 / t214 / t110 * t323 - t215 * (t326 - 0.1e1 / t109 / t108 * t107 * t330 + t217 * t330 + t218 * t326))
  t342 = t173 ** 2
  t354 = t41 / t19 / t63
  t358 = 0.88e2 / 0.9e1 * t354 - 0.40e2 / 0.9e1 * t44 * t165
  t362 = t52 ** 2
  t374 = t63 ** 2
  t377 = t61 * s0 / t374 / t25
  t407 = params.a1 ** 2
  t411 = t35 ** 2
  t415 = params.b1 ** 2
  t419 = t60 ** 2
  t421 = t222 ** 2
  t435 = t115 ** 2
  t441 = 0.24e2 * t149 * t62 * t274 * params.a1 - 0.36e2 * t159 * t62 * t274 * params.b1 - 0.6e1 * t183 * t228 * t232 - 0.3e1 * t229 * t230 * t60 * t337 + params.b * (0.2e1 * params.a2 * t342 * t53 + 0.64e2 / 0.3e1 * t169 * t178 * t173 * s0 * t24 * t165 + 0.2e1 * t169 * t53 * t358 + 0.256e3 / 0.3e1 * t50 / t362 * t286 - 0.176e3 / 0.9e1 * t179 * t354) * t123 - 0.64e2 / 0.3e1 * t148 * t158 * t377 * params.a1 * params.b1 + 0.88e2 / 0.9e1 * t40 * t354 + 0.4e1 * t185 * t223 * t48 * t173 + 0.4e1 * t183 * t114 * t237 + 0.2e1 * t183 * t60 * t224 + t185 * t337 * t121 * t49 + 0.2e1 * t56 * t122 * t342 + 0.2e1 * t235 * t236 * t358 - 0.64e2 / 0.9e1 * params.a / t31 / t30 * t39 * t377 * t407 + 0.112e3 / 0.3e1 * t32 / t38 / t411 * t377 * t415 - 0.6e1 * t56 * t419 * t421 * t227 * t230 - 0.12e2 * t229 * t48 * t115 * t231 * t173 + 0.12e2 * t56 * t114 / t226 / t118 * t49 * t435 * t419 * t421
  t453 = t131 ** 2
  t454 = params.b ** 2
  t467 = f.my_piecewise3(t2, 0, t6 * t17 * t46 * t140 / 0.12e2 - t144 * t20 * t145 * t250 / 0.8e1 + 0.3e1 / 0.32e2 * t144 * t18 / t140 / t139 * t268 - 0.3e1 / 0.16e2 * t144 * t146 * (t441 * t138 + 0.108e3 * t240 * t243 * t130 * t247 + 0.34992e5 * t125 / t242 / t137 * t3 * t128 * t127 * t453 * t454 * t286 - 0.198e3 * t245 * t246 * t354))
  v2rho2_0_ = 0.2e1 * r0 * t467 + 0.4e1 * t255
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
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = r0 ** 2
  t28 = 0.1e1 / t19 / t26
  t29 = t25 * t28
  t31 = params.a1 * s0 * t29 + 0.1e1
  t32 = jnp.sqrt(t31)
  t33 = params.a * t32
  t36 = params.b1 * s0 * t29 + 0.1e1
  t37 = t36 ** (0.1e1 / 0.4e1)
  t38 = t37 ** 2
  t39 = t38 * t37
  t40 = 0.1e1 / t39
  t41 = t33 * t40
  t42 = s0 * t25
  t43 = t42 * t28
  t45 = l0 * t25
  t47 = -t45 * t21 + t43
  t48 = t47 ** 2
  t49 = params.a2 * t48
  t50 = 0.1e1 + t43
  t51 = t50 ** 2
  t52 = 0.1e1 / t51
  t55 = params.b * (t49 * t52 + 0.1e1)
  t56 = params.b2 ** 2
  t58 = jnp.sqrt(t56 + 0.1e1)
  t59 = t58 - params.b2
  t60 = s0 ** 2
  t61 = t60 * t24
  t62 = t26 ** 2
  t63 = t62 * r0
  t65 = 0.1e1 / t18 / t63
  t66 = t61 * t65
  t67 = 0.2e1 * t66
  t68 = l0 ** 2
  t69 = t68 * t24
  t70 = t26 * r0
  t73 = t69 / t18 / t70
  t74 = 0.2e1 * t73
  t75 = t67 - t74 - params.b2
  t76 = DBL_EPSILON ** (0.1e1 / 0.4e1)
  t77 = 0.1e1 / t76
  t78 = t75 < -t77
  t84 = t75 ** 2
  t85 = t84 * t75
  t86 = 0.1e1 / t85
  t88 = t84 ** 2
  t89 = t88 * t75
  t90 = 0.1e1 / t89
  t95 = f.my_piecewise3(0.0e0 < t75, t75, -t75)
  t96 = t95 < t76
  t99 = t88 * t84
  t101 = t88 ** 2
  t104 = -t77 < t75
  t105 = f.my_piecewise3(t104, t75, -t77)
  t106 = t105 ** 2
  t107 = 0.1e1 + t106
  t108 = jnp.sqrt(t107)
  t109 = t105 + t108
  t111 = f.my_piecewise5(t78, -0.4e1 * t66 + 0.4e1 * t73 + 0.2e1 * params.b2 - 0.1e1 / t75 / 0.2e1 + t86 / 0.8e1 - t90 / 0.16e2, t96, 0.1e1 - t67 + t74 + params.b2 + t84 / 0.2e1 - t88 / 0.8e1 + t99 / 0.16e2 - 0.5e1 / 0.128e3 * t101, 0.1e1 / t109)
  t113 = t59 * t111 + 0.1e1
  t114 = t24 - 0.1e1
  t115 = t114 * t59
  t117 = t115 * t111 + 0.1e1
  t118 = t117 ** 2
  t120 = 0.1e1 / t118 / t117
  t121 = t113 * t120
  t122 = t121 * t48
  t124 = t55 * t122 + t41 * t43 + 0.1e1
  t125 = t3 ** 2
  t126 = 0.1e1 / jnp.pi
  t127 = t126 ** (0.1e1 / 0.3e1)
  t128 = t127 ** 2
  t129 = t125 * t128
  t130 = 4 ** (0.1e1 / 0.3e1)
  t136 = 0.1e1 + 0.81e2 / 0.4e1 * t129 * t130 * params.b * s0 * t29
  t137 = 0.1e1 / t136
  t138 = t124 * t137
  t139 = jnp.sqrt(t138)
  t143 = t6 * t17
  t144 = 0.1e1 / t19
  t145 = 0.1e1 / t139
  t146 = t144 * t145
  t148 = params.a / t32
  t149 = t148 * t40
  t152 = 0.1e1 / t18 / t62 / t26
  t158 = 0.1e1 / t39 / t36
  t159 = t33 * t158
  t165 = 0.1e1 / t19 / t70
  t166 = t42 * t165
  t169 = params.a2 * t47
  t173 = -0.8e1 / 0.3e1 * t166 + 0.5e1 / 0.3e1 * t45 * t28
  t178 = 0.1e1 / t51 / t50
  t179 = t49 * t178
  t183 = params.b * (0.2e1 * t169 * t52 * t173 + 0.16e2 / 0.3e1 * t179 * t166)
  t185 = t55 * t59
  t186 = t61 * t152
  t190 = t69 / t18 / t62
  t192 = 0.1e1 / t84
  t193 = 0.32e2 / 0.3e1 * t186
  t194 = 0.20e2 / 0.3e1 * t190
  t195 = -t193 + t194
  t198 = 0.1e1 / t88
  t201 = 0.1e1 / t99
  t210 = t88 * t85
  t214 = t109 ** 2
  t215 = 0.1e1 / t214
  t216 = f.my_piecewise3(t104, t195, 0)
  t217 = 0.1e1 / t108
  t218 = t217 * t105
  t220 = t218 * t216 + t216
  t222 = f.my_piecewise5(t78, 0.64e2 / 0.3e1 * t186 - 0.40e2 / 0.3e1 * t190 + t192 * t195 / 0.2e1 - 0.3e1 / 0.8e1 * t198 * t195 + 0.5e1 / 0.16e2 * t201 * t195, t96, t193 - t194 + t75 * t195 - t85 * t195 / 0.2e1 + 0.3e1 / 0.8e1 * t89 * t195 - 0.5e1 / 0.16e2 * t210 * t195, -t215 * t220)
  t223 = t222 * t120
  t224 = t223 * t48
  t226 = t118 ** 2
  t227 = 0.1e1 / t226
  t228 = t113 * t227
  t229 = t55 * t228
  t230 = t48 * t114
  t231 = t59 * t222
  t232 = t230 * t231
  t235 = t55 * t113
  t236 = t120 * t47
  t237 = t236 * t173
  t240 = -0.8e1 / 0.3e1 * t149 * t61 * t152 * params.a1 + 0.4e1 * t159 * t61 * t152 * params.b1 - 0.8e1 / 0.3e1 * t41 * t166 + t183 * t122 + t185 * t224 - 0.3e1 * t229 * t232 + 0.2e1 * t235 * t237
  t242 = t136 ** 2
  t243 = 0.1e1 / t242
  t245 = t124 * t243 * t129
  t246 = t130 * params.b
  t247 = t246 * t166
  t250 = t240 * t137 + 0.54e2 * t245 * t247
  t255 = 0.1e1 / t139 / t138
  t256 = t18 * t255
  t257 = t250 ** 2
  t261 = t18 * t145
  t264 = 0.1e1 / t18 / t62 / t70
  t269 = t183 * t228
  t272 = t61 * t264
  t274 = t69 * t65
  t276 = t195 ** 2
  t278 = 0.608e3 / 0.9e1 * t272
  t279 = 0.260e3 / 0.9e1 * t274
  t280 = t278 - t279
  t287 = 0.1e1 / t210
  t308 = 0.1e1 / t214 / t109
  t309 = t220 ** 2
  t312 = f.my_piecewise3(t104, t280, 0)
  t314 = 0.1e1 / t108 / t107
  t315 = t314 * t106
  t316 = t216 ** 2
  t320 = t217 * t316 + t218 * t312 - t315 * t316 + t312
  t323 = f.my_piecewise5(t78, -0.1216e4 / 0.9e1 * t272 + 0.520e3 / 0.9e1 * t274 - t86 * t276 + t192 * t280 / 0.2e1 + 0.3e1 / 0.2e1 * t90 * t276 - 0.3e1 / 0.8e1 * t198 * t280 - 0.15e2 / 0.8e1 * t287 * t276 + 0.5e1 / 0.16e2 * t201 * t280, t96, -t278 + t279 + t276 + t75 * t280 - 0.3e1 / 0.2e1 * t84 * t276 - t85 * t280 / 0.2e1 + 0.15e2 / 0.8e1 * t88 * t276 + 0.3e1 / 0.8e1 * t89 * t280 - 0.35e2 / 0.16e2 * t99 * t276 - 0.5e1 / 0.16e2 * t210 * t280, -t215 * t320 + 0.2e1 * t308 * t309)
  t324 = t59 * t323
  t325 = t230 * t324
  t332 = t173 ** 2
  t333 = params.a2 * t332
  t336 = t169 * t178
  t337 = t173 * s0
  t338 = t25 * t165
  t343 = 0.1e1 / t19 / t62
  t344 = t42 * t343
  t348 = 0.88e2 / 0.9e1 * t344 - 0.40e2 / 0.9e1 * t45 * t165
  t349 = t52 * t348
  t352 = t51 ** 2
  t353 = 0.1e1 / t352
  t354 = t49 * t353
  t360 = params.b * (0.2e1 * t333 * t52 + 0.64e2 / 0.3e1 * t336 * t337 * t338 + 0.2e1 * t169 * t349 + 0.256e3 / 0.3e1 * t354 * t272 - 0.176e3 / 0.9e1 * t179 * t344)
  t362 = t148 * t158
  t363 = t60 * s0
  t364 = t62 ** 2
  t367 = t363 / t364 / t26
  t368 = params.a1 * params.b1
  t374 = t47 * t173
  t375 = t223 * t374
  t378 = t183 * t113
  t381 = t183 * t59
  t384 = t323 * t120
  t385 = t384 * t48
  t387 = t121 * t332
  t390 = t236 * t348
  t395 = params.a / t32 / t31
  t396 = t395 * t40
  t397 = params.a1 ** 2
  t401 = t36 ** 2
  t403 = 0.1e1 / t39 / t401
  t404 = t33 * t403
  t405 = params.b1 ** 2
  t409 = t59 ** 2
  t411 = t222 ** 2
  t413 = t411 * t227 * t230
  t416 = t47 * t114
  t418 = t416 * t231 * t173
  t422 = 0.1e1 / t226 / t117
  t423 = t113 * t422
  t424 = t55 * t423
  t425 = t114 ** 2
  t426 = t48 * t425
  t427 = t409 * t411
  t428 = t426 * t427
  t431 = -0.36e2 * t159 * t61 * t264 * params.b1 - 0.6e1 * t269 * t232 - 0.3e1 * t229 * t325 + 0.24e2 * t149 * t61 * t264 * params.a1 + t360 * t122 - 0.64e2 / 0.3e1 * t362 * t367 * t368 + 0.88e2 / 0.9e1 * t41 * t344 + 0.4e1 * t185 * t375 + 0.4e1 * t378 * t237 + 0.2e1 * t381 * t224 + t185 * t385 + 0.2e1 * t55 * t387 + 0.2e1 * t235 * t390 - 0.64e2 / 0.9e1 * t396 * t367 * t397 + 0.112e3 / 0.3e1 * t404 * t367 * t405 - 0.6e1 * t55 * t409 * t413 - 0.12e2 * t229 * t418 + 0.12e2 * t424 * t428
  t434 = t240 * t243 * t129
  t438 = 0.1e1 / t242 / t136
  t441 = t3 * t127 * t126
  t442 = t124 * t438 * t441
  t443 = t130 ** 2
  t444 = params.b ** 2
  t445 = t443 * t444
  t446 = t445 * t272
  t449 = t246 * t344
  t452 = t431 * t137 - 0.198e3 * t245 * t449 + 0.108e3 * t434 * t247 + 0.34992e5 * t442 * t446
  t457 = f.my_piecewise3(t2, 0, t6 * t17 * t21 * t139 / 0.12e2 - t143 * t146 * t250 / 0.8e1 + 0.3e1 / 0.32e2 * t143 * t256 * t257 - 0.3e1 / 0.16e2 * t143 * t261 * t452)
  t474 = t124 ** 2
  t488 = 0.1e1 / t18 / t364
  t489 = t61 * t488
  t491 = t69 * t152
  t493 = t276 * t195
  t499 = 0.13376e5 / 0.27e2 * t489
  t500 = 0.4160e4 / 0.27e2 * t491
  t501 = -t499 + t500
  t519 = 0.26752e5 / 0.27e2 * t489 - 0.8320e4 / 0.27e2 * t491 + 0.3e1 * t198 * t493 - 0.3e1 * t86 * t195 * t280 + t192 * t501 / 0.2e1 - 0.15e2 / 0.2e1 * t201 * t493 + 0.9e1 / 0.2e1 * t90 * t195 * t280 - 0.3e1 / 0.8e1 * t198 * t501 + 0.105e3 / 0.8e1 / t101 * t493 - 0.45e2 / 0.8e1 * t287 * t195 * t280 + 0.5e1 / 0.16e2 * t201 * t501
  t544 = t499 - t500 + 0.3e1 * t195 * t280 + t75 * t501 - 0.3e1 * t75 * t493 - 0.9e1 / 0.2e1 * t84 * t195 * t280 - t85 * t501 / 0.2e1 + 0.15e2 / 0.2e1 * t85 * t493 + 0.45e2 / 0.8e1 * t88 * t195 * t280 + 0.3e1 / 0.8e1 * t89 * t501 - 0.105e3 / 0.8e1 * t89 * t493 - 0.105e3 / 0.16e2 * t99 * t195 * t280 - 0.5e1 / 0.16e2 * t210 * t501
  t545 = t214 ** 2
  t553 = f.my_piecewise3(t104, t501, 0)
  t554 = t107 ** 2
  t559 = t316 * t216
  t575 = f.my_piecewise5(t78, t519, t96, t544, -0.6e1 / t545 * t309 * t220 + 0.6e1 * t308 * t220 * t320 - t215 * (t553 + 0.3e1 / t108 / t554 * t106 * t105 * t559 - 0.3e1 * t314 * t105 * t559 - 0.3e1 * t315 * t216 * t312 + 0.3e1 * t217 * t216 * t312 + t218 * t553))
  t585 = t42 / t19 / t63
  t589 = -0.1232e4 / 0.27e2 * t585 + 0.440e3 / 0.27e2 * t45 * t343
  t594 = 0.1e1 / t364 / t70
  t595 = t363 * t594
  t633 = t60 ** 2
  t638 = 0.1e1 / t19 / t364 / t63
  t658 = t185 * t575 * t120 * t48 + 0.6e1 * t235 * t120 * t173 * t348 + 0.2e1 * t235 * t236 * t589 - 0.2128e4 / 0.3e1 * t404 * t595 * t405 + 0.1216e4 / 0.9e1 * t396 * t595 * t397 + 0.6e1 * t360 * t113 * t237 + 0.3e1 * t360 * t59 * t224 + 0.6e1 * t378 * t390 + 0.6e1 * t185 * t223 * t332 - 0.1232e4 / 0.27e2 * t41 * t585 + 0.3e1 * t381 * t385 - 0.18e2 * t55 * t409 * t222 * t227 * t48 * t114 * t323 - 0.9e1 * t360 * t228 * t232 - 0.9e1 * t269 * t325 - 0.3e1 * t229 * t230 * t59 * t575 - 0.128e3 / 0.3e1 * t395 * t158 * t633 * t638 * t397 * params.b1 * t25 - 0.448e3 / 0.3e1 * t148 * t403 * t633 * t638 * params.a1 * t405 * t25 - 0.18e2 * t229 * t332 * t114 * t231 + 0.36e2 * t183 * t423 * t428
  t665 = t409 * t59
  t666 = t411 * t222
  t719 = t47 * t348
  t723 = t31 ** 2
  t728 = t633 * t638
  t783 = -0.60e2 * t55 * t113 / t226 / t118 * t48 * t425 * t114 * t665 * t666 - 0.36e2 * t55 * t427 * t227 * t47 * t173 * t114 + params.b * (0.6e1 * params.a2 * t173 * t349 + 0.32e2 * t333 * t178 * t166 + 0.512e3 * t169 * t353 * t173 * t60 * t24 * t264 + 0.32e2 * t336 * t348 * s0 * t338 - 0.352e3 / 0.3e1 * t336 * t337 * t25 * t343 + 0.2e1 * t169 * t52 * t589 + 0.16384e5 / 0.9e1 * t49 / t352 / t50 * t363 * t594 - 0.2816e4 / 0.3e1 * t354 * t489 + 0.2464e4 / 0.27e2 * t179 * t585) * t122 + 0.6e1 * t183 * t387 - 0.5456e4 / 0.27e2 * t149 * t61 * t488 * params.a1 + 0.6e1 * t185 * t223 * t719 - 0.256e3 / 0.9e1 * params.a / t32 / t723 * t40 * t728 * t397 * params.a1 * t25 + 0.2464e4 / 0.9e1 * t33 / t39 / t401 / t36 * t728 * t405 * params.b1 * t25 + 0.12e2 * t381 * t375 + 0.6e1 * t185 * t384 * t374 + 0.1216e4 / 0.3e1 * t362 * t595 * t368 + 0.36e2 * t55 * t665 * t666 * t422 * t426 - 0.18e2 * t183 * t409 * t413 + 0.2728e4 / 0.9e1 * t159 * t61 * t488 * params.b1 - 0.36e2 * t269 * t418 - 0.18e2 * t229 * t416 * t324 * t173 - 0.18e2 * t229 * t719 * t115 * t222 + 0.72e2 * t424 * t47 * t425 * t427 * t173 + 0.36e2 * t424 * t426 * t409 * t323 * t222
  t796 = t242 ** 2
  t799 = jnp.pi ** 2
  t818 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t28 * t139 + t143 * t21 * t145 * t250 / 0.8e1 + 0.3e1 / 0.32e2 * t143 * t144 * t255 * t257 - 0.3e1 / 0.16e2 * t143 * t146 * t452 - 0.9e1 / 0.64e2 * t143 * t18 / t139 / t474 / t243 * t257 * t250 + 0.9e1 / 0.32e2 * t143 * t256 * t250 * t452 - 0.3e1 / 0.16e2 * t143 * t261 * ((t658 + t783) * t137 + 0.162e3 * t431 * t243 * t129 * t247 + 0.104976e6 * t240 * t438 * t441 * t446 - 0.594e3 * t434 * t449 + 0.136048896e9 * t124 / t796 / t799 * t444 * params.b * t363 * t594 - 0.384912e6 * t442 * t445 * t489 + 0.924e3 * t245 * t246 * t585))
  v3rho3_0_ = 0.2e1 * r0 * t818 + 0.6e1 * t457

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
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = t26 * t22
  t29 = s0 * t27 * params.a1 + 0.1e1
  t30 = jnp.sqrt(t29)
  t31 = params.a * t30
  t34 = s0 * t27 * params.b1 + 0.1e1
  t35 = t34 ** (0.1e1 / 0.4e1)
  t36 = t35 ** 2
  t37 = t36 * t35
  t38 = 0.1e1 / t37
  t39 = t31 * t38
  t40 = s0 * t26
  t41 = t40 * t22
  t43 = l0 * t26
  t45 = 0.1e1 / t20 / r0
  t47 = -t43 * t45 + t41
  t48 = t47 ** 2
  t49 = params.a2 * t48
  t50 = 0.1e1 + t41
  t51 = t50 ** 2
  t52 = 0.1e1 / t51
  t55 = params.b * (t49 * t52 + 0.1e1)
  t56 = params.b2 ** 2
  t58 = jnp.sqrt(t56 + 0.1e1)
  t59 = t58 - params.b2
  t60 = s0 ** 2
  t61 = t60 * t25
  t62 = t18 ** 2
  t63 = t62 * r0
  t65 = 0.1e1 / t19 / t63
  t66 = t61 * t65
  t67 = 0.2e1 * t66
  t68 = l0 ** 2
  t69 = t68 * t25
  t70 = t18 * r0
  t73 = t69 / t19 / t70
  t74 = 0.2e1 * t73
  t75 = t67 - t74 - params.b2
  t76 = DBL_EPSILON ** (0.1e1 / 0.4e1)
  t77 = 0.1e1 / t76
  t78 = t75 < -t77
  t84 = t75 ** 2
  t85 = t84 * t75
  t86 = 0.1e1 / t85
  t88 = t84 ** 2
  t89 = t88 * t75
  t90 = 0.1e1 / t89
  t95 = f.my_piecewise3(0.0e0 < t75, t75, -t75)
  t96 = t95 < t76
  t99 = t88 * t84
  t101 = t88 ** 2
  t104 = -t77 < t75
  t105 = f.my_piecewise3(t104, t75, -t77)
  t106 = t105 ** 2
  t107 = 0.1e1 + t106
  t108 = jnp.sqrt(t107)
  t109 = t105 + t108
  t111 = f.my_piecewise5(t78, -0.4e1 * t66 + 0.4e1 * t73 + 0.2e1 * params.b2 - 0.1e1 / t75 / 0.2e1 + t86 / 0.8e1 - t90 / 0.16e2, t96, 0.1e1 - t67 + t74 + params.b2 + t84 / 0.2e1 - t88 / 0.8e1 + t99 / 0.16e2 - 0.5e1 / 0.128e3 * t101, 0.1e1 / t109)
  t113 = t111 * t59 + 0.1e1
  t114 = t25 - 0.1e1
  t115 = t114 * t59
  t117 = t111 * t115 + 0.1e1
  t118 = t117 ** 2
  t119 = t118 * t117
  t120 = 0.1e1 / t119
  t121 = t113 * t120
  t122 = t121 * t48
  t124 = t122 * t55 + t39 * t41 + 0.1e1
  t125 = t3 ** 2
  t126 = 0.1e1 / jnp.pi
  t127 = t126 ** (0.1e1 / 0.3e1)
  t128 = t127 ** 2
  t129 = t125 * t128
  t130 = 4 ** (0.1e1 / 0.3e1)
  t136 = 0.1e1 + 0.81e2 / 0.4e1 * t129 * t130 * params.b * s0 * t27
  t137 = 0.1e1 / t136
  t138 = t124 * t137
  t139 = jnp.sqrt(t138)
  t143 = t6 * t17
  t144 = 0.1e1 / t139
  t145 = t45 * t144
  t147 = params.a / t30
  t148 = t147 * t38
  t149 = t62 * t18
  t151 = 0.1e1 / t19 / t149
  t157 = 0.1e1 / t37 / t34
  t158 = t31 * t157
  t164 = 0.1e1 / t20 / t70
  t165 = t40 * t164
  t168 = params.a2 * t47
  t172 = -0.8e1 / 0.3e1 * t165 + 0.5e1 / 0.3e1 * t43 * t22
  t177 = 0.1e1 / t51 / t50
  t178 = t49 * t177
  t182 = params.b * (0.2e1 * t168 * t52 * t172 + 0.16e2 / 0.3e1 * t178 * t165)
  t184 = t55 * t59
  t185 = t61 * t151
  t189 = t69 / t19 / t62
  t191 = 0.1e1 / t84
  t192 = 0.32e2 / 0.3e1 * t185
  t193 = 0.20e2 / 0.3e1 * t189
  t194 = -t192 + t193
  t197 = 0.1e1 / t88
  t200 = 0.1e1 / t99
  t209 = t88 * t85
  t213 = t109 ** 2
  t214 = 0.1e1 / t213
  t215 = f.my_piecewise3(t104, t194, 0)
  t216 = 0.1e1 / t108
  t217 = t216 * t105
  t219 = t215 * t217 + t215
  t221 = f.my_piecewise5(t78, 0.64e2 / 0.3e1 * t185 - 0.40e2 / 0.3e1 * t189 + t191 * t194 / 0.2e1 - 0.3e1 / 0.8e1 * t197 * t194 + 0.5e1 / 0.16e2 * t200 * t194, t96, t192 - t193 + t75 * t194 - t85 * t194 / 0.2e1 + 0.3e1 / 0.8e1 * t89 * t194 - 0.5e1 / 0.16e2 * t209 * t194, -t214 * t219)
  t222 = t221 * t120
  t223 = t222 * t48
  t225 = t118 ** 2
  t226 = 0.1e1 / t225
  t227 = t113 * t226
  t228 = t55 * t227
  t229 = t48 * t114
  t230 = t59 * t221
  t231 = t229 * t230
  t234 = t55 * t113
  t235 = t120 * t47
  t236 = t235 * t172
  t239 = -0.8e1 / 0.3e1 * t148 * t61 * t151 * params.a1 + 0.4e1 * t158 * t61 * t151 * params.b1 - 0.8e1 / 0.3e1 * t39 * t165 + t182 * t122 + t184 * t223 - 0.3e1 * t228 * t231 + 0.2e1 * t234 * t236
  t241 = t136 ** 2
  t242 = 0.1e1 / t241
  t244 = t124 * t242 * t129
  t245 = t130 * params.b
  t246 = t245 * t165
  t249 = t137 * t239 + 0.54e2 * t244 * t246
  t253 = 0.1e1 / t20
  t255 = 0.1e1 / t139 / t138
  t256 = t253 * t255
  t257 = t249 ** 2
  t261 = t253 * t144
  t262 = t47 * t172
  t263 = t222 * t262
  t266 = t147 * t157
  t267 = t60 * s0
  t268 = t62 ** 2
  t271 = t267 / t268 / t18
  t272 = params.a1 * params.b1
  t277 = 0.1e1 / t20 / t62
  t278 = t40 * t277
  t283 = 0.1e1 / t19 / t62 / t70
  t284 = t61 * t283
  t286 = t69 * t65
  t288 = t194 ** 2
  t290 = 0.608e3 / 0.9e1 * t284
  t291 = 0.260e3 / 0.9e1 * t286
  t292 = t290 - t291
  t299 = 0.1e1 / t209
  t320 = 0.1e1 / t213 / t109
  t321 = t219 ** 2
  t324 = f.my_piecewise3(t104, t292, 0)
  t326 = 0.1e1 / t108 / t107
  t327 = t326 * t106
  t328 = t215 ** 2
  t332 = t216 * t328 + t217 * t324 - t327 * t328 + t324
  t335 = f.my_piecewise5(t78, -0.1216e4 / 0.9e1 * t284 + 0.520e3 / 0.9e1 * t286 - t86 * t288 + t191 * t292 / 0.2e1 + 0.3e1 / 0.2e1 * t90 * t288 - 0.3e1 / 0.8e1 * t197 * t292 - 0.15e2 / 0.8e1 * t299 * t288 + 0.5e1 / 0.16e2 * t200 * t292, t96, -t290 + t291 + t288 + t75 * t292 - 0.3e1 / 0.2e1 * t84 * t288 - t85 * t292 / 0.2e1 + 0.15e2 / 0.8e1 * t88 * t288 + 0.3e1 / 0.8e1 * t89 * t292 - 0.35e2 / 0.16e2 * t99 * t288 - 0.5e1 / 0.16e2 * t209 * t292, -t214 * t332 + 0.2e1 * t320 * t321)
  t336 = t59 * t335
  t337 = t229 * t336
  t348 = t182 * t227
  t351 = t172 ** 2
  t352 = params.a2 * t351
  t355 = t168 * t177
  t356 = t172 * s0
  t357 = t26 * t164
  t364 = 0.88e2 / 0.9e1 * t278 - 0.40e2 / 0.9e1 * t43 * t164
  t365 = t52 * t364
  t368 = t51 ** 2
  t369 = 0.1e1 / t368
  t370 = t49 * t369
  t376 = params.b * (0.2e1 * t352 * t52 + 0.64e2 / 0.3e1 * t355 * t356 * t357 + 0.2e1 * t168 * t365 + 0.256e3 / 0.3e1 * t370 * t284 - 0.176e3 / 0.9e1 * t178 * t278)
  t378 = t182 * t113
  t381 = t182 * t59
  t384 = t335 * t120
  t385 = t384 * t48
  t387 = t121 * t351
  t390 = t235 * t364
  t395 = params.a / t30 / t29
  t396 = t395 * t38
  t397 = params.a1 ** 2
  t401 = t34 ** 2
  t403 = 0.1e1 / t37 / t401
  t404 = t31 * t403
  t405 = params.b1 ** 2
  t409 = t59 ** 2
  t410 = t55 * t409
  t411 = t221 ** 2
  t412 = t411 * t226
  t413 = t412 * t229
  t416 = t47 * t114
  t418 = t416 * t230 * t172
  t422 = 0.1e1 / t225 / t117
  t423 = t113 * t422
  t424 = t55 * t423
  t425 = t114 ** 2
  t426 = t48 * t425
  t427 = t409 * t411
  t428 = t426 * t427
  t431 = 0.4e1 * t184 * t263 - 0.64e2 / 0.3e1 * t266 * t271 * t272 + 0.88e2 / 0.9e1 * t39 * t278 - 0.3e1 * t228 * t337 + 0.24e2 * t148 * t61 * t283 * params.a1 - 0.36e2 * t158 * t61 * t283 * params.b1 - 0.6e1 * t348 * t231 + t376 * t122 + 0.4e1 * t378 * t236 + 0.2e1 * t381 * t223 + t184 * t385 + 0.2e1 * t55 * t387 + 0.2e1 * t234 * t390 - 0.64e2 / 0.9e1 * t396 * t271 * t397 + 0.112e3 / 0.3e1 * t404 * t271 * t405 - 0.6e1 * t410 * t413 - 0.12e2 * t228 * t418 + 0.12e2 * t424 * t428
  t434 = t239 * t242 * t129
  t438 = 0.1e1 / t241 / t136
  t441 = t3 * t127 * t126
  t442 = t124 * t438 * t441
  t443 = t130 ** 2
  t444 = params.b ** 2
  t445 = t443 * t444
  t446 = t445 * t284
  t449 = t245 * t278
  t452 = t137 * t431 - 0.198e3 * t244 * t449 + 0.108e3 * t246 * t434 + 0.34992e5 * t442 * t446
  t456 = t124 ** 2
  t459 = 0.1e1 / t139 / t456 / t242
  t460 = t19 * t459
  t461 = t257 * t249
  t465 = t19 * t255
  t466 = t249 * t452
  t470 = t19 * t144
  t472 = 0.1e1 / t19 / t268
  t477 = t409 * t59
  t479 = t411 * t221
  t481 = t479 * t422 * t426
  t488 = 0.1e1 / t268 / t70
  t489 = t267 * t488
  t493 = t29 ** 2
  t496 = params.a / t30 / t493
  t497 = t496 * t38
  t498 = t60 ** 2
  t501 = 0.1e1 / t20 / t268 / t63
  t502 = t498 * t501
  t503 = t397 * params.a1
  t504 = t503 * t26
  t510 = 0.1e1 / t37 / t401 / t34
  t511 = t31 * t510
  t512 = t405 * params.b1
  t513 = t512 * t26
  t519 = t384 * t262
  t522 = t47 * t364
  t523 = t222 * t522
  t530 = params.a2 * t172
  t533 = t352 * t177
  t536 = t168 * t369
  t537 = t172 * t60
  t538 = t25 * t283
  t542 = t364 * s0
  t543 = t542 * t357
  t546 = t26 * t277
  t551 = 0.1e1 / t20 / t63
  t552 = t40 * t551
  t556 = -0.1232e4 / 0.27e2 * t552 + 0.440e3 / 0.27e2 * t43 * t277
  t557 = t52 * t556
  t561 = 0.1e1 / t368 / t50
  t562 = t561 * t267
  t566 = t61 * t472
  t572 = params.b * (0.6e1 * t530 * t365 + 0.32e2 * t533 * t165 + 0.512e3 * t536 * t537 * t538 + 0.32e2 * t355 * t543 - 0.352e3 / 0.3e1 * t355 * t356 * t546 + 0.2e1 * t168 * t557 + 0.16384e5 / 0.9e1 * t49 * t562 * t488 - 0.2816e4 / 0.3e1 * t370 * t566 + 0.2464e4 / 0.27e2 * t178 * t552)
  t578 = t115 * t221
  t579 = t522 * t578
  t582 = t47 * t425
  t584 = t582 * t427 * t172
  t589 = t426 * t409 * t335 * t221
  t593 = t416 * t336 * t172
  t596 = t376 * t59
  t599 = t222 * t351
  t602 = 0.2728e4 / 0.9e1 * t158 * t61 * t472 * params.b1 + 0.36e2 * t55 * t477 * t481 - 0.18e2 * t182 * t409 * t413 + 0.1216e4 / 0.3e1 * t266 * t489 * t272 - 0.256e3 / 0.9e1 * t497 * t502 * t504 + 0.2464e4 / 0.9e1 * t511 * t502 * t513 + 0.12e2 * t381 * t263 + 0.6e1 * t184 * t519 + 0.6e1 * t184 * t523 - 0.5456e4 / 0.27e2 * t148 * t61 * t472 * params.a1 + t572 * t122 + 0.6e1 * t182 * t387 - 0.36e2 * t348 * t418 - 0.18e2 * t228 * t579 + 0.72e2 * t424 * t584 + 0.36e2 * t424 * t589 - 0.18e2 * t228 * t593 + 0.3e1 * t596 * t223 + 0.6e1 * t184 * t599
  t610 = t69 * t151
  t612 = t288 * t194
  t615 = t86 * t194
  t618 = 0.13376e5 / 0.27e2 * t566
  t619 = 0.4160e4 / 0.27e2 * t610
  t620 = -t618 + t619
  t625 = t90 * t194
  t630 = 0.1e1 / t101
  t633 = t299 * t194
  t638 = 0.26752e5 / 0.27e2 * t566 - 0.8320e4 / 0.27e2 * t610 + 0.3e1 * t197 * t612 - 0.3e1 * t615 * t292 + t191 * t620 / 0.2e1 - 0.15e2 / 0.2e1 * t200 * t612 + 0.9e1 / 0.2e1 * t625 * t292 - 0.3e1 / 0.8e1 * t197 * t620 + 0.105e3 / 0.8e1 * t630 * t612 - 0.45e2 / 0.8e1 * t633 * t292 + 0.5e1 / 0.16e2 * t200 * t620
  t644 = t84 * t194
  t651 = t88 * t194
  t658 = t99 * t194
  t663 = t618 - t619 + 0.3e1 * t194 * t292 + t75 * t620 - 0.3e1 * t75 * t612 - 0.9e1 / 0.2e1 * t644 * t292 - t85 * t620 / 0.2e1 + 0.15e2 / 0.2e1 * t85 * t612 + 0.45e2 / 0.8e1 * t651 * t292 + 0.3e1 / 0.8e1 * t89 * t620 - 0.105e3 / 0.8e1 * t89 * t612 - 0.105e3 / 0.16e2 * t658 * t292 - 0.5e1 / 0.16e2 * t209 * t620
  t664 = t213 ** 2
  t665 = 0.1e1 / t664
  t669 = t320 * t219
  t672 = f.my_piecewise3(t104, t620, 0)
  t673 = t107 ** 2
  t675 = 0.1e1 / t108 / t673
  t677 = t675 * t106 * t105
  t678 = t328 * t215
  t681 = t326 * t105
  t687 = t216 * t215
  t691 = -0.3e1 * t215 * t324 * t327 + t217 * t672 + 0.3e1 * t324 * t687 + 0.3e1 * t677 * t678 - 0.3e1 * t678 * t681 + t672
  t694 = f.my_piecewise5(t78, t638, t96, t663, -0.6e1 * t219 * t321 * t665 - t214 * t691 + 0.6e1 * t332 * t669)
  t695 = t694 * t120
  t696 = t695 * t48
  t698 = t120 * t172
  t699 = t698 * t364
  t702 = t235 * t556
  t711 = t376 * t113
  t715 = 0.1e1 / t225 / t118
  t716 = t113 * t715
  t717 = t55 * t716
  t718 = t425 * t114
  t719 = t48 * t718
  t720 = t477 * t479
  t721 = t719 * t720
  t724 = t55 * t427
  t725 = t226 * t47
  t726 = t172 * t114
  t727 = t725 * t726
  t730 = t409 * t221
  t731 = t55 * t730
  t732 = t226 * t48
  t734 = t732 * t114 * t335
  t738 = t395 * t157 * t498
  t740 = params.b1 * t26
  t745 = t147 * t403 * t498
  t747 = t405 * t26
  t753 = t59 * t694
  t754 = t229 * t753
  t757 = t376 * t227
  t760 = t351 * t114
  t761 = t760 * t230
  t764 = t182 * t423
  t767 = -0.1232e4 / 0.27e2 * t39 * t552 + 0.6e1 * t378 * t390 + 0.3e1 * t381 * t385 + t184 * t696 + 0.6e1 * t234 * t699 + 0.2e1 * t234 * t702 + 0.1216e4 / 0.9e1 * t396 * t489 * t397 - 0.2128e4 / 0.3e1 * t404 * t489 * t405 + 0.6e1 * t711 * t236 - 0.60e2 * t717 * t721 - 0.36e2 * t724 * t727 - 0.18e2 * t731 * t734 - 0.128e3 / 0.3e1 * t738 * t501 * t397 * t740 - 0.448e3 / 0.3e1 * t745 * t501 * params.a1 * t747 - 0.9e1 * t348 * t337 - 0.3e1 * t228 * t754 - 0.9e1 * t757 * t231 - 0.18e2 * t228 * t761 + 0.36e2 * t764 * t428
  t768 = t602 + t767
  t771 = t431 * t242 * t129
  t775 = t239 * t438 * t441
  t780 = t241 ** 2
  t781 = 0.1e1 / t780
  t783 = jnp.pi ** 2
  t784 = 0.1e1 / t783
  t785 = t124 * t781 * t784
  t787 = t444 * params.b * t267
  t788 = t787 * t488
  t791 = t445 * t566
  t794 = t245 * t552
  t797 = t137 * t768 + 0.924e3 * t244 * t794 + 0.162e3 * t246 * t771 - 0.594e3 * t434 * t449 - 0.384912e6 * t442 * t791 + 0.104976e6 * t446 * t775 + 0.136048896e9 * t785 * t788
  t802 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t139 + t143 * t145 * t249 / 0.8e1 + 0.3e1 / 0.32e2 * t143 * t256 * t257 - 0.3e1 / 0.16e2 * t143 * t261 * t452 - 0.9e1 / 0.64e2 * t143 * t460 * t461 + 0.9e1 / 0.32e2 * t143 * t465 * t466 - 0.3e1 / 0.16e2 * t143 * t470 * t797)
  t834 = t257 ** 2
  t842 = t452 ** 2
  t851 = 0.1e1 / t268 / t62
  t860 = 0.1e1 / t20 / t268 / t149
  t861 = t498 * t860
  t875 = t40 / t20 / t149
  t888 = 0.1e1 / t19 / t268 / r0
  t889 = t61 * t888
  t892 = t364 ** 2
  t901 = 0.20944e5 / 0.81e2 * t875 - 0.6160e4 / 0.81e2 * t43 * t551
  t921 = -0.360448e6 / 0.9e1 * t49 * t562 * t851 + 0.655360e6 / 0.27e2 * t49 / t368 / t51 * t861 * t26 + 0.1024e4 * t352 * t369 * t284 + 0.131072e6 / 0.9e1 * t168 * t561 * t172 * t267 * t488 - 0.41888e5 / 0.81e2 * t178 * t875 + 0.1024e4 * t536 * t364 * t60 * t538 + 0.128e3 / 0.3e1 * t355 * t556 * s0 * t357 + 0.250624e6 / 0.27e2 * t370 * t889 + 0.6e1 * params.a2 * t892 * t52 + 0.8e1 * t530 * t557 + 0.2e1 * t168 * t52 * t901 + 0.128e3 * t530 * t177 * t543 - 0.704e3 / 0.3e1 * t533 * t278 - 0.22528e5 / 0.3e1 * t536 * t537 * t25 * t472 - 0.704e3 / 0.3e1 * t355 * t542 * t546 + 0.19712e5 / 0.27e2 * t355 * t356 * t26 * t551
  t928 = t267 * t851
  t945 = t69 * t283
  t947 = t288 ** 2
  t953 = t292 ** 2
  t958 = 0.334400e6 / 0.81e2 * t889
  t959 = 0.79040e5 / 0.81e2 * t945
  t960 = t958 - t959
  t987 = -0.668800e6 / 0.81e2 * t889 + 0.158080e6 / 0.81e2 * t945 - 0.12e2 * t90 * t947 + 0.18e2 * t197 * t288 * t292 - 0.3e1 * t86 * t953 - 0.4e1 * t615 * t620 + t191 * t960 / 0.2e1 + 0.45e2 * t299 * t947 - 0.45e2 * t200 * t288 * t292 + 0.9e1 / 0.2e1 * t90 * t953 + 0.6e1 * t625 * t620 - 0.3e1 / 0.8e1 * t197 * t960 - 0.105e3 / t101 / t75 * t947 + 0.315e3 / 0.4e1 * t630 * t288 * t292 - 0.45e2 / 0.8e1 * t299 * t953 - 0.15e2 / 0.2e1 * t633 * t620 + 0.5e1 / 0.16e2 * t200 * t960
  t1024 = 0.3e1 * t953 + 0.4e1 * t194 * t620 + t75 * t960 - 0.3e1 * t947 - t85 * t960 / 0.2e1 + 0.3e1 / 0.8e1 * t89 * t960 - 0.5e1 / 0.16e2 * t209 * t960 - t958 + t959 - 0.18e2 * t75 * t288 * t292 - 0.9e1 / 0.2e1 * t84 * t953 - 0.6e1 * t644 * t620 + 0.45e2 / 0.2e1 * t84 * t947 + 0.45e2 * t85 * t288 * t292 + 0.45e2 / 0.8e1 * t88 * t953 + 0.15e2 / 0.2e1 * t651 * t620 - 0.525e3 / 0.8e1 * t88 * t947 - 0.315e3 / 0.4e1 * t89 * t288 * t292 - 0.105e3 / 0.16e2 * t99 * t953 - 0.35e2 / 0.4e1 * t658 * t620
  t1027 = t321 ** 2
  t1033 = t332 ** 2
  t1038 = f.my_piecewise3(t104, t960, 0)
  t1042 = t106 ** 2
  t1044 = t328 ** 2
  t1050 = t328 * t324
  t1057 = t324 ** 2
  t1068 = t1038 - 0.15e2 / t108 / t673 / t107 * t1042 * t1044 + 0.18e2 * t675 * t106 * t1044 + 0.18e2 * t677 * t1050 - 0.3e1 * t326 * t1044 - 0.18e2 * t681 * t1050 - 0.3e1 * t327 * t1057 - 0.4e1 * t327 * t215 * t672 + 0.3e1 * t216 * t1057 + 0.4e1 * t687 * t672 + t217 * t1038
  t1071 = f.my_piecewise5(t78, t987, t96, t1024, 0.24e2 / t664 / t109 * t1027 - 0.36e2 * t665 * t321 * t332 + 0.6e1 * t320 * t1033 + 0.8e1 * t669 * t691 - t214 * t1068)
  t1097 = t498 * s0
  t1098 = t268 ** 2
  t1101 = 0.1e1 / t19 / t1098 / r0
  t1102 = t1097 * t1101
  t1103 = t397 ** 2
  t1110 = params.b * t921 * t122 + 0.4e1 * t381 * t696 + 0.12e2 * t711 * t390 + 0.287056e6 / 0.27e2 * t404 * t928 * t405 + 0.20944e5 / 0.81e2 * t39 * t875 - 0.164032e6 / 0.81e2 * t396 * t928 * t397 + 0.6e1 * t596 * t385 + 0.12e2 * t184 * t384 * t351 + 0.8e1 * t378 * t702 + t184 * t1071 * t120 * t48 + 0.8e1 * t234 * t698 * t556 + 0.2e1 * t234 * t235 * t901 + 0.12e2 * t376 * t387 + 0.6e1 * t55 * t121 * t892 - 0.241472e6 / 0.27e2 * t511 * t861 * t513 + 0.12e2 * t184 * t384 * t522 - 0.10240e5 / 0.27e2 * params.a / t30 / t493 / t29 * t38 * t1102 * t1103 * t25 + 0.24e2 * t596 * t263
  t1136 = t47 * t556
  t1144 = t409 ** 2
  t1146 = t411 ** 2
  t1163 = t335 ** 2
  t1168 = t401 ** 2
  t1172 = t405 ** 2
  t1180 = 0.24e2 * t184 * t222 * t172 * t364 + 0.8e1 * t572 * t113 * t236 + 0.4e1 * t572 * t59 * t223 + 0.24e2 * t378 * t699 + 0.24e2 * t381 * t599 + 0.48752e5 / 0.27e2 * t148 * t61 * t888 * params.a1 + 0.24e2 * t381 * t523 + 0.24e2 * t381 * t519 + 0.8e1 * t184 * t695 * t262 + 0.8e1 * t184 * t222 * t1136 - 0.24376e5 / 0.9e1 * t158 * t61 * t888 * params.b1 - 0.240e3 * t55 * t1144 * t1146 * t715 * t719 - 0.72e2 * t410 * t412 * t760 - 0.164032e6 / 0.27e2 * t266 * t928 * t272 + 0.144e3 * t182 * t477 * t481 - 0.36e2 * t376 * t409 * t413 - 0.18e2 * t410 * t1163 * t226 * t229 + 0.49280e5 / 0.9e1 * t31 / t37 / t1168 * t1102 * t1172 * t25 + 0.25088e5 / 0.27e2 * t497 * t861 * t504
  t1189 = t425 ** 2
  t1233 = t477 * t411
  t1267 = -0.240e3 * t182 * t716 * t721 + 0.360e3 * t55 * t113 / t225 / t119 * t48 * t1189 * t1144 * t1146 - 0.24e2 * t731 * t732 * t114 * t694 - 0.4096e4 / 0.9e1 * t496 * t157 * t1097 * t1101 * t503 * params.b1 * t25 - 0.7168e4 / 0.9e1 * t395 * t403 * t1097 * t1101 * t397 * t405 * t25 - 0.78848e5 / 0.27e2 * t147 * t510 * t1097 * t1101 * params.a1 * t512 * t25 - 0.12e2 * t348 * t754 - 0.3e1 * t228 * t229 * t59 * t1071 + 0.72e2 * t376 * t423 * t428 + 0.144e3 * t424 * t351 * t425 * t427 + 0.216e3 * t55 * t1233 * t422 * t48 * t425 * t335 + 0.288e3 * t55 * t720 * t422 * t47 * t425 * t172 - 0.72e2 * t182 * t730 * t734 - 0.144e3 * t182 * t427 * t727 - 0.12e2 * t572 * t227 * t231 + 0.12544e5 / 0.9e1 * t738 * t860 * t397 * t740 + 0.43904e5 / 0.9e1 * t745 * t860 * params.a1 * t747 + 0.36e2 * t424 * t426 * t409 * t1163
  t1334 = -0.72e2 * t348 * t761 - 0.36e2 * t228 * t760 * t336 - 0.72e2 * t724 * t725 * t364 * t114 - 0.18e2 * t757 * t337 + 0.288e3 * t55 * t423 * t47 * t425 * t409 * t221 * t172 * t335 - 0.72e2 * t757 * t418 + 0.48e2 * t424 * t426 * t409 * t694 * t221 - 0.72e2 * t348 * t579 - 0.24e2 * t228 * t1136 * t578 + 0.144e3 * t424 * t582 * t427 * t364 - 0.72e2 * t348 * t593 - 0.24e2 * t228 * t416 * t753 * t172 - 0.36e2 * t228 * t416 * t336 * t364 - 0.72e2 * t228 * t726 * t230 * t364 + 0.288e3 * t764 * t584 + 0.144e3 * t764 * t589 - 0.480e3 * t717 * t47 * t718 * t720 * t172 - 0.360e3 * t717 * t719 * t1233 * t335 - 0.144e3 * t731 * t725 * t726 * t335
  t1359 = t444 ** 2
  t1378 = (t1110 + t1180 + t1267 + t1334) * t137 + 0.216e3 * t768 * t242 * t129 * t246 + 0.209952e6 * t431 * t438 * t441 * t446 - 0.1188e4 * t771 * t449 + 0.544195584e9 * t239 * t781 * t784 * t788 - 0.1539648e7 * t775 * t791 + 0.3696e4 * t434 * t794 + 0.29386561536e11 * t124 / t780 / t136 * t784 * t1359 * t498 * t860 * t125 * t128 * t130 * t26 - 0.2993075712e10 * t785 * t787 * t851 + 0.3806352e7 * t442 * t445 * t889 - 0.5236e4 * t244 * t245 * t875
  t1382 = 0.10e2 / 0.27e2 * t6 * t17 * t164 * t139 - 0.5e1 / 0.18e2 * t143 * t22 * t144 * t249 - t143 * t45 * t255 * t257 / 0.8e1 + t143 * t145 * t452 / 0.4e1 - 0.3e1 / 0.16e2 * t143 * t253 * t459 * t461 + 0.3e1 / 0.8e1 * t143 * t256 * t466 - t143 * t261 * t797 / 0.4e1 + 0.45e2 / 0.128e3 * t143 * t19 / t139 / t456 / t124 / t438 * t834 - 0.27e2 / 0.32e2 * t143 * t460 * t257 * t452 + 0.9e1 / 0.32e2 * t143 * t465 * t842 + 0.3e1 / 0.8e1 * t143 * t465 * t249 * t797 - 0.3e1 / 0.16e2 * t143 * t470 * t1378
  t1383 = f.my_piecewise3(t2, 0, t1382)
  v4rho4_0_ = 0.2e1 * r0 * t1383 + 0.8e1 * t802

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
  t33 = r0 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / t33
  t39 = params.a1 * s0 * t37 + 0.1e1
  t40 = jnp.sqrt(t39)
  t41 = params.a * t40
  t44 = params.b1 * s0 * t37 + 0.1e1
  t45 = t44 ** (0.1e1 / 0.4e1)
  t46 = t45 ** 2
  t47 = t46 * t45
  t48 = 0.1e1 / t47
  t49 = t48 * s0
  t52 = s0 * t37
  t56 = t52 - l0 / t35 / r0
  t57 = t56 ** 2
  t58 = params.a2 * t57
  t59 = 0.1e1 + t52
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t64 = params.b * (t58 * t61 + 0.1e1)
  t65 = params.b2 ** 2
  t67 = jnp.sqrt(t65 + 0.1e1)
  t68 = t67 - params.b2
  t69 = s0 ** 2
  t70 = t33 ** 2
  t73 = 0.1e1 / t34 / t70 / r0
  t74 = t69 * t73
  t75 = l0 ** 2
  t76 = t33 * r0
  t79 = t75 / t34 / t76
  t80 = t74 - t79 - params.b2
  t81 = DBL_EPSILON ** (0.1e1 / 0.4e1)
  t82 = 0.1e1 / t81
  t83 = t80 < -t82
  t86 = 0.2e1 * params.b2
  t89 = t80 ** 2
  t90 = t89 * t80
  t91 = 0.1e1 / t90
  t93 = t89 ** 2
  t94 = t93 * t80
  t95 = 0.1e1 / t94
  t100 = f.my_piecewise3(0.0e0 < t80, t80, -t80)
  t101 = t100 < t81
  t104 = t93 * t89
  t106 = t93 ** 2
  t109 = -t82 < t80
  t110 = f.my_piecewise3(t109, t80, -t82)
  t111 = t110 ** 2
  t112 = 0.1e1 + t111
  t113 = jnp.sqrt(t112)
  t114 = t110 + t113
  t116 = f.my_piecewise5(t83, -0.2e1 * t74 + 0.2e1 * t79 + t86 - 0.1e1 / t80 / 0.2e1 + t91 / 0.8e1 - t95 / 0.16e2, t101, 0.1e1 - t74 + t79 + params.b2 + t89 / 0.2e1 - t93 / 0.8e1 + t104 / 0.16e2 - 0.5e1 / 0.128e3 * t106, 0.1e1 / t114)
  t118 = t68 * t116 + 0.1e1
  t119 = 2 ** (0.1e1 / 0.3e1)
  t120 = t119 - 0.1e1
  t121 = t120 * t68
  t123 = t121 * t116 + 0.1e1
  t124 = t123 ** 2
  t126 = 0.1e1 / t124 / t123
  t127 = t118 * t126
  t128 = t127 * t57
  t130 = t41 * t49 * t37 + t64 * t128 + 0.1e1
  t131 = t2 ** 2
  t132 = 0.1e1 / jnp.pi
  t133 = t132 ** (0.1e1 / 0.3e1)
  t134 = t133 ** 2
  t135 = t131 * t134
  t136 = 4 ** (0.1e1 / 0.3e1)
  t137 = t135 * t136
  t142 = 0.1e1 + 0.81e2 / 0.4e1 * t137 * params.b * s0 * t37
  t143 = 0.1e1 / t142
  t144 = t130 * t143
  t145 = jnp.sqrt(t144)
  t149 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t150 = t149 * f.p.zeta_threshold
  t152 = f.my_piecewise3(t20, t150, t21 * t19)
  t153 = t30 ** 2
  t154 = 0.1e1 / t153
  t158 = t5 * t152 * t154 * t145 / 0.8e1
  t159 = t5 * t152
  t160 = 0.1e1 / t145
  t161 = t30 * t160
  t163 = params.a / t40
  t164 = t163 * t48
  t168 = t69 / t34 / t70 / t33
  t173 = 0.1e1 / t47 / t44
  t174 = t41 * t173
  t179 = 0.1e1 / t35 / t76
  t183 = params.a2 * t56
  t184 = s0 * t179
  t188 = -0.8e1 / 0.3e1 * t184 + 0.5e1 / 0.3e1 * l0 * t37
  t193 = 0.1e1 / t60 / t59
  t194 = t193 * s0
  t199 = params.b * (0.2e1 * t183 * t61 * t188 + 0.16e2 / 0.3e1 * t58 * t194 * t179)
  t201 = t64 * t68
  t205 = t75 / t34 / t70
  t207 = 0.1e1 / t89
  t208 = 0.16e2 / 0.3e1 * t168
  t209 = 0.10e2 / 0.3e1 * t205
  t210 = -t208 + t209
  t213 = 0.1e1 / t93
  t216 = 0.1e1 / t104
  t225 = t93 * t90
  t229 = t114 ** 2
  t230 = 0.1e1 / t229
  t231 = f.my_piecewise3(t109, t210, 0)
  t232 = 0.1e1 / t113
  t233 = t232 * t110
  t235 = t233 * t231 + t231
  t237 = f.my_piecewise5(t83, 0.32e2 / 0.3e1 * t168 - 0.20e2 / 0.3e1 * t205 + t207 * t210 / 0.2e1 - 0.3e1 / 0.8e1 * t213 * t210 + 0.5e1 / 0.16e2 * t216 * t210, t101, t208 - t209 + t80 * t210 - t90 * t210 / 0.2e1 + 0.3e1 / 0.8e1 * t94 * t210 - 0.5e1 / 0.16e2 * t225 * t210, -t230 * t235)
  t238 = t237 * t126
  t239 = t238 * t57
  t241 = t124 ** 2
  t242 = 0.1e1 / t241
  t243 = t118 * t242
  t244 = t64 * t243
  t245 = t57 * t120
  t246 = t68 * t237
  t247 = t245 * t246
  t250 = t64 * t118
  t251 = t126 * t56
  t252 = t251 * t188
  t255 = -0.4e1 / 0.3e1 * t164 * t168 * params.a1 + 0.2e1 * t174 * t168 * params.b1 - 0.8e1 / 0.3e1 * t41 * t49 * t179 + t199 * t128 + t201 * t239 - 0.3e1 * t244 * t247 + 0.2e1 * t250 * t252
  t257 = t142 ** 2
  t258 = 0.1e1 / t257
  t260 = t130 * t258 * t135
  t261 = t136 * params.b
  t262 = t261 * t184
  t265 = t255 * t143 + 0.54e2 * t260 * t262
  t266 = t161 * t265
  t270 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t145 - t158 - 0.3e1 / 0.16e2 * t159 * t266)
  t272 = r1 <= f.p.dens_threshold
  t273 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t274 = 0.1e1 + t273
  t275 = t274 <= f.p.zeta_threshold
  t276 = t274 ** (0.1e1 / 0.3e1)
  t278 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t281 = f.my_piecewise3(t275, 0, 0.4e1 / 0.3e1 * t276 * t278)
  t284 = r1 ** 2
  t285 = r1 ** (0.1e1 / 0.3e1)
  t286 = t285 ** 2
  t288 = 0.1e1 / t286 / t284
  t290 = params.a1 * s2 * t288 + 0.1e1
  t291 = jnp.sqrt(t290)
  t292 = params.a * t291
  t295 = params.b1 * s2 * t288 + 0.1e1
  t296 = t295 ** (0.1e1 / 0.4e1)
  t297 = t296 ** 2
  t298 = t297 * t296
  t299 = 0.1e1 / t298
  t300 = t299 * s2
  t303 = s2 * t288
  t307 = t303 - l1 / t286 / r1
  t308 = t307 ** 2
  t309 = params.a2 * t308
  t310 = 0.1e1 + t303
  t311 = t310 ** 2
  t312 = 0.1e1 / t311
  t315 = params.b * (t309 * t312 + 0.1e1)
  t316 = s2 ** 2
  t317 = t284 ** 2
  t320 = 0.1e1 / t285 / t317 / r1
  t321 = t316 * t320
  t322 = l1 ** 2
  t323 = t284 * r1
  t326 = t322 / t285 / t323
  t327 = t321 - t326 - params.b2
  t328 = t327 < -t82
  t333 = t327 ** 2
  t334 = t333 * t327
  t335 = 0.1e1 / t334
  t337 = t333 ** 2
  t338 = t337 * t327
  t339 = 0.1e1 / t338
  t344 = f.my_piecewise3(0.0e0 < t327, t327, -t327)
  t345 = t344 < t81
  t348 = t337 * t333
  t350 = t337 ** 2
  t353 = -t82 < t327
  t354 = f.my_piecewise3(t353, t327, -t82)
  t355 = t354 ** 2
  t356 = 0.1e1 + t355
  t357 = jnp.sqrt(t356)
  t358 = t354 + t357
  t360 = f.my_piecewise5(t328, -0.2e1 * t321 + 0.2e1 * t326 + t86 - 0.1e1 / t327 / 0.2e1 + t335 / 0.8e1 - t339 / 0.16e2, t345, 0.1e1 - t321 + t326 + params.b2 + t333 / 0.2e1 - t337 / 0.8e1 + t348 / 0.16e2 - 0.5e1 / 0.128e3 * t350, 0.1e1 / t358)
  t362 = t68 * t360 + 0.1e1
  t364 = t121 * t360 + 0.1e1
  t365 = t364 ** 2
  t367 = 0.1e1 / t365 / t364
  t368 = t362 * t367
  t369 = t368 * t308
  t371 = t292 * t300 * t288 + t315 * t369 + 0.1e1
  t376 = 0.1e1 + 0.81e2 / 0.4e1 * t137 * params.b * s2 * t288
  t377 = 0.1e1 / t376
  t378 = t371 * t377
  t379 = jnp.sqrt(t378)
  t384 = f.my_piecewise3(t275, t150, t276 * t274)
  t388 = t5 * t384 * t154 * t379 / 0.8e1
  t390 = f.my_piecewise3(t272, 0, -0.3e1 / 0.8e1 * t5 * t281 * t30 * t379 - t388)
  t392 = t21 ** 2
  t393 = 0.1e1 / t392
  t394 = t26 ** 2
  t399 = t16 / t22 / t6
  t401 = -0.2e1 * t23 + 0.2e1 * t399
  t402 = f.my_piecewise5(t10, 0, t14, 0, t401)
  t406 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t393 * t394 + 0.4e1 / 0.3e1 * t21 * t402)
  t413 = t5 * t29 * t154 * t145
  t419 = 0.1e1 / t153 / t6
  t423 = t5 * t152 * t419 * t145 / 0.12e2
  t426 = t159 * t154 * t160 * t265
  t431 = t265 ** 2
  t435 = t188 ** 2
  t445 = 0.1e1 / t35 / t70
  t446 = s0 * t445
  t450 = 0.88e2 / 0.9e1 * t446 - 0.40e2 / 0.9e1 * l0 * t179
  t454 = t60 ** 2
  t459 = 0.1e1 / t34 / t70 / t76
  t472 = t69 * t459
  t474 = t75 * t73
  t476 = t210 ** 2
  t478 = 0.304e3 / 0.9e1 * t472
  t479 = 0.130e3 / 0.9e1 * t474
  t480 = t478 - t479
  t509 = t235 ** 2
  t512 = f.my_piecewise3(t109, t480, 0)
  t516 = t231 ** 2
  t523 = f.my_piecewise5(t83, -0.608e3 / 0.9e1 * t472 + 0.260e3 / 0.9e1 * t474 - t91 * t476 + t207 * t480 / 0.2e1 + 0.3e1 / 0.2e1 * t95 * t476 - 0.3e1 / 0.8e1 * t213 * t480 - 0.15e2 / 0.8e1 / t225 * t476 + 0.5e1 / 0.16e2 * t216 * t480, t101, -t478 + t479 + t476 + t80 * t480 - 0.3e1 / 0.2e1 * t89 * t476 - t90 * t480 / 0.2e1 + 0.15e2 / 0.8e1 * t93 * t476 + 0.3e1 / 0.8e1 * t94 * t480 - 0.35e2 / 0.16e2 * t104 * t476 - 0.5e1 / 0.16e2 * t225 * t480, 0.2e1 / t229 / t114 * t509 - t230 * (t512 - 0.1e1 / t113 / t112 * t111 * t516 + t232 * t516 + t233 * t512))
  t548 = t70 ** 2
  t551 = t69 * s0 / t548 / t33
  t552 = params.a1 ** 2
  t556 = t44 ** 2
  t560 = params.b1 ** 2
  t571 = params.a1 * params.b1
  t586 = t120 ** 2
  t588 = t68 ** 2
  t589 = t237 ** 2
  t604 = params.b * (0.2e1 * params.a2 * t435 * t61 + 0.64e2 / 0.3e1 * t183 * t193 * t188 * s0 * t179 + 0.2e1 * t183 * t61 * t450 + 0.128e3 / 0.3e1 * t58 / t454 * t69 * t459 - 0.176e3 / 0.9e1 * t58 * t194 * t445) * t128 - 0.6e1 * t199 * t243 * t247 - 0.3e1 * t244 * t245 * t68 * t523 + 0.4e1 * t199 * t118 * t252 + 0.2e1 * t199 * t68 * t239 + t201 * t523 * t126 * t57 + 0.2e1 * t64 * t127 * t435 + 0.2e1 * t250 * t251 * t450 - 0.16e2 / 0.9e1 * params.a / t40 / t39 * t48 * t551 * t552 + 0.28e2 / 0.3e1 * t41 / t47 / t556 * t551 * t560 + 0.88e2 / 0.9e1 * t41 * t49 * t445 + 0.12e2 * t164 * t472 * params.a1 - 0.16e2 / 0.3e1 * t163 * t173 * t551 * t571 - 0.18e2 * t174 * t472 * params.b1 + 0.4e1 * t201 * t238 * t56 * t188 + 0.12e2 * t64 * t118 / t241 / t123 * t57 * t586 * t588 * t589 - 0.6e1 * t64 * t588 * t589 * t242 * t245 - 0.12e2 * t244 * t56 * t120 * t246 * t188
  t614 = t2 * t133 * t132
  t616 = t136 ** 2
  t617 = params.b ** 2
  t618 = t616 * t617
  t630 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t406 * t30 * t145 - t413 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t29 * t266 + t423 - t426 / 0.8e1 + 0.3e1 / 0.32e2 * t159 * t30 / t145 / t144 * t431 - 0.3e1 / 0.16e2 * t159 * t161 * (t604 * t143 + 0.108e3 * t255 * t258 * t135 * t262 + 0.17496e5 * t130 / t257 / t142 * t614 * t618 * t472 - 0.198e3 * t260 * t261 * t446))
  t631 = t276 ** 2
  t632 = 0.1e1 / t631
  t633 = t278 ** 2
  t637 = f.my_piecewise5(t14, 0, t10, 0, -t401)
  t641 = f.my_piecewise3(t275, 0, 0.4e1 / 0.9e1 * t632 * t633 + 0.4e1 / 0.3e1 * t276 * t637)
  t648 = t5 * t281 * t154 * t379
  t653 = t5 * t384 * t419 * t379 / 0.12e2
  t655 = f.my_piecewise3(t272, 0, -0.3e1 / 0.8e1 * t5 * t641 * t30 * t379 - t648 / 0.4e1 + t653)
  d11 = 0.2e1 * t270 + 0.2e1 * t390 + t6 * (t630 + t655)
  t658 = -t7 - t24
  t659 = f.my_piecewise5(t10, 0, t14, 0, t658)
  t662 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t659)
  t668 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t662 * t30 * t145 - t158)
  t670 = f.my_piecewise5(t14, 0, t10, 0, -t658)
  t673 = f.my_piecewise3(t275, 0, 0.4e1 / 0.3e1 * t276 * t670)
  t678 = t5 * t384
  t679 = 0.1e1 / t379
  t680 = t30 * t679
  t682 = params.a / t291
  t683 = t682 * t299
  t687 = t316 / t285 / t317 / t284
  t692 = 0.1e1 / t298 / t295
  t693 = t292 * t692
  t698 = 0.1e1 / t286 / t323
  t702 = params.a2 * t307
  t703 = s2 * t698
  t707 = -0.8e1 / 0.3e1 * t703 + 0.5e1 / 0.3e1 * l1 * t288
  t712 = 0.1e1 / t311 / t310
  t713 = t712 * s2
  t718 = params.b * (0.2e1 * t702 * t312 * t707 + 0.16e2 / 0.3e1 * t309 * t713 * t698)
  t720 = t315 * t68
  t724 = t322 / t285 / t317
  t726 = 0.1e1 / t333
  t727 = 0.16e2 / 0.3e1 * t687
  t728 = 0.10e2 / 0.3e1 * t724
  t729 = -t727 + t728
  t732 = 0.1e1 / t337
  t735 = 0.1e1 / t348
  t744 = t337 * t334
  t748 = t358 ** 2
  t749 = 0.1e1 / t748
  t750 = f.my_piecewise3(t353, t729, 0)
  t751 = 0.1e1 / t357
  t752 = t751 * t354
  t754 = t752 * t750 + t750
  t756 = f.my_piecewise5(t328, 0.32e2 / 0.3e1 * t687 - 0.20e2 / 0.3e1 * t724 + t726 * t729 / 0.2e1 - 0.3e1 / 0.8e1 * t732 * t729 + 0.5e1 / 0.16e2 * t735 * t729, t345, t727 - t728 + t327 * t729 - t334 * t729 / 0.2e1 + 0.3e1 / 0.8e1 * t338 * t729 - 0.5e1 / 0.16e2 * t744 * t729, -t749 * t754)
  t757 = t756 * t367
  t758 = t757 * t308
  t760 = t365 ** 2
  t761 = 0.1e1 / t760
  t762 = t362 * t761
  t763 = t315 * t762
  t764 = t308 * t120
  t765 = t68 * t756
  t766 = t764 * t765
  t769 = t315 * t362
  t770 = t367 * t307
  t771 = t770 * t707
  t774 = -0.4e1 / 0.3e1 * t683 * t687 * params.a1 + 0.2e1 * t693 * t687 * params.b1 - 0.8e1 / 0.3e1 * t292 * t300 * t698 + t718 * t369 + t720 * t758 - 0.3e1 * t763 * t766 + 0.2e1 * t769 * t771
  t776 = t376 ** 2
  t777 = 0.1e1 / t776
  t779 = t371 * t777 * t135
  t780 = t261 * t703
  t783 = t774 * t377 + 0.54e2 * t779 * t780
  t784 = t680 * t783
  t788 = f.my_piecewise3(t272, 0, -0.3e1 / 0.8e1 * t5 * t673 * t30 * t379 - t388 - 0.3e1 / 0.16e2 * t678 * t784)
  t792 = 0.2e1 * t399
  t793 = f.my_piecewise5(t10, 0, t14, 0, t792)
  t797 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t393 * t659 * t26 + 0.4e1 / 0.3e1 * t21 * t793)
  t804 = t5 * t662 * t154 * t145
  t812 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t797 * t30 * t145 - t804 / 0.8e1 - 0.3e1 / 0.16e2 * t5 * t662 * t266 - t413 / 0.8e1 + t423 - t426 / 0.16e2)
  t816 = f.my_piecewise5(t14, 0, t10, 0, -t792)
  t820 = f.my_piecewise3(t275, 0, 0.4e1 / 0.9e1 * t632 * t670 * t278 + 0.4e1 / 0.3e1 * t276 * t816)
  t827 = t5 * t673 * t154 * t379
  t835 = t678 * t154 * t679 * t783
  t838 = f.my_piecewise3(t272, 0, -0.3e1 / 0.8e1 * t5 * t820 * t30 * t379 - t827 / 0.8e1 - t648 / 0.8e1 + t653 - 0.3e1 / 0.16e2 * t5 * t281 * t784 - t835 / 0.16e2)
  d12 = t270 + t390 + t668 + t788 + t6 * (t812 + t838)
  t843 = t659 ** 2
  t847 = 0.2e1 * t23 + 0.2e1 * t399
  t848 = f.my_piecewise5(t10, 0, t14, 0, t847)
  t852 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t393 * t843 + 0.4e1 / 0.3e1 * t21 * t848)
  t859 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t852 * t30 * t145 - t804 / 0.4e1 + t423)
  t860 = t670 ** 2
  t864 = f.my_piecewise5(t14, 0, t10, 0, -t847)
  t868 = f.my_piecewise3(t275, 0, 0.4e1 / 0.9e1 * t632 * t860 + 0.4e1 / 0.3e1 * t276 * t864)
  t881 = t783 ** 2
  t885 = t707 ** 2
  t895 = 0.1e1 / t286 / t317
  t896 = s2 * t895
  t900 = 0.88e2 / 0.9e1 * t896 - 0.40e2 / 0.9e1 * l1 * t698
  t904 = t311 ** 2
  t909 = 0.1e1 / t285 / t317 / t323
  t924 = t756 ** 2
  t938 = t316 * t909
  t940 = t322 * t320
  t942 = t729 ** 2
  t944 = 0.304e3 / 0.9e1 * t938
  t945 = 0.130e3 / 0.9e1 * t940
  t946 = t944 - t945
  t975 = t754 ** 2
  t978 = f.my_piecewise3(t353, t946, 0)
  t982 = t750 ** 2
  t989 = f.my_piecewise5(t328, -0.608e3 / 0.9e1 * t938 + 0.260e3 / 0.9e1 * t940 - t335 * t942 + t726 * t946 / 0.2e1 + 0.3e1 / 0.2e1 * t339 * t942 - 0.3e1 / 0.8e1 * t732 * t946 - 0.15e2 / 0.8e1 / t744 * t942 + 0.5e1 / 0.16e2 * t735 * t946, t345, -t944 + t945 + t942 + t327 * t946 - 0.3e1 / 0.2e1 * t333 * t942 - t334 * t946 / 0.2e1 + 0.15e2 / 0.8e1 * t337 * t942 + 0.3e1 / 0.8e1 * t338 * t946 - 0.35e2 / 0.16e2 * t348 * t942 - 0.5e1 / 0.16e2 * t744 * t946, 0.2e1 / t748 / t358 * t975 - t749 * (t978 - 0.1e1 / t357 / t356 * t355 * t982 + t751 * t982 + t752 * t978))
  t1004 = t317 ** 2
  t1007 = t316 * s2 / t1004 / t284
  t1011 = t295 ** 2
  t1049 = params.b * (0.2e1 * params.a2 * t885 * t312 + 0.64e2 / 0.3e1 * t702 * t712 * t707 * s2 * t698 + 0.2e1 * t702 * t312 * t900 + 0.128e3 / 0.3e1 * t309 / t904 * t316 * t909 - 0.176e3 / 0.9e1 * t309 * t713 * t895) * t369 + 0.12e2 * t315 * t362 / t760 / t364 * t308 * t586 * t588 * t924 + 0.88e2 / 0.9e1 * t292 * t300 * t895 + 0.4e1 * t718 * t362 * t771 + 0.2e1 * t718 * t68 * t758 + t720 * t989 * t367 * t308 + 0.2e1 * t315 * t368 * t885 + 0.2e1 * t769 * t770 * t900 - 0.16e2 / 0.9e1 * params.a / t291 / t290 * t299 * t1007 * t552 + 0.28e2 / 0.3e1 * t292 / t298 / t1011 * t1007 * t560 + 0.12e2 * t683 * t938 * params.a1 - 0.16e2 / 0.3e1 * t682 * t692 * t1007 * t571 - 0.18e2 * t693 * t938 * params.b1 + 0.4e1 * t720 * t757 * t307 * t707 - 0.6e1 * t718 * t762 * t766 - 0.3e1 * t763 * t764 * t68 * t989 - 0.6e1 * t315 * t588 * t924 * t761 * t764 - 0.12e2 * t763 * t307 * t120 * t765 * t707
  t1070 = f.my_piecewise3(t272, 0, -0.3e1 / 0.8e1 * t5 * t868 * t30 * t379 - t827 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t673 * t784 + t653 - t835 / 0.8e1 + 0.3e1 / 0.32e2 * t678 * t30 / t379 / t378 * t881 - 0.3e1 / 0.16e2 * t678 * t680 * (t1049 * t377 + 0.108e3 * t774 * t777 * t135 * t780 + 0.17496e5 * t371 / t776 / t376 * t614 * t618 * t938 - 0.198e3 * t779 * t261 * t896))
  d22 = 0.2e1 * t668 + 0.2e1 * t788 + t6 * (t859 + t1070)
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
  t45 = r0 ** 2
  t46 = r0 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t49 = 0.1e1 / t47 / t45
  t51 = params.a1 * s0 * t49 + 0.1e1
  t52 = jnp.sqrt(t51)
  t53 = params.a * t52
  t56 = params.b1 * s0 * t49 + 0.1e1
  t57 = t56 ** (0.1e1 / 0.4e1)
  t58 = t57 ** 2
  t59 = t58 * t57
  t60 = 0.1e1 / t59
  t61 = t60 * s0
  t64 = s0 * t49
  t68 = t64 - l0 / t47 / r0
  t69 = t68 ** 2
  t70 = params.a2 * t69
  t71 = 0.1e1 + t64
  t72 = t71 ** 2
  t73 = 0.1e1 / t72
  t76 = params.b * (t70 * t73 + 0.1e1)
  t77 = params.b2 ** 2
  t79 = jnp.sqrt(t77 + 0.1e1)
  t80 = t79 - params.b2
  t81 = s0 ** 2
  t82 = t45 ** 2
  t83 = t82 * r0
  t85 = 0.1e1 / t46 / t83
  t86 = t81 * t85
  t87 = l0 ** 2
  t88 = t45 * r0
  t91 = t87 / t46 / t88
  t92 = t86 - t91 - params.b2
  t93 = DBL_EPSILON ** (0.1e1 / 0.4e1)
  t94 = 0.1e1 / t93
  t95 = t92 < -t94
  t98 = 0.2e1 * params.b2
  t101 = t92 ** 2
  t102 = t101 * t92
  t103 = 0.1e1 / t102
  t105 = t101 ** 2
  t106 = t105 * t92
  t107 = 0.1e1 / t106
  t112 = f.my_piecewise3(0.0e0 < t92, t92, -t92)
  t113 = t112 < t93
  t116 = t105 * t101
  t118 = t105 ** 2
  t121 = -t94 < t92
  t122 = f.my_piecewise3(t121, t92, -t94)
  t123 = t122 ** 2
  t124 = 0.1e1 + t123
  t125 = jnp.sqrt(t124)
  t126 = t122 + t125
  t128 = f.my_piecewise5(t95, -0.2e1 * t86 + 0.2e1 * t91 + t98 - 0.1e1 / t92 / 0.2e1 + t103 / 0.8e1 - t107 / 0.16e2, t113, 0.1e1 - t86 + t91 + params.b2 + t101 / 0.2e1 - t105 / 0.8e1 + t116 / 0.16e2 - 0.5e1 / 0.128e3 * t118, 0.1e1 / t126)
  t130 = t80 * t128 + 0.1e1
  t131 = 2 ** (0.1e1 / 0.3e1)
  t132 = t131 - 0.1e1
  t133 = t132 * t80
  t135 = t133 * t128 + 0.1e1
  t136 = t135 ** 2
  t138 = 0.1e1 / t136 / t135
  t139 = t130 * t138
  t140 = t139 * t69
  t142 = t53 * t61 * t49 + t76 * t140 + 0.1e1
  t143 = t2 ** 2
  t144 = 0.1e1 / jnp.pi
  t145 = t144 ** (0.1e1 / 0.3e1)
  t146 = t145 ** 2
  t147 = t143 * t146
  t148 = 4 ** (0.1e1 / 0.3e1)
  t149 = t147 * t148
  t154 = 0.1e1 + 0.81e2 / 0.4e1 * t149 * params.b * s0 * t49
  t155 = 0.1e1 / t154
  t156 = t142 * t155
  t157 = jnp.sqrt(t156)
  t163 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t164 = t42 ** 2
  t165 = 0.1e1 / t164
  t170 = t5 * t163
  t171 = 0.1e1 / t157
  t172 = t42 * t171
  t174 = params.a / t52
  t175 = t174 * t60
  t178 = 0.1e1 / t46 / t82 / t45
  t179 = t81 * t178
  t184 = 0.1e1 / t59 / t56
  t185 = t53 * t184
  t190 = 0.1e1 / t47 / t88
  t194 = params.a2 * t68
  t195 = s0 * t190
  t199 = -0.8e1 / 0.3e1 * t195 + 0.5e1 / 0.3e1 * l0 * t49
  t204 = 0.1e1 / t72 / t71
  t205 = t204 * s0
  t206 = t205 * t190
  t210 = params.b * (0.2e1 * t194 * t73 * t199 + 0.16e2 / 0.3e1 * t70 * t206)
  t212 = t76 * t80
  t216 = t87 / t46 / t82
  t218 = 0.1e1 / t101
  t219 = 0.16e2 / 0.3e1 * t179
  t220 = 0.10e2 / 0.3e1 * t216
  t221 = -t219 + t220
  t224 = 0.1e1 / t105
  t227 = 0.1e1 / t116
  t236 = t105 * t102
  t240 = t126 ** 2
  t241 = 0.1e1 / t240
  t242 = f.my_piecewise3(t121, t221, 0)
  t243 = 0.1e1 / t125
  t244 = t243 * t122
  t246 = t244 * t242 + t242
  t248 = f.my_piecewise5(t95, 0.32e2 / 0.3e1 * t179 - 0.20e2 / 0.3e1 * t216 + t218 * t221 / 0.2e1 - 0.3e1 / 0.8e1 * t224 * t221 + 0.5e1 / 0.16e2 * t227 * t221, t113, t219 - t220 + t92 * t221 - t102 * t221 / 0.2e1 + 0.3e1 / 0.8e1 * t106 * t221 - 0.5e1 / 0.16e2 * t236 * t221, -t241 * t246)
  t249 = t248 * t138
  t250 = t249 * t69
  t252 = t136 ** 2
  t253 = 0.1e1 / t252
  t254 = t130 * t253
  t255 = t76 * t254
  t256 = t69 * t132
  t257 = t80 * t248
  t258 = t256 * t257
  t261 = t76 * t130
  t262 = t138 * t68
  t263 = t262 * t199
  t266 = -0.4e1 / 0.3e1 * t175 * t179 * params.a1 + 0.2e1 * t185 * t179 * params.b1 - 0.8e1 / 0.3e1 * t53 * t61 * t190 + t210 * t140 + t212 * t250 - 0.3e1 * t255 * t258 + 0.2e1 * t261 * t263
  t268 = t154 ** 2
  t269 = 0.1e1 / t268
  t271 = t142 * t269 * t147
  t272 = t148 * params.b
  t273 = t272 * t195
  t276 = t266 * t155 + 0.54e2 * t271 * t273
  t277 = t172 * t276
  t280 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t281 = t280 * f.p.zeta_threshold
  t283 = f.my_piecewise3(t20, t281, t21 * t19)
  t285 = 0.1e1 / t164 / t6
  t290 = t5 * t283
  t291 = t165 * t171
  t292 = t291 * t276
  t296 = 0.1e1 / t157 / t156
  t297 = t42 * t296
  t298 = t276 ** 2
  t299 = t297 * t298
  t302 = t199 ** 2
  t303 = params.a2 * t302
  t306 = t194 * t204
  t307 = t199 * s0
  t312 = 0.1e1 / t47 / t82
  t313 = s0 * t312
  t317 = 0.88e2 / 0.9e1 * t313 - 0.40e2 / 0.9e1 * l0 * t190
  t318 = t73 * t317
  t321 = t72 ** 2
  t322 = 0.1e1 / t321
  t323 = t322 * t81
  t326 = 0.1e1 / t46 / t82 / t88
  t334 = params.b * (0.2e1 * t303 * t73 + 0.64e2 / 0.3e1 * t306 * t307 * t190 + 0.2e1 * t194 * t318 + 0.128e3 / 0.3e1 * t70 * t323 * t326 - 0.176e3 / 0.9e1 * t70 * t205 * t312)
  t336 = t210 * t254
  t339 = t81 * t326
  t341 = t87 * t85
  t343 = t221 ** 2
  t345 = 0.304e3 / 0.9e1 * t339
  t346 = 0.130e3 / 0.9e1 * t341
  t347 = t345 - t346
  t354 = 0.1e1 / t236
  t375 = 0.1e1 / t240 / t126
  t376 = t246 ** 2
  t379 = f.my_piecewise3(t121, t347, 0)
  t381 = 0.1e1 / t125 / t124
  t382 = t381 * t123
  t383 = t242 ** 2
  t387 = t243 * t383 + t244 * t379 - t382 * t383 + t379
  t390 = f.my_piecewise5(t95, -0.608e3 / 0.9e1 * t339 + 0.260e3 / 0.9e1 * t341 - t103 * t343 + t218 * t347 / 0.2e1 + 0.3e1 / 0.2e1 * t107 * t343 - 0.3e1 / 0.8e1 * t224 * t347 - 0.15e2 / 0.8e1 * t354 * t343 + 0.5e1 / 0.16e2 * t227 * t347, t113, -t345 + t346 + t343 + t92 * t347 - 0.3e1 / 0.2e1 * t101 * t343 - t102 * t347 / 0.2e1 + 0.15e2 / 0.8e1 * t105 * t343 + 0.3e1 / 0.8e1 * t106 * t347 - 0.35e2 / 0.16e2 * t116 * t343 - 0.5e1 / 0.16e2 * t236 * t347, -t241 * t387 + 0.2e1 * t375 * t376)
  t391 = t80 * t390
  t392 = t256 * t391
  t395 = t139 * t302
  t398 = t262 * t317
  t403 = params.a / t52 / t51
  t404 = t403 * t60
  t405 = t81 * s0
  t406 = t82 ** 2
  t409 = t405 / t406 / t45
  t410 = params.a1 ** 2
  t414 = t56 ** 2
  t416 = 0.1e1 / t59 / t414
  t417 = t53 * t416
  t418 = params.b1 ** 2
  t425 = t210 * t130
  t428 = t210 * t80
  t431 = t390 * t138
  t432 = t431 * t69
  t434 = t68 * t199
  t435 = t249 * t434
  t441 = t174 * t184
  t442 = params.a1 * params.b1
  t450 = 0.1e1 / t252 / t135
  t451 = t130 * t450
  t452 = t76 * t451
  t453 = t132 ** 2
  t454 = t69 * t453
  t455 = t80 ** 2
  t456 = t248 ** 2
  t457 = t455 * t456
  t458 = t454 * t457
  t463 = t456 * t253 * t256
  t466 = t68 * t132
  t468 = t466 * t257 * t199
  t471 = t334 * t140 - 0.6e1 * t336 * t258 - 0.3e1 * t255 * t392 + 0.2e1 * t76 * t395 + 0.2e1 * t261 * t398 - 0.16e2 / 0.9e1 * t404 * t409 * t410 + 0.28e2 / 0.3e1 * t417 * t409 * t418 + 0.88e2 / 0.9e1 * t53 * t61 * t312 + 0.4e1 * t425 * t263 + 0.2e1 * t428 * t250 + t212 * t432 + 0.4e1 * t212 * t435 + 0.12e2 * t175 * t339 * params.a1 - 0.16e2 / 0.3e1 * t441 * t409 * t442 - 0.18e2 * t185 * t339 * params.b1 + 0.12e2 * t452 * t458 - 0.6e1 * t76 * t455 * t463 - 0.12e2 * t255 * t468
  t474 = t266 * t269 * t147
  t478 = 0.1e1 / t268 / t154
  t481 = t2 * t145 * t144
  t482 = t142 * t478 * t481
  t483 = t148 ** 2
  t484 = params.b ** 2
  t485 = t483 * t484
  t486 = t485 * t339
  t489 = t272 * t313
  t492 = t471 * t155 - 0.198e3 * t271 * t489 + 0.108e3 * t474 * t273 + 0.17496e5 * t482 * t486
  t493 = t172 * t492
  t497 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t157 - t5 * t163 * t165 * t157 / 0.4e1 - 0.3e1 / 0.8e1 * t170 * t277 + t5 * t283 * t285 * t157 / 0.12e2 - t290 * t292 / 0.8e1 + 0.3e1 / 0.32e2 * t290 * t299 - 0.3e1 / 0.16e2 * t290 * t493)
  t499 = r1 <= f.p.dens_threshold
  t500 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t501 = 0.1e1 + t500
  t502 = t501 <= f.p.zeta_threshold
  t503 = t501 ** (0.1e1 / 0.3e1)
  t504 = t503 ** 2
  t505 = 0.1e1 / t504
  t507 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t508 = t507 ** 2
  t512 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t516 = f.my_piecewise3(t502, 0, 0.4e1 / 0.9e1 * t505 * t508 + 0.4e1 / 0.3e1 * t503 * t512)
  t519 = r1 ** 2
  t520 = r1 ** (0.1e1 / 0.3e1)
  t521 = t520 ** 2
  t523 = 0.1e1 / t521 / t519
  t526 = jnp.sqrt(params.a1 * s2 * t523 + 0.1e1)
  t531 = (params.b1 * s2 * t523 + 0.1e1) ** (0.1e1 / 0.4e1)
  t532 = t531 ** 2
  t538 = s2 * t523
  t543 = (t538 - l1 / t521 / r1) ** 2
  t546 = (0.1e1 + t538) ** 2
  t551 = s2 ** 2
  t552 = t519 ** 2
  t556 = t551 / t520 / t552 / r1
  t557 = l1 ** 2
  t561 = t557 / t520 / t519 / r1
  t562 = t556 - t561 - params.b2
  t568 = t562 ** 2
  t572 = t568 ** 2
  t579 = f.my_piecewise3(0.0e0 < t562, t562, -t562)
  t585 = t572 ** 2
  t589 = f.my_piecewise3(-t94 < t562, t562, -t94)
  t590 = t589 ** 2
  t592 = jnp.sqrt(0.1e1 + t590)
  t595 = f.my_piecewise5(t562 < -t94, -0.2e1 * t556 + 0.2e1 * t561 + t98 - 0.1e1 / t562 / 0.2e1 + 0.1e1 / t568 / t562 / 0.8e1 - 0.1e1 / t572 / t562 / 0.16e2, t579 < t93, 0.1e1 - t556 + t561 + params.b2 + t568 / 0.2e1 - t572 / 0.8e1 + t572 * t568 / 0.16e2 - 0.5e1 / 0.128e3 * t585, 0.1e1 / (t589 + t592))
  t599 = t133 * t595 + 0.1e1
  t600 = t599 ** 2
  t614 = jnp.sqrt((0.1e1 + params.a * t526 / t532 / t531 * s2 * t523 + params.b * (0.1e1 + params.a2 * t543 / t546) * (t80 * t595 + 0.1e1) / t600 / t599 * t543) / (0.1e1 + 0.81e2 / 0.4e1 * t149 * params.b * s2 * t523))
  t620 = f.my_piecewise3(t502, 0, 0.4e1 / 0.3e1 * t503 * t507)
  t626 = f.my_piecewise3(t502, t281, t503 * t501)
  t632 = f.my_piecewise3(t499, 0, -0.3e1 / 0.8e1 * t5 * t516 * t42 * t614 - t5 * t620 * t165 * t614 / 0.4e1 + t5 * t626 * t285 * t614 / 0.12e2)
  t642 = t24 ** 2
  t646 = 0.6e1 * t33 - 0.6e1 * t16 / t642
  t647 = f.my_piecewise5(t10, 0, t14, 0, t646)
  t651 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t647)
  t672 = 0.1e1 / t164 / t24
  t687 = t455 * t80
  t689 = t456 * t248
  t695 = t81 ** 2
  t699 = t695 / t47 / t406 / t83
  t715 = 0.1e1 / t406 / t88
  t716 = t405 * t715
  t720 = t68 * t317
  t742 = 0.1e1 / t47 / t83
  t743 = s0 * t742
  t747 = -0.1232e4 / 0.27e2 * t743 + 0.440e3 / 0.27e2 * l0 * t312
  t758 = 0.1e1 / t46 / t406
  t776 = t51 ** 2
  t793 = t81 * t758
  t808 = -0.18e2 * t210 * t455 * t463 + 0.36e2 * t76 * t687 * t689 * t450 * t454 - 0.32e2 / 0.3e1 * t403 * t184 * t699 * t410 * params.b1 - 0.112e3 / 0.3e1 * t174 * t416 * t699 * t418 * params.a1 + 0.12e2 * t428 * t435 + 0.6e1 * t212 * t431 * t434 + 0.304e3 / 0.3e1 * t441 * t716 * t442 + 0.6e1 * t212 * t249 * t720 + params.b * (0.6e1 * params.a2 * t199 * t318 + 0.32e2 * t303 * t206 + 0.256e3 * t194 * t322 * t199 * t81 * t326 + 0.32e2 * t306 * t317 * s0 * t190 - 0.352e3 / 0.3e1 * t306 * t307 * t312 + 0.2e1 * t194 * t73 * t747 + 0.4096e4 / 0.9e1 * t70 / t321 / t71 * t405 * t715 - 0.1408e4 / 0.3e1 * t70 * t323 * t758 + 0.2464e4 / 0.27e2 * t70 * t205 * t742) * t140 + 0.6e1 * t210 * t395 - 0.1232e4 / 0.27e2 * t53 * t61 * t742 + 0.2e1 * t261 * t262 * t747 - 0.64e2 / 0.9e1 * params.a / t52 / t776 * t60 * t699 * t410 * params.a1 + 0.616e3 / 0.9e1 * t53 / t59 / t414 / t56 * t699 * t418 * params.b1 - 0.2728e4 / 0.27e2 * t175 * t793 * params.a1 + 0.304e3 / 0.9e1 * t404 * t716 * t410 - 0.532e3 / 0.3e1 * t417 * t716 * t418 + 0.1364e4 / 0.9e1 * t185 * t793 * params.b1 + 0.3e1 * t428 * t432
  t810 = t87 * t178
  t812 = t343 * t221
  t818 = 0.6688e4 / 0.27e2 * t793
  t819 = 0.2080e4 / 0.27e2 * t810
  t820 = -t818 + t819
  t838 = 0.13376e5 / 0.27e2 * t793 - 0.4160e4 / 0.27e2 * t810 + 0.3e1 * t224 * t812 - 0.3e1 * t103 * t221 * t347 + t218 * t820 / 0.2e1 - 0.15e2 / 0.2e1 * t227 * t812 + 0.9e1 / 0.2e1 * t107 * t221 * t347 - 0.3e1 / 0.8e1 * t224 * t820 + 0.105e3 / 0.8e1 / t118 * t812 - 0.45e2 / 0.8e1 * t354 * t221 * t347 + 0.5e1 / 0.16e2 * t227 * t820
  t863 = t818 - t819 + 0.3e1 * t221 * t347 + t92 * t820 - 0.3e1 * t92 * t812 - 0.9e1 / 0.2e1 * t101 * t221 * t347 - t102 * t820 / 0.2e1 + 0.15e2 / 0.2e1 * t102 * t812 + 0.45e2 / 0.8e1 * t105 * t221 * t347 + 0.3e1 / 0.8e1 * t106 * t820 - 0.105e3 / 0.8e1 * t106 * t812 - 0.105e3 / 0.16e2 * t116 * t221 * t347 - 0.5e1 / 0.16e2 * t236 * t820
  t864 = t240 ** 2
  t872 = f.my_piecewise3(t121, t820, 0)
  t873 = t124 ** 2
  t878 = t383 * t242
  t894 = f.my_piecewise5(t95, t838, t113, t863, -0.6e1 / t864 * t376 * t246 + 0.6e1 * t375 * t246 * t387 - t241 * (t872 + 0.3e1 / t125 / t873 * t123 * t122 * t878 - 0.3e1 * t381 * t122 * t878 - 0.3e1 * t382 * t242 * t379 + 0.3e1 * t243 * t242 * t379 + t244 * t872))
  t972 = t212 * t894 * t138 * t69 + 0.6e1 * t334 * t130 * t263 + 0.3e1 * t334 * t80 * t250 + 0.6e1 * t261 * t138 * t199 * t317 + 0.6e1 * t212 * t249 * t302 + 0.6e1 * t425 * t398 + 0.36e2 * t452 * t454 * t455 * t390 * t248 - 0.36e2 * t336 * t468 - 0.18e2 * t255 * t466 * t391 * t199 - 0.18e2 * t255 * t720 * t133 * t248 + 0.72e2 * t452 * t68 * t453 * t457 * t199 - 0.36e2 * t76 * t457 * t253 * t68 * t199 * t132 + 0.36e2 * t210 * t451 * t458 - 0.60e2 * t76 * t130 / t252 / t136 * t69 * t453 * t132 * t687 * t689 - 0.9e1 * t334 * t254 * t258 - 0.9e1 * t336 * t392 - 0.3e1 * t255 * t256 * t80 * t894 - 0.18e2 * t255 * t302 * t132 * t257 - 0.18e2 * t76 * t455 * t248 * t253 * t69 * t132 * t390
  t985 = t268 ** 2
  t988 = jnp.pi ** 2
  t1006 = t142 ** 2
  t1025 = -0.3e1 / 0.8e1 * t5 * t651 * t42 * t157 - 0.3e1 / 0.8e1 * t5 * t41 * t165 * t157 - 0.9e1 / 0.16e2 * t5 * t41 * t277 + t5 * t163 * t285 * t157 / 0.4e1 - 0.3e1 / 0.8e1 * t170 * t292 - 0.9e1 / 0.16e2 * t170 * t493 - 0.5e1 / 0.36e2 * t5 * t283 * t672 * t157 + t290 * t285 * t171 * t276 / 0.8e1 - 0.3e1 / 0.16e2 * t290 * t291 * t492 - 0.3e1 / 0.16e2 * t290 * t172 * ((t808 + t972) * t155 + 0.162e3 * t471 * t269 * t147 * t273 + 0.52488e5 * t266 * t478 * t481 * t486 - 0.594e3 * t474 * t489 + 0.34012224e8 * t142 / t985 / t988 * t484 * params.b * t405 * t715 - 0.192456e6 * t482 * t485 * t793 + 0.924e3 * t271 * t272 * t743) - 0.9e1 / 0.64e2 * t290 * t42 / t157 / t1006 / t269 * t298 * t276 + 0.9e1 / 0.32e2 * t290 * t297 * t276 * t492 + 0.9e1 / 0.32e2 * t170 * t299 + 0.3e1 / 0.32e2 * t290 * t165 * t296 * t298
  t1026 = f.my_piecewise3(t1, 0, t1025)
  t1036 = f.my_piecewise5(t14, 0, t10, 0, -t646)
  t1040 = f.my_piecewise3(t502, 0, -0.8e1 / 0.27e2 / t504 / t501 * t508 * t507 + 0.4e1 / 0.3e1 * t505 * t507 * t512 + 0.4e1 / 0.3e1 * t503 * t1036)
  t1058 = f.my_piecewise3(t499, 0, -0.3e1 / 0.8e1 * t5 * t1040 * t42 * t614 - 0.3e1 / 0.8e1 * t5 * t516 * t165 * t614 + t5 * t620 * t285 * t614 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t626 * t672 * t614)
  d111 = 0.3e1 * t497 + 0.3e1 * t632 + t6 * (t1026 + t1058)

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
  t57 = r0 ** 2
  t58 = r0 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t61 = 0.1e1 / t59 / t57
  t63 = params.a1 * s0 * t61 + 0.1e1
  t64 = jnp.sqrt(t63)
  t65 = params.a * t64
  t68 = params.b1 * s0 * t61 + 0.1e1
  t69 = t68 ** (0.1e1 / 0.4e1)
  t70 = t69 ** 2
  t71 = t70 * t69
  t72 = 0.1e1 / t71
  t73 = t72 * s0
  t76 = s0 * t61
  t80 = t76 - l0 / t59 / r0
  t81 = t80 ** 2
  t82 = params.a2 * t81
  t83 = 0.1e1 + t76
  t84 = t83 ** 2
  t85 = 0.1e1 / t84
  t88 = params.b * (t82 * t85 + 0.1e1)
  t89 = params.b2 ** 2
  t91 = jnp.sqrt(t89 + 0.1e1)
  t92 = t91 - params.b2
  t93 = s0 ** 2
  t94 = t57 ** 2
  t95 = t94 * r0
  t97 = 0.1e1 / t58 / t95
  t98 = t93 * t97
  t99 = l0 ** 2
  t100 = t57 * r0
  t103 = t99 / t58 / t100
  t104 = t98 - t103 - params.b2
  t105 = DBL_EPSILON ** (0.1e1 / 0.4e1)
  t106 = 0.1e1 / t105
  t107 = t104 < -t106
  t110 = 0.2e1 * params.b2
  t113 = t104 ** 2
  t114 = t113 * t104
  t115 = 0.1e1 / t114
  t117 = t113 ** 2
  t118 = t117 * t104
  t119 = 0.1e1 / t118
  t124 = f.my_piecewise3(0.0e0 < t104, t104, -t104)
  t125 = t124 < t105
  t128 = t117 * t113
  t130 = t117 ** 2
  t133 = -t106 < t104
  t134 = f.my_piecewise3(t133, t104, -t106)
  t135 = t134 ** 2
  t136 = 0.1e1 + t135
  t137 = jnp.sqrt(t136)
  t138 = t134 + t137
  t140 = f.my_piecewise5(t107, -0.2e1 * t98 + 0.2e1 * t103 + t110 - 0.1e1 / t104 / 0.2e1 + t115 / 0.8e1 - t119 / 0.16e2, t125, 0.1e1 - t98 + t103 + params.b2 + t113 / 0.2e1 - t117 / 0.8e1 + t128 / 0.16e2 - 0.5e1 / 0.128e3 * t130, 0.1e1 / t138)
  t142 = t92 * t140 + 0.1e1
  t143 = 2 ** (0.1e1 / 0.3e1)
  t144 = t143 - 0.1e1
  t145 = t144 * t92
  t147 = t145 * t140 + 0.1e1
  t148 = t147 ** 2
  t149 = t148 * t147
  t150 = 0.1e1 / t149
  t151 = t142 * t150
  t152 = t151 * t81
  t154 = t65 * t73 * t61 + t88 * t152 + 0.1e1
  t155 = t2 ** 2
  t156 = 0.1e1 / jnp.pi
  t157 = t156 ** (0.1e1 / 0.3e1)
  t158 = t157 ** 2
  t159 = t155 * t158
  t160 = 4 ** (0.1e1 / 0.3e1)
  t161 = t159 * t160
  t166 = 0.1e1 + 0.81e2 / 0.4e1 * t161 * params.b * s0 * t61
  t167 = 0.1e1 / t166
  t168 = t154 * t167
  t169 = jnp.sqrt(t168)
  t178 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t179 = t54 ** 2
  t180 = 0.1e1 / t179
  t185 = t5 * t178
  t186 = 0.1e1 / t169
  t187 = t54 * t186
  t189 = params.a / t64
  t190 = t189 * t72
  t191 = t94 * t57
  t193 = 0.1e1 / t58 / t191
  t194 = t93 * t193
  t199 = 0.1e1 / t71 / t68
  t200 = t65 * t199
  t205 = 0.1e1 / t59 / t100
  t209 = params.a2 * t80
  t210 = s0 * t205
  t214 = -0.8e1 / 0.3e1 * t210 + 0.5e1 / 0.3e1 * l0 * t61
  t219 = 0.1e1 / t84 / t83
  t220 = t219 * s0
  t221 = t220 * t205
  t225 = params.b * (0.2e1 * t209 * t85 * t214 + 0.16e2 / 0.3e1 * t82 * t221)
  t227 = t88 * t92
  t231 = t99 / t58 / t94
  t233 = 0.1e1 / t113
  t234 = 0.16e2 / 0.3e1 * t194
  t235 = 0.10e2 / 0.3e1 * t231
  t236 = -t234 + t235
  t239 = 0.1e1 / t117
  t242 = 0.1e1 / t128
  t251 = t117 * t114
  t255 = t138 ** 2
  t256 = 0.1e1 / t255
  t257 = f.my_piecewise3(t133, t236, 0)
  t258 = 0.1e1 / t137
  t259 = t258 * t134
  t261 = t259 * t257 + t257
  t263 = f.my_piecewise5(t107, 0.32e2 / 0.3e1 * t194 - 0.20e2 / 0.3e1 * t231 + t233 * t236 / 0.2e1 - 0.3e1 / 0.8e1 * t239 * t236 + 0.5e1 / 0.16e2 * t242 * t236, t125, t234 - t235 + t104 * t236 - t114 * t236 / 0.2e1 + 0.3e1 / 0.8e1 * t118 * t236 - 0.5e1 / 0.16e2 * t251 * t236, -t256 * t261)
  t264 = t263 * t150
  t265 = t264 * t81
  t267 = t148 ** 2
  t268 = 0.1e1 / t267
  t269 = t142 * t268
  t270 = t88 * t269
  t271 = t81 * t144
  t272 = t92 * t263
  t273 = t271 * t272
  t276 = t88 * t142
  t277 = t150 * t80
  t278 = t277 * t214
  t281 = -0.4e1 / 0.3e1 * t190 * t194 * params.a1 + 0.2e1 * t200 * t194 * params.b1 - 0.8e1 / 0.3e1 * t65 * t73 * t205 + t225 * t152 + t227 * t265 - 0.3e1 * t270 * t273 + 0.2e1 * t276 * t278
  t283 = t166 ** 2
  t284 = 0.1e1 / t283
  t286 = t154 * t284 * t159
  t287 = t160 * params.b
  t288 = t287 * t210
  t291 = t281 * t167 + 0.54e2 * t286 * t288
  t292 = t187 * t291
  t297 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t299 = 0.1e1 / t179 / t6
  t304 = t5 * t297
  t305 = t180 * t186
  t306 = t305 * t291
  t309 = t214 ** 2
  t310 = params.a2 * t309
  t313 = t209 * t219
  t314 = t214 * s0
  t319 = 0.1e1 / t59 / t94
  t320 = s0 * t319
  t324 = 0.88e2 / 0.9e1 * t320 - 0.40e2 / 0.9e1 * l0 * t205
  t325 = t85 * t324
  t328 = t84 ** 2
  t329 = 0.1e1 / t328
  t330 = t329 * t93
  t333 = 0.1e1 / t58 / t94 / t100
  t334 = t330 * t333
  t337 = t220 * t319
  t341 = params.b * (0.2e1 * t310 * t85 + 0.64e2 / 0.3e1 * t313 * t314 * t205 + 0.2e1 * t209 * t325 + 0.128e3 / 0.3e1 * t82 * t334 - 0.176e3 / 0.9e1 * t82 * t337)
  t343 = t225 * t269
  t346 = t93 * t333
  t348 = t99 * t97
  t350 = t236 ** 2
  t352 = 0.304e3 / 0.9e1 * t346
  t353 = 0.130e3 / 0.9e1 * t348
  t354 = t352 - t353
  t361 = 0.1e1 / t251
  t382 = 0.1e1 / t255 / t138
  t383 = t261 ** 2
  t386 = f.my_piecewise3(t133, t354, 0)
  t388 = 0.1e1 / t137 / t136
  t389 = t388 * t135
  t390 = t257 ** 2
  t394 = t258 * t390 + t259 * t386 - t389 * t390 + t386
  t397 = f.my_piecewise5(t107, -0.608e3 / 0.9e1 * t346 + 0.260e3 / 0.9e1 * t348 - t115 * t350 + t233 * t354 / 0.2e1 + 0.3e1 / 0.2e1 * t119 * t350 - 0.3e1 / 0.8e1 * t239 * t354 - 0.15e2 / 0.8e1 * t361 * t350 + 0.5e1 / 0.16e2 * t242 * t354, t125, -t352 + t353 + t350 + t104 * t354 - 0.3e1 / 0.2e1 * t113 * t350 - t114 * t354 / 0.2e1 + 0.15e2 / 0.8e1 * t117 * t350 + 0.3e1 / 0.8e1 * t118 * t354 - 0.35e2 / 0.16e2 * t128 * t350 - 0.5e1 / 0.16e2 * t251 * t354, -t256 * t394 + 0.2e1 * t382 * t383)
  t398 = t92 * t397
  t399 = t271 * t398
  t402 = t151 * t309
  t405 = t277 * t324
  t410 = params.a / t64 / t63
  t411 = t410 * t72
  t412 = t93 * s0
  t413 = t94 ** 2
  t416 = t412 / t413 / t57
  t417 = params.a1 ** 2
  t421 = t68 ** 2
  t423 = 0.1e1 / t71 / t421
  t424 = t65 * t423
  t425 = params.b1 ** 2
  t432 = t225 * t142
  t435 = t225 * t92
  t438 = t397 * t150
  t439 = t438 * t81
  t444 = t189 * t199
  t445 = params.a1 * params.b1
  t452 = t80 * t214
  t453 = t264 * t452
  t457 = 0.1e1 / t267 / t147
  t458 = t142 * t457
  t459 = t88 * t458
  t460 = t144 ** 2
  t461 = t81 * t460
  t462 = t92 ** 2
  t463 = t263 ** 2
  t464 = t462 * t463
  t465 = t461 * t464
  t468 = t88 * t462
  t469 = t463 * t268
  t470 = t469 * t271
  t473 = t80 * t144
  t475 = t473 * t272 * t214
  t478 = t341 * t152 - 0.6e1 * t343 * t273 - 0.3e1 * t270 * t399 + 0.2e1 * t88 * t402 + 0.2e1 * t276 * t405 - 0.16e2 / 0.9e1 * t411 * t416 * t417 + 0.28e2 / 0.3e1 * t424 * t416 * t425 + 0.88e2 / 0.9e1 * t65 * t73 * t319 + 0.4e1 * t432 * t278 + 0.2e1 * t435 * t265 + t227 * t439 + 0.12e2 * t190 * t346 * params.a1 - 0.16e2 / 0.3e1 * t444 * t416 * t445 - 0.18e2 * t200 * t346 * params.b1 + 0.4e1 * t227 * t453 + 0.12e2 * t459 * t465 - 0.6e1 * t468 * t470 - 0.12e2 * t270 * t475
  t481 = t281 * t284 * t159
  t485 = 0.1e1 / t283 / t166
  t488 = t2 * t157 * t156
  t489 = t154 * t485 * t488
  t490 = t160 ** 2
  t491 = params.b ** 2
  t492 = t490 * t491
  t493 = t492 * t346
  t496 = t287 * t320
  t499 = t478 * t167 - 0.198e3 * t286 * t496 + 0.108e3 * t481 * t288 + 0.17496e5 * t489 * t493
  t500 = t187 * t499
  t503 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t504 = t503 * f.p.zeta_threshold
  t506 = f.my_piecewise3(t20, t504, t21 * t19)
  t508 = 0.1e1 / t179 / t25
  t513 = t5 * t506
  t514 = t299 * t186
  t515 = t514 * t291
  t518 = t305 * t499
  t524 = 0.1e1 / t59 / t95
  t525 = s0 * t524
  t529 = -0.1232e4 / 0.27e2 * t525 + 0.440e3 / 0.27e2 * l0 * t319
  t530 = t277 * t529
  t533 = t63 ** 2
  t536 = params.a / t64 / t533
  t537 = t536 * t72
  t538 = t93 ** 2
  t542 = t538 / t59 / t413 / t95
  t543 = t417 * params.a1
  t549 = 0.1e1 / t71 / t421 / t68
  t550 = t65 * t549
  t551 = t425 * params.b1
  t556 = 0.1e1 / t413 / t100
  t557 = t412 * t556
  t565 = 0.1e1 / t58 / t413
  t566 = t93 * t565
  t576 = t99 * t193
  t578 = t350 * t236
  t581 = t115 * t236
  t584 = 0.6688e4 / 0.27e2 * t566
  t585 = 0.2080e4 / 0.27e2 * t576
  t586 = -t584 + t585
  t591 = t119 * t236
  t596 = 0.1e1 / t130
  t599 = t361 * t236
  t604 = 0.13376e5 / 0.27e2 * t566 - 0.4160e4 / 0.27e2 * t576 + 0.3e1 * t239 * t578 - 0.3e1 * t581 * t354 + t233 * t586 / 0.2e1 - 0.15e2 / 0.2e1 * t242 * t578 + 0.9e1 / 0.2e1 * t591 * t354 - 0.3e1 / 0.8e1 * t239 * t586 + 0.105e3 / 0.8e1 * t596 * t578 - 0.45e2 / 0.8e1 * t599 * t354 + 0.5e1 / 0.16e2 * t242 * t586
  t610 = t113 * t236
  t617 = t117 * t236
  t624 = t128 * t236
  t629 = t584 - t585 + 0.3e1 * t236 * t354 + t104 * t586 - 0.3e1 * t104 * t578 - 0.9e1 / 0.2e1 * t610 * t354 - t114 * t586 / 0.2e1 + 0.15e2 / 0.2e1 * t114 * t578 + 0.45e2 / 0.8e1 * t617 * t354 + 0.3e1 / 0.8e1 * t118 * t586 - 0.105e3 / 0.8e1 * t118 * t578 - 0.105e3 / 0.16e2 * t624 * t354 - 0.5e1 / 0.16e2 * t251 * t586
  t630 = t255 ** 2
  t631 = 0.1e1 / t630
  t635 = t382 * t261
  t638 = f.my_piecewise3(t133, t586, 0)
  t639 = t136 ** 2
  t641 = 0.1e1 / t137 / t639
  t643 = t641 * t135 * t134
  t644 = t390 * t257
  t647 = t388 * t134
  t653 = t258 * t257
  t657 = -0.3e1 * t389 * t257 * t386 + t259 * t638 + 0.3e1 * t653 * t386 + 0.3e1 * t643 * t644 - 0.3e1 * t647 * t644 + t638
  t660 = f.my_piecewise5(t107, t604, t125, t629, -0.6e1 * t631 * t383 * t261 - t256 * t657 + 0.6e1 * t635 * t394)
  t661 = t660 * t150
  t662 = t661 * t81
  t664 = t341 * t142
  t667 = t341 * t92
  t670 = t150 * t214
  t671 = t670 * t324
  t674 = t264 * t309
  t677 = params.a2 * t214
  t682 = t209 * t329
  t683 = t214 * t93
  t687 = t324 * s0
  t688 = t687 * t205
  t694 = t85 * t529
  t698 = 0.1e1 / t328 / t83
  t699 = t698 * t412
  t710 = params.b * (0.6e1 * t677 * t325 + 0.32e2 * t310 * t221 + 0.256e3 * t682 * t683 * t333 + 0.32e2 * t313 * t688 - 0.352e3 / 0.3e1 * t313 * t314 * t319 + 0.2e1 * t209 * t694 + 0.4096e4 / 0.9e1 * t82 * t699 * t556 - 0.1408e4 / 0.3e1 * t82 * t330 * t565 + 0.2464e4 / 0.27e2 * t82 * t220 * t524)
  t717 = t462 * t397
  t719 = t461 * t717 * t263
  t724 = 0.6e1 * t432 * t405 + 0.2e1 * t276 * t530 - 0.64e2 / 0.9e1 * t537 * t542 * t543 + 0.616e3 / 0.9e1 * t550 * t542 * t551 - 0.532e3 / 0.3e1 * t424 * t557 * t425 + 0.304e3 / 0.9e1 * t411 * t557 * t417 - 0.2728e4 / 0.27e2 * t190 * t566 * params.a1 + 0.1364e4 / 0.9e1 * t200 * t566 * params.b1 + 0.3e1 * t435 * t439 + t227 * t662 + 0.6e1 * t664 * t278 + 0.3e1 * t667 * t265 + 0.6e1 * t276 * t671 + 0.6e1 * t227 * t674 + t710 * t152 + 0.6e1 * t225 * t402 - 0.1232e4 / 0.27e2 * t65 * t73 * t524 + 0.36e2 * t459 * t719 - 0.36e2 * t343 * t475
  t726 = t473 * t398 * t214
  t729 = t80 * t324
  t730 = t145 * t263
  t731 = t729 * t730
  t736 = t80 * t460 * t464 * t214
  t739 = t462 * t92
  t741 = t463 * t263
  t743 = t741 * t457 * t461
  t746 = t410 * t199
  t747 = t417 * params.b1
  t751 = t189 * t423
  t752 = t425 * params.a1
  t758 = t438 * t452
  t764 = t264 * t729
  t770 = t309 * t144
  t771 = t770 * t272
  t774 = t341 * t269
  t779 = t92 * t660
  t780 = t271 * t779
  t785 = t268 * t81
  t790 = t88 * t464
  t791 = t268 * t80
  t792 = t214 * t144
  t793 = t791 * t792
  t796 = t225 * t458
  t800 = 0.1e1 / t267 / t148
  t801 = t142 * t800
  t802 = t88 * t801
  t803 = t460 * t144
  t804 = t81 * t803
  t805 = t739 * t741
  t806 = t804 * t805
  t809 = -0.18e2 * t270 * t726 - 0.18e2 * t270 * t731 + 0.72e2 * t459 * t736 + 0.36e2 * t88 * t739 * t743 - 0.32e2 / 0.3e1 * t746 * t542 * t747 - 0.112e3 / 0.3e1 * t751 * t542 * t752 + 0.12e2 * t435 * t453 + 0.6e1 * t227 * t758 + 0.304e3 / 0.3e1 * t444 * t557 * t445 + 0.6e1 * t227 * t764 - 0.18e2 * t225 * t462 * t470 - 0.18e2 * t270 * t771 - 0.9e1 * t774 * t273 - 0.9e1 * t343 * t399 - 0.3e1 * t270 * t780 - 0.18e2 * t88 * t462 * t263 * t785 * t144 * t397 - 0.36e2 * t790 * t793 + 0.36e2 * t796 * t465 - 0.60e2 * t802 * t806
  t810 = t724 + t809
  t813 = t478 * t284 * t159
  t817 = t281 * t485 * t488
  t822 = t283 ** 2
  t823 = 0.1e1 / t822
  t825 = jnp.pi ** 2
  t826 = 0.1e1 / t825
  t827 = t154 * t823 * t826
  t829 = t491 * params.b * t412
  t830 = t829 * t556
  t833 = t492 * t566
  t836 = t287 * t525
  t839 = t810 * t167 + 0.924e3 * t286 * t836 + 0.162e3 * t813 * t288 - 0.594e3 * t481 * t496 - 0.192456e6 * t489 * t833 + 0.52488e5 * t817 * t493 + 0.34012224e8 * t827 * t830
  t840 = t187 * t839
  t843 = t154 ** 2
  t846 = 0.1e1 / t169 / t843 / t284
  t847 = t54 * t846
  t848 = t291 ** 2
  t849 = t848 * t291
  t850 = t847 * t849
  t854 = 0.1e1 / t169 / t168
  t855 = t54 * t854
  t856 = t291 * t499
  t857 = t855 * t856
  t860 = t855 * t848
  t863 = t180 * t854
  t864 = t863 * t848
  t867 = -0.3e1 / 0.8e1 * t5 * t53 * t54 * t169 - 0.3e1 / 0.8e1 * t5 * t178 * t180 * t169 - 0.9e1 / 0.16e2 * t185 * t292 + t5 * t297 * t299 * t169 / 0.4e1 - 0.3e1 / 0.8e1 * t304 * t306 - 0.9e1 / 0.16e2 * t304 * t500 - 0.5e1 / 0.36e2 * t5 * t506 * t508 * t169 + t513 * t515 / 0.8e1 - 0.3e1 / 0.16e2 * t513 * t518 - 0.3e1 / 0.16e2 * t513 * t840 - 0.9e1 / 0.64e2 * t513 * t850 + 0.9e1 / 0.32e2 * t513 * t857 + 0.9e1 / 0.32e2 * t304 * t860 + 0.3e1 / 0.32e2 * t513 * t864
  t868 = f.my_piecewise3(t1, 0, t867)
  t870 = r1 <= f.p.dens_threshold
  t871 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t872 = 0.1e1 + t871
  t873 = t872 <= f.p.zeta_threshold
  t874 = t872 ** (0.1e1 / 0.3e1)
  t875 = t874 ** 2
  t877 = 0.1e1 / t875 / t872
  t879 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t880 = t879 ** 2
  t884 = 0.1e1 / t875
  t885 = t884 * t879
  t887 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t891 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t895 = f.my_piecewise3(t873, 0, -0.8e1 / 0.27e2 * t877 * t880 * t879 + 0.4e1 / 0.3e1 * t885 * t887 + 0.4e1 / 0.3e1 * t874 * t891)
  t898 = r1 ** 2
  t899 = r1 ** (0.1e1 / 0.3e1)
  t900 = t899 ** 2
  t902 = 0.1e1 / t900 / t898
  t905 = jnp.sqrt(params.a1 * s2 * t902 + 0.1e1)
  t910 = (params.b1 * s2 * t902 + 0.1e1) ** (0.1e1 / 0.4e1)
  t911 = t910 ** 2
  t917 = s2 * t902
  t922 = (t917 - l1 / t900 / r1) ** 2
  t925 = (0.1e1 + t917) ** 2
  t930 = s2 ** 2
  t931 = t898 ** 2
  t935 = t930 / t899 / t931 / r1
  t936 = l1 ** 2
  t940 = t936 / t899 / t898 / r1
  t941 = t935 - t940 - params.b2
  t947 = t941 ** 2
  t951 = t947 ** 2
  t958 = f.my_piecewise3(0.0e0 < t941, t941, -t941)
  t964 = t951 ** 2
  t968 = f.my_piecewise3(-t106 < t941, t941, -t106)
  t969 = t968 ** 2
  t971 = jnp.sqrt(0.1e1 + t969)
  t974 = f.my_piecewise5(t941 < -t106, -0.2e1 * t935 + 0.2e1 * t940 + t110 - 0.1e1 / t941 / 0.2e1 + 0.1e1 / t947 / t941 / 0.8e1 - 0.1e1 / t951 / t941 / 0.16e2, t958 < t105, 0.1e1 - t935 + t940 + params.b2 + t947 / 0.2e1 - t951 / 0.8e1 + t951 * t947 / 0.16e2 - 0.5e1 / 0.128e3 * t964, 0.1e1 / (t968 + t971))
  t978 = t145 * t974 + 0.1e1
  t979 = t978 ** 2
  t993 = jnp.sqrt((0.1e1 + params.a * t905 / t911 / t910 * s2 * t902 + params.b * (0.1e1 + params.a2 * t922 / t925) * (t92 * t974 + 0.1e1) / t979 / t978 * t922) / (0.1e1 + 0.81e2 / 0.4e1 * t161 * params.b * s2 * t902))
  t1002 = f.my_piecewise3(t873, 0, 0.4e1 / 0.9e1 * t884 * t880 + 0.4e1 / 0.3e1 * t874 * t887)
  t1009 = f.my_piecewise3(t873, 0, 0.4e1 / 0.3e1 * t874 * t879)
  t1015 = f.my_piecewise3(t873, t504, t874 * t872)
  t1021 = f.my_piecewise3(t870, 0, -0.3e1 / 0.8e1 * t5 * t895 * t54 * t993 - 0.3e1 / 0.8e1 * t5 * t1002 * t180 * t993 + t5 * t1009 * t299 * t993 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t1015 * t508 * t993)
  t1026 = t397 ** 2
  t1036 = t413 ** 2
  t1040 = t538 * s0 / t58 / t1036 / r0
  t1047 = 0.1e1 / t59 / t413 / t191
  t1048 = t538 * t1047
  t1053 = 0.1e1 / t413 / t94
  t1054 = t412 * t1053
  t1065 = t214 * t324
  t1071 = t80 * t529
  t1088 = t462 ** 2
  t1090 = t463 ** 2
  t1101 = 0.144e3 * t225 * t739 * t743 - 0.18e2 * t468 * t1026 * t268 * t271 + 0.12e2 * t227 * t438 * t729 - 0.896e3 / 0.9e1 * t410 * t423 * t1040 * t417 * t425 + 0.3136e4 / 0.9e1 * t746 * t1048 * t747 - 0.41008e5 / 0.27e2 * t444 * t1054 * t445 + 0.24e2 * t435 * t758 + 0.8e1 * t227 * t661 * t452 + 0.24e2 * t667 * t453 + 0.24e2 * t227 * t264 * t1065 + 0.24e2 * t435 * t764 + 0.8e1 * t227 * t264 * t1071 - 0.512e3 / 0.9e1 * t536 * t199 * t1040 * t543 * params.b1 - 0.9856e4 / 0.27e2 * t189 * t549 * t1040 * t551 * params.a1 + 0.10976e5 / 0.9e1 * t751 * t1048 * t752 - 0.240e3 * t88 * t1088 * t1090 * t800 * t804 - 0.36e2 * t341 * t462 * t470 - 0.72e2 * t468 * t469 * t770
  t1103 = 0.1e1 / t59 / t191
  t1109 = t324 ** 2
  t1118 = s0 * t1103
  t1122 = 0.20944e5 / 0.81e2 * t1118 - 0.6160e4 / 0.81e2 * l0 * t524
  t1131 = 0.1e1 / t58 / t413 / r0
  t1173 = 0.6e1 * params.a2 * t1109 * t85 + 0.8e1 * t677 * t694 + 0.2e1 * t209 * t85 * t1122 - 0.90112e5 / 0.9e1 * t82 * t699 * t1053 + 0.125312e6 / 0.27e2 * t82 * t330 * t1131 - 0.41888e5 / 0.81e2 * t82 * t220 * t1103 + 0.128e3 * t677 * t219 * t688 - 0.704e3 / 0.3e1 * t310 * t337 + 0.512e3 * t682 * t324 * t93 * t333 + 0.32768e5 / 0.9e1 * t209 * t698 * t214 * t412 * t556 + 0.128e3 / 0.3e1 * t313 * t529 * s0 * t205 - 0.11264e5 / 0.3e1 * t682 * t683 * t565 - 0.704e3 / 0.3e1 * t313 * t687 * t319 + 0.19712e5 / 0.27e2 * t313 * t314 * t524 + 0.512e3 * t310 * t334 + 0.163840e6 / 0.27e2 * t82 / t328 / t84 * t538 * t1047
  t1188 = t93 * t1131
  t1203 = t417 ** 2
  t1207 = t421 ** 2
  t1211 = t425 ** 2
  t1218 = t99 * t333
  t1220 = t350 ** 2
  t1226 = t354 ** 2
  t1231 = 0.167200e6 / 0.81e2 * t1188
  t1232 = 0.39520e5 / 0.81e2 * t1218
  t1233 = t1231 - t1232
  t1260 = -0.334400e6 / 0.81e2 * t1188 + 0.79040e5 / 0.81e2 * t1218 - 0.12e2 * t119 * t1220 + 0.18e2 * t239 * t350 * t354 - 0.3e1 * t115 * t1226 - 0.4e1 * t581 * t586 + t233 * t1233 / 0.2e1 + 0.45e2 * t361 * t1220 - 0.45e2 * t242 * t350 * t354 + 0.9e1 / 0.2e1 * t119 * t1226 + 0.6e1 * t591 * t586 - 0.3e1 / 0.8e1 * t239 * t1233 - 0.105e3 / t130 / t104 * t1220 + 0.315e3 / 0.4e1 * t596 * t350 * t354 - 0.45e2 / 0.8e1 * t361 * t1226 - 0.15e2 / 0.2e1 * t599 * t586 + 0.5e1 / 0.16e2 * t242 * t1233
  t1297 = -t1231 + t1232 + 0.3e1 * t1226 + 0.4e1 * t236 * t586 - 0.18e2 * t104 * t350 * t354 - 0.9e1 / 0.2e1 * t113 * t1226 - 0.6e1 * t610 * t586 + 0.45e2 / 0.2e1 * t113 * t1220 + 0.45e2 * t114 * t350 * t354 + 0.45e2 / 0.8e1 * t117 * t1226 + 0.15e2 / 0.2e1 * t617 * t586 - 0.525e3 / 0.8e1 * t117 * t1220 - 0.315e3 / 0.4e1 * t118 * t350 * t354 - 0.105e3 / 0.16e2 * t128 * t1226 - 0.35e2 / 0.4e1 * t624 * t586 + t104 * t1233 - 0.3e1 * t1220 - t114 * t1233 / 0.2e1 + 0.3e1 / 0.8e1 * t118 * t1233 - 0.5e1 / 0.16e2 * t251 * t1233
  t1300 = t383 ** 2
  t1306 = t394 ** 2
  t1311 = f.my_piecewise3(t133, t1233, 0)
  t1315 = t135 ** 2
  t1317 = t390 ** 2
  t1323 = t390 * t386
  t1330 = t386 ** 2
  t1341 = t1311 - 0.15e2 / t137 / t639 / t136 * t1315 * t1317 + 0.18e2 * t641 * t135 * t1317 + 0.18e2 * t643 * t1323 - 0.3e1 * t388 * t1317 - 0.18e2 * t647 * t1323 - 0.3e1 * t389 * t1330 - 0.4e1 * t389 * t257 * t638 + 0.3e1 * t258 * t1330 + 0.4e1 * t653 * t638 + t259 * t1311
  t1344 = f.my_piecewise5(t107, t1260, t125, t1297, 0.24e2 / t630 / t138 * t1300 - 0.36e2 * t631 * t383 * t394 + 0.6e1 * t382 * t1306 + 0.8e1 * t635 * t657 - t256 * t1341)
  t1358 = 0.20944e5 / 0.81e2 * t65 * t73 * t1103 + 0.12e2 * t341 * t402 + 0.6e1 * t88 * t151 * t1109 + params.b * t1173 * t152 + 0.6272e4 / 0.27e2 * t537 * t1048 * t543 - 0.60368e5 / 0.27e2 * t550 * t1048 * t551 + 0.71764e5 / 0.27e2 * t424 * t1054 * t425 - 0.41008e5 / 0.81e2 * t411 * t1054 * t417 + 0.24376e5 / 0.27e2 * t190 * t1188 * params.a1 - 0.12188e5 / 0.9e1 * t200 * t1188 * params.b1 + 0.2e1 * t276 * t277 * t1122 - 0.1280e4 / 0.27e2 * params.a / t64 / t533 / t63 * t72 * t1040 * t1203 + 0.6160e4 / 0.9e1 * t65 / t71 / t1207 * t1040 * t1211 + 0.4e1 * t435 * t662 + t227 * t1344 * t150 * t81 + 0.8e1 * t710 * t142 * t278 + 0.12e2 * t664 * t405 + 0.4e1 * t710 * t92 * t265 + 0.6e1 * t667 * t439
  t1378 = t785 * t144 * t263
  t1381 = t462 * t660
  t1385 = t739 * t463
  t1405 = t460 ** 2
  t1428 = 0.24e2 * t432 * t671 + 0.8e1 * t276 * t670 * t529 + 0.24e2 * t435 * t674 + 0.12e2 * t227 * t438 * t309 + 0.8e1 * t432 * t530 + 0.36e2 * t459 * t461 * t462 * t1026 - 0.72e2 * t225 * t717 * t1378 - 0.24e2 * t88 * t1381 * t1378 + 0.216e3 * t88 * t1385 * t457 * t81 * t460 * t397 + 0.288e3 * t88 * t805 * t457 * t80 * t214 * t460 - 0.240e3 * t225 * t801 * t806 + 0.360e3 * t88 * t142 / t267 / t149 * t81 * t1405 * t1088 * t1090 + 0.144e3 * t459 * t309 * t460 * t464 - 0.18e2 * t774 * t399 - 0.12e2 * t343 * t780 - 0.3e1 * t270 * t271 * t92 * t1344 - 0.12e2 * t710 * t269 * t273 - 0.72e2 * t343 * t771
  t1444 = t460 * t462
  t1496 = -0.72e2 * t790 * t791 * t324 * t144 - 0.144e3 * t225 * t464 * t793 + 0.72e2 * t341 * t458 * t465 - 0.36e2 * t270 * t770 * t398 + 0.288e3 * t88 * t458 * t80 * t1444 * t397 * t263 * t214 + 0.144e3 * t796 * t719 + 0.48e2 * t459 * t461 * t1381 * t263 + 0.144e3 * t459 * t729 * t1444 * t463 + 0.288e3 * t796 * t736 - 0.480e3 * t802 * t80 * t803 * t805 * t214 - 0.360e3 * t802 * t804 * t1385 * t397 - 0.72e2 * t774 * t475 - 0.72e2 * t270 * t1065 * t730 - 0.72e2 * t343 * t731 - 0.24e2 * t270 * t1071 * t730 - 0.72e2 * t343 * t726 - 0.24e2 * t270 * t473 * t779 * t214 - 0.36e2 * t270 * t473 * t398 * t324 - 0.144e3 * t88 * t717 * t791 * t792 * t263
  t1521 = t491 ** 2
  t1536 = (t1101 + t1358 + t1428 + t1496) * t167 + 0.216e3 * t810 * t284 * t159 * t288 + 0.104976e6 * t478 * t485 * t488 * t493 - 0.1188e4 * t813 * t496 + 0.136048896e9 * t281 * t823 * t826 * t830 - 0.769824e6 * t817 * t833 + 0.3696e4 * t481 * t836 + 0.7346640384e10 * t154 / t822 / t166 * t826 * t1521 * t1048 * t161 - 0.748268928e9 * t827 * t829 * t1053 + 0.1903176e7 * t489 * t492 * t1188 - 0.5236e4 * t286 * t287 * t1118
  t1552 = t848 ** 2
  t1577 = t499 ** 2
  t1583 = -0.3e1 / 0.16e2 * t513 * t187 * t1536 + t513 * t514 * t499 / 0.4e1 + 0.9e1 / 0.16e2 * t185 * t860 + 0.3e1 / 0.8e1 * t304 * t864 + 0.45e2 / 0.128e3 * t513 * t54 / t169 / t843 / t154 / t485 * t1552 - t513 * t299 * t854 * t848 / 0.8e1 - 0.3e1 / 0.16e2 * t513 * t180 * t846 * t849 - 0.5e1 / 0.18e2 * t513 * t508 * t186 * t291 + 0.3e1 / 0.8e1 * t513 * t863 * t856 + 0.3e1 / 0.8e1 * t513 * t855 * t839 * t291 + 0.9e1 / 0.8e1 * t304 * t857 + 0.9e1 / 0.32e2 * t513 * t855 * t1577 - 0.3e1 / 0.4e1 * t304 * t840
  t1603 = 0.1e1 / t179 / t36
  t1616 = t19 ** 2
  t1619 = t30 ** 2
  t1625 = t41 ** 2
  t1634 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t1635 = f.my_piecewise5(t10, 0, t14, 0, t1634)
  t1639 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t1616 * t1619 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t1625 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t1635)
  t1650 = -0.9e1 / 0.16e2 * t304 * t850 + t304 * t515 / 0.2e1 - 0.3e1 / 0.4e1 * t304 * t518 - 0.27e2 / 0.32e2 * t513 * t847 * t848 * t499 - 0.9e1 / 0.8e1 * t185 * t500 - 0.3e1 / 0.4e1 * t185 * t306 - 0.5e1 / 0.9e1 * t5 * t297 * t508 * t169 + 0.10e2 / 0.27e2 * t5 * t506 * t1603 * t169 - t5 * t53 * t180 * t169 / 0.2e1 + t5 * t178 * t299 * t169 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t1639 * t54 * t169 - t513 * t305 * t839 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t53 * t292
  t1652 = f.my_piecewise3(t1, 0, t1583 + t1650)
  t1653 = t872 ** 2
  t1656 = t880 ** 2
  t1662 = t887 ** 2
  t1668 = f.my_piecewise5(t14, 0, t10, 0, -t1634)
  t1672 = f.my_piecewise3(t873, 0, 0.40e2 / 0.81e2 / t875 / t1653 * t1656 - 0.16e2 / 0.9e1 * t877 * t880 * t887 + 0.4e1 / 0.3e1 * t884 * t1662 + 0.16e2 / 0.9e1 * t885 * t891 + 0.4e1 / 0.3e1 * t874 * t1668)
  t1694 = f.my_piecewise3(t870, 0, -0.3e1 / 0.8e1 * t5 * t1672 * t54 * t993 - t5 * t895 * t180 * t993 / 0.2e1 + t5 * t1002 * t299 * t993 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t1009 * t508 * t993 + 0.10e2 / 0.27e2 * t5 * t1015 * t1603 * t993)
  d1111 = 0.4e1 * t868 + 0.4e1 * t1021 + t6 * (t1652 + t1694)

  res = {'v4rho4': d1111}
  return res
