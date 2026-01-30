"""Generated from mgga_k_rda.mpl."""

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
  params_A0_raw = params.A0
  if isinstance(params_A0_raw, (str, bytes, dict)):
    params_A0 = params_A0_raw
  else:
    try:
      params_A0_seq = list(params_A0_raw)
    except TypeError:
      params_A0 = params_A0_raw
    else:
      params_A0_seq = np.asarray(params_A0_seq, dtype=np.float64)
      params_A0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A0_seq))
  params_A1_raw = params.A1
  if isinstance(params_A1_raw, (str, bytes, dict)):
    params_A1 = params_A1_raw
  else:
    try:
      params_A1_seq = list(params_A1_raw)
    except TypeError:
      params_A1 = params_A1_raw
    else:
      params_A1_seq = np.asarray(params_A1_seq, dtype=np.float64)
      params_A1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A1_seq))
  params_A2_raw = params.A2
  if isinstance(params_A2_raw, (str, bytes, dict)):
    params_A2 = params_A2_raw
  else:
    try:
      params_A2_seq = list(params_A2_raw)
    except TypeError:
      params_A2 = params_A2_raw
    else:
      params_A2_seq = np.asarray(params_A2_seq, dtype=np.float64)
      params_A2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A2_seq))
  params_A3_raw = params.A3
  if isinstance(params_A3_raw, (str, bytes, dict)):
    params_A3 = params_A3_raw
  else:
    try:
      params_A3_seq = list(params_A3_raw)
    except TypeError:
      params_A3 = params_A3_raw
    else:
      params_A3_seq = np.asarray(params_A3_seq, dtype=np.float64)
      params_A3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A3_seq))
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
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))
  params_beta3_raw = params.beta3
  if isinstance(params_beta3_raw, (str, bytes, dict)):
    params_beta3 = params_beta3_raw
  else:
    try:
      params_beta3_seq = list(params_beta3_raw)
    except TypeError:
      params_beta3 = params_beta3_raw
    else:
      params_beta3_seq = np.asarray(params_beta3_seq, dtype=np.float64)
      params_beta3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta3_seq))
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

  rda_s = lambda x: X2S * x

  rda_p = lambda u: jnp.zeros_like(u)

  rda_k4 = lambda s, p, b: jnp.sqrt(s ** 4 + b * p ** 2)

  rda_k2 = lambda s, p, b: s ** 2 + b * p

  rda_f0 = lambda s, p: 5 / 3 * s ** 2 + params_A0 + params_A1 * (rda_k4(s, p, params_a) / (1 + params_beta1 * rda_k4(s, p, params_a))) ** 2 + params_A2 * (rda_k4(s, p, params_b) / (1 + params_beta2 * rda_k4(s, p, params_b))) ** 4 + params_A3 * (rda_k2(s, p, params_c) / (1 + params_beta3 * rda_k2(s, p, params_c)))

  rda_f = lambda xs, us: rda_f0(rda_s(xs), rda_p(us))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, rda_f, rs, z, xs0, xs1, u0, u1)

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
  params_A0_raw = params.A0
  if isinstance(params_A0_raw, (str, bytes, dict)):
    params_A0 = params_A0_raw
  else:
    try:
      params_A0_seq = list(params_A0_raw)
    except TypeError:
      params_A0 = params_A0_raw
    else:
      params_A0_seq = np.asarray(params_A0_seq, dtype=np.float64)
      params_A0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A0_seq))
  params_A1_raw = params.A1
  if isinstance(params_A1_raw, (str, bytes, dict)):
    params_A1 = params_A1_raw
  else:
    try:
      params_A1_seq = list(params_A1_raw)
    except TypeError:
      params_A1 = params_A1_raw
    else:
      params_A1_seq = np.asarray(params_A1_seq, dtype=np.float64)
      params_A1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A1_seq))
  params_A2_raw = params.A2
  if isinstance(params_A2_raw, (str, bytes, dict)):
    params_A2 = params_A2_raw
  else:
    try:
      params_A2_seq = list(params_A2_raw)
    except TypeError:
      params_A2 = params_A2_raw
    else:
      params_A2_seq = np.asarray(params_A2_seq, dtype=np.float64)
      params_A2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A2_seq))
  params_A3_raw = params.A3
  if isinstance(params_A3_raw, (str, bytes, dict)):
    params_A3 = params_A3_raw
  else:
    try:
      params_A3_seq = list(params_A3_raw)
    except TypeError:
      params_A3 = params_A3_raw
    else:
      params_A3_seq = np.asarray(params_A3_seq, dtype=np.float64)
      params_A3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A3_seq))
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
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))
  params_beta3_raw = params.beta3
  if isinstance(params_beta3_raw, (str, bytes, dict)):
    params_beta3 = params_beta3_raw
  else:
    try:
      params_beta3_seq = list(params_beta3_raw)
    except TypeError:
      params_beta3 = params_beta3_raw
    else:
      params_beta3_seq = np.asarray(params_beta3_seq, dtype=np.float64)
      params_beta3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta3_seq))
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

  rda_s = lambda x: X2S * x

  rda_p = lambda u: jnp.zeros_like(u)

  rda_k4 = lambda s, p, b: jnp.sqrt(s ** 4 + b * p ** 2)

  rda_k2 = lambda s, p, b: s ** 2 + b * p

  rda_f0 = lambda s, p: 5 / 3 * s ** 2 + params_A0 + params_A1 * (rda_k4(s, p, params_a) / (1 + params_beta1 * rda_k4(s, p, params_a))) ** 2 + params_A2 * (rda_k4(s, p, params_b) / (1 + params_beta2 * rda_k4(s, p, params_b))) ** 4 + params_A3 * (rda_k2(s, p, params_c) / (1 + params_beta3 * rda_k2(s, p, params_c)))

  rda_f = lambda xs, us: rda_f0(rda_s(xs), rda_p(us))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, rda_f, rs, z, xs0, xs1, u0, u1)

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
  params_A0_raw = params.A0
  if isinstance(params_A0_raw, (str, bytes, dict)):
    params_A0 = params_A0_raw
  else:
    try:
      params_A0_seq = list(params_A0_raw)
    except TypeError:
      params_A0 = params_A0_raw
    else:
      params_A0_seq = np.asarray(params_A0_seq, dtype=np.float64)
      params_A0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A0_seq))
  params_A1_raw = params.A1
  if isinstance(params_A1_raw, (str, bytes, dict)):
    params_A1 = params_A1_raw
  else:
    try:
      params_A1_seq = list(params_A1_raw)
    except TypeError:
      params_A1 = params_A1_raw
    else:
      params_A1_seq = np.asarray(params_A1_seq, dtype=np.float64)
      params_A1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A1_seq))
  params_A2_raw = params.A2
  if isinstance(params_A2_raw, (str, bytes, dict)):
    params_A2 = params_A2_raw
  else:
    try:
      params_A2_seq = list(params_A2_raw)
    except TypeError:
      params_A2 = params_A2_raw
    else:
      params_A2_seq = np.asarray(params_A2_seq, dtype=np.float64)
      params_A2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A2_seq))
  params_A3_raw = params.A3
  if isinstance(params_A3_raw, (str, bytes, dict)):
    params_A3 = params_A3_raw
  else:
    try:
      params_A3_seq = list(params_A3_raw)
    except TypeError:
      params_A3 = params_A3_raw
    else:
      params_A3_seq = np.asarray(params_A3_seq, dtype=np.float64)
      params_A3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A3_seq))
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
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))
  params_beta3_raw = params.beta3
  if isinstance(params_beta3_raw, (str, bytes, dict)):
    params_beta3 = params_beta3_raw
  else:
    try:
      params_beta3_seq = list(params_beta3_raw)
    except TypeError:
      params_beta3 = params_beta3_raw
    else:
      params_beta3_seq = np.asarray(params_beta3_seq, dtype=np.float64)
      params_beta3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta3_seq))
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

  rda_s = lambda x: X2S * x
  rda_p = lambda u: jnp.zeros_like(u)

  rda_k4 = lambda s, p, b: jnp.sqrt(s ** 4 + b * p ** 2)

  rda_k2 = lambda s, p, b: s ** 2 + b * p

  rda_f0 = lambda s, p: 5 / 3 * s ** 2 + params_A0 + params_A1 * (rda_k4(s, p, params_a) / (1 + params_beta1 * rda_k4(s, p, params_a))) ** 2 + params_A2 * (rda_k4(s, p, params_b) / (1 + params_beta2 * rda_k4(s, p, params_b))) ** 4 + params_A3 * (rda_k2(s, p, params_c) / (1 + params_beta3 * rda_k2(s, p, params_c)))

  rda_f = lambda xs, us: rda_f0(rda_s(xs), rda_p(us))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, rda_f, rs, z, xs0, xs1, u0, u1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
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
  t23 = t22 ** 2
  t24 = t23 * f.p.zeta_threshold
  t25 = t20 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = f.my_piecewise3(t21, t24, t26 * t20)
  t29 = t7 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = t28 * t30
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
  t44 = t37 * s0 * t42
  t46 = t32 ** 2
  t48 = 0.1e1 / t34 / t33
  t49 = t46 * t48
  t50 = s0 ** 2
  t51 = t38 ** 2
  t54 = 0.1e1 / t39 / t51 / r0
  t56 = t49 * t50 * t54
  t57 = params.a * t46
  t58 = l0 ** 2
  t59 = t48 * t58
  t60 = t38 * r0
  t62 = 0.1e1 / t39 / t60
  t63 = t59 * t62
  t65 = t57 * t63 + t56
  t67 = jnp.sqrt(t65)
  t70 = 0.1e1 + params.beta1 * t67 / 0.24e2
  t71 = t70 ** 2
  t72 = 0.1e1 / t71
  t75 = params.b * t46
  t77 = t75 * t63 + t56
  t78 = t77 ** 2
  t80 = jnp.sqrt(t77)
  t83 = 0.1e1 + params.beta2 * t80 / 0.24e2
  t84 = t83 ** 2
  t85 = t84 ** 2
  t86 = 0.1e1 / t85
  t89 = params.c * t32
  t90 = t36 * l0
  t92 = 0.1e1 / t40 / r0
  t96 = t89 * t90 * t92 / 0.24e2 + t44 / 0.24e2
  t97 = params.A3 * t96
  t99 = params.beta3 * t96 + 0.1e1
  t100 = 0.1e1 / t99
  t102 = 0.5e1 / 0.72e2 * t44 + params.A0 + params.A1 * t65 * t72 / 0.576e3 + params.A2 * t78 * t86 / 0.331776e6 + t97 * t100
  t106 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t102)
  t107 = r1 <= f.p.dens_threshold
  t108 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t109 = 0.1e1 + t108
  t110 = t109 <= f.p.zeta_threshold
  t111 = t109 ** (0.1e1 / 0.3e1)
  t112 = t111 ** 2
  t114 = f.my_piecewise3(t110, t24, t112 * t109)
  t115 = t114 * t30
  t116 = r1 ** 2
  t117 = r1 ** (0.1e1 / 0.3e1)
  t118 = t117 ** 2
  t120 = 0.1e1 / t118 / t116
  t122 = t37 * s2 * t120
  t124 = s2 ** 2
  t125 = t116 ** 2
  t128 = 0.1e1 / t117 / t125 / r1
  t130 = t49 * t124 * t128
  t131 = l1 ** 2
  t132 = t48 * t131
  t133 = t116 * r1
  t135 = 0.1e1 / t117 / t133
  t136 = t132 * t135
  t138 = t57 * t136 + t130
  t140 = jnp.sqrt(t138)
  t143 = 0.1e1 + params.beta1 * t140 / 0.24e2
  t144 = t143 ** 2
  t145 = 0.1e1 / t144
  t149 = t75 * t136 + t130
  t150 = t149 ** 2
  t152 = jnp.sqrt(t149)
  t155 = 0.1e1 + params.beta2 * t152 / 0.24e2
  t156 = t155 ** 2
  t157 = t156 ** 2
  t158 = 0.1e1 / t157
  t161 = t36 * l1
  t163 = 0.1e1 / t118 / r1
  t167 = t89 * t161 * t163 / 0.24e2 + t122 / 0.24e2
  t168 = params.A3 * t167
  t170 = params.beta3 * t167 + 0.1e1
  t171 = 0.1e1 / t170
  t173 = 0.5e1 / 0.72e2 * t122 + params.A0 + params.A1 * t138 * t145 / 0.576e3 + params.A2 * t150 * t158 / 0.331776e6 + t168 * t171
  t177 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t6 * t115 * t173)
  t178 = t7 ** 2
  t180 = t17 / t178
  t181 = t8 - t180
  t182 = f.my_piecewise5(t11, 0, t15, 0, t181)
  t185 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t182)
  t190 = 0.1e1 / t29
  t194 = t6 * t28 * t190 * t102 / 0.10e2
  t198 = t37 * s0 / t40 / t60
  t205 = 0.16e2 / 0.3e1 * t49 * t50 / t39 / t51 / t38
  t208 = t59 / t39 / t51
  t211 = -t205 - 0.10e2 / 0.3e1 * t57 * t208
  t215 = params.A1 * t67
  t218 = 0.1e1 / t71 / t70 * params.beta1
  t222 = params.A2 * t77
  t225 = -t205 - 0.10e2 / 0.3e1 * t75 * t208
  t230 = params.A2 * t80 * t77
  t233 = 0.1e1 / t85 / t83 * params.beta2
  t241 = -t198 / 0.9e1 - 0.5e1 / 0.72e2 * t89 * t90 * t42
  t244 = t99 ** 2
  t245 = 0.1e1 / t244
  t246 = t245 * params.beta3
  t254 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t185 * t30 * t102 + t194 + 0.3e1 / 0.20e2 * t6 * t31 * (-0.5e1 / 0.27e2 * t198 + params.A1 * t211 * t72 / 0.576e3 - t215 * t218 * t211 / 0.13824e5 + t222 * t86 * t225 / 0.165888e6 - t230 * t233 * t225 / 0.3981312e7 + params.A3 * t241 * t100 - t97 * t246 * t241))
  t256 = f.my_piecewise5(t15, 0, t11, 0, -t181)
  t259 = f.my_piecewise3(t110, 0, 0.5e1 / 0.3e1 * t112 * t256)
  t267 = t6 * t114 * t190 * t173 / 0.10e2
  t269 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t6 * t259 * t30 * t173 + t267)
  vrho_0_ = t106 + t177 + t7 * (t254 + t269)
  t272 = -t8 - t180
  t273 = f.my_piecewise5(t11, 0, t15, 0, t272)
  t276 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t273)
  t282 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t276 * t30 * t102 + t194)
  t284 = f.my_piecewise5(t15, 0, t11, 0, -t272)
  t287 = f.my_piecewise3(t110, 0, 0.5e1 / 0.3e1 * t112 * t284)
  t295 = t37 * s2 / t118 / t133
  t302 = 0.16e2 / 0.3e1 * t49 * t124 / t117 / t125 / t116
  t305 = t132 / t117 / t125
  t308 = -t302 - 0.10e2 / 0.3e1 * t57 * t305
  t312 = params.A1 * t140
  t315 = 0.1e1 / t144 / t143 * params.beta1
  t319 = params.A2 * t149
  t322 = -t302 - 0.10e2 / 0.3e1 * t75 * t305
  t327 = params.A2 * t152 * t149
  t330 = 0.1e1 / t157 / t155 * params.beta2
  t338 = -t295 / 0.9e1 - 0.5e1 / 0.72e2 * t89 * t161 * t120
  t341 = t170 ** 2
  t342 = 0.1e1 / t341
  t343 = t342 * params.beta3
  t351 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t6 * t287 * t30 * t173 + t267 + 0.3e1 / 0.20e2 * t6 * t115 * (-0.5e1 / 0.27e2 * t295 + params.A1 * t308 * t145 / 0.576e3 - t312 * t315 * t308 / 0.13824e5 + t319 * t158 * t322 / 0.165888e6 - t327 * t330 * t322 / 0.3981312e7 + params.A3 * t338 * t171 - t168 * t343 * t338))
  vrho_1_ = t106 + t177 + t7 * (t282 + t351)
  t357 = params.A1 * t46 * t48
  t358 = s0 * t54
  t362 = t215 * t218
  t363 = t49 * t358
  t369 = t230 * t233
  t372 = params.A3 * t32
  t373 = t36 * t42
  t378 = params.beta3 * t32
  t386 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.5e1 / 0.72e2 * t37 * t42 + t357 * t358 * t72 / 0.288e3 - t362 * t363 / 0.6912e4 + t222 * t86 * t363 / 0.82944e5 - t369 * t363 / 0.1990656e7 + t372 * t373 * t100 / 0.24e2 - t97 * t245 * t378 * t373 / 0.24e2))
  vsigma_0_ = t7 * t386
  vsigma_1_ = 0.0e0
  t389 = s2 * t128
  t393 = t312 * t315
  t394 = t49 * t389
  t400 = t327 * t330
  t403 = t36 * t120
  t415 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t6 * t115 * (0.5e1 / 0.72e2 * t37 * t120 + t357 * t389 * t145 / 0.288e3 - t393 * t394 / 0.6912e4 + t319 * t158 * t394 / 0.82944e5 - t400 * t394 / 0.1990656e7 + t372 * t403 * t171 / 0.24e2 - t168 * t342 * t378 * t403 / 0.24e2))
  vsigma_2_ = t7 * t415
  t417 = params.A1 * params.a * t46
  t418 = t48 * l0
  t423 = t418 * t62
  t437 = params.A3 * params.c * t32
  t438 = t36 * t92
  t450 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (t417 * t418 * t62 * t72 / 0.288e3 - t362 * t57 * t423 / 0.6912e4 + t222 * t86 * params.b * t49 * l0 * t62 / 0.82944e5 - t369 * t75 * t423 / 0.1990656e7 + t437 * t438 * t100 / 0.24e2 - t97 * t246 * t89 * t438 / 0.24e2))
  vlapl_0_ = t7 * t450
  t451 = t48 * l1
  t456 = t451 * t135
  t469 = t36 * t163
  t481 = f.my_piecewise3(t107, 0, 0.3e1 / 0.20e2 * t6 * t115 * (t417 * t451 * t135 * t145 / 0.288e3 - t393 * t57 * t456 / 0.6912e4 + t319 * t158 * params.b * t49 * l1 * t135 / 0.82944e5 - t400 * t75 * t456 / 0.1990656e7 + t437 * t469 * t171 / 0.24e2 - t168 * t343 * t89 * t469 / 0.24e2))
  vlapl_1_ = t7 * t481
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
  params_A0_raw = params.A0
  if isinstance(params_A0_raw, (str, bytes, dict)):
    params_A0 = params_A0_raw
  else:
    try:
      params_A0_seq = list(params_A0_raw)
    except TypeError:
      params_A0 = params_A0_raw
    else:
      params_A0_seq = np.asarray(params_A0_seq, dtype=np.float64)
      params_A0 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A0_seq))
  params_A1_raw = params.A1
  if isinstance(params_A1_raw, (str, bytes, dict)):
    params_A1 = params_A1_raw
  else:
    try:
      params_A1_seq = list(params_A1_raw)
    except TypeError:
      params_A1 = params_A1_raw
    else:
      params_A1_seq = np.asarray(params_A1_seq, dtype=np.float64)
      params_A1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A1_seq))
  params_A2_raw = params.A2
  if isinstance(params_A2_raw, (str, bytes, dict)):
    params_A2 = params_A2_raw
  else:
    try:
      params_A2_seq = list(params_A2_raw)
    except TypeError:
      params_A2 = params_A2_raw
    else:
      params_A2_seq = np.asarray(params_A2_seq, dtype=np.float64)
      params_A2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A2_seq))
  params_A3_raw = params.A3
  if isinstance(params_A3_raw, (str, bytes, dict)):
    params_A3 = params_A3_raw
  else:
    try:
      params_A3_seq = list(params_A3_raw)
    except TypeError:
      params_A3 = params_A3_raw
    else:
      params_A3_seq = np.asarray(params_A3_seq, dtype=np.float64)
      params_A3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_A3_seq))
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
  params_beta1_raw = params.beta1
  if isinstance(params_beta1_raw, (str, bytes, dict)):
    params_beta1 = params_beta1_raw
  else:
    try:
      params_beta1_seq = list(params_beta1_raw)
    except TypeError:
      params_beta1 = params_beta1_raw
    else:
      params_beta1_seq = np.asarray(params_beta1_seq, dtype=np.float64)
      params_beta1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta1_seq))
  params_beta2_raw = params.beta2
  if isinstance(params_beta2_raw, (str, bytes, dict)):
    params_beta2 = params_beta2_raw
  else:
    try:
      params_beta2_seq = list(params_beta2_raw)
    except TypeError:
      params_beta2 = params_beta2_raw
    else:
      params_beta2_seq = np.asarray(params_beta2_seq, dtype=np.float64)
      params_beta2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta2_seq))
  params_beta3_raw = params.beta3
  if isinstance(params_beta3_raw, (str, bytes, dict)):
    params_beta3 = params_beta3_raw
  else:
    try:
      params_beta3_seq = list(params_beta3_raw)
    except TypeError:
      params_beta3 = params_beta3_raw
    else:
      params_beta3_seq = np.asarray(params_beta3_seq, dtype=np.float64)
      params_beta3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta3_seq))
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

  rda_s = lambda x: X2S * x
  rda_p = lambda u: jnp.zeros_like(u)

  rda_k4 = lambda s, p, b: jnp.sqrt(s ** 4 + b * p ** 2)

  rda_k2 = lambda s, p, b: s ** 2 + b * p

  rda_f0 = lambda s, p: 5 / 3 * s ** 2 + params_A0 + params_A1 * (rda_k4(s, p, params_a) / (1 + params_beta1 * rda_k4(s, p, params_a))) ** 2 + params_A2 * (rda_k4(s, p, params_b) / (1 + params_beta2 * rda_k4(s, p, params_b))) ** 4 + params_A3 * (rda_k2(s, p, params_c) / (1 + params_beta3 * rda_k2(s, p, params_c)))

  rda_f = lambda xs, us: rda_f0(rda_s(xs), rda_p(us))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, rda_f, rs, z, xs0, xs1, u0, u1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = t20 * t22
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t22 / t33
  t37 = t29 * t32 * t35
  t39 = t24 ** 2
  t41 = 0.1e1 / t26 / t25
  t42 = t39 * t41
  t43 = s0 ** 2
  t44 = t43 * t30
  t45 = t33 ** 2
  t48 = 0.1e1 / t21 / t45 / r0
  t50 = t42 * t44 * t48
  t52 = params.a * t39 * t41
  t53 = l0 ** 2
  t54 = t53 * t30
  t55 = t33 * r0
  t57 = 0.1e1 / t21 / t55
  t58 = t54 * t57
  t61 = 0.2e1 * t52 * t58 + 0.2e1 * t50
  t63 = jnp.sqrt(t61)
  t66 = 0.1e1 + params.beta1 * t63 / 0.24e2
  t67 = t66 ** 2
  t68 = 0.1e1 / t67
  t72 = params.b * t39 * t41
  t75 = 0.2e1 * t72 * t58 + 0.2e1 * t50
  t76 = t75 ** 2
  t78 = jnp.sqrt(t75)
  t81 = 0.1e1 + params.beta2 * t78 / 0.24e2
  t82 = t81 ** 2
  t83 = t82 ** 2
  t84 = 0.1e1 / t83
  t87 = params.c * t24
  t88 = t87 * t28
  t89 = l0 * t31
  t91 = 0.1e1 / t22 / r0
  t95 = t88 * t89 * t91 / 0.24e2 + t37 / 0.24e2
  t96 = params.A3 * t95
  t98 = params.beta3 * t95 + 0.1e1
  t99 = 0.1e1 / t98
  t101 = 0.5e1 / 0.72e2 * t37 + params.A0 + params.A1 * t61 * t68 / 0.576e3 + params.A2 * t76 * t84 / 0.331776e6 + t96 * t99
  t105 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t101)
  t114 = t29 * t32 / t22 / t55
  t121 = 0.32e2 / 0.3e1 * t42 * t44 / t21 / t45 / t33
  t124 = t54 / t21 / t45
  t127 = -t121 - 0.20e2 / 0.3e1 * t52 * t124
  t131 = params.A1 * t63
  t134 = 0.1e1 / t67 / t66 * params.beta1
  t138 = params.A2 * t75
  t141 = -t121 - 0.20e2 / 0.3e1 * t72 * t124
  t146 = params.A2 * t78 * t75
  t149 = 0.1e1 / t83 / t81 * params.beta2
  t157 = -t114 / 0.9e1 - 0.5e1 / 0.72e2 * t88 * t89 * t35
  t160 = t98 ** 2
  t162 = 0.1e1 / t160 * params.beta3
  t170 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t101 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-0.5e1 / 0.27e2 * t114 + params.A1 * t127 * t68 / 0.576e3 - t131 * t134 * t127 / 0.13824e5 + t138 * t84 * t141 / 0.165888e6 - t146 * t149 * t141 / 0.3981312e7 + params.A3 * t157 * t99 - t96 * t162 * t157))
  vrho_0_ = 0.2e1 * r0 * t170 + 0.2e1 * t105
  t173 = t31 * t35
  t174 = t29 * t173
  t178 = s0 * t30
  t185 = t42 * t178 * t48
  t203 = t96 * t162
  t210 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.5e1 / 0.72e2 * t174 + params.A1 * t39 * t41 * t178 * t48 * t68 / 0.144e3 - t131 * t134 * t185 / 0.3456e4 + t138 * t84 * t39 * t41 * s0 * t30 * t48 / 0.41472e5 - t146 * t149 * t185 / 0.995328e6 + params.A3 * t24 * t28 * t173 * t99 / 0.24e2 - t203 * t174 / 0.24e2))
  vsigma_0_ = 0.2e1 * r0 * t210
  t214 = l0 * t30
  t222 = t42 * t214 * t57
  t235 = t28 * t31
  t248 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (params.A1 * params.a * t42 * t214 * t57 * t68 / 0.144e3 - t131 * t134 * params.a * t222 / 0.3456e4 + t138 * t84 * params.b * t222 / 0.41472e5 - t146 * t149 * params.b * t222 / 0.995328e6 + params.A3 * params.c * t24 * t235 * t91 * t99 / 0.24e2 - t203 * t87 * t235 * t91 / 0.24e2))
  vlapl_0_ = 0.2e1 * r0 * t248
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
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t23 = t20 / t21
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t34 = t21 ** 2
  t36 = 0.1e1 / t34 / t33
  t38 = t29 * t32 * t36
  t40 = t24 ** 2
  t42 = 0.1e1 / t26 / t25
  t43 = t40 * t42
  t44 = s0 ** 2
  t45 = t44 * t30
  t46 = t33 ** 2
  t49 = 0.1e1 / t21 / t46 / r0
  t51 = t43 * t45 * t49
  t53 = params.a * t40 * t42
  t54 = l0 ** 2
  t55 = t54 * t30
  t56 = t33 * r0
  t59 = t55 / t21 / t56
  t62 = 0.2e1 * t53 * t59 + 0.2e1 * t51
  t64 = jnp.sqrt(t62)
  t67 = 0.1e1 + params.beta1 * t64 / 0.24e2
  t68 = t67 ** 2
  t69 = 0.1e1 / t68
  t73 = params.b * t40 * t42
  t76 = 0.2e1 * t73 * t59 + 0.2e1 * t51
  t77 = t76 ** 2
  t79 = jnp.sqrt(t76)
  t82 = 0.1e1 + params.beta2 * t79 / 0.24e2
  t83 = t82 ** 2
  t84 = t83 ** 2
  t85 = 0.1e1 / t84
  t89 = params.c * t24 * t28
  t90 = l0 * t31
  t96 = t38 / 0.24e2 + t89 * t90 / t34 / r0 / 0.24e2
  t97 = params.A3 * t96
  t99 = params.beta3 * t96 + 0.1e1
  t100 = 0.1e1 / t99
  t102 = 0.5e1 / 0.72e2 * t38 + params.A0 + params.A1 * t62 * t69 / 0.576e3 + params.A2 * t77 * t85 / 0.331776e6 + t97 * t100
  t106 = t20 * t34
  t108 = 0.1e1 / t34 / t56
  t110 = t29 * t32 * t108
  t117 = 0.32e2 / 0.3e1 * t43 * t45 / t21 / t46 / t33
  t120 = t55 / t21 / t46
  t123 = -t117 - 0.20e2 / 0.3e1 * t53 * t120
  t127 = params.A1 * t64
  t130 = 0.1e1 / t68 / t67 * params.beta1
  t134 = params.A2 * t76
  t137 = -t117 - 0.20e2 / 0.3e1 * t73 * t120
  t142 = params.A2 * t79 * t76
  t144 = 0.1e1 / t84 / t82
  t145 = t144 * params.beta2
  t153 = -t110 / 0.9e1 - 0.5e1 / 0.72e2 * t89 * t90 * t36
  t156 = t99 ** 2
  t158 = 0.1e1 / t156 * params.beta3
  t161 = -0.5e1 / 0.27e2 * t110 + params.A1 * t123 * t69 / 0.576e3 - t127 * t130 * t123 / 0.13824e5 + t134 * t85 * t137 / 0.165888e6 - t142 * t145 * t137 / 0.3981312e7 + params.A3 * t153 * t100 - t97 * t158 * t153
  t166 = f.my_piecewise3(t2, 0, t7 * t23 * t102 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t106 * t161)
  t180 = t29 * t32 / t34 / t46
  t187 = 0.608e3 / 0.9e1 * t43 * t45 / t21 / t46 / t56
  t188 = t55 * t49
  t191 = t187 + 0.260e3 / 0.9e1 * t53 * t188
  t195 = t123 ** 2
  t201 = t68 ** 2
  t204 = params.beta1 ** 2
  t211 = t137 ** 2
  t222 = t187 + 0.260e3 / 0.9e1 * t73 * t188
  t228 = params.beta2 ** 2
  t240 = 0.11e2 / 0.27e2 * t180 + 0.5e1 / 0.27e2 * t89 * t90 * t108
  t243 = t153 ** 2
  t249 = params.beta3 ** 2
  t256 = 0.55e2 / 0.81e2 * t180 + params.A1 * t191 * t69 / 0.576e3 - params.A1 * t195 * t130 / t64 / 0.9216e4 + params.A1 / t201 * t204 * t195 / 0.221184e6 - t127 * t130 * t191 / 0.13824e5 + params.A2 * t211 * t85 / 0.165888e6 - 0.7e1 / 0.7962624e7 * params.A2 * t79 * t144 * t211 * params.beta2 + t134 * t85 * t222 / 0.165888e6 + 0.5e1 / 0.191102976e9 * t134 / t84 / t83 * t228 * t211 - t142 * t145 * t222 / 0.3981312e7 + params.A3 * t240 * t100 - 0.2e1 * params.A3 * t243 * t158 + 0.2e1 * t97 / t156 / t99 * t249 * t243 - t97 * t158 * t240
  t261 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t102 / 0.30e2 + t7 * t23 * t161 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t106 * t256)
  v2rho2_0_ = 0.2e1 * r0 * t261 + 0.4e1 * t166
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t24 = t20 / t21 / r0
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = t25 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t37 = 0.1e1 / t35 / t34
  t39 = t30 * t33 * t37
  t41 = t25 ** 2
  t43 = 0.1e1 / t27 / t26
  t44 = t41 * t43
  t45 = s0 ** 2
  t46 = t45 * t31
  t47 = t34 ** 2
  t48 = t47 * r0
  t50 = 0.1e1 / t21 / t48
  t52 = t44 * t46 * t50
  t54 = params.a * t41 * t43
  t55 = l0 ** 2
  t56 = t55 * t31
  t57 = t34 * r0
  t60 = t56 / t21 / t57
  t63 = 0.2e1 * t54 * t60 + 0.2e1 * t52
  t65 = jnp.sqrt(t63)
  t68 = 0.1e1 + params.beta1 * t65 / 0.24e2
  t69 = t68 ** 2
  t70 = 0.1e1 / t69
  t74 = params.b * t41 * t43
  t77 = 0.2e1 * t74 * t60 + 0.2e1 * t52
  t78 = t77 ** 2
  t80 = jnp.sqrt(t77)
  t83 = 0.1e1 + params.beta2 * t80 / 0.24e2
  t84 = t83 ** 2
  t85 = t84 ** 2
  t86 = 0.1e1 / t85
  t90 = params.c * t25 * t29
  t91 = l0 * t32
  t97 = t39 / 0.24e2 + t90 * t91 / t35 / r0 / 0.24e2
  t98 = params.A3 * t97
  t100 = params.beta3 * t97 + 0.1e1
  t101 = 0.1e1 / t100
  t103 = 0.5e1 / 0.72e2 * t39 + params.A0 + params.A1 * t63 * t70 / 0.576e3 + params.A2 * t78 * t86 / 0.331776e6 + t98 * t101
  t108 = t20 / t21
  t110 = 0.1e1 / t35 / t57
  t112 = t30 * t33 * t110
  t116 = 0.1e1 / t21 / t47 / t34
  t119 = 0.32e2 / 0.3e1 * t44 * t46 * t116
  t122 = t56 / t21 / t47
  t125 = -t119 - 0.20e2 / 0.3e1 * t54 * t122
  t129 = params.A1 * t65
  t131 = 0.1e1 / t69 / t68
  t132 = t131 * params.beta1
  t136 = params.A2 * t77
  t139 = -t119 - 0.20e2 / 0.3e1 * t74 * t122
  t144 = params.A2 * t80 * t77
  t146 = 0.1e1 / t85 / t83
  t147 = t146 * params.beta2
  t155 = -t112 / 0.9e1 - 0.5e1 / 0.72e2 * t90 * t91 * t37
  t158 = t100 ** 2
  t160 = 0.1e1 / t158 * params.beta3
  t161 = t160 * t155
  t163 = -0.5e1 / 0.27e2 * t112 + params.A1 * t125 * t70 / 0.576e3 - t129 * t132 * t125 / 0.13824e5 + t136 * t86 * t139 / 0.165888e6 - t144 * t147 * t139 / 0.3981312e7 + params.A3 * t155 * t101 - t98 * t161
  t167 = t20 * t35
  t169 = 0.1e1 / t35 / t47
  t171 = t30 * t33 * t169
  t178 = 0.608e3 / 0.9e1 * t44 * t46 / t21 / t47 / t57
  t179 = t56 * t50
  t182 = t178 + 0.260e3 / 0.9e1 * t54 * t179
  t183 = params.A1 * t182
  t186 = t125 ** 2
  t188 = 0.1e1 / t65
  t192 = t69 ** 2
  t193 = 0.1e1 / t192
  t194 = params.A1 * t193
  t195 = params.beta1 ** 2
  t202 = t139 ** 2
  t206 = params.A2 * t80
  t213 = t178 + 0.260e3 / 0.9e1 * t74 * t179
  t214 = t86 * t213
  t218 = 0.1e1 / t85 / t84
  t219 = params.beta2 ** 2
  t231 = 0.11e2 / 0.27e2 * t171 + 0.5e1 / 0.27e2 * t90 * t91 * t110
  t232 = params.A3 * t231
  t234 = t155 ** 2
  t239 = 0.1e1 / t158 / t100
  t240 = params.beta3 ** 2
  t241 = t239 * t240
  t247 = 0.55e2 / 0.81e2 * t171 + t183 * t70 / 0.576e3 - params.A1 * t186 * t132 * t188 / 0.9216e4 + t194 * t195 * t186 / 0.221184e6 - t129 * t132 * t182 / 0.13824e5 + params.A2 * t202 * t86 / 0.165888e6 - 0.7e1 / 0.7962624e7 * t206 * t146 * t202 * params.beta2 + t136 * t214 / 0.165888e6 + 0.5e1 / 0.191102976e9 * t136 * t218 * t219 * t202 - t144 * t147 * t213 / 0.3981312e7 + t232 * t101 - 0.2e1 * params.A3 * t234 * t160 + 0.2e1 * t98 * t241 * t234 - t98 * t160 * t231
  t252 = f.my_piecewise3(t2, 0, -t7 * t24 * t103 / 0.30e2 + t7 * t108 * t163 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t167 * t247)
  t266 = t158 ** 2
  t270 = t234 * t155
  t279 = t202 * t139
  t283 = t47 ** 2
  t288 = 0.13376e5 / 0.27e2 * t44 * t46 / t21 / t283
  t289 = t56 * t116
  t292 = -t288 - 0.4160e4 / 0.27e2 * t74 * t289
  t299 = t30 * t33 / t35 / t48
  t307 = -0.154e3 / 0.81e2 * t299 - 0.55e2 / 0.81e2 * t90 * t91 * t169
  t310 = t186 * t125
  t311 = params.A1 * t310
  t331 = -t288 - 0.4160e4 / 0.27e2 * t54 * t289
  t340 = -0.6e1 * t98 / t266 * t240 * params.beta3 * t270 - 0.5e1 / 0.1528823808e10 * t206 / t85 / t84 / t83 * t219 * params.beta2 * t279 - t144 * t147 * t292 / 0.3981312e7 - 0.770e3 / 0.243e3 * t299 - 0.6e1 * t232 * t161 - t98 * t160 * t307 + t311 * t193 * t195 / t63 / 0.147456e6 + t194 * t195 * t125 * t182 / 0.73728e5 - params.A1 / t192 / t68 * t195 * params.beta1 * t310 * t188 / 0.2654208e7 - t129 * t132 * t331 / 0.13824e5 - 0.5e1 / 0.5308416e7 * params.A2 * t279 * t147 / t80
  t384 = params.A2 * t139 * t214 / 0.55296e5 + 0.5e1 / 0.42467328e8 * params.A2 * t218 * t279 * t219 + t136 * t86 * t292 / 0.165888e6 + params.A1 * t331 * t70 / 0.576e3 + params.A3 * t307 * t101 - t183 * t131 * params.beta1 * t188 * t125 / 0.3072e4 + t311 * t132 / t65 / t63 / 0.18432e5 - 0.7e1 / 0.2654208e7 * t206 * t146 * t139 * params.beta2 * t213 + 0.5e1 / 0.63700992e8 * t136 * t218 * t219 * t139 * t213 + 0.6e1 * params.A3 * t270 * t241 + 0.6e1 * t98 * t239 * t240 * t155 * t231
  t390 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t103 - t7 * t24 * t163 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t108 * t247 + 0.3e1 / 0.20e2 * t7 * t167 * (t340 + t384))
  v3rho3_0_ = 0.2e1 * r0 * t390 + 0.6e1 * t252

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** 2
  t22 = r0 ** (0.1e1 / 0.3e1)
  t25 = t20 / t22 / t21
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = t26 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = t22 ** 2
  t37 = 0.1e1 / t35 / t21
  t39 = t31 * t34 * t37
  t41 = t26 ** 2
  t43 = 0.1e1 / t28 / t27
  t44 = t41 * t43
  t45 = s0 ** 2
  t46 = t45 * t32
  t47 = t21 ** 2
  t48 = t47 * r0
  t50 = 0.1e1 / t22 / t48
  t52 = t44 * t46 * t50
  t54 = params.a * t41 * t43
  t55 = l0 ** 2
  t56 = t55 * t32
  t57 = t21 * r0
  t59 = 0.1e1 / t22 / t57
  t60 = t56 * t59
  t63 = 0.2e1 * t54 * t60 + 0.2e1 * t52
  t65 = jnp.sqrt(t63)
  t68 = 0.1e1 + params.beta1 * t65 / 0.24e2
  t69 = t68 ** 2
  t70 = 0.1e1 / t69
  t74 = params.b * t41 * t43
  t77 = 0.2e1 * t74 * t60 + 0.2e1 * t52
  t78 = t77 ** 2
  t80 = jnp.sqrt(t77)
  t83 = 0.1e1 + params.beta2 * t80 / 0.24e2
  t84 = t83 ** 2
  t85 = t84 ** 2
  t86 = 0.1e1 / t85
  t90 = params.c * t26 * t30
  t91 = l0 * t33
  t97 = t39 / 0.24e2 + t90 * t91 / t35 / r0 / 0.24e2
  t98 = params.A3 * t97
  t100 = params.beta3 * t97 + 0.1e1
  t101 = 0.1e1 / t100
  t103 = 0.5e1 / 0.72e2 * t39 + params.A0 + params.A1 * t63 * t70 / 0.576e3 + params.A2 * t78 * t86 / 0.331776e6 + t98 * t101
  t109 = t20 / t22 / r0
  t111 = 0.1e1 / t35 / t57
  t113 = t31 * t34 * t111
  t115 = t47 * t21
  t117 = 0.1e1 / t22 / t115
  t120 = 0.32e2 / 0.3e1 * t44 * t46 * t117
  t123 = t56 / t22 / t47
  t126 = -t120 - 0.20e2 / 0.3e1 * t54 * t123
  t130 = params.A1 * t65
  t132 = 0.1e1 / t69 / t68
  t133 = t132 * params.beta1
  t137 = params.A2 * t77
  t140 = -t120 - 0.20e2 / 0.3e1 * t74 * t123
  t144 = t80 * t77
  t145 = params.A2 * t144
  t147 = 0.1e1 / t85 / t83
  t148 = t147 * params.beta2
  t156 = -t113 / 0.9e1 - 0.5e1 / 0.72e2 * t90 * t91 * t37
  t159 = t100 ** 2
  t161 = 0.1e1 / t159 * params.beta3
  t162 = t161 * t156
  t164 = -0.5e1 / 0.27e2 * t113 + params.A1 * t126 * t70 / 0.576e3 - t130 * t133 * t126 / 0.13824e5 + t137 * t86 * t140 / 0.165888e6 - t145 * t148 * t140 / 0.3981312e7 + params.A3 * t156 * t101 - t98 * t162
  t169 = t20 / t22
  t171 = 0.1e1 / t35 / t47
  t173 = t31 * t34 * t171
  t177 = 0.1e1 / t22 / t47 / t57
  t180 = 0.608e3 / 0.9e1 * t44 * t46 * t177
  t181 = t56 * t50
  t184 = t180 + 0.260e3 / 0.9e1 * t54 * t181
  t185 = params.A1 * t184
  t188 = t126 ** 2
  t189 = params.A1 * t188
  t190 = 0.1e1 / t65
  t191 = t133 * t190
  t194 = t69 ** 2
  t195 = 0.1e1 / t194
  t196 = params.A1 * t195
  t197 = params.beta1 ** 2
  t204 = t140 ** 2
  t205 = params.A2 * t204
  t208 = params.A2 * t80
  t215 = t180 + 0.260e3 / 0.9e1 * t74 * t181
  t216 = t86 * t215
  t220 = 0.1e1 / t85 / t84
  t221 = params.beta2 ** 2
  t222 = t220 * t221
  t233 = 0.11e2 / 0.27e2 * t173 + 0.5e1 / 0.27e2 * t90 * t91 * t111
  t234 = params.A3 * t233
  t236 = t156 ** 2
  t241 = 0.1e1 / t159 / t100
  t242 = params.beta3 ** 2
  t243 = t241 * t242
  t244 = t243 * t236
  t249 = 0.55e2 / 0.81e2 * t173 + t185 * t70 / 0.576e3 - t189 * t191 / 0.9216e4 + t196 * t197 * t188 / 0.221184e6 - t130 * t133 * t184 / 0.13824e5 + t205 * t86 / 0.165888e6 - 0.7e1 / 0.7962624e7 * t208 * t147 * t204 * params.beta2 + t137 * t216 / 0.165888e6 + 0.5e1 / 0.191102976e9 * t137 * t222 * t204 - t145 * t148 * t215 / 0.3981312e7 + t234 * t101 - 0.2e1 * params.A3 * t236 * t161 + 0.2e1 * t98 * t244 - t98 * t161 * t233
  t253 = t20 * t35
  t254 = t159 ** 2
  t255 = 0.1e1 / t254
  t256 = t242 * params.beta3
  t257 = t255 * t256
  t258 = t236 * t156
  t264 = 0.1e1 / t85 / t84 / t83
  t265 = t221 * params.beta2
  t266 = t264 * t265
  t267 = t204 * t140
  t271 = t47 ** 2
  t276 = 0.13376e5 / 0.27e2 * t44 * t46 / t22 / t271
  t277 = t56 * t117
  t280 = -t276 - 0.4160e4 / 0.27e2 * t74 * t277
  t285 = 0.1e1 / t35 / t48
  t287 = t31 * t34 * t285
  t295 = -0.154e3 / 0.81e2 * t287 - 0.55e2 / 0.81e2 * t90 * t91 * t171
  t298 = t188 * t126
  t299 = params.A1 * t298
  t300 = t195 * t197
  t301 = 0.1e1 / t63
  t305 = t197 * t126
  t310 = 0.1e1 / t194 / t68
  t311 = params.A1 * t310
  t312 = t197 * params.beta1
  t319 = -t276 - 0.4160e4 / 0.27e2 * t54 * t277
  t324 = 0.1e1 / t80
  t328 = -0.6e1 * t98 * t257 * t258 - 0.5e1 / 0.1528823808e10 * t208 * t266 * t267 - t145 * t148 * t280 / 0.3981312e7 - 0.770e3 / 0.243e3 * t287 - 0.6e1 * t234 * t162 - t98 * t161 * t295 + t299 * t300 * t301 / 0.147456e6 + t196 * t305 * t184 / 0.73728e5 - t311 * t312 * t298 * t190 / 0.2654208e7 - t130 * t133 * t319 / 0.13824e5 - 0.5e1 / 0.5308416e7 * params.A2 * t267 * t148 * t324
  t329 = params.A2 * t140
  t332 = params.A2 * t220
  t336 = t86 * t280
  t342 = params.A3 * t295
  t344 = t185 * t132
  t350 = 0.1e1 / t65 / t63
  t354 = t208 * t147
  t359 = t137 * t220
  t367 = t98 * t241
  t372 = t329 * t216 / 0.55296e5 + 0.5e1 / 0.42467328e8 * t332 * t267 * t221 + t137 * t336 / 0.165888e6 + params.A1 * t319 * t70 / 0.576e3 + t342 * t101 - t344 * params.beta1 * t190 * t126 / 0.3072e4 + t299 * t133 * t350 / 0.18432e5 - 0.7e1 / 0.2654208e7 * t354 * t140 * params.beta2 * t215 + 0.5e1 / 0.63700992e8 * t359 * t221 * t140 * t215 + 0.6e1 * params.A3 * t258 * t243 + 0.6e1 * t367 * t242 * t156 * t233
  t373 = t328 + t372
  t378 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t103 - t7 * t109 * t164 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t169 * t249 + 0.3e1 / 0.20e2 * t7 * t253 * t373)
  t393 = t215 ** 2
  t402 = 0.334400e6 / 0.81e2 * t44 * t46 / t22 / t271 / r0
  t403 = t56 * t177
  t406 = t402 + 0.79040e5 / 0.81e2 * t54 * t403
  t413 = t31 * t34 / t35 / t115
  t418 = 0.2618e4 / 0.243e3 * t413 + 0.770e3 / 0.243e3 * t90 * t91 * t285
  t470 = t242 ** 2
  t472 = t236 ** 2
  t481 = t197 ** 2
  t482 = t188 ** 2
  t490 = t204 ** 2
  t491 = params.A2 * t490
  t500 = params.A2 * t393 * t86 / 0.55296e5 + params.A1 * t406 * t70 / 0.576e3 + params.A3 * t418 * t101 + 0.8e1 * t367 * t242 * t295 * t156 + 0.5e1 / 0.47775744e8 * t359 * t221 * t280 * t140 + t189 * t195 * t197 * t301 * t184 / 0.24576e5 - t311 * t312 * t188 * t184 * t190 / 0.442368e6 - params.A1 * t190 * t132 * params.beta1 * t319 * t126 / 0.2304e4 - 0.36e2 * t98 * t255 * t256 * t236 * t233 - 0.5e1 / 0.884736e6 * t205 * t147 * params.beta2 * t324 * t215 + t344 * params.beta1 * t350 * t188 / 0.3072e4 - 0.5e1 / 0.254803968e9 * t208 * t264 * t265 * t204 * t215 - 0.7e1 / 0.1990656e7 * t354 * params.beta2 * t280 * t140 + 0.24e2 * t98 / t254 / t100 * t470 * t472 + 0.36e2 * t234 * t244 + 0.5e1 / 0.127401984e9 * params.A1 / t194 / t69 * t481 * t482 * t301 - t130 * t133 * t406 / 0.13824e5 + 0.25e2 / 0.254803968e9 * t491 * t222 / t77 + 0.5e1 / 0.7077888e7 * t332 * t204 * t221 * t215
  t503 = t402 + 0.79040e5 / 0.81e2 * t74 * t403
  t507 = params.A1 * t482
  t508 = t63 ** 2
  t521 = t233 ** 2
  t549 = t184 ** 2
  t562 = t85 ** 2
  t565 = t221 ** 2
  t574 = -t145 * t148 * t503 / 0.3981312e7 - t507 * t133 / t65 / t508 / 0.12288e5 - 0.7e1 / 0.2654208e7 * t208 * t147 * t393 * params.beta2 + 0.5e1 / 0.63700992e8 * t137 * t222 * t393 + 0.6e1 * t98 * t243 * t521 - 0.25e2 / 0.1528823808e10 * params.A2 * t324 * t266 * t490 - 0.8e1 * t342 * t162 + 0.13090e5 / 0.729e3 * t413 - t98 * t161 * t418 - t507 * t310 * t312 * t350 / 0.2654208e7 + t196 * t305 * t319 / 0.55296e5 - t507 * t300 / t508 / 0.98304e5 + 0.5e1 / 0.10616832e8 * t491 * t148 / t144 - params.A1 * t549 * t191 / 0.3072e4 - 0.6e1 * params.A3 * t521 * t161 + t196 * t197 * t549 / 0.73728e5 - 0.24e2 * params.A3 * t472 * t257 + 0.35e2 / 0.73383542784e11 * params.A2 / t562 * t565 * t490 + t329 * t336 / 0.41472e5 + t137 * t86 * t503 / 0.165888e6
  t580 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t59 * t103 + 0.8e1 / 0.45e2 * t7 * t25 * t164 - t7 * t109 * t249 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t169 * t373 + 0.3e1 / 0.20e2 * t7 * t253 * (t500 + t574))
  v4rho4_0_ = 0.2e1 * r0 * t580 + 0.8e1 * t378

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
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
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t26 = t17 * t25
  t27 = t8 - t26
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t31 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t28)
  t32 = t7 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = t31 * t33
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t40 = t35 * t39
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t47 = t40 * s0 * t45
  t49 = t35 ** 2
  t51 = 0.1e1 / t37 / t36
  t52 = t49 * t51
  t53 = s0 ** 2
  t54 = t41 ** 2
  t57 = 0.1e1 / t42 / t54 / r0
  t59 = t52 * t53 * t57
  t60 = params.a * t49
  t61 = l0 ** 2
  t62 = t51 * t61
  t63 = t41 * r0
  t66 = t62 / t42 / t63
  t68 = t60 * t66 + t59
  t70 = jnp.sqrt(t68)
  t73 = 0.1e1 + params.beta1 * t70 / 0.24e2
  t74 = t73 ** 2
  t75 = 0.1e1 / t74
  t78 = params.b * t49
  t80 = t78 * t66 + t59
  t81 = t80 ** 2
  t83 = jnp.sqrt(t80)
  t86 = 0.1e1 + params.beta2 * t83 / 0.24e2
  t87 = t86 ** 2
  t88 = t87 ** 2
  t89 = 0.1e1 / t88
  t92 = params.c * t35
  t93 = t39 * l0
  t99 = t47 / 0.24e2 + t92 * t93 / t43 / r0 / 0.24e2
  t100 = params.A3 * t99
  t102 = params.beta3 * t99 + 0.1e1
  t103 = 0.1e1 / t102
  t105 = 0.5e1 / 0.72e2 * t47 + params.A0 + params.A1 * t68 * t75 / 0.576e3 + params.A2 * t81 * t89 / 0.331776e6 + t100 * t103
  t109 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t110 = t109 ** 2
  t111 = t110 * f.p.zeta_threshold
  t113 = f.my_piecewise3(t21, t111, t23 * t20)
  t114 = 0.1e1 / t32
  t115 = t113 * t114
  t118 = t6 * t115 * t105 / 0.10e2
  t119 = t113 * t33
  t121 = 0.1e1 / t43 / t63
  t123 = t40 * s0 * t121
  t130 = 0.16e2 / 0.3e1 * t52 * t53 / t42 / t54 / t41
  t133 = t62 / t42 / t54
  t136 = -t130 - 0.10e2 / 0.3e1 * t60 * t133
  t140 = params.A1 * t70
  t143 = 0.1e1 / t74 / t73 * params.beta1
  t147 = params.A2 * t80
  t150 = -t130 - 0.10e2 / 0.3e1 * t78 * t133
  t155 = params.A2 * t83 * t80
  t157 = 0.1e1 / t88 / t86
  t158 = t157 * params.beta2
  t166 = -t123 / 0.9e1 - 0.5e1 / 0.72e2 * t92 * t93 * t45
  t169 = t102 ** 2
  t171 = 0.1e1 / t169 * params.beta3
  t174 = -0.5e1 / 0.27e2 * t123 + params.A1 * t136 * t75 / 0.576e3 - t140 * t143 * t136 / 0.13824e5 + t147 * t89 * t150 / 0.165888e6 - t155 * t158 * t150 / 0.3981312e7 + params.A3 * t166 * t103 - t100 * t171 * t166
  t179 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t105 + t118 + 0.3e1 / 0.20e2 * t6 * t119 * t174)
  t181 = r1 <= f.p.dens_threshold
  t182 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t183 = 0.1e1 + t182
  t184 = t183 <= f.p.zeta_threshold
  t185 = t183 ** (0.1e1 / 0.3e1)
  t186 = t185 ** 2
  t188 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t191 = f.my_piecewise3(t184, 0, 0.5e1 / 0.3e1 * t186 * t188)
  t192 = t191 * t33
  t193 = r1 ** 2
  t194 = r1 ** (0.1e1 / 0.3e1)
  t195 = t194 ** 2
  t197 = 0.1e1 / t195 / t193
  t199 = t40 * s2 * t197
  t201 = s2 ** 2
  t202 = t193 ** 2
  t205 = 0.1e1 / t194 / t202 / r1
  t207 = t52 * t201 * t205
  t208 = l1 ** 2
  t209 = t51 * t208
  t210 = t193 * r1
  t213 = t209 / t194 / t210
  t215 = t60 * t213 + t207
  t217 = jnp.sqrt(t215)
  t220 = 0.1e1 + params.beta1 * t217 / 0.24e2
  t221 = t220 ** 2
  t222 = 0.1e1 / t221
  t226 = t78 * t213 + t207
  t227 = t226 ** 2
  t229 = jnp.sqrt(t226)
  t232 = 0.1e1 + params.beta2 * t229 / 0.24e2
  t233 = t232 ** 2
  t234 = t233 ** 2
  t235 = 0.1e1 / t234
  t238 = t39 * l1
  t244 = t199 / 0.24e2 + t92 * t238 / t195 / r1 / 0.24e2
  t245 = params.A3 * t244
  t247 = params.beta3 * t244 + 0.1e1
  t248 = 0.1e1 / t247
  t250 = 0.5e1 / 0.72e2 * t199 + params.A0 + params.A1 * t215 * t222 / 0.576e3 + params.A2 * t227 * t235 / 0.331776e6 + t245 * t248
  t255 = f.my_piecewise3(t184, t111, t186 * t183)
  t256 = t255 * t114
  t259 = t6 * t256 * t250 / 0.10e2
  t261 = f.my_piecewise3(t181, 0, 0.3e1 / 0.20e2 * t6 * t192 * t250 + t259)
  t263 = 0.1e1 / t22
  t264 = t28 ** 2
  t269 = t17 / t24 / t7
  t271 = -0.2e1 * t25 + 0.2e1 * t269
  t272 = f.my_piecewise5(t11, 0, t15, 0, t271)
  t276 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t263 * t264 + 0.5e1 / 0.3e1 * t23 * t272)
  t283 = t6 * t31 * t114 * t105
  t289 = 0.1e1 / t32 / t7
  t293 = t6 * t113 * t289 * t105 / 0.30e2
  t295 = t6 * t115 * t174
  t300 = t40 * s0 / t43 / t54
  t307 = 0.304e3 / 0.9e1 * t52 * t53 / t42 / t54 / t63
  t308 = t62 * t57
  t311 = t307 + 0.130e3 / 0.9e1 * t60 * t308
  t315 = t136 ** 2
  t321 = t74 ** 2
  t324 = params.beta1 ** 2
  t331 = t150 ** 2
  t342 = t307 + 0.130e3 / 0.9e1 * t78 * t308
  t348 = params.beta2 ** 2
  t360 = 0.11e2 / 0.27e2 * t300 + 0.5e1 / 0.27e2 * t92 * t93 * t121
  t363 = t166 ** 2
  t369 = params.beta3 ** 2
  t376 = 0.55e2 / 0.81e2 * t300 + params.A1 * t311 * t75 / 0.576e3 - params.A1 * t315 * t143 / t70 / 0.9216e4 + params.A1 / t321 * t324 * t315 / 0.221184e6 - t140 * t143 * t311 / 0.13824e5 + params.A2 * t331 * t89 / 0.165888e6 - 0.7e1 / 0.7962624e7 * params.A2 * t83 * t157 * t331 * params.beta2 + t147 * t89 * t342 / 0.165888e6 + 0.5e1 / 0.191102976e9 * t147 / t88 / t87 * t348 * t331 - t155 * t158 * t342 / 0.3981312e7 + params.A3 * t360 * t103 - 0.2e1 * params.A3 * t363 * t171 + 0.2e1 * t100 / t169 / t102 * t369 * t363 - t100 * t171 * t360
  t381 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t276 * t33 * t105 + t283 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t174 - t293 + t295 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t119 * t376)
  t382 = 0.1e1 / t185
  t383 = t188 ** 2
  t387 = f.my_piecewise5(t15, 0, t11, 0, -t271)
  t391 = f.my_piecewise3(t184, 0, 0.10e2 / 0.9e1 * t382 * t383 + 0.5e1 / 0.3e1 * t186 * t387)
  t398 = t6 * t191 * t114 * t250
  t403 = t6 * t255 * t289 * t250 / 0.30e2
  t405 = f.my_piecewise3(t181, 0, 0.3e1 / 0.20e2 * t6 * t391 * t33 * t250 + t398 / 0.5e1 - t403)
  d11 = 0.2e1 * t179 + 0.2e1 * t261 + t7 * (t381 + t405)
  t408 = -t8 - t26
  t409 = f.my_piecewise5(t11, 0, t15, 0, t408)
  t412 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t409)
  t413 = t412 * t33
  t418 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t413 * t105 + t118)
  t420 = f.my_piecewise5(t15, 0, t11, 0, -t408)
  t423 = f.my_piecewise3(t184, 0, 0.5e1 / 0.3e1 * t186 * t420)
  t424 = t423 * t33
  t428 = t255 * t33
  t430 = 0.1e1 / t195 / t210
  t432 = t40 * s2 * t430
  t439 = 0.16e2 / 0.3e1 * t52 * t201 / t194 / t202 / t193
  t442 = t209 / t194 / t202
  t445 = -t439 - 0.10e2 / 0.3e1 * t60 * t442
  t449 = params.A1 * t217
  t452 = 0.1e1 / t221 / t220 * params.beta1
  t456 = params.A2 * t226
  t459 = -t439 - 0.10e2 / 0.3e1 * t78 * t442
  t464 = params.A2 * t229 * t226
  t466 = 0.1e1 / t234 / t232
  t467 = t466 * params.beta2
  t475 = -t432 / 0.9e1 - 0.5e1 / 0.72e2 * t92 * t238 * t197
  t478 = t247 ** 2
  t480 = 0.1e1 / t478 * params.beta3
  t483 = -0.5e1 / 0.27e2 * t432 + params.A1 * t445 * t222 / 0.576e3 - t449 * t452 * t445 / 0.13824e5 + t456 * t235 * t459 / 0.165888e6 - t464 * t467 * t459 / 0.3981312e7 + params.A3 * t475 * t248 - t245 * t480 * t475
  t488 = f.my_piecewise3(t181, 0, 0.3e1 / 0.20e2 * t6 * t424 * t250 + t259 + 0.3e1 / 0.20e2 * t6 * t428 * t483)
  t492 = 0.2e1 * t269
  t493 = f.my_piecewise5(t11, 0, t15, 0, t492)
  t497 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t263 * t409 * t28 + 0.5e1 / 0.3e1 * t23 * t493)
  t504 = t6 * t412 * t114 * t105
  t512 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t497 * t33 * t105 + t504 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t413 * t174 + t283 / 0.10e2 - t293 + t295 / 0.10e2)
  t516 = f.my_piecewise5(t15, 0, t11, 0, -t492)
  t520 = f.my_piecewise3(t184, 0, 0.10e2 / 0.9e1 * t382 * t420 * t188 + 0.5e1 / 0.3e1 * t186 * t516)
  t527 = t6 * t423 * t114 * t250
  t534 = t6 * t256 * t483
  t537 = f.my_piecewise3(t181, 0, 0.3e1 / 0.20e2 * t6 * t520 * t33 * t250 + t527 / 0.10e2 + t398 / 0.10e2 - t403 + 0.3e1 / 0.20e2 * t6 * t192 * t483 + t534 / 0.10e2)
  d12 = t179 + t261 + t418 + t488 + t7 * (t512 + t537)
  t542 = t409 ** 2
  t546 = 0.2e1 * t25 + 0.2e1 * t269
  t547 = f.my_piecewise5(t11, 0, t15, 0, t546)
  t551 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t263 * t542 + 0.5e1 / 0.3e1 * t23 * t547)
  t558 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t551 * t33 * t105 + t504 / 0.5e1 - t293)
  t559 = t420 ** 2
  t563 = f.my_piecewise5(t15, 0, t11, 0, -t546)
  t567 = f.my_piecewise3(t184, 0, 0.10e2 / 0.9e1 * t382 * t559 + 0.5e1 / 0.3e1 * t186 * t563)
  t580 = t40 * s2 / t195 / t202
  t587 = 0.304e3 / 0.9e1 * t52 * t201 / t194 / t202 / t210
  t588 = t209 * t205
  t591 = t587 + 0.130e3 / 0.9e1 * t60 * t588
  t595 = t445 ** 2
  t601 = t221 ** 2
  t610 = t459 ** 2
  t621 = t587 + 0.130e3 / 0.9e1 * t78 * t588
  t638 = 0.11e2 / 0.27e2 * t580 + 0.5e1 / 0.27e2 * t92 * t238 * t430
  t641 = t475 ** 2
  t653 = 0.55e2 / 0.81e2 * t580 + params.A1 * t591 * t222 / 0.576e3 - params.A1 * t595 * t452 / t217 / 0.9216e4 + params.A1 / t601 * t324 * t595 / 0.221184e6 - t449 * t452 * t591 / 0.13824e5 + params.A2 * t610 * t235 / 0.165888e6 - 0.7e1 / 0.7962624e7 * params.A2 * t229 * t466 * t610 * params.beta2 + t456 * t235 * t621 / 0.165888e6 + 0.5e1 / 0.191102976e9 * t456 / t234 / t233 * t348 * t610 - t464 * t467 * t621 / 0.3981312e7 + params.A3 * t638 * t248 - 0.2e1 * params.A3 * t641 * t480 + 0.2e1 * t245 / t478 / t247 * t369 * t641 - t245 * t480 * t638
  t658 = f.my_piecewise3(t181, 0, 0.3e1 / 0.20e2 * t6 * t567 * t33 * t250 + t527 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t424 * t483 - t403 + t534 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t428 * t653)
  d22 = 0.2e1 * t418 + 0.2e1 * t488 + t7 * (t558 + t658)
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
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
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
  t23 = 0.1e1 / t22
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t27 = -t17 * t25 + t8
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t29 = t28 ** 2
  t32 = t22 ** 2
  t34 = 0.1e1 / t24 / t7
  t37 = 0.2e1 * t17 * t34 - 0.2e1 * t25
  t38 = f.my_piecewise5(t11, 0, t15, 0, t37)
  t42 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t23 * t29 + 0.5e1 / 0.3e1 * t32 * t38)
  t43 = t7 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = t42 * t44
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
  t58 = t51 * s0 * t56
  t60 = t46 ** 2
  t62 = 0.1e1 / t48 / t47
  t63 = t60 * t62
  t64 = s0 ** 2
  t65 = t52 ** 2
  t66 = t65 * r0
  t68 = 0.1e1 / t53 / t66
  t70 = t63 * t64 * t68
  t71 = params.a * t60
  t72 = l0 ** 2
  t73 = t62 * t72
  t74 = t52 * r0
  t77 = t73 / t53 / t74
  t79 = t71 * t77 + t70
  t81 = jnp.sqrt(t79)
  t84 = 0.1e1 + params.beta1 * t81 / 0.24e2
  t85 = t84 ** 2
  t86 = 0.1e1 / t85
  t89 = params.b * t60
  t91 = t89 * t77 + t70
  t92 = t91 ** 2
  t94 = jnp.sqrt(t91)
  t97 = 0.1e1 + params.beta2 * t94 / 0.24e2
  t98 = t97 ** 2
  t99 = t98 ** 2
  t100 = 0.1e1 / t99
  t103 = params.c * t46
  t104 = t50 * l0
  t110 = t58 / 0.24e2 + t103 * t104 / t54 / r0 / 0.24e2
  t111 = params.A3 * t110
  t113 = params.beta3 * t110 + 0.1e1
  t114 = 0.1e1 / t113
  t116 = 0.5e1 / 0.72e2 * t58 + params.A0 + params.A1 * t79 * t86 / 0.576e3 + params.A2 * t92 * t100 / 0.331776e6 + t111 * t114
  t122 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t123 = 0.1e1 / t43
  t124 = t122 * t123
  t128 = t122 * t44
  t130 = 0.1e1 / t54 / t74
  t132 = t51 * s0 * t130
  t136 = 0.1e1 / t53 / t65 / t52
  t139 = 0.16e2 / 0.3e1 * t63 * t64 * t136
  t142 = t73 / t53 / t65
  t145 = -t139 - 0.10e2 / 0.3e1 * t71 * t142
  t149 = params.A1 * t81
  t151 = 0.1e1 / t85 / t84
  t152 = t151 * params.beta1
  t156 = params.A2 * t91
  t159 = -t139 - 0.10e2 / 0.3e1 * t89 * t142
  t164 = params.A2 * t94 * t91
  t166 = 0.1e1 / t99 / t97
  t167 = t166 * params.beta2
  t175 = -t132 / 0.9e1 - 0.5e1 / 0.72e2 * t103 * t104 * t56
  t178 = t113 ** 2
  t180 = 0.1e1 / t178 * params.beta3
  t181 = t180 * t175
  t183 = -0.5e1 / 0.27e2 * t132 + params.A1 * t145 * t86 / 0.576e3 - t149 * t152 * t145 / 0.13824e5 + t156 * t100 * t159 / 0.165888e6 - t164 * t167 * t159 / 0.3981312e7 + params.A3 * t175 * t114 - t111 * t181
  t187 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t188 = t187 ** 2
  t189 = t188 * f.p.zeta_threshold
  t191 = f.my_piecewise3(t21, t189, t32 * t20)
  t193 = 0.1e1 / t43 / t7
  t194 = t191 * t193
  t198 = t191 * t123
  t202 = t191 * t44
  t204 = 0.1e1 / t54 / t65
  t206 = t51 * s0 * t204
  t213 = 0.304e3 / 0.9e1 * t63 * t64 / t53 / t65 / t74
  t214 = t73 * t68
  t217 = t213 + 0.130e3 / 0.9e1 * t71 * t214
  t218 = params.A1 * t217
  t221 = t145 ** 2
  t223 = 0.1e1 / t81
  t227 = t85 ** 2
  t228 = 0.1e1 / t227
  t229 = params.A1 * t228
  t230 = params.beta1 ** 2
  t237 = t159 ** 2
  t241 = params.A2 * t94
  t248 = t213 + 0.130e3 / 0.9e1 * t89 * t214
  t249 = t100 * t248
  t253 = 0.1e1 / t99 / t98
  t254 = params.beta2 ** 2
  t266 = 0.11e2 / 0.27e2 * t206 + 0.5e1 / 0.27e2 * t103 * t104 * t130
  t267 = params.A3 * t266
  t269 = t175 ** 2
  t274 = 0.1e1 / t178 / t113
  t275 = params.beta3 ** 2
  t276 = t274 * t275
  t282 = 0.55e2 / 0.81e2 * t206 + t218 * t86 / 0.576e3 - params.A1 * t221 * t152 * t223 / 0.9216e4 + t229 * t230 * t221 / 0.221184e6 - t149 * t152 * t217 / 0.13824e5 + params.A2 * t237 * t100 / 0.165888e6 - 0.7e1 / 0.7962624e7 * t241 * t166 * t237 * params.beta2 + t156 * t249 / 0.165888e6 + 0.5e1 / 0.191102976e9 * t156 * t253 * t254 * t237 - t164 * t167 * t248 / 0.3981312e7 + t267 * t114 - 0.2e1 * params.A3 * t269 * t180 + 0.2e1 * t111 * t276 * t269 - t111 * t180 * t266
  t287 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t116 + t6 * t124 * t116 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t128 * t183 - t6 * t194 * t116 / 0.30e2 + t6 * t198 * t183 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t202 * t282)
  t289 = r1 <= f.p.dens_threshold
  t290 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t291 = 0.1e1 + t290
  t292 = t291 <= f.p.zeta_threshold
  t293 = t291 ** (0.1e1 / 0.3e1)
  t294 = 0.1e1 / t293
  t296 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t297 = t296 ** 2
  t300 = t293 ** 2
  t302 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t306 = f.my_piecewise3(t292, 0, 0.10e2 / 0.9e1 * t294 * t297 + 0.5e1 / 0.3e1 * t300 * t302)
  t308 = r1 ** 2
  t309 = r1 ** (0.1e1 / 0.3e1)
  t310 = t309 ** 2
  t314 = t51 * s2 / t310 / t308
  t316 = s2 ** 2
  t317 = t308 ** 2
  t322 = t63 * t316 / t309 / t317 / r1
  t323 = l1 ** 2
  t328 = t62 * t323 / t309 / t308 / r1
  t330 = t71 * t328 + t322
  t332 = jnp.sqrt(t330)
  t336 = (0.1e1 + params.beta1 * t332 / 0.24e2) ** 2
  t341 = t89 * t328 + t322
  t342 = t341 ** 2
  t344 = jnp.sqrt(t341)
  t348 = (0.1e1 + params.beta2 * t344 / 0.24e2) ** 2
  t349 = t348 ** 2
  t359 = t314 / 0.24e2 + t103 * t50 * l1 / t310 / r1 / 0.24e2
  t365 = 0.5e1 / 0.72e2 * t314 + params.A0 + params.A1 * t330 / t336 / 0.576e3 + params.A2 * t342 / t349 / 0.331776e6 + params.A3 * t359 / (params.beta3 * t359 + 0.1e1)
  t371 = f.my_piecewise3(t292, 0, 0.5e1 / 0.3e1 * t300 * t296)
  t377 = f.my_piecewise3(t292, t189, t300 * t291)
  t383 = f.my_piecewise3(t289, 0, 0.3e1 / 0.20e2 * t6 * t306 * t44 * t365 + t6 * t371 * t123 * t365 / 0.5e1 - t6 * t377 * t193 * t365 / 0.30e2)
  t393 = t24 ** 2
  t397 = 0.6e1 * t34 - 0.6e1 * t17 / t393
  t398 = f.my_piecewise5(t11, 0, t15, 0, t397)
  t402 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t398)
  t425 = 0.1e1 / t43 / t24
  t436 = t65 ** 2
  t441 = 0.6688e4 / 0.27e2 * t63 * t64 / t53 / t436
  t442 = t73 * t136
  t445 = -t441 - 0.2080e4 / 0.27e2 * t71 * t442
  t452 = t51 * s0 / t54 / t66
  t457 = -0.154e3 / 0.81e2 * t452 - 0.55e2 / 0.81e2 * t103 * t104 * t204
  t468 = t221 * t145
  t476 = t237 * t159
  t492 = -t441 - 0.2080e4 / 0.27e2 * t89 * t442
  t500 = params.A1 * t468
  t506 = params.A1 * t445 * t86 / 0.576e3 + params.A3 * t457 * t114 + t229 * t230 * t145 * t217 / 0.73728e5 - params.A1 / t227 / t84 * t230 * params.beta1 * t468 * t223 / 0.2654208e7 - t149 * t152 * t445 / 0.13824e5 - 0.5e1 / 0.5308416e7 * params.A2 * t476 * t167 / t94 - 0.5e1 / 0.1528823808e10 * t241 / t99 / t98 / t97 * t254 * params.beta2 * t476 - t164 * t167 * t492 / 0.3981312e7 - 0.6e1 * t267 * t181 - t111 * t180 * t457 + t500 * t228 * t230 / t79 / 0.147456e6
  t518 = t178 ** 2
  t522 = t269 * t175
  t554 = params.A2 * t159 * t249 / 0.55296e5 + 0.5e1 / 0.42467328e8 * params.A2 * t253 * t476 * t254 + t156 * t100 * t492 / 0.165888e6 - 0.770e3 / 0.243e3 * t452 - 0.6e1 * t111 / t518 * t275 * params.beta3 * t522 - t218 * t151 * params.beta1 * t223 * t145 / 0.3072e4 + t500 * t152 / t81 / t79 / 0.18432e5 - 0.7e1 / 0.2654208e7 * t241 * t166 * t159 * params.beta2 * t248 + 0.5e1 / 0.63700992e8 * t156 * t253 * t254 * t159 * t248 + 0.6e1 * params.A3 * t522 * t276 + 0.6e1 * t111 * t274 * t275 * t175 * t266
  t560 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t402 * t44 * t116 + 0.3e1 / 0.10e2 * t6 * t42 * t123 * t116 + 0.9e1 / 0.20e2 * t6 * t45 * t183 - t6 * t122 * t193 * t116 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t124 * t183 + 0.9e1 / 0.20e2 * t6 * t128 * t282 + 0.2e1 / 0.45e2 * t6 * t191 * t425 * t116 - t6 * t194 * t183 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t198 * t282 + 0.3e1 / 0.20e2 * t6 * t202 * (t506 + t554))
  t570 = f.my_piecewise5(t15, 0, t11, 0, -t397)
  t574 = f.my_piecewise3(t292, 0, -0.10e2 / 0.27e2 / t293 / t291 * t297 * t296 + 0.10e2 / 0.3e1 * t294 * t296 * t302 + 0.5e1 / 0.3e1 * t300 * t570)
  t592 = f.my_piecewise3(t289, 0, 0.3e1 / 0.20e2 * t6 * t574 * t44 * t365 + 0.3e1 / 0.10e2 * t6 * t306 * t123 * t365 - t6 * t371 * t193 * t365 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t377 * t425 * t365)
  d111 = 0.3e1 * t287 + 0.3e1 * t383 + t7 * (t560 + t592)

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
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
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
  t24 = 0.1e1 / t22 / t20
  t25 = t7 ** 2
  t26 = 0.1e1 / t25
  t28 = -t17 * t26 + t8
  t29 = f.my_piecewise5(t11, 0, t15, 0, t28)
  t30 = t29 ** 2
  t34 = 0.1e1 / t22
  t35 = t34 * t29
  t36 = t25 * t7
  t37 = 0.1e1 / t36
  t40 = 0.2e1 * t17 * t37 - 0.2e1 * t26
  t41 = f.my_piecewise5(t11, 0, t15, 0, t40)
  t44 = t22 ** 2
  t45 = t25 ** 2
  t46 = 0.1e1 / t45
  t49 = -0.6e1 * t17 * t46 + 0.6e1 * t37
  t50 = f.my_piecewise5(t11, 0, t15, 0, t49)
  t54 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 * t24 * t30 * t29 + 0.10e2 / 0.3e1 * t35 * t41 + 0.5e1 / 0.3e1 * t44 * t50)
  t55 = t7 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = t54 * t56
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
  t70 = t63 * s0 * t68
  t72 = t58 ** 2
  t74 = 0.1e1 / t60 / t59
  t75 = t72 * t74
  t76 = s0 ** 2
  t77 = t64 ** 2
  t78 = t77 * r0
  t80 = 0.1e1 / t65 / t78
  t82 = t75 * t76 * t80
  t83 = params.a * t72
  t84 = l0 ** 2
  t85 = t74 * t84
  t86 = t64 * r0
  t89 = t85 / t65 / t86
  t91 = t83 * t89 + t82
  t93 = jnp.sqrt(t91)
  t96 = 0.1e1 + params.beta1 * t93 / 0.24e2
  t97 = t96 ** 2
  t98 = 0.1e1 / t97
  t101 = params.b * t72
  t103 = t101 * t89 + t82
  t104 = t103 ** 2
  t106 = jnp.sqrt(t103)
  t109 = 0.1e1 + params.beta2 * t106 / 0.24e2
  t110 = t109 ** 2
  t111 = t110 ** 2
  t112 = 0.1e1 / t111
  t115 = params.c * t58
  t116 = t62 * l0
  t122 = t70 / 0.24e2 + t115 * t116 / t66 / r0 / 0.24e2
  t123 = params.A3 * t122
  t125 = params.beta3 * t122 + 0.1e1
  t126 = 0.1e1 / t125
  t128 = 0.5e1 / 0.72e2 * t70 + params.A0 + params.A1 * t91 * t98 / 0.576e3 + params.A2 * t104 * t112 / 0.331776e6 + t123 * t126
  t137 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t138 = 0.1e1 / t55
  t139 = t137 * t138
  t143 = t137 * t56
  t145 = 0.1e1 / t66 / t86
  t147 = t63 * s0 * t145
  t149 = t77 * t64
  t151 = 0.1e1 / t65 / t149
  t154 = 0.16e2 / 0.3e1 * t75 * t76 * t151
  t157 = t85 / t65 / t77
  t160 = -t154 - 0.10e2 / 0.3e1 * t83 * t157
  t164 = params.A1 * t93
  t166 = 0.1e1 / t97 / t96
  t167 = t166 * params.beta1
  t171 = params.A2 * t103
  t174 = -t154 - 0.10e2 / 0.3e1 * t101 * t157
  t178 = t106 * t103
  t179 = params.A2 * t178
  t181 = 0.1e1 / t111 / t109
  t182 = t181 * params.beta2
  t190 = -t147 / 0.9e1 - 0.5e1 / 0.72e2 * t115 * t116 * t68
  t193 = t125 ** 2
  t195 = 0.1e1 / t193 * params.beta3
  t196 = t195 * t190
  t198 = -0.5e1 / 0.27e2 * t147 + params.A1 * t160 * t98 / 0.576e3 - t164 * t167 * t160 / 0.13824e5 + t171 * t112 * t174 / 0.165888e6 - t179 * t182 * t174 / 0.3981312e7 + params.A3 * t190 * t126 - t123 * t196
  t204 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t206 = 0.1e1 / t55 / t7
  t207 = t204 * t206
  t211 = t204 * t138
  t215 = t204 * t56
  t217 = 0.1e1 / t66 / t77
  t219 = t63 * s0 * t217
  t223 = 0.1e1 / t65 / t77 / t86
  t226 = 0.304e3 / 0.9e1 * t75 * t76 * t223
  t227 = t85 * t80
  t230 = t226 + 0.130e3 / 0.9e1 * t83 * t227
  t231 = params.A1 * t230
  t234 = t160 ** 2
  t235 = params.A1 * t234
  t236 = 0.1e1 / t93
  t237 = t167 * t236
  t240 = t97 ** 2
  t241 = 0.1e1 / t240
  t242 = params.A1 * t241
  t243 = params.beta1 ** 2
  t250 = t174 ** 2
  t251 = params.A2 * t250
  t254 = params.A2 * t106
  t261 = t226 + 0.130e3 / 0.9e1 * t101 * t227
  t262 = t112 * t261
  t266 = 0.1e1 / t111 / t110
  t267 = params.beta2 ** 2
  t268 = t266 * t267
  t279 = 0.11e2 / 0.27e2 * t219 + 0.5e1 / 0.27e2 * t115 * t116 * t145
  t280 = params.A3 * t279
  t282 = t190 ** 2
  t287 = 0.1e1 / t193 / t125
  t288 = params.beta3 ** 2
  t289 = t287 * t288
  t290 = t289 * t282
  t295 = 0.55e2 / 0.81e2 * t219 + t231 * t98 / 0.576e3 - t235 * t237 / 0.9216e4 + t242 * t243 * t234 / 0.221184e6 - t164 * t167 * t230 / 0.13824e5 + t251 * t112 / 0.165888e6 - 0.7e1 / 0.7962624e7 * t254 * t181 * t250 * params.beta2 + t171 * t262 / 0.165888e6 + 0.5e1 / 0.191102976e9 * t171 * t268 * t250 - t179 * t182 * t261 / 0.3981312e7 + t280 * t126 - 0.2e1 * params.A3 * t282 * t195 + 0.2e1 * t123 * t290 - t123 * t195 * t279
  t299 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t300 = t299 ** 2
  t301 = t300 * f.p.zeta_threshold
  t303 = f.my_piecewise3(t21, t301, t44 * t20)
  t305 = 0.1e1 / t55 / t25
  t306 = t303 * t305
  t310 = t303 * t206
  t314 = t303 * t138
  t318 = t303 * t56
  t319 = t77 ** 2
  t324 = 0.6688e4 / 0.27e2 * t75 * t76 / t65 / t319
  t325 = t85 * t151
  t328 = -t324 - 0.2080e4 / 0.27e2 * t83 * t325
  t329 = params.A1 * t328
  t333 = 0.1e1 / t66 / t78
  t335 = t63 * s0 * t333
  t340 = -0.154e3 / 0.81e2 * t335 - 0.55e2 / 0.81e2 * t115 * t116 * t217
  t341 = params.A3 * t340
  t343 = t243 * t160
  t349 = params.A1 / t240 / t96
  t350 = t243 * params.beta1
  t351 = t234 * t160
  t359 = t250 * t174
  t361 = 0.1e1 / t106
  t367 = 0.1e1 / t111 / t110 / t109
  t368 = t267 * params.beta2
  t369 = t367 * t368
  t375 = -t324 - 0.2080e4 / 0.27e2 * t101 * t325
  t383 = params.A1 * t351
  t384 = t241 * t243
  t385 = 0.1e1 / t91
  t389 = t329 * t98 / 0.576e3 + t341 * t126 + t242 * t343 * t230 / 0.73728e5 - t349 * t350 * t351 * t236 / 0.2654208e7 - t164 * t167 * t328 / 0.13824e5 - 0.5e1 / 0.5308416e7 * params.A2 * t359 * t182 * t361 - 0.5e1 / 0.1528823808e10 * t254 * t369 * t359 - t179 * t182 * t375 / 0.3981312e7 - 0.6e1 * t280 * t196 - t123 * t195 * t340 + t383 * t384 * t385 / 0.147456e6
  t390 = params.A2 * t174
  t393 = params.A2 * t266
  t397 = t112 * t375
  t401 = t193 ** 2
  t402 = 0.1e1 / t401
  t403 = t288 * params.beta3
  t404 = t402 * t403
  t405 = t282 * t190
  t409 = t231 * t166
  t411 = params.beta1 * t236 * t160
  t415 = 0.1e1 / t93 / t91
  t419 = t254 * t181
  t424 = t171 * t266
  t432 = t123 * t287
  t437 = t390 * t262 / 0.55296e5 + 0.5e1 / 0.42467328e8 * t393 * t359 * t267 + t171 * t397 / 0.165888e6 - 0.770e3 / 0.243e3 * t335 - 0.6e1 * t123 * t404 * t405 - t409 * t411 / 0.3072e4 + t383 * t167 * t415 / 0.18432e5 - 0.7e1 / 0.2654208e7 * t419 * t174 * params.beta2 * t261 + 0.5e1 / 0.63700992e8 * t424 * t267 * t174 * t261 + 0.6e1 * params.A3 * t405 * t289 + 0.6e1 * t432 * t288 * t190 * t279
  t438 = t389 + t437
  t443 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t128 + 0.3e1 / 0.10e2 * t6 * t139 * t128 + 0.9e1 / 0.20e2 * t6 * t143 * t198 - t6 * t207 * t128 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t211 * t198 + 0.9e1 / 0.20e2 * t6 * t215 * t295 + 0.2e1 / 0.45e2 * t6 * t306 * t128 - t6 * t310 * t198 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t314 * t295 + 0.3e1 / 0.20e2 * t6 * t318 * t438)
  t445 = r1 <= f.p.dens_threshold
  t446 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t447 = 0.1e1 + t446
  t448 = t447 <= f.p.zeta_threshold
  t449 = t447 ** (0.1e1 / 0.3e1)
  t451 = 0.1e1 / t449 / t447
  t453 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t454 = t453 ** 2
  t458 = 0.1e1 / t449
  t459 = t458 * t453
  t461 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t464 = t449 ** 2
  t466 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t470 = f.my_piecewise3(t448, 0, -0.10e2 / 0.27e2 * t451 * t454 * t453 + 0.10e2 / 0.3e1 * t459 * t461 + 0.5e1 / 0.3e1 * t464 * t466)
  t472 = r1 ** 2
  t473 = r1 ** (0.1e1 / 0.3e1)
  t474 = t473 ** 2
  t478 = t63 * s2 / t474 / t472
  t480 = s2 ** 2
  t481 = t472 ** 2
  t486 = t75 * t480 / t473 / t481 / r1
  t487 = l1 ** 2
  t492 = t74 * t487 / t473 / t472 / r1
  t494 = t83 * t492 + t486
  t496 = jnp.sqrt(t494)
  t500 = (0.1e1 + params.beta1 * t496 / 0.24e2) ** 2
  t505 = t101 * t492 + t486
  t506 = t505 ** 2
  t508 = jnp.sqrt(t505)
  t512 = (0.1e1 + params.beta2 * t508 / 0.24e2) ** 2
  t513 = t512 ** 2
  t523 = t478 / 0.24e2 + t115 * t62 * l1 / t474 / r1 / 0.24e2
  t529 = 0.5e1 / 0.72e2 * t478 + params.A0 + params.A1 * t494 / t500 / 0.576e3 + params.A2 * t506 / t513 / 0.331776e6 + params.A3 * t523 / (params.beta3 * t523 + 0.1e1)
  t538 = f.my_piecewise3(t448, 0, 0.10e2 / 0.9e1 * t458 * t454 + 0.5e1 / 0.3e1 * t464 * t461)
  t545 = f.my_piecewise3(t448, 0, 0.5e1 / 0.3e1 * t464 * t453)
  t551 = f.my_piecewise3(t448, t301, t464 * t447)
  t557 = f.my_piecewise3(t445, 0, 0.3e1 / 0.20e2 * t6 * t470 * t56 * t529 + 0.3e1 / 0.10e2 * t6 * t538 * t138 * t529 - t6 * t545 * t206 * t529 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t551 * t305 * t529)
  t559 = t20 ** 2
  t562 = t30 ** 2
  t568 = t41 ** 2
  t577 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t578 = f.my_piecewise5(t11, 0, t15, 0, t577)
  t582 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t559 * t562 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t568 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t578)
  t616 = t230 ** 2
  t620 = t234 ** 2
  t621 = params.A1 * t620
  t622 = t91 ** 2
  t628 = t261 ** 2
  t636 = t279 ** 2
  t647 = t243 ** 2
  t657 = 0.167200e6 / 0.81e2 * t75 * t76 / t65 / t319 / r0
  t658 = t85 * t223
  t661 = t657 + 0.39520e5 / 0.81e2 * t83 * t658
  t665 = t250 ** 2
  t666 = params.A2 * t665
  t673 = t657 + 0.39520e5 / 0.81e2 * t101 * t658
  t680 = t63 * s0 / t66 / t149
  t685 = 0.2618e4 / 0.243e3 * t680 + 0.770e3 / 0.243e3 * t115 * t116 * t333
  t694 = t288 ** 2
  t696 = t282 ** 2
  t717 = 0.36e2 * t280 * t290 - params.A1 * t616 * t237 / 0.3072e4 - t621 * t167 / t93 / t622 / 0.12288e5 - 0.7e1 / 0.2654208e7 * t254 * t181 * t628 * params.beta2 + 0.5e1 / 0.63700992e8 * t171 * t268 * t628 + 0.6e1 * t123 * t289 * t636 - t621 * t384 / t622 / 0.98304e5 + 0.5e1 / 0.127401984e9 * params.A1 / t240 / t97 * t647 * t620 * t385 - t164 * t167 * t661 / 0.13824e5 + 0.25e2 / 0.254803968e9 * t666 * t268 / t103 - t179 * t182 * t673 / 0.3981312e7 - t123 * t195 * t685 + 0.5e1 / 0.7077888e7 * t393 * t250 * t267 * t261 + 0.24e2 * t123 / t401 / t125 * t694 * t696 - 0.8e1 * t341 * t196 + t242 * t343 * t328 / 0.55296e5 - t349 * t350 * t620 * t415 / 0.2654208e7 + 0.5e1 / 0.10616832e8 * t666 * t182 / t178 - 0.25e2 / 0.1528823808e10 * params.A2 * t361 * t369 * t665
  t772 = t111 ** 2
  t775 = t267 ** 2
  t792 = -0.36e2 * t123 * t402 * t403 * t282 * t279 + t409 * params.beta1 * t415 * t234 / 0.3072e4 + 0.8e1 * t432 * t288 * t340 * t190 - t329 * t166 * t411 / 0.2304e4 - t349 * t350 * t234 * t230 * t236 / 0.442368e6 - 0.5e1 / 0.884736e6 * t251 * t181 * params.beta2 * t361 * t261 - 0.5e1 / 0.254803968e9 * t254 * t367 * t368 * t250 * t261 - 0.7e1 / 0.1990656e7 * t419 * params.beta2 * t375 * t174 + 0.5e1 / 0.47775744e8 * t424 * t267 * t375 * t174 + t235 * t241 * t243 * t385 * t230 / 0.24576e5 + 0.13090e5 / 0.729e3 * t680 + t242 * t243 * t616 / 0.73728e5 - 0.6e1 * params.A3 * t636 * t195 - 0.24e2 * params.A3 * t696 * t404 + 0.35e2 / 0.73383542784e11 * params.A2 / t772 * t775 * t665 + t390 * t397 / 0.41472e5 + t171 * t112 * t673 / 0.165888e6 + params.A2 * t628 * t112 / 0.55296e5 + params.A1 * t661 * t98 / 0.576e3 + params.A3 * t685 * t126
  t810 = 0.1e1 / t55 / t36
  t815 = 0.3e1 / 0.20e2 * t6 * t582 * t56 * t128 + 0.3e1 / 0.5e1 * t6 * t57 * t198 + 0.6e1 / 0.5e1 * t6 * t139 * t198 + 0.9e1 / 0.10e2 * t6 * t143 * t295 - 0.2e1 / 0.5e1 * t6 * t207 * t198 + 0.6e1 / 0.5e1 * t6 * t211 * t295 + 0.3e1 / 0.5e1 * t6 * t215 * t438 + 0.8e1 / 0.45e2 * t6 * t306 * t198 - t6 * t310 * t295 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t314 * t438 + 0.3e1 / 0.20e2 * t6 * t318 * (t717 + t792) + 0.2e1 / 0.5e1 * t6 * t54 * t138 * t128 - t6 * t137 * t206 * t128 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t204 * t305 * t128 - 0.14e2 / 0.135e3 * t6 * t303 * t810 * t128
  t816 = f.my_piecewise3(t1, 0, t815)
  t817 = t447 ** 2
  t820 = t454 ** 2
  t826 = t461 ** 2
  t832 = f.my_piecewise5(t15, 0, t11, 0, -t577)
  t836 = f.my_piecewise3(t448, 0, 0.40e2 / 0.81e2 / t449 / t817 * t820 - 0.20e2 / 0.9e1 * t451 * t454 * t461 + 0.10e2 / 0.3e1 * t458 * t826 + 0.40e2 / 0.9e1 * t459 * t466 + 0.5e1 / 0.3e1 * t464 * t832)
  t858 = f.my_piecewise3(t445, 0, 0.3e1 / 0.20e2 * t6 * t836 * t56 * t529 + 0.2e1 / 0.5e1 * t6 * t470 * t138 * t529 - t6 * t538 * t206 * t529 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t545 * t305 * t529 - 0.14e2 / 0.135e3 * t6 * t551 * t810 * t529)
  d1111 = 0.4e1 * t443 + 0.4e1 * t557 + t7 * (t816 + t858)

  res = {'v4rho4': d1111}
  return res
