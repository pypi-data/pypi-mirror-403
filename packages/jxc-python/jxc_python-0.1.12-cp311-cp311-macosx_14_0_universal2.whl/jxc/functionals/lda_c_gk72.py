"""Generated from lda_c_gk72.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
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
  f_ls = lambda rs, zeta=None: 0.0311 * jnp.log(rs) - 0.048 + 0.009 * rs * jnp.log(rs) - 0.01 * rs

  f_ms = lambda rs, zeta=None: -0.06156 + 0.01898 * jnp.log(rs)

  f_hs = lambda rs, zeta=None: -0.438 / rs + 1.325 / rs ** (3 / 2) - 1.47 / rs ** 2 - 0.4 / rs ** (5 / 2)

  functional_body = lambda rs, zeta: f.my_piecewise5(rs < 0.7, f_ls(rs, zeta), rs < 10, f_ms(rs, zeta), f_hs(rs, zeta))

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res


def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  f_ls = lambda rs, zeta=None: 0.0311 * jnp.log(rs) - 0.048 + 0.009 * rs * jnp.log(rs) - 0.01 * rs

  f_ms = lambda rs, zeta=None: -0.06156 + 0.01898 * jnp.log(rs)

  f_hs = lambda rs, zeta=None: -0.438 / rs + 1.325 / rs ** (3 / 2) - 1.47 / rs ** 2 - 0.4 / rs ** (5 / 2)

  functional_body = lambda rs, zeta: f.my_piecewise5(rs < 0.7, f_ls(rs, zeta), rs < 10, f_ms(rs, zeta), f_hs(rs, zeta))

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t10 = t6 / t8
  t11 = t4 * t10
  t12 = t11 / 0.4e1
  t13 = t12 < 0.7e0
  t14 = jnp.log(t12)
  t21 = t12 < 0.10e2
  t24 = t1 ** 2
  t26 = t24 / t3
  t30 = jnp.sqrt(0.4e1)
  t31 = jnp.sqrt(t11)
  t36 = t3 ** 2
  t38 = t1 / t36
  t39 = t8 ** 2
  t45 = t5 / t39
  t49 = 0.1e1 / t31 / t24 / t36 / t45 / 0.4e1
  t53 = f.my_piecewise5(t13, 0.311e-1 * t14 - 0.48e-1 + 0.22500000000000000000000000000000000000000000000000e-2 * t4 * t10 * t14 - 0.25000000000000000000000000000000000000000000000000e-2 * t11, t21, -0.6156e-1 + 0.1898e-1 * t14, -0.14600000000000000000000000000000000000000000000000e0 * t26 * t5 * t8 + 0.53000000000000000000000000000000000000000000000000e1 * t30 / t31 / t11 - 0.49000000000000000000000000000000000000000000000000e0 * t38 * t6 * t39 - 0.64000000000000000000000000000000000000000000000000e1 * t30 * t49)
  t54 = 0.1e1 / t7
  t57 = 0.1e1 / t8 / t7
  t58 = t6 * t57
  t68 = 4 ** (0.1e1 / 0.6e1)
  t70 = t4 * t57
  t83 = f.my_piecewise5(t13, -0.10366666666666666666666666666666666666666666666667e-1 * t54 - 0.75000000000000000000000000000000000000000000000000e-3 * t4 * t58 * t14 + 0.8333333333333333333333333333333333333333333333333e-4 * t4 * t58, t21, -0.63266666666666666666666666666666666666666666666667e-2 * t54, -0.48666666666666666666666666666666666666666666666667e-1 * t26 * t45 + 0.10600000000000000000000000000000000000000000000000e2 * t68 * t49 * t70 - 0.32666666666666666666666666666666666666666666666667e0 * t38 * t10 - 0.44444444444444444444444444444444444444444444444444e0 * t68 / t31 / t2 / t54 * t70)
  vrho_0_ = t7 * t83 + t53
  vrho_1_ = vrho_0_

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res


def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / jnp.pi
  t3 = t2 ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t9 = t6 / t7
  t10 = t4 * t9
  t11 = t10 / 0.4e1
  t12 = t11 < 0.7e0
  t13 = jnp.log(t11)
  t20 = t11 < 0.10e2
  t23 = t1 ** 2
  t25 = t23 / t3
  t29 = jnp.sqrt(0.4e1)
  t30 = jnp.sqrt(t10)
  t35 = t3 ** 2
  t37 = t1 / t35
  t38 = t7 ** 2
  t44 = t5 / t38
  t48 = 0.1e1 / t30 / t23 / t35 / t44 / 0.4e1
  t52 = f.my_piecewise5(t12, 0.311e-1 * t13 - 0.48e-1 + 0.22500000000000000000000000000000000000000000000000e-2 * t4 * t9 * t13 - 0.25000000000000000000000000000000000000000000000000e-2 * t10, t20, -0.6156e-1 + 0.1898e-1 * t13, -0.14600000000000000000000000000000000000000000000000e0 * t25 * t5 * t7 + 0.53000000000000000000000000000000000000000000000000e1 * t29 / t30 / t10 - 0.49000000000000000000000000000000000000000000000000e0 * t37 * t6 * t38 - 0.64000000000000000000000000000000000000000000000000e1 * t29 * t48)
  t53 = 0.1e1 / r0
  t56 = 0.1e1 / t7 / r0
  t57 = t6 * t56
  t67 = 4 ** (0.1e1 / 0.6e1)
  t69 = t4 * t56
  t82 = f.my_piecewise5(t12, -0.10366666666666666666666666666666666666666666666667e-1 * t53 - 0.75000000000000000000000000000000000000000000000000e-3 * t4 * t57 * t13 + 0.8333333333333333333333333333333333333333333333333e-4 * t4 * t57, t20, -0.63266666666666666666666666666666666666666666666667e-2 * t53, -0.48666666666666666666666666666666666666666666666667e-1 * t25 * t44 + 0.10600000000000000000000000000000000000000000000000e2 * t67 * t48 * t69 - 0.32666666666666666666666666666666666666666666666667e0 * t37 * t9 - 0.44444444444444444444444444444444444444444444444444e0 * t67 / t30 / t2 / t53 * t69)
  vrho_0_ = r0 * t82 + t52

  res = {'vrho': vrho_0_}
  return res
