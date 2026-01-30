"""Generated from gga_x_pbea.mpl."""

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
  pbea_mu = 0.003612186453650947

  pbea_alpha = 0.52

  pbea_f = lambda x: 1 + KAPPA_PBE * (1 - (1 + pbea_mu * x ** 2 / (pbea_alpha * KAPPA_PBE)) ** (-pbea_alpha))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbea_f, rs, z, xs0, xs1)

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
  pbea_mu = 0.003612186453650947

  pbea_alpha = 0.52

  pbea_f = lambda x: 1 + KAPPA_PBE * (1 - (1 + pbea_mu * x ** 2 / (pbea_alpha * KAPPA_PBE)) ** (-pbea_alpha))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbea_f, rs, z, xs0, xs1)

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
  pbea_mu = 0.003612186453650947

  pbea_alpha = 0.52

  pbea_f = lambda x: 1 + KAPPA_PBE * (1 - (1 + pbea_mu * x ** 2 / (pbea_alpha * KAPPA_PBE)) ** (-pbea_alpha))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbea_f, rs, z, xs0, xs1)

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
  t28 = r0 ** 2
  t29 = r0 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t32 = 0.1e1 / t30 / t28
  t35 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * s0 * t32
  t36 = t35 ** (-0.52e0)
  t38 = 0.18040e1 - 0.8040e0 * t36
  t42 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t38)
  t43 = r1 <= f.p.dens_threshold
  t44 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t45 = 0.1e1 + t44
  t46 = t45 <= f.p.zeta_threshold
  t47 = t45 ** (0.1e1 / 0.3e1)
  t49 = f.my_piecewise3(t46, t22, t47 * t45)
  t51 = r1 ** 2
  t52 = r1 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t55 = 0.1e1 / t53 / t51
  t58 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * s2 * t55
  t59 = t58 ** (-0.52e0)
  t61 = 0.18040e1 - 0.8040e0 * t59
  t65 = f.my_piecewise3(t43, 0, -0.3e1 / 0.8e1 * t5 * t49 * t26 * t61)
  t66 = t6 ** 2
  t68 = t16 / t66
  t69 = t7 - t68
  t70 = f.my_piecewise5(t10, 0, t14, 0, t69)
  t73 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t70)
  t78 = t26 ** 2
  t79 = 0.1e1 / t78
  t83 = t5 * t25 * t79 * t38 / 0.8e1
  t84 = t5 * t25
  t85 = t35 ** (-0.152e1)
  t86 = t26 * t85
  t95 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t73 * t26 * t38 - t83 + 0.36121864536509469700000000000000000000000000000000e-2 * t84 * t86 * s0 / t30 / t28 / r0)
  t97 = f.my_piecewise5(t14, 0, t10, 0, -t69)
  t100 = f.my_piecewise3(t46, 0, 0.4e1 / 0.3e1 * t47 * t97)
  t108 = t5 * t49 * t79 * t61 / 0.8e1
  t110 = f.my_piecewise3(t43, 0, -0.3e1 / 0.8e1 * t5 * t100 * t26 * t61 - t108)
  vrho_0_ = t42 + t65 + t6 * (t95 + t110)
  t113 = -t7 - t68
  t114 = f.my_piecewise5(t10, 0, t14, 0, t113)
  t117 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t114)
  t123 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t117 * t26 * t38 - t83)
  t125 = f.my_piecewise5(t14, 0, t10, 0, -t113)
  t128 = f.my_piecewise3(t46, 0, 0.4e1 / 0.3e1 * t47 * t125)
  t133 = t5 * t49
  t134 = t58 ** (-0.152e1)
  t135 = t26 * t134
  t144 = f.my_piecewise3(t43, 0, -0.3e1 / 0.8e1 * t5 * t128 * t26 * t61 - t108 + 0.36121864536509469700000000000000000000000000000000e-2 * t133 * t135 * s2 / t53 / t51 / r1)
  vrho_1_ = t42 + t65 + t6 * (t123 + t144)
  t150 = f.my_piecewise3(t1, 0, -0.13545699201191051137500000000000000000000000000000e-2 * t84 * t86 * t32)
  vsigma_0_ = t6 * t150
  vsigma_1_ = 0.0e0
  t154 = f.my_piecewise3(t43, 0, -0.13545699201191051137500000000000000000000000000000e-2 * t133 * t135 * t55)
  vsigma_2_ = t6 * t154
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
  pbea_mu = 0.003612186453650947

  pbea_alpha = 0.52

  pbea_f = lambda x: 1 + KAPPA_PBE * (1 - (1 + pbea_mu * x ** 2 / (pbea_alpha * KAPPA_PBE)) ** (-pbea_alpha))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbea_f, rs, z, xs0, xs1)

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
  t20 = 2 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t22 = s0 * t21
  t23 = r0 ** 2
  t24 = t18 ** 2
  t29 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * t22 / t24 / t23
  t30 = t29 ** (-0.52e0)
  t32 = 0.18040e1 - 0.8040e0 * t30
  t36 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t32)
  t42 = t6 * t17
  t46 = t29 ** (-0.152e1)
  t52 = f.my_piecewise3(t2, 0, -t6 * t17 / t24 * t32 / 0.8e1 + 0.36121864536509469700000000000000000000000000000000e-2 * t42 / t18 / t23 / r0 * t46 * t22)
  vrho_0_ = 0.2e1 * r0 * t52 + 0.2e1 * t36
  t61 = f.my_piecewise3(t2, 0, -0.13545699201191051137500000000000000000000000000000e-2 * t42 / t18 / t23 * t46 * t21)
  vsigma_0_ = 0.2e1 * r0 * t61
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
  t22 = 2 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = s0 * t23
  t25 = r0 ** 2
  t30 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * t24 / t19 / t25
  t31 = t30 ** (-0.52e0)
  t33 = 0.18040e1 - 0.8040e0 * t31
  t37 = t6 * t17
  t38 = t25 * r0
  t41 = t30 ** (-0.152e1)
  t42 = 0.1e1 / t18 / t38 * t41
  t47 = f.my_piecewise3(t2, 0, -t6 * t17 / t19 * t33 / 0.8e1 + 0.36121864536509469700000000000000000000000000000000e-2 * t37 * t42 * t24)
  t55 = t25 ** 2
  t64 = t30 ** (-0.252e1)
  t66 = s0 ** 2
  t72 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t33 / 0.12e2 - 0.10836559360952840910000000000000000000000000000000e-1 * t37 / t18 / t55 * t41 * t24 + 0.25300158545003055735880189695348022666156397499681e-3 * t37 / t55 / t38 * t64 * t66 * t22)
  v2rho2_0_ = 0.2e1 * r0 * t72 + 0.4e1 * t47
  t81 = f.my_piecewise3(t2, 0, -0.13545699201191051137500000000000000000000000000000e-2 * t37 / t18 / t25 * t41 * t23)
  t93 = f.my_piecewise3(t2, 0, 0.31606631469445785987500000000000000000000000000000e-2 * t37 * t42 * t23 - 0.94875594543761459009550711357555084998086490623803e-4 * t37 / t55 / t25 * t64 * t22 * s0)
  v2rhosigma_0_ = 0.2e1 * r0 * t93 + 0.2e1 * t81
  t102 = f.my_piecewise3(t2, 0, 0.35578347953910547128581516759083156874282433983926e-4 * t37 / t55 / r0 * t64 * t22)
  v2sigma2_0_ = 0.2e1 * r0 * t102
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
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = s0 * t24
  t26 = r0 ** 2
  t28 = 0.1e1 / t19 / t26
  t31 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * t25 * t28
  t32 = t31 ** (-0.52e0)
  t34 = 0.18040e1 - 0.8040e0 * t32
  t38 = t6 * t17
  t39 = t26 ** 2
  t42 = t31 ** (-0.152e1)
  t50 = t31 ** (-0.252e1)
  t52 = s0 ** 2
  t53 = t52 * t23
  t58 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t34 / 0.12e2 - 0.10836559360952840910000000000000000000000000000000e-1 * t38 / t18 / t39 * t42 * t25 + 0.25300158545003055735880189695348022666156397499681e-3 * t38 / t39 / t26 / r0 * t50 * t53)
  t71 = t39 ** 2
  t80 = t31 ** (-0.352e1)
  t87 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t28 * t34 + 0.46155715796650989061111111111111111111111111111111e-1 * t38 / t18 / t39 / r0 * t42 * t25 - 0.25300158545003055735880189695348022666156397499681e-2 * t38 / t71 * t50 * t53 + 0.29378747637215569792283720098476720115805910151256e-4 * t38 / t19 / t71 / t26 * t80 * t52 * s0)
  v3rho3_0_ = 0.2e1 * r0 * t87 + 0.6e1 * t58

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
  t22 = 0.1e1 / t20 / t18
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = s0 * t25
  t29 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * t26 * t22
  t30 = t29 ** (-0.52e0)
  t32 = 0.18040e1 - 0.8040e0 * t30
  t36 = t6 * t17
  t37 = t18 ** 2
  t41 = t29 ** (-0.152e1)
  t46 = t37 ** 2
  t48 = t29 ** (-0.252e1)
  t50 = s0 ** 2
  t51 = t50 * t24
  t58 = t29 ** (-0.352e1)
  t60 = t50 * s0
  t65 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t32 + 0.46155715796650989061111111111111111111111111111111e-1 * t36 / t19 / t37 / r0 * t41 * t26 - 0.25300158545003055735880189695348022666156397499681e-2 * t36 / t46 * t48 * t51 + 0.29378747637215569792283720098476720115805910151256e-4 * t36 / t20 / t46 / t18 * t58 * t60)
  t67 = t18 * r0
  t74 = t37 * t18
  t97 = t29 ** (-0.452e1)
  t99 = t50 ** 2
  t105 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 / t20 / t67 * t32 - 0.24482597074745307241111111111111111111111111111112e0 * t36 / t19 / t74 * t41 * t26 + 0.23472924872308390599399953772906221029156213235815e-1 * t36 / t46 / r0 * t48 * t51 - 0.60716078450245510904053021536851888239332214312596e-3 * t36 / t20 / t46 / t67 * t58 * t60 + 0.23826236135102504148248246617537799504687851948602e-5 * t36 / t19 / t46 / t74 * t97 * t99 * t25)
  v4rho4_0_ = 0.2e1 * r0 * t105 + 0.8e1 * t65

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
  t32 = r0 ** 2
  t33 = r0 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t39 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * s0 / t34 / t32
  t40 = t39 ** (-0.52e0)
  t42 = 0.18040e1 - 0.8040e0 * t40
  t46 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t47 = t46 * f.p.zeta_threshold
  t49 = f.my_piecewise3(t20, t47, t21 * t19)
  t50 = t30 ** 2
  t51 = 0.1e1 / t50
  t55 = t5 * t49 * t51 * t42 / 0.8e1
  t56 = t5 * t49
  t57 = t39 ** (-0.152e1)
  t58 = t30 * t57
  t59 = t32 * r0
  t62 = s0 / t34 / t59
  t63 = t58 * t62
  t67 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t42 - t55 + 0.36121864536509469700000000000000000000000000000000e-2 * t56 * t63)
  t69 = r1 <= f.p.dens_threshold
  t70 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t71 = 0.1e1 + t70
  t72 = t71 <= f.p.zeta_threshold
  t73 = t71 ** (0.1e1 / 0.3e1)
  t75 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t78 = f.my_piecewise3(t72, 0, 0.4e1 / 0.3e1 * t73 * t75)
  t80 = r1 ** 2
  t81 = r1 ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t87 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * s2 / t82 / t80
  t88 = t87 ** (-0.52e0)
  t90 = 0.18040e1 - 0.8040e0 * t88
  t95 = f.my_piecewise3(t72, t47, t73 * t71)
  t99 = t5 * t95 * t51 * t90 / 0.8e1
  t101 = f.my_piecewise3(t69, 0, -0.3e1 / 0.8e1 * t5 * t78 * t30 * t90 - t99)
  t103 = t21 ** 2
  t104 = 0.1e1 / t103
  t105 = t26 ** 2
  t110 = t16 / t22 / t6
  t112 = -0.2e1 * t23 + 0.2e1 * t110
  t113 = f.my_piecewise5(t10, 0, t14, 0, t112)
  t117 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t104 * t105 + 0.4e1 / 0.3e1 * t21 * t113)
  t124 = t5 * t29 * t51 * t42
  t130 = 0.1e1 / t50 / t6
  t134 = t5 * t49 * t130 * t42 / 0.12e2
  t137 = t56 * t51 * t57 * t62
  t139 = t39 ** (-0.252e1)
  t141 = s0 ** 2
  t142 = t32 ** 2
  t157 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t117 * t30 * t42 - t124 / 0.4e1 + 0.72243729073018939400000000000000000000000000000000e-2 * t5 * t29 * t63 + t134 + 0.24081243024339646466666666666666666666666666666666e-2 * t137 + 0.12650079272501527867940094847674011333078198749840e-3 * t56 * t30 * t139 * t141 / t33 / t142 / t59 - 0.13244683663386805556666666666666666666666666666667e-1 * t56 * t58 * s0 / t34 / t142)
  t158 = t73 ** 2
  t159 = 0.1e1 / t158
  t160 = t75 ** 2
  t164 = f.my_piecewise5(t14, 0, t10, 0, -t112)
  t168 = f.my_piecewise3(t72, 0, 0.4e1 / 0.9e1 * t159 * t160 + 0.4e1 / 0.3e1 * t73 * t164)
  t175 = t5 * t78 * t51 * t90
  t180 = t5 * t95 * t130 * t90 / 0.12e2
  t182 = f.my_piecewise3(t69, 0, -0.3e1 / 0.8e1 * t5 * t168 * t30 * t90 - t175 / 0.4e1 + t180)
  d11 = 0.2e1 * t67 + 0.2e1 * t101 + t6 * (t157 + t182)
  t185 = -t7 - t24
  t186 = f.my_piecewise5(t10, 0, t14, 0, t185)
  t189 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t186)
  t195 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t189 * t30 * t42 - t55)
  t197 = f.my_piecewise5(t14, 0, t10, 0, -t185)
  t200 = f.my_piecewise3(t72, 0, 0.4e1 / 0.3e1 * t73 * t197)
  t205 = t5 * t95
  t206 = t87 ** (-0.152e1)
  t207 = t30 * t206
  t208 = t80 * r1
  t211 = s2 / t82 / t208
  t212 = t207 * t211
  t216 = f.my_piecewise3(t69, 0, -0.3e1 / 0.8e1 * t5 * t200 * t30 * t90 - t99 + 0.36121864536509469700000000000000000000000000000000e-2 * t205 * t212)
  t220 = 0.2e1 * t110
  t221 = f.my_piecewise5(t10, 0, t14, 0, t220)
  t225 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t104 * t186 * t26 + 0.4e1 / 0.3e1 * t21 * t221)
  t232 = t5 * t189 * t51 * t42
  t240 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t225 * t30 * t42 - t232 / 0.8e1 + 0.36121864536509469700000000000000000000000000000000e-2 * t5 * t189 * t63 - t124 / 0.8e1 + t134 + 0.12040621512169823233333333333333333333333333333333e-2 * t137)
  t244 = f.my_piecewise5(t14, 0, t10, 0, -t220)
  t248 = f.my_piecewise3(t72, 0, 0.4e1 / 0.9e1 * t159 * t197 * t75 + 0.4e1 / 0.3e1 * t73 * t244)
  t255 = t5 * t200 * t51 * t90
  t263 = t205 * t51 * t206 * t211
  t266 = f.my_piecewise3(t69, 0, -0.3e1 / 0.8e1 * t5 * t248 * t30 * t90 - t255 / 0.8e1 - t175 / 0.8e1 + t180 + 0.36121864536509469700000000000000000000000000000000e-2 * t5 * t78 * t212 + 0.12040621512169823233333333333333333333333333333333e-2 * t263)
  d12 = t67 + t101 + t195 + t216 + t6 * (t240 + t266)
  t271 = t186 ** 2
  t275 = 0.2e1 * t23 + 0.2e1 * t110
  t276 = f.my_piecewise5(t10, 0, t14, 0, t275)
  t280 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t104 * t271 + 0.4e1 / 0.3e1 * t21 * t276)
  t287 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t280 * t30 * t42 - t232 / 0.4e1 + t134)
  t288 = t197 ** 2
  t292 = f.my_piecewise5(t14, 0, t10, 0, -t275)
  t296 = f.my_piecewise3(t72, 0, 0.4e1 / 0.9e1 * t159 * t288 + 0.4e1 / 0.3e1 * t73 * t292)
  t306 = t87 ** (-0.252e1)
  t308 = s2 ** 2
  t309 = t80 ** 2
  t324 = f.my_piecewise3(t69, 0, -0.3e1 / 0.8e1 * t5 * t296 * t30 * t90 - t255 / 0.4e1 + 0.72243729073018939400000000000000000000000000000000e-2 * t5 * t200 * t212 + t180 + 0.24081243024339646466666666666666666666666666666666e-2 * t263 + 0.12650079272501527867940094847674011333078198749840e-3 * t205 * t30 * t306 * t308 / t81 / t309 / t208 - 0.13244683663386805556666666666666666666666666666667e-1 * t205 * t207 * s2 / t82 / t309)
  d22 = 0.2e1 * t195 + 0.2e1 * t216 + t6 * (t287 + t324)
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
  t44 = r0 ** 2
  t45 = r0 ** (0.1e1 / 0.3e1)
  t46 = t45 ** 2
  t51 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * s0 / t46 / t44
  t52 = t51 ** (-0.52e0)
  t54 = 0.18040e1 - 0.8040e0 * t52
  t60 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t61 = t42 ** 2
  t62 = 0.1e1 / t61
  t67 = t5 * t60
  t68 = t51 ** (-0.152e1)
  t69 = t42 * t68
  t70 = t44 * r0
  t73 = s0 / t46 / t70
  t74 = t69 * t73
  t77 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t78 = t77 * f.p.zeta_threshold
  t80 = f.my_piecewise3(t20, t78, t21 * t19)
  t82 = 0.1e1 / t61 / t6
  t87 = t5 * t80
  t88 = t62 * t68
  t89 = t88 * t73
  t92 = t51 ** (-0.252e1)
  t93 = t42 * t92
  t94 = s0 ** 2
  t95 = t44 ** 2
  t99 = t94 / t45 / t95 / t70
  t100 = t93 * t99
  t105 = s0 / t46 / t95
  t106 = t69 * t105
  t110 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t54 - t5 * t60 * t62 * t54 / 0.4e1 + 0.72243729073018939400000000000000000000000000000000e-2 * t67 * t74 + t5 * t80 * t82 * t54 / 0.12e2 + 0.24081243024339646466666666666666666666666666666666e-2 * t87 * t89 + 0.12650079272501527867940094847674011333078198749840e-3 * t87 * t100 - 0.13244683663386805556666666666666666666666666666667e-1 * t87 * t106)
  t112 = r1 <= f.p.dens_threshold
  t113 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t114 = 0.1e1 + t113
  t115 = t114 <= f.p.zeta_threshold
  t116 = t114 ** (0.1e1 / 0.3e1)
  t117 = t116 ** 2
  t118 = 0.1e1 / t117
  t120 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t121 = t120 ** 2
  t125 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t129 = f.my_piecewise3(t115, 0, 0.4e1 / 0.9e1 * t118 * t121 + 0.4e1 / 0.3e1 * t116 * t125)
  t131 = r1 ** 2
  t132 = r1 ** (0.1e1 / 0.3e1)
  t133 = t132 ** 2
  t139 = (0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * s2 / t133 / t131) ** (-0.52e0)
  t141 = 0.18040e1 - 0.8040e0 * t139
  t147 = f.my_piecewise3(t115, 0, 0.4e1 / 0.3e1 * t116 * t120)
  t153 = f.my_piecewise3(t115, t78, t116 * t114)
  t159 = f.my_piecewise3(t112, 0, -0.3e1 / 0.8e1 * t5 * t129 * t42 * t141 - t5 * t147 * t62 * t141 / 0.4e1 + t5 * t153 * t82 * t141 / 0.12e2)
  t176 = t51 ** (-0.352e1)
  t179 = t95 ** 2
  t194 = t24 ** 2
  t198 = 0.6e1 * t33 - 0.6e1 * t16 / t194
  t199 = f.my_piecewise5(t10, 0, t14, 0, t198)
  t203 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t199)
  t235 = 0.1e1 / t61 / t24
  t240 = 0.10836559360952840910000000000000000000000000000000e-1 * t5 * t41 * t74 + 0.72243729073018939399999999999999999999999999999999e-2 * t67 * t89 + 0.37950237817504583603820284543022033999234596249521e-3 * t67 * t100 - 0.24081243024339646466666666666666666666666666666666e-2 * t87 * t82 * t68 * t73 + 0.12650079272501527867940094847674011333078198749840e-3 * t87 * t62 * t92 * t99 + 0.73446869093038924480709300246191800289514775378135e-5 * t87 * t42 * t176 * t94 * s0 / t179 / t70 - 0.3e1 / 0.8e1 * t5 * t203 * t42 * t54 - 0.13915087199751680654734104332441412466386018624824e-2 * t87 * t93 * t94 / t45 / t179 + 0.61808523762471759264444444444444444444444444444446e-1 * t87 * t69 * s0 / t46 / t95 / r0 - 0.39734050990160416670000000000000000000000000000000e-1 * t67 * t106 - 0.13244683663386805556666666666666666666666666666666e-1 * t87 * t88 * t105 - 0.3e1 / 0.8e1 * t5 * t41 * t62 * t54 + t5 * t60 * t82 * t54 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t80 * t235 * t54
  t241 = f.my_piecewise3(t1, 0, t240)
  t251 = f.my_piecewise5(t14, 0, t10, 0, -t198)
  t255 = f.my_piecewise3(t115, 0, -0.8e1 / 0.27e2 / t117 / t114 * t121 * t120 + 0.4e1 / 0.3e1 * t118 * t120 * t125 + 0.4e1 / 0.3e1 * t116 * t251)
  t273 = f.my_piecewise3(t112, 0, -0.3e1 / 0.8e1 * t5 * t255 * t42 * t141 - 0.3e1 / 0.8e1 * t5 * t129 * t62 * t141 + t5 * t147 * t82 * t141 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t153 * t235 * t141)
  d111 = 0.3e1 * t110 + 0.3e1 * t159 + t6 * (t241 + t273)

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
  t23 = 0.1e1 / t22
  t24 = t6 ** 2
  t25 = 0.1e1 / t24
  t27 = -t16 * t25 + t7
  t28 = f.my_piecewise5(t10, 0, t14, 0, t27)
  t29 = t28 ** 2
  t32 = t24 * t6
  t33 = 0.1e1 / t32
  t36 = 0.2e1 * t16 * t33 - 0.2e1 * t25
  t37 = f.my_piecewise5(t10, 0, t14, 0, t36)
  t41 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t23 * t29 + 0.4e1 / 0.3e1 * t21 * t37)
  t42 = t5 * t41
  t43 = t6 ** (0.1e1 / 0.3e1)
  t44 = r0 ** 2
  t45 = r0 ** (0.1e1 / 0.3e1)
  t46 = t45 ** 2
  t51 = 0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * s0 / t46 / t44
  t52 = t51 ** (-0.152e1)
  t53 = t43 * t52
  t54 = t44 * r0
  t57 = s0 / t46 / t54
  t58 = t53 * t57
  t63 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t64 = t5 * t63
  t65 = t43 ** 2
  t66 = 0.1e1 / t65
  t67 = t66 * t52
  t68 = t67 * t57
  t71 = t51 ** (-0.252e1)
  t72 = t43 * t71
  t73 = s0 ** 2
  t74 = t44 ** 2
  t78 = t73 / t45 / t74 / t54
  t79 = t72 * t78
  t82 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t83 = t82 * f.p.zeta_threshold
  t85 = f.my_piecewise3(t20, t83, t21 * t19)
  t86 = t5 * t85
  t88 = 0.1e1 / t65 / t6
  t89 = t88 * t52
  t90 = t89 * t57
  t93 = t66 * t71
  t94 = t93 * t78
  t97 = t51 ** (-0.352e1)
  t98 = t43 * t97
  t99 = t73 * s0
  t100 = t74 ** 2
  t103 = t99 / t100 / t54
  t104 = t98 * t103
  t108 = 0.1e1 / t22 / t19
  t112 = t23 * t28
  t115 = t24 ** 2
  t116 = 0.1e1 / t115
  t119 = -0.6e1 * t16 * t116 + 0.6e1 * t33
  t120 = f.my_piecewise5(t10, 0, t14, 0, t119)
  t124 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t108 * t29 * t28 + 0.4e1 / 0.3e1 * t112 * t37 + 0.4e1 / 0.3e1 * t21 * t120)
  t126 = t51 ** (-0.52e0)
  t128 = 0.18040e1 - 0.8040e0 * t126
  t134 = t73 / t45 / t100
  t135 = t72 * t134
  t141 = s0 / t46 / t74 / r0
  t142 = t53 * t141
  t147 = s0 / t46 / t74
  t148 = t53 * t147
  t151 = t67 * t147
  t163 = 0.1e1 / t65 / t24
  t168 = 0.10836559360952840910000000000000000000000000000000e-1 * t42 * t58 + 0.72243729073018939399999999999999999999999999999999e-2 * t64 * t68 + 0.37950237817504583603820284543022033999234596249521e-3 * t64 * t79 - 0.24081243024339646466666666666666666666666666666666e-2 * t86 * t90 + 0.12650079272501527867940094847674011333078198749840e-3 * t86 * t94 + 0.73446869093038924480709300246191800289514775378135e-5 * t86 * t104 - 0.3e1 / 0.8e1 * t5 * t124 * t43 * t128 - 0.13915087199751680654734104332441412466386018624824e-2 * t86 * t135 + 0.61808523762471759264444444444444444444444444444446e-1 * t86 * t142 - 0.39734050990160416670000000000000000000000000000000e-1 * t64 * t148 - 0.13244683663386805556666666666666666666666666666666e-1 * t86 * t151 - 0.3e1 / 0.8e1 * t5 * t41 * t66 * t128 + t5 * t63 * t88 * t128 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t85 * t163 * t128
  t169 = f.my_piecewise3(t1, 0, t168)
  t171 = r1 <= f.p.dens_threshold
  t172 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t173 = 0.1e1 + t172
  t174 = t173 <= f.p.zeta_threshold
  t175 = t173 ** (0.1e1 / 0.3e1)
  t176 = t175 ** 2
  t178 = 0.1e1 / t176 / t173
  t180 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t181 = t180 ** 2
  t185 = 0.1e1 / t176
  t186 = t185 * t180
  t188 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t192 = f.my_piecewise5(t14, 0, t10, 0, -t119)
  t196 = f.my_piecewise3(t174, 0, -0.8e1 / 0.27e2 * t178 * t181 * t180 + 0.4e1 / 0.3e1 * t186 * t188 + 0.4e1 / 0.3e1 * t175 * t192)
  t198 = r1 ** 2
  t199 = r1 ** (0.1e1 / 0.3e1)
  t200 = t199 ** 2
  t206 = (0.1e1 + 0.86399408095363255118637581324148488327592805204745e-2 * s2 / t200 / t198) ** (-0.52e0)
  t208 = 0.18040e1 - 0.8040e0 * t206
  t217 = f.my_piecewise3(t174, 0, 0.4e1 / 0.9e1 * t185 * t181 + 0.4e1 / 0.3e1 * t175 * t188)
  t224 = f.my_piecewise3(t174, 0, 0.4e1 / 0.3e1 * t175 * t180)
  t230 = f.my_piecewise3(t174, t83, t175 * t173)
  t236 = f.my_piecewise3(t171, 0, -0.3e1 / 0.8e1 * t5 * t196 * t43 * t208 - 0.3e1 / 0.8e1 * t5 * t217 * t66 * t208 + t5 * t224 * t88 * t208 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t230 * t163 * t208)
  t238 = t19 ** 2
  t241 = t29 ** 2
  t247 = t37 ** 2
  t256 = -0.24e2 * t116 + 0.24e2 * t16 / t115 / t6
  t257 = f.my_piecewise5(t10, 0, t14, 0, t256)
  t261 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t238 * t241 - 0.16e2 / 0.9e1 * t108 * t29 * t37 + 0.4e1 / 0.3e1 * t23 * t247 + 0.16e2 / 0.9e1 * t112 * t120 + 0.4e1 / 0.3e1 * t21 * t257)
  t279 = 0.1e1 / t65 / t32
  t303 = -0.3e1 / 0.8e1 * t5 * t261 * t43 * t128 - t5 * t124 * t66 * t128 / 0.2e1 + t5 * t41 * t88 * t128 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t63 * t163 * t128 + 0.10e2 / 0.27e2 * t5 * t85 * t279 * t128 - 0.52978734653547222226666666666666666666666666666666e-1 * t64 * t151 - 0.55660348799006722618936417329765649865544074499297e-2 * t64 * t135 + 0.53513873387421436592592592592592592592592592592591e-2 * t86 * t163 * t52 * t57 + 0.17659578217849074075555555555555555555555555555555e-1 * t86 * t89 * t147 + 0.50600317090006111471760379390696045332312794999360e-3 * t64 * t94 + 0.29378747637215569792283720098476720115805910151254e-4 * t64 * t104 - 0.16866772363335370490586793130232015110770931666453e-3 * t86 * t88 * t71 * t78
  t308 = t51 ** (-0.452e1)
  t310 = t73 ** 2
  t311 = t74 * t44
  t357 = 0.97929158790718565974279066994922400386019700504180e-5 * t86 * t66 * t97 * t103 + 0.59565590337756260370620616543844498761719629871502e-6 * t86 * t43 * t308 * t310 / t46 / t100 / t311 + 0.24723409504988703705777777777777777777777777777778e0 * t64 * t142 + 0.14448745814603787880000000000000000000000000000000e-1 * t5 * t124 * t58 + 0.75900475635009167207640569086044067998469192499042e-3 * t42 * t79 - 0.18553449599668907539645472443255216621848024833099e-2 * t86 * t93 * t134 - 0.16158311200468563385756046054162196063693250583190e-3 * t86 * t98 * t99 / t100 / t74 + 0.13760475119754439758570392062080952327870618417882e-1 * t86 * t72 * t73 / t45 / t100 / r0 + 0.82411365016629012352592592592592592592592592592590e-1 * t86 * t67 * t141 - 0.35024830132067330249851851851851851851851851851853e0 * t86 * t53 * s0 / t46 / t311 + 0.14448745814603787880000000000000000000000000000000e-1 * t42 * t68 - 0.79468101980320833340000000000000000000000000000000e-1 * t42 * t148 - 0.96324972097358585866666666666666666666666666666665e-2 * t64 * t90
  t359 = f.my_piecewise3(t1, 0, t303 + t357)
  t360 = t173 ** 2
  t363 = t181 ** 2
  t369 = t188 ** 2
  t375 = f.my_piecewise5(t14, 0, t10, 0, -t256)
  t379 = f.my_piecewise3(t174, 0, 0.40e2 / 0.81e2 / t176 / t360 * t363 - 0.16e2 / 0.9e1 * t178 * t181 * t188 + 0.4e1 / 0.3e1 * t185 * t369 + 0.16e2 / 0.9e1 * t186 * t192 + 0.4e1 / 0.3e1 * t175 * t375)
  t401 = f.my_piecewise3(t171, 0, -0.3e1 / 0.8e1 * t5 * t379 * t43 * t208 - t5 * t196 * t66 * t208 / 0.2e1 + t5 * t217 * t88 * t208 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t224 * t163 * t208 + 0.10e2 / 0.27e2 * t5 * t230 * t279 * t208)
  d1111 = 0.4e1 * t169 + 0.4e1 * t236 + t6 * (t359 + t401)

  res = {'v4rho4': d1111}
  return res
