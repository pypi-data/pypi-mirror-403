"""Generated from gga_x_ol2.mpl."""

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

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ol2_f, rs, zeta, xs0, xs1)

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

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ol2_f, rs, zeta, xs0, xs1)

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

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ol2_f, rs, zeta, xs0, xs1)

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
  t28 = params.bb * s0
  t29 = r0 ** 2
  t30 = r0 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t33 = 0.1e1 / t31 / t29
  t36 = jnp.sqrt(s0)
  t37 = params.cc * t36
  t39 = 0.1e1 / t30 / r0
  t40 = 2 ** (0.1e1 / 0.3e1)
  t43 = 0.4e1 * t36 * t39 + t40
  t44 = 0.1e1 / t43
  t45 = t39 * t44
  t47 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t28 * t33 + t37 * t45
  t51 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t47)
  t52 = r1 <= f.p.dens_threshold
  t53 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t54 = 0.1e1 + t53
  t55 = t54 <= f.p.zeta_threshold
  t56 = t54 ** (0.1e1 / 0.3e1)
  t58 = f.my_piecewise3(t55, t22, t56 * t54)
  t59 = t58 * t26
  t60 = params.bb * s2
  t61 = r1 ** 2
  t62 = r1 ** (0.1e1 / 0.3e1)
  t63 = t62 ** 2
  t65 = 0.1e1 / t63 / t61
  t68 = jnp.sqrt(s2)
  t69 = params.cc * t68
  t71 = 0.1e1 / t62 / r1
  t74 = 0.4e1 * t68 * t71 + t40
  t75 = 0.1e1 / t74
  t76 = t71 * t75
  t78 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t60 * t65 + t69 * t76
  t82 = f.my_piecewise3(t52, 0, -0.3e1 / 0.8e1 * t5 * t59 * t78)
  t83 = t6 ** 2
  t85 = t16 / t83
  t86 = t7 - t85
  t87 = f.my_piecewise5(t10, 0, t14, 0, t86)
  t90 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t87)
  t95 = t26 ** 2
  t96 = 0.1e1 / t95
  t100 = t5 * t25 * t96 * t47 / 0.8e1
  t103 = 0.1e1 / t31 / t29 / r0
  t112 = t43 ** 2
  t113 = 0.1e1 / t112
  t122 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t90 * t26 * t47 - t100 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.37037037037037037037037037037037037037037037037037e-1 * t28 * t103 - 0.4e1 / 0.3e1 * t37 / t30 / t29 * t44 + 0.16e2 / 0.3e1 * params.cc * s0 * t103 * t113))
  t124 = f.my_piecewise5(t14, 0, t10, 0, -t86)
  t127 = f.my_piecewise3(t55, 0, 0.4e1 / 0.3e1 * t56 * t124)
  t135 = t5 * t58 * t96 * t78 / 0.8e1
  t137 = f.my_piecewise3(t52, 0, -0.3e1 / 0.8e1 * t5 * t127 * t26 * t78 - t135)
  vrho_0_ = t51 + t82 + t6 * (t122 + t137)
  t140 = -t7 - t85
  t141 = f.my_piecewise5(t10, 0, t14, 0, t140)
  t144 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t141)
  t150 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t144 * t26 * t47 - t100)
  t152 = f.my_piecewise5(t14, 0, t10, 0, -t140)
  t155 = f.my_piecewise3(t55, 0, 0.4e1 / 0.3e1 * t56 * t152)
  t162 = 0.1e1 / t63 / t61 / r1
  t171 = t74 ** 2
  t172 = 0.1e1 / t171
  t181 = f.my_piecewise3(t52, 0, -0.3e1 / 0.8e1 * t5 * t155 * t26 * t78 - t135 - 0.3e1 / 0.8e1 * t5 * t59 * (-0.37037037037037037037037037037037037037037037037037e-1 * t60 * t162 - 0.4e1 / 0.3e1 * t69 / t62 / t61 * t75 + 0.16e2 / 0.3e1 * params.cc * s2 * t162 * t172))
  vrho_1_ = t51 + t82 + t6 * (t150 + t181)
  t197 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.13888888888888888888888888888888888888888888888889e-1 * params.bb * t33 + params.cc / t36 * t45 / 0.2e1 - 0.2e1 * params.cc * t33 * t113))
  vsigma_0_ = t6 * t197
  vsigma_1_ = 0.0e0
  t211 = f.my_piecewise3(t52, 0, -0.3e1 / 0.8e1 * t5 * t59 * (0.13888888888888888888888888888888888888888888888889e-1 * params.bb * t65 + params.cc / t68 * t76 / 0.2e1 - 0.2e1 * params.cc * t65 * t172))
  vsigma_2_ = t6 * t211
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

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ol2_f, rs, zeta, xs0, xs1)

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
  t20 = params.bb * s0
  t21 = 2 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = r0 ** 2
  t24 = t18 ** 2
  t26 = 0.1e1 / t24 / t23
  t30 = jnp.sqrt(s0)
  t31 = params.cc * t30
  t33 = 0.1e1 / t18 / r0
  t38 = 0.4e1 * t30 * t21 * t33 + t21
  t39 = 0.1e1 / t38
  t40 = t21 * t33 * t39
  t42 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t20 * t22 * t26 + t31 * t40
  t46 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t42)
  t55 = t22 / t24 / t23 / r0
  t65 = t38 ** 2
  t66 = 0.1e1 / t65
  t75 = f.my_piecewise3(t2, 0, -t6 * t17 / t24 * t42 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.37037037037037037037037037037037037037037037037037e-1 * t20 * t55 - 0.4e1 / 0.3e1 * t31 * t21 / t18 / t23 * t39 + 0.16e2 / 0.3e1 * params.cc * s0 * t55 * t66))
  vrho_0_ = 0.2e1 * r0 * t75 + 0.2e1 * t46
  t93 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.13888888888888888888888888888888888888888888888889e-1 * params.bb * t22 * t26 + params.cc / t30 * t40 / 0.2e1 - 0.2e1 * params.cc * t22 * t26 * t66))
  vsigma_0_ = 0.2e1 * r0 * t93
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
  t22 = params.bb * s0
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = r0 ** 2
  t27 = 0.1e1 / t19 / t25
  t28 = t24 * t27
  t31 = jnp.sqrt(s0)
  t32 = params.cc * t31
  t34 = 0.1e1 / t18 / r0
  t39 = 0.4e1 * t31 * t23 * t34 + t23
  t40 = 0.1e1 / t39
  t41 = t23 * t34 * t40
  t43 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t22 * t28 + t32 * t41
  t47 = t17 * t18
  t48 = t25 * r0
  t50 = 0.1e1 / t19 / t48
  t51 = t24 * t50
  t57 = t23 / t18 / t25 * t40
  t60 = params.cc * s0
  t61 = t39 ** 2
  t62 = 0.1e1 / t61
  t66 = -0.37037037037037037037037037037037037037037037037037e-1 * t22 * t51 - 0.4e1 / 0.3e1 * t32 * t57 + 0.16e2 / 0.3e1 * t60 * t51 * t62
  t71 = f.my_piecewise3(t2, 0, -t6 * t21 * t43 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t47 * t66)
  t82 = t25 ** 2
  t85 = t24 / t19 / t82
  t97 = t31 * s0
  t102 = 0.1e1 / t61 / t39
  t111 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t43 / 0.12e2 - t6 * t21 * t66 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t47 * (0.13580246913580246913580246913580246913580246913580e0 * t22 * t85 + 0.28e2 / 0.9e1 * t32 * t23 / t18 / t48 * t40 - 0.80e2 / 0.3e1 * t60 * t85 * t62 + 0.1024e4 / 0.9e1 * params.cc * t97 / t82 / t25 * t102))
  v2rho2_0_ = 0.2e1 * r0 * t111 + 0.4e1 * t71
  t114 = params.bb * t24
  t117 = 0.1e1 / t31
  t118 = params.cc * t117
  t121 = params.cc * t24
  t125 = 0.13888888888888888888888888888888888888888888888889e-1 * t114 * t27 + t118 * t41 / 0.2e1 - 0.2e1 * t121 * t27 * t62
  t129 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t47 * t125)
  t151 = f.my_piecewise3(t2, 0, -t6 * t21 * t125 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t47 * (-0.37037037037037037037037037037037037037037037037037e-1 * t114 * t50 - 0.2e1 / 0.3e1 * t118 * t57 + 0.8e1 * t121 * t50 * t62 - 0.128e3 / 0.3e1 * params.cc / t82 / r0 * t102 * t31))
  v2rhosigma_0_ = 0.2e1 * r0 * t151 + 0.2e1 * t129
  t171 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t47 * (-params.cc / t97 * t41 / 0.4e1 - params.cc / s0 * t28 * t62 + 0.16e2 * params.cc / t82 * t102 * t117))
  v2sigma2_0_ = 0.2e1 * r0 * t171
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
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
  t22 = t17 / t19 / r0
  t23 = params.bb * s0
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = r0 ** 2
  t28 = 0.1e1 / t19 / t26
  t32 = jnp.sqrt(s0)
  t33 = params.cc * t32
  t35 = 0.1e1 / t18 / r0
  t40 = 0.4e1 * t32 * t24 * t35 + t24
  t41 = 0.1e1 / t40
  t44 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t23 * t25 * t28 + t33 * t24 * t35 * t41
  t49 = t17 / t19
  t50 = t26 * r0
  t53 = t25 / t19 / t50
  t62 = params.cc * s0
  t63 = t40 ** 2
  t64 = 0.1e1 / t63
  t68 = -0.37037037037037037037037037037037037037037037037037e-1 * t23 * t53 - 0.4e1 / 0.3e1 * t33 * t24 / t18 / t26 * t41 + 0.16e2 / 0.3e1 * t62 * t53 * t64
  t72 = t17 * t18
  t73 = t26 ** 2
  t76 = t25 / t19 / t73
  t89 = params.cc * t32 * s0
  t93 = 0.1e1 / t63 / t40
  t97 = 0.13580246913580246913580246913580246913580246913580e0 * t23 * t76 + 0.28e2 / 0.9e1 * t33 * t24 / t18 / t50 * t41 - 0.80e2 / 0.3e1 * t62 * t76 * t64 + 0.1024e4 / 0.9e1 * t89 / t73 / t26 * t93
  t102 = f.my_piecewise3(t2, 0, t6 * t22 * t44 / 0.12e2 - t6 * t49 * t68 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t72 * t97)
  t117 = t25 / t19 / t73 / r0
  t134 = s0 ** 2
  t136 = t73 ** 2
  t139 = t63 ** 2
  t150 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t28 * t44 + t6 * t22 * t68 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t49 * t97 - 0.3e1 / 0.8e1 * t6 * t72 * (-0.63374485596707818930041152263374485596707818930040e0 * t23 * t117 - 0.280e3 / 0.27e2 * t33 * t24 / t18 / t73 * t41 + 0.3808e4 / 0.27e2 * t62 * t117 * t64 - 0.11264e5 / 0.9e1 * t89 / t73 / t50 * t93 + 0.16384e5 / 0.9e1 * params.cc * t134 / t18 / t136 / t139 * t24))
  v3rho3_0_ = 0.2e1 * r0 * t150 + 0.6e1 * t102

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
  t24 = params.bb * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t30 = jnp.sqrt(s0)
  t31 = params.cc * t30
  t33 = 0.1e1 / t19 / r0
  t38 = 0.4e1 * t30 * t25 * t33 + t25
  t39 = 0.1e1 / t38
  t42 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t24 * t26 * t22 + t31 * t25 * t33 * t39
  t48 = t17 / t20 / r0
  t49 = t18 * r0
  t51 = 0.1e1 / t20 / t49
  t52 = t26 * t51
  t61 = params.cc * s0
  t62 = t38 ** 2
  t63 = 0.1e1 / t62
  t67 = -0.37037037037037037037037037037037037037037037037037e-1 * t24 * t52 - 0.4e1 / 0.3e1 * t31 * t25 / t19 / t18 * t39 + 0.16e2 / 0.3e1 * t61 * t52 * t63
  t72 = t17 / t20
  t73 = t18 ** 2
  t76 = t26 / t20 / t73
  t89 = params.cc * t30 * s0
  t90 = t73 * t18
  t93 = 0.1e1 / t62 / t38
  t97 = 0.13580246913580246913580246913580246913580246913580e0 * t24 * t76 + 0.28e2 / 0.9e1 * t31 * t25 / t19 / t49 * t39 - 0.80e2 / 0.3e1 * t61 * t76 * t63 + 0.1024e4 / 0.9e1 * t89 / t90 * t93
  t101 = t17 * t19
  t102 = t73 * r0
  t105 = t26 / t20 / t102
  t122 = s0 ** 2
  t123 = params.cc * t122
  t124 = t73 ** 2
  t127 = t62 ** 2
  t128 = 0.1e1 / t127
  t133 = -0.63374485596707818930041152263374485596707818930040e0 * t24 * t105 - 0.280e3 / 0.27e2 * t31 * t25 / t19 / t73 * t39 + 0.3808e4 / 0.27e2 * t61 * t105 * t63 - 0.11264e5 / 0.9e1 * t89 / t73 / t49 * t93 + 0.16384e5 / 0.9e1 * t123 / t19 / t124 * t128 * t25
  t138 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t42 + t6 * t48 * t67 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t72 * t97 - 0.3e1 / 0.8e1 * t6 * t101 * t133)
  t155 = t26 / t20 / t90
  t194 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t51 * t42 - 0.5e1 / 0.9e1 * t6 * t23 * t67 + t6 * t48 * t97 / 0.2e1 - t6 * t72 * t133 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t101 * (0.35912208504801097393689986282578875171467764060356e1 * t24 * t155 + 0.3640e4 / 0.81e2 * t31 * t25 / t19 / t102 * t39 - 0.23072e5 / 0.27e2 * t61 * t155 * t63 + 0.953344e6 / 0.81e2 * t89 / t124 * t93 - 0.950272e6 / 0.27e2 * t123 / t19 / t124 / r0 * t128 * t25 + 0.1048576e7 / 0.27e2 * params.cc * t30 * t122 / t20 / t124 / t18 / t127 / t38 * t26))
  v4rho4_0_ = 0.2e1 * r0 * t194 + 0.8e1 * t138

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
  t32 = params.bb * s0
  t33 = r0 ** 2
  t34 = r0 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t40 = jnp.sqrt(s0)
  t41 = params.cc * t40
  t43 = 0.1e1 / t34 / r0
  t44 = 2 ** (0.1e1 / 0.3e1)
  t47 = 0.4e1 * t40 * t43 + t44
  t48 = 0.1e1 / t47
  t51 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t32 / t35 / t33 + t41 * t43 * t48
  t55 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t56 = t55 * f.p.zeta_threshold
  t58 = f.my_piecewise3(t20, t56, t21 * t19)
  t59 = t30 ** 2
  t60 = 0.1e1 / t59
  t61 = t58 * t60
  t64 = t5 * t61 * t51 / 0.8e1
  t65 = t58 * t30
  t66 = t33 * r0
  t68 = 0.1e1 / t35 / t66
  t76 = params.cc * s0
  t77 = t47 ** 2
  t78 = 0.1e1 / t77
  t82 = -0.37037037037037037037037037037037037037037037037037e-1 * t32 * t68 - 0.4e1 / 0.3e1 * t41 / t34 / t33 * t48 + 0.16e2 / 0.3e1 * t76 * t68 * t78
  t87 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t51 - t64 - 0.3e1 / 0.8e1 * t5 * t65 * t82)
  t89 = r1 <= f.p.dens_threshold
  t90 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t91 = 0.1e1 + t90
  t92 = t91 <= f.p.zeta_threshold
  t93 = t91 ** (0.1e1 / 0.3e1)
  t95 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t98 = f.my_piecewise3(t92, 0, 0.4e1 / 0.3e1 * t93 * t95)
  t99 = t98 * t30
  t100 = params.bb * s2
  t101 = r1 ** 2
  t102 = r1 ** (0.1e1 / 0.3e1)
  t103 = t102 ** 2
  t108 = jnp.sqrt(s2)
  t109 = params.cc * t108
  t111 = 0.1e1 / t102 / r1
  t114 = 0.4e1 * t108 * t111 + t44
  t115 = 0.1e1 / t114
  t118 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t100 / t103 / t101 + t109 * t111 * t115
  t123 = f.my_piecewise3(t92, t56, t93 * t91)
  t124 = t123 * t60
  t127 = t5 * t124 * t118 / 0.8e1
  t129 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t99 * t118 - t127)
  t131 = t21 ** 2
  t132 = 0.1e1 / t131
  t133 = t26 ** 2
  t138 = t16 / t22 / t6
  t140 = -0.2e1 * t23 + 0.2e1 * t138
  t141 = f.my_piecewise5(t10, 0, t14, 0, t140)
  t145 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t132 * t133 + 0.4e1 / 0.3e1 * t21 * t141)
  t152 = t5 * t29 * t60 * t51
  t158 = 0.1e1 / t59 / t6
  t162 = t5 * t58 * t158 * t51 / 0.12e2
  t164 = t5 * t61 * t82
  t166 = t33 ** 2
  t168 = 0.1e1 / t35 / t166
  t193 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t145 * t30 * t51 - t152 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t82 + t162 - t164 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t65 * (0.13580246913580246913580246913580246913580246913580e0 * t32 * t168 + 0.28e2 / 0.9e1 * t41 / t34 / t66 * t48 - 0.80e2 / 0.3e1 * t76 * t168 * t78 + 0.512e3 / 0.9e1 * params.cc * t40 * s0 / t166 / t33 / t77 / t47))
  t194 = t93 ** 2
  t195 = 0.1e1 / t194
  t196 = t95 ** 2
  t200 = f.my_piecewise5(t14, 0, t10, 0, -t140)
  t204 = f.my_piecewise3(t92, 0, 0.4e1 / 0.9e1 * t195 * t196 + 0.4e1 / 0.3e1 * t93 * t200)
  t211 = t5 * t98 * t60 * t118
  t216 = t5 * t123 * t158 * t118 / 0.12e2
  t218 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t204 * t30 * t118 - t211 / 0.4e1 + t216)
  d11 = 0.2e1 * t87 + 0.2e1 * t129 + t6 * (t193 + t218)
  t221 = -t7 - t24
  t222 = f.my_piecewise5(t10, 0, t14, 0, t221)
  t225 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t222)
  t226 = t225 * t30
  t231 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t226 * t51 - t64)
  t233 = f.my_piecewise5(t14, 0, t10, 0, -t221)
  t236 = f.my_piecewise3(t92, 0, 0.4e1 / 0.3e1 * t93 * t233)
  t237 = t236 * t30
  t241 = t123 * t30
  t242 = t101 * r1
  t244 = 0.1e1 / t103 / t242
  t252 = params.cc * s2
  t253 = t114 ** 2
  t254 = 0.1e1 / t253
  t258 = -0.37037037037037037037037037037037037037037037037037e-1 * t100 * t244 - 0.4e1 / 0.3e1 * t109 / t102 / t101 * t115 + 0.16e2 / 0.3e1 * t252 * t244 * t254
  t263 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t237 * t118 - t127 - 0.3e1 / 0.8e1 * t5 * t241 * t258)
  t267 = 0.2e1 * t138
  t268 = f.my_piecewise5(t10, 0, t14, 0, t267)
  t272 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t132 * t222 * t26 + 0.4e1 / 0.3e1 * t21 * t268)
  t279 = t5 * t225 * t60 * t51
  t287 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t272 * t30 * t51 - t279 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t226 * t82 - t152 / 0.8e1 + t162 - t164 / 0.8e1)
  t291 = f.my_piecewise5(t14, 0, t10, 0, -t267)
  t295 = f.my_piecewise3(t92, 0, 0.4e1 / 0.9e1 * t195 * t233 * t95 + 0.4e1 / 0.3e1 * t93 * t291)
  t302 = t5 * t236 * t60 * t118
  t309 = t5 * t124 * t258
  t312 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t295 * t30 * t118 - t302 / 0.8e1 - t211 / 0.8e1 + t216 - 0.3e1 / 0.8e1 * t5 * t99 * t258 - t309 / 0.8e1)
  d12 = t87 + t129 + t231 + t263 + t6 * (t287 + t312)
  t317 = t222 ** 2
  t321 = 0.2e1 * t23 + 0.2e1 * t138
  t322 = f.my_piecewise5(t10, 0, t14, 0, t321)
  t326 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t132 * t317 + 0.4e1 / 0.3e1 * t21 * t322)
  t333 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t326 * t30 * t51 - t279 / 0.4e1 + t162)
  t334 = t233 ** 2
  t338 = f.my_piecewise5(t14, 0, t10, 0, -t321)
  t342 = f.my_piecewise3(t92, 0, 0.4e1 / 0.9e1 * t195 * t334 + 0.4e1 / 0.3e1 * t93 * t338)
  t352 = t101 ** 2
  t354 = 0.1e1 / t103 / t352
  t379 = f.my_piecewise3(t89, 0, -0.3e1 / 0.8e1 * t5 * t342 * t30 * t118 - t302 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t237 * t258 + t216 - t309 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t241 * (0.13580246913580246913580246913580246913580246913580e0 * t100 * t354 + 0.28e2 / 0.9e1 * t109 / t102 / t242 * t115 - 0.80e2 / 0.3e1 * t252 * t354 * t254 + 0.512e3 / 0.9e1 * params.cc * t108 * s2 / t352 / t101 / t253 / t114))
  d22 = 0.2e1 * t231 + 0.2e1 * t263 + t6 * (t333 + t379)
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
  t43 = t41 * t42
  t44 = params.bb * s0
  t45 = r0 ** 2
  t46 = r0 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t52 = jnp.sqrt(s0)
  t53 = params.cc * t52
  t55 = 0.1e1 / t46 / r0
  t56 = 2 ** (0.1e1 / 0.3e1)
  t59 = 0.4e1 * t52 * t55 + t56
  t60 = 0.1e1 / t59
  t63 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t44 / t47 / t45 + t53 * t55 * t60
  t69 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t70 = t42 ** 2
  t71 = 0.1e1 / t70
  t72 = t69 * t71
  t76 = t69 * t42
  t77 = t45 * r0
  t79 = 0.1e1 / t47 / t77
  t87 = params.cc * s0
  t88 = t59 ** 2
  t89 = 0.1e1 / t88
  t93 = -0.37037037037037037037037037037037037037037037037037e-1 * t44 * t79 - 0.4e1 / 0.3e1 * t53 / t46 / t45 * t60 + 0.16e2 / 0.3e1 * t87 * t79 * t89
  t97 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t98 = t97 * f.p.zeta_threshold
  t100 = f.my_piecewise3(t20, t98, t21 * t19)
  t102 = 0.1e1 / t70 / t6
  t103 = t100 * t102
  t107 = t100 * t71
  t111 = t100 * t42
  t112 = t45 ** 2
  t114 = 0.1e1 / t47 / t112
  t126 = params.cc * t52 * s0
  t130 = 0.1e1 / t88 / t59
  t134 = 0.13580246913580246913580246913580246913580246913580e0 * t44 * t114 + 0.28e2 / 0.9e1 * t53 / t46 / t77 * t60 - 0.80e2 / 0.3e1 * t87 * t114 * t89 + 0.512e3 / 0.9e1 * t126 / t112 / t45 * t130
  t139 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t63 - t5 * t72 * t63 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t76 * t93 + t5 * t103 * t63 / 0.12e2 - t5 * t107 * t93 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t111 * t134)
  t141 = r1 <= f.p.dens_threshold
  t142 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t143 = 0.1e1 + t142
  t144 = t143 <= f.p.zeta_threshold
  t145 = t143 ** (0.1e1 / 0.3e1)
  t146 = t145 ** 2
  t147 = 0.1e1 / t146
  t149 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t150 = t149 ** 2
  t154 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t158 = f.my_piecewise3(t144, 0, 0.4e1 / 0.9e1 * t147 * t150 + 0.4e1 / 0.3e1 * t145 * t154)
  t161 = r1 ** 2
  t162 = r1 ** (0.1e1 / 0.3e1)
  t163 = t162 ** 2
  t168 = jnp.sqrt(s2)
  t171 = 0.1e1 / t162 / r1
  t178 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * params.bb * s2 / t163 / t161 + params.cc * t168 * t171 / (0.4e1 * t168 * t171 + t56)
  t184 = f.my_piecewise3(t144, 0, 0.4e1 / 0.3e1 * t145 * t149)
  t190 = f.my_piecewise3(t144, t98, t145 * t143)
  t196 = f.my_piecewise3(t141, 0, -0.3e1 / 0.8e1 * t5 * t158 * t42 * t178 - t5 * t184 * t71 * t178 / 0.4e1 + t5 * t190 * t102 * t178 / 0.12e2)
  t206 = t24 ** 2
  t210 = 0.6e1 * t33 - 0.6e1 * t16 / t206
  t211 = f.my_piecewise5(t10, 0, t14, 0, t210)
  t215 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t211)
  t238 = 0.1e1 / t70 / t24
  t251 = 0.1e1 / t47 / t112 / r0
  t267 = s0 ** 2
  t269 = t112 ** 2
  t272 = t88 ** 2
  t282 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t215 * t42 * t63 - 0.3e1 / 0.8e1 * t5 * t41 * t71 * t63 - 0.9e1 / 0.8e1 * t5 * t43 * t93 + t5 * t69 * t102 * t63 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t72 * t93 - 0.9e1 / 0.8e1 * t5 * t76 * t134 - 0.5e1 / 0.36e2 * t5 * t100 * t238 * t63 + t5 * t103 * t93 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t107 * t134 - 0.3e1 / 0.8e1 * t5 * t111 * (-0.63374485596707818930041152263374485596707818930040e0 * t44 * t251 - 0.280e3 / 0.27e2 * t53 / t46 / t112 * t60 + 0.3808e4 / 0.27e2 * t87 * t251 * t89 - 0.5632e4 / 0.9e1 * t126 / t112 / t77 * t130 + 0.8192e4 / 0.9e1 * params.cc * t267 / t46 / t269 / t272))
  t292 = f.my_piecewise5(t14, 0, t10, 0, -t210)
  t296 = f.my_piecewise3(t144, 0, -0.8e1 / 0.27e2 / t146 / t143 * t150 * t149 + 0.4e1 / 0.3e1 * t147 * t149 * t154 + 0.4e1 / 0.3e1 * t145 * t292)
  t314 = f.my_piecewise3(t141, 0, -0.3e1 / 0.8e1 * t5 * t296 * t42 * t178 - 0.3e1 / 0.8e1 * t5 * t158 * t71 * t178 + t5 * t184 * t102 * t178 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t190 * t238 * t178)
  d111 = 0.3e1 * t139 + 0.3e1 * t196 + t6 * (t282 + t314)

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
  t55 = t53 * t54
  t56 = params.bb * s0
  t57 = r0 ** 2
  t58 = r0 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t64 = jnp.sqrt(s0)
  t65 = params.cc * t64
  t67 = 0.1e1 / t58 / r0
  t68 = 2 ** (0.1e1 / 0.3e1)
  t71 = 0.4e1 * t64 * t67 + t68
  t72 = 0.1e1 / t71
  t75 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * t56 / t59 / t57 + t65 * t67 * t72
  t84 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t85 = t54 ** 2
  t86 = 0.1e1 / t85
  t87 = t84 * t86
  t91 = t84 * t54
  t92 = t57 * r0
  t94 = 0.1e1 / t59 / t92
  t102 = params.cc * s0
  t103 = t71 ** 2
  t104 = 0.1e1 / t103
  t108 = -0.37037037037037037037037037037037037037037037037037e-1 * t56 * t94 - 0.4e1 / 0.3e1 * t65 / t58 / t57 * t72 + 0.16e2 / 0.3e1 * t102 * t94 * t104
  t114 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t116 = 0.1e1 / t85 / t6
  t117 = t114 * t116
  t121 = t114 * t86
  t125 = t114 * t54
  t126 = t57 ** 2
  t128 = 0.1e1 / t59 / t126
  t140 = params.cc * t64 * s0
  t141 = t126 * t57
  t144 = 0.1e1 / t103 / t71
  t148 = 0.13580246913580246913580246913580246913580246913580e0 * t56 * t128 + 0.28e2 / 0.9e1 * t65 / t58 / t92 * t72 - 0.80e2 / 0.3e1 * t102 * t128 * t104 + 0.512e3 / 0.9e1 * t140 / t141 * t144
  t152 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t153 = t152 * f.p.zeta_threshold
  t155 = f.my_piecewise3(t20, t153, t21 * t19)
  t157 = 0.1e1 / t85 / t25
  t158 = t155 * t157
  t162 = t155 * t116
  t166 = t155 * t86
  t170 = t155 * t54
  t171 = t126 * r0
  t173 = 0.1e1 / t59 / t171
  t189 = s0 ** 2
  t190 = params.cc * t189
  t191 = t126 ** 2
  t194 = t103 ** 2
  t195 = 0.1e1 / t194
  t199 = -0.63374485596707818930041152263374485596707818930040e0 * t56 * t173 - 0.280e3 / 0.27e2 * t65 / t58 / t126 * t72 + 0.3808e4 / 0.27e2 * t102 * t173 * t104 - 0.5632e4 / 0.9e1 * t140 / t126 / t92 * t144 + 0.8192e4 / 0.9e1 * t190 / t58 / t191 * t195
  t204 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t75 - 0.3e1 / 0.8e1 * t5 * t87 * t75 - 0.9e1 / 0.8e1 * t5 * t91 * t108 + t5 * t117 * t75 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t121 * t108 - 0.9e1 / 0.8e1 * t5 * t125 * t148 - 0.5e1 / 0.36e2 * t5 * t158 * t75 + t5 * t162 * t108 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t166 * t148 - 0.3e1 / 0.8e1 * t5 * t170 * t199)
  t206 = r1 <= f.p.dens_threshold
  t207 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t208 = 0.1e1 + t207
  t209 = t208 <= f.p.zeta_threshold
  t210 = t208 ** (0.1e1 / 0.3e1)
  t211 = t210 ** 2
  t213 = 0.1e1 / t211 / t208
  t215 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t216 = t215 ** 2
  t220 = 0.1e1 / t211
  t221 = t220 * t215
  t223 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t227 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t231 = f.my_piecewise3(t209, 0, -0.8e1 / 0.27e2 * t213 * t216 * t215 + 0.4e1 / 0.3e1 * t221 * t223 + 0.4e1 / 0.3e1 * t210 * t227)
  t234 = r1 ** 2
  t235 = r1 ** (0.1e1 / 0.3e1)
  t236 = t235 ** 2
  t241 = jnp.sqrt(s2)
  t244 = 0.1e1 / t235 / r1
  t251 = params.aa + 0.13888888888888888888888888888888888888888888888889e-1 * params.bb * s2 / t236 / t234 + params.cc * t241 * t244 / (0.4e1 * t241 * t244 + t68)
  t260 = f.my_piecewise3(t209, 0, 0.4e1 / 0.9e1 * t220 * t216 + 0.4e1 / 0.3e1 * t210 * t223)
  t267 = f.my_piecewise3(t209, 0, 0.4e1 / 0.3e1 * t210 * t215)
  t273 = f.my_piecewise3(t209, t153, t210 * t208)
  t279 = f.my_piecewise3(t206, 0, -0.3e1 / 0.8e1 * t5 * t231 * t54 * t251 - 0.3e1 / 0.8e1 * t5 * t260 * t86 * t251 + t5 * t267 * t116 * t251 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t273 * t157 * t251)
  t285 = 0.1e1 / t59 / t141
  t334 = t19 ** 2
  t337 = t30 ** 2
  t343 = t41 ** 2
  t352 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t353 = f.my_piecewise5(t10, 0, t14, 0, t352)
  t357 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t334 * t337 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t343 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t353)
  t384 = 0.1e1 / t85 / t36
  t389 = -t5 * t166 * t199 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t170 * (0.35912208504801097393689986282578875171467764060356e1 * t56 * t285 + 0.3640e4 / 0.81e2 * t65 / t58 / t171 * t72 - 0.23072e5 / 0.27e2 * t102 * t285 * t104 + 0.476672e6 / 0.81e2 * t140 / t191 * t144 - 0.475136e6 / 0.27e2 * t190 / t58 / t191 / r0 * t195 + 0.524288e6 / 0.27e2 * params.cc * t64 * t189 / t59 / t191 / t57 / t194 / t71) + t5 * t117 * t108 - 0.3e1 / 0.2e1 * t5 * t121 * t148 - 0.3e1 / 0.2e1 * t5 * t125 * t199 - 0.5e1 / 0.9e1 * t5 * t158 * t108 + t5 * t162 * t148 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t357 * t54 * t75 - 0.3e1 / 0.2e1 * t5 * t55 * t108 - 0.3e1 / 0.2e1 * t5 * t87 * t108 - 0.9e1 / 0.4e1 * t5 * t91 * t148 - t5 * t53 * t86 * t75 / 0.2e1 + t5 * t84 * t116 * t75 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t114 * t157 * t75 + 0.10e2 / 0.27e2 * t5 * t155 * t384 * t75
  t390 = f.my_piecewise3(t1, 0, t389)
  t391 = t208 ** 2
  t394 = t216 ** 2
  t400 = t223 ** 2
  t406 = f.my_piecewise5(t14, 0, t10, 0, -t352)
  t410 = f.my_piecewise3(t209, 0, 0.40e2 / 0.81e2 / t211 / t391 * t394 - 0.16e2 / 0.9e1 * t213 * t216 * t223 + 0.4e1 / 0.3e1 * t220 * t400 + 0.16e2 / 0.9e1 * t221 * t227 + 0.4e1 / 0.3e1 * t210 * t406)
  t432 = f.my_piecewise3(t206, 0, -0.3e1 / 0.8e1 * t5 * t410 * t54 * t251 - t5 * t231 * t86 * t251 / 0.2e1 + t5 * t260 * t116 * t251 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t267 * t157 * t251 + 0.10e2 / 0.27e2 * t5 * t273 * t384 * t251)
  d1111 = 0.4e1 * t204 + 0.4e1 * t279 + t6 * (t390 + t432)

  res = {'v4rho4': d1111}
  return res
