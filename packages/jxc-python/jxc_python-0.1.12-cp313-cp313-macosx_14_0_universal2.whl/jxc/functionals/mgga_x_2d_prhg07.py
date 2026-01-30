"""Generated from mgga_x_2d_prhg07.mpl."""

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

  prhg07_f = lambda x, u, t: prhg07_v(prhg07_y(prhg07_C(x, u, t))) / 2

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, prhg07_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  prhg07_f = lambda x, u, t: prhg07_v(prhg07_y(prhg07_C(x, u, t))) / 2

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, prhg07_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  prhg07_C = lambda x, u, t: (u - 4 * t + x ** 2 / 2) / 4

  prhg07_y = lambda x: LambertW(jnp.maximum(x / jnp.pi, -0.9999999999) * jnp.exp(-1)) + 1

  prhg07_v = lambda y: jnp.pi / X_FACTOR_2D_C * BesselI(0, y / 2)

  prhg07_f = lambda x, u, t: prhg07_v(prhg07_y(prhg07_C(x, u, t))) / 2

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, prhg07_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.6e1)
  t5 = t2 * t3 * jnp.pi
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
  t28 = r0 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t31 = 0.1e1 / t29 / r0
  t35 = r0 ** 2
  t37 = 0.1e1 / t29 / t35
  t41 = 0.1e1 / jnp.pi
  t42 = (l0 * t31 / 0.4e1 - tau0 * t31 + s0 * t37 / 0.8e1) * t41
  t43 = -0.9999999999e0 < t42
  t44 = f.my_piecewise3(t43, t42, -0.9999999999e0)
  t45 = jnp.exp(-1)
  t47 = lambertw(t44 * t45)
  t48 = t47 + 0.1e1
  t49 = t48 / 0.2e1
  t50 = jax.scipy.special.i0(t49)
  t54 = f.my_piecewise3(t1, 0, -0.9e1 / 0.128e3 * t5 * t27 * t50)
  t55 = r1 <= f.p.dens_threshold
  t56 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t57 = 0.1e1 + t56
  t58 = t57 <= f.p.zeta_threshold
  t59 = t57 ** (0.1e1 / 0.3e1)
  t61 = f.my_piecewise3(t58, t22, t59 * t57)
  t62 = t61 * t26
  t63 = r1 ** (0.1e1 / 0.3e1)
  t64 = t63 ** 2
  t66 = 0.1e1 / t64 / r1
  t70 = r1 ** 2
  t72 = 0.1e1 / t64 / t70
  t76 = (l1 * t66 / 0.4e1 - tau1 * t66 + s2 * t72 / 0.8e1) * t41
  t77 = -0.9999999999e0 < t76
  t78 = f.my_piecewise3(t77, t76, -0.9999999999e0)
  t80 = lambertw(t78 * t45)
  t81 = t80 + 0.1e1
  t82 = t81 / 0.2e1
  t83 = jax.scipy.special.i0(t82)
  t87 = f.my_piecewise3(t55, 0, -0.9e1 / 0.128e3 * t5 * t62 * t83)
  t88 = t6 ** 2
  t90 = t16 / t88
  t91 = t7 - t90
  t92 = f.my_piecewise5(t10, 0, t14, 0, t91)
  t95 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t92)
  t100 = t26 ** 2
  t101 = 0.1e1 / t100
  t105 = 0.3e1 / 0.128e3 * t5 * t25 * t101 * t50
  t106 = t5 * t27
  t107 = scipy.special.i1(t49)
  t119 = f.my_piecewise3(t43, (-0.5e1 / 0.12e2 * l0 * t37 + 0.5e1 / 0.3e1 * tau0 * t37 - s0 / t29 / t35 / r0 / 0.3e1) * t41, 0)
  t124 = t47 / t48 / t44
  t129 = f.my_piecewise3(t1, 0, -0.9e1 / 0.128e3 * t5 * t95 * t26 * t50 - t105 - 0.9e1 / 0.256e3 * t106 * t107 * t119 * t124)
  t131 = f.my_piecewise5(t14, 0, t10, 0, -t91)
  t134 = f.my_piecewise3(t58, 0, 0.4e1 / 0.3e1 * t59 * t131)
  t142 = 0.3e1 / 0.128e3 * t5 * t61 * t101 * t83
  t144 = f.my_piecewise3(t55, 0, -0.9e1 / 0.128e3 * t5 * t134 * t26 * t83 - t142)
  vrho_0_ = t54 + t87 + t6 * (t129 + t144)
  t147 = -t7 - t90
  t148 = f.my_piecewise5(t10, 0, t14, 0, t147)
  t151 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t148)
  t157 = f.my_piecewise3(t1, 0, -0.9e1 / 0.128e3 * t5 * t151 * t26 * t50 - t105)
  t159 = f.my_piecewise5(t14, 0, t10, 0, -t147)
  t162 = f.my_piecewise3(t58, 0, 0.4e1 / 0.3e1 * t59 * t159)
  t167 = t5 * t62
  t168 = scipy.special.i1(t82)
  t180 = f.my_piecewise3(t77, (-0.5e1 / 0.12e2 * l1 * t72 + 0.5e1 / 0.3e1 * tau1 * t72 - s2 / t64 / t70 / r1 / 0.3e1) * t41, 0)
  t185 = t80 / t81 / t78
  t190 = f.my_piecewise3(t55, 0, -0.9e1 / 0.128e3 * t5 * t162 * t26 * t83 - t142 - 0.9e1 / 0.256e3 * t167 * t168 * t180 * t185)
  vrho_1_ = t54 + t87 + t6 * (t157 + t190)
  t195 = f.my_piecewise3(t43, t37 * t41 / 0.8e1, 0)
  t200 = f.my_piecewise3(t1, 0, -0.9e1 / 0.256e3 * t106 * t107 * t195 * t124)
  vsigma_0_ = t6 * t200
  vsigma_1_ = 0.0e0
  t203 = f.my_piecewise3(t77, t72 * t41 / 0.8e1, 0)
  t208 = f.my_piecewise3(t55, 0, -0.9e1 / 0.256e3 * t167 * t168 * t203 * t185)
  vsigma_2_ = t6 * t208
  t209 = t31 * t41
  t211 = f.my_piecewise3(t43, t209 / 0.4e1, 0)
  t216 = f.my_piecewise3(t1, 0, -0.9e1 / 0.256e3 * t106 * t107 * t211 * t124)
  vlapl_0_ = t6 * t216
  t217 = t66 * t41
  t219 = f.my_piecewise3(t77, t217 / 0.4e1, 0)
  t224 = f.my_piecewise3(t55, 0, -0.9e1 / 0.256e3 * t167 * t168 * t219 * t185)
  vlapl_1_ = t6 * t224
  t225 = f.my_piecewise3(t43, -t209, 0)
  t230 = f.my_piecewise3(t1, 0, -0.9e1 / 0.256e3 * t106 * t107 * t225 * t124)
  vtau_0_ = t6 * t230
  t231 = f.my_piecewise3(t77, -t217, 0)
  t236 = f.my_piecewise3(t55, 0, -0.9e1 / 0.256e3 * t167 * t168 * t231 * t185)
  vtau_1_ = t6 * t236
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

  prhg07_f = lambda x, u, t: prhg07_v(prhg07_y(prhg07_C(x, u, t))) / 2

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, prhg07_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.6e1)
  t6 = t3 * t4 * jnp.pi
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t17 * t18
  t20 = 2 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t22 = l0 * t21
  t23 = t18 ** 2
  t25 = 0.1e1 / t23 / r0
  t28 = tau0 * t21
  t30 = s0 * t21
  t31 = r0 ** 2
  t33 = 0.1e1 / t23 / t31
  t37 = 0.1e1 / jnp.pi
  t38 = (t22 * t25 / 0.4e1 - t28 * t25 + t30 * t33 / 0.8e1) * t37
  t39 = -0.9999999999e0 < t38
  t40 = f.my_piecewise3(t39, t38, -0.9999999999e0)
  t41 = jnp.exp(-1)
  t43 = lambertw(t40 * t41)
  t44 = t43 + 0.1e1
  t45 = t44 / 0.2e1
  t46 = jax.scipy.special.i0(t45)
  t50 = f.my_piecewise3(t2, 0, -0.9e1 / 0.128e3 * t6 * t19 * t46)
  t56 = t6 * t19
  t57 = scipy.special.i1(t45)
  t69 = f.my_piecewise3(t39, (-0.5e1 / 0.12e2 * t22 * t33 + 0.5e1 / 0.3e1 * t28 * t33 - t30 / t23 / t31 / r0 / 0.3e1) * t37, 0)
  t74 = t43 / t44 / t40
  t79 = f.my_piecewise3(t2, 0, -0.3e1 / 0.128e3 * t6 * t17 / t23 * t46 - 0.9e1 / 0.256e3 * t56 * t57 * t69 * t74)
  vrho_0_ = 0.2e1 * r0 * t79 + 0.2e1 * t50
  t85 = f.my_piecewise3(t39, t21 * t33 * t37 / 0.8e1, 0)
  t90 = f.my_piecewise3(t2, 0, -0.9e1 / 0.256e3 * t56 * t57 * t85 * t74)
  vsigma_0_ = 0.2e1 * r0 * t90
  t93 = t21 * t25 * t37
  t95 = f.my_piecewise3(t39, t93 / 0.4e1, 0)
  t100 = f.my_piecewise3(t2, 0, -0.9e1 / 0.256e3 * t56 * t57 * t95 * t74)
  vlapl_0_ = 0.2e1 * r0 * t100
  t102 = f.my_piecewise3(t39, -t93, 0)
  t107 = f.my_piecewise3(t2, 0, -0.9e1 / 0.256e3 * t56 * t57 * t102 * t74)
  vtau_0_ = 0.2e1 * r0 * t107
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
  t4 = jnp.pi ** (0.1e1 / 0.6e1)
  t6 = t3 * t4 * jnp.pi
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
  t22 = 2 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = l0 * t23
  t26 = 0.1e1 / t19 / r0
  t29 = tau0 * t23
  t31 = s0 * t23
  t32 = r0 ** 2
  t34 = 0.1e1 / t19 / t32
  t38 = 0.1e1 / jnp.pi
  t39 = (t24 * t26 / 0.4e1 - t29 * t26 + t31 * t34 / 0.8e1) * t38
  t40 = -0.9999999999e0 < t39
  t41 = f.my_piecewise3(t40, t39, -0.9999999999e0)
  t42 = jnp.exp(-1)
  t44 = lambertw(t41 * t42)
  t45 = t44 + 0.1e1
  t46 = t45 / 0.2e1
  t47 = jax.scipy.special.i0(t46)
  t52 = t6 * t17 * t18
  t53 = scipy.special.i1(t46)
  t60 = 0.1e1 / t19 / t32 / r0
  t65 = f.my_piecewise3(t40, (-0.5e1 / 0.12e2 * t24 * t34 + 0.5e1 / 0.3e1 * t29 * t34 - t31 * t60 / 0.3e1) * t38, 0)
  t68 = t44 / t45
  t70 = t68 / t41
  t71 = t53 * t65 * t70
  t75 = f.my_piecewise3(t2, 0, -0.3e1 / 0.128e3 * t6 * t21 * t47 - 0.9e1 / 0.256e3 * t52 * t71)
  t87 = t65 ** 2
  t89 = t44 ** 2
  t90 = t45 ** 2
  t91 = 0.1e1 / t90
  t93 = t41 ** 2
  t94 = 0.1e1 / t93
  t103 = t32 ** 2
  t110 = f.my_piecewise3(t40, (0.10e2 / 0.9e1 * t24 * t60 - 0.40e2 / 0.9e1 * t29 * t60 + 0.11e2 / 0.9e1 * t31 / t19 / t103) * t38, 0)
  t115 = t53 * t87
  t133 = f.my_piecewise3(t2, 0, t6 * t17 * t26 * t47 / 0.64e2 - 0.3e1 / 0.128e3 * t6 * t21 * t71 - 0.9e1 / 0.512e3 * t52 * (t47 - 0.1e1 / t46 * t53) * t87 * t89 * t91 * t94 - 0.9e1 / 0.256e3 * t52 * t53 * t110 * t70 - 0.9e1 / 0.256e3 * t52 * t115 * t44 * t91 * t94 + 0.9e1 / 0.256e3 * t52 * t115 * t89 / t90 / t45 * t94 + 0.9e1 / 0.256e3 * t52 * t115 * t68 * t94)
  v2rho2_0_ = 0.2e1 * r0 * t133 + 0.4e1 * t75
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.6e1)
  t6 = t3 * t4 * jnp.pi
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
  t22 = t17 * t21
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = l0 * t24
  t28 = tau0 * t24
  t30 = s0 * t24
  t31 = r0 ** 2
  t33 = 0.1e1 / t19 / t31
  t37 = 0.1e1 / jnp.pi
  t38 = (t25 * t21 / 0.4e1 - t28 * t21 + t30 * t33 / 0.8e1) * t37
  t39 = -0.9999999999e0 < t38
  t40 = f.my_piecewise3(t39, t38, -0.9999999999e0)
  t41 = jnp.exp(-1)
  t43 = scipy.special.lambertw(t40 * t41)
  t44 = t43 + 0.1e1
  t45 = t44 / 0.2e1
  t46 = scipy.special.i0(t45)
  t52 = t6 * t17 / t19
  t53 = scipy.special.i1(t45)
  t60 = 0.1e1 / t19 / t31 / r0
  t65 = f.my_piecewise3(t39, (-0.5e1 / 0.12e2 * t25 * t33 + 0.5e1 / 0.3e1 * t28 * t33 - t30 * t60 / 0.3e1) * t37, 0)
  t67 = 0.1e1 / t44
  t68 = t43 * t67
  t70 = t68 / t40
  t71 = t53 * t65 * t70
  t74 = t17 * t18
  t75 = t6 * t74
  t76 = 0.1e1 / t45
  t78 = -t76 * t53 + t46
  t79 = t65 ** 2
  t81 = t43 ** 2
  t82 = t44 ** 2
  t83 = 0.1e1 / t82
  t84 = t81 * t83
  t85 = t40 ** 2
  t86 = 0.1e1 / t85
  t87 = t84 * t86
  t88 = t78 * t79 * t87
  t95 = t31 ** 2
  t97 = 0.1e1 / t19 / t95
  t102 = f.my_piecewise3(t39, (0.10e2 / 0.9e1 * t25 * t60 - 0.40e2 / 0.9e1 * t28 * t60 + 0.11e2 / 0.9e1 * t30 * t97) * t37, 0)
  t104 = t53 * t102 * t70
  t107 = t53 * t79
  t108 = t43 * t83
  t109 = t108 * t86
  t110 = t107 * t109
  t114 = 0.1e1 / t82 / t44
  t115 = t81 * t114
  t117 = t107 * t115 * t86
  t121 = t107 * t68 * t86
  t125 = f.my_piecewise3(t2, 0, t6 * t22 * t46 / 0.64e2 - 0.3e1 / 0.128e3 * t52 * t71 - 0.9e1 / 0.512e3 * t75 * t88 - 0.9e1 / 0.256e3 * t75 * t104 - 0.9e1 / 0.256e3 * t75 * t110 + 0.9e1 / 0.256e3 * t75 * t117 + 0.9e1 / 0.256e3 * t75 * t121)
  t127 = t79 * t65
  t128 = t53 * t127
  t130 = 0.1e1 / t85 / t40
  t131 = t115 * t130
  t147 = t78 * t127
  t153 = t6 * t74 * t53
  t173 = t45 ** 2
  t187 = -0.27e2 / 0.256e3 * t75 * t128 * t131 - 0.9e1 / 0.128e3 * t75 * t128 * t68 * t130 - 0.27e2 / 0.512e3 * t6 * t74 * t78 * t65 * t81 * t83 * t86 * t102 + 0.27e2 / 0.512e3 * t75 * t147 * t84 * t130 + 0.27e2 / 0.256e3 * t153 * t102 * t43 * t67 * t86 * t65 + 0.27e2 / 0.256e3 * t75 * t128 * t108 * t130 + 0.9e1 / 0.256e3 * t52 * t121 + 0.3e1 / 0.128e3 * t6 * t22 * t71 - 0.9e1 / 0.256e3 * t52 * t104 - 0.9e1 / 0.512e3 * t52 * t88 - 0.9e1 / 0.512e3 * t75 * (t71 / 0.2e1 + 0.1e1 / t173 * t53 * t65 * t70 / 0.2e1 - t76 * t78 * t65 * t70 / 0.2e1) * t79 * t87
  t199 = f.my_piecewise3(t39, (-0.110e3 / 0.27e2 * t25 * t97 + 0.440e3 / 0.27e2 * t28 * t97 - 0.154e3 / 0.27e2 * t30 / t19 / t95 / r0) * t37, 0)
  t220 = t81 * t43
  t221 = t82 ** 2
  t222 = 0.1e1 / t221
  t250 = -0.9e1 / 0.256e3 * t75 * t53 * t199 * t70 - 0.9e1 / 0.256e3 * t52 * t110 - 0.27e2 / 0.256e3 * t153 * t102 * t65 * t109 - 0.9e1 / 0.256e3 * t75 * t128 * t43 * t114 * t130 + 0.9e1 / 0.256e3 * t52 * t117 - 0.27e2 / 0.512e3 * t75 * t147 * t131 + 0.27e2 / 0.512e3 * t75 * t147 * t220 * t222 * t130 + 0.27e2 / 0.256e3 * t153 * t102 * t81 * t114 * t86 * t65 + 0.9e1 / 0.64e2 * t75 * t128 * t81 * t222 * t130 - 0.27e2 / 0.256e3 * t75 * t128 * t220 / t221 / t44 * t130 - 0.5e1 / 0.192e3 * t6 * t17 * t33 * t46
  t252 = f.my_piecewise3(t2, 0, t187 + t250)
  v3rho3_0_ = 0.2e1 * r0 * t252 + 0.6e1 * t125

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.6e1)
  t6 = t3 * t4 * jnp.pi
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t17 * t18
  t20 = t6 * t19
  t21 = 2 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = l0 * t22
  t24 = t18 ** 2
  t26 = 0.1e1 / t24 / r0
  t29 = tau0 * t22
  t31 = s0 * t22
  t32 = r0 ** 2
  t34 = 0.1e1 / t24 / t32
  t38 = 0.1e1 / jnp.pi
  t39 = (t23 * t26 / 0.4e1 - t29 * t26 + t31 * t34 / 0.8e1) * t38
  t40 = -0.9999999999e0 < t39
  t41 = f.my_piecewise3(t40, t39, -0.9999999999e0)
  t42 = jnp.exp(-1)
  t44 = scipy.special.lambertw(t41 * t42)
  t45 = t44 + 0.1e1
  t46 = t45 / 0.2e1
  t47 = scipy.special.i1(t46)
  t54 = 0.1e1 / t24 / t32 / r0
  t59 = f.my_piecewise3(t40, (-0.5e1 / 0.12e2 * t23 * t34 + 0.5e1 / 0.3e1 * t29 * t34 - t31 * t54 / 0.3e1) * t38, 0)
  t60 = t59 ** 2
  t61 = t60 * t59
  t62 = t47 * t61
  t63 = t44 ** 2
  t64 = t45 ** 2
  t65 = t64 * t45
  t66 = 0.1e1 / t65
  t67 = t63 * t66
  t68 = t41 ** 2
  t70 = 0.1e1 / t68 / t41
  t71 = t67 * t70
  t72 = t62 * t71
  t75 = 0.1e1 / t45
  t76 = t44 * t75
  t78 = t62 * t76 * t70
  t81 = scipy.special.i0(t46)
  t82 = 0.1e1 / t46
  t84 = -t82 * t47 + t81
  t86 = t6 * t19 * t84
  t87 = t59 * t63
  t88 = 0.1e1 / t64
  t89 = 0.1e1 / t68
  t90 = t88 * t89
  t95 = t32 ** 2
  t97 = 0.1e1 / t24 / t95
  t102 = f.my_piecewise3(t40, (0.10e2 / 0.9e1 * t23 * t54 - 0.40e2 / 0.9e1 * t29 * t54 + 0.11e2 / 0.9e1 * t31 * t97) * t38, 0)
  t104 = t87 * t90 * t102
  t107 = t84 * t61
  t108 = t63 * t88
  t109 = t108 * t70
  t110 = t107 * t109
  t114 = t6 * t19 * t47
  t117 = t75 * t89 * t59
  t118 = t102 * t44 * t117
  t121 = t44 * t88
  t122 = t121 * t70
  t123 = t62 * t122
  t127 = t17 / t24
  t128 = t6 * t127
  t129 = t47 * t60
  t130 = t76 * t89
  t131 = t129 * t130
  t135 = t6 * t17 * t26
  t138 = t76 / t41
  t139 = t47 * t59 * t138
  t143 = t47 * t102 * t138
  t147 = t108 * t89
  t148 = t84 * t60 * t147
  t151 = t46 ** 2
  t152 = 0.1e1 / t151
  t153 = t152 * t47
  t156 = t82 * t84
  t160 = t153 * t59 * t138 / 0.2e1 - t156 * t59 * t138 / 0.2e1 + t139 / 0.2e1
  t162 = t160 * t60 * t147
  t165 = -0.27e2 / 0.256e3 * t20 * t72 - 0.9e1 / 0.128e3 * t20 * t78 - 0.27e2 / 0.512e3 * t86 * t104 + 0.27e2 / 0.512e3 * t20 * t110 + 0.27e2 / 0.256e3 * t114 * t118 + 0.27e2 / 0.256e3 * t20 * t123 + 0.9e1 / 0.256e3 * t128 * t131 + 0.3e1 / 0.128e3 * t135 * t139 - 0.9e1 / 0.256e3 * t128 * t143 - 0.9e1 / 0.512e3 * t128 * t148 - 0.9e1 / 0.512e3 * t20 * t162
  t172 = 0.1e1 / t24 / t95 / r0
  t177 = f.my_piecewise3(t40, (-0.110e3 / 0.27e2 * t23 * t97 + 0.440e3 / 0.27e2 * t29 * t97 - 0.154e3 / 0.27e2 * t31 * t172) * t38, 0)
  t179 = t47 * t177 * t138
  t182 = t121 * t89
  t183 = t129 * t182
  t187 = t102 * t59 * t182
  t190 = t44 * t66
  t191 = t190 * t70
  t192 = t62 * t191
  t195 = t67 * t89
  t196 = t129 * t195
  t199 = t107 * t71
  t202 = t63 * t44
  t203 = t64 ** 2
  t204 = 0.1e1 / t203
  t205 = t202 * t204
  t206 = t205 * t70
  t207 = t107 * t206
  t212 = t66 * t89 * t59
  t213 = t102 * t63 * t212
  t216 = t63 * t204
  t217 = t216 * t70
  t218 = t62 * t217
  t222 = 0.1e1 / t203 / t45
  t223 = t202 * t222
  t225 = t62 * t223 * t70
  t228 = t17 * t34
  t232 = -0.9e1 / 0.256e3 * t20 * t179 - 0.9e1 / 0.256e3 * t128 * t183 - 0.27e2 / 0.256e3 * t114 * t187 - 0.9e1 / 0.256e3 * t20 * t192 + 0.9e1 / 0.256e3 * t128 * t196 - 0.27e2 / 0.512e3 * t20 * t199 + 0.27e2 / 0.512e3 * t20 * t207 + 0.27e2 / 0.256e3 * t114 * t213 + 0.9e1 / 0.64e2 * t20 * t218 - 0.27e2 / 0.256e3 * t20 * t225 - 0.5e1 / 0.192e3 * t6 * t228 * t81
  t234 = f.my_piecewise3(t2, 0, t165 + t232)
  t240 = t60 * t63
  t243 = t240 * t66 * t70 * t102
  t252 = t102 * t60
  t272 = t6 * t127 * t47
  t299 = 0.5e1 / 0.72e2 * t6 * t17 * t54 * t81 - 0.81e2 / 0.256e3 * t86 * t243 + 0.81e2 / 0.256e3 * t86 * t60 * t202 * t204 * t70 * t102 + 0.27e2 / 0.32e2 * t114 * t252 * t217 - 0.81e2 / 0.128e3 * t114 * t102 * t202 * t222 * t70 * t60 - 0.9e1 / 0.128e3 * t6 * t127 * t84 * t104 + 0.81e2 / 0.256e3 * t86 * t240 * t88 * t70 * t102 + 0.9e1 / 0.64e2 * t272 * t118 - 0.9e1 / 0.64e2 * t272 * t187 - 0.9e1 / 0.64e2 * t114 * t177 * t59 * t182 + 0.9e1 / 0.64e2 * t114 * t177 * t63 * t212 - 0.27e2 / 0.128e3 * t114 * t252 * t191 + 0.81e2 / 0.128e3 * t114 * t252 * t122 + 0.9e1 / 0.64e2 * t272 * t213 - 0.27e2 / 0.64e2 * t114 * t60 * t44 * t75 * t70 * t102
  t314 = t60 ** 2
  t315 = t47 * t314
  t316 = t68 ** 2
  t317 = 0.1e1 / t316
  t333 = t160 * t61
  t353 = -0.45e2 / 0.512e3 * t6 * t19 * t160 * t104 - 0.9e1 / 0.128e3 * t86 * t87 * t90 * t177 + 0.9e1 / 0.64e2 * t114 * t177 * t44 * t117 - 0.81e2 / 0.128e3 * t114 * t243 - 0.99e2 / 0.256e3 * t20 * t315 * t121 * t317 + 0.27e2 / 0.128e3 * t20 * t315 * t190 * t317 - 0.9e1 / 0.256e3 * t20 * t315 * t44 * t204 * t317 + 0.9e1 / 0.128e3 * t128 * t207 - 0.45e2 / 0.512e3 * t20 * t333 * t71 + 0.45e2 / 0.512e3 * t20 * t333 * t206 + 0.3e1 / 0.16e2 * t128 * t218 + 0.99e2 / 0.256e3 * t20 * t315 * t63 * t222 * t317 - 0.9e1 / 0.64e2 * t128 * t225 - 0.3e1 / 0.64e2 * t135 * t196 - 0.9e1 / 0.128e3 * t128 * t199
  t355 = t102 ** 2
  t356 = t47 * t355
  t389 = t67 * t317
  t406 = f.my_piecewise3(t40, (0.1540e4 / 0.81e2 * t23 * t172 - 0.6160e4 / 0.81e2 * t29 * t172 + 0.2618e4 / 0.81e2 * t31 / t24 / t95 / t32) * t38, 0)
  t411 = 0.27e2 / 0.256e3 * t20 * t356 * t195 - 0.27e2 / 0.256e3 * t20 * t356 * t182 + 0.9e1 / 0.64e2 * t128 * t123 - 0.3e1 / 0.64e2 * t135 * t131 - 0.5e1 / 0.96e2 * t6 * t228 * t139 + 0.27e2 / 0.128e3 * t20 * t315 * t76 * t317 - 0.27e2 / 0.512e3 * t20 * t84 * t355 * t147 + 0.9e1 / 0.128e3 * t128 * t110 + 0.27e2 / 0.256e3 * t20 * t356 * t130 - 0.9e1 / 0.64e2 * t128 * t72 + 0.3e1 / 0.64e2 * t135 * t183 - 0.3e1 / 0.64e2 * t128 * t192 + 0.99e2 / 0.256e3 * t20 * t315 * t389 - 0.3e1 / 0.32e2 * t128 * t78 - 0.9e1 / 0.256e3 * t20 * t47 * t406 * t138
  t412 = t84 * t314
  t413 = t216 * t317
  t443 = t153 * t60
  t457 = t156 * t60
  t464 = t148 / 0.4e1 + t143 / 0.2e1 + t183 / 0.2e1 - t196 / 0.2e1 - t131 / 0.2e1 - 0.1e1 / t151 / t46 * t47 * t60 * t147 / 0.2e1 + t152 * t84 * t60 * t147 / 0.2e1 + t153 * t102 * t138 / 0.2e1 + t443 * t182 / 0.2e1 - t443 * t195 / 0.2e1 - t443 * t130 / 0.2e1 - t82 * t160 * t59 * t138 / 0.2e1 - t156 * t102 * t138 / 0.2e1 - t457 * t182 / 0.2e1 + t457 * t195 / 0.2e1 + t457 * t130 / 0.2e1
  t480 = t223 * t317
  t484 = t63 ** 2
  t486 = 0.1e1 / t203 / t64
  t513 = -0.63e2 / 0.512e3 * t20 * t412 * t413 + 0.3e1 / 0.64e2 * t135 * t143 + 0.3e1 / 0.128e3 * t135 * t148 - 0.3e1 / 0.64e2 * t128 * t179 - 0.3e1 / 0.128e3 * t128 * t162 - 0.9e1 / 0.512e3 * t20 * t464 * t60 * t147 - 0.81e2 / 0.256e3 * t20 * t412 * t205 * t317 - 0.99e2 / 0.512e3 * t20 * t412 * t108 * t317 + 0.45e2 / 0.512e3 * t20 * t333 * t109 + 0.99e2 / 0.256e3 * t20 * t412 * t480 - 0.135e3 / 0.512e3 * t20 * t412 * t484 * t486 * t317 - 0.225e3 / 0.256e3 * t20 * t315 * t202 * t486 * t317 + 0.135e3 / 0.256e3 * t20 * t315 * t484 / t203 / t65 * t317 - 0.27e2 / 0.32e2 * t20 * t315 * t413 + 0.81e2 / 0.128e3 * t20 * t315 * t480 + 0.81e2 / 0.256e3 * t20 * t412 * t389
  t516 = f.my_piecewise3(t2, 0, t299 + t353 + t411 + t513)
  v4rho4_0_ = 0.2e1 * r0 * t516 + 0.8e1 * t234

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.6e1)
  t5 = t2 * t3 * jnp.pi
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
  t32 = r0 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t35 = 0.1e1 / t33 / r0
  t39 = r0 ** 2
  t41 = 0.1e1 / t33 / t39
  t45 = 0.1e1 / jnp.pi
  t46 = (l0 * t35 / 0.4e1 - tau0 * t35 + s0 * t41 / 0.8e1) * t45
  t47 = -0.9999999999e0 < t46
  t48 = f.my_piecewise3(t47, t46, -0.9999999999e0)
  t49 = jnp.exp(-1)
  t51 = lambertw(t48 * t49)
  t52 = t51 + 0.1e1
  t53 = t52 / 0.2e1
  t54 = jax.scipy.special.i0(t53)
  t58 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t59 = t58 * f.p.zeta_threshold
  t61 = f.my_piecewise3(t20, t59, t21 * t19)
  t62 = t30 ** 2
  t63 = 0.1e1 / t62
  t64 = t61 * t63
  t67 = 0.3e1 / 0.128e3 * t5 * t64 * t54
  t69 = t5 * t61 * t30
  t70 = scipy.special.i1(t53)
  t77 = 0.1e1 / t33 / t39 / r0
  t82 = f.my_piecewise3(t47, (-0.5e1 / 0.12e2 * l0 * t41 + 0.5e1 / 0.3e1 * tau0 * t41 - s0 * t77 / 0.3e1) * t45, 0)
  t85 = t51 / t52
  t87 = t85 / t48
  t88 = t70 * t82 * t87
  t92 = f.my_piecewise3(t1, 0, -0.9e1 / 0.128e3 * t5 * t31 * t54 - t67 - 0.9e1 / 0.256e3 * t69 * t88)
  t94 = r1 <= f.p.dens_threshold
  t95 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t96 = 0.1e1 + t95
  t97 = t96 <= f.p.zeta_threshold
  t98 = t96 ** (0.1e1 / 0.3e1)
  t100 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t103 = f.my_piecewise3(t97, 0, 0.4e1 / 0.3e1 * t98 * t100)
  t104 = t103 * t30
  t105 = r1 ** (0.1e1 / 0.3e1)
  t106 = t105 ** 2
  t108 = 0.1e1 / t106 / r1
  t112 = r1 ** 2
  t114 = 0.1e1 / t106 / t112
  t118 = (l1 * t108 / 0.4e1 - tau1 * t108 + s2 * t114 / 0.8e1) * t45
  t119 = -0.9999999999e0 < t118
  t120 = f.my_piecewise3(t119, t118, -0.9999999999e0)
  t122 = lambertw(t120 * t49)
  t123 = t122 + 0.1e1
  t124 = t123 / 0.2e1
  t125 = jax.scipy.special.i0(t124)
  t130 = f.my_piecewise3(t97, t59, t98 * t96)
  t131 = t130 * t63
  t134 = 0.3e1 / 0.128e3 * t5 * t131 * t125
  t136 = f.my_piecewise3(t94, 0, -0.9e1 / 0.128e3 * t5 * t104 * t125 - t134)
  t138 = t21 ** 2
  t139 = 0.1e1 / t138
  t140 = t26 ** 2
  t145 = t16 / t22 / t6
  t147 = -0.2e1 * t23 + 0.2e1 * t145
  t148 = f.my_piecewise5(t10, 0, t14, 0, t147)
  t152 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t139 * t140 + 0.4e1 / 0.3e1 * t21 * t148)
  t159 = t5 * t29 * t63 * t54
  t165 = 0.1e1 / t62 / t6
  t169 = t5 * t61 * t165 * t54 / 0.64e2
  t171 = t5 * t64 * t88
  t176 = t82 ** 2
  t178 = t51 ** 2
  t179 = t52 ** 2
  t180 = 0.1e1 / t179
  t182 = t48 ** 2
  t183 = 0.1e1 / t182
  t192 = t39 ** 2
  t199 = f.my_piecewise3(t47, (0.10e2 / 0.9e1 * l0 * t77 - 0.40e2 / 0.9e1 * tau0 * t77 + 0.11e2 / 0.9e1 * s0 / t33 / t192) * t45, 0)
  t204 = t70 * t176
  t222 = f.my_piecewise3(t1, 0, -0.9e1 / 0.128e3 * t5 * t152 * t30 * t54 - 0.3e1 / 0.64e2 * t159 - 0.9e1 / 0.128e3 * t5 * t31 * t88 + t169 - 0.3e1 / 0.128e3 * t171 - 0.9e1 / 0.512e3 * t69 * (t54 - 0.1e1 / t53 * t70) * t176 * t178 * t180 * t183 - 0.9e1 / 0.256e3 * t69 * t70 * t199 * t87 - 0.9e1 / 0.256e3 * t69 * t204 * t51 * t180 * t183 + 0.9e1 / 0.256e3 * t69 * t204 * t178 / t179 / t52 * t183 + 0.9e1 / 0.256e3 * t69 * t204 * t85 * t183)
  t223 = t98 ** 2
  t224 = 0.1e1 / t223
  t225 = t100 ** 2
  t229 = f.my_piecewise5(t14, 0, t10, 0, -t147)
  t233 = f.my_piecewise3(t97, 0, 0.4e1 / 0.9e1 * t224 * t225 + 0.4e1 / 0.3e1 * t98 * t229)
  t240 = t5 * t103 * t63 * t125
  t245 = t5 * t130 * t165 * t125 / 0.64e2
  t247 = f.my_piecewise3(t94, 0, -0.9e1 / 0.128e3 * t5 * t233 * t30 * t125 - 0.3e1 / 0.64e2 * t240 + t245)
  d11 = 0.2e1 * t92 + 0.2e1 * t136 + t6 * (t222 + t247)
  t250 = -t7 - t24
  t251 = f.my_piecewise5(t10, 0, t14, 0, t250)
  t254 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t251)
  t255 = t254 * t30
  t260 = f.my_piecewise3(t1, 0, -0.9e1 / 0.128e3 * t5 * t255 * t54 - t67)
  t262 = f.my_piecewise5(t14, 0, t10, 0, -t250)
  t265 = f.my_piecewise3(t97, 0, 0.4e1 / 0.3e1 * t98 * t262)
  t266 = t265 * t30
  t271 = t5 * t130 * t30
  t272 = scipy.special.i1(t124)
  t279 = 0.1e1 / t106 / t112 / r1
  t284 = f.my_piecewise3(t119, (-0.5e1 / 0.12e2 * l1 * t114 + 0.5e1 / 0.3e1 * tau1 * t114 - s2 * t279 / 0.3e1) * t45, 0)
  t287 = t122 / t123
  t289 = t287 / t120
  t290 = t272 * t284 * t289
  t294 = f.my_piecewise3(t94, 0, -0.9e1 / 0.128e3 * t5 * t266 * t125 - t134 - 0.9e1 / 0.256e3 * t271 * t290)
  t298 = 0.2e1 * t145
  t299 = f.my_piecewise5(t10, 0, t14, 0, t298)
  t303 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t139 * t251 * t26 + 0.4e1 / 0.3e1 * t21 * t299)
  t310 = t5 * t254 * t63 * t54
  t318 = f.my_piecewise3(t1, 0, -0.9e1 / 0.128e3 * t5 * t303 * t30 * t54 - 0.3e1 / 0.128e3 * t310 - 0.9e1 / 0.256e3 * t5 * t255 * t88 - 0.3e1 / 0.128e3 * t159 + t169 - 0.3e1 / 0.256e3 * t171)
  t322 = f.my_piecewise5(t14, 0, t10, 0, -t298)
  t326 = f.my_piecewise3(t97, 0, 0.4e1 / 0.9e1 * t224 * t262 * t100 + 0.4e1 / 0.3e1 * t98 * t322)
  t333 = t5 * t265 * t63 * t125
  t340 = t5 * t131 * t290
  t343 = f.my_piecewise3(t94, 0, -0.9e1 / 0.128e3 * t5 * t326 * t30 * t125 - 0.3e1 / 0.128e3 * t333 - 0.3e1 / 0.128e3 * t240 + t245 - 0.9e1 / 0.256e3 * t5 * t104 * t290 - 0.3e1 / 0.256e3 * t340)
  d12 = t92 + t136 + t260 + t294 + t6 * (t318 + t343)
  t348 = t251 ** 2
  t352 = 0.2e1 * t23 + 0.2e1 * t145
  t353 = f.my_piecewise5(t10, 0, t14, 0, t352)
  t357 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t139 * t348 + 0.4e1 / 0.3e1 * t21 * t353)
  t364 = f.my_piecewise3(t1, 0, -0.9e1 / 0.128e3 * t5 * t357 * t30 * t54 - 0.3e1 / 0.64e2 * t310 + t169)
  t365 = t262 ** 2
  t369 = f.my_piecewise5(t14, 0, t10, 0, -t352)
  t373 = f.my_piecewise3(t97, 0, 0.4e1 / 0.9e1 * t224 * t365 + 0.4e1 / 0.3e1 * t98 * t369)
  t386 = t284 ** 2
  t388 = t122 ** 2
  t389 = t123 ** 2
  t390 = 0.1e1 / t389
  t392 = t120 ** 2
  t393 = 0.1e1 / t392
  t402 = t112 ** 2
  t409 = f.my_piecewise3(t119, (0.10e2 / 0.9e1 * l1 * t279 - 0.40e2 / 0.9e1 * tau1 * t279 + 0.11e2 / 0.9e1 * s2 / t106 / t402) * t45, 0)
  t414 = t272 * t386
  t432 = f.my_piecewise3(t94, 0, -0.9e1 / 0.128e3 * t5 * t373 * t30 * t125 - 0.3e1 / 0.64e2 * t333 - 0.9e1 / 0.128e3 * t5 * t266 * t290 + t245 - 0.3e1 / 0.128e3 * t340 - 0.9e1 / 0.512e3 * t271 * (t125 - 0.1e1 / t124 * t272) * t386 * t388 * t390 * t393 - 0.9e1 / 0.256e3 * t271 * t272 * t409 * t289 - 0.9e1 / 0.256e3 * t271 * t414 * t122 * t390 * t393 + 0.9e1 / 0.256e3 * t271 * t414 * t388 / t389 / t123 * t393 + 0.9e1 / 0.256e3 * t271 * t414 * t287 * t393)
  d22 = 0.2e1 * t260 + 0.2e1 * t294 + t6 * (t364 + t432)
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
  t3 = jnp.pi ** (0.1e1 / 0.6e1)
  t5 = t2 * t3 * jnp.pi
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
  t44 = r0 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t47 = 0.1e1 / t45 / r0
  t51 = r0 ** 2
  t53 = 0.1e1 / t45 / t51
  t57 = 0.1e1 / jnp.pi
  t58 = (l0 * t47 / 0.4e1 - tau0 * t47 + s0 * t53 / 0.8e1) * t57
  t59 = -0.9999999999e0 < t58
  t60 = f.my_piecewise3(t59, t58, -0.9999999999e0)
  t61 = jnp.exp(-1)
  t63 = scipy.special.lambertw(t60 * t61)
  t64 = t63 + 0.1e1
  t65 = t64 / 0.2e1
  t66 = scipy.special.i0(t65)
  t72 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t73 = t42 ** 2
  t74 = 0.1e1 / t73
  t75 = t72 * t74
  t80 = t5 * t72 * t42
  t81 = scipy.special.i1(t65)
  t88 = 0.1e1 / t45 / t51 / r0
  t93 = f.my_piecewise3(t59, (-0.5e1 / 0.12e2 * l0 * t53 + 0.5e1 / 0.3e1 * tau0 * t53 - s0 * t88 / 0.3e1) * t57, 0)
  t95 = 0.1e1 / t64
  t96 = t63 * t95
  t98 = t96 / t60
  t99 = t81 * t93 * t98
  t102 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t103 = t102 * f.p.zeta_threshold
  t105 = f.my_piecewise3(t20, t103, t21 * t19)
  t107 = 0.1e1 / t73 / t6
  t108 = t105 * t107
  t113 = t5 * t105 * t74
  t116 = t105 * t42
  t117 = t5 * t116
  t118 = 0.1e1 / t65
  t120 = -t118 * t81 + t66
  t121 = t93 ** 2
  t123 = t63 ** 2
  t124 = t64 ** 2
  t125 = 0.1e1 / t124
  t126 = t123 * t125
  t127 = t60 ** 2
  t128 = 0.1e1 / t127
  t129 = t126 * t128
  t130 = t120 * t121 * t129
  t137 = t51 ** 2
  t139 = 0.1e1 / t45 / t137
  t144 = f.my_piecewise3(t59, (0.10e2 / 0.9e1 * l0 * t88 - 0.40e2 / 0.9e1 * tau0 * t88 + 0.11e2 / 0.9e1 * s0 * t139) * t57, 0)
  t146 = t81 * t144 * t98
  t149 = t81 * t121
  t150 = t63 * t125
  t151 = t150 * t128
  t152 = t149 * t151
  t156 = 0.1e1 / t124 / t64
  t157 = t123 * t156
  t159 = t149 * t157 * t128
  t163 = t149 * t96 * t128
  t167 = f.my_piecewise3(t1, 0, -0.9e1 / 0.128e3 * t5 * t43 * t66 - 0.3e1 / 0.64e2 * t5 * t75 * t66 - 0.9e1 / 0.128e3 * t80 * t99 + t5 * t108 * t66 / 0.64e2 - 0.3e1 / 0.128e3 * t113 * t99 - 0.9e1 / 0.512e3 * t117 * t130 - 0.9e1 / 0.256e3 * t117 * t146 - 0.9e1 / 0.256e3 * t117 * t152 + 0.9e1 / 0.256e3 * t117 * t159 + 0.9e1 / 0.256e3 * t117 * t163)
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
  t188 = r1 ** (0.1e1 / 0.3e1)
  t189 = t188 ** 2
  t191 = 0.1e1 / t189 / r1
  t195 = r1 ** 2
  t201 = (l1 * t191 / 0.4e1 - tau1 * t191 + s2 / t189 / t195 / 0.8e1) * t57
  t203 = f.my_piecewise3(-0.9999999999e0 < t201, t201, -0.9999999999e0)
  t205 = scipy.special.lambertw(t203 * t61)
  t208 = scipy.special.i0(t205 / 0.2e1 + 0.1e1 / 0.2e1)
  t214 = f.my_piecewise3(t172, 0, 0.4e1 / 0.3e1 * t173 * t177)
  t220 = f.my_piecewise3(t172, t103, t173 * t171)
  t226 = f.my_piecewise3(t169, 0, -0.9e1 / 0.128e3 * t5 * t186 * t42 * t208 - 0.3e1 / 0.64e2 * t5 * t214 * t74 * t208 + t5 * t220 * t107 * t208 / 0.64e2)
  t236 = t24 ** 2
  t240 = 0.6e1 * t33 - 0.6e1 * t16 / t236
  t241 = f.my_piecewise5(t10, 0, t14, 0, t240)
  t245 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t241)
  t259 = 0.1e1 / t73 / t24
  t265 = t5 * t116 * t81
  t294 = t121 * t93
  t295 = t120 * t294
  t297 = 0.1e1 / t127 / t60
  t298 = t157 * t297
  t302 = t123 * t63
  t303 = t124 ** 2
  t304 = 0.1e1 / t303
  t310 = t81 * t294
  t330 = -0.9e1 / 0.128e3 * t5 * t245 * t42 * t66 - 0.9e1 / 0.128e3 * t5 * t41 * t74 * t66 + 0.3e1 / 0.64e2 * t5 * t72 * t107 * t66 - 0.5e1 / 0.192e3 * t5 * t105 * t259 * t66 - 0.27e2 / 0.256e3 * t265 * t144 * t93 * t151 + 0.27e2 / 0.256e3 * t265 * t144 * t123 * t156 * t128 * t93 + 0.27e2 / 0.256e3 * t265 * t144 * t63 * t95 * t128 * t93 - 0.27e2 / 0.512e3 * t5 * t116 * t120 * t93 * t123 * t125 * t128 * t144 + 0.27e2 / 0.256e3 * t80 * t159 + 0.9e1 / 0.256e3 * t113 * t159 - 0.27e2 / 0.512e3 * t117 * t295 * t298 + 0.27e2 / 0.512e3 * t117 * t295 * t302 * t304 * t297 + 0.9e1 / 0.64e2 * t117 * t310 * t123 * t304 * t297 - 0.27e2 / 0.256e3 * t117 * t310 * t302 / t303 / t64 * t297 + 0.27e2 / 0.256e3 * t117 * t310 * t150 * t297 - 0.27e2 / 0.256e3 * t117 * t310 * t298
  t369 = t65 ** 2
  t394 = f.my_piecewise3(t59, (-0.110e3 / 0.27e2 * l0 * t139 + 0.440e3 / 0.27e2 * tau0 * t139 - 0.154e3 / 0.27e2 * s0 / t45 / t137 / r0) * t57, 0)
  t399 = -0.9e1 / 0.128e3 * t117 * t310 * t96 * t297 + 0.27e2 / 0.256e3 * t80 * t163 + 0.9e1 / 0.256e3 * t113 * t163 + 0.27e2 / 0.512e3 * t117 * t295 * t126 * t297 - 0.27e2 / 0.256e3 * t80 * t152 - 0.9e1 / 0.256e3 * t113 * t152 - 0.9e1 / 0.256e3 * t117 * t310 * t63 * t156 * t297 - 0.27e2 / 0.256e3 * t5 * t43 * t99 - 0.9e1 / 0.128e3 * t5 * t75 * t99 - 0.27e2 / 0.256e3 * t80 * t146 - 0.27e2 / 0.512e3 * t80 * t130 + 0.3e1 / 0.128e3 * t5 * t108 * t99 - 0.9e1 / 0.256e3 * t113 * t146 - 0.9e1 / 0.512e3 * t113 * t130 - 0.9e1 / 0.512e3 * t117 * (t99 / 0.2e1 + 0.1e1 / t369 * t81 * t93 * t98 / 0.2e1 - t118 * t120 * t93 * t98 / 0.2e1) * t121 * t129 - 0.9e1 / 0.256e3 * t117 * t81 * t394 * t98
  t401 = f.my_piecewise3(t1, 0, t330 + t399)
  t411 = f.my_piecewise5(t14, 0, t10, 0, -t240)
  t415 = f.my_piecewise3(t172, 0, -0.8e1 / 0.27e2 / t174 / t171 * t178 * t177 + 0.4e1 / 0.3e1 * t175 * t177 * t182 + 0.4e1 / 0.3e1 * t173 * t411)
  t433 = f.my_piecewise3(t169, 0, -0.9e1 / 0.128e3 * t5 * t415 * t42 * t208 - 0.9e1 / 0.128e3 * t5 * t186 * t74 * t208 + 0.3e1 / 0.64e2 * t5 * t214 * t107 * t208 - 0.5e1 / 0.192e3 * t5 * t220 * t259 * t208)
  d111 = 0.3e1 * t167 + 0.3e1 * t226 + t6 * (t401 + t433)

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
  t3 = jnp.pi ** (0.1e1 / 0.6e1)
  t5 = t2 * t3 * jnp.pi
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
  t28 = r0 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t31 = 0.1e1 / t29 / r0
  t35 = r0 ** 2
  t37 = 0.1e1 / t29 / t35
  t41 = 0.1e1 / jnp.pi
  t42 = (l0 * t31 / 0.4e1 - tau0 * t31 + s0 * t37 / 0.8e1) * t41
  t43 = -0.9999999999e0 < t42
  t44 = f.my_piecewise3(t43, t42, -0.9999999999e0)
  t45 = jnp.exp(-1)
  t47 = scipy.special.lambertw(t44 * t45)
  t48 = 0.1e1 + t47
  t49 = t48 / 0.2e1
  t50 = scipy.special.i0(t49)
  t51 = 0.1e1 / t49
  t52 = scipy.special.i1(t49)
  t54 = -t51 * t52 + t50
  t56 = t5 * t27 * t54
  t63 = 0.1e1 / t29 / t35 / r0
  t68 = f.my_piecewise3(t43, (-0.5e1 / 0.12e2 * l0 * t37 + 0.5e1 / 0.3e1 * tau0 * t37 - s0 * t63 / 0.3e1) * t41, 0)
  t69 = t47 ** 2
  t70 = t68 * t69
  t71 = t48 ** 2
  t72 = 0.1e1 / t71
  t73 = t44 ** 2
  t74 = 0.1e1 / t73
  t75 = t72 * t74
  t80 = t35 ** 2
  t82 = 0.1e1 / t29 / t80
  t87 = f.my_piecewise3(t43, (0.10e2 / 0.9e1 * l0 * t63 - 0.40e2 / 0.9e1 * tau0 * t63 + 0.11e2 / 0.9e1 * s0 * t82) * t41, 0)
  t89 = t70 * t75 * t87
  t93 = t5 * t27 * t52
  t95 = t47 * t72
  t96 = t95 * t74
  t97 = t87 * t68 * t96
  t100 = t87 * t69
  t101 = t71 * t48
  t102 = 0.1e1 / t101
  t104 = t102 * t74 * t68
  t105 = t100 * t104
  t108 = t87 * t47
  t109 = 0.1e1 / t48
  t111 = t109 * t74 * t68
  t112 = t108 * t111
  t115 = t23 ** 2
  t117 = 0.1e1 / t115 / t19
  t118 = t6 ** 2
  t119 = 0.1e1 / t118
  t121 = -t16 * t119 + t7
  t122 = f.my_piecewise5(t10, 0, t14, 0, t121)
  t123 = t122 ** 2
  t127 = 0.1e1 / t115
  t128 = t127 * t122
  t129 = t118 * t6
  t130 = 0.1e1 / t129
  t133 = 0.2e1 * t16 * t130 - 0.2e1 * t119
  t134 = f.my_piecewise5(t10, 0, t14, 0, t133)
  t137 = t118 ** 2
  t138 = 0.1e1 / t137
  t141 = -0.6e1 * t16 * t138 + 0.6e1 * t130
  t142 = f.my_piecewise5(t10, 0, t14, 0, t141)
  t146 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t117 * t123 * t122 + 0.4e1 / 0.3e1 * t128 * t134 + 0.4e1 / 0.3e1 * t23 * t142)
  t147 = t146 * t26
  t156 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t127 * t123 + 0.4e1 / 0.3e1 * t23 * t134)
  t157 = t26 ** 2
  t158 = 0.1e1 / t157
  t159 = t156 * t158
  t165 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t122)
  t167 = 0.1e1 / t157 / t6
  t168 = t165 * t167
  t173 = 0.1e1 / t157 / t118
  t174 = t25 * t173
  t178 = t5 * t27
  t179 = t68 ** 2
  t180 = t179 * t68
  t181 = t54 * t180
  t182 = t69 * t102
  t184 = 0.1e1 / t73 / t44
  t185 = t182 * t184
  t186 = t181 * t185
  t189 = t69 * t47
  t190 = t71 ** 2
  t191 = 0.1e1 / t190
  t192 = t189 * t191
  t193 = t192 * t184
  t194 = t181 * t193
  t197 = t52 * t180
  t198 = t69 * t191
  t200 = t197 * t198 * t184
  t204 = 0.1e1 / t190 / t48
  t205 = t189 * t204
  t207 = t197 * t205 * t184
  t210 = t95 * t184
  t211 = t197 * t210
  t214 = t197 * t185
  t217 = t47 * t109
  t219 = t197 * t217 * t184
  t222 = t165 * t26
  t223 = t5 * t222
  t224 = t52 * t179
  t225 = t217 * t74
  t226 = t224 * t225
  t229 = -0.27e2 / 0.512e3 * t56 * t89 - 0.27e2 / 0.256e3 * t93 * t97 + 0.27e2 / 0.256e3 * t93 * t105 + 0.27e2 / 0.256e3 * t93 * t112 - 0.9e1 / 0.128e3 * t5 * t147 * t50 - 0.9e1 / 0.128e3 * t5 * t159 * t50 + 0.3e1 / 0.64e2 * t5 * t168 * t50 - 0.5e1 / 0.192e3 * t5 * t174 * t50 - 0.27e2 / 0.512e3 * t178 * t186 + 0.27e2 / 0.512e3 * t178 * t194 + 0.9e1 / 0.64e2 * t178 * t200 - 0.27e2 / 0.256e3 * t178 * t207 + 0.27e2 / 0.256e3 * t178 * t211 - 0.27e2 / 0.256e3 * t178 * t214 - 0.9e1 / 0.128e3 * t178 * t219 + 0.27e2 / 0.256e3 * t223 * t226
  t230 = t25 * t158
  t231 = t5 * t230
  t234 = t69 * t72
  t235 = t234 * t184
  t236 = t181 * t235
  t239 = t224 * t96
  t244 = t47 * t102
  t245 = t244 * t184
  t246 = t197 * t245
  t250 = t5 * t156 * t26
  t253 = t217 / t44
  t254 = t52 * t68 * t253
  t258 = t5 * t165 * t158
  t262 = t52 * t87 * t253
  t266 = t234 * t74
  t267 = t54 * t179 * t266
  t271 = t5 * t25 * t167
  t278 = t49 ** 2
  t279 = 0.1e1 / t278
  t280 = t279 * t52
  t283 = t51 * t54
  t287 = t280 * t68 * t253 / 0.2e1 - t283 * t68 * t253 / 0.2e1 + t254 / 0.2e1
  t289 = t287 * t179 * t266
  t298 = 0.1e1 / t29 / t80 / r0
  t303 = f.my_piecewise3(t43, (-0.110e3 / 0.27e2 * l0 * t82 + 0.440e3 / 0.27e2 * tau0 * t82 - 0.154e3 / 0.27e2 * s0 * t298) * t41, 0)
  t305 = t52 * t303 * t253
  t308 = t182 * t74
  t309 = t224 * t308
  t314 = 0.9e1 / 0.256e3 * t231 * t226 + 0.27e2 / 0.512e3 * t178 * t236 - 0.27e2 / 0.256e3 * t223 * t239 - 0.9e1 / 0.256e3 * t231 * t239 - 0.9e1 / 0.256e3 * t178 * t246 - 0.27e2 / 0.256e3 * t250 * t254 - 0.9e1 / 0.128e3 * t258 * t254 - 0.27e2 / 0.256e3 * t223 * t262 - 0.27e2 / 0.512e3 * t223 * t267 + 0.3e1 / 0.128e3 * t271 * t254 - 0.9e1 / 0.256e3 * t231 * t262 - 0.9e1 / 0.512e3 * t231 * t267 - 0.9e1 / 0.512e3 * t178 * t289 - 0.9e1 / 0.256e3 * t178 * t305 + 0.27e2 / 0.256e3 * t223 * t309 + 0.9e1 / 0.256e3 * t231 * t309
  t316 = f.my_piecewise3(t1, 0, t229 + t314)
  t318 = r1 <= f.p.dens_threshold
  t319 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t320 = 0.1e1 + t319
  t321 = t320 <= f.p.zeta_threshold
  t322 = t320 ** (0.1e1 / 0.3e1)
  t323 = t322 ** 2
  t325 = 0.1e1 / t323 / t320
  t327 = f.my_piecewise5(t14, 0, t10, 0, -t121)
  t328 = t327 ** 2
  t332 = 0.1e1 / t323
  t333 = t332 * t327
  t335 = f.my_piecewise5(t14, 0, t10, 0, -t133)
  t339 = f.my_piecewise5(t14, 0, t10, 0, -t141)
  t343 = f.my_piecewise3(t321, 0, -0.8e1 / 0.27e2 * t325 * t328 * t327 + 0.4e1 / 0.3e1 * t333 * t335 + 0.4e1 / 0.3e1 * t322 * t339)
  t345 = r1 ** (0.1e1 / 0.3e1)
  t346 = t345 ** 2
  t348 = 0.1e1 / t346 / r1
  t352 = r1 ** 2
  t358 = (l1 * t348 / 0.4e1 - tau1 * t348 + s2 / t346 / t352 / 0.8e1) * t41
  t360 = f.my_piecewise3(-0.9999999999e0 < t358, t358, -0.9999999999e0)
  t362 = scipy.special.lambertw(t360 * t45)
  t365 = scipy.special.i0(t362 / 0.2e1 + 0.1e1 / 0.2e1)
  t374 = f.my_piecewise3(t321, 0, 0.4e1 / 0.9e1 * t332 * t328 + 0.4e1 / 0.3e1 * t322 * t335)
  t381 = f.my_piecewise3(t321, 0, 0.4e1 / 0.3e1 * t322 * t327)
  t387 = f.my_piecewise3(t321, t22, t322 * t320)
  t393 = f.my_piecewise3(t318, 0, -0.9e1 / 0.128e3 * t5 * t343 * t26 * t365 - 0.9e1 / 0.128e3 * t5 * t374 * t158 * t365 + 0.3e1 / 0.64e2 * t5 * t381 * t167 * t365 - 0.5e1 / 0.192e3 * t5 * t387 * t173 * t365)
  t423 = t280 * t179
  t437 = t283 * t179
  t444 = t267 / 0.4e1 + t262 / 0.2e1 + t239 / 0.2e1 - t309 / 0.2e1 - t226 / 0.2e1 - 0.1e1 / t278 / t49 * t52 * t179 * t266 / 0.2e1 + t279 * t54 * t179 * t266 / 0.2e1 + t280 * t87 * t253 / 0.2e1 + t423 * t96 / 0.2e1 - t423 * t308 / 0.2e1 - t423 * t225 / 0.2e1 - t51 * t287 * t68 * t253 / 0.2e1 - t283 * t87 * t253 / 0.2e1 - t437 * t96 / 0.2e1 + t437 * t308 / 0.2e1 + t437 * t225 / 0.2e1
  t460 = f.my_piecewise3(t43, (0.1540e4 / 0.81e2 * l0 * t298 - 0.6160e4 / 0.81e2 * tau0 * t298 + 0.2618e4 / 0.81e2 * s0 / t29 / t80 / t35) * t41, 0)
  t465 = t87 * t179
  t477 = t191 * t184
  t482 = -0.9e1 / 0.128e3 * t223 * t289 + 0.3e1 / 0.64e2 * t271 * t262 + 0.3e1 / 0.128e3 * t271 * t267 - 0.3e1 / 0.64e2 * t231 * t305 - 0.3e1 / 0.128e3 * t231 * t289 - 0.9e1 / 0.512e3 * t178 * t444 * t179 * t266 - 0.9e1 / 0.256e3 * t178 * t52 * t460 * t253 + 0.81e2 / 0.128e3 * t93 * t465 * t210 - 0.27e2 / 0.128e3 * t93 * t465 * t245 + 0.9e1 / 0.64e2 * t93 * t303 * t69 * t104 + 0.81e2 / 0.256e3 * t56 * t179 * t189 * t477 * t87
  t484 = t5 * t222 * t52
  t491 = t179 * t69
  t529 = t491 * t102 * t184 * t87
  t532 = 0.27e2 / 0.64e2 * t484 * t112 + 0.9e1 / 0.64e2 * t93 * t303 * t47 * t111 + 0.81e2 / 0.256e3 * t56 * t491 * t72 * t184 * t87 - 0.27e2 / 0.128e3 * t5 * t222 * t54 * t89 - 0.45e2 / 0.512e3 * t5 * t27 * t287 * t89 - 0.9e1 / 0.128e3 * t56 * t70 * t75 * t303 - 0.27e2 / 0.64e2 * t484 * t97 - 0.9e1 / 0.64e2 * t93 * t303 * t68 * t96 + 0.27e2 / 0.64e2 * t484 * t105 + 0.27e2 / 0.32e2 * t93 * t100 * t477 * t179 - 0.81e2 / 0.128e3 * t93 * t87 * t189 * t204 * t184 * t179 - 0.81e2 / 0.256e3 * t56 * t529
  t535 = t5 * t230 * t52
  t553 = t19 ** 2
  t556 = t123 ** 2
  t562 = t134 ** 2
  t571 = -0.24e2 * t138 + 0.24e2 * t16 / t137 / t6
  t572 = f.my_piecewise5(t10, 0, t14, 0, t571)
  t576 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t115 / t553 * t556 - 0.16e2 / 0.9e1 * t117 * t123 * t134 + 0.4e1 / 0.3e1 * t127 * t562 + 0.16e2 / 0.9e1 * t128 * t142 + 0.4e1 / 0.3e1 * t23 * t572)
  t594 = 0.1e1 / t157 / t129
  t599 = 0.9e1 / 0.64e2 * t535 * t112 - 0.27e2 / 0.64e2 * t93 * t108 * t109 * t184 * t179 - 0.9e1 / 0.128e3 * t5 * t230 * t54 * t89 - 0.9e1 / 0.64e2 * t535 * t97 + 0.9e1 / 0.64e2 * t535 * t105 - 0.81e2 / 0.128e3 * t93 * t529 - 0.9e1 / 0.128e3 * t5 * t576 * t26 * t50 - 0.3e1 / 0.32e2 * t5 * t146 * t158 * t50 + 0.3e1 / 0.32e2 * t5 * t156 * t167 * t50 - 0.5e1 / 0.48e2 * t5 * t165 * t173 * t50 + 0.5e1 / 0.72e2 * t5 * t25 * t594 * t50
  t608 = t179 ** 2
  t609 = t54 * t608
  t610 = t73 ** 2
  t611 = 0.1e1 / t610
  t612 = t198 * t611
  t616 = t205 * t611
  t620 = t69 ** 2
  t622 = 0.1e1 / t190 / t71
  t628 = t52 * t608
  t650 = 0.9e1 / 0.16e2 * t223 * t200 - 0.27e2 / 0.64e2 * t223 * t207 + 0.3e1 / 0.16e2 * t231 * t200 - 0.9e1 / 0.64e2 * t231 * t207 - 0.63e2 / 0.512e3 * t178 * t609 * t612 + 0.99e2 / 0.256e3 * t178 * t609 * t616 - 0.135e3 / 0.512e3 * t178 * t609 * t620 * t622 * t611 + 0.99e2 / 0.256e3 * t178 * t628 * t69 * t204 * t611 - 0.225e3 / 0.256e3 * t178 * t628 * t189 * t622 * t611 + 0.135e3 / 0.256e3 * t178 * t628 * t620 / t190 / t101 * t611 + 0.3e1 / 0.64e2 * t271 * t239 + 0.9e1 / 0.64e2 * t258 * t226
  t663 = t182 * t611
  t686 = -0.3e1 / 0.64e2 * t271 * t226 - 0.9e1 / 0.64e2 * t258 * t239 + 0.9e1 / 0.64e2 * t231 * t211 - 0.99e2 / 0.256e3 * t178 * t628 * t95 * t611 + 0.99e2 / 0.256e3 * t178 * t628 * t663 - 0.3e1 / 0.32e2 * t231 * t219 + 0.27e2 / 0.128e3 * t178 * t628 * t217 * t611 + 0.81e2 / 0.256e3 * t178 * t609 * t663 - 0.81e2 / 0.256e3 * t178 * t609 * t192 * t611 - 0.27e2 / 0.32e2 * t178 * t628 * t612 + 0.81e2 / 0.128e3 * t178 * t628 * t616
  t697 = t87 ** 2
  t698 = t52 * t697
  t720 = 0.9e1 / 0.64e2 * t258 * t309 - 0.27e2 / 0.64e2 * t223 * t214 - 0.3e1 / 0.64e2 * t271 * t309 - 0.9e1 / 0.64e2 * t231 * t214 - 0.9e1 / 0.128e3 * t231 * t186 + 0.27e2 / 0.256e3 * t178 * t698 * t308 + 0.27e2 / 0.256e3 * t178 * t698 * t225 - 0.27e2 / 0.512e3 * t178 * t54 * t697 * t266 - 0.27e2 / 0.256e3 * t178 * t698 * t96 + 0.27e2 / 0.128e3 * t178 * t628 * t244 * t611 - 0.9e1 / 0.64e2 * t223 * t246 - 0.3e1 / 0.64e2 * t231 * t246
  t747 = t287 * t180
  t756 = -0.9e1 / 0.256e3 * t178 * t628 * t47 * t191 * t611 - 0.9e1 / 0.64e2 * t5 * t147 * t254 - 0.9e1 / 0.64e2 * t5 * t159 * t254 + 0.3e1 / 0.32e2 * t5 * t168 * t254 - 0.5e1 / 0.96e2 * t5 * t174 * t254 + 0.27e2 / 0.128e3 * t250 * t309 + 0.27e2 / 0.128e3 * t223 * t194 + 0.9e1 / 0.128e3 * t231 * t194 - 0.27e2 / 0.128e3 * t223 * t186 - 0.45e2 / 0.512e3 * t178 * t747 * t185 + 0.45e2 / 0.512e3 * t178 * t747 * t193 + 0.27e2 / 0.64e2 * t223 * t211
  t784 = -0.9e1 / 0.32e2 * t223 * t219 - 0.99e2 / 0.512e3 * t178 * t609 * t234 * t611 + 0.27e2 / 0.128e3 * t250 * t226 + 0.27e2 / 0.128e3 * t223 * t236 + 0.9e1 / 0.128e3 * t231 * t236 + 0.45e2 / 0.512e3 * t178 * t747 * t235 - 0.27e2 / 0.128e3 * t250 * t239 - 0.27e2 / 0.128e3 * t250 * t262 - 0.27e2 / 0.256e3 * t250 * t267 - 0.9e1 / 0.64e2 * t258 * t262 - 0.9e1 / 0.128e3 * t258 * t267 - 0.9e1 / 0.64e2 * t223 * t305
  t788 = f.my_piecewise3(t1, 0, t482 + t532 + t599 + t650 + t686 + t720 + t756 + t784)
  t789 = t320 ** 2
  t792 = t328 ** 2
  t798 = t335 ** 2
  t804 = f.my_piecewise5(t14, 0, t10, 0, -t571)
  t808 = f.my_piecewise3(t321, 0, 0.40e2 / 0.81e2 / t323 / t789 * t792 - 0.16e2 / 0.9e1 * t325 * t328 * t335 + 0.4e1 / 0.3e1 * t332 * t798 + 0.16e2 / 0.9e1 * t333 * t339 + 0.4e1 / 0.3e1 * t322 * t804)
  t830 = f.my_piecewise3(t318, 0, -0.9e1 / 0.128e3 * t5 * t808 * t26 * t365 - 0.3e1 / 0.32e2 * t5 * t343 * t158 * t365 + 0.3e1 / 0.32e2 * t5 * t374 * t167 * t365 - 0.5e1 / 0.48e2 * t5 * t381 * t173 * t365 + 0.5e1 / 0.72e2 * t5 * t387 * t594 * t365)
  d1111 = 0.4e1 * t316 + 0.4e1 * t393 + t6 * (t788 + t830)

  res = {'v4rho4': d1111}
  return res
