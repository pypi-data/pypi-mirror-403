"""Generated from gga_x_g96.mpl."""

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
  g96_c1 = 1 / 137

  f_g96 = lambda x: 1 + g96_c1 / X_FACTOR_C * x ** (3 / 2)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, f_g96, rs, z, xs0, xs1)

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
  g96_c1 = 1 / 137

  f_g96 = lambda x: 1 + g96_c1 / X_FACTOR_C * x ** (3 / 2)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, f_g96, rs, z, xs0, xs1)

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
  g96_c1 = 1 / 137

  f_g96 = lambda x: 1 + g96_c1 / X_FACTOR_C * x ** (3 / 2)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, f_g96, rs, z, xs0, xs1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
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
  t28 = t2 ** 2
  t30 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t31 = 0.1e1 / t30
  t32 = t28 * t31
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = jnp.sqrt(s0)
  t35 = r0 ** (0.1e1 / 0.3e1)
  t37 = 0.1e1 / t35 / r0
  t38 = t34 * t37
  t39 = jnp.sqrt(t38)
  t44 = 0.1e1 + 0.2e1 / 0.1233e4 * t32 * t33 * t39 * t38
  t48 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t44)
  t49 = r1 <= f.p.dens_threshold
  t50 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t51 = 0.1e1 + t50
  t52 = t51 <= f.p.zeta_threshold
  t53 = t51 ** (0.1e1 / 0.3e1)
  t55 = f.my_piecewise3(t52, t22, t53 * t51)
  t57 = jnp.sqrt(s2)
  t58 = r1 ** (0.1e1 / 0.3e1)
  t60 = 0.1e1 / t58 / r1
  t61 = t57 * t60
  t62 = jnp.sqrt(t61)
  t67 = 0.1e1 + 0.2e1 / 0.1233e4 * t32 * t33 * t62 * t61
  t71 = f.my_piecewise3(t49, 0, -0.3e1 / 0.8e1 * t5 * t55 * t26 * t67)
  t72 = t6 ** 2
  t74 = t16 / t72
  t75 = t7 - t74
  t76 = f.my_piecewise5(t10, 0, t14, 0, t75)
  t79 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t76)
  t84 = t26 ** 2
  t85 = 0.1e1 / t84
  t89 = t5 * t25 * t85 * t44 / 0.8e1
  t91 = t26 * t31
  t92 = t4 * t25 * t91
  t93 = t33 * t39
  t94 = r0 ** 2
  t102 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t79 * t26 * t44 - t89 + t92 * t93 * t34 / t35 / t94 / 0.274e3)
  t104 = f.my_piecewise5(t14, 0, t10, 0, -t75)
  t107 = f.my_piecewise3(t52, 0, 0.4e1 / 0.3e1 * t53 * t104)
  t115 = t5 * t55 * t85 * t67 / 0.8e1
  t117 = f.my_piecewise3(t49, 0, -0.3e1 / 0.8e1 * t5 * t107 * t26 * t67 - t115)
  vrho_0_ = t48 + t71 + t6 * (t102 + t117)
  t120 = -t7 - t74
  t121 = f.my_piecewise5(t10, 0, t14, 0, t120)
  t124 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t121)
  t130 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t124 * t26 * t44 - t89)
  t132 = f.my_piecewise5(t14, 0, t10, 0, -t120)
  t135 = f.my_piecewise3(t52, 0, 0.4e1 / 0.3e1 * t53 * t132)
  t141 = t4 * t55 * t91
  t142 = t33 * t62
  t143 = r1 ** 2
  t151 = f.my_piecewise3(t49, 0, -0.3e1 / 0.8e1 * t5 * t135 * t26 * t67 - t115 + t141 * t142 * t57 / t58 / t143 / 0.274e3)
  vrho_1_ = t48 + t71 + t6 * (t130 + t151)
  t159 = f.my_piecewise3(t1, 0, -0.3e1 / 0.2192e4 * t92 * t93 / t34 * t37)
  vsigma_0_ = t6 * t159
  vsigma_1_ = 0.0e0
  t165 = f.my_piecewise3(t49, 0, -0.3e1 / 0.2192e4 * t141 * t142 / t57 * t60)
  vsigma_2_ = t6 * t165
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
  g96_c1 = 1 / 137

  f_g96 = lambda x: 1 + g96_c1 / X_FACTOR_C * x ** (3 / 2)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, f_g96, rs, z, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t6 = t3 * t5
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t20 = t3 ** 2
  t22 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t23 = 0.1e1 / t22
  t25 = 4 ** (0.1e1 / 0.3e1)
  t26 = jnp.sqrt(s0)
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t26 * t27
  t31 = t28 / t18 / r0
  t32 = jnp.sqrt(t31)
  t37 = 0.1e1 + 0.2e1 / 0.1233e4 * t20 * t23 * t25 * t32 * t31
  t41 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t37)
  t42 = t18 ** 2
  t48 = t5 * t17
  t49 = r0 ** 2
  t53 = t25 * t32
  t58 = f.my_piecewise3(t2, 0, -t6 * t17 / t42 * t37 / 0.8e1 + t48 / t49 * t23 * t53 * t28 / 0.274e3)
  vrho_0_ = 0.2e1 * r0 * t58 + 0.2e1 * t41
  t69 = f.my_piecewise3(t2, 0, -0.3e1 / 0.2192e4 * t48 / r0 * t23 * t53 / t26 * t27)
  vsigma_0_ = 0.2e1 * r0 * t69
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
  t5 = 0.1e1 / t4
  t6 = t3 * t5
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t22 = t3 ** 2
  t24 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t25 = 0.1e1 / t24
  t27 = 4 ** (0.1e1 / 0.3e1)
  t28 = jnp.sqrt(s0)
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t28 * t29
  t33 = t30 / t18 / r0
  t34 = jnp.sqrt(t33)
  t39 = 0.1e1 + 0.2e1 / 0.1233e4 * t22 * t25 * t27 * t34 * t33
  t43 = t5 * t17
  t44 = r0 ** 2
  t47 = t43 / t44 * t25
  t48 = t27 * t34
  t49 = t48 * t30
  t53 = f.my_piecewise3(t2, 0, -t6 * t17 / t19 * t39 / 0.8e1 + t47 * t49 / 0.274e3)
  t61 = t44 * r0
  t67 = t44 ** 2
  t72 = 0.1e1 / t34
  t73 = t27 * t72
  t74 = t29 ** 2
  t80 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t39 / 0.12e2 - 0.5e1 / 0.822e3 * t43 / t61 * t25 * t49 - t43 / t18 / t67 * t25 * t73 * s0 * t74 / 0.411e3)
  v2rho2_0_ = 0.2e1 * r0 * t80 + 0.4e1 * t53
  t85 = t43 / r0 * t25
  t88 = t48 / t28 * t29
  t91 = f.my_piecewise3(t2, 0, -0.3e1 / 0.2192e4 * t85 * t88)
  t103 = f.my_piecewise3(t2, 0, 0.3e1 / 0.2192e4 * t47 * t88 + t43 / t18 / t61 * t25 * t27 * t72 * t74 / 0.1096e4)
  v2rhosigma_0_ = 0.2e1 * r0 * t103 + 0.2e1 * t91
  t122 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8768e4 * t43 / t18 / t44 * t25 * t73 / s0 * t74 + 0.3e1 / 0.4384e4 * t85 * t48 / t28 / s0 * t29)
  v2sigma2_0_ = 0.2e1 * r0 * t122
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t6 = t3 * t5
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t23 = t3 ** 2
  t25 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = jnp.sqrt(s0)
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t29 * t30
  t34 = t31 / t18 / r0
  t35 = jnp.sqrt(t34)
  t36 = t35 * t34
  t40 = 0.1e1 + 0.2e1 / 0.1233e4 * t23 * t26 * t28 * t36
  t44 = t5 * t17
  t45 = r0 ** 2
  t51 = t28 * t35 * t31
  t54 = t45 ** 2
  t61 = t30 ** 2
  t63 = t28 / t35 * s0 * t61
  t67 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t40 / 0.12e2 - 0.5e1 / 0.822e3 * t44 / t45 / r0 * t26 * t51 - t44 / t18 / t54 * t26 * t63 / 0.411e3)
  t99 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 / t19 / t45 * t40 + 0.43e2 / 0.2466e4 * t44 / t54 * t26 * t51 + 0.2e1 / 0.137e3 * t44 / t18 / t54 / r0 * t26 * t63 - 0.4e1 / 0.1233e4 * t44 / t19 / t54 / t45 * t26 * t28 / t36 * t29 * s0)
  v3rho3_0_ = 0.2e1 * r0 * t99 + 0.6e1 * t67

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t6 = t3 * t5
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
  t24 = t3 ** 2
  t26 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t26
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = jnp.sqrt(s0)
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t30 * t31
  t35 = t32 / t19 / r0
  t36 = jnp.sqrt(t35)
  t37 = t36 * t35
  t41 = 0.1e1 + 0.2e1 / 0.1233e4 * t24 * t27 * t29 * t37
  t45 = t5 * t17
  t46 = t18 ** 2
  t51 = t29 * t36 * t32
  t54 = t46 * r0
  t61 = t31 ** 2
  t62 = s0 * t61
  t63 = t29 / t36 * t62
  t66 = t46 * t18
  t74 = t27 * t29 / t37 * t30 * s0
  t78 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t41 + 0.43e2 / 0.2466e4 * t45 / t46 * t27 * t51 + 0.2e1 / 0.137e3 * t45 / t19 / t54 * t27 * t63 - 0.4e1 / 0.1233e4 * t45 / t20 / t66 * t74)
  t80 = t18 * r0
  t104 = t46 ** 2
  t113 = s0 ** 2
  t119 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 / t20 / t80 * t41 - 0.253e3 / 0.3699e4 * t45 / t54 * t27 * t51 - 0.331e3 / 0.3699e4 * t45 / t19 / t66 * t27 * t63 + 0.152e3 / 0.3699e4 * t45 / t20 / t46 / t80 * t74 - 0.8e1 / 0.1233e4 * t45 / t104 / r0 * t27 * t29 / t36 / t62 / t22 * t113 * t31)
  v4rho4_0_ = 0.2e1 * r0 * t119 + 0.8e1 * t78

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
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
  t32 = t2 ** 2
  t34 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t35 = 0.1e1 / t34
  t36 = t32 * t35
  t37 = 4 ** (0.1e1 / 0.3e1)
  t38 = jnp.sqrt(s0)
  t39 = r0 ** (0.1e1 / 0.3e1)
  t42 = t38 / t39 / r0
  t43 = jnp.sqrt(t42)
  t48 = 0.1e1 + 0.2e1 / 0.1233e4 * t36 * t37 * t43 * t42
  t52 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t53 = t52 * f.p.zeta_threshold
  t55 = f.my_piecewise3(t20, t53, t21 * t19)
  t56 = t30 ** 2
  t57 = 0.1e1 / t56
  t61 = t5 * t55 * t57 * t48 / 0.8e1
  t62 = t4 * t55
  t63 = t30 * t35
  t64 = t62 * t63
  t65 = t37 * t43
  t66 = r0 ** 2
  t70 = t65 * t38 / t39 / t66
  t74 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t48 - t61 + t64 * t70 / 0.274e3)
  t76 = r1 <= f.p.dens_threshold
  t77 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t78 = 0.1e1 + t77
  t79 = t78 <= f.p.zeta_threshold
  t80 = t78 ** (0.1e1 / 0.3e1)
  t82 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t85 = f.my_piecewise3(t79, 0, 0.4e1 / 0.3e1 * t80 * t82)
  t87 = jnp.sqrt(s2)
  t88 = r1 ** (0.1e1 / 0.3e1)
  t91 = t87 / t88 / r1
  t92 = jnp.sqrt(t91)
  t97 = 0.1e1 + 0.2e1 / 0.1233e4 * t36 * t37 * t92 * t91
  t102 = f.my_piecewise3(t79, t53, t80 * t78)
  t106 = t5 * t102 * t57 * t97 / 0.8e1
  t108 = f.my_piecewise3(t76, 0, -0.3e1 / 0.8e1 * t5 * t85 * t30 * t97 - t106)
  t110 = t21 ** 2
  t111 = 0.1e1 / t110
  t112 = t26 ** 2
  t117 = t16 / t22 / t6
  t119 = -0.2e1 * t23 + 0.2e1 * t117
  t120 = f.my_piecewise5(t10, 0, t14, 0, t119)
  t124 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t111 * t112 + 0.4e1 / 0.3e1 * t21 * t120)
  t131 = t5 * t29 * t57 * t48
  t138 = 0.1e1 / t56 / t6
  t142 = t5 * t55 * t138 * t48 / 0.12e2
  t143 = t57 * t35
  t145 = t62 * t143 * t70
  t149 = t66 ** 2
  t150 = t39 ** 2
  t165 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t124 * t30 * t48 - t131 / 0.4e1 + t4 * t29 * t63 * t70 / 0.137e3 + t142 + t145 / 0.411e3 - t64 * t37 / t43 * s0 / t150 / t149 / 0.411e3 - 0.7e1 / 0.822e3 * t64 * t65 * t38 / t39 / t66 / r0)
  t166 = t80 ** 2
  t167 = 0.1e1 / t166
  t168 = t82 ** 2
  t172 = f.my_piecewise5(t14, 0, t10, 0, -t119)
  t176 = f.my_piecewise3(t79, 0, 0.4e1 / 0.9e1 * t167 * t168 + 0.4e1 / 0.3e1 * t80 * t172)
  t183 = t5 * t85 * t57 * t97
  t188 = t5 * t102 * t138 * t97 / 0.12e2
  t190 = f.my_piecewise3(t76, 0, -0.3e1 / 0.8e1 * t5 * t176 * t30 * t97 - t183 / 0.4e1 + t188)
  d11 = 0.2e1 * t74 + 0.2e1 * t108 + t6 * (t165 + t190)
  t193 = -t7 - t24
  t194 = f.my_piecewise5(t10, 0, t14, 0, t193)
  t197 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t194)
  t203 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t197 * t30 * t48 - t61)
  t205 = f.my_piecewise5(t14, 0, t10, 0, -t193)
  t208 = f.my_piecewise3(t79, 0, 0.4e1 / 0.3e1 * t80 * t205)
  t213 = t4 * t102
  t214 = t213 * t63
  t215 = t37 * t92
  t216 = r1 ** 2
  t220 = t215 * t87 / t88 / t216
  t224 = f.my_piecewise3(t76, 0, -0.3e1 / 0.8e1 * t5 * t208 * t30 * t97 - t106 + t214 * t220 / 0.274e3)
  t228 = 0.2e1 * t117
  t229 = f.my_piecewise5(t10, 0, t14, 0, t228)
  t233 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t111 * t194 * t26 + 0.4e1 / 0.3e1 * t21 * t229)
  t240 = t5 * t197 * t57 * t48
  t249 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t233 * t30 * t48 - t240 / 0.8e1 + t4 * t197 * t63 * t70 / 0.274e3 - t131 / 0.8e1 + t142 + t145 / 0.822e3)
  t253 = f.my_piecewise5(t14, 0, t10, 0, -t228)
  t257 = f.my_piecewise3(t79, 0, 0.4e1 / 0.9e1 * t167 * t205 * t82 + 0.4e1 / 0.3e1 * t80 * t253)
  t264 = t5 * t208 * t57 * t97
  t272 = t213 * t143 * t220
  t275 = f.my_piecewise3(t76, 0, -0.3e1 / 0.8e1 * t5 * t257 * t30 * t97 - t264 / 0.8e1 - t183 / 0.8e1 + t188 + t4 * t85 * t63 * t220 / 0.274e3 + t272 / 0.822e3)
  d12 = t74 + t108 + t203 + t224 + t6 * (t249 + t275)
  t280 = t194 ** 2
  t284 = 0.2e1 * t23 + 0.2e1 * t117
  t285 = f.my_piecewise5(t10, 0, t14, 0, t284)
  t289 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t111 * t280 + 0.4e1 / 0.3e1 * t21 * t285)
  t296 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t289 * t30 * t48 - t240 / 0.4e1 + t142)
  t297 = t205 ** 2
  t301 = f.my_piecewise5(t14, 0, t10, 0, -t284)
  t305 = f.my_piecewise3(t79, 0, 0.4e1 / 0.9e1 * t167 * t297 + 0.4e1 / 0.3e1 * t80 * t301)
  t318 = t216 ** 2
  t319 = t88 ** 2
  t334 = f.my_piecewise3(t76, 0, -0.3e1 / 0.8e1 * t5 * t305 * t30 * t97 - t264 / 0.4e1 + t4 * t208 * t63 * t220 / 0.137e3 + t188 + t272 / 0.411e3 - t214 * t37 / t92 * s2 / t319 / t318 / 0.411e3 - 0.7e1 / 0.822e3 * t214 * t215 * t87 / t88 / t216 / r1)
  d22 = 0.2e1 * t203 + 0.2e1 * t224 + t6 * (t296 + t334)
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
  t4 = 0.1e1 / t3
  t5 = t2 * t4
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
  t44 = t2 ** 2
  t46 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t47 = 0.1e1 / t46
  t48 = t44 * t47
  t49 = 4 ** (0.1e1 / 0.3e1)
  t50 = jnp.sqrt(s0)
  t51 = r0 ** (0.1e1 / 0.3e1)
  t54 = t50 / t51 / r0
  t55 = jnp.sqrt(t54)
  t56 = t55 * t54
  t60 = 0.1e1 + 0.2e1 / 0.1233e4 * t48 * t49 * t56
  t66 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t67 = t42 ** 2
  t68 = 0.1e1 / t67
  t73 = t4 * t66
  t74 = t42 * t47
  t75 = t73 * t74
  t76 = t49 * t55
  t77 = r0 ** 2
  t81 = t76 * t50 / t51 / t77
  t84 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t85 = t84 * f.p.zeta_threshold
  t87 = f.my_piecewise3(t20, t85, t21 * t19)
  t89 = 0.1e1 / t67 / t6
  t94 = t4 * t87
  t95 = t68 * t47
  t96 = t94 * t95
  t99 = t94 * t74
  t101 = t49 / t55
  t102 = t77 ** 2
  t103 = t51 ** 2
  t107 = t101 * s0 / t103 / t102
  t110 = t77 * r0
  t114 = t76 * t50 / t51 / t110
  t118 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t60 - t5 * t66 * t68 * t60 / 0.4e1 + t75 * t81 / 0.137e3 + t5 * t87 * t89 * t60 / 0.12e2 + t96 * t81 / 0.411e3 - t99 * t107 / 0.411e3 - 0.7e1 / 0.822e3 * t99 * t114)
  t120 = r1 <= f.p.dens_threshold
  t121 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t122 = 0.1e1 + t121
  t123 = t122 <= f.p.zeta_threshold
  t124 = t122 ** (0.1e1 / 0.3e1)
  t125 = t124 ** 2
  t126 = 0.1e1 / t125
  t128 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t129 = t128 ** 2
  t133 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t137 = f.my_piecewise3(t123, 0, 0.4e1 / 0.9e1 * t126 * t129 + 0.4e1 / 0.3e1 * t124 * t133)
  t139 = jnp.sqrt(s2)
  t140 = r1 ** (0.1e1 / 0.3e1)
  t143 = t139 / t140 / r1
  t144 = jnp.sqrt(t143)
  t149 = 0.1e1 + 0.2e1 / 0.1233e4 * t48 * t49 * t144 * t143
  t155 = f.my_piecewise3(t123, 0, 0.4e1 / 0.3e1 * t124 * t128)
  t161 = f.my_piecewise3(t123, t85, t124 * t122)
  t167 = f.my_piecewise3(t120, 0, -0.3e1 / 0.8e1 * t5 * t137 * t42 * t149 - t5 * t155 * t68 * t149 / 0.4e1 + t5 * t161 * t89 * t149 / 0.12e2)
  t177 = t24 ** 2
  t181 = 0.6e1 * t33 - 0.6e1 * t16 / t177
  t182 = f.my_piecewise5(t10, 0, t14, 0, t181)
  t186 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t182)
  t224 = 0.1e1 / t67 / t24
  t246 = -0.3e1 / 0.8e1 * t5 * t186 * t42 * t60 + 0.3e1 / 0.274e3 * t4 * t41 * t74 * t81 + t73 * t95 * t81 / 0.137e3 - t75 * t107 / 0.137e3 - t94 * t89 * t47 * t81 / 0.411e3 - t96 * t107 / 0.411e3 - 0.2e1 / 0.1233e4 * t99 * t49 / t56 * t50 * s0 / t102 / t110 - 0.3e1 / 0.8e1 * t5 * t41 * t68 * t60 + t5 * t66 * t89 * t60 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t87 * t224 * t60 - 0.7e1 / 0.274e3 * t75 * t114 - 0.7e1 / 0.822e3 * t96 * t114 + 0.7e1 / 0.411e3 * t99 * t101 * s0 / t103 / t102 / r0 + 0.35e2 / 0.1233e4 * t99 * t76 * t50 / t51 / t102
  t247 = f.my_piecewise3(t1, 0, t246)
  t257 = f.my_piecewise5(t14, 0, t10, 0, -t181)
  t261 = f.my_piecewise3(t123, 0, -0.8e1 / 0.27e2 / t125 / t122 * t129 * t128 + 0.4e1 / 0.3e1 * t126 * t128 * t133 + 0.4e1 / 0.3e1 * t124 * t257)
  t279 = f.my_piecewise3(t120, 0, -0.3e1 / 0.8e1 * t5 * t261 * t42 * t149 - 0.3e1 / 0.8e1 * t5 * t137 * t68 * t149 + t5 * t155 * t89 * t149 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t161 * t224 * t149)
  d111 = 0.3e1 * t118 + 0.3e1 * t167 + t6 * (t247 + t279)

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
  t4 = 0.1e1 / t3
  t5 = t2 * t4
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
  t56 = t2 ** 2
  t58 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t59 = 0.1e1 / t58
  t60 = t56 * t59
  t61 = 4 ** (0.1e1 / 0.3e1)
  t62 = jnp.sqrt(s0)
  t63 = r0 ** (0.1e1 / 0.3e1)
  t66 = t62 / t63 / r0
  t67 = jnp.sqrt(t66)
  t68 = t67 * t66
  t72 = 0.1e1 + 0.2e1 / 0.1233e4 * t60 * t61 * t68
  t81 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t82 = t4 * t81
  t83 = t54 * t59
  t84 = t82 * t83
  t85 = t61 * t67
  t86 = r0 ** 2
  t90 = t85 * t62 / t63 / t86
  t95 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t96 = t4 * t95
  t97 = t54 ** 2
  t98 = 0.1e1 / t97
  t99 = t98 * t59
  t100 = t96 * t99
  t103 = t96 * t83
  t105 = t61 / t67
  t106 = t86 ** 2
  t107 = t63 ** 2
  t111 = t105 * s0 / t107 / t106
  t114 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t115 = t114 * f.p.zeta_threshold
  t117 = f.my_piecewise3(t20, t115, t21 * t19)
  t118 = t4 * t117
  t120 = 0.1e1 / t97 / t6
  t121 = t120 * t59
  t122 = t118 * t121
  t125 = t118 * t99
  t128 = t118 * t83
  t130 = t61 / t68
  t131 = t62 * s0
  t132 = t86 * r0
  t136 = t130 * t131 / t106 / t132
  t148 = 0.1e1 / t97 / t25
  t156 = t85 * t62 / t63 / t132
  t161 = t106 * r0
  t165 = t105 * s0 / t107 / t161
  t171 = t85 * t62 / t63 / t106
  t174 = -0.3e1 / 0.8e1 * t5 * t53 * t54 * t72 + 0.3e1 / 0.274e3 * t84 * t90 + t100 * t90 / 0.137e3 - t103 * t111 / 0.137e3 - t122 * t90 / 0.411e3 - t125 * t111 / 0.411e3 - 0.2e1 / 0.1233e4 * t128 * t136 - 0.3e1 / 0.8e1 * t5 * t81 * t98 * t72 + t5 * t95 * t120 * t72 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t117 * t148 * t72 - 0.7e1 / 0.274e3 * t103 * t156 - 0.7e1 / 0.822e3 * t125 * t156 + 0.7e1 / 0.411e3 * t128 * t165 + 0.35e2 / 0.1233e4 * t128 * t171
  t175 = f.my_piecewise3(t1, 0, t174)
  t177 = r1 <= f.p.dens_threshold
  t178 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t179 = 0.1e1 + t178
  t180 = t179 <= f.p.zeta_threshold
  t181 = t179 ** (0.1e1 / 0.3e1)
  t182 = t181 ** 2
  t184 = 0.1e1 / t182 / t179
  t186 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t187 = t186 ** 2
  t191 = 0.1e1 / t182
  t192 = t191 * t186
  t194 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t198 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t202 = f.my_piecewise3(t180, 0, -0.8e1 / 0.27e2 * t184 * t187 * t186 + 0.4e1 / 0.3e1 * t192 * t194 + 0.4e1 / 0.3e1 * t181 * t198)
  t204 = jnp.sqrt(s2)
  t205 = r1 ** (0.1e1 / 0.3e1)
  t208 = t204 / t205 / r1
  t209 = jnp.sqrt(t208)
  t214 = 0.1e1 + 0.2e1 / 0.1233e4 * t60 * t61 * t209 * t208
  t223 = f.my_piecewise3(t180, 0, 0.4e1 / 0.9e1 * t191 * t187 + 0.4e1 / 0.3e1 * t181 * t194)
  t230 = f.my_piecewise3(t180, 0, 0.4e1 / 0.3e1 * t181 * t186)
  t236 = f.my_piecewise3(t180, t115, t181 * t179)
  t242 = f.my_piecewise3(t177, 0, -0.3e1 / 0.8e1 * t5 * t202 * t54 * t214 - 0.3e1 / 0.8e1 * t5 * t223 * t98 * t214 + t5 * t230 * t120 * t214 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t236 * t148 * t214)
  t244 = t106 ** 2
  t271 = t19 ** 2
  t274 = t30 ** 2
  t280 = t41 ** 2
  t289 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t290 = f.my_piecewise5(t10, 0, t14, 0, t289)
  t294 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t271 * t274 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t280 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t290)
  t312 = 0.1e1 / t97 / t36
  t317 = 0.28e2 / 0.1233e4 * t128 * t130 * t131 / t244 + 0.140e3 / 0.1233e4 * t103 * t171 + 0.140e3 / 0.3699e4 * t125 * t171 - 0.427e3 / 0.3699e4 * t128 * t105 * s0 / t107 / t106 / t86 - 0.455e3 / 0.3699e4 * t128 * t85 * t62 / t63 / t161 - 0.8e1 / 0.1233e4 * t103 * t136 + 0.4e1 / 0.1233e4 * t122 * t111 - 0.3e1 / 0.8e1 * t5 * t294 * t54 * t72 - t5 * t53 * t98 * t72 / 0.2e1 + t5 * t81 * t120 * t72 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t95 * t148 * t72 + 0.10e2 / 0.27e2 * t5 * t117 * t312 * t72
  t326 = s0 ** 2
  t362 = -0.8e1 / 0.3699e4 * t125 * t136 - 0.4e1 / 0.1233e4 * t128 * t61 / t67 / s0 * t107 * t86 * t326 / t63 / t244 / r0 + 0.2e1 / 0.137e3 * t4 * t53 * t83 * t90 - 0.2e1 / 0.137e3 * t84 * t111 - 0.4e1 / 0.411e3 * t100 * t111 + 0.2e1 / 0.137e3 * t82 * t99 * t90 - 0.7e1 / 0.137e3 * t84 * t156 - 0.4e1 / 0.411e3 * t96 * t121 * t90 - 0.14e2 / 0.411e3 * t100 * t156 + 0.28e2 / 0.411e3 * t103 * t165 + 0.20e2 / 0.3699e4 * t118 * t148 * t59 * t90 + 0.14e2 / 0.1233e4 * t122 * t156 + 0.28e2 / 0.1233e4 * t125 * t165
  t364 = f.my_piecewise3(t1, 0, t317 + t362)
  t365 = t179 ** 2
  t368 = t187 ** 2
  t374 = t194 ** 2
  t380 = f.my_piecewise5(t14, 0, t10, 0, -t289)
  t384 = f.my_piecewise3(t180, 0, 0.40e2 / 0.81e2 / t182 / t365 * t368 - 0.16e2 / 0.9e1 * t184 * t187 * t194 + 0.4e1 / 0.3e1 * t191 * t374 + 0.16e2 / 0.9e1 * t192 * t198 + 0.4e1 / 0.3e1 * t181 * t380)
  t406 = f.my_piecewise3(t177, 0, -0.3e1 / 0.8e1 * t5 * t384 * t54 * t214 - t5 * t202 * t98 * t214 / 0.2e1 + t5 * t223 * t120 * t214 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t230 * t148 * t214 + 0.10e2 / 0.27e2 * t5 * t236 * t312 * t214)
  d1111 = 0.4e1 * t175 + 0.4e1 * t242 + t6 * (t364 + t406)

  res = {'v4rho4': d1111}
  return res
