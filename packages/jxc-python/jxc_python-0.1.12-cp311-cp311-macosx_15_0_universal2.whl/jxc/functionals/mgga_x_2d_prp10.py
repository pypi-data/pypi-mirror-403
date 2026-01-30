"""Generated from mgga_x_2d_prp10.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
import scipy.special as sp_special
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
  prhg07_C = lambda x, u, t: (u - 4 * t + x ** 2 / 2) / 4

  prhg07_y = lambda x: LambertW(jnp.maximum(x / jnp.pi, -0.9999999999) * jnp.exp(-1)) + 1

  prhg07_v = lambda y: jnp.pi / X_FACTOR_2D_C * BesselI(0, y / 2)

  prp10_f = lambda rs, z, x, u, t: -(X_FACTOR_2D_C * prhg07_v(prhg07_y(prhg07_C(x, u, t))) - 2 * jnp.sqrt(2) / (3 * jnp.pi) * jnp.sqrt(2 * jnp.maximum(t - x ** 2 / 8, 1e-10))) * f.n_spin(rs, z) ** (1 / 2)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1=None: prp10_f(rs, z, xs0, u0, t0)

  _raise_value_error = lambda msg: (_ for _ in ()).throw(ValueError(msg))

  BesselI = lambda order, value: (
      bessel_i0(value)
      if order == 0
      else (
          bessel_i1(value)
          if order == 1
          else _raise_value_error(f"Unsupported BesselI order: {order}")
      )
  )

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
  prhg07_C = lambda x, u, t: (u - 4 * t + x ** 2 / 2) / 4

  prhg07_y = lambda x: LambertW(jnp.maximum(x / jnp.pi, -0.9999999999) * jnp.exp(-1)) + 1

  prhg07_v = lambda y: jnp.pi / X_FACTOR_2D_C * BesselI(0, y / 2)

  prp10_f = lambda rs, z, x, u, t: -(X_FACTOR_2D_C * prhg07_v(prhg07_y(prhg07_C(x, u, t))) - 2 * jnp.sqrt(2) / (3 * jnp.pi) * jnp.sqrt(2 * jnp.maximum(t - x ** 2 / 8, 1e-10))) * f.n_spin(rs, z) ** (1 / 2)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1=None: prp10_f(rs, z, xs0, u0, t0)

  _raise_value_error = lambda msg: (_ for _ in ()).throw(ValueError(msg))

  BesselI = lambda order, value: (
      bessel_i0(value)
      if order == 0
      else (
          bessel_i1(value)
          if order == 1
          else _raise_value_error(f"Unsupported BesselI order: {order}")
      )
  )

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

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = jnp.sqrt(r0)
  t3 = 2 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = l0 * t4
  t6 = r0 ** (0.1e1 / 0.3e1)
  t7 = t6 ** 2
  t9 = 0.1e1 / t7 / r0
  t12 = tau0 * t4
  t13 = t12 * t9
  t14 = s0 * t4
  t15 = r0 ** 2
  t17 = 0.1e1 / t7 / t15
  t19 = t14 * t17 / 0.8e1
  t21 = 0.1e1 / jnp.pi
  t22 = (t5 * t9 / 0.4e1 - t13 + t19) * t21
  t23 = -0.9999999999e0 < t22
  t24 = f.my_piecewise3(t23, t22, -0.9999999999e0)
  t25 = jnp.exp(-1)
  t27 = lambertw(t24 * t25)
  t28 = t27 + 0.1e1
  t29 = t28 / 0.2e1
  t30 = jax.scipy.special.i0(t29)
  t32 = t13 - t19
  t33 = 0.1e-9 < t32
  t34 = f.my_piecewise3(t33, t32, 0.1e-9)
  t35 = jnp.sqrt(t34)
  t40 = jnp.sqrt(0.2e1)
  t43 = scipy.special.i1(t29)
  t44 = jnp.pi * t43
  t48 = 0.5e1 / 0.3e1 * t12 * t17
  t51 = 0.1e1 / t7 / t15 / r0
  t53 = t14 * t51 / 0.3e1
  t56 = f.my_piecewise3(t23, (-0.5e1 / 0.12e2 * t5 * t17 + t48 - t53) * t21, 0)
  t59 = t27 / t28
  t61 = t59 / t24
  t65 = t21 / t35
  t67 = f.my_piecewise3(t33, -t48 + t53, 0)
  t79 = t56 ** 2
  t81 = t27 ** 2
  t82 = t28 ** 2
  t83 = 0.1e1 / t82
  t85 = t24 ** 2
  t86 = 0.1e1 / t85
  t93 = 0.40e2 / 0.9e1 * t12 * t51
  t94 = t15 ** 2
  t98 = 0.11e2 / 0.9e1 * t14 / t7 / t94
  t101 = f.my_piecewise3(t23, (0.10e2 / 0.9e1 * t5 * t51 - t93 + t98) * t21, 0)
  t105 = t44 * t79
  t122 = t67 ** 2
  t126 = f.my_piecewise3(t33, t93 - t98, 0)
  v2rho2_0_ = -0.3e1 / 0.8e1 / t1 * (jnp.pi * t30 - 0.4e1 / 0.3e1 * t21 * t35) * t40 - 0.3e1 / 0.2e1 * t1 * (t44 * t56 * t61 / 0.2e1 - 0.2e1 / 0.3e1 * t65 * t67) * t40 - t1 * r0 * (jnp.pi * (t30 - 0.1e1 / t29 * t43) * t79 * t81 * t83 * t86 / 0.4e1 + t44 * t101 * t61 / 0.2e1 + t105 * t27 * t83 * t86 / 0.2e1 - t105 * t81 / t82 / t28 * t86 / 0.2e1 - t105 * t59 * t86 / 0.2e1 + t21 / t35 / t34 * t122 / 0.3e1 - 0.2e1 / 0.3e1 * t65 * t126) * t40 / 0.2e1
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = jnp.sqrt(r0)
  t2 = t1 * r0
  t4 = 2 ** (0.1e1 / 0.3e1)
  t5 = t4 ** 2
  t6 = l0 * t5
  t7 = r0 ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t10 = 0.1e1 / t8 / r0
  t13 = tau0 * t5
  t14 = t13 * t10
  t15 = s0 * t5
  t16 = r0 ** 2
  t18 = 0.1e1 / t8 / t16
  t20 = t15 * t18 / 0.8e1
  t22 = 0.1e1 / jnp.pi
  t23 = (t6 * t10 / 0.4e1 - t14 + t20) * t22
  t24 = -0.9999999999e0 < t23
  t25 = f.my_piecewise3(t24, t23, -0.9999999999e0)
  t26 = jnp.exp(-1)
  t28 = scipy.special.lambertw(t25 * t26)
  t29 = 0.1e1 + t28
  t30 = t29 / 0.2e1
  t31 = scipy.special.i0(t30)
  t33 = t14 - t20
  t34 = 0.1e-9 < t33
  t35 = f.my_piecewise3(t34, t33, 0.1e-9)
  t36 = jnp.sqrt(t35)
  t41 = jnp.sqrt(0.2e1)
  t45 = scipy.special.i1(t30)
  t46 = jnp.pi * t45
  t50 = 0.5e1 / 0.3e1 * t13 * t18
  t53 = 0.1e1 / t8 / t16 / r0
  t55 = t15 * t53 / 0.3e1
  t58 = f.my_piecewise3(t24, (-0.5e1 / 0.12e2 * t6 * t18 + t50 - t55) * t22, 0)
  t61 = t28 / t29
  t63 = t61 / t25
  t67 = t22 / t36
  t69 = f.my_piecewise3(t34, -t50 + t55, 0)
  t76 = 0.1e1 / t30
  t78 = -t76 * t45 + t31
  t79 = jnp.pi * t78
  t80 = t58 ** 2
  t82 = t28 ** 2
  t83 = t29 ** 2
  t84 = 0.1e1 / t83
  t85 = t82 * t84
  t86 = t25 ** 2
  t87 = 0.1e1 / t86
  t88 = t85 * t87
  t94 = 0.40e2 / 0.9e1 * t13 * t53
  t95 = t16 ** 2
  t97 = 0.1e1 / t8 / t95
  t99 = 0.11e2 / 0.9e1 * t15 * t97
  t102 = f.my_piecewise3(t24, (0.10e2 / 0.9e1 * t6 * t53 - t94 + t99) * t22, 0)
  t103 = t46 * t102
  t106 = t46 * t80
  t107 = t28 * t84
  t112 = 0.1e1 / t83 / t29
  t113 = t82 * t112
  t122 = t22 / t36 / t35
  t123 = t69 ** 2
  t127 = f.my_piecewise3(t34, t94 - t99, 0)
  t134 = t87 * t58
  t138 = t80 * t58
  t139 = t46 * t138
  t141 = 0.1e1 / t86 / t25
  t145 = t113 * t141
  t155 = t79 * t138
  t170 = t82 * t28
  t171 = t83 ** 2
  t172 = 0.1e1 / t171
  t190 = t35 ** 2
  t201 = t30 ** 2
  t218 = 0.440e3 / 0.27e2 * t13 * t97
  t223 = 0.154e3 / 0.27e2 * t15 / t8 / t95 / r0
  t226 = f.my_piecewise3(t24, (-0.110e3 / 0.27e2 * t6 * t97 + t218 - t223) * t22, 0)
  t231 = f.my_piecewise3(t34, -t218 + t223, 0)
  t234 = -0.3e1 / 0.2e1 * t103 * t61 * t134 - 0.3e1 / 0.2e1 * t139 * t107 * t141 + 0.3e1 / 0.2e1 * t139 * t145 + t139 * t61 * t141 + 0.3e1 / 0.4e1 * t79 * t58 * t85 * t87 * t102 - 0.3e1 / 0.4e1 * t155 * t85 * t141 + 0.3e1 / 0.2e1 * t103 * t58 * t28 * t84 * t87 + t139 * t28 * t112 * t141 / 0.2e1 + 0.3e1 / 0.4e1 * t155 * t145 - 0.3e1 / 0.4e1 * t155 * t170 * t172 * t141 - 0.3e1 / 0.2e1 * t103 * t113 * t134 - 0.2e1 * t139 * t82 * t172 * t141 + 0.3e1 / 0.2e1 * t139 * t170 / t171 / t29 * t141 - t22 / t36 / t190 * t123 * t69 / 0.2e1 + t122 * t69 * t127 + jnp.pi * (t45 * t58 * t63 / 0.2e1 + 0.1e1 / t201 * t45 * t58 * t63 / 0.2e1 - t76 * t78 * t58 * t63 / 0.2e1) * t80 * t88 / 0.4e1 + t46 * t226 * t63 / 0.2e1 - 0.2e1 / 0.3e1 * t67 * t231
  v3rho3_0_ = 0.3e1 / 0.16e2 / t2 * (jnp.pi * t31 - 0.4e1 / 0.3e1 * t22 * t36) * t41 - 0.9e1 / 0.8e1 / t1 * (t46 * t58 * t63 / 0.2e1 - 0.2e1 / 0.3e1 * t67 * t69) * t41 - 0.9e1 / 0.4e1 * t1 * (t79 * t80 * t88 / 0.4e1 + t103 * t63 / 0.2e1 + t106 * t107 * t87 / 0.2e1 - t106 * t113 * t87 / 0.2e1 - t106 * t61 * t87 / 0.2e1 + t122 * t123 / 0.3e1 - 0.2e1 / 0.3e1 * t67 * t127) * t41 - t2 * t234 * t41 / 0.2e1

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** 2
  t2 = jnp.sqrt(r0)
  t5 = 2 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = l0 * t6
  t8 = r0 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t11 = 0.1e1 / t9 / r0
  t14 = tau0 * t6
  t15 = t14 * t11
  t16 = s0 * t6
  t18 = 0.1e1 / t9 / t1
  t20 = t16 * t18 / 0.8e1
  t22 = 0.1e1 / jnp.pi
  t23 = (t7 * t11 / 0.4e1 - t15 + t20) * t22
  t24 = -0.9999999999e0 < t23
  t25 = f.my_piecewise3(t24, t23, -0.9999999999e0)
  t26 = jnp.exp(-1)
  t28 = scipy.special.lambertw(t25 * t26)
  t29 = 0.1e1 + t28
  t30 = t29 / 0.2e1
  t31 = scipy.special.i0(t30)
  t33 = t15 - t20
  t34 = 0.1e-9 < t33
  t35 = f.my_piecewise3(t34, t33, 0.1e-9)
  t36 = jnp.sqrt(t35)
  t41 = jnp.sqrt(0.2e1)
  t44 = t2 * r0
  t46 = scipy.special.i1(t30)
  t47 = jnp.pi * t46
  t51 = 0.5e1 / 0.3e1 * t14 * t18
  t54 = 0.1e1 / t9 / t1 / r0
  t56 = t16 * t54 / 0.3e1
  t59 = f.my_piecewise3(t24, (-0.5e1 / 0.12e2 * t7 * t18 + t51 - t56) * t22, 0)
  t62 = t28 / t29
  t64 = t62 / t25
  t68 = t22 / t36
  t70 = f.my_piecewise3(t34, -t51 + t56, 0)
  t78 = 0.1e1 / t30
  t80 = -t78 * t46 + t31
  t81 = jnp.pi * t80
  t82 = t59 ** 2
  t83 = t81 * t82
  t84 = t28 ** 2
  t85 = t29 ** 2
  t86 = 0.1e1 / t85
  t87 = t84 * t86
  t88 = t25 ** 2
  t89 = 0.1e1 / t88
  t90 = t87 * t89
  t96 = 0.40e2 / 0.9e1 * t14 * t54
  t97 = t1 ** 2
  t99 = 0.1e1 / t9 / t97
  t101 = 0.11e2 / 0.9e1 * t16 * t99
  t104 = f.my_piecewise3(t24, (0.10e2 / 0.9e1 * t7 * t54 - t96 + t101) * t22, 0)
  t105 = t47 * t104
  t108 = t47 * t82
  t109 = t28 * t86
  t110 = t109 * t89
  t113 = t85 * t29
  t114 = 0.1e1 / t113
  t115 = t84 * t114
  t116 = t115 * t89
  t119 = t62 * t89
  t124 = t22 / t36 / t35
  t125 = t70 ** 2
  t129 = f.my_piecewise3(t34, t96 - t101, 0)
  t136 = t89 * t59
  t137 = t62 * t136
  t140 = t82 * t59
  t141 = t47 * t140
  t143 = 0.1e1 / t88 / t25
  t147 = t115 * t143
  t152 = t81 * t59
  t154 = t87 * t89 * t104
  t157 = t81 * t140
  t158 = t87 * t143
  t163 = t59 * t28 * t86 * t89
  t166 = t28 * t114
  t172 = t84 * t28
  t173 = t85 ** 2
  t174 = 0.1e1 / t173
  t175 = t172 * t174
  t176 = t175 * t143
  t179 = t115 * t136
  t182 = t84 * t174
  t187 = 0.1e1 / t173 / t29
  t188 = t172 * t187
  t192 = t35 ** 2
  t195 = t22 / t36 / t192
  t203 = t30 ** 2
  t204 = 0.1e1 / t203
  t205 = t204 * t46
  t208 = t78 * t80
  t212 = t205 * t59 * t64 / 0.2e1 - t208 * t59 * t64 / 0.2e1 + t46 * t59 * t64 / 0.2e1
  t213 = jnp.pi * t212
  t220 = 0.440e3 / 0.27e2 * t14 * t99
  t223 = 0.1e1 / t9 / t97 / r0
  t225 = 0.154e3 / 0.27e2 * t16 * t223
  t228 = f.my_piecewise3(t24, (-0.110e3 / 0.27e2 * t7 * t99 + t220 - t225) * t22, 0)
  t229 = t47 * t228
  t233 = f.my_piecewise3(t34, -t220 + t225, 0)
  t236 = -0.3e1 / 0.2e1 * t105 * t137 - 0.3e1 / 0.2e1 * t141 * t109 * t143 + 0.3e1 / 0.2e1 * t141 * t147 + t141 * t62 * t143 + 0.3e1 / 0.4e1 * t152 * t154 - 0.3e1 / 0.4e1 * t157 * t158 + 0.3e1 / 0.2e1 * t105 * t163 + t141 * t166 * t143 / 0.2e1 + 0.3e1 / 0.4e1 * t157 * t147 - 0.3e1 / 0.4e1 * t157 * t176 - 0.3e1 / 0.2e1 * t105 * t179 - 0.2e1 * t141 * t182 * t143 + 0.3e1 / 0.2e1 * t141 * t188 * t143 - t195 * t125 * t70 / 0.2e1 + t124 * t70 * t129 + t213 * t82 * t90 / 0.4e1 + t229 * t64 / 0.2e1 - 0.2e1 / 0.3e1 * t68 * t233
  t241 = 0.6160e4 / 0.81e2 * t14 * t223
  t246 = 0.2618e4 / 0.81e2 * t16 / t9 / t97 / t1
  t248 = f.my_piecewise3(t34, t241 - t246, 0)
  t255 = t125 ** 2
  t258 = t129 ** 2
  t269 = t82 * t28
  t274 = t143 * t82
  t278 = t143 * t104
  t290 = -0.2e1 / 0.3e1 * t68 * t248 + 0.5e1 / 0.4e1 * t22 / t36 / t192 / t35 * t255 + t124 * t258 - 0.3e1 * t195 * t125 * t129 + 0.4e1 / 0.3e1 * t124 * t70 * t233 + 0.5e1 / 0.4e1 * t213 * t59 * t154 - 0.9e1 * t105 * t269 * t86 * t143 + 0.9e1 * t105 * t115 * t274 + 0.9e1 / 0.2e1 * t83 * t115 * t278 - 0.9e1 / 0.2e1 * t83 * t175 * t278 - 0.12e2 * t105 * t82 * t84 * t174 * t143
  t319 = t46 * t82
  t339 = t205 * t82
  t353 = t208 * t82
  t360 = t80 * t82 * t90 / 0.4e1 + t46 * t104 * t64 / 0.2e1 + t319 * t110 / 0.2e1 - t319 * t116 / 0.2e1 - t319 * t119 / 0.2e1 - 0.1e1 / t203 / t30 * t46 * t82 * t90 / 0.2e1 + t204 * t80 * t82 * t90 / 0.2e1 + t205 * t104 * t64 / 0.2e1 + t339 * t110 / 0.2e1 - t339 * t116 / 0.2e1 - t339 * t119 / 0.2e1 - t78 * t212 * t59 * t64 / 0.2e1 - t208 * t104 * t64 / 0.2e1 - t353 * t110 / 0.2e1 + t353 * t116 / 0.2e1 + t353 * t119 / 0.2e1
  t369 = f.my_piecewise3(t24, (0.1540e4 / 0.81e2 * t7 * t223 - t241 + t246) * t22, 0)
  t373 = t82 ** 2
  t374 = t47 * t373
  t376 = t88 ** 2
  t377 = 0.1e1 / t376
  t381 = 0.9e1 * t105 * t188 * t274 + 0.6e1 * t105 * t62 * t274 + 0.3e1 * t105 * t269 * t114 * t143 - 0.2e1 * t229 * t179 + t152 * t87 * t89 * t228 + 0.2e1 * t229 * t163 - 0.2e1 * t229 * t137 - 0.9e1 / 0.2e1 * t83 * t87 * t278 + jnp.pi * t360 * t82 * t90 / 0.4e1 + t47 * t369 * t64 / 0.2e1 - 0.11e2 / 0.2e1 * t374 * t84 * t187 * t377
  t383 = t81 * t373
  t384 = t188 * t377
  t387 = t84 ** 2
  t389 = 0.1e1 / t173 / t85
  t404 = t104 ** 2
  t405 = t47 * t404
  t418 = t115 * t377
  t424 = -0.11e2 / 0.2e1 * t383 * t384 + 0.15e2 / 0.4e1 * t383 * t387 * t389 * t377 + 0.25e2 / 0.2e1 * t374 * t172 * t389 * t377 - 0.15e2 / 0.2e1 * t374 * t387 / t173 / t113 * t377 - 0.3e1 / 0.2e1 * t405 * t116 + 0.3e1 / 0.4e1 * t81 * t404 * t90 + 0.3e1 / 0.2e1 * t405 * t110 - 0.3e1 / 0.2e1 * t405 * t119 + 0.11e2 / 0.2e1 * t374 * t109 * t377 - 0.11e2 / 0.2e1 * t374 * t418 - 0.3e1 * t374 * t62 * t377
  t432 = t182 * t377
  t445 = t213 * t140
  t454 = -0.3e1 * t374 * t166 * t377 + t374 * t28 * t174 * t377 / 0.2e1 + 0.12e2 * t374 * t432 - 0.9e1 * t374 * t384 - 0.9e1 / 0.2e1 * t383 * t418 + 0.9e1 / 0.2e1 * t383 * t175 * t377 + 0.11e2 / 0.4e1 * t383 * t87 * t377 - 0.5e1 / 0.4e1 * t445 * t158 + 0.7e1 / 0.4e1 * t383 * t432 + 0.5e1 / 0.4e1 * t445 * t147 - 0.5e1 / 0.4e1 * t445 * t176
  v4rho4_0_ = -0.9e1 / 0.32e2 / t2 / t1 * (jnp.pi * t31 - 0.4e1 / 0.3e1 * t22 * t36) * t41 + 0.3e1 / 0.4e1 / t44 * (t47 * t59 * t64 / 0.2e1 - 0.2e1 / 0.3e1 * t68 * t70) * t41 - 0.9e1 / 0.4e1 / t2 * (t83 * t90 / 0.4e1 + t105 * t64 / 0.2e1 + t108 * t110 / 0.2e1 - t108 * t116 / 0.2e1 - t108 * t119 / 0.2e1 + t124 * t125 / 0.3e1 - 0.2e1 / 0.3e1 * t68 * t129) * t41 - 0.3e1 * t2 * t236 * t41 - t44 * (t290 + t381 + t424 + t454) * t41 / 0.2e1

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t4 = 0.1e1 / t2 / r0
  t7 = tau0 * t4
  t8 = r0 ** 2
  t10 = 0.1e1 / t2 / t8
  t12 = s0 * t10 / 0.8e1
  t14 = 0.1e1 / jnp.pi
  t15 = (l0 * t4 / 0.4e1 - t7 + t12) * t14
  t16 = -0.9999999999e0 < t15
  t17 = f.my_piecewise3(t16, t15, -0.9999999999e0)
  t18 = jnp.exp(-1)
  t20 = lambertw(t17 * t18)
  t21 = 0.1e1 + t20
  t22 = t21 / 0.2e1
  t23 = scipy.special.i1(t22)
  t24 = jnp.pi * t23
  t28 = 0.5e1 / 0.3e1 * tau0 * t10
  t31 = 0.1e1 / t2 / t8 / r0
  t33 = s0 * t31 / 0.3e1
  t36 = f.my_piecewise3(t16, (-0.5e1 / 0.12e2 * l0 * t10 + t28 - t33) * t14, 0)
  t39 = t20 / t21
  t41 = t39 / t17
  t44 = t7 - t12
  t45 = 0.1e-9 < t44
  t46 = f.my_piecewise3(t45, t44, 0.1e-9)
  t47 = jnp.sqrt(t46)
  t49 = t14 / t47
  t51 = f.my_piecewise3(t45, -t28 + t33, 0)
  t54 = t24 * t36 * t41 / 0.2e1 - 0.2e1 / 0.3e1 * t49 * t51
  t55 = jnp.sqrt(r0)
  t56 = t54 * t55
  t58 = jax.scipy.special.i0(t22)
  t62 = jnp.pi * t58 - 0.4e1 / 0.3e1 * t14 * t47
  t63 = 0.1e1 / t55
  t64 = t62 * t63
  t65 = r0 + r1
  t70 = t36 ** 2
  t72 = t20 ** 2
  t73 = t21 ** 2
  t74 = 0.1e1 / t73
  t76 = t17 ** 2
  t77 = 0.1e1 / t76
  t84 = 0.40e2 / 0.9e1 * tau0 * t31
  t85 = t8 ** 2
  t89 = 0.11e2 / 0.9e1 * s0 / t2 / t85
  t92 = f.my_piecewise3(t16, (0.10e2 / 0.9e1 * l0 * t31 - t84 + t89) * t14, 0)
  t96 = t24 * t70
  t113 = t51 ** 2
  t117 = f.my_piecewise3(t45, t84 - t89, 0)
  d11 = -0.2e1 * t56 - t64 - t65 * (jnp.pi * (t58 - 0.1e1 / t22 * t23) * t70 * t72 * t74 * t77 / 0.4e1 + t24 * t92 * t41 / 0.2e1 + t96 * t20 * t74 * t77 / 0.2e1 - t96 * t72 / t73 / t21 * t77 / 0.2e1 - t96 * t39 * t77 / 0.2e1 + t14 / t47 / t46 * t113 / 0.3e1 - 0.2e1 / 0.3e1 * t49 * t117) * t55 - t65 * t54 * t63 + t65 * t62 / t55 / r0 / 0.4e1
  d12 = -t56 - t64 / 0.2e1
  d22 = 0.0e0
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

  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t4 = 0.1e1 / t2 / r0
  t7 = tau0 * t4
  t8 = r0 ** 2
  t10 = 0.1e1 / t2 / t8
  t12 = s0 * t10 / 0.8e1
  t14 = 0.1e1 / jnp.pi
  t15 = (l0 * t4 / 0.4e1 - t7 + t12) * t14
  t16 = -0.9999999999e0 < t15
  t17 = f.my_piecewise3(t16, t15, -0.9999999999e0)
  t18 = jnp.exp(-1)
  t20 = scipy.special.lambertw(t17 * t18)
  t21 = 0.1e1 + t20
  t22 = t21 / 0.2e1
  t23 = scipy.special.i0(t22)
  t24 = 0.1e1 / t22
  t25 = scipy.special.i1(t22)
  t27 = -t24 * t25 + t23
  t28 = jnp.pi * t27
  t32 = 0.5e1 / 0.3e1 * tau0 * t10
  t35 = 0.1e1 / t2 / t8 / r0
  t37 = s0 * t35 / 0.3e1
  t40 = f.my_piecewise3(t16, (-0.5e1 / 0.12e2 * l0 * t10 + t32 - t37) * t14, 0)
  t41 = t40 ** 2
  t43 = t20 ** 2
  t44 = t21 ** 2
  t45 = 0.1e1 / t44
  t46 = t43 * t45
  t47 = t17 ** 2
  t48 = 0.1e1 / t47
  t49 = t46 * t48
  t52 = jnp.pi * t25
  t56 = 0.40e2 / 0.9e1 * tau0 * t35
  t57 = t8 ** 2
  t59 = 0.1e1 / t2 / t57
  t61 = 0.11e2 / 0.9e1 * s0 * t59
  t64 = f.my_piecewise3(t16, (0.10e2 / 0.9e1 * l0 * t35 - t56 + t61) * t14, 0)
  t65 = t52 * t64
  t67 = t20 / t21
  t69 = t67 / t17
  t72 = t52 * t41
  t73 = t20 * t45
  t78 = 0.1e1 / t44 / t21
  t79 = t43 * t78
  t86 = t7 - t12
  t87 = 0.1e-9 < t86
  t88 = f.my_piecewise3(t87, t86, 0.1e-9)
  t89 = jnp.sqrt(t88)
  t92 = t14 / t89 / t88
  t94 = f.my_piecewise3(t87, -t32 + t37, 0)
  t95 = t94 ** 2
  t99 = t14 / t89
  t101 = f.my_piecewise3(t87, t56 - t61, 0)
  t104 = t28 * t41 * t49 / 0.4e1 + t65 * t69 / 0.2e1 + t72 * t73 * t48 / 0.2e1 - t72 * t79 * t48 / 0.2e1 - t72 * t67 * t48 / 0.2e1 + t92 * t95 / 0.3e1 - 0.2e1 / 0.3e1 * t99 * t101
  t105 = jnp.sqrt(r0)
  t113 = t52 * t40 * t69 / 0.2e1 - 0.2e1 / 0.3e1 * t99 * t94
  t114 = 0.1e1 / t105
  t120 = jnp.pi * t23 - 0.4e1 / 0.3e1 * t14 * t89
  t122 = 0.1e1 / t105 / r0
  t125 = r0 + r1
  t131 = t41 * t40
  t132 = t28 * t131
  t134 = 0.1e1 / t47 / t17
  t138 = t48 * t40
  t142 = t52 * t131
  t146 = t79 * t134
  t162 = t43 * t20
  t163 = t44 ** 2
  t164 = 0.1e1 / t163
  t182 = t88 ** 2
  t192 = 0.440e3 / 0.27e2 * tau0 * t59
  t197 = 0.154e3 / 0.27e2 * s0 / t2 / t57 / r0
  t199 = f.my_piecewise3(t87, -t192 + t197, 0)
  t204 = t22 ** 2
  t222 = f.my_piecewise3(t16, (-0.110e3 / 0.27e2 * l0 * t59 + t192 - t197) * t14, 0)
  t226 = 0.3e1 / 0.4e1 * t28 * t40 * t46 * t48 * t64 - 0.3e1 / 0.4e1 * t132 * t46 * t134 - 0.3e1 / 0.2e1 * t65 * t67 * t138 - 0.3e1 / 0.2e1 * t142 * t73 * t134 + 0.3e1 / 0.2e1 * t142 * t146 + t142 * t67 * t134 + 0.3e1 / 0.2e1 * t65 * t40 * t20 * t45 * t48 + t142 * t20 * t78 * t134 / 0.2e1 + 0.3e1 / 0.4e1 * t132 * t146 - 0.3e1 / 0.4e1 * t132 * t162 * t164 * t134 - 0.3e1 / 0.2e1 * t65 * t79 * t138 - 0.2e1 * t142 * t43 * t164 * t134 + 0.3e1 / 0.2e1 * t142 * t162 / t163 / t21 * t134 - t14 / t89 / t182 * t95 * t94 / 0.2e1 + t92 * t94 * t101 - 0.2e1 / 0.3e1 * t99 * t199 + jnp.pi * (t25 * t40 * t69 / 0.2e1 + 0.1e1 / t204 * t25 * t40 * t69 / 0.2e1 - t24 * t27 * t40 * t69 / 0.2e1) * t41 * t49 / 0.4e1 + t52 * t222 * t69 / 0.2e1
  d111 = -0.3e1 * t104 * t105 - 0.3e1 * t113 * t114 + 0.3e1 / 0.4e1 * t120 * t122 - t125 * t226 * t105 - 0.3e1 / 0.2e1 * t125 * t104 * t114 + 0.3e1 / 0.4e1 * t125 * t113 * t122 - 0.3e1 / 0.8e1 * t125 * t120 / t105 / t8

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

  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t4 = 0.1e1 / t2 / r0
  t7 = tau0 * t4
  t8 = r0 ** 2
  t10 = 0.1e1 / t2 / t8
  t12 = s0 * t10 / 0.8e1
  t14 = 0.1e1 / jnp.pi
  t15 = (l0 * t4 / 0.4e1 - t7 + t12) * t14
  t16 = -0.9999999999e0 < t15
  t17 = f.my_piecewise3(t16, t15, -0.9999999999e0)
  t18 = jnp.exp(-1)
  t20 = scipy.special.lambertw(t17 * t18)
  t21 = 0.1e1 + t20
  t22 = t21 / 0.2e1
  t23 = scipy.special.i0(t22)
  t24 = 0.1e1 / t22
  t25 = scipy.special.i1(t22)
  t27 = -t24 * t25 + t23
  t28 = jnp.pi * t27
  t32 = 0.5e1 / 0.3e1 * tau0 * t10
  t33 = t8 * r0
  t35 = 0.1e1 / t2 / t33
  t37 = s0 * t35 / 0.3e1
  t40 = f.my_piecewise3(t16, (-0.5e1 / 0.12e2 * l0 * t10 + t32 - t37) * t14, 0)
  t41 = t28 * t40
  t42 = t20 ** 2
  t43 = t21 ** 2
  t44 = 0.1e1 / t43
  t45 = t42 * t44
  t46 = t17 ** 2
  t47 = 0.1e1 / t46
  t51 = 0.40e2 / 0.9e1 * tau0 * t35
  t52 = t8 ** 2
  t54 = 0.1e1 / t2 / t52
  t56 = 0.11e2 / 0.9e1 * s0 * t54
  t59 = f.my_piecewise3(t16, (0.10e2 / 0.9e1 * l0 * t35 - t51 + t56) * t14, 0)
  t61 = t45 * t47 * t59
  t64 = t40 ** 2
  t65 = t64 * t40
  t66 = t28 * t65
  t68 = 0.1e1 / t46 / t17
  t69 = t45 * t68
  t72 = jnp.pi * t25
  t73 = t72 * t59
  t75 = t20 / t21
  t76 = t47 * t40
  t77 = t75 * t76
  t80 = t72 * t65
  t81 = t20 * t44
  t85 = t43 * t21
  t86 = 0.1e1 / t85
  t87 = t42 * t86
  t88 = t87 * t68
  t95 = t40 * t20 * t44 * t47
  t98 = t20 * t86
  t104 = t42 * t20
  t105 = t43 ** 2
  t106 = 0.1e1 / t105
  t107 = t104 * t106
  t108 = t107 * t68
  t111 = t87 * t76
  t114 = t42 * t106
  t119 = 0.1e1 / t105 / t21
  t120 = t104 * t119
  t124 = t7 - t12
  t125 = 0.1e-9 < t124
  t126 = f.my_piecewise3(t125, t124, 0.1e-9)
  t127 = t126 ** 2
  t128 = jnp.sqrt(t126)
  t131 = t14 / t128 / t127
  t133 = f.my_piecewise3(t125, -t32 + t37, 0)
  t134 = t133 ** 2
  t140 = t14 / t128 / t126
  t142 = f.my_piecewise3(t125, t51 - t56, 0)
  t146 = t14 / t128
  t148 = 0.440e3 / 0.27e2 * tau0 * t54
  t151 = 0.1e1 / t2 / t52 / r0
  t153 = 0.154e3 / 0.27e2 * s0 * t151
  t155 = f.my_piecewise3(t125, -t148 + t153, 0)
  t160 = t75 / t17
  t162 = t22 ** 2
  t163 = 0.1e1 / t162
  t164 = t163 * t25
  t167 = t24 * t27
  t171 = t164 * t40 * t160 / 0.2e1 - t167 * t40 * t160 / 0.2e1 + t25 * t40 * t160 / 0.2e1
  t172 = jnp.pi * t171
  t174 = t45 * t47
  t181 = f.my_piecewise3(t16, (-0.110e3 / 0.27e2 * l0 * t54 + t148 - t153) * t14, 0)
  t182 = t72 * t181
  t185 = 0.3e1 / 0.4e1 * t41 * t61 - 0.3e1 / 0.4e1 * t66 * t69 - 0.3e1 / 0.2e1 * t73 * t77 - 0.3e1 / 0.2e1 * t80 * t81 * t68 + 0.3e1 / 0.2e1 * t80 * t88 + t80 * t75 * t68 + 0.3e1 / 0.2e1 * t73 * t95 + t80 * t98 * t68 / 0.2e1 + 0.3e1 / 0.4e1 * t66 * t88 - 0.3e1 / 0.4e1 * t66 * t108 - 0.3e1 / 0.2e1 * t73 * t111 - 0.2e1 * t80 * t114 * t68 + 0.3e1 / 0.2e1 * t80 * t120 * t68 - t131 * t134 * t133 / 0.2e1 + t140 * t133 * t142 - 0.2e1 / 0.3e1 * t146 * t155 + t172 * t64 * t174 / 0.4e1 + t182 * t160 / 0.2e1
  t186 = jnp.sqrt(r0)
  t189 = t28 * t64
  t194 = t72 * t64
  t195 = t81 * t47
  t198 = t87 * t47
  t201 = t75 * t47
  t208 = t189 * t174 / 0.4e1 + t73 * t160 / 0.2e1 + t194 * t195 / 0.2e1 - t194 * t198 / 0.2e1 - t194 * t201 / 0.2e1 + t140 * t134 / 0.3e1 - 0.2e1 / 0.3e1 * t146 * t142
  t209 = 0.1e1 / t186
  t217 = t72 * t40 * t160 / 0.2e1 - 0.2e1 / 0.3e1 * t146 * t133
  t219 = 0.1e1 / t186 / r0
  t225 = jnp.pi * t23 - 0.4e1 / 0.3e1 * t14 * t128
  t227 = 0.1e1 / t186 / t8
  t230 = r0 + r1
  t235 = t134 ** 2
  t238 = t142 ** 2
  t241 = 0.6160e4 / 0.81e2 * tau0 * t151
  t246 = 0.2618e4 / 0.81e2 * s0 / t2 / t52 / t8
  t248 = f.my_piecewise3(t125, t241 - t246, 0)
  t257 = t25 * t64
  t277 = t164 * t64
  t291 = t167 * t64
  t298 = t27 * t64 * t174 / 0.4e1 + t25 * t59 * t160 / 0.2e1 + t257 * t195 / 0.2e1 - t257 * t198 / 0.2e1 - t257 * t201 / 0.2e1 - 0.1e1 / t162 / t22 * t25 * t64 * t174 / 0.2e1 + t163 * t27 * t64 * t174 / 0.2e1 + t164 * t59 * t160 / 0.2e1 + t277 * t195 / 0.2e1 - t277 * t198 / 0.2e1 - t277 * t201 / 0.2e1 - t24 * t171 * t40 * t160 / 0.2e1 - t167 * t59 * t160 / 0.2e1 - t291 * t195 / 0.2e1 + t291 * t198 / 0.2e1 + t291 * t201 / 0.2e1
  t307 = f.my_piecewise3(t16, (0.1540e4 / 0.81e2 * l0 * t151 - t241 + t246) * t14, 0)
  t311 = t64 ** 2
  t312 = t72 * t311
  t313 = t46 ** 2
  t314 = 0.1e1 / t313
  t318 = t87 * t314
  t324 = t59 ** 2
  t325 = t72 * t324
  t335 = 0.5e1 / 0.4e1 * t14 / t128 / t127 / t126 * t235 + t140 * t238 - 0.2e1 / 0.3e1 * t146 * t248 + jnp.pi * t298 * t64 * t174 / 0.4e1 + t72 * t307 * t160 / 0.2e1 + 0.11e2 / 0.2e1 * t312 * t81 * t314 - 0.11e2 / 0.2e1 * t312 * t318 - 0.3e1 * t312 * t75 * t314 + 0.3e1 / 0.2e1 * t325 * t195 - 0.3e1 * t312 * t98 * t314 + t312 * t20 * t106 * t314 / 0.2e1
  t336 = t28 * t311
  t342 = t172 * t65
  t345 = t114 * t314
  t354 = t120 * t314
  t363 = t42 ** 2
  t365 = 0.1e1 / t105 / t43
  t370 = -0.9e1 / 0.2e1 * t336 * t318 + 0.9e1 / 0.2e1 * t336 * t107 * t314 - 0.5e1 / 0.4e1 * t342 * t69 + 0.7e1 / 0.4e1 * t336 * t345 + 0.5e1 / 0.4e1 * t342 * t88 - 0.5e1 / 0.4e1 * t342 * t108 + 0.12e2 * t312 * t345 - 0.9e1 * t312 * t354 - 0.11e2 / 0.2e1 * t312 * t42 * t119 * t314 - 0.11e2 / 0.2e1 * t336 * t354 + 0.15e2 / 0.4e1 * t336 * t363 * t365 * t314
  t398 = t64 * t20
  t408 = 0.25e2 / 0.2e1 * t312 * t104 * t365 * t314 - 0.15e2 / 0.2e1 * t312 * t363 / t105 / t85 * t314 - 0.3e1 / 0.2e1 * t325 * t198 + 0.3e1 / 0.4e1 * t28 * t324 * t174 + 0.11e2 / 0.4e1 * t336 * t45 * t314 - 0.3e1 / 0.2e1 * t325 * t201 - 0.3e1 * t131 * t134 * t142 + 0.4e1 / 0.3e1 * t140 * t133 * t155 + 0.3e1 * t73 * t398 * t86 * t68 - 0.2e1 * t182 * t111 + t41 * t45 * t47 * t181
  t420 = t68 * t59
  t427 = t68 * t64
  t445 = -0.2e1 * t182 * t77 + 0.2e1 * t182 * t95 + 0.5e1 / 0.4e1 * t172 * t40 * t61 - 0.9e1 * t73 * t398 * t44 * t68 + 0.9e1 / 0.2e1 * t189 * t87 * t420 - 0.9e1 / 0.2e1 * t189 * t107 * t420 + 0.9e1 * t73 * t87 * t427 - 0.12e2 * t73 * t64 * t42 * t106 * t68 + 0.9e1 * t73 * t120 * t427 - 0.9e1 / 0.2e1 * t189 * t45 * t420 + 0.6e1 * t73 * t75 * t427
  d1111 = -0.4e1 * t185 * t186 - 0.6e1 * t208 * t209 + 0.3e1 * t217 * t219 - 0.3e1 / 0.2e1 * t225 * t227 - t230 * (t335 + t370 + t408 + t445) * t186 - 0.2e1 * t230 * t185 * t209 + 0.3e1 / 0.2e1 * t230 * t208 * t219 - 0.3e1 / 0.2e1 * t230 * t217 * t227 + 0.15e2 / 0.16e2 * t230 * t225 / t186 / t33

  res = {'v4rho4': d1111}
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  prhg07_C = lambda x, u, t: (u - 4 * t + x ** 2 / 2) / 4

  prhg07_y = lambda x: LambertW(jnp.maximum(x / jnp.pi, -0.9999999999) * jnp.exp(-1)) + 1

  prhg07_v = lambda y: jnp.pi / X_FACTOR_2D_C * BesselI(0, y / 2)

  prp10_f = lambda rs, z, x, u, t: -(X_FACTOR_2D_C * prhg07_v(prhg07_y(prhg07_C(x, u, t))) - 2 * jnp.sqrt(2) / (3 * jnp.pi) * jnp.sqrt(2 * jnp.maximum(t - x ** 2 / 8, 1e-10))) * f.n_spin(rs, z) ** (1 / 2)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1=None: prp10_f(rs, z, xs0, u0, t0)

  _raise_value_error = lambda msg: (_ for _ in ()).throw(ValueError(msg))

  BesselI = lambda order, value: (
      bessel_i0(value)
      if order == 0
      else (
          bessel_i1(value)
          if order == 1
          else _raise_value_error(f"Unsupported BesselI order: {order}")
      )
  )

  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t4 = 0.1e1 / t2 / r0
  t7 = tau0 * t4
  t8 = r0 ** 2
  t10 = 0.1e1 / t2 / t8
  t12 = s0 * t10 / 0.8e1
  t14 = 0.1e1 / jnp.pi
  t15 = (l0 * t4 / 0.4e1 - t7 + t12) * t14
  t16 = -0.9999999999e0 < t15
  t17 = f.my_piecewise3(t16, t15, -0.9999999999e0)
  t18 = jnp.exp(-1)
  t20 = lambertw(t17 * t18)
  t21 = t20 + 0.1e1
  t22 = t21 / 0.2e1
  t23 = bessel_i0(t22)
  t25 = t7 - t12
  t26 = 0.1e-9 < t25
  t27 = f.my_piecewise3(t26, t25, 0.1e-9)
  t28 = jnp.sqrt(t27)
  t31 = jnp.pi * t23 - 0.4e1 / 0.3e1 * t14 * t28
  t32 = jnp.sqrt(r0)
  t33 = t31 * t32
  t34 = r0 + r1
  t35 = bessel_i1(t22)
  t36 = jnp.pi * t35
  t40 = 0.5e1 / 0.3e1 * tau0 * t10
  t45 = s0 / t2 / t8 / r0 / 0.3e1
  t48 = f.my_piecewise3(t16, (-0.5e1 / 0.12e2 * l0 * t10 + t40 - t45) * t14, 0)
  t51 = t20 / t21
  t52 = 0.1e1 / t17
  t53 = t51 * t52
  t57 = t14 / t28
  t59 = f.my_piecewise3(t26, -t40 + t45, 0)
  vrho_0_ = -t33 - t34 * (t36 * t48 * t53 / 0.2e1 - 0.2e1 / 0.3e1 * t57 * t59) * t32 - t34 * t31 / t32 / 0.2e1
  vrho_1_ = -t33
  t71 = f.my_piecewise3(t16, t10 * t14 / 0.8e1, 0)
  t76 = f.my_piecewise3(t26, -t10 / 0.8e1, 0)
  vsigma_0_ = -t34 * (t36 * t71 * t53 / 0.2e1 - 0.2e1 / 0.3e1 * t57 * t76) * t32
  vsigma_1_ = 0.0e0
  vsigma_2_ = 0.0e0
  t83 = t4 * t14
  t85 = f.my_piecewise3(t16, t83 / 0.4e1, 0)
  vlapl_0_ = -t34 * jnp.pi * t35 * t85 * t51 * t52 * t32 / 0.2e1
  vlapl_1_ = 0.0e0
  t92 = f.my_piecewise3(t16, -t83, 0)
  t96 = f.my_piecewise3(t26, t4, 0)
  vtau_0_ = -t34 * (t36 * t92 * t53 / 0.2e1 - 0.2e1 / 0.3e1 * t57 * t96) * t32
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
  prhg07_C = lambda x, u, t: (u - 4 * t + x ** 2 / 2) / 4

  prhg07_y = lambda x: LambertW(jnp.maximum(x / jnp.pi, -0.9999999999) * jnp.exp(-1)) + 1

  prhg07_v = lambda y: jnp.pi / X_FACTOR_2D_C * BesselI(0, y / 2)

  prp10_f = lambda rs, z, x, u, t: -(X_FACTOR_2D_C * prhg07_v(prhg07_y(prhg07_C(x, u, t))) - 2 * jnp.sqrt(2) / (3 * jnp.pi) * jnp.sqrt(2 * jnp.maximum(t - x ** 2 / 8, 1e-10))) * f.n_spin(rs, z) ** (1 / 2)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1=None: prp10_f(rs, z, xs0, u0, t0)

  _raise_value_error = lambda msg: (_ for _ in ()).throw(ValueError(msg))

  BesselI = lambda order, value: (
      bessel_i0(value)
      if order == 0
      else (
          bessel_i1(value)
          if order == 1
          else _raise_value_error(f"Unsupported BesselI order: {order}")
      )
  )

  t1 = 2 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t3 = l0 * t2
  t4 = r0 ** (0.1e1 / 0.3e1)
  t5 = t4 ** 2
  t7 = 0.1e1 / t5 / r0
  t10 = tau0 * t2
  t11 = t10 * t7
  t12 = s0 * t2
  t13 = r0 ** 2
  t15 = 0.1e1 / t5 / t13
  t17 = t12 * t15 / 0.8e1
  t19 = 0.1e1 / jnp.pi
  t20 = (t3 * t7 / 0.4e1 - t11 + t17) * t19
  t21 = -0.9999999999e0 < t20
  t22 = f.my_piecewise3(t21, t20, -0.9999999999e0)
  t23 = jnp.exp(-1)
  t25 = lambertw(t22 * t23)
  t26 = t25 + 0.1e1
  t27 = t26 / 0.2e1
  t28 = bessel_i0(t27)
  t30 = t11 - t17
  t31 = 0.1e-9 < t30
  t32 = f.my_piecewise3(t31, t30, 0.1e-9)
  t33 = jnp.sqrt(t32)
  t37 = jnp.sqrt(0.2e1)
  t39 = jnp.sqrt(r0)
  t42 = t39 * r0
  t43 = bessel_i1(t27)
  t44 = jnp.pi * t43
  t48 = 0.5e1 / 0.3e1 * t10 * t15
  t53 = t12 / t5 / t13 / r0 / 0.3e1
  t56 = f.my_piecewise3(t21, (-0.5e1 / 0.12e2 * t3 * t15 + t48 - t53) * t19, 0)
  t59 = t25 / t26
  t60 = 0.1e1 / t22
  t61 = t59 * t60
  t65 = t19 / t33
  t67 = f.my_piecewise3(t31, -t48 + t53, 0)
  vrho_0_ = -0.3e1 / 0.4e1 * (jnp.pi * t28 - 0.4e1 / 0.3e1 * t19 * t33) * t37 * t39 - t42 * (t44 * t56 * t61 / 0.2e1 - 0.2e1 / 0.3e1 * t65 * t67) * t37 / 0.2e1
  t74 = t2 * t15
  t77 = f.my_piecewise3(t21, t74 * t19 / 0.8e1, 0)
  t82 = f.my_piecewise3(t31, -t74 / 0.8e1, 0)
  vsigma_0_ = -t42 * (t44 * t77 * t61 / 0.2e1 - 0.2e1 / 0.3e1 * t65 * t82) * t37 / 0.2e1
  t90 = t2 * t7
  t91 = t90 * t19
  t93 = f.my_piecewise3(t21, t91 / 0.4e1, 0)
  vlapl_0_ = -t42 * jnp.pi * t43 * t93 * t59 * t60 * t37 / 0.4e1
  t100 = f.my_piecewise3(t21, -t91, 0)
  t104 = f.my_piecewise3(t31, t90, 0)
  vtau_0_ = -t42 * (t44 * t100 * t61 / 0.2e1 - 0.2e1 / 0.3e1 * t65 * t104) * t37 / 0.2e1
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
  return res

