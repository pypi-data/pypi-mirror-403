"""Generated from mgga_x_th.mpl."""

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
  th_f0 = lambda x, u, t: -27 * jnp.pi / (10 * t) * (1 + 7 * x ** 2 / (108 * t))

  th_f = lambda x, u, t: -th_f0(x, u, 2 * t) / X_FACTOR_C

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, th_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  th_f0 = lambda x, u, t: -27 * jnp.pi / (10 * t) * (1 + 7 * x ** 2 / (108 * t))

  th_f = lambda x, u, t: -th_f0(x, u, 2 * t) / X_FACTOR_C

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, th_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  th_f0 = lambda x, u, t: -27 * jnp.pi / (10 * t) * (1 + 7 * x ** 2 / (108 * t))

  th_f = lambda x, u, t: -th_f0(x, u, 2 * t) / X_FACTOR_C

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, th_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t1 = r0 <= f.p.dens_threshold
  t2 = jnp.pi ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = r0 + r1
  t5 = 0.1e1 / t4
  t8 = 0.2e1 * r0 * t5 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t12 = 0.2e1 * r1 * t5 <= f.p.zeta_threshold
  t13 = -t9
  t14 = r0 - r1
  t15 = t14 * t5
  t16 = f.my_piecewise5(t8, t9, t12, t13, t15)
  t17 = 0.1e1 + t16
  t18 = t17 <= f.p.zeta_threshold
  t19 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t20 = t19 * f.p.zeta_threshold
  t21 = t17 ** (0.1e1 / 0.3e1)
  t23 = f.my_piecewise3(t18, t20, t21 * t17)
  t24 = t3 * t23
  t25 = t4 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / tau0
  t27 = t25 * t26
  t28 = t24 * t27
  t29 = r0 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t36 = 0.1e1 + 0.7e1 / 0.216e3 * s0 / r0 * t26
  t39 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t41 = 4 ** (0.1e1 / 0.3e1)
  t42 = 0.1e1 / t39 * t41
  t43 = t30 * r0 * t36 * t42
  t46 = f.my_piecewise3(t1, 0, -0.27e2 / 0.80e2 * t28 * t43)
  t47 = r1 <= f.p.dens_threshold
  t48 = f.my_piecewise5(t12, t9, t8, t13, -t15)
  t49 = 0.1e1 + t48
  t50 = t49 <= f.p.zeta_threshold
  t51 = t49 ** (0.1e1 / 0.3e1)
  t53 = f.my_piecewise3(t50, t20, t51 * t49)
  t54 = t3 * t53
  t55 = 0.1e1 / tau1
  t56 = t25 * t55
  t57 = t54 * t56
  t58 = r1 ** (0.1e1 / 0.3e1)
  t59 = t58 ** 2
  t65 = 0.1e1 + 0.7e1 / 0.216e3 * s2 / r1 * t55
  t67 = t59 * r1 * t65 * t42
  t70 = f.my_piecewise3(t47, 0, -0.27e2 / 0.80e2 * t57 * t67)
  t71 = t4 ** 2
  t73 = t14 / t71
  t74 = t5 - t73
  t75 = f.my_piecewise5(t8, 0, t12, 0, t74)
  t78 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t21 * t75)
  t83 = t25 ** 2
  t84 = 0.1e1 / t83
  t88 = 0.9e1 / 0.80e2 * t24 * t84 * t26 * t43
  t93 = tau0 ** 2
  t94 = 0.1e1 / t93
  t96 = t24 * t25 * t94
  t103 = f.my_piecewise3(t1, 0, -0.27e2 / 0.80e2 * t3 * t78 * t27 * t43 - t88 - 0.9e1 / 0.16e2 * t28 * t30 * t36 * t42 + 0.7e1 / 0.640e3 * t96 / t29 * s0 * t42)
  t105 = f.my_piecewise5(t12, 0, t8, 0, -t74)
  t108 = f.my_piecewise3(t50, 0, 0.4e1 / 0.3e1 * t51 * t105)
  t116 = 0.9e1 / 0.80e2 * t54 * t84 * t55 * t67
  t118 = f.my_piecewise3(t47, 0, -0.27e2 / 0.80e2 * t3 * t108 * t56 * t67 - t116)
  vrho_0_ = t46 + t70 + t4 * (t103 + t118)
  t121 = -t5 - t73
  t122 = f.my_piecewise5(t8, 0, t12, 0, t121)
  t125 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t21 * t122)
  t131 = f.my_piecewise3(t1, 0, -0.27e2 / 0.80e2 * t3 * t125 * t27 * t43 - t88)
  t133 = f.my_piecewise5(t12, 0, t8, 0, -t121)
  t136 = f.my_piecewise3(t50, 0, 0.4e1 / 0.3e1 * t51 * t133)
  t145 = tau1 ** 2
  t146 = 0.1e1 / t145
  t148 = t54 * t25 * t146
  t155 = f.my_piecewise3(t47, 0, -0.27e2 / 0.80e2 * t3 * t136 * t56 * t67 - t116 - 0.9e1 / 0.16e2 * t57 * t59 * t65 * t42 + 0.7e1 / 0.640e3 * t148 / t58 * s2 * t42)
  vrho_1_ = t46 + t70 + t4 * (t131 + t155)
  t163 = f.my_piecewise3(t1, 0, -0.7e1 / 0.640e3 * t24 * t25 * t94 * t30 * t42)
  vsigma_0_ = t4 * t163
  vsigma_1_ = 0.0e0
  t169 = f.my_piecewise3(t47, 0, -0.7e1 / 0.640e3 * t54 * t25 * t146 * t59 * t42)
  vsigma_2_ = t4 * t169
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t181 = f.my_piecewise3(t1, 0, 0.27e2 / 0.80e2 * t96 * t43 + 0.7e1 / 0.640e3 * t24 * t25 / t93 / tau0 * t30 * s0 * t42)
  vtau_0_ = t4 * t181
  t193 = f.my_piecewise3(t47, 0, 0.27e2 / 0.80e2 * t148 * t67 + 0.7e1 / 0.640e3 * t54 * t25 / t145 / tau1 * t59 * s2 * t42)
  vtau_1_ = t4 * t193
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
  th_f0 = lambda x, u, t: -27 * jnp.pi / (10 * t) * (1 + 7 * x ** 2 / (108 * t))

  th_f = lambda x, u, t: -th_f0(x, u, 2 * t) / X_FACTOR_C

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, th_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = 0.1e1 <= f.p.zeta_threshold
  t6 = f.p.zeta_threshold - 0.1e1
  t8 = f.my_piecewise5(t5, t6, t5, -t6, 0)
  t9 = 0.1e1 + t8
  t11 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t13 = t9 ** (0.1e1 / 0.3e1)
  t15 = f.my_piecewise3(t9 <= f.p.zeta_threshold, t11 * f.p.zeta_threshold, t13 * t9)
  t16 = t4 * t15
  t17 = r0 ** 2
  t18 = 0.1e1 / tau0
  t21 = 2 ** (0.1e1 / 0.3e1)
  t29 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t31 = 4 ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t29 * t31
  t33 = t21 * (0.1e1 + 0.7e1 / 0.216e3 * s0 / r0 * t18) * t32
  t36 = f.my_piecewise3(t2, 0, -0.27e2 / 0.160e3 * t16 * t17 * t18 * t33)
  t41 = tau0 ** 2
  t42 = 0.1e1 / t41
  t45 = t21 * s0 * t32
  t49 = f.my_piecewise3(t2, 0, -0.27e2 / 0.80e2 * t16 * r0 * t18 * t33 + 0.7e1 / 0.1280e4 * t16 * t42 * t45)
  vrho_0_ = 0.2e1 * r0 * t49 + 0.2e1 * t36
  t57 = f.my_piecewise3(t2, 0, -0.7e1 / 0.1280e4 * t16 * r0 * t42 * t21 * t32)
  vsigma_0_ = 0.2e1 * r0 * t57
  vlapl_0_ = 0.0e0
  t70 = f.my_piecewise3(t2, 0, 0.27e2 / 0.160e3 * t16 * t17 * t42 * t33 + 0.7e1 / 0.1280e4 * t16 * r0 / t41 / tau0 * t45)
  vtau_0_ = 0.2e1 * r0 * t70
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
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = 0.1e1 <= f.p.zeta_threshold
  t6 = f.p.zeta_threshold - 0.1e1
  t8 = f.my_piecewise5(t5, t6, t5, -t6, 0)
  t9 = 0.1e1 + t8
  t11 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t13 = t9 ** (0.1e1 / 0.3e1)
  t15 = f.my_piecewise3(t9 <= f.p.zeta_threshold, t11 * f.p.zeta_threshold, t13 * t9)
  t16 = t4 * t15
  t17 = 0.1e1 / tau0
  t20 = 2 ** (0.1e1 / 0.3e1)
  t21 = 0.1e1 / r0
  t28 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t30 = 4 ** (0.1e1 / 0.3e1)
  t31 = 0.1e1 / t28 * t30
  t32 = t20 * (0.1e1 + 0.7e1 / 0.216e3 * s0 * t21 * t17) * t31
  t35 = tau0 ** 2
  t36 = 0.1e1 / t35
  t39 = t20 * s0 * t31
  t43 = f.my_piecewise3(t2, 0, -0.27e2 / 0.80e2 * t16 * r0 * t17 * t32 + 0.7e1 / 0.1280e4 * t16 * t36 * t39)
  t53 = f.my_piecewise3(t2, 0, -0.27e2 / 0.80e2 * t16 * t17 * t32 + 0.7e1 / 0.640e3 * t16 * t21 * t36 * t39)
  v2rho2_0_ = 0.2e1 * r0 * t53 + 0.4e1 * t43
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = 0.1e1 <= f.p.zeta_threshold
  t6 = f.p.zeta_threshold - 0.1e1
  t8 = f.my_piecewise5(t5, t6, t5, -t6, 0)
  t9 = 0.1e1 + t8
  t11 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t13 = t9 ** (0.1e1 / 0.3e1)
  t15 = f.my_piecewise3(t9 <= f.p.zeta_threshold, t11 * f.p.zeta_threshold, t13 * t9)
  t16 = t4 * t15
  t17 = 0.1e1 / tau0
  t19 = 2 ** (0.1e1 / 0.3e1)
  t20 = 0.1e1 / r0
  t27 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / t27 * t29
  t34 = tau0 ** 2
  t43 = f.my_piecewise3(t2, 0, -0.27e2 / 0.80e2 * t16 * t17 * t19 * (0.1e1 + 0.7e1 / 0.216e3 * s0 * t20 * t17) * t30 + 0.7e1 / 0.640e3 * t16 * t20 / t34 * t19 * s0 * t30)
  t45 = f.my_piecewise3(t2, 0, 0)
  v3rho3_0_ = 0.2e1 * r0 * t45 + 0.6e1 * t43

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t3 = f.my_piecewise3(r0 / 0.2e1 <= f.p.dens_threshold, 0, 0)
  v4rho4_0_ = 0.2e1 * r0 * t3 + 0.8e1 * t3

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = jnp.pi ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = r0 + r1
  t5 = 0.1e1 / t4
  t8 = 0.2e1 * r0 * t5 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t12 = 0.2e1 * r1 * t5 <= f.p.zeta_threshold
  t13 = -t9
  t14 = r0 - r1
  t15 = t14 * t5
  t16 = f.my_piecewise5(t8, t9, t12, t13, t15)
  t17 = 0.1e1 + t16
  t18 = t17 <= f.p.zeta_threshold
  t19 = t17 ** (0.1e1 / 0.3e1)
  t20 = t4 ** 2
  t21 = 0.1e1 / t20
  t22 = t14 * t21
  t23 = t5 - t22
  t24 = f.my_piecewise5(t8, 0, t12, 0, t23)
  t27 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t19 * t24)
  t28 = t3 * t27
  t29 = t4 ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / tau0
  t31 = t29 * t30
  t32 = t28 * t31
  t33 = r0 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t40 = 0.1e1 + 0.7e1 / 0.216e3 * s0 / r0 * t30
  t43 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t45 = 4 ** (0.1e1 / 0.3e1)
  t46 = 0.1e1 / t43 * t45
  t47 = t34 * r0 * t40 * t46
  t50 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t51 = t50 * f.p.zeta_threshold
  t53 = f.my_piecewise3(t18, t51, t19 * t17)
  t54 = t3 * t53
  t55 = t29 ** 2
  t56 = 0.1e1 / t55
  t57 = t56 * t30
  t58 = t54 * t57
  t60 = 0.9e1 / 0.80e2 * t58 * t47
  t61 = t54 * t31
  t63 = t34 * t40 * t46
  t66 = tau0 ** 2
  t67 = 0.1e1 / t66
  t68 = t29 * t67
  t69 = t54 * t68
  t70 = 0.1e1 / t33
  t72 = t70 * s0 * t46
  t76 = f.my_piecewise3(t1, 0, -0.27e2 / 0.80e2 * t32 * t47 - t60 - 0.9e1 / 0.16e2 * t61 * t63 + 0.7e1 / 0.640e3 * t69 * t72)
  t78 = r1 <= f.p.dens_threshold
  t79 = f.my_piecewise5(t12, t9, t8, t13, -t15)
  t80 = 0.1e1 + t79
  t81 = t80 <= f.p.zeta_threshold
  t82 = t80 ** (0.1e1 / 0.3e1)
  t84 = f.my_piecewise5(t12, 0, t8, 0, -t23)
  t87 = f.my_piecewise3(t81, 0, 0.4e1 / 0.3e1 * t82 * t84)
  t88 = t3 * t87
  t89 = 0.1e1 / tau1
  t90 = t29 * t89
  t91 = t88 * t90
  t92 = r1 ** (0.1e1 / 0.3e1)
  t93 = t92 ** 2
  t99 = 0.1e1 + 0.7e1 / 0.216e3 * s2 / r1 * t89
  t101 = t93 * r1 * t99 * t46
  t105 = f.my_piecewise3(t81, t51, t82 * t80)
  t106 = t3 * t105
  t107 = t56 * t89
  t108 = t106 * t107
  t110 = 0.9e1 / 0.80e2 * t108 * t101
  t112 = f.my_piecewise3(t78, 0, -0.27e2 / 0.80e2 * t91 * t101 - t110)
  t114 = t19 ** 2
  t115 = 0.1e1 / t114
  t116 = t24 ** 2
  t121 = t14 / t20 / t4
  t123 = -0.2e1 * t21 + 0.2e1 * t121
  t124 = f.my_piecewise5(t8, 0, t12, 0, t123)
  t128 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t115 * t116 + 0.4e1 / 0.3e1 * t19 * t124)
  t134 = t28 * t57 * t47
  t142 = 0.1e1 / t55 / t4
  t146 = 0.3e1 / 0.40e2 * t54 * t142 * t30 * t47
  t147 = t58 * t63
  t151 = t54 * t56 * t67 * t72
  t164 = f.my_piecewise3(t1, 0, -0.27e2 / 0.80e2 * t3 * t128 * t31 * t47 - 0.9e1 / 0.40e2 * t134 - 0.9e1 / 0.8e1 * t32 * t63 + 0.7e1 / 0.320e3 * t28 * t68 * t72 + t146 - 0.3e1 / 0.8e1 * t147 + 0.7e1 / 0.960e3 * t151 - 0.3e1 / 0.8e1 * t61 * t70 * t40 * t46 + 0.7e1 / 0.480e3 * t69 / t33 / r0 * s0 * t46)
  t165 = t82 ** 2
  t166 = 0.1e1 / t165
  t167 = t84 ** 2
  t171 = f.my_piecewise5(t12, 0, t8, 0, -t123)
  t175 = f.my_piecewise3(t81, 0, 0.4e1 / 0.9e1 * t166 * t167 + 0.4e1 / 0.3e1 * t82 * t171)
  t181 = t88 * t107 * t101
  t186 = 0.3e1 / 0.40e2 * t106 * t142 * t89 * t101
  t188 = f.my_piecewise3(t78, 0, -0.27e2 / 0.80e2 * t3 * t175 * t90 * t101 - 0.9e1 / 0.40e2 * t181 + t186)
  d11 = 0.2e1 * t76 + 0.2e1 * t112 + t4 * (t164 + t188)
  t191 = -t5 - t22
  t192 = f.my_piecewise5(t8, 0, t12, 0, t191)
  t195 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t19 * t192)
  t196 = t3 * t195
  t197 = t196 * t31
  t201 = f.my_piecewise3(t1, 0, -0.27e2 / 0.80e2 * t197 * t47 - t60)
  t203 = f.my_piecewise5(t12, 0, t8, 0, -t191)
  t206 = f.my_piecewise3(t81, 0, 0.4e1 / 0.3e1 * t82 * t203)
  t207 = t3 * t206
  t208 = t207 * t90
  t211 = t106 * t90
  t213 = t93 * t99 * t46
  t216 = tau1 ** 2
  t217 = 0.1e1 / t216
  t218 = t29 * t217
  t219 = t106 * t218
  t220 = 0.1e1 / t92
  t222 = t220 * s2 * t46
  t226 = f.my_piecewise3(t78, 0, -0.27e2 / 0.80e2 * t208 * t101 - t110 - 0.9e1 / 0.16e2 * t211 * t213 + 0.7e1 / 0.640e3 * t219 * t222)
  t230 = 0.2e1 * t121
  t231 = f.my_piecewise5(t8, 0, t12, 0, t230)
  t235 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t115 * t192 * t24 + 0.4e1 / 0.3e1 * t19 * t231)
  t241 = t196 * t57 * t47
  t252 = f.my_piecewise3(t1, 0, -0.27e2 / 0.80e2 * t3 * t235 * t31 * t47 - 0.9e1 / 0.80e2 * t241 - 0.9e1 / 0.16e2 * t197 * t63 + 0.7e1 / 0.640e3 * t196 * t68 * t72 - 0.9e1 / 0.80e2 * t134 + t146 - 0.3e1 / 0.16e2 * t147 + 0.7e1 / 0.1920e4 * t151)
  t256 = f.my_piecewise5(t12, 0, t8, 0, -t230)
  t260 = f.my_piecewise3(t81, 0, 0.4e1 / 0.9e1 * t166 * t203 * t84 + 0.4e1 / 0.3e1 * t82 * t256)
  t266 = t207 * t107 * t101
  t271 = t108 * t213
  t278 = t106 * t56 * t217 * t222
  t281 = f.my_piecewise3(t78, 0, -0.27e2 / 0.80e2 * t3 * t260 * t90 * t101 - 0.9e1 / 0.80e2 * t266 - 0.9e1 / 0.80e2 * t181 + t186 - 0.9e1 / 0.16e2 * t91 * t213 - 0.3e1 / 0.16e2 * t271 + 0.7e1 / 0.640e3 * t88 * t218 * t222 + 0.7e1 / 0.1920e4 * t278)
  d12 = t76 + t112 + t201 + t226 + t4 * (t252 + t281)
  t286 = t192 ** 2
  t290 = 0.2e1 * t21 + 0.2e1 * t121
  t291 = f.my_piecewise5(t8, 0, t12, 0, t290)
  t295 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t115 * t286 + 0.4e1 / 0.3e1 * t19 * t291)
  t302 = f.my_piecewise3(t1, 0, -0.27e2 / 0.80e2 * t3 * t295 * t31 * t47 - 0.9e1 / 0.40e2 * t241 + t146)
  t303 = t203 ** 2
  t307 = f.my_piecewise5(t12, 0, t8, 0, -t290)
  t311 = f.my_piecewise3(t81, 0, 0.4e1 / 0.9e1 * t166 * t303 + 0.4e1 / 0.3e1 * t82 * t307)
  t335 = f.my_piecewise3(t78, 0, -0.27e2 / 0.80e2 * t3 * t311 * t90 * t101 - 0.9e1 / 0.40e2 * t266 - 0.9e1 / 0.8e1 * t208 * t213 + 0.7e1 / 0.320e3 * t207 * t218 * t222 + t186 - 0.3e1 / 0.8e1 * t271 + 0.7e1 / 0.960e3 * t278 - 0.3e1 / 0.8e1 * t211 * t220 * t99 * t46 + 0.7e1 / 0.480e3 * t219 / t92 / r1 * s2 * t46)
  d22 = 0.2e1 * t201 + 0.2e1 * t226 + t4 * (t302 + t335)
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
  t2 = jnp.pi ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = r0 + r1
  t5 = 0.1e1 / t4
  t8 = 0.2e1 * r0 * t5 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t12 = 0.2e1 * r1 * t5 <= f.p.zeta_threshold
  t13 = -t9
  t14 = r0 - r1
  t15 = t14 * t5
  t16 = f.my_piecewise5(t8, t9, t12, t13, t15)
  t17 = 0.1e1 + t16
  t18 = t17 <= f.p.zeta_threshold
  t19 = t17 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t22 = t4 ** 2
  t23 = 0.1e1 / t22
  t25 = -t14 * t23 + t5
  t26 = f.my_piecewise5(t8, 0, t12, 0, t25)
  t27 = t26 ** 2
  t31 = 0.1e1 / t22 / t4
  t34 = 0.2e1 * t14 * t31 - 0.2e1 * t23
  t35 = f.my_piecewise5(t8, 0, t12, 0, t34)
  t39 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t21 * t27 + 0.4e1 / 0.3e1 * t19 * t35)
  t40 = t3 * t39
  t41 = t4 ** (0.1e1 / 0.3e1)
  t42 = 0.1e1 / tau0
  t43 = t41 * t42
  t44 = t40 * t43
  t45 = r0 ** (0.1e1 / 0.3e1)
  t46 = t45 ** 2
  t52 = 0.1e1 + 0.7e1 / 0.216e3 * s0 / r0 * t42
  t55 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t57 = 4 ** (0.1e1 / 0.3e1)
  t58 = 0.1e1 / t55 * t57
  t59 = t46 * r0 * t52 * t58
  t64 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t19 * t26)
  t65 = t3 * t64
  t66 = t41 ** 2
  t67 = 0.1e1 / t66
  t68 = t67 * t42
  t69 = t65 * t68
  t72 = t65 * t43
  t74 = t46 * t52 * t58
  t77 = tau0 ** 2
  t78 = 0.1e1 / t77
  t79 = t41 * t78
  t80 = t65 * t79
  t81 = 0.1e1 / t45
  t83 = t81 * s0 * t58
  t86 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t87 = t86 * f.p.zeta_threshold
  t89 = f.my_piecewise3(t18, t87, t19 * t17)
  t90 = t3 * t89
  t92 = 0.1e1 / t66 / t4
  t93 = t92 * t42
  t94 = t90 * t93
  t97 = t90 * t68
  t100 = t67 * t78
  t101 = t90 * t100
  t104 = t90 * t43
  t106 = t81 * t52 * t58
  t109 = t90 * t79
  t111 = 0.1e1 / t45 / r0
  t113 = t111 * s0 * t58
  t117 = f.my_piecewise3(t1, 0, -0.27e2 / 0.80e2 * t44 * t59 - 0.9e1 / 0.40e2 * t69 * t59 - 0.9e1 / 0.8e1 * t72 * t74 + 0.7e1 / 0.320e3 * t80 * t83 + 0.3e1 / 0.40e2 * t94 * t59 - 0.3e1 / 0.8e1 * t97 * t74 + 0.7e1 / 0.960e3 * t101 * t83 - 0.3e1 / 0.8e1 * t104 * t106 + 0.7e1 / 0.480e3 * t109 * t113)
  t119 = r1 <= f.p.dens_threshold
  t120 = f.my_piecewise5(t12, t9, t8, t13, -t15)
  t121 = 0.1e1 + t120
  t122 = t121 <= f.p.zeta_threshold
  t123 = t121 ** (0.1e1 / 0.3e1)
  t124 = t123 ** 2
  t125 = 0.1e1 / t124
  t127 = f.my_piecewise5(t12, 0, t8, 0, -t25)
  t128 = t127 ** 2
  t132 = f.my_piecewise5(t12, 0, t8, 0, -t34)
  t136 = f.my_piecewise3(t122, 0, 0.4e1 / 0.9e1 * t125 * t128 + 0.4e1 / 0.3e1 * t123 * t132)
  t137 = t3 * t136
  t138 = 0.1e1 / tau1
  t139 = t41 * t138
  t141 = r1 ** (0.1e1 / 0.3e1)
  t142 = t141 ** 2
  t150 = t142 * r1 * (0.1e1 + 0.7e1 / 0.216e3 * s2 / r1 * t138) * t58
  t155 = f.my_piecewise3(t122, 0, 0.4e1 / 0.3e1 * t123 * t127)
  t156 = t3 * t155
  t157 = t67 * t138
  t162 = f.my_piecewise3(t122, t87, t123 * t121)
  t163 = t3 * t162
  t164 = t92 * t138
  t169 = f.my_piecewise3(t119, 0, -0.27e2 / 0.80e2 * t137 * t139 * t150 - 0.9e1 / 0.40e2 * t156 * t157 * t150 + 0.3e1 / 0.40e2 * t163 * t164 * t150)
  t177 = r0 ** 2
  t192 = t22 ** 2
  t196 = 0.6e1 * t31 - 0.6e1 * t14 / t192
  t197 = f.my_piecewise5(t8, 0, t12, 0, t196)
  t201 = f.my_piecewise3(t18, 0, -0.8e1 / 0.27e2 / t20 / t17 * t27 * t26 + 0.4e1 / 0.3e1 * t21 * t26 * t35 + 0.4e1 / 0.3e1 * t19 * t197)
  t227 = 0.1e1 / t66 / t22
  t240 = -0.7e1 / 0.960e3 * t90 * t92 * t78 * t83 + 0.7e1 / 0.480e3 * t101 * t113 - 0.7e1 / 0.960e3 * t109 / t45 / t177 * s0 * t58 - 0.27e2 / 0.80e2 * t3 * t201 * t43 * t59 + 0.21e2 / 0.640e3 * t40 * t79 * t83 + 0.7e1 / 0.320e3 * t65 * t100 * t83 + 0.7e1 / 0.160e3 * t80 * t113 - 0.27e2 / 0.80e2 * t40 * t68 * t59 - 0.27e2 / 0.16e2 * t44 * t74 + 0.9e1 / 0.40e2 * t65 * t93 * t59 - 0.9e1 / 0.8e1 * t69 * t74 - 0.9e1 / 0.8e1 * t72 * t106 - t90 * t227 * t42 * t59 / 0.8e1 + 0.3e1 / 0.8e1 * t94 * t74 - 0.3e1 / 0.8e1 * t97 * t106 + t104 * t111 * t52 * t58 / 0.8e1
  t241 = f.my_piecewise3(t1, 0, t240)
  t251 = f.my_piecewise5(t12, 0, t8, 0, -t196)
  t255 = f.my_piecewise3(t122, 0, -0.8e1 / 0.27e2 / t124 / t121 * t128 * t127 + 0.4e1 / 0.3e1 * t125 * t127 * t132 + 0.4e1 / 0.3e1 * t123 * t251)
  t271 = f.my_piecewise3(t119, 0, -0.27e2 / 0.80e2 * t3 * t255 * t139 * t150 - 0.27e2 / 0.80e2 * t137 * t157 * t150 + 0.9e1 / 0.40e2 * t156 * t164 * t150 - t163 * t227 * t138 * t150 / 0.8e1)
  d111 = 0.3e1 * t117 + 0.3e1 * t169 + t4 * (t241 + t271)

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
  t2 = jnp.pi ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = r0 + r1
  t5 = 0.1e1 / t4
  t8 = 0.2e1 * r0 * t5 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t12 = 0.2e1 * r1 * t5 <= f.p.zeta_threshold
  t13 = -t9
  t14 = r0 - r1
  t15 = t14 * t5
  t16 = f.my_piecewise5(t8, t9, t12, t13, t15)
  t17 = 0.1e1 + t16
  t18 = t17 <= f.p.zeta_threshold
  t19 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t20 = t19 * f.p.zeta_threshold
  t21 = t17 ** (0.1e1 / 0.3e1)
  t23 = f.my_piecewise3(t18, t20, t21 * t17)
  t24 = t3 * t23
  t25 = t4 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = 0.1e1 / t26 / t4
  t29 = tau0 ** 2
  t30 = 0.1e1 / t29
  t31 = t28 * t30
  t32 = t24 * t31
  t33 = r0 ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t33
  t37 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t39 = 4 ** (0.1e1 / 0.3e1)
  t40 = 0.1e1 / t37 * t39
  t41 = t34 * s0 * t40
  t44 = 0.1e1 / t26
  t45 = t44 * t30
  t46 = t24 * t45
  t48 = 0.1e1 / t33 / r0
  t50 = t48 * s0 * t40
  t53 = t25 * t30
  t54 = t24 * t53
  t55 = r0 ** 2
  t57 = 0.1e1 / t33 / t55
  t59 = t57 * s0 * t40
  t62 = t21 ** 2
  t64 = 0.1e1 / t62 / t17
  t65 = t4 ** 2
  t66 = 0.1e1 / t65
  t68 = -t14 * t66 + t5
  t69 = f.my_piecewise5(t8, 0, t12, 0, t68)
  t70 = t69 ** 2
  t74 = 0.1e1 / t62
  t75 = t74 * t69
  t76 = t65 * t4
  t77 = 0.1e1 / t76
  t80 = 0.2e1 * t14 * t77 - 0.2e1 * t66
  t81 = f.my_piecewise5(t8, 0, t12, 0, t80)
  t84 = t65 ** 2
  t85 = 0.1e1 / t84
  t88 = -0.6e1 * t14 * t85 + 0.6e1 * t77
  t89 = f.my_piecewise5(t8, 0, t12, 0, t88)
  t93 = f.my_piecewise3(t18, 0, -0.8e1 / 0.27e2 * t64 * t70 * t69 + 0.4e1 / 0.3e1 * t75 * t81 + 0.4e1 / 0.3e1 * t21 * t89)
  t94 = t3 * t93
  t95 = 0.1e1 / tau0
  t96 = t25 * t95
  t97 = t94 * t96
  t98 = t33 ** 2
  t104 = 0.1e1 + 0.7e1 / 0.216e3 * s0 / r0 * t95
  t106 = t98 * r0 * t104 * t40
  t114 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t74 * t70 + 0.4e1 / 0.3e1 * t21 * t81)
  t115 = t3 * t114
  t116 = t115 * t53
  t121 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t21 * t69)
  t122 = t3 * t121
  t123 = t122 * t45
  t126 = t122 * t53
  t129 = t44 * t95
  t130 = t115 * t129
  t133 = t115 * t96
  t135 = t98 * t104 * t40
  t138 = t28 * t95
  t139 = t122 * t138
  t142 = t122 * t129
  t145 = t122 * t96
  t147 = t34 * t104 * t40
  t151 = 0.1e1 / t26 / t65
  t152 = t151 * t95
  t153 = t24 * t152
  t156 = t24 * t138
  t159 = t24 * t129
  t162 = t24 * t96
  t164 = t48 * t104 * t40
  t167 = -0.7e1 / 0.960e3 * t32 * t41 + 0.7e1 / 0.480e3 * t46 * t50 - 0.7e1 / 0.960e3 * t54 * t59 - 0.27e2 / 0.80e2 * t97 * t106 + 0.21e2 / 0.640e3 * t116 * t41 + 0.7e1 / 0.320e3 * t123 * t41 + 0.7e1 / 0.160e3 * t126 * t50 - 0.27e2 / 0.80e2 * t130 * t106 - 0.27e2 / 0.16e2 * t133 * t135 + 0.9e1 / 0.40e2 * t139 * t106 - 0.9e1 / 0.8e1 * t142 * t135 - 0.9e1 / 0.8e1 * t145 * t147 - t153 * t106 / 0.8e1 + 0.3e1 / 0.8e1 * t156 * t135 - 0.3e1 / 0.8e1 * t159 * t147 + t162 * t164 / 0.8e1
  t168 = f.my_piecewise3(t1, 0, t167)
  t170 = r1 <= f.p.dens_threshold
  t171 = f.my_piecewise5(t12, t9, t8, t13, -t15)
  t172 = 0.1e1 + t171
  t173 = t172 <= f.p.zeta_threshold
  t174 = t172 ** (0.1e1 / 0.3e1)
  t175 = t174 ** 2
  t177 = 0.1e1 / t175 / t172
  t179 = f.my_piecewise5(t12, 0, t8, 0, -t68)
  t180 = t179 ** 2
  t184 = 0.1e1 / t175
  t185 = t184 * t179
  t187 = f.my_piecewise5(t12, 0, t8, 0, -t80)
  t191 = f.my_piecewise5(t12, 0, t8, 0, -t88)
  t195 = f.my_piecewise3(t173, 0, -0.8e1 / 0.27e2 * t177 * t180 * t179 + 0.4e1 / 0.3e1 * t185 * t187 + 0.4e1 / 0.3e1 * t174 * t191)
  t196 = t3 * t195
  t197 = 0.1e1 / tau1
  t198 = t25 * t197
  t200 = r1 ** (0.1e1 / 0.3e1)
  t201 = t200 ** 2
  t209 = t201 * r1 * (0.1e1 + 0.7e1 / 0.216e3 * s2 / r1 * t197) * t40
  t217 = f.my_piecewise3(t173, 0, 0.4e1 / 0.9e1 * t184 * t180 + 0.4e1 / 0.3e1 * t174 * t187)
  t218 = t3 * t217
  t219 = t44 * t197
  t225 = f.my_piecewise3(t173, 0, 0.4e1 / 0.3e1 * t174 * t179)
  t226 = t3 * t225
  t227 = t28 * t197
  t232 = f.my_piecewise3(t173, t20, t174 * t172)
  t233 = t3 * t232
  t234 = t151 * t197
  t239 = f.my_piecewise3(t170, 0, -0.27e2 / 0.80e2 * t196 * t198 * t209 - 0.27e2 / 0.80e2 * t218 * t219 * t209 + 0.9e1 / 0.40e2 * t226 * t227 * t209 - t233 * t234 * t209 / 0.8e1)
  t253 = 0.1e1 / t26 / t76
  t273 = -0.9e1 / 0.4e1 * t133 * t147 - t122 * t152 * t106 / 0.2e1 + 0.3e1 / 0.2e1 * t139 * t135 - 0.3e1 / 0.2e1 * t142 * t147 + t145 * t164 / 0.2e1 + t24 * t253 * t95 * t106 / 0.3e1 - 0.5e1 / 0.6e1 * t153 * t135 + t156 * t147 / 0.2e1 + t159 * t164 / 0.6e1 - t162 * t57 * t104 * t40 / 0.6e1 - 0.7e1 / 0.240e3 * t122 * t31 * t41 + 0.7e1 / 0.120e3 * t123 * t50
  t276 = t17 ** 2
  t279 = t70 ** 2
  t285 = t81 ** 2
  t294 = -0.24e2 * t85 + 0.24e2 * t14 / t84 / t4
  t295 = f.my_piecewise5(t8, 0, t12, 0, t294)
  t299 = f.my_piecewise3(t18, 0, 0.40e2 / 0.81e2 / t62 / t276 * t279 - 0.16e2 / 0.9e1 * t64 * t70 * t81 + 0.4e1 / 0.3e1 * t74 * t285 + 0.16e2 / 0.9e1 * t75 * t89 + 0.4e1 / 0.3e1 * t21 * t295)
  t337 = -0.7e1 / 0.240e3 * t126 * t59 - 0.27e2 / 0.80e2 * t3 * t299 * t96 * t106 + 0.7e1 / 0.160e3 * t94 * t53 * t41 + 0.7e1 / 0.432e3 * t24 * t151 * t30 * t41 - 0.7e1 / 0.360e3 * t32 * t50 - 0.7e1 / 0.720e3 * t46 * t59 + 0.7e1 / 0.540e3 * t54 / t33 / t55 / r0 * s0 * t40 - 0.9e1 / 0.20e2 * t94 * t129 * t106 - 0.9e1 / 0.4e1 * t97 * t135 + 0.7e1 / 0.160e3 * t115 * t45 * t41 + 0.7e1 / 0.80e2 * t116 * t50 + 0.9e1 / 0.20e2 * t115 * t138 * t106 - 0.9e1 / 0.4e1 * t130 * t135
  t339 = f.my_piecewise3(t1, 0, t273 + t337)
  t340 = t172 ** 2
  t343 = t180 ** 2
  t349 = t187 ** 2
  t355 = f.my_piecewise5(t12, 0, t8, 0, -t294)
  t359 = f.my_piecewise3(t173, 0, 0.40e2 / 0.81e2 / t175 / t340 * t343 - 0.16e2 / 0.9e1 * t177 * t180 * t187 + 0.4e1 / 0.3e1 * t184 * t349 + 0.16e2 / 0.9e1 * t185 * t191 + 0.4e1 / 0.3e1 * t174 * t355)
  t378 = f.my_piecewise3(t170, 0, -0.27e2 / 0.80e2 * t3 * t359 * t198 * t209 - 0.9e1 / 0.20e2 * t196 * t219 * t209 + 0.9e1 / 0.20e2 * t218 * t227 * t209 - t226 * t234 * t209 / 0.2e1 + t233 * t253 * t197 * t209 / 0.3e1)
  d1111 = 0.4e1 * t168 + 0.4e1 * t239 + t4 * (t339 + t378)

  res = {'v4rho4': d1111}
  return res
