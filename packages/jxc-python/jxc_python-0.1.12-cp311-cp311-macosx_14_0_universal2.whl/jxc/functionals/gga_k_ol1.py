"""Generated from gga_k_ol1.mpl."""

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
  ol1_f = lambda x: 1 + (x ** 2 / 72 + 0.00677 * 2 ** (1 / 3) * x) / K_FACTOR_C

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, ol1_f, rs, zeta, xs0, xs1)

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
  ol1_f = lambda x: 1 + (x ** 2 / 72 + 0.00677 * 2 ** (1 / 3) * x) / K_FACTOR_C

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, ol1_f, rs, zeta, xs0, xs1)

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
  ol1_f = lambda x: 1 + (x ** 2 / 72 + 0.00677 * 2 ** (1 / 3) * x) / K_FACTOR_C

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, ol1_f, rs, zeta, xs0, xs1)

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
  t32 = r0 ** 2
  t33 = r0 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t36 = 0.1e1 / t34 / t32
  t39 = 2 ** (0.1e1 / 0.3e1)
  t40 = jnp.sqrt(s0)
  t41 = t39 * t40
  t43 = 0.1e1 / t33 / r0
  t47 = 6 ** (0.1e1 / 0.3e1)
  t49 = jnp.pi ** 2
  t50 = t49 ** (0.1e1 / 0.3e1)
  t51 = t50 ** 2
  t52 = 0.1e1 / t51
  t55 = 0.1e1 + 0.5e1 / 0.9e1 * (s0 * t36 / 0.72e2 + 0.677e-2 * t41 * t43) * t47 * t52
  t59 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t28 * t30 * t55)
  t60 = r1 <= f.p.dens_threshold
  t61 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t62 = 0.1e1 + t61
  t63 = t62 <= f.p.zeta_threshold
  t64 = t62 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t67 = f.my_piecewise3(t63, t24, t65 * t62)
  t69 = r1 ** 2
  t70 = r1 ** (0.1e1 / 0.3e1)
  t71 = t70 ** 2
  t73 = 0.1e1 / t71 / t69
  t76 = jnp.sqrt(s2)
  t77 = t39 * t76
  t79 = 0.1e1 / t70 / r1
  t86 = 0.1e1 + 0.5e1 / 0.9e1 * (s2 * t73 / 0.72e2 + 0.677e-2 * t77 * t79) * t47 * t52
  t90 = f.my_piecewise3(t60, 0, 0.3e1 / 0.20e2 * t6 * t67 * t30 * t86)
  t91 = t7 ** 2
  t93 = t17 / t91
  t94 = t8 - t93
  t95 = f.my_piecewise5(t11, 0, t15, 0, t94)
  t98 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t95)
  t103 = 0.1e1 / t29
  t107 = t6 * t28 * t103 * t55 / 0.10e2
  t108 = t6 * t28
  t120 = t47 * t52
  t125 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t98 * t30 * t55 + t107 + t108 * t30 * (-s0 / t34 / t32 / r0 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t41 / t33 / t32) * t120 / 0.12e2)
  t127 = f.my_piecewise5(t15, 0, t11, 0, -t94)
  t130 = f.my_piecewise3(t63, 0, 0.5e1 / 0.3e1 * t65 * t127)
  t138 = t6 * t67 * t103 * t86 / 0.10e2
  t140 = f.my_piecewise3(t60, 0, 0.3e1 / 0.20e2 * t6 * t130 * t30 * t86 + t138)
  vrho_0_ = t59 + t90 + t7 * (t125 + t140)
  t143 = -t8 - t93
  t144 = f.my_piecewise5(t11, 0, t15, 0, t143)
  t147 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t144)
  t153 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t147 * t30 * t55 + t107)
  t155 = f.my_piecewise5(t15, 0, t11, 0, -t143)
  t158 = f.my_piecewise3(t63, 0, 0.5e1 / 0.3e1 * t65 * t155)
  t163 = t6 * t67
  t179 = f.my_piecewise3(t60, 0, 0.3e1 / 0.20e2 * t6 * t158 * t30 * t86 + t138 + t163 * t30 * (-s2 / t71 / t69 / r1 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t77 / t70 / t69) * t120 / 0.12e2)
  vrho_1_ = t59 + t90 + t7 * (t153 + t179)
  t192 = f.my_piecewise3(t1, 0, t108 * t30 * (t36 / 0.72e2 + 0.33850000000000000000000000000000000000000000000000e-2 * t39 / t40 * t43) * t120 / 0.12e2)
  vsigma_0_ = t7 * t192
  vsigma_1_ = 0.0e0
  t203 = f.my_piecewise3(t60, 0, t163 * t30 * (t73 / 0.72e2 + 0.33850000000000000000000000000000000000000000000000e-2 * t39 / t76 * t79) * t120 / 0.12e2)
  vsigma_2_ = t7 * t203
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
  ol1_f = lambda x: 1 + (x ** 2 / 72 + 0.00677 * 2 ** (1 / 3) * x) / K_FACTOR_C

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, ol1_f, rs, zeta, xs0, xs1)

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
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = s0 * t25
  t27 = r0 ** 2
  t29 = 0.1e1 / t22 / t27
  t32 = jnp.sqrt(s0)
  t33 = t25 * t32
  t35 = 0.1e1 / t21 / r0
  t39 = 6 ** (0.1e1 / 0.3e1)
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t47 = 0.1e1 + 0.5e1 / 0.9e1 * (t26 * t29 / 0.72e2 + 0.677e-2 * t33 * t35) * t39 * t44
  t51 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t20 * t22 * t47)
  t57 = t7 * t20
  t69 = t39 * t44
  t74 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t47 / 0.10e2 + t57 * t22 * (-t26 / t22 / t27 / r0 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t33 / t21 / t27) * t69 / 0.12e2)
  vrho_0_ = 0.2e1 * r0 * t74 + 0.2e1 * t51
  t88 = f.my_piecewise3(t2, 0, t57 * t22 * (t25 * t29 / 0.72e2 + 0.33850000000000000000000000000000000000000000000000e-2 * t25 / t32 * t35) * t69 / 0.12e2)
  vsigma_0_ = 0.2e1 * r0 * t88
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
  t22 = 0.1e1 / t21
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = s0 * t25
  t27 = r0 ** 2
  t28 = t21 ** 2
  t30 = 0.1e1 / t28 / t27
  t33 = jnp.sqrt(s0)
  t34 = t25 * t33
  t36 = 0.1e1 / t21 / r0
  t40 = 6 ** (0.1e1 / 0.3e1)
  t42 = jnp.pi ** 2
  t43 = t42 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t48 = 0.1e1 + 0.5e1 / 0.9e1 * (t26 * t30 / 0.72e2 + 0.677e-2 * t34 * t36) * t40 * t45
  t52 = t7 * t20
  t53 = t27 * r0
  t55 = 0.1e1 / t28 / t53
  t59 = 0.1e1 / t21 / t27
  t62 = -t26 * t55 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t34 * t59
  t64 = t40 * t45
  t69 = f.my_piecewise3(t2, 0, t7 * t20 * t22 * t48 / 0.10e2 + t52 * t28 * t62 * t64 / 0.12e2)
  t79 = t27 ** 2
  t94 = f.my_piecewise3(t2, 0, -t7 * t20 * t36 * t48 / 0.30e2 + t52 * t22 * t62 * t64 / 0.9e1 + t52 * t28 * (0.11e2 / 0.81e2 * t26 / t28 / t79 + 0.21062222222222222222222222222222222222222222222222e-1 * t34 / t21 / t53) * t64 / 0.12e2)
  v2rho2_0_ = 0.2e1 * r0 * t94 + 0.4e1 * t69
  t100 = t25 / t33
  t103 = t25 * t30 / 0.72e2 + 0.33850000000000000000000000000000000000000000000000e-2 * t100 * t36
  t108 = f.my_piecewise3(t2, 0, t52 * t28 * t103 * t64 / 0.12e2)
  t123 = f.my_piecewise3(t2, 0, t52 * t22 * t103 * t64 / 0.18e2 + t52 * t28 * (-t25 * t55 / 0.27e2 - 0.45133333333333333333333333333333333333333333333333e-2 * t100 * t59) * t64 / 0.12e2)
  v2rhosigma_0_ = 0.2e1 * r0 * t123 + 0.2e1 * t108
  t135 = f.my_piecewise3(t2, 0, -0.14104166666666666666666666666666666666666666666667e-3 * t7 * t20 / t28 * t25 / t33 / s0 * t64)
  v2sigma2_0_ = 0.2e1 * r0 * t135
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
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = s0 * t26
  t28 = r0 ** 2
  t29 = t21 ** 2
  t34 = jnp.sqrt(s0)
  t35 = t26 * t34
  t39 = 6 ** (0.1e1 / 0.3e1)
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t47 = 0.1e1 + 0.5e1 / 0.9e1 * (t27 / t29 / t28 / 0.72e2 + 0.677e-2 * t35 * t23) * t39 * t44
  t51 = t7 * t20
  t52 = 0.1e1 / t21
  t53 = t28 * r0
  t59 = 0.1e1 / t21 / t28
  t62 = -t27 / t29 / t53 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t35 * t59
  t64 = t39 * t44
  t68 = t28 ** 2
  t77 = 0.11e2 / 0.81e2 * t27 / t29 / t68 + 0.21062222222222222222222222222222222222222222222222e-1 * t35 / t21 / t53
  t83 = f.my_piecewise3(t2, 0, -t7 * t20 * t23 * t47 / 0.30e2 + t51 * t52 * t62 * t64 / 0.9e1 + t51 * t29 * t77 * t64 / 0.12e2)
  t112 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t59 * t47 - t51 * t23 * t62 * t64 / 0.18e2 + t51 * t52 * t77 * t64 / 0.6e1 + t51 * t29 * (-0.154e3 / 0.243e3 * t27 / t29 / t68 / r0 - 0.70207407407407407407407407407407407407407407407407e-1 * t35 / t21 / t68) * t64 / 0.12e2)
  v3rho3_0_ = 0.2e1 * r0 * t112 + 0.6e1 * t83

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
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = s0 * t27
  t29 = t22 ** 2
  t34 = jnp.sqrt(s0)
  t35 = t27 * t34
  t37 = 0.1e1 / t22 / r0
  t41 = 6 ** (0.1e1 / 0.3e1)
  t43 = jnp.pi ** 2
  t44 = t43 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t46 = 0.1e1 / t45
  t49 = 0.1e1 + 0.5e1 / 0.9e1 * (t28 / t29 / t21 / 0.72e2 + 0.677e-2 * t35 * t37) * t41 * t46
  t53 = t7 * t20
  t54 = t21 * r0
  t61 = -t28 / t29 / t54 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t35 * t24
  t63 = t41 * t46
  t67 = 0.1e1 / t22
  t68 = t21 ** 2
  t74 = 0.1e1 / t22 / t54
  t77 = 0.11e2 / 0.81e2 * t28 / t29 / t68 + 0.21062222222222222222222222222222222222222222222222e-1 * t35 * t74
  t82 = t68 * r0
  t91 = -0.154e3 / 0.243e3 * t28 / t29 / t82 - 0.70207407407407407407407407407407407407407407407407e-1 * t35 / t22 / t68
  t97 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t24 * t49 - t53 * t37 * t61 * t63 / 0.18e2 + t53 * t67 * t77 * t63 / 0.6e1 + t53 * t29 * t91 * t63 / 0.12e2)
  t130 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t74 * t49 + 0.8e1 / 0.81e2 * t53 * t24 * t61 * t63 - t53 * t37 * t77 * t63 / 0.9e1 + 0.2e1 / 0.9e1 * t53 * t67 * t91 * t63 + t53 * t29 * (0.2618e4 / 0.729e3 * t28 / t29 / t68 / t21 + 0.30423209876543209876543209876543209876543209876543e0 * t35 / t22 / t82) * t63 / 0.12e2)
  v4rho4_0_ = 0.2e1 * r0 * t130 + 0.8e1 * t97

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
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t42 = 2 ** (0.1e1 / 0.3e1)
  t43 = jnp.sqrt(s0)
  t44 = t42 * t43
  t50 = 6 ** (0.1e1 / 0.3e1)
  t52 = jnp.pi ** 2
  t53 = t52 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t55 = 0.1e1 / t54
  t58 = 0.1e1 + 0.5e1 / 0.9e1 * (s0 / t37 / t35 / 0.72e2 + 0.677e-2 * t44 / t36 / r0) * t50 * t55
  t62 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t63 = t62 ** 2
  t64 = t63 * f.p.zeta_threshold
  t66 = f.my_piecewise3(t21, t64, t23 * t20)
  t67 = 0.1e1 / t32
  t71 = t6 * t66 * t67 * t58 / 0.10e2
  t72 = t6 * t66
  t73 = t35 * r0
  t82 = -s0 / t37 / t73 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t44 / t36 / t35
  t84 = t50 * t55
  t85 = t33 * t82 * t84
  t89 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t33 * t58 + t71 + t72 * t85 / 0.12e2)
  t91 = r1 <= f.p.dens_threshold
  t92 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t93 = 0.1e1 + t92
  t94 = t93 <= f.p.zeta_threshold
  t95 = t93 ** (0.1e1 / 0.3e1)
  t96 = t95 ** 2
  t98 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t101 = f.my_piecewise3(t94, 0, 0.5e1 / 0.3e1 * t96 * t98)
  t103 = r1 ** 2
  t104 = r1 ** (0.1e1 / 0.3e1)
  t105 = t104 ** 2
  t110 = jnp.sqrt(s2)
  t111 = t42 * t110
  t120 = 0.1e1 + 0.5e1 / 0.9e1 * (s2 / t105 / t103 / 0.72e2 + 0.677e-2 * t111 / t104 / r1) * t50 * t55
  t125 = f.my_piecewise3(t94, t64, t96 * t93)
  t129 = t6 * t125 * t67 * t120 / 0.10e2
  t131 = f.my_piecewise3(t91, 0, 0.3e1 / 0.20e2 * t6 * t101 * t33 * t120 + t129)
  t133 = 0.1e1 / t22
  t134 = t28 ** 2
  t139 = t17 / t24 / t7
  t141 = -0.2e1 * t25 + 0.2e1 * t139
  t142 = f.my_piecewise5(t11, 0, t15, 0, t141)
  t146 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t133 * t134 + 0.5e1 / 0.3e1 * t23 * t142)
  t153 = t6 * t31 * t67 * t58
  t159 = 0.1e1 / t32 / t7
  t163 = t6 * t66 * t159 * t58 / 0.30e2
  t166 = t72 * t67 * t82 * t84
  t168 = t35 ** 2
  t183 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t146 * t33 * t58 + t153 / 0.5e1 + t6 * t31 * t85 / 0.6e1 - t163 + t166 / 0.9e1 + t72 * t33 * (0.11e2 / 0.81e2 * s0 / t37 / t168 + 0.21062222222222222222222222222222222222222222222222e-1 * t44 / t36 / t73) * t84 / 0.12e2)
  t184 = 0.1e1 / t95
  t185 = t98 ** 2
  t189 = f.my_piecewise5(t15, 0, t11, 0, -t141)
  t193 = f.my_piecewise3(t94, 0, 0.10e2 / 0.9e1 * t184 * t185 + 0.5e1 / 0.3e1 * t96 * t189)
  t200 = t6 * t101 * t67 * t120
  t205 = t6 * t125 * t159 * t120 / 0.30e2
  t207 = f.my_piecewise3(t91, 0, 0.3e1 / 0.20e2 * t6 * t193 * t33 * t120 + t200 / 0.5e1 - t205)
  d11 = 0.2e1 * t89 + 0.2e1 * t131 + t7 * (t183 + t207)
  t210 = -t8 - t26
  t211 = f.my_piecewise5(t11, 0, t15, 0, t210)
  t214 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t211)
  t220 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t214 * t33 * t58 + t71)
  t222 = f.my_piecewise5(t15, 0, t11, 0, -t210)
  t225 = f.my_piecewise3(t94, 0, 0.5e1 / 0.3e1 * t96 * t222)
  t230 = t6 * t125
  t231 = t103 * r1
  t240 = -s2 / t105 / t231 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t111 / t104 / t103
  t242 = t33 * t240 * t84
  t246 = f.my_piecewise3(t91, 0, 0.3e1 / 0.20e2 * t6 * t225 * t33 * t120 + t129 + t230 * t242 / 0.12e2)
  t250 = 0.2e1 * t139
  t251 = f.my_piecewise5(t11, 0, t15, 0, t250)
  t255 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t133 * t211 * t28 + 0.5e1 / 0.3e1 * t23 * t251)
  t262 = t6 * t214 * t67 * t58
  t270 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t255 * t33 * t58 + t262 / 0.10e2 + t6 * t214 * t85 / 0.12e2 + t153 / 0.10e2 - t163 + t166 / 0.18e2)
  t274 = f.my_piecewise5(t15, 0, t11, 0, -t250)
  t278 = f.my_piecewise3(t94, 0, 0.10e2 / 0.9e1 * t184 * t222 * t98 + 0.5e1 / 0.3e1 * t96 * t274)
  t285 = t6 * t225 * t67 * t120
  t293 = t230 * t67 * t240 * t84
  t296 = f.my_piecewise3(t91, 0, 0.3e1 / 0.20e2 * t6 * t278 * t33 * t120 + t285 / 0.10e2 + t200 / 0.10e2 - t205 + t6 * t101 * t242 / 0.12e2 + t293 / 0.18e2)
  d12 = t89 + t131 + t220 + t246 + t7 * (t270 + t296)
  t301 = t211 ** 2
  t305 = 0.2e1 * t25 + 0.2e1 * t139
  t306 = f.my_piecewise5(t11, 0, t15, 0, t305)
  t310 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t133 * t301 + 0.5e1 / 0.3e1 * t23 * t306)
  t317 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t310 * t33 * t58 + t262 / 0.5e1 - t163)
  t318 = t222 ** 2
  t322 = f.my_piecewise5(t15, 0, t11, 0, -t305)
  t326 = f.my_piecewise3(t94, 0, 0.10e2 / 0.9e1 * t184 * t318 + 0.5e1 / 0.3e1 * t96 * t322)
  t336 = t103 ** 2
  t351 = f.my_piecewise3(t91, 0, 0.3e1 / 0.20e2 * t6 * t326 * t33 * t120 + t285 / 0.5e1 + t6 * t225 * t242 / 0.6e1 - t205 + t293 / 0.9e1 + t230 * t33 * (0.11e2 / 0.81e2 * s2 / t105 / t336 + 0.21062222222222222222222222222222222222222222222222e-1 * t111 / t104 / t231) * t84 / 0.12e2)
  d22 = 0.2e1 * t220 + 0.2e1 * t246 + t7 * (t317 + t351)
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
  t46 = r0 ** 2
  t47 = r0 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t53 = 2 ** (0.1e1 / 0.3e1)
  t54 = jnp.sqrt(s0)
  t55 = t53 * t54
  t61 = 6 ** (0.1e1 / 0.3e1)
  t63 = jnp.pi ** 2
  t64 = t63 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t66 = 0.1e1 / t65
  t69 = 0.1e1 + 0.5e1 / 0.9e1 * (s0 / t48 / t46 / 0.72e2 + 0.677e-2 * t55 / t47 / r0) * t61 * t66
  t75 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t76 = 0.1e1 / t43
  t81 = t6 * t75
  t82 = t46 * r0
  t91 = -s0 / t48 / t82 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t55 / t47 / t46
  t93 = t61 * t66
  t94 = t44 * t91 * t93
  t97 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t98 = t97 ** 2
  t99 = t98 * f.p.zeta_threshold
  t101 = f.my_piecewise3(t21, t99, t32 * t20)
  t103 = 0.1e1 / t43 / t7
  t108 = t6 * t101
  t110 = t76 * t91 * t93
  t113 = t46 ** 2
  t122 = 0.11e2 / 0.81e2 * s0 / t48 / t113 + 0.21062222222222222222222222222222222222222222222222e-1 * t55 / t47 / t82
  t124 = t44 * t122 * t93
  t128 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t42 * t44 * t69 + t6 * t75 * t76 * t69 / 0.5e1 + t81 * t94 / 0.6e1 - t6 * t101 * t103 * t69 / 0.30e2 + t108 * t110 / 0.9e1 + t108 * t124 / 0.12e2)
  t130 = r1 <= f.p.dens_threshold
  t131 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t132 = 0.1e1 + t131
  t133 = t132 <= f.p.zeta_threshold
  t134 = t132 ** (0.1e1 / 0.3e1)
  t135 = 0.1e1 / t134
  t137 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t138 = t137 ** 2
  t141 = t134 ** 2
  t143 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t147 = f.my_piecewise3(t133, 0, 0.10e2 / 0.9e1 * t135 * t138 + 0.5e1 / 0.3e1 * t141 * t143)
  t149 = r1 ** 2
  t150 = r1 ** (0.1e1 / 0.3e1)
  t151 = t150 ** 2
  t156 = jnp.sqrt(s2)
  t166 = 0.1e1 + 0.5e1 / 0.9e1 * (s2 / t151 / t149 / 0.72e2 + 0.677e-2 * t53 * t156 / t150 / r1) * t61 * t66
  t172 = f.my_piecewise3(t133, 0, 0.5e1 / 0.3e1 * t141 * t137)
  t178 = f.my_piecewise3(t133, t99, t141 * t132)
  t184 = f.my_piecewise3(t130, 0, 0.3e1 / 0.20e2 * t6 * t147 * t44 * t166 + t6 * t172 * t76 * t166 / 0.5e1 - t6 * t178 * t103 * t166 / 0.30e2)
  t194 = t24 ** 2
  t198 = 0.6e1 * t34 - 0.6e1 * t17 / t194
  t199 = f.my_piecewise5(t11, 0, t15, 0, t198)
  t203 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t199)
  t224 = 0.1e1 / t43 / t24
  t252 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t203 * t44 * t69 + 0.3e1 / 0.10e2 * t6 * t42 * t76 * t69 + t6 * t42 * t94 / 0.4e1 - t6 * t75 * t103 * t69 / 0.10e2 + t81 * t110 / 0.3e1 + t81 * t124 / 0.4e1 + 0.2e1 / 0.45e2 * t6 * t101 * t224 * t69 - t108 * t103 * t91 * t93 / 0.18e2 + t108 * t76 * t122 * t93 / 0.6e1 + t108 * t44 * (-0.154e3 / 0.243e3 * s0 / t48 / t113 / r0 - 0.70207407407407407407407407407407407407407407407407e-1 * t55 / t47 / t113) * t93 / 0.12e2)
  t262 = f.my_piecewise5(t15, 0, t11, 0, -t198)
  t266 = f.my_piecewise3(t133, 0, -0.10e2 / 0.27e2 / t134 / t132 * t138 * t137 + 0.10e2 / 0.3e1 * t135 * t137 * t143 + 0.5e1 / 0.3e1 * t141 * t262)
  t284 = f.my_piecewise3(t130, 0, 0.3e1 / 0.20e2 * t6 * t266 * t44 * t166 + 0.3e1 / 0.10e2 * t6 * t147 * t76 * t166 - t6 * t172 * t103 * t166 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t178 * t224 * t166)
  d111 = 0.3e1 * t128 + 0.3e1 * t184 + t7 * (t252 + t284)

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
  t58 = r0 ** 2
  t59 = r0 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t65 = 2 ** (0.1e1 / 0.3e1)
  t66 = jnp.sqrt(s0)
  t67 = t65 * t66
  t73 = 6 ** (0.1e1 / 0.3e1)
  t75 = jnp.pi ** 2
  t76 = t75 ** (0.1e1 / 0.3e1)
  t77 = t76 ** 2
  t78 = 0.1e1 / t77
  t81 = 0.1e1 + 0.5e1 / 0.9e1 * (s0 / t60 / t58 / 0.72e2 + 0.677e-2 * t67 / t59 / r0) * t73 * t78
  t90 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t91 = 0.1e1 / t55
  t96 = t6 * t90
  t97 = t58 * r0
  t106 = -s0 / t60 / t97 / 0.27e2 - 0.90266666666666666666666666666666666666666666666666e-2 * t67 / t59 / t58
  t108 = t73 * t78
  t109 = t56 * t106 * t108
  t114 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t116 = 0.1e1 / t55 / t7
  t121 = t6 * t114
  t123 = t91 * t106 * t108
  t126 = t58 ** 2
  t135 = 0.11e2 / 0.81e2 * s0 / t60 / t126 + 0.21062222222222222222222222222222222222222222222222e-1 * t67 / t59 / t97
  t137 = t56 * t135 * t108
  t140 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t141 = t140 ** 2
  t142 = t141 * f.p.zeta_threshold
  t144 = f.my_piecewise3(t21, t142, t44 * t20)
  t146 = 0.1e1 / t55 / t25
  t151 = t6 * t144
  t153 = t116 * t106 * t108
  t157 = t91 * t135 * t108
  t160 = t126 * r0
  t169 = -0.154e3 / 0.243e3 * s0 / t60 / t160 - 0.70207407407407407407407407407407407407407407407407e-1 * t67 / t59 / t126
  t171 = t56 * t169 * t108
  t175 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t54 * t56 * t81 + 0.3e1 / 0.10e2 * t6 * t90 * t91 * t81 + t96 * t109 / 0.4e1 - t6 * t114 * t116 * t81 / 0.10e2 + t121 * t123 / 0.3e1 + t121 * t137 / 0.4e1 + 0.2e1 / 0.45e2 * t6 * t144 * t146 * t81 - t151 * t153 / 0.18e2 + t151 * t157 / 0.6e1 + t151 * t171 / 0.12e2)
  t177 = r1 <= f.p.dens_threshold
  t178 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t179 = 0.1e1 + t178
  t180 = t179 <= f.p.zeta_threshold
  t181 = t179 ** (0.1e1 / 0.3e1)
  t183 = 0.1e1 / t181 / t179
  t185 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t186 = t185 ** 2
  t190 = 0.1e1 / t181
  t191 = t190 * t185
  t193 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t196 = t181 ** 2
  t198 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t202 = f.my_piecewise3(t180, 0, -0.10e2 / 0.27e2 * t183 * t186 * t185 + 0.10e2 / 0.3e1 * t191 * t193 + 0.5e1 / 0.3e1 * t196 * t198)
  t204 = r1 ** 2
  t205 = r1 ** (0.1e1 / 0.3e1)
  t206 = t205 ** 2
  t211 = jnp.sqrt(s2)
  t221 = 0.1e1 + 0.5e1 / 0.9e1 * (s2 / t206 / t204 / 0.72e2 + 0.677e-2 * t65 * t211 / t205 / r1) * t73 * t78
  t230 = f.my_piecewise3(t180, 0, 0.10e2 / 0.9e1 * t190 * t186 + 0.5e1 / 0.3e1 * t196 * t193)
  t237 = f.my_piecewise3(t180, 0, 0.5e1 / 0.3e1 * t196 * t185)
  t243 = f.my_piecewise3(t180, t142, t196 * t179)
  t249 = f.my_piecewise3(t177, 0, 0.3e1 / 0.20e2 * t6 * t202 * t56 * t221 + 0.3e1 / 0.10e2 * t6 * t230 * t91 * t221 - t6 * t237 * t116 * t221 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t243 * t146 * t221)
  t290 = t20 ** 2
  t293 = t30 ** 2
  t299 = t41 ** 2
  t308 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t309 = f.my_piecewise5(t11, 0, t15, 0, t308)
  t313 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t290 * t293 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t299 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t309)
  t331 = 0.1e1 / t55 / t36
  t336 = t96 * t137 / 0.2e1 - 0.2e1 / 0.9e1 * t121 * t153 + 0.2e1 / 0.3e1 * t121 * t157 + t121 * t171 / 0.3e1 + 0.8e1 / 0.81e2 * t151 * t146 * t106 * t108 - t151 * t116 * t135 * t108 / 0.9e1 + 0.2e1 / 0.9e1 * t151 * t91 * t169 * t108 + t151 * t56 * (0.2618e4 / 0.729e3 * s0 / t60 / t126 / t58 + 0.30423209876543209876543209876543209876543209876543e0 * t67 / t59 / t160) * t108 / 0.12e2 + t6 * t54 * t109 / 0.3e1 + 0.2e1 / 0.3e1 * t96 * t123 + 0.3e1 / 0.20e2 * t6 * t313 * t56 * t81 + 0.2e1 / 0.5e1 * t6 * t54 * t91 * t81 - t6 * t90 * t116 * t81 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t114 * t146 * t81 - 0.14e2 / 0.135e3 * t6 * t144 * t331 * t81
  t337 = f.my_piecewise3(t1, 0, t336)
  t338 = t179 ** 2
  t341 = t186 ** 2
  t347 = t193 ** 2
  t353 = f.my_piecewise5(t15, 0, t11, 0, -t308)
  t357 = f.my_piecewise3(t180, 0, 0.40e2 / 0.81e2 / t181 / t338 * t341 - 0.20e2 / 0.9e1 * t183 * t186 * t193 + 0.10e2 / 0.3e1 * t190 * t347 + 0.40e2 / 0.9e1 * t191 * t198 + 0.5e1 / 0.3e1 * t196 * t353)
  t379 = f.my_piecewise3(t177, 0, 0.3e1 / 0.20e2 * t6 * t357 * t56 * t221 + 0.2e1 / 0.5e1 * t6 * t202 * t91 * t221 - t6 * t230 * t116 * t221 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t237 * t146 * t221 - 0.14e2 / 0.135e3 * t6 * t243 * t331 * t221)
  d1111 = 0.4e1 * t175 + 0.4e1 * t249 + t7 * (t337 + t379)

  res = {'v4rho4': d1111}
  return res
