"""Generated from gga_x_mpbe.mpl."""

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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, mpbe_f, rs, z, xs0, xs1)

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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, mpbe_f, rs, z, xs0, xs1)

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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, mpbe_f, rs, z, xs0, xs1)

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
  t29 = params.c1 * t28
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = t29 * t33
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t41 = params.a * t28
  t46 = 0.1e1 + t41 * t33 * s0 * t39 / 0.24e2
  t47 = 0.1e1 / t46
  t51 = t28 ** 2
  t54 = 0.1e1 / t31 / t30
  t55 = params.c2 * t51 * t54
  t56 = s0 ** 2
  t57 = t35 ** 2
  t60 = 0.1e1 / t36 / t57 / r0
  t62 = t46 ** 2
  t63 = 0.1e1 / t62
  t67 = t30 ** 2
  t68 = 0.1e1 / t67
  t69 = params.c3 * t68
  t70 = t56 * s0
  t71 = t57 ** 2
  t72 = 0.1e1 / t71
  t75 = 0.1e1 / t62 / t46
  t79 = 0.1e1 + t34 * s0 * t39 * t47 / 0.24e2 + t55 * t56 * t60 * t63 / 0.576e3 + t69 * t70 * t72 * t75 / 0.2304e4
  t83 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t79)
  t84 = r1 <= f.p.dens_threshold
  t85 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t86 = 0.1e1 + t85
  t87 = t86 <= f.p.zeta_threshold
  t88 = t86 ** (0.1e1 / 0.3e1)
  t90 = f.my_piecewise3(t87, t22, t88 * t86)
  t91 = t90 * t26
  t92 = r1 ** 2
  t93 = r1 ** (0.1e1 / 0.3e1)
  t94 = t93 ** 2
  t96 = 0.1e1 / t94 / t92
  t102 = 0.1e1 + t41 * t33 * s2 * t96 / 0.24e2
  t103 = 0.1e1 / t102
  t107 = s2 ** 2
  t108 = t92 ** 2
  t111 = 0.1e1 / t93 / t108 / r1
  t113 = t102 ** 2
  t114 = 0.1e1 / t113
  t118 = t107 * s2
  t119 = t108 ** 2
  t120 = 0.1e1 / t119
  t123 = 0.1e1 / t113 / t102
  t127 = 0.1e1 + t34 * s2 * t96 * t103 / 0.24e2 + t55 * t107 * t111 * t114 / 0.576e3 + t69 * t118 * t120 * t123 / 0.2304e4
  t131 = f.my_piecewise3(t84, 0, -0.3e1 / 0.8e1 * t5 * t91 * t127)
  t132 = t6 ** 2
  t134 = t16 / t132
  t135 = t7 - t134
  t136 = f.my_piecewise5(t10, 0, t14, 0, t135)
  t139 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t136)
  t144 = t26 ** 2
  t145 = 0.1e1 / t144
  t149 = t5 * t25 * t145 * t79 / 0.8e1
  t150 = t35 * r0
  t158 = params.c1 * t51 * t54
  t162 = t56 / t36 / t57 / t35
  t163 = t63 * params.a
  t170 = params.c2 * t68
  t173 = 0.1e1 / t71 / r0
  t182 = t56 ** 2
  t188 = t62 ** 2
  t191 = t28 * t33
  t192 = 0.1e1 / t188 * params.a * t191
  t200 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t139 * t26 * t79 - t149 - 0.3e1 / 0.8e1 * t5 * t27 * (-t34 * s0 / t37 / t150 * t47 / 0.9e1 + t158 * t162 * t163 / 0.216e3 - t55 * t162 * t63 / 0.108e3 + t170 * t70 * t173 * t75 * params.a / 0.432e3 - t69 * t70 * t173 * t75 / 0.288e3 + t69 * t182 / t37 / t71 / t150 * t192 / 0.6912e4))
  t202 = f.my_piecewise5(t14, 0, t10, 0, -t135)
  t205 = f.my_piecewise3(t87, 0, 0.4e1 / 0.3e1 * t88 * t202)
  t213 = t5 * t90 * t145 * t127 / 0.8e1
  t215 = f.my_piecewise3(t84, 0, -0.3e1 / 0.8e1 * t5 * t205 * t26 * t127 - t213)
  vrho_0_ = t83 + t131 + t6 * (t200 + t215)
  t218 = -t7 - t134
  t219 = f.my_piecewise5(t10, 0, t14, 0, t218)
  t222 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t219)
  t228 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t222 * t26 * t79 - t149)
  t230 = f.my_piecewise5(t14, 0, t10, 0, -t218)
  t233 = f.my_piecewise3(t87, 0, 0.4e1 / 0.3e1 * t88 * t230)
  t238 = t92 * r1
  t248 = t107 / t93 / t108 / t92
  t249 = t114 * params.a
  t258 = 0.1e1 / t119 / r1
  t267 = t107 ** 2
  t273 = t113 ** 2
  t276 = 0.1e1 / t273 * params.a * t191
  t284 = f.my_piecewise3(t84, 0, -0.3e1 / 0.8e1 * t5 * t233 * t26 * t127 - t213 - 0.3e1 / 0.8e1 * t5 * t91 * (-t34 * s2 / t94 / t238 * t103 / 0.9e1 + t158 * t248 * t249 / 0.216e3 - t55 * t248 * t114 / 0.108e3 + t170 * t118 * t258 * t123 * params.a / 0.432e3 - t69 * t118 * t258 * t123 / 0.288e3 + t69 * t267 / t94 / t119 / t238 * t276 / 0.6912e4))
  vrho_1_ = t83 + t131 + t6 * (t228 + t284)
  t291 = s0 * t60
  t318 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t29 * t33 * t39 * t47 / 0.24e2 - t158 * t291 * t163 / 0.576e3 + t55 * t291 * t63 / 0.288e3 - t170 * t56 * t72 * t75 * params.a / 0.1152e4 + t69 * t56 * t72 * t75 / 0.768e3 - t69 * t70 / t37 / t71 / t35 * t192 / 0.18432e5))
  vsigma_0_ = t6 * t318
  vsigma_1_ = 0.0e0
  t323 = s2 * t111
  t350 = f.my_piecewise3(t84, 0, -0.3e1 / 0.8e1 * t5 * t91 * (t29 * t33 * t96 * t103 / 0.24e2 - t158 * t323 * t249 / 0.576e3 + t55 * t323 * t114 / 0.288e3 - t170 * t107 * t120 * t123 * params.a / 0.1152e4 + t69 * t107 * t120 * t123 / 0.768e3 - t69 * t118 / t94 / t119 / t92 * t276 / 0.18432e5))
  vsigma_2_ = t6 * t350
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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, mpbe_f, rs, z, xs0, xs1)

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
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t26 = params.c1 * t20 * t25
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = s0 * t28
  t30 = r0 ** 2
  t31 = t18 ** 2
  t33 = 0.1e1 / t31 / t30
  t39 = 0.1e1 + params.a * t20 * t25 * t29 * t33 / 0.24e2
  t40 = 0.1e1 / t39
  t45 = t20 ** 2
  t48 = 0.1e1 / t23 / t22
  t49 = params.c2 * t45 * t48
  t50 = s0 ** 2
  t51 = t50 * t27
  t52 = t30 ** 2
  t55 = 0.1e1 / t18 / t52 / r0
  t56 = t39 ** 2
  t57 = 0.1e1 / t56
  t58 = t55 * t57
  t62 = t22 ** 2
  t63 = 0.1e1 / t62
  t64 = params.c3 * t63
  t65 = t50 * s0
  t66 = t52 ** 2
  t67 = 0.1e1 / t66
  t70 = 0.1e1 / t56 / t39
  t74 = 0.1e1 + t26 * t29 * t33 * t40 / 0.24e2 + t49 * t51 * t58 / 0.288e3 + t64 * t65 * t67 * t70 / 0.576e3
  t78 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t74)
  t84 = t30 * r0
  t91 = params.c1 * t45
  t96 = 0.1e1 / t18 / t52 / t30
  t98 = t57 * params.a
  t106 = params.c2 * t63
  t109 = 0.1e1 / t66 / r0
  t118 = t50 ** 2
  t124 = t56 ** 2
  t129 = 0.1e1 / t124 * params.a * t20 * t25 * t28
  t137 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t74 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t26 * t29 / t31 / t84 * t40 / 0.9e1 + t91 * t48 * t50 * t27 * t96 * t98 / 0.108e3 - t49 * t51 * t96 * t57 / 0.54e2 + t106 * t65 * t109 * t70 * params.a / 0.108e3 - t64 * t65 * t109 * t70 / 0.72e2 + t64 * t118 / t31 / t66 / t84 * t129 / 0.1728e4))
  vrho_0_ = 0.2e1 * r0 * t137 + 0.2e1 * t78
  t174 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t26 * t28 * t33 * t40 / 0.24e2 - t91 * t48 * s0 * t27 * t55 * t98 / 0.288e3 + t49 * s0 * t27 * t58 / 0.144e3 - t106 * t50 * t67 * t70 * params.a / 0.288e3 + t64 * t50 * t67 * t70 / 0.192e3 - t64 * t65 / t31 / t66 / t30 * t129 / 0.4608e4))
  vsigma_0_ = 0.2e1 * r0 * t174
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
  t22 = 6 ** (0.1e1 / 0.3e1)
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = params.c1 * t22 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t40 = 0.1e1 + params.a * t22 * t27 * t31 * t34 / 0.24e2
  t41 = 0.1e1 / t40
  t46 = t22 ** 2
  t49 = 0.1e1 / t25 / t24
  t50 = params.c2 * t46 * t49
  t51 = s0 ** 2
  t52 = t51 * t29
  t53 = t32 ** 2
  t54 = t53 * r0
  t56 = 0.1e1 / t18 / t54
  t57 = t40 ** 2
  t58 = 0.1e1 / t57
  t59 = t56 * t58
  t63 = t24 ** 2
  t64 = 0.1e1 / t63
  t65 = params.c3 * t64
  t66 = t51 * s0
  t67 = t53 ** 2
  t68 = 0.1e1 / t67
  t71 = 0.1e1 / t57 / t40
  t75 = 0.1e1 + t28 * t31 * t34 * t41 / 0.24e2 + t50 * t52 * t59 / 0.288e3 + t65 * t66 * t68 * t71 / 0.576e3
  t79 = t17 * t18
  t80 = t32 * r0
  t82 = 0.1e1 / t19 / t80
  t87 = params.c1 * t46
  t89 = t87 * t49 * t51
  t90 = t53 * t32
  t92 = 0.1e1 / t18 / t90
  t94 = t58 * params.a
  t98 = t92 * t58
  t102 = params.c2 * t64
  t103 = t102 * t66
  t105 = 0.1e1 / t67 / r0
  t106 = t105 * t71
  t107 = t106 * params.a
  t114 = t51 ** 2
  t117 = 0.1e1 / t19 / t67 / t80
  t120 = t57 ** 2
  t121 = 0.1e1 / t120
  t124 = t22 * t27 * t30
  t125 = t121 * params.a * t124
  t128 = -t28 * t31 * t82 * t41 / 0.9e1 + t89 * t29 * t92 * t94 / 0.108e3 - t50 * t52 * t98 / 0.54e2 + t103 * t107 / 0.108e3 - t65 * t66 * t105 * t71 / 0.72e2 + t65 * t114 * t117 * t125 / 0.1728e4
  t133 = f.my_piecewise3(t2, 0, -t6 * t21 * t75 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t79 * t128)
  t150 = t53 * t80
  t152 = 0.1e1 / t18 / t150
  t157 = params.c1 * t64
  t159 = t67 * t32
  t160 = 0.1e1 / t159
  t161 = t160 * t71
  t162 = params.a ** 2
  t176 = t114 / t19 / t67 / t53
  t179 = t121 * t162 * t124
  t200 = 0.1e1 / t120 / t40 * t162 * t46 * t49 * t29
  t208 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t75 / 0.12e2 - t6 * t21 * t128 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t79 * (0.11e2 / 0.27e2 * t28 * t31 / t19 / t53 * t41 - t89 * t29 * t152 * t94 / 0.12e2 + 0.2e1 / 0.81e2 * t157 * t66 * t161 * t162 + 0.19e2 / 0.162e3 * t50 * t52 * t152 * t58 - 0.43e2 / 0.324e3 * t103 * t161 * params.a + t102 * t176 * t179 / 0.324e3 + t65 * t66 * t160 * t71 / 0.8e1 - 0.59e2 / 0.5184e4 * t65 * t176 * t125 + t65 * t114 * s0 / t18 / t67 / t150 * t200 / 0.1944e4))
  v2rho2_0_ = 0.2e1 * r0 * t208 + 0.4e1 * t133
  t217 = t29 * t56
  t218 = t217 * t94
  t221 = s0 * t29
  t225 = t102 * t51
  t226 = t68 * t71
  t227 = t226 * params.a
  t235 = 0.1e1 / t19 / t159
  t240 = t28 * t30 * t34 * t41 / 0.24e2 - t87 * t49 * s0 * t218 / 0.288e3 + t50 * t221 * t59 / 0.144e3 - t225 * t227 / 0.288e3 + t65 * t51 * t68 * t71 / 0.192e3 - t65 * t66 * t235 * t125 / 0.4608e4
  t244 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t79 * t240)
  t267 = t66 * t117
  t290 = f.my_piecewise3(t2, 0, -t6 * t21 * t240 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t79 * (-t28 * t30 * t82 * t41 / 0.9e1 + t87 * t49 * t29 * t98 * params.a * s0 / 0.36e2 - t157 * t51 * t106 * t162 / 0.108e3 - t50 * t221 * t98 / 0.27e2 + 0.5e1 / 0.108e3 * t225 * t107 - t102 * t267 * t179 / 0.864e3 - t65 * t51 * t105 * t71 / 0.24e2 + 0.7e1 / 0.1728e4 * t65 * t267 * t125 - t65 * t114 / t18 / t67 / t90 * t200 / 0.5184e4))
  v2rhosigma_0_ = 0.2e1 * r0 * t290 + 0.2e1 * t244
  t306 = t51 * t235
  t328 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t79 * (-t87 * t49 * t218 / 0.144e3 + t157 * s0 * t226 * t162 / 0.288e3 + t50 * t217 * t58 / 0.144e3 - t102 * s0 * t227 / 0.72e2 + t102 * t306 * t179 / 0.2304e4 + t65 * s0 * t68 * t71 / 0.96e2 - t65 * t306 * t125 / 0.768e3 + t65 * t66 / t18 / t67 / t54 * t200 / 0.13824e5))
  v2sigma2_0_ = 0.2e1 * r0 * t328
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
  t23 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = params.c1 * t23 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t41 = 0.1e1 + params.a * t23 * t28 * t32 * t35 / 0.24e2
  t42 = 0.1e1 / t41
  t47 = t23 ** 2
  t50 = 0.1e1 / t26 / t25
  t51 = params.c2 * t47 * t50
  t52 = s0 ** 2
  t53 = t52 * t30
  t54 = t33 ** 2
  t55 = t54 * r0
  t58 = t41 ** 2
  t59 = 0.1e1 / t58
  t64 = t25 ** 2
  t65 = 0.1e1 / t64
  t66 = params.c3 * t65
  t67 = t52 * s0
  t68 = t54 ** 2
  t72 = 0.1e1 / t58 / t41
  t76 = 0.1e1 + t29 * t32 * t35 * t42 / 0.24e2 + t51 * t53 / t18 / t55 * t59 / 0.288e3 + t66 * t67 / t68 * t72 / 0.576e3
  t81 = t17 / t19
  t82 = t33 * r0
  t91 = params.c1 * t47 * t50 * t52
  t94 = 0.1e1 / t18 / t54 / t33
  t96 = t59 * params.a
  t104 = params.c2 * t65
  t105 = t104 * t67
  t107 = 0.1e1 / t68 / r0
  t116 = t52 ** 2
  t117 = t68 * t82
  t122 = t58 ** 2
  t123 = 0.1e1 / t122
  t126 = t23 * t28 * t31
  t127 = t123 * params.a * t126
  t130 = -t29 * t32 / t19 / t82 * t42 / 0.9e1 + t91 * t30 * t94 * t96 / 0.108e3 - t51 * t53 * t94 * t59 / 0.54e2 + t105 * t107 * t72 * params.a / 0.108e3 - t66 * t67 * t107 * t72 / 0.72e2 + t66 * t116 / t19 / t117 * t127 / 0.1728e4
  t134 = t17 * t18
  t141 = t54 * t82
  t143 = 0.1e1 / t18 / t141
  t148 = params.c1 * t65
  t149 = t148 * t67
  t151 = 0.1e1 / t68 / t33
  t152 = t151 * t72
  t153 = params.a ** 2
  t167 = t116 / t19 / t68 / t54
  t170 = t123 * t153 * t126
  t180 = t116 * s0
  t187 = 0.1e1 / t122 / t41
  t190 = t47 * t50 * t30
  t191 = t187 * t153 * t190
  t194 = 0.11e2 / 0.27e2 * t29 * t32 / t19 / t54 * t42 - t91 * t30 * t143 * t96 / 0.12e2 + 0.2e1 / 0.81e2 * t149 * t152 * t153 + 0.19e2 / 0.162e3 * t51 * t53 * t143 * t59 - 0.43e2 / 0.324e3 * t105 * t152 * params.a + t104 * t167 * t170 / 0.324e3 + t66 * t67 * t151 * t72 / 0.8e1 - 0.59e2 / 0.5184e4 * t66 * t167 * t127 + t66 * t180 / t18 / t68 / t141 * t191 / 0.1944e4
  t199 = f.my_piecewise3(t2, 0, t6 * t22 * t76 / 0.12e2 - t6 * t81 * t130 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t134 * t194)
  t218 = 0.1e1 / t18 / t68
  t223 = 0.1e1 / t117
  t224 = t223 * t72
  t231 = t116 / t19 / t68 / t55
  t233 = t153 * params.a
  t248 = t68 ** 2
  t251 = t180 / t18 / t248
  t267 = t64 ** 2
  t280 = -0.154e3 / 0.81e2 * t29 * t32 / t19 / t55 * t42 + 0.341e3 / 0.486e3 * t91 * t30 * t218 * t96 - 0.38e2 / 0.81e2 * t149 * t224 * t153 + 0.2e1 / 0.243e3 * t148 * t231 * t123 * t233 * t126 - 0.209e3 / 0.243e3 * t51 * t53 * t218 * t59 + 0.797e3 / 0.486e3 * t105 * t224 * params.a - t104 * t231 * t170 / 0.12e2 + 0.2e1 / 0.729e3 * t104 * t251 * t187 * t233 * t190 - 0.5e1 / 0.4e1 * t66 * t67 * t223 * t72 + 0.1445e4 / 0.7776e4 * t66 * t231 * t127 - 0.35e2 / 0.1944e4 * t66 * t251 * t191 + 0.5e1 / 0.1458e4 * params.c3 / t267 * t116 * t52 / t248 / t82 / t122 / t58 * t233
  t285 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t76 + t6 * t22 * t130 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t81 * t194 - 0.3e1 / 0.8e1 * t6 * t134 * t280)
  v3rho3_0_ = 0.2e1 * r0 * t285 + 0.6e1 * t199

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
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = params.c1 * t24 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t39 = 0.1e1 + params.a * t24 * t29 * t33 * t22 / 0.24e2
  t40 = 0.1e1 / t39
  t45 = t24 ** 2
  t48 = 0.1e1 / t27 / t26
  t49 = params.c2 * t45 * t48
  t50 = s0 ** 2
  t51 = t50 * t31
  t52 = t18 ** 2
  t53 = t52 * r0
  t56 = t39 ** 2
  t57 = 0.1e1 / t56
  t62 = t26 ** 2
  t63 = 0.1e1 / t62
  t64 = params.c3 * t63
  t65 = t50 * s0
  t66 = t52 ** 2
  t69 = t56 * t39
  t70 = 0.1e1 / t69
  t74 = 0.1e1 + t30 * t33 * t22 * t40 / 0.24e2 + t49 * t51 / t19 / t53 * t57 / 0.288e3 + t64 * t65 / t66 * t70 / 0.576e3
  t80 = t17 / t20 / r0
  t81 = t18 * r0
  t83 = 0.1e1 / t20 / t81
  t90 = params.c1 * t45 * t48 * t50
  t91 = t52 * t18
  t93 = 0.1e1 / t19 / t91
  t95 = t57 * params.a
  t103 = params.c2 * t63
  t104 = t103 * t65
  t105 = t66 * r0
  t106 = 0.1e1 / t105
  t115 = t50 ** 2
  t116 = t66 * t81
  t121 = t56 ** 2
  t122 = 0.1e1 / t121
  t125 = t24 * t29 * t32
  t126 = t122 * params.a * t125
  t129 = -t30 * t33 * t83 * t40 / 0.9e1 + t90 * t31 * t93 * t95 / 0.108e3 - t49 * t51 * t93 * t57 / 0.54e2 + t104 * t106 * t70 * params.a / 0.108e3 - t64 * t65 * t106 * t70 / 0.72e2 + t64 * t115 / t20 / t116 * t126 / 0.1728e4
  t134 = t17 / t20
  t141 = t52 * t81
  t143 = 0.1e1 / t19 / t141
  t148 = params.c1 * t63
  t149 = t148 * t65
  t151 = 0.1e1 / t66 / t18
  t152 = t151 * t70
  t153 = params.a ** 2
  t164 = t66 * t52
  t167 = t115 / t20 / t164
  t170 = t122 * t153 * t125
  t180 = t115 * s0
  t187 = 0.1e1 / t121 / t39
  t190 = t45 * t48 * t31
  t191 = t187 * t153 * t190
  t194 = 0.11e2 / 0.27e2 * t30 * t33 / t20 / t52 * t40 - t90 * t31 * t143 * t95 / 0.12e2 + 0.2e1 / 0.81e2 * t149 * t152 * t153 + 0.19e2 / 0.162e3 * t49 * t51 * t143 * t57 - 0.43e2 / 0.324e3 * t104 * t152 * params.a + t103 * t167 * t170 / 0.324e3 + t64 * t65 * t151 * t70 / 0.8e1 - 0.59e2 / 0.5184e4 * t64 * t167 * t126 + t64 * t180 / t19 / t66 / t141 * t191 / 0.1944e4
  t198 = t17 * t19
  t206 = 0.1e1 / t19 / t66
  t211 = 0.1e1 / t116
  t212 = t211 * t70
  t219 = t115 / t20 / t66 / t53
  t221 = t153 * params.a
  t223 = t122 * t221 * t125
  t236 = t66 ** 2
  t239 = t180 / t19 / t236
  t242 = t187 * t221 * t190
  t255 = t62 ** 2
  t256 = 0.1e1 / t255
  t257 = params.c3 * t256
  t258 = t115 * t50
  t259 = t257 * t258
  t263 = 0.1e1 / t121 / t56
  t268 = -0.154e3 / 0.81e2 * t30 * t33 / t20 / t53 * t40 + 0.341e3 / 0.486e3 * t90 * t31 * t206 * t95 - 0.38e2 / 0.81e2 * t149 * t212 * t153 + 0.2e1 / 0.243e3 * t148 * t219 * t223 - 0.209e3 / 0.243e3 * t49 * t51 * t206 * t57 + 0.797e3 / 0.486e3 * t104 * t212 * params.a - t103 * t219 * t170 / 0.12e2 + 0.2e1 / 0.729e3 * t103 * t239 * t242 - 0.5e1 / 0.4e1 * t64 * t65 * t211 * t70 + 0.1445e4 / 0.7776e4 * t64 * t219 * t126 - 0.35e2 / 0.1944e4 * t64 * t239 * t191 + 0.5e1 / 0.1458e4 * t259 / t236 / t81 * t263 * t221
  t273 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t74 + t6 * t80 * t129 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t134 * t194 - 0.3e1 / 0.8e1 * t6 * t198 * t268)
  t295 = 0.1e1 / t19 / t105
  t300 = 0.1e1 / t164
  t301 = t300 * t70
  t308 = t115 / t20 / t66 / t91
  t315 = t180 / t19 / t236 / r0
  t317 = t153 ** 2
  t339 = 0.1e1 / t236 / t52 * t263
  t368 = 0.2618e4 / 0.243e3 * t30 * t33 / t20 / t91 * t40 - 0.3047e4 / 0.486e3 * t90 * t31 * t295 * t95 + 0.5126e4 / 0.729e3 * t149 * t301 * t153 - 0.196e3 / 0.729e3 * t148 * t308 * t223 + 0.16e2 / 0.2187e4 * t148 * t315 * t187 * t317 * t190 + 0.5225e4 / 0.729e3 * t49 * t51 * t295 * t57 - 0.29645e5 / 0.1458e4 * t104 * t301 * params.a + 0.4915e4 / 0.2916e4 * t103 * t308 * t170 - 0.260e3 / 0.2187e4 * t103 * t315 * t242 + 0.40e2 / 0.2187e4 * params.c2 * t256 * t258 * t339 * t317 + 0.55e2 / 0.4e1 * t64 * t65 * t300 * t70 - 0.68965e5 / 0.23328e5 * t64 * t308 * t126 + 0.8035e4 / 0.17496e5 * t64 * t315 * t191 - 0.5e1 / 0.27e2 * t259 * t339 * t221 + 0.5e1 / 0.2187e4 * t257 * t115 * t65 / t20 / t236 / t91 / t121 / t69 * t317 * t125
  t373 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t83 * t74 - 0.5e1 / 0.9e1 * t6 * t23 * t129 + t6 * t80 * t194 / 0.2e1 - t6 * t134 * t268 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t198 * t368)
  v4rho4_0_ = 0.2e1 * r0 * t373 + 0.8e1 * t273

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
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = params.c1 * t32 * t37
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
  t66 = t50 ** 2
  t67 = 0.1e1 / t66
  t71 = t34 ** 2
  t72 = 0.1e1 / t71
  t73 = params.c3 * t72
  t74 = t60 * s0
  t75 = t61 ** 2
  t79 = 0.1e1 / t66 / t50
  t83 = 0.1e1 + t38 * s0 * t43 * t51 / 0.24e2 + t59 * t60 / t40 / t61 / r0 * t67 / 0.576e3 + t73 * t74 / t75 * t79 / 0.2304e4
  t87 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t88 = t87 * f.p.zeta_threshold
  t90 = f.my_piecewise3(t20, t88, t21 * t19)
  t91 = t30 ** 2
  t92 = 0.1e1 / t91
  t93 = t90 * t92
  t96 = t5 * t93 * t83 / 0.8e1
  t97 = t90 * t30
  t98 = t39 * r0
  t106 = params.c1 * t55 * t58
  t110 = t60 / t40 / t61 / t39
  t111 = t67 * params.a
  t118 = params.c2 * t72
  t119 = t118 * t74
  t121 = 0.1e1 / t75 / r0
  t130 = t60 ** 2
  t136 = t66 ** 2
  t137 = 0.1e1 / t136
  t139 = t32 * t37
  t140 = t137 * params.a * t139
  t143 = -t38 * s0 / t41 / t98 * t51 / 0.9e1 + t106 * t110 * t111 / 0.216e3 - t59 * t110 * t67 / 0.108e3 + t119 * t121 * t79 * params.a / 0.432e3 - t73 * t74 * t121 * t79 / 0.288e3 + t73 * t130 / t41 / t75 / t98 * t140 / 0.6912e4
  t148 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t83 - t96 - 0.3e1 / 0.8e1 * t5 * t97 * t143)
  t150 = r1 <= f.p.dens_threshold
  t151 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t152 = 0.1e1 + t151
  t153 = t152 <= f.p.zeta_threshold
  t154 = t152 ** (0.1e1 / 0.3e1)
  t156 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t159 = f.my_piecewise3(t153, 0, 0.4e1 / 0.3e1 * t154 * t156)
  t160 = t159 * t30
  t161 = r1 ** 2
  t162 = r1 ** (0.1e1 / 0.3e1)
  t163 = t162 ** 2
  t165 = 0.1e1 / t163 / t161
  t171 = 0.1e1 + t45 * t37 * s2 * t165 / 0.24e2
  t172 = 0.1e1 / t171
  t176 = s2 ** 2
  t177 = t161 ** 2
  t182 = t171 ** 2
  t183 = 0.1e1 / t182
  t187 = t176 * s2
  t188 = t177 ** 2
  t192 = 0.1e1 / t182 / t171
  t196 = 0.1e1 + t38 * s2 * t165 * t172 / 0.24e2 + t59 * t176 / t162 / t177 / r1 * t183 / 0.576e3 + t73 * t187 / t188 * t192 / 0.2304e4
  t201 = f.my_piecewise3(t153, t88, t154 * t152)
  t202 = t201 * t92
  t205 = t5 * t202 * t196 / 0.8e1
  t207 = f.my_piecewise3(t150, 0, -0.3e1 / 0.8e1 * t5 * t160 * t196 - t205)
  t209 = t21 ** 2
  t210 = 0.1e1 / t209
  t211 = t26 ** 2
  t216 = t16 / t22 / t6
  t218 = -0.2e1 * t23 + 0.2e1 * t216
  t219 = f.my_piecewise5(t10, 0, t14, 0, t218)
  t223 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t210 * t211 + 0.4e1 / 0.3e1 * t21 * t219)
  t230 = t5 * t29 * t92 * t83
  t236 = 0.1e1 / t91 / t6
  t240 = t5 * t90 * t236 * t83 / 0.12e2
  t242 = t5 * t93 * t143
  t250 = t61 * t98
  t253 = t60 / t40 / t250
  t257 = params.c1 * t72
  t260 = 0.1e1 / t75 / t39
  t261 = t260 * t79
  t262 = params.a ** 2
  t275 = t130 / t41 / t75 / t61
  t297 = t55 * t58
  t306 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t223 * t30 * t83 - t230 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t143 + t240 - t242 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t97 * (0.11e2 / 0.27e2 * t38 * s0 / t41 / t61 * t51 - t106 * t253 * t111 / 0.24e2 + t257 * t74 * t261 * t262 / 0.162e3 + 0.19e2 / 0.324e3 * t59 * t253 * t67 - 0.43e2 / 0.1296e4 * t119 * t261 * params.a + t118 * t275 * t137 * t262 * t139 / 0.1296e4 + t73 * t74 * t260 * t79 / 0.32e2 - 0.59e2 / 0.20736e5 * t73 * t275 * t140 + t73 * t130 * s0 / t40 / t75 / t250 / t136 / t50 * t262 * t297 / 0.15552e5))
  t307 = t154 ** 2
  t308 = 0.1e1 / t307
  t309 = t156 ** 2
  t313 = f.my_piecewise5(t14, 0, t10, 0, -t218)
  t317 = f.my_piecewise3(t153, 0, 0.4e1 / 0.9e1 * t308 * t309 + 0.4e1 / 0.3e1 * t154 * t313)
  t324 = t5 * t159 * t92 * t196
  t329 = t5 * t201 * t236 * t196 / 0.12e2
  t331 = f.my_piecewise3(t150, 0, -0.3e1 / 0.8e1 * t5 * t317 * t30 * t196 - t324 / 0.4e1 + t329)
  d11 = 0.2e1 * t148 + 0.2e1 * t207 + t6 * (t306 + t331)
  t334 = -t7 - t24
  t335 = f.my_piecewise5(t10, 0, t14, 0, t334)
  t338 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t335)
  t339 = t338 * t30
  t344 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t339 * t83 - t96)
  t346 = f.my_piecewise5(t14, 0, t10, 0, -t334)
  t349 = f.my_piecewise3(t153, 0, 0.4e1 / 0.3e1 * t154 * t346)
  t350 = t349 * t30
  t354 = t201 * t30
  t355 = t161 * r1
  t365 = t176 / t162 / t177 / t161
  t366 = t183 * params.a
  t373 = t118 * t187
  t375 = 0.1e1 / t188 / r1
  t384 = t176 ** 2
  t390 = t182 ** 2
  t391 = 0.1e1 / t390
  t393 = t391 * params.a * t139
  t396 = -t38 * s2 / t163 / t355 * t172 / 0.9e1 + t106 * t365 * t366 / 0.216e3 - t59 * t365 * t183 / 0.108e3 + t373 * t375 * t192 * params.a / 0.432e3 - t73 * t187 * t375 * t192 / 0.288e3 + t73 * t384 / t163 / t188 / t355 * t393 / 0.6912e4
  t401 = f.my_piecewise3(t150, 0, -0.3e1 / 0.8e1 * t5 * t350 * t196 - t205 - 0.3e1 / 0.8e1 * t5 * t354 * t396)
  t405 = 0.2e1 * t216
  t406 = f.my_piecewise5(t10, 0, t14, 0, t405)
  t410 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t210 * t335 * t26 + 0.4e1 / 0.3e1 * t21 * t406)
  t417 = t5 * t338 * t92 * t83
  t425 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t410 * t30 * t83 - t417 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t339 * t143 - t230 / 0.8e1 + t240 - t242 / 0.8e1)
  t429 = f.my_piecewise5(t14, 0, t10, 0, -t405)
  t433 = f.my_piecewise3(t153, 0, 0.4e1 / 0.9e1 * t308 * t346 * t156 + 0.4e1 / 0.3e1 * t154 * t429)
  t440 = t5 * t349 * t92 * t196
  t447 = t5 * t202 * t396
  t450 = f.my_piecewise3(t150, 0, -0.3e1 / 0.8e1 * t5 * t433 * t30 * t196 - t440 / 0.8e1 - t324 / 0.8e1 + t329 - 0.3e1 / 0.8e1 * t5 * t160 * t396 - t447 / 0.8e1)
  d12 = t148 + t207 + t344 + t401 + t6 * (t425 + t450)
  t455 = t335 ** 2
  t459 = 0.2e1 * t23 + 0.2e1 * t216
  t460 = f.my_piecewise5(t10, 0, t14, 0, t459)
  t464 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t210 * t455 + 0.4e1 / 0.3e1 * t21 * t460)
  t471 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t464 * t30 * t83 - t417 / 0.4e1 + t240)
  t472 = t346 ** 2
  t476 = f.my_piecewise5(t14, 0, t10, 0, -t459)
  t480 = f.my_piecewise3(t153, 0, 0.4e1 / 0.9e1 * t308 * t472 + 0.4e1 / 0.3e1 * t154 * t476)
  t496 = t177 * t355
  t499 = t176 / t162 / t496
  t505 = 0.1e1 / t188 / t161
  t506 = t505 * t192
  t519 = t384 / t163 / t188 / t177
  t549 = f.my_piecewise3(t150, 0, -0.3e1 / 0.8e1 * t5 * t480 * t30 * t196 - t440 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t350 * t396 + t329 - t447 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t354 * (0.11e2 / 0.27e2 * t38 * s2 / t163 / t177 * t172 - t106 * t499 * t366 / 0.24e2 + t257 * t187 * t506 * t262 / 0.162e3 + 0.19e2 / 0.324e3 * t59 * t499 * t183 - 0.43e2 / 0.1296e4 * t373 * t506 * params.a + t118 * t519 * t391 * t262 * t139 / 0.1296e4 + t73 * t187 * t505 * t192 / 0.32e2 - 0.59e2 / 0.20736e5 * t73 * t519 * t393 + t73 * t384 * s2 / t162 / t188 / t496 / t390 / t171 * t262 * t297 / 0.15552e5))
  d22 = 0.2e1 * t344 + 0.2e1 * t401 + t6 * (t471 + t549)
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
  t44 = 6 ** (0.1e1 / 0.3e1)
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t50 = params.c1 * t44 * t49
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t55 = 0.1e1 / t53 / t51
  t57 = params.a * t44
  t62 = 0.1e1 + t57 * t49 * s0 * t55 / 0.24e2
  t63 = 0.1e1 / t62
  t67 = t44 ** 2
  t70 = 0.1e1 / t47 / t46
  t71 = params.c2 * t67 * t70
  t72 = s0 ** 2
  t73 = t51 ** 2
  t74 = t73 * r0
  t78 = t62 ** 2
  t79 = 0.1e1 / t78
  t83 = t46 ** 2
  t84 = 0.1e1 / t83
  t85 = params.c3 * t84
  t86 = t72 * s0
  t87 = t73 ** 2
  t91 = 0.1e1 / t78 / t62
  t95 = 0.1e1 + t50 * s0 * t55 * t63 / 0.24e2 + t71 * t72 / t52 / t74 * t79 / 0.576e3 + t85 * t86 / t87 * t91 / 0.2304e4
  t101 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t102 = t42 ** 2
  t103 = 0.1e1 / t102
  t104 = t101 * t103
  t108 = t101 * t42
  t109 = t51 * r0
  t117 = params.c1 * t67 * t70
  t121 = t72 / t52 / t73 / t51
  t122 = t79 * params.a
  t129 = params.c2 * t84
  t130 = t129 * t86
  t132 = 0.1e1 / t87 / r0
  t141 = t72 ** 2
  t142 = t87 * t109
  t147 = t78 ** 2
  t148 = 0.1e1 / t147
  t150 = t44 * t49
  t151 = t148 * params.a * t150
  t154 = -t50 * s0 / t53 / t109 * t63 / 0.9e1 + t117 * t121 * t122 / 0.216e3 - t71 * t121 * t79 / 0.108e3 + t130 * t132 * t91 * params.a / 0.432e3 - t85 * t86 * t132 * t91 / 0.288e3 + t85 * t141 / t53 / t142 * t151 / 0.6912e4
  t158 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t159 = t158 * f.p.zeta_threshold
  t161 = f.my_piecewise3(t20, t159, t21 * t19)
  t163 = 0.1e1 / t102 / t6
  t164 = t161 * t163
  t168 = t161 * t103
  t172 = t161 * t42
  t179 = t73 * t109
  t182 = t72 / t52 / t179
  t186 = params.c1 * t84
  t187 = t186 * t86
  t189 = 0.1e1 / t87 / t51
  t190 = t189 * t91
  t191 = params.a ** 2
  t204 = t141 / t53 / t87 / t73
  t207 = t148 * t191 * t150
  t217 = t141 * s0
  t224 = 0.1e1 / t147 / t62
  t226 = t67 * t70
  t227 = t224 * t191 * t226
  t230 = 0.11e2 / 0.27e2 * t50 * s0 / t53 / t73 * t63 - t117 * t182 * t122 / 0.24e2 + t187 * t190 * t191 / 0.162e3 + 0.19e2 / 0.324e3 * t71 * t182 * t79 - 0.43e2 / 0.1296e4 * t130 * t190 * params.a + t129 * t204 * t207 / 0.1296e4 + t85 * t86 * t189 * t91 / 0.32e2 - 0.59e2 / 0.20736e5 * t85 * t204 * t151 + t85 * t217 / t52 / t87 / t179 * t227 / 0.15552e5
  t235 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t95 - t5 * t104 * t95 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t108 * t154 + t5 * t164 * t95 / 0.12e2 - t5 * t168 * t154 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t172 * t230)
  t237 = r1 <= f.p.dens_threshold
  t238 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t239 = 0.1e1 + t238
  t240 = t239 <= f.p.zeta_threshold
  t241 = t239 ** (0.1e1 / 0.3e1)
  t242 = t241 ** 2
  t243 = 0.1e1 / t242
  t245 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t246 = t245 ** 2
  t250 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t254 = f.my_piecewise3(t240, 0, 0.4e1 / 0.9e1 * t243 * t246 + 0.4e1 / 0.3e1 * t241 * t250)
  t256 = r1 ** 2
  t257 = r1 ** (0.1e1 / 0.3e1)
  t258 = t257 ** 2
  t260 = 0.1e1 / t258 / t256
  t266 = 0.1e1 + t57 * t49 * s2 * t260 / 0.24e2
  t271 = s2 ** 2
  t272 = t256 ** 2
  t277 = t266 ** 2
  t283 = t272 ** 2
  t291 = 0.1e1 + t50 * s2 * t260 / t266 / 0.24e2 + t71 * t271 / t257 / t272 / r1 / t277 / 0.576e3 + t85 * t271 * s2 / t283 / t277 / t266 / 0.2304e4
  t297 = f.my_piecewise3(t240, 0, 0.4e1 / 0.3e1 * t241 * t245)
  t303 = f.my_piecewise3(t240, t159, t241 * t239)
  t309 = f.my_piecewise3(t237, 0, -0.3e1 / 0.8e1 * t5 * t254 * t42 * t291 - t5 * t297 * t103 * t291 / 0.4e1 + t5 * t303 * t163 * t291 / 0.12e2)
  t319 = t24 ** 2
  t323 = 0.6e1 * t33 - 0.6e1 * t16 / t319
  t324 = f.my_piecewise5(t10, 0, t14, 0, t323)
  t328 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t324)
  t351 = 0.1e1 / t102 / t24
  t370 = t72 / t52 / t87
  t374 = 0.1e1 / t142
  t375 = t374 * t91
  t382 = t141 / t53 / t87 / t74
  t384 = t191 * params.a
  t398 = t87 ** 2
  t401 = t217 / t52 / t398
  t417 = t83 ** 2
  t430 = -0.154e3 / 0.81e2 * t50 * s0 / t53 / t74 * t63 + 0.341e3 / 0.972e3 * t117 * t370 * t122 - 0.19e2 / 0.162e3 * t187 * t375 * t191 + t186 * t382 * t148 * t384 * t150 / 0.486e3 - 0.209e3 / 0.486e3 * t71 * t370 * t79 + 0.797e3 / 0.1944e4 * t130 * t375 * params.a - t129 * t382 * t207 / 0.48e2 + t129 * t401 * t224 * t384 * t226 / 0.2916e4 - 0.5e1 / 0.16e2 * t85 * t86 * t374 * t91 + 0.1445e4 / 0.31104e5 * t85 * t382 * t151 - 0.35e2 / 0.15552e5 * t85 * t401 * t227 + 0.5e1 / 0.23328e5 * params.c3 / t417 * t141 * t72 / t398 / t109 / t147 / t78 * t384
  t435 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t328 * t42 * t95 - 0.3e1 / 0.8e1 * t5 * t41 * t103 * t95 - 0.9e1 / 0.8e1 * t5 * t43 * t154 + t5 * t101 * t163 * t95 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t104 * t154 - 0.9e1 / 0.8e1 * t5 * t108 * t230 - 0.5e1 / 0.36e2 * t5 * t161 * t351 * t95 + t5 * t164 * t154 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t168 * t230 - 0.3e1 / 0.8e1 * t5 * t172 * t430)
  t445 = f.my_piecewise5(t14, 0, t10, 0, -t323)
  t449 = f.my_piecewise3(t240, 0, -0.8e1 / 0.27e2 / t242 / t239 * t246 * t245 + 0.4e1 / 0.3e1 * t243 * t245 * t250 + 0.4e1 / 0.3e1 * t241 * t445)
  t467 = f.my_piecewise3(t237, 0, -0.3e1 / 0.8e1 * t5 * t449 * t42 * t291 - 0.3e1 / 0.8e1 * t5 * t254 * t103 * t291 + t5 * t297 * t163 * t291 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t303 * t351 * t291)
  d111 = 0.3e1 * t235 + 0.3e1 * t309 + t6 * (t435 + t467)

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
  t56 = 6 ** (0.1e1 / 0.3e1)
  t58 = jnp.pi ** 2
  t59 = t58 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = 0.1e1 / t60
  t62 = params.c1 * t56 * t61
  t63 = r0 ** 2
  t64 = r0 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t67 = 0.1e1 / t65 / t63
  t69 = params.a * t56
  t74 = 0.1e1 + t69 * t61 * s0 * t67 / 0.24e2
  t75 = 0.1e1 / t74
  t79 = t56 ** 2
  t82 = 0.1e1 / t59 / t58
  t83 = params.c2 * t79 * t82
  t84 = s0 ** 2
  t85 = t63 ** 2
  t86 = t85 * r0
  t90 = t74 ** 2
  t91 = 0.1e1 / t90
  t95 = t58 ** 2
  t96 = 0.1e1 / t95
  t97 = params.c3 * t96
  t98 = t84 * s0
  t99 = t85 ** 2
  t102 = t90 * t74
  t103 = 0.1e1 / t102
  t107 = 0.1e1 + t62 * s0 * t67 * t75 / 0.24e2 + t83 * t84 / t64 / t86 * t91 / 0.576e3 + t97 * t98 / t99 * t103 / 0.2304e4
  t116 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t117 = t54 ** 2
  t118 = 0.1e1 / t117
  t119 = t116 * t118
  t123 = t116 * t54
  t124 = t63 * r0
  t132 = params.c1 * t79 * t82
  t133 = t85 * t63
  t136 = t84 / t64 / t133
  t137 = t91 * params.a
  t144 = params.c2 * t96
  t145 = t144 * t98
  t146 = t99 * r0
  t147 = 0.1e1 / t146
  t156 = t84 ** 2
  t157 = t99 * t124
  t162 = t90 ** 2
  t163 = 0.1e1 / t162
  t165 = t56 * t61
  t166 = t163 * params.a * t165
  t169 = -t62 * s0 / t65 / t124 * t75 / 0.9e1 + t132 * t136 * t137 / 0.216e3 - t83 * t136 * t91 / 0.108e3 + t145 * t147 * t103 * params.a / 0.432e3 - t97 * t98 * t147 * t103 / 0.288e3 + t97 * t156 / t65 / t157 * t166 / 0.6912e4
  t175 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t177 = 0.1e1 / t117 / t6
  t178 = t175 * t177
  t182 = t175 * t118
  t186 = t175 * t54
  t193 = t85 * t124
  t196 = t84 / t64 / t193
  t200 = params.c1 * t96
  t201 = t200 * t98
  t203 = 0.1e1 / t99 / t63
  t204 = t203 * t103
  t205 = params.a ** 2
  t215 = t99 * t85
  t218 = t156 / t65 / t215
  t221 = t163 * t205 * t165
  t231 = t156 * s0
  t238 = 0.1e1 / t162 / t74
  t240 = t79 * t82
  t241 = t238 * t205 * t240
  t244 = 0.11e2 / 0.27e2 * t62 * s0 / t65 / t85 * t75 - t132 * t196 * t137 / 0.24e2 + t201 * t204 * t205 / 0.162e3 + 0.19e2 / 0.324e3 * t83 * t196 * t91 - 0.43e2 / 0.1296e4 * t145 * t204 * params.a + t144 * t218 * t221 / 0.1296e4 + t97 * t98 * t203 * t103 / 0.32e2 - 0.59e2 / 0.20736e5 * t97 * t218 * t166 + t97 * t231 / t64 / t99 / t193 * t241 / 0.15552e5
  t248 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t249 = t248 * f.p.zeta_threshold
  t251 = f.my_piecewise3(t20, t249, t21 * t19)
  t253 = 0.1e1 / t117 / t25
  t254 = t251 * t253
  t258 = t251 * t177
  t262 = t251 * t118
  t266 = t251 * t54
  t275 = t84 / t64 / t99
  t279 = 0.1e1 / t157
  t280 = t279 * t103
  t287 = t156 / t65 / t99 / t86
  t289 = t205 * params.a
  t291 = t163 * t289 * t165
  t303 = t99 ** 2
  t306 = t231 / t64 / t303
  t309 = t238 * t289 * t240
  t322 = t95 ** 2
  t323 = 0.1e1 / t322
  t324 = params.c3 * t323
  t325 = t156 * t84
  t326 = t324 * t325
  t330 = 0.1e1 / t162 / t90
  t335 = -0.154e3 / 0.81e2 * t62 * s0 / t65 / t86 * t75 + 0.341e3 / 0.972e3 * t132 * t275 * t137 - 0.19e2 / 0.162e3 * t201 * t280 * t205 + t200 * t287 * t291 / 0.486e3 - 0.209e3 / 0.486e3 * t83 * t275 * t91 + 0.797e3 / 0.1944e4 * t145 * t280 * params.a - t144 * t287 * t221 / 0.48e2 + t144 * t306 * t309 / 0.2916e4 - 0.5e1 / 0.16e2 * t97 * t98 * t279 * t103 + 0.1445e4 / 0.31104e5 * t97 * t287 * t166 - 0.35e2 / 0.15552e5 * t97 * t306 * t241 + 0.5e1 / 0.23328e5 * t326 / t303 / t124 * t330 * t289
  t340 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t107 - 0.3e1 / 0.8e1 * t5 * t119 * t107 - 0.9e1 / 0.8e1 * t5 * t123 * t169 + t5 * t178 * t107 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t182 * t169 - 0.9e1 / 0.8e1 * t5 * t186 * t244 - 0.5e1 / 0.36e2 * t5 * t254 * t107 + t5 * t258 * t169 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t262 * t244 - 0.3e1 / 0.8e1 * t5 * t266 * t335)
  t342 = r1 <= f.p.dens_threshold
  t343 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t344 = 0.1e1 + t343
  t345 = t344 <= f.p.zeta_threshold
  t346 = t344 ** (0.1e1 / 0.3e1)
  t347 = t346 ** 2
  t349 = 0.1e1 / t347 / t344
  t351 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t352 = t351 ** 2
  t356 = 0.1e1 / t347
  t357 = t356 * t351
  t359 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t363 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t367 = f.my_piecewise3(t345, 0, -0.8e1 / 0.27e2 * t349 * t352 * t351 + 0.4e1 / 0.3e1 * t357 * t359 + 0.4e1 / 0.3e1 * t346 * t363)
  t369 = r1 ** 2
  t370 = r1 ** (0.1e1 / 0.3e1)
  t371 = t370 ** 2
  t373 = 0.1e1 / t371 / t369
  t379 = 0.1e1 + t69 * t61 * s2 * t373 / 0.24e2
  t384 = s2 ** 2
  t385 = t369 ** 2
  t390 = t379 ** 2
  t396 = t385 ** 2
  t404 = 0.1e1 + t62 * s2 * t373 / t379 / 0.24e2 + t83 * t384 / t370 / t385 / r1 / t390 / 0.576e3 + t97 * t384 * s2 / t396 / t390 / t379 / 0.2304e4
  t413 = f.my_piecewise3(t345, 0, 0.4e1 / 0.9e1 * t356 * t352 + 0.4e1 / 0.3e1 * t346 * t359)
  t420 = f.my_piecewise3(t345, 0, 0.4e1 / 0.3e1 * t346 * t351)
  t426 = f.my_piecewise3(t345, t249, t346 * t344)
  t432 = f.my_piecewise3(t342, 0, -0.3e1 / 0.8e1 * t5 * t367 * t54 * t404 - 0.3e1 / 0.8e1 * t5 * t413 * t118 * t404 + t5 * t420 * t177 * t404 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t426 * t253 * t404)
  t442 = t84 / t64 / t146
  t446 = 0.1e1 / t215
  t447 = t446 * t103
  t454 = t156 / t65 / t99 / t133
  t461 = t231 / t64 / t303 / r0
  t463 = t205 ** 2
  t484 = 0.1e1 / t303 / t85 * t330
  t513 = 0.2618e4 / 0.243e3 * t62 * s0 / t65 / t133 * t75 - 0.3047e4 / 0.972e3 * t132 * t442 * t137 + 0.2563e4 / 0.1458e4 * t201 * t447 * t205 - 0.49e2 / 0.729e3 * t200 * t454 * t291 + 0.2e1 / 0.2187e4 * t200 * t461 * t238 * t463 * t240 + 0.5225e4 / 0.1458e4 * t83 * t442 * t91 - 0.29645e5 / 0.5832e4 * t145 * t447 * params.a + 0.4915e4 / 0.11664e5 * t144 * t454 * t221 - 0.65e2 / 0.4374e4 * t144 * t461 * t309 + 0.5e1 / 0.4374e4 * params.c2 * t323 * t325 * t484 * t463 + 0.55e2 / 0.16e2 * t97 * t98 * t446 * t103 - 0.68965e5 / 0.93312e5 * t97 * t454 * t166 + 0.8035e4 / 0.139968e6 * t97 * t461 * t241 - 0.5e1 / 0.432e3 * t326 * t484 * t289 + 0.5e1 / 0.34992e5 * t324 * t156 * t98 / t65 / t303 / t133 / t162 / t102 * t463 * t165
  t517 = t19 ** 2
  t520 = t30 ** 2
  t526 = t41 ** 2
  t535 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t536 = f.my_piecewise5(t10, 0, t14, 0, t535)
  t540 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t517 * t520 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t526 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t536)
  t584 = 0.1e1 / t117 / t36
  t589 = -0.3e1 / 0.8e1 * t5 * t266 * t513 - 0.3e1 / 0.8e1 * t5 * t540 * t54 * t107 - 0.3e1 / 0.2e1 * t5 * t55 * t169 - 0.3e1 / 0.2e1 * t5 * t119 * t169 - 0.9e1 / 0.4e1 * t5 * t123 * t244 + t5 * t178 * t169 - 0.3e1 / 0.2e1 * t5 * t182 * t244 - 0.3e1 / 0.2e1 * t5 * t186 * t335 - 0.5e1 / 0.9e1 * t5 * t254 * t169 + t5 * t258 * t244 / 0.2e1 - t5 * t262 * t335 / 0.2e1 - t5 * t53 * t118 * t107 / 0.2e1 + t5 * t116 * t177 * t107 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t175 * t253 * t107 + 0.10e2 / 0.27e2 * t5 * t251 * t584 * t107
  t590 = f.my_piecewise3(t1, 0, t589)
  t591 = t344 ** 2
  t594 = t352 ** 2
  t600 = t359 ** 2
  t606 = f.my_piecewise5(t14, 0, t10, 0, -t535)
  t610 = f.my_piecewise3(t345, 0, 0.40e2 / 0.81e2 / t347 / t591 * t594 - 0.16e2 / 0.9e1 * t349 * t352 * t359 + 0.4e1 / 0.3e1 * t356 * t600 + 0.16e2 / 0.9e1 * t357 * t363 + 0.4e1 / 0.3e1 * t346 * t606)
  t632 = f.my_piecewise3(t342, 0, -0.3e1 / 0.8e1 * t5 * t610 * t54 * t404 - t5 * t367 * t118 * t404 / 0.2e1 + t5 * t413 * t177 * t404 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t420 * t253 * t404 + 0.10e2 / 0.27e2 * t5 * t426 * t584 * t404)
  d1111 = 0.4e1 * t340 + 0.4e1 * t432 + t6 * (t590 + t632)

  res = {'v4rho4': d1111}
  return res
