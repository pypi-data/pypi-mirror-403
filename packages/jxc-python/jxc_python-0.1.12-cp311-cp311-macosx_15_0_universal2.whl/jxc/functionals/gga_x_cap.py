"""Generated from gga_x_cap.mpl."""

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
  params_alphaoAx_raw = params.alphaoAx
  if isinstance(params_alphaoAx_raw, (str, bytes, dict)):
    params_alphaoAx = params_alphaoAx_raw
  else:
    try:
      params_alphaoAx_seq = list(params_alphaoAx_raw)
    except TypeError:
      params_alphaoAx = params_alphaoAx_raw
    else:
      params_alphaoAx_seq = np.asarray(params_alphaoAx_seq, dtype=np.float64)
      params_alphaoAx = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphaoAx_seq))
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

  cap_f0 = lambda s: 1 - params_alphaoAx * s * jnp.log(1 + s) / (1 + params_c * jnp.log(1 + s))

  cap_f = lambda x: cap_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, cap_f, rs, z, xs0, xs1)

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
  params_alphaoAx_raw = params.alphaoAx
  if isinstance(params_alphaoAx_raw, (str, bytes, dict)):
    params_alphaoAx = params_alphaoAx_raw
  else:
    try:
      params_alphaoAx_seq = list(params_alphaoAx_raw)
    except TypeError:
      params_alphaoAx = params_alphaoAx_raw
    else:
      params_alphaoAx_seq = np.asarray(params_alphaoAx_seq, dtype=np.float64)
      params_alphaoAx = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphaoAx_seq))
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

  cap_f0 = lambda s: 1 - params_alphaoAx * s * jnp.log(1 + s) / (1 + params_c * jnp.log(1 + s))

  cap_f = lambda x: cap_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, cap_f, rs, z, xs0, xs1)

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
  params_alphaoAx_raw = params.alphaoAx
  if isinstance(params_alphaoAx_raw, (str, bytes, dict)):
    params_alphaoAx = params_alphaoAx_raw
  else:
    try:
      params_alphaoAx_seq = list(params_alphaoAx_raw)
    except TypeError:
      params_alphaoAx = params_alphaoAx_raw
    else:
      params_alphaoAx_seq = np.asarray(params_alphaoAx_seq, dtype=np.float64)
      params_alphaoAx = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphaoAx_seq))
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

  cap_f0 = lambda s: 1 - params_alphaoAx * s * jnp.log(1 + s) / (1 + params_c * jnp.log(1 + s))

  cap_f = lambda x: cap_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, cap_f, rs, z, xs0, xs1)

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
  t34 = params.alphaoAx * t29 * t33
  t35 = jnp.sqrt(s0)
  t36 = r0 ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t36 / r0
  t39 = t35 * t38
  t40 = t29 * t33
  t43 = 0.1e1 + t40 * t39 / 0.12e2
  t44 = jnp.log(t43)
  t46 = params.c * t44 + 0.1e1
  t47 = 0.1e1 / t46
  t48 = t44 * t47
  t52 = 0.1e1 - t34 * t39 * t48 / 0.12e2
  t56 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t52)
  t57 = r1 <= f.p.dens_threshold
  t58 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t59 = 0.1e1 + t58
  t60 = t59 <= f.p.zeta_threshold
  t61 = t59 ** (0.1e1 / 0.3e1)
  t63 = f.my_piecewise3(t60, t22, t61 * t59)
  t64 = t63 * t26
  t65 = jnp.sqrt(s2)
  t66 = r1 ** (0.1e1 / 0.3e1)
  t68 = 0.1e1 / t66 / r1
  t69 = t65 * t68
  t72 = 0.1e1 + t40 * t69 / 0.12e2
  t73 = jnp.log(t72)
  t75 = params.c * t73 + 0.1e1
  t76 = 0.1e1 / t75
  t77 = t73 * t76
  t81 = 0.1e1 - t34 * t69 * t77 / 0.12e2
  t85 = f.my_piecewise3(t57, 0, -0.3e1 / 0.8e1 * t5 * t64 * t81)
  t86 = t6 ** 2
  t88 = t16 / t86
  t89 = t7 - t88
  t90 = f.my_piecewise5(t10, 0, t14, 0, t89)
  t93 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t90)
  t98 = t26 ** 2
  t99 = 0.1e1 / t98
  t103 = t5 * t25 * t99 * t52 / 0.8e1
  t104 = r0 ** 2
  t111 = params.alphaoAx * t28
  t112 = t32 ** 2
  t113 = 0.1e1 / t112
  t114 = t111 * t113
  t116 = t36 ** 2
  t118 = 0.1e1 / t116 / t104 / r0
  t120 = 0.1e1 / t43
  t128 = t46 ** 2
  t129 = 0.1e1 / t128
  t140 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t93 * t26 * t52 - t103 - 0.3e1 / 0.8e1 * t5 * t27 * (t34 * t35 / t36 / t104 * t48 / 0.9e1 + t114 * s0 * t118 * t120 * t47 / 0.18e2 - t111 * t113 * s0 * t118 * t44 * t129 * params.c * t120 / 0.18e2))
  t142 = f.my_piecewise5(t14, 0, t10, 0, -t89)
  t145 = f.my_piecewise3(t60, 0, 0.4e1 / 0.3e1 * t61 * t142)
  t153 = t5 * t63 * t99 * t81 / 0.8e1
  t155 = f.my_piecewise3(t57, 0, -0.3e1 / 0.8e1 * t5 * t145 * t26 * t81 - t153)
  vrho_0_ = t56 + t85 + t6 * (t140 + t155)
  t158 = -t7 - t88
  t159 = f.my_piecewise5(t10, 0, t14, 0, t158)
  t162 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t159)
  t168 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t162 * t26 * t52 - t103)
  t170 = f.my_piecewise5(t14, 0, t10, 0, -t158)
  t173 = f.my_piecewise3(t60, 0, 0.4e1 / 0.3e1 * t61 * t170)
  t178 = r1 ** 2
  t186 = t66 ** 2
  t188 = 0.1e1 / t186 / t178 / r1
  t190 = 0.1e1 / t72
  t198 = t75 ** 2
  t199 = 0.1e1 / t198
  t210 = f.my_piecewise3(t57, 0, -0.3e1 / 0.8e1 * t5 * t173 * t26 * t81 - t153 - 0.3e1 / 0.8e1 * t5 * t64 * (t34 * t65 / t66 / t178 * t77 / 0.9e1 + t114 * s2 * t188 * t190 * t76 / 0.18e2 - t111 * t113 * s2 * t188 * t73 * t199 * params.c * t190 / 0.18e2))
  vrho_1_ = t56 + t85 + t6 * (t168 + t210)
  t219 = 0.1e1 / t116 / t104
  t235 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-t34 / t35 * t38 * t48 / 0.24e2 - t114 * t219 * t120 * t47 / 0.48e2 + t111 * t113 * t219 * t44 * t129 * params.c * t120 / 0.48e2))
  vsigma_0_ = t6 * t235
  vsigma_1_ = 0.0e0
  t242 = 0.1e1 / t186 / t178
  t258 = f.my_piecewise3(t57, 0, -0.3e1 / 0.8e1 * t5 * t64 * (-t34 / t65 * t68 * t77 / 0.24e2 - t114 * t242 * t190 * t76 / 0.48e2 + t111 * t113 * t242 * t73 * t199 * params.c * t190 / 0.48e2))
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
  params_alphaoAx_raw = params.alphaoAx
  if isinstance(params_alphaoAx_raw, (str, bytes, dict)):
    params_alphaoAx = params_alphaoAx_raw
  else:
    try:
      params_alphaoAx_seq = list(params_alphaoAx_raw)
    except TypeError:
      params_alphaoAx = params_alphaoAx_raw
    else:
      params_alphaoAx_seq = np.asarray(params_alphaoAx_seq, dtype=np.float64)
      params_alphaoAx = np.concatenate((np.array([np.nan], dtype=np.float64), params_alphaoAx_seq))
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

  cap_f0 = lambda s: 1 - params_alphaoAx * s * jnp.log(1 + s) / (1 + params_c * jnp.log(1 + s))

  cap_f = lambda x: cap_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, cap_f, rs, z, xs0, xs1)

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
  t22 = params.alphaoAx * t21
  t23 = jnp.pi ** 2
  t24 = t23 ** (0.1e1 / 0.3e1)
  t25 = 0.1e1 / t24
  t26 = jnp.sqrt(s0)
  t28 = t22 * t25 * t26
  t29 = 2 ** (0.1e1 / 0.3e1)
  t31 = 0.1e1 / t18 / r0
  t38 = 0.1e1 + t21 * t25 * t26 * t29 * t31 / 0.12e2
  t39 = jnp.log(t38)
  t41 = params.c * t39 + 0.1e1
  t42 = 0.1e1 / t41
  t43 = t39 * t42
  t44 = t29 * t31 * t43
  t47 = 0.1e1 - t28 * t44 / 0.12e2
  t51 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t47)
  t52 = t18 ** 2
  t58 = r0 ** 2
  t65 = params.alphaoAx * t20
  t66 = t24 ** 2
  t67 = 0.1e1 / t66
  t68 = t67 * s0
  t70 = t29 ** 2
  t73 = 0.1e1 / t52 / t58 / r0
  t75 = 0.1e1 / t38
  t76 = t75 * t42
  t83 = t41 ** 2
  t86 = 0.1e1 / t83 * params.c * t75
  t95 = f.my_piecewise3(t2, 0, -t6 * t17 / t52 * t47 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (t28 * t29 / t18 / t58 * t43 / 0.9e1 + t65 * t68 * t70 * t73 * t76 / 0.18e2 - t65 * t68 * t70 * t73 * t39 * t86 / 0.18e2))
  vrho_0_ = 0.2e1 * r0 * t95 + 0.2e1 * t51
  t105 = 0.1e1 / t52 / t58
  t120 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-t22 * t25 / t26 * t44 / 0.24e2 - t65 * t67 * t70 * t105 * t76 / 0.48e2 + t65 * t67 * t70 * t105 * t39 * t86 / 0.48e2))
  vsigma_0_ = 0.2e1 * r0 * t120
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
  t24 = params.alphaoAx * t23
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t26
  t28 = jnp.sqrt(s0)
  t30 = t24 * t27 * t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t33 = 0.1e1 / t18 / r0
  t40 = 0.1e1 + t23 * t27 * t28 * t31 * t33 / 0.12e2
  t41 = jnp.log(t40)
  t43 = params.c * t41 + 0.1e1
  t44 = 0.1e1 / t43
  t45 = t41 * t44
  t46 = t31 * t33 * t45
  t49 = 0.1e1 - t30 * t46 / 0.12e2
  t53 = t17 * t18
  t54 = r0 ** 2
  t58 = t31 / t18 / t54 * t45
  t61 = params.alphaoAx * t22
  t62 = t26 ** 2
  t63 = 0.1e1 / t62
  t64 = t63 * s0
  t65 = t61 * t64
  t66 = t31 ** 2
  t67 = t54 * r0
  t69 = 0.1e1 / t19 / t67
  t71 = 0.1e1 / t40
  t72 = t71 * t44
  t73 = t66 * t69 * t72
  t77 = t61 * t64 * t66
  t79 = t43 ** 2
  t80 = 0.1e1 / t79
  t81 = t80 * params.c
  t82 = t81 * t71
  t83 = t69 * t41 * t82
  t86 = t30 * t58 / 0.9e1 + t65 * t73 / 0.18e2 - t77 * t83 / 0.18e2
  t91 = f.my_piecewise3(t2, 0, -t6 * t21 * t49 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t53 * t86)
  t108 = t54 ** 2
  t110 = 0.1e1 / t19 / t108
  t120 = params.alphaoAx / t25
  t121 = t28 * s0
  t122 = t120 * t121
  t124 = 0.1e1 / t108 / t54
  t125 = t40 ** 2
  t126 = 0.1e1 / t125
  t127 = t124 * t126
  t135 = t120 * t121 * t124
  t137 = 0.1e1 / t79 / t43
  t139 = params.c ** 2
  t154 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t49 / 0.12e2 - t6 * t21 * t86 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t53 * (-0.7e1 / 0.27e2 * t30 * t31 / t18 / t67 * t45 - 0.5e1 / 0.18e2 * t65 * t66 * t110 * t72 + 0.5e1 / 0.18e2 * t77 * t110 * t41 * t82 + 0.2e1 / 0.27e2 * t122 * t127 * t44 + 0.4e1 / 0.27e2 * t122 * t127 * t81 - 0.4e1 / 0.27e2 * t135 * t41 * t137 * t139 * t126 - 0.2e1 / 0.27e2 * t135 * t41 * t80 * params.c * t126))
  v2rho2_0_ = 0.2e1 * r0 * t154 + 0.4e1 * t91
  t157 = 0.1e1 / t28
  t159 = t24 * t27 * t157
  t162 = t61 * t63
  t164 = 0.1e1 / t19 / t54
  t166 = t66 * t164 * t72
  t170 = t61 * t63 * t66
  t172 = t164 * t41 * t82
  t175 = -t159 * t46 / 0.24e2 - t162 * t166 / 0.48e2 + t170 * t172 / 0.48e2
  t179 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t53 * t175)
  t190 = 0.1e1 / t108 / r0
  t191 = t120 * t190
  t192 = t126 * t44
  t196 = t126 * t80
  t198 = t196 * params.c * t28
  t202 = t120 * t190 * t41
  t203 = t137 * t139
  t215 = f.my_piecewise3(t2, 0, -t6 * t21 * t175 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t53 * (t159 * t58 / 0.18e2 + t162 * t73 / 0.12e2 - t170 * t83 / 0.12e2 - t191 * t192 * t28 / 0.36e2 - t191 * t198 / 0.18e2 + t202 * t203 * t126 * t28 / 0.18e2 + t202 * t198 / 0.36e2))
  v2rhosigma_0_ = 0.2e1 * r0 * t215 + 0.2e1 * t179
  t224 = t63 / s0
  t232 = 0.1e1 / t108
  t233 = t120 * t232
  t238 = t196 * params.c * t157
  t242 = t120 * t232 * t41
  t253 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t53 * (t24 * t27 / t121 * t46 / 0.48e2 - t61 * t224 * t166 / 0.96e2 + t61 * t224 * t66 * t172 / 0.96e2 + t233 * t192 * t157 / 0.96e2 + t233 * t238 / 0.48e2 - t242 * t203 * t126 * t157 / 0.48e2 - t242 * t238 / 0.96e2))
  v2sigma2_0_ = 0.2e1 * r0 * t253
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
  t29 = jnp.sqrt(s0)
  t31 = params.alphaoAx * t24 * t28 * t29
  t32 = 2 ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t18 / r0
  t36 = t24 * t28
  t41 = 0.1e1 + t36 * t29 * t32 * t34 / 0.12e2
  t42 = jnp.log(t41)
  t44 = params.c * t42 + 0.1e1
  t45 = 0.1e1 / t44
  t46 = t42 * t45
  t50 = 0.1e1 - t31 * t32 * t34 * t46 / 0.12e2
  t55 = t17 / t19
  t56 = r0 ** 2
  t63 = params.alphaoAx * t23
  t64 = t27 ** 2
  t66 = 0.1e1 / t64 * s0
  t67 = t63 * t66
  t68 = t32 ** 2
  t69 = t56 * r0
  t71 = 0.1e1 / t19 / t69
  t73 = 0.1e1 / t41
  t74 = t73 * t45
  t79 = t63 * t66 * t68
  t81 = t44 ** 2
  t82 = 0.1e1 / t81
  t83 = t82 * params.c
  t84 = t83 * t73
  t88 = t31 * t32 / t18 / t56 * t46 / 0.9e1 + t67 * t68 * t71 * t74 / 0.18e2 - t79 * t71 * t42 * t84 / 0.18e2
  t92 = t17 * t18
  t99 = t56 ** 2
  t101 = 0.1e1 / t19 / t99
  t111 = params.alphaoAx / t26
  t112 = t29 * s0
  t113 = t111 * t112
  t115 = 0.1e1 / t99 / t56
  t116 = t41 ** 2
  t117 = 0.1e1 / t116
  t118 = t115 * t117
  t126 = t111 * t112 * t115
  t128 = 0.1e1 / t81 / t44
  t130 = params.c ** 2
  t132 = t42 * t128 * t130 * t117
  t137 = t42 * t82 * params.c * t117
  t140 = -0.7e1 / 0.27e2 * t31 * t32 / t18 / t69 * t46 - 0.5e1 / 0.18e2 * t67 * t68 * t101 * t74 + 0.5e1 / 0.18e2 * t79 * t101 * t42 * t84 + 0.2e1 / 0.27e2 * t113 * t118 * t45 + 0.4e1 / 0.27e2 * t113 * t118 * t83 - 0.4e1 / 0.27e2 * t126 * t132 - 0.2e1 / 0.27e2 * t126 * t137
  t145 = f.my_piecewise3(t2, 0, t6 * t22 * t50 / 0.12e2 - t6 * t55 * t88 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t92 * t140)
  t167 = 0.1e1 / t19 / t99 / r0
  t177 = 0.1e1 / t99 / t69
  t178 = t177 * t117
  t186 = t111 * t112 * t177
  t191 = s0 ** 2
  t192 = t99 ** 2
  t195 = t191 / t18 / t192
  t198 = 0.1e1 / t116 / t41
  t200 = t36 * t32
  t205 = t111 * t195 * t198
  t209 = t128 * t130
  t214 = t111 * t195 * t42
  t215 = t81 ** 2
  t231 = 0.70e2 / 0.81e2 * t31 * t32 / t18 / t99 * t46 + 0.119e3 / 0.81e2 * t67 * t68 * t167 * t74 - 0.119e3 / 0.81e2 * t79 * t167 * t42 * t84 - 0.22e2 / 0.27e2 * t113 * t178 * t45 - 0.44e2 / 0.27e2 * t113 * t178 * t83 + 0.44e2 / 0.27e2 * t186 * t132 + 0.22e2 / 0.27e2 * t186 * t137 + 0.4e1 / 0.243e3 * t111 * t195 * t198 * t45 * t200 + 0.4e1 / 0.81e2 * t205 * t83 * t200 + 0.4e1 / 0.81e2 * t205 * t209 * t200 - 0.4e1 / 0.81e2 * t214 / t215 * t130 * params.c * t198 * t200 - 0.4e1 / 0.81e2 * t214 * t209 * t198 * t200 - 0.4e1 / 0.243e3 * t214 * t83 * t198 * t200
  t236 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 / t19 / t56 * t50 + t6 * t22 * t88 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t55 * t140 - 0.3e1 / 0.8e1 * t6 * t92 * t231)
  v3rho3_0_ = 0.2e1 * r0 * t236 + 0.6e1 * t145

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
  t30 = jnp.sqrt(s0)
  t32 = params.alphaoAx * t25 * t29 * t30
  t33 = 2 ** (0.1e1 / 0.3e1)
  t35 = 0.1e1 / t19 / r0
  t37 = t25 * t29
  t42 = 0.1e1 + t37 * t30 * t33 * t35 / 0.12e2
  t43 = jnp.log(t42)
  t45 = params.c * t43 + 0.1e1
  t46 = 0.1e1 / t45
  t47 = t43 * t46
  t51 = 0.1e1 - t32 * t33 * t35 * t47 / 0.12e2
  t57 = t17 / t20 / r0
  t64 = params.alphaoAx * t24
  t65 = t28 ** 2
  t66 = 0.1e1 / t65
  t67 = t66 * s0
  t68 = t64 * t67
  t69 = t33 ** 2
  t70 = t18 * r0
  t72 = 0.1e1 / t20 / t70
  t74 = 0.1e1 / t42
  t75 = t74 * t46
  t80 = t64 * t67 * t69
  t82 = t45 ** 2
  t83 = 0.1e1 / t82
  t84 = t83 * params.c
  t85 = t84 * t74
  t89 = t32 * t33 / t19 / t18 * t47 / 0.9e1 + t68 * t69 * t72 * t75 / 0.18e2 - t80 * t72 * t43 * t85 / 0.18e2
  t94 = t17 / t20
  t101 = t18 ** 2
  t103 = 0.1e1 / t20 / t101
  t113 = params.alphaoAx / t27
  t114 = t30 * s0
  t115 = t113 * t114
  t116 = t101 * t18
  t117 = 0.1e1 / t116
  t118 = t42 ** 2
  t119 = 0.1e1 / t118
  t120 = t117 * t119
  t128 = t113 * t114 * t117
  t130 = 0.1e1 / t82 / t45
  t132 = params.c ** 2
  t134 = t43 * t130 * t132 * t119
  t139 = t43 * t83 * params.c * t119
  t142 = -0.7e1 / 0.27e2 * t32 * t33 / t19 / t70 * t47 - 0.5e1 / 0.18e2 * t68 * t69 * t103 * t75 + 0.5e1 / 0.18e2 * t80 * t103 * t43 * t85 + 0.2e1 / 0.27e2 * t115 * t120 * t46 + 0.4e1 / 0.27e2 * t115 * t120 * t84 - 0.4e1 / 0.27e2 * t128 * t134 - 0.2e1 / 0.27e2 * t128 * t139
  t146 = t17 * t19
  t153 = t101 * r0
  t155 = 0.1e1 / t20 / t153
  t165 = 0.1e1 / t101 / t70
  t166 = t165 * t119
  t174 = t113 * t114 * t165
  t179 = s0 ** 2
  t180 = t101 ** 2
  t183 = t179 / t19 / t180
  t186 = 0.1e1 / t118 / t42
  t188 = t37 * t33
  t189 = t186 * t46 * t188
  t193 = t113 * t183 * t186
  t194 = t84 * t188
  t197 = t130 * t132
  t198 = t197 * t188
  t202 = t113 * t183 * t43
  t203 = t82 ** 2
  t206 = 0.1e1 / t203 * t132 * params.c
  t208 = t206 * t186 * t188
  t212 = t197 * t186 * t188
  t216 = t84 * t186 * t188
  t219 = 0.70e2 / 0.81e2 * t32 * t33 / t19 / t101 * t47 + 0.119e3 / 0.81e2 * t68 * t69 * t155 * t75 - 0.119e3 / 0.81e2 * t80 * t155 * t43 * t85 - 0.22e2 / 0.27e2 * t115 * t166 * t46 - 0.44e2 / 0.27e2 * t115 * t166 * t84 + 0.44e2 / 0.27e2 * t174 * t134 + 0.22e2 / 0.27e2 * t174 * t139 + 0.4e1 / 0.243e3 * t113 * t183 * t189 + 0.4e1 / 0.81e2 * t193 * t194 + 0.4e1 / 0.81e2 * t193 * t198 - 0.4e1 / 0.81e2 * t202 * t208 - 0.4e1 / 0.81e2 * t202 * t212 - 0.4e1 / 0.243e3 * t202 * t216
  t224 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t51 + t6 * t57 * t89 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t94 * t142 - 0.3e1 / 0.8e1 * t6 * t146 * t219)
  t240 = 0.1e1 / t20 / t116
  t245 = 0.1e1 / t180
  t247 = t113 * t114 * t245
  t256 = t30 * t179 / t20 / t180 / t18
  t257 = t118 ** 2
  t258 = 0.1e1 / t257
  t260 = t113 * t256 * t258
  t268 = t24 * t66 * t69
  t282 = t179 / t19 / t180 / r0
  t284 = t113 * t282 * t186
  t289 = t245 * t119
  t298 = t113 * t282 * t43
  t306 = t113 * t256 * t43
  t309 = t132 ** 2
  t341 = 0.1862e4 / 0.243e3 * t115 * t289 * t46 + 0.232e3 / 0.243e3 * t298 * t208 + 0.232e3 / 0.243e3 * t298 * t212 + 0.232e3 / 0.729e3 * t298 * t216 - 0.32e2 / 0.243e3 * t306 / t203 / t45 * t309 * t258 * t268 - 0.16e2 / 0.81e2 * t306 * t206 * t258 * t268 - 0.88e2 / 0.729e3 * t306 * t197 * t258 * t268 - 0.8e1 / 0.243e3 * t306 * t84 * t258 * t268 - 0.910e3 / 0.243e3 * t32 * t33 / t19 / t153 * t47 - 0.232e3 / 0.729e3 * t113 * t282 * t189 + 0.8e1 / 0.243e3 * t113 * t256 * t258 * t46 * t268
  t347 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t72 * t51 - 0.5e1 / 0.9e1 * t6 * t23 * t89 + t6 * t57 * t142 / 0.2e1 - t6 * t94 * t219 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t146 * (-0.721e3 / 0.81e2 * t68 * t69 * t240 * t75 - 0.3724e4 / 0.243e3 * t247 * t134 - 0.1862e4 / 0.243e3 * t247 * t139 + 0.88e2 / 0.729e3 * t260 * t83 * t24 * t66 * t69 * params.c + 0.16e2 / 0.81e2 * t260 * t197 * t268 + 0.32e2 / 0.243e3 * t260 * t206 * t268 + 0.721e3 / 0.81e2 * t80 * t240 * t43 * t85 - 0.232e3 / 0.243e3 * t284 * t194 - 0.232e3 / 0.243e3 * t284 * t198 + 0.3724e4 / 0.243e3 * t115 * t289 * t84 + t341))
  v4rho4_0_ = 0.2e1 * r0 * t347 + 0.8e1 * t224

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
  t38 = params.alphaoAx * t33 * t37
  t39 = jnp.sqrt(s0)
  t40 = r0 ** (0.1e1 / 0.3e1)
  t43 = t39 / t40 / r0
  t44 = t33 * t37
  t47 = 0.1e1 + t44 * t43 / 0.12e2
  t48 = jnp.log(t47)
  t50 = params.c * t48 + 0.1e1
  t51 = 0.1e1 / t50
  t52 = t48 * t51
  t56 = 0.1e1 - t38 * t43 * t52 / 0.12e2
  t60 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t61 = t60 * f.p.zeta_threshold
  t63 = f.my_piecewise3(t20, t61, t21 * t19)
  t64 = t30 ** 2
  t65 = 0.1e1 / t64
  t66 = t63 * t65
  t69 = t5 * t66 * t56 / 0.8e1
  t70 = t63 * t30
  t71 = r0 ** 2
  t78 = params.alphaoAx * t32
  t79 = t36 ** 2
  t80 = 0.1e1 / t79
  t81 = t78 * t80
  t82 = t71 * r0
  t83 = t40 ** 2
  t85 = 0.1e1 / t83 / t82
  t87 = 0.1e1 / t47
  t88 = t87 * t51
  t93 = t78 * t80 * s0
  t95 = t50 ** 2
  t96 = 0.1e1 / t95
  t97 = t96 * params.c
  t98 = t97 * t87
  t102 = t38 * t39 / t40 / t71 * t52 / 0.9e1 + t81 * s0 * t85 * t88 / 0.18e2 - t93 * t85 * t48 * t98 / 0.18e2
  t107 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t56 - t69 - 0.3e1 / 0.8e1 * t5 * t70 * t102)
  t109 = r1 <= f.p.dens_threshold
  t110 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t111 = 0.1e1 + t110
  t112 = t111 <= f.p.zeta_threshold
  t113 = t111 ** (0.1e1 / 0.3e1)
  t115 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t118 = f.my_piecewise3(t112, 0, 0.4e1 / 0.3e1 * t113 * t115)
  t119 = t118 * t30
  t120 = jnp.sqrt(s2)
  t121 = r1 ** (0.1e1 / 0.3e1)
  t124 = t120 / t121 / r1
  t127 = 0.1e1 + t44 * t124 / 0.12e2
  t128 = jnp.log(t127)
  t130 = params.c * t128 + 0.1e1
  t131 = 0.1e1 / t130
  t132 = t128 * t131
  t136 = 0.1e1 - t38 * t124 * t132 / 0.12e2
  t141 = f.my_piecewise3(t112, t61, t113 * t111)
  t142 = t141 * t65
  t145 = t5 * t142 * t136 / 0.8e1
  t147 = f.my_piecewise3(t109, 0, -0.3e1 / 0.8e1 * t5 * t119 * t136 - t145)
  t149 = t21 ** 2
  t150 = 0.1e1 / t149
  t151 = t26 ** 2
  t156 = t16 / t22 / t6
  t158 = -0.2e1 * t23 + 0.2e1 * t156
  t159 = f.my_piecewise5(t10, 0, t14, 0, t158)
  t163 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t150 * t151 + 0.4e1 / 0.3e1 * t21 * t159)
  t170 = t5 * t29 * t65 * t56
  t176 = 0.1e1 / t64 / t6
  t180 = t5 * t63 * t176 * t56 / 0.12e2
  t182 = t5 * t66 * t102
  t190 = t71 ** 2
  t192 = 0.1e1 / t83 / t190
  t202 = params.alphaoAx / t35
  t203 = t39 * s0
  t204 = t202 * t203
  t206 = 0.1e1 / t190 / t71
  t207 = t47 ** 2
  t208 = 0.1e1 / t207
  t209 = t206 * t208
  t217 = t202 * t203 * t206
  t221 = params.c ** 2
  t236 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t163 * t30 * t56 - t170 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t102 + t180 - t182 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t70 * (-0.7e1 / 0.27e2 * t38 * t39 / t40 / t82 * t52 - 0.5e1 / 0.18e2 * t81 * s0 * t192 * t88 + 0.5e1 / 0.18e2 * t93 * t192 * t48 * t98 + t204 * t209 * t51 / 0.27e2 + 0.2e1 / 0.27e2 * t204 * t209 * t97 - 0.2e1 / 0.27e2 * t217 * t48 / t95 / t50 * t221 * t208 - t217 * t48 * t96 * params.c * t208 / 0.27e2))
  t237 = t113 ** 2
  t238 = 0.1e1 / t237
  t239 = t115 ** 2
  t243 = f.my_piecewise5(t14, 0, t10, 0, -t158)
  t247 = f.my_piecewise3(t112, 0, 0.4e1 / 0.9e1 * t238 * t239 + 0.4e1 / 0.3e1 * t113 * t243)
  t254 = t5 * t118 * t65 * t136
  t259 = t5 * t141 * t176 * t136 / 0.12e2
  t261 = f.my_piecewise3(t109, 0, -0.3e1 / 0.8e1 * t5 * t247 * t30 * t136 - t254 / 0.4e1 + t259)
  d11 = 0.2e1 * t107 + 0.2e1 * t147 + t6 * (t236 + t261)
  t264 = -t7 - t24
  t265 = f.my_piecewise5(t10, 0, t14, 0, t264)
  t268 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t265)
  t269 = t268 * t30
  t274 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t269 * t56 - t69)
  t276 = f.my_piecewise5(t14, 0, t10, 0, -t264)
  t279 = f.my_piecewise3(t112, 0, 0.4e1 / 0.3e1 * t113 * t276)
  t280 = t279 * t30
  t284 = t141 * t30
  t285 = r1 ** 2
  t292 = t285 * r1
  t293 = t121 ** 2
  t295 = 0.1e1 / t293 / t292
  t297 = 0.1e1 / t127
  t298 = t297 * t131
  t303 = t78 * t80 * s2
  t305 = t130 ** 2
  t306 = 0.1e1 / t305
  t307 = t306 * params.c
  t308 = t307 * t297
  t312 = t38 * t120 / t121 / t285 * t132 / 0.9e1 + t81 * s2 * t295 * t298 / 0.18e2 - t303 * t295 * t128 * t308 / 0.18e2
  t317 = f.my_piecewise3(t109, 0, -0.3e1 / 0.8e1 * t5 * t280 * t136 - t145 - 0.3e1 / 0.8e1 * t5 * t284 * t312)
  t321 = 0.2e1 * t156
  t322 = f.my_piecewise5(t10, 0, t14, 0, t321)
  t326 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t150 * t265 * t26 + 0.4e1 / 0.3e1 * t21 * t322)
  t333 = t5 * t268 * t65 * t56
  t341 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t326 * t30 * t56 - t333 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t269 * t102 - t170 / 0.8e1 + t180 - t182 / 0.8e1)
  t345 = f.my_piecewise5(t14, 0, t10, 0, -t321)
  t349 = f.my_piecewise3(t112, 0, 0.4e1 / 0.9e1 * t238 * t276 * t115 + 0.4e1 / 0.3e1 * t113 * t345)
  t356 = t5 * t279 * t65 * t136
  t363 = t5 * t142 * t312
  t366 = f.my_piecewise3(t109, 0, -0.3e1 / 0.8e1 * t5 * t349 * t30 * t136 - t356 / 0.8e1 - t254 / 0.8e1 + t259 - 0.3e1 / 0.8e1 * t5 * t119 * t312 - t363 / 0.8e1)
  d12 = t107 + t147 + t274 + t317 + t6 * (t341 + t366)
  t371 = t265 ** 2
  t375 = 0.2e1 * t23 + 0.2e1 * t156
  t376 = f.my_piecewise5(t10, 0, t14, 0, t375)
  t380 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t150 * t371 + 0.4e1 / 0.3e1 * t21 * t376)
  t387 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t380 * t30 * t56 - t333 / 0.4e1 + t180)
  t388 = t276 ** 2
  t392 = f.my_piecewise5(t14, 0, t10, 0, -t375)
  t396 = f.my_piecewise3(t112, 0, 0.4e1 / 0.9e1 * t238 * t388 + 0.4e1 / 0.3e1 * t113 * t392)
  t412 = t285 ** 2
  t414 = 0.1e1 / t293 / t412
  t423 = t120 * s2
  t424 = t202 * t423
  t426 = 0.1e1 / t412 / t285
  t427 = t127 ** 2
  t428 = 0.1e1 / t427
  t429 = t426 * t428
  t437 = t202 * t423 * t426
  t455 = f.my_piecewise3(t109, 0, -0.3e1 / 0.8e1 * t5 * t396 * t30 * t136 - t356 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t280 * t312 + t259 - t363 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t284 * (-0.7e1 / 0.27e2 * t38 * t120 / t121 / t292 * t132 - 0.5e1 / 0.18e2 * t81 * s2 * t414 * t298 + 0.5e1 / 0.18e2 * t303 * t414 * t128 * t308 + t424 * t429 * t131 / 0.27e2 + 0.2e1 / 0.27e2 * t424 * t429 * t307 - 0.2e1 / 0.27e2 * t437 * t128 / t305 / t130 * t221 * t428 - t437 * t128 * t306 * params.c * t428 / 0.27e2))
  d22 = 0.2e1 * t274 + 0.2e1 * t317 + t6 * (t387 + t455)
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
  t50 = params.alphaoAx * t45 * t49
  t51 = jnp.sqrt(s0)
  t52 = r0 ** (0.1e1 / 0.3e1)
  t55 = t51 / t52 / r0
  t56 = t45 * t49
  t59 = 0.1e1 + t56 * t55 / 0.12e2
  t60 = jnp.log(t59)
  t62 = params.c * t60 + 0.1e1
  t63 = 0.1e1 / t62
  t64 = t60 * t63
  t68 = 0.1e1 - t50 * t55 * t64 / 0.12e2
  t74 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t75 = t42 ** 2
  t76 = 0.1e1 / t75
  t77 = t74 * t76
  t81 = t74 * t42
  t82 = r0 ** 2
  t89 = params.alphaoAx * t44
  t90 = t48 ** 2
  t91 = 0.1e1 / t90
  t92 = t89 * t91
  t93 = t82 * r0
  t94 = t52 ** 2
  t96 = 0.1e1 / t94 / t93
  t98 = 0.1e1 / t59
  t99 = t98 * t63
  t104 = t89 * t91 * s0
  t106 = t62 ** 2
  t107 = 0.1e1 / t106
  t108 = t107 * params.c
  t109 = t108 * t98
  t113 = t50 * t51 / t52 / t82 * t64 / 0.9e1 + t92 * s0 * t96 * t99 / 0.18e2 - t104 * t96 * t60 * t109 / 0.18e2
  t117 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t118 = t117 * f.p.zeta_threshold
  t120 = f.my_piecewise3(t20, t118, t21 * t19)
  t122 = 0.1e1 / t75 / t6
  t123 = t120 * t122
  t127 = t120 * t76
  t131 = t120 * t42
  t138 = t82 ** 2
  t140 = 0.1e1 / t94 / t138
  t150 = params.alphaoAx / t47
  t151 = t51 * s0
  t152 = t150 * t151
  t154 = 0.1e1 / t138 / t82
  t155 = t59 ** 2
  t156 = 0.1e1 / t155
  t157 = t154 * t156
  t165 = t150 * t151 * t154
  t167 = 0.1e1 / t106 / t62
  t169 = params.c ** 2
  t171 = t60 * t167 * t169 * t156
  t176 = t60 * t107 * params.c * t156
  t179 = -0.7e1 / 0.27e2 * t50 * t51 / t52 / t93 * t64 - 0.5e1 / 0.18e2 * t92 * s0 * t140 * t99 + 0.5e1 / 0.18e2 * t104 * t140 * t60 * t109 + t152 * t157 * t63 / 0.27e2 + 0.2e1 / 0.27e2 * t152 * t157 * t108 - 0.2e1 / 0.27e2 * t165 * t171 - t165 * t176 / 0.27e2
  t184 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t68 - t5 * t77 * t68 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t81 * t113 + t5 * t123 * t68 / 0.12e2 - t5 * t127 * t113 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t131 * t179)
  t186 = r1 <= f.p.dens_threshold
  t187 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t188 = 0.1e1 + t187
  t189 = t188 <= f.p.zeta_threshold
  t190 = t188 ** (0.1e1 / 0.3e1)
  t191 = t190 ** 2
  t192 = 0.1e1 / t191
  t194 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t195 = t194 ** 2
  t199 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t203 = f.my_piecewise3(t189, 0, 0.4e1 / 0.9e1 * t192 * t195 + 0.4e1 / 0.3e1 * t190 * t199)
  t205 = jnp.sqrt(s2)
  t206 = r1 ** (0.1e1 / 0.3e1)
  t209 = t205 / t206 / r1
  t213 = jnp.log(0.1e1 + t56 * t209 / 0.12e2)
  t221 = 0.1e1 - t50 * t209 * t213 / (params.c * t213 + 0.1e1) / 0.12e2
  t227 = f.my_piecewise3(t189, 0, 0.4e1 / 0.3e1 * t190 * t194)
  t233 = f.my_piecewise3(t189, t118, t190 * t188)
  t239 = f.my_piecewise3(t186, 0, -0.3e1 / 0.8e1 * t5 * t203 * t42 * t221 - t5 * t227 * t76 * t221 / 0.4e1 + t5 * t233 * t122 * t221 / 0.12e2)
  t249 = t24 ** 2
  t253 = 0.6e1 * t33 - 0.6e1 * t16 / t249
  t254 = f.my_piecewise5(t10, 0, t14, 0, t253)
  t258 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t254)
  t281 = 0.1e1 / t75 / t24
  t300 = 0.1e1 / t94 / t138 / r0
  t310 = 0.1e1 / t138 / t93
  t311 = t310 * t156
  t319 = t150 * t151 * t310
  t324 = s0 ** 2
  t325 = t138 ** 2
  t328 = t324 / t52 / t325
  t329 = t150 * t328
  t331 = 0.1e1 / t155 / t59
  t339 = t331 * t107 * params.c * t45 * t49
  t345 = t331 * t167 * t169 * t45 * t49
  t349 = t150 * t328 * t60
  t350 = t106 ** 2
  t363 = 0.70e2 / 0.81e2 * t50 * t51 / t52 / t138 * t64 + 0.119e3 / 0.81e2 * t92 * s0 * t300 * t99 - 0.119e3 / 0.81e2 * t104 * t300 * t60 * t109 - 0.11e2 / 0.27e2 * t152 * t311 * t63 - 0.22e2 / 0.27e2 * t152 * t311 * t108 + 0.22e2 / 0.27e2 * t319 * t171 + 0.11e2 / 0.27e2 * t319 * t176 + 0.2e1 / 0.243e3 * t329 * t331 * t63 * t56 + 0.2e1 / 0.81e2 * t329 * t339 + 0.2e1 / 0.81e2 * t329 * t345 - 0.2e1 / 0.81e2 * t349 / t350 * t169 * params.c * t331 * t45 * t49 - 0.2e1 / 0.81e2 * t349 * t345 - 0.2e1 / 0.243e3 * t349 * t339
  t368 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t258 * t42 * t68 - 0.3e1 / 0.8e1 * t5 * t41 * t76 * t68 - 0.9e1 / 0.8e1 * t5 * t43 * t113 + t5 * t74 * t122 * t68 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t77 * t113 - 0.9e1 / 0.8e1 * t5 * t81 * t179 - 0.5e1 / 0.36e2 * t5 * t120 * t281 * t68 + t5 * t123 * t113 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t127 * t179 - 0.3e1 / 0.8e1 * t5 * t131 * t363)
  t378 = f.my_piecewise5(t14, 0, t10, 0, -t253)
  t382 = f.my_piecewise3(t189, 0, -0.8e1 / 0.27e2 / t191 / t188 * t195 * t194 + 0.4e1 / 0.3e1 * t192 * t194 * t199 + 0.4e1 / 0.3e1 * t190 * t378)
  t400 = f.my_piecewise3(t186, 0, -0.3e1 / 0.8e1 * t5 * t382 * t42 * t221 - 0.3e1 / 0.8e1 * t5 * t203 * t76 * t221 + t5 * t227 * t122 * t221 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t233 * t281 * t221)
  d111 = 0.3e1 * t184 + 0.3e1 * t239 + t6 * (t368 + t400)

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
  t62 = params.alphaoAx * t57 * t61
  t63 = jnp.sqrt(s0)
  t64 = r0 ** (0.1e1 / 0.3e1)
  t67 = t63 / t64 / r0
  t68 = t57 * t61
  t71 = 0.1e1 + t68 * t67 / 0.12e2
  t72 = jnp.log(t71)
  t74 = params.c * t72 + 0.1e1
  t75 = 0.1e1 / t74
  t76 = t72 * t75
  t80 = 0.1e1 - t62 * t67 * t76 / 0.12e2
  t89 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t90 = t54 ** 2
  t91 = 0.1e1 / t90
  t92 = t89 * t91
  t96 = t89 * t54
  t97 = r0 ** 2
  t104 = params.alphaoAx * t56
  t105 = t60 ** 2
  t106 = 0.1e1 / t105
  t107 = t104 * t106
  t108 = t97 * r0
  t109 = t64 ** 2
  t111 = 0.1e1 / t109 / t108
  t113 = 0.1e1 / t71
  t114 = t113 * t75
  t119 = t104 * t106 * s0
  t121 = t74 ** 2
  t122 = 0.1e1 / t121
  t123 = t122 * params.c
  t124 = t123 * t113
  t128 = t62 * t63 / t64 / t97 * t76 / 0.9e1 + t107 * s0 * t111 * t114 / 0.18e2 - t119 * t111 * t72 * t124 / 0.18e2
  t134 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t136 = 0.1e1 / t90 / t6
  t137 = t134 * t136
  t141 = t134 * t91
  t145 = t134 * t54
  t152 = t97 ** 2
  t154 = 0.1e1 / t109 / t152
  t164 = params.alphaoAx / t59
  t165 = t63 * s0
  t166 = t164 * t165
  t167 = t152 * t97
  t168 = 0.1e1 / t167
  t169 = t71 ** 2
  t170 = 0.1e1 / t169
  t171 = t168 * t170
  t179 = t164 * t165 * t168
  t181 = 0.1e1 / t121 / t74
  t183 = params.c ** 2
  t185 = t72 * t181 * t183 * t170
  t190 = t72 * t122 * params.c * t170
  t193 = -0.7e1 / 0.27e2 * t62 * t63 / t64 / t108 * t76 - 0.5e1 / 0.18e2 * t107 * s0 * t154 * t114 + 0.5e1 / 0.18e2 * t119 * t154 * t72 * t124 + t166 * t171 * t75 / 0.27e2 + 0.2e1 / 0.27e2 * t166 * t171 * t123 - 0.2e1 / 0.27e2 * t179 * t185 - t179 * t190 / 0.27e2
  t197 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t198 = t197 * f.p.zeta_threshold
  t200 = f.my_piecewise3(t20, t198, t21 * t19)
  t202 = 0.1e1 / t90 / t25
  t203 = t200 * t202
  t207 = t200 * t136
  t211 = t200 * t91
  t215 = t200 * t54
  t222 = t152 * r0
  t224 = 0.1e1 / t109 / t222
  t234 = 0.1e1 / t152 / t108
  t235 = t234 * t170
  t243 = t164 * t165 * t234
  t248 = s0 ** 2
  t249 = t152 ** 2
  t252 = t248 / t64 / t249
  t253 = t164 * t252
  t255 = 0.1e1 / t169 / t71
  t257 = t255 * t75 * t68
  t263 = t255 * t122 * params.c * t57 * t61
  t269 = t255 * t181 * t183 * t57 * t61
  t273 = t164 * t252 * t72
  t274 = t121 ** 2
  t277 = 0.1e1 / t274 * t183 * params.c
  t280 = t277 * t255 * t57 * t61
  t287 = 0.70e2 / 0.81e2 * t62 * t63 / t64 / t152 * t76 + 0.119e3 / 0.81e2 * t107 * s0 * t224 * t114 - 0.119e3 / 0.81e2 * t119 * t224 * t72 * t124 - 0.11e2 / 0.27e2 * t166 * t235 * t75 - 0.22e2 / 0.27e2 * t166 * t235 * t123 + 0.22e2 / 0.27e2 * t243 * t185 + 0.11e2 / 0.27e2 * t243 * t190 + 0.2e1 / 0.243e3 * t253 * t257 + 0.2e1 / 0.81e2 * t253 * t263 + 0.2e1 / 0.81e2 * t253 * t269 - 0.2e1 / 0.81e2 * t273 * t280 - 0.2e1 / 0.81e2 * t273 * t269 - 0.2e1 / 0.243e3 * t273 * t263
  t292 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t80 - 0.3e1 / 0.8e1 * t5 * t92 * t80 - 0.9e1 / 0.8e1 * t5 * t96 * t128 + t5 * t137 * t80 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t141 * t128 - 0.9e1 / 0.8e1 * t5 * t145 * t193 - 0.5e1 / 0.36e2 * t5 * t203 * t80 + t5 * t207 * t128 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t211 * t193 - 0.3e1 / 0.8e1 * t5 * t215 * t287)
  t294 = r1 <= f.p.dens_threshold
  t295 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t296 = 0.1e1 + t295
  t297 = t296 <= f.p.zeta_threshold
  t298 = t296 ** (0.1e1 / 0.3e1)
  t299 = t298 ** 2
  t301 = 0.1e1 / t299 / t296
  t303 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t304 = t303 ** 2
  t308 = 0.1e1 / t299
  t309 = t308 * t303
  t311 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t315 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t319 = f.my_piecewise3(t297, 0, -0.8e1 / 0.27e2 * t301 * t304 * t303 + 0.4e1 / 0.3e1 * t309 * t311 + 0.4e1 / 0.3e1 * t298 * t315)
  t321 = jnp.sqrt(s2)
  t322 = r1 ** (0.1e1 / 0.3e1)
  t325 = t321 / t322 / r1
  t329 = jnp.log(0.1e1 + t68 * t325 / 0.12e2)
  t337 = 0.1e1 - t62 * t325 * t329 / (params.c * t329 + 0.1e1) / 0.12e2
  t346 = f.my_piecewise3(t297, 0, 0.4e1 / 0.9e1 * t308 * t304 + 0.4e1 / 0.3e1 * t298 * t311)
  t353 = f.my_piecewise3(t297, 0, 0.4e1 / 0.3e1 * t298 * t303)
  t359 = f.my_piecewise3(t297, t198, t298 * t296)
  t365 = f.my_piecewise3(t294, 0, -0.3e1 / 0.8e1 * t5 * t319 * t54 * t337 - 0.3e1 / 0.8e1 * t5 * t346 * t91 * t337 + t5 * t353 * t136 * t337 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t359 * t202 * t337)
  t388 = t63 * t248 / t109 / t249 / t97
  t389 = t164 * t388
  t390 = t169 ** 2
  t391 = 0.1e1 / t390
  t403 = 0.1e1 / t249
  t405 = t164 * t165 * t403
  t413 = t248 / t64 / t249 / r0
  t414 = t164 * t413
  t418 = t164 * t388 * t72
  t421 = t183 ** 2
  t424 = t391 * t56 * t106
  t428 = t277 * t424
  t432 = t181 * t183 * t424
  t435 = t123 * t424
  t439 = t164 * t413 * t72
  t448 = 0.1e1 / t109 / t167
  t453 = t403 * t170
  t474 = 0.116e3 / 0.243e3 * t439 * t269 + 0.116e3 / 0.729e3 * t439 * t263 - 0.721e3 / 0.81e2 * t107 * s0 * t448 * t114 + 0.1862e4 / 0.243e3 * t166 * t453 * t123 + 0.931e3 / 0.243e3 * t166 * t453 * t75 + 0.721e3 / 0.81e2 * t119 * t448 * t72 * t124 - 0.116e3 / 0.243e3 * t414 * t263 - 0.116e3 / 0.243e3 * t414 * t269 + 0.44e2 / 0.729e3 * t389 * t435 + 0.8e1 / 0.81e2 * t389 * t432 + 0.16e2 / 0.243e3 * t389 * t428
  t479 = t19 ** 2
  t482 = t30 ** 2
  t488 = t41 ** 2
  t497 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t498 = f.my_piecewise5(t10, 0, t14, 0, t497)
  t502 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t479 * t482 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t488 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t498)
  t529 = 0.1e1 / t90 / t36
  t534 = t5 * t137 * t128 - 0.3e1 / 0.2e1 * t5 * t141 * t193 - 0.3e1 / 0.2e1 * t5 * t145 * t287 - 0.5e1 / 0.9e1 * t5 * t203 * t128 + t5 * t207 * t193 / 0.2e1 - t5 * t211 * t287 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t215 * (0.4e1 / 0.243e3 * t389 * t391 * t75 * t56 * t106 - 0.910e3 / 0.243e3 * t62 * t63 / t64 / t222 * t76 - 0.1862e4 / 0.243e3 * t405 * t185 - 0.931e3 / 0.243e3 * t405 * t190 - 0.116e3 / 0.729e3 * t414 * t257 - 0.16e2 / 0.243e3 * t418 / t274 / t74 * t421 * t424 - 0.8e1 / 0.81e2 * t418 * t428 - 0.44e2 / 0.729e3 * t418 * t432 - 0.4e1 / 0.243e3 * t418 * t435 + 0.116e3 / 0.243e3 * t439 * t280 + t474) - 0.3e1 / 0.8e1 * t5 * t502 * t54 * t80 - 0.3e1 / 0.2e1 * t5 * t55 * t128 - 0.3e1 / 0.2e1 * t5 * t92 * t128 - 0.9e1 / 0.4e1 * t5 * t96 * t193 - t5 * t53 * t91 * t80 / 0.2e1 + t5 * t89 * t136 * t80 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t134 * t202 * t80 + 0.10e2 / 0.27e2 * t5 * t200 * t529 * t80
  t535 = f.my_piecewise3(t1, 0, t534)
  t536 = t296 ** 2
  t539 = t304 ** 2
  t545 = t311 ** 2
  t551 = f.my_piecewise5(t14, 0, t10, 0, -t497)
  t555 = f.my_piecewise3(t297, 0, 0.40e2 / 0.81e2 / t299 / t536 * t539 - 0.16e2 / 0.9e1 * t301 * t304 * t311 + 0.4e1 / 0.3e1 * t308 * t545 + 0.16e2 / 0.9e1 * t309 * t315 + 0.4e1 / 0.3e1 * t298 * t551)
  t577 = f.my_piecewise3(t294, 0, -0.3e1 / 0.8e1 * t5 * t555 * t54 * t337 - t5 * t319 * t91 * t337 / 0.2e1 + t5 * t346 * t136 * t337 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t353 * t202 * t337 + 0.10e2 / 0.27e2 * t5 * t359 * t529 * t337)
  d1111 = 0.4e1 * t292 + 0.4e1 * t365 + t6 * (t535 + t577)

  res = {'v4rho4': d1111}
  return res
