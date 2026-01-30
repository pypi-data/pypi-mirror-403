"""Generated from mgga_k_gea4.mpl."""

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
  gea4_s = lambda x: X2S * x

  gea4_q = lambda u: X2S ** 2 * u

  gea4_f0 = lambda s, q: 1 + 5 / 27 * s ** 2 + 20 / 9 * q + 8 / 81 * q ** 2 - 1 / 9 * s ** 2 * q + 8 / 243 * s ** 4

  gea4_f = lambda x, u: gea4_f0(gea4_s(x), gea4_q(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, gea4_f, rs, z, xs0, xs1, u0, u1)

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
  gea4_s = lambda x: X2S * x

  gea4_q = lambda u: X2S ** 2 * u

  gea4_f0 = lambda s, q: 1 + 5 / 27 * s ** 2 + 20 / 9 * q + 8 / 81 * q ** 2 - 1 / 9 * s ** 2 * q + 8 / 243 * s ** 4

  gea4_f = lambda x, u: gea4_f0(gea4_s(x), gea4_q(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, gea4_f, rs, z, xs0, xs1, u0, u1)

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
  gea4_s = lambda x: X2S * x

  gea4_q = lambda u: X2S ** 2 * u

  gea4_f0 = lambda s, q: 1 + 5 / 27 * s ** 2 + 20 / 9 * q + 8 / 81 * q ** 2 - 1 / 9 * s ** 2 * q + 8 / 243 * s ** 4

  gea4_f = lambda x, u: gea4_f0(gea4_s(x), gea4_q(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, gea4_f, rs, z, xs0, xs1, u0, u1)

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
  t37 = t32 / t35
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t47 = 0.1e1 / t40 / r0
  t51 = t32 ** 2
  t54 = t51 / t34 / t33
  t55 = l0 ** 2
  t56 = t38 * r0
  t58 = 0.1e1 / t39 / t56
  t62 = t38 ** 2
  t64 = 0.1e1 / t39 / t62
  t65 = s0 * t64
  t69 = s0 ** 2
  t72 = 0.1e1 / t39 / t62 / r0
  t76 = 0.1e1 + 0.5e1 / 0.648e3 * t37 * s0 * t42 + 0.5e1 / 0.54e2 * t37 * l0 * t47 + t54 * t55 * t58 / 0.5832e4 - t54 * t65 * l0 / 0.5184e4 + t54 * t69 * t72 / 0.17496e5
  t80 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t76)
  t81 = r1 <= f.p.dens_threshold
  t82 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t83 = 0.1e1 + t82
  t84 = t83 <= f.p.zeta_threshold
  t85 = t83 ** (0.1e1 / 0.3e1)
  t86 = t85 ** 2
  t88 = f.my_piecewise3(t84, t24, t86 * t83)
  t89 = t88 * t30
  t90 = r1 ** 2
  t91 = r1 ** (0.1e1 / 0.3e1)
  t92 = t91 ** 2
  t94 = 0.1e1 / t92 / t90
  t99 = 0.1e1 / t92 / r1
  t103 = l1 ** 2
  t104 = t90 * r1
  t106 = 0.1e1 / t91 / t104
  t110 = t90 ** 2
  t112 = 0.1e1 / t91 / t110
  t113 = s2 * t112
  t117 = s2 ** 2
  t120 = 0.1e1 / t91 / t110 / r1
  t124 = 0.1e1 + 0.5e1 / 0.648e3 * t37 * s2 * t94 + 0.5e1 / 0.54e2 * t37 * l1 * t99 + t54 * t103 * t106 / 0.5832e4 - t54 * t113 * l1 / 0.5184e4 + t54 * t117 * t120 / 0.17496e5
  t128 = f.my_piecewise3(t81, 0, 0.3e1 / 0.20e2 * t6 * t89 * t124)
  t129 = t7 ** 2
  t131 = t17 / t129
  t132 = t8 - t131
  t133 = f.my_piecewise5(t11, 0, t15, 0, t132)
  t136 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t133)
  t141 = 0.1e1 / t29
  t145 = t6 * t28 * t141 * t76 / 0.10e2
  t157 = s0 * t72
  t172 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t136 * t30 * t76 + t145 + 0.3e1 / 0.20e2 * t6 * t31 * (-0.5e1 / 0.243e3 * t37 * s0 / t40 / t56 - 0.25e2 / 0.162e3 * t37 * l0 * t42 - 0.5e1 / 0.8748e4 * t54 * t55 * t64 + 0.13e2 / 0.15552e5 * t54 * t157 * l0 - 0.2e1 / 0.6561e4 * t54 * t69 / t39 / t62 / t38))
  t174 = f.my_piecewise5(t15, 0, t11, 0, -t132)
  t177 = f.my_piecewise3(t84, 0, 0.5e1 / 0.3e1 * t86 * t174)
  t185 = t6 * t88 * t141 * t124 / 0.10e2
  t187 = f.my_piecewise3(t81, 0, 0.3e1 / 0.20e2 * t6 * t177 * t30 * t124 + t185)
  vrho_0_ = t80 + t128 + t7 * (t172 + t187)
  t190 = -t8 - t131
  t191 = f.my_piecewise5(t11, 0, t15, 0, t190)
  t194 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t191)
  t200 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t194 * t30 * t76 + t145)
  t202 = f.my_piecewise5(t15, 0, t11, 0, -t190)
  t205 = f.my_piecewise3(t84, 0, 0.5e1 / 0.3e1 * t86 * t202)
  t221 = s2 * t120
  t236 = f.my_piecewise3(t81, 0, 0.3e1 / 0.20e2 * t6 * t205 * t30 * t124 + t185 + 0.3e1 / 0.20e2 * t6 * t89 * (-0.5e1 / 0.243e3 * t37 * s2 / t92 / t104 - 0.25e2 / 0.162e3 * t37 * l1 * t94 - 0.5e1 / 0.8748e4 * t54 * t103 * t112 + 0.13e2 / 0.15552e5 * t54 * t221 * l1 - 0.2e1 / 0.6561e4 * t54 * t117 / t91 / t110 / t90))
  vrho_1_ = t80 + t128 + t7 * (t200 + t236)
  t250 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.5e1 / 0.648e3 * t37 * t42 - t54 * t64 * l0 / 0.5184e4 + t54 * t157 / 0.8748e4))
  vsigma_0_ = t7 * t250
  vsigma_1_ = 0.0e0
  t262 = f.my_piecewise3(t81, 0, 0.3e1 / 0.20e2 * t6 * t89 * (0.5e1 / 0.648e3 * t37 * t94 - t54 * t112 * l1 / 0.5184e4 + t54 * t221 / 0.8748e4))
  vsigma_2_ = t7 * t262
  t274 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.5e1 / 0.54e2 * t37 * t47 + t54 * l0 * t58 / 0.2916e4 - t54 * t65 / 0.5184e4))
  vlapl_0_ = t7 * t274
  t286 = f.my_piecewise3(t81, 0, 0.3e1 / 0.20e2 * t6 * t89 * (0.5e1 / 0.54e2 * t37 * t99 + t54 * l1 * t106 / 0.2916e4 - t54 * t113 / 0.5184e4))
  vlapl_1_ = t7 * t286
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
  gea4_s = lambda x: X2S * x

  gea4_q = lambda u: X2S ** 2 * u

  gea4_f0 = lambda s, q: 1 + 5 / 27 * s ** 2 + 20 / 9 * q + 8 / 81 * q ** 2 - 1 / 9 * s ** 2 * q + 8 / 243 * s ** 4

  gea4_f = lambda x, u: gea4_f0(gea4_s(x), gea4_q(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, gea4_f, rs, z, xs0, xs1, u0, u1)

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
  t29 = t24 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t22 / t33
  t39 = l0 * t31
  t41 = 0.1e1 / t22 / r0
  t45 = t24 ** 2
  t48 = t45 / t26 / t25
  t49 = l0 ** 2
  t50 = t49 * t30
  t51 = t33 * r0
  t53 = 0.1e1 / t21 / t51
  t57 = t48 * s0
  t58 = t33 ** 2
  t60 = 0.1e1 / t21 / t58
  t62 = t30 * t60 * l0
  t65 = s0 ** 2
  t66 = t65 * t30
  t69 = 0.1e1 / t21 / t58 / r0
  t73 = 0.1e1 + 0.5e1 / 0.648e3 * t29 * t32 * t35 + 0.5e1 / 0.54e2 * t29 * t39 * t41 + t48 * t50 * t53 / 0.2916e4 - t57 * t62 / 0.2592e4 + t48 * t66 * t69 / 0.8748e4
  t77 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t73)
  t109 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t73 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-0.5e1 / 0.243e3 * t29 * t32 / t22 / t51 - 0.25e2 / 0.162e3 * t29 * t39 * t35 - 0.5e1 / 0.4374e4 * t48 * t50 * t60 + 0.13e2 / 0.7776e4 * t57 * t30 * t69 * l0 - 0.4e1 / 0.6561e4 * t48 * t66 / t21 / t58 / t33))
  vrho_0_ = 0.2e1 * r0 * t109 + 0.2e1 * t77
  t117 = s0 * t30
  t125 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.5e1 / 0.648e3 * t29 * t31 * t35 - t48 * t62 / 0.2592e4 + t48 * t117 * t69 / 0.4374e4))
  vsigma_0_ = 0.2e1 * r0 * t125
  t141 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.5e1 / 0.54e2 * t29 * t31 * t41 + t48 * l0 * t30 * t53 / 0.1458e4 - t48 * t117 * t60 / 0.2592e4))
  vlapl_0_ = 0.2e1 * r0 * t141
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
  t29 = t24 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t34 = t21 ** 2
  t36 = 0.1e1 / t34 / t33
  t40 = l0 * t31
  t46 = t24 ** 2
  t49 = t46 / t26 / t25
  t50 = l0 ** 2
  t51 = t50 * t30
  t52 = t33 * r0
  t58 = t49 * s0
  t59 = t33 ** 2
  t61 = 0.1e1 / t21 / t59
  t66 = s0 ** 2
  t67 = t66 * t30
  t70 = 0.1e1 / t21 / t59 / r0
  t74 = 0.1e1 + 0.5e1 / 0.648e3 * t29 * t32 * t36 + 0.5e1 / 0.54e2 * t29 * t40 / t34 / r0 + t49 * t51 / t21 / t52 / 0.2916e4 - t58 * t30 * t61 * l0 / 0.2592e4 + t49 * t67 * t70 / 0.8748e4
  t78 = t20 * t34
  t80 = 0.1e1 / t34 / t52
  t96 = 0.1e1 / t21 / t59 / t33
  t100 = -0.5e1 / 0.243e3 * t29 * t32 * t80 - 0.25e2 / 0.162e3 * t29 * t40 * t36 - 0.5e1 / 0.4374e4 * t49 * t51 * t61 + 0.13e2 / 0.7776e4 * t58 * t30 * t70 * l0 - 0.4e1 / 0.6561e4 * t49 * t67 * t96
  t105 = f.my_piecewise3(t2, 0, t7 * t23 * t74 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t78 * t100)
  t142 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t74 / 0.30e2 + t7 * t23 * t100 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t78 * (0.55e2 / 0.729e3 * t29 * t32 / t34 / t59 + 0.100e3 / 0.243e3 * t29 * t40 * t80 + 0.65e2 / 0.13122e5 * t49 * t51 * t70 - 0.13e2 / 0.1458e4 * t58 * t30 * t96 * l0 + 0.76e2 / 0.19683e5 * t49 * t67 / t21 / t59 / t52))
  v2rho2_0_ = 0.2e1 * r0 * t142 + 0.4e1 * t105
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
  t30 = t25 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t37 = 0.1e1 / t35 / t34
  t41 = l0 * t32
  t47 = t25 ** 2
  t50 = t47 / t27 / t26
  t51 = l0 ** 2
  t52 = t51 * t31
  t53 = t34 * r0
  t59 = t50 * s0
  t60 = t34 ** 2
  t62 = 0.1e1 / t21 / t60
  t67 = s0 ** 2
  t68 = t67 * t31
  t69 = t60 * r0
  t71 = 0.1e1 / t21 / t69
  t75 = 0.1e1 + 0.5e1 / 0.648e3 * t30 * t33 * t37 + 0.5e1 / 0.54e2 * t30 * t41 / t35 / r0 + t50 * t52 / t21 / t53 / 0.2916e4 - t59 * t31 * t62 * l0 / 0.2592e4 + t50 * t68 * t71 / 0.8748e4
  t80 = t20 / t21
  t82 = 0.1e1 / t35 / t53
  t98 = 0.1e1 / t21 / t60 / t34
  t102 = -0.5e1 / 0.243e3 * t30 * t33 * t82 - 0.25e2 / 0.162e3 * t30 * t41 * t37 - 0.5e1 / 0.4374e4 * t50 * t52 * t62 + 0.13e2 / 0.7776e4 * t59 * t31 * t71 * l0 - 0.4e1 / 0.6561e4 * t50 * t68 * t98
  t106 = t20 * t35
  t108 = 0.1e1 / t35 / t60
  t124 = 0.1e1 / t21 / t60 / t53
  t128 = 0.55e2 / 0.729e3 * t30 * t33 * t108 + 0.100e3 / 0.243e3 * t30 * t41 * t82 + 0.65e2 / 0.13122e5 * t50 * t52 * t71 - 0.13e2 / 0.1458e4 * t59 * t31 * t98 * l0 + 0.76e2 / 0.19683e5 * t50 * t68 * t124
  t133 = f.my_piecewise3(t2, 0, -t7 * t24 * t75 / 0.30e2 + t7 * t80 * t102 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t106 * t128)
  t162 = t60 ** 2
  t173 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t75 - t7 * t24 * t102 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t80 * t128 + 0.3e1 / 0.20e2 * t7 * t106 * (-0.770e3 / 0.2187e4 * t30 * t33 / t35 / t69 - 0.1100e4 / 0.729e3 * t30 * t41 * t108 - 0.520e3 / 0.19683e5 * t50 * t52 * t98 + 0.247e3 / 0.4374e4 * t59 * t31 * t124 * l0 - 0.1672e4 / 0.59049e5 * t50 * t68 / t21 / t162))
  v3rho3_0_ = 0.2e1 * r0 * t173 + 0.6e1 * t133

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
  t31 = t26 / t29
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = t22 ** 2
  t37 = 0.1e1 / t35 / t21
  t41 = l0 * t33
  t47 = t26 ** 2
  t50 = t47 / t28 / t27
  t51 = l0 ** 2
  t52 = t51 * t32
  t53 = t21 * r0
  t55 = 0.1e1 / t22 / t53
  t59 = t50 * s0
  t60 = t21 ** 2
  t62 = 0.1e1 / t22 / t60
  t67 = s0 ** 2
  t68 = t67 * t32
  t69 = t60 * r0
  t71 = 0.1e1 / t22 / t69
  t75 = 0.1e1 + 0.5e1 / 0.648e3 * t31 * t34 * t37 + 0.5e1 / 0.54e2 * t31 * t41 / t35 / r0 + t50 * t52 * t55 / 0.2916e4 - t59 * t32 * t62 * l0 / 0.2592e4 + t50 * t68 * t71 / 0.8748e4
  t81 = t20 / t22 / r0
  t83 = 0.1e1 / t35 / t53
  t97 = t60 * t21
  t99 = 0.1e1 / t22 / t97
  t103 = -0.5e1 / 0.243e3 * t31 * t34 * t83 - 0.25e2 / 0.162e3 * t31 * t41 * t37 - 0.5e1 / 0.4374e4 * t50 * t52 * t62 + 0.13e2 / 0.7776e4 * t59 * t32 * t71 * l0 - 0.4e1 / 0.6561e4 * t50 * t68 * t99
  t108 = t20 / t22
  t110 = 0.1e1 / t35 / t60
  t126 = 0.1e1 / t22 / t60 / t53
  t130 = 0.55e2 / 0.729e3 * t31 * t34 * t110 + 0.100e3 / 0.243e3 * t31 * t41 * t83 + 0.65e2 / 0.13122e5 * t50 * t52 * t71 - 0.13e2 / 0.1458e4 * t59 * t32 * t99 * l0 + 0.76e2 / 0.19683e5 * t50 * t68 * t126
  t134 = t20 * t35
  t136 = 0.1e1 / t35 / t69
  t150 = t60 ** 2
  t152 = 0.1e1 / t22 / t150
  t156 = -0.770e3 / 0.2187e4 * t31 * t34 * t136 - 0.1100e4 / 0.729e3 * t31 * t41 * t110 - 0.520e3 / 0.19683e5 * t50 * t52 * t99 + 0.247e3 / 0.4374e4 * t59 * t32 * t126 * l0 - 0.1672e4 / 0.59049e5 * t50 * t68 * t152
  t161 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t75 - t7 * t81 * t103 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t108 * t130 + 0.3e1 / 0.20e2 * t7 * t134 * t156)
  t202 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t55 * t75 + 0.8e1 / 0.45e2 * t7 * t25 * t103 - t7 * t81 * t130 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t108 * t156 + 0.3e1 / 0.20e2 * t7 * t134 * (0.13090e5 / 0.6561e4 * t31 * t34 / t35 / t97 + 0.15400e5 / 0.2187e4 * t31 * t41 * t136 + 0.9880e4 / 0.59049e5 * t50 * t52 * t126 - 0.2717e4 / 0.6561e4 * t59 * t32 * t152 * l0 + 0.41800e5 / 0.177147e6 * t50 * t68 / t22 / t150 / r0))
  v4rho4_0_ = 0.2e1 * r0 * t202 + 0.8e1 * t161

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
  t40 = t35 / t38
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t54 = t35 ** 2
  t57 = t54 / t37 / t36
  t58 = l0 ** 2
  t59 = t41 * r0
  t65 = t41 ** 2
  t67 = 0.1e1 / t42 / t65
  t72 = s0 ** 2
  t75 = 0.1e1 / t42 / t65 / r0
  t79 = 0.1e1 + 0.5e1 / 0.648e3 * t40 * s0 * t45 + 0.5e1 / 0.54e2 * t40 * l0 / t43 / r0 + t57 * t58 / t42 / t59 / 0.5832e4 - t57 * s0 * t67 * l0 / 0.5184e4 + t57 * t72 * t75 / 0.17496e5
  t83 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t84 = t83 ** 2
  t85 = t84 * f.p.zeta_threshold
  t87 = f.my_piecewise3(t21, t85, t23 * t20)
  t88 = 0.1e1 / t32
  t89 = t87 * t88
  t92 = t6 * t89 * t79 / 0.10e2
  t93 = t87 * t33
  t95 = 0.1e1 / t43 / t59
  t111 = 0.1e1 / t42 / t65 / t41
  t115 = -0.5e1 / 0.243e3 * t40 * s0 * t95 - 0.25e2 / 0.162e3 * t40 * l0 * t45 - 0.5e1 / 0.8748e4 * t57 * t58 * t67 + 0.13e2 / 0.15552e5 * t57 * s0 * t75 * l0 - 0.2e1 / 0.6561e4 * t57 * t72 * t111
  t120 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t79 + t92 + 0.3e1 / 0.20e2 * t6 * t93 * t115)
  t122 = r1 <= f.p.dens_threshold
  t123 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t124 = 0.1e1 + t123
  t125 = t124 <= f.p.zeta_threshold
  t126 = t124 ** (0.1e1 / 0.3e1)
  t127 = t126 ** 2
  t129 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t132 = f.my_piecewise3(t125, 0, 0.5e1 / 0.3e1 * t127 * t129)
  t133 = t132 * t33
  t134 = r1 ** 2
  t135 = r1 ** (0.1e1 / 0.3e1)
  t136 = t135 ** 2
  t138 = 0.1e1 / t136 / t134
  t147 = l1 ** 2
  t148 = t134 * r1
  t154 = t134 ** 2
  t156 = 0.1e1 / t135 / t154
  t161 = s2 ** 2
  t164 = 0.1e1 / t135 / t154 / r1
  t168 = 0.1e1 + 0.5e1 / 0.648e3 * t40 * s2 * t138 + 0.5e1 / 0.54e2 * t40 * l1 / t136 / r1 + t57 * t147 / t135 / t148 / 0.5832e4 - t57 * s2 * t156 * l1 / 0.5184e4 + t57 * t161 * t164 / 0.17496e5
  t173 = f.my_piecewise3(t125, t85, t127 * t124)
  t174 = t173 * t88
  t177 = t6 * t174 * t168 / 0.10e2
  t179 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t133 * t168 + t177)
  t181 = 0.1e1 / t22
  t182 = t28 ** 2
  t187 = t17 / t24 / t7
  t189 = -0.2e1 * t25 + 0.2e1 * t187
  t190 = f.my_piecewise5(t11, 0, t15, 0, t189)
  t194 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t181 * t182 + 0.5e1 / 0.3e1 * t23 * t190)
  t201 = t6 * t31 * t88 * t79
  t207 = 0.1e1 / t32 / t7
  t211 = t6 * t87 * t207 * t79 / 0.30e2
  t213 = t6 * t89 * t115
  t241 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t194 * t33 * t79 + t201 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t115 - t211 + t213 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t93 * (0.55e2 / 0.729e3 * t40 * s0 / t43 / t65 + 0.100e3 / 0.243e3 * t40 * l0 * t95 + 0.65e2 / 0.26244e5 * t57 * t58 * t75 - 0.13e2 / 0.2916e4 * t57 * s0 * t111 * l0 + 0.38e2 / 0.19683e5 * t57 * t72 / t42 / t65 / t59))
  t242 = 0.1e1 / t126
  t243 = t129 ** 2
  t247 = f.my_piecewise5(t15, 0, t11, 0, -t189)
  t251 = f.my_piecewise3(t125, 0, 0.10e2 / 0.9e1 * t242 * t243 + 0.5e1 / 0.3e1 * t127 * t247)
  t258 = t6 * t132 * t88 * t168
  t263 = t6 * t173 * t207 * t168 / 0.30e2
  t265 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t251 * t33 * t168 + t258 / 0.5e1 - t263)
  d11 = 0.2e1 * t120 + 0.2e1 * t179 + t7 * (t241 + t265)
  t268 = -t8 - t26
  t269 = f.my_piecewise5(t11, 0, t15, 0, t268)
  t272 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t269)
  t273 = t272 * t33
  t278 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t273 * t79 + t92)
  t280 = f.my_piecewise5(t15, 0, t11, 0, -t268)
  t283 = f.my_piecewise3(t125, 0, 0.5e1 / 0.3e1 * t127 * t280)
  t284 = t283 * t33
  t288 = t173 * t33
  t290 = 0.1e1 / t136 / t148
  t306 = 0.1e1 / t135 / t154 / t134
  t310 = -0.5e1 / 0.243e3 * t40 * s2 * t290 - 0.25e2 / 0.162e3 * t40 * l1 * t138 - 0.5e1 / 0.8748e4 * t57 * t147 * t156 + 0.13e2 / 0.15552e5 * t57 * s2 * t164 * l1 - 0.2e1 / 0.6561e4 * t57 * t161 * t306
  t315 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t284 * t168 + t177 + 0.3e1 / 0.20e2 * t6 * t288 * t310)
  t319 = 0.2e1 * t187
  t320 = f.my_piecewise5(t11, 0, t15, 0, t319)
  t324 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t181 * t269 * t28 + 0.5e1 / 0.3e1 * t23 * t320)
  t331 = t6 * t272 * t88 * t79
  t339 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t324 * t33 * t79 + t331 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t273 * t115 + t201 / 0.10e2 - t211 + t213 / 0.10e2)
  t343 = f.my_piecewise5(t15, 0, t11, 0, -t319)
  t347 = f.my_piecewise3(t125, 0, 0.10e2 / 0.9e1 * t242 * t280 * t129 + 0.5e1 / 0.3e1 * t127 * t343)
  t354 = t6 * t283 * t88 * t168
  t361 = t6 * t174 * t310
  t364 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t347 * t33 * t168 + t354 / 0.10e2 + t258 / 0.10e2 - t263 + 0.3e1 / 0.20e2 * t6 * t133 * t310 + t361 / 0.10e2)
  d12 = t120 + t179 + t278 + t315 + t7 * (t339 + t364)
  t369 = t269 ** 2
  t373 = 0.2e1 * t25 + 0.2e1 * t187
  t374 = f.my_piecewise5(t11, 0, t15, 0, t373)
  t378 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t181 * t369 + 0.5e1 / 0.3e1 * t23 * t374)
  t385 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t378 * t33 * t79 + t331 / 0.5e1 - t211)
  t386 = t280 ** 2
  t390 = f.my_piecewise5(t15, 0, t11, 0, -t373)
  t394 = f.my_piecewise3(t125, 0, 0.10e2 / 0.9e1 * t242 * t386 + 0.5e1 / 0.3e1 * t127 * t390)
  t430 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t394 * t33 * t168 + t354 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t284 * t310 - t263 + t361 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t288 * (0.55e2 / 0.729e3 * t40 * s2 / t136 / t154 + 0.100e3 / 0.243e3 * t40 * l1 * t290 + 0.65e2 / 0.26244e5 * t57 * t147 * t164 - 0.13e2 / 0.2916e4 * t57 * s2 * t306 * l1 + 0.38e2 / 0.19683e5 * t57 * t161 / t135 / t154 / t148))
  d22 = 0.2e1 * t278 + 0.2e1 * t315 + t7 * (t385 + t430)
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
  t51 = t46 / t49
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / t52
  t65 = t46 ** 2
  t68 = t65 / t48 / t47
  t69 = l0 ** 2
  t70 = t52 * r0
  t76 = t52 ** 2
  t78 = 0.1e1 / t53 / t76
  t83 = s0 ** 2
  t84 = t76 * r0
  t86 = 0.1e1 / t53 / t84
  t90 = 0.1e1 + 0.5e1 / 0.648e3 * t51 * s0 * t56 + 0.5e1 / 0.54e2 * t51 * l0 / t54 / r0 + t68 * t69 / t53 / t70 / 0.5832e4 - t68 * s0 * t78 * l0 / 0.5184e4 + t68 * t83 * t86 / 0.17496e5
  t96 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t97 = 0.1e1 / t43
  t98 = t96 * t97
  t102 = t96 * t44
  t104 = 0.1e1 / t54 / t70
  t120 = 0.1e1 / t53 / t76 / t52
  t124 = -0.5e1 / 0.243e3 * t51 * s0 * t104 - 0.25e2 / 0.162e3 * t51 * l0 * t56 - 0.5e1 / 0.8748e4 * t68 * t69 * t78 + 0.13e2 / 0.15552e5 * t68 * s0 * t86 * l0 - 0.2e1 / 0.6561e4 * t68 * t83 * t120
  t128 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t129 = t128 ** 2
  t130 = t129 * f.p.zeta_threshold
  t132 = f.my_piecewise3(t21, t130, t32 * t20)
  t134 = 0.1e1 / t43 / t7
  t135 = t132 * t134
  t139 = t132 * t97
  t143 = t132 * t44
  t145 = 0.1e1 / t54 / t76
  t161 = 0.1e1 / t53 / t76 / t70
  t165 = 0.55e2 / 0.729e3 * t51 * s0 * t145 + 0.100e3 / 0.243e3 * t51 * l0 * t104 + 0.65e2 / 0.26244e5 * t68 * t69 * t86 - 0.13e2 / 0.2916e4 * t68 * s0 * t120 * l0 + 0.38e2 / 0.19683e5 * t68 * t83 * t161
  t170 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t90 + t6 * t98 * t90 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t102 * t124 - t6 * t135 * t90 / 0.30e2 + t6 * t139 * t124 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t143 * t165)
  t172 = r1 <= f.p.dens_threshold
  t173 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t174 = 0.1e1 + t173
  t175 = t174 <= f.p.zeta_threshold
  t176 = t174 ** (0.1e1 / 0.3e1)
  t177 = 0.1e1 / t176
  t179 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t180 = t179 ** 2
  t183 = t176 ** 2
  t185 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t189 = f.my_piecewise3(t175, 0, 0.10e2 / 0.9e1 * t177 * t180 + 0.5e1 / 0.3e1 * t183 * t185)
  t191 = r1 ** 2
  t192 = r1 ** (0.1e1 / 0.3e1)
  t193 = t192 ** 2
  t204 = l1 ** 2
  t211 = t191 ** 2
  t218 = s2 ** 2
  t225 = 0.1e1 + 0.5e1 / 0.648e3 * t51 * s2 / t193 / t191 + 0.5e1 / 0.54e2 * t51 * l1 / t193 / r1 + t68 * t204 / t192 / t191 / r1 / 0.5832e4 - t68 * s2 / t192 / t211 * l1 / 0.5184e4 + t68 * t218 / t192 / t211 / r1 / 0.17496e5
  t231 = f.my_piecewise3(t175, 0, 0.5e1 / 0.3e1 * t183 * t179)
  t237 = f.my_piecewise3(t175, t130, t183 * t174)
  t243 = f.my_piecewise3(t172, 0, 0.3e1 / 0.20e2 * t6 * t189 * t44 * t225 + t6 * t231 * t97 * t225 / 0.5e1 - t6 * t237 * t134 * t225 / 0.30e2)
  t253 = t24 ** 2
  t257 = 0.6e1 * t34 - 0.6e1 * t17 / t253
  t258 = f.my_piecewise5(t11, 0, t15, 0, t257)
  t262 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t258)
  t285 = 0.1e1 / t43 / t24
  t311 = t76 ** 2
  t322 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t262 * t44 * t90 + 0.3e1 / 0.10e2 * t6 * t42 * t97 * t90 + 0.9e1 / 0.20e2 * t6 * t45 * t124 - t6 * t96 * t134 * t90 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t98 * t124 + 0.9e1 / 0.20e2 * t6 * t102 * t165 + 0.2e1 / 0.45e2 * t6 * t132 * t285 * t90 - t6 * t135 * t124 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t139 * t165 + 0.3e1 / 0.20e2 * t6 * t143 * (-0.770e3 / 0.2187e4 * t51 * s0 / t54 / t84 - 0.1100e4 / 0.729e3 * t51 * l0 * t145 - 0.260e3 / 0.19683e5 * t68 * t69 * t120 + 0.247e3 / 0.8748e4 * t68 * s0 * t161 * l0 - 0.836e3 / 0.59049e5 * t68 * t83 / t53 / t311))
  t332 = f.my_piecewise5(t15, 0, t11, 0, -t257)
  t336 = f.my_piecewise3(t175, 0, -0.10e2 / 0.27e2 / t176 / t174 * t180 * t179 + 0.10e2 / 0.3e1 * t177 * t179 * t185 + 0.5e1 / 0.3e1 * t183 * t332)
  t354 = f.my_piecewise3(t172, 0, 0.3e1 / 0.20e2 * t6 * t336 * t44 * t225 + 0.3e1 / 0.10e2 * t6 * t189 * t97 * t225 - t6 * t231 * t134 * t225 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t237 * t285 * t225)
  d111 = 0.3e1 * t170 + 0.3e1 * t243 + t7 * (t322 + t354)

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
  t63 = t58 / t61
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t77 = t58 ** 2
  t80 = t77 / t60 / t59
  t81 = l0 ** 2
  t82 = t64 * r0
  t88 = t64 ** 2
  t90 = 0.1e1 / t65 / t88
  t95 = s0 ** 2
  t96 = t88 * r0
  t98 = 0.1e1 / t65 / t96
  t102 = 0.1e1 + 0.5e1 / 0.648e3 * t63 * s0 * t68 + 0.5e1 / 0.54e2 * t63 * l0 / t66 / r0 + t80 * t81 / t65 / t82 / 0.5832e4 - t80 * s0 * t90 * l0 / 0.5184e4 + t80 * t95 * t98 / 0.17496e5
  t111 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t112 = 0.1e1 / t55
  t113 = t111 * t112
  t117 = t111 * t56
  t119 = 0.1e1 / t66 / t82
  t133 = t88 * t64
  t135 = 0.1e1 / t65 / t133
  t139 = -0.5e1 / 0.243e3 * t63 * s0 * t119 - 0.25e2 / 0.162e3 * t63 * l0 * t68 - 0.5e1 / 0.8748e4 * t80 * t81 * t90 + 0.13e2 / 0.15552e5 * t80 * s0 * t98 * l0 - 0.2e1 / 0.6561e4 * t80 * t95 * t135
  t145 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t147 = 0.1e1 / t55 / t7
  t148 = t145 * t147
  t152 = t145 * t112
  t156 = t145 * t56
  t158 = 0.1e1 / t66 / t88
  t174 = 0.1e1 / t65 / t88 / t82
  t178 = 0.55e2 / 0.729e3 * t63 * s0 * t158 + 0.100e3 / 0.243e3 * t63 * l0 * t119 + 0.65e2 / 0.26244e5 * t80 * t81 * t98 - 0.13e2 / 0.2916e4 * t80 * s0 * t135 * l0 + 0.38e2 / 0.19683e5 * t80 * t95 * t174
  t182 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t183 = t182 ** 2
  t184 = t183 * f.p.zeta_threshold
  t186 = f.my_piecewise3(t21, t184, t44 * t20)
  t188 = 0.1e1 / t55 / t25
  t189 = t186 * t188
  t193 = t186 * t147
  t197 = t186 * t112
  t201 = t186 * t56
  t203 = 0.1e1 / t66 / t96
  t217 = t88 ** 2
  t219 = 0.1e1 / t65 / t217
  t223 = -0.770e3 / 0.2187e4 * t63 * s0 * t203 - 0.1100e4 / 0.729e3 * t63 * l0 * t158 - 0.260e3 / 0.19683e5 * t80 * t81 * t135 + 0.247e3 / 0.8748e4 * t80 * s0 * t174 * l0 - 0.836e3 / 0.59049e5 * t80 * t95 * t219
  t228 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t102 + 0.3e1 / 0.10e2 * t6 * t113 * t102 + 0.9e1 / 0.20e2 * t6 * t117 * t139 - t6 * t148 * t102 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t152 * t139 + 0.9e1 / 0.20e2 * t6 * t156 * t178 + 0.2e1 / 0.45e2 * t6 * t189 * t102 - t6 * t193 * t139 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t197 * t178 + 0.3e1 / 0.20e2 * t6 * t201 * t223)
  t230 = r1 <= f.p.dens_threshold
  t231 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t232 = 0.1e1 + t231
  t233 = t232 <= f.p.zeta_threshold
  t234 = t232 ** (0.1e1 / 0.3e1)
  t236 = 0.1e1 / t234 / t232
  t238 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t239 = t238 ** 2
  t243 = 0.1e1 / t234
  t244 = t243 * t238
  t246 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t249 = t234 ** 2
  t251 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t255 = f.my_piecewise3(t233, 0, -0.10e2 / 0.27e2 * t236 * t239 * t238 + 0.10e2 / 0.3e1 * t244 * t246 + 0.5e1 / 0.3e1 * t249 * t251)
  t257 = r1 ** 2
  t258 = r1 ** (0.1e1 / 0.3e1)
  t259 = t258 ** 2
  t270 = l1 ** 2
  t277 = t257 ** 2
  t284 = s2 ** 2
  t291 = 0.1e1 + 0.5e1 / 0.648e3 * t63 * s2 / t259 / t257 + 0.5e1 / 0.54e2 * t63 * l1 / t259 / r1 + t80 * t270 / t258 / t257 / r1 / 0.5832e4 - t80 * s2 / t258 / t277 * l1 / 0.5184e4 + t80 * t284 / t258 / t277 / r1 / 0.17496e5
  t300 = f.my_piecewise3(t233, 0, 0.10e2 / 0.9e1 * t243 * t239 + 0.5e1 / 0.3e1 * t249 * t246)
  t307 = f.my_piecewise3(t233, 0, 0.5e1 / 0.3e1 * t249 * t238)
  t313 = f.my_piecewise3(t233, t184, t249 * t232)
  t319 = f.my_piecewise3(t230, 0, 0.3e1 / 0.20e2 * t6 * t255 * t56 * t291 + 0.3e1 / 0.10e2 * t6 * t300 * t112 * t291 - t6 * t307 * t147 * t291 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t313 * t188 * t291)
  t364 = t20 ** 2
  t367 = t30 ** 2
  t373 = t41 ** 2
  t382 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t383 = f.my_piecewise5(t11, 0, t15, 0, t382)
  t387 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t364 * t367 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t373 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t383)
  t414 = 0.1e1 / t55 / t36
  t419 = -0.2e1 / 0.5e1 * t6 * t148 * t139 + 0.6e1 / 0.5e1 * t6 * t152 * t178 + 0.3e1 / 0.5e1 * t6 * t156 * t223 + 0.8e1 / 0.45e2 * t6 * t189 * t139 - t6 * t193 * t178 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t197 * t223 + 0.3e1 / 0.20e2 * t6 * t201 * (0.13090e5 / 0.6561e4 * t63 * s0 / t66 / t133 + 0.15400e5 / 0.2187e4 * t63 * l0 * t203 + 0.4940e4 / 0.59049e5 * t80 * t81 * t174 - 0.2717e4 / 0.13122e5 * t80 * s0 * t219 * l0 + 0.20900e5 / 0.177147e6 * t80 * t95 / t65 / t217 / r0) + 0.3e1 / 0.20e2 * t6 * t387 * t56 * t102 + 0.3e1 / 0.5e1 * t6 * t57 * t139 + 0.6e1 / 0.5e1 * t6 * t113 * t139 + 0.9e1 / 0.10e2 * t6 * t117 * t178 + 0.2e1 / 0.5e1 * t6 * t54 * t112 * t102 - t6 * t111 * t147 * t102 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t145 * t188 * t102 - 0.14e2 / 0.135e3 * t6 * t186 * t414 * t102
  t420 = f.my_piecewise3(t1, 0, t419)
  t421 = t232 ** 2
  t424 = t239 ** 2
  t430 = t246 ** 2
  t436 = f.my_piecewise5(t15, 0, t11, 0, -t382)
  t440 = f.my_piecewise3(t233, 0, 0.40e2 / 0.81e2 / t234 / t421 * t424 - 0.20e2 / 0.9e1 * t236 * t239 * t246 + 0.10e2 / 0.3e1 * t243 * t430 + 0.40e2 / 0.9e1 * t244 * t251 + 0.5e1 / 0.3e1 * t249 * t436)
  t462 = f.my_piecewise3(t230, 0, 0.3e1 / 0.20e2 * t6 * t440 * t56 * t291 + 0.2e1 / 0.5e1 * t6 * t255 * t112 * t291 - t6 * t300 * t147 * t291 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t307 * t188 * t291 - 0.14e2 / 0.135e3 * t6 * t313 * t414 * t291)
  d1111 = 0.4e1 * t228 + 0.4e1 * t319 + t7 * (t420 + t462)

  res = {'v4rho4': d1111}
  return res
