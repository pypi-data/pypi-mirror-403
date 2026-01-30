"""Generated from gga_k_lkt.mpl."""

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

  lkt_f0 = lambda s: 1 / jnp.cosh(params_a * jnp.minimum(200, s)) + 5 * s ** 2 / 3

  lkt_f = lambda x: lkt_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lkt_f, rs, z, xs0, xs1)

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

  lkt_f0 = lambda s: 1 / jnp.cosh(params_a * jnp.minimum(200, s)) + 5 * s ** 2 / 3

  lkt_f = lambda x: lkt_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lkt_f, rs, z, xs0, xs1)

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

  lkt_f0 = lambda s: 1 / jnp.cosh(params_a * jnp.minimum(200, s)) + 5 * s ** 2 / 3

  lkt_f = lambda x: lkt_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lkt_f, rs, z, xs0, xs1)

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
  t33 = t32 ** 2
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t37 = t33 / t35
  t38 = jnp.sqrt(s0)
  t39 = r0 ** (0.1e1 / 0.3e1)
  t41 = 0.1e1 / t39 / r0
  t44 = t37 * t38 * t41 / 0.12e2
  t45 = t44 < 0.200e3
  t46 = f.my_piecewise3(t45, t44, 200)
  t47 = params.a * t46
  t48 = jnp.cosh(t47)
  t50 = t35 ** 2
  t52 = t32 / t50
  t53 = r0 ** 2
  t54 = t39 ** 2
  t56 = 0.1e1 / t54 / t53
  t60 = 0.1e1 / t48 + 0.5e1 / 0.72e2 * t52 * s0 * t56
  t64 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t60)
  t65 = r1 <= f.p.dens_threshold
  t66 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t67 = 0.1e1 + t66
  t68 = t67 <= f.p.zeta_threshold
  t69 = t67 ** (0.1e1 / 0.3e1)
  t70 = t69 ** 2
  t72 = f.my_piecewise3(t68, t24, t70 * t67)
  t73 = t72 * t30
  t74 = jnp.sqrt(s2)
  t75 = r1 ** (0.1e1 / 0.3e1)
  t77 = 0.1e1 / t75 / r1
  t80 = t37 * t74 * t77 / 0.12e2
  t81 = t80 < 0.200e3
  t82 = f.my_piecewise3(t81, t80, 200)
  t83 = params.a * t82
  t84 = jnp.cosh(t83)
  t86 = r1 ** 2
  t87 = t75 ** 2
  t89 = 0.1e1 / t87 / t86
  t93 = 0.1e1 / t84 + 0.5e1 / 0.72e2 * t52 * s2 * t89
  t97 = f.my_piecewise3(t65, 0, 0.3e1 / 0.20e2 * t6 * t73 * t93)
  t98 = t7 ** 2
  t100 = t17 / t98
  t101 = t8 - t100
  t102 = f.my_piecewise5(t11, 0, t15, 0, t101)
  t105 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t102)
  t110 = 0.1e1 / t29
  t114 = t6 * t28 * t110 * t60 / 0.10e2
  t115 = t48 ** 2
  t117 = jnp.sinh(t47)
  t118 = 0.1e1 / t115 * t117
  t124 = f.my_piecewise3(t45, -t37 * t38 / t39 / t53 / 0.9e1, 0)
  t138 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t105 * t30 * t60 + t114 + 0.3e1 / 0.20e2 * t6 * t31 * (-t118 * params.a * t124 - 0.5e1 / 0.27e2 * t52 * s0 / t54 / t53 / r0))
  t140 = f.my_piecewise5(t15, 0, t11, 0, -t101)
  t143 = f.my_piecewise3(t68, 0, 0.5e1 / 0.3e1 * t70 * t140)
  t151 = t6 * t72 * t110 * t93 / 0.10e2
  t153 = f.my_piecewise3(t65, 0, 0.3e1 / 0.20e2 * t6 * t143 * t30 * t93 + t151)
  vrho_0_ = t64 + t97 + t7 * (t138 + t153)
  t156 = -t8 - t100
  t157 = f.my_piecewise5(t11, 0, t15, 0, t156)
  t160 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t157)
  t166 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t160 * t30 * t60 + t114)
  t168 = f.my_piecewise5(t15, 0, t11, 0, -t156)
  t171 = f.my_piecewise3(t68, 0, 0.5e1 / 0.3e1 * t70 * t168)
  t176 = t84 ** 2
  t178 = jnp.sinh(t83)
  t179 = 0.1e1 / t176 * t178
  t185 = f.my_piecewise3(t81, -t37 * t74 / t75 / t86 / 0.9e1, 0)
  t199 = f.my_piecewise3(t65, 0, 0.3e1 / 0.20e2 * t6 * t171 * t30 * t93 + t151 + 0.3e1 / 0.20e2 * t6 * t73 * (-t179 * params.a * t185 - 0.5e1 / 0.27e2 * t52 * s2 / t87 / t86 / r1))
  vrho_1_ = t64 + t97 + t7 * (t166 + t199)
  t206 = f.my_piecewise3(t45, t37 / t38 * t41 / 0.24e2, 0)
  t215 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (-t118 * params.a * t206 + 0.5e1 / 0.72e2 * t52 * t56))
  vsigma_0_ = t7 * t215
  vsigma_1_ = 0.0e0
  t220 = f.my_piecewise3(t81, t37 / t74 * t77 / 0.24e2, 0)
  t229 = f.my_piecewise3(t65, 0, 0.3e1 / 0.20e2 * t6 * t73 * (-t179 * params.a * t220 + 0.5e1 / 0.72e2 * t52 * t89))
  vsigma_2_ = t7 * t229
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

  lkt_f0 = lambda s: 1 / jnp.cosh(params_a * jnp.minimum(200, s)) + 5 * s ** 2 / 3

  lkt_f = lambda x: lkt_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, lkt_f, rs, z, xs0, xs1)

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
  t25 = t24 ** 2
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t29 = t25 / t27
  t30 = jnp.sqrt(s0)
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t30 * t31
  t34 = 0.1e1 / t21 / r0
  t37 = t29 * t32 * t34 / 0.12e2
  t38 = t37 < 0.200e3
  t39 = f.my_piecewise3(t38, t37, 200)
  t40 = params.a * t39
  t41 = jnp.cosh(t40)
  t43 = t27 ** 2
  t45 = t24 / t43
  t46 = t31 ** 2
  t47 = s0 * t46
  t48 = r0 ** 2
  t50 = 0.1e1 / t22 / t48
  t54 = 0.1e1 / t41 + 0.5e1 / 0.72e2 * t45 * t47 * t50
  t58 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t54)
  t64 = t41 ** 2
  t66 = jnp.sinh(t40)
  t67 = 0.1e1 / t64 * t66
  t73 = f.my_piecewise3(t38, -t29 * t32 / t21 / t48 / 0.9e1, 0)
  t87 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t54 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-t67 * params.a * t73 - 0.5e1 / 0.27e2 * t45 * t47 / t22 / t48 / r0))
  vrho_0_ = 0.2e1 * r0 * t87 + 0.2e1 * t58
  t95 = f.my_piecewise3(t38, t29 / t30 * t31 * t34 / 0.24e2, 0)
  t105 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (-t67 * params.a * t95 + 0.5e1 / 0.72e2 * t45 * t46 * t50))
  vsigma_0_ = 0.2e1 * r0 * t105
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
  t25 = t24 ** 2
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t29 = t25 / t27
  t30 = jnp.sqrt(s0)
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t30 * t31
  t34 = 0.1e1 / t21 / r0
  t37 = t29 * t32 * t34 / 0.12e2
  t38 = t37 < 0.200e3
  t39 = f.my_piecewise3(t38, t37, 200)
  t40 = params.a * t39
  t41 = jnp.cosh(t40)
  t42 = 0.1e1 / t41
  t43 = t27 ** 2
  t45 = t24 / t43
  t46 = t31 ** 2
  t47 = s0 * t46
  t48 = r0 ** 2
  t49 = t21 ** 2
  t51 = 0.1e1 / t49 / t48
  t55 = t42 + 0.5e1 / 0.72e2 * t45 * t47 * t51
  t59 = t20 * t49
  t60 = t41 ** 2
  t62 = jnp.sinh(t40)
  t63 = 0.1e1 / t60 * t62
  t65 = 0.1e1 / t21 / t48
  t69 = f.my_piecewise3(t38, -t29 * t32 * t65 / 0.9e1, 0)
  t72 = t48 * r0
  t74 = 0.1e1 / t49 / t72
  t78 = -t63 * params.a * t69 - 0.5e1 / 0.27e2 * t45 * t47 * t74
  t83 = f.my_piecewise3(t2, 0, t7 * t23 * t55 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t59 * t78)
  t94 = t62 ** 2
  t95 = 0.1e1 / t60 / t41 * t94
  t96 = params.a ** 2
  t97 = t69 ** 2
  t101 = t42 * t96
  t108 = f.my_piecewise3(t38, 0.7e1 / 0.27e2 * t29 * t32 / t21 / t72, 0)
  t111 = t48 ** 2
  t122 = f.my_piecewise3(t2, 0, -t7 * t20 * t34 * t55 / 0.30e2 + t7 * t23 * t78 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t59 * (0.2e1 * t95 * t96 * t97 - t101 * t97 - t63 * params.a * t108 + 0.55e2 / 0.81e2 * t45 * t47 / t49 / t111))
  v2rho2_0_ = 0.2e1 * r0 * t122 + 0.4e1 * t83
  t126 = 0.1e1 / t30 * t31
  t130 = f.my_piecewise3(t38, t29 * t126 * t34 / 0.24e2, 0)
  t136 = -t63 * params.a * t130 + 0.5e1 / 0.72e2 * t45 * t46 * t51
  t140 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t59 * t136)
  t153 = f.my_piecewise3(t38, -t29 * t126 * t65 / 0.18e2, 0)
  t164 = f.my_piecewise3(t2, 0, t7 * t23 * t136 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t59 * (0.2e1 * t95 * t96 * t130 * t69 - t101 * t69 * t130 - t63 * params.a * t153 - 0.5e1 / 0.27e2 * t45 * t46 * t74))
  v2rhosigma_0_ = 0.2e1 * r0 * t164 + 0.2e1 * t140
  t167 = t130 ** 2
  t178 = f.my_piecewise3(t38, -t29 / t30 / s0 * t31 * t34 / 0.48e2, 0)
  t185 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t59 * (0.2e1 * t95 * t96 * t167 - t63 * params.a * t178 - t101 * t167))
  v2sigma2_0_ = 0.2e1 * r0 * t185
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
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t30 = t26 / t28
  t31 = jnp.sqrt(s0)
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t31 * t32
  t36 = t30 * t33 * t23 / 0.12e2
  t37 = t36 < 0.200e3
  t38 = f.my_piecewise3(t37, t36, 200)
  t39 = params.a * t38
  t40 = jnp.cosh(t39)
  t41 = 0.1e1 / t40
  t42 = t28 ** 2
  t44 = t25 / t42
  t45 = t32 ** 2
  t46 = s0 * t45
  t47 = r0 ** 2
  t48 = t21 ** 2
  t54 = t41 + 0.5e1 / 0.72e2 * t44 * t46 / t48 / t47
  t59 = t20 / t21
  t60 = t40 ** 2
  t62 = jnp.sinh(t39)
  t63 = 0.1e1 / t60 * t62
  t65 = 0.1e1 / t21 / t47
  t69 = f.my_piecewise3(t37, -t30 * t33 * t65 / 0.9e1, 0)
  t72 = t47 * r0
  t78 = -t63 * params.a * t69 - 0.5e1 / 0.27e2 * t44 * t46 / t48 / t72
  t82 = t20 * t48
  t85 = t62 ** 2
  t86 = 0.1e1 / t60 / t40 * t85
  t87 = params.a ** 2
  t88 = t69 ** 2
  t92 = t41 * t87
  t99 = f.my_piecewise3(t37, 0.7e1 / 0.27e2 * t30 * t33 / t21 / t72, 0)
  t102 = t47 ** 2
  t108 = 0.2e1 * t86 * t87 * t88 - t92 * t88 - t63 * params.a * t99 + 0.55e2 / 0.81e2 * t44 * t46 / t48 / t102
  t113 = f.my_piecewise3(t2, 0, -t7 * t24 * t54 / 0.30e2 + t7 * t59 * t78 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t82 * t108)
  t125 = t60 ** 2
  t131 = t87 * params.a * t88 * t69
  t148 = f.my_piecewise3(t37, -0.70e2 / 0.81e2 * t30 * t33 / t21 / t102, 0)
  t162 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t65 * t54 - t7 * t24 * t78 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t59 * t108 + 0.3e1 / 0.20e2 * t7 * t82 * (-0.6e1 / t125 * t85 * t62 * t131 + 0.5e1 * t63 * t131 + 0.6e1 * t86 * t87 * t69 * t99 - 0.3e1 * t92 * t69 * t99 - t63 * params.a * t148 - 0.770e3 / 0.243e3 * t44 * t46 / t48 / t102 / r0))
  v3rho3_0_ = 0.2e1 * r0 * t162 + 0.6e1 * t113

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
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t31 = t27 / t29
  t32 = jnp.sqrt(s0)
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t32 * t33
  t36 = 0.1e1 / t22 / r0
  t39 = t31 * t34 * t36 / 0.12e2
  t40 = t39 < 0.200e3
  t41 = f.my_piecewise3(t40, t39, 200)
  t42 = params.a * t41
  t43 = jnp.cosh(t42)
  t44 = 0.1e1 / t43
  t45 = t29 ** 2
  t47 = t26 / t45
  t48 = t33 ** 2
  t49 = s0 * t48
  t50 = t22 ** 2
  t56 = t44 + 0.5e1 / 0.72e2 * t47 * t49 / t50 / t21
  t60 = t20 * t36
  t61 = t43 ** 2
  t63 = jnp.sinh(t42)
  t64 = 0.1e1 / t61 * t63
  t68 = f.my_piecewise3(t40, -t31 * t34 * t24 / 0.9e1, 0)
  t71 = t21 * r0
  t77 = -t64 * params.a * t68 - 0.5e1 / 0.27e2 * t47 * t49 / t50 / t71
  t82 = t20 / t22
  t85 = t63 ** 2
  t86 = 0.1e1 / t61 / t43 * t85
  t87 = params.a ** 2
  t88 = t68 ** 2
  t92 = t44 * t87
  t95 = 0.1e1 / t22 / t71
  t99 = f.my_piecewise3(t40, 0.7e1 / 0.27e2 * t31 * t34 * t95, 0)
  t102 = t21 ** 2
  t108 = 0.2e1 * t86 * t87 * t88 - t92 * t88 - t64 * params.a * t99 + 0.55e2 / 0.81e2 * t47 * t49 / t50 / t102
  t112 = t20 * t50
  t113 = t61 ** 2
  t116 = 0.1e1 / t113 * t85 * t63
  t117 = t87 * params.a
  t119 = t117 * t88 * t68
  t124 = t87 * t68
  t136 = f.my_piecewise3(t40, -0.70e2 / 0.81e2 * t31 * t34 / t22 / t102, 0)
  t139 = t102 * r0
  t145 = -0.6e1 * t116 * t119 + 0.5e1 * t64 * t119 + 0.6e1 * t86 * t124 * t99 - 0.3e1 * t92 * t68 * t99 - t64 * params.a * t136 - 0.770e3 / 0.243e3 * t47 * t49 / t50 / t139
  t150 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t56 - t7 * t60 * t77 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t82 * t108 + 0.3e1 / 0.20e2 * t7 * t112 * t145)
  t167 = t85 ** 2
  t169 = t87 ** 2
  t170 = t88 ** 2
  t171 = t169 * t170
  t177 = t117 * t88 * t99
  t185 = t99 ** 2
  t202 = f.my_piecewise3(t40, 0.910e3 / 0.243e3 * t31 * t34 / t22 / t139, 0)
  t211 = 0.24e2 / t113 / t43 * t167 * t171 - 0.28e2 * t86 * t171 - 0.36e2 * t116 * t177 + 0.5e1 * t44 * t169 * t170 + 0.30e2 * t64 * t177 + 0.6e1 * t86 * t87 * t185 + 0.8e1 * t86 * t124 * t136 - 0.3e1 * t92 * t185 - 0.4e1 * t92 * t68 * t136 - t64 * params.a * t202 + 0.13090e5 / 0.729e3 * t47 * t49 / t50 / t102 / t21
  t216 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t95 * t56 + 0.8e1 / 0.45e2 * t7 * t25 * t77 - t7 * t60 * t108 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t82 * t145 + 0.3e1 / 0.20e2 * t7 * t112 * t211)
  v4rho4_0_ = 0.2e1 * r0 * t216 + 0.8e1 * t150

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
  t36 = t35 ** 2
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t40 = t36 / t38
  t41 = jnp.sqrt(s0)
  t42 = r0 ** (0.1e1 / 0.3e1)
  t47 = t40 * t41 / t42 / r0 / 0.12e2
  t48 = t47 < 0.200e3
  t49 = f.my_piecewise3(t48, t47, 200)
  t50 = params.a * t49
  t51 = jnp.cosh(t50)
  t52 = 0.1e1 / t51
  t53 = t38 ** 2
  t55 = t35 / t53
  t56 = r0 ** 2
  t57 = t42 ** 2
  t63 = t52 + 0.5e1 / 0.72e2 * t55 * s0 / t57 / t56
  t67 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t68 = t67 ** 2
  t69 = t68 * f.p.zeta_threshold
  t71 = f.my_piecewise3(t21, t69, t23 * t20)
  t72 = 0.1e1 / t32
  t73 = t71 * t72
  t76 = t6 * t73 * t63 / 0.10e2
  t77 = t71 * t33
  t78 = t51 ** 2
  t80 = jnp.sinh(t50)
  t81 = 0.1e1 / t78 * t80
  t87 = f.my_piecewise3(t48, -t40 * t41 / t42 / t56 / 0.9e1, 0)
  t90 = t56 * r0
  t96 = -t81 * params.a * t87 - 0.5e1 / 0.27e2 * t55 * s0 / t57 / t90
  t101 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t63 + t76 + 0.3e1 / 0.20e2 * t6 * t77 * t96)
  t103 = r1 <= f.p.dens_threshold
  t104 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t105 = 0.1e1 + t104
  t106 = t105 <= f.p.zeta_threshold
  t107 = t105 ** (0.1e1 / 0.3e1)
  t108 = t107 ** 2
  t110 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t113 = f.my_piecewise3(t106, 0, 0.5e1 / 0.3e1 * t108 * t110)
  t114 = t113 * t33
  t115 = jnp.sqrt(s2)
  t116 = r1 ** (0.1e1 / 0.3e1)
  t121 = t40 * t115 / t116 / r1 / 0.12e2
  t122 = t121 < 0.200e3
  t123 = f.my_piecewise3(t122, t121, 200)
  t124 = params.a * t123
  t125 = jnp.cosh(t124)
  t126 = 0.1e1 / t125
  t127 = r1 ** 2
  t128 = t116 ** 2
  t134 = t126 + 0.5e1 / 0.72e2 * t55 * s2 / t128 / t127
  t139 = f.my_piecewise3(t106, t69, t108 * t105)
  t140 = t139 * t72
  t143 = t6 * t140 * t134 / 0.10e2
  t145 = f.my_piecewise3(t103, 0, 0.3e1 / 0.20e2 * t6 * t114 * t134 + t143)
  t147 = 0.1e1 / t22
  t148 = t28 ** 2
  t153 = t17 / t24 / t7
  t155 = -0.2e1 * t25 + 0.2e1 * t153
  t156 = f.my_piecewise5(t11, 0, t15, 0, t155)
  t160 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t147 * t148 + 0.5e1 / 0.3e1 * t23 * t156)
  t167 = t6 * t31 * t72 * t63
  t173 = 0.1e1 / t32 / t7
  t177 = t6 * t71 * t173 * t63 / 0.30e2
  t179 = t6 * t73 * t96
  t183 = t80 ** 2
  t185 = params.a ** 2
  t186 = t87 ** 2
  t197 = f.my_piecewise3(t48, 0.7e1 / 0.27e2 * t40 * t41 / t42 / t90, 0)
  t200 = t56 ** 2
  t211 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t160 * t33 * t63 + t167 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t96 - t177 + t179 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t77 * (0.2e1 / t78 / t51 * t183 * t185 * t186 - t52 * t185 * t186 - t81 * params.a * t197 + 0.55e2 / 0.81e2 * t55 * s0 / t57 / t200))
  t212 = 0.1e1 / t107
  t213 = t110 ** 2
  t217 = f.my_piecewise5(t15, 0, t11, 0, -t155)
  t221 = f.my_piecewise3(t106, 0, 0.10e2 / 0.9e1 * t212 * t213 + 0.5e1 / 0.3e1 * t108 * t217)
  t228 = t6 * t113 * t72 * t134
  t233 = t6 * t139 * t173 * t134 / 0.30e2
  t235 = f.my_piecewise3(t103, 0, 0.3e1 / 0.20e2 * t6 * t221 * t33 * t134 + t228 / 0.5e1 - t233)
  d11 = 0.2e1 * t101 + 0.2e1 * t145 + t7 * (t211 + t235)
  t238 = -t8 - t26
  t239 = f.my_piecewise5(t11, 0, t15, 0, t238)
  t242 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t239)
  t243 = t242 * t33
  t248 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t243 * t63 + t76)
  t250 = f.my_piecewise5(t15, 0, t11, 0, -t238)
  t253 = f.my_piecewise3(t106, 0, 0.5e1 / 0.3e1 * t108 * t250)
  t254 = t253 * t33
  t258 = t139 * t33
  t259 = t125 ** 2
  t261 = jnp.sinh(t124)
  t262 = 0.1e1 / t259 * t261
  t268 = f.my_piecewise3(t122, -t40 * t115 / t116 / t127 / 0.9e1, 0)
  t271 = t127 * r1
  t277 = -t262 * params.a * t268 - 0.5e1 / 0.27e2 * t55 * s2 / t128 / t271
  t282 = f.my_piecewise3(t103, 0, 0.3e1 / 0.20e2 * t6 * t254 * t134 + t143 + 0.3e1 / 0.20e2 * t6 * t258 * t277)
  t286 = 0.2e1 * t153
  t287 = f.my_piecewise5(t11, 0, t15, 0, t286)
  t291 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t147 * t239 * t28 + 0.5e1 / 0.3e1 * t23 * t287)
  t298 = t6 * t242 * t72 * t63
  t306 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t291 * t33 * t63 + t298 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t243 * t96 + t167 / 0.10e2 - t177 + t179 / 0.10e2)
  t310 = f.my_piecewise5(t15, 0, t11, 0, -t286)
  t314 = f.my_piecewise3(t106, 0, 0.10e2 / 0.9e1 * t212 * t250 * t110 + 0.5e1 / 0.3e1 * t108 * t310)
  t321 = t6 * t253 * t72 * t134
  t328 = t6 * t140 * t277
  t331 = f.my_piecewise3(t103, 0, 0.3e1 / 0.20e2 * t6 * t314 * t33 * t134 + t321 / 0.10e2 + t228 / 0.10e2 - t233 + 0.3e1 / 0.20e2 * t6 * t114 * t277 + t328 / 0.10e2)
  d12 = t101 + t145 + t248 + t282 + t7 * (t306 + t331)
  t336 = t239 ** 2
  t340 = 0.2e1 * t25 + 0.2e1 * t153
  t341 = f.my_piecewise5(t11, 0, t15, 0, t340)
  t345 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t147 * t336 + 0.5e1 / 0.3e1 * t23 * t341)
  t352 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t345 * t33 * t63 + t298 / 0.5e1 - t177)
  t353 = t250 ** 2
  t357 = f.my_piecewise5(t15, 0, t11, 0, -t340)
  t361 = f.my_piecewise3(t106, 0, 0.10e2 / 0.9e1 * t212 * t353 + 0.5e1 / 0.3e1 * t108 * t357)
  t373 = t261 ** 2
  t375 = t268 ** 2
  t386 = f.my_piecewise3(t122, 0.7e1 / 0.27e2 * t40 * t115 / t116 / t271, 0)
  t389 = t127 ** 2
  t400 = f.my_piecewise3(t103, 0, 0.3e1 / 0.20e2 * t6 * t361 * t33 * t134 + t321 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t254 * t277 - t233 + t328 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t258 * (0.2e1 / t259 / t125 * t373 * t185 * t375 - t126 * t185 * t375 - t262 * params.a * t386 + 0.55e2 / 0.81e2 * t55 * s2 / t128 / t389))
  d22 = 0.2e1 * t248 + 0.2e1 * t282 + t7 * (t352 + t400)
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
  t47 = t46 ** 2
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t51 = t47 / t49
  t52 = jnp.sqrt(s0)
  t53 = r0 ** (0.1e1 / 0.3e1)
  t58 = t51 * t52 / t53 / r0 / 0.12e2
  t59 = t58 < 0.200e3
  t60 = f.my_piecewise3(t59, t58, 200)
  t61 = params.a * t60
  t62 = jnp.cosh(t61)
  t63 = 0.1e1 / t62
  t64 = t49 ** 2
  t66 = t46 / t64
  t67 = r0 ** 2
  t68 = t53 ** 2
  t74 = t63 + 0.5e1 / 0.72e2 * t66 * s0 / t68 / t67
  t80 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t81 = 0.1e1 / t43
  t82 = t80 * t81
  t86 = t80 * t44
  t87 = t62 ** 2
  t89 = jnp.sinh(t61)
  t90 = 0.1e1 / t87 * t89
  t96 = f.my_piecewise3(t59, -t51 * t52 / t53 / t67 / 0.9e1, 0)
  t99 = t67 * r0
  t105 = -t90 * params.a * t96 - 0.5e1 / 0.27e2 * t66 * s0 / t68 / t99
  t109 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t110 = t109 ** 2
  t111 = t110 * f.p.zeta_threshold
  t113 = f.my_piecewise3(t21, t111, t32 * t20)
  t115 = 0.1e1 / t43 / t7
  t116 = t113 * t115
  t120 = t113 * t81
  t124 = t113 * t44
  t127 = t89 ** 2
  t128 = 0.1e1 / t87 / t62 * t127
  t129 = params.a ** 2
  t130 = t96 ** 2
  t134 = t63 * t129
  t141 = f.my_piecewise3(t59, 0.7e1 / 0.27e2 * t51 * t52 / t53 / t99, 0)
  t144 = t67 ** 2
  t150 = 0.2e1 * t128 * t129 * t130 - t134 * t130 - t90 * params.a * t141 + 0.55e2 / 0.81e2 * t66 * s0 / t68 / t144
  t155 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t74 + t6 * t82 * t74 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t86 * t105 - t6 * t116 * t74 / 0.30e2 + t6 * t120 * t105 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t124 * t150)
  t157 = r1 <= f.p.dens_threshold
  t158 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t159 = 0.1e1 + t158
  t160 = t159 <= f.p.zeta_threshold
  t161 = t159 ** (0.1e1 / 0.3e1)
  t162 = 0.1e1 / t161
  t164 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t165 = t164 ** 2
  t168 = t161 ** 2
  t170 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t174 = f.my_piecewise3(t160, 0, 0.10e2 / 0.9e1 * t162 * t165 + 0.5e1 / 0.3e1 * t168 * t170)
  t176 = jnp.sqrt(s2)
  t177 = r1 ** (0.1e1 / 0.3e1)
  t182 = t51 * t176 / t177 / r1 / 0.12e2
  t184 = f.my_piecewise3(t182 < 0.200e3, t182, 200)
  t186 = jnp.cosh(params.a * t184)
  t188 = r1 ** 2
  t189 = t177 ** 2
  t195 = 0.1e1 / t186 + 0.5e1 / 0.72e2 * t66 * s2 / t189 / t188
  t201 = f.my_piecewise3(t160, 0, 0.5e1 / 0.3e1 * t168 * t164)
  t207 = f.my_piecewise3(t160, t111, t168 * t159)
  t213 = f.my_piecewise3(t157, 0, 0.3e1 / 0.20e2 * t6 * t174 * t44 * t195 + t6 * t201 * t81 * t195 / 0.5e1 - t6 * t207 * t115 * t195 / 0.30e2)
  t223 = t24 ** 2
  t227 = 0.6e1 * t34 - 0.6e1 * t17 / t223
  t228 = f.my_piecewise5(t11, 0, t15, 0, t227)
  t232 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t228)
  t255 = 0.1e1 / t43 / t24
  t266 = t87 ** 2
  t272 = t129 * params.a * t130 * t96
  t289 = f.my_piecewise3(t59, -0.70e2 / 0.81e2 * t51 * t52 / t53 / t144, 0)
  t303 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t232 * t44 * t74 + 0.3e1 / 0.10e2 * t6 * t42 * t81 * t74 + 0.9e1 / 0.20e2 * t6 * t45 * t105 - t6 * t80 * t115 * t74 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t82 * t105 + 0.9e1 / 0.20e2 * t6 * t86 * t150 + 0.2e1 / 0.45e2 * t6 * t113 * t255 * t74 - t6 * t116 * t105 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t120 * t150 + 0.3e1 / 0.20e2 * t6 * t124 * (-0.6e1 / t266 * t127 * t89 * t272 + 0.5e1 * t90 * t272 + 0.6e1 * t128 * t129 * t96 * t141 - 0.3e1 * t134 * t96 * t141 - t90 * params.a * t289 - 0.770e3 / 0.243e3 * t66 * s0 / t68 / t144 / r0))
  t313 = f.my_piecewise5(t15, 0, t11, 0, -t227)
  t317 = f.my_piecewise3(t160, 0, -0.10e2 / 0.27e2 / t161 / t159 * t165 * t164 + 0.10e2 / 0.3e1 * t162 * t164 * t170 + 0.5e1 / 0.3e1 * t168 * t313)
  t335 = f.my_piecewise3(t157, 0, 0.3e1 / 0.20e2 * t6 * t317 * t44 * t195 + 0.3e1 / 0.10e2 * t6 * t174 * t81 * t195 - t6 * t201 * t115 * t195 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t207 * t255 * t195)
  d111 = 0.3e1 * t155 + 0.3e1 * t213 + t7 * (t303 + t335)

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
  t59 = t58 ** 2
  t60 = jnp.pi ** 2
  t61 = t60 ** (0.1e1 / 0.3e1)
  t63 = t59 / t61
  t64 = jnp.sqrt(s0)
  t65 = r0 ** (0.1e1 / 0.3e1)
  t70 = t63 * t64 / t65 / r0 / 0.12e2
  t71 = t70 < 0.200e3
  t72 = f.my_piecewise3(t71, t70, 200)
  t73 = params.a * t72
  t74 = jnp.cosh(t73)
  t75 = 0.1e1 / t74
  t76 = t61 ** 2
  t78 = t58 / t76
  t79 = r0 ** 2
  t80 = t65 ** 2
  t86 = t75 + 0.5e1 / 0.72e2 * t78 * s0 / t80 / t79
  t95 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t96 = 0.1e1 / t55
  t97 = t95 * t96
  t101 = t95 * t56
  t102 = t74 ** 2
  t104 = jnp.sinh(t73)
  t105 = 0.1e1 / t102 * t104
  t111 = f.my_piecewise3(t71, -t63 * t64 / t65 / t79 / 0.9e1, 0)
  t114 = t79 * r0
  t120 = -t105 * params.a * t111 - 0.5e1 / 0.27e2 * t78 * s0 / t80 / t114
  t126 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t128 = 0.1e1 / t55 / t7
  t129 = t126 * t128
  t133 = t126 * t96
  t137 = t126 * t56
  t140 = t104 ** 2
  t141 = 0.1e1 / t102 / t74 * t140
  t142 = params.a ** 2
  t143 = t111 ** 2
  t147 = t75 * t142
  t154 = f.my_piecewise3(t71, 0.7e1 / 0.27e2 * t63 * t64 / t65 / t114, 0)
  t157 = t79 ** 2
  t163 = 0.2e1 * t141 * t142 * t143 - t147 * t143 - t105 * params.a * t154 + 0.55e2 / 0.81e2 * t78 * s0 / t80 / t157
  t167 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t168 = t167 ** 2
  t169 = t168 * f.p.zeta_threshold
  t171 = f.my_piecewise3(t21, t169, t44 * t20)
  t173 = 0.1e1 / t55 / t25
  t174 = t171 * t173
  t178 = t171 * t128
  t182 = t171 * t96
  t186 = t171 * t56
  t187 = t102 ** 2
  t190 = 0.1e1 / t187 * t140 * t104
  t191 = t142 * params.a
  t193 = t191 * t143 * t111
  t198 = t142 * t111
  t210 = f.my_piecewise3(t71, -0.70e2 / 0.81e2 * t63 * t64 / t65 / t157, 0)
  t213 = t157 * r0
  t219 = -0.6e1 * t190 * t193 + 0.5e1 * t105 * t193 + 0.6e1 * t141 * t198 * t154 - 0.3e1 * t147 * t111 * t154 - t105 * params.a * t210 - 0.770e3 / 0.243e3 * t78 * s0 / t80 / t213
  t224 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t86 + 0.3e1 / 0.10e2 * t6 * t97 * t86 + 0.9e1 / 0.20e2 * t6 * t101 * t120 - t6 * t129 * t86 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t133 * t120 + 0.9e1 / 0.20e2 * t6 * t137 * t163 + 0.2e1 / 0.45e2 * t6 * t174 * t86 - t6 * t178 * t120 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t182 * t163 + 0.3e1 / 0.20e2 * t6 * t186 * t219)
  t226 = r1 <= f.p.dens_threshold
  t227 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t228 = 0.1e1 + t227
  t229 = t228 <= f.p.zeta_threshold
  t230 = t228 ** (0.1e1 / 0.3e1)
  t232 = 0.1e1 / t230 / t228
  t234 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t235 = t234 ** 2
  t239 = 0.1e1 / t230
  t240 = t239 * t234
  t242 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t245 = t230 ** 2
  t247 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t251 = f.my_piecewise3(t229, 0, -0.10e2 / 0.27e2 * t232 * t235 * t234 + 0.10e2 / 0.3e1 * t240 * t242 + 0.5e1 / 0.3e1 * t245 * t247)
  t253 = jnp.sqrt(s2)
  t254 = r1 ** (0.1e1 / 0.3e1)
  t259 = t63 * t253 / t254 / r1 / 0.12e2
  t261 = f.my_piecewise3(t259 < 0.200e3, t259, 200)
  t263 = jnp.cosh(params.a * t261)
  t265 = r1 ** 2
  t266 = t254 ** 2
  t272 = 0.1e1 / t263 + 0.5e1 / 0.72e2 * t78 * s2 / t266 / t265
  t281 = f.my_piecewise3(t229, 0, 0.10e2 / 0.9e1 * t239 * t235 + 0.5e1 / 0.3e1 * t245 * t242)
  t288 = f.my_piecewise3(t229, 0, 0.5e1 / 0.3e1 * t245 * t234)
  t294 = f.my_piecewise3(t229, t169, t245 * t228)
  t300 = f.my_piecewise3(t226, 0, 0.3e1 / 0.20e2 * t6 * t251 * t56 * t272 + 0.3e1 / 0.10e2 * t6 * t281 * t96 * t272 - t6 * t288 * t128 * t272 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t294 * t173 * t272)
  t302 = t20 ** 2
  t305 = t30 ** 2
  t311 = t41 ** 2
  t320 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t321 = f.my_piecewise5(t11, 0, t15, 0, t320)
  t325 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t302 * t305 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t311 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t321)
  t359 = t140 ** 2
  t361 = t142 ** 2
  t362 = t143 ** 2
  t363 = t361 * t362
  t369 = t191 * t143 * t154
  t377 = t154 ** 2
  t394 = f.my_piecewise3(t71, 0.910e3 / 0.243e3 * t63 * t64 / t65 / t213, 0)
  t403 = 0.24e2 / t187 / t74 * t359 * t363 - 0.28e2 * t141 * t363 - 0.36e2 * t190 * t369 + 0.5e1 * t75 * t361 * t362 + 0.30e2 * t105 * t369 + 0.6e1 * t141 * t142 * t377 + 0.8e1 * t141 * t198 * t210 - 0.3e1 * t147 * t377 - 0.4e1 * t147 * t111 * t210 - t105 * params.a * t394 + 0.13090e5 / 0.729e3 * t78 * s0 / t80 / t157 / t79
  t420 = 0.1e1 / t55 / t36
  t425 = 0.3e1 / 0.20e2 * t6 * t325 * t56 * t86 + 0.3e1 / 0.5e1 * t6 * t57 * t120 + 0.6e1 / 0.5e1 * t6 * t97 * t120 + 0.9e1 / 0.10e2 * t6 * t101 * t163 - 0.2e1 / 0.5e1 * t6 * t129 * t120 + 0.6e1 / 0.5e1 * t6 * t133 * t163 + 0.3e1 / 0.5e1 * t6 * t137 * t219 + 0.8e1 / 0.45e2 * t6 * t174 * t120 - t6 * t178 * t163 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t182 * t219 + 0.3e1 / 0.20e2 * t6 * t186 * t403 + 0.2e1 / 0.5e1 * t6 * t54 * t96 * t86 - t6 * t95 * t128 * t86 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t126 * t173 * t86 - 0.14e2 / 0.135e3 * t6 * t171 * t420 * t86
  t426 = f.my_piecewise3(t1, 0, t425)
  t427 = t228 ** 2
  t430 = t235 ** 2
  t436 = t242 ** 2
  t442 = f.my_piecewise5(t15, 0, t11, 0, -t320)
  t446 = f.my_piecewise3(t229, 0, 0.40e2 / 0.81e2 / t230 / t427 * t430 - 0.20e2 / 0.9e1 * t232 * t235 * t242 + 0.10e2 / 0.3e1 * t239 * t436 + 0.40e2 / 0.9e1 * t240 * t247 + 0.5e1 / 0.3e1 * t245 * t442)
  t468 = f.my_piecewise3(t226, 0, 0.3e1 / 0.20e2 * t6 * t446 * t56 * t272 + 0.2e1 / 0.5e1 * t6 * t251 * t96 * t272 - t6 * t281 * t128 * t272 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t288 * t173 * t272 - 0.14e2 / 0.135e3 * t6 * t294 * t420 * t272)
  d1111 = 0.4e1 * t224 + 0.4e1 * t300 + t7 * (t426 + t468)

  res = {'v4rho4': d1111}
  return res
