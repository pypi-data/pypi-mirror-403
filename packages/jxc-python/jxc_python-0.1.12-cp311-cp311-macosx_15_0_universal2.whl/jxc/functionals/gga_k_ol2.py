"""Generated from gga_k_ol2.mpl."""

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
  params_aa_raw = params.aa
  if isinstance(params_aa_raw, (str, bytes, dict)):
    params_aa = params_aa_raw
  else:
    try:
      params_aa_seq = list(params_aa_raw)
    except TypeError:
      params_aa = params_aa_raw
    else:
      params_aa_seq = np.asarray(params_aa_seq, dtype=np.float64)
      params_aa = np.concatenate((np.array([np.nan], dtype=np.float64), params_aa_seq))
  params_bb_raw = params.bb
  if isinstance(params_bb_raw, (str, bytes, dict)):
    params_bb = params_bb_raw
  else:
    try:
      params_bb_seq = list(params_bb_raw)
    except TypeError:
      params_bb = params_bb_raw
    else:
      params_bb_seq = np.asarray(params_bb_seq, dtype=np.float64)
      params_bb = np.concatenate((np.array([np.nan], dtype=np.float64), params_bb_seq))
  params_cc_raw = params.cc
  if isinstance(params_cc_raw, (str, bytes, dict)):
    params_cc = params_cc_raw
  else:
    try:
      params_cc_seq = list(params_cc_raw)
    except TypeError:
      params_cc = params_cc_raw
    else:
      params_cc_seq = np.asarray(params_cc_seq, dtype=np.float64)
      params_cc = np.concatenate((np.array([np.nan], dtype=np.float64), params_cc_seq))

  ol2_f = lambda x: +params_aa + params_bb * x ** 2 / 72.0 + params_cc * x / (2 ** (1 / 3) + 4 * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, ol2_f, rs, zeta, xs0, xs1)

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
  params_aa_raw = params.aa
  if isinstance(params_aa_raw, (str, bytes, dict)):
    params_aa = params_aa_raw
  else:
    try:
      params_aa_seq = list(params_aa_raw)
    except TypeError:
      params_aa = params_aa_raw
    else:
      params_aa_seq = np.asarray(params_aa_seq, dtype=np.float64)
      params_aa = np.concatenate((np.array([np.nan], dtype=np.float64), params_aa_seq))
  params_bb_raw = params.bb
  if isinstance(params_bb_raw, (str, bytes, dict)):
    params_bb = params_bb_raw
  else:
    try:
      params_bb_seq = list(params_bb_raw)
    except TypeError:
      params_bb = params_bb_raw
    else:
      params_bb_seq = np.asarray(params_bb_seq, dtype=np.float64)
      params_bb = np.concatenate((np.array([np.nan], dtype=np.float64), params_bb_seq))
  params_cc_raw = params.cc
  if isinstance(params_cc_raw, (str, bytes, dict)):
    params_cc = params_cc_raw
  else:
    try:
      params_cc_seq = list(params_cc_raw)
    except TypeError:
      params_cc = params_cc_raw
    else:
      params_cc_seq = np.asarray(params_cc_seq, dtype=np.float64)
      params_cc = np.concatenate((np.array([np.nan], dtype=np.float64), params_cc_seq))

  ol2_f = lambda x: +params_aa + params_bb * x ** 2 / 72.0 + params_cc * x / (2 ** (1 / 3) + 4 * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, ol2_f, rs, zeta, xs0, xs1)

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
  params_aa_raw = params.aa
  if isinstance(params_aa_raw, (str, bytes, dict)):
    params_aa = params_aa_raw
  else:
    try:
      params_aa_seq = list(params_aa_raw)
    except TypeError:
      params_aa = params_aa_raw
    else:
      params_aa_seq = np.asarray(params_aa_seq, dtype=np.float64)
      params_aa = np.concatenate((np.array([np.nan], dtype=np.float64), params_aa_seq))
  params_bb_raw = params.bb
  if isinstance(params_bb_raw, (str, bytes, dict)):
    params_bb = params_bb_raw
  else:
    try:
      params_bb_seq = list(params_bb_raw)
    except TypeError:
      params_bb = params_bb_raw
    else:
      params_bb_seq = np.asarray(params_bb_seq, dtype=np.float64)
      params_bb = np.concatenate((np.array([np.nan], dtype=np.float64), params_bb_seq))
  params_cc_raw = params.cc
  if isinstance(params_cc_raw, (str, bytes, dict)):
    params_cc = params_cc_raw
  else:
    try:
      params_cc_seq = list(params_cc_raw)
    except TypeError:
      params_cc = params_cc_raw
    else:
      params_cc_seq = np.asarray(params_cc_seq, dtype=np.float64)
      params_cc = np.concatenate((np.array([np.nan], dtype=np.float64), params_cc_seq))

  ol2_f = lambda x: +params_aa + params_bb * x ** 2 / 72.0 + params_cc * x / (2 ** (1 / 3) + 4 * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, ol2_f, rs, zeta, xs0, xs1)

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
  t32 = params.bb * s0
  t33 = r0 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t37 = 0.1e1 / t35 / t33
  t40 = jnp.sqrt(s0)
  t41 = params.cc * t40
  t43 = 0.1e1 / t34 / r0
  t44 = 2 ** (0.1e1 / 0.3e1)
  t47 = 0.4e1 * t40 * t43 + t44
  t48 = 0.1e1 / t47
  t49 = t43 * t48
  t51 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t32 * t37 + t41 * t49
  t55 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t51)
  t56 = r1 <= f.p.dens_threshold
  t57 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t58 = 0.1e1 + t57
  t59 = t58 <= f.p.zeta_threshold
  t60 = t58 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t63 = f.my_piecewise3(t59, t24, t61 * t58)
  t64 = t63 * t30
  t65 = params.bb * s2
  t66 = r1 ** 2
  t67 = r1 ** (0.1e1 / 0.3e1)
  t68 = t67 ** 2
  t70 = 0.1e1 / t68 / t66
  t73 = jnp.sqrt(s2)
  t74 = params.cc * t73
  t76 = 0.1e1 / t67 / r1
  t79 = 0.4e1 * t73 * t76 + t44
  t80 = 0.1e1 / t79
  t81 = t76 * t80
  t83 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t65 * t70 + t74 * t81
  t87 = f.my_piecewise3(t56, 0, 0.3e1 / 0.20e2 * t6 * t64 * t83)
  t88 = t7 ** 2
  t90 = t17 / t88
  t91 = t8 - t90
  t92 = f.my_piecewise5(t11, 0, t15, 0, t91)
  t95 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t92)
  t100 = 0.1e1 / t29
  t104 = t6 * t28 * t100 * t51 / 0.10e2
  t107 = 0.1e1 / t35 / t33 / r0
  t116 = t47 ** 2
  t117 = 0.1e1 / t116
  t126 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t95 * t30 * t51 + t104 + 0.3e1 / 0.20e2 * t6 * t31 * (-0.37037037037037037037037037037037037037037037037037e-1 * t32 * t107 - 0.4e1 / 0.3e1 * t41 / t34 / t33 * t48 + 0.16e2 / 0.3e1 * params.cc * s0 * t107 * t117))
  t128 = f.my_piecewise5(t15, 0, t11, 0, -t91)
  t131 = f.my_piecewise3(t59, 0, 0.5e1 / 0.3e1 * t61 * t128)
  t139 = t6 * t63 * t100 * t83 / 0.10e2
  t141 = f.my_piecewise3(t56, 0, 0.3e1 / 0.20e2 * t6 * t131 * t30 * t83 + t139)
  vrho_0_ = t55 + t87 + t7 * (t126 + t141)
  t144 = -t8 - t90
  t145 = f.my_piecewise5(t11, 0, t15, 0, t144)
  t148 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t145)
  t154 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t148 * t30 * t51 + t104)
  t156 = f.my_piecewise5(t15, 0, t11, 0, -t144)
  t159 = f.my_piecewise3(t59, 0, 0.5e1 / 0.3e1 * t61 * t156)
  t166 = 0.1e1 / t68 / t66 / r1
  t175 = t79 ** 2
  t176 = 0.1e1 / t175
  t185 = f.my_piecewise3(t56, 0, 0.3e1 / 0.20e2 * t6 * t159 * t30 * t83 + t139 + 0.3e1 / 0.20e2 * t6 * t64 * (-0.37037037037037037037037037037037037037037037037037e-1 * t65 * t166 - 0.4e1 / 0.3e1 * t74 / t67 / t66 * t80 + 0.16e2 / 0.3e1 * params.cc * s2 * t166 * t176))
  vrho_1_ = t55 + t87 + t7 * (t154 + t185)
  t201 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.13888888888888888888888888888888888888888888888889e-1 * params.bb * t37 + params.cc / t40 * t49 / 0.2e1 - 0.2e1 * params.cc * t37 * t117))
  vsigma_0_ = t7 * t201
  vsigma_1_ = 0.0e0
  t215 = f.my_piecewise3(t56, 0, 0.3e1 / 0.20e2 * t6 * t64 * (0.13888888888888888888888888888888888888888888888889e-1 * params.bb * t70 + params.cc / t73 * t81 / 0.2e1 - 0.2e1 * params.cc * t70 * t176))
  vsigma_2_ = t7 * t215
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
  params_aa_raw = params.aa
  if isinstance(params_aa_raw, (str, bytes, dict)):
    params_aa = params_aa_raw
  else:
    try:
      params_aa_seq = list(params_aa_raw)
    except TypeError:
      params_aa = params_aa_raw
    else:
      params_aa_seq = np.asarray(params_aa_seq, dtype=np.float64)
      params_aa = np.concatenate((np.array([np.nan], dtype=np.float64), params_aa_seq))
  params_bb_raw = params.bb
  if isinstance(params_bb_raw, (str, bytes, dict)):
    params_bb = params_bb_raw
  else:
    try:
      params_bb_seq = list(params_bb_raw)
    except TypeError:
      params_bb = params_bb_raw
    else:
      params_bb_seq = np.asarray(params_bb_seq, dtype=np.float64)
      params_bb = np.concatenate((np.array([np.nan], dtype=np.float64), params_bb_seq))
  params_cc_raw = params.cc
  if isinstance(params_cc_raw, (str, bytes, dict)):
    params_cc = params_cc_raw
  else:
    try:
      params_cc_seq = list(params_cc_raw)
    except TypeError:
      params_cc = params_cc_raw
    else:
      params_cc_seq = np.asarray(params_cc_seq, dtype=np.float64)
      params_cc = np.concatenate((np.array([np.nan], dtype=np.float64), params_cc_seq))

  ol2_f = lambda x: +params_aa + params_bb * x ** 2 / 72.0 + params_cc * x / (2 ** (1 / 3) + 4 * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, ol2_f, rs, zeta, xs0, xs1)

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
  t24 = params.bb * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = r0 ** 2
  t29 = 0.1e1 / t22 / t27
  t33 = jnp.sqrt(s0)
  t34 = params.cc * t33
  t36 = 0.1e1 / t21 / r0
  t41 = 0.4e1 * t33 * t25 * t36 + t25
  t42 = 0.1e1 / t41
  t43 = t25 * t36 * t42
  t45 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t24 * t26 * t29 + t34 * t43
  t49 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t45)
  t58 = t26 / t22 / t27 / r0
  t68 = t41 ** 2
  t69 = 0.1e1 / t68
  t78 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t45 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-0.37037037037037037037037037037037037037037037037037e-1 * t24 * t58 - 0.4e1 / 0.3e1 * t34 * t25 / t21 / t27 * t42 + 0.16e2 / 0.3e1 * params.cc * s0 * t58 * t69))
  vrho_0_ = 0.2e1 * r0 * t78 + 0.2e1 * t49
  t96 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.13888888888888888888888888888888888888888888888889e-1 * params.bb * t26 * t29 + params.cc / t33 * t43 / 0.2e1 - 0.2e1 * params.cc * t26 * t29 * t69))
  vsigma_0_ = 0.2e1 * r0 * t96
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
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
  t24 = params.bb * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = r0 ** 2
  t28 = t21 ** 2
  t30 = 0.1e1 / t28 / t27
  t31 = t26 * t30
  t34 = jnp.sqrt(s0)
  t35 = params.cc * t34
  t37 = 0.1e1 / t21 / r0
  t42 = 0.4e1 * t34 * t25 * t37 + t25
  t43 = 0.1e1 / t42
  t44 = t25 * t37 * t43
  t46 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t24 * t31 + t35 * t44
  t50 = t20 * t28
  t51 = t27 * r0
  t53 = 0.1e1 / t28 / t51
  t54 = t26 * t53
  t60 = t25 / t21 / t27 * t43
  t63 = params.cc * s0
  t64 = t42 ** 2
  t65 = 0.1e1 / t64
  t69 = -0.37037037037037037037037037037037037037037037037037e-1 * t24 * t54 - 0.4e1 / 0.3e1 * t35 * t60 + 0.16e2 / 0.3e1 * t63 * t54 * t65
  t74 = f.my_piecewise3(t2, 0, t7 * t23 * t46 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t50 * t69)
  t83 = t27 ** 2
  t86 = t26 / t28 / t83
  t98 = t34 * s0
  t103 = 0.1e1 / t64 / t42
  t112 = f.my_piecewise3(t2, 0, -t7 * t20 * t37 * t46 / 0.30e2 + t7 * t23 * t69 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t50 * (0.13580246913580246913580246913580246913580246913580e0 * t24 * t86 + 0.28e2 / 0.9e1 * t35 * t25 / t21 / t51 * t43 - 0.80e2 / 0.3e1 * t63 * t86 * t65 + 0.1024e4 / 0.9e1 * params.cc * t98 / t83 / t27 * t103))
  v2rho2_0_ = 0.2e1 * r0 * t112 + 0.4e1 * t74
  t115 = params.bb * t26
  t118 = 0.1e1 / t34
  t119 = params.cc * t118
  t122 = params.cc * t26
  t126 = 0.13888888888888888888888888888888888888888888888889e-1 * t115 * t30 + t119 * t44 / 0.2e1 - 0.2e1 * t122 * t30 * t65
  t130 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t50 * t126)
  t152 = f.my_piecewise3(t2, 0, t7 * t23 * t126 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t50 * (-0.37037037037037037037037037037037037037037037037037e-1 * t115 * t53 - 0.2e1 / 0.3e1 * t119 * t60 + 0.8e1 * t122 * t53 * t65 - 0.128e3 / 0.3e1 * params.cc / t83 / r0 * t103 * t34))
  v2rhosigma_0_ = 0.2e1 * r0 * t152 + 0.2e1 * t130
  t172 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t50 * (-params.cc / t98 * t44 / 0.4e1 - params.cc / s0 * t31 * t65 + 0.16e2 * params.cc / t83 * t103 * t118))
  v2sigma2_0_ = 0.2e1 * r0 * t172
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
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
  t23 = 0.1e1 / t21 / r0
  t24 = t20 * t23
  t25 = params.bb * s0
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = r0 ** 2
  t29 = t21 ** 2
  t35 = jnp.sqrt(s0)
  t36 = params.cc * t35
  t41 = 0.4e1 * t35 * t26 * t23 + t26
  t42 = 0.1e1 / t41
  t45 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t25 * t27 / t29 / t28 + t36 * t26 * t23 * t42
  t50 = t20 / t21
  t51 = t28 * r0
  t54 = t27 / t29 / t51
  t58 = 0.1e1 / t21 / t28
  t63 = params.cc * s0
  t64 = t41 ** 2
  t65 = 0.1e1 / t64
  t69 = -0.37037037037037037037037037037037037037037037037037e-1 * t25 * t54 - 0.4e1 / 0.3e1 * t36 * t26 * t58 * t42 + 0.16e2 / 0.3e1 * t63 * t54 * t65
  t73 = t20 * t29
  t74 = t28 ** 2
  t77 = t27 / t29 / t74
  t90 = params.cc * t35 * s0
  t94 = 0.1e1 / t64 / t41
  t98 = 0.13580246913580246913580246913580246913580246913580e0 * t25 * t77 + 0.28e2 / 0.9e1 * t36 * t26 / t21 / t51 * t42 - 0.80e2 / 0.3e1 * t63 * t77 * t65 + 0.1024e4 / 0.9e1 * t90 / t74 / t28 * t94
  t103 = f.my_piecewise3(t2, 0, -t7 * t24 * t45 / 0.30e2 + t7 * t50 * t69 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t73 * t98)
  t118 = t27 / t29 / t74 / r0
  t135 = s0 ** 2
  t137 = t74 ** 2
  t140 = t64 ** 2
  t151 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t58 * t45 - t7 * t24 * t69 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t50 * t98 + 0.3e1 / 0.20e2 * t7 * t73 * (-0.63374485596707818930041152263374485596707818930040e0 * t25 * t118 - 0.280e3 / 0.27e2 * t36 * t26 / t21 / t74 * t42 + 0.3808e4 / 0.27e2 * t63 * t118 * t65 - 0.11264e5 / 0.9e1 * t90 / t74 / t51 * t94 + 0.16384e5 / 0.9e1 * params.cc * t135 / t21 / t137 / t140 * t26))
  v3rho3_0_ = 0.2e1 * r0 * t151 + 0.6e1 * t103

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
  t24 = 0.1e1 / t22 / t21
  t25 = t20 * t24
  t26 = params.bb * s0
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = t22 ** 2
  t35 = jnp.sqrt(s0)
  t36 = params.cc * t35
  t38 = 0.1e1 / t22 / r0
  t43 = 0.4e1 * t35 * t27 * t38 + t27
  t44 = 0.1e1 / t43
  t47 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t26 * t28 / t29 / t21 + t36 * t27 * t38 * t44
  t51 = t20 * t38
  t52 = t21 * r0
  t55 = t28 / t29 / t52
  t62 = params.cc * s0
  t63 = t43 ** 2
  t64 = 0.1e1 / t63
  t68 = -0.37037037037037037037037037037037037037037037037037e-1 * t26 * t55 - 0.4e1 / 0.3e1 * t36 * t27 * t24 * t44 + 0.16e2 / 0.3e1 * t62 * t55 * t64
  t73 = t20 / t22
  t74 = t21 ** 2
  t77 = t28 / t29 / t74
  t81 = 0.1e1 / t22 / t52
  t90 = params.cc * t35 * s0
  t91 = t74 * t21
  t94 = 0.1e1 / t63 / t43
  t98 = 0.13580246913580246913580246913580246913580246913580e0 * t26 * t77 + 0.28e2 / 0.9e1 * t36 * t27 * t81 * t44 - 0.80e2 / 0.3e1 * t62 * t77 * t64 + 0.1024e4 / 0.9e1 * t90 / t91 * t94
  t102 = t20 * t29
  t103 = t74 * r0
  t106 = t28 / t29 / t103
  t123 = s0 ** 2
  t124 = params.cc * t123
  t125 = t74 ** 2
  t128 = t63 ** 2
  t129 = 0.1e1 / t128
  t134 = -0.63374485596707818930041152263374485596707818930040e0 * t26 * t106 - 0.280e3 / 0.27e2 * t36 * t27 / t22 / t74 * t44 + 0.3808e4 / 0.27e2 * t62 * t106 * t64 - 0.11264e5 / 0.9e1 * t90 / t74 / t52 * t94 + 0.16384e5 / 0.9e1 * t124 / t22 / t125 * t129 * t27
  t139 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t47 - t7 * t51 * t68 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t73 * t98 + 0.3e1 / 0.20e2 * t7 * t102 * t134)
  t156 = t28 / t29 / t91
  t195 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t81 * t47 + 0.8e1 / 0.45e2 * t7 * t25 * t68 - t7 * t51 * t98 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t73 * t134 + 0.3e1 / 0.20e2 * t7 * t102 * (0.35912208504801097393689986282578875171467764060356e1 * t26 * t156 + 0.3640e4 / 0.81e2 * t36 * t27 / t22 / t103 * t44 - 0.23072e5 / 0.27e2 * t62 * t156 * t64 + 0.953344e6 / 0.81e2 * t90 / t125 * t94 - 0.950272e6 / 0.27e2 * t124 / t22 / t125 / r0 * t129 * t27 + 0.1048576e7 / 0.27e2 * params.cc * t35 * t123 / t29 / t125 / t21 / t128 / t43 * t28))
  v4rho4_0_ = 0.2e1 * r0 * t195 + 0.8e1 * t139

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
  t35 = params.bb * s0
  t36 = r0 ** 2
  t37 = r0 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t43 = jnp.sqrt(s0)
  t44 = params.cc * t43
  t46 = 0.1e1 / t37 / r0
  t47 = 2 ** (0.1e1 / 0.3e1)
  t50 = 0.4e1 * t43 * t46 + t47
  t51 = 0.1e1 / t50
  t54 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t35 / t38 / t36 + t44 * t46 * t51
  t58 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t60 = t59 * f.p.zeta_threshold
  t62 = f.my_piecewise3(t21, t60, t23 * t20)
  t63 = 0.1e1 / t32
  t64 = t62 * t63
  t67 = t6 * t64 * t54 / 0.10e2
  t68 = t62 * t33
  t69 = t36 * r0
  t71 = 0.1e1 / t38 / t69
  t79 = params.cc * s0
  t80 = t50 ** 2
  t81 = 0.1e1 / t80
  t85 = -0.37037037037037037037037037037037037037037037037037e-1 * t35 * t71 - 0.4e1 / 0.3e1 * t44 / t37 / t36 * t51 + 0.16e2 / 0.3e1 * t79 * t71 * t81
  t90 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t54 + t67 + 0.3e1 / 0.20e2 * t6 * t68 * t85)
  t92 = r1 <= f.p.dens_threshold
  t93 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t94 = 0.1e1 + t93
  t95 = t94 <= f.p.zeta_threshold
  t96 = t94 ** (0.1e1 / 0.3e1)
  t97 = t96 ** 2
  t99 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t102 = f.my_piecewise3(t95, 0, 0.5e1 / 0.3e1 * t97 * t99)
  t103 = t102 * t33
  t104 = params.bb * s2
  t105 = r1 ** 2
  t106 = r1 ** (0.1e1 / 0.3e1)
  t107 = t106 ** 2
  t112 = jnp.sqrt(s2)
  t113 = params.cc * t112
  t115 = 0.1e1 / t106 / r1
  t118 = 0.4e1 * t112 * t115 + t47
  t119 = 0.1e1 / t118
  t122 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t104 / t107 / t105 + t113 * t115 * t119
  t127 = f.my_piecewise3(t95, t60, t97 * t94)
  t128 = t127 * t63
  t131 = t6 * t128 * t122 / 0.10e2
  t133 = f.my_piecewise3(t92, 0, 0.3e1 / 0.20e2 * t6 * t103 * t122 + t131)
  t135 = 0.1e1 / t22
  t136 = t28 ** 2
  t141 = t17 / t24 / t7
  t143 = -0.2e1 * t25 + 0.2e1 * t141
  t144 = f.my_piecewise5(t11, 0, t15, 0, t143)
  t148 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t135 * t136 + 0.5e1 / 0.3e1 * t23 * t144)
  t155 = t6 * t31 * t63 * t54
  t161 = 0.1e1 / t32 / t7
  t165 = t6 * t62 * t161 * t54 / 0.30e2
  t167 = t6 * t64 * t85
  t169 = t36 ** 2
  t171 = 0.1e1 / t38 / t169
  t196 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t148 * t33 * t54 + t155 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t85 - t165 + t167 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t68 * (0.13580246913580246913580246913580246913580246913580e0 * t35 * t171 + 0.28e2 / 0.9e1 * t44 / t37 / t69 * t51 - 0.80e2 / 0.3e1 * t79 * t171 * t81 + 0.512e3 / 0.9e1 * params.cc * t43 * s0 / t169 / t36 / t80 / t50))
  t197 = 0.1e1 / t96
  t198 = t99 ** 2
  t202 = f.my_piecewise5(t15, 0, t11, 0, -t143)
  t206 = f.my_piecewise3(t95, 0, 0.10e2 / 0.9e1 * t197 * t198 + 0.5e1 / 0.3e1 * t97 * t202)
  t213 = t6 * t102 * t63 * t122
  t218 = t6 * t127 * t161 * t122 / 0.30e2
  t220 = f.my_piecewise3(t92, 0, 0.3e1 / 0.20e2 * t6 * t206 * t33 * t122 + t213 / 0.5e1 - t218)
  d11 = 0.2e1 * t90 + 0.2e1 * t133 + t7 * (t196 + t220)
  t223 = -t8 - t26
  t224 = f.my_piecewise5(t11, 0, t15, 0, t223)
  t227 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t224)
  t228 = t227 * t33
  t233 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t228 * t54 + t67)
  t235 = f.my_piecewise5(t15, 0, t11, 0, -t223)
  t238 = f.my_piecewise3(t95, 0, 0.5e1 / 0.3e1 * t97 * t235)
  t239 = t238 * t33
  t243 = t127 * t33
  t244 = t105 * r1
  t246 = 0.1e1 / t107 / t244
  t254 = params.cc * s2
  t255 = t118 ** 2
  t256 = 0.1e1 / t255
  t260 = -0.37037037037037037037037037037037037037037037037037e-1 * t104 * t246 - 0.4e1 / 0.3e1 * t113 / t106 / t105 * t119 + 0.16e2 / 0.3e1 * t254 * t246 * t256
  t265 = f.my_piecewise3(t92, 0, 0.3e1 / 0.20e2 * t6 * t239 * t122 + t131 + 0.3e1 / 0.20e2 * t6 * t243 * t260)
  t269 = 0.2e1 * t141
  t270 = f.my_piecewise5(t11, 0, t15, 0, t269)
  t274 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t135 * t224 * t28 + 0.5e1 / 0.3e1 * t23 * t270)
  t281 = t6 * t227 * t63 * t54
  t289 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t274 * t33 * t54 + t281 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t228 * t85 + t155 / 0.10e2 - t165 + t167 / 0.10e2)
  t293 = f.my_piecewise5(t15, 0, t11, 0, -t269)
  t297 = f.my_piecewise3(t95, 0, 0.10e2 / 0.9e1 * t197 * t235 * t99 + 0.5e1 / 0.3e1 * t97 * t293)
  t304 = t6 * t238 * t63 * t122
  t311 = t6 * t128 * t260
  t314 = f.my_piecewise3(t92, 0, 0.3e1 / 0.20e2 * t6 * t297 * t33 * t122 + t304 / 0.10e2 + t213 / 0.10e2 - t218 + 0.3e1 / 0.20e2 * t6 * t103 * t260 + t311 / 0.10e2)
  d12 = t90 + t133 + t233 + t265 + t7 * (t289 + t314)
  t319 = t224 ** 2
  t323 = 0.2e1 * t25 + 0.2e1 * t141
  t324 = f.my_piecewise5(t11, 0, t15, 0, t323)
  t328 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t135 * t319 + 0.5e1 / 0.3e1 * t23 * t324)
  t335 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t328 * t33 * t54 + t281 / 0.5e1 - t165)
  t336 = t235 ** 2
  t340 = f.my_piecewise5(t15, 0, t11, 0, -t323)
  t344 = f.my_piecewise3(t95, 0, 0.10e2 / 0.9e1 * t197 * t336 + 0.5e1 / 0.3e1 * t97 * t340)
  t354 = t105 ** 2
  t356 = 0.1e1 / t107 / t354
  t381 = f.my_piecewise3(t92, 0, 0.3e1 / 0.20e2 * t6 * t344 * t33 * t122 + t304 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t239 * t260 - t218 + t311 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t243 * (0.13580246913580246913580246913580246913580246913580e0 * t104 * t356 + 0.28e2 / 0.9e1 * t113 / t106 / t244 * t119 - 0.80e2 / 0.3e1 * t254 * t356 * t256 + 0.512e3 / 0.9e1 * params.cc * t112 * s2 / t354 / t105 / t255 / t118))
  d22 = 0.2e1 * t233 + 0.2e1 * t265 + t7 * (t335 + t381)
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
  t46 = params.bb * s0
  t47 = r0 ** 2
  t48 = r0 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t54 = jnp.sqrt(s0)
  t55 = params.cc * t54
  t57 = 0.1e1 / t48 / r0
  t58 = 2 ** (0.1e1 / 0.3e1)
  t61 = 0.4e1 * t54 * t57 + t58
  t62 = 0.1e1 / t61
  t65 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t46 / t49 / t47 + t55 * t57 * t62
  t71 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t72 = 0.1e1 / t43
  t73 = t71 * t72
  t77 = t71 * t44
  t78 = t47 * r0
  t80 = 0.1e1 / t49 / t78
  t88 = params.cc * s0
  t89 = t61 ** 2
  t90 = 0.1e1 / t89
  t94 = -0.37037037037037037037037037037037037037037037037037e-1 * t46 * t80 - 0.4e1 / 0.3e1 * t55 / t48 / t47 * t62 + 0.16e2 / 0.3e1 * t88 * t80 * t90
  t98 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t100 = t99 * f.p.zeta_threshold
  t102 = f.my_piecewise3(t21, t100, t32 * t20)
  t104 = 0.1e1 / t43 / t7
  t105 = t102 * t104
  t109 = t102 * t72
  t113 = t102 * t44
  t114 = t47 ** 2
  t116 = 0.1e1 / t49 / t114
  t128 = params.cc * t54 * s0
  t132 = 0.1e1 / t89 / t61
  t136 = 0.13580246913580246913580246913580246913580246913580e0 * t46 * t116 + 0.28e2 / 0.9e1 * t55 / t48 / t78 * t62 - 0.80e2 / 0.3e1 * t88 * t116 * t90 + 0.512e3 / 0.9e1 * t128 / t114 / t47 * t132
  t141 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t65 + t6 * t73 * t65 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t77 * t94 - t6 * t105 * t65 / 0.30e2 + t6 * t109 * t94 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t113 * t136)
  t143 = r1 <= f.p.dens_threshold
  t144 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t145 = 0.1e1 + t144
  t146 = t145 <= f.p.zeta_threshold
  t147 = t145 ** (0.1e1 / 0.3e1)
  t148 = 0.1e1 / t147
  t150 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t151 = t150 ** 2
  t154 = t147 ** 2
  t156 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t160 = f.my_piecewise3(t146, 0, 0.10e2 / 0.9e1 * t148 * t151 + 0.5e1 / 0.3e1 * t154 * t156)
  t163 = r1 ** 2
  t164 = r1 ** (0.1e1 / 0.3e1)
  t165 = t164 ** 2
  t170 = jnp.sqrt(s2)
  t173 = 0.1e1 / t164 / r1
  t180 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * params.bb * s2 / t165 / t163 + params.cc * t170 * t173 / (0.4e1 * t170 * t173 + t58)
  t186 = f.my_piecewise3(t146, 0, 0.5e1 / 0.3e1 * t154 * t150)
  t192 = f.my_piecewise3(t146, t100, t154 * t145)
  t198 = f.my_piecewise3(t143, 0, 0.3e1 / 0.20e2 * t6 * t160 * t44 * t180 + t6 * t186 * t72 * t180 / 0.5e1 - t6 * t192 * t104 * t180 / 0.30e2)
  t208 = t24 ** 2
  t212 = 0.6e1 * t34 - 0.6e1 * t17 / t208
  t213 = f.my_piecewise5(t11, 0, t15, 0, t212)
  t217 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t213)
  t240 = 0.1e1 / t43 / t24
  t253 = 0.1e1 / t49 / t114 / r0
  t269 = s0 ** 2
  t271 = t114 ** 2
  t274 = t89 ** 2
  t284 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t217 * t44 * t65 + 0.3e1 / 0.10e2 * t6 * t42 * t72 * t65 + 0.9e1 / 0.20e2 * t6 * t45 * t94 - t6 * t71 * t104 * t65 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t73 * t94 + 0.9e1 / 0.20e2 * t6 * t77 * t136 + 0.2e1 / 0.45e2 * t6 * t102 * t240 * t65 - t6 * t105 * t94 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t109 * t136 + 0.3e1 / 0.20e2 * t6 * t113 * (-0.63374485596707818930041152263374485596707818930040e0 * t46 * t253 - 0.280e3 / 0.27e2 * t55 / t48 / t114 * t62 + 0.3808e4 / 0.27e2 * t88 * t253 * t90 - 0.5632e4 / 0.9e1 * t128 / t114 / t78 * t132 + 0.8192e4 / 0.9e1 * params.cc * t269 / t48 / t271 / t274))
  t294 = f.my_piecewise5(t15, 0, t11, 0, -t212)
  t298 = f.my_piecewise3(t146, 0, -0.10e2 / 0.27e2 / t147 / t145 * t151 * t150 + 0.10e2 / 0.3e1 * t148 * t150 * t156 + 0.5e1 / 0.3e1 * t154 * t294)
  t316 = f.my_piecewise3(t143, 0, 0.3e1 / 0.20e2 * t6 * t298 * t44 * t180 + 0.3e1 / 0.10e2 * t6 * t160 * t72 * t180 - t6 * t186 * t104 * t180 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t192 * t240 * t180)
  d111 = 0.3e1 * t141 + 0.3e1 * t198 + t7 * (t284 + t316)

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
  t58 = params.bb * s0
  t59 = r0 ** 2
  t60 = r0 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t66 = jnp.sqrt(s0)
  t67 = params.cc * t66
  t69 = 0.1e1 / t60 / r0
  t70 = 2 ** (0.1e1 / 0.3e1)
  t73 = 0.4e1 * t66 * t69 + t70
  t74 = 0.1e1 / t73
  t77 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t58 / t61 / t59 + t67 * t69 * t74
  t86 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t87 = 0.1e1 / t55
  t88 = t86 * t87
  t92 = t86 * t56
  t93 = t59 * r0
  t95 = 0.1e1 / t61 / t93
  t103 = params.cc * s0
  t104 = t73 ** 2
  t105 = 0.1e1 / t104
  t109 = -0.37037037037037037037037037037037037037037037037037e-1 * t58 * t95 - 0.4e1 / 0.3e1 * t67 / t60 / t59 * t74 + 0.16e2 / 0.3e1 * t103 * t95 * t105
  t115 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t117 = 0.1e1 / t55 / t7
  t118 = t115 * t117
  t122 = t115 * t87
  t126 = t115 * t56
  t127 = t59 ** 2
  t129 = 0.1e1 / t61 / t127
  t141 = params.cc * t66 * s0
  t142 = t127 * t59
  t145 = 0.1e1 / t104 / t73
  t149 = 0.13580246913580246913580246913580246913580246913580e0 * t58 * t129 + 0.28e2 / 0.9e1 * t67 / t60 / t93 * t74 - 0.80e2 / 0.3e1 * t103 * t129 * t105 + 0.512e3 / 0.9e1 * t141 / t142 * t145
  t153 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t154 = t153 ** 2
  t155 = t154 * f.p.zeta_threshold
  t157 = f.my_piecewise3(t21, t155, t44 * t20)
  t159 = 0.1e1 / t55 / t25
  t160 = t157 * t159
  t164 = t157 * t117
  t168 = t157 * t87
  t172 = t157 * t56
  t173 = t127 * r0
  t175 = 0.1e1 / t61 / t173
  t191 = s0 ** 2
  t192 = params.cc * t191
  t193 = t127 ** 2
  t196 = t104 ** 2
  t197 = 0.1e1 / t196
  t201 = -0.63374485596707818930041152263374485596707818930040e0 * t58 * t175 - 0.280e3 / 0.27e2 * t67 / t60 / t127 * t74 + 0.3808e4 / 0.27e2 * t103 * t175 * t105 - 0.5632e4 / 0.9e1 * t141 / t127 / t93 * t145 + 0.8192e4 / 0.9e1 * t192 / t60 / t193 * t197
  t206 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t77 + 0.3e1 / 0.10e2 * t6 * t88 * t77 + 0.9e1 / 0.20e2 * t6 * t92 * t109 - t6 * t118 * t77 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t122 * t109 + 0.9e1 / 0.20e2 * t6 * t126 * t149 + 0.2e1 / 0.45e2 * t6 * t160 * t77 - t6 * t164 * t109 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t168 * t149 + 0.3e1 / 0.20e2 * t6 * t172 * t201)
  t208 = r1 <= f.p.dens_threshold
  t209 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t210 = 0.1e1 + t209
  t211 = t210 <= f.p.zeta_threshold
  t212 = t210 ** (0.1e1 / 0.3e1)
  t214 = 0.1e1 / t212 / t210
  t216 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t217 = t216 ** 2
  t221 = 0.1e1 / t212
  t222 = t221 * t216
  t224 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t227 = t212 ** 2
  t229 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t233 = f.my_piecewise3(t211, 0, -0.10e2 / 0.27e2 * t214 * t217 * t216 + 0.10e2 / 0.3e1 * t222 * t224 + 0.5e1 / 0.3e1 * t227 * t229)
  t236 = r1 ** 2
  t237 = r1 ** (0.1e1 / 0.3e1)
  t238 = t237 ** 2
  t243 = jnp.sqrt(s2)
  t246 = 0.1e1 / t237 / r1
  t253 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * params.bb * s2 / t238 / t236 + params.cc * t243 * t246 / (0.4e1 * t243 * t246 + t70)
  t262 = f.my_piecewise3(t211, 0, 0.10e2 / 0.9e1 * t221 * t217 + 0.5e1 / 0.3e1 * t227 * t224)
  t269 = f.my_piecewise3(t211, 0, 0.5e1 / 0.3e1 * t227 * t216)
  t275 = f.my_piecewise3(t211, t155, t227 * t210)
  t281 = f.my_piecewise3(t208, 0, 0.3e1 / 0.20e2 * t6 * t233 * t56 * t253 + 0.3e1 / 0.10e2 * t6 * t262 * t87 * t253 - t6 * t269 * t117 * t253 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t275 * t159 * t253)
  t296 = 0.1e1 / t61 / t142
  t331 = t20 ** 2
  t334 = t30 ** 2
  t340 = t41 ** 2
  t349 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t350 = f.my_piecewise5(t11, 0, t15, 0, t349)
  t354 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t331 * t334 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t340 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t350)
  t387 = 0.1e1 / t55 / t36
  t392 = 0.3e1 / 0.5e1 * t6 * t126 * t201 + 0.8e1 / 0.45e2 * t6 * t160 * t109 - t6 * t164 * t149 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t168 * t201 + 0.3e1 / 0.20e2 * t6 * t172 * (0.35912208504801097393689986282578875171467764060356e1 * t58 * t296 + 0.3640e4 / 0.81e2 * t67 / t60 / t173 * t74 - 0.23072e5 / 0.27e2 * t103 * t296 * t105 + 0.476672e6 / 0.81e2 * t141 / t193 * t145 - 0.475136e6 / 0.27e2 * t192 / t60 / t193 / r0 * t197 + 0.524288e6 / 0.27e2 * params.cc * t66 * t191 / t61 / t193 / t59 / t196 / t73) + 0.3e1 / 0.20e2 * t6 * t354 * t56 * t77 + 0.3e1 / 0.5e1 * t6 * t57 * t109 + 0.6e1 / 0.5e1 * t6 * t88 * t109 + 0.9e1 / 0.10e2 * t6 * t92 * t149 - 0.2e1 / 0.5e1 * t6 * t118 * t109 + 0.6e1 / 0.5e1 * t6 * t122 * t149 + 0.2e1 / 0.5e1 * t6 * t54 * t87 * t77 - t6 * t86 * t117 * t77 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t115 * t159 * t77 - 0.14e2 / 0.135e3 * t6 * t157 * t387 * t77
  t393 = f.my_piecewise3(t1, 0, t392)
  t394 = t210 ** 2
  t397 = t217 ** 2
  t403 = t224 ** 2
  t409 = f.my_piecewise5(t15, 0, t11, 0, -t349)
  t413 = f.my_piecewise3(t211, 0, 0.40e2 / 0.81e2 / t212 / t394 * t397 - 0.20e2 / 0.9e1 * t214 * t217 * t224 + 0.10e2 / 0.3e1 * t221 * t403 + 0.40e2 / 0.9e1 * t222 * t229 + 0.5e1 / 0.3e1 * t227 * t409)
  t435 = f.my_piecewise3(t208, 0, 0.3e1 / 0.20e2 * t6 * t413 * t56 * t253 + 0.2e1 / 0.5e1 * t6 * t233 * t87 * t253 - t6 * t262 * t117 * t253 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t269 * t159 * t253 - 0.14e2 / 0.135e3 * t6 * t275 * t387 * t253)
  d1111 = 0.4e1 * t206 + 0.4e1 * t281 + t7 * (t393 + t435)

  res = {'v4rho4': d1111}
  return res
