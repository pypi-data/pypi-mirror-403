"""Generated from mgga_k_gea2.mpl."""

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
  gea2_s = lambda x: X2S * x

  gea2_q = lambda u: X2S ** 2 * u

  gea2_f0 = lambda s, q: 1 + 5 / 27 * s ** 2 + 20 / 9 * q

  gea2_f = lambda x, u: gea2_f0(gea2_s(x), gea2_q(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, gea2_f, rs, z, xs0, xs1, u0, u1)

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
  gea2_s = lambda x: X2S * x

  gea2_q = lambda u: X2S ** 2 * u

  gea2_f0 = lambda s, q: 1 + 5 / 27 * s ** 2 + 20 / 9 * q

  gea2_f = lambda x, u: gea2_f0(gea2_s(x), gea2_q(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, gea2_f, rs, z, xs0, xs1, u0, u1)

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
  gea2_s = lambda x: X2S * x

  gea2_q = lambda u: X2S ** 2 * u

  gea2_f0 = lambda s, q: 1 + 5 / 27 * s ** 2 + 20 / 9 * q

  gea2_f = lambda x, u: gea2_f0(gea2_s(x), gea2_q(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, gea2_f, rs, z, xs0, xs1, u0, u1)

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
  t36 = 0.1e1 / t35
  t37 = t32 * t36
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t47 = 0.1e1 / t40 / r0
  t51 = 0.1e1 + 0.5e1 / 0.648e3 * t37 * s0 * t42 + 0.5e1 / 0.54e2 * t37 * l0 * t47
  t55 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t51)
  t56 = r1 <= f.p.dens_threshold
  t57 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t58 = 0.1e1 + t57
  t59 = t58 <= f.p.zeta_threshold
  t60 = t58 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t63 = f.my_piecewise3(t59, t24, t61 * t58)
  t64 = t63 * t30
  t65 = r1 ** 2
  t66 = r1 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t69 = 0.1e1 / t67 / t65
  t74 = 0.1e1 / t67 / r1
  t78 = 0.1e1 + 0.5e1 / 0.648e3 * t37 * s2 * t69 + 0.5e1 / 0.54e2 * t37 * l1 * t74
  t82 = f.my_piecewise3(t56, 0, 0.3e1 / 0.20e2 * t6 * t64 * t78)
  t83 = t7 ** 2
  t85 = t17 / t83
  t86 = t8 - t85
  t87 = f.my_piecewise5(t11, 0, t15, 0, t86)
  t90 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t87)
  t95 = 0.1e1 / t29
  t99 = t6 * t28 * t95 * t51 / 0.10e2
  t114 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t90 * t30 * t51 + t99 + 0.3e1 / 0.20e2 * t6 * t31 * (-0.5e1 / 0.243e3 * t37 * s0 / t40 / t38 / r0 - 0.25e2 / 0.162e3 * t37 * l0 * t42))
  t116 = f.my_piecewise5(t15, 0, t11, 0, -t86)
  t119 = f.my_piecewise3(t59, 0, 0.5e1 / 0.3e1 * t61 * t116)
  t127 = t6 * t63 * t95 * t78 / 0.10e2
  t129 = f.my_piecewise3(t56, 0, 0.3e1 / 0.20e2 * t6 * t119 * t30 * t78 + t127)
  vrho_0_ = t55 + t82 + t7 * (t114 + t129)
  t132 = -t8 - t85
  t133 = f.my_piecewise5(t11, 0, t15, 0, t132)
  t136 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t133)
  t142 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t136 * t30 * t51 + t99)
  t144 = f.my_piecewise5(t15, 0, t11, 0, -t132)
  t147 = f.my_piecewise3(t59, 0, 0.5e1 / 0.3e1 * t61 * t144)
  t166 = f.my_piecewise3(t56, 0, 0.3e1 / 0.20e2 * t6 * t147 * t30 * t78 + t127 + 0.3e1 / 0.20e2 * t6 * t64 * (-0.5e1 / 0.243e3 * t37 * s2 / t67 / t65 / r1 - 0.25e2 / 0.162e3 * t37 * l1 * t69))
  vrho_1_ = t55 + t82 + t7 * (t142 + t166)
  t169 = t6 * t28
  t170 = t30 * t32
  t175 = f.my_piecewise3(t1, 0, t169 * t170 * t36 * t42 / 0.864e3)
  vsigma_0_ = t7 * t175
  vsigma_1_ = 0.0e0
  t176 = t6 * t63
  t181 = f.my_piecewise3(t56, 0, t176 * t170 * t36 * t69 / 0.864e3)
  vsigma_2_ = t7 * t181
  t186 = f.my_piecewise3(t1, 0, t169 * t170 * t36 * t47 / 0.72e2)
  vlapl_0_ = t7 * t186
  t191 = f.my_piecewise3(t56, 0, t176 * t170 * t36 * t74 / 0.72e2)
  vlapl_1_ = t7 * t191
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
  gea2_s = lambda x: X2S * x

  gea2_q = lambda u: X2S ** 2 * u

  gea2_f0 = lambda s, q: 1 + 5 / 27 * s ** 2 + 20 / 9 * q

  gea2_f = lambda x, u: gea2_f0(gea2_s(x), gea2_q(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, gea2_f, rs, z, xs0, xs1, u0, u1)

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
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t22 / t33
  t39 = l0 * t31
  t45 = 0.1e1 + 0.5e1 / 0.648e3 * t29 * t32 * t35 + 0.5e1 / 0.54e2 * t29 * t39 / t22 / r0
  t49 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t45)
  t69 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t45 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-0.5e1 / 0.243e3 * t29 * t32 / t22 / t33 / r0 - 0.25e2 / 0.162e3 * t29 * t39 * t35))
  vrho_0_ = 0.2e1 * r0 * t69 + 0.2e1 * t49
  t72 = t7 * t20
  t75 = t28 * t31
  t79 = f.my_piecewise3(t2, 0, t72 / t33 * t24 * t75 / 0.864e3)
  vsigma_0_ = 0.2e1 * r0 * t79
  t86 = f.my_piecewise3(t2, 0, t72 / r0 * t24 * t75 / 0.72e2)
  vlapl_0_ = 0.2e1 * r0 * t86
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
  t46 = 0.1e1 + 0.5e1 / 0.648e3 * t29 * t32 * t36 + 0.5e1 / 0.54e2 * t29 * t40 / t34 / r0
  t50 = t20 * t34
  t53 = 0.1e1 / t34 / t33 / r0
  t60 = -0.5e1 / 0.243e3 * t29 * t32 * t53 - 0.25e2 / 0.162e3 * t29 * t40 * t36
  t65 = f.my_piecewise3(t2, 0, t7 * t23 * t46 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t50 * t60)
  t76 = t33 ** 2
  t90 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t46 / 0.30e2 + t7 * t23 * t60 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t50 * (0.55e2 / 0.729e3 * t29 * t32 / t34 / t76 + 0.100e3 / 0.243e3 * t29 * t40 * t53))
  v2rho2_0_ = 0.2e1 * r0 * t90 + 0.4e1 * t65
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
  t47 = 0.1e1 + 0.5e1 / 0.648e3 * t30 * t33 * t37 + 0.5e1 / 0.54e2 * t30 * t41 / t35 / r0
  t52 = t20 / t21
  t55 = 0.1e1 / t35 / t34 / r0
  t62 = -0.5e1 / 0.243e3 * t30 * t33 * t55 - 0.25e2 / 0.162e3 * t30 * t41 * t37
  t66 = t20 * t35
  t67 = t34 ** 2
  t69 = 0.1e1 / t35 / t67
  t76 = 0.55e2 / 0.729e3 * t30 * t33 * t69 + 0.100e3 / 0.243e3 * t30 * t41 * t55
  t81 = f.my_piecewise3(t2, 0, -t7 * t24 * t47 / 0.30e2 + t7 * t52 * t62 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t66 * t76)
  t109 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t47 - t7 * t24 * t62 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t52 * t76 + 0.3e1 / 0.20e2 * t7 * t66 * (-0.770e3 / 0.2187e4 * t30 * t33 / t35 / t67 / r0 - 0.1100e4 / 0.729e3 * t30 * t41 * t69))
  v3rho3_0_ = 0.2e1 * r0 * t109 + 0.6e1 * t81

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
  t47 = 0.1e1 + 0.5e1 / 0.648e3 * t31 * t34 * t37 + 0.5e1 / 0.54e2 * t31 * t41 / t35 / r0
  t53 = t20 / t22 / r0
  t54 = t21 * r0
  t56 = 0.1e1 / t35 / t54
  t63 = -0.5e1 / 0.243e3 * t31 * t34 * t56 - 0.25e2 / 0.162e3 * t31 * t41 * t37
  t68 = t20 / t22
  t69 = t21 ** 2
  t71 = 0.1e1 / t35 / t69
  t78 = 0.55e2 / 0.729e3 * t31 * t34 * t71 + 0.100e3 / 0.243e3 * t31 * t41 * t56
  t82 = t20 * t35
  t85 = 0.1e1 / t35 / t69 / r0
  t92 = -0.770e3 / 0.2187e4 * t31 * t34 * t85 - 0.1100e4 / 0.729e3 * t31 * t41 * t71
  t97 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t47 - t7 * t53 * t63 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t68 * t78 + 0.3e1 / 0.20e2 * t7 * t82 * t92)
  t128 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 / t22 / t54 * t47 + 0.8e1 / 0.45e2 * t7 * t25 * t63 - t7 * t53 * t78 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t68 * t92 + 0.3e1 / 0.20e2 * t7 * t82 * (0.13090e5 / 0.6561e4 * t31 * t34 / t35 / t69 / t21 + 0.15400e5 / 0.2187e4 * t31 * t41 * t85))
  v4rho4_0_ = 0.2e1 * r0 * t128 + 0.8e1 * t97

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
  t54 = 0.1e1 + 0.5e1 / 0.648e3 * t40 * s0 * t45 + 0.5e1 / 0.54e2 * t40 * l0 / t43 / r0
  t58 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t60 = t59 * f.p.zeta_threshold
  t62 = f.my_piecewise3(t21, t60, t23 * t20)
  t63 = 0.1e1 / t32
  t64 = t62 * t63
  t67 = t6 * t64 * t54 / 0.10e2
  t68 = t62 * t33
  t71 = 0.1e1 / t43 / t41 / r0
  t78 = -0.5e1 / 0.243e3 * t40 * s0 * t71 - 0.25e2 / 0.162e3 * t40 * l0 * t45
  t83 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t54 + t67 + 0.3e1 / 0.20e2 * t6 * t68 * t78)
  t85 = r1 <= f.p.dens_threshold
  t86 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t87 = 0.1e1 + t86
  t88 = t87 <= f.p.zeta_threshold
  t89 = t87 ** (0.1e1 / 0.3e1)
  t90 = t89 ** 2
  t92 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t95 = f.my_piecewise3(t88, 0, 0.5e1 / 0.3e1 * t90 * t92)
  t96 = t95 * t33
  t97 = r1 ** 2
  t98 = r1 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t101 = 0.1e1 / t99 / t97
  t110 = 0.1e1 + 0.5e1 / 0.648e3 * t40 * s2 * t101 + 0.5e1 / 0.54e2 * t40 * l1 / t99 / r1
  t115 = f.my_piecewise3(t88, t60, t90 * t87)
  t116 = t115 * t63
  t119 = t6 * t116 * t110 / 0.10e2
  t121 = f.my_piecewise3(t85, 0, 0.3e1 / 0.20e2 * t6 * t96 * t110 + t119)
  t123 = 0.1e1 / t22
  t124 = t28 ** 2
  t129 = t17 / t24 / t7
  t131 = -0.2e1 * t25 + 0.2e1 * t129
  t132 = f.my_piecewise5(t11, 0, t15, 0, t131)
  t136 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t123 * t124 + 0.5e1 / 0.3e1 * t23 * t132)
  t143 = t6 * t31 * t63 * t54
  t149 = 0.1e1 / t32 / t7
  t153 = t6 * t62 * t149 * t54 / 0.30e2
  t155 = t6 * t64 * t78
  t157 = t41 ** 2
  t171 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t136 * t33 * t54 + t143 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t78 - t153 + t155 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t68 * (0.55e2 / 0.729e3 * t40 * s0 / t43 / t157 + 0.100e3 / 0.243e3 * t40 * l0 * t71))
  t172 = 0.1e1 / t89
  t173 = t92 ** 2
  t177 = f.my_piecewise5(t15, 0, t11, 0, -t131)
  t181 = f.my_piecewise3(t88, 0, 0.10e2 / 0.9e1 * t172 * t173 + 0.5e1 / 0.3e1 * t90 * t177)
  t188 = t6 * t95 * t63 * t110
  t193 = t6 * t115 * t149 * t110 / 0.30e2
  t195 = f.my_piecewise3(t85, 0, 0.3e1 / 0.20e2 * t6 * t181 * t33 * t110 + t188 / 0.5e1 - t193)
  d11 = 0.2e1 * t83 + 0.2e1 * t121 + t7 * (t171 + t195)
  t198 = -t8 - t26
  t199 = f.my_piecewise5(t11, 0, t15, 0, t198)
  t202 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t199)
  t203 = t202 * t33
  t208 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t203 * t54 + t67)
  t210 = f.my_piecewise5(t15, 0, t11, 0, -t198)
  t213 = f.my_piecewise3(t88, 0, 0.5e1 / 0.3e1 * t90 * t210)
  t214 = t213 * t33
  t218 = t115 * t33
  t221 = 0.1e1 / t99 / t97 / r1
  t228 = -0.5e1 / 0.243e3 * t40 * s2 * t221 - 0.25e2 / 0.162e3 * t40 * l1 * t101
  t233 = f.my_piecewise3(t85, 0, 0.3e1 / 0.20e2 * t6 * t214 * t110 + t119 + 0.3e1 / 0.20e2 * t6 * t218 * t228)
  t237 = 0.2e1 * t129
  t238 = f.my_piecewise5(t11, 0, t15, 0, t237)
  t242 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t123 * t199 * t28 + 0.5e1 / 0.3e1 * t23 * t238)
  t249 = t6 * t202 * t63 * t54
  t257 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t242 * t33 * t54 + t249 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t203 * t78 + t143 / 0.10e2 - t153 + t155 / 0.10e2)
  t261 = f.my_piecewise5(t15, 0, t11, 0, -t237)
  t265 = f.my_piecewise3(t88, 0, 0.10e2 / 0.9e1 * t172 * t210 * t92 + 0.5e1 / 0.3e1 * t90 * t261)
  t272 = t6 * t213 * t63 * t110
  t279 = t6 * t116 * t228
  t282 = f.my_piecewise3(t85, 0, 0.3e1 / 0.20e2 * t6 * t265 * t33 * t110 + t272 / 0.10e2 + t188 / 0.10e2 - t193 + 0.3e1 / 0.20e2 * t6 * t96 * t228 + t279 / 0.10e2)
  d12 = t83 + t121 + t208 + t233 + t7 * (t257 + t282)
  t287 = t199 ** 2
  t291 = 0.2e1 * t25 + 0.2e1 * t129
  t292 = f.my_piecewise5(t11, 0, t15, 0, t291)
  t296 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t123 * t287 + 0.5e1 / 0.3e1 * t23 * t292)
  t303 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t296 * t33 * t54 + t249 / 0.5e1 - t153)
  t304 = t210 ** 2
  t308 = f.my_piecewise5(t15, 0, t11, 0, -t291)
  t312 = f.my_piecewise3(t88, 0, 0.10e2 / 0.9e1 * t172 * t304 + 0.5e1 / 0.3e1 * t90 * t308)
  t322 = t97 ** 2
  t336 = f.my_piecewise3(t85, 0, 0.3e1 / 0.20e2 * t6 * t312 * t33 * t110 + t272 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t214 * t228 - t193 + t279 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t218 * (0.55e2 / 0.729e3 * t40 * s2 / t99 / t322 + 0.100e3 / 0.243e3 * t40 * l1 * t221))
  d22 = 0.2e1 * t208 + 0.2e1 * t233 + t7 * (t303 + t336)
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
  t65 = 0.1e1 + 0.5e1 / 0.648e3 * t51 * s0 * t56 + 0.5e1 / 0.54e2 * t51 * l0 / t54 / r0
  t71 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t72 = 0.1e1 / t43
  t73 = t71 * t72
  t77 = t71 * t44
  t80 = 0.1e1 / t54 / t52 / r0
  t87 = -0.5e1 / 0.243e3 * t51 * s0 * t80 - 0.25e2 / 0.162e3 * t51 * l0 * t56
  t91 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t92 = t91 ** 2
  t93 = t92 * f.p.zeta_threshold
  t95 = f.my_piecewise3(t21, t93, t32 * t20)
  t97 = 0.1e1 / t43 / t7
  t98 = t95 * t97
  t102 = t95 * t72
  t106 = t95 * t44
  t107 = t52 ** 2
  t109 = 0.1e1 / t54 / t107
  t116 = 0.55e2 / 0.729e3 * t51 * s0 * t109 + 0.100e3 / 0.243e3 * t51 * l0 * t80
  t121 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t65 + t6 * t73 * t65 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t77 * t87 - t6 * t98 * t65 / 0.30e2 + t6 * t102 * t87 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t106 * t116)
  t123 = r1 <= f.p.dens_threshold
  t124 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t125 = 0.1e1 + t124
  t126 = t125 <= f.p.zeta_threshold
  t127 = t125 ** (0.1e1 / 0.3e1)
  t128 = 0.1e1 / t127
  t130 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t131 = t130 ** 2
  t134 = t127 ** 2
  t136 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t140 = f.my_piecewise3(t126, 0, 0.10e2 / 0.9e1 * t128 * t131 + 0.5e1 / 0.3e1 * t134 * t136)
  t142 = r1 ** 2
  t143 = r1 ** (0.1e1 / 0.3e1)
  t144 = t143 ** 2
  t155 = 0.1e1 + 0.5e1 / 0.648e3 * t51 * s2 / t144 / t142 + 0.5e1 / 0.54e2 * t51 * l1 / t144 / r1
  t161 = f.my_piecewise3(t126, 0, 0.5e1 / 0.3e1 * t134 * t130)
  t167 = f.my_piecewise3(t126, t93, t134 * t125)
  t173 = f.my_piecewise3(t123, 0, 0.3e1 / 0.20e2 * t6 * t140 * t44 * t155 + t6 * t161 * t72 * t155 / 0.5e1 - t6 * t167 * t97 * t155 / 0.30e2)
  t183 = t24 ** 2
  t187 = 0.6e1 * t34 - 0.6e1 * t17 / t183
  t188 = f.my_piecewise5(t11, 0, t15, 0, t187)
  t192 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t188)
  t215 = 0.1e1 / t43 / t24
  t240 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t192 * t44 * t65 + 0.3e1 / 0.10e2 * t6 * t42 * t72 * t65 + 0.9e1 / 0.20e2 * t6 * t45 * t87 - t6 * t71 * t97 * t65 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t73 * t87 + 0.9e1 / 0.20e2 * t6 * t77 * t116 + 0.2e1 / 0.45e2 * t6 * t95 * t215 * t65 - t6 * t98 * t87 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t102 * t116 + 0.3e1 / 0.20e2 * t6 * t106 * (-0.770e3 / 0.2187e4 * t51 * s0 / t54 / t107 / r0 - 0.1100e4 / 0.729e3 * t51 * l0 * t109))
  t250 = f.my_piecewise5(t15, 0, t11, 0, -t187)
  t254 = f.my_piecewise3(t126, 0, -0.10e2 / 0.27e2 / t127 / t125 * t131 * t130 + 0.10e2 / 0.3e1 * t128 * t130 * t136 + 0.5e1 / 0.3e1 * t134 * t250)
  t272 = f.my_piecewise3(t123, 0, 0.3e1 / 0.20e2 * t6 * t254 * t44 * t155 + 0.3e1 / 0.10e2 * t6 * t140 * t72 * t155 - t6 * t161 * t97 * t155 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t167 * t215 * t155)
  d111 = 0.3e1 * t121 + 0.3e1 * t173 + t7 * (t240 + t272)

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
  t77 = 0.1e1 + 0.5e1 / 0.648e3 * t63 * s0 * t68 + 0.5e1 / 0.54e2 * t63 * l0 / t66 / r0
  t86 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t87 = 0.1e1 / t55
  t88 = t86 * t87
  t92 = t86 * t56
  t95 = 0.1e1 / t66 / t64 / r0
  t102 = -0.5e1 / 0.243e3 * t63 * s0 * t95 - 0.25e2 / 0.162e3 * t63 * l0 * t68
  t108 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t110 = 0.1e1 / t55 / t7
  t111 = t108 * t110
  t115 = t108 * t87
  t119 = t108 * t56
  t120 = t64 ** 2
  t122 = 0.1e1 / t66 / t120
  t129 = 0.55e2 / 0.729e3 * t63 * s0 * t122 + 0.100e3 / 0.243e3 * t63 * l0 * t95
  t133 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t134 = t133 ** 2
  t135 = t134 * f.p.zeta_threshold
  t137 = f.my_piecewise3(t21, t135, t44 * t20)
  t139 = 0.1e1 / t55 / t25
  t140 = t137 * t139
  t144 = t137 * t110
  t148 = t137 * t87
  t152 = t137 * t56
  t155 = 0.1e1 / t66 / t120 / r0
  t162 = -0.770e3 / 0.2187e4 * t63 * s0 * t155 - 0.1100e4 / 0.729e3 * t63 * l0 * t122
  t167 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t77 + 0.3e1 / 0.10e2 * t6 * t88 * t77 + 0.9e1 / 0.20e2 * t6 * t92 * t102 - t6 * t111 * t77 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t115 * t102 + 0.9e1 / 0.20e2 * t6 * t119 * t129 + 0.2e1 / 0.45e2 * t6 * t140 * t77 - t6 * t144 * t102 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t148 * t129 + 0.3e1 / 0.20e2 * t6 * t152 * t162)
  t169 = r1 <= f.p.dens_threshold
  t170 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t171 = 0.1e1 + t170
  t172 = t171 <= f.p.zeta_threshold
  t173 = t171 ** (0.1e1 / 0.3e1)
  t175 = 0.1e1 / t173 / t171
  t177 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t178 = t177 ** 2
  t182 = 0.1e1 / t173
  t183 = t182 * t177
  t185 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t188 = t173 ** 2
  t190 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t194 = f.my_piecewise3(t172, 0, -0.10e2 / 0.27e2 * t175 * t178 * t177 + 0.10e2 / 0.3e1 * t183 * t185 + 0.5e1 / 0.3e1 * t188 * t190)
  t196 = r1 ** 2
  t197 = r1 ** (0.1e1 / 0.3e1)
  t198 = t197 ** 2
  t209 = 0.1e1 + 0.5e1 / 0.648e3 * t63 * s2 / t198 / t196 + 0.5e1 / 0.54e2 * t63 * l1 / t198 / r1
  t218 = f.my_piecewise3(t172, 0, 0.10e2 / 0.9e1 * t182 * t178 + 0.5e1 / 0.3e1 * t188 * t185)
  t225 = f.my_piecewise3(t172, 0, 0.5e1 / 0.3e1 * t188 * t177)
  t231 = f.my_piecewise3(t172, t135, t188 * t171)
  t237 = f.my_piecewise3(t169, 0, 0.3e1 / 0.20e2 * t6 * t194 * t56 * t209 + 0.3e1 / 0.10e2 * t6 * t218 * t87 * t209 - t6 * t225 * t110 * t209 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t231 * t139 * t209)
  t239 = t20 ** 2
  t242 = t30 ** 2
  t248 = t41 ** 2
  t257 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t258 = f.my_piecewise5(t11, 0, t15, 0, t257)
  t262 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t239 * t242 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t248 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t258)
  t320 = 0.1e1 / t55 / t36
  t325 = 0.3e1 / 0.20e2 * t6 * t262 * t56 * t77 + 0.3e1 / 0.5e1 * t6 * t57 * t102 + 0.6e1 / 0.5e1 * t6 * t88 * t102 + 0.9e1 / 0.10e2 * t6 * t92 * t129 - 0.2e1 / 0.5e1 * t6 * t111 * t102 + 0.6e1 / 0.5e1 * t6 * t115 * t129 + 0.3e1 / 0.5e1 * t6 * t119 * t162 + 0.8e1 / 0.45e2 * t6 * t140 * t102 - t6 * t144 * t129 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t148 * t162 + 0.3e1 / 0.20e2 * t6 * t152 * (0.13090e5 / 0.6561e4 * t63 * s0 / t66 / t120 / t64 + 0.15400e5 / 0.2187e4 * t63 * l0 * t155) + 0.2e1 / 0.5e1 * t6 * t54 * t87 * t77 - t6 * t86 * t110 * t77 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t108 * t139 * t77 - 0.14e2 / 0.135e3 * t6 * t137 * t320 * t77
  t326 = f.my_piecewise3(t1, 0, t325)
  t327 = t171 ** 2
  t330 = t178 ** 2
  t336 = t185 ** 2
  t342 = f.my_piecewise5(t15, 0, t11, 0, -t257)
  t346 = f.my_piecewise3(t172, 0, 0.40e2 / 0.81e2 / t173 / t327 * t330 - 0.20e2 / 0.9e1 * t175 * t178 * t185 + 0.10e2 / 0.3e1 * t182 * t336 + 0.40e2 / 0.9e1 * t183 * t190 + 0.5e1 / 0.3e1 * t188 * t342)
  t368 = f.my_piecewise3(t169, 0, 0.3e1 / 0.20e2 * t6 * t346 * t56 * t209 + 0.2e1 / 0.5e1 * t6 * t194 * t87 * t209 - t6 * t218 * t110 * t209 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t225 * t139 * t209 - 0.14e2 / 0.135e3 * t6 * t231 * t320 * t209)
  d1111 = 0.4e1 * t167 + 0.4e1 * t237 + t7 * (t326 + t368)

  res = {'v4rho4': d1111}
  return res
