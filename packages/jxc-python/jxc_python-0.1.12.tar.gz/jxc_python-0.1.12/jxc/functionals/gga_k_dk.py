"""Generated from gga_k_dk.mpl."""

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

  dk_f = lambda x: jnp.sum(jnp.array([params_aa[i] * x ** (2 * (i - 1)) for i in range(1, 5 + 1)]), axis=0) / jnp.sum(jnp.array([params_bb[i] * x ** (2 * (i - 1)) for i in range(1, 5 + 1)]), axis=0)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, dk_f, rs, zeta, xs0, xs1)

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

  dk_f = lambda x: jnp.sum(jnp.array([params_aa[i] * x ** (2 * (i - 1)) for i in range(1, 5 + 1)]), axis=0) / jnp.sum(jnp.array([params_bb[i] * x ** (2 * (i - 1)) for i in range(1, 5 + 1)]), axis=0)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, dk_f, rs, zeta, xs0, xs1)

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

  dk_f = lambda x: jnp.sum(jnp.array([params_aa[i] * x ** (2 * (i - 1)) for i in range(1, 5 + 1)]), axis=0) / jnp.sum(jnp.array([params_bb[i] * x ** (2 * (i - 1)) for i in range(1, 5 + 1)]), axis=0)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, dk_f, rs, zeta, xs0, xs1)

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
  t29 = t6 * t28
  t30 = t7 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = params.aa[0]
  t33 = params.aa[1]
  t34 = t33 * s0
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t41 = params.aa[2]
  t42 = s0 ** 2
  t43 = t41 * t42
  t44 = t35 ** 2
  t47 = 0.1e1 / t36 / t44 / r0
  t49 = params.aa[3]
  t50 = t42 * s0
  t51 = t49 * t50
  t52 = t44 ** 2
  t53 = 0.1e1 / t52
  t55 = params.aa[4]
  t56 = t42 ** 2
  t57 = t55 * t56
  t60 = 0.1e1 / t37 / t52 / t35
  t62 = t34 * t39 + t43 * t47 + t51 * t53 + t57 * t60 + t32
  t63 = t31 * t62
  t64 = params.bb[0]
  t65 = params.bb[1]
  t66 = t65 * s0
  t68 = params.bb[2]
  t69 = t68 * t42
  t71 = params.bb[3]
  t72 = t71 * t50
  t74 = params.bb[4]
  t75 = t74 * t56
  t77 = t66 * t39 + t69 * t47 + t72 * t53 + t75 * t60 + t64
  t78 = 0.1e1 / t77
  t79 = t63 * t78
  t82 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t29 * t79)
  t83 = r1 <= f.p.dens_threshold
  t84 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t85 = 0.1e1 + t84
  t86 = t85 <= f.p.zeta_threshold
  t87 = t85 ** (0.1e1 / 0.3e1)
  t88 = t87 ** 2
  t90 = f.my_piecewise3(t86, t24, t88 * t85)
  t91 = t6 * t90
  t92 = t33 * s2
  t93 = r1 ** 2
  t94 = r1 ** (0.1e1 / 0.3e1)
  t95 = t94 ** 2
  t97 = 0.1e1 / t95 / t93
  t99 = s2 ** 2
  t100 = t41 * t99
  t101 = t93 ** 2
  t104 = 0.1e1 / t94 / t101 / r1
  t106 = t99 * s2
  t107 = t49 * t106
  t108 = t101 ** 2
  t109 = 0.1e1 / t108
  t111 = t99 ** 2
  t112 = t55 * t111
  t115 = 0.1e1 / t95 / t108 / t93
  t117 = t100 * t104 + t107 * t109 + t112 * t115 + t92 * t97 + t32
  t118 = t31 * t117
  t119 = t65 * s2
  t121 = t68 * t99
  t123 = t71 * t106
  t125 = t74 * t111
  t127 = t121 * t104 + t123 * t109 + t125 * t115 + t119 * t97 + t64
  t128 = 0.1e1 / t127
  t129 = t118 * t128
  t132 = f.my_piecewise3(t83, 0, 0.3e1 / 0.20e2 * t91 * t129)
  t133 = t7 ** 2
  t135 = t17 / t133
  t136 = t8 - t135
  t137 = f.my_piecewise5(t11, 0, t15, 0, t136)
  t140 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t137)
  t144 = 0.1e1 / t30
  t148 = t29 * t144 * t62 * t78 / 0.10e2
  t149 = t35 * r0
  t151 = 0.1e1 / t37 / t149
  t156 = 0.1e1 / t36 / t44 / t35
  t160 = 0.1e1 / t52 / r0
  t165 = 0.1e1 / t37 / t52 / t149
  t173 = t77 ** 2
  t174 = 0.1e1 / t173
  t189 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t140 * t79 + t148 + 0.3e1 / 0.20e2 * t29 * t31 * (-0.8e1 / 0.3e1 * t34 * t151 - 0.16e2 / 0.3e1 * t43 * t156 - 0.8e1 * t51 * t160 - 0.32e2 / 0.3e1 * t57 * t165) * t78 - 0.3e1 / 0.20e2 * t29 * t63 * t174 * (-0.8e1 / 0.3e1 * t66 * t151 - 0.16e2 / 0.3e1 * t69 * t156 - 0.8e1 * t72 * t160 - 0.32e2 / 0.3e1 * t75 * t165))
  t191 = f.my_piecewise5(t15, 0, t11, 0, -t136)
  t194 = f.my_piecewise3(t86, 0, 0.5e1 / 0.3e1 * t88 * t191)
  t201 = t91 * t144 * t117 * t128 / 0.10e2
  t203 = f.my_piecewise3(t83, 0, 0.3e1 / 0.20e2 * t6 * t194 * t129 + t201)
  vrho_0_ = t82 + t132 + t7 * (t189 + t203)
  t206 = -t8 - t135
  t207 = f.my_piecewise5(t11, 0, t15, 0, t206)
  t210 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t207)
  t215 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t210 * t79 + t148)
  t217 = f.my_piecewise5(t15, 0, t11, 0, -t206)
  t220 = f.my_piecewise3(t86, 0, 0.5e1 / 0.3e1 * t88 * t217)
  t224 = t93 * r1
  t226 = 0.1e1 / t95 / t224
  t231 = 0.1e1 / t94 / t101 / t93
  t235 = 0.1e1 / t108 / r1
  t240 = 0.1e1 / t95 / t108 / t224
  t248 = t127 ** 2
  t249 = 0.1e1 / t248
  t264 = f.my_piecewise3(t83, 0, 0.3e1 / 0.20e2 * t6 * t220 * t129 + t201 + 0.3e1 / 0.20e2 * t91 * t31 * (-0.8e1 / 0.3e1 * t92 * t226 - 0.16e2 / 0.3e1 * t100 * t231 - 0.8e1 * t107 * t235 - 0.32e2 / 0.3e1 * t112 * t240) * t128 - 0.3e1 / 0.20e2 * t91 * t118 * t249 * (-0.8e1 / 0.3e1 * t119 * t226 - 0.16e2 / 0.3e1 * t121 * t231 - 0.8e1 * t123 * t235 - 0.32e2 / 0.3e1 * t125 * t240))
  vrho_1_ = t82 + t132 + t7 * (t215 + t264)
  t297 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t29 * t31 * (0.2e1 * t41 * s0 * t47 + 0.3e1 * t49 * t42 * t53 + 0.4e1 * t55 * t50 * t60 + t33 * t39) * t78 - 0.3e1 / 0.20e2 * t29 * t63 * t174 * (0.2e1 * t68 * s0 * t47 + 0.3e1 * t71 * t42 * t53 + 0.4e1 * t74 * t50 * t60 + t65 * t39))
  vsigma_0_ = t7 * t297
  vsigma_1_ = 0.0e0
  t328 = f.my_piecewise3(t83, 0, 0.3e1 / 0.20e2 * t91 * t31 * (0.2e1 * t41 * s2 * t104 + 0.4e1 * t55 * t106 * t115 + 0.3e1 * t49 * t99 * t109 + t33 * t97) * t128 - 0.3e1 / 0.20e2 * t91 * t118 * t249 * (0.2e1 * t68 * s2 * t104 + 0.4e1 * t74 * t106 * t115 + 0.3e1 * t71 * t99 * t109 + t65 * t97))
  vsigma_2_ = t7 * t328
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

  dk_f = lambda x: jnp.sum(jnp.array([params_aa[i] * x ** (2 * (i - 1)) for i in range(1, 5 + 1)]), axis=0) / jnp.sum(jnp.array([params_bb[i] * x ** (2 * (i - 1)) for i in range(1, 5 + 1)]), axis=0)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, dk_f, rs, zeta, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = t4 * t5 * jnp.pi * t20
  t22 = r0 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t25 = params.aa[1]
  t26 = t25 * s0
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = r0 ** 2
  t31 = 0.1e1 / t23 / t29
  t32 = t28 * t31
  t34 = params.aa[2]
  t35 = s0 ** 2
  t36 = t34 * t35
  t37 = t29 ** 2
  t41 = t27 / t22 / t37 / r0
  t44 = params.aa[3]
  t45 = t35 * s0
  t46 = t44 * t45
  t47 = t37 ** 2
  t48 = 0.1e1 / t47
  t51 = params.aa[4]
  t52 = t35 ** 2
  t53 = t51 * t52
  t57 = t28 / t23 / t47 / t29
  t60 = t26 * t32 + 0.2e1 * t36 * t41 + 0.4e1 * t46 * t48 + 0.4e1 * t53 * t57 + params.aa[0]
  t61 = t23 * t60
  t63 = params.bb[1]
  t64 = t63 * s0
  t66 = params.bb[2]
  t67 = t66 * t35
  t70 = params.bb[3]
  t71 = t70 * t45
  t74 = params.bb[4]
  t75 = t74 * t52
  t78 = t64 * t32 + 0.2e1 * t67 * t41 + 0.4e1 * t71 * t48 + 0.4e1 * t75 * t57 + params.bb[0]
  t79 = 0.1e1 / t78
  t83 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t21 * t61 * t79)
  t89 = t29 * r0
  t92 = t28 / t23 / t89
  t98 = t27 / t22 / t37 / t29
  t102 = 0.1e1 / t47 / r0
  t108 = t28 / t23 / t47 / t89
  t116 = t78 ** 2
  t117 = 0.1e1 / t116
  t132 = f.my_piecewise3(t2, 0, t21 / t22 * t60 * t79 / 0.10e2 + 0.3e1 / 0.20e2 * t21 * t23 * (-0.8e1 / 0.3e1 * t26 * t92 - 0.32e2 / 0.3e1 * t36 * t98 - 0.32e2 * t46 * t102 - 0.128e3 / 0.3e1 * t53 * t108) * t79 - 0.3e1 / 0.20e2 * t21 * t61 * t117 * (-0.8e1 / 0.3e1 * t64 * t92 - 0.32e2 / 0.3e1 * t67 * t98 - 0.32e2 * t71 * t102 - 0.128e3 / 0.3e1 * t75 * t108))
  vrho_0_ = 0.2e1 * r0 * t132 + 0.2e1 * t83
  t167 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t21 * t23 * (0.4e1 * t34 * s0 * t41 + t25 * t28 * t31 + 0.12e2 * t44 * t35 * t48 + 0.16e2 * t51 * t45 * t57) * t79 - 0.3e1 / 0.20e2 * t21 * t61 * t117 * (0.4e1 * t66 * s0 * t41 + t63 * t28 * t31 + 0.12e2 * t70 * t35 * t48 + 0.16e2 * t74 * t45 * t57))
  vsigma_0_ = 0.2e1 * r0 * t167
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
  t21 = t7 * t20
  t22 = r0 ** (0.1e1 / 0.3e1)
  t23 = 0.1e1 / t22
  t25 = params.aa[1]
  t26 = t25 * s0
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = r0 ** 2
  t30 = t22 ** 2
  t32 = 0.1e1 / t30 / t29
  t33 = t28 * t32
  t35 = params.aa[2]
  t36 = s0 ** 2
  t37 = t35 * t36
  t38 = t29 ** 2
  t41 = 0.1e1 / t22 / t38 / r0
  t42 = t27 * t41
  t45 = params.aa[3]
  t46 = t36 * s0
  t47 = t45 * t46
  t48 = t38 ** 2
  t49 = 0.1e1 / t48
  t52 = params.aa[4]
  t53 = t36 ** 2
  t54 = t52 * t53
  t55 = t48 * t29
  t58 = t28 / t30 / t55
  t61 = t26 * t33 + 0.2e1 * t37 * t42 + 0.4e1 * t47 * t49 + 0.4e1 * t54 * t58 + params.aa[0]
  t62 = t23 * t61
  t64 = params.bb[1]
  t65 = t64 * s0
  t67 = params.bb[2]
  t68 = t67 * t36
  t71 = params.bb[3]
  t72 = t71 * t46
  t75 = params.bb[4]
  t76 = t75 * t53
  t79 = t65 * t33 + 0.2e1 * t68 * t42 + 0.4e1 * t72 * t49 + 0.4e1 * t76 * t58 + params.bb[0]
  t80 = 0.1e1 / t79
  t84 = t29 * r0
  t86 = 0.1e1 / t30 / t84
  t87 = t28 * t86
  t93 = t27 / t22 / t38 / t29
  t97 = 0.1e1 / t48 / r0
  t103 = t28 / t30 / t48 / t84
  t106 = -0.8e1 / 0.3e1 * t26 * t87 - 0.32e2 / 0.3e1 * t37 * t93 - 0.32e2 * t47 * t97 - 0.128e3 / 0.3e1 * t54 * t103
  t107 = t30 * t106
  t111 = t30 * t61
  t112 = t79 ** 2
  t113 = 0.1e1 / t112
  t122 = -0.8e1 / 0.3e1 * t65 * t87 - 0.32e2 / 0.3e1 * t68 * t93 - 0.32e2 * t72 * t97 - 0.128e3 / 0.3e1 * t76 * t103
  t123 = t113 * t122
  t128 = f.my_piecewise3(t2, 0, t21 * t62 * t80 / 0.10e2 + 0.3e1 / 0.20e2 * t21 * t107 * t80 - 0.3e1 / 0.20e2 * t21 * t111 * t123)
  t145 = t28 / t30 / t38
  t151 = t27 / t22 / t38 / t84
  t154 = 0.1e1 / t55
  t160 = t28 / t30 / t48 / t38
  t172 = 0.1e1 / t112 / t79
  t173 = t122 ** 2
  t192 = f.my_piecewise3(t2, 0, -t21 / t22 / r0 * t61 * t80 / 0.30e2 + t21 * t23 * t106 * t80 / 0.5e1 - t21 * t62 * t123 / 0.5e1 + 0.3e1 / 0.20e2 * t21 * t30 * (0.88e2 / 0.9e1 * t26 * t145 + 0.608e3 / 0.9e1 * t37 * t151 + 0.288e3 * t47 * t154 + 0.4480e4 / 0.9e1 * t54 * t160) * t80 - 0.3e1 / 0.10e2 * t21 * t107 * t123 + 0.3e1 / 0.10e2 * t21 * t111 * t172 * t173 - 0.3e1 / 0.20e2 * t21 * t111 * t113 * (0.88e2 / 0.9e1 * t65 * t145 + 0.608e3 / 0.9e1 * t68 * t151 + 0.288e3 * t72 * t154 + 0.4480e4 / 0.9e1 * t76 * t160))
  v2rho2_0_ = 0.2e1 * r0 * t192 + 0.4e1 * t128
  t195 = t25 * t28
  t197 = t35 * s0
  t200 = t45 * t36
  t203 = t52 * t46
  t206 = t195 * t32 + 0.4e1 * t197 * t42 + 0.12e2 * t200 * t49 + 0.16e2 * t203 * t58
  t207 = t30 * t206
  t210 = t64 * t28
  t212 = t67 * s0
  t215 = t71 * t36
  t218 = t75 * t46
  t221 = t210 * t32 + 0.4e1 * t212 * t42 + 0.12e2 * t215 * t49 + 0.16e2 * t218 * t58
  t222 = t113 * t221
  t227 = f.my_piecewise3(t2, 0, -0.3e1 / 0.20e2 * t21 * t111 * t222 + 0.3e1 / 0.20e2 * t21 * t207 * t80)
  t275 = f.my_piecewise3(t2, 0, t21 * t23 * t206 * t80 / 0.10e2 + 0.3e1 / 0.20e2 * t21 * t30 * (-0.8e1 / 0.3e1 * t195 * t86 - 0.64e2 / 0.3e1 * t197 * t93 - 0.96e2 * t200 * t97 - 0.512e3 / 0.3e1 * t203 * t103) * t80 - 0.3e1 / 0.20e2 * t21 * t207 * t123 - t21 * t62 * t222 / 0.10e2 - 0.3e1 / 0.20e2 * t21 * t107 * t222 + 0.3e1 / 0.10e2 * t7 * t20 * t30 * t61 * t172 * t221 * t122 - 0.3e1 / 0.20e2 * t21 * t111 * t113 * (-0.8e1 / 0.3e1 * t210 * t86 - 0.64e2 / 0.3e1 * t212 * t93 - 0.96e2 * t215 * t97 - 0.512e3 / 0.3e1 * t218 * t103))
  v2rhosigma_0_ = 0.2e1 * r0 * t275 + 0.2e1 * t227
  t295 = t221 ** 2
  t315 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t21 * t30 * (0.24e2 * t45 * s0 * t49 + 0.4e1 * t35 * t27 * t41 + 0.48e2 * t52 * t36 * t58) * t80 - 0.3e1 / 0.10e2 * t21 * t207 * t222 + 0.3e1 / 0.10e2 * t21 * t111 * t172 * t295 - 0.3e1 / 0.20e2 * t21 * t111 * t113 * (0.24e2 * t71 * s0 * t49 + 0.4e1 * t67 * t27 * t41 + 0.48e2 * t75 * t36 * t58))
  v2sigma2_0_ = 0.2e1 * r0 * t315
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
  t21 = t7 * t20
  t22 = r0 ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t22 / r0
  t27 = params.aa[1] * s0
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = r0 ** 2
  t31 = t22 ** 2
  t34 = t29 / t31 / t30
  t37 = s0 ** 2
  t38 = params.aa[2] * t37
  t39 = t30 ** 2
  t40 = t39 * r0
  t43 = t28 / t22 / t40
  t47 = t37 * s0
  t48 = params.aa[3] * t47
  t49 = t39 ** 2
  t50 = 0.1e1 / t49
  t54 = t37 ** 2
  t55 = params.aa[4] * t54
  t56 = t49 * t30
  t59 = t29 / t31 / t56
  t62 = t27 * t34 + 0.2e1 * t38 * t43 + 0.4e1 * t48 * t50 + 0.4e1 * t55 * t59 + params.aa[0]
  t63 = t24 * t62
  t66 = params.bb[1] * s0
  t69 = params.bb[2] * t37
  t73 = params.bb[3] * t47
  t77 = params.bb[4] * t54
  t80 = t66 * t34 + 0.2e1 * t69 * t43 + 0.4e1 * t73 * t50 + 0.4e1 * t77 * t59 + params.bb[0]
  t81 = 0.1e1 / t80
  t85 = 0.1e1 / t22
  t86 = t30 * r0
  t89 = t29 / t31 / t86
  t95 = t28 / t22 / t39 / t30
  t99 = 0.1e1 / t49 / r0
  t102 = t49 * t86
  t105 = t29 / t31 / t102
  t108 = -0.8e1 / 0.3e1 * t27 * t89 - 0.32e2 / 0.3e1 * t38 * t95 - 0.32e2 * t48 * t99 - 0.128e3 / 0.3e1 * t55 * t105
  t109 = t85 * t108
  t113 = t85 * t62
  t114 = t80 ** 2
  t115 = 0.1e1 / t114
  t124 = -0.8e1 / 0.3e1 * t66 * t89 - 0.32e2 / 0.3e1 * t69 * t95 - 0.32e2 * t73 * t99 - 0.128e3 / 0.3e1 * t77 * t105
  t125 = t115 * t124
  t131 = t29 / t31 / t39
  t137 = t28 / t22 / t39 / t86
  t140 = 0.1e1 / t56
  t146 = t29 / t31 / t49 / t39
  t149 = 0.88e2 / 0.9e1 * t27 * t131 + 0.608e3 / 0.9e1 * t38 * t137 + 0.288e3 * t48 * t140 + 0.4480e4 / 0.9e1 * t55 * t146
  t150 = t31 * t149
  t154 = t31 * t108
  t158 = t31 * t62
  t160 = 0.1e1 / t114 / t80
  t161 = t124 ** 2
  t162 = t160 * t161
  t174 = 0.88e2 / 0.9e1 * t66 * t131 + 0.608e3 / 0.9e1 * t69 * t137 + 0.288e3 * t73 * t140 + 0.4480e4 / 0.9e1 * t77 * t146
  t175 = t115 * t174
  t180 = f.my_piecewise3(t2, 0, -t21 * t63 * t81 / 0.30e2 + t21 * t109 * t81 / 0.5e1 - t21 * t113 * t125 / 0.5e1 + 0.3e1 / 0.20e2 * t21 * t150 * t81 - 0.3e1 / 0.10e2 * t21 * t154 * t125 + 0.3e1 / 0.10e2 * t21 * t158 * t162 - 0.3e1 / 0.20e2 * t21 * t158 * t175)
  t205 = t29 / t31 / t40
  t210 = t28 / t22 / t49
  t213 = 0.1e1 / t102
  t219 = t29 / t31 / t49 / t40
  t233 = t114 ** 2
  t268 = 0.2e1 / 0.45e2 * t21 / t22 / t30 * t62 * t81 + t21 * t63 * t125 / 0.10e2 - 0.3e1 / 0.5e1 * t21 * t109 * t125 - 0.3e1 / 0.10e2 * t21 * t113 * t175 - 0.9e1 / 0.20e2 * t21 * t150 * t125 - 0.9e1 / 0.20e2 * t21 * t154 * t175 - 0.3e1 / 0.20e2 * t21 * t158 * t115 * (-0.1232e4 / 0.27e2 * t66 * t205 - 0.13376e5 / 0.27e2 * t69 * t210 - 0.2880e4 * t73 * t213 - 0.170240e6 / 0.27e2 * t77 * t219) + 0.3e1 / 0.5e1 * t21 * t113 * t162 + 0.9e1 / 0.10e2 * t21 * t154 * t162 - 0.9e1 / 0.10e2 * t21 * t158 / t233 * t161 * t124 + 0.9e1 / 0.10e2 * t7 * t20 * t31 * t62 * t160 * t124 * t174 - t21 * t24 * t108 * t81 / 0.10e2 + 0.3e1 / 0.10e2 * t21 * t85 * t149 * t81 + 0.3e1 / 0.20e2 * t21 * t31 * (-0.1232e4 / 0.27e2 * t27 * t205 - 0.13376e5 / 0.27e2 * t38 * t210 - 0.2880e4 * t48 * t213 - 0.170240e6 / 0.27e2 * t55 * t219) * t81
  t269 = f.my_piecewise3(t2, 0, t268)
  v3rho3_0_ = 0.2e1 * r0 * t269 + 0.6e1 * t180

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
  t21 = t7 * t20
  t22 = r0 ** 2
  t23 = r0 ** (0.1e1 / 0.3e1)
  t25 = 0.1e1 / t23 / t22
  t28 = params.aa[1] * s0
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = t23 ** 2
  t34 = t30 / t31 / t22
  t37 = s0 ** 2
  t38 = params.aa[2] * t37
  t39 = t22 ** 2
  t40 = t39 * r0
  t43 = t29 / t23 / t40
  t47 = t37 * s0
  t48 = params.aa[3] * t47
  t49 = t39 ** 2
  t50 = 0.1e1 / t49
  t54 = t37 ** 2
  t55 = params.aa[4] * t54
  t56 = t49 * t22
  t59 = t30 / t31 / t56
  t62 = t28 * t34 + 0.2e1 * t38 * t43 + 0.4e1 * t48 * t50 + 0.4e1 * t55 * t59 + params.aa[0]
  t63 = t25 * t62
  t66 = params.bb[1] * s0
  t69 = params.bb[2] * t37
  t73 = params.bb[3] * t47
  t77 = params.bb[4] * t54
  t80 = t66 * t34 + 0.2e1 * t69 * t43 + 0.4e1 * t73 * t50 + 0.4e1 * t77 * t59 + params.bb[0]
  t81 = 0.1e1 / t80
  t86 = 0.1e1 / t23 / r0
  t87 = t86 * t62
  t88 = t80 ** 2
  t89 = 0.1e1 / t88
  t90 = t22 * r0
  t93 = t30 / t31 / t90
  t96 = t39 * t22
  t99 = t29 / t23 / t96
  t102 = t49 * r0
  t103 = 0.1e1 / t102
  t106 = t49 * t90
  t109 = t30 / t31 / t106
  t112 = -0.8e1 / 0.3e1 * t66 * t93 - 0.32e2 / 0.3e1 * t69 * t99 - 0.32e2 * t73 * t103 - 0.128e3 / 0.3e1 * t77 * t109
  t113 = t89 * t112
  t117 = 0.1e1 / t23
  t126 = -0.8e1 / 0.3e1 * t28 * t93 - 0.32e2 / 0.3e1 * t38 * t99 - 0.32e2 * t48 * t103 - 0.128e3 / 0.3e1 * t55 * t109
  t127 = t117 * t126
  t131 = t117 * t62
  t134 = t30 / t31 / t39
  t140 = t29 / t23 / t39 / t90
  t143 = 0.1e1 / t56
  t146 = t49 * t39
  t149 = t30 / t31 / t146
  t152 = 0.88e2 / 0.9e1 * t66 * t134 + 0.608e3 / 0.9e1 * t69 * t140 + 0.288e3 * t73 * t143 + 0.4480e4 / 0.9e1 * t77 * t149
  t153 = t89 * t152
  t165 = 0.88e2 / 0.9e1 * t28 * t134 + 0.608e3 / 0.9e1 * t38 * t140 + 0.288e3 * t48 * t143 + 0.4480e4 / 0.9e1 * t55 * t149
  t166 = t31 * t165
  t170 = t31 * t126
  t174 = t31 * t62
  t177 = t30 / t31 / t40
  t182 = t29 / t23 / t49
  t185 = 0.1e1 / t106
  t191 = t30 / t31 / t49 / t40
  t194 = -0.1232e4 / 0.27e2 * t66 * t177 - 0.13376e5 / 0.27e2 * t69 * t182 - 0.2880e4 * t73 * t185 - 0.170240e6 / 0.27e2 * t77 * t191
  t195 = t89 * t194
  t199 = t88 ** 2
  t200 = 0.1e1 / t199
  t201 = t112 ** 2
  t203 = t200 * t201 * t112
  t208 = t7 * t20 * t31
  t210 = 0.1e1 / t88 / t80
  t211 = t62 * t210
  t212 = t112 * t152
  t213 = t211 * t212
  t216 = t210 * t201
  t223 = t86 * t126
  t227 = t117 * t165
  t239 = -0.1232e4 / 0.27e2 * t28 * t177 - 0.13376e5 / 0.27e2 * t38 * t182 - 0.2880e4 * t48 * t185 - 0.170240e6 / 0.27e2 * t55 * t191
  t240 = t31 * t239
  t244 = 0.2e1 / 0.45e2 * t21 * t63 * t81 + t21 * t87 * t113 / 0.10e2 - 0.3e1 / 0.5e1 * t21 * t127 * t113 - 0.3e1 / 0.10e2 * t21 * t131 * t153 - 0.9e1 / 0.20e2 * t21 * t166 * t113 - 0.9e1 / 0.20e2 * t21 * t170 * t153 - 0.3e1 / 0.20e2 * t21 * t174 * t195 - 0.9e1 / 0.10e2 * t21 * t174 * t203 + 0.9e1 / 0.10e2 * t208 * t213 + 0.3e1 / 0.5e1 * t21 * t131 * t216 + 0.9e1 / 0.10e2 * t21 * t170 * t216 - t21 * t223 * t81 / 0.10e2 + 0.3e1 / 0.10e2 * t21 * t227 * t81 + 0.3e1 / 0.20e2 * t21 * t240 * t81
  t245 = f.my_piecewise3(t2, 0, t244)
  t284 = t30 / t31 / t96
  t289 = t29 / t23 / t102
  t292 = 0.1e1 / t146
  t298 = t30 / t31 / t49 / t96
  t312 = -0.27e2 / 0.5e1 * t208 * t62 * t200 * t201 * t152 + 0.12e2 / 0.5e1 * t7 * t20 * t117 * t213 + 0.18e2 / 0.5e1 * t208 * t126 * t210 * t212 + 0.6e1 / 0.5e1 * t208 * t211 * t194 * t112 - 0.6e1 / 0.5e1 * t21 * t227 * t113 - 0.6e1 / 0.5e1 * t21 * t127 * t153 - 0.2e1 / 0.5e1 * t21 * t131 * t195 - 0.3e1 / 0.5e1 * t21 * t240 * t113 - 0.9e1 / 0.10e2 * t21 * t166 * t153 - 0.3e1 / 0.5e1 * t21 * t170 * t195 - 0.3e1 / 0.20e2 * t21 * t174 * t89 * (0.20944e5 / 0.81e2 * t66 * t284 + 0.334400e6 / 0.81e2 * t69 * t289 + 0.31680e5 * t73 * t292 + 0.6979840e7 / 0.81e2 * t77 * t298) - 0.18e2 / 0.5e1 * t21 * t170 * t203 - 0.12e2 / 0.5e1 * t21 * t131 * t203
  t315 = t201 ** 2
  t320 = t152 ** 2
  t374 = 0.18e2 / 0.5e1 * t21 * t174 / t199 / t80 * t315 + 0.9e1 / 0.10e2 * t21 * t174 * t210 * t320 - 0.2e1 / 0.5e1 * t21 * t87 * t216 + 0.12e2 / 0.5e1 * t21 * t127 * t216 + 0.9e1 / 0.5e1 * t21 * t166 * t216 - 0.8e1 / 0.45e2 * t21 * t63 * t113 + 0.2e1 / 0.5e1 * t21 * t223 * t113 + t21 * t87 * t153 / 0.5e1 - 0.14e2 / 0.135e3 * t21 / t23 / t90 * t62 * t81 + 0.8e1 / 0.45e2 * t21 * t25 * t126 * t81 - t21 * t86 * t165 * t81 / 0.5e1 + 0.2e1 / 0.5e1 * t21 * t117 * t239 * t81 + 0.3e1 / 0.20e2 * t21 * t31 * (0.20944e5 / 0.81e2 * t28 * t284 + 0.334400e6 / 0.81e2 * t38 * t289 + 0.31680e5 * t48 * t292 + 0.6979840e7 / 0.81e2 * t55 * t298) * t81
  t376 = f.my_piecewise3(t2, 0, t312 + t374)
  v4rho4_0_ = 0.2e1 * r0 * t376 + 0.8e1 * t245

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
  t32 = t6 * t31
  t33 = t7 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = params.aa[0]
  t36 = params.aa[1]
  t37 = t36 * s0
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t44 = params.aa[2]
  t45 = s0 ** 2
  t46 = t44 * t45
  t47 = t38 ** 2
  t50 = 0.1e1 / t39 / t47 / r0
  t52 = params.aa[3]
  t53 = t45 * s0
  t54 = t52 * t53
  t55 = t47 ** 2
  t56 = 0.1e1 / t55
  t58 = params.aa[4]
  t59 = t45 ** 2
  t60 = t58 * t59
  t61 = t55 * t38
  t63 = 0.1e1 / t40 / t61
  t65 = t37 * t42 + t46 * t50 + t54 * t56 + t60 * t63 + t35
  t66 = t34 * t65
  t67 = params.bb[0]
  t68 = params.bb[1]
  t69 = t68 * s0
  t71 = params.bb[2]
  t72 = t71 * t45
  t74 = params.bb[3]
  t75 = t74 * t53
  t77 = params.bb[4]
  t78 = t77 * t59
  t80 = t69 * t42 + t72 * t50 + t75 * t56 + t78 * t63 + t67
  t81 = 0.1e1 / t80
  t82 = t66 * t81
  t85 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t86 = t85 ** 2
  t87 = t86 * f.p.zeta_threshold
  t89 = f.my_piecewise3(t21, t87, t23 * t20)
  t90 = t6 * t89
  t91 = 0.1e1 / t33
  t92 = t91 * t65
  t93 = t92 * t81
  t95 = t90 * t93 / 0.10e2
  t96 = t38 * r0
  t98 = 0.1e1 / t40 / t96
  t103 = 0.1e1 / t39 / t47 / t38
  t107 = 0.1e1 / t55 / r0
  t112 = 0.1e1 / t40 / t55 / t96
  t115 = -0.8e1 / 0.3e1 * t37 * t98 - 0.16e2 / 0.3e1 * t46 * t103 - 0.8e1 * t54 * t107 - 0.32e2 / 0.3e1 * t60 * t112
  t116 = t34 * t115
  t117 = t116 * t81
  t120 = t80 ** 2
  t121 = 0.1e1 / t120
  t130 = -0.8e1 / 0.3e1 * t69 * t98 - 0.16e2 / 0.3e1 * t72 * t103 - 0.8e1 * t75 * t107 - 0.32e2 / 0.3e1 * t78 * t112
  t131 = t121 * t130
  t132 = t66 * t131
  t136 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t32 * t82 + t95 + 0.3e1 / 0.20e2 * t90 * t117 - 0.3e1 / 0.20e2 * t90 * t132)
  t138 = r1 <= f.p.dens_threshold
  t139 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t140 = 0.1e1 + t139
  t141 = t140 <= f.p.zeta_threshold
  t142 = t140 ** (0.1e1 / 0.3e1)
  t143 = t142 ** 2
  t145 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t148 = f.my_piecewise3(t141, 0, 0.5e1 / 0.3e1 * t143 * t145)
  t149 = t6 * t148
  t150 = t36 * s2
  t151 = r1 ** 2
  t152 = r1 ** (0.1e1 / 0.3e1)
  t153 = t152 ** 2
  t155 = 0.1e1 / t153 / t151
  t157 = s2 ** 2
  t158 = t44 * t157
  t159 = t151 ** 2
  t162 = 0.1e1 / t152 / t159 / r1
  t164 = t157 * s2
  t165 = t52 * t164
  t166 = t159 ** 2
  t167 = 0.1e1 / t166
  t169 = t157 ** 2
  t170 = t58 * t169
  t171 = t166 * t151
  t173 = 0.1e1 / t153 / t171
  t175 = t150 * t155 + t158 * t162 + t165 * t167 + t170 * t173 + t35
  t176 = t34 * t175
  t177 = t68 * s2
  t179 = t71 * t157
  t181 = t74 * t164
  t183 = t77 * t169
  t185 = t177 * t155 + t179 * t162 + t181 * t167 + t183 * t173 + t67
  t186 = 0.1e1 / t185
  t187 = t176 * t186
  t191 = f.my_piecewise3(t141, t87, t143 * t140)
  t192 = t6 * t191
  t193 = t91 * t175
  t194 = t193 * t186
  t196 = t192 * t194 / 0.10e2
  t198 = f.my_piecewise3(t138, 0, 0.3e1 / 0.20e2 * t149 * t187 + t196)
  t200 = 0.1e1 / t22
  t201 = t28 ** 2
  t206 = t17 / t24 / t7
  t208 = -0.2e1 * t25 + 0.2e1 * t206
  t209 = f.my_piecewise5(t11, 0, t15, 0, t208)
  t213 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t200 * t201 + 0.5e1 / 0.3e1 * t23 * t209)
  t217 = t32 * t93
  t224 = 0.1e1 / t33 / t7
  t228 = t90 * t224 * t65 * t81 / 0.30e2
  t231 = t90 * t91 * t115 * t81
  t234 = t90 * t92 * t131
  t237 = 0.1e1 / t40 / t47
  t242 = 0.1e1 / t39 / t47 / t96
  t245 = 0.1e1 / t61
  t250 = 0.1e1 / t40 / t55 / t47
  t263 = t130 ** 2
  t281 = 0.3e1 / 0.20e2 * t6 * t213 * t82 + t217 / 0.5e1 + 0.3e1 / 0.10e2 * t32 * t117 - 0.3e1 / 0.10e2 * t32 * t132 - t228 + t231 / 0.5e1 - t234 / 0.5e1 + 0.3e1 / 0.20e2 * t90 * t34 * (0.88e2 / 0.9e1 * t37 * t237 + 0.304e3 / 0.9e1 * t46 * t242 + 0.72e2 * t54 * t245 + 0.1120e4 / 0.9e1 * t60 * t250) * t81 - 0.3e1 / 0.10e2 * t90 * t116 * t131 + 0.3e1 / 0.10e2 * t90 * t66 / t120 / t80 * t263 - 0.3e1 / 0.20e2 * t90 * t66 * t121 * (0.88e2 / 0.9e1 * t69 * t237 + 0.304e3 / 0.9e1 * t72 * t242 + 0.72e2 * t75 * t245 + 0.1120e4 / 0.9e1 * t78 * t250)
  t282 = f.my_piecewise3(t1, 0, t281)
  t283 = 0.1e1 / t142
  t284 = t145 ** 2
  t288 = f.my_piecewise5(t15, 0, t11, 0, -t208)
  t292 = f.my_piecewise3(t141, 0, 0.10e2 / 0.9e1 * t283 * t284 + 0.5e1 / 0.3e1 * t143 * t288)
  t296 = t149 * t194
  t301 = t192 * t224 * t175 * t186 / 0.30e2
  t303 = f.my_piecewise3(t138, 0, 0.3e1 / 0.20e2 * t6 * t292 * t187 + t296 / 0.5e1 - t301)
  d11 = 0.2e1 * t136 + 0.2e1 * t198 + t7 * (t282 + t303)
  t306 = -t8 - t26
  t307 = f.my_piecewise5(t11, 0, t15, 0, t306)
  t310 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t307)
  t311 = t6 * t310
  t315 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t311 * t82 + t95)
  t317 = f.my_piecewise5(t15, 0, t11, 0, -t306)
  t320 = f.my_piecewise3(t141, 0, 0.5e1 / 0.3e1 * t143 * t317)
  t321 = t6 * t320
  t324 = t151 * r1
  t326 = 0.1e1 / t153 / t324
  t331 = 0.1e1 / t152 / t159 / t151
  t335 = 0.1e1 / t166 / r1
  t340 = 0.1e1 / t153 / t166 / t324
  t343 = -0.8e1 / 0.3e1 * t150 * t326 - 0.16e2 / 0.3e1 * t158 * t331 - 0.8e1 * t165 * t335 - 0.32e2 / 0.3e1 * t170 * t340
  t344 = t34 * t343
  t345 = t344 * t186
  t348 = t185 ** 2
  t349 = 0.1e1 / t348
  t358 = -0.8e1 / 0.3e1 * t177 * t326 - 0.16e2 / 0.3e1 * t179 * t331 - 0.8e1 * t181 * t335 - 0.32e2 / 0.3e1 * t183 * t340
  t359 = t349 * t358
  t360 = t176 * t359
  t364 = f.my_piecewise3(t138, 0, 0.3e1 / 0.20e2 * t321 * t187 + t196 + 0.3e1 / 0.20e2 * t192 * t345 - 0.3e1 / 0.20e2 * t192 * t360)
  t368 = 0.2e1 * t206
  t369 = f.my_piecewise5(t11, 0, t15, 0, t368)
  t373 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t200 * t307 * t28 + 0.5e1 / 0.3e1 * t23 * t369)
  t377 = t311 * t93
  t387 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t373 * t82 + t377 / 0.10e2 + 0.3e1 / 0.20e2 * t311 * t117 - 0.3e1 / 0.20e2 * t311 * t132 + t217 / 0.10e2 - t228 + t231 / 0.10e2 - t234 / 0.10e2)
  t391 = f.my_piecewise5(t15, 0, t11, 0, -t368)
  t395 = f.my_piecewise3(t141, 0, 0.10e2 / 0.9e1 * t283 * t317 * t145 + 0.5e1 / 0.3e1 * t143 * t391)
  t399 = t321 * t194
  t406 = t192 * t91 * t343 * t186
  t411 = t192 * t193 * t359
  t414 = f.my_piecewise3(t138, 0, 0.3e1 / 0.20e2 * t6 * t395 * t187 + t399 / 0.10e2 + t296 / 0.10e2 - t301 + 0.3e1 / 0.20e2 * t149 * t345 + t406 / 0.10e2 - 0.3e1 / 0.20e2 * t149 * t360 - t411 / 0.10e2)
  d12 = t136 + t198 + t315 + t364 + t7 * (t387 + t414)
  t419 = t307 ** 2
  t423 = 0.2e1 * t25 + 0.2e1 * t206
  t424 = f.my_piecewise5(t11, 0, t15, 0, t423)
  t428 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t200 * t419 + 0.5e1 / 0.3e1 * t23 * t424)
  t434 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t428 * t82 + t377 / 0.5e1 - t228)
  t435 = t317 ** 2
  t439 = f.my_piecewise5(t15, 0, t11, 0, -t423)
  t443 = f.my_piecewise3(t141, 0, 0.10e2 / 0.9e1 * t283 * t435 + 0.5e1 / 0.3e1 * t143 * t439)
  t455 = 0.1e1 / t153 / t159
  t460 = 0.1e1 / t152 / t159 / t324
  t463 = 0.1e1 / t171
  t468 = 0.1e1 / t153 / t166 / t159
  t481 = t358 ** 2
  t499 = 0.3e1 / 0.20e2 * t6 * t443 * t187 + t399 / 0.5e1 + 0.3e1 / 0.10e2 * t321 * t345 - 0.3e1 / 0.10e2 * t321 * t360 - t301 + t406 / 0.5e1 - t411 / 0.5e1 + 0.3e1 / 0.20e2 * t192 * t34 * (0.88e2 / 0.9e1 * t150 * t455 + 0.304e3 / 0.9e1 * t158 * t460 + 0.72e2 * t165 * t463 + 0.1120e4 / 0.9e1 * t170 * t468) * t186 - 0.3e1 / 0.10e2 * t192 * t344 * t359 + 0.3e1 / 0.10e2 * t192 * t176 / t348 / t185 * t481 - 0.3e1 / 0.20e2 * t192 * t176 * t349 * (0.88e2 / 0.9e1 * t177 * t455 + 0.304e3 / 0.9e1 * t179 * t460 + 0.72e2 * t181 * t463 + 0.1120e4 / 0.9e1 * t183 * t468)
  t500 = f.my_piecewise3(t138, 0, t499)
  d22 = 0.2e1 * t315 + 0.2e1 * t364 + t7 * (t434 + t500)
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
  t43 = t6 * t42
  t44 = t7 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = params.aa[0]
  t47 = params.aa[1]
  t48 = t47 * s0
  t49 = r0 ** 2
  t50 = r0 ** (0.1e1 / 0.3e1)
  t51 = t50 ** 2
  t53 = 0.1e1 / t51 / t49
  t55 = params.aa[2]
  t56 = s0 ** 2
  t57 = t55 * t56
  t58 = t49 ** 2
  t59 = t58 * r0
  t61 = 0.1e1 / t50 / t59
  t63 = params.aa[3]
  t64 = t56 * s0
  t65 = t63 * t64
  t66 = t58 ** 2
  t67 = 0.1e1 / t66
  t69 = params.aa[4]
  t70 = t56 ** 2
  t71 = t69 * t70
  t72 = t66 * t49
  t74 = 0.1e1 / t51 / t72
  t76 = t48 * t53 + t57 * t61 + t65 * t67 + t71 * t74 + t46
  t77 = t45 * t76
  t78 = params.bb[0]
  t79 = params.bb[1]
  t80 = t79 * s0
  t82 = params.bb[2]
  t83 = t82 * t56
  t85 = params.bb[3]
  t86 = t85 * t64
  t88 = params.bb[4]
  t89 = t88 * t70
  t91 = t80 * t53 + t83 * t61 + t86 * t67 + t89 * t74 + t78
  t92 = 0.1e1 / t91
  t93 = t77 * t92
  t98 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t99 = t6 * t98
  t100 = 0.1e1 / t44
  t101 = t100 * t76
  t102 = t101 * t92
  t105 = t49 * r0
  t107 = 0.1e1 / t51 / t105
  t112 = 0.1e1 / t50 / t58 / t49
  t116 = 0.1e1 / t66 / r0
  t119 = t66 * t105
  t121 = 0.1e1 / t51 / t119
  t124 = -0.8e1 / 0.3e1 * t48 * t107 - 0.16e2 / 0.3e1 * t57 * t112 - 0.8e1 * t65 * t116 - 0.32e2 / 0.3e1 * t71 * t121
  t125 = t45 * t124
  t126 = t125 * t92
  t129 = t91 ** 2
  t130 = 0.1e1 / t129
  t139 = -0.8e1 / 0.3e1 * t80 * t107 - 0.16e2 / 0.3e1 * t83 * t112 - 0.8e1 * t86 * t116 - 0.32e2 / 0.3e1 * t89 * t121
  t140 = t130 * t139
  t141 = t77 * t140
  t144 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t145 = t144 ** 2
  t146 = t145 * f.p.zeta_threshold
  t148 = f.my_piecewise3(t21, t146, t32 * t20)
  t149 = t6 * t148
  t151 = 0.1e1 / t44 / t7
  t152 = t151 * t76
  t153 = t152 * t92
  t156 = t100 * t124
  t157 = t156 * t92
  t160 = t101 * t140
  t164 = 0.1e1 / t51 / t58
  t169 = 0.1e1 / t50 / t58 / t105
  t172 = 0.1e1 / t72
  t177 = 0.1e1 / t51 / t66 / t58
  t180 = 0.88e2 / 0.9e1 * t48 * t164 + 0.304e3 / 0.9e1 * t57 * t169 + 0.72e2 * t65 * t172 + 0.1120e4 / 0.9e1 * t71 * t177
  t181 = t45 * t180
  t182 = t181 * t92
  t185 = t125 * t140
  t189 = 0.1e1 / t129 / t91
  t190 = t139 ** 2
  t191 = t189 * t190
  t192 = t77 * t191
  t203 = 0.88e2 / 0.9e1 * t80 * t164 + 0.304e3 / 0.9e1 * t83 * t169 + 0.72e2 * t86 * t172 + 0.1120e4 / 0.9e1 * t89 * t177
  t204 = t130 * t203
  t205 = t77 * t204
  t208 = 0.3e1 / 0.20e2 * t43 * t93 + t99 * t102 / 0.5e1 + 0.3e1 / 0.10e2 * t99 * t126 - 0.3e1 / 0.10e2 * t99 * t141 - t149 * t153 / 0.30e2 + t149 * t157 / 0.5e1 - t149 * t160 / 0.5e1 + 0.3e1 / 0.20e2 * t149 * t182 - 0.3e1 / 0.10e2 * t149 * t185 + 0.3e1 / 0.10e2 * t149 * t192 - 0.3e1 / 0.20e2 * t149 * t205
  t209 = f.my_piecewise3(t1, 0, t208)
  t211 = r1 <= f.p.dens_threshold
  t212 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t213 = 0.1e1 + t212
  t214 = t213 <= f.p.zeta_threshold
  t215 = t213 ** (0.1e1 / 0.3e1)
  t216 = 0.1e1 / t215
  t218 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t219 = t218 ** 2
  t222 = t215 ** 2
  t224 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t228 = f.my_piecewise3(t214, 0, 0.10e2 / 0.9e1 * t216 * t219 + 0.5e1 / 0.3e1 * t222 * t224)
  t229 = t6 * t228
  t231 = r1 ** 2
  t232 = r1 ** (0.1e1 / 0.3e1)
  t233 = t232 ** 2
  t235 = 0.1e1 / t233 / t231
  t237 = s2 ** 2
  t239 = t231 ** 2
  t242 = 0.1e1 / t232 / t239 / r1
  t244 = t237 * s2
  t246 = t239 ** 2
  t247 = 0.1e1 / t246
  t249 = t237 ** 2
  t253 = 0.1e1 / t233 / t246 / t231
  t255 = t47 * s2 * t235 + t55 * t237 * t242 + t63 * t244 * t247 + t69 * t249 * t253 + t46
  t266 = 0.1e1 / (t79 * s2 * t235 + t82 * t237 * t242 + t85 * t244 * t247 + t88 * t249 * t253 + t78)
  t267 = t45 * t255 * t266
  t272 = f.my_piecewise3(t214, 0, 0.5e1 / 0.3e1 * t222 * t218)
  t273 = t6 * t272
  t275 = t100 * t255 * t266
  t279 = f.my_piecewise3(t214, t146, t222 * t213)
  t280 = t6 * t279
  t282 = t151 * t255 * t266
  t286 = f.my_piecewise3(t211, 0, 0.3e1 / 0.20e2 * t229 * t267 + t273 * t275 / 0.5e1 - t280 * t282 / 0.30e2)
  t306 = t129 ** 2
  t327 = 0.9e1 / 0.10e2 * t6 * t148 * t45 * t76 * t189 * t139 * t203 - 0.9e1 / 0.20e2 * t43 * t141 - 0.3e1 / 0.5e1 * t99 * t160 - 0.9e1 / 0.10e2 * t99 * t185 - 0.9e1 / 0.20e2 * t99 * t205 + 0.9e1 / 0.10e2 * t149 * t125 * t191 - 0.9e1 / 0.10e2 * t149 * t77 / t306 * t190 * t139 + 0.9e1 / 0.10e2 * t99 * t192 + 0.3e1 / 0.5e1 * t149 * t101 * t191 + t149 * t152 * t140 / 0.10e2 - 0.3e1 / 0.5e1 * t149 * t156 * t140 - 0.3e1 / 0.10e2 * t149 * t101 * t204
  t335 = 0.1e1 / t51 / t59
  t339 = 0.1e1 / t50 / t66
  t342 = 0.1e1 / t119
  t347 = 0.1e1 / t51 / t66 / t59
  t356 = 0.1e1 / t44 / t24
  t373 = t24 ** 2
  t377 = 0.6e1 * t34 - 0.6e1 * t17 / t373
  t378 = f.my_piecewise5(t11, 0, t15, 0, t377)
  t382 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t378)
  t413 = -0.9e1 / 0.20e2 * t149 * t181 * t140 - 0.9e1 / 0.20e2 * t149 * t125 * t204 - 0.3e1 / 0.20e2 * t149 * t77 * t130 * (-0.1232e4 / 0.27e2 * t80 * t335 - 0.6688e4 / 0.27e2 * t83 * t339 - 0.720e3 * t86 * t342 - 0.42560e5 / 0.27e2 * t89 * t347) + 0.2e1 / 0.45e2 * t149 * t356 * t76 * t92 + 0.3e1 / 0.10e2 * t43 * t102 - t99 * t153 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t382 * t93 + 0.9e1 / 0.20e2 * t43 * t126 + 0.3e1 / 0.5e1 * t99 * t157 + 0.9e1 / 0.20e2 * t99 * t182 - t149 * t151 * t124 * t92 / 0.10e2 + 0.3e1 / 0.10e2 * t149 * t100 * t180 * t92 + 0.3e1 / 0.20e2 * t149 * t45 * (-0.1232e4 / 0.27e2 * t48 * t335 - 0.6688e4 / 0.27e2 * t57 * t339 - 0.720e3 * t65 * t342 - 0.42560e5 / 0.27e2 * t71 * t347) * t92
  t415 = f.my_piecewise3(t1, 0, t327 + t413)
  t425 = f.my_piecewise5(t15, 0, t11, 0, -t377)
  t429 = f.my_piecewise3(t214, 0, -0.10e2 / 0.27e2 / t215 / t213 * t219 * t218 + 0.10e2 / 0.3e1 * t216 * t218 * t224 + 0.5e1 / 0.3e1 * t222 * t425)
  t442 = f.my_piecewise3(t211, 0, 0.3e1 / 0.20e2 * t6 * t429 * t267 + 0.3e1 / 0.10e2 * t229 * t275 - t273 * t282 / 0.10e2 + 0.2e1 / 0.45e2 * t280 * t356 * t255 * t266)
  d111 = 0.3e1 * t209 + 0.3e1 * t286 + t7 * (t415 + t442)

  res = {'v3rho3': d111}
  return res
