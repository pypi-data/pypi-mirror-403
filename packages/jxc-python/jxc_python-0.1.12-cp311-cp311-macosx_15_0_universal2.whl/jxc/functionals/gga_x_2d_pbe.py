"""Generated from gga_x_2d_pbe.mpl."""

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
  _2d_pbe_kappa = 0.4604

  _2d_pbe_mu = 0.354546875

  _2d_pbe_f0 = lambda s: 1 + _2d_pbe_kappa * (1 - _2d_pbe_kappa / (_2d_pbe_kappa + _2d_pbe_mu * s ** 2))

  _2d_pbe_f = lambda x: _2d_pbe_f0(X2S_2D * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, _2d_pbe_f, rs, zeta, xs0, xs1)

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
  _2d_pbe_kappa = 0.4604

  _2d_pbe_mu = 0.354546875

  _2d_pbe_f0 = lambda s: 1 + _2d_pbe_kappa * (1 - _2d_pbe_kappa / (_2d_pbe_kappa + _2d_pbe_mu * s ** 2))

  _2d_pbe_f = lambda x: _2d_pbe_f0(X2S_2D * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, _2d_pbe_f, rs, zeta, xs0, xs1)

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
  _2d_pbe_kappa = 0.4604

  _2d_pbe_mu = 0.354546875

  _2d_pbe_f0 = lambda s: 1 + _2d_pbe_kappa * (1 - _2d_pbe_kappa / (_2d_pbe_kappa + _2d_pbe_mu * s ** 2))

  _2d_pbe_f = lambda x: _2d_pbe_f0(X2S_2D * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, _2d_pbe_f, rs, zeta, xs0, xs1)

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
  t28 = 0.1e1 / jnp.pi
  t30 = r0 ** 2
  t31 = r0 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t34 = 0.1e1 / t32 / t30
  t37 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 * t28 * s0 * t34
  t40 = 0.14604e1 - 0.21196816e0 / t37
  t44 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t40)
  t45 = r1 <= f.p.dens_threshold
  t46 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t47 = 0.1e1 + t46
  t48 = t47 <= f.p.zeta_threshold
  t49 = t47 ** (0.1e1 / 0.3e1)
  t51 = f.my_piecewise3(t48, t22, t49 * t47)
  t54 = r1 ** 2
  t55 = r1 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t58 = 0.1e1 / t56 / t54
  t61 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 * t28 * s2 * t58
  t64 = 0.14604e1 - 0.21196816e0 / t61
  t68 = f.my_piecewise3(t45, 0, -0.3e1 / 0.8e1 * t5 * t51 * t26 * t64)
  t69 = t6 ** 2
  t71 = t16 / t69
  t72 = t7 - t71
  t73 = f.my_piecewise5(t10, 0, t14, 0, t72)
  t76 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t73)
  t81 = t26 ** 2
  t82 = 0.1e1 / t81
  t86 = t5 * t25 * t82 * t40 / 0.8e1
  t89 = t2 / t3 / jnp.pi
  t90 = t89 * t25
  t91 = t37 ** 2
  t93 = t26 / t91
  t102 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t76 * t26 * t40 - t86 + 0.46970405454687499999999999999999999999999999999999e-2 * t90 * t93 * s0 / t32 / t30 / r0)
  t104 = f.my_piecewise5(t14, 0, t10, 0, -t72)
  t107 = f.my_piecewise3(t48, 0, 0.4e1 / 0.3e1 * t49 * t104)
  t115 = t5 * t51 * t82 * t64 / 0.8e1
  t117 = f.my_piecewise3(t45, 0, -0.3e1 / 0.8e1 * t5 * t107 * t26 * t64 - t115)
  vrho_0_ = t44 + t68 + t6 * (t102 + t117)
  t120 = -t7 - t71
  t121 = f.my_piecewise5(t10, 0, t14, 0, t120)
  t124 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t121)
  t130 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t124 * t26 * t40 - t86)
  t132 = f.my_piecewise5(t14, 0, t10, 0, -t120)
  t135 = f.my_piecewise3(t48, 0, 0.4e1 / 0.3e1 * t49 * t132)
  t140 = t89 * t51
  t141 = t61 ** 2
  t143 = t26 / t141
  t152 = f.my_piecewise3(t45, 0, -0.3e1 / 0.8e1 * t5 * t135 * t26 * t64 - t115 + 0.46970405454687499999999999999999999999999999999999e-2 * t140 * t143 * s2 / t56 / t54 / r1)
  vrho_1_ = t44 + t68 + t6 * (t130 + t152)
  t158 = f.my_piecewise3(t1, 0, -0.17613902045507812500000000000000000000000000000000e-2 * t90 * t93 * t34)
  vsigma_0_ = t6 * t158
  vsigma_1_ = 0.0e0
  t162 = f.my_piecewise3(t45, 0, -0.17613902045507812500000000000000000000000000000000e-2 * t140 * t143 * t58)
  vsigma_2_ = t6 * t162
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
  _2d_pbe_kappa = 0.4604

  _2d_pbe_mu = 0.354546875

  _2d_pbe_f0 = lambda s: 1 + _2d_pbe_kappa * (1 - _2d_pbe_kappa / (_2d_pbe_kappa + _2d_pbe_mu * s ** 2))

  _2d_pbe_f = lambda x: _2d_pbe_f0(X2S_2D * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange(f, params, _2d_pbe_f, rs, zeta, xs0, xs1)

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
  t22 = 2 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = r0 ** 2
  t25 = t18 ** 2
  t31 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 / jnp.pi * s0 * t23 / t25 / t24
  t34 = 0.14604e1 - 0.21196816e0 / t31
  t38 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t34)
  t47 = t3 / t4 / jnp.pi * t17
  t51 = t31 ** 2
  t52 = 0.1e1 / t51
  t59 = f.my_piecewise3(t2, 0, -t6 * t17 / t25 * t34 / 0.8e1 + 0.46970405454687499999999999999999999999999999999999e-2 * t47 / t18 / t24 / r0 * t52 * s0 * t23)
  vrho_0_ = 0.2e1 * r0 * t59 + 0.2e1 * t38
  t68 = f.my_piecewise3(t2, 0, -0.17613902045507812500000000000000000000000000000000e-2 * t47 / t18 / t24 * t52 * t23)
  vsigma_0_ = 0.2e1 * r0 * t68
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
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = r0 ** 2
  t32 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 / jnp.pi * s0 * t25 / t19 / t26
  t35 = 0.14604e1 - 0.21196816e0 / t32
  t42 = t3 / t4 / jnp.pi * t17
  t43 = t26 * r0
  t46 = t32 ** 2
  t47 = 0.1e1 / t46
  t48 = 0.1e1 / t18 / t43 * t47
  t49 = s0 * t25
  t54 = f.my_piecewise3(t2, 0, -t6 * t17 / t19 * t35 / 0.8e1 + 0.46970405454687499999999999999999999999999999999999e-2 * t42 * t48 * t49)
  t62 = t26 ** 2
  t69 = jnp.pi ** 2
  t73 = t3 / t4 / t69 * t17
  t77 = 0.1e1 / t46 / t32
  t79 = s0 ** 2
  t85 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t35 / 0.12e2 - 0.14091121636406249999999999999999999999999999999999e-1 * t42 / t18 / t62 * t47 * t49 + 0.11102140314294938151041666666666666666666666666667e-2 * t73 / t62 / t43 * t77 * t79 * t24)
  v2rho2_0_ = 0.2e1 * r0 * t85 + 0.4e1 * t54
  t94 = f.my_piecewise3(t2, 0, -0.17613902045507812500000000000000000000000000000000e-2 * t42 / t18 / t26 * t47 * t25)
  t106 = f.my_piecewise3(t2, 0, 0.41099104772851562500000000000000000000000000000000e-2 * t42 * t48 * t25 - 0.41633026178606018066406250000000000000000000000001e-3 * t73 / t62 / t26 * t77 * t24 * s0)
  v2rhosigma_0_ = 0.2e1 * r0 * t106 + 0.2e1 * t94
  t115 = f.my_piecewise3(t2, 0, 0.15612384816977256774902343750000000000000000000000e-3 * t73 / t62 / r0 * t77 * t24)
  v2sigma2_0_ = 0.2e1 * r0 * t115
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
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = r0 ** 2
  t29 = 0.1e1 / t19 / t27
  t33 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 / jnp.pi * s0 * t26 * t29
  t36 = 0.14604e1 - 0.21196816e0 / t33
  t43 = t3 / t4 / jnp.pi * t17
  t44 = t27 ** 2
  t47 = t33 ** 2
  t48 = 0.1e1 / t47
  t50 = s0 * t26
  t54 = jnp.pi ** 2
  t58 = t3 / t4 / t54 * t17
  t63 = 0.1e1 / t47 / t33
  t65 = s0 ** 2
  t66 = t65 * t25
  t71 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t36 / 0.12e2 - 0.14091121636406249999999999999999999999999999999999e-1 * t43 / t18 / t44 * t48 * t50 + 0.11102140314294938151041666666666666666666666666667e-2 * t58 / t44 / t27 / r0 * t63 * t66)
  t84 = t44 ** 2
  t98 = t47 ** 2
  t106 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t29 * t36 + 0.60017740303211805555555555555555555555555555555552e-1 * t43 / t18 / t44 / r0 * t48 * t50 - 0.11102140314294938151041666666666666666666666666667e-1 * t58 / t84 * t63 * t66 + 0.39362291542447881497701009114583333333333333333336e-3 * t3 / t4 / t54 / jnp.pi * t17 / t19 / t84 / t27 / t98 * t65 * s0)
  v3rho3_0_ = 0.2e1 * r0 * t106 + 0.6e1 * t71

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
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t31 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 / jnp.pi * s0 * t27 * t22
  t34 = 0.14604e1 - 0.21196816e0 / t31
  t41 = t3 / t4 / jnp.pi * t17
  t42 = t18 ** 2
  t46 = t31 ** 2
  t47 = 0.1e1 / t46
  t49 = s0 * t27
  t53 = jnp.pi ** 2
  t57 = t3 / t4 / t53 * t17
  t58 = t42 ** 2
  t61 = 0.1e1 / t46 / t31
  t63 = s0 ** 2
  t64 = t63 * t26
  t72 = t3 / t4 / t53 / jnp.pi * t17
  t76 = t46 ** 2
  t77 = 0.1e1 / t76
  t79 = t63 * s0
  t84 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t34 + 0.60017740303211805555555555555555555555555555555552e-1 * t41 / t19 / t42 / r0 * t47 * t49 - 0.11102140314294938151041666666666666666666666666667e-1 * t57 / t58 * t61 * t64 + 0.39362291542447881497701009114583333333333333333336e-3 * t72 / t20 / t58 / t18 * t77 * t79)
  t86 = t18 * r0
  t93 = t42 * t18
  t113 = t53 ** 2
  t124 = t63 ** 2
  t130 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 / t20 / t86 * t34 - 0.31835497030399305555555555555555555555555555555553e0 * t41 / t19 / t93 * t47 * t49 + 0.10300319069373637062355324074074074074074074074074e0 * t57 / t58 / r0 * t61 * t64 - 0.81348735854392288428582085503472222222222222222228e-2 * t72 / t20 / t58 / t86 * t77 * t79 + 0.93038516394758841569201416439480251736111111111116e-4 * t3 / t4 / t113 * t17 / t19 / t58 / t93 / t76 / t31 * t124 * t27)
  v4rho4_0_ = 0.2e1 * r0 * t130 + 0.8e1 * t84

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
  t32 = 0.1e1 / jnp.pi
  t34 = r0 ** 2
  t35 = r0 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t41 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 * t32 * s0 / t36 / t34
  t44 = 0.14604e1 - 0.21196816e0 / t41
  t48 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t49 = t48 * f.p.zeta_threshold
  t51 = f.my_piecewise3(t20, t49, t21 * t19)
  t52 = t30 ** 2
  t53 = 0.1e1 / t52
  t57 = t5 * t51 * t53 * t44 / 0.8e1
  t60 = t2 / t3 / jnp.pi
  t61 = t60 * t51
  t62 = t41 ** 2
  t63 = 0.1e1 / t62
  t64 = t30 * t63
  t65 = t34 * r0
  t68 = s0 / t36 / t65
  t69 = t64 * t68
  t73 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t44 - t57 + 0.46970405454687499999999999999999999999999999999999e-2 * t61 * t69)
  t75 = r1 <= f.p.dens_threshold
  t76 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t77 = 0.1e1 + t76
  t78 = t77 <= f.p.zeta_threshold
  t79 = t77 ** (0.1e1 / 0.3e1)
  t81 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t84 = f.my_piecewise3(t78, 0, 0.4e1 / 0.3e1 * t79 * t81)
  t87 = r1 ** 2
  t88 = r1 ** (0.1e1 / 0.3e1)
  t89 = t88 ** 2
  t94 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 * t32 * s2 / t89 / t87
  t97 = 0.14604e1 - 0.21196816e0 / t94
  t102 = f.my_piecewise3(t78, t49, t79 * t77)
  t106 = t5 * t102 * t53 * t97 / 0.8e1
  t108 = f.my_piecewise3(t75, 0, -0.3e1 / 0.8e1 * t5 * t84 * t30 * t97 - t106)
  t110 = t21 ** 2
  t111 = 0.1e1 / t110
  t112 = t26 ** 2
  t117 = t16 / t22 / t6
  t119 = -0.2e1 * t23 + 0.2e1 * t117
  t120 = f.my_piecewise5(t10, 0, t14, 0, t119)
  t124 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t111 * t112 + 0.4e1 / 0.3e1 * t21 * t120)
  t131 = t5 * t29 * t53 * t44
  t137 = 0.1e1 / t52 / t6
  t141 = t5 * t51 * t137 * t44 / 0.12e2
  t144 = t61 * t53 * t63 * t68
  t146 = jnp.pi ** 2
  t149 = t2 / t3 / t146
  t154 = s0 ** 2
  t155 = t34 ** 2
  t170 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t124 * t30 * t44 - t131 / 0.4e1 + 0.93940810909374999999999999999999999999999999999998e-2 * t60 * t29 * t69 + t141 + 0.31313603636458333333333333333333333333333333333332e-2 * t144 + 0.55510701571474690755208333333333333333333333333334e-3 * t149 * t51 * t30 / t62 / t41 * t154 / t35 / t155 / t65 - 0.17222482000052083333333333333333333333333333333333e-1 * t61 * t64 * s0 / t36 / t155)
  t171 = t79 ** 2
  t172 = 0.1e1 / t171
  t173 = t81 ** 2
  t177 = f.my_piecewise5(t14, 0, t10, 0, -t119)
  t181 = f.my_piecewise3(t78, 0, 0.4e1 / 0.9e1 * t172 * t173 + 0.4e1 / 0.3e1 * t79 * t177)
  t188 = t5 * t84 * t53 * t97
  t193 = t5 * t102 * t137 * t97 / 0.12e2
  t195 = f.my_piecewise3(t75, 0, -0.3e1 / 0.8e1 * t5 * t181 * t30 * t97 - t188 / 0.4e1 + t193)
  d11 = 0.2e1 * t73 + 0.2e1 * t108 + t6 * (t170 + t195)
  t198 = -t7 - t24
  t199 = f.my_piecewise5(t10, 0, t14, 0, t198)
  t202 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t199)
  t208 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t202 * t30 * t44 - t57)
  t210 = f.my_piecewise5(t14, 0, t10, 0, -t198)
  t213 = f.my_piecewise3(t78, 0, 0.4e1 / 0.3e1 * t79 * t210)
  t218 = t60 * t102
  t219 = t94 ** 2
  t220 = 0.1e1 / t219
  t221 = t30 * t220
  t222 = t87 * r1
  t225 = s2 / t89 / t222
  t226 = t221 * t225
  t230 = f.my_piecewise3(t75, 0, -0.3e1 / 0.8e1 * t5 * t213 * t30 * t97 - t106 + 0.46970405454687499999999999999999999999999999999999e-2 * t218 * t226)
  t234 = 0.2e1 * t117
  t235 = f.my_piecewise5(t10, 0, t14, 0, t234)
  t239 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t111 * t199 * t26 + 0.4e1 / 0.3e1 * t21 * t235)
  t246 = t5 * t202 * t53 * t44
  t254 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t239 * t30 * t44 - t246 / 0.8e1 + 0.46970405454687499999999999999999999999999999999999e-2 * t60 * t202 * t69 - t131 / 0.8e1 + t141 + 0.15656801818229166666666666666666666666666666666666e-2 * t144)
  t258 = f.my_piecewise5(t14, 0, t10, 0, -t234)
  t262 = f.my_piecewise3(t78, 0, 0.4e1 / 0.9e1 * t172 * t210 * t81 + 0.4e1 / 0.3e1 * t79 * t258)
  t269 = t5 * t213 * t53 * t97
  t277 = t218 * t53 * t220 * t225
  t280 = f.my_piecewise3(t75, 0, -0.3e1 / 0.8e1 * t5 * t262 * t30 * t97 - t269 / 0.8e1 - t188 / 0.8e1 + t193 + 0.46970405454687499999999999999999999999999999999999e-2 * t60 * t84 * t226 + 0.15656801818229166666666666666666666666666666666666e-2 * t277)
  d12 = t73 + t108 + t208 + t230 + t6 * (t254 + t280)
  t285 = t199 ** 2
  t289 = 0.2e1 * t23 + 0.2e1 * t117
  t290 = f.my_piecewise5(t10, 0, t14, 0, t289)
  t294 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t111 * t285 + 0.4e1 / 0.3e1 * t21 * t290)
  t301 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t294 * t30 * t44 - t246 / 0.4e1 + t141)
  t302 = t210 ** 2
  t306 = f.my_piecewise5(t14, 0, t10, 0, -t289)
  t310 = f.my_piecewise3(t78, 0, 0.4e1 / 0.9e1 * t172 * t302 + 0.4e1 / 0.3e1 * t79 * t306)
  t324 = s2 ** 2
  t325 = t87 ** 2
  t340 = f.my_piecewise3(t75, 0, -0.3e1 / 0.8e1 * t5 * t310 * t30 * t97 - t269 / 0.4e1 + 0.93940810909374999999999999999999999999999999999998e-2 * t60 * t213 * t226 + t193 + 0.31313603636458333333333333333333333333333333333332e-2 * t277 + 0.55510701571474690755208333333333333333333333333334e-3 * t149 * t102 * t30 / t219 / t94 * t324 / t88 / t325 / t222 - 0.17222482000052083333333333333333333333333333333333e-1 * t218 * t221 * s2 / t89 / t325)
  d22 = 0.2e1 * t208 + 0.2e1 * t230 + t6 * (t301 + t340)
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
  t44 = 0.1e1 / jnp.pi
  t46 = r0 ** 2
  t47 = r0 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t53 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 * t44 * s0 / t48 / t46
  t56 = 0.14604e1 - 0.21196816e0 / t53
  t62 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t63 = t42 ** 2
  t64 = 0.1e1 / t63
  t71 = t2 / t3 / jnp.pi
  t72 = t71 * t62
  t73 = t53 ** 2
  t74 = 0.1e1 / t73
  t75 = t42 * t74
  t76 = t46 * r0
  t79 = s0 / t48 / t76
  t80 = t75 * t79
  t83 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t84 = t83 * f.p.zeta_threshold
  t86 = f.my_piecewise3(t20, t84, t21 * t19)
  t88 = 0.1e1 / t63 / t6
  t93 = t71 * t86
  t94 = t64 * t74
  t95 = t94 * t79
  t98 = jnp.pi ** 2
  t101 = t2 / t3 / t98
  t102 = t101 * t86
  t104 = 0.1e1 / t73 / t53
  t105 = t42 * t104
  t106 = s0 ** 2
  t107 = t46 ** 2
  t111 = t106 / t47 / t107 / t76
  t112 = t105 * t111
  t117 = s0 / t48 / t107
  t118 = t75 * t117
  t122 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t56 - t5 * t62 * t64 * t56 / 0.4e1 + 0.93940810909374999999999999999999999999999999999998e-2 * t72 * t80 + t5 * t86 * t88 * t56 / 0.12e2 + 0.31313603636458333333333333333333333333333333333332e-2 * t93 * t95 + 0.55510701571474690755208333333333333333333333333334e-3 * t102 * t112 - 0.17222482000052083333333333333333333333333333333333e-1 * t93 * t118)
  t124 = r1 <= f.p.dens_threshold
  t125 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t126 = 0.1e1 + t125
  t127 = t126 <= f.p.zeta_threshold
  t128 = t126 ** (0.1e1 / 0.3e1)
  t129 = t128 ** 2
  t130 = 0.1e1 / t129
  t132 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t133 = t132 ** 2
  t137 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t141 = f.my_piecewise3(t127, 0, 0.4e1 / 0.9e1 * t130 * t133 + 0.4e1 / 0.3e1 * t128 * t137)
  t144 = r1 ** 2
  t145 = r1 ** (0.1e1 / 0.3e1)
  t146 = t145 ** 2
  t154 = 0.14604e1 - 0.21196816e0 / (0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 * t44 * s2 / t146 / t144)
  t160 = f.my_piecewise3(t127, 0, 0.4e1 / 0.3e1 * t128 * t132)
  t166 = f.my_piecewise3(t127, t84, t128 * t126)
  t172 = f.my_piecewise3(t124, 0, -0.3e1 / 0.8e1 * t5 * t141 * t42 * t154 - t5 * t160 * t64 * t154 / 0.4e1 + t5 * t166 * t88 * t154 / 0.12e2)
  t195 = t73 ** 2
  t199 = t107 ** 2
  t214 = t24 ** 2
  t218 = 0.6e1 * t33 - 0.6e1 * t16 / t214
  t219 = f.my_piecewise5(t10, 0, t14, 0, t218)
  t223 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t219)
  t255 = 0.1e1 / t63 / t24
  t260 = 0.14091121636406250000000000000000000000000000000000e-1 * t71 * t41 * t80 + 0.93940810909374999999999999999999999999999999999997e-2 * t72 * t95 + 0.16653210471442407226562500000000000000000000000000e-2 * t101 * t62 * t112 - 0.31313603636458333333333333333333333333333333333332e-2 * t93 * t88 * t74 * t79 + 0.55510701571474690755208333333333333333333333333333e-3 * t102 * t64 * t104 * t111 + 0.98405728856119703744252522786458333333333333333335e-4 * t2 / t3 / t98 / jnp.pi * t86 * t42 / t195 * t106 * s0 / t199 / t76 - 0.3e1 / 0.8e1 * t5 * t223 * t42 * t56 - 0.17222482000052083333333333333333333333333333333332e-1 * t93 * t94 * t117 - 0.61061771728622159830729166666666666666666666666667e-2 * t102 * t105 * t106 / t47 / t199 + 0.80371582666909722222222222222222222222222222222221e-1 * t93 * t75 * s0 / t48 / t107 / r0 - 0.51667446000156249999999999999999999999999999999999e-1 * t72 * t118 - 0.3e1 / 0.8e1 * t5 * t41 * t64 * t56 + t5 * t62 * t88 * t56 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t86 * t255 * t56
  t261 = f.my_piecewise3(t1, 0, t260)
  t271 = f.my_piecewise5(t14, 0, t10, 0, -t218)
  t275 = f.my_piecewise3(t127, 0, -0.8e1 / 0.27e2 / t129 / t126 * t133 * t132 + 0.4e1 / 0.3e1 * t130 * t132 * t137 + 0.4e1 / 0.3e1 * t128 * t271)
  t293 = f.my_piecewise3(t124, 0, -0.3e1 / 0.8e1 * t5 * t275 * t42 * t154 - 0.3e1 / 0.8e1 * t5 * t141 * t64 * t154 + t5 * t160 * t88 * t154 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t166 * t255 * t154)
  d111 = 0.3e1 * t122 + 0.3e1 * t172 + t6 * (t261 + t293)

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
  t6 = t2 / t3 / jnp.pi
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
  t24 = 0.1e1 / t23
  t25 = t7 ** 2
  t26 = 0.1e1 / t25
  t28 = -t17 * t26 + t8
  t29 = f.my_piecewise5(t11, 0, t15, 0, t28)
  t30 = t29 ** 2
  t33 = t25 * t7
  t34 = 0.1e1 / t33
  t37 = 0.2e1 * t17 * t34 - 0.2e1 * t26
  t38 = f.my_piecewise5(t11, 0, t15, 0, t37)
  t42 = f.my_piecewise3(t21, 0, 0.4e1 / 0.9e1 * t24 * t30 + 0.4e1 / 0.3e1 * t22 * t38)
  t43 = t6 * t42
  t44 = t7 ** (0.1e1 / 0.3e1)
  t45 = 0.1e1 / jnp.pi
  t47 = r0 ** 2
  t48 = r0 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t54 = 0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 * t45 * s0 / t49 / t47
  t55 = t54 ** 2
  t56 = 0.1e1 / t55
  t57 = t44 * t56
  t58 = t47 * r0
  t61 = s0 / t49 / t58
  t62 = t57 * t61
  t67 = f.my_piecewise3(t21, 0, 0.4e1 / 0.3e1 * t22 * t29)
  t68 = t6 * t67
  t69 = t44 ** 2
  t70 = 0.1e1 / t69
  t71 = t70 * t56
  t72 = t71 * t61
  t75 = jnp.pi ** 2
  t78 = t2 / t3 / t75
  t79 = t78 * t67
  t81 = 0.1e1 / t55 / t54
  t82 = t44 * t81
  t83 = s0 ** 2
  t84 = t47 ** 2
  t88 = t83 / t48 / t84 / t58
  t89 = t82 * t88
  t92 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t93 = t92 * f.p.zeta_threshold
  t95 = f.my_piecewise3(t21, t93, t22 * t20)
  t96 = t6 * t95
  t98 = 0.1e1 / t69 / t7
  t99 = t98 * t56
  t100 = t99 * t61
  t103 = t78 * t95
  t104 = t70 * t81
  t105 = t104 * t88
  t111 = t2 / t3 / t75 / jnp.pi
  t112 = t111 * t95
  t113 = t55 ** 2
  t114 = 0.1e1 / t113
  t115 = t44 * t114
  t116 = t83 * s0
  t117 = t84 ** 2
  t120 = t116 / t117 / t58
  t121 = t115 * t120
  t125 = t2 / t3
  t127 = 0.1e1 / t23 / t20
  t131 = t24 * t29
  t134 = t25 ** 2
  t135 = 0.1e1 / t134
  t138 = -0.6e1 * t17 * t135 + 0.6e1 * t34
  t139 = f.my_piecewise5(t11, 0, t15, 0, t138)
  t143 = f.my_piecewise3(t21, 0, -0.8e1 / 0.27e2 * t127 * t30 * t29 + 0.4e1 / 0.3e1 * t131 * t38 + 0.4e1 / 0.3e1 * t22 * t139)
  t147 = 0.14604e1 - 0.21196816e0 / t54
  t153 = t83 / t48 / t117
  t154 = t82 * t153
  t160 = s0 / t49 / t84 / r0
  t161 = t57 * t160
  t166 = s0 / t49 / t84
  t167 = t57 * t166
  t170 = t71 * t166
  t182 = 0.1e1 / t69 / t25
  t187 = 0.14091121636406250000000000000000000000000000000000e-1 * t43 * t62 + 0.93940810909374999999999999999999999999999999999997e-2 * t68 * t72 + 0.16653210471442407226562500000000000000000000000000e-2 * t79 * t89 - 0.31313603636458333333333333333333333333333333333332e-2 * t96 * t100 + 0.55510701571474690755208333333333333333333333333333e-3 * t103 * t105 + 0.98405728856119703744252522786458333333333333333335e-4 * t112 * t121 - 0.3e1 / 0.8e1 * t125 * t143 * t44 * t147 - 0.61061771728622159830729166666666666666666666666667e-2 * t103 * t154 + 0.80371582666909722222222222222222222222222222222221e-1 * t96 * t161 - 0.51667446000156249999999999999999999999999999999999e-1 * t68 * t167 - 0.17222482000052083333333333333333333333333333333332e-1 * t96 * t170 - 0.3e1 / 0.8e1 * t125 * t42 * t70 * t147 + t125 * t67 * t98 * t147 / 0.4e1 - 0.5e1 / 0.36e2 * t125 * t95 * t182 * t147
  t188 = f.my_piecewise3(t1, 0, t187)
  t190 = r1 <= f.p.dens_threshold
  t191 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t192 = 0.1e1 + t191
  t193 = t192 <= f.p.zeta_threshold
  t194 = t192 ** (0.1e1 / 0.3e1)
  t195 = t194 ** 2
  t197 = 0.1e1 / t195 / t192
  t199 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t200 = t199 ** 2
  t204 = 0.1e1 / t195
  t205 = t204 * t199
  t207 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t211 = f.my_piecewise5(t15, 0, t11, 0, -t138)
  t215 = f.my_piecewise3(t193, 0, -0.8e1 / 0.27e2 * t197 * t200 * t199 + 0.4e1 / 0.3e1 * t205 * t207 + 0.4e1 / 0.3e1 * t194 * t211)
  t218 = r1 ** 2
  t219 = r1 ** (0.1e1 / 0.3e1)
  t220 = t219 ** 2
  t228 = 0.14604e1 - 0.21196816e0 / (0.4604e0 + 0.22159179687500000000000000000000000000000000000000e-1 * t45 * s2 / t220 / t218)
  t237 = f.my_piecewise3(t193, 0, 0.4e1 / 0.9e1 * t204 * t200 + 0.4e1 / 0.3e1 * t194 * t207)
  t244 = f.my_piecewise3(t193, 0, 0.4e1 / 0.3e1 * t194 * t199)
  t250 = f.my_piecewise3(t193, t93, t194 * t192)
  t256 = f.my_piecewise3(t190, 0, -0.3e1 / 0.8e1 * t125 * t215 * t44 * t228 - 0.3e1 / 0.8e1 * t125 * t237 * t70 * t228 + t125 * t244 * t98 * t228 / 0.4e1 - 0.5e1 / 0.36e2 * t125 * t250 * t182 * t228)
  t258 = t20 ** 2
  t261 = t30 ** 2
  t267 = t38 ** 2
  t276 = -0.24e2 * t135 + 0.24e2 * t17 / t134 / t7
  t277 = f.my_piecewise5(t11, 0, t15, 0, t276)
  t281 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t23 / t258 * t261 - 0.16e2 / 0.9e1 * t127 * t30 * t38 + 0.4e1 / 0.3e1 * t24 * t267 + 0.16e2 / 0.9e1 * t131 * t139 + 0.4e1 / 0.3e1 * t22 * t277)
  t299 = 0.1e1 / t69 / t33
  t308 = t75 ** 2
  t316 = t83 ** 2
  t317 = t84 * t47
  t337 = -0.3e1 / 0.8e1 * t125 * t281 * t44 * t147 - t125 * t143 * t70 * t147 / 0.2e1 + t125 * t42 * t98 * t147 / 0.2e1 - 0.5e1 / 0.9e1 * t125 * t67 * t182 * t147 + 0.10e2 / 0.27e2 * t125 * t95 * t299 * t147 + 0.13120763847482627165900336371527777777777777777778e-3 * t112 * t70 * t114 * t120 + 0.23259629098689710392300354109870062934027777777778e-4 * t2 / t3 / t308 * t95 * t44 / t113 / t54 * t316 / t49 / t117 / t317 + 0.32148633066763888888888888888888888888888888888888e0 * t68 * t161 + 0.18788162181875000000000000000000000000000000000000e-1 * t6 * t143 * t62 + 0.33306420942884814453125000000000000000000000000000e-2 * t78 * t42 * t89 + 0.18788162181875000000000000000000000000000000000000e-1 * t43 * t72 - 0.10333489200031250000000000000000000000000000000000e0 * t43 * t167
  t385 = -0.12525441454583333333333333333333333333333333333333e-1 * t68 * t100 - 0.68889928000208333333333333333333333333333333333331e-1 * t68 * t170 - 0.24424708691448863932291666666666666666666666666667e-1 * t79 * t154 + 0.69585785858796296296296296296296296296296296296294e-2 * t96 * t182 * t56 * t61 + 0.22963309333402777777777777777777777777777777777776e-1 * t96 * t99 * t166 - 0.81415695638162879774305555555555555555555555555555e-2 * t103 * t104 * t153 - 0.21649260348346334823735555013020833333333333333334e-2 * t112 * t115 * t116 / t117 / t84 + 0.60383307598304135832609953703703703703703703703704e-1 * t103 * t82 * t83 / t48 / t117 / r0 + 0.10716211022254629629629629629629629629629629629629e0 * t96 * t71 * t160 - 0.45543896844582175925925925925925925925925925925925e0 * t96 * t57 * s0 / t49 / t317 + 0.22204280628589876302083333333333333333333333333333e-2 * t79 * t105 + 0.39362291542447881497701009114583333333333333333334e-3 * t111 * t67 * t121 - 0.74014268761966254340277777777777777777777777777777e-3 * t103 * t98 * t81 * t88
  t387 = f.my_piecewise3(t1, 0, t337 + t385)
  t388 = t192 ** 2
  t391 = t200 ** 2
  t397 = t207 ** 2
  t403 = f.my_piecewise5(t15, 0, t11, 0, -t276)
  t407 = f.my_piecewise3(t193, 0, 0.40e2 / 0.81e2 / t195 / t388 * t391 - 0.16e2 / 0.9e1 * t197 * t200 * t207 + 0.4e1 / 0.3e1 * t204 * t397 + 0.16e2 / 0.9e1 * t205 * t211 + 0.4e1 / 0.3e1 * t194 * t403)
  t429 = f.my_piecewise3(t190, 0, -0.3e1 / 0.8e1 * t125 * t407 * t44 * t228 - t125 * t215 * t70 * t228 / 0.2e1 + t125 * t237 * t98 * t228 / 0.2e1 - 0.5e1 / 0.9e1 * t125 * t244 * t182 * t228 + 0.10e2 / 0.27e2 * t125 * t250 * t299 * t228)
  d1111 = 0.4e1 * t188 + 0.4e1 * t256 + t7 * (t387 + t429)

  res = {'v4rho4': d1111}
  return res
