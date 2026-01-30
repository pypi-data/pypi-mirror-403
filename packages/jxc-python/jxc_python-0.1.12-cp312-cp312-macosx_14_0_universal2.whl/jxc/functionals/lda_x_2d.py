"""Generated from lda_x_2d.mpl."""

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
  ax = -4 / 3 * jnp.sqrt(2) / jnp.pi

  functional_body = lambda rs, z: ax * f.f_zeta_2d(z) / rs

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  ax = -4 / 3 * jnp.sqrt(2) / jnp.pi

  functional_body = lambda rs, z: ax * f.f_zeta_2d(z) / rs

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  ax = -4 / 3 * jnp.sqrt(2) / jnp.pi

  functional_body = lambda rs, z: ax * f.f_zeta_2d(z) / rs

  t1 = jnp.sqrt(0.2e1)
  t2 = 0.1e1 / jnp.pi
  t4 = r0 - r1
  t5 = r0 + r1
  t6 = 0.1e1 / t5
  t7 = t4 * t6
  t8 = 0.1e1 + t7
  t9 = t8 <= f.p.zeta_threshold
  t10 = jnp.sqrt(f.p.zeta_threshold)
  t11 = t10 * f.p.zeta_threshold
  t12 = jnp.sqrt(t8)
  t14 = f.my_piecewise3(t9, t11, t12 * t8)
  t15 = 0.1e1 - t7
  t16 = t15 <= f.p.zeta_threshold
  t17 = jnp.sqrt(t15)
  t19 = f.my_piecewise3(t16, t11, t17 * t15)
  t23 = 3 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = t2 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = t5 ** (0.1e1 / 0.3e1)
  t33 = 0.16e2 / 0.27e2 * t1 * t2 * (t14 / 0.2e1 + t19 / 0.2e1) * t24 * t26 * t28 * t29
  t36 = t29 * t5 * t1 * t2
  t37 = t5 ** 2
  t39 = t4 / t37
  t40 = t6 - t39
  t43 = f.my_piecewise3(t9, 0, 0.3e1 / 0.2e1 * t12 * t40)
  t47 = f.my_piecewise3(t16, 0, -0.3e1 / 0.2e1 * t17 * t40)
  t51 = t26 * t28
  vrho_0_ = -t33 - 0.4e1 / 0.9e1 * t36 * (t43 / 0.2e1 + t47 / 0.2e1) * t24 * t51
  t55 = -t6 - t39
  t58 = f.my_piecewise3(t9, 0, 0.3e1 / 0.2e1 * t12 * t55)
  t62 = f.my_piecewise3(t16, 0, -0.3e1 / 0.2e1 * t17 * t55)
  vrho_1_ = -t33 - 0.4e1 / 0.9e1 * t36 * (t58 / 0.2e1 + t62 / 0.2e1) * t24 * t51
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  ax = -4 / 3 * jnp.sqrt(2) / jnp.pi

  functional_body = lambda rs, z: ax * f.f_zeta_2d(z) / rs

  t1 = jnp.sqrt(0.2e1)
  t2 = 0.1e1 / jnp.pi
  t5 = jnp.sqrt(f.p.zeta_threshold)
  t7 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t5 * f.p.zeta_threshold, 1)
  t9 = 3 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = t2 ** (0.1e1 / 0.3e1)
  t14 = 4 ** (0.1e1 / 0.3e1)
  t15 = r0 ** (0.1e1 / 0.3e1)
  vrho_0_ = -0.16e2 / 0.27e2 * t1 * t2 * t7 * t10 / t11 * t14 * t15
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t4 = jnp.sqrt(0.2e1)
  t6 = 0.1e1 / jnp.pi
  t9 = jnp.sqrt(f.p.zeta_threshold)
  t11 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t9 * f.p.zeta_threshold, 1)
  t12 = 3 ** (0.1e1 / 0.3e1)
  t13 = t12 ** 2
  t15 = t6 ** (0.1e1 / 0.3e1)
  t17 = 4 ** (0.1e1 / 0.3e1)
  v2rho2_0_ = -0.16e2 / 0.81e2 / t2 * t4 * t6 * t11 * t13 / t15 * t17
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t5 = jnp.sqrt(0.2e1)
  t7 = 0.1e1 / jnp.pi
  t10 = jnp.sqrt(f.p.zeta_threshold)
  t12 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t10 * f.p.zeta_threshold, 1)
  t13 = 3 ** (0.1e1 / 0.3e1)
  t14 = t13 ** 2
  t16 = t7 ** (0.1e1 / 0.3e1)
  t18 = 4 ** (0.1e1 / 0.3e1)
  v3rho3_0_ = 0.32e2 / 0.243e3 / t2 / r0 * t5 * t7 * t12 * t14 / t16 * t18

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** 2
  t2 = r0 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t6 = jnp.sqrt(0.2e1)
  t8 = 0.1e1 / jnp.pi
  t11 = jnp.sqrt(f.p.zeta_threshold)
  t13 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t11 * f.p.zeta_threshold, 1)
  t14 = 3 ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t8 ** (0.1e1 / 0.3e1)
  t19 = 4 ** (0.1e1 / 0.3e1)
  v4rho4_0_ = -0.160e3 / 0.729e3 / t3 / t1 * t6 * t8 * t13 * t15 / t17 * t19

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t5 = jnp.sqrt(0.2e1)
  t7 = 0.1e1 / jnp.pi
  t9 = r0 - r1
  t10 = 0.1e1 / t1
  t11 = t9 * t10
  t12 = 0.1e1 + t11
  t13 = t12 <= f.p.zeta_threshold
  t14 = jnp.sqrt(f.p.zeta_threshold)
  t15 = t14 * f.p.zeta_threshold
  t16 = jnp.sqrt(t12)
  t18 = f.my_piecewise3(t13, t15, t16 * t12)
  t19 = 0.1e1 - t11
  t20 = t19 <= f.p.zeta_threshold
  t21 = jnp.sqrt(t19)
  t23 = f.my_piecewise3(t20, t15, t21 * t19)
  t26 = 3 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t29 = t7 ** (0.1e1 / 0.3e1)
  t31 = 4 ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t29 * t31
  t35 = 0.16e2 / 0.81e2 / t3 * t5 * t7 * (t18 / 0.2e1 + t23 / 0.2e1) * t27 * t32
  t37 = t2 * t5 * t7
  t38 = t1 ** 2
  t39 = 0.1e1 / t38
  t40 = t9 * t39
  t41 = t10 - t40
  t44 = f.my_piecewise3(t13, 0, 0.3e1 / 0.2e1 * t16 * t41)
  t45 = -t41
  t48 = f.my_piecewise3(t20, 0, 0.3e1 / 0.2e1 * t21 * t45)
  t53 = t37 * (t44 / 0.2e1 + t48 / 0.2e1) * t27 * t32
  t57 = t2 * t1 * t5 * t7
  t58 = 0.1e1 / t16
  t59 = t41 ** 2
  t63 = 0.1e1 / t38 / t1
  t64 = t9 * t63
  t66 = -0.2e1 * t39 + 0.2e1 * t64
  t70 = f.my_piecewise3(t13, 0, 0.3e1 / 0.4e1 * t58 * t59 + 0.3e1 / 0.2e1 * t16 * t66)
  t71 = 0.1e1 / t21
  t72 = t45 ** 2
  t79 = f.my_piecewise3(t20, 0, 0.3e1 / 0.4e1 * t71 * t72 - 0.3e1 / 0.2e1 * t21 * t66)
  d11 = -t35 - 0.32e2 / 0.27e2 * t53 - 0.4e1 / 0.9e1 * t57 * (t70 / 0.2e1 + t79 / 0.2e1) * t27 * t32
  t87 = -t10 - t40
  t90 = f.my_piecewise3(t13, 0, 0.3e1 / 0.2e1 * t16 * t87)
  t91 = -t87
  t94 = f.my_piecewise3(t20, 0, 0.3e1 / 0.2e1 * t21 * t91)
  t99 = t37 * (t90 / 0.2e1 + t94 / 0.2e1) * t27 * t32
  t108 = f.my_piecewise3(t13, 0, 0.3e1 / 0.4e1 * t58 * t87 * t41 + 0.3e1 * t16 * t9 * t63)
  t116 = f.my_piecewise3(t20, 0, 0.3e1 / 0.4e1 * t71 * t91 * t45 - 0.3e1 * t21 * t9 * t63)
  d12 = -t35 - 0.16e2 / 0.27e2 * t53 - 0.16e2 / 0.27e2 * t99 - 0.4e1 / 0.9e1 * t57 * (t108 / 0.2e1 + t116 / 0.2e1) * t27 * t32
  t124 = t87 ** 2
  t128 = 0.2e1 * t39 + 0.2e1 * t64
  t132 = f.my_piecewise3(t13, 0, 0.3e1 / 0.4e1 * t58 * t124 + 0.3e1 / 0.2e1 * t16 * t128)
  t133 = t91 ** 2
  t140 = f.my_piecewise3(t20, 0, 0.3e1 / 0.4e1 * t71 * t133 - 0.3e1 / 0.2e1 * t21 * t128)
  d22 = -t35 - 0.32e2 / 0.27e2 * t99 - 0.4e1 / 0.9e1 * t57 * (t132 / 0.2e1 + t140 / 0.2e1) * t27 * t32
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t6 = jnp.sqrt(0.2e1)
  t8 = 0.1e1 / jnp.pi
  t10 = r0 - r1
  t11 = 0.1e1 / t1
  t12 = t10 * t11
  t13 = 0.1e1 + t12
  t14 = t13 <= f.p.zeta_threshold
  t15 = jnp.sqrt(f.p.zeta_threshold)
  t16 = t15 * f.p.zeta_threshold
  t17 = jnp.sqrt(t13)
  t18 = t17 * t13
  t19 = f.my_piecewise3(t14, t16, t18)
  t20 = 0.1e1 - t12
  t21 = t20 <= f.p.zeta_threshold
  t22 = jnp.sqrt(t20)
  t23 = t22 * t20
  t24 = f.my_piecewise3(t21, t16, t23)
  t27 = 3 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t30 = t8 ** (0.1e1 / 0.3e1)
  t32 = 4 ** (0.1e1 / 0.3e1)
  t33 = 0.1e1 / t30 * t32
  t40 = t1 ** 2
  t41 = 0.1e1 / t40
  t43 = -t10 * t41 + t11
  t46 = f.my_piecewise3(t14, 0, 0.3e1 / 0.2e1 * t17 * t43)
  t47 = -t43
  t50 = f.my_piecewise3(t21, 0, 0.3e1 / 0.2e1 * t22 * t47)
  t59 = 0.1e1 / t17
  t60 = t43 ** 2
  t64 = 0.1e1 / t40 / t1
  t67 = 0.2e1 * t10 * t64 - 0.2e1 * t41
  t71 = f.my_piecewise3(t14, 0, 0.3e1 / 0.4e1 * t59 * t60 + 0.3e1 / 0.2e1 * t17 * t67)
  t72 = 0.1e1 / t22
  t73 = t47 ** 2
  t76 = -t67
  t80 = f.my_piecewise3(t21, 0, 0.3e1 / 0.4e1 * t72 * t73 + 0.3e1 / 0.2e1 * t22 * t76)
  t97 = t40 ** 2
  t101 = 0.6e1 * t64 - 0.6e1 * t10 / t97
  t105 = f.my_piecewise3(t14, 0, -0.3e1 / 0.8e1 / t18 * t60 * t43 + 0.9e1 / 0.4e1 * t59 * t43 * t67 + 0.3e1 / 0.2e1 * t17 * t101)
  t117 = f.my_piecewise3(t21, 0, -0.3e1 / 0.8e1 / t23 * t73 * t47 + 0.9e1 / 0.4e1 * t72 * t47 * t76 - 0.3e1 / 0.2e1 * t22 * t101)
  d111 = 0.32e2 / 0.243e3 / t3 / t1 * t6 * t8 * (t19 / 0.2e1 + t24 / 0.2e1) * t28 * t33 - 0.16e2 / 0.27e2 / t3 * t6 * t8 * (t46 / 0.2e1 + t50 / 0.2e1) * t28 * t33 - 0.16e2 / 0.9e1 * t2 * t6 * t8 * (t71 / 0.2e1 + t80 / 0.2e1) * t28 * t33 - 0.4e1 / 0.9e1 * t2 * t1 * t6 * t8 * (t105 / 0.2e1 + t117 / 0.2e1) * t28 * t33

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** 2
  t3 = t1 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t7 = jnp.sqrt(0.2e1)
  t9 = 0.1e1 / jnp.pi
  t11 = r0 - r1
  t12 = 0.1e1 / t1
  t13 = t11 * t12
  t14 = 0.1e1 + t13
  t15 = t14 <= f.p.zeta_threshold
  t16 = jnp.sqrt(f.p.zeta_threshold)
  t17 = t16 * f.p.zeta_threshold
  t18 = jnp.sqrt(t14)
  t19 = t18 * t14
  t20 = f.my_piecewise3(t15, t17, t19)
  t21 = 0.1e1 - t13
  t22 = t21 <= f.p.zeta_threshold
  t23 = jnp.sqrt(t21)
  t24 = t23 * t21
  t25 = f.my_piecewise3(t22, t17, t24)
  t28 = 3 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t31 = t9 ** (0.1e1 / 0.3e1)
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t31 * t33
  t42 = 0.1e1 / t2
  t44 = -t11 * t42 + t12
  t47 = f.my_piecewise3(t15, 0, 0.3e1 / 0.2e1 * t18 * t44)
  t48 = -t44
  t51 = f.my_piecewise3(t22, 0, 0.3e1 / 0.2e1 * t23 * t48)
  t61 = 0.1e1 / t18
  t62 = t44 ** 2
  t66 = 0.1e1 / t2 / t1
  t69 = 0.2e1 * t11 * t66 - 0.2e1 * t42
  t73 = f.my_piecewise3(t15, 0, 0.3e1 / 0.4e1 * t61 * t62 + 0.3e1 / 0.2e1 * t18 * t69)
  t74 = 0.1e1 / t23
  t75 = t48 ** 2
  t78 = -t69
  t82 = f.my_piecewise3(t22, 0, 0.3e1 / 0.4e1 * t74 * t75 + 0.3e1 / 0.2e1 * t23 * t78)
  t91 = 0.1e1 / t19
  t95 = t61 * t44
  t98 = t2 ** 2
  t99 = 0.1e1 / t98
  t102 = -0.6e1 * t11 * t99 + 0.6e1 * t66
  t106 = f.my_piecewise3(t15, 0, -0.3e1 / 0.8e1 * t91 * t62 * t44 + 0.9e1 / 0.4e1 * t95 * t69 + 0.3e1 / 0.2e1 * t18 * t102)
  t107 = 0.1e1 / t24
  t111 = t74 * t48
  t114 = -t102
  t118 = f.my_piecewise3(t22, 0, -0.3e1 / 0.8e1 * t107 * t75 * t48 + 0.9e1 / 0.4e1 * t111 * t78 + 0.3e1 / 0.2e1 * t23 * t114)
  t128 = t14 ** 2
  t131 = t62 ** 2
  t137 = t69 ** 2
  t146 = -0.24e2 * t99 + 0.24e2 * t11 / t98 / t1
  t150 = f.my_piecewise3(t15, 0, 0.9e1 / 0.16e2 / t18 / t128 * t131 - 0.9e1 / 0.4e1 * t91 * t62 * t69 + 0.9e1 / 0.4e1 * t61 * t137 + 0.3e1 * t95 * t102 + 0.3e1 / 0.2e1 * t18 * t146)
  t151 = t21 ** 2
  t154 = t75 ** 2
  t160 = t78 ** 2
  t169 = f.my_piecewise3(t22, 0, 0.9e1 / 0.16e2 / t23 / t151 * t154 - 0.9e1 / 0.4e1 * t107 * t75 * t78 + 0.9e1 / 0.4e1 * t74 * t160 + 0.3e1 * t111 * t114 - 0.3e1 / 0.2e1 * t23 * t146)
  d1111 = -0.160e3 / 0.729e3 / t4 / t2 * t7 * t9 * (t20 / 0.2e1 + t25 / 0.2e1) * t29 * t34 + 0.128e3 / 0.243e3 / t4 / t1 * t7 * t9 * (t47 / 0.2e1 + t51 / 0.2e1) * t29 * t34 - 0.32e2 / 0.27e2 / t4 * t7 * t9 * (t73 / 0.2e1 + t82 / 0.2e1) * t29 * t34 - 0.64e2 / 0.27e2 * t3 * t7 * t9 * (t106 / 0.2e1 + t118 / 0.2e1) * t29 * t34 - 0.4e1 / 0.9e1 * t3 * t1 * t7 * t9 * (t150 / 0.2e1 + t169 / 0.2e1) * t29 * t34

  res = {'v4rho4': d1111}
  return res
