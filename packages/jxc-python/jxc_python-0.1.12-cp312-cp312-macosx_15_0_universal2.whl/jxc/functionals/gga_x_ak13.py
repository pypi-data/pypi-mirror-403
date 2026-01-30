"""Generated from gga_x_ak13.mpl."""

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
  params_B1_raw = params.B1
  if isinstance(params_B1_raw, (str, bytes, dict)):
    params_B1 = params_B1_raw
  else:
    try:
      params_B1_seq = list(params_B1_raw)
    except TypeError:
      params_B1 = params_B1_raw
    else:
      params_B1_seq = np.asarray(params_B1_seq, dtype=np.float64)
      params_B1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_B1_seq))
  params_B2_raw = params.B2
  if isinstance(params_B2_raw, (str, bytes, dict)):
    params_B2 = params_B2_raw
  else:
    try:
      params_B2_seq = list(params_B2_raw)
    except TypeError:
      params_B2 = params_B2_raw
    else:
      params_B2_seq = np.asarray(params_B2_seq, dtype=np.float64)
      params_B2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_B2_seq))

  ak13_f0 = lambda s: 1 + params_B1 * s * jnp.log(1 + s) + params_B2 * s * jnp.log(1 + jnp.log(1 + s))

  ak13_f = lambda x: ak13_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ak13_f, rs, zeta, xs0, xs1)

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
  params_B1_raw = params.B1
  if isinstance(params_B1_raw, (str, bytes, dict)):
    params_B1 = params_B1_raw
  else:
    try:
      params_B1_seq = list(params_B1_raw)
    except TypeError:
      params_B1 = params_B1_raw
    else:
      params_B1_seq = np.asarray(params_B1_seq, dtype=np.float64)
      params_B1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_B1_seq))
  params_B2_raw = params.B2
  if isinstance(params_B2_raw, (str, bytes, dict)):
    params_B2 = params_B2_raw
  else:
    try:
      params_B2_seq = list(params_B2_raw)
    except TypeError:
      params_B2 = params_B2_raw
    else:
      params_B2_seq = np.asarray(params_B2_seq, dtype=np.float64)
      params_B2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_B2_seq))

  ak13_f0 = lambda s: 1 + params_B1 * s * jnp.log(1 + s) + params_B2 * s * jnp.log(1 + jnp.log(1 + s))

  ak13_f = lambda x: ak13_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ak13_f, rs, zeta, xs0, xs1)

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
  params_B1_raw = params.B1
  if isinstance(params_B1_raw, (str, bytes, dict)):
    params_B1 = params_B1_raw
  else:
    try:
      params_B1_seq = list(params_B1_raw)
    except TypeError:
      params_B1 = params_B1_raw
    else:
      params_B1_seq = np.asarray(params_B1_seq, dtype=np.float64)
      params_B1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_B1_seq))
  params_B2_raw = params.B2
  if isinstance(params_B2_raw, (str, bytes, dict)):
    params_B2 = params_B2_raw
  else:
    try:
      params_B2_seq = list(params_B2_raw)
    except TypeError:
      params_B2 = params_B2_raw
    else:
      params_B2_seq = np.asarray(params_B2_seq, dtype=np.float64)
      params_B2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_B2_seq))

  ak13_f0 = lambda s: 1 + params_B1 * s * jnp.log(1 + s) + params_B2 * s * jnp.log(1 + jnp.log(1 + s))

  ak13_f = lambda x: ak13_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ak13_f, rs, zeta, xs0, xs1)

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
  t29 = t28 ** 2
  t31 = jnp.pi ** 2
  t32 = t31 ** (0.1e1 / 0.3e1)
  t33 = 0.1e1 / t32
  t34 = params.B1 * t29 * t33
  t35 = jnp.sqrt(s0)
  t36 = r0 ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t36 / r0
  t39 = t35 * t38
  t40 = t29 * t33
  t43 = 0.1e1 + t40 * t39 / 0.12e2
  t44 = jnp.log(t43)
  t49 = params.B2 * t29 * t33
  t50 = 0.1e1 + t44
  t51 = jnp.log(t50)
  t55 = 0.1e1 + t34 * t39 * t44 / 0.12e2 + t49 * t39 * t51 / 0.12e2
  t59 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t55)
  t60 = r1 <= f.p.dens_threshold
  t61 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t62 = 0.1e1 + t61
  t63 = t62 <= f.p.zeta_threshold
  t64 = t62 ** (0.1e1 / 0.3e1)
  t66 = f.my_piecewise3(t63, t22, t64 * t62)
  t67 = t66 * t26
  t68 = jnp.sqrt(s2)
  t69 = r1 ** (0.1e1 / 0.3e1)
  t71 = 0.1e1 / t69 / r1
  t72 = t68 * t71
  t75 = 0.1e1 + t40 * t72 / 0.12e2
  t76 = jnp.log(t75)
  t80 = 0.1e1 + t76
  t81 = jnp.log(t80)
  t85 = 0.1e1 + t34 * t72 * t76 / 0.12e2 + t49 * t72 * t81 / 0.12e2
  t89 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t67 * t85)
  t90 = t6 ** 2
  t92 = t16 / t90
  t93 = t7 - t92
  t94 = f.my_piecewise5(t10, 0, t14, 0, t93)
  t97 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t94)
  t102 = t26 ** 2
  t103 = 0.1e1 / t102
  t107 = t5 * t25 * t103 * t55 / 0.8e1
  t108 = r0 ** 2
  t111 = t35 / t36 / t108
  t115 = params.B1 * t28
  t116 = t32 ** 2
  t117 = 0.1e1 / t116
  t118 = t115 * t117
  t120 = t36 ** 2
  t123 = s0 / t120 / t108 / r0
  t124 = 0.1e1 / t43
  t132 = params.B2 * t28 * t117
  t133 = 0.1e1 / t50
  t143 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t97 * t26 * t55 - t107 - 0.3e1 / 0.8e1 * t5 * t27 * (-t34 * t111 * t44 / 0.9e1 - t118 * t123 * t124 / 0.18e2 - t49 * t111 * t51 / 0.9e1 - t132 * t123 * t124 * t133 / 0.18e2))
  t145 = f.my_piecewise5(t14, 0, t10, 0, -t93)
  t148 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t145)
  t156 = t5 * t66 * t103 * t85 / 0.8e1
  t158 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t148 * t26 * t85 - t156)
  vrho_0_ = t59 + t89 + t6 * (t143 + t158)
  t161 = -t7 - t92
  t162 = f.my_piecewise5(t10, 0, t14, 0, t161)
  t165 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t162)
  t171 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t165 * t26 * t55 - t107)
  t173 = f.my_piecewise5(t14, 0, t10, 0, -t161)
  t176 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t173)
  t181 = r1 ** 2
  t184 = t68 / t69 / t181
  t189 = t69 ** 2
  t192 = s2 / t189 / t181 / r1
  t193 = 0.1e1 / t75
  t200 = 0.1e1 / t80
  t210 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t176 * t26 * t85 - t156 - 0.3e1 / 0.8e1 * t5 * t67 * (-t34 * t184 * t76 / 0.9e1 - t118 * t192 * t193 / 0.18e2 - t49 * t184 * t81 / 0.9e1 - t132 * t192 * t193 * t200 / 0.18e2))
  vrho_1_ = t59 + t89 + t6 * (t171 + t210)
  t214 = 0.1e1 / t35 * t38
  t219 = 0.1e1 / t120 / t108
  t235 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (t34 * t214 * t44 / 0.24e2 + t115 * t117 * t219 * t124 / 0.48e2 + t49 * t214 * t51 / 0.24e2 + t132 * t219 * t124 * t133 / 0.48e2))
  vsigma_0_ = t6 * t235
  vsigma_1_ = 0.0e0
  t237 = 0.1e1 / t68 * t71
  t242 = 0.1e1 / t189 / t181
  t258 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t67 * (t34 * t237 * t76 / 0.24e2 + t115 * t117 * t242 * t193 / 0.48e2 + t49 * t237 * t81 / 0.24e2 + t132 * t242 * t193 * t200 / 0.48e2))
  vsigma_2_ = t6 * t258
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
  params_B1_raw = params.B1
  if isinstance(params_B1_raw, (str, bytes, dict)):
    params_B1 = params_B1_raw
  else:
    try:
      params_B1_seq = list(params_B1_raw)
    except TypeError:
      params_B1 = params_B1_raw
    else:
      params_B1_seq = np.asarray(params_B1_seq, dtype=np.float64)
      params_B1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_B1_seq))
  params_B2_raw = params.B2
  if isinstance(params_B2_raw, (str, bytes, dict)):
    params_B2 = params_B2_raw
  else:
    try:
      params_B2_seq = list(params_B2_raw)
    except TypeError:
      params_B2 = params_B2_raw
    else:
      params_B2_seq = np.asarray(params_B2_seq, dtype=np.float64)
      params_B2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_B2_seq))

  ak13_f0 = lambda s: 1 + params_B1 * s * jnp.log(1 + s) + params_B2 * s * jnp.log(1 + jnp.log(1 + s))

  ak13_f = lambda x: ak13_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, ak13_f, rs, zeta, xs0, xs1)

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
  t21 = t20 ** 2
  t23 = jnp.pi ** 2
  t24 = t23 ** (0.1e1 / 0.3e1)
  t25 = 0.1e1 / t24
  t26 = params.B1 * t21 * t25
  t27 = jnp.sqrt(s0)
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t27 * t28
  t31 = 0.1e1 / t18 / r0
  t36 = 0.1e1 + t21 * t25 * t29 * t31 / 0.12e2
  t37 = jnp.log(t36)
  t38 = t31 * t37
  t43 = params.B2 * t21 * t25
  t44 = 0.1e1 + t37
  t45 = jnp.log(t44)
  t46 = t31 * t45
  t50 = 0.1e1 + t26 * t29 * t38 / 0.12e2 + t43 * t29 * t46 / 0.12e2
  t54 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t50)
  t55 = t18 ** 2
  t61 = r0 ** 2
  t63 = 0.1e1 / t18 / t61
  t69 = t24 ** 2
  t70 = 0.1e1 / t69
  t71 = params.B1 * t20 * t70
  t72 = t28 ** 2
  t76 = 0.1e1 / t55 / t61 / r0
  t77 = 0.1e1 / t36
  t86 = params.B2 * t20
  t91 = t77 / t44
  t100 = f.my_piecewise3(t2, 0, -t6 * t17 / t55 * t50 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-t26 * t29 * t63 * t37 / 0.9e1 - t71 * s0 * t72 * t76 * t77 / 0.18e2 - t43 * t29 * t63 * t45 / 0.9e1 - t86 * t70 * s0 * t72 * t76 * t91 / 0.18e2))
  vrho_0_ = 0.2e1 * r0 * t100 + 0.2e1 * t54
  t104 = 0.1e1 / t27 * t28
  t110 = t72 / t55 / t61
  t125 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (t26 * t104 * t38 / 0.24e2 + t71 * t110 * t77 / 0.48e2 + t43 * t104 * t46 / 0.24e2 + t86 * t70 * t110 * t91 / 0.48e2))
  vsigma_0_ = 0.2e1 * r0 * t125
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
  t23 = t22 ** 2
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t26
  t28 = params.B1 * t23 * t27
  t29 = jnp.sqrt(s0)
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t29 * t30
  t33 = 0.1e1 / t18 / r0
  t38 = 0.1e1 + t23 * t27 * t31 * t33 / 0.12e2
  t39 = jnp.log(t38)
  t40 = t33 * t39
  t45 = params.B2 * t23 * t27
  t46 = 0.1e1 + t39
  t47 = jnp.log(t46)
  t48 = t33 * t47
  t52 = 0.1e1 + t28 * t31 * t40 / 0.12e2 + t45 * t31 * t48 / 0.12e2
  t56 = t17 * t18
  t57 = r0 ** 2
  t59 = 0.1e1 / t18 / t57
  t60 = t59 * t39
  t65 = t26 ** 2
  t66 = 0.1e1 / t65
  t67 = params.B1 * t22 * t66
  t68 = t30 ** 2
  t69 = s0 * t68
  t70 = t57 * r0
  t72 = 0.1e1 / t19 / t70
  t73 = 0.1e1 / t38
  t78 = t59 * t47
  t82 = params.B2 * t22
  t84 = t82 * t66 * s0
  t85 = t68 * t72
  t86 = 0.1e1 / t46
  t87 = t73 * t86
  t88 = t85 * t87
  t91 = -t28 * t31 * t60 / 0.9e1 - t67 * t69 * t72 * t73 / 0.18e2 - t45 * t31 * t78 / 0.9e1 - t84 * t88 / 0.18e2
  t96 = f.my_piecewise3(t2, 0, -t6 * t21 * t52 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t56 * t91)
  t108 = 0.1e1 / t18 / t70
  t113 = t57 ** 2
  t115 = 0.1e1 / t19 / t113
  t120 = 0.1e1 / t25
  t121 = params.B1 * t120
  t122 = t29 * s0
  t124 = 0.1e1 / t113 / t57
  t126 = t38 ** 2
  t127 = 0.1e1 / t126
  t139 = params.B2 * t120
  t140 = t139 * t122
  t141 = t124 * t127
  t145 = t46 ** 2
  t146 = 0.1e1 / t145
  t155 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t52 / 0.12e2 - t6 * t21 * t91 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t56 * (0.7e1 / 0.27e2 * t28 * t31 * t108 * t39 + 0.5e1 / 0.18e2 * t67 * t69 * t115 * t73 - 0.2e1 / 0.27e2 * t121 * t122 * t124 * t127 + 0.7e1 / 0.27e2 * t45 * t31 * t108 * t47 + 0.5e1 / 0.18e2 * t84 * t68 * t115 * t87 - 0.2e1 / 0.27e2 * t140 * t141 * t86 - 0.2e1 / 0.27e2 * t140 * t141 * t146))
  v2rho2_0_ = 0.2e1 * r0 * t155 + 0.4e1 * t96
  t158 = 0.1e1 / t29
  t159 = t158 * t30
  t164 = 0.1e1 / t19 / t57
  t165 = t68 * t164
  t172 = t82 * t66
  t173 = t165 * t87
  t176 = t28 * t159 * t40 / 0.24e2 + t67 * t165 * t73 / 0.48e2 + t45 * t159 * t48 / 0.24e2 + t172 * t173 / 0.48e2
  t180 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t56 * t176)
  t191 = 0.1e1 / t113 / r0
  t201 = t139 * t191
  t202 = t127 * t86
  t206 = t127 * t146
  t215 = f.my_piecewise3(t2, 0, -t6 * t21 * t176 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t56 * (-t28 * t159 * t60 / 0.18e2 - t67 * t85 * t73 / 0.12e2 + t121 * t191 * t127 * t29 / 0.36e2 - t45 * t159 * t78 / 0.18e2 - t172 * t88 / 0.12e2 + t201 * t202 * t29 / 0.36e2 + t201 * t206 * t29 / 0.36e2))
  v2rhosigma_0_ = 0.2e1 * r0 * t215 + 0.2e1 * t180
  t219 = 0.1e1 / t122 * t30
  t223 = 0.1e1 / s0
  t229 = 0.1e1 / t113
  t241 = t139 * t229
  t252 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t56 * (-t28 * t219 * t40 / 0.48e2 + t67 * t223 * t68 * t164 * t73 / 0.96e2 - t121 * t229 * t127 * t158 / 0.96e2 - t45 * t219 * t48 / 0.48e2 + t82 * t66 * t223 * t173 / 0.96e2 - t241 * t202 * t158 / 0.96e2 - t241 * t206 * t158 / 0.96e2))
  v2sigma2_0_ = 0.2e1 * r0 * t252
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
  t24 = t23 ** 2
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = 0.1e1 / t27
  t29 = params.B1 * t24 * t28
  t30 = jnp.sqrt(s0)
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t30 * t31
  t34 = 0.1e1 / t18 / r0
  t35 = t24 * t28
  t39 = 0.1e1 + t35 * t32 * t34 / 0.12e2
  t40 = jnp.log(t39)
  t46 = params.B2 * t24 * t28
  t47 = 0.1e1 + t40
  t48 = jnp.log(t47)
  t53 = 0.1e1 + t29 * t32 * t34 * t40 / 0.12e2 + t46 * t32 * t34 * t48 / 0.12e2
  t58 = t17 / t19
  t59 = r0 ** 2
  t61 = 0.1e1 / t18 / t59
  t67 = t27 ** 2
  t68 = 0.1e1 / t67
  t69 = params.B1 * t23 * t68
  t70 = t31 ** 2
  t71 = s0 * t70
  t72 = t59 * r0
  t74 = 0.1e1 / t19 / t72
  t75 = 0.1e1 / t39
  t86 = params.B2 * t23 * t68 * s0
  t88 = 0.1e1 / t47
  t89 = t75 * t88
  t93 = -t29 * t32 * t61 * t40 / 0.9e1 - t69 * t71 * t74 * t75 / 0.18e2 - t46 * t32 * t61 * t48 / 0.9e1 - t86 * t70 * t74 * t89 / 0.18e2
  t97 = t17 * t18
  t99 = 0.1e1 / t18 / t72
  t104 = t59 ** 2
  t106 = 0.1e1 / t19 / t104
  t111 = 0.1e1 / t26
  t112 = params.B1 * t111
  t113 = t30 * s0
  t115 = 0.1e1 / t104 / t59
  t117 = t39 ** 2
  t118 = 0.1e1 / t117
  t130 = params.B2 * t111
  t131 = t130 * t113
  t132 = t115 * t118
  t136 = t47 ** 2
  t137 = 0.1e1 / t136
  t141 = 0.7e1 / 0.27e2 * t29 * t32 * t99 * t40 + 0.5e1 / 0.18e2 * t69 * t71 * t106 * t75 - 0.2e1 / 0.27e2 * t112 * t113 * t115 * t118 + 0.7e1 / 0.27e2 * t46 * t32 * t99 * t48 + 0.5e1 / 0.18e2 * t86 * t70 * t106 * t89 - 0.2e1 / 0.27e2 * t131 * t132 * t88 - 0.2e1 / 0.27e2 * t131 * t132 * t137
  t146 = f.my_piecewise3(t2, 0, t6 * t22 * t53 / 0.12e2 - t6 * t58 * t93 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t97 * t141)
  t161 = 0.1e1 / t18 / t104
  t168 = 0.1e1 / t19 / t104 / r0
  t174 = 0.1e1 / t104 / t72
  t179 = s0 ** 2
  t180 = t104 ** 2
  t183 = t179 / t18 / t180
  t186 = 0.1e1 / t117 / t39
  t200 = t174 * t118
  t207 = t130 * t183
  t209 = t35 * t31
  t223 = -0.70e2 / 0.81e2 * t29 * t32 * t161 * t40 - 0.119e3 / 0.81e2 * t69 * t71 * t168 * t75 + 0.22e2 / 0.27e2 * t112 * t113 * t174 * t118 - 0.4e1 / 0.243e3 * t112 * t183 * t186 * t24 * t28 * t31 - 0.70e2 / 0.81e2 * t46 * t32 * t161 * t48 - 0.119e3 / 0.81e2 * t86 * t70 * t168 * t89 + 0.22e2 / 0.27e2 * t131 * t200 * t88 + 0.22e2 / 0.27e2 * t131 * t200 * t137 - 0.4e1 / 0.243e3 * t207 * t186 * t88 * t209 - 0.2e1 / 0.81e2 * t207 * t186 * t137 * t209 - 0.4e1 / 0.243e3 * t207 * t186 / t136 / t47 * t209
  t228 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 / t19 / t59 * t53 + t6 * t22 * t93 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t58 * t141 - 0.3e1 / 0.8e1 * t6 * t97 * t223)
  v3rho3_0_ = 0.2e1 * r0 * t228 + 0.6e1 * t146

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
  t23 = t17 / t20 / t18
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t28
  t30 = params.B1 * t25 * t29
  t31 = jnp.sqrt(s0)
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t31 * t32
  t35 = 0.1e1 / t19 / r0
  t36 = t25 * t29
  t40 = 0.1e1 + t36 * t33 * t35 / 0.12e2
  t41 = jnp.log(t40)
  t47 = params.B2 * t25 * t29
  t48 = 0.1e1 + t41
  t49 = jnp.log(t48)
  t54 = 0.1e1 + t30 * t33 * t35 * t41 / 0.12e2 + t47 * t33 * t35 * t49 / 0.12e2
  t60 = t17 / t20 / r0
  t62 = 0.1e1 / t19 / t18
  t68 = t28 ** 2
  t69 = 0.1e1 / t68
  t70 = params.B1 * t24 * t69
  t71 = t32 ** 2
  t72 = s0 * t71
  t73 = t18 * r0
  t75 = 0.1e1 / t20 / t73
  t76 = 0.1e1 / t40
  t87 = params.B2 * t24 * t69 * s0
  t89 = 0.1e1 / t48
  t90 = t76 * t89
  t94 = -t30 * t33 * t62 * t41 / 0.9e1 - t70 * t72 * t75 * t76 / 0.18e2 - t47 * t33 * t62 * t49 / 0.9e1 - t87 * t71 * t75 * t90 / 0.18e2
  t99 = t17 / t20
  t101 = 0.1e1 / t19 / t73
  t106 = t18 ** 2
  t108 = 0.1e1 / t20 / t106
  t113 = 0.1e1 / t27
  t114 = params.B1 * t113
  t115 = t31 * s0
  t116 = t106 * t18
  t117 = 0.1e1 / t116
  t119 = t40 ** 2
  t120 = 0.1e1 / t119
  t132 = params.B2 * t113
  t133 = t132 * t115
  t134 = t117 * t120
  t138 = t48 ** 2
  t139 = 0.1e1 / t138
  t143 = 0.7e1 / 0.27e2 * t30 * t33 * t101 * t41 + 0.5e1 / 0.18e2 * t70 * t72 * t108 * t76 - 0.2e1 / 0.27e2 * t114 * t115 * t117 * t120 + 0.7e1 / 0.27e2 * t47 * t33 * t101 * t49 + 0.5e1 / 0.18e2 * t87 * t71 * t108 * t90 - 0.2e1 / 0.27e2 * t133 * t134 * t89 - 0.2e1 / 0.27e2 * t133 * t134 * t139
  t147 = t17 * t19
  t149 = 0.1e1 / t19 / t106
  t154 = t106 * r0
  t156 = 0.1e1 / t20 / t154
  t162 = 0.1e1 / t106 / t73
  t167 = s0 ** 2
  t168 = t106 ** 2
  t171 = t167 / t19 / t168
  t174 = 0.1e1 / t119 / t40
  t177 = t174 * t25 * t29 * t32
  t188 = t162 * t120
  t195 = t132 * t171
  t197 = t36 * t32
  t198 = t174 * t89 * t197
  t202 = t174 * t139 * t197
  t206 = 0.1e1 / t138 / t48
  t208 = t174 * t206 * t197
  t211 = -0.70e2 / 0.81e2 * t30 * t33 * t149 * t41 - 0.119e3 / 0.81e2 * t70 * t72 * t156 * t76 + 0.22e2 / 0.27e2 * t114 * t115 * t162 * t120 - 0.4e1 / 0.243e3 * t114 * t171 * t177 - 0.70e2 / 0.81e2 * t47 * t33 * t149 * t49 - 0.119e3 / 0.81e2 * t87 * t71 * t156 * t90 + 0.22e2 / 0.27e2 * t133 * t188 * t89 + 0.22e2 / 0.27e2 * t133 * t188 * t139 - 0.4e1 / 0.243e3 * t195 * t198 - 0.2e1 / 0.81e2 * t195 * t202 - 0.4e1 / 0.243e3 * t195 * t208
  t216 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t54 + t6 * t60 * t94 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t99 * t143 - 0.3e1 / 0.8e1 * t6 * t147 * t211)
  t232 = 0.1e1 / t19 / t154
  t240 = t167 / t19 / t168 / r0
  t248 = t31 * t167 / t20 / t168 / t18
  t250 = t119 ** 2
  t251 = 0.1e1 / t250
  t262 = 0.1e1 / t20 / t116
  t267 = t132 * t240
  t274 = t132 * t248
  t277 = t24 * t69 * t71
  t289 = t138 ** 2
  t295 = 0.1e1 / t168
  t304 = t295 * t120
  t311 = 0.910e3 / 0.243e3 * t30 * t33 * t232 * t41 + 0.232e3 / 0.729e3 * t114 * t240 * t177 - 0.8e1 / 0.243e3 * t114 * t248 * t251 * t24 * t69 * t71 + 0.910e3 / 0.243e3 * t47 * t33 * t232 * t49 + 0.721e3 / 0.81e2 * t87 * t71 * t262 * t90 + 0.232e3 / 0.729e3 * t267 * t198 + 0.116e3 / 0.243e3 * t267 * t202 + 0.232e3 / 0.729e3 * t267 * t208 - 0.8e1 / 0.243e3 * t274 * t251 * t89 * t277 - 0.44e2 / 0.729e3 * t274 * t251 * t139 * t277 - 0.16e2 / 0.243e3 * t274 * t251 * t206 * t277 - 0.8e1 / 0.243e3 * t274 * t251 / t289 * t277 - 0.1862e4 / 0.243e3 * t114 * t115 * t295 * t120 + 0.721e3 / 0.81e2 * t70 * t72 * t262 * t76 - 0.1862e4 / 0.243e3 * t133 * t304 * t89 - 0.1862e4 / 0.243e3 * t133 * t304 * t139
  t316 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t75 * t54 - 0.5e1 / 0.9e1 * t6 * t23 * t94 + t6 * t60 * t143 / 0.2e1 - t6 * t99 * t211 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t147 * t311)
  v4rho4_0_ = 0.2e1 * r0 * t316 + 0.8e1 * t216

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
  t33 = t32 ** 2
  t35 = jnp.pi ** 2
  t36 = t35 ** (0.1e1 / 0.3e1)
  t37 = 0.1e1 / t36
  t38 = params.B1 * t33 * t37
  t39 = jnp.sqrt(s0)
  t40 = r0 ** (0.1e1 / 0.3e1)
  t43 = t39 / t40 / r0
  t44 = t33 * t37
  t47 = 0.1e1 + t44 * t43 / 0.12e2
  t48 = jnp.log(t47)
  t53 = params.B2 * t33 * t37
  t54 = 0.1e1 + t48
  t55 = jnp.log(t54)
  t59 = 0.1e1 + t38 * t43 * t48 / 0.12e2 + t53 * t43 * t55 / 0.12e2
  t63 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t64 = t63 * f.p.zeta_threshold
  t66 = f.my_piecewise3(t20, t64, t21 * t19)
  t67 = t30 ** 2
  t68 = 0.1e1 / t67
  t69 = t66 * t68
  t72 = t5 * t69 * t59 / 0.8e1
  t73 = t66 * t30
  t74 = r0 ** 2
  t77 = t39 / t40 / t74
  t82 = t36 ** 2
  t83 = 0.1e1 / t82
  t84 = params.B1 * t32 * t83
  t85 = t74 * r0
  t86 = t40 ** 2
  t89 = s0 / t86 / t85
  t90 = 0.1e1 / t47
  t98 = params.B2 * t32 * t83
  t99 = 0.1e1 / t54
  t100 = t90 * t99
  t104 = -t38 * t77 * t48 / 0.9e1 - t84 * t89 * t90 / 0.18e2 - t53 * t77 * t55 / 0.9e1 - t98 * t89 * t100 / 0.18e2
  t109 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t59 - t72 - 0.3e1 / 0.8e1 * t5 * t73 * t104)
  t111 = r1 <= f.p.dens_threshold
  t112 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t113 = 0.1e1 + t112
  t114 = t113 <= f.p.zeta_threshold
  t115 = t113 ** (0.1e1 / 0.3e1)
  t117 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t120 = f.my_piecewise3(t114, 0, 0.4e1 / 0.3e1 * t115 * t117)
  t121 = t120 * t30
  t122 = jnp.sqrt(s2)
  t123 = r1 ** (0.1e1 / 0.3e1)
  t126 = t122 / t123 / r1
  t129 = 0.1e1 + t44 * t126 / 0.12e2
  t130 = jnp.log(t129)
  t134 = 0.1e1 + t130
  t135 = jnp.log(t134)
  t139 = 0.1e1 + t38 * t126 * t130 / 0.12e2 + t53 * t126 * t135 / 0.12e2
  t144 = f.my_piecewise3(t114, t64, t115 * t113)
  t145 = t144 * t68
  t148 = t5 * t145 * t139 / 0.8e1
  t150 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t121 * t139 - t148)
  t152 = t21 ** 2
  t153 = 0.1e1 / t152
  t154 = t26 ** 2
  t159 = t16 / t22 / t6
  t161 = -0.2e1 * t23 + 0.2e1 * t159
  t162 = f.my_piecewise5(t10, 0, t14, 0, t161)
  t166 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t153 * t154 + 0.4e1 / 0.3e1 * t21 * t162)
  t173 = t5 * t29 * t68 * t59
  t179 = 0.1e1 / t67 / t6
  t183 = t5 * t66 * t179 * t59 / 0.12e2
  t185 = t5 * t69 * t104
  t189 = t39 / t40 / t85
  t193 = t74 ** 2
  t196 = s0 / t86 / t193
  t200 = 0.1e1 / t35
  t201 = params.B1 * t200
  t202 = t39 * s0
  t204 = 0.1e1 / t193 / t74
  t206 = t47 ** 2
  t207 = 0.1e1 / t206
  t217 = params.B2 * t200
  t218 = t217 * t202
  t219 = t204 * t207
  t223 = t54 ** 2
  t233 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t166 * t30 * t59 - t173 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t104 + t183 - t185 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t73 * (0.7e1 / 0.27e2 * t38 * t189 * t48 + 0.5e1 / 0.18e2 * t84 * t196 * t90 - t201 * t202 * t204 * t207 / 0.27e2 + 0.7e1 / 0.27e2 * t53 * t189 * t55 + 0.5e1 / 0.18e2 * t98 * t196 * t100 - t218 * t219 * t99 / 0.27e2 - t218 * t219 / t223 / 0.27e2))
  t234 = t115 ** 2
  t235 = 0.1e1 / t234
  t236 = t117 ** 2
  t240 = f.my_piecewise5(t14, 0, t10, 0, -t161)
  t244 = f.my_piecewise3(t114, 0, 0.4e1 / 0.9e1 * t235 * t236 + 0.4e1 / 0.3e1 * t115 * t240)
  t251 = t5 * t120 * t68 * t139
  t256 = t5 * t144 * t179 * t139 / 0.12e2
  t258 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t244 * t30 * t139 - t251 / 0.4e1 + t256)
  d11 = 0.2e1 * t109 + 0.2e1 * t150 + t6 * (t233 + t258)
  t261 = -t7 - t24
  t262 = f.my_piecewise5(t10, 0, t14, 0, t261)
  t265 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t262)
  t266 = t265 * t30
  t271 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t266 * t59 - t72)
  t273 = f.my_piecewise5(t14, 0, t10, 0, -t261)
  t276 = f.my_piecewise3(t114, 0, 0.4e1 / 0.3e1 * t115 * t273)
  t277 = t276 * t30
  t281 = t144 * t30
  t282 = r1 ** 2
  t285 = t122 / t123 / t282
  t289 = t282 * r1
  t290 = t123 ** 2
  t293 = s2 / t290 / t289
  t294 = 0.1e1 / t129
  t301 = 0.1e1 / t134
  t302 = t294 * t301
  t306 = -t38 * t285 * t130 / 0.9e1 - t84 * t293 * t294 / 0.18e2 - t53 * t285 * t135 / 0.9e1 - t98 * t293 * t302 / 0.18e2
  t311 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t277 * t139 - t148 - 0.3e1 / 0.8e1 * t5 * t281 * t306)
  t315 = 0.2e1 * t159
  t316 = f.my_piecewise5(t10, 0, t14, 0, t315)
  t320 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t153 * t262 * t26 + 0.4e1 / 0.3e1 * t21 * t316)
  t327 = t5 * t265 * t68 * t59
  t335 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t320 * t30 * t59 - t327 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t266 * t104 - t173 / 0.8e1 + t183 - t185 / 0.8e1)
  t339 = f.my_piecewise5(t14, 0, t10, 0, -t315)
  t343 = f.my_piecewise3(t114, 0, 0.4e1 / 0.9e1 * t235 * t273 * t117 + 0.4e1 / 0.3e1 * t115 * t339)
  t350 = t5 * t276 * t68 * t139
  t357 = t5 * t145 * t306
  t360 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t343 * t30 * t139 - t350 / 0.8e1 - t251 / 0.8e1 + t256 - 0.3e1 / 0.8e1 * t5 * t121 * t306 - t357 / 0.8e1)
  d12 = t109 + t150 + t271 + t311 + t6 * (t335 + t360)
  t365 = t262 ** 2
  t369 = 0.2e1 * t23 + 0.2e1 * t159
  t370 = f.my_piecewise5(t10, 0, t14, 0, t369)
  t374 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t153 * t365 + 0.4e1 / 0.3e1 * t21 * t370)
  t381 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t374 * t30 * t59 - t327 / 0.4e1 + t183)
  t382 = t273 ** 2
  t386 = f.my_piecewise5(t14, 0, t10, 0, -t369)
  t390 = f.my_piecewise3(t114, 0, 0.4e1 / 0.9e1 * t235 * t382 + 0.4e1 / 0.3e1 * t115 * t386)
  t402 = t122 / t123 / t289
  t406 = t282 ** 2
  t409 = s2 / t290 / t406
  t413 = t122 * s2
  t415 = 0.1e1 / t406 / t282
  t417 = t129 ** 2
  t418 = 0.1e1 / t417
  t428 = t217 * t413
  t429 = t415 * t418
  t433 = t134 ** 2
  t443 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t390 * t30 * t139 - t350 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t277 * t306 + t256 - t357 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t281 * (0.7e1 / 0.27e2 * t38 * t402 * t130 + 0.5e1 / 0.18e2 * t84 * t409 * t294 - t201 * t413 * t415 * t418 / 0.27e2 + 0.7e1 / 0.27e2 * t53 * t402 * t135 + 0.5e1 / 0.18e2 * t98 * t409 * t302 - t428 * t429 * t301 / 0.27e2 - t428 * t429 / t433 / 0.27e2))
  d22 = 0.2e1 * t271 + 0.2e1 * t311 + t6 * (t381 + t443)
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
  t45 = t44 ** 2
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = 0.1e1 / t48
  t50 = params.B1 * t45 * t49
  t51 = jnp.sqrt(s0)
  t52 = r0 ** (0.1e1 / 0.3e1)
  t55 = t51 / t52 / r0
  t56 = t45 * t49
  t59 = 0.1e1 + t56 * t55 / 0.12e2
  t60 = jnp.log(t59)
  t65 = params.B2 * t45 * t49
  t66 = 0.1e1 + t60
  t67 = jnp.log(t66)
  t71 = 0.1e1 + t50 * t55 * t60 / 0.12e2 + t65 * t55 * t67 / 0.12e2
  t77 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t78 = t42 ** 2
  t79 = 0.1e1 / t78
  t80 = t77 * t79
  t84 = t77 * t42
  t85 = r0 ** 2
  t88 = t51 / t52 / t85
  t93 = t48 ** 2
  t94 = 0.1e1 / t93
  t95 = params.B1 * t44 * t94
  t96 = t85 * r0
  t97 = t52 ** 2
  t100 = s0 / t97 / t96
  t101 = 0.1e1 / t59
  t109 = params.B2 * t44 * t94
  t110 = 0.1e1 / t66
  t111 = t101 * t110
  t115 = -t50 * t88 * t60 / 0.9e1 - t95 * t100 * t101 / 0.18e2 - t65 * t88 * t67 / 0.9e1 - t109 * t100 * t111 / 0.18e2
  t119 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t120 = t119 * f.p.zeta_threshold
  t122 = f.my_piecewise3(t20, t120, t21 * t19)
  t124 = 0.1e1 / t78 / t6
  t125 = t122 * t124
  t129 = t122 * t79
  t133 = t122 * t42
  t136 = t51 / t52 / t96
  t140 = t85 ** 2
  t143 = s0 / t97 / t140
  t147 = 0.1e1 / t47
  t148 = params.B1 * t147
  t149 = t51 * s0
  t151 = 0.1e1 / t140 / t85
  t153 = t59 ** 2
  t154 = 0.1e1 / t153
  t164 = params.B2 * t147
  t165 = t164 * t149
  t166 = t151 * t154
  t170 = t66 ** 2
  t171 = 0.1e1 / t170
  t175 = 0.7e1 / 0.27e2 * t50 * t136 * t60 + 0.5e1 / 0.18e2 * t95 * t143 * t101 - t148 * t149 * t151 * t154 / 0.27e2 + 0.7e1 / 0.27e2 * t65 * t136 * t67 + 0.5e1 / 0.18e2 * t109 * t143 * t111 - t165 * t166 * t110 / 0.27e2 - t165 * t166 * t171 / 0.27e2
  t180 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t71 - t5 * t80 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t84 * t115 + t5 * t125 * t71 / 0.12e2 - t5 * t129 * t115 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t133 * t175)
  t182 = r1 <= f.p.dens_threshold
  t183 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t184 = 0.1e1 + t183
  t185 = t184 <= f.p.zeta_threshold
  t186 = t184 ** (0.1e1 / 0.3e1)
  t187 = t186 ** 2
  t188 = 0.1e1 / t187
  t190 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t191 = t190 ** 2
  t195 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t199 = f.my_piecewise3(t185, 0, 0.4e1 / 0.9e1 * t188 * t191 + 0.4e1 / 0.3e1 * t186 * t195)
  t201 = jnp.sqrt(s2)
  t202 = r1 ** (0.1e1 / 0.3e1)
  t205 = t201 / t202 / r1
  t209 = jnp.log(0.1e1 + t56 * t205 / 0.12e2)
  t214 = jnp.log(0.1e1 + t209)
  t218 = 0.1e1 + t50 * t205 * t209 / 0.12e2 + t65 * t205 * t214 / 0.12e2
  t224 = f.my_piecewise3(t185, 0, 0.4e1 / 0.3e1 * t186 * t190)
  t230 = f.my_piecewise3(t185, t120, t186 * t184)
  t236 = f.my_piecewise3(t182, 0, -0.3e1 / 0.8e1 * t5 * t199 * t42 * t218 - t5 * t224 * t79 * t218 / 0.4e1 + t5 * t230 * t124 * t218 / 0.12e2)
  t246 = t24 ** 2
  t250 = 0.6e1 * t33 - 0.6e1 * t16 / t246
  t251 = f.my_piecewise5(t10, 0, t14, 0, t250)
  t255 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t251)
  t278 = 0.1e1 / t78 / t24
  t291 = t51 / t52 / t140
  t298 = s0 / t97 / t140 / r0
  t303 = 0.1e1 / t140 / t96
  t308 = s0 ** 2
  t310 = t140 ** 2
  t312 = 0.1e1 / t52 / t310
  t314 = 0.1e1 / t153 / t59
  t325 = t303 * t154
  t333 = t164 * t308 * t312
  t348 = -0.70e2 / 0.81e2 * t50 * t291 * t60 - 0.119e3 / 0.81e2 * t95 * t298 * t101 + 0.11e2 / 0.27e2 * t148 * t149 * t303 * t154 - 0.2e1 / 0.243e3 * t148 * t308 * t312 * t314 * t56 - 0.70e2 / 0.81e2 * t65 * t291 * t67 - 0.119e3 / 0.81e2 * t109 * t298 * t111 + 0.11e2 / 0.27e2 * t165 * t325 * t110 + 0.11e2 / 0.27e2 * t165 * t325 * t171 - 0.2e1 / 0.243e3 * t333 * t314 * t110 * t56 - t333 * t314 * t171 * t56 / 0.81e2 - 0.2e1 / 0.243e3 * t333 * t314 / t170 / t66 * t56
  t353 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t255 * t42 * t71 - 0.3e1 / 0.8e1 * t5 * t41 * t79 * t71 - 0.9e1 / 0.8e1 * t5 * t43 * t115 + t5 * t77 * t124 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t80 * t115 - 0.9e1 / 0.8e1 * t5 * t84 * t175 - 0.5e1 / 0.36e2 * t5 * t122 * t278 * t71 + t5 * t125 * t115 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t129 * t175 - 0.3e1 / 0.8e1 * t5 * t133 * t348)
  t363 = f.my_piecewise5(t14, 0, t10, 0, -t250)
  t367 = f.my_piecewise3(t185, 0, -0.8e1 / 0.27e2 / t187 / t184 * t191 * t190 + 0.4e1 / 0.3e1 * t188 * t190 * t195 + 0.4e1 / 0.3e1 * t186 * t363)
  t385 = f.my_piecewise3(t182, 0, -0.3e1 / 0.8e1 * t5 * t367 * t42 * t218 - 0.3e1 / 0.8e1 * t5 * t199 * t79 * t218 + t5 * t224 * t124 * t218 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t230 * t278 * t218)
  d111 = 0.3e1 * t180 + 0.3e1 * t236 + t6 * (t353 + t385)

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
  t57 = t56 ** 2
  t59 = jnp.pi ** 2
  t60 = t59 ** (0.1e1 / 0.3e1)
  t61 = 0.1e1 / t60
  t62 = params.B1 * t57 * t61
  t63 = jnp.sqrt(s0)
  t64 = r0 ** (0.1e1 / 0.3e1)
  t67 = t63 / t64 / r0
  t68 = t57 * t61
  t71 = 0.1e1 + t68 * t67 / 0.12e2
  t72 = jnp.log(t71)
  t77 = params.B2 * t57 * t61
  t78 = 0.1e1 + t72
  t79 = jnp.log(t78)
  t83 = 0.1e1 + t62 * t67 * t72 / 0.12e2 + t77 * t67 * t79 / 0.12e2
  t92 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t93 = t54 ** 2
  t94 = 0.1e1 / t93
  t95 = t92 * t94
  t99 = t92 * t54
  t100 = r0 ** 2
  t103 = t63 / t64 / t100
  t108 = t60 ** 2
  t109 = 0.1e1 / t108
  t110 = params.B1 * t56 * t109
  t111 = t100 * r0
  t112 = t64 ** 2
  t115 = s0 / t112 / t111
  t116 = 0.1e1 / t71
  t124 = params.B2 * t56 * t109
  t125 = 0.1e1 / t78
  t126 = t116 * t125
  t130 = -t62 * t103 * t72 / 0.9e1 - t110 * t115 * t116 / 0.18e2 - t77 * t103 * t79 / 0.9e1 - t124 * t115 * t126 / 0.18e2
  t136 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t138 = 0.1e1 / t93 / t6
  t139 = t136 * t138
  t143 = t136 * t94
  t147 = t136 * t54
  t150 = t63 / t64 / t111
  t154 = t100 ** 2
  t157 = s0 / t112 / t154
  t161 = 0.1e1 / t59
  t162 = params.B1 * t161
  t163 = t63 * s0
  t164 = t154 * t100
  t165 = 0.1e1 / t164
  t167 = t71 ** 2
  t168 = 0.1e1 / t167
  t178 = params.B2 * t161
  t179 = t178 * t163
  t180 = t165 * t168
  t184 = t78 ** 2
  t185 = 0.1e1 / t184
  t189 = 0.7e1 / 0.27e2 * t62 * t150 * t72 + 0.5e1 / 0.18e2 * t110 * t157 * t116 - t162 * t163 * t165 * t168 / 0.27e2 + 0.7e1 / 0.27e2 * t77 * t150 * t79 + 0.5e1 / 0.18e2 * t124 * t157 * t126 - t179 * t180 * t125 / 0.27e2 - t179 * t180 * t185 / 0.27e2
  t193 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t194 = t193 * f.p.zeta_threshold
  t196 = f.my_piecewise3(t20, t194, t21 * t19)
  t198 = 0.1e1 / t93 / t25
  t199 = t196 * t198
  t203 = t196 * t138
  t207 = t196 * t94
  t211 = t196 * t54
  t214 = t63 / t64 / t154
  t218 = t154 * r0
  t221 = s0 / t112 / t218
  t226 = 0.1e1 / t154 / t111
  t231 = s0 ** 2
  t232 = t162 * t231
  t233 = t154 ** 2
  t235 = 0.1e1 / t64 / t233
  t237 = 0.1e1 / t167 / t71
  t248 = t226 * t168
  t256 = t178 * t231 * t235
  t258 = t237 * t125 * t68
  t262 = t237 * t185 * t68
  t266 = 0.1e1 / t184 / t78
  t268 = t237 * t266 * t68
  t271 = -0.70e2 / 0.81e2 * t62 * t214 * t72 - 0.119e3 / 0.81e2 * t110 * t221 * t116 + 0.11e2 / 0.27e2 * t162 * t163 * t226 * t168 - 0.2e1 / 0.243e3 * t232 * t235 * t237 * t68 - 0.70e2 / 0.81e2 * t77 * t214 * t79 - 0.119e3 / 0.81e2 * t124 * t221 * t126 + 0.11e2 / 0.27e2 * t179 * t248 * t125 + 0.11e2 / 0.27e2 * t179 * t248 * t185 - 0.2e1 / 0.243e3 * t256 * t258 - t256 * t262 / 0.81e2 - 0.2e1 / 0.243e3 * t256 * t268
  t276 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t83 - 0.3e1 / 0.8e1 * t5 * t95 * t83 - 0.9e1 / 0.8e1 * t5 * t99 * t130 + t5 * t139 * t83 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t143 * t130 - 0.9e1 / 0.8e1 * t5 * t147 * t189 - 0.5e1 / 0.36e2 * t5 * t199 * t83 + t5 * t203 * t130 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t207 * t189 - 0.3e1 / 0.8e1 * t5 * t211 * t271)
  t278 = r1 <= f.p.dens_threshold
  t279 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t280 = 0.1e1 + t279
  t281 = t280 <= f.p.zeta_threshold
  t282 = t280 ** (0.1e1 / 0.3e1)
  t283 = t282 ** 2
  t285 = 0.1e1 / t283 / t280
  t287 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t288 = t287 ** 2
  t292 = 0.1e1 / t283
  t293 = t292 * t287
  t295 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t299 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t303 = f.my_piecewise3(t281, 0, -0.8e1 / 0.27e2 * t285 * t288 * t287 + 0.4e1 / 0.3e1 * t293 * t295 + 0.4e1 / 0.3e1 * t282 * t299)
  t305 = jnp.sqrt(s2)
  t306 = r1 ** (0.1e1 / 0.3e1)
  t309 = t305 / t306 / r1
  t313 = jnp.log(0.1e1 + t68 * t309 / 0.12e2)
  t318 = jnp.log(0.1e1 + t313)
  t322 = 0.1e1 + t62 * t309 * t313 / 0.12e2 + t77 * t309 * t318 / 0.12e2
  t331 = f.my_piecewise3(t281, 0, 0.4e1 / 0.9e1 * t292 * t288 + 0.4e1 / 0.3e1 * t282 * t295)
  t338 = f.my_piecewise3(t281, 0, 0.4e1 / 0.3e1 * t282 * t287)
  t344 = f.my_piecewise3(t281, t194, t282 * t280)
  t350 = f.my_piecewise3(t278, 0, -0.3e1 / 0.8e1 * t5 * t303 * t54 * t322 - 0.3e1 / 0.8e1 * t5 * t331 * t94 * t322 + t5 * t338 * t138 * t322 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t344 * t198 * t322)
  t357 = s0 / t112 / t164
  t361 = 0.1e1 / t233
  t362 = t361 * t168
  t371 = 0.1e1 / t64 / t233 / r0
  t373 = t178 * t231 * t371
  t380 = t63 * t231
  t383 = 0.1e1 / t112 / t233 / t100
  t385 = t178 * t380 * t383
  t386 = t167 ** 2
  t387 = 0.1e1 / t386
  t389 = t56 * t109
  t401 = t184 ** 2
  t413 = t63 / t64 / t218
  t432 = 0.721e3 / 0.81e2 * t110 * t357 * t116 - 0.931e3 / 0.243e3 * t179 * t362 * t125 - 0.931e3 / 0.243e3 * t179 * t362 * t185 + 0.116e3 / 0.729e3 * t373 * t258 + 0.58e2 / 0.243e3 * t373 * t262 + 0.116e3 / 0.729e3 * t373 * t268 - 0.4e1 / 0.243e3 * t385 * t387 * t125 * t389 - 0.22e2 / 0.729e3 * t385 * t387 * t185 * t389 - 0.8e1 / 0.243e3 * t385 * t387 * t266 * t389 - 0.4e1 / 0.243e3 * t385 * t387 / t401 * t389 - 0.931e3 / 0.243e3 * t162 * t163 * t361 * t168 + 0.910e3 / 0.243e3 * t62 * t413 * t72 + 0.116e3 / 0.729e3 * t232 * t371 * t237 * t68 - 0.4e1 / 0.243e3 * t162 * t380 * t383 * t387 * t389 + 0.910e3 / 0.243e3 * t77 * t413 * t79 + 0.721e3 / 0.81e2 * t124 * t357 * t126
  t436 = t19 ** 2
  t439 = t30 ** 2
  t445 = t41 ** 2
  t454 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t455 = f.my_piecewise5(t10, 0, t14, 0, t454)
  t459 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t436 * t439 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t445 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t455)
  t492 = 0.1e1 / t93 / t36
  t505 = -t5 * t207 * t271 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t211 * t432 - 0.3e1 / 0.8e1 * t5 * t459 * t54 * t83 - 0.3e1 / 0.2e1 * t5 * t55 * t130 - 0.3e1 / 0.2e1 * t5 * t95 * t130 - 0.9e1 / 0.4e1 * t5 * t99 * t189 + t5 * t139 * t130 - 0.3e1 / 0.2e1 * t5 * t143 * t189 - 0.3e1 / 0.2e1 * t5 * t147 * t271 - 0.5e1 / 0.9e1 * t5 * t199 * t130 + t5 * t203 * t189 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t136 * t198 * t83 + 0.10e2 / 0.27e2 * t5 * t196 * t492 * t83 - t5 * t53 * t94 * t83 / 0.2e1 + t5 * t92 * t138 * t83 / 0.2e1
  t506 = f.my_piecewise3(t1, 0, t505)
  t507 = t280 ** 2
  t510 = t288 ** 2
  t516 = t295 ** 2
  t522 = f.my_piecewise5(t14, 0, t10, 0, -t454)
  t526 = f.my_piecewise3(t281, 0, 0.40e2 / 0.81e2 / t283 / t507 * t510 - 0.16e2 / 0.9e1 * t285 * t288 * t295 + 0.4e1 / 0.3e1 * t292 * t516 + 0.16e2 / 0.9e1 * t293 * t299 + 0.4e1 / 0.3e1 * t282 * t522)
  t548 = f.my_piecewise3(t278, 0, -0.3e1 / 0.8e1 * t5 * t526 * t54 * t322 - t5 * t303 * t94 * t322 / 0.2e1 + t5 * t331 * t138 * t322 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t338 * t198 * t322 + 0.10e2 / 0.27e2 * t5 * t344 * t492 * t322)
  d1111 = 0.4e1 * t276 + 0.4e1 * t350 + t6 * (t506 + t548)

  res = {'v4rho4': d1111}
  return res
