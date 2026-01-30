"""Generated from gga_k_mpbe.mpl."""

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_c3_raw = params.c3
  if isinstance(params_c3_raw, (str, bytes, dict)):
    params_c3 = params_c3_raw
  else:
    try:
      params_c3_seq = list(params_c3_raw)
    except TypeError:
      params_c3 = params_c3_raw
    else:
      params_c3_seq = np.asarray(params_c3_seq, dtype=np.float64)
      params_c3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c3_seq))

  mpbe_f0 = lambda s: s ** 2 / (1 + params_a * s ** 2)

  mpbe_f = lambda x: 1 + params_c1 * mpbe_f0(X2S * x) + params_c2 * mpbe_f0(X2S * x) ** 2 + params_c3 * mpbe_f0(X2S * x) ** 3

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, mpbe_f, rs, z, xs0, xs1)

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_c3_raw = params.c3
  if isinstance(params_c3_raw, (str, bytes, dict)):
    params_c3 = params_c3_raw
  else:
    try:
      params_c3_seq = list(params_c3_raw)
    except TypeError:
      params_c3 = params_c3_raw
    else:
      params_c3_seq = np.asarray(params_c3_seq, dtype=np.float64)
      params_c3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c3_seq))

  mpbe_f0 = lambda s: s ** 2 / (1 + params_a * s ** 2)

  mpbe_f = lambda x: 1 + params_c1 * mpbe_f0(X2S * x) + params_c2 * mpbe_f0(X2S * x) ** 2 + params_c3 * mpbe_f0(X2S * x) ** 3

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, mpbe_f, rs, z, xs0, xs1)

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_c3_raw = params.c3
  if isinstance(params_c3_raw, (str, bytes, dict)):
    params_c3 = params_c3_raw
  else:
    try:
      params_c3_seq = list(params_c3_raw)
    except TypeError:
      params_c3 = params_c3_raw
    else:
      params_c3_seq = np.asarray(params_c3_seq, dtype=np.float64)
      params_c3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c3_seq))

  mpbe_f0 = lambda s: s ** 2 / (1 + params_a * s ** 2)

  mpbe_f = lambda x: 1 + params_c1 * mpbe_f0(X2S * x) + params_c2 * mpbe_f0(X2S * x) ** 2 + params_c3 * mpbe_f0(X2S * x) ** 3

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, mpbe_f, rs, z, xs0, xs1)

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
  t33 = params.c1 * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t33 * t37
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = 0.1e1 / t41 / t39
  t45 = params.a * t32
  t50 = 0.1e1 + t45 * t37 * s0 * t43 / 0.24e2
  t51 = 0.1e1 / t50
  t55 = t32 ** 2
  t58 = 0.1e1 / t35 / t34
  t59 = params.c2 * t55 * t58
  t60 = s0 ** 2
  t61 = t39 ** 2
  t64 = 0.1e1 / t40 / t61 / r0
  t66 = t50 ** 2
  t67 = 0.1e1 / t66
  t71 = t34 ** 2
  t72 = 0.1e1 / t71
  t73 = params.c3 * t72
  t74 = t60 * s0
  t75 = t61 ** 2
  t76 = 0.1e1 / t75
  t79 = 0.1e1 / t66 / t50
  t83 = 0.1e1 + t38 * s0 * t43 * t51 / 0.24e2 + t59 * t60 * t64 * t67 / 0.576e3 + t73 * t74 * t76 * t79 / 0.2304e4
  t87 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t83)
  t88 = r1 <= f.p.dens_threshold
  t89 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t90 = 0.1e1 + t89
  t91 = t90 <= f.p.zeta_threshold
  t92 = t90 ** (0.1e1 / 0.3e1)
  t93 = t92 ** 2
  t95 = f.my_piecewise3(t91, t24, t93 * t90)
  t96 = t95 * t30
  t97 = r1 ** 2
  t98 = r1 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t101 = 0.1e1 / t99 / t97
  t107 = 0.1e1 + t45 * t37 * s2 * t101 / 0.24e2
  t108 = 0.1e1 / t107
  t112 = s2 ** 2
  t113 = t97 ** 2
  t116 = 0.1e1 / t98 / t113 / r1
  t118 = t107 ** 2
  t119 = 0.1e1 / t118
  t123 = t112 * s2
  t124 = t113 ** 2
  t125 = 0.1e1 / t124
  t128 = 0.1e1 / t118 / t107
  t132 = 0.1e1 + t38 * s2 * t101 * t108 / 0.24e2 + t59 * t112 * t116 * t119 / 0.576e3 + t73 * t123 * t125 * t128 / 0.2304e4
  t136 = f.my_piecewise3(t88, 0, 0.3e1 / 0.20e2 * t6 * t96 * t132)
  t137 = t7 ** 2
  t139 = t17 / t137
  t140 = t8 - t139
  t141 = f.my_piecewise5(t11, 0, t15, 0, t140)
  t144 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t141)
  t149 = 0.1e1 / t29
  t153 = t6 * t28 * t149 * t83 / 0.10e2
  t154 = t39 * r0
  t162 = params.c1 * t55 * t58
  t166 = t60 / t40 / t61 / t39
  t167 = t67 * params.a
  t174 = params.c2 * t72
  t177 = 0.1e1 / t75 / r0
  t186 = t60 ** 2
  t192 = t66 ** 2
  t195 = t32 * t37
  t196 = 0.1e1 / t192 * params.a * t195
  t204 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t144 * t30 * t83 + t153 + 0.3e1 / 0.20e2 * t6 * t31 * (-t38 * s0 / t41 / t154 * t51 / 0.9e1 + t162 * t166 * t167 / 0.216e3 - t59 * t166 * t67 / 0.108e3 + t174 * t74 * t177 * t79 * params.a / 0.432e3 - t73 * t74 * t177 * t79 / 0.288e3 + t73 * t186 / t41 / t75 / t154 * t196 / 0.6912e4))
  t206 = f.my_piecewise5(t15, 0, t11, 0, -t140)
  t209 = f.my_piecewise3(t91, 0, 0.5e1 / 0.3e1 * t93 * t206)
  t217 = t6 * t95 * t149 * t132 / 0.10e2
  t219 = f.my_piecewise3(t88, 0, 0.3e1 / 0.20e2 * t6 * t209 * t30 * t132 + t217)
  vrho_0_ = t87 + t136 + t7 * (t204 + t219)
  t222 = -t8 - t139
  t223 = f.my_piecewise5(t11, 0, t15, 0, t222)
  t226 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t223)
  t232 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t226 * t30 * t83 + t153)
  t234 = f.my_piecewise5(t15, 0, t11, 0, -t222)
  t237 = f.my_piecewise3(t91, 0, 0.5e1 / 0.3e1 * t93 * t234)
  t242 = t97 * r1
  t252 = t112 / t98 / t113 / t97
  t253 = t119 * params.a
  t262 = 0.1e1 / t124 / r1
  t271 = t112 ** 2
  t277 = t118 ** 2
  t280 = 0.1e1 / t277 * params.a * t195
  t288 = f.my_piecewise3(t88, 0, 0.3e1 / 0.20e2 * t6 * t237 * t30 * t132 + t217 + 0.3e1 / 0.20e2 * t6 * t96 * (-t38 * s2 / t99 / t242 * t108 / 0.9e1 + t162 * t252 * t253 / 0.216e3 - t59 * t252 * t119 / 0.108e3 + t174 * t123 * t262 * t128 * params.a / 0.432e3 - t73 * t123 * t262 * t128 / 0.288e3 + t73 * t271 / t99 / t124 / t242 * t280 / 0.6912e4))
  vrho_1_ = t87 + t136 + t7 * (t232 + t288)
  t295 = s0 * t64
  t322 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (t33 * t37 * t43 * t51 / 0.24e2 - t162 * t295 * t167 / 0.576e3 + t59 * t295 * t67 / 0.288e3 - t174 * t60 * t76 * t79 * params.a / 0.1152e4 + t73 * t60 * t76 * t79 / 0.768e3 - t73 * t74 / t41 / t75 / t39 * t196 / 0.18432e5))
  vsigma_0_ = t7 * t322
  vsigma_1_ = 0.0e0
  t327 = s2 * t116
  t354 = f.my_piecewise3(t88, 0, 0.3e1 / 0.20e2 * t6 * t96 * (t33 * t37 * t101 * t108 / 0.24e2 - t162 * t327 * t253 / 0.576e3 + t59 * t327 * t119 / 0.288e3 - t174 * t112 * t125 * t128 * params.a / 0.1152e4 + t73 * t112 * t125 * t128 / 0.768e3 - t73 * t123 / t99 / t124 / t97 * t280 / 0.18432e5))
  vsigma_2_ = t7 * t354
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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_c3_raw = params.c3
  if isinstance(params_c3_raw, (str, bytes, dict)):
    params_c3 = params_c3_raw
  else:
    try:
      params_c3_seq = list(params_c3_raw)
    except TypeError:
      params_c3 = params_c3_raw
    else:
      params_c3_seq = np.asarray(params_c3_seq, dtype=np.float64)
      params_c3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c3_seq))

  mpbe_f0 = lambda s: s ** 2 / (1 + params_a * s ** 2)

  mpbe_f = lambda x: 1 + params_c1 * mpbe_f0(X2S * x) + params_c2 * mpbe_f0(X2S * x) ** 2 + params_c3 * mpbe_f0(X2S * x) ** 3

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, mpbe_f, rs, z, xs0, xs1)

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
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = params.c1 * t24 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t36 = 0.1e1 / t22 / t34
  t42 = 0.1e1 + params.a * t24 * t29 * t33 * t36 / 0.24e2
  t43 = 0.1e1 / t42
  t48 = t24 ** 2
  t51 = 0.1e1 / t27 / t26
  t52 = params.c2 * t48 * t51
  t53 = s0 ** 2
  t54 = t53 * t31
  t55 = t34 ** 2
  t58 = 0.1e1 / t21 / t55 / r0
  t59 = t42 ** 2
  t60 = 0.1e1 / t59
  t61 = t58 * t60
  t65 = t26 ** 2
  t66 = 0.1e1 / t65
  t67 = params.c3 * t66
  t68 = t53 * s0
  t69 = t55 ** 2
  t70 = 0.1e1 / t69
  t73 = 0.1e1 / t59 / t42
  t77 = 0.1e1 + t30 * t33 * t36 * t43 / 0.24e2 + t52 * t54 * t61 / 0.288e3 + t67 * t68 * t70 * t73 / 0.576e3
  t81 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t77)
  t87 = t34 * r0
  t94 = params.c1 * t48
  t99 = 0.1e1 / t21 / t55 / t34
  t101 = t60 * params.a
  t109 = params.c2 * t66
  t112 = 0.1e1 / t69 / r0
  t121 = t53 ** 2
  t127 = t59 ** 2
  t132 = 0.1e1 / t127 * params.a * t24 * t29 * t32
  t140 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t77 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-t30 * t33 / t22 / t87 * t43 / 0.9e1 + t94 * t51 * t53 * t31 * t99 * t101 / 0.108e3 - t52 * t54 * t99 * t60 / 0.54e2 + t109 * t68 * t112 * t73 * params.a / 0.108e3 - t67 * t68 * t112 * t73 / 0.72e2 + t67 * t121 / t22 / t69 / t87 * t132 / 0.1728e4))
  vrho_0_ = 0.2e1 * r0 * t140 + 0.2e1 * t81
  t177 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (t30 * t32 * t36 * t43 / 0.24e2 - t94 * t51 * s0 * t31 * t58 * t101 / 0.288e3 + t52 * s0 * t31 * t61 / 0.144e3 - t109 * t53 * t70 * t73 * params.a / 0.288e3 + t67 * t53 * t70 * t73 / 0.192e3 - t67 * t68 / t22 / t69 / t34 * t132 / 0.4608e4))
  vsigma_0_ = 0.2e1 * r0 * t177
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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = params.c1 * t24 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t37 = 0.1e1 / t35 / t34
  t43 = 0.1e1 + params.a * t24 * t29 * t33 * t37 / 0.24e2
  t44 = 0.1e1 / t43
  t49 = t24 ** 2
  t52 = 0.1e1 / t27 / t26
  t53 = params.c2 * t49 * t52
  t54 = s0 ** 2
  t55 = t54 * t31
  t56 = t34 ** 2
  t57 = t56 * r0
  t59 = 0.1e1 / t21 / t57
  t60 = t43 ** 2
  t61 = 0.1e1 / t60
  t62 = t59 * t61
  t66 = t26 ** 2
  t67 = 0.1e1 / t66
  t68 = params.c3 * t67
  t69 = t54 * s0
  t70 = t56 ** 2
  t71 = 0.1e1 / t70
  t74 = 0.1e1 / t60 / t43
  t78 = 0.1e1 + t30 * t33 * t37 * t44 / 0.24e2 + t53 * t55 * t62 / 0.288e3 + t68 * t69 * t71 * t74 / 0.576e3
  t82 = t20 * t35
  t83 = t34 * r0
  t85 = 0.1e1 / t35 / t83
  t90 = params.c1 * t49
  t92 = t90 * t52 * t54
  t93 = t56 * t34
  t95 = 0.1e1 / t21 / t93
  t97 = t61 * params.a
  t101 = t95 * t61
  t105 = params.c2 * t67
  t106 = t105 * t69
  t108 = 0.1e1 / t70 / r0
  t109 = t108 * t74
  t110 = t109 * params.a
  t117 = t54 ** 2
  t120 = 0.1e1 / t35 / t70 / t83
  t123 = t60 ** 2
  t124 = 0.1e1 / t123
  t127 = t24 * t29 * t32
  t128 = t124 * params.a * t127
  t131 = -t30 * t33 * t85 * t44 / 0.9e1 + t92 * t31 * t95 * t97 / 0.108e3 - t53 * t55 * t101 / 0.54e2 + t106 * t110 / 0.108e3 - t68 * t69 * t108 * t74 / 0.72e2 + t68 * t117 * t120 * t128 / 0.1728e4
  t136 = f.my_piecewise3(t2, 0, t7 * t23 * t78 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t82 * t131)
  t153 = t56 * t83
  t155 = 0.1e1 / t21 / t153
  t160 = params.c1 * t67
  t162 = t70 * t34
  t163 = 0.1e1 / t162
  t164 = t163 * t74
  t165 = params.a ** 2
  t179 = t117 / t35 / t70 / t56
  t182 = t124 * t165 * t127
  t203 = 0.1e1 / t123 / t43 * t165 * t49 * t52 * t31
  t211 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t78 / 0.30e2 + t7 * t23 * t131 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t82 * (0.11e2 / 0.27e2 * t30 * t33 / t35 / t56 * t44 - t92 * t31 * t155 * t97 / 0.12e2 + 0.2e1 / 0.81e2 * t160 * t69 * t164 * t165 + 0.19e2 / 0.162e3 * t53 * t55 * t155 * t61 - 0.43e2 / 0.324e3 * t106 * t164 * params.a + t105 * t179 * t182 / 0.324e3 + t68 * t69 * t163 * t74 / 0.8e1 - 0.59e2 / 0.5184e4 * t68 * t179 * t128 + t68 * t117 * s0 / t21 / t70 / t153 * t203 / 0.1944e4))
  v2rho2_0_ = 0.2e1 * r0 * t211 + 0.4e1 * t136
  t220 = t31 * t59
  t221 = t220 * t97
  t224 = s0 * t31
  t228 = t105 * t54
  t229 = t71 * t74
  t230 = t229 * params.a
  t238 = 0.1e1 / t35 / t162
  t243 = t30 * t32 * t37 * t44 / 0.24e2 - t90 * t52 * s0 * t221 / 0.288e3 + t53 * t224 * t62 / 0.144e3 - t228 * t230 / 0.288e3 + t68 * t54 * t71 * t74 / 0.192e3 - t68 * t69 * t238 * t128 / 0.4608e4
  t247 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t82 * t243)
  t270 = t69 * t120
  t293 = f.my_piecewise3(t2, 0, t7 * t23 * t243 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t82 * (-t30 * t32 * t85 * t44 / 0.9e1 + t90 * t52 * t31 * t101 * params.a * s0 / 0.36e2 - t160 * t54 * t109 * t165 / 0.108e3 - t53 * t224 * t101 / 0.27e2 + 0.5e1 / 0.108e3 * t228 * t110 - t105 * t270 * t182 / 0.864e3 - t68 * t54 * t108 * t74 / 0.24e2 + 0.7e1 / 0.1728e4 * t68 * t270 * t128 - t68 * t117 / t21 / t70 / t93 * t203 / 0.5184e4))
  v2rhosigma_0_ = 0.2e1 * r0 * t293 + 0.2e1 * t247
  t309 = t54 * t238
  t331 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t82 * (-t90 * t52 * t221 / 0.144e3 + t160 * s0 * t229 * t165 / 0.288e3 + t53 * t220 * t61 / 0.144e3 - t105 * s0 * t230 / 0.72e2 + t105 * t309 * t182 / 0.2304e4 + t68 * s0 * t71 * t74 / 0.96e2 - t68 * t309 * t128 / 0.768e3 + t68 * t69 / t21 / t70 / t57 * t203 / 0.13824e5))
  v2sigma2_0_ = 0.2e1 * r0 * t331
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
  t24 = t20 / t21 / r0
  t25 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = params.c1 * t25 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = r0 ** 2
  t36 = t21 ** 2
  t38 = 0.1e1 / t36 / t35
  t44 = 0.1e1 + params.a * t25 * t30 * t34 * t38 / 0.24e2
  t45 = 0.1e1 / t44
  t50 = t25 ** 2
  t53 = 0.1e1 / t28 / t27
  t54 = params.c2 * t50 * t53
  t55 = s0 ** 2
  t56 = t55 * t32
  t57 = t35 ** 2
  t58 = t57 * r0
  t61 = t44 ** 2
  t62 = 0.1e1 / t61
  t67 = t27 ** 2
  t68 = 0.1e1 / t67
  t69 = params.c3 * t68
  t70 = t55 * s0
  t71 = t57 ** 2
  t75 = 0.1e1 / t61 / t44
  t79 = 0.1e1 + t31 * t34 * t38 * t45 / 0.24e2 + t54 * t56 / t21 / t58 * t62 / 0.288e3 + t69 * t70 / t71 * t75 / 0.576e3
  t84 = t20 / t21
  t85 = t35 * r0
  t94 = params.c1 * t50 * t53 * t55
  t97 = 0.1e1 / t21 / t57 / t35
  t99 = t62 * params.a
  t107 = params.c2 * t68
  t108 = t107 * t70
  t110 = 0.1e1 / t71 / r0
  t119 = t55 ** 2
  t120 = t71 * t85
  t125 = t61 ** 2
  t126 = 0.1e1 / t125
  t129 = t25 * t30 * t33
  t130 = t126 * params.a * t129
  t133 = -t31 * t34 / t36 / t85 * t45 / 0.9e1 + t94 * t32 * t97 * t99 / 0.108e3 - t54 * t56 * t97 * t62 / 0.54e2 + t108 * t110 * t75 * params.a / 0.108e3 - t69 * t70 * t110 * t75 / 0.72e2 + t69 * t119 / t36 / t120 * t130 / 0.1728e4
  t137 = t20 * t36
  t144 = t57 * t85
  t146 = 0.1e1 / t21 / t144
  t151 = params.c1 * t68
  t152 = t151 * t70
  t154 = 0.1e1 / t71 / t35
  t155 = t154 * t75
  t156 = params.a ** 2
  t170 = t119 / t36 / t71 / t57
  t173 = t126 * t156 * t129
  t183 = t119 * s0
  t190 = 0.1e1 / t125 / t44
  t193 = t50 * t53 * t32
  t194 = t190 * t156 * t193
  t197 = 0.11e2 / 0.27e2 * t31 * t34 / t36 / t57 * t45 - t94 * t32 * t146 * t99 / 0.12e2 + 0.2e1 / 0.81e2 * t152 * t155 * t156 + 0.19e2 / 0.162e3 * t54 * t56 * t146 * t62 - 0.43e2 / 0.324e3 * t108 * t155 * params.a + t107 * t170 * t173 / 0.324e3 + t69 * t70 * t154 * t75 / 0.8e1 - 0.59e2 / 0.5184e4 * t69 * t170 * t130 + t69 * t183 / t21 / t71 / t144 * t194 / 0.1944e4
  t202 = f.my_piecewise3(t2, 0, -t7 * t24 * t79 / 0.30e2 + t7 * t84 * t133 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t137 * t197)
  t223 = 0.1e1 / t21 / t71
  t228 = 0.1e1 / t120
  t229 = t228 * t75
  t236 = t119 / t36 / t71 / t58
  t238 = t156 * params.a
  t253 = t71 ** 2
  t256 = t183 / t21 / t253
  t272 = t67 ** 2
  t285 = -0.154e3 / 0.81e2 * t31 * t34 / t36 / t58 * t45 + 0.341e3 / 0.486e3 * t94 * t32 * t223 * t99 - 0.38e2 / 0.81e2 * t152 * t229 * t156 + 0.2e1 / 0.243e3 * t151 * t236 * t126 * t238 * t129 - 0.209e3 / 0.243e3 * t54 * t56 * t223 * t62 + 0.797e3 / 0.486e3 * t108 * t229 * params.a - t107 * t236 * t173 / 0.12e2 + 0.2e1 / 0.729e3 * t107 * t256 * t190 * t238 * t193 - 0.5e1 / 0.4e1 * t69 * t70 * t228 * t75 + 0.1445e4 / 0.7776e4 * t69 * t236 * t130 - 0.35e2 / 0.1944e4 * t69 * t256 * t194 + 0.5e1 / 0.1458e4 * params.c3 / t272 * t119 * t55 / t253 / t85 / t125 / t61 * t238
  t290 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t35 * t79 - t7 * t24 * t133 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t84 * t197 + 0.3e1 / 0.20e2 * t7 * t137 * t285)
  v3rho3_0_ = 0.2e1 * r0 * t290 + 0.6e1 * t202

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
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = 0.1e1 / t30
  t32 = params.c1 * t26 * t31
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = s0 * t34
  t36 = t22 ** 2
  t38 = 0.1e1 / t36 / t21
  t44 = 0.1e1 + params.a * t26 * t31 * t35 * t38 / 0.24e2
  t45 = 0.1e1 / t44
  t50 = t26 ** 2
  t53 = 0.1e1 / t29 / t28
  t54 = params.c2 * t50 * t53
  t55 = s0 ** 2
  t56 = t55 * t33
  t57 = t21 ** 2
  t58 = t57 * r0
  t61 = t44 ** 2
  t62 = 0.1e1 / t61
  t67 = t28 ** 2
  t68 = 0.1e1 / t67
  t69 = params.c3 * t68
  t70 = t55 * s0
  t71 = t57 ** 2
  t74 = t61 * t44
  t75 = 0.1e1 / t74
  t79 = 0.1e1 + t32 * t35 * t38 * t45 / 0.24e2 + t54 * t56 / t22 / t58 * t62 / 0.288e3 + t69 * t70 / t71 * t75 / 0.576e3
  t85 = t20 / t22 / r0
  t86 = t21 * r0
  t95 = params.c1 * t50 * t53 * t55
  t96 = t57 * t21
  t98 = 0.1e1 / t22 / t96
  t100 = t62 * params.a
  t108 = params.c2 * t68
  t109 = t108 * t70
  t110 = t71 * r0
  t111 = 0.1e1 / t110
  t120 = t55 ** 2
  t121 = t71 * t86
  t126 = t61 ** 2
  t127 = 0.1e1 / t126
  t130 = t26 * t31 * t34
  t131 = t127 * params.a * t130
  t134 = -t32 * t35 / t36 / t86 * t45 / 0.9e1 + t95 * t33 * t98 * t100 / 0.108e3 - t54 * t56 * t98 * t62 / 0.54e2 + t109 * t111 * t75 * params.a / 0.108e3 - t69 * t70 * t111 * t75 / 0.72e2 + t69 * t120 / t36 / t121 * t131 / 0.1728e4
  t139 = t20 / t22
  t146 = t57 * t86
  t148 = 0.1e1 / t22 / t146
  t153 = params.c1 * t68
  t154 = t153 * t70
  t156 = 0.1e1 / t71 / t21
  t157 = t156 * t75
  t158 = params.a ** 2
  t169 = t71 * t57
  t172 = t120 / t36 / t169
  t175 = t127 * t158 * t130
  t185 = t120 * s0
  t192 = 0.1e1 / t126 / t44
  t195 = t50 * t53 * t33
  t196 = t192 * t158 * t195
  t199 = 0.11e2 / 0.27e2 * t32 * t35 / t36 / t57 * t45 - t95 * t33 * t148 * t100 / 0.12e2 + 0.2e1 / 0.81e2 * t154 * t157 * t158 + 0.19e2 / 0.162e3 * t54 * t56 * t148 * t62 - 0.43e2 / 0.324e3 * t109 * t157 * params.a + t108 * t172 * t175 / 0.324e3 + t69 * t70 * t156 * t75 / 0.8e1 - 0.59e2 / 0.5184e4 * t69 * t172 * t131 + t69 * t185 / t22 / t71 / t146 * t196 / 0.1944e4
  t203 = t20 * t36
  t211 = 0.1e1 / t22 / t71
  t216 = 0.1e1 / t121
  t217 = t216 * t75
  t224 = t120 / t36 / t71 / t58
  t226 = t158 * params.a
  t228 = t127 * t226 * t130
  t241 = t71 ** 2
  t244 = t185 / t22 / t241
  t247 = t192 * t226 * t195
  t260 = t67 ** 2
  t261 = 0.1e1 / t260
  t262 = params.c3 * t261
  t263 = t120 * t55
  t264 = t262 * t263
  t268 = 0.1e1 / t126 / t61
  t273 = -0.154e3 / 0.81e2 * t32 * t35 / t36 / t58 * t45 + 0.341e3 / 0.486e3 * t95 * t33 * t211 * t100 - 0.38e2 / 0.81e2 * t154 * t217 * t158 + 0.2e1 / 0.243e3 * t153 * t224 * t228 - 0.209e3 / 0.243e3 * t54 * t56 * t211 * t62 + 0.797e3 / 0.486e3 * t109 * t217 * params.a - t108 * t224 * t175 / 0.12e2 + 0.2e1 / 0.729e3 * t108 * t244 * t247 - 0.5e1 / 0.4e1 * t69 * t70 * t216 * t75 + 0.1445e4 / 0.7776e4 * t69 * t224 * t131 - 0.35e2 / 0.1944e4 * t69 * t244 * t196 + 0.5e1 / 0.1458e4 * t264 / t241 / t86 * t268 * t226
  t278 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t79 - t7 * t85 * t134 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t139 * t199 + 0.3e1 / 0.20e2 * t7 * t203 * t273)
  t302 = 0.1e1 / t22 / t110
  t307 = 0.1e1 / t169
  t308 = t307 * t75
  t315 = t120 / t36 / t71 / t96
  t322 = t185 / t22 / t241 / r0
  t324 = t158 ** 2
  t346 = 0.1e1 / t241 / t57 * t268
  t375 = 0.2618e4 / 0.243e3 * t32 * t35 / t36 / t96 * t45 - 0.3047e4 / 0.486e3 * t95 * t33 * t302 * t100 + 0.5126e4 / 0.729e3 * t154 * t308 * t158 - 0.196e3 / 0.729e3 * t153 * t315 * t228 + 0.16e2 / 0.2187e4 * t153 * t322 * t192 * t324 * t195 + 0.5225e4 / 0.729e3 * t54 * t56 * t302 * t62 - 0.29645e5 / 0.1458e4 * t109 * t308 * params.a + 0.4915e4 / 0.2916e4 * t108 * t315 * t175 - 0.260e3 / 0.2187e4 * t108 * t322 * t247 + 0.40e2 / 0.2187e4 * params.c2 * t261 * t263 * t346 * t324 + 0.55e2 / 0.4e1 * t69 * t70 * t307 * t75 - 0.68965e5 / 0.23328e5 * t69 * t315 * t131 + 0.8035e4 / 0.17496e5 * t69 * t322 * t196 - 0.5e1 / 0.27e2 * t264 * t346 * t226 + 0.5e1 / 0.2187e4 * t262 * t120 * t70 / t36 / t241 / t96 / t126 / t74 * t324 * t130
  t380 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 / t22 / t86 * t79 + 0.8e1 / 0.45e2 * t7 * t25 * t134 - t7 * t85 * t199 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t139 * t273 + 0.3e1 / 0.20e2 * t7 * t203 * t375)
  v4rho4_0_ = 0.2e1 * r0 * t380 + 0.8e1 * t278

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
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t40 = 0.1e1 / t39
  t41 = params.c1 * t35 * t40
  t42 = r0 ** 2
  t43 = r0 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t46 = 0.1e1 / t44 / t42
  t48 = params.a * t35
  t53 = 0.1e1 + t48 * t40 * s0 * t46 / 0.24e2
  t54 = 0.1e1 / t53
  t58 = t35 ** 2
  t61 = 0.1e1 / t38 / t37
  t62 = params.c2 * t58 * t61
  t63 = s0 ** 2
  t64 = t42 ** 2
  t69 = t53 ** 2
  t70 = 0.1e1 / t69
  t74 = t37 ** 2
  t75 = 0.1e1 / t74
  t76 = params.c3 * t75
  t77 = t63 * s0
  t78 = t64 ** 2
  t82 = 0.1e1 / t69 / t53
  t86 = 0.1e1 + t41 * s0 * t46 * t54 / 0.24e2 + t62 * t63 / t43 / t64 / r0 * t70 / 0.576e3 + t76 * t77 / t78 * t82 / 0.2304e4
  t90 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t91 = t90 ** 2
  t92 = t91 * f.p.zeta_threshold
  t94 = f.my_piecewise3(t21, t92, t23 * t20)
  t95 = 0.1e1 / t32
  t96 = t94 * t95
  t99 = t6 * t96 * t86 / 0.10e2
  t100 = t94 * t33
  t101 = t42 * r0
  t109 = params.c1 * t58 * t61
  t113 = t63 / t43 / t64 / t42
  t114 = t70 * params.a
  t121 = params.c2 * t75
  t122 = t121 * t77
  t124 = 0.1e1 / t78 / r0
  t133 = t63 ** 2
  t139 = t69 ** 2
  t140 = 0.1e1 / t139
  t142 = t35 * t40
  t143 = t140 * params.a * t142
  t146 = -t41 * s0 / t44 / t101 * t54 / 0.9e1 + t109 * t113 * t114 / 0.216e3 - t62 * t113 * t70 / 0.108e3 + t122 * t124 * t82 * params.a / 0.432e3 - t76 * t77 * t124 * t82 / 0.288e3 + t76 * t133 / t44 / t78 / t101 * t143 / 0.6912e4
  t151 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t86 + t99 + 0.3e1 / 0.20e2 * t6 * t100 * t146)
  t153 = r1 <= f.p.dens_threshold
  t154 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t155 = 0.1e1 + t154
  t156 = t155 <= f.p.zeta_threshold
  t157 = t155 ** (0.1e1 / 0.3e1)
  t158 = t157 ** 2
  t160 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t163 = f.my_piecewise3(t156, 0, 0.5e1 / 0.3e1 * t158 * t160)
  t164 = t163 * t33
  t165 = r1 ** 2
  t166 = r1 ** (0.1e1 / 0.3e1)
  t167 = t166 ** 2
  t169 = 0.1e1 / t167 / t165
  t175 = 0.1e1 + t48 * t40 * s2 * t169 / 0.24e2
  t176 = 0.1e1 / t175
  t180 = s2 ** 2
  t181 = t165 ** 2
  t186 = t175 ** 2
  t187 = 0.1e1 / t186
  t191 = t180 * s2
  t192 = t181 ** 2
  t196 = 0.1e1 / t186 / t175
  t200 = 0.1e1 + t41 * s2 * t169 * t176 / 0.24e2 + t62 * t180 / t166 / t181 / r1 * t187 / 0.576e3 + t76 * t191 / t192 * t196 / 0.2304e4
  t205 = f.my_piecewise3(t156, t92, t158 * t155)
  t206 = t205 * t95
  t209 = t6 * t206 * t200 / 0.10e2
  t211 = f.my_piecewise3(t153, 0, 0.3e1 / 0.20e2 * t6 * t164 * t200 + t209)
  t213 = 0.1e1 / t22
  t214 = t28 ** 2
  t219 = t17 / t24 / t7
  t221 = -0.2e1 * t25 + 0.2e1 * t219
  t222 = f.my_piecewise5(t11, 0, t15, 0, t221)
  t226 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t213 * t214 + 0.5e1 / 0.3e1 * t23 * t222)
  t233 = t6 * t31 * t95 * t86
  t239 = 0.1e1 / t32 / t7
  t243 = t6 * t94 * t239 * t86 / 0.30e2
  t245 = t6 * t96 * t146
  t253 = t64 * t101
  t256 = t63 / t43 / t253
  t260 = params.c1 * t75
  t263 = 0.1e1 / t78 / t42
  t264 = t263 * t82
  t265 = params.a ** 2
  t278 = t133 / t44 / t78 / t64
  t300 = t58 * t61
  t309 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t226 * t33 * t86 + t233 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t146 - t243 + t245 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t100 * (0.11e2 / 0.27e2 * t41 * s0 / t44 / t64 * t54 - t109 * t256 * t114 / 0.24e2 + t260 * t77 * t264 * t265 / 0.162e3 + 0.19e2 / 0.324e3 * t62 * t256 * t70 - 0.43e2 / 0.1296e4 * t122 * t264 * params.a + t121 * t278 * t140 * t265 * t142 / 0.1296e4 + t76 * t77 * t263 * t82 / 0.32e2 - 0.59e2 / 0.20736e5 * t76 * t278 * t143 + t76 * t133 * s0 / t43 / t78 / t253 / t139 / t53 * t265 * t300 / 0.15552e5))
  t310 = 0.1e1 / t157
  t311 = t160 ** 2
  t315 = f.my_piecewise5(t15, 0, t11, 0, -t221)
  t319 = f.my_piecewise3(t156, 0, 0.10e2 / 0.9e1 * t310 * t311 + 0.5e1 / 0.3e1 * t158 * t315)
  t326 = t6 * t163 * t95 * t200
  t331 = t6 * t205 * t239 * t200 / 0.30e2
  t333 = f.my_piecewise3(t153, 0, 0.3e1 / 0.20e2 * t6 * t319 * t33 * t200 + t326 / 0.5e1 - t331)
  d11 = 0.2e1 * t151 + 0.2e1 * t211 + t7 * (t309 + t333)
  t336 = -t8 - t26
  t337 = f.my_piecewise5(t11, 0, t15, 0, t336)
  t340 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t337)
  t341 = t340 * t33
  t346 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t341 * t86 + t99)
  t348 = f.my_piecewise5(t15, 0, t11, 0, -t336)
  t351 = f.my_piecewise3(t156, 0, 0.5e1 / 0.3e1 * t158 * t348)
  t352 = t351 * t33
  t356 = t205 * t33
  t357 = t165 * r1
  t367 = t180 / t166 / t181 / t165
  t368 = t187 * params.a
  t375 = t121 * t191
  t377 = 0.1e1 / t192 / r1
  t386 = t180 ** 2
  t392 = t186 ** 2
  t393 = 0.1e1 / t392
  t395 = t393 * params.a * t142
  t398 = -t41 * s2 / t167 / t357 * t176 / 0.9e1 + t109 * t367 * t368 / 0.216e3 - t62 * t367 * t187 / 0.108e3 + t375 * t377 * t196 * params.a / 0.432e3 - t76 * t191 * t377 * t196 / 0.288e3 + t76 * t386 / t167 / t192 / t357 * t395 / 0.6912e4
  t403 = f.my_piecewise3(t153, 0, 0.3e1 / 0.20e2 * t6 * t352 * t200 + t209 + 0.3e1 / 0.20e2 * t6 * t356 * t398)
  t407 = 0.2e1 * t219
  t408 = f.my_piecewise5(t11, 0, t15, 0, t407)
  t412 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t213 * t337 * t28 + 0.5e1 / 0.3e1 * t23 * t408)
  t419 = t6 * t340 * t95 * t86
  t427 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t412 * t33 * t86 + t419 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t341 * t146 + t233 / 0.10e2 - t243 + t245 / 0.10e2)
  t431 = f.my_piecewise5(t15, 0, t11, 0, -t407)
  t435 = f.my_piecewise3(t156, 0, 0.10e2 / 0.9e1 * t310 * t348 * t160 + 0.5e1 / 0.3e1 * t158 * t431)
  t442 = t6 * t351 * t95 * t200
  t449 = t6 * t206 * t398
  t452 = f.my_piecewise3(t153, 0, 0.3e1 / 0.20e2 * t6 * t435 * t33 * t200 + t442 / 0.10e2 + t326 / 0.10e2 - t331 + 0.3e1 / 0.20e2 * t6 * t164 * t398 + t449 / 0.10e2)
  d12 = t151 + t211 + t346 + t403 + t7 * (t427 + t452)
  t457 = t337 ** 2
  t461 = 0.2e1 * t25 + 0.2e1 * t219
  t462 = f.my_piecewise5(t11, 0, t15, 0, t461)
  t466 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t213 * t457 + 0.5e1 / 0.3e1 * t23 * t462)
  t473 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t466 * t33 * t86 + t419 / 0.5e1 - t243)
  t474 = t348 ** 2
  t478 = f.my_piecewise5(t15, 0, t11, 0, -t461)
  t482 = f.my_piecewise3(t156, 0, 0.10e2 / 0.9e1 * t310 * t474 + 0.5e1 / 0.3e1 * t158 * t478)
  t498 = t181 * t357
  t501 = t180 / t166 / t498
  t507 = 0.1e1 / t192 / t165
  t508 = t507 * t196
  t521 = t386 / t167 / t192 / t181
  t551 = f.my_piecewise3(t153, 0, 0.3e1 / 0.20e2 * t6 * t482 * t33 * t200 + t442 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t352 * t398 - t331 + t449 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t356 * (0.11e2 / 0.27e2 * t41 * s2 / t167 / t181 * t176 - t109 * t501 * t368 / 0.24e2 + t260 * t191 * t508 * t265 / 0.162e3 + 0.19e2 / 0.324e3 * t62 * t501 * t187 - 0.43e2 / 0.1296e4 * t375 * t508 * params.a + t121 * t521 * t393 * t265 * t142 / 0.1296e4 + t76 * t191 * t507 * t196 / 0.32e2 - 0.59e2 / 0.20736e5 * t76 * t521 * t395 + t76 * t386 * s2 / t166 / t192 / t498 / t392 / t175 * t265 * t300 / 0.15552e5))
  d22 = 0.2e1 * t346 + 0.2e1 * t403 + t7 * (t473 + t551)
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
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t52 = params.c1 * t46 * t51
  t53 = r0 ** 2
  t54 = r0 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t57 = 0.1e1 / t55 / t53
  t59 = params.a * t46
  t64 = 0.1e1 + t59 * t51 * s0 * t57 / 0.24e2
  t65 = 0.1e1 / t64
  t69 = t46 ** 2
  t72 = 0.1e1 / t49 / t48
  t73 = params.c2 * t69 * t72
  t74 = s0 ** 2
  t75 = t53 ** 2
  t76 = t75 * r0
  t80 = t64 ** 2
  t81 = 0.1e1 / t80
  t85 = t48 ** 2
  t86 = 0.1e1 / t85
  t87 = params.c3 * t86
  t88 = t74 * s0
  t89 = t75 ** 2
  t93 = 0.1e1 / t80 / t64
  t97 = 0.1e1 + t52 * s0 * t57 * t65 / 0.24e2 + t73 * t74 / t54 / t76 * t81 / 0.576e3 + t87 * t88 / t89 * t93 / 0.2304e4
  t103 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t104 = 0.1e1 / t43
  t105 = t103 * t104
  t109 = t103 * t44
  t110 = t53 * r0
  t118 = params.c1 * t69 * t72
  t122 = t74 / t54 / t75 / t53
  t123 = t81 * params.a
  t130 = params.c2 * t86
  t131 = t130 * t88
  t133 = 0.1e1 / t89 / r0
  t142 = t74 ** 2
  t143 = t89 * t110
  t148 = t80 ** 2
  t149 = 0.1e1 / t148
  t151 = t46 * t51
  t152 = t149 * params.a * t151
  t155 = -t52 * s0 / t55 / t110 * t65 / 0.9e1 + t118 * t122 * t123 / 0.216e3 - t73 * t122 * t81 / 0.108e3 + t131 * t133 * t93 * params.a / 0.432e3 - t87 * t88 * t133 * t93 / 0.288e3 + t87 * t142 / t55 / t143 * t152 / 0.6912e4
  t159 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t160 = t159 ** 2
  t161 = t160 * f.p.zeta_threshold
  t163 = f.my_piecewise3(t21, t161, t32 * t20)
  t165 = 0.1e1 / t43 / t7
  t166 = t163 * t165
  t170 = t163 * t104
  t174 = t163 * t44
  t181 = t75 * t110
  t184 = t74 / t54 / t181
  t188 = params.c1 * t86
  t189 = t188 * t88
  t191 = 0.1e1 / t89 / t53
  t192 = t191 * t93
  t193 = params.a ** 2
  t206 = t142 / t55 / t89 / t75
  t209 = t149 * t193 * t151
  t219 = t142 * s0
  t226 = 0.1e1 / t148 / t64
  t228 = t69 * t72
  t229 = t226 * t193 * t228
  t232 = 0.11e2 / 0.27e2 * t52 * s0 / t55 / t75 * t65 - t118 * t184 * t123 / 0.24e2 + t189 * t192 * t193 / 0.162e3 + 0.19e2 / 0.324e3 * t73 * t184 * t81 - 0.43e2 / 0.1296e4 * t131 * t192 * params.a + t130 * t206 * t209 / 0.1296e4 + t87 * t88 * t191 * t93 / 0.32e2 - 0.59e2 / 0.20736e5 * t87 * t206 * t152 + t87 * t219 / t54 / t89 / t181 * t229 / 0.15552e5
  t237 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t97 + t6 * t105 * t97 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t109 * t155 - t6 * t166 * t97 / 0.30e2 + t6 * t170 * t155 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t174 * t232)
  t239 = r1 <= f.p.dens_threshold
  t240 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t241 = 0.1e1 + t240
  t242 = t241 <= f.p.zeta_threshold
  t243 = t241 ** (0.1e1 / 0.3e1)
  t244 = 0.1e1 / t243
  t246 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t247 = t246 ** 2
  t250 = t243 ** 2
  t252 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t256 = f.my_piecewise3(t242, 0, 0.10e2 / 0.9e1 * t244 * t247 + 0.5e1 / 0.3e1 * t250 * t252)
  t258 = r1 ** 2
  t259 = r1 ** (0.1e1 / 0.3e1)
  t260 = t259 ** 2
  t262 = 0.1e1 / t260 / t258
  t268 = 0.1e1 + t59 * t51 * s2 * t262 / 0.24e2
  t273 = s2 ** 2
  t274 = t258 ** 2
  t279 = t268 ** 2
  t285 = t274 ** 2
  t293 = 0.1e1 + t52 * s2 * t262 / t268 / 0.24e2 + t73 * t273 / t259 / t274 / r1 / t279 / 0.576e3 + t87 * t273 * s2 / t285 / t279 / t268 / 0.2304e4
  t299 = f.my_piecewise3(t242, 0, 0.5e1 / 0.3e1 * t250 * t246)
  t305 = f.my_piecewise3(t242, t161, t250 * t241)
  t311 = f.my_piecewise3(t239, 0, 0.3e1 / 0.20e2 * t6 * t256 * t44 * t293 + t6 * t299 * t104 * t293 / 0.5e1 - t6 * t305 * t165 * t293 / 0.30e2)
  t321 = t24 ** 2
  t325 = 0.6e1 * t34 - 0.6e1 * t17 / t321
  t326 = f.my_piecewise5(t11, 0, t15, 0, t325)
  t330 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t326)
  t353 = 0.1e1 / t43 / t24
  t372 = t74 / t54 / t89
  t376 = 0.1e1 / t143
  t377 = t376 * t93
  t384 = t142 / t55 / t89 / t76
  t386 = t193 * params.a
  t400 = t89 ** 2
  t403 = t219 / t54 / t400
  t419 = t85 ** 2
  t432 = -0.154e3 / 0.81e2 * t52 * s0 / t55 / t76 * t65 + 0.341e3 / 0.972e3 * t118 * t372 * t123 - 0.19e2 / 0.162e3 * t189 * t377 * t193 + t188 * t384 * t149 * t386 * t151 / 0.486e3 - 0.209e3 / 0.486e3 * t73 * t372 * t81 + 0.797e3 / 0.1944e4 * t131 * t377 * params.a - t130 * t384 * t209 / 0.48e2 + t130 * t403 * t226 * t386 * t228 / 0.2916e4 - 0.5e1 / 0.16e2 * t87 * t88 * t376 * t93 + 0.1445e4 / 0.31104e5 * t87 * t384 * t152 - 0.35e2 / 0.15552e5 * t87 * t403 * t229 + 0.5e1 / 0.23328e5 * params.c3 / t419 * t142 * t74 / t400 / t110 / t148 / t80 * t386
  t437 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t330 * t44 * t97 + 0.3e1 / 0.10e2 * t6 * t42 * t104 * t97 + 0.9e1 / 0.20e2 * t6 * t45 * t155 - t6 * t103 * t165 * t97 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t105 * t155 + 0.9e1 / 0.20e2 * t6 * t109 * t232 + 0.2e1 / 0.45e2 * t6 * t163 * t353 * t97 - t6 * t166 * t155 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t170 * t232 + 0.3e1 / 0.20e2 * t6 * t174 * t432)
  t447 = f.my_piecewise5(t15, 0, t11, 0, -t325)
  t451 = f.my_piecewise3(t242, 0, -0.10e2 / 0.27e2 / t243 / t241 * t247 * t246 + 0.10e2 / 0.3e1 * t244 * t246 * t252 + 0.5e1 / 0.3e1 * t250 * t447)
  t469 = f.my_piecewise3(t239, 0, 0.3e1 / 0.20e2 * t6 * t451 * t44 * t293 + 0.3e1 / 0.10e2 * t6 * t256 * t104 * t293 - t6 * t299 * t165 * t293 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t305 * t353 * t293)
  d111 = 0.3e1 * t237 + 0.3e1 * t311 + t7 * (t437 + t469)

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
  t60 = jnp.pi ** 2
  t61 = t60 ** (0.1e1 / 0.3e1)
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t64 = params.c1 * t58 * t63
  t65 = r0 ** 2
  t66 = r0 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t69 = 0.1e1 / t67 / t65
  t71 = params.a * t58
  t76 = 0.1e1 + t71 * t63 * s0 * t69 / 0.24e2
  t77 = 0.1e1 / t76
  t81 = t58 ** 2
  t84 = 0.1e1 / t61 / t60
  t85 = params.c2 * t81 * t84
  t86 = s0 ** 2
  t87 = t65 ** 2
  t88 = t87 * r0
  t92 = t76 ** 2
  t93 = 0.1e1 / t92
  t97 = t60 ** 2
  t98 = 0.1e1 / t97
  t99 = params.c3 * t98
  t100 = t86 * s0
  t101 = t87 ** 2
  t104 = t92 * t76
  t105 = 0.1e1 / t104
  t109 = 0.1e1 + t64 * s0 * t69 * t77 / 0.24e2 + t85 * t86 / t66 / t88 * t93 / 0.576e3 + t99 * t100 / t101 * t105 / 0.2304e4
  t118 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t119 = 0.1e1 / t55
  t120 = t118 * t119
  t124 = t118 * t56
  t125 = t65 * r0
  t133 = params.c1 * t81 * t84
  t134 = t87 * t65
  t137 = t86 / t66 / t134
  t138 = t93 * params.a
  t145 = params.c2 * t98
  t146 = t145 * t100
  t147 = t101 * r0
  t148 = 0.1e1 / t147
  t157 = t86 ** 2
  t158 = t101 * t125
  t163 = t92 ** 2
  t164 = 0.1e1 / t163
  t166 = t58 * t63
  t167 = t164 * params.a * t166
  t170 = -t64 * s0 / t67 / t125 * t77 / 0.9e1 + t133 * t137 * t138 / 0.216e3 - t85 * t137 * t93 / 0.108e3 + t146 * t148 * t105 * params.a / 0.432e3 - t99 * t100 * t148 * t105 / 0.288e3 + t99 * t157 / t67 / t158 * t167 / 0.6912e4
  t176 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t178 = 0.1e1 / t55 / t7
  t179 = t176 * t178
  t183 = t176 * t119
  t187 = t176 * t56
  t194 = t87 * t125
  t197 = t86 / t66 / t194
  t201 = params.c1 * t98
  t202 = t201 * t100
  t204 = 0.1e1 / t101 / t65
  t205 = t204 * t105
  t206 = params.a ** 2
  t216 = t101 * t87
  t219 = t157 / t67 / t216
  t222 = t164 * t206 * t166
  t232 = t157 * s0
  t239 = 0.1e1 / t163 / t76
  t241 = t81 * t84
  t242 = t239 * t206 * t241
  t245 = 0.11e2 / 0.27e2 * t64 * s0 / t67 / t87 * t77 - t133 * t197 * t138 / 0.24e2 + t202 * t205 * t206 / 0.162e3 + 0.19e2 / 0.324e3 * t85 * t197 * t93 - 0.43e2 / 0.1296e4 * t146 * t205 * params.a + t145 * t219 * t222 / 0.1296e4 + t99 * t100 * t204 * t105 / 0.32e2 - 0.59e2 / 0.20736e5 * t99 * t219 * t167 + t99 * t232 / t66 / t101 / t194 * t242 / 0.15552e5
  t249 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t250 = t249 ** 2
  t251 = t250 * f.p.zeta_threshold
  t253 = f.my_piecewise3(t21, t251, t44 * t20)
  t255 = 0.1e1 / t55 / t25
  t256 = t253 * t255
  t260 = t253 * t178
  t264 = t253 * t119
  t268 = t253 * t56
  t277 = t86 / t66 / t101
  t281 = 0.1e1 / t158
  t282 = t281 * t105
  t289 = t157 / t67 / t101 / t88
  t291 = t206 * params.a
  t293 = t164 * t291 * t166
  t305 = t101 ** 2
  t308 = t232 / t66 / t305
  t311 = t239 * t291 * t241
  t324 = t97 ** 2
  t325 = 0.1e1 / t324
  t326 = params.c3 * t325
  t327 = t157 * t86
  t328 = t326 * t327
  t332 = 0.1e1 / t163 / t92
  t337 = -0.154e3 / 0.81e2 * t64 * s0 / t67 / t88 * t77 + 0.341e3 / 0.972e3 * t133 * t277 * t138 - 0.19e2 / 0.162e3 * t202 * t282 * t206 + t201 * t289 * t293 / 0.486e3 - 0.209e3 / 0.486e3 * t85 * t277 * t93 + 0.797e3 / 0.1944e4 * t146 * t282 * params.a - t145 * t289 * t222 / 0.48e2 + t145 * t308 * t311 / 0.2916e4 - 0.5e1 / 0.16e2 * t99 * t100 * t281 * t105 + 0.1445e4 / 0.31104e5 * t99 * t289 * t167 - 0.35e2 / 0.15552e5 * t99 * t308 * t242 + 0.5e1 / 0.23328e5 * t328 / t305 / t125 * t332 * t291
  t342 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t109 + 0.3e1 / 0.10e2 * t6 * t120 * t109 + 0.9e1 / 0.20e2 * t6 * t124 * t170 - t6 * t179 * t109 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t183 * t170 + 0.9e1 / 0.20e2 * t6 * t187 * t245 + 0.2e1 / 0.45e2 * t6 * t256 * t109 - t6 * t260 * t170 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t264 * t245 + 0.3e1 / 0.20e2 * t6 * t268 * t337)
  t344 = r1 <= f.p.dens_threshold
  t345 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t346 = 0.1e1 + t345
  t347 = t346 <= f.p.zeta_threshold
  t348 = t346 ** (0.1e1 / 0.3e1)
  t350 = 0.1e1 / t348 / t346
  t352 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t353 = t352 ** 2
  t357 = 0.1e1 / t348
  t358 = t357 * t352
  t360 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t363 = t348 ** 2
  t365 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t369 = f.my_piecewise3(t347, 0, -0.10e2 / 0.27e2 * t350 * t353 * t352 + 0.10e2 / 0.3e1 * t358 * t360 + 0.5e1 / 0.3e1 * t363 * t365)
  t371 = r1 ** 2
  t372 = r1 ** (0.1e1 / 0.3e1)
  t373 = t372 ** 2
  t375 = 0.1e1 / t373 / t371
  t381 = 0.1e1 + t71 * t63 * s2 * t375 / 0.24e2
  t386 = s2 ** 2
  t387 = t371 ** 2
  t392 = t381 ** 2
  t398 = t387 ** 2
  t406 = 0.1e1 + t64 * s2 * t375 / t381 / 0.24e2 + t85 * t386 / t372 / t387 / r1 / t392 / 0.576e3 + t99 * t386 * s2 / t398 / t392 / t381 / 0.2304e4
  t415 = f.my_piecewise3(t347, 0, 0.10e2 / 0.9e1 * t357 * t353 + 0.5e1 / 0.3e1 * t363 * t360)
  t422 = f.my_piecewise3(t347, 0, 0.5e1 / 0.3e1 * t363 * t352)
  t428 = f.my_piecewise3(t347, t251, t363 * t346)
  t434 = f.my_piecewise3(t344, 0, 0.3e1 / 0.20e2 * t6 * t369 * t56 * t406 + 0.3e1 / 0.10e2 * t6 * t415 * t119 * t406 - t6 * t422 * t178 * t406 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t428 * t255 * t406)
  t468 = t86 / t66 / t147
  t472 = 0.1e1 / t216
  t473 = t472 * t105
  t480 = t157 / t67 / t101 / t134
  t487 = t232 / t66 / t305 / r0
  t489 = t206 ** 2
  t510 = 0.1e1 / t305 / t87 * t332
  t539 = 0.2618e4 / 0.243e3 * t64 * s0 / t67 / t134 * t77 - 0.3047e4 / 0.972e3 * t133 * t468 * t138 + 0.2563e4 / 0.1458e4 * t202 * t473 * t206 - 0.49e2 / 0.729e3 * t201 * t480 * t293 + 0.2e1 / 0.2187e4 * t201 * t487 * t239 * t489 * t241 + 0.5225e4 / 0.1458e4 * t85 * t468 * t93 - 0.29645e5 / 0.5832e4 * t146 * t473 * params.a + 0.4915e4 / 0.11664e5 * t145 * t480 * t222 - 0.65e2 / 0.4374e4 * t145 * t487 * t311 + 0.5e1 / 0.4374e4 * params.c2 * t325 * t327 * t510 * t489 + 0.55e2 / 0.16e2 * t99 * t100 * t472 * t105 - 0.68965e5 / 0.93312e5 * t99 * t480 * t167 + 0.8035e4 / 0.139968e6 * t99 * t487 * t242 - 0.5e1 / 0.432e3 * t328 * t510 * t291 + 0.5e1 / 0.34992e5 * t326 * t157 * t100 / t67 / t305 / t134 / t163 / t104 * t489 * t166
  t543 = t20 ** 2
  t546 = t30 ** 2
  t552 = t41 ** 2
  t561 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t562 = f.my_piecewise5(t11, 0, t15, 0, t561)
  t566 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t543 * t546 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t552 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t562)
  t587 = 0.1e1 / t55 / t36
  t592 = 0.6e1 / 0.5e1 * t6 * t120 * t170 + 0.9e1 / 0.10e2 * t6 * t124 * t245 - 0.2e1 / 0.5e1 * t6 * t179 * t170 + 0.6e1 / 0.5e1 * t6 * t183 * t245 + 0.3e1 / 0.5e1 * t6 * t187 * t337 + 0.8e1 / 0.45e2 * t6 * t256 * t170 - t6 * t260 * t245 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t264 * t337 + 0.3e1 / 0.20e2 * t6 * t268 * t539 + 0.3e1 / 0.20e2 * t6 * t566 * t56 * t109 + 0.3e1 / 0.5e1 * t6 * t57 * t170 + 0.2e1 / 0.5e1 * t6 * t54 * t119 * t109 - t6 * t118 * t178 * t109 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t176 * t255 * t109 - 0.14e2 / 0.135e3 * t6 * t253 * t587 * t109
  t593 = f.my_piecewise3(t1, 0, t592)
  t594 = t346 ** 2
  t597 = t353 ** 2
  t603 = t360 ** 2
  t609 = f.my_piecewise5(t15, 0, t11, 0, -t561)
  t613 = f.my_piecewise3(t347, 0, 0.40e2 / 0.81e2 / t348 / t594 * t597 - 0.20e2 / 0.9e1 * t350 * t353 * t360 + 0.10e2 / 0.3e1 * t357 * t603 + 0.40e2 / 0.9e1 * t358 * t365 + 0.5e1 / 0.3e1 * t363 * t609)
  t635 = f.my_piecewise3(t344, 0, 0.3e1 / 0.20e2 * t6 * t613 * t56 * t406 + 0.2e1 / 0.5e1 * t6 * t369 * t119 * t406 - t6 * t415 * t178 * t406 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t422 * t255 * t406 - 0.14e2 / 0.135e3 * t6 * t428 * t587 * t406)
  d1111 = 0.4e1 * t342 + 0.4e1 * t434 + t7 * (t593 + t635)

  res = {'v4rho4': d1111}
  return res
