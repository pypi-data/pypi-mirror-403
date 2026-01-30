"""Generated from gga_x_pw86.mpl."""

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

  pw86_f0 = lambda s: (1 + params_aa * s ** 2 + params_bb * s ** 4 + params_cc * s ** 6) ** (1 / 15)

  pw86_f = lambda x: pw86_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pw86_f, rs, z, xs0, xs1)

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

  pw86_f0 = lambda s: (1 + params_aa * s ** 2 + params_bb * s ** 4 + params_cc * s ** 6) ** (1 / 15)

  pw86_f = lambda x: pw86_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pw86_f, rs, z, xs0, xs1)

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

  pw86_f0 = lambda s: (1 + params_aa * s ** 2 + params_bb * s ** 4 + params_cc * s ** 6) ** (1 / 15)

  pw86_f = lambda x: pw86_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pw86_f, rs, z, xs0, xs1)

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
  t28 = 6 ** (0.1e1 / 0.3e1)
  t29 = params.aa * t28
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = t33 * s0
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t43 = t28 ** 2
  t44 = params.bb * t43
  t46 = 0.1e1 / t31 / t30
  t47 = s0 ** 2
  t48 = t46 * t47
  t49 = t35 ** 2
  t52 = 0.1e1 / t36 / t49 / r0
  t56 = t30 ** 2
  t58 = params.cc / t56
  t59 = t47 * s0
  t60 = t49 ** 2
  t61 = 0.1e1 / t60
  t66 = (0.1e1 + t29 * t34 * t39 / 0.24e2 + t44 * t48 * t52 / 0.576e3 + t58 * t59 * t61 / 0.2304e4) ** (0.1e1 / 0.15e2)
  t70 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t66)
  t71 = r1 <= f.p.dens_threshold
  t72 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t73 = 0.1e1 + t72
  t74 = t73 <= f.p.zeta_threshold
  t75 = t73 ** (0.1e1 / 0.3e1)
  t77 = f.my_piecewise3(t74, t22, t75 * t73)
  t79 = t33 * s2
  t80 = r1 ** 2
  t81 = r1 ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t84 = 0.1e1 / t82 / t80
  t88 = s2 ** 2
  t89 = t46 * t88
  t90 = t80 ** 2
  t93 = 0.1e1 / t81 / t90 / r1
  t97 = t88 * s2
  t98 = t90 ** 2
  t99 = 0.1e1 / t98
  t104 = (0.1e1 + t29 * t79 * t84 / 0.24e2 + t44 * t89 * t93 / 0.576e3 + t58 * t97 * t99 / 0.2304e4) ** (0.1e1 / 0.15e2)
  t108 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t77 * t26 * t104)
  t109 = t6 ** 2
  t111 = t16 / t109
  t112 = t7 - t111
  t113 = f.my_piecewise5(t10, 0, t14, 0, t112)
  t116 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t113)
  t121 = t26 ** 2
  t122 = 0.1e1 / t121
  t126 = t5 * t25 * t122 * t66 / 0.8e1
  t127 = t5 * t25
  t128 = t66 ** 2
  t129 = t128 ** 2
  t131 = t129 ** 2
  t134 = t26 / t131 / t129 / t128
  t157 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t116 * t26 * t66 - t126 - t127 * t134 * (-t29 * t34 / t37 / t35 / r0 / 0.9e1 - t44 * t48 / t36 / t49 / t35 / 0.108e3 - t58 * t59 / t60 / r0 / 0.288e3) / 0.40e2)
  t159 = f.my_piecewise5(t14, 0, t10, 0, -t112)
  t162 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t75 * t159)
  t170 = t5 * t77 * t122 * t104 / 0.8e1
  t172 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t162 * t26 * t104 - t170)
  vrho_0_ = t70 + t108 + t6 * (t157 + t172)
  t175 = -t7 - t111
  t176 = f.my_piecewise5(t10, 0, t14, 0, t175)
  t179 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t176)
  t185 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t179 * t26 * t66 - t126)
  t187 = f.my_piecewise5(t14, 0, t10, 0, -t175)
  t190 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t75 * t187)
  t195 = t5 * t77
  t196 = t104 ** 2
  t197 = t196 ** 2
  t199 = t197 ** 2
  t202 = t26 / t199 / t197 / t196
  t225 = f.my_piecewise3(t71, 0, -0.3e1 / 0.8e1 * t5 * t190 * t26 * t104 - t170 - t195 * t202 * (-t29 * t79 / t82 / t80 / r1 / 0.9e1 - t44 * t89 / t81 / t90 / t80 / 0.108e3 - t58 * t97 / t98 / r1 / 0.288e3) / 0.40e2)
  vrho_1_ = t70 + t108 + t6 * (t185 + t225)
  t242 = f.my_piecewise3(t1, 0, -t127 * t134 * (t29 * t33 * t39 / 0.24e2 + t44 * t46 * s0 * t52 / 0.288e3 + t58 * t47 * t61 / 0.768e3) / 0.40e2)
  vsigma_0_ = t6 * t242
  vsigma_1_ = 0.0e0
  t257 = f.my_piecewise3(t71, 0, -t195 * t202 * (t29 * t33 * t84 / 0.24e2 + t44 * t46 * s2 * t93 / 0.288e3 + t58 * t88 * t99 / 0.768e3) / 0.40e2)
  vsigma_2_ = t6 * t257
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

  pw86_f0 = lambda s: (1 + params_aa * s ** 2 + params_bb * s ** 4 + params_cc * s ** 6) ** (1 / 15)

  pw86_f = lambda x: pw86_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pw86_f, rs, z, xs0, xs1)

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
  t20 = 6 ** (0.1e1 / 0.3e1)
  t21 = params.aa * t20
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t26 = t21 * t25
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t18 ** 2
  t33 = 0.1e1 / t31 / t30
  t37 = t20 ** 2
  t41 = params.bb * t37 / t23 / t22
  t42 = s0 ** 2
  t43 = t42 * t27
  t44 = t30 ** 2
  t47 = 0.1e1 / t18 / t44 / r0
  t51 = t22 ** 2
  t53 = params.cc / t51
  t54 = t42 * s0
  t55 = t44 ** 2
  t56 = 0.1e1 / t55
  t61 = (0.1e1 + t26 * t29 * t33 / 0.24e2 + t41 * t43 * t47 / 0.288e3 + t53 * t54 * t56 / 0.576e3) ** (0.1e1 / 0.15e2)
  t65 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t61)
  t71 = t6 * t17
  t72 = t61 ** 2
  t73 = t72 ** 2
  t75 = t73 ** 2
  t78 = t18 / t75 / t73 / t72
  t101 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t61 / 0.8e1 - t71 * t78 * (-t26 * t29 / t31 / t30 / r0 / 0.9e1 - t41 * t43 / t18 / t44 / t30 / 0.54e2 - t53 * t54 / t55 / r0 / 0.72e2) / 0.40e2)
  vrho_0_ = 0.2e1 * r0 * t101 + 0.2e1 * t65
  t119 = f.my_piecewise3(t2, 0, -t71 * t78 * (t21 * t25 * t28 * t33 / 0.24e2 + t41 * s0 * t27 * t47 / 0.144e3 + t53 * t42 * t56 / 0.192e3) / 0.40e2)
  vsigma_0_ = 0.2e1 * r0 * t119
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
  t20 = 0.1e1 / t19
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = params.aa * t22
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = t23 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t38 = t22 ** 2
  t39 = params.bb * t38
  t41 = 0.1e1 / t25 / t24
  t42 = t39 * t41
  t43 = s0 ** 2
  t44 = t43 * t29
  t45 = t32 ** 2
  t48 = 0.1e1 / t18 / t45 / r0
  t52 = t24 ** 2
  t54 = params.cc / t52
  t55 = t43 * s0
  t56 = t45 ** 2
  t57 = 0.1e1 / t56
  t61 = 0.1e1 + t28 * t31 * t34 / 0.24e2 + t42 * t44 * t48 / 0.288e3 + t54 * t55 * t57 / 0.576e3
  t62 = t61 ** (0.1e1 / 0.15e2)
  t66 = t6 * t17
  t67 = t62 ** 2
  t68 = t67 ** 2
  t70 = t68 ** 2
  t71 = t70 * t68 * t67
  t72 = 0.1e1 / t71
  t73 = t18 * t72
  t74 = t32 * r0
  t76 = 0.1e1 / t19 / t74
  t82 = 0.1e1 / t18 / t45 / t32
  t87 = 0.1e1 / t56 / r0
  t91 = -t28 * t31 * t76 / 0.9e1 - t42 * t44 * t82 / 0.54e2 - t54 * t55 * t87 / 0.72e2
  t96 = f.my_piecewise3(t2, 0, -t6 * t17 * t20 * t62 / 0.8e1 - t66 * t73 * t91 / 0.40e2)
  t104 = t20 * t72
  t110 = t18 / t71 / t61
  t111 = t91 ** 2
  t136 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t62 / 0.12e2 - t66 * t104 * t91 / 0.60e2 + 0.7e1 / 0.300e3 * t66 * t110 * t111 - t66 * t73 * (0.11e2 / 0.27e2 * t28 * t31 / t19 / t45 + 0.19e2 / 0.162e3 * t42 * t44 / t18 / t45 / t74 + t54 * t55 / t56 / t32 / 0.8e1) / 0.40e2)
  v2rho2_0_ = 0.2e1 * r0 * t136 + 0.4e1 * t96
  t139 = t27 * t30
  t143 = s0 * t29
  t150 = t23 * t139 * t34 / 0.24e2 + t42 * t143 * t48 / 0.144e3 + t54 * t43 * t57 / 0.192e3
  t154 = f.my_piecewise3(t2, 0, -t66 * t73 * t150 / 0.40e2)
  t176 = f.my_piecewise3(t2, 0, -t66 * t104 * t150 / 0.120e3 + 0.7e1 / 0.300e3 * t66 * t110 * t150 * t91 - t66 * t73 * (-t23 * t139 * t76 / 0.9e1 - t42 * t143 * t82 / 0.27e2 - t54 * t43 * t87 / 0.24e2) / 0.40e2)
  v2rhosigma_0_ = 0.2e1 * r0 * t176 + 0.2e1 * t154
  t179 = t150 ** 2
  t195 = f.my_piecewise3(t2, 0, 0.7e1 / 0.300e3 * t66 * t110 * t179 - t66 * t73 * (t39 * t41 * t29 * t48 / 0.144e3 + t54 * s0 * t57 / 0.96e2) / 0.40e2)
  v2sigma2_0_ = 0.2e1 * r0 * t195
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
  t21 = 0.1e1 / t19 / r0
  t23 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t29 = params.aa * t23 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t39 = t23 ** 2
  t43 = params.bb * t39 / t26 / t25
  t44 = s0 ** 2
  t45 = t44 * t30
  t46 = t33 ** 2
  t47 = t46 * r0
  t53 = t25 ** 2
  t55 = params.cc / t53
  t56 = t44 * s0
  t57 = t46 ** 2
  t62 = 0.1e1 + t29 * t32 * t35 / 0.24e2 + t43 * t45 / t18 / t47 / 0.288e3 + t55 * t56 / t57 / 0.576e3
  t63 = t62 ** (0.1e1 / 0.15e2)
  t67 = t6 * t17
  t68 = 0.1e1 / t19
  t69 = t63 ** 2
  t70 = t69 ** 2
  t72 = t70 ** 2
  t73 = t72 * t70 * t69
  t74 = 0.1e1 / t73
  t75 = t68 * t74
  t76 = t33 * r0
  t93 = -t29 * t32 / t19 / t76 / 0.9e1 - t43 * t45 / t18 / t46 / t33 / 0.54e2 - t55 * t56 / t57 / r0 / 0.72e2
  t98 = 0.1e1 / t73 / t62
  t99 = t18 * t98
  t100 = t93 ** 2
  t104 = t18 * t74
  t121 = 0.11e2 / 0.27e2 * t29 * t32 / t19 / t46 + 0.19e2 / 0.162e3 * t43 * t45 / t18 / t46 / t76 + t55 * t56 / t57 / t33 / 0.8e1
  t126 = f.my_piecewise3(t2, 0, t6 * t17 * t21 * t63 / 0.12e2 - t67 * t75 * t93 / 0.60e2 + 0.7e1 / 0.300e3 * t67 * t99 * t100 - t67 * t104 * t121 / 0.40e2)
  t143 = t62 ** 2
  t175 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t63 + t67 * t21 * t74 * t93 / 0.60e2 + 0.7e1 / 0.300e3 * t67 * t68 * t98 * t100 - t67 * t75 * t121 / 0.40e2 - 0.203e3 / 0.4500e4 * t67 * t18 / t73 / t143 * t100 * t93 + 0.7e1 / 0.100e3 * t67 * t99 * t93 * t121 - t67 * t104 * (-0.154e3 / 0.81e2 * t29 * t32 / t19 / t47 - 0.209e3 / 0.243e3 * t43 * t45 / t18 / t57 - 0.5e1 / 0.4e1 * t55 * t56 / t57 / t76) / 0.40e2)
  v3rho3_0_ = 0.2e1 * r0 * t175 + 0.6e1 * t126

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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t30 = params.aa * t24 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t37 = t24 ** 2
  t41 = params.bb * t37 / t27 / t26
  t42 = s0 ** 2
  t43 = t42 * t31
  t44 = t18 ** 2
  t45 = t44 * r0
  t51 = t26 ** 2
  t53 = params.cc / t51
  t54 = t42 * s0
  t55 = t44 ** 2
  t60 = 0.1e1 + t30 * t33 * t22 / 0.24e2 + t41 * t43 / t19 / t45 / 0.288e3 + t53 * t54 / t55 / 0.576e3
  t61 = t60 ** (0.1e1 / 0.15e2)
  t65 = t6 * t17
  t67 = 0.1e1 / t20 / r0
  t68 = t61 ** 2
  t69 = t68 ** 2
  t71 = t69 ** 2
  t72 = t71 * t69 * t68
  t73 = 0.1e1 / t72
  t74 = t67 * t73
  t75 = t18 * r0
  t77 = 0.1e1 / t20 / t75
  t81 = t44 * t18
  t87 = t55 * r0
  t92 = -t30 * t33 * t77 / 0.9e1 - t41 * t43 / t19 / t81 / 0.54e2 - t53 * t54 / t87 / 0.72e2
  t96 = 0.1e1 / t20
  t98 = 0.1e1 / t72 / t60
  t99 = t96 * t98
  t100 = t92 ** 2
  t104 = t96 * t73
  t121 = 0.11e2 / 0.27e2 * t30 * t33 / t20 / t44 + 0.19e2 / 0.162e3 * t41 * t43 / t19 / t44 / t75 + t53 * t54 / t55 / t18 / 0.8e1
  t125 = t60 ** 2
  t127 = 0.1e1 / t72 / t125
  t128 = t19 * t127
  t129 = t100 * t92
  t133 = t19 * t98
  t134 = t92 * t121
  t138 = t19 * t73
  t154 = -0.154e3 / 0.81e2 * t30 * t33 / t20 / t45 - 0.209e3 / 0.243e3 * t41 * t43 / t19 / t55 - 0.5e1 / 0.4e1 * t53 * t54 / t55 / t75
  t159 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t61 + t65 * t74 * t92 / 0.60e2 + 0.7e1 / 0.300e3 * t65 * t99 * t100 - t65 * t104 * t121 / 0.40e2 - 0.203e3 / 0.4500e4 * t65 * t128 * t129 + 0.7e1 / 0.100e3 * t65 * t133 * t134 - t65 * t138 * t154 / 0.40e2)
  t190 = t100 ** 2
  t198 = t121 ** 2
  t225 = 0.10e2 / 0.27e2 * t6 * t17 * t77 * t61 - t65 * t22 * t73 * t92 / 0.27e2 - 0.7e1 / 0.225e3 * t65 * t67 * t98 * t100 + t65 * t74 * t121 / 0.30e2 - 0.203e3 / 0.3375e4 * t65 * t96 * t127 * t129 + 0.7e1 / 0.75e2 * t65 * t99 * t134 - t65 * t104 * t154 / 0.30e2 + 0.2233e4 / 0.16875e5 * t65 * t19 / t72 / t125 / t60 * t190 - 0.203e3 / 0.750e3 * t65 * t128 * t100 * t121 + 0.7e1 / 0.100e3 * t65 * t133 * t198 + 0.7e1 / 0.75e2 * t65 * t133 * t92 * t154 - t65 * t138 * (0.2618e4 / 0.243e3 * t30 * t33 / t20 / t81 + 0.5225e4 / 0.729e3 * t41 * t43 / t19 / t87 + 0.55e2 / 0.4e1 * t53 * t54 / t55 / t44) / 0.40e2
  t226 = f.my_piecewise3(t2, 0, t225)
  v4rho4_0_ = 0.2e1 * r0 * t226 + 0.8e1 * t159

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
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = params.aa * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t47 = t32 ** 2
  t48 = params.bb * t47
  t50 = 0.1e1 / t35 / t34
  t51 = s0 ** 2
  t52 = t50 * t51
  t53 = t39 ** 2
  t60 = t34 ** 2
  t62 = params.cc / t60
  t63 = t51 * s0
  t64 = t53 ** 2
  t69 = 0.1e1 + t33 * t38 / t41 / t39 / 0.24e2 + t48 * t52 / t40 / t53 / r0 / 0.576e3 + t62 * t63 / t64 / 0.2304e4
  t70 = t69 ** (0.1e1 / 0.15e2)
  t74 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t75 = t74 * f.p.zeta_threshold
  t77 = f.my_piecewise3(t20, t75, t21 * t19)
  t78 = t30 ** 2
  t79 = 0.1e1 / t78
  t83 = t5 * t77 * t79 * t70 / 0.8e1
  t84 = t5 * t77
  t85 = t70 ** 2
  t86 = t85 ** 2
  t88 = t86 ** 2
  t89 = t88 * t86 * t85
  t90 = 0.1e1 / t89
  t91 = t30 * t90
  t92 = t39 * r0
  t109 = -t33 * t38 / t41 / t92 / 0.9e1 - t48 * t52 / t40 / t53 / t39 / 0.108e3 - t62 * t63 / t64 / r0 / 0.288e3
  t110 = t91 * t109
  t114 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t70 - t83 - t84 * t110 / 0.40e2)
  t116 = r1 <= f.p.dens_threshold
  t117 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t118 = 0.1e1 + t117
  t119 = t118 <= f.p.zeta_threshold
  t120 = t118 ** (0.1e1 / 0.3e1)
  t122 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t125 = f.my_piecewise3(t119, 0, 0.4e1 / 0.3e1 * t120 * t122)
  t127 = t37 * s2
  t128 = r1 ** 2
  t129 = r1 ** (0.1e1 / 0.3e1)
  t130 = t129 ** 2
  t136 = s2 ** 2
  t137 = t50 * t136
  t138 = t128 ** 2
  t145 = t136 * s2
  t146 = t138 ** 2
  t151 = 0.1e1 + t33 * t127 / t130 / t128 / 0.24e2 + t48 * t137 / t129 / t138 / r1 / 0.576e3 + t62 * t145 / t146 / 0.2304e4
  t152 = t151 ** (0.1e1 / 0.15e2)
  t157 = f.my_piecewise3(t119, t75, t120 * t118)
  t161 = t5 * t157 * t79 * t152 / 0.8e1
  t163 = f.my_piecewise3(t116, 0, -0.3e1 / 0.8e1 * t5 * t125 * t30 * t152 - t161)
  t165 = t21 ** 2
  t166 = 0.1e1 / t165
  t167 = t26 ** 2
  t172 = t16 / t22 / t6
  t174 = -0.2e1 * t23 + 0.2e1 * t172
  t175 = f.my_piecewise5(t10, 0, t14, 0, t174)
  t179 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t166 * t167 + 0.4e1 / 0.3e1 * t21 * t175)
  t186 = t5 * t29 * t79 * t70
  t192 = 0.1e1 / t78 / t6
  t196 = t5 * t77 * t192 * t70 / 0.12e2
  t199 = t84 * t79 * t90 * t109
  t204 = t109 ** 2
  t229 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t179 * t30 * t70 - t186 / 0.4e1 - t5 * t29 * t110 / 0.20e2 + t196 - t199 / 0.60e2 + 0.7e1 / 0.300e3 * t84 * t30 / t89 / t69 * t204 - t84 * t91 * (0.11e2 / 0.27e2 * t33 * t38 / t41 / t53 + 0.19e2 / 0.324e3 * t48 * t52 / t40 / t53 / t92 + t62 * t63 / t64 / t39 / 0.32e2) / 0.40e2)
  t230 = t120 ** 2
  t231 = 0.1e1 / t230
  t232 = t122 ** 2
  t236 = f.my_piecewise5(t14, 0, t10, 0, -t174)
  t240 = f.my_piecewise3(t119, 0, 0.4e1 / 0.9e1 * t231 * t232 + 0.4e1 / 0.3e1 * t120 * t236)
  t247 = t5 * t125 * t79 * t152
  t252 = t5 * t157 * t192 * t152 / 0.12e2
  t254 = f.my_piecewise3(t116, 0, -0.3e1 / 0.8e1 * t5 * t240 * t30 * t152 - t247 / 0.4e1 + t252)
  d11 = 0.2e1 * t114 + 0.2e1 * t163 + t6 * (t229 + t254)
  t257 = -t7 - t24
  t258 = f.my_piecewise5(t10, 0, t14, 0, t257)
  t261 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t258)
  t267 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t261 * t30 * t70 - t83)
  t269 = f.my_piecewise5(t14, 0, t10, 0, -t257)
  t272 = f.my_piecewise3(t119, 0, 0.4e1 / 0.3e1 * t120 * t269)
  t277 = t5 * t157
  t278 = t152 ** 2
  t279 = t278 ** 2
  t281 = t279 ** 2
  t282 = t281 * t279 * t278
  t283 = 0.1e1 / t282
  t284 = t30 * t283
  t285 = t128 * r1
  t302 = -t33 * t127 / t130 / t285 / 0.9e1 - t48 * t137 / t129 / t138 / t128 / 0.108e3 - t62 * t145 / t146 / r1 / 0.288e3
  t303 = t284 * t302
  t307 = f.my_piecewise3(t116, 0, -0.3e1 / 0.8e1 * t5 * t272 * t30 * t152 - t161 - t277 * t303 / 0.40e2)
  t311 = 0.2e1 * t172
  t312 = f.my_piecewise5(t10, 0, t14, 0, t311)
  t316 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t166 * t258 * t26 + 0.4e1 / 0.3e1 * t21 * t312)
  t323 = t5 * t261 * t79 * t70
  t331 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t316 * t30 * t70 - t323 / 0.8e1 - t5 * t261 * t110 / 0.40e2 - t186 / 0.8e1 + t196 - t199 / 0.120e3)
  t335 = f.my_piecewise5(t14, 0, t10, 0, -t311)
  t339 = f.my_piecewise3(t119, 0, 0.4e1 / 0.9e1 * t231 * t269 * t122 + 0.4e1 / 0.3e1 * t120 * t335)
  t346 = t5 * t272 * t79 * t152
  t354 = t277 * t79 * t283 * t302
  t357 = f.my_piecewise3(t116, 0, -0.3e1 / 0.8e1 * t5 * t339 * t30 * t152 - t346 / 0.8e1 - t247 / 0.8e1 + t252 - t5 * t125 * t303 / 0.40e2 - t354 / 0.120e3)
  d12 = t114 + t163 + t267 + t307 + t6 * (t331 + t357)
  t362 = t258 ** 2
  t366 = 0.2e1 * t23 + 0.2e1 * t172
  t367 = f.my_piecewise5(t10, 0, t14, 0, t366)
  t371 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t166 * t362 + 0.4e1 / 0.3e1 * t21 * t367)
  t378 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t371 * t30 * t70 - t323 / 0.4e1 + t196)
  t379 = t269 ** 2
  t383 = f.my_piecewise5(t14, 0, t10, 0, -t366)
  t387 = f.my_piecewise3(t119, 0, 0.4e1 / 0.9e1 * t231 * t379 + 0.4e1 / 0.3e1 * t120 * t383)
  t400 = t302 ** 2
  t425 = f.my_piecewise3(t116, 0, -0.3e1 / 0.8e1 * t5 * t387 * t30 * t152 - t346 / 0.4e1 - t5 * t272 * t303 / 0.20e2 + t252 - t354 / 0.60e2 + 0.7e1 / 0.300e3 * t277 * t30 / t282 / t151 * t400 - t277 * t284 * (0.11e2 / 0.27e2 * t33 * t127 / t130 / t138 + 0.19e2 / 0.324e3 * t48 * t137 / t129 / t138 / t285 + t62 * t145 / t146 / t128 / 0.32e2) / 0.40e2)
  d22 = 0.2e1 * t267 + 0.2e1 * t307 + t6 * (t378 + t425)
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
  t44 = 6 ** (0.1e1 / 0.3e1)
  t45 = params.aa * t44
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t50 = t49 * s0
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t59 = t44 ** 2
  t60 = params.bb * t59
  t62 = 0.1e1 / t47 / t46
  t63 = s0 ** 2
  t64 = t62 * t63
  t65 = t51 ** 2
  t66 = t65 * r0
  t72 = t46 ** 2
  t74 = params.cc / t72
  t75 = t63 * s0
  t76 = t65 ** 2
  t81 = 0.1e1 + t45 * t50 / t53 / t51 / 0.24e2 + t60 * t64 / t52 / t66 / 0.576e3 + t74 * t75 / t76 / 0.2304e4
  t82 = t81 ** (0.1e1 / 0.15e2)
  t88 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t89 = t42 ** 2
  t90 = 0.1e1 / t89
  t95 = t5 * t88
  t96 = t82 ** 2
  t97 = t96 ** 2
  t99 = t97 ** 2
  t100 = t99 * t97 * t96
  t101 = 0.1e1 / t100
  t102 = t42 * t101
  t103 = t51 * r0
  t120 = -t45 * t50 / t53 / t103 / 0.9e1 - t60 * t64 / t52 / t65 / t51 / 0.108e3 - t74 * t75 / t76 / r0 / 0.288e3
  t121 = t102 * t120
  t124 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t125 = t124 * f.p.zeta_threshold
  t127 = f.my_piecewise3(t20, t125, t21 * t19)
  t129 = 0.1e1 / t89 / t6
  t134 = t5 * t127
  t135 = t90 * t101
  t136 = t135 * t120
  t140 = 0.1e1 / t100 / t81
  t141 = t42 * t140
  t142 = t120 ** 2
  t143 = t141 * t142
  t162 = 0.11e2 / 0.27e2 * t45 * t50 / t53 / t65 + 0.19e2 / 0.324e3 * t60 * t64 / t52 / t65 / t103 + t74 * t75 / t76 / t51 / 0.32e2
  t163 = t102 * t162
  t167 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t82 - t5 * t88 * t90 * t82 / 0.4e1 - t95 * t121 / 0.20e2 + t5 * t127 * t129 * t82 / 0.12e2 - t134 * t136 / 0.60e2 + 0.7e1 / 0.300e3 * t134 * t143 - t134 * t163 / 0.40e2)
  t169 = r1 <= f.p.dens_threshold
  t170 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t171 = 0.1e1 + t170
  t172 = t171 <= f.p.zeta_threshold
  t173 = t171 ** (0.1e1 / 0.3e1)
  t174 = t173 ** 2
  t175 = 0.1e1 / t174
  t177 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t178 = t177 ** 2
  t182 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t186 = f.my_piecewise3(t172, 0, 0.4e1 / 0.9e1 * t175 * t178 + 0.4e1 / 0.3e1 * t173 * t182)
  t189 = r1 ** 2
  t190 = r1 ** (0.1e1 / 0.3e1)
  t191 = t190 ** 2
  t197 = s2 ** 2
  t199 = t189 ** 2
  t207 = t199 ** 2
  t213 = (0.1e1 + t45 * t49 * s2 / t191 / t189 / 0.24e2 + t60 * t62 * t197 / t190 / t199 / r1 / 0.576e3 + t74 * t197 * s2 / t207 / 0.2304e4) ** (0.1e1 / 0.15e2)
  t219 = f.my_piecewise3(t172, 0, 0.4e1 / 0.3e1 * t173 * t177)
  t225 = f.my_piecewise3(t172, t125, t173 * t171)
  t231 = f.my_piecewise3(t169, 0, -0.3e1 / 0.8e1 * t5 * t186 * t42 * t213 - t5 * t219 * t90 * t213 / 0.4e1 + t5 * t225 * t129 * t213 / 0.12e2)
  t239 = t81 ** 2
  t259 = t24 ** 2
  t263 = 0.6e1 * t33 - 0.6e1 * t16 / t259
  t264 = f.my_piecewise5(t10, 0, t14, 0, t263)
  t268 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t264)
  t289 = 0.1e1 / t89 / t24
  t320 = 0.7e1 / 0.100e3 * t95 * t143 + 0.7e1 / 0.300e3 * t134 * t90 * t140 * t142 - 0.203e3 / 0.4500e4 * t134 * t42 / t100 / t239 * t142 * t120 + 0.7e1 / 0.100e3 * t134 * t141 * t120 * t162 - 0.3e1 / 0.8e1 * t5 * t268 * t42 * t82 - 0.3e1 / 0.8e1 * t5 * t41 * t90 * t82 - 0.3e1 / 0.40e2 * t5 * t41 * t121 + t5 * t88 * t129 * t82 / 0.4e1 - t95 * t136 / 0.20e2 - 0.3e1 / 0.40e2 * t95 * t163 - 0.5e1 / 0.36e2 * t5 * t127 * t289 * t82 + t134 * t129 * t101 * t120 / 0.60e2 - t134 * t135 * t162 / 0.40e2 - t134 * t102 * (-0.154e3 / 0.81e2 * t45 * t50 / t53 / t66 - 0.209e3 / 0.486e3 * t60 * t64 / t52 / t76 - 0.5e1 / 0.16e2 * t74 * t75 / t76 / t103) / 0.40e2
  t321 = f.my_piecewise3(t1, 0, t320)
  t331 = f.my_piecewise5(t14, 0, t10, 0, -t263)
  t335 = f.my_piecewise3(t172, 0, -0.8e1 / 0.27e2 / t174 / t171 * t178 * t177 + 0.4e1 / 0.3e1 * t175 * t177 * t182 + 0.4e1 / 0.3e1 * t173 * t331)
  t353 = f.my_piecewise3(t169, 0, -0.3e1 / 0.8e1 * t5 * t335 * t42 * t213 - 0.3e1 / 0.8e1 * t5 * t186 * t90 * t213 + t5 * t219 * t129 * t213 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t225 * t289 * t213)
  d111 = 0.3e1 * t167 + 0.3e1 * t231 + t6 * (t321 + t353)

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
  t22 = t6 ** 2
  t23 = 0.1e1 / t22
  t25 = -t16 * t23 + t7
  t26 = f.my_piecewise5(t10, 0, t14, 0, t25)
  t29 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t26)
  t30 = t5 * t29
  t31 = t6 ** (0.1e1 / 0.3e1)
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = params.aa * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t47 = t32 ** 2
  t48 = params.bb * t47
  t50 = 0.1e1 / t35 / t34
  t51 = s0 ** 2
  t52 = t50 * t51
  t53 = t39 ** 2
  t54 = t53 * r0
  t60 = t34 ** 2
  t62 = params.cc / t60
  t63 = t51 * s0
  t64 = t53 ** 2
  t69 = 0.1e1 + t33 * t38 / t41 / t39 / 0.24e2 + t48 * t52 / t40 / t54 / 0.576e3 + t62 * t63 / t64 / 0.2304e4
  t70 = t69 ** (0.1e1 / 0.15e2)
  t71 = t70 ** 2
  t72 = t71 ** 2
  t74 = t72 ** 2
  t75 = t74 * t72 * t71
  t77 = 0.1e1 / t75 / t69
  t78 = t31 * t77
  t79 = t39 * r0
  t85 = t53 * t39
  t91 = t64 * r0
  t96 = -t33 * t38 / t41 / t79 / 0.9e1 - t48 * t52 / t40 / t85 / 0.108e3 - t62 * t63 / t91 / 0.288e3
  t97 = t96 ** 2
  t98 = t78 * t97
  t101 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t102 = t101 * f.p.zeta_threshold
  t104 = f.my_piecewise3(t20, t102, t21 * t19)
  t105 = t5 * t104
  t106 = t31 ** 2
  t107 = 0.1e1 / t106
  t108 = t107 * t77
  t109 = t108 * t97
  t112 = t69 ** 2
  t114 = 0.1e1 / t75 / t112
  t115 = t31 * t114
  t116 = t97 * t96
  t117 = t115 * t116
  t136 = 0.11e2 / 0.27e2 * t33 * t38 / t41 / t53 + 0.19e2 / 0.324e3 * t48 * t52 / t40 / t53 / t79 + t62 * t63 / t64 / t39 / 0.32e2
  t137 = t96 * t136
  t138 = t78 * t137
  t141 = t21 ** 2
  t143 = 0.1e1 / t141 / t19
  t144 = t26 ** 2
  t148 = 0.1e1 / t141
  t149 = t148 * t26
  t150 = t22 * t6
  t151 = 0.1e1 / t150
  t154 = 0.2e1 * t16 * t151 - 0.2e1 * t23
  t155 = f.my_piecewise5(t10, 0, t14, 0, t154)
  t158 = t22 ** 2
  t159 = 0.1e1 / t158
  t162 = -0.6e1 * t16 * t159 + 0.6e1 * t151
  t163 = f.my_piecewise5(t10, 0, t14, 0, t162)
  t167 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t143 * t144 * t26 + 0.4e1 / 0.3e1 * t149 * t155 + 0.4e1 / 0.3e1 * t21 * t163)
  t177 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t148 * t144 + 0.4e1 / 0.3e1 * t21 * t155)
  t182 = t5 * t177
  t183 = 0.1e1 / t75
  t184 = t31 * t183
  t185 = t184 * t96
  t189 = 0.1e1 / t106 / t6
  t194 = t107 * t183
  t195 = t194 * t96
  t198 = t184 * t136
  t202 = 0.1e1 / t106 / t22
  t207 = t189 * t183
  t208 = t207 * t96
  t211 = t194 * t136
  t229 = -0.154e3 / 0.81e2 * t33 * t38 / t41 / t54 - 0.209e3 / 0.486e3 * t48 * t52 / t40 / t64 - 0.5e1 / 0.16e2 * t62 * t63 / t64 / t79
  t230 = t184 * t229
  t233 = 0.7e1 / 0.100e3 * t30 * t98 + 0.7e1 / 0.300e3 * t105 * t109 - 0.203e3 / 0.4500e4 * t105 * t117 + 0.7e1 / 0.100e3 * t105 * t138 - 0.3e1 / 0.8e1 * t5 * t167 * t31 * t70 - 0.3e1 / 0.8e1 * t5 * t177 * t107 * t70 - 0.3e1 / 0.40e2 * t182 * t185 + t5 * t29 * t189 * t70 / 0.4e1 - t30 * t195 / 0.20e2 - 0.3e1 / 0.40e2 * t30 * t198 - 0.5e1 / 0.36e2 * t5 * t104 * t202 * t70 + t105 * t208 / 0.60e2 - t105 * t211 / 0.40e2 - t105 * t230 / 0.40e2
  t234 = f.my_piecewise3(t1, 0, t233)
  t236 = r1 <= f.p.dens_threshold
  t237 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t238 = 0.1e1 + t237
  t239 = t238 <= f.p.zeta_threshold
  t240 = t238 ** (0.1e1 / 0.3e1)
  t241 = t240 ** 2
  t243 = 0.1e1 / t241 / t238
  t245 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t246 = t245 ** 2
  t250 = 0.1e1 / t241
  t251 = t250 * t245
  t253 = f.my_piecewise5(t14, 0, t10, 0, -t154)
  t257 = f.my_piecewise5(t14, 0, t10, 0, -t162)
  t261 = f.my_piecewise3(t239, 0, -0.8e1 / 0.27e2 * t243 * t246 * t245 + 0.4e1 / 0.3e1 * t251 * t253 + 0.4e1 / 0.3e1 * t240 * t257)
  t264 = r1 ** 2
  t265 = r1 ** (0.1e1 / 0.3e1)
  t266 = t265 ** 2
  t272 = s2 ** 2
  t274 = t264 ** 2
  t282 = t274 ** 2
  t288 = (0.1e1 + t33 * t37 * s2 / t266 / t264 / 0.24e2 + t48 * t50 * t272 / t265 / t274 / r1 / 0.576e3 + t62 * t272 * s2 / t282 / 0.2304e4) ** (0.1e1 / 0.15e2)
  t297 = f.my_piecewise3(t239, 0, 0.4e1 / 0.9e1 * t250 * t246 + 0.4e1 / 0.3e1 * t240 * t253)
  t304 = f.my_piecewise3(t239, 0, 0.4e1 / 0.3e1 * t240 * t245)
  t310 = f.my_piecewise3(t239, t102, t240 * t238)
  t316 = f.my_piecewise3(t236, 0, -0.3e1 / 0.8e1 * t5 * t261 * t31 * t288 - 0.3e1 / 0.8e1 * t5 * t297 * t107 * t288 + t5 * t304 * t189 * t288 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t310 * t202 * t288)
  t319 = 0.1e1 / t106 / t150
  t324 = t19 ** 2
  t327 = t144 ** 2
  t333 = t155 ** 2
  t342 = -0.24e2 * t159 + 0.24e2 * t16 / t158 / t6
  t343 = f.my_piecewise5(t10, 0, t14, 0, t342)
  t347 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t141 / t324 * t327 - 0.16e2 / 0.9e1 * t143 * t144 * t155 + 0.4e1 / 0.3e1 * t148 * t333 + 0.16e2 / 0.9e1 * t149 * t163 + 0.4e1 / 0.3e1 * t21 * t343)
  t403 = 0.10e2 / 0.27e2 * t5 * t104 * t319 * t70 - 0.3e1 / 0.8e1 * t5 * t347 * t31 * t70 - t5 * t167 * t107 * t70 / 0.2e1 + t5 * t177 * t189 * t70 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t29 * t202 * t70 + t30 * t208 / 0.15e2 - t30 * t211 / 0.10e2 - t30 * t230 / 0.10e2 - t105 * t202 * t183 * t96 / 0.27e2 + t105 * t207 * t136 / 0.30e2 - t105 * t194 * t229 / 0.30e2 - t105 * t184 * (0.2618e4 / 0.243e3 * t33 * t38 / t41 / t85 + 0.5225e4 / 0.1458e4 * t48 * t52 / t40 / t91 + 0.55e2 / 0.16e2 * t62 * t63 / t64 / t53) / 0.40e2 - 0.7e1 / 0.225e3 * t105 * t189 * t77 * t97
  t412 = t97 ** 2
  t416 = t136 ** 2
  t446 = -0.203e3 / 0.3375e4 * t105 * t107 * t114 * t116 + 0.2233e4 / 0.16875e5 * t105 * t31 / t75 / t112 / t69 * t412 + 0.7e1 / 0.100e3 * t105 * t78 * t416 + 0.7e1 / 0.50e2 * t182 * t98 - t5 * t167 * t185 / 0.10e2 - t182 * t195 / 0.10e2 - 0.3e1 / 0.20e2 * t182 * t198 + 0.7e1 / 0.75e2 * t30 * t109 - 0.203e3 / 0.1125e4 * t30 * t117 + 0.7e1 / 0.25e2 * t30 * t138 + 0.7e1 / 0.75e2 * t105 * t108 * t137 - 0.203e3 / 0.750e3 * t105 * t115 * t97 * t136 + 0.7e1 / 0.75e2 * t105 * t78 * t96 * t229
  t448 = f.my_piecewise3(t1, 0, t403 + t446)
  t449 = t238 ** 2
  t452 = t246 ** 2
  t458 = t253 ** 2
  t464 = f.my_piecewise5(t14, 0, t10, 0, -t342)
  t468 = f.my_piecewise3(t239, 0, 0.40e2 / 0.81e2 / t241 / t449 * t452 - 0.16e2 / 0.9e1 * t243 * t246 * t253 + 0.4e1 / 0.3e1 * t250 * t458 + 0.16e2 / 0.9e1 * t251 * t257 + 0.4e1 / 0.3e1 * t240 * t464)
  t490 = f.my_piecewise3(t236, 0, -0.3e1 / 0.8e1 * t5 * t468 * t31 * t288 - t5 * t261 * t107 * t288 / 0.2e1 + t5 * t297 * t189 * t288 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t304 * t202 * t288 + 0.10e2 / 0.27e2 * t5 * t310 * t319 * t288)
  d1111 = 0.4e1 * t234 + 0.4e1 * t316 + t6 * (t448 + t490)

  res = {'v4rho4': d1111}
  return res
